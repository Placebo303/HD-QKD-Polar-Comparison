"""CLI for the V11 full-vector spatially coupled MC-DE kernel
(``formal-nonbinary-ldpc-v11-sc-de-gate``, Stage E engineering, V11-20.1).

Engineering scope ONLY: kernel self-check, the frozen G1-G3 rate-contract
check, and small deterministic dry runs.  The G1-G3 scientific matrix is
V11-40.2 and requires the frozen formal plan — it is NOT run here.

Usage:
  python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v11_mcde \
      --self-check
  python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v11_mcde \
      --rate-check
  python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v11_mcde \
      --dry-run [--q 8] [--L 4] [--w 1] [--W 4] [--n-samples 200] [--max-iter 5] \
      [--p 0.15] [--stratum S1|S3] [--lambda-json FILE] [--seed N] [--out-dir DIR]

The dry-run lambda defaults to the frozen V10 S1 winner (V11-A06, reused
without optimization); ``--stratum`` selects the frozen S3 winner and
``--lambda-json`` injects a caller-provided ``{degree: weight}`` mapping (the
formal-plan-stage injection path).  The check distribution is reconstructed
harmonically at ``R_base`` from the full-chain rate contract.
"""
from __future__ import annotations

import argparse
import json
import os

from ..formal_ir import nonbinary_v11_mcde as v11


def _write_json(path: str, payload: dict) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def _load_lambda_edges(args: argparse.Namespace) -> dict[int, float]:
    if args.lambda_json:
        with open(args.lambda_json, encoding="utf-8") as handle:
            payload = json.load(handle)
        edges = {int(degree): float(weight) for degree, weight in payload.items()}
        v11.parse_degree_hist(edges, "lambda_edge", v11.DEGREE_MAX)
        return edges
    if args.stratum == "S3":
        return dict(v11.V10_WINNER_S3)
    return dict(v11.V10_WINNER_S1)


def _rate_checks() -> dict:
    checks: list[dict] = []
    for stratum, winner, rate in (("S1", v11.V10_WINNER_S1, v11.V10_WINNER_S1_RATE),
                                  ("S3", v11.V10_WINNER_S3, v11.V10_WINNER_S3_RATE)):
        for geometry, params in v11.FROZEN_GEOMETRIES.items():
            contract = v11.rate_contract(params["L"], params["w"], rate, winner)
            checks.append({"stratum": stratum, "geometry": geometry, **contract})
    return {"schema": "v11_mcde_rate_contract_v1", "checks": checks}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true",
                        help="rate contract (G1-G3 x S1/S3) + one tiny coupled run")
    parser.add_argument("--rate-check", action="store_true",
                        help="print the frozen G1-G3 x S1/S3 rate contract")
    parser.add_argument("--dry-run", action="store_true",
                        help="one small deterministic coupled MC-DE run")
    parser.add_argument("--q", type=int, default=8, help="GF size (power of two, 2..1024)")
    parser.add_argument("--L", type=int, default=4, help="terminated chain length")
    parser.add_argument("--w", type=int, default=1, help="coupling width (0..L-1)")
    parser.add_argument("--W", type=int, default=4, help="decoding window (1..L)")
    parser.add_argument("--n-samples", type=int, default=200)
    parser.add_argument("--max-iter", type=int, default=5)
    parser.add_argument("--p", type=float, default=0.15, help="QSC crossover probability")
    parser.add_argument("--stratum", choices=("S1", "S3"), default="S1",
                        help="frozen V10 winner distribution (V11-A06)")
    parser.add_argument("--lambda-json", default=None,
                        help="caller-injected {degree: weight} lambda mapping")
    parser.add_argument("--seed", type=int, default=v11.V11_DRY_RUN_SEED)
    parser.add_argument("--out-dir", default=None,
                        help="write JSON evidence here (additive name); default: stdout only")
    args = parser.parse_args()

    if args.self_check:
        result = _rate_checks()
        checks_ok = all(check["ok"] for check in result["checks"])
        rho = v11.rate_contract(4, 1, v11.V10_WINNER_S1_RATE, v11.V10_WINNER_S1)["rho"]
        run = v11.run_coupled_mcde(8, v11.V10_WINNER_S1, rho, 0.15, L=4, w=1, W=4,
                                   n_samples=100, max_iter=3, seed=v11.V11_DRY_RUN_SEED)
        result["dry_run"] = {key: run[key] for key in
                             ("converged", "iterations", "q", "L", "w", "W",
                              "final_per_position_entropy")}
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if checks_ok and "dry_run" in result else 1)

    if args.rate_check:
        print(json.dumps(_rate_checks(), indent=2, sort_keys=True))
        raise SystemExit(0 if all(c["ok"] for c in _rate_checks()["checks"]) else 1)

    if args.dry_run:
        lambda_edge = _load_lambda_edges(args)
        if args.stratum == "S3":
            rate = v11.V10_WINNER_S3_RATE
        else:
            rate = v11.V10_WINNER_S1_RATE
        rho = v11.rate_contract(args.L, args.w, rate, lambda_edge)["rho"]
        run = v11.run_coupled_mcde(args.q, lambda_edge, rho, args.p,
                                   L=args.L, w=args.w, W=args.W,
                                   n_samples=args.n_samples, max_iter=args.max_iter,
                                   seed=args.seed)
        summary = {key: run[key] for key in
                   ("converged", "iterations", "q", "p", "L", "w", "W",
                    "n_samples", "max_iter", "seed",
                    "final_per_position_entropy")}
        summary["entropy_trace"] = run["entropy_trace"]
        summary["error_trace"] = run["error_trace"]
        if args.out_dir is not None:
            path = os.path.join(args.out_dir, f"mcde_dry_run_seed{args.seed}.json")
            _write_json(path, {"schema": "v11_mcde_dry_run_v1", **summary,
                               "lambda": lambda_edge, "rho": rho})
            summary["evidence_path"] = path
        print(json.dumps(summary, indent=2, sort_keys=True))
        raise SystemExit(0)

    parser.print_help()
    raise SystemExit(1)


if __name__ == "__main__":
    main()
