"""Produire la preuve locale J03 ; aucun appel SNCF ou BigQuery."""

import argparse
import collections
from decimal import Decimal
import json
from pathlib import Path
import platform
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sncf_reliability.ingest import (REPO, compare_snapshots, now, read_config, sha256,
                                     strict_json, verify_snapshot, write_json)


def numeric_precision_review(previous, current):
    def grouped(snapshot):
        raw = (snapshot.path / "source.json").read_bytes()
        if sha256(raw) != snapshot.context["source_sha256"]:
            raise ValueError("Source modifiée après vérification.")
        result = collections.defaultdict(list)
        for row in json.loads(raw, parse_float=Decimal):
            key = tuple(row[name] for name in ("date", "gare_depart", "gare_arrivee", "service"))
            result[key].append(row)
        return result
    old, new = grouped(previous), grouped(current)
    deltas, non_numeric = collections.defaultdict(list), 0
    for key in old.keys() & new.keys():
        if len(old[key]) != 1 or len(new[key]) != 1:
            continue
        for field, value in old[key][0].items():
            other = new[key][0][field]
            if value == other:
                continue
            if isinstance(value, (int, Decimal)) and isinstance(other, (int, Decimal)):
                deltas[field].append(abs(Decimal(other) - Decimal(value)))
            else:
                non_numeric += 1
    return {"method": "Comparaison Decimal des valeurs JSON originales, sans seuil de tolérance analytique.",
            "previous_version_id": previous.version_id, "current_version_id": current.version_id,
            "fields": {field: {"changed_values": len(values), "maximum_absolute_decimal_difference": str(max(values))}
                       for field, values in sorted(deltas.items())},
            "changed_non_numeric_values": non_numeric,
            "changed_train_count_values": sum(len(values) for field, values in deltas.items() if field.startswith("nb_")),
            "largest_absolute_decimal_difference": str(max((max(values) for values in deltas.values()), default=Decimal(0)))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--previous", required=True)
    parser.add_argument("--output", default="reports/ingestion_evidence")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    config = read_config()
    snapshot = verify_snapshot(args.snapshot, config)
    previous = verify_snapshot(args.previous, config)
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                           cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = tests.stdout + tests.stderr
    (output / "tests.txt").write_text(log, encoding="utf-8")
    paths = sorted((REPO / "src/sncf_reliability").glob("*.py"))
    paths += sorted((REPO / "scripts").glob("*ingestion*.py"))
    paths += [REPO / "tests/test_ingestion.py", REPO / "tests/fixtures/ingestion_rows.json",
              REPO / "config/datasets.yaml", REPO / "pyproject.toml", REPO / "uv.lock"]
    hashes = {path.relative_to(REPO).as_posix(): sha256(path.read_bytes()) for path in paths}
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=REPO, capture_output=True, text=True)
    commit = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=REPO, capture_output=True, text=True)
    report = {"validated_at_utc": now(), "scope": "local_only", "python_version": platform.python_version(),
              "tests": {"command": "python -m unittest discover -s tests -v", "return_code": tests.returncode,
                        "log": "tests.txt", "log_sha256": sha256((output / "tests.txt").read_bytes())},
              "snapshot": {**snapshot.context, **snapshot.checks},
              "previous_snapshot": {**previous.context, **previous.checks},
              "comparison": compare_snapshots(previous, snapshot), "code_sha256": hashes,
              "git_branch": branch.stdout.strip(), "git_commit": commit.stdout.strip() if commit.returncode == 0 else None}
    cloud = output / "cloud_scenarios.json"
    if cloud.exists():
        evidence = strict_json(cloud.read_bytes())
        current = {path: value for path, value in hashes.items() if path.startswith("src/")}
        recorded = {path.replace("\\", "/"): value for path, value in evidence.get("code_sha256", {}).items()}
        report["recorded_cloud_scenarios"] = {"file": cloud.name, "sha256": sha256(cloud.read_bytes()),
            "status": evidence.get("status"), "code_matches": current == recorded,
            "note": "Preuve archivée ; cette commande ne renouvelle pas la vérification cloud."}
    report["status"] = "passed" if tests.returncode == 0 else "failed"
    write_json(output / "validation.json", report)
    write_json(output / "source_comparison.json", report["comparison"])
    write_json(output / "numeric_precision_review.json", numeric_precision_review(previous, snapshot))
    print(json.dumps({"status": report["status"], "evidence": str(output / "validation.json"),
                      "comparison": report["comparison"]}, ensure_ascii=False, indent=2))
    return tests.returncode


if __name__ == "__main__":
    raise SystemExit(main())
