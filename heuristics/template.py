from __future__ import annotations

from typing import Protocol, Sequence


class PriorityFunction(Protocol):
    def __call__(
        self,
        job_id: int,
        proc_times: Sequence[Sequence[int]],
        partial_sequence: Sequence[int],
    ) -> float:
        ...
