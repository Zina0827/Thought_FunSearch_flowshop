"""Shared dataset-loading helpers for experiment scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from core.bks import load_bks
from core.parser import PFSPInstance, load_dataset_splits


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = ROOT / 'data' / 'raw'
DEFAULT_SPLITS_DIR = ROOT / 'data' / 'splits'
DEFAULT_BKS_PATH = ROOT / 'data' / 'processed' / 'bks.csv'


def get_requested_split(raw_dir: str, splits_dir: str, split: str, format_hint: str = '') -> tuple[list[PFSPInstance], list[PFSPInstance], list[PFSPInstance], dict[str, int]]:
    """Return the requested primary split plus auxiliary splits and BKS references."""
    dataset = load_dataset_splits(raw_dir, splits_dir, format_hint=format_hint or None)
    references = load_bks(DEFAULT_BKS_PATH)
    train, val, test = dataset.train, dataset.val, dataset.test
    if split == 'train':
        return train, val, test, references
    if split == 'val':
        return val, train, test, references
    if split == 'test':
        return test, train, val, references
    return train + val + test, val, test, references
