#!/usr/bin/env python3
"""
Fetch Materials Project rows for a fixed list of formulas and save one CSV per
formula using the exact reduced-formula match with the minimum energy above hull.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from mp_api.client import MPRester
from pymatgen.core import Composition


HARDCODED_MP_API_KEY = "JNETXdNFU6A03rQsthLfx5gxwU2viDG0"
ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "selected_formula_csvs"

TARGET_FORMULAS = [
    "NiO",
    "CoO",
    "FeO",
    "TiO2",
    "RuO2",
    "IrO2",
    "SrTiO3",
    "LaMnO3",
]

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


def sanitize_name(text: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in text)


def formula_to_chemsys_and_reduced(formula_text: str) -> tuple[str, str]:
    comp = Composition(formula_text)
    reduced = comp.reduced_formula
    elements = sorted(el.symbol for el in comp.elements)
    chemsys = "-".join(elements)
    return chemsys, reduced


def docs_to_frame(docs: list[object]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for doc in docs:
        formula_pretty = getattr(doc, "formula_pretty", None)
        try:
            reduced = Composition(formula_pretty).reduced_formula if formula_pretty else None
        except Exception:
            reduced = None

        rows.append(
            {
                "material_id": getattr(doc, "material_id", None),
                "formula_pretty": formula_pretty,
                "formula_reduced": reduced,
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
    return pd.DataFrame(rows)


def best_exact_match_for_formula(mpr: MPRester, formula_text: str) -> pd.DataFrame:
    chemsys, reduced_formula = formula_to_chemsys_and_reduced(formula_text)
    docs = list(mpr.materials.summary.search(chemsys=chemsys, fields=FIELDS, all_fields=False))
    if not docs:
        raise ValueError(f"No Materials Project rows found for chemsys {chemsys}")

    df = docs_to_frame(docs)
    exact = df[df["formula_reduced"] == reduced_formula].copy()
    if exact.empty:
        raise ValueError(f"No exact reduced-formula match found for {reduced_formula} in {chemsys}")

    exact = exact.sort_values(
        ["energy_above_hull", "formation_energy_per_atom", "material_id"],
        ascending=[True, True, True],
        na_position="last",
    ).reset_index(drop=True)
    return exact.head(1)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    saved_rows: list[pd.DataFrame] = []

    with MPRester(HARDCODED_MP_API_KEY) as mpr:
        for formula in TARGET_FORMULAS:
            best = best_exact_match_for_formula(mpr, formula)
            normalized = Composition(formula).reduced_formula
            out_csv = OUT_DIR / f"{sanitize_name(normalized)}_best_match.csv"
            best.to_csv(out_csv, index=False)
            saved_rows.append(best.assign(requested_formula=normalized))
            print(f"Saved {normalized}: {out_csv}")

    combined = pd.concat(saved_rows, ignore_index=True)
    combined.to_csv(OUT_DIR / "selected_formulas_summary.csv", index=False)
    print(f"Saved combined summary: {OUT_DIR / 'selected_formulas_summary.csv'}")


if __name__ == "__main__":
    main()
