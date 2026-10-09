"""S-3 soft-vs-hard real-data two-level decode (S3_PREEXECUTE.md, DECIDE).

Modes: --smoke (real, tiny) | --tune (synthetic, R16) | --full (frozen, each
cell once). Fresh-root guards everywhere. Standard RA ensemble instances
(seeds frozen, not new codes). Level-A: hard uniform LLR vs soft per-symbol
LLR (A6 interface, S-1 verified Bob-side). Level-B: frozen both arms
(structurally-pinned LLRs) + K2=64 one-shot rescue. undetected kept single,
never merged. Noisy: scipy sparse syndromes, ldpc BpOsdDecoder (A6 settings).
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy import sparse
import scipy.stats as st

SPAN_PS = 204800
BW = 200
D = SPAN_PS // BW
HA_OP = 10.0
TAG = 64
K2 = 64
QA = 5  # frozen: RA info weight (G-5 strength; q=3 proved too weak in tune post-mortem)
SEED = 20261009
NS = (4096, 8192, 16384)
GAPS_A = (0.08, 0.12, 0.18)
FRACS_B = (0.05, 0.10, 0.15)

SOURCES = {
    "T2-1M": ("D:/Data/Raw Data/2026.1.21/Type2_1M_3s_2026-01-21_184040/Type2_1M_3s_2026-01-21_184040.ttbin", -50),
    "T2-1.5M": ("D:/Data/Raw Data/2026.1.21/Type2_1-5M_3s_2026-01-21_183806/Type2_1-5M_3s_2026-01-21_183806.ttbin", +50),
    "T2-2M": ("D:/Data/Raw Data/2026.1.21/Type2_2M_3s_2026-01-21_183657/Type2_2M_3s_2026-01-21_183657.ttbin", +50),
    "0dB": ("D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_0dB_2026-01-23_174534.1.ttbin", -50),
    "4dB": ("D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_4dB_2026-01-23_174758.1.ttbin", -50),
}
MAIN_SOURCES = ("T2-1M", "T2-1.5M", "T2-2M")


def Phi(z: float) -> float:  # noqa: N802
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def h2(x: float) -> float:
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -(x * math.log2(x) + (1.0 - x) * math.log2(1.0 - x))


def build_ra(n: int, m: int, q: int, seed: int) -> sparse.csr_matrix:
    k = n - m
    rng = np.random.default_rng(seed)
    H = sparse.lil_matrix((m, n), dtype=np.uint8)
    order = rng.permutation(m * ((q * k) // m + 1))[:q * k]
    for j in range(k):
        for tt in range(q):
            r = int(order[(j * q + tt) % len(order)] % m)
            H[r, j] ^= 1
    for i in range(m):
        H[i, k + i] ^= 1
        if i > 0:
            H[i, k + i - 1] ^= 1
    return H.tocsr()


DEC_MAX_ITER = 100  # frozen: numba min-sum default (M3-verified kernel)


def decode(H, syn: np.ndarray, channel) -> np.ndarray:
    """Frozen S-3 decoder: repo numba syndrome min-sum (M3 45.9x kernel).

    Same settings both arms; differs from A6's ldpc product-sum (verification
    only) — stated here, frozen for all S-3 cells.
    """
    from comparison_bench.src.comparison_bench.methods.binary_spa_numba import (
        decode_error_min_sum_llr_numba,
    )
    if sparse.issparse(H):
        Hd = H.toarray().astype(np.uint8)
    else:
        Hd = np.ascontiguousarray(H, dtype=np.uint8)
    err, _ok, _it, _tot = decode_error_min_sum_llr_numba(
        Hd, np.asarray(syn, dtype=np.uint8).ravel(),
        np.asarray(channel, dtype=np.float64).ravel(), DEC_MAX_ITER)
    return np.asarray(err, dtype=np.uint8)


def p_of_v(v: float, sig: float, mu: float) -> float:
    p = 1.0 - (Phi((v - mu) / sig) - Phi((v - BW - mu) / sig))
    return min(max(p, 1e-6), 1.0 - 1e-6)


def _Phi_w(v: float, sig: float, mu: float, w: float) -> float:
    return (1.0 - w) * Phi((v - mu) / sig) + w * Phi((v - mu) / 100.0)


def p_of_v_mix(v: float, sig: float, mu: float, w: float) -> float:
    """Per-symbol error prob under the S-2 prefix DoubleGauss law
    (core sig + wide comp w@100ps). Pure-Gauss p_of_v is the w=0 special
    case; the mixture is the frozen S-3 LLR (packet: wide comp = prefix w).
    Overconfident-narrow LLRs on wide events poisoned tune v1 (soft FER floor).
    """
    p = 1.0 - (_Phi_w(v, sig, mu, w) - _Phi_w(v - BW, sig, mu, w))
    return min(max(p, 1e-6), 1.0 - 1e-6)


def llr(p: float) -> float:
    return math.log((1.0 - p) / p)


def gen_block(rng: np.random.Generator, N: int, sig: float, mu: float, w: float):
    """Synthetic ternary-error block (calibrated-regime Gaussian + wide)."""
    v = rng.uniform(0.0, BW, size=N)
    wide = rng.random(N) < w
    delta = np.where(wide, rng.normal(mu, 100.0, size=N), rng.normal(mu, sig, size=N))
    e = -np.floor((v - delta) / BW).astype(np.int64)
    x = (e % 2).astype(np.uint8)          # level-A target (LSB diff, b=0)
    sgn = (e == -1).astype(np.uint8)      # level-B target on marked
    return v, e, x, sgn


_W: dict = {}


def _w_init(HA_d, HB_d, HR_d, p_bar, sig, mu, w, p_minus, arm, mA, mB) -> None:
    _W.update(H_A=np.ascontiguousarray(HA_d, dtype=np.uint8),
              H_B=np.ascontiguousarray(HB_d, dtype=np.uint8),
              H_R=np.ascontiguousarray(HR_d, dtype=np.uint8),
              p_bar=p_bar, sig=sig, mu=mu, w=w, p_minus=p_minus, arm=arm,
              mA=mA, mB=mB)


def _pack(blocks: list[dict]) -> list[tuple]:
    return [(b["x"], b["b0"], b["a1"], b["b1"], b["v"], b["a"], b["b"]) for b in blocks]


def _block_once(H_A, H_B, H_R, blk: dict, p_bar: float, sig: float, mu: float,
                w: float, p_minus: float, arm: str, mA: int, mB: int) -> tuple:
    x = blk["x"]
    t0 = time.perf_counter()
    synA = np.asarray((H_A @ x) % 2, dtype=np.uint8).ravel()
    if arm == "hard":
        chA = [llr(p_bar)] * len(x)
    else:
        chA = [llr(p_of_v_mix(vv, sig, mu, w)) for vv in blk["v"]]
    xa = decode(H_A, synA, chA)
    okA = bool(np.array_equal(xa, x) and np.array_equal(((H_A @ xa) % 2).ravel(), synA))
    la = mA
    lb = r = 0
    okB = False
    exact = False
    if okA:
        b0 = blk["b0"]
        # POST-LANDING FIX 2 (S-4d root cause, primary): marked (e!=0) is (xa==1)
        # since xa IS the difference x=a0^b0 — NOT (xa!=b0), which inflates the
        # set ~8x on real data (identical iff b0=0, hence invisible on synthetic)
        # and hands level-B an underdetermined system: the S-3 100% mechanism
        # (compounding the prior-sign fix above). Landed S/F/U stand (see S4D_RESULT).
        marked = (xa == 1)
        mk = int(marked.sum())
        y = blk["a1"][marked]
        lb = mB  # level-B syndrome always transmitted
        # POST-LANDING FIX (S-4d root cause): xa is the difference x=a0^b0,
        # not a0. Recover a0hat=xa^b0 for prior signs AND reconstruction.
        # S-3 full ran with xa-as-a0 (50%-flipped priors on real data, invisible
        # on synthetic b0=0). S-3's landed S/F/U stand: okB failed before exact
        # was reached, and okA never used a0. See S4D_RESULT.
        a0hat = (xa ^ b0).astype(np.uint8)
        yhat = np.empty((0,), dtype=np.uint8)
        if mk == 0:
            okB = True  # nothing to reconcile at level-B
        else:
            synB = np.asarray((H_B[:, marked] @ y) % 2, dtype=np.uint8).ravel()
            chB = np.where((blk["b1"][marked] ^ a0hat[marked]) == 1, -llr(p_minus), llr(p_minus))
            Hsub = H_B[:, marked]
            yhat = decode(Hsub, synB, [float(c) for c in chB])
            okB = bool(np.array_equal(yhat, y))
            if not okB:  # K2 one-shot rescue with extended rows
                synR = np.asarray((H_R[:, marked] @ y) % 2, dtype=np.uint8).ravel()
                Hsub2 = sparse.vstack([Hsub, H_R[:, marked]]).tocsr()
                yhat = decode(Hsub2, np.concatenate([synB, synR]),
                              [float(c) for c in chB])
                okB = bool(np.array_equal(yhat, y))
                r = K2
                lb += K2
        if okB:
            a1hat = blk["b1"].copy()  # unmarked: e=0 -> a=b -> a1=b1
            a1hat[marked] = yhat
            # reconstruct: a = b-e; sgn=(e==-1): sgn=0 (e=+1) -> b-1, sgn=1 -> b+1
            ahat = blk["b"].copy()
            sgn = (yhat ^ blk["b1"][marked] ^ a0hat[marked]).astype(bool)
            ahat[marked] = np.where(sgn, (blk["b"][marked] + 1) % D,
                                    (blk["b"][marked] - 1) % D)
            exact = bool(np.array_equal(ahat, blk["a"]))
    t = time.perf_counter() - t0
    if okA and okB and exact:
        res = "S"
    elif okA and okB:
        res = "U"  # valid-wrong: checks passed but wrong (never merged)
    else:
        res = "F"
    row = {"okA": bool(okA), "okB": bool(okB), "exact": bool(exact),
           "L": int(la + lb + r), "L_A": int(la), "L_B": int(lb), "L_R": int(r)}
    return res, t, row


def _w_one(task: tuple) -> tuple:
    x, b0, a1, b1, v, a, b = task
    blk = {"x": x, "b0": b0, "a1": a1, "b1": b1, "v": v, "a": a, "b": b}
    return _block_once(_W["H_A"], _W["H_B"], _W["H_R"], blk, _W["p_bar"],
                       _W["sig"], _W["mu"], _W["w"], _W["p_minus"], _W["arm"],
                       _W["mA"], _W["mB"])


def run_cell(*, H_A, H_B, H_R, blocks: list[dict], p_bar: float,
             sig: float, mu: float, p_minus: float, arm: str,
             nproc: int = 16, w: float = 0.0) -> dict:
    """One (source,N,arm) cell over frozen real/synthetic blocks.

    Block-level parallelism (nproc worker processes, ordered results):
    blocks are independent given frozen (H, params); serial schedule +
    fixed order keep decoding deterministic. nproc=1 forces serial.
    Returns per-block rows (needed for paired McNemar; caller persists them —
    cells are never re-run).
    """
    mA = H_A.shape[0]
    mB = H_B.shape[0]
    if nproc <= 1 or len(blocks) <= 8:
        outs = [_block_once(H_A, H_B, H_R, blk, p_bar, sig, mu, w, p_minus, arm, mA, mB)
                for blk in blocks]
    else:
        import concurrent.futures as _cf
        # dense H shipped once per worker (numba kernel needs dense anyway)
        def _den(H):
            return H.toarray().astype(np.uint8) if sparse.issparse(H) else np.ascontiguousarray(H, dtype=np.uint8)
        _W_INIT = (_den(H_A), _den(H_B), _den(H_R),
                   float(p_bar), float(sig), float(mu), float(w), float(p_minus), arm, mA, mB)
        with _cf.ProcessPoolExecutor(max_workers=nproc,
                                     initializer=_w_init, initargs=_W_INIT) as ex:
            outs = list(ex.map(_w_one, _pack(blocks)))
    S = F = U = 0
    LA = LB = RS = 0
    T = []
    rows = []
    for res, t, row in outs:
        T.append(t)
        rows.append(row)
        if res == "S":
            S += 1
            LA += row["L_A"]
            LB += row["L_B"]
            RS += row["L_R"]
        elif res == "U":
            U += 1
        else:
            F += 1
    n = S + F + U
    assert n > 0, "empty cell"
    fer = (F + U) / n if n else 1.0
    # Clopper-Pearson 95% (exact beta quantiles, with all-fail/all-ok edges)
    fails = F + U
    lo = 0.0 if fails == 0 else float(st.beta.ppf(0.025, fails, n - fails + 1))
    hi = 1.0 if fails == n else float(st.beta.ppf(0.975, fails + 1, n - fails))
    net = S * (HA_OP * len(blocks[0]["x"]) - 0) - (LA + LB) - S * TAG
    return {"S": S, "F": F, "U": U, "FER": round(fer, 4),
            "FER_CP95": [round(float(lo), 4), round(float(hi), 4)],
            "L_A": LA, "L_B": LB, "L_rescue": RS, "L_tot": LA + LB + RS,
            "Net_seg": round(net, 0), "T_med": round(float(np.median(T)), 3),
            "T_tot": round(float(sum(T)), 1), "rows": rows}


def real_blocks(source: str, N: int, law: dict, limit: int | None = None) -> list[dict]:
    """Frozen real-data blocks: frame -> calibrate -> kept -> chunk (level-A/B truth)."""
    from comparison_bench.src.comparison_bench.io import align_wrapper as aw
    from comparison_bench.src.comparison_bench.io.ttbin_compat import install_timetagger_alias
    from comparison_bench.src.comparison_bench.cli.probes_closed import m0_realframe_runner as _m0
    install_timetagger_alias()
    from src.qkd_io.ttbin_pipeline import _frame_global, _pair_nearest_unique, read_ttbin_events
    path, dl = SOURCES[source]
    events = read_ttbin_events(path)
    t = np.asarray(events.time_ps, dtype=np.int64)
    valid = (np.asarray(events.event_type, dtype=np.int64) == 0) if events.event_type is not None else np.ones(t.shape, dtype=bool)
    ch = np.asarray(events.channel, dtype=np.int64)
    t_a, t_b = t[valid & (ch == _m0.CH_A)], t[valid & (ch == _m0.CH_B)]
    tmin = int(t.min())
    off = aw.require_alignment_passed(aw.derive_alignment(events=events, ch_a=_m0.CH_A, ch_b=_m0.CH_B))
    del events
    pa, pb = _pair_nearest_unique(t_a=t_a, t_b=t_b, window_ps=_m0.COIN_WINDOW_PS, offset_ps=int(off))
    pb = pb + np.int64(dl)
    fa, sa = _frame_global(t_ps=pa, bin_width_ps=BW, frame_bins=D, t0_ps=tmin)
    fb, sb = _frame_global(t_ps=pb, bin_width_ps=BW, frame_bins=D, t0_ps=tmin)
    keep = (fa >= 0) & (fb >= 0) & (fa == fb)
    aa, bb = sa[keep].astype(np.int64), sb[keep].astype(np.int64)
    pbt = pb[keep]
    ee = (bb - aa) % D
    x = (ee % 2).astype(np.uint8)
    b0 = (bb % 2).astype(np.uint8)
    a0 = (aa % 2).astype(np.uint8)
    b1 = ((bb >> 1) & 1).astype(np.uint8)
    a1 = ((aa >> 1) & 1).astype(np.uint8)
    v = ((pbt.astype(np.int64) - np.int64(tmin)) % np.int64(BW)).astype(np.float64)
    nblk = len(x) // N
    out = []
    for i in range(nblk):
        s = slice(i * N, (i + 1) * N)
        out.append({"x": x[s], "b0": b0[s], "a1": a1[s], "b1": b1[s],
                    "v": v[s], "a": aa[s], "b": bb[s]})
        if limit is not None and len(out) >= limit:
            break
    return out


def synth_blocks(rng: np.random.Generator, n: int, N: int, sig: float, mu: float, w: float) -> list[dict]:
    out = []
    for _ in range(n):
        v, e, x, sgn = gen_block(rng, N, sig, mu, w)
        aa = (-e) % D  # true Alice symbols (b fixed at 0)
        out.append({"x": x, "b0": np.zeros(N, dtype=np.uint8),
                    "a1": ((aa >> 1) & 1).astype(np.uint8),
                    "b1": np.zeros(N, dtype=np.uint8), "v": v,
                    "a": aa.astype(np.int64), "b": np.zeros(N, dtype=np.int64)})
    return out


def self_test() -> None:
    rng = np.random.default_rng(SEED)
    H = build_ra(64, 32, QA, seed=7)
    assert H.shape == (32, 64) and H.nnz > 0
    x = (rng.random(64) < 0.1).astype(np.uint8)
    syn = np.asarray((H @ x) % 2, dtype=np.uint8).ravel()
    assert syn.shape == (32,)
    v, e, xs, sgn = gen_block(rng, 512, 25.0, 0.0, 0.0)
    assert abs(float(xs.mean()) - 0.0997) < 0.03, xs.mean()
    assert abs(p_of_v(0.0, 25.0, 0.0) - 0.5) < 0.02  # bin edge
    assert p_of_v(100.0, 25.0, 0.0) < 0.01  # bin centre
    assert llr(0.1) > 0 and abs(llr(0.5)) < 1e-12
    print("s3 self-test OK (RA/syndrome/channel/LLR)")


P_MINUS_TUNE = 0.6
P_MINUS_SRC = {"T2-1M": 0.609, "T2-1.5M": 0.519, "T2-2M": 0.519,
               "0dB": 0.529, "4dB": 0.609}  # B3/C-0 calibrated p- (frozen)


NPROC_OF_N = {4096: 16, 8192: 8, 16384: 4}  # dense-message memory bound


def rate_of(p: float, gap: float) -> float:
    return max(0.05, 1.0 - h2(p) - gap)


def tune_law() -> dict:
    import json as _j
    d = _j.load(open("workspace/s_softmap/s2_20261009/s2_summary.json", encoding="utf-8"))
    f = d["sources"]["T2-1M"]["prefix_fit"]
    return {"sig": f["sig"], "mu": 0.0, "w": f["w"], "p_bar": 0.0607}


def do_tune_sup(root: Path, tune: dict) -> dict:
    """Supplement (additive s3_tune_sup.json): wider gaps {0.25,0.35} at N=4096
    (both arms, B=200) + soft-arm large-N resolution (B=60). Landed tune untouched."""
    rng = np.random.default_rng(SEED + 555)
    law = tune["law"]
    sup: dict = {"gaps": [], "verify60": []}
    t0 = time.perf_counter()
    for arm in ("hard", "soft"):
        for gap in (0.25, 0.35):
            m = int(4096 * (1.0 - rate_of(law["p_bar"], gap)))
            H = build_ra(4096, m, QA, seed=2000 + int(gap * 100))
            HB = build_ra(4096, int(4096 * float(tune["levelB"]["frac"])), QA, seed=2500)
            HR = build_ra(4096, K2, QA, seed=2600)
            blks = synth_blocks(rng, 200, 4096, law["sig"], law["mu"], law["w"])
            r = run_cell(H_A=H, H_B=HB, H_R=HR, blocks=blks, p_bar=law["p_bar"],
                         sig=law["sig"], mu=law["mu"], p_minus=P_MINUS_TUNE, arm=arm,
                         nproc=NPROC_OF_N[4096], w=law["w"])
            sup["gaps"].append({"arm": arm, "gap": gap, "N": 4096,
                                "FER": r["FER"], "Net_seg": r["Net_seg"], "T_med": r["T_med"]})
            print(f"sup {arm} N=4096 gap={gap} FER={r['FER']} Net={r['Net_seg']} T={r['T_med']}s", flush=True)
    gap_soft = tune["arms"]["soft"]["gap"]
    for N in (8192, 16384):
        m = int(N * (1.0 - rate_of(law["p_bar"], gap_soft)))
        H = build_ra(N, m, QA, seed=3000 + N)
        HB = build_ra(N, int(N * float(tune["levelB"]["frac"])), QA, seed=3500 + N)
        HR = build_ra(N, K2, QA, seed=3600 + N)
        blks = synth_blocks(rng, 60, N, law["sig"], law["mu"], law["w"])
        r = run_cell(H_A=H, H_B=HB, H_R=HR, blocks=blks, p_bar=law["p_bar"],
                     sig=law["sig"], mu=law["mu"], p_minus=P_MINUS_TUNE, arm="soft",
                     nproc=NPROC_OF_N[N], w=law["w"])
        sup["verify60"].append({"N": N, "FER": r["FER"], "Net_seg": r["Net_seg"],
                                "T_med": r["T_med"], "B": 60})
        print(f"sup soft N={N} B=60 FER={r['FER']} Net={r['Net_seg']} T={r['T_med']}s", flush=True)
    sup["wall_s"] = round(time.perf_counter() - t0, 1)
    (root / "s3_tune_sup.json").write_text(json.dumps(sup, indent=1), encoding="utf-8")
    print(f"sup done -> {root}")
    return sup


def do_tune(root: Path) -> dict:
    rng = np.random.default_rng(SEED)
    law = tune_law()
    frozen: dict = {"law": law, "p_minus": P_MINUS_TUNE, "arms": {}}
    t0 = time.perf_counter()
    TUNE_CAP = 3000.0
    # Level-A: full gap ladder at N=4096 (B=200), winner verified at 8192/16384 (B=100)
    for arm in ("hard", "soft"):
        grid = []
        for gap in GAPS_A:
            if time.perf_counter() - t0 > TUNE_CAP:
                break
            m = int(4096 * (1.0 - rate_of(law["p_bar"], gap)))
            H = build_ra(4096, m, QA, seed=100 + GAPS_A.index(gap))
            blks = synth_blocks(rng, 200, 4096, law["sig"], law["mu"], law["w"])
            HB = build_ra(4096, int(4096 * 0.10), QA, seed=500)
            HR = build_ra(4096, K2, QA, seed=600)
            r = run_cell(H_A=H, H_B=HB, H_R=HR, blocks=blks, p_bar=law["p_bar"],
                         sig=law["sig"], mu=law["mu"], p_minus=P_MINUS_TUNE, arm=arm,
                         nproc=NPROC_OF_N[4096], w=law["w"])
            print(f"tune L-A {arm} N=4096 gap={gap} FER={r['FER']} Net={r['Net_seg']} T={r['T_med']}s", flush=True)
            grid.append({"gap": gap, "m": m, "FER": r["FER"], "Net_seg": r["Net_seg"],
                         "T_med": r["T_med"]})
        if not grid:
            raise SystemExit(f"tune budget exhausted before any {arm} point")
        best = max(grid, key=lambda g: g["Net_seg"])
        # verify at larger N (B=20: order-of-magnitude selection only, stated)
        ver = []
        for N in (8192, 16384):
            if time.perf_counter() - t0 > TUNE_CAP:
                break
            m = int(N * (1.0 - rate_of(law["p_bar"], best["gap"])))
            H = build_ra(N, m, QA, seed=100 + GAPS_A.index(best["gap"]) + N)
            blks = synth_blocks(rng, 20, N, law["sig"], law["mu"], law["w"])
            HB = build_ra(N, int(N * 0.10), QA, seed=500 + N)
            HR = build_ra(N, K2, QA, seed=600 + N)
            r = run_cell(H_A=H, H_B=HB, H_R=HR, blocks=blks, p_bar=law["p_bar"],
                         sig=law["sig"], mu=law["mu"], p_minus=P_MINUS_TUNE, arm=arm,
                         nproc=NPROC_OF_N[N], w=law["w"])
            print(f"tune L-A {arm} N={N} FER={r['FER']} Net={r['Net_seg']} T={r['T_med']}s", flush=True)
            ver.append({"N": N, "FER": r["FER"], "Net_seg": r["Net_seg"], "T_med": r["T_med"]})
        # R16: per-arm optimal N by Net_seg (incl. N=4096 grid point, rescaled per-block)
        cand = [{"N": 4096, "FER": best["FER"],
                 "Net_seg": best["Net_seg"], "T_med": best["T_med"], "gap": best["gap"]}]
        for v in ver:
            cand.append({**v, "gap": best["gap"]})
        opt = max(cand, key=lambda c: c["Net_seg"])
        frozen["arms"][arm] = {"gap": best["gap"], "grid": grid, "verify": ver, "opt": opt}
    # Level-B frac: same block sample per frac (rng reset -> fair), metric =
    # level-B conditional fail P(not okB | okA). Pick min conditional, tie -> smaller frac.
    fb = []
    gap = frozen["arms"]["soft"]["gap"]
    m = int(4096 * (1.0 - rate_of(law["p_bar"], gap)))
    H = build_ra(4096, m, QA, seed=777)
    for fr in FRACS_B:
        if time.perf_counter() - t0 > TUNE_CAP:
            break
        HB = build_ra(4096, int(4096 * fr), QA, seed=800 + int(fr * 100))
        HR = build_ra(4096, K2, QA, seed=900)
        blks = synth_blocks(np.random.default_rng(SEED + 999), 200, 4096,
                            law["sig"], law["mu"], law["w"])
        r = run_cell(H_A=H, H_B=HB, H_R=HR, blocks=blks, p_bar=law["p_bar"],
                     sig=law["sig"], mu=law["mu"], p_minus=P_MINUS_TUNE, arm="soft",
                     nproc=NPROC_OF_N[4096], w=law["w"])
        nA = sum(1 for b in r["rows"] if b["okA"])
        nAB = sum(1 for b in r["rows"] if b["okA"] and not b["okB"])
        cond = (nAB / nA) if nA else 1.0
        fb.append({"frac": fr, "FER": r["FER"], "cond_B_fail": round(cond, 4),
                   "nA": nA})
        print(f"tune L-B frac={fr} FER={r['FER']} condB={cond:.4f} (nA={nA})", flush=True)
    frozen["levelB"] = {"scan": fb,
                        "frac": min(fb, key=lambda f: (f["cond_B_fail"], f["frac"]))["frac"] if fb else FRACS_B[-1]}
    (root / "s3_tune.json").write_text(json.dumps(frozen, indent=1), encoding="utf-8")
    print(f"tune frozen: {json.dumps({a: frozen['arms'][a]['opt'] for a in frozen['arms']})}, LB frac={frozen['levelB']['frac']} -> {root}")
    return frozen


def do_smoke(root: Path) -> dict:
    law = {"sig": 13.34, "mu": 0.0, "w": 0.0069, "p_bar": 0.0607}
    blks = real_blocks("T2-1M", 4096, law, limit=2)
    m = int(4096 * (1.0 - rate_of(law["p_bar"], 0.12)))
    H = build_ra(4096, m, QA, seed=112)
    HB = build_ra(4096, int(4096 * 0.10), QA, seed=512)
    HR = build_ra(4096, K2, QA, seed=612)
    out = {}
    for arm in ("hard", "soft"):
        r = run_cell(H_A=H, H_B=HB, H_R=HR, blocks=blks, p_bar=law["p_bar"],
                     sig=law["sig"], mu=law["mu"], p_minus=P_MINUS_SRC["T2-1M"], arm=arm,
                     nproc=NPROC_OF_N[4096], w=law["w"])
        out[arm] = {"S": r["S"], "F": r["F"], "U": r["U"], "T_med": r["T_med"], "T_tot": r["T_tot"]}
        print(f"smoke {arm}: S={r['S']} F={r['F']} U={r['U']} T_med={r['T_med']}s", flush=True)
    tmax = max(out["hard"]["T_med"], out["soft"]["T_med"])
    out["T_block_max"] = tmax
    (root / "s3_smoke.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def source_p_bar(src: str) -> float:
    """Frozen model-marginal p per source (S-2 prefix DoubleGauss at mu_cal)."""
    import json as _j
    from comparison_bench.src.comparison_bench.formal_ir.msd_a3_jitter_model import (
        DoubleGauss, error_pmf, summary_of_pmf)
    d = _j.load(open("workspace/s_softmap/s2_20261009/s2_summary.json", encoding="utf-8"))
    fit = d["sources"][src]["prefix_fit"]
    dl = SOURCES[src][1]
    law = DoubleGauss(float(fit["sig"]), 100.0, float(fit["w"]))
    return summary_of_pmf(error_pmf(law=law, bw=float(BW), mu=float(fit["mu"]) - dl,
                                    window=None))["p"]


def mcnemar(soft_only: int, hard_only: int) -> float:
    """Exact two-sided McNemar p on discordant counts."""
    from math import comb
    n_d, k = soft_only + hard_only, min(soft_only, hard_only)
    if n_d == 0:
        return 1.0
    return min(1.0, 2.0 * sum(comb(n_d, i) for i in range(k + 1)) / 2.0 ** n_d)


def do_full(root: Path, tune: dict) -> dict:
    import json as _j
    t_start = time.perf_counter()
    BUDGET_CAP = 14400.0
    summary: dict = {"tune": tune, "cells": {}, "mcnemar": {}, "secondary": {}}
    jlf = (root / "s3_blocks.jsonl").open("w", encoding="utf-8")
    import json as _jj
    s2 = _jj.load(open("workspace/s_softmap/s2_20261009/s2_summary.json", encoding="utf-8"))

    def run_source(src: str) -> dict:
        law = s2["sources"][src]["prefix_fit"]
        sig = float(law["sig"])
        w_src = float(law["w"])
        p_bar = source_p_bar(src)
        Ns = sorted({int(tune["arms"][a]["opt"]["N"]) for a in ("hard", "soft")})
        cache: dict[int, list[dict]] = {}
        out: dict = {}
        for N in Ns:
            if time.perf_counter() - t_start > BUDGET_CAP:
                out[N] = {"stopped": "budget-cap"}
                print(f"full {src} N={N}: STOPPED budget-cap", flush=True)
                continue
            cache[N] = real_blocks(src, N, law)  # read once, both arms share blocks
            for arm in ("hard", "soft"):
                opt = tune["arms"][arm]["opt"]
                gap = float(opt["gap"])
                m = int(N * (1.0 - rate_of(p_bar, gap)))
                H = build_ra(N, m, QA, seed=1000 + N + (1 if arm == "soft" else 0))
                fr = float(tune["levelB"]["frac"])
                HB = build_ra(N, int(N * fr), QA, seed=2000 + N)
                HR = build_ra(N, K2, QA, seed=3000 + N)
                r = run_cell(H_A=H, H_B=HB, H_R=HR, blocks=cache[N], p_bar=p_bar,
                             sig=sig, mu=0.0, p_minus=P_MINUS_SRC[src], arm=arm,
                             nproc=NPROC_OF_N[N], w=w_src)
                rows = r.pop("rows")
                for bi, brow in enumerate(rows):
                    jlf.write(_jj.dumps({"cell": f"{src}/{arm}/{N}", "block": bi,
                                         **{k: bool(brow[k]) if isinstance(brow[k], (bool, np.bool_)) else brow[k]
                                            for k in ("okA", "okB", "exact")},
                                         "L": int(brow["L"])}) + "\n")
                r.update({"source": src, "arm": arm, "N": N, "gap": gap, "m_A": m,
                          "m_B": int(N * fr), "p_bar": round(p_bar, 4)})
                out[f"{arm}/{N}"] = (r, rows)
                print(f"full {src} {arm} N={N}: S={r['S']} F={r['F']} U={r['U']} "
                      f"FER={r['FER']}{r['FER_CP95']} Net={r['Net_seg']} T={r['T_tot']}s", flush=True)
        return out

    for src in MAIN_SOURCES:
        cells = run_source(src)
        for key, val in cells.items():
            if isinstance(val, dict) and "stopped" in val:
                summary["cells"][f"{src}/{key}"] = val
                continue
            r, _rows = val
            summary["cells"][f"{src}/{key}"] = r
        # paired McNemar per N from persisted rows (same blocks both arms)
        Ns = sorted({int(tune["arms"][a]["opt"]["N"]) for a in ("hard", "soft")});
        for N in Ns:
            ka, kb = f"{src}/hard/{N}", f"{src}/soft/{N}"
            if ka not in cells or kb not in cells:
                continue
            ra, rows_a = cells[ka]
            rb, rows_b = cells[kb]
            if isinstance(ra, dict) and "stopped" in ra:
                continue
            ah = [row["okA"] and row["okB"] and row["exact"] for row in rows_a]
            ast_ = [row["okA"] and row["okB"] and row["exact"] for row in rows_b]
            b = sum(1 for h, s in zip(ah, ast_) if h and not s)
            c = sum(1 for h, s in zip(ah, ast_) if (not h) and s)
            summary["mcnemar"][f"{src}/{N}"] = {"hard_only": b, "soft_only": c,
                                                "p": round(mcnemar(c, b), 4)}
            print(f"mcnemar {src} N={N}: hard_only={b} soft_only={c} "
                  f"p={summary['mcnemar'][f'{src}/{N}']['p']}", flush=True)
        (root / "s3_cells.json").write_text(_j.dumps(summary, indent=1), encoding="utf-8")
    # secondary regime (0dB/4dB) only if <50% budget elapsed
    elapsed = time.perf_counter() - t_start
    if elapsed < 0.5 * BUDGET_CAP:
        for src in ("0dB", "4dB"):
            cells = run_source(src)
            for key, val in cells.items():
                if isinstance(val, dict) and "stopped" in val:
                    summary["secondary"][f"{src}/{key}"] = val
                    continue
                r, _rows = val
                summary["secondary"][f"{src}/{key}"] = r
            (root / "s3_cells.json").write_text(_j.dumps(summary, indent=1), encoding="utf-8")
    else:
        summary["secondary"] = {"skipped": f"elapsed {round(elapsed,0)}s >= 50% cap"}
    summary["wall_s_total"] = round(time.perf_counter() - t_start, 1)
    (root / "s3_cells.json").write_text(_j.dumps(summary, indent=1), encoding="utf-8")
    jlf.close()
    print(f"full done wall={summary['wall_s_total']}s -> {root}")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--tune", action="store_true")
    ap.add_argument("--tune-sup", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output-root", required=False, default=None)
    ap.add_argument("--tune-root", required=False, default=None)
    # R16 post-hoc selection overrides (recorded in RESULT; landed tune untouched)
    ap.add_argument("--opt-hard-N", type=int, default=None)
    ap.add_argument("--opt-soft-N", type=int, default=None)
    ap.add_argument("--gap-hard", type=float, default=None)
    ap.add_argument("--gap-soft", type=float, default=None)
    ap.add_argument("--frac-B", type=float, default=None)
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.tune_sup:  # additive supplement into the landed tune root (no fresh gate)
        import json as _j
        if not args.tune_root:
            raise SystemExit("--tune-sup requires --tune-root (landed tune)")
        troot = Path(args.tune_root)
        if not troot.exists():
            raise SystemExit(f"tune root missing: {troot}")
        tune = _j.load(open(troot / "s3_tune.json", encoding="utf-8"))
        do_tune_sup(troot, tune)
        return
    if not args.output_root:
        raise SystemExit("S-3 requires --output-root")
    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    if args.smoke:
        do_smoke(root)
    elif args.tune:
        do_tune(root)
    elif args.full:
        import json as _j
        if not args.tune_root:
            raise SystemExit("--full requires --tune-root (frozen tune)")
        tune = _j.load(open(Path(args.tune_root) / "s3_tune.json", encoding="utf-8"))
        ov = {"opt-hard-N": args.opt_hard_N, "opt-soft-N": args.opt_soft_N,
              "gap-hard": args.gap_hard, "gap-soft": args.gap_soft, "frac-B": args.frac_B}
        if any(v is not None for v in ov.values()):
            import copy as _copy
            tune = _copy.deepcopy(tune)
            if args.opt_hard_N:
                tune["arms"]["hard"]["opt"]["N"] = args.opt_hard_N
            if args.opt_soft_N:
                tune["arms"]["soft"]["opt"]["N"] = args.opt_soft_N
            if args.gap_hard:
                tune["arms"]["hard"]["opt"]["gap"] = args.gap_hard
            if args.gap_soft:
                tune["arms"]["soft"]["opt"]["gap"] = args.gap_soft
            if args.frac_B:
                tune["levelB"]["frac"] = args.frac_B
            tune["overrides"] = {k: v for k, v in ov.items() if v is not None}
            print(f"full overrides: {tune['overrides']}", flush=True)
        do_full(root, tune)
    else:
        raise SystemExit("S-3 needs one of --smoke/--tune/--full")


if __name__ == "__main__":
    main()
