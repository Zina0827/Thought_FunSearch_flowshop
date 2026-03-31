from __future__ import annotations

from pathlib import Path
import csv
import argparse
from time import perf_counter

from core.bks import load_bks
from core.evaluator import evaluate_priority_function
from core.makespan import compute_makespan
from core.parser import load_dataset_splits
from heuristics.lpt import LPTPriority
from heuristics.random_rule import RandomPriority
from heuristics.spt import SPTPriority
from heuristics.neh import neh_sequence, neh_plus_sequence
from core.metrics import gap_to_reference


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = ROOT / 'data' / 'raw'
DEFAULT_SPLITS_DIR = ROOT / 'data' / 'splits'
DEFAULT_BKS_PATH = ROOT / 'data' / 'processed' / 'bks.csv'
DEFAULT_OUTPUT = ROOT / 'results' / 'tables' / 'baseline_results.csv'
DEFAULT_SUMMARY = ROOT / 'results' / 'tables' / 'baseline_summary.csv'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default=str(DEFAULT_RAW_DIR))
    parser.add_argument('--splits_dir', type=str, default=str(DEFAULT_SPLITS_DIR))
    parser.add_argument('--split', type=str, default='test', choices=['train', 'val', 'test', 'all'])
    parser.add_argument('--format_hint', type=str, default='')
    parser.add_argument('--output', type=str, default=str(DEFAULT_OUTPUT))
    parser.add_argument('--summary_output', type=str, default=str(DEFAULT_SUMMARY))
    args = parser.parse_args()

    splits = load_dataset_splits(args.data_dir, args.splits_dir, format_hint=args.format_hint or None)
    if args.split == 'train':
        instances = splits["test"]
    elif args.split == 'val':
        instances = splits["val"]
    elif args.split == 'test':
        instances = splits["test"]
    else:
        instances = splits["train"] + splits["val"] + splits["test"]

    if not instances:
        raise SystemExit('No instances found for the requested split.')

    references = load_bks(DEFAULT_BKS_PATH)
    summaries = [
        evaluate_priority_function('random', instances, RandomPriority(seed=42), references=references),
        evaluate_priority_function('spt', instances, SPTPriority(), references=references),
        evaluate_priority_function('lpt', instances, LPTPriority(), references=references),
    ]

    neh_rows = []
    for method, builder in [('neh', neh_sequence), ('neh_plus', neh_plus_sequence)]:
        for inst in instances:
            start = perf_counter()
            seq = builder(inst["proc_times"])
            runtime = perf_counter() - start
            value = compute_makespan(seq, inst["proc_times"])
            ref = references.get(inst["name"])
            neh_rows.append({
                'instance': inst["name"],
                'method': method,
                'sequence': seq,
                'makespan': value,
                'runtime_sec': runtime,
                'reference': ref,
                'gap_percent': gap_to_reference(value, ref),
            })

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ['instance', 'method', 'sequence', 'makespan', 'runtime_sec', 'reference', 'gap_percent']
    with output.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for summary in summaries:
            for row in summary.results:
                writer.writerow(row.to_dict())
        for row in neh_rows:
            writer.writerow(row)

    summary_output = Path(args.summary_output)
    with summary_output.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['method', 'n_instances', 'avg_makespan', 'median_makespan', 'best_makespan', 'worst_makespan', 'avg_runtime_sec', 'avg_gap_percent'])
        writer.writeheader()
        for summary in summaries:
            writer.writerow(summary.to_dict())
        for method in ('neh', 'neh_plus'):
            rows = [row for row in neh_rows if row['method'] == method]
            makespans = [float(row['makespan']) for row in rows]
            gaps = [row['gap_percent'] for row in rows if row['gap_percent'] is not None]
            runtimes = [float(row['runtime_sec']) for row in rows]
            writer.writerow({
                'method': method,
                'n_instances': len(rows),
                'avg_makespan': sum(makespans) / len(makespans),
                'median_makespan': (sorted(makespans)[len(makespans) // 2] if len(makespans) % 2 == 1 else (sorted(makespans)[len(makespans)//2 - 1] + sorted(makespans)[len(makespans)//2]) / 2.0),
                'best_makespan': min(makespans),
                'worst_makespan': max(makespans),
                'avg_runtime_sec': sum(runtimes) / len(runtimes),
                'avg_gap_percent': (sum(gaps) / len(gaps)) if gaps else None,
            })

    print(f'Saved baseline results to {output}')
    print(f'Saved baseline summary to {summary_output}')


if __name__ == '__main__':
    main()
