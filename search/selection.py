"""Selection and objective helpers for ranking generated candidates."""

from __future__ import annotations

from random import Random

from search.population import Candidate


def objective_from_summary(avg_makespan: float, avg_gap_percent: float | None = None, avg_runtime_sec: float | None = None) -> float:
    """Convert evaluation metrics into a maximization score for search."""
    # Search code expects larger scores to be better, while PFSP makespan and gap
    # are minimization metrics, so the objective is expressed as a penalty.
    score = -float(avg_makespan)
    if avg_gap_percent is not None:
        score -= 10.0 * float(avg_gap_percent)
    if avg_runtime_sec is not None:
        score -= 0.01 * float(avg_runtime_sec)
    return score


def select_elites(candidates: list[Candidate], k: int) -> list[Candidate]:
    """Return the top ``k`` candidates by dataclass ordering."""
    return sorted(candidates, reverse=True)[:k]


def tournament_select(candidates: list[Candidate], k: int, tournament_size: int = 3, seed: int = 42) -> list[Candidate]:
    """Select candidates by repeated seeded tournaments without replacement."""
    if not candidates or k <= 0:
        return []
    rng = Random(seed)
    remaining = list(candidates)
    selected: list[Candidate] = []
    while remaining and len(selected) < min(k, len(candidates)):
        pool = rng.sample(remaining, k=min(tournament_size, len(remaining)))
        winner = max(pool)
        selected.append(winner)
        remaining.remove(winner)
    return selected


def diversify_elites(candidates: list[Candidate], k: int, seed: int = 42) -> list[Candidate]:
    """Select strong candidates while preferring novelty among near-elites."""
    if not candidates or k <= 0:
        return []
    rng = Random(seed)
    pool = sorted(candidates, reverse=True)
    selected: list[Candidate] = [pool[0]]
    remainder = pool[1:]
    while remainder and len(selected) < min(k, len(pool)):
        # Keep the best candidate fixed, then sample among the strongest diverse
        # alternatives to avoid prompting the generator with clones of one idea.
        remainder.sort(key=lambda cand: cand.composite_score(selected), reverse=True)
        top = remainder[: min(3, len(remainder))]
        winner = rng.choice(top)
        selected.append(winner)
        remainder.remove(winner)
    return selected
