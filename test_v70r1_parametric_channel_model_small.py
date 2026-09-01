"""V70R1 small tests — pure functions on synthetic data only.

No real session data, no TEST frames, no decoder, no run_01.
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import numpy as np
import pytest

_spec = importlib.util.spec_from_file_location(
    "v70r1", Path(__file__).parent / "scripts" / "v70r1_parametric_channel_model_check.py"
)
v = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v)

Q = v.Q


# ---------------------------------------------------------------- kernels
def test_m2_shape_normalized_and_centred():
    for family in v.M2_FAMILIES:
        s = v.m2_shape(family, 0.0, 0.6)
        assert abs(s.sum() - 1.0) < 1e-12
        assert int(np.argmax(s)) == 0
        assert s[1] == pytest.approx(s[Q - 1], rel=1e-9)  # symmetric at mu=0


def test_m2_shape_offset_moves_mode():
    s = v.m2_shape("gaussian", 2.0, 0.4)
    assert int(np.argmax(s)) == 2


def test_m2_kernel_normalized_and_background_floor():
    K = v.m2_kernel({"family": "gaussian", "mu": 0.0, "scale": 0.5, "eps": 0.6})
    assert abs(K.sum() - 1.0) < 1e-12
    far = K[Q // 2]
    assert far == pytest.approx(0.6 / Q, rel=1e-6)   # background dominates far away


def test_circulant_normalized_and_smoothing_monotone():
    h = np.zeros(Q)
    h[0] = 900.0
    h[5] = 100.0
    K_light = v.fit_circulant(h, 1e-2)
    K_heavy = v.fit_circulant(h, 1e4)
    assert abs(K_light.sum() - 1.0) < 1e-12
    assert abs(K_heavy.sum() - 1.0) < 1e-12
    assert K_heavy[0] < K_light[0]                    # heavier lambda pulls to uniform
    assert K_heavy[7] > K_light[7]


def test_delta_hist_matches_definition():
    a = np.array([0, 5, 1023, 7], dtype=np.int32)
    b = np.array([0, 3, 0, 9], dtype=np.int32)
    h = v.delta_hist(a, b)
    assert h[0] == 1 and h[2] == 1 and h[1023] == 1 and h[(7 - 9) % Q] == 1
    assert h.sum() == 4


# ---------------------------------------------------------------- entropy
def test_ce_from_kernel_matches_direct_sum():
    rng = np.random.default_rng(0)
    K = rng.random(Q) + 1e-3
    K /= K.sum()
    h = rng.integers(0, 20, size=Q).astype(np.float64)
    direct = -float((h * np.log2(K)).sum() / h.sum())
    assert v.ce_from_kernel(K, h) == pytest.approx(direct, rel=1e-12)


def test_ce_of_uniform_kernel_is_ten_bits():
    K = np.full(Q, 1.0 / Q)
    h = np.full(Q, 3.0)
    assert v.ce_from_kernel(K, h) == pytest.approx(10.0, abs=1e-12)


def test_two_point_model_closed_form():
    """P = (1-eps)*delta_0 + eps/Q reproduces the analytic CE."""
    eps = 0.585
    K = v.m2_kernel({"family": "gaussian", "mu": 0.0, "scale": 0.01, "eps": eps})
    h = np.zeros(Q)
    h[0] = 1.0 - eps
    h[1:] = eps / (Q - 1)
    h *= 1e6
    p0 = (1 - eps) + eps / Q
    expected = -((1 - eps) * math.log2(p0) + eps * math.log2(eps / Q))
    assert v.ce_from_kernel(K, h) == pytest.approx(expected, rel=2e-3)


# ---------------------------------------------------------------- recovery
def test_m2_fit_recovers_planted_parameters():
    rng = np.random.default_rng(7)
    truth = {"family": "gaussian", "mu": 0.0, "scale": 0.5, "eps": 0.55}
    K = v.m2_kernel(truth)
    draws = rng.choice(Q, size=400_000, p=K)
    hist = np.bincount(draws, minlength=Q).astype(np.float64)
    fit = v.fit_m2(hist, "gaussian")
    assert abs(fit["mu"] - truth["mu"]) <= 0.25
    assert abs(fit["eps"] - truth["eps"]) <= 0.05
    assert v.ce_from_kernel(v.m2_kernel(fit), hist) == pytest.approx(
        v.ce_from_kernel(K, hist), abs=0.02
    )


def test_circulant_beats_uniform_on_peaked_source():
    rng = np.random.default_rng(11)
    K = v.m2_kernel({"family": "laplace", "mu": 1.0, "scale": 0.7, "eps": 0.4})
    draws = rng.choice(Q, size=200_000, p=K)
    hist = np.bincount(draws, minlength=Q).astype(np.float64)
    ce_circ = v.ce_from_kernel(v.fit_circulant(hist, 1.0), hist)
    assert ce_circ < 10.0 - 1.0


# ---------------------------------------------------------------- budget
def test_required_uses_ceil_and_is_not_capped():
    assert v.required_bits(7.150000879558332) == 9519
    assert v.required_bits(8.3901) == math.ceil(1.3 * 1024 * 8.3901)
    assert v.required_bits(8.3901) > v.COLS          # never capped at the budget


def test_f_max_is_channel_ceiling_independent_of_planning_f():
    ce = 7.150000879558332
    fmax = v.f_max_from_ce(ce)
    assert fmax * 1024 * ce == pytest.approx(v.COLS - v.TAG_BITS, rel=1e-12)
    assert fmax == pytest.approx(1.3899, abs=1e-4)


def test_classify_budget_three_way_boundaries():
    assert v.classify_budget(v.COLS) == "NO_INFORMATION_MARGIN"
    assert v.classify_budget(v.COLS + 1) == "NO_INFORMATION_MARGIN"
    assert v.classify_budget(v.COLS - 1) == "MARGINAL"
    assert v.classify_budget(v.COLS - 511) == "MARGINAL"
    assert v.classify_budget(v.COLS - 512) == "FEASIBLE"


def test_v70_authority_rows_reproduce_classification():
    """M0 route must match the frozen V70 result for the three sessions."""
    for ce, req, cls in ((7.150000879558332, 9519, "FEASIBLE"),
                         (7.547198, 10047, "MARGINAL"),
                         (8.390100, 11169, "NO_INFORMATION_MARGIN")):
        assert v.required_bits(ce) == req
        assert v.classify_budget(v.required_bits(ce)) == cls


# ---------------------------------------------------------------- fano
def test_fano_is_upper_bound_diagnostic():
    assert v.fano_upper_bound(1.0) == 0.0
    assert v.fano_upper_bound(0.4149) == pytest.approx(6.830, abs=5e-3)
    assert v.fano_upper_bound(0.0) == pytest.approx(math.log2(Q), abs=1e-9)
    accs = [0.1, 0.3, 0.5, 0.7, 0.9]
    bounds = [v.fano_upper_bound(x) for x in accs]
    assert all(bounds[i] > bounds[i + 1] for i in range(len(bounds) - 1))


# ---------------------------------------------------------------- estimator identity
def test_hierarchical_P_is_v70_formula_and_normalized():
    rng = np.random.default_rng(3)
    C = rng.integers(0, 5, size=(Q, Q)).astype(np.int32)
    N_b = C.sum(axis=1).astype(np.float64)
    P_global = C.sum(axis=0).astype(np.float64) / C.sum()
    lam = 221.0
    P = v.hierarchical_P(C, P_global, N_b, lam)
    b = 17
    expected = (C[b] + lam * P_global) / (N_b[b] + lam)
    assert np.allclose(P[b], expected, rtol=0, atol=1e-15)
    assert np.allclose(P.sum(axis=1), 1.0, atol=1e-9)


def test_hierarchical_P_empty_row_falls_back_to_global():
    C = np.zeros((Q, Q), dtype=np.int32)
    C[0, 0] = 10
    N_b = C.sum(axis=1).astype(np.float64)
    P_global = np.full(Q, 1.0 / Q)
    P = v.hierarchical_P(C, P_global, N_b, 1.0)
    assert np.allclose(P[500], P_global)


# ---------------------------------------------------------------- guards
def test_terminals_are_ordered_and_unique():
    assert len(set(v.TERMINALS)) == len(v.TERMINALS)
    assert v.TERMINALS[0] == "V70R1_EVIDENCE_INVALID"
    assert v.TERMINALS[-1] == "V70R1_PARAMETRIC_MODEL_NO_VALUE"


def test_source_is_decoder_free_and_declares_no_decomposition():
    src = (Path(__file__).parent / "scripts" / "v70r1_parametric_channel_model_check.py").read_text(
        encoding="utf-8"
    )
    assert "decode_" not in src
    assert "run_01" not in src.replace("no run_01", "").replace("no_run_01", "")
    assert "ce_decomposition_claimed" in src
    assert "TARGET_F_PLANNING" in src


def test_preregistered_grids_are_frozen():
    assert v.M2_FAMILIES == ("gaussian", "laplace")
    assert v.MU_GRID[0] == -4.0 and v.MU_GRID[-1] == 4.0
    assert len(v.LAMBDA_GRID) == 30
    assert v.EPS_GRID[0] == 0.0


def test_provenance_accepted_plan_and_four_artifacts():
    """Provenance: accepted_plan_sha 0509d10b (full 0509d10ba78902b36f6bcf447f1ebfe289e03fc89b) only four files, 179916f7 successor, four terminals."""
    base = Path(__file__).parent / "openspec" / "changes" / "formal-ir-v70r1-parametric-channel-model-check"
    four = [base / "proposal.md", base / "design.md", base / "tasks.md", base / "specs" / "spec.md"]
    for p in four:
        txt = p.read_text(encoding="utf-8")
        assert "0509d10ba78902b36f6bcf447f1ebfe289e03fc89b" in txt
        assert "0509d10b" in txt
        assert "13b38b79" not in txt
        assert "179916f7" in txt
    # only four files should mention accepted_plan_sha
    assert len(four) == 4
    # four terminals consistent across artifacts and script
    assert len(v.TERMINALS) == 4
    assert v.TERMINALS == (
        "V70R1_EVIDENCE_INVALID",
        "V70R1_TRANSLATION_INVARIANCE_REJECTED",
        "V70R1_PARAMETRIC_MODEL_CHANGES_CAPACITY_ROUTE",
        "V70R1_PARAMETRIC_MODEL_NO_VALUE",
    )
