"""S-4a sign-prior convention diagnostic (S4A_PREEXECUTE.md, DECIDE zero-decode).

On TRUE-marked positions (no decoder): Bob's argmax sign guess agreement,
fine-conditioned sign rates, marked-count/sgn distributions vs synthetic,
and line-by-line G1/reconstruction mapping checks. Pre-written verdict rule:
agreement <<50% -> flipped convention; ~50% -> uninformative; high but
S-3 still failed -> code/accounting.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

SPAN_PS = 204800
BWS = (100, 200, 400)
N_BLK = 4096
RNG_SEED = 20261011

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


def frame_symbols(t: np.ndarray, bw: int, d: int, t0: int):
    rel = np.maximum(t.astype(np.int64) - np.int64(t0), 0)
    bidx = np.floor_divide(rel, np.int64(bw))
    return (np.floor_divide(bidx, np.int64(d)).astype(np.int64),
            np.mod(bidx, np.int64(d)).astype(np.int64))


def boot_ci(x: np.ndarray, rng: np.random.Generator, nrep: int = 50, cap: int = 30000):
    n = len(x)
    if n == 0:
        return [None, None]
    cap = min(n, cap)
    sel = rng.choice(n, size=cap, replace=False)
    xs = x[sel].astype(float)
    reps = [float(rng.choice(xs, size=cap, replace=True).mean()) for _ in range(nrep)]
    m, se = float(np.mean(reps)), float(np.std(reps, ddof=1))
    return [round(m - 1.96 * se, 4), round(m + 1.96 * se, 4)]


def analyze(aa: np.ndarray, bb: np.ndarray, fine_raw: np.ndarray, d: int,
              bw: int, rng: np.random.Generator) -> dict:
    ee = (bb.astype(np.int64) - aa.astype(np.int64)) % int(d)
    e_signed = np.where(ee <= d // 2, ee, ee - d)  # fold to symmetric range
    narrow = np.abs(e_signed) <= 1
    marked = ee != 0
    a0, b0 = (aa % 2).astype(np.uint8), (bb % 2).astype(np.uint8)
    a1, b1 = ((aa >> 1) & 1).astype(np.uint8), ((bb >> 1) & 1).astype(np.uint8)
    sgn = (e_signed == -1).astype(np.uint8)
    out: dict = {"n": int(len(aa)), "n_marked": int(marked.sum()),
                 "marked_rate": round(float(marked.mean()), 5)}
    # G1 + reconstruction closure on the narrow subset
    nm = marked & narrow
    out["narrow_frac"] = round(float(nm.sum() / max(marked.sum(), 1)), 5)
    if int(nm.sum()):
        g1 = (a1[nm] == (b1[nm] ^ a0[nm] ^ sgn[nm])).mean()
        out["G1_hold"] = round(float(g1), 5)
        rec = np.where(sgn[nm] == 1, (bb[nm] + 1) % d, (bb[nm] - 1 + d) % d)
        out["recon_hold"] = round(float((rec == aa[nm]).mean()), 5)
        out["sgn_rate"] = round(float(sgn[nm].mean()), 5)
    else:
        out.update(G1_hold=None, recon_hold=None, sgn_rate=None)
    # argmax-guess agreement (the code's prior direction) + inverted
    if int(marked.sum()):
        guess = (b1[marked] ^ a0[marked] ^ np.uint8(1))
        agree = (guess == a1[marked]).astype(float)
        out["agree_argmax"] = round(float(agree.mean()), 4)
        out["agree_argmax_ci95"] = boot_ci(agree, rng)
        out["agree_inverted"] = round(float(1.0 - agree.mean()), 4)
    else:
        out.update(agree_argmax=None, agree_argmax_ci95=[None, None], agree_inverted=None)
    # fine-conditioned sign curve (8 sub-bins of Bob's intra-bin phase)
    sub = np.minimum(fine_raw.astype(np.int64) // max(bw // 8, 1), 7)
    curve = []
    for s in range(8):
        m = (sub == s) & nm
        curve.append(round(float(sgn[m].mean()), 4) if int(m.sum()) else None)
    out["sgn_by_fine"] = curve
    return out


def self_test() -> None:
    rng = np.random.default_rng(RNG_SEED)
    # synthetic stream with KNOWN convention (sgn=1 w.p. 0.6 on marked)
    n = 100000
    d, bw = 1024, 200
    e = np.zeros(n, dtype=np.int64)
    mk = rng.random(n) < 0.24
    e[mk] = np.where(rng.random(mk.sum()) < 0.6, -1, 1)
    b = rng.integers(0, d, size=n)
    a = (b - e) % d
    fine = rng.integers(0, bw, size=n)
    r = analyze(a, b, fine, d, bw, rng)
    assert r["G1_hold"] == 1.0, r
    assert r["recon_hold"] == 1.0, r
    assert abs(r["agree_argmax"] - 0.6) < 0.02, r
    assert abs(r["agree_inverted"] - 0.4) < 0.02, r
    # flipped-convention stream: diagnostic must fire (agreement <<50%)
    e2 = np.where(e == -1, 1, np.where(e == 1, -1, 0))
    a2 = (b - e2) % d
    r2 = analyze(a2, b, fine, d, bw, rng)
    assert r2["agree_argmax"] < 0.5 - 0.05, r2  # ~0.4: flip detected
    print("s4a self-test OK (G1/recon closure, 0.6/0.4 readout, flip power)")


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
        raise SystemExit("S-4a runs only with --full")
    if not args.output_root:
        raise SystemExit("S-4a --full requires --output-root")
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
    jl = (root / "s4a_rows.jsonl").open("w", encoding="utf-8")
    summary: dict = {"track": "DECIDE-zero-decode", "seed": RNG_SEED, "sources": {}}
    csv_rows = ["source,bw,framing,n,n_marked,marked_rate,narrow_frac,G1_hold,recon_hold,"
                "sgn_rate,agree_argmax,ci_lo,ci_hi,agree_inverted"]
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
        srec: dict = {"source": src, "offset_ps": int(off), "delta_star": dl_star,
                      "n_pairs": int(len(pa)), "cells": {}}
        for bw in BWS:
            d = SPAN_PS // bw
            fa, sa = _frame_global(t_ps=pa, bin_width_ps=bw, frame_bins=d, t0_ps=tmin)
            for tag, shift in (("uncal", 0), ("cal", dl_star)):
                fb, sb = _frame_global(t_ps=(pb + np.int64(shift)), bin_width_ps=bw,
                                       frame_bins=d, t0_ps=tmin)
                keep = (fa >= 0) & (fb >= 0) & (fa == fb)
                fine = ((pb[keep].astype(np.int64) + np.int64(shift)
                         - np.int64(tmin)) % np.int64(bw)).astype(np.int64)
                # rescale fine to 8 sub-bins inside analyze via max trick -> pass bw instead
                r = analyze(sa[keep], sb[keep], fine, d, bw, rng)
                # block-level marked-count distribution (N=4096 chunks, calibrated frame)
                if tag == "cal":
                    ee = (sb[keep].astype(np.int64) - sa[keep].astype(np.int64)) % d
                    mk = (ee != 0).astype(np.int64)
                    nb = len(mk) // N_BLK
                    cnts = np.array([mk[i * N_BLK:(i + 1) * N_BLK].sum() for i in range(nb)])
                    r["blk_marked_mean"] = round(float(cnts.mean()), 1) if nb else None
                    r["blk_marked_q05_med_q95_max"] = [round(float(np.quantile(cnts, q)), 0)
                                                       for q in (0.05, 0.5, 0.95)] + \
                                                      [int(cnts.max())] if nb else None
                r["bw"] = bw
                r["framing"] = tag
                srec["cells"][f"{bw}/{tag}"] = {k: v for k, v in r.items() if k != "sgn_by_fine"}
                srec["cells"][f"{bw}/{tag}"]["sgn_by_fine"] = r["sgn_by_fine"]
                jl.write(json.dumps({"source": src, **r}) + "\n")
                ci = r["agree_argmax_ci95"]
                csv_rows.append(f"{src},{bw},{tag},{r['n']},{r['n_marked']},{r['marked_rate']},"
                                f"{r['narrow_frac']},{r['G1_hold']},{r['recon_hold']},{r['sgn_rate']},"
                                f"{r['agree_argmax']},{ci[0]},{ci[1]},{r['agree_inverted']}")
                print(f"  bw={bw} {tag}: marked={r['n_marked']} sgn={r['sgn_rate']} "
                      f"agree={r['agree_argmax']}{ci} inv={r['agree_inverted']} "
                      f"G1={r['G1_hold']} recon={r['recon_hold']}", flush=True)
        # synthetic对照 (S-2 prefix DoubleGauss, truncated |Δ|<=200 like kept set)
        s2 = json.load(open("workspace/s_softmap/s2_20261009/s2_summary.json", encoding="utf-8"))
        fit = s2["sources"][src]["prefix_fit"]
        rg = np.random.default_rng(RNG_SEED + 7)
        Jn = 200000
        wmask = rg.random(Jn) < fit["w"]
        delta = np.where(wmask, rg.normal(fit["mu"], 100.0, size=Jn),
                         rg.normal(fit["mu"], fit["sig"], size=Jn))
        delta = delta[np.abs(delta) <= 200.0]
        vs = rg.uniform(0, 200, size=len(delta))
        es = -np.floor((vs - delta) / 200).astype(np.int64)
        aa0 = (-es) % 1024
        bb0 = np.zeros(len(es), dtype=np.int64)
        rs = analyze(aa0, bb0, vs.astype(np.int64), 1024, 200, rg)
        srec["synthetic"] = {k: rs[k] for k in ("n_marked", "marked_rate", "sgn_rate",
                                                "agree_argmax", "G1_hold", "recon_hold")}
        print(f"  synth: marked_rate={rs['marked_rate']} sgn={rs['sgn_rate']} "
              f"agree={rs['agree_argmax']} G1={rs['G1_hold']}", flush=True)
        srec["wall_s"] = round(time.perf_counter() - t0, 1)
        summary["sources"][src] = srec
        jl.flush()
        del pa, pb
    jl.close()
    (root / "s4a_table.csv").write_text("\n".join(csv_rows) + "\n", encoding="utf-8")
    summary["wall_s_total"] = round(time.perf_counter() - t_all, 1)
    (root / "s4a_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(f"S-4a done wall={summary['wall_s_total']}s -> {root}")


if __name__ == "__main__":
    main()
