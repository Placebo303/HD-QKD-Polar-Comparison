#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from _security_round_common import REPO_ROOT, ensure_output_dir, write_summary


def _default_output_dir() -> Path:
    return REPO_ROOT / "results" / "_tmp_round2_finite_key"


def main() -> int:
    ap = argparse.ArgumentParser(description="Build actual-IR finite-key calibrated shadow from audit table.")
    ap.add_argument("--input-dirs", nargs="*", default=[])
    ap.add_argument("--franson-visibility", type=float, default=0.95)
    ap.add_argument("--eps-sec", type=float, default=1e-10)
    ap.add_argument("--eps-cor", type=float, default=1e-10)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        ensure_output_dir(output_dir, overwrite=bool(args.overwrite))
    audit = pd.read_csv(output_dir / "finite_key_audit_point_table.csv")
    audit["PIE_secure_actual_ir"] = np.maximum(
        0.0,
        pd.to_numeric(audit["IAB_est"], errors="coerce")
        - pd.to_numeric(audit["leak_EC_actual_bits"], errors="coerce")
        - pd.to_numeric(audit["chi_E_calibrated"], errors="coerce")
        - pd.to_numeric(audit["DeltaFK_calibrated"], errors="coerce")
        - pd.to_numeric(audit["post_selection_correction"], errors="coerce").fillna(0.0),
    )
    audit["SKR_secure_actual_ir_bps"] = pd.to_numeric(audit["PIE_secure_actual_ir"], errors="coerce") * pd.to_numeric(audit["accepted_rate_proxy"], errors="coerce")
    audit["beta_eff"] = np.where(
        pd.to_numeric(audit["IAB_est"], errors="coerce") > 0.0,
        np.maximum(
            0.0,
            pd.to_numeric(audit["IAB_est"], errors="coerce") - pd.to_numeric(audit["leak_EC_actual_bits"], errors="coerce"),
        ) / pd.to_numeric(audit["IAB_est"], errors="coerce"),
        np.nan,
    )
    audit["actual_ir_model_tag"] = "strict_zhong_like_actual_ir_finite_key_calibrated"
    keep = [
        "loss_db", "dimension", "bin_width_ps", "franson_visibility_global", "IAB_est", "leak_EC_actual_bits",
        "leak_EC_source_tag", "eps_sec", "eps_cor", "n_eff_pairs", "clean_pair_fraction", "layer_fraction",
        "accepted_frame_fraction", "rejected_frame_fraction", "exactly_one_click_fraction", "post_selection_correction",
        "DeltaFK_calibrated", "accepted_rate_proxy", "PIE_secure_actual_ir", "SKR_secure_actual_ir_bps", "beta_eff",
        "processing_rule_version", "pairing_path_tag", "pairing_window_source_tag", "threshold_ps", "effective_pairing_window_ps",
        "threshold_ratio_to_bw", "best_hard_PIE", "PIE_practical", "SKR_measured_bps", "actual_ir_model_tag",
    ]
    audit[keep].to_csv(output_dir / "actual_ir_finite_key_point_table.csv", index=False)
    perf_drop = pd.to_numeric(audit["PIE_practical"], errors="coerce") - pd.to_numeric(audit["PIE_secure_actual_ir"], errors="coerce")
    large_mask = (pd.to_numeric(audit["bin_width_ps"], errors="coerce") >= 120) | (pd.to_numeric(audit["dimension"], errors="coerce") >= 1024)
    lines = [
        f"point_count: {len(audit)}",
        f"actual_leak_rows: {int(audit['leak_EC_source_tag'].astype(str).str.startswith('actual_ir_replay').sum())}",
        f"surrogate_leak_rows: {int(audit['leak_EC_source_tag'].astype(str).str.startswith('surrogate').sum())}",
        "DeltaFK_primary_inputs: n_pairs_actual, layer_fraction, accepted_frame_fraction, block_success_rate_used",
        f"mean_PIE_drop_vs_performance_proxy: {perf_drop.mean()}",
        f"large_bw_or_large_d_mean_PIE_drop: {pd.to_numeric(perf_drop[large_mask], errors='coerce').mean()}",
        f"beta_eff_range_p10_p90: {audit['beta_eff'].quantile(0.10)} .. {audit['beta_eff'].quantile(0.90)}",
    ]
    write_summary(output_dir / "actual_ir_finite_key_summary.txt", lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
