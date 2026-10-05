"""M5 real-frame validation (DECIDE, authorized; see M5_PREEXECUTE_DRAFT.md).

Reuses VERBATIM (zero edits): m0.load_real_series + superframes (frozen A1/R1
chain, R1 offset/count/split assertions, VAL+HOLD eval region); M4 R1-bundle
derivation; p1.construct_and_pin (frozen A208); b2f.decode_block_marginal
rescue mirror (base m=200 + COLD full m=208). MSD: frozen M2 config per
16384-symbol block (16 consecutive superframes; remainder dropped/reported).
NB: per-1024-symbol superframe (native unit). Fresh output root, JSONL per
unit, unified f + Poisson-band consistency vs synthetic predictions.
"""

from __future__ import annotations

import argparse
import functools
import json
import math
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
    load_train_table,
    plane_conditional_entropies,
    read_p1_scalars,
    wilson_upper,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
    build_conditional_prior_model,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_m1primea_repetition import (  # noqa: E402
    make_group_factory,
    spc_matrix,
    split_groups,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_m1primeb_mixed import (  # noqa: E402
    M1_16384,
    MAX_ITER,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_m4_nb_marginal import (  # noqa: E402
    derive_bundle,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (  # noqa: E402
    build_peg_code,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
    _natural_symbols_from_stages,
    _syndrome,
    disclose_syndromes,
    make_bp_decoder,
)
from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
    v80_b2f_campaign as b2f,
)
from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
    v80_s2c_campaign as s2c,
)
from comparison_bench.src.comparison_bench.cli import (  # noqa: E402
    p1_stage1_runner as p1,
)
from comparison_bench.src.comparison_bench.cli.probes_closed import (  # noqa: E402
    m0_realframe_runner as m0,
)

SRC = {"1M": "T2-1M", "1p5M": "T2-1.5M", "2M": "T2-2M"}
C0_MSD = 2000
K_MSD = 400
N_MSD = 16384
N_NB = 1024
TAG_BITS = 64
GROUP = 16  # superframes per MSD block
NB_ARMS = ("P1S1-R1", "P1S1-R2")
WORKERS_NB = 12


def group_blocks(supers: list[tuple[np.ndarray, np.ndarray]], group: int = GROUP):
    """Consecutive non-overlapping groups; remainder dropped (count reported)."""
    k = len(supers) // group
    blocks = []
    for i in range(k):
        seg = supers[i * group:(i + 1) * group]
        blocks.append((np.concatenate([a for a, _ in seg]),
                       np.concatenate([b for _, b in seg])))
    return blocks, len(supers) - k * group


def build_msd_matrices(n: int, h_plane: list[float]):
    bp = functools.partial(make_bp_decoder, max_iter=MAX_ITER)
    matrices, factories = [], []
    m0 = min(n - 1, max(1, int(math.ceil(n * h_plane[0] + C0_MSD))))
    matrices.append(build_peg_code(n=n, m=m0, variable_degree=3).parity_check_matrix)
    factories.append(bp)
    matrices.append(build_peg_code(n=n, m=M1_16384, variable_degree=3).parity_check_matrix)
    factories.append(bp)
    groups = split_groups(n, 256)
    for _ in range(8):
        matrices.append(spc_matrix(groups, n))
        factories.append(make_group_factory(groups, "spc", 0))
    return matrices, factories


def decode_block_msd(alice: np.ndarray, bob: np.ndarray, model,
                     matrices, factories, k_rescue: int) -> dict:
    """M5-scoped MSD block decode (frozen M2 procedure: base + 1 targeted round)."""
    n = alice.size
    dis = disclose_syndromes(alice, model, matrices)
    recovered: list[np.ndarray] = []
    passed: list[bool] = []
    rescued = False
    extra = 0
    for stage, mat in enumerate(matrices):
        prev = np.stack(recovered, axis=0) if recovered else np.empty((0, n), dtype=np.uint8)
        q = model.query(stage, bob, prev)
        base = (q.p_one > 0.5).astype(np.uint8)
        ch = np.minimum(q.p_one, 1 - q.p_one).copy()
        syndromes = np.asarray(dis.public_syndromes[stage], dtype=np.uint8)
        delta = np.bitwise_xor(syndromes, _syndrome(mat, base))
        fac = factories[stage]
        if stage == 0:
            dec = fac(parity_check_matrix=mat, error_channel=ch)
            rec = np.bitwise_xor(base, np.asarray(dec.decode(delta.copy())).astype(np.uint8))
            if not bool(np.array_equal(_syndrome(mat, rec), syndromes)):
                rescued = True
                extra = k_rescue
                w = np.log((1 - np.maximum(ch, 1e-300)) / np.maximum(ch, 1e-300))
                weak = np.argsort(w, kind="stable")[:k_rescue]
                base[weak] = ((alice >> 0) & 1).astype(np.uint8)[weak]
                ch[weak] = 0.0
                delta2 = np.bitwise_xor(syndromes, _syndrome(mat, base))
                dec2 = fac(parity_check_matrix=mat, error_channel=ch)
                rec = np.bitwise_xor(
                    base, np.asarray(dec2.decode(delta2.copy())).astype(np.uint8))
        else:
            dec = fac(parity_check_matrix=mat, error_channel=ch)
            rec = np.bitwise_xor(
                base, np.asarray(dec.decode(delta.copy())).astype(np.uint8))
        recovered.append(rec)
        ok = bool(np.array_equal(_syndrome(mat, rec), syndromes))
        passed.append(ok)
        if not ok:
            break
    full = len(passed) == 10 and all(passed)
    recon = _natural_symbols_from_stages(recovered, model, n) if full else None
    exact = recon is not None and bool(np.array_equal(recon, alice))
    return {"exact_ok": exact, "undetected": full and not exact, "rescued": rescued,
            "extra": extra, "stages_passed": [bool(v) for v in passed]}


_NB = {}


def _nb_init_pool(source: str):
    """Worker initializer: bundle + both frozen constructions + dense matrices."""
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v10_peg as peg,
    )
    from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (  # noqa: E402
        GF2mField as _GF,
    )

    table = load_train_table(SRC[source])
    _NB["bundle"] = s2c.bind_empirical_bundle(derive_bundle(table))
    _NB["field"] = _GF.create(32)
    _NB["codes"] = {}
    for arm in NB_ARMS:
        pinned = p1.construct_and_pin(arm, p1.PRODUCTION_CONSTRUCT[arm],
                                      p1.production_rank_fn)
        entry = {}
        for key, m in (("base", 200), ("full", 208)):
            code = pinned["base"] if key == "base" else pinned["full"]
            dense = peg.sparse_to_dense(code["triples"], 1024, m, _NB["field"])
            entry[key] = dense
        _NB["codes"][arm] = entry


def _nb_one(args) -> dict:
    """M0-style real-superframe NB decode: real (a,b), marginal prior, rescue mirror."""
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v28 as _v28,
    )

    source, arm, idx, a_list, b_list = args
    bundle, field = _NB["bundle"], _NB["field"]
    dense = _NB["codes"][arm]
    a = np.asarray(a_list, dtype=np.int64)
    b = np.asarray(b_list, dtype=np.int64)
    x = a & 31
    y = b & 31
    out = []
    for key in ("base", "full"):
        if key == "full" and out and bool(out[0].get("exact_match")):
            break
        prior = s2c.center_rows_prior(b2f.marginal_prior_l2(bundle, b), y)
        from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
            nonbinary_v10_fftqspa as _q,
        )
        sxx = _q.syndrome_of(field, dense[key], x.tolist())
        res = _v28.decode_error_domain_posterior(field, y.tolist(), dense[key],
                                                 sxx, prior, 300)
        x_hat = res.get("x_hat")
        exact = x_hat is not None and bool(np.array_equal(np.asarray(x_hat), x))
        rok = bool(res.get("reconstruction_ok", False))
        out.append({"exact_match": exact, "reconstruction_ok": rok,
                    "status": str(res.get("status")),
                    "iterations": int(res.get("iterations", -1))})
    from comparison_bench.src.comparison_bench.cli.probes_closed import (  # noqa: E402
        m0_realframe_runner as _m0,
    )
    u1mm = int((((np.asarray(_m0.recover_u1(bundle, b, x))) != ((a >> 5) & 31))).sum())
    if out[0]["exact_match"]:
        final, l_rows, rescued = out[0], 200, False
    elif len(out) > 1:
        final, l_rows, rescued = out[1], 208, True
    else:
        final, l_rows, rescued = out[0], 200, False
    exact = bool(final["exact_match"])
    return {"block": idx, "arm": arm, "m_rows": l_rows, "L_EC": 5 * l_rows,
            "rescued": rescued, "exact_ok": exact,
            "undetected": (not exact) and bool(final["reconstruction_ok"]),
            "u1_mismatches": u1mm, "status": final["status"],
            "iterations": final["iterations"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("M5 runs only with --full under authorization")
    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    scalars = read_p1_scalars()
    msd_rows: list[dict] = []
    nb_rows: list[dict] = []
    for label in ("1M", "1p5M", "2M"):
        source = SRC[label]
        series = m0.load_real_series(label)
        supers = m0.superframes(series["a"], series["b"])
        blocks, dropped = group_blocks(supers)
        table = load_train_table(source)
        model = build_conditional_prior_model(table, encoding="NATURAL", order="LSB_FIRST")
        h_plane = plane_conditional_entropies(table)
        matrices, factories = build_msd_matrices(N_MSD, h_plane)
        l_base = sum(int(mt.shape[0]) for mt in matrices)
        jl = root / f"blocks_msd_{label}.jsonl"
        n_fail = n_und = n_res = 0
        t0 = time.perf_counter()
        with jl.open("w", encoding="utf-8", buffering=1) as fh:
            for bi, (alice, bob) in enumerate(blocks):
                r = decode_block_msd(alice, bob, model, matrices, factories, K_MSD)
                n_fail += 0 if r["exact_ok"] else 1
                n_und += 1 if r["undetected"] else 0
                n_res += 1 if r["rescued"] else 0
                fh.write(json.dumps({"source": source, "block": bi, **r,
                                     "L_base": l_base}) + "\n")
        wall = time.perf_counter() - t0
        e_l = l_base + K_MSD * n_res / max(1, len(blocks))
        fer = n_fail / max(1, len(blocks))
        s = scalars[source]
        denom = N_MSD * s["H_AB"]
        kept = N_MSD * s["H_A"] - e_l
        f_p = (e_l + TAG_BITS + kept * fer) / denom
        msd_rows.append({"source": source, "N": N_MSD, "backend": "msd-m2-frozen",
                         "superframes": len(supers), "dropped": dropped,
                         "blocks": len(blocks), "L_base": l_base, "n_rescue": n_res,
                         "failures": n_fail, "undetected": n_und, "E_L": e_l,
                         "FER_exact": fer,
                         "FER_wilson_upper95": wilson_upper(n_fail, max(1, len(blocks))),
                         "f_expected": f_p, "wall_s": wall,
                         "n_pairs_eval": series["n_pairs_eval"]})
        # NB per superframe (pooled x12; worker state via initializer)
        import concurrent.futures as cf

        t1 = time.perf_counter()
        tasks = [(label, arm, si, a.tolist(), b.tolist())
                 for si, (a, b) in enumerate(supers) for arm in NB_ARMS]
        with cf.ProcessPoolExecutor(max_workers=WORKERS_NB, initializer=_nb_init_pool,
                                    initargs=(label,)) as ex:
            recs = list(ex.map(_nb_one, tasks))
        wall_nb = time.perf_counter() - t1
        jl2 = root / f"blocks_nb_{label}.jsonl"
        with jl2.open("w", encoding="utf-8") as fh:
            for r in recs:
                fh.write(json.dumps({"source": source, **r}) + "\n")
        for arm in NB_ARMS:
            armrec = [r for r in recs if r["arm"] == arm]
            nb = len(armrec)
            nf = sum(0 if r["exact_ok"] else 1 for r in armrec)
            nu = sum(1 for r in armrec if r["undetected"])
            nr = sum(1 for r in armrec if r["rescued"])
            e2 = 1000.0 + 40.0 * nr / max(1, nb)
            fer2 = nf / max(1, nb)
            denom2 = N_NB * s["H_AB"]
            kept2 = N_NB * s["H_A"] - e2
            f2 = (e2 + TAG_BITS + kept2 * fer2) / denom2
            nb_rows.append({"source": source, "arm": arm, "N": N_NB,
                            "backend": "nb-marginal-P1", "blocks": nb, "failures": nf,
                            "undetected": nu, "n_rescue": nr, "E_L": e2,
                            "FER_exact": fer2,
                            "FER_wilson_upper95": wilson_upper(nf, max(1, nb)),
                            "f_expected": f2,
                            "u1_mm_total": sum(r["u1_mismatches"] for r in armrec),
                            "wall_s": wall_nb})
    (root / "m5_msd_summary.json").write_text(json.dumps(msd_rows, indent=2), encoding="utf-8")
    (root / "m5_nb_summary.json").write_text(json.dumps(nb_rows, indent=2), encoding="utf-8")
    print(json.dumps({"msd": msd_rows, "nb": nb_rows}, indent=2))


if __name__ == "__main__":
    main()
