# Pipeline Guide

This repository can reproduce the workflow from **Materials Project** data fetch to final summary plots.

## Data source

- Website: <https://materialsproject.org/>
- API docs and key management: <https://materialsproject.org/api>
- Required credential: `MP_API_KEY`

## Python dependencies

Install the Python stack with:

```bash
pip install -r requirements.txt
```

Main libraries used:

- `mp-api`
- `pymatgen`
- `pandas`
- `numpy`
- `matplotlib`
- `plotly`
- `adjustText`

## External executable

The fetch-and-strain scripts also need Grimme DFT-D3 through the `s-dftd3` command.

Set its location with:

```bash
S_DFTD3_CMD=/path/to/s-dftd3
```

If `s-dftd3` is already on `PATH`, the default `S_DFTD3_CMD=s-dftd3` is enough.

## Configuration

The shared config loader reads environment variables directly and also auto-loads a repo-local `.env` file if present.

Start from:

```bash
cp .env.example .env
```

Important variables:

- `MP_API_KEY`: Materials Project API key
- `S_DFTD3_CMD`: path or command name for the DFT-D3 executable
- `MP_TASK_WORKERS`: parallel Materials Project task count
- `DFTD3_WORKERS`: parallel strain calculations per structure
- `DFTD3_TIMEOUT_SECONDS`: timeout for one `s-dftd3` call
- `MP_API_SLEEP_SECONDS`: delay between Materials Project requests
- `STRAIN_START`, `STRAIN_STOP`: inclusive strain index range
- `PIPELINE_METALS`: optional comma-separated metal subset
- `PIPELINE_LIGANDS`: optional comma-separated ligand subset
- `ALLOW_IDENTICAL_METAL_PAIRS`: ternary option for pairs like `Sc-Sc`

## Full run

Run the whole workflow with:

```bash
python run_full_pipeline.py
```

Useful variants:

```bash
python run_full_pipeline.py --binary-only
python run_full_pipeline.py --ternary-only
python run_full_pipeline.py --skip-interactive-plots
python run_full_pipeline.py --dry-run
```

## Step-by-step sequence

Binary pipeline:

```bash
python all_d_metals/run_all.py
python all_d_metals/delta_calc.py
python all_d_metals/figure.py
```

Ternary pipeline:

```bash
python all_3_metals/run.py
python all_3_metals/delta.py
python all_3_metals/figure.py
```

Summary analyses:

```bash
python packing_efficiency_analysis.py
python max_delta_point_plots.py
python bar_graph_statistics.py
python binary_electronegativity_vs_delta.py
python plot_binary_metal_focus.py --all
python plot_binary_metal_focus_interactive.py --all
python plot_ternary_pair_focus_interactive.py --all
```

## Output locations

- Binary raw and delta outputs: `all_d_metals/`
- Ternary raw and delta outputs: `all_3_metals/`
- Packing-efficiency results: `packing_efficiency_results/`
- Maximum-delta summaries: `max_delta_point_results/`
- Grouped bar statistics: `bar_graph_statistics/`
- Binary electronegativity summaries: `binary_electronegativity_vs_delta/`
