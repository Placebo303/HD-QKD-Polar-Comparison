"""G-4a level-A incremental disclosure (packet scope): single PEG at M_max,
staged disclosure rows[0,m0), [m0,m1), [m1,m2) with COLD full-matrix re-decode
per round (P1 F2 mirror). Tune round model on stream A (B=200), confirm on
disjoint stream B (B=300, sample-out calibration). Expected-yield f with
E[L] = sum_r P(reach r) * m_r. N=16384 pilot (BSC p=0.2376 ternary channel).
R14: ideal N*h2(p); actual = expected disclosed rows.
"""

from __future__ import annotations

import argparse
import functools
import json
import math
import time
from pathlib import Path

import numpy as np

N = 16384
P = 0.2376
PM_ABS = 0.00138
GAPS = (0.03, 0.08, 0.15)  # round disclosure levels (nested prefixes)
B_TUNE = 200
B_CONFIRM = 300
SEED_A = 20267100
SEED_B = 20267200
TAG_BITS = 64


def h2(x: float) -> float:
    return -(x * math.log2(x) + (1 - x) * math.log2(1 - x))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("G-4a runs only with --full")
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        load_train_table,
        read_p1_scalars,
        wilson_upper,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (  # noqa: E402
        build_peg_code,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
        _syndrome,
        make_bp_decoder,
    )

    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    t = np.asarray(load_train_table("T2-1M"), dtype=np.float64)
    pa = t.sum(axis=1) / t.sum()
    pa = pa / pa.sum()
    m_levels = [min(N - 1, max(1, int(math.ceil(N * (h2(P) + g))))) for g in GAPS]
    H = build_peg_code(n=N, m=m_levels[-1], variable_degree=3).parity_check_matrix
    Hd = np.asarray(H.toarray(), dtype=np.uint8)
    scalars = read_p1_scalars()["T2-1M"]
    jl = root / "blocks_g4a.jsonl"
    if jl.exists():
        raise SystemExit(f"refusing to overwrite {jl}")

    def run_stream(seed, n_blocks, tag):
        rng = np.random.default_rng(seed)
        aks = np.arange(1024)
        recs = []
        t0 = time.perf_counter()
        with jl.open("a", encoding="utf-8", buffering=1) as fh:
            for blk in range(n_blocks):
                a = rng.choice(aks, size=N, p=pa)
                u = rng.random(size=N)
                e = np.where(u < 1 - P, 0, np.where(u < 1 - PM_ABS, 1, 1023)).astype(np.int64)
                alice = a.astype(np.int64)
                bob = ((a + e) % 1024).astype(np.int64)
                xt = (alice & 1).astype(np.uint8)
                # model priors P(x0|b)
                lik0, likp, likm = 1 - P, P - PM_ABS, PM_ABS
                a_cand = np.stack([(bob - 1) % 1024, bob, (bob + 1) % 1024], axis=0)
                w = np.stack([likm * pa[(bob - 1) % 1024], lik0 * pa[bob],
                              likp * pa[(bob + 1) % 1024]], axis=0)
                w = w / w.sum(axis=0, keepdims=True)
                p1 = (w * ((a_cand & 1).astype(float))).sum(axis=0)
                base = (p1 > 0.5).astype(np.uint8)
                ch = np.minimum(p1, 1 - p1).copy()
                syn_full = (Hd @ xt) % 2
                ok, rounds, l_dis = False, 0, 0
                for r, m in enumerate(m_levels):
                    Hsub = Hd[:m]
                    syn = syn_full[:m]
                    delta = np.bitwise_xor(syn, (Hsub @ base) % 2)
                    # sliced sparse matrix for decoder (COLD full re-decode)
                    Hs = H.tocsr()[:m]
                    dec = make_bp_decoder(parity_check_matrix=Hs,
                                          error_channel=ch.copy(), max_iter=200)
                    err = np.asarray(dec.decode(delta.copy())).astype(np.uint8)
                    rec = np.bitwise_xor(base, err)
                    rounds = r + 1
                    l_dis = m
                    if bool(np.array_equal((Hsub @ rec) % 2, syn)) and bool(np.array_equal(rec, xt)):
                        ok = True
                        break
                recs.append({"block": blk, "exact_A": ok, "rounds": rounds,
                             "L_A": l_dis})
                fh.write(json.dumps({"stream": tag, "block": blk,
                                     "exact_A": ok, "rounds": rounds,
                                     "L_A": l_dis}) + "\n")
        return recs, time.perf_counter() - t0

    tune, wall_t = run_stream(SEED_A, B_TUNE, "A")
    # round model from tune stream (sample-out calibration input)
    from collections import Counter
    rh = Counter(r["rounds"] for r in tune)
    ntf = sum(0 if r["exact_A"] else 1 for r in tune)
    print("tune rounds:", dict(rh), "fails:", ntf, flush=True)
    conf, wall_c = run_stream(SEED_B, B_CONFIRM, "B")
    ncf = sum(0 if r["exact_A"] else 1 for r in conf)
    e_l = sum(r["L_A"] for r in conf) / len(conf)
    fer = ncf / len(conf)
    denom = N * scalars["H_AB"]
    kept = N * scalars["H_A"] - e_l
    f_p = (e_l + TAG_BITS + kept * fer) / denom
    out = {"tune_rounds": {str(k): v for k, v in rh.items()},
           "tune_fails": ntf, "confirm": {"blocks": len(conf), "failures": ncf,
                                          "E_L_A": e_l, "FER_A": fer,
                                          "FER_wilson_upper95": wilson_upper(ncf, len(conf)),
                                          "f_levelA_only": f_p},
           "levels": m_levels, "N": N, "wall_s": wall_t + wall_c}
    (root / "g4a_summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
