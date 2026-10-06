"""T-4 multi-round incremental disclosure (T4_PACKET.md): fresh M=224+32
construction; step grid {(8,8),(8,16),(16,16)}; COLD full-matrix re-decode per
round (P1 F2 mirror); tune on seed-A (B=60), confirm best on seed-B (B=100,
sample-out calibration). u1 frozen. Full-symbol metric (R11). Pooled x12.
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
M_BASE = 224
M_MAX = 256
STEPS = ((8, 8), (8, 16), (16, 16))
B_TUNE = 60
B_CONFIRM = 100
SEED_A = 20265100
SEED_B = 20265200
TAG_BITS = 64
WORKERS = 12

_W = {}


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
    counts, triples, pa, pb, steps = pickle.loads(payload)
    _W["bundle"] = _s2c.bind_empirical_bundle(derive_bundle(counts))
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        build_conditional_prior_model as _bcp,
    )
    _W["model"] = _bcp(counts, encoding="NATURAL", order="LSB_FIRST")
    field = _GF.create(32)
    _W["field"] = field
    _W["dense"] = {}
    cum = M_BASE
    _W["rounds"] = [M_BASE]
    for s in steps:
        cum += s
        _W["rounds"].append(cum)
    for key, m in zip(("r0", "r1", "r2"), _W["rounds"]):
        sub = [(r, c, v) for r, c, v in triples if int(r) < m]
        _W["dense"][key] = _peg.sparse_to_dense(sub, N, m, field)
    _W["groups"] = _sg(N, 102)
    _W["mat_u1"] = _spc(_W["groups"], N)
    _W["pa"], _W["pb"] = pa, pb
    _W["_qq"], _W["_v28"], _W["_b2f"], _W["_s2c"] = _qq, _v28, _b2f, _s2c
    _W["_GML"] = _GML
    _W["steps"] = steps


def _decode_one(args) -> dict:
    blk, seed = args
    pa, pb = _W["pa"], _W["pb"]
    import numpy as _np
    rng = _np.random.default_rng(seed + blk)
    pick = rng.choice(pa.size, size=N, replace=True)
    alice = pa[pick].astype(_np.int64)
    bob = pb[pick].astype(_np.int64)
    model, bundle, field = _W["model"], _W["bundle"], _W["field"]
    dense = _W["dense"]
    _qq, _v28, _b2f, _s2c = _W["_qq"], _W["_v28"], _W["_b2f"], _W["_s2c"]
    H1 = _np.asarray(_W["mat_u1"].toarray(), dtype=_np.uint8)
    x = alice & 31
    y = bob & 31
    l_u2, final, rounds_used = 5 * M_BASE, None, 0
    for key in ("r0", "r1", "r2"):
        prior = _s2c.center_rows_prior(_b2f.marginal_prior_l2(bundle, bob), y)
        sxx = _qq.syndrome_of(field, dense[key], x.tolist())
        res = _v28.decode_error_domain_posterior(field, y.tolist(), dense[key],
                                                 sxx, prior, 300)
        xh = res.get("x_hat")
        ex = xh is not None and bool(_np.array_equal(_np.asarray(xh), x))
        if ex:
            final = {"exact_match": True,
                     "x_hat": _np.asarray(xh, dtype=_np.int64).tolist(),
                     "reconstruction_ok": bool(res.get("reconstruction_ok", False))}
            break
        rounds_used += 1
        l_u2 = 5 * (M_BASE + sum(_W["steps"][:rounds_used]))
        final = {"exact_match": False,
                 "x_hat": None,
                 "reconstruction_ok": bool(res.get("reconstruction_ok", False))}
    u2ok = bool(final["exact_match"])
    if not u2ok:
        return {"block": blk, "u2_ok": False, "exact_full": False,
                "undetected": False, "L_u2": l_u2, "L_u1": 0, "u1_extra": 0,
                "rounds": rounds_used}
    u2hat = _np.asarray(final["x_hat"], dtype=_np.int64)
    low5 = [((u2hat >> i) & 1).astype(_np.uint8) for i in range(5)]
    high_rec = []
    u1_ok, u1_extra, u1_syn_ok = True, 0, True
    rok_u2 = bool(final.get("reconstruction_ok", False))
    for bit in range(5, 10):
        prev = _np.stack(low5 + high_rec, axis=0)
        q = model.query(bit, bob, prev)
        base = (q.p_one > 0.5).astype(_np.uint8)
        truth = ((alice >> bit) & 1).astype(_np.uint8)
        syn = (H1 @ truth) % 2
        ch = _np.minimum(q.p_one, 1 - q.p_one).copy()
        dec = _W["_GML"](_W["groups"], "spc", ch, 0)
        rec = _np.bitwise_xor(base, dec.decode(_np.bitwise_xor(syn, (H1 @ base) % 2)))
        syn_ok_first = bool(_np.array_equal((H1 @ rec) % 2, syn))
        if not (syn_ok_first and bool(_np.array_equal(rec, truth))):
            w = _np.log((1 - _np.maximum(ch, 1e-300)) / _np.maximum(ch, 1e-300))
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
            "undetected": bool(und), "L_u2": l_u2,
            "L_u1": 50, "u1_extra": u1_extra, "rounds": rounds_used}


def _run_cfg(payload, seed, n_blocks, tag):
    import concurrent.futures as cf

    t0 = time.perf_counter()
    with cf.ProcessPoolExecutor(max_workers=WORKERS,
                                initializer=_worker_init,
                                initargs=(payload,)) as ex:
        recs = list(ex.map(_decode_one, [(b, seed) for b in range(n_blocks)]))
    return recs, time.perf_counter() - t0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("T-4 runs only with --full")
    import pickle

    from comparison_bench.src.comparison_bench.formal_ir.msd_s1_proxy import (  # noqa: E402
        load_tier_pairs,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_s3triple_u2grid import (  # noqa: E402
        build_point as _bp,
    )

    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    scalars = read_p1_scalars()["T2-1M"]
    proot = Path("workspace/s1_proxy/s1_20261006")
    pa_all, _ = load_tier_pairs(proot, "T2-1M", "half_a")
    z = np.load(proot / "T2-1M_tier_pairs.npz")
    bh_a = np.asarray(z["a_half_b"], dtype=np.int64)
    bh_b = np.asarray(z["b_half_b"], dtype=np.int64)
    counts = np.zeros((1024, 1024), dtype=np.float64)
    np.add.at(counts, (bh_a, bh_b), 1)
    info = _bp(224 + 32, 20265301)
    triples = info["triples"]
    jl = root / "blocks_t4.jsonl"
    if jl.exists():
        jl.unlink()
    tuned = []
    for steps in STEPS:
        import pickle as _pk
        payload = _pk.dumps((counts, triples, pa_all,
                             np.asarray(z["b_half_a"], dtype=np.int64), steps))
        recs, wall = _run_cfg(payload, SEED_A, B_TUNE, steps)
        with jl.open("a", encoding="utf-8", buffering=1) as fh:
            for r in recs:
                fh.write(json.dumps({"steps": list(steps), "stream": "A", **r}) + "\n")
        tuned.append(_summarize(recs, wall, scalars, steps, "A"))
        print(f"tune {steps}: " + json.dumps({k: tuned[-1][k] for k in
              ("failures", "E_L", "f_expected")}), flush=True)
    best = min(tuned, key=lambda r: r["f_expected"])
    payload = pickle.dumps((counts, triples, pa_all,
                            np.asarray(z["b_half_a"], dtype=np.int64),
                            tuple(best["steps"])))
    recs, wall = _run_cfg(payload, SEED_B, B_CONFIRM, tuple(best["steps"]))
    with jl.open("a", encoding="utf-8", buffering=1) as fh:
        for r in recs:
            fh.write(json.dumps({"steps": list(best["steps"]), "stream": "B", **r}) + "\n")
    conf = _summarize(recs, wall, scalars, tuple(best["steps"]), "B")
    out = {"tune": tuned, "best_steps": list(best["steps"]), "confirm": conf}
    (root / "t4_summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


def _summarize(recs, wall, scalars, steps, stream):
    nb = len(recs)
    nf = sum(0 if r["exact_full"] else 1 for r in recs)
    nu = sum(1 for r in recs if r["undetected"])
    e_l = sum(r["L_u2"] + r["L_u1"] + r.get("u1_extra", 0) for r in recs) / nb
    fer = nf / nb
    denom = N * scalars["H_AB"]
    kept = N * scalars["H_A"] - e_l
    f_p = (e_l + TAG_BITS + kept * fer) / denom
    from collections import Counter as _C
    rhist = dict(_C(r.get("rounds", 0) for r in recs))
    return {"steps": list(steps), "stream": stream, "blocks": nb, "failures": nf,
            "undetected": nu, "E_L": e_l, "FER_exact": fer,
            "FER_wilson_upper95": wilson_upper(nf, nb), "f_expected": f_p,
            "source": "T2-1M", "N": N, "backend": "t4-multiround",
            "round_hist": {str(k): v for k, v in rhist.items()}, "wall_s": wall}


if __name__ == "__main__":
    main()
