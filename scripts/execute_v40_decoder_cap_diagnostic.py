"""V40P0 guarded decoder-cap diagnostic runner: 12 + conditional 12 + conditional 6 calls.

Formal CLI for change ``formal-ir-v40-decoder-cap-diagnostic`` (cycle V40P0).
The mandatory ``--execution-authorized`` flag plus an explicit
``--authorized-target-sha`` (bound by user EXECUTE_AUTH to scope
``v40_decoder_only_max30_calls_exactly_once``) are required. There is no
fake-runner option; the production path always binds ``fake_runner=False``
and writes only the fixed additive run root.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comparison_bench/src"))

from comparison_bench.formal_ir.v40_decoder_cap_diagnostic import (  # noqa: E402
    OUTPUT_ROOT,
    IntegrityFailure,
    run_v40_diagnostic,
)


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the guarded V40P0 decoder-cap diagnostic (hard cap 30 real decoder calls)."
    )
    parser.add_argument(
        "--execution-authorized",
        action="store_true",
        help="Required explicit authorization flag for the single diagnostic run.",
    )
    parser.add_argument(
        "--authorized-target-sha",
        default=None,
        help="Full implementation SHA bound by the user EXECUTE_AUTH (exact equality "
        "with HEAD and origin/formal-ir-mainline is enforced).",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.execution_authorized:
        print(
            "BLOCKED: EXECUTE_NOT_AUTHORIZED — pass --execution-authorized "
            "with --authorized-target-sha per the accepted plan and explicit user EXECUTE_AUTH.",
            file=sys.stderr,
        )
        return 2
    if not args.authorized_target_sha:
        print(
            "BLOCKED: --authorized-target-sha is required together with "
            "--execution-authorized (R16 exact SHA binding).",
            file=sys.stderr,
        )
        return 2

    try:
        results = run_v40_diagnostic(
            execution_authorized=True,
            authorized_target_sha=args.authorized_target_sha,
            fake_runner=False,
            output_root=OUTPUT_ROOT,
        )
    except IntegrityFailure as exc:
        print(f"BLOCKED: integrity failure {exc}", file=sys.stderr)
        return 2

    print(f"V40P0 additive evidence written to {results['output_root']}")
    print(f"Terminal state: {results['terminal_state']}")
    if results.get("terminal_reason"):
        print(f"Terminal reason: {results['terminal_reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
