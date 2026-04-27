#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from _longrun_common import candidate_dir_for_loss, csv_read, python_tool, write_text


KEY = ["loss_db", "dimension", "bin_width_ps"]


def _point_id(row: pd.Series) -> str:
    return f"loss{int(row['loss_db'])}_d{int(row['dimension'])}_bw{int(row['bin_width_ps'])}"


def _routea_stage1(loss_db: int, routea_dir: Path) -> Path:
    return routea_dir / f"loss_{int(loss_db)}dB" / "stage1_actual_ir"


def _write_subset_index(*, src_stage1: Path, manifest_loss: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    point = pd.read_csv(src_stage1 / "replay_index_point_table.csv")
    layer = pd.read_csv(src_stage1 / "replay_index_layer_table.csv")
    pids = set(manifest_loss["point_id"].astype(str))
    point = point[point["point_id"].astype(str).isin(pids)].copy()
    layer = layer[layer["point_id"].astype(str).isin(pids)].copy()
    point.to_csv(out_dir / "replay_index_point_table.csv", index=False)
    layer.to_csv(out_dir / "replay_index_layer_table.csv", index=False)


def _run_model_loss(
    *,
    model_root: Path,
    model_tag: str,
    loss_db: int,
    manifest_loss: pd.DataFrame,
    routea_dir: Path,
    channel_model_table: Path,
    workers: int,
) -> dict[str, object]:
    candidate_dir = candidate_dir_for_loss(loss_db)
    loss_root = model_root / f"loss_{int(loss_db)}dB"
    subset_index = loss_root / "replay_index_subset"
    stage1 = loss_root / "stage1_actual_ir"
    stage2 = loss_root / "stage2_security"
    _write_subset_index(src_stage1=_routea_stage1(loss_db, routea_dir), manifest_loss=manifest_loss, out_dir=subset_index)
    start = time.perf_counter()
    python_tool(
        "routeA_run_formal_replay_shards.py",
        "--candidate-dir",
        str(candidate_dir),
        "--replay-index-dir",
        str(subset_index),
        "--output-dir",
        str(stage1),
        "--shards",
        str(len(manifest_loss)),
        "--workers",
        str(int(workers)),
        "--verification-tag-bits",
        "32",
        "--channel-model-tag",
        model_tag,
        *(["--channel-model-table", str(channel_model_table)] if model_tag == "asym_binary_v1" else []),
        "--overwrite",
    )
    stage1_seconds = time.perf_counter() - start
    start = time.perf_counter()
    python_tool(
        "routeA_build_formal_stageC.py",
        "--candidate-dir",
        str(candidate_dir),
        "--stage1-dir",
        str(stage1),
        "--output-dir",
        str(stage2),
        "--overwrite",
    )
    stage2_seconds = time.perf_counter() - start
    return {
        "model_tag": model_tag,
        "loss_db": int(loss_db),
        "point_count": int(len(manifest_loss)),
        "stage1_seconds": float(stage1_seconds),
        "stage2_seconds": float(stage2_seconds),
        "runtime_seconds_total": float(stage1_seconds + stage2_seconds),
        "runtime_seconds_per_point": float((stage1_seconds + stage2_seconds) / max(1, len(manifest_loss))),
        "stage1_dir": str(stage1),
        "stage2_dir": str(stage2),
    }


def _load_model_outputs(model_root: Path, losses: list[int]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    points = []
    masters = []
    blocks = []
    for loss in losses:
        loss_root = model_root / f"loss_{int(loss)}dB"
        stage1 = loss_root / "stage1_actual_ir"
        stage2 = loss_root / "stage2_security"
        pt = pd.read_csv(stage1 / "actual_ir_point_table.csv")
        ms = pd.read_csv(stage2 / "security_calibrated_master_table.csv")
        bl = pd.read_csv(stage1 / "actual_ir_block_table.csv")
        for frame in (pt, ms, bl):
            if "point_id" not in frame.columns:
                frame["point_id"] = frame.apply(_point_id, axis=1)
        points.append(pt)
        masters.append(ms)
        blocks.append(bl)
    return pd.concat(points, ignore_index=True), pd.concat(masters, ignore_index=True), pd.concat(blocks, ignore_index=True)


def _block_model_summary(block: pd.DataFrame) -> pd.DataFrame:
    ok = block[block["replay_status"].astype(str).str.startswith("ok")].copy()
    rows = []
    for pid, grp in ok.groupby("point_id"):
        rows.append(
            {
                "point_id": pid,
                "decoder_mode_used": ";".join(sorted(str(x) for x in grp.get("decoder_mode_used", pd.Series(dtype=str)).dropna().unique() if str(x).strip())),
                "channel_model_tag": ";".join(sorted(str(x) for x in grp.get("channel_model_tag", pd.Series(dtype=str)).dropna().unique() if str(x).strip())),
                "model_fallback_tag": ";".join(sorted(str(x) for x in grp.get("model_fallback_tag", pd.Series(dtype=str)).dropna().unique() if str(x).strip())),
            }
        )
    return pd.DataFrame(rows)


def _pick_num(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce") if col in df.columns else pd.Series([np.nan] * len(df), index=df.index)


def _build_compare(
    *,
    manifest: pd.DataFrame,
    old_point: pd.DataFrame,
    old_master: pd.DataFrame,
    old_block: pd.DataFrame,
    old_runtime: pd.DataFrame,
    new_point: pd.DataFrame,
    new_master: pd.DataFrame,
    new_block: pd.DataFrame,
    new_runtime: pd.DataFrame,
    channel_model: pd.DataFrame,
) -> pd.DataFrame:
    old_block_sum = _block_model_summary(old_block).add_suffix("_old").rename(columns={"point_id_old": "point_id"})
    new_block_sum = _block_model_summary(new_block).add_suffix("_new").rename(columns={"point_id_new": "point_id"})
    old = old_point.merge(old_master, on=KEY + ["point_id"], how="left", suffixes=("_point", ""))
    new = new_point.merge(new_master, on=KEY + ["point_id"], how="left", suffixes=("_point", ""))
    old = old.merge(old_block_sum, on="point_id", how="left")
    new = new.merge(new_block_sum, on="point_id", how="left")
    old_rt = old_runtime[["loss_db", "runtime_seconds_per_point"]].rename(columns={"runtime_seconds_per_point": "runtime_seconds_old"})
    new_rt = new_runtime[["loss_db", "runtime_seconds_per_point"]].rename(columns={"runtime_seconds_per_point": "runtime_seconds_new"})
    cm = channel_model.groupby("point_id", as_index=False).agg(
        p01_model=("p01_model", "mean"),
        p10_model=("p10_model", "mean"),
        llr_b0=("llr_b0", "mean"),
        llr_b1=("llr_b1", "mean"),
    )
    merged = manifest[KEY + ["point_id"]].merge(old.add_suffix("_old"), left_on=KEY + ["point_id"], right_on=[f"{c}_old" for c in KEY] + ["point_id_old"], how="left")
    merged = merged.merge(new.add_suffix("_new"), left_on=KEY + ["point_id"], right_on=[f"{c}_new" for c in KEY] + ["point_id_new"], how="left")
    merged = merged.merge(old_rt, on="loss_db", how="left").merge(new_rt, on="loss_db", how="left").merge(cm, on="point_id", how="left")
    out = manifest[KEY + ["point_id"]].copy()
    out["model_tag_old"] = "bsc_legacy"
    out["model_tag_new"] = "asym_binary_v1"
    out["channel_model_tag"] = merged.get("channel_model_tag_new", "missing")
    out["model_fallback_tag"] = merged.get("model_fallback_tag_new", "missing")
    for c in ("p01_model", "p10_model", "llr_b0", "llr_b1"):
        out[c] = merged[c]
    out["decoder_mode_used_old"] = merged.get("decoder_mode_used_old", "")
    out["decoder_mode_used_new"] = merged.get("decoder_mode_used_new", "")
    out["block_success_rate_old"] = _pick_num(merged, "block_success_rate_old")
    out["block_success_rate_new"] = _pick_num(merged, "block_success_rate_new")
    out["decoder_fail_rate_oracle_old"] = _pick_num(merged, "decoder_fail_rate_oracle_old")
    out["decoder_fail_rate_oracle_new"] = _pick_num(merged, "decoder_fail_rate_oracle_new")
    old_total = _pick_num(merged, "total_leak_ec_bits_old")
    new_total = _pick_num(merged, "total_leak_ec_bits_new")
    out["syndrome_bits_old"] = old_total - _pick_num(merged, "lambda_ver_bits_actual_old")
    out["syndrome_bits_new"] = new_total - _pick_num(merged, "lambda_ver_bits_actual_new")
    out["lambda_ver_bits_actual_old"] = _pick_num(merged, "lambda_ver_bits_actual_old")
    out["lambda_ver_bits_actual_new"] = _pick_num(merged, "lambda_ver_bits_actual_new")
    for c in ("leak_EC_actual_bits", "epsilon_EC_bound", "PIE_secure_actual_ir", "SKR_secure_actual_ir_bps"):
        out[f"{c}_old"] = _pick_num(merged, f"{c}_old")
        out[f"{c}_new"] = _pick_num(merged, f"{c}_new")
    out["runtime_seconds_old"] = merged["runtime_seconds_old"]
    out["runtime_seconds_new"] = merged["runtime_seconds_new"]
    out["delta_block_success"] = out["block_success_rate_new"] - out["block_success_rate_old"]
    out["delta_decoder_fail_rate_oracle"] = out["decoder_fail_rate_oracle_new"] - out["decoder_fail_rate_oracle_old"]
    out["delta_leak_EC_actual_bits"] = out["leak_EC_actual_bits_new"] - out["leak_EC_actual_bits_old"]
    out["delta_PIE_secure_actual_ir"] = out["PIE_secure_actual_ir_new"] - out["PIE_secure_actual_ir_old"]
    out["delta_SKR_secure_actual_ir_bps"] = out["SKR_secure_actual_ir_bps_new"] - out["SKR_secure_actual_ir_bps_old"]
    out["improvement_flag"] = ((out["delta_decoder_fail_rate_oracle"] < -1e-12) & (out["delta_block_success"] > 1e-12) & (out["delta_SKR_secure_actual_ir_bps"] >= -1e-9)).astype(int)
    out["degradation_flag"] = ((out["delta_decoder_fail_rate_oracle"] > 1e-12) | (out["delta_block_success"] < -1e-12) | (out["delta_SKR_secure_actual_ir_bps"] < -1e-9)).astype(int)
    return out


def _write_summary(compare: pd.DataFrame, runtime: pd.DataFrame, out_path: Path) -> None:
    n = len(compare)
    improve = int(compare["improvement_flag"].sum())
    degrade = int(compare["degradation_flag"].sum())
    mean_delta_fail = pd.to_numeric(compare["delta_decoder_fail_rate_oracle"], errors="coerce").mean()
    mean_delta_success = pd.to_numeric(compare["delta_block_success"], errors="coerce").mean()
    mean_delta_pie = pd.to_numeric(compare["delta_PIE_secure_actual_ir"], errors="coerce").mean()
    mean_delta_skr = pd.to_numeric(compare["delta_SKR_secure_actual_ir_bps"], errors="coerce").mean()
    runtime_ratio = (pd.to_numeric(compare["runtime_seconds_new"], errors="coerce").mean() / pd.to_numeric(compare["runtime_seconds_old"], errors="coerce").mean()) if pd.to_numeric(compare["runtime_seconds_old"], errors="coerce").mean() > 0 else np.nan
    correctness_same = bool((pd.to_numeric(compare["epsilon_EC_bound_new"], errors="coerce") - pd.to_numeric(compare["epsilon_EC_bound_old"], errors="coerce")).abs().fillna(0).le(1e-18).all())
    go = (
        improve > n / 2
        and mean_delta_fail < 0
        and mean_delta_success > 0
        and (mean_delta_pie > 0 or mean_delta_skr > 0)
        and (not np.isfinite(runtime_ratio) or runtime_ratio <= 1.25)
        and correctness_same
    )
    decision = "GO_FULL_20DB" if go else "STOP_NEGATIVE_OR_LIMITED"
    lines = [
        "# Route B-lite B3 Very-Small Subset Summary",
        "",
        f"- selected_points: {n}",
        f"- improvement_points: {improve}",
        f"- degradation_points: {degrade}",
        f"- mean_delta_decoder_fail_rate_oracle: {mean_delta_fail}",
        f"- mean_delta_block_success: {mean_delta_success}",
        f"- mean_delta_PIE_secure_actual_ir: {mean_delta_pie}",
        f"- mean_delta_SKR_secure_actual_ir_bps: {mean_delta_skr}",
        f"- runtime_ratio_new_over_old_mean: {runtime_ratio}",
        f"- correctness_same_epsilon_EC_bound: {int(correctness_same)}",
        f"- stop_go_decision: {decision}",
        "",
        "## Answers",
        "",
        "1. Stable improvement: " + ("yes" if go else "no"),
        "2. Improvement channel: " + ("decoder/block/security metrics moved consistently" if go else "no stable system-level improvement across decoder fail, block success, PIE, and SKR"),
        f"3. Minority-only behavior: {'yes' if improve > 0 and improve <= n / 2 else 'no'}",
        f"4. Correctness columns same-protocol: {'yes' if correctness_same else 'no'}; verification remains `uhv1_per_block` and epsilon_EC_bound is still the universal-hash union bound.",
        f"5. Recommendation: {decision}",
        "",
        "## Boundary",
        "",
        "This experiment is LLR-only with fixed `k_best`, fixed frozen ordering, and unchanged universal-hash verification. It is not channel-aware Polar construction.",
    ]
    if not go:
        lines.extend(
            [
                "",
                "## Conclusion",
                "",
                "In the current 12-point very-small subset, `asym_binary_v1` LLR-only ablation did not show stable, systematic replay gain. Combined with B1/B2, this should stop at a negative/limited result unless the candidate set or model scope changes.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## Conclusion",
                "",
                "The subset shows local and reproducible improvement under the fixed-order LLR-only ablation. The next step may be full 20 dB validation only; this does not justify immediate cross-loss expansion or mainline migration.",
            ]
        )
    write_text(out_path, "\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Route B-lite B3 very-small subset LLR-only ablation.")
    ap.add_argument("--audit-dir", default="results/_tmp_routeB_lite_error_audit")
    ap.add_argument("--routeA-cross-loss-dir", default="results/_tmp_routeA_correctness_formal_stageD_cross_loss")
    ap.add_argument("--output-dir", default="results/_tmp_routeB_lite_b3_subset_ablation")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    audit_dir = Path(args.audit_dir)
    routea_dir = Path(args.routeA_cross_loss_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(audit_dir / "routeB_ab_subset_manifest.csv")
    channel_model = pd.read_csv(audit_dir / "routeB_channel_model_layer_table.csv")
    losses = sorted(manifest["loss_db"].dropna().astype(int).unique().tolist())
    runtime_rows: list[dict[str, object]] = []
    for model_tag, model_subdir in (("bsc_legacy", "baseline_bsc_legacy"), ("asym_binary_v1", "ablation_asym_binary_v1")):
        model_root = out_dir / model_subdir
        for loss in losses:
            mloss = manifest[manifest["loss_db"].astype(int).eq(int(loss))].copy()
            runtime_rows.append(
                _run_model_loss(
                    model_root=model_root,
                    model_tag=model_tag,
                    loss_db=int(loss),
                    manifest_loss=mloss,
                    routea_dir=routea_dir,
                    channel_model_table=audit_dir / "routeB_channel_model_layer_table.csv",
                    workers=int(args.workers),
                )
            )

    runtime = pd.DataFrame(runtime_rows)
    runtime.to_csv(out_dir / "routeB_b3_subset_runtime.csv", index=False)
    old_point, old_master, old_block = _load_model_outputs(out_dir / "baseline_bsc_legacy", losses)
    new_point, new_master, new_block = _load_model_outputs(out_dir / "ablation_asym_binary_v1", losses)
    compare = _build_compare(
        manifest=manifest,
        old_point=old_point,
        old_master=old_master,
        old_block=old_block,
        old_runtime=runtime[runtime["model_tag"].eq("bsc_legacy")],
        new_point=new_point,
        new_master=new_master,
        new_block=new_block,
        new_runtime=runtime[runtime["model_tag"].eq("asym_binary_v1")],
        channel_model=channel_model,
    )
    compare.to_csv(out_dir / "routeB_b3_subset_compare.csv", index=False)
    notes = compare[["loss_db", "dimension", "bin_width_ps", "point_id", "model_fallback_tag", "improvement_flag", "degradation_flag"]].copy()
    notes["note"] = np.where(
        notes["model_fallback_tag"].astype(str).str.contains("invalid|ineligible|missing", case=False, na=False),
        "asym_binary layer fallback occurred; inspect block table before interpreting this point",
        "LLR-only asym-binary evaluated with fixed k/order and unchanged correctness",
    )
    notes.to_csv(out_dir / "routeB_b3_subset_point_notes.csv", index=False)
    _write_summary(compare, runtime, out_dir / "routeB_b3_subset_summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
