#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SECURITY_REPORTS = REPO_ROOT / "tools" / "security_reports"
for _p in (REPO_ROOT, SECURITY_REPORTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import argparse
from pathlib import Path

from _longrun_common import (
    DEFAULT_BETA_BASELINE,
    DEFAULT_EPS_COR,
    DEFAULT_EPS_SEC,
    DEFAULT_FRANSON_VISIBILITY,
    python_tool,
    write_text,
)
from src.reconciliation.verification import VERIFICATION_PROTOCOL_ID


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Route A formal Stage C security outputs from formal stage1 replay tables.")
    ap.add_argument("--candidate-dir", required=True)
    ap.add_argument("--stage1-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    candidate_dir = Path(args.candidate_dir)
    stage1_dir = Path(args.stage1_dir)
    output_dir = Path(args.output_dir)
    required_candidate_csv = candidate_dir / "polar_e2e_results.csv"
    if not required_candidate_csv.is_file():
        raise SystemExit(
            "Stage 2 requires a candidate containing polar_e2e_results.csv: "
            f"{required_candidate_csv}"
        )

    python_tool(
        "longrun_build_finite_key_audit_table.py",
        "--input-dirs",
        str(candidate_dir),
        str(stage1_dir),
        "--franson-visibility",
        str(DEFAULT_FRANSON_VISIBILITY),
        "--eps-sec",
        str(DEFAULT_EPS_SEC),
        "--eps-cor",
        str(DEFAULT_EPS_COR),
        "--output-dir",
        str(output_dir),
        *(["--overwrite"] if bool(args.overwrite) else []),
    )
    python_tool(
        "longrun_build_actual_ir_finite_key_shadow.py",
        "--franson-visibility",
        str(DEFAULT_FRANSON_VISIBILITY),
        "--eps-sec",
        str(DEFAULT_EPS_SEC),
        "--eps-cor",
        str(DEFAULT_EPS_COR),
        "--output-dir",
        str(output_dir),
        "--overwrite",
    )
    python_tool(
        "longrun_build_beta_baseline_shadow.py",
        "--franson-visibility",
        str(DEFAULT_FRANSON_VISIBILITY),
        "--beta-baseline",
        str(DEFAULT_BETA_BASELINE),
        "--eps-sec",
        str(DEFAULT_EPS_SEC),
        "--eps-cor",
        str(DEFAULT_EPS_COR),
        "--output-dir",
        str(output_dir),
        "--overwrite",
    )
    python_tool(
        "longrun_build_security_master_table.py",
        "--actual-ir-dir",
        str(output_dir),
        "--beta-baseline-dir",
        str(output_dir),
        "--performance-proxy-input-dirs",
        str(candidate_dir),
        "--output-dir",
        str(output_dir),
        "--overwrite",
    )

    write_text(
        output_dir / "routeA_formal_stageC_summary.txt",
        "\n".join(
            [
                f"candidate_dir: {candidate_dir}",
                f"stage1_dir: {stage1_dir}",
                f"output_dir: {output_dir}",
                f"verification_protocol_id: {VERIFICATION_PROTOCOL_ID}",
                "correctness_budget_rule: epsilon_EC_bound enters eps_cor_total; empirical replay quantities are audit-only.",
                "claim_boundary: paper-grade reconciliation correctness is formalized; the calibrated actual-IR finite-key output is non-composable.",
            ]
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

