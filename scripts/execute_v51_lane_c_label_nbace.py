"""V51P0 guarded Lane C label-only paired runner: exactly 45 decoder calls conditional.

Formal CLI for change ``formal-ir-v51-lane-c-label-nbace`` (cycle V51P0).
Mandatory ``--execution-authorized`` plus explicit ``--authorized-target-sha`` required.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comparison_bench/src"))

from comparison_bench.formal_ir.v51_lane_c_label_nbace import (  # noqa: E402
    OUTPUT_ROOT,
    IntegrityFailure,
    run_v51_diagnostic,
)


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the guarded V51P0 Lane C label-only paired diagnostic (hard cap 45 decoder calls; scope v51_lane_c_label_nbace_45_calls_paired_exactly_once).")
    parser.add_argument("--execution-authorized", action="store_true", help="Required explicit authorization flag for the single diagnostic run (scope v51_lane_c_label_nbace_45_calls_paired_exactly_once).")
    parser.add_argument("--authorized-target-sha", default=None, help="Full implementation SHA bound by the user EXECUTE_AUTH (exact equality with HEAD and origin/formal-ir-mainline is enforced).")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.execution_authorized:
        print("BLOCKED: EXECUTE_NOT_AUTHORIZED — pass --execution-authorized with --authorized-target-sha per the accepted plan and explicit user EXECUTE_AUTH (scope v51_lane_c_label_nbace_45_calls_paired_exactly_once).", file=sys.stderr)
        return 2
    if not args.authorized_target_sha:
        print("BLOCKED: --authorized-target-sha is required together with --execution-authorized (R14 exact SHA binding; scope v51_lane_c_label_nbace_45_calls_paired_exactly_once).", file=sys.stderr)
        return 2
    try:
        results = run_v51_diagnostic(execution_authorized=True, authorized_target_sha=args.authorized_target_sha, fake_runner=False, output_root=OUTPUT_ROOT)
    except IntegrityFailure as exc:
        print(f"BLOCKED: integrity failure {exc}", file=sys.stderr)
        return 2
    except PermissionError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    except FileExistsError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(f"V51P0 additive evidence written to {results['output_root']}")
    print(f"Terminal state: {results['terminal_state']}")
    if results.get("terminal_reason"):
        print(f"Terminal reason: {results['terminal_reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
