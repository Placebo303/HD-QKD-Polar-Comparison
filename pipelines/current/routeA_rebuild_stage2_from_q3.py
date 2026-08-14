#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
LOSSES = (20, 16, 10, 6)
KEYS = ["dimension", "bin_width_ps"]


def _candidate_name(loss_db: int) -> str:
    suffix = "_t15" if int(loss_db) == 20 else ""
    return f"e2e_{int(loss_db)}dB_fullgrid_pairing_v2_candidate{suffix}"


def _refresh_candidate_metadata(source: Path, authoritative: Path, output: Path) -> None:
    """Copy fresh algorithm outputs and restore measured rate/occupancy provenance."""
    output.mkdir(parents=True, exist_ok=False)
    for name in ("polar_e2e_results.csv", "polar_diag_summary.csv", "polar_layer_metrics.csv"):
        shutil.copy2(source / name, output / name)

    rates = pd.read_csv(authoritative / "_tmp_grid_table.csv")[KEYS + ["coincidence_rate_hz"]]
    if len(rates) != 121 or rates.duplicated(KEYS).any():
        raise SystemExit(f"invalid authoritative rate table: {authoritative / '_tmp_grid_table.csv'}")

    occupancy_rows: list[dict[str, float | int]] = []
    for _, key in rates[KEYS].iterrows():
        d, bw = int(key["dimension"]), int(key["bin_width_ps"])
        path = authoritative / "sidecars" / f"d{d}_bw{bw}" / "blk0" / "occupancy_filter_summary.csv"
        occ = pd.read_csv(path)
        if len(occ) != 1 or int(occ.iloc[0]["frame_diag_available"]) != 1:
            raise SystemExit(f"invalid occupancy evidence: {path}")
        row = occ.iloc[0]
        clean = int(row["n_pairs_in_clean_frames"])
        ambiguous = int(row["n_pairs_in_ambiguous_frames"])
        frames = int(row["n_frames_total"])
        both_multi = int(row["n_frames_both_multi"])
        occupancy_rows.append(
            {
                "dimension": d,
                "bin_width_ps": bw,
                "frame_diag_available": 1,
                "n_pairs_in_clean_frames": clean,
                "n_pairs_in_ambiguous_frames": ambiguous,
                "clean_pair_fraction": clean / (clean + ambiguous),
                "both_multi_frame_fraction": both_multi / frames,
            }
        )
    nuisance = pd.DataFrame(occupancy_rows)

    for name in ("polar_e2e_results.csv", "polar_diag_summary.csv"):
        path = output / name
        frame = pd.read_csv(path).drop(
            columns=[
                "coincidence_rate_hz",
                "frame_diag_available",
                "n_pairs_in_clean_frames",
                "n_pairs_in_ambiguous_frames",
                "clean_pair_fraction",
                "both_multi_frame_fraction",
            ],
            errors="ignore",
        )
        frame = frame.merge(rates, on=KEYS, how="left", validate="one_to_one").merge(
            nuisance, on=KEYS, how="left", validate="one_to_one"
        )
        if len(frame) != 121 or frame["coincidence_rate_hz"].isna().any() or frame["clean_pair_fraction"].isna().any():
            raise SystemExit(f"metadata refresh incomplete: {path}")
        frame["accepted_rate_proxy"] = frame["coincidence_rate_hz"]
        frame["coincidence_rate_source_tag"] = "authoritative_candidate_grid_table_preserved_measured_rate"
        if name == "polar_e2e_results.csv":
            frame["SKR_measured_bps"] = frame["PIE_practical"] * frame["coincidence_rate_hz"]
        frame.to_csv(path, index=False)


def _run(*args: str) -> None:
    subprocess.run([sys.executable, *args], cwd=REPO_ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild corrected Stage 2 tables from frozen Q3 Stage 0/1 evidence.")
    parser.add_argument("--source-root", default="results/paper_grade_v2/four_loss_parts_tag64")
    parser.add_argument("--output-root", default="results/paper_grade_v3/reconciled_stage2_20260812")
    args = parser.parse_args()

    source_root = Path(args.source_root)
    output_root = Path(args.output_root)
    if output_root.exists():
        raise SystemExit(f"output already exists: {output_root}")
    output_root.mkdir(parents=True)

    masters: list[pd.DataFrame] = []
    summary = [f"source_root: {source_root}", "rebuild_scope: Stage2 only; frozen Q3 Stage1 replay reused", "losses:"]
    for loss_db in LOSSES:
        name = _candidate_name(loss_db)
        source_loss = source_root / f"loss{loss_db}" / f"loss_{loss_db}dB"
        source_candidate = source_loss / "stage0_replay_index" / "_recomputed_replay_inputs" / name
        authoritative = REPO_ROOT / "results" / "authoritative" / name
        stage1 = source_loss / "stage1_actual_ir"
        loss_out = output_root / f"loss_{loss_db}dB"
        candidate_out = loss_out / "candidate_reconciled" / name
        stage2 = loss_out / "stage2_security"
        validation = loss_out / "validation"

        _refresh_candidate_metadata(source_candidate, authoritative, candidate_out)
        _run(
            "pipelines/current/routeA_build_formal_stageC.py",
            "--candidate-dir", str(candidate_out),
            "--stage1-dir", str(stage1),
            "--output-dir", str(stage2),
            "--overwrite",
        )
        master_path = stage2 / "security_calibrated_master_table.csv"
        _run(
            "pipelines/current/routeA_validate_correctness_formal.py",
            "--stage1-dir", str(stage1),
            "--master", str(master_path),
            "--expected-points", "121",
            "--verification-tag-bits", "64",
            "--output-dir", str(validation),
        )
        master = pd.read_csv(master_path)
        master["source_q3_stage1_dir"] = str(stage1)
        masters.append(master)
        summary.append(f"  - loss={loss_db} rows={len(master)} candidate={candidate_out} stage1={stage1}")

    merged = pd.concat(masters, ignore_index=True)
    merged.to_csv(output_root / "cross_loss_reconciled_master_table.csv", index=False)
    summary.extend(
        [
            f"cross_loss_rows: {len(merged)}",
            f"reconciled_reportable_rows: {int(merged['reconciliation_evidence_status'].eq('verified_actual_ir_replay_reconciled_net').sum())}",
            "main_result_source: actual_ir_reconciled_net_not_secure",
            "claim_boundary: public_ec_only_not_secure",
            "legacy_secure_shadow_status: scientifically_blocked_dimensional_inconsistency",
        ]
    )
    (output_root / "rebuild_summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
