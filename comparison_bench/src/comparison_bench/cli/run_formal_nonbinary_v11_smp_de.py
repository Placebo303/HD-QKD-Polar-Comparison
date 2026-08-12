"""CLI for the V11 paper-faithful SMP-DE reference reproduction
(``formal-nonbinary-ldpc-v11-sc-de-gate``, Stage E / R1).

Usage:
  python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v11_smp_de \
      --q 4 --mode uncoupled [--W 30] [--p-tol 0.001] [--out-dir DIR] [--trace]
  python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v11_smp_de \
      --reproduce [--out-dir DIR] [--traces]
  python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v11_smp_de \
      --self-check

``--reproduce`` runs the four frozen (q, mode) reference cases and writes a
JSON evidence bundle (full traces, search probes, reproduced vs published
values, deviations, per-case pass/fail and the overall status
``reproduce_pass`` / ``failed_reference``) to ``--out-dir``.
"""
from __future__ import annotations

import argparse
import json
import os

from ..formal_ir import nonbinary_v11_smp_de as v11


def _write_json(path: str, payload: dict) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reproduce", action="store_true",
                        help="run the four frozen (q, mode) reference cases")
    parser.add_argument("--self-check", action="store_true",
                        help="run the module self-check (all four cases)")
    parser.add_argument("--q", type=int, choices=(4, 16), default=4)
    parser.add_argument("--mode", choices=("uncoupled", "coupled"), default="uncoupled")
    parser.add_argument("--W", type=int, default=v11.W_FROZEN)
    parser.add_argument("--p-tol", type=float, default=v11.SEARCH_P_TOL)
    parser.add_argument("--max-iter", type=int, default=3000)
    parser.add_argument("--conv-tol", type=float, default=1e-8)
    parser.add_argument("--streak", type=int, default=5)
    parser.add_argument("--traces", action="store_true",
                        help="include per-iteration traces in --reproduce output")
    parser.add_argument("--out-dir", default=None,
                        help="directory for the JSON evidence bundle")
    args = parser.parse_args()

    if args.self_check:
        result = v11.reproduce_ben_yacoub_2019(
            W=args.W, p_tol=args.p_tol, max_iter=args.max_iter,
            conv_tol=args.conv_tol, streak=args.streak, include_traces=False)
        print(json.dumps({key: value for key, value in result.items()
                          if key != "cases"}, indent=2, sort_keys=True))
        for case in result["cases"]:
            print(f"q={case['q']} {case['mode']:9s} reproduced={case['reproduced']:.4f} "
                  f"published={case['published']:.4f} dev={case['deviation']:.6f} "
                  f"pass={case['pass']}")
        raise SystemExit(0 if result["status"] == "reproduce_pass" else 1)

    if args.reproduce:
        result = v11.reproduce_ben_yacoub_2019(
            W=args.W, p_tol=args.p_tol, max_iter=args.max_iter,
            conv_tol=args.conv_tol, streak=args.streak,
            include_traces=args.traces)
        if args.out_dir is None:
            args.out_dir = "."
        _write_json(os.path.join(args.out_dir, "smp_de_trace.json"), result)
        print(json.dumps({"status": result["status"],
                          "reproduced": {f"q{case['q']}_{case['mode']}": case["reproduced"]
                                         for case in result["cases"]},
                          "published": {f"q{case['q']}_{case['mode']}": case["published"]
                                        for case in result["cases"]},
                          "deviations": {f"q{case['q']}_{case['mode']}": case["deviation"]
                                         for case in result["cases"]},
                          "pass": {f"q{case['q']}_{case['mode']}": case["pass"]
                                   for case in result["cases"]}},
                         indent=2, sort_keys=True))
        raise SystemExit(0 if result["status"] == "reproduce_pass" else 1)

    # single (q, mode) threshold search with a full trace
    search = v11.threshold_binary_search(
        args.q, v11.REPRODUCTION_DV, v11.REPRODUCTION_DC, args.mode,
        W=args.W, p_tol=args.p_tol, max_iter=args.max_iter,
        conv_tol=args.conv_tol, streak=args.streak)
    print(json.dumps(search, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
