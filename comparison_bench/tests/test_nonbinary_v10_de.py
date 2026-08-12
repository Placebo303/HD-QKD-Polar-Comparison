"""V10 DE/rand/1/bin kernel tests (additive; V10-10 scope, T0/T1).

Covers the own WHT kernel, MC-DE determinism and q=4 agreement with the V8
direct MC-DE (test-only import), the K=8 decode/quantization, deterministic
bias-free population init, the 6-tier lexicographic objective ordering, the
fail-closed penalties (NaN/Inf -> 1e12, structural -> 1e6+), checkpoint/resume
equivalence and no-overwrite, the max_evaluations cap, threshold binary search
determinism, and whole-search determinism.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v10_de as de
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v10_common as common
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v8_mcde as v8


def _rho_from_concentrated(conc: dict) -> dict[int, float]:
    return {int(conc["dc_lo"]): conc["w_lo"]} if conc["w_hi"] <= 0.0 else {
        int(conc["dc_lo"]): conc["w_lo"], int(conc["dc_hi"]): conc["w_hi"]}


def _q4_config():
    lam = {2: 0.5, 3: 0.5}
    rho = _rho_from_concentrated(common.concentrated_check_distribution(0.5, lam))
    return lam, rho


def _valid_8_lambda():
    return {2: 0.2, 3: 0.3, 5: 0.15, 8: 0.1, 12: 0.1, 20: 0.05, 30: 0.05, 40: 0.05}


# --------------------------------------------------------------------------- #
# small pure-numpy references for the njit kernels (AMEND-2026-08-05-01)
# --------------------------------------------------------------------------- #


def _numpy_wht_reference(block: np.ndarray) -> np.ndarray:
    """In-test pure-numpy XOR-order WHT (row loops, no reshape tricks)."""
    out = block.copy()
    n, q = out.shape
    width = 1
    while width < q:
        for i in range(n):
            row = out[i]
            for j in range(0, q, 2 * width):
                for k in range(j, j + width):
                    a, b = row[k], row[k + width]
                    row[k] = a + b
                    row[k + width] = a - b
        width *= 2
    return out


def _numpy_check_conv_reference(v2c: np.ndarray, idx: np.ndarray,
                                draws: np.ndarray, q_floor: float = 1e-300) -> np.ndarray:
    """In-test numpy check-node convolution mirroring the original V10 numpy
    semantics: gather pre-drawn rows, WHT, multiply with the per-sample degree
    mask, inverse WHT / q, 1e-300 floor, row-normalize."""
    n, q = v2c.shape
    acc = np.ones((n, q))  # spectrum of delta at 0 = all ones
    for d in range(idx.shape[0]):
        incoming = v2c[idx[d]]
        acc = np.where((draws > d)[:, None], acc * _numpy_wht_reference(incoming), acc)
    conv = _numpy_wht_reference(acc) / q
    floored = np.maximum(conv, q_floor)
    return floored / floored.sum(axis=1, keepdims=True)


# --------------------------------------------------------------------------- #
# T0: WHT kernel
# --------------------------------------------------------------------------- #


def test_fwht_batched_hand_computed_q4():
    vector = np.array([1.0, 2.0, 3.0, 4.0])
    out = de.fwht_batched(vector)
    assert np.allclose(out, [10.0, -2.0, -4.0, 0.0], atol=1e-12)
    assert np.allclose(de.fwht_batched(out) / 4.0, vector, atol=1e-12)
    with pytest.raises(ValueError):
        de.fwht_batched(np.array([1.0, 2.0, 3.0]))
    with pytest.raises(ValueError):
        de.fwht_batched(np.array([1.0, np.nan, 2.0, 3.0]))


def test_fwht_batched_vectorized_over_leading_axes():
    rng = np.random.default_rng(2026100211)
    batch = np.stack([rng.random(8) for _ in range(5)])
    for row in range(5):
        assert np.allclose(de.fwht_batched(batch)[row],
                           de.fwht_batched(batch[row]), atol=1e-12)


# --------------------------------------------------------------------------- #
# T0/T1: MC-DE determinism + q=4 agreement with the V8 direct oracle
# --------------------------------------------------------------------------- #


def test_run_mcde_determinism():
    lam, rho = _q4_config()
    first = de.run_mcde(4, lam, rho, 0.1, n_samples=300, max_iter=40, seed=2026100211)
    second = de.run_mcde(4, lam, rho, 0.1, n_samples=300, max_iter=40, seed=2026100211)
    assert first["entropy_trace"] == second["entropy_trace"]
    assert first["error_trace"] == second["error_trace"]
    assert first["iterations"] == second["iterations"]
    assert first["converged"] == second["converged"]
    third = de.run_mcde(4, lam, rho, 0.1, n_samples=300, max_iter=40, seed=2026100212)
    assert third["entropy_trace"] != first["entropy_trace"]


def test_run_mcde_q4_agrees_with_v8_oracle():
    """V10's own MC-DE is numerically consistent with the accepted V8 direct
    MC-DE (test-only import): same convergence, same iteration count, and
    close entropy/error traces at q=4."""
    lam, rho = _q4_config()
    own = de.run_mcde(4, lam, rho, 0.1, n_samples=300, max_iter=40, seed=2026100213)
    oracle = v8.run_mcde(4, lam, rho, 0.1, n_samples=300, max_iter=40, seed=2026100213)
    assert own["converged"] == oracle["converged"]
    assert own["iterations"] == oracle["iterations"]
    assert len(own["entropy_trace"]) == len(oracle["entropy_trace"])
    assert np.allclose(own["entropy_trace"], oracle["entropy_trace"], atol=1e-9)
    assert np.allclose(own["error_trace"], oracle["error_trace"], atol=1e-9)


def test_run_mcde_q1024_bounded_deterministic():
    lam = {3: 1.0}
    rho = _rho_from_concentrated(common.concentrated_check_distribution(0.5, lam))
    first = de.run_mcde(1024, lam, rho, 0.05, n_samples=100, max_iter=5, seed=2026100211)
    second = de.run_mcde(1024, lam, rho, 0.05, n_samples=100, max_iter=5, seed=2026100211)
    assert first["entropy_trace"] == second["entropy_trace"]
    assert len(first["entropy_trace"]) == 5


def test_run_mcde_fail_closed():
    lam, rho = _q4_config()
    with pytest.raises(ValueError):
        de.run_mcde(4, lam, rho, 0.0, n_samples=300, max_iter=40, seed=1)
    with pytest.raises(ValueError):
        de.run_mcde(4, lam, rho, 0.1, n_samples=99, max_iter=40, seed=1)
    with pytest.raises(ValueError):
        de.run_mcde(3, lam, rho, 0.1, n_samples=300, max_iter=40, seed=1)
    with pytest.raises(ValueError):
        de.run_mcde(2048, lam, rho, 0.1, n_samples=300, max_iter=40, seed=1)
    with pytest.raises(ValueError):
        de.run_mcde(4, {}, rho, 0.1, n_samples=300, max_iter=40, seed=1)
    with pytest.raises(ValueError):
        de.run_mcde(4, {2: math.nan}, rho, 0.1, n_samples=300, max_iter=40, seed=1)


def test_threshold_binary_search_deterministic():
    lam, rho = _q4_config()
    result = de.threshold_binary_search(4, lam, rho, n_samples=300, max_iter=40,
                                        seed=2026100211, p_lo=0.01, p_hi=0.49, p_tol=0.01)
    again = de.threshold_binary_search(4, lam, rho, n_samples=300, max_iter=40,
                                       seed=2026100211, p_lo=0.01, p_hi=0.49, p_tol=0.01)
    assert result["threshold_proxy"] == again["threshold_proxy"]
    assert result["probes"] == again["probes"]
    assert abs(result["probes"][0]["p"] - 0.25) < 1e-12


# --------------------------------------------------------------------------- #
# K=8 representation
# --------------------------------------------------------------------------- #


def test_quantize_degree_slots():
    slots = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
    assert list(de.quantize_degree_slots(slots)) == [2, 3, 4, 5, 6, 7, 8, 9]
    assert list(de.quantize_degree_slots(np.full(8, -100.0))) == [2] * 8
    assert list(de.quantize_degree_slots(np.full(8, 100.0))) == [40] * 8
    with pytest.raises(ValueError):
        de.quantize_degree_slots(np.zeros(7))


def test_decode_vector_softmax_and_quantization():
    x = np.zeros(16)
    x[:8] = np.arange(8)  # degrees 2..9
    lam = de.decode_vector(x)
    assert sorted(lam) == [2, 3, 4, 5, 6, 7, 8, 9]
    assert abs(sum(lam.values()) - 1.0) < 1e-12
    assert all(weight == 0.125 for weight in lam.values())
    # logits pass through: a large logit dominates its degree.
    x2 = x.copy()
    x2[8] = 10.0
    lam2 = de.decode_vector(x2)
    assert lam2[2] > 0.999
    with pytest.raises(ValueError):
        de.decode_vector(np.zeros(15))
    with pytest.raises(ValueError):
        de.decode_vector(np.full(16, np.nan))


def test_init_population_deterministic_and_bias_free():
    first = de.init_population(5, 2026100201)
    second = de.init_population(5, 2026100201)
    assert np.array_equal(first, second)
    third = de.init_population(5, 2026100202)
    assert not np.array_equal(first, third)
    for row in first:
        degrees = np.sort(de.quantize_degree_slots(row[:8]))
        assert len(set(degrees)) == 8
        assert 2 <= degrees.min() and degrees.max() <= 40
        assert np.all(np.isfinite(row))


def test_de_mutation_determinism():
    population = de.init_population(6, 2026100201)
    from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v10_de import (
        _mutation_rng, _draw_distinct, _binomial_crossover)
    f, cr = 0.5, 0.9
    results = []
    for _ in range(2):
        rng = _mutation_rng(2026100201, 1, 2)
        r1, r2, r3 = _draw_distinct(rng, 6, 2)
        mutant = population[r1] + f * (population[r2] - population[r3])
        trial = _binomial_crossover(rng, mutant, population[2], cr)
        results.append((r1, r2, r3, tuple(mutant), tuple(trial)))
    assert results[0] == results[1]
    r1, r2, r3, _, _ = results[0]
    assert r1 != r2 and r2 != r3 and r1 != r3
    assert 2 not in (r1, r2, r3)


# --------------------------------------------------------------------------- #
# 6-tier objective ordering
# --------------------------------------------------------------------------- #


def _record(converged, iterations, entropy, error, threshold, canonical, penalty=0.0):
    return de.ObjectiveRecord(
        entropy_converged=converged, converged_iter=iterations,
        final_entropy=entropy, error_prob=error,
        threshold_proxy=threshold, canonical_tuple=canonical, penalty=penalty)


def test_objective_6tier_ordering():
    # tier1: eligible beats ineligible regardless of the other components.
    assert de.objective_compare(
        _record(True, 30, 0.05, 0.1, None, (2, 3)),
        _record(False, 10, 0.001, 0.0, None, (2, 3))) == -1
    # tier2: fewer converged iterations.
    assert de.objective_compare(
        _record(True, 20, 0.05, 0.1, None, (2, 3)),
        _record(True, 21, 0.05, 0.1, None, (2, 3))) == -1
    # tier3: lower final entropy.
    assert de.objective_compare(
        _record(True, 20, 0.02, 0.1, None, (2, 3)),
        _record(True, 20, 0.05, 0.1, None, (2, 3))) == -1
    # tier4: lower error probability.
    assert de.objective_compare(
        _record(True, 20, 0.02, 0.05, None, (2, 3)),
        _record(True, 20, 0.02, 0.10, None, (2, 3))) == -1
    # tier5: higher threshold proxy (only when both present).
    assert de.objective_compare(
        _record(True, 20, 0.02, 0.05, 0.31, (2, 3)),
        _record(True, 20, 0.02, 0.05, 0.29, (2, 3))) == -1
    # both None -> skip tier5.
    assert de.objective_compare(
        _record(True, 20, 0.02, 0.05, None, (2, 3)),
        _record(True, 20, 0.02, 0.05, None, (2, 3))) == 0
    # tier6: canonical tuple ascending lexicographic.
    assert de.objective_compare(
        _record(True, 20, 0.02, 0.05, 0.30, (2, 3)),
        _record(True, 20, 0.02, 0.05, 0.30, (2, 4))) == -1
    # exact tie -> equal (incumbent retained).
    assert de.objective_compare(
        _record(True, 20, 0.02, 0.05, 0.30, (2, 3)),
        _record(True, 20, 0.02, 0.05, 0.30, (2, 3))) == 0


def test_penalty_ordering_and_fail_closed():
    penalized = _record(False, 10 ** 9, 1e18, 1e18, None, (2, 3), penalty=1e6)
    valid_ineligible = _record(False, 10 ** 9, 1e18, 1e18, None, (2, 3), penalty=0.0)
    assert de.objective_compare(valid_ineligible, penalized) == -1
    nan_inf = _record(False, 10 ** 9, 1e18, 1e18, None, (), penalty=1e12)
    assert de.objective_compare(nan_inf, penalized) == 1
    # NaN/Inf raw vector -> 1e12 penalty.
    record = de.evaluate_vector(np.full(16, np.nan), 4, 0.5, 0.1,
                                seed=2026100211, n_samples=100, max_iter=10)
    assert record.penalty == de.PENALTY_NAN_INF
    # duplicate degrees after quantization -> structural penalty >= 1e6.
    vector = np.zeros(16)
    vector[:8] = 0.0  # all eight slots quantize to degree 2 -> duplicates
    record = de.evaluate_vector(vector, 4, 0.5, 0.1, seed=2026100211,
                                n_samples=100, max_iter=10)
    assert record.penalty >= de.PENALTY_STRUCTURAL_BASE
    assert record.penalty < de.PENALTY_NAN_INF
    # a valid candidate evaluates cleanly.
    lam = _valid_8_lambda()
    record = de.evaluate_candidate(lam, 4, 0.5, 0.1, seed=2026100211,
                                   n_samples=100, max_iter=10)
    assert record.penalty == 0.0


def test_objective_record_json_roundtrip():
    record = _record(True, 20, 0.02, 0.05, 0.30, (2, 3, 0.5))
    restored = de.record_from_dict(de.record_to_dict(record))
    assert restored == record


# --------------------------------------------------------------------------- #
# checkpoint / resume / no-overwrite / max_evaluations
# --------------------------------------------------------------------------- #


def test_checkpoint_resume_equivalence(tmp_path):
    budget = dict(q=4, p_gate=0.1, rate=0.5, search_seed=2026100201,
                  pop_size=4, max_gen=3, f=0.5, cr=0.9,
                  n_samples=100, max_iter=20)
    full_dir = os.path.join(str(tmp_path), "full")
    full = de.run_de_search(out_dir=full_dir, **budget)
    interrupted_dir = os.path.join(str(tmp_path), "interrupted")
    de.run_de_search(out_dir=interrupted_dir, **budget)
    # simulate a crash after generation 2: drop the completion marker and the
    # last checkpoint, then resume with the identical frozen parameters.
    os.remove(os.path.join(interrupted_dir, "run_complete.json"))
    os.remove(os.path.join(interrupted_dir, "checkpoint_gen_0003.json"))
    resumed = de.run_de_search(out_dir=interrupted_dir, resume=True, **budget)
    assert resumed["best_lambda"] == full["best_lambda"]
    assert resumed["evaluations"] == full["evaluations"]
    assert resumed["generations_completed"] == full["generations_completed"]
    assert resumed["best_objective"] == full["best_objective"]
    assert resumed["eligible_candidates"] == full["eligible_candidates"]
    assert [entry["threshold_proxy"] for entry in resumed["eligible_candidates"]] \
        == [entry["threshold_proxy"] for entry in full["eligible_candidates"]]
    assert os.path.exists(os.path.join(interrupted_dir, "checkpoint_gen_0003.json"))


def test_no_overwrite_completed_run(tmp_path):
    budget = dict(q=4, p_gate=0.1, rate=0.5, search_seed=2026100202,
                  pop_size=4, max_gen=1, f=0.5, cr=0.9,
                  n_samples=100, max_iter=15)
    out_dir = os.path.join(str(tmp_path), "done")
    de.run_de_search(out_dir=out_dir, **budget)
    assert os.path.exists(os.path.join(out_dir, "run_complete.json"))
    with pytest.raises(ValueError):
        de.run_de_search(out_dir=out_dir, **budget)


def test_resume_without_checkpoint_raises(tmp_path):
    with pytest.raises(ValueError):
        de.run_de_search(resume=True, out_dir=os.path.join(str(tmp_path), "empty"),
                         q=4, p_gate=0.1, rate=0.5, search_seed=2026100203,
                         pop_size=4, max_gen=1, f=0.5, cr=0.9,
                         n_samples=100, max_iter=15)


def test_max_evaluations_hard_cap(tmp_path):
    budget = dict(q=4, p_gate=0.1, rate=0.5, search_seed=2026100204,
                  pop_size=4, max_gen=20, f=0.5, cr=0.9,
                  n_samples=100, max_iter=15, max_evaluations=6)
    out_dir = os.path.join(str(tmp_path), "cap")
    result = de.run_de_search(out_dir=out_dir, **budget)
    assert result["evaluations"] == 6
    assert result["stop_reason"] == "max_evaluations_reached"
    assert result["generations_completed"] < 20
    with open(os.path.join(out_dir, "run_complete.json"), encoding="utf-8") as handle:
        final = json.load(handle)
    assert final["stop_reason"] == "max_evaluations_reached"


def test_run_de_search_determinism():
    budget = dict(q=4, p_gate=0.1, rate=0.5, search_seed=2026100201,
                  pop_size=4, max_gen=2, f=0.5, cr=0.9,
                  n_samples=100, max_iter=20)
    first = de.run_de_search(**budget)
    second = de.run_de_search(**budget)
    assert first["best_lambda"] == second["best_lambda"]
    assert first["best_objective"] == second["best_objective"]
    assert first["eligible_candidates"] == second["eligible_candidates"]
    assert first["evaluations"] == second["evaluations"]


def test_search_produces_eligible_candidates_and_transcript(tmp_path):
    budget = dict(q=4, p_gate=0.05, rate=0.5, search_seed=2026100205,
                  pop_size=4, max_gen=2, f=0.5, cr=0.9,
                  n_samples=100, max_iter=40)
    out_dir = os.path.join(str(tmp_path), "eligible")
    result = de.run_de_search(out_dir=out_dir, **budget)
    checkpoint = os.path.join(out_dir, "checkpoint_gen_0002.json")
    assert os.path.exists(checkpoint)
    with open(checkpoint, encoding="utf-8") as handle:
        state = json.load(handle)
    assert state["schema"] == "v10_de_checkpoint_v1"
    assert len(state["population"]) == 4
    assert len(state["objectives"]) == 4
    assert len(state["transcript"]) == 2
    # at least one generation transcript recorded per-generation trials
    for generation_entry in state["transcript"]:
        assert len(generation_entry["trials"]) == 4


# --------------------------------------------------------------------------- #
# numba njit kernels (AMEND-2026-08-05-01): known answer + numpy references
# --------------------------------------------------------------------------- #


def test_numba_wht_known_answer():
    """Delta (unit impulse) input -> all-ones output (known answer that
    catches the half-block butterfly bug: a butterfly touching only half the
    pairs leaves the output non-constant)."""
    for q in (4, 8, 1024):
        delta = np.zeros(q)
        delta[0] = 1.0
        out = de.fwht_batched(delta)
        assert np.array_equal(out, np.ones(q)), (q, out[:8])
        # half-block regression: delta at q/2 -> alternating +/-1 pattern.
        delta_mid = np.zeros(q)
        delta_mid[q // 2] = 1.0
        out_mid = de.fwht_batched(delta_mid)
        expect = np.where((np.arange(q) & (q // 2)) != 0, -1.0, 1.0)
        assert np.array_equal(out_mid, expect), (q, out_mid[:8], expect[:8])
    # batch form exercises the same njit kernel entry point.
    batch = np.zeros((3, 8))
    batch[:, 0] = 1.0
    assert np.array_equal(de.fwht_batched(batch), np.ones((3, 8)))
    # direct kernel-level check (the compiled butterfly itself).
    assert np.array_equal(de._wht_rows_jit(batch), np.ones((3, 8)))


def test_numba_wht_matches_numpy_reference():
    """njit WHT vs the in-test pure-numpy reference: allclose(rtol=1e-12)."""
    rng = np.random.default_rng(2026100211)
    for q in (4, 8, 16, 1024):
        block = rng.random((5, q))
        ref = _numpy_wht_reference(block)
        jit = de._wht_rows_jit(block)
        assert np.allclose(jit, ref, rtol=1e-12, atol=0.0), (q, np.max(np.abs(jit - ref)))
        assert np.max(np.abs(jit - ref)) < 1e-15
        # public entry point agrees too.
        assert np.allclose(de.fwht_batched(block), ref, rtol=1e-12, atol=0.0)


def test_numba_check_conv_matches_numpy():
    """njit check convolution vs the in-test numpy reference (incl. the
    per-sample degree mask path): allclose(rtol=1e-12)."""
    rng = np.random.default_rng(2026100212)
    raw = rng.random((100, 16))
    v2c = raw / raw.sum(axis=1, keepdims=True)
    n_rows = v2c.shape[0]
    cases = [
        rng.integers(1, 4, size=n_rows),        # mixed mask
        np.full(n_rows, 3, dtype=np.int64),     # full mask
        np.full(n_rows, 1, dtype=np.int64),     # degree-2 all draw
        np.zeros(n_rows, dtype=np.int64),       # no draw slots at all
    ]
    for draws in cases:
        idx = rng.integers(0, v2c.shape[0],
                           size=(int(draws.max()), v2c.shape[0]))
        ref = _numpy_check_conv_reference(v2c, idx, draws)
        jit = de._check_conv_jit(v2c, idx, draws)
        assert np.allclose(jit, ref, rtol=1e-12, atol=0.0), np.max(np.abs(jit - ref))
    # q=1024 with high-degree mask path.
    raw2 = rng.random((50, 1024))
    v2c2 = raw2 / raw2.sum(axis=1, keepdims=True)
    draws2 = rng.integers(1, 6, size=50)
    idx2 = rng.integers(0, 50, size=(int(draws2.max()), 50))
    ref2 = _numpy_check_conv_reference(v2c2, idx2, draws2)
    jit2 = de._check_conv_jit(v2c2, idx2, draws2)
    assert np.allclose(jit2, ref2, rtol=1e-12, atol=0.0), np.max(np.abs(jit2 - ref2))


def test_mcde_determinism_after_numba():
    """Same seed -> byte-identical run_mcde results (incl. the transcript
    traces) with the njit kernels in the hot loop; different seed differs."""
    lam, rho = _q4_config()
    first = de.run_mcde(4, lam, rho, 0.1, n_samples=300, max_iter=40, seed=2026100211)
    second = de.run_mcde(4, lam, rho, 0.1, n_samples=300, max_iter=40, seed=2026100211)
    assert first == second
    assert first["entropy_trace"] == second["entropy_trace"]
    assert first["error_trace"] == second["error_trace"]
    third = de.run_mcde(4, lam, rho, 0.1, n_samples=300, max_iter=40, seed=2026100212)
    assert third["entropy_trace"] != first["entropy_trace"]
    # q=1024 path through the same njit kernels is deterministic too.
    lam1024 = {3: 1.0}
    rho1024 = _rho_from_concentrated(common.concentrated_check_distribution(0.5, lam1024))
    a = de.run_mcde(1024, lam1024, rho1024, 0.05, n_samples=100, max_iter=5, seed=2026100211)
    b = de.run_mcde(1024, lam1024, rho1024, 0.05, n_samples=100, max_iter=5, seed=2026100211)
    assert a == b
