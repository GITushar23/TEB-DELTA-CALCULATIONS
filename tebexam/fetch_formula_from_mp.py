#!/usr/bin/env python3
"""
Fetch Materials Project summary data for the binary chemsys implied by a target
formula, then extract only the rows that match that exact reduced formula.

Example:
    python fetch_formula_from_mp.py IrO2

Outputs for IrO2:
    - Ir-O_all_materials.csv
    - IrO2_exact_matches.csv
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import pandas as pd
    from mp_api.client import MPRester
    from pymatgen.core import Composition
except Exception as exc:
    print(f"Missing dependency: {exc}")
    print("Install with: pip install mp-api pymatgen pandas")
    sys.exit(1)


ROOT = Path(__file__).resolve().parent
MP_KEY_ENV = "MP_API_KEY"
MP_KEY_FILE_ENV = "MP_API_KEY_FILE"
HARDCODED_MP_API_KEY = "JNETXdNFU6A03rQsthLfx5gxwU2viDG0"

FIELDS = [
    "material_id",
    "formula_pretty",
    "symmetry.crystal_system",
    "symmetry.symbol",
    "symmetry.number",
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a binary Materials Project chemsys and keep only one target formula.",
    )
    parser.add_argument(
        "formula",
        help="Target formula, for example IrO2 or TiS2",
    )
    return parser.parse_args()


def get_api_key() -> str | None:
    if HARDCODED_MP_API_KEY.strip():
        return HARDCODED_MP_API_KEY.strip()

    direct = os.environ.get(MP_KEY_ENV, "").strip()
    if direct:
        return direct

    key_file_raw = os.environ.get(MP_KEY_FILE_ENV, "").strip()
    key_file = Path(key_file_raw) if key_file_raw else Path.home() / ".mp_api_key"
    if key_file.exists():
        value = key_file.read_text(encoding="utf-8").strip()
        if value:
            return value
    return None


def sanitize_name(text: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in text)


def derive_binary_chemsys_and_formula(formula_text: str) -> tuple[str, str]:
    composition = Composition(formula_text)
    reduced_formula = composition.reduced_formula
    elements = sorted([el.symbol for el in composition.elements])

    if len(elements) != 2:
        raise ValueError(
            f"{formula_text!r} is not binary. This script expects exactly 2 elements."
        )

    chemsys = "-".join(elements)
    return chemsys, reduced_formula


def build_rows(docs: list[object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for doc in docs:
        formula_pretty = getattr(doc, "formula_pretty", None)
        reduced_formula = None
        if formula_pretty:
            try:
                reduced_formula = Composition(formula_pretty).reduced_formula
            except Exception:
                reduced_formula = None

        rows.append(
            {
                "material_id": getattr(doc, "material_id", None),
                "formula_pretty": formula_pretty,
                "formula_reduced": reduced_formula,
                "crystal_system": getattr(getattr(doc, "symmetry", None), "crystal_system", None),
                "space_group_symbol": getattr(getattr(doc, "symmetry", None), "symbol", None),
                "space_group_number": getattr(getattr(doc, "symmetry", None), "number", None),
                "nsites": getattr(doc, "nsites", None),
                "energy_above_hull": getattr(doc, "energy_above_hull", None),
                "formation_energy_per_atom": getattr(doc, "formation_energy_per_atom", None),
                "is_stable": getattr(doc, "is_stable", None),
                "volume": getattr(doc, "volume", None),
                "density": getattr(doc, "density", None),
                "band_gap": getattr(doc, "band_gap", None),
                "is_gap_direct": getattr(doc, "is_gap_direct", None),
                "is_metal": getattr(doc, "is_metal", None),
                "ordering": getattr(doc, "ordering", None),
                "total_magnetization": getattr(doc, "total_magnetization", None),
            }
        )
    return rows


def main() -> None:
    args = parse_args()
    api_key = get_api_key()
    if not api_key:
        raise SystemExit(
            "No Materials Project API key found. Set MP_API_KEY or create ~/.mp_api_key"
        )

    chemsys, target_formula = derive_binary_chemsys_and_formula(args.formula)

    print(f"Target formula: {target_formula}")
    print(f"Fetching chemsys: {chemsys}")

    with MPRester(api_key) as mpr:
        docs = list(
            mpr.materials.summary.search(
                chemsys=chemsys,
                fields=FIELDS,
                all_fields=False,
            )
        )

    if not docs:
        raise SystemExit(f"No Materials Project entries found for chemsys {chemsys}")

    df = pd.DataFrame(build_rows(docs))
    df = df.sort_values(["formula_pretty", "energy_above_hull", "material_id"]).reset_index(drop=True)

    matches = df[df["formula_reduced"] == target_formula].copy()
    matches = matches.sort_values(["energy_above_hull", "material_id"]).reset_index(drop=True)

    all_csv = ROOT / f"{sanitize_name(chemsys)}_all_materials.csv"
    exact_csv = ROOT / f"{sanitize_name(target_formula)}_exact_matches.csv"

    df.to_csv(all_csv, index=False)
    matches.to_csv(exact_csv, index=False)

    print(f"Wrote full chemsys CSV: {all_csv}")
    print(f"Wrote exact-match CSV: {exact_csv}")
    print(f"Total chemsys rows: {len(df)}")
    print(f"Exact {target_formula} rows: {len(matches)}")


if __name__ == "__main__":
    main()
