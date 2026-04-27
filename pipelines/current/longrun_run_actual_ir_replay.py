#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SECURITY_REPORTS = REPO_ROOT / "tools" / "security_reports"
for _p in (REPO_ROOT, SECURITY_REPORTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

from _longrun_common import (
    DEFAULT_WORKERS,
    REPO_ROOT,
    csv_read,
    point_table_sort,
    python_tool,
    shard_dataframe,
)


def _run_shard(shard_index_dir: str, shard_output_dir: str, candidate_dirs: list[str]) -> str:
    python_tool(
        "round1b_run_actual_ir_replay.py",
        "--replay-index-dir",
        shard_index_dir,
        "--output-dir",
        shard_output_dir,
        "--input-dirs",
        *candidate_dirs,
        "--overwrite",
    )
    return shard_output_dir


def main() -> int:
    ap = argparse.ArgumentParser(description="Longrun wrapper for sharded actual-IR replay.")
    ap.add_argument("--input-dirs", nargs="*", default=[str(REPO_ROOT / "results" / "e2e_20dB_fullgrid_pairing_v2_candidate_t15")])
    ap.add_argument("--replay-index-dir", default="")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    replay_index_dir = Path(args.replay_index_dir) if str(args.replay_index_dir).strip() else output_dir
    if output_dir.exists():
        if bool(args.overwrite) and output_dir.resolve() != replay_index_dir.resolve():
            for child in output_dir.iterdir():
                if child.is_dir():
                    import shutil
                    shutil.rmtree(child)
                else:
                    child.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "_shards").mkdir(parents=True, exist_ok=True)
    point_df = csv_read(replay_index_dir / "replay_index_point_table.csv")
    layer_df = csv_read(replay_index_dir / "replay_index_layer_table.csv")
    point_df = point_table_sort(point_df)
    shard_frames = shard_dataframe(point_df, int(args.workers))

    shard_output_dirs: list[Path] = []
    shard_specs: list[tuple[str, str, list[str]]] = []
    for shard_no, shard_points in enumerate(shard_frames):
        shard_key = f"shard_{shard_no:02d}"
        shard_index_dir = output_dir / "_shards" / shard_key / "replay_index"
        shard_output_dir = output_dir / "_shards" / shard_key / "replay_output"
        shard_index_dir.mkdir(parents=True, exist_ok=True)
        shard_output_dir.mkdir(parents=True, exist_ok=True)
        shard_points.to_csv(shard_index_dir / "replay_index_point_table.csv", index=False)
        shard_layer = layer_df[layer_df["point_id"].isin(shard_points["point_id"].astype(str))].copy()
        shard_layer.to_csv(shard_index_dir / "replay_index_layer_table.csv", index=False)
        shard_output_dirs.append(shard_output_dir)
        shard_specs.append((str(shard_index_dir), str(shard_output_dir), [str(Path(p)) for p in args.input_dirs]))

    max_workers = max(1, min(int(args.workers), len(shard_specs)))
    if max_workers == 1:
        for spec in shard_specs:
            _run_shard(*spec)
    else:
        with ProcessPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(_run_shard, *spec) for spec in shard_specs]
            for fut in futures:
                fut.result()

    block_frames = [csv_read(p / "actual_ir_block_table.csv") for p in shard_output_dirs]
    block_df = point_table_sort(pd.concat(block_frames, ignore_index=True))
    block_df.to_csv(output_dir / "actual_ir_block_table.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

