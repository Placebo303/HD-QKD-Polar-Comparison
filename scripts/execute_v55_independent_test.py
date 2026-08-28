"""V55P0 guarded two-stage rescue independent TEST: 180-360 decoder calls conditional.

Formal CLI for change ``formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation`` (cycle V55P0).
Mandatory ``--execution-authorized`` plus explicit ``--authorized-target-sha`` required.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comparison_bench/src"))

from comparison_bench.formal_ir.v55_two_stage_rescue_independent_test import (  # noqa: E402
    OUTPUT_ROOT,
    IntegrityFailure,
    run_v55_diagnostic,
)


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the guarded V55P0 two-stage rescue independent TEST (hard cap 360 total 90 L1+90 base+≤90 stage1+≤90 stage2).")
    parser.add_argument("--execution-authorized", action="store_true", help="Required explicit authorization flag for the single diagnostic run (scope v55_two_stage_rescue_independent_test_90_blocks_triple_exactly_once_authoritative).")
    parser.add_argument("--authorized-target-sha", default=None, help="Full implementation SHA bound by the user EXECUTE_AUTH (exact equality with HEAD and origin/formal-ir-mainline is enforced).")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.execution_authorized:
        print("BLOCKED: EXECUTE_NOT_AUTHORIZED — pass --execution-authorized with --authorized-target-sha per the accepted plan and explicit user EXECUTE_AUTH (scope v55_two_stage_rescue_independent_test_90_blocks_triple_exactly_once_authoritative).", file=sys.stderr)
        return 2
    if not args.authorized_target_sha:
        print("BLOCKED: --authorized-target-sha is required together with --execution-authorized (R14 exact SHA binding; scope v55_two_stage_rescue_independent_test_90_blocks_triple_exactly_once_authoritative).", file=sys.stderr)
        return 2
    try:
        results = run_v55_diagnostic(execution_authorized=True, authorized_target_sha=args.authorized_target_sha, fake_runner=False, output_root=OUTPUT_ROOT)
    except IntegrityFailure as exc:
        print(f"BLOCKED: integrity failure {exc}", file=sys.stderr)
        return 2
    except PermissionError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    except FileExistsError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    except BaseException as exc:
        print(f"INTERRUPTED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(f"V55P0 additive evidence written to {results['output_root']}")
    print(f"Terminal state: {results['terminal_state']}")
    if results.get("summary"):
        s = results['summary']
        print(f"base_exact {s['counts']['base_exact_full']} verify_base {s['counts']['verify_base']} stage1_call {s['counts']['stage1_call_exact_full']} stage1_final {s['counts']['stage1_final_exact_full_count']} final {s['counts']['final_exact_full_count']} undetected {s['counts']['undetected_accepted_wrong']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
