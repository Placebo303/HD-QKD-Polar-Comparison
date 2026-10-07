"""Z-3 surface + representative real checks (Z3_PREEXECUTE.md, DECIDE):
(a) f(d,bw) surface assembly from Z-1 f(p) x Z-2 p(d,bw) with stated mapping
rules + SKR side metric; (b) two real rep points (d=512,bw=400)x{4dB,0dB},
N=16384, PEG-dv3 gap0.12 + margin3.0, ternary priors (Z-2 frozen p per seg +
same-segment 512 marginal, stated). Single run.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

SPAN_PS = 204800
BW = 400
D = 512
N = 16384
GAP = 0.12
MARGIN = 3.0
B = 300
K2 = 64
SEED = 20267800
TAG_BITS = 64
WORKERS = 12

_W = {}


def h2(x: float) -> float:
    return -(x * math.log2(x) + (1 - x) * math.log2(1 - x))


def _worker_init(payload):
    import pickle
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
        make_bp_decoder as _mbp,
    )
    dense_a, dense_b, pa_l, pp, dd = pickle.loads(payload)
    _W["HA"], _W["HB"] = dense_a, dense_b
    _W["pa"] = np.asarray(pa_l)
    _W["_mbp"] = _mbp
    _W["pp"] = pp
    _W["dd"] = dd


def _decode_one(args) -> dict:
    blk, seed = args[:2]
    real_pair = args[2] if len(args) > 2 else None
    import numpy as _np
    HA, HB = _W["HA"], _W["HB"]
    pa_l, pp, dd = _W["pa"], _W["pp"], _W["dd"]
    p, pm = pp["p"], pp["pm"]
    if real_pair is not None:
        alice = _np.asarray(real_pair[0], dtype=_np.int64)
        bob = _np.asarray(real_pair[1], dtype=_np.int64)
    else:
        rng = _np.random.default_rng(seed + blk)
        aks = _np.arange(dd)
        a = rng.choice(aks, size=N, p=pa_l)
        u = rng.random(size=N)
        e = _np.where(u < 1 - p, 0, _np.where(u < 1 - p * pm, 1, dd - 1)).astype(_np.int64)
        alice = a.astype(_np.int64)
        bob = ((a + e) % dd).astype(_np.int64)
    # level A (model priors)
    xt = (alice & 1).astype(_np.uint8)
    lik0, likp, likm = 1 - p, p * (1 - pm), p * pm
    a_cand = _np.stack([(bob - 1) % dd, bob, (bob + 1) % dd], axis=0)
    w = _np.stack([likm * pa_l[(bob - 1) % dd], lik0 * pa_l[bob],
                   likp * pa_l[(bob + 1) % dd]], axis=0)
    w = w / w.sum(axis=0, keepdims=True)
    p1 = (w * ((a_cand & 1).astype(float))).sum(axis=0)
    base = (p1 > 0.5).astype(_np.uint8)
    ch = _np.minimum(p1, 1 - p1).copy()
    HAd = _np.asarray(HA.toarray(), dtype=_np.uint8)
    syn_a = (HAd @ xt) % 2
    delta = _np.bitwise_xor(syn_a, (HAd @ base) % 2)
    dec = _W["_mbp"](parity_check_matrix=HA, error_channel=ch.copy(), max_iter=200)
    err = _np.asarray(dec.decode(delta.copy())).astype(_np.uint8)
    xh = _np.bitwise_xor(base, err)
    a_ok = bool(_np.array_equal((HAd @ xh) % 2, syn_a)) and bool(_np.array_equal(xh, xt))
    a_extra = 0
    if not a_ok:
        w8 = _np.log((1 - _np.maximum(ch, 1e-300)) / _np.maximum(ch, 1e-300))
        weak = _np.argsort(w8, kind="stable")[:400]
        base[weak] = xt[weak]
        a_extra = 400
        delta2 = _np.bitwise_xor(syn_a, (HAd @ base) % 2)
        dec2 = _W["_mbp"](parity_check_matrix=HA, error_channel=ch.copy(),
                          max_iter=200)
        err2 = _np.asarray(dec2.decode(delta2.copy())).astype(_np.uint8)
        xh = _np.bitwise_xor(base, err2)
        a_ok = bool(_np.array_equal((HAd @ xh) % 2, syn_a)) and bool(_np.array_equal(xh, xt))
    if not a_ok:
        return {"block": blk, "a_ok": False, "exact_full": False,
                "undetected": False, "L_A": int(HA.shape[0]), "L_B": 0,
                "extra": a_extra}
    # level B (sign)
    yb = (bob & 1).astype(_np.uint8)
    marked = (xh != yb)
    b1 = ((bob >> 1) & 1).astype(_np.uint8)
    base1 = _np.where(marked, _np.bitwise_xor(b1, xh), b1).astype(_np.uint8)
    truth1 = ((alice >> 1) & 1).astype(_np.uint8)
    HBd = _np.asarray(HB.toarray(), dtype=_np.uint8)
    syn_b = (HBd @ truth1) % 2
    chb = _np.where(marked, pm, 0.0)
    delta_b = _np.bitwise_xor(syn_b, (HBd @ base1) % 2)
    dec_b = _W["_mbp"](parity_check_matrix=HB, error_channel=chb.copy(), max_iter=200)
    err_b = _np.asarray(dec_b.decode(delta_b.copy())).astype(_np.uint8)
    rec1 = _np.bitwise_xor(base1, err_b)
    b_ok = bool(_np.array_equal((HBd @ rec1) % 2, syn_b)) and bool(_np.array_equal(rec1, truth1))
    b_syn_ok = bool(_np.array_equal((HBd @ rec1) % 2, syn_b))
    extra = 0
    if not b_ok:
        w = _np.log((1 - _np.maximum(chb, 1e-300)) / _np.maximum(chb, 1e-300))
        w[~marked] = _np.inf
        weak = _np.argsort(w, kind="stable")[:K2]
        base1[weak] = truth1[weak]
        extra = K2
        rec1 = base1.copy()
        b_ok = bool(_np.array_equal(rec1, truth1))
    if not b_ok:
        return {"block": blk, "a_ok": True, "exact_full": False,
                "undetected": bool(b_syn_ok), "L_A": int(HA.shape[0]),
                "L_B": int(HB.shape[0]), "extra": extra}
    sgn = _np.bitwise_xor(rec1, _np.bitwise_xor((bob >> 1) & 1, xh)).astype(_np.int64)
    delta_rec = _np.where(~marked, 0, _np.where(sgn == 0, 1, dd - 1)).astype(_np.int64)
    arec = ((bob - delta_rec) % dd).astype(_np.int64)
    full = bool(_np.array_equal(arec, alice))
    return {"block": blk, "a_ok": True, "exact_full": full,
            "undetected": bool((not full)), "L_A": int(HA.shape[0]),
            "L_B": int(HB.shape[0]), "extra": extra}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("Z-3 runs only with --full")
    import concurrent.futures as cf
    import pickle
    from comparison_bench.src.comparison_bench.io import align_wrapper as aw
    from comparison_bench.src.comparison_bench.io.ttbin_compat import (
        install_timetagger_alias,
    )
    from comparison_bench.src.comparison_bench.cli.probes_closed import (  # noqa: E402
        m0_realframe_runner as _m0,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (  # noqa: E402
        build_peg_code,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        wilson_upper,
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

    # (a) surface assembly from frozen Z-1/Z-2 artifacts
    z1 = {r["p"]: r for r in
          json.load(open("workspace/z1_fpcuve/z1_20261008/h4_backbone.json", encoding="utf-8"))
          if r["p"] not in (0.05, 0.10)}  # void points (code-limited) excluded
    z1.update({r["p"]: r for r in
               json.load(open("workspace/z1_fpcuve/z1c_20261008/h4_backbone.json", encoding="utf-8"))})
    z2 = json.load(open("workspace/z2_reframe/z2_20261008b/z2_summary.json", encoding="utf-8"))
    surf = []
    for r in z2:
        p = r["p"]
        # nearest measured Z-1 point (interpolation backbone)
        cand = sorted(z1.keys(), key=lambda q: abs(q - p))
        q = cand[0]
        fz = z1[q]
        if abs(q - p) > 0.03 or r["wide_window"]:
            status = "UNMEASURED (extrapolation or wide-support regime)"
            f_map = None
        else:
            status = f"mapped from Z-1 p={q}"
            f_map = fz["f_expected"]
        # SKR side: R_pair * max(0,2-f) * H_AB (R_pair = pairs/3s)
        skr = (r["pairs"] / 3.0) * max(0.0, 2 - (f_map or 2)) * r["H_AB"] \
            if f_map else None
        surf.append({"source": r["source"], "bw_ps": r["bw_ps"], "d": r["d"],
                     "p": p, "H_AB": r["H_AB"], "R_pair_s": round(r["pairs"] / 3.0, 1),
                     "f_mapped": f_map, "SKR_bps": round(skr, 1) if skr else None,
                     "status": status})
    (root / "z3_surface.json").write_text(json.dumps(surf, indent=2), encoding="utf-8")

    # (b) two real rep points (d=512,bw=400) x {4dB, 0dB}
    segs = {
        "4dB": ("D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_4dB_2026-01-23_174758.1.ttbin", 0.1196),
        "0dB": ("D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_0dB_2026-01-23_174534.1.ttbin", 0.1237),
    }
    jl = root / "blocks_z3.jsonl"
    rows = []
    for seg, (path, p_frozen) in segs.items():
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
        pa_, pb_ = _pair_nearest_unique(t_a=t_a, t_b=t_b,
                                        window_ps=_m0.COIN_WINDOW_PS,
                                        offset_ps=int(offset))
        fa, sa = _frame_global(t_ps=pa_, bin_width_ps=BW, frame_bins=D, t0_ps=tmin)
        fb, sb = _frame_global(t_ps=pb_, bin_width_ps=BW, frame_bins=D, t0_ps=tmin)
        keep = (fa >= 0) & (fb >= 0) & (fa == fb) & (sa >= 0) & (sb >= 0)
        a_all = sa[keep].astype(np.int64)
        b_all = sb[keep].astype(np.int64)
        # 512-marginal from same segment (stated source statistic)
        pa512 = np.bincount(a_all, minlength=D).astype(float)
        pa512 = (pa512 / pa512.sum()).tolist()
        pm = 0.0058
        m_a = min(N - 1, max(1, int(math.ceil(N * (h2(p_frozen) + GAP)))))
        HA = build_peg_code(n=N, m=m_a, variable_degree=3).parity_check_matrix
        m_b = min(N - 1, max(1, int(math.ceil(N * p_frozen * h2(pm) * 3.0))))
        HB = build_peg_code(n=N, m=m_b, variable_degree=3).parity_check_matrix
        payload = pickle.dumps((HA, HB, pa512, {"p": p_frozen, "pm": pm}, D))
        n_blocks = len(a_all) // N
        t0 = time.perf_counter()
        with cf.ProcessPoolExecutor(max_workers=WORKERS,
                                    initializer=_worker_init,
                                    initargs=(payload,)) as ex:
            recs = list(ex.map(_decode_one,
                               [(i, 0, (a_all[i * N:(i + 1) * N].tolist(),
                                        b_all[i * N:(i + 1) * N].tolist()))
                                for i in range(n_blocks)]))
        wall = time.perf_counter() - t0
        with jl.open("a", encoding="utf-8", buffering=1) as fh:
            for r in recs:
                fh.write(json.dumps({"seg": seg, "d": D, "bw": BW, **r}) + "\n")
        nb = len(recs)
        nf = sum(0 if r["exact_full"] else 1 for r in recs)
        nu = sum(1 for r in recs if r["undetected"])
        e_l = sum(r["L_A"] + r["L_B"] + r.get("extra", 0) for r in recs) / nb
        fer = nf / nb
        # H from Z-2 frozen row for this seg@(512,400)
        # empirical H_A from 512 marginal (same-segment source statistic):
        pa_arr = np.asarray(pa512)
        ha_seg = float(-(pa_arr * np.log2(np.maximum(pa_arr, 1e-300))).sum())
        zr = next(x for x in z2 if x["source"] == seg and x["bw_ps"] == 400)
        denom = N * zr["H_AB"]
        kept = N * ha_seg - e_l
        f_p = (e_l + TAG_BITS + kept * fer) / denom
        rows.append({"seg": seg, "d": D, "bw_ps": BW, "N": N, "p_frozen": p_frozen,
                     "H_A_seg": round(ha_seg, 4), "H_AB_seg": zr["H_AB"],
                     "blocks": nb, "failures": nf, "undetected": nu,
                     "E_L": e_l, "FER_exact": fer,
                     "FER_wilson_upper95": wilson_upper(nf, nb),
                     "f_expected": f_p, "backend": "z3-rep",
                     "wall_s": wall})
        print(seg, f"fail {nf}/{nb} f={f_p:.3f}", flush=True)
    (root / "z3_summary.json").write_text(json.dumps({"surface_note": "see z3_surface.json",
                                                     "rep_points": rows}, indent=2),
                                          encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
