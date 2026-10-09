"""Vérifier le brut SNCF et le journal réellement présents dans BigQuery (lecture seule)."""

import argparse
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sncf_reliability.ingest import (canonical, data_root, now, read_config, sha256,
                                     strict_json, verify_snapshot, write_json)
from sncf_reliability.warehouse import Warehouse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--output", default="reports/ingestion_evidence/live_warehouse.json")
    args = parser.parse_args()
    snapshot = verify_snapshot(args.snapshot, read_config())
    warehouse = Warehouse(args.project)
    warehouse.prepare()
    table_id = warehouse.base + "_v_" + snapshot.version_id
    report = {"verified_at_utc": now(), "snapshot": {**snapshot.context, **snapshot.checks},
              "table_id": table_id, "current_view": warehouse.current}
    verification = warehouse.verify_version(snapshot, table_id, "sncf_final_check_" + uuid.uuid4().hex)
    report["full_payload_verification"] = verification
    current = warehouse._table(warehouse.current)
    expected_sql = f"SELECT version_id, row_number, row_sha256, payload FROM `{table_id}`"
    assert current and current.table_type == "VIEW" and current.view_query == expected_sql
    report["current_view_definition"] = current.view_query
    table = warehouse._table(table_id)
    report["raw_table"] = {"num_rows": table.num_rows, "expires": table.expires,
                           "schema": [field.to_api_repr() for field in table.schema]}
    local, attempts = {}, []
    for attempt_file in sorted((data_root() / "attempts").glob("*/attempt.json")):
        attempt = strict_json(attempt_file.read_bytes())
        if any(attempt.get(key) != value for key, value in warehouse.context.items()):
            continue
        events_file = attempt_file.parent / "events.jsonl"
        events = [strict_json(line) for line in events_file.read_text(encoding="utf-8").splitlines()]
        local.update({(event["attempt_id"], event["sequence"]): canonical(event) for event in events})
        result_file = attempt_file.parent / "result.json"
        attempts.append({"attempt_id": attempt["attempt_id"], "attempt_path": str(attempt_file.parent),
                         "events": [event["event"] for event in events],
                         "result": strict_json(result_file.read_bytes()) if result_file.exists() else None})
    query = warehouse._query(f"SELECT attempt_id, sequence, event_json FROM `{warehouse.audit_table}`",
                             "sncf_final_audit_" + uuid.uuid4().hex)
    cloud_rows = list(query.result())
    cloud = {(row.attempt_id, row.sequence): row.event_json for row in cloud_rows}
    assert len(cloud) == len(cloud_rows), "Doublons dans le journal cloud"
    assert local and all(cloud.get(key) == value for key, value in local.items()), "Journal local/cloud différent"
    version_tables = [entry.table_id for entry in warehouse.client.list_tables(f"{args.project}.sncf_dev")
                      if entry.table_id.startswith("raw_tgv_v_")]
    report["audit"] = {"table_id": warehouse.audit_table, "cloud_event_count": len(cloud_rows),
                       "local_event_count": len(local), "all_local_events_match_cloud": True,
                       "duplicate_event_groups": 0, "query_job_id": query.job_id,
                       "total_bytes_processed": query.total_bytes_processed,
                       "total_bytes_billed": query.total_bytes_billed}
    report["recorded_attempts"] = attempts
    report["version_tables"] = sorted(version_tables)
    report["status"] = "passed"
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, report)
    print(json.dumps({"status": "passed", "rows_verified": verification["rows_verified"],
                      "version_tables": len(version_tables), "audit_events": len(cloud_rows),
                      "evidence": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
