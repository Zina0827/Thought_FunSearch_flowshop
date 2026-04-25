"""Generate candidate PFSP priority-function code from prompts or stubs."""

from __future__ import annotations
import os
from dataclasses import dataclass
import os
import re
from typing import Any

from llm.prompts import DIRECT_CODE_SYSTEM_PROMPT, build_direct_code_user_prompt

DEFAULT_DIRECT_CANDIDATES = [
    """
def priority(job_id, proc_times, partial_sequence):
    total = sum(proc_times[job_id])
    front = proc_times[job_id][0]
    back = proc_times[job_id][-1]
    imbalance = max(proc_times[job_id]) - min(proc_times[job_id])
    return 0.45 * total + 1.0 * back - 0.35 * front + 0.2 * imbalance
""".strip(),
    """
def priority(job_id, proc_times, partial_sequence):
    total = sum(proc_times[job_id])
    bottleneck = max(proc_times[job_id])
    tail_avg = (proc_times[job_id][-1] + bottleneck) / 2.0
    return total + 0.4 * tail_avg - 0.25 * proc_times[job_id][0]
""".strip(),
    """
def priority(job_id, proc_times, partial_sequence):
    total = sum(proc_times[job_id])
    front = proc_times[job_id][0]
    back = proc_times[job_id][-1]
    partial_bias = len(partial_sequence)
    return 0.6 * total + 0.7 * back - 0.3 * front + 0.05 * partial_bias
""".strip(),
]


@dataclass
class CandidateCode:
    """Generated priority-function code plus the prompt and provenance metadata."""

    code: str
    prompt: str
    metadata: dict[str, Any]


class StubCodeGenerator:
    """Deterministic offline fallback with light variation around elite examples."""

    def generate(self, n: int = 1, seed_description: str = '', elite_codes: list[str] | None = None) -> list[CandidateCode]:
        """Return deterministic candidate code snippets without calling an LLM."""
        elite_examples = ''
        if elite_codes:
            elite_examples = '\n\n'.join(elite_codes[:2])
        prompt = build_direct_code_user_prompt(seed_description, elite_examples=elite_examples)
        candidates = []
        pool = list(DEFAULT_DIRECT_CANDIDATES)
        if elite_codes:
            pool = elite_codes[:2] + pool
        for i in range(n):
            code = pool[i % len(pool)]
            candidates.append(CandidateCode(code=code, prompt=prompt, metadata={'generator': 'stub', 'index': i}))
        return candidates


class OpenAIGeneratorError(RuntimeError):
    """Raised when OpenAI-backed direct code generation cannot run."""

    pass


class OpenAICodeGenerator:
    """OpenAI-backed generator using the Responses API."""

    def __init__(
        self,
        model: str | None = None,
        reasoning_effort: str = 'medium',
        temperature: float | None = None,
    ) -> None:
        """Create an OpenAI-backed direct code generator."""
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4o')
        self.reasoning_effort = reasoning_effort
        self.temperature = temperature
        try:
            import importlib
            openai_mod = importlib.import_module('openai')
            OpenAI = getattr(openai_mod, 'OpenAI')
        except Exception as exc:
            raise OpenAIGeneratorError('The `openai` package is not installed or missing OpenAI class.') from exc
        self._client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url="https://api.bltcy.ai/v1"
        )

    def _fix_signature(self, code: str) -> str:
        # 如果已经是正确签名
        if "def priority(job, proc_times, sequence):" in code:
            return code

        # 如果是错误的4参数版本 → 自动替换
        if "def priority(" in code:
            print("⚠️ Fixing invalid function signature")

            code = re.sub(
                r"def\s+priority\s*\(.*?\):",
                "def priority(job, proc_times, sequence):",
                code
            )
            return code

        # fallback（防止完全乱输出）
        print("⚠️ Using fallback priority function")

        return """def priority(job, proc_times, sequence):
        return sum(proc_times[job])"""

    def _sanitize_code(self, code: str) -> str:
        forbidden = ["isinstance", "type(", "import"]

        for f in forbidden:
            if f in code:
                # The sandbox will reject unsafe constructs later; replacing early
                # keeps the search loop moving when a model ignores the prompt.
                print(f"⚠️ Removing unsafe code: {f}")
                return """def priority(job, proc_times, sequence):
        total = 0
        for t in proc_times[job]:
            total += t
        return -total"""

        return code
    
    def _fix_variables(self, code: str) -> str:
        # Older prompt templates used different parameter names; normalizing them
        # preserves useful generated formulas instead of discarding the candidate.
        code = code.replace("job_id", "job")
        code = code.replace("partial_sequence", "sequence")
        code = code.replace("unscheduled_jobs", "sequence")  # 或直接删
        return code

    @staticmethod
    def _extract_code(text: str) -> str:
        text = text.strip()

        # 去掉 markdown fence
        text = text.replace("```python", "").replace("```", "")

        # 优先提取 priority 函数
        match = re.search(
            r"def\s+priority\s*\(.*?\):[\s\S]+?(?=\n\S|\Z)",
            text
        )
        if match:
            return match.group(0).strip()

        return text

    def _single_generate(self, seed_description: str = '', elite_codes: list[str] | None = None) -> CandidateCode:
        elite_examples = ''
        if elite_codes:
            elite_examples = '\n\n'.join(elite_codes[:2])

        prompt = """
                Write a Python function named `priority`.

                STRICT REQUIREMENTS:
                - The function signature MUST be exactly:

                def priority(job, proc_times, sequence):

                - Do NOT use:
                isinstance, type, any imports

                - Only use:
                basic arithmetic, loops, indexing

                - Return a numeric score

                Only output Python code.

                You MUST follow this exact template:

                def priority(job, proc_times, sequence):
                    # You can ONLY use:
                    # - job
                    # - proc_times
                    # - sequence

                    # DO NOT use:
                    # job_id
                    # unscheduled_jobs
                    # partial_sequence

                    # Only write code inside this function.
                """

        response = self._client.chat.completions.create(
            model="gpt-5-nano",   
            messages=[
                {"role": "system", "content": DIRECT_CODE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        text = response.choices[0].message.content 

        print("\n===== LLM RAW OUTPUT =====")
        print(text)
        print("==========================\n")

        code = self._extract_code(text)
        code = self._fix_signature(code)
        code = self._sanitize_code(code)
        code = self._fix_variables(code)

        if 'def priority' not in code:
            print("⚠️ WARNING: fallback priority function used")
            code = """def priority(job, proc_times, sequence):
        return sum(proc_times[job])"""

        return CandidateCode(
            code=code,
            prompt=prompt,
            metadata={
                'generator': 'openai',
                'model': self.model,
            },
        )

    def generate(self, n: int = 1, seed_description: str = '', elite_codes: list[str] | None = None) -> list[CandidateCode]:
        """Generate ``n`` candidate priority functions from the configured model."""
        return [self._single_generate(seed_description=seed_description, elite_codes=elite_codes) for _ in range(n)]


def build_code_generator(provider: str = 'auto', **kwargs: Any) -> StubCodeGenerator | OpenAICodeGenerator:
    """Build a direct code generator, falling back to the stub in ``auto`` mode."""
    provider = provider.lower().strip()
    if provider == 'stub':
        return StubCodeGenerator()
    if provider in {'openai', 'auto'}:
        if os.getenv('OPENAI_API_KEY'):
            return OpenAICodeGenerator(**kwargs)
        if provider == 'openai':
            raise OpenAIGeneratorError('OPENAI_API_KEY is not set.')
        return StubCodeGenerator()
    raise ValueError(f'Unsupported generator provider: {provider}')
