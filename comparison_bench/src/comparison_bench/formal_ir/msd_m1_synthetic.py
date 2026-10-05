"""M1 synthetic MSD decode loop (EXPLORE, M1_PACKET.md frozen scope).

Calibrated-synthetic only: (A,B) symbols sampled i.i.d. from the accepted R1
TRAIN plug-in joint distribution. No VAL/HOLD/raw/real-frame reads.
Reuses (read-only calls, no source edits):
  formal_ir.msd_sparse_code, formal_ir.msd_conditional_prior,
  formal_ir.msd_syndrome (disclose/receive + ldpc backend factory).
"""

from __future__ import annotations

import argparse
import functools
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy import sparse  # noqa: F401  (kept for explicit sparse provenance)

from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (
    build_conditional_prior_model,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_sparse_code import (
    build_msd_sparse_code,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (
    disclose_syndromes,
    make_bp_decoder,
    receive_syndromes,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
TRAIN_ROOT = REPO_ROOT / "workspace" / "r1_histogram_5e2a91c4"
P1_NUMBERS = (
    REPO_ROOT
    / "docs"
    / "research_cycles"
    / "MSD-REAL-CALIBRATED-MAINLINE"
    / "P1_NUMBERS.json"
)

SOURCES = ("T2-1M", "T2-1.5M", "T2-2M")
SOURCE_SEEDS = {"T2-1M": 20261005, "T2-1.5M": 20261006, "T2-2M": 20261007}
GAPS_1024 = (0.03, 0.06, 0.10, 0.16)
GAPS_16384 = (0.06, 0.10)
TAG_BITS = 64
MAX_ITER = 100
B_1024 = 300
B_16384 = 300

PIN_MAG = 1e6  # same finite stand-in as methods/binary_spa_numpy.py


def load_train_table(source: str) -> np.ndarray:
    """Load the accepted TRAIN plug-in joint counts as a dense float table."""
    z = np.load(TRAIN_ROOT / f"{source}_N_ab_train_sparse.npz")
    table = np.zeros(tuple(int(v) for v in z["shape"]), dtype=np.float64)
    table[z["row"], z["col"]] = z["count"]
    if table.sum() <= 0:
        raise ValueError(f"{source} TRAIN counts are empty")
    return table


def read_p1_scalars() -> dict:
    """Read accepted H_A / H(A|B) per source from the frozen P1 numbers."""
    doc = json.loads(P1_NUMBERS.read_text(encoding="utf-8"))
    out: dict = {}
    for row in doc["analysis_rows"]:
        if (
            row.get("encoding") == "NATURAL"
            and row.get("order") == "LSB_FIRST"
            and row.get("source") in SOURCES
        ):
            ana = row["analysis"]
            out[row["source"]] = {
                "H_A": float(ana["H_A_bits_per_symbol"]),
                "H_AB": float(ana["H_A_given_B_bits_per_symbol"]),
            }
    if set(out) != set(SOURCES):
        raise ValueError("P1 NATURAL/LSB_FIRST rows missing for a source")
    return out


def plane_conditional_entropies(table: np.ndarray) -> list[float]:
    """Plug-in H(bit_k | B, prefix_<k) per plane, natural LSB-first (bits/symbol)."""
    q = table.shape[0]
    total = table.sum()
    prob = table / total
    alice = np.arange(q, dtype=np.int64)
    entropies: list[float] = []
    for bit in range(10):
        n_prefix = 1 << bit
        prefix_of = alice & (n_prefix - 1)
        abit = ((alice >> bit) & 1).astype(np.float64)
        h = 0.0
        for b in range(q):
            col = prob[:, b]
            if col.sum() == 0.0:
                continue
            mass = np.bincount(prefix_of, weights=col, minlength=n_prefix)
            one = np.bincount(prefix_of, weights=col * abit, minlength=n_prefix)
            nz = mass > 0.0
            p1 = np.zeros_like(mass)
            p1[nz] = one[nz] / mass[nz]
            valid = nz & (p1 > 0.0) & (p1 < 1.0)
            pv = p1[valid]
            h -= float((mass[valid] * (pv * np.log2(pv) + (1 - pv) * np.log2(1 - pv))).sum())
        entropies.append(h)
    return entropies


def disclosure_per_plane(h_plane: list[float], n: int, gap: float) -> list[int]:
    """Frozen rate rule: m_k = clamp(ceil(N (h_k + gap)), 1, N-1)."""
    out = []
    for h in h_plane:
        m = int(math.ceil(n * (h + gap)))
        out.append(min(n - 1, max(1, m)))
    return out


def decode_error_min_sum_llr(
    h_dense: np.ndarray,
    syndrome: np.ndarray,
    llr0: np.ndarray,
    max_iter: int = 100,
) -> tuple[np.ndarray, bool, int]:
    """M1-local per-variable-LLR min-sum mirroring binary_spa_numpy rules.

    Same check-to-variable update, syndrome-sign rule, degree-1 pinning
    magnitude, exact-zero sign convention and extrinsic rebuild; only the
    uniform BSC prior is replaced by the caller-supplied per-variable LLR.
    Reference arm only (N=1024 cross-check); never a production claim.
    """
    h = np.asarray(h_dense, dtype=np.uint8)
    d = np.asarray(syndrome, dtype=np.uint8).reshape(-1)
    v0 = np.asarray(llr0, dtype=float).reshape(-1)
    m, n = int(h.shape[0]), int(h.shape[1])
    if d.shape != (m,) or v0.shape != (n,):
        raise ValueError("shape mismatch (fail closed)")
    chk_nb = [np.flatnonzero(h[c]).tolist() for c in range(m)]
    v2c = np.where(h.astype(bool), v0[None, :], 0.0)
    c2v = np.zeros((m, n), dtype=float)
    tot = v0.copy()
    err = (tot < 0).astype(np.uint8)
    if bool(np.array_equal((h @ err) % 2, d)):
        return err, True, 0
    for it in range(1, int(max_iter) + 1):
        for c in range(m):
            nb = chk_nb[c]
            if not nb:
                continue
            msgs = v2c[c, nb]
            signs = np.where(msgs < 0.0, -1.0, 1.0)
            mags = np.abs(msgs)
            flip = -1.0 if int(d[c]) == 1 else 1.0
            for i, v in enumerate(nb):
                others = [k for k in range(len(nb)) if k != i]
                if not others:
                    c2v[c, v] = flip * PIN_MAG
                    continue
                s = flip
                for k in others:
                    s *= signs[k]
                c2v[c, v] = s * float(np.min(mags[others]))
        tot = v0 + c2v.sum(axis=0)
        err = (tot < 0).astype(np.uint8)
        v2c = np.where(h.astype(bool), tot[None, :] - c2v, 0.0)
        if bool(np.array_equal((h @ err) % 2, d)):
            return err, True, int(it)
    return err, False, int(max_iter)


def wilson_upper(k: int, n: int, z: float = 1.96) -> float:
    """Wilson 95% upper bound for a binomial rate."""
    if n == 0:
        return 1.0
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return min(1.0, center + half)


def run_point(
    *,
    source: str,
    n: int,
    gap: float,
    n_blocks: int,
    seed: int,
    backend: str,
    jsonl_path: Path,
    max_iter: int = MAX_ITER,
) -> dict:
    """Run one (source, N, gap) point; append one JSON line per block."""
    table = load_train_table(source)
    model = build_conditional_prior_model(table, encoding="NATURAL", order="LSB_FIRST")
    h_plane = plane_conditional_entropies(table)
    m_list = disclosure_per_plane(h_plane, n, gap)
    matrices = [
        build_msd_sparse_code(
            n=n, m=m, information_degree=min(3, m), tie_offset=stage
        ).parity_check_matrix
        for stage, m in enumerate(m_list)
    ]
    flat = table.ravel() / table.sum()
    nnz_idx = np.flatnonzero(flat)
    probs = flat[nnz_idx]
    rows, cols = np.unravel_index(nnz_idx, table.shape)
    rng = np.random.default_rng(seed)
    factory = functools.partial(make_bp_decoder, max_iter=max_iter)

    n_fail = 0
    n_undetected = 0
    stage_attempted = [0] * 10
    stage_passed = [0] * 10
    t0 = time.perf_counter()
    with jsonl_path.open("a", encoding="utf-8") as fh:
        for b in range(n_blocks):
            pick = rng.choice(nnz_idx.size, size=n, p=probs)
            alice = rows[pick].astype(np.int64)
            bob = cols[pick].astype(np.int64)
            disclosure = disclose_syndromes(alice, model, matrices)
            if backend == "ldpc":
                res = receive_syndromes(
                    model, bob, matrices, disclosure.public_syndromes, factory
                )
            elif backend == "numpy":
                res = _receive_numpy(model, bob, matrices, disclosure.public_syndromes, max_iter)
            else:
                raise ValueError("backend must be ldpc or numpy")
            for s, ok in enumerate(res.attempted_stage_syndrome_passed):
                stage_attempted[s] += 1
                if ok:
                    stage_passed[s] += 1
            exact = (
                res.reconstructed_natural_symbols is not None
                and bool(np.array_equal(res.reconstructed_natural_symbols, alice))
            )
            all_pass = len(res.attempted_stage_syndrome_passed) == 10 and all(
                res.attempted_stage_syndrome_passed
            )
            undetected = all_pass and not exact
            if not exact:
                n_fail += 1
            if undetected:
                n_undetected += 1
            fh.write(
                json.dumps(
                    {
                        "source": source,
                        "N": n,
                        "gap": gap,
                        "block": b,
                        "L_EC": int(sum(m_list)),
                        "stages_passed": [bool(v) for v in res.attempted_stage_syndrome_passed],
                        "exact_ok": bool(exact),
                        "undetected": bool(undetected),
                    }
                )
                + "\n"
            )
    wall = time.perf_counter() - t0
    return {
        "source": source,
        "N": n,
        "gap": gap,
        "blocks": n_blocks,
        "L_EC": int(sum(m_list)),
        "m_per_plane": [int(m) for m in m_list],
        "h_per_plane": [float(h) for h in h_plane],
        "failures": n_fail,
        "undetected": n_undetected,
        "stage_attempted": stage_attempted,
        "stage_passed": stage_passed,
        "wall_s": wall,
        "s_per_block": wall / n_blocks,
        "backend": backend,
        "max_iter": max_iter,
        "seed": seed,
    }


def _receive_numpy(model, bob, matrices, syndromes, max_iter: int):
    """Reference receiver: same staging, M1-local LLR min-sum per stage."""
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (
        adapt_soft_error_prior,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (
        SyndromeReceiverResult,
        _syndrome,
    )

    recovered: list[np.ndarray] = []
    passed: list[bool] = []
    unsupported: list[int] = []
    for stage, matrix in enumerate(matrices):
        prev = (
            np.stack(recovered, axis=0)
            if recovered
            else np.empty((0, bob.size), dtype=np.uint8)
        )
        query = model.query(stage, bob, prev)
        soft = adapt_soft_error_prior(query, llr_floor=1e-6)
        base = soft.base_bits
        delta = np.bitwise_xor(
            np.asarray(syndromes[stage], dtype=np.uint8), _syndrome(matrix, base)
        )
        h_dense = np.asarray(matrix.toarray(), dtype=np.uint8)
        err, _, _ = decode_error_min_sum_llr(h_dense, delta, soft.llr_natural_log, max_iter)
        stage_bits = np.bitwise_xor(base, err)
        recovered.append(stage_bits)
        ok = bool(
            np.array_equal(_syndrome(matrix, stage_bits), np.asarray(syndromes[stage]))
        )
        passed.append(ok)
        unsupported.append(int(np.count_nonzero(query.unsupported)))
        if not ok:
            break
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (
        _natural_symbols_from_stages,
    )

    full = len(passed) == len(matrices) and all(passed)
    return SyndromeReceiverResult(
        recovered_stage_bits=tuple(recovered),
        reconstructed_natural_symbols=(
            _natural_symbols_from_stages(recovered, model, bob.size) if full else None
        ),
        attempted_stage_syndrome_passed=tuple(passed),
        unsupported_counts_by_attempted_stage=tuple(unsupported),
        transmitted_row_count_bits_per_block=sum(int(mt.shape[0]) for mt in matrices),
    )


def summarize(points: list[dict], scalars: dict) -> list[dict]:
    """Attach f_expected (point + Wilson-upper) to each run point."""
    rows = []
    for p in points:
        s = scalars[p["source"]]
        n, lec = p["N"], p["L_EC"]
        fer = p["failures"] / p["blocks"]
        denom = n * s["H_AB"]
        kept = n * s["H_A"] - lec
        f_point = (lec + TAG_BITS + kept * fer) / denom
        f_upper = (lec + TAG_BITS + kept * wilson_upper(p["failures"], p["blocks"])) / denom
        rows.append(
            {
                **p,
                "tag_bits": TAG_BITS,
                "H_A": s["H_A"],
                "H_AB": s["H_AB"],
                "FER_exact": fer,
                "FER_wilson_upper95": wilson_upper(p["failures"], p["blocks"]),
                "f_expected": f_point,
                "f_expected_upper95": f_upper,
            }
        )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)

    import ldpc  # noqa: F401  (backend provenance)

    scalars = read_p1_scalars()
    points: list[dict] = []
    if args.smoke:
        jl = root / "blocks_smoke.jsonl"
        if jl.exists():
            jl.unlink()
        t = time.perf_counter()
        p1 = run_point(
            source="T2-1M", n=1024, gap=0.10, n_blocks=6, seed=SOURCE_SEEDS["T2-1M"],
            backend="ldpc", jsonl_path=jl,
        )
        points.append(p1)
        p2 = run_point(
            source="T2-1M", n=16384, gap=0.10, n_blocks=1, seed=SOURCE_SEEDS["T2-1M"],
            backend="ldpc", jsonl_path=jl,
        )
        points.append(p2)
        p3 = run_point(
            source="T2-1M", n=1024, gap=0.10, n_blocks=2, seed=SOURCE_SEEDS["T2-1M"],
            backend="numpy", jsonl_path=jl,
        )
        points.append(p3)
        smoke_wall = time.perf_counter() - t
        out = {
            "mode": "smoke",
            "smoke_wall_s": smoke_wall,
            "c1024_s_per_block": p1["s_per_block"],
            "c16384_s_per_block": p2["s_per_block"],
            "c1024_numpy_s_per_block": p3["s_per_block"],
            "ldpc_version": getattr(ldpc, "__version__", "n/a"),
            "points": summarize(points, scalars),
        }
        (root / "smoke.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(json.dumps({k: out[k] for k in ("smoke_wall_s", "c1024_s_per_block", "c16384_s_per_block", "c1024_numpy_s_per_block")}, indent=2))
    elif args.full:
        jl = root / "blocks.jsonl"
        if jl.exists():
            jl.unlink()
        for source in SOURCES:
            for gap in GAPS_1024:
                points.append(
                    run_point(
                        source=source, n=1024, gap=gap, n_blocks=B_1024,
                        seed=SOURCE_SEEDS[source], backend="ldpc", jsonl_path=jl,
                    )
                )
        points.append(
            run_point(
                source="T2-1M", n=1024, gap=0.10, n_blocks=30,
                seed=SOURCE_SEEDS["T2-1M"] + 1000, backend="numpy", jsonl_path=jl,
            )
        )
        for source in SOURCES:
            for gap in GAPS_16384:
                points.append(
                    run_point(
                        source=source, n=16384, gap=gap, n_blocks=B_16384,
                        seed=SOURCE_SEEDS[source], backend="ldpc", jsonl_path=jl,
                    )
                )
        rows = summarize(points, scalars)
        (root / "m1_summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        with (root / "m1_summary.csv").open("w", encoding="utf-8") as fh:
            fh.write(
                "source,N,gap,backend,blocks,L_EC,failures,undetected,"
                "FER_exact,FER_wilson_upper95,f_expected,f_expected_upper95,"
                "s_per_block,wall_s\n"
            )
            for r in rows:
                fh.write(
                    f"{r['source']},{r['N']},{r['gap']},{r['backend']},{r['blocks']},"
                    f"{r['L_EC']},{r['failures']},{r['undetected']},"
                    f"{r['FER_exact']:.6f},{r['FER_wilson_upper95']:.6f},"
                    f"{r['f_expected']:.4f},{r['f_expected_upper95']:.4f},"
                    f"{r['s_per_block']:.3f},{r['wall_s']:.1f}\n"
                )
        print((root / "m1_summary.csv").read_text(encoding="utf-8"))
    else:
        raise SystemExit("specify --smoke or --full")


if __name__ == "__main__":
    main()
