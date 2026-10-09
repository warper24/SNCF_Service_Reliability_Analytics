"""Interface d'ingestion et de reprise J03."""

from __future__ import annotations

import argparse
import json
import os
import sys

from .api_client import ApiClient
from .ingest import (Journal, capture, compare_snapshots, data_root, execution_lock,
                     read_config, verify_snapshot)


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("command", choices=("fetch", "replay", "verify", "compare", "sync-audit"))
    result.add_argument("--snapshot", help="Archive figée (J01 ou J03)")
    result.add_argument("--previous", help="Archive précédente pour compare")
    result.add_argument("--attempt", help="Dossier de tentative pour sync-audit")
    result.add_argument("--data-dir", help="Stockage externe, sinon SNCF_DATA_DIR")
    result.add_argument("--load", action="store_true", help="Charger dans BigQuery après extraction/rejeu")
    result.add_argument("--project", default=os.getenv("GOOGLE_CLOUD_PROJECT", ""))
    result.add_argument("--dataset", default=os.getenv("BQ_DEV_DATASET", "sncf_dev"))
    result.add_argument("--audit-dataset", default=os.getenv("BQ_AUDIT_DATASET", "sncf_audit"))
    result.add_argument("--prefix", default="raw_tgv")
    result.add_argument("--location", default=os.getenv("BQ_LOCATION", "EU"))
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    config = read_config()
    if args.command in {"replay", "verify", "compare"} and not args.snapshot:
        raise SystemExit("--snapshot est obligatoire.")
    if args.command == "compare" and not args.previous:
        raise SystemExit("--previous est obligatoire.")
    if args.command == "sync-audit" and not args.attempt:
        raise SystemExit("--attempt est obligatoire.")
    if args.load and args.command not in {"fetch", "replay"}:
        raise SystemExit("--load s'applique uniquement à fetch ou replay.")
    root = data_root(args.data_dir)
    warehouse = None
    scope = f"{args.project}/{args.dataset}/{args.prefix}"
    journal = None
    try:
        with execution_lock(root, scope):
            if args.command in {"fetch", "replay"}:
                context = ({"project": args.project, "warehouse_dataset": args.dataset,
                            "audit_dataset": args.audit_dataset, "table_prefix": args.prefix} if args.load else {})
                journal = Journal(root, context=context)
                journal.emit("attempt_started", command=args.command, cloud_requested=args.load)
            if args.load or args.command == "sync-audit":
                from .warehouse import Warehouse
                warehouse = Warehouse(args.project, dataset=args.dataset, audit_dataset=args.audit_dataset,
                                      prefix=args.prefix, location=args.location)
            if args.command == "sync-audit":
                output = warehouse.reconcile(args.attempt)
            elif args.command in {"verify", "compare"}:
                snapshot = verify_snapshot(args.snapshot, config)
                output = ({**snapshot.context, **snapshot.checks} if args.command == "verify" else
                          compare_snapshots(verify_snapshot(args.previous, config), snapshot))
            else:
                if warehouse:
                    warehouse.prepare()
                    warehouse.sync_audit(journal.path)
                snapshot = (capture(root, config, ApiClient(**config["network"]), journal)
                            if args.command == "fetch" else verify_snapshot(args.snapshot, config))
                journal.context.update(snapshot.context)
                if args.command == "replay":
                    journal.emit("replay_validated", **snapshot.checks)
                output = (warehouse.load(snapshot, journal) if warehouse else
                          {**snapshot.context, **snapshot.checks, "status": "verified_local"})
                output["attempt_path"] = str(journal.path)
            print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        if journal:
            journal.emit("attempt_error", error_type=type(error).__name__, error=str(error))
            if warehouse:
                try:
                    warehouse.sync_audit(journal.path)
                except Exception:
                    pass
        print(json.dumps({"status": "failed", "error_type": type(error).__name__, "error": str(error),
                          "attempt_path": str(journal.path) if journal else None}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
