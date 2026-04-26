#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _longrun_common import REPO_ROOT, csv_read, python_tool, safe_copy, write_text


def main() -> int:
    ap = argparse.ArgumentParser(description="Longrun wrapper for the Stage 2 20 dB security master table.")
    ap.add_argument("--actual-ir-dir", required=True)
    ap.add_argument("--beta-baseline-dir", required=True)
    ap.add_argument("--performance-proxy-input-dirs", nargs="*", default=[str(REPO_ROOT / "results" / "e2e_20dB_fullgrid_pairing_v2_candidate_t15")])
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    python_tool(
        "round2_build_security_round2_summary.py",
        "--actual-ir-dir",
        str(Path(args.actual_ir_dir)),
        "--beta-baseline-dir",
        str(Path(args.beta_baseline_dir)),
        "--performance-proxy-input-dirs",
        *[str(Path(p)) for p in args.performance_proxy_input_dirs],
        "--output-dir",
        str(output_dir),
        "--overwrite",
    )

    safe_copy(output_dir / "round2_security_master_table.csv", output_dir / "security_calibrated_master_table.csv")
    merged = csv_read(output_dir / "security_calibrated_master_table.csv")
    actual_rows = int(merged["leak_EC_source_tag"].astype(str).str.startswith("actual_ir_replay").sum()) if "leak_EC_source_tag" in merged.columns else 0
    coverage_ratio = (float(actual_rows) / float(len(merged))) if len(merged) > 0 else 0.0
    ready_tag = "yes_with_caveats" if coverage_ratio >= 0.80 else "partial_mixed_actual_surrogate"
    proxy_delta = pd.to_numeric(merged["PIE_practical"], errors="coerce") - pd.to_numeric(merged["PIE_secure_actual_ir"], errors="coerce")
    beta_delta = pd.to_numeric(merged["PIE_secure_beta_baseline"], errors="coerce") - pd.to_numeric(merged["PIE_secure_actual_ir"], errors="coerce")
    perf_best = merged.loc[pd.to_numeric(merged["SKR_measured_bps"], errors="coerce").idxmax()]
    actual_best = merged.loc[pd.to_numeric(merged["SKR_secure_actual_ir_bps"], errors="coerce").idxmax()]
    lines = [
        f"point_count: {len(merged)}",
        f"actual_leak_rows: {actual_rows}",
        f"surrogate_rows: {int(merged['leak_EC_source_tag'].astype(str).str.startswith('surrogate').sum())}",
        "DeltaFK_primary_inputs: n_pairs_actual, layer_fraction, accepted_frame_fraction, block_success_rate_used, eps_sec, eps_cor",
        "post_selection_sensitive_region: higher-bw / lower-clean-fraction points move most because post_selection_correction follows accepted_frame_fraction",
        f"mean_PIE_drop_actual_vs_performance: {proxy_delta.mean()}",
        f"beta_baseline_more_optimistic_rows: {int((beta_delta > 0).sum())}",
        f"beta_baseline_more_conservative_rows: {int((beta_delta < 0).sum())}",
        f"performance_best_point: d={int(perf_best['dimension'])}, bw={int(perf_best['bin_width_ps'])}",
        f"actual_ir_best_point: d={int(actual_best['dimension'])}, bw={int(actual_best['bin_width_ps'])}",
        f"positive_actual_secure_rows: {int((pd.to_numeric(merged['SKR_secure_actual_ir_bps'], errors='coerce') > 0).sum())}",
        f"conference_paper_ready_tag: {ready_tag}",
        "PRIMARY_REPORTING_MODE = actual_ir_finite_key",
        "BETA_BASELINE_ROLE = comparison_only",
        "NIU_2016_STATUS = not_supported_by_current_observables",
    ]
    write_text(output_dir / "stage2_summary.txt", "\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
