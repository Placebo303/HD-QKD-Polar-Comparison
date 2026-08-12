from __future__ import annotations
import argparse
from pathlib import Path
from ..formal_ir.real_qualification import run_locked, verify_run
def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--output-dir", default="comparison_bench/outputs_comparison/formal_ir_methods/20260725_v2_real_cascade"); p.add_argument("--verify", action="store_true"); a=p.parse_args()
    (verify_run if a.verify else run_locked)(Path(a.output_dir)); print("verified" if a.verify else "completed"); return 0
if __name__ == "__main__": raise SystemExit(main())
