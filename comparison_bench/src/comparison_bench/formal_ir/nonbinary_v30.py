"""V30R finite-graph construction primitives.

This module contains the deterministic, finite-graph part of the V30R
contract.  It deliberately does not run DE, a decoder, or load the V25
parquet inputs.  The later gate/orchestrator can consume the small, explicit
``matrix_audit`` and ``matrix_packet`` records returned here.

The implementation reuses the accepted field and rank implementations from
V25/V28.  A degree-two column is represented by a support ``(a, b)`` with
coefficients ``(1, ratio)``.  Consequently its projective key is exactly
``(a, b, ratio)`` and the zero duplicate-key condition is the V30R 4-cycle
full-rank hard gate.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from itertools import combinations
import json
import inspect
import math
from numbers import Integral
from pathlib import Path
import time
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from . import nonbinary_codebook as codebook
from . import nonbinary_v28 as v28
from .nonbinary_field import GF2mField, get_field_spec


Q = 32
N = 1024
FIELD = GF2mField.create(Q)
FIELD_ID = "c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf"
PRIMITIVE_POLYNOMIAL = 0b100101
FAMILY_BALANCED = "balanced-projective"
FAMILY_PEG = "PEG-projective-cycle-cancelled"
FAMILY_ORDER = {FAMILY_BALANCED: 0, FAMILY_PEG: 1}
SUPPORTED_FAMILIES = (FAMILY_BALANCED, FAMILY_PEG)
M1_CANDIDATES = (9, 12, 16, 24, 32, 40)
SOURCE_ORDER = ("1M", "1p5M", "2M")
SOURCE_IDS = {
    "1M": "type2_1M_20260121_184040",
    "1p5M": "type2_1p5M_20260121_183806",
    "2M": "type2_2M_20260121_183657",
}
SOURCE_PARQUETS = {
    "1M": "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1M_20260121_184040/pairs.parquet",
    "1p5M": "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1p5M_20260121_183806/pairs.parquet",
    "2M": "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_2M_20260121_183657/pairs.parquet",
}
SOURCE_DELAY_PS = {"1M": -50, "1p5M": 50, "2M": 50}
SOURCE_M_TOTAL = {"1M": 200, "1p5M": 206, "2M": 208}
SOURCE_M2_V28R = {"1M": 194, "1p5M": 200, "2M": 202}
SOURCE_H = {
    "1M": {"L1": 0.0242805468186788, "L2": 0.7767572780789986},
    "1p5M": {"L1": 0.02519949687785432, "L2": 0.8003665547438693},
    "2M": {"L1": 0.02566204879687012, "L2": 0.8069006731253252},
}
RATIO_ORDER = "zero_based_field_nonzero_cycle"

V25_INVENTORY = (
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
    "nbldpc_v25_20260818/run_04/data_inventory.json"
)
V25_SPLIT_MANIFEST = (
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
    "nbldpc_v25_20260818/run_04/split_manifest.json"
)
V25_CHANNEL_COUNTS = (
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
    "nbldpc_v25_20260818/run_04/channel_counts.npz"
)
V26_CANONICAL = (
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
    "nbldpc_v26_20260818/run_02"
)
V28R_CANONICAL = (
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
    "nbldpc_v28_gf32_finite_code/run_02_v28r"
)
SOURCE_FRAME_RANGES = {"1M": (1200, 1599), "1p5M": (1660, 2059), "2M": (2187, 2586)}
FRAME_PAIRS = 256
BLOCK_FRAMES = 4
BLOCKS_PER_SOURCE = 100
TAG_BITS = 64
SCREEN_BLOCKS = tuple(range(0, 20))
CONFIRMATION_BLOCKS = tuple(range(20, 70))
SCREEN_SEEDS = (30001, 30002)
CONFIRMATION_SEEDS = (30101, 30102, 30103, 30104, 30105)
SCREEN_N_SAMPLES = 400
SCREEN_MAX_ITER = 100
CONFIRMATION_N_SAMPLES = 2000
CONFIRMATION_MAX_ITER = 200
ENTROPY_TOL_BITS = 0.01
RESOURCE_LIMIT_SECONDS = 24.0 * 60.0 * 60.0
TERMINAL_PASS = "pass_projective_finite_graph_ready_for_fresh"
TERMINAL_FINITE_FAIL = "finite_graph_fail"
TERMINAL_DE_FAIL = "de_allocation_fail"
TERMINAL_RESOURCE = "resource_blocked"
TERMINAL_IMPL = "implementation_blocked"

__all__ = [
    "Q", "N", "FIELD", "FIELD_ID", "PRIMITIVE_POLYNOMIAL", "M1_CANDIDATES",
    "SOURCE_ORDER", "SOURCE_IDS", "SOURCE_PARQUETS", "SOURCE_DELAY_PS", "SOURCE_M_TOTAL",
    "SOURCE_M2_V28R", "SOURCE_H", "FAMILY_BALANCED", "FAMILY_PEG",
    "SUPPORTED_FAMILIES", "frozen_v30r_config", "projective_key",
    "projective_column_audit", "run_m0_baseline", "build_supports_balanced",
    "build_supports_peg", "peg_support_score", "build_supports", "canonical_tanner6_tuple",
    "tanner6_alternating_product", "newly_closed_tanner6",
    "score_tanner6_candidate", "select_projective_ratio", "label_degree_two_column", "cycle_topology",
    "build_layer", "build_matrix_packet", "json_safe", "load_bound_h_values",
    "build_allocation_plan", "run_m1_screen", "run_m1_confirmation",
    "build_confirmed_packets", "validation_frame_manifest", "load_validation_blocks",
    "run_m3_gate", "run_v30r_gate", "verify_v30r",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _resolved_repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (_repo_root() / path).resolve()


def frozen_v30r_config(*, n: int = N) -> dict[str, Any]:
    """Return the immutable construction portion of the V30R configuration.

    ``n`` is parameterized only to make small in-memory unit tests possible;
    the production default is the frozen ``n=1024`` contract.  No production
    input path is opened by this function.
    """
    if isinstance(n, bool) or not isinstance(n, Integral) or int(n) < 1:
        raise ValueError("n must be a positive integer")
    field = get_field_spec(Q)
    if field.primitive_polynomial != PRIMITIVE_POLYNOMIAL or field.field_id != FIELD_ID:
        raise ValueError("pinned GF32 field metadata changed")
    return {
        "schema": "nbldpc_v30r_frozen_construction_v1",
        "q": Q, "n": int(n), "factorization": "F03_natural_MSB_to_LSB_GF32_plus_GF32",
        "lambda": {2: 1}, "m1_candidates": list(M1_CANDIDATES),
        "source_order": list(SOURCE_ORDER),
        "sources": {
            label: {
                "source_id": SOURCE_IDS[label], "pairs_parquet": SOURCE_PARQUETS[label],
                "delay_used_ps": SOURCE_DELAY_PS[label],
                "m_total": SOURCE_M_TOTAL[label], "m2_v28r": SOURCE_M2_V28R[label],
                "H": dict(SOURCE_H[label]),
            } for label in SOURCE_ORDER
        },
        "field": {
            "constructor": "GF2mField.create(32)", "q": Q, "m": 5,
            "primitive_polynomial": PRIMITIVE_POLYNOMIAL,
            "basis": field.basis, "symbol_encoding": field.symbol_encoding,
            "field_id": FIELD_ID, "ratio_order": RATIO_ORDER,
        },
        "input_bindings": {
            "v25_inventory": V25_INVENTORY,
            "v25_split_manifest": V25_SPLIT_MANIFEST,
            "v25_channel_counts": V25_CHANNEL_COUNTS,
            "v26_canonical": V26_CANONICAL,
            "v28r_canonical": V28R_CANONICAL,
        },
        "families": list(SUPPORTED_FAMILIES),
        "projective_gate": "zero_duplicate_projective_keys_and_proportional_pairs",
        "tanner6_score": "(degenerate_6_new,ratio_index)",
        "tanner8": "topology_only",
        "standard_variable_side_ace": "omitted_for_dv_2",
    }


def _matrix_array(matrix: Any) -> np.ndarray:
    arr = np.asarray(matrix, dtype=np.int64)
    if arr.ndim != 2:
        raise ValueError("matrix must be a two-dimensional array")
    if np.any(arr < 0) or np.any(arr >= Q):
        raise ValueError("matrix values must be in GF(32)")
    return arr


def _column_support(matrix: np.ndarray, column: int) -> tuple[int, int]:
    nz = np.flatnonzero(matrix[:, int(column)] != 0).tolist()
    if len(nz) != 2:
        raise ValueError(f"column {column} must have exactly two nonzero entries")
    return int(nz[0]), int(nz[1])


def projective_key(field: GF2mField, support: Sequence[int], coefficients: Sequence[int]) -> tuple[int, int, int]:
    """Return the sorted-support normalized projective key ``(a,b,h_b/h_a)``."""
    if not isinstance(field, GF2mField) or field.q != Q:
        raise ValueError("V30R projective keys require the pinned GF(32) field")
    if len(support) != 2 or len(coefficients) != 2:
        raise ValueError("degree-two support and coefficient lengths must be two")
    a, b = (int(support[0]), int(support[1]))
    ha, hb = (int(coefficients[0]), int(coefficients[1]))
    if a == b or a > b:
        raise ValueError("support must be sorted with a < b")
    if ha == 0 or hb == 0:
        raise ValueError("projective coefficients must be nonzero")
    return (a, b, field.mul(hb, field.inverse(ha)))


def _key_json(key: Sequence[int]) -> list[int]:
    return [int(x) for x in key]


def projective_column_audit(matrix: Any, field: GF2mField | None = None) -> dict[str, Any]:
    """Audit every degree-two column and the exact projective hard gate."""
    field = field or FIELD
    arr = _matrix_array(matrix)
    rows, columns = arr.shape
    duplicate_groups: dict[tuple[int, int, int], list[int]] = defaultdict(list)
    support_groups: dict[tuple[int, int], list[int]] = defaultdict(list)
    columns_doc: list[dict[str, Any]] = []
    zero_columns: list[int] = []
    invalid_columns: list[int] = []
    for j in range(columns):
        nz = np.flatnonzero(arr[:, j] != 0).tolist()
        if len(nz) != 2:
            invalid_columns.append(j)
            if not nz:
                zero_columns.append(j)
            columns_doc.append({"column": j, "support": [int(x) for x in nz], "valid": False})
            continue
        a, b = (int(nz[0]), int(nz[1]))
        coeff = (int(arr[a, j]), int(arr[b, j]))
        key = projective_key(field, (a, b), coeff)
        support_groups[(a, b)].append(j)
        duplicate_groups[key].append(j)
        ratio_index = field.nonzero_cycle.index(key[2])
        columns_doc.append({
            "column": j, "support": [a, b], "coefficients": list(coeff),
            "projective_key": _key_json(key), "ratio_index": int(ratio_index),
            "valid": True,
        })
    duplicate = {key: cols for key, cols in duplicate_groups.items() if len(cols) > 1}
    proportional_pairs = sum(len(cols) * (len(cols) - 1) // 2 for cols in duplicate.values())
    support_pair_count = sum(len(cols) * (len(cols) - 1) // 2 for cols in support_groups.values())
    zero_rows = np.flatnonzero(np.count_nonzero(arr, axis=1) == 0).astype(int).tolist()
    rank = int(codebook.gf_rank(arr.tolist(), field)) if rows and columns else 0
    return {
        "schema": "nbldpc_v30r_projective_column_audit_v1",
        "shape": [int(rows), int(columns)], "row_count": int(rows), "column_count": int(columns),
        "columns": columns_doc,
        "support_groups": {f"{a},{b}": len(cols) for (a, b), cols in sorted(support_groups.items())},
        "support_group_count": len(support_groups),
        "max_support_group_multiplicity": max((len(v) for v in support_groups.values()), default=0),
        "duplicate_groups": [
            {"projective_key": _key_json(key), "columns": list(cols)}
            for key, cols in sorted(duplicate.items())
        ],
        "duplicate_projective_classes": len(duplicate),
        "affected_columns": sum(len(cols) for cols in duplicate.values()),
        "proportional_pairs": int(proportional_pairs),
        "ordinary_four_cycle_count": int(support_pair_count),
        "zero_columns": zero_columns,
        "invalid_degree_columns": invalid_columns,
        "zero_rows": zero_rows,
        "rank": rank,
        "full_row_rank": bool(rank == rows),
        "projective_safe": bool(not invalid_columns and not zero_rows and not duplicate and rank == rows),
    }


def run_m0_baseline(*, canonical_root: str | Path | None = None) -> dict[str, Any]:
    """Rebuild the accepted V28R matrix in memory and reproduce the M0 counts.

    ``canonical_root`` is checked read-only when supplied; no evidence file is
    modified and no parquet/DE/decoder path is touched.  The baseline values
    are the shared-L1 values frozen by V30R design section 1.
    """
    root = Path(canonical_root) if canonical_root is not None else _repo_root() / V28R_CANONICAL
    required = ["v28_config.json", "v28_evidence.json", "RUN_MANIFEST.json", "readonly_verify.json"]
    missing = [name for name in required if not (root / name).exists()]
    config_path = root / "v28_config.json"
    config_problems: list[str] = []
    if not config_path.exists():
        config_problems.append("missing canonical v28_config.json")
        canonical_config = v28.frozen_v28_config()
    else:
        try:
            canonical_config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError) as exc:
            config_problems.append(f"cannot read canonical v28_config.json: {type(exc).__name__}")
            canonical_config = v28.frozen_v28_config()
    config_checks = {
        "schema": canonical_config.get("schema") == "nbldpc_v28r_frozen_config_v2",
        "q": canonical_config.get("q") == Q,
        "n": canonical_config.get("n") == N,
        "m1": canonical_config.get("m1") == 6,
        "m2_max": canonical_config.get("m2_max") == 202,
        "field_id": canonical_config.get("field_id") == FIELD_ID,
        "factorization": canonical_config.get("factorization") == "F03_natural_MSB_to_LSB_GF32_plus_GF32",
        "seed_l1": canonical_config.get("seed_l1") == 2026082001,
        "seed_l2": canonical_config.get("seed_l2") == 2026082002,
    }
    expected_sources = {
        label: {
            "source_id": SOURCE_IDS[label], "delay_used_ps": SOURCE_DELAY_PS[label],
            "m2": SOURCE_M2_V28R[label],
        } for label in SOURCE_ORDER
    }
    source_checks = {}
    for label, expected_source in expected_sources.items():
        actual = canonical_config.get("sources", {}).get(label, {})
        source_checks[label] = all(actual.get(key) == value for key, value in expected_source.items())
    if not all(config_checks.values()):
        config_problems.extend(name for name, ok in config_checks.items() if not ok)
    config_problems.extend(f"source:{label}" for label, ok in source_checks.items() if not ok)
    # The matrix must be rebuilt from the canonical V28R config, not merely
    # from the current Python default.  This remains an in-memory operation.
    h1, h2 = v28.build_matrices(canonical_config)
    audits = {"L1": projective_column_audit(h1, FIELD)}
    audits.update({f"L2:{label}": projective_column_audit(matrix, FIELD) for label, matrix in h2.items()})
    l1 = audits["L1"]
    expected = {
        "support_group_count": 15,
        "max_support_group_multiplicity": 69,
        "duplicate_projective_classes": 303,
        "affected_columns": 922,
        "proportional_pairs": 1107,
    }
    reproduced = {name: l1[name] == value for name, value in expected.items()}
    return {
        "schema": "nbldpc_v30r_m0_baseline_v1", "canonical_root": str(root),
        "missing_canonical_files": missing, "canonical_config_checks": config_checks,
        "canonical_source_checks": source_checks, "config_problems": config_problems,
        "audits": audits,
        "expected_l1_counts": expected, "reproduced": reproduced,
        "ok": bool(not missing and not config_problems and all(reproduced.values())),
        "scientific_inputs_read": [], "decoder_rerun": False, "de_rerun": False,
    }


def _candidate_supports(m: int) -> tuple[tuple[int, int], ...]:
    if isinstance(m, bool) or not isinstance(m, Integral) or int(m) < 2:
        raise ValueError("m must be an integer >= 2")
    return tuple((a, b) for a in range(int(m)) for b in range(a + 1, int(m)))


def _degree_score(degrees: Sequence[int], a: int, b: int) -> tuple[int, int, int, int, int]:
    updated = list(map(int, degrees))
    updated[a] += 1
    updated[b] += 1
    occupancy_after = 1  # replaced by caller for the selected support
    return (occupancy_after, max(updated, default=0), sum(x * x for x in updated), a, b)


def build_supports_balanced(m: int, n: int = N) -> list[tuple[int, int]]:
    """Deterministic balanced support construction from design §4."""
    if int(n) < 1:
        raise ValueError("n must be positive")
    candidates = _candidate_supports(m)
    degrees = [0] * int(m)
    occupancy: Counter[tuple[int, int]] = Counter()
    selected: list[tuple[int, int]] = []
    for _j in range(int(n)):
        scored = []
        for a, b in candidates:
            after = list(degrees)
            after[a] += 1
            after[b] += 1
            score = (
                1 + occupancy[(a, b)],
                max(after),
                sum(value * value for value in after),
                a, b,
            )
            scored.append((score, (a, b)))
        _, support = min(scored, key=lambda item: item[0])
        selected.append(support)
        occupancy[support] += 1
        degrees[support[0]] += 1
        degrees[support[1]] += 1
    return selected


def _shortest_edge_distance(adjacency: Sequence[set[int]], start: int, target: int) -> int | None:
    if start == target:
        return 0
    if not adjacency[start] or not adjacency[target]:
        return None
    queue: deque[tuple[int, int]] = deque([(start, 0)])
    seen = {start}
    while queue:
        node, distance = queue.popleft()
        for neighbour in sorted(adjacency[node]):
            if neighbour == target:
                return distance + 1
            if neighbour not in seen:
                seen.add(neighbour)
                queue.append((neighbour, distance + 1))
    return None


def peg_support_score(
    m: int, prior_supports: Sequence[Sequence[int]], candidate: Sequence[int],
) -> tuple[int, int, int, int, int, int]:
    """Return the exact frozen PEG support tuple for one candidate.

    ``component_flag=0,distance_cost=0`` is the explicit unreachable case.
    For a connected candidate, ``distance_cost`` is the negative local Tanner
    girth ``-(2*d_check+2)`` so lexicographic ``min`` maximizes that distance.
    Parallel prior support edges remain in ``prior_supports``; they do not
    create a shorter simple check-graph path.
    """
    m = int(m)
    if len(candidate) != 2:
        raise ValueError("candidate support must have two checks")
    a, b = map(int, candidate)
    if not (0 <= a < b < m):
        raise ValueError("candidate support must satisfy 0 <= a < b < m")
    degrees = [0] * m
    adjacency = [set() for _ in range(m)]
    for support in prior_supports:
        if len(support) != 2:
            raise ValueError("prior supports must have two checks")
        u, v = map(int, support)
        if not (0 <= u < v < m):
            raise ValueError("prior support outside check domain")
        degrees[u] += 1
        degrees[v] += 1
        adjacency[u].add(v)
        adjacency[v].add(u)
    degrees[a] += 1
    degrees[b] += 1
    distance_edges = _shortest_edge_distance(adjacency, a, b)
    if distance_edges is None:
        component_flag, distance_cost = 0, 0
    else:
        component_flag, distance_cost = 1, -(2 * distance_edges + 2)
    return (
        int(component_flag), int(distance_cost), int(max(degrees, default=0)),
        int(sum(value * value for value in degrees)), a, b,
    )


def build_supports_peg(m: int, n: int = N) -> list[tuple[int, int]]:
    """Deterministic PEG support construction from design §4.

    The adjacency sets are used only for shortest-path distance.  The
    ``edges`` list retains parallel support edges, making the state a check
    multigraph as required by the frozen contract.
    """
    if int(n) < 1:
        raise ValueError("n must be positive")
    candidates = _candidate_supports(m)
    degrees = [0] * int(m)
    occupancy: Counter[tuple[int, int]] = Counter()
    adjacency = [set() for _ in range(int(m))]
    edges: list[tuple[int, int]] = []
    selected: list[tuple[int, int]] = []
    for _j in range(int(n)):
        scored = []
        for a, b in candidates:
            distance_edges = _shortest_edge_distance(adjacency, a, b)
            after = list(degrees)
            after[a] += 1
            after[b] += 1
            if distance_edges is None:
                component_flag, distance_cost = 0, 0
            else:
                component_flag, distance_cost = 1, -(2 * distance_edges + 2)
            scored.append((
                (component_flag, distance_cost, max(after),
                 sum(value * value for value in after), a, b),
                (a, b),
            ))
        _, support = min(scored, key=lambda item: item[0])
        selected.append(support)
        occupancy[support] += 1
        degrees[support[0]] += 1
        degrees[support[1]] += 1
        adjacency[support[0]].add(support[1])
        adjacency[support[1]].add(support[0])
        edges.append(support)
    return selected


def build_supports(family: str, m: int, n: int = N) -> list[tuple[int, int]]:
    if family == FAMILY_BALANCED:
        return build_supports_balanced(m, n)
    if family == FAMILY_PEG:
        return build_supports_peg(m, n)
    raise ValueError(f"unsupported V30R family: {family}")


def canonical_tanner6_tuple(j: int, a: int, k1: int, c: int, k2: int, b: int) -> tuple[int, int, int, int, int, int]:
    """Canonicalize the two orientations of one current-column Tanner-6."""
    left = (int(j), int(a), int(k1), int(c), int(k2), int(b))
    right = (int(j), int(b), int(k2), int(c), int(k1), int(a))
    return min(left, right)


def _coeff_for_prior(
    prior_supports: Sequence[Sequence[int]],
    prior_coefficients: Sequence[Sequence[int]],
) -> dict[tuple[int, int], list[tuple[int, int, int]]]:
    by_support: dict[tuple[int, int], list[tuple[int, int, int]]] = defaultdict(list)
    if len(prior_supports) != len(prior_coefficients):
        raise ValueError("prior support/coefficient lengths differ")
    for k, (support, coeff) in enumerate(zip(prior_supports, prior_coefficients)):
        if len(support) != 2 or len(coeff) != 2:
            raise ValueError("prior degree-two entries must have length two")
        a, b = map(int, support)
        if a > b:
            a, b = b, a
            coeff = (int(coeff[1]), int(coeff[0]))
        ha, hb = map(int, coeff)
        if not ha or not hb:
            raise ValueError("prior coefficients must be nonzero")
        by_support[(a, b)].append((int(k), ha, hb))
    return by_support


def tanner6_alternating_product(
    field: GF2mField, current_coefficients: Sequence[int],
    left_coefficients: Sequence[int], right_coefficients: Sequence[int],
) -> int:
    """Compute the frozen GF32 alternating product for a Tanner-6 cycle."""
    ha_j, hb_j = map(int, current_coefficients)
    ha_k1, hc_k1 = map(int, left_coefficients)
    hc_k2, hb_k2 = map(int, right_coefficients)
    value = field.mul(field.mul(
        field.mul(ha_j, field.inverse(ha_k1)),
        field.mul(hc_k1, field.inverse(hc_k2))),
        field.mul(hb_k2, field.inverse(hb_j)),
    )
    return int(value)


def newly_closed_tanner6(
    field: GF2mField,
    prior_supports: Sequence[Sequence[int]],
    prior_coefficients: Sequence[Sequence[int]],
    current_column: int,
    current_support: Sequence[int],
    current_coefficients: Sequence[int],
) -> dict[str, Any]:
    """Count only newly closed, degenerate Tanner-6 cycles containing ``j``."""
    a, b = map(int, current_support)
    if a > b:
        a, b = b, a
        current_coefficients = (int(current_coefficients[1]), int(current_coefficients[0]))
    if a == b or len(current_coefficients) != 2 or not all(int(x) for x in current_coefficients):
        raise ValueError("invalid current degree-two column")
    by_support = _coeff_for_prior(prior_supports, prior_coefficients)
    cycles: set[tuple[int, int, int, int, int, int]] = set()
    degenerate: list[tuple[int, int, int, int, int, int]] = []
    all_nodes = {a, b}
    all_nodes.update(int(x) for support in prior_supports for x in support)
    for c in sorted(all_nodes):
        if c in (a, b):
            continue
        left = by_support.get(tuple(sorted((a, c))), ())
        right = by_support.get(tuple(sorted((c, b))), ())
        for k1, ha_k1, hc_k1 in left:
            for k2, hc_k2, hb_k2 in right:
                if k1 == k2:
                    continue
                canonical = canonical_tanner6_tuple(current_column, a, k1, c, k2, b)
                # The explicit current-column representation is unique here;
                # the set keeps the orientation rule observable and robust.
                if canonical in cycles:
                    continue
                cycles.add(canonical)
                product = tanner6_alternating_product(
                    field, current_coefficients,
                    (ha_k1, hc_k1), (hc_k2, hb_k2),
                )
                if product == 1:
                    degenerate.append(canonical)
    return {
        "new_cycle_count": len(cycles),
        "degenerate_6_new": len(degenerate),
        "canonical_degenerate_cycles": sorted(degenerate),
    }


def score_tanner6_candidate(
    field: GF2mField,
    prior_supports: Sequence[Sequence[int]],
    prior_coefficients: Sequence[Sequence[int]],
    current_column: int,
    current_support: Sequence[int],
    ratio: int,
) -> int:
    """Return the scalar first component of the frozen candidate score."""
    result = newly_closed_tanner6(
        field, prior_supports, prior_coefficients, current_column,
        current_support, (1, int(ratio)),
    )
    return int(result["degenerate_6_new"])


def select_projective_ratio(
    field: GF2mField,
    prior_supports: Sequence[Sequence[int]],
    prior_coefficients: Sequence[Sequence[int]],
    current_column: int,
    current_support: Sequence[int],
    used_ratios: Iterable[int] | None = None,
) -> dict[str, Any]:
    """Choose the exact projective-safe ratio.

    ``used_ratios`` may be supplied explicitly.  When it is ``None`` the
    current support's normalized ratios are derived from prior coefficients;
    it is never treated as an implicit empty set.  Duplicate projective keys
    are filtered before any Tanner-6 score is evaluated.
    """
    a, b = map(int, current_support)
    if a >= b:
        raise ValueError("current support must be sorted")
    if used_ratios is None:
        used: set[int] = set()
        for support, coefficients in zip(prior_supports, prior_coefficients):
            if tuple(map(int, support)) != (a, b):
                continue
            if len(coefficients) != 2 or not int(coefficients[0]) or not int(coefficients[1]):
                raise ValueError("prior coefficients must be nonzero")
            used.add(field.mul(int(coefficients[1]), field.inverse(int(coefficients[0]))))
    else:
        used = {int(x) for x in used_ratios}
    candidates: list[tuple[tuple[int, int], int, int]] = []
    for ratio_index, ratio in enumerate(field.nonzero_cycle):
        # Projective duplicates are rejected before Tanner-6 scoring.
        if int(ratio) in used:
            continue
        count = score_tanner6_candidate(
            field, prior_supports, prior_coefficients, current_column,
            (a, b), int(ratio),
        )
        candidates.append(((count, int(ratio_index)), int(ratio), int(ratio_index)))
    if not candidates:
        raise ValueError(f"no projectively unique ratio remains for support {(a, b)}")
    score, ratio, ratio_index = min(candidates, key=lambda item: item[0])
    selected_cycles = newly_closed_tanner6(
        field, prior_supports, prior_coefficients, current_column,
        (a, b), (1, int(ratio)),
    )
    return {
        "coefficients": [1, int(ratio)], "ratio": int(ratio),
        "ratio_index": int(ratio_index), "score": [int(score[0]), int(score[1])],
        "new_cycle_count": int(selected_cycles["new_cycle_count"]),
        "candidate_count": len(candidates),
        "projective_key": [a, b, int(ratio)],
    }


def label_degree_two_column(
    field: GF2mField,
    prior_supports: Sequence[Sequence[int]],
    prior_coefficients: Sequence[Sequence[int]],
    current_column: int,
    current_support: Sequence[int],
    used_ratios: Iterable[int] | None = None,
) -> dict[str, Any]:
    """Compatibility wrapper for the explicit projective-ratio selector."""
    return select_projective_ratio(
        field, prior_supports, prior_coefficients, current_column,
        current_support, used_ratios,
    )


def cycle_topology(supports: Sequence[Sequence[int]]) -> dict[str, int]:
    """Return aggregate ordinary 4/6/8 topology counts only.

    These are deliberately topology metrics; no coefficient/FRC elimination
    is applied to the 6- or 8-cycle counts.
    """
    counts: Counter[tuple[int, int]] = Counter(tuple(sorted(map(int, p))) for p in supports)
    four = sum(value * (value - 1) // 2 for value in counts.values())
    nodes = sorted({node for support in counts for node in support})
    six = 0
    for a, b, c in combinations(nodes, 3):
        six += counts[(a, b)] * counts[(a, c)] * counts[(b, c)]
    eight = 0
    for a, b, c, d in combinations(nodes, 4):
        eight += counts[(a, b)] * counts[(b, c)] * counts[(c, d)] * counts[(a, d)]
        eight += counts[(a, b)] * counts[(b, d)] * counts[(c, d)] * counts[(a, c)]
        eight += counts[(a, c)] * counts[(b, c)] * counts[(b, d)] * counts[(a, d)]
    return {"four_cycle_count": int(four), "six_cycle_count": int(six), "eight_cycle_count": int(eight)}


def build_layer(
    m: int, n: int = N, *, family: str = FAMILY_BALANCED,
    field: GF2mField | None = None, require_full_rank: bool = True,
) -> tuple[tuple[tuple[int, ...], ...], dict[str, Any]]:
    """Build one deterministic degree-two matrix and its replayable audit."""
    field = field or FIELD
    if field.q != Q:
        raise ValueError("V30R matrices require GF(32)")
    if family not in SUPPORTED_FAMILIES:
        raise ValueError(f"unsupported V30R family: {family}")
    m, n = int(m), int(n)
    if m < 2 or n < 1:
        raise ValueError("invalid matrix dimensions")
    supports = build_supports(family, m, n)
    maximum_columns = len(_candidate_supports(m)) * (Q - 1)
    if n > maximum_columns:
        raise ValueError("matrix needs more projectively unique columns than the support space allows")
    rows = [[0] * n for _ in range(m)]
    prior_supports: list[tuple[int, int]] = []
    prior_coefficients: list[tuple[int, int]] = []
    used_by_support: dict[tuple[int, int], set[int]] = defaultdict(set)
    label_replay: list[dict[str, Any]] = []
    for j, support in enumerate(supports):
        a, b = support
        label = label_degree_two_column(
            field, prior_supports, prior_coefficients, j, support,
            used_by_support[support],
        )
        ha, hb = map(int, label["coefficients"])
        rows[a][j], rows[b][j] = ha, hb
        prior_supports.append((a, b))
        prior_coefficients.append((ha, hb))
        used_by_support[support].add(hb)
        label_replay.append({
            "column": int(j), "support": [a, b], "selected_ratio_index": int(label["ratio_index"]),
            "selected_score": list(label["score"]),
            "newly_closed_tanner6": int(label["new_cycle_count"]),
            "projective_key": list(label["projective_key"]),
        })
    matrix = tuple(tuple(int(x) for x in row) for row in rows)
    projective = projective_column_audit(matrix, field)
    topology = cycle_topology(supports)
    tanner6_new_total = sum(int(item["newly_closed_tanner6"]) for item in label_replay)
    tanner6_degenerate_total = sum(int(item["selected_score"][0]) for item in label_replay)
    tanner6_degenerate_max = max((int(item["selected_score"][0]) for item in label_replay), default=0)
    audit = {
        "schema": "nbldpc_v30r_matrix_audit_v1", "family": family,
        "shape": [m, n], "support_order": [list(pair) for pair in supports],
        "label_replay": label_replay, "projective": projective,
        "rank": int(projective["rank"]), "full_row_rank": bool(projective["full_row_rank"]),
        "four_cycle_count": int(topology["four_cycle_count"]),
        "six_cycle_count": int(topology["six_cycle_count"]),
        "eight_cycle_count": int(topology["eight_cycle_count"]),
        "tanner6_newly_closed_total": int(tanner6_new_total),
        "tanner6_degenerate_total": int(tanner6_degenerate_total),
        "tanner6_degenerate_max_per_column": int(tanner6_degenerate_max),
        "ordinary_short_cycle_frc_rule": "Pi(C)!=1; Pi(C)=1 is degenerate",
        "tanner8_rule": "topology_only",
        "standard_variable_side_ace": "omitted_for_dv_2",
        "projective_hard_gate": bool(projective["projective_safe"]),
        "construction_ok": bool(projective["projective_safe"] and (not require_full_rank or projective["full_row_rank"])),
    }
    return matrix, audit


def build_matrix_packet(
    m1: int, m2_by_source: Mapping[str, int], *, family: str = FAMILY_BALANCED,
    n: int = N, allocation_id: str | None = None,
) -> dict[str, Any]:
    """Build the shared-L1 and independent per-source L2 packet structure."""
    if set(m2_by_source) != set(SOURCE_ORDER):
        raise ValueError("m2_by_source must contain exactly the three frozen sources")
    l1, l1_audit = build_layer(int(m1), n, family=family)
    l2: dict[str, tuple[tuple[int, ...], ...]] = {}
    l2_audits: dict[str, dict[str, Any]] = {}
    for source in SOURCE_ORDER:
        matrix, audit = build_layer(int(m2_by_source[source]), n, family=family)
        l2[source], l2_audits[source] = matrix, audit
    components = {"L1": l1_audit["four_cycle_count"]}
    components.update({f"L2:{source}": l2_audits[source]["four_cycle_count"] for source in SOURCE_ORDER})
    packet = {
        "schema": "nbldpc_v30r_matrix_packet_v1",
        "matrix_id": f"{allocation_id or f'm1_{int(m1)}'}|{family}",
        "allocation_id": allocation_id or f"m1_{int(m1)}",
        "family": family, "q": Q, "n": int(n), "m1": int(m1),
        "m2_by_source": {source: int(m2_by_source[source]) for source in SOURCE_ORDER},
        "field": frozen_v30r_config(n=n)["field"],
        "matrices": {"L1": l1, "L2": l2},
        "audits": {"L1": l1_audit, "L2": l2_audits},
        "four_cycle_components": components,
        "four_cycle_count": int(sum(components.values())),
        "projective_hard_gate": bool(l1_audit["projective_hard_gate"] and all(a["projective_hard_gate"] for a in l2_audits.values())),
        "full_row_rank": bool(l1_audit["full_row_rank"] and all(a["full_row_rank"] for a in l2_audits.values())),
    }
    packet["construction_ok"] = bool(packet["projective_hard_gate"] and packet["full_row_rank"])
    return packet


def json_safe(value: Any) -> Any:
    """Convert numpy/scalar/tuple containers to JSON-compatible values."""
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, tuple):
        return [json_safe(x) for x in value]
    if isinstance(value, list):
        return [json_safe(x) for x in value]
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    return value


# ---------------------------------------------------------------------------
# V30R M1 allocation and M3 finite-gate orchestration
# ---------------------------------------------------------------------------


def load_bound_h_values(path: str | Path | None = None) -> dict[str, dict[str, float]]:
    """Load the frozen F03 float64 H values from V26 canonical M0 evidence."""
    if path is None:
        path = _repo_root() / V26_CANONICAL / "m0_report.json"
    path = Path(path)
    doc = json.loads(path.read_text(encoding="utf-8"))
    detail = doc.get("detail", {})
    values: dict[str, dict[str, float]] = {}
    for label in SOURCE_ORDER:
        source = SOURCE_IDS[label]
        entry = detail.get(f"A02:{source}")
        if not isinstance(entry, Mapping) or not isinstance(entry.get("adapter_H"), Mapping):
            raise ValueError(f"V26 canonical M0 has no A02 adapter_H for {source}")
        h = entry["adapter_H"]
        values[label] = {"L1": float(h["L1"]), "L2": float(h["L2"])}
    return values


def load_v26_adapters_once() -> dict[str, Any]:
    """Load the accepted V26 F03 adapters once for the complete production gate."""
    from .nonbinary_v26_channel import build_adapter, load_channel_counts
    counts = load_channel_counts(_resolved_repo_path(V25_CHANNEL_COUNTS))
    return {
        label: build_adapter(counts, fact_id="F03", source=SOURCE_IDS[label])
        for label in SOURCE_ORDER
    }


def build_allocation_plan(
    *, m1_candidates: Sequence[int] = M1_CANDIDATES, n: int = N,
    h_values: Mapping[str, Mapping[str, float]] | None = None,
) -> list[dict[str, Any]]:
    """Build the six frozen allocation records and exact leakage accounting."""
    h_values = h_values or SOURCE_H
    result: list[dict[str, Any]] = []
    for m1 in map(int, m1_candidates):
        if m1 not in M1_CANDIDATES:
            raise ValueError(f"unregistered V30R m1 candidate: {m1}")
        allocation_id = f"m1_{m1}"
        sources: dict[str, Any] = {}
        for label in SOURCE_ORDER:
            m_total = int(SOURCE_M_TOTAL[label])
            m2 = m_total - m1
            if m2 <= 0 or m2 >= int(n):
                raise ValueError(f"invalid m2={m2} for {label}, m1={m1}")
            h = {"L1": float(h_values[label]["L1"]), "L2": float(h_values[label]["L2"])}
            layers: dict[str, Any] = {}
            for layer, m in (("L1", m1), ("L2", m2)):
                leak = float(5 * int(m))
                entropy = float(h[layer])
                layers[layer] = {
                    "m": int(m), "H_bits_per_symbol": entropy,
                    "rate": float(1.0 - float(m) / float(n)),
                    "leak_bits": leak,
                    "f": float(leak / (float(n) * entropy)),
                }
            total_leak = float(5 * m_total + TAG_BITS)
            sources[label] = {
                "source": label, "source_id": SOURCE_IDS[label],
                "delay_used_ps": int(SOURCE_DELAY_PS[label]),
                "m_total": m_total, "m1": int(m1), "m2": int(m2),
                "H": h, "layers": layers,
                "leak_total_bits": total_leak,
                "f_total": float(total_leak / (float(n) * (h["L1"] + h["L2"]))),
            }
        result.append({
            "allocation_id": allocation_id, "m1": int(m1), "n": int(n),
            "m2_by_source": {label: sources[label]["m2"] for label in SOURCE_ORDER},
            "sources": sources, "tag_bits": TAG_BITS,
            "total_formula": "leak_total=5*m_total+64; f_total=leak_total/(n*(H_L1+H_L2))",
        })
    return result


def _invoke_de_runner(runner: Any, item: Mapping[str, Any], adapter: Any) -> Mapping[str, Any]:
    if runner is None:
        from . import nonbinary_v26_mcde as mcde
        if adapter is None:
            raise ValueError("V30R M1 production call requires a preloaded V26 adapter")
        layer = str(item["layer"])
        channel = adapter.make_channel_sampler(layer)
        rate = float(item["rate"])
        rho = mcde.make_rho(rate, {2: 1})
        result = mcde.run_mcde_posterior(
            Q, {2: 1}, rho, channel_sampler=channel,
            n_samples=int(item["n_samples"]), max_iter=int(item["max_iter"]),
            seed=int(item["seed"]), entropy_tol_bits=ENTROPY_TOL_BITS, streak=20,
        )
        return result
    return _invoke_callable(runner, [(item, adapter), (item,)])


def _invoke_callable(fn: Any, candidates: Sequence[tuple[Any, ...]]) -> Mapping[str, Any]:
    """Call an injected test runner without masking runner-internal errors."""
    try:
        signature = inspect.signature(fn)
        positional = [p for p in signature.parameters.values()
                      if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
        has_varargs = any(p.kind == p.VAR_POSITIONAL for p in signature.parameters.values())
        required = sum(p.default is p.empty for p in positional)
        maximum = float("inf") if has_varargs else len(positional)
        for args in candidates:
            if required <= len(args) <= maximum:
                return fn(*args)
    except (TypeError, ValueError):
        pass
    return fn(*candidates[0])


def _finite_json_value(value: Any) -> Any:
    """Replace non-finite numeric leaves with JSON null for evidence."""
    value = json_safe(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, list):
        return [_finite_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _finite_json_value(item) for key, item in value.items()}
    return value


def _normalize_de_result(raw: Mapping[str, Any], item: Mapping[str, Any], runtime_s: float) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise TypeError("DE runner must return a mapping")
    converged = bool(raw.get("converged", raw.get("status") in {"converged", "success"}))
    entropy = float(raw.get("final_entropy_bits", raw.get("final_entropy", math.inf)))
    terminal = str(raw.get("terminal", "converged" if converged else "not_converged"))
    if not math.isfinite(entropy):
        return {
            **{key: item[key] for key in ("allocation_id", "m1", "m2", "source", "source_id", "delay_used_ps", "layer", "seed", "rate", "f", "H_bits_per_symbol", "n_samples", "max_iter") if key in item},
            "converged": False, "final_entropy_bits": None,
            "iterations": int(raw.get("iterations", raw.get("iteration", 0))),
            "terminal": TERMINAL_IMPL, "error": "nonfinite_final_entropy_bits",
            "nonfinite_result": True,
            "entropy_trace_bits": _finite_json_value(raw.get("entropy_trace_bits", raw.get("entropy_trace", []))),
            "runtime_s": float(raw.get("runtime_s", runtime_s)),
        }
    return {
        **{key: item[key] for key in ("allocation_id", "m1", "m2", "source", "source_id", "delay_used_ps", "layer", "seed", "rate", "f", "H_bits_per_symbol", "n_samples", "max_iter") if key in item},
        "converged": converged, "final_entropy_bits": entropy,
        "iterations": int(raw.get("iterations", raw.get("iteration", 0))),
        "terminal": terminal, "nonfinite_result": False,
        "entropy_trace_bits": _finite_json_value(raw.get("entropy_trace_bits", raw.get("entropy_trace", []))),
        "runtime_s": float(raw.get("runtime_s", runtime_s)),
    }


def _screen_items(allocations: Sequence[Mapping[str, Any]]) -> Iterable[dict[str, Any]]:
    for allocation in allocations:
        for seed in SCREEN_SEEDS:
            for label in SOURCE_ORDER:
                source = allocation["sources"][label]
                for layer in ("L1", "L2"):
                    info = source["layers"][layer]
                    yield {
                        "allocation_id": allocation["allocation_id"], "m1": allocation["m1"],
                        "m2": source["m2"], "source": label,
                        "source_id": source["source_id"], "delay_used_ps": source["delay_used_ps"],
                        "layer": layer, "seed": int(seed), "rate": info["rate"],
                        "f": info["f"], "H_bits_per_symbol": info["H_bits_per_symbol"],
                        "n_samples": SCREEN_N_SAMPLES, "max_iter": SCREEN_MAX_ITER,
                    }


def _confirmation_items(allocation: Mapping[str, Any]) -> Iterable[dict[str, Any]]:
    for seed in CONFIRMATION_SEEDS:
        for label in SOURCE_ORDER:
            source = allocation["sources"][label]
            for layer in ("L1", "L2"):
                info = source["layers"][layer]
                yield {
                    "allocation_id": allocation["allocation_id"], "m1": allocation["m1"],
                    "m2": source["m2"], "source": label,
                    "source_id": source["source_id"], "delay_used_ps": source["delay_used_ps"],
                    "layer": layer, "seed": int(seed), "rate": info["rate"],
                    "f": info["f"], "H_bits_per_symbol": info["H_bits_per_symbol"],
                    "n_samples": CONFIRMATION_N_SAMPLES, "max_iter": CONFIRMATION_MAX_ITER,
                }


def _m1_registry(
    allocations: Sequence[Mapping[str, Any]], screen: Mapping[str, Any],
    confirmation: Mapping[str, Any],
) -> dict[str, Any]:
    """Materialize the complete pre-registered M1 call registry.

    The registry is independent of runner results: it records the six frozen
    allocations, every registered screen descriptor, and the confirmation
    descriptor sequence implied by the selected allocation IDs.  Actual call
    results remain in the E03/E04 files.
    """
    allocations = list(allocations)
    by_id = {str(allocation["allocation_id"]): allocation for allocation in allocations}
    allocation_order = [str(allocation["allocation_id"]) for allocation in allocations]
    screen_order = list(_screen_items(allocations))
    selected = [str(value) for value in screen.get("selected_allocations", [])]
    if any(value not in by_id for value in selected):
        raise ValueError("M1 selected allocation is not in the frozen registry")
    confirmation_order: list[dict[str, Any]] = []
    for allocation_id in selected:
        confirmation_order.extend(_confirmation_items(by_id[allocation_id]))
    return {
        "schema": "nbldpc_v30r_m1_registry_v1",
        "allocation_order": allocation_order,
        "allocations": json_safe(allocations),
        "screen": {
            "seed_order": list(SCREEN_SEEDS), "n_samples": SCREEN_N_SAMPLES,
            "max_iter": SCREEN_MAX_ITER, "entropy_tol_bits": ENTROPY_TOL_BITS,
            "calls_per_allocation": 12, "expected_calls": 72,
            "registered_call_order": json_safe(screen_order),
            "selected_allocations": selected,
            "allocation_call_sets": {
                allocation_id: [index for index, item in enumerate(screen_order)
                                if item["allocation_id"] == allocation_id]
                for allocation_id in allocation_order
            },
        },
        "confirmation": {
            "seed_order": list(CONFIRMATION_SEEDS), "n_samples": CONFIRMATION_N_SAMPLES,
            "max_iter": CONFIRMATION_MAX_ITER, "entropy_tol_bits": ENTROPY_TOL_BITS,
            "calls_per_allocation": 30, "expected_max_calls": 60,
            "selected_allocations": selected,
            "registered_call_order": json_safe(confirmation_order),
            "allocation_call_sets": {
                allocation_id: [index for index, item in enumerate(confirmation_order)
                                if item["allocation_id"] == allocation_id]
                for allocation_id in selected
            },
            "confirmed_allocations": [str(value) for value in confirmation.get("confirmed_allocations", [])],
        },
        "selection": {
            "screen_selected_allocations": selected,
            "confirmation_selected_allocations": [str(value) for value in confirmation.get("selected_allocations", [])],
            "confirmed_allocations": [str(value) for value in confirmation.get("confirmed_allocations", [])],
        },
    }


def _allocation_rank(calls: Sequence[Mapping[str, Any]], allocation: Mapping[str, Any]) -> tuple[float, float, int]:
    own = [row for row in calls if row.get("allocation_id") == allocation["allocation_id"]]
    entropies = [math.inf if row.get("final_entropy_bits") is None else float(row.get("final_entropy_bits")) for row in own]
    return (max(entropies, default=math.inf), sum(entropies) / len(entropies) if entropies else math.inf, int(allocation["m1"]))


def _is_de_pass(row: Mapping[str, Any]) -> bool:
    entropy = row.get("final_entropy_bits")
    return bool(row.get("converged")) and entropy is not None and math.isfinite(float(entropy)) and float(entropy) <= ENTROPY_TOL_BITS


def _validate_de_call_rows(rows: Sequence[Mapping[str, Any]], label: str) -> list[str]:
    """Validate persisted DE result types without rerunning DE."""
    problems: list[str] = []
    for index, row in enumerate(rows):
        prefix = f"{label}_row:{index}"
        iterations = row.get("iterations")
        if isinstance(iterations, bool) or not isinstance(iterations, int) or iterations < 0:
            problems.append(f"{prefix}:iterations")
        entropy = row.get("final_entropy_bits")
        terminal = row.get("terminal")
        if not isinstance(terminal, str) or not terminal:
            problems.append(f"{prefix}:terminal")
        is_implementation = terminal == TERMINAL_IMPL
        if entropy is None:
            if not is_implementation:
                problems.append(f"{prefix}:null_entropy_without_implementation")
        elif isinstance(entropy, bool) or not isinstance(entropy, (int, float)) or not math.isfinite(float(entropy)):
            problems.append(f"{prefix}:entropy")
        trace = row.get("entropy_trace_bits")
        if not isinstance(trace, list):
            problems.append(f"{prefix}:entropy_trace")
        else:
            for value in trace:
                if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value))):
                    problems.append(f"{prefix}:entropy_trace_value")
                    break
        runtime = row.get("runtime_s")
        if isinstance(runtime, bool) or not isinstance(runtime, (int, float)) or not math.isfinite(float(runtime)) or float(runtime) < 0:
            problems.append(f"{prefix}:runtime")
        nonfinite = row.get("nonfinite_result", False)
        if not isinstance(nonfinite, bool):
            problems.append(f"{prefix}:nonfinite_flag")
        if is_implementation and not isinstance(row.get("error"), str):
            problems.append(f"{prefix}:implementation_error")
        if nonfinite and entropy is not None:
            problems.append(f"{prefix}:nonfinite_entropy_not_null")
    return problems


def run_m1_screen(
    allocations: Sequence[Mapping[str, Any]], *, de_runner: Any = None,
    adapters: Mapping[str, Any] | None = None,
    resource_limit_seconds: float = RESOURCE_LIMIT_SECONDS,
) -> dict[str, Any]:
    """Run the exact 72-call M1 screen, retaining failed allocations."""
    adapters = dict(adapters or {})
    if de_runner is None and not adapters:
        adapters = load_v26_adapters_once()
    calls: list[dict[str, Any]] = []
    meter = 0.0
    terminal: str | None = None
    plan = list(_screen_items(allocations))
    for index, item in enumerate(plan):
        # The resource gate is checked before starting the next registered
        # call.  The current call, if any, was already persisted below.
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
                   "nonfinite_result": False,
                   "entropy_trace_bits": [], "runtime_s": time.monotonic() - started,
                   "error": f"{type(exc).__name__}: {exc}"}
            meter += float(row["runtime_s"])
            terminal = TERMINAL_IMPL
        if row.get("terminal") == TERMINAL_IMPL or row.get("nonfinite_result"):
            terminal = TERMINAL_IMPL
        row["call_index"] = len(calls)
        calls.append(row)  # persist current call before any gate decision
        remaining = len(plan) - index - 1
        if terminal == TERMINAL_IMPL:
            break
        if remaining and meter >= float(resource_limit_seconds):
            terminal = TERMINAL_RESOURCE
            break
    allocation_counts = {
        allocation["allocation_id"]: sum(row.get("allocation_id") == allocation["allocation_id"] for row in calls)
        for allocation in allocations
    }
    eligible = [allocation for allocation in allocations
                if allocation_counts[allocation["allocation_id"]] == 12 and
                all(_is_de_pass(row) for row in calls if row.get("allocation_id") == allocation["allocation_id"])]
    ranks = {allocation["allocation_id"]: list(_allocation_rank(calls, allocation)) for allocation in eligible}
    ordered = sorted(eligible, key=lambda allocation: _allocation_rank(calls, allocation))
    selected = ordered[:2]
    # A complete screen at the meter limit still needs a confirmation stage
    # when an eligible allocation exists; block before starting that stage.
    if terminal is None and len(calls) == len(plan) and meter >= float(resource_limit_seconds) and eligible:
        terminal = TERMINAL_RESOURCE
    return {
        "schema": "nbldpc_v30r_de_allocation_screen_v1", "calls": calls,
        "n_calls": len(calls), "expected_calls": 72,
        "allocation_call_counts": allocation_counts,
        "allocation_eligibility": {allocation["allocation_id"]: allocation in eligible for allocation in allocations},
        "eligible_allocations": [allocation["allocation_id"] for allocation in eligible],
        "rank_tuples": ranks, "selected_allocations": [allocation["allocation_id"] for allocation in selected],
        "resource_meter_seconds": meter, "resource_limit_seconds": float(resource_limit_seconds),
        "terminal": terminal, "registered_plan_calls": len(plan),
    }


def run_m1_confirmation(
    screen: Mapping[str, Any], allocations: Sequence[Mapping[str, Any]], *,
    de_runner: Any = None, adapters: Mapping[str, Any] | None = None,
    resource_limit_seconds: float = RESOURCE_LIMIT_SECONDS,
    initial_resource_meter_seconds: float = 0.0,
) -> dict[str, Any]:
    """Run each selected allocation's complete 30-call confirmation."""
    if screen.get("terminal") in {TERMINAL_RESOURCE, TERMINAL_IMPL}:
        return {
            "schema": "nbldpc_v30r_de_allocation_confirmation_v1", "calls": [],
            "n_calls": 0, "expected_max_calls": 60,
            "selected_allocations": list(screen.get("selected_allocations", [])),
            "allocation_call_counts": {
                str(allocation_id): 0 for allocation_id in screen.get("selected_allocations", [])
            },
            "allocation_confirmed": {
                str(allocation_id): False for allocation_id in screen.get("selected_allocations", [])
            },
            "confirmed_allocations": [], "resource_meter_seconds": float(screen.get("resource_meter_seconds", 0.0)),
            "resource_limit_seconds": float(resource_limit_seconds),
            "terminal": screen.get("terminal"),
        }
    selected_ids = list(screen.get("selected_allocations", []))
    by_id = {allocation["allocation_id"]: allocation for allocation in allocations}
    calls: list[dict[str, Any]] = []
    adapters = dict(adapters or {})
    if de_runner is None and not adapters:
        adapters = load_v26_adapters_once()
    meter = float(initial_resource_meter_seconds)
    terminal: str | None = None
    for allocation_id in selected_ids:
        allocation = by_id[allocation_id]
        items = list(_confirmation_items(allocation))
        for index, item in enumerate(items):
            if meter >= float(resource_limit_seconds):
                terminal = TERMINAL_RESOURCE
                break
            started = time.monotonic()
            try:
                raw = _invoke_de_runner(de_runner, item, (adapters or {}).get(item["source"]))
                elapsed = time.monotonic() - started
                row = _normalize_de_result(raw, item, elapsed)
                runtime = float(row["runtime_s"])
                if not math.isfinite(runtime) or runtime < 0:
                    raise ValueError("DE runtime_s must be finite and nonnegative")
                meter += runtime
            except Exception as exc:
                row = {**item, "converged": False, "final_entropy_bits": None,
                       "iterations": 0, "terminal": TERMINAL_IMPL,
                       "nonfinite_result": False,
                       "entropy_trace_bits": [], "runtime_s": time.monotonic() - started,
                       "error": f"{type(exc).__name__}: {exc}"}
                meter += float(row["runtime_s"])
                terminal = TERMINAL_IMPL
            if row.get("terminal") == TERMINAL_IMPL or row.get("nonfinite_result"):
                terminal = TERMINAL_IMPL
            row["call_index"] = len(calls)
            calls.append(row)
            remaining = sum(30 for candidate in selected_ids if candidate == allocation_id) - index - 1
            remaining += sum(30 for candidate in selected_ids[selected_ids.index(allocation_id) + 1:]) if selected_ids.index(allocation_id) < len(selected_ids) - 1 else 0
            if terminal == TERMINAL_IMPL:
                break
            if remaining and meter >= float(resource_limit_seconds):
                terminal = TERMINAL_RESOURCE
                break
        if terminal is not None:
            break
    outcomes: dict[str, bool] = {}
    for allocation_id in selected_ids:
        own = [row for row in calls if row.get("allocation_id") == allocation_id]
        outcomes[allocation_id] = len(own) == 30 and all(_is_de_pass(row) for row in own)
    confirmed = [allocation_id for allocation_id in selected_ids if outcomes.get(allocation_id)]
    if terminal is None and not confirmed:
        terminal = TERMINAL_DE_FAIL
    elif terminal is None:
        terminal = "de_allocation_pass"
    return {
        "schema": "nbldpc_v30r_de_allocation_confirmation_v1", "calls": calls,
        "n_calls": len(calls), "expected_max_calls": 60,
        "selected_allocations": selected_ids, "allocation_call_counts": {
            allocation_id: sum(row.get("allocation_id") == allocation_id for row in calls)
            for allocation_id in selected_ids
        },
        "allocation_confirmed": outcomes, "confirmed_allocations": confirmed,
        "resource_meter_seconds": meter, "resource_limit_seconds": float(resource_limit_seconds),
        "terminal": terminal,
    }


def build_confirmed_packets(
    confirmation: Mapping[str, Any], allocations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build at most two deterministic family packets per confirmed allocation."""
    by_id = {allocation["allocation_id"]: allocation for allocation in allocations}
    packets: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for allocation_id in list(confirmation.get("confirmed_allocations", []))[:2]:
        allocation = by_id[allocation_id]
        for family in SUPPORTED_FAMILIES:
            try:
                packet = build_matrix_packet(
                    int(allocation["m1"]), allocation["m2_by_source"],
                    family=family, n=N, allocation_id=allocation_id,
                )
                packet["packet_id"] = packet["matrix_id"]
                if not packet["construction_ok"]:
                    raise ValueError("projective/rank hard gate failed")
                packets.append(packet)
            except Exception as exc:
                rejected.append({"allocation_id": allocation_id, "family": family,
                                 "terminal": TERMINAL_FINITE_FAIL,
                                 "error": f"{type(exc).__name__}: {exc}"})
    return {
        "schema": "nbldpc_v30r_matrix_construction_v1", "packets": packets,
        "rejected": rejected, "packet_cap": 4,
        "packet_cap_ok": len(packets) <= 4,
    }


def validation_frame_manifest() -> dict[str, Any]:
    """Return the exact V30R 300-block validation identity manifest."""
    sources: dict[str, Any] = {}
    blocks: list[dict[str, Any]] = []
    global_index = 0
    for label in SOURCE_ORDER:
        start, end = SOURCE_FRAME_RANGES[label]
        frame_ids = list(range(start, end + 1))
        source_blocks = []
        for block_index in range(BLOCKS_PER_SOURCE):
            frame_group = frame_ids[block_index * BLOCK_FRAMES:(block_index + 1) * BLOCK_FRAMES]
            row = {
                "global_block_index": global_index, "source": label,
                "source_id": SOURCE_IDS[label], "delay_used_ps": SOURCE_DELAY_PS[label],
                "block_index": block_index, "frame_ids": frame_group,
                "pair_idx_ranges": [[0, FRAME_PAIRS - 1]] * BLOCK_FRAMES,
            }
            blocks.append(row)
            source_blocks.append(row)
            global_index += 1
        sources[label] = {
            "source_id": SOURCE_IDS[label], "delay_used_ps": SOURCE_DELAY_PS[label],
            "pairs_parquet": SOURCE_PARQUETS[label],
            "frame_start": start, "frame_end": end, "frame_count": BLOCKS_PER_SOURCE * BLOCK_FRAMES,
            "frame_ids": frame_ids, "pair_count_per_frame": FRAME_PAIRS,
            "pair_idx_range": [0, FRAME_PAIRS - 1], "block_count": BLOCKS_PER_SOURCE,
        }
    return {
        "frame_selection": {"schema": "nbldpc_v30r_frame_selection_v1", "sources": sources},
        "block_manifest": {"schema": "nbldpc_v30r_block_manifest_v1", "block_count": len(blocks), "blocks": blocks},
    }


def _validate_validation_blocks(blocks: Sequence[Mapping[str, Any]]) -> None:
    if len(blocks) != len(SOURCE_ORDER) * BLOCKS_PER_SOURCE:
        raise ValueError("V30R validation requires exactly 300 blocks")
    for label in SOURCE_ORDER:
        own = sorted((block for block in blocks if block.get("source") == label),
                     key=lambda block: int(block.get("block_index", -1)))
        if len(own) != BLOCKS_PER_SOURCE or [int(block.get("block_index", -1)) for block in own] != list(range(BLOCKS_PER_SOURCE)):
            raise ValueError(f"{label}: validation block index sequence is not 0..99")
        start, end = SOURCE_FRAME_RANGES[label]
        for block in own:
            index = int(block["block_index"])
            expected_global_index = SOURCE_ORDER.index(label) * BLOCKS_PER_SOURCE + index
            if int(block.get("global_block_index", -1)) != expected_global_index:
                raise ValueError(f"{label} block {index}: global block index mismatch")
            expected_frames = list(range(start + index * BLOCK_FRAMES, start + (index + 1) * BLOCK_FRAMES))
            if list(block.get("frame_ids", [])) != expected_frames:
                raise ValueError(f"{label} block {index}: frame ids do not match frozen range")
            if block.get("source_id") != SOURCE_IDS[label] or block.get("delay_used_ps") != SOURCE_DELAY_PS[label]:
                raise ValueError(f"{label} block {index}: source metadata mismatch")
            if list(block.get("pair_idx_ranges", [])) != [[0, FRAME_PAIRS - 1]] * BLOCK_FRAMES:
                raise ValueError(f"{label} block {index}: pair-index ranges mismatch")
            for key in ("alice_symbols", "bob_symbols"):
                values = np.asarray(block.get(key), dtype=np.int64)
                if values.shape != (N,) or np.any(values < 0) or np.any(values >= 1024):
                    raise ValueError(f"{label} block {index}: {key} shape/domain mismatch")


def load_validation_blocks() -> list[dict[str, Any]]:
    """Load only the frozen V25 validation ranges through the accepted V29 loader."""
    from . import nonbinary_v29 as v29
    cfg = {
        "source_order": list(SOURCE_ORDER),
        "sources": {
            label: {
                "source_id": SOURCE_IDS[label], "delay_used_ps": SOURCE_DELAY_PS[label],
                "frame_start": SOURCE_FRAME_RANGES[label][0], "frame_end": SOURCE_FRAME_RANGES[label][1],
                "block_count": BLOCKS_PER_SOURCE,
            } for label in SOURCE_ORDER
        },
    }
    blocks = v29.load_blocks(SOURCE_PARQUETS, config=cfg, input_root=_repo_root())
    _validate_validation_blocks(blocks)
    return blocks


def _factor_layers(symbols: Sequence[int]) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(symbols, dtype=np.int64)
    if values.ndim != 1 or np.any(values < 0) or np.any(values >= 1024):
        raise ValueError("F03 symbols must be one-dimensional 10-bit values")
    return ((values >> 5) & 31).astype(np.int64), (values & 31).astype(np.int64)


def _default_decoder_runner(block_public: Mapping[str, Any], public: Mapping[str, Any], adapter: Any,
                            packet: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    """Bob-only V28/V26 decoder binding used only by an authorized production run."""
    from . import nonbinary_v10_fftqspa as qspa
    if adapter is None:
        raise ValueError("V30R decoder requires the accepted V26 channel adapter")
    bob = np.asarray(public["bob_symbols"], dtype=np.int64)
    y1, y2 = _factor_layers(bob)
    matrices = packet["matrices"]
    h1, h2 = matrices["L1"], matrices["L2"][block_public["source"]]
    field = FIELD
    rows1 = adapter.posterior_rows("L1", bob)
    r1 = v28.decode_error_domain_posterior(
        field, y1.tolist(), h1, public["s1"], v28._center_rows(field, rows1, y1),
        int(config.get("max_iter", CONFIRMATION_MAX_ITER)), streak=20,
    )
    if r1.get("status") != qspa.STATUS_SUCCESS or not r1.get("reconstruction_ok"):
        return {"L1": r1, "L2": {"status": "not_run", "x_hat": None,
                "reconstruction_ok": False, "syndrome_ok": False},
                "x1_hat": r1.get("x_hat"), "x2_hat": None,
                "l2_conditioning": "not_run", "decoder_calls": 1}
    x1_hat = r1.get("x_hat")
    rows2 = adapter.posterior_rows("L2", bob, x1_hat)
    r2 = v28.decode_error_domain_posterior(
        field, y2.tolist(), h2, public["s2"], v28._center_rows(field, rows2, y2),
        int(config.get("max_iter", CONFIRMATION_MAX_ITER)), streak=20,
    )
    return {"L1": r1, "L2": r2, "x1_hat": x1_hat,
            "x2_hat": r2.get("x_hat"), "l2_conditioning": "returned_L1_x1_hat",
            "decoder_calls": 2}


def _invoke_decoder(runner: Any, block_public: Mapping[str, Any], public: Mapping[str, Any],
                    adapter: Any, packet: Mapping[str, Any], config: Mapping[str, Any]) -> Mapping[str, Any]:
    if runner is None:
        return _default_decoder_runner(block_public, public, adapter, packet, config)
    return _invoke_callable(runner, [
        (block_public, public, adapter, packet, config),
        (block_public, public, packet, config),
        (block_public, public, packet),
        (block_public, public),
    ])


def _block_public_and_syndromes(block: Mapping[str, Any], packet: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], tuple[np.ndarray, np.ndarray] | None]:
    public = dict(block.get("public", {}))
    if "bob_symbols" in block:
        bob = np.asarray(block["bob_symbols"], dtype=np.int64)
        public["bob_symbols"] = bob
    if "s1" not in public or "s2" not in public:
        if "alice_symbols" not in block:
            raise ValueError("block needs public syndromes or Alice symbols for offline syndrome construction")
        truth1, truth2 = _factor_layers(block["alice_symbols"])
        public["s1"] = v28.compute_syndrome(FIELD, packet["matrices"]["L1"], truth1.tolist())
        public["s2"] = v28.compute_syndrome(FIELD, packet["matrices"]["L2"][block["source"]], truth2.tolist())
    oracle_keys = {"alice_symbols", "truth1", "truth2", "alice_truth", "alice_x1", "alice_x2", "x1", "x2", "tag_true"}
    block_public = {key: value for key, value in block.items() if key not in oracle_keys}
    return block_public, public, (_factor_layers(block["alice_symbols"]) if "alice_symbols" in block else None)


def _finite_block_record(block: Mapping[str, Any], public: Mapping[str, Any], result: Mapping[str, Any],
                         truth: tuple[np.ndarray, np.ndarray] | None,
                         packet: Mapping[str, Any], runtime_s: float) -> dict[str, Any]:
    l1 = result.get("L1", {}) if isinstance(result.get("L1", {}), Mapping) else {}
    l2 = result.get("L2", {}) if isinstance(result.get("L2", {}), Mapping) else {}
    x1 = result.get("x1_hat", l1.get("x_hat"))
    x2 = result.get("x2_hat", l2.get("x_hat"))
    l1_syndrome = None
    l2_syndrome = None
    l1_syndrome_ok = None
    l2_syndrome_ok = None
    if truth is not None:
        h1 = packet["matrices"]["L1"]
        h2 = packet["matrices"]["L2"][block["source"]]
        if x1 is not None:
            l1_syndrome = v28.compute_syndrome(FIELD, h1, [int(value) for value in x1])
        if x2 is not None:
            l2_syndrome = v28.compute_syndrome(FIELD, h2, [int(value) for value in x2])
        l1_syndrome_ok = bool(l1_syndrome is not None and l1_syndrome == [int(value) for value in public["s1"]])
        l2_syndrome_ok = bool(l2_syndrome is not None and l2_syndrome == [int(value) for value in public["s2"]])
        l1_ok = l1_syndrome_ok
    else:
        l1_ok = bool(result.get("l1_ok", l1.get("reconstruction_ok", l1.get("status") in {"success", "converged"})))
    if not l1_ok:
        x2 = None
        l2_status = "not_run"
        l2_ok = False
    else:
        l2_status = str(l2.get("status", result.get("l2_status", "success" if x2 is not None else "failed")))
        l2_ok = l2_syndrome_ok if truth is not None else bool(result.get("l2_ok", l2.get("reconstruction_ok", x2 is not None)))
    exact = None
    tag_verified = None
    false_accept = None
    true_tag = decoded_tag = None
    if truth is not None:
        true_tag = v29_tag64(truth[0], truth[1])
        if x1 is not None and x2 is not None:
            decoded_tag = v29_tag64(x1, x2)
        exact = bool(x1 is not None and x2 is not None and
                     np.array_equal(np.asarray(x1, dtype=np.int64), truth[0]) and
                     np.array_equal(np.asarray(x2, dtype=np.int64), truth[1]))
        tag_verified = bool(decoded_tag is not None and decoded_tag == true_tag)
        false_accept = bool(tag_verified and not exact)
    else:
        # This branch is reserved for in-memory fake runners that deliberately
        # omit Alice symbols.  A production block always has truth and follows
        # the recomputation branch above.
        exact = result.get("offline_exact")
        tag_verified = result.get("tag_verified")
        false_accept = result.get("false_accept")
    exact = bool(exact) if exact is not None else False
    tag_verified = bool(tag_verified) if tag_verified is not None else False
    false_accept = bool(false_accept) if false_accept is not None else bool(tag_verified and not exact)
    return {
        "schema": "nbldpc_v30r_block_result_v1", "packet_id": packet.get("packet_id", packet.get("matrix_id")),
        "source": block.get("source"), "source_id": block.get("source_id"),
        "delay_used_ps": block.get("delay_used_ps"), "block_index": int(block.get("block_index", -1)),
        "frame_ids": list(block.get("frame_ids", [])), "l1_ok": l1_ok,
        "l1_status": str(l1.get("status", result.get("l1_status", "success" if l1_ok else "failed"))),
        "l2_ok": l2_ok, "l2_status": l2_status, "l2_conditioning": result.get("l2_conditioning", "returned_L1_x1_hat" if l1_ok else "not_run"),
        "l2_not_run_due_l1": bool(not l1_ok and l2_status == "not_run"),
        "l1_syndrome": l1_syndrome, "l2_syndrome": l2_syndrome,
        "l1_syndrome_target": None if "s1" not in public else [int(value) for value in public["s1"]],
        "l2_syndrome_target": None if "s2" not in public else [int(value) for value in public["s2"]],
        "l1_syndrome_ok": l1_syndrome_ok if truth is not None else None,
        "l2_syndrome_ok": l2_syndrome_ok if truth is not None else None,
        "l1_symbol_errors": None if truth is None or x1 is None else int(np.count_nonzero(np.asarray(x1, dtype=np.int64) != truth[0])),
        "l2_symbol_errors": None if truth is None or x2 is None else int(np.count_nonzero(np.asarray(x2, dtype=np.int64) != truth[1])),
        "decoded_x1": None if x1 is None else [int(value) for value in x1],
        "decoded_x2": None if x2 is None else [int(value) for value in x2],
        "truth_x1": None if truth is None else [int(value) for value in truth[0]],
        "truth_x2": None if truth is None else [int(value) for value in truth[1]],
        "offline_exact": bool(exact) if exact is not None else False,
        "tag_verified": bool(tag_verified) if tag_verified is not None else False,
        "false_accept": bool(false_accept) if false_accept is not None else False,
        "true_tag": true_tag, "decoded_tag": decoded_tag,
        "l1_iterations": int(l1.get("iterations", l1.get("iteration", 0))),
        "l2_iterations": int(l2.get("iterations", l2.get("iteration", 0))),
        "decoder_calls": int(result.get("decoder_calls", 1 if not l1_ok else 2)),
        "runtime_s": float(result.get("runtime_s", runtime_s)),
    }


def v29_tag64(x1: Sequence[int], x2: Sequence[int]) -> str:
    import hashlib
    payload = bytes(int(v) & 0xFF for v in x1) + bytes(int(v) & 0xFF for v in x2)
    return hashlib.sha256(payload).digest()[:8].hex()


def _source_blocks(blocks: Sequence[Mapping[str, Any]], label: str, indices: Sequence[int]) -> list[Mapping[str, Any]]:
    by_index = {int(block.get("block_index", -1)): block for block in blocks if block.get("source") == label}
    return [by_index[index] for index in indices if index in by_index]


def _packet_screen_rank(packet: Mapping[str, Any], source_stats: Mapping[str, Mapping[str, int]]) -> tuple[int, int, int, int, int]:
    minimum = min((int(source_stats[label].get("offline_exact", 0)) for label in SOURCE_ORDER), default=0)
    total = sum(int(source_stats[label].get("offline_exact", 0)) for label in SOURCE_ORDER)
    return (
        -minimum, -total, int(packet.get("four_cycle_count", 0)),
        int(packet.get("m1", 0)), FAMILY_ORDER.get(str(packet.get("family")), 99),
    )


def _m3_recompute_selection(
    packets: Sequence[Mapping[str, Any]], records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Recompute M3 selection evidence from persisted block records only."""
    screen_outcomes: list[dict[str, Any]] = []
    for packet in packets:
        packet_id = str(packet.get("packet_id", packet.get("matrix_id")))
        rows = [row for row in records if str(row.get("packet_id")) == packet_id and row.get("stage") == "screen"]
        if not rows:
            continue
        stats = {
            label: {
                "completed": sum(row.get("source") == label for row in rows),
                "offline_exact": sum(int(bool(row.get("offline_exact"))) for row in rows if row.get("source") == label),
                "tag_verified": sum(int(bool(row.get("tag_verified"))) for row in rows if row.get("source") == label),
                "false_accept": sum(int(bool(row.get("false_accept"))) for row in rows if row.get("source") == label),
            } for label in SOURCE_ORDER
        }
        eligible = all(
            stats[label]["completed"] == len(SCREEN_BLOCKS) and
            stats[label]["offline_exact"] >= 15 and
            stats[label]["tag_verified"] >= 15 and
            stats[label]["false_accept"] == 0
            for label in SOURCE_ORDER
        )
        screen_outcomes.append({
            "packet_id": packet_id, "matrix_id": packet.get("matrix_id"),
            "family": packet.get("family"), "source_stats": stats,
            "rank_tuple": list(_packet_screen_rank(packet, stats)),
            "eligible": eligible,
            "status": "screen_pass" if eligible else "matrix_local_fail",
        })
    eligible_outcomes = [outcome for outcome in screen_outcomes if outcome["eligible"]]
    eligible_outcomes.sort(key=lambda outcome: tuple(outcome["rank_tuple"]))
    top_ranked_packet_ids: list[str] = []
    if eligible_outcomes:
        best_rank = tuple(eligible_outcomes[0]["rank_tuple"])
        top_ranked_packet_ids = [str(outcome["packet_id"]) for outcome in eligible_outcomes
                                 if tuple(outcome["rank_tuple"]) == best_rank]
    selected_packet_id = top_ranked_packet_ids[0] if len(top_ranked_packet_ids) == 1 else None
    confirmation_rows = [row for row in records if row.get("stage") == "confirmation"]
    confirmation = None
    if confirmation_rows:
        confirmation_packet_ids = sorted({str(row.get("packet_id")) for row in confirmation_rows})
        packet_id = confirmation_packet_ids[0] if len(confirmation_packet_ids) == 1 else None
        stats = {
            label: {
                "completed": sum(row.get("source") == label for row in confirmation_rows),
                "offline_exact": sum(int(bool(row.get("offline_exact"))) for row in confirmation_rows if row.get("source") == label),
                "tag_verified": sum(int(bool(row.get("tag_verified"))) for row in confirmation_rows if row.get("source") == label),
                "false_accept": sum(int(bool(row.get("false_accept"))) for row in confirmation_rows if row.get("source") == label),
            } for label in SOURCE_ORDER
        }
        passed = bool(packet_id is not None and all(
            stats[label]["completed"] == len(CONFIRMATION_BLOCKS) and
            stats[label]["offline_exact"] >= 45 and
            stats[label]["tag_verified"] >= 45 and
            stats[label]["false_accept"] == 0
            for label in SOURCE_ORDER
        ))
        confirmation = {
            "packet_id": packet_id, "source_stats": stats,
            "threshold": 45, "block_count_per_source": len(CONFIRMATION_BLOCKS),
            "status": "confirmation_pass" if passed else TERMINAL_FINITE_FAIL,
        }
    return {
        "screen_outcomes": screen_outcomes,
        "screen_eligible": [outcome for outcome in eligible_outcomes],
        "top_ranked_packet_ids": top_ranked_packet_ids,
        "selected_packet_id": selected_packet_id,
        "confirmation": confirmation,
    }


def _m3_confirmation_expected_keys(packet_id: str | None) -> list[tuple[str, str, str, int]]:
    """Return the frozen global order for one confirmation packet.

    ``_run_one_packet_window`` visits sources in ``SOURCE_ORDER`` and then
    visits that source's block indices in ascending order.  Keeping the
    registration contract as an explicit tuple sequence makes a persisted
    JSONL prefix independently auditable: a missing middle row, duplicate, or
    source/block permutation cannot be mistaken for a legal early stop.
    """
    if packet_id is None:
        return []
    return [
        (str(packet_id), "confirmation", str(source), int(block_index))
        for source in SOURCE_ORDER
        for block_index in CONFIRMATION_BLOCKS
    ]


def _m3_confirmation_stop_analysis(
    records: Sequence[Mapping[str, Any]], selected_packet_id: str | None, *,
    screen_runtime_seconds: float = 0.0,
    resource_limit_seconds: float = RESOURCE_LIMIT_SECONDS,
) -> tuple[str, dict[str, Any] | None]:
    """Infer confirmation terminal and an auditable early-stop proof.

    The analysis mirrors the actual execution order in
    ``_run_one_packet_window``: implementation is checked first, then the
    scientific impossible-threshold condition, then the resource boundary.
    A non-complete confirmation is valid only when one of those conditions is
    reached at the final persisted row (or before the first row for a global
    resource/implementation stop).  A complete successful window has no
    early-stop proof and returns ``TERMINAL_PASS``.
    """
    confirmation_rows = [row for row in records if row.get("stage") == "confirmation"]
    expected = _m3_confirmation_expected_keys(selected_packet_id)
    prefix_count = len(confirmation_rows)
    proof_base = {
        "schema": "nbldpc_v30r_m3_early_stop_v1",
        "stage": "confirmation",
        "packet_id": None if selected_packet_id is None else str(selected_packet_id),
        "prefix_count": int(prefix_count),
        "expected_count": int(len(expected)),
    }

    if selected_packet_id is None:
        # No unique screen top-1 means confirmation must not be registered.
        return TERMINAL_FINITE_FAIL, None

    screen_meter = float(screen_runtime_seconds)
    if not confirmation_rows:
        if screen_meter >= float(resource_limit_seconds):
            proof = dict(proof_base)
            proof.update({
                "terminal": TERMINAL_RESOURCE, "reason": "resource_before_first",
                "source": SOURCE_ORDER[0], "block_index": int(CONFIRMATION_BLOCKS[0]),
            })
            return TERMINAL_RESOURCE, proof
        proof = dict(proof_base)
        proof.update({
            "terminal": TERMINAL_IMPL, "reason": "implementation_before_first",
            "source": SOURCE_ORDER[0], "block_index": int(CONFIRMATION_BLOCKS[0]),
        })
        return TERMINAL_IMPL, proof

    actual_keys: list[tuple[str, str, str, int]] = []
    for row in confirmation_rows:
        try:
            actual_keys.append((
                str(row.get("packet_id")), "confirmation", str(row.get("source")),
                int(row.get("block_index")),
            ))
        except (TypeError, ValueError):
            return TERMINAL_FINITE_FAIL, dict(proof_base, terminal=TERMINAL_FINITE_FAIL,
                                              reason="invalid_registration")

    # A malformed order is never a legal early-stop prefix.  The caller adds
    # a dedicated registration problem; the finite result is only a safe
    # recomputation fallback for terminal comparison.
    if actual_keys != expected[:prefix_count]:
        return TERMINAL_FINITE_FAIL, dict(proof_base, terminal=TERMINAL_FINITE_FAIL,
                                          reason="invalid_registration")

    stats = {
        source: {"completed": 0, "offline_exact": 0, "tag_verified": 0, "false_accept": 0}
        for source in SOURCE_ORDER
    }
    meter = screen_meter
    for index, row in enumerate(confirmation_rows):
        source = str(row.get("source"))
        if source not in stats:
            return TERMINAL_FINITE_FAIL, dict(proof_base, terminal=TERMINAL_FINITE_FAIL,
                                              reason="invalid_registration")
        source_stats = stats[source]
        source_stats["completed"] += 1
        source_stats["offline_exact"] += int(bool(row.get("offline_exact")))
        source_stats["tag_verified"] += int(bool(row.get("tag_verified")))
        source_stats["false_accept"] += int(bool(row.get("false_accept")))

        # The production runner persists an implementation row before it
        # returns.  It therefore has precedence over scientific/resource
        # outcomes for the same persisted call.
        if (row.get("l1_status") == TERMINAL_IMPL or row.get("l2_status") == TERMINAL_IMPL or
                isinstance(row.get("error"), str) and bool(row.get("error"))):
            proof = dict(proof_base)
            proof.update({
                "terminal": TERMINAL_IMPL, "reason": "implementation_row",
                "source": source, "block_index": int(row.get("block_index")),
            })
            return TERMINAL_IMPL, proof

        remaining = len(CONFIRMATION_BLOCKS) - source_stats["completed"]
        impossible = (
            source_stats["false_accept"] > 0 or
            source_stats["offline_exact"] + remaining < 45 or
            source_stats["tag_verified"] + remaining < 45
        )
        if impossible:
            proof = dict(proof_base)
            proof.update({
                "terminal": TERMINAL_FINITE_FAIL, "reason": "impossible_threshold",
                "source": source, "block_index": int(row.get("block_index")),
            })
            return TERMINAL_FINITE_FAIL, proof

        runtime = row.get("runtime_s", 0.0)
        if isinstance(runtime, bool) or not isinstance(runtime, (int, float)) or not math.isfinite(float(runtime)) or float(runtime) < 0:
            return TERMINAL_IMPL, dict(proof_base, terminal=TERMINAL_IMPL,
                                       reason="invalid_runtime", source=source,
                                       block_index=int(row.get("block_index")))
        meter += float(runtime)
        if index + 1 < len(expected) and meter >= float(resource_limit_seconds):
            proof = dict(proof_base)
            proof.update({
                "terminal": TERMINAL_RESOURCE, "reason": "resource_before_next",
                "source": source, "block_index": int(row.get("block_index")),
            })
            return TERMINAL_RESOURCE, proof

    if prefix_count < len(expected):
        # A strict prefix without an actual stop condition is tampering or an
        # incomplete implementation record; neither is accepted as finite
        # science.  The registration validator reports the specific problem.
        proof = dict(proof_base)
        proof.update({
            "terminal": TERMINAL_IMPL, "reason": "unproven_incomplete_prefix",
            "source": str(confirmation_rows[-1].get("source")),
            "block_index": int(confirmation_rows[-1].get("block_index")),
        })
        return TERMINAL_IMPL, proof

    # A full 150-row confirmation reaches PASS exactly when all source
    # thresholds hold.  Any failed threshold would already have been caught
    # at its earliest impossible row above.
    return TERMINAL_PASS, None


def _m3_record_registration_problems(
    packets: Sequence[Mapping[str, Any]], records: Sequence[Mapping[str, Any]],
    selection: Mapping[str, Any], *, terminal: str | None = None,
    resource_meter_seconds: float = 0.0,
    resource_limit_seconds: float = RESOURCE_LIMIT_SECONDS,
) -> list[str]:
    """Check uniqueness and frozen screen/confirmation block registration."""
    problems: list[str] = []
    packet_ids = {str(packet.get("packet_id", packet.get("matrix_id"))) for packet in packets}
    seen: set[tuple[str, str, str, int]] = set()
    grouped: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for row in records:
        packet_id = str(row.get("packet_id"))
        stage = row.get("stage")
        source = row.get("source")
        block_index = row.get("block_index")
        if packet_id not in packet_ids or stage not in {"screen", "confirmation"} or source not in SOURCE_ORDER:
            problems.append("m3_unregistered_record")
            continue
        if isinstance(block_index, bool) or not isinstance(block_index, int):
            problems.append("m3_block_index_type")
            continue
        key = (packet_id, str(stage), str(source), int(block_index))
        if key in seen:
            problems.append("m3_duplicate_record")
        seen.add(key)
        grouped[(packet_id, str(stage), str(source))].append(int(block_index))
    for (packet_id, stage, source), indices in grouped.items():
        ordered = sorted(indices)
        if stage == "screen":
            expected_prefix = list(range(0, len(ordered)))
        else:
            expected_prefix = list(range(20, 20 + len(ordered)))
        if ordered != expected_prefix:
            problems.append(f"m3_noncontiguous_registration:{packet_id}:{stage}:{source}")
    # A completed screen outcome is an exact 20-block/source registration;
    # incomplete matrix-local/resource windows remain prefix-checked above.
    for outcome in selection.get("screen_outcomes", []):
        if outcome.get("status") == "screen_pass":
            packet_id = str(outcome.get("packet_id"))
            for source in SOURCE_ORDER:
                indices = sorted(grouped.get((packet_id, "screen", source), []))
                if indices != list(SCREEN_BLOCKS):
                    problems.append(f"m3_screen_registered_set:{packet_id}:{source}")

    # Confirmation is allowed only for the unique screen top-1.  Its JSONL
    # rows must be a prefix of the one global source-major sequence; checking
    # each source independently would incorrectly accept missing-middle rows
    # and source permutations.
    top_ranked = [str(value) for value in selection.get("top_ranked_packet_ids", [])]
    selected_packet_id = selection.get("selected_packet_id")
    selected_packet_id = None if selected_packet_id is None else str(selected_packet_id)
    confirmation_rows = [row for row in records if row.get("stage") == "confirmation"]
    expected_confirmation = _m3_confirmation_expected_keys(selected_packet_id)
    actual_confirmation: list[tuple[str, str, str, int]] = []
    for row in confirmation_rows:
        try:
            actual_confirmation.append((
                str(row.get("packet_id")), "confirmation", str(row.get("source")),
                int(row.get("block_index")),
            ))
        except (TypeError, ValueError):
            # The generic field/type checks above retain the precise error;
            # this marker prevents an invalid row from being treated as a
            # valid prefix below.
            actual_confirmation.append(("<invalid>", "confirmation", "<invalid>", -1))
            problems.append("m3_confirmation_key_type")
    confirmation_positions = [index for index, row in enumerate(records) if row.get("stage") == "confirmation"]
    if confirmation_positions:
        first_confirmation = min(confirmation_positions)
        if any(row.get("stage") == "screen" for row in records[first_confirmation + 1:]):
            problems.append("m3_confirmation_before_screen_complete")
        if len(top_ranked) != 1 or selected_packet_id != top_ranked[0]:
            problems.append("m3_confirmation_without_unique_top1")
        if any(key[0] != selected_packet_id for key in actual_confirmation):
            problems.append("m3_confirmation_packet_not_selected")
        if actual_confirmation != expected_confirmation[:len(actual_confirmation)]:
            problems.append("m3_confirmation_global_order")
        if len(actual_confirmation) != len(set(actual_confirmation)):
            problems.append("m3_confirmation_duplicate_key")
    elif terminal == TERMINAL_PASS:
        problems.append("m3_confirmation_missing_for_pass")

    # A PASS is a complete 3 x 50 confirmation window, not merely a passing
    # subset.  For non-PASS terminals, the analysis below accepts only a
    # legal prefix whose final row proves finite impossibility, resource
    # exhaustion, or implementation stop.
    if terminal == TERMINAL_PASS and actual_confirmation != expected_confirmation:
        problems.append("m3_pass_confirmation_registered_set")
    if selected_packet_id is not None and (confirmation_rows or terminal in {
        TERMINAL_PASS, TERMINAL_RESOURCE, TERMINAL_FINITE_FAIL, TERMINAL_IMPL,
    }):
        screen_runtime = sum(
            float(row.get("runtime_s", 0.0)) for row in records if row.get("stage") == "screen"
            and isinstance(row.get("runtime_s", 0.0), (int, float))
            and not isinstance(row.get("runtime_s", 0.0), bool)
        )
        inferred_terminal, proof = _m3_confirmation_stop_analysis(
            records, selected_packet_id, screen_runtime_seconds=screen_runtime,
            resource_limit_seconds=resource_limit_seconds,
        )
        if terminal is not None and inferred_terminal != terminal:
            problems.append("m3_confirmation_early_stop_terminal")
        if terminal != TERMINAL_PASS and len(actual_confirmation) < len(expected_confirmation):
            if proof is None:
                problems.append("m3_confirmation_early_stop_proof_missing")
            else:
                # A proof object is not sufficient by itself: a contiguous
                # short prefix with no observed stop condition is an
                # incomplete implementation, not a legal finite result.
                legal_reasons = {
                    "resource_before_first", "resource_before_next",
                    "implementation_before_first", "implementation_row",
                    "impossible_threshold",
                }
                if (proof.get("terminal") != terminal or
                        proof.get("reason") not in legal_reasons):
                    problems.append("m3_confirmation_early_stop_proof_invalid")
    return problems


def _has_implementation_record(rows: Sequence[Mapping[str, Any]]) -> bool:
    return any(
        row.get("terminal") == TERMINAL_IMPL or
        row.get("l1_status") == TERMINAL_IMPL or
        row.get("l2_status") == TERMINAL_IMPL or
        bool(row.get("error"))
        for row in rows
    )


def _recompute_m1_terminals(
    screen: Mapping[str, Any], confirmation: Mapping[str, Any],
    expected_eligible: Sequence[str], selected: Sequence[str],
    *, resource_limit_seconds: float,
) -> tuple[str | None, str, str]:
    """Derive M1 stage terminals from call records, not persisted terminal fields."""
    screen_calls = list(screen.get("calls", []))
    screen_meter = float(screen.get("resource_meter_seconds", 0.0))
    if _has_implementation_record(screen_calls):
        screen_terminal: str | None = TERMINAL_IMPL
    elif len(screen_calls) < 72:
        screen_terminal = TERMINAL_RESOURCE if screen_meter >= resource_limit_seconds else TERMINAL_IMPL
    elif screen_meter >= resource_limit_seconds and expected_eligible:
        screen_terminal = TERMINAL_RESOURCE
    else:
        screen_terminal = None

    if screen_terminal in {TERMINAL_RESOURCE, TERMINAL_IMPL}:
        return screen_terminal, screen_terminal, screen_terminal

    confirmation_calls = list(confirmation.get("calls", []))
    confirmation_meter = float(confirmation.get("resource_meter_seconds", 0.0))
    if _has_implementation_record(confirmation_calls):
        confirmation_terminal = TERMINAL_IMPL
    elif not selected:
        confirmation_terminal = TERMINAL_DE_FAIL
    elif len(confirmation_calls) < 30 * len(selected):
        confirmation_terminal = (
            TERMINAL_RESOURCE if confirmation_meter >= resource_limit_seconds else TERMINAL_IMPL
        )
    else:
        confirmed = [allocation_id for allocation_id in selected
                     if sum(row.get("allocation_id") == allocation_id for row in confirmation_calls) == 30 and
                     all(_is_de_pass(row) for row in confirmation_calls
                         if row.get("allocation_id") == allocation_id)]
        confirmation_terminal = "de_allocation_pass" if confirmed else TERMINAL_DE_FAIL
    return screen_terminal, confirmation_terminal, confirmation_terminal


def _recompute_m3_terminal(
    packets: Sequence[Mapping[str, Any]], records: Sequence[Mapping[str, Any]],
    *, resource_meter_seconds: float, resource_limit_seconds: float,
) -> tuple[str, dict[str, Any]]:
    """Derive M3 terminal and selection from JSONL records only."""
    selection = _m3_recompute_selection(packets, records)
    if not packets:
        return TERMINAL_FINITE_FAIL, selection
    if _has_implementation_record(records):
        return TERMINAL_IMPL, selection
    if len(selection["screen_outcomes"]) < len(packets):
        if resource_meter_seconds >= resource_limit_seconds:
            return TERMINAL_RESOURCE, selection
        return TERMINAL_IMPL, selection
    if len(selection["top_ranked_packet_ids"]) != 1:
        return TERMINAL_FINITE_FAIL, selection
    screen_runtime = sum(
        float(row.get("runtime_s", 0.0)) for row in records if row.get("stage") == "screen"
        and isinstance(row.get("runtime_s", 0.0), (int, float))
        and not isinstance(row.get("runtime_s", 0.0), bool)
    )
    inferred_terminal, _proof = _m3_confirmation_stop_analysis(
        records, str(selection["selected_packet_id"]),
        screen_runtime_seconds=screen_runtime,
        resource_limit_seconds=resource_limit_seconds,
    )
    return inferred_terminal, selection


def _run_one_packet_window(
    packet: Mapping[str, Any], blocks: Sequence[Mapping[str, Any]], *,
    block_indices: Sequence[int], threshold: int, max_iter: int,
    decoder_runner: Any, adapters: Mapping[str, Any], resource_meter: float,
    resource_limit_seconds: float, stage: str, records: list[dict[str, Any]],
) -> tuple[dict[str, Any], float, str | None]:
    """Run one packet window, persisting each record before a gate decision."""
    source_stats: dict[str, dict[str, int]] = {
        label: {"completed": 0, "offline_exact": 0, "tag_verified": 0, "false_accept": 0}
        for label in SOURCE_ORDER
    }
    terminal: str | None = None
    for label in SOURCE_ORDER:
        selected = _source_blocks(blocks, label, block_indices)
        if len(selected) != len(block_indices):
            return source_stats, resource_meter, TERMINAL_IMPL
        for block in selected:
            if resource_meter >= float(resource_limit_seconds):
                return source_stats, resource_meter, TERMINAL_RESOURCE
            try:
                block_public, public, truth = _block_public_and_syndromes(block, packet)
                started = time.monotonic()
                result = _invoke_decoder(decoder_runner, block_public, public, adapters.get(label), packet,
                                         {"max_iter": max_iter, "streak": 20})
                elapsed = time.monotonic() - started
                record = _finite_block_record(block, public, result, truth, packet, elapsed)
                runtime = float(record["runtime_s"])
                if not math.isfinite(runtime) or runtime < 0:
                    raise ValueError("decoder runtime_s must be finite and nonnegative")
                resource_meter += runtime
                record["stage"] = stage
            except Exception as exc:
                record = {
                    "schema": "nbldpc_v30r_block_result_v1", "packet_id": packet.get("packet_id"),
                    "source": label, "block_index": int(block.get("block_index", -1)),
                    "frame_ids": list(block.get("frame_ids", [])), "l1_ok": False,
                    "l1_status": TERMINAL_IMPL, "l2_ok": False, "l2_status": "not_run",
                    "l2_conditioning": "not_run", "l2_not_run_due_l1": True,
                    "offline_exact": False, "tag_verified": False, "false_accept": False,
                    "decoder_calls": 0, "runtime_s": time.monotonic() - started,
                    "stage": stage,
                    "error": f"{type(exc).__name__}: {exc}",
                }
                resource_meter += float(record["runtime_s"])
                terminal = TERMINAL_IMPL
            records.append(record)  # persist before threshold/resource ordering
            stats = source_stats[label]
            stats["completed"] += 1
            stats["offline_exact"] += int(bool(record.get("offline_exact")))
            stats["tag_verified"] += int(bool(record.get("tag_verified")))
            stats["false_accept"] += int(bool(record.get("false_accept")))
            remaining = len(block_indices) - stats["completed"]
            if terminal == TERMINAL_IMPL:
                return source_stats, resource_meter, terminal
            # Matrix-local/global scientific decisions happen before resource.
            if stats["false_accept"] > 0 or stats["offline_exact"] + remaining < threshold or stats["tag_verified"] + remaining < threshold:
                return source_stats, resource_meter, "matrix_local_fail" if stage == "screen" else TERMINAL_FINITE_FAIL
            all_done = all(source_stats[item]["completed"] == len(block_indices) for item in SOURCE_ORDER)
            if not all_done and resource_meter >= float(resource_limit_seconds):
                return source_stats, resource_meter, TERMINAL_RESOURCE
    return source_stats, resource_meter, None


def run_m3_gate(
    packets: Sequence[Mapping[str, Any]], blocks: Sequence[Mapping[str, Any]], *,
    decoder_runner: Any = None, adapters: Mapping[str, Any] | None = None,
    resource_limit_seconds: float = RESOURCE_LIMIT_SECONDS,
) -> dict[str, Any]:
    """Run fixed V30R finite screen/confirmation windows over in-memory blocks."""
    packets = list(packets)
    if len(packets) > 4:
        raise ValueError("V30R packet cap is four")
    adapters = dict(adapters or {})
    if decoder_runner is None and not adapters:
        adapters = load_v26_adapters_once()
    records: list[dict[str, Any]] = []
    screen_outcomes: list[dict[str, Any]] = []
    screen_eligible: list[dict[str, Any]] = []
    meter = 0.0
    terminal: str | None = None
    for packet_index, packet in enumerate(packets):
        stats, meter, status = _run_one_packet_window(
            packet, blocks, block_indices=SCREEN_BLOCKS, threshold=15,
            max_iter=SCREEN_MAX_ITER, decoder_runner=decoder_runner,
            adapters=adapters, resource_meter=meter, resource_limit_seconds=resource_limit_seconds,
            stage="screen", records=records,
        )
        outcome = {
            "packet_id": packet.get("packet_id", packet.get("matrix_id")),
            "matrix_id": packet.get("matrix_id"), "family": packet.get("family"),
            "source_stats": stats, "rank_tuple": list(_packet_screen_rank(packet, stats)),
            "eligible": status is None,
            "status": "screen_pass" if status is None else status,
        }
        screen_outcomes.append(outcome)
        if status is None:
            screen_eligible.append({
                "packet": packet, "packet_id": outcome["packet_id"],
                "matrix_id": outcome["matrix_id"], "family": outcome["family"],
                "source_stats": stats, "rank_tuple": list(_packet_screen_rank(packet, stats)),
                "eligible": True, "status": "screen_pass",
            })
        elif status in {TERMINAL_RESOURCE, TERMINAL_IMPL}:
            terminal = status
            break
        # matrix_local_fail intentionally removes only this matrix and lets
        # other registered packets continue.
        if meter >= float(resource_limit_seconds) and status == "matrix_local_fail" and packet_index < len(packets) - 1:
            terminal = TERMINAL_RESOURCE
            break
    confirmation: dict[str, Any] | None = None
    selected_packet_id = None
    top_ranked_packet_ids: list[str] = []
    if terminal is None:
        if not screen_eligible:
            terminal = TERMINAL_FINITE_FAIL
        else:
            screen_eligible.sort(key=lambda item: tuple(item["rank_tuple"]))
            best_rank = tuple(screen_eligible[0]["rank_tuple"])
            top_ranked_packet_ids = [str(item["packet"].get("packet_id", item["packet"].get("matrix_id")))
                                     for item in screen_eligible if tuple(item["rank_tuple"]) == best_rank]
            if len(top_ranked_packet_ids) != 1:
                terminal = TERMINAL_FINITE_FAIL
            else:
                selected = screen_eligible[0]
                selected_packet_id = selected["packet"].get("packet_id", selected["packet"].get("matrix_id"))
                stats, meter, status = _run_one_packet_window(
                    selected["packet"], blocks, block_indices=CONFIRMATION_BLOCKS, threshold=45,
                    max_iter=CONFIRMATION_MAX_ITER, decoder_runner=decoder_runner,
                    adapters=adapters, resource_meter=meter, resource_limit_seconds=resource_limit_seconds,
                    stage="confirmation", records=records,
                )
                confirmation = {
                    "packet_id": selected_packet_id, "source_stats": stats,
                    "threshold": 45, "block_count_per_source": len(CONFIRMATION_BLOCKS),
                    "status": "confirmation_pass" if status is None else status,
                }
                if status is None:
                    terminal = TERMINAL_PASS
                elif status == TERMINAL_RESOURCE:
                    terminal = TERMINAL_RESOURCE
                elif status == TERMINAL_IMPL:
                    terminal = TERMINAL_IMPL
                else:
                    terminal = TERMINAL_FINITE_FAIL
    def summarize(stage_name: str | None = None) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        for label in SOURCE_ORDER:
            rows = [row for row in records if row.get("source") == label and
                    (stage_name is None or row.get("stage") == stage_name)]
            summary[label] = {
                "record_count": len(rows),
                "offline_exact": sum(int(row.get("offline_exact", False)) for row in rows),
                "tag_verified": sum(int(row.get("tag_verified", False)) for row in rows),
                "false_accept": sum(int(row.get("false_accept", False)) for row in rows),
                "stage_scoped": stage_name is not None,
            }
        return summary
    source_summary = summarize()
    screen_runtime = sum(
        float(row.get("runtime_s", 0.0)) for row in records if row.get("stage") == "screen"
        and isinstance(row.get("runtime_s", 0.0), (int, float))
        and not isinstance(row.get("runtime_s", 0.0), bool)
    )
    _early_stop_terminal, early_stop_proof = _m3_confirmation_stop_analysis(
        records, None if selected_packet_id is None else str(selected_packet_id),
        screen_runtime_seconds=screen_runtime,
        resource_limit_seconds=resource_limit_seconds,
    )
    return {
        "schema": "nbldpc_v30r_finite_gate_v1", "status": terminal or TERMINAL_IMPL,
        "screen_outcomes": screen_outcomes,
        "screen_eligible": [{key: value for key, value in item.items() if key != "packet"} for item in screen_eligible],
        "selected_packet_id": selected_packet_id, "top_ranked_packet_ids": top_ranked_packet_ids,
        "confirmation": confirmation,
        "records": records, "record_count": len(records),
        "resource_meter_seconds": meter, "resource_limit_seconds": float(resource_limit_seconds),
        "source_summary": source_summary,
        "screen_source_summary": summarize("screen"),
        "confirmation_source_summary": summarize("confirmation"),
        "early_stop_proof": early_stop_proof,
        "no_fallback_confirmation": True,
        "screen_block_window": [0, 19], "confirmation_block_window": [20, 69],
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(json_safe(value), indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def _matrix_audit_records(construction: Mapping[str, Any]) -> list[dict[str, Any]]:
    records = []
    for packet in construction.get("packets", []):
        records.append({
            "packet_id": packet.get("packet_id", packet.get("matrix_id")),
            "matrix_id": packet.get("matrix_id"), "allocation_id": packet.get("allocation_id"),
            "family": packet.get("family"), "m1": packet.get("m1"),
            "m2_by_source": packet.get("m2_by_source"), "construction_ok": packet.get("construction_ok"),
            "field": packet.get("field"),
            "four_cycle_components": packet.get("four_cycle_components"),
            "four_cycle_count": packet.get("four_cycle_count"),
            "projective_hard_gate": packet.get("projective_hard_gate"),
            "full_row_rank": packet.get("full_row_rank"), "audits": packet.get("audits"),
        })
    return records


def _matrix_payload_records(construction: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Persist deterministic finite matrices for independent replay."""
    return [{
        "packet_id": packet.get("packet_id", packet.get("matrix_id")),
        "matrix_id": packet.get("matrix_id"), "allocation_id": packet.get("allocation_id"),
        "family": packet.get("family"), "m1": packet.get("m1"),
        "m2_by_source": packet.get("m2_by_source"), "q": Q, "n": N,
        "matrices": json_safe(packet.get("matrices", {})),
    } for packet in construction.get("packets", [])]


def _manifest_for_run(config: Mapping[str, Any], m0: Mapping[str, Any], screen: Mapping[str, Any],
                      confirmation: Mapping[str, Any], construction: Mapping[str, Any], m3: Mapping[str, Any] | None,
                      status: str, m1_registry: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": "nbldpc_v30r_run_manifest_v1", "run_role": "v30r_projective_safe_finite_graph_gate",
        "frozen_config": config, "source_order": list(SOURCE_ORDER),
        "source_mappings": {label: {"source_id": SOURCE_IDS[label], "delay_used_ps": SOURCE_DELAY_PS[label]} for label in SOURCE_ORDER},
        "v25_holdout_used": False, "v29_holdout_used": False, "raw_ttbin_used": False,
        "scientific_input_paths": {
            "v25_channel_counts": str(_resolved_repo_path(V25_CHANNEL_COUNTS)),
            "validation_pairs_parquet": {
                label: str(_resolved_repo_path(path)) for label, path in SOURCE_PARQUETS.items()
            },
        },
        "scientific_input_bindings": {
            "v25_channel_counts": V25_CHANNEL_COUNTS,
            "validation_pairs_parquet": dict(SOURCE_PARQUETS),
        },
        "m1_registry": json_safe(m1_registry),
        "evidence_files": ["RUN_MANIFEST.json", "projective_column_audit.json", "de_allocation_screen.json",
                           "de_allocation_confirmation.json", "matrix_audits.json", "frame_selection.json",
                           "matrix_payloads.json", "m1_registry.json", "validation_frame_selection.json",
                           "validation_block_results.jsonl", "validation_summary.json",
                           "block_manifest.json", "per_block_results.jsonl", "source_summary.json", "gate.json", "readonly_verify.json"],
        "m0_status": m0.get("ok"), "screen_calls": screen.get("n_calls"),
        "confirmation_calls": confirmation.get("n_calls"), "packet_count": len(construction.get("packets", [])),
        "terminal_state": status, "de_rerun": False, "decoder_rerun": False,
        "scientific_inputs_read": [],
    }


def run_v30r_gate(
    output_root: str | Path, *, de_runner: Any = None, decoder_runner: Any = None,
    adapters: Mapping[str, Any] | None = None, blocks: Sequence[Mapping[str, Any]] | None = None,
    resource_limit_seconds: float = RESOURCE_LIMIT_SECONDS,
) -> dict[str, Any]:
    """Execute one V30R packet; injected runners/blocks are test-only seams."""
    root = Path(output_root)
    if root.exists():
        raise FileExistsError(f"V30R output root must be new: {root}")
    root.mkdir(parents=True, exist_ok=False)
    config = frozen_v30r_config(n=N)
    h_values = load_bound_h_values()
    allocations = build_allocation_plan(h_values=h_values)
    if adapters is None and (de_runner is None or decoder_runner is None):
        adapters = load_v26_adapters_once()
    m0 = run_m0_baseline()
    screen = run_m1_screen(allocations, de_runner=de_runner, adapters=adapters,
                           resource_limit_seconds=resource_limit_seconds)
    confirmation = run_m1_confirmation(screen, allocations, de_runner=de_runner, adapters=adapters,
                                        resource_limit_seconds=resource_limit_seconds,
                                        initial_resource_meter_seconds=screen.get("resource_meter_seconds", 0.0))
    registry = _m1_registry(allocations, screen, confirmation)
    # M2 is not entered after any global M1 terminal.  In particular, a
    # confirmation resource/implementation/failure terminal must not be
    # turned into a partial matrix construction attempt.
    if (screen.get("terminal") in {TERMINAL_RESOURCE, TERMINAL_IMPL} or
            confirmation.get("terminal") != "de_allocation_pass"):
        construction = {
            "schema": "nbldpc_v30r_matrix_construction_v1", "packets": [],
            "rejected": [], "packet_cap": 4, "packet_cap_ok": True,
        }
    else:
        construction = build_confirmed_packets(confirmation, allocations)
    validation_docs = validation_frame_manifest()
    if blocks is None:
        if construction.get("packets"):
            blocks = load_validation_blocks()
        else:
            blocks = []
    else:
        # Even injected test blocks must obey the frozen public validation
        # identity; only the private in-memory M3 helper may bypass this.
        _validate_validation_blocks(blocks)
    if construction.get("packets") and confirmation.get("terminal") == "de_allocation_pass":
        m3 = run_m3_gate(construction["packets"], blocks, decoder_runner=decoder_runner,
                         adapters=adapters, resource_limit_seconds=resource_limit_seconds)
    else:
        m3 = {"schema": "nbldpc_v30r_finite_gate_v1", "status": TERMINAL_FINITE_FAIL,
              "records": [], "record_count": 0, "screen_outcomes": [], "screen_eligible": [],
              "selected_packet_id": None, "top_ranked_packet_ids": [], "confirmation": None,
              "resource_meter_seconds": 0.0, "source_summary": {}, "early_stop_proof": None,
              "no_fallback_confirmation": True, "screen_block_window": [0, 19], "confirmation_block_window": [20, 69]}
    if screen.get("terminal") in {TERMINAL_RESOURCE, TERMINAL_IMPL}:
        status = screen["terminal"]
    elif confirmation.get("terminal") in {TERMINAL_RESOURCE, TERMINAL_IMPL, TERMINAL_DE_FAIL}:
        status = confirmation["terminal"]
    elif not construction.get("packets"):
        status = TERMINAL_FINITE_FAIL
    else:
        status = m3.get("status", TERMINAL_IMPL)
    manifest = _manifest_for_run(config, m0, screen, confirmation, construction, m3, status, registry)
    _write_json(root / "RUN_MANIFEST.json", manifest)
    _write_json(root / "projective_column_audit.json", {
        "schema": "nbldpc_v30r_projective_audit_bundle_v1",
        "baseline": m0,
        "candidate_audits": _matrix_audit_records(construction),
    })
    _write_json(root / "de_allocation_screen.json", screen)
    _write_json(root / "de_allocation_confirmation.json", confirmation)
    _write_json(root / "m1_registry.json", registry)
    _write_json(root / "matrix_audits.json", {"schema": "nbldpc_v30r_matrix_audits_v1",
                                               "packets": _matrix_audit_records(construction),
                                               "rejected": construction.get("rejected", []),
                                               "packet_cap": 4})
    _write_json(root / "matrix_payloads.json", {
        "schema": "nbldpc_v30r_matrix_payloads_v1",
        "packets": _matrix_payload_records(construction),
    })
    _write_json(root / "frame_selection.json", validation_docs["frame_selection"])
    _write_json(root / "validation_frame_selection.json", validation_docs["frame_selection"])
    _write_json(root / "block_manifest.json", validation_docs["block_manifest"])
    with (root / "validation_block_results.jsonl").open("w", encoding="utf-8") as formal_stream, \
            (root / "per_block_results.jsonl").open("w", encoding="utf-8") as legacy_stream:
        for record in m3.get("records", []):
            line = json.dumps(json_safe(record), sort_keys=True, allow_nan=False) + "\n"
            formal_stream.write(line)
            legacy_stream.write(line)
    # Keep legacy aliases additive while the formal design filenames are the
    # verifier's source of truth.
    formal_summary = {
        "all": m3.get("source_summary", {}),
        "screen": m3.get("screen_source_summary", {}),
        "confirmation": m3.get("confirmation_source_summary", {}),
        "early_stop_proof": m3.get("early_stop_proof"),
        "selection": {
            "screen_outcomes": m3.get("screen_outcomes", []),
            "screen_eligible": m3.get("screen_eligible", []),
            "top_ranked_packet_ids": m3.get("top_ranked_packet_ids", []),
            "selected_packet_id": m3.get("selected_packet_id"),
            "confirmation": m3.get("confirmation"),
            "no_fallback_confirmation": m3.get("no_fallback_confirmation") is True,
        },
    }
    _write_json(root / "validation_summary.json", formal_summary)
    _write_json(root / "source_summary.json", formal_summary)
    gate = {
        "schema": "nbldpc_v30r_gate_v1", "status": status,
        # Confirmation carries the cumulative M1 meter (including screen).
        # When it made no calls, retain the screen meter as the authoritative
        # value for a screen-terminal or pre-confirmation stop.
        "m1_de_resource_meter_seconds": (
            confirmation.get("resource_meter_seconds", screen.get("resource_meter_seconds", 0.0))
            if int(confirmation.get("n_calls", 0)) > 0
            else screen.get("resource_meter_seconds", 0.0)
        ),
        "m3_decoder_resource_meter_seconds": m3.get("resource_meter_seconds", 0.0),
        "resource_limit_seconds": float(resource_limit_seconds),
        "terminal_precedence": "persist_current; scientific_stage_decision; resource; implementation",
        "m1_terminal": screen.get("terminal"), "confirmation_terminal": confirmation.get("terminal"),
        "m3_terminal": m3.get("status"), "packet_count": len(construction.get("packets", [])),
        "m3_record_count": m3.get("record_count", 0),
        "m3_screen_outcomes": m3.get("screen_outcomes", []),
        "m3_screen_eligible": m3.get("screen_eligible", []),
        "m3_top_ranked_packet_ids": m3.get("top_ranked_packet_ids", []),
        "m3_selected_packet_id": m3.get("selected_packet_id"),
        "m3_confirmation": m3.get("confirmation"),
        "m3_early_stop_proof": m3.get("early_stop_proof"),
        "m1_selected_allocations": screen.get("selected_allocations", []),
        "m1_confirmed_allocations": confirmation.get("confirmed_allocations", []),
        "no_fallback_confirmation": True, "de_rerun": False, "decoder_rerun": False,
    }
    _write_json(root / "gate.json", gate)
    verification = verify_v30r(root)
    _write_json(root / "readonly_verify.json", verification)
    return {"status": status, "evidence_root": str(root), "gate": gate, "readonly_verify": verification}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_v30r(run_root: str | Path) -> dict[str, Any]:
    """Read-only structural verifier; it never invokes DE or a decoder."""
    root = Path(run_root)
    required = ["RUN_MANIFEST.json", "projective_column_audit.json", "de_allocation_screen.json",
                "de_allocation_confirmation.json", "m1_registry.json", "matrix_audits.json", "matrix_payloads.json",
                "validation_frame_selection.json", "validation_block_results.jsonl", "validation_summary.json",
                "block_manifest.json", "gate.json"]
    problems: list[str] = []
    missing = [name for name in required if not (root / name).exists()]
    problems.extend(f"missing:{name}" for name in missing)
    if missing:
        return {"schema": "nbldpc_v30r_readonly_verify_v1", "ok": False,
                "problems": problems, "no_de_rerun": True, "no_decoder_rerun": True,
                "verifier_rerun_flags": {"de": False, "decoder": False}}
    try:
        manifest = _read_json(root / "RUN_MANIFEST.json")
        m0_bundle = _read_json(root / "projective_column_audit.json")
        m0 = m0_bundle.get("baseline", m0_bundle)
        screen = _read_json(root / "de_allocation_screen.json")
        confirmation = _read_json(root / "de_allocation_confirmation.json")
        registry = _read_json(root / "m1_registry.json")
        matrices = _read_json(root / "matrix_audits.json")
        payloads = _read_json(root / "matrix_payloads.json")
        frame = _read_json(root / "validation_frame_selection.json")
        blocks = _read_json(root / "block_manifest.json")
        source_summary = _read_json(root / "validation_summary.json")
        gate = _read_json(root / "gate.json")
    except (OSError, ValueError, TypeError) as exc:
        return {"schema": "nbldpc_v30r_readonly_verify_v1", "ok": False,
                "problems": [f"read:{type(exc).__name__}:{exc}"], "no_de_rerun": True,
                "no_decoder_rerun": True, "verifier_rerun_flags": {"de": False, "decoder": False}}
    if manifest.get("schema") != "nbldpc_v30r_run_manifest_v1":
        problems.append("manifest_schema")
    rebuilt_m0 = run_m0_baseline()
    if not m0.get("ok") or not rebuilt_m0.get("ok"):
        problems.append("m0_not_ok")
    if m0.get("expected_l1_counts") != rebuilt_m0.get("expected_l1_counts") or m0.get("reproduced") != rebuilt_m0.get("reproduced"):
        problems.append("m0_rebuild_mismatch")
    if m0_bundle.get("candidate_audits") != matrices.get("packets", []):
        problems.append("e02_candidate_audit_bundle_mismatch")
    frozen = manifest.get("frozen_config", {})
    if frozen.get("q") != Q or frozen.get("n") != N or frozen.get("factorization") != "F03_natural_MSB_to_LSB_GF32_plus_GF32":
        problems.append("frozen_architecture")
    field_meta = frozen.get("field", {})
    if (field_meta.get("constructor") != "GF2mField.create(32)" or
            field_meta.get("primitive_polynomial") != PRIMITIVE_POLYNOMIAL or
            field_meta.get("field_id") != FIELD_ID or
            field_meta.get("ratio_order") != RATIO_ORDER):
        problems.append("field_binding")
    if (manifest.get("v25_holdout_used") is not False or
            manifest.get("v29_holdout_used") is not False or
            manifest.get("raw_ttbin_used") is not False):
        problems.append("forbidden_input")
    expected_input_paths = {
        "v25_channel_counts": str(_resolved_repo_path(V25_CHANNEL_COUNTS)),
        "validation_pairs_parquet": {
            label: str(_resolved_repo_path(path)) for label, path in SOURCE_PARQUETS.items()
        },
    }
    if manifest.get("scientific_input_paths") != expected_input_paths:
        problems.append("scientific_input_paths")
    if manifest.get("scientific_input_bindings") != {
        "v25_channel_counts": V25_CHANNEL_COUNTS,
        "validation_pairs_parquet": dict(SOURCE_PARQUETS),
    }:
        problems.append("scientific_input_bindings")
    if manifest.get("m1_registry") != registry:
        problems.append("manifest_registry_copy")
    try:
        expected_allocations = build_allocation_plan(h_values=load_bound_h_values())
        expected_registry = _m1_registry(expected_allocations, screen, confirmation)
        if registry != expected_registry:
            problems.append("m1_registry_rebuild")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        expected_allocations = []
        expected_registry = {}
        problems.append(f"m1_registry_error:{type(exc).__name__}:{exc}")
    expected_source_mapping = {
        label: {"source_id": SOURCE_IDS[label], "delay_used_ps": SOURCE_DELAY_PS[label]}
        for label in SOURCE_ORDER
    }
    if manifest.get("source_mappings") != expected_source_mapping:
        problems.append("source_mapping")
    expected_allocation_ids = [str(allocation["allocation_id"]) for allocation in expected_allocations]
    if registry.get("allocation_order") != expected_allocation_ids:
        problems.append("m1_allocation_order")
    screen_registry = registry.get("screen", {}) if isinstance(registry, Mapping) else {}
    expected_screen_items = list(_screen_items(expected_allocations)) if expected_allocations else []
    if (screen_registry.get("seed_order") != list(SCREEN_SEEDS) or
            screen_registry.get("n_samples") != SCREEN_N_SAMPLES or
            screen_registry.get("max_iter") != SCREEN_MAX_ITER or
            screen_registry.get("calls_per_allocation") != 12 or
            screen_registry.get("expected_calls") != 72 or
            screen_registry.get("registered_call_order") != json_safe(expected_screen_items)):
        problems.append("m1_screen_registry")
    calls = screen.get("calls", [])
    if screen.get("n_calls") != len(calls):
        problems.append("screen_call_count_field")
    if screen.get("registered_plan_calls") != 72:
        problems.append("screen_registered_plan")
    if screen.get("terminal") is None and len(calls) != 72:
        problems.append("screen_not_72")
    descriptor_keys = ("allocation_id", "m1", "m2", "source", "source_id", "delay_used_ps",
                       "layer", "seed", "rate", "f", "H_bits_per_symbol", "n_samples", "max_iter")
    for index, row in enumerate(calls):
        if index >= len(expected_screen_items):
            problems.append("screen_unregistered_call")
            break
        expected_item = expected_screen_items[index]
        if row.get("call_index") != index or any(row.get(key) != expected_item.get(key) for key in descriptor_keys):
            problems.append(f"screen_registry_call:{index}")
    expected_screen_counts = {
        allocation_id: sum(row.get("allocation_id") == allocation_id for row in calls)
        for allocation_id in expected_allocation_ids
    }
    if screen.get("allocation_call_counts") != expected_screen_counts:
        problems.append("screen_allocation_counts_recompute")
    for allocation_id, count in expected_screen_counts.items():
        if count not in (0, 12):
            problems.append(f"screen_allocation_count:{allocation_id}")
    call_eligibility: dict[str, bool] = {}
    for allocation_id, count in expected_screen_counts.items():
        own = [row for row in calls if row.get("allocation_id") == allocation_id]
        call_eligibility[allocation_id] = count == 12 and len(own) == 12 and all(_is_de_pass(row) for row in own)
        for row in own:
            label = row.get("source")
            if label not in SOURCE_ORDER or row.get("source_id") != SOURCE_IDS.get(label) or row.get("delay_used_ps") != SOURCE_DELAY_PS.get(label):
                problems.append(f"screen_source_binding:{allocation_id}")
            if row.get("layer") not in {"L1", "L2"}:
                problems.append(f"screen_layer:{allocation_id}")
    expected_eligible = [allocation_id for allocation_id, ok in call_eligibility.items() if ok]
    if screen.get("eligible_allocations") != expected_eligible:
        problems.append("screen_eligibility_recompute")
    rank_items = []
    allocation_rank_tuples = screen.get("rank_tuples", {})
    for allocation_id in expected_eligible:
        own = [row for row in calls if row.get("allocation_id") == allocation_id]
        entropy = [math.inf if row.get("final_entropy_bits") is None else float(row.get("final_entropy_bits")) for row in own]
        rank_items.append((max(entropy), sum(entropy) / len(entropy), int(allocation_id.split("_")[-1]), allocation_id))
        expected_tuple = [max(entropy), sum(entropy) / len(entropy), int(allocation_id.split("_")[-1])]
        actual_tuple = allocation_rank_tuples.get(allocation_id)
        if actual_tuple is None or any(abs(float(actual_tuple[index]) - expected_tuple[index]) > 1e-12 for index in range(3)):
            problems.append(f"screen_rank:{allocation_id}")
    expected_selected = [item[3] for item in sorted(rank_items)[:2]]
    selected = list(screen.get("selected_allocations", []))
    if (len(selected) > 2 or any(item not in expected_eligible for item in selected) or
            (len(calls) == 72 and selected != expected_selected)):
        problems.append("screen_selection")
    if screen_registry.get("selected_allocations") != selected:
        problems.append("m1_registry_screen_selection")
    confirmation_registry = registry.get("confirmation", {}) if isinstance(registry, Mapping) else {}
    expected_confirmation_items: list[dict[str, Any]] = []
    allocation_by_id = {str(allocation["allocation_id"]): allocation for allocation in expected_allocations}
    for allocation_id in selected:
        if allocation_id in allocation_by_id:
            expected_confirmation_items.extend(_confirmation_items(allocation_by_id[allocation_id]))
    if (confirmation_registry.get("seed_order") != list(CONFIRMATION_SEEDS) or
            confirmation_registry.get("n_samples") != CONFIRMATION_N_SAMPLES or
            confirmation_registry.get("max_iter") != CONFIRMATION_MAX_ITER or
            confirmation_registry.get("calls_per_allocation") != 30 or
            confirmation_registry.get("expected_max_calls") != 60 or
            confirmation_registry.get("selected_allocations") != selected or
            confirmation_registry.get("registered_call_order") != json_safe(expected_confirmation_items)):
        problems.append("m1_confirmation_registry")
    confirm_calls = confirmation.get("calls", [])
    if confirmation.get("n_calls") != len(confirm_calls) or len(confirm_calls) > 60:
        problems.append("confirmation_count")
    problems.extend(_validate_de_call_rows(calls, "screen"))
    problems.extend(_validate_de_call_rows(confirm_calls, "confirmation"))
    if confirmation.get("selected_allocations") != selected:
        problems.append("confirmation_selected_ids")
    for index, row in enumerate(confirm_calls):
        if index >= len(expected_confirmation_items):
            problems.append("confirmation_unregistered_call")
            break
        expected_item = expected_confirmation_items[index]
        if row.get("call_index") != index or any(row.get(key) != expected_item.get(key) for key in descriptor_keys):
            problems.append(f"confirmation_registry_call:{index}")
    expected_confirmation_counts = {
        allocation_id: sum(row.get("allocation_id") == allocation_id for row in confirm_calls)
        for allocation_id in selected
    }
    if confirmation.get("allocation_call_counts") != expected_confirmation_counts:
        problems.append("confirmation_allocation_counts_recompute")
    for allocation_id in confirmation.get("selected_allocations", []):
        count = confirmation.get("allocation_call_counts", {}).get(allocation_id, 0)
        if confirmation.get("terminal") not in {TERMINAL_RESOURCE, TERMINAL_IMPL} and count != 30:
            problems.append(f"confirmation_allocation_count:{allocation_id}")
        own = [row for row in confirm_calls if row.get("allocation_id") == allocation_id]
        if count == 30 and not all(_is_de_pass(row) for row in own) and confirmation.get("allocation_confirmed", {}).get(allocation_id) is True:
            problems.append(f"confirmation_pass_tamper:{allocation_id}")
    confirmed_recomputed = [allocation_id for allocation_id in confirmation.get("selected_allocations", [])
                            if confirmation.get("allocation_call_counts", {}).get(allocation_id) == 30 and
                            all(_is_de_pass(row) for row in confirm_calls if row.get("allocation_id") == allocation_id)]
    if confirmation.get("terminal") not in {TERMINAL_RESOURCE, TERMINAL_IMPL} and confirmation.get("confirmed_allocations") != confirmed_recomputed:
        problems.append("confirmation_selection_recompute")
    packets = matrices.get("packets", [])
    rejected_packets = matrices.get("rejected", [])
    payload_packet_list = payloads.get("packets", []) if isinstance(payloads, Mapping) else []
    rebuilt_packets: dict[str, dict[str, Any]] = {}
    if len(packets) > 4:
        problems.append("packet_cap")
    expected_packet_specs = {
        (str(allocation_id), family)
        for allocation_id in confirmed_recomputed
        for family in SUPPORTED_FAMILIES
    }
    observed_specs: list[tuple[str, str]] = []
    for packet in packets:
        observed_specs.append((str(packet.get("allocation_id")), str(packet.get("family"))))
    for rejected in rejected_packets:
        observed_specs.append((str(rejected.get("allocation_id")), str(rejected.get("family"))))
        if rejected.get("terminal") != TERMINAL_FINITE_FAIL or not isinstance(rejected.get("error"), str):
            problems.append("rejected_packet_record")
    if len(observed_specs) != len(set(observed_specs)):
        problems.append("packet_spec_duplicate")
    if set(observed_specs) != expected_packet_specs:
        problems.append("confirmed_packet_completeness")
    for packet in packets:
        if (str(packet.get("allocation_id")), str(packet.get("family"))) not in expected_packet_specs:
            problems.append(f"unregistered_packet:{packet.get('packet_id')}")
    if len(payload_packet_list) != len(packets):
        problems.append("matrix_payload_count")
    for audit_record, payload_record in zip(packets, payload_packet_list):
        try:
            if audit_record.get("packet_id") != payload_record.get("packet_id"):
                problems.append("matrix_payload_id")
            expected_packet = build_matrix_packet(
                int(payload_record["m1"]), payload_record["m2_by_source"],
                family=str(payload_record["family"]), n=N,
                allocation_id=str(payload_record["allocation_id"]),
            )
            expected_matrices = json_safe(expected_packet["matrices"])
            rebuilt_packets[str(payload_record["packet_id"])] = expected_packet
            if payload_record.get("matrices") != expected_matrices:
                problems.append(f"matrix_deterministic_rebuild:{payload_record.get('packet_id')}")
            for layer_name in ("L1", "L2"):
                expected_audit = expected_packet["audits"][layer_name]
                persisted_audit = audit_record.get("audits", {}).get(layer_name, {})
                if persisted_audit != json_safe(expected_audit):
                    problems.append(f"matrix_audit_full_rebuild:{payload_record.get('packet_id')}:{layer_name}")
                for key in ("shape", "rank", "full_row_rank", "projective_hard_gate",
                            "tanner6_newly_closed_total", "tanner6_degenerate_total",
                            "tanner6_degenerate_max_per_column"):
                    if persisted_audit.get(key) != expected_audit.get(key):
                        problems.append(f"matrix_audit_rebuild:{payload_record.get('packet_id')}:{layer_name}:{key}")
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            problems.append(f"matrix_rebuild_error:{type(exc).__name__}:{exc}")
    if manifest.get("packet_count") != len(packets):
        problems.append("manifest_packet_count")
    for packet in packets:
        if not packet.get("projective_hard_gate") or not packet.get("full_row_rank"):
            problems.append(f"matrix_hard_gate:{packet.get('packet_id')}")
        field = packet.get("field", {})
        if field.get("constructor") != "GF2mField.create(32)" or field.get("primitive_polynomial") != PRIMITIVE_POLYNOMIAL or field.get("field_id") != FIELD_ID:
            problems.append(f"matrix_field:{packet.get('packet_id')}")
        components = packet.get("four_cycle_components", {}) or {}
        if packet.get("four_cycle_count") != sum(int(value) for value in components.values()):
            problems.append(f"four_cycle_total:{packet.get('packet_id')}")
        audit_bundle = packet.get("audits", {}) or {}
        audit_items: list[tuple[str, Mapping[str, Any]]] = []
        l1_audit = audit_bundle.get("L1") if isinstance(audit_bundle, Mapping) else None
        if isinstance(l1_audit, Mapping):
            audit_items.append(("L1", l1_audit))
        else:
            problems.append(f"matrix_audit_shape:{packet.get('packet_id')}:L1")
        l2_audits = audit_bundle.get("L2") if isinstance(audit_bundle, Mapping) else None
        if not isinstance(l2_audits, Mapping):
            problems.append(f"matrix_audit_shape:{packet.get('packet_id')}:L2")
            l2_audits = {}
        for source in SOURCE_ORDER:
            source_audit = l2_audits.get(source)
            if isinstance(source_audit, Mapping):
                audit_items.append((f"L2:{source}", source_audit))
            else:
                problems.append(f"matrix_audit_shape:{packet.get('packet_id')}:L2:{source}")
        for layer_name, audit in audit_items:
            if audit.get("tanner8_rule") != "topology_only":
                problems.append(f"tanner8_rule:{packet.get('packet_id')}:{layer_name}")
            projective = audit.get("projective", {}) or {}
            columns = projective.get("columns", [])
            keys: dict[tuple[int, int, int], list[int]] = defaultdict(list)
            for column in columns:
                if column.get("valid") is not True:
                    problems.append(f"invalid_column:{packet.get('packet_id')}:{layer_name}")
                    continue
                key = tuple(int(value) for value in column.get("projective_key", []))
                if len(key) != 3:
                    problems.append(f"projective_key:{packet.get('packet_id')}:{layer_name}")
                keys[key].append(int(column.get("column", -1)))
            duplicate = [value for value in keys.values() if len(value) > 1]
            if len(duplicate) != int(projective.get("duplicate_projective_classes", -1)):
                problems.append(f"duplicate_recompute:{packet.get('packet_id')}:{layer_name}")
            if sum(len(value) for value in duplicate) != int(projective.get("affected_columns", -1)):
                problems.append(f"affected_recompute:{packet.get('packet_id')}:{layer_name}")
            replay = audit.get("label_replay", [])
            if int(audit.get("tanner6_newly_closed_total", -1)) != sum(int(row.get("newly_closed_tanner6", 0)) for row in replay):
                problems.append(f"tanner6_new_total:{packet.get('packet_id')}:{layer_name}")
            if int(audit.get("tanner6_degenerate_total", -1)) != sum(int(row.get("selected_score", [0, 0])[0]) for row in replay):
                problems.append(f"tanner6_degenerate_total:{packet.get('packet_id')}:{layer_name}")
            if replay and int(audit.get("tanner6_degenerate_max_per_column", -1)) != max(int(row.get("selected_score", [0, 0])[0]) for row in replay):
                problems.append(f"tanner6_degenerate_max:{packet.get('packet_id')}:{layer_name}")
            for row in replay:
                if int(row.get("selected_score", [0, -1])[1]) != int(row.get("selected_ratio_index", -2)):
                    problems.append(f"ratio_replay:{packet.get('packet_id')}:{layer_name}")
    if frame.get("schema") != "nbldpc_v30r_frame_selection_v1" or set(frame.get("sources", {})) != set(SOURCE_ORDER):
        problems.append("frame_manifest_sources")
    else:
        for label in SOURCE_ORDER:
            info = frame["sources"][label]
            start, end = SOURCE_FRAME_RANGES[label]
            if (info.get("frame_start") != start or info.get("frame_end") != end or
                    info.get("block_count") != 100 or info.get("pairs_parquet") != SOURCE_PARQUETS[label]):
                problems.append(f"frame_range:{label}")
    if blocks.get("schema") != "nbldpc_v30r_block_manifest_v1" or blocks.get("block_count") != 300:
        problems.append("block_manifest_300")
    persisted_status = gate.get("status")
    allowed = {TERMINAL_PASS, TERMINAL_FINITE_FAIL, TERMINAL_DE_FAIL, TERMINAL_RESOURCE, TERMINAL_IMPL}
    if persisted_status not in allowed:
        problems.append("terminal_state")
    if gate.get("no_fallback_confirmation") is not True:
        problems.append("fallback_flag")
    if gate.get("de_rerun") is not False or gate.get("decoder_rerun") is not False:
        problems.append("gate_rerun_flag")
    expected_m1_meter = (
        confirmation.get("resource_meter_seconds", screen.get("resource_meter_seconds", 0.0))
        if int(confirmation.get("n_calls", 0)) > 0
        else screen.get("resource_meter_seconds", 0.0)
    )
    actual_m1_meter = gate.get("m1_de_resource_meter_seconds")
    if (isinstance(actual_m1_meter, bool) or not isinstance(actual_m1_meter, (int, float)) or
            not math.isfinite(float(actual_m1_meter)) or
            abs(float(actual_m1_meter) - float(expected_m1_meter)) > 1e-12):
        problems.append("m1_resource_meter_recompute")
    jsonl_records: list[dict[str, Any]] = []
    try:
        jsonl_records = [json.loads(line) for line in (root / "validation_block_results.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        jsonl_count = len(jsonl_records)
        if int(gate.get("m3_record_count", -1)) != jsonl_count:
            problems.append("block_record_count")
        for row in jsonl_records:
            label = row.get("source")
            packet_id = str(row.get("packet_id"))
            packet = rebuilt_packets.get(packet_id)
            if label not in SOURCE_ORDER or packet is None:
                problems.append("block_packet_or_source")
                continue
            if row.get("source_id") != SOURCE_IDS[label] or row.get("delay_used_ps") != SOURCE_DELAY_PS[label]:
                problems.append("block_source_binding")
            index = int(row.get("block_index", -1))
            stage = row.get("stage")
            if stage == "screen" and not 0 <= index < 20:
                problems.append("screen_block_window")
            if stage == "confirmation" and not 20 <= index < 70:
                problems.append("confirmation_block_window")
            start = SOURCE_FRAME_RANGES[label][0] + index * BLOCK_FRAMES
            expected_frames = list(range(start, start + BLOCK_FRAMES))
            if row.get("frame_ids") != expected_frames:
                problems.append("block_frame_ids")
            truth1 = row.get("truth_x1")
            truth2 = row.get("truth_x2")
            decoded1 = row.get("decoded_x1")
            decoded2 = row.get("decoded_x2")
            if truth1 is not None and truth2 is not None:
                exact = (decoded1 is not None and decoded2 is not None and decoded1 == truth1 and decoded2 == truth2)
                true_tag = v29_tag64(truth1, truth2)
                decoded_tag = None if decoded1 is None or decoded2 is None else v29_tag64(decoded1, decoded2)
                if row.get("offline_exact") != exact or row.get("tag_verified") != bool(decoded_tag == true_tag):
                    problems.append("block_exact_tag_recompute")
                if row.get("false_accept") != bool(decoded_tag == true_tag and not exact):
                    problems.append("block_false_accept_recompute")
                h1 = packet["matrices"]["L1"]
                h2 = packet["matrices"]["L2"][label]
                expected_s1 = v28.compute_syndrome(FIELD, h1, truth1)
                expected_s2 = v28.compute_syndrome(FIELD, h2, truth2)
                if row.get("l1_syndrome_target") != expected_s1 or row.get("l2_syndrome_target") != expected_s2:
                    problems.append("block_syndrome_target")
                actual_s1 = None if decoded1 is None else v28.compute_syndrome(FIELD, h1, decoded1)
                actual_s2 = None if decoded2 is None else v28.compute_syndrome(FIELD, h2, decoded2)
                if row.get("l1_syndrome") != actual_s1 or row.get("l2_syndrome") != actual_s2:
                    problems.append("block_syndrome_recompute")
    except (OSError, ValueError, TypeError):
        problems.append("block_record_read")
    screen_terminal_recomputed, confirmation_terminal_recomputed, m1_terminal_recomputed = _recompute_m1_terminals(
        screen, confirmation, expected_eligible, selected,
        resource_limit_seconds=float(screen.get("resource_limit_seconds", RESOURCE_LIMIT_SECONDS)),
    )
    m3_terminal_recomputed, m3_selection_recomputed = _recompute_m3_terminal(
        list(rebuilt_packets.values()), jsonl_records,
        resource_meter_seconds=float(gate.get("m3_decoder_resource_meter_seconds", 0.0)),
        resource_limit_seconds=float(gate.get("resource_limit_seconds", RESOURCE_LIMIT_SECONDS)),
    )
    m3_screen_runtime = sum(
        float(row.get("runtime_s", 0.0)) for row in jsonl_records if row.get("stage") == "screen"
        and isinstance(row.get("runtime_s", 0.0), (int, float))
        and not isinstance(row.get("runtime_s", 0.0), bool)
    )
    problems.extend(_m3_record_registration_problems(
        list(rebuilt_packets.values()), jsonl_records, m3_selection_recomputed,
        # Use the persisted gate terminal for the proof comparison.  The
        # recomputed terminal is checked independently below; this catches a
        # persisted PASS/FAIL label that is inconsistent with the legal
        # confirmation prefix before the final terminal comparison.
        terminal=persisted_status,
        resource_meter_seconds=float(gate.get("m3_decoder_resource_meter_seconds", 0.0)),
        resource_limit_seconds=float(gate.get("resource_limit_seconds", RESOURCE_LIMIT_SECONDS)),
    ))
    _proof_terminal, expected_m3_early_stop_proof = _m3_confirmation_stop_analysis(
        jsonl_records, m3_selection_recomputed.get("selected_packet_id"),
        screen_runtime_seconds=m3_screen_runtime,
        resource_limit_seconds=float(gate.get("resource_limit_seconds", RESOURCE_LIMIT_SECONDS)),
    )
    if gate.get("m3_early_stop_proof") != expected_m3_early_stop_proof:
        problems.append("m3_early_stop_proof_recompute")
    if screen.get("terminal") != screen_terminal_recomputed:
        problems.append("screen_terminal_recompute")
    if confirmation.get("terminal") != confirmation_terminal_recomputed:
        problems.append("confirmation_terminal_recompute")
    if gate.get("m1_terminal") != screen_terminal_recomputed:
        problems.append("gate_m1_terminal_recompute")
    if gate.get("confirmation_terminal") != confirmation_terminal_recomputed:
        problems.append("gate_confirmation_terminal_recompute")
    if gate.get("m3_terminal") != m3_terminal_recomputed:
        problems.append("gate_m3_terminal_recompute")
    if screen_terminal_recomputed in {TERMINAL_RESOURCE, TERMINAL_IMPL}:
        recomputed_status = screen_terminal_recomputed
    elif confirmation_terminal_recomputed in {TERMINAL_RESOURCE, TERMINAL_IMPL, TERMINAL_DE_FAIL}:
        recomputed_status = confirmation_terminal_recomputed
    elif confirmation_terminal_recomputed != "de_allocation_pass":
        recomputed_status = TERMINAL_DE_FAIL
    elif not packets:
        recomputed_status = TERMINAL_FINITE_FAIL
    else:
        recomputed_status = m3_terminal_recomputed
    if persisted_status != recomputed_status:
        problems.append("terminal_recompute")
    if gate.get("m3_screen_outcomes") != m3_selection_recomputed.get("screen_outcomes", []):
        problems.append("m3_screen_outcomes_recompute")
    if gate.get("m3_screen_eligible") != m3_selection_recomputed.get("screen_eligible", []):
        problems.append("m3_screen_eligible_recompute")
    if gate.get("m3_top_ranked_packet_ids") != m3_selection_recomputed.get("top_ranked_packet_ids", []):
        problems.append("m3_top_rank_recompute")
    if gate.get("m3_selected_packet_id") != m3_selection_recomputed.get("selected_packet_id"):
        problems.append("m3_selected_packet_recompute")
    if gate.get("m3_confirmation") != m3_selection_recomputed.get("confirmation"):
        problems.append("m3_confirmation_recompute")
    summary_selection = source_summary.get("selection", {}) if isinstance(source_summary, Mapping) else {}
    if (summary_selection.get("screen_outcomes") != m3_selection_recomputed.get("screen_outcomes", []) or
            summary_selection.get("screen_eligible") != m3_selection_recomputed.get("screen_eligible", []) or
            summary_selection.get("top_ranked_packet_ids") != m3_selection_recomputed.get("top_ranked_packet_ids", []) or
            summary_selection.get("selected_packet_id") != m3_selection_recomputed.get("selected_packet_id") or
            summary_selection.get("confirmation") != m3_selection_recomputed.get("confirmation")):
        problems.append("source_summary_selection_recompute")
    if source_summary.get("early_stop_proof") != expected_m3_early_stop_proof:
        problems.append("source_summary_early_stop_proof_recompute")
    return {
        "schema": "nbldpc_v30r_readonly_verify_v1", "ok": not problems,
        "problems": problems, "recomputed_terminal": recomputed_status,
        "persisted_terminal": persisted_status,
        "recomputed_m1_terminal": m1_terminal_recomputed,
        "recomputed_m3_terminal": m3_terminal_recomputed,
        "screen_call_count": len(calls), "confirmation_call_count": len(confirm_calls),
        "packet_count": len(packets), "no_de_rerun": True, "no_decoder_rerun": True,
        "verifier_rerun_flags": {"de": False, "decoder": False},
    }
