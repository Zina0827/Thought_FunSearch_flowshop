"""Shortest-processing-time baseline priority rule for PFSP scheduling."""

from __future__ import annotations

from typing import Sequence


class SPTPriority:
    """Shortest total processing time first. Returns larger score for shorter jobs."""

    def __call__(
        self,
        job_id: int,
        proc_times: Sequence[Sequence[int]],
        partial_sequence: Sequence[int],
    ) -> float:
        """Return negative total processing time so shorter jobs score higher."""
        return -float(sum(proc_times[job_id]))
