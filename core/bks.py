from __future__ import annotations

from pathlib import Path
import csv
import json
from typing import Any


def _coerce_reference_map(raw: dict[str, Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    for key, value in raw.items():
        try:
            out[str(key).strip()] = int(value)
        except (TypeError, ValueError):
            continue
    return out


def default_bks() -> dict[str, int]:
    """Built-in references for sample files and a few common PFSP names.

    Users should normally provide a CSV/JSON file in data/processed for real runs.
    """
    return {
        'sample_instance_01': 19,
        'sample_instance_02': 35,
        'tai20_5_1': 1278,
        'tai20_5_2': 1359,
        'tai50_10_1': 2991,
    }


def load_bks(path: str | Path | None = None) -> dict[str, int]:
    references = default_bks()
    if path is None:
        return references

    path = Path(path)
    if not path.exists():
        return references

    if path.suffix.lower() == '.json':
        loaded = json.loads(path.read_text(encoding='utf-8'))
        references.update(_coerce_reference_map(loaded))
        return references

    if path.suffix.lower() == '.csv':
        with path.open('r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = str(row.get('instance', '')).strip()
                value = row.get('bks') or row.get('reference') or row.get('best_known')
                if name and value not in (None, ''):
                    try:
                        references[name] = int(value)
                    except ValueError:
                        continue
        return references

    return references
