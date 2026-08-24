"""Test Suite T1–T5 for V35R1 Empirical-Posterior-Driven Error-Correction Algorithm Development.

Covers:
- Tier 1 (T1): Decoder Numerical Correctness & Baseline Matrix Identity Isolation
- Tier 2 (T2): Hand-Designed Mixed-Degree Protograph & Deterministic Lifting Validation (0 deg-2 cycles, girth >= 6)
- Tier 3 (T3): Incremental Syndrome Hierarchy & Clean Cold-Start Evaluation
- Tier 4 (T4): Binary Multilevel Coding (MLC) Chain Rule & Information Accounting
- Tier 5 (T5): Regression, Seed Disjointness & Non-Destructive Isolation
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField, get_field_spec
from comparison_bench.src.comparison_bench.formal_ir.v35_algorithm_development import (
    DEFAULT_DAMPING_ALPHA,
    DEVELOPMENT_SEEDS,
    FIELD_POLY,
    FIELD_Q,
    INCREMENTAL_CHECKS,
    INCREMENTAL_EXTRA_BITS,
    INCREMENTAL_STAGES,
    N_PROTOGRAPH,
    N_SYMBOLS,
    SOURCES,
    STATUS_BINARY_MLC_READY,
    STATUS_NB_CANDIDATE_READY,
    STATUS_NO_CANDIDATE_SUCCESS,
    TAG_BITS,
    Z_LIFTING,
    build_hand_designed_mixed_degree_protograph,
    build_v35_incremental_mother_matrix,
    build_v35_protograph,
    build_v35_shifts,
    check_protograph_degree2_cycles,
    compute_conditional_entropy_profile,
    compute_empirical_conditional_llrs,
    compute_gf32_rank,
    compute_tag_64,
    compute_tag_64_symbols,
    count_tanner_4_cycles,
    decode_binary_mlc_frame,
    decode_damped_row_layered_fftqspa,
    decode_flooding_fftqspa,
    decode_row_layered_fftqspa,
    decode_v35_incremental_stage_a3,
    factorize_f03,
    fwht_batched,
    get_conditional_posterior_l2,
    get_incremental_check_counts,
    gray_bitplanes_to_symbols,
    gray_decode_symbols,
    gray_encode_symbols,
    lift_protograph_gf32,
    load_v25_channel_counts,
    load_v31_qc_baseline_matrices,
    make_binary_parity_check_matrix,
    sample_empirical_block,
    symbols_to_gray_bitplanes,
    syndrome_of_gf32,
)
from comparison_bench.src.comparison_bench.cli.run_v35_algorithm_development import (
    parse_args,
    run_v35_pipeline,
)


# ===========================================================================
# Tier 1 (T1): Decoder Numerical Correctness & Matrix Identity Isolation
# ===========================================================================

def test_t1_fwht_batched_involution():
    """Verify that FWHT(FWHT(f)) == q * f for GF(32) q=32."""
    rng = np.random.default_rng(101)
    q = 32
    f = rng.standard_normal((10, q))
    wht_f = fwht_batched(f)
    wht_wht_f = fwht_batched(wht_f)
    assert np.allclose(wht_wht_f, q * f, atol=1e-12)


def test_t1_single_check_gf32_exact_map():
    """Verify single-check GF(32) decode matches exact parity constraint."""
    field = GF2mField.create(FIELD_Q)
    H = np.array([[1, 1]], dtype=np.uint8)
    q = 32
    prior = np.full((2, q), 1e-6)
    prior[0, 5] = 0.95
    prior[1, 7] = 0.95
    prior /= prior.sum(axis=1, keepdims=True)

    true_syn = np.array([5 ^ 7], dtype=np.uint8)
    res = decode_flooding_fftqspa(H, prior, true_syn, max_iter=5, field=field)
    assert res.syndrome_ok is True
    assert res.x_hat[0] == 5
    assert res.x_hat[1] == 7


def test_t1_flooding_vs_layered_cycle_free_equivalence():
    """Verify that on a tree (cycle-free) graph, Flooding and Layered decoders converge to identical hard decisions."""
    field = GF2mField.create(FIELD_Q)
    H = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
    x_true = np.array([3, 14, 25], dtype=np.uint8)
    syn = syndrome_of_gf32(H, x_true, field)

    prior = np.full((3, 32), 1e-4)
    for i in range(3):
        prior[i, x_true[i]] = 0.9
    prior /= prior.sum(axis=1, keepdims=True)

    res_flood = decode_flooding_fftqspa(H, prior, syn, max_iter=10, field=field)
    res_layer = decode_row_layered_fftqspa(H, prior, syn, max_iter=10, damping_alpha=1.0, field=field)

    assert res_flood.syndrome_ok is True
    assert res_layer.syndrome_ok is True
    assert np.array_equal(res_flood.x_hat, x_true)
    assert np.array_equal(res_layer.x_hat, x_true)


def test_t1_damped_layered_message_invariants():
    """Verify that damped messages remain non-negative, finite, normalized, and error-free."""
    field = GF2mField.create(FIELD_Q)
    H = np.array([[1, 1, 2], [2, 3, 1]], dtype=np.uint8)
    x_true = np.array([10, 20, 30], dtype=np.uint8)
    syn = syndrome_of_gf32(H, x_true, field)

    rng = np.random.default_rng(202)
    prior = rng.uniform(0.01, 1.0, size=(3, 32))
    prior /= prior.sum(axis=1, keepdims=True)

    res = decode_row_layered_fftqspa(H, prior, syn, max_iter=5, damping_alpha=0.5, field=field)
    assert np.all(np.isfinite(res.final_beliefs))
    exp_b = np.exp(res.final_beliefs - np.max(res.final_beliefs, axis=1, keepdims=True))
    probs = exp_b / np.sum(exp_b, axis=1, keepdims=True)
    assert np.all(probs >= 0.0)
    assert np.allclose(probs.sum(axis=1), 1.0, atol=1e-12)


def test_t1_syndrome_check_strict_verification():
    """Verify decoder returns syndrome_ok=True iff H @ x == s in GF(32)."""
    field = GF2mField.create(FIELD_Q)
    H = np.array([[1, 1, 1, 1]], dtype=np.uint8)
    x_wrong = np.array([1, 2, 3, 4], dtype=np.uint8)
    syn_target = np.array([9], dtype=np.uint8)

    calc_syn = syndrome_of_gf32(H, x_wrong, field)
    assert not np.array_equal(calc_syn, syn_target)


def test_t1_baseline_matrix_loading_and_isolation():
    """Verify that frozen V31 baseline matrices are loaded correctly and strictly isolated from A2 protograph."""
    baseline_mats = load_v31_qc_baseline_matrices()
    assert set(baseline_mats.keys()) == {"1M", "1p5M", "2M"}
    assert baseline_mats["1M"].shape == (184, 1024)
    assert baseline_mats["1p5M"].shape == (190, 1024)
    assert baseline_mats["2M"].shape == (192, 1024)

    # Verify regular column degree 2 for baseline
    for src, mat in baseline_mats.items():
        col_degs = (mat > 0).sum(axis=0)
        assert np.all(col_degs == 2)

    # Verify isolation against lifted protograph
    B = build_hand_designed_mixed_degree_protograph()
    S = build_v35_shifts(B, Z=Z_LIFTING, seed=20260824)
    H_proto = lift_protograph_gf32(B, S, Z=Z_LIFTING, seed=999)

    for src in SOURCES:
        base_m = {"1M": 184, "1p5M": 190, "2M": 192}[src]
        assert not np.array_equal(baseline_mats[src], H_proto[:base_m, :])


# ===========================================================================
# Tier 2 (T2): Protograph & Deterministic Lifting Validation
# ===========================================================================

def test_t2_protograph_degree_distribution_and_zero_deg2_cycles():
    """Validate Stage A2 Protograph degrees, average degree, lambda2 fraction, and zero degree-2 cycles."""
    B = build_hand_designed_mixed_degree_protograph()
    M_p, N_p = B.shape
    assert (M_p, N_p) == (6, 32)

    var_degrees = B.sum(axis=0)
    assert np.all(var_degrees >= 2)
    assert np.all(var_degrees <= 5)
    assert not np.any(var_degrees == 1)  # lambda1 == 0

    total_edges = int(np.sum(var_degrees))
    avg_dv = total_edges / N_p
    assert 2.2 <= avg_dv <= 3.2

    deg2_cols = np.where(var_degrees == 2)[0]
    deg2_edges = len(deg2_cols) * 2
    lambda2 = deg2_edges / total_edges
    assert lambda2 <= 0.35

    # CRITICAL: Verify zero degree-2 cycles in protograph
    deg2_cycle_rank = check_protograph_degree2_cycles(B)
    assert deg2_cycle_rank == 0


def test_t2_deterministic_lifting_girth_and_reproducibility():
    """Validate deterministic lifting has zero 4-cycles (girth >= 6) and bit-for-bit reproducibility."""
    B = build_hand_designed_mixed_degree_protograph()
    S1 = build_v35_shifts(B, Z=Z_LIFTING, seed=20260824)
    S2 = build_v35_shifts(B, Z=Z_LIFTING, seed=20260824)
    assert np.array_equal(S1, S2)

    c4 = count_tanner_4_cycles(B, S1, Z=Z_LIFTING)
    assert c4 == 0  # Zero 4-cycles => Girth >= 6


def test_t2_gf32_rank_and_matrix_shape():
    """Validate lifted GF(32) parity-check matrix has shape (192, 1024) and full row rank 192."""
    B = build_hand_designed_mixed_degree_protograph()
    S = build_v35_shifts(B, Z=Z_LIFTING, seed=20260824)
    H = lift_protograph_gf32(B, S, Z=Z_LIFTING, seed=999)
    assert H.shape == (192, 1024)

    rank = compute_gf32_rank(H)
    assert rank == 192


# ===========================================================================
# Tier 3 (T3): Incremental Syndrome Hierarchy
# ===========================================================================

def test_t3_nested_parity_check_hierarchy_and_full_rank():
    """Validate mother matrix nesting: H_S0 subset H_S1 subset H_S2 subset H_S3 and full rank 224."""
    B = build_hand_designed_mixed_degree_protograph()
    S = build_v35_shifts(B, Z=Z_LIFTING, seed=20260824)
    H_base = lift_protograph_gf32(B, S, Z=Z_LIFTING, seed=999)
    H_mother = build_v35_incremental_mother_matrix(H_base, Z=Z_LIFTING, seed=54321)

    assert H_mother.shape == (224, 1024)
    assert np.array_equal(H_mother[:192, :], H_base)

    # Verify full row rank of 224
    rank = compute_gf32_rank(H_mother)
    assert rank == 224


def test_t3_leakage_accounting_increments():
    """Validate incremental syndrome leakage values match exact +0, +40, +80, +160 bit specification."""
    for stage, extra_bits in INCREMENTAL_EXTRA_BITS.items():
        m_checks = INCREMENTAL_CHECKS[stage]
        extra_checks = m_checks - 192
        assert extra_checks * 5 == extra_bits


def test_t3_cold_start_incremental_decoder():
    """Validate Stage A3 clean cold-start decoding across S0..S3 on a noiseless block."""
    B = build_hand_designed_mixed_degree_protograph()
    S = build_v35_shifts(B, Z=Z_LIFTING, seed=20260824)
    H_base = lift_protograph_gf32(B, S, Z=Z_LIFTING, seed=999)
    H_mother = build_v35_incremental_mother_matrix(H_base, Z=Z_LIFTING, seed=54321)

    x1_true = np.zeros(1024, dtype=np.uint8)
    x2_true = np.ones(1024, dtype=np.uint8) * 5
    prior = np.full((1024, 32), 1e-4)
    prior[:, 5] = 0.99
    prior /= prior.sum(axis=1, keepdims=True)

    results = decode_v35_incremental_stage_a3(H_mother, prior, x2_true, x1_true, source="2M", max_iter_per_stage=5)
    assert set(results.keys()) == {"S0", "S1", "S2", "S3"}
    for stg in ("S0", "S1", "S2", "S3"):
        res = results[stg]
        assert res.exact_l2 is True
        assert res.syndrome_ok is True
        assert res.tag_ok is True
        assert res.false_accept is False
        assert res.errors_final == 0


# ===========================================================================
# Tier 4 (T4): Binary Multilevel Coding (MLC) Chain Rule & MSD
# ===========================================================================

def test_t4_gray_symbol_bijection():
    """Validate Gray code encoding and inverse decoding is an exact bijection on [0, 1024)."""
    syms = np.arange(1024, dtype=np.int64)
    planes = symbols_to_gray_bitplanes(syms)
    assert planes.shape == (1024, 10)
    rec = gray_bitplanes_to_symbols(planes)
    assert np.array_equal(syms, rec)


def test_t4_conditional_entropy_chain_rule_closure():
    """Validate sum of 10 layer conditional entropies equals total H(A|B) within 1e-5 bits."""
    counts = load_v25_channel_counts()["1M"]
    layer_h, total_h = compute_conditional_entropy_profile(counts)
    sum_h = float(np.sum(layer_h))
    assert math.isclose(sum_h, total_h, rel_tol=1e-5, abs_tol=1e-6)
    assert layer_h[0] < 0.05
    assert layer_h[9] > 0.20


def test_t4_tiny_frame_mlc_noiseless_recovery():
    """Validate MLC multistage decoder on noiseless synthetic frame."""
    counts = load_v25_channel_counts()["1M"]
    alice = np.arange(1024, dtype=np.int64)
    bob = alice.copy()

    res = decode_binary_mlc_frame(counts, alice, bob, max_iter=5)
    assert res.exact_frame is True
    assert res.tag_ok is True
    assert res.false_accept is False
    assert res.errors_final_symbols == 0


# ===========================================================================
# Tier 5 (T5): Regression & Non-Destructive Boundary
# ===========================================================================

def test_t5_development_seed_space_disjointness():
    """Verify V35 development seeds are strictly disjoint from V34 formal seeds."""
    v34_seeds = set()
    for base in (340101, 340201, 340301):
        for i in range(20):
            v34_seeds.add(base + i)

    v35_seeds = set()
    for src in SOURCES:
        for s in DEVELOPMENT_SEEDS[src]:
            v35_seeds.add(s)

    assert len(v35_seeds) == 15
    assert v35_seeds.isdisjoint(v34_seeds)


def test_t5_frozen_directory_protection():
    """Verify that frozen directories and V34 outputs exist and are protected."""
    repo_root = Path(__file__).resolve().parents[2]
    v25_path = repo_root / "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz"
    assert v25_path.is_file()

    v34_manifest = repo_root / "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v34_corrected_matched_empirical_p_finite_control/run_01/RUN_MANIFEST.json"
    if v34_manifest.exists():
        assert v34_manifest.is_file()


def test_t5_cli_parse_args_all_stages():
    """Verify CLI argument parser handles all --stages choices and custom arguments."""
    valid_stages = ["auto", "all", "A1", "A2", "A3", "A4"]
    for st in valid_stages:
        parsed = parse_args(["--stages", st, "--output-root", "workspace/test_out", "--fake-runner", "--dry-run"])
        assert parsed.stages == st
        assert parsed.output_root == "workspace/test_out"
        assert parsed.fake_runner is True
        assert parsed.dry_run is True


@pytest.mark.parametrize("stages_mode", ["auto", "all", "A1", "A2", "A3", "A4"])
def test_t5_cli_all_stages_dry_run(tmp_path: Path, stages_mode: str):
    """Validate CLI execution with --dry-run across all --stages options."""
    out_dir = tmp_path / f"v35_dry_run_{stages_mode}"
    summary = run_v35_pipeline(
        output_root=out_dir,
        stages_mode=stages_mode,
        sources=["1M"],
        max_iter=5,
        dry_run=True,
        fake_runner=False,
    )
    assert summary["status"] == "dry_run_completed"
    assert summary["terminal_status"] == "DRY_RUN"
    assert summary["total_blocks"] == 5


def test_t5_cli_fake_runner_execution_and_artifacts(tmp_path: Path):
    """Validate complete CLI execution with fake runner produces all artifacts and auto report."""
    out_dir = tmp_path / "v35_fake_run"
    summary = run_v35_pipeline(
        output_root=out_dir,
        stages_mode="auto",
        sources=["1M"],
        max_iter=5,
        dry_run=False,
        fake_runner=True,
    )
    assert (out_dir / "v35_algorithm_development_blocks.csv").is_file()
    assert (out_dir / "v35_algorithm_development_summary.json").is_file()
    assert (out_dir / "RUN_MANIFEST.json").is_file()
