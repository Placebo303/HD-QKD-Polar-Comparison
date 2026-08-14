"""V11 full-vector spatially coupled MC-DE kernel tests (V11-20.2, T0/T1).

T0: module import/exports, frozen constants (seed prefix, harmonic tol, the
exactly-three frozen geometries G1-G3 = V11-A07), the frozen V10 S1/S3 winner
reuse (V11-A06), signatures, fail-closed domain validation, chain structure,
and the no-production-import boundary.

T1 — the four verification families:

- **collapse (V11-A03)**: ``w=0`` / a single spatial position degenerates to
  the exact V8/V9 uncoupled semantics — byte-identical to the V9 uncoupled
  run, float-close to the V8 run, and statistically consistent for a
  multi-position ``w=0`` chain;
- **oracle (V11-A04)**: q=4/q=8 full-vector check/variable/belief updates
  agree with the independent V8 direct probability-domain oracle
  (``oracle_check_update_dense`` / ``oracle_variable_update``) on constant
  (deterministic) populations within the frozen MC tolerance 1e-9;
- **normalization / noiseless-limit**: outputs stay finite, nonnegative and
  normalized (row sums within 1e-9); the ``p -> 0`` channel message gives
  deterministic correct messages; the all-zero input fails closed;
- **harmonic rate (V11-A05)**: the terminated-rate formula
  ``R_L = 1 - ((L+w)/L)(1 - R_base)`` and the degree-distribution
  reconstructed rate agree within ``1e-12`` for ``w = 1, 2`` and several
  ``L`` values, including the frozen G1-G3 x S1/S3 geometry set.

V8 is a test-only oracle import (same boundary as the V9 test suite); the V11
kernel itself never imports it.
"""
from __future__ import annotations

import inspect
import math
import re
import types

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v11_mcde as v11
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v8_mcde as v8
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v9_mcde as v9
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v10_common as common
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v8_reference as ref
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField

FIELD4 = GF2mField.create(4)
FIELD8 = GF2mField.create(8)

#: Frozen tolerance for the full-vector updates vs the V8 direct oracle
#: (same frozen MC tolerance as the V9 test suite).
_ORACLE_TOL = 1e-9
#: Frozen tolerance for the w=0 collapse vs the V8 uncoupled run.
_COLLAPSE_TOL = 1e-9
#: MC statistical tolerance for the multi-position w=0 collapse comparison.
_MC_ENTROPY_TOL = 0.02
_MC_ITER_TOL = 5

V11_MODULE_PATH = "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v11_mcde.py"


def _constant_population(vector: np.ndarray, n: int) -> np.ndarray:
    return np.stack([vector] * n)


def _regular_config():
    return {3: 1.0}, {6: 1.0}


# --------------------------------------------------------------------------- #
# T0: import, constants, signatures, fail-closed domain
# --------------------------------------------------------------------------- #


def test_module_import_and_all_exports():
    expected = {
        "V11_SEED_PREFIX", "V11_DRY_RUN_SEED", "FROZEN_GEOMETRIES",
        "HARMONIC_TOL", "V10_WINNER_S1", "V10_WINNER_S3",
        "V10_WINNER_S1_RATE", "V10_WINNER_S3_RATE",
        "v11_seed", "parse_degree_hist", "fwht_batched", "entropy_base_q",
        "chain_structure", "variable_update_coupled", "check_update_coupled",
        "belief_update_coupled", "run_coupled_mcde", "terminated_rate",
        "base_rate", "rate_contract",
    }
    assert expected <= set(v11.__all__)


def test_frozen_seed_prefix_and_geometry_set():
    # V11-A07: the formal packet contains exactly G1, G2, G3 and no other
    # geometry.
    assert v11.V11_SEED_PREFIX == "202611"
    assert v11.V11_DRY_RUN_SEED == 2026110101
    assert v11.HARMONIC_TOL == 1e-12
    assert v11.FROZEN_GEOMETRIES == {
        "G1": {"w": 1, "L": 32, "W": 8},    # low-latency primary
        "G2": {"w": 2, "L": 32, "W": 16},   # wider-coupling sensitivity
        "G3": {"w": 2, "L": 32, "W": 32},   # full-chain control
    }


def test_v11_seed_rule():
    assert v11.v11_seed("probe") == v11.v11_seed("probe")
    assert v11.v11_seed("a") != v11.v11_seed("b")
    # Disjoint by construction from the V10 seed family (different prefix).
    assert v11.v11_seed("a") != common.v10_seed("a")
    assert 0 <= v11.v11_seed("a") < 2 ** 32


def test_frozen_v10_winners_reused_without_optimization():
    # V11-A06: the frozen V10 S1/S3 winners validate under the V10 frozen
    # K=8 sparse representation and are embedded verbatim.
    for winner in (v11.V10_WINNER_S1, v11.V10_WINNER_S3):
        canonical = v11.lambda_validate(winner)  # K=8, degrees 2..40, min 0.01
        assert canonical == winner
        assert len(winner) == 8
        assert len(set(winner)) == 8
        assert abs(sum(winner.values()) - 1.0) < 1e-12


def test_frozen_v10_winner_rates_match_design_formula():
    # design.md §3: R_eff,s = 1 - f_s * H_q(p_s) with q=1024, f_s=1.15.
    assert abs(v11.V10_WINNER_S1_RATE
               - (1.0 - 1.15 * common.qary_entropy_bits_baseq(1024, 0.20))) < 1e-12
    assert abs(v11.V10_WINNER_S3_RATE
               - (1.0 - 1.15 * common.qary_entropy_bits_baseq(1024, 0.30))) < 1e-12


def test_function_signatures():
    assert list(inspect.signature(v11.run_coupled_mcde).parameters)[:4] == \
        ["q", "lambda_edge", "rho_edge", "p"]
    run_params = inspect.signature(v11.run_coupled_mcde).parameters
    for name in ("L", "w", "W", "n_samples", "max_iter", "seed",
                 "entropy_tol", "streak"):
        assert name in run_params
    assert list(inspect.signature(v11.variable_update_coupled).parameters)[:6] == \
        ["c2v", "position", "dv_degrees", "dv_probs", "channel", "rng"]
    assert list(inspect.signature(v11.check_update_coupled).parameters)[:6] == \
        ["v2c", "position", "dc_degrees", "dc_probs", "rng", "q"]
    assert list(inspect.signature(v11.belief_update_coupled).parameters)[:6] == \
        ["c2v", "position", "dv_degrees", "dv_probs", "channel", "rng"]
    assert list(inspect.signature(v11.rate_contract).parameters)[:4] == \
        ["L", "w", "R_eff", "lambda_edge"]


def test_chain_structure():
    structure = v11.chain_structure(4, 2)
    assert structure["n_vn"] == 4
    assert structure["n_check"] == 6
    # uniform spreading over offsets 0..w: VN c connects to checks c..c+w
    assert structure["vn_neighbors"][0] == [0, 1, 2]
    assert structure["vn_neighbors"][3] == [3, 4, 5]
    # boundary truncation on the check side
    assert structure["check_neighbors"][0] == [0]
    assert structure["check_neighbors"][2] == [0, 1, 2]
    assert structure["check_neighbors"][5] == [3]
    with pytest.raises(ValueError):
        v11.chain_structure(2, 2)  # w must be < window


def test_fail_closed_run_domain_validation():
    lam, rho = _regular_config()
    good = dict(q=4, lambda_edge=lam, rho_edge=rho, p=0.1, L=4, w=1, W=4,
                n_samples=100, max_iter=3, seed=1)
    v11.run_coupled_mcde(**good)  # smoke: a valid call executes
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "q": 3})
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "q": 2048})
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "p": 0.0})
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "p": 0.75})  # (q-1)/q boundary excluded
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "L": 0})
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "w": 4})     # w must be < L
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "w": -1})
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "W": 0})
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "W": 5})     # W must be <= L
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "n_samples": 99})
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "max_iter": 0})
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "max_iter": 2001})
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "seed": 1.5})
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "entropy_tol": 0.0})
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "streak": 0})
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "lambda_edge": {}})
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(**{**good, "rho_edge": {3: math.nan}})


# --------------------------------------------------------------------------- #
# T1-A03: collapse to the V8/V9 uncoupled semantics
# --------------------------------------------------------------------------- #


def test_collapse_single_position_byte_identical_v9():
    """A single spatial position (L=1, w=0, W=1) reproduces the V9 uncoupled
    run byte-for-byte: same RNG trajectory, same WHT arithmetic."""
    lam, rho = _regular_config()
    for seed in (2026110201, 2026110202):
        coupled = v11.run_coupled_mcde(4, lam, rho, 0.1, L=1, w=0, W=1,
                                       n_samples=500, max_iter=60, seed=seed)
        uncoupled = v9.run_mcde(4, lam, rho, 0.1, n_samples=500, max_iter=60,
                                seed=seed)
        assert coupled["entropy_trace"] == uncoupled["entropy_trace"]
        assert coupled["error_trace"] == uncoupled["error_trace"]
        assert coupled["iterations"] == uncoupled["iterations"]
        assert coupled["converged"] == uncoupled["converged"]


def test_collapse_single_position_matches_v8_within_tolerance():
    """Same collapse against the V8 run: identical RNG trajectory, pairwise-XOR
    vs WHT arithmetic differ only at float precision."""
    lam, rho = _regular_config()
    coupled = v11.run_coupled_mcde(4, lam, rho, 0.1, L=1, w=0, W=1,
                                   n_samples=500, max_iter=60, seed=2026110203)
    uncoupled = v8.run_mcde(4, lam, rho, 0.1, n_samples=500, max_iter=60,
                            seed=2026110203)
    assert len(coupled["entropy_trace"]) == len(uncoupled["entropy_trace"])
    diff = np.max(np.abs(np.asarray(coupled["entropy_trace"])
                         - np.asarray(uncoupled["entropy_trace"])))
    assert diff < _COLLAPSE_TOL
    assert coupled["iterations"] == uncoupled["iterations"]
    assert coupled["converged"] == uncoupled["converged"]


def test_collapse_w0_multi_position_matches_uncoupled():
    """w=0 decouples the chain: the multi-position coupled run behaves like
    the uncoupled run (same convergence, entropy within MC tolerance)."""
    lam, rho = _regular_config()
    coupled = v11.run_coupled_mcde(4, lam, rho, 0.05, L=3, w=0, W=3,
                                   n_samples=500, max_iter=100, seed=2026110204)
    uncoupled = v8.run_mcde(4, lam, rho, 0.05, n_samples=500, max_iter=100,
                            seed=2026110204)
    assert coupled["converged"] == uncoupled["converged"] is True
    assert abs(coupled["entropy_trace"][-1] - uncoupled["entropy_trace"][-1]) < _MC_ENTROPY_TOL
    assert abs(coupled["iterations"] - uncoupled["iterations"]) <= _MC_ITER_TOL


def test_collapse_update_semantics_equal_uncoupled():
    """With a constant population every sampled row equals the same vector, so
    the coupled w=0 updates reproduce the V9 uncoupled updates exactly."""
    q, n = 4, 64
    rng = np.random.default_rng(2026110205)
    msg = np.array([0.5, 0.25, 0.25, 0.0])
    ch = np.array([0.7, 0.1, 0.1, 0.1])
    pop = _constant_population(msg, n)
    chpop = _constant_population(ch, n)
    v_out = v11.variable_update_coupled([pop], 0, [3], [1.0], chpop, rng, q, w=0, window=1)
    v_ref = v9.variable_update_mcde(pop, [3], [1.0], chpop, rng, q)
    assert np.array_equal(v_out, v_ref)
    c_out = v11.check_update_coupled([pop], 0, [3], [1.0], rng, q, w=0, window=1)
    c_ref = v9.check_update_mcde(pop, [3], [1.0], rng, q)
    assert np.array_equal(c_out, c_ref)
    b_out = v11.belief_update_coupled([pop], 0, [3], [1.0], chpop, rng, q, w=0, window=1)
    b_ref = v9.belief_update_mcde(pop, [3], [1.0], chpop, rng, q)
    assert np.array_equal(b_out, b_ref)


# --------------------------------------------------------------------------- #
# T1-A04: full-vector updates vs the V8 direct oracle (q=4, q=8)
# --------------------------------------------------------------------------- #


def test_check_update_oracle_q4_q8():
    """Constant (deterministic) populations remove the MC draw randomness: the
    coupled check update must equal the V8 direct dense oracle (all-unity
    coefficients, zero syndrome) within 1e-9 — for w=0 and for the w=1 uniform
    mixture over identical populations."""
    rng = np.random.default_rng(2026110210)
    n = 64
    cases = (
        (4, FIELD4, np.array([0.5, 0.25, 0.25, 0.0])),
        (4, FIELD4, np.array([0.8, 0.05, 0.1, 0.05])),
        (4, FIELD4, np.array([0.25, 0.25, 0.25, 0.25])),
        (8, FIELD8, np.array([0.4, 0.1, 0.1, 0.1, 0.05, 0.05, 0.1, 0.1])),
        (8, FIELD8, np.array([0.5, 0.05, 0.05, 0.05, 0.05, 0.2, 0.05, 0.05])),
        (8, FIELD8, np.array([0.125] * 8)),
    )
    comparisons = 0
    for q, field, msg in cases:
        pop = _constant_population(msg, n)
        for dc in (3, 4, 5):
            oracle = ref.oracle_check_update_dense([msg] * dc, [1] * dc, 0, 0, field)
            assert oracle is not None
            out_w0 = v11.check_update_coupled([pop], 0, [dc], [1.0], rng, q, w=0, window=1)
            assert np.max(np.abs(out_w0 - oracle)) < _ORACLE_TOL, (q, dc, "w0")
            out_w1 = v11.check_update_coupled([pop, pop], 1, [dc], [1.0], rng, q, w=1, window=2)
            assert np.max(np.abs(out_w1 - oracle)) < _ORACLE_TOL, (q, dc, "w1")
            comparisons += 2
    assert comparisons == 6 * 3 * 2


def test_variable_and_belief_update_oracle_q4_q8():
    """Variable (extrinsic, dv-1 messages) and belief (dv messages) updates on
    constant populations equal the V8 oracle ``oracle_variable_update`` within
    1e-9."""
    rng = np.random.default_rng(2026110211)
    n = 64
    cases = (
        (4, FIELD4, np.array([0.5, 0.25, 0.25, 0.0]), np.array([0.7, 0.1, 0.1, 0.1])),
        (8, FIELD8, np.array([0.4, 0.1, 0.1, 0.1, 0.05, 0.05, 0.1, 0.1]),
         np.array([0.3, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])),
    )
    comparisons = 0
    for q, _field, msg, ch in cases:
        pop = _constant_population(msg, n)
        chpop = _constant_population(ch, n)
        for dv in (3, 4, 5):
            oracle_v = ref.oracle_variable_update(ch, [msg] * (dv - 1))
            oracle_b = ref.oracle_variable_update(ch, [msg] * dv)
            assert oracle_v is not None and oracle_b is not None
            out_v = v11.variable_update_coupled([pop], 0, [dv], [1.0], chpop, rng, q, w=0, window=1)
            out_b = v11.belief_update_coupled([pop], 0, [dv], [1.0], chpop, rng, q, w=0, window=1)
            assert np.max(np.abs(out_v - oracle_v)) < _ORACLE_TOL, (q, dv, "variable")
            assert np.max(np.abs(out_b - oracle_b)) < _ORACLE_TOL, (q, dv, "belief")
            comparisons += 2
    assert comparisons == 2 * 3 * 2


# --------------------------------------------------------------------------- #
# T1: normalization / noiseless limit / all-zero fail-closed
# --------------------------------------------------------------------------- #


def test_updates_output_normalized_finite_nonnegative():
    """Every update output stays finite, nonnegative and normalized (row sums
    within 1e-9), across q=4/q=8 and several (w, window) mixtures."""
    rng = np.random.default_rng(2026110212)
    for q in (4, 8):
        n = 100
        channel_vec = rng.random(q)
        channel_vec /= channel_vec.sum()
        check_vec = rng.random(q)
        check_vec /= check_vec.sum()
        for w, window in ((0, 1), (1, 2), (2, 3)):
            v2c = [_constant_population(check_vec, n) for _ in range(window)]
            c2v = [_constant_population(check_vec, n) for _ in range(window + w)]
            chpop = _constant_population(channel_vec, n)
            outputs = (
                v11.variable_update_coupled(c2v, 0, [3, 4], [0.5, 0.5], chpop, rng, q,
                                            w=w, window=window),
                v11.check_update_coupled(v2c, window - 1, [3, 4], [0.5, 0.5], rng, q,
                                         w=w, window=window),
                v11.belief_update_coupled(c2v, 0, [3, 4], [0.5, 0.5], chpop, rng, q,
                                          w=w, window=window),
            )
            for out in outputs:
                assert np.all(np.isfinite(out))
                assert np.all(out >= 0.0)
                assert np.max(np.abs(out.sum(axis=1) - 1.0)) < 1e-9


def test_run_trace_finite_and_bounded():
    """A small coupled run produces finite, bounded traces; rerunning with the
    same seed reproduces them exactly (determinism)."""
    lam, rho = _regular_config()
    first = v11.run_coupled_mcde(4, lam, rho, 0.05, L=4, w=1, W=4,
                                 n_samples=500, max_iter=100, seed=2026110213)
    second = v11.run_coupled_mcde(4, lam, rho, 0.05, L=4, w=1, W=4,
                                  n_samples=500, max_iter=100, seed=2026110213)
    assert first["entropy_trace"] == second["entropy_trace"]
    assert first["error_trace"] == second["error_trace"]
    assert first["converged"] is True
    assert all(math.isfinite(value) and 0.0 <= value <= 1.0
               for value in first["entropy_trace"])
    assert all(math.isfinite(value) and 0.0 <= value <= 1.0
               for value in first["error_trace"])
    assert all(math.isfinite(value) and 0.0 <= value <= 1.0
               for value in first["final_per_position_entropy"])


def test_noiseless_limit_channel_delta():
    """p -> 0: the channel message is delta at 0 and the updates emit
    deterministic correct messages (mass at symbol 0 >= 1 - 1e-9)."""
    q, n = 4, 64
    rng = np.random.default_rng(2026110214)
    e0 = np.array([1.0, 0.0, 0.0, 0.0])
    delta_pop = _constant_population(e0, n)
    uniform_pop = np.full((n, q), 0.25)
    out = v11.variable_update_coupled([uniform_pop], 0, [3], [1.0], delta_pop, rng, q,
                                      w=0, window=1)
    assert np.all(np.argmax(out, axis=1) == 0)
    assert np.min(out[:, 0]) >= 1.0 - 1e-9
    cout = v11.check_update_coupled([delta_pop], 0, [3], [1.0], rng, q, w=0, window=1)
    assert np.all(np.argmax(cout, axis=1) == 0)
    assert np.min(cout[:, 0]) >= 1.0 - 1e-9


def test_p_zero_and_saturation_rejected_fail_closed():
    lam, rho = _regular_config()
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(4, lam, rho, 0.0, L=2, w=1, W=2,
                             n_samples=500, max_iter=60, seed=1)
    with pytest.raises(ValueError):
        v11.run_coupled_mcde(4, lam, rho, 0.75, L=2, w=1, W=2,
                             n_samples=500, max_iter=60, seed=1)


def test_all_zero_input_fail_closed():
    q, n = 4, 64
    rng = np.random.default_rng(2026110215)
    zero = np.zeros((n, q))
    good = np.full((n, q), 0.25)
    with pytest.raises(ValueError):
        v11.variable_update_coupled([good], 0, [3], [1.0], zero, rng, q, w=0, window=1)
    with pytest.raises(ValueError):
        v11.check_update_coupled([zero], 0, [3], [1.0], rng, q, w=0, window=1)
    with pytest.raises(ValueError):
        v11.belief_update_coupled([good], 0, [3], [1.0], zero, rng, q, w=0, window=1)
    with pytest.raises(ValueError):
        v11.entropy_base_q(zero)


# --------------------------------------------------------------------------- #
# T1-A05: terminated-rate formula vs reconstructed degree-distribution rate
# --------------------------------------------------------------------------- #


def test_rate_contract_formula_1e12():
    """For w = 1, 2 and several L: the check distribution reconstructed
    harmonically at R_base reproduces R_base, and the terminated rate R_L
    recovers R_eff, both within 1e-12."""
    for L in (8, 16, 32):
        for w in (1, 2):
            for winner, rate in ((v11.V10_WINNER_S1, v11.V10_WINNER_S1_RATE),
                                 (v11.V10_WINNER_S3, v11.V10_WINNER_S3_RATE)):
                contract = v11.rate_contract(L, w, rate, winner)
                assert contract["ok"], (L, w, contract)
                assert abs(contract["rate_reconstructed_base"] - contract["R_base"]) < 1e-12
                assert abs(v11.terminated_rate(L, w, contract["R_base"]) - rate) < 1e-12


def test_rate_contract_formula_direct():
    """Direct evaluation of the design.md §3 formulas against the helpers."""
    L, w, R_eff = 32, 2, 0.6
    R_base = 1.0 - (L / (L + w)) * (1.0 - R_eff)
    assert abs(v11.base_rate(L, w, R_eff) - R_base) < 1e-15
    R_L = 1.0 - ((L + w) / L) * (1.0 - R_base)
    assert abs(v11.terminated_rate(L, w, R_base) - R_L) < 1e-15
    assert abs(R_L - R_eff) < 1e-12


def test_rate_contract_frozen_geometries_s1_s3():
    """The frozen G1-G3 geometries satisfy the rate contract for both frozen
    S1 and S3 winners at 1e-12 (V11-A05 on the actual formal geometry set)."""
    for stratum, winner, rate in (
            ("S1", v11.V10_WINNER_S1, v11.V10_WINNER_S1_RATE),
            ("S3", v11.V10_WINNER_S3, v11.V10_WINNER_S3_RATE)):
        for geometry, params in v11.FROZEN_GEOMETRIES.items():
            contract = v11.rate_contract(params["L"], params["w"], rate, winner)
            assert contract["ok"], (stratum, geometry, contract)
            assert contract["rho"]


def test_rate_contract_rho_harmonic_at_base_rate():
    """The rho produced by the rate contract is the harmonic-exact concentrated
    distribution at R_base (V8-60 / V10 semantics)."""
    L, w, rate = 32, 1, v11.V10_WINNER_S1_RATE
    contract = v11.rate_contract(L, w, rate, v11.V10_WINNER_S1)
    concentrated = v11.concentrated_check_distribution(contract["R_base"],
                                                       v11.V10_WINNER_S1)
    expected = {int(concentrated["dc_lo"]): float(concentrated["w_lo"])}
    if concentrated["w_hi"] > 0.0:
        expected[int(concentrated["dc_hi"])] = float(concentrated["w_hi"])
    assert contract["rho"] == expected
    assert abs(1.0 - sum(contract["rho"].values())) < 1e-12


# --------------------------------------------------------------------------- #
# boundary: no V8/V9/V10-DE production import
# --------------------------------------------------------------------------- #


def test_no_production_import_boundary():
    """Importing the V11 kernel must bind no V8/V9/V10-DE module (V10 shared
    helpers are the sanctioned read-only reuse), and its source must contain
    no forbidden import lines."""
    for value in vars(v11).values():
        if isinstance(value, types.ModuleType) and "nonbinary" in value.__name__:
            assert value.__name__.endswith("nonbinary_v10_common"), value.__name__
    forbidden_import = re.compile(
        r"^\s*(from|import)\s+.*(nonbinary_qspa|nonbinary_v8|nonbinary_v9|"
        r"nonbinary_v10_de|decode_|production|numpy\s*\.\s*fft)", re.MULTILINE)
    with open(V11_MODULE_PATH, encoding="utf-8") as handle:
        source = handle.read()
    assert not forbidden_import.search(source), "forbidden import line"
    assert "nonbinary_qspa" not in source, "qspa token in source"
