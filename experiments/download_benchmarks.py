"""Command-line entry point for downloading PFSP benchmark data."""

from __future__ import annotations

from pathlib import Path
import argparse

from core.downloader import download_orlibrary, download_taillard

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = ROOT / 'data' / 'raw'


def main() -> None:
    """Parse CLI flags and download the requested benchmark collections."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw_dir', type=str, default=str(DEFAULT_RAW_DIR))
    parser.add_argument('--taillard', action='store_true')
    parser.add_argument('--orlibrary', action='store_true')
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    do_all = not args.taillard and not args.orlibrary
    if args.taillard or do_all:
        archive = download_taillard(raw_dir / 'taillard')
        print(f'Downloaded Taillard archive to {archive}')
    if args.orlibrary or do_all:
        outputs = download_orlibrary(raw_dir / 'orlib')
        for path in outputs:
            print(f'Downloaded {path.name} to {path}')


if __name__ == '__main__':
    main()
