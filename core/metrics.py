from __future__ import annotations

from statistics import mean as _stats_mean, median as _stats_median
from typing import Iterable, Sequence


def mean(values: Iterable[float]) -> float:
    values = list(values)
    return float(_stats_mean(values)) if values else 0.0


def median(values: Sequence[float]) -> float:
    values = list(values)
    return float(_stats_median(values)) if values else 0.0


def gap_to_reference(value: float, reference: float | None) -> float | None:
    if reference is None:
        return None
    if reference <= 0:
        return 0.0
    return 100.0 * (value - reference) / reference


def safe_min(values: Sequence[float]) -> float:
    return float(min(values)) if values else 0.0


def safe_max(values: Sequence[float]) -> float:
    return float(max(values)) if values else 0.0
