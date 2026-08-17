"""V22 structured DE gate CLI (diagnostic)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from ..formal_ir.nonbinary_v18_b2_structured_de import build_folded_w, build_real_w_q1024
from ..formal_ir.nonbinary_v22_de_gate import run_v22_de_gate


def _load_candidates(path: str) -> list[dict[int, float]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return [{int(k): float(v) for k, v in data.items()}]
    if isinstance(data, list):
        return [{int(k): float(v) for k, v in item.items()} for item in data]
    raise ValueError("candidate JSON must be a mapping or list of mappings")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--q", type=int, default=1024)
    ap.add_argument("--rate", type=float, required=True)
    ap.add_argument("--n-samples", type=int, default=800)
    ap.add_argument("--max-iter", type=int, default=30)
    ap.add_argument("--seed", type=int, default=2026092001)
    ap.add_argument("--candidate-json", required=True)
    args = ap.parse_args()

    if args.q == 1024:
        w = np.asarray(build_real_w_q1024(), dtype=np.float64)
    else:
        w = np.asarray(build_folded_w(args.q), dtype=np.float64)
    candidates = _load_candidates(args.candidate_json)
    doc = run_v22_de_gate(q=args.q, w=w, rate=args.rate,
                          candidates=candidates,
                          n_samples=args.n_samples, max_iter=args.max_iter,
                          seed=args.seed, out_dir=args.out_dir)
    print(json.dumps({k: v for k, v in doc.items() if k != "candidates"},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
