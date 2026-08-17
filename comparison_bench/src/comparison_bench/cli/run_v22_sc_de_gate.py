"""V22 SC-LDPC DE gate CLI (diagnostic)."""
from __future__ import annotations

import argparse
import json

from ..formal_ir.nonbinary_v22_sc_de_gate import run_v22_sc_de_gate


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--q", type=int, default=1024)
    ap.add_argument("--p", type=float, required=True)
    ap.add_argument("--n-samples", type=int, default=200)
    ap.add_argument("--max-iter", type=int, default=20)
    ap.add_argument("--seed", type=int, default=2026095001)
    args = ap.parse_args()
    doc = run_v22_sc_de_gate(q=args.q, p=args.p, n_samples=args.n_samples,
                             max_iter=args.max_iter, seed=args.seed,
                             out_dir=args.out_dir)
    print(json.dumps({k: v for k, v in doc.items() if k != "rows"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
