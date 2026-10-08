"""M5 prefix-only delta estimation (C_BATCH_AMEND; DECIDE zero-decode).

Same frozen chain as C-0 (derive_alignment gate + _pair_nearest_unique
window 200ps + _frame_global); reuses tested ``compute_stats`` /
``frame_symbols`` / ``FILES`` / ``SPAN_PS`` from msd_c0_delayscan.
Difference: per source, time-ordered pair split (pairing output is
monotonic) into EST = first 10k pairs, TEST = rest. Delta scan (41 pts,
step 5ps, bw 200/400) runs on EST ONLY (p/p-/support); delta*_est is then
applied to TEST (2 points: nominal d=0 and d=delta*_est). Stability =
spread of delta*_est across acquisitions + EST-vs-C0-full-delta* gap.
Counts JSON only, no decoding.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_c0_delayscan import (
    BWS,
    FILES,
    SPAN_PS,
    compute_stats,
    frame_symbols,
)

N_EST = 10_000


def self_test() -> None:
    # Split logic + EST-only scan on synthetic pairs (no raw data).
    d = 1024
    aa = np.arange(5000, dtype=np.int64) % d
    bb = aa.copy()
    bb[::4] = (bb[::4] + 1) % d  # p = 0.25 exactly
    est_a, est_b = aa[:1000], bb[:1000]
    tst_a, tst_b = aa[1000:], bb[1000:]
    r_est = compute_stats(est_a, est_b, d)
    r_tst = compute_stats(tst_a, tst_b, d)
    assert r_est["n"] == 1000 and r_tst["n"] == 4000, (r_est, r_tst)
    assert r_est["p"] == 0.25 and r_tst["p"] == 0.25
    assert r_est["support_size"] == 2  # {0, +1}
    print("c0-prefix self-test OK")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", default=None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--n-est", type=int, default=N_EST)
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.full:
        raise SystemExit("M5 runs only with --full")
    if not args.output_root:
        raise SystemExit("M5 --full requires --output-root")
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

    deltas = list(range(-100, 101, 5))
    summary: list[dict] = []
    jl = (root / "m5_rows.jsonl").open("w", encoding="utf-8")
    t_all = time.perf_counter()
    for src, path in FILES.items():
        events = read_ttbin_events(path)
        t = np.asarray(events.time_ps, dtype=np.int64)
        valid = (np.asarray(events.event_type, dtype=np.int64) == 0) \
            if events.event_type is not None else np.ones(t.shape, dtype=bool)
        ch = np.asarray(events.channel, dtype=np.int64)
        t_a, t_b = t[valid & (ch == _m0.CH_A)], t[valid & (ch == _m0.CH_B)]
        tmin = int(t.min())
        offset = aw.require_alignment_passed(
            aw.derive_alignment(events=events, ch_a=_m0.CH_A, ch_b=_m0.CH_B))
        del events
        pa, pb = _pair_nearest_unique(t_a=t_a, t_b=t_b,
                                      window_ps=_m0.COIN_WINDOW_PS,
                                      offset_ps=int(offset))
        del t_a, t_b
        n_est = min(args.n_est, len(pa))
        for bw in BWS:
            d = SPAN_PS // bw
            fa, sa = frame_symbols(pa, bw, d, tmin)
            # EST-only scan.
            est_rows = []
            for dl in deltas:
                fb, sb = frame_symbols(pb[:n_est] + np.int64(dl), bw, d, tmin)
                keep = (fa[:n_est] >= 0) & (fb >= 0) & (fa[:n_est] == fb)
                st = compute_stats(sa[:n_est][keep], sb[keep], d)
                row = {"source": src, "bw_ps": bw, "d": d,
                       "delta_ps": int(dl), "seg": "EST",
                       "offset_ps": int(offset), **st}
                est_rows.append(row)
                jl.write(json.dumps(row) + "\n")
            best = min(est_rows, key=lambda r: r["p"])
            # TEST application (nominal + est-optimum only).
            tst = []
            for dl in (0, best["delta_ps"]):
                fb, sb = frame_symbols(pb[n_est:] + np.int64(dl), bw, d, tmin)
                keep = (fa[n_est:] >= 0) & (fb >= 0) & (fa[n_est:] == fb)
                st = compute_stats(sa[n_est:][keep], sb[keep], d)
                row = {"source": src, "bw_ps": bw, "d": d,
                       "delta_ps": int(dl), "seg": "TEST",
                       "offset_ps": int(offset), **st}
                tst.append(row)
                jl.write(json.dumps(row) + "\n")
            jl.flush()
            nom_e = next(r for r in est_rows if r["delta_ps"] == 0)
            nom_t, opt_t = tst
            summary.append({
                "source": src, "bw_ps": bw, "d": d, "n_est": int(n_est),
                "n_test": int(len(pa) - n_est), "offset_ps": int(offset),
                "est_nom_p": nom_e["p"], "delta_star_est": best["delta_ps"],
                "est_best_p": best["p"],
                "test_nom_p": nom_t["p"], "test_best_p": opt_t["p"],
                "test_best_pm": opt_t["p_minus_cond"],
                "test_best_sup": opt_t["support_size"],
                "test_best_dist": opt_t["top_errors"]})
            print(f"{src} bw={bw} EST*: {best['delta_ps']}ps "
                  f"p {nom_e['p']}->{best['p']} | TEST: "
                  f"{nom_t['p']}->{opt_t['p']}", flush=True)
        del pa, pb
    jl.close()
    (root / "m5_summary.json").write_text(json.dumps(
        {"deltas_ps": deltas, "n_est": args.n_est, "track": "DECIDE-zero-decode",
         "wall_s_total": round(time.perf_counter() - t_all, 1),
         "cells": summary}, indent=2), encoding="utf-8")
    print(f"wrote {len(summary)} cells")


if __name__ == "__main__":
    main()
