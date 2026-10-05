"""M1'b mixed per-plane codes: PEG-dv3 (planes 0-1) + SPC exact-ML (rest).

Reuses UNCHANGED: TRAIN/prior/disclose/receive/seeds/f-formula/summarize
from msd_m1_synthetic; group builders + GroupML factories from
msd_m1primea_repetition; PEG from msd_peg_code. Scope: M1_PRIMEB_PACKET.md.
"""

from __future__ import annotations

import argparse
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
    summarize,
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
    disclose_syndromes,
    make_bp_decoder,
    receive_syndromes,
)
import functools

REPO_ROOT = Path(__file__).resolve().parents[4]
C0_LADDER_1024 = (96, 128, 160, 192)
C0_LADDER_16384 = (1500, 2000, 2569)  # D3 measured: same-rate R_0=0.055 (C_0=2569) 10/10
C1_POINTS = (16, 32)
G_REST_1024 = 64
G_REST_16384 = 256  # D3 full-chain 10/10 with g=256
M1_16384 = 600  # D3 full-chain 10/10 (dc=82 OK); ceil-rule gives dc=252 (BP-hostile)
B = 300
MAX_ITER = 200
WALL_CAP_S = 21600


def build_mixed_point(
    n: int, h_plane: list[float], c0: int, c1: int, g_rest: int
) -> tuple[list, list, list[str], list[int]]:
    """Build per-plane (matrix, factory, kind) for one ladder point."""
    matrices = []
    factories = []
    kinds = []
    bp = functools.partial(make_bp_decoder, max_iter=MAX_ITER)
    for stage, h in enumerate(h_plane):
        if stage == 0:
            m = min(n - 1, max(1, int(math.ceil(n * h + c0))))
            mat = build_peg_code(n=n, m=m, variable_degree=3).parity_check_matrix
            matrices.append(mat)
            factories.append(bp)
            kinds.append(f"peg-dv3/C0={c0}")
        elif stage == 1:
            if n == 1024:
                m = min(n - 1, max(1, int(math.ceil(n * h + c1))))
            else:
                m = M1_16384  # frozen: ceil-rule under-provisions check sparsity at N=16384
            mat = build_peg_code(n=n, m=m, variable_degree=3).parity_check_matrix
            matrices.append(mat)
            factories.append(bp)
            kinds.append(f"peg-dv3/C1={c1}")
        else:
            groups = split_groups(n, g_rest)
            mat = spc_matrix(groups, n)
            matrices.append(mat)
            factories.append(make_group_factory(groups, "spc", 0))
            kinds.append(f"spc/g{g_rest}")
    return matrices, factories, kinds, [int(mt.shape[0]) for mt in matrices]


def run_mixed_point(
    *,
    source: str,
    n: int,
    c0: int,
    c1: int,
    g_rest: int,
    n_blocks: int,
    seed: int,
    jsonl_path: Path,
) -> dict:
    table = load_train_table(source)
    model = build_conditional_prior_model(table, encoding="NATURAL", order="LSB_FIRST")
    h_plane = plane_conditional_entropies(table)
    matrices, factories, kinds, m_list = build_mixed_point(n, h_plane, c0, c1, g_rest)
    flat = table.ravel() / table.sum()
    nnz = np.flatnonzero(flat)
    probs = flat[nnz]
    rows, cols = np.unravel_index(nnz, table.shape)
    rng = np.random.default_rng(seed)

    def mux_factory(*, parity_check_matrix, error_channel):
        idx = mux_factory.calls[0]
        mux_factory.calls[0] += 1
        return factories[idx](parity_check_matrix=parity_check_matrix, error_channel=error_channel)

    n_fail = n_und = 0
    attempted = [0] * 10
    passed = [0] * 10
    t0 = time.perf_counter()
    with jsonl_path.open("a", encoding="utf-8") as fh:
        for b in range(n_blocks):
            mux_factory.calls = [0]
            pick = rng.choice(nnz.size, size=n, p=probs)
            alice = rows[pick].astype(np.int64)
            bob = cols[pick].astype(np.int64)
            dis = disclose_syndromes(alice, model, matrices)
            res = receive_syndromes(model, bob, matrices, dis.public_syndromes, mux_factory)
            for s, ok in enumerate(res.attempted_stage_syndrome_passed):
                attempted[s] += 1
                if ok:
                    passed[s] += 1
            exact = res.reconstructed_natural_symbols is not None and bool(
                np.array_equal(res.reconstructed_natural_symbols, alice)
            )
            all_pass = len(res.attempted_stage_syndrome_passed) == 10 and all(
                res.attempted_stage_syndrome_passed
            )
            und = all_pass and not exact
            n_fail += 0 if exact else 1
            n_und += 1 if und else 0
            fh.write(
                json.dumps(
                    {
                        "source": source, "N": n, "c0": c0, "c1": c1, "g_rest": g_rest,
                        "block": b, "L_EC": int(sum(m_list)),
                        "stages_passed": [bool(v) for v in res.attempted_stage_syndrome_passed],
                        "exact_ok": bool(exact), "undetected": bool(und),
                    }
                )
                + "\n"
            )
    wall = time.perf_counter() - t0
    return {
        "source": source, "N": n, "gap": f"peg-C0:{c0}/C1:{c1}/SPC:{g_rest}",
        "blocks": n_blocks, "L_EC": int(sum(m_list)), "m_per_plane": m_list,
        "h_per_plane": [float(h) for h in h_plane], "kinds": kinds,
        "failures": n_fail, "undetected": n_und,
        "stage_attempted": attempted, "stage_passed": passed,
        "wall_s": wall, "s_per_block": wall / n_blocks,
        "backend": "pegBP-spcML", "max_iter": MAX_ITER, "seed": seed,
    }


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
        jl = root / "blocks_primeb_smoke.jsonl"
        if jl.exists():
            jl.unlink()
        t = time.perf_counter()
        points.append(
            run_mixed_point(source="T2-1M", n=1024, c0=160, c1=32, g_rest=G_REST_1024,
                            n_blocks=6, seed=SOURCE_SEEDS["T2-1M"], jsonl_path=jl)
        )
        points.append(
            run_mixed_point(source="T2-1M", n=16384, c0=160, c1=32, g_rest=G_REST_16384,
                            n_blocks=2, seed=SOURCE_SEEDS["T2-1M"], jsonl_path=jl)
        )
        wall = time.perf_counter() - t
        out = {"mode": "primeb-smoke", "smoke_wall_s": wall, "points": summarize(points, scalars)}
        (root / "primeb_smoke.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(json.dumps({"smoke_wall_s": wall,
                          "p1024": {k: points[0][k] for k in ("failures", "undetected", "s_per_block", "L_EC")},
                          "p16384": {k: points[1][k] for k in ("failures", "undetected", "s_per_block", "L_EC")}}, indent=2))
    elif args.full:
        jl = root / "blocks_primeb.jsonl"
        if jl.exists():
            jl.unlink()
        for source in SOURCES:
            for c0 in C0_LADDER_1024:
                points.append(
                    run_mixed_point(source=source, n=1024, c0=c0, c1=32, g_rest=G_REST_1024,
                                    n_blocks=B, seed=SOURCE_SEEDS[source], jsonl_path=jl)
                )
        points.append(
            run_mixed_point(source="T2-1M", n=1024, c0=160, c1=16, g_rest=G_REST_1024,
                            n_blocks=B, seed=SOURCE_SEEDS["T2-1M"] + 500, jsonl_path=jl)
        )
        for source in SOURCES:
            for c0 in C0_LADDER_16384:
                points.append(
                    run_mixed_point(source=source, n=16384, c0=c0, c1=32, g_rest=G_REST_16384,
                                    n_blocks=B, seed=SOURCE_SEEDS[source], jsonl_path=jl)
                )
        rows = summarize(points, scalars)
        (root / "m1primeb_summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        with (root / "m1primeb_summary.csv").open("w", encoding="utf-8") as fh:
            fh.write("source,N,gap,backend,blocks,L_EC,failures,undetected,FER_exact,"
                     "FER_wilson_upper95,f_expected,f_expected_upper95,s_per_block,wall_s\n")
            for r in rows:
                fh.write(f"{r['source']},{r['N']},{r['gap']},{r['backend']},{r['blocks']},"
                         f"{r['L_EC']},{r['failures']},{r['undetected']},"
                         f"{r['FER_exact']:.6f},{r['FER_wilson_upper95']:.6f},"
                         f"{r['f_expected']:.4f},{r['f_expected_upper95']:.4f},"
                         f"{r['s_per_block']:.4f},{r['wall_s']:.1f}\n")
        print((root / "m1primeb_summary.csv").read_text(encoding="utf-8"))
    else:
        raise SystemExit("specify --smoke or --full")


if __name__ == "__main__":
    main()
