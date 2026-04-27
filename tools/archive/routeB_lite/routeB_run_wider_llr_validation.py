#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from _longrun_common import candidate_dir_for_loss, python_tool, write_text
from routeB_run_b3_subset_ablation import _build_compare, _load_model_outputs, _point_id, _write_subset_index


KEY = ["loss_db", "dimension", "bin_width_ps"]


def _parse_ints(text: str) -> list[int]:
    return [int(x.strip()) for x in str(text).split(",") if x.strip()]


def _load_manifest(routea_dir: Path, losses: list[int], bws: list[int]) -> pd.DataFrame:
    frames = []
    for loss in losses:
        stage1 = routea_dir / f"loss_{int(loss)}dB" / "stage1_actual_ir"
        point = pd.read_csv(stage1 / "replay_index_point_table.csv")
        if "point_id" not in point.columns:
            point["point_id"] = point.apply(_point_id, axis=1)
        point = point[point["loss_db"].astype(int).eq(int(loss)) & point["bin_width_ps"].astype(int).isin(bws)].copy()
        frames.append(point[KEY + ["point_id"]].drop_duplicates())
    out = pd.concat(frames, ignore_index=True).sort_values(KEY).reset_index(drop=True)
    if out.empty:
        raise SystemExit("wider validation manifest is empty")
    return out


def _validate(stage1: Path, stage2: Path, expected_points: int) -> None:
    point = pd.read_csv(stage1 / "actual_ir_point_table.csv")
    master = pd.read_csv(stage2 / "security_calibrated_master_table.csv")
    if len(point) != expected_points:
        raise RuntimeError(f"point table row count mismatch: {len(point)} != {expected_points}")
    if len(master) != expected_points:
        raise RuntimeError(f"master table row count mismatch: {len(master)} != {expected_points}")


def _run_loss_attempt(
    *,
    model_root: Path,
    loss: int,
    manifest_loss: pd.DataFrame,
    routea_dir: Path,
    audit_dir: Path,
    workers: int,
    verification_tag_bits: int,
    overwrite: bool,
) -> dict[str, object]:
    loss_root = model_root / f"loss_{int(loss)}dB"
    index_dir = loss_root / "replay_index_subset"
    stage1 = loss_root / "stage1_actual_ir"
    stage2 = loss_root / "stage2_security"
    _write_subset_index(src_stage1=routea_dir / f"loss_{int(loss)}dB" / "stage1_actual_ir", manifest_loss=manifest_loss, out_dir=index_dir)
    start = time.perf_counter()
    args = [
        "--candidate-dir",
        str(candidate_dir_for_loss(loss)),
        "--replay-index-dir",
        str(index_dir),
        "--output-dir",
        str(stage1),
        "--shards",
        str(len(manifest_loss)),
        "--workers",
        str(int(workers)),
        "--verification-tag-bits",
        str(int(verification_tag_bits)),
        "--channel-model-tag",
        "asym_binary_v1",
        "--channel-model-table",
        str(audit_dir / "routeB_channel_model_layer_table.csv"),
    ]
    if overwrite:
        args.append("--overwrite")
    python_tool("routeA_run_formal_replay_shards.py", *args)
    stage1_seconds = time.perf_counter() - start
    start = time.perf_counter()
    stage2_args = [
        "--candidate-dir",
        str(candidate_dir_for_loss(loss)),
        "--stage1-dir",
        str(stage1),
        "--output-dir",
        str(stage2),
    ]
    if overwrite:
        stage2_args.append("--overwrite")
    python_tool("routeA_build_formal_stageC.py", *stage2_args)
    stage2_seconds = time.perf_counter() - start
    _validate(stage1, stage2, len(manifest_loss))
    return {
        "model_tag": "asym_binary_v1",
        "loss_db": int(loss),
        "point_count": int(len(manifest_loss)),
        "workers": int(workers),
        "attempt_status": "success",
        "attempt_error": "",
        "stage1_seconds": float(stage1_seconds),
        "stage2_seconds": float(stage2_seconds),
        "runtime_seconds_total": float(stage1_seconds + stage2_seconds),
        "runtime_seconds_per_point": float((stage1_seconds + stage2_seconds) / max(1, len(manifest_loss))),
        "stage1_dir": str(stage1),
        "stage2_dir": str(stage2),
    }


def _run_loss_with_fallback(**kwargs: object) -> list[dict[str, object]]:
    workers = int(kwargs.pop("workers"))
    overwrite = bool(kwargs.pop("overwrite"))
    candidates = []
    for w in (workers, 2, 1):
        if w > 0 and w not in candidates:
            candidates.append(w)
    rows = []
    for idx, worker_count in enumerate(candidates):
        try:
            row = _run_loss_attempt(workers=worker_count, overwrite=True if idx > 0 else overwrite, **kwargs)
            row["attempt_index"] = idx + 1
            rows.append(row)
            return rows
        except Exception as exc:
            rows.append(
                {
                    "model_tag": "asym_binary_v1",
                    "loss_db": int(kwargs["loss"]),
                    "point_count": int(len(kwargs["manifest_loss"])),
                    "workers": int(worker_count),
                    "attempt_index": idx + 1,
                    "attempt_status": "failed",
                    "attempt_error": str(exc),
                    "stage1_seconds": np.nan,
                    "stage2_seconds": np.nan,
                    "runtime_seconds_total": np.nan,
                    "runtime_seconds_per_point": np.nan,
                    "stage1_dir": "",
                    "stage2_dir": "",
                }
            )
    raise SystemExit(f"all worker attempts failed for loss {kwargs['loss']}")


def _num(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce") if col in df.columns else pd.Series(np.nan, index=df.index)


def _write_summary(compare: pd.DataFrame, runtime: pd.DataFrame, out_path: Path, bws: list[int]) -> str:
    n = len(compare)
    improve = int(compare["improvement_flag"].sum())
    degrade = int(compare["degradation_flag"].sum())
    tie = n - improve - degrade
    delta_fail = _num(compare, "delta_decoder_fail_rate_oracle")
    delta_success = _num(compare, "delta_block_success")
    delta_pie = _num(compare, "delta_PIE_secure_actual_ir")
    delta_skr = _num(compare, "delta_SKR_secure_actual_ir_bps")
    delta_eps = (_num(compare, "epsilon_EC_bound_new") - _num(compare, "epsilon_EC_bound_old")).abs()
    delta_lambda = (_num(compare, "lambda_ver_bits_actual_new") - _num(compare, "lambda_ver_bits_actual_old")).abs()
    delta_leak = _num(compare, "delta_leak_EC_actual_bits").abs()
    fallback_points = int(compare["model_fallback_tag"].astype(str).str.contains("invalid|ineligible|missing", case=False, na=False).sum())
    correctness_same = bool(delta_eps.fillna(0).le(1e-18).all() and delta_lambda.fillna(0).le(0).all())
    per_loss = compare.groupby("loss_db").agg(
        points=("point_id", "size"),
        improve=("improvement_flag", "sum"),
        degrade=("degradation_flag", "sum"),
        mean_delta_fail=("delta_decoder_fail_rate_oracle", "mean"),
        mean_delta_skr=("delta_SKR_secure_actual_ir_bps", "mean"),
    )
    stable_losses = int(((per_loss["improve"] > per_loss["degrade"]) & (per_loss["mean_delta_fail"] < 0)).sum())
    if correctness_same and improve > degrade and stable_losses >= 3 and delta_fail.mean() < 0 and (delta_pie.mean() > 0 or delta_skr.mean() > 0):
        decision = "GO_WIDER_VALIDATION_BUT_NOT_MAINLINE"
    else:
        decision = "STOP_AT_WIDER_VALIDATION"
    lines = [
        "# Route B-lite Wider Band-limited LLR-only Validation Summary",
        "",
        f"- selected_bin_width_ps: {','.join(str(x) for x in bws)}",
        f"- point_count: {n}",
        f"- improvement_points: {improve}",
        f"- degradation_points: {degrade}",
        f"- tie_points: {tie}",
        f"- stable_loss_count: {stable_losses}",
        f"- mean_delta_decoder_fail_rate_oracle: {float(delta_fail.mean())}",
        f"- median_delta_decoder_fail_rate_oracle: {float(delta_fail.median())}",
        f"- mean_delta_block_success: {float(delta_success.mean())}",
        f"- mean_delta_PIE_secure_actual_ir: {float(delta_pie.mean())}",
        f"- mean_delta_SKR_secure_actual_ir_bps: {float(delta_skr.mean())}",
        f"- max_abs_delta_epsilon_EC_bound: {float(delta_eps.max())}",
        f"- max_abs_delta_lambda_ver_bits_actual: {float(delta_lambda.max())}",
        f"- max_abs_delta_leak_EC_actual_bits: {float(delta_leak.max())}",
        f"- fallback_points: {fallback_points}",
        f"- correctness_same_flag: {int(correctness_same)}",
        f"- decision: {decision}",
        "",
        "## Per Loss",
        "",
        "```text",
        per_loss.reset_index().to_string(index=False),
        "```",
        "",
        "## Boundary",
        "",
        "This is band-limited cross-loss LLR-only validation. It is not mainline migration and not channel-aware Polar construction.",
    ]
    write_text(out_path, "\n".join(lines))
    return decision


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Route B-lite wider band-limited LLR-only validation.")
    ap.add_argument("--audit-dir", default="results/_tmp_routeB_lite_error_audit")
    ap.add_argument("--routeA-cross-loss-dir", default="results/_tmp_routeA_correctness_formal_stageD_cross_loss")
    ap.add_argument("--output-dir", default="results/_tmp_routeB_lite_wider_llr_validation")
    ap.add_argument("--losses", default="6,10,16,20")
    ap.add_argument("--bin-widths", default="50,180,200")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--verification-tag-bits", type=int, default=32)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    audit_dir = Path(args.audit_dir)
    routea_dir = Path(args.routeA_cross_loss_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    losses = _parse_ints(args.losses)
    bws = _parse_ints(args.bin_widths)
    manifest = _load_manifest(routea_dir, losses, bws)
    manifest.to_csv(out_dir / "routeB_wider_llr_manifest.csv", index=False)
    runtime_rows: list[dict[str, object]] = []
    model_root = out_dir / "ablation_asym_binary_v1"
    for loss in losses:
        manifest_loss = manifest[manifest["loss_db"].astype(int).eq(int(loss))].copy()
        runtime_rows.extend(
            _run_loss_with_fallback(
                model_root=model_root,
                loss=int(loss),
                manifest_loss=manifest_loss,
                routea_dir=routea_dir,
                audit_dir=audit_dir,
                workers=int(args.workers),
                verification_tag_bits=int(args.verification_tag_bits),
                overwrite=bool(args.overwrite),
            )
        )
    runtime = pd.DataFrame(runtime_rows)
    runtime.to_csv(out_dir / "routeB_wider_llr_runtime.csv", index=False)
    old_point, old_master, old_block = _load_model_outputs(routea_dir, losses)
    new_point, new_master, new_block = _load_model_outputs(model_root, losses)
    old_point = old_point.merge(manifest[["point_id"]], on="point_id", how="inner")
    old_master = old_master.merge(manifest[["point_id"]], on="point_id", how="inner")
    old_block = old_block.merge(manifest[["point_id"]], on="point_id", how="inner")
    channel_model = pd.read_csv(audit_dir / "routeB_channel_model_layer_table.csv")
    old_runtime = pd.DataFrame({"loss_db": losses, "runtime_seconds_per_point": [np.nan] * len(losses)})
    runtime_success = runtime[runtime["attempt_status"].eq("success")]
    compare = _build_compare(
        manifest=manifest,
        old_point=old_point,
        old_master=old_master,
        old_block=old_block,
        old_runtime=old_runtime,
        new_point=new_point,
        new_master=new_master,
        new_block=new_block,
        new_runtime=runtime_success,
        channel_model=channel_model,
    )
    compare.to_csv(out_dir / "routeB_wider_llr_compare.csv", index=False)
    notes = compare[["loss_db", "dimension", "bin_width_ps", "point_id", "model_fallback_tag", "improvement_flag", "degradation_flag"]].copy()
    notes["note"] = np.where(
        notes["model_fallback_tag"].astype(str).str.contains("invalid|ineligible|missing", case=False, na=False),
        "asym_binary layer fallback occurred; inspect block table before interpreting this point",
        "band-limited LLR-only validation under unchanged correctness",
    )
    notes.to_csv(out_dir / "routeB_wider_llr_point_notes.csv", index=False)
    decision = _write_summary(compare, runtime, out_dir / "routeB_wider_llr_summary.md", bws)
    write_text(out_dir / "routeB_wider_llr_decision.txt", decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
