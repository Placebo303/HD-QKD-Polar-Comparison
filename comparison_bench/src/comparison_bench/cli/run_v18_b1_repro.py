"""CLI for V18-B1 small-q DE reproduction smoke."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..formal_ir import nonbinary_v18_b1_repro as core


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("smoke",), default="smoke")
    ap.add_argument("--q", type=int, default=core.SMOKE_Q)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--seed", type=int, default=core.SMOKE_SEED)
    args = ap.parse_args()
    out = Path(args.out_dir)
    if out.exists() and any(out.iterdir()):
        print("out-dir must be empty/fresh", file=__import__("sys").stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    doc = core.run_smoke(q=args.q, out_dir=out, seed=args.seed)
    print(json.dumps({"schema": doc["schema"], "q": doc["q"], "mode": doc["mode"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
