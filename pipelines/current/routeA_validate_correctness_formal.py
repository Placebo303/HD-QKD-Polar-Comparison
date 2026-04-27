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

import pandas as pd


FORMULA_TAG = "union_bound_over_blocks_universal_hash"


def _num(frame: pd.DataFrame, col: str) -> pd.Series:
    if col not in frame.columns:
        return pd.Series([float("nan")] * len(frame), index=frame.index)
    return pd.to_numeric(frame[col], errors="coerce")


def _missing(frame: pd.DataFrame, cols: list[str]) -> list[str]:
    return [c for c in cols if c not in frame.columns]


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Route A formal correctness block/point/master outputs.")
    ap.add_argument("--stage1-dir", required=True)
    ap.add_argument("--master", default="")
    ap.add_argument("--expected-points", type=int, default=0)
    ap.add_argument("--verification-tag-bits", type=int, default=32)
    ap.add_argument("--output-dir", default="")
    args = ap.parse_args()

    stage1_dir = Path(args.stage1_dir)
    output_dir = Path(args.output_dir) if str(args.output_dir).strip() else stage1_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    warnings: list[str] = []

    block = pd.read_csv(stage1_dir / "actual_ir_block_table.csv")
    point = pd.read_csv(stage1_dir / "actual_ir_point_table.csv")
    master = pd.read_csv(Path(args.master)) if str(args.master).strip() else pd.DataFrame()

    block_required = [
        "verification_protocol_id",
        "verification_family",
        "verification_invoked_flag",
        "verification_bits_budgeted",
        "verification_bits_used_actual",
        "verification_seed_index",
        "verification_pass_flag",
        "verification_fail_flag",
        "verification_transcript_source_tag",
        "block_match_oracle_flag",
        "undetected_error_oracle_flag",
    ]
    point_required = [
        "lambda_ver_bits_actual",
        "lambda_ver_source_tag",
        "verification_invoked_block_count",
        "verification_pass_count",
        "verification_fail_count",
        "undetected_error_count_empirical",
        "epsilon_EC_empirical",
        "epsilon_EC_bound",
        "epsilon_EC_bound_formula_tag",
        "decoder_fail_rate_oracle",
        "decoder_fail_rate_oracle_source_tag",
    ]
    master_required = [
        "eps_cor_total",
        "eps_cor_from_epsilon_EC",
        "eps_cor_budget_rule",
        "epsilon_EC_in_budget_flag",
        "epsilon_EC_bound",
        "epsilon_EC_bound_formula_tag",
    ]

    for col in _missing(block, block_required):
        errors.append(f"missing block column: {col}")
    for col in _missing(point, point_required):
        errors.append(f"missing point column: {col}")
    if not master.empty:
        for col in _missing(master, master_required):
            errors.append(f"missing master column: {col}")

    if not errors:
        invoked_block = _num(block, "verification_invoked_flag").fillna(0)
        block_match = _num(block, "block_match_oracle_flag").fillna(0)
        undetected = _num(block, "undetected_error_oracle_flag").fillna(0)
        if bool(((undetected == 1) & (block_match != 0)).any()):
            errors.append("undetected_error_oracle_flag=1 found where block_match_oracle_flag is not 0")

        used_bits = _num(block, "verification_bits_used_actual")
        bad_block_bits = (invoked_block == 1) & used_bits.notna() & (used_bits != int(args.verification_tag_bits))
        if bool(bad_block_bits.any()):
            errors.append("invoked block has verification_bits_used_actual different from verification_tag_bits")

        empirical = _num(point, "epsilon_EC_empirical")
        bound = _num(point, "epsilon_EC_bound")
        if bool((empirical.dropna() > 1.0).any()):
            errors.append("epsilon_EC_empirical exceeds 1")
        if bool((bound.dropna() > 1.0).any()):
            errors.append("epsilon_EC_bound exceeds 1")

        invoked_point = _num(point, "verification_invoked_block_count")
        lambda_ver = _num(point, "lambda_ver_bits_actual")
        expected_lambda = invoked_point * int(args.verification_tag_bits)
        lambda_valid = invoked_point.notna() & lambda_ver.notna()
        if bool(((lambda_ver[lambda_valid] - expected_lambda[lambda_valid]).abs() > 1e-9).any()):
            errors.append("lambda_ver_bits_actual != verification_invoked_block_count * verification_tag_bits")

    point_formal_rows = int(point.get("epsilon_EC_bound_formula_tag", pd.Series(dtype=str)).astype(str).eq(FORMULA_TAG).sum())
    master_formal_rows = 0
    if not master.empty:
        master_formal_rows = int(master.get("epsilon_EC_bound_formula_tag", pd.Series(dtype=str)).astype(str).eq(FORMULA_TAG).sum())
        budget_flags = _num(master, "epsilon_EC_in_budget_flag")
        formal_mask = master.get("epsilon_EC_bound_formula_tag", pd.Series(dtype=str)).astype(str).eq(FORMULA_TAG)
        if bool((budget_flags[formal_mask].dropna() != 1).any()):
            errors.append("formal master rows contain epsilon_EC_in_budget_flag values different from 1")

    expected_points = int(args.expected_points)
    if expected_points > 0:
        if len(point) != expected_points:
            errors.append(f"point row count {len(point)} != expected {expected_points}")
        if point_formal_rows != expected_points:
            errors.append(f"formal point rows {point_formal_rows} != expected {expected_points}")
        if not master.empty and master_formal_rows != expected_points:
            errors.append(f"formal master rows {master_formal_rows} != expected {expected_points}")

    if block.empty:
        errors.append("block table is empty")
    if point.empty:
        errors.append("point table is empty")
    if master.empty and str(args.master).strip():
        errors.append("master table is empty")
    if not master.empty and len(master) != len(point):
        warnings.append(f"master row count {len(master)} differs from point row count {len(point)}")

    status = "ok" if not errors else "failed"
    error_lines = [f"  - {e}" for e in errors] if errors else ["  - none"]
    warning_lines = [f"  - {w}" for w in warnings] if warnings else ["  - none"]
    lines = [
        f"validation_status: {status}",
        f"stage1_dir: {stage1_dir}",
        f"master: {Path(args.master) if str(args.master).strip() else 'not_provided'}",
        f"verification_tag_bits: {int(args.verification_tag_bits)}",
        f"block_rows: {len(block)}",
        f"point_rows: {len(point)}",
        f"point_formal_rows: {point_formal_rows}",
        f"master_rows: {len(master) if not master.empty else 0}",
        f"master_formal_rows: {master_formal_rows}",
        f"expected_points: {expected_points if expected_points > 0 else 'not_set'}",
        "errors:",
        *error_lines,
        "warnings:",
        *warning_lines,
    ]
    (output_dir / "routeA_correctness_formal_validation.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if errors:
        raise SystemExit(1)
    print(f"formal_validation_ok point_formal_rows={point_formal_rows} master_formal_rows={master_formal_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

