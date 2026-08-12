from __future__ import annotations
import argparse
from pathlib import Path
from ..formal_ir.real_qualification import make_lock, verify_lock
def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--source", default="comparison_bench/outputs_comparison/real_sidecars_frame_batch.parquet"); p.add_argument("--output-dir", default="comparison_bench/outputs_comparison/formal_ir_methods/20260725_v2_real_cascade"); p.add_argument("--final-ir-manifest", default="comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1/data_lock_manifest.json"); p.add_argument("--synthetic-report", default="comparison_bench/outputs_comparison/formal_ir_methods/20260725_v3_synthetic/formal_qualification_report.json"); p.add_argument("--verify", action="store_true"); a=p.parse_args()
    if a.verify: verify_lock(Path(a.output_dir)); print("verified")
    else: make_lock(Path(a.source), Path(a.output_dir), Path(a.final_ir_manifest), Path(a.synthetic_report)); print("locked")
    return 0
if __name__ == "__main__": raise SystemExit(main())
