from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ..metrics.summary import summarize_methods


def main() -> int:
    ap = argparse.ArgumentParser(description="Summarize comparison benchmark methods.")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    df = pd.read_csv(args.input)
    summary = summarize_methods(df)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out, index=False)
    print(f"wrote summary: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
