"""Archives vérifiées, identité de contenu et journaux locaux, sans logique KPI."""

from __future__ import annotations

import collections
import contextlib
import hashlib
import json
import math
import os
import platform
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
KEY = ("date", "gare_depart", "gare_arrivee", "service")


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256(value: bytes):
    return hashlib.sha256(value).hexdigest()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Clé JSON répétée : " + key)
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("Constante JSON non finie : " + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def external_path(path):
    resolved = Path(path).expanduser().resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError("Les archives et journaux doivent être hors du dépôt.")
    roots = [os.environ.get(name) for name in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial")]
    if any("onedrive" in part.casefold() for part in resolved.parts):
        raise ValueError("Le stockage des données doit être hors OneDrive.")
    for root in filter(None, roots):
        sync = Path(root).resolve()
        if resolved == sync or sync in resolved.parents:
            raise ValueError("Le stockage des données doit être hors OneDrive.")
    return resolved


def data_root(value=None):
    selected = value or os.getenv("SNCF_DATA_DIR")
    if not selected:
        local = os.getenv("LOCALAPPDATA")
        if not local:
            raise ValueError("Définir SNCF_DATA_DIR en dehors de Windows.")
        selected = Path(local) / "SNCF_Service_Reliability_Analytics" / "data"
    return external_path(selected)


def read_config(path=REPO / "config/datasets.yaml"):
    import yaml

    config = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if config.get("dataset_id") != "regularite-mensuelle-tgv-aqst":
        raise ValueError("Seule la source TGV prévue par J03 est autorisée.")
    if config.get("base_url") != "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets":
        raise ValueError("URL source non conforme à la V1.")
    fields = config.get("fields")
    if not isinstance(fields, dict) or not set(KEY) <= fields.keys():
        raise ValueError("Configuration de schéma invalide.")
    if not all(isinstance(name, str) and kind in {"int", "double", "text", "date"}
               for name, kind in fields.items()):
        raise ValueError("Type de schéma inconnu.")
    return config


class Journal:
    def __init__(self, root, *, attempt_id=None, context=None):
        self.attempt_id = attempt_id or uuid.uuid4().hex
        if not re.fullmatch(r"[a-f0-9]{32}", self.attempt_id):
            raise ValueError("Identifiant de tentative invalide.")
        self.path = external_path(root) / "attempts" / self.attempt_id
        self.path.mkdir(parents=True, exist_ok=False)
        self.context = dict(context or {})
        self.sequence = 0
        write_json(self.path / "attempt.json", {"attempt_id": self.attempt_id, "started_at_utc": now(),
                                                **self.context})

    @classmethod
    def reopen(cls, path):
        path = external_path(path)
        attempt = strict_json((path / "attempt.json").read_bytes())
        records = [strict_json(line) for line in (path / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        if path.name != attempt["attempt_id"] or any(
                record["attempt_id"] != attempt["attempt_id"] or record["sequence"] != index
                for index, record in enumerate(records, 1)):
            raise ValueError("Journal local incohérent.")
        journal = cls.__new__(cls)
        journal.path, journal.attempt_id, journal.sequence = path, attempt["attempt_id"], len(records)
        journal.context = records[-1]["context"] if records else {}
        return journal

    def emit(self, event, **details):
        self.sequence += 1
        record = {"attempt_id": self.attempt_id, "sequence": self.sequence,
                  "event_at": now(), "event": event, "context": dict(self.context), "details": details}
        with (self.path / "events.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical(record) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        return record


@contextlib.contextmanager
def execution_lock(root, scope):
    """Verrou OS libéré à la sortie du processus ; le fichier témoin peut rester."""
    directory = external_path(root) / ".locks"
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / (sha256(scope.encode()) + ".lock")).open("a+b") as stream:
        stream.seek(0, 2)
        if not stream.tell():
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RuntimeError("Une ingestion utilise déjà ce stockage et cette destination.") from error
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def inspect_source(before, after, rows, config):
    dataset_id = config["dataset_id"]
    for metadata in (before, after):
        if metadata.get("dataset_id") != dataset_id:
            raise ValueError("Identifiant source inattendu.")
        fields = metadata.get("fields", [])
        if len({field["name"] for field in fields}) != len(fields):
            raise ValueError("Champs répétés dans les métadonnées.")
        if {field["name"]: field["type"] for field in fields} != config["fields"]:
            raise ValueError("Schéma source incompatible avec config/datasets.yaml.")
    mb, ma = (metadata["metas"]["default"] for metadata in (before, after))
    markers = ("modified", "data_processed", "records_count")
    if any(mb.get(name) is None or ma.get(name) is None for name in markers):
        raise ValueError("Marqueur source absent : cohérence non vérifiable.")
    if any(mb[name] != ma[name] for name in markers) or before["fields"] != after["fields"]:
        raise ValueError("Source modifiée pendant l'extraction.")
    if type(ma["records_count"]) is not int or ma["records_count"] <= 0:
        raise ValueError("Effectif source nul ou invalide ; promotion refusée.")
    if not isinstance(rows, list) or len(rows) != ma["records_count"]:
        raise ValueError("Export incomplet : effectif reçu différent de l'effectif attendu.")
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict) or set(row) != set(config["fields"]):
            raise ValueError(f"Structure incompatible à la ligne {index}.")
        for name, kind in config["fields"].items():
            value = row[name]
            if value is None:
                continue
            valid = (isinstance(value, str) if kind in {"text", "date"} else
                     type(value) is int if kind == "int" else
                     type(value) in {int, float} and math.isfinite(value))
            if not valid:
                raise ValueError(f"Type incompatible à la ligne {index}, champ {name}.")
    months = [row["date"] for row in rows if isinstance(row["date"], str)
              and re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", row["date"])
              and not row["date"].startswith("0000")]
    return {"expected_count": ma["records_count"], "received_count": len(rows),
            "source_modified": ma["modified"], "source_data_processed": ma["data_processed"],
            "schema_sha256": sha256(canonical(config["fields"]).encode()),
            "first_business_month": min(months, default=None), "last_business_month": max(months, default=None),
            "missing_or_invalid_months": len(rows) - len(months)}


@dataclass
class Snapshot:
    path: Path
    manifest: dict
    manifest_sha256: str
    rows: list
    records: list[str]
    version_id: str
    checks: dict

    @property
    def context(self):
        return {"snapshot_id": self.manifest["snapshot_id"], "version_id": self.version_id,
                "dataset_id": self.manifest["dataset_id"], "manifest_sha256": self.manifest_sha256,
                "source_sha256": self.manifest["files"]["source.json"]["sha256"],
                "snapshot_path": str(self.path), "received_count": len(self.rows)}


def verify_snapshot(path, config):
    path = external_path(path)
    raw_manifest = (path / "manifest.json").read_bytes()
    manifest = strict_json(raw_manifest)
    if manifest.get("status") != "complete" or manifest.get("dataset_id") != config["dataset_id"]:
        raise ValueError("Archive incomplète ou source incompatible.")
    if manifest.get("format_version") not in (None, 1):
        raise ValueError("Version du manifeste non prise en charge.")
    files = manifest["files"]
    required = {"source.json", "metadata_before.json", "metadata_after.json"}
    if not required <= files.keys():
        raise ValueError("Pièce obligatoire absente du manifeste.")
    loaded = {}
    for name, entry in files.items():
        candidate = (path / name).resolve()
        if candidate.parent != path:
            raise ValueError("Chemin de manifeste invalide.")
        raw = candidate.read_bytes()
        if sha256(raw) != entry["sha256"] or len(raw) != entry["bytes"]:
            raise ValueError("Empreinte ou taille différente : " + name)
        if name in required:
            loaded[name] = strict_json(raw)
    checks = inspect_source(loaded["metadata_before.json"], loaded["metadata_after.json"],
                            loaded["source.json"], config)
    rows = loaded["source.json"]
    records = sorted(canonical(row) for row in rows)
    content = canonical({"dataset_id": config["dataset_id"], "fields": config["fields"],
                         "records": records}).encode()
    version_id = sha256(content)
    if manifest.get("format_version") == 1:
        if manifest.get("version_id") != version_id or manifest.get("checks") != checks:
            raise ValueError("Identité ou contrôles du manifeste incohérents.")
    else:
        # Compatibilité explicite avec l'archive J01, sans la réécrire.
        if manifest.get("source_sha256") != files["source.json"]["sha256"]:
            raise ValueError("Empreinte source J01 incohérente.")
    return Snapshot(path, manifest, sha256(raw_manifest), rows, records, version_id, checks)


def capture(root, config, client, journal):
    snapshot_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + journal.attempt_id[:8]
    path = external_path(root) / "ingestion" / snapshot_id
    path.mkdir(parents=True, exist_ok=False)
    manifest = {"format_version": 1, "dataset_id": config["dataset_id"], "snapshot_id": snapshot_id,
                "status": "in_progress", "started_at_utc": now(), "files": {},
                "python_version": platform.python_version(), "capture_attempt_id": journal.attempt_id,
                "code_sha256": {file.name: sha256(file.read_bytes()) for file in Path(__file__).parent.glob("*.py")}}
    journal.context.update(snapshot_id=snapshot_id, dataset_id=config["dataset_id"], snapshot_path=str(path))
    write_json(path / "manifest.json", manifest)
    base = config["base_url"] + "/" + config["dataset_id"]
    try:
        for name, url in (("metadata_before.json", base), ("source.json", base + "/exports/json"),
                          ("metadata_after.json", base)):
            entry = client.download(url, path / name, journal)
            entry["retrieved_at_utc"] = now()
            manifest["files"][name] = entry
            write_json(path / "manifest.json", manifest)
        before, rows, after = [strict_json((path / name).read_bytes()) for name in
                               ("metadata_before.json", "source.json", "metadata_after.json")]
        checks = inspect_source(before, after, rows, config)
        version_id = sha256(canonical({"dataset_id": config["dataset_id"], "fields": config["fields"],
                                      "records": sorted(canonical(row) for row in rows)}).encode())
        manifest.update(status="complete", completed_at_utc=now(), checks=checks, version_id=version_id)
        write_json(path / "manifest.json", manifest)
        snapshot = verify_snapshot(path, config)
        journal.context.update(snapshot.context)
        journal.emit("capture_validated", **checks)
        return snapshot
    except Exception as error:
        manifest.update(status="failed", completed_at_utc=now(), error_type=type(error).__name__, error=str(error))
        write_json(path / "manifest.json", manifest)
        journal.emit("capture_failed", error_type=type(error).__name__, error=str(error))
        raise


def compare_snapshots(previous, current):
    """Comparaison descriptive par clé ; aucun choix de correction métier."""
    def grouped(snapshot):
        result = collections.defaultdict(list)
        for row in snapshot.rows:
            result[tuple(row[name] for name in KEY)].append(canonical(row))
        return result
    old, new = grouped(previous), grouped(current)
    common = old.keys() & new.keys()
    ambiguous = [key for key in common if len(old[key]) != 1 or len(new[key]) != 1]
    changes = [key for key in common if key not in ambiguous and old[key] != new[key]]
    field_counts = collections.Counter()
    for key in changes:
        before, after = strict_json(old[key][0]), strict_json(new[key][0])
        field_counts.update(name for name in before if canonical(before[name]) != canonical(after[name]))
    return {"previous_version_id": previous.version_id, "current_version_id": current.version_id,
            "previous_count": len(previous.rows), "current_count": len(current.rows),
            "added_keys": len(new.keys() - old.keys()), "removed_keys": len(old.keys() - new.keys()),
            "changed_unique_keys": sum(old[key] != new[key] for key in common if key not in ambiguous),
            "unchanged_unique_keys": sum(old[key] == new[key] for key in common if key not in ambiguous),
            "ambiguous_common_keys": len(ambiguous), "key_fields": list(KEY),
            "changed_fields": dict(sorted(field_counts.items())),
            "changed_months": dict(sorted(collections.Counter(str(key[0]) for key in changes).items())),
            "added_months": dict(sorted(collections.Counter(str(key[0]) for key in new.keys() - old.keys()).items()))}
