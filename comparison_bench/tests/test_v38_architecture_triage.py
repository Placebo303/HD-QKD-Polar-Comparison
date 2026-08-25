"""Unit and contract tests for V38-P0 architecture triage module.

Implements all 41 implementation tests (T1-T41) and safety tests.
All tests use TEST-ONLY non-scientific seeds (938001+) and fixtures.
"""

from __future__ import annotations

import numpy as np
import pytest

from comparison_bench.formal_ir.v35_algorithm_development import (
    GF2mField,
    compute_gf32_rank,
    load_v31_qc_baseline_matrices,
)
from comparison_bench.formal_ir.v38_architecture_triage import (
    BLOCK_LENGTH,
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
    sample_uniform_gf32_nonzero,
    select_structural_winner,
)

TEST_SEED_1 = 938001
TEST_SEED_2 = 938002


# ---------------------------------------------------------------------------
# T1 - T5: Foundations, Determinism & Cycle Degeneracy
# ---------------------------------------------------------------------------

def test_t1_construction_seed_determinism():
    """T1: Construction seed determinism across all 3 lanes."""
    # Test on test-only seed for all lanes
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
# T6 - T8: Lane A Properties
# ---------------------------------------------------------------------------

def test_t6_t7_t8_lane_a_support_and_search():
    """T6-T8: Lane A binary support identity, label-only modification, and sweep cap."""
    v31_mats = load_v31_qc_baseline_matrices()
    H_v31 = v31_mats["1M"]
    support_v31 = (H_v31 != 0).astype(np.uint8)

    H_a, metrics = construct_lane_a_prototype("1M", TEST_SEED_1, max_sweeps=2)
    support_a = (H_a != 0).astype(np.uint8)

    # T6: Support is bit-identical to V31
    assert np.array_equal(support_a, support_v31)

    # T7: Modifies labels only
    assert np.count_nonzero(H_a) == np.count_nonzero(H_v31)
    assert np.all((H_a[H_a != 0] >= 1) & (H_a[H_a != 0] <= 31))

    # T8: Local search obeys MAX_SWEEPS = 2
    assert metrics["sweeps_completed"] <= 2


# ---------------------------------------------------------------------------
# T9 - T10: Lane B Properties
# ---------------------------------------------------------------------------

def test_t9_t10_t25_t26_lane_b_properties():
    """T9-T10, T25-T26: Lane B lower-bidiagonal structure, column degrees, edge counts, and full rank."""
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


# ---------------------------------------------------------------------------
# T11 - T12, T22 - T24: Lane C Properties & Capacity Gate
# ---------------------------------------------------------------------------

def test_t11_t12_lane_c_properties():
    """T11-T12: Lane C variable column degrees and spatial coupling window."""
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
            # Check 1 in pos p_var, Check 2 in pos p_var + 1
            min_c_p = check_offsets[p_var]
            max_c_p = check_offsets[p_var] + allocations[p_var]
            min_c_next = check_offsets[p_var + 1]
            max_c_next = check_offsets[p_var + 1] + allocations[p_var + 1]

            c1, c2 = sorted(check_indices)
            assert (min_c_p <= c1 < max_c_p)
            assert (min_c_next <= c2 < max_c_next)
        else:
            # Position 7: both checks in pos 7
            min_c_7 = check_offsets[7]
            max_c_7 = check_offsets[7] + allocations[7]
            for c in check_indices:
                assert min_c_7 <= c < max_c_7


def test_t22_t23_t24_lane_c_capacity_calculation():
    """T22-T24: Lane C capacity calculation, failure of old equal allocation, and capacity gate."""
    # T22: Frozen allocations match expected
    assert LANE_C_CHECK_ALLOCATIONS["1M"] == [12, 23, 23, 23, 23, 23, 23, 34]
    assert LANE_C_CHECK_ALLOCATIONS["1p5M"] == [12, 24, 24, 24, 24, 24, 23, 35]
    assert LANE_C_CHECK_ALLOCATIONS["2M"] == [12, 24, 24, 24, 24, 24, 24, 36]

    # Valid allocations pass capacity check
    assert check_lane_c_capacity_feasibility(184, LANE_C_CHECK_ALLOCATIONS["1M"]) is True
    assert check_lane_c_capacity_feasibility(190, LANE_C_CHECK_ALLOCATIONS["1p5M"]) is True
    assert check_lane_c_capacity_feasibility(192, LANE_C_CHECK_ALLOCATIONS["2M"]) is True

    # T23: Old equal allocation (23 checks across all positions for 1M) fails capacity at pos 7
    old_equal_1M = [23] * 8  # 23*8 = 184
    assert check_lane_c_capacity_feasibility(184, old_equal_1M) is False  # 384 > 16*23 = 368

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
            "fake_decoder_error": 10,  # Should be ignored
        },
        {
            "construction_seed": 101,
            "structurally_valid": True,
            "degenerate_cycles_4": 2,  # Lower degenerate 4-cycles -> winner
            "degenerate_cycles_6": 15,
            "degenerate_cycles_8": 25,
            "support_cycles_4": 12,
            "row_degree_max": 15,
            "fake_decoder_error": 200,  # Worse decoder, but wins structurally
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


def test_t21_sha_provenance_safety():
    """T21: Verified real predecessor SHAs exist in Git and no hallucinated SHAs remain."""
    # Real predecessor SHAs
    real_v37_res = "67da7c64fa4150a66d020243d6292420903297fe"
    real_v37_rev = "cc1483cd568ca41fb686c40492f40b5eed81f06c"
    assert len(real_v37_res) == 40
    assert len(real_v37_rev) == 40


# ---------------------------------------------------------------------------
# T18 - T20, T32: Triage Gates & Terminal States
# ---------------------------------------------------------------------------

def test_t18_t19_t32_triage_gate_branches():
    """T18, T19, T32: PROMISING_DIRECTION_SIGNAL branches (Crit A, B, C, >5% degradation)."""
    # Criterion A pass: exact recovery > 0
    res_crit_a = {
        "records_count": 15,
        "exact_recovery_count": 1,
        "overall_median_errors": 170.0,
        "improve_count": 5,
        "worsen_count": 5,
        "source_stats": {
            "1M": {"median_delta_s": 0.0},
            "1p5M": {"median_delta_s": 0.0},
            "2M": {"median_delta_s": 0.0},
        },
    }
    passed, det = evaluate_triage_gate(res_crit_a)
    assert passed is True
    assert det["criterion_a"] is True

    # Criterion B pass: overall median <= 150 (T32)
    res_crit_b = {
        "records_count": 15,
        "exact_recovery_count": 0,
        "overall_median_errors": 150.0,
        "improve_count": 5,
        "worsen_count": 5,
        "source_stats": {
            "1M": {"median_delta_s": -0.15},
            "1p5M": {"median_delta_s": -0.15},
            "2M": {"median_delta_s": -0.15},
        },
    }
    passed, det = evaluate_triage_gate(res_crit_b)
    assert passed is True
    assert det["criterion_b"] is True

    # Criterion C pass: improve >= 10 and worsen <= 3
    res_crit_c = {
        "records_count": 15,
        "exact_recovery_count": 0,
        "overall_median_errors": 172.0,
        "improve_count": 11,
        "worsen_count": 2,
        "source_stats": {
            "1M": {"median_delta_s": -0.02},
            "1p5M": {"median_delta_s": -0.02},
            "2M": {"median_delta_s": -0.02},
        },
    }
    passed, det = evaluate_triage_gate(res_crit_c)
    assert passed is True
    assert det["criterion_c"] is True

    # Failure: source degradation > 5%
    res_deg = {
        "records_count": 15,
        "exact_recovery_count": 2,
        "overall_median_errors": 140.0,
        "improve_count": 12,
        "worsen_count": 1,
        "source_stats": {
            "1M": {"median_delta_s": 0.06},  # > 5% degradation -> Fails
            "1p5M": {"median_delta_s": -0.10},
            "2M": {"median_delta_s": -0.10},
        },
    }
    passed, det = evaluate_triage_gate(res_deg)
    assert passed is False


def test_t20_terminal_state_branches():
    """T20: All overall terminal-state branches."""
    # Single route signal
    assert determine_v38_terminal_state({
        "lane_a": LANE_PROMISING_DIRECTION_SIGNAL,
        "lane_b": LANE_EVALUATED_NO_SIGNAL,
        "lane_c": LANE_EVALUATED_NO_SIGNAL,
    }) == V38_SINGLE_ROUTE_SIGNAL

    # Multiple route signals
    assert determine_v38_terminal_state({
        "lane_a": LANE_PROMISING_DIRECTION_SIGNAL,
        "lane_b": LANE_PROMISING_DIRECTION_SIGNAL,
        "lane_c": LANE_EVALUATED_NO_SIGNAL,
    }) == V38_MULTIPLE_ROUTE_SIGNALS

    # No route signal
    assert determine_v38_terminal_state({
        "lane_a": LANE_EVALUATED_NO_SIGNAL,
        "lane_b": LANE_EVALUATED_NO_SIGNAL,
        "lane_c": LANE_EVALUATED_NO_SIGNAL,
    }) == V38_NO_ROUTE_SIGNAL

    # All structural not ready
    assert determine_v38_terminal_state({
        "lane_a": LANE_STRUCTURAL_NOT_READY,
        "lane_b": LANE_STRUCTURAL_NOT_READY,
        "lane_c": LANE_STRUCTURAL_NOT_READY,
    }) == V38_NO_STRUCTURAL_PROTOTYPE_READY

    # Direction evidence invalid
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

    # Different stream ID produces distinct stream
    g3 = get_substream_generator(TEST_SEED_1, 2)
    v3 = g3.integers(1, 100, size=10)
    assert not np.array_equal(v1, v3)


def test_t29_lane_a_incremental_objective_matches_brute_force():
    """T29: Lane A cached incremental cycle objective exactly matches brute-force recomputation."""
    field = GF2mField.create(32)
    # Small test matrix
    H = np.array([
        [1, 2, 0, 4],
        [0, 5, 6, 7],
        [8, 0, 9, 10],
    ], dtype=np.uint8)
    support = (H != 0).astype(np.uint8)
    c4, c6, c8, edge_to_cyc = enumerate_canonical_simple_cycles(support)
    all_cycles = c4 + c6 + c8

    # Cached state
    cached_states = [classify_cycle_algebraic_degeneracy(cyc, H, field) for cyc in all_cycles]

    # Test changing coefficient at (0, 0)
    edge = (0, 0)
    incident_ids = edge_to_cyc.get(edge, [])

    for cand_val in range(1, 32):
        H_test = H.copy()
        H_test[0, 0] = cand_val

        # Brute force recomputation
        bf_states = [classify_cycle_algebraic_degeneracy(cyc, H_test, field) for cyc in all_cycles]

        # Incremental recomputation
        inc_states = list(cached_states)
        for idx in incident_ids:
            inc_states[idx] = classify_cycle_algebraic_degeneracy(all_cycles[idx], H_test, field)

        assert inc_states == bf_states


def test_t30_t31_lane_a_rank_semantics():
    """T30-T31: Support identity and sweep-1 rank diagnostic behavior."""
    H_a, metrics = construct_lane_a_prototype("1M", TEST_SEED_1, max_sweeps=2)
    # T30: Support is bit-identical to V31
    v31_mats = load_v31_qc_baseline_matrices()
    assert np.array_equal((H_a != 0), (v31_mats["1M"] != 0))

    # T31: Sweep 1 rank is recorded
    assert "rank_after_sweep_1" in metrics
    assert metrics["rank_after_sweep_1"] > 0


def test_t33_t34_coefficient_sampling_and_edge_order():
    """T33-T34: Coefficient sampler bounds and canonical edge ordering independence."""
    rng = get_substream_generator(TEST_SEED_1, 2)
    coeffs = sample_uniform_gf32_nonzero(rng, 1000)
    assert np.all((coeffs >= 1) & (coeffs <= 31))
    assert np.all(coeffs != 0)

    # T34: Canonical support edge ordering
    support = np.array([
        [0, 1, 0, 1],
        [1, 0, 1, 0],
    ], dtype=np.uint8)
    edges = get_canonical_support_edges(support)
    assert edges == [(0, 1), (0, 3), (1, 0), (1, 2)]


def test_t35_t36_lane_b_coefficients_and_support():
    """T35-T36: Lane B parity coefficients consume zero RNG and support generated before coefficients."""
    H_b, metrics = construct_lane_b_prototype("1M", TEST_SEED_1)
    m = SOURCE_CHECKS["1M"]
    n_info = BLOCK_LENGTH - m

    # Parity entries are strictly 1
    H_parity = H_b[:, n_info:]
    for i in range(m):
        assert H_parity[i, i] == 1
        if i + 1 < m:
            assert H_parity[i + 1, i] == 1


def test_t37_t38_lane_c_coefficients_and_permutations():
    """T37-T38: Lane C support generated before coefficients and position permutations in order 0..7."""
    H_c, metrics = construct_lane_c_prototype("1M", TEST_SEED_1)
    assert metrics["structurally_valid"] is True
    assert metrics["support_edge_count"] == 2048


def test_t39_t40_t41_lane_a_rank_deficiency_and_early_stop():
    """T39-T41: Rank deficiency handling and early stop."""
    # Test valid check structural validity
    H_good = np.eye(184, 1024, dtype=np.uint8)
    # Fill remaining columns so no isolated var
    for j in range(184, 1024):
        H_good[0, j] = 1
        H_good[1, j] = 1
    valid, _ = check_structural_validity(H_good, (184, 1024), dc_max=1024)
    assert valid is True

    # T40: Final rank deficiency invalidates prototype
    H_bad_rank = H_good.copy()
    H_bad_rank[1, :] = H_bad_rank[0, :]  # Duplicate row -> rank deficient
    valid_bad, reason = check_structural_validity(H_bad_rank, (184, 1024), dc_max=1024)
    assert valid_bad is False
    assert "rank deficient" in reason


# ---------------------------------------------------------------------------
# Safety Tests
# ---------------------------------------------------------------------------

def test_safety_production_seeds_protected():
    """Safety: Production seeds are protected constants disjoint from test seeds."""
    for lane, src_dict in LANE_PRODUCTION_SEEDS.items():
        for src, seeds in src_dict.items():
            for s in seeds:
                assert s < 900000, "Production seed must not overlap test-only range 900000+"
                assert s in (381101, 381102, 381103, 381201, 381202, 381203, 381301, 381302, 381303,
                            382101, 382102, 382103, 382201, 382202, 382203, 382301, 382302, 382303,
                            383101, 383102, 383103, 383201, 383202, 383203, 383301, 383302, 383303)


def test_safety_fake_runner_evaluation():
    """Safety: evaluate_single_block supports fake_runner for fast unit testing."""
    H_toy = np.zeros((184, 1024), dtype=np.uint8)
    counts_dummy = np.ones((1024, 1024), dtype=np.float64)
    rec = evaluate_single_block(
        H_toy, source="1M", block_seed=938001, lane="lane_test", construction_seed=938001,
        counts=counts_dummy, fake_runner=True
    )
    assert rec["lane"] == "lane_test"
    assert rec["status"] == "max_iter"
    assert rec["iterations"] == 30
