#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from _security_calibrated_common import (
    chi_from_visibility,
    default_input_dirs,
    ensure_output_dir,
    format_float,
    load_candidate_frame,
    safe_div,
    write_summary,
)
from build_actual_ir_finite_key_shadow import _build_shadow as build_actual_ir_shadow


BETA_BASELINE_MODEL_TAG = "literature_beta_finite_key_baseline"



def _build_beta_baseline(frame: pd.DataFrame, *, franson_visibility: float, beta_baseline: float, eps_sec: float, eps_cor: float) -> pd.DataFrame:
    actual = build_actual_ir_shadow(frame, franson_visibility=franson_visibility, eps_sec=eps_sec, eps_cor=eps_cor)
    beta_vals: list[float] = []
    skr_vals: list[float] = []
    for _, row in actual.iterrows():
        iab = row.get("IAB_est")
        delta_fk = row.get("DeltaFK_calibrated")
        chi_e = chi_from_visibility(dimension=int(row["dimension"]), franson_visibility=float(franson_visibility))
        pie = np.nan
        if pd.notna(iab) and pd.notna(delta_fk):
            pie = max(0.0, float(beta_baseline) * float(iab) - float(chi_e) - float(delta_fk))
        rate = row.get("accepted_rate_proxy")
        skr = float(pie) * float(rate) if pd.notna(rate) and pd.notna(pie) else np.nan
        beta_vals.append(pie)
        skr_vals.append(skr)
    actual["beta_baseline"] = float(beta_baseline)
    actual["PIE_secure_beta_baseline"] = beta_vals
    actual["SKR_secure_beta_baseline_bps"] = skr_vals
    actual["beta_baseline_model_tag"] = BETA_BASELINE_MODEL_TAG
    return actual



def _summary_lines(df: pd.DataFrame, *, input_dirs: list[Path], beta_baseline: float, franson_visibility: float) -> list[str]:
    pie_delta = pd.to_numeric(df["PIE_secure_beta_baseline"], errors="coerce") - pd.to_numeric(df["PIE_secure_actual_ir"], errors="coerce")
    skr_delta = pd.to_numeric(df["SKR_secure_beta_baseline_bps"], errors="coerce") - pd.to_numeric(df["SKR_secure_actual_ir_bps"], errors="coerce")
    optimistic = int((pie_delta > 1e-9).sum())
    conservative = int((pie_delta < -1e-9).sum())
    abs_gap = skr_delta.abs()
    top = df.loc[abs_gap.sort_values(ascending=False).head(10).index, ["loss_db", "dimension", "bin_width_ps", "beta_eff", "PIE_secure_actual_ir", "PIE_secure_beta_baseline"]]
    beta_gap_mask = (pd.to_numeric(df["beta_eff"], errors="coerce") - float(beta_baseline)).abs() > 0.05
    lines = [
        "input_dirs:",
        *[f"  - {p}" for p in input_dirs],
        f"point_count: {len(df)}",
        f"franson_visibility_global: {franson_visibility}",
        f"beta_baseline: {beta_baseline}",
        f"beta_vs_actual_more_optimistic_rows: {optimistic}",
        f"beta_vs_actual_more_conservative_rows: {conservative}",
        f"mean_delta_PIE_beta_minus_actual: {format_float(pie_delta.mean())}",
        f"mean_delta_SKR_beta_minus_actual: {format_float(skr_delta.mean())}",
        f"material_beta_gap_rows_abs_gt_0.05: {int(beta_gap_mask.sum())}/{len(df)}",
        "comparison_verdict:",
        f"- beta baseline is {'more optimistic' if optimistic >= conservative else 'more conservative'} than actual-IR on average.",
        "- fixed beta masks actual Polar coordination variation when beta_eff departs materially from beta_baseline.",
        "- literature beta should remain comparison-only, not the primary reporting mode.",
        "largest_gap_examples:",
    ]
    for _, row in top.iterrows():
        lines.append(
            f"- loss={int(row['loss_db'])} d={int(row['dimension'])} bw={int(row['bin_width_ps'])} beta_eff={format_float(row['beta_eff'])} PIE_actual={format_float(row['PIE_secure_actual_ir'])} PIE_beta={format_float(row['PIE_secure_beta_baseline'])}"
        )
    return lines



def main() -> int:
    ap = argparse.ArgumentParser(description="Build literature-beta finite-key baseline shadow.")
    ap.add_argument("--input-dirs", nargs="*", default=[])
    ap.add_argument("--franson-visibility", type=float, default=0.95)
    ap.add_argument("--beta-baseline", type=float, default=0.90)
    ap.add_argument("--eps-sec", type=float, default=1e-10)
    ap.add_argument("--eps-cor", type=float, default=1e-10)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir, overwrite=bool(args.overwrite))
    input_dirs = [Path(p) for p in args.input_dirs] if args.input_dirs else default_input_dirs()

    frame = pd.concat([load_candidate_frame(p) for p in input_dirs], ignore_index=True)
    shadow = _build_beta_baseline(
        frame,
        franson_visibility=float(args.franson_visibility),
        beta_baseline=float(args.beta_baseline),
        eps_sec=float(args.eps_sec),
        eps_cor=float(args.eps_cor),
    )
    keep_cols = [
        "loss_db", "dimension", "bin_width_ps", "processing_rule_version", "pairing_path_tag", "pairing_window_source_tag",
        "threshold_ps", "effective_pairing_window_ps", "raw_ser", "map_ser", "coincidence_rate_hz", "accepted_rate_proxy",
        "best_hard_PIE", "IAB_est", "beta_eff", "DeltaFK_calibrated", "PIE_secure_actual_ir", "SKR_secure_actual_ir_bps",
        "beta_baseline", "PIE_secure_beta_baseline", "SKR_secure_beta_baseline_bps", "beta_baseline_model_tag",
    ]
    shadow[keep_cols].to_csv(output_dir / "beta_baseline_finite_key_point_table.csv", index=False)
    write_summary(
        output_dir / "beta_baseline_finite_key_summary.txt",
        _summary_lines(
            shadow,
            input_dirs=input_dirs,
            beta_baseline=float(args.beta_baseline),
            franson_visibility=float(args.franson_visibility),
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
