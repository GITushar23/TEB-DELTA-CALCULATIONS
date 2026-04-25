#!/usr/bin/env python3
"""
Self-contained TEB exam D3 strain runner.

This script does not need Materials Project access. The eight selected
Materials Project structures are embedded below as POSCAR text.

Run:
    python run_hardcoded_8_materials.py

Optional environment variables:
    S_DFTD3_CMD=s-dftd3
    DFTD3_WORKERS=4
    DFTD3_TIMEOUT_SECONDS=900
    STRAIN_START=-5
    STRAIN_STOP=29
"""

from __future__ import annotations

import csv
import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "hardcoded_8_material_results"
POSCAR_DIR = OUT_DIR / "poscars"
STRAIN_DIR = OUT_DIR / "strains"
AGG_DIR = OUT_DIR / "aggregated"
PLOT_DIR = OUT_DIR / "plots"
DELTA_DIR = OUT_DIR / "delta_analysis"
DELTA_PLOT_DIR = DELTA_DIR / "plots"

S_DFTD3_CMD = os.environ.get("S_DFTD3_CMD", "s-dftd3")
DFTD3_WORKERS = int(os.environ.get("DFTD3_WORKERS", "4"))
DFTD3_TIMEOUT_SECONDS = int(os.environ.get("DFTD3_TIMEOUT_SECONDS", "900"))
STRAIN_START = int(os.environ.get("STRAIN_START", "-5"))
STRAIN_STOP = int(os.environ.get("STRAIN_STOP", "29"))
STRAIN_INDICES = list(range(STRAIN_START, STRAIN_STOP + 1))

MIN_POINTS = 10
SLOPE_SIGMA = 2.0
RIGHT_FLAT_PCTILE = 25
RIGHT_MIN_OFFSET = 2
LEFT_FALLBACK_FRAC = 0.33
MIN_DIP_DROP = 0.05
LOCAL_MAX_WINDOW = 15


@dataclass(frozen=True)
class Material:
    name: str
    material_id: str
    formula: str
    crystal_system: str
    space_group_symbol: str
    space_group_number: int
    nsites: int
    energy_above_hull: float
    formation_energy_per_atom: float
    is_stable: bool
    volume: float
    density: float
    band_gap: float
    is_gap_direct: bool
    is_metal: bool
    ordering: str
    total_magnetization: float
    poscar: str


MATERIALS = [
    Material(
        name="NiO",
        material_id="mp-19009",
        formula="NiO",
        crystal_system="Cubic",
        space_group_symbol="Fm-3m",
        space_group_number=225,
        nsites=2,
        energy_above_hull=0.0,
        formation_energy_per_atom=-1.218085299999999,
        is_stable=True,
        volume=18.34183362776642,
        density=6.762154477618838,
        band_gap=2.300899999999999,
        is_gap_direct=False,
        is_metal=False,
        ordering="FM",
        total_magnetization=2.0000001,
        poscar="""Ni1 O1
1.0
   2.5635985799999998   -0.0000000100000000    1.4800937100000000
   0.8545325200000000    2.4169825600000001    1.4800937100000000
  -0.0000000000000000   -0.0000000000000000    2.9601874300000000
Ni O
1 1
direct
   0.0000000000000000   -0.0000000000000000   -0.0000000000000000 Ni
   0.5000000000000000    0.5000000000000000    0.5000010000000000 O
""",
    ),
    Material(
        name="CoO",
        material_id="mp-22408",
        formula="CoO",
        crystal_system="Cubic",
        space_group_symbol="F-43m",
        space_group_number=216,
        nsites=4,
        energy_above_hull=0.0,
        formation_energy_per_atom=-1.2718311462500012,
        is_stable=True,
        volume=45.6458388279094,
        density=5.451909946417111,
        band_gap=0.5880000000000001,
        is_gap_direct=True,
        is_metal=False,
        ordering="AFM",
        total_magnetization=0.0000007,
        poscar="""Co2 O2
1.0
   2.7751261000000000    0.0000000300000000    1.6022204000000000
   0.9250430900000001    2.6164141000000001    1.6022203900000000
  -0.8779556500000000   -2.5831191200000001    4.7251026400000002
Co O
2 2
direct
   0.0010245500000000    0.9994877300000000    0.9984631800000000 Co
   0.0010181600000000    0.4994909200000000    0.4984717700000000 Co
   0.2490082800000000    0.3754958600000000    0.1264865800000000 O
   0.2489490100000000    0.8755254900000000    0.6265764800000000 O
""",
    ),
    Material(
        name="FeO",
        material_id="mp-1274279",
        formula="FeO",
        crystal_system="Monoclinic",
        space_group_symbol="C2/m",
        space_group_number=12,
        nsites=8,
        energy_above_hull=0.0,
        formation_energy_per_atom=-1.481519387499999,
        is_stable=True,
        volume=84.98847683834407,
        density=5.6148992124359385,
        band_gap=1.8157,
        is_gap_direct=False,
        is_metal=False,
        ordering="AFM",
        total_magnetization=0.0000002,
        poscar="""Fe4 O4
1.0
   2.1766480000000001   -2.2104390000000000   -0.0197360000000000
   2.1576909999999998    2.1571919999999989   -4.4259459999999997
   2.1635130000000000    2.2368310000000000    4.4666480000000002
Fe O
4 4
direct
   0.5000000000000000    0.0000000000000000    0.5000000000000000 Fe
   0.0000000000000000    0.5000000000000000    0.5000000000000000 Fe
   0.0000000000000000    0.0000000000000000    0.0000000000000000 Fe
   0.5000010000000000    0.5000000000000000    0.0000000000000000 Fe
   0.9682909999999991    0.2516760000000000    0.7420660000000000 O
   0.4683130000000000    0.2516730000000000    0.2420679999999990 O
   0.0317090000000000    0.7483240000000000    0.2579340000000000 O
   0.5316860000000000    0.7483270000000000    0.7579319999999991 O
""",
    ),
    Material(
        name="TiO2",
        material_id="mp-390",
        formula="TiO2",
        crystal_system="Tetragonal",
        space_group_symbol="I4_1/amd",
        space_group_number=141,
        nsites=6,
        energy_above_hull=0.0,
        formation_energy_per_atom=-3.5080554519444442,
        is_stable=True,
        volume=68.78397225482972,
        density=3.856139057916947,
        band_gap=2.0586,
        is_gap_direct=False,
        is_metal=False,
        ordering="NM",
        total_magnetization=0.0,
        poscar="""Ti2 O4
1.0
   3.5477163100000002    0.0000000000000000   -1.3119886300000001
  -0.4851878600000000    3.5143827700000001   -1.3119886300000001
   0.0180249800000000    0.0206831400000000    5.5013829899999998
Ti O
2 4
direct
   0.8750000000000000    0.6250000000000000    0.2500000000000000 Ti
   0.1250000000000000    0.3750000000000000    0.7500000000000000 Ti
   0.3321526300000000    0.5821526300000001    0.1643042500000000 O
   0.0821526300000000    0.8321526300000001    0.6643042500000000 O
   0.9178473700000001    0.1678473700000000    0.3356957500000000 O
   0.6678473700000001    0.4178473700000000    0.8356957500000001 O
""",
    ),
    Material(
        name="RuO2",
        material_id="mp-825",
        formula="RuO2",
        crystal_system="Tetragonal",
        space_group_symbol="P4_2/mnm",
        space_group_number=136,
        nsites=6,
        energy_above_hull=0.0,
        formation_energy_per_atom=-1.457661898333333,
        is_stable=True,
        volume=62.515586451455455,
        density=7.0691471835481,
        band_gap=0.0,
        is_gap_direct=False,
        is_metal=True,
        ordering="NM",
        total_magnetization=0.0000001,
        poscar="""Ru2 O4
1.0
   3.1113414000000001    0.0000000000000000    0.0000000000000000
   0.0000000000000000    4.4816475300000000   -0.0000000000000000
   0.0000000000000000    0.0000000000000000    4.4833530999999986
Ru O
2 4
direct
   0.5000000000000000    0.5000000000000000    0.5000000000000000 Ru
  -0.0000000000000000    0.0000000000000000   -0.0000000000000000 Ru
   0.5000000000000000    0.8053618700000000    0.1944775500000000 O
   0.5000000000000000    0.1946381300000000    0.8055224500000000 O
   0.0000000000000000    0.6946381300000000    0.6944775500000000 O
  -0.0000000000000000    0.3053618700000000    0.3055224500000000 O
""",
    ),
    Material(
        name="IrO2",
        material_id="mp-2723",
        formula="IrO2",
        crystal_system="Tetragonal",
        space_group_symbol="P4_2/mnm",
        space_group_number=136,
        nsites=6,
        energy_above_hull=0.0,
        formation_energy_per_atom=-1.260892841666664,
        is_stable=True,
        volume=64.48031649722306,
        density=11.548302349446649,
        band_gap=0.0,
        is_gap_direct=False,
        is_metal=True,
        ordering="NM",
        total_magnetization=0.0,
        poscar="""Ir2 O4
1.0
   3.1767062400000001    0.0000000000000000    0.0000000000000000
   0.0000000000000000    4.5053138700000002   -0.0000000000000000
   0.0000000000000000   -0.0000000000000000    4.5053138700000002
Ir O
2 4
direct
   0.5000000000000000    0.5000000000000000    0.5000000000000000 Ir
  -0.0000000000000000    0.0000000000000000    0.0000000000000000 Ir
   0.0000000000000000    0.6913366999999990    0.6913366999999990 O
   0.5000000000000000    0.8086633000000000    0.1913367000000000 O
   0.0000000000000000    0.3086633000000000    0.3086633000000000 O
   0.5000000000000000    0.1913367000000000    0.8086633000000000 O
""",
    ),
    Material(
        name="SrTiO3",
        material_id="mp-4651",
        formula="SrTiO3",
        crystal_system="Tetragonal",
        space_group_symbol="I4/mcm",
        space_group_number=140,
        nsites=10,
        energy_above_hull=0.0,
        formation_energy_per_atom=-3.551662291666667,
        is_stable=True,
        volume=119.62507795144641,
        density=5.093987781835845,
        band_gap=1.848799999999999,
        is_gap_direct=False,
        is_metal=False,
        ordering="NM",
        total_magnetization=0.0,
        poscar="""Sr2 Ti2 O6
1.0
   4.7827101699999996    0.0000000000000000   -2.7607623500000003
  -1.5936169599999990    4.5094012899999996   -2.7607623500000003
   0.0067837700000000    0.0095921300000000    5.5348860100000001
Sr Ti O
2 2 6
direct
   0.7500000000000000    0.2500000000000000    0.5000000000000000 Sr
   0.2500000000000000    0.7500000000000000    0.5000000000000000 Sr
   0.5000000000000000    0.5000000000000000   -0.0000000000000000 Ti
  -0.0000000000000000    0.0000000000000000   -0.0000000000000000 Ti
   0.7709574500000000    0.2709574500000000   -0.0000000000000000 O
   0.7290425500000001    0.7709574500000000    0.0000000000000000 O
   0.2709574500000000    0.2290425500000000   -0.0000000000000000 O
   0.2290425500000000    0.7290425500000001    0.0000000000000000 O
   0.2500000000000000    0.2500000000000000    0.5000000000000000 O
   0.7500000000000000    0.7500000000000000    0.5000000000000000 O
""",
    ),
    Material(
        name="LaMnO3",
        material_id="mp-17554",
        formula="LaMnO3",
        crystal_system="Orthorhombic",
        space_group_symbol="Pnma",
        space_group_number=62,
        nsites=20,
        energy_above_hull=0.125533495023809,
        formation_energy_per_atom=-3.009731305586207,
        is_stable=False,
        volume=255.08175724819074,
        density=6.297394529869173,
        band_gap=0.0,
        is_gap_direct=False,
        is_metal=True,
        ordering="FM",
        total_magnetization=16.0083734,
        poscar="""La4 Mn4 O12
1.0
   5.8714300000000001    0.0000080000000000    0.0000040000000000
   0.0000100000000000    7.7774169999999998   -0.0068860000000000
   0.0000040000000000   -0.0049000000000000    5.5859940000000003
La Mn O
4 4 12
direct
   0.0576120000000000    0.2502240000000000    0.9888460000000000 La
   0.9424070000000000    0.7497549999999999    0.0111760000000000 La
   0.5576190000000000    0.2497740000000000    0.5111479999999990 La
   0.4424209999999990    0.7502150000000000    0.4888260000000000 La
   0.9999629999999990    0.9999709999999991    0.4999650000000000 Mn
   0.0000070000000000    0.5000240000000000    0.5000669999999990 Mn
   0.4999800000000000    0.5000550000000000    0.9999579999999991 Mn
   0.4999559999999990    0.9999779999999990    0.0000510000000000 Mn
   0.4789859999999990    0.2486950000000000    0.0867810000000000 O
   0.5210210000000000    0.7513010000000000    0.9131870000000000 O
   0.9789850000000000    0.2513100000000000    0.4132170000000000 O
   0.0210220000000000    0.7487020000000000    0.5868129999999990 O
   0.3100370000000000    0.0441229999999990    0.7190200000000001 O
   0.6888600000000000    0.5442500000000000    0.2796360000000000 O
   0.6900100000000000    0.9558280000000000    0.2810410000000000 O
   0.3110970000000000    0.4557960000000000    0.7203079999999999 O
   0.8099959999999991    0.4558800000000001    0.7810349999999990 O
   0.1889020000000000    0.9557490000000000    0.2202889999999990 O
   0.1899750000000000    0.5441739999999990    0.2190190000000000 O
   0.8111440000000000    0.0441980000000000    0.7796170000000000 O
""",
    ),
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, POSCAR_DIR, STRAIN_DIR, AGG_DIR, PLOT_DIR, DELTA_DIR, DELTA_PLOT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def sanitize_filename(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", text.strip())


def material_tag(material: Material) -> str:
    return f"{sanitize_filename(material.formula)}_{material.material_id.replace('mp-', '')}"


def write_metadata_csv() -> Path:
    out_csv = OUT_DIR / "hardcoded_materials_summary.csv"
    fieldnames = [
        "material_id",
        "formula_pretty",
        "crystal_system",
        "space_group_symbol",
        "space_group_number",
        "nsites",
        "energy_above_hull",
        "formation_energy_per_atom",
        "is_stable",
        "volume",
        "density",
        "band_gap",
        "is_gap_direct",
        "is_metal",
        "ordering",
        "total_magnetization",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for mat in MATERIALS:
            writer.writerow(
                {
                    "material_id": mat.material_id,
                    "formula_pretty": mat.formula,
                    "crystal_system": mat.crystal_system,
                    "space_group_symbol": mat.space_group_symbol,
                    "space_group_number": mat.space_group_number,
                    "nsites": mat.nsites,
                    "energy_above_hull": mat.energy_above_hull,
                    "formation_energy_per_atom": mat.formation_energy_per_atom,
                    "is_stable": mat.is_stable,
                    "volume": mat.volume,
                    "density": mat.density,
                    "band_gap": mat.band_gap,
                    "is_gap_direct": mat.is_gap_direct,
                    "is_metal": mat.is_metal,
                    "ordering": mat.ordering,
                    "total_magnetization": mat.total_magnetization,
                }
            )
    return out_csv


def write_base_poscars() -> list[tuple[Material, Path]]:
    written = []
    for mat in MATERIALS:
        path = POSCAR_DIR / f"{material_tag(mat)}_POSCAR"
        path.write_text(mat.poscar.strip() + "\n", encoding="utf-8")
        written.append((mat, path))
    return written


def parse_vector_line(line: str) -> list[float]:
    values = []
    for part in line.split()[:3]:
        try:
            values.append(float(part))
        except ValueError:
            values.append(0.0)
    while len(values) < 3:
        values.append(0.0)
    return values


def parse_output_for_props(
    text: str,
    cation_symbol: Optional[str] = None,
    anion_symbol: Optional[str] = None,
) -> tuple[str, str, str, str, str]:
    cn_c = cn_a = c6_c = c6_a = "N/A"
    edis = "N/A"
    lines = text.splitlines()

    for line in lines:
        match = re.search(r"Dispersion\s+energy[:\s]+([-.\dEe+]+)", line, re.I)
        if match:
            edis = match.group(1)
            break

    elem_map: dict[str, tuple[str, str]] = {}
    for line in lines:
        toks = line.split()
        if len(toks) >= 5:
            symbol = toks[2]
            cn = toks[3]
            c6 = toks[4]
            if re.fullmatch(r"[A-Z][a-z]?", symbol) and symbol not in elem_map:
                elem_map[symbol] = (cn, c6)

    if cation_symbol and cation_symbol in elem_map:
        cn_c, c6_c = elem_map[cation_symbol]
    elif elem_map:
        first = next(iter(elem_map))
        cn_c, c6_c = elem_map[first]

    if anion_symbol and anion_symbol in elem_map:
        cn_a, c6_a = elem_map[anion_symbol]
    elif len(elem_map) >= 2:
        second = list(elem_map)[1]
        cn_a, c6_a = elem_map[second]
    elif elem_map:
        first = next(iter(elem_map))
        cn_a, c6_a = elem_map[first]

    return cn_c, cn_a, c6_c, c6_a, edis


def run_single_strain(
    strain_index: int,
    base_vectors: list[list[float]],
    orig_lines: list[str],
    target_dir: Path,
    results_dir: Path,
) -> tuple[int, Path, Path]:
    factor = 1.0 + (0.05 * strain_index)
    new_vectors = [[value * factor for value in vector] for vector in base_vectors]
    poscar_path = target_dir / f"POSCAR{strain_index}"
    out_path = results_dir / f"out{strain_index}.txt"

    new_lines = list(orig_lines)
    while len(new_lines) < 5:
        new_lines.append("")

    def fmt_vec(vector: list[float]) -> str:
        return "{:18.10f} {:18.10f} {:18.10f}".format(vector[0], vector[1], vector[2])

    new_lines[2] = fmt_vec(new_vectors[0])
    new_lines[3] = fmt_vec(new_vectors[1])
    new_lines[4] = fmt_vec(new_vectors[2])
    poscar_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    command = [
        S_DFTD3_CMD,
        "-i",
        "vasp",
        str(poscar_path),
        "--zero",
        "pbe",
        "--property",
        "--verbose",
    ]

    try:
        if shutil.which(S_DFTD3_CMD) is None and not Path(S_DFTD3_CMD).exists():
            out_path.write_text(f"=== RUN SKIPPED: {S_DFTD3_CMD} not found in PATH ===\n", encoding="utf-8")
        else:
            with out_path.open("w", encoding="utf-8") as handle:
                subprocess.run(
                    command,
                    stdout=handle,
                    stderr=subprocess.STDOUT,
                    timeout=DFTD3_TIMEOUT_SECONDS,
                    check=False,
                )
    except Exception as exc:
        with out_path.open("a", encoding="utf-8") as handle:
            handle.write(f"\n\n=== RUN ERROR ===\n{exc}\n")

    return strain_index, poscar_path, out_path


def process_material(mat: Material, poscar_path: Path) -> Path:
    tag = material_tag(mat)
    target_dir = STRAIN_DIR / tag
    results_dir = target_dir / "results"
    target_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    orig_lines = [line.rstrip("\n") for line in poscar_path.read_text(encoding="utf-8").splitlines()]
    base_vectors = [
        parse_vector_line(orig_lines[2]),
        parse_vector_line(orig_lines[3]),
        parse_vector_line(orig_lines[4]),
    ]
    elements = orig_lines[5].split() if len(orig_lines) >= 6 else []
    cation_symbol = elements[0] if elements else None
    anion_symbol = "O" if "O" in elements else (elements[-1] if elements else None)

    print(f"[{mat.formula}] Running {len(STRAIN_INDICES)} strains with {DFTD3_WORKERS} workers")
    results = []
    with ThreadPoolExecutor(max_workers=DFTD3_WORKERS) as executor:
        futures = [
            executor.submit(run_single_strain, index, base_vectors, orig_lines, target_dir, results_dir)
            for index in STRAIN_INDICES
        ]
        for future in as_completed(futures):
            results.append(future.result())

    rows = []
    for strain_index, strained_poscar, out_path in sorted(results, key=lambda item: item[0]):
        poscar_lines = strained_poscar.read_text(encoding="utf-8").splitlines()
        cell_length = poscar_lines[2].split()[0] if len(poscar_lines) >= 3 else "N/A"
        out_text = out_path.read_text(encoding="utf-8", errors="ignore") if out_path.exists() else ""
        cn_c, cn_a, c6_c, c6_a, edis = parse_output_for_props(out_text, cation_symbol, anion_symbol)
        rows.append(
            {
                "source": f"{tag}_POSCAR",
                "strain_index": strain_index,
                "cell_length": cell_length,
                "CN_C": cn_c,
                "CN_A": cn_a,
                "C6_C": c6_c,
                "C6_A": c6_a,
                "Edis": edis,
                "material_id": mat.material_id,
                "formula": mat.formula,
                "space_group_symbol": mat.space_group_symbol,
            }
        )

    agg_csv = AGG_DIR / f"{tag}_output.csv"
    with agg_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"[{mat.formula}] Wrote {agg_csv}")
    return agg_csv


def plot_aggregated_csv(csv_path: Path, mat: Material) -> None:
    df = pd.read_csv(csv_path)
    df["cell_length"] = pd.to_numeric(df["cell_length"], errors="coerce")
    df["Edis"] = pd.to_numeric(df["Edis"], errors="coerce")
    df = df.dropna(subset=["cell_length", "Edis"]).sort_values("cell_length")
    if df.empty:
        print(f"[{mat.formula}] No valid Edis data to plot")
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df["cell_length"], df["Edis"], marker="o", linewidth=1.3)
    ax.set_xlabel("Cell length")
    ax.set_ylabel("Dispersion energy (Edis)")
    ax.set_title(f"{mat.formula} ({mat.material_id})")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    out_png = PLOT_DIR / f"{material_tag(mat)}_cell_length_vs_Edis.png"
    fig.savefig(out_png, dpi=300)
    plt.close(fig)


def clean_curve(df: pd.DataFrame) -> pd.DataFrame:
    curve = df.copy()
    curve["cell_length"] = pd.to_numeric(curve["cell_length"], errors="coerce")
    curve["Edis"] = pd.to_numeric(curve["Edis"], errors="coerce")
    curve = curve.replace([np.inf, -np.inf], np.nan)
    curve = curve.dropna(subset=["cell_length", "Edis"])
    return curve.sort_values("cell_length").reset_index(drop=True)


def detect_dip(x: np.ndarray, y: np.ndarray) -> tuple[Optional[int], dict[str, object]]:
    debug: dict[str, object] = {}
    n = len(y)
    dy = np.gradient(y, x)

    local_maxima = [i for i in range(1, n - 1) if y[i] > y[i - 1] and y[i] > y[i + 1]]
    debug["n_local_maxima"] = len(local_maxima)

    dip_idx = None
    best_drop = 0.0
    peak_used = None
    for peak_i in local_maxima:
        search_end = min(peak_i + LOCAL_MAX_WINDOW, n)
        for j in range(peak_i + 1, search_end):
            drop = y[peak_i] - y[j]
            if drop > best_drop and drop > MIN_DIP_DROP:
                best_drop = drop
                dip_idx = j
                peak_used = peak_i

    if dip_idx is not None:
        debug.update(
            {
                "method": "local_max_drop",
                "peak_idx": int(peak_used),
                "peak_x": float(x[peak_used]),
                "peak_y": float(y[peak_used]),
                "drop_magnitude": float(best_drop),
            }
        )
        return dip_idx, debug

    threshold = float(np.mean(dy) - SLOPE_SIGMA * np.std(dy))
    candidates = np.where(dy < threshold)[0]
    debug.update({"method": "global_gradient_fallback", "threshold": threshold, "n_candidates": int(len(candidates))})
    if len(candidates) == 0:
        debug["reason"] = "no dip candidate"
        return None, debug

    dip_idx = int(candidates[np.argmin(y[candidates])])
    return dip_idx, debug


def estimate_baseline(
    x: np.ndarray,
    y: np.ndarray,
    dip_idx: int,
    peak_idx: Optional[int],
) -> tuple[Optional[float], Optional[np.ndarray], dict[str, object]]:
    debug: dict[str, object] = {}
    n = len(x)
    dy = np.gradient(y, x)

    if peak_idx is not None:
        left_idx = peak_idx
        debug["left_method"] = "peak from local_max_drop"
    else:
        left_idx = None
        for i in range(dip_idx - 1, 0, -1):
            if abs(dy[i]) < abs(dy[i - 1]):
                left_idx = i
            elif left_idx is not None:
                break
        if left_idx is None or left_idx < 1:
            fallback_offset = max(2, int(dip_idx * LEFT_FALLBACK_FRAC))
            left_idx = max(0, dip_idx - fallback_offset)
            debug["left_method"] = f"fallback offset {fallback_offset}"
        else:
            debug["left_method"] = "gradient shoulder"

    right_start = dip_idx + RIGHT_MIN_OFFSET
    right_candidates = []
    if right_start < n:
        flat_threshold = max(float(np.percentile(np.abs(dy[right_start:]), RIGHT_FLAT_PCTILE)), 1e-8)
        right_candidates = [i for i in range(right_start, n) if abs(dy[i]) <= flat_threshold]

    if not right_candidates:
        right_idx = max(right_start, n - 3)
        debug["right_method"] = "fallback last 3 pts"
    else:
        right_idx = right_candidates[-1]
        debug["right_method"] = "flattest quartile"

    window = min(3, n - right_idx)
    x_right = float(np.mean(x[right_idx : right_idx + window]))
    y_right = float(np.mean(y[right_idx : right_idx + window]))
    dx = x_right - float(x[left_idx])
    if abs(dx) < 1e-10:
        debug["reason"] = "left and right anchors at same x"
        return None, None, debug

    slope = (y_right - float(y[left_idx])) / dx
    intercept = float(y[left_idx]) - slope * float(x[left_idx])
    baseline = slope * x + intercept
    expected = slope * float(x[dip_idx]) + intercept
    debug.update(
        {
            "left_idx": int(left_idx),
            "right_idx": int(right_idx),
            "left_x": float(x[left_idx]),
            "right_x": x_right,
            "slope": float(slope),
            "intercept": float(intercept),
            "E_expected": float(expected),
        }
    )
    return expected, baseline, debug


def analyze_delta(csv_path: Path, mat: Material) -> Optional[dict[str, object]]:
    df = clean_curve(pd.read_csv(csv_path))
    if len(df) < MIN_POINTS:
        return None

    x = df["cell_length"].to_numpy(float)
    y = df["Edis"].to_numpy(float)
    dip_idx, dip_debug = detect_dip(x, y)
    if dip_idx is None:
        return None

    peak_idx = dip_debug.get("peak_idx")
    expected, baseline, base_debug = estimate_baseline(x, y, dip_idx, int(peak_idx) if peak_idx is not None else None)
    if expected is None or baseline is None:
        return None

    e_min = float(y[dip_idx])
    delta_e = e_min - float(expected)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x, y, "o-", label="s-dftd3 Edis")
    ax.plot(x, baseline, "--", label="baseline")
    ax.scatter([x[dip_idx]], [e_min], s=70, zorder=3, label="dip")
    ax.set_xlabel("Cell length")
    ax.set_ylabel("Dispersion energy (Edis)")
    ax.set_title(f"{mat.formula}: delta_E = {delta_e:.6f}")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(DELTA_PLOT_DIR / f"{material_tag(mat)}_delta.png", dpi=300)
    plt.close(fig)

    return {
        "material": mat.formula,
        "material_id": mat.material_id,
        "space_group_symbol": mat.space_group_symbol,
        "source": f"{material_tag(mat)}_POSCAR",
        "n_points": len(df),
        "method": dip_debug.get("method"),
        "dip_cell_length": float(x[dip_idx]),
        "E_min": e_min,
        "E_expected_dip": float(expected),
        "delta_E": delta_e,
        "baseline_slope": base_debug.get("slope"),
    }


def write_delta_summary(rows: list[dict[str, object]]) -> Path:
    out_csv = DELTA_DIR / "delta_summary.csv"
    if not rows:
        out_csv.write_text("material,material_id,status\n", encoding="utf-8")
        return out_csv
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return out_csv


def main() -> None:
    ensure_dirs()
    print("TEB hardcoded 8-material D3 strain runner")
    print(f"Output directory: {OUT_DIR}")
    print(f"s-dftd3 command: {S_DFTD3_CMD}")
    print(f"Strain indices: {STRAIN_START}..{STRAIN_STOP}")
    print(f"Workers per material: {DFTD3_WORKERS}")

    if shutil.which(S_DFTD3_CMD) is None and not Path(S_DFTD3_CMD).exists():
        print(f"WARNING: {S_DFTD3_CMD} was not found. Output files will record skipped runs.")

    metadata_csv = write_metadata_csv()
    poscars = write_base_poscars()
    print(f"Wrote metadata: {metadata_csv}")
    print(f"Wrote {len(poscars)} embedded POSCAR files")

    delta_rows = []
    for mat, poscar_path in poscars:
        agg_csv = process_material(mat, poscar_path)
        plot_aggregated_csv(agg_csv, mat)
        delta_row = analyze_delta(agg_csv, mat)
        if delta_row:
            delta_rows.append(delta_row)
            print(f"[{mat.formula}] delta_E = {delta_row['delta_E']:.8f}")
        else:
            print(f"[{mat.formula}] No delta result calculated")

    delta_csv = write_delta_summary(delta_rows)
    print("\nDone.")
    print(f"Aggregated CSVs: {AGG_DIR}")
    print(f"Plots: {PLOT_DIR}")
    print(f"Delta summary: {delta_csv}")


if __name__ == "__main__":
    main()
