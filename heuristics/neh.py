"""NEH-style constructive heuristics for permutation flow shop scheduling."""

from __future__ import annotations

from typing import Sequence

from core.makespan import compute_makespan


def neh_key(proc_times: Sequence[Sequence[int]], job: int) -> tuple[float, ...]:
    """Return the descending sort key used to seed the NEH job order."""
    total = float(sum(proc_times[job]))
    tail = float(proc_times[job][-1])
    peak = float(max(proc_times[job]))
    front = float(proc_times[job][0])
    # NEH benefits from placing influential jobs early; the negative front-machine
    # tie-breaker avoids blocking the first machine with an especially slow start.
    return (total, tail, peak, -front)


def partial_makespan(sequence: list[int], proc_times: Sequence[Sequence[int]]) -> int:
    """Compute the makespan of a partial or complete job sequence."""
    return compute_makespan(sequence, proc_times)


def insertion_best(sequence: list[int], job: int, proc_times: Sequence[Sequence[int]]) -> list[int]:
    """Insert ``job`` at the position that minimizes partial makespan."""
    best_seq = None
    best_makespan = None
    best_tie = None
    for pos in range(len(sequence) + 1):
        candidate = sequence[:pos] + [job] + sequence[pos:]
        value = partial_makespan(candidate, proc_times)
        tie = sum(proc_times[candidate[-1]])
        # The tie-breaker favors a lighter final job so equal makespans leave more
        # flexibility for later insertions.
        if best_makespan is None or value < best_makespan or (value == best_makespan and tie < best_tie):
            best_makespan = value
            best_tie = tie
            best_seq = candidate
    return best_seq if best_seq is not None else [job]


def neh_sequence(proc_times: Sequence[Sequence[int]]) -> list[int]:
    """Build a PFSP sequence with the classic NEH insertion heuristic."""
    n_jobs = len(proc_times)
    jobs = list(range(n_jobs))
    jobs.sort(key=lambda j: neh_key(proc_times, j), reverse=True)
    sequence: list[int] = []
    for job in jobs:
        sequence = insertion_best(sequence, job, proc_times)
    return sequence


def improve_by_adjacent_swaps(sequence: list[int], proc_times: Sequence[Sequence[int]]) -> list[int]:
    """Greedily improve a sequence by accepting beneficial adjacent swaps."""
    improved = list(sequence)
    changed = True
    while changed:
        changed = False
        base = compute_makespan(improved, proc_times)
        for i in range(len(improved) - 1):
            candidate = improved[:]
            candidate[i], candidate[i + 1] = candidate[i + 1], candidate[i]
            value = compute_makespan(candidate, proc_times)
            if value < base:
                improved = candidate
                base = value
                changed = True
                break
    return improved


def improve_by_reinsertion(sequence: list[int], proc_times: Sequence[Sequence[int]]) -> list[int]:
    """Greedily improve a sequence by removing and reinserting single jobs."""
    improved = list(sequence)
    base = compute_makespan(improved, proc_times)
    changed = True
    while changed:
        changed = False
        for i in range(len(improved)):
            job = improved[i]
            reduced = improved[:i] + improved[i + 1:]
            best = insertion_best(reduced, job, proc_times)
            value = compute_makespan(best, proc_times)
            if value < base:
                improved = best
                base = value
                changed = True
                break
    return improved


def neh_plus_sequence(proc_times: Sequence[Sequence[int]]) -> list[int]:
    """Return an NEH sequence refined by local swap and reinsertion moves."""
    seq = neh_sequence(proc_times)
    seq = improve_by_adjacent_swaps(seq, proc_times)
    seq = improve_by_reinsertion(seq, proc_times)
    return seq


class NEHPriority:
    """Priority wrapper that replays an NEH or NEH+ sequence in greedy scheduling."""

    def __init__(self, proc_times: Sequence[Sequence[int]], plus: bool = False) -> None:
        """Precompute the target sequence and job ranks for an instance."""
        self.sequence = neh_plus_sequence(proc_times) if plus else neh_sequence(proc_times)
        self.rank = {job: idx for idx, job in enumerate(self.sequence)}

    def __call__(self, job_id: int, proc_times: Sequence[Sequence[int]], partial_sequence: Sequence[int]) -> float:
        """Return a score that schedules earlier NEH-ranked jobs first."""
        return -float(self.rank[job_id])
