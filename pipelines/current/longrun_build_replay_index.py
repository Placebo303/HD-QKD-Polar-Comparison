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
from pathlib import Path

from _longrun_common import (
    DEFAULT_WORKERS,
    REPO_ROOT,
    ensure_stage_dir,
    python_tool,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Longrun wrapper for fullgrid replay-index generation.")
    ap.add_argument("--input-dirs", nargs="*", default=[str(REPO_ROOT / "results" / "e2e_20dB_fullgrid_pairing_v2_candidate_t15")])
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--jobs", type=int, default=DEFAULT_WORKERS)
    ap.add_argument("--dimensions", default="")
    ap.add_argument("--bin-widths", default="")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    ensure_stage_dir(output_dir, overwrite=bool(args.overwrite))

    cmd_args = [
        "--output-dir",
        str(output_dir),
        "--jobs",
        str(int(args.jobs)),
        "--overwrite",
        "--input-dirs",
        *[str(Path(p)) for p in args.input_dirs],
    ]
    if str(args.dimensions).strip():
        cmd_args.extend(["--dimensions", str(args.dimensions).strip()])
    if str(args.bin_widths).strip():
        cmd_args.extend(["--bin-widths", str(args.bin_widths).strip()])
    python_tool("round1a_build_replay_index.py", *cmd_args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

