"""Read-only verifier CLI for a V13 six-file diagnostic package
(``formal-nonbinary-ldpc-v13-existing-data-diagnostics``).

Strict and decoder-free: verifies the six-file artifact contract, the role
ledger, the aggregate-only channel diagnostics, the outcome CSV, the decoder
telemetry JSONL and the manifest cross-bindings without importing or calling
any decoder and without touching a real source loader.  Never writes to the
package.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ..formal_ir import nonbinary_v13_diagnostics as core


def verify_output(output_dir: Path, *, _private_test_only: bool = False) -> dict:
    """Strict read-only verification of a V13 diagnostic package."""
    return core.verify_package(output_dir, _private_test_only=_private_test_only)


def main() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(message)s")
    parser = argparse.ArgumentParser(
        description="read-only decoder-free verifier for a V13 six-file diagnostic package")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify_output(args.output_dir)
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(core._compact(result).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
