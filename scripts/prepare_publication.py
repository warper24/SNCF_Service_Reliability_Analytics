"""Créer les copies publiques des preuves sans modifier les originaux validés."""

import argparse
import hashlib
import json
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]
GROUPS = ("audit_evidence", "ingestion_evidence", "data_quality_evidence", "data_model_evidence", "diagnostic_evidence", "powerbi_evidence")
# Journal Windows identifié à J06 : conversion de la copie, original intact.
LEGACY_ENCODINGS = {("diagnostic_evidence", "compile.txt"): "cp1252"}
USER_PATH = re.compile(r"([A-Za-z]:[\\/]+Users[\\/]+)([^\\/\r\n\"<>]+)")
SECRET = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
                    r"\bgh[pousr]_[A-Za-z0-9]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b|"
                    r"\bAIza[0-9A-Za-z_-]{30,}\b")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def anonymize(text):
    """Remplacer seulement le nom du profil Windows ; garder les valeurs métier."""
    return USER_PATH.sub(lambda match: match.group(1) + "<utilisateur>", text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Vérifier les copies existantes sans écrire.")
    args = parser.parse_args()
    destination = REPO / "reports/publication_evidence"
    entries = []
    for group in GROUPS:
        source_dir = REPO / "reports" / group
        if not source_dir.is_dir():
            raise ValueError(f"Preuves locales absentes : {group}. Les récupérer ou les produire avant publication.")
        for source in sorted(source_dir.iterdir()):
            if not source.is_file():
                raise ValueError(f"Sous-dossier inattendu : {source.name}")
            if source.suffix not in (".json", ".csv", ".txt"):
                raise ValueError(f"Format de preuve inattendu : {source.name}")
            original = source.read_bytes()
            source_encoding = "utf-8"
            try:
                text = original.decode(source_encoding)
            except UnicodeDecodeError:
                source_encoding = LEGACY_ENCODINGS.get((group, source.name))
                if source_encoding is None:
                    raise
                text = original.decode(source_encoding)
            if SECRET.search(text):
                raise ValueError(f"Secret potentiel : {group}/{source.name}. Ne pas publier.")
            public = anonymize(text).encode("utf-8")
            if source.suffix == ".json":
                json.loads(public)
            target = destination / group / source.name
            if args.check:
                if not target.is_file() or target.read_bytes() != public:
                    raise ValueError(f"Copie publique absente ou différente : {group}/{source.name}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(public)
            entry = {"path": f"{group}/{source.name}", "original_sha256": digest(original),
                     "public_sha256": digest(public), "anonymized": original != public}
            if source_encoding != "utf-8":
                entry.update(source_encoding=source_encoding, public_encoding="utf-8")
            entries.append(entry)
    manifest = {
        "purpose": "Copies publiques de preuves historiques ; aucune nouvelle validation revendiquée.",
        "transformation": "Remplacement du nom de profil Windows par <utilisateur> ; conversion explicite vers UTF-8 des journaux Windows déclarés ; valeurs métier inchangées.",
        "hash_policy": "Les empreintes internes des validations restent celles des originaux. Utiliser ce manifeste pour vérifier les octets publics.",
        "entries": entries,
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest_path = destination / "manifest.json"
    if args.check:
        if not manifest_path.is_file() or manifest_path.read_bytes() != manifest_bytes:
            raise ValueError("Manifeste de publication différent.")
    else:
        manifest_path.write_bytes(manifest_bytes)
    print(json.dumps({"mode": "check" if args.check else "prepare", "files": len(entries),
                      "anonymized_files": sum(entry["anonymized"] for entry in entries),
                      "originals_modified": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
