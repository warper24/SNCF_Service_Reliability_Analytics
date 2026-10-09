"""Contrôle minimal de lecture/écriture BigQuery pour J02, sans donnée SNCF."""

from __future__ import annotations

import argparse
import os
import re
from datetime import datetime, timedelta, timezone


ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")
DATASET_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,1023}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Créer et relire la table d'essai")
    parser.add_argument("--project", default=os.getenv("GOOGLE_CLOUD_PROJECT", ""))
    parser.add_argument("--dataset", default=os.getenv("BQ_DEV_DATASET", "sncf_dev"))
    parser.add_argument("--location", default=os.getenv("BQ_LOCATION", "EU"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not ID_PATTERN.fullmatch(args.project):
        raise SystemExit("GOOGLE_CLOUD_PROJECT manque ou n'est pas un identifiant valide.")
    if not DATASET_PATTERN.fullmatch(args.dataset):
        raise SystemExit("BQ_DEV_DATASET n'est pas un identifiant valide.")
    if args.location.upper() != "EU":
        raise SystemExit("J02 attend la localisation EU décrite dans infra/bootstrap.sql.")
    print(f"Configuration valide : projet={args.project}, dataset={args.dataset}, lieu=EU")
    if not args.execute:
        print("Contrôle local uniquement. Utiliser --execute pour le test cloud.")
        return 0

    from google.cloud import bigquery

    client = bigquery.Client(project=args.project, location="EU")
    dataset = client.get_dataset(f"{args.project}.{args.dataset}")
    if dataset.location.upper() != "EU":
        raise SystemExit(f"Localisation inattendue du dataset : {dataset.location}")
    table_id = f"{args.project}.{args.dataset}.j02_python_connection_check"
    table = bigquery.Table(table_id, schema=[
        bigquery.SchemaField("connection_ok", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("milestone", "STRING", mode="REQUIRED"),
    ])
    table.expires = datetime.now(timezone.utc) + timedelta(days=7)
    table = client.create_table(table, exists_ok=True)
    table.expires = datetime.now(timezone.utc) + timedelta(days=7)
    client.update_table(table, ["expires"])
    load = client.load_table_from_json(
        [{"connection_ok": 1, "milestone": "J02"}],
        table_id,
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE"),
        location="EU",
    )
    load.result()
    query = client.query(
        f"SELECT connection_ok, milestone FROM `{table_id}`",
        job_config=bigquery.QueryJobConfig(maximum_bytes_billed=100_000_000),
        location="EU",
    )
    rows = [(row.connection_ok, row.milestone) for row in query.result()]
    if rows != [(1, "J02")]:
        raise SystemExit(f"Lecture différente de l'essai attendu : {rows!r}")
    print(f"Lecture/écriture vérifiée : {table_id}, lignes={len(rows)}")
    print(f"Jobs BigQuery : load={load.job_id}, query={query.job_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
