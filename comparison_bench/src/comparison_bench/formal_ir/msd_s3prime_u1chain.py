"""S-3' chained u1 coverage (packet scope): u2 FIRST, then u1 five binary
planes with TRUE recovered prefix P(u1 | b, u2-hat).

Budget frozen from measured conditional quantity FIRST (rule): per-plane
H(bit|B,true-prefix) ≈ 0.001 b/sym (~1 bit/1024-block each, ~5 bits total)
-> m=10/plane SPC (~102-bit groups) + K=16 targeted rescue backstop.
Target: u1 disclosure <= 75 bits/superframe with full-symbol success.
Channel Tier1 bootstrap / prior half_b (R10). B=100, T2-1M pilot.
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
from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
    build_conditional_prior_model,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_m1primea_repetition import (  # noqa: E402
    GroupMLDecoder,
    spc_matrix,
    split_groups,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
    _syndrome,
)

N = 1024
M_U1 = 10
G_U1 = 102  # ~N/10 single-parity groups per plane (1024/10; tail merged)
K_U1 = 16
B = 100
SEED = 20264600
TAG_BITS = 64


def run_chain_prime(*, pairs_a, pairs_b, model, bundle, dense_u2, field,
                    n_blocks: int, seed: int, jsonl_path: Path) -> dict:
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v10_fftqspa as _q,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v28 as _v28,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        v80_b2f_campaign as _b2f,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        v80_s2c_campaign as _s2c,
    )
    groups = split_groups(N, G_U1)
    mat_u1 = spc_matrix(groups, N)
    H1 = np.asarray(mat_u1.toarray(), dtype=np.uint8)
    m_u1 = int(mat_u1.shape[0])
    rng = np.random.default_rng(seed)
    n_fail = n_und = 0
    u1_dis = 0
    u1_res_blocks = 0
    n_res_u2 = 0
    t0 = time.perf_counter()
    with jsonl_path.open("a", encoding="utf-8", buffering=1) as fh:
        for blk in range(n_blocks):
            pick = rng.choice(pairs_a.size, size=N, replace=True)
            alice = pairs_a[pick].astype(np.int64)
            bob = pairs_b[pick].astype(np.int64)
            # stage 1: u2 (M0-style, base+rescue)
            x = alice & 31
            y = bob & 31
            outs = []
            for key in ("base", "full"):
                if key == "full" and outs and bool(outs[0]["exact_match"]):
                    break
                prior = _s2c.center_rows_prior(
                    _b2f.marginal_prior_l2(bundle, bob), y)
                sxx = _q.syndrome_of(field, dense_u2[key], x.tolist())
                res = _v28.decode_error_domain_posterior(
                    field, y.tolist(), dense_u2[key], sxx, prior, 300)
                xh = res.get("x_hat")
                ex = xh is not None and bool(np.array_equal(np.asarray(xh), x))
                outs.append({"exact_match": ex,
                             "x_hat": (np.asarray(xh, dtype=np.int64).tolist()
                                       if xh is not None else None),
                             "reconstruction_ok": bool(res.get("reconstruction_ok", False))})
            u2ok = bool(outs[0]["exact_match"]) or (
                len(outs) > 1 and bool(outs[1]["exact_match"]))
            l_u2 = 200 if (len(outs) == 1) else 208
            if len(outs) > 1:
                n_res_u2 += 1
            if not u2ok:
                n_fail += 1
                fh.write(json.dumps({"block": blk, "u2_ok": False,
                                     "exact_full": False}) + "\n")
                continue
            # stage 2: five u1 planes; prefix = recovered u2 bits 0-4,
            # extended by each recovered high bit (full chain conditioning).
            # u2ok gate above guarantees outs holds an exact x_hat.
            _xh = outs[0]["x_hat"] if outs[0]["exact_match"] else outs[1]["x_hat"]
            u2hat = np.asarray(_xh, dtype=np.int64)
            low5 = [((u2hat >> i) & 1).astype(np.uint8) for i in range(5)]
            high_rec = []
            u1_ok, u1_extra, u1_syn_ok = True, 0, True
            rok_u2 = bool((outs[0].get("reconstruction_ok", False))
                          if len(outs) == 1 else outs[-1].get("reconstruction_ok", False))
            for bit in range(5, 10):
                prev = np.stack(low5 + high_rec, axis=0)
                q = model.query(bit, bob, prev)
                base = (q.p_one > 0.5).astype(np.uint8)
                truth = ((alice >> bit) & 1).astype(np.uint8)
                syn = (H1 @ truth) % 2
                ch = np.minimum(q.p_one, 1 - q.p_one).copy()
                dec = GroupMLDecoder(groups, "spc", ch, 0)
                rec = np.bitwise_xor(
                    base, dec.decode(np.bitwise_xor(syn, (H1 @ base) % 2)))
                syn_ok_first = bool(np.array_equal((H1 @ rec) % 2, syn))
                if not (syn_ok_first and bool(np.array_equal(rec, truth))):
                    # K-targeted rescue on this plane
                    w = np.log((1 - np.maximum(ch, 1e-300)) / np.maximum(ch, 1e-300))
                    weak = np.argsort(w, kind="stable")[:K_U1]
                    base[weak] = truth[weak]
                    u1_extra += K_U1
                    rec2 = base.copy()
                    if not bool(np.array_equal(rec2, truth)):
                        u1_ok = False
                        u1_syn_ok = bool(syn_ok_first)
                        break
                    rec = rec2
                high_rec.append(rec.astype(np.uint8))
            u1_dis += 5 * m_u1 + u1_extra
            if u1_extra:
                u1_res_blocks += 1
            full = u1_ok
            n_fail += 0 if full else 1
            if (not full) and rok_u2 and u1_syn_ok:
                # every attempted syndrome check passed but block inexact
                n_und += 1
            fh.write(json.dumps({"block": blk, "u2_ok": True,
                                 "exact_full": bool(full),
                                 "u1_extra": u1_extra}) + "\n")
    wall = time.perf_counter() - t0
    return {"m_u1_total": 5 * m_u1, "u1_disclosure_mean": u1_dis / n_blocks,
            "u1_rescue_blocks": u1_res_blocks, "blocks": n_blocks,
            "failures": n_fail, "undetected": n_und, "n_rescue_u2": n_res_u2,
            "wall_s": wall, "s_per_block": wall / n_blocks}


_R = {}


def _real_init(source: str):
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        load_train_table,
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
    from comparison_bench.src.comparison_bench.cli import (  # noqa: E402
        p1_stage1_runner as _p1,
    )
    table = load_train_table(source)
    _R["model"] = _bcp(table, encoding="NATURAL", order="LSB_FIRST")
    _R["bundle"] = _s2c.bind_empirical_bundle(derive_bundle(table))
    # S-3''' optimum m=224 (fresh A208-family construction + gates), NOT the
    # frozen A208 (m=200/208). Rescue = nested rows[224,232).
    from comparison_bench.src.comparison_bench.formal_ir.msd_s3triple_u2grid import (  # noqa: E402
        build_point as _build224,
    )
    info = _build224(224, 20263835)
    _R["construction"] = info
    field = _GF.create(32)
    _R["field"] = field
    _R["dense"] = {}
    for key, m in (("base", 224), ("full", 232)):
        trips = [(int(r), int(c), int(v)) for r, c, v in info["triples"]
                 if int(r) < m]
        _R["dense"][key] = _peg.sparse_to_dense(trips, N, m, field)
    _R["groups"] = split_groups(N, G_U1)
    _R["mat_u1"] = spc_matrix(_R["groups"], N)
    _R["_qq"], _R["_v28"], _R["_b2f"], _R["_s2c"] = _qq, _v28, _b2f, _s2c


def _real_one(args) -> dict:
    a_list, b_list, blk = args
    alice = np.asarray(a_list, dtype=np.int64)
    bob = np.asarray(b_list, dtype=np.int64)
    model, bundle, field = _R["model"], _R["bundle"], _R["field"]
    dense, groups, mat_u1 = _R["dense"], _R["groups"], _R["mat_u1"]
    _qq, _v28, _b2f, _s2c = _R["_qq"], _R["_v28"], _R["_b2f"], _R["_s2c"]
    H1 = np.asarray(mat_u1.toarray(), dtype=np.uint8)
    m_u1 = int(mat_u1.shape[0])
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
        ex = xh is not None and bool(np.array_equal(np.asarray(xh), x))
        outs.append({"exact_match": ex,
                     "x_hat": (np.asarray(xh, dtype=np.int64).tolist()
                               if xh is not None else None),
                     "reconstruction_ok": bool(res.get("reconstruction_ok", False))})
    u2ok = bool(outs[0]["exact_match"]) or (len(outs) > 1 and bool(outs[1]["exact_match"]))
    l_u2 = 5 * (224 if len(outs) == 1 else 232)
    if not u2ok:
        return {"block": blk, "u2_ok": False, "exact_full": False,
                "undetected": False, "L_u2": l_u2, "L_u1": 0, "u1_extra": 0}
    _xh = outs[0]["x_hat"] if outs[0]["exact_match"] else outs[1]["x_hat"]
    u2hat = np.asarray(_xh, dtype=np.int64)
    low5 = [((u2hat >> i) & 1).astype(np.uint8) for i in range(5)]
    high_rec = []
    u1_ok, u1_extra, u1_syn_ok = True, 0, True
    rok_u2 = bool(outs[-1].get("reconstruction_ok", False))
    for bit in range(5, 10):
        prev = np.stack(low5 + high_rec, axis=0)
        q = model.query(bit, bob, prev)
        base = (q.p_one > 0.5).astype(np.uint8)
        truth = ((alice >> bit) & 1).astype(np.uint8)
        syn = (H1 @ truth) % 2
        ch = np.minimum(q.p_one, 1 - q.p_one).copy()
        dec = GroupMLDecoder(groups, "spc", ch, 0)
        rec = np.bitwise_xor(base, dec.decode(np.bitwise_xor(syn, (H1 @ base) % 2)))
        syn_ok_first = bool(np.array_equal((H1 @ rec) % 2, syn))
        if not (syn_ok_first and bool(np.array_equal(rec, truth))):
            w = np.log((1 - np.maximum(ch, 1e-300)) / np.maximum(ch, 1e-300))
            weak = np.argsort(w, kind="stable")[:K_U1]
            base[weak] = truth[weak]
            u1_extra += K_U1
            rec2 = base.copy()
            if not bool(np.array_equal(rec2, truth)):
                u1_ok = False
                u1_syn_ok = bool(syn_ok_first)
                break
            rec = rec2
        high_rec.append(rec.astype(np.uint8))
    full = u1_ok
    und = (not full) and rok_u2 and u1_syn_ok
    return {"block": blk, "u2_ok": True, "exact_full": bool(full),
            "undetected": bool(und), "L_u2": l_u2,
            "L_u1": 5 * m_u1, "u1_extra": u1_extra}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--proxy-root", required=False, default=None)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if args.real:
        run_real_main(args)
        return
    if not args.full:
        raise SystemExit("S-3' runs only with --full")
    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    scalars = read_p1_scalars()["T2-1M"]
    z = np.load(Path(args.proxy_root) / "T2-1M_tier_pairs.npz")
    pa, pb = (np.asarray(z["a_half_a"], dtype=np.int64),
              np.asarray(z["b_half_a"], dtype=np.int64))
    pt = np.asarray(np.load(Path(args.proxy_root) / "T2-1M_tier_tables.npz")["half_b"])
    model = build_conditional_prior_model(pt, encoding="NATURAL", order="LSB_FIRST")
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
    from comparison_bench.src.comparison_bench.cli import (  # noqa: E402
        p1_stage1_runner as _p1,
    )
    bundle = _s2c.bind_empirical_bundle(
        {"g1": derive_bundle(pt)["g1"], "g2": derive_bundle(pt)["g2"],
         "p_b": derive_bundle(pt)["p_b"]})
    pinned = _p1.construct_and_pin("P1S1-R1", _p1.PRODUCTION_CONSTRUCT["P1S1-R1"],
                                   _p1.production_rank_fn)
    field = _GF.create(32)
    dense_u2 = {k: _peg.sparse_to_dense(
        pinned["base" if k == "base" else "full"]["triples"], N,
        200 if k == "base" else 208, field) for k in ("base", "full")}
    jl = root / "blocks_s3p.jsonl"
    if jl.exists():
        jl.unlink()
    r = run_chain_prime(pairs_a=pa, pairs_b=pb, model=model, bundle=bundle,
                        dense_u2=dense_u2, field=field, n_blocks=100,
                        seed=20264700, jsonl_path=jl)
    e_u2 = 1000.0 + 40.0 * r["n_rescue_u2"] / r["blocks"]
    e_l = e_u2 + r["u1_disclosure_mean"]
    fer = r["failures"] / r["blocks"]
    denom = N * scalars["H_AB"]
    kept = N * scalars["H_A"] - e_l
    f_p = (e_l + TAG_BITS + kept * fer) / denom
    row = {**r, "E_L": e_l, "E_u2": e_u2, "FER_exact": fer,
           "FER_wilson_upper95": wilson_upper(r["failures"], r["blocks"]),
           "f_expected": f_p, "source": "T2-1M", "N": N,
           "backend": "nb-u1chain"}
    (root / "s3p_summary.json").write_text(json.dumps([row], indent=2),
                                           encoding="utf-8")
    print(json.dumps([row], indent=2))


def run_real_main(args) -> None:
    """S-5 execution path (authorized Pre-EXECUTE only): NB full chain on
    real VAL/HOLD superframes, pooled per source. R1 originals, re-test label.
    """
    import concurrent.futures as cf
    from comparison_bench.src.comparison_bench.formal_ir.msd_m5_realframe import (  # noqa: E402
        load_real_series_win as _load_real,
    )
    from comparison_bench.src.comparison_bench.cli.probes_closed import (  # noqa: E402
        m0_realframe_runner as _m0sup,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        read_p1_scalars as _scalars,
    )

    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    scalars = _scalars()
    msd_rows, nb_rows = [], []
    srcmap = {"1M": "T2-1M", "1p5M": "T2-1.5M", "2M": "T2-2M"}
    for label in ("1M", "1p5M", "2M"):
        source = srcmap[label]
        series = _load_real(label)
        supers = _m0sup.superframes(series["a"], series["b"])
        t0 = time.perf_counter()
        with cf.ProcessPoolExecutor(max_workers=12,
                                    initializer=_real_init,
                                    initargs=(source,)) as ex:
            recs = list(ex.map(_real_one,
                               [(a.tolist(), b.tolist(), si)
                                for si, (a, b) in enumerate(supers)]))
        wall = time.perf_counter() - t0
        jl = root / f"blocks_s5_{label}.jsonl"
        with jl.open("w", encoding="utf-8", buffering=1) as fh:
            for r in recs:
                fh.write(json.dumps({"source": source, **r}) + "\n")
        nb = len(recs)
        nf = sum(0 if r["exact_full"] else 1 for r in recs)
        nu = sum(1 for r in recs if r["undetected"])
        e_u2 = sum(r["L_u2"] for r in recs) / nb
        e_u1 = sum(50 + r.get("u1_extra", 0) if r.get("u2_ok") else 0
                   for r in recs) / nb
        e_l = e_u2 + e_u1
        fer = nf / nb
        s = scalars[source]
        denom = N * s["H_AB"]
        kept = N * s["H_A"] - e_l
        f_p = (e_l + TAG_BITS + kept * fer) / denom
        nb_rows.append({"source": source, "arm": "nb-full-chain-R1", "N": N,
                        "backend": "nb-u1chain-real", "blocks": nb,
                        "superframes": len(supers), "failures": nf,
                        "undetected": nu, "E_u2": e_u2, "E_u1": e_u1, "E_L": e_l,
                        "FER_exact": fer,
                        "FER_wilson_upper95": wilson_upper(nf, nb),
                        "f_expected": f_p, "H_A": s["H_A"], "H_AB": s["H_AB"],
                        "wall_s": wall})
    (root / "s5_nb_summary.json").write_text(json.dumps(nb_rows, indent=2),
                                             encoding="utf-8")
    print(json.dumps(nb_rows, indent=2))


if __name__ == "__main__":
    main()
