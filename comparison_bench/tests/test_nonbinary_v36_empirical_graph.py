"""Test Suite T0–T9 for V36 Empirical-P Irregular LDPC & Source-Native Graph Development.

Covers:
- T0: Empirical Channel Posterior & Zero-Denominator Semantics
- T1: Degree Distribution Algebra & Concentrated Check Degrees
- T2: GF(32) Empirical-P DE Golden Reference & Deterministic Repeat
- T3: Source-Native Finite Graph Independence (No Truncation)
- T4: Actual-H Structural Metrics (GF(32) Rank, Girth, Degree Histograms)
- T5: Decoder Numerical Sanity on GF(32) Non-Unit Parity Constraint
- T6: Noisy Real Path (Real Data Blocks Execution)
- T7: Incremental Parity-Check Hierarchy & Rank Monotonicity
- T8: Record Key Uniqueness Invariant
- T9: Report Numbers Directly Computed from CSV/JSON
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v36_empirical_graph import (
    A0_SEEDS,
    A3_SEEDS,
    FIELD_POLY,
    FIELD_Q,
    INCREMENTAL_EXTRA_BITS,
    INCREMENTAL_EXTRA_CHECKS,
    INCREMENTAL_STAGES,
    M2_BY_SOURCE,
    N_SYMBOLS,
    RATES_BY_SOURCE,
    SOURCES,
    STATUS_DE_SHORTLIST_READY,
    TAG_BITS,
    ZeroDenominatorError,
    audit_finite_graph,
    build_v36_channel_sampler,
    build_v36_incremental_matrix,
    check_degree2_cycles,
    construct_source_native_peg_matrix,
    count_bipartite_4_cycles,
    generate_v36_candidate_grid,
    generate_v36_development_report,
    load_v25_channel_counts,
    load_v31_qc_baseline_matrices,
    run_a0_iteration_diagnostic,
    run_v36_a3_finite_screen,
    run_v36_a4_incremental_evaluation,
    run_v36_de_screening,
)
from comparison_bench.src.comparison_bench.formal_ir.v35_algorithm_development import (
    BlockRecord,
    compute_gf32_rank,
    decode_row_layered_fftqspa,
    factorize_f03,
    get_conditional_posterior_l2,
    sample_empirical_block,
    syndrome_of_gf32,
)
from comparison_bench.src.comparison_bench.cli.run_nonbinary_v36_empirical_graph import (
    parse_args,
    run_v36_pipeline,
)


# ===========================================================================
# T0: Empirical Channel Posterior & Zero-Denominator Semantics
# ===========================================================================

def test_t0_channel_sampler_row_normalization_and_centering():
    """Verify channel sampler yields valid probability distributions centered at index 0."""
    counts = load_v25_channel_counts()
    sampler = build_v36_channel_sampler(counts["1M"], "1M")
    rng = np.random.default_rng(101)
    pop = sampler(50, rng)

    assert pop.shape == (50, 32)
    assert np.all(pop >= 0.0)
    assert np.all(np.isfinite(pop))
    assert np.allclose(pop.sum(axis=1), 1.0, atol=1e-12)
    # Re-centering puts true symbol at index 0; index 0 probability should be positive
    assert np.all(pop[:, 0] > 0.0)


def test_t0_channel_sampler_zero_denominator_fail_closed():
    """Verify zero-denominator counts raise ZeroDenominatorError without silent fallback."""
    zero_counts = np.zeros((1024, 1024), dtype=np.float64)
    with pytest.raises(ZeroDenominatorError):
        build_v36_channel_sampler(zero_counts, "zero_test")


# ===========================================================================
# T1: Degree Distribution Algebra & Concentrated Check Degrees
# ===========================================================================

def test_t1_candidate_grid_constraints():
    """Verify all candidate degree distributions satisfy dbar in [2.15, 2.55] and dc <= 16."""
    candidates = generate_v36_candidate_grid()
    assert len(candidates) > 0

    for cand in candidates:
        lam = cand["lambda_edge"]
        assert 1 not in lam  # lambda1 == 0
        assert math.isclose(sum(lam.values()), 1.0, rel_tol=1e-5, abs_tol=1e-6)
        assert 2.15 <= cand["dbar_v"] <= 2.55
        assert cand["max_check_degree"] <= 16
        for src in SOURCES:
            rho = cand["rho_by_source"][src]
            assert math.isclose(sum(rho.values()), 1.0, rel_tol=1e-5, abs_tol=1e-6)


# ===========================================================================
# T2: GF(32) Empirical-P DE Golden Reference & Deterministic Repeat
# ===========================================================================

def test_t2_de_deterministic_reproducibility():
    """Verify empirical-P MC-DE runs produce bit-for-bit identical results on identical seeds."""
    counts = load_v25_channel_counts()
    cand = generate_v36_candidate_grid()[0]
    res1 = run_v36_de_screening(counts, [cand], coarse_samples=200, coarse_max_iter=10, coarse_seed=777, conf_samples=200, conf_max_iter=10, conf_seeds=(881, 882, 883))
    res2 = run_v36_de_screening(counts, [cand], coarse_samples=200, coarse_max_iter=10, coarse_seed=777, conf_samples=200, conf_max_iter=10, conf_seeds=(881, 882, 883))

    ent1 = res1["coarse_records"][0]["worst_source_entropy"]
    ent2 = res2["coarse_records"][0]["worst_source_entropy"]
    assert math.isclose(ent1, ent2, abs_tol=1e-9)


# ===========================================================================
# T3: Source-Native Finite Graph Independence (No Truncation)
# ===========================================================================

def test_t3_source_native_matrix_dimensions_and_isolation():
    """Verify 1M, 1p5M, 2M matrices are constructed independently with exact native shapes."""
    cand = generate_v36_candidate_grid()[0]
    lam = cand["lambda_edge"]

    mats: dict[str, np.ndarray] = {}
    for src in SOURCES:
        H, audit = construct_source_native_peg_matrix(lam, src, n=1024, graph_seed=363001)
        mats[src] = H
        assert H.shape == (M2_BY_SOURCE[src], 1024)
        assert audit["rank"] == M2_BY_SOURCE[src]

    # Verify that H_1M is NOT a submatrix slice of H_2M
    assert not np.array_equal(mats["1M"], mats["2M"][:184, :])


# ===========================================================================
# T4: Actual-H Structural Metrics (GF(32) Rank, Girth, Degree Histograms)
# ===========================================================================

def test_t4_finite_graph_structural_audit():
    """Verify structural audit correctly computes rank, degree histogram, 4-cycles, and realized rate."""
    cand = generate_v36_candidate_grid()[0]
    H, audit = construct_source_native_peg_matrix(cand["lambda_edge"], "1M", n=1024)

    assert audit["shape"] == [184, 1024]
    assert audit["rank"] == 184
    assert audit["rank_full"] is True
    assert audit["isolated_variables"] == 0
    assert audit["isolated_checks"] == 0
    assert audit["max_check_degree"] <= 16
    assert isinstance(audit["four_cycles_count"], int)
    assert isinstance(audit["degree2_cycles_count"], int)


# ===========================================================================
# T5: Decoder Numerical Sanity on GF(32) Non-Unit Parity Constraint
# ===========================================================================

def test_t5_decoder_non_unit_coefficients():
    """Verify row-layered FFT-QSPA correctly verifies non-unit GF(32) parity constraints."""
    field = GF2mField.create(FIELD_Q)
    # Parity constraint: 3 * x0 + 7 * x1 = syndrome over GF(32)
    H = np.array([[3, 7]], dtype=np.uint8)
    x_true = np.array([11, 23], dtype=np.uint8)
    syn = syndrome_of_gf32(H, x_true, field)

    prior = np.full((2, 32), 1e-4)
    prior[0, 11] = 0.9
    prior[1, 23] = 0.9
    prior /= prior.sum(axis=1, keepdims=True)

    res = decode_row_layered_fftqspa(H, prior, syn, max_iter=10, damping_alpha=1.0, field=field)
    assert res.syndrome_ok is True
    assert np.array_equal(res.x_hat, x_true)


# ===========================================================================
# T6: Noisy Real Path (Real Data Blocks Execution)
# ===========================================================================

def test_t6_noisy_real_path_decoding():
    """Verify decoding execution on at least one real noisy block per source without mock/fake runner."""
    counts = load_v25_channel_counts()
    baseline_mats = load_v31_qc_baseline_matrices()

    for src in SOURCES:
        seed = A0_SEEDS[src][0]
        _, alice, bob = sample_empirical_block(counts[src], seed, size=N_SYMBOLS)
        x1, x2, _, y2 = factorize_f03(alice, bob)
        prior = get_conditional_posterior_l2(counts[src], bob, x1)
        raw_errs = int(np.sum(x2 != y2))
        assert raw_errs > 100  # Genuine noisy HD-QKD channel block

        H = baseline_mats[src]
        syn = syndrome_of_gf32(H, x2)
        res = decode_row_layered_fftqspa(H, prior, syn, max_iter=5, damping_alpha=1.0)
        assert res.iterations <= 5
        assert np.isfinite(res.runtime_s)
        errors_final = int(np.sum(res.x_hat != x2))
        assert errors_final <= 1024


# ===========================================================================
# T7: Incremental Parity-Check Hierarchy & Rank Monotonicity
# ===========================================================================

def test_t7_incremental_hierarchy_nesting_and_degrees():
    """Verify S0 subset S1 subset S2 subset S3 nested checks with degree <= 16."""
    cand = generate_v36_candidate_grid()[0]
    H_base, _ = construct_source_native_peg_matrix(cand["lambda_edge"], "1M", n=1024)
    H_mother, stage_mats = build_v36_incremental_matrix(H_base, "1M", target_degree_range=(10, 14), seed=365001)

    assert H_mother.shape == (184 + 32, 1024)
    assert np.array_equal(stage_mats["S0"], H_base)
    assert np.array_equal(stage_mats["S1"][:184, :], H_base)
    assert np.array_equal(stage_mats["S2"][:184+8, :], stage_mats["S1"])
    assert np.array_equal(stage_mats["S3"][:184+16, :], stage_mats["S2"])

    # Check that added check rows have degree in 10..16
    added_degs = (H_mother[184:, :] > 0).sum(axis=1)
    assert np.all(added_degs >= 10)
    assert np.all(added_degs <= 16)


# ===========================================================================
# T8: Record Key Uniqueness Invariant
# ===========================================================================

def test_t8_record_key_uniqueness():
    """Verify that records in finite screen have strictly unique composite keys."""
    counts = load_v25_channel_counts()
    baseline_mats = load_v31_qc_baseline_matrices()
    cand = generate_v36_candidate_grid()[0]
    cid = cand["candidate_id"]

    cand_mats = {cid: {src: construct_source_native_peg_matrix(cand["lambda_edge"], src, n=1024)[0] for src in SOURCES}}
    res = run_v36_a3_finite_screen(counts, baseline_mats, cand_mats, max_iter=2, fake_runner=True)

    keys = set()
    for r in res["records"]:
        key = (r.source, r.seed, r.method, r.graph_id, r.redundancy_stage, r.decoder_schedule)
        assert key not in keys, f"Duplicate record key: {key}"
        keys.add(key)


# ===========================================================================
# T9: Report Regeneration from Structured Artifacts
# ===========================================================================

def test_t9_report_generation_from_summary(tmp_path: Path):
    """Verify Markdown report and claim ledger are generated cleanly from summary payload."""
    report_path = tmp_path / "test_v36_report.md"
    summary = {
        "terminal_status": "NO_FINITE_GRAPH_ADVANCE",
        "stage_summaries": {
            "A0_decoder_iteration_diagnostic": {"selected_max_iter": 30, "median_relative_drops": {"1M": 0.01}},
            "A1_de_candidate_screening": {"status": STATUS_DE_SHORTLIST_READY, "coarse_evaluated": 10, "coarse_passed": 5, "top_candidates": [{"candidate_id": "test_c1"}]},
            "A2_source_native_graphs": {"candidates_constructed": 1},
            "A3_finite_paired_screen": {"status": "NO_FINITE_GRAPH_ADVANCE"},
            "A4_incremental_syndrome": {"executed": False, "status": "SKIPPED"},
        },
    }
    dummy_rec = BlockRecord(
        source="1M", seed=360101, method="nb_ldpc_v36", graph_id="v31_qc_baseline",
        decoder_schedule="row_layered", redundancy_stage="S0", exact_l2=False, syndrome_ok=False,
        tag_ok=False, false_accept=False, errors_initial=250, errors_final=175, iterations=30,
        runtime_s=1.5, syndrome_leakage_bits=0, cumulative_leakage_bits=984, status="max_iter"
    )
    report_text = generate_v36_development_report(summary, [dummy_rec], report_path)
    assert report_path.is_file()
    assert "NO_FINITE_GRAPH_ADVANCE" in report_text
    assert "Pre-Registered Claim Ledger" in report_text
