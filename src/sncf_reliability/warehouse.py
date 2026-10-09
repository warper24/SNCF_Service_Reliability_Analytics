"""Versions brutes immuables, vue courante et journal BigQuery append-only."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .ingest import Journal, canonical, external_path, sha256, strict_json, write_json


class Warehouse:
    def __init__(self, project, *, dataset="sncf_dev", audit_dataset="sncf_audit",
                 prefix="raw_tgv", location="EU", client=None):
        if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", project or ""):
            raise ValueError("Identifiant de projet BigQuery invalide.")
        if not all(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", value)
                   for value in (dataset, audit_dataset, prefix)):
            raise ValueError("Identifiant de dataset ou préfixe invalide.")
        if location.upper() != "EU" or dataset == "sncf_publish" or audit_dataset == "sncf_publish":
            raise ValueError("J03 utilise EU et ne modifie pas sncf_publish.")
        from google.cloud import bigquery
        from google.api_core.retry import Retry

        self.bq = bigquery
        self.retry = Retry(deadline=45)
        self.project, self.dataset, self.audit_dataset, self.prefix = project, dataset, audit_dataset, prefix
        self.client = client or bigquery.Client(project=project, location="EU")
        self.base = f"{project}.{dataset}.{prefix}"
        self.current = self.base + "_current"
        self.audit_table = f"{project}.{audit_dataset}.{prefix}_load_events"
        self.raw_schema = [bigquery.SchemaField(name, kind, mode="REQUIRED") for name, kind in
                           (("version_id", "STRING"), ("row_number", "INTEGER"),
                            ("row_sha256", "STRING"), ("payload", "STRING"))]
        self.audit_schema = [bigquery.SchemaField(name, kind, mode="REQUIRED") for name, kind in
                             (("attempt_id", "STRING"), ("sequence", "INTEGER"),
                              ("event_at", "TIMESTAMP"), ("event", "STRING"), ("event_json", "STRING"))]

    @property
    def context(self):
        return {"project": self.project, "warehouse_dataset": self.dataset,
                "audit_dataset": self.audit_dataset, "table_prefix": self.prefix}

    def prepare(self):
        for name in {self.dataset, self.audit_dataset}:
            dataset = self.client.get_dataset(f"{self.project}.{name}", retry=self.retry, timeout=20)
            if dataset.location.upper() != "EU":
                raise ValueError("Localisation BigQuery incompatible : " + name)
            if name != "sncf_test" and dataset.default_table_expiration_ms is not None:
                raise ValueError("Expiration automatique inattendue sur un dataset durable : " + name)

    def _table(self, table_id):
        from google.api_core.exceptions import NotFound
        try:
            return self.client.get_table(table_id, retry=self.retry, timeout=20)
        except NotFound:
            return None

    def _job(self, submit, job_id):
        """Retrouver le même job en cas de réponse perdue ; jamais changer son identité."""
        from google.api_core.exceptions import GoogleAPICallError, NotFound
        try:
            job = self.client.get_job(job_id, location="EU", retry=self.retry, timeout=20)
        except NotFound:
            try:
                job = submit()
            except GoogleAPICallError:
                # Une écriture peut avoir réussi avant l'erreur de transport.
                job = self.client.get_job(job_id, location="EU", retry=self.retry, timeout=20)
        job.result(timeout=120, retry=self.retry)
        return job

    def _query(self, sql, job_id, parameters=None):
        config = self.bq.QueryJobConfig(maximum_bytes_billed=100_000_000, query_parameters=parameters or [])
        return self._job(lambda: self.client.query(sql, job_config=config, job_id=job_id,
                         location="EU", retry=self.retry, timeout=20, job_retry=None), job_id)

    def sync_audit(self, attempt_path):
        """MERGE durable par tentative/séquence, même après expiration des métadonnées des jobs."""
        path = external_path(attempt_path)
        attempt = strict_json((path / "attempt.json").read_bytes())
        attempt_id = attempt["attempt_id"]
        if not re.fullmatch(r"[a-f0-9]{32}", attempt_id) or path.name != attempt_id:
            raise ValueError("Identité du journal local incompatible.")
        if any(attempt.get(key) != value for key, value in self.context.items()):
            raise ValueError("Destination du journal différente de la connexion demandée.")
        events_path = path / "events.jsonl"
        if not events_path.exists():
            return 0
        table = self._table(self.audit_table)
        if table and (table.table_type != "TABLE" or table.schema != self.audit_schema):
            raise ValueError("Table d'audit incompatible.")
        rows = []
        for sequence, line in enumerate(events_path.read_text(encoding="utf-8").splitlines(), 1):
            event = strict_json(line)
            if event["attempt_id"] != attempt_id or event["sequence"] != sequence:
                raise ValueError("Séquence du journal local invalide.")
            row = {key: event[key] for key in ("attempt_id", "sequence", "event_at", "event")}
            row["event_json"] = canonical(event)
            rows.append(row)
        if not rows:
            return 0
        if table is None:
            table = self.bq.Table(self.audit_table, schema=self.audit_schema)
            self.client.create_table(table, exists_ok=True, retry=self.retry, timeout=20)
        payload = canonical(rows)
        source = """SELECT JSON_VALUE(element, '$.attempt_id') AS attempt_id,
            CAST(JSON_VALUE(element, '$.sequence') AS INT64) AS sequence,
            TIMESTAMP(JSON_VALUE(element, '$.event_at')) AS event_at,
            JSON_VALUE(element, '$.event') AS event,
            JSON_VALUE(element, '$.event_json') AS event_json
            FROM UNNEST(JSON_QUERY_ARRAY(@events)) AS element"""
        sql = f"""BEGIN TRANSACTION;
            ASSERT (SELECT COUNT(*) FROM `{self.audit_table}` t JOIN ({source}) s
                    USING (attempt_id, sequence) WHERE t.event_json != s.event_json) = 0
                AS 'Evenement existant different du journal local';
            MERGE `{self.audit_table}` t USING ({source}) s
                ON t.attempt_id = s.attempt_id AND t.sequence = s.sequence
            WHEN NOT MATCHED THEN INSERT (attempt_id, sequence, event_at, event, event_json)
                VALUES (s.attempt_id, s.sequence, s.event_at, s.event, s.event_json);
            COMMIT TRANSACTION;"""
        job_id = f"sncf_audit_{self.prefix}_{attempt_id}_{sha256(payload.encode())[:24]}"
        self._query(sql, job_id, [self.bq.ScalarQueryParameter("events", "STRING", payload)])
        return len(rows)

    def verify_version(self, snapshot, table_id, job_id):
        table = self._table(table_id)
        if table is None or table.table_type != "TABLE" or table.schema != self.raw_schema:
            raise ValueError("Table brute absente ou schéma incompatible.")
        if self.dataset != "sncf_test" and table.expires is not None:
            raise ValueError("Expiration inattendue sur la version brute durable.")
        if table.num_rows != len(snapshot.records):
            raise ValueError("Effectif BigQuery différent de l'archive.")
        query = self._query(f"SELECT version_id, row_number, row_sha256, payload FROM `{table_id}` ORDER BY row_number",
                            job_id)
        received = 0
        for received, row in enumerate(query.result(timeout=120, retry=self.retry), 1):
            if received > len(snapshot.records):
                raise ValueError("Lignes BigQuery excédentaires.")
            expected = snapshot.records[received - 1]
            if (row.version_id != snapshot.version_id or row.row_number != received
                    or row.payload != expected or row.row_sha256 != sha256(expected.encode())):
                raise ValueError(f"Contenu BigQuery différent à la ligne {received}.")
        if received != len(snapshot.records):
            raise ValueError("Lecture BigQuery incomplète.")
        return {"rows_verified": received, "verification_job_id": query.job_id,
                "total_bytes_processed": query.total_bytes_processed,
                "total_bytes_billed": query.total_bytes_billed}

    def load(self, snapshot, journal):
        journal.context.update(self.context, **snapshot.context)
        table_id = self.base + "_v_" + snapshot.version_id
        load_id = f"sncf_raw_{self.prefix}_{journal.attempt_id}"
        check_id = f"sncf_check_{self.prefix}_{journal.attempt_id}"
        promote_id = f"sncf_promote_{self.prefix}_{journal.attempt_id}"
        journal.emit("load_started", table_id=table_id, load_job_id=load_id,
                     verification_job_id=check_id, promotion_job_id=promote_id)
        promoted, promotion_requested = False, False
        view_sql = f"SELECT version_id, row_number, row_sha256, payload FROM `{table_id}`"
        try:
            self.prepare()
            self.sync_audit(journal.path)
            existing = self._table(table_id)
            if existing is None:
                payload_path = journal.path / "load.ndjson"
                with payload_path.open("x", encoding="utf-8", newline="\n") as out:
                    for number, record in enumerate(snapshot.records, 1):
                        out.write(canonical({"version_id": snapshot.version_id, "row_number": number,
                                             "row_sha256": sha256(record.encode()), "payload": record}) + "\n")
                config = self.bq.LoadJobConfig(schema=self.raw_schema,
                    source_format=self.bq.SourceFormat.NEWLINE_DELIMITED_JSON,
                    write_disposition="WRITE_EMPTY", max_bad_records=0, ignore_unknown_values=False)
                def submit():
                    with payload_path.open("rb") as stream:
                        return self.client.load_table_from_file(stream, table_id, job_config=config,
                            job_id=load_id, location="EU", num_retries=2, timeout=20)
                job = self._job(submit, load_id)
                journal.emit("raw_loaded", job_id=job.job_id, output_rows=job.output_rows,
                             table_id=table_id, load_file_sha256=sha256(payload_path.read_bytes()))
            else:
                journal.emit("raw_reused", table_id=table_id)
            verification = self.verify_version(snapshot, table_id, check_id)
            journal.emit("version_validated", table_id=table_id, **verification)
            # Les preuves doivent être durables avant de rendre les données courantes.
            self.sync_audit(journal.path)
            current = self._table(self.current)
            if current and current.table_type != "VIEW":
                raise ValueError("L'objet courant existe et n'est pas une vue ; remplacement refusé.")
            changed = current is None or current.view_query != view_sql
            if changed:
                promotion_requested = True
                journal.emit("promotion_requested", table_id=table_id, job_id=promote_id)
                self._query(f"CREATE OR REPLACE VIEW `{self.current}` AS {view_sql}", promote_id)
            current = self._table(self.current)
            if current is None or current.view_query != view_sql:
                raise ValueError("Promotion non confirmée par les métadonnées BigQuery.")
            promoted = True
            journal.emit("promoted" if changed else "current_unchanged", table_id=table_id,
                         current_view=self.current, promotion_job_id=promote_id if changed else None)
            self.sync_audit(journal.path)
            result = {**snapshot.context, **self.context, "table_id": table_id,
                      "current_view": self.current, "reused": existing is not None,
                      "promotion_changed": changed, "status": "complete", **verification}
            write_json(journal.path / "result.json", result)
            return result
        except Exception as error:
            if promotion_requested and not promoted:
                try:
                    current = self._table(self.current)
                    promoted = bool(current and current.table_type == "VIEW" and current.view_query == view_sql)
                except Exception:
                    pass
            status = ("audit_pending" if promoted else
                      "promotion_uncertain" if promotion_requested else "load_failed")
            journal.emit(status, error_type=type(error).__name__, error=str(error),
                         current_view=self.current, promotion_confirmed=promoted)
            try:
                self.sync_audit(journal.path)
            except Exception:
                pass  # La trace locale est conservée ; sync-audit permet sa reprise explicite.
            raise

    def reconcile(self, attempt_path):
        """Relire la vue après une interruption, puis rejouer le journal sans promotion."""
        path = external_path(attempt_path)
        events = [strict_json(line) for line in (path / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        current = self._table(self.current)
        context = events[-1]["context"] if events else {}
        version = context.get("version_id")
        expected = (f"SELECT version_id, row_number, row_sha256, payload FROM `{self.base}_v_{version}`"
                    if version else None)
        self.prepare()
        synced = self.sync_audit(path)
        observed = bool(expected and current and current.table_type == "VIEW" and current.view_query == expected)
        journal = Journal.reopen(path)
        journal.emit("reconciled", current_view=self.current, current_points_to_attempt_version=observed)
        synced = self.sync_audit(path)
        return {"attempt_path": str(path), "events_synchronized": synced,
                "current_view": self.current, "current_points_to_attempt_version":
                    observed}
