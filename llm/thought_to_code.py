"""Convert heuristic thoughts into executable PFSP priority functions."""

from __future__ import annotations

from dataclasses import dataclass
import os
import re
from typing import Any

from llm.prompts import THOUGHT_TO_CODE_SYSTEM_PROMPT, build_thought_to_code_user_prompt


@dataclass
class ThoughtCodePair:
    """A heuristic thought paired with generated priority-function code."""

    thought: str
    code: str
    prompt: str
    metadata: dict[str, Any]


class StubThoughtToCodeGenerator:
    """Deterministic fallback that maps thought keywords to code templates."""

    def generate_code(self, thought: str, elite_codes: list[str] | None = None) -> ThoughtCodePair:
        """Translate a thought into candidate code without calling an LLM."""
        prompt = build_thought_to_code_user_prompt(thought, elite_code_context='\n\n'.join((elite_codes or [])[:2]))
        lowered = thought.lower()
        if 'last machine' in lowered or 'late machine' in lowered:
            code = """
def priority(job_id, unscheduled_jobs, proc_times, partial_sequence):
    total = sum(proc_times[job_id])
    imbalance = max(proc_times[job_id]) - min(proc_times[job_id])
    return total + 1.2 * proc_times[job_id][-1] - 0.3 * proc_times[job_id][0] + 0.15 * imbalance
""".strip()
        elif 'maximum single-machine time' in lowered or 'maximum' in lowered:
            code = """
def priority(job_id, unscheduled_jobs, proc_times, partial_sequence):
    total = sum(proc_times[job_id])
    peak = max(proc_times[job_id])
    return total + 0.8 * peak - 0.2 * proc_times[job_id][0]
""".strip()
        else:
            code = """
def priority(job_id, unscheduled_jobs, proc_times, partial_sequence):
    total = sum(proc_times[job_id])
    imbalance = max(proc_times[job_id]) - min(proc_times[job_id])
    return total + 0.6 * proc_times[job_id][-1] - 0.4 * proc_times[job_id][0] + 0.1 * imbalance
""".strip()
        return ThoughtCodePair(thought=thought, code=code, prompt=prompt, metadata={'generator': 'stub_thought_to_code'})


class OpenAIThoughtToCodeError(RuntimeError):
    """Raised when OpenAI-backed thought-to-code generation cannot run."""

    pass


class OpenAIThoughtToCodeGenerator:
    """OpenAI-backed generator that converts thoughts into priority functions."""

    def __init__(self, model: str | None = None, reasoning_effort: str = 'medium', temperature: float | None = None) -> None:
        """Create a thought-to-code generator using the configured OpenAI client."""
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-5')
        self.reasoning_effort = reasoning_effort
        self.temperature = temperature
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise OpenAIThoughtToCodeError('The `openai` package is not installed.') from exc
        self._client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.bltcy.ai/v1"   
        )

    @staticmethod
    def _extract_code(text: str) -> str:
        text = text.strip()
        fenced = re.findall(r'```(?:python)?\s*(.*?)```', text, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            return fenced[0].strip()
        return text

    def generate_code(self, thought: str, elite_codes: list[str] | None = None) -> ThoughtCodePair:
        """Generate candidate priority-function code for one heuristic thought."""
        prompt = f"""
                Convert the following idea into Python code:

                {thought}

                STRICT REQUIREMENTS:
                - MUST output a function named priority
                - Signature must be:

                def priority(job, proc_times, sequence):

                - Only output code
                - No explanation
                """
        kwargs: dict[str, Any] = {
            'model': self.model,
            'reasoning': {'effort': self.reasoning_effort},
            'input': [
                {'role': 'developer', 'content': [{'type': 'input_text', 'text': THOUGHT_TO_CODE_SYSTEM_PROMPT}]},
                {'role': 'user', 'content': [{'type': 'input_text', 'text': prompt}]},
            ],
        }
        if self.temperature is not None:
            kwargs['temperature'] = self.temperature
        response = self._client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": "You are a code generator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        text = response.choices[0].message.content
        code = self._extract_code(text)

        print("\n===== THOUGHT → CODE OUTPUT =====")
        print(text)
        print("=================================\n")

        # ✅ 第一步：检查有没有函数
        if 'def priority' not in code:
            print("⚠️ Invalid code generated, using fallback")
            code = """def priority(job, proc_times, sequence):
            total = 0
            for t in proc_times[job]:
                total += t
            return -total"""

        # ✅ 第二步：再统一做安全过滤（在外面！）
        forbidden = ["isinstance", "type(", "list", "dict", "import"]

        for f in forbidden:
            if f in code:
                print(f"⚠️ Unsafe code detected: {f}, using fallback")
                code = """def priority(job, proc_times, sequence):
            total = 0
            for t in proc_times[job]:
                total += t
            return -total"""
                break
        return ThoughtCodePair(
            thought=thought,
            code=code,
            prompt=prompt,
            metadata={'generator': 'openai', 'model': self.model, 'response_id': getattr(response, 'id', None)},
        )


def build_thought_to_code_generator(provider: str = 'auto', **kwargs: Any) -> StubThoughtToCodeGenerator | OpenAIThoughtToCodeGenerator:
    """Build a thought-to-code generator, using the stub fallback in ``auto`` mode."""
    provider = provider.lower().strip()
    if provider == 'stub':
        return StubThoughtToCodeGenerator()
    if provider in {'openai', 'auto'}:
        if os.getenv('OPENAI_API_KEY'):
            return OpenAIThoughtToCodeGenerator(**kwargs)
        if provider == 'openai':
            raise OpenAIThoughtToCodeError('OPENAI_API_KEY is not set.')
        return StubThoughtToCodeGenerator()
    raise ValueError(f'Unsupported thought-to-code provider: {provider}')
