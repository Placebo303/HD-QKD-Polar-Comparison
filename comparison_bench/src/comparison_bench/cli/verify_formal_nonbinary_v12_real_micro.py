"""Read-only verifier CLI for a V12 nonbinary LDPC real micro-feasibility
package.

Strict and decoder-free: verifies the exact seven-artifact contract, the
exclusion inventory, the partition lock, the plan bindings, the per-row
public syndrome/tag/leakage reconstruction, the transcript, the run manifest,
the gate and the terminal state without importing or calling any decoder.
Never writes to the package.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from ..formal_ir import nonbinary_v12_real_micro as core


def verify_output(output_dir: Path, *, _private_test_only: bool = False) -> dict[str, Any]:
    """Strict read-only verification of a V12 real micro package."""
    return core.verify(output_dir, _test_only=_private_test_only)


def main() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(message)s")
    parser = argparse.ArgumentParser(
        description="read-only decoder-free verifier for a V12 real micro package")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(core._compact(verify_output(args.output_dir)).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
