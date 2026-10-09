"""A6 soft time-information decoding interface (synthetic verification only).

First level of the two-level binary chain accepts per-symbol LLRs computed
by Bob from the intra-bin fine position:
    LLR_i = log[P(x=0|v_i)/P(x=1|v_i)],
    P(x=1|v) = 1 - [Phi((v-mu)/sig) - Phi((v-bw-mu)/sig)].
Paired design: identical error realizations for the hard arm (uniform LLR
from the model marginal) and the soft arm (per-symbol LLRs); same parity
matrix (standard repeat-accumulate ensemble, same construction as G-5 RA),
same decoder settings. No real data, no new code claim.

Claim ceiling: gain DIRECTION on a synthetic Gaussian channel vs
Boutros & Soljanin (soft needs no more disclosure than hard at equal FER).
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

SEED = 20261009


def Phi(z: float) -> float:  # noqa: N802
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def build_ra(n: int, m: int, q: int, seed: int) -> np.ndarray:
    """Standard repeat-accumulate ensemble (same construction as
    msd_g5_bakeoff.ra_matrix; instance regenerated, seed stated)."""
    k = n - m
    rng = np.random.default_rng(seed)
    H = np.zeros((m, n), dtype=np.uint8)
    order = rng.permutation(m * ((q * k) // m + 1))[:q * k]
    for j in range(k):
        for tt in range(q):
            H[int(order[(j * q + tt) % len(order)] % m), j] ^= 1
    for i in range(m):
        H[i, k + i] ^= 1
        if i > 0:
            H[i, k + i - 1] ^= 1
    return H


def p_given_v(v: float, *, sig: float, mu: float, bw: float) -> float:
    p = 1.0 - (Phi((v - mu) / sig) - Phi((v - bw - mu) / sig))
    return min(max(p, 1e-6), 1.0 - 1e-6)


def llr_of(p: float) -> float:
    return math.log((1.0 - p) / p)


def decode_block(H: np.ndarray, syn: np.ndarray, channel: list[float]) -> np.ndarray:
    from ldpc import BpOsdDecoder
    n = H.shape[1]
    dec = BpOsdDecoder(
        H, error_channel=channel, max_iter=50, bp_method="product_sum",
        schedule="serial", omp_thread_count=1,
        serial_schedule_order=list(range(n)),
        osd_method="OSD_CS", osd_order=1)
    return np.asarray(dec.decode(np.asarray(syn, dtype=np.uint8))).reshape(-1).astype(np.uint8)


def run(*, n: int, m: int, q: int, blocks: int, seed: int,
        sig: float, mu: float, bw: float, p_model: float) -> dict:
    H = build_ra(n, m, q, seed=7)
    rng = np.random.default_rng(seed)
    a = b = c = d = 0  # hard-ok/soft-ok, hard-ok/soft-fail, hard-fail/soft-ok, both-fail
    t0 = time.perf_counter()
    for _ in range(blocks):
        v = rng.uniform(0.0, bw, size=n)
        delta = mu + sig * rng.standard_normal(n)
        e = -np.floor((v - delta) / bw).astype(np.int64)
        x = (e != 0).astype(np.uint8)
        syn = (H @ x) % 2
        pv = np.array([p_given_v(vv, sig=sig, mu=mu, bw=bw) for vv in v])
        xh = decode_block(H, syn, [p_model] * n)
        xs = decode_block(H, syn, [float(p) for p in pv])
        okh = bool(np.array_equal(xh, x) and np.array_equal((H @ xh) % 2, syn))
        oks = bool(np.array_equal(xs, x) and np.array_equal((H @ xs) % 2, syn))
        a += okh and oks
        b += okh and not oks
        c += (not okh) and oks
        d += (not okh) and (not oks)
    from math import sqrt
    fer_h, fer_s = (c + d) / blocks, (b + d) / blocks
    # McNemar exact (binomial) two-sided on discordant pairs
    from math import comb
    n_d, k = b + c, min(b, c)
    pmcn = min(1.0, 2.0 * sum(comb(n_d, i) for i in range(k + 1)) / 2.0 ** n_d) if n_d else 1.0
    return {"n": n, "m": m, "q": q, "blocks": blocks, "seed": seed,
            "sig": sig, "mu": mu, "bw": bw, "p_model": p_model,
            "FER_hard": round(fer_h, 4), "FER_soft": round(fer_s, 4),
            "paired": {"both_ok": a, "hard_only": b, "soft_only": c, "both_fail": d},
            "mcnemar_p": round(pmcn, 4),
            "wall_s": round(time.perf_counter() - t0, 1)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", required=True)
    ap.add_argument("--blocks", type=int, default=200)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    # calibrated-regime synthetic point: sig=25, mu=0, bw=200
    from comparison_bench.src.comparison_bench.formal_ir.msd_a3_jitter_model import (
        Gauss, error_pmf, summary_of_pmf)
    p_model = summary_of_pmf(error_pmf(law=Gauss(25.0), bw=200.0, mu=0.0,
                                       window=None))["p"]
    res = run(n=512, m=256, q=3, blocks=args.blocks, seed=args.seed,
              sig=25.0, mu=0.0, bw=200.0, p_model=p_model)
    (root / "a6_result.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"hard FER={res['FER_hard']} soft FER={res['FER_soft']} "
          f"paired={res['paired']} mcnemar_p={res['mcnemar_p']} "
          f"wall={res['wall_s']}s -> {root}")


if __name__ == "__main__":
    main()
