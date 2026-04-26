#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _minrerun_common import (
    KEY_COLS,
    existing_fresh_losses,
    fresh_candidate_dir,
    fresh_stage1_dir,
    fresh_stage2_dir,
    build_frame_audit_from_candidate,
    csv_read,
    ensure_output_dir,
    load_stage1_tables,
    write_summary,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit whether fresh rerun outputs support minimal replay/frame/security rerun only.")
    ap.add_argument("--input-dirs", nargs="*", default=[])
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    ensure_output_dir(out_dir, overwrite=bool(args.overwrite))

    rows: list[dict[str, object]] = []
    for loss_db in existing_fresh_losses():
        candidate_dir = fresh_candidate_dir(loss_db)
        stage1_dir = fresh_stage1_dir(loss_db)
        stage2_dir = fresh_stage2_dir(loss_db)
        block_df, point_df = load_stage1_tables(stage1_dir)
        frame_df = build_frame_audit_from_candidate(candidate_dir, point_df)
        point_lookup = point_df.set_index(KEY_COLS, drop=False)
        frame_lookup = frame_df.set_index(KEY_COLS, drop=False)
        for key in sorted(point_lookup.index.unique().tolist()):
            prow = point_lookup.loc[key]
            if isinstance(prow, pd.DataFrame):
                prow = prow.iloc[0]
            frow = frame_lookup.loc[key]
            if isinstance(frow, pd.DataFrame):
                frow = frow.iloc[0]
            d = int(prow["dimension"])
            bw = int(prow["bin_width_ps"])
            has_block = not block_df[(block_df["loss_db"] == loss_db) & (block_df["dimension"] == d) & (block_df["bin_width_ps"] == bw)].empty
            has_verif_tag = has_block and block_df[(block_df["loss_db"] == loss_db) & (block_df["dimension"] == d) & (block_df["bin_width_ps"] == bw)]["verification_source_tag"].astype(str).str.len().gt(0).any()
            has_occ = str(frow["accepted_frame_fraction_source_tag"]) == "actual_sidecar_occupancy_summary"
            has_a_eff = Path(str(candidate_dir / 'sidecars' / f'd{d}_bw{bw}' / 'blk0' / 'a_eff.npy')).exists()
            has_b_eff = Path(str(candidate_dir / 'sidecars' / f'd{d}_bw{bw}' / 'blk0' / 'b_eff.npy')).exists()
            if has_block and has_occ:
                status = "minrerun_ready"
            elif has_block:
                status = "replay_patch_needed"
            else:
                status = "front_half_rerun_required"
            rows.append(
                {
                    "loss_db": loss_db,
                    "dimension": d,
                    "bin_width_ps": bw,
                    "point_id": str(prow["point_id"]),
                    "has_replay_index": True,
                    "has_actual_ir_block_table": has_block,
                    "has_actual_ir_point_table": True,
                    "has_sidecar_occupancy_summary": has_occ,
                    "has_a_eff": has_a_eff,
                    "has_b_eff": has_b_eff,
                    "has_verification_source_tag": has_verif_tag,
                    "has_frame_count_fields": has_occ,
                    "minrerun_status": status,
                    "stage2_exists": stage2_dir.exists(),
                }
            )

    audit = pd.DataFrame(rows).sort_values(KEY_COLS).reset_index(drop=True)
    audit.to_csv(out_dir / "frame_accounting_input_audit.csv", index=False)
    ready = int(audit["minrerun_status"].eq("minrerun_ready").sum()) if not audit.empty else 0
    replay_patch_needed = int(audit["minrerun_status"].eq("replay_patch_needed").sum()) if not audit.empty else 0
    front_half = int(audit["minrerun_status"].eq("front_half_rerun_required").sum()) if not audit.empty else 0
    lines = [
        "inputs:",
        *[f"  - {p}" for p in (args.input_dirs or [str(fresh_stage1_dir(20)), str(fresh_stage2_dir(20))])],
        f"point_count: {len(audit)}",
        f"minrerun_ready_points: {ready}",
        f"replay_patch_needed_points: {replay_patch_needed}",
        f"front_half_rerun_required_points: {front_half}",
        "answers:",
        f"1. sufficient_for_back_half_only: {'yes' if front_half == 0 else 'partial'}",
        "2. directly_rebuildable_fields: verification_source_tag, verification_bits_used_actual_from_existing_budget, candidate_frame_count, accepted_frame_count, rejected_frame_count, accepted_frame_fraction, rejected_frame_fraction",
        f"3. fields_requiring_replay_patch: {'none' if replay_patch_needed == 0 else 'verification logging only'}",
        f"4. actual_ir_replay_rerun_required: {'no' if replay_patch_needed == 0 else 'point-selective_only'}",
        f"5. full_front_half_rerun_required: {'no' if front_half == 0 else 'yes_for_some_points'}",
    ]
    write_summary(out_dir / 'stageA_summary.txt', lines)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
