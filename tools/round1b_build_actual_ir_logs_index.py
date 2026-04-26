#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from _security_calibrated_common import load_candidate_frame
from _security_round_common import REPO_ROOT, ensure_output_dir, point_id, write_summary


def _default_replay_dir() -> Path:
    return REPO_ROOT / "results" / "_tmp_round1b_actual_ir"


def _default_candidate_dir() -> Path:
    return REPO_ROOT / "results" / "e2e_20dB_fullgrid_pairing_v2_candidate_t15"


def main() -> int:
    ap = argparse.ArgumentParser(description="Aggregate actual IR replay block logs into point-level audit tables.")
    ap.add_argument("--input-dirs", nargs="*", default=[])
    ap.add_argument("--candidate-dirs", nargs="*", default=[])
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    replay_dirs = [Path(p) for p in args.input_dirs] if args.input_dirs else [_default_replay_dir()]
    candidate_dirs = [Path(p) for p in args.candidate_dirs] if args.candidate_dirs else [_default_candidate_dir()]
    output_dir = Path(args.output_dir)
    same_in_out = any(output_dir.resolve() == p.resolve() for p in replay_dirs if p.exists())
    if bool(args.overwrite) and not same_in_out:
        ensure_output_dir(output_dir, overwrite=True)
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    block_frames = []
    for replay_dir in replay_dirs:
        block_frames.append(pd.read_csv(replay_dir / "actual_ir_block_table.csv"))
    block_df = pd.concat(block_frames, ignore_index=True)
    block_df["loss_db"] = pd.to_numeric(block_df["loss_db"], errors="coerce")
    block_df["dimension"] = pd.to_numeric(block_df["dimension"], errors="coerce")
    block_df["bin_width_ps"] = pd.to_numeric(block_df["bin_width_ps"], errors="coerce")
    for col in (
        "k_used",
        "total_leak_ec_bits",
        "total_leak_ec_bits_legacy_crc",
        "block_success_flag",
        "decode_fail_flag",
        "verification_invoked_flag",
        "verification_bits_used_actual",
        "verification_bits_revealed_legacy_crc",
        "verification_pass_flag",
        "verification_fail_flag",
        "undetected_error_oracle_flag",
        "block_match_oracle_flag",
    ):
        block_df[col] = pd.to_numeric(block_df.get(col), errors="coerce")

    point_rows = []
    for pid, grp in block_df.groupby("point_id"):
        loss_db = int(grp["loss_db"].dropna().iloc[0])
        d = int(grp["dimension"].dropna().iloc[0])
        bw = int(grp["bin_width_ps"].dropna().iloc[0])
        ok_rows = grp[grp["replay_status"].astype(str).str.startswith("ok")].copy()
        blocked_rows = grp[~grp["replay_status"].astype(str).str.startswith("ok")].copy()
        audited_blocks = int(len(ok_rows))
        kept_blocks = int(pd.to_numeric(ok_rows["block_success_flag"], errors="coerce").fillna(0).sum())
        fail_blocks = int(pd.to_numeric(ok_rows["decode_fail_flag"], errors="coerce").fillna(0).sum())
        total_leak = float(pd.to_numeric(ok_rows["total_leak_ec_bits"], errors="coerce").fillna(0).sum()) if audited_blocks > 0 else np.nan
        total_leak_legacy_crc = float(pd.to_numeric(ok_rows["total_leak_ec_bits_legacy_crc"], errors="coerce").fillna(0).sum()) if audited_blocks > 0 else np.nan
        total_kept_info_bits = float((pd.to_numeric(ok_rows["k_used"], errors="coerce").fillna(0) * pd.to_numeric(ok_rows["block_success_flag"], errors="coerce").fillna(0)).sum()) if audited_blocks > 0 else np.nan
        verification_bits_used_actual = float(pd.to_numeric(ok_rows["verification_bits_used_actual"], errors="coerce").fillna(0).sum()) if audited_blocks > 0 else np.nan
        verification_bits_used_actual_legacy_crc = float(pd.to_numeric(ok_rows["verification_bits_revealed_legacy_crc"], errors="coerce").fillna(0).sum()) if audited_blocks > 0 else np.nan
        lambda_ver_bits_actual = verification_bits_used_actual
        lambda_ver_bits_legacy_crc = verification_bits_used_actual_legacy_crc
        verification_tags = sorted(str(x) for x in ok_rows["verification_source_tag"].dropna().unique())
        verification_protocol_ids = sorted(str(x) for x in ok_rows.get("verification_protocol_id", pd.Series(dtype=str)).dropna().unique() if str(x).strip())
        verification_families = sorted(str(x) for x in ok_rows.get("verification_family", pd.Series(dtype=str)).dropna().unique() if str(x).strip())
        channel_model_tags = sorted(str(x) for x in ok_rows.get("channel_model_tag", pd.Series(dtype=str)).dropna().unique() if str(x).strip())
        model_fallback_tags = sorted(str(x) for x in ok_rows.get("model_fallback_tag", pd.Series(dtype=str)).dropna().unique() if str(x).strip())
        p01_model_vals = pd.to_numeric(ok_rows.get("p01_model"), errors="coerce").dropna()
        p10_model_vals = pd.to_numeric(ok_rows.get("p10_model"), errors="coerce").dropna()
        llr_b0_vals = pd.to_numeric(ok_rows.get("llr_b0"), errors="coerce").dropna()
        llr_b1_vals = pd.to_numeric(ok_rows.get("llr_b1"), errors="coerce").dropna()
        verification_invoked_block_count = int(pd.to_numeric(ok_rows.get("verification_invoked_flag"), errors="coerce").fillna(0).sum()) if audited_blocks > 0 else 0
        verification_pass_count = int(pd.to_numeric(ok_rows.get("verification_pass_flag"), errors="coerce").fillna(0).sum()) if audited_blocks > 0 else 0
        verification_fail_count = int(pd.to_numeric(ok_rows.get("verification_fail_flag"), errors="coerce").fillna(0).sum()) if audited_blocks > 0 else 0
        undetected_error_count_empirical = int(pd.to_numeric(ok_rows.get("undetected_error_oracle_flag"), errors="coerce").fillna(0).sum()) if audited_blocks > 0 else 0
        epsilon_ec_empirical = (float(undetected_error_count_empirical) / float(verification_invoked_block_count)) if verification_invoked_block_count > 0 else np.nan
        verification_tag_bits = pd.to_numeric(ok_rows.get("verification_tag_bits"), errors="coerce").dropna()
        tag_bits_used = int(verification_tag_bits.iloc[0]) if not verification_tag_bits.empty else 0
        epsilon_ec_bound = min(1.0, float(verification_invoked_block_count) * (2.0 ** (-tag_bits_used))) if verification_invoked_block_count > 0 and tag_bits_used > 0 else np.nan
        decoder_fail_rate_oracle = (float(fail_blocks) / float(audited_blocks)) if audited_blocks > 0 else np.nan
        if audited_blocks > 0:
            leak_tag = "actual_ir_replay_with_universal_hash_verification"
            verification_source_tag = ";".join(verification_tags) if verification_tags else "missing"
            verification_outcome_source_tag = "replay_oracle_and_universal_hash_transcript"
            epsilon_ec_empirical_source_tag = "empirical_undetected_error_rate_from_replay"
            epsilon_ec_bound_source_tag = "union_bound_over_blocks_universal_hash"
            decoder_fail_rate_oracle_source_tag = "empirical_decode_fail_rate_from_replay"
        else:
            leak_tag = "MISSING"
            verification_source_tag = "missing"
            verification_outcome_source_tag = "missing"
            epsilon_ec_empirical_source_tag = "missing"
            epsilon_ec_bound_source_tag = "missing"
            decoder_fail_rate_oracle_source_tag = "missing"
        blocked_reason = ";".join(sorted(str(x) for x in blocked_rows["blocked_reason"].dropna().unique() if str(x).strip()))
        point_rows.append(
            {
                "point_id": pid,
                "loss_db": loss_db,
                "dimension": d,
                "bin_width_ps": bw,
                "total_leak_ec_bits": total_leak,
                "total_leak_ec_bits_legacy_crc": total_leak_legacy_crc,
                "block_success_rate": (float(kept_blocks) / float(audited_blocks)) if audited_blocks > 0 else "MISSING",
                "frame_success_rate": "MISSING",
                "decode_fail_count": fail_blocks if audited_blocks > 0 else "MISSING",
                "kept_block_count": kept_blocks if audited_blocks > 0 else "MISSING",
                "dropped_block_count": (audited_blocks - kept_blocks) if audited_blocks > 0 else "MISSING",
                "audited_block_count": audited_blocks,
                "total_kept_info_bits": total_kept_info_bits,
                "verification_bits_used_actual": verification_bits_used_actual,
                "verification_bits_used_actual_legacy_crc": verification_bits_used_actual_legacy_crc,
                "lambda_ver_bits_actual": lambda_ver_bits_actual,
                "lambda_ver_source_tag": "universal_hash_transcript",
                "lambda_ver_bits_legacy_crc": lambda_ver_bits_legacy_crc,
                "verification_source_tag": verification_source_tag,
                "verification_protocol_id": ";".join(verification_protocol_ids) if verification_protocol_ids else "missing",
                "verification_family": ";".join(verification_families) if verification_families else "missing",
                "channel_model_tag": ";".join(channel_model_tags) if channel_model_tags else "missing",
                "model_fallback_tag": ";".join(model_fallback_tags) if model_fallback_tags else "missing",
                "p01_model": float(p01_model_vals.mean()) if not p01_model_vals.empty else np.nan,
                "p10_model": float(p10_model_vals.mean()) if not p10_model_vals.empty else np.nan,
                "llr_b0": float(llr_b0_vals.mean()) if not llr_b0_vals.empty else np.nan,
                "llr_b1": float(llr_b1_vals.mean()) if not llr_b1_vals.empty else np.nan,
                "verification_tag_bits": tag_bits_used if tag_bits_used > 0 else np.nan,
                "verification_invoked_block_count": verification_invoked_block_count,
                "verification_pass_count": verification_pass_count,
                "verification_fail_count": verification_fail_count,
                "undetected_error_count_empirical": undetected_error_count_empirical,
                "verification_outcome_source_tag": verification_outcome_source_tag,
                "epsilon_EC_empirical": epsilon_ec_empirical,
                "epsilon_EC_empirical_source_tag": epsilon_ec_empirical_source_tag,
                "epsilon_EC_bound": epsilon_ec_bound,
                "epsilon_EC_bound_formula_tag": epsilon_ec_bound_source_tag,
                "decoder_fail_rate_oracle": decoder_fail_rate_oracle,
                "decoder_fail_rate_oracle_source_tag": decoder_fail_rate_oracle_source_tag,
                "leak_ec_source_tag": leak_tag,
                "replay_status": "ok" if audited_blocks > 0 else "blocked",
                "blocked_reason": blocked_reason if blocked_reason else "",
            }
        )

    point_df = pd.DataFrame(point_rows).sort_values(["dimension", "bin_width_ps"]).reset_index(drop=True)
    point_df.to_csv(output_dir / "actual_ir_point_table.csv", index=False)

    cand = pd.concat([load_candidate_frame(p) for p in candidate_dirs], ignore_index=True)
    cand["point_id"] = cand.apply(lambda r: point_id(loss_db=int(r["loss_db"]), dimension=int(r["dimension"]), bin_width_ps=int(r["bin_width_ps"])), axis=1)
    merged = point_df.merge(
        cand[["point_id", "loss_db", "dimension", "bin_width_ps", "leak_ec_bits_or_proxy"]],
        on=["point_id", "loss_db", "dimension", "bin_width_ps"],
        how="left",
    )
    merged["delta_actual_minus_surrogate"] = pd.to_numeric(merged["total_leak_ec_bits"], errors="coerce") - pd.to_numeric(merged["leak_ec_bits_or_proxy"], errors="coerce")

    actual_count = int(merged["leak_ec_source_tag"].astype(str).str.startswith("actual_ir_replay").sum())
    blocked_count = int(merged["replay_status"].astype(str).eq("blocked").sum())
    summary_lines = [
        "replay_input_dirs:",
        *[f"  - {p}" for p in replay_dirs],
        "candidate_dirs:",
        *[f"  - {p}" for p in candidate_dirs],
        f"point_count: {len(merged)}",
        f"points_with_actual_total_leak: {actual_count}",
        f"blocked_points: {blocked_count}",
        f"fields_still_missing: {'frame_success_rate' if True else 'none'}",
        f"median_delta_actual_minus_surrogate: {pd.to_numeric(merged['delta_actual_minus_surrogate'], errors='coerce').median()}",
        "notes:",
        "- actual_ir_replay_with_universal_hash_verification means replay leakage is paired with a formal per-block universal-hash verification transcript.",
        "- epsilon_EC_empirical is based on undetected-error oracle counts; epsilon_EC_bound is the union bound over per-block universal-hash tags.",
        "- frame_success_rate remains MISSING because a rigorous frame-level denominator is not currently emitted by the replay chain.",
    ]
    write_summary(output_dir / "round1b_summary.txt", summary_lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
