"""Qualifier J04 et conserver ses preuves ; les règles métier restent en SQL/dbt."""

import argparse
import csv
from datetime import date, datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

import yaml
from google.cloud import bigquery

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sncf_reliability.ingest import REPO, data_root, now, read_config, sha256, verify_snapshot, write_json
from sncf_reliability.warehouse import Warehouse


def serial(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [serial(item) for item in value]
    if isinstance(value, dict):
        return {key: serial(item) for key, item in value.items()}
    return value


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"Résultat de contrôle vide : {path.name}")
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict))
                             else value for key, value in row.items()})


def code_hashes():
    paths = [p for p in (REPO / "dbt").rglob("*") if p.is_file()
             and not any(part in ("target", "logs") for part in p.relative_to(REPO / "dbt").parts)]
    paths += [REPO / "scripts/validate_data_quality.py", REPO / "scripts/run_dbt.py",
              REPO / "config/datasets.yaml", REPO / "pyproject.toml", REPO / "uv.lock"]
    return {p.relative_to(REPO).as_posix(): sha256(p.read_bytes()) for p in sorted(paths)
            if p.name != "profiles.yml"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Autorise les vues et tests BigQuery J04.")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", default="reports/data_quality_evidence")
    args = parser.parse_args()
    if not args.execute:
        parser.error("Ajouter --execute pour exécuter les contrôles cloud, soumis à facturation.")
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,61}[a-z0-9]", args.project):
        parser.error("Identifiant de projet invalide.")
    if os.environ.get("BQ_DEV_DATASET", "sncf_dev") != "sncf_dev":
        parser.error("La qualification J04 cible explicitement sncf_dev.")
    if os.environ.get("BQ_RAW_DATASET", "sncf_dev") != "sncf_dev":
        parser.error("La source J04 doit être sncf_dev.")
    if os.environ.get("BQ_LOCATION", "EU") != "EU":
        parser.error("Localisation EU requise.")
    profiles_dir = Path(os.environ["DBT_PROFILES_DIR"])
    profiles = yaml.safe_load((profiles_dir / "profiles.yml").read_text(encoding="utf-8"))
    profile = profiles["sncf_service_reliability"]
    limit = profile["outputs"][profile.get("target", "dev")].get("maximum_bytes_billed")
    if not isinstance(limit, int) or not 0 < limit <= 100_000_000:
        parser.error("Le profil dbt doit borner chaque requête à au plus 100 MB.")
    snapshot = verify_snapshot(args.snapshot, read_config())
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    run_dir = data_root() / "quality_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    report = {"started_at_utc": now(), "status": "running", "run_id": run_id,
              "run_directory": str(run_dir.resolve()), "source": {**snapshot.context, **snapshot.checks},
              "code_sha256": code_hashes(), "commands": [], "queries": []}
    write_json(run_dir / "validation.json", report)
    try:
        os.environ["GOOGLE_CLOUD_PROJECT"] = args.project
        os.environ.setdefault("BQ_LOCATION", "EU")
        warehouse = Warehouse(args.project)
        table_id = warehouse.base + "_v_" + snapshot.version_id
        print("Vérification complète du brut figé", flush=True)
        report["raw_verification"] = warehouse.verify_version(
            snapshot, table_id, "sncf_j04_raw_" + uuid.uuid4().hex)
        client = warehouse.client
        for dataset in ("sncf_dev", "sncf_audit"):
            if client.get_dataset(args.project + "." + dataset).location != "EU":
                raise ValueError("Dataset hors EU.")
        variables = {"raw_tgv_identifier": table_id.rsplit(".", 1)[1],
                     "expected_version_id": snapshot.version_id}
        report["dbt_vars"] = variables
        report["versions"] = {name: importlib.metadata.version(name)
                              for name in ("dbt-core", "dbt-bigquery", "google-cloud-bigquery")}
        common = ["--project-dir", "dbt", "--profiles-dir", os.environ["DBT_PROFILES_DIR"],
                  "--vars", json.dumps(variables), "--target-path", str(run_dir / "target"),
                  "--log-path", str(run_dir / "logs"), "--no-use-colors"]
        for label, command in (("models", ["run", "--select", "tag:j04"]),
                               ("tests", ["test", "--select", "tag:j04"]),
                               ("compile", ["compile", "--select", "j04_quality_summary",
                                            "j04_coverage", "j04_anomaly_examples",
                                            "j04_period_coverage", "j04_manual_cases"])):
            argv = [sys.executable, "scripts/run_dbt.py", *command, *common]
            print(f"dbt {label}", flush=True)
            log = run_dir / (label + ".txt")
            with log.open("w", encoding="utf-8") as stream:
                result = subprocess.run(argv, cwd=REPO, stdout=stream, stderr=subprocess.STDOUT)
            report["commands"].append({"label": label, "argv": argv, "return_code": result.returncode,
                                       "log": str(log), "log_sha256": sha256(log.read_bytes())})
            results = run_dir / "target/run_results.json"
            if results.exists():
                shutil.copy2(results, run_dir / (label + "_run_results.json"))
            if result.returncode:
                raise RuntimeError(f"dbt {label} échoue ; consulter {log}")
        test_results = json.loads((run_dir / "tests_run_results.json").read_text(encoding="utf-8"))
        report["tests"] = [{key: result.get(key) for key in
                            ("unique_id", "status", "failures", "message", "adapter_response")}
                           for result in test_results["results"]]
        if not report["tests"] or any(r["status"] not in ("pass", "warn") for r in report["tests"]):
            raise ValueError("Suite de tests incomplète ou non réussie.")
        if sum(r["unique_id"].startswith("unit_test.") for r in report["tests"]) != 2:
            raise ValueError("Les deux suites unitaires J04 n'ont pas été exécutées.")
        manifest = json.loads((run_dir / "target/manifest.json").read_text(encoding="utf-8"))
        report["views"] = {}
        for model in ("stg_tgv_reliability", "int_tgv_quality_flags"):
            table = client.get_table(args.project + ".sncf_dev." + model)
            if table.table_type != "VIEW":
                raise ValueError(f"{model} n'est pas une vue.")
            report["views"][model] = {"type": table.table_type, "sql": table.view_query,
                                      "schema": [field.to_api_repr() for field in table.schema]}
            properties = yaml.safe_load((REPO / "dbt/models" /
                          ("staging" if model.startswith("stg") else "intermediate") /
                          (model + ".yml")).read_text(encoding="utf-8"))["models"][0]
            actual = {field.name: ("ARRAY<" + field.field_type + ">" if field.mode == "REPEATED"
                                  else field.field_type) for field in table.schema}
            aliases = {"INT64": "INTEGER", "FLOAT64": "FLOAT", "BOOL": "BOOLEAN"}
            for col in properties["columns"]:
                expected = aliases.get(col["data_type"], col["data_type"])
                if actual.get(col["name"]) != expected:
                    raise ValueError(f"Type inattendu : {model}.{col['name']}")
        report["schema_types_verified"] = True
        for analysis, filename in (("j04_quality_summary", "quality_summary.csv"),
                                   ("j04_coverage", "coverage.csv"),
                                   ("j04_anomaly_examples", "anomaly_examples.csv"),
                                   ("j04_period_coverage", "period_coverage.csv"),
                                   ("j04_manual_cases", "manual_cases.csv")):
            node = manifest["nodes"]["analysis.sncf_service_reliability." + analysis]
            sql = node["compiled_code"]
            job = client.query(sql, location="EU", job_id="sncf_j04_" + uuid.uuid4().hex,
                               job_config=bigquery.QueryJobConfig(maximum_bytes_billed=100_000_000),
                               timeout=30, job_retry=None)
            rows = [serial(dict(row)) for row in job.result(timeout=120)]
            write_csv(run_dir / filename, rows)
            (run_dir / (analysis + ".sql")).write_text(sql, encoding="utf-8")
            report["queries"].append({"analysis": analysis, "job_id": job.job_id,
                                      "rows": len(rows), "total_bytes_processed": job.total_bytes_processed,
                                      "total_bytes_billed": job.total_bytes_billed,
                                      "cache_hit": job.cache_hit})
        if report["code_sha256"] != code_hashes():
            raise ValueError("Le code a changé pendant la qualification.")
        report["status"] = "passed_with_documented_warnings" if any(
            result["status"] == "warn" for result in report["tests"]) else "passed"
        report["completed_at_utc"] = now()
        report["evidence_sha256"] = {p.name: sha256(p.read_bytes()) for p in run_dir.iterdir()
                                    if p.is_file() and p.name != "validation.json"}
        write_json(run_dir / "validation.json", report)
        # Le dossier de travail externe garde chaque exécution ; la synthèse du dépôt pointe la dernière.
        for name in ("quality_summary.csv", "coverage.csv", "anomaly_examples.csv", "validation.json",
                     "period_coverage.csv", "manual_cases.csv",
                     "models.txt", "tests.txt", "compile.txt"):
            shutil.copy2(run_dir / name, output / name)
        print(json.dumps({"status": report["status"], "tests": len(report["tests"]),
                          "warnings": sum(r["status"] == "warn" for r in report["tests"]),
                          "evidence": str(output)}, ensure_ascii=False), flush=True)
    except Exception as exc:
        report.update(status="failed", completed_at_utc=now(), error=str(exc))
        write_json(run_dir / "validation.json", report)
        print(f"Échec conservé : {run_dir}", file=sys.stderr, flush=True)
        raise


if __name__ == "__main__":
    main()
