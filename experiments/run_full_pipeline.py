"""Run the end-to-end PFSP benchmark pipeline from the command line."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_module(module: str, extra_args: list[str]) -> None:
    """Run an experiment module as a checked subprocess from the repo root."""
    # Running modules with ``-m`` keeps imports consistent with normal CLI usage
    # and avoids relying on the caller's current working directory.
    cmd = [sys.executable, '-m', module] + extra_args
    subprocess.run(cmd, check=True, cwd=str(ROOT))


def main() -> None:
    """Parse pipeline options and run the selected experiment stages."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['baseline', 'direct', 'thought', 'ablation', 'all'], required=True)
    parser.add_argument('--provider', type=str, default='auto')
    parser.add_argument('--model', type=str, default='gpt-5')
    parser.add_argument('--reasoning_effort', type=str, default='medium')
    args, unknown = parser.parse_known_args()

    # Unknown arguments are forwarded so shared options such as data paths and
    # output locations can be supplied once to the pipeline wrapper.
    if args.mode in {'baseline', 'all'}:
        run_module('experiments.run_baselines', unknown)
    if args.mode in {'direct', 'all'}:
        run_module('experiments.run_direct_funsearch', ['--provider', args.provider, '--model', args.model, '--reasoning_effort', args.reasoning_effort] + unknown)
    if args.mode in {'thought', 'all'}:
        run_module('experiments.run_thought_funsearch', ['--provider', args.provider, '--model', args.model, '--reasoning_effort', args.reasoning_effort] + unknown)
    if args.mode in {'ablation', 'all'}:
        run_module('experiments.run_ablation', ['--provider', args.provider, '--model', args.model, '--reasoning_effort', args.reasoning_effort] + unknown)
    if args.mode == 'all':
        run_module('experiments.plot_results', unknown)


if __name__ == '__main__':
    main()
