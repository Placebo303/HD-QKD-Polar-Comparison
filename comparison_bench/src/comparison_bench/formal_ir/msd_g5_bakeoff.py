"""G-5 methods bake-off (G5_PACKET.md): level-A methods Polar-SCL8 / RA-LDPC /
PEG-LDPC with SHARED model LLRs P(x0|b) (isolates code effect) + shared level-B
(margin ladder) + rebuild. Parametric ternary synthetic. Full-symbol f.
Pooled x12. B=300.
R14 ideals per row. Polar = same-data Polar control column (syndrome |F|).
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy import sparse

P = 0.2376
PM_ABS = 0.00138
PM_COND = PM_ABS / P
POLAR_DISC = (0.85, 0.88)
RA_GAPS = (0.08, 0.10, 0.12)
PEG_GAPS = (0.15,)
MARGINS = (2.5, 3.0)
B = 300
K2 = 64
K_A = 400
SEED = 20267400
TAG_BITS = 64
WORKERS = 12
SIBLING_ROOT = "D:/Code/HD-QKD_Polar_Release"


def h2(x: float) -> float:
    return -(x * math.log2(x) + (1 - x) * math.log2(1 - x))


_W = {}


def _worker_init(payload):
    import pickle
    import sys
    if SIBLING_ROOT not in sys.path:
        sys.path.insert(0, SIBLING_ROOT)
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
        make_bp_decoder as _mbp,
    )
    dense_a, kind_a, hb_mat, pa_l, info_idx = pickle.loads(payload)
    _W["A"] = dense_a
    _W["kind_A"] = kind_a
    _W["HB"] = hb_mat
    _W["pa"] = np.asarray(pa_l)
    _W["_mbp"] = _mbp
    _W["info_idx"] = None if info_idx is None else np.asarray(info_idx)
    if kind_a == "polar":
        from low_dim_opt.core import polar_core as _P
        _W["_P"] = _P


def _decode_one(args) -> dict:
    blk, seed, n = args[:3]
    real_pair = args[3] if len(args) > 3 else None
    import numpy as _np
    pa_l = _W["pa"]
    if real_pair is not None:
        alice = _np.asarray(real_pair[0], dtype=_np.int64)
        bob = _np.asarray(real_pair[1], dtype=_np.int64)
    else:
        rng = _np.random.default_rng(seed + blk)
        aks = _np.arange(1024)
        a = rng.choice(aks, size=n, p=pa_l)
        u = rng.random(size=n)
        e = _np.where(u < 1 - P, 0, _np.where(u < 1 - PM_ABS, 1, 1023)).astype(_np.int64)
        alice = a.astype(_np.int64)
        bob = ((a + e) % 1024).astype(_np.int64)
    xt = (alice & 1).astype(_np.uint8)
    # shared model LLRs P(x0|b)
    lik0, likp, likm = 1 - P, P - PM_ABS, PM_ABS
    a_cand = _np.stack([(bob - 1) % 1024, bob, (bob + 1) % 1024], axis=0)
    w = _np.stack([likm * pa_l[(bob - 1) % 1024], lik0 * pa_l[bob],
                   likp * pa_l[(bob + 1) % 1024]], axis=0)
    w = w / w.sum(axis=0, keepdims=True)
    p1 = (w * ((a_cand & 1).astype(float))).sum(axis=0)
    kind = _W["kind_A"]
    l_a = 0
    a_extra = 0
    if kind == "polar":
        _P = _W["_P"]
        n_log = int(math.log2(n))
        llr = _np.log(np.maximum(1 - p1, 1e-300) / np.maximum(p1, 1e-300))
        info = _W["info_idx"]
        mask = _np.zeros(n, dtype=_np.uint8)
        mask[info] = 1
        fv = _np.zeros(n, dtype=_np.uint8)
        ua = _P.polar_encode(xt.astype(_np.int8), n_log)
        l_a = n - len(info)
        fv[:] = 0
        # disclose u[F]
        frz = _np.where(mask == 0)[0]
        fv[frz] = ua[frz]
        uh = _P.scl_decode_batch(llr.reshape(1, -1), mask,
                                 fv.reshape(1, -1), n_log, 8)
        xh = _P.polar_encode(np.asarray(uh[0]).astype(np.int8), n_log).astype(_np.uint8)
        a_ok = bool(_np.array_equal(xh, xt))
        a_syn_ok = a_ok
    else:
        HA = _W["A"]
        HAd = _np.asarray(HA.toarray(), dtype=_np.uint8)
        base = (p1 > 0.5).astype(_np.uint8)
        ch = _np.minimum(p1, 1 - p1).copy()
        syn_a = (HAd @ xt) % 2
        delta = _np.bitwise_xor(syn_a, (HAd @ base) % 2)
        dec = _W["_mbp"](parity_check_matrix=HA, error_channel=ch.copy(),
                         max_iter=200)
        err = _np.asarray(dec.decode(delta.copy())).astype(_np.uint8)
        xh = _np.bitwise_xor(base, err)
        l_a = int(HA.shape[0])
        a_ok = bool(_np.array_equal((HAd @ xh) % 2, syn_a)) and bool(_np.array_equal(xh, xt))
        a_syn_ok = bool(_np.array_equal((HAd @ xh) % 2, syn_a))
        a_extra = 0
        if not a_ok:
            w8 = _np.log((1 - _np.maximum(ch, 1e-300)) / _np.maximum(ch, 1e-300))
            weak = _np.argsort(w8, kind="stable")[:K_A]
            base[weak] = xt[weak]
            a_extra = K_A
            delta2 = _np.bitwise_xor(syn_a, (HAd @ base) % 2)
            dec2 = _W["_mbp"](parity_check_matrix=HA, error_channel=ch.copy(),
                              max_iter=200)
            err2 = _np.asarray(dec2.decode(delta2.copy())).astype(_np.uint8)
            xh = _np.bitwise_xor(base, err2)
            a_ok = bool(_np.array_equal((HAd @ xh) % 2, syn_a)) and bool(_np.array_equal(xh, xt))
    if not a_ok:
        return {"block": blk, "a_ok": False, "exact_full": False,
                "undetected": False, "L_A": l_a, "L_B": 0, "extra": a_extra}
    # --- shared level B (PEG-BP margin ladder + K2 + rebuild) ---
    HB = _W["HB"]
    HBd = _np.asarray(HB.toarray(), dtype=_np.uint8)
    yb = (bob & 1).astype(_np.uint8)
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
        return {"block": blk, "a_ok": True, "exact_full": False,
                "undetected": bool(b_syn_ok), "L_A": l_a,
                "L_B": int(HB.shape[0]), "extra": extra}
    sgn = _np.bitwise_xor(rec1, _np.bitwise_xor((bob >> 1) & 1, xh)).astype(_np.int64)
    delta_rec = _np.where(~marked, 0, _np.where(sgn == 0, 1, 1023)).astype(_np.int64)
    arec = ((bob - delta_rec) % 1024).astype(_np.int64)
    full = bool(_np.array_equal(arec, alice))
    return {"block": blk, "a_ok": True, "exact_full": full,
            "undetected": bool((not full)), "L_A": l_a,
            "L_B": int(HB.shape[0]), "extra": extra}


def run_real_main(args) -> None:
    """G-6 execution (conditionally authorized): winner RA-q5-gap0.08/m3.0
    (+N=16384 control at same settings) on 4dB/10dB clean + 0dB retest."""
    import concurrent.futures as cf
    import pickle
    import sys
    if SIBLING_ROOT not in sys.path:
        sys.path.insert(0, SIBLING_ROOT)
    from comparison_bench.src.comparison_bench.io import align_wrapper as aw
    from comparison_bench.src.comparison_bench.io.ttbin_compat import (
        install_timetagger_alias,
    )
    from comparison_bench.src.comparison_bench.cli.probes_closed import (  # noqa: E402
        m0_realframe_runner as _m0,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        load_train_table,
        read_p1_scalars,
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
        a_all = sa[keep].astype(np.int64)
        b_all = sb[keep].astype(np.int64)
        return a_all, b_all, int(offset)

    segs = {
        "4dB": "D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_4dB_2026-01-23_174758.1.ttbin",
        "10dB": "D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_10dB_2026-01-23_174842.1.ttbin",
        "0dB": "D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_0dB_2026-01-23_174534.1.ttbin",
    }
    t = np.asarray(load_train_table("T2-1M"), dtype=np.float64)
    pa = (t.sum(axis=1) / t.sum()).tolist()
    hA = h2(P)
    hB = P * h2(PM_COND)
    scalars = read_p1_scalars()["T2-1M"]
    jl = root / "blocks_g6.jsonl"
    rows = []

    def ra_matrix_l(n, m, q=5, seed=0):
        k = n - m
        rng = np.random.default_rng(seed)
        rows_, cols_ = [], []
        order = rng.permutation(m * ((q * k) // m + 1))[:q * k]
        for j in range(k):
            for tt in range(q):
                rows_.append(int(order[(j * q + tt) % len(order)] % m))
                cols_.append(j)
        for i in range(m):
            rows_.append(i)
            cols_.append(k + i)
            if i > 0:
                rows_.append(i)
                cols_.append(k + i - 1)
        return sparse.csr_matrix((np.ones(len(rows_), dtype=np.uint8), (rows_, cols_)),
                                 shape=(m, n))

    from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (  # noqa: E402
        build_peg_code,
    )
    for seg, path in segs.items():
        a_all, b_all, off = load_seg(path)
        for n in (32768, 16384):
            n_blocks = len(a_all) // n
            if n_blocks < 1:
                print(f"{seg} N={n}: SKIP (only {len(a_all)} pairs)", flush=True)
                rows.append({"seg": seg, "N": n, "skipped": True,
                             "pairs": int(len(a_all))})
                continue
            # winner config: RA-q5-gap0.08/margin3.0
            m_a = min(n - 1, max(1, int(math.ceil(n * (hA + 0.08)))))
            HA = ra_matrix_l(n, m_a)
            m_b = min(n - 1, max(1, int(math.ceil(n * hB * 3.0))))
            HB = build_peg_code(n=n, m=m_b, variable_degree=3).parity_check_matrix
            payload = pickle.dumps((HA, "ldpc", HB, pa, None))
            t0 = time.perf_counter()
            with cf.ProcessPoolExecutor(max_workers=WORKERS,
                                        initializer=_worker_init,
                                        initargs=(payload,)) as ex:
                recs = list(ex.map(_decode_one,
                                   [(i, 0, n,
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
            fer = nf / nb
            denom = n * scalars["H_AB"]
            kept = n * scalars["H_A"] - e_l
            f_p = (e_l + TAG_BITS + kept * fer) / denom
            rows.append({"seg": seg, "N": n, "gap": 0.08, "margin": 3.0,
                         "m_A": m_a, "m_B": m_b, "blocks": nb,
                         "offset_ps": int(off), "failures": nf,
                         "undetected": nu, "E_L": e_l, "FER_exact": fer,
                         "FER_wilson_upper95": wilson_upper(nf, nb),
                         "f_expected": f_p, "backend": "g6-RA-real",
                         "wall_s": wall})
            print(seg, f"N={n}", f"fail {nf}/{nb} f={f_p:.3f}", flush=True)
    (root / "g6_summary.json").write_text(json.dumps(rows, indent=2),
                                          encoding="utf-8")
    print(json.dumps(rows, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--ns", default="16384")
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if args.real:
        run_real_main(args)
        return
    if not args.full:
        raise SystemExit("G-5 runs only with --full")
    import concurrent.futures as cf
    import pickle
    import sys
    if SIBLING_ROOT not in sys.path:
        sys.path.insert(0, SIBLING_ROOT)
    from low_dim_opt.core import de_frozen as _D
    from low_dim_opt.core import polar_core as _P
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        load_train_table,
        read_p1_scalars,
        wilson_upper,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (  # noqa: E402
        build_peg_code,
    )

    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    t = np.asarray(load_train_table("T2-1M"), dtype=np.float64)
    pa = (t.sum(axis=1) / t.sum()).tolist()
    hA = h2(P)
    hB = P * h2(PM_COND)
    scalars = read_p1_scalars()["T2-1M"]
    jl = root / "blocks_g5.jsonl"
    if jl.exists():
        raise SystemExit(f"refusing to overwrite {jl}")

    def ra_matrix(n, m, q, seed):
        k = n - m
        rng = np.random.default_rng(seed)
        rows, cols = [], []
        order = rng.permutation(m * ((q * k) // m + 1))[:q * k]
        for j in range(k):
            for tt in range(q):
                rows.append(int(order[(j * q + tt) % len(order)] % m))
                cols.append(j)
        for i in range(m):
            rows.append(i)
            cols.append(k + i)
            if i > 0:
                rows.append(i)
                cols.append(k + i - 1)
        return sparse.csr_matrix((np.ones(len(rows), dtype=np.uint8), (rows, cols)),
                                 shape=(m, n))

    rows = []
    ns = [int(x) for x in args.ns.split(",")]
    for n in ns:
        n_log = int(math.log2(n))
        assert 2 ** n_log == n
        # A-method configs: (kind, disclosure, builder)
        cfgs = []
        for disc in POLAR_DISC:
            Kinfo = n - int(math.ceil(n * disc))
            order = _D.de_order_from_population(
                _D.de_llr_populations(n_log, P, n_samples=2048, seed=1))
            info = np.asarray(sorted(order[:Kinfo]), dtype=np.int64)
            cfgs.append((f"polar-SCL8-{disc}", "polar", None, info))
        for gap in RA_GAPS:
            m = min(n - 1, max(1, int(math.ceil(n * (hA + gap)))))
            cfgs.append((f"RA-q5-gap{gap}", "ldpc", ra_matrix(n, m, 5, 0), None))
        for gap in PEG_GAPS:
            m = min(n - 1, max(1, int(math.ceil(n * (hA + gap)))))
            cfgs.append((f"PEG-dv3-gap{gap}", "ldpc",
                         build_peg_code(n=n, m=m, variable_degree=3).parity_check_matrix,
                         None))
        for margin in MARGINS:
            m_b = min(n - 1, max(1, int(math.ceil(n * hB * margin))))
            HB = build_peg_code(n=n, m=m_b, variable_degree=3).parity_check_matrix
            for tag, kind, mat, info in cfgs:
                import pickle as _pk
                payload = pickle.dumps((mat, kind, HB, pa,
                                        None if info is None else info.tolist()))
                t0 = time.perf_counter()
                with cf.ProcessPoolExecutor(max_workers=WORKERS,
                                            initializer=_worker_init,
                                            initargs=(payload,)) as ex:
                    # polar info_idx travels in payload; no post-init attach
                    recs = list(ex.map(_decode_one,
                                       [(b, SEED, n) for b in range(B)]))
                wall = time.perf_counter() - t0
                with jl.open("a", encoding="utf-8", buffering=1) as fh:
                    for r in recs:
                        fh.write(json.dumps({"n": n, "A": tag, "margin": margin,
                                             **r}) + "\n")
                nb = len(recs)
                nf = sum(0 if r["exact_full"] else 1 for r in recs)
                nu = sum(1 for r in recs if r["undetected"])
                e_l = sum(r["L_A"] + r["L_B"] + r.get("extra", 0) for r in recs) / nb
                fer = nf / nb
                denom = n * scalars["H_AB"]
                kept = n * scalars["H_A"] - e_l
                f_p = (e_l + TAG_BITS + kept * fer) / denom
                rows.append({"N": n, "A_method": tag, "margin_B": margin,
                             "blocks": nb, "failures": nf, "undetected": nu,
                             "E_L": e_l, "FER_exact": fer,
                             "FER_wilson_upper95": wilson_upper(nf, nb),
                             "f_expected": f_p, "backend": "g5-bakeoff",
                             "wall_s": wall,
                             "R14_ideal_A": n * hA,
                             "R14_ideal_B": n * hB})
                print(f"N={n} {tag} m{margin}: fail {nf}/{nb} f={f_p:.3f}", flush=True)
    (root / "g5_summary.json").write_text(json.dumps(rows, indent=2),
                                          encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
