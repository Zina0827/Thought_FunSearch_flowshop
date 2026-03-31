# Flow Shop Thought-Augmented FunSearch

A research-ready starter framework for the permutation flow shop scheduling problem (PFSP).

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
