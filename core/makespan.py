from __future__ import annotations

from typing import Sequence


def compute_completion_times(order: Sequence[int], proc_times: Sequence[Sequence[int]]) -> list[list[int]]:
    if not order:
        return []
    n_jobs = len(order)
    n_machines = len(proc_times[0])
    completion = [[0] * n_machines for _ in range(n_jobs)]

    for i, job in enumerate(order):
        for m in range(n_machines):
            duration = int(proc_times[job][m])
            if i == 0 and m == 0:
                completion[i][m] = duration
            elif i == 0:
                completion[i][m] = completion[i][m - 1] + duration
            elif m == 0:
                completion[i][m] = completion[i - 1][m] + duration
            else:
                completion[i][m] = max(completion[i - 1][m], completion[i][m - 1]) + duration
    return completion


def compute_makespan(order: Sequence[int], proc_times: Sequence[Sequence[int]]) -> int:
    if not order:
        return 0
    completion = compute_completion_times(order, proc_times)
    return completion[-1][-1]
