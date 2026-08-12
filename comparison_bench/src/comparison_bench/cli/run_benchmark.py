from __future__ import annotations

import argparse
from pathlib import Path

from ..pipeline.run_ir_benchmark import benchmark_from_yaml


def main() -> int:
    ap = argparse.ArgumentParser(description="Run comparison IR benchmark from YAML config.")
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    result_df, frame_df = benchmark_from_yaml(Path(args.config))
    print(f"benchmark rows: {len(result_df)}")
    print(f"frame rows: {len(frame_df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
