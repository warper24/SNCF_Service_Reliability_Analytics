"""Qualifier J05 sur une archive figée ; SQL/dbt porte tous les calculs métier."""

import argparse
from decimal import Decimal
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone

import yaml
from google.cloud import bigquery

from validate_data_quality import serial as base_serial, write_csv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sncf_reliability.ingest import REPO, data_root, now, read_config, sha256, verify_snapshot, write_json
from sncf_reliability.warehouse import Warehouse

MODELS = ("dim_date", "dim_route", "dim_service", "dim_cause", "fct_reliability_monthly",
          "fct_delay_causes_monthly", "mart_route_trends", "mart_route_priorities")
ANALYSES = ("j05_model_summary", "j05_reconciliation", "j05_period_coverage")


def serial(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [serial(item) for item in value]
    if isinstance(value, dict):
        return {key: serial(item) for key, item in value.items()}
    return base_serial(value)


def code_hashes():
    paths = [p for p in (REPO / "dbt").rglob("*") if p.is_file()
             and not any(part in ("target", "logs", "dbt_packages") for part in p.relative_to(REPO / "dbt").parts)
             and p.name != "profiles.yml"]
    paths += [REPO / p for p in ("scripts/validate_data_model.py", "scripts/validate_data_quality.py",
              "scripts/run_dbt.py", "config/datasets.yaml", "pyproject.toml", "uv.lock")]
    paths += list((REPO / "src/sncf_reliability").glob("*.py"))
    return {p.relative_to(REPO).as_posix(): sha256(p.read_bytes()) for p in sorted(paths)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", default="reports/data_model_evidence")
    args = parser.parse_args()
    if not args.execute:
        parser.error("--execute requis pour construire et tester dans BigQuery.")
    for variable in ("BQ_DEV_DATASET", "BQ_RAW_DATASET"):
        if os.environ.get(variable, "sncf_dev") != "sncf_dev":
            parser.error("La qualification J05 cible sncf_dev.")
    if os.environ.get("BQ_LOCATION", "EU") != "EU":
        parser.error("EU requis.")
    profiles_dir = Path(os.environ["DBT_PROFILES_DIR"])
    profile = yaml.safe_load((profiles_dir / "profiles.yml").read_text(encoding="utf-8"))["sncf_service_reliability"]
    limit = profile["outputs"][profile.get("target", "dev")].get("maximum_bytes_billed")
    if not isinstance(limit, int) or not 0 < limit <= 100_000_000:
        parser.error("Chaque requête doit être limitée à 100 MB au plus.")
    snapshot = verify_snapshot(args.snapshot, read_config())
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    run_dir = data_root() / "model_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    output = Path(args.output).resolve()
    report = {"status": "running", "run_id": run_id, "started_at_utc": now(),
              "run_directory": str(run_dir), "source": {**snapshot.context, **snapshot.checks},
              "code_sha256": code_hashes(), "commands": [], "queries": [], "tests": []}
    write_json(run_dir / "validation.json", report)
    try:
        os.environ["GOOGLE_CLOUD_PROJECT"] = args.project
        warehouse = Warehouse(args.project)
        warehouse.prepare()
        table_id = warehouse.base + "_v_" + snapshot.version_id
        print("Vérification de l’archive et de la table brute", flush=True)
        report["raw_verification"] = warehouse.verify_version(snapshot, table_id, "sncf_j05_raw_" + uuid.uuid4().hex)
        variables = {"raw_tgv_identifier": table_id.rsplit(".", 1)[1], "expected_version_id": snapshot.version_id}
        report["dbt_vars"] = variables
        report["versions"] = {n: importlib.metadata.version(n) for n in ("dbt-core", "dbt-bigquery", "google-cloud-bigquery")}
        report["versions"]["python"] = sys.version.split()[0]
        common = ["--project-dir", "dbt", "--profiles-dir", str(profiles_dir), "--vars", json.dumps(variables),
                  "--target-path", str(run_dir / "target"), "--log-path", str(run_dir / "logs"), "--no-use-colors"]
        steps = (("upstream_models", ["run", "--select", "tag:j04"]),
                 ("upstream_tests", ["test", "--select", "tag:j04", "--indirect-selection", "cautious"]),
                 ("models", ["run", "--select", "tag:j05"]),
                 ("tests", ["test", "--select", "tag:j05"]),
                 ("compile", ["compile", "--select", *ANALYSES]))
        for label, command in steps:
            print("dbt " + label, flush=True)
            argv = [sys.executable, "scripts/run_dbt.py", *command, *common]
            log = run_dir / (label + ".txt")
            with log.open("w", encoding="utf-8") as stream:
                result = subprocess.run(argv, cwd=REPO, stdout=stream, stderr=subprocess.STDOUT)
            report["commands"].append({"label": label, "argv": argv, "return_code": result.returncode,
                                       "log_sha256": sha256(log.read_bytes())})
            results = run_dir / "target/run_results.json"
            if results.exists():
                shutil.copy2(results, run_dir / (label + "_run_results.json"))
            if result.returncode:
                raise RuntimeError("dbt " + label + " échoue ; consulter " + str(log))
            if label.endswith("tests"):
                rows = json.loads(results.read_text(encoding="utf-8"))["results"]
                report["tests"].extend({key: r.get(key) for key in
                    ("unique_id", "status", "failures", "message", "adapter_response")} for r in rows)
                if not rows or any(r["status"] not in ("pass", "warn") for r in rows):
                    raise ValueError("Suite vide ou non réussie.")
            write_json(run_dir / "validation.json", report)
        manifest = json.loads((run_dir / "target/manifest.json").read_text(encoding="utf-8"))
        expected_units = {"unit_test.sncf_service_reliability." + t["model"] + "." + t["name"]
                          for t in yaml.safe_load((REPO / "dbt/models/marts/j05_unit_tests.yml").read_text(encoding="utf-8"))["unit_tests"]}
        executed_units = {t["unique_id"] for t in report["tests"] if t["unique_id"].startswith("unit_test.")}
        if not expected_units or not expected_units <= executed_units:
            raise ValueError("Des tests unitaires J05 n'ont pas été exécutés.")
        client = warehouse.client
        report["objects"] = {}
        properties = {m["name"]: m for m in yaml.safe_load(
            (REPO / "dbt/models/marts/marts.yml").read_text(encoding="utf-8"))["models"]}
        for model in (*MODELS, "stg_tgv_reliability", "int_tgv_quality_flags"):
            obj = client.get_table(args.project + ".sncf_dev." + model)
            expected_type = "TABLE" if model in MODELS else "VIEW"
            if obj.table_type != expected_type:
                raise ValueError("Matérialisation incorrecte : " + model)
            if model in properties:
                actual = {f.name: ("ARRAY<" + f.field_type + ">" if f.mode == "REPEATED" else f.field_type)
                          for f in obj.schema}
                if set(actual) != {c["name"] for c in properties[model]["columns"]}:
                    raise ValueError("Documentation des colonnes incomplète : " + model)
                aliases = {"INT64": "INTEGER", "BOOL": "BOOLEAN", "FLOAT64": "FLOAT"}
                for column in properties[model]["columns"]:
                    kind = column.get("data_type")
                    if kind and actual[column["name"]] != aliases.get(kind, kind):
                        raise ValueError("Type incorrect : " + model + "." + column["name"])
            report["objects"][model] = {"type": obj.table_type, "rows": obj.num_rows,
                                        "schema": [f.to_api_repr() for f in obj.schema]}
        report["schema_types_verified"] = True
        # Tous les modèles d'une même qualification doivent être issus d'une invocation unique.
        report["model_invocation_id"] = json.loads((run_dir / "models_run_results.json").read_text(encoding="utf-8"))["metadata"]["invocation_id"]
        for analysis in ANALYSES:
            sql = manifest["nodes"]["analysis.sncf_service_reliability." + analysis]["compiled_code"]
            job = client.query(sql, location="EU", job_id="sncf_j05_" + uuid.uuid4().hex,
                job_config=bigquery.QueryJobConfig(maximum_bytes_billed=100_000_000), timeout=30, job_retry=None)
            rows = [serial(dict(row)) for row in job.result(timeout=120)]
            write_csv(run_dir / (analysis + ".csv"), rows)
            (run_dir / (analysis + ".sql")).write_text(sql, encoding="utf-8")
            report["queries"].append({"analysis": analysis, "job_id": job.job_id, "rows": len(rows),
                "total_bytes_processed": job.total_bytes_processed, "total_bytes_billed": job.total_bytes_billed,
                "cache_hit": job.cache_hit})
        if report["code_sha256"] != code_hashes():
            raise ValueError("Code modifié pendant la qualification.")
        report["status"] = "passed_with_documented_warnings" if any(t["status"] == "warn" for t in report["tests"]) else "passed"
        report["completed_at_utc"] = now()
        report["evidence_sha256"] = {p.name: sha256(p.read_bytes()) for p in run_dir.iterdir()
                                    if p.is_file() and p.name != "validation.json"}
        write_json(run_dir / "validation.json", report)
        output.mkdir(parents=True, exist_ok=True)
        for name in ("validation.json", *(a + ".csv" for a in ANALYSES), *(label + ".txt" for label, _ in steps)):
            shutil.copy2(run_dir / name, output / name)
        print(json.dumps({"status": report["status"], "tests": len(report["tests"]), "output": str(output)}, ensure_ascii=False), flush=True)
    except Exception as exc:
        report.update(status="failed", completed_at_utc=now(), error=str(exc))
        write_json(run_dir / "validation.json", report)
        print("Échec conservé : " + str(run_dir), file=sys.stderr, flush=True)
        raise


if __name__ == "__main__":
    main()
