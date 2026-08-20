"""Production entry point for the frozen V30R gate.

The CLI intentionally exposes no tuning, input-path, seed, degree, matrix, or
decoder options.  It accepts only a new additive evidence root and delegates
all frozen choices to :func:`nonbinary_v30.run_v30r_gate`.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..formal_ir.nonbinary_v30 import run_v30r_gate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_nonbinary_v30_gate")
    parser.add_argument("output_root", help="new additive V30R evidence directory")
    args = parser.parse_args(argv)
    root = Path(args.output_root)
    if root.exists():
        parser.error(f"output root already exists; choose a new additive root: {root}")
    result = run_v30r_gate(root)
    print(json.dumps({"status": result["status"], "evidence_root": result["evidence_root"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
