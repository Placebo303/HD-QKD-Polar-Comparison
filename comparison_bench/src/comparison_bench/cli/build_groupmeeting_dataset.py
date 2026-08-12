#!/usr/bin/env python3
"""Build expanded real-data subset for group-meeting comparison.

Selects:
  - d=8:  bw=50 (high noise), bw=120 (medium), bw=180 (low), bw=200 (very low) — 4 frames each
  - d=16: bw=60 (high), bw=100 (medium), bw=180 (low) — 4 frames each
  - d=32: bw=40 (very high), bw=60 (high), bw=100 (medium), bw=180 (low) — 4 frames each
  - d=1024: bw=100 (medium), bw=180 (low), bw=200 (very low) — up to 64 frames each

Output: group_meeting_ir_20260615/groupmeeting_subset.parquet (pair-level data)
"""

import argparse
from pathlib import Path
import pandas as pd


def build_groupmeeting_dataset(input_path: Path, output_path: Path, max_frames: int = 64) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    batch = pd.read_parquet(input_path)
    print(f"Loaded batch: {len(batch)} rows, {batch.dataset_id.nunique()} datasets")

    # Define target datasets with noise regime labels
    targets = {
        # d=8: dimension low, 4 noise points
        "real_typeii_20db_d8_bw50_blk0":  "high",
        "real_typeii_20db_d8_bw120_blk0": "medium",
        "real_typeii_20db_d8_bw180_blk0": "low",
        "real_typeii_20db_d8_bw200_blk0": "very_low",
        # d=16: dimension low, 3 noise points
        "real_typeii_20db_d16_bw60_blk0":  "high",
        "real_typeii_20db_d16_bw100_blk0": "medium",
        "real_typeii_20db_d16_bw180_blk0": "low",
        # d=32: dimension mid, 4 noise points
        "real_typeii_20db_d32_bw40_blk0":  "very_high",
        "real_typeii_20db_d32_bw60_blk0":  "high",
        "real_typeii_20db_d32_bw100_blk0": "medium",
        "real_typeii_20db_d32_bw180_blk0": "low",
        # d=1024: dimension high, for large-frame-count perspective
        "real_typeii_20db_d1024_bw100_blk0": "medium",
        "real_typeii_20db_d1024_bw180_blk0": "low",
        "real_typeii_20db_d1024_bw200_blk0": "very_low",
    }

    available = [ds for ds in targets if ds in batch.dataset_id.unique()]
    missing = [ds for ds in targets if ds not in batch.dataset_id.unique()]
    if missing:
        print(f"WARNING: Missing datasets: {missing}")

    print(f"Selected datasets: {len(available)}")
    
    # Collect up to max_frames frames per dataset
    chunks = []
    frame_counts = {}
    for ds_id in available:
        sub = batch[batch.dataset_id == ds_id]
        # Get frame IDs
        frame_ids = sorted(sub.frame_id.unique())
        selected = frame_ids[:min(len(frame_ids), max_frames)]
        chunk = sub[sub.frame_id.isin(selected)].copy()
        chunk["noise_regime"] = targets.get(ds_id, "unknown")
        chunks.append(chunk)
        frame_counts[ds_id] = len(selected)
        print(f"  {ds_id}: {len(selected)} frames (noise={targets.get(ds_id, '?')})")

    result = pd.concat(chunks, ignore_index=True)
    result.to_parquet(output_path, index=False)
    print(f"\nWrote {len(result)} rows to {output_path}")
    print(f"Total datasets: {result.dataset_id.nunique()}")
    print(f"Total frames: {result.groupby('dataset_id').frame_id.nunique().sum()}")

    # Summary table
    print("\n=== SUMMARY ===")
    summary = result.groupby("dataset_id").agg(
        dimension=("dimension", "first"),
        bin_width_ps=("bin_width_ps", "first"),
        n_frames=("frame_id", "nunique"),
        n_pairs=("pair_idx", "count"),
        noise_regime=("noise_regime", "first"),
    ).reset_index()
    print(summary.to_string(index=False))


def main() -> int:
    ap = argparse.ArgumentParser(description="Build expanded group-meeting dataset subset.")
    ap.add_argument("--input", default="comparison_bench/outputs_comparison/real_sidecars_frame_batch.parquet")
    ap.add_argument("--output", default="comparison_bench/outputs_comparison/group_meeting_ir_20260615/groupmeeting_subset.parquet")
    ap.add_argument("--max-frames", type=int, default=64, help="Max frames per dataset (default: 64)")
    args = ap.parse_args()

    build_groupmeeting_dataset(Path(args.input), Path(args.output), args.max_frames)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
