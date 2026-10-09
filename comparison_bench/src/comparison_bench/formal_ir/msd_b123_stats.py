"""B1-B3 zero-decode raw-data statistics (B123_PREEXECUTE.md, DECIDE).

Frozen chain (same as Z-2/M5/C-0): base/.1-variant read + derive_alignment
gate + _pair_nearest_unique (window 200 ps, nominal offset) + _frame_global
(span 204800 ps). Statistics only: no decoding, no key, no acquisition.

B1: ps-resolution Delta histogram + Gaussian / Gaussian+uniform /
    double-Gaussian fits + 3-subsegment mu drift.
B2: H(A|B bin) vs H(A|B fine time) at bw {100,200,400}, bootstrap SE.
B3: Type-0 (2026-01-20, 4 segs) vs Type-II (2026-01-21, 3 segs): coarse
    delta scan for T0 new sources, C-0 delta* verification for T2,
    calibrated p / support / CAR estimate / H decomposition.

AGENTS.md section 5.7: plain functions, numpy only, no heavy deps.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

SPAN_PS = 204800
COIN_W = 200
B2_BWS = (100, 200, 400)
CAL_BW = 200
# C-0 frozen optima (C0_RESULT.md section 1, bw200): additional shift dB ps.
C0_DELTA_STAR = {"T2-1M": -50, "T2-1.5M": +50, "T2-2M": +50}
T0_COARSE_DELTAS = (-100, -75, -50, -25, 0, 25, 50, 75, 100)

FILES = {
    # label: (path, variant-note, b3-group or None)
    "T2-1M": ("D:/Data/Raw Data/2026.1.21/Type2_1M_3s_2026-01-21_184040/Type2_1M_3s_2026-01-21_184040.ttbin", "base", "T2"),
    "T2-1.5M": ("D:/Data/Raw Data/2026.1.21/Type2_1-5M_3s_2026-01-21_183806/Type2_1-5M_3s_2026-01-21_183806.ttbin", "base", "T2"),
    "T2-2M": ("D:/Data/Raw Data/2026.1.21/Type2_2M_3s_2026-01-21_183657/Type2_2M_3s_2026-01-21_183657.ttbin", "base", "T2"),
    "T0-500K": ("D:/Data/Raw Data/2026.1.20/Type0_nofilter_500K_3s_2026-01-20_193050/Type0_nofilter_500K_3s_2026-01-20_193050.ttbin", "base", "T0"),
    "T0-1M": ("D:/Data/Raw Data/2026.1.20/Type0_nofilter_1M_3s_2026-01-20_192857/Type0_nofilter_1M_3s_2026-01-20_192857.ttbin", "base", "T0"),
    "T0-1.5M": ("D:/Data/Raw Data/2026.1.20/Type0_nofilter_1_5M_3s_2026-01-20_193255/Type0_nofilter_1_5M_3s_2026-01-20_193255.ttbin", "base", "T0"),
    "T0-2M": ("D:/Data/Raw Data/2026.1.20/Type0_nofilter_2M_3s_2026-01-20_193411/Type0_nofilter_2M_3s_2026-01-20_193411.ttbin", "base", "T0"),
    "0dB": ("D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_0dB_2026-01-23_174534.1.ttbin", ".1", None),
    "4dB": ("D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_4dB_2026-01-23_174758.1.ttbin", ".1", None),
    "10dB": ("D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_10dB_2026-01-23_174842.1.ttbin", ".1", None),
}

RNG_SEED = 20261009


def h2(x: float) -> float:
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -(x * math.log2(x) + (1.0 - x) * math.log2(1.0 - x))


def phi(z: float) -> float:
    return math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)


def Phi(z: float) -> float:  # noqa: N802
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def err_stats(aa: np.ndarray, bb: np.ndarray, d: int) -> dict:
    n = int(len(aa))
    if n == 0:
        return {"n": 0, "p": None, "p_minus_cond": None,
                "support_size": 0, "top_errors": [], "H_e": None,
                "decomp": None}
    ee = (bb.astype(np.int64) - aa.astype(np.int64)) % int(d)
    vals, cnts = np.unique(ee, return_counts=True)
    probs = cnts / n
    he = float(-(probs * np.log2(np.maximum(probs, 1e-300))).sum())
    n0 = int(cnts[vals.tolist().index(0)]) if 0 in vals else 0
    p = float(1.0 - n0 / n)
    neg = int(d - 1)
    n_neg = int(cnts[vals.tolist().index(neg)]) if neg in vals else 0
    pm = float(n_neg / (n - n0)) if (n - n0) else float("nan")
    decomp = h2(p) + (p * h2(pm) if pm == pm and 0.0 < pm < 1.0 else 0.0)
    top = sorted(((int(v), round(float(c / n), 6)) for v, c in zip(vals, cnts)),
                 key=lambda kv: -kv[1])
    return {"n": n, "p": round(p, 6),
            "p_minus_cond": round(pm, 6) if pm == pm else None,
            "support_size": int(len(vals)), "top_errors": top,
            "H_e": round(he, 4), "decomp": round(decomp, 4)}


def frame_symbols(t: np.ndarray, bw: int, d: int, t0: int):
    rel = np.maximum(t.astype(np.int64) - np.int64(t0), 0)
    bidx = np.floor_divide(rel, np.int64(bw))
    return (np.floor_divide(bidx, np.int64(d)).astype(np.int64),
            np.mod(bidx, np.int64(d)).astype(np.int64))


def gauss_hist_ll(counts: np.ndarray, edges: np.ndarray,
                  mu: float, sig: float) -> float:
    """Poisson log-likelihood of a truncated Gaussian on the hist grid."""
    lo = (edges[:-1] - mu) / sig
    hi = (edges[1:] - mu) / sig
    norm = Phi((edges[-1] - mu) / sig) - Phi((edges[0] - mu) / sig)
    if norm <= 0:
        return float("-inf")
    probs = np.array([Phi(h) - Phi(lo_i) for lo_i, h in zip(lo, hi)]) / norm
    probs = np.maximum(probs, 1e-300)
    tot = float(counts.sum())
    if tot <= 0:
        return float("-inf")
    return float((counts * np.log(probs)).sum())


def fit_delta(delta: np.ndarray) -> dict:
    """Fit Gaussian / Gaussian+uniform / double-Gaussian on 5 ps grid."""
    edges = np.arange(-500, 505, 5, dtype=np.float64)
    counts, _ = np.histogram(delta.astype(np.float64), bins=edges)
    n = int(counts.sum())
    mu0 = float(np.mean(delta)) if n else 0.0
    sd0 = float(np.std(delta)) if n else 1.0
    # (a) plain Gaussian: moment fit on the +/-200 window (truncation
    # negligible at sig~25ps << 200ps; stated explicitly).
    g = {"mu": round(mu0, 2), "sigma": round(sd0, 2),
         "ll": round(gauss_hist_ll(counts, edges, mu0, max(sd0, 1e-6)), 1)}
    # tail masses (data vs plain-Gaussian prediction)
    tail_obs = float(((np.abs(delta) > 100)).sum() / n) if n else float("nan")
    z1, z2 = (100 - mu0) / max(sd0, 1e-9), (-100 - mu0) / max(sd0, 1e-9)
    tail_pred = float((1.0 - Phi(z1)) + Phi(z2))
    # (b) Gaussian + uniform over [-200,200]: 1-D golden search on eps.
    sig = max(sd0, 1e-6)
    lo_e = (edges[:-1] - mu0) / sig
    hi_e = (edges[1:] - mu0) / sig
    norm = Phi((edges[-1] - mu0) / sig) - Phi((edges[0] - mu0) / sig)
    pg = np.array([Phi(h) - Phi(lo_i) for lo_i, h in zip(lo_e, hi_e)]) / norm
    inwin = (edges[:-1] >= -200) & (edges[1:] <= 200)
    pu = np.where(inwin, 5.0 / 400.0, 0.0)
    pu = pu / max(pu.sum(), 1e-300)
    pg = np.maximum(pg, 1e-300)

    def ll_eps(eps: float) -> float:
        mix = (1.0 - eps) * pg + eps * pu
        return float((counts * np.log(np.maximum(mix, 1e-300))).sum())

    a, b = 0.0, 0.20
    gr = (math.sqrt(5.0) - 1.0) / 2.0
    c, d_ = b - gr * (b - a), a + gr * (b - a)
    for _ in range(40):
        if ll_eps(c) < ll_eps(d_):
            a = c
            c = d_
            d_ = a + gr * (b - a)
        else:
            b = d_
            d_ = c
            c = b - gr * (b - a)
    eps_hat = round((a + b) / 2.0, 5)
    gu = {"eps_uniform": eps_hat, "ll": round(ll_eps(eps_hat), 1)}
    # (c) double Gaussian: narrow fixed at (mu0, sd0), wide grid.
    best = {"w": 0.0, "sigma2": None, "ll": g["ll"]}
    for s2 in (50.0, 100.0, 200.0, 400.0):
        lo2 = (edges[:-1] - mu0) / s2
        hi2 = (edges[1:] - mu0) / s2
        norm2 = Phi((edges[-1] - mu0) / s2) - Phi((edges[0] - mu0) / s2)
        p2 = np.array([Phi(h) - Phi(lo_i) for lo_i, h in zip(lo2, hi2)]) / norm2
        p2 = np.maximum(p2, 1e-300)
        aa, bb = 0.0, 0.10
        for _ in range(30):
            m1 = aa + (bb - aa) / 3.0
            m2 = bb - (bb - aa) / 3.0

            def llw(w: float) -> float:
                return float((counts * np.log(np.maximum((1 - w) * pg + w * p2, 1e-300))).sum())

            if llw(m1) < llw(m2):
                aa = m1
            else:
                bb = m2
        w_hat = (aa + bb) / 2.0

        def llw2(w: float) -> float:
            return float((counts * np.log(np.maximum((1 - w) * pg + w * p2, 1e-300))).sum())

        llv = llw2(w_hat)
        if llv > best["ll"]:
            best = {"w": round(float(w_hat), 5), "sigma2": s2,
                    "ll": round(float(llv), 1)}
    # sub-segment drift is computed by the caller (drift_thirds, time order).
    return {"n": n, "mean": round(mu0, 2), "sd": round(sd0, 2),
            "median": round(float(np.median(delta)) if n else 0.0, 2),
            "q01": round(float(np.quantile(delta, 0.01)) if n else 0.0, 1),
            "q99": round(float(np.quantile(delta, 0.99)) if n else 0.0, 1),
            "tail_gt100_obs": round(tail_obs, 6) if tail_obs == tail_obs else None,
            "tail_gt100_gauss_pred": round(tail_pred, 6),
            "gauss": g, "gauss_uniform": gu, "double_gauss": best}


def drift_thirds(pa: np.ndarray, delta: np.ndarray) -> dict:
    """Split pairs into time thirds (pa is non-decreasing from pairing)."""
    n = len(pa)
    if n < 30:
        return {"mu thirds": [], "drift": None, "note": "n<30"}
    idx = np.argsort(pa, kind="stable")
    thirds = np.array_split(idx, 3)
    mus, ses = [], []
    for th in thirds:
        seg = delta[th]
        mus.append(round(float(np.mean(seg)), 2))
        ses.append(round(float(np.std(seg) / math.sqrt(len(seg))), 2))
    return {"mu_thirds": mus, "mu_se": ses,
            "drift": round(float(max(mus) - min(mus)), 2)}


def soft_gain(pa: np.ndarray, pb: np.ndarray, tmin: int, bw: int,
              rng: np.random.Generator) -> dict:
    d = SPAN_PS // bw
    fa, sa = frame_symbols(pa, bw, d, tmin)
    fb, sb = frame_symbols(pb, bw, d, tmin)
    keep = (fa >= 0) & (fb >= 0) & (fa == fb)
    aa, bb = sa[keep].astype(np.int64), sb[keep].astype(np.int64)
    fine = ((pb[keep].astype(np.int64) - np.int64(tmin)) % np.int64(bw)).astype(np.int64)
    n = int(len(aa))
    if n == 0:
        return {"bw": bw, "n": 0, "H_bin": None, "H_fine": None,
                "gain": None, "gain_se": None, "rel": None}
    ee = (bb - aa) % d
    vals, cnts = np.unique(ee, return_counts=True)
    Hb = float(-((cnts / n) * np.log2(np.maximum(cnts / n, 1e-300))).sum())
    sub = np.minimum(fine // max(bw // 8, 1), 7)
    Hf, tab = 0.0, []
    for s in range(8):
        m = sub == s
        ns = int(m.sum())
        if ns == 0:
            tab.append({"s": s, "n": 0, "H": None})
            continue
        v2, c2 = np.unique(ee[m], return_counts=True)
        Hs = float(-((c2 / ns) * np.log2(np.maximum(c2 / ns, 1e-300))).sum())
        Hf += (ns / n) * Hs
        tab.append({"s": s, "n": ns, "H": round(Hs, 4)})
    gain = float(Hb - Hf)
    # bootstrap SE on a seeded subsample (bounded cost)
    cap = min(n, 50000)
    sel = rng.choice(n, size=cap, replace=False)
    ee_s, sub_s = ee[sel], sub[sel]
    reps = []
    for _ in range(50):
        bi = rng.integers(0, cap, size=cap)
        e_b, s_b = ee_s[bi], sub_s[bi]
        v_b, c_b = np.unique(e_b, return_counts=True)
        Hb_b = float(-((c_b / cap) * np.log2(np.maximum(c_b / cap, 1e-300))).sum())
        Hf_b = 0.0
        for s in range(8):
            m = s_b == s
            ns = int(m.sum())
            if ns == 0:
                continue
            v2, c2 = np.unique(e_b[m], return_counts=True)
            Hf_b += (ns / cap) * float(-((c2 / ns) * np.log2(np.maximum(c2 / ns, 1e-300))).sum())
        reps.append(Hb_b - Hf_b)
    se = float(np.std(reps, ddof=1)) if len(reps) > 1 else 0.0
    return {"bw": bw, "n": n, "H_bin": round(Hb, 4), "H_fine": round(Hf, 4),
            "gain": round(gain, 4), "gain_se": round(se, 4),
            "gain_ci95": [round(gain - 1.96 * se, 4), round(gain + 1.96 * se, 4)],
            "rel_to_Hbin": round(gain / Hb, 4) if Hb > 0 else None,
            "subsample": cap, "reps": 50, "sub_table": tab}


def self_test() -> None:
    rng = np.random.default_rng(RNG_SEED)
    # tiny exact checks, no real data
    aa = np.array([0, 0, 0, 1, 5], dtype=np.int64)
    bb = np.array([0, 1, 1023, 1, 5], dtype=np.int64)
    r = err_stats(aa, bb, 1024)
    assert r["n"] == 5 and r["support_size"] == 3, r
    assert r["p"] == round(2 / 5, 6), r
    dl = np.array([-30, -10, 0, 10, 30] * 200, dtype=np.int64)
    f = fit_delta(dl)
    assert abs(f["mean"]) < 1.0 and 15 < f["sd"] < 25, f
    pa = np.arange(1000, dtype=np.int64) * 200
    pb = pa + rng.integers(-30, 31, size=1000)
    g = soft_gain(pa, pb, 0, 200, rng)
    assert g["n"] == 1000 and g["gain"] is not None and g["gain"] >= -1e-9, g
    fa, sa = frame_symbols(np.array([0, 199, 200, 400]), 200, 1024, 0)
    assert sa.tolist() == [0, 0, 1, 2], sa.tolist()
    print("b123 self-test OK")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=False, default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.full:
        raise SystemExit("B123 runs only with --full")
    if not args.output_root:
        raise SystemExit("B123 --full requires --output-root")
    from comparison_bench.src.comparison_bench.io import align_wrapper as aw
    from comparison_bench.src.comparison_bench.io.ttbin_compat import (
        install_timetagger_alias,
    )
    from comparison_bench.src.comparison_bench.cli.probes_closed import (  # noqa: E402
        m0_realframe_runner as _m0,
    )

    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    install_timetagger_alias()
    from src.qkd_io.ttbin_pipeline import (  # noqa: E402
        _frame_global,
        _pair_nearest_unique,
        read_ttbin_events,
    )

    rng = np.random.default_rng(RNG_SEED)
    jl = (root / "b123_rows.jsonl").open("w", encoding="utf-8")
    summary: dict = {"track": "DECIDE-zero-decode", "seed": RNG_SEED,
                     "files": {}, "b1": {}, "b2": {}, "b3": {}}
    hist_rows = ["source,center_ps,count"]
    soft_rows = ["source,bw,n,H_bin,H_fine,gain,se,ci_lo,ci_hi,rel"]
    t_all = time.perf_counter()
    for src, (path, variant, grp) in FILES.items():
        t0 = time.perf_counter()
        events = read_ttbin_events(path)
        t = np.asarray(events.time_ps, dtype=np.int64)
        valid = (np.asarray(events.event_type, dtype=np.int64) == 0) \
            if events.event_type is not None else np.ones(t.shape, dtype=bool)
        ch = np.asarray(events.channel, dtype=np.int64)
        nA = int((valid & (ch == _m0.CH_A)).sum())
        nB = int((valid & (ch == _m0.CH_B)).sum())
        tmin, tmax = int(t.min()), int(t.max())
        Tacq = max((tmax - tmin) * 1e-12, 1e-12)
        SA, SB = nA / Tacq, nB / Tacq
        al = aw.derive_alignment(events=events, ch_a=_m0.CH_A, ch_b=_m0.CH_B)
        status = al.get("align_status")
        off = al.get("offset_ps_derived")
        frec = {"path": path, "variant": variant, "group": grp,
                "n_events": int(valid.sum()), "singles_A": nA,
                "singles_B": nB, "Tacq_s": round(Tacq, 3),
                "S_A_per_s": round(SA, 1), "S_B_per_s": round(SB, 1),
                "align_status": status, "offset_ps": off,
                "peak_center_ps": al.get("peak_center_ps")}
        summary["files"][src] = frec
        print(f"{src} events={valid.sum()} A={nA} B={nB} "
              f"T={Tacq:.2f}s align={status} off={off}", flush=True)
        if status != "ok":
            row = {"source": src, "blocked": status}
            jl.write(json.dumps(row) + "\n")
            jl.flush()
            summary["b1"][src] = row
            continue
        t_a = t[valid & (ch == _m0.CH_A)]
        t_b = t[valid & (ch == _m0.CH_B)]
        del events
        pa, pb = _pair_nearest_unique(t_a=t_a, t_b=t_b,
                                      window_ps=_m0.COIN_WINDOW_PS,
                                      offset_ps=int(off))
        del t_a, t_b
        n_pairs = int(len(pa))
        Rc = n_pairs / Tacq
        Racc = SA * SB * (COIN_W * 1e-12)
        frec.update({"n_pairs": n_pairs, "R_coin_per_s": round(Rc, 1),
                     "R_acc_per_s": round(Racc, 3),
                     "CAR_est": round(Rc / Racc, 1) if Racc > 0 else None})
        # ---- B1 ----
        delta = (pa.astype(np.int64) - pb.astype(np.int64))
        fit = fit_delta(delta)
        dr = drift_thirds(pa, delta)
        b1 = {"source": src, "n_pairs": n_pairs, "offset_ps": int(off),
              "fit": fit, "drift": dr,
              "wall_s": round(time.perf_counter() - t0, 1)}
        summary["b1"][src] = b1
        jl.write(json.dumps({"task": "B1", **b1}) + "\n")
        edges = np.arange(-500, 505, 5, dtype=np.float64)
        cc, _ = np.histogram(delta.astype(np.float64), bins=edges)
        ctr = (edges[:-1] + edges[1:]) / 2.0
        for c_, k_ in zip(ctr, cc):
            hist_rows.append(f"{src},{c_:.0f},{int(k_)}")
        # ---- B2 ----
        b2src = {}
        for bw in B2_BWS:
            g = soft_gain(pa, pb, tmin, bw, rng)
            b2src[str(bw)] = g
            jl.write(json.dumps({"task": "B2", "source": src, **g}) + "\n")
            soft_rows.append(f"{src},{bw},{g['n']},{g['H_bin']},{g['H_fine']},"
                             f"{g['gain']},{g['gain_se']},"
                             f"{(g['gain_ci95'][0] if g['gain_ci95'] else '')},"
                             f"{(g['gain_ci95'][1] if g['gain_ci95'] else '')},"
                             f"{g['rel_to_Hbin']}")
            print(f"  B2 bw={bw} n={g['n']} Hb={g['H_bin']} Hf={g['H_fine']} "
                  f"G={g['gain']} se={g['gain_se']}", flush=True)
        summary["b2"][src] = b2src
        # ---- B3 (only T0/T2 groups) ----
        if grp in ("T0", "T2"):
            bw = CAL_BW
            d = SPAN_PS // bw
            fa, sa = _frame_global(t_ps=pa, bin_width_ps=bw,
                                   frame_bins=d, t0_ps=tmin)
            if grp == "T2":
                dl_star = int(C0_DELTA_STAR[src])
                fb, sb = _frame_global(t_ps=(pb + np.int64(dl_star)),
                                       bin_width_ps=bw, frame_bins=d,
                                       t0_ps=tmin)
                keep = (fa >= 0) & (fb >= 0) & (fa == fb)
                # nominal (uncalibrated) at delta=0
                fb0, sb0 = _frame_global(t_ps=pb, bin_width_ps=bw,
                                         frame_bins=d, t0_ps=tmin)
                keep0 = (fa >= 0) & (fb0 >= 0) & (fa == fb0)
                nom = err_stats(sa[keep0], sb0[keep0], d)
                cal = err_stats(sa[keep], sb[keep], d)
                scan = [{"delta": dl_star, "p": cal["p"], "note": "C-0 frozen optimum"}]
            else:
                fb0, sb0 = _frame_global(t_ps=pb, bin_width_ps=bw,
                                         frame_bins=d, t0_ps=tmin)
                keep0 = (fa >= 0) & (fb0 >= 0) & (fa == fb0)
                nom = err_stats(sa[keep0], sb0[keep0], d)
                scan = []
                best = None
                for dl in T0_COARSE_DELTAS:
                    fbx, sbx = _frame_global(t_ps=(pb + np.int64(dl)),
                                             bin_width_ps=bw, frame_bins=d,
                                             t0_ps=tmin)
                    kpx = (fa >= 0) & (fbx >= 0) & (fa == fbx)
                    stx = err_stats(sa[kpx], sbx[kpx], d)
                    scan.append({"delta": dl, "p": stx["p"],
                                 "support": stx["support_size"], "n": stx["n"]})
                    if best is None or (stx["p"] is not None and stx["p"] < best[1]):
                        best = (dl, stx["p"], stx)
                dl_star = int(best[0])
                cal = {k: best[2][k] for k in ("n", "p", "p_minus_cond",
                                               "support_size", "top_errors",
                                               "H_e", "decomp")}
            b3 = {"source": src, "group": grp, "bw": bw, "d": d,
                  "delta_star": dl_star, "nominal": nom, "calibrated": cal,
                  "scan": scan, "CAR_est": frec["CAR_est"],
                  "R_coin": frec["R_coin_per_s"], "R_acc": frec["R_acc_per_s"],
                  "wall_s": round(time.perf_counter() - t0, 1)}
            summary["b3"][src] = b3
            jl.write(json.dumps({"task": "B3", **b3}) + "\n")
            print(f"  B3 {src}: nom p={nom['p']} -> cal p={cal['p']} "
                  f"@ {dl_star}ps sup={cal['support_size']} "
                  f"CAR~{frec['CAR_est']}", flush=True)
        jl.flush()
        del pa, pb
    jl.close()
    (root / "b123_delta_hist.csv").write_text("\n".join(hist_rows) + "\n", encoding="utf-8")
    (root / "b123_soft.csv").write_text("\n".join(soft_rows) + "\n", encoding="utf-8")
    summary["wall_s_total"] = round(time.perf_counter() - t_all, 1)
    (root / "b123_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(f"B123 done wall={summary['wall_s_total']}s -> {root}")


if __name__ == "__main__":
    main()
