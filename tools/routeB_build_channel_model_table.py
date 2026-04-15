#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

from _security_round_common import write_summary


def _h2(p: float) -> float:
    if not math.isfinite(p):
        return float("nan")
    p = min(1.0, max(0.0, float(p)))
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return float(-(p * math.log2(p) + (1.0 - p) * math.log2(1.0 - p)))


def _mi(p01: float, p10: float, prior_a1: float) -> float:
    if not all(math.isfinite(x) for x in (p01, p10, prior_a1)):
        return float("nan")
    pi1 = min(1.0, max(0.0, float(prior_a1)))
    pi0 = 1.0 - pi1
    py1 = pi0 * p01 + pi1 * (1.0 - p10)
    return float(_h2(py1) - pi0 * _h2(p01) - pi1 * _h2(p10))


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Route B-lite asymmetric binary channel model tables.")
    ap.add_argument("--audit-dir", default="results/_tmp_routeB_lite_error_audit")
    ap.add_argument("--output-dir", default="")
    args = ap.parse_args()

    audit_dir = Path(args.audit_dir)
    output_dir = Path(args.output_dir) if str(args.output_dir).strip() else audit_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    layer = pd.read_csv(audit_dir / "routeB_layer_confusion_table.csv")
    diagnosis = pd.read_csv(audit_dir / "routeB_model_diagnosis_table.csv")

    out = layer.copy()
    out["channel_model_tag"] = "asym_binary_v1"
    out["prior_model_tag"] = "uniform_prior_decoder_model"
    out["p01_model"] = pd.to_numeric(out["p01_model"], errors="coerce")
    out["p10_model"] = pd.to_numeric(out["p10_model"], errors="coerce")
    out["p_a1_empirical"] = pd.to_numeric(out["p_a1_empirical"], errors="coerce")
    out["uniform_prior_asym_mi"] = [
        _mi(float(p01), float(p10), 0.5) for p01, p10 in zip(out["p01_model"], out["p10_model"])
    ]
    out["empirical_prior_asym_mi"] = [
        _mi(float(p01), float(p10), float(pa1))
        for p01, p10, pa1 in zip(out["p01_model"], out["p10_model"], out["p_a1_empirical"])
    ]
    out["bsc_capacity_1_minus_h2_ber"] = [1.0 - _h2(float(x)) for x in pd.to_numeric(out["ber_symmetric"], errors="coerce")]
    out["capacity_delta_uniform_asym_minus_bsc"] = out["uniform_prior_asym_mi"] - out["bsc_capacity_1_minus_h2_ber"]
    out["capacity_delta_empirical_asym_minus_bsc"] = out["empirical_prior_asym_mi"] - out["bsc_capacity_1_minus_h2_ber"]
    out["llr_b0"] = np.log((1.0 - out["p01_model"]) / out["p10_model"])
    out["llr_b1"] = np.log(out["p01_model"] / (1.0 - out["p10_model"]))
    out["model_source_tag"] = "routeB_error_audit_from_a_eff_b_eff"
    out["capacity_interpretation_tag"] = "model_diagnostic_not_decoder_gain_prediction"
    out["eligible_for_B3_model_flag"] = (
        (pd.to_numeric(out["eligible_for_B3_flag"], errors="coerce") == 1)
        & (pd.to_numeric(out["p01_clipped_flag"], errors="coerce") == 0)
        & (pd.to_numeric(out["p10_clipped_flag"], errors="coerce") == 0)
    ).astype(int)
    out.to_csv(output_dir / "routeB_channel_model_layer_table.csv", index=False)

    compare_cols = [
        "loss_db", "dimension", "bin_width_ps", "point_id", "layer_idx",
        "channel_model_tag", "prior_model_tag", "p_a0_empirical", "p_a1_empirical",
        "p01_model", "p10_model", "uniform_prior_asym_mi", "empirical_prior_asym_mi",
        "bsc_capacity_1_minus_h2_ber", "capacity_delta_uniform_asym_minus_bsc",
        "capacity_delta_empirical_asym_minus_bsc", "eligible_for_B2_flag",
        "eligible_for_B3_model_flag", "capacity_interpretation_tag",
    ]
    out[[c for c in compare_cols if c in out.columns]].to_csv(output_dir / "routeB_bsc_vs_asym_capacity_compare.csv", index=False)

    point_model = out.groupby(["loss_db", "dimension", "bin_width_ps", "point_id"], as_index=False).agg(
        eligible_B3_model_layers=("eligible_for_B3_model_flag", "sum"),
        mean_capacity_delta_uniform_asym_minus_bsc=("capacity_delta_uniform_asym_minus_bsc", "mean"),
        max_capacity_delta_uniform_asym_minus_bsc=("capacity_delta_uniform_asym_minus_bsc", "max"),
        mean_uniform_prior_asym_mi=("uniform_prior_asym_mi", "mean"),
        mean_bsc_capacity=("bsc_capacity_1_minus_h2_ber", "mean"),
    )
    point_model = point_model.merge(
        diagnosis[["point_id", "asym_binary_candidate_flag", "offset_like_candidate_flag", "diagnostic_only_flag", "decoder_fail_rate_oracle"]],
        on="point_id",
        how="left",
    )
    point_model.to_csv(output_dir / "routeB_channel_model_point_table.csv", index=False)

    finite_cols = ["uniform_prior_asym_mi", "empirical_prior_asym_mi", "bsc_capacity_1_minus_h2_ber"]
    bad_ranges = {}
    for col in finite_cols:
        vals = pd.to_numeric(out[col], errors="coerce").dropna()
        bad_ranges[col] = int(((vals < -1e-9) | (vals > 1.0 + 1e-9)).sum())
    summary = [
        f"audit_dir: {audit_dir}",
        f"layer_rows: {len(out)}",
        f"point_rows: {len(point_model)}",
        f"eligible_B3_model_layers: {int(out['eligible_for_B3_model_flag'].sum())}",
        f"positive_capacity_delta_layers: {int((pd.to_numeric(out['capacity_delta_uniform_asym_minus_bsc'], errors='coerce') > 0).sum())}",
        f"mean_capacity_delta_uniform_asym_minus_bsc: {pd.to_numeric(out['capacity_delta_uniform_asym_minus_bsc'], errors='coerce').mean()}",
        f"bad_range_counts: {bad_ranges}",
        "prior_note: uniform_prior_asym_mi is the decoder-model diagnostic line; empirical_prior_asym_mi is source-prior audit only.",
        "capacity_boundary: positive capacity_delta_uniform_asym_minus_bsc means the asymmetric model is a better statistical description under the chosen prior; it does not imply replay, block success, PIE, or SKR improvement.",
    ]
    write_summary(output_dir / "routeB_channel_model_summary.txt", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
