"""V38-P0 Structured Low-Degree Architecture Triage Module.

This module implements the frozen V38-P0 architecture triage protocol:
- Lane A: Near-dv=2 + GF(32) cycle-aware edge labeling (controlled label-only isolation experiment on V31 support).
- Lane B: eIRA-like dual-diagonal structured NB-LDPC prototype.
- Lane C: SC-inspired finite spatially banded prototype (L=8, w=2, load-aware check allocation).
- Deterministic PRNG contract (PCG64 + SeedSequence([S, 1/2/3])).
- Direct submatrix-rank algebraic cycle degeneracy classification (lengths 4, 6, 8).
- Prototype structural selection (prior to decoding).
- Finite development evaluation and triage gate (reusing frozen V36 A3 baseline).
- Terminal state orchestration.

Lifecycle: IMPLEMENTATION_CANDIDATE
"""

from __future__ import annotations

import math
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np

from comparison_bench.formal_ir.v35_algorithm_development import (
    GF2mField,
    compute_gf32_rank,
    decode_row_layered_fftqspa,
    factorize_f03,
    get_conditional_posterior_l2,
    load_v25_channel_counts,
    load_v31_qc_baseline_matrices,
    sample_empirical_block,
    syndrome_of_gf32,
)

# ---------------------------------------------------------------------------
# Constants & Configuration
# ---------------------------------------------------------------------------

DIMENSION: int = 32
POLYNOMIAL: int = 37  # 0b100101
BLOCK_LENGTH: int = 1024
MAX_CHECK_DEGREE_LIMIT: int = 16

SOURCE_CHECKS: dict[str, int] = {
    "1M": 184,
    "1p5M": 190,
    "2M": 192,
}

# Pre-registered production construction seeds (Frozen; for future development execution)
LANE_PRODUCTION_SEEDS: dict[str, dict[str, list[int]]] = {
    "lane_a": {
        "1M": [381101, 381102, 381103],
        "1p5M": [381201, 381202, 381203],
        "2M": [381301, 381302, 381303],
    },
    "lane_b": {
        "1M": [382101, 382102, 382103],
        "1p5M": [382201, 382202, 382203],
        "2M": [382301, 382302, 382303],
    },
    "lane_c": {
        "1M": [383101, 383102, 383103],
        "1p5M": [383201, 383202, 383203],
        "2M": [383301, 383302, 383303],
    },
}

# 15 Fixed development blocks established in V36 A3
V36_A3_BLOCK_SEEDS: dict[str, list[int]] = {
    "1M": [360101, 360102, 360103, 360104, 360105],
    "1p5M": [360201, 360202, 360203, 360204, 360205],
    "2M": [360301, 360302, 360303, 360304, 360305],
}

# Lane C positional configurations (L=8, w=2)
LANE_C_EDGE_LOAD_VECTOR: list[int] = [128, 256, 256, 256, 256, 256, 256, 384]
LANE_C_CHECK_ALLOCATIONS: dict[str, list[int]] = {
    "1M": [12, 23, 23, 23, 23, 23, 23, 34],
    "1p5M": [12, 24, 24, 24, 24, 24, 23, 35],
    "2M": [12, 24, 24, 24, 24, 24, 24, 36],
}

# Authoritative frozen V31 baseline performance (from committed V36 A3 records)
FROZEN_BASELINE_ERROR_MAP: dict[str, dict[int, int]] = {
    "1M": {
        360101: 166,
        360102: 177,
        360103: 171,
        360104: 178,
        360105: 162,
    },
    "1p5M": {
        360201: 167,
        360202: 199,
        360203: 187,
        360204: 148,
        360205: 178,
    },
    "2M": {
        360301: 164,
        360302: 189,
        360303: 183,
        360304: 184,
        360305: 169,
    },
}

V31_BASELINE_REFERENCE: dict[str, Any] = {
    "exact_count": 0,
    "overall_mean": 174.80,
    "overall_median": 177.0,
    "sources": {
        "1M": {
            "mean": 170.8,
            "median": 171.0,
            "errors": [166, 177, 171, 178, 162],
            "seed_map": FROZEN_BASELINE_ERROR_MAP["1M"],
        },
        "1p5M": {
            "mean": 175.8,
            "median": 178.0,
            "errors": [167, 199, 187, 148, 178],
            "seed_map": FROZEN_BASELINE_ERROR_MAP["1p5M"],
        },
        "2M": {
            "mean": 177.8,
            "median": 183.0,
            "errors": [164, 189, 183, 184, 169],
            "seed_map": FROZEN_BASELINE_ERROR_MAP["2M"],
        },
    },
}

# Terminal states
V38_SINGLE_ROUTE_SIGNAL = "V38_SINGLE_ROUTE_SIGNAL"
V38_MULTIPLE_ROUTE_SIGNALS = "V38_MULTIPLE_ROUTE_SIGNALS"
V38_NO_ROUTE_SIGNAL = "V38_NO_ROUTE_SIGNAL"
V38_NO_STRUCTURAL_PROTOTYPE_READY = "V38_NO_STRUCTURAL_PROTOTYPE_READY"
V38_DIRECTION_EVIDENCE_INVALID = "V38_DIRECTION_EVIDENCE_INVALID"

# Lane statuses
LANE_READY = "LANE_READY"
LANE_STRUCTURAL_NOT_READY = "LANE_STRUCTURAL_NOT_READY"
LANE_EVALUATED_NO_SIGNAL = "LANE_EVALUATED_NO_SIGNAL"
LANE_PROMISING_DIRECTION_SIGNAL = "LANE_PROMISING_DIRECTION_SIGNAL"

# V38R1 decoder-only successor: the nine winners are frozen from V38-P0
# run_01.  This mapping intentionally bypasses the 27-candidate construction
# and structural winner search used by V38-P0.
V38R1_WINNER_SEEDS: dict[str, dict[str, int]] = {
    "lane_a": {"1M": 381101, "1p5M": 381201, "2M": 381301},
    "lane_b": {"1M": 382103, "1p5M": 382201, "2M": 382301},
    "lane_c": {"1M": 383103, "1p5M": 383203, "2M": 383301},
}
V38R1_LANE_ORDER: tuple[str, ...] = ("lane_a", "lane_b", "lane_c")
V38R1_SOURCE_ORDER: tuple[str, ...] = ("1M", "1p5M", "2M")
V38R1_REPO_ROOT = Path(__file__).resolve().parents[4]
V38R1_RUN01_METRICS_PATH = (
    V38R1_REPO_ROOT
    / "comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json"
)
V38R1_RUN02_ROOT = (
    V38R1_REPO_ROOT
    / "comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_02"
)

V38R1_REQUIRED_METRIC_KEYS: tuple[str, ...] = (
    "lane",
    "source",
    "construction_seed",
    "matrix_id",
    "shape",
    "rank_GF32",
    "support_edge_count",
    "col_degree_min",
    "col_degree_mean",
    "col_degree_max",
    "row_degree_min",
    "row_degree_mean",
    "row_degree_max",
    "degenerate_cycles_4",
    "degenerate_cycles_6",
    "degenerate_cycles_8",
    "support_cycles_4",
    "structurally_valid",
)


# ---------------------------------------------------------------------------
# PRNG & Sampling Utilities
# ---------------------------------------------------------------------------

def get_substream_generator(base_seed: int, stream_id: int) -> np.random.Generator:
    """Derive a deterministic PCG64 NumPy Generator using SeedSequence."""
    ss = np.random.SeedSequence([int(base_seed), int(stream_id)])
    return np.random.Generator(np.random.PCG64(ss))


def sample_uniform_gf32_nonzero(rng: np.random.Generator, size: int) -> np.ndarray:
    """Sample uniform integer elements from GF(32)\\{0} -> {1, 2, ..., 31}."""
    return rng.integers(low=1, high=32, size=int(size), endpoint=False).astype(np.uint8)


def get_canonical_support_edges(binary_support: np.ndarray) -> list[tuple[int, int]]:
    """Return support edges sorted lexicographically: (check_index, variable_index)."""
    rows, cols = np.nonzero(binary_support)
    edges = [(int(r), int(c)) for r, c in zip(rows, cols)]
    edges.sort()
    return edges


# ---------------------------------------------------------------------------
# Cycle Enumeration & Algebraic Degeneracy Classifier
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CycleInfo:
    """Canonical simple cycle in a bipartite Tanner graph."""
    length: int
    checks: tuple[int, ...]
    vars: tuple[int, ...]
    edges: tuple[tuple[int, int], ...]


def enumerate_canonical_simple_cycles(
    binary_support: np.ndarray,
) -> tuple[list[CycleInfo], list[CycleInfo], list[CycleInfo], dict[tuple[int, int], list[int]]]:
    """Enumerate canonical simple cycles of lengths 4, 6, and 8 without duplicates.

    Returns:
        cycles_4: list of CycleInfo of length 4
        cycles_6: list of CycleInfo of length 6
        cycles_8: list of CycleInfo of length 8
        edge_to_cycle_ids: mapping (c, v) -> list of global cycle indices in all_cycles
    """
    m, n = binary_support.shape
    adj_c = [np.nonzero(binary_support[i, :])[0].tolist() for i in range(m)]
    adj_v = [np.nonzero(binary_support[:, j])[0].tolist() for j in range(n)]

    cycles_4: list[CycleInfo] = []
    cycles_6: list[CycleInfo] = []
    cycles_8: list[CycleInfo] = []

    # Length 4: c0 < c1, v0 < v1
    for c0 in range(m):
        for c1 in range(c0 + 1, m):
            common = sorted(set(adj_c[c0]).intersection(adj_c[c1]))
            k = len(common)
            for i in range(k):
                v0 = common[i]
                for j in range(i + 1, k):
                    v1 = common[j]
                    c_tuple = (c0, c1)
                    v_tuple = (v0, v1)
                    edges = ((c0, v0), (c1, v0), (c1, v1), (c0, v1))
                    cycles_4.append(CycleInfo(length=4, checks=c_tuple, vars=v_tuple, edges=edges))

    # Length 6: c0 = min(c0, c1, c2), c1 < c2
    for c0 in range(m):
        for v0 in adj_c[c0]:
            for c1 in adj_v[v0]:
                if c1 <= c0:
                    continue
                for v1 in adj_c[c1]:
                    if v1 == v0:
                        continue
                    for c2 in adj_v[v1]:
                        if c2 <= c1:
                            continue
                        for v2 in adj_c[c2]:
                            if v2 == v1 or v2 == v0:
                                continue
                            if c0 in adj_v[v2]:
                                c_tuple = (c0, c1, c2)
                                v_tuple = (v0, v1, v2)
                                edges = ((c0, v0), (c1, v0), (c1, v1), (c2, v1), (c2, v2), (c0, v2))
                                cycles_6.append(CycleInfo(length=6, checks=c_tuple, vars=v_tuple, edges=edges))

    # Length 8: c0 = min(c0, c1, c2, c3), c1 < c3
    for c0 in range(m):
        for v0 in adj_c[c0]:
            for c1 in adj_v[v0]:
                if c1 <= c0:
                    continue
                for v1 in adj_c[c1]:
                    if v1 == v0:
                        continue
                    for c2 in adj_v[v1]:
                        if c2 <= c0 or c2 == c1:
                            continue
                        for v2 in adj_c[c2]:
                            if v2 == v1 or v2 == v0:
                                continue
                            for c3 in adj_v[v2]:
                                if c3 <= c0 or c3 == c1 or c3 == c2 or c3 <= c1:
                                    continue
                                for v3 in adj_c[c3]:
                                    if v3 == v2 or v3 == v1 or v3 == v0:
                                        continue
                                    if c0 in adj_v[v3]:
                                        c_tuple = (c0, c1, c2, c3)
                                        v_tuple = (v0, v1, v2, v3)
                                        edges = (
                                            (c0, v0), (c1, v0),
                                            (c1, v1), (c2, v1),
                                            (c2, v2), (c3, v2),
                                            (c3, v3), (c0, v3),
                                        )
                                        cycles_8.append(CycleInfo(length=8, checks=c_tuple, vars=v_tuple, edges=edges))

    # Build global edge -> cycle IDs mapping
    all_cycles = cycles_4 + cycles_6 + cycles_8
    edge_to_cycle_ids: dict[tuple[int, int], list[int]] = {}
    for edge in get_canonical_support_edges(binary_support):
        edge_to_cycle_ids[edge] = []

    for idx, cyc in enumerate(all_cycles):
        for e in cyc.edges:
            if e in edge_to_cycle_ids:
                edge_to_cycle_ids[e].append(idx)
            else:
                edge_to_cycle_ids[e] = [idx]

    return cycles_4, cycles_6, cycles_8, edge_to_cycle_ids


def compute_cycle_submatrix_rank(
    cycle: CycleInfo,
    H: np.ndarray,
    field: Optional[GF2mField] = None,
) -> int:
    """Compute the GF(32) rank of the r x r cycle-only submatrix."""
    if field is None:
        field = GF2mField.create(32)
    r = len(cycle.checks)
    H_sub = np.zeros((r, r), dtype=np.uint8)
    for j in range(r):
        c_curr = cycle.checks[j]
        c_next = cycle.checks[(j + 1) % r]
        v_curr = cycle.vars[j]
        H_sub[j, j] = H[c_curr, v_curr]
        H_sub[(j + 1) % r, j] = H[c_next, v_curr]
    return compute_gf32_rank(H_sub, field)


def classify_cycle_algebraic_degeneracy(
    cycle: CycleInfo,
    H: np.ndarray,
    field: Optional[GF2mField] = None,
) -> bool:
    """Return True if cycle is algebraically DEGENERATE (rank < r), False if NON-DEGENERATE (rank == r)."""
    r = len(cycle.checks)
    rank = compute_cycle_submatrix_rank(cycle, H, field)
    return bool(rank < r)


# ---------------------------------------------------------------------------
# Common Hard Structural Validity & Metrics
# ---------------------------------------------------------------------------

def check_lane_c_capacity_feasibility(m: int, allocations: list[int]) -> bool:
    """Verify that expected edges at each position p satisfy load[p] <= 16 * checks[p]."""
    if len(allocations) != 8 or sum(allocations) != m:
        return False
    for p in range(8):
        load = LANE_C_EDGE_LOAD_VECTOR[p]
        capacity = 16 * allocations[p]
        if load > capacity:
            return False
    return True


def check_structural_validity(
    H: np.ndarray,
    expected_shape: tuple[int, int],
    dc_max: int = MAX_CHECK_DEGREE_LIMIT,
    field: Optional[GF2mField] = None,
) -> tuple[bool, str]:
    """Check all hard structural validity requirements for a prototype matrix."""
    if field is None:
        field = GF2mField.create(32)

    m, n = H.shape
    exp_m, exp_n = expected_shape
    if (m, n) != (exp_m, exp_n):
        return False, f"Shape mismatch: expected {expected_shape}, got {H.shape}"

    # Row rank over GF(32)
    rank = compute_gf32_rank(H, field)
    if rank != m:
        return False, f"GF(32) row rank deficient: expected {m}, got {rank}"

    # Isolated nodes
    col_weights = np.count_nonzero(H, axis=0)
    if np.any(col_weights == 0):
        return False, "Isolated variable node detected (column weight == 0)"

    row_weights = np.count_nonzero(H, axis=1)
    if np.any(row_weights == 0):
        return False, "Isolated check node detected (row weight == 0)"

    # Max check degree
    if int(row_weights.max()) > dc_max:
        return False, f"Max check degree {row_weights.max()} exceeds limit {dc_max}"

    # Nonzero entries in GF(32)\{0}
    nonzeros = H[H != 0]
    if np.any((nonzeros < 1) | (nonzeros > 31)):
        return False, "Invalid non-zero GF(32) label outside 1..31"

    return True, "VALID"


def compute_structural_metrics(
    H: np.ndarray,
    lane: str,
    source: str,
    seed: int,
    field: Optional[GF2mField] = None,
) -> dict[str, Any]:
    """Compute comprehensive structural metrics for a prototype matrix."""
    if field is None:
        field = GF2mField.create(32)

    m, n = H.shape
    exp_m = SOURCE_CHECKS.get(source, m)
    valid, reason = check_structural_validity(H, (exp_m, BLOCK_LENGTH), dc_max=16, field=field)

    rank = compute_gf32_rank(H, field)
    binary_support = (H != 0).astype(np.uint8)
    support_edge_count = int(np.count_nonzero(binary_support))

    col_weights = np.count_nonzero(binary_support, axis=0)
    row_weights = np.count_nonzero(binary_support, axis=1)

    c4, c6, c8, _ = enumerate_canonical_simple_cycles(binary_support)

    deg_4 = sum(classify_cycle_algebraic_degeneracy(c, H, field) for c in c4)
    deg_6 = sum(classify_cycle_algebraic_degeneracy(c, H, field) for c in c6)
    deg_8 = sum(classify_cycle_algebraic_degeneracy(c, H, field) for c in c8)

    nondeg_4 = len(c4) - deg_4
    nondeg_6 = len(c6) - deg_6
    nondeg_8 = len(c8) - deg_8

    frac_4 = nondeg_4 / len(c4) if len(c4) > 0 else 1.0
    frac_6 = nondeg_6 / len(c6) if len(c6) > 0 else 1.0
    frac_8 = nondeg_8 / len(c8) if len(c8) > 0 else 1.0

    return {
        "lane": lane,
        "source": source,
        "construction_seed": seed,
        "matrix_id": f"{lane}_{source}_s{seed}",
        "shape": list(H.shape),
        "rank_GF32": rank,
        "support_edge_count": support_edge_count,
        "col_degree_min": int(col_weights.min()),
        "col_degree_mean": float(col_weights.mean()),
        "col_degree_max": int(col_weights.max()),
        "row_degree_min": int(row_weights.min()),
        "row_degree_mean": float(row_weights.mean()),
        "row_degree_max": int(row_weights.max()),
        "support_cycles_4": len(c4),
        "support_cycles_6": len(c6),
        "support_cycles_8": len(c8),
        "degenerate_cycles_4": deg_4,
        "degenerate_cycles_6": deg_6,
        "degenerate_cycles_8": deg_8,
        "nondegenerate_cycles_4": nondeg_4,
        "nondegenerate_cycles_6": nondeg_6,
        "nondegenerate_cycles_8": nondeg_8,
        "nondegenerate_fraction_4": float(frac_4),
        "nondegenerate_fraction_6": float(frac_6),
        "nondegenerate_fraction_8": float(frac_8),
        "structurally_valid": valid,
        "structural_failure_reason": reason if not valid else "",
    }


# ---------------------------------------------------------------------------
# Lane A Optimization Helper
# ---------------------------------------------------------------------------

def optimize_lane_a_coefficients(
    H_init: np.ndarray,
    binary_support: np.ndarray,
    max_sweeps: int = 2,
    field: Optional[GF2mField] = None,
) -> tuple[np.ndarray, int, int, int, int]:
    """Perform deterministic Lane-A cycle-degeneracy minimization search over GF(32) edge labels.

    Candidate key for every edge and candidate value:
        candidate_key = (cand_d4, cand_d6, cand_d8, cand)
    The minimum candidate_key across all cand in 1..31 is chosen (strict tie-break to lowest integer).
    Edges with 0 incident cycles choose cand = 1.

    Returns:
        H_opt: optimized matrix
        sweeps_completed: number of sweeps executed
        total_updates: total coefficient updates made
        rank_sweep_1: GF(32) rank after sweep 1 (diagnostic only)
        final_rank: GF(32) rank after final sweep
    """
    if field is None:
        field = GF2mField.create(32)

    H = H_init.copy()
    canonical_edges = get_canonical_support_edges(binary_support)

    c4, c6, c8, edge_to_cycle_ids = enumerate_canonical_simple_cycles(binary_support)
    all_cycles = c4 + c6 + c8
    num_cycles = len(all_cycles)

    # Initial cycle degeneracy states
    is_degenerate = [classify_cycle_algebraic_degeneracy(cyc, H, field) for cyc in all_cycles]

    def _count_degeneracies() -> tuple[int, int, int]:
        d4 = sum(is_degenerate[i] for i in range(len(c4)))
        d6 = sum(is_degenerate[i] for i in range(len(c4), len(c4) + len(c6)))
        d8 = sum(is_degenerate[i] for i in range(len(c4) + len(c6), num_cycles))
        return d4, d6, d8

    curr_d4, curr_d6, curr_d8 = _count_degeneracies()
    rank_sweep_1 = -1
    sweeps_completed = 0
    total_updates = 0

    for sweep in range(1, max_sweeps + 1):
        sweeps_completed = sweep
        updates_in_sweep = 0

        for edge in canonical_edges:
            r, c = edge
            old_val = int(H[r, c])
            incident_ids = edge_to_cycle_ids.get(edge, [])

            if not incident_ids:
                # 0 incident cycles: all cand in 1..31 yield same objective (curr_d4, curr_d6, curr_d8).
                # Minimum key (curr_d4, curr_d6, curr_d8, cand) is at cand = 1.
                best_val = 1
                if best_val != old_val:
                    H[r, c] = best_val
                    updates_in_sweep += 1
                continue

            old_inc_4 = sum(is_degenerate[idx] for idx in incident_ids if all_cycles[idx].length == 4)
            old_inc_6 = sum(is_degenerate[idx] for idx in incident_ids if all_cycles[idx].length == 6)
            old_inc_8 = sum(is_degenerate[idx] for idx in incident_ids if all_cycles[idx].length == 8)

            best_key = (float("inf"), float("inf"), float("inf"), float("inf"))
            best_val = old_val
            best_states: list[bool] = []

            for cand in range(1, 32):
                if cand == old_val:
                    cand_states = [is_degenerate[idx] for idx in incident_ids]
                    cand_d4, cand_d6, cand_d8 = curr_d4, curr_d6, curr_d8
                else:
                    H[r, c] = cand
                    cand_states = [
                        classify_cycle_algebraic_degeneracy(all_cycles[idx], H, field)
                        for idx in incident_ids
                    ]
                    cand_inc_4 = sum(cand_states[k] for k, idx in enumerate(incident_ids) if all_cycles[idx].length == 4)
                    cand_inc_6 = sum(cand_states[k] for k, idx in enumerate(incident_ids) if all_cycles[idx].length == 6)
                    cand_inc_8 = sum(cand_states[k] for k, idx in enumerate(incident_ids) if all_cycles[idx].length == 8)

                    cand_d4 = curr_d4 - old_inc_4 + cand_inc_4
                    cand_d6 = curr_d6 - old_inc_6 + cand_inc_6
                    cand_d8 = curr_d8 - old_inc_8 + cand_inc_8

                cand_key = (cand_d4, cand_d6, cand_d8, cand)
                if cand_key < best_key:
                    best_key = cand_key
                    best_val = cand
                    best_states = cand_states

            if best_val != old_val:
                H[r, c] = best_val
                curr_d4, curr_d6, curr_d8, _ = best_key
                for k, idx in enumerate(incident_ids):
                    is_degenerate[idx] = best_states[k]
                updates_in_sweep += 1
            else:
                H[r, c] = old_val

        total_updates += updates_in_sweep

        if sweep == 1:
            rank_sweep_1 = compute_gf32_rank(H, field)

        if updates_in_sweep == 0:
            break

    final_rank = compute_gf32_rank(H, field)
    return H, sweeps_completed, total_updates, rank_sweep_1, final_rank


# ---------------------------------------------------------------------------
# Lane Constructors
# ---------------------------------------------------------------------------

def construct_lane_a_prototype(
    source: str,
    seed: int,
    max_sweeps: int = 2,
    field: Optional[GF2mField] = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Construct Lane A prototype on frozen V31 support via cycle-aware label optimization.

    - Support is strictly bit-identical to V31 baseline.
    - Initial labels drawn from Generator(PCG64(SeedSequence([seed, 3]))).
    - Local search over (deg_4, deg_6, deg_8, cand) with cached incremental updates.
    - MAX_SWEEPS = 2. Stop early on 0 updates.
    - Sweep 1 rank is diagnostic; final rank is hard validity gate.
    """
    if field is None:
        field = GF2mField.create(32)

    v31_mats = load_v31_qc_baseline_matrices()
    if source not in v31_mats:
        raise ValueError(f"Unknown source rate {source}")

    H_v31 = v31_mats[source]
    binary_support = (H_v31 != 0).astype(np.uint8)
    canonical_edges = get_canonical_support_edges(binary_support)

    # Initial labels
    label_rng = get_substream_generator(seed, stream_id=3)
    init_coeffs = sample_uniform_gf32_nonzero(label_rng, len(canonical_edges))

    H_init = np.zeros_like(H_v31, dtype=np.uint8)
    for (r, c), val in zip(canonical_edges, init_coeffs):
        H_init[r, c] = val

    H_opt, sweeps_completed, total_updates, rank_sweep_1, final_rank = optimize_lane_a_coefficients(
        H_init=H_init,
        binary_support=binary_support,
        max_sweeps=max_sweeps,
        field=field,
    )

    metrics = compute_structural_metrics(H_opt, lane="lane_a", source=source, seed=seed, field=field)
    metrics["sweeps_completed"] = sweeps_completed
    metrics["total_updates"] = total_updates
    metrics["rank_after_sweep_1"] = rank_sweep_1
    metrics["final_rank_GF32"] = final_rank

    return H_opt, metrics


def construct_lane_b_prototype(
    source: str,
    seed: int,
    field: Optional[GF2mField] = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Construct Lane B high-rate eIRA-like dual-diagonal structured prototype.

    - Matrix partition: H = [H_info | H_parity].
    - H_parity is m x m lower-bidiagonal with unit diagonal (all GF(32) element 1).
    - H_info: (1024 - m) columns, degree exactly 2 per column.
    - Check degrees initialized from H_parity.
    - Sequential placement with degree-balancing prioritized over 4-cycle avoidance.
    - Labels assigned after support completion via Generator(PCG64(SeedSequence([seed, 2]))).
    """
    if field is None:
        field = GF2mField.create(32)

    m = SOURCE_CHECKS.get(source)
    if m is None:
        raise ValueError(f"Unknown source {source}")

    n = BLOCK_LENGTH
    n_info = n - m

    support_rng = get_substream_generator(seed, stream_id=1)
    coeff_rng = get_substream_generator(seed, stream_id=2)

    # 1. H_parity: m x m lower-bidiagonal (consuming 0 coefficient-RNG draws)
    H_parity = np.zeros((m, m), dtype=np.uint8)
    for i in range(m):
        H_parity[i, i] = 1
        if i + 1 < m:
            H_parity[i + 1, i] = 1

    # Initialize check total degrees from H_parity
    check_degrees = np.count_nonzero(H_parity, axis=1)  # check 0 degree 1, checks 1..m-1 degree 2

    # Frozen check tie-permutation
    check_tie_perm = support_rng.permutation(m).tolist()
    check_rank_in_perm = {c: idx for idx, c in enumerate(check_tie_perm)}

    # 2. H_info Support Construction
    H_info_support = np.zeros((m, n_info), dtype=np.uint8)
    check_pairs_connected: set[tuple[int, int]] = set()

    for j in range(n_info):
        # First edge: minimum current degree among all m checks
        min_deg_1 = int(check_degrees.min())
        eligible_1 = [c for c in range(m) if check_degrees[c] == min_deg_1]
        c1 = min(eligible_1, key=lambda c: check_rank_in_perm[c])

        check_degrees[c1] += 1

        # Second edge: eligible = all checks except c1
        eligible_2_checks = [c for c in range(m) if c != c1]
        min_deg_2 = min(check_degrees[c] for c in eligible_2_checks)
        min_deg_set = [c for c in eligible_2_checks if check_degrees[c] == min_deg_2]

        no_4cycle_cands = [
            c for c in min_deg_set if (min(c1, c), max(c1, c)) not in check_pairs_connected
        ]

        if no_4cycle_cands:
            c2 = min(no_4cycle_cands, key=lambda c: check_rank_in_perm[c])
        else:
            c2 = min(min_deg_set, key=lambda c: check_rank_in_perm[c])

        check_degrees[c2] += 1

        H_info_support[c1, j] = 1
        H_info_support[c2, j] = 1
        check_pairs_connected.add((min(c1, c2), max(c1, c2)))

    # 3. Assign H_info Coefficients after support completion
    canonical_info_edges = get_canonical_support_edges(H_info_support)
    info_coeffs = sample_uniform_gf32_nonzero(coeff_rng, len(canonical_info_edges))

    H_info = np.zeros((m, n_info), dtype=np.uint8)
    for (r, c), val in zip(canonical_info_edges, info_coeffs):
        H_info[r, c] = val

    # 4. Concatenate full matrix H = [H_info | H_parity]
    H = np.hstack([H_info, H_parity]).astype(np.uint8)

    metrics = compute_structural_metrics(H, lane="lane_b", source=source, seed=seed, field=field)
    return H, metrics


def construct_lane_c_prototype(
    source: str,
    seed: int,
    field: Optional[GF2mField] = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Construct Lane C SC-inspired finite spatially banded prototype (L=8, w=2).

    - Variable nodes: L=8 positions, exactly 128 variables per position.
    - Check nodes allocated via frozen edge-load vector.
    - Capacity gate verified prior to generation.
    - Support placement: variable at position p connects to check positions p and min(p+1, 7).
    - Labels assigned after support completion via Generator(PCG64(SeedSequence([seed, 2]))).
    """
    if field is None:
        field = GF2mField.create(32)

    m = SOURCE_CHECKS.get(source)
    allocations = LANE_C_CHECK_ALLOCATIONS.get(source)
    if m is None or allocations is None:
        raise ValueError(f"Unknown source rate {source}")

    if not check_lane_c_capacity_feasibility(m, allocations):
        raise ValueError(f"Lane C capacity sanity failure for source {source}")

    n = BLOCK_LENGTH
    support_rng = get_substream_generator(seed, stream_id=1)
    coeff_rng = get_substream_generator(seed, stream_id=2)

    check_offsets = [0] * 8
    for p in range(1, 8):
        check_offsets[p] = check_offsets[p - 1] + allocations[p - 1]

    check_ranges = [list(range(check_offsets[p], check_offsets[p] + allocations[p])) for p in range(8)]

    # Generate frozen check permutations for each spatial position sequentially (order 0..7)
    check_rank_in_perm: dict[int, dict[int, int]] = {}
    position_permutations: list[list[int]] = []
    for p in range(8):
        perm_p = support_rng.permutation(check_ranges[p]).tolist()
        position_permutations.append(perm_p)
        check_rank_in_perm[p] = {c: idx for idx, c in enumerate(perm_p)}

    # Support construction
    H_support = np.zeros((m, n), dtype=np.uint8)
    check_degrees = np.zeros(m, dtype=np.int32)
    check_pairs_connected: set[tuple[int, int]] = set()

    for j in range(n):
        p = min(j // 128, 7)

        if p < 7:
            # Edge 1: check position p
            min_deg_1 = min(check_degrees[c] for c in check_ranges[p])
            min_deg_set_1 = [c for c in check_ranges[p] if check_degrees[c] == min_deg_1]
            c1 = min(min_deg_set_1, key=lambda c: check_rank_in_perm[p][c])
            check_degrees[c1] += 1

            # Edge 2: check position p + 1
            min_deg_2 = min(check_degrees[c] for c in check_ranges[p + 1])
            min_deg_set_2 = [c for c in check_ranges[p + 1] if check_degrees[c] == min_deg_2]
            no_4c_2 = [c for c in min_deg_set_2 if (min(c1, c), max(c1, c)) not in check_pairs_connected]
            if no_4c_2:
                c2 = min(no_4c_2, key=lambda c: check_rank_in_perm[p + 1][c])
            else:
                c2 = min(min_deg_set_2, key=lambda c: check_rank_in_perm[p + 1][c])
            check_degrees[c2] += 1

        else:
            # Position 7: both edges in check position 7
            min_deg_1 = min(check_degrees[c] for c in check_ranges[7])
            min_deg_set_1 = [c for c in check_ranges[7] if check_degrees[c] == min_deg_1]
            c1 = min(min_deg_set_1, key=lambda c: check_rank_in_perm[7][c])
            check_degrees[c1] += 1

            eligible_p7 = [c for c in check_ranges[7] if c != c1]
            min_deg_2 = min(check_degrees[c] for c in eligible_p7)
            min_deg_set_2 = [c for c in eligible_p7 if check_degrees[c] == min_deg_2]
            no_4c_2 = [c for c in min_deg_set_2 if (min(c1, c), max(c1, c)) not in check_pairs_connected]
            if no_4c_2:
                c2 = min(no_4c_2, key=lambda c: check_rank_in_perm[7][c])
            else:
                c2 = min(min_deg_set_2, key=lambda c: check_rank_in_perm[7][c])
            check_degrees[c2] += 1

        H_support[c1, j] = 1
        H_support[c2, j] = 1
        check_pairs_connected.add((min(c1, c2), max(c1, c2)))

    # Assign coefficients after support completion
    canonical_edges = get_canonical_support_edges(H_support)
    coeffs = sample_uniform_gf32_nonzero(coeff_rng, len(canonical_edges))

    H = np.zeros((m, n), dtype=np.uint8)
    for (r, c), val in zip(canonical_edges, coeffs):
        H[r, c] = val

    metrics = compute_structural_metrics(H, lane="lane_c", source=source, seed=seed, field=field)
    metrics["position_permutations"] = position_permutations
    return H, metrics


# ---------------------------------------------------------------------------
# Structural Prototype Selection
# ---------------------------------------------------------------------------

def select_structural_winner(prototypes: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
    """Select exactly one winning prototype from a candidate list for a source/lane.

    Tie-break order among valid prototypes:
    1. Lower degenerate 4-cycles
    2. Lower degenerate 6-cycles
    3. Lower degenerate 8-cycles
    4. Lower support 4-cycles
    5. Lower max check degree (dc_max)
    6. Lower construction seed (deterministic tie-breaker)
    """
    valid_candidates = [p for p in prototypes if p.get("structurally_valid", False)]
    if not valid_candidates:
        return None, "STRUCTURAL_PROTOTYPE_NOT_READY"

    def _sort_key(p: dict[str, Any]) -> tuple[Any, ...]:
        return (
            p.get("degenerate_cycles_4", 0),
            p.get("degenerate_cycles_6", 0),
            p.get("degenerate_cycles_8", 0),
            p.get("support_cycles_4", 0),
            p.get("row_degree_max", 16),
            p.get("construction_seed", 0),
        )

    valid_candidates.sort(key=_sort_key)
    return valid_candidates[0], "WINNER_SELECTED"


def _load_v38r1_reference_metrics(
    reference_metrics_path: Path | str = V38R1_RUN01_METRICS_PATH,
) -> dict[str, dict[str, Any]]:
    """Load the committed V38-P0 structural metrics indexed by matrix ID."""
    path = Path(reference_metrics_path)
    with path.open("r", encoding="utf-8") as handle:
        records = json.load(handle)
    if not isinstance(records, list) or len(records) != 27:
        raise ValueError(f"V38R1 requires exactly 27 run_01 metrics, got {len(records) if isinstance(records, list) else 'non-list'}")

    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("matrix_id"), str):
            raise ValueError("V38R1 run_01 metrics contain a record without matrix_id")
        matrix_id = record["matrix_id"]
        if matrix_id in indexed:
            raise ValueError(f"Duplicate V38R1 run_01 matrix_id: {matrix_id}")
        indexed[matrix_id] = record
    return indexed


def _check_v38r1_metric_match(
    expected: dict[str, Any],
    actual: dict[str, Any],
    matrix_id: str,
) -> None:
    """Fail closed when reconstructed metrics drift from committed run_01."""
    for key in V38R1_REQUIRED_METRIC_KEYS:
        if key not in expected or key not in actual:
            raise ValueError(f"V38R1 winner metric missing required field {matrix_id}: {key}")
    for key, expected_value in expected.items():
        if key not in actual or actual[key] != expected_value:
            actual_value = actual.get(key, "<missing>")
            raise ValueError(
                f"V38R1 winner metric mismatch for {matrix_id}: "
                f"{key} expected={expected_value!r} actual={actual_value!r}"
            )


def reconstruct_v38r1_winners(
    reference_metrics_path: Path | str = V38R1_RUN01_METRICS_PATH,
) -> dict[str, dict[str, tuple[np.ndarray, dict[str, Any]]]]:
    """Rebuild exactly the nine frozen V38R1 winners without candidate search.

    The committed V38-P0 structural JSON is the metric authority.  Matrix
    bytes are rebuilt from the accepted constructors and frozen seeds; the
    ignored local NPZ is deliberately not an input.
    """
    reference_by_id = _load_v38r1_reference_metrics(reference_metrics_path)
    field = GF2mField.create(DIMENSION)
    if field.primitive_polynomial != POLYNOMIAL:
        raise RuntimeError(
            f"V38R1 field polynomial mismatch: expected {POLYNOMIAL}, got {field.primitive_polynomial}"
        )

    constructors: dict[str, Callable[..., tuple[np.ndarray, dict[str, Any]]]] = {
        "lane_a": construct_lane_a_prototype,
        "lane_b": construct_lane_b_prototype,
        "lane_c": construct_lane_c_prototype,
    }
    winners: dict[str, dict[str, tuple[np.ndarray, dict[str, Any]]]] = {
        lane: {} for lane in V38R1_LANE_ORDER
    }
    reconstructed_count = 0

    for lane in V38R1_LANE_ORDER:
        for source in V38R1_SOURCE_ORDER:
            seed = V38R1_WINNER_SEEDS[lane][source]
            matrix_id = f"{lane}_{source}_s{seed}"
            expected = reference_by_id.get(matrix_id)
            if expected is None:
                raise ValueError(f"Missing frozen V38R1 winner in run_01 metrics: {matrix_id}")
            if expected.get("lane") != lane or expected.get("source") != source:
                raise ValueError(f"V38R1 winner identity mismatch in run_01 metrics: {matrix_id}")

            constructor = constructors[lane]
            if lane == "lane_a":
                matrix, metrics = constructor(
                    source=source, seed=seed, max_sweeps=2, field=field
                )
            else:
                matrix, metrics = constructor(source=source, seed=seed, field=field)
            _check_v38r1_metric_match(expected, metrics, matrix_id)
            if lane == "lane_c" and "position_permutations" not in expected:
                raise ValueError(f"Missing frozen Lane C permutations in run_01 metrics: {matrix_id}")
            winners[lane][source] = (matrix, metrics)
            reconstructed_count += 1

    if reconstructed_count != 9:
        raise AssertionError(f"V38R1 must reconstruct exactly 9 winners, got {reconstructed_count}")
    return winners


# ---------------------------------------------------------------------------
# Finite Block Evaluation & Diagnostic Plumbing
# ---------------------------------------------------------------------------

def evaluate_single_block(
    H: np.ndarray,
    source: str,
    block_seed: int,
    lane: str,
    construction_seed: int,
    counts: np.ndarray,
    max_iter: int = 30,
    damping_alpha: float = 1.0,
    fake_runner: bool = False,
    field: Optional[GF2mField] = None,
) -> dict[str, Any]:
    """Evaluate one finite block under row-layered FFT-QSPA decoder."""
    if field is None:
        field = GF2mField.create(32)

    matrix_id = f"{lane}_{source}_s{construction_seed}"
    idx, alice, bob = sample_empirical_block(counts, seed=block_seed, size=BLOCK_LENGTH)
    u1_alice, u2_alice, u1_bob, u2_bob = factorize_f03(alice, bob)
    prior = get_conditional_posterior_l2(counts, bob, u1_alice)
    raw_errors = int(np.sum(u2_alice != u2_bob))
    syn_true = syndrome_of_gf32(H, u2_alice, field)

    if fake_runner:
        final_errors = max(0, raw_errors - 10)
        iters = 30
        runtime = 0.001
        syn_ok = False
        exact = bool(final_errors == 0)
        status = "max_iter"
    else:
        dec_res = decode_row_layered_fftqspa(
            H, prior, syn_true, max_iter=max_iter, damping_alpha=damping_alpha, field=field
        )
        final_errors = int(np.sum(dec_res.x_hat != u2_alice))
        iters = dec_res.iterations
        runtime = dec_res.runtime_s
        syn_ok = dec_res.syndrome_ok
        exact = bool(np.array_equal(dec_res.x_hat, u2_alice))
        status = dec_res.status

    return {
        "source": source,
        "block_seed": block_seed,
        "lane": lane,
        "construction_seed": construction_seed,
        "matrix_id": matrix_id,
        "errors_initial": raw_errors,
        "errors_final": final_errors,
        "exact_l2": exact,
        "syndrome_ok": syn_ok,
        "iterations": iters,
        "status": status,
        "runtime_s": runtime,
    }


# ---------------------------------------------------------------------------
# Aggregation & Triage Decision Gates
# ---------------------------------------------------------------------------

def validate_block_records_integrity(block_records: list[dict[str, Any]]) -> tuple[bool, str]:
    """Validate that the block record set satisfies exact frozen 15-block requirements."""
    if len(block_records) != 15:
        return False, f"Expected exactly 15 records, got {len(block_records)}"

    seen_pairs: set[tuple[str, int]] = set()
    for rec in block_records:
        src = rec.get("source")
        seed = rec.get("block_seed")
        if src not in SOURCE_CHECKS:
            return False, f"Unexpected source rate: {src}"
        if seed not in V36_A3_BLOCK_SEEDS.get(src, []):
            return False, f"Unexpected seed {seed} for source {src}"
        pair = (src, seed)
        if pair in seen_pairs:
            return False, f"Duplicate record for source {src} seed {seed}"
        seen_pairs.add(pair)

    # Check exact coverage for all 3 sources (5 seeds each)
    for src, expected_seeds in V36_A3_BLOCK_SEEDS.items():
        src_seeds = {pair[1] for pair in seen_pairs if pair[0] == src}
        if src_seeds != set(expected_seeds):
            return False, f"Incomplete seed set for source {src}: expected {expected_seeds}, got {src_seeds}"

    return True, "INTEGRITY_OK"


def aggregate_lane_results(
    block_records: list[dict[str, Any]],
    reference_baseline: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Aggregate block evaluation records for a lane and compute paired comparisons keyed by (source, block_seed)."""
    if reference_baseline is None:
        reference_baseline = V31_BASELINE_REFERENCE

    integrity_ok, integrity_reason = validate_block_records_integrity(block_records)
    if not integrity_ok:
        return {
            "records_count": len(block_records),
            "status": "INVALID_BLOCK_SET",
            "integrity_ok": False,
            "failure_reason": integrity_reason,
        }

    lane_name = block_records[0]["lane"]
    errors_final_list = [r["errors_final"] for r in block_records]
    exact_count = sum(1 for r in block_records if r.get("exact_l2", False))
    overall_mean = float(np.mean(errors_final_list))
    overall_median = float(np.median(errors_final_list))

    ref_median_overall = float(reference_baseline["overall_median"])
    if ref_median_overall > 0:
        overall_median_improvement = (ref_median_overall - overall_median) / ref_median_overall
    else:
        overall_median_improvement = 0.0

    # Index candidate records by (source, block_seed)
    records_by_key: dict[tuple[str, int], dict[str, Any]] = {
        (r["source"], r["block_seed"]): r for r in block_records
    }

    source_stats: dict[str, Any] = {}
    improve_count = 0
    equal_count = 0
    worsen_count = 0
    worst_single_degradation = 0

    for src in SOURCE_CHECKS:
        expected_seeds = V36_A3_BLOCK_SEEDS[src]
        src_recs = [records_by_key[(src, s)] for s in expected_seeds]

        src_errs = [r["errors_final"] for r in src_recs]
        src_exact = sum(1 for r in src_recs if r.get("exact_l2", False))
        src_mean = float(np.mean(src_errs))
        src_median = float(np.median(src_errs))

        ref_src = reference_baseline["sources"].get(src, {})
        ref_src_median = float(ref_src.get("median", 0.0))
        ref_src_seed_map = ref_src.get("seed_map", FROZEN_BASELINE_ERROR_MAP[src])

        if ref_src_median > 0:
            median_delta_s = (src_median - ref_src_median) / ref_src_median
        else:
            median_delta_s = 0.0 if src_median == 0 else 1.0

        # Exact key-based paired block comparison
        for rec in src_recs:
            b_seed = rec["block_seed"]
            ref_e = ref_src_seed_map[b_seed]
            lane_e = rec["errors_final"]
            diff = lane_e - ref_e
            if diff < 0:
                improve_count += 1
            elif diff == 0:
                equal_count += 1
            else:
                worsen_count += 1
                if diff > worst_single_degradation:
                    worst_single_degradation = diff

        source_stats[src] = {
            "exact_count": src_exact,
            "mean_errors": src_mean,
            "median_errors": src_median,
            "median_delta_s": float(median_delta_s),
            "ref_median": ref_src_median,
        }

    return {
        "lane": lane_name,
        "records_count": len(block_records),
        "integrity_ok": True,
        "status": "OK",
        "exact_recovery_count": exact_count,
        "overall_mean_errors": overall_mean,
        "overall_median_errors": overall_median,
        "overall_median_improvement": float(overall_median_improvement),
        "improve_count": improve_count,
        "equal_count": equal_count,
        "worsen_count": worsen_count,
        "worst_single_block_degradation": worst_single_degradation,
        "source_stats": source_stats,
    }


def evaluate_triage_gate(aggregated_results: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Evaluate whether a lane achieves PROMISING_DIRECTION_SIGNAL."""
    if not aggregated_results.get("integrity_ok", False) or aggregated_results.get("records_count", 0) != 15:
        return False, {"gate_passed": False, "reason": "INVALID_BLOCK_SET"}

    source_stats = aggregated_results.get("source_stats", {})
    if len(source_stats) != 3:
        return False, {"gate_passed": False, "reason": "INCOMPLETE_SOURCES"}

    # Non-degradation gate: all sources median_delta_s <= +0.05
    for src, stats in source_stats.items():
        if stats["median_delta_s"] > 0.05:
            return False, {
                "gate_passed": False,
                "reason": f"Source {src} degraded by > 5% (delta = {stats['median_delta_s']:.4f})",
            }

    # Error reduction criteria: at least one must hold
    exact_count = aggregated_results["exact_recovery_count"]
    overall_median = aggregated_results["overall_median_errors"]
    improve_count = aggregated_results["improve_count"]
    worsen_count = aggregated_results["worsen_count"]

    crit_a = exact_count > 0
    crit_b = overall_median <= 150.0  # operational integer threshold: 177 * 0.85 = 150.45 -> <= 150
    crit_c = (improve_count >= 10) and (worsen_count <= 3)

    passed = bool(crit_a or crit_b or crit_c)
    details = {
        "gate_passed": passed,
        "criterion_a": crit_a,
        "criterion_b": crit_b,
        "criterion_c": crit_c,
        "exact_count": exact_count,
        "overall_median": overall_median,
        "improve_count": improve_count,
        "worsen_count": worsen_count,
    }
    return passed, details


def determine_v38_terminal_state(
    lane_statuses: dict[str, str],
    integrity_ok: bool = True,
) -> str:
    """Determine the final overall V38 terminal state across all lanes."""
    if not integrity_ok:
        return V38_DIRECTION_EVIDENCE_INVALID

    signal_lanes = [lane for lane, st in lane_statuses.items() if st == LANE_PROMISING_DIRECTION_SIGNAL]
    ready_lanes = [
        lane for lane, st in lane_statuses.items()
        if st in (LANE_READY, LANE_EVALUATED_NO_SIGNAL, LANE_PROMISING_DIRECTION_SIGNAL)
    ]

    if len(signal_lanes) == 1:
        return V38_SINGLE_ROUTE_SIGNAL
    elif len(signal_lanes) >= 2:
        return V38_MULTIPLE_ROUTE_SIGNALS
    elif len(ready_lanes) > 0:
        return V38_NO_ROUTE_SIGNAL
    else:
        return V38_NO_STRUCTURAL_PROTOTYPE_READY


# ---------------------------------------------------------------------------
# Future Development Orchestration (Guarded; Not Executed During Implementation)
# ---------------------------------------------------------------------------

def run_v38_development(
    development_execution_authorized: bool = False,
    fake_runner: bool = False,
    custom_seed_dict: Optional[dict[str, dict[str, list[int]]]] = None,
) -> dict[str, Any]:
    """Execute the full frozen V38 development triage workflow.

    Software Guard:
        Requires development_execution_authorized=True, otherwise raises PermissionError.
        This guard prevents accidental or unauthorized execution during planning/implementation.

    Maximum Workload Enforced:
        - Structural prototype generation attempts: exactly 27 across all 3 lanes x 3 sources x 3 seeds.
        - New decoder runs: <= 45 (15 per READY lane; 0 for NOT_READY lanes).
    """
    if not development_execution_authorized:
        raise PermissionError(
            "V38 development execution not authorized. "
            "Formal development execution requires explicit authorization."
        )

    seed_dict = custom_seed_dict if custom_seed_dict is not None else LANE_PRODUCTION_SEEDS

    # Load empirical counts for all 3 sources
    counts_by_source = load_v25_channel_counts()

    field = GF2mField.create(32)
    lane_constructors = {
        "lane_a": construct_lane_a_prototype,
        "lane_b": construct_lane_b_prototype,
        "lane_c": construct_lane_c_prototype,
    }

    prototypes_generated_count = 0
    decoder_runs_count = 0

    all_prototype_metrics: dict[str, dict[str, list[dict[str, Any]]]] = {}
    lane_winners: dict[str, dict[str, tuple[np.ndarray, dict[str, Any]]]] = {}
    lane_statuses: dict[str, str] = {}
    lane_aggregates: dict[str, dict[str, Any]] = {}
    all_block_records: list[dict[str, Any]] = []

    # 1. Structural prototype generation: ALL 27 attempts must be completed unconditionally
    for lane_name, constructor in lane_constructors.items():
        all_prototype_metrics[lane_name] = {}
        lane_winners[lane_name] = {}

        for src in ("1M", "1p5M", "2M"):
            seeds = seed_dict[lane_name][src]
            assert len(seeds) == 3, f"Must have exactly 3 pre-registered seeds for {lane_name}/{src}, got {len(seeds)}"

            src_prototypes: list[dict[str, Any]] = []
            src_mats: dict[int, np.ndarray] = {}

            for seed in seeds:
                assert prototypes_generated_count < 27, "Maximum prototype generation cap (27) exceeded"
                H_proto, metrics = constructor(source=src, seed=seed, field=field)
                prototypes_generated_count += 1
                src_prototypes.append(metrics)
                src_mats[seed] = H_proto

            all_prototype_metrics[lane_name][src] = src_prototypes

            winner_metric, sel_status = select_structural_winner(src_prototypes)
            if winner_metric is not None:
                win_seed = winner_metric["construction_seed"]
                lane_winners[lane_name][src] = (src_mats[win_seed], winner_metric)

    assert prototypes_generated_count == 27, f"Expected exactly 27 structural prototype attempts, got {prototypes_generated_count}"

    # 2. Evaluation Phase: only lanes with valid winners for all 3 sources receive decoder runs
    for lane_name in ("lane_a", "lane_b", "lane_c"):
        has_all_sources = all(src in lane_winners[lane_name] for src in ("1M", "1p5M", "2M"))

        if not has_all_sources:
            lane_statuses[lane_name] = LANE_STRUCTURAL_NOT_READY
            lane_aggregates[lane_name] = {
                "lane": lane_name,
                "records_count": 0,
                "status": "STRUCTURAL_NOT_READY",
                "integrity_ok": False,
            }
            continue

        # Evaluate the 3 winners on 15 frozen development blocks
        lane_block_records: list[dict[str, Any]] = []
        for src in ("1M", "1p5M", "2M"):
            H_win, win_metric = lane_winners[lane_name][src]
            win_seed = win_metric["construction_seed"]
            counts = counts_by_source[src]

            for b_seed in V36_A3_BLOCK_SEEDS[src]:
                assert decoder_runs_count < 45, "Maximum new decoder runs cap (45) exceeded"
                rec = evaluate_single_block(
                    H=H_win,
                    source=src,
                    block_seed=b_seed,
                    lane=lane_name,
                    construction_seed=win_seed,
                    counts=counts,
                    max_iter=30,
                    damping_alpha=1.0,
                    fake_runner=fake_runner,
                    field=field,
                )
                decoder_runs_count += 1
                lane_block_records.append(rec)
                all_block_records.append(rec)

        agg = aggregate_lane_results(lane_block_records)
        lane_aggregates[lane_name] = agg
        passed, gate_details = evaluate_triage_gate(agg)
        if passed:
            lane_statuses[lane_name] = LANE_PROMISING_DIRECTION_SIGNAL
        else:
            lane_statuses[lane_name] = LANE_EVALUATED_NO_SIGNAL

    terminal_state = determine_v38_terminal_state(lane_statuses, integrity_ok=True)

    return {
        "prototypes_generated_count": prototypes_generated_count,
        "decoder_runs_count": decoder_runs_count,
        "all_prototype_metrics": all_prototype_metrics,
        "lane_winners": lane_winners,
        "lane_statuses": lane_statuses,
        "lane_aggregates": lane_aggregates,
        "terminal_state": terminal_state,
        "all_block_records": all_block_records,
    }


def run_v38r1_development(
    development_execution_authorized: bool = False,
    fake_runner: bool = False,
    reference_metrics_path: Path | str = V38R1_RUN01_METRICS_PATH,
) -> dict[str, Any]:
    """Run the frozen V38R1 decoder-only successor with exactly 45 calls."""
    if not development_execution_authorized:
        raise PermissionError(
            "V38R1 development execution not authorized. "
            "Explicit --development-execution-authorized is required."
        )

    winners = reconstruct_v38r1_winners(reference_metrics_path)
    counts_by_source = load_v25_channel_counts()
    field = GF2mField.create(DIMENSION)
    if field.primitive_polynomial != POLYNOMIAL:
        raise RuntimeError(
            f"V38R1 field polynomial mismatch: expected {POLYNOMIAL}, got {field.primitive_polynomial}"
        )

    decoder_runs_count = 0
    lane_statuses: dict[str, str] = {}
    lane_aggregates: dict[str, dict[str, Any]] = {}
    triage_gate_details: dict[str, dict[str, Any]] = {}
    all_block_records: list[dict[str, Any]] = []

    for lane in V38R1_LANE_ORDER:
        lane_records: list[dict[str, Any]] = []
        for source in V38R1_SOURCE_ORDER:
            matrix, metrics = winners[lane][source]
            for block_seed in V36_A3_BLOCK_SEEDS[source]:
                if decoder_runs_count >= 45:
                    raise AssertionError("V38R1 decoder call cap exceeded")
                record = evaluate_single_block(
                    H=matrix,
                    source=source,
                    block_seed=block_seed,
                    lane=lane,
                    construction_seed=int(metrics["construction_seed"]),
                    counts=counts_by_source[source],
                    max_iter=30,
                    damping_alpha=1.0,
                    fake_runner=fake_runner,
                    field=field,
                )
                decoder_runs_count += 1
                lane_records.append(record)
                all_block_records.append(record)

        aggregate = aggregate_lane_results(lane_records)
        lane_aggregates[lane] = aggregate
        passed, details = evaluate_triage_gate(aggregate)
        triage_gate_details[lane] = details
        lane_statuses[lane] = (
            LANE_PROMISING_DIRECTION_SIGNAL if passed else LANE_EVALUATED_NO_SIGNAL
        )

    if decoder_runs_count != 45:
        raise AssertionError(f"V38R1 requires exactly 45 decoder calls, got {decoder_runs_count}")

    winner_metrics = [
        winners[lane][source][1]
        for lane in V38R1_LANE_ORDER
        for source in V38R1_SOURCE_ORDER
    ]
    return {
        "cycle_id": "V38R1",
        "predecessor_cycle": "V38P0",
        "winners_reconstructed_count": 9,
        "winner_metrics": winner_metrics,
        "lane_winners": winners,
        "decoder_runs_count": decoder_runs_count,
        "lane_statuses": lane_statuses,
        "lane_aggregates": lane_aggregates,
        "triage_gate_details": triage_gate_details,
        "terminal_state": determine_v38_terminal_state(lane_statuses, integrity_ok=True),
        "all_block_records": all_block_records,
        "fake_runner": fake_runner,
    }
