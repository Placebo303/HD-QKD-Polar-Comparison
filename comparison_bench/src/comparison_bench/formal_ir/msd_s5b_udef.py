"""S-5b U-definition check (S5B_PREEXECUTE.md, DECIDE zero-decode).

Confirms U (okA + level-B ok + exact fail) == blocks containing |e|>=2 events:
per-symbol wide rate per source vs C-0 tails; blocks-with-wide count vs S-4d
landed U counts; narrow-subset reconstruction closure. No decoding.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

SPAN_PS = 204800
BW = 200
D = SPAN_PS // BW
N = 4096

FILES = {
    "T2-1M": ("D:/Data/Raw Data/2026.1.21/Type2_1M_3s_2026-01-21_184040/Type2_1M_3s_2026-01-21_184040.ttbin", -50),
    "T2-1.5M": ("D:/Data/Raw Data/2026.1.21/Type2_1-5M_3s_2026-01-21_183806/Type2_1-5M_3s_2026-01-21_183806.ttbin", +50),
    "T2-2M": ("D:/Data/Raw Data/2026.1.21/Type2_2M_3s_2026-01-21_183657/Type2_2M_3s_2026-01-21_183657.ttbin", +50),
    "0dB": ("D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_0dB_2026-01-23_174534.1.ttbin", -50),
    "4dB": ("D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_4dB_2026-01-23_174758.1.ttbin", -50),
}
# S-4d landed U (soft/plain) + C-0 tail mass per pair (bw200 cal)
S4D_U = {"T2-1M": 7, "T2-1.5M": 22, "T2-2M": 44, "0dB": 5, "4dB": 4}
C0_TAIL = {"T2-1M": 1.3e-05, "T2-1.5M": 3.3e-05, "T2-2M": 5.0e-05,
           "0dB": 2.2e-05, "4dB": 3.5e-05}


def self_test() -> None:
    rng = np.random.default_rng(0)
    d = 1024
    b = rng.integers(0, d, size=20000)
    e = np.zeros(20000, dtype=np.int64)
    mk = rng.random(20000) < 0.06
    e[mk] = np.where(rng.random(mk.sum()) < 0.6, -1, 1)
    e[500] = 2
    e[1500] = -2
    a = (b - e) % d
    ee = (b - a) % d
    es = np.where(ee <= d // 2, ee, ee - d)
    wide = np.abs(es) >= 2
    assert wide.sum() == 2 and wide[500] and wide[1500]
    assert float(wide.mean()) == round(2 / 20000, 6)
    print("s5b self-test OK (wide detection)")


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
        raise SystemExit("S-5b runs only with --full")
    if not args.output_root:
        raise SystemExit("S-5b --full requires --output-root")
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

    import scipy.stats as st
    jl = (root / "s5b_rows.jsonl").open("w", encoding="utf-8")
    summary: dict = {"track": "DECIDE-zero-decode", "sources": {}}
    csv_rows = ["source,n_pairs,wide_rate,wide_ci_lo,wide_ci_hi,n_blocks,blocks_wide,pred_U_C0,landed_U"]
    t_all = time.perf_counter()
    for src, (path, dl) in FILES.items():
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
            jl.write(json.dumps({"source": src, "blocked": status}) + "\n")
            summary["sources"][src] = {"blocked": status}
            continue
        pa, pb = _pair_nearest_unique(t_a=t_a, t_b=t_b,
                                      window_ps=_m0.COIN_WINDOW_PS,
                                      offset_ps=int(off))
        del t_a, t_b, events
        pb = pb + np.int64(dl)
        fa, sa = _frame_global(t_ps=pa, bin_width_ps=BW, frame_bins=D, t0_ps=tmin)
        fb, sb = _frame_global(t_ps=pb, bin_width_ps=BW, frame_bins=D, t0_ps=tmin)
        keep = (fa >= 0) & (fb >= 0) & (fa == fb)
        aa, bb = sa[keep].astype(np.int64), sb[keep].astype(np.int64)
        ee = (bb - aa) % D
        es = np.where(ee <= D // 2, ee, ee - D)
        wide = np.abs(es) >= 2
        n = len(aa)
        wr = float(wide.mean())
        lo = 0.0 if wide.sum() == 0 else float(st.beta.ppf(0.025, wide.sum(), n - wide.sum() + 1))
        hi = 1.0 if wide.sum() == n else float(st.beta.ppf(0.975, wide.sum() + 1, n - wide.sum()))
        nblk = n // N
        bwblk = sum(1 for i in range(nblk) if wide[i * N:(i + 1) * N].any())
        pred = nblk * N * C0_TAIL[src]
        # narrow-subset reconstruction closure
        nm = (ee != 0) & (np.abs(es) <= 1)
        a0 = (aa % 2).astype(np.uint8)
        b0 = (bb % 2).astype(np.uint8)
        a1 = ((aa >> 1) & 1).astype(np.uint8)
        b1 = ((bb >> 1) & 1).astype(np.uint8)
        sgn = (es == -1).astype(np.uint8)
        g1 = float((a1[nm] == (b1[nm] ^ a0[nm] ^ sgn[nm])).mean()) if nm.sum() else None
        rec = np.where(sgn[nm] == 1, (bb[nm] + 1) % D, (bb[nm] - 1 + D) % D)
        recon = float((rec == aa[nm]).mean()) if nm.sum() else None
        row = {"source": src, "n_pairs": n, "wide_rate": round(wr, 7),
               "wide_ci95": [round(lo, 7), round(hi, 7)], "n_blocks": nblk,
               "blocks_wide": bwblk, "pred_U_C0": round(pred, 1),
               "landed_U": S4D_U[src], "G1_narrow": round(g1, 5) if g1 is not None else None,
               "recon_narrow": round(recon, 5) if recon is not None else None,
               "wall_s": round(time.perf_counter() - t0, 1)}
        summary["sources"][src] = row
        jl.write(json.dumps(row) + "\n")
        jl.flush()
        csv_rows.append(f"{src},{n},{wr:.7f},{lo:.7f},{hi:.7f},{nblk},{bwblk},{pred:.1f},{S4D_U[src]}")
        print(f"  wide={wr:.2e}{[round(lo,7),round(hi,7)]} blocks_wide={bwblk} "
              f"pred_C0={pred:.1f} landed_U={S4D_U[src]} G1={row['G1_narrow']}", flush=True)
    jl.close()
    (root / "s5b_table.csv").write_text("\n".join(csv_rows) + "\n", encoding="utf-8")
    summary["wall_s_total"] = round(time.perf_counter() - t_all, 1)
    (root / "s5b_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(f"S-5b done wall={summary['wall_s_total']}s -> {root}")


if __name__ == "__main__":
    main()
