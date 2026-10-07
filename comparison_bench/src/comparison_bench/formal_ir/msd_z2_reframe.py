"""Z-2 reframe statistics (Z2_PREEXECUTE.md, DECIDE zero-decode): per (file, bw)
pair with frozen M5 chain + frame at (span 204800, bw, d) + error statistics
(support, p, p-, lag-1 memory, event rate, H(e)/H(A|B) closure). Counts JSON
only, no decoding.
R1 1.21 files use base variant (M0/M3C precedent); 1.23 files use .1 variant.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

SPAN_PS = 204800
BWS = (50, 100, 200, 400, 6400)
FILES = {
    "T2-1M": "D:/Data/Raw Data/2026.1.21/Type2_1M_3s_2026-01-21_184040/Type2_1M_3s_2026-01-21_184040.ttbin",
    "T2-1.5M": "D:/Data/Raw Data/2026.1.21/Type2_1-5M_3s_2026-01-21_183806/Type2_1-5M_3s_2026-01-21_183806.ttbin",
    "T2-2M": "D:/Data/Raw Data/2026.1.21/Type2_2M_3s_2026-01-21_183657/Type2_2M_3s_2026-01-21_183657.ttbin",
    "0dB": "D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_0dB_2026-01-23_174534.1.ttbin",
    "4dB": "D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_4dB_2026-01-23_174758.1.ttbin",
    "10dB": "D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_10dB_2026-01-23_174842.1.ttbin",
}


def h2(x: float) -> float:
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -(x * math.log2(x) + (1 - x) * math.log2(1 - x))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("Z-2 runs only with --full")
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

    rows = []
    for src, path in FILES.items():
        events = read_ttbin_events(path)
        t = np.asarray(events.time_ps, dtype=np.int64)
        valid = (np.asarray(events.event_type, dtype=np.int64) == 0) \
            if events.event_type is not None else np.ones(t.shape, dtype=bool)
        ch = np.asarray(events.channel, dtype=np.int64)
        t_a, t_b = t[valid & (ch == _m0.CH_A)], t[valid & (ch == _m0.CH_B)]
        tmin = int(t.min())
        n_ev = int(valid.sum())
        offset = aw.require_alignment_passed(
            aw.derive_alignment(events=events, ch_a=_m0.CH_A, ch_b=_m0.CH_B))
        del events
        pa, pb = _pair_nearest_unique(t_a=t_a, t_b=t_b,
                                      window_ps=_m0.COIN_WINDOW_PS,
                                      offset_ps=int(offset))
        n_pairs = len(pa)
        for bw in BWS:
            d = SPAN_PS // bw
            t0 = time.perf_counter()
            fa, sa = _frame_global(t_ps=pa, bin_width_ps=bw, frame_bins=d,
                                   t0_ps=tmin)
            fb, sb = _frame_global(t_ps=pb, bin_width_ps=bw, frame_bins=d,
                                   t0_ps=tmin)
            keep = (fa >= 0) & (fb >= 0) & (fa == fb) & (sa >= 0) & (sb >= 0)
            aa = sa[keep].astype(np.int64)
            bb = sb[keep].astype(np.int64)
            n = len(aa)
            ee = (bb - aa) % d
            vals, cnts = np.unique(ee, return_counts=True)
            probs = cnts / n
            he = float(-(probs * np.log2(np.maximum(probs, 1e-300))).sum())
            p = float(1.0 - (cnts[vals.tolist().index(0)] / n if 0 in vals else 0.0))
            # p- = P(e==-1|marked)
            neg = (d - 1) if d > 1 else 0
            n_neg = int(cnts[vals.tolist().index(neg)] if neg in vals else 0)
            n_mark = int(n - (cnts[vals.tolist().index(0)] if 0 in vals else 0))
            pm = float(n_neg / n_mark) if n_mark else float("nan")
            ind = (ee != 0).astype(float)
            lag1 = float(np.corrcoef(ind[:-1], ind[1:])[0, 1]) if n > 10 else float("nan")
            decomp = h2(p) + (p * h2(pm) if pm == pm and 0 < pm < 1 else 0.0)
            # H(A|B) via joint table
            jt = np.zeros((d, d))
            np.add.at(jt, (aa, bb), 1)
            tot = jt.sum()
            pb_m = jt.sum(axis=0) / tot
            with np.errstate(divide="ignore", invalid="ignore"):
                cond = jt / jt.sum(axis=0, keepdims=True)
                hab = float(-np.nansum((jt / tot) * np.log2(np.where(cond > 0, cond, 1.0))))
            top = sorted([(int(v), round(float(c / n), 6)) for v, c in zip(vals, cnts)],
                         key=lambda kv: -kv[1])  # FULL support (<=9), not top-6
            wide = bool((np.abs(np.minimum(ee, d - ee)) > 1).any())
            rows.append({"source": src, "bw_ps": bw, "d": d, "pairs": n,
                         "events": n_ev, "offset_ps": int(offset),
                         "support_size": int(len(vals)), "top_errors": top,
                         "p": round(p, 6), "p_minus_cond": round(pm, 6) if pm == pm else None,
                         "lag1_corr": round(lag1, 5) if lag1 == lag1 else None,
                         "H_e": round(he, 4), "H_AB": round(hab, 4),
                         "decomp": round(decomp, 4), "wide_window": wide,
                         "wall_s": round(time.perf_counter() - t0, 1)})
            print(src, f"bw={bw}", f"d={d}", f"n={n}", f"sup={len(vals)}",
                  f"p={p:.4f}", f"He={he:.4f}", f"HAB={hab:.4f}",
                  "WIDE" if wide else "", flush=True)
    (root / "z2_summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows")


if __name__ == "__main__":
    main()
