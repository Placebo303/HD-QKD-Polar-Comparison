"""V25 empirical timestamp channel + multilevel factorization gate CLI.

Runs M0-M4 over the frozen q=1024 fresh pairs and writes an additive run root.
Use --verify-only <root> for the read-only verifier.
"""
from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

from ..formal_ir.nonbinary_v25_gate import (
    SOURCES,
    run_v25_gate,
    verify_run,
)

REPO_OUT_ROOT = Path(__file__).resolve().parents[3] / "outputs_comparison" / "nonbinary_diagnostics" / "nbldpc_v25_20260818"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--verify-only", default=None)
    ap.add_argument("--sources", default=",".join(SOURCES.keys()),
                    help="comma-separated source ids (default: all 3)")
    args = ap.parse_args()

    if args.verify_only:
        report = verify_run(args.verify_only)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["ok"] else 1

    srcs = [s.strip() for s in args.sources.split(",") if s.strip()]
    for s in srcs:
        if s not in SOURCES:
            raise SystemExit(f"unknown source {s}")
    out_dir = Path(args.out_dir) if args.out_dir else REPO_OUT_ROOT / f"run_{uuid.uuid4().hex[:12]}"
    res = run_v25_gate(out_dir=out_dir, sources=srcs)
    print(json.dumps(res, indent=2, sort_keys=True))
    print(f"evidence root: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
