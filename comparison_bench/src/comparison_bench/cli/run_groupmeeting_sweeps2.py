#!/usr/bin/env python3
"""Master sweep runner for group meeting.

Each frame length writes to its own subdirectory to avoid key collisions.
Usage:
    python -m comparison_bench.src.comparison_bench.cli.run_groupmeeting_sweeps2

Outputs: comparison_bench/outputs_comparison/group_meeting_ir_20260615/flen64/ etc.
"""
import argparse
import os
import subprocess
import sys
import time
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

BASE_DIR = Path("comparison_bench/outputs_comparison/group_meeting_ir_20260615")

CASCADE_TEMPLATE = """global:
  output_dir: {output_dir}
dataset:
  frame_batch_path: {batch_path}
cascade:
  block_size_schedule:
    - [16, 32, 64, 128]
    - [12, 6, 24, 13]
    - [8, 4, 16, 13]
  num_passes: [3, 4]
  permutation_mode: ["seeded_random"]
  seed: [0]
  mapping: ["gray"]
  bisection_mode: ["recursive_binary"]
  verify_mode: ["crc32"]
  frame_caps: [4]
  max_workers: 16
  include_all_points: true
  force: {force}
"""

LDPC_TEMPLATE = """global:
  output_dir: {output_dir}
dataset:
  frame_batch_path: {batch_path}
layered_ldpc:
  parity_fraction: [0.5, 0.67, 0.8, 0.9, 1.0]
  max_iter: [50]
  osd_order: [0]
  bp_method: ["minimum_sum"]
  mapping: ["gray"]
  llr_mode: ["hard", "bsc_estimated"]
  bitplane_rate_mode: ["uniform"]
  column_weight: [3]
  seed: [20260428]
  frame_caps: [4]
  max_workers: 16
  include_all_points: true
  force: {force}
"""

QLDPC_TEMPLATE = """global:
  output_dir: {output_dir}
dataset:
  frame_batch_path: {batch_path}
qldpc_reference:
  check_fraction: [0.33, 0.4, 0.5]
  row_weight: [3, 4]
  target_ser_min: [0.01]
  frame_caps: [4]
  max_workers: 8
  include_all_points: true
  force: {force}
"""


def run_stage(name: str, template: str, flen: int, force: bool = False):
    out_dir = BASE_DIR / f"flen{flen}"
    out_dir.mkdir(parents=True, exist_ok=True)

    batch_name = "groupmeeting_subset.parquet" if flen == 64 else f"groupmeeting_subset_flen{flen}.parquet"
    batch_path = str(BASE_DIR / batch_name)

    if not (BASE_DIR / batch_name).exists():
        print(f"  SKIP {name} flen={flen}: {batch_name} not found")
        return

    yaml_text = template.format(output_dir=str(out_dir), batch_path=batch_path, force=str(force).lower())
    config_path = out_dir / f"_config_{name}.yaml"
    config_path.write_text(yaml_text)

    module_map = {
        "cascade": "comparison_bench.cli.run_cascade_param_sweep",
        "ldpc": "comparison_bench.cli.run_layered_ldpc_param_sweep",
        "qldpc": "comparison_bench.cli.run_qldpc_param_sweep",
    }
    env = os.environ.copy()
    # PYTHONPATH must include src/ so comparison_bench package is found
    src_dir = str(REPO / "comparison_bench" / "src")
    existing_pypath = env.get("PYTHONPATH", "").strip()
    env["PYTHONPATH"] = f"{src_dir};{existing_pypath}" if existing_pypath else src_dir
    
    cmd = [sys.executable, "-m", module_map[name], "--config", str(config_path)]
    print(f"  {name} flen={flen}: started...", flush=True)
    t0 = time.perf_counter()
    result = subprocess.run(cmd, cwd=str(REPO), env=env, capture_output=True, text=True)
    dt = time.perf_counter() - t0
    print(f"  {name} flen={flen}: {dt:.1f}s", flush=True)
    if result.returncode != 0:
        print(f"  FAILED rc={result.returncode}: {result.stderr[-300:]}")
    else:
        lines = [l for l in result.stdout.split("\n") if l.strip()]
        for l in lines[-3:]:
            print(f"    {l}")
    config_path.unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--cascade-only", action="store_true")
    ap.add_argument("--ldpc-only", action="store_true")
    ap.add_argument("--qldpc-only", action="store_true")
    ap.add_argument("--flen", type=int, choices=[64, 128, 256])
    args = ap.parse_args()

    BASE_DIR.mkdir(parents=True, exist_ok=True)
    flens = [args.flen] if args.flen else [64, 128, 256]
    t0 = time.perf_counter()

    for flen in flens:
        if not args.ldpc_only and not args.qldpc_only:
            print(f"\n{'='*60}")
            print(f"CASCADE flen={flen}")
            print(f"{'='*60}")
            run_stage("cascade", CASCADE_TEMPLATE, flen, force=args.force)

        if not args.cascade_only and not args.qldpc_only:
            print(f"\n{'='*60}")
            print(f"LDPC flen={flen}")
            print(f"{'='*60}")
            run_stage("ldpc", LDPC_TEMPLATE, flen, force=args.force)

        if (args.qldpc_only or not (args.cascade_only or args.ldpc_only)) and flen == 64:
            print(f"\n{'='*60}")
            print(f"QLDPC flen={flen}")
            print(f"{'='*60}")
            run_stage("qldpc", QLDPC_TEMPLATE, flen, force=args.force)

    dt = time.perf_counter() - t0
    print(f"\nTotal: {dt:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
