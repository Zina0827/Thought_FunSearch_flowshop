from __future__ import annotations

from pathlib import Path
import json

from core.evaluator import evaluate_priority_function
from llm.code_generator import StubCodeGenerator
from llm.sandbox import load_priority_function, SandboxError
from search.population import Candidate, Population
from search.selection import diversify_elites, objective_from_summary


class DirectFunSearch:
    def __init__(self, population_size: int = 8, generator: object | None = None, novelty_weight: float = 0.05) -> None:
        self.population = Population(max_size=population_size, novelty_weight=novelty_weight)
        self.generator = generator or StubCodeGenerator()

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
            elites = diversify_elites(self.population.topk(), k=3, seed=42 + step)
            elite_codes = [candidate.code for candidate in elites]
            raw_candidates = self.generator.generate(
                n=candidates_per_iteration,
                seed_description=seed_description,
                elite_codes=elite_codes,
            )
            for idx, raw in enumerate(raw_candidates):
                try:
                    priority_fn = load_priority_function(raw.code)
                    train_summary = evaluate_priority_function(
                        method_name=f'direct_funsearch_train_iter{step}_cand{idx}',
                        instances=train_instances,
                        priority_fn=priority_fn,
                        references=references,
                    )
                    if val_instances:
                        val_summary = evaluate_priority_function(
                            method_name=f'direct_funsearch_val_iter{step}_cand{idx}',
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
                        code=raw.code,
                        method='direct_funsearch',
                        metrics={'train': train_summary.to_dict(), 'val': val_summary.to_dict()},
                        metadata=raw.metadata,
                    )
                    self.population.add(candidate)
                    if log_path:
                        payload = {
                            'iteration': step,
                            'candidate_idx': idx,
                            'score': score,
                            'train_metrics': train_summary.to_dict(),
                            'val_metrics': val_summary.to_dict(),
                            'code': raw.code,
                        }
                        (log_path / f'direct_iter{step}_cand{idx}.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
                except SandboxError as exc:
                    if log_path:
                        payload = {'iteration': step, 'candidate_idx': idx, 'error': str(exc), 'code': raw.code}
                        (log_path / f'direct_iter{step}_cand{idx}_error.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
        if log_path:
            self.population.export_json(log_path / 'direct_population.json')
        return self.population
