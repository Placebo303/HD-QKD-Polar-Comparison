"""Development-only CLI for the NBLDPC v7 R1A/R1B/R2/R3 engineering lanes.

The default action is plan preparation, never execution:

- ``plan`` (default) prepares the frozen development plan; without
  ``--output`` it prints the in-memory plan preview, with ``--output DIR`` it
  writes ``pre_run_plan.json`` into an explicit (workspace) directory.  After
  the corresponding main-thread review, plan *preparation* is authorized for
  the sacrificed 4+4 CANARY config only (``--canary``; R1A via V7-12, R1B via
  V7-15, R2 via V7-22, R3 via V7-30); every DEVELOPMENT plan still refuses
  until a later review.  The official development root under
  ``comparison_bench/outputs_comparison/formal_ir_methods/`` is locked for
  every config.
- ``verify`` is read-only and requires ``--output DIR``.
- ``execute`` is a hard stop for every DEVELOPMENT config (R1A, R1B, R2, R3):
  production development execution requires a separately reviewed plan and is
  never invoked here.  The four V7 exceptions are the sacrificed CANARY
  configs: the V7-12 R1A ``--canary``, the V7-15 R1B ``--r1b --canary``, the
  V7-22 R2 ``--r2 --canary`` and the V7-30 R3 ``--r3 --canary``.
  ``execute`` is then allowed only together with ``--output DIR`` and runs
  the sacrificed 4+4-frame CANARY plan through the explicit production runner
  (``production_runner`` for R1A, ``production_runner_r1b`` for R1B,
  ``production_runner_r2`` for R2, ``production_runner_r3`` for R3) into
  that non-official workspace directory.  ``execute`` never touches the
  official root.  **R2/R3 DEVELOPMENT ``execute`` is a hard stop until a
  later review** (mirror of the R1A/R1B development-execute stops).

``--r2`` selects the QSC density-evolution lane
(``nbldpc_formal_v7_r2_qsc_de``); ``--r3`` selects the GF(32)xGF(32)
multilevel lane (``nbldpc_formal_v7_r3_gf32x2``); ``--r1b`` selects the
one-repetition lane (``nbldpc_formal_v7_r1b_mr1``); with
``--canary``/``--development`` the corresponding 4+4 canary / 16+16
development config is chosen.  ``--r2``/``--r3``/``--r1b`` are mutually
exclusive; ``--canary`` and ``--development`` are mutually exclusive.
"""
from __future__ import annotations
import argparse
import json
import sys

from ..formal_ir import nonbinary_v7_development as lane


def main():
    parser = argparse.ArgumentParser(
        description="NBLDPC v7 R1A/R1B/R2/R3 development harness (plan-first, engineering stage: never executes R2/R3 development)")
    parser.add_argument("action", nargs="?", default="plan",
                        choices=("plan", "execute", "verify"))
    parser.add_argument("--output", default=None,
                        help="explicit workspace directory for plan/verify (never the official root)")
    parser.add_argument("--canary", action="store_true",
                        help="use the sacrificed CANARY config (4+4 development frames, fresh roots)")
    parser.add_argument("--development", action="store_true",
                        help="use the DEVELOPMENT config (16+16 development frames, fresh roots)")
    parser.add_argument("--r1b", action="store_true",
                        help="use the R1B one-repetition lane (nbldpc_formal_v7_r1b_mr1)")
    parser.add_argument("--r2", action="store_true",
                        help="use the R2 QSC-DE lane (nbldpc_formal_v7_r2_qsc_de)")
    parser.add_argument("--r3", action="store_true",
                        help="use the R3 GF(32)xGF(32) multilevel lane (nbldpc_formal_v7_r3_gf32x2)")
    args = parser.parse_args()
    if args.canary and args.development:
        print("choose exactly one of --canary / --development", file=sys.stderr)
        raise SystemExit(2)
    if sum((args.r1b, args.r2, args.r3)) > 1:
        print("choose exactly one of --r1b / --r2 / --r3", file=sys.stderr)
        raise SystemExit(2)
    if args.r3:
        config = lane.CANARY_R3 if args.canary else lane.DEVELOPMENT_R3
    elif args.r2:
        config = lane.CANARY_R2 if args.canary else lane.DEVELOPMENT_R2
    elif args.r1b:
        config = lane.CANARY_R1B if args.canary else lane.DEVELOPMENT_R1B
    else:
        config = lane.CANARY if args.canary else lane.DEVELOPMENT
    if args.action == "execute":
        if args.r3 and not args.canary:
            # V7-32 second-half gate: R3 execute is a hard stop for every
            # DEVELOPMENT R3 config; only the sacrificed R3 CANARY may
            # execute (mirror of the R2 canary-only gate).
            print("R3 development execution is blocked; only the sacrificed R3 CANARY may execute",
                  file=sys.stderr)
            raise SystemExit(2)
        if args.r2 and not args.canary:
            print("R2 development execution is blocked; only the sacrificed R2 CANARY may execute",
                  file=sys.stderr)
            raise SystemExit(2)
        if not args.canary:
            print("development execution is not authorized before V7-12/V7-15 main-thread review",
                  file=sys.stderr)
            raise SystemExit(2)
        if args.output is None:
            print("canary execute requires --output DIR", file=sys.stderr)
            raise SystemExit(2)
        try:
            if args.r3:
                runner = lane.production_runner_r3
            elif args.r2:
                runner = lane.production_runner_r2
            elif args.r1b:
                runner = lane.production_runner_r1b
            else:
                runner = lane.production_runner
            print(json.dumps(lane.run(args.output, config=config, runner=runner,
                                      production_authorized=True), sort_keys=True))
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            raise SystemExit(2)
        return
    if args.action == "verify":
        if args.output is None:
            print("verify requires --output DIR", file=sys.stderr)
            raise SystemExit(2)
        print(json.dumps(lane.verify(args.output, config=config), sort_keys=True))
        return
    if args.output is None:
        print(json.dumps(lane.expected_plan(config), sort_keys=True))
        return
    try:
        plan = lane.create_plan(args.output, config=config,
                                production_authorized=args.canary)
        print(json.dumps({"created": str(args.output), "plan_sha256": lane._sha(
            lane._compact(plan))}, sort_keys=True))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
