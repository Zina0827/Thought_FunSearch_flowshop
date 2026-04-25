"""Randomized baseline priority rule for PFSP scheduling."""

from __future__ import annotations

import random
from typing import Sequence


class RandomPriority:
    """Seeded random priority function for baseline comparisons."""

    def __init__(self, seed: int = 42) -> None:
        """Create an independent random-number generator for repeatability."""
        self.rng = random.Random(seed)

    def __call__(
        self,
        job_id: int,
        proc_times: Sequence[Sequence[int]],
        partial_sequence: Sequence[int],
    ) -> float:
        """Return a random score for the requested job."""
        return self.rng.random()
