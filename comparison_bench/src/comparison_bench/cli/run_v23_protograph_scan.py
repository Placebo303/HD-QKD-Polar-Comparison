"""V23 protograph DE scan CLI (diagnostic)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..formal_ir.nonbinary_v23_protograph import run_protograph_de_scan


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--matrices-json", required=True,
                    help="JSON list of base matrices (each is list of rows of ints)")
    ap.add_argument("--q", type=int, default=1024)
    ap.add_argument("--n-samples", type=int, default=200)
    ap.add_argument("--max-iter", type=int, default=50)
    ap.add_argument("--seed", type=int, default=2026099001)
    ap.add_argument("--degree-max", type=int, default=512)
    args = ap.parse_args()
    matrices = json.loads(Path(args.matrices_json).read_text(encoding="utf-8"))
    doc = run_protograph_de_scan(q=args.q, base_matrices=matrices,
                                 n_samples=args.n_samples,
                                 max_iter=args.max_iter, seed=args.seed,
                                 degree_max=args.degree_max,
                                 out_dir=args.out_dir)
    print(json.dumps({k: v for k, v in doc.items() if k != "rows"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
