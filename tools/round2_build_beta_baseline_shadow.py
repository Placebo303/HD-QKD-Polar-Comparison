#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from _security_round_common import REPO_ROOT, ensure_output_dir, write_summary


def main() -> int:
    ap = argparse.ArgumentParser(description="Build literature-beta finite-key baseline shadow from audit table.")
    ap.add_argument("--input-dirs", nargs="*", default=[])
    ap.add_argument("--franson-visibility", type=float, default=0.95)
    ap.add_argument("--beta-baseline", type=float, default=0.90)
    ap.add_argument("--eps-sec", type=float, default=1e-10)
    ap.add_argument("--eps-cor", type=float, default=1e-10)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        ensure_output_dir(output_dir, overwrite=bool(args.overwrite))
    audit = pd.read_csv(output_dir / "finite_key_audit_point_table.csv")
    beta = float(args.beta_baseline)
    audit["beta_baseline"] = beta
    audit["PIE_secure_beta_baseline"] = np.maximum(
        0.0,
        beta * pd.to_numeric(audit["IAB_est"], errors="coerce")
        - pd.to_numeric(audit["chi_E_calibrated"], errors="coerce")
        - pd.to_numeric(audit["DeltaFK_calibrated"], errors="coerce")
        - pd.to_numeric(audit["post_selection_correction"], errors="coerce").fillna(0.0),
    )
    audit["SKR_secure_beta_baseline_bps"] = pd.to_numeric(audit["PIE_secure_beta_baseline"], errors="coerce") * pd.to_numeric(audit["accepted_rate_proxy"], errors="coerce")
    audit["beta_baseline_model_tag"] = "literature_beta_finite_key_baseline"
    keep = [
        "loss_db", "dimension", "bin_width_ps", "beta_baseline", "IAB_est", "DeltaFK_calibrated", "accepted_rate_proxy",
        "PIE_secure_beta_baseline", "SKR_secure_beta_baseline_bps", "beta_baseline_model_tag",
    ]
    audit[keep].to_csv(output_dir / "beta_baseline_finite_key_point_table.csv", index=False)
    lines = [
        f"point_count: {len(audit)}",
        f"beta_baseline: {beta}",
        "comparison_role: comparison_only",
        "note: fixed beta can mask real Polar IR quality differences across points.",
    ]
    write_summary(output_dir / "beta_baseline_finite_key_summary.txt", lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
