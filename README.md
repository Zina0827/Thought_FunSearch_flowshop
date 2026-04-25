# Flow Shop Thought-Augmented FunSearch

A research-ready starter framework for the permutation flow shop scheduling problem (PFSP).

Traditional-method references and exploratory notebooks are kept in `traditional_method/`.
The main notebooks are `traditional_method/Google_OR_Tool.ipynb` and
`traditional_method/KamilGos_With_Flowshop1_Data.ipynb`; the supporting
implementations from the KamilGos reference are under `traditional_method/KamilGos/`.

## What is included
- Benchmark-aware parsers for simple PFSP files, Taillard PFSP files, and OR-Library multi-instance files
- Split generation and split loading
- Classical baselines: Random, SPT, LPT, NEH, NEH+
- Direct code-generation search
- Thought-augmented search
- Safe sandbox execution for generated priority functions
- Benchmark download helpers
- Plotting and report scaffolding

## Project structure
- `core/`: parsing, evaluation, metrics, split generation, benchmark download helpers
- `heuristics/`: classical priority rules and NEH-style builders
- `llm/`: prompt builders, OpenAI-backed generators, fallback stub generators, sandbox
- `search/`: candidate population and search loops
- `experiments/`: runnable entry points
- `report/`: outline and notes for the final writeup

## Algorithm Overview
The project searches for priority functions for the permutation flow shop scheduling problem. A priority function scores each unscheduled job from the current partial sequence, and the greedy scheduler repeatedly selects the best-scoring job until a full sequence is built. The final sequence is evaluated by makespan and, when available, gap to a best-known reference value.

The direct FunSearch path asks a generator to produce Python `priority(...)` functions directly. Each candidate is sandboxed, evaluated on training instances, optionally ranked on validation instances, and retained in a bounded population. The population uses both objective score and a small novelty bonus so later prompts can reuse strong ideas without collapsing to near-duplicate code.

The thought-augmented path separates the search into two stages. First, a generator proposes a structured heuristic thought describing the scheduling intuition, signal, tie-breaker, and expected effect. Second, another generator translates that thought into executable priority-function code. This makes the generated heuristic easier to inspect and supports the ablation between direct code generation and thought-to-code generation.

Classical baselines provide reference points: Random, SPT, LPT, NEH, and NEH+. NEH constructs a sequence by sorting influential jobs first and inserting each job into the position that minimizes partial makespan; NEH+ adds local adjacent-swap and reinsertion refinements.

## Code Structure Details
- `core/parser.py`: loads PFSP instances from simple text files, Taillard files, and OR-Library files.
- `core/scheduler.py`: builds a greedy schedule from a priority function.
- `core/makespan.py`: computes completion times and makespan for a sequence.
- `core/evaluator.py`: evaluates one priority function across a split and summarizes makespan, runtime, and reference gaps.
- `core/bks.py`: loads best-known solution references from built-in defaults plus optional CSV/JSON files.
- `heuristics/`: contains baseline priority rules and NEH-style constructive heuristics.
- `llm/prompts.py`: stores prompt templates for direct generation, thought generation, and thought-to-code conversion.
- `llm/code_generator.py`, `llm/thought_generator.py`, `llm/thought_to_code.py`: provide OpenAI-backed generators and deterministic stub fallbacks.
- `llm/sandbox.py`: parses and executes generated code with a restricted AST and builtin set.
- `search/population.py`: stores generated candidates, removes duplicate code, ranks by score plus novelty, and exports logs.
- `search/direct_funsearch.py`: runs the direct code-generation search loop.
- `search/thought_funsearch.py`: runs the thought-augmented search loop.
- `experiments/`: command-line scripts for downloading data, making splits, running baselines/search, summarizing tables, and plotting figures.

## Installation
```bash
pip install -r requirements.txt
```

To use OpenAI-backed generation, set:
```bash
export OPENAI_BASE_URL="https://hk-api.gptbest.vip"
export OPENAI_API_KEY="sk-0TF42ZPrrqdGcumljLXQ0Zd9gF7PvRXYfEamuMQqoz1VHN9S"
export OPENAI_MODEL="gpt-5-nano"
```

## Supported instance formats
### Simple format
First line: `n_jobs n_machines`
Then `n_jobs` rows of `n_machines` processing times.

### Taillard format
The parser accepts common Taillard headers, including files whose first row is:
`n_jobs n_machines seed upper_bound lower_bound`
followed by the processing-time matrix.

### OR-Library format
The parser scans a text file and extracts one or more PFSP instances stored sequentially.

## Download benchmarks
```bash
python -m experiments.download_benchmarks
```

## Generate splits
```bash
python -m experiments.make_splits --data_dir data/raw --splits_dir data/splits
```

## Run baselines
```bash
python -m experiments.run_baselines --split test
```

## Run direct FunSearch
```bash
python -m experiments.run_direct_funsearch   --provider openai   --model gpt-5   --reasoning_effort medium   --split train
```

## Run thought-augmented FunSearch
```bash
python -m experiments.run_thought_funsearch   --provider openai   --model gpt-5   --reasoning_effort medium   --split train
```

## Run the full pipeline
```bash
python -m experiments.run_full_pipeline --mode all --provider openai --model gpt-5
```

## Reproduce Results
To reproduce the included workflow from a fresh checkout:

1. Install dependencies.
   ```bash
   pip install -r requirements.txt
   ```

2. Download benchmark files, or keep the existing files under `data/raw/`.
   ```bash
   python -m experiments.download_benchmarks
   ```

3. Generate train/validation/test split files.
   ```bash
   python -m experiments.make_splits --data_dir data/raw --splits_dir data/splits
   ```

4. Run the baseline heuristics on the test split.
   ```bash
   python -m experiments.run_baselines --split test
   ```

5. Run direct search. Use `--provider stub` for a deterministic offline run, or `--provider openai` when API credentials are configured.
   ```bash
   python -m experiments.run_direct_funsearch --provider stub --split train
   ```

6. Run thought-augmented search.
   ```bash
   python -m experiments.run_thought_funsearch --provider stub --split train
   ```

7. Run the ablation and generate plots.
   ```bash
   python -m experiments.run_ablation --split test
   python -m experiments.plot_results
   ```

Result CSV files are written to `results/tables/`, figures to `results/figures/`, and generated candidate logs to `results/logs/`. For one-command reproduction, use:

```bash
python -m experiments.run_full_pipeline --mode all --provider stub
```

## Results
Result tables are stored in `results/tables/`.
Figures are stored in `results/figures/`.
Candidate logs are stored in `results/logs/`.

## Notes on OpenAI API usage
The OpenAI-backed generators in `llm/` use the Python SDK `OpenAI()` client and call the Responses API via `client.responses.create(...)`. The code includes a stub fallback so the framework remains runnable without credentials.

## Suggested report framing
- Compare classical baselines against search-generated heuristics.
- Report both makespan and gap to best-known values where available.
- Include an ablation showing whether thought improves code quality over direct generation.
