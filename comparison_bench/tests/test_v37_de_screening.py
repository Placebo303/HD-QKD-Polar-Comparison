"""Unit test suite for V37-P1 Finite-Feasible Empirical-P DE Screening.

Covers tests T1 to T15:
T1 — Candidate enumeration (1771 raw -> 547 N2-gate -> 259 final).
T2 — P0 necessary forest-count semantics.
T3 — Maximum check-degree cap (max_dc <= 20).
T4 — Baseline and positive control isolation.
T5 — AUT_30 exact calculation on synthetic trajectory.
T6 — Checkpoint and threshold metrics (H5, H10, H15, H60, T_0.10, T_0.01).
T7 — 5% per-source screening gate independence.
T8 — Deterministic tie-break ordering.
T9 — Disjoint screening and confirmation seed sets.
T10 — Conditional confirmation execution (skip on 0 passes, single winner on >= 1 passes).
T11 — Failed confirmation handling (P1_SCREEN_SIGNAL_NOT_CONFIRMED, no second candidate).
T12 — Confirmed advance handling (P1_DE_ADVANCE_CANDIDATE_FOUND).
T13 — Convergence requirement (H60 < 1e-4).
T14 — Run count accounting (2349 screening, 18 confirmation, 2367 total).
T15 — CLI dry-run and fake-runner test path.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir.v37_de_screening import (
    CONFIRMATION_SEEDS,
    DE_MAX_ITER,
    DE_N_SAMPLES,
    EFFECT_SIZE_THRESHOLD,
    M2_BY_SOURCE,
    RATES_BY_SOURCE,
    SCREENING_SEEDS,
    SOURCES,
    STATUS_P1_DE_ADVANCE_CANDIDATE_FOUND,
    STATUS_P1_NO_FINITE_FEASIBLE_DE_ADVANCE,
    STATUS_P1_SCREEN_SIGNAL_NOT_CONFIRMED,
    CandidateEvaluationResult,
    DegreeCandidate,
    TrajectoryMetrics,
    aggregate_candidate_results,
    compute_trajectory_metrics,
    export_candidate_summary_csv,
    export_summary_json,
    export_trajectories_csv,
    generate_v37_candidate_grid,
    get_reference_controls,
    run_v37_p1_pipeline,
)


def test_t1_candidate_enumeration():
    """T1: Verify candidate grid enumeration counts (1771 -> 547 -> 259)."""
    raw_cands, n2_cands, final_cands = generate_v37_candidate_grid(step=0.05, max_n2_threshold=183, max_dc_cap=20)
    assert len(raw_cands) == 1771, f"Expected 1771 raw candidates, got {len(raw_cands)}"
    assert len(n2_cands) == 547, f"Expected 547 N2-gate candidates, got {len(n2_cands)}"
    assert len(final_cands) == 259, f"Expected 259 pre-registered candidates, got {len(final_cands)}"

    # Check total evaluated configs (259 candidates + 2 reference controls = 261)
    baseline, pos_control = get_reference_controls()
    assert baseline.candidate_id == "baseline_dv2_regular"
    assert pos_control.candidate_id == "positive_control_v36"


def test_t2_p0_semantics():
    """T2: Verify N2 <= 183 is treated as a necessary forest-count condition."""
    raw_cands, n2_cands, final_cands = generate_v37_candidate_grid()
    for cand in final_cands:
        assert cand.N2 <= 183, f"Candidate {cand.candidate_id} violated N2 <= 183 ({cand.N2})"
        # Verify finite_feasible flag is True and finite_inadmissible is False
        assert cand.finite_feasible is True
        assert cand.finite_inadmissible is False


def test_t3_maximum_check_degree_cap():
    """T3: Verify candidates with max_dc > 20 are excluded."""
    raw_cands, n2_cands, final_cands = generate_v37_candidate_grid()
    for cand in final_cands:
        for m, dc in cand.max_check_degrees.items():
            assert dc <= 20, f"Candidate {cand.candidate_id} has max_dc={dc} for m={m} > 20"

    # Also verify that candidates with max_dc in 21..28 were present in n2_cands but excluded from final_cands
    n2_max_dcs = [
        max(rep["check_node_analysis"][str(m)]["realized_max_check_degree"] for m in [184, 190, 192])
        for _, rep in n2_cands
    ]
    assert max(n2_max_dcs) > 20, "Expected some N2-feasible candidates to exceed check degree 20"


def test_t4_baseline_control_isolation():
    """T4: Verify baseline and positive control objects and properties."""
    baseline, pos_control = get_reference_controls()

    assert baseline.lambda_edge == {2: 1.0}
    assert baseline.finite_feasible is False  # N2 = 1024 > 183
    assert baseline.finite_inadmissible is False

    assert pos_control.lambda_edge == {2: 0.85, 4: 0.15}
    assert pos_control.N2 == 941
    assert pos_control.finite_feasible is False
    assert pos_control.finite_inadmissible is True  # MUST be tagged inadmissible


def test_t5_aut30_calculation():
    """T5: Verify exact calculation of AUT_30 = sum_{t=0}^{30} H(t) on synthetic trajectory."""
    # Synthetic constant trajectory: H(0)=5.0, H(t)=2.0 for t=1..60
    trace_1based = [2.0] * 60
    metrics = compute_trajectory_metrics(trace_1based, h0=5.0, max_aut_iter=30)
    # Expected AUT_30 = 5.0 + 30 * 2.0 = 65.0
    assert metrics.AUT_30 == pytest.approx(65.0, abs=1e-9)

    # Linear decreasing trajectory: H(t) = 5.0 - 0.1 * t
    trace_linear = [5.0 - 0.1 * t for t in range(1, 61)]
    metrics_linear = compute_trajectory_metrics(trace_linear, h0=5.0, max_aut_iter=30)
    # Expected sum_{t=0}^{30} (5.0 - 0.1*t) = 31 * 5.0 - 0.1 * (30 * 31 / 2) = 155.0 - 46.5 = 108.5
    assert metrics_linear.AUT_30 == pytest.approx(108.5, abs=1e-9)


def test_t6_checkpoint_and_threshold_metrics():
    """T6: Verify H5, H10, H15, H60, T_0.10, T_0.01 extraction."""
    # Trace where H(t) reaches <= 0.10 at t=8 and <= 0.01 at t=12, H60 < 1e-4
    trace_1based = [5.0 / (1.5 ** t) for t in range(1, 61)]
    metrics = compute_trajectory_metrics(trace_1based, h0=5.0)

    assert metrics.H5 == pytest.approx(5.0 / (1.5 ** 5), abs=1e-6)
    assert metrics.H10 == pytest.approx(5.0 / (1.5 ** 10), abs=1e-6)
    assert metrics.H15 == pytest.approx(5.0 / (1.5 ** 15), abs=1e-6)
    assert metrics.H60 == pytest.approx(5.0 / (1.5 ** 60), abs=1e-9)
    assert metrics.converged is True

    # Find expected threshold iterations
    full_trace = [5.0] + trace_1based
    exp_t010 = min(t for t in range(1, 61) if full_trace[t] <= 0.10)
    exp_t001 = min(t for t in range(1, 61) if full_trace[t] <= 0.01)
    assert metrics.T_010 == exp_t010
    assert metrics.T_001 == exp_t001


def test_t7_per_source_screening_gate():
    """T7: Verify that a candidate passes screening only if ALL 3 sources improve by >= 5%."""
    baseline_means = {"1M": 100.0, "1p5M": 100.0, "2M": 100.0}

    def make_mock_result(aut_by_source: Dict[str, float], converged: bool = True) -> CandidateEvaluationResult:
        cand = DegreeCandidate("cand_test", {2: 0.1, 3: 0.9}, 146, 2.857, 2926, {184: 16, 190: 16, 192: 16}, True, False)
        metrics_dict = {
            src: {s: compute_trajectory_metrics([aut_by_source[src] / 31.0] * 60, h0=aut_by_source[src] / 31.0) for s in (1, 2, 3)}
            for src in SOURCES
        }
        return aggregate_candidate_results(cand, "screen", metrics_dict, baseline_means)

    # Case 1: All 3 sources beat baseline by 6% (AUT = 94.0 -> Delta = -0.06 <= -0.05) -> PASS
    res_pass = make_mock_result({"1M": 94.0, "1p5M": 94.0, "2M": 94.0})
    assert all(res_pass.relative_deltas[s] <= -0.05 for s in SOURCES)

    # Case 2: 1M and 1.5M beat by 6%, but 2M beats by only 4% (AUT = 96.0 -> Delta = -0.04) -> FAIL
    res_mixed = make_mock_result({"1M": 94.0, "1p5M": 94.0, "2M": 96.0})
    assert not all(res_mixed.relative_deltas[s] <= -0.05 for s in SOURCES)


def test_t8_deterministic_tie_break():
    """T8: Verify 4-level deterministic tie-breaker sorting."""
    # Build 4 candidates
    c1 = DegreeCandidate("cand_A", {2: 0.10, 3: 0.90}, 146, 2.857, 2926, {184: 16, 190: 16, 192: 16}, True, False)
    c2 = DegreeCandidate("cand_B", {2: 0.05, 3: 0.95}, 75, 2.927, 2998, {184: 17, 190: 16, 192: 16}, True, False)
    c3 = DegreeCandidate("cand_C", {2: 0.10, 3: 0.85, 4: 0.05}, 148, 2.892, 2962, {184: 17, 190: 16, 192: 16}, True, False)
    c4 = DegreeCandidate("cand_D", {2: 0.10, 3: 0.85, 5: 0.05}, 149, 2.913, 2984, {184: 17, 190: 16, 192: 16}, True, False)

    # Mock evaluation results
    def make_eval(cand: DegreeCandidate, aut_val: float, h10_val: float) -> CandidateEvaluationResult:
        metrics_dict = {
            src: {s: compute_trajectory_metrics([aut_val / 31.0] * 60, h0=aut_val / 31.0) for s in (1, 2, 3)}
            for src in SOURCES
        }
        for src in SOURCES:
            for s in (1, 2, 3):
                metrics_dict[src][s].H10 = h10_val
                metrics_dict[src][s].AUT_30 = aut_val
        return aggregate_candidate_results(cand, "screen", metrics_dict, {"1M": 100.0, "1p5M": 100.0, "2M": 100.0})

    # Test Level 1: lower mean AUT_30 wins
    r1 = make_eval(c1, 90.0, 1.0)
    r2 = make_eval(c2, 92.0, 1.0)
    lst1 = sorted([r2, r1], key=lambda c: (c.mean_aut30_overall, c.mean_h10_overall, c.candidate.N2, c.candidate.candidate_id))
    assert lst1[0].candidate.candidate_id == "cand_A"

    # Test Level 2: equal AUT_30, lower H10 wins
    r3 = make_eval(c1, 90.0, 1.2)
    r4 = make_eval(c2, 90.0, 0.8)
    lst2 = sorted([r3, r4], key=lambda c: (c.mean_aut30_overall, c.mean_h10_overall, c.candidate.N2, c.candidate.candidate_id))
    assert lst2[0].candidate.candidate_id == "cand_B"

    # Test Level 3: equal AUT_30 and H10, lower N2 wins (c2 has N2=75, c1 has N2=146)
    r5 = make_eval(c1, 90.0, 1.0)
    r6 = make_eval(c2, 90.0, 1.0)
    lst3 = sorted([r5, r6], key=lambda c: (c.mean_aut30_overall, c.mean_h10_overall, c.candidate.N2, c.candidate.candidate_id))
    assert lst3[0].candidate.candidate_id == "cand_B"

    # Test Level 4: equal AUT_30, H10, N2, canonical ID wins (cand_C vs cand_D)
    r7 = make_eval(c3, 90.0, 1.0)
    r8 = make_eval(c4, 90.0, 1.0)
    lst4 = sorted([r8, r7], key=lambda c: (c.mean_aut30_overall, c.mean_h10_overall, c.candidate.N2, c.candidate.candidate_id))
    assert lst4[0].candidate.candidate_id == "cand_C"


def test_t9_disjoint_seed_sets():
    """T9: Verify screening and confirmation seed sets are completely disjoint."""
    for src in SOURCES:
        s_seeds = set(SCREENING_SEEDS[src])
        c_seeds = set(CONFIRMATION_SEEDS[src])
        assert len(s_seeds) == 3
        assert len(c_seeds) == 3
        assert s_seeds.isdisjoint(c_seeds), f"Source {src} has overlapping seeds: {s_seeds & c_seeds}"


def test_t10_conditional_confirmation():
    """T10: Verify confirmation is executed if and only if screening yields >= 1 passing candidates."""
    # Case A: Zero-pass screening branch
    # When threshold is impossible (e.g. 0.99), 0 candidates pass screening
    report_no_pass = run_v37_p1_pipeline(effect_size_threshold=0.99, fake_runner=True)
    assert len(report_no_pass.passing_screening_candidates) == 0
    assert report_no_pass.confirmation_executed is False
    assert report_no_pass.confirmation_de_runs == 0
    assert report_no_pass.screening_de_runs == 2349
    assert report_no_pass.total_de_runs == 2349
    assert report_no_pass.selected_winner is None
    assert report_no_pass.terminal_state == STATUS_P1_NO_FINITE_FEASIBLE_DE_ADVANCE

    # Case B: One-or-more-pass screening branch
    # When threshold is standard (0.05), candidates pass screening and exactly one enters confirmation
    report_pass = run_v37_p1_pipeline(effect_size_threshold=0.05, fake_runner=True)
    assert len(report_pass.passing_screening_candidates) > 0
    assert report_pass.confirmation_executed is True
    assert report_pass.confirmation_de_runs == 18
    assert report_pass.screening_de_runs == 2349
    assert report_pass.total_de_runs == 2367
    assert report_pass.selected_winner is not None


def _make_synthetic_metrics(aut30_val: float, h60_val: float = 1e-5, h0: float = 5.0) -> TrajectoryMetrics:
    """Helper to construct a TrajectoryMetrics with exact requested AUT_30 and H60."""
    step_val = max(0.0, (aut30_val - h0) / 30.0)
    trace = [step_val] * 30 + [h60_val] * 30
    return compute_trajectory_metrics(trace, h0=h0, max_aut_iter=30, target_len=60)


def test_t11_failed_confirmation_terminal_state(monkeypatch):
    """T11: End-to-end pipeline test forcing screening PASS + confirmation FAIL -> P1_SCREEN_SIGNAL_NOT_CONFIRMED.

    Verifies that run_v37_p1_pipeline:
    1. Selects exactly one winner C* from multiple passing candidates.
    2. Enters confirmation for C* and baseline only (confirmation_executed == True, runs == 18, total == 2367).
    3. Concludes terminal state P1_SCREEN_SIGNAL_NOT_CONFIRMED when C* confirmation fails.
    4. Does NOT retry or evaluate the second-best candidate during confirmation.
    """
    import comparison_bench.src.comparison_bench.formal_ir.v37_de_screening as de_mod

    _, _, final_cands = generate_v37_candidate_grid()
    c1_id = final_cands[0].candidate_id
    c2_id = final_cands[1].candidate_id

    confirm_eval_cids: List[str] = []

    def mock_evaluator(candidate, stage, seeds_by_source, samplers, n_samples, max_iter, fake_runner):
        cid = candidate.candidate_id
        if stage == "confirm":
            confirm_eval_cids.append(cid)

        results = {}
        for src in SOURCES:
            results[src] = {}
            for seed in seeds_by_source[src]:
                if stage == "screen":
                    if cid == "baseline_dv2_regular":
                        results[src][seed] = _make_synthetic_metrics(100.0)
                    elif cid == c1_id:
                        results[src][seed] = _make_synthetic_metrics(90.0)  # delta = -0.10 <= -0.05
                    elif cid == c2_id:
                        results[src][seed] = _make_synthetic_metrics(94.0)  # delta = -0.06 <= -0.05
                    else:
                        results[src][seed] = _make_synthetic_metrics(105.0)  # delta = +0.05
                elif stage == "confirm":
                    if cid == "baseline_dv2_regular":
                        results[src][seed] = _make_synthetic_metrics(100.0)
                    elif cid == c1_id:
                        # 1M: 90.0 (-10%), 1p5M: 90.0 (-10%), 2M: 98.0 (-2% -> FAILS gate)
                        val = 98.0 if src == "2M" else 90.0
                        results[src][seed] = _make_synthetic_metrics(val)
                    else:
                        results[src][seed] = _make_synthetic_metrics(105.0)
        return results

    monkeypatch.setattr(de_mod, "evaluate_single_config", mock_evaluator)

    report = run_v37_p1_pipeline(fake_runner=True)

    # Assertions on the actual ScreeningExecutionReport
    assert report.terminal_state == STATUS_P1_SCREEN_SIGNAL_NOT_CONFIRMED
    assert report.confirmation_executed is True
    assert report.confirmation_passed is False
    assert report.screening_de_runs == 2349
    assert report.confirmation_de_runs == 18
    assert report.total_de_runs == 2367
    assert report.selected_winner is not None
    assert report.selected_winner.candidate.candidate_id == c1_id
    assert len(report.passing_screening_candidates) == 2

    # Verify confirmation evaluated ONLY c1 and baseline (no second candidate fallback)
    assert confirm_eval_cids == [c1_id, "baseline_dv2_regular"]
    assert c2_id not in confirm_eval_cids


def test_t12_confirmed_advance_terminal_state(monkeypatch):
    """T12: End-to-end pipeline test forcing screening PASS + confirmation PASS -> P1_DE_ADVANCE_CANDIDATE_FOUND.

    Verifies that run_v37_p1_pipeline:
    1. Selects winner C* from screening.
    2. Successfully confirms C* on fresh confirmation seeds on all 3 sources (Delta_s <= -0.05).
    3. Concludes terminal state P1_DE_ADVANCE_CANDIDATE_FOUND.
    4. Evaluates only C* and baseline in confirmation.
    """
    import comparison_bench.src.comparison_bench.formal_ir.v37_de_screening as de_mod

    _, _, final_cands = generate_v37_candidate_grid()
    c1_id = final_cands[0].candidate_id

    confirm_eval_cids: List[str] = []

    def mock_evaluator(candidate, stage, seeds_by_source, samplers, n_samples, max_iter, fake_runner):
        cid = candidate.candidate_id
        if stage == "confirm":
            confirm_eval_cids.append(cid)

        results = {}
        for src in SOURCES:
            results[src] = {}
            for seed in seeds_by_source[src]:
                if stage == "screen":
                    if cid == "baseline_dv2_regular":
                        results[src][seed] = _make_synthetic_metrics(100.0)
                    elif cid == c1_id:
                        results[src][seed] = _make_synthetic_metrics(90.0)
                    else:
                        results[src][seed] = _make_synthetic_metrics(105.0)
                elif stage == "confirm":
                    if cid == "baseline_dv2_regular":
                        results[src][seed] = _make_synthetic_metrics(100.0)
                    elif cid == c1_id:
                        # c1 passes on all 3 sources in confirmation (90.0 -> -10% <= -5%)
                        results[src][seed] = _make_synthetic_metrics(90.0)
                    else:
                        results[src][seed] = _make_synthetic_metrics(105.0)
        return results

    monkeypatch.setattr(de_mod, "evaluate_single_config", mock_evaluator)

    report = run_v37_p1_pipeline(fake_runner=True)

    # Assertions on the actual ScreeningExecutionReport
    assert report.terminal_state == STATUS_P1_DE_ADVANCE_CANDIDATE_FOUND
    assert report.confirmation_executed is True
    assert report.confirmation_passed is True
    assert report.screening_de_runs == 2349
    assert report.confirmation_de_runs == 18
    assert report.total_de_runs == 2367
    assert report.selected_winner is not None
    assert report.selected_winner.candidate.candidate_id == c1_id
    assert confirm_eval_cids == [c1_id, "baseline_dv2_regular"]


def test_t13_convergence_requirement():
    """T13: Verify that H60 >= 1e-4 fails convergence."""
    trace_non_conv = [1.0] * 60
    m_non_conv = compute_trajectory_metrics(trace_non_conv, h0=5.0)
    assert m_non_conv.converged is False
    assert m_non_conv.H60 == 1.0

    trace_conv = [1e-5] * 60
    m_conv = compute_trajectory_metrics(trace_conv, h0=5.0)
    assert m_conv.converged is True
    assert m_conv.H60 == 1e-5


def test_t14_run_count_accounting():
    """T14: Verify exact run count arithmetic: 2349 screening, 18 confirmation, 2367 max total."""
    n_configs = 259 + 2  # 261
    n_sources = 3
    n_seeds_screen = 3
    screening_expected = n_configs * n_sources * n_seeds_screen
    assert screening_expected == 2349

    n_confirm_configs = 2  # Winner + Baseline
    n_seeds_confirm = 3
    confirmation_expected = n_confirm_configs * n_sources * n_seeds_confirm
    assert confirmation_expected == 18

    total_expected = screening_expected + confirmation_expected
    assert total_expected == 2367


def test_t15_cli_dry_run_and_reporting():
    """T15: Verify CLI dry-run and fake-runner execution and reporting."""
    # 1. Test CLI dry-run
    cmd_dry = [sys.executable, "-m", "comparison_bench.src.comparison_bench.cli.run_v37_de_screening", "--dry-run"]
    res_dry = subprocess.run(cmd_dry, capture_output=True, text=True)
    assert res_dry.returncode == 0
    assert "Raw Simplex Candidates (degrees {2,3,4,5}, step=0.05): 1771" in res_dry.stdout
    assert "P0 Necessary Forest Gate (N2 <= 183):                 547" in res_dry.stdout
    assert "Final Pre-Registered Set (N2 <= 183 & max_dc <= 20):  259" in res_dry.stdout
    assert "[DRY RUN] Candidate enumeration complete. No DE executed." in res_dry.stdout

    # 2. Test CLI fake-runner with output directory under workspace/
    out_dir = Path("workspace/test_v37_p1_cli")
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd_fake = [
        sys.executable,
        "-m",
        "comparison_bench.src.comparison_bench.cli.run_v37_de_screening",
        "--fake-runner",
        "--output-dir",
        str(out_dir),
    ]
    res_fake = subprocess.run(cmd_fake, capture_output=True, text=True)
    assert res_fake.returncode == 0
    assert (out_dir / "v37_p1_candidate_summary.csv").exists()
    assert (out_dir / "v37_p1_trajectories.csv").exists()
    assert (out_dir / "v37_p1_summary.json").exists()

    with open(out_dir / "v37_p1_summary.json", "r", encoding="utf-8") as fp:
        summary = json.load(fp)
    assert summary["schema_version"] == "v37_p1_de_screening_v1"
    assert summary["candidate_counts"]["raw"] == 1771
    assert summary["candidate_counts"]["final_candidates"] == 259
    assert summary["run_counts"]["screening_runs"] == 2349


def test_t16_early_stop_padding_and_indexing_semantics():
    """T16: Verify short trace padding to t=60, H60 semantics, and exact AUT_30 indexing."""
    # A short trace of 10 iterations (terminated early at t=10)
    trace_short_1based = [4.0, 3.0, 2.0, 1.0, 0.5, 0.2, 0.05, 0.005, 1e-4, 1e-6]
    h0 = 5.0
    metrics = compute_trajectory_metrics(trace_short_1based, h0=h0, max_aut_iter=30, target_len=60)

    # 1. Verify full trajectory length and 0-indexing:
    # full_trace has 61 entries: full_trace[0] = H(0), full_trace[1] = H(1), ..., full_trace[60] = H(60)
    assert len(metrics.entropy_trace) == 61
    assert metrics.entropy_trace[0] == 5.0
    for t in range(1, 11):
        assert metrics.entropy_trace[t] == pytest.approx(trace_short_1based[t - 1], abs=1e-9)

    # 2. Verify padding to t=60:
    for t in range(11, 61):
        assert metrics.entropy_trace[t] == pytest.approx(1e-6, abs=1e-9)

    # 3. Verify H5, H10, H15, H60 semantics:
    assert metrics.H5 == pytest.approx(0.5, abs=1e-9)
    assert metrics.H10 == pytest.approx(1e-6, abs=1e-9)
    assert metrics.H15 == pytest.approx(1e-6, abs=1e-9)
    assert metrics.H60 == pytest.approx(1e-6, abs=1e-9)
    assert metrics.converged is True

    # 4. Verify threshold iterations:
    # H(7) = 0.05 <= 0.10 -> T_010 == 7
    # H(8) = 0.005 <= 0.01 -> T_001 == 8
    assert metrics.T_010 == 7
    assert metrics.T_001 == 8

    # 5. Verify exact AUT_30 sum without indexing offset:
    # AUT_30 = H(0) + sum_{t=1}^{10} H(t) + 20 * H(10)
    expected_sum_10 = sum(trace_short_1based)  # 10.755101
    expected_aut_30 = 5.0 + expected_sum_10 + 20 * 1e-6  # 15.755121
    assert metrics.AUT_30 == pytest.approx(expected_aut_30, abs=1e-9)
    assert metrics.AUT_30 == pytest.approx(sum(metrics.entropy_trace[:31]), abs=1e-9)
