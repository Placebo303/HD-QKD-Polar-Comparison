"""G-2 two-level binary IR (G2_PACKET.md): level A = LSB BSC(p) syndrome
(binary PEG + BP, gap ladder, NO rescue — uniform priors carry no reliability
ordering); level B = sign-bit plane syndrome (marked p=0.0058 vs b1^a0,
unmarked structural pins, PEG-BP + K2 rescue); arithmetic higher-bit rebuild.
Parametric (p,p-) memoryless synthetic (credible proxy). Full-symbol f.
Pooled x12. B=300/config.
R14 ideals: A: N*h2(p); B: N*p*h2(p-/p). Margin = actual/ideal - 1.
"""

from __future__ import annotations

import argparse
import functools
import json
import math
import time
from pathlib import Path

import numpy as np

P = 0.2376
# PM_ABS = absolute P(e=-1) = 0.00138; conditional P(-|marked) = PM_ABS/P.
# (Earlier PM=0.0058 was used as an ABSOLUTE rate — 4x too many sign flips.)
PM_ABS = 0.00138
PM_COND = PM_ABS / P
# N=4096 dropped: below BP finite-length threshold at p=0.24 even at gap 0.15
# (0/10); N=16384 works 6/6 at gap 0.12 with model priors.
# N=65536 dropped: PEG build scales ~4x per 2x size (41s/176s measured at
# 8k/16k -> ~50min per 60k-row build; 4 configs infeasible tonight).
# Margin fixed at 3.0 (2.0 omitted: duplicate-config after indent fix revealed
# margin irrelevance at fixed SPC... now PEG-BP; unit test 10/10 across
# 512-1200 keeps single-margin honest; deviation recorded).
NS = (16384, 32768)
MARGINS = (3.0,)
# dv3 needs gap ~0.12 at p=0.24 (measured threshold scan; matches M1 C0 rule).
# Higher dv is worse at these rates. Gap ladder brackets M1's operating point.
GAPS = (0.10, 0.15)
MARGINS = (2.0, 3.0)
B = 300
K2 = 64
SEED = 20267000
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
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primea_repetition import (  # noqa: E402
        GroupMLDecoder as _GML,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primea_repetition import (  # noqa: E402
        spc_matrix as _spc,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primea_repetition import (  # noqa: E402
        split_groups as _sg,
    )
    dense_a, dense_b, pa_l = pickle.loads(payload)
    _W["HA"], _W["HB"] = dense_a, dense_b
    _W["pa"] = np.asarray(pa_l)
    _W["_mbp"] = _mbp
    _W["_GML"], _W["_spc"], _W["_sg"] = _GML, _spc, _sg
    # model-based non-uniform LSB priors P(x0|b) from ternary (pa, p, p-).
    _W["ternary"] = True


def _decode_one(args) -> dict:
    blk, seed, n, m_a, m_b = args[:5]
    real_pair = args[5] if len(args) > 5 else None
    import numpy as _np
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
        _syndrome as _syn,
    )
    HA = _W["HA"]
    if real_pair is not None:
        alice = _np.asarray(real_pair[0], dtype=_np.int64)
        bob = _np.asarray(real_pair[1], dtype=_np.int64)
    else:
        rng = _np.random.default_rng(seed + blk)
        aks = _np.arange(1024)
        a = rng.choice(aks, size=n, p=_W["pa"])
        u = rng.random(size=n)
        e = _np.where(u < 1 - P, 0, _np.where(u < 1 - PM_ABS, 1, 1023)).astype(_np.int64)
        alice = a.astype(_np.int64)
        bob = ((a + e) % 1024).astype(_np.int64)
    # --- level A: LSB with MODEL-BASED non-uniform priors P(x0|b) ---
    xt = (alice & 1).astype(_np.uint8)
    yb = (bob & 1).astype(_np.uint8)
    HAd = _np.asarray(HA.toarray(), dtype=_np.uint8)
    syn_a = (HAd @ xt) % 2
    # ternary posterior: a in {b, b-1, b+1}; P(a|b) propto lik*pa
    dmod = 1024
    pa_l = _W["pa"]
    lik0, likp, likm = 1 - P, P - PM_ABS, PM_ABS
    a_cand = _np.stack([(bob - 1) % dmod, bob, (bob + 1) % dmod], axis=0)
    w = _np.stack([likm * pa_l[(bob - 1) % dmod],
                   lik0 * pa_l[bob],
                   likp * pa_l[(bob + 1) % dmod]], axis=0)
    w = w / w.sum(axis=0, keepdims=True)
    p1 = (w * ((a_cand & 1).astype(_np.float64))).sum(axis=0)
    base = (p1 > 0.5).astype(_np.uint8)
    ch = _np.minimum(p1, 1 - p1)
    delta = _np.bitwise_xor(syn_a, (HAd @ base) % 2)
    dec = _W["_mbp"](parity_check_matrix=HA, error_channel=ch.copy(), max_iter=200)
    err = _np.asarray(dec.decode(delta.copy())).astype(_np.uint8)
    xh = _np.bitwise_xor(base, err)
    a_ok = bool(_np.array_equal((HAd @ xh) % 2, syn_a)) and bool(_np.array_equal(xh, xt))
    a_syn_ok = bool(_np.array_equal((HAd @ xh) % 2, syn_a))
    a_extra = 0
    if not a_ok:
        # K-targeted rescue (priors informative -> weakest meaningful)
        w8 = _np.log((1 - _np.maximum(ch, 1e-300)) / _np.maximum(ch, 1e-300))
        weak = _np.argsort(w8, kind="stable")[:400]
        base[weak] = xt[weak]
        ch[weak] = 0.0
        a_extra = 400
        delta2 = _np.bitwise_xor(syn_a, (HAd @ base) % 2)
        dec2 = _W["_mbp"](parity_check_matrix=HA, error_channel=ch.copy(),
                          max_iter=200)
        err2 = _np.asarray(dec2.decode(delta2.copy())).astype(_np.uint8)
        xh = _np.bitwise_xor(base, err2)
        a_ok = bool(_np.array_equal((HAd @ xh) % 2, syn_a)) and bool(_np.array_equal(xh, xt))
        a_syn_ok = a_syn_ok and bool(_np.array_equal((HAd @ xh) % 2, syn_a))
    if not a_ok:
        return {"block": blk, "a_ok": False, "exact_full": False,
                "undetected": False, "L_A": int(HA.shape[0]), "L_B": 0,
                "extra": a_extra}
    # --- level B: sign on marked via PEG-BP (base fixed: pins now correct).
    # base1 equals truth1 on unmarked (there a==b so a1==b1); on marked it is
    # b1^a0hat, leaving the sign bit as the error to decode.
    HB = _W["HB"]
    HBd = _np.asarray(HB.toarray(), dtype=_np.uint8)
    marked = (xh != yb)
    b1 = ((bob >> 1) & 1).astype(_np.uint8)
    base1 = _np.where(marked, _np.bitwise_xor(b1, xh), b1).astype(_np.uint8)
    truth1 = ((alice >> 1) & 1).astype(_np.uint8)
    syn_b = (HBd @ truth1) % 2
    chb = _np.where(marked, PM_COND, 0.0)
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
        und = b_syn_ok
        return {"block": blk, "a_ok": True, "exact_full": False,
                "undetected": bool(und), "L_A": int(HA.shape[0]),
                "L_B": int(HB.shape[0]), "extra": extra}
    # --- arithmetic rebuild: a = b - delta(mark, sign) ---
    sgn = _np.bitwise_xor(rec1, _np.bitwise_xor((bob >> 1) & 1, xh)).astype(_np.int64)
    delta_rec = _np.where(~marked, 0, _np.where(sgn == 0, 1, 1023)).astype(_np.int64)
    arec = ((bob - delta_rec) % 1024).astype(_np.int64)
    full = bool(_np.array_equal(arec, alice))
    return {"block": blk, "a_ok": True, "exact_full": full,
            "undetected": bool((not full)),
            "L_A": int(HA.shape[0]), "L_B": m_b, "extra": extra}


def run_real_main(args) -> None:
    """G-3 execution (authorized Pre-EXECUTE only): two-level chain on real
    superframes (4dB/10dB clean + 0dB retest), best + control configs."""
    import concurrent.futures as cf
    import pickle
    from comparison_bench.src.comparison_bench.io import align_wrapper as aw
    from comparison_bench.src.comparison_bench.io.ttbin_compat import (
        install_timetagger_alias,
    )
    from comparison_bench.src.comparison_bench.cli.probes_closed import (  # noqa: E402
        m0_realframe_runner as _m0,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        load_train_table,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (  # noqa: E402
        build_peg_code,
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

    def load_seg(path):
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
        fa, sa = _frame_global(t_ps=pa, bin_width_ps=200, frame_bins=1024,
                               t0_ps=tmin)
        fb, sb = _frame_global(t_ps=pb, bin_width_ps=200, frame_bins=1024,
                               t0_ps=tmin)
        keep = (fa >= 0) & (fb >= 0) & (fa == fb) & (sa >= 0) & (sb >= 0)
        return sa[keep].astype(np.int64), sb[keep].astype(np.int64), int(offset)

    segs = {
        "4dB": "D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_4dB_2026-01-23_174758.1.ttbin",
        "10dB": "D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_10dB_2026-01-23_174842.1.ttbin",
        "0dB": "D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_0dB_2026-01-23_174534.1.ttbin",
    }
    t = np.asarray(load_train_table("T2-1M"), dtype=np.float64)
    pa = (t.sum(axis=1) / t.sum()).tolist()
    hA = h2(P)
    hB = P * h2(PM_COND)
    jl = root / "blocks_g3.jsonl"
    rows = []
    for seg, path in segs.items():
        a_all, b_all, off = load_seg(path)
        for n in (32768, 16384):
            n_blocks = len(a_all) // n
            if n_blocks < 1:
                print(f"{seg} N={n}: SKIP (only {len(a_all)} pairs)", flush=True)
                rows.append({"seg": seg, "N": n, "skipped": True,
                             "pairs": int(len(a_all))})
                continue
            gap, margin = 0.15, 3.0
            m_a = min(n - 1, max(1, int(math.ceil(n * (hA + gap)))))
            HA = build_peg_code(n=n, m=m_a, variable_degree=3).parity_check_matrix
            m_b = min(n - 1, max(1, int(math.ceil(n * hB * margin))))
            HB = build_peg_code(n=n, m=m_b, variable_degree=3).parity_check_matrix
            payload = pickle.dumps((HA, HB, pa))
            t0 = time.perf_counter()
            with cf.ProcessPoolExecutor(max_workers=WORKERS,
                                        initializer=_worker_init,
                                        initargs=(payload,)) as ex:
                recs = list(ex.map(_decode_one,
                                   [(i, 0, n, m_a, m_b,
                                     (a_all[i * n:(i + 1) * n].tolist(),
                                      b_all[i * n:(i + 1) * n].tolist()))
                                    for i in range(n_blocks)]))
            wall = time.perf_counter() - t0
            with jl.open("a", encoding="utf-8", buffering=1) as fh:
                for r in recs:
                    fh.write(json.dumps({"seg": seg, "N": n, **r}) + "\n")
            nb = len(recs)
            nf = sum(0 if r["exact_full"] else 1 for r in recs)
            nu = sum(1 for r in recs if r["undetected"])
            e_l = sum(r["L_A"] + r["L_B"] + r.get("extra", 0) for r in recs) / nb
            # H from R1 T2-1M P1 scalars (frozen)
            from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
                read_p1_scalars as _rs,
            )
            s = _rs()["T2-1M"]
            fer = nf / nb
            denom = n * s["H_AB"]
            kept = n * s["H_A"] - e_l
            f_p = (e_l + TAG_BITS + kept * fer) / denom
            rows.append({"seg": seg, "N": n, "gap": gap, "margin": margin,
                         "m_A": m_a, "m_B": m_b, "blocks": nb, "offset_ps": int(off),
                         "failures": nf, "undetected": nu, "E_L": e_l,
                         "FER_exact": fer, "f_expected": f_p,
                         "backend": "g2-twolevel-real", "wall_s": wall})
            print(seg, f"N={n}", f"fail {nf}/{nb} E_L={e_l:.0f} f={f_p:.3f}",
                  flush=True)
    (root / "g3_summary.json").write_text(json.dumps(rows, indent=2),
                                          encoding="utf-8")
    print(json.dumps(rows, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--ns", default=None)
    ap.add_argument("--gaps", default=None)
    ap.add_argument("--margins", default=None)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if args.real:
        run_real_main(args)
        return
    if not args.full:
        raise SystemExit("G-2 runs only with --full")
    import concurrent.futures as cf
    import pickle
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        load_train_table,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (  # noqa: E402
        build_peg_code,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        read_p1_scalars,
        wilson_upper,
    )

    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    t = np.asarray(load_train_table("T2-1M"), dtype=np.float64)
    pa = (t.sum(axis=1) / t.sum()).tolist()
    hA = h2(P)
    hB = P * h2(PM_COND)
    scalars = read_p1_scalars()["T2-1M"]
    jl = root / "blocks_g2.jsonl"
    if jl.exists():
        raise SystemExit(f"refusing to overwrite {jl}")
    rows = []
    ns = [int(x) for x in args.ns.split(",")] if args.ns else list(NS)
    gaps = [float(x) for x in args.gaps.split(",")] if args.gaps else list(GAPS)
    margins = [float(x) for x in args.margins.split(",")] if args.margins else list(MARGINS)
    for n in ns:
        for gap in gaps:
            m_a = min(n - 1, max(1, int(math.ceil(n * (hA + gap)))))
            HA = build_peg_code(n=n, m=m_a, variable_degree=3).parity_check_matrix
            for margin in margins:
                m_b = min(n - 1, max(1, int(math.ceil(n * hB * margin))))
                HB = build_peg_code(n=n, m=m_b, variable_degree=3).parity_check_matrix
                payload = pickle.dumps((HA, HB, pa))
                t0 = time.perf_counter()
                with cf.ProcessPoolExecutor(max_workers=WORKERS,
                                            initializer=_worker_init,
                                            initargs=(payload,)) as ex:
                    recs = list(ex.map(_decode_one,
                                       [(b, SEED, n, m_a, m_b) for b in range(B)]))
                wall = time.perf_counter() - t0
                with jl.open("a", encoding="utf-8", buffering=1) as fh:
                    for r in recs:
                        fh.write(json.dumps({"n": n, "gap": gap,
                                             "margin": margin, **r}) + "\n")
                nb = len(recs)
                nf = sum(0 if r["exact_full"] else 1 for r in recs)
                nu = sum(1 for r in recs if r["undetected"])
                e_l = sum(r["L_A"] + r["L_B"] + r.get("extra", 0)
                          for r in recs) / nb
                fer = nf / nb
                denom = n * scalars["H_AB"]
                kept = n * scalars["H_A"] - e_l
                f_p = (e_l + TAG_BITS + kept * fer) / denom
                rows.append({"N": n, "gap_A": gap, "margin_B": margin,
                             "m_A": m_a, "m_B": m_b, "blocks": nb, "failures": nf, "undetected": nu,
                             "E_L": e_l,
                             "E_A": sum(r["L_A"] for r in recs) / nb,
                             "E_B": sum(r["L_B"] + r.get("extra", 0)
                                        for r in recs) / nb,
                             "FER_exact": fer,
                             "FER_wilson_upper95": wilson_upper(nf, nb),
                             "f_expected": f_p, "backend": "g2-twolevel",
                             "wall_s": wall,
                             "R14_ideal_A": n * hA,
                             "R14_ideal_B": n * hB})
                print(f"N={n} gap={gap} margin={margin}: fail {nf}/{nb} "
                      f"E_L={e_l:.0f} f={f_p:.3f}", flush=True)
    (root / "g2_summary.json").write_text(json.dumps(rows, indent=2),
                                          encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
