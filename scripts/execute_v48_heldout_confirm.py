"""V48P0 guarded held-out confirm runner: exactly 90 decoder calls.

Formal CLI for change ``formal-ir-v48-heldout-confirm`` (cycle V48P0).
Mandatory ``--execution-authorized`` plus explicit ``--authorized-target-sha`` required.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comparison_bench/src"))

from comparison_bench.formal_ir.v48_heldout_confirm import (  # noqa: E402
    OUTPUT_ROOT,
    IntegrityFailure,
    run_v48_diagnostic,
)


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the guarded V48P0 held-out confirm diagnostic (hard cap 90 decoder calls; scope v48_diagnostic_90_invocations_heldout_exactly_once).")
    parser.add_argument("--execution-authorized", action="store_true", help="Required explicit authorization flag for the single diagnostic run (scope v48_diagnostic_90_invocations_heldout_exactly_once).")
    parser.add_argument("--authorized-target-sha", default=None, help="Full implementation SHA bound by the user EXECUTE_AUTH (exact equality with HEAD and origin/formal-ir-mainline is enforced).")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.execution_authorized:
        print("BLOCKED: EXECUTE_NOT_AUTHORIZED — pass --execution-authorized with --authorized-target-sha per the accepted plan and explicit user EXECUTE_AUTH (scope v48_diagnostic_90_invocations_heldout_exactly_once).", file=sys.stderr)
        return 2
    if not args.authorized_target_sha:
        print("BLOCKED: --authorized-target-sha is required together with --execution-authorized (R14 exact SHA binding; scope v48_diagnostic_90_invocations_heldout_exactly_once).", file=sys.stderr)
        return 2
    try:
        results = run_v48_diagnostic(execution_authorized=True, authorized_target_sha=args.authorized_target_sha, fake_runner=False, output_root=OUTPUT_ROOT)
    except IntegrityFailure as exc:
        print(f"BLOCKED: integrity failure {exc}", file=sys.stderr)
        return 2
    except PermissionError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    except FileExistsError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(f"V48P0 additive evidence written to {results['output_root']}")
    print(f"Terminal state: {results['terminal_state']}")
    if results.get("terminal_reason"):
        print(f"Terminal reason: {results['terminal_reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
