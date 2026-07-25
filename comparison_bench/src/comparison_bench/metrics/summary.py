from __future__ import annotations

import pandas as pd


def add_fraction_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    attempted = pd.to_numeric(out.get("n_frames_attempted"), errors="coerce").astype("float64")
    success = pd.to_numeric(out.get("n_frames_success"), errors="coerce").astype("float64")
    fraction = success.div(attempted.where(attempted != 0))
    out["accepted_frame_fraction"] = fraction.fillna(0.0).astype("float64")
    out["rejected_frame_fraction"] = (1.0 - out["accepted_frame_fraction"]).clip(lower=0.0, upper=1.0)
    return out


def summarize_methods(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    group_cols = [c for c in ["dataset_id", "data_mode", "dimension", "bin_width_ps", "method", "method_variant", "method_status", "backend_status", "real_ir_success", "success_classification"] if c in df.columns]
    metric_cols = [c for c in [
        "n_frames_attempted", "n_frames_success", "n_frames_failed_decode", "n_frames_failed_verify",
        "accepted_frame_fraction", "raw_ser", "raw_ber", "post_ir_ser", "post_ir_ber",
        "leak_EC_actual_bits", "leak_EC_per_input_bit", "beta_eff_empirical", "runtime_s",
        "throughput_input_bits_per_s", "throughput_output_bits_per_s",
    ] if c in df.columns]
    return df.groupby(group_cols, dropna=False)[metric_cols].mean(numeric_only=True).reset_index()
