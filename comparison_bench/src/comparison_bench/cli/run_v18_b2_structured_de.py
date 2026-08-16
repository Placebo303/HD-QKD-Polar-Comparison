"""CLI for V18-B2 structured DE prep (plan-only)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..formal_ir import nonbinary_v18_b2_structured_de as core


import json as _json
from pathlib import Path as _Path


def load_seed_lambda(path: str | None):
    if path is None:
        return None
    data = _json.loads(_Path(path).read_text(encoding="utf-8"))
    return {int(k): float(v) for k, v in data.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--mode", choices=("plan","smoke","search-smoke","real-search"), default="plan")
    ap.add_argument("--q-small", type=int, default=16)
    ap.add_argument("--rate", type=float, default=0.75)
    ap.add_argument("--pop-size", type=int, default=15)
    ap.add_argument("--max-gen", type=int, default=10)
    ap.add_argument("--n-samples", type=int, default=5000)
    ap.add_argument("--max-iter", type=int, default=50)
    ap.add_argument("--seed", type=int, default=2026081606)
    ap.add_argument("--seed-lambda-json", type=str, default=None,
                        help="Optional JSON file with a K-entry degree distribution to seed one DE population member")
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if args.mode == "real-search":
        w = core.build_folded_w(args.q_small)
        doc = core.run_structured_de_search(
            q=args.q_small, rate=args.rate, w=w, search_seed=args.seed,
            pop_size=args.pop_size, max_gen=args.max_gen, F=0.85, CR=0.7,
            n_samples=args.n_samples, max_iter=args.max_iter,
            seed_lambda=load_seed_lambda(args.seed_lambda_json), out_dir=out)
        print(json.dumps({"schema": doc["schema"], "q": doc["q"], "best": doc["best_objective"]}, sort_keys=True))
        return 0
    if args.mode == "search-smoke":
        doc = core.run_search_smoke(q=args.q_small, out_dir=out)
        print(json.dumps({"schema": doc["schema"], "q": doc["q"], "best": doc["best_objective"]}, sort_keys=True))
        return 0
    if args.mode == "smoke":
        doc = core.run_smoke(q=args.q_small, out_dir=out)
        print(json.dumps({"schema": doc["schema"], "q": doc["q"], "converged": doc["run"]["converged"]}, sort_keys=True))
        return 0
    plan = core.build_m2_plan(q_small=args.q_small)
    path = out / "m2_plan.json"
    if path.exists():
        print("m2_plan already exists; refusing overwrite", file=__import__("sys").stderr)
        return 2
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(plan, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
