"""J01: snapshot and profile SNCF data with Python's standard library only.

This is an audit, not the production ingestion pipeline or the analytical model.
No source values are corrected. Replay never accesses the network.
"""

import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import sys
import unicodedata
import urllib.request

DATASET = "regularite-mensuelle-tgv-aqst"
BASE = "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/" + DATASET
KEY = ("date", "gare_depart", "gare_arrivee", "service")
COUNTS = ("nb_train_prevu", "nb_annulation", "nb_train_depart_retard",
          "nb_train_retard_arrivee", "nb_train_retard_sup_15",
          "nb_train_retard_sup_30", "nb_train_retard_sup_60")
CAUSES = ("prct_cause_externe", "prct_cause_infra", "prct_cause_gestion_trafic",
          "prct_cause_materiel_roulant", "prct_cause_gestion_gare",
          "prct_cause_prise_en_charge_voyageurs")
EVIDENCE = {
    "source_information.html": "https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/",
    "aqst_definitions.html": "https://www.qualitetransports.gouv.fr/definition-des-indicateurs-et-chiffres-de-la-a460.html",
    "aqst_2022.pdf": "https://www.qualitetransports.gouv.fr/IMG/pdf/bilan_aqst_2022_ok.pdf",
    "sncf_terms.html": "https://ressources.data.sncf.com/pages/cgu/",
    "odbl.html": "https://opendatacommons.org/licenses/odbl/1-0/",
}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def download(url, path):
    request = urllib.request.Request(url, headers={"User-Agent": "SNCF-Portfolio-J01/1.0"})
    # Retain a partial download if transport fails; never treat it as a valid export.
    partial = path.with_suffix(path.suffix + ".partial")
    with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as out:
        while chunk := response.read(1024 * 1024):
            out.write(chunk)
    partial.replace(path)
    return {"url": url, "retrieved_at_utc": now(), "sha256": digest(path),
            "bytes": path.stat().st_size}


def default_data_dir():
    configured = os.environ.get("SNCF_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise ValueError("Set SNCF_DATA_DIR when LOCALAPPDATA is unavailable.")
    return Path(local) / "SNCF_Service_Reliability_Analytics" / "data"


def capture(data_dir):
    root = data_dir.resolve()
    repo = Path(__file__).resolve().parents[1]
    if root == repo or repo in root.parents:
        raise ValueError("Audit exports must be outside the project directory.")
    snapshot = root / "audit" / dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    snapshot.mkdir(parents=True, exist_ok=False)
    manifest = {"dataset_id": DATASET, "started_at_utc": now(), "status": "in_progress",
                "files": {}, "python_version": platform.python_version(),
                "capture_script_sha256": digest(__file__)}
    write_json(snapshot / "manifest.json", manifest)
    try:
        for filename, url in [("metadata_before.json", BASE),
                              ("source.json", BASE + "/exports/json"),
                              ("metadata_after.json", BASE)]:
            manifest["files"][filename] = download(url, snapshot / filename)
            write_json(snapshot / "manifest.json", manifest)
        before = read_json(snapshot / "metadata_before.json")
        after = read_json(snapshot / "metadata_after.json")
        rows = read_json(snapshot / "source.json")
        if not isinstance(rows, list) or not rows or not all(isinstance(r, dict) for r in rows):
            raise ValueError("Expected a non-empty JSON array of records.")
        mb, ma = before["metas"]["default"], after["metas"]["default"]
        checks = {"count_matches": len(rows) == mb["records_count"] == ma["records_count"],
                  "source_stable": all(mb.get(k) == ma.get(k) for k in
                                       ("modified", "data_processed", "records_count")),
                  "schema_stable": before["fields"] == after["fields"]}
        manifest.update({"extraction_checks": checks, "record_count": len(rows),
                         "source_modified": ma.get("modified"),
                         "source_data_processed": ma.get("data_processed"),
                         "source_metadata_processed": ma.get("metadata_processed"),
                         "snapshot_id": snapshot.name,
                         "source_sha256": digest(snapshot / "source.json")})
        if not all(checks.values()):
            raise ValueError("Source changed during capture or export is incomplete.")
        for filename, url in EVIDENCE.items():
            try:
                manifest["files"][filename] = download(url, snapshot / filename)
            except Exception as error:
                manifest.setdefault("evidence_errors", {})[filename] = str(error)
        manifest.update(status="complete", completed_at_utc=now())
        write_json(snapshot / "manifest.json", manifest)
        return snapshot
    except Exception as error:
        manifest.update(status="failed", error=str(error), completed_at_utc=now())
        write_json(snapshot / "manifest.json", manifest)
        raise


def verify_snapshot(snapshot):
    manifest = read_json(snapshot / "manifest.json")
    if manifest["status"] != "complete":
        raise ValueError("Snapshot is not complete.")
    for filename, entry in manifest["files"].items():
        candidate = (snapshot / filename).resolve()
        if snapshot.resolve() not in candidate.parents:
            raise ValueError("Invalid manifest path.")
        if digest(candidate) != entry["sha256"]:
            raise ValueError("Checksum mismatch: " + filename)
    return manifest


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def integer(value):
    return numeric(value) and value == int(value)


def month_number(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}", value):
        raise ValueError("Month must be YYYY-MM.")
    year, month = map(int, value.split("-"))
    if not 1 <= year <= 9999 or not 1 <= month <= 12:
        raise ValueError("Invalid month.")
    return year * 12 + month - 1


def month_label(number):
    return f"{number // 12:04d}-{number % 12 + 1:02d}"


def safe_rate(numerator, denominator):
    if not numeric(numerator) or not numeric(denominator) or denominator <= 0:
        return None
    if not 0 <= numerator <= denominator:
        return None
    return numerator / denominator


def valid_counts(row):
    p, a, l = (row.get(k) for k in ("nb_train_prevu", "nb_annulation", "nb_train_retard_arrivee"))
    return all(integer(v) for v in (p, a, l)) and p >= a >= 0 and 0 <= l <= p - a


def profile(rows, metadata):
    if not rows:
        raise ValueError("Empty input.")
    fields = {f["name"]: f for f in metadata["fields"]}
    missing_required = set(KEY + COUNTS + CAUSES) - fields.keys()
    if missing_required:
        raise ValueError("Missing required schema fields: " + str(sorted(missing_required)))
    keys = collections.Counter(tuple(r.get(k) for k in KEY) for r in rows)
    exact = collections.Counter(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    anomalies, groups, observed_months = [], collections.defaultdict(list), set()

    def flag(index, row, rule, detail):
        anomalies.append({"row_number": index, **{k: row.get(k) for k in KEY},
                          "rule": rule, "detail": detail})

    for index, row in enumerate(rows, 1):
        if set(row) != set(fields):
            flag(index, row, "row_schema_mismatch", str(sorted(set(row) ^ set(fields))))
        for name, field in fields.items():
            v = row.get(name)
            if v is None:
                continue
            ok = {"int": integer, "double": numeric,
                  "text": lambda x: isinstance(x, str),
                  "date": lambda x: isinstance(x, str)}[field["type"]](v)
            if not ok:
                flag(index, row, "invalid_type", name)
        if any(row.get(k) in (None, "") for k in KEY):
            flag(index, row, "missing_key", "Incomplete candidate key")
            continue
        try:
            month = month_number(row["date"])
        except ValueError:
            flag(index, row, "invalid_month", str(row["date"]))
            continue
        observed_months.add(month)
        groups[tuple(row[k] for k in KEY[1:])].append(row)
        if keys[tuple(row[k] for k in KEY)] > 1:
            flag(index, row, "duplicate_key", "Do not deduplicate automatically")
        for name in COUNTS:
            v = row.get(name)
            if v is not None and (not integer(v) or v < 0):
                flag(index, row, "invalid_count", name)
        p, a = row.get("nb_train_prevu"), row.get("nb_annulation")
        if numeric(p) and numeric(a):
            if a > p:
                flag(index, row, "cancelled_above_planned", f"{a} > {p}")
            if p == 0:
                flag(index, row, "zero_planned", "Cancellation rate unavailable")
            if p - a == 0:
                flag(index, row, "zero_operated_proxy", "Delay rate unavailable")
            for name in COUNTS[2:]:
                if numeric(row.get(name)) and row[name] > p - a:
                    flag(index, row, "delay_above_operated_proxy", name)
        for lower, upper in [("nb_train_retard_sup_60", "nb_train_retard_sup_30"),
                             ("nb_train_retard_sup_30", "nb_train_retard_arrivee")]:
            if numeric(row.get(lower)) and numeric(row.get(upper)) and row[lower] > row[upper]:
                flag(index, row, "nested_counts_inconsistent", lower + " > " + upper)
        cause_values = [row.get(k) for k in CAUSES]
        for name in CAUSES:
            if row.get(name) is not None and (not numeric(row[name]) or not 0 <= row[name] <= 100):
                flag(index, row, "cause_out_of_range", name)
        if all(numeric(v) for v in cause_values) and abs(sum(cause_values) - 100) > 0.1:
            flag(index, row, "cause_sum_not_100", str(sum(cause_values)))
        for name in fields:
            if (name.startswith("retard_moyen") or name == "duree_moyenne") and numeric(row.get(name)) and row[name] < 0:
                flag(index, row, "negative_duration_or_mean", name)

    if not observed_months:
        raise ValueError("No valid months.")
    first, last = min(observed_months), max(observed_months)
    routes = []
    for key, items in sorted(groups.items()):
        months = {month_number(r["date"]) for r in items}
        lo, hi = min(months), max(months)
        absent = [month_label(m) for m in range(lo, hi + 1) if m not in months]
        routes.append(dict(zip(KEY[1:], key)) | {
            "rows": len(items), "observed_months": len(months),
            "first_month": month_label(lo), "last_month": month_label(hi),
            "internal_missing_count": len(absent), "internal_missing_months": ";".join(absent),
            "months_before_first": lo - first, "months_after_last": last - hi})
    field_stats = []
    for name, field in fields.items():
        values = [r.get(name) for r in rows]
        numbers = [v for v in values if numeric(v)]
        field_stats.append({"field": name, "declared_type": field["type"],
                            "null_count": sum(v is None for v in values),
                            "empty_string_count": sum(v == "" for v in values),
                            "zero_count": sum(numeric(v) and v == 0 for v in values),
                            "distinct_non_null": len({v for v in values if v is not None}),
                            "minimum": min(numbers) if numbers else None,
                            "maximum": max(numbers) if numbers else None})
    monthly = collections.Counter((r["date"], r["service"]) for values in groups.values() for r in values)
    summary = {
        "records": len(rows), "fields": len(fields), "candidate_key": list(KEY),
        "duplicate_key_groups": sum(n > 1 for n in keys.values()),
        "duplicate_key_excess_rows": sum(n - 1 for n in keys.values()),
        "exact_duplicate_excess_rows": sum(n - 1 for n in exact.values()),
        "first_month": month_label(first), "last_month": month_label(last),
        "global_observed_months": len(observed_months), "global_expected_months": last - first + 1,
        "routes": len(routes), "services": dict(collections.Counter(r.get("service") for r in rows)),
        "routes_by_service": dict(collections.Counter(r["service"] for r in routes)),
        "internal_missing_route_months": sum(r["internal_missing_count"] for r in routes),
        "routes_with_internal_gaps": sum(r["internal_missing_count"] > 0 for r in routes),
        "routes_starting_after_global_first": sum(r["months_before_first"] > 0 for r in routes),
        "routes_ending_before_global_last": sum(r["months_after_last"] > 0 for r in routes),
        "anomalies_by_rule": dict(sorted(collections.Counter(a["rule"] for a in anomalies).items())),
        "distinct_rows_by_rule": {rule: len({a["row_number"] for a in anomalies if a["rule"] == rule})
                                  for rule in sorted({a["rule"] for a in anomalies})},
        "valid_core_count_rows": sum(valid_counts(r) for r in rows),
        "complete_cause_profiles": sum(all(numeric(r.get(k)) for k in CAUSES) for r in rows),
        "all_zero_cause_profiles": sum(all(r.get(k) == 0 for k in CAUSES) for r in rows),
        "all_zero_causes_with_arrival_delays": sum(all(r.get(k) == 0 for k in CAUSES)
                                                  and numeric(r.get("nb_train_retard_arrivee"))
                                                  and r["nb_train_retard_arrivee"] > 0 for r in rows),
    }
    return summary, field_stats, routes, anomalies, [
        {"month": m, "service": s, "rows": n} for (m, s), n in sorted(monthly.items())]


def eligibility(rows, start, end, minimum_monthly=30):
    """Coverage screening only; no performance ranking or production KPI materialization."""
    lo, hi = month_number(start), month_number(end)
    if hi < lo or hi - lo >= 12:
        raise ValueError("Comparison window must contain between 1 and 12 months.")
    current = {month_label(m) for m in range(lo, hi + 1)}
    previous = {month_label(m - 12) for m in range(lo, hi + 1)}
    groups = collections.defaultdict(lambda: collections.defaultdict(list))
    services_in_window = collections.defaultdict(set)
    for row in rows:
        if row.get("date") in current | previous:
            services_in_window[(row.get("gare_depart"), row.get("gare_arrivee"))].add(row.get("service"))
        if row.get("service") == "National" and all(row.get(k) for k in KEY):
            groups[tuple(row[k] for k in KEY[1:])][row["date"]].append(row)
    result = []
    for key, months in sorted(groups.items()):
        reasons, totals = [], {}
        if len(services_in_window[key[:2]]) > 1:
            reasons.append("service_scope_requires_review")
        for label, expected in [("current", current), ("previous", previous)]:
            total = 0
            for month in sorted(expected):
                observations = months.get(month, [])
                if len(observations) != 1:
                    reasons.append(label + ":missing_or_duplicate_month")
                    continue
                r = observations[0]
                if not valid_counts(r):
                    reasons.append(label + ":invalid_core_counts")
                    continue
                operated = r["nb_train_prevu"] - r["nb_annulation"]
                total += operated
                if operated < minimum_monthly:
                    reasons.append(label + ":low_monthly_volume")
            totals[label + "_operated_proxy"] = total
        result.append(dict(zip(KEY[1:], key)) | totals | {
            "eligible": not reasons, "reasons": ";".join(sorted(set(reasons)))})
    return result


def scope_profile(rows):
    pairs, stations = collections.defaultdict(lambda: collections.defaultdict(set)), set()
    for row in rows:
        if any(not row.get(k) for k in KEY):
            continue
        pairs[(row["gare_depart"], row["gare_arrivee"])][row["service"]].add(row["date"])
        stations.update((row["gare_depart"], row["gare_arrivee"]))
    changes = []
    for pair, services in sorted(pairs.items()):
        if len(services) < 2:
            continue
        overlap = set.intersection(*services.values())
        for service, months in sorted(services.items()):
            changes.append({"gare_depart": pair[0], "gare_arrivee": pair[1], "service": service,
                            "first_month": min(months), "last_month": max(months),
                            "observed_months": len(months), "overlapping_months": len(overlap)})
    normalized = collections.defaultdict(list)
    for station in sorted(stations):
        name = unicodedata.normalize("NFKD", station.casefold())
        name = "".join(c for c in name if c.isalnum())
        normalized[name].append(station)
    collisions = [values for values in normalized.values() if len(values) > 1]
    return changes, {"station_labels": len(stations),
                     "station_normalization_collisions": collisions,
                     "oriented_pairs": len(pairs),
                     "pairs_with_multiple_services": len({(x['gare_depart'], x['gare_arrivee']) for x in changes}),
                     "pairs_with_simultaneous_services": len({(x['gare_depart'], x['gare_arrivee']) for x in changes if x['overlapping_months']})}


def write_csv(path, rows, columns=None):
    columns = columns or list(rows[0])
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def run(snapshot, output, start, end, minimum_monthly):
    manifest = verify_snapshot(snapshot)
    rows, metadata = read_json(snapshot / "source.json"), read_json(snapshot / "metadata_after.json")
    summary, fields, routes, anomalies, monthly = profile(rows, metadata)
    scope, scope_summary = scope_profile(rows)
    eligible = eligibility(rows, start, end, minimum_monthly)
    summary.update({"snapshot_id": manifest["snapshot_id"], "source_sha256": manifest["source_sha256"],
                    "extracted_at_utc": manifest["files"]["source.json"]["retrieved_at_utc"],
                    "source_modified": manifest["source_modified"],
                    "source_metadata_processed": manifest["source_metadata_processed"],
                    "profile_script_sha256": digest(__file__),
                    "comparison": {"start": start, "end": end, "previous_year_same_months": True,
                                   "minimum_monthly_operated_proxy": minimum_monthly,
                                   "national_routes": len(eligible),
                                   "eligible_national_routes": sum(r["eligible"] for r in eligible)}})
    summary["scope"] = scope_summary
    summary["coverage_sensitivity"] = {
        str(threshold): sum(r["eligible"] for r in eligibility(rows, start, end, threshold))
        for threshold in (15, 30, 60)}
    annual = eligibility(rows, "2025-01", "2025-12", minimum_monthly)
    summary["annual_comparison"] = {"current": "2025-01/2025-12", "previous": "2024-01/2024-12",
                                    "eligible_national_routes": sum(r["eligible"] for r in annual)}
    output = output.resolve()
    if output == snapshot.resolve() or snapshot.resolve() in output.parents:
        raise ValueError("Write results outside the immutable snapshot.")
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "summary.json", summary)
    write_csv(output / "fields.csv", fields)
    write_csv(output / "routes.csv", routes)
    write_csv(output / "monthly_coverage.csv", monthly)
    write_csv(output / "service_scope.csv", scope, [*KEY[1:], "first_month", "last_month",
              "observed_months", "overlapping_months"])
    write_csv(output / "anomalies.csv", anomalies,
              ["row_number", *KEY, "rule", "detail"])
    write_csv(output / "eligibility.csv", eligible, [*KEY[1:], "current_operated_proxy",
              "previous_operated_proxy", "eligible", "reasons"])
    write_json(output / "provenance.json", {"snapshot_id": manifest["snapshot_id"],
               "source_sha256": manifest["source_sha256"], "files": manifest["files"],
               "extraction_checks": manifest["extraction_checks"],
               "evidence_errors": manifest.get("evidence_errors", {})})
    write_csv(output / "eligibility_2025_vs_2024.csv", annual, [*KEY[1:], "current_operated_proxy",
              "previous_operated_proxy", "eligible", "reasons"])
    print(json.dumps({"snapshot": str(snapshot), "output": str(output), "summary": summary},
                     ensure_ascii=True, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fetch", action="store_true", help="Capture a new immutable snapshot")
    mode.add_argument("--snapshot", type=Path, help="Replay a complete snapshot, without network")
    parser.add_argument("--data-dir", type=Path, help="Override SNCF_DATA_DIR")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/audit_evidence"))
    parser.add_argument("--comparison-start", default="2026-01")
    parser.add_argument("--comparison-end", default="2026-06")
    parser.add_argument("--minimum-monthly", type=int, default=30)
    args = parser.parse_args()
    if args.minimum_monthly < 1:
        parser.error("--minimum-monthly must be positive")
    snapshot = capture(args.data_dir or default_data_dir()) if args.fetch else args.snapshot.resolve()
    run(snapshot, args.output_dir, args.comparison_start, args.comparison_end, args.minimum_monthly)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        print(f"Audit failed: {error}", file=sys.stderr)
        sys.exit(1)
