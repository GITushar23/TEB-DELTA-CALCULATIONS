#!/usr/bin/env python3
"""
Recalculate delta_E from existing s-dftd3 strain CSVs using local dip shoulders.

This script does not rerun s-dftd3. It reads:
    hardcoded_8_material_results/aggregated/*_output.csv

and writes:
    hardcoded_8_material_results/delta_analysis_local/delta_summary_local.csv
    hardcoded_8_material_results/delta_analysis_local/plots/*_delta_local.png

The older delta script can fail on narrow one-point drops because it falls back
to a global gradient baseline. Here the baseline is anchored at the local
pre-drop shoulder and the first recovered point on the post-dip branch.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "hardcoded_8_material_results"
AGG_DIR = RESULTS_DIR / "aggregated"
OUT_DIR = RESULTS_DIR / "delta_analysis_local"
PLOT_DIR = OUT_DIR / "plots"

LOCAL_SEARCH_WINDOW = 10
MIN_ABSOLUTE_DROP = 1.0e-4
MIN_RELATIVE_DROP = 0.01


@dataclass(frozen=True)
class DipResult:
    source: str
    material: str
    material_id: str
    space_group_symbol: str
    n_points: int
    peak_idx: int
    dip_idx: int
    right_idx: int
    peak_cell_length: float
    dip_cell_length: float
    right_cell_length: float
    E_peak: float
    E_min: float
    E_right: float
    E_expected_dip: float
    delta_E: float
    raw_drop: float
    baseline_slope: float
    baseline_intercept: float
    method: str


def clean_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["cell_length"] = pd.to_numeric(df["cell_length"], errors="coerce")
    df["Edis"] = pd.to_numeric(df["Edis"], errors="coerce")
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["cell_length", "Edis"])
    df = df.sort_values("cell_length").reset_index(drop=True)
    return df


def infer_material_name(path: Path, df: pd.DataFrame) -> str:
    if "formula" in df.columns and df["formula"].notna().any():
        return str(df["formula"].dropna().iloc[0])
    return path.stem.replace("_output", "").split("_")[0]


def infer_material_id(path: Path, df: pd.DataFrame) -> str:
    if "material_id" in df.columns and df["material_id"].notna().any():
        return str(df["material_id"].dropna().iloc[0])
    parts = path.stem.replace("_output", "").split("_")
    return f"mp-{parts[-1]}" if parts[-1].isdigit() else ""


def infer_space_group(df: pd.DataFrame) -> str:
    if "space_group_symbol" in df.columns and df["space_group_symbol"].notna().any():
        return str(df["space_group_symbol"].dropna().iloc[0])
    return ""


def adaptive_drop_threshold(y: np.ndarray) -> float:
    span = float(np.nanmax(y) - np.nanmin(y))
    return max(MIN_ABSOLUTE_DROP, MIN_RELATIVE_DROP * span)


def find_best_local_dip(x: np.ndarray, y: np.ndarray) -> Optional[tuple[int, int, float]]:
    """
    Return (peak_idx, dip_idx, raw_drop).

    The s-dftd3 artifact appears as a downward interruption in a curve that is
    otherwise generally recovering upward. For each point followed by a drop,
    search a short window for the local minimum and keep the strongest drop.
    """
    min_drop = adaptive_drop_threshold(y)
    best: Optional[tuple[int, int, float]] = None

    for peak_idx in range(1, len(y) - 1):
        if y[peak_idx + 1] >= y[peak_idx]:
            continue

        end = min(len(y), peak_idx + LOCAL_SEARCH_WINDOW + 1)
        dip_idx = peak_idx + int(np.argmin(y[peak_idx + 1 : end])) + 1
        raw_drop = float(y[peak_idx] - y[dip_idx])

        if raw_drop < min_drop:
            continue

        if best is None or raw_drop > best[2]:
            best = (peak_idx, dip_idx, raw_drop)

    return best


def find_right_recovery_idx(y: np.ndarray, peak_idx: int, dip_idx: int) -> int:
    """
    Pick the first post-dip point that has recovered to the pre-drop shoulder.
    If the curve never recovers that far, use the highest post-dip point.
    """
    peak_y = y[peak_idx]
    for idx in range(dip_idx + 1, len(y)):
        if y[idx] >= peak_y:
            return idx

    post = y[dip_idx + 1 :]
    if len(post) == 0:
        return min(dip_idx + 1, len(y) - 1)
    return dip_idx + 1 + int(np.argmax(post))


def calculate_delta(path: Path) -> Optional[DipResult]:
    df = clean_data(path)
    if len(df) < 5:
        return None

    x = df["cell_length"].to_numpy(dtype=float)
    y = df["Edis"].to_numpy(dtype=float)
    found = find_best_local_dip(x, y)
    if found is None:
        return None

    peak_idx, dip_idx, raw_drop = found
    right_idx = find_right_recovery_idx(y, peak_idx, dip_idx)
    if right_idx <= dip_idx:
        return None

    dx = float(x[right_idx] - x[peak_idx])
    if abs(dx) < 1.0e-12:
        return None

    slope = float((y[right_idx] - y[peak_idx]) / dx)
    intercept = float(y[peak_idx] - slope * x[peak_idx])
    expected = float(slope * x[dip_idx] + intercept)
    delta_e = float(y[dip_idx] - expected)

    return DipResult(
        source=str(df["source"].iloc[0]) if "source" in df.columns and len(df) else path.stem,
        material=infer_material_name(path, df),
        material_id=infer_material_id(path, df),
        space_group_symbol=infer_space_group(df),
        n_points=len(df),
        peak_idx=peak_idx,
        dip_idx=dip_idx,
        right_idx=right_idx,
        peak_cell_length=float(x[peak_idx]),
        dip_cell_length=float(x[dip_idx]),
        right_cell_length=float(x[right_idx]),
        E_peak=float(y[peak_idx]),
        E_min=float(y[dip_idx]),
        E_right=float(y[right_idx]),
        E_expected_dip=expected,
        delta_E=delta_e,
        raw_drop=raw_drop,
        baseline_slope=slope,
        baseline_intercept=intercept,
        method="local_peak_dip_recovery",
    )


def plot_result(path: Path, result: DipResult) -> None:
    df = clean_data(path)
    x = df["cell_length"].to_numpy(dtype=float)
    y = df["Edis"].to_numpy(dtype=float)
    baseline = result.baseline_slope * x + result.baseline_intercept

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(x, y, "o-", label="s-dftd3 Edis")
    ax.plot(x, baseline, "--", label="local baseline")
    ax.scatter([result.peak_cell_length], [result.E_peak], s=70, label="left shoulder", zorder=3)
    ax.scatter([result.dip_cell_length], [result.E_min], s=80, label="dip", zorder=3)
    ax.scatter([result.right_cell_length], [result.E_right], s=70, label="right recovery", zorder=3)
    ax.set_xlabel("Cell length")
    ax.set_ylabel("Dispersion energy (Edis)")
    ax.set_title(f"{result.material}: delta_E = {result.delta_E:.6f}")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    out_png = PLOT_DIR / f"{path.stem.replace('_output', '')}_delta_local.png"
    fig.savefig(out_png, dpi=300)
    plt.close(fig)


def write_summary(results: list[DipResult]) -> Path:
    out_csv = OUT_DIR / "delta_summary_local.csv"
    fieldnames = list(DipResult.__dataclass_fields__.keys())
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.__dict__)
    return out_csv


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    csv_paths = sorted(AGG_DIR.glob("*_output.csv"))
    if not csv_paths:
        raise SystemExit(f"No aggregated CSV files found in {AGG_DIR}")

    results: list[DipResult] = []
    skipped: list[str] = []

    for path in csv_paths:
        result = calculate_delta(path)
        if result is None:
            skipped.append(path.name)
            print(f"[SKIP] {path.name}: no local drop detected")
            continue
        results.append(result)
        plot_result(path, result)
        print(
            f"[OK] {result.material:8s} {result.material_id:12s} "
            f"dip={result.dip_cell_length:.6f} delta_E={result.delta_E:.8f}"
        )

    summary_path = write_summary(results)
    print(f"\nWrote {summary_path}")
    print(f"Wrote plots to {PLOT_DIR}")
    if skipped:
        print(f"Skipped: {', '.join(skipped)}")


if __name__ == "__main__":
    main()
