"""S-2 {uncal,cal}x{hard,soft} H(A|B) table (S2_PREEXECUTE.md, DECIDE zero-decode).

Frozen chain (Z-2/M5/C-0/B123) + prefix(10k pairs)/test split per segment.
Prefix fits (mu, sig, w) ONLY; test part carries the four empirical H's +
prefix-model reference + bootstrap CIs. No decoding.

AGENTS.md 5.7: plain functions, numpy only.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_b123_stats import (
    frame_symbols,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_a5_soft_rate import (
    hard_rate,
    soft_rate,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_a3_jitter_model import (
    DoubleGauss,
)

SPAN_PS = 204800
BWS = (100, 200, 400)
N_PREFIX = 10000
RNG_SEED = 20261010
WIDE_SIG2 = 100.0

FILES = {
    "T2-1M": ("D:/Data/Raw Data/2026.1.21/Type2_1M_3s_2026-01-21_184040/Type2_1M_3s_2026-01-21_184040.ttbin", -50),
    "T2-1.5M": ("D:/Data/Raw Data/2026.1.21/Type2_1-5M_3s_2026-01-21_183806/Type2_1-5M_3s_2026-01-21_183806.ttbin", +50),
    "T2-2M": ("D:/Data/Raw Data/2026.1.21/Type2_2M_3s_2026-01-21_183657/Type2_2M_3s_2026-01-21_183657.ttbin", +50),
    "T0-500K": ("D:/Data/Raw Data/2026.1.20/Type0_nofilter_500K_3s_2026-01-20_193050/Type0_nofilter_500K_3s_2026-01-20_193050.ttbin", -50),
    "T0-1M": ("D:/Data/Raw Data/2026.1.20/Type0_nofilter_1M_3s_2026-01-20_192857/Type0_nofilter_1M_3s_2026-01-20_192857.ttbin", -50),
    "0dB": ("D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_0dB_2026-01-23_174534.1.ttbin", -50),
    "4dB": ("D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_4dB_2026-01-23_174758.1.ttbin", -50),
    "10dB": ("D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_10dB_2026-01-23_174842.1.ttbin", -45),
}


def H_plugin(codes: np.ndarray) -> float:  # noqa: N802
    _, cnts = np.unique(codes, return_counts=True)
    p = cnts / len(codes)
    return float(-(p * np.log2(np.maximum(p, 1e-300))).sum())


def prefix_fit(delta: np.ndarray) -> dict:
    mu = float(np.median(delta))
    mad = float(np.median(np.abs(delta - mu)))
    sig = float(1.4826 * mad)
    w = float(np.mean(np.abs(delta) > 100.0))
    return {"mu": round(mu, 2), "sig": round(sig, 2), "w": round(w, 5)}


def four_H(pa_t, pb_t, tmin: int, bw: int, dl_star: int):  # noqa: N802
    """Empirical (H_hard_uncal, H_hard_cal, H_soft_uncal, H_soft_cal) on test."""
    d = SPAN_PS // bw
    fa, sa = frame_symbols(pa_t, bw, d, tmin)
    fb0, sb0 = frame_symbols(pb_t, bw, d, tmin)
    fb1, sb1 = frame_symbols(pb_t + np.int64(dl_star), bw, d, tmin)
    k0 = (fa >= 0) & (fb0 >= 0) & (fa == fb0)
    k1 = (fa >= 0) & (fb1 >= 0) & (fa == fb1)
    out = {}
    for tag, aa, bb, keep in (("uncal", sa, sb0, k0), ("cal", sa, sb1, k1)):
        ee = (bb[keep].astype(np.int64) - aa[keep].astype(np.int64)) % d
        n = int(len(ee))
        Hh = H_plugin(ee)
        fine = ((pb_t[keep].astype(np.int64) + (np.int64(dl_star) if tag == "cal" else np.int64(0))
                 - np.int64(tmin)) % np.int64(bw))
        sub = np.minimum(fine // max(bw // 8, 1), 7)
        Hs, wsum = 0.0, 0
        for s in range(8):
            m = sub == s
            ns = int(m.sum())
            if ns:
                Hs += ns * H_plugin(ee[m])
                wsum += ns
        out[f"H_hard_{tag}"] = round(Hh, 4)
        out[f"H_soft_{tag}"] = round(Hs / wsum, 4) if wsum else None
        out[f"n_{tag}"] = n
    return out


def boot_cis(pa_t, pb_t, tmin: int, bw: int, dl_star: int,
             rng: np.random.Generator) -> dict:
    """Bootstrap 95% CIs for the four H's (seeded subsample, bounded)."""
    d = SPAN_PS // bw
    fa, sa = frame_symbols(pa_t, bw, d, tmin)
    fb0, sb0 = frame_symbols(pb_t, bw, d, tmin)
    fb1, sb1 = frame_symbols(pb_t + np.int64(dl_star), bw, d, tmin)
    k0 = (fa >= 0) & (fb0 >= 0) & (fa == fb0)
    k1 = (fa >= 0) & (fb1 >= 0) & (fa == fb1)
    res = {}
    arms = {"uncal": (sa[k0], sb0[k0], pb_t[k0], 0),
            "cal": (sa[k1], sb1[k1], pb_t[k1], dl_star)}
    for tag, (aa, bb, pbt, dl) in arms.items():
        n = len(aa)
        if n == 0:
            res[tag] = None
            continue
        ee = (bb.astype(np.int64) - aa.astype(np.int64)) % d
        fine = ((pbt.astype(np.int64) + np.int64(dl) - np.int64(tmin)) % np.int64(bw))
        sub = np.minimum(fine // max(bw // 8, 1), 7)
        cap = min(n, 30000)
        sel = rng.choice(n, size=cap, replace=False)
        ee_s, sub_s = ee[sel], sub[sel]
        rh = []
        rs = []
        for _ in range(50):
            bi = rng.integers(0, cap, size=cap)
            e_b, s_b = ee_s[bi], sub_s[bi]
            rh.append(H_plugin(e_b))
            h = 0.0
            for s in range(8):
                m = s_b == s
                if int(m.sum()):
                    h += int(m.sum()) * H_plugin(e_b[m])
            rs.append(h / cap)
        for key, arr in (("H_hard", rh), ("H_soft", rs)):
            m_, se = float(np.mean(arr)), float(np.std(arr, ddof=1))
            res[f"{key}_{tag}_ci95"] = [round(m_ - 1.96 * se, 4), round(m_ + 1.96 * se, 4)]
    return res


def self_test() -> None:
    rng = np.random.default_rng(RNG_SEED)
    # synthetic ternary-error stream with known (mu, sig, w)
    n = 60000
    v = rng.uniform(0, 200, size=n)
    wide = rng.random(n) < 0.02
    j = np.where(wide, rng.normal(0, 100, size=n), rng.normal(47.0, 18.0, size=n))
    delta = j  # paired residual convention
    fit = prefix_fit(delta[:N_PREFIX])
    assert abs(fit["mu"] - 47.0) < 3.0, fit
    assert abs(fit["sig"] - 18.0) < 4.0, fit
    assert abs(fit["w"] - 0.02) < 0.015, fit
    # framing-level ordering checks on a synthetic framed pair
    bw, d, tmin = 200, SPAN_PS // 200, 0
    pa = np.arange(n, dtype=np.int64) * 200
    pb = pa - delta.astype(np.int64)
    fh = four_H(pa[N_PREFIX:], pb[N_PREFIX:], tmin, bw, -50)
    assert fh["H_soft_uncal"] <= fh["H_hard_uncal"] + 1e-9, fh
    assert fh["H_hard_cal"] <= fh["H_hard_uncal"] + 1e-9, fh
    ci = boot_cis(pa[N_PREFIX:N_PREFIX + 5000], pb[N_PREFIX:N_PREFIX + 5000],
                  tmin, bw, -50, rng)
    assert ci["H_hard_uncal_ci95"][0] <= ci["H_hard_uncal_ci95"][1]
    print("s2 self-test OK (prefix recovery / ordering / bootstrap)")


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
        raise SystemExit("S-2 runs only with --full")
    if not args.output_root:
        raise SystemExit("S-2 --full requires --output-root")
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
        _pair_nearest_unique,
        read_ttbin_events,
    )

    rng = np.random.default_rng(RNG_SEED)
    jl = (root / "s2_rows.jsonl").open("w", encoding="utf-8")
    summary: dict = {"track": "DECIDE-zero-decode", "seed": RNG_SEED,
                     "n_prefix": N_PREFIX, "sources": {}}
    csv_rows = ["source,bw,n_test,H_hard_uncal,H_hard_cal,H_soft_uncal,H_soft_cal,"
                "pred_hard_uncal,pred_soft_uncal,pred_hard_cal,pred_soft_cal,"
                "mu_pre,sig_pre,w_pre"]
    t_all = time.perf_counter()
    for src, (path, dl_star) in FILES.items():
        t0 = time.perf_counter()
        events = read_ttbin_events(path)
        t = np.asarray(events.time_ps, dtype=np.int64)
        valid = (np.asarray(events.event_type, dtype=np.int64) == 0) \
            if events.event_type is not None else np.ones(t.shape, dtype=bool)
        ch = np.asarray(events.channel, dtype=np.int64)
        t_a, t_b = t[valid & (ch == _m0.CH_A)], t[valid & (ch == _m0.CH_B)]
        tmin = int(t.min())
        al = aw.derive_alignment(events=events, ch_a=_m0.CH_A, ch_b=_m0.CH_B)
        status = al.get("align_status")
        off = al.get("offset_ps_derived")
        print(f"{src} align={status} off={off}", flush=True)
        if status != "ok":
            row = {"source": src, "blocked": status}
            jl.write(json.dumps(row) + "\n")
            jl.flush()
            summary["sources"][src] = row
            continue
        pa, pb = _pair_nearest_unique(t_a=t_a, t_b=t_b,
                                      window_ps=_m0.COIN_WINDOW_PS,
                                      offset_ps=int(off))
        del t_a, t_b, events
        # time-ordered prefix/test split (pa non-decreasing from pairing)
        idx = np.argsort(pa, kind="stable")
        pre, tst = idx[:N_PREFIX], idx[N_PREFIX:]
        fit = prefix_fit((pa[pre].astype(np.int64) - pb[pre].astype(np.int64)))
        law = DoubleGauss(fit["sig"], WIDE_SIG2, fit["w"])
        mu_cal = fit["mu"] - dl_star  # Δ_cal = Δ − δ*  → mean μ̂−δ*
        srec: dict = {"source": src, "offset_ps": int(off),
                      "delta_star": dl_star, "n_pairs": int(len(pa)),
                      "n_prefix": int(len(pre)), "n_test": int(len(tst)),
                      "prefix_fit": fit, "cells": {}}
        pa_t, pb_t = pa[tst], pb[tst]
        for bw in BWS:
            fh = four_H(pa_t, pb_t, tmin, bw, dl_star)
            ci = boot_cis(pa_t, pb_t, tmin, bw, dl_star, rng)
            href = hard_rate(law, bw, fit["mu"])
            sref = soft_rate(law, bw, fit["mu"])
            href_c = hard_rate(law, bw, mu_cal)
            sref_c = soft_rate(law, bw, mu_cal)
            cell = {**fh, **ci,
                    "pred_hard_uncal": round(href["H_hard"], 4),
                    "pred_soft_uncal": round(sref["H_soft"], 4),
                    "pred_hard_cal": round(href_c["H_hard"], 4),
                    "pred_soft_cal": round(sref_c["H_soft"], 4)}
            srec["cells"][str(bw)] = cell
            jl.write(json.dumps({"source": src, "bw": bw, **cell}) + "\n")
            csv_rows.append(
                f"{src},{bw},{fh['n_uncal']},{fh['H_hard_uncal']},{fh['H_hard_cal']},"
                f"{fh['H_soft_uncal']},{fh['H_soft_cal']},{cell['pred_hard_uncal']},"
                f"{cell['pred_soft_uncal']},{cell['pred_hard_cal']},{cell['pred_soft_cal']},"
                f"{fit['mu']},{fit['sig']},{fit['w']}")
            print(f"  bw={bw} test_n={fh['n_uncal']} "
                  f"Hh={fh['H_hard_uncal']}/{fh['H_hard_cal']} "
                  f"Hs={fh['H_soft_uncal']}/{fh['H_soft_cal']}", flush=True)
        srec["wall_s"] = round(time.perf_counter() - t0, 1)
        summary["sources"][src] = srec
        jl.flush()
        del pa, pb
    jl.close()
    (root / "s2_table.csv").write_text("\n".join(csv_rows) + "\n", encoding="utf-8")
    summary["wall_s_total"] = round(time.perf_counter() - t_all, 1)
    (root / "s2_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(f"S-2 done wall={summary['wall_s_total']}s -> {root}")


if __name__ == "__main__":
    main()
