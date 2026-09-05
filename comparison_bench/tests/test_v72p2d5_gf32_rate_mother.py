"""V72P2D5 GF32 rate-mother — R2 T0 (no decoder) + T1 (fake decoder only).

R2 dv3 implementation stage only: small fixture n=12/m_max=10/k_min=7 plus
tiny hand matrices and injected fakes. No full-size construction, no real
decoder, no data reads, no output files.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))
CORE_PATH = (ROOT / "comparison_bench" / "src" / "comparison_bench"
             / "formal_ir" / "v72p2d5_gf32_rate_mother.py")
CLI_PATH = ROOT / "scripts" / "v72p2d5_gf32_rate_mother.py"
STATE_PATH = (ROOT / "docs" / "research_cycles" / "V72P2D5-GF32-RATE-MOTHER"
              / "cycle_state.yaml")

_SPEC = importlib.util.spec_from_file_location(
    "v72p2d5_gf32_rate_mother", str(CORE_PATH))
assert _SPEC is not None and _SPEC.loader is not None
mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mod)

_CSPEC = importlib.util.spec_from_file_location(
    "v72p2d5_gf32_rate_mother_cli", str(CLI_PATH))
assert _CSPEC is not None and _CSPEC.loader is not None
cli = importlib.util.module_from_spec(_CSPEC)
_CSPEC.loader.exec_module(cli)

CORE_SRC = CORE_PATH.read_text(encoding="utf-8")
CLI_SRC = CLI_PATH.read_text(encoding="utf-8")
PHASE_FUNCS = {"run_structure_phase", "run_g0_phase", "run_p0_cost_phase",
               "run_g1_phase", "run_g2_phase"}

SMALL_N = 12
SMALL_M = 10
SMALL_K = 7
SMALL_SEED = 7


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------
def _full_tables():
    rng = np.random.default_rng(20260905)
    counts = rng.integers(0, 50, size=(1024, 1024)).astype(np.float64)
    p_b = np.full(1024, 1.0 / 1024)
    return counts, p_b


def _tiny_tables():
    rng = np.random.default_rng(11)
    raw = rng.random((64, 8)) + 0.5
    p_f = raw / raw.sum(axis=0)
    p_b = np.full(8, 1.0 / 8)
    return p_b, p_f


def _tiny_h():
    h1 = np.array([[1, 1, 0, 0, 0, 0],
                   [0, 1, 2, 0, 0, 0],
                   [0, 0, 1, 1, 0, 0]], dtype=np.uint8)
    h2 = np.array([[1, 2, 0, 0, 0, 0],
                   [0, 1, 1, 0, 0, 0],
                   [0, 0, 1, 2, 0, 0],
                   [0, 0, 0, 1, 1, 0]], dtype=np.uint8)
    return {"L1": h1, "L2": h2}


def _small_support(seed=SMALL_SEED):
    return mod.build_dv3_nested_support(SMALL_N, SMALL_M, SMALL_K, seed)


def _small_mother(seed=SMALL_SEED):
    return mod.build_dv3_nested_mother(SMALL_N, SMALL_M, SMALL_K, seed, None)


class FakeDecoder:
    def __init__(self):
        self.calls = []

    def __call__(self, h, prior, syndrome, layer=None):
        prior = np.asarray(prior, dtype=np.float64)
        self.calls.append((np.shape(h), prior.shape, layer))
        n = prior.shape[0]
        return {"x_hat": np.zeros(n, dtype=np.int64),
                "syndrome_ok": False,
                "iterations": 1,
                "final_beliefs": np.zeros_like(prior)}


def _boom(name):
    def _f(**kw):
        raise AssertionError(f"{name} must not be entered")
    return _f


# --------------------------------------------------------------------------
# T0 — no decoder calls
# --------------------------------------------------------------------------
def test_T0_01_counts_axis_asymmetry_hand_calc():
    counts = np.zeros((1024, 1024))
    counts[0, 0] = 5.0
    counts[1, 0] = 5.0
    counts[0, 1] = 10.0
    p = mod.build_f_model(counts, 0.0)
    assert p[0, 0] == pytest.approx(0.5)
    assert p[1, 0] == pytest.approx(0.5)
    assert p[0, 1] == pytest.approx(1.0)
    assert p[2, 1] == pytest.approx(0.0)
    assert p[0, 2] == pytest.approx(1.0 / 1024)
    assert np.allclose(p.sum(axis=0), 1.0)


def test_T0_02_transpose_counterexample():
    counts = np.zeros((1024, 1024))
    counts[0, 0] = 5.0
    counts[1, 0] = 5.0
    counts[0, 1] = 10.0
    a = mod.build_f_model(counts, 0.0)
    b = mod.build_f_model(counts.T, 0.0)
    assert not np.allclose(a, b)
    assert a[0, 0] == pytest.approx(0.5)
    assert b[0, 0] == pytest.approx(1.0 / 3.0)


def test_T0_03_pf_col_normalize_axis0():
    counts, _ = _full_tables()
    p = mod.build_f_model(counts)
    assert p.shape == (1024, 1024)
    assert np.allclose(p.sum(axis=0), 1.0, atol=1e-12)
    assert np.all(p >= 0.0)


def test_T0_04_p1_marginalize_hand_calc():
    p = np.full((1024, 1024), 1.0 / 1024)
    p[:, 0] = 0.0
    p[0, 0] = 0.5
    p[1, 0] = 0.25
    p[32, 0] = 0.125
    p[33, 0] = 0.125
    p1 = mod.marginalize_f_to_p1(p)
    assert p1.shape == (32, 1024)
    assert p1[0, 0] == pytest.approx(0.75)
    assert p1[1, 0] == pytest.approx(0.25)
    assert p1[2, 0] == pytest.approx(0.0)
    assert np.allclose(p1[:, 5], 1.0 / 32)
    assert np.allclose(p1.sum(axis=0), 1.0)


def test_T0_05_p2_conditionalize_hand_calc_and_fallback():
    p = np.full((1024, 1024), 1.0 / 1024)
    p[:, 0] = 0.0
    p[0, 0] = 0.5
    p[1, 0] = 0.25
    p[32, 0] = 0.125
    p[33, 0] = 0.125
    p2 = mod.conditionalize_f_to_p2(p)
    assert p2.shape == (32, 1024, 32)
    assert np.allclose(p2.sum(axis=2), 1.0)
    assert p2[0, 0, 0] == pytest.approx(0.5 / 0.75)
    assert p2[0, 0, 1] == pytest.approx(0.25 / 0.75)
    assert p2[1, 0, 0] == pytest.approx(0.5)
    assert p2[1, 0, 1] == pytest.approx(0.5)
    assert np.allclose(p2[7, 0, :], 1.0 / 32)


def test_T0_06_one_hot_q_recovers_oracle():
    p2 = np.full((32, 1024, 32), 1.0 / 32)
    p2[3, 7, :] = 0.0
    p2[3, 7, 5] = 1.0
    bob = np.array([7, 7])
    q = np.zeros((2, 32))
    q[:, 3] = 1.0
    app = mod.app_fed_l2_prior(p2, bob, q)
    ora = mod.oracle_l2_prior(p2, bob, np.array([3, 3]))
    assert np.allclose(app, ora, atol=1e-12)
    assert app[0, 5] == pytest.approx(1.0, abs=1e-9)
    assert "diagnostic" in mod.oracle_l2_prior.__doc__.lower()
    assert "oracle" in mod.oracle_l2_prior.__name__


def test_T0_07_q_mixture_hand_calc():
    p2 = np.full((32, 1024, 32), 1.0 / 32)
    p2[0, 0, :] = 0.0
    p2[0, 0, 0] = 1.0
    p2[1, 0, :] = 0.0
    p2[1, 0, 1] = 1.0
    q = np.zeros((1, 32))
    q[0, 0] = 0.25
    q[0, 1] = 0.75
    prior = mod.app_fed_l2_prior(p2, np.array([0]), q)
    assert prior.shape == (1, 32)
    assert prior[0, 0] == pytest.approx(0.25, abs=1e-12)
    assert prior[0, 1] == pytest.approx(0.75, abs=1e-12)
    assert prior.sum() == pytest.approx(1.0)


def test_T0_08_app_signature_rejects_alice():
    names = [p.name.lower() for p in
             inspect.signature(mod.app_fed_l2_prior).parameters.values()]
    assert not any("alice" in n or "u1_true" in n or n == "u1" for n in names)
    assert len(names) == 3


def test_T0_09_dual_floor_and_renormalize():
    assert mod.DECODER_FLOOR == 1e-15
    assert mod.AUDIT_FLOOR == 1e-300
    p2 = np.full((32, 1024, 32), 1.0 / 32)
    p2[:, 9, :] = 0.0
    q = np.full((3, 32), 1.0 / 32)
    prior = mod.app_fed_l2_prior(p2, np.array([9, 9, 9]), q)
    assert np.allclose(prior.sum(axis=1), 1.0)
    assert np.all(np.isfinite(prior))
    assert prior.min() >= 5e-16
    v = np.array([0.0, 0.5, 0.5])
    w = np.maximum(v, mod.AUDIT_FLOOR)
    w = w / w.sum()
    assert w.sum() == pytest.approx(1.0)
    assert np.all(np.isfinite(np.log2(w)))


def test_T0_10_layer_mapping_roundtrip():
    s = np.array([0, 1, 31, 32, 33, 63, 1023, 5 * 32 + 7, 31 * 32 + 31])
    u1, u2 = mod.symbols_to_layers(s)
    assert u1.tolist() == [0, 0, 0, 1, 1, 1, 31, 5, 31]
    assert u2.tolist() == [0, 1, 31, 0, 1, 31, 31, 7, 31]
    assert np.array_equal(mod.layers_to_symbols(u1, u2), s)


def test_T0_11_row_count_table():
    cases = [(mod.CE_L1_MEAN, 1.0, 782), (mod.CE_L1_MEAN, 1.05, 821),
             (mod.CE_L1_MEAN, 1.1, 860), (mod.CE_L1_MEAN, 1.2, 938),
             (mod.CE_L2_ORACLE_MEAN, 1.0, 686),
             (mod.CE_L2_ORACLE_MEAN, 1.05, 720),
             (mod.CE_L2_ORACLE_MEAN, 1.1, 755),
             (mod.CE_L2_ORACLE_MEAN, 1.2, 823)]
    for ce, f, want in cases:
        assert math.ceil(1024 * ce * f / 5) == want


def test_T0_12_seed_and_prefix_constants():
    assert mod.N == 1024
    assert mod.M_MAX == 1000
    assert mod.COLUMN_DEGREE == 3
    assert mod.L1_K_MIN == 782
    assert mod.L2_K_MIN == 686
    assert mod.L1_GRAPH_SEED == 2026090501
    assert mod.L2_GRAPH_SEED == 2026090502
    assert tuple(mod.L1_PREFIXES) == (782, 821, 860, 938)
    assert tuple(mod.L2_PREFIXES) == (686, 720, 755, 823)
    assert tuple(mod.G0_SEEDS) == tuple(range(2026090510, 2026090518))
    assert len(mod.G1_SEEDS) == 100 and mod.G1_SEEDS[0] == 2026090600
    assert mod.G1_SEEDS[-1] == 2026090699
    assert len(mod.G2_SEEDS) == 200 and mod.G2_SEEDS[0] == 2026091000
    assert mod.G2_SEEDS[-1] == 2026091199
    assert mod.LAMBDA_STAR == 137.3823795883264


def test_T0_13_degree2_impossibility_arithmetic():
    n, m = 1024, 1000
    e_full = 2 * n
    v_full = n + m
    assert e_full == 2048
    assert v_full == 2024
    assert e_full >= v_full - 1
    e_l2 = 2048 - 2 * (1000 - 686)
    assert e_l2 == 1420
    assert 1024 + 686 - 1 == 1709
    assert e_l2 < 1709
    e_l1 = 2048 - 2 * (1000 - 782)
    assert e_l1 == 1612
    assert 1024 + 782 - 1 == 1805
    assert e_l1 < 1805


def test_T0_14_dv3_capacity_arithmetic_and_blocked():
    assert 7 * 6 // 2 == 21
    assert 21 >= 12
    assert 12 >= 2 * (10 - 7)
    assert 3 * 12 >= 2 * 10
    assert 2 * 12 >= 12 + 7 - 1
    with pytest.raises(ValueError, match="DV3_SUPPORT_CAPACITY_BLOCKED"):
        mod.build_dv3_nested_support(12, 10, 5, 1)
    with pytest.raises(ValueError, match="DV3_SUPPORT_CAPACITY_BLOCKED"):
        mod.build_dv3_nested_support(12, 20, 7, 1)


def test_T0_15_small_support_shape():
    s = _small_support()
    assert s.shape == (12, 3)
    assert bool(np.all(s >= 0)) and bool(np.all(s < 10))


def test_T0_16_variable_degree3_distinct():
    s = _small_support()
    for v in range(12):
        row = [int(s[v, 0]), int(s[v, 1]), int(s[v, 2])]
        assert len(set(row)) == 3


def test_T0_17_earliest_prefix_degree2():
    h = _small_mother()
    rep = mod.audit_prefix(h, 7)
    assert rep["variable_degree_min"] >= 2
    assert rep["degree1_variables"] == 0
    assert rep["zero_columns"] == 0


def test_T0_18_suffix_degree_at_least_2():
    h = _small_mother()
    for r in range(7, 10):
        assert int(np.count_nonzero(h[r])) >= 2


def test_T0_19_all_rows_degree_at_least_2():
    h = _small_mother()
    for r in range(10):
        assert int(np.count_nonzero(h[r])) >= 2
    rep = mod.audit_prefix(h, 10)
    assert rep["zero_rows"] == 0
    assert int(np.count_nonzero(h)) == 36


def test_T0_20_unique_base_pairs():
    s = _small_support()
    pairs = [tuple(sorted((int(s[v, 0]), int(s[v, 1])))) for v in range(12)]
    assert len(set(pairs)) == 12


def test_T0_21_unique_support_triples():
    s = _small_support()
    triples = [tuple(sorted((int(s[v, 0]), int(s[v, 1]), int(s[v, 2]))))
               for v in range(12)]
    assert len(set(triples)) == 12


def test_T0_22_no_duplicate_edges():
    s = _small_support()
    h = _small_mother()
    assert int(np.count_nonzero(h)) == 36
    for v in range(12):
        assert int(np.count_nonzero(h[:, v])) == 3
    seen: set = set()
    for v in range(12):
        for j in range(3):
            key = (int(s[v, j]), v)
            assert key not in seen
            seen.add(key)
    assert len(seen) == 36


def test_T0_23_same_seed_deterministic():
    a = mod.build_dv3_nested_support(12, 10, 7, 11)
    b = mod.build_dv3_nested_support(12, 10, 7, 11)
    assert np.array_equal(a, b)
    ha = mod.assign_gf32_coefficients(a, 11, None, 10)
    hb = mod.assign_gf32_coefficients(b, 11, None, 10)
    assert np.array_equal(ha, hb)


def test_T0_24_different_seeds_differ():
    s1 = mod.build_dv3_nested_support(12, 10, 7, mod.L1_GRAPH_SEED)
    s2 = mod.build_dv3_nested_support(12, 10, 7, mod.L2_GRAPH_SEED)
    h1 = mod.assign_gf32_coefficients(s1, mod.L1_GRAPH_SEED, None, 10)
    h2 = mod.assign_gf32_coefficients(s2, mod.L2_GRAPH_SEED, None, 10)
    assert not np.array_equal(s1, s2) or not np.array_equal(h1, h2)
    rng1 = np.random.default_rng(mod.L1_GRAPH_SEED)
    rng2 = np.random.default_rng(mod.L2_GRAPH_SEED)
    assert not np.array_equal(rng1.permutation(12), rng2.permutation(12))


def test_T0_25_coeff_values_1_to_31():
    h = _small_mother()
    assert h.shape == (10, 12)
    assert h.dtype == np.uint8
    assert bool(np.all(h >= 0)) and bool(np.all(h < 32))
    s = _small_support()
    for v in range(12):
        for j in range(3):
            assert 1 <= int(h[int(s[v, j]), v]) <= 31
    mask = np.zeros_like(h, dtype=bool)
    for v in range(12):
        for j in range(3):
            mask[int(s[v, j]), v] = True
    assert bool(np.all(h[~mask] == 0))


def test_T0_26_coeff_deterministic():
    s = _small_support()
    assert np.array_equal(mod.assign_gf32_coefficients(s, 9, None, 10),
                          mod.assign_gf32_coefficients(s, 9, None, 10))


def test_T0_27_coeff_fn_does_not_call_rank():
    src = inspect.getsource(mod.assign_gf32_coefficients)
    assert "rank" not in src.lower()
    called = []
    orig = mod._gf32_rank

    def _spy(m):
        called.append(1)
        return orig(m)

    mod._gf32_rank = _spy
    try:
        mod.assign_gf32_coefficients(_small_support(), 9, None, 10)
    finally:
        mod._gf32_rank = orig
    assert called == []


def test_T0_28_coeff_fn_no_resample():
    src = inspect.getsource(mod.assign_gf32_coefficients)
    assert "resample" not in src.lower()
    s = _small_support()
    first = mod.assign_gf32_coefficients(s, 13, None, 10)
    second = mod.assign_gf32_coefficients(s, 13, None, 10)
    assert np.array_equal(first, second)


def test_T0_29_small_prefix_rank_hand_calc():
    assert mod.audit_prefix(np.diag([1, 2, 3]).astype(np.uint8), 3)["rank"] == 3
    assert mod.audit_prefix(np.array([[1, 2, 0], [2, 4, 0]],
                                     dtype=np.uint8), 2)["rank"] == 1
    assert mod.audit_prefix(np.zeros((2, 3), dtype=np.uint8), 2)["rank"] == 0


def test_T0_30_zero_row_col_detection():
    h = np.array([[1, 1, 0, 0],
                  [0, 1, 1, 0],
                  [0, 0, 0, 0]], dtype=np.uint8)
    rep = mod.audit_prefix(h, 3)
    assert rep["zero_rows"] == 1
    assert rep["zero_columns"] == 1
    assert rep["passed"] is False
    assert rep["status"] == "STRUCTURE_BLOCKED"


def test_T0_31_connected_components_hand_calc():
    h = np.array([[1, 1, 0, 0],
                  [0, 0, 1, 1]], dtype=np.uint8)
    rep = mod.audit_prefix(h, 2)
    assert rep["connected_components"] == 2
    assert rep["largest_component_fraction"] == pytest.approx(0.5)
    assert rep["isolated_variables"] == 0


def test_T0_32_four_cycle_hand_calc():
    h = np.array([[1, 1, 0],
                  [1, 2, 1]], dtype=np.uint8)
    rep = mod.audit_prefix(h, 2)
    assert rep["four_cycles"] == 1
    assert rep["four_cycle_variable_incidence_max"] == 1
    rep2 = mod.audit_prefix(np.eye(3, dtype=np.uint8), 3)
    assert rep2["four_cycles"] == 0
    assert rep2["four_cycle_variable_incidence_max"] == 0


def test_T0_33_cycle_risk_not_auto_fail():
    h = np.array([[1, 1, 0, 2],
                  [1, 2, 1, 0],
                  [0, 0, 1, 1]], dtype=np.uint8)
    rep = mod.audit_prefix(h, 3)
    assert rep["four_cycles"] == 1
    assert rep["passed"] is True
    assert rep["status"] == "STRUCTURE_PASS_WITH_CYCLE_RISK"


def test_T0_34_projective_duplicate_gf32():
    assert mod.audit_prefix(np.array([[1, 1], [1, 1]],
                                     dtype=np.uint8), 2)[
        "duplicate_projective_columns"] == 1
    assert mod.audit_prefix(np.array([[16, 5], [1, 2]],
                                     dtype=np.uint8), 2)[
        "duplicate_projective_columns"] == 1
    assert 16 * 2 != 5 and 1 * 2 == 2
    assert mod._gf32_mul_raw(16, 2) == 5
    assert mod.audit_prefix(np.array([[1, 0], [2, 1]],
                                     dtype=np.uint8), 2)[
        "duplicate_projective_columns"] == 0
    assert mod.audit_prefix(np.array([[1, 1], [2, 3]],
                                     dtype=np.uint8), 2)[
        "duplicate_projective_columns"] == 0
    assert mod.audit_prefix(np.eye(3, dtype=np.uint8), 3)[
        "duplicate_projective_columns"] == 0


def test_T0_35_broken_support_blocked():
    with pytest.raises(ValueError, match="DV3_SUPPORT_CAPACITY_BLOCKED"):
        mod.build_dv3_nested_support(12, 10, 4, 1)
    rep = mod.audit_prefix(np.zeros((3, 4), dtype=np.uint8), 3)
    assert rep["passed"] is False
    assert rep["status"] == "STRUCTURE_BLOCKED"


def test_T0_36_forbidden_row_ordering_symbol_absent():
    assert CORE_SRC.count("order_rows_for_prefix_coverage") == 0
    assert CLI_SRC.count("order_rows_for_prefix_coverage") == 0
    assert not hasattr(mod, "order_rows_for_prefix_coverage")
    tree = ast.parse(CORE_SRC)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert "order_rows_for_prefix_coverage" not in names


def test_T0_37_matched_generator_deterministic():
    _, p_b = _full_tables()
    p_f = np.full((1024, 1024), 1.0 / 1024)
    a = mod.sample_matched_block(p_b, p_f, 16, 2026090510)
    b = mod.sample_matched_block(p_b, p_f, 16, 2026090510)
    for key in ("bob", "alice", "u1", "u2"):
        assert np.array_equal(a[key], b[key])
    assert np.array_equal(a["alice"], a["u1"] * 32 + a["u2"])


def test_T0_38_no_val_file_loader():
    assert "read_CAL" not in CORE_SRC
    assert "read_VAL" not in CORE_SRC
    assert not re.search(r"def\s+load_", CORE_SRC)
    bad = [n for n in dir(mod)
           if n.startswith("load_") or n in ("read_CAL", "read_VAL")]
    assert bad == []
    assert CORE_SRC.count("open(") == 0


# --------------------------------------------------------------------------
# T1 — fake decoder only
# --------------------------------------------------------------------------
def test_T1_01_decode_fn_none_refuses():
    p_b, p_f = _tiny_tables()
    with pytest.raises((ValueError, TypeError)):
        mod.run_g0_phase(h=_tiny_h(), p_b=p_b, p_f=p_f,
                         decode_fn=None, authorized=True)
    with pytest.raises((ValueError, TypeError)):
        mod.run_g1_phase(h=_tiny_h(), p_b=p_b, p_f=p_f,
                         decode_fn=None, authorized=True)
    with pytest.raises((ValueError, TypeError)):
        mod.run_g2_phase(h=_tiny_h(), p_b=p_b, p_f=p_f,
                         decode_fn=None, authorized=True)
    with pytest.raises((ValueError, TypeError)):
        mod.run_p0_cost_phase(h=_tiny_h(), p_b=p_b, p_f=p_f,
                              decode_fn=None, authorized=True)


def test_T1_02_unauthorized_structure_refuses_before_builder(monkeypatch):
    calls = []
    orig = mod.build_dv3_nested_support

    def _spy(n, m_max, k_min, seed):
        calls.append((n, m_max, k_min, seed))
        return orig(n, m_max, k_min, seed)

    monkeypatch.setattr(mod, "build_dv3_nested_support", _spy)
    with pytest.raises(Exception):
        mod.run_structure_phase(authorized=False)
    assert calls == []


def test_T1_03_unauthorized_decoder_refuses_before_decode():
    fake = FakeDecoder()
    p_b, p_f = _tiny_tables()
    with pytest.raises(Exception):
        mod.run_g1_phase(h=_tiny_h(), p_b=p_b, p_f=p_f,
                         decode_fn=fake, authorized=False)
    assert fake.calls == []


def test_T1_04_fake_decoder_call_counts():
    p_b, p_f = _tiny_tables()
    h = _tiny_h()
    g0 = mod.run_g0_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                          authorized=True)
    assert g0["decoder_calls"] == 8
    p0 = mod.run_p0_cost_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                               authorized=True)
    assert p0["decoder_calls"] == 12
    g1 = mod.run_g1_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                          authorized=True)
    assert g1["decoder_calls"] == 440
    g2 = mod.run_g2_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                          authorized=True)
    assert g2["decoder_calls"] == 1320


def test_T1_05_structure_uses_dv3_builder(monkeypatch):
    assert "build_dv3_nested_mother" in inspect.getsource(
        mod.run_structure_phase)
    calls = []
    orig = mod.build_dv3_nested_support

    def _spy(n, m_max, k_min, seed):
        calls.append((n, m_max, k_min, seed))
        return orig(n, m_max, k_min, seed)

    monkeypatch.setattr(mod, "build_dv3_nested_support", _spy)
    keep = (mod.N, mod.M_MAX, mod.L1_K_MIN, mod.L1_PREFIXES)
    mod.N, mod.M_MAX, mod.L1_K_MIN = 12, 10, 7
    mod.L1_PREFIXES = (7, 8, 9, 10)
    try:
        res = mod.run_structure_phase(layer="L1", authorized=True)
    finally:
        mod.N, mod.M_MAX, mod.L1_K_MIN, mod.L1_PREFIXES = keep
    assert len(calls) == 1
    assert res["phase"] == "structure"


def test_T1_06_no_v31_degree2_path():
    low = CORE_SRC.lower()
    assert "v31" not in low
    assert "nonbinary_v31" not in CORE_SRC
    assert "build_candidate_mother" not in CORE_SRC
    assert not hasattr(mod, "build_candidate_mother")
    assert "build_layer" not in CORE_SRC


def test_T1_07_builder_fail_skips_audit_output(monkeypatch):
    def _fail(n, m_max, k_min, seed):
        raise ValueError("DV3_SUPPORT_CONSTRUCTION_BLOCKED: injected")

    monkeypatch.setattr(mod, "build_dv3_nested_support", _fail)
    audits = []
    orig = mod.audit_frozen_prefixes

    def _aspy(h, prefs, field=None):
        audits.append(1)
        return orig(h, prefs, field)

    monkeypatch.setattr(mod, "audit_frozen_prefixes", _aspy)
    with pytest.raises(ValueError, match="DV3_SUPPORT_CONSTRUCTION_BLOCKED"):
        mod.run_structure_phase(authorized=True)
    assert audits == []


def test_T1_08_audit_fail_blocks_g0(monkeypatch):
    entered = []
    monkeypatch.setattr(mod, "run_g0_phase",
                        lambda **kw: entered.append(kw) or {"phase": "g0"})
    keep = (mod.N, mod.M_MAX, mod.L1_K_MIN, mod.L1_PREFIXES)
    mod.N, mod.M_MAX, mod.L1_K_MIN = 12, 10, 7
    mod.L1_PREFIXES = (7, 8, 9, 10)
    try:
        res = mod.run_structure_phase(h=np.zeros((10, 12), dtype=np.uint8),
                                      authorized=True)
    finally:
        mod.N, mod.M_MAX, mod.L1_K_MIN, mod.L1_PREFIXES = keep
    assert res["passed"] is False
    assert res["status"] == "STRUCTURE_BLOCKED"
    assert res["decoder_calls"] == 0
    assert entered == []


def test_T1_09_g0_does_not_chain_next_phases(monkeypatch):
    for name in ("run_p0_cost_phase", "run_g1_phase", "run_g2_phase"):
        monkeypatch.setattr(mod, name, _boom(name))
    p_b, p_f = _tiny_tables()
    res = mod.run_g0_phase(h=_tiny_h(), p_b=p_b, p_f=p_f,
                           decode_fn=FakeDecoder(), authorized=True)
    assert res["phase"] == "g0"


def test_T1_10_g1_does_not_chain_g2(monkeypatch):
    monkeypatch.setattr(mod, "run_g2_phase", _boom("run_g2_phase"))
    p_b, p_f = _tiny_tables()
    res = mod.run_g1_phase(h=_tiny_h(), p_b=p_b, p_f=p_f,
                           decode_fn=FakeDecoder(), authorized=True)
    assert res["phase"] == "g1"


def test_T1_11_phase_output_fields_complete(monkeypatch):
    p_b, p_f = _tiny_tables()
    h = _tiny_h()
    fake = FakeDecoder()
    keep = (mod.N, mod.M_MAX, mod.L1_K_MIN, mod.L1_PREFIXES)
    mod.N, mod.M_MAX, mod.L1_K_MIN = 12, 10, 7
    mod.L1_PREFIXES = (7, 8, 9, 10)
    try:
        st = mod.run_structure_phase(authorized=True)
    finally:
        mod.N, mod.M_MAX, mod.L1_K_MIN, mod.L1_PREFIXES = keep
    for key in ("phase", "layer", "m_max", "n", "prefix_rows",
                "per_prefix", "passed", "status", "decoder_calls"):
        assert key in st
    assert len(st["per_prefix"]) == 4
    for rep in st["per_prefix"]:
        for key in ("prefix_rows", "total_edges", "rank", "zero_rows",
                    "zero_columns", "variable_degree_min",
                    "variable_degree_median", "variable_degree_max",
                    "degree1_variables", "degree2_variables",
                    "degree3_variables", "connected_components",
                    "largest_component_fraction", "isolated_variables",
                    "row_degree_histogram", "four_cycles",
                    "four_cycle_variable_incidence_max",
                    "duplicate_projective_columns", "base_pair_duplicates",
                    "support_triple_duplicates", "coefficients_nonzero",
                    "passed", "status"):
            assert key in rep
    g0 = mod.run_g0_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=fake,
                          authorized=True)
    for key in ("phase", "marginal_err", "conditional_err", "chain_err",
                "attempted_blocks", "exact_count", "exact_failure_fraction",
                "decoder_calls", "passed"):
        assert key in g0
    p0 = mod.run_p0_cost_phase(h=h, p_b=p_b, p_f=p_f,
                               decode_fn=FakeDecoder(), authorized=True)
    for key in ("phase", "block_length", "f_list", "records",
                "decoder_calls", "projected_g1_s", "projected_g2_s",
                "projection_blocked", "passed"):
        assert key in p0
    assert len(p0["records"]) == 4
    g1 = mod.run_g1_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                          authorized=True)
    for key in ("phase", "block_length", "f_list", "frozen_rows", "per_f",
                "monotonic", "crashes", "nonfinite", "decoder_calls",
                "passed"):
        assert key in g1
    assert g1["frozen_rows"]["1.0"] == {"m1": 49, "m2": 43}
    g2 = mod.run_g2_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                          authorized=True)
    for key in ("phase", "block_length", "f_list", "frozen_rows", "per_f",
                "monotonic", "crashes", "nonfinite", "decoder_calls",
                "grade", "passed"):
        assert key in g2
    assert g2["frozen_rows"]["1.2"] == {"m1": 235, "m2": 206}
    assert g2["grade"] == "G2_CURRENT_CONFIGURATION_FAILED"


def test_T1_12_no_raw_arrays_saved(tmp_path, monkeypatch):
    for src in (CORE_SRC, CLI_SRC):
        for frag in ("write_text", "write_bytes", "np.save", "np.savez",
                     "to_csv", "to_parquet", "pickle", "mkdir"):
            assert frag not in src
        assert not re.search(r"open\([^)]*['\"]w", src)
    p_b, p_f = _tiny_tables()
    h = _tiny_h()
    monkeypatch.chdir(tmp_path)
    keep = (mod.N, mod.M_MAX, mod.L1_K_MIN, mod.L1_PREFIXES)
    mod.N, mod.M_MAX, mod.L1_K_MIN = 12, 10, 7
    mod.L1_PREFIXES = (7, 8, 9, 10)
    try:
        mod.run_structure_phase(authorized=True)
    finally:
        mod.N, mod.M_MAX, mod.L1_K_MIN, mod.L1_PREFIXES = keep
    mod.run_g0_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                     authorized=True)
    mod.run_p0_cost_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                          authorized=True)
    mod.run_g1_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                     authorized=True)
    mod.run_g2_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                     authorized=True)
    assert list(tmp_path.rglob("*")) == []
    for fn in PHASE_FUNCS:
        params = {p.name for p in
                  inspect.signature(getattr(mod, fn)).parameters.values()}
        assert not (params & {"out_dir", "path", "run_id", "output", "save"})


def test_T1_13_no_production_decoder_import():
    for src in (CORE_SRC.lower(), CLI_SRC.lower()):
        for frag in ("v35", "production_decoder", "fftqspa",
                     "decode_row_layered"):
            assert frag not in src
    for src in (CORE_SRC, CLI_SRC):
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = " ".join(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names = node.module or ""
            else:
                continue
            low = names.lower()
            assert "v35" not in low and "fftqspa" not in low
            assert "production_decoder" not in low
    _block_import_smoke()


def _block_import_smoke():
    blocked = ("v35", "production_decoder", "fftqspa")

    class Blocker:
        def find_spec(self, name, path=None, target=None):
            if any(f in name.lower() for f in blocked):
                raise ImportError(f"blocked decoder-side import: {name}")
            return None

    sys.meta_path.insert(0, Blocker())
    try:
        for tag, path in (("t1_core", CORE_PATH), ("t1_cli", CLI_PATH)):
            spec = importlib.util.spec_from_file_location(tag, str(path))
            assert spec is not None and spec.loader is not None
            fresh = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fresh)
    finally:
        sys.meta_path[:] = [f for f in sys.meta_path
                            if not isinstance(f, Blocker)]


def test_T1_14_no_data_reads():
    for src in (CORE_SRC, CLI_SRC):
        for frag in ("parquet", "np.load", "loadtxt", "genfromtxt",
                     "read_bytes", "pd.read", "csv.reader"):
            assert frag not in src
    assert CORE_SRC.count("open(") == 0
    assert CLI_SRC.count("open(") == 1
    assert "cycle_state" in CLI_SRC
    for fn in PHASE_FUNCS:
        params = {p.name for p in
                  inspect.signature(getattr(mod, fn)).parameters.values()}
        assert not (params & {"path", "file", "csv", "parquet", "dir",
                              "root", "output"})


def test_T1_15_cli_missing_phase_refuses():
    r = subprocess.run([sys.executable, str(CLI_PATH)],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode != 0


def test_T1_16_cli_illegal_phase_refuses():
    r = subprocess.run([sys.executable, str(CLI_PATH), "--phase", "all"],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode != 0
    h = subprocess.run([sys.executable, str(CLI_PATH), "--phase", "g1",
                        "--help"], capture_output=True, text=True,
                       timeout=120)
    assert "run_01" not in h.stdout
    assert "--real" not in h.stdout
    r2 = subprocess.run([sys.executable, str(CLI_PATH), "--phase",
                         "structure"], capture_output=True, text=True,
                        timeout=120)
    assert r2.returncode != 0


def test_T1_17_cli_forbids_frozen_param_override():
    h = subprocess.run([sys.executable, str(CLI_PATH), "--help"],
                       capture_output=True, text=True, timeout=120)
    out = h.stdout + h.stderr
    for frag in ("--seed", "--degree", "--family", "--k_min", "--m_max",
                 "--retry", "--real", "--run_01", "--VAL", "--all"):
        assert frag not in out
    for frag in ("--seed", "--degree", "--family", "k_min", "m_max"):
        assert frag not in CLI_SRC


def test_T1_18_cli_no_family_retry():
    low = CLI_SRC.lower()
    assert "family" not in low
    assert "retry" not in low
    assert "seed-list" not in low and "seed_list" not in low
    out = subprocess.run([sys.executable, str(CLI_PATH), "--help"],
                         capture_output=True, text=True,
                         timeout=120).stdout
    assert "family" not in out.lower()
    assert "retry" not in out.lower()


def test_T1_19_current_cycle_phases_all_unauthorized():
    state = cli._load_state(STATE_PATH)
    for key in ("structure_execution_authorized", "g0_execution_authorized",
                "p0_cost_execution_authorized", "g1_execution_authorized",
                "g2_execution_authorized"):
        assert key in state
        assert state[key] is False
    for phase in ("structure", "g0", "p0-cost", "g1", "g2"):
        assert mod.is_phase_authorized(state, phase) is False


def test_T1_20_no_workspace_or_production_output(tmp_path, monkeypatch):
    p_b, p_f = _tiny_tables()
    h = _tiny_h()
    monkeypatch.chdir(tmp_path)
    mod.run_g0_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                     authorized=True)
    mod.run_g1_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                     authorized=True)
    assert list(tmp_path.rglob("*")) == []
    assert list((ROOT / "workspace").glob("v72p2d5_*")) == []
    assert list((ROOT / "comparison_bench" / "outputs_comparison").glob(
        "v72p2d5_*")) == []
    cyc = ROOT / "docs" / "research_cycles" / "V72P2D5-GF32-RATE-MOTHER"
    assert not (cyc / "run_01").exists()


def test_T1_21_no_hash_checksum_tag():
    for src in (CORE_SRC.lower(), CLI_SRC.lower()):
        for frag in ("hashlib", "sha256", "sha512", "sha1", "md5",
                     "checksum", "hmac", "blake2"):
            assert frag not in src
    p_b, p_f = _tiny_tables()
    h = _tiny_h()
    keep = (mod.N, mod.M_MAX, mod.L1_K_MIN, mod.L1_PREFIXES)
    mod.N, mod.M_MAX, mod.L1_K_MIN = 12, 10, 7
    mod.L1_PREFIXES = (7, 8, 9, 10)
    try:
        results = [
            mod.run_structure_phase(authorized=True),
            mod.run_g0_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                             authorized=True),
            mod.run_g2_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                             authorized=True),
        ]
    finally:
        mod.N, mod.M_MAX, mod.L1_K_MIN, mod.L1_PREFIXES = keep
    frags = ("hash", "checksum", "hmac", "sha256", "md5", "signature",
             "tag")
    stack = list(results)
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                assert not any(f in str(k).lower() for f in frags)
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)


def test_T1_22_openspec_history_zero_mod():
    clean_paths = ["openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan",
                   "docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/PLAN_CORRIGENDUM_R2.md",
                   "docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/PLAN_REVIEW_VERDICT_R2.md",
                   "docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/IMPLEMENTATION_PACKET_R2.md",
                   "src", "experiments", "tools", "results"]
    r = subprocess.run(["git", "status", "--porcelain", "--"] + clean_paths,
                       capture_output=True, text=True, timeout=120,
                       cwd=str(ROOT))
    assert r.returncode == 0
    assert r.stdout.strip() == ""
    test_src = Path(__file__).read_text(encoding="utf-8")
    banned_calls = {"write_text", "write_bytes", "save", "savez", "to_csv",
                    "to_parquet", "dump", "mkdir", "remove", "unlink",
                    "rmtree", "rename", "replace", "touch"}
    tree = ast.parse(test_src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id != "open"
            elif isinstance(func, ast.Attribute):
                assert func.attr not in banned_calls
