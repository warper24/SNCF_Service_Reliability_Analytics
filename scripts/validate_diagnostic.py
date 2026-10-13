"""Exécuter J06 sur les tables J05 qualifiées ; SQL porte tous les calculs métier."""

import argparse
import csv
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

from validate_data_model import serial, MODELS

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sncf_reliability.ingest import REPO, data_root, now, read_config, sha256, verify_snapshot, write_json
from sncf_reliability.warehouse import Warehouse

ANALYSES = ("diagnostic_fixtures", "diagnostic_validation", "route_degradation",
            "persistent_underperformance", "volume_rate_decomposition", "cause_profiles",
            "priority_sensitivity", "diagnostic_summary", "period_sensitivity")
EXPECTED_CHECKS = {"diagnostic_fixtures": 26, "diagnostic_validation": 10}


def code_hashes():
    paths = []
    for directory in ("dbt", "analyses/sql", "src/sncf_reliability"):
        paths.extend(p for p in (REPO / directory).rglob("*") if p.is_file()
                     and not any(part in ("target", "logs", "dbt_packages", "__pycache__") for part in p.parts)
                     and p.name != "profiles.yml")
    paths.extend(REPO / name for name in ("scripts/validate_diagnostic.py", "scripts/validate_data_model.py",
                 "scripts/validate_data_quality.py", "scripts/run_dbt.py", "config/datasets.yaml",
                 "pyproject.toml", "uv.lock", "docs/prioritization_method.md"))
    return {p.relative_to(REPO).as_posix(): sha256(p.read_bytes()) for p in sorted(set(paths))}


def object_state(client, project):
    states = {}
    for name in (*MODELS, "stg_tgv_reliability", "int_tgv_quality_flags"):
        obj = client.get_table(f"{project}.sncf_dev.{name}", timeout=30)
        if obj.table_type != ("TABLE" if name in MODELS else "VIEW"):
            raise ValueError("Type d'objet inattendu : " + name)
        states[name] = {"type": obj.table_type, "modified": obj.modified.isoformat(),
                        "rows": obj.num_rows, "schema": [f.to_api_repr() for f in obj.schema],
                        "view_query": obj.view_query}
    return states


def write_result(path, rows, schema):
    # Un diagnostic sans liaison prioritaire est valide ; conserver les en-têtes.
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=[f.name for f in schema])
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                             for k, v in row.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--project", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--upstream-evidence", default="reports/data_model_evidence/validation.json")
    parser.add_argument("--output", default="reports/diagnostic_evidence")
    parser.add_argument("--reuse-upstream-run", help="Réutiliser seulement les tests amont d'une tentative J06 réussie, à entrées inchangées.")
    args = parser.parse_args()
    if not args.execute:
        parser.error("--execute requis pour les requêtes BigQuery.")
    for variable in ("BQ_DEV_DATASET", "BQ_RAW_DATASET"):
        if os.environ.get(variable, "sncf_dev") != "sncf_dev":
            parser.error("Les entrées J06 doivent être dans sncf_dev.")
    if os.environ.get("BQ_LOCATION", "EU") != "EU":
        parser.error("EU requis.")
    profile_dir = Path(os.environ["DBT_PROFILES_DIR"])
    profile = yaml.safe_load((profile_dir / "profiles.yml").read_text(encoding="utf-8"))["sncf_service_reliability"]
    limit = profile["outputs"][profile.get("target", "dev")].get("maximum_bytes_billed")
    if not isinstance(limit, int) or not 0 < limit <= 100_000_000:
        parser.error("Limite de requête de 100 MB au plus requise.")
    upstream_path = Path(args.upstream_evidence)
    upstream = json.loads(upstream_path.read_text(encoding="utf-8"))
    if upstream.get("status") not in ("passed", "passed_with_documented_warnings"):
        raise ValueError("Qualification J05 réussie requise.")
    # Le raccordement des analyses et la version du projet changent, pas les modèles J05.
    for name, digest in upstream["code_sha256"].items():
        if name != "dbt/dbt_project.yml" and sha256((REPO / name).read_bytes()) != digest:
            raise ValueError("Code amont différent du code J05 qualifié : " + name)
    config = yaml.safe_load((REPO / "dbt/dbt_project.yml").read_text(encoding="utf-8"))
    expected_vars = {"minimum_monthly_operated_proxy": 30, "deterioration_threshold_pp": 2,
                     "regularity_target_pct": 90, "persistence_months": 4}
    if any(config["vars"].get(k) != v for k, v in expected_vars.items()):
        raise ValueError("Les paramètres de référence J05 ont changé.")
    if config["vars"]["comparison_windows"] != [
        {"comparison_id": "2026_h1_vs_2025_h1", "current_start": "2026-01-01", "current_end": "2026-06-01",
         "expected_months": 6, "persistence_applicable": True},
        {"comparison_id": "2025_vs_2024", "current_start": "2025-01-01", "current_end": "2025-12-01",
         "expected_months": 12, "persistence_applicable": False}]:
        raise ValueError("Les fenêtres préspécifiées ont changé.")
    snapshot = verify_snapshot(args.snapshot, read_config())
    if snapshot.version_id != upstream["source"]["version_id"]:
        raise ValueError("Archive différente de la qualification J05.")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    run_dir = data_root() / "diagnostic_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    report = {"status": "running", "run_id": run_id, "started_at_utc": now(),
              "run_directory": str(run_dir), "source": {**snapshot.context, **snapshot.checks},
              "upstream_run_id": upstream["run_id"], "upstream_validation_sha256": sha256(upstream_path.read_bytes()),
              "code_sha256": code_hashes(), "commands": [], "queries": [], "checks": [], "tests": []}
    write_json(run_dir / "validation.json", report)
    try:
        os.environ["GOOGLE_CLOUD_PROJECT"] = args.project
        warehouse = Warehouse(args.project)
        warehouse.prepare()
        report["raw_verification"] = warehouse.verify_version(snapshot, warehouse.base + "_v_" + snapshot.version_id,
                                                               "sncf_j06_raw_" + uuid.uuid4().hex)
        client = warehouse.client
        report["objects_before"] = object_state(client, args.project)
        for name in MODELS:
            if report["objects_before"][name]["schema"] != upstream["objects"][name]["schema"]:
                raise ValueError("Schéma différent de J05 : " + name)
        report["versions"] = {name: importlib.metadata.version(name) for name in
                              ("dbt-core", "dbt-bigquery", "google-cloud-bigquery")}
        report["versions"]["python"] = sys.version.split()[0]
        variables = {"raw_tgv_identifier": "raw_tgv_v_" + snapshot.version_id, "expected_version_id": snapshot.version_id}
        report["dbt_vars"] = variables
        common = ["--project-dir", "dbt", "--profiles-dir", str(profile_dir), "--vars", json.dumps(variables),
                  "--target-path", str(run_dir / "target"), "--log-path", str(run_dir / "logs"), "--no-use-colors"]
        for label, command in (
            ("compile", ["compile", "--select", *ANALYSES]),
            ("upstream_tests", ["test", "--select", "tag:j04", "tag:j05", "--indirect-selection", "cautious"])):
            if label == "upstream_tests" and args.reuse_upstream_run:
                prior_dir = Path(args.reuse_upstream_run).resolve()
                prior = json.loads((prior_dir / "validation.json").read_text(encoding="utf-8"))
                if prior["status"] not in ("passed", "passed_with_documented_warnings") or prior["source"] != report["source"]:
                    raise ValueError("Réutilisation : qualification ou version incompatible.")
                if prior["objects_after"] != report["objects_before"] or prior["versions"] != report["versions"]:
                    raise ValueError("Réutilisation : entrées ou environnement modifiés.")
                # Les 57 fichiers J05 sont déjà contrôlés plus haut contre la qualification historique.
                for name in upstream["code_sha256"]:
                    if prior["code_sha256"][name] != report["code_sha256"][name]:
                        raise ValueError("Réutilisation : code amont modifié : " + name)
                expected = {r["unique_id"] for r in upstream["tests"]}
                if not expected <= {r["unique_id"] for r in prior["tests"]} or any(r["status"] not in ("pass", "warn") for r in prior["tests"]):
                    raise ValueError("Réutilisation : tests amont incomplets ou échoués.")
                for filename in ("upstream_tests.txt", "upstream_tests_run_results.json"):
                    if sha256((prior_dir / filename).read_bytes()) != prior["evidence_sha256"][filename]:
                        raise ValueError("Réutilisation : preuve amont altérée.")
                    shutil.copy2(prior_dir / filename, run_dir / filename)
                report["tests"] = prior["tests"]
                report["upstream_tests_reused_from"] = {"run_id": prior["run_id"],
                    "validation_sha256": sha256((prior_dir / "validation.json").read_bytes())}
                report["commands"].append({"label": label, "reused": True,
                    "log_sha256": sha256((run_dir / "upstream_tests.txt").read_bytes())})
                write_json(run_dir / "validation.json", report)
                print("Tests amont réutilisés, entrées et preuves inchangées", flush=True)
                continue
            print(label, flush=True)
            argv = [sys.executable, "scripts/run_dbt.py", *command, *common]
            with (run_dir / (label + ".txt")).open("w", encoding="utf-8") as log:
                result = subprocess.run(argv, cwd=REPO, stdout=log, stderr=subprocess.STDOUT)
            report["commands"].append({"label": label, "return_code": result.returncode,
                                       "log_sha256": sha256((run_dir / (label + ".txt")).read_bytes())})
            results_path = run_dir / "target/run_results.json"
            if results_path.exists():
                shutil.copy2(results_path, run_dir / (label + "_run_results.json"))
            if result.returncode:
                raise RuntimeError("dbt " + label + " échoue ; consulter son journal.")
            if label == "compile":
                manifest = json.loads((run_dir / "target/manifest.json").read_text(encoding="utf-8"))
                shutil.copy2(run_dir / "target/manifest.json", run_dir / "compiled_manifest.json")
                report["preflight"] = []
                for name in ANALYSES:
                    sql = manifest["nodes"]["analysis.sncf_service_reliability." + name]["compiled_code"]
                    dry = client.query(sql, location="EU", timeout=30, job_retry=None,
                        job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False, maximum_bytes_billed=limit))
                    if dry.statement_type != "SELECT" or (dry.total_bytes_processed or 0) > limit:
                        raise ValueError("Analyse non SELECT ou estimation au-delà de la limite : " + name)
                    report["preflight"].append({"analysis": name, "statement_type": dry.statement_type,
                                                 "estimated_bytes": dry.total_bytes_processed})
            if label == "upstream_tests":
                executed = json.loads(results_path.read_text(encoding="utf-8"))["results"]
                expected = {r["unique_id"] for r in upstream["tests"]}
                report["tests"] = [{k: r.get(k) for k in ("unique_id", "status", "failures", "message")} for r in executed]
                if not expected <= {r["unique_id"] for r in executed} or any(r["status"] not in ("pass", "warn") for r in executed):
                    raise ValueError("Contrôles amont absents ou échoués.")
            write_json(run_dir / "validation.json", report)
        for name in ANALYSES:
            sql = manifest["nodes"]["analysis.sncf_service_reliability." + name]["compiled_code"]
            (run_dir / (name + ".sql")).write_text(sql, encoding="utf-8")
            print(name, flush=True)
            job_id = "sncf_j06_" + uuid.uuid4().hex
            report["queries"].append({"analysis": name, "job_id": job_id, "status": "submitted"})
            write_json(run_dir / "validation.json", report)
            job = client.query(sql, location="EU", job_id=job_id, job_retry=None, timeout=30,
                               job_config=bigquery.QueryJobConfig(maximum_bytes_billed=limit))
            result_rows = job.result(timeout=300)
            rows = [serial(dict(row)) for row in result_rows]
            write_result(run_dir / (name + ".csv"), rows, result_rows.schema)
            report["queries"][-1].update(status="complete", rows=len(rows), total_bytes_processed=job.total_bytes_processed,
                                         total_bytes_billed=job.total_bytes_billed, cache_hit=job.cache_hit,
                                         sql_sha256=sha256(sql.encode("utf-8")))
            if name in EXPECTED_CHECKS:
                report["checks"].extend(rows)
                if len(rows) != EXPECTED_CHECKS[name] or any(row["failures"] != 0 for row in rows):
                    raise ValueError("Contrôle J06 échoué ou suite incomplète : " + name)
            write_json(run_dir / "validation.json", report)
        report["objects_after"] = object_state(client, args.project)
        if report["objects_before"] != report["objects_after"]:
            raise ValueError("Une entrée a changé pendant le diagnostic.")
        if code_hashes() != report["code_sha256"]:
            raise ValueError("Code ou méthode modifiés pendant la qualification.")
        report["status"] = "passed_with_documented_warnings"
        report["completed_at_utc"] = now()
        report["evidence_sha256"] = {p.name: sha256(p.read_bytes()) for p in run_dir.iterdir()
                                     if p.is_file() and p.name != "validation.json"}
        write_json(run_dir / "validation.json", report)
        output = Path(args.output).resolve()
        output.mkdir(parents=True, exist_ok=True)
        for name in ("validation.json", "upstream_tests.txt", "compile.txt", *(a + ".csv" for a in ANALYSES)):
            shutil.copy2(run_dir / name, output / name)
        print(json.dumps({"status": report["status"], "run_id": run_id, "checks": len(report["checks"]),
                          "output": str(output)}, ensure_ascii=False), flush=True)
    except Exception as exc:
        report.update(status="failed", completed_at_utc=now(), error=str(exc))
        write_json(run_dir / "validation.json", report)
        print("Échec conservé : " + str(run_dir), file=sys.stderr, flush=True)
        raise


if __name__ == "__main__":
    main()
