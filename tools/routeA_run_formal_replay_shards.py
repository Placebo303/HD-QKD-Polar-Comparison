#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from _longrun_common import csv_read, point_table_sort, python_tool, shard_dataframe, write_text
from _security_round_common import ensure_output_dir


def _shard_done(shard_output_dir: Path) -> bool:
    return (
        (shard_output_dir / "actual_ir_block_table.csv").exists()
        and (shard_output_dir / "round1b_summary.txt").exists()
    )


def _write_shard_index(
    *,
    shard_index_dir: Path,
    shard_points: pd.DataFrame,
    layer_df: pd.DataFrame,
) -> None:
    shard_index_dir.mkdir(parents=True, exist_ok=True)
    shard_points.to_csv(shard_index_dir / "replay_index_point_table.csv", index=False)
    shard_layer = layer_df[layer_df["point_id"].astype(str).isin(shard_points["point_id"].astype(str))].copy()
    shard_layer.to_csv(shard_index_dir / "replay_index_layer_table.csv", index=False)


def _run_shard(
    *,
    candidate_dir: Path,
    shard_index_dir: Path,
    shard_output_dir: Path,
    verification_tag_bits: int,
    shard_key: str,
    row_count: int,
) -> str:
    python_tool(
        "round1b_run_actual_ir_replay.py",
        "--input-dirs",
        str(candidate_dir),
        "--replay-index-dir",
        str(shard_index_dir),
        "--output-dir",
        str(shard_output_dir),
        "--verification-tag-bits",
        str(int(verification_tag_bits)),
        "--overwrite",
    )
    return f"{shard_key}: ran rows={row_count}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Route A resumable formal replay shard runner.")
    ap.add_argument("--candidate-dir", required=True)
    ap.add_argument("--replay-index-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--shards", type=int, default=16)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--verification-tag-bits", type=int, default=32)
    ap.add_argument("--resume", dest="resume", action="store_true", default=True)
    ap.add_argument("--no-resume", dest="resume", action="store_false")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    candidate_dir = Path(args.candidate_dir)
    replay_index_dir = Path(args.replay_index_dir)
    output_dir = Path(args.output_dir)

    if bool(args.overwrite):
        ensure_output_dir(output_dir, overwrite=True)
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "_shards").mkdir(parents=True, exist_ok=True)

    point_df = point_table_sort(csv_read(replay_index_dir / "replay_index_point_table.csv"))
    layer_df = csv_read(replay_index_dir / "replay_index_layer_table.csv")

    # Keep a root copy so the formal stage1 directory is self-contained.
    point_df.to_csv(output_dir / "replay_index_point_table.csv", index=False)
    layer_df.to_csv(output_dir / "replay_index_layer_table.csv", index=False)

    shard_frames = shard_dataframe(point_df, int(args.shards))
    shard_output_dirs: list[Path] = []
    shard_status: list[str] = []
    pending: list[tuple[str, Path, Path, int]] = []

    for shard_no, shard_points in enumerate(shard_frames):
        shard_key = f"shard_{shard_no:03d}"
        shard_root = output_dir / "_shards" / shard_key
        shard_index_dir = shard_root / "replay_index"
        shard_output_dir = shard_root / "replay_output"
        shard_output_dir.mkdir(parents=True, exist_ok=True)
        _write_shard_index(shard_index_dir=shard_index_dir, shard_points=shard_points, layer_df=layer_df)
        shard_output_dirs.append(shard_output_dir)

        if bool(args.resume) and _shard_done(shard_output_dir):
            shard_status.append(f"{shard_key}: skipped_existing rows={len(shard_points)}")
            continue

        pending.append((shard_key, shard_index_dir, shard_output_dir, len(shard_points)))

    max_workers = max(1, int(args.workers))
    if max_workers == 1:
        for shard_key, shard_index_dir, shard_output_dir, row_count in pending:
            shard_status.append(
                _run_shard(
                    candidate_dir=candidate_dir,
                    shard_index_dir=shard_index_dir,
                    shard_output_dir=shard_output_dir,
                    verification_tag_bits=int(args.verification_tag_bits),
                    shard_key=shard_key,
                    row_count=row_count,
                )
            )
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [
                ex.submit(
                    _run_shard,
                    candidate_dir=candidate_dir,
                    shard_index_dir=shard_index_dir,
                    shard_output_dir=shard_output_dir,
                    verification_tag_bits=int(args.verification_tag_bits),
                    shard_key=shard_key,
                    row_count=row_count,
                )
                for shard_key, shard_index_dir, shard_output_dir, row_count in pending
            ]
            for fut in as_completed(futures):
                shard_status.append(fut.result())

    block_frames = []
    missing_shards = []
    for shard_output_dir in shard_output_dirs:
        block_path = shard_output_dir / "actual_ir_block_table.csv"
        if block_path.exists():
            block_frames.append(csv_read(block_path))
        else:
            missing_shards.append(str(shard_output_dir))
    if missing_shards:
        raise SystemExit("missing shard outputs:\n" + "\n".join(missing_shards))

    block_df = point_table_sort(pd.concat(block_frames, ignore_index=True)) if block_frames else pd.DataFrame()
    block_df.to_csv(output_dir / "actual_ir_block_table.csv", index=False)

    python_tool(
        "round1b_build_actual_ir_logs_index.py",
        "--input-dirs",
        str(output_dir),
        "--candidate-dirs",
        str(candidate_dir),
        "--output-dir",
        str(output_dir),
        "--overwrite",
    )

    point_actual = csv_read(output_dir / "actual_ir_point_table.csv")
    formal_rows = int(
        point_actual.get("epsilon_EC_bound_formula_tag", pd.Series(dtype=str))
        .astype(str)
        .eq("union_bound_over_blocks_universal_hash")
        .sum()
    )
    summary_lines = [
        f"candidate_dir: {candidate_dir}",
        f"replay_index_dir: {replay_index_dir}",
        f"output_dir: {output_dir}",
        f"point_count: {len(point_df)}",
        f"shard_count: {len(shard_frames)}",
        f"verification_tag_bits: {int(args.verification_tag_bits)}",
        f"block_row_count: {len(block_df)}",
        f"point_row_count: {len(point_actual)}",
        f"formal_point_rows: {formal_rows}",
        f"resume_enabled: {bool(args.resume)}",
        f"workers: {max_workers}",
        "shard_status:",
        *[f"  - {s}" for s in shard_status],
        "notes:",
        "- runner is resumable and uses thread-scheduled subprocesses when workers > 1; no multiprocessing Pipe is used.",
        "- universal-hash verification is produced by round1b_run_actual_ir_replay.py.",
    ]
    write_text(output_dir / "routeA_formal_replay_shards_summary.txt", "\n".join(summary_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
