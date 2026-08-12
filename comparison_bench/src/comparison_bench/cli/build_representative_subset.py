from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

def main() -> int:
    ap = argparse.ArgumentParser(description="Build representative real-frame subset.")
    ap.add_argument("--input", default="comparison_bench/outputs_comparison/real_sidecars_frame_batch.parquet")
    ap.add_argument("--output", default="comparison_bench/outputs_comparison/real_ir_success_first/representative_subset.parquet")
    args = ap.parse_args()
    
    in_path = Path(args.input)
    out_path = Path(args.output)
    
    if not in_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {in_path}")
        
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.read_parquet(in_path)
    
    # Selected dataset IDs
    selected_ids = [
        "real_typeii_20db_d8_bw180_blk0",
        "real_typeii_20db_d8_bw120_blk0",
        "real_typeii_20db_d8_bw50_blk0",
        "real_typeii_20db_d16_bw180_blk0",
        "real_typeii_20db_d16_bw100_blk0",
        "real_typeii_20db_d16_bw60_blk0"
    ]
    
    filtered_df = df[df["dataset_id"].isin(selected_ids)].copy()
    
    # Save output
    filtered_df.to_parquet(out_path, index=False)
    print(f"wrote representative subset to {out_path}")
    print(f"rows: {len(filtered_df)}, datasets: {filtered_df['dataset_id'].nunique()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
