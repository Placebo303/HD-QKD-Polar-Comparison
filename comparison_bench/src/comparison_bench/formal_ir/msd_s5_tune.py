"""S-5a/S-5b synthetic tuning — FINAL (all scoring bugs closed).

Chain under test (soft arm): level-A (gap grid, per-symbol LLRs) -> level-B
fixed (fine-conditioned priors, frac 0.10) -> third level (w @ m3=64 AND
w2 @ m3'=320, BOTH with honest priors) -> bits0-2-patch exact (|e|<=3).

Prior-honesty ledger (each learned from a caught bug, all with tests):
- w (=a1^b1): marked pinned to decoded (yhat^b1, exact given okB);
  unmarked +10.6 (P~2.5e-5 wide background), NEVER +25 (confident-wrong
  on +-2 positions poisons min-sum).
- w2 (=a2^b2): marked +-1.1 (borrow spill P~0.25), unmarked +-10.6.
  (An m3'=64 confident-0 design is 7x undersized: w2 needs ~300.)
- marked (xa==1), a0hat=xa^b0 everywhere; reconstruction from b.copy();
  random Bob bits in all synthetic (b0=0 hides xa-vs-a0-class bugs).
- GF(5) arm (S-5b(ii)): e in {-2..2} soft 5-LLRs into A3 QSPA (per-symbol
  prior interface, verified equivalent to global path); disclosure in BITS.

Selection by per-pair leakage (deterministic disclosures) + Net + FER<=0.05
gate; N-verify winner per R16. Synthetic only, seeds frozen.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_s3_softdecode import (
    QA,
    K2,
    build_ra,
    decode,
    llr,
    rate_of,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_a3_jitter_model import (
    DoubleGauss,
)

SPAN_PS = 204800
BW = 200
D = SPAN_PS // BW
N = 4096
TAG = 64
HA = 10.0
SEED = 20261013
N_SUB = 8
GAPS_SOFT = (0.0, 0.05, 0.10, 0.18)  # -0.05 dropped: R=0.723 above capacity 0.714
M3_W = 64
M3P_W2 = 320
GF5_MS = (0.19, 0.24, 0.29)
# honest third-level priors (see ledger above)
LLR_W_UNMARKED = 10.6
LLR_W2_MARKED = 1.1
LLR_W2_UNMARKED = 10.6


def law_T2():
    import json as _j
    f = _j.load(open("workspace/s_softmap/s2_20261009/s2_summary.json",
                      encoding="utf-8"))["sources"]["T2-1M"]["prefix_fit"]
    return DoubleGauss(float(f["sig"]), 100.0, float(f["w"]))


def gen_blocks(rng: np.random.Generator, n: int, Nn: int, law) -> list[dict]:
    """FULLY CONSISTENT chain: random Bob symbols b -> e from (v,Delta)
    mechanism -> a=(b-e)%D; all truth fields derived from (a,b,e)."""
    out = []
    for _ in range(n):
        v = rng.uniform(0.0, BW, size=Nn)
        wmask = rng.random(Nn) < law.w
        sig = np.where(wmask, 100.0, law.g1.sig)
        delta = rng.normal(0.0, sig)
        e = -np.floor((v - delta) / BW).astype(np.int64)
        bb = rng.integers(0, D, size=Nn).astype(np.int64)
        aa = (bb - e) % D
        b0 = (bb % 2).astype(np.uint8)
        b1 = ((bb >> 1) & 1).astype(np.uint8)
        a0 = (aa % 2).astype(np.uint8)
        a1 = ((aa >> 1) & 1).astype(np.uint8)
        x = (a0 ^ b0).astype(np.uint8)
        assert bool((((x ^ (np.abs(e) % 2).astype(np.uint8)) == 0).all()))
        out.append({"x": x, "b0": b0, "a1": a1, "b1": b1, "v": v,
                    "a": aa, "b": bb, "e": e})
    return out


def sub_of(v: np.ndarray) -> np.ndarray:
    return np.minimum((v // (BW // N_SUB)).astype(int), N_SUB - 1)


def p_soft_vec(vv: np.ndarray, law) -> np.ndarray:
    """P(x=1|v) under the mixture law (A5 caliber)."""
    F = law.interval_mass
    ps = []
    for t in vv:
        p = 1.0 - F(float(t) - BW, float(t))
        ps.append(min(max(p, 1e-6), 1.0 - 1e-6))
    return np.array(ps)


def decode_A(H, blk: dict, p_bar: float, arm: str, law):
    x = blk["x"]
    syn = np.asarray((H @ x) % 2, dtype=np.uint8).ravel()
    ch = [llr(p_bar)] * len(x) if arm == "hard" else \
        [llr(p) for p in p_soft_vec(blk["v"], law)]
    xa = decode(H, syn, ch)
    okA = bool(np.array_equal(xa, x) and np.array_equal(((H @ xa) % 2).ravel(), syn))
    return syn, xa, okA


def decode_B(HB, HR, blk: dict, xa: np.ndarray, curve: np.ndarray):
    """Fixed fine-conditioned level-B (S-4d design). Returns (yhat, okB, lb, r)."""
    a0hat = (xa ^ blk["b0"]).astype(np.uint8)
    marked = (xa == 1)
    y = blk["a1"][marked]
    mB = HB.shape[0]
    if int(marked.sum()) == 0:
        return np.empty((0,), dtype=np.uint8), True, mB, 0
    synB = np.asarray((HB[:, marked] @ y) % 2, dtype=np.uint8).ravel()
    pv = curve[sub_of(blk["v"][marked])]
    L = np.array([math.log((1.0 - p) / p) for p in pv])
    chB = np.where((blk["b1"][marked] ^ a0hat[marked]) == 1, -L, L)
    yhat = decode(HB[:, marked], synB, [float(c) for c in chB])
    if np.array_equal(yhat, y):
        return yhat, True, mB, 0
    synR = np.asarray((HR[:, marked] @ y) % 2, dtype=np.uint8).ravel()
    from scipy import sparse
    Hsub2 = sparse.vstack([HB[:, marked], HR[:, marked]]).tocsr()
    yhat = decode(Hsub2, np.concatenate([synB, synR]), [float(c) for c in chB])
    okB = bool(np.array_equal(yhat, y))
    return yhat, okB, mB + (K2 if okB else 0), (K2 if okB else 0)


def decode_3(H3, blk: dict, yhat: np.ndarray, marked: np.ndarray):
    """Third level, w-plane: honest priors (marked pinned, unmarked +10.6).

    Returns (ok, what): the decoded w is LOAD-BEARING for exact reconstruction
    (unmarked +-2 positions have a1=~b1; assuming b1 there fails every block
    containing one). Callers must use what^b1 as a1hat, never bare b1.
    """
    w = (blk["a1"] ^ blk["b1"]).astype(np.uint8)
    syn3 = np.asarray((H3 @ w) % 2, dtype=np.uint8).ravel()
    ch = np.full(len(w), LLR_W_UNMARKED)
    if int(marked.sum()):
        ch = ch.copy()
        ch[marked] = np.where((yhat ^ blk["b1"][marked]) == 1, -25.0, 25.0)
    what = decode(H3, syn3, [float(c) for c in ch])
    if not np.array_equal(what, w):
        return False, None
    return True, what


def decode_3b(H3B, blk: dict) -> bool:
    """Third level, w2-plane: honest priors (marked +-1.1, unmarked +-10.6)."""
    w2 = (((blk["a"] >> 2) & 1) ^ ((blk["b"] >> 2) & 1)).astype(np.uint8)
    syn32 = np.asarray((H3B @ w2) % 2, dtype=np.uint8).ravel()
    marked = (blk["x"] == 1)
    ch = np.full(len(w2), LLR_W2_UNMARKED)
    ch[marked] = np.where(ch[marked] > 0, LLR_W2_MARKED, LLR_W2_MARKED)
    ch[marked] = LLR_W2_MARKED
    what = decode(H3B, syn32, [float(c) for c in ch])
    return bool(np.array_equal(what, w2))


def chain_once(H, HB, HR, H3, H3B, blk: dict, ctx: dict):
    """Full 3-level chain with bits0-2-patch exact. Returns (S/F/U, L tuple)."""
    syn, xa, okA = decode_A(H, blk, ctx["p_bar"], "soft", ctx["law"])
    if not okA:
        return "F", (0, 0, 0)
    yhat, okB, lb, _r = decode_B(HB, HR, blk, xa, ctx["curve"])
    if not okB:
        return "F", (0, 0, 0)
    marked = (xa == 1)
    wok, what = decode_3(H3, blk, yhat, marked)
    if not wok:
        return "U", (0, 0, 0)
    w2 = (((blk["a"] >> 2) & 1) ^ ((blk["b"] >> 2) & 1)).astype(np.uint8)
    syn32 = np.asarray((H3B @ w2) % 2, dtype=np.uint8).ravel()
    ch32 = np.full(len(w2), LLR_W2_UNMARKED)
    ch32[marked] = LLR_W2_MARKED
    w2hat = decode(H3B, syn32, [float(c) for c in ch32])
    if not np.array_equal(w2hat, w2):
        return "U", (0, 0, 0)
    a0hat = (xa ^ blk["b0"]).astype(np.uint8)
    a1hat = (what ^ blk["b1"]).astype(np.uint8)
    a2hat = (w2hat ^ ((blk["b"] >> 2) & 1)).astype(np.uint8)
    # modular reconstruction: (a-b)%8 = (-e)%8, so e = -signed((plo-blo)%8).
    # Exact for |e|<=3 (NOT bit-OR patch: borrows cross bit3 when b&7==0).
    plo = (a0hat.astype(np.int64) | (a1hat.astype(np.int64) << 1) |
           (a2hat.astype(np.int64) << 2))
    blo = (blk["b"] & 0b111).astype(np.int64)
    e_est = (blo - plo) % 8
    e_est = np.where(e_est <= 3, e_est, e_est - 8)
    ahat = (blk["b"] - e_est) % D
    if np.array_equal(ahat, blk["a"]):
        return "S", (H.shape[0], lb, H3.shape[0] + H3B.shape[0])
    return "U", (0, 0, 0)


def self_test() -> None:
    rng = np.random.default_rng(SEED)
    law = DoubleGauss(13.34, 100.0, 0.007)
    blks = gen_blocks(rng, 2, 128, law)
    assert all(len(b["x"]) == 128 for b in blks)
    for b in blks:
        assert bool((((b["a"] % 2).astype(np.uint8) ^ (b["b"] % 2).astype(np.uint8) ^ b["x"]) == 0).all())
        assert bool((((b["a"] >> 1) & 1).astype(np.uint8) == b["a1"]).all())
    p = p_soft_vec(np.array([0.0, 100.0, 199.0]), law)
    assert p[0] > p[1] and p[1] < 0.05 and p[2] > p[1], p
    print("s5 self-test OK (consistent gen + soft-LLR)")


def do_tune_sup(tune_root: Path) -> dict:
    raise SystemExit("tune-sup folded into --full (single joint run); see s5_tune.json")


def do_gf5_confirm(root: Path) -> dict:
    """GF(5) N=4096 confirm (B=25) + N=8192 R16 point (B=10).

    The --full GF5 ladder ran at N=1024 only; S-5c needs the frozen N.
    QSPA python cost unknown -> measure first block, abort N=8192 if slow.
    Additive s5_gf5conf.json in a FRESH root (never touches s5_tune.json).
    """
    import json as _j
    from comparison_bench.src.comparison_bench.formal_ir import (
        msd_c1_nbldpc as A3,
    )
    law = law_T2()
    rng = np.random.default_rng(SEED + 31337)
    t0 = time.perf_counter()
    out: dict = {"cells": []}
    for Nn, B, fr in ((4096, 25, 0.19), (8192, 10, 0.19)):
        if time.perf_counter() - t0 > 5400:
            break
        mq = int(Nn * fr)
        code = A3.construct(Nn, mq, 5, seed=8100 + Nn)
        blks = gen_blocks(rng, B, Nn, law)
        S = F = U = 0
        LA = 0.0
        t_blk = []
        abort_N = False
        for bi, blk in enumerate(blks):
            v, e = blk["v"], blk["e"]
            s = (e % 5).astype(np.int64)
            F_ = law.interval_mass
            prior = np.zeros((Nn, 5))
            for i, vv in enumerate(v):
                for k in range(-6, 7):
                    prior[i, k % 5] += max(F_(float(vv) + k * BW - BW,
                                             float(vv) + k * BW), 0.0)
                prior[i] /= max(prior[i].sum(), 1e-300)
            syn = np.asarray((code.H @ s) % 5, dtype=np.int64).ravel()
            t1 = time.perf_counter()
            shat = A3.decode(code, np.zeros(Nn, dtype=np.int64), syn, prior, 100)
            t_blk.append(time.perf_counter() - t1)
            if bi == 0:
                print(f"gf5 N={Nn} first-block {t_blk[-1]:.1f}s", flush=True)
                if Nn > 4096 and t_blk[-1] > 60.0:
                    print(f"gf5 N={Nn} too slow, aborting N", flush=True)
                    abort_N = True
                    break
            if shat is None:
                F += 1
                continue
            ehat = np.where(shat <= 2, shat, shat - 5)
            ahat = (blk["b"] - ehat) % D
            if np.array_equal(ahat, blk["a"]):
                S += 1
                LA += mq * math.log2(5)
            else:
                U += 1
        if abort_N:
            out["cells"].append({"N": Nn, "aborted": "too-slow"})
            continue
        n = S + F + U
        fer = (F + U) / n
        leak = round(mq * math.log2(5) / Nn, 4)
        net = S * HA * Nn - LA - S * TAG
        out["cells"].append({"N": Nn, "B": B, "S": S, "F": F, "U": U,
                             "FER": round(fer, 4), "leak_pair": leak,
                             "Net_seg": round(net, 0),
                             "T_med": round(float(np.median(t_blk)), 1)})
        print(f"gf5 N={Nn} S={S} F={F} U={U} FER={fer:.3f} leak={leak} "
              f"Net={net:.0f} Tmed={np.median(t_blk):.1f}s", flush=True)
    (root / "s5_gf5conf.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"gf5conf done -> {root}")
    return out


def do_gf5_laws(root: Path) -> dict:
    """GF(5) per-source-law validation (N=1024, B=30, frac 0.19).

    S-5c real run uses per-source S-2 prefix laws for priors (matched);
    this validates each law on its own synthetic stream before freezing.
    Additive s5_gf5laws.json (supplement pattern, landed files untouched).
    """
    import json as _j
    from comparison_bench.src.comparison_bench.formal_ir import (
        msd_c1_nbldpc as A3,
    )
    s2 = _j.load(open("workspace/s_softmap/s2_20261009/s2_summary.json",
                      encoding="utf-8"))
    rng = np.random.default_rng(SEED + 424242)
    t0 = time.perf_counter()
    out: dict = {"cells": []}
    for src in ("T2-1M", "T2-1.5M", "T2-2M", "0dB", "4dB"):
        if time.perf_counter() - t0 > 3600:
            break
        fit = s2["sources"][src]["prefix_fit"]
        law = DoubleGauss(float(fit["sig"]), 100.0, float(fit["w"]))
        Nn, B, fr = 1024, 30, 0.19
        mq = int(Nn * fr)
        code = A3.construct(Nn, mq, 5, seed=8200)
        blks = gen_blocks(rng, B, Nn, law)
        S = F = U = 0
        LA = 0.0
        for blk in blks:
            v, e = blk["v"], blk["e"]
            s = (e % 5).astype(np.int64)
            F_ = law.interval_mass
            prior = np.zeros((Nn, 5))
            for i, vv in enumerate(v):
                for k in range(-6, 7):
                    prior[i, k % 5] += max(F_(float(vv) + k * BW - BW,
                                             float(vv) + k * BW), 0.0)
                prior[i] /= max(prior[i].sum(), 1e-300)
            syn = np.asarray((code.H @ s) % 5, dtype=np.int64).ravel()
            shat = A3.decode(code, np.zeros(Nn, dtype=np.int64), syn, prior, 100)
            if shat is None:
                F += 1
                continue
            ehat = np.where(shat <= 2, shat, shat - 5)
            ahat = (blk["b"] - ehat) % D
            if np.array_equal(ahat, blk["a"]):
                S += 1
                LA += mq * math.log2(5)
            else:
                U += 1
        n = S + F + U
        fer = (F + U) / n
        out["cells"].append({"source": src, "S": S, "F": F, "U": U,
                             "FER": round(fer, 4),
                             "Net_seg": round(S * HA * Nn - LA - S * TAG, 0)})
        print(f"gf5-laws {src} S={S} F={F} U={U} FER={fer:.3f}", flush=True)
    (root / "s5_gf5laws.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"gf5laws done -> {root}")
    return out
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--gf5-confirm", action="store_true")
    ap.add_argument("--gf5-laws", action="store_true")
    ap.add_argument("--tune-root", required=False, default=None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output-root", required=False, default=None)
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.gf5_confirm:
        if not args.output_root:
            raise SystemExit("--gf5-confirm requires --output-root")
        root = Path(args.output_root)
        if root.exists():
            raise SystemExit(f"output root not fresh: {root}")
        root.mkdir(parents=True, exist_ok=True)
        do_gf5_confirm(root)
        return
    if args.gf5_laws:
        if not args.tune_root:
            raise SystemExit("--gf5-laws requires --tune-root (landed gf5 root)")
        troot = Path(args.tune_root)
        if not troot.exists():
            raise SystemExit(f"gf5 root missing: {troot}")
        do_gf5_laws(troot)
        return
    if not args.full:
        raise SystemExit("S-5 tune runs only with --full")
    if not args.output_root:
        raise SystemExit("--full requires --output-root")
    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    import json as _j
    law = law_T2()
    curve = np.array(_j.load(
        open("workspace/s4d_fix/s4d_gate_20261009/s4d_curves.json",
             encoding="utf-8"))["T2-1M"]["curve"])
    rng = np.random.default_rng(SEED)
    t_all = time.perf_counter()
    CAP = 7200.0
    out: dict = {"seed": SEED, "soft_grid": [], "gf5": [], "n_verify": []}
    ctx = {"p_bar": 0.0607, "law": law, "curve": curve}
    H3 = build_ra(N, 128, QA, seed=7428)
    H3B = build_ra(N, 320, QA, seed=7450)
    # ---- S-5a + S-5b(i): joint gap grid with honest third level (B=200)
    for gap in GAPS_SOFT:
        if time.perf_counter() - t_all > CAP:
            break
        m = int(N * (1.0 - rate_of(ctx["p_bar"], gap)))
        H = build_ra(N, m, QA, seed=6000 + int(gap * 100))
        HB = build_ra(N, int(N * 0.10), QA, seed=6100)
        HR = build_ra(N, K2, QA, seed=6200)
        blks = gen_blocks(rng, 200, N, law)
        S = F = U = 0
        LA = LB = L3 = 0
        for blk in blks:
            res, L = chain_once(H, HB, HR, H3, H3B, blk, ctx)
            if res == "S":
                S += 1
                LA += m
                LB += L[1]
                L3 += 128 + 320
            elif res == "F":
                F += 1
            else:
                U += 1
        n = S + F + U
        fer = (F + U) / n
        leak = round((m + int(N * 0.10) + 128 + 320) / N, 4)
        net = S * HA * N - (LA + LB + L3) - S * TAG
        out["soft_grid"].append({"gap": gap, "m_A": m, "S": S, "F": F, "U": U,
                                 "FER": round(fer, 4), "leak_pair": leak,
                                 "Net_seg": round(net, 0)})
        print(f"soft gap={gap} m={m} S={S} F={F} U={U} FER={fer:.3f} "
              f"leak={leak} Net={net:.0f}", flush=True)
    feas = [g for g in out["soft_grid"] if g["FER"] <= 0.05]
    win = min(feas if feas else out["soft_grid"],
              key=lambda g: g["leak_pair"] if feas else g["FER"])
    print(f"winner gap={win['gap']} leak={win['leak_pair']} FER={win['FER']}",
          flush=True)
    # ---- S-5b(ii): GF(5) single-level arm (A3 QSPA, per-symbol priors)
    from comparison_bench.src.comparison_bench.formal_ir import (
        msd_c1_nbldpc as A3,
    )
    for frac in GF5_MS:
        if time.perf_counter() - t_all > CAP:
            break
        nq, mq = 1024, int(1024 * frac)
        code = A3.construct(nq, mq, 5, seed=8000 + int(frac * 100))
        blks = gen_blocks(rng, 60, nq, law)
        S = F = U = 0
        LA = 0.0
        for blk in blks:
            v, e = blk["v"], blk["e"]
            s = (e % 5).astype(np.int64)
            F_ = law.interval_mass
            prior = np.zeros((nq, 5))
            for i, vv in enumerate(v):
                for k in range(-6, 7):
                    prior[i, k % 5] += max(F_(float(vv) + k * BW - BW,
                                             float(vv) + k * BW), 0.0)
                prior[i] /= max(prior[i].sum(), 1e-300)
            syn = np.asarray((code.H @ s) % 5, dtype=np.int64).ravel()
            shat = A3.decode(code, np.zeros(nq, dtype=np.int64), syn, prior, 100)
            if shat is None:
                F += 1
                continue
            ehat = np.where(shat <= 2, shat, shat - 5)
            ahat = (blk["b"] - ehat) % D
            if np.array_equal(ahat, blk["a"]):
                S += 1
                LA += mq * math.log2(5)
            else:
                U += 1
        n = S + F + U
        fer = (F + U) / n
        leak = round(mq * math.log2(5) / nq, 4)
        net = S * HA * nq - LA - S * TAG
        out["gf5"].append({"m_frac": frac, "S": S, "F": F, "U": U,
                           "FER": round(fer, 4), "leak_pair": leak,
                           "Net_seg": round(net, 0)})
        print(f"gf5 frac={frac} S={S} F={F} U={U} FER={fer:.3f} leak={leak} "
              f"Net={net:.0f}", flush=True)
    # ---- N-verify joint winner (per-bit R16 selection)
    for Nn in (8192, 16384):
        if time.perf_counter() - t_all > CAP:
            break
        mw = int(Nn * (1.0 - rate_of(ctx["p_bar"], win["gap"])))
        Hw = build_ra(Nn, mw, QA, seed=9000 + Nn)
        HBw = build_ra(Nn, int(Nn * 0.10), QA, seed=9100 + Nn)
        HRw = build_ra(Nn, K2, QA, seed=9200 + Nn)
        H3w = build_ra(Nn, 128, QA, seed=9300 + Nn)
        H3Bw = build_ra(Nn, 320, QA, seed=9400 + Nn)
        blks = gen_blocks(rng, 20, Nn, law)
        S = F = U = 0
        LA = LB = L3 = 0
        for blk in blks:
            res, L = chain_once(Hw, HBw, HRw, H3w, H3Bw, blk, ctx)
            if res == "S":
                S += 1
                LA += mw
                LB += L[1]
                L3 += 128 + 320
            elif res == "F":
                F += 1
            else:
                U += 1
        n = S + F + U
        fer = (F + U) / n
        out["n_verify"].append({"N": Nn, "S": S, "F": F, "U": U,
                                "FER": round(fer, 4),
                                "leak_pair": round((mw + int(Nn * 0.10) + 448) / Nn, 4),
                                "Net_seg": round(S * HA * Nn - (LA + LB + L3) - S * TAG, 0)})
        print(f"verify N={Nn} S={S} F={F} U={U} FER={fer:.3f}", flush=True)
    (root / "s5_tune.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"s5 tune done wall={round(time.perf_counter()-t_all,1)}s -> {root}")


if __name__ == "__main__":
    main()
