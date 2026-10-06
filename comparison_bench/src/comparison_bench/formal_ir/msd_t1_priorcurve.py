"""T-1 prior-mass curve (T1_PACKET.md scope): fixed S-3''' chain, prior tables
from half_b subsamples (1/4, 1/2, 1x) + full TRAIN (2x). Channel fixed Tier1
bootstrap (isolates prior mass). Pooled x12. Full-symbol metric (R11).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
    read_p1_scalars,
    wilson_upper,
)

N = 1024
M_U2, R_U2 = 224, 232
FRACS = (0.25, 0.5, 1.0, "full")
B = 60
SEED = 20264900
TAG_BITS = 64
WORKERS = 12

_W = {}


def _worker_init(frac: float, triples):
    from comparison_bench.src.comparison_bench.formal_ir.msd_s1_proxy import (  # noqa: E402
        load_tier_pairs,
    )
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
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        build_conditional_prior_model as _bcp,
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
    root = Path("workspace/s1_proxy/s1_20261006")
    pa, pb = load_tier_pairs(root, "T2-1M", "half_a")
    z = np.load(root / "T2-1M_tier_pairs.npz")
    bh_a = np.asarray(z["a_half_b"], dtype=np.int64)
    bh_b = np.asarray(z["b_half_b"], dtype=np.int64)
    if frac == "full":
        from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
            load_train_table as _ltt,
        )
        t = _ltt("T2-1M")
    else:
        rng = np.random.default_rng(20264999)
        sub = rng.choice(bh_a.size, size=int(bh_a.size * frac), replace=False)
        t = np.zeros((1024, 1024), dtype=np.float64)
        np.add.at(t, (bh_a[sub], bh_b[sub]), 1)
    _W["bundle"] = _s2c.bind_empirical_bundle(derive_bundle(t))
    _W["model"] = _bcp(t, encoding="NATURAL", order="LSB_FIRST")
    field = _GF.create(32)
    _W["field"] = field
    # FIXED code = S-3''' optimum (fresh m=224 + nested 232 rescue)
    _W["dense"] = {}
    for key, m in (("base", 224), ("full", 232)):
        sub = [(r, c, v) for r, c, v in triples if int(r) < m]
        _W["dense"][key] = _peg.sparse_to_dense(sub, N, m, field)
    _W["groups"] = _sg(N, 102)
    _W["mat_u1"] = _spc(_W["groups"], N)
    _W["pa"], _W["pb"] = pa, pb
    _W["_qq"], _W["_v28"], _W["_b2f"], _W["_s2c"] = _qq, _v28, _b2f, _s2c
    _W["_GML"] = _GML
    _W["frac"] = frac


def _decode_one(args) -> dict:
    import numpy as _np

    blk, seed = args
    pa, pb = _W["pa"], _W["pb"]
    rng = _np.random.default_rng(seed + blk)
    pick = rng.choice(pa.size, size=N, replace=True)
    alice = pa[pick].astype(_np.int64)
    bob = pb[pick].astype(_np.int64)
    model, bundle, field = _W["model"], _W["bundle"], _W["field"]
    dense, groups, mat_u1 = _W["dense"], _W["groups"], _W["mat_u1"]
    _qq, _v28, _b2f, _s2c = _W["_qq"], _W["_v28"], _W["_b2f"], _W["_s2c"]
    H1 = _np.asarray(mat_u1.toarray(), dtype=_np.uint8)
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
                     "x_hat": (_np.asarray(xh, dtype=_np.int64).tolist()
                               if xh is not None else None),
                     "reconstruction_ok": bool(res.get("reconstruction_ok", False))})
    u2ok = bool(outs[0]["exact_match"]) or (len(outs) > 1 and bool(outs[1]["exact_match"]))
    l_u2 = 224 if len(outs) == 1 else 232
    if not u2ok:
        return {"block": blk, "u2_ok": False, "exact_full": False,
                "undetected": False, "L_u2": 5 * l_u2, "L_u1": 0, "u1_extra": 0}
    _xh = outs[0]["x_hat"] if outs[0]["exact_match"] else outs[1]["x_hat"]
    u2hat = _np.asarray(_xh, dtype=_np.int64)
    low5 = [((u2hat >> i) & 1).astype(_np.uint8) for i in range(5)]
    high_rec = []
    u1_ok, u1_extra, u1_syn_ok = True, 0, True
    rok_u2 = bool(outs[-1].get("reconstruction_ok", False))
    for bit in range(5, 10):
        prev = _np.stack(low5 + high_rec, axis=0)
        q = model.query(bit, bob, prev)
        base = (q.p_one > 0.5).astype(_np.uint8)
        truth = ((alice >> bit) & 1).astype(_np.uint8)
        syn = (H1 @ truth) % 2
        chh = _np.minimum(q.p_one, 1 - q.p_one).copy()
        dec = _W["_GML"](groups, "spc", chh, 0)
        rec = _np.bitwise_xor(base, dec.decode(_np.bitwise_xor(syn, (H1 @ base) % 2)))
        syn_ok_first = bool(_np.array_equal((H1 @ rec) % 2, syn))
        if not (syn_ok_first and bool(_np.array_equal(rec, truth))):
            w = _np.log((1 - _np.maximum(chh, 1e-300)) / _np.maximum(chh, 1e-300))
            weak = _np.argsort(w, kind="stable")[:16]
            base[weak] = truth[weak]
            u1_extra += 16
            rec2 = base.copy()
            if not bool(_np.array_equal(rec2, truth)):
                u1_ok = False
                u1_syn_ok = bool(syn_ok_first)
                break
            rec = rec2
        high_rec.append(rec.astype(_np.uint8))
    full = u1_ok
    und = (not full) and rok_u2 and u1_syn_ok
    return {"block": blk, "u2_ok": True, "exact_full": bool(full),
            "undetected": bool(und), "L_u2": 5 * l_u2,
            "L_u1": 5 * int(mat_u1.shape[0]), "u1_extra": u1_extra}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("T-1 runs only with --full")
    import concurrent.futures as cf

    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    scalars = read_p1_scalars()["T2-1M"]
    jl = root / "blocks_t1.jsonl"
    if jl.exists():
        jl.unlink()
    rows = []
    from comparison_bench.src.comparison_bench.formal_ir.msd_s3triple_u2grid import (  # noqa: E402
        build_point as _bp224,
    )
    triples224 = _bp224(224, 20263835)["triples"]
    for frac in FRACS:
        t0 = time.perf_counter()
        with cf.ProcessPoolExecutor(max_workers=WORKERS,
                                    initializer=_worker_init,
                                    initargs=(frac, triples224)) as ex:
            recs = list(ex.map(_decode_one, [(b, SEED) for b in range(B)]))
        wall = time.perf_counter() - t0
        with jl.open("a", encoding="utf-8", buffering=1) as fh:
            for r in recs:
                fh.write(json.dumps({"frac": str(frac), **r}) + "\n")
        nb = len(recs)
        nf = sum(0 if r["exact_full"] else 1 for r in recs)
        nu = sum(1 for r in recs if r["undetected"])
        e_l = sum(r["L_u2"] + r["L_u1"] + r.get("u1_extra", 0) for r in recs) / nb
        fer = nf / nb
        denom = N * scalars["H_AB"]
        kept = N * scalars["H_A"] - e_l
        f_p = (e_l + TAG_BITS + kept * fer) / denom
        rows.append({"prior_frac": str(frac), "blocks": nb, "failures": nf,
                     "undetected": nu, "E_L": e_l, "FER_exact": fer,
                     "FER_wilson_upper95": wilson_upper(nf, nb),
                     "f_expected": f_p, "source": "T2-1M", "N": N,
                     "backend": "t1-prior-curve", "wall_s": wall})
        print(f"frac={frac}: fail {nf}/{nb} E_L={e_l:.0f} f={f_p:.3f}", flush=True)
    (root / "t1_summary.json").write_text(json.dumps(rows, indent=2),
                                          encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
