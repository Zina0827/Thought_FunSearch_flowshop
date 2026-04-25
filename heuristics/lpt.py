"""Longest-processing-time baseline priority rule for PFSP scheduling."""

from __future__ import annotations

from typing import Sequence


class LPTPriority:
    """Longest total processing time first."""

    def __call__(
        self,
        job_id: int,
        proc_times: Sequence[Sequence[int]],
        partial_sequence: Sequence[int],
    ) -> float:
        """Return total processing time so larger jobs can be chosen first."""
        return float(sum(proc_times[job_id]))
