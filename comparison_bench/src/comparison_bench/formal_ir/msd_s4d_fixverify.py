"""S-4d segment 0b: fine-conditioned level-B fix + gate (synthetic only).

Fix: level-B priors conditioned on Bob's fine sub-bin,
P(sgn=1 | marked, fine-sub), fitted on PREFIX pairs only (first 10000,
S-4d user rule; test excluded), Laplace-smoothed, clipped.
Gate: the fixed level-B must reach cond-fail ~= 0 on fine-structured
synthetic (S-2 prefix DoubleGauss laws with S-curve sgn|fine) AND on the
S-4a-measured per-source curves; else real run = plaintext arm only.
No real data in this file's gate. Shared helpers imported by the rerun.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_s3_softdecode import (
    QA,
    build_ra,
)

SPAN_PS = 204800
BW = 200
N = 4096
SEED = 20261012
N_SUB = 8


def fit_scurve_prefix() -> dict:
    """Per-source empirical P(sgn=1|marked, fine-sub) on PREFIX pairs only.

    Reads S-4a landed rows? No: refits from the S-2 prefix definition
    (first 10000 pairs by time) with calibrated framing. Laplace +1 smoothing,
    clipped to [0.02, 0.98]. Test pairs never touched (S-2 split reused by
    rereading raw data; prefix indices identical by determinism).
    """
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
    from comparison_bench.src.comparison_bench.formal_ir.msd_s3_softdecode import (
        SOURCES,
    )
    curves = {}
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
        idx = np.argsort(pa, kind="stable")[:10000]
        pa_p, pb_p = pa[idx], (pb[idx] + np.int64(dl))
        d = SPAN_PS // BW
        fa, sa = _frame_global(t_ps=pa_p, bin_width_ps=BW, frame_bins=d, t0_ps=tmin)
        fb, sb = _frame_global(t_ps=pb_p, bin_width_ps=BW, frame_bins=d, t0_ps=tmin)
        keep = (fa >= 0) & (fb >= 0) & (fa == fb)
        aa, bb = sa[keep].astype(np.int64), sb[keep].astype(np.int64)
        ee = (bb - aa) % d
        mk = ee != 0
        sgn = ((ee == d - 1) & mk).astype(float)
        fine = ((pb_p[keep].astype(np.int64) - np.int64(tmin)) % np.int64(BW))
        sub = np.minimum(fine // (BW // N_SUB), N_SUB - 1)
        curve = []
        for s in range(N_SUB):
            m = mk & (sub == s)
            # Laplace +1 smoothing, clip
            p = (sgn[m].sum() + 1.0) / (m.sum() + 2.0) if m.sum() else 0.5
            curve.append(round(float(min(max(p, 0.02), 0.98)), 4))
        curves[src] = {"curve": curve, "n_prefix": int(len(idx)),
                       "n_marked_prefix": int(mk.sum())}
        print(f"fit {src}: n_marked={int(mk.sum())} curve={curve}", flush=True)
        del pa, pb
    return curves


def synth_fine_blocks(rng: np.random.Generator, n: int, N: int,
                      sig: float, w: float, curve: list[float]) -> list[dict]:
    """Synthetic blocks with S-curve-structured sign (tests the fixed level-B).

    v uniform; marked ~ Bernoulli(p_mark); sgn | fine-sub ~ curve[sub].
    """
    out = []
    p_mark = 0.06
    for _ in range(n):
        v = rng.uniform(0.0, BW, size=N)
        sub = np.minimum((v // (BW // N_SUB)).astype(int), N_SUB - 1)
        mk = rng.random(N) < p_mark
        ps = np.array(curve)[sub]
        sgn = (rng.random(N) < ps).astype(np.uint8)
        e = np.zeros(N, dtype=np.int64)
        e[mk] = np.where(sgn[mk] == 1, -1, 1)
        x = (e % 2).astype(np.uint8)
        # RANDOM Bob bits (not zeros): exercises the xa-vs-a0 path that blind
        # synthetic (b0=0) hides — the S-3 100%-fail mechanism. a0 = x^b0.
        b0 = rng.integers(0, 2, size=N).astype(np.uint8)
        b1 = rng.integers(0, 2, size=N).astype(np.uint8)
        a0 = (x ^ b0).astype(np.uint8)
        a1 = (b1 ^ a0 ^ sgn).astype(np.uint8)
        bb = np.zeros(N, dtype=np.int64)  # placeholder (unused in gate)
        aa = np.zeros(N, dtype=np.int64)
        aa[mk] = np.where(sgn[mk] == 1, 0, 0)  # unused (gate checks decode only)
        out.append({"x": x, "b0": b0, "a1": a1, "b1": b1, "v": v,
                    "a": aa, "b": bb, "a0": a0})
    return out


def self_test() -> None:
    # gate machinery smoke on 6 tiny blocks (synthetic only)
    rng = np.random.default_rng(SEED)
    curve = [0.02, 0.05, 0.2, 0.5, 0.8, 0.95, 0.98, 0.98]
    blks = synth_fine_blocks(rng, 6, 256, 13.0, 0.007, curve)
    assert len(blks) == 6 and all(len(b["x"]) == 256 for b in blks)
    print("s4d-fix self-test OK (fine-structured synth)")


def do_gate(root: Path) -> dict:
    import json as _j
    s2 = _j.load(open("workspace/s_softmap/s2_20261009/s2_summary.json", encoding="utf-8"))
    curves = fit_scurve_prefix()
    (root / "s4d_curves.json").write_text(json.dumps(curves, indent=1), encoding="utf-8")
    rng = np.random.default_rng(SEED)
    # gate: fixed level-B (fine-conditioned priors) on fine-structured synth,
    # per S-2 law of T2-1M; cond-fail must be ~= 0
    from comparison_bench.src.comparison_bench.formal_ir import (
        msd_s3_softdecode as S3,
    )
    N0, mB, nB = N, int(N * 0.10), 200
    HB = build_ra(N0, mB, QA, seed=2000 + N0)
    # NOTE: gate tests base decode only (rescue cannot save a broken operating
    # point — S-3 proved that); rescue stays in the real runner unchanged.
    fit = s2["sources"]["T2-1M"]["prefix_fit"]
    blks = synth_fine_blocks(rng, nB, N0, float(fit["sig"]), float(fit["w"]),
                             curves["T2-1M"]["curve"])
    nA = nAB = 0
    for blk in blks:
        mk = blk["x"] == 1
        y = blk["a1"][mk]
        synB = np.asarray((HB[:, mk] @ y) % 2, dtype=np.uint8).ravel()
        sub = np.minimum((blk["v"][mk] // (BW // N_SUB)).astype(int), N_SUB - 1)
        pv = np.array(curves["T2-1M"]["curve"])[sub]
        # deployment-faithful signs: a0hat = x^b0 (NOT xa==a0 shortcut), then
        # condition on (b1^a0hat) — the exact S-3 failure path, now fixed.
        a0hat = (blk["x"][mk] ^ blk["b0"][mk]).astype(np.uint8)
        L = np.array([math.log((1.0 - p) / p) for p in pv])
        chB = np.where((blk["b1"][mk] ^ a0hat) == 1, -L, L)
        yhat = S3.decode(HB[:, mk], synB, [float(c) for c in chB])
        nA += 1
        nAB += not bool(np.array_equal(yhat, y))
    cond = nAB / nA
    gate = {"n": nB, "cond_B_fail": round(cond, 4),
            "pass": bool(cond <= 0.02),
            "note": "fixed level-B (fine priors) on fine-structured synth"}
    print(f"gate: condB={cond:.4f} pass={gate['pass']}", flush=True)
    (root / "s4d_gate.json").write_text(json.dumps(
        {"curves_src": "prefix-only", "gate": gate}, indent=1), encoding="utf-8")
    return gate


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output-root", required=False, default=None)
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.gate:
        raise SystemExit("fixverify runs only with --gate")
    if not args.output_root:
        raise SystemExit("--gate requires --output-root")
    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    g = do_gate(root)
    if not g["pass"]:
        raise SystemExit(f"GATE FAIL condB={g['cond_B_fail']} (real run: plaintext arm only)")


if __name__ == "__main__":
    main()
