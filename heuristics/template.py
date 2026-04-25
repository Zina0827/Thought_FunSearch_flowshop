"""Protocol definition for PFSP priority-function callables."""

from __future__ import annotations

from typing import Protocol, Sequence


class PriorityFunction(Protocol):
    """Callable interface expected by the greedy PFSP scheduler."""

    def __call__(
        self,
        job_id: int,
        proc_times: Sequence[Sequence[int]],
        partial_sequence: Sequence[int],
    ) -> float:
        """Return a numeric priority score for ``job_id``."""
        ...
