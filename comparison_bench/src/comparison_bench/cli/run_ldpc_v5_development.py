"""Immutable v1 sacrificed-development package runner for binary LDPC v5.

Production entry point: prepare once, main-thread review, execute once.
Exposes no test switch; test execution lives in the private test suite with
explicit fakes and a test-owned workspace root.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from ..formal_ir.ldpc_v5_development import execute_plan, prepare_plan


def main() -> int:
    p = argparse.ArgumentParser(description="binary LDPC v5 sacrificed-development package runner")
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--mode", choices=("prepare", "execute"), required=True)
    p.add_argument("--partition-lock", type=Path)
    a = p.parse_args()
    if a.mode == "prepare":
        if a.partition_lock is None:
            p.error("--partition-lock required for prepare")
        prepare_plan(a.output_dir, a.partition_lock)
    else:
        execute_plan(a.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
