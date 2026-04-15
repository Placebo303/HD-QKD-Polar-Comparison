#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _security_round_common import write_summary


def main() -> int:
    ap = argparse.ArgumentParser(description="Select Route B-lite very-small A/B replay subset.")
    ap.add_argument("--audit-dir", default="results/_tmp_routeB_lite_error_audit")
    ap.add_argument("--routeA-cross-loss-master", default="results/_tmp_routeA_correctness_formal_stageD_cross_loss/cross_loss_security_master_table.csv")
    ap.add_argument("--output-dir", default="")
    ap.add_argument("--target-size", type=int, default=12)
    args = ap.parse_args()

    audit_dir = Path(args.audit_dir)
    output_dir = Path(args.output_dir) if str(args.output_dir).strip() else audit_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    model_point = pd.read_csv(audit_dir / "routeB_channel_model_point_table.csv")
    diagnosis = pd.read_csv(audit_dir / "routeB_model_diagnosis_table.csv")
    master = pd.read_csv(Path(args.routeA_cross_loss_master))
    if "point_id" not in master.columns:
        master["point_id"] = master.apply(lambda r: f"loss{int(r['loss_db'])}_d{int(r['dimension'])}_bw{int(r['bin_width_ps'])}", axis=1)

    df = model_point.merge(
        diagnosis[["point_id", "max_asymmetry_abs_gap", "mean_asymmetry_abs_gap", "eligible_B3_layers", "clipped_layer_count"]],
        on="point_id",
        how="left",
        suffixes=("", "_diag"),
    ).merge(
        master[["point_id", "decoder_fail_rate_oracle", "leak_EC_actual_bits", "epsilon_EC_bound", "PIE_secure_actual_ir", "SKR_secure_actual_ir_bps"]],
        on="point_id",
        how="left",
        suffixes=("", "_routeA"),
    )
    df["decoder_fail_rate_for_rank"] = pd.to_numeric(df["decoder_fail_rate_oracle_routeA"], errors="coerce").combine_first(
        pd.to_numeric(df.get("decoder_fail_rate_oracle"), errors="coerce")
    )
    df["loss_median_decoder_fail"] = df.groupby("loss_db")["decoder_fail_rate_for_rank"].transform("median")
    eligible = df[
        (pd.to_numeric(df["eligible_B3_model_layers"], errors="coerce") > 0)
        & (pd.to_numeric(df["clipped_layer_count"], errors="coerce").fillna(0) == 0)
        & (
            (pd.to_numeric(df["asym_binary_candidate_flag"], errors="coerce").fillna(0) == 1)
            | (pd.to_numeric(df["offset_like_candidate_flag"], errors="coerce").fillna(0) == 1)
        )
        & (pd.to_numeric(df["decoder_fail_rate_for_rank"], errors="coerce") >= pd.to_numeric(df["loss_median_decoder_fail"], errors="coerce"))
    ].copy()
    eligible["routeB_subset_score"] = (
        pd.to_numeric(eligible["max_asymmetry_abs_gap"], errors="coerce").fillna(0) * 100.0
        + pd.to_numeric(eligible["decoder_fail_rate_for_rank"], errors="coerce").fillna(0) * 10.0
        + pd.to_numeric(eligible["mean_capacity_delta_uniform_asym_minus_bsc"], errors="coerce").fillna(0) * 5.0
        + pd.to_numeric(eligible["offset_like_candidate_flag"], errors="coerce").fillna(0)
    )

    selected = []
    target_size = max(1, int(args.target_size))
    per_loss_first = eligible.sort_values("routeB_subset_score", ascending=False).groupby("loss_db", as_index=False).head(1)
    selected.append(per_loss_first)
    remaining_slots = max(0, target_size - len(per_loss_first))
    already = set(per_loss_first["point_id"].astype(str))
    rest = eligible[~eligible["point_id"].astype(str).isin(already)].sort_values("routeB_subset_score", ascending=False).head(remaining_slots)
    selected.append(rest)
    manifest = pd.concat(selected, ignore_index=True) if selected else pd.DataFrame()
    manifest = manifest.sort_values(["loss_db", "routeB_subset_score"], ascending=[True, False]).reset_index(drop=True)
    manifest["ablation_plan"] = "llr_only_first_then_llr_kadapt_if_gate_passes"
    manifest["baseline_tag"] = "routeA_formal_bsc_replay"
    manifest["b3_boundary_tag"] = "fixed_polar_weight_order_ablation_not_channel_aware_construction"
    keep = [
        "loss_db", "dimension", "bin_width_ps", "point_id", "routeB_subset_score",
        "eligible_B3_model_layers", "max_asymmetry_abs_gap", "mean_capacity_delta_uniform_asym_minus_bsc",
        "decoder_fail_rate_for_rank", "loss_median_decoder_fail", "asym_binary_candidate_flag",
        "offset_like_candidate_flag", "leak_EC_actual_bits", "epsilon_EC_bound",
        "PIE_secure_actual_ir", "SKR_secure_actual_ir_bps", "ablation_plan",
        "baseline_tag", "b3_boundary_tag",
    ]
    manifest[[c for c in keep if c in manifest.columns]].to_csv(output_dir / "routeB_ab_subset_manifest.csv", index=False)

    summary = [
        f"audit_dir: {audit_dir}",
        f"eligible_candidate_points: {len(eligible)}",
        f"selected_points: {len(manifest)}",
        f"target_size: {target_size}",
        f"selected_losses: {sorted(manifest['loss_db'].dropna().astype(int).unique().tolist()) if not manifest.empty else []}",
        "gate_rule: run LLR-only first; do not run LLR+k adaptation unless decoder fail improves on the very-small subset.",
        "boundary: selected subset is for fixed-order model-aware ablation only; it is not channel-aware Polar construction.",
    ]
    missing_losses = sorted(set([6, 10, 16, 20]) - set(manifest["loss_db"].dropna().astype(int).unique().tolist())) if not manifest.empty else [6, 10, 16, 20]
    if missing_losses:
        summary.append(f"losses_without_selected_candidate: {missing_losses}")
    write_summary(output_dir / "routeB_ab_subset_summary.txt", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
