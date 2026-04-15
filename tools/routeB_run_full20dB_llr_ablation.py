#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from _longrun_common import candidate_dir_for_loss, python_tool, write_text
from routeB_run_b3_subset_ablation import _build_compare, _load_model_outputs, _point_id


KEY = ["loss_db", "dimension", "bin_width_ps"]
LOSS_DB = 20
EXPECTED_POINTS = 121


def _load_full20_manifest(routea_dir: Path) -> pd.DataFrame:
    stage1 = routea_dir / "loss_20dB" / "stage1_actual_ir"
    point = pd.read_csv(stage1 / "replay_index_point_table.csv")
    for col in KEY:
        if col not in point.columns:
            raise SystemExit(f"missing column in replay index: {col}")
    point = point[point["loss_db"].astype(int).eq(LOSS_DB)].copy()
    if "point_id" not in point.columns:
        point["point_id"] = point.apply(_point_id, axis=1)
    point = point[KEY + ["point_id"]].drop_duplicates().sort_values(KEY).reset_index(drop=True)
    if len(point) != EXPECTED_POINTS:
        raise SystemExit(f"expected {EXPECTED_POINTS} 20dB points, got {len(point)}")
    return point


def _run_one_model(
    *,
    model_root: Path,
    model_tag: str,
    routea_dir: Path,
    audit_dir: Path,
    workers: int,
    verification_tag_bits: int,
    overwrite: bool,
) -> dict[str, object]:
    candidate_dir = candidate_dir_for_loss(LOSS_DB)
    src_stage1 = routea_dir / "loss_20dB" / "stage1_actual_ir"
    loss_root = model_root / "loss_20dB"
    stage1 = loss_root / "stage1_actual_ir"
    stage2 = loss_root / "stage2_security"
    start = time.perf_counter()
    cmd_args = [
        "--candidate-dir",
        str(candidate_dir),
        "--replay-index-dir",
        str(src_stage1),
        "--output-dir",
        str(stage1),
        "--shards",
        str(EXPECTED_POINTS),
        "--workers",
        str(int(workers)),
        "--verification-tag-bits",
        str(int(verification_tag_bits)),
        "--channel-model-tag",
        str(model_tag),
    ]
    if model_tag == "asym_binary_v1":
        cmd_args.extend(["--channel-model-table", str(audit_dir / "routeB_channel_model_layer_table.csv")])
    if overwrite:
        cmd_args.append("--overwrite")
    python_tool("routeA_run_formal_replay_shards.py", *cmd_args)
    stage1_seconds = time.perf_counter() - start
    start = time.perf_counter()
    stage2_args = [
        "--candidate-dir",
        str(candidate_dir),
        "--stage1-dir",
        str(stage1),
        "--output-dir",
        str(stage2),
    ]
    if overwrite:
        stage2_args.append("--overwrite")
    python_tool("routeA_build_formal_stageC.py", *stage2_args)
    stage2_seconds = time.perf_counter() - start
    _validate_model_output(stage1, stage2)
    return {
        "model_tag": model_tag,
        "loss_db": LOSS_DB,
        "point_count": EXPECTED_POINTS,
        "workers": int(workers),
        "attempt_status": "success",
        "attempt_error": "",
        "stage1_seconds": float(stage1_seconds),
        "stage2_seconds": float(stage2_seconds),
        "runtime_seconds_total": float(stage1_seconds + stage2_seconds),
        "runtime_seconds_per_point": float((stage1_seconds + stage2_seconds) / EXPECTED_POINTS),
        "stage1_dir": str(stage1),
        "stage2_dir": str(stage2),
    }


def _validate_model_output(stage1: Path, stage2: Path) -> None:
    point = pd.read_csv(stage1 / "actual_ir_point_table.csv")
    master = pd.read_csv(stage2 / "security_calibrated_master_table.csv")
    if len(point) != EXPECTED_POINTS:
        raise RuntimeError(f"point table row count mismatch: {len(point)} != {EXPECTED_POINTS}")
    if len(master) != EXPECTED_POINTS:
        raise RuntimeError(f"master table row count mismatch: {len(master)} != {EXPECTED_POINTS}")


def _run_with_fallback(
    *,
    model_root: Path,
    model_tag: str,
    routea_dir: Path,
    audit_dir: Path,
    workers: int,
    verification_tag_bits: int,
    overwrite: bool,
) -> list[dict[str, object]]:
    candidates = []
    for w in (int(workers), 2, 1):
        if w > 0 and w not in candidates:
            candidates.append(w)
    rows: list[dict[str, object]] = []
    for idx, worker_count in enumerate(candidates):
        try:
            row = _run_one_model(
                model_root=model_root,
                model_tag=model_tag,
                routea_dir=routea_dir,
                audit_dir=audit_dir,
                workers=worker_count,
                verification_tag_bits=verification_tag_bits,
                overwrite=True if idx > 0 else overwrite,
            )
            row["attempt_index"] = idx + 1
            rows.append(row)
            return rows
        except Exception as exc:
            rows.append(
                {
                    "model_tag": model_tag,
                    "loss_db": LOSS_DB,
                    "point_count": EXPECTED_POINTS,
                    "workers": int(worker_count),
                    "attempt_index": idx + 1,
                    "attempt_status": "failed",
                    "attempt_error": str(exc),
                    "stage1_seconds": np.nan,
                    "stage2_seconds": np.nan,
                    "runtime_seconds_total": np.nan,
                    "runtime_seconds_per_point": np.nan,
                    "stage1_dir": str(model_root / "loss_20dB" / "stage1_actual_ir"),
                    "stage2_dir": str(model_root / "loss_20dB" / "stage2_security"),
                }
            )
    raise SystemExit(f"all worker attempts failed for {model_tag}")


def _num(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce") if col in df.columns else pd.Series(np.nan, index=df.index)


def _write_point_notes(compare: pd.DataFrame, out_path: Path) -> None:
    notes = compare[["loss_db", "dimension", "bin_width_ps", "point_id", "model_fallback_tag", "improvement_flag", "degradation_flag"]].copy()
    notes["note"] = np.select(
        [
            notes["model_fallback_tag"].astype(str).str.contains("invalid|ineligible|missing", case=False, na=False),
            notes["improvement_flag"].eq(1),
            notes["degradation_flag"].eq(1),
        ],
        [
            "asym_binary layer fallback occurred; inspect block table before interpreting this point",
            "LLR-only asym-binary improved decoder/block metrics under unchanged correctness",
            "LLR-only asym-binary degraded at least one monitored replay/security metric",
        ],
        default="LLR-only asym-binary tied baseline under unchanged correctness",
    )
    notes.to_csv(out_path, index=False)


def _decide(compare: pd.DataFrame, runtime_success: pd.DataFrame) -> tuple[str, dict[str, float | int | str]]:
    n = len(compare)
    improve = int(compare["improvement_flag"].sum())
    degrade = int(compare["degradation_flag"].sum())
    tie = int(n - improve - degrade)
    delta_fail = _num(compare, "delta_decoder_fail_rate_oracle")
    delta_success = _num(compare, "delta_block_success")
    delta_pie = _num(compare, "delta_PIE_secure_actual_ir")
    delta_skr = _num(compare, "delta_SKR_secure_actual_ir_bps")
    delta_eps = (_num(compare, "epsilon_EC_bound_new") - _num(compare, "epsilon_EC_bound_old")).abs()
    delta_lambda = (_num(compare, "lambda_ver_bits_actual_new") - _num(compare, "lambda_ver_bits_actual_old")).abs()
    delta_leak = (_num(compare, "delta_leak_EC_actual_bits")).abs()
    old_rt = pd.to_numeric(runtime_success.loc[runtime_success["model_tag"].eq("bsc_legacy"), "runtime_seconds_per_point"], errors="coerce").mean()
    new_rt = pd.to_numeric(runtime_success.loc[runtime_success["model_tag"].eq("asym_binary_v1"), "runtime_seconds_per_point"], errors="coerce").mean()
    runtime_ratio = float(new_rt / old_rt) if old_rt and np.isfinite(old_rt) else np.nan
    fallback_points = int(compare["model_fallback_tag"].astype(str).str.contains("invalid|ineligible|missing", case=False, na=False).sum())
    correctness_same = bool(delta_eps.fillna(0).le(1e-18).all() and delta_lambda.fillna(0).le(0).all())
    metrics = {
        "point_count": n,
        "improvement_points": improve,
        "degradation_points": degrade,
        "tie_points": tie,
        "mean_delta_decoder_fail_rate_oracle": float(delta_fail.mean()),
        "median_delta_decoder_fail_rate_oracle": float(delta_fail.median()),
        "mean_delta_block_success": float(delta_success.mean()),
        "median_delta_block_success": float(delta_success.median()),
        "mean_delta_PIE_secure_actual_ir": float(delta_pie.mean()),
        "median_delta_PIE_secure_actual_ir": float(delta_pie.median()),
        "mean_delta_SKR_secure_actual_ir_bps": float(delta_skr.mean()),
        "median_delta_SKR_secure_actual_ir_bps": float(delta_skr.median()),
        "max_abs_delta_epsilon_EC_bound": float(delta_eps.max()),
        "max_abs_delta_lambda_ver_bits_actual": float(delta_lambda.max()),
        "max_abs_delta_leak_EC_actual_bits": float(delta_leak.max()),
        "fallback_points": fallback_points,
        "runtime_ratio_new_over_old": runtime_ratio,
        "correctness_same_flag": int(correctness_same),
    }
    if not correctness_same:
        return "STOP_AT_FULL_20DB", metrics
    if improve > n / 2 and degrade <= n * 0.25 and metrics["mean_delta_decoder_fail_rate_oracle"] < 0 and metrics["mean_delta_block_success"] > 0 and (metrics["mean_delta_PIE_secure_actual_ir"] > 0 or metrics["mean_delta_SKR_secure_actual_ir_bps"] > 0) and (not np.isfinite(runtime_ratio) or runtime_ratio <= 1.25) and fallback_points <= n * 0.25:
        return "GO_EXPAND_LLR_ONLY", metrics
    if improve >= max(10, int(0.25 * n)) and metrics["mean_delta_decoder_fail_rate_oracle"] < 0 and metrics["mean_delta_block_success"] > 0 and (not np.isfinite(runtime_ratio) or runtime_ratio <= 1.50):
        return "GO_WIDER_VALIDATION_BUT_NOT_MAINLINE", metrics
    return "STOP_AT_FULL_20DB", metrics


def _write_summary(compare: pd.DataFrame, runtime: pd.DataFrame, out_path: Path) -> str:
    runtime_success = runtime[runtime["attempt_status"].eq("success")].copy()
    decision, metrics = _decide(compare, runtime_success)
    failed_attempts = runtime[runtime["attempt_status"].eq("failed")]
    lines = [
        "# Route B-lite Full 20dB LLR-only Validation Summary",
        "",
        f"- final_decision: {decision}",
        f"- point_count: {metrics['point_count']}",
        f"- improvement_points: {metrics['improvement_points']}",
        f"- degradation_points: {metrics['degradation_points']}",
        f"- tie_points: {metrics['tie_points']}",
        f"- mean_delta_decoder_fail_rate_oracle: {metrics['mean_delta_decoder_fail_rate_oracle']}",
        f"- median_delta_decoder_fail_rate_oracle: {metrics['median_delta_decoder_fail_rate_oracle']}",
        f"- mean_delta_block_success: {metrics['mean_delta_block_success']}",
        f"- median_delta_block_success: {metrics['median_delta_block_success']}",
        f"- mean_delta_PIE_secure_actual_ir: {metrics['mean_delta_PIE_secure_actual_ir']}",
        f"- median_delta_PIE_secure_actual_ir: {metrics['median_delta_PIE_secure_actual_ir']}",
        f"- mean_delta_SKR_secure_actual_ir_bps: {metrics['mean_delta_SKR_secure_actual_ir_bps']}",
        f"- median_delta_SKR_secure_actual_ir_bps: {metrics['median_delta_SKR_secure_actual_ir_bps']}",
        f"- max_abs_delta_epsilon_EC_bound: {metrics['max_abs_delta_epsilon_EC_bound']}",
        f"- max_abs_delta_lambda_ver_bits_actual: {metrics['max_abs_delta_lambda_ver_bits_actual']}",
        f"- max_abs_delta_leak_EC_actual_bits: {metrics['max_abs_delta_leak_EC_actual_bits']}",
        f"- fallback_points: {metrics['fallback_points']}",
        f"- runtime_ratio_new_over_old: {metrics['runtime_ratio_new_over_old']}",
        f"- correctness_same_flag: {metrics['correctness_same_flag']}",
        "",
        "## Run Strategy",
        "",
        "The runner tries workers 4, then 2, then 1 when needed. Successful attempts are listed in `routeB_full20dB_runtime.csv` with `attempt_status=success`.",
        f"Fallback_attempt_count: {len(failed_attempts)}",
        "",
        "## Answers",
        "",
        f"1. Full 20dB improvement/degradation/tie: {metrics['improvement_points']} / {metrics['degradation_points']} / {metrics['tie_points']}",
        "2. Decoder fail and block success changes are reported above; PIE/SKR deltas are replay/security outcomes under unchanged correctness.",
        f"3. Correctness contamination: {'no' if metrics['correctness_same_flag'] else 'yes'}; `uhv1_per_block`, `epsilon_EC_bound`, and `lambda_ver_bits_actual` remain same-protocol.",
        "4. Stability is decided by the final label and point distribution, not by isolated best points.",
        "5. Wider expansion is allowed only for `GO_EXPAND_LLR_ONLY` or `GO_WIDER_VALIDATION_BUT_NOT_MAINLINE`.",
        "6. Full application/mainline migration is not supported by this validation.",
        f"7. Final stop/go label: {decision}",
        "8. Any next step must remain LLR-only unless a separate plan explicitly changes frozen ordering or construction.",
        "",
        "## Boundary",
        "",
        "This is fixed-order LLR-only validation. It is not q-ary Polar, nonbinary decoding, density evolution, Gaussian approximation construction, channel-aware Polar construction, or mainline migration.",
    ]
    if decision == "STOP_AT_FULL_20DB":
        lines.extend(["", "## Conclusion", "", "The full 20dB evidence is insufficient for wider LLR-only expansion. Stop at this gate and report a limited/negative result."])
    elif decision == "GO_EXPAND_LLR_ONLY":
        lines.extend(["", "## Conclusion", "", "The full 20dB evidence supports expanding LLR-only validation. This still does not justify mainline migration."])
    else:
        lines.extend(["", "## Conclusion", "", "The full 20dB evidence supports wider validation but not broad application or mainline migration."])
    write_text(out_path, "\n".join(lines))
    return decision


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Route B-lite full 20dB fixed-order LLR-only validation.")
    ap.add_argument("--audit-dir", default="results/_tmp_routeB_lite_error_audit")
    ap.add_argument("--routeA-cross-loss-dir", default="results/_tmp_routeA_correctness_formal_stageD_cross_loss")
    ap.add_argument("--output-dir", default="results/_tmp_routeB_lite_full20dB_llr_ablation")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--verification-tag-bits", type=int, default=32)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    audit_dir = Path(args.audit_dir)
    routea_dir = Path(args.routeA_cross_loss_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = _load_full20_manifest(routea_dir)
    channel_model = pd.read_csv(audit_dir / "routeB_channel_model_layer_table.csv")
    runtime_rows: list[dict[str, object]] = []
    for model_tag, subdir in (("bsc_legacy", "baseline_bsc_legacy"), ("asym_binary_v1", "ablation_asym_binary_v1")):
        runtime_rows.extend(
            _run_with_fallback(
                model_root=out_dir / subdir,
                model_tag=model_tag,
                routea_dir=routea_dir,
                audit_dir=audit_dir,
                workers=int(args.workers),
                verification_tag_bits=int(args.verification_tag_bits),
                overwrite=bool(args.overwrite),
            )
        )
    runtime = pd.DataFrame(runtime_rows)
    runtime.to_csv(out_dir / "routeB_full20dB_runtime.csv", index=False)
    runtime_success = runtime[runtime["attempt_status"].eq("success")].copy()
    old_point, old_master, old_block = _load_model_outputs(out_dir / "baseline_bsc_legacy", [LOSS_DB])
    new_point, new_master, new_block = _load_model_outputs(out_dir / "ablation_asym_binary_v1", [LOSS_DB])
    compare = _build_compare(
        manifest=manifest,
        old_point=old_point,
        old_master=old_master,
        old_block=old_block,
        old_runtime=runtime_success[runtime_success["model_tag"].eq("bsc_legacy")],
        new_point=new_point,
        new_master=new_master,
        new_block=new_block,
        new_runtime=runtime_success[runtime_success["model_tag"].eq("asym_binary_v1")],
        channel_model=channel_model,
    )
    if len(compare) != EXPECTED_POINTS:
        raise SystemExit(f"compare row count mismatch: {len(compare)} != {EXPECTED_POINTS}")
    compare.to_csv(out_dir / "routeB_full20dB_compare.csv", index=False)
    _write_point_notes(compare, out_dir / "routeB_full20dB_point_notes.csv")
    decision = _write_summary(compare, runtime, out_dir / "routeB_full20dB_summary.md")
    write_text(out_dir / "routeB_full20dB_decision.txt", decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
