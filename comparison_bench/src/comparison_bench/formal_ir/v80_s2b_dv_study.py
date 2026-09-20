"""V80 S2b dv-distribution study (EXPLORE synthetic, observations only).

Frozen-mechanics probe: alternative dv mixes via peg_construct +
make_rho directly (m2=47/n=256/seed=2026092001 for all three),
bypassing frozen construct_l2 (Study C feasibility path). Imports
frozen modules READ-ONLY; modifies nothing. Production stopping
(kernel default streak); matched QSC sampler+prior; 4 PAIRED frame
seeds per cell (new hundred-block 2026097101..104). Raw JSON -> /tmp.
"""
import json
import sys
import time

sys.path.insert(0, "/mnt/d/Code/HD-QKD_Polar_Comparison/comparison_bench/src")
import numpy as np  # noqa: E402

from comparison_bench.formal_ir import nonbinary_v10_common as common  # noqa: E402
from comparison_bench.formal_ir import nonbinary_v10_fftqspa as fftqspa  # noqa: E402
from comparison_bench.formal_ir import nonbinary_v10_peg as peg  # noqa: E402
from comparison_bench.formal_ir import nonbinary_v26_mcde as mcde  # noqa: E402
from comparison_bench.formal_ir.nonbinary_field import GF2mField  # noqa: E402
from comparison_bench.formal_ir.v80_s2_peg import (  # noqa: E402
    M2, MAX_ITER, N_FRAME, Q, count_four_cycles, qsc_pair_sampler)

LAMBDAS = {"L-A": {2: 1.0}, "L-B": {2: 0.5, 3: 0.5}, "L-C": {3: 1.0}}
P_GRID = [0.04, 0.05, 0.06, 0.081]
FRAMES = [2026097101, 2026097102, 2026097103, 2026097104]
C_SEED = 2026092001  # construction tie-break seed, all three (fixed mechanics)
OUT = "/tmp/opencode/s2b_dv_study.json"


def build(lam):
    field = GF2mField.create(Q)
    rho = mcde.make_rho(1.0 - M2 / N_FRAME, dict(lam))
    c = peg.peg_construct(N_FRAME, M2, dict(lam), rho, C_SEED,
                          max_trials=20, field=field)
    assert c["status"] == "ok", c
    dense = peg.sparse_to_dense(c["triples"], N_FRAME, M2, field)
    return c, field, dense, rho


def run_frame(field, dense, seed, p):
    rng = np.random.default_rng(common.v10_seed(f"s2_smoke:{int(seed)}"))
    alice, bob = qsc_pair_sampler(rng, N_FRAME, Q, p=float(p))
    alice = np.asarray(alice, dtype=np.int64)
    bob = np.asarray(bob, dtype=np.int64)
    s_x = fftqspa.syndrome_of(field, dense, alice.tolist())
    t0 = time.time()
    res = fftqspa.decode_error_domain(bob.tolist(), dense, s_x, float(p),
                                      field, MAX_ITER)
    dt = time.time() - t0
    x_hat = res.get("x_hat")
    exact = (bool(np.array_equal(np.asarray(x_hat, dtype=np.int64), alice))
             if x_hat is not None else False)
    diffw = None
    if res.get("status") == "success" and not exact and x_hat is not None:
        diffw = int(np.sum(np.asarray(x_hat, dtype=np.int64) != alice))
    return {"seed": int(seed), "p": float(p), "status": res.get("status"),
            "iterations": res.get("iterations"), "exact": exact,
            "reconstruction_ok": bool(res.get("reconstruction_ok")),
            "diff_weight": diffw, "wall_s": round(dt, 2)}


def main():
    t0 = time.time()
    wants = set(sys.argv[1:]) or set(LAMBDAS)
    lambdas = {k: v for k, v in LAMBDAS.items() if k in wants}
    out = {"design": {"lambdas": LAMBDAS, "p_grid": P_GRID, "frames": FRAMES,
                      "c_seed": C_SEED, "max_iter": MAX_ITER,
                      "stopping": "production-default (no streak override)",
                      "numpy": np.__version__},
           "constructions": {}, "cells": {}, "checks": {}}
    built = {}
    for name, lam in lambdas.items():
        c1, field, dense, rho = build(lam)
        c2, _, _, _ = build(lam)  # determinism: construct twice
        det = c1["triples"] == c2["triples"]
        built[name] = (c1, field, dense)
        out["constructions"][name] = {
            "lambda": lam, "rho": rho, "status": c1["status"],
            "four_cycles": int(c1["four_cycles"]),
            "four_cycles_xcheck": int(count_four_cycles(
                c1["triples"], N_FRAME, M2)),
            "min_girth": c1.get("min_girth"), "rank": c1.get("rank"),
            "trials_used": c1.get("trials_used"),
            "var_counts": c1.get("var_counts"),
            "construct_twice_identical": det}
        print(f"{name} lam={lam} 4cyc={c1['four_cycles']} "
              f"girth={c1.get('min_girth')} rank={c1.get('rank')} "
              f"trials={c1.get('trials_used')} det={det}", flush=True)
    for name, (_, field, dense) in built.items():
        for p in P_GRID:
            rows = [run_frame(field, dense, sd, p) for sd in FRAMES]
            out["cells"][f"{name}@p={p}"] = rows
            print(f"{name} p={p}: " + json.dumps(
                [(r["seed"], r["status"], r["iterations"], r["exact"],
                  r["diff_weight"]) for r in rows]), flush=True)
    _, f_a, d_a = built["L-A"]  # determinism: re-run one cell twice
    r1 = run_frame(f_a, d_a, FRAMES[0], 0.04)
    r2 = run_frame(f_a, d_a, FRAMES[0], 0.04)
    out["checks"]["rerun_identical"] = (
        {k: r1[k] for k in ("status", "iterations", "exact", "diff_weight")}
        == {k: r2[k] for k in ("status", "iterations", "exact", "diff_weight")})
    print("rerun_identical:", out["checks"]["rerun_identical"], flush=True)
    la81 = out["cells"]["L-A@p=0.081"]
    out["checks"]["sanity_LA_p0081"] = [(r["status"], r["iterations"]) for r in la81]
    out["wall_s_total"] = round(time.time() - t0, 1)
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"wrote {OUT} wall={out['wall_s_total']}s", flush=True)


if __name__ == "__main__":
    main()
