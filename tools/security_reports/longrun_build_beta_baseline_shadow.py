#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from _longrun_common import (
    DEFAULT_BETA_BASELINE,
    DEFAULT_EPS_COR,
    DEFAULT_EPS_SEC,
    DEFAULT_FRANSON_VISIBILITY,
    python_tool,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Longrun wrapper for beta-baseline finite-key shadow.")
    ap.add_argument("--input-dirs", nargs="*", default=[])
    ap.add_argument("--franson-visibility", type=float, default=DEFAULT_FRANSON_VISIBILITY)
    ap.add_argument("--beta-baseline", type=float, default=DEFAULT_BETA_BASELINE)
    ap.add_argument("--eps-sec", type=float, default=DEFAULT_EPS_SEC)
    ap.add_argument("--eps-cor", type=float, default=DEFAULT_EPS_COR)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    python_tool(
        "round2_build_beta_baseline_shadow.py",
        "--franson-visibility",
        str(float(args.franson_visibility)),
        "--beta-baseline",
        str(float(args.beta_baseline)),
        "--eps-sec",
        str(float(args.eps_sec)),
        "--eps-cor",
        str(float(args.eps_cor)),
        "--output-dir",
        str(Path(args.output_dir)),
        "--overwrite",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
