def build_schedule(proc_times, priority_fn, maximize=False):
    """
    Build a job sequence using a priority function.

    Args:
        proc_times: list of list (job x machine)
        priority_fn: function(job_id, proc_times, current_sequence) -> score
        maximize: whether to maximize score

    Returns:
        sequence: list of job indices
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