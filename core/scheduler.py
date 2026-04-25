"""Build PFSP job sequences from user-provided priority functions."""

def build_schedule(proc_times, priority_fn, maximize=False):
    """Build a job sequence greedily by repeatedly scoring remaining jobs.

    Args:
        proc_times: Processing-time matrix in job-by-machine order.
        priority_fn: Callable ``priority(job, proc_times, current_sequence)``.
        maximize: If true, select the largest score; otherwise select the smallest.

    Returns:
        A list of job indices in scheduled order.
    """

    n_jobs = len(proc_times)
    remaining_jobs = set(range(n_jobs))
    sequence = []

    while remaining_jobs:
        best_job = None
        best_score = None

        for job in remaining_jobs:
            score = priority_fn(job, proc_times, sequence)

            if best_score is None:
                best_job = job
                best_score = score
            else:
                if maximize:
                    if score > best_score:
                        best_job = job
                        best_score = score
                else:
                    if score < best_score:
                        best_job = job
                        best_score = score

        sequence.append(best_job)
        remaining_jobs.remove(best_job)

    return sequence
