"""Run ablation experiments comparing thought quality and generated code."""

from __future__ import annotations

from pathlib import Path
import argparse
import csv

from core.bks import load_bks
from core.evaluator import evaluate_priority_function
from core.parser import load_dataset_splits
from llm.code_generator import StubCodeGenerator
from llm.sandbox import load_priority_function
from llm.thought_generator import StubThoughtGenerator
from llm.thought_to_code import StubThoughtToCodeGenerator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = ROOT / 'data' / 'raw'
DEFAULT_SPLITS_DIR = ROOT / 'data' / 'splits'
DEFAULT_BKS_PATH = ROOT / 'data' / 'processed' / 'bks.csv'
DEFAULT_OUTPUT = ROOT / 'results' / 'tables' / 'ablation_results.csv'


def main() -> None:
    """Parse CLI arguments and run the thought-vs-direct ablation evaluation."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default=str(DEFAULT_RAW_DIR))
    parser.add_argument('--splits_dir', type=str, default=str(DEFAULT_SPLITS_DIR))
    parser.add_argument('--split', type=str, default='test', choices=['train', 'val', 'test', 'all'])
    parser.add_argument('--format_hint', type=str, default='')
    parser.add_argument('--output', type=str, default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    splits = load_dataset_splits(args.data_dir, args.splits_dir, format_hint=args.format_hint or None)
    if args.split == 'train':
        instances = splits.train
    elif args.split == 'val':
        instances = splits.val
    elif args.split == 'test':
        instances = splits.test
    else:
        instances = splits.train + splits.val + splits.test

    if not instances:
        raise SystemExit('No instances found for the requested split.')

    references = load_bks(DEFAULT_BKS_PATH)
    direct_code = StubCodeGenerator().generate(n=1)[0].code
    direct_summary = evaluate_priority_function(
        method_name='direct_code',
        instances=instances,
        priority_fn=load_priority_function(direct_code),
        references=references,
    )

    thought = StubThoughtGenerator().generate(n=1)[0].thought
    thought_code = StubThoughtToCodeGenerator().generate_code(thought).code
    thought_summary = evaluate_priority_function(
        method_name='thought_to_code',
        instances=instances,
        priority_fn=load_priority_function(thought_code),
        references=references,
    )

    random_thought = """intuition: choose jobs using a noisy and weak signal
primary_signal: arbitrary combination of totals without clear scheduling meaning
tie_breaker: none
expected_effect: no consistent benefit"""
    random_thought_code = StubThoughtToCodeGenerator().generate_code(random_thought).code
    random_thought_summary = evaluate_priority_function(
        method_name='random_thought_to_code',
        instances=instances,
        priority_fn=load_priority_function(random_thought_code),
        references=references,
    )

    rows = [direct_summary.to_dict(), thought_summary.to_dict(), random_thought_summary.to_dict()]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['method', 'n_instances', 'avg_makespan', 'median_makespan', 'best_makespan', 'worst_makespan', 'avg_runtime_sec', 'avg_gap_percent'])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f'Saved ablation results to {output}')


if __name__ == '__main__':
    main()
