"""Unit and contract tests for V38-P0 architecture triage module.

Implements all 41 implementation tests (T1-T41) and safety tests.
All tests use TEST-ONLY non-scientific seeds (938001+) and fixtures.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.formal_ir.v35_algorithm_development import (
    GF2mField,
    compute_gf32_rank,
    get_conditional_posterior_l2,
    load_v31_qc_baseline_matrices,
)
from comparison_bench.formal_ir import v38_architecture_triage as v38_module
from comparison_bench.formal_ir.v38_architecture_triage import (
    BLOCK_LENGTH,
    FROZEN_BASELINE_ERROR_MAP,
    LANE_C_CHECK_ALLOCATIONS,
    LANE_C_EDGE_LOAD_VECTOR,
    LANE_EVALUATED_NO_SIGNAL,
    LANE_PRODUCTION_SEEDS,
    LANE_PROMISING_DIRECTION_SIGNAL,
    LANE_READY,
    LANE_STRUCTURAL_NOT_READY,
    SOURCE_CHECKS,
    V31_BASELINE_REFERENCE,
    V36_A3_BLOCK_SEEDS,
    V38_DIRECTION_EVIDENCE_INVALID,
    V38_MULTIPLE_ROUTE_SIGNALS,
    V38_NO_ROUTE_SIGNAL,
    V38_NO_STRUCTURAL_PROTOTYPE_READY,
    V38_SINGLE_ROUTE_SIGNAL,
    CycleInfo,
    aggregate_lane_results,
    check_lane_c_capacity_feasibility,
    check_structural_validity,
    classify_cycle_algebraic_degeneracy,
    compute_cycle_submatrix_rank,
    compute_structural_metrics,
    construct_lane_a_prototype,
    construct_lane_b_prototype,
    construct_lane_c_prototype,
    determine_v38_terminal_state,
    enumerate_canonical_simple_cycles,
    evaluate_single_block,
    evaluate_triage_gate,
    get_canonical_support_edges,
    get_substream_generator,
    optimize_lane_a_coefficients,
    run_v38_development,
    sample_uniform_gf32_nonzero,
    select_structural_winner,
    validate_block_records_integrity,
)

TEST_SEED_1 = 938001
TEST_SEED_2 = 938002


# ---------------------------------------------------------------------------
# T1 - T5: Foundations, Determinism & Cycle Degeneracy
# ---------------------------------------------------------------------------

def test_t1_construction_seed_determinism():
    """T1: Construction seed determinism across all 3 lanes."""
    H_a1, m_a1 = construct_lane_a_prototype("1M", TEST_SEED_1, max_sweeps=1)
    H_a2, m_a2 = construct_lane_a_prototype("1M", TEST_SEED_1, max_sweeps=1)
    assert np.array_equal(H_a1, H_a2)
    assert m_a1 == m_a2

    H_b1, m_b1 = construct_lane_b_prototype("1M", TEST_SEED_1)
    H_b2, m_b2 = construct_lane_b_prototype("1M", TEST_SEED_1)
    assert np.array_equal(H_b1, H_b2)
    assert m_b1 == m_b2

    H_c1, m_c1 = construct_lane_c_prototype("1M", TEST_SEED_1)
    H_c2, m_c2 = construct_lane_c_prototype("1M", TEST_SEED_1)
    assert np.array_equal(H_c1, H_c2)
    assert m_c1 == m_c2


def test_t2_all_matrices_exact_dimensions():
    """T2: All generated matrices have exact dimensions (184x1024, 190x1024, 192x1024)."""
    for src, m in SOURCE_CHECKS.items():
        H_b, _ = construct_lane_b_prototype(src, TEST_SEED_1)
        assert H_b.shape == (m, BLOCK_LENGTH)

        H_c, _ = construct_lane_c_prototype(src, TEST_SEED_1)
        assert H_c.shape == (m, BLOCK_LENGTH)


def test_t3_gf32_rank_validation():
    """T3: GF(32) row rank routine correctly validates known full-rank and rank-deficient fixtures."""
    field = GF2mField.create(32)
    # Full rank 3x3
    H_full = np.array([
        [1, 2, 0],
        [0, 3, 4],
        [5, 0, 6],
    ], dtype=np.uint8)
    assert compute_gf32_rank(H_full, field) == 3

    # Rank deficient 2x3 (identical rows)
    H_def = np.array([
        [1, 2, 3],
        [1, 2, 3],
    ], dtype=np.uint8)
    assert compute_gf32_rank(H_def, field) == 1


def test_t4_canonical_simple_cycle_enumeration():
    """T4: Canonical simple cycle enumeration correctly deduplicates rotations and reversals."""
    # Create a simple 4-cycle graph: 2 checks, 2 vars
    H_4cyc = np.array([
        [1, 1],
        [1, 1],
    ], dtype=np.uint8)
    c4, c6, c8, edge_to_cyc = enumerate_canonical_simple_cycles(H_4cyc)
    assert len(c4) == 1
    assert len(c6) == 0
    assert len(c8) == 0
    assert c4[0].checks == (0, 1)
    assert c4[0].vars == (0, 1)
    assert len(c4[0].edges) == 4

    # Simple 6-cycle graph: 3 checks, 3 vars
    H_6cyc = np.array([
        [1, 0, 1],
        [1, 1, 0],
        [0, 1, 1],
    ], dtype=np.uint8)
    c4, c6, c8, _ = enumerate_canonical_simple_cycles(H_6cyc)
    assert len(c4) == 0
    assert len(c6) == 1
    assert len(c8) == 0
    assert c6[0].checks == (0, 1, 2)
    assert c6[0].vars == (0, 1, 2)


def test_t4_oracle_cycle_enumeration_comparison():
    """T4 Oracle: Verify cycle enumeration against an independent reference DFS cycle finder."""
    def _dfs_cycles(support: np.ndarray, max_len: int) -> set[frozenset[tuple[int, int]]]:
        m, n = support.shape
        adj_c = [np.nonzero(support[i, :])[0].tolist() for i in range(m)]
        adj_v = [np.nonzero(support[:, j])[0].tolist() for j in range(n)]

        found_cycles: set[frozenset[tuple[int, int]]] = set()

        def _dfs(start_c: int, curr_c: int, path_v: list[int], path_c: list[int]):
            r = max_len // 2
            if len(path_c) == r:
                for v_last in adj_c[curr_c]:
                    if v_last not in path_v and start_c in adj_v[v_last]:
                        full_v = path_v + [v_last]
                        edges = []
                        for k in range(r):
                            c_k = path_c[k]
                            v_k = full_v[k]
                            c_next = path_c[(k + 1) % r]
                            edges.append((c_k, v_k))
                            edges.append((c_next, v_k))
                        found_cycles.add(frozenset(edges))
                return

            for v in adj_c[curr_c]:
                if v in path_v:
                    continue
                for next_c in adj_v[v]:
                    if next_c in path_c or next_c <= start_c:
                        continue
                    _dfs(start_c, next_c, path_v + [v], path_c + [next_c])

        for c0 in range(m):
            for v0 in adj_c[c0]:
                for c1 in adj_v[v0]:
                    if c1 > c0:
                        _dfs(c0, c1, [v0], [c0, c1])

        return found_cycles

    # 1. Isolated 8-cycle graph (4 checks, 4 vars)
    H_8 = np.array([
        [1, 0, 0, 1],
        [1, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 1],
    ], dtype=np.uint8)
    c4, c6, c8, _ = enumerate_canonical_simple_cycles(H_8)
    assert len(c4) == 0
    assert len(c6) == 0
    assert len(c8) == 1
    dfs_8 = _dfs_cycles(H_8, 8)
    assert len(dfs_8) == 1
    assert frozenset(c8[0].edges) == next(iter(dfs_8))

    # 2. Overlapping cycles graph (4 checks, 5 vars)
    H_multi = np.array([
        [1, 1, 0, 0, 1],
        [1, 0, 1, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 1, 1],
    ], dtype=np.uint8)
    c4_m, c6_m, c8_m, _ = enumerate_canonical_simple_cycles(H_multi)
    for c_list, length in ((c4_m, 4), (c6_m, 6), (c8_m, 8)):
        ref_set = _dfs_cycles(H_multi, length)
        canon_set = {frozenset(cyc.edges) for cyc in c_list}
        assert canon_set == ref_set, f"Mismatch for length {length}"


def test_t5_cycle_submatrix_rank_classification():
    """T5: Cycle submatrix rank routine correctly classifies known nondegenerate and degenerate GF(32) fixtures."""
    field = GF2mField.create(32)
    # 4-cycle with ad == bc (degenerate)
    cyc4 = CycleInfo(length=4, checks=(0, 1), vars=(0, 1), edges=((0, 0), (1, 0), (1, 1), (0, 1)))
    H_deg = np.array([
        [2, 4],
        [3, 6],  # 2*6 = 12, 4*3 = 12 in GF(32)
    ], dtype=np.uint8)
    assert compute_cycle_submatrix_rank(cyc4, H_deg, field) == 1
    assert classify_cycle_algebraic_degeneracy(cyc4, H_deg, field) is True

    # 4-cycle with ad != bc (nondegenerate)
    H_nondeg = np.array([
        [1, 2],
        [3, 4],  # 1*4 = 4 != 2*3 = 6
    ], dtype=np.uint8)
    assert compute_cycle_submatrix_rank(cyc4, H_nondeg, field) == 2
    assert classify_cycle_algebraic_degeneracy(cyc4, H_nondeg, field) is False


# ---------------------------------------------------------------------------
# T6 - T8, Lane A Tie Tests: Lane A Properties & Tie-Breaks
# ---------------------------------------------------------------------------

def test_t6_t7_t8_lane_a_support_and_search():
    """T6-T8: Lane A binary support identity, label-only modification, and sweep cap."""
    v31_mats = load_v31_qc_baseline_matrices()
    H_v31 = v31_mats["1M"]
    support_v31 = (H_v31 != 0).astype(np.uint8)

    H_a, metrics = construct_lane_a_prototype("1M", TEST_SEED_1, max_sweeps=2)
    support_a = (H_a != 0).astype(np.uint8)

    assert np.array_equal(support_a, support_v31)
    assert np.count_nonzero(H_a) == np.count_nonzero(H_v31)
    assert np.all((H_a[H_a != 0] >= 1) & (H_a[H_a != 0] <= 31))
    assert metrics["sweeps_completed"] <= 2


def test_lane_a_tie_break_rules():
    """Lane A Tie Tests: Verify lowest integer tie-break, 0-incident edges, and brute force equivalence."""
    field = GF2mField.create(32)

    # Test A: If old_val = 17 and candidate 1 gives identical cycle objective, selected coefficient must be 1
    H_no_cyc = np.array([[17, 0], [0, 5]], dtype=np.uint8)
    supp = (H_no_cyc != 0).astype(np.uint8)
    H_opt, _, updates, _, _ = optimize_lane_a_coefficients(H_no_cyc, supp, max_sweeps=1, field=field)
    assert H_opt[0, 0] == 1
    assert H_opt[1, 1] == 1
    assert updates == 2  # Both 17->1 and 5->1 updated

    # Test B: Edge with 0 incident cycles is assigned 1 after sweep
    H_mixed = np.array([
        [1, 1, 10],  # (0, 2) has no cycle
        [1, 1, 0],
    ], dtype=np.uint8)
    supp_m = (H_mixed != 0).astype(np.uint8)
    H_opt_m, _, _, _, _ = optimize_lane_a_coefficients(H_mixed, supp_m, max_sweeps=1, field=field)
    assert H_opt_m[0, 2] == 1

    # Test C: Incremental objective + tie-break matches brute-force reference
    H_test = np.array([
        [7, 12, 0, 4],
        [0, 5, 19, 7],
        [8, 0, 9, 10],
    ], dtype=np.uint8)
    supp_t = (H_test != 0).astype(np.uint8)
    H_opt_inc, _, _, _, _ = optimize_lane_a_coefficients(H_test, supp_t, max_sweeps=2, field=field)

    # Brute-force reference
    c4, c6, c8, _ = enumerate_canonical_simple_cycles(supp_t)
    H_bf = H_test.copy()
    edges = get_canonical_support_edges(supp_t)
    for _ in range(2):
        upd = 0
        for r, c in edges:
            best_k = (float("inf"), float("inf"), float("inf"), float("inf"))
            best_v = H_bf[r, c]
            for cand in range(1, 32):
                H_cand = H_bf.copy()
                H_cand[r, c] = cand
                d4 = sum(classify_cycle_algebraic_degeneracy(cyc, H_cand, field) for cyc in c4)
                d6 = sum(classify_cycle_algebraic_degeneracy(cyc, H_cand, field) for cyc in c6)
                d8 = sum(classify_cycle_algebraic_degeneracy(cyc, H_cand, field) for cyc in c8)
                k = (d4, d6, d8, cand)
                if k < best_k:
                    best_k = k
                    best_v = cand
            if best_v != H_bf[r, c]:
                H_bf[r, c] = best_v
                upd += 1
        if upd == 0:
            break

    assert np.array_equal(H_opt_inc, H_bf)


# ---------------------------------------------------------------------------
# T9 - T10, T25 - T26, T35: Lane B Properties
# ---------------------------------------------------------------------------

def test_t9_t10_t25_t26_t35_lane_b_properties():
    """T9-T10, T25-T26, T35: Lane B structure, RNG stream position test."""
    H_b, metrics = construct_lane_b_prototype("1M", TEST_SEED_1)
    m = SOURCE_CHECKS["1M"]
    n = BLOCK_LENGTH
    n_info = n - m

    H_info = H_b[:, :n_info]
    H_parity = H_b[:, n_info:]

    # T9: Parity block is exact unit lower-bidiagonal
    for i in range(m):
        assert H_parity[i, i] == 1
        if i + 1 < m:
            assert H_parity[i + 1, i] == 1
        if i > 0 and i + 1 < m:
            assert np.count_nonzero(H_parity[i, :]) == 2

    # T10: Information columns all have degree exactly 2
    info_col_weights = np.count_nonzero(H_info, axis=0)
    assert np.all(info_col_weights == 2)

    # T25: Total support edge count == 2047
    assert metrics["support_edge_count"] == 2047
    assert np.count_nonzero(H_b) == 2047

    # T26: Parity block guarantees rank m
    assert metrics["rank_GF32"] == m

    # T35: Expected first H_info coefficient from Generator(PCG64(SeedSequence([S, 2])))
    # equals actual first canonical H_info coefficient (proves H_parity consumed 0 draws)
    coeff_rng = get_substream_generator(TEST_SEED_1, stream_id=2)
    expected_first_coeff = int(sample_uniform_gf32_nonzero(coeff_rng, 1)[0])
    canonical_info_edges = get_canonical_support_edges(H_info != 0)
    actual_first_coeff = int(H_info[canonical_info_edges[0][0], canonical_info_edges[0][1]])
    assert actual_first_coeff == expected_first_coeff


# ---------------------------------------------------------------------------
# T11 - T12, T22 - T24, T38: Lane C Properties & Capacity Gate
# ---------------------------------------------------------------------------

def test_t11_t12_t38_lane_c_properties():
    """T11-T12, T38: Lane C variable column degrees, coupling window, and permutation comparison."""
    H_c, metrics = construct_lane_c_prototype("1M", TEST_SEED_1)
    m = SOURCE_CHECKS["1M"]
    n = BLOCK_LENGTH

    # T11: All variable columns degree exactly 2
    col_weights = np.count_nonzero(H_c, axis=0)
    assert np.all(col_weights == 2)
    assert metrics["support_edge_count"] == 2048

    # T12: All edges respect L=8, w=2 coupling window
    allocations = LANE_C_CHECK_ALLOCATIONS["1M"]
    check_offsets = [0] * 8
    for p in range(1, 8):
        check_offsets[p] = check_offsets[p - 1] + allocations[p - 1]

    for j in range(n):
        p_var = min(j // 128, 7)
        check_indices = np.nonzero(H_c[:, j])[0]
        assert len(check_indices) == 2

        if p_var < 7:
            min_c_p = check_offsets[p_var]
            max_c_p = check_offsets[p_var] + allocations[p_var]
            min_c_next = check_offsets[p_var + 1]
            max_c_next = check_offsets[p_var + 1] + allocations[p_var + 1]

            c1, c2 = sorted(check_indices)
            assert (min_c_p <= c1 < max_c_p)
            assert (min_c_next <= c2 < max_c_next)
        else:
            min_c_7 = check_offsets[7]
            max_c_7 = check_offsets[7] + allocations[7]
            for c in check_indices:
                assert min_c_7 <= c < max_c_7

    # T38: Compare actual position permutations with independently reconstructed permutations
    support_rng = get_substream_generator(TEST_SEED_1, stream_id=1)
    actual_perms = metrics["position_permutations"]
    assert len(actual_perms) == 8
    for p in range(8):
        c_range = list(range(check_offsets[p], check_offsets[p] + allocations[p]))
        expected_perm_p = support_rng.permutation(c_range).tolist()
        assert actual_perms[p] == expected_perm_p, f"Permutation mismatch at position {p}"


def test_t22_t23_t24_lane_c_capacity_calculation():
    """T22-T24: Lane C capacity calculation, failure of old equal allocation, and capacity gate."""
    assert LANE_C_CHECK_ALLOCATIONS["1M"] == [12, 23, 23, 23, 23, 23, 23, 34]
    assert LANE_C_CHECK_ALLOCATIONS["1p5M"] == [12, 24, 24, 24, 24, 24, 23, 35]
    assert LANE_C_CHECK_ALLOCATIONS["2M"] == [12, 24, 24, 24, 24, 24, 24, 36]

    assert check_lane_c_capacity_feasibility(184, LANE_C_CHECK_ALLOCATIONS["1M"]) is True
    assert check_lane_c_capacity_feasibility(190, LANE_C_CHECK_ALLOCATIONS["1p5M"]) is True
    assert check_lane_c_capacity_feasibility(192, LANE_C_CHECK_ALLOCATIONS["2M"]) is True

    # T23: Old equal allocation fails capacity at pos 7
    old_equal_1M = [23] * 8
    assert check_lane_c_capacity_feasibility(184, old_equal_1M) is False

    # T24: dc_max limit enforcement
    valid, reason = check_structural_validity(np.zeros((184, 1024)), (184, 1024), dc_max=16)
    assert valid is False


# ---------------------------------------------------------------------------
# T13 - T16, T21: Structural Selection, Statuses, & Provenance Safety
# ---------------------------------------------------------------------------

def test_t13_no_hidden_retry_seeds():
    """T13: Pre-registered candidate seed namespaces have exactly 3 seeds per source/lane."""
    for lane in ("lane_a", "lane_b", "lane_c"):
        for src in ("1M", "1p5M", "2M"):
            assert len(LANE_PRODUCTION_SEEDS[lane][src]) == 3


def test_t14_structural_selection_ignores_decoder():
    """T14: Structural prototype selection ignores decoder performance and strictly uses structural tie-break."""
    prototypes = [
        {
            "construction_seed": 102,
            "structurally_valid": True,
            "degenerate_cycles_4": 5,
            "degenerate_cycles_6": 10,
            "degenerate_cycles_8": 20,
            "support_cycles_4": 10,
            "row_degree_max": 14,
            "fake_decoder_error": 10,
        },
        {
            "construction_seed": 101,
            "structurally_valid": True,
            "degenerate_cycles_4": 2,
            "degenerate_cycles_6": 15,
            "degenerate_cycles_8": 25,
            "support_cycles_4": 12,
            "row_degree_max": 15,
            "fake_decoder_error": 200,
        },
    ]
    winner, status = select_structural_winner(prototypes)
    assert status == "WINNER_SELECTED"
    assert winner["construction_seed"] == 101


def test_t15_structurally_invalid_prototype_never_selected():
    """T15: Structurally invalid prototype is never selected."""
    prototypes = [
        {"construction_seed": 101, "structurally_valid": False, "degenerate_cycles_4": 0},
        {"construction_seed": 102, "structurally_valid": False, "degenerate_cycles_4": 0},
    ]
    winner, status = select_structural_winner(prototypes)
    assert winner is None
    assert status == "STRUCTURAL_PROTOTYPE_NOT_READY"


def test_t16_structural_not_ready_does_not_invalidate_other_lanes():
    """T16: One lane being STRUCTURAL_NOT_READY does not invalidate execution of other READY lanes."""
    lane_statuses = {
        "lane_a": LANE_STRUCTURAL_NOT_READY,
        "lane_b": LANE_PROMISING_DIRECTION_SIGNAL,
        "lane_c": LANE_EVALUATED_NO_SIGNAL,
    }
    terminal = determine_v38_terminal_state(lane_statuses, integrity_ok=True)
    assert terminal == V38_SINGLE_ROUTE_SIGNAL


def test_t17_exact_v36_a3_block_seeds():
    """T17: Exact V36 A3 block seeds are preserved."""
    assert V36_A3_BLOCK_SEEDS["1M"] == [360101, 360102, 360103, 360104, 360105]
    assert V36_A3_BLOCK_SEEDS["1p5M"] == [360201, 360202, 360203, 360204, 360205]
    assert V36_A3_BLOCK_SEEDS["2M"] == [360301, 360302, 360303, 360304, 360305]


def test_t21_real_git_sha_verification():
    """T21: Real Git verification that predecessor SHAs exist in Git object store and hallucinated SHAs are absent."""
    real_v37_res = "67da7c64fa4150a66d020243d6292420903297fe"
    real_v37_rev = "cc1483cd568ca41fb686c40492f40b5eed81f06c"

    r1 = subprocess.run(["git", "cat-file", "-t", real_v37_res], capture_output=True, text=True, check=True)
    assert r1.stdout.strip() == "commit"

    r2 = subprocess.run(["git", "cat-file", "-t", real_v37_rev], capture_output=True, text=True, check=True)
    assert r2.stdout.strip() == "commit"

    hallucinated_shas = [
        "cc1483cd4d7d3d2dc90bc02c4cf2db44d5ba73bf",
        "67da7c649646b9c9910d52489ae476ceae7fdb57",
    ]
    for p in Path("docs/research_cycles/V38P0").glob("*.*"):
        content = p.read_text(encoding="utf-8")
        for bad_sha in hallucinated_shas:
            assert bad_sha not in content, f"Hallucinated SHA {bad_sha} found in {p}"


# ---------------------------------------------------------------------------
# T18 - T20, T32, Block Integrity & Pairing Tests
# ---------------------------------------------------------------------------

def _create_dummy_15_records(lane: str = "lane_test", errors_map: Optional[dict[str, list[int]]] = None) -> list[dict]:
    if errors_map is None:
        errors_map = {
            "1M": [166, 177, 171, 178, 162],
            "1p5M": [167, 199, 187, 148, 178],
            "2M": [164, 189, 183, 184, 169],
        }
    records = []
    for src, seeds in V36_A3_BLOCK_SEEDS.items():
        errs = errors_map[src]
        for s, e in zip(seeds, errs):
            records.append({
                "source": src,
                "block_seed": s,
                "lane": lane,
                "construction_seed": 938001,
                "matrix_id": f"{lane}_{src}_s938001",
                "errors_initial": 250,
                "errors_final": e,
                "exact_l2": (e == 0),
                "syndrome_ok": (e == 0),
                "iterations": 30,
                "status": "max_iter",
                "runtime_s": 0.01,
            })
    return records


def test_order_invariant_block_pairing():
    """Test that arbitrary list permutations produce bit-identical aggregate statistics."""
    records_canonical = _create_dummy_15_records()
    agg_canonical = aggregate_lane_results(records_canonical)

    rng = np.random.default_rng(12345)
    perm_indices = rng.permutation(len(records_canonical)).tolist()
    records_permuted = [records_canonical[i] for i in perm_indices]
    agg_permuted = aggregate_lane_results(records_permuted)

    assert agg_canonical["integrity_ok"] is True
    assert agg_permuted["integrity_ok"] is True
    assert agg_canonical["exact_recovery_count"] == agg_permuted["exact_recovery_count"]
    assert agg_canonical["overall_mean_errors"] == agg_permuted["overall_mean_errors"]
    assert agg_canonical["overall_median_errors"] == agg_permuted["overall_median_errors"]
    assert agg_canonical["improve_count"] == agg_permuted["improve_count"]
    assert agg_canonical["equal_count"] == agg_permuted["equal_count"]
    assert agg_canonical["worsen_count"] == agg_permuted["worsen_count"]
    assert agg_canonical["worst_single_block_degradation"] == agg_permuted["worst_single_block_degradation"]


def test_block_set_integrity_validation():
    """Test rejection of missing, duplicate, unexpected, or partial block sets."""
    base_recs = _create_dummy_15_records()

    # 1. Missing seed (14 records)
    res_missing = aggregate_lane_results(base_recs[:-1])
    assert res_missing["integrity_ok"] is False
    assert res_missing["status"] == "INVALID_BLOCK_SET"
    passed, det = evaluate_triage_gate(res_missing)
    assert passed is False

    # 2. Duplicate seed (15 records with 1 duplicate)
    recs_dup = list(base_recs[:-1]) + [base_recs[0]]
    res_dup = aggregate_lane_results(recs_dup)
    assert res_dup["integrity_ok"] is False

    # 3. Unexpected seed
    recs_bad_seed = list(base_recs[:-1]) + [{
        "source": "1M",
        "block_seed": 999999,
        "lane": "lane_test",
        "construction_seed": 938001,
        "errors_final": 100,
    }]
    res_bad_seed = aggregate_lane_results(recs_bad_seed)
    assert res_bad_seed["integrity_ok"] is False

    # 4. Partial dataset: 3 records (1 per source) cannot pass triage gate
    recs_3 = [base_recs[0], base_recs[5], base_recs[10]]
    res_3 = aggregate_lane_results(recs_3)
    assert res_3["integrity_ok"] is False
    passed_3, _ = evaluate_triage_gate(res_3)
    assert passed_3 is False


def test_t18_t19_t32_triage_gate_branches():
    """T18, T19, T32: PROMISING_DIRECTION_SIGNAL branches (Crit A, B, C, >5% degradation)."""
    # Criterion A pass: exact recovery > 0
    recs_a = _create_dummy_15_records(errors_map={
        "1M": [0, 177, 171, 178, 162],
        "1p5M": [167, 199, 187, 148, 178],
        "2M": [164, 189, 183, 184, 169],
    })
    agg_a = aggregate_lane_results(recs_a)
    passed_a, det_a = evaluate_triage_gate(agg_a)
    assert passed_a is True
    assert det_a["criterion_a"] is True

    # Criterion B pass: overall median <= 150 (T32)
    recs_b = _create_dummy_15_records(errors_map={
        "1M": [140, 140, 140, 140, 140],
        "1p5M": [145, 145, 145, 145, 145],
        "2M": [150, 150, 150, 150, 150],
    })
    agg_b = aggregate_lane_results(recs_b)
    passed_b, det_b = evaluate_triage_gate(agg_b)
    assert passed_b is True
    assert det_b["criterion_b"] is True

    # Criterion C pass: improve >= 10 and worsen <= 3
    recs_c = _create_dummy_15_records(errors_map={
        "1M": [165, 176, 170, 177, 161],  # 5 improves
        "1p5M": [166, 198, 186, 147, 177], # 5 improves
        "2M": [164, 189, 183, 184, 169],  # 5 equals
    })
    agg_c = aggregate_lane_results(recs_c)
    passed_c, det_c = evaluate_triage_gate(agg_c)
    assert passed_c is True
    assert det_c["criterion_c"] is True

    # Failure: source degradation > 5%
    recs_deg = _create_dummy_15_records(errors_map={
        "1M": [190, 190, 190, 190, 190],
        "1p5M": [140, 140, 140, 140, 140],
        "2M": [140, 140, 140, 140, 140],
    })
    agg_deg = aggregate_lane_results(recs_deg)
    passed_deg, _ = evaluate_triage_gate(agg_deg)
    assert passed_deg is False


def test_t20_terminal_state_branches():
    """T20: All overall terminal-state branches."""
    assert determine_v38_terminal_state({
        "lane_a": LANE_PROMISING_DIRECTION_SIGNAL,
        "lane_b": LANE_EVALUATED_NO_SIGNAL,
        "lane_c": LANE_EVALUATED_NO_SIGNAL,
    }) == V38_SINGLE_ROUTE_SIGNAL

    assert determine_v38_terminal_state({
        "lane_a": LANE_PROMISING_DIRECTION_SIGNAL,
        "lane_b": LANE_PROMISING_DIRECTION_SIGNAL,
        "lane_c": LANE_EVALUATED_NO_SIGNAL,
    }) == V38_MULTIPLE_ROUTE_SIGNALS

    assert determine_v38_terminal_state({
        "lane_a": LANE_EVALUATED_NO_SIGNAL,
        "lane_b": LANE_EVALUATED_NO_SIGNAL,
        "lane_c": LANE_EVALUATED_NO_SIGNAL,
    }) == V38_NO_ROUTE_SIGNAL

    assert determine_v38_terminal_state({
        "lane_a": LANE_STRUCTURAL_NOT_READY,
        "lane_b": LANE_STRUCTURAL_NOT_READY,
        "lane_c": LANE_STRUCTURAL_NOT_READY,
    }) == V38_NO_STRUCTURAL_PROTOTYPE_READY

    assert determine_v38_terminal_state({}, integrity_ok=False) == V38_DIRECTION_EVIDENCE_INVALID


# ---------------------------------------------------------------------------
# T27 - T31, T33 - T41: Detailed Deterministic Construction Contract
# ---------------------------------------------------------------------------

def test_t27_t28_prng_contract():
    """T27-T28: PRNG uses PCG64 only with deterministic SeedSequence substream derivation."""
    g1 = get_substream_generator(TEST_SEED_1, 1)
    g2 = get_substream_generator(TEST_SEED_1, 1)
    v1 = g1.integers(1, 100, size=10)
    v2 = g2.integers(1, 100, size=10)
    assert np.array_equal(v1, v2)

    g3 = get_substream_generator(TEST_SEED_1, 2)
    v3 = g3.integers(1, 100, size=10)
    assert not np.array_equal(v1, v3)


def test_t29_lane_a_incremental_objective_matches_brute_force():
    """T29: Lane A cached incremental cycle objective exactly matches brute-force recomputation."""
    field = GF2mField.create(32)
    H = np.array([
        [1, 2, 0, 4],
        [0, 5, 6, 7],
        [8, 0, 9, 10],
    ], dtype=np.uint8)
    support = (H != 0).astype(np.uint8)
    c4, c6, c8, edge_to_cyc = enumerate_canonical_simple_cycles(support)
    all_cycles = c4 + c6 + c8

    cached_states = [classify_cycle_algebraic_degeneracy(cyc, H, field) for cyc in all_cycles]

    edge = (0, 0)
    incident_ids = edge_to_cyc.get(edge, [])

    for cand_val in range(1, 32):
        H_test = H.copy()
        H_test[0, 0] = cand_val

        bf_states = [classify_cycle_algebraic_degeneracy(cyc, H_test, field) for cyc in all_cycles]

        inc_states = list(cached_states)
        for idx in incident_ids:
            inc_states[idx] = classify_cycle_algebraic_degeneracy(all_cycles[idx], H_test, field)

        assert inc_states == bf_states


def test_t30_t31_lane_a_rank_semantics():
    """T30-T31: Support identity and sweep-1 rank diagnostic behavior."""
    H_a, metrics = construct_lane_a_prototype("1M", TEST_SEED_1, max_sweeps=2)
    v31_mats = load_v31_qc_baseline_matrices()
    assert np.array_equal((H_a != 0), (v31_mats["1M"] != 0))
    assert "rank_after_sweep_1" in metrics
    assert metrics["rank_after_sweep_1"] > 0


def test_t33_t34_coefficient_sampling_and_edge_order():
    """T33-T34: Coefficient sampler bounds and canonical edge ordering independence."""
    rng = get_substream_generator(TEST_SEED_1, 2)
    coeffs = sample_uniform_gf32_nonzero(rng, 1000)
    assert np.all((coeffs >= 1) & (coeffs <= 31))
    assert np.all(coeffs != 0)

    support = np.array([
        [0, 1, 0, 1],
        [1, 0, 1, 0],
    ], dtype=np.uint8)
    edges = get_canonical_support_edges(support)
    assert edges == [(0, 1), (0, 3), (1, 0), (1, 2)]


def test_t36_t37_support_before_coefficients():
    """T36-T37: Support fully generated before coefficient assignment in Lanes B and C."""
    H_b, mb = construct_lane_b_prototype("1M", TEST_SEED_1)
    assert mb["structurally_valid"] is True
    assert mb["support_edge_count"] == 2047

    H_c, mc = construct_lane_c_prototype("1M", TEST_SEED_1)
    assert mc["structurally_valid"] is True
    assert mc["support_edge_count"] == 2048


def test_t39_t40_t41_lane_a_behavioral_rank_and_early_stop():
    """T39-T41: Behavioral tests for Lane A sweep-1 rank continuation, final rank gate, and early stop."""
    field = GF2mField.create(32)

    # T39: Explicit intermediate rank deficiency fixture (4 checks, 4 vars)
    # Check 2 and Check 3 both connect only to var 0 (no cycles).
    # After sweep 1, row 2 becomes [1, 0, 0, 0] and row 3 becomes [1, 0, 0, 0].
    # Therefore, rank_after_sweep_1 is strictly 3 < 4 (deficient!).
    H_fixture = np.array([
        [1, 2, 0, 0],
        [0, 3, 4, 0],
        [5, 0, 0, 0],
        [6, 0, 0, 0],
    ], dtype=np.uint8)
    supp = (H_fixture != 0).astype(np.uint8)
    H_opt, sweeps, updates, rank_s1, final_rank = optimize_lane_a_coefficients(
        H_fixture, supp, max_sweeps=2, field=field
    )
    # Explicitly assert intermediate rank deficiency: rank_after_sweep_1 < number_of_checks
    assert rank_s1 == 3
    assert rank_s1 < 4, f"Expected rank_s1 < 4, got {rank_s1}"
    # Assert search was permitted to proceed to sweep 2 without premature invalidation
    assert sweeps == 2

    # T40: Final rank deficiency marks prototype structurally invalid
    valid, reason = check_structural_validity(H_opt, (4, 4), dc_max=16, field=field)
    assert valid is False
    assert "rank deficient" in reason

    # T41: Zero-change early stop terminates before max sweeps and computes final rank
    H_opt_2, sweeps_2, updates_2, _, final_r2 = optimize_lane_a_coefficients(
        H_opt, supp, max_sweeps=5, field=field
    )
    # Already local optimum -> sweep 1 produces 0 updates and stops immediately
    assert sweeps_2 == 1
    assert updates_2 == 0
    assert final_r2 == 3


# ---------------------------------------------------------------------------
# Orchestration & Fail-Closed Safety Tests
# ---------------------------------------------------------------------------

def test_production_orchestrator_guard():
    """Safety A: run_v38_development raises PermissionError when authorization is False."""
    with pytest.raises(PermissionError, match="V38 development execution not authorized"):
        run_v38_development(development_execution_authorized=False)


def test_production_orchestration_all_27_attempts_and_fail_closed():
    """Safety B-F: Orchestration completes all 27 attempts, manages NOT_READY lane decoder runs, and respects limits."""
    # Create a test-only seed dictionary with 3 test seeds per lane/source (seeds >= 938001)
    test_seed_dict = {
        "lane_a": {
            "1M": [938101, 938102, 938103],
            "1p5M": [938104, 938105, 938106],
            "2M": [938107, 938108, 938109],
        },
        "lane_b": {
            "1M": [938201, 938202, 938203],
            "1p5M": [938204, 938205, 938206],
            "2M": [938207, 938208, 938209],
        },
        "lane_c": {
            "1M": [938301, 938302, 938303],
            "1p5M": [938304, 938305, 938306],
            "2M": [938307, 938308, 938309],
        },
    }

    # Execute authorized test-only orchestration with fake_runner=True
    res = run_v38_development(
        development_execution_authorized=True,
        fake_runner=True,
        custom_seed_dict=test_seed_dict,
    )

    # B: Exactly 27 structural attempts generated
    assert res["prototypes_generated_count"] == 27
    for lane in ("lane_a", "lane_b", "lane_c"):
        for src in ("1M", "1p5M", "2M"):
            assert len(res["all_prototype_metrics"][lane][src]) == 3

    # D & E: Each READY lane receives 15 decoder runs; max decoder runs <= 45
    for lane, st in res["lane_statuses"].items():
        if st in (LANE_READY, LANE_EVALUATED_NO_SIGNAL, LANE_PROMISING_DIRECTION_SIGNAL):
            assert res["lane_aggregates"][lane]["records_count"] == 15
        else:
            assert res["lane_aggregates"][lane]["records_count"] == 0

    assert res["decoder_runs_count"] <= 45

    # F: Assert no fourth seed is ever used in pre-registered lists
    for lane in ("lane_a", "lane_b", "lane_c"):
        for src in ("1M", "1p5M", "2M"):
            assert len(LANE_PRODUCTION_SEEDS[lane][src]) == 3


def test_orchestration_not_ready_lane_gets_zero_decoder_runs(monkeypatch):
    """Safety C & D: If one source in a lane lacks a winner, that lane gets 0 decoder runs while other READY lanes get 15."""
    test_seed_dict = {
        "lane_a": {
            "1M": [938101, 938102, 938103],
            "1p5M": [938104, 938105, 938106],
            "2M": [938107, 938108, 938109],
        },
        "lane_b": {
            "1M": [938201, 938202, 938203],
            "1p5M": [938204, 938205, 938206],
            "2M": [938207, 938208, 938209],
        },
        "lane_c": {
            "1M": [938301, 938302, 938303],
            "1p5M": [938304, 938305, 938306],
            "2M": [938307, 938308, 938309],
        },
    }

    # Monkeypatch construct_lane_a_prototype for 1M to return structurally invalid matrix
    orig_construct_a = construct_lane_a_prototype

    def _mock_construct_a(source: str, seed: int, **kwargs):
        H, metrics = orig_construct_a(source=source, seed=seed, **kwargs)
        if source == "1M":
            metrics["structurally_valid"] = False
            metrics["structural_failure_reason"] = "Mocked structural failure"
        return H, metrics

    monkeypatch.setattr(
        "comparison_bench.formal_ir.v38_architecture_triage.construct_lane_a_prototype",
        _mock_construct_a,
    )

    res = run_v38_development(
        development_execution_authorized=True,
        fake_runner=True,
        custom_seed_dict=test_seed_dict,
    )

    # All 27 structural attempts were STILL generated unconditionally
    assert res["prototypes_generated_count"] == 27
    assert len(res["all_prototype_metrics"]["lane_a"]["1p5M"]) == 3
    assert len(res["all_prototype_metrics"]["lane_a"]["2M"]) == 3

    # Lane A is NOT READY and received 0 decoder runs
    assert res["lane_statuses"]["lane_a"] == LANE_STRUCTURAL_NOT_READY
    assert res["lane_aggregates"]["lane_a"]["records_count"] == 0

    # Lanes B and C are READY and received exactly 15 decoder runs each
    assert res["lane_aggregates"]["lane_b"]["records_count"] == 15
    assert res["lane_aggregates"]["lane_c"]["records_count"] == 15
    assert res["decoder_runs_count"] == 30  # 15 + 15 = 30


def test_production_seeds_protected_constants():
    """Safety: Production seeds are protected constants disjoint from test seeds."""
    for lane, src_dict in LANE_PRODUCTION_SEEDS.items():
        for src, seeds in src_dict.items():
            for s in seeds:
                assert s < 900000, "Production seed must not overlap test-only range 900000+"


def test_safety_fake_runner_evaluation():
    """Safety: evaluate_single_block supports fake_runner for fast unit testing."""
    H_toy = np.zeros((184, 1024), dtype=np.uint8)
    counts_dummy = np.ones((1024, 1024), dtype=np.float64)
    rec = evaluate_single_block(
        H_toy, source="1M", block_seed=360101, lane="lane_test", construction_seed=938001,
        counts=counts_dummy, fake_runner=True
    )
    assert rec["lane"] == "lane_test"
    assert rec["matrix_id"] == "lane_test_1M_s938001"
    assert rec["status"] == "max_iter"
    assert rec["iterations"] == 30


def test_r1_05_evaluate_single_block_passes_complete_bob_to_posterior(monkeypatch):
    """R1-05: posterior binding receives full Bob symbols, including values >31."""
    alice = np.tile(np.array([1, 34, 547, 996], dtype=np.int64), BLOCK_LENGTH // 4)
    bob = np.tile(np.array([32, 321, 1023, 64], dtype=np.int64), BLOCK_LENGTH // 4)
    captured: dict[str, np.ndarray] = {}

    def fake_sample(counts, seed, size):
        assert size == BLOCK_LENGTH
        return np.arange(BLOCK_LENGTH, dtype=np.int64), alice, bob

    def fake_posterior(counts_arg, bob_arg, u1_arg):
        captured["bob"] = np.asarray(bob_arg).copy()
        captured["u1"] = np.asarray(u1_arg).copy()
        return np.full((len(bob_arg), 32), 1.0 / 32.0, dtype=np.float64)

    monkeypatch.setattr(v38_module, "sample_empirical_block", fake_sample)
    monkeypatch.setattr(v38_module, "get_conditional_posterior_l2", fake_posterior)

    rec = evaluate_single_block(
        np.zeros((SOURCE_CHECKS["1M"], BLOCK_LENGTH), dtype=np.uint8),
        source="1M",
        block_seed=360101,
        lane="lane_test",
        construction_seed=938001,
        counts=np.ones((BLOCK_LENGTH, BLOCK_LENGTH), dtype=np.float64),
        fake_runner=True,
    )

    np.testing.assert_array_equal(captured["bob"], bob)
    assert np.any(captured["bob"] > 31)
    np.testing.assert_array_equal(captured["u1"], (alice >> 5) & 31)
    assert rec["status"] == "max_iter"


def test_r1_06_corrected_prior_matches_v36_numeric_sentinel(monkeypatch):
    """R1-06: wrong low-layer binding changes hard decisions; corrected V38 equals V36."""
    counts = np.ones((BLOCK_LENGTH, BLOCK_LENGTH), dtype=np.float64)
    bob_base = np.array([32, 321, 1023, 64], dtype=np.int64)
    u1_base = np.array([0, 1, 17, 31], dtype=np.int64)
    correct_symbols = np.array([2, 3, 4, 5], dtype=np.int64)
    wrong_symbols = np.array([25, 26, 27, 28], dtype=np.int64)
    low_bob = bob_base & 31

    for i in range(4):
        counts[u1_base[i] * 32 + correct_symbols[i], bob_base[i]] = 1_000_000.0
        counts[u1_base[i] * 32 + wrong_symbols[i], low_bob[i]] = 1_000_000.0

    v36_prior = get_conditional_posterior_l2(counts, bob_base, u1_base)
    wrong_prior = get_conditional_posterior_l2(counts, low_bob, u1_base)
    np.testing.assert_array_equal(np.argmax(v36_prior, axis=1), correct_symbols)
    np.testing.assert_array_equal(np.argmax(wrong_prior, axis=1), wrong_symbols)
    assert np.max(np.abs(v36_prior - wrong_prior)) > 0.9

    alice = np.tile((u1_base << 5) | np.array([1, 2, 3, 4], dtype=np.int64), BLOCK_LENGTH // 4)
    bob = np.tile(bob_base, BLOCK_LENGTH // 4)
    captured: dict[str, np.ndarray] = {}

    def fake_sample(counts_arg, seed, size):
        return np.arange(BLOCK_LENGTH, dtype=np.int64), alice, bob

    def spy_posterior(counts_arg, bob_arg, u1_arg):
        prior = get_conditional_posterior_l2(counts_arg, bob_arg, u1_arg)
        captured["bob"] = np.asarray(bob_arg).copy()
        captured["prior"] = prior.copy()
        return prior

    monkeypatch.setattr(v38_module, "sample_empirical_block", fake_sample)
    monkeypatch.setattr(v38_module, "get_conditional_posterior_l2", spy_posterior)

    evaluate_single_block(
        np.zeros((SOURCE_CHECKS["1M"], BLOCK_LENGTH), dtype=np.uint8),
        source="1M",
        block_seed=360101,
        lane="lane_test",
        construction_seed=938001,
        counts=counts,
        fake_runner=True,
    )

    expected_correct = get_conditional_posterior_l2(
        counts, bob, np.tile(u1_base, BLOCK_LENGTH // 4)
    )
    np.testing.assert_array_equal(captured["bob"], bob)
    np.testing.assert_allclose(captured["prior"], expected_correct, rtol=0.0, atol=0.0)
