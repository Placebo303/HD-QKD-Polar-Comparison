"""CLI for the V11 Stage M resource microbenchmark
(``formal-nonbinary-ldpc-v11-sc-de-gate``, design.md §5 Stage M, V11-30.1).

Engineering-only, non-gating: small q=1024 coupled MC-DE runs with a
synthetic non-gating distribution; measures per-iteration wall clock,
per-sample-per-iteration cost and process-tree peak RSS; extrapolates the
frozen formal matrix with explicit conservative assumptions and returns
``resource_ok`` / ``resource_blocked`` (design.md:92-95).  No threshold,
winner, gate or any scientific claim is made.  The formal matrix size is
frozen (2x3x5x2) and is never shrunk here.

Usage:
  python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v11_microbench \
      --run [--out-dir DIR]
  python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v11_microbench \
      --self-check
"""
from __future__ import annotations

import argparse
import json
import os
import uuid

from ..formal_ir import nonbinary_v11_microbench as mb


def _write_json(path: str, payload: dict) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true",
                        help="run the microbenchmark cells and extrapolate")
    parser.add_argument("--self-check", action="store_true",
                        help="run the module self-check (tiny, no runs)")
    parser.add_argument("--out-dir", default=None,
                        help="write JSON evidence here (additive); default: "
                             "workspace/nbldpc_v11_microbench_<short-uuid>/")
    parser.add_argument("--watcher-interval", type=float, default=1.0,
                        help="RSS watcher sampling interval in seconds")
    args = parser.parse_args()

    if args.self_check:
        mb._self_check()
        raise SystemExit(0)

    if args.run:
        environment = mb.environment_info()
        measurements = {}
        for cell in mb.MICRO_CELLS:
            measurement = mb.run_cell(cell, watcher_interval=args.watcher_interval)
            measurements[measurement["label"]] = measurement
            print(f"{measurement['label']:10s} "
                  f"N={measurement['n_samples']:5d} w={measurement['w']} "
                  f"W={measurement['W']:3d} iter={measurement['iterations_executed']:3d} "
                  f"per_iter={measurement['per_iteration_seconds']:.4f}s "
                  f"per_sample_per_iter={measurement['per_sample_per_iteration_seconds']:.6f}s "
                  f"peak_rss={measurement['peak_rss_bytes'] / (1024**3):.3f} GiB")
        projection = mb.extrapolate_formal_matrix(measurements)
        bundle = {
            "schema": "v11_microbenchmark_v1",
            "engineering_only_non_scientific": True,
            "environment": environment,
            "measurements": measurements,
            "extrapolation": projection,
        }
        if args.out_dir is None:
            args.out_dir = os.path.join("workspace",
                                        f"nbldpc_v11_microbench_{uuid.uuid4().hex[:8]}")
        raw_path = os.path.join(args.out_dir, "microbenchmark_raw.json")
        _write_json(raw_path, bundle)
        summary = {
            "status": projection["status"],
            "total_wall_hours": projection["total_wall_hours"],
            "wall_limit_hours": projection["wall_limit_seconds"] / 3600.0,
            "peak_rss_bytes": projection["peak_rss_bytes"],
            "rss_cap_bytes": projection["rss_cap_bytes"],
            "n_runs_total": projection["n_runs_total"],
            "evidence_path": raw_path,
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        raise SystemExit(0)

    parser.print_help()
    raise SystemExit(1)


if __name__ == "__main__":
    main()
