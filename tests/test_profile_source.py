"""Offline regression cases for audit risks, independent of current live volumes."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import profile_source as audit


def observation(month="2026-01", **values):
    row = {k: 0 for k in audit.COUNTS + audit.CAUSES}
    row.update(date=month, gare_depart="A", gare_arrivee="B", service="National",
               nb_train_prevu=100, nb_annulation=10, nb_train_retard_arrivee=18,
               nb_train_retard_sup_30=4, nb_train_retard_sup_60=1, prct_cause_externe=100)
    row.update(values)
    return row


def metadata():
    fields = [{"name": k, "type": "int"} for k in audit.COUNTS]
    fields += [{"name": k, "type": "double"} for k in audit.CAUSES]
    fields += [{"name": k, "type": "date" if k == "date" else "text"} for k in audit.KEY]
    return {"fields": fields}


class AuditTests(unittest.TestCase):
    def test_direction_is_part_of_key(self):
        s, *_ = audit.profile([observation(), observation(gare_depart="B", gare_arrivee="A")], metadata())
        self.assertEqual((s["routes"], s["duplicate_key_groups"]), (2, 0))

    def test_exact_and_conflicting_duplicates(self):
        s, *_ = audit.profile([observation(), observation(), observation(nb_annulation=3)], metadata())
        self.assertEqual(s["exact_duplicate_excess_rows"], 1)
        self.assertEqual(s["duplicate_key_excess_rows"], 2)
        result = audit.eligibility([observation(), observation(), observation("2025-01")], "2026-01", "2026-01")
        self.assertFalse(result[0]["eligible"])

    def test_absent_null_and_zero_are_distinct(self):
        s, fields, routes, *_ = audit.profile([observation("2026-01", nb_train_retard_arrivee=None),
                                               observation("2026-03", nb_train_retard_arrivee=0)], metadata())
        stat = next(x for x in fields if x["field"] == "nb_train_retard_arrivee")
        self.assertEqual((stat["null_count"], stat["zero_count"]), (1, 1))
        self.assertEqual(routes[0]["internal_missing_months"], "2026-02")

    def test_bad_counts_and_nested_thresholds(self):
        s, *_ = audit.profile([observation(nb_train_prevu=0, nb_annulation=8,
                                           nb_train_retard_sup_30=-1, nb_train_retard_sup_60=30)], metadata())
        self.assertEqual(s["anomalies_by_rule"]["invalid_count"], 1)
        self.assertEqual(s["anomalies_by_rule"]["cancelled_above_planned"], 1)
        self.assertIn("nested_counts_inconsistent", s["anomalies_by_rule"])

    def test_ratio_denominator_and_zero(self):
        self.assertEqual(audit.safe_rate(18, 90), 0.2)
        self.assertIsNone(audit.safe_rate(0, 0))
        self.assertIsNone(audit.safe_rate(None, 90))
        self.assertIsNone(audit.safe_rate(91, 90))
        self.assertIsNone(audit.safe_rate(1, -1))

    def test_coverage_and_low_volume(self):
        rows = [observation("2025-01"), observation("2026-01", nb_train_prevu=39)]
        self.assertFalse(audit.eligibility(rows, "2026-01", "2026-01")[0]["eligible"])
        rows[1]["nb_train_prevu"] = 40
        self.assertTrue(audit.eligibility(rows, "2026-01", "2026-01")[0]["eligible"])
        self.assertFalse(audit.eligibility(rows, "2026-01", "2026-02")[0]["eligible"])

    def test_year_boundary_comparison(self):
        rows = [observation(m) for m in ["2024-12", "2025-01", "2025-12", "2026-01"]]
        self.assertTrue(audit.eligibility(rows, "2025-12", "2026-01")[0]["eligible"])

    def test_service_changes_are_not_merged(self):
        rows = [observation("2025-01", service="International"), observation()]
        changes, s = audit.scope_profile(rows)
        self.assertEqual(s["pairs_with_multiple_services"], 1)
        self.assertEqual(s["pairs_with_simultaneous_services"], 0)
        self.assertFalse(audit.eligibility(rows, "2026-01", "2026-01")[0]["eligible"])

    def test_simultaneous_services_require_review(self):
        rows = [observation("2025-01"), observation(), observation(service="International")]
        result = audit.eligibility(rows, "2026-01", "2026-01")[0]
        self.assertFalse(result["eligible"])
        self.assertIn("service_scope_requires_review", result["reasons"])

    def test_no_cause_volume_reconstruction(self):
        row = observation(**{k: 0 for k in audit.CAUSES})
        original = copy.deepcopy(row)
        s, *_ = audit.profile([row], metadata())
        self.assertEqual(s["all_zero_causes_with_arrival_delays"], 1)
        self.assertEqual(row, original)

    def test_invalid_month_and_missing_schema(self):
        with self.assertRaises(ValueError):
            audit.month_number("2026-13")
        with self.assertRaises(ValueError):
            audit.profile([observation()], {"fields": []})

    def test_checksum_detects_tampering_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.json").write_text("[]", encoding="utf8")
            audit.write_json(root / "manifest.json", {"status": "complete", "files": {
                "source.json": {"sha256": audit.digest(root / "source.json")}}})
            with patch("urllib.request.urlopen", side_effect=AssertionError("Network forbidden")):
                audit.verify_snapshot(root)
                (root / "source.json").write_text("[{}]", encoding="utf8")
                with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
                    audit.verify_snapshot(root)

    def test_incomplete_export_preserves_failed_snapshot(self):
        def fake_download(url, path):
            value = [observation()] if path.name == "source.json" else {
                "fields": metadata()["fields"], "metas": {"default": {
                    "records_count": 2, "modified": "fixed", "data_processed": "fixed"}}}
            audit.write_json(path, value)
            return {"url": url, "sha256": audit.digest(path), "retrieved_at_utc": "test"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(audit, "download", side_effect=fake_download):
                with self.assertRaisesRegex(ValueError, "incomplete"):
                    audit.capture(root)
            manifests = list(root.glob("audit/*/manifest.json"))
            self.assertEqual(len(manifests), 1)
            manifest = audit.read_json(manifests[0])
            self.assertEqual(manifest["status"], "failed")
            self.assertFalse(manifest["extraction_checks"]["count_matches"])
            self.assertTrue((manifests[0].parent / "source.json").exists())


if __name__ == "__main__":
    unittest.main()
