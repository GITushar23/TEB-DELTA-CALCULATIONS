# TEB-DELTA-CALCULATIONS

Reproducible scripts and analysis outputs for binary and ternary delta-energy studies on d-metal oxides and sulfides.

This repo is organized so someone else can regenerate the workflow from the original **Materials Project** source data through the final summary plots.

## Source data

- Website: <https://materialsproject.org/>
- API key required: `MP_API_KEY`

The fetch scripts query Materials Project directly, download structures, convert them to POSCAR-style inputs, run strained `s-dftd3` calculations, detect delta dips, and build the downstream plots.

## What is included

- Binary fetch / strain / delta scripts in [binary_delta_pipeline](./binary_delta_pipeline)
- Ternary fetch / strain / delta scripts in [ternary_delta_pipeline](./ternary_delta_pipeline)
- Analysis scripts in [scripts/analysis](./scripts/analysis)
- Plotting scripts in [scripts/plotting](./scripts/plotting)
- Shared pipeline config in [scripts/pipeline_config.py](./scripts/pipeline_config.py)
- One-command orchestration in [scripts/run_full_pipeline.py](./scripts/run_full_pipeline.py)

## Setup

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Provide your Materials Project API key and DFT-D3 command:

   ```bash
   cp .env.example .env
   ```

   Then edit `.env` and set:

   ```bash
   MP_API_KEY=your_key_here
   S_DFTD3_CMD=s-dftd3
   ```

   If `s-dftd3` is not on `PATH`, use the full executable path.

## Run

Run the full pipeline:

```bash
python scripts/run_full_pipeline.py
```

Useful options:

```bash
python scripts/run_full_pipeline.py --binary-only
python scripts/run_full_pipeline.py --ternary-only
python scripts/run_full_pipeline.py --skip-interactive-plots
python scripts/run_full_pipeline.py --dry-run
```

## Main outputs

- `binary_delta_pipeline/`: binary CSVs, aggregated outputs, delta tables, and binary comparison plots
- `ternary_delta_pipeline/`: ternary CSVs, aggregated outputs, delta tables, and ternary comparison plots
- `packing_efficiency_results/`
- `max_delta_point_results/`
- `bar_graph_statistics/`
- `binary_electronegativity_vs_delta/`

More detail is in [docs/pipeline.md](./docs/pipeline.md).
