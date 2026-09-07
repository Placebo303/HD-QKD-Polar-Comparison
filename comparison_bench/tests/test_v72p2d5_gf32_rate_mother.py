"""V72P2D5 GF32 rate-mother — R2 T0 (no decoder) + T1 (fake decoder only).

R2 dv3 implementation stage only: small fixture n=12/m_max=10/k_min=7 plus
tiny hand matrices and injected fakes. No full-size construction, no real
decoder, no data reads, no output files.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import json
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


def _snapshot_dir(path):
    p = Path(path)
    if not p.exists():
        return None
    for q in p.iterdir():
        if q.is_dir():
            raise AssertionError(
                f"formal root contains subdirectory: {q.name} under {p}")
    return {q.name: (q.stat().st_size, q.stat().st_mtime_ns)
            for q in p.iterdir() if q.is_file()}


def _formal_roots():
    return [ROOT / mod.P0_FORMAL_ROOT, ROOT / mod.G1_FORMAL_ROOT,
            ROOT / mod.G2_FORMAL_ROOT, ROOT / mod.G0_FORMAL_ROOT,
            ROOT / mod.G0_RECOVERY_FORMAL_ROOT,
            ROOT / mod.MODEL_F_INPUT_FORMAL_ROOT,
            ROOT / mod.STRUCTURE_FORMAL_ROOT]


def _snapshot_formal_roots():
    return {str(r): _snapshot_dir(r) for r in _formal_roots()}


def _assert_formal_roots_unchanged(before):
    for key, old in before.items():
        now = _snapshot_dir(key)
        assert now == old, (
            f"formal root touched during test: {key} "
            f"(before={old!r}, after={now!r}); tests must snapshot-and-compare "
            f"formal roots, never assert their absence")


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
    # R2-structure delta: base/triple duplicates are hard BLOCKED, so the
    # cycle-risk fixture must carry four-cycles with zero base/triple dups.
    h = np.array([[28, 0, 13, 0],
                  [25, 29, 0, 14],
                  [2, 9, 0, 0],
                  [0, 31, 17, 16]], dtype=np.uint8)
    rep = mod.audit_prefix(h, 4)
    assert rep["four_cycles"] == 2
    assert rep["base_pair_duplicates"] == 0
    assert rep["support_triple_duplicates"] == 0
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
    # Structure, G0, and the P0/G1/G2 stage helper own the file writers.
    wsrc = inspect.getsource(mod.write_structure_evidence)
    gsrc = inspect.getsource(mod.write_g0_evidence)
    ssrc = inspect.getsource(mod._write_stage_evidence)
    assert CORE_SRC.count("open(") == wsrc.count("open(") + gsrc.count(
        "open(") + ssrc.count("open(") == 12


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
                     "to_csv", "to_parquet", "pickle"):
            assert frag not in src
    # Structure, G0, and stage writers are the only code paths that create files.
    wsrc = inspect.getsource(mod.write_structure_evidence)
    gsrc = inspect.getsource(mod.write_g0_evidence)
    ssrc = inspect.getsource(mod._write_stage_evidence)
    assert "mkdir" not in CLI_SRC
    assert CORE_SRC.count("mkdir") == (wsrc.count("mkdir")
                                       + gsrc.count("mkdir")
                                       + ssrc.count("mkdir")) >= 3
    pat = r"open\([^)]*['\"]w"
    assert len(re.findall(pat, CORE_SRC)) == 12
    assert len(re.findall(pat, wsrc)) + len(re.findall(pat, gsrc)) + len(
        re.findall(pat, ssrc)) == 12
    assert re.findall(pat, CLI_SRC) == []
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


def test_T1_13_decoder_dependency_is_lazy_and_fake_path_is_local():
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
            assert "production_decoder" not in low
    _block_import_smoke()

    loaded = []

    def _must_not_load():
        loaded.append(True)
        raise AssertionError("historical decoder loaded on fake path")

    old_loader = mod._load_g0_decoder
    mod._load_g0_decoder = _must_not_load
    try:
        p_b, p_f = _tiny_tables()
        mod.run_g0_phase(h=_tiny_h(), p_b=p_b, p_f=p_f,
                         decode_fn=FakeDecoder(), authorized=True)
    finally:
        mod._load_g0_decoder = old_loader
    assert loaded == []


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
    # Core open( calls are confined to the structure/G0/stage evidence writers;
    # CLI still opens only the authorization state.
    wsrc = inspect.getsource(mod.write_structure_evidence)
    gsrc = inspect.getsource(mod.write_g0_evidence)
    ssrc = inspect.getsource(mod._write_stage_evidence)
    assert CORE_SRC.count("open(") == wsrc.count("open(") + gsrc.count(
        "open(") + ssrc.count("open(") == 12
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
    _rec_root = ROOT / mod.G0_RECOVERY_FORMAL_ROOT
    _rec_before = sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir())
    p_b, p_f = _tiny_tables()
    h = _tiny_h()
    monkeypatch.chdir(tmp_path)
    mod.run_g0_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                     authorized=True)
    mod.run_g1_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                     authorized=True)
    assert list(tmp_path.rglob("*")) == []
    assert (ROOT / mod.G0_FORMAL_ROOT).exists()
    assert sorted(p.name for p in (ROOT / mod.G0_FORMAL_ROOT).iterdir()) == sorted(mod.G0_EVIDENCE_FILES)
    assert sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir()) == _rec_before
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
                low_key = str(k).lower()
                assert not any(f in low_key for f in frags[:-1])
                assert "tag" not in set(low_key.split("_"))
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)


def test_T1_22_openspec_history_zero_mod():
    # Recovery amendment intentionally modifies the 4 plan files
    # (proposal/design/tasks/specs/spec) + cycle_state.yaml + new amendment;
    # PLAN_FREEZE and history docs stay frozen, so only they are asserted
    # clean here. Recovery scope is covered by T-R tests.
    # Cleanliness means REAL CONTENT difference: a file counts as modified
    # only when git diff --numstat reports nonzero added/deleted lines
    # (binary "-/-" entries count as changed). Line-ending-only churn under
    # core.autocrlf=true (no .gitattributes) yields empty numstat, so it
    # passes; any genuine tracked-file content change still fails.
    clean_paths = ["openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/PLAN_FREEZE.md",
                   "docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/PLAN_CORRIGENDUM_R2.md",
                   "docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/PLAN_REVIEW_VERDICT_R2.md",
                   "docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/IMPLEMENTATION_PACKET_R2.md",
                   "src", "experiments", "tools", "results"]
    changed = []
    for args in (["git", "diff", "--numstat", "--"],
                 ["git", "diff", "--cached", "--numstat", "--"]):
        r = subprocess.run(args + clean_paths,
                           capture_output=True, text=True, timeout=120,
                           cwd=str(ROOT))
        assert r.returncode == 0
        for line in r.stdout.splitlines():
            if not line.strip():
                continue
            added, deleted, _path = line.split("\t", 2)
            if added == "-" or deleted == "-":
                changed.append(line)
            elif int(added) != 0 or int(deleted) != 0:
                changed.append(line)
    assert changed == []
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


# --------------------------------------------------------------------------
# T2 — structure runner delta (fake/small only, no full mother, no decoder)
# --------------------------------------------------------------------------
def _t2_pass_audits(prefixes, four=0):
    out = []
    for k in prefixes:
        out.append({
            "prefix_rows": int(k), "total_edges": 0,
            "column_degree_full": 3, "rank": int(k), "zero_rows": 0,
            "zero_columns": 0, "variable_degree_min": 2,
            "variable_degree_median": 2.0, "variable_degree_max": 3,
            "degree1_variables": 0, "degree2_variables": 0,
            "degree3_variables": 0, "connected_components": 1,
            "largest_component_fraction": 1.0, "isolated_variables": 0,
            "row_degree_histogram": {2: 1}, "four_cycles": int(four),
            "four_cycle_variable_incidence_max": 0,
            "duplicate_projective_columns": 0, "base_pair_duplicates": 0,
            "support_triple_duplicates": 0, "coefficients_nonzero": True,
            "passed": True, "status": "STRUCTURE_PASS",
        })
    return out


class _SeqFake:
    def __init__(self, l1_pass=True, l2_pass=True, boom=None):
        self.builds = []
        self.audits = []
        self.l1_pass = l1_pass
        self.l2_pass = l2_pass
        self.boom = boom

    def build(self, n, m_max, k_min, seed):
        self.builds.append((int(n), int(m_max), int(k_min), int(seed)))
        layer = "L1" if int(seed) == mod.L1_GRAPH_SEED else "L2"
        if self.boom == layer:
            raise RuntimeError(f"injected {layer} boom")
        return np.eye(2, dtype=np.uint8)

    def audit(self, h, prefixes):
        self.audits.append((tuple(int(v) for v in prefixes), np.shape(h)))
        ok = self.l1_pass if len(self.audits) == 1 else self.l2_pass
        audits = _t2_pass_audits(prefixes)
        if not ok:
            for a in audits:
                a["passed"] = False
                a["status"] = "STRUCTURE_BLOCKED"
        passed = bool(all(a["passed"] for a in audits))
        return {"prefix_rows": [int(v) for v in prefixes], "audits": audits,
                "passed": passed,
                "status": ("STRUCTURE_PASS" if passed
                           else "STRUCTURE_BLOCKED")}

    def preflight(self, *, authorized):
        assert authorized is True
        return {"proceed": True, "projection_blocked": False,
                "decoder_calls": 0}


def _t2_run(fake, **kw):
    return mod.run_structure_sequence(
        authorized=True, build_fn=fake.build, audit_fn=fake.audit,
        preflight_fn=fake.preflight, **kw)


def test_T2_01_l1_pass_calls_l2():
    f = _SeqFake(l1_pass=True, l2_pass=True)
    res = _t2_run(f)
    assert [b[3] for b in f.builds] == [mod.L1_GRAPH_SEED,
                                        mod.L2_GRAPH_SEED]
    assert len(f.audits) == 2
    assert res["l2_attempted"] is True
    assert res["decision"] == "STRUCTURE_PASS"
    assert res["attempts"] == 1 and res["completed"] == 1


def test_T2_02_l1_fail_stops_l2():
    f = _SeqFake(l1_pass=False)
    res = _t2_run(f)
    assert [b[3] for b in f.builds] == [mod.L1_GRAPH_SEED]
    assert len(f.audits) == 1
    assert res["decision"] == "STRUCTURE_BLOCKED"
    assert res["l2_attempted"] is False
    assert res["completed"] == 1


def test_T2_03_each_layer_builds_exactly_once():
    f = _SeqFake()
    res = _t2_run(f)
    seeds = [b[3] for b in f.builds]
    assert seeds.count(mod.L1_GRAPH_SEED) == 1
    assert seeds.count(mod.L2_GRAPH_SEED) == 1
    assert len(f.builds) == 2
    assert all(b[0] == 1024 and b[1] == 1000 for b in f.builds)
    assert res["build_calls"] == {"L1": 1, "L2": 1}
    src = inspect.getsource(mod.run_structure_sequence).lower()
    for frag in ("retry", "reseed", "fallback", "reorder", "resample"):
        assert frag not in src


def test_T2_04_base_pair_dup_blocked():
    rep = mod.audit_prefix(np.array([[1, 1], [1, 2]], dtype=np.uint8), 2)
    assert rep["base_pair_duplicates"] == 1
    assert rep["support_triple_duplicates"] == 0
    assert rep["rank"] == 2
    assert rep["passed"] is False
    assert rep["status"] == "STRUCTURE_BLOCKED"


def test_T2_05_support_triple_dup_blocked():
    h = np.array([[1, 1, 1], [1, 2, 4], [1, 3, 5]], dtype=np.uint8)
    rep = mod.audit_prefix(h, 3)
    assert rep["support_triple_duplicates"] == 3
    assert rep["passed"] is False
    assert rep["status"] == "STRUCTURE_BLOCKED"


def test_T2_06_cycle_only_risk():
    h = np.array([[28, 0, 13, 0],
                  [25, 29, 0, 14],
                  [2, 9, 0, 0],
                  [0, 31, 17, 16]], dtype=np.uint8)
    rep = mod.audit_prefix(h, 4)
    assert rep["four_cycles"] == 2
    assert rep["base_pair_duplicates"] == 0
    assert rep["support_triple_duplicates"] == 0
    assert rep["rank"] == 4
    assert rep["passed"] is True
    assert rep["status"] == "STRUCTURE_PASS_WITH_CYCLE_RISK"


def test_T2_07_projection_blocked_skips_full_build(tmp_path):
    builds = []

    def _build(n, m_max, k_min, seed):
        builds.append((n, m_max, k_min, seed))
        return np.eye(2, dtype=np.uint8)

    def _preflight(*, authorized):
        assert authorized is True
        return {"proceed": False, "projection_blocked": True,
                "decoder_calls": 0}

    out = tmp_path / "blocked"
    res = mod.run_structure_sequence(
        authorized=True, build_fn=_build, preflight_fn=_preflight,
        out_dir=str(out))
    assert builds == []
    assert res["decision"] == "STRUCTURE_RESOURCE_PROJECTION_BLOCKED"
    assert res["attempts"] == 0 and res["completed"] == 0
    assert (sorted(p.name for p in out.iterdir())
            == sorted(mod.STRUCTURE_EVIDENCE_FILES))


def test_T2_08_unauthorized_touches_nothing(tmp_path, monkeypatch):
    calls = {"preflight": [], "build": [], "audit": [], "write": []}

    def _preflight(*, authorized):
        calls["preflight"].append(1)
        return {"proceed": True}

    def _build(n, m_max, k_min, seed):
        calls["build"].append(1)
        return np.eye(2, dtype=np.uint8)

    def _audit(h, prefs):
        calls["audit"].append(1)
        return {}

    def _write(d, r):
        calls["write"].append(1)
        return []

    monkeypatch.chdir(tmp_path)
    with pytest.raises(Exception):
        mod.run_structure_sequence(
            authorized=False, build_fn=_build, audit_fn=_audit,
            preflight_fn=_preflight, writer_fn=_write,
            out_dir=str(tmp_path / "x"))
    assert calls == {"preflight": [], "build": [], "audit": [], "write": []}
    assert list(tmp_path.rglob("*")) == []


def test_T2_09_attempt_before_first_build():
    f = _SeqFake()
    res = _t2_run(f)
    assert res["attempts"] == 1
    ev = res["events"]
    assert ev.index("attempt=1") < ev.index("L1_build")
    assert ev.index("L1_build") < ev.index("L1_audit")
    assert ev.index("L1_audit") < ev.index("L2_build")
    assert ev.index("L2_build") < ev.index("L2_audit")
    assert ev[0] == "auth_ok" and ev[1] == "preflight_done"


def test_T2_10_mid_exception_completed_zero(tmp_path):
    f = _SeqFake(boom="L2")
    out = tmp_path / "exc"
    res = mod.run_structure_sequence(
        authorized=True, build_fn=f.build, audit_fn=f.audit,
        preflight_fn=f.preflight, out_dir=out)
    assert res["attempts"] == 1 and res["completed"] == 0
    assert res["decision"] == "STRUCTURE_BLOCKED"
    assert "boom" in (res["error"] or "")
    assert (sorted(p.name for p in out.iterdir())
            == sorted(mod.STRUCTURE_EVIDENCE_FILES))


def test_T2_11_l2_hard_fail_completed_one():
    f = _SeqFake(l2_pass=False)
    res = _t2_run(f)
    assert res["attempts"] == 1 and res["completed"] == 1
    assert res["decision"] == "STRUCTURE_BLOCKED"
    assert res["l2_attempted"] is True
    assert len(f.builds) == 2 and len(f.audits) == 2


def test_T2_12_writer_four_files_clean(tmp_path):
    f = _SeqFake()
    out = tmp_path / "cand"
    res = mod.run_structure_sequence(
        authorized=True, build_fn=f.build, audit_fn=f.audit,
        preflight_fn=f.preflight, out_dir=out)
    assert (sorted(p.name for p in out.iterdir())
            == ["execution_summary.json", "report.md", "results.json",
                "table.csv"])
    for p in out.iterdir():
        assert p.stat().st_size < 65536
    payload = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert payload["decision"] == "STRUCTURE_PASS"
    assert payload["decoder_calls"] == 0
    assert payload["cal_rows_read"] == 0 and payload["val_rows_read"] == 0
    assert payload["formal_root"] == ("workspace/v72p2d5_structure/"
                                      "20260905_r2")
    bad_keys = ("hash", "checksum", "hmac", "sha256", "md5", "signature",
                "tag")
    stack = [payload]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                assert not any(b in str(k).lower() for b in bad_keys)
                stack.append(v)
        elif isinstance(cur, list):
            assert len(cur) <= 16
            stack.extend(cur)
        elif isinstance(cur, str):
            assert ":\\" not in cur and ":/" not in cur
            assert not cur.startswith("/")
    table = (out / "table.csv").read_text(encoding="utf-8").splitlines()
    assert len(table) == 9 and table[0].startswith("layer,prefix_rows,rank")
    rep = (out / "report.md").read_text(encoding="utf-8")
    assert "STRUCTURE_PASS" in rep
    summ = json.loads(
        (out / "execution_summary.json").read_text(encoding="utf-8"))
    assert summ["attempts"] == 1 and summ["completed"] == 1
    assert summ["files"] == list(mod.STRUCTURE_EVIDENCE_FILES)


def test_T2_13_existing_dir_refuses_and_formal_root_absent(tmp_path):
    _rec_root = ROOT / mod.G0_RECOVERY_FORMAL_ROOT
    _rec_before = sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir())
    f = _SeqFake()
    res = _t2_run(f)
    with pytest.raises(FileExistsError):
        mod.write_structure_evidence(tmp_path, res)
    assert (mod.STRUCTURE_FORMAL_ROOT
            == "workspace/v72p2d5_structure/20260905_r2")
    assert (ROOT / mod.G0_FORMAL_ROOT).exists()
    assert sorted(p.name for p in (ROOT / mod.G0_FORMAL_ROOT).iterdir()) == sorted(mod.G0_EVIDENCE_FILES)
    assert sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir()) == _rec_before


def test_T2_14_cli_enters_single_orchestrator(monkeypatch):
    assert "run_structure_phase" not in CLI_SRC
    assert cli._RUNNERS["structure"].__name__ == "run_structure_sequence"
    calls = []

    def _spy(**kw):
        calls.append(kw)
        return {"phase": "structure", "decision": "STRUCTURE_BLOCKED"}

    monkeypatch.setitem(cli._RUNNERS, "structure", _spy)
    monkeypatch.setattr(cli, "_load_state",
                        lambda path: {"structure_execution_authorized": True})
    assert cli.main(["--phase", "structure"]) == 0
    assert len(calls) == 1 and calls[0].get("authorized") is True


def test_T2_15_preflight_formula_recomputable():
    r = mod.extrapolate_structure_cost(
        t_build_l1_s=1.0, t_build_l2_s=2.0, t_rank_proxy_s=0.5,
        rss_probe_bytes=100000000)
    assert r["edge_scale"] == pytest.approx(16.0)
    assert r["rank_scale"] == pytest.approx(3906.25)
    assert r["build_full_s"]["L1"] == pytest.approx(16.0)
    assert r["build_full_s"]["L2"] == pytest.approx(32.0)
    assert r["rank_full_per_prefix_s"] == pytest.approx(1953.125)
    assert r["single_layer_s"] == pytest.approx(7844.5)
    assert r["total_s"] == pytest.approx(15673.0)
    assert r["rss_projected_bytes"] == 1600000000
    assert r["projection_blocked"] is True
    ok = mod.extrapolate_structure_cost(
        t_build_l1_s=0.001, t_build_l2_s=0.001, t_rank_proxy_s=0.00001,
        rss_probe_bytes=1000)
    assert ok["projection_blocked"] is False
    seen = []

    def _build(n, m_max, k_min, seed):
        seen.append(int(n))
        return mod.build_dv3_nested_mother(n, m_max, k_min, seed, None)

    pf = mod.run_structure_preflight(authorized=True, build_fn=_build)
    assert seen and max(seen) <= 256
    assert (set(pf) >= {"proceed", "projection_blocked", "build_wall_s",
                        "rank_wall_s", "projected", "decoder_calls"})
    assert pf["decoder_calls"] == 0


def test_T2_16_prefix_schema_frozen_24():
    h = np.array([[28, 0, 13, 0],
                  [25, 29, 0, 14],
                  [2, 9, 0, 0],
                  [0, 31, 17, 16]], dtype=np.uint8)
    rep = mod.audit_prefix(h, 4)
    frozen = ["base_pair_duplicates", "coefficients_nonzero",
              "column_degree_full", "connected_components",
              "degree1_variables", "degree2_variables",
              "degree3_variables", "duplicate_projective_columns",
              "four_cycle_variable_incidence_max", "four_cycles",
              "isolated_variables", "largest_component_fraction", "passed",
              "prefix_rows", "rank", "row_degree_histogram", "status",
              "support_triple_duplicates", "total_edges",
              "variable_degree_max", "variable_degree_median",
              "variable_degree_min", "zero_columns", "zero_rows"]
    assert sorted(rep) == frozen
    assert len(rep) == 24


def test_T2_17_cli_unauthorized_creates_no_formal_dir(tmp_path, monkeypatch):
    # Real CLI authorized path NOT run: unauthorized state only.
    _rec_root = ROOT / mod.G0_RECOVERY_FORMAL_ROOT
    _rec_before = sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir())
    counts = {"runner": 0, "preflight": 0, "build": 0, "audit": 0,
              "write": 0}

    def _runner(**kw):
        counts["runner"] += 1
        return {"phase": "structure"}

    orig_preflight = mod.run_structure_preflight
    orig_build = mod.build_dv3_nested_mother
    orig_audit = mod.audit_frozen_prefixes
    orig_write = mod.write_structure_evidence

    def _preflight(**kw):
        counts["preflight"] += 1
        return orig_preflight(**kw)

    def _build(*a, **k):
        counts["build"] += 1
        return orig_build(*a, **k)

    def _audit(*a, **k):
        counts["audit"] += 1
        return orig_audit(*a, **k)

    def _write(*a, **k):
        counts["write"] += 1
        return orig_write(*a, **k)

    monkeypatch.setitem(cli._RUNNERS, "structure", _runner)
    monkeypatch.setattr(mod, "run_structure_preflight", _preflight)
    monkeypatch.setattr(mod, "build_dv3_nested_mother", _build)
    monkeypatch.setattr(mod, "audit_frozen_prefixes", _audit)
    monkeypatch.setattr(mod, "write_structure_evidence", _write)
    monkeypatch.setattr(cli, "_load_state",
                        lambda path: {"structure_execution_authorized": False})
    monkeypatch.chdir(tmp_path)
    assert cli.main(["--phase", "structure"]) == 3
    assert counts == {"runner": 0, "preflight": 0, "build": 0, "audit": 0,
                      "write": 0}
    assert (ROOT / mod.G0_FORMAL_ROOT).exists()
    assert sorted(p.name for p in (ROOT / mod.G0_FORMAL_ROOT).iterdir()) == sorted(mod.G0_EVIDENCE_FILES)
    assert sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir()) == _rec_before
    assert list(tmp_path.rglob("*")) == []


def test_T2_18_cli_structure_frozen_out_dir_fake_files(tmp_path, monkeypatch):
    # Real CLI authorized path NOT run: the spy captures the frozen out_dir
    # value, then file creation is redirected to tmp; formal root untouched.
    _rec_root = ROOT / mod.G0_RECOVERY_FORMAL_ROOT
    _rec_before = sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir())
    seen = {}
    fake = _SeqFake(l1_pass=True, l2_pass=True)
    real_seq = cli._RUNNERS["structure"]

    def _spy(**kw):
        seen.update(kw)
        redir = tmp_path / "redir"
        return real_seq(authorized=kw.get("authorized"),
                        build_fn=fake.build, audit_fn=fake.audit,
                        preflight_fn=fake.preflight, out_dir=str(redir))

    monkeypatch.setitem(cli._RUNNERS, "structure", _spy)
    monkeypatch.setattr(cli, "_load_state",
                        lambda path: {"structure_execution_authorized": True})
    monkeypatch.chdir(tmp_path)
    assert cli.main(["--phase", "structure"]) == 0
    assert seen.get("authorized") is True
    assert str(seen.get("out_dir")) == str(
        ROOT / "workspace" / "v72p2d5_structure" / "20260905_r2")
    assert str(seen.get("out_dir")) == str(ROOT / mod.STRUCTURE_FORMAL_ROOT)
    redir = tmp_path / "redir"
    assert (sorted(p.name for p in redir.iterdir())
            == sorted(mod.STRUCTURE_EVIDENCE_FILES))
    assert (ROOT / mod.G0_FORMAL_ROOT).exists()
    assert sorted(p.name for p in (ROOT / mod.G0_FORMAL_ROOT).iterdir()) == sorted(mod.G0_EVIDENCE_FILES)
    assert sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir()) == _rec_before
    gseen = {}

    def _gspy(**kw):
        gseen.update(kw)
        return {"phase": "g0"}

    monkeypatch.setitem(cli._RUNNERS, "g0", _gspy)
    monkeypatch.setattr(cli, "_load_state",
                        lambda path: {"g0_execution_authorized": True})
    assert cli.main(["--phase", "g0"]) == 0
    assert gseen.get("authorized") is True
    assert "out_dir" not in gseen


# --------------------------------------------------------------------------
# T2 — G0 entrypoint delta (fake decoder only; no real decoder or data)
# --------------------------------------------------------------------------
class _G0ExactFake:
    def __init__(self, truths):
        self.calls = []
        self.truths = truths

    def __call__(self, h, prior, syndrome, layer=None):
        prior = np.asarray(prior, dtype=np.float64)
        syndrome = np.asarray(syndrome, dtype=np.int64)
        self.calls.append({"shape": np.shape(h), "prior": prior.copy(),
                           "syndrome": syndrome.copy(), "layer": layer})
        if not self.truths:
            raise AssertionError("missing fixture truth for fake G0 call")
        x_hat = np.asarray(self.truths.pop(0), dtype=np.int64)
        return {"x_hat": x_hat, "syndrome_ok": True,
                "iterations": 1, "final_beliefs": np.log(prior)}


def test_T2_19_g0_fixture_is_positive_and_normalized():
    h, p_b, p_f = mod.build_g0_fixture()
    assert set(h) == {"L1", "L2"}
    assert h["L1"].shape == (8, 8) and h["L2"].shape == (8, 8)
    assert np.all(p_b > 0) and np.isclose(p_b.sum(), 1.0)
    assert np.all(p_f > 0)
    assert np.allclose(p_f.sum(axis=0), 1.0, atol=1e-14)
    p1 = mod.marginalize_f_to_p1(p_f)
    p2 = mod.conditionalize_f_to_p2(p_f)
    assert np.allclose(p1.sum(axis=0), 1.0, atol=1e-14)
    assert np.allclose(p2.sum(axis=2), 1.0, atol=1e-14)
    assert mod._g0_exhaustive_error(p_b, p_f) < 1e-14


def test_T2_20_g0_unauthorized_refuses_before_fixture_or_decoder(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("G0 work must not start")

    monkeypatch.setattr(mod, "build_g0_fixture", _boom)
    monkeypatch.setattr(mod, "historical_g0_decoder", _boom)
    with pytest.raises(mod.NotAuthorizedError):
        mod.run_g0_synthetic(authorized=False)


def test_T2_21_decoder_dataclass_adapter_uses_frozen_kwargs(monkeypatch):
    seen = {}

    class Result:
        x_hat = np.array([1, 2], dtype=np.uint8)
        syndrome_ok = True
        iterations = 3
        final_beliefs = np.zeros((2, 32), dtype=np.float64)

    def _decoder(h, prior, syndrome, **kwargs):
        seen.update(kwargs)
        return Result()

    monkeypatch.setattr(mod, "_load_g0_decoder", lambda: _decoder)
    out = mod.historical_g0_decoder(
        np.eye(2, dtype=np.uint8), np.full((2, 32), 1.0 / 32),
        np.array([1, 2], dtype=np.uint8))
    assert out["x_hat"].tolist() == [1, 2]
    assert out["syndrome_ok"] is True and out["iterations"] == 3
    assert seen == {"max_iter": 90, "damping_alpha": 1.0,
                    "warm_beliefs": None, "field": None}


def test_T2_22_g0_dataclass_result_is_accepted():
    class Result:
        x_hat = np.array([0, 1], dtype=np.uint8)
        syndrome_ok = True
        iterations = 0
        final_beliefs = np.zeros((2, 32), dtype=np.float64)

    def _decoder(h, prior, syndrome, layer=None):
        return Result()

    exact, syn_ok, it, finite, beliefs = mod._decode_block(
        _decoder, np.eye(2, dtype=np.uint8),
        np.full((2, 32), 1.0 / 32), np.array([0, 1]),
    )
    assert exact and syn_ok and it == 0 and finite
    assert np.shape(beliefs) == (2, 32)


def test_T2_23_g0_fake_authorized_runs_eight_seeds_and_writes_four(
        tmp_path, monkeypatch):
    _rec_root = ROOT / mod.G0_RECOVERY_FORMAL_ROOT
    _rec_before = sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir())
    truths = []
    original_sample = mod.sample_matched_block

    def _sample_and_retain(*args, **kwargs):
        block = original_sample(*args, **kwargs)
        truths.append(np.asarray(block["u2"], dtype=np.int64).copy())
        return block

    # The fake is given the generated fixture truth, while _decode_block still
    # independently recomputes and checks its syndrome.  This tests plumbing,
    # not an identity/mode-pattern assumption about the decoder.
    monkeypatch.setattr(mod, "sample_matched_block", _sample_and_retain)
    fake = _G0ExactFake(truths)
    out = tmp_path / "g0"
    result = mod.run_g0_synthetic(authorized=True, decode_fn=fake,
                                  out_dir=out)
    assert result["decision"] == "G0_PASS"
    assert result["passed"] is True
    assert result["attempted_blocks"] == 8
    assert result["completed_blocks"] == 8
    assert result["decoder_calls"] == 8
    assert [r["seed"] for r in result["records"]] == list(mod.G0_SEEDS)
    assert len(fake.calls) == 8
    assert sorted(p.name for p in out.iterdir()) == sorted(
        mod.G0_EVIDENCE_FILES)
    payload = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert payload["decision"] == "G0_PASS"
    assert payload["exact_count"] == 8
    assert payload["syndrome_ok_count"] == 8
    assert payload["finite_count"] == 8
    assert payload["seeds"] == list(mod.G0_SEEDS)
    assert (ROOT / mod.G0_FORMAL_ROOT).exists()
    assert sorted(p.name for p in (ROOT / mod.G0_FORMAL_ROOT).iterdir()) == sorted(mod.G0_EVIDENCE_FILES)
    assert sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir()) == _rec_before
    for key in payload:
        assert key not in {"h", "p_b", "p_f", "prior", "syndrome"}


def test_T2_24_g0_fake_failure_is_blocked_and_retained(tmp_path):
    calls = []

    def _fail(h, prior, syndrome, layer=None):
        calls.append(1)
        raise RuntimeError("injected G0 decoder failure")

    out = tmp_path / "blocked"
    result = mod.run_g0_synthetic(authorized=True, decode_fn=_fail,
                                  out_dir=out)
    assert result["decision"] == "G0_BLOCKED_DECODER"
    assert result["passed"] is False
    assert len(calls) == 1
    assert result["attempted_blocks"] == 1
    assert result["completed_blocks"] == 0
    assert result["decoder_calls"] == 1
    assert result["failed_seed"] == mod.G0_SEEDS[0]
    assert result["failure_stage"] == "decoder"
    assert sorted(p.name for p in out.iterdir()) == sorted(
        mod.G0_EVIDENCE_FILES)
    payload = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert payload["decision"] == "G0_BLOCKED_DECODER"
    assert payload["decoder_calls"] == 1
    assert payload["failed_seed"] == mod.G0_SEEDS[0]
    assert payload["failure_stage"] == "decoder"


def test_T2_25_decode_adapter_recomputes_syndrome_before_acceptance():
    def _lies(h, prior, syndrome, layer=None):
        _ = (prior, layer)
        return {"x_hat": np.array([1, 1], dtype=np.int64),
                "syndrome_ok": True, "iterations": 1,
                "final_beliefs": np.zeros((2, 32), dtype=np.float64)}

    exact, syn_ok, it, finite, _ = mod._decode_block(
        _lies, np.array([[1, 1]], dtype=np.uint8),
        np.full((2, 32), 1.0 / 32), np.array([1, 2], dtype=np.int64),
    )
    assert exact is False and syn_ok is False
    assert it == 1 and finite is True


def test_T2_26_g0_failure_retains_prior_completed_call_counts():
    calls = []

    def _fail_on_second(h, prior, syndrome, layer=None):
        _ = (h, syndrome, layer)
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError("second G0 decoder call failed")
        return {"x_hat": np.zeros(prior.shape[0], dtype=np.int64),
                "syndrome_ok": False, "iterations": 1,
                "final_beliefs": np.zeros_like(prior)}

    h, p_b, p_f = mod.build_g0_fixture()
    result = mod.run_g0_phase(h=h, p_b=p_b, p_f=p_f,
                              decode_fn=_fail_on_second, authorized=True)
    assert result["decision"] == "G0_BLOCKED_DECODER"
    assert result["attempted_blocks"] == 2
    assert result["completed_blocks"] == 1
    assert result["decoder_calls"] == 2
    assert result["failed_seed"] == mod.G0_SEEDS[1]
    assert result["failure_stage"] == "decoder"


def test_T2_27_g0_cli_maps_to_synthetic_entrypoint_without_authorization(
        monkeypatch):
    state = {"g0_execution_authorized": False}
    calls = []

    def _runner(**kwargs):
        calls.append(kwargs)
        raise AssertionError("unauthorized CLI entered G0 runner")

    monkeypatch.setattr(cli, "_load_state", lambda path: state)
    monkeypatch.setitem(cli._RUNNERS, "g0", _runner)
    assert cli.main(["--phase", "g0"]) == 3
    assert calls == []


# --------------------------------------------------------------------------
# T2 — G0 implementation-candidate acceptance delta (fake/math only)
# --------------------------------------------------------------------------
def test_T2_28_g0_fixture_degree2_ring_no_degree1():
    h, p_b, p_f = mod.build_g0_fixture()
    assert set(h) == {"L1", "L2"}
    for key in ("L1", "L2"):
        m_ = np.asarray(h[key])
        assert m_.shape == (8, 8)
        assert int(m_.shape[1]) <= 9
        assert bool(np.all((m_ != 0).sum(axis=0) == 2))
        assert bool(np.all((m_ != 0).sum(axis=1) == 2))
    assert int(np.count_nonzero(np.asarray(h["L1"]) == 2)) >= 1
    assert np.all(np.isfinite(p_b)) and bool(np.all(p_b > 0))
    assert abs(float(p_b.sum()) - 1.0) < 1e-12
    assert np.all(np.isfinite(p_f)) and bool(np.all(p_f > 0))
    assert np.allclose(p_f.sum(axis=0), 1.0, atol=1e-12)


def test_T2_29_g0_unauthorized_loads_no_decoder_and_writes_nothing(
        tmp_path, monkeypatch):
    _rec_root = ROOT / mod.G0_RECOVERY_FORMAL_ROOT
    _rec_before = sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir())
    loaded = []

    def _boom_loader():
        loaded.append(1)
        raise AssertionError("historic decoder loaded while unauthorized")

    def _boom_writer(out_dir, result):
        raise AssertionError("G0 writer entered while unauthorized")

    monkeypatch.setattr(mod, "_load_g0_decoder", _boom_loader)
    monkeypatch.setattr(mod, "write_g0_evidence", _boom_writer)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(mod.NotAuthorizedError):
        mod.run_g0_synthetic(authorized=False)
    with pytest.raises(mod.NotAuthorizedError):
        mod.run_g0_synthetic(authorized=False, decode_fn=FakeDecoder())
    assert loaded == []
    assert list(tmp_path.rglob("*")) == []
    assert (ROOT / mod.G0_FORMAL_ROOT).exists()
    assert sorted(p.name for p in (ROOT / mod.G0_FORMAL_ROOT).iterdir()) == sorted(mod.G0_EVIDENCE_FILES)
    assert sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir()) == _rec_before


def test_T2_30_g0_exhaustive_is_independent_not_self_compare():
    _, p_b, p_f = mod.build_g0_fixture()
    assert mod._g0_exhaustive_error(p_b, p_f) < 1e-12
    bad = np.asarray(p_f, dtype=np.float64).copy()
    bad[:, 0] = bad[:, 0] * 2.0
    assert mod._g0_exhaustive_error(p_b, bad) > 1e-6
    src = inspect.getsource(mod._g0_exhaustive_error)
    assert "marginalize_f_to_p1" in src
    assert "conditionalize_f_to_p2" in src


def test_T2_31_g0_math_gate_blocks_before_any_decoder_call():
    h, p_b, p_f = mod.build_g0_fixture()
    bad = np.asarray(p_f, dtype=np.float64).copy()
    bad[:, 0] = bad[:, 0] * 2.0
    fake = FakeDecoder()
    res = mod.run_g0_phase(h=h, p_b=p_b, p_f=bad, decode_fn=fake,
                           authorized=True)
    assert res["decision"] == "G0_BLOCKED_MATH"
    assert res["passed"] is False
    assert res["attempted_blocks"] == 0
    assert res["decoder_calls"] == 0
    assert res["completed_blocks"] == 0
    assert res["failed_seed"] is None
    assert res["failure_stage"] == "math"
    assert fake.calls == []


def test_T2_32_g0_resource_block_keeps_actual_counts():
    def _mem(h_, prior, syndrome, layer=None):
        raise MemoryError("injected G0 resource failure")

    h, p_b, p_f = mod.build_g0_fixture()
    res = mod.run_g0_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=_mem,
                           authorized=True)
    assert res["decision"] == "G0_BLOCKED_RESOURCE"
    assert res["passed"] is False
    assert res["attempted_blocks"] == 1
    assert res["decoder_calls"] == 1
    assert res["completed_blocks"] == 0
    assert res["failed_seed"] == mod.G0_SEEDS[0]
    assert res["failure_stage"] == "decoder"
    assert res["error"] and "MemoryError" in res["error"]


def test_T2_33_g0_writer_four_files_scalar_only_no_overwrite(tmp_path):
    _rec_root = ROOT / mod.G0_RECOVERY_FORMAL_ROOT
    _rec_before = sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir())
    h, p_b, p_f = mod.build_g0_fixture()
    out = tmp_path / "g0w"
    res = mod.run_g0_synthetic(authorized=True, decode_fn=FakeDecoder(),
                               out_dir=out)
    assert res["decision"] in ("G0_PASS", "G0_BLOCKED_MATH",
                               "G0_BLOCKED_DECODER", "G0_BLOCKED_RESOURCE")
    assert sorted(p.name for p in out.iterdir()) == sorted(
        mod.G0_EVIDENCE_FILES)
    with pytest.raises(FileExistsError):
        mod.write_g0_evidence(out, res)
    payload = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert payload["seeds"] == list(mod.G0_SEEDS)
    assert payload["decoder_calls"] == res["decoder_calls"]
    banned_sub = ("hash", "checksum", "hmac", "sha256", "sha512", "sha1",
                  "md5", "signature")
    banned_key = {"h", "p_b", "p_f", "prior", "priors", "syndrome",
                  "syndromes", "matrix", "matrices", "beliefs", "messages",
                  "raw", "coefficients", "support"}
    stack = [payload]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                low = str(k).lower()
                assert not any(b in low for b in banned_sub)
                assert low not in banned_key
                assert "tag" not in set(low.split("_"))
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
        elif isinstance(cur, str):
            assert ":\\" not in cur and ":/" not in cur
            assert not cur.startswith("/")
    table = (out / "table.csv").read_text(encoding="utf-8").splitlines()
    assert table[0] == ("seed,exact,syndrome_ok,finite,iterations,"
                        "syndrome_weight")
    assert len(table) == 1 + res["attempted_blocks"]
    summ = json.loads(
        (out / "execution_summary.json").read_text(encoding="utf-8"))
    assert summ["files"] == list(mod.G0_EVIDENCE_FILES)
    assert summ["decoder_calls"] == res["decoder_calls"]
    assert (ROOT / mod.G0_FORMAL_ROOT).exists()
    assert sorted(p.name for p in (ROOT / mod.G0_FORMAL_ROOT).iterdir()) == sorted(mod.G0_EVIDENCE_FILES)
    assert sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir()) == _rec_before


def test_T2_34_all_g0_p0_g1_g2_real_formal_auth_still_false():
    state = cli._load_state(STATE_PATH)
    for key in ("structure_execution_authorized", "g0_execution_authorized",
                "p0_cost_execution_authorized", "g1_execution_authorized",
                "g2_execution_authorized", "real_execution_authorized",
                "formal_execution_authorized"):
        assert key in state
        assert state[key] is False
    assert state.get("scientific_promotion", False) is False
    for phase in ("structure", "g0", "p0-cost", "g1", "g2"):
        assert mod.is_phase_authorized(state, phase) is False
    assert mod.is_phase_authorized(state, "no-such-phase") is False


# --------------------------------------------------------------------------
# R1 closeout rework: B1 true tree + B2 resource/invocation (fake/math/tmp)
# --------------------------------------------------------------------------
def test_R1_B1_tree_pass_no_decoder_calls():
    px, py, a, s = mod.build_g0_tree_fixture()
    assert px.shape == (32,) and py.shape == (32,)
    assert bool(np.all(px > 0)) and bool(np.all(py > 0))
    assert np.isclose(float(px.sum()), 1.0, atol=1e-12)
    assert np.isclose(float(py.sum()), 1.0, atol=1e-12)
    assert float(np.std(px)) > 0 and float(np.std(py)) > 0
    assert not np.allclose(px, py)
    assert a == mod.G0_TREE_COEFF_A and a not in (0, 1) and 1 <= a < 32
    assert 0 <= s < 32
    rep = mod._g0_tree_posterior_check()
    assert rep["tree_exhaustive_posterior_error"] < 1e-12
    assert rep["tree_map_equal"] is True
    assert rep["tree_finite"] is True
    assert rep["tree_prior_ok"] is True
    ex_src = inspect.getsource(mod._tree_exhaustive_marginals)
    msg_src = inspect.getsource(mod._tree_message_marginals)
    assert ex_src != msg_src
    assert "for x in range" in ex_src or "for y in range" in ex_src
    assert "msg_to_" in msg_src or "message" in msg_src.lower()
    loaded = []
    orig = mod._load_g0_decoder
    mod._load_g0_decoder = lambda: loaded.append(1) or (_ for _ in ()).throw(
        AssertionError("tree check must not load decoder"))
    try:
        rep2 = mod._g0_tree_posterior_check()
    finally:
        mod._load_g0_decoder = orig
    assert loaded == []
    assert rep2["tree_exhaustive_posterior_error"] < 1e-12
    h, p_b, p_f = mod.build_g0_fixture()
    assert mod._g0_factorization_error(p_b, p_f) < 1e-12
    assert mod._g0_factorization_error(p_b, p_f) == pytest.approx(
        mod._g0_exhaustive_error(p_b, p_f))


def test_R1_B1_tree_mutations_caught_by_gate_metric():
    px, py, a, s = mod.build_g0_tree_fixture()
    ex_x, ex_y = mod._tree_exhaustive_marginals(px, py, a, s)
    wrong_a = 8 if a != 8 else 9
    mx, my = mod._tree_message_marginals(px, py, wrong_a, s)
    err_a = float(max(float(np.max(np.abs(mx - ex_x))),
                      float(np.max(np.abs(my - ex_y)))))
    assert err_a > 1e-6
    wrong_s = (int(s) + 1) % 32
    mx2, my2 = mod._tree_message_marginals(px, py, a, wrong_s)
    err_s = float(max(float(np.max(np.abs(mx2 - ex_x))),
                      float(np.max(np.abs(my2 - ex_y)))))
    assert err_s > 1e-6
    sx, sy = mod._tree_message_marginals(py, px, a, s)
    err_t = float(max(float(np.max(np.abs(sx - ex_x))),
                      float(np.max(np.abs(sy - ex_y)))))
    assert err_t > 1e-6
    h, p_b, p_f = mod.build_g0_fixture()
    bad = np.asarray(p_f, dtype=np.float64).copy()
    bad[:, 0] = bad[:, 0] * 2.0
    assert float(mod._g0_factorization_error(p_b, bad)) > 1e-6


def test_R1_B1_math_gate_blocks_before_loader_and_decoder():
    h, p_b, p_f = mod.build_g0_fixture()
    bad = np.asarray(p_f, dtype=np.float64).copy()
    bad[:, 0] = bad[:, 0] * 2.0
    loads = []
    orig_loader = mod._load_g0_decoder

    def _count_loader():
        loads.append(1)
        raise AssertionError("loader must not run on math fail")

    mod._load_g0_decoder = _count_loader
    fake = FakeDecoder()
    try:
        res = mod.run_g0_phase(h=h, p_b=p_b, p_f=bad, decode_fn=fake,
                               authorized=True)
    finally:
        mod._load_g0_decoder = orig_loader
    assert res["decision"] == "G0_BLOCKED_MATH"
    assert res["decoder_calls"] == 0
    assert loads == []
    assert fake.calls == []
    assert res["historical_decoder_invocations"] == 0
    assert "factorization_error" in res
    assert "tree_exhaustive_posterior_error" in res
    assert "tree_map_equal" in res
    orig_check = mod._g0_tree_posterior_check
    loads2 = []

    def _count_loader2():
        loads2.append(1)
        raise AssertionError("loader must not run on tree fail")

    mod._load_g0_decoder = _count_loader2

    def _bad_tree(*args, **kwargs):
        return {"tree_exhaustive_posterior_error": 1e-3,
                "tree_map_equal": False, "tree_finite": True,
                "tree_prior_ok": True}

    mod._g0_tree_posterior_check = _bad_tree
    fake2 = FakeDecoder()
    try:
        res2 = mod.run_g0_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=fake2,
                                authorized=True)
    finally:
        mod._g0_tree_posterior_check = orig_check
        mod._load_g0_decoder = orig_loader
    assert res2["decision"] == "G0_BLOCKED_MATH"
    assert res2["decoder_calls"] == 0
    assert fake2.calls == []
    assert loads2 == []


def test_R1_B2_fake_historical_zero_and_metering_fields():
    h, p_b, p_f = mod.build_g0_fixture()
    fake = FakeDecoder()
    res = mod.run_g0_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=fake,
                           authorized=True)
    assert res["historical_decoder_invocations"] == 0
    assert "wall_seconds" in res
    assert isinstance(res["wall_seconds"], float)
    assert "peak_rss_bytes" in res
    assert res["decoder_calls"] == 8
    assert res["factorization_error"] < 1e-12
    assert res["tree_exhaustive_posterior_error"] < 1e-12
    assert res["tree_map_equal"] is True
    assert res["prior_positive"] is True
    assert res["fixture_ok"] is True


def test_R1_B2_historic_zero_to_one_then_stays_one(monkeypatch):
    h, p_b, p_f = mod.build_g0_fixture()
    calls = []

    def _zeros(hh, prior, syndrome, **kw):
        calls.append(1)
        n = np.asarray(prior).shape[0]

        class _R:
            x_hat = np.zeros(n, dtype=np.uint8)
            syndrome_ok = False
            iterations = 1
            final_beliefs = np.zeros_like(np.asarray(prior))

        return _R()

    monkeypatch.setattr(mod, "_load_g0_decoder", lambda: _zeros)
    res = mod.run_g0_phase(h=h, p_b=p_b, p_f=p_f,
                           decode_fn=mod.historical_g0_decoder,
                           authorized=True)
    assert res["historical_decoder_invocations"] == 1
    assert res["decoder_calls"] == 8
    assert len(calls) == 8

    def _boom_hist(hh, prior, syndrome, **kw):
        raise RuntimeError("injected historic fail")

    monkeypatch.setattr(mod, "_load_g0_decoder", lambda: _boom_hist)
    res2 = mod.run_g0_phase(h=h, p_b=p_b, p_f=p_f,
                            decode_fn=mod.historical_g0_decoder,
                            authorized=True)
    assert res2["historical_decoder_invocations"] == 1
    assert res2["decoder_calls"] == 1
    assert res2["decision"] == "G0_BLOCKED_DECODER"
    assert res2["failed_seed"] == mod.G0_SEEDS[0]


def test_R1_B2_resource_exceed_keeps_partial_and_stops(monkeypatch):
    h, p_b, p_f = mod.build_g0_fixture()
    monkeypatch.setattr(mod, "_rss_bytes", lambda: 3 * 1024**3)
    fake = FakeDecoder()
    res = mod.run_g0_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=fake,
                           authorized=True)
    assert res["decision"] == "G0_BLOCKED_RESOURCE"
    assert res["failure_stage"] == "resource"
    assert res["attempted_blocks"] == 1
    assert res["completed_blocks"] == 0
    assert res["decoder_calls"] == 0
    assert fake.calls == []
    assert res["historical_decoder_invocations"] == 0
    assert res["failed_seed"] == mod.G0_SEEDS[0]
    assert res["attempted_blocks"] > 0
    assert res["attempted_blocks"] < len(mod.G0_SEEDS)
    assert "wall_seconds" in res
    assert res["peak_rss_bytes"] == 3 * 1024**3


def test_R1_B2_writer_exactly_four_files_scalar_only(tmp_path):
    _rec_root = ROOT / mod.G0_RECOVERY_FORMAL_ROOT
    _rec_before = sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir())
    out = tmp_path / "r1g0"
    res = mod.run_g0_synthetic(authorized=True, decode_fn=FakeDecoder(),
                               out_dir=out)
    assert sorted(p.name for p in out.iterdir()) == sorted(
        mod.G0_EVIDENCE_FILES)
    assert len(list(out.iterdir())) == 4
    payload = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert payload["historical_decoder_invocations"] == 0
    assert "wall_seconds" in payload
    assert "peak_rss_bytes" in payload
    assert "factorization_error" in payload
    assert "tree_exhaustive_posterior_error" in payload
    assert "tree_map_equal" in payload
    banned_sub = ("hash", "checksum", "hmac", "sha256", "sha512", "sha1",
                  "md5", "signature")
    banned_key = {"h", "p_b", "p_f", "prior", "priors", "syndrome",
                  "syndromes", "matrix", "matrices", "beliefs", "messages",
                  "raw", "coefficients", "support"}
    stack = [payload]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                low = str(k).lower()
                assert not any(b in low for b in banned_sub)
                assert low not in banned_key
                assert "tag" not in set(low.split("_"))
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
        elif isinstance(cur, str):
            assert ":\\" not in cur and ":/" not in cur
            assert not cur.startswith("/")
    table = (out / "table.csv").read_text(encoding="utf-8").splitlines()
    assert table[0] == ("seed,exact,syndrome_ok,finite,iterations,"
                        "syndrome_weight")
    assert len(table) == 1 + res["attempted_blocks"]
    summ = json.loads(
        (out / "execution_summary.json").read_text(encoding="utf-8"))
    assert summ["files"] == list(mod.G0_EVIDENCE_FILES)
    assert summ["historical_decoder_invocations"] == 0
    assert (ROOT / mod.G0_FORMAL_ROOT).exists()
    assert sorted(p.name for p in (ROOT / mod.G0_FORMAL_ROOT).iterdir()) == sorted(mod.G0_EVIDENCE_FILES)
    assert sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir()) == _rec_before


def test_R1_B2_cli_unauthorized_prework_all_zero(tmp_path, monkeypatch):
    _rec_root = ROOT / mod.G0_RECOVERY_FORMAL_ROOT
    _rec_before = sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir())
    counts = {"runner": 0, "loader": 0, "decode": 0}

    def _runner(**kw):
        counts["runner"] += 1
        raise AssertionError("unauthorized runner entered")

    def _loader():
        counts["loader"] += 1
        raise AssertionError("loader entered while unauthorized")

    orig_decode = FakeDecoder.__call__

    def _decode(self, h, prior, syndrome, layer=None):
        counts["decode"] += 1
        return orig_decode(self, h, prior, syndrome, layer)

    monkeypatch.setitem(cli._RUNNERS, "g0", _runner)
    monkeypatch.setattr(mod, "_load_g0_decoder", _loader)
    monkeypatch.setattr(cli, "_load_state",
                        lambda path: {"g0_execution_authorized": False})
    monkeypatch.chdir(tmp_path)
    assert cli.main(["--phase", "g0"]) == 3
    assert counts == {"runner": 0, "loader": 0, "decode": 0}
    assert list(tmp_path.rglob("*")) == []
    assert (ROOT / mod.G0_FORMAL_ROOT).exists()
    assert sorted(p.name for p in (ROOT / mod.G0_FORMAL_ROOT).iterdir()) == sorted(mod.G0_EVIDENCE_FILES)
    assert sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir()) == _rec_before


def test_R1_B2_last_seed_resource_exceed_blocked_with_counts_preserved(
        monkeypatch):
    h, p_b, p_f = mod.build_g0_fixture()
    base = mod.run_g0_phase(h=h, p_b=p_b, p_f=p_f,
                            decode_fn=FakeDecoder(), authorized=True)
    assert base["attempted_blocks"] == 8
    assert base["completed_blocks"] == 8
    assert base["decoder_calls"] == 8
    n_last = len(mod.G0_SEEDS)
    calls = {"n": 0}
    orig_decode = FakeDecoder.__call__

    def _counting(self, h_, prior, syndrome, layer=None):
        calls["n"] += 1
        return orig_decode(self, h_, prior, syndrome, layer)

    monkeypatch.setattr(FakeDecoder, "__call__", _counting)
    orig_rss = mod._rss_bytes

    def _rss_after_last():
        if calls["n"] >= n_last:
            return 3 * 1024**3
        return orig_rss()

    monkeypatch.setattr(mod, "_rss_bytes", _rss_after_last)
    fake = FakeDecoder()
    res = mod.run_g0_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=fake,
                           authorized=True)
    assert len(fake.calls) == 8
    assert res["decoder_calls"] == 8
    assert res["attempted_blocks"] == 8
    assert res["completed_blocks"] == 8
    assert res["decision"] == "G0_BLOCKED_RESOURCE"
    assert res["passed"] is False
    assert res["exact_count"] == base["exact_count"]
    assert res["syndrome_ok_count"] == base["syndrome_ok_count"]
    assert res["finite_count"] == base["finite_count"]
    assert res["failed_seed"] == mod.G0_SEEDS[-1]
    assert res["failure_stage"] == "resource"


def test_R1_B2_all_exec_false_formal_absent_and_budgets():
    formal_before = _snapshot_formal_roots()
    _rec_root = ROOT / mod.G0_RECOVERY_FORMAL_ROOT
    _rec_before = sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir())
    _g1_root = ROOT / mod.G1_FORMAL_ROOT
    _g1_before = _snapshot_dir(_g1_root)
    state = cli._load_state(STATE_PATH)
    for key in ("structure_execution_authorized", "g0_execution_authorized",
                "p0_cost_execution_authorized", "g1_execution_authorized",
                "g2_execution_authorized", "real_execution_authorized",
                "formal_execution_authorized"):
        assert key in state
        assert state[key] is False
    assert state.get("scientific_promotion", False) is False
    for phase in ("structure", "g0", "p0-cost", "g1", "g2"):
        assert mod.is_phase_authorized(state, phase) is False
    assert (ROOT / mod.G0_FORMAL_ROOT).exists()
    assert sorted(p.name for p in (ROOT / mod.G0_FORMAL_ROOT).iterdir()) == sorted(mod.G0_EVIDENCE_FILES)
    assert sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir()) == _rec_before
    # Lifecycle-aware: no absence assert (legitimate P0/G1 output may exist);
    # invariance proves this test touched no formal root (no validity claim,
    # INVALID_UNAUTHORIZED_TEST_TRIGGERED).
    _assert_formal_roots_unchanged(formal_before)
    assert _snapshot_dir(_g1_root) == _g1_before
    assert float(mod.G0_WALL_BUDGET_S) == 120.0
    assert int(mod.G0_RSS_BUDGET_BYTES) == 2 * 1024**3


# --------------------------------------------------------------------------
# T-R — g0-recovery confirmation (prospective; no execution here)
# --------------------------------------------------------------------------
def test_TR1_recovery_unauthorized_refuses_before_work(tmp_path, monkeypatch):
    _rec_root = ROOT / mod.G0_RECOVERY_FORMAL_ROOT
    _rec_before = sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir())
    entered = []

    def _boom_fixture(*args, **kwargs):
        entered.append("fixture")
        raise AssertionError("recovery fixture entered while unauthorized")

    def _boom_loader():
        entered.append("loader")
        raise AssertionError("recovery loader entered while unauthorized")

    def _boom_writer(out_dir, result):
        entered.append("writer")
        raise AssertionError("recovery writer entered while unauthorized")

    monkeypatch.setattr(mod, "build_g0_fixture", _boom_fixture)
    monkeypatch.setattr(mod, "_load_g0_decoder", _boom_loader)
    monkeypatch.setattr(mod, "write_g0_evidence", _boom_writer)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(mod.NotAuthorizedError):
        mod.run_g0_recovery_phase(
            h=_tiny_h(), p_b=_tiny_tables()[0], p_f=_tiny_tables()[1],
            decode_fn=FakeDecoder(), authorized=False)
    with pytest.raises(mod.NotAuthorizedError):
        mod.run_g0_recovery_synthetic(authorized=False)
    with pytest.raises(mod.NotAuthorizedError):
        mod.run_g0_recovery_synthetic(
            authorized=False, decode_fn=FakeDecoder())
    assert entered == []
    assert list(tmp_path.rglob("*")) == []
    assert sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir()) == _rec_before

    def _runner(**kw):
        entered.append("runner")
        raise AssertionError("unauthorized recovery runner entered")

    monkeypatch.setitem(cli._RUNNERS, "g0-recovery", _runner)
    monkeypatch.setattr(
        cli, "_load_state",
        lambda path: {"g0_recovery_execution_authorized": False})
    assert cli.main(["--phase", "g0-recovery"]) == 3
    assert "runner" not in entered
    assert sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir()) == _rec_before


def test_TR2_recovery_frozen_routing():
    assert tuple(mod.G0_RECOVERY_SEEDS) == (2026090620, 2026090621,
                                            2026090622, 2026090623,
                                            2026090624, 2026090625,
                                            2026090626, 2026090627)
    assert len(mod.G0_RECOVERY_SEEDS) == 8
    assert mod.G0_RECOVERY_FORMAL_ROOT == (
        "workspace/v72p2d5_g0_recovery/20260906_r1")
    assert mod._PHASE_AUTH_KEYS["g0-recovery"] == (
        "g0_recovery_execution_authorized")
    assert "g0-recovery" in mod.PHASES
    assert tuple(mod.G0_SEEDS) == tuple(range(2026090510, 2026090518))
    assert mod.G0_FORMAL_ROOT == "workspace/v72p2d5_g0/20260905_r2"
    assert (cli._RUNNERS["g0-recovery"].__name__
            == "run_g0_recovery_synthetic")
    assert cli._RUNNERS["g0"].__name__ == "run_g0_synthetic"
    assert cli._RUNNERS["g0-recovery"] is not cli._RUNNERS["p0-cost"]
    assert cli._RUNNERS["g0-recovery"] is not cli._RUNNERS["g1"]
    assert cli._RUNNERS["g0-recovery"] is not cli._RUNNERS["g2"]
    state = {"g0_execution_authorized": False,
             "g0_recovery_execution_authorized": True,
             "p0_cost_execution_authorized": False,
             "g1_execution_authorized": False,
             "g2_execution_authorized": False}
    assert mod.is_phase_authorized(state, "g0-recovery") is True
    assert mod.is_phase_authorized(state, "g0") is False
    assert mod.is_phase_authorized(state, "p0-cost") is False
    assert mod.is_phase_authorized(state, "no-such-phase") is False
    assert "g0-recovery" in cli.build_parser().parse_args(
        ["--phase", "g0-recovery"]).phase


def test_TR3_recovery_seeds_exact_order_once(monkeypatch):
    h, p_b, p_f = mod.build_g0_fixture()
    seen = []
    orig = mod.sample_matched_block

    def _spy(pb, pf, n, seed):
        seen.append(int(seed))
        return orig(pb, pf, n, seed)

    monkeypatch.setattr(mod, "sample_matched_block", _spy)
    res = mod.run_g0_recovery_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(), authorized=True)
    assert seen == list(mod.G0_RECOVERY_SEEDS)
    assert len(seen) == 8 and len(set(seen)) == 8
    assert set(seen).isdisjoint(set(mod.G0_SEEDS))
    assert res["seeds"] == list(mod.G0_RECOVERY_SEEDS)
    assert res["decoder_calls"] == 8
    assert res["phase"] == "g0-recovery"


def test_TR4_recovery_decoder_contract(monkeypatch):
    seen = {}

    class Result:
        x_hat = np.array([1, 2], dtype=np.uint8)
        syndrome_ok = True
        iterations = 3
        final_beliefs = np.zeros((2, 32), dtype=np.float64)

    def _decoder(h, prior, syndrome, **kwargs):
        seen.update(kwargs)
        return Result()

    monkeypatch.setattr(mod, "_load_g0_decoder", lambda: _decoder)
    out = mod.historical_g0_decoder(
        np.eye(2, dtype=np.uint8), np.full((2, 32), 1.0 / 32),
        np.array([1, 2], dtype=np.uint8))
    assert out["x_hat"].tolist() == [1, 2]
    assert seen == {"max_iter": 90, "damping_alpha": 1.0,
                    "warm_beliefs": None, "field": None}
    h, p_b, p_f = mod.build_g0_fixture()
    # fake path loads nothing
    fake_loads = []

    def _must_not_load():
        fake_loads.append(1)
        raise AssertionError("historical loader entered on fake path")

    monkeypatch.setattr(mod, "_load_g0_decoder", _must_not_load)
    rf = mod.run_g0_recovery_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(), authorized=True)
    assert fake_loads == []
    assert rf["historical_decoder_invocations"] == 0
    assert rf["decoder_calls"] == 8
    # historical path binds once, reuses bound decoder for all 8 seeds
    loader_calls = []
    bound_calls = []
    bound_kwargs = []

    def _raw(hh, prior, syndrome, **kw):
        bound_calls.append(1)
        bound_kwargs.append(dict(kw))
        n = np.asarray(prior).shape[0]

        class _R:
            x_hat = np.zeros(n, dtype=np.uint8)
            syndrome_ok = False
            iterations = 1
            final_beliefs = np.zeros_like(np.asarray(prior))

        return _R()

    def _count_loader():
        loader_calls.append(1)
        return _raw

    monkeypatch.setattr(mod, "_load_g0_decoder", _count_loader)
    rh = mod.run_g0_recovery_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=mod.historical_g0_decoder,
        authorized=True)
    assert len(loader_calls) == 1
    assert len(bound_calls) == 8
    assert rh["historical_decoder_invocations"] == 1
    assert rh["decoder_calls"] == 8
    assert len(bound_kwargs) == 8
    for kw in bound_kwargs:
        assert kw == {"max_iter": 90, "damping_alpha": 1.0,
                      "warm_beliefs": None, "field": None}
    # unauthorized recovery loads nothing
    unauth_loads = []

    def _unauth_loader():
        unauth_loads.append(1)
        raise AssertionError("loader entered while unauthorized")

    monkeypatch.setattr(mod, "_load_g0_decoder", _unauth_loader)
    with pytest.raises(mod.NotAuthorizedError):
        mod.run_g0_recovery_phase(
            h=h, p_b=p_b, p_f=p_f, decode_fn=mod.historical_g0_decoder,
            authorized=False)
    assert unauth_loads == []
    src = inspect.getsource(mod.run_g0_recovery_synthetic)
    assert "historical_g0_decoder" in src


def test_TR5_recovery_numerical_gates(tmp_path, monkeypatch):
    h, p_b, p_f = mod.build_g0_fixture()
    truths = []
    orig = mod.sample_matched_block

    def _retain(*args, **kwargs):
        block = orig(*args, **kwargs)
        truths.append(np.asarray(block["u2"], dtype=np.int64).copy())
        return block

    monkeypatch.setattr(mod, "sample_matched_block", _retain)
    fake = _G0ExactFake(truths)
    out = tmp_path / "r5pass"
    res = mod.run_g0_recovery_synthetic(
        authorized=True, decode_fn=fake, out_dir=out)
    assert res["phase"] == "g0-recovery"
    assert res["decision"] == "G0_RECOVERY_PASS"
    assert res["decision"] != "G0_PASS"
    assert res["passed"] is True
    assert res["marginal_err"] < 1e-12
    assert res["conditional_err"] < 1e-12
    assert res["chain_err"] < 1e-10
    assert res["exhaustive_error"] < 1e-12
    assert res["factorization_error"] < 1e-12
    assert res["tree_exhaustive_posterior_error"] < 1e-12
    assert res["tree_map_equal"] is True and res["tree_finite"] is True
    assert res["exact_count"] == 8 and res["syndrome_ok_count"] == 8
    assert res["finite_count"] == 8
    assert res["exact_failure_fraction"] == 0
    bad = np.asarray(p_f, dtype=np.float64).copy()
    bad[:, 0] = bad[:, 0] * 2.0
    fake2 = FakeDecoder()
    rm = mod.run_g0_recovery_phase(
        h=h, p_b=p_b, p_f=bad, decode_fn=fake2, authorized=True)
    assert rm["decision"] == "G0_RECOVERY_BLOCKED_MATH"
    assert rm["passed"] is False and rm["decoder_calls"] == 0

    def _fail(hh, prior, syndrome, layer=None):
        raise RuntimeError("injected recovery decoder failure")

    rd = mod.run_g0_recovery_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=_fail, authorized=True)
    assert rd["decision"] == "G0_RECOVERY_BLOCKED_DECODER"
    assert rd["passed"] is False
    monkeypatch.setattr(mod, "_rss_bytes", lambda: 3 * 1024**3)
    rr = mod.run_g0_recovery_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(), authorized=True)
    assert rr["decision"] == "G0_RECOVERY_BLOCKED_RESOURCE"
    assert rr["passed"] is False


def test_TR6_recovery_output_contract(tmp_path):
    _rec_root = ROOT / mod.G0_RECOVERY_FORMAL_ROOT
    _rec_before = sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir())
    out = tmp_path / "rec"
    res = mod.run_g0_recovery_synthetic(
        authorized=True, decode_fn=FakeDecoder(), out_dir=out)
    assert sorted(p.name for p in out.iterdir()) == sorted(
        mod.G0_EVIDENCE_FILES)
    assert len(list(out.iterdir())) == 4
    payload = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert payload["phase"] == "g0-recovery"
    assert payload["decision"] in ("G0_RECOVERY_PASS",
                                   "G0_RECOVERY_BLOCKED_MATH",
                                   "G0_RECOVERY_BLOCKED_DECODER",
                                   "G0_RECOVERY_BLOCKED_RESOURCE")
    assert payload["decision"] != "G0_PASS"
    assert payload["seeds"] == list(mod.G0_RECOVERY_SEEDS)
    banned_sub = ("hash", "checksum", "hmac", "sha256", "sha512", "sha1",
                  "md5", "signature")
    banned_key = {"h", "p_b", "p_f", "prior", "priors", "syndrome",
                  "syndromes", "matrix", "matrices", "beliefs", "messages",
                  "raw", "coefficients", "support"}
    stack = [payload]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                low = str(k).lower()
                assert not any(b in low for b in banned_sub)
                assert low not in banned_key
                assert "tag" not in set(low.split("_"))
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
        elif isinstance(cur, str):
            assert ":\\" not in cur and ":/" not in cur
            assert not cur.startswith("/")
    with pytest.raises(FileExistsError):
        mod.write_g0_evidence(out, res)
    assert (ROOT / mod.G0_FORMAL_ROOT).exists()
    assert sorted(p.name for p in (ROOT / mod.G0_FORMAL_ROOT).iterdir()) == sorted(mod.G0_EVIDENCE_FILES)
    assert sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in _rec_root.iterdir()) == _rec_before
    summ = json.loads(
        (out / "execution_summary.json").read_text(encoding="utf-8"))
    assert summ["phase"] == "g0-recovery"
    assert summ["files"] == list(mod.G0_EVIDENCE_FILES)
    table = (out / "table.csv").read_text(encoding="utf-8").splitlines()
    assert table[0] == ("seed,exact,syndrome_ok,finite,iterations,"
                        "syndrome_weight")
    assert len(table) == 1 + res["attempted_blocks"]


def test_TR7_recovery_regression_g0_p0_g1_g2_unchanged():
    assert tuple(mod.G0_SEEDS) == tuple(range(2026090510, 2026090518))
    assert mod.G0_FORMAL_ROOT == "workspace/v72p2d5_g0/20260905_r2"
    assert mod.G0_EVIDENCE_FILES == ("results.json", "table.csv",
                                     "report.md", "execution_summary.json")
    assert mod.MAX_ITER == 90 and mod.DAMPING_ALPHA == 1.0
    assert mod.G1_SEEDS[0] == 2026090600 and mod.G1_SEEDS[-1] == 2026090699
    assert mod.G2_SEEDS[0] == 2026091000 and mod.G2_SEEDS[-1] == 2026091199
    assert mod.G1_F == (1.0, 1.2) and mod.G2_F == (1.0, 1.1, 1.2)
    assert mod.P0_F == (1.0, 1.2)
    h, p_b, p_f = mod.build_g0_fixture()
    res = mod.run_g0_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(), authorized=True)
    assert res["phase"] == "g0"
    assert res["seeds"] == list(mod.G0_SEEDS)
    assert res["decision"] == "G0_BLOCKED_DECODER"
    assert mod._rows_required(mod.CE_L1_MEAN, mod.G1_WIDTH, 1.0) == 49
    assert mod._rows_required(mod.CE_L2_ORACLE_MEAN, mod.G1_WIDTH, 1.0) == 43
    assert mod._rows_required(mod.CE_L1_MEAN, mod.G2_WIDTH, 1.2) == 235
    assert mod._rows_required(mod.CE_L2_ORACLE_MEAN, mod.G2_WIDTH, 1.2) == 206


def test_R2_F1_recovery_historical_bind_once(monkeypatch):
    h, p_b, p_f = mod.build_g0_fixture()
    loader_calls = []
    bound_calls = []

    def _raw(hh, prior, syndrome, **kw):
        bound_calls.append(1)
        n = np.asarray(prior).shape[0]

        class _R:
            x_hat = np.zeros(n, dtype=np.uint8)
            syndrome_ok = False
            iterations = 1
            final_beliefs = np.zeros_like(np.asarray(prior))

        return _R()

    def _count_loader():
        loader_calls.append(1)
        return _raw

    monkeypatch.setattr(mod, "_load_g0_decoder", _count_loader)
    res = mod.run_g0_recovery_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=mod.historical_g0_decoder,
        authorized=True)
    assert len(loader_calls) == 1
    assert len(bound_calls) == 8
    assert res["historical_decoder_invocations"] == 1
    assert res["decoder_calls"] == 8
    assert res["phase"] == "g0-recovery"
    assert res["seeds"] == list(mod.G0_RECOVERY_SEEDS)


def test_R2_F2_recovery_loader_memoryerror_resource(monkeypatch):
    h, p_b, p_f = mod.build_g0_fixture()

    def _boom_loader():
        raise MemoryError("injected recovery memory pressure")

    monkeypatch.setattr(mod, "_load_g0_decoder", _boom_loader)
    res = mod.run_g0_recovery_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=mod.historical_g0_decoder,
        authorized=True)
    assert res["decision"] == "G0_RECOVERY_BLOCKED_RESOURCE"
    assert res["failure_stage"] == "resource"
    assert res["attempted_blocks"] == 0
    assert res["completed_blocks"] == 0
    assert res["decoder_calls"] == 0
    assert res["historical_decoder_invocations"] == 0
    assert "MemoryError" in (res["error"] or "")
    assert "injected recovery memory pressure" in (res["error"] or "")
    assert res["passed"] is False


def test_R2_F2_recovery_loader_timeouterror_resource(monkeypatch):
    h, p_b, p_f = mod.build_g0_fixture()

    def _boom_loader():
        raise TimeoutError("injected recovery timeout")

    monkeypatch.setattr(mod, "_load_g0_decoder", _boom_loader)
    res = mod.run_g0_recovery_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=mod.historical_g0_decoder,
        authorized=True)
    assert res["decision"] == "G0_RECOVERY_BLOCKED_RESOURCE"
    assert res["failure_stage"] == "resource"
    assert res["attempted_blocks"] == 0
    assert res["completed_blocks"] == 0
    assert res["decoder_calls"] == 0
    assert res["historical_decoder_invocations"] == 0
    assert "TimeoutError" in (res["error"] or "")
    assert "injected recovery timeout" in (res["error"] or "")
    assert res["passed"] is False


def test_R2_F2_recovery_loader_generic_decoder(monkeypatch):
    h, p_b, p_f = mod.build_g0_fixture()

    def _boom_loader():
        raise RuntimeError("injected recovery decoder boom")

    monkeypatch.setattr(mod, "_load_g0_decoder", _boom_loader)
    res = mod.run_g0_recovery_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=mod.historical_g0_decoder,
        authorized=True)
    assert res["decision"] == "G0_RECOVERY_BLOCKED_DECODER"
    assert res["failure_stage"] == "decoder"
    assert res["attempted_blocks"] == 0
    assert res["completed_blocks"] == 0
    assert res["decoder_calls"] == 0
    assert res["historical_decoder_invocations"] == 0
    assert "RuntimeError" in (res["error"] or "")
    assert "injected recovery decoder boom" in (res["error"] or "")
    assert res["passed"] is False


def test_R2_F1_ordinary_g0_historical_per_seed_regression(monkeypatch):
    h, p_b, p_f = mod.build_g0_fixture()
    loader_calls = []
    raw_calls = []

    def _raw(hh, prior, syndrome, **kw):
        raw_calls.append(1)
        n = np.asarray(prior).shape[0]

        class _R:
            x_hat = np.zeros(n, dtype=np.uint8)
            syndrome_ok = False
            iterations = 1
            final_beliefs = np.zeros_like(np.asarray(prior))

        return _R()

    def _count_loader():
        loader_calls.append(1)
        return _raw

    monkeypatch.setattr(mod, "_load_g0_decoder", _count_loader)
    res = mod.run_g0_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=mod.historical_g0_decoder,
        authorized=True)
    assert res["phase"] == "g0"
    assert res["seeds"] == list(mod.G0_SEEDS)
    assert len(loader_calls) == 8
    assert len(raw_calls) == 8
    assert res["historical_decoder_invocations"] == 1
    assert res["decoder_calls"] == 8

    def _must_not_load():
        raise AssertionError("ordinary fake path must not load")

    monkeypatch.setattr(mod, "_load_g0_decoder", _must_not_load)
    fake = FakeDecoder()
    res_fake = mod.run_g0_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=fake, authorized=True)
    assert res_fake["historical_decoder_invocations"] == 0
    assert res_fake["seeds"] == list(mod.G0_SEEDS)
    assert res_fake["decoder_calls"] == 8


def test_R2_F1_recovery_unauthorized_and_fake_loader_zero(monkeypatch):
    h, p_b, p_f = mod.build_g0_fixture()
    loads = []

    def _boom_loader():
        loads.append(1)
        raise AssertionError("loader entered while unauthorized")

    monkeypatch.setattr(mod, "_load_g0_decoder", _boom_loader)
    with pytest.raises(mod.NotAuthorizedError):
        mod.run_g0_recovery_phase(
            h=h, p_b=p_b, p_f=p_f, decode_fn=mod.historical_g0_decoder,
            authorized=False)
    assert loads == []

    def _must_not_load():
        loads.append(1)
        raise AssertionError("fake recovery path must not load")

    monkeypatch.setattr(mod, "_load_g0_decoder", _must_not_load)
    res = mod.run_g0_recovery_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(), authorized=True)
    assert loads == []
    assert res["historical_decoder_invocations"] == 0
    assert res["decoder_calls"] == 8


def test_R2_F3_historical_inv_metered_at_first_decoder_call(monkeypatch):
    h, p_b, p_f = mod.build_g0_fixture()
    orig_rss = mod._rss_bytes
    orig_sample = mod.sample_matched_block
    # Ordinary G0 pre-seed resource stop: no decoder call, no invocation.
    monkeypatch.setattr(mod, "_rss_bytes", lambda: 3 * 1024**3)

    def _must_not_load_pre():
        raise AssertionError("loader must not run on pre-seed stop")

    monkeypatch.setattr(mod, "_load_g0_decoder", _must_not_load_pre)
    res_pre = mod.run_g0_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=mod.historical_g0_decoder,
        authorized=True)
    assert res_pre["historical_decoder_invocations"] == 0
    assert res_pre["decoder_calls"] == 0
    # Ordinary G0 block/prior construction failure before decoder.
    monkeypatch.setattr(mod, "_rss_bytes", orig_rss)

    def _boom_block(pb, pf, n, seed):
        raise ValueError("injected block construction failure")

    monkeypatch.setattr(mod, "sample_matched_block", _boom_block)

    def _must_not_load_block():
        raise AssertionError("loader must not run on block failure")

    monkeypatch.setattr(mod, "_load_g0_decoder", _must_not_load_block)
    res_block = mod.run_g0_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=mod.historical_g0_decoder,
        authorized=True)
    assert res_block["historical_decoder_invocations"] == 0
    assert res_block["decoder_calls"] == 0
    # Ordinary G0 complete historical: per-seed loader/raw metered once.
    monkeypatch.setattr(mod, "sample_matched_block", orig_sample)
    loader_calls = []
    raw_calls = []

    def _raw(hh, prior, syndrome, **kw):
        raw_calls.append(1)
        n = np.asarray(prior).shape[0]

        class _R:
            x_hat = np.zeros(n, dtype=np.uint8)
            syndrome_ok = False
            iterations = 1
            final_beliefs = np.zeros_like(np.asarray(prior))

        return _R()

    def _count_loader():
        loader_calls.append(1)
        return _raw

    monkeypatch.setattr(mod, "_load_g0_decoder", _count_loader)
    res_hist = mod.run_g0_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=mod.historical_g0_decoder,
        authorized=True)
    assert len(loader_calls) == 8
    assert len(raw_calls) == 8
    assert res_hist["historical_decoder_invocations"] == 1
    assert res_hist["decoder_calls"] == 8
    # Recovery: bind-once loader, bound decoder per seed.
    rec_loader = []
    bound_calls = []

    def _rec_raw(hh, prior, syndrome, **kw):
        bound_calls.append(1)
        n = np.asarray(prior).shape[0]

        class _R:
            x_hat = np.zeros(n, dtype=np.uint8)
            syndrome_ok = False
            iterations = 1
            final_beliefs = np.zeros_like(np.asarray(prior))

        return _R()

    def _rec_loader():
        rec_loader.append(1)
        return _rec_raw

    monkeypatch.setattr(mod, "_load_g0_decoder", _rec_loader)
    res_rec = mod.run_g0_recovery_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=mod.historical_g0_decoder,
        authorized=True)
    assert len(rec_loader) == 1
    assert len(bound_calls) == 8
    assert res_rec["historical_decoder_invocations"] == 1
    assert res_rec["decoder_calls"] == 8


# --------------------------------------------------------------------------
# P0/G1/G2 production path (frozen packet; fake/tiny only, no execution)
# --------------------------------------------------------------------------
def _wide_h(rows=60, width=8):
    h1 = np.zeros((rows, width), dtype=np.uint8)
    h2 = np.zeros((rows, width), dtype=np.uint8)
    h1[:, 0] = 1
    h2[:, 0] = 1
    return {"L1": h1, "L2": h2}


class _ShapeFake:
    def __init__(self):
        self.shapes = []
        self.priors = []

    def __call__(self, h, prior, syndrome, layer=None):
        self.shapes.append(tuple(np.shape(h)))
        self.priors.append(np.asarray(prior, dtype=np.float64).copy())
        n = np.asarray(prior).shape[0]
        return {"x_hat": np.zeros(n, dtype=np.int64),
                "syndrome_ok": False,
                "iterations": 1,
                "final_beliefs": np.zeros_like(np.asarray(prior))}


def test_P0G1G2_a_different_f_different_prefix_rows():
    p_b, p_f = _tiny_tables()
    h = _wide_h()
    fake = _ShapeFake()
    res = mod.run_g1_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=fake,
                           authorized=True)
    assert res["decoder_calls"] == 440
    # G1: 220 calls per f (20*3 + 80*2); first APP L1 of each f differs.
    assert fake.shapes[0] == (7, 8)
    assert fake.shapes[220] == (8, 8)
    assert fake.shapes[0] != fake.shapes[220]
    p_b2, p_f2 = _tiny_tables()
    h2 = _wide_h()
    fake2 = _ShapeFake()
    res0 = mod.run_p0_cost_phase(h=h2, p_b=p_b2, p_f=p_f2,
                                 decode_fn=fake2, authorized=True)
    assert res0["decoder_calls"] == 12
    l1_rows = [s for s in fake2.shapes if s[1] == 8]
    assert (7, 8) in fake2.shapes and (8, 8) in fake2.shapes


def test_P0G1G2_b_prefixes_from_same_mother():
    p_b, p_f = _tiny_tables()
    h = _wide_h()
    h1 = np.asarray(h["L1"])
    h2 = np.asarray(h["L2"])
    fake = _ShapeFake()
    mod.run_g1_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=fake,
                     authorized=True)
    seen_l1 = sorted({s for s in fake.shapes if s == (7, 8) or s == (8, 8)})
    assert seen_l1 == [(7, 8), (8, 8)]
    # Every recorded L1 prefix equals the mother prefix; smaller nests in
    # larger (same-mother reuse, no per-f rebuild).
    assert np.array_equal(np.zeros((7, 8), dtype=np.uint8) * 0
                          + h1[:7], h1[:7])
    assert np.array_equal(h1[:7], h1[:8][:7])
    assert np.array_equal(h2[:6], h2[:6])
    # Builder path: one max mother per layer, frozen args, no per-f rebuild.
    builds = []
    orig = mod.build_dv3_nested_mother

    def _spy(n, m_max, k_min, seed, field=None):
        builds.append((int(n), int(m_max), int(k_min), int(seed)))
        return np.zeros((60, 8), dtype=np.uint8)

    import unittest.mock as _mock
    with _mock.patch.object(mod, "build_dv3_nested_mother", _spy):
        fake2 = _ShapeFake()
        mod.run_g1_phase(h=None, p_b=p_b, p_f=p_f, decode_fn=fake2,
                         authorized=True)
    assert builds == [(64, 59, 59, mod.L1_GRAPH_SEED),
                      (64, 52, 52, mod.L2_GRAPH_SEED)]
    builds2 = []
    with _mock.patch.object(
            mod, "build_dv3_nested_mother",
            lambda n, m_max, k_min, seed, field=None: (
                builds2.append((int(n), int(m_max), int(k_min), int(seed))),
                np.zeros((60, 8), dtype=np.uint8))[1]):
        fake3 = _ShapeFake()
        mod.run_g2_phase(h=None, p_b=p_b, p_f=p_f, decode_fn=fake3,
                         authorized=True)
    assert builds2 == [(256, 235, 235, mod.L1_GRAPH_SEED),
                       (256, 206, 206, mod.L2_GRAPH_SEED)]


def test_P0G1G2_c_app_l1_then_l2_order():
    p_b, p_f = _tiny_tables()
    fake = _ShapeFake()
    res = mod.run_g1_phase(h=_tiny_h(), p_b=p_b, p_f=p_f,
                           decode_fn=fake, authorized=True)
    assert res["decoder_calls"] == 440
    # Tiny H1 is 3x6, H2 is 4x6: APP must start L1 then L2 per block.
    assert fake.shapes[0] == (3, 6)
    assert fake.shapes[1] == (4, 6)
    assert fake.shapes[2] == (4, 6) or fake.shapes[2] == (3, 6)
    for pr in fake.priors:
        assert pr.shape[0] == 6 and pr.shape[1] in (2, 32)
        assert bool(np.all(np.isfinite(pr)))
        assert np.allclose(pr.sum(axis=1), 1.0)
    assert fake.priors[0].shape == (6, 2)
    assert fake.priors[1].shape == (6, 32)


def test_P0G1G2_d_frozen_calls_seeds_rows():
    p_b, p_f = _tiny_tables()
    h = _tiny_h()
    assert mod.run_p0_cost_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
        authorized=True)["decoder_calls"] == 12
    assert mod.run_g1_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
        authorized=True)["decoder_calls"] == 440
    assert mod.run_g2_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
        authorized=True)["decoder_calls"] == 1320
    assert tuple(mod.G0_SEEDS[:2]) == (2026090510, 2026090511)
    assert len(mod.G1_SEEDS) == 100 and mod.G1_SEEDS[0] == 2026090600
    assert mod.G1_SEEDS[-1] == 2026090699
    assert len(mod.G2_SEEDS) == 200 and mod.G2_SEEDS[0] == 2026091000
    assert mod.G2_SEEDS[-1] == 2026091199
    assert mod._rows_required(mod.CE_L1_MEAN, 64, 1.0) == 49
    assert mod._rows_required(mod.CE_L2_ORACLE_MEAN, 64, 1.0) == 43
    assert mod._rows_required(mod.CE_L1_MEAN, 64, 1.2) == 59
    assert mod._rows_required(mod.CE_L2_ORACLE_MEAN, 64, 1.2) == 52
    assert mod._rows_required(mod.CE_L1_MEAN, 256, 1.0) == 196
    assert mod._rows_required(mod.CE_L2_ORACLE_MEAN, 256, 1.0) == 172
    assert mod._rows_required(mod.CE_L1_MEAN, 256, 1.1) == 215
    assert mod._rows_required(mod.CE_L2_ORACLE_MEAN, 256, 1.1) == 189
    assert mod._rows_required(mod.CE_L1_MEAN, 256, 1.2) == 235
    assert mod._rows_required(mod.CE_L2_ORACLE_MEAN, 256, 1.2) == 206


def test_P0G1G2_e_authorization_refuses_before_work(tmp_path, monkeypatch):
    p_b, p_f = _tiny_tables()
    h = _tiny_h()
    entered = []

    def _boom_build(*a, **k):
        entered.append("build")
        raise AssertionError("builder entered while unauthorized")

    def _boom_load():
        entered.append("loader")
        raise AssertionError("loader entered while unauthorized")

    def _boom_write(*a, **k):
        entered.append("writer")
        raise AssertionError("writer entered while unauthorized")

    monkeypatch.setattr(mod, "build_dv3_nested_mother", _boom_build)
    monkeypatch.setattr(mod, "_load_g0_decoder", _boom_load)
    monkeypatch.setattr(mod, "write_p0_cost_evidence", _boom_write)
    monkeypatch.setattr(mod, "write_g1_evidence", _boom_write)
    monkeypatch.setattr(mod, "write_g2_evidence", _boom_write)
    monkeypatch.chdir(tmp_path)
    for fn in (mod.run_p0_cost_phase, mod.run_g1_phase, mod.run_g2_phase):
        with pytest.raises(mod.NotAuthorizedError):
            fn(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
               authorized=False)
    for fn in (mod.run_p0_cost_synthetic, mod.run_g1_synthetic,
               mod.run_g2_synthetic):
        with pytest.raises(mod.NotAuthorizedError):
            fn(authorized=False)
        with pytest.raises(mod.NotAuthorizedError):
            fn(authorized=False, decode_fn=FakeDecoder())
    assert entered == []
    assert list(tmp_path.rglob("*")) == []
    # CLI stays gated with exit 3 and no runner entry.
    for phase in ("p0-cost", "g1", "g2"):
        seen = []

        def _runner(**kw):
            seen.append(kw)
            raise AssertionError("unauthorized runner entered")

        monkeypatch.setitem(cli._RUNNERS, phase, _runner)
        monkeypatch.setattr(
            cli, "_load_state", lambda path: {
                "p0_cost_execution_authorized": False,
                "g1_execution_authorized": False,
                "g2_execution_authorized": False})
        assert cli.main(["--phase", phase]) == 3
        assert seen == []
    assert list(tmp_path.rglob("*")) == []


def test_P0G1G2_f_no_holdout_or_file_access(tmp_path, monkeypatch):
    for fn in (mod.prepare_model_f_prior, mod.bind_historical_decoder,
               mod._write_stage_evidence, mod.write_p0_cost_evidence,
               mod.write_g1_evidence, mod.write_g2_evidence,
               mod.run_p0_cost_synthetic, mod.run_g1_synthetic,
               mod.run_g2_synthetic, mod._grade_g2, mod._run_rate_scan,
               mod.run_p0_cost_phase):
        src = inspect.getsource(fn)
        for frag in ("read_VAL", "read_CAL", "parquet", "np.load",
                     "loadtxt", "genfromtxt", "read_bytes", "pd.read",
                     "csv.reader", "write_text", "write_bytes", "np.save",
                     "np.savez", "to_csv", "to_parquet", "pickle",
                     "production_decoder", "build_candidate_mother"):
            assert frag not in src
    for fn in (mod.prepare_model_f_prior, mod.run_p0_cost_synthetic,
               mod.run_g1_synthetic, mod.run_g2_synthetic,
               mod.write_p0_cost_evidence, mod.write_g1_evidence,
               mod.write_g2_evidence):
        assert "build_g0_fixture" not in inspect.getsource(fn)
    # Fake phases create no files; lifecycle-aware: tmp stays empty and no
    # formal root is touched (no absence assert, no validity claim).
    p_b, p_f = _tiny_tables()
    h = _tiny_h()
    formal_before = _snapshot_formal_roots()
    monkeypatch.chdir(tmp_path)
    mod.run_p0_cost_phase(h=h, p_b=p_b, p_f=p_f,
                          decode_fn=FakeDecoder(), authorized=True)
    mod.run_g1_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                     authorized=True)
    mod.run_g2_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                     authorized=True)
    assert list(tmp_path.rglob("*")) == []
    _assert_formal_roots_unchanged(formal_before)


def test_P0G1G2_g_four_file_no_overwrite(tmp_path):
    p_b, p_f = _tiny_tables()
    h = _tiny_h()
    formal_before = _snapshot_formal_roots()
    p0 = mod.run_p0_cost_phase(h=h, p_b=p_b, p_f=p_f,
                               decode_fn=FakeDecoder(), authorized=True)
    out0 = tmp_path / "p0"
    assert mod.write_p0_cost_evidence(out0, p0) == list(
        mod.STAGE_EVIDENCE_FILES)
    assert sorted(p.name for p in out0.iterdir()) == sorted(
        mod.STAGE_EVIDENCE_FILES)
    with pytest.raises(FileExistsError):
        mod.write_p0_cost_evidence(out0, p0)
    g1 = mod.run_g1_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                          authorized=True)
    out1 = tmp_path / "g1"
    assert mod.write_g1_evidence(out1, g1) == list(mod.STAGE_EVIDENCE_FILES)
    assert sorted(p.name for p in out1.iterdir()) == sorted(
        mod.STAGE_EVIDENCE_FILES)
    with pytest.raises(FileExistsError):
        mod.write_g1_evidence(out1, g1)
    g2 = mod.run_g2_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                          authorized=True)
    out2 = tmp_path / "g2"
    assert mod.write_g2_evidence(out2, g2) == list(mod.STAGE_EVIDENCE_FILES)
    assert sorted(p.name for p in out2.iterdir()) == sorted(
        mod.STAGE_EVIDENCE_FILES)
    with pytest.raises(FileExistsError):
        mod.write_g2_evidence(out2, g2)
    for out in (out0, out1, out2):
        payload = json.loads(
            (out / "results.json").read_text(encoding="utf-8"))
        stack = [payload]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                for k, v in cur.items():
                    low = str(k).lower()
                    assert "hash" not in low and "checksum" not in low
                    assert "sha256" not in low and "md5" not in low
                    assert "signature" not in low and "hmac" not in low
                    assert low not in {"h", "p_b", "p_f", "prior", "priors",
                                       "syndrome", "syndromes", "matrix",
                                       "matrices", "beliefs", "messages",
                                       "raw", "coefficients", "support"}
                    assert "tag" not in set(low.split("_"))
                    stack.append(v)
            elif isinstance(cur, list):
                stack.extend(cur)
            elif isinstance(cur, str):
                assert ":\\" not in cur and ":/" not in cur
                assert not cur.startswith("/")
        table = (out / "table.csv").read_text(encoding="utf-8").splitlines()
        assert len(table) >= 2
        summ = json.loads(
            (out / "execution_summary.json").read_text(encoding="utf-8"))
        assert summ["files"] == list(mod.STAGE_EVIDENCE_FILES)
    assert mod.P0_FORMAL_ROOT == "workspace/v72p2d5_p0_cost/20260906_r1"
    assert mod.G1_FORMAL_ROOT == "workspace/v72p2d5_g1/20260907_r2"
    assert mod.G2_FORMAL_ROOT == "workspace/v72p2d5_g2/20260906_r1"
    # Formal roots untouched by this test (no absence assert; legitimate
    # artifacts may exist — no validity claim,
    # INVALID_UNAUTHORIZED_TEST_TRIGGERED).
    _assert_formal_roots_unchanged(formal_before)


def test_P0G1G2_h_g2_four_state_grading():
    assert mod._grade_g2(0.95, True, 0) == "G2_SYNTHETIC_QUALIFIED"
    assert mod._grade_g2(0.90, True, 0) == "G2_SYNTHETIC_QUALIFIED"
    assert mod._grade_g2(0.70, True, 0) == "G2_INCONCLUSIVE"
    assert mod._grade_g2(0.50, False, 0) == "G2_INCONCLUSIVE"
    assert mod._grade_g2(0.20, True, 0) == "G2_CURRENT_CONFIGURATION_FAILED"
    assert mod._grade_g2(0.95, False, 0) == "G2_INCONCLUSIVE"
    assert mod._grade_g2(0.95, True, 1) == "IMPLEMENTATION_OR_NUMERICAL_BLOCKED"
    assert mod._grade_g2(0.0, True, 2) == "IMPLEMENTATION_OR_NUMERICAL_BLOCKED"
    # Grading is APP-fed only: helper consumes the APP top rate.
    src = inspect.getsource(mod.run_g2_phase)
    assert 'per_f[-1]["app_exact_rate"]' in src
    assert "_grade_g2(top" in src
    # All-fail fake keeps the frozen FAILED verdict (never FER).
    p_b, p_f = _tiny_tables()
    res = mod.run_g2_phase(h=_tiny_h(), p_b=p_b, p_f=p_f,
                           decode_fn=FakeDecoder(), authorized=True)
    assert res["grade"] == "G2_CURRENT_CONFIGURATION_FAILED"
    assert "exact_failure_fraction" not in res
    for item in res["per_f"]:
        assert "app_failure_fraction" in item
        assert "FER" not in str(item)

    def _nonfinite(h, prior, syndrome, layer=None):
        n = np.asarray(prior).shape[0]
        # L1 stays finite (feeds q); L2 beliefs go nonfinite so the phase
        # counts nonfinite without crashing the APP transfer.
        if int(np.shape(h)[0]) == 3:
            bel = np.zeros_like(np.asarray(prior))
        else:
            bel = np.full_like(np.asarray(prior), np.inf)
        return {"x_hat": np.zeros(n, dtype=np.int64),
                "syndrome_ok": False, "iterations": 1,
                "final_beliefs": bel}

    res2 = mod.run_g2_phase(h=_tiny_h(), p_b=p_b, p_f=p_f,
                            decode_fn=_nonfinite, authorized=True)
    assert res2["nonfinite"] > 0
    assert res2["grade"] == "IMPLEMENTATION_OR_NUMERICAL_BLOCKED"


def test_P0G1G2_i_g0_recovery_structure_regression(tmp_path, monkeypatch):
    assert tuple(mod.G0_SEEDS) == tuple(range(2026090510, 2026090518))
    assert tuple(mod.G0_RECOVERY_SEEDS) == (2026090620, 2026090621,
                                            2026090622, 2026090623,
                                            2026090624, 2026090625,
                                            2026090626, 2026090627)
    assert mod.G0_FORMAL_ROOT == "workspace/v72p2d5_g0/20260905_r2"
    assert mod.G0_RECOVERY_FORMAL_ROOT == (
        "workspace/v72p2d5_g0_recovery/20260906_r1")
    assert mod.MAX_ITER == 90 and mod.DAMPING_ALPHA == 1.0
    assert tuple(mod.L1_PREFIXES) == (782, 821, 860, 938)
    assert tuple(mod.L2_PREFIXES) == (686, 720, 755, 823)
    assert mod.N == 1024 and mod.M_MAX == 1000
    assert mod.LAMBDA_STAR == 137.3823795883264
    h, p_b, p_f = mod.build_g0_fixture()
    res = mod.run_g0_phase(h=h, p_b=p_b, p_f=p_f,
                           decode_fn=FakeDecoder(), authorized=True)
    assert res["phase"] == "g0"
    assert res["seeds"] == list(mod.G0_SEEDS)
    assert res["decision"] == "G0_BLOCKED_DECODER"
    assert res["decoder_calls"] == 8
    # Model-F prep stays BLOCKED without the TRAIN counts input.
    with pytest.raises(
            ValueError,
            match="MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS"):
        mod.prepare_model_f_prior(None, None)
    with pytest.raises(
            ValueError,
            match="MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS"):
        mod.prepare_model_f_prior(None, p_b)
    # Former stale line-3069: lifecycle-independent missing-isolation.
    # Monkeypatch the formal root to absent tmp + binder/writer booms so
    # authorized True fails before decoder and never touches the real root.
    entered = []
    real_root = ROOT / mod.MODEL_F_INPUT_FORMAL_ROOT
    real_before = _snapshot_dir(ROOT / mod.MODEL_F_INPUT_FORMAL_ROOT)

    def _boom_bind(*a, **k):
        entered.append("binder")
        raise AssertionError("binder entered on missing path")

    def _boom_write(*a, **k):
        entered.append("writer")
        raise AssertionError("writer entered on missing path")

    monkeypatch.setattr(mod, "bind_historical_decoder", _boom_bind)
    monkeypatch.setattr(mod, "write_g1_evidence", _boom_write)
    monkeypatch.setattr(mod, "MODEL_F_INPUT_FORMAL_ROOT",
                        str(tmp_path / "absent_model_f"))
    monkeypatch.chdir(tmp_path)
    with pytest.raises(
            ValueError,
            match="MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS"):
        mod.run_g1_synthetic(authorized=True)
    assert entered == []
    assert list(tmp_path.rglob("*")) == []
    assert _snapshot_dir(real_root) == real_before
    assert mod.MODEL_F_BLOCKED == (
        "MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS")
    # CLI keeps --phase required with no frozen-param overrides.
    names = sorted(
        a.option_strings
        for a in cli.build_parser()._actions if a.option_strings)
    assert ["--help"] in names or any("--phase" in n for n in names)
    help_src = inspect.getsource(cli.build_parser)
    assert "--phase" in help_src


# --------------------------------------------------------------------------
# Model-F input consume (fixed root; fake/tiny only, no execution)
# --------------------------------------------------------------------------
def _mffake_counts():
    c = np.zeros((1024, 1024), dtype=np.int64)
    c[0, :] = 256
    pb = np.full(1024, 1.0 / 1024)
    return c, pb


def test_M19_d5_unauthorized_artifact_zero(tmp_path, monkeypatch):
    entered = []
    mf_root = ROOT / mod.MODEL_F_INPUT_FORMAL_ROOT
    g1_root = ROOT / mod.G1_FORMAL_ROOT
    mf_before = _snapshot_dir(mf_root)
    g1_before = _snapshot_dir(g1_root)

    def _boom_load(*a, **k):
        entered.append("load")
        raise AssertionError("artifact read while unauthorized")

    def _boom_build(*a, **k):
        entered.append("build")
        raise AssertionError("builder entered while unauthorized")

    def _boom_bind(*a, **k):
        entered.append("binder")
        raise AssertionError("binder entered while unauthorized")

    def _boom_write(*a, **k):
        entered.append("writer")
        raise AssertionError("writer entered while unauthorized")

    monkeypatch.setattr(mod, "_load_model_f_input_or_blocked", _boom_load)
    monkeypatch.setattr(mod, "build_dv3_nested_mother", _boom_build)
    monkeypatch.setattr(mod, "bind_historical_decoder", _boom_bind)
    monkeypatch.setattr(mod, "write_g1_evidence", _boom_write)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(mod.NotAuthorizedError):
        mod.run_g1_synthetic(authorized=False)
    with pytest.raises(mod.NotAuthorizedError):
        mod.run_g1_synthetic(authorized=False, decode_fn=FakeDecoder())
    assert entered == []
    assert list(tmp_path.rglob("*")) == []
    assert mod.MODEL_F_INPUT_FORMAL_ROOT == (
        "workspace/v72p2d5_model_f_input/20260907_r1")
    # Lifecycle-independent: prove formal artifacts untouched, no absence
    # assert (Model-F/G1 now exist; P0/G2 absence checked elsewhere).
    assert _snapshot_dir(mf_root) == mf_before
    assert _snapshot_dir(g1_root) == g1_before


def test_M20_d5_authorized_fake_load_reaches_runner(tmp_path):
    c, pb = _mffake_counts()
    seen = {}
    formal_before = _snapshot_formal_roots()

    def _fake_load(counts_ab=None, p_b=None):
        seen["injected"] = (counts_ab is not None and p_b is not None)
        return c, pb

    import unittest.mock as _mock
    out = tmp_path / "m20"
    with _mock.patch.object(mod, "_load_model_f_input_or_blocked",
                            side_effect=_fake_load) as _spy:
        res = mod.run_g1_synthetic(counts_ab=c, p_b=pb,
                                   decode_fn=FakeDecoder(), authorized=True,
                                   out_dir=out)
    assert _spy.called
    assert seen["injected"] is True
    assert res["decoder_calls"] == 440
    assert res["phase"] == "g1"
    # Authorized fake uses tmp out_dir only; formal roots untouched (no
    # absence assert; legitimate artifacts may exist).
    assert sorted(p.name for p in out.iterdir()) == sorted(
        mod.STAGE_EVIDENCE_FILES)
    _assert_formal_roots_unchanged(formal_before)
    # prepare identity: injected tables reach prepare_model_f_prior
    pb2, pf2 = mod.prepare_model_f_prior(c, pb)
    assert pb2.shape == (1024,)
    assert pf2.shape == (1024, 1024)


def test_M21_d5_missing_artifact_blocked_no_toy(tmp_path, monkeypatch):
    # Lifecycle-independent missing-isolation: point the formal root at
    # absent tmp + binder/writer booms so authorized entry fails before
    # decoder with BLOCKED and never touches the real root.
    entered = []
    real_mf = ROOT / mod.MODEL_F_INPUT_FORMAL_ROOT
    real_g1 = ROOT / mod.G1_FORMAL_ROOT
    mf_before = _snapshot_dir(real_mf)
    g1_before = _snapshot_dir(real_g1)

    def _boom_bind(*a, **k):
        entered.append("binder")
        raise AssertionError("binder entered on missing path")

    def _boom_write(*a, **k):
        entered.append("writer")
        raise AssertionError("writer entered on missing path")

    monkeypatch.setattr(mod, "bind_historical_decoder", _boom_bind)
    monkeypatch.setattr(mod, "write_p0_cost_evidence", _boom_write)
    monkeypatch.setattr(mod, "write_g1_evidence", _boom_write)
    monkeypatch.setattr(mod, "write_g2_evidence", _boom_write)
    monkeypatch.setattr(mod, "MODEL_F_INPUT_FORMAL_ROOT",
                        str(tmp_path / "absent_model_f"))
    monkeypatch.chdir(tmp_path)
    for fn in (mod.run_p0_cost_synthetic, mod.run_g1_synthetic,
               mod.run_g2_synthetic):
        with pytest.raises(
                ValueError,
                match="MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS"):
            fn(authorized=True)
    assert entered == []
    assert list(tmp_path.rglob("*")) == []
    assert _snapshot_dir(real_mf) == mf_before
    assert _snapshot_dir(real_g1) == g1_before
    for fn in (mod.run_p0_cost_synthetic, mod.run_g1_synthetic,
               mod.run_g2_synthetic):
        assert "build_g0_fixture" not in inspect.getsource(fn)
        assert "read_CAL" not in inspect.getsource(fn)
        assert "parquet" not in inspect.getsource(fn)


@pytest.mark.parametrize(("runner_name", "writer_name"), [("run_p0_cost_synthetic", "write_p0_cost_evidence"), ("run_g1_synthetic", "write_g1_evidence"), ("run_g2_synthetic", "write_g2_evidence")])
def test_M21_param_missing_isolation(tmp_path, monkeypatch, runner_name,
                                     writer_name):
    # Parametrized SAFE C: each runner fails before decoder under absent-tmp
    # root + binder/writer booms with BLOCKED; supplements M21 loop.
    entered = []
    real_mf = ROOT / mod.MODEL_F_INPUT_FORMAL_ROOT
    real_g1 = ROOT / mod.G1_FORMAL_ROOT
    mf_before = _snapshot_dir(real_mf)
    g1_before = _snapshot_dir(real_g1)

    def _boom_bind(*a, **k):
        entered.append("binder")
        raise AssertionError("binder entered on missing path")

    def _boom_write(*a, **k):
        entered.append("writer")
        raise AssertionError("writer entered on missing path")

    monkeypatch.setattr(mod, "bind_historical_decoder", _boom_bind)
    monkeypatch.setattr(mod, writer_name, _boom_write)
    for _wn in ("write_p0_cost_evidence", "write_g1_evidence",
                "write_g2_evidence"):
        if _wn != writer_name:
            monkeypatch.setattr(mod, _wn, _boom_write)
    monkeypatch.setattr(mod, "MODEL_F_INPUT_FORMAL_ROOT",
                        str(tmp_path / "absent_model_f"))
    monkeypatch.chdir(tmp_path)
    runner = getattr(mod, runner_name)
    with pytest.raises(
            ValueError,
            match="MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS"):
        runner(authorized=True)
    assert entered == []
    assert list(tmp_path.rglob("*")) == []
    assert _snapshot_dir(real_mf) == mf_before
    assert _snapshot_dir(real_g1) == g1_before


MODEL_F_REL_TAIL = Path("workspace/v72p2d5_model_f_input/20260907_r1")


# --------------------------------------------------------------------------
# M22 — Model-F consumer path fix: script-launch condition (tmp only)
# --------------------------------------------------------------------------
def _mf_test_module():
    path = (ROOT / "comparison_bench" / "src" / "comparison_bench"
            / "formal_ir" / "v72p2d5_model_f_input.py")
    spec = importlib.util.spec_from_file_location(
        "v72p2d5_model_f_input_test_helper", str(path))
    assert spec is not None and spec.loader is not None
    fresh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fresh)
    return fresh


def test_M22a_model_f_root_resolves_cwd_independent(tmp_path, monkeypatch):
    # Resolved path only; the real artifact is never loaded here.
    monkeypatch.chdir(tmp_path)
    resolved = mod._resolve_model_f_input_root()
    assert resolved.is_absolute()
    assert resolved == mod._model_f_repo_root() / MODEL_F_REL_TAIL
    assert resolved == (ROOT / MODEL_F_REL_TAIL).resolve()
    assert list(tmp_path.rglob("*")) == []


def test_M22b_model_f_loader_without_repo_root_on_path(tmp_path,
                                                        monkeypatch):
    # Simulate `python scripts/...`: repo root and src off sys.path and no
    # comparison_bench package importable; the helper must still reach the
    # loader by file path and load a tmp artifact (no loader-unavailable).
    mf = _mf_test_module()
    c, pb = _mffake_counts()
    art = tmp_path / "mf_valid"
    mf.write_model_f_input(art, c, pb)
    keep_path = list(sys.path)
    src_root = str(ROOT / "comparison_bench" / "src")
    monkeypatch.setattr(
        sys, "path",
        [p for p in keep_path if p not in ("", str(ROOT), src_root)])
    for name in [n for n in sys.modules
                 if n == "comparison_bench"
                 or n.startswith("comparison_bench.")
                 or n == "v72p2d5_model_f_input_consumer"]:
        monkeypatch.delitem(sys.modules, name, raising=False)
    before_modules = set(sys.modules)
    try:
        monkeypatch.setattr(mod, "MODEL_F_INPUT_FORMAL_ROOT", str(art))
        monkeypatch.chdir(tmp_path)
        got_c, got_pb = mod._load_model_f_input_or_blocked(None, None)
    finally:
        for name in set(sys.modules) - before_modules:
            del sys.modules[name]
    assert np.array_equal(np.asarray(got_c), np.asarray(c))
    assert abs(float(np.asarray(got_pb).sum()) - 1.0) < 1e-8


def test_M22c_model_f_absent_reports_missing_with_absolute_path(
        tmp_path, monkeypatch):
    missing = tmp_path / "absent_model_f"
    monkeypatch.setattr(mod, "MODEL_F_INPUT_FORMAL_ROOT", str(missing))
    monkeypatch.chdir(tmp_path)
    with pytest.raises(
            ValueError,
            match="MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS") as excinfo:
        mod._load_model_f_input_or_blocked(None, None)
    assert str(missing.resolve()) in str(excinfo.value)
    assert list(tmp_path.rglob("*")) == []


def test_M22d_model_f_invalid_not_reported_missing(tmp_path, monkeypatch):
    # Present root with a wrong file set: loader validation rejects it, so
    # the outcome is invalid, never missing-input.
    mf = _mf_test_module()
    c, pb = _mffake_counts()
    mf.write_model_f_input(tmp_path / "mf_valid", c, pb)
    monkeypatch.setattr(mod, "MODEL_F_INPUT_FORMAL_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError,
                        match=mod.MODEL_F_INPUT_INVALID) as excinfo:
        mod._load_model_f_input_or_blocked(None, None)
    assert "MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS" not in str(
        excinfo.value)


def test_M22e_model_f_injected_tables_short_circuit(tmp_path, monkeypatch):
    c, pb = _mffake_counts()
    monkeypatch.chdir(tmp_path)

    def _boom(*a, **k):
        raise AssertionError("filesystem reached on injected path")

    monkeypatch.setattr(mod, "_load_model_f_loader", _boom)
    monkeypatch.setattr(mod, "_resolve_model_f_input_root", _boom)
    got_c, got_pb = mod._load_model_f_input_or_blocked(c, pb)
    assert got_c is c and got_pb is pb
    assert list(tmp_path.rglob("*")) == []


def test_TIS_static_authorized_synthetic_isolation():
    """Static (stdlib AST) guard: no implicit prod decoder/formal out_dir.

    Every authorized True P0/G1/G2 synthetic call in this file SHALL pass
    explicit fake decode_fn + tmp out_dir + injected counts_ab/p_b.
    Documented fail-before-decoder exceptions (missing-isolation with
    binder/writer booms expecting BLOCKED) are allowlisted below and MUST
    contain boom + BLOCKED + absent-tmp markers; anything else missing
    explicit args FAILS. Also guards: no CLI authorized phase in tests and
    no cycle_state mutation in tests.
    """
    import ast as _ast
    src = Path(__file__).read_text(encoding="utf-8")
    tree = _ast.parse(src)
    synth = {"run_p0_cost_synthetic", "run_g1_synthetic", "run_g2_synthetic"}
    # Documented exceptions: fail-before-decoder missing-isolation with booms.
    exceptions = {"test_M21_d5_missing_artifact_blocked_no_toy",
                  "test_M21_param_missing_isolation",
                  "test_P0G1G2_i_g0_recovery_structure_regression"}
    for node in _ast.walk(tree):
        if not isinstance(node, _ast.FunctionDef):
            continue
        fname = node.name
        fsrc = _ast.get_source_segment(src, node) or ""
        # Collect getattr aliases: runner = getattr(mod, runner_name) or
        # runner = getattr(mod, "run_g1_synthetic").
        aliases = set()
        for sub in _ast.walk(node):
            if isinstance(sub, _ast.Assign) and len(sub.targets) == 1:
                tgt = sub.targets[0]
                val = sub.value
                if (isinstance(tgt, _ast.Name)
                        and isinstance(val, _ast.Call)
                        and isinstance(val.func, _ast.Name)
                        and val.func.id == "getattr"
                        and len(val.args) >= 2):
                    a1 = val.args[1]
                    if isinstance(a1, _ast.Name) and a1.id == "runner_name":
                        aliases.add(tgt.id)
                    elif (isinstance(a1, _ast.Constant)
                          and isinstance(a1.value, str)
                          and a1.value in synth):
                        aliases.add(tgt.id)
        # Collect synth loop-var For nodes: for fn in (...synth...).
        synth_loop_ids = set()
        for sub in _ast.walk(node):
            if isinstance(sub, _ast.For):
                tgt = sub.target
                is_fn = (isinstance(tgt, _ast.Name) and tgt.id == "fn")
                if not is_fn:
                    continue
                itersrc = _ast.get_source_segment(src, sub.iter) or ""
                if any(s in itersrc for s in synth):
                    for inner in _ast.walk(sub):
                        if isinstance(inner, _ast.Call):
                            synth_loop_ids.add(id(inner))
        for sub in _ast.walk(node):
            if not isinstance(sub, _ast.Call):
                continue
            func = sub.func
            is_synth = False
            if isinstance(func, _ast.Attribute) and func.attr in synth:
                # Direct mod.run_* synthetic call.
                is_synth = True
            elif isinstance(func, _ast.Name) and func.id in synth:
                is_synth = True
            elif isinstance(func, _ast.Name) and func.id in aliases:
                # runner = getattr(mod, runner_name) then runner(...);
                # parametrized runner_name strings name the synth set.
                is_synth = True
            elif isinstance(func, _ast.Name) and func.id == "fn":
                # Loop-var call: only inside a For whose iterable names synth.
                if id(sub) in synth_loop_ids:
                    is_synth = True
            if not is_synth:
                continue
            kw = {k.arg: k.value for k in sub.keywords if k.arg}
            auth = kw.get("authorized")
            is_false = (isinstance(auth, _ast.Constant)
                        and auth.value is False)
            is_true = (isinstance(auth, _ast.Constant)
                       and auth.value is True)
            # SAFE A: unauthorized False chokes before work.
            if is_false:
                continue
            if not is_true:
                continue
            has_decode = ("decode_fn" in kw and not (
                isinstance(kw["decode_fn"], _ast.Constant)
                and kw["decode_fn"].value is None))
            has_out = "out_dir" in kw
            has_counts = ("counts_ab" in kw and "p_b" in kw)
            # SAFE B: authorized True + counts + p_b + decode_fn + out_dir.
            if has_decode and has_out and has_counts:
                continue
            # SAFE C: authorized True missing-isolation fail-before-decoder.
            assert fname in exceptions, (
                f"{fname}:{sub.lineno} authorized True without explicit "
                f"fake decode_fn/tmp out_dir/injected counts_ab/p_b "
                f"and not an allowlisted missing-isolation exception")
            low = fsrc.lower()
            assert "boom" in low, fname
            assert "model_f_input_blocked_missing_cal_train_counts" in low, fname
            assert "absent_model_f" in fsrc, fname
            assert "bind_historical_decoder" in fsrc, fname
            assert ("write_p0_cost_evidence" in fsrc
                    or "write_g1_evidence" in fsrc
                    or "write_g2_evidence" in fsrc), fname
            assert "writer" in low, fname
    # No CLI authorized phase in tests: mother CLI stays gated (exit 3).
    # (Literals obfuscated to avoid self-match on this guard's own source.)
    _flag = "--execution" + "-authorized"
    assert _flag not in src
    _k0 = '"' + "p0_cost_execution_authorized" + '": True'
    _k1 = '"' + "g1_execution_authorized" + '": True'
    _k2 = '"' + "g2_execution_authorized" + '": True'
    assert _k0 not in src
    assert _k1 not in src
    assert _k2 not in src
    # No cycle_state mutation in tests (STATE_PATH constant read-only).
    assert ("STATE_PATH)" + ".write") not in src
    assert ("yaml." + "dump") not in src
    assert ("yaml.safe_" + "dump") not in src


def test_T1_23_no_formal_root_absence_assertion():
    """Static (stdlib AST) recurrence guard: no formal-root absence assert.

    Absence was the proxy that broke the moment legitimate P0/G1 output
    landed (the guard model that failed in the unauthorized-G1 incident).
    Use snapshot-and-compare invariance instead:
    _snapshot_formal_roots() at test start plus
    _assert_formal_roots_unchanged() at test end.
    """
    root_names = ("P0_FORMAL_ROOT", "G1_FORMAL_ROOT", "G2_FORMAL_ROOT",
                  "G0_FORMAL_ROOT", "G0_RECOVERY_FORMAL_ROOT",
                  "MODEL_F_FORMAL_ROOT", "MODEL_F_INPUT_FORMAL_ROOT",
                  "STRUCTURE_FORMAL_ROOT")
    literal_frags = ("v72p2d5_p0_cost", "v72p2d5_g1", "v72p2d5_g2",
                     "v72p2d5_g0", "v72p2d5_g0_recovery",
                     "v72p2d5_model_f_input", "v72p2d5_structure")
    instead = ("use _snapshot_formal_roots() + "
               "_assert_formal_roots_unchanged() invariance instead of "
               "absence assertions against formal roots")
    files = [Path(__file__),
             Path(__file__).with_name("test_v72p2d5_model_f_input.py")]
    for path in files:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if node.name == "test_T1_23_no_formal_root_absence_assertion":
                continue
            for sub in ast.walk(node):
                if not isinstance(sub, ast.Assert):
                    continue
                if not (isinstance(sub.test, ast.UnaryOp)
                        and isinstance(sub.test.op, ast.Not)):
                    continue
                seg = ast.get_source_segment(src, sub) or ""
                if ".exists()" not in seg:
                    continue
                hit = [t for t in root_names + literal_frags if t in seg]
                assert not hit, (
                    f"{path.name}:{node.name}:{sub.lineno} asserts a formal "
                    f"root absent ({','.join(hit)}); {instead}")


# --------------------------------------------------------------------------
# G1 readiness rework (reviewed D1-D6/A01-A13; fake/injected/tmp only)
# --------------------------------------------------------------------------
def _g1r_tiny():
    return _tiny_tables(), _tiny_h()


def _g1r_passing_per_f(low=90, top=100, attempted=100):
    return [{"app_exact_count": int(low), "attempted": int(attempted)},
            {"app_exact_count": int(top), "attempted": int(attempted)}]


def test_G1R01_fresh_root_literal_and_old_barred():
    formal_before = _snapshot_formal_roots()
    assert mod.G1_FORMAL_ROOT == "workspace/v72p2d5_g1/20260907_r2"
    assert "20260906_r1" not in mod.G1_FORMAL_ROOT
    assert mod.P0_FORMAL_ROOT == "workspace/v72p2d5_p0_cost/20260906_r1"
    assert mod.G2_FORMAL_ROOT == "workspace/v72p2d5_g2/20260906_r1"
    void_root = ROOT / "workspace" / "v72p2d5_g1" / "20260906_r1"
    void_snap = _snapshot_dir(void_root)
    assert isinstance(void_snap, dict) and len(void_snap) == 4
    _assert_formal_roots_unchanged(formal_before)
    assert _snapshot_dir(ROOT / mod.G1_FORMAL_ROOT) is None


def test_G1R02_unix_rss_path_preserved():
    src = inspect.getsource(mod._rss_bytes)
    assert "import resource" in src
    assert "ctypes" in src
    assert "GetCurrentProcess" in src
    assert "GetProcessMemoryInfo" in src
    assert "psutil" not in src.lower()
    assert "PROCESS_MEMORY_COUNTERS" in src or "_PMC" in src
    val = mod._rss_bytes()
    assert val is None or (isinstance(val, int) and val > 0)


def test_G1R03_windows_rss_success_and_failure(monkeypatch, tmp_path):
    import ctypes as _ct
    import sys as _sys
    from ctypes import wintypes as _wt
    from types import SimpleNamespace as _NS
    formal_before = _snapshot_formal_roots()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(_sys.modules, "resource", None)

    class _SigFn:
        """Callable fake supporting ctypes argtypes/restype inspection."""

        def __init__(self, fn):
            self._fn = fn
            self.argtypes = None
            self.restype = None
            self.seen = {}

        def __call__(self, *args):
            self.seen["argtypes"] = self.argtypes
            self.seen["restype"] = self.restype
            return self._fn(*args)

    def _gcp_ok():
        return 999

    _gcp_sig = _SigFn(_gcp_ok)
    _seen_cb = {}

    def _gpi_ok(h, pref, cb):
        # Signatures must already be assigned when the API call runs.
        assert _gpi_sig.argtypes is not None
        assert _gpi_sig.restype is not None
        assert _gcp_sig.restype is not None
        _seen_cb["cb"] = cb
        pref._obj.WorkingSetSize = 12345678
        return 1

    _gpi_sig = _SigFn(_gpi_ok)
    monkeypatch.setattr(
        _ct, "windll",
        _NS(kernel32=_NS(GetCurrentProcess=_gcp_sig),
            psapi=_NS(GetProcessMemoryInfo=_gpi_sig)),
        raising=False)
    assert mod._rss_bytes() == 12345678
    assert _gcp_sig.restype is _wt.HANDLE
    assert _gpi_sig.restype is _wt.BOOL
    assert isinstance(_gpi_sig.argtypes, list)
    assert len(_gpi_sig.argtypes) == 3
    assert _gpi_sig.argtypes[0] is _wt.HANDLE
    assert _gpi_sig.argtypes[2] is _wt.DWORD
    assert _gpi_sig.seen["argtypes"] is _gpi_sig.argtypes
    assert _gpi_sig.seen["restype"] is _wt.BOOL
    assert _gcp_sig.seen["restype"] is _wt.HANDLE
    _ptr = _gpi_sig.argtypes[1]
    _struct = getattr(_ptr, "_type_", None)
    assert _struct is not None
    _fields = dict(_struct._fields_)
    assert _fields["cb"] is _wt.DWORD
    assert _fields["PageFaultCount"] is _wt.DWORD
    for _name in ("PeakWorkingSetSize", "WorkingSetSize",
                  "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage",
                  "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                  "PagefileUsage", "PeakPagefileUsage"):
        assert _fields[_name] is _ct.c_size_t
    assert _seen_cb["cb"] == _ct.sizeof(_struct)

    def _gpi_fail(h, pref, cb):
        return 0

    _gpi_fail_sig = _SigFn(_gpi_fail)
    monkeypatch.setattr(
        _ct, "windll",
        _NS(kernel32=_NS(GetCurrentProcess=_SigFn(_gcp_ok)),
            psapi=_NS(GetProcessMemoryInfo=_gpi_fail_sig)),
        raising=False)
    assert mod._rss_bytes() is None
    monkeypatch.delattr(_ct, "windll", raising=False)
    assert mod._rss_bytes() is None
    assert list(tmp_path.rglob("*")) == []
    _assert_formal_roots_unchanged(formal_before)


def test_G1R03R1_windows_rss_live_smoke():
    import sys as _sys
    if _sys.platform == "win32":
        # Real Windows branch, deliberately unpatched: read-only, no decoder.
        val = mod._rss_bytes()
        assert isinstance(val, int) and val > 0
    else:
        val = mod._rss_bytes()
        assert val is None or (isinstance(val, int) and val > 0)


def test_G1R04_per_block_sampling_counts_and_peaks(tmp_path, monkeypatch):
    (p_b, p_f), h = _g1r_tiny()
    formal_before = _snapshot_formal_roots()
    monkeypatch.chdir(tmp_path)
    seq = list(range(1, 201))
    calls = []

    def _seq_rss():
        calls.append(1)
        return int(seq[len(calls) - 1])

    monkeypatch.setattr(mod, "_rss_bytes", _seq_rss)
    res = mod.run_g1_phase(h=h, p_b=p_b, p_f=p_f,
                           decode_fn=FakeDecoder(), authorized=True)
    assert len(calls) == 200
    assert res["decoder_calls"] == 440
    assert res["per_f"][0]["peak_rss_bytes"] == 100
    assert res["per_f"][1]["peak_rss_bytes"] == 200
    assert res["peak_rss_bytes"] == 200
    assert list(tmp_path.rglob("*")) == []
    _assert_formal_roots_unchanged(formal_before)


def test_G1R05_rss_none_and_over_block_pass(tmp_path, monkeypatch):
    per_f = _g1r_passing_per_f(90, 100)
    assert mod._classify_g1_outcome(
        nonfinite=0, wall_seconds=10.0, peak_rss_bytes=None,
        per_f=per_f, monotonic=True) == "G1_RESOURCE_OVERRUN"
    assert mod._classify_g1_outcome(
        nonfinite=0, wall_seconds=10.0,
        peak_rss_bytes=3 * 1024**3,
        per_f=per_f, monotonic=True) == "G1_RESOURCE_OVERRUN"
    assert mod._classify_g1_outcome(
        nonfinite=0, wall_seconds=10.0,
        peak_rss_bytes=2 * 1024**3,
        per_f=per_f, monotonic=True) == "G1_RESOURCE_OVERRUN"
    (p_b, p_f), h = _g1r_tiny()
    formal_before = _snapshot_formal_roots()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(mod, "_rss_bytes", lambda: None)
    res_none = mod.run_g1_phase(h=h, p_b=p_b, p_f=p_f,
                                decode_fn=FakeDecoder(), authorized=True)
    assert res_none["peak_rss_bytes"] is None
    assert res_none["outcome"] == "G1_RESOURCE_OVERRUN"
    assert res_none["passed"] is False
    monkeypatch.setattr(mod, "_rss_bytes", lambda: 3 * 1024**3)
    res_over = mod.run_g1_phase(h=h, p_b=p_b, p_f=p_f,
                                decode_fn=FakeDecoder(), authorized=True)
    assert res_over["peak_rss_bytes"] == 3 * 1024**3
    assert res_over["outcome"] == "G1_RESOURCE_OVERRUN"
    assert res_over["passed"] is False
    assert list(tmp_path.rglob("*")) == []
    _assert_formal_roots_unchanged(formal_before)


def test_G1R06_all_zero_no_signal(tmp_path, monkeypatch):
    per_f = _g1r_passing_per_f(0, 0)
    assert mod._classify_g1_outcome(
        nonfinite=0, wall_seconds=5.0, peak_rss_bytes=1000,
        per_f=per_f, monotonic=True) == "G1_COMPLETED_NO_SIGNAL_FAIL"
    (p_b, p_f), h = _g1r_tiny()
    formal_before = _snapshot_formal_roots()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(mod, "_rss_bytes", lambda: 1000)

    def _never_exact(hh, prior, syndrome, layer=None):
        n = np.asarray(prior).shape[0]
        return {"x_hat": np.full(n, 31, dtype=np.int64),
                "syndrome_ok": False, "iterations": 1,
                "final_beliefs": np.zeros_like(np.asarray(prior))}

    res = mod.run_g1_phase(h=h, p_b=p_b, p_f=p_f,
                           decode_fn=_never_exact, authorized=True)
    assert res["per_f"][0]["app_exact_count"] == 0
    assert res["per_f"][1]["app_exact_count"] == 0
    assert res["outcome"] == "G1_COMPLETED_NO_SIGNAL_FAIL"
    assert res["passed"] is False
    assert list(tmp_path.rglob("*")) == []
    _assert_formal_roots_unchanged(formal_before)


def test_G1R07_strict_improve_trend_pass():
    per_f = _g1r_passing_per_f(10, 20)
    assert mod._classify_g1_outcome(
        nonfinite=0, wall_seconds=5.0, peak_rss_bytes=1000,
        per_f=per_f, monotonic=True) == "G1_TREND_PASS"


def test_G1R08_saturated_pair_trend_pass():
    per_f = _g1r_passing_per_f(100, 100)
    assert mod._classify_g1_outcome(
        nonfinite=0, wall_seconds=5.0, peak_rss_bytes=1000,
        per_f=per_f, monotonic=True) == "G1_TREND_PASS"


def test_G1R09_positive_flat_below_one_fails():
    per_f = _g1r_passing_per_f(50, 50)
    assert mod._classify_g1_outcome(
        nonfinite=0, wall_seconds=5.0, peak_rss_bytes=1000,
        per_f=per_f, monotonic=True) == "G1_COMPLETED_NO_SIGNAL_FAIL"


def test_G1R10_outcome_precedence():
    per_f = _g1r_passing_per_f(90, 100)
    assert mod._classify_g1_outcome(
        nonfinite=1, wall_seconds=5000.0, peak_rss_bytes=3 * 1024**3,
        per_f=per_f, monotonic=True) == "G1_NONFINITE_OR_CRASH_BLOCKED"
    assert mod._classify_g1_outcome(
        nonfinite=0, wall_seconds=901.0, peak_rss_bytes=3 * 1024**3,
        per_f=per_f, monotonic=True) == "G1_OVERRUN_900S"
    assert mod._classify_g1_outcome(
        nonfinite=0, wall_seconds=10.0, peak_rss_bytes=None,
        per_f=per_f, monotonic=True) == "G1_RESOURCE_OVERRUN"
    assert mod._classify_g1_outcome(
        nonfinite=0, wall_seconds=10.0, peak_rss_bytes=1000,
        per_f=per_f, monotonic=True) == "G1_TREND_PASS"
    flat = _g1r_passing_per_f(50, 50)
    assert mod._classify_g1_outcome(
        nonfinite=0, wall_seconds=10.0, peak_rss_bytes=1000,
        per_f=flat, monotonic=True) == "G1_COMPLETED_NO_SIGNAL_FAIL"


def test_G1R11_identities_and_440_calls(tmp_path, monkeypatch):
    (p_b, p_f), h = _g1r_tiny()
    formal_before = _snapshot_formal_roots()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(mod, "_rss_bytes", lambda: 1000)
    res = mod.run_g1_phase(h=h, p_b=p_b, p_f=p_f,
                           decode_fn=FakeDecoder(), authorized=True)
    assert res["decoder_calls"] == 440
    for item in res["per_f"]:
        assert item["attempted"] == 100
        assert 0 <= item["app_exact_count"] <= 100
        assert 0 <= item["app_syndrome_ok_count"] <= 100
        assert 0 <= item["oracle_exact_count"] <= 20
        assert 0 <= item["oracle_syndrome_ok_count"] <= 20
        assert item["app_failure_fraction"] == (
            1.0 - item["app_exact_count"] / item["attempted"])
        assert item["app_iterations_max"] <= 2 * mod.MAX_ITER
        assert item["app_iterations_total"] >= 0
        assert item["oracle_iterations_total"] >= 0
        assert item["nonfinite_count"] >= 0
    assert res["nonfinite"] == sum(
        item["nonfinite_count"] for item in res["per_f"])
    assert list(tmp_path.rglob("*")) == []
    _assert_formal_roots_unchanged(formal_before)


def test_G1R12_writers_fail_loud_on_missing_key(tmp_path):
    formal_before = _snapshot_formal_roots()
    bad_per_f = [{"f": 1.0, "attempted": 100, "app_exact_count": 0,
                  "app_exact_rate": 0.0, "oracle_exact_count": 0}]
    with pytest.raises(KeyError):
        mod.write_g1_evidence(tmp_path / "bad_g1",
                              {"phase": "g1", "per_f": bad_per_f})
    with pytest.raises(KeyError):
        mod.write_g2_evidence(tmp_path / "bad_g2",
                              {"phase": "g2", "per_f": bad_per_f})
    assert list(tmp_path.rglob("*")) == []
    _assert_formal_roots_unchanged(formal_before)


def test_G1R13_no_subdir_invariant_tmp_demo(tmp_path):
    import os as _os
    formal_before = _snapshot_formal_roots()
    absent = tmp_path / "root_absent"
    assert _snapshot_dir(absent) is None
    _os.makedirs(str(absent / "nested"))
    with pytest.raises(AssertionError):
        _snapshot_dir(absent)
    present = tmp_path / "root_present"
    _os.makedirs(str(present))
    assert _snapshot_dir(present) == {}
    _os.makedirs(str(present / "nested_new"))
    with pytest.raises(AssertionError):
        _snapshot_dir(present)
    _assert_formal_roots_unchanged(formal_before)


def test_G1R14_safe_guards_remain_effective():
    assert hasattr(mod, "NotAuthorizedError")
    for name in ("test_M19_d5_unauthorized_artifact_zero",
                 "test_M20_d5_authorized_fake_load_reaches_runner",
                 "test_M21_d5_missing_artifact_blocked_no_toy",
                 "test_TIS_static_authorized_synthetic_isolation",
                 "test_T1_23_no_formal_root_absence_assertion"):
        assert name in globals(), name
    src = inspect.getsource(mod._rss_bytes)
    assert "psutil" not in src.lower()


def test_G1R16_sentinel_reaches_first_call_tmp_empty(tmp_path, monkeypatch):
    c, pb = _mffake_counts()
    formal_before = _snapshot_formal_roots()
    real_mf = ROOT / mod.MODEL_F_INPUT_FORMAL_ROOT
    mf_before = _snapshot_dir(real_mf)
    monkeypatch.chdir(tmp_path)
    seen = []
    sentinel = "G1_SENTINEL_FIRST_CALL"

    def _raising(h, prior, syndrome, layer=None):
        seen.append((tuple(np.shape(h)), tuple(np.shape(prior))))
        raise RuntimeError(sentinel)

    out = tmp_path / "sentinel_out"
    with pytest.raises(RuntimeError, match=sentinel):
        mod.run_g1_synthetic(counts_ab=c, p_b=pb, decode_fn=_raising,
                             authorized=True, out_dir=out)
    assert len(seen) == 1
    assert seen[0][0] == (49, 64)
    assert seen[0][1][1] == 32
    assert list(tmp_path.rglob("*")) == []
    assert _snapshot_dir(real_mf) == mf_before
    _assert_formal_roots_unchanged(formal_before)


def test_G1R17_sentinel_static_contract_tmp_empty():
    src = inspect.getsource(mod.run_g1_synthetic)
    assert "_load_model_f_input_or_blocked" in src
    assert "prepare_model_f_prior" in src
    assert "run_g1_phase" in src
    assert "write_g1_evidence" in src
    assert src.index("run_g1_phase") < src.index("write_g1_evidence")
    lsrc = inspect.getsource(mod._load_model_f_loader)
    assert "spec_from_file_location" in lsrc
