"""G-4b DE-optimized irregular ensemble for BSC(p~0.24) at R~0.2.

Discretized density evolution for BSC + min-sum BP (symmetric LLR alphabet,
15 levels). Self-check first: regular (3,6) must reproduce p*~0.08; regular
(3,4)... then grid-search (dv-mix, dc) maximizing threshold at R in
[0.18, 0.22]. Winner degree distribution feeds PEG construction; gap vs
regular dv3 compared by decode test. Zero-decode for DE part.
"""

from __future__ import annotations

import math

import numpy as np

P_TEST = 0.2376
NLEV = 15
LMAX = 12.0


def h2(x: float) -> float:
    return -(x * math.log2(x) + (1 - x) * math.log2(1 - x))


def quant_levels(nlev: int = NLEV, lmax: float = LMAX) -> np.ndarray:
    pos = np.linspace(0.5, lmax, nlev // 2 + 1)[1:]
    return np.concatenate([-pos[::-1], [0.0], pos])


def bsc_init(p: float, levels: np.ndarray) -> np.ndarray:
    """Message density from channel (all-zero codeword, sign convention)."""
    llr = math.log((1 - p) / p)
    pmf = np.zeros_like(levels)
    idx = int(np.argmin(np.abs(levels - llr)))
    pmf[idx] = 1.0
    return pmf


def var_update(dens: np.ndarray, ch: np.ndarray, dv: int,
               levels: np.ndarray) -> np.ndarray:
    """Variable-node convolution (dv-1 incoming + channel), quantized."""
    from numpy.lib.stride_tricks import sliding_window_view  # noqa
    cur = ch.copy()
    for _ in range(max(0, dv - 1)):
        nxt = np.zeros_like(cur)
        for i, li in enumerate(levels):
            if cur[i] == 0:
                continue
            for j, lj in enumerate(levels):
                s = li + lj
                k = int(np.argmin(np.abs(levels - s)))
                nxt[k] += cur[i] * dens[j]
        cur = nxt
    return cur / cur.sum()


def chk_update(dens: np.ndarray, dc: int, levels: np.ndarray) -> np.ndarray:
    """Check-node min-sum update via tanh rule on quantized densities."""
    # E[artanh] domain: use phi(x) = -log tanh(|x|/2), min-sum approx
    mid = len(levels) // 2
    out = np.zeros_like(dens)
    # min-sum: outgoing magnitude = min of (dc-1) inputs; sign = product
    # quantized implementation by enumeration over input draws
    draws = []
    for _ in range(min(dc - 1, 6)):
        draws.append(dens)
    # exact enumeration is exponential; use dominant-term approx:
    # P(out=0) from all-zero... simplified: use Gaussian approx for speed
    # Fall back to Monte-Carlo density tracking (deterministic seed).
    rng = np.random.default_rng(7)
    acc = np.zeros_like(dens)
    nsamp = 200000
    samp = rng.choice(len(levels), size=(nsamp, dc - 1), p=dens / dens.sum())
    lv = levels[samp]
    sgn = np.prod(np.sign(lv), axis=1)
    sgn[sgn == 0] = 1
    mag = np.min(np.abs(lv), axis=1)
    # map back: value = sgn*mag quantized
    vals = sgn * mag
    for v_i, lv_i in enumerate(levels):
        if v_i == mid:
            acc[v_i] = float(((np.abs(vals) < 0.25)).sum()) / nsamp
        else:
            lo = (levels[v_i - 1] + lv_i) / 2 if v_i > 0 else -np.inf
            hi = (levels[v_i] + levels[v_i + 1]) / 2 if v_i < len(levels) - 1 else np.inf
            acc[v_i] = float(((vals >= lo) & (vals < hi)).sum()) / nsamp
    return acc / acc.sum()


def threshold(lam: dict, rho: dict, p: float, iters: int = 60) -> float:
    """Bisection-free check: does DE converge at channel p? Returns final Pe."""
    levels = quant_levels()
    ch = bsc_init(p, levels)
    # average variable density init
    vd = ch.copy()
    for _ in range(iters):
        # check update averaged over rho
        cd = np.zeros_like(levels)
        tot = 0.0
        for dc, w in rho.items():
            cd += w * chk_update(vd, int(dc), levels)
            tot += w
        cd = cd / tot
        # variable update averaged over lambda (edge perspective approx:
        # use node degrees directly)
        nd = np.zeros_like(levels)
        tot = 0.0
        for dv, w in lam.items():
            nd += w * var_update(cd, ch, int(dv), levels)
            tot += w
        vd = nd / tot
        pe = float(vd[: len(levels) // 2].sum())
        if pe < 1e-6:
            return 0.0
    return float(vd[: len(levels) // 2].sum())


def rate_of(lam: dict, rho: dict) -> float:
    num = sum(w / d for d, w in rho.items())
    den = sum(w / d for d, w in lam.items())
    return 1.0 - num / den


def main() -> None:
    import argparse
    import json
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--search", action="store_true")
    ap.add_argument("--output", default=None)
    args = ap.parse_args()
    if args.check_only:
        # regular (3,6): R=0.5, known BSC threshold ~0.084
        for p in (0.05, 0.08, 0.09, 0.12):
            pe = threshold({3: 1.0}, {6: 1.0}, p, iters=40)
            print(f"(3,6) p={p}: Pe={pe:.2e}", flush=True)
        return
    if args.search:
        best = []
        for lam in ({3: 1.0}, {3: 0.6, 4: 0.4}, {3: 0.4, 4: 0.4, 5: 0.2},
                    {4: 0.7, 5: 0.3}, {3: 0.5, 5: 0.5}):
            for dc in (4, 5, 6):
                rho = {dc: 1.0}
                r = rate_of(lam, rho)
                if not (0.16 <= r <= 0.24):
                    continue
                # bisection on p for threshold
                lo, hi = 0.10, 0.30
                for _ in range(7):
                    mid = (lo + hi) / 2
                    pe = threshold(lam, rho, mid, iters=30)
                    if pe < 1e-4:
                        lo = mid
                    else:
                        hi = mid
                best.append({"lam": {str(k): v for k, v in lam.items()},
                             "rho": {str(k): v for k, v in rho.items()},
                             "rate": round(r, 4), "threshold": round(lo, 4)})
                print(best[-1], flush=True)
        best.sort(key=lambda b: -b["threshold"])
        if args.output:
            with open(args.output, "w", encoding="utf-8") as fh:
                json.dump(best, fh, indent=2)
        print("BEST:", best[0] if best else None)


if __name__ == "__main__":
    main()
