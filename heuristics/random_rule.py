from __future__ import annotations

import random
from typing import Sequence


class RandomPriority:
    def __init__(self, seed: int = 42) -> None:
        self.rng = random.Random(seed)

    def __call__(
        self,
        job_id: int,
        proc_times: Sequence[Sequence[int]],
        partial_sequence: Sequence[int],
    ) -> float:
        return self.rng.random()
