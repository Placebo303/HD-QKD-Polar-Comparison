#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _security_round_common import REPO_ROOT, candidate_sidecar_root, ensure_output_dir, infer_loss_db_from_path, load_candidate_bundle, write_summary

REQUIRED_LAYER_COLS = [
    "decoder_mode_best",
    "k_best",
    "rate_best",
    "crc_bits",
    "frozen_count_best",
    "layer_block_symbols",
]


def _default_input_dirs() -> list[Path]:
    return [REPO_ROOT / "results" / "e2e_20dB_fullgrid_pairing_v2_candidate_t15"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit whether current outputs are sufficient for actual IR replay.")
    ap.add_argument("--input-dirs", nargs="*", default=[])
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir, overwrite=bool(args.overwrite))
    input_dirs = [Path(p) for p in args.input_dirs] if args.input_dirs else _default_input_dirs()

    md_lines = ["# Replay Input Audit", "", "## Inputs", *[f"- {p}" for p in input_dirs], ""]
    summary_lines = ["input_dirs:", *[f"  - {p}" for p in input_dirs]]
    all_ready = True

    for candidate_dir in input_dirs:
        loss_db = infer_loss_db_from_path(candidate_dir)
        main, diag, layer = load_candidate_bundle(candidate_dir)
        missing_layer_cols = [c for c in REQUIRED_LAYER_COLS if c not in layer.columns]
        ready_arrays = 0
        total_points = 0
        for _, row in main.iterrows():
            total_points += 1
            sidecar_root = candidate_sidecar_root(candidate_dir, int(row["dimension"]), int(row["bin_width_ps"]))
            if (sidecar_root / "a_eff.npy").exists() and (sidecar_root / "b_eff.npy").exists():
                ready_arrays += 1
        main_ready = ready_arrays == total_points and not missing_layer_cols
        all_ready = all_ready and main_ready

        md_lines.extend([
            f"## loss={loss_db} dB",
            f"- point_count: {total_points}",
            f"- points with a_eff/b_eff present: {ready_arrays}/{total_points}",
            f"- polar_layer_metrics columns missing for replay: {', '.join(missing_layer_cols) if missing_layer_cols else 'none'}",
            f"- replay minimum conditions currently satisfied from existing tables alone: {'yes' if main_ready else 'no'}",
            "",
        ])
        summary_lines.extend([
            f"loss_{loss_db}db_point_count: {total_points}",
            f"loss_{loss_db}db_arrays_ready: {ready_arrays}/{total_points}",
            f"loss_{loss_db}db_missing_layer_cols: {', '.join(missing_layer_cols) if missing_layer_cols else 'none'}",
        ])

    md_lines.extend([
        "## Conclusions",
        f"1. replay metadata already complete: {'yes' if all_ready else 'no'}",
        "2. current blocking classes: missing sidecar arrays, missing per-layer code-choice metadata, ambiguous block slicing rule, missing point-to-layer mapping.",
        "3. next action: regenerate replay-only layer metrics with appended code-choice metadata if current tables do not already contain them.",
    ])
    summary_lines.extend([
        f"replay_input_chain_complete_from_existing_tables: {'yes' if all_ready else 'no'}",
        "required_replay_columns:",
        *[f"  - {c}" for c in REQUIRED_LAYER_COLS],
    ])

    write_summary(output_dir / "replay_input_audit.md", md_lines)
    write_summary(output_dir / "round1a_summary.txt", summary_lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
