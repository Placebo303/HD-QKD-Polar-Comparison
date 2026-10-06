"""S-3 probe: u1-plane short binary syndrome code ladder (S3_PACKET_DRAFT scope).

u1 = bit5 plane; genie true lower prefix (stages 0-4) isolates u1-code
performance (labeled; full chain later). Channel: bootstrap TRAIN-a pairs;
prior: TRAIN-b table stage-5 query (R10). Codes: SPC groups g in {8,16,32}
+ exact ML (reused GroupMLDecoder). Metric: u1-plane FER ladder + projected
full-symbol f (measured u1 FER + frozen S-1-proxy Tier1 u2 FER, labeled).
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
BIT = 5
GS = (8, 16, 32)
B = 60
SEED = 20263201
TAG_BITS = 64
# frozen S-1-proxy Tier1 u2 inputs for projection (labeled, T2-1M)
U2_FER = 0.05
U2_L = 1000.0


def run_ladder(*, pairs_a: np.ndarray, pairs_b: np.ndarray,
               prior_table: np.ndarray, h_ab: float, h_a: float,
               n_blocks: int, seed: int, jsonl_path: Path) -> list[dict]:
    model = build_conditional_prior_model(prior_table, encoding="NATURAL",
                                          order="LSB_FIRST")
    rng = np.random.default_rng(seed)
    rows = []
    for g in GS:
        groups = split_groups(N, g)
        mat = spc_matrix(groups, N)
        Hd = np.asarray(mat.toarray(), dtype=np.uint8)
        n_fail = 0
        t0 = time.perf_counter()
        with jsonl_path.open("a", encoding="utf-8", buffering=1) as fh:
            for blk in range(n_blocks):
                pick = rng.choice(pairs_a.size, size=N, replace=True)
                alice = pairs_a[pick].astype(np.int64)
                bob = pairs_b[pick].astype(np.int64)
                prev = np.stack([((alice >> i) & 1).astype(np.uint8)
                                 for i in range(5)], axis=0)
                q = model.query(5, bob, prev)
                base = (q.p_one > 0.5).astype(np.uint8)
                truth = ((alice >> BIT) & 1).astype(np.uint8)
                syn = (Hd @ truth) % 2
                delta = np.bitwise_xor(syn, (Hd @ base) % 2)
                ch = np.minimum(q.p_one, 1 - q.p_one).copy()
                dec = GroupMLDecoder(groups, "spc", ch, 0)
                rec = np.bitwise_xor(base, dec.decode(delta))
                ok = bool(np.array_equal((Hd @ rec) % 2, syn)
                          and np.array_equal(rec, truth))
                n_fail += 0 if ok else 1
                fh.write(json.dumps({"g": g, "block": blk, "exact_ok": bool(ok)}) + "\n")
        wall = time.perf_counter() - t0
        m_u1 = int(mat.shape[0])
        fer_u1 = n_fail / n_blocks
        fer_full = 1 - (1 - fer_u1) * (1 - U2_FER)
        l_tot = m_u1 + U2_L
        denom = N * h_ab
        kept = N * h_a - l_tot
        f_p = (l_tot + TAG_BITS + kept * fer_full) / denom
        rows.append({"g": g, "m_u1": m_u1, "blocks": n_blocks,
                     "u1_failures": n_fail, "u1_fer": fer_u1,
                     "u1_fer_upper95": wilson_upper(n_fail, n_blocks),
                     "proj_full_fer": fer_full, "proj_f": f_p,
                     "wall_s": wall, "s_per_block": wall / n_blocks})
    return rows


def run_chain(*, pairs_a: np.ndarray, pairs_b: np.ndarray,
              prior_table: np.ndarray,
              dense_u2: dict,
              n_blocks: int, seed: int,
              jsonl_path: Path) -> dict:
    """Full-symbol NB chain: 5 Bob-only binary high-bit planes + u2 GF32.

    bit5 rep-3 (m=683), bit6 rep-2 (m=512), bit7 SPC-8 (128), bit8 SPC-16 (64),
    bit9 SPC-32 (32), all exact-ML; u1 assembled -> u2 via adapter conditioned
    on RECOVERED u1 (v28-style, real L1). Full-symbol exact = all stages exact.
    """
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primea_repetition import (
        repetition_matrix,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (
        build_conditional_prior_model,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v10_fftqspa as _q,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v28 as _v28,
    )
    from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (  # noqa: E402
        GF2mField as _GF,
    )

    models = {}
    for ob in (5, 6, 7, 8, 9):
        order = [ob] + [i for i in range(10) if i != ob]
        models[ob] = build_conditional_prior_model(
            prior_table, encoding="NATURAL", order=order)
    plane_codes = {}
    for ob, g, kind in ((5, 3, "rep"), (6, 2, "rep"), (7, 8, "spc"),
                        (8, 16, "spc"), (9, 32, "spc")):
        groups = split_groups(N, g if kind == "spc" else g)
        if kind == "rep":
            groups = split_groups(N, g)
            mat = repetition_matrix(groups, N)
        else:
            mat = spc_matrix(groups, N)
        plane_codes[ob] = (groups, mat, kind)
    field = _GF.create(32)
    rng = np.random.default_rng(seed)
    n_fail = n_und = n_res_u2 = 0
    m_u1 = sum(int(plane_codes[ob][1].shape[0]) for ob in (5, 6, 7, 8, 9))
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v26_channel as _v26,
    )
    _adapter = _v26.build_adapter(
        {"type2_1M_20260121_184040": prior_table},
        fact_id="F03", source="type2_1M_20260121_184040")
    t0 = time.perf_counter()
    with jsonl_path.open("a", encoding="utf-8", buffering=1) as fh:
        for blk in range(n_blocks):
            pick = rng.choice(pairs_a.size, size=N, replace=True)
            alice = pairs_a[pick].astype(np.int64)
            bob = pairs_b[pick].astype(np.int64)
            u1hat = np.zeros(N, dtype=np.int64)
            ok_all, u1mm = True, 0
            for ob in (5, 6, 7, 8, 9):
                groups, mat, kind = plane_codes[ob]
                Hd = np.asarray(mat.toarray(), dtype=np.uint8)
                q = models[ob].query(0, bob, np.empty((0, N), dtype=np.uint8))
                base = (q.p_one > 0.5).astype(np.uint8)
                truth = ((alice >> ob) & 1).astype(np.uint8)
                syn = (Hd @ truth) % 2
                dec = GroupMLDecoder(groups, "repetition" if kind == "rep" else "spc",
                                     np.minimum(q.p_one, 1 - q.p_one).copy(), 0)
                rec = np.bitwise_xor(base, dec.decode(np.bitwise_xor(syn, (Hd @ base) % 2)))
                good = bool(np.array_equal((Hd @ rec) % 2, syn)
                            and np.array_equal(rec, truth))
                ok_all = ok_all and good
                u1hat |= rec.astype(np.int64) << (ob - 5)
                if not good:
                    break
            # u2 GF32 conditioned on RECOVERED u1 (v28-style real L1):
            # V26 adapter posteriors P(u2 | b, u1hat), centered on y.
            x2t = (alice & 31).tolist()
            b2 = (bob & 31).tolist()
            s2 = _q.syndrome_of(field, dense_u2["base"], x2t)
            from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
                v80_s2c_campaign as _s2c,
            )
            rows2 = _adapter.posterior_rows("L2", bob, u1hat.tolist())
            prior2 = _s2c.center_rows_prior(rows2, np.asarray(b2))
            res_b = _v28.decode_error_domain_posterior(
                field, b2, dense_u2["base"], s2, prior2, 300)
            xh = res_b.get("x_hat")
            u2ok = xh is not None and bool(np.array_equal(np.asarray(xh), x2t))
            l_u2, rescued_u2 = 200, False
            if not u2ok:
                s2f = _q.syndrome_of(field, dense_u2["full"], x2t)
                res_f = _v28.decode_error_domain_posterior(
                    field, b2, dense_u2["full"], s2f, prior2, 300)
                xhf = res_f.get("x_hat")
                if xhf is not None and bool(np.array_equal(np.asarray(xhf), x2t)):
                    u2ok, res = True, res_f
                else:
                    res = res_f
                l_u2, rescued_u2 = 208, True
            full = ok_all and u2ok
            n_fail += 0 if full else 1
            rok = bool(res.get("reconstruction_ok", False))
            n_und += 1 if ((not full) and rok and ok_all) else 0
            n_res_u2 += 1 if rescued_u2 else 0
            fh.write(json.dumps({"block": blk, "u1_ok": bool(ok_all),
                                 "u2_ok": bool(u2ok), "exact_full": bool(full),
                                 "l_u2": l_u2, "rescued_u2": rescued_u2,
                                 "u1_mm_proxy": int((u1hat != ((alice >> 5) & 31)).sum())}) + "\n")
    wall = time.perf_counter() - t0
    return {"m_u1": m_u1, "m_u2_base": 200, "blocks": n_blocks, "failures": n_fail,
            "undetected": n_und, "n_rescue_u2": n_res_u2, "wall_s": wall,
            "s_per_block": wall / n_blocks}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--chain", action="store_true")
    ap.add_argument("--proxy-root", required=True)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not (args.full or args.chain):
        raise SystemExit("S-3 runs with --full (ladder) and/or --chain (full chain)")
    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    scalars = read_p1_scalars()["T2-1M"]
    z = np.load(Path(args.proxy_root) / "T2-1M_tier_pairs.npz")
    pa, pb = (np.asarray(z["a_half_a"], dtype=np.int64),
              np.asarray(z["b_half_a"], dtype=np.int64))
    pt = np.asarray(np.load(Path(args.proxy_root) / "T2-1M_tier_tables.npz")["half_b"])
    if args.full:
        jl = root / "blocks_s3.jsonl"
        if jl.exists():
            jl.unlink()
        rows = run_ladder(pairs_a=pa, pairs_b=pb, prior_table=pt,
                          h_ab=scalars["H_AB"], h_a=scalars["H_A"],
                          n_blocks=B, seed=SEED, jsonl_path=jl)
        (root / "s3_u1_summary.json").write_text(json.dumps(rows, indent=2),
                                                 encoding="utf-8")
        print(json.dumps(rows, indent=2))
    if args.chain:
        from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
            nonbinary_v10_peg as _peg,
        )
        from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (  # noqa: E402
            GF2mField as _GF,
        )
        from comparison_bench.src.comparison_bench.cli import (  # noqa: E402
            p1_stage1_runner as _p1,
        )
        pinned = _p1.construct_and_pin("P1S1-R1", _p1.PRODUCTION_CONSTRUCT["P1S1-R1"],
                                       _p1.production_rank_fn)
        field = _GF.create(32)
        dense = {key: _peg.sparse_to_dense(
            pinned["base" if key == "base" else "full"]["triples"], N,
            200 if key == "base" else 208, field) for key in ("base", "full")}
        jl = root / "blocks_s3_chain.jsonl"
        if jl.exists():
            jl.unlink()
        r = run_chain(pairs_a=pa, pairs_b=pb, prior_table=pt, dense_u2=dense,
                      n_blocks=B, seed=SEED + 7, jsonl_path=jl)
        e_l = r["m_u1"] + 1000.0 + 40.0 * r["n_rescue_u2"] / r["blocks"]
        fer = r["failures"] / r["blocks"]
        denom = N * scalars["H_AB"]
        kept = N * scalars["H_A"] - e_l
        f_p = (e_l + TAG_BITS + kept * fer) / denom
        row = {**r, "E_L": e_l, "FER_exact": fer,
               "FER_wilson_upper95": wilson_upper(r["failures"], r["blocks"]),
               "f_expected": f_p, "source": "T2-1M", "N": N,
               "backend": "nb-full-chain"}
        (root / "s3_chain_summary.json").write_text(json.dumps([row], indent=2),
                                                    encoding="utf-8")
        print(json.dumps([row], indent=2))


if __name__ == "__main__":
    main()
