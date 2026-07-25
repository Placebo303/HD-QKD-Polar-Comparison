from __future__ import annotations

import argparse
import numpy as np
import pandas as pd
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser(description="Generate synthetic paired symbols.")
    ap.add_argument("--output", required=True)
    ap.add_argument("--dimension", type=int, required=True)
    ap.add_argument("--frame-len-symbols", type=int, required=True)
    ap.add_argument("--n-frames", type=int, default=8)
    ap.add_argument("--ser", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    q = args.dimension
    flen = args.frame_len_symbols
    n_total = flen * args.n_frames
    
    rng = np.random.default_rng(args.seed)
    
    alice = rng.integers(0, q, size=n_total, dtype=np.int64)
    bob = alice.copy()
    
    # Flip symbols with probability ser
    flip = rng.random(n_total) < args.ser
    if np.any(flip):
        n_flip = np.count_nonzero(flip)
        # Offset Bob symbol by a random non-zero value mod q
        offsets = rng.integers(1, q, size=n_flip, dtype=np.int64)
        bob[flip] = (alice[flip] + offsets) % q
        
    df = pd.DataFrame({
        "frame_id": np.repeat(np.arange(args.n_frames), flen),
        "pair_idx": np.tile(np.arange(flen), args.n_frames),
        "alice_symbol": alice,
        "bob_symbol": bob,
        "dimension": q,
        "frame_len_symbols": flen
    })
    
    df.to_csv(out_path, index=False)
    print(f"wrote synthetic pairs to {out_path}, rows: {len(df)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
