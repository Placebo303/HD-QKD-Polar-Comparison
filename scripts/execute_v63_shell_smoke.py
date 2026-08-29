"""V63 smoke (9 blocks) guarded runner — DECODE_FORBIDDEN until EXECUTE_AUTH."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comparison_bench/src"))

def _parse_args(argv: Iterable[str] | None = None):
    p = argparse.ArgumentParser(description="V63 smoke 9 blocks (INTEGRATION_REPLAY_SMOKE) — requires --execution-authorized")
    p.add_argument("--execution-authorized", action="store_true", help="Required explicit authorization")
    p.add_argument("--authorized-target-sha", default=None, help="Full implementation SHA")
    p.add_argument("--fake", action="store_true", help="Use fake runner (decoder-free, for T tests)")
    return p.parse_args(argv)

def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.execution_authorized:
        print("BLOCKED: EXECUTE_NOT_AUTHORIZED — pass --execution-authorized with --authorized-target-sha (V63 smoke 9 blocks).", file=sys.stderr)
        return 2
    if not args.authorized_target_sha:
        print("BLOCKED: --authorized-target-sha required with --execution-authorized (V63 smoke).", file=sys.stderr)
        return 2
    # In this phase smoke execution is DECODE_FORBIDDEN beyond fake; real decode not implemented here
    if args.fake:
        print(f"V63 smoke fake run authorized at {args.authorized_target_sha} — no decoder executed (DECODE_FORBIDDEN guard exercised)")
        return 0
    print("BLOCKED: DECODE_FORBIDDEN — real V63 smoke decoder requires future IMPLEMENTATION SHA binding + independent ACCEPT (not authorized in this phase).", file=sys.stderr)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
