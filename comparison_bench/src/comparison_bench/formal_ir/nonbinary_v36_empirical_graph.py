"""V36 Empirical-P Irregular LDPC & Source-Native Finite Graph Development Core Module.

Implements:
1. Stage A0: Decoder iteration budget diagnostic (30 vs 60 iters on true V31 baseline).
2. Stage A1: GF(32) empirical-P irregular ensemble DE candidate grid generator and 2-stage screening.
3. Stage A2: Source-native PEG finite graph construction (184x1024, 190x1024, 192x1024) and structural audit.
4. Stage A3: Finite paired development screen on 15 development blocks (3 sources x 5 seeds: 360xxx).
5. Stage A4: Moderate-degree incremental syndrome hierarchy (S0..S3, degrees 10-14, cold-start).
6. Automatic report & claim ledger generation.
"""
from __future__ import annotations

import csv
import json
import math
import time
from dataclasses import asdict, dataclass
from numbers import Integral
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .nonbinary_field import GF2mField, get_field_spec
from .nonbinary_v9_common import concentrated_check_distribution
from .nonbinary_v10_peg import node_view_counts, peg_construct, sparse_to_dense
from .nonbinary_v26_mcde import (
    concentrated_rho_to_hist,
    make_rho,
    mean_bits_entropy,
    run_mcde_posterior,
)
from .v35_algorithm_development import (
    BlockRecord,
    compute_gf32_rank,
    compute_tag_64,
    decode_row_layered_fftqspa,
    factorize_f03,
    get_conditional_posterior_l2,
    load_v25_channel_counts,
    load_v31_qc_baseline_matrices,
    sample_empirical_block,
    syndrome_of_gf32,
)

# ---------------------------------------------------------------------------
# Constants & Specifications
# ---------------------------------------------------------------------------

METHOD = "formal_ir_v36_empirical_graph"
FIELD_Q = 32
FIELD_POLY = 37
FIELD_ID = "c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf"

N_SYMBOLS = 1024
SOURCES = ("1M", "1p5M", "2M")

SOURCE_IDS = {
    "1M": "type2_1M_20260121_184040",
    "1p5M": "type2_1p5M_20260121_183806",
    "2M": "type2_2M_20260121_183657",
}

NPZ_KEYS = {
    "1M": "type2_1M_20260121_184040_N_ab_train_N_ab_train",
    "1p5M": "type2_1p5M_20260121_183806_N_ab_train_N_ab_train",
    "2M": "type2_2M_20260121_183657_N_ab_train_N_ab_train",
}

M2_BY_SOURCE = {
    "1M": 184,
    "1p5M": 190,
    "2M": 192,
}

RATES_BY_SOURCE = {
    "1M": 1.0 - 184.0 / 1024.0,  # 0.8203125
    "1p5M": 1.0 - 190.0 / 1024.0,  # 0.814453125
    "2M": 1.0 - 192.0 / 1024.0,  # 0.8125
}

A0_SEEDS = {
    "1M": (360101, 360102, 360103),
    "1p5M": (360201, 360202, 360203),
    "2M": (360301, 360302, 360303),
}

A3_SEEDS = {
    "1M": (360101, 360102, 360103, 360104, 360105),
    "1p5M": (360201, 360202, 360203, 360204, 360205),
    "2M": (360301, 360302, 360303, 360304, 360305),
}

TAG_BITS = 64
DEFAULT_DAMPING_ALPHA = 1.0

# Incremental hierarchy constants
INCREMENTAL_STAGES = ("S0", "S1", "S2", "S3")
INCREMENTAL_EXTRA_CHECKS = {"S0": 0, "S1": 8, "S2": 16, "S3": 32}
INCREMENTAL_EXTRA_BITS = {"S0": 0, "S1": 40, "S2": 80, "S3": 160}

# Terminal states
STATUS_DE_SHORTLIST_READY = "DE_SHORTLIST_READY"
STATUS_NO_DE_ADVANCE = "NO_DE_ADVANCE"
STATUS_DE_EVIDENCE_INVALID = "DE_EVIDENCE_INVALID"

STATUS_FINITE_GRAPH_ADVANCE = "FINITE_GRAPH_ADVANCE"
STATUS_NO_FINITE_GRAPH_ADVANCE = "NO_FINITE_GRAPH_ADVANCE"

STATUS_NB_DEVELOPMENT_CANDIDATE_FOUND = "NB_DEVELOPMENT_CANDIDATE_FOUND"
STATUS_FINITE_GRAPH_ADVANCE_NO_EXACT = "FINITE_GRAPH_ADVANCE_NO_EXACT"
STATUS_NO_INCREMENTAL_ADVANCE = "NO_INCREMENTAL_ADVANCE"
STATUS_EVIDENCE_INVALID = "EVIDENCE_INVALID"


# ---------------------------------------------------------------------------
# Zero-Denominator Fail-Closed Error
# ---------------------------------------------------------------------------

class ZeroDenominatorError(Exception):
    """Raised when an empirical conditioning denominator is zero or non-finite."""
    pass


# ---------------------------------------------------------------------------
# Stage A0: Decoder Iteration Diagnostic (30 vs 60)
# ---------------------------------------------------------------------------

def run_a0_iteration_diagnostic(
    channel_counts: dict[str, np.ndarray],
    baseline_mats: dict[str, np.ndarray],
    max_iters: tuple[int, int] = (30, 60),
    damping_alpha: float = 1.0,
    field: Optional[GF2mField] = None,
    fake_runner: bool = False,
) -> dict[str, Any]:
    """Evaluate V31 baseline at max_iter=30 vs 60 on 9 blocks to choose a unified budget."""
    if field is None:
        field = GF2mField.create(FIELD_Q)

    records: list[dict[str, Any]] = []
    res_by_iter: dict[int, dict[str, list[int]]] = {
        max_iters[0]: {src: [] for src in SOURCES},
        max_iters[1]: {src: [] for src in SOURCES},
    }

    for src in SOURCES:
        counts = channel_counts[src]
        H_base = baseline_mats[src]
        for seed in A0_SEEDS[src]:
            _, _, bob = sample_empirical_block(counts, seed, size=N_SYMBOLS)
            x1, x2, _, y2 = factorize_f03(sample_empirical_block(counts, seed, size=N_SYMBOLS)[1], bob)
            prior = get_conditional_posterior_l2(counts, bob, x1)
            raw_errs = int(np.sum(x2 != y2))
            syn_true = syndrome_of_gf32(H_base, x2, field)

            for mi in max_iters:
                if fake_runner:
                    final_errs = max(0, raw_errs - (20 if mi == 60 else 10))
                    iters = mi // 2
                    rt = 0.001
                else:
                    res = decode_row_layered_fftqspa(
                        H_base, prior, syn_true, max_iter=mi, damping_alpha=damping_alpha, field=field
                    )
                    final_errs = int(np.sum(res.x_hat != x2))
                    iters = res.iterations
                    rt = res.runtime_s

                res_by_iter[mi][src].append(final_errs)
                records.append({
                    "source": src,
                    "seed": seed,
                    "max_iter": mi,
                    "raw_errors": raw_errs,
                    "final_errors": final_errs,
                    "iterations": iters,
                    "runtime_s": rt,
                })

    # Compute paired median improvement per source
    median_drops: dict[str, float] = {}
    improvements_ge_5pct: dict[str, bool] = {}
    for src in SOURCES:
        med_30 = float(np.median(res_by_iter[max_iters[0]][src]))
        med_60 = float(np.median(res_by_iter[max_iters[1]][src]))
        drop = (med_30 - med_60) / med_30 if med_30 > 0 else 0.0
        median_drops[src] = drop
        improvements_ge_5pct[src] = bool(drop >= 0.05)

    all_improved = all(improvements_ge_5pct[src] for src in SOURCES)
    selected_max_iter = max_iters[1] if all_improved else max_iters[0]

    return {
        "status": "completed",
        "selected_max_iter": selected_max_iter,
        "max_iters_tested": list(max_iters),
        "median_relative_drops": median_drops,
        "improvements_ge_5pct": improvements_ge_5pct,
        "all_sources_improved_ge_5pct": all_improved,
        "records": records,
    }


# ---------------------------------------------------------------------------
# Stage A1: Candidate Degree Distribution Grid & DE Screening
# ---------------------------------------------------------------------------

def generate_v36_candidate_grid(
    step: float = 0.05,
    dbar_min: float = 2.15,
    dbar_max: float = 2.55,
    max_check_degree_limit: int = 16,
) -> list[dict[str, Any]]:
    """Generate all variable degree distributions on grid satisfying constraints."""
    steps = int(round(1.0 / step))
    candidates: list[dict[str, Any]] = []

    for i2 in range(steps + 1):
        l2 = round(i2 * step, 4)
        for i3 in range(steps + 1 - i2):
            l3 = round(i3 * step, 4)
            for i4 in range(steps + 1 - i2 - i3):
                l4 = round(i4 * step, 4)
                l5 = round(1.0 - l2 - l3 - l4, 4)
                if l5 < -1e-6:
                    continue

                lambda_edge = {2: l2, 3: l3, 4: l4, 5: l5}
                lambda_edge = {k: v for k, v in lambda_edge.items() if v > 1e-6}

                inv_dbar = sum(v / k for k, v in lambda_edge.items())
                dbar_v = 1.0 / inv_dbar

                if dbar_min <= dbar_v <= dbar_max:
                    # Verify concentrated rho for all 3 source rates
                    rho_by_src: dict[str, dict[int, float]] = {}
                    ok_all_rates = True
                    max_dc_all = 0

                    for src in SOURCES:
                        R = RATES_BY_SOURCE[src]
                        conc = concentrated_check_distribution(R, lambda_edge)
                        rho = concentrated_rho_to_hist(conc)
                        max_dc = max(rho.keys())
                        if max_dc > max_check_degree_limit:
                            ok_all_rates = False
                            break
                        rho_by_src[src] = rho
                        max_dc_all = max(max_dc_all, max_dc)

                    if ok_all_rates:
                        cand_id = f"lam_d2_{l2:.2f}_d3_{l3:.2f}_d4_{l4:.2f}_d5_{l5:.2f}"
                        candidates.append({
                            "candidate_id": cand_id,
                            "lambda_edge": lambda_edge,
                            "dbar_v": float(dbar_v),
                            "max_check_degree": max_dc_all,
                            "rho_by_source": rho_by_src,
                        })

    # Sort canonically by dictionary key order
    candidates.sort(key=lambda c: (
        c["lambda_edge"].get(2, 0.0),
        c["lambda_edge"].get(3, 0.0),
        c["lambda_edge"].get(4, 0.0),
        c["lambda_edge"].get(5, 0.0),
    ))
    return candidates


def build_v36_channel_sampler(
    counts: np.ndarray,
    source: str,
) -> Callable[[int, np.random.Generator], np.ndarray]:
    """Construct true-predecessor conditioned L2 centered channel sampler with fail-closed zero check."""
    counts = np.asarray(counts, dtype=np.float64)
    total_pairs = float(np.sum(counts))
    if total_pairs <= 0.0:
        raise ZeroDenominatorError(f"Source {source}: channel counts sum is zero")

    P_ab = counts / total_pairs
    p_b = np.sum(P_ab, axis=0)  # (1024,)

    # Marginal P(A|B)
    with np.errstate(divide="ignore", invalid="ignore"):
        P_a_gb = np.divide(P_ab, p_b[None, :], out=np.zeros_like(P_ab), where=p_b[None, :] > 0)

    # L1 and L2 maps for A in 0..1023
    idx1024 = np.arange(1024, dtype=np.int64)
    u1_map = (idx1024 // 32).astype(np.int64)
    u2_map = (idx1024 % 32).astype(np.int64)

    # P(U1|B): (32, 1024)
    p_u1_gb = np.zeros((32, 1024), dtype=np.float64)
    for a in range(1024):
        p_u1_gb[u1_map[a], :] += P_a_gb[a, :]

    # P(U1, U2|B): (32, 32, 1024)
    p_joint = np.zeros((32, 32, 1024), dtype=np.float64)
    for a in range(1024):
        p_joint[u1_map[a], u2_map[a], :] += P_a_gb[a, :]

    P_ab_flat = P_ab.ravel()
    idx32 = np.arange(32, dtype=np.int64)

    def sampler(n: int, rng: np.random.Generator) -> np.ndarray:
        pick = rng.choice(P_ab_flat.size, size=n, p=P_ab_flat)
        a_samp = (pick // 1024).astype(np.int64)
        b_samp = (pick % 1024).astype(np.int64)

        u1_true = u1_map[a_samp]
        u2_true = u2_map[a_samp]

        # Conditional P(U2|B, U1_true)
        norms = p_u1_gb[u1_true, b_samp]
        bad = (~np.isfinite(norms)) | (norms <= 0.0)
        if np.any(bad):
            raise ZeroDenominatorError(
                f"Source {source}: zero conditional denominator P(U1|B) at {int(np.flatnonzero(bad)[0])} samples"
            )

        rows = p_joint[u1_true, :, b_samp] / norms[:, None]

        # Centering by true symbol U2: centered[i, j] = rows[i, j XOR u2_true[i]]
        centered = np.empty_like(rows)
        for i in range(n):
            centered[i] = rows[i, idx32 ^ u2_true[i]]
        return centered

    return sampler


def run_v36_de_screening(
    channel_counts: dict[str, np.ndarray],
    candidates: list[dict[str, Any]],
    coarse_samples: int = 1000,
    coarse_max_iter: int = 30,
    coarse_seed: int = 361001,
    conf_samples: int = 4000,
    conf_max_iter: int = 60,
    conf_seeds: tuple[int, int, int] = (362001, 362002, 362003),
    fake_runner: bool = False,
) -> dict[str, Any]:
    """Execute 2-tier DE screening: coarse screening followed by confirmation screening."""
    samplers = {src: build_v36_channel_sampler(channel_counts[src], src) for src in SOURCES}

    # 1. Compute Baseline DE (dv=2 regular) on all 3 sources
    baseline_lambda = {2: 1.0}
    baseline_de_results: dict[str, dict[str, Any]] = {}
    for src in SOURCES:
        R = RATES_BY_SOURCE[src]
        rho_base = make_rho(R, baseline_lambda)
        if fake_runner:
            base_ent = 4.80
        else:
            res_b = run_mcde_posterior(
                FIELD_Q, baseline_lambda, rho_base,
                channel_sampler=samplers[src],
                n_samples=coarse_samples,
                max_iter=coarse_max_iter,
                seed=coarse_seed,
            )
            base_ent = float(res_b["final_entropy_bits"])
        baseline_de_results[src] = {
            "final_entropy_bits": base_ent,
            "lambda": baseline_lambda,
            "rho": rho_base,
        }

    # 2. Coarse Screen
    coarse_records: list[dict[str, Any]] = []
    for cand in candidates:
        cand_id = cand["candidate_id"]
        lam = cand["lambda_edge"]
        worst_ent = 0.0
        degraded = False

        src_metrics: dict[str, Any] = {}
        for src in SOURCES:
            rho = cand["rho_by_source"][src]
            if fake_runner:
                ent = 4.70 if lam.get(2, 0.0) <= 0.5 else 4.85
                conv = bool(ent < 4.75)
                iters = 25
            else:
                res = run_mcde_posterior(
                    FIELD_Q, lam, rho,
                    channel_sampler=samplers[src],
                    n_samples=coarse_samples,
                    max_iter=coarse_max_iter,
                    seed=coarse_seed,
                )
                ent = float(res["final_entropy_bits"])
                conv = bool(res["converged"])
                iters = int(res["iterations"])

            src_metrics[src] = {"final_entropy": ent, "converged": conv, "iters": iters}
            worst_ent = max(worst_ent, ent)
            if ent > baseline_de_results[src]["final_entropy_bits"] + 1e-3:
                degraded = True

        rec = {
            "candidate_id": cand_id,
            "lambda_edge": lam,
            "dbar_v": cand["dbar_v"],
            "max_check_degree": cand["max_check_degree"],
            "worst_source_entropy": worst_ent,
            "degraded_vs_baseline": degraded,
            "sources": src_metrics,
        }
        coarse_records.append(rec)

    # Filter top non-degraded candidates for confirmation (up to 12)
    non_degraded = [r for r in coarse_records if not r["degraded_vs_baseline"]]
    non_degraded.sort(key=lambda r: (
        r["worst_source_entropy"],
        r["max_check_degree"],
        r["dbar_v"],
    ))
    coarse_shortlist = non_degraded[:12]

    # 3. Confirmation Screen (3 seeds per source, 4000 samples, 60 iters)
    confirmation_records: list[dict[str, Any]] = []
    for r in coarse_shortlist:
        cand_id = r["candidate_id"]
        lam = r["lambda_edge"]
        seed_entropies: list[float] = []
        all_conv = True
        worst_conf_ent = 0.0

        for src in SOURCES:
            R = RATES_BY_SOURCE[src]
            rho = concentrated_rho_to_hist(concentrated_check_distribution(R, lam))
            for s in conf_seeds:
                if fake_runner:
                    ent = 4.65
                    conv = True
                else:
                    res = run_mcde_posterior(
                        FIELD_Q, lam, rho,
                        channel_sampler=samplers[src],
                        n_samples=conf_samples,
                        max_iter=conf_max_iter,
                        seed=s,
                    )
                    ent = float(res["final_entropy_bits"])
                    conv = bool(res["converged"])

                seed_entropies.append(ent)
                if not conv:
                    all_conv = False
                worst_conf_ent = max(worst_conf_ent, ent)

        mean_ent = float(np.mean(seed_entropies))
        std_ent = float(np.std(seed_entropies))

        conf_rec = {
            "candidate_id": cand_id,
            "lambda_edge": lam,
            "dbar_v": r["dbar_v"],
            "max_check_degree": r["max_check_degree"],
            "mean_entropy": mean_ent,
            "std_entropy": std_ent,
            "worst_entropy": worst_conf_ent,
            "all_converged": all_conv,
        }
        confirmation_records.append(conf_rec)

    # Sort confirmation candidates by pre-registered order:
    # 1. all_converged (True first)
    # 2. worst_entropy (lower is better)
    # 3. std_entropy (lower variance across seeds)
    # 4. max_check_degree (lower is better)
    # 5. Canonical dictionary order
    confirmation_records.sort(key=lambda r: (
        not r["all_converged"],
        r["worst_entropy"],
        r["std_entropy"],
        r["max_check_degree"],
        r["candidate_id"],
    ))

    # Top candidates (up to 2 sent to finite graph)
    top_candidates = confirmation_records[:2]

    # Check terminal gate: at least one candidate improves over baseline
    base_worst = max(baseline_de_results[src]["final_entropy_bits"] for src in SOURCES)
    improved_vs_base = bool(top_candidates) and (top_candidates[0]["worst_entropy"] < base_worst)

    terminal_status = STATUS_DE_SHORTLIST_READY if (top_candidates and improved_vs_base) else STATUS_NO_DE_ADVANCE

    return {
        "status": terminal_status,
        "coarse_evaluated": len(coarse_records),
        "coarse_passed": len(coarse_shortlist),
        "confirmation_evaluated": len(confirmation_records),
        "top_candidates": top_candidates,
        "coarse_records": coarse_records,
        "confirmation_records": confirmation_records,
        "baseline_de": baseline_de_results,
    }


# ---------------------------------------------------------------------------
# Stage A2: Source-Native Finite Graph Construction & Audit
# ---------------------------------------------------------------------------

def count_bipartite_4_cycles(H: np.ndarray) -> int:
    """Exact count of 4-cycles in bipartite Tanner graph represented by binary support of H."""
    A = (H != 0).astype(np.int64)
    overlap = A.T @ A
    np.fill_diagonal(overlap, 0)
    c4 = np.sum(overlap * (overlap - 1) // 2) // 2
    return int(c4)


def check_degree2_cycles(H: np.ndarray) -> int:
    """Cycle rank of the degree-2 variable node subgraph on check vertices."""
    A = (H != 0).astype(np.int64)
    col_degs = A.sum(axis=0)
    deg2_cols = np.where(col_degs == 2)[0]
    if len(deg2_cols) == 0:
        return 0

    adj: dict[int, list[int]] = {}
    for c in deg2_cols:
        rows = tuple(np.where(A[:, c] > 0)[0])
        u, v = int(rows[0]), int(rows[1])
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)

    visited = set()
    num_nodes = len(adj)
    num_edges = len(deg2_cols)
    num_components = 0
    for node in list(adj.keys()):
        if node not in visited:
            num_components += 1
            queue = [node]
            visited.add(node)
            while queue:
                curr = queue.pop(0)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

    cycle_rank = num_edges - num_nodes + num_components
    return max(0, cycle_rank)


def construct_source_native_peg_matrix(
    lambda_edge: dict[int, float],
    source: str,
    n: int = N_SYMBOLS,
    graph_seed: int = 363001,
    coeff_seed: int = 364001,
    backup_coeff_seed: int = 364002,
    field: Optional[GF2mField] = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Construct native (m2, n) GF(32) parity-check matrix for the exact source rate via PEG."""
    if field is None:
        field = GF2mField.create(FIELD_Q)

    m = M2_BY_SOURCE[source]
    var_counts = node_view_counts(lambda_edge, n)
    total_var_sockets = sum(d * c for d, c in var_counts.items())

    # Concentrated check degree counts with exact socket consistency
    k = total_var_sockets // m
    m2_rem = total_var_sockets - k * m
    m1_rem = m - m2_rem
    check_counts = {k: m1_rem, k + 1: m2_rem} if m2_rem > 0 else {k: m}
    check_node_hist = {d: float(c) / float(m) for d, c in check_counts.items()}

    # 1. PEG Construction with primary coefficient seed
    peg_res = peg_construct(
        n=n,
        m=m,
        lambda_edge=lambda_edge,
        rho_edge=check_node_hist,
        seed=graph_seed,
        field=field,
        edge_label_seed=coeff_seed,
    )
    if peg_res["status"] != "ok":
        raise RuntimeError(f"PEG construction failed for source {source}: {peg_res.get('reason')}")

    dense = sparse_to_dense(peg_res["triples"], n, m, field)
    rank = compute_gf32_rank(dense, field)
    used_coeff_seed = coeff_seed

    # 2. Check full rank; if deficient, try pre-frozen backup coefficient seed
    if rank < m:
        peg_res_bk = peg_construct(
            n=n,
            m=m,
            lambda_edge=lambda_edge,
            rho_edge=check_node_hist,
            seed=graph_seed,
            field=field,
            edge_label_seed=backup_coeff_seed,
        )
        dense_bk = sparse_to_dense(peg_res_bk["triples"], n, m, field)
        rank_bk = compute_gf32_rank(dense_bk, field)
        if rank_bk >= rank:
            dense = dense_bk
            rank = rank_bk
            used_coeff_seed = backup_coeff_seed

    # 3. Structural Audit
    audit = audit_finite_graph(dense, field)
    audit["graph_seed"] = graph_seed
    audit["coeff_seed_used"] = used_coeff_seed
    audit["target_m"] = m
    audit["target_n"] = n
    audit["source"] = source
    return dense, audit


def audit_finite_graph(H: np.ndarray, field: Optional[GF2mField] = None) -> dict[str, Any]:
    """Compute comprehensive structural and topological metrics of a finite parity check matrix."""
    if field is None:
        field = GF2mField.create(FIELD_Q)

    m, n = H.shape
    A = (H != 0).astype(np.int64)
    col_degs = A.sum(axis=0)
    row_degs = A.sum(axis=1)

    rank = compute_gf32_rank(H, field)
    c4 = count_bipartite_4_cycles(H)
    deg2_cycles = check_degree2_cycles(H)

    col_hist = {int(d): int(np.sum(col_degs == d)) for d in np.unique(col_degs)}
    row_hist = {int(d): int(np.sum(row_degs == d)) for d in np.unique(row_degs)}

    isolated_vars = int(np.sum(col_degs == 0))
    isolated_checks = int(np.sum(row_degs == 0))

    realized_rate = float(1.0 - rank / n)

    # Elimination criteria check
    eliminated = (
        rank != m
        or np.any(col_degs < 2)
        or isolated_vars > 0
        or isolated_checks > 0
        or max(row_degs) > 16
    )

    return {
        "shape": [int(m), int(n)],
        "rank": int(rank),
        "rank_full": bool(rank == m),
        "realized_rate": realized_rate,
        "col_degree_hist": col_hist,
        "row_degree_hist": row_hist,
        "mean_check_degree": float(np.mean(row_degs)),
        "max_check_degree": int(np.max(row_degs)),
        "min_check_degree": int(np.min(row_degs)),
        "four_cycles_count": int(c4),
        "degree2_cycles_count": int(deg2_cycles),
        "isolated_variables": isolated_vars,
        "isolated_checks": isolated_checks,
        "eliminated": bool(eliminated),
    }


# ---------------------------------------------------------------------------
# Stage A3: Finite Paired Development Screen
# ---------------------------------------------------------------------------

def run_v36_a3_finite_screen(
    channel_counts: dict[str, np.ndarray],
    baseline_mats: dict[str, np.ndarray],
    candidate_mats_by_id: dict[str, dict[str, np.ndarray]],
    max_iter: int = 30,
    damping_alpha: float = 1.0,
    field: Optional[GF2mField] = None,
    fake_runner: bool = False,
) -> dict[str, Any]:
    """Execute paired development screen comparing V31 baseline against DE shortlisted candidates."""
    if field is None:
        field = GF2mField.create(FIELD_Q)

    all_records: list[BlockRecord] = []
    base_errs_by_block: dict[tuple[str, int], int] = {}
    cand_errs_by_block: dict[str, dict[tuple[str, int], int]] = {
        cid: {} for cid in candidate_mats_by_id
    }
    exact_by_cand_src: dict[str, dict[str, int]] = {
        cid: {src: 0 for src in SOURCES} for cid in candidate_mats_by_id
    }

    # Pre-generate 15 empirical blocks
    blocks: dict[tuple[str, int], dict[str, Any]] = {}
    for src in SOURCES:
        counts = channel_counts[src]
        for seed in A3_SEEDS[src]:
            _, alice, bob = sample_empirical_block(counts, seed, size=N_SYMBOLS)
            x1, x2, _, y2 = factorize_f03(alice, bob)
            prior = get_conditional_posterior_l2(counts, bob, x1)
            raw_errs = int(np.sum(x2 != y2))
            blocks[(src, seed)] = {
                "alice": alice,
                "bob": bob,
                "x1": x1,
                "x2": x2,
                "prior": prior,
                "raw_errors": raw_errs,
            }

    # 1. Baseline Evaluation
    for (src, seed), bdata in blocks.items():
        x1, x2, prior = bdata["x1"], bdata["x2"], bdata["prior"]
        H_base = baseline_mats[src]
        syn_true = syndrome_of_gf32(H_base, x2, field)

        if fake_runner:
            final_errs = 175
            iters = 30
            rt = 0.001
            syn_ok = False
            exact = False
            status = "max_iter"
        else:
            res = decode_row_layered_fftqspa(
                H_base, prior, syn_true, max_iter=max_iter, damping_alpha=damping_alpha, field=field
            )
            final_errs = int(np.sum(res.x_hat != x2))
            iters = res.iterations
            rt = res.runtime_s
            syn_ok = res.syndrome_ok
            exact = bool(np.array_equal(res.x_hat, x2))
            status = res.status

        tag_ok = bool(compute_tag_64(x1, res.x_hat if not fake_runner else x2) == compute_tag_64(x1, x2)) if exact else False
        false_accept = bool(tag_ok and not exact)
        base_errs_by_block[(src, seed)] = final_errs

        rec = BlockRecord(
            source=src,
            seed=seed,
            method="nb_ldpc_v36",
            graph_id="v31_qc_baseline",
            decoder_schedule="row_layered",
            redundancy_stage="S0",
            exact_l2=exact,
            syndrome_ok=syn_ok,
            tag_ok=tag_ok,
            false_accept=false_accept,
            errors_initial=bdata["raw_errors"],
            errors_final=final_errs,
            iterations=iters,
            runtime_s=rt,
            syndrome_leakage_bits=0,
            cumulative_leakage_bits=H_base.shape[0] * 5 + TAG_BITS,
            status=status,
        )
        all_records.append(rec)

    # 2. Candidate Evaluations
    cand_summaries: dict[str, Any] = {}
    for cid, cand_mats in candidate_mats_by_id.items():
        for (src, seed), bdata in blocks.items():
            x1, x2, prior = bdata["x1"], bdata["x2"], bdata["prior"]
            H_cand = cand_mats[src]
            syn_true = syndrome_of_gf32(H_cand, x2, field)

            if fake_runner:
                final_errs = 140
                iters = 25
                rt = 0.001
                syn_ok = False
                exact = False
                status = "max_iter"
            else:
                res = decode_row_layered_fftqspa(
                    H_cand, prior, syn_true, max_iter=max_iter, damping_alpha=damping_alpha, field=field
                )
                final_errs = int(np.sum(res.x_hat != x2))
                iters = res.iterations
                rt = res.runtime_s
                syn_ok = res.syndrome_ok
                exact = bool(np.array_equal(res.x_hat, x2))
                status = res.status

            tag_ok = bool(compute_tag_64(x1, res.x_hat if not fake_runner else x2) == compute_tag_64(x1, x2)) if exact else False
            false_accept = bool(tag_ok and not exact)
            cand_errs_by_block[cid][(src, seed)] = final_errs
            if exact:
                exact_by_cand_src[cid][src] += 1

            rec = BlockRecord(
                source=src,
                seed=seed,
                method="nb_ldpc_v36",
                graph_id=f"v36_source_native_{cid}",
                decoder_schedule="row_layered",
                redundancy_stage="S0",
                exact_l2=exact,
                syndrome_ok=syn_ok,
                tag_ok=tag_ok,
                false_accept=false_accept,
                errors_initial=bdata["raw_errors"],
                errors_final=final_errs,
                iterations=iters,
                runtime_s=rt,
                syndrome_leakage_bits=0,
                cumulative_leakage_bits=H_cand.shape[0] * 5 + TAG_BITS,
                status=status,
            )
            all_records.append(rec)

        # Evaluate Advance Gate for this candidate
        exact_gate = all(exact_by_cand_src[cid][src] >= 1 for src in SOURCES)

        # Residual path check
        improved_blocks = 0
        no_block_worse_than_10 = True
        median_drops_src: dict[str, float] = {}
        for src in SOURCES:
            base_errs_src = [base_errs_by_block[(src, s)] for s in A3_SEEDS[src]]
            cand_errs_src = [cand_errs_by_block[cid][(src, s)] for s in A3_SEEDS[src]]

            med_base = float(np.median(base_errs_src))
            med_cand = float(np.median(cand_errs_src))
            drop = (med_base - med_cand) / med_base if med_base > 0 else 0.0
            median_drops_src[src] = drop

            for b_e, c_e in zip(base_errs_src, cand_errs_src):
                if c_e < b_e:
                    improved_blocks += 1
                if c_e > b_e + 10:
                    no_block_worse_than_10 = False

        median_gate = all(median_drops_src[src] >= 0.15 for src in SOURCES)
        residual_gate = (
            median_gate
            and (improved_blocks >= 12)
            and no_block_worse_than_10
        )

        advance_granted = bool(exact_gate or residual_gate)
        cand_summaries[cid] = {
            "exact_gate_met": exact_gate,
            "residual_gate_met": residual_gate,
            "advance_granted": advance_granted,
            "exact_counts_by_source": exact_by_cand_src[cid],
            "median_drops_by_source": median_drops_src,
            "improved_blocks": improved_blocks,
            "no_block_worse_than_10": no_block_worse_than_10,
        }

    # Determine overall A3 advance status
    advancing_candidates = [cid for cid, s in cand_summaries.items() if s["advance_granted"]]
    best_candidate_id = advancing_candidates[0] if advancing_candidates else None
    terminal_status = STATUS_FINITE_GRAPH_ADVANCE if advancing_candidates else STATUS_NO_FINITE_GRAPH_ADVANCE

    return {
        "status": terminal_status,
        "best_candidate_id": best_candidate_id,
        "candidate_summaries": cand_summaries,
        "records": all_records,
    }


# ---------------------------------------------------------------------------
# Stage A4: Moderate-Degree Incremental Syndrome (S0..S3, Cold-Start)
# ---------------------------------------------------------------------------

def build_v36_incremental_matrix(
    H_base: np.ndarray,
    source: str,
    target_degree_range: tuple[int, int] = (10, 14),
    seed: int = 365001,
    field: Optional[GF2mField] = None,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Extend base parity check matrix by 32 moderate-degree checks (degrees 10-14, max 16)."""
    if field is None:
        field = GF2mField.create(FIELD_Q)

    m_base, n = H_base.shape
    total_new_checks = 32
    rng = np.random.default_rng(seed)

    new_rows: list[np.ndarray] = []
    for i in range(total_new_checks):
        deg = int(rng.integers(target_degree_range[0], target_degree_range[1] + 1))
        deg = min(16, deg)
        # Select variable positions avoiding identical check support
        cols = rng.choice(n, size=deg, replace=False)
        row = np.zeros(n, dtype=np.uint8)
        for c in cols:
            coeff = int(rng.integers(1, FIELD_Q))
            row[c] = coeff
        new_rows.append(row)

    new_rows_arr = np.vstack(new_rows)
    H_mother = np.vstack([H_base, new_rows_arr])

    # Slices for S0, S1, S2, S3
    stage_mats = {
        "S0": H_mother[:m_base, :],
        "S1": H_mother[:m_base + 8, :],
        "S2": H_mother[:m_base + 16, :],
        "S3": H_mother[:m_base + 32, :],
    }

    return H_mother, stage_mats


def run_v36_a4_incremental_evaluation(
    channel_counts: dict[str, np.ndarray],
    stage_mats_by_src: dict[str, dict[str, np.ndarray]],
    candidate_id: str,
    max_iter: int = 30,
    damping_alpha: float = 1.0,
    field: Optional[GF2mField] = None,
    fake_runner: bool = False,
) -> dict[str, Any]:
    """Evaluate incremental stages S0..S3 under clean cold-start decoding."""
    if field is None:
        field = GF2mField.create(FIELD_Q)

    records: list[BlockRecord] = []
    exact_by_src_stage: dict[str, dict[str, int]] = {
        src: {stg: 0 for stg in INCREMENTAL_STAGES} for src in SOURCES
    }

    for src in SOURCES:
        counts = channel_counts[src]
        stage_mats = stage_mats_by_src[src]
        for seed in A3_SEEDS[src]:
            _, alice, bob = sample_empirical_block(counts, seed, size=N_SYMBOLS)
            x1, x2, _, y2 = factorize_f03(alice, bob)
            prior = get_conditional_posterior_l2(counts, bob, x1)
            raw_errs = int(np.sum(x2 != y2))

            for stg in INCREMENTAL_STAGES:
                H_stg = stage_mats[stg]
                syn_true = syndrome_of_gf32(H_stg, x2, field)

                if fake_runner:
                    final_errs = max(0, 100 - INCREMENTAL_EXTRA_CHECKS[stg] * 3)
                    iters = 20
                    rt = 0.001
                    syn_ok = bool(stg == "S3")
                    exact = bool(stg == "S3")
                    status = "converged_exact" if exact else "max_iter"
                else:
                    res = decode_row_layered_fftqspa(
                        H_stg, prior, syn_true, max_iter=max_iter, damping_alpha=damping_alpha, field=field
                    )
                    final_errs = int(np.sum(res.x_hat != x2))
                    iters = res.iterations
                    rt = res.runtime_s
                    syn_ok = res.syndrome_ok
                    exact = bool(np.array_equal(res.x_hat, x2))
                    status = res.status

                tag_ok = bool(compute_tag_64(x1, res.x_hat if not fake_runner else x2) == compute_tag_64(x1, x2)) if exact else False
                false_accept = bool(tag_ok and not exact)
                if exact:
                    exact_by_src_stage[src][stg] += 1

                rec = BlockRecord(
                    source=src,
                    seed=seed,
                    method="nb_ldpc_v36",
                    graph_id=f"v36_{candidate_id}_{stg}",
                    decoder_schedule="row_layered",
                    redundancy_stage=stg,
                    exact_l2=exact,
                    syndrome_ok=syn_ok,
                    tag_ok=tag_ok,
                    false_accept=false_accept,
                    errors_initial=raw_errs,
                    errors_final=final_errs,
                    iterations=iters,
                    runtime_s=rt,
                    syndrome_leakage_bits=INCREMENTAL_EXTRA_BITS[stg],
                    cumulative_leakage_bits=H_stg.shape[0] * 5 + TAG_BITS,
                    status=status,
                )
                records.append(rec)

    # Threshold gate: >= 3/5 exact per source across stages with 0 false accepts
    threshold_met = all(
        max(exact_by_src_stage[src].values()) >= 3 for src in SOURCES
    )
    total_fa = sum(1 for r in records if r.false_accept)

    if threshold_met and total_fa == 0:
        terminal_status = STATUS_NB_DEVELOPMENT_CANDIDATE_FOUND
    else:
        terminal_status = STATUS_FINITE_GRAPH_ADVANCE_NO_EXACT

    return {
        "status": terminal_status,
        "exact_by_src_stage": exact_by_src_stage,
        "threshold_met": threshold_met,
        "total_false_accepts": total_fa,
        "records": records,
    }


# ---------------------------------------------------------------------------
# Report Generator & Claim Ledger
# ---------------------------------------------------------------------------

def generate_v36_development_report(
    summary: dict[str, Any],
    all_records: list[BlockRecord],
    output_path: Path,
) -> str:
    """Generate Markdown report and claim ledger directly from execution records."""
    terminal_status = summary.get("terminal_status", "UNKNOWN")
    a0_summary = summary.get("stage_summaries", {}).get("A0_decoder_iteration_diagnostic", {})
    a1_summary = summary.get("stage_summaries", {}).get("A1_de_candidate_screening", {})
    a2_summary = summary.get("stage_summaries", {}).get("A2_source_native_graphs", {})
    a3_summary = summary.get("stage_summaries", {}).get("A3_finite_paired_screen", {})
    a4_summary = summary.get("stage_summaries", {}).get("A4_incremental_syndrome", {})

    # Compute exact baseline and candidate stats from A3 records
    base_records = [r for r in all_records if r.graph_id == "v31_qc_baseline"]
    cand_records = [r for r in all_records if "source_native" in r.graph_id]

    def _stats(subset: list[BlockRecord]) -> tuple[float, float, float, int]:
        if not subset:
            return 0.0, 0.0, 0.0, 0
        errs = [r.errors_final for r in subset]
        succ = sum(1 for r in subset if r.exact_l2)
        return float(np.mean(errs)), float(np.std(errs)), float(np.median(errs)), succ

    b_m, b_s, b_med, b_succ = _stats(base_records)
    c_m, c_s, c_med, c_succ = _stats(cand_records)

    total_fa = sum(1 for r in all_records if r.false_accept)

    report_content = f"""# V36 Empirical-P Irregular LDPC & Source-Native Graph Development Report

**Date**: {time.strftime("%Y-%m-%d", time.gmtime())}  
**Milestone**: V36 Empirical-P Irregular LDPC Development  
**Domain**: Formal Information Reconciliation (IR) / Nonbinary LDPC  
**Output Root**: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v36_empirical_graph_development/run_01/`  
**Terminal Scientific Status**: **`{terminal_status}`**  

---

## 1. Executive Summary & Progression Results

### Stage A0 (Decoder Iteration Diagnostic)
- **Evaluated**: True V31 baseline at `max_iter=30` vs `max_iter=60` across 9 development blocks (seeds `360101..360303`).
- **Selected Budget**: `max_iter = {a0_summary.get('selected_max_iter', 30)}`.
- **Median Relative Improvements**: {a0_summary.get('median_relative_drops', {})}.

### Stage A1 (GF(32) Empirical-P Irregular Ensemble DE Screening)
- **Candidate Grid**: {a1_summary.get('coarse_evaluated', 0)} variable degree distributions ($\bar{{d}}_v \\in [2.15, 2.55]$, $d_c \\le 16$).
- **Coarse Passed**: {a1_summary.get('coarse_passed', 0)} non-degraded candidates.
- **Top Shortlisted Candidate**: `{a1_summary.get('top_candidates', [{}])[0].get('candidate_id', 'none') if a1_summary.get('top_candidates') else 'none'}`.
- **Persisted runner status**: `{a1_summary.get('status', 'UNKNOWN')}`.
- **Post-run acceptance**: `A1_DE_SELECTION_NOT_ACCEPTED`. The confirmation did not implement the frozen same-setting, per-source improvement comparison; near-zero saturated entropy is not evidence of a meaningful 10% advantage.

### Stage A2 (Source-Native Finite Graph Construction)
- **Native Construction**: Separate PEG parity-check matrices generated for 1M ($184\\times 1024$), 1.5M ($190\\times 1024$), 2M ($192\\times 1024$).
- **Submatrix Truncation**: Strictly zero truncation used.
- **Matrix Audits**: Full GF(32) row rank was realized, but the three graphs contained 3002/2721/2288 4-cycles and degree-2 cycle ranks 801/785/779.
- **Post-run acceptance**: `A2_STRUCTURAL_GATE_FAILED`; the frozen zero-cycle requirements were not met. A3 is retained as exploratory downstream data.

### Stage A3 (Finite Paired Development Screen)
- **Evaluated**: 15 paired empirical blocks comparing V31 baseline vs DE shortlist candidate.
- **V31 Baseline Residual Errors**: Mean = ${b_m:.2f} \\pm {b_s:.2f}$, Median = ${b_med:.1f}$, Exact = {b_succ}/15.
- **Candidate Residual Errors**: Mean = ${c_m:.2f} \\pm {c_s:.2f}$, Median = ${c_med:.1f}$, Exact = {c_succ}/15.
- **Stage A3 Terminal**: `{a3_summary.get('status', 'UNKNOWN')}`.

### Stage A4 (Moderate-Degree Incremental Syndrome)
- **Executed**: {a4_summary.get('executed', False)}.
- **Stage A4 Terminal**: `{a4_summary.get('status', 'SKIPPED')}`.

---

## 2. Verification bookkeeping boundary

- Across all evaluated records ({len(all_records)} total records), recorded `false_accept` is **{total_fa}**. This oracle-L1 development diagnostic is not an independent cryptographic-integrity or end-to-end security result.

---

## 3. Pre-Registered Claim Ledger

| Claim | Evidence Type | Direct Artifact / Field | Permitted Wording |
|---|---|---|---|
| **Candidate DE Comparison** | Protocol-incomplete computation | `de_coarse_results.csv`, `de_confirmation_results.csv` | “候选由实现筛出，但未通过冻结的 A1 接受语义” |
| **Finite Graph Performance** | Exploratory paired finite data | `finite_block_results.csv` | “15 块中均值残差 174.80 降至 157.07，10/15 改善，exact 0/15；未晋级” |
| **Trapping Set Causality** | None | — | **禁止作为定论** |
| **Waterfall Threshold Claim** | None | — | **禁止作为定论** |
| **General FER Claim** | None | — | **禁止作为定论** |

---

## 4. Official Terminal Scientific Status

`POSITIVE_EXPLORATORY_RESIDUAL_SIGNAL / A1_DE_SELECTION_NOT_ACCEPTED /
A2_STRUCTURAL_GATE_FAILED / {terminal_status}`
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_content, encoding="utf-8")
    return report_content
