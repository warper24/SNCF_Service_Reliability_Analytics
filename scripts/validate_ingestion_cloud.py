"""Contrôles J03 opt-in dans sncf_test, sans modification de la vue réelle sncf_dev."""

import argparse
import copy
import io
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from google.cloud import bigquery
from google.api_core.exceptions import BadRequest
from sncf_reliability.ingest import (Journal, canonical, capture, data_root, execution_lock,
                                     read_config, sha256, write_json)
from sncf_reliability.warehouse import Warehouse


class FixtureClient:
    def __init__(self, config, rows, *, incompatible=False):
        fields = [{"name": name, "type": kind} for name, kind in config["fields"].items()]
        if incompatible:
            fields[0]["type"] = "text"
        metadata = {"dataset_id": config["dataset_id"], "fields": fields,
                    "metas": {"default": {"records_count": len(rows), "modified": "2026-01-01T00:00:00Z",
                                          "data_processed": "2026-01-01T00:00:00Z"}}}
        self.items = iter((metadata, rows, metadata))

    def download(self, url, target, journal):
        raw = canonical(next(self.items)).encode()
        target.write_bytes(raw)
        journal.emit("synthetic_fixture", file=target.name)
        return {"url": "synthetic-fixture:" + target.name, "bytes": len(raw), "sha256": sha256(raw)}


class RecordingClient:
    def __init__(self, client, *, corrupt_load=False):
        self.client, self.corrupt_load = client, corrupt_load
        self.jobs = []

    def __getattr__(self, name):
        return getattr(self.client, name)

    def query(self, *args, **kwargs):
        job = self.client.query(*args, **kwargs)
        self.jobs.append(job)
        return job

    def load_table_from_file(self, stream, *args, **kwargs):
        if self.corrupt_load:
            rows = [json.loads(line) for line in stream]
            rows[-1]["row_number"] = "invalid-integer-for-J03-test"
            stream = io.BytesIO(("\n".join(canonical(row) for row in rows) + "\n").encode())
        job = self.client.load_table_from_file(stream, *args, **kwargs)
        self.jobs.append(job)
        return job


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", default="reports/ingestion_evidence/cloud_scenarios.json")
    args = parser.parse_args()
    if not args.execute:
        parser.error("--execute est obligatoire pour ces écritures de test BigQuery.")
    root, config = data_root(), read_config()
    prefix = "j03_check_" + uuid.uuid4().hex[:10]
    client = RecordingClient(bigquery.Client(project=args.project, location="EU"))
    warehouse = Warehouse(args.project, dataset="sncf_test", audit_dataset="sncf_test", prefix=prefix, client=client)
    rows = json.loads((Path(__file__).resolve().parents[1] / "tests/fixtures/ingestion_rows.json").read_text(encoding="utf-8"))
    attempts = []

    def snapshot(values, incompatible=False):
        journal = Journal(root, context=warehouse.context)
        attempts.append(journal)
        return capture(root, config, FixtureClient(config, values, incompatible=incompatible), journal)

    def load(value, target=warehouse):
        journal = Journal(root, context=warehouse.context)
        attempts.append(journal)
        return target.load(value, journal)

    report = {"prefix": prefix, "project": args.project, "dataset": "sncf_test", "synthetic_data": True,
              "code_sha256": {str(path.relative_to(Path(__file__).resolve().parents[1])): sha256(path.read_bytes())
                               for path in (Path(__file__).resolve().parents[1] / "src/sncf_reliability").glob("*.py")}}
    print("Contrôles BigQuery isolés : " + prefix, flush=True)
    try:
        with execution_lock(root, f"{args.project}/sncf_test/{prefix}"):
            first_snapshot = snapshot(rows)
            first = load(first_snapshot)
            second = load(first_snapshot)
            assert first["table_id"] == second["table_id"] and second["reused"] and not second["promotion_changed"]
            report["idempotence"] = {"first": first, "replay": second}
            print("Relance identique vérifiée.", flush=True)
            corrected_rows = copy.deepcopy(rows[:1])
            corrected_rows[0]["nb_annulation"] = 7
            corrected_snapshot = snapshot(corrected_rows)
            corrected = load(corrected_snapshot)
            check = warehouse._query(f"SELECT payload FROM `{warehouse.current}`", "sncf_scenario_" + uuid.uuid4().hex)
            payloads = [json.loads(row.payload) for row in check.result()]
            assert payloads == corrected_rows
            assert warehouse._table(first["table_id"]).num_rows == 2
            assert warehouse._table(corrected["table_id"]).num_rows == 1
            report["historical_correction_and_deletion"] = {"result": corrected, "current_count": 1,
                "historical_count": 2, "corrected_cancellations": payloads[0]["nb_annulation"],
                "raw_negative_preserved": payloads[0]["nb_train_retard_sup_30"] == -3}
            before_view = warehouse._table(warehouse.current).view_query
            print("Correction, suppression et conservation du brut vérifiées.", flush=True)
            corrupt_rows = copy.deepcopy(corrected_rows)
            corrupt_rows[0]["nb_train_prevu"] = 101
            rejected_snapshot = snapshot(corrupt_rows)
            faulty_client = RecordingClient(client.client, corrupt_load=True)
            faulty = Warehouse(args.project, dataset="sncf_test", audit_dataset="sncf_test",
                               prefix=prefix, client=faulty_client)
            try:
                load(rejected_snapshot, faulty)
            except BadRequest as error:
                report["invalid_load"] = {"error_type": type(error).__name__, "error": str(error)}
            else:
                raise AssertionError("Le chargement invalide aurait dû être rejeté.")
            client.jobs.extend(faulty_client.jobs)
            assert warehouse._table(warehouse.current).view_query == before_view
            rejected_table = warehouse._table(warehouse.base + "_v_" + rejected_snapshot.version_id)
            assert rejected_table is None or rejected_table.num_rows == 0
            report["invalid_load"].update(current_preserved=True, partial_rows_visible=False)
            try:
                snapshot(rows, incompatible=True)
            except ValueError as error:
                report["incompatible_schema"] = {"error": str(error), "current_preserved":
                                                 warehouse._table(warehouse.current).view_query == before_view}
                assert report["incompatible_schema"]["current_preserved"]
                warehouse.sync_audit(attempts[-1].path)
            else:
                raise AssertionError("Le schéma incompatible aurait dû être rejeté.")
            print("Échecs de chargement et de schéma sans remplacement de la version courante.", flush=True)
            journal = attempts[2]
            warehouse.sync_audit(journal.path)
            warehouse.sync_audit(journal.path)
            duplicate_check = warehouse._query(f"SELECT attempt_id, sequence, COUNT(*) AS n FROM `{warehouse.audit_table}` "
                "GROUP BY attempt_id, sequence HAVING COUNT(*) != 1", "sncf_scenario_" + uuid.uuid4().hex)
            assert list(duplicate_check.result()) == []
            report["audit_resynchronization"] = {"duplicate_event_groups": 0,
                                                  "reconciled": warehouse.reconcile(journal.path)}
            report["status"] = "passed"
    except Exception as error:
        report.update(status="failed", error_type=type(error).__name__, error=str(error))
        raise
    finally:
        report["attempt_paths"] = [str(journal.path) for journal in attempts]
        report["jobs"] = [{"job_id": job.job_id, "job_type": job.job_type,
                           "total_bytes_processed": getattr(job, "total_bytes_processed", None),
                           "total_bytes_billed": getattr(job, "total_bytes_billed", None),
                           "errors": job.errors} for job in client.jobs]
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        write_json(output, report)
    print("Preuves conservées : " + args.output, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
