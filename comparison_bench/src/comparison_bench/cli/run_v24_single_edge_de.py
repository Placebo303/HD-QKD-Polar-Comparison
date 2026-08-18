"""V24 bounded single-edge lambda/rho DE optimization CLI (M0-M2 gate).

Runs the frozen M0-M2 scientific gate once, writing all evidence additively
under a fresh ``nbldpc_v24_<run_id>`` root.  Use ``--verify-only <run_root>``
to run the read-only semantic verifier on an existing run.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from ..formal_ir.nonbinary_v18_b2_structured_de import build_real_w_q1024
from ..formal_ir.nonbinary_v24_single_edge_de import (
    run_v24_gate,
    verify_run,
)

REPO_OUT_ROOT = Path(__file__).resolve().parents[3] / "outputs_comparison" / "nonbinary_diagnostics" / "nbldpc_v24_20260818"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=None,
                    help="explicit additive V24 run root (default: fresh under "
                         "nbldpc_v24_20260818)")
    ap.add_argument("--verify-only", default=None,
                    help="read-only verify an existing V24 run root and exit")
    ap.add_argument("--resource-limit-seconds", type=float, default=None,
                    help="completed-DE-call perf-counter ceiling (default: none)")
    ap.add_argument("--stop-on-limit", action="store_true",
                    help="stop with resource_blocked when ceiling reached and "
                         "required evaluations remain")
    args = ap.parse_args()

    if args.verify_only:
        report = verify_run(args.verify_only)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["ok"] else 1

    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        # Fresh additive run root (do not overwrite anything).
        import uuid
        out_dir = REPO_OUT_ROOT / f"run_{uuid.uuid4().hex[:12]}"

    w = np.asarray(build_real_w_q1024(), dtype=np.float64)
    decision = run_v24_gate(
        w=w, out_dir=out_dir,
        resource_limit_seconds=args.resource_limit_seconds,
        stop_on_limit=args.stop_on_limit,
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    print(f"evidence root: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
