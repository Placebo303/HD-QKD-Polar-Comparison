"""Immutable v1 fresh synthetic qualification package runner for binary LDPC v5.

Production entry point: prepare once, main-thread review, execute once.
Exposes no test switch; test execution lives in the private test suite with
explicit fakes and a test-owned workspace root.
"""
from __future__ import annotations
import argparse, logging, sys
from pathlib import Path
from ..formal_ir.ldpc_v5_synthetic_qualification import execute_plan, prepare_plan


def main() -> int:
    # Progress logs go to stderr; stdout stays reserved for canonical output.
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(description="binary LDPC v5 synthetic qualification package runner")
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--mode", choices=("prepare", "execute"), required=True)
    p.add_argument("--development-dir", type=Path)
    a = p.parse_args()
    if a.mode == "prepare":
        if a.development_dir is None:
            p.error("--development-dir required for prepare")
        prepare_plan(a.output_dir, a.development_dir)
    else:
        execute_plan(a.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
