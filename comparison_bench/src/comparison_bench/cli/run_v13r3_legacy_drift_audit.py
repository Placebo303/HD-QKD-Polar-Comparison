"""CLI for V13 R3 legacy drift audit
(``formal-nonbinary-ldpc-v13-r3-legacy-drift-audit``).

- ``execute`` — run the frozen R3 candidate once on the first 64 complete
  frames of each declared legacy parquet and write one additive package.
  Production requires ``--authorized --production`` (main-thread
  authorization) and a fresh ``--output`` root.
- ``verify`` — read-only package verification; changes no bytes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..formal_ir import nonbinary_v13r3_legacy_audit as core


def main() -> int:
    parser = argparse.ArgumentParser(
        description="V13 R3 legacy drift audit (execute / verify)")
    parser.add_argument("action", choices=("execute", "verify"))
    parser.add_argument("--parquet", action="append", default=None,
                        help="legacy pairs parquet path (repeatable, execute only)")
    parser.add_argument("--output", default=None,
                        help="output root (fresh additive root for execute)")
    parser.add_argument("--run-id", default=core.RUN_ID)
    parser.add_argument("--authorized", action="store_true",
                        help="explicit main-thread authorization for production execute")
    parser.add_argument("--production", action="store_true",
                        help="explicit production-lane flag for execute")
    args = parser.parse_args()

    if args.action == "verify":
        if args.output is None:
            print("--output DIR is required", file=sys.stderr)
            return 2
        out = Path(args.output)
        if not out.exists():
            print("output root not found", file=sys.stderr)
            return 2
        try:
            result = core.verify_package(out)
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, sort_keys=True))
        return 0 if result["ok"] else 2

    if not args.authorized or not args.production:
        print("V13 R3 legacy drift audit production execute requires the explicit "
              "--authorized --production flags (main-thread authorization)",
              file=sys.stderr)
        return 2
    if args.output is None:
        print("--output DIR is required", file=sys.stderr)
        return 2
    if not args.parquet:
        print("at least one --parquet PATH is required", file=sys.stderr)
        return 2
    out = Path(args.output)
    if out.exists():
        print("fresh additive output root required", file=sys.stderr)
        return 2
    try:
        result = core.run_audit(out, parquet_paths=args.parquet,
                                run_id=args.run_id, command=" ".join(sys.argv),
                                production_authorized=True)
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
