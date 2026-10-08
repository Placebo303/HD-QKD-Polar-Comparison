"""C-0 residual-delay scan (C_BATCH_PREREG_20261008.md, DECIDE zero-decode).

Frozen chain (same as Z-2/M5): base-variant read + derive_alignment gate +
_pair_nearest_unique (window 200 ps, nominal offset) + _frame_global.
Pairing is frozen once per source at the nominal offset; the delta scan
shifts Bob's paired times (pb + delta) before re-framing, isolating the
bin-assignment (clock-residual) effect. One re-pairing control (T2-1M,
3 deltas) bounds the frozen-pairing bias. Output: counts JSON only.

Stats per (source, bw, delta): n, p, p_minus_cond, support only.
p_minus_cond keeps the Z-2 definition P(e == d-1 | e != 0) so C-2 can
compare directly; flipped sources (≈0.99) keep their dominant direction.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

SPAN_PS = 204800
BWS = (200, 400)
FILES = {
    "T2-1M": "D:/Data/Raw Data/2026.1.21/Type2_1M_3s_2026-01-21_184040/Type2_1M_3s_2026-01-21_184040.ttbin",
    "T2-1.5M": "D:/Data/Raw Data/2026.1.21/Type2_1-5M_3s_2026-01-21_183806/Type2_1-5M_3s_2026-01-21_183806.ttbin",
    "T2-2M": "D:/Data/Raw Data/2026.1.21/Type2_2M_3s_2026-01-21_183657/Type2_2M_3s_2026-01-21_183657.ttbin",
    "0dB": "D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_0dB_2026-01-23_174534.1.ttbin",
    "4dB": "D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_4dB_2026-01-23_174758.1.ttbin",
    "10dB": "D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_10dB_2026-01-23_174842.1.ttbin",
}


def compute_stats(aa: np.ndarray, bb: np.ndarray, d: int) -> dict:
    n = int(len(aa))
    if n == 0:
        return {"n": 0, "p": None, "p_minus_cond": None,
                "support_size": 0, "top_errors": []}
    ee = (bb.astype(np.int64) - aa.astype(np.int64)) % d
    vals, cnts = np.unique(ee, return_counts=True)
    probs = cnts / n
    n0 = int(cnts[vals.tolist().index(0)]) if 0 in vals else 0
    p = float(1.0 - n0 / n)
    neg = d - 1
    n_neg = int(cnts[vals.tolist().index(neg)]) if neg in vals else 0
    n_mark = int(n - n0)
    pm = float(n_neg / n_mark) if n_mark else float("nan")
    top = sorted(((int(v), round(float(c / n), 6)) for v, c in zip(vals, cnts)),
                 key=lambda kv: -kv[1])
    return {"n": n, "p": round(p, 6),
            "p_minus_cond": round(pm, 6) if pm == pm else None,
            "support_size": int(len(vals)), "top_errors": top}


def frame_symbols(t: np.ndarray, bw: int, d: int, t0: int):
    rel = np.maximum(t.astype(np.int64) - np.int64(t0), 0)
    bidx = np.floor_divide(rel, np.int64(bw))
    return (np.floor_divide(bidx, np.int64(d)).astype(np.int64),
            np.mod(bidx, np.int64(d)).astype(np.int64))


def self_test() -> None:
    # Tiny exact checks, no real data.
    aa = np.array([0, 0, 0, 1, 5], dtype=np.int64)
    bb = np.array([0, 1, 1023, 1, 5], dtype=np.int64)
    r = compute_stats(aa, bb, 1024)
    assert r["n"] == 5, r
    assert r["p"] == round(2 / 5, 6), r
    assert r["p_minus_cond"] == round(1 / 2, 6), r
    assert r["support_size"] == 3, r
    fa, sa = frame_symbols(np.array([0, 199, 200, 400]), 200, 1024, 0)
    assert sa.tolist() == [0, 0, 1, 2], (fa.tolist(), sa.tolist())
    assert fa.tolist() == [0, 0, 0, 0], fa.tolist()
    print("c0 self-test OK")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=False, default=None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--delta-min", type=int, default=-100)
    ap.add_argument("--delta-max", type=int, default=100)
    ap.add_argument("--delta-step", type=int, default=5)
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.full:
        raise SystemExit("C-0 runs only with --full")
    if not args.output_root:
        raise SystemExit("C-0 --full requires --output-root")
    if not (args.delta_step <= 5 and args.delta_step > 0):
        raise SystemExit("prereg requires step <= 5 ps")
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

    deltas = list(range(args.delta_min, args.delta_max + 1, args.delta_step))
    rows: list[dict] = []
    jl = (root / "c0_rows.jsonl").open("w", encoding="utf-8")
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
        for bw in BWS:
            d = SPAN_PS // bw
            fa, sa = _frame_global(t_ps=pa, bin_width_ps=bw,
                                   frame_bins=d, t0_ps=tmin)
            for dl in deltas:
                fb, sb = _frame_global(t_ps=(pb + np.int64(dl)),
                                       bin_width_ps=bw,
                                       frame_bins=d, t0_ps=tmin)
                keep = (fa >= 0) & (fb >= 0) & (fa == fb)
                st = compute_stats(sa[keep], sb[keep], d)
                row = {"source": src, "bw_ps": bw, "d": d,
                       "delta_ps": int(dl), "offset_ps": int(offset),
                       "pairs": int(len(pa)), **st,
                       "repaired": False, "wall_s": 0.0}
                rows.append(row)
                jl.write(json.dumps(row) + "\n")
            jl.flush()
            best = min((r for r in rows if r["source"] == src and r["bw_ps"] == bw),
                       key=lambda r: r["p"])
            nom = next(r for r in rows if r["source"] == src
                       and r["bw_ps"] == bw and r["delta_ps"] == 0)
            print(f"{src} bw={bw} d={d} nominal p={nom['p']} "
                  f"best p={best['p']} @ {best['delta_ps']}ps "
                  f"(gain={nom['p'] - best['p']:.4f})", flush=True)
        # Re-pairing control: T2-1M only, 3 deltas, bounds frozen-pairing bias.
        if src == "T2-1M":
            events = read_ttbin_events(path)
            t = np.asarray(events.time_ps, dtype=np.int64)
            valid = (np.asarray(events.event_type, dtype=np.int64) == 0) \
                if events.event_type is not None else np.ones(t.shape, dtype=bool)
            ch = np.asarray(events.channel, dtype=np.int64)
            t_a, t_b = t[valid & (ch == _m0.CH_A)], t[valid & (ch == _m0.CH_B)]
            del events
            for dl in (args.delta_min, 0, args.delta_max):
                t0 = time.perf_counter()
                qa, qb = _pair_nearest_unique(
                    t_a=t_a, t_b=t_b, window_ps=_m0.COIN_WINDOW_PS,
                    offset_ps=int(offset) + int(dl))
                bw = 200
                d = SPAN_PS // bw
                fa, sa = _frame_global(t_ps=qa, bin_width_ps=bw,
                                       frame_bins=d, t0_ps=tmin)
                fb, sb = _frame_global(t_ps=qb, bin_width_ps=bw,
                                       frame_bins=d, t0_ps=tmin)
                keep = (fa >= 0) & (fb >= 0) & (fa == fb)
                st = compute_stats(sa[keep], sb[keep], d)
                row = {"source": src, "bw_ps": bw, "d": d,
                       "delta_ps": int(dl), "offset_ps": int(offset) + int(dl),
                       "pairs": int(len(qa)), **st,
                       "repaired": True,
                       "wall_s": round(time.perf_counter() - t0, 1)}
                rows.append(row)
                jl.write(json.dumps(row) + "\n")
                print(f"CONTROL re-paired {src} d={dl}ps pairs={len(qa)} "
                      f"p={st['p']}", flush=True)
            jl.flush()
            del t_a, t_b
        del pa, pb
    jl.close()
    (root / "c0_summary.json").write_text(
        json.dumps({"deltas_ps": deltas, "bws": list(BWS),
                    "track": "DECIDE-zero-decode",
                    "wall_s_total": round(time.perf_counter() - t_all, 1),
                    "rows": rows}, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows")


if __name__ == "__main__":
    main()
