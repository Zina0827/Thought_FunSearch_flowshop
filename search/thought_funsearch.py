from __future__ import annotations

from pathlib import Path
import json

from core.evaluator import evaluate_priority_function
from llm.sandbox import load_priority_function, SandboxError
from llm.thought_generator import StubThoughtGenerator
from llm.thought_to_code import StubThoughtToCodeGenerator
from search.population import Candidate, Population
from search.selection import diversify_elites, objective_from_summary


class ThoughtFunSearch:
    def __init__(
        self,
        population_size: int = 8,
        thought_generator: object | None = None,
        code_generator: object | None = None,
        novelty_weight: float = 0.05,
    ) -> None:
        self.population = Population(max_size=population_size, novelty_weight=novelty_weight)
        self.thought_generator = thought_generator or StubThoughtGenerator()
        self.code_generator = code_generator or StubThoughtToCodeGenerator()

    def run(
        self,
        train_instances: list,
        val_instances: list | None = None,
        iterations: int = 3,
        candidates_per_iteration: int = 4,
        log_dir: str | Path | None = None,
        seed_description: str = '',
        references: dict[str, int] | None = None,
    ) -> Population:
        log_path = Path(log_dir) if log_dir else None
        if log_path:
            log_path.mkdir(parents=True, exist_ok=True)

        val_instances = val_instances or []
        for step in range(iterations):
            elites = diversify_elites(self.population.topk(), k=3, seed=123 + step)
            elite_thoughts = [candidate.thought for candidate in elites if candidate.thought]
            elite_codes = [candidate.code for candidate in elites]
            thoughts = self.thought_generator.generate(
                n=candidates_per_iteration,
                seed_description=seed_description,
                elite_thoughts=elite_thoughts,
            )
            for idx, item in enumerate(thoughts):
                pair = self.code_generator.generate_code(item.thought, elite_codes=elite_codes)
                try:
                    priority_fn = load_priority_function(pair.code)
                    train_summary = evaluate_priority_function(
                        method_name=f'thought_funsearch_train_iter{step}_cand{idx}',
                        instances=train_instances,
                        priority_fn=priority_fn,
                        references=references,
                    )
                    if val_instances:
                        val_summary = evaluate_priority_function(
                            method_name=f'thought_funsearch_val_iter{step}_cand{idx}',
                            instances=val_instances,
                            priority_fn=priority_fn,
                            references=references,
                        )
                    else:
                        val_summary = train_summary
                    score = objective_from_summary(
                        val_summary.avg_makespan,
                        val_summary.avg_gap_percent,
                        val_summary.avg_runtime_sec,
                    )
                    candidate = Candidate(
                        score=score,
                        code=pair.code,
                        thought=pair.thought,
                        method='thought_funsearch',
                        metrics={'train': train_summary.to_dict(), 'val': val_summary.to_dict()},
                        metadata=pair.metadata,
                    )
                    self.population.add(candidate)
                    if log_path:
                        payload = {
                            'iteration': step,
                            'candidate_idx': idx,
                            'score': score,
                            'train_metrics': train_summary.to_dict(),
                            'val_metrics': val_summary.to_dict(),
                            'thought': pair.thought,
                            'code': pair.code,
                        }
                        (log_path / f'thought_iter{step}_cand{idx}.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
                except SandboxError as exc:
                    if log_path:
                        payload = {
                            'iteration': step,
                            'candidate_idx': idx,
                            'thought': pair.thought,
                            'error': str(exc),
                            'code': pair.code,
                        }
                        (log_path / f'thought_iter{step}_cand{idx}_error.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
        if log_path:
            self.population.export_json(log_path / 'thought_population.json')
        return self.population
