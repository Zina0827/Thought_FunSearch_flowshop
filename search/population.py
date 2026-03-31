from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import json
import math
from pathlib import Path


@dataclass(order=True)
class Candidate:
    score: float
    code: str = field(compare=False)
    method: str = field(compare=False, default='unknown')
    thought: str | None = field(compare=False, default=None)
    metrics: dict[str, Any] = field(compare=False, default_factory=dict)
    metadata: dict[str, Any] = field(compare=False, default_factory=dict)

    def signature(self) -> str:
        return self.code.strip()

    def novelty(self, others: list['Candidate']) -> float:
        if not others:
            return 1.0
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
        novelty = self.novelty(others)
        return self.score + novelty_weight * novelty

    def to_dict(self) -> dict[str, Any]:
        return {
            'score': self.score,
            'code': self.code,
            'method': self.method,
            'thought': self.thought,
            'metrics': self.metrics,
            'metadata': self.metadata,
        }


class Population:
    def __init__(self, max_size: int = 10, novelty_weight: float = 0.05) -> None:
        self.max_size = max_size
        self.novelty_weight = novelty_weight
        self._items: list[Candidate] = []
        self._seen: set[str] = set()

    def _rerank(self) -> None:
        items = list(self._items)
        items.sort(key=lambda item: item.composite_score(items, novelty_weight=self.novelty_weight), reverse=True)
        self._items = items[: self.max_size]
        self._seen = {item.signature() for item in self._items}

    def add(self, candidate: Candidate) -> bool:
        signature = candidate.signature()
        if signature in self._seen:
            return False
        self._items.append(candidate)
        self._seen.add(signature)
        self._rerank()
        return True

    def topk(self, k: int | None = None) -> list[Candidate]:
        if k is None:
            return list(self._items)
        return list(self._items[:k])

    def sample_codes(self, k: int = 2) -> list[str]:
        return [item.code for item in self._items[:k]]

    def best(self) -> Candidate | None:
        return self._items[0] if self._items else None

    def export_json(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [item.to_dict() for item in self._items]
        path.write_text(json.dumps(payload, indent=2), encoding='utf-8')

    def __len__(self) -> int:
        return len(self._items)
