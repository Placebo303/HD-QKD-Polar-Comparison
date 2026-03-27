#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _longrun_common import (
    REPRESENTATIVE_BWS,
    REPRESENTATIVE_DIMS,
    candidate_dir_for_loss,
    dims_arg,
    bws_arg,
    write_text,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare fresh smoke rerun subset against existing candidate outputs.")
    ap.add_argument("--fresh-dir", required=True)
    ap.add_argument("--baseline-dir", default="")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    fresh_dir = Path(args.fresh_dir)
    baseline_dir = Path(args.baseline_dir) if str(args.baseline_dir).strip() else candidate_dir_for_loss(20)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fresh = pd.read_csv(fresh_dir / "polar_e2e_results.csv")
    base = pd.read_csv(baseline_dir / "polar_e2e_results.csv")
    dims = set(REPRESENTATIVE_DIMS)
    bws = set(REPRESENTATIVE_BWS)
    fresh = fresh[
        pd.to_numeric(fresh["dimension"], errors="coerce").isin(dims)
        & pd.to_numeric(fresh["bin_width_ps"], errors="coerce").isin(bws)
    ].copy()
    base = base[
        pd.to_numeric(base["dimension"], errors="coerce").isin(dims)
        & pd.to_numeric(base["bin_width_ps"], errors="coerce").isin(bws)
    ].copy()
    keep = ["dimension", "bin_width_ps", "map_ser", "PIE_practical", "SKR_measured_bps", "layers_success_best"]
    merged = base[keep].merge(fresh[keep], on=["dimension", "bin_width_ps"], how="outer", suffixes=("_baseline", "_fresh"))
    merged["delta_map_ser"] = pd.to_numeric(merged["map_ser_fresh"], errors="coerce") - pd.to_numeric(merged["map_ser_baseline"], errors="coerce")
    merged["delta_PIE_practical"] = pd.to_numeric(merged["PIE_practical_fresh"], errors="coerce") - pd.to_numeric(merged["PIE_practical_baseline"], errors="coerce")
    merged["delta_SKR_measured_bps"] = pd.to_numeric(merged["SKR_measured_bps_fresh"], errors="coerce") - pd.to_numeric(merged["SKR_measured_bps_baseline"], errors="coerce")
    merged["delta_layers_success_best"] = pd.to_numeric(merged["layers_success_best_fresh"], errors="coerce") - pd.to_numeric(merged["layers_success_best_baseline"], errors="coerce")
    merged = merged.sort_values(["dimension", "bin_width_ps"]).reset_index(drop=True)
    merged.to_csv(output_dir / "smoke_compare_vs_candidate.csv", index=False)
    max_abs_map = pd.to_numeric(merged["delta_map_ser"], errors="coerce").abs().max()
    max_abs_pie = pd.to_numeric(merged["delta_PIE_practical"], errors="coerce").abs().max()
    max_abs_skr = pd.to_numeric(merged["delta_SKR_measured_bps"], errors="coerce").abs().max()
    nonzero_layers = int((pd.to_numeric(merged["delta_layers_success_best"], errors="coerce").fillna(0) != 0).sum())
    lines = [
        f"fresh_dir: {fresh_dir}",
        f"baseline_dir: {baseline_dir}",
        f"dimensions: {dims_arg(REPRESENTATIVE_DIMS)}",
        f"bin_widths: {bws_arg(REPRESENTATIVE_BWS)}",
        f"point_count: {len(merged)}",
        f"max_abs_delta_map_ser: {max_abs_map}",
        f"max_abs_delta_PIE_practical: {max_abs_pie}",
        f"max_abs_delta_SKR_measured_bps: {max_abs_skr}",
        f"nonzero_delta_layers_success_best: {nonzero_layers}",
        "interpretation: exact or near-exact agreement means the new cache-boundary wrapper preserves current logic.",
    ]
    write_text(output_dir / "smoke_compare_summary.txt", "\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
