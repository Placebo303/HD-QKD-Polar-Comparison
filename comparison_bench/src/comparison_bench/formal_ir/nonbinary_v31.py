"""V31 deterministic finite-graph redesign gate.

This module implements the frozen V31 contract: F03 GF32+GF32, V25
source-conditioned channel, fixed m1=16, projective-capacity-aware PEG and a
deterministic QC-cyclic control family, and Bob-only full-window validation at
n=1024 and n=2048.  It deliberately does not rerun any V30R packet.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
import json
import math
import time
from numbers import Integral
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from . import nonbinary_v30 as v30
from . import nonbinary_v29 as v29
from . import nonbinary_v28 as v28
from .nonbinary_field import GF2mField, get_field_spec

Q = 32
N_VALUES = (1024, 2048)
M1 = 16
SOURCE_ORDER = tuple(v30.SOURCE_ORDER)
SOURCE_IDS = dict(v30.SOURCE_IDS)
SOURCE_PARQUETS = dict(v30.SOURCE_PARQUETS)
SOURCE_DELAY_PS = dict(v30.SOURCE_DELAY_PS)
SOURCE_H = {label: dict(v30.SOURCE_H[label]) for label in SOURCE_ORDER}
SOURCE_M_TOTAL_BY_N = {
    1024: {"1M": 200, "1p5M": 206, "2M": 208},
    2048: {"1M": 413, "1p5M": 426, "2M": 430},
}
SOURCE_FRAME_RANGES = {"1M": (1200, 1599), "1p5M": (1660, 2059), "2M": (2187, 2586)}
FRAME_PAIRS = 256
TAG_BITS = 64
M1_SEEDS = (30101, 30102, 30103, 30104, 30105)
M1_N_SAMPLES = 2000
M1_MAX_ITER = 200
M1_ENTROPY_TOL_BITS = 0.01
M1_STREAK = 20
M3_MAX_ITER = 200
M3_STREAK = 20
# Per-n DE/decoder cumulative wall/resource gate.  The 24h V30R gate was
# raised for V31 because n=2048 L2 non-converging decodes are extremely slow;
# this is a resource-limit parameter, not a search/tuning knob.
RESOURCE_LIMIT_SECONDS = 5.0 * 24.0 * 60.0 * 60.0
THRESHOLD_RATIO = 0.95
MAX_SUPPORT_OCCUPANCY = Q - 1  # 31 nonzero GF(32) ratios
FAMILY_PEG = "PEG-capacity-aware"
FAMILY_QC = "QC-cyclic-projective"
FAMILY_ORDER = {FAMILY_PEG: 0, FAMILY_QC: 1}
SUPPORTED_FAMILIES = (FAMILY_PEG, FAMILY_QC)
TERMINAL_PASS = "finite_graph_pass"
TERMINAL_FAIL = "finite_graph_fail"
TERMINAL_DE_FAIL = "de_allocation_fail"
TERMINAL_RESOURCE = "resource_blocked"
TERMINAL_IMPL = "implementation_blocked"
FIELD = v30.FIELD
FIELD_ID = v30.FIELD_ID
PRIMITIVE_POLYNOMIAL = v30.PRIMITIVE_POLYNOMIAL
RATIO_ORDER = v30.RATIO_ORDER
V25_CHANNEL_COUNTS = v30.V25_CHANNEL_COUNTS
V26_CANONICAL = v30.V26_CANONICAL
V28R_CANONICAL = v30.V28R_CANONICAL
V30R_CANONICAL = "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v30_20260820/run_01"
M1_CONFIRMATION_CALLS_PER_N = len(M1_SEEDS) * len(SOURCE_ORDER) * 2

__all__ = [
    "Q", "N_VALUES", "M1", "SOURCE_ORDER", "SOURCE_IDS", "SOURCE_PARQUETS",
    "SOURCE_DELAY_PS", "SOURCE_H", "SOURCE_M_TOTAL_BY_N", "SOURCE_FRAME_RANGES",
    "FAMILY_PEG", "FAMILY_QC", "SUPPORTED_FAMILIES", "MAX_SUPPORT_OCCUPANCY",
    "frozen_v31_config", "build_allocation_plan", "run_m1_confirmation",
    "build_supports_peg_capacity", "build_supports_qc_cyclic", "build_supports",
    "build_layer", "build_matrix_packet", "run_m2", "validation_frame_manifest",
    "load_validation_blocks", "run_m3_gate", "run_v31_gate", "verify_v31",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _resolved_repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (_repo_root() / path).resolve()


def frozen_v31_config(n: int = 1024) -> dict[str, Any]:
    """Return the immutable V31 configuration for one block length."""
    n = int(n)
    if n not in N_VALUES:
        raise ValueError(f"V31 supports only n in {N_VALUES}")
    field = get_field_spec(Q)
    if field.primitive_polynomial != PRIMITIVE_POLYNOMIAL or field.field_id != FIELD_ID:
        raise ValueError("pinned GF32 field metadata changed")
    sources: dict[str, Any] = {}
    for label in SOURCE_ORDER:
        m_total = int(SOURCE_M_TOTAL_BY_N[n][label])
        m2 = m_total - M1
        if m2 <= 0 or m2 >= n:
            raise ValueError(f"invalid m2={m2} for {label}, n={n}")
        h = {"L1": float(SOURCE_H[label]["L1"]), "L2": float(SOURCE_H[label]["L2"])}
        total_leak = float(5 * m_total + TAG_BITS)
        f_total = total_leak / (float(n) * (h["L1"] + h["L2"]))
        if f_total >= 1.3:
            raise ValueError(f"f_total not below 1.3 for {label}, n={n}")
        sources[label] = {
            "source_id": SOURCE_IDS[label], "pairs_parquet": SOURCE_PARQUETS[label],
            "delay_used_ps": int(SOURCE_DELAY_PS[label]),
            "m_total": m_total, "m1": M1, "m2": m2, "H": h,
            "leak_total_bits": float(total_leak), "f_total": float(f_total),
        }
    return {
        "schema": "nbldpc_v31_frozen_config_v1", "q": Q, "n": n,
        "factorization": "F03_natural_MSB_to_LSB_GF32_plus_GF32",
        "m1": M1, "lambda": {2: 1},
        "source_order": list(SOURCE_ORDER), "sources": sources,
        "families": list(SUPPORTED_FAMILIES),
        "field": {
            "constructor": "GF2mField.create(32)", "q": Q, "m": 5,
            "primitive_polynomial": PRIMITIVE_POLYNOMIAL,
            "basis": field.basis, "symbol_encoding": field.symbol_encoding,
            "field_id": FIELD_ID, "ratio_order": RATIO_ORDER,
        },
        "m1_confirmation": {
            "seeds": list(M1_SEEDS), "n_samples": M1_N_SAMPLES,
            "max_iter": M1_MAX_ITER, "entropy_tol_bits": M1_ENTROPY_TOL_BITS,
            "streak": M1_STREAK, "calls_per_n": M1_CONFIRMATION_CALLS_PER_N,
        },
        "m3": {
            "max_iter": M3_MAX_ITER, "streak": M3_STREAK,
            "threshold_ratio": THRESHOLD_RATIO,
            "block_frames": int(n) // FRAME_PAIRS,
            "blocks_per_source": (400 // (int(n) // FRAME_PAIRS)),
        },
        "input_bindings": {
            "v25_inventory": v30.V25_INVENTORY,
            "v25_split_manifest": v30.V25_SPLIT_MANIFEST,
            "v25_channel_counts": V25_CHANNEL_COUNTS,
            "v26_canonical": V26_CANONICAL,
            "v28r_canonical": V28R_CANONICAL,
            "v30r_canonical": V30R_CANONICAL,
        },
        "projective_gate": "zero_duplicate_projective_keys_and_proportional_pairs",
        "tanner6_score": "(degenerate_6_new,ratio_index)",
        "tanner8": "topology_only",
        "standard_variable_side_ace": "omitted_for_dv_2",
        "support_occupancy_limit": MAX_SUPPORT_OCCUPANCY,
    }


def build_allocation_plan(n: int = 1024, h_values: Mapping[str, Mapping[str, float]] | None = None) -> dict[str, Any]:
    """Build the single frozen m1=16 allocation record for one n."""
    n = int(n)
    if n not in N_VALUES:
        raise ValueError(f"V31 supports only n in {N_VALUES}")
    h_values = dict(h_values or {label: SOURCE_H[label] for label in SOURCE_ORDER})
    allocation_id = f"m1_16_n{n}"
    sources: dict[str, Any] = {}
    for label in SOURCE_ORDER:
        m_total = int(SOURCE_M_TOTAL_BY_N[n][label])
        m2 = m_total - M1
        h = {"L1": float(h_values[label]["L1"]), "L2": float(h_values[label]["L2"])}
        layers: dict[str, Any] = {}
        for layer, m in (("L1", M1), ("L2", m2)):
            leak = float(5 * m)
            layers[layer] = {
                "m": int(m), "H_bits_per_symbol": float(h[layer]),
                "rate": float(1.0 - float(m) / float(n)),
                "leak_bits": leak,
                "f": float(leak / (float(n) * float(h[layer]))),
            }
        total_leak = float(5 * m_total + TAG_BITS)
        sources[label] = {
            "source": label, "source_id": SOURCE_IDS[label],
            "delay_used_ps": int(SOURCE_DELAY_PS[label]),
            "m_total": m_total, "m1": M1, "m2": int(m2), "H": h,
            "layers": layers, "leak_total_bits": total_leak,
            "f_total": float(total_leak / (float(n) * (h["L1"] + h["L2"]))),
        }
        if sources[label]["f_total"] >= 1.3:
            raise ValueError(f"f_total not below 1.3 for {label}, n={n}")
    return {
        "schema": "nbldpc_v31_allocation_v1", "allocation_id": allocation_id,
        "m1": M1, "n": int(n),
        "m2_by_source": {label: sources[label]["m2"] for label in SOURCE_ORDER},
        "sources": sources, "tag_bits": TAG_BITS,
        "total_formula": "leak_total=5*m_total+64; f_total=leak_total/(n*(H_L1+H_L2))",
    }


def _confirmation_items(allocation: Mapping[str, Any]) -> Iterable[dict[str, Any]]:
    n = int(allocation["n"])
    for seed in M1_SEEDS:
        for label in SOURCE_ORDER:
            source = allocation["sources"][label]
            for layer in ("L1", "L2"):
                info = source["layers"][layer]
                yield {
                    "allocation_id": allocation["allocation_id"], "n": n,
                    "m1": allocation["m1"], "m2": source["m2"], "source": label,
                    "source_id": source["source_id"], "delay_used_ps": source["delay_used_ps"],
                    "layer": layer, "seed": int(seed), "rate": info["rate"],
                    "f": info["f"], "H_bits_per_symbol": info["H_bits_per_symbol"],
                    "n_samples": M1_N_SAMPLES, "max_iter": M1_MAX_ITER,
                }


def _is_de_pass(row: Mapping[str, Any]) -> bool:
    entropy = row.get("final_entropy_bits")
    return (bool(row.get("converged")) and entropy is not None
            and math.isfinite(float(entropy)) and float(entropy) <= M1_ENTROPY_TOL_BITS)


def _invoke_de_runner(runner: Any, item: Mapping[str, Any], adapter: Any) -> Mapping[str, Any]:
    return v30._invoke_de_runner(runner, item, adapter)


def _normalize_de_result(raw: Mapping[str, Any], item: Mapping[str, Any], runtime_s: float) -> dict[str, Any]:
    return v30._normalize_de_result(raw, item, runtime_s)


def run_m1_confirmation(
    plans: Mapping[int, Mapping[str, Any]], *,
    de_runner: Any = None, adapters: Mapping[str, Any] | None = None,
    resource_limit_seconds: float = RESOURCE_LIMIT_SECONDS,
) -> dict[str, Any]:
    """Run the pre-registered 60-call DE confirmation (30 per n)."""
    plans = dict(plans)
    adapters = dict(adapters or {})
    if de_runner is None and not adapters:
        adapters = v30.load_v26_adapters_once()
    calls: list[dict[str, Any]] = []
    meter = 0.0
    terminal: str | None = None
    per_n: dict[str, Any] = {}
    for n in N_VALUES:
        allocation = plans[n]
        items = list(_confirmation_items(allocation))
        own: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            if meter >= float(resource_limit_seconds):
                terminal = TERMINAL_RESOURCE
                break
            started = time.monotonic()
            try:
                raw = _invoke_de_runner(de_runner, item, adapters.get(item["source"]))
                elapsed = time.monotonic() - started
                row = _normalize_de_result(raw, item, elapsed)
                runtime = float(row["runtime_s"])
                if not math.isfinite(runtime) or runtime < 0:
                    raise ValueError("DE runtime_s must be finite and nonnegative")
                meter += runtime
            except Exception as exc:
                row = {**item, "converged": False, "final_entropy_bits": None,
                       "iterations": 0, "terminal": TERMINAL_IMPL,
                       "nonfinite_result": False, "entropy_trace_bits": [],
                       "runtime_s": time.monotonic() - started,
                       "error": f"{type(exc).__name__}: {exc}"}
                meter += float(row["runtime_s"])
                terminal = TERMINAL_IMPL
            if row.get("terminal") == TERMINAL_IMPL or row.get("nonfinite_result"):
                terminal = TERMINAL_IMPL
            row["call_index"] = len(calls)
            calls.append(row)
            own.append(row)
            if terminal is not None:
                break
            if meter >= float(resource_limit_seconds) and len(calls) < 60:
                terminal = TERMINAL_RESOURCE
                break
        pass_n = bool(len(own) == len(items) and all(_is_de_pass(row) for row in own))
        per_n[str(n)] = {
            "n": int(n), "expected_calls": len(items), "n_calls": len(own),
            "all_calls_pass": pass_n,
            "worst_final_entropy": max((float(row.get("final_entropy_bits", math.inf))
                                        for row in own), default=math.inf),
        }
        if terminal is None and not pass_n:
            terminal = TERMINAL_DE_FAIL
        if terminal is not None:
            break
    confirmed_n = [int(n) for n, info in per_n.items() if info["all_calls_pass"]]
    if terminal is None and len(confirmed_n) == len(N_VALUES):
        terminal = "de_allocation_pass"
    elif terminal is None:
        terminal = TERMINAL_DE_FAIL
    return {
        "schema": "nbldpc_v31_de_confirmation_v1", "calls": calls,
        "n_calls": len(calls), "expected_calls": 60,
        "per_n": per_n, "confirmed_n": confirmed_n,
        "resource_meter_seconds": meter, "resource_limit_seconds": float(resource_limit_seconds),
        "terminal": terminal,
    }


# ---------------------------------------------------------------------------
# M2 deterministic finite matrices
# ---------------------------------------------------------------------------

def build_supports_peg_capacity(m: int, n: int = 1024) -> list[tuple[int, int]]:
    """Projective-capacity-aware PEG supports with occupancy<=31 hard gate.

    Vectorized numpy scoring over the full lexicographic candidate set with an
    incrementally maintained all-pairs shortest-distance matrix.  The score is
    exactly (occupancy_after, component_flag, distance_cost, max_degree_after,
    sumsq_after, a, b) and it is minimized component-wise (equivalent to the
    lexicographic minimum) to avoid a full per-column sort.
    """
    m, n = int(m), int(n)
    if m < 2 or n < 1:
        raise ValueError("invalid matrix dimensions")
    rows = np.arange(m, dtype=np.int64)
    # Upper-triangle lexicographic candidate pairs (a,b), a<b.
    triu = np.triu_indices(m, k=1)
    A = triu[0].astype(np.int64)
    B = triu[1].astype(np.int64)
    occ = np.zeros((m, m), dtype=np.int64)
    dist = np.full((m, m), np.inf, dtype=np.float64)
    np.fill_diagonal(dist, 0.0)
    degrees = np.zeros(m, dtype=np.int64)
    base_sumsq = 0
    selected: list[tuple[int, int]] = []
    for _ in range(n):
        occ_ab = occ[A, B]
        valid = occ_ab < MAX_SUPPORT_OCCUPANCY
        if not bool(valid.any()):
            raise ValueError("PEG-capacity-aware: no candidate survives the occupancy<=31 hard gate")
        occ_valid = occ_ab[valid]
        A1 = A[valid]
        B1 = B[valid]
        # 1) minimimal occupancy_after
        min_occ = int(occ_valid.min())
        m1 = occ_valid == min_occ
        A2 = A1[m1]
        B2 = B1[m1]
        # 2) minimal component_flag (prefer disconnected = 0)
        dist2 = dist[A2, B2]
        comp = np.isfinite(dist2).astype(np.int64)
        min_comp = int(comp.min())
        m2 = comp == min_comp
        A3 = A2[m2]
        B3 = B2[m2]
        # 3) minimal distance_cost
        dist3 = dist[A3, B3]
        if min_comp == 1:
            cost = -(2 * dist3 + 2.0).astype(np.int64)
        else:
            cost = np.zeros(len(A3), dtype=np.int64)
        min_cost = int(cost.min())
        m3 = cost == min_cost
        A4 = A3[m3]
        B4 = B3[m3]
        # 4) minimal max_degree_after
        deg_a = degrees[A4]
        deg_b = degrees[B4]
        max_deg_base = int(degrees.max())
        max_after = np.maximum(np.maximum(max_deg_base, deg_a + 1), deg_b + 1)
        min_max = int(max_after.min())
        m4 = max_after == min_max
        A5 = A4[m4]
        B5 = B4[m4]
        # 5) minimal sumsq_after
        sumsq_after = base_sumsq + 2 * (degrees[A5] + degrees[B5]) + 2
        min_sumsq = int(sumsq_after.min())
        m5 = sumsq_after == min_sumsq
        A6 = A5[m5]
        B6 = B5[m5]
        # 6) lexicographically smallest (a,b)
        order = np.lexsort((B6, A6))
        idx = int(order[0])
        a = int(A6[idx])
        b = int(B6[idx])
        selected.append((a, b))
        old_a = int(degrees[a])
        old_b = int(degrees[b])
        base_sumsq = base_sumsq + 2 * (old_a + old_b) + 2
        occ[a, b] += 1
        occ[b, a] += 1
        degrees[a] += 1
        degrees[b] += 1
        # Incremental all-pairs shortest-path update for the new edge (a,b).
        dist = np.minimum(dist, dist[:, a:a + 1] + 1.0 + dist[b:b + 1, :])
        dist = np.minimum(dist, dist[:, b:b + 1] + 1.0 + dist[a:a + 1, :])
        np.fill_diagonal(dist, 0.0)
    return selected


def build_supports_qc_cyclic(m: int, n: int = 1024) -> list[tuple[int, int]]:
    """Deterministic QC-cyclic-projective support enumeration.

    Supports are (a, (a+s) mod m) for increasing shift s>=1 and base row a,
    skipping invalid s%m==0 candidates, until n supports are selected.
    """
    m, n = int(m), int(n)
    if m < 2 or n < 1:
        raise ValueError("invalid matrix dimensions")
    selected: list[tuple[int, int]] = []
    s = 1
    while len(selected) < n:
        for a in range(m):
            if len(selected) >= n:
                break
            b = (a + s) % m
            if a == b:
                continue
            selected.append((min(a, b), max(a, b)))
        s += 1
    occ = Counter(selected)
    if any(v > MAX_SUPPORT_OCCUPANCY for v in occ.values()):
        raise ValueError("QC-cyclic-projective: support occupancy exceeds 31")
    return selected


def build_supports(family: str, m: int, n: int = 1024) -> list[tuple[int, int]]:
    if family == FAMILY_PEG:
        return build_supports_peg_capacity(m, n)
    if family == FAMILY_QC:
        return build_supports_qc_cyclic(m, n)
    raise ValueError(f"unsupported V31 family: {family}")


def _by_support_index(
    prior_supports: Sequence[Sequence[int]],
    prior_coefficients: Sequence[Sequence[int]],
) -> dict[tuple[int, int], list[tuple[int, int, int]]]:
    by_support: dict[tuple[int, int], list[tuple[int, int, int]]] = defaultdict(list)
    if len(prior_supports) != len(prior_coefficients):
        raise ValueError("prior support/coefficient lengths differ")
    for k, (support, coeff) in enumerate(zip(prior_supports, prior_coefficients)):
        a, b = map(int, support)
        ha, hb = map(int, coeff)
        if a > b:
            a, b = b, a
            ha, hb = hb, ha
        if a == b or not ha or not hb:
            raise ValueError("invalid prior degree-two column")
        by_support[(a, b)].append((int(k), ha, hb))
    return by_support


def _count_degenerate_tanner6_for_ratio(
    field: GF2mField,
    by_support: Mapping[tuple[int, int], Sequence[tuple[int, int, int]]],
    current_column: int,
    support: Sequence[int],
    coefficients: Sequence[int],
) -> int:
    a, b = map(int, support)
    ha, hb = map(int, coefficients)
    if a > b:
        a, b = b, a
        ha, hb = hb, ha
    all_nodes: set[int] = {a, b}
    for key in by_support:
        all_nodes.update(int(x) for x in key)
    seen: set[tuple[int, int, int, int, int, int]] = set()
    degenerate = 0
    for c in sorted(all_nodes):
        if c in (a, b):
            continue
        left = by_support.get((min(a, c), max(a, c)), ())
        right = by_support.get((min(c, b), max(c, b)), ())
        for k1, ha_k1, hc_k1 in left:
            for k2, hc_k2, hb_k2 in right:
                if k1 == k2:
                    continue
                canonical = v30.canonical_tanner6_tuple(current_column, a, k1, c, k2, b)
                if canonical in seen:
                    continue
                seen.add(canonical)
                product = v30.tanner6_alternating_product(
                    field, (ha, hb), (ha_k1, hc_k1), (hc_k2, hb_k2),
                )
                if product == 1:
                    degenerate += 1
    return degenerate


def select_projective_ratio_v31(
    field: GF2mField,
    prior_supports: Sequence[Sequence[int]],
    prior_coefficients: Sequence[Sequence[int]],
    current_column: int,
    current_support: Sequence[int],
    used_ratios: Iterable[int] | None = None,
) -> dict[str, Any]:
    """Same projective/Tanner-6 selection as V30R, with early-stop optimization.

    The result is identical to ``v30.select_projective_ratio``: the chosen
    ratio minimizes (degenerate_6_new, ratio_index) over ratios not already
    used by the same support.
    """
    a, b = map(int, current_support)
    if a >= b:
        raise ValueError("current support must be sorted")
    prior_supports = list(prior_supports)
    prior_coefficients = list(prior_coefficients)
    if used_ratios is None:
        used: set[int] = set()
        for support, coeff in zip(prior_supports, prior_coefficients):
            if tuple(map(int, support)) != (a, b):
                continue
            if len(coeff) != 2 or not int(coeff[0]) or not int(coeff[1]):
                raise ValueError("prior coefficients must be nonzero")
            used.add(field.mul(int(coeff[1]), field.inverse(int(coeff[0]))))
    else:
        used = {int(x) for x in used_ratios}
    by_support = _by_support_index(prior_supports, prior_coefficients)
    best: tuple[int, int] | None = None
    best_ratio: int | None = None
    for ratio_index, ratio in enumerate(field.nonzero_cycle):
        if int(ratio) in used:
            continue
        count = _count_degenerate_tanner6_for_ratio(
            field, by_support, current_column, (a, b), (1, int(ratio)),
        )
        if best is None or (count, int(ratio_index)) < best:
            best = (int(count), int(ratio_index))
            best_ratio = int(ratio)
            if count == 0:
                break
    if best is None:
        raise ValueError(f"no projectively unique ratio remains for support {(a, b)}")
    selected_cycles = _count_degenerate_tanner6_for_ratio(
        field, by_support, current_column, (a, b), (1, best_ratio),
    )
    return {
        "coefficients": [1, best_ratio], "ratio": best_ratio,
        "ratio_index": int(best[1]), "score": list(best),
        "new_cycle_count": None,
        "candidate_count": None,
        "projective_key": [a, b, best_ratio],
    }


def cycle_topology(supports: Sequence[Sequence[int]], *, m: int | None = None) -> dict[str, Any]:
    """Bounded 4/6/8-cycle topology diagnostics.

    The 4-cycle count is exact from support multiplicities.  Exact 6/8-cycle
    enumeration over the check multigraph is C(m,3)/C(m,4) and is infeasible
    for the large check counts used by V31 L2 (m~200-414); it is therefore
    computed exactly only for small ``m`` and otherwise reported as ``None``
    with ``six_eight_exact=False`` (diagnostic only; these counts never enter
    the finite pass/fail gate).  Girth is always computed exactly on the simple
    check graph via BFS.
    """
    counts: Counter[tuple[int, int]] = Counter(tuple(sorted(map(int, p))) for p in supports)
    four = sum(value * (value - 1) // 2 for value in counts.values())
    girth = None
    nodes = sorted({node for support in counts for node in support})
    adjacency: dict[int, set[int]] = {node: set() for node in nodes}
    for (u, v) in counts:
        adjacency[u].add(v)
        adjacency[v].add(u)
    best = None
    for start in nodes:
        dist = {start: 0}
        queue = [start]
        while queue:
            cur = queue.pop(0)
            for nb in sorted(adjacency[cur]):
                if nb not in dist:
                    dist[nb] = dist[cur] + 1
                    queue.append(nb)
        # a cycle appears when a neighbor already discovered is not the parent at depth>=1
        for (u, v) in counts:
            if dist.get(u) is None or dist.get(v) is None:
                continue
            cand = dist[u] + 1 + dist[v] + 1
            if cand < 4:
                continue
            # only consider when u,v are at the same BFS depth (even cycle) or differ by 1 handled via parent
            if cand < (best or float("inf")):
                # this overcounts; BFS-based girth is refined below
                pass
    # exact girth by BFS from each node: shortest cycle through start
    for s in nodes:
        parent: dict[int, int] = {}
        depth: dict[int, int] = {s: 0}
        queue = [s]
        while queue:
            cur = queue.pop(0)
            for nb in sorted(adjacency[cur]):
                if nb not in depth:
                    depth[nb] = depth[cur] + 1
                    parent[nb] = cur
                    queue.append(nb)
                elif parent.get(cur) != nb:
                    cand = depth[cur] + depth[nb] + 1
                    if best is None or cand < best:
                        best = cand
    if best is not None:
        girth = best
    m_val = m if m is not None else max(nodes, default=0) + 1
    small = int(m_val) <= 60
    if small:
        six = 0
        for a, b, c in combinations(nodes, 3):
            six += counts[(a, b)] * counts[(a, c)] * counts[(b, c)]
        eight = 0
        for a, b, c, d in combinations(nodes, 4):
            eight += counts[(a, b)] * counts[(b, c)] * counts[(c, d)] * counts[(a, d)]
            eight += counts[(a, b)] * counts[(b, d)] * counts[(c, d)] * counts[(a, c)]
            eight += counts[(a, c)] * counts[(b, c)] * counts[(b, d)] * counts[(a, d)]
        six_val: int | None = int(six)
        eight_val: int | None = int(eight)
        exact = True
    else:
        six_val = None
        eight_val = None
        exact = False
    return {
        "four_cycle_count": int(four), "six_cycle_count": six_val,
        "eight_cycle_count": eight_val, "six_eight_exact": exact, "girth": girth,
    }


def build_layer(
    m: int, n: int = 1024, *, family: str = FAMILY_PEG,
    field: GF2mField | None = None, require_full_rank: bool = True,
) -> tuple[tuple[tuple[int, ...], ...], dict[str, Any]]:
    """Build one deterministic degree-two matrix and its replayable audit."""
    field = field or FIELD
    if field.q != Q:
        raise ValueError("V31 matrices require GF(32)")
    if family not in SUPPORTED_FAMILIES:
        raise ValueError(f"unsupported V31 family: {family}")
    m, n = int(m), int(n)
    supports = build_supports(family, m, n)
    if len(supports) != n:
        raise ValueError("support construction returned the wrong number of columns")
    occ = Counter(supports)
    max_support_occupancy = max(occ.values(), default=0)
    capacity_ok = bool(max_support_occupancy <= MAX_SUPPORT_OCCUPANCY)
    if not capacity_ok:
        raise ValueError(f"support occupancy exceeds {MAX_SUPPORT_OCCUPANCY}")
    rows = np.zeros((m, n), dtype=np.int64)
    prior_supports: list[tuple[int, int]] = []
    prior_coefficients: list[tuple[int, int]] = []
    used_by_support: dict[tuple[int, int], set[int]] = defaultdict(set)
    label_replay: list[dict[str, Any]] = []
    for j, support in enumerate(supports):
        a, b = (int(support[0]), int(support[1]))
        label = select_projective_ratio_v31(
            field, prior_supports, prior_coefficients, j, (a, b),
            used_by_support[(a, b)],
        )
        ha, hb = map(int, label["coefficients"])
        rows[a, j] = ha
        rows[b, j] = hb
        prior_supports.append((a, b))
        prior_coefficients.append((ha, hb))
        used_by_support[(a, b)].add(hb)
        label_replay.append({
            "column": int(j), "support": [a, b],
            "selected_ratio_index": int(label["ratio_index"]),
            "selected_score": list(label["score"]),
            "projective_key": list(label["projective_key"]),
        })
    matrix = tuple(tuple(int(x) for x in row) for row in rows.tolist())
    projective = v30.projective_column_audit(matrix, field)
    topology = cycle_topology(supports, m=m)
    tanner6_degenerate_total = sum(int(item["selected_score"][0]) for item in label_replay)
    tanner6_degenerate_max = max((int(item["selected_score"][0]) for item in label_replay), default=0)
    audit = {
        "schema": "nbldpc_v31_matrix_audit_v1", "family": family,
        "shape": [m, n], "support_order": [list(pair) for pair in supports],
        "label_replay": label_replay, "projective": {
            "columns": projective["columns"], "support_groups": projective["support_groups"],
            "support_group_count": projective["support_group_count"],
            "max_support_group_multiplicity": projective["max_support_group_multiplicity"],
            "duplicate_projective_classes": projective["duplicate_projective_classes"],
            "affected_columns": projective["affected_columns"],
            "proportional_pairs": projective["proportional_pairs"],
            "ordinary_four_cycle_count": projective["ordinary_four_cycle_count"],
            "zero_columns": projective["zero_columns"],
            "invalid_degree_columns": projective["invalid_degree_columns"],
            "zero_rows": projective["zero_rows"],
            "rank": projective["rank"], "full_row_rank": projective["full_row_rank"],
            "projective_safe": projective["projective_safe"],
        },
        "support_occupancy": {f"{a},{b}": int(count) for (a, b), count in sorted(occ.items())},
        "max_support_occupancy": int(max_support_occupancy),
        "capacity_ok": capacity_ok,
        "rank": int(projective["rank"]), "full_row_rank": bool(projective["full_row_rank"]),
        "four_cycle_count": int(topology["four_cycle_count"]),
        "six_cycle_count": topology["six_cycle_count"],
        "eight_cycle_count": topology["eight_cycle_count"],
        "six_eight_exact": bool(topology["six_eight_exact"]),
        "girth": topology["girth"],
        "tanner6_newly_closed_total": int(len(label_replay)),
        "tanner6_degenerate_total": int(tanner6_degenerate_total),
        "tanner6_degenerate_max_per_column": int(tanner6_degenerate_max),
        "ordinary_short_cycle_frc_rule": "Pi(C)!=1; Pi(C)=1 is degenerate",
        "tanner8_rule": "topology_only",
        "standard_variable_side_ace": "omitted_for_dv_2",
        "projective_hard_gate": bool(projective["projective_safe"]),
        "construction_ok": bool(capacity_ok and projective["projective_safe"]
                              and (not require_full_rank or projective["full_row_rank"])),
    }
    return matrix, audit


def build_matrix_packet(
    m1: int, m2_by_source: Mapping[str, int], *, n: int = 1024,
    family: str = FAMILY_PEG, allocation_id: str | None = None,
) -> dict[str, Any]:
    if set(m2_by_source) != set(SOURCE_ORDER):
        raise ValueError("m2_by_source must contain exactly the three frozen sources")
    if isinstance(n, bool) or not isinstance(n, Integral) or int(n) < 1:
        raise ValueError("n must be a positive integer")
    try:
        l1, l1_audit = build_layer(int(m1), n, family=family)
    except Exception as exc:
        raise ValueError(f"V31 build_matrix_packet L1(m={m1}, n={n}) failed: {type(exc).__name__}: {exc}") from exc
    l2: dict[str, tuple[tuple[int, ...], ...]] = {}
    l2_audits: dict[str, dict[str, Any]] = {}
    for source in SOURCE_ORDER:
        try:
            matrix, audit = build_layer(int(m2_by_source[source]), n, family=family)
        except Exception as exc:
            raise ValueError(f"V31 build_matrix_packet L2:{source}(m={m2_by_source[source]}, n={n}) failed: {type(exc).__name__}: {exc}") from exc
        l2[source], l2_audits[source] = matrix, audit
    components = {"L1": l1_audit["four_cycle_count"]}
    components.update({f"L2:{source}": l2_audits[source]["four_cycle_count"] for source in SOURCE_ORDER})
    packet = {
        "schema": "nbldpc_v31_matrix_packet_v1",
        "matrix_id": f"{allocation_id or f'm1_{int(m1)}'}_n{n}|{family}",
        "allocation_id": allocation_id or f"m1_{int(m1)}",
        "family": family, "q": Q, "n": int(n), "m1": int(m1),
        "m2_by_source": {source: int(m2_by_source[source]) for source in SOURCE_ORDER},
        "field": v30.frozen_v30r_config(n=n)["field"],
        "matrices": {"L1": l1, "L2": l2},
        "audits": {"L1": l1_audit, "L2": l2_audits},
        "four_cycle_components": components,
        "four_cycle_count": int(sum(components.values())),
        "max_support_occupancy": max(
            [l1_audit["max_support_occupancy"]] + [a["max_support_occupancy"] for a in l2_audits.values()],
            default=0,
        ),
        "projective_hard_gate": bool(l1_audit["projective_hard_gate"]
                                     and all(a["projective_hard_gate"] for a in l2_audits.values())),
        "full_row_rank": bool(l1_audit["full_row_rank"]
                              and all(a["full_row_rank"] for a in l2_audits.values())),
    }
    packet["capacity_ok"] = bool(packet["max_support_occupancy"] <= MAX_SUPPORT_OCCUPANCY)
    packet["construction_ok"] = bool(packet["capacity_ok"] and packet["projective_hard_gate"]
                                     and packet["full_row_rank"])
    return packet


def run_m2(plans: Mapping[int, Mapping[str, Any]], *, wallclock_budget_seconds: float | None = None,
           start_time: float | None = None) -> dict[str, Any]:
    """Build both family packets for each passing n."""
    plans = dict(plans)
    start_time = time.monotonic() if start_time is None else start_time
    result: dict[str, Any] = {}
    for n in N_VALUES:
        allocation = plans[n]
        packets: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        for family in SUPPORTED_FAMILIES:
            if wallclock_budget_seconds is not None and time.monotonic() - start_time > float(wallclock_budget_seconds):
                raise _ChunkTimeout(f"m2_n{n}_{family}")
            try:
                packet = build_matrix_packet(
                    int(allocation["m1"]), allocation["m2_by_source"],
                    n=n, family=family, allocation_id=allocation["allocation_id"],
                )
                packet["packet_id"] = packet["matrix_id"]
                if not packet["construction_ok"]:
                    raise ValueError("V31 construction hard gate failed")
                packets.append(packet)
            except Exception as exc:
                rejected.append({
                    "n": int(n), "family": family,
                    "allocation_id": allocation["allocation_id"],
                    "terminal": TERMINAL_FAIL,
                    "error": f"{type(exc).__name__}: {exc}",
                })
        result[n] = {
            "n": int(n), "packets": packets, "rejected": rejected,
            "packet_cap_ok": len(packets) <= 2,
        }
    return result


# ---------------------------------------------------------------------------
# M3 Bob-only validation
# ---------------------------------------------------------------------------

def validation_frame_manifest() -> dict[str, Any]:
    """Return the frozen V31 frame source identities (shared by both n)."""
    sources: dict[str, Any] = {}
    for label in SOURCE_ORDER:
        start, end = SOURCE_FRAME_RANGES[label]
        sources[label] = {
            "source_id": SOURCE_IDS[label], "delay_used_ps": int(SOURCE_DELAY_PS[label]),
            "pairs_parquet": SOURCE_PARQUETS[label],
            "frame_start": start, "frame_end": end, "frame_count": end - start + 1,
            "pair_count_per_frame": FRAME_PAIRS, "frames": list(range(start, end + 1)),
        }
    return {"schema": "nbldpc_v31_frame_manifest_v1", "sources": sources}


def load_validation_blocks(n: int = 1024, input_root: str | Path | None = None) -> list[dict[str, Any]]:
    """Load V25 validation frames and group them into blocks for the given n."""
    n = int(n)
    if n not in N_VALUES:
        raise ValueError(f"V31 supports only n in {N_VALUES}")
    block_frames = n // FRAME_PAIRS
    root = Path(input_root) if input_root is not None else _repo_root()
    cfg = {
        "source_order": list(SOURCE_ORDER),
        "sources": {
            label: {
                "source_id": SOURCE_IDS[label], "delay_used_ps": int(SOURCE_DELAY_PS[label]),
                "frame_start": SOURCE_FRAME_RANGES[label][0],
                "frame_end": SOURCE_FRAME_RANGES[label][1],
                "block_count": 400 // block_frames,
            } for label in SOURCE_ORDER
        },
    }
    parts = v29.select_frames(None, cfg, input_root=root)
    blocks: list[dict[str, Any]] = []
    global_index = 0
    for label in SOURCE_ORDER:
        info = cfg["sources"][label]
        frame_ids = list(range(int(info["frame_start"]), int(info["frame_end"]) + 1))
        part = parts[label]
        for block_index in range(len(frame_ids) // block_frames):
            group_ids = frame_ids[block_index * block_frames:(block_index + 1) * block_frames]
            groups = [part[part["frame_id"] == fid].sort_values("pair_idx") for fid in group_ids]
            alice = np.concatenate([g["alice_symbol"].to_numpy(dtype=np.int64) for g in groups])
            bob = np.concatenate([g["bob_symbol"].to_numpy(dtype=np.int64) for g in groups])
            if len(alice) != n or len(bob) != n:
                raise ValueError(f"{label} block {block_index}: expected {n} symbols")
            blocks.append({
                "source": label, "source_id": info["source_id"],
                "delay_used_ps": info["delay_used_ps"],
                "block_index": block_index, "global_block_index": global_index,
                "frame_ids": group_ids,
                "pair_idx_ranges": [[0, FRAME_PAIRS - 1] for _ in group_ids],
                "alice_symbols": alice, "bob_symbols": bob,
            })
            global_index += 1
    _validate_validation_blocks(blocks, n)
    return blocks


def _validate_validation_blocks(blocks: Sequence[Mapping[str, Any]], n: int) -> None:
    n = int(n)
    block_frames = n // FRAME_PAIRS
    blocks_per_source = 400 // block_frames
    if len(blocks) != len(SOURCE_ORDER) * blocks_per_source:
        raise ValueError(f"V31 n={n} validation requires {len(SOURCE_ORDER) * blocks_per_source} blocks")
    for label in SOURCE_ORDER:
        own = sorted((block for block in blocks if block.get("source") == label),
                     key=lambda block: int(block.get("block_index", -1)))
        if len(own) != blocks_per_source or [int(b.get("block_index", -1)) for b in own] != list(range(blocks_per_source)):
            raise ValueError(f"{label}: invalid block index sequence")
        start, end = SOURCE_FRAME_RANGES[label]
        for block in own:
            index = int(block["block_index"])
            expected_global_index = SOURCE_ORDER.index(label) * blocks_per_source + index
            if int(block.get("global_block_index", -1)) != expected_global_index:
                raise ValueError(f"{label} block {index}: global block index mismatch")
            expected_frames = list(range(start + index * block_frames, start + (index + 1) * block_frames))
            if list(block.get("frame_ids", [])) != expected_frames:
                raise ValueError(f"{label} block {index}: frame ids mismatch")
            if block.get("source_id") != SOURCE_IDS[label] or block.get("delay_used_ps") != SOURCE_DELAY_PS[label]:
                raise ValueError(f"{label} block {index}: source metadata mismatch")
            if list(block.get("pair_idx_ranges", [])) != [[0, FRAME_PAIRS - 1]] * block_frames:
                raise ValueError(f"{label} block {index}: pair-index ranges mismatch")
            for key in ("alice_symbols", "bob_symbols"):
                values = np.asarray(block.get(key), dtype=np.int64)
                if values.shape != (n,) or np.any(values < 0) or np.any(values >= 1024):
                    raise ValueError(f"{label} block {index}: {key} shape/domain mismatch")


def _run_packet_full_window(
    packet: Mapping[str, Any], blocks: Sequence[Mapping[str, Any]], *,
    max_iter: int, streak: int, decoder_runner: Any,
    adapters: Mapping[str, Any], resource_meter: float,
    resource_limit_seconds: float, records: list[dict[str, Any]],
    wallclock_budget_seconds: float | None = None,
) -> tuple[dict[str, dict[str, int]], float, str | None]:
    """Run one packet over ALL validation blocks, persisting each record first."""
    n = int(packet["n"])
    family = str(packet["family"])
    start_time = time.monotonic()
    first_source_blocks = sorted(
        (b for b in blocks if b.get("source") == SOURCE_ORDER[0]),
        key=lambda b: int(b.get("block_index", -1)),
    )
    block_indices = [int(b.get("block_index", -1)) for b in first_source_blocks]
    stats: dict[str, dict[str, int]] = {
        label: {"completed": 0, "offline_exact": 0, "tag_verified": 0, "false_accept": 0,
                "l1_ok": 0, "l2_ok": 0}
        for label in SOURCE_ORDER
    }
    terminal: str | None = None
    for label in SOURCE_ORDER:
        selected = [block for block in blocks if block.get("source") == label]
        selected.sort(key=lambda block: int(block.get("block_index", -1)))
        if len(selected) != len(block_indices):
            return stats, resource_meter, TERMINAL_IMPL
        for block in selected:
            if resource_meter >= float(resource_limit_seconds):
                return stats, resource_meter, TERMINAL_RESOURCE
            if wallclock_budget_seconds is not None and time.monotonic() - start_time > float(wallclock_budget_seconds):
                raise _ChunkTimeout(f"m3_n{n}_{family}_block_{int(block.get('block_index', -1))}")
            try:
                block_public, public, truth = v30._block_public_and_syndromes(block, packet)
                started = time.monotonic()
                result = v30._invoke_decoder(
                    decoder_runner, block_public, public, adapters.get(label), packet,
                    {"max_iter": int(max_iter), "streak": int(streak)},
                )
                elapsed = time.monotonic() - started
                record = v30._finite_block_record(block, public, result, truth, packet, elapsed)
                runtime = float(record["runtime_s"])
                if not math.isfinite(runtime) or runtime < 0:
                    raise ValueError("decoder runtime_s must be finite and nonnegative")
                resource_meter += runtime
            except Exception as exc:
                record = {
                    "schema": "nbldpc_v31_block_result_v1",
                    "packet_id": packet.get("packet_id"), "source": label,
                    "block_index": int(block.get("block_index", -1)),
                    "frame_ids": list(block.get("frame_ids", [])), "l1_ok": False,
                    "l1_status": TERMINAL_IMPL, "l2_ok": False, "l2_status": "not_run",
                    "l2_conditioning": "not_run", "l2_not_run_due_l1": True,
                    "l1_syndrome_ok": False, "l2_syndrome_ok": False,
                    "offline_exact": False, "tag_verified": False, "false_accept": False,
                    "l1_symbol_errors": None, "l2_symbol_errors": None,
                    "l1_iterations": 0, "l2_iterations": 0, "decoder_calls": 0,
                    "runtime_s": time.monotonic() - started,
                    "error": f"{type(exc).__name__}: {exc}",
                }
                resource_meter += float(record["runtime_s"])
                terminal = TERMINAL_IMPL
            record["n"] = n
            record["family"] = family
            records.append(record)
            s = stats[label]
            s["completed"] += 1
            s["offline_exact"] += int(bool(record.get("offline_exact")))
            s["tag_verified"] += int(bool(record.get("tag_verified")))
            s["false_accept"] += int(bool(record.get("false_accept")))
            s["l1_ok"] += int(bool(record.get("l1_ok")))
            s["l2_ok"] += int(bool(record.get("l2_ok")))
            if terminal == TERMINAL_IMPL:
                return stats, resource_meter, terminal
    return stats, resource_meter, None


def _packet_summary(packet: Mapping[str, Any], records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    n = int(packet["n"])
    family = str(packet["family"])
    packet_id = str(packet.get("packet_id", packet.get("matrix_id")))
    rows = [r for r in records if str(r.get("packet_id")) == packet_id and int(r.get("n", -1)) == n]
    per_source: dict[str, Any] = {}
    total_blocks = 0
    total_exact = 0
    total_tag = 0
    total_false = 0
    for label in SOURCE_ORDER:
        own = sorted((r for r in rows if r.get("source") == label),
                     key=lambda r: int(r.get("block_index", -1)))
        block_count = len(own)
        exact = sum(int(bool(r.get("offline_exact"))) for r in own)
        tag = sum(int(bool(r.get("tag_verified"))) for r in own)
        false_accept = sum(int(bool(r.get("false_accept"))) for r in own)
        l1_ok = sum(int(bool(r.get("l1_ok"))) for r in own)
        l2_ok = sum(int(bool(r.get("l2_ok"))) for r in own)
        threshold = math.ceil(THRESHOLD_RATIO * block_count) if block_count else 0
        failures = [{
            "block_index": int(r.get("block_index", -1)),
            "exact_failed": not bool(r.get("offline_exact")),
            "tag_failed": not bool(r.get("tag_verified")),
            "l1_failed": not bool(r.get("l1_ok")),
            "l2_failed": not bool(r.get("l2_ok")),
            "l1_syndrome_ok": bool(r.get("l1_syndrome_ok")),
            "l2_syndrome_ok": bool(r.get("l2_syndrome_ok")),
        } for r in own if not bool(r.get("offline_exact")) or not bool(r.get("tag_verified"))]
        waterfall = [{
            "block_index": int(r.get("block_index", -1)),
            "cumulative_exact": sum(int(bool(x.get("offline_exact"))) for x in own[:i + 1]),
            "cumulative_tag": sum(int(bool(x.get("tag_verified"))) for x in own[:i + 1]),
        } for i, r in enumerate(own)]
        passed = bool(block_count == len(own) and exact >= threshold and tag >= threshold and false_accept == 0)
        per_source[label] = {
            "block_count": block_count, "exact_count": exact, "tag_verified_count": tag,
            "false_accept_count": false_accept, "threshold": threshold,
            "syndrome_convergence": (l2_ok / block_count) if block_count else 0.0,
            "l1_ok_count": l1_ok, "l2_ok_count": l2_ok,
            "exact_fer": 1.0 - (exact / block_count) if block_count else 1.0,
            "tag_fer": 1.0 - (tag / block_count) if block_count else 1.0,
            "failure_positions": failures, "waterfall": waterfall, "passed": passed,
        }
        total_blocks += block_count
        total_exact += exact
        total_tag += tag
        total_false += false_accept
    packet_pass = bool(per_source and all(per_source[label]["passed"] for label in SOURCE_ORDER))
    return {
        "packet_id": packet_id, "family": family, "n": n,
        "per_source": per_source,
        "overall": {
            "block_count": total_blocks, "exact_count": total_exact,
            "tag_verified_count": total_tag, "false_accept_count": total_false,
            "exact_fer": (1.0 - total_exact / total_blocks) if total_blocks else 1.0,
            "tag_fer": (1.0 - total_tag / total_blocks) if total_blocks else 1.0,
        },
        "passed": packet_pass,
    }


def run_m3_gate(
    construction: Mapping[int, Mapping[str, Any]], blocks_by_n: Mapping[int, Sequence[Mapping[str, Any]]], *,
    decoder_runner: Any = None, adapters: Mapping[str, Any] | None = None,
    resource_limit_seconds: float = RESOURCE_LIMIT_SECONDS,
    wallclock_budget_seconds: float | None = None,
) -> dict[str, Any]:
    """Run the full Bob-only validation windows for both n."""
    construction = dict(construction)
    blocks_by_n = {int(n): list(blocks) for n, blocks in blocks_by_n.items()}
    adapters = dict(adapters or {})
    if decoder_runner is None and not adapters:
        adapters = v30.load_v26_adapters_once()
    records: list[dict[str, Any]] = []
    meter = 0.0
    terminal: str | None = None
    summaries: dict[str, Any] = {}
    per_n_pass: dict[str, bool] = {}
    for n in N_VALUES:
        entry = construction.get(n, {"packets": []})
        blocks = blocks_by_n.get(n, [])
        n_summaries: list[dict[str, Any]] = []
        passed_any = False
        for packet in entry.get("packets", []):
            stats, meter, status = _run_packet_full_window(
                packet, blocks, max_iter=M3_MAX_ITER, streak=M3_STREAK,
                decoder_runner=decoder_runner, adapters=adapters,
                resource_meter=meter, resource_limit_seconds=resource_limit_seconds,
                records=records, wallclock_budget_seconds=wallclock_budget_seconds,
            )
            summary = _packet_summary(packet, records)
            summary["window_status"] = status
            n_summaries.append(summary)
            if status is not None:
                terminal = status
                break
            if summary["passed"]:
                passed_any = True
        per_n_pass[str(n)] = bool(passed_any)
        summaries[str(n)] = {"n": n, "summaries": n_summaries, "passed_any": passed_any}
        if terminal is not None:
            break
    if terminal is None:
        if all(per_n_pass.get(str(n), False) for n in N_VALUES):
            terminal = TERMINAL_PASS
        else:
            terminal = TERMINAL_FAIL
    return {
        "schema": "nbldpc_v31_finite_gate_v1", "status": terminal,
        "records": records, "record_count": len(records),
        "summaries": summaries, "per_n_pass": per_n_pass,
        "resource_meter_seconds": meter, "resource_limit_seconds": float(resource_limit_seconds),
    }


# ---------------------------------------------------------------------------
# Orchestration and evidence
# ---------------------------------------------------------------------------

def _json_safe(value: Any) -> Any:
    return v30.json_safe(value)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(_json_safe(value), indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _matrix_audit_records(construction: Mapping[int, Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for n in N_VALUES:
        for packet in construction.get(n, {}).get("packets", []):
            records.append({
                "packet_id": packet.get("packet_id", packet.get("matrix_id")),
                "matrix_id": packet.get("matrix_id"), "allocation_id": packet.get("allocation_id"),
                "family": packet.get("family"), "n": packet.get("n"), "m1": packet.get("m1"),
                "m2_by_source": packet.get("m2_by_source"), "construction_ok": packet.get("construction_ok"),
                "capacity_ok": packet.get("capacity_ok"), "max_support_occupancy": packet.get("max_support_occupancy"),
                "projective_hard_gate": packet.get("projective_hard_gate"),
                "full_row_rank": packet.get("full_row_rank"), "field": packet.get("field"),
                "four_cycle_components": packet.get("four_cycle_components"),
                "four_cycle_count": packet.get("four_cycle_count"), "audits": packet.get("audits"),
            })
    return records


def _matrix_payload_records(construction: Mapping[int, Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for n in N_VALUES:
        for packet in construction.get(n, {}).get("packets", []):
            records.append({
                "packet_id": packet.get("packet_id", packet.get("matrix_id")),
                "matrix_id": packet.get("matrix_id"), "allocation_id": packet.get("allocation_id"),
                "family": packet.get("family"), "n": packet.get("n"), "m1": packet.get("m1"),
                "m2_by_source": packet.get("m2_by_source"), "q": Q, "n_cols": n,
                "matrices": _json_safe(packet.get("matrices", {})),
            })
    return records


def _manifest_for_run(
    configs: Mapping[int, Mapping[str, Any]], allocations: Mapping[int, Mapping[str, Any]],
    m1: Mapping[str, Any], construction: Mapping[int, Mapping[str, Any]], m3: Mapping[str, Any],
    status: str,
) -> dict[str, Any]:
    return {
        "schema": "nbldpc_v31_run_manifest_v1", "run_role": "v31_deterministic_finite_graph_redesign_gate",
        "configs": _json_safe({str(n): configs[n] for n in N_VALUES}),
        "allocations": _json_safe({str(n): allocations[n] for n in N_VALUES}),
        "source_order": list(SOURCE_ORDER),
        "source_mappings": {label: {"source_id": SOURCE_IDS[label], "delay_used_ps": SOURCE_DELAY_PS[label]}
                            for label in SOURCE_ORDER},
        "v30_rerun": False, "v25_holdout_used": False, "v29_holdout_used": False,
        "raw_ttbin_used": False,
        "scientific_input_paths": {
            "v25_channel_counts": str(_resolved_repo_path(V25_CHANNEL_COUNTS)),
            "validation_pairs_parquet": {label: str(_resolved_repo_path(path)) for label, path in SOURCE_PARQUETS.items()},
            "v30r_canonical": str(_resolved_repo_path(V30R_CANONICAL)),
        },
        "scientific_input_bindings": {
            "v25_channel_counts": V25_CHANNEL_COUNTS,
            "validation_pairs_parquet": dict(SOURCE_PARQUETS),
            "v30r_canonical": V30R_CANONICAL,
        },
        "m1": m1, "construction": {
            str(n): {
                "n": n, "packet_ids": [p.get("packet_id") for p in construction.get(n, {}).get("packets", [])],
                "rejected": construction.get(n, {}).get("rejected", []),
            } for n in N_VALUES
        },
        "m3_status": m3.get("status"), "terminal_state": status,
        "de_rerun": False, "decoder_rerun": False, "scientific_inputs_read": [],
        "evidence_files": [
            "RUN_MANIFEST.json", "de_confirmation.json", "m1_registry.json",
            "matrix_audits.json", "matrix_payloads.json",
            "validation_frames_n1024.json", "validation_blocks_n1024.json",
            "validation_frames_n2048.json", "validation_blocks_n2048.json",
            "per_block_n1024.jsonl", "per_block_n2048.jsonl",
            "summary_n1024.json", "summary_n2048.json", "gate.json", "readonly_verify.json",
        ],
    }


class _ChunkTimeout(Exception):
    """Raised internally when a wall-clock chunk budget is exhausted."""
    def __init__(self, stage: str):
        super().__init__(f"V31 chunk timeout at stage {stage}")
        self.stage = stage


def _packet_key(packet: Mapping[str, Any]) -> tuple[int, str]:
    return (int(packet.get("n", -1)), str(packet.get("family")))


def _load_construction(root: Path) -> dict[int, dict[str, Any]]:
    construction = {n: {"n": n, "packets": [], "rejected": []} for n in N_VALUES}
    audits_file = root / "matrix_audits.json"
    payloads_file = root / "matrix_payloads.json"
    if not payloads_file.exists():
        return construction
    payloads = _read_json(payloads_file).get("packets", [])
    audits = _read_json(audits_file).get("packets", []) if audits_file.exists() else []
    for p in payloads:
        n = int(p["n"])
        audit = next((a for a in audits if str(a.get("packet_id")) == str(p.get("packet_id"))), {})
        packet = {**p, "audits": audit.get("audits", {})}
        if "packet_id" not in packet:
            packet["packet_id"] = packet.get("matrix_id")
        construction[n]["packets"].append(packet)
    return construction


def _persist_construction(root: Path, construction: Mapping[int, Mapping[str, Any]]) -> None:
    _write_json(root / "matrix_audits.json", {"schema": "nbldpc_v31_matrix_audits_v1",
                                              "packets": _matrix_audit_records(construction),
                                              "rejected": [r for n in N_VALUES for r in construction.get(n, {}).get("rejected", [])]})
    _write_json(root / "matrix_payloads.json", {"schema": "nbldpc_v31_matrix_payloads_v1",
                                                "packets": _matrix_payload_records(construction)})


def run_m2_incremental(
    root: Path, allocations: Mapping[int, Mapping[str, Any]], *,
    start_time: float | None = None, wallclock_budget_seconds: float | None = None,
) -> dict[int, dict[str, Any]]:
    """Build and persist all family packets, resuming from already-built ones."""
    start_time = time.monotonic() if start_time is None else start_time
    construction = _load_construction(root)
    existing = {_packet_key(p): True for n in construction.values() for p in n["packets"]}
    for n in N_VALUES:
        allocation = allocations[n]
        for family in SUPPORTED_FAMILIES:
            if (int(n), family) in existing:
                continue
            if wallclock_budget_seconds is not None and time.monotonic() - start_time > float(wallclock_budget_seconds):
                raise _ChunkTimeout(f"m2_n{n}_{family}")
            try:
                packet = build_matrix_packet(
                    int(allocation["m1"]), allocation["m2_by_source"],
                    n=n, family=family, allocation_id=allocation["allocation_id"],
                )
                packet["packet_id"] = packet["matrix_id"]
                if not packet["construction_ok"]:
                    raise ValueError("V31 construction hard gate failed")
                construction[n]["packets"].append(packet)
            except Exception as exc:
                construction[n]["rejected"].append({
                    "n": int(n), "family": family,
                    "allocation_id": allocation["allocation_id"],
                    "terminal": TERMINAL_FAIL,
                    "error": f"{type(exc).__name__}: {exc}",
                })
            _persist_construction(root, construction)
    return construction


def _load_block_records(root: Path) -> dict[int, list[dict[str, Any]]]:
    result: dict[int, list[dict[str, Any]]] = {}
    for n in N_VALUES:
        path = root / f"per_block_n{n}.jsonl"
        records: list[dict[str, Any]] = []
        if path.exists():
            with path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    if line.strip():
                        records.append(json.loads(line))
        result[n] = records
    return result


def _append_block_record(root: Path, n: int, record: Mapping[str, Any]) -> None:
    with (root / f"per_block_n{n}.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(_json_safe(record), sort_keys=True, allow_nan=False) + "\n")


def run_m3_incremental(
    root: Path, construction: Mapping[int, Mapping[str, Any]],
    blocks_by_n: Mapping[int, Sequence[Mapping[str, Any]]], *,
    decoder_runner: Any = None, adapters: Mapping[str, Any] | None = None,
    resource_limit_seconds: float = RESOURCE_LIMIT_SECONDS,
    start_time: float | None = None, wallclock_budget_seconds: float | None = None,
) -> dict[str, Any]:
    """Run Bob-only validation windows, persisting each block record immediately."""
    start_time = time.monotonic() if start_time is None else start_time
    adapters = dict(adapters or {})
    if decoder_runner is None and not adapters:
        adapters = v30.load_v26_adapters_once()
    records_by_n = _load_block_records(root)
    meter = 0.0
    terminal: str | None = None
    for n in N_VALUES:
        entry = construction.get(n, {"packets": []})
        blocks = list(blocks_by_n.get(n, []))
        done_keys = {(str(r.get("packet_id")), str(r.get("source")), int(r.get("block_index", -1)))
                     for r in records_by_n[n]}
        for packet in entry.get("packets", []):
            family = str(packet.get("family"))
            for label in SOURCE_ORDER:
                selected = sorted((b for b in blocks if b.get("source") == label),
                                  key=lambda b: int(b.get("block_index", -1)))
                for block in selected:
                    key = (str(packet.get("packet_id")), label, int(block.get("block_index", -1)))
                    if key in done_keys:
                        continue
                    if meter >= float(resource_limit_seconds):
                        terminal = TERMINAL_RESOURCE
                        break
                    if wallclock_budget_seconds is not None and time.monotonic() - start_time > float(wallclock_budget_seconds):
                        raise _ChunkTimeout(f"m3_n{n}_{family}_block_{int(block.get('block_index', -1))}")
                    try:
                        block_public, public, truth = v30._block_public_and_syndromes(block, packet)
                        started = time.monotonic()
                        result = v30._invoke_decoder(
                            decoder_runner, block_public, public, adapters.get(label), packet,
                            {"max_iter": M3_MAX_ITER, "streak": M3_STREAK},
                        )
                        elapsed = time.monotonic() - started
                        record = v30._finite_block_record(block, public, result, truth, packet, elapsed)
                        runtime = float(record["runtime_s"])
                        if not math.isfinite(runtime) or runtime < 0:
                            raise ValueError("decoder runtime_s must be finite and nonnegative")
                        meter += runtime
                    except Exception as exc:
                        record = {
                            "schema": "nbldpc_v31_block_result_v1",
                            "packet_id": packet.get("packet_id"), "source": label,
                            "block_index": int(block.get("block_index", -1)),
                            "frame_ids": list(block.get("frame_ids", [])), "l1_ok": False,
                            "l1_status": TERMINAL_IMPL, "l2_ok": False, "l2_status": "not_run",
                            "l2_conditioning": "not_run", "l2_not_run_due_l1": True,
                            "l1_syndrome_ok": False, "l2_syndrome_ok": False,
                            "offline_exact": False, "tag_verified": False, "false_accept": False,
                            "l1_symbol_errors": None, "l2_symbol_errors": None,
                            "l1_iterations": 0, "l2_iterations": 0, "decoder_calls": 0,
                            "runtime_s": time.monotonic() - started,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                        meter += float(record["runtime_s"])
                        terminal = TERMINAL_IMPL
                    record["n"] = n
                    record["family"] = family
                    records_by_n[n].append(record)
                    _append_block_record(root, n, record)
                    done_keys.add(key)
                    if terminal is not None:
                        break
                if terminal is not None:
                    break
            if terminal is not None:
                break
        if terminal is not None:
            break

    all_records = [r for n in N_VALUES for r in records_by_n[n]]
    summaries: dict[str, Any] = {}
    per_n_pass: dict[str, bool] = {}
    for n in N_VALUES:
        n_summaries: list[dict[str, Any]] = []
        passed_any = False
        for packet in construction.get(n, {}).get("packets", []):
            summary = _packet_summary(packet, all_records)
            n_summaries.append(summary)
            if summary.get("passed"):
                passed_any = True
        per_n_pass[str(n)] = bool(passed_any)
        summaries[str(n)] = {"n": n, "summaries": n_summaries, "passed_any": passed_any}
        _write_json(root / f"summary_n{n}.json", summaries[str(n)])
    if terminal is None:
        if all(per_n_pass.get(str(n), False) for n in N_VALUES):
            terminal = TERMINAL_PASS
        else:
            terminal = TERMINAL_FAIL
    return {
        "schema": "nbldpc_v31_finite_gate_v1", "status": terminal,
        "records": all_records, "record_count": len(all_records),
        "summaries": summaries, "per_n_pass": per_n_pass,
        "resource_meter_seconds": meter, "resource_limit_seconds": float(resource_limit_seconds),
    }


def run_v31_gate(
    output_root: str | Path, *, de_runner: Any = None, decoder_runner: Any = None,
    adapters: Mapping[str, Any] | None = None, blocks_by_n: Mapping[int, Sequence[Mapping[str, Any]]] | None = None,
    resource_limit_seconds: float = RESOURCE_LIMIT_SECONDS,
    wallclock_budget_seconds: float | None = None,
) -> dict[str, Any]:
    """Execute the frozen V31 gate with resumable wall-clock chunking.

    Injected runners/blocks are test-only seams. When a wall-clock budget is
    provided and exhausted, the run persists progress and returns
    status "paused"; re-invoking the same command resumes from that point.
    """
    root = Path(output_root)
    progress_path = root / "progress.json"
    start_time = time.monotonic()
    if root.exists() and progress_path.exists():
        progress = _read_json(progress_path)
        stage = progress.get("stage")
        resume = True
    else:
        stage = None
        resume = False
        if root.exists():
            raise FileExistsError(f"V31 output root must be new: {root}")
        root.mkdir(parents=True, exist_ok=False)

    configs = {n: frozen_v31_config(n) for n in N_VALUES}
    h_values = v30.load_bound_h_values()
    allocations = {n: build_allocation_plan(n, h_values=h_values) for n in N_VALUES}

    if adapters is None and (de_runner is None or decoder_runner is None):
        adapters = v30.load_v26_adapters_once()

    try:
        construction = _load_construction(root) if resume else {n: {"n": n, "packets": [], "rejected": []} for n in N_VALUES}

        if stage is None or stage == "start":
            _write_json(root / "progress.json", {"stage": "start"})
            m0 = v30.run_m0_baseline()
            m1 = run_m1_confirmation(allocations, de_runner=de_runner, adapters=adapters,
                                     resource_limit_seconds=resource_limit_seconds)
            registry = {
                "schema": "nbldpc_v31_m1_registry_v1",
                "params": configs[N_VALUES[0]]["m1_confirmation"],
                "registered_calls": _json_safe([dict(item) for n in N_VALUES for item in _confirmation_items(allocations[n])]),
                "per_n": m1.get("per_n", {}), "confirmed_n": m1.get("confirmed_n", []),
            }
            _write_json(root / "de_confirmation.json", m1)
            _write_json(root / "m1_registry.json", registry)
            _write_json(root / "progress.json", {"stage": "m1_done", "m1_terminal": m1.get("terminal"),
                                                "confirmed_n": m1.get("confirmed_n", []),
                                                "m1_meter_seconds": m1.get("resource_meter_seconds", 0.0)})
            if m1.get("terminal") != "de_allocation_pass":
                status = m1.get("terminal") or TERMINAL_DE_FAIL
                m3 = {"schema": "nbldpc_v31_finite_gate_v1", "status": status, "records": [],
                      "record_count": 0, "summaries": {}, "per_n_pass": {},
                      "resource_meter_seconds": 0.0, "resource_limit_seconds": float(resource_limit_seconds)}
                construction = {n: {"n": n, "packets": [], "rejected": []} for n in N_VALUES}
                _persist_construction(root, construction)
                for n in N_VALUES:
                    _write_json(root / f"validation_frames_n{n}.json", validation_frame_manifest())
                    _write_json(root / f"validation_blocks_n{n}.json", {"n": n, "blocks": []})
                    (root / f"per_block_n{n}.jsonl").write_text("", encoding="utf-8")
                    _write_json(root / f"summary_n{n}.json", {})
                _finish_v31_run(root, configs, allocations, m1, construction, m3, status)
                return {"status": status, "evidence_root": str(root)}
            status = None
        elif stage == "m1_done":
            m1 = _read_json(root / "de_confirmation.json")
            registry = _read_json(root / "m1_registry.json")
            status = None
        else:
            # resume from m2/m3 stages: load persisted artifacts
            m1 = _read_json(root / "de_confirmation.json")
            registry = _read_json(root / "m1_registry.json")
            status = None

        # M2 incremental
        construction = run_m2_incremental(root, allocations, start_time=start_time,
                                          wallclock_budget_seconds=wallclock_budget_seconds)
        _persist_construction(root, construction)
        _write_json(root / "progress.json", {"stage": "m2_done",
                                            "packet_count": sum(len(construction[n]["packets"]) for n in N_VALUES),
                                            "rejected_count": sum(len(construction[n]["rejected"]) for n in N_VALUES)})
        if blocks_by_n is None:
            blocks_by_n = {n: load_validation_blocks(n) if construction[n]["packets"] else [] for n in N_VALUES}
        else:
            for n in N_VALUES:
                if construction[n]["packets"]:
                    _validate_validation_blocks(blocks_by_n[n], n)
        for n in N_VALUES:
            _write_json(root / f"validation_frames_n{n}.json", validation_frame_manifest())
            _write_json(root / f"validation_blocks_n{n}.json", {"schema": f"nbldpc_v31_validation_blocks_v{n}",
                                                                "n": n, "blocks": _json_safe(blocks_by_n[n])})
        if not any(construction[n]["packets"] for n in N_VALUES):
            m3 = {"schema": "nbldpc_v31_finite_gate_v1", "status": TERMINAL_FAIL, "records": [],
                  "record_count": 0, "summaries": {}, "per_n_pass": {},
                  "resource_meter_seconds": 0.0, "resource_limit_seconds": float(resource_limit_seconds)}
            status = TERMINAL_FAIL
        else:
            m3 = run_m3_incremental(root, construction, blocks_by_n, decoder_runner=decoder_runner,
                                    adapters=adapters, resource_limit_seconds=resource_limit_seconds,
                                    start_time=start_time, wallclock_budget_seconds=wallclock_budget_seconds)
            _write_json(root / "progress.json", {"stage": "m3_done", "status": m3.get("status"),
                                                 "record_count": m3.get("record_count", 0),
                                                 "per_n_pass": m3.get("per_n_pass", {})})
            status = m3.get("status", TERMINAL_IMPL)
        return _finish_v31_run(root, configs, allocations, m1, construction, m3, status)
    except _ChunkTimeout as exc:
        _write_json(root / "progress.json", {"stage": exc.stage, "paused": True,
                                            "wallclock_elapsed_seconds": time.monotonic() - start_time})
        return {"status": "paused", "evidence_root": str(root), "chunk_stage": exc.stage}


def _finish_v31_run(root: Path, configs: Mapping[int, Mapping[str, Any]],
                    allocations: Mapping[int, Mapping[str, Any]], m1: Mapping[str, Any],
                    construction: Mapping[int, Mapping[str, Any]], m3: Mapping[str, Any],
                    status: str) -> dict[str, Any]:
    for n in N_VALUES:
        # block records already persisted incrementally; ensure summary files exist
        _write_json(root / f"summary_n{n}.json", m3.get("summaries", {}).get(str(n), {}))
    manifest = _manifest_for_run(configs, allocations, m1, construction, m3, status)
    _write_json(root / "RUN_MANIFEST.json", manifest)
    gate = {
        "schema": "nbldpc_v31_gate_v1", "status": status,
        "m1_de_resource_meter_seconds": m1.get("resource_meter_seconds", 0.0) if isinstance(m1, dict) else 0.0,
        "m3_decoder_resource_meter_seconds": m3.get("resource_meter_seconds", 0.0) if isinstance(m3, dict) else 0.0,
        "resource_limit_seconds": float(RESOURCE_LIMIT_SECONDS),
        "m1_terminal": m1.get("terminal") if isinstance(m1, dict) else None,
        "m3_terminal": m3.get("status") if isinstance(m3, dict) else None,
        "per_n_pass": m3.get("per_n_pass", {}) if isinstance(m3, dict) else {},
        "de_rerun": False, "decoder_rerun": False, "v30_rerun": False,
    }
    _write_json(root / "gate.json", gate)
    verification = verify_v31(root)
    _write_json(root / "readonly_verify.json", verification)
    return {"status": status, "evidence_root": str(root), "gate": gate, "readonly_verify": verification}



def _expected_allocations() -> dict[int, dict[str, Any]]:
    h_values = v30.load_bound_h_values()
    return {n: build_allocation_plan(n, h_values=h_values) for n in N_VALUES}


def _recompute_m1_from_registry(registry: Mapping[str, Any], allocations: Mapping[int, Mapping[str, Any]]) -> dict[str, Any]:
    expected_calls = [dict(item) for n in N_VALUES for item in _confirmation_items(allocations[n])]
    per_n: dict[str, Any] = {}
    for n in N_VALUES:
        own = [item for item in expected_calls if item["n"] == n]
        per_n[str(n)] = {"n": int(n), "expected_calls": len(own), "n_calls": len(own)}
    confirmed = [int(n) for n in N_VALUES]
    return {"expected_calls": expected_calls, "expected_total": 60, "per_n": per_n, "confirmed_n": confirmed}


def verify_v31(run_root: str | Path) -> dict[str, Any]:
    """Read-only structural verifier; never invokes DE or a decoder."""
    root = Path(run_root)
    required = [
        "RUN_MANIFEST.json", "de_confirmation.json", "m1_registry.json",
        "matrix_audits.json", "matrix_payloads.json",
        "validation_frames_n1024.json", "validation_blocks_n1024.json",
        "validation_frames_n2048.json", "validation_blocks_n2048.json",
        "per_block_n1024.jsonl", "per_block_n2048.jsonl",
        "summary_n1024.json", "summary_n2048.json", "gate.json",
    ]
    problems: list[str] = []
    missing = [name for name in required if not (root / name).exists()]
    problems.extend(f"missing:{name}" for name in missing)
    if missing:
        return {"schema": "nbldpc_v31_readonly_verify_v1", "ok": False,
                "problems": problems, "no_de_rerun": True, "no_decoder_rerun": True,
                "verifier_rerun_flags": {"de": False, "decoder": False}}
    try:
        manifest = _read_json(root / "RUN_MANIFEST.json")
        m1 = _read_json(root / "de_confirmation.json")
        registry = _read_json(root / "m1_registry.json")
        matrix_audits = _read_json(root / "matrix_audits.json")
        payloads = _read_json(root / "matrix_payloads.json")
        gate = _read_json(root / "gate.json")
    except (OSError, ValueError, TypeError) as exc:
        return {"schema": "nbldpc_v31_readonly_verify_v1", "ok": False,
                "problems": [f"read:{type(exc).__name__}:{exc}"], "no_de_rerun": True,
                "no_decoder_rerun": True, "verifier_rerun_flags": {"de": False, "decoder": False}}

    if manifest.get("schema") != "nbldpc_v31_run_manifest_v1":
        problems.append("manifest_schema")
    if manifest.get("v30_rerun") is not False or manifest.get("v29_holdout_used") is not False \
            or manifest.get("v25_holdout_used") is not False or manifest.get("raw_ttbin_used") is not False:
        problems.append("forbidden_input_or_rerun")

    # Allocation/config rebuild (no DE, no decoder, no matrix rebuild)
    try:
        expected_alloc = _expected_allocations()
        expected_registry = _recompute_m1_from_registry(registry, expected_alloc)
        expected_config = {n: frozen_v31_config(n) for n in N_VALUES}
    except (OSError, ValueError, TypeError, KeyError) as exc:
        problems.append(f"rebuild_error:{type(exc).__name__}:{exc}")
        expected_alloc = {}
        expected_registry = {}
        expected_config = {}

    configs = manifest.get("configs", {}) if isinstance(manifest.get("configs"), dict) else {}
    for n in N_VALUES:
        if configs.get(str(n)) != _json_safe(expected_config.get(n)):
            problems.append(f"config_rebuild_n{n}")
    allocs = manifest.get("allocations", {}) if isinstance(manifest.get("allocations"), dict) else {}
    for n in N_VALUES:
        if allocs.get(str(n)) != _json_safe(expected_alloc.get(n)):
            problems.append(f"allocation_rebuild_n{n}")

    # M1 verification from persisted calls only
    calls = list(m1.get("calls", []))
    expected_calls = expected_registry.get("expected_calls", []) if expected_registry else []
    if len(calls) != len(expected_calls):
        problems.append("m1_call_count")
    n2calls: dict[int, list[dict]] = {n: [] for n in N_VALUES}
    for index, row in enumerate(calls):
        if index >= len(expected_calls):
            problems.append("m1_unregistered_call")
            break
        exp = expected_calls[index]
        keys = ("allocation_id", "m1", "m2", "source", "source_id", "delay_used_ps",
                "layer", "seed", "rate", "f", "H_bits_per_symbol", "n_samples", "max_iter")
        if row.get("call_index") != index or any(row.get(k) != exp.get(k) for k in keys):
            problems.append(f"m1_registry_call:{index}")
        n_int = int(exp.get("n", -1))
        if n_int in n2calls:
            n2calls[n_int].append(row)
    for n in N_VALUES:
        own = n2calls[n]
        if len(own) != 30:
            problems.append(f"m1_n{n}_call_count")
            continue
        passed = all(_is_de_pass(row) for row in own)
        persisted = m1.get("per_n", {}).get(str(n), {})
        if not passed or not persisted.get("all_calls_pass"):
            problems.append(f"m1_n{n}_pass_mismatch")
    if m1.get("confirmed_n") != [int(n) for n in N_VALUES]:
        problems.append("m1_confirmed_n")

    # Matrix payload structural checks (recompute audits from persisted matrices)
    payload_map = {(str(p.get("packet_id")), int(p.get("n", -1))): p for p in payloads.get("packets", [])}
    audit_map = {(str(a.get("packet_id")), int(a.get("n", -1))): a for a in matrix_audits.get("packets", [])}
    for key, packet in payload_map.items():
        packet_id, n = key
        matrices = packet.get("matrices", {})
        for layer in ("L1",):
            if layer not in matrices:
                problems.append(f"payload_missing_L1:{packet_id}")
                continue
        for label in SOURCE_ORDER:
            if "L2" not in matrices or label not in matrices.get("L2", {}):
                problems.append(f"payload_missing_L2:{packet_id}:{label}")
    # Recompute audit aggregates from payload matrices (cheap structural checks)
    for packet_id, n in list(audit_map.keys()):
        payload = payload_map.get((packet_id, n))
        if payload is None:
            problems.append(f"audit_without_payload:{packet_id}")
            continue
        matrices = payload.get("matrices", {})
        occ_all: list[int] = []
        for layer_name, matrix in (("L1", matrices.get("L1")),):
            if matrix is None:
                continue
            arr = v30._matrix_array(matrix)
            nz_by_col = [tuple(sorted(np.flatnonzero(arr[:, j] != 0).tolist())) for j in range(arr.shape[1])]
            occ = Counter(nz_by_col)
            if any(v > MAX_SUPPORT_OCCUPANCY for v in occ.values()):
                problems.append(f"payload_occupancy_L1:{packet_id}")
            occ_all.extend(occ.values())
            audit = v30.projective_column_audit(matrix, FIELD)
            persisted_audit = audit_map.get((packet_id, n), {}).get("audits", {}).get("L1", {})
            if persisted_audit.get("projective", {}).get("duplicate_projective_classes") != audit["duplicate_projective_classes"]:
                problems.append(f"payload_audit_L1_duplicates:{packet_id}")
            if persisted_audit.get("projective", {}).get("proportional_pairs") != audit["proportional_pairs"]:
                problems.append(f"payload_audit_L1_proportional:{packet_id}")
            if not audit["full_row_rank"]:
                problems.append(f"payload_rank_L1:{packet_id}")
        for label in SOURCE_ORDER:
            matrix = matrices.get("L2", {}).get(label)
            if matrix is None:
                continue
            arr = v30._matrix_array(matrix)
            nz_by_col = [tuple(sorted(np.flatnonzero(arr[:, j] != 0).tolist())) for j in range(arr.shape[1])]
            occ = Counter(nz_by_col)
            if any(v > MAX_SUPPORT_OCCUPANCY for v in occ.values()):
                problems.append(f"payload_occupancy_L2:{packet_id}:{label}")
            occ_all.extend(occ.values())
            audit = v30.projective_column_audit(matrix, FIELD)
            persisted_audit = audit_map.get((packet_id, n), {}).get("audits", {}).get("L2", {}).get(label, {})
            if persisted_audit.get("projective", {}).get("duplicate_projective_classes") != audit["duplicate_projective_classes"]:
                problems.append(f"payload_audit_L2_duplicates:{packet_id}:{label}")
            if persisted_audit.get("projective", {}).get("proportional_pairs") != audit["proportional_pairs"]:
                problems.append(f"payload_audit_L2_proportional:{packet_id}:{label}")
            if not audit["full_row_rank"]:
                problems.append(f"payload_rank_L2:{packet_id}:{label}")
        max_occ = max(occ_all, default=0)
        persisted_max = audit_map.get((packet_id, n), {}).get("max_support_occupancy")
        if persisted_max is not None and persisted_max != max_occ:
            problems.append(f"payload_max_occupancy:{packet_id}")

    # Validation frame/block identity
    for n in N_VALUES:
        frame_doc = _read_json(root / f"validation_frames_n{n}.json")
        blocks_doc = _read_json(root / f"validation_blocks_n{n}.json")
        try:
            blocks = blocks_doc.get("blocks", [])
            _validate_validation_blocks(blocks, n)
        except (ValueError, KeyError, TypeError) as exc:
            problems.append(f"validation_blocks_n{n}:{type(exc).__name__}:{exc}")

    # Block record registration and summary recomputation
    for n in N_VALUES:
        records: list[dict[str, Any]] = []
        with (root / f"per_block_n{n}.jsonl").open("r", encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    records.append(json.loads(line))
        seen: set[tuple[str, str, int]] = set()
        grouped: dict[tuple[str, str], list[int]] = defaultdict(list)
        for r in records:
            pid = str(r.get("packet_id"))
            source = str(r.get("source"))
            bi = int(r.get("block_index", -1))
            key = (pid, source, bi)
            if key in seen:
                problems.append(f"block_duplicate:{n}:{pid}:{source}:{bi}")
            seen.add(key)
            grouped[(pid, source)].append(bi)
        blocks_per_source = 400 // (n // FRAME_PAIRS)
        # Pre-registered bounded closeout contingency (design §5): if the n=1024
        # window already fixes global finite_graph_fail, the n=2048 window may be
        # closed on a contiguous block prefix (at least one recorded block).
        gate_status = gate.get("status") if isinstance(gate, dict) else None
        bounded = bool(n == 2048 and gate_status == TERMINAL_FAIL and bool(records))
        for (pid, source), indices in grouped.items():
            if bounded:
                if sorted(indices) != list(range(0, len(indices))):
                    problems.append(f"block_registration_prefix:{n}:{pid}:{source}")
            else:
                if sorted(indices) != list(range(blocks_per_source)):
                    problems.append(f"block_registration:{n}:{pid}:{source}")
        # Recompute summaries from records and compare to persisted
        summary_doc = _read_json(root / f"summary_n{n}.json")
        if not isinstance(summary_doc, dict):
            problems.append(f"summary_n{n}_type")
            summaries = []
        else:
            summaries = summary_doc.get("summaries", [])
        payload_ids = {str(p["packet_id"]) for p in payload_map.values() if int(p.get("n", -1)) == n}
        for pid in sorted(payload_ids):
            rows = [r for r in records if str(r.get("packet_id")) == pid]
            if not rows:
                if not bounded:
                    problems.append(f"missing_blocks:{n}:{pid}")
                continue
            exact = sum(int(bool(r.get("offline_exact"))) for r in rows)
            tag = sum(int(bool(r.get("tag_verified"))) for r in rows)
            false_acc = sum(int(bool(r.get("false_accept"))) for r in rows)
            threshold = math.ceil(THRESHOLD_RATIO * blocks_per_source)
            passed = exact >= threshold and tag >= threshold and false_acc == 0
            matching = [s for s in summaries if str(s.get("packet_id")) == pid]
            if len(matching) != 1:
                problems.append(f"summary_missing_packet:{n}:{pid}")
                continue
            persisted_summary = matching[0]
            per = persisted_summary.get("per_source", {}) if isinstance(persisted_summary, dict) else {}
            for label in SOURCE_ORDER:
                info = per.get(label) if isinstance(per, dict) else None
                if not isinstance(info, dict):
                    problems.append(f"summary_source_missing:{n}:{pid}:{label}")
                    continue
                if int(info.get("exact_count", -1)) != sum(int(bool(r.get("offline_exact")))
                                                            for r in rows if r.get("source") == label):
                    problems.append(f"summary_exact_mismatch:{n}:{pid}:{label}")
                if int(info.get("tag_verified_count", -1)) != sum(int(bool(r.get("tag_verified")))
                                                                   for r in rows if r.get("source") == label):
                    problems.append(f"summary_tag_mismatch:{n}:{pid}:{label}")
                if int(info.get("false_accept_count", -1)) != sum(int(bool(r.get("false_accept")))
                                                                   for r in rows if r.get("source") == label):
                    problems.append(f"summary_false_accept_mismatch:{n}:{pid}:{label}")
            if bool(persisted_summary.get("passed")) != bool(passed):
                problems.append(f"summary_pass_mismatch:{n}:{pid}")

    # Terminal recomputation
    recomputed_status = gate.get("status") or TERMINAL_IMPL
    per_n_pass = {str(n): False for n in N_VALUES}
    for n in N_VALUES:
        summary_doc = _read_json(root / f"summary_n{n}.json")
        summaries = summary_doc.get("summaries", []) if isinstance(summary_doc, dict) else []
        passed_any = any(s.get("passed") for s in summaries)
        per_n_pass[str(n)] = bool(passed_any)
    if gate.get("status") in (TERMINAL_RESOURCE, TERMINAL_IMPL, TERMINAL_DE_FAIL):
        recomputed_status = gate.get("status")
    elif gate.get("m3_terminal") == TERMINAL_FAIL or not all(per_n_pass.values()):
        recomputed_status = TERMINAL_FAIL
    elif all(per_n_pass.values()):
        recomputed_status = TERMINAL_PASS
    if gate.get("status") != recomputed_status:
        problems.append("terminal_recompute")
    ok = not problems
    return {
        "schema": "nbldpc_v31_readonly_verify_v1", "ok": ok, "problems": problems,
        "recomputed_terminal": recomputed_status, "persisted_terminal": gate.get("status"),
        "no_de_rerun": True, "no_decoder_rerun": True,
        "verifier_rerun_flags": {"de": False, "decoder": False},
    }
