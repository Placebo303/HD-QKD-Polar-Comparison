"""CLI for V11 deterministic parallel execution
(``formal-nonbinary-ldpc-v11-sc-de-gate``, AMEND-2026-08-06-02).

Engineering-only, non-scientific: runs the frozen microbenchmark #3 (same
synthetic configuration as #1/#2) through a ``multiprocessing`` worker pool
to measure parallel speedup and project the formal-matrix wall time.

Usage:
  python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v11_parallel \
      --microbench3 [--out-dir DIR] [--workers N]
  python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v11_parallel \
      --self-check
"""
from __future__ import annotations

import argparse
import json
import os
import uuid

from ..formal_ir import nonbinary_v11_microbench as mb
from ..formal_ir.nonbinary_v11_parallel import (
    DEFAULT_WORKERS,
    microbench3_run_specs,
    microbench3_serial_baseline,
    parallel_matrix_projection,
    run_parallel,
)


def _write_json(path: str, payload: dict) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--microbench3", action="store_true",
                        help="run parallel microbenchmark #3 and project")
    parser.add_argument("--self-check", action="store_true",
                        help="run the module self-check (tiny, no runs)")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help=f"worker count (default: {DEFAULT_WORKERS})")
    parser.add_argument("--out-dir", default=None,
                        help="write JSON evidence here (additive); default: "
                             "workspace/nbldpc_v11_parallel_<short-uuid>/")
    parser.add_argument("--no-warmup", action="store_true",
                        help="skip the numba warmup pass (debug)")
    args = parser.parse_args()

    if args.self_check:
        from ..formal_ir.nonbinary_v11_parallel import _self_check
        _self_check()
        raise SystemExit(0)

    if args.microbench3:
        if args.out_dir is None:
            args.out_dir = os.path.join(
                "workspace",
                f"nbldpc_v11_parallel_{uuid.uuid4().hex[:8]}")
        os.makedirs(args.out_dir, exist_ok=True)

        environment = mb.environment_info()

        # microbenchmark #3: 8 identical synthetic cells in parallel
        run_specs = microbench3_run_specs(args.out_dir)
        measurements, results, batch_wall = run_parallel(
            run_specs, args.workers, warmup=not args.no_warmup)

        # print per-run summary
        for m in measurements:
            print(f"{m['run_id']:14s} "
                  f"N={m['n_samples']:5d} w={m['w']} "
                  f"W={m['W']:3d} iter={m['iterations_executed']:3d} "
                  f"wall={m['wall_seconds']:.2f}s "
                  f"peak_rss={m['peak_rss_bytes'] / (1024**3):.3f} GiB")

        # load frozen #2 serial baseline for extrapolation
        baseline_path = os.path.join(
            "openspec", "changes", "formal-nonbinary-ldpc-v11-sc-de-gate",
            "evidence", "resource", "microbenchmark2.json")
        baseline = microbench3_serial_baseline(baseline_path)

        # parallel speedup: batch_wall / serial sum of same cells
        serial_cell_sum = baseline["serial_cell_sum_seconds"]
        parallel_speedup = serial_cell_sum / batch_wall if batch_wall > 0 else float("inf")

        # peak RSS: max across all parallel runs
        peak_rss = max(int(m["peak_rss_bytes"]) for m in measurements)

        projection = parallel_matrix_projection(
            serial_total_hours=baseline["serial_total_hours"],
            parallel_speedup=parallel_speedup,
            workers=args.workers,
            peak_rss_bytes=peak_rss,
            serial_cell_sum_seconds=serial_cell_sum,
            parallel_batch_wall_seconds=batch_wall)

        # build per-run measurement map
        measurement_map = {m["run_id"]: m for m in measurements}

        bundle = {
            "schema": "v11_parallel_microbench3_v1",
            "engineering_only_non_scientific": True,
            "amendment_ref": "AMEND-2026-08-06-02",
            "environment": environment,
            "workers": args.workers,
            "batch_wall_seconds": batch_wall,
            "serial_cell_sum_seconds": serial_cell_sum,
            "parallel_speedup": parallel_speedup,
            "measurements": measurement_map,
            "extrapolation": projection,
        }
        raw_path = os.path.join(args.out_dir, "microbench3_parallel_raw.json")
        _write_json(raw_path, bundle)

        summary = {
            "status": projection["status"],
            "workers": args.workers,
            "batch_wall_seconds": batch_wall,
            "serial_cell_sum_seconds": serial_cell_sum,
            "parallel_speedup": parallel_speedup,
            "predicted_parallel_wall_hours": projection["predicted_parallel_wall_hours"],
            "peak_rss_bytes": peak_rss,
            "rss_cap_bytes": projection["rss_cap_bytes"],
            "evidence_path": raw_path,
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        raise SystemExit(0)

    parser.print_help()
    raise SystemExit(1)


if __name__ == "__main__":
    main()
