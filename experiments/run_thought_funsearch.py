from __future__ import annotations

from pathlib import Path
import argparse
import csv

from core.bks import load_bks
from core.evaluator import evaluate_priority_function
from core.parser import load_dataset_splits
from llm.thought_generator import build_thought_generator
from llm.thought_to_code import build_thought_to_code_generator
from llm.sandbox import load_priority_function
from search.thought_funsearch import ThoughtFunSearch


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = ROOT / 'data' / 'raw'
DEFAULT_SPLITS_DIR = ROOT / 'data' / 'splits'
DEFAULT_BKS_PATH = ROOT / 'data' / 'processed' / 'bks.csv'
DEFAULT_LOG_DIR = ROOT / 'results' / 'logs' / 'thought'
DEFAULT_OUTPUT = ROOT / 'results' / 'tables' / 'thought_funsearch_best.csv'
DEFAULT_TEST_OUTPUT = ROOT / 'results' / 'tables' / 'thought_funsearch_test.csv'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default=str(DEFAULT_RAW_DIR))
    parser.add_argument('--splits_dir', type=str, default=str(DEFAULT_SPLITS_DIR))
    parser.add_argument('--split', type=str, default='train', choices=['train', 'val', 'test', 'all'])
    parser.add_argument('--format_hint', type=str, default='')
    parser.add_argument('--provider', type=str, default='auto', choices=['auto', 'stub', 'openai'])
    parser.add_argument('--model', type=str, default='')
    parser.add_argument('--reasoning_effort', type=str, default='medium')
    parser.add_argument('--iterations', type=int, default=4)
    parser.add_argument('--candidates_per_iteration', type=int, default=6)
    parser.add_argument('--log_dir', type=str, default=str(DEFAULT_LOG_DIR))
    parser.add_argument('--output', type=str, default=str(DEFAULT_OUTPUT))
    parser.add_argument('--test_output', type=str, default=str(DEFAULT_TEST_OUTPUT))
    args = parser.parse_args()

    dataset = load_dataset_splits(args.data_dir, args.splits_dir, format_hint=args.format_hint or None)
    references = load_bks(DEFAULT_BKS_PATH)
    train_instances = dataset['train']
    val_instances = dataset['val']
    test_instances = dataset['test']
    active_instances = train_instances if args.split == 'train' else val_instances if args.split == 'val' else test_instances if args.split == 'test' else train_instances + val_instances + test_instances

    if not active_instances:
        raise SystemExit('No instances found for the requested split.')

    thought_generator = build_thought_generator(
        provider=args.provider,
        model=args.model or None,
        reasoning_effort=args.reasoning_effort,
    )
    code_generator = build_thought_to_code_generator(
        provider=args.provider,
        model=args.model or None,
        reasoning_effort=args.reasoning_effort,
    )

    engine = ThoughtFunSearch(population_size=8, thought_generator=thought_generator, code_generator=code_generator)
    population = engine.run(
        train_instances=active_instances,
        val_instances=val_instances if args.split in {'train', 'all'} else [],
        iterations=args.iterations,
        candidates_per_iteration=args.candidates_per_iteration,
        log_dir=args.log_dir,
        references=references,
    )

    best = population.best()
    if best is None:
        raise SystemExit('No valid thought-augmented candidates were produced.')

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['method', 'score', 'thought', 'code', 'metrics'])
        writer.writeheader()
        writer.writerow({'method': best.method, 'score': best.score, 'thought': best.thought, 'code': best.code, 'metrics': best.metrics})

    if test_instances:
        test_summary = evaluate_priority_function(
            method_name='thought_funsearch_best',
            instances=test_instances,
            priority_fn=load_priority_function(best.code),
            references=references,
        )
        test_output = Path(args.test_output)
        with test_output.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['instance', 'method', 'sequence', 'makespan', 'runtime_sec', 'reference', 'gap_percent'])
            writer.writeheader()
            for row in test_summary.results:
                writer.writerow(row.to_dict())

    print(f'Saved best thought-augmented candidate to {output}')


if __name__ == '__main__':
    main()
