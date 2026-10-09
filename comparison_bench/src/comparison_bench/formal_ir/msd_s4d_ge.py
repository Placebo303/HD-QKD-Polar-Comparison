"""S-4d segment 0a: post-hoc GE solvability diagnostic (no new data).

For S-3's saved level-B-failed blocks (okA=True, okB=False from landed
s3_blocks.jsonl): deterministically rebuild the EXACT instances (frozen
H seeds + frozen framing chain, same 5 sources) and check the GF(2) systems
(Hsub, synB) and rescue-extended ([Hsub;HRsub], [synB;synR]) for rank,
nullity and uniqueness.

Reading: synB derives from true y, so solvability per se is guaranteed
(y_true solves it) — the informative quantities are NULLITY (unique vs
ambiguous) and rank. uniq-everywhere + BP-100-iter-fail-100% ==> "BP stuck
on this structure" (paper sentence); nullity>0 ==> ambiguous system noted.
"Steps-vs-structure" (100 vs more iters) needs a decoder rerun, NOT done
here (would be a real-data decode beyond this GE order) — stated as open.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_s3_softdecode import (
    K2,
    QA,
    build_ra,
)

SPAN_PS = 204800
BW = 200
D = SPAN_PS // BW
N = 4096
FR = 0.10

SOURCES = {
    "T2-1M": ("D:/Data/Raw Data/2026.1.21/Type2_1M_3s_2026-01-21_184040/Type2_1M_3s_2026-01-21_184040.ttbin", -50),
    "T2-1.5M": ("D:/Data/Raw Data/2026.1.21/Type2_1-5M_3s_2026-01-21_183806/Type2_1-5M_3s_2026-01-21_183806.ttbin", +50),
    "T2-2M": ("D:/Data/Raw Data/2026.1.21/Type2_2M_3s_2026-01-21_183657/Type2_2M_3s_2026-01-21_183657.ttbin", +50),
    "0dB": ("D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_0dB_2026-01-23_174534.1.ttbin", -50),
    "4dB": ("D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_4dB_2026-01-23_174758.1.ttbin", -50),
}


def gf2_rank_nullity(rows: list[int], ncols: int) -> tuple[int, int]:
    """Rank + nullity of a binary matrix given as row bitmask ints."""
    basis: dict[int, int] = {}
    for r in rows:
        v = r
        while v:
            hb = v.bit_length() - 1
            if hb in basis:
                v ^= basis[hb]
            else:
                basis[hb] = v
                break
    rank = len(basis)
    return rank, ncols - rank


def self_test() -> None:
    # full-rank tall, rank-deficient, empty-column cases
    assert gf2_rank_nullity([0b101, 0b011, 0b110], 3) == (2, 1)
    assert gf2_rank_nullity([0b100, 0b010, 0b001], 3) == (3, 0)
    assert gf2_rank_nullity([0b000, 0b000], 2) == (0, 2)
    print("s4d-ge self-test OK (rank/nullity)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", required=False, default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.output_root:
        raise SystemExit("s4d-ge requires --output-root")
    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    from comparison_bench.src.comparison_bench.io import align_wrapper as aw
    from comparison_bench.src.comparison_bench.io.ttbin_compat import (
        install_timetagger_alias,
    )
    from comparison_bench.src.comparison_bench.cli.probes_closed import (  # noqa: E402
        m0_realframe_runner as _m0,
    )
    install_timetagger_alias()
    from src.qkd_io.ttbin_pipeline import (  # noqa: E402
        _frame_global,
        _pair_nearest_unique,
        read_ttbin_events,
    )

    # S-3 saved failed blocks with okA (level-B failed): select (cell, block)
    want: dict[str, set[int]] = {}
    n_rows = 0
    for line in open("workspace/s3_softdecode/s3_20261009/s3_blocks.jsonl", encoding="utf-8"):
        r = json.loads(line)
        n_rows += 1
        if r["okA"] and not r["okB"]:
            want.setdefault(r["cell"], set()).add(int(r["block"]))
    H_B = build_ra(N, int(N * FR), QA, seed=2000 + N).tocsr()
    H_R = build_ra(N, K2, QA, seed=3000 + N).tocsr()

    def sub_masks(H, cols: np.ndarray) -> list[int]:
        sub = H[:, cols].toarray().astype(np.uint8)
        return [int.from_bytes(np.packbits(r).tobytes(), "big") for r in sub]
    jl = (root / "s4d_ge_rows.jsonl").open("w", encoding="utf-8")
    summary: dict = {"track": "post-hoc-GE-no-new-data", "cells": {}}
    t_all = time.perf_counter()
    for src, (path, dl) in SOURCES.items():
        events = read_ttbin_events(path)
        t = np.asarray(events.time_ps, dtype=np.int64)
        valid = (np.asarray(events.event_type, dtype=np.int64) == 0) \
            if events.event_type is not None else np.ones(t.shape, dtype=bool)
        ch = np.asarray(events.channel, dtype=np.int64)
        t_a, t_b = t[valid & (ch == _m0.CH_A)], t[valid & (ch == _m0.CH_B)]
        tmin = int(t.min())
        off = aw.require_alignment_passed(
            aw.derive_alignment(events=events, ch_a=_m0.CH_A, ch_b=_m0.CH_B))
        del events
        pa, pb = _pair_nearest_unique(t_a=t_a, t_b=t_b,
                                      window_ps=_m0.COIN_WINDOW_PS,
                                      offset_ps=int(off))
        del t_a, t_b
        pb = pb + np.int64(dl)
        fa, sa = _frame_global(t_ps=pa, bin_width_ps=BW, frame_bins=D, t0_ps=tmin)
        fb, sb = _frame_global(t_ps=pb, bin_width_ps=BW, frame_bins=D, t0_ps=tmin)
        keep = (fa >= 0) & (fb >= 0) & (fa == fb)
        aa, bb = sa[keep].astype(np.int64), sb[keep].astype(np.int64)
        ee = (bb - aa) % D
        x = (ee % 2).astype(np.uint8)
        a1 = ((aa >> 1) & 1).astype(np.uint8)
        nblk = len(x) // N
        stat = {"n_blocks": nblk, "n_ge": 0, "unique": 0, "nullity_hist": {},
                "k_min_med_max": []}
        ks = []
        for cell in (f"{src}/hard/{N}", f"{src}/soft/{N}"):
            for bi in sorted(want.get(cell, ())):
                if bi >= nblk:
                    continue
                s = slice(bi * N, (bi + 1) * N)
                mk = np.flatnonzero(x[s] == 1)  # true marked (okA blocks: == decoded)
                k = len(mk)
                ks.append(k)
                brows = sub_masks(H_B, mk)
                rank, null = gf2_rank_nullity(brows, k)
                # rescue-extended
                rrows = sub_masks(H_R, mk)
                rank2, null2 = gf2_rank_nullity(brows + rrows, k)
                stat["n_ge"] += 1
                stat["unique"] += (null == 0)
                stat["nullity_hist"][str(null)] = stat["nullity_hist"].get(str(null), 0) + 1
                jl.write(json.dumps({"cell": cell, "block": bi, "k": k,
                                     "rank": rank, "nullity": null,
                                     "rank_ext": rank2, "nullity_ext": null2}) + "\n")
        if ks:
            stat["k_min_med_max"] = [int(min(ks)), round(float(np.median(ks)), 1), int(max(ks))]
        summary["cells"][src] = stat
        jl.flush()
        print(f"{src}: ge={stat['n_ge']} unique={stat['unique']} "
              f"nullity={stat['nullity_hist']} k={stat['k_min_med_max']}", flush=True)
    jl.close()
    summary["wall_s_total"] = round(time.perf_counter() - t_all, 1)
    (root / "s4d_ge_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(f"ge done wall={summary['wall_s_total']}s -> {root}")


if __name__ == "__main__":
    main()
