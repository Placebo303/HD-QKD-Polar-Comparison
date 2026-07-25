from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
from ..io.dataset_builder import build_frame_batch, frame_batch_to_table

def main() -> int:
    ap = argparse.ArgumentParser(description="Regroup representative subset into longer frames.")
    ap.add_argument("--input", default="comparison_bench/outputs_comparison/real_ir_success_first/representative_subset.parquet")
    ap.add_argument("--flen", type=int, required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    
    in_path = Path(args.input)
    out_path = Path(args.output)
    
    if not in_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {in_path}")
        
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.read_parquet(in_path)
    
    tables = []
    # Group by dataset_id and build new frame batch for each
    for ds_id, group in df.groupby("dataset_id"):
        dim = int(group["dimension"].iloc[0])
        # We need to sort by the original frame_id and pair_idx to keep symbol order correct
        work = group.sort_values(["frame_id", "pair_idx"]).reset_index(drop=True)
        batch = build_frame_batch(work, ds_id, dim, args.flen)
        tables.append(frame_batch_to_table(batch))
        
    out_df = pd.concat(tables, ignore_index=True)
    out_df.to_parquet(out_path, index=False)
    print(f"wrote long frames (len={args.flen}) to {out_path}, rows: {len(out_df)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
