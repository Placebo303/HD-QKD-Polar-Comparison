#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _security_calibrated_common import default_input_dirs, ensure_output_dir, format_float, load_candidate_frame, write_summary



def _load_shadow(path: Path, filename: str) -> pd.DataFrame:
    csv_path = path / filename
    if not csv_path.exists():
        raise SystemExit(f"input file not found: {csv_path}")
    return pd.read_csv(csv_path)



def main() -> int:
    ap = argparse.ArgumentParser(description="Build calibrated security summary across actual-IR, beta baseline, and performance proxy.")
    ap.add_argument("--actual-ir-dir", required=True)
    ap.add_argument("--beta-baseline-dir", required=True)
    ap.add_argument("--performance-proxy-input-dirs", nargs="*", default=[])
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir, overwrite=bool(args.overwrite))

    perf_dirs = [Path(p) for p in args.performance_proxy_input_dirs] if args.performance_proxy_input_dirs else default_input_dirs()
    perf = pd.concat([load_candidate_frame(p) for p in perf_dirs], ignore_index=True)
    perf = perf[[
        "loss_db", "dimension", "bin_width_ps", "PIE_practical", "SKR_measured_bps", "processing_rule_version", "pairing_path_tag",
        "effective_pairing_window_ps", "pairing_window_source_tag", "best_hard_PIE", "IAB_est", "raw_ser", "map_ser",
        "coincidence_rate_hz", "layers_success_best",
    ]].copy()

    actual = _load_shadow(Path(args.actual_ir_dir), "actual_ir_finite_key_point_table.csv")
    beta = _load_shadow(Path(args.beta_baseline_dir), "beta_baseline_finite_key_point_table.csv")
    key_cols = ["loss_db", "dimension", "bin_width_ps"]
    merged = perf.merge(
        actual[[*key_cols, "PIE_secure_actual_ir", "SKR_secure_actual_ir_bps", "beta_eff", "franson_visibility_global", "leak_EC_source_tag", "DeltaFK_calibrated"]],
        on=key_cols,
        how="left",
    ).merge(
        beta[[*key_cols, "PIE_secure_beta_baseline", "SKR_secure_beta_baseline_bps"]],
        on=key_cols,
        how="left",
    )
    merged.to_csv(output_dir / "security_calibrated_master_table.csv", index=False)

    pie_actual = pd.to_numeric(merged["PIE_secure_actual_ir"], errors="coerce")
    pie_perf = pd.to_numeric(merged["PIE_practical"], errors="coerce")
    skr_actual = pd.to_numeric(merged["SKR_secure_actual_ir_bps"], errors="coerce")
    skr_perf = pd.to_numeric(merged["SKR_measured_bps"], errors="coerce")
    pie_beta = pd.to_numeric(merged["PIE_secure_beta_baseline"], errors="coerce")
    beta_gap = (pie_beta - pie_actual).abs()
    loss_abs_skr = merged.assign(abs_delta=(skr_perf - skr_actual).abs()).groupby("loss_db")["abs_delta"].mean().sort_values(ascending=False)
    sensitive_security = merged.loc[beta_gap.sort_values(ascending=False).head(20).index, ["loss_db", "dimension", "bin_width_ps"]]
    sensitive_ir = merged.assign(drop=(pie_perf - pie_actual)).sort_values("drop", ascending=False).head(20)[["loss_db", "dimension", "bin_width_ps"]]

    bw_preserved = int(((pie_actual > 0) & (pie_perf > 0)).sum())
    reversed_count = int(((pie_actual <= 0) & (pie_perf > 0)).sum())
    trend_tag = "preserved" if reversed_count == 0 else ("flattened" if reversed_count < max(1, len(merged) // 5) else "reversed")

    lines = [
        "input_actual_ir_dir:",
        f"- {Path(args.actual_ir_dir)}",
        "input_beta_baseline_dir:",
        f"- {Path(args.beta_baseline_dir)}",
        "input_performance_proxy_dirs:",
        *[f"- {p}" for p in perf_dirs],
        f"point_count: {len(merged)}",
        "",
        "1. current paper/report primary result should be: actual-IR finite-key calibrated.",
        "2. actual-IR should be primary because it deducts the real Polar coordination surrogate leak, while literature beta cannot represent pointwise IR quality variation.",
        f"3. finite-key calibration overall effect: {trend_tag}.",
        f"4. high-dimensional anti-loss trend under actual-IR: {'still visible' if merged.groupby('loss_db')['SKR_secure_actual_ir_bps'].max().notna().all() else 'partially blocked'}.",
        "5. regions most sensitive to security assumption: top abs(beta-baseline - actual-IR) rows cluster in the high-gap subset listed below.",
        "6. regions most sensitive to actual IR efficiency: top performance-to-actual drop rows cluster in the high-drop subset listed below.",
        "",
        f"mean_PIE_actual_minus_performance: {format_float((pie_actual - pie_perf).mean())}",
        f"mean_SKR_actual_minus_performance: {format_float((skr_actual - skr_perf).mean())}",
        f"mean_PIE_beta_minus_actual: {format_float((pie_beta - pie_actual).mean())}",
        f"loss_with_largest_mean_abs_delta_SKR: {int(loss_abs_skr.index[0]) if len(loss_abs_skr) else 'nan'}",
        "high_security_assumption_sensitivity_examples:",
    ]
    for _, row in sensitive_security.iterrows():
        lines.append(f"- loss={int(row['loss_db'])} d={int(row['dimension'])} bw={int(row['bin_width_ps'])}")
    lines.append("high_actual_ir_sensitivity_examples:")
    for _, row in sensitive_ir.iterrows():
        lines.append(f"- loss={int(row['loss_db'])} d={int(row['dimension'])} bw={int(row['bin_width_ps'])}")
    lines.extend([
        "",
        "PRIMARY_REPORTING_MODE = actual_ir_finite_key",
        "BETA_BASELINE_ROLE = comparison_only",
        "NIU_2016_STATUS = not_supported_by_current_observables",
    ])
    write_summary(output_dir / "security_calibrated_summary.txt", lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
