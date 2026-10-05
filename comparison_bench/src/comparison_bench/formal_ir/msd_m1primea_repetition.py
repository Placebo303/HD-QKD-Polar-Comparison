"""M1'a repetition/SPC exact-ML per-plane codes (M1_PRIMEA_PACKET.md scope).

Reuses UNCHANGED: load_train_table, plane_conditional_entropies,
disclose_syndromes, receive_syndromes, summarize, wilson_upper, f formula.
New: group-code H builders + exact-ML decoder factories honoring the
factory(parity_check_matrix=, error_channel=) → decode(delta) interface.
"""

from __future__ import annotations

import argparse
import functools
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy import sparse

from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (
    SOURCE_SEEDS,
    SOURCES,
    TAG_BITS,
    load_train_table,
    plane_conditional_entropies,
    read_p1_scalars,
    summarize,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (
    build_conditional_prior_model,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (
    disclose_syndromes,
    receive_syndromes,
)

REPO_ROOT = Path(__file__).resolve().parents[4]

# Frozen ladders (group sizes). Plane classes by plug-in h_k (bits/symbol).
PLANE0_GS = (5, 7, 9, 11)
PLANE1_GS = (2, 3, 4)
SPC_GS = (32, 64, 128)
B_1024 = 300
B_16384 = 300
WALL_CAP_S = 21600


def split_groups(n: int, g: int) -> list[np.ndarray]:
    """Consecutive groups of size g; the tail merges into the last group."""
    n_full = n // g
    groups = [np.arange(i * g, (i + 1) * g, dtype=np.int64) for i in range(n_full)]
    tail = n % g
    if tail:
        groups[-1] = np.concatenate([groups[-1], np.arange(n - tail, n, dtype=np.int64)])
    return groups


def repetition_matrix(groups: list[np.ndarray], n: int) -> sparse.csr_matrix:
    """Adjacent-difference checks per group: codewords are 0^g / 1^g."""
    rows: list[int] = []
    cols: list[int] = []
    r = 0
    for grp in groups:
        for a, b in zip(grp[:-1], grp[1:]):
            rows += [r, r]
            cols += [int(a), int(b)]
            r += 1
    m = sparse.coo_matrix(
        (np.ones(len(rows), dtype=np.uint8), (np.asarray(rows), np.asarray(cols))),
        shape=(r, n),
        dtype=np.uint8,
    ).tocsr()
    m.sort_indices()
    return m


def spc_matrix(groups: list[np.ndarray], n: int) -> sparse.csr_matrix:
    """One parity check per group."""
    rows: list[int] = []
    cols: list[int] = []
    for r, grp in enumerate(groups):
        rows += [r] * len(grp)
        cols += [int(v) for v in grp]
    m = sparse.coo_matrix(
        (np.ones(len(rows), dtype=np.uint8), (np.asarray(rows), np.asarray(cols))),
        shape=(len(groups), n),
        dtype=np.uint8,
    ).tocsr()
    m.sort_indices()
    return m


def _weights(error_channel: np.ndarray) -> np.ndarray:
    p = np.asarray(error_channel, dtype=np.float64)
    w = np.empty_like(p)
    zero = p <= 0.0
    one = p >= 1.0
    mid = ~(zero | one)
    w[zero] = 1e12
    w[one] = -1e12  # p=1: e_i=1 is free; handled by sign flip below
    w[mid] = np.log((1 - p[mid]) / p[mid])
    return w


def ml_repetition_group(w: np.ndarray, delta: np.ndarray) -> np.ndarray:
    """Exact min-weight e with adjacent-difference syndrome delta (chain DP).

    Checks: e[i] XOR e[i+1] = delta[i]. Two global assignments (e[0]=0/1);
    pick the cheaper syndrome-consistent one.
    """
    g = w.size
    best = None
    for first in (0, 1):
        e = np.empty(g, dtype=np.uint8)
        e[0] = first
        for i in range(g - 1):
            e[i + 1] = e[i] ^ int(delta[i])
        cost = float(np.sum(w[e == 1]))
        if best is None or cost < best[0]:
            best = (cost, e)
    assert best is not None
    return best[1]


def ml_spc_group(w: np.ndarray, parity: int) -> np.ndarray:
    """Exact min-weight e with single parity syndrome bit (general weights).

    Start from all negative-weight bits set; flip the min-|w| bit iff the
    parity mismatches. Exact for any real weights.
    """
    g = w.size
    e = (w < 0.0).astype(np.uint8)
    if int(np.sum(e)) % 2 != int(parity):
        e[int(np.argmin(np.abs(w)))] ^= 1
    return e


class GroupMLDecoder:
    """Exact-ML decoder over explicit groups (factory-compatible)."""

    def __init__(
        self,
        groups: list[np.ndarray],
        kind: str,
        error_channel: np.ndarray,
        row_base: int,
    ) -> None:
        self._groups = groups
        self._kind = kind
        self._w = _weights(np.asarray(error_channel, dtype=np.float64).reshape(-1))
        self._row_base = row_base

    def decode(self, delta: np.ndarray) -> np.ndarray:
        d = np.asarray(delta, dtype=np.uint8).reshape(-1)
        n = self._w.size
        err = np.zeros(n, dtype=np.uint8)
        r = self._row_base
        for grp in self._groups:
            w = self._w[grp]
            if self._kind == "repetition":
                seg = d[r : r + len(grp) - 1]
                err[grp] = ml_repetition_group(w, seg)
                r += len(grp) - 1
            else:
                err[grp] = ml_spc_group(w, int(d[r]))
                r += 1
        return err


def make_group_factory(
    groups: list[np.ndarray], kind: str, row_base: int
):
    """Factory(parity_check_matrix=, error_channel=) honoring the receiver interface."""

    def factory(*, parity_check_matrix, error_channel):
        return GroupMLDecoder(groups, kind, error_channel, row_base)

    return factory


def plane_class(h: float) -> str:
    if h > 0.05:
        return "repetition"
    if h > 0.0:
        return "repetition"
    return "spc"


def build_point_matrices(
    n: int, h_plane: list[float], g0: int, g1: int, g_rest: int
) -> tuple[list[sparse.csr_matrix], list, list[str]]:
    """Build per-plane H + factories; returns (matrices, factories, kinds)."""
    matrices = []
    factories = []
    kinds = []
    row = 0
    for stage, h in enumerate(h_plane):
        g = g0 if stage == 0 else (g1 if stage == 1 else g_rest)
        groups = split_groups(n, g)
        kind = "repetition" if h > 0.0 else "spc"
        mat = repetition_matrix(groups, n) if kind == "repetition" else spc_matrix(groups, n)
        matrices.append(mat)
        # NOTE: receive_syndromes passes a stage-local delta to decode(), so
        # the in-decoder row base is always 0 (factories are already per stage).
        factories.append(make_group_factory(groups, kind, 0))
        kinds.append(f"{kind}/g{g}")
        row += mat.shape[0]
    return matrices, factories, kinds


def run_rep_point(
    *,
    source: str,
    n: int,
    g0: int,
    g1: int,
    g_rest: int,
    n_blocks: int,
    seed: int,
    jsonl_path: Path,
) -> dict:
    table = load_train_table(source)
    model = build_conditional_prior_model(table, encoding="NATURAL", order="LSB_FIRST")
    h_plane = plane_conditional_entropies(table)
    matrices, factories, kinds = build_point_matrices(n, h_plane, g0, g1, g_rest)
    m_list = [int(mt.shape[0]) for mt in matrices]
    flat = table.ravel() / table.sum()
    nnz = np.flatnonzero(flat)
    probs = flat[nnz]
    rows, cols = np.unravel_index(nnz, table.shape)
    rng = np.random.default_rng(seed)

    n_fail = n_und = 0
    attempted = [0] * 10
    passed = [0] * 10
    # receive_syndromes takes ONE factory; multiplex per stage via closure.
    fac_list = factories

    def mux_factory(*, parity_check_matrix, error_channel):
        idx = mux_factory.calls[0]
        mux_factory.calls[0] += 1
        return fac_list[idx](parity_check_matrix=parity_check_matrix, error_channel=error_channel)

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
                        "source": source, "N": n, "g0": g0, "g1": g1, "g_rest": g_rest,
                        "block": b, "L_EC": int(sum(m_list)),
                        "stages_passed": [bool(v) for v in res.attempted_stage_syndrome_passed],
                        "exact_ok": bool(exact), "undetected": bool(und),
                    }
                )
                + "\n"
            )
    wall = time.perf_counter() - t0
    return {
        "source": source, "N": n, "gap": f"rep-g0:{g0}/g1:{g1}/gr:{g_rest}",
        "blocks": n_blocks, "L_EC": int(sum(m_list)), "m_per_plane": m_list,
        "h_per_plane": [float(h) for h in h_plane], "kinds": kinds,
        "failures": n_fail, "undetected": n_und,
        "stage_attempted": attempted, "stage_passed": passed,
        "wall_s": wall, "s_per_block": wall / n_blocks,
        "backend": "exact-ML", "max_iter": 0, "seed": seed,
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
        jl = root / "blocks_primea_smoke.jsonl"
        if jl.exists():
            jl.unlink()
        t = time.perf_counter()
        points.append(
            run_rep_point(source="T2-1M", n=1024, g0=9, g1=3, g_rest=64,
                          n_blocks=6, seed=SOURCE_SEEDS["T2-1M"], jsonl_path=jl)
        )
        points.append(
            run_rep_point(source="T2-1M", n=16384, g0=9, g1=3, g_rest=64,
                          n_blocks=2, seed=SOURCE_SEEDS["T2-1M"], jsonl_path=jl)
        )
        wall = time.perf_counter() - t
        out = {"mode": "primea-smoke", "smoke_wall_s": wall,
               "points": summarize(points, scalars)}
        (root / "primea_smoke.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(json.dumps({"smoke_wall_s": wall,
                          "p0": {k: points[0][k] for k in ("failures", "s_per_block", "L_EC")},
                          "p1": {k: points[1][k] for k in ("failures", "s_per_block", "L_EC")}}, indent=2))
    elif args.full:
        jl = root / "blocks_primea.jsonl"
        if jl.exists():
            jl.unlink()
        for source in SOURCES:
            for g0 in PLANE0_GS:
                points.append(
                    run_rep_point(source=source, n=1024, g0=g0, g1=3, g_rest=64,
                                  n_blocks=B_1024, seed=SOURCE_SEEDS[source], jsonl_path=jl)
                )
        for source in SOURCES:
            for g1 in PLANE1_GS:
                if g1 == 3:
                    continue  # covered by the g0 ladder rows
                points.append(
                    run_rep_point(source=source, n=1024, g0=9, g1=g1, g_rest=64,
                                  n_blocks=B_1024, seed=SOURCE_SEEDS[source] + 500, jsonl_path=jl)
                )
        for source in SOURCES:
            for g_rest in SPC_GS:
                if g_rest == 64:
                    continue  # covered
                points.append(
                    run_rep_point(source=source, n=1024, g0=9, g1=3, g_rest=g_rest,
                                  n_blocks=B_1024, seed=SOURCE_SEEDS[source] + 700, jsonl_path=jl)
                )
        for source in SOURCES:
            for g0 in (7, 9, 11):
                points.append(
                    run_rep_point(source=source, n=16384, g0=g0, g1=3, g_rest=64,
                                  n_blocks=B_16384, seed=SOURCE_SEEDS[source], jsonl_path=jl)
                )
        rows = summarize(points, scalars)
        (root / "m1primea_summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        with (root / "m1primea_summary.csv").open("w", encoding="utf-8") as fh:
            fh.write("source,N,gap,backend,blocks,L_EC,failures,undetected,FER_exact,"
                     "FER_wilson_upper95,f_expected,f_expected_upper95,s_per_block,wall_s\n")
            for r in rows:
                fh.write(f"{r['source']},{r['N']},{r['gap']},{r['backend']},{r['blocks']},"
                         f"{r['L_EC']},{r['failures']},{r['undetected']},"
                         f"{r['FER_exact']:.6f},{r['FER_wilson_upper95']:.6f},"
                         f"{r['f_expected']:.4f},{r['f_expected_upper95']:.4f},"
                         f"{r['s_per_block']:.4f},{r['wall_s']:.1f}\n")
        print((root / "m1primea_summary.csv").read_text(encoding="utf-8"))
    else:
        raise SystemExit("specify --smoke or --full")


if __name__ == "__main__":
    main()
