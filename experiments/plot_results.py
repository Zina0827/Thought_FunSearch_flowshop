"""Create summary figures from PFSP experiment result tables."""

from __future__ import annotations

from pathlib import Path
import argparse
import csv

import matplotlib.pyplot as plt


DEFAULT_TABLE_DIR = Path(__file__).resolve().parents[1] / 'results' / 'tables'
DEFAULT_FIGURE_DIR = Path(__file__).resolve().parents[1] / 'results' / 'figures'


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _to_float(value: str | None, default: float = 0.0) -> float:
    if value in (None, '', 'None'):
        return default
    return float(value)


def plot_bar(summary_csv: Path, figure_dir: Path) -> None:
    """Plot baseline average makespan and gap bar charts from a summary CSV."""
    rows = _read_rows(summary_csv)
    methods = [row['method'] for row in rows]
    makespans = [_to_float(row['avg_makespan']) for row in rows]
    gaps = [_to_float(row.get('avg_gap_percent')) for row in rows]

    plt.figure(figsize=(9, 5))
    plt.bar(methods, makespans)
    plt.ylabel('Average Makespan')
    plt.title('PFSP Baseline Comparison')
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(figure_dir / 'baseline_avg_makespan.png', dpi=200)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.bar(methods, gaps)
    plt.ylabel('Average Gap (%)')
    plt.title('PFSP Baseline Gap to Reference')
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(figure_dir / 'baseline_avg_gap.png', dpi=200)
    plt.close()


def plot_method_comparison(table_dir: Path, figure_dir: Path) -> None:
    """Plot a compact comparison across direct, thought, and ablation outputs."""
    files = {
        'direct': table_dir / 'direct_funsearch_best.csv',
        'thought': table_dir / 'thought_funsearch_best.csv',
        'ablation': table_dir / 'ablation_results.csv',
    }
    existing = {name: path for name, path in files.items() if path.exists()}
    if not existing:
        return

    # Search experiments may be run independently, so the comparison plot is built
    # from whichever result tables are present instead of requiring a full pipeline.
    labels: list[str] = []
    values: list[float] = []
    for name, path in existing.items():
        rows = _read_rows(path)
        if not rows:
            continue
        row = rows[0]
        labels.append(name)
        metric = row.get('avg_makespan') or row.get('best_makespan') or row.get('thought_avg_makespan') or row.get('direct_avg_makespan')
        values.append(_to_float(metric))

    if labels:
        plt.figure(figsize=(8, 5))
        plt.bar(labels, values)
        plt.ylabel('Average Makespan')
        plt.title('Search Method Comparison')
        plt.tight_layout()
        plt.savefig(figure_dir / 'search_method_comparison.png', dpi=200)
        plt.close()


def main() -> None:
    """Parse CLI arguments and create available result figures."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary_csv', type=str, default=str(DEFAULT_TABLE_DIR / 'baseline_summary.csv'))
    parser.add_argument('--table_dir', type=str, default=str(DEFAULT_TABLE_DIR))
    parser.add_argument('--figure_dir', type=str, default=str(DEFAULT_FIGURE_DIR))
    args = parser.parse_args()

    summary_csv = Path(args.summary_csv)
    table_dir = Path(args.table_dir)
    figure_dir = Path(args.figure_dir)
    figure_dir.mkdir(parents=True, exist_ok=True)

    if summary_csv.exists():
        plot_bar(summary_csv, figure_dir)
    plot_method_comparison(table_dir, figure_dir)
    print(f'Saved figures to {figure_dir}')


if __name__ == '__main__':
    main()
