"""CLI for V18-B2 structured DE prep (plan-only)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..formal_ir import nonbinary_v18_b2_structured_de as core


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--mode", choices=("plan","smoke"), default="plan")
    ap.add_argument("--q-small", type=int, default=16)
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
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
