"""S-5c GF(5) real-data single-level decode (DECIDE, Pre-EXECUTE-gated).

Frozen: N=4096, frac=0.19 (m=778), code seed 12192 (validated instance),
per-source S-2 prefix DoubleGauss laws for per-symbol 5-priors, A3 QSPA
max_iter=100. Paired vs landed S-4d hard/plain cells (same framing → same
blocks). e in {-2..2} -> s=e mod 5; disclosure BITS via disclose().
|e|>=3 (mass ~1e-9) -> honest U. Labels: retest-on-used-data.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import scipy.stats as st

from comparison_bench.src.comparison_bench.formal_ir.msd_s3_softdecode import (
    SOURCES,
    real_blocks,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_a3_jitter_model import (
    DoubleGauss,
)

SPAN_PS = 204800
BW = 200
D = SPAN_PS // BW
N = 4096
FRAC = 0.19
M = int(N * FRAC)
CODE_SEED = 12192
TAG = 64
HA = 10.0
RETEST = "retest-on-used-data"


def priors_of(vv: np.ndarray, law, Nn: int) -> np.ndarray:
    F_ = law.interval_mass
    prior = np.zeros((Nn, 5))
    for i, vv_ in enumerate(vv):
        for k in range(-6, 7):
            prior[i, k % 5] += max(F_(float(vv_) + k * BW - BW,
                                     float(vv_) + k * BW), 0.0)
        prior[i] /= max(prior[i].sum(), 1e-300)
    return prior


def self_test() -> None:
    # tiny GF(5) roundtrip on synthetic truth (no real data)
    from comparison_bench.src.comparison_bench.formal_ir import (
        msd_c1_nbldpc as A3,
    )
    rng = np.random.default_rng(0)
    code = A3.construct(64, 32, 5, seed=3)
    e = rng.choice([-1, 0, 0, 0, 1], size=64)
    s = (e % 5).astype(np.int64)
    syn, bits = A3.disclose(code, s)
    assert bits == math.ceil(32 * math.log2(5))
    prior = np.full((64, 5), 0.02)
    prior[np.arange(64), s] = 0.92
    shat = A3.decode(code, np.zeros(64, dtype=np.int64), syn, prior, 100)
    assert shat is not None and np.array_equal(shat, s)
    print("s5c self-test OK (GF5 roundtrip + bits)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output-root", required=False, default=None)
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.full:
        raise SystemExit("S-5c runs only with --full (after user confirmation)")
    if not args.output_root:
        raise SystemExit("--full requires --output-root")
    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    from comparison_bench.src.comparison_bench.formal_ir import (
        msd_c1_nbldpc as A3,
    )
    import json as _j
    s2 = _j.load(open("workspace/s_softmap/s2_20261009/s2_summary.json",
                      encoding="utf-8"))
    code = A3.construct(N, M, 5, seed=CODE_SEED)
    t_start = time.perf_counter()
    BUDGET_CAP = 7200.0
    summary: dict = {"track": "DECIDE-real-decode", "label": RETEST,
                     "frozen": {"N": N, "frac": FRAC, "m": M, "code_seed": CODE_SEED,
                                "priors": "per-source S-2 prefix DoubleGauss"},
                     "cells": {}, "mcnemar_vs_S4d_hard": {}}
    jlf = (root / "s5c_blocks.jsonl").open("w", encoding="utf-8")
    s2H = _j.load(open("workspace/s_softmap/s2_20261009/s2_summary.json",
                       encoding="utf-8"))
    for src in ("T2-1M", "T2-1.5M", "T2-2M", "0dB", "4dB"):
        if time.perf_counter() - t_start > BUDGET_CAP:
            summary["cells"][src] = {"stopped": "budget-cap"}
            print(f"{src}: STOPPED budget-cap", flush=True)
            continue
        fit = s2["sources"][src]["prefix_fit"]
        law = DoubleGauss(float(fit["sig"]), 100.0, float(fit["w"]))
        blks = real_blocks(src, N, {"sig": 1.0, "mu": 0.0, "w": 0.0})
        S = F = U = 0
        LA = 0.0
        T = []
        for bi, blk in enumerate(blks):
            aa, bb = blk["a"], blk["b"]
            ee = (bb.astype(np.int64) - aa.astype(np.int64)) % D
            s = (np.where(ee <= D // 2, ee, ee - D) % 5).astype(np.int64)
            # priors only needed in full; |e|>2 positions get flat-ish mass
            # from the law tails automatically (k=-6..6 sum)
            prior = priors_of(blk["v"], law, N)
            syn, bits = A3.disclose(code, s)
            t0 = time.perf_counter()
            shat = A3.decode(code, np.zeros(N, dtype=np.int64), syn, prior, 100)
            T.append(time.perf_counter() - t0)
            if shat is None:
                F += 1
                jlf.write(_j.dumps({"cell": src, "block": bi, "ok": False}) + "\n")
                continue
            ehat = np.where(shat <= 2, shat, shat - 5)
            ahat = (bb - ehat) % D
            if np.array_equal(ahat, aa):
                S += 1
                LA += bits
            else:
                U += 1
            jlf.write(_j.dumps({"cell": src, "block": bi,
                                "ok": bool(np.array_equal(ahat, aa)) if shat is not None else False}) + "\n")
        n = S + F + U
        fer = (F + U) / n
        fails = F + U
        lo = 0.0 if fails == 0 else float(st.beta.ppf(0.025, fails, n - fails + 1))
        hi = 1.0 if fails == n else float(st.beta.ppf(0.975, fails + 1, n - fails))
        H = s2H["sources"][src]["cells"]["200"]
        net = S * HA * N - LA - S * TAG
        summary["cells"][src] = {"S": S, "F": F, "U": U, "FER": round(fer, 4),
                                 "FER_CP95": [round(lo, 4), round(hi, 4)],
                                 "L_tot": round(LA, 0), "Net_seg": round(net, 0),
                                 "f_ref": round(LA / (n * N * H["H_hard_cal"]), 4),
                                 "T_med": round(float(np.median(T)), 2),
                                 "T_tot": round(float(sum(T)), 0)}
        print(f"full {src}: S={S} F={F} U={U} FER={fer:.4f} Net={net:.0f} "
              f"f_ref={summary['cells'][src]['f_ref']}", flush=True)
        (root / "s5c_cells.json").write_text(_j.dumps(summary, indent=1), encoding="utf-8")
        jlf.flush()
    # paired McNemar vs landed S-4d hard/plain FULL success (s3 rows carry
    # okA/okB/exact per block; same framing+N+order => same blocks).
    for src in ("T2-1M", "T2-1.5M", "T2-2M", "0dB", "4dB"):
        mine = [json.loads(l) for l in open(root / "s5c_blocks.jsonl", encoding="utf-8")
                if json.loads(l)["cell"] == src]
        his = [json.loads(l) for l in
               open("workspace/s3_softdecode/s3_20261009/s3_blocks.jsonl", encoding="utf-8")
               if json.loads(l)["cell"] == f"{src}/hard/4096"]
        mh = {x["block"]: (x["okA"] and x["okB"] and x["exact"]) for x in his}
        so = ho = 0
        for x in mine:
            h = mh.get(x["block"], False)
            s_ok = bool(x["ok"])
            so += (not h) and s_ok
            ho += h and (not s_ok)
        from math import comb
        nd, kk = so + ho, min(so, ho)
        p = 1.0 if nd == 0 else min(1.0, 2.0 * sum(comb(nd, i) for i in range(kk + 1)) / 2.0 ** nd)
        summary["mcnemar_vs_S4d_hard"][src] = {"soft_only": so, "hard_only": ho,
                                               "p": round(p, 6)}
        print(f"mcnemar {src}: {so}/{ho} p={p:.2g}", flush=True)
    summary["wall_s_total"] = round(time.perf_counter() - t_start, 1)
    (root / "s5c_cells.json").write_text(_j.dumps(summary, indent=1), encoding="utf-8")
    jlf.close()
    print(f"s5c done wall={summary['wall_s_total']}s -> {root}")


if __name__ == "__main__":
    main()
