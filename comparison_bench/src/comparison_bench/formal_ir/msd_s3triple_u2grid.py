"""S-3''' u2 m-grid with fresh rate-compatible GF32 construction (packet scope).

m <= 208 cap REMOVED (leftover of discarded A208 certification gate).
Per m in {200,208,216,224,232,240}: fresh peg_construct (A208 lambda family
{2:1.0}, rho derived per m, new seeds, four_cycles==0 + rank==m gates) with
M = m+8 rows; base rows[0,m) + single nested rescue rows[m,m+8).
Rescue accounting = ACTUAL appended rows x 5 (no (208-m) formula).
u1 via S-3' chained SPC-10 + K16. Full-symbol metric (R11), Tier1 proxy (R10).
Pooled x12. B=100/point, T2-1M pilot.
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
M_GRID = (200, 208, 216, 224, 232, 240)
RESCUE_ROWS = 8
B = 100
SEED_BASE = 20263611
TAG_BITS = 64
WORKERS = 12
LAM = {2: 1.0}

_W = {}


def build_point(m_base: int, seed: int) -> dict:
    """Fresh A208-family construction with gates (returns triples + pins)."""
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v10_peg as _peg,
    )
    from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (  # noqa: E402
        GF2mField as _GF,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v26_mcde as _mcde,
    )
    from comparison_bench.src.comparison_bench.cli import (  # noqa: E402
        p1_stage1_runner as _p1r,
    )
    field = _GF.create(32)
    m_tot = m_base + RESCUE_ROWS
    rho = _mcde.make_rho(1.0 - m_tot / N, {int(k): float(v) for k, v in LAM.items()})
    code = _peg.peg_construct(N, m_tot, {int(k): float(v) for k, v in LAM.items()},
                              rho, int(seed), max_trials=20, field=field)
    if int(code.get("four_cycles", -1)) != 0:
        raise SystemExit(f"m={m_base}: four_cycles {code.get('four_cycles')} != 0")
    sa = [(int(r), int(c), int(v)) for r, c, v in code["triples"]]
    dense = _peg.sparse_to_dense(sa, N, m_tot, field)
    dm = np.asarray(dense.todense() if hasattr(dense, "todense") else dense)
    base_rank = int(_p1r.production_rank_fn(dm[:m_base]))
    if base_rank != m_base:
        raise SystemExit(f"m={m_base}: base rank {base_rank} != {m_base}")
    return {"triples": sa,
            "m_base": m_base, "m_total": m_tot, "seed": seed,
            "four_cycles": int(code.get("four_cycles", 0)), "base_rank": base_rank}


def _worker_init(m_base: int, triples):
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
    pt = np.asarray(np.load(root / "T2-1M_tier_tables.npz")["half_b"])
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        build_conditional_prior_model as _bcp,
    )
    _W["model"] = _bcp(pt, encoding="NATURAL", order="LSB_FIRST")
    _W["bundle"] = _s2c.bind_empirical_bundle(derive_bundle(pt))
    _W["model"] = _bcp(pt, encoding="NATURAL", order="LSB_FIRST")
    field = _GF.create(32)
    _W["field"] = field
    _W["dense"] = {}
    for key, m in (("base", m_base), ("full", m_base + RESCUE_ROWS)):
        sub = [(r, c, v) for r, c, v in triples if r < m]
        _W["dense"][key] = _peg.sparse_to_dense(sub, N, m, field)
    _W["groups"] = _sg(N, 102)
    _W["mat_u1"] = _spc(_W["groups"], N)
    _W["pa"], _W["pb"] = pa, pb
    _W["_qq"], _W["_v28"], _W["_b2f"], _W["_s2c"] = _qq, _v28, _b2f, _s2c
    _W["_GML"] = _GML
    _W["m_base"] = m_base


def _decode_one(args) -> dict:
    blk, seed = args
    pa, pb = _W["pa"], _W["pb"]
    Nloc = N
    rng = np.random.default_rng(seed + blk)
    pick = rng.choice(pa.size, size=Nloc, replace=True)
    alice = pa[pick].astype(np.int64)
    bob = pb[pick].astype(np.int64)
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
        t = time.perf_counter()
        res = _v28.decode_error_domain_posterior(field, y.tolist(), dense[key],
                                                 sxx, prior, 300)
        wall = time.perf_counter() - t
        xh = res.get("x_hat")
        ex = xh is not None and bool(np.array_equal(np.asarray(xh), x))
        outs.append({"exact_match": ex,
                     "x_hat": (np.asarray(xh, dtype=np.int64).tolist()
                               if xh is not None else None),
                     "reconstruction_ok": bool(res.get("reconstruction_ok", False)),
                     "wall": wall})
    u2ok = bool(outs[0]["exact_match"]) or (len(outs) > 1 and bool(outs[1]["exact_match"]))
    l_u2 = _W["m_base"] if len(outs) == 1 else _W["m_base"] + RESCUE_ROWS
    if not u2ok:
        return {"block": blk, "u2_ok": False, "exact_full": False,
                "undetected": False, "L_u2": l_u2, "L_u1": 0, "u1_extra": 0,
                "wall": sum(o.get("wall", 0.0) for o in outs)}
    _xh = outs[0]["x_hat"] if outs[0]["exact_match"] else outs[1]["x_hat"]
    u2hat = np.asarray(_xh, dtype=np.int64)
    model, groups, mat_u1 = _W["model"], _W["groups"], _W["mat_u1"]
    H1 = np.asarray(mat_u1.toarray(), dtype=np.uint8)
    low5 = [((u2hat >> i) & 1).astype(np.uint8) for i in range(5)]
    high_rec = []
    u1_ok, u1_extra, u1_syn_ok = True, 0, True
    rok_u2 = bool(outs[0].get("reconstruction_ok", False))
    for bit in range(5, 10):
        prev = np.stack(low5 + high_rec, axis=0)
        q = model.query(bit, bob, prev)
        base = (q.p_one > 0.5).astype(np.uint8)
        truth = ((alice >> bit) & 1).astype(np.uint8)
        syn = (H1 @ truth) % 2
        ch = np.minimum(q.p_one, 1 - q.p_one).copy()
        dec = _W["_GML"](groups, "spc", ch, 0)
        rec = np.bitwise_xor(base, dec.decode(np.bitwise_xor(syn, (H1 @ base) % 2)))
        syn_ok_first = bool(np.array_equal((H1 @ rec) % 2, syn))
        if not (syn_ok_first and bool(np.array_equal(rec, truth))):
            w = np.log((1 - np.maximum(ch, 1e-300)) / np.maximum(ch, 1e-300))
            weak = np.argsort(w, kind="stable")[:16]
            base[weak] = truth[weak]
            u1_extra += 16
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
            "L_u1": 5 * int(mat_u1.shape[0]), "u1_extra": u1_extra,
            "wall": sum(o.get("wall", 0.0) for o in outs)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("S-3''' runs only with --full")
    import concurrent.futures as cf

    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    jl = root / "blocks_s3t.jsonl"
    if jl.exists():
        jl.unlink()
    scalars = read_p1_scalars()["T2-1M"]
    rows = []
    for m_base in M_GRID:
        info = build_point(m_base, SEED_BASE + m_base)
        t0 = time.perf_counter()
        with cf.ProcessPoolExecutor(max_workers=WORKERS,
                                    initializer=_worker_init,
                                    initargs=(m_base, info["triples"])) as ex:
            recs = list(ex.map(_decode_one, [(b, 20264700 + m_base) for b in range(B)]))
        wall = time.perf_counter() - t0
        with jl.open("a", encoding="utf-8", buffering=1) as fh:
            for r in recs:
                fh.write(json.dumps({"m_base": m_base, **r}) + "\n")
        nb = len(recs)
        nf = sum(0 if r["exact_full"] else 1 for r in recs)
        nu = sum(1 for r in recs if r["undetected"])
        e_u2 = sum(r["L_u2"] for r in recs) / nb
        e_u1 = sum((r["L_u1"] + r.get("u1_extra", 0)) if r.get("u2_ok") else 0
                   for r in recs) / nb
        e_l = e_u2 + e_u1
        fer = nf / nb
        denom = N * scalars["H_AB"]
        kept = N * scalars["H_A"] - e_l
        f_p = (e_l + TAG_BITS + kept * fer) / denom
        rows.append({"m_base": m_base, "four_cycles": info["four_cycles"],
                     "blocks": nb, "failures": nf, "undetected": nu,
                     "E_u2": e_u2, "E_u1": e_u1, "E_L": e_l, "FER_exact": fer,
                     "FER_wilson_upper95": wilson_upper(nf, nb),
                     "f_expected": f_p, "source": "T2-1M", "N": N,
                     "backend": "nb-u1chain-mgrid", "wall_s": wall})
        print(f"m={m_base}: fail {nf}/{nb} und {nu} E_L={e_l:.0f} f={f_p:.3f}", flush=True)
    (root / "s3t_summary.json").write_text(json.dumps(rows, indent=2),
                                           encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
