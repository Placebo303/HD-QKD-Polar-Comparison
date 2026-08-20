"""Production entry point for the frozen V31 deterministic finite-graph gate.

The CLI intentionally exposes no tuning, seed, matrix, family, or decoder
options.  It accepts only a new additive evidence root (or resume of the same
root) and a wall-clock chunk budget for long-running stages.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..formal_ir.nonbinary_v31 import run_v31_gate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_nonbinary_v31_gate")
    parser.add_argument("output_root", help="V31 evidence directory (new, or existing for resume)")
    parser.add_argument("--chunk-budget", type=float, default=240.0,
                        help="max wall-clock seconds per invocation before pausing (default 240)")
    parser.add_argument("--verify-only", metavar="ROOT", help="run only the read-only verifier on an existing evidence root")
    args = parser.parse_args(argv)
    if args.verify_only:
        from ..formal_ir.nonbinary_v31 import verify_v31
        result = verify_v31(args.verify_only)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result.get("ok") else 1
    root = Path(args.output_root)
    result = run_v31_gate(root, wallclock_budget_seconds=args.chunk_budget)
    print(json.dumps({"status": result["status"], "evidence_root": result["evidence_root"],
                      "chunk_stage": result.get("chunk_stage")}, ensure_ascii=False))
    return 0 if result.get("status") != "paused" else 0


if __name__ == "__main__":
    raise SystemExit(main())
