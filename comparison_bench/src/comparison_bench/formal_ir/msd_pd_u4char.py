"""P-d U-4 characterization (user-authorized; zero-decode): read 2026.1.23
Type2_1M trio ttbin, frozen M5-style chain (pair+frame), compute SER, event
rates, joint counts. NO syndromes, NO decode. Output: per-file JSON + joint
counts (for prior-mass-use assessment). Budget 1800 s.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

FILES = {
    "0dB": "D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_0dB_2026-01-23_174534.1.ttbin",
    "4dB": "D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_4dB_2026-01-23_174758.1.ttbin",
    "10dB": "D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_10dB_2026-01-23_174842.1.ttbin",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    import sys
    sys.path.insert(0, ".")
    from comparison_bench.src.comparison_bench.io import align_wrapper as aw
    from comparison_bench.src.comparison_bench.io.ttbin_compat import (
        install_timetagger_alias,
    )
    from comparison_bench.src.comparison_bench.cli.probes_closed import (
        m0_realframe_runner as m0,
    )

    install_timetagger_alias()
    from src.qkd_io.ttbin_pipeline import (
        _frame_global,
        _pair_nearest_unique,
        read_ttbin_events,
    )

    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for tag, base in FILES.items():
        t0 = time.perf_counter()
        events = read_ttbin_events(base)
        t = np.asarray(events.time_ps, dtype=np.int64)
        valid = (np.asarray(events.event_type, dtype=np.int64) == 0) \
            if events.event_type is not None else np.ones(t.shape, dtype=bool)
        ch = np.asarray(events.channel, dtype=np.int64)
        n_a = int((valid & (ch == m0.CH_A)).sum())
        n_b = int((valid & (ch == m0.CH_B)).sum())
        t_a, t_b = t[valid & (ch == m0.CH_A)], t[valid & (ch == m0.CH_B)]
        tmin = int(t.min())
        span_s = (int(t.max()) - tmin) / 1e12
        align = aw.derive_alignment(events=events, ch_a=m0.CH_A, ch_b=m0.CH_B)
        offset = aw.require_alignment_passed(align)
        del events
        pa, pb = _pair_nearest_unique(t_a=t_a, t_b=t_b, window_ps=m0.COIN_WINDOW_PS,
                                      offset_ps=int(offset))
        fa, sa = _frame_global(t_ps=pa, bin_width_ps=m0.BIN_WIDTH_PS,
                               frame_bins=m0.FRAME_BINS, t0_ps=tmin)
        fb, sb = _frame_global(t_ps=pb, bin_width_ps=m0.BIN_WIDTH_PS,
                               frame_bins=m0.FRAME_BINS, t0_ps=tmin)
        keep = (fa >= 0) & (fb >= 0) & (fa == fb) & (sa >= 0) & (sb >= 0)
        a, b = sa[keep].astype(np.int64), sb[keep].astype(np.int64)
        n_pairs = int(keep.sum())
        ser = float((a != b).mean()) if n_pairs else float("nan")
        joint = np.zeros((1024, 1024), dtype=np.int64)
        if n_pairs:
            np.add.at(joint, (a, b), 1)
        np.savez_compressed(root / f"u4_{tag}_joint.npz", joint=joint)
        tot = joint.sum()
        pa_m = joint.sum(axis=1) / tot if tot else joint.sum(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            hab = float(-(joint / tot * np.log2(np.maximum(
                joint / np.maximum(joint.sum(axis=0, keepdims=True), 1),
                1e-300))).sum()) if tot else float("nan")
        wall = time.perf_counter() - t0
        rows.append({"file": tag, "n_events_A": n_a, "n_events_B": n_b,
                     "span_s": span_s, "rate_A_cps": n_a / span_s,
                     "rate_B_cps": n_b / span_s, "n_pairs": n_pairs,
                     "pairs_per_s": n_pairs / span_s, "SER": ser,
                     "support": int((joint > 0).sum()), "H_AB_plugin": hab,
                     "offset_ps": int(offset),
                     "wall_s": wall})
        print(tag, "pairs", n_pairs, "SER", round(ser, 4), flush=True)
    (root / "pd_summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
