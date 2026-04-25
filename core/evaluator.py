"""Evaluate scheduling priority functions on PFSP benchmark instances."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from time import perf_counter
from typing import Callable, Sequence

from core.makespan import compute_makespan
from core.metrics import mean, median, gap_to_reference, safe_max, safe_min
from core.scheduler import build_schedule


@dataclass
class InstanceResult:
    """Evaluation result for one method on one PFSP instance."""

    instance: str
    method: str
    sequence: list[int]
    makespan: int
    runtime_sec: float
    reference: int | None = None
    gap_percent: float | None = None

    def to_dict(self) -> dict:
        """Serialize the per-instance result as a plain dictionary."""
        return asdict(self)


@dataclass
class EvaluationSummary:
    """Aggregate metrics and detailed per-instance results for one method."""

    method: str
    n_instances: int
    avg_makespan: float
    median_makespan: float
    best_makespan: float
    worst_makespan: float
    avg_runtime_sec: float
    avg_gap_percent: float | None
    results: list[InstanceResult]

    def to_dict(self) -> dict:
        """Serialize summary statistics without embedding per-instance rows."""
        return {
            'method': self.method,
            'n_instances': self.n_instances,
            'avg_makespan': self.avg_makespan,
            'median_makespan': self.median_makespan,
            'best_makespan': self.best_makespan,
            'worst_makespan': self.worst_makespan,
            'avg_runtime_sec': self.avg_runtime_sec,
            'avg_gap_percent': self.avg_gap_percent,
        }


def evaluate_priority_function(
    method_name: str,
    instances,
    priority_fn: Callable,
    references: dict[str, int] | None = None,
    maximize: bool = True,
) -> EvaluationSummary:
    """Build schedules with ``priority_fn`` and summarize their PFSP performance."""
    results: list[InstanceResult] = []

    for inst in instances:
        start = perf_counter()
        sequence = build_schedule(inst["proc_times"], priority_fn=priority_fn, maximize=maximize)
        makespan = compute_makespan(sequence, inst["proc_times"])
        runtime = perf_counter() - start
        reference = references.get(inst["name"]) if references else None
        gap = gap_to_reference(makespan, reference)
        results.append(
            InstanceResult(
                instance=inst["name"],
                method=method_name,
                sequence=sequence,
                makespan=makespan,
                runtime_sec=runtime,
                reference=reference,
                gap_percent=gap,
            )
        )

    avg_gap = None
    gap_values = [r.gap_percent for r in results if r.gap_percent is not None]
    if gap_values:
        avg_gap = mean(gap_values)

    makespans = [float(r.makespan) for r in results]
    runtimes = [float(r.runtime_sec) for r in results]
    return EvaluationSummary(
        method=method_name,
        n_instances=len(results),
        avg_makespan=mean(makespans),
        median_makespan=median(makespans),
        best_makespan=safe_min(makespans),
        worst_makespan=safe_max(makespans),
        avg_runtime_sec=mean(runtimes),
        avg_gap_percent=avg_gap,
        results=results,
    )
