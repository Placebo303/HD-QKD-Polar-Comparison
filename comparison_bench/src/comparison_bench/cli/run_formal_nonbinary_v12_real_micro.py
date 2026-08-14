"""CLI for the V12 nonbinary LDPC real micro-feasibility lane
(``formal-nonbinary-ldpc-v12-real-micro-feasibility``).

Main-thread-authorized prepare-only production path (V12-RP01..RP03): the
``prepare`` action writes exactly the three preparation artifacts
(``exclusion_manifest.json``, ``partition_lock.json``, ``pre_run_plan.json``)
into one fresh additive package directory under
``comparison_bench/outputs_comparison/formal_ir_methods/``, without decoding
and without ever loading Alice/Bob arrays.  If four fresh traceable 10 dB
identities cannot be frozen, the partition lock and plan record
``source_partition_blocked``.

Standalone ``plan`` and ``execute`` remain hard stops — real decoding and the
one real execute (V12-X01) require explicit future main-thread authorization.
The read-only ``verify`` action never imports or calls a decoder.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..formal_ir import nonbinary_v12_real_micro as core


def main() -> int:
    root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(
        description="V12 nonbinary LDPC real micro-feasibility "
                    "(prepare-only production path; plan/execute blocked)")
    parser.add_argument("action", nargs="?", default="plan",
                        choices=("prepare", "plan", "execute", "verify"))
    parser.add_argument("--output", default=None,
                        help="fresh additive package directory (prepare/verify)")
    parser.add_argument("--formal-ir-root", default=None,
                        help="formal_ir_methods discovery root "
                             "(default comparison_bench/outputs_comparison/formal_ir_methods)")
    parser.add_argument("--transfer-eval-root", default=None,
                        help="transfer_evaluation discovery root "
                             "(default comparison_bench/outputs_comparison/transfer_evaluation)")
    parser.add_argument("--final-ir-root", default=None,
                        help="final_ir_method_selection discovery root "
                             "(default comparison_bench/outputs_comparison/final_ir_method_selection)")
    args = parser.parse_args()
    if args.action in ("plan", "execute"):
        print(f"V12 production {args.action} is not authorized during the initial phase; "
              "use the prepare action for the prepare-only production path", file=sys.stderr)
        raise SystemExit(2)
    if args.output is None:
        print("--output DIR is required", file=sys.stderr)
        raise SystemExit(2)
    if args.action == "prepare":
        roots = [
            Path(args.formal_ir_root) if args.formal_ir_root else root / "comparison_bench/outputs_comparison/formal_ir_methods",
            Path(args.transfer_eval_root) if args.transfer_eval_root else root / "comparison_bench/outputs_comparison/transfer_evaluation",
            Path(args.final_ir_root) if args.final_ir_root else root / "comparison_bench/outputs_comparison/final_ir_method_selection",
        ]
        try:
            result = core.prepare_production(args.output, discovery_roots=roots)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            raise SystemExit(2)
        print(json.dumps(result, sort_keys=True))
        return 0
    try:
        print(json.dumps(core.verify(args.output, _test_only=False), sort_keys=True))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
    return 0


if __name__ == "__main__":
    main()
