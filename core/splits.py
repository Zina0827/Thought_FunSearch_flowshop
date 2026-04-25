"""Create and persist train/validation/test splits for PFSP instances."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import random

from core.parser import PFSPInstance, save_split


@dataclass(frozen=True)
class SplitConfig:
    """Configuration for stratified train/validation/test split generation."""

    train_ratio: float = 0.6
    val_ratio: float = 0.2
    seed: int = 42


def _bucket(inst: PFSPInstance) -> tuple[int, int]:
    return (inst.n_jobs, inst.n_machines)


def generate_splits(instances: list[PFSPInstance], config: SplitConfig | None = None) -> tuple[list[str], list[str], list[str]]:
    """Split instances by size bucket and return train, validation, and test names."""
    config = config or SplitConfig()
    rng = random.Random(config.seed)

    grouped: dict[tuple[int, int], list[PFSPInstance]] = {}
    for inst in instances:
        # Stratifying by size prevents one split from accidentally getting all
        # easy small instances or all hard large instances.
        grouped.setdefault(_bucket(inst), []).append(inst)

    train: list[str] = []
    val: list[str] = []
    test: list[str] = []

    for _, group in sorted(grouped.items()):
        names = [inst.name for inst in group]
        rng.shuffle(names)
        n = len(names)
        if n == 1:
            # Singletons cannot be distributed fairly, so keep them in training
            # rather than creating empty or misleading validation/test buckets.
            train.extend(names)
            continue
        if n == 2:
            train.append(names[0])
            test.append(names[1])
            continue
        train_end = max(1, int(round(config.train_ratio * n)))
        val_end = max(train_end + 1, int(round((config.train_ratio + config.val_ratio) * n)))
        train.extend(names[:train_end])
        val.extend(names[train_end:val_end])
        test.extend(names[val_end:])

    return train, val, test


def write_split_files(instances: list[PFSPInstance], splits_dir: str | Path, config: SplitConfig | None = None) -> None:
    """Generate dataset splits and write ``train.txt``, ``val.txt``, and ``test.txt``."""
    splits_dir = Path(splits_dir)
    train, val, test = generate_splits(instances, config=config)
    save_split(splits_dir / 'train.txt', train)
    save_split(splits_dir / 'val.txt', val)
    save_split(splits_dir / 'test.txt', test)
