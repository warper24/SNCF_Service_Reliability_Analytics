"""Lancer J03 depuis le dépôt avec l'interpréteur Python verrouillé."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sncf_reliability.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
