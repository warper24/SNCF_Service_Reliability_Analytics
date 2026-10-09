"""Scénarios J03 hors réseau ; le pilote cloud séparé conserve les preuves réelles."""

import copy
import io
import inspect
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sncf_reliability.api_client import ApiClient
from sncf_reliability.ingest import (Journal, canonical, capture, compare_snapshots, execution_lock,
                                     external_path, read_config, sha256, strict_json, verify_snapshot)


def fixture_rows():
    return json.loads((Path(__file__).parent / "fixtures/ingestion_rows.json").read_text(encoding="utf-8"))


def metadata(config, count=2, **values):
    return {"dataset_id": config["dataset_id"],
            "fields": [{"name": name, "type": kind} for name, kind in config["fields"].items()],
            "metas": {"default": {"records_count": count, "modified": "2026-01-01T00:00:00Z",
                                  "data_processed": "2026-01-01T00:00:00Z", **values}}}


class Response(io.BytesIO):
    status = 200

    def __init__(self, content, length=None):
        super().__init__(content)
        self.headers = {"Content-Length": str(len(content) if length is None else length)}


def queue_client(items, **kwargs):
    queue = iter(items)
    def opener(*args, **options):
        item = next(queue)
        if isinstance(item, Exception):
            raise item
        return item if isinstance(item, Response) else Response(canonical(item).encode())
    return ApiClient(opener=opener, sleep=lambda _: None, **kwargs)


def make_snapshot(root, config, rows=None, before=None, after=None):
    rows = fixture_rows() if rows is None else rows
    before = metadata(config, len(rows)) if before is None else before
    after = before if after is None else after
    journal = Journal(root)
    return capture(root, config, queue_client([before, rows, after]), journal)


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.config = read_config()

    def test_complete_capture_replay_without_network_and_raw_values(self):
        snapshot = make_snapshot(self.root, self.config)
        with patch("urllib.request.urlopen", side_effect=AssertionError("Réseau interdit")):
            replay = verify_snapshot(snapshot.path, self.config)
        self.assertEqual(snapshot.version_id, replay.version_id)
        self.assertEqual(replay.rows[0]["nb_train_retard_sup_30"], -3)
        self.assertIsNone(replay.rows[1]["prct_cause_externe"])
        self.assertEqual(replay.rows[1]["nb_train_prevu"], 0)

    def test_order_and_format_do_not_change_content_identity(self):
        first = make_snapshot(self.root, self.config)
        second = make_snapshot(self.root, self.config, list(reversed(fixture_rows())))
        self.assertEqual(first.version_id, second.version_id)
        self.assertNotEqual(first.context["source_sha256"], second.context["source_sha256"])
        duplicate = make_snapshot(self.root, self.config, fixture_rows() + [fixture_rows()[0]])
        self.assertNotEqual(first.version_id, duplicate.version_id)
        self.assertEqual(len(duplicate.records), 3)

    def test_truncation_preserves_failed_manifest_and_received_payload(self):
        journal = Journal(self.root)
        with self.assertRaisesRegex(ValueError, "incomplet"):
            capture(self.root, self.config, queue_client([metadata(self.config, 3), fixture_rows(),
                                                        metadata(self.config, 3)]), journal)
        path = Path(journal.context["snapshot_path"])
        self.assertEqual(strict_json((path / "manifest.json").read_bytes())["status"], "failed")
        self.assertTrue((path / "source.json").exists())
        with self.assertRaisesRegex(ValueError, "incomplète"):
            verify_snapshot(path, self.config)

    def test_source_changed_with_same_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "modifiée"):
            make_snapshot(self.root, self.config, after=metadata(self.config, modified="2026-01-02T00:00:00Z"))

    def test_empty_source_is_not_promoted(self):
        with self.assertRaisesRegex(ValueError, "nul ou invalide"):
            make_snapshot(self.root, self.config, [])

    def test_schema_drift_and_row_type_rejected(self):
        changed = metadata(self.config)
        changed["fields"][0]["type"] = "text"
        with self.assertRaisesRegex(ValueError, "Schéma"):
            make_snapshot(self.root, self.config, before=changed)
        rows = fixture_rows()
        rows[0]["nb_train_prevu"] = "100"
        with self.assertRaisesRegex(ValueError, "Type incompatible"):
            make_snapshot(self.root, self.config, rows)

    def test_row_shape_and_missing_marker_rejected(self):
        rows = fixture_rows()
        del rows[0]["commentaire_annulation"]
        with self.assertRaisesRegex(ValueError, "Structure"):
            make_snapshot(self.root, self.config, rows)
        with self.assertRaisesRegex(ValueError, "Marqueur"):
            make_snapshot(self.root, self.config, before=metadata(self.config, modified=None))

    def test_null_month_preserved_and_coverage_unavailable(self):
        rows = fixture_rows()
        for row in rows:
            row["date"] = None
        snapshot = make_snapshot(self.root, self.config, rows)
        self.assertIsNone(snapshot.checks["last_business_month"])
        self.assertEqual(snapshot.checks["missing_or_invalid_months"], 2)

    def test_tampered_archive_and_path_traversal_rejected(self):
        snapshot = make_snapshot(self.root, self.config)
        source = snapshot.path / "source.json"
        source.write_bytes(source.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "Empreinte"):
            verify_snapshot(snapshot.path, self.config)
        manifest = snapshot.manifest
        manifest["files"]["../outside.json"] = {"sha256": "", "bytes": 0}
        (snapshot.path / "manifest.json").write_text(canonical(manifest), encoding="utf-8")
        # Le chemin sortant est vérifié même s'il n'existe pas.
        with self.assertRaisesRegex(ValueError, "Chemin"):
            verify_snapshot(snapshot.path, self.config)

    def test_json_duplicate_keys_and_nan_rejected(self):
        for value in ('{"a":1,"a":2}', '{"a":NaN}'):
            with self.assertRaises(ValueError):
                strict_json(value)

    def test_transient_retry_and_terminal_error(self):
        journal = Journal(self.root)
        client = queue_client([urllib.error.HTTPError("https://source", 503, "busy", {}, None), {"ok": 1}])
        client.download("https://source", self.root / "received.json", journal)
        events = (journal.path / "events.jsonl").read_text(encoding="utf-8")
        self.assertIn('"network_attempt":2', events)
        with self.assertRaises(urllib.error.HTTPError):
            queue_client([urllib.error.HTTPError("https://source", 404, "missing", {}, None)]).download(
                "https://source", self.root / "missing.json", journal)

    def test_retry_exhaustion_and_partial_body_retained(self):
        journal = Journal(self.root)
        client = queue_client([Response(b"short", length=20), Response(b"short", length=20)], attempts=2)
        with self.assertRaises(Exception):
            client.download("https://source", self.root / "partial.json", journal)
        self.assertFalse((self.root / "partial.json").exists())
        self.assertEqual(len(list(self.root.glob("*.partial"))), 2)

    def test_timeout_retried_and_bounded(self):
        journal = Journal(self.root)
        with self.assertRaises(TimeoutError):
            queue_client([TimeoutError("timeout"), TimeoutError("timeout")], attempts=2).download(
                "https://source", self.root / "timeout.json", journal)
        with self.assertRaises(ValueError):
            ApiClient(attempts=100)

    def test_historical_correction_and_deletion_are_classified(self):
        first = make_snapshot(self.root, self.config)
        rows = fixture_rows()[:1]
        rows[0]["nb_annulation"] = 4
        second = make_snapshot(self.root, self.config, rows)
        comparison = compare_snapshots(first, second)
        self.assertEqual(comparison["changed_unique_keys"], 1)
        self.assertEqual(comparison["removed_keys"], 1)

    def test_storage_and_os_lock(self):
        with self.assertRaises(ValueError):
            external_path(Path(__file__).parent)
        with self.assertRaises(ValueError):
            external_path(self.root / "OneDrive" / "data")
        with execution_lock(self.root, "destination"):
            with self.assertRaises(RuntimeError):
                with execution_lock(self.root, "destination"):
                    pass
        with execution_lock(self.root, "destination"):
            pass


class FakeJob:
    def __init__(self, job_id, rows=None, error=None):
        self.job_id, self.rows, self.error = job_id, rows or [], error
        self.output_rows = len(self.rows)
        self.total_bytes_processed = self.total_bytes_billed = 0

    def result(self, **kwargs):
        if self.error:
            raise self.error
        return iter(self.rows)


class FakeBigQuery:
    """Double d'état : les assertions finales lisent tables, vue et événements."""
    def __init__(self):
        self.tables, self.jobs, self.events = {}, {}, {}
        self.fail_load = self.lose_load_response = self.lose_promotion_response = False
        self.fail_audit_after_promotion = self.promoted = False
        self.query_configs = []

    def get_dataset(self, name, **kwargs):
        return SimpleNamespace(location="EU", default_table_expiration_ms=None)

    def get_table(self, name, **kwargs):
        from google.api_core.exceptions import NotFound
        if name not in self.tables:
            raise NotFound(name)
        return self.tables[name]

    def create_table(self, table, **kwargs):
        self.tables[str(table.reference)] = SimpleNamespace(
            table_type="TABLE", schema=table.schema, num_rows=0, expires=None, rows=[])
        return table

    def get_job(self, job_id, **kwargs):
        from google.api_core.exceptions import NotFound
        if job_id not in self.jobs:
            raise NotFound(job_id)
        return self.jobs[job_id]

    def load_table_from_file(self, stream, name, *, job_id, job_config, **kwargs):
        from google.api_core.exceptions import ServiceUnavailable
        from google.cloud import bigquery
        inspect.signature(bigquery.Client.load_table_from_file).bind(
            None, stream, name, job_id=job_id, job_config=job_config, **kwargs)
        if self.fail_load:
            job = FakeJob(job_id, error=ValueError("Chargement incomplet simulé"))
        else:
            rows = [json.loads(line) for line in stream]
            self.tables[name] = SimpleNamespace(table_type="TABLE", schema=job_config.schema,
                num_rows=len(rows), expires=None, rows=rows)
            job = FakeJob(job_id, rows)
        self.jobs[job_id] = job
        if self.lose_load_response:
            raise ServiceUnavailable("Réponse perdue après écriture")
        return job

    def query(self, sql, *, job_id, job_config, **kwargs):
        from google.api_core.exceptions import ServiceUnavailable
        from google.cloud import bigquery
        inspect.signature(bigquery.Client.query).bind(None, sql, job_id=job_id, job_config=job_config, **kwargs)
        self.query_configs.append(job_config)
        if "BEGIN TRANSACTION" in sql:
            if self.fail_audit_after_promotion and self.promoted:
                raise ServiceUnavailable("Audit momentanément indisponible")
            for row in json.loads(job_config.query_parameters[0].value):
                key = (row["attempt_id"], row["sequence"])
                if key in self.events and self.events[key] != row:
                    raise ValueError("Evenement existant different")
                self.events[key] = row
            job = FakeJob(job_id)
        elif sql.startswith("CREATE OR REPLACE VIEW"):
            name = sql.split("`")[1]
            query = sql.split(" AS ", 1)[1]
            self.tables[name] = SimpleNamespace(table_type="VIEW", view_query=query)
            self.promoted = True
            job = FakeJob(job_id)
            self.jobs[job_id] = job
            if self.lose_promotion_response:
                raise ServiceUnavailable("Réponse de promotion perdue")
        else:
            name = sql.split("`")[1]
            rows = sorted(self.tables[name].rows, key=lambda row: row["row_number"])
            job = FakeJob(job_id, [SimpleNamespace(**row) for row in rows])
        self.jobs[job_id] = job
        return job


class WarehouseTests(unittest.TestCase):
    def setUp(self):
        from sncf_reliability.warehouse import Warehouse
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.config = read_config()
        self.client = FakeBigQuery()
        self.warehouse = Warehouse("sncf-test-project", client=self.client)
        self.snapshot = make_snapshot(self.root, self.config)

    def load(self, snapshot=None):
        journal = Journal(self.root, context=self.warehouse.context)
        return self.warehouse.load(snapshot or self.snapshot, journal), journal

    def test_same_content_reused_and_attempts_preserved(self):
        first, journal = self.load()
        second, other = self.load()
        self.assertEqual(first["table_id"], second["table_id"])
        self.assertTrue(second["reused"])
        self.assertFalse(second["promotion_changed"])
        self.assertNotEqual(journal.attempt_id, other.attempt_id)
        self.assertEqual(self.client.tables[first["table_id"]].num_rows, 2)
        self.assertTrue(all(config.maximum_bytes_billed == 100_000_000 for config in self.client.query_configs))

    def test_correction_deletion_and_archive_history(self):
        first, _ = self.load()
        rows = fixture_rows()[:1]
        rows[0]["nb_annulation"] = 8
        second_snapshot = make_snapshot(self.root, self.config, rows)
        second, _ = self.load(second_snapshot)
        self.assertEqual(self.client.tables[first["table_id"]].num_rows, 2)
        self.assertEqual(self.client.tables[second["table_id"]].num_rows, 1)
        self.assertIn(second["table_id"], self.client.tables[self.warehouse.current].view_query)

    def test_incomplete_load_preserves_current(self):
        first, _ = self.load()
        before = self.client.tables[self.warehouse.current].view_query
        self.client.fail_load = True
        rows = fixture_rows()[:1]
        with self.assertRaisesRegex(ValueError, "incomplet"):
            self.load(make_snapshot(self.root, self.config, rows))
        self.assertEqual(before, self.client.tables[self.warehouse.current].view_query)

    def test_same_count_corrupt_cloud_payload_rejected_before_promotion(self):
        result, _ = self.load()
        self.client.tables[result["table_id"]].rows[0]["payload"] = "{}"
        with self.assertRaisesRegex(ValueError, "Contenu BigQuery différent"):
            self.load()

    def test_lost_load_and_promotion_responses_recover_same_jobs(self):
        self.client.lose_load_response = self.client.lose_promotion_response = True
        result, _ = self.load()
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len([name for name in self.client.tables if "_v_" in name]), 1)

    def test_audit_pending_can_be_reconciled_without_changing_current(self):
        self.client.fail_audit_after_promotion = True
        journal = Journal(self.root, context=self.warehouse.context)
        with self.assertRaises(Exception):
            self.warehouse.load(self.snapshot, journal)
        events = (journal.path / "events.jsonl").read_text(encoding="utf-8")
        self.assertIn('"event":"audit_pending"', events)
        before = self.client.tables[self.warehouse.current].view_query
        self.client.fail_audit_after_promotion = False
        result = self.warehouse.reconcile(journal.path)
        self.assertTrue(result["current_points_to_attempt_version"])
        self.assertEqual(before, self.client.tables[self.warehouse.current].view_query)

    def test_audit_sync_is_durable_and_detects_changed_history(self):
        _, journal = self.load()
        count = len(self.client.events)
        self.client.jobs.clear()  # Simule l'expiration des métadonnées des jobs.
        self.warehouse.sync_audit(journal.path)
        self.assertEqual(count, len(self.client.events))
        path = journal.path / "events.jsonl"
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        records[0]["details"]["tampered"] = True
        path.write_text("\n".join(canonical(record) for record in records) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Evenement"):
            self.warehouse.sync_audit(journal.path)

    def test_current_table_not_overwritten(self):
        self.client.tables[self.warehouse.current] = SimpleNamespace(table_type="TABLE")
        with self.assertRaisesRegex(ValueError, "n'est pas une vue"):
            self.load()

    def test_cloud_schema_drift_does_not_replace_current(self):
        first, _ = self.load()
        before = self.client.tables[self.warehouse.current].view_query
        self.client.tables[first["table_id"]].schema = []
        with self.assertRaisesRegex(ValueError, "schéma incompatible"):
            self.load()
        self.assertEqual(before, self.client.tables[self.warehouse.current].view_query)


if __name__ == "__main__":
    unittest.main()
