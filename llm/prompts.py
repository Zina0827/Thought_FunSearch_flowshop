from __future__ import annotations

DIRECT_CODE_SYSTEM_PROMPT = """You design priority functions for permutation flow shop scheduling.
Return only valid Python code. The function name must be `priority`.
The function signature is:

def priority(job_id, unscheduled_jobs, proc_times, partial_sequence):
    ...

Return a numeric score. Higher score means the scheduler selects the job earlier.
Use only Python built-ins and arithmetic. Do not import modules.
Keep the function short, deterministic, and safe to execute inside a restricted sandbox.
Prefer signals that plausibly reduce makespan in PFSP, such as total workload,
late-machine pressure, front-machine blocking risk, machine imbalance, and simple
context features from the partial sequence.
"""

THOUGHT_SYSTEM_PROMPT = """You design interpretable scheduling heuristics for permutation flow shop scheduling.
Produce a short, structured heuristic thought with these exact fields:
- intuition
- primary_signal
- tie_breaker
- expected_effect
Keep it concise, concrete, and tied to the available inputs:
job_id, unscheduled_jobs, proc_times, partial_sequence.
Focus on why the heuristic could reduce makespan.
"""

THOUGHT_TO_CODE_SYSTEM_PROMPT = """Convert the provided heuristic thought into a Python priority function.
Return only valid Python code with the required signature:

def priority(job_id, unscheduled_jobs, proc_times, partial_sequence):
    ...

Return a numeric score. Higher score means earlier selection.
Use only Python built-ins and arithmetic. Do not import modules.
Implement the stated primary signal and tie-breaker faithfully.
"""


def build_direct_code_user_prompt(seed_description: str = '', example_features: str = '', elite_examples: str = '') -> str:
    description = seed_description.strip() or 'Design a strong priority heuristic for minimizing makespan in permutation flow shop scheduling.'
    features = example_features.strip() or (
        'Available signals include total job processing time, first-machine time, last-machine time, '
        'machine imbalance, partial sequence length, and simple aggregates over unscheduled jobs.'
    )
    prompt = (
        f'Task: {description}\n'
        f'Context: {features}\n'
        'Return one candidate priority function only.\n'
    )
    if elite_examples.strip():
        prompt += 'Strong prior candidates to improve upon:\n' + elite_examples.strip() + '\n'
    return prompt


def build_thought_user_prompt(seed_description: str = '', example_features: str = '', elite_thoughts: str = '') -> str:
    description = seed_description.strip() or 'Design a concise, plausible PFSP heuristic idea.'
    features = example_features.strip() or (
        'You may reason about front-machine blocking, downstream congestion, total workload, '
        'and the effect of scheduling large jobs earlier or later.'
    )
    prompt = f'Task: {description}\nContext: {features}\nReturn the structured thought only.\n'
    if elite_thoughts.strip():
        prompt += 'High-performing prior thoughts to diversify or improve:\n' + elite_thoughts.strip() + '\n'
    return prompt


def build_thought_to_code_user_prompt(thought: str, elite_code_context: str = '') -> str:
    prompt = f'Heuristic thought:\n{thought}\n\nTranslate it into the required Python function.'
    if elite_code_context.strip():
        prompt += '\n\nReference patterns from previous strong code candidates:\n' + elite_code_context.strip()
    return prompt
