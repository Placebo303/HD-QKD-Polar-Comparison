"""Z-1 rate-adaptive f(p) curve (EXPLORE): uniform rule gap 0.12 + margin 3.0
(RA-q5 level A) per p. Replaces voided H-4 fixed-rate curve.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy import sparse

N = 16384
PM_ABS = 0.00138
# Z-1 rule: gap 0.12 + margin 3.0 universal; ENSEMBLE branches on rate
# (pilot evidence): R>0.25 -> PEG-dv3 (RA-q5 threshold collapses at high rate:
# 293/300 + 33 und at p=0.05); R<=0.25 -> RA-q5 (verified low-rate winner).
# Matches M1 C0 gap; documents the rate-dependent ensemble choice.
GAP = 0.12
PS = (0.05, 0.10, 0.15, 0.20, 0.24, 0.28, 0.33)
B = 300
K = 400
SEED = 20267600
TAG_BITS = 64
WORKERS = 12

_W = {}


def h2(x: float) -> float:
    return -(x * math.log2(x) + (1 - x) * math.log2(1 - x))


def ra_matrix(n: int, m: int, q: int, seed: int):
    k = n - m
    rng = np.random.default_rng(seed)
    rows, cols = [], []
    # per-column DISTINCT rows (binary!): sample q rows per column directly.
    # Row balance is approximate (Poisson) rather than exact — documented.
    for j in range(k):
        rr = rng.choice(m, size=min(q, m), replace=False)
        for r in rr:
            rows.append(int(r))
            cols.append(j)
    for i in range(m):
        rows.append(i)
        cols.append(k + i)
        if i > 0:
            rows.append(i)
            cols.append(k + i - 1)
    mat = sparse.csr_matrix((np.ones(len(rows), dtype=np.uint8), (rows, cols)),
                            shape=(m, n))
    mat.data[:] = 1
    assert mat.max() <= 1
    return mat


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
    dense_a, dense_b, pa_l, pp = pickle.loads(payload)
    _W["HA"], _W["HB"] = dense_a, dense_b
    _W["pa"] = np.asarray(pa_l)
    _W["_mbp"] = _mbp
    _W["_GML"], _W["_spc"], _W["_sg"] = _GML, _spc, _sg
    _W["pp"] = pp


def _decode_one(args) -> dict:
    blk, seed = args
    import numpy as _np
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
        _syndrome as _syn,
    )
    HA, HB = _W["HA"], _W["HB"]
    pp, pa_l = _W["pp"], _W["pa"]
    p = pp["p"]
    pm_cond = pp["pm"]
    rng = _np.random.default_rng(seed + blk)
    aks = _np.arange(1024)
    a = rng.choice(aks, size=N, p=pa_l)
    u = rng.random(size=N)
    e = _np.where(u < 1 - p, 0, _np.where(u < 1 - p * pm_cond, 1, 1023)).astype(_np.int64)
    alice = a.astype(_np.int64)
    bob = ((a + e) % 1024).astype(_np.int64)
    # level A with model priors at operating p
    xt = (alice & 1).astype(_np.uint8)
    lik0, likp, likm = 1 - p, p * (1 - pm_cond), p * pm_cond
    a_cand = _np.stack([(bob - 1) % 1024, bob, (bob + 1) % 1024], axis=0)
    w = _np.stack([likm * pa_l[(bob - 1) % 1024], lik0 * pa_l[bob],
                   likp * pa_l[(bob + 1) % 1024]], axis=0)
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
    # level B (sign, margin 3.0 design point)
    yb = (bob & 1).astype(_np.uint8)
    marked = (xh != yb)
    b1 = ((bob >> 1) & 1).astype(_np.uint8)
    base1 = _np.where(marked, _np.bitwise_xor(b1, xh), b1).astype(_np.uint8)
    truth1 = ((alice >> 1) & 1).astype(_np.uint8)
    HBd = _np.asarray(HB.toarray(), dtype=_np.uint8)
    syn_b = (HBd @ truth1) % 2
    chb = _np.where(marked, pm_cond, 0.0)
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
        weak = _np.argsort(w, kind="stable")[:64]
        base1[weak] = truth1[weak]
        extra = 64
        rec1 = base1.copy()
        b_ok = bool(_np.array_equal(rec1, truth1))
    if not b_ok:
        return {"block": blk, "a_ok": True, "exact_full": False,
                "undetected": bool(b_syn_ok), "L_A": int(HA.shape[0]),
                "L_B": int(HB.shape[0]), "extra": extra}
    sgn = _np.bitwise_xor(rec1, _np.bitwise_xor((bob >> 1) & 1, xh)).astype(_np.int64)
    delta_rec = _np.where(~marked, 0, _np.where(sgn == 0, 1, 1023)).astype(_np.int64)
    arec = ((bob - delta_rec) % 1024).astype(_np.int64)
    full = bool(_np.array_equal(arec, alice))
    return {"block": blk, "a_ok": True, "exact_full": full,
            "undetected": bool((not full)), "L_A": int(HA.shape[0]),
            "L_B": int(HB.shape[0]), "extra": extra}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--ps", default=None)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("Z-1 runs only with --full")
    import concurrent.futures as cf
    import pickle
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
    scalars = read_p1_scalars()["T2-1M"]
    jl = root / "blocks_h4.jsonl"
    if jl.exists():
        raise SystemExit(f"refusing to overwrite {jl}")
    rows = []
    pss = [float(x) for x in args.ps.split(",")] if args.ps else list(PS)
    for p in pss:
        pm_cond = 0.0058
        m_a = min(N - 1, max(1, int(math.ceil(N * (h2(p) + GAP)))))
        rate = 1.0 - m_a / N
        if rate > 0.25:
            from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (  # noqa: E402
                build_peg_code as _bpeg,
            )
            HA = _bpeg(n=N, m=m_a, variable_degree=3).parity_check_matrix
            ens = "PEG-dv3"
        else:
            HA = ra_matrix(N, m_a, 5, 0)
            ens = "RA-q5"
        m_b = min(N - 1, max(1, int(math.ceil(N * p * h2(pm_cond) * 3.0))))
        HB = build_peg_code(n=N, m=m_b, variable_degree=3).parity_check_matrix
        payload = pickle.dumps((HA, HB, pa, {"p": p, "pm": pm_cond}))
        t0 = time.perf_counter()
        with cf.ProcessPoolExecutor(max_workers=WORKERS,
                                    initializer=_worker_init,
                                    initargs=(payload,)) as ex:
            recs = list(ex.map(_decode_one, [(b, SEED) for b in range(B)]))
        wall = time.perf_counter() - t0
        with jl.open("a", encoding="utf-8", buffering=1) as fh:
            for r in recs:
                fh.write(json.dumps({"p": p, "ensemble": ens, **r}) + "\n")
        nb = len(recs)
        nf = sum(0 if r["exact_full"] else 1 for r in recs)
        nu = sum(1 for r in recs if r["undetected"])
        e_l = sum(r["L_A"] + r["L_B"] + r.get("extra", 0) for r in recs) / nb
        fer = nf / nb
        # f vs channel's own H (not frozen P1): honest per-p efficiency
        import math as _m
        hab = h2(p) + p * h2(pm_cond)
        ha = 9.9976919099  # empirical pa fixed across p (P1 T2-1M)
        # use empirical H_A per p? symbols uniform over d here -> H_A = 10
        denom = N * hab
        kept = N * ha - e_l
        f_p = (e_l + TAG_BITS + kept * fer) / denom
        rows.append({"p": p, "ensemble": ens, "pm_cond": pm_cond, "N": N, "m_A": m_a, "m_B": m_b,
                     "blocks": nb, "failures": nf, "undetected": nu, "E_L": e_l,
                     "FER_exact": fer, "FER_wilson_upper95": wilson_upper(nf, nb),
                     "f_expected": f_p, "H_AB_channel": hab, "wall_s": wall})
        print(f"p={p} {ens}: fail {nf}/{nb} f={f_p:.3f}", flush=True)
    (root / "h4_backbone.json").write_text(json.dumps(rows, indent=2),
                                           encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
