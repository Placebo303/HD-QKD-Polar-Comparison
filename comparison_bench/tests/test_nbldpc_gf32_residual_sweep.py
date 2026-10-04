"""Focused numerical gates for residual-ranked GF(32) row-layered decoding."""
from __future__ import annotations

import numpy as np
import pytest

from comparison_bench.formal_ir import nbldpc_gf32_residual_sweep as residual
from comparison_bench.formal_ir import v35_algorithm_development as v35
from comparison_bench.formal_ir.nonbinary_field import GF2mField


Q = 32
ATOL = 1e-12


def _field() -> GF2mField:
    return GF2mField.create(Q)


def _probabilities(log_values: np.ndarray) -> np.ndarray:
    values = np.asarray(log_values, dtype=np.float64)
    shifted = values - np.max(values, axis=1, keepdims=True)
    exp_values = np.exp(shifted)
    return exp_values / np.sum(exp_values, axis=1, keepdims=True)


def _assert_same_decoder_output(actual, expected) -> None:
    for name in ("syndrome_ok", "iterations", "status", "belief_provenance",
                 "extrinsic_provenance"):
        assert getattr(actual, name) == getattr(expected, name), name
    np.testing.assert_array_equal(actual.x_hat, expected.x_hat)
    np.testing.assert_allclose(
        actual.final_beliefs, expected.final_beliefs, rtol=0.0, atol=ATOL)
    if actual.extrinsic_log_beliefs is None or expected.extrinsic_log_beliefs is None:
        assert actual.extrinsic_log_beliefs is expected.extrinsic_log_beliefs
    else:
        np.testing.assert_allclose(
            actual.extrinsic_log_beliefs, expected.extrinsic_log_beliefs,
            rtol=0.0, atol=ATOL)


def _tree_prior_case(case: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if case == 0:
        # One GF(32) parity check. Exact zeros exercise the shared v35 floor.
        h = np.array([[1, 1]], dtype=np.uint8)
        prior = np.zeros((2, Q), dtype=np.float64)
        prior[0, [0, 2]] = (0.99, 0.01)
        prior[1, [0, 1]] = (0.99, 0.01)
        syndrome = np.array([1], dtype=np.uint8)
    else:
        # A two-check tree with zero-support priors and nonzero target syndrome.
        h = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
        prior = np.zeros((3, Q), dtype=np.float64)
        prior[0, [0, 3]] = (0.8, 0.2)
        prior[1, [0, 2]] = (0.9, 0.1)
        prior[2, [0, 1]] = (0.7, 0.3)
        syndrome = np.array([1, 2], dtype=np.uint8)
    return h, prior, syndrome


def test_e1_single_check_gf32_tiny_tree_matches_exhaustive_posterior():
    h, prior, syndrome = _tree_prior_case(0)
    field = _field()
    result = residual.decode_row_layered_residual_sweep(
        h, prior, syndrome, max_iter=90, schedule="residual",
        damping_alpha=1.0, field=field)

    # A one-check factor graph is a tree: enumerate every pair satisfying the
    # GF(32) check and compare its exact posterior marginals with one BP sweep.
    clean = np.maximum(prior, 1e-15)
    clean /= clean.sum(axis=1, keepdims=True)
    values = np.arange(Q, dtype=np.uint8)
    valid = np.bitwise_xor(values[:, None], values[None, :]) == int(syndrome[0])
    joint = clean[0, :, None] * clean[1, None, :] * valid
    joint /= joint.sum()
    oracle = np.stack((joint.sum(axis=1), joint.sum(axis=0)))

    assert result.status == "converged_exact"
    assert result.syndrome_ok is True
    assert result.iterations == 1
    assert [list(order) for order in result.row_orders] == [[0]]
    np.testing.assert_allclose(
        _probabilities(result.final_beliefs), oracle, rtol=0.0, atol=1e-10)
    assert result.score_check_updates == 1
    assert result.applied_check_updates == 1
    assert result.score_edge_updates == 2
    assert result.applied_edge_updates == 2


@pytest.mark.parametrize("case", [0, 1])
def test_e1_natural_schedule_matches_v35_on_raw_zero_support_priors(case):
    h, prior, syndrome = _tree_prior_case(case)
    field = _field()
    reference = v35.decode_row_layered_fftqspa(
        h, prior, syndrome, max_iter=5, damping_alpha=1.0,
        warm_beliefs=None, field=field)
    natural = residual.decode_row_layered_residual_sweep(
        h, prior, syndrome, max_iter=5, schedule="natural",
        damping_alpha=1.0, field=field)

    _assert_same_decoder_output(natural, reference)
    assert len(natural.row_orders) == natural.iterations
    assert all(list(order) == list(range(h.shape[0])) for order in natural.row_orders)
    assert natural.score_check_updates == natural.score_edge_updates == 0
    assert natural.applied_check_updates == natural.iterations * h.shape[0]
    assert natural.applied_edge_updates == natural.iterations * int(np.count_nonzero(h))


def test_e1_prior_only_is_zero_work_for_both_schedules():
    h = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
    prior = np.zeros((3, Q), dtype=np.float64)
    prior[:, 0] = 1.0
    syndrome = np.zeros(2, dtype=np.uint8)
    field = _field()
    calls: list[int] = []

    def spy(*args):
        calls.append(1)
        return v35._check_update_log_batch(*args)

    reference = v35.decode_row_layered_fftqspa(
        h, prior, syndrome, max_iter=90, damping_alpha=1.0,
        warm_beliefs=None, field=field)
    for schedule in ("natural", "residual"):
        result = residual.decode_row_layered_residual_sweep(
            h, prior, syndrome, max_iter=90, schedule=schedule,
            damping_alpha=1.0, field=field, check_update_fn=spy)
        _assert_same_decoder_output(result, reference)
        assert result.iterations == 0
        assert result.status == "converged_exact"
        assert result.belief_provenance == v35.BELIEF_PROVENANCE_PRIOR_ONLY
        assert result.extrinsic_provenance == v35.EXTRINSIC_NO_CHECK_EVIDENCE
        np.testing.assert_array_equal(result.extrinsic_log_beliefs, np.zeros((3, Q)))
        assert len(result.row_orders) == 0
        assert result.score_check_updates == result.applied_check_updates == 0
        assert result.score_edge_updates == result.applied_edge_updates == 0
    assert calls == []


def test_e2_exact_residual_ties_choose_row_order_and_rescore_each_sweep():
    h = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
    prior = np.full((3, Q), 1.0 / Q, dtype=np.float64)
    syndrome = np.array([1, 2], dtype=np.uint8)
    field = _field()
    calls: list[tuple[int, list[np.ndarray]]] = []

    def spy(in_messages, coefficients, row_syndrome, local_field, tables):
        calls.append((int(row_syndrome), [np.asarray(msg).copy() for msg in in_messages]))
        return v35._check_update_log_batch(
            in_messages, coefficients, row_syndrome, local_field, tables)

    result = residual.decode_row_layered_residual_sweep(
        h, prior, syndrome, max_iter=2, schedule="residual",
        damping_alpha=1.0, field=field, check_update_fn=spy)

    assert result.iterations == 2
    assert len(result.row_orders) == 2
    assert [list(order) for order in result.row_orders] == [[0, 1], [0, 1]]
    np.testing.assert_array_equal(result.first_sweep_residuals, np.zeros(2))
    assert [row_syndrome for row_syndrome, _ in calls] == [1, 2] * 4
    assert result.score_check_updates == 4
    assert result.applied_check_updates == 4
    assert result.score_edge_updates == 8
    assert result.applied_edge_updates == 8


def test_e2_sub_picounit_unequal_scores_keep_raw_order_and_recompute_commit():
    h = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
    prior = np.full((3, Q), 1.0 / Q, dtype=np.float64)
    prior[0, 0] += 1e-13
    prior[1, 0] += 1.5e-13
    prior[2, 0] += 2e-13
    prior /= prior.sum(axis=1, keepdims=True)
    syndrome = np.array([1, 2], dtype=np.uint8)
    field = _field()
    calls: list[tuple[int, list[np.ndarray]]] = []

    def spy(in_messages, coefficients, row_syndrome, local_field, tables):
        calls.append((int(row_syndrome), [np.asarray(msg).copy() for msg in in_messages]))
        return v35._check_update_log_batch(
            in_messages, coefficients, row_syndrome, local_field, tables)

    result = residual.decode_row_layered_residual_sweep(
        h, prior, syndrome, max_iter=1, schedule="residual",
        damping_alpha=1.0, field=field, check_update_fn=spy)

    scores = np.asarray(result.first_sweep_residuals, dtype=np.float64)
    assert scores.shape == (2,)
    assert scores[1] > scores[0]
    assert 0.0 < scores[1] - scores[0] < 1e-12
    assert [list(order) for order in result.row_orders] == [[1, 0]]
    # The first two calls score an immutable row-ascending snapshot; the next
    # calls apply in ranked order. Row 0 is recomputed after row 1 changed its
    # shared variable, rather than committing its stale scoring message.
    assert [row_syndrome for row_syndrome, _ in calls] == [1, 2, 2, 1]
    np.testing.assert_array_equal(calls[1][1][0], calls[2][1][0])
    assert not np.array_equal(calls[0][1][1], calls[3][1][1])
    assert result.score_check_updates == result.applied_check_updates == 2
    assert result.score_edge_updates == result.applied_edge_updates == 4
