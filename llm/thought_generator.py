"""Generate natural-language heuristic thoughts for PFSP scheduling."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

from llm.prompts import THOUGHT_SYSTEM_PROMPT, build_thought_user_prompt


DEFAULT_THOUGHTS = [
    """intuition: prioritize jobs with large total workload but avoid very heavy first-machine processing
primary_signal: sum of processing times with extra weight on later machines
tie_breaker: prefer smaller first-machine time
expected_effect: reduce downstream congestion while keeping the first machine flowing""",
    """intuition: schedule jobs that are likely to create bottlenecks on late machines earlier
primary_signal: high processing time on the last machine and high total workload
tie_breaker: smaller middle-machine average
expected_effect: reduce waiting near the end of the line""",
    """intuition: combine overall job size and imbalance across machines
primary_signal: total workload plus the maximum single-machine time
tie_breaker: smaller first-machine time
expected_effect: process influential jobs early without creating too much front-end blocking""",
]


@dataclass
class CandidateThought:
    """Generated heuristic thought plus prompt and provenance metadata."""

    thought: str
    prompt: str
    metadata: dict[str, Any]


class StubThoughtGenerator:
    """Deterministic fallback that cycles through hand-written heuristic thoughts."""

    def generate(self, n: int = 1, seed_description: str = '', elite_thoughts: list[str] | None = None) -> list[CandidateThought]:
        """Return structured heuristic thoughts without calling an LLM."""
        prompt = build_thought_user_prompt(seed_description, elite_thoughts='\n\n'.join((elite_thoughts or [])[:2]))
        thoughts = []
        pool = (elite_thoughts or []) + DEFAULT_THOUGHTS
        for i in range(n):
            thoughts.append(CandidateThought(thought=pool[i % len(pool)], prompt=prompt, metadata={'generator': 'stub', 'index': i}))
        return thoughts


class OpenAIThoughtGeneratorError(RuntimeError):
    """Raised when OpenAI-backed thought generation cannot run."""

    pass


class OpenAIThoughtGenerator:
    """OpenAI-backed generator for structured heuristic thoughts."""

    def __init__(self, model: str | None = None, reasoning_effort: str = 'medium', temperature: float | None = None) -> None:
        """Create a thought generator using the configured OpenAI client."""
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-5')
        self.reasoning_effort = reasoning_effort
        self.temperature = temperature
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise OpenAIThoughtGeneratorError('The `openai` package is not installed.') from exc
        self._client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.bltcy.ai/v1"   
        )

    def _single_generate(self, seed_description: str = '', elite_thoughts: list[str] | None = None) -> CandidateThought:
        prompt = build_thought_user_prompt(seed_description, elite_thoughts='\n\n'.join((elite_thoughts or [])[:2]))
        kwargs: dict[str, Any] = {
            'model': self.model,
            'reasoning': {'effort': self.reasoning_effort},
            'input': [
                {'role': 'developer', 'content': [{'type': 'input_text', 'text': THOUGHT_SYSTEM_PROMPT}]},
                {'role': 'user', 'content': [{'type': 'input_text', 'text': prompt}]},
            ],
        }
        if self.temperature is not None:
            kwargs['temperature'] = self.temperature

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a heuristic designer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        thought = response.choices[0].message.content

        if not thought:
            raise OpenAIThoughtGeneratorError('The model returned an empty thought.')
        return CandidateThought(
            thought=thought,
            prompt=prompt,
            metadata={'generator': 'openai', 'model': self.model, 'response_id': getattr(response, 'id', None)},
        )

    def generate(self, n: int = 1, seed_description: str = '', elite_thoughts: list[str] | None = None) -> list[CandidateThought]:
        """Generate ``n`` structured heuristic thoughts."""
        return [self._single_generate(seed_description=seed_description, elite_thoughts=elite_thoughts) for _ in range(n)]


def build_thought_generator(provider: str = 'auto', **kwargs: Any) -> StubThoughtGenerator | OpenAIThoughtGenerator:
    """Build a thought generator, using the stub fallback in ``auto`` mode."""
    provider = provider.lower().strip()
    if provider == 'stub':
        return StubThoughtGenerator()
    if provider in {'openai', 'auto'}:
        if os.getenv('OPENAI_API_KEY'):
            return OpenAIThoughtGenerator(**kwargs)
        if provider == 'openai':
            raise OpenAIThoughtGeneratorError('OPENAI_API_KEY is not set.')
        return StubThoughtGenerator()
    raise ValueError(f'Unsupported thought generator provider: {provider}')
