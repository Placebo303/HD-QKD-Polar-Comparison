"""M2 targeted incremental disclosure (M2_PACKET.md scope).

Plane-0 only: base PEG-dv3 BP attempt; on plane-0 failure disclose Alice
plane-0 values at the K weakest-prior positions (K public bits) and re-run
base BP with those positions fixed. Other planes frozen M1'b operating.
Disclosure: E[L] = L_base + K*P(rescue attempted); f uses E[L] and final FER.
Fresh seeds (+5000 vs M1'b) = synthetic sample-out for round calibration.
"""

from __future__ import annotations

import argparse
import functools
import json
import math
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (
    SOURCE_SEEDS,
    SOURCES,
    load_train_table,
    plane_conditional_entropies,
    read_p1_scalars,
    wilson_upper,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (
    build_conditional_prior_model,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_m1primea_repetition import (
    make_group_factory,
    spc_matrix,
    split_groups,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (
    build_peg_code,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (
    _syndrome,
    disclose_syndromes,
    make_bp_decoder,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_m1primeb_mixed import (
    G_REST_1024,
    G_REST_16384,
    M1_16384,
    MAX_ITER,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
K_1024 = 100  # probe: 43/43 rescued at K>=100 (N=1024, C_0=96)
K_16384 = 400  # P3 probe: 10/10 rescued at K=400 (T2-2M, C_0=2000)
BASES_1024 = (160,)
BASES_16384 = (1500, 2000)
SEED_OFFSET = 5000
B = 300
TAG_BITS = 64


def run_m2_point(
    *,
    source: str,
    n: int,
    c0_base: int,
    k_rescue: int,
    n_blocks: int,
    seed: int,
    jsonl_path: Path,
) -> dict:
    table = load_train_table(source)
    model = build_conditional_prior_model(table, encoding="NATURAL", order="LSB_FIRST")
    h_plane = plane_conditional_entropies(table)
    bp = functools.partial(make_bp_decoder, max_iter=MAX_ITER)
    matrices = []
    m0 = min(n - 1, max(1, int(math.ceil(n * h_plane[0] + c0_base))))
    matrices.append(build_peg_code(n=n, m=m0, variable_degree=3).parity_check_matrix)
    if n == 1024:
        m1 = min(n - 1, max(1, int(math.ceil(n * h_plane[1] + 32))))
    else:
        m1 = M1_16384
    matrices.append(build_peg_code(n=n, m=m1, variable_degree=3).parity_check_matrix)
    grest = G_REST_1024 if n == 1024 else G_REST_16384
    for _ in range(8):
        groups = split_groups(n, grest)
        matrices.append(spc_matrix(groups, n))
    m_list = [int(mt.shape[0]) for mt in matrices]
    l_base = int(sum(m_list))
    H0d = np.asarray(matrices[0].toarray(), dtype=np.int64)

    flat = table.ravel() / table.sum()
    nnz = np.flatnonzero(flat)
    probs = flat[nnz]
    rows, cols = np.unravel_index(nnz, table.shape)
    rng = np.random.default_rng(seed)

    n_rescue = n_fail = n_und = 0
    s_attempted = [0] * 10
    s_passed = [0] * 10
    t0 = time.perf_counter()
    with jsonl_path.open("a", encoding="utf-8") as fh:
        for b in range(n_blocks):
            pick = rng.choice(nnz.size, size=n, p=probs)
            alice = rows[pick].astype(np.int64)
            bob = cols[pick].astype(np.int64)
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
                if stage == 0:
                    dec = bp(parity_check_matrix=mat, error_channel=ch)
                    err = np.asarray(dec.decode(delta.copy())).astype(np.uint8)
                    rec = np.bitwise_xor(base, err)
                    if not bool(np.array_equal(_syndrome(mat, rec), syndromes)):
                        # targeted rescue round (K disclosed values)
                        n_rescue += 1
                        rescued = True
                        extra = k_rescue
                        w = np.log((1 - np.maximum(ch, 1e-300)) / np.maximum(ch, 1e-300))
                        weak = np.argsort(w, kind="stable")[:k_rescue]
                        base[weak] = ((alice >> 0) & 1).astype(np.uint8)[weak]
                        ch[weak] = 0.0
                        etrue2 = base ^ ((alice >> 0) & 1).astype(np.uint8)
                        delta2 = np.bitwise_xor(syndromes, _syndrome(mat, base))
                        dec2 = bp(parity_check_matrix=mat, error_channel=ch)
                        err2 = np.asarray(dec2.decode(delta2.copy())).astype(np.uint8)
                        rec = np.bitwise_xor(base, err2)
                else:
                    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primeb_mixed import (  # noqa: E402
                        make_group_factory as _mgf,
                    )

                    _ = _mgf  # plane>=1 share the frozen factory interface below
                    fac = _stage_factory(stage, matrices, grest, n, bp)
                    dec = fac(parity_check_matrix=mat, error_channel=ch)
                    err = np.asarray(dec.decode(delta.copy())).astype(np.uint8)
                    rec = np.bitwise_xor(base, err)
                recovered.append(rec)
                ok = bool(np.array_equal(_syndrome(mat, rec), syndromes))
                passed.append(ok)
                if not ok:
                    break
            for s, ok in enumerate(passed):
                s_attempted[s] += 1
                if ok:
                    s_passed[s] += 1
            from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
                _natural_symbols_from_stages,
            )

            full = len(passed) == 10 and all(passed)
            recon = _natural_symbols_from_stages(recovered, model, n) if full else None
            exact = recon is not None and bool(np.array_equal(recon, alice))
            und = full and not exact
            n_fail += 0 if exact else 1
            n_und += 1 if und else 0
            fh.write(json.dumps({
                "source": source, "N": n, "c0_base": c0_base, "k_rescue": k_rescue,
                "block": b, "L_base": l_base, "extra": extra, "rescued": rescued,
                "stages_passed": [bool(v) for v in passed],
                "exact_ok": bool(exact), "undetected": bool(und)}) + "\n")
    wall = time.perf_counter() - t0
    return {"source": source, "N": n, "c0_base": c0_base, "k_rescue": k_rescue,
            "blocks": n_blocks, "L_base": l_base, "n_rescue": n_rescue,
            "failures": n_fail, "undetected": n_und,
            "stage_attempted": s_attempted, "stage_passed": s_passed,
            "wall_s": wall, "s_per_block": wall / n_blocks,
            "backend": "m2-targeted", "seed": seed}


def _stage_factory(stage, matrices, grest, n, bp):
    if stage == 1:
        return bp
    groups = split_groups(n, grest)
    return make_group_factory(groups, "spc", 0)


def summarize_m2(points: list[dict], scalars: dict) -> list[dict]:
    rows = []
    for p in points:
        s = scalars[p["source"]]
        n = p["N"]
        e_l = p["L_base"] + p["k_rescue"] * p["n_rescue"] / p["blocks"]
        fer = p["failures"] / p["blocks"]
        denom = n * s["H_AB"]
        kept = n * s["H_A"] - e_l
        f_point = (e_l + TAG_BITS + kept * fer) / denom
        f_upper = (e_l + TAG_BITS + kept * wilson_upper(p["failures"], p["blocks"])) / denom
        rows.append({**p, "E_L": e_l, "tag_bits": TAG_BITS, "H_A": s["H_A"],
                     "H_AB": s["H_AB"], "FER_exact": fer,
                     "FER_wilson_upper95": wilson_upper(p["failures"], p["blocks"]),
                     "f_expected": f_point, "f_expected_upper95": f_upper})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    scalars = read_p1_scalars()
    points: list[dict] = []
    if args.smoke:
        jl = root / "blocks_m2_smoke.jsonl"
        if jl.exists():
            jl.unlink()
        t = time.perf_counter()
        points.append(run_m2_point(source="T2-1M", n=1024, c0_base=160, k_rescue=K_1024,
                                   n_blocks=6, seed=SOURCE_SEEDS["T2-1M"] + SEED_OFFSET, jsonl_path=jl))
        wall = time.perf_counter() - t
        out = {"mode": "m2-smoke", "smoke_wall_s": wall, "points": summarize_m2(points, scalars)}
        (root / "m2_smoke.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(json.dumps({"smoke_wall_s": wall,
                          "p": {k: points[0][k] for k in ("failures", "n_rescue", "s_per_block")}}, indent=2))
    elif args.full:
        jl = root / "blocks_m2.jsonl"
        if jl.exists():
            jl.unlink()
        for source in SOURCES:
            points.append(run_m2_point(source=source, n=1024, c0_base=160, k_rescue=K_1024,
                                       n_blocks=B, seed=SOURCE_SEEDS[source] + SEED_OFFSET, jsonl_path=jl))
        for source in SOURCES:
            for c0 in BASES_16384:
                points.append(run_m2_point(source=source, n=16384, c0_base=c0, k_rescue=K_16384,
                                           n_blocks=B, seed=SOURCE_SEEDS[source] + SEED_OFFSET, jsonl_path=jl))
        rows = summarize_m2(points, scalars)
        (root / "m2_summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        with (root / "m2_summary.csv").open("w", encoding="utf-8") as fh:
            fh.write("source,N,c0_base,k,backend,blocks,L_base,n_rescue,failures,undetected,E_L,"
                     "FER_exact,FER_wilson_upper95,f_expected,f_expected_upper95,s_per_block,wall_s\n")
            for r in rows:
                fh.write(f"{r['source']},{r['N']},{r['c0_base']},{r['k_rescue']},{r['backend']},{r['blocks']},"
                         f"{r['L_base']},{r['n_rescue']},{r['failures']},{r['undetected']},{r['E_L']:.1f},"
                         f"{r['FER_exact']:.6f},{r['FER_wilson_upper95']:.6f},"
                         f"{r['f_expected']:.4f},{r['f_expected_upper95']:.4f},"
                         f"{r['s_per_block']:.4f},{r['wall_s']:.1f}\n")
        print((root / "m2_summary.csv").read_text(encoding="utf-8"))
    else:
        raise SystemExit("specify --smoke or --full")


if __name__ == "__main__":
    main()
