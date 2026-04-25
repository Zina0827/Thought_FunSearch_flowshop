"""Candidate and population containers used by FunSearch-style loops."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import json
import math
from pathlib import Path


@dataclass(order=True)
class Candidate:
    """Generated heuristic candidate with score, source code, and evaluation metadata."""

    score: float
    code: str = field(compare=False)
    method: str = field(compare=False, default='unknown')
    thought: str | None = field(compare=False, default=None)
    metrics: dict[str, Any] = field(compare=False, default_factory=dict)
    metadata: dict[str, Any] = field(compare=False, default_factory=dict)

    def signature(self) -> str:
        """Return the normalized string used to detect duplicate candidate code."""
        return self.code.strip()

    def novelty(self, others: list['Candidate']) -> float:
        """Estimate token-level Jaccard distance from the most similar candidate."""
        if not others:
            return 1.0
        # A lightweight token distance is enough here: it discourages near-duplicate
        # generated code without adding a heavy AST-normalization dependency.
        self_tokens = set(self.signature().replace('(', ' ').replace(')', ' ').replace(',', ' ').split())
        if not self_tokens:
            return 0.0
        best_overlap = 1.0
        for other in others:
            if other is self:
                continue
            other_tokens = set(other.signature().replace('(', ' ').replace(')', ' ').replace(',', ' ').split())
            union = len(self_tokens | other_tokens)
            if union == 0:
                continue
            jaccard_distance = 1.0 - (len(self_tokens & other_tokens) / union)
            best_overlap = min(best_overlap, jaccard_distance)
        return best_overlap

    def composite_score(self, others: list['Candidate'], novelty_weight: float = 0.05) -> float:
        """Combine objective score with a small novelty bonus."""
        novelty = self.novelty(others)
        return self.score + novelty_weight * novelty

    def to_dict(self) -> dict[str, Any]:
        """Serialize the candidate for logs and population snapshots."""
        return {
            'score': self.score,
            'code': self.code,
            'method': self.method,
            'thought': self.thought,
            'metrics': self.metrics,
            'metadata': self.metadata,
        }


class Population:
    """Bounded set of unique candidates ranked by score and novelty."""

    def __init__(self, max_size: int = 10, novelty_weight: float = 0.05) -> None:
        """Create an empty population with a maximum retained size."""
        self.max_size = max_size
        self.novelty_weight = novelty_weight
        self._items: list[Candidate] = []
        self._seen: set[str] = set()

    def _rerank(self) -> None:
        items = list(self._items)
        # Recompute novelty against the current population after each insertion so
        # a candidate's diversity bonus reflects the candidates it competes with now.
        items.sort(key=lambda item: item.composite_score(items, novelty_weight=self.novelty_weight), reverse=True)
        self._items = items[: self.max_size]
        self._seen = {item.signature() for item in self._items}

    def add(self, candidate: Candidate) -> bool:
        """Add a candidate if its code signature has not already been retained."""
        signature = candidate.signature()
        if signature in self._seen:
            return False
        self._items.append(candidate)
        self._seen.add(signature)
        self._rerank()
        return True

    def topk(self, k: int | None = None) -> list[Candidate]:
        """Return the top ``k`` ranked candidates, or the whole population."""
        if k is None:
            return list(self._items)
        return list(self._items[:k])

    def sample_codes(self, k: int = 2) -> list[str]:
        """Return code strings from the top candidates for prompt conditioning."""
        return [item.code for item in self._items[:k]]

    def best(self) -> Candidate | None:
        """Return the highest-ranked candidate, if the population is non-empty."""
        return self._items[0] if self._items else None

    def export_json(self, path: str | Path) -> None:
        """Write the retained population to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [item.to_dict() for item in self._items]
        path.write_text(json.dumps(payload, indent=2), encoding='utf-8')

    def __len__(self) -> int:
        """Return the number of retained candidates."""
        return len(self._items)
