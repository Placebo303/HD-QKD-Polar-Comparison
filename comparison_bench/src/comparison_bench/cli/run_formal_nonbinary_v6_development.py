"""Development-only CLI for the NBLDPC v6 long-block engineering lane.

The default action is plan preparation, never execution:

- ``plan`` (default) prepares the frozen development plan; without
  ``--output`` it prints the in-memory plan preview, with ``--output DIR`` it
  writes ``pre_run_plan.json`` into an explicit (workspace) directory.  The
  official development root under
  ``comparison_bench/outputs_comparison/formal_ir_methods/`` is locked until
  the V6-50 main-thread review, so it is never created here.
- ``verify`` is read-only and requires ``--output DIR``.
- ``execute`` is a hard stop for ``CONFIG``: production development execution
  requires a separately reviewed plan (V6-50) and is never invoked for the
  official config.  The single V6-51 exception is ``--canary``: ``execute``
  is then allowed only together with ``--output DIR`` and runs the sacrificed
  4+4-frame CANARY plan through the explicit production runner into that
  non-official workspace directory.  ``--canary`` also switches ``plan`` and
  ``verify`` to the CANARY config.
"""
from __future__ import annotations
import argparse
import json
import sys

from ..formal_ir import nonbinary_v6_development as lane


def main():
    parser = argparse.ArgumentParser(
        description="NBLDPC v6 long-block development harness (plan-first, never executes)")
    parser.add_argument("action", nargs="?", default="plan",
                        choices=("plan", "execute", "verify"))
    parser.add_argument("--output", default=None,
                        help="explicit workspace directory for plan/verify (never the official root)")
    parser.add_argument("--canary", action="store_true",
                        help="use the sacrificed CANARY config (4+4 development frames, fresh roots)")
    args = parser.parse_args()
    config = lane.CANARY if args.canary else lane.CONFIG
    if args.action == "execute":
        if not args.canary:
            print("development execution is not authorized before V6-50 main-thread review",
                  file=sys.stderr)
            raise SystemExit(2)
        if args.output is None:
            print("canary execute requires --output DIR", file=sys.stderr)
            raise SystemExit(2)
        print(json.dumps(lane.run(args.output, config=config, runner=lane.production_runner,
                                  production_authorized=True), sort_keys=True))
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
    plan = lane.create_plan(args.output, config=config)
    print(json.dumps({"created": str(args.output), "plan_sha256": lane._sha(
        lane._compact(plan))}, sort_keys=True))


if __name__ == "__main__":
    main()
