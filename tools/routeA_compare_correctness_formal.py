#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


KEY_COLS = ["loss_db", "dimension", "bin_width_ps"]


def pick(frame: pd.DataFrame, preferred: str, fallback: str | None = None) -> pd.Series:
    if preferred in frame.columns:
        return pd.to_numeric(frame[preferred], errors="coerce")
    if fallback is not None and fallback in frame.columns:
        return pd.to_numeric(frame[fallback], errors="coerce")
    return pd.Series([float("nan")] * len(frame), index=frame.index)


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare legacy vs formal Route A correctness outputs.")
    ap.add_argument("--old-master", required=True)
    ap.add_argument("--new-master", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    old_df = pd.read_csv(Path(args.old_master))
    new_df = pd.read_csv(Path(args.new_master))
    merged = old_df.merge(new_df, on=KEY_COLS, how="inner", suffixes=("_old", "_new"))

    compare = merged[KEY_COLS].copy()
    compare["leak_EC_actual_bits_old"] = pick(merged, "leak_EC_actual_bits_old")
    compare["leak_EC_actual_bits_new"] = pick(merged, "leak_EC_actual_bits_new", "leak_EC_actual_bits")
    compare["lambda_ver_bits_actual_new"] = pick(merged, "lambda_ver_bits_actual_new", "lambda_ver_bits_actual")
    compare["decoder_fail_rate_oracle_new"] = pick(merged, "decoder_fail_rate_oracle_new", "decoder_fail_rate_oracle")
    compare["epsilon_EC_empirical_new"] = pick(merged, "epsilon_EC_empirical_new", "epsilon_EC_empirical")
    compare["epsilon_EC_bound_new"] = pick(merged, "epsilon_EC_bound_new", "epsilon_EC_bound")
    compare["PIE_secure_actual_ir_old"] = pick(merged, "PIE_secure_actual_ir_old")
    compare["PIE_secure_actual_ir_new"] = pick(merged, "PIE_secure_actual_ir_new", "PIE_secure_actual_ir")
    compare["SKR_secure_actual_ir_bps_old"] = pick(merged, "SKR_secure_actual_ir_bps_old")
    compare["SKR_secure_actual_ir_bps_new"] = pick(merged, "SKR_secure_actual_ir_bps_new", "SKR_secure_actual_ir_bps")
    compare["delta_leak_EC_actual_bits"] = compare["leak_EC_actual_bits_new"] - compare["leak_EC_actual_bits_old"]
    compare["delta_PIE_secure_actual_ir"] = compare["PIE_secure_actual_ir_new"] - compare["PIE_secure_actual_ir_old"]
    compare["delta_SKR_secure_actual_ir_bps"] = compare["SKR_secure_actual_ir_bps_new"] - compare["SKR_secure_actual_ir_bps_old"]
    compare.to_csv(out_dir / "routeA_correctness_compare.csv", index=False)

    old_best = old_df.loc[pd.to_numeric(old_df["SKR_secure_actual_ir_bps"], errors="coerce").idxmax()]
    new_best = new_df.loc[pd.to_numeric(new_df["SKR_secure_actual_ir_bps"], errors="coerce").idxmax()]
    old_best_key = (int(old_best["dimension"]), int(old_best["bin_width_ps"]))
    new_best_key = (int(new_best["dimension"]), int(new_best["bin_width_ps"]))
    best_changed = old_best_key != new_best_key
    formal_rows = int(compare["epsilon_EC_bound_new"].notna().sum())
    formal_ratio = (float(formal_rows) / float(len(compare))) if len(compare) > 0 else 0.0
    lines = [
        f"row_count: {len(compare)}",
        f"formal_rows: {formal_rows}",
        f"formal_coverage_ratio: {formal_ratio:.6f}",
        f"mean_delta_leak_EC_actual_bits: {compare['delta_leak_EC_actual_bits'].mean()}",
        f"mean_delta_PIE_secure_actual_ir: {compare['delta_PIE_secure_actual_ir'].mean()}",
        f"mean_delta_SKR_secure_actual_ir_bps: {compare['delta_SKR_secure_actual_ir_bps'].mean()}",
        f"mean_lambda_ver_bits_actual_new: {compare['lambda_ver_bits_actual_new'].mean()}",
        f"mean_decoder_fail_rate_oracle_new: {compare['decoder_fail_rate_oracle_new'].mean()}",
        f"mean_epsilon_EC_empirical_new: {compare['epsilon_EC_empirical_new'].mean()}",
        f"mean_epsilon_EC_bound_new: {compare['epsilon_EC_bound_new'].mean()}",
        f"old_best_point: d={old_best_key[0]}, bw={old_best_key[1]}",
        f"new_best_point: d={new_best_key[0]}, bw={new_best_key[1]}",
        f"best_point_changed_flag: {1 if best_changed else 0}",
        f"best_point_change_explanation: {'changed under formal universal-hash verification leakage and epsilon_EC_bound correctness budgeting; no error-model or q-ary protocol change is included' if best_changed else 'unchanged'}",
        "note: new route uses universal-hash verification leakage and epsilon_EC_bound correctness budgeting; empirical quantities remain audit-only.",
    ]
    (out_dir / "routeA_correctness_compare_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
