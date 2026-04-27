#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

from _security_calibrated_common import (
    calibrated_effective_sample_count,
    chi_from_visibility,
    default_input_dirs,
    delta_fk_calibrated,
    ensure_output_dir,
    format_float,
    load_candidate_frame,
    safe_div,
    write_summary,
)


ACTUAL_IR_MODEL_TAG = "strict_zhong_like_calibrated_actual_ir"


def _build_shadow(frame: pd.DataFrame, *, franson_visibility: float, eps_sec: float, eps_cor: float) -> pd.DataFrame:
    df = frame.copy()
    df["franson_visibility_global"] = float(franson_visibility)
    df["eps_sec"] = float(eps_sec)
    df["eps_cor"] = float(eps_cor)

    leak_vals: list[float] = []
    leak_tags: list[str] = []
    delta_vals: list[float] = []
    n_eff_vals: list[float] = []
    layer_fraction_vals: list[float] = []
    clean_fraction_vals: list[float] = []
    delta_driver_tags: list[str] = []
    chi_vals: list[float] = []
    pie_vals: list[float] = []
    skr_vals: list[float] = []
    beta_eff_vals: list[float] = []

    for _, row in df.iterrows():
        iab = row.get("IAB_est")
        best_hard = row.get("best_hard_PIE")
        leak = np.nan
        leak_tag = "surrogate_from_best_hard_pie_gap"
        if pd.notna(iab) and pd.notna(best_hard):
            leak = max(float(iab) - float(best_hard), 0.0)
        n_eff, fk_meta = calibrated_effective_sample_count(row)
        delta_fk = delta_fk_calibrated(n_eff_pairs=n_eff, eps_sec=float(eps_sec), eps_cor=float(eps_cor))
        chi_e = chi_from_visibility(dimension=int(row["dimension"]), franson_visibility=float(franson_visibility))
        pie = np.nan
        if pd.notna(iab) and math.isfinite(float(iab)) and math.isfinite(float(leak)) and delta_fk is not None:
            pie = max(0.0, float(iab) - float(leak) - float(chi_e) - float(delta_fk))
        accepted_rate = row.get("accepted_rate_proxy")
        skr = float(pie) * float(accepted_rate) if pd.notna(accepted_rate) and pd.notna(pie) and math.isfinite(float(accepted_rate)) else np.nan
        beta_eff = np.nan
        if pd.notna(iab) and float(iab) > 0.0 and math.isfinite(float(iab)) and math.isfinite(float(leak)):
            beta_eff = max(0.0, float(iab) - float(leak)) / float(iab)

        leak_vals.append(leak)
        leak_tags.append(leak_tag)
        delta_vals.append(delta_fk if delta_fk is not None else np.nan)
        n_eff_vals.append(fk_meta.get("n_eff_pairs", np.nan))
        layer_fraction_vals.append(fk_meta.get("layer_fraction_used", np.nan))
        clean_fraction_vals.append(fk_meta.get("clean_fraction_used", np.nan))
        delta_driver_tags.append(str(fk_meta.get("delta_fk_driver_tag", "unknown")))
        chi_vals.append(chi_e)
        pie_vals.append(pie)
        skr_vals.append(skr)
        beta_eff_vals.append(beta_eff)

    df["leak_EC_actual_bits"] = leak_vals
    df["leak_EC_source_tag"] = leak_tags
    df["DeltaFK_calibrated"] = delta_vals
    df["n_eff_pairs_for_fk"] = n_eff_vals
    df["delta_fk_layer_fraction_used"] = layer_fraction_vals
    df["delta_fk_clean_fraction_used"] = clean_fraction_vals
    df["delta_fk_driver_tag"] = delta_driver_tags
    df["chi_E_calibrated"] = chi_vals
    df["PIE_secure_actual_ir"] = pie_vals
    df["SKR_secure_actual_ir_bps"] = skr_vals
    df["beta_eff"] = beta_eff_vals
    df["actual_ir_model_tag"] = ACTUAL_IR_MODEL_TAG
    return df



def _summary_lines(df: pd.DataFrame, *, input_dirs: list[Path], franson_visibility: float, eps_sec: float, eps_cor: float) -> list[str]:
    leak_actual_mask = df["leak_EC_source_tag"].eq("actual_total_leak_ec_bits")
    surrogate_mask = ~leak_actual_mask
    perf_positive = pd.to_numeric(df["PIE_practical"], errors="coerce") > 0
    pie_drop = pd.to_numeric(df["PIE_practical"], errors="coerce") - pd.to_numeric(df["PIE_secure_actual_ir"], errors="coerce")
    skr_drop = pd.to_numeric(df["SKR_measured_bps"], errors="coerce") - pd.to_numeric(df["SKR_secure_actual_ir_bps"], errors="coerce")
    large_mask = (pd.to_numeric(df["bin_width_ps"], errors="coerce") >= 120) | (pd.to_numeric(df["dimension"], errors="coerce") >= 1024)

    perf_by_loss = []
    for loss_db, sl in df.groupby("loss_db"):
        cur_best = sl.loc[pd.to_numeric(sl["SKR_measured_bps"], errors="coerce").idxmax()]
        new_best = sl.loc[pd.to_numeric(sl["SKR_secure_actual_ir_bps"], errors="coerce").idxmax()]
        perf_by_loss.append(
            f"- loss={int(loss_db)} current_best=(d={int(cur_best['dimension'])},bw={int(cur_best['bin_width_ps'])}) actual_ir_best=(d={int(new_best['dimension'])},bw={int(new_best['bin_width_ps'])})"
        )

    lines = [
        "input_dirs:",
        *[f"  - {p}" for p in input_dirs],
        f"point_count: {len(df)}",
        f"franson_visibility_global: {franson_visibility}",
        f"eps_sec: {eps_sec}",
        f"eps_cor: {eps_cor}",
        "finite_key_model_tag: zhong_like_finite_key_calibrated",
        "finite_key_note: calibrated penalty based on effective retained sample mass; not full niu_2016 composable proof.",
        "",
        f"actual_leak_rows: {int(leak_actual_mask.sum())}",
        f"surrogate_leak_rows: {int(surrogate_mask.sum())}",
        f"DeltaFK_calibrated_range: {format_float(df['DeltaFK_calibrated'].min())} .. {format_float(df['DeltaFK_calibrated'].max())}",
        f"DeltaFK_primary_inputs: n_pairs_actual, layers_success_best/log2(d), clean_pair_fraction or frame_diag fallback",
        f"relative_to_performance_proxy_mean_PIE_drop_frac: {format_float(safe_div(float(pie_drop[perf_positive].mean()), float(pd.to_numeric(df.loc[perf_positive, 'PIE_practical'], errors='coerce').mean()))) if perf_positive.any() else 'nan'}",
        f"relative_to_performance_proxy_mean_SKR_drop_frac: {format_float(safe_div(float(skr_drop[perf_positive].mean()), float(pd.to_numeric(df.loc[perf_positive, 'SKR_measured_bps'], errors='coerce').mean()))) if perf_positive.any() else 'nan'}",
        f"large_bw_or_large_d_mean_PIE_drop: {format_float(pd.to_numeric(pie_drop[large_mask], errors='coerce').mean())}",
        f"large_bw_or_large_d_mean_SKR_drop: {format_float(pd.to_numeric(skr_drop[large_mask], errors='coerce').mean())}",
        f"beta_eff_typical_range_p10_p90: {format_float(df['beta_eff'].quantile(0.10))} .. {format_float(df['beta_eff'].quantile(0.90))}",
        "optimum_shift_by_loss:",
        *perf_by_loss,
    ]
    return lines



def main() -> int:
    ap = argparse.ArgumentParser(description="Build actual-IR finite-key calibrated security shadow.")
    ap.add_argument("--input-dirs", nargs="*", default=[])
    ap.add_argument("--franson-visibility", type=float, default=0.95)
    ap.add_argument("--eps-sec", type=float, default=1e-10)
    ap.add_argument("--eps-cor", type=float, default=1e-10)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir, overwrite=bool(args.overwrite))
    input_dirs = [Path(p) for p in args.input_dirs] if args.input_dirs else default_input_dirs()

    frame = pd.concat([load_candidate_frame(p) for p in input_dirs], ignore_index=True)
    shadow = _build_shadow(frame, franson_visibility=float(args.franson_visibility), eps_sec=float(args.eps_sec), eps_cor=float(args.eps_cor))
    keep_cols = [
        "loss_db", "dimension", "bin_width_ps", "processing_rule_version", "pairing_path_tag", "pairing_window_source_tag",
        "threshold_ps", "effective_pairing_window_ps", "threshold_ratio_to_bw", "raw_ser", "map_ser", "coincidence_rate_hz",
        "accepted_rate_proxy", "layers_success_best", "best_hard_PIE", "chi_E", "IAB_est", "IAB_source_tag",
        "franson_visibility_global", "leak_EC_actual_bits", "leak_EC_source_tag", "DeltaFK_calibrated", "eps_sec", "eps_cor",
        "PIE_practical", "SKR_measured_bps", "PIE_secure_actual_ir", "SKR_secure_actual_ir_bps", "beta_eff", "actual_ir_model_tag",
        "n_pairs_actual", "frame_diag_available", "clean_pair_fraction", "n_eff_pairs_for_fk", "delta_fk_driver_tag",
    ]
    shadow[keep_cols].to_csv(output_dir / "actual_ir_finite_key_point_table.csv", index=False)
    write_summary(
        output_dir / "actual_ir_finite_key_summary.txt",
        _summary_lines(
            shadow,
            input_dirs=input_dirs,
            franson_visibility=float(args.franson_visibility),
            eps_sec=float(args.eps_sec),
            eps_cor=float(args.eps_cor),
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
