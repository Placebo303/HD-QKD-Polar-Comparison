"""D-1 genie-diff self-check (pure synthetic, zero real data beyond the
already-read TRAIN tables used to fit g): channel pairs generated from the
shift-invariant diff model g itself (a ~ P_fit(a), delta ~ g, b = a+delta);
prior = SAME g (genie). MSD + NB must succeed near H_g rates at B>=300.
If either fails, the diff-prior path has an implementation defect and ALL
smoothed-prior negatives stay void until fixed.
R14: single-layer design here is the diff model itself: H_g measured below;
ideal disclosure = N*H_g; actual m = N*(h+gap) with M2 gap rule.
"""

from __future__ import annotations

import argparse
import functools
import json
import math
import time
from pathlib import Path

import numpy as np

N_MSD = 16384
N_NB = 1024
GAP = 2000 / 16384
K = 400
B = 300
SEED = 20266200
TAG_BITS = 64
WORKERS = 12

_W = {}


def fit_g(counts: np.ndarray):
    tot = counts.sum()
    pa = counts.sum(axis=1) / tot
    d = (np.arange(1024)[None, :] - np.arange(1024)[:, None]) % 1024
    g = np.bincount(d.ravel(), weights=counts.ravel(), minlength=1024)
    return pa / pa.sum(), g / g.sum()


def gen_pairs(pa, g, n, rng):
    aks = np.arange(1024)
    a = rng.choice(aks, size=n, p=pa)
    delta = rng.choice(aks, size=n, p=g)
    return a.astype(np.int64), ((a + delta) % 1024).astype(np.int64)


def _worker_init(payload):
    import pickle
    from comparison_bench.src.comparison_bench.formal_ir.msd_m4_nb_marginal import (  # noqa: E402
        derive_bundle,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        v80_s2c_campaign as _s2c,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v10_peg as _peg,
    )
    from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (  # noqa: E402
        GF2mField as _GF,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v10_fftqspa as _qq,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v28 as _v28,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        v80_b2f_campaign as _b2f,
    )
    pseudo, triples = pickle.loads(payload)
    _W["bundle"] = _s2c.bind_empirical_bundle(derive_bundle(pseudo))
    field = _GF.create(32)
    _W["field"] = field
    _W["dense"] = {}
    for key, m in (("base", 200), ("full", 208)):
        sub = [(r, c, v) for r, c, v in triples if int(r) < m]
        _W["dense"][key] = _peg.sparse_to_dense(sub, N_NB, m, field)
    _W["_qq"], _W["_v28"], _W["_b2f"], _W["_s2c"] = _qq, _v28, _b2f, _s2c


def _nb_one(args) -> dict:
    blk, seed, pa_l, g_l = args
    import numpy as _np
    rng = _np.random.default_rng(seed + blk)
    aks = _np.arange(1024)
    a = rng.choice(aks, size=N_NB, p=_np.asarray(pa_l))
    b = (a + rng.choice(aks, size=N_NB, p=_np.asarray(g_l))) % 1024
    alice, bob = a.astype(_np.int64), b.astype(_np.int64)
    bundle, field = _W["bundle"], _W["field"]
    dense = _W["dense"]
    _qq, _v28, _b2f, _s2c = _W["_qq"], _W["_v28"], _W["_b2f"], _W["_s2c"]
    x = alice & 31
    y = bob & 31
    outs = []
    for key in ("base", "full"):
        if key == "full" and outs and bool(outs[0]["exact_match"]):
            break
        prior = _s2c.center_rows_prior(_b2f.marginal_prior_l2(bundle, bob), y)
        sxx = _qq.syndrome_of(field, dense[key], x.tolist())
        res = _v28.decode_error_domain_posterior(field, y.tolist(), dense[key],
                                                 sxx, prior, 300)
        xh = res.get("x_hat")
        ex = xh is not None and bool(_np.array_equal(_np.asarray(xh), x))
        outs.append({"exact_match": ex,
                     "reconstruction_ok": bool(res.get("reconstruction_ok", False))})
    ok = bool(outs[0]["exact_match"]) or (len(outs) > 1 and bool(outs[1]["exact_match"]))
    rok = bool(outs[-1].get("reconstruction_ok", False))
    umm = "NA"
    return {"block": blk, "exact_u2": ok,
            "undetected": bool((not ok) and rok),
            "rescued": len(outs) > 1,
            "L_u2": 5 * (200 if len(outs) == 1 else 208), "u1_mm": umm}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--proxy-root", required=True)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("D-1 runs only with --full")
    import pickle
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        build_conditional_prior_model as _bcp,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primeb_mixed import (  # noqa: E402
        build_mixed_point,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        plane_conditional_entropies,
        read_p1_scalars,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
        make_bp_decoder,
    )
    from comparison_bench.src.comparison_bench.cli import (  # noqa: E402
        p1_stage1_runner as _p1,
    )

    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    proot = Path(args.proxy_root)
    th_a = np.asarray(np.load(proot / "T2-1M_tier_tables.npz")["half_a"])
    assert th_a.shape == (1024, 1024) and th_a.sum() > 100000, "proxy tables"
    pa_fit, g_fit = fit_g(th_a)
    # H_g (zero-decode): E over generating distribution
    hb = -(g_fit[g_fit > 0] * np.log2(g_fit[g_fit > 0])).sum()
    aks = np.arange(1024)
    joint = pa_fit[:, None] * g_fit[(aks[None, :] - aks[:, None]) % 1024]
    joint = joint / joint.sum()
    pseudo = joint * th_a.sum()
    model = _bcp(pseudo, encoding="NATURAL", order="LSB_FIRST")
    h = plane_conditional_entropies(pseudo)
    print("H_g(diff) =", round(float(hb), 4), "b/sym; plane h sum =",
          round(float(sum(h)), 4), flush=True)
    matrices, factories, _, m_list = build_mixed_point(N_MSD, h, 2000, 32, 256)
    l_base = int(sum(m_list))
    bp = functools.partial(make_bp_decoder, max_iter=200)
    rng = np.random.default_rng(SEED)
    jl = root / "blocks_d1.jsonl"
    if jl.exists():
        jl.unlink()
    # MSD arm (serial, fast blocks)
    n_fail = n_und = n_res = n_vw = 0
    t0 = time.perf_counter()
    from comparison_bench.src.comparison_bench.formal_ir.msd_s1_proxy import (  # noqa: E402
        _decode_msd_block,
    )
    with jl.open("a", encoding="utf-8", buffering=1) as fh:
        for blk in range(B):
            alice, bob = gen_pairs(pa_fit, g_fit, N_MSD, rng)
            r = _decode_msd_block(alice, bob, model, matrices, factories, K, bp)
            n_fail += 0 if r["exact_ok"] else 1
            n_und += 1 if r["undetected"] else 0
            n_res += 1 if r["rescued"] else 0
            n_vw += r["valid_wrong_stages"]
            fh.write(json.dumps({"arm": "msd", "block": blk,
                                 "exact_ok": bool(r["exact_ok"]),
                                 "undetected": bool(r["undetected"])}) + "\n")
    msd_wall = time.perf_counter() - t0
    print(f"MSD genie-diff: fail {n_fail}/{B} und {n_und} vw {n_vw}", flush=True)
    # NB arm (pooled; frozen A208 construction — same code family as S-5)
    import concurrent.futures as cf
    pinned = _p1.construct_and_pin("P1S1-R1", _p1.PRODUCTION_CONSTRUCT["P1S1-R1"],
                                   _p1.production_rank_fn)
    payload = pickle.dumps((pseudo, pinned["full"]["triples"]))
    t0 = time.perf_counter()
    with cf.ProcessPoolExecutor(max_workers=WORKERS,
                                initializer=_worker_init,
                                initargs=(payload,)) as ex:
        recs = list(ex.map(_nb_one, [(b, SEED + 1, pa_fit.tolist(), g_fit.tolist())
                                     for b in range(B)]))
    nb_wall = time.perf_counter() - t0
    with jl.open("a", encoding="utf-8", buffering=1) as fh:
        for r in recs:
            fh.write(json.dumps({"arm": "nb", **r}) + "\n")
    nf = sum(0 if r["exact_u2"] else 1 for r in recs)
    nu = sum(1 for r in recs if r["undetected"])
    print(f"NB genie-diff: fail {nf}/{B} und {nu}", flush=True)
    out = {"H_g": float(hb), "msd": {"failures": n_fail, "undetected": n_und,
                                     "valid_wrong": n_vw, "blocks": B,
                                     "wall_s": msd_wall, "L_base": l_base},
           "nb": {"failures": nf, "undetected": nu, "blocks": B, "wall_s": nb_wall},
           "verdict": "PASS" if (n_fail == 0 and nf == 0) else "FAIL"}
    (root / "d1_summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
