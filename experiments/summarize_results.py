from __future__ import annotations

from pathlib import Path
import argparse
import csv
from collections import defaultdict


DEFAULT_TABLE_DIR = Path(__file__).resolve().parents[1] / 'results' / 'tables'
DEFAULT_SUMMARY_PATH = DEFAULT_TABLE_DIR / 'all_tables_summary.txt'


def summarize_csv(path: Path) -> list[dict]:
    rows = []
    with path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows.extend(reader)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--table_dir', type=str, default=str(DEFAULT_TABLE_DIR))
    parser.add_argument('--output', type=str, default=str(DEFAULT_SUMMARY_PATH))
    args = parser.parse_args()

    table_dir = Path(args.table_dir)
    csv_files = sorted(table_dir.glob('*.csv'))
    if not csv_files:
        raise SystemExit(f'No CSV files found in {table_dir}')

    lines: list[str] = []
    for path in csv_files:
        rows = summarize_csv(path)
        lines.append(f'=== {path.name} ===')
        lines.append(f'Rows: {len(rows)}')
        if rows:
            lines.append('Columns: ' + ', '.join(rows[0].keys()))
        lines.append('')

    output = Path(args.output)
    output.write_text('
'.join(lines), encoding='utf-8')
    print(output.read_text(encoding='utf-8'))


if __name__ == '__main__':
    main()
