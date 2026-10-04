"""Tiny numerical gates for the isolated GF(32) edge-state loop."""
from __future__ import annotations

from pathlib import Path
import time

import numpy as np

from comparison_bench.formal_ir import v35_algorithm_development as v35
from comparison_bench.formal_ir import nbldpc_gf32_edge_state as edge_state
from comparison_bench.formal_ir.nbldpc_gf32_edge_state import (
    capture_reference_state,
    decode_row_layered_edge_state,
    initial_v2c_message,
    rebase_edge_state,
)


ATOL = 1e-12


def _tiny_problem(*, unequal: bool = True):
    """A two-row GF(32) graph with distinct coefficients and row syndromes."""
    h = np.asarray([[1, 2, 0], [0, 3, 5]], dtype=np.uint8)
    syndrome = np.asarray([1, 2], dtype=np.uint8)
    priors = np.full((3, 32), 1e-3 / 31, dtype=np.float64)
    priors[0, 0] = 0.999
    if unequal:
        for row, mode, peak in ((1, 1, 0.72), (2, 2, 0.91)):
            priors[row] = (1.0 - peak) / 31
            priors[row, mode] = peak
    else:
        priors.fill(1.0 / 32.0)
    return h, priors, syndrome, v35.GF2mField.create(32)


def _one_check_converges_in_one_sweep():
    h = np.asarray([[1, 1]], dtype=np.uint8)
    syndrome = np.asarray([1], dtype=np.uint8)
    priors = np.full((2, 32), 1e-8, dtype=np.float64)
    priors[0] = 1e-3 / 31
    priors[0, 0] = 0.999
    priors[1, 0] = 0.6
    priors[1, 1] = 0.4
    return h, priors, syndrome, v35.GF2mField.create(32)


def _assert_state_close(left, right):
    np.testing.assert_allclose(left.beliefs, right.beliefs, atol=ATOL, rtol=0.0)
    assert len(left.check_to_var) == len(right.check_to_var)
    for left_row, right_row in zip(left.check_to_var, right.check_to_var):
        assert len(left_row) == len(right_row)
        for left_edge, right_edge in zip(left_row, right_row):
            np.testing.assert_allclose(
                left_edge, right_edge, atol=ATOL, rtol=0.0
            )


def _clean_prior(priors):
    clean = np.maximum(np.asarray(priors, dtype=np.float64), 1e-15)
    return clean / clean.sum(axis=1, keepdims=True)


def _log_normalize(values):
    values = np.asarray(values, dtype=np.float64)
    return values - np.logaddexp.reduce(values, axis=1, keepdims=True)


def test_g0_zero_state_and_capture_wrapper_match_v35_on_tiny_nonzero_message_case():
    h, priors, syndrome, field = _tiny_problem()
    reference = v35.decode_row_layered_fftqspa(
        h, priors, syndrome, max_iter=4, damping_alpha=1.0, field=field
    )
    capture_calls = []

    def capture_helper(messages, coefficients, row_syndrome, call_field, tables):
        out_msgs = v35._check_update_log_batch(
            messages, coefficients, row_syndrome, call_field, tables
        )
        capture_calls.append((
            tuple(int(value) for value in coefficients),
            int(row_syndrome),
            [message.copy() for message in out_msgs],
        ))
        return out_msgs

    captured_reference, captured = capture_reference_state(
        h,
        priors,
        syndrome,
        max_iter=4,
        damping_alpha=1.0,
        decode_fn=v35.decode_row_layered_fftqspa,
        check_update_impl=capture_helper,
    )
    zero_state = decode_row_layered_edge_state(
        h, priors, syndrome, max_iter=4, damping_alpha=1.0, field=field
    )

    assert reference.iterations >= 1
    assert captured_reference.iterations == reference.iterations
    assert captured_reference.status == reference.status
    assert captured_reference.syndrome_ok is reference.syndrome_ok
    np.testing.assert_array_equal(captured_reference.x_hat, reference.x_hat)
    np.testing.assert_allclose(
        captured_reference.final_beliefs,
        reference.final_beliefs,
        atol=ATOL,
        rtol=0.0,
    )
    own_syndrome = v35.syndrome_of_gf32(h, reference.x_hat, field)
    assert bool(np.array_equal(own_syndrome, syndrome)) is reference.syndrome_ok

    assert zero_state.iterations == reference.iterations
    assert zero_state.iterations_this_call == reference.iterations
    assert zero_state.status == reference.status
    assert zero_state.syndrome_ok is reference.syndrome_ok
    np.testing.assert_array_equal(zero_state.x_hat, reference.x_hat)
    np.testing.assert_allclose(
        zero_state.final_beliefs, reference.final_beliefs, atol=ATOL, rtol=0.0
    )
    np.testing.assert_allclose(
        zero_state.state.beliefs, reference.final_beliefs, atol=ATOL, rtol=0.0
    )
    np.testing.assert_allclose(
        zero_state.state.log_prior,
        np.log(_clean_prior(priors)),
        atol=ATOL,
        rtol=0.0,
    )
    assert captured.completed_sweeps == reference.iterations
    assert captured.stopped_exact is reference.syndrome_ok
    assert len(captured.check_to_var) == h.shape[0] == 2
    assert [len(row) for row in captured.check_to_var] == [2, 2]
    expected_callback_order = [((1, 2), 1), ((3, 5), 2)] * reference.iterations
    assert [(coefficients, row_syn)
            for coefficients, row_syn, _ in capture_calls] == expected_callback_order
    assert len(capture_calls) == reference.iterations * h.shape[0]
    final_iteration_calls = capture_calls[-h.shape[0]:]
    for row, (_coefficients, _row_syn, out_msgs) in enumerate(final_iteration_calls):
        for edge_index, out_msg in enumerate(out_msgs):
            np.testing.assert_allclose(
                captured.check_to_var[row][edge_index],
                out_msg,
                atol=ATOL,
                rtol=0.0,
            )
    # A captured C2V vector must contain check evidence, not the zero initial state.
    assert any(np.ptp(message) > 1.0
               for row in captured.check_to_var for message in row)
    _assert_state_close(captured, zero_state.state)


def test_g1_same_prior_split_resume_matches_continuous_and_counts_cumulative_sweeps():
    h, priors, syndrome, field = _tiny_problem(unequal=False)
    continuous = decode_row_layered_edge_state(
        h, priors, syndrome, max_iter=4, field=field
    )
    first = decode_row_layered_edge_state(
        h, priors, syndrome, max_iter=2, field=field
    )
    resumed = decode_row_layered_edge_state(
        h, priors, syndrome, max_iter=2, state=first.state, field=field
    )

    assert continuous.syndrome_ok is False
    assert first.syndrome_ok is False
    assert resumed.syndrome_ok is False
    assert first.iterations == first.iterations_this_call == 2
    assert resumed.iterations == 4
    assert resumed.iterations_this_call == 2
    assert continuous.iterations == 4
    assert continuous.state.completed_sweeps == resumed.state.completed_sweeps == 4
    assert continuous.state.stopped_exact is resumed.state.stopped_exact is False
    assert resumed.status == continuous.status
    np.testing.assert_array_equal(resumed.x_hat, continuous.x_hat)
    np.testing.assert_allclose(
        resumed.final_beliefs, continuous.final_beliefs, atol=ATOL, rtol=0.0
    )
    _assert_state_close(resumed.state, continuous.state)


def test_g1_exact_stop_is_retained_and_resume_adds_no_sweeps():
    h, priors, syndrome, field = _one_check_converges_in_one_sweep()
    first = decode_row_layered_edge_state(
        h, priors, syndrome, max_iter=4, field=field
    )
    resumed = decode_row_layered_edge_state(
        h, priors, syndrome, max_iter=3, state=first.state, field=field
    )

    assert first.syndrome_ok is resumed.syndrome_ok is True
    assert first.iterations == first.iterations_this_call == 1
    assert resumed.iterations == 1
    assert resumed.iterations_this_call == 0
    assert first.state.completed_sweeps == resumed.state.completed_sweeps == 1
    assert first.state.stopped_exact is resumed.state.stopped_exact is True
    assert resumed.status == first.status == "converged_exact"
    np.testing.assert_array_equal(resumed.x_hat, first.x_hat)
    np.testing.assert_allclose(
        resumed.final_beliefs, first.final_beliefs, atol=ATOL, rtol=0.0
    )
    _assert_state_close(resumed.state, first.state)


def test_g2_rebase_uses_clean_new_prior_preserves_old_c2v_and_copies_each_branch():
    h, priors, syndrome, field = _tiny_problem()
    original = decode_row_layered_edge_state(
        h, priors, syndrome, max_iter=1, field=field
    ).state
    old_beliefs = original.beliefs.copy()
    old_messages = [[message.copy() for message in row]
                    for row in original.check_to_var]

    changed_prior = np.zeros((3, 32), dtype=np.float64)
    changed_prior[1, 3] = 0.2
    changed_prior[2, 8] = 0.1
    clean = _clean_prior(changed_prior)
    branch_a = rebase_edge_state(original, changed_prior)
    branch_b = rebase_edge_state(original, changed_prior)

    expected_beliefs = np.log(clean)
    for row in range(h.shape[0]):
        columns = np.flatnonzero(h[row])
        for edge_index, column in enumerate(columns):
            expected_beliefs[column] += old_messages[row][edge_index]
    np.testing.assert_allclose(
        branch_a.beliefs, expected_beliefs, atol=ATOL, rtol=0.0
    )
    assert branch_a.completed_sweeps == 0
    assert branch_a.stopped_exact is False
    np.testing.assert_allclose(
        branch_a.log_prior, np.log(clean), atol=ATOL, rtol=0.0
    )
    for row in range(h.shape[0]):
        for edge_index, column in enumerate(np.flatnonzero(h[row])):
            np.testing.assert_allclose(
                branch_a.check_to_var[row][edge_index],
                old_messages[row][edge_index],
                atol=ATOL,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                initial_v2c_message(branch_a, row, int(column)),
                expected_beliefs[int(column)] - old_messages[row][edge_index],
                atol=ATOL,
                rtol=0.0,
            )

    assert not np.shares_memory(branch_a.beliefs, original.beliefs)
    assert not np.shares_memory(branch_b.beliefs, original.beliefs)
    assert not np.shares_memory(
        branch_a.check_to_var[0][0], original.check_to_var[0][0]
    )
    assert not np.shares_memory(
        branch_a.check_to_var[0][0], branch_b.check_to_var[0][0]
    )
    branch_a.beliefs[0, 0] += 17.0
    branch_a.check_to_var[0][0][0] += 19.0
    np.testing.assert_array_equal(original.beliefs, old_beliefs)
    for row in range(h.shape[0]):
        for edge_index in range(len(h[row].nonzero()[0])):
            np.testing.assert_array_equal(
                original.check_to_var[row][edge_index], old_messages[row][edge_index]
            )
    _assert_state_close(branch_b, rebase_edge_state(original, changed_prior))

    decoded = decode_row_layered_edge_state(
        h, changed_prior, syndrome, max_iter=1, state=branch_b, field=field
    )
    clean_log_prior = np.log(clean)
    expected_extrinsic = _log_normalize(decoded.final_beliefs - clean_log_prior)
    np.testing.assert_allclose(
        decoded.extrinsic_log_beliefs,
        expected_extrinsic,
        atol=ATOL,
        rtol=0.0,
    )
    reconstructed = _log_normalize(clean_log_prior + decoded.extrinsic_log_beliefs)
    np.testing.assert_allclose(
        reconstructed,
        _log_normalize(decoded.final_beliefs),
        atol=ATOL,
        rtol=0.0,
    )

    # A zero-sweep exact decision after prior rebasing still carries stale
    # messages from the old prior; its provenance must remain unspecified.
    one_check_h = np.asarray([[1, 1]], dtype=np.uint8)
    one_check_syndrome = np.asarray([1], dtype=np.uint8)
    old_prior = np.full((2, 32), 1e-8, dtype=np.float64)
    old_prior[:, 0] = 0.999
    old_check_state = decode_row_layered_edge_state(
        one_check_h, old_prior, one_check_syndrome, max_iter=1, field=field
    ).state
    assert any(np.any(message != 0.0) for message in old_check_state.check_to_var[0])
    new_prior = np.zeros((2, 32), dtype=np.float64)
    new_prior[0, 0] = 1.0
    new_prior[1, 1] = 1.0
    rebased_exact = rebase_edge_state(old_check_state, new_prior)
    warm_exact = decode_row_layered_edge_state(
        one_check_h, new_prior, one_check_syndrome,
        max_iter=3, state=rebased_exact, field=field,
    )
    assert warm_exact.syndrome_ok is True
    assert warm_exact.iterations == warm_exact.state.completed_sweeps == 0
    assert warm_exact.iterations_this_call == 0
    assert warm_exact.belief_provenance == v35.BELIEF_PROVENANCE_WARM_START_UNSPECIFIED
    assert warm_exact.extrinsic_provenance == v35.EXTRINSIC_WARM_START_UNSPECIFIED

    import pytest

    with pytest.raises(ValueError, match="prior changed; call rebase_edge_state"):
        decode_row_layered_edge_state(
            h, changed_prior, syndrome, max_iter=1, state=original, field=field
        )


def test_capture_delegates_raw_zero_prior_and_tracks_cleaned_copy_once():
    h = np.asarray([[1, 1]], dtype=np.uint8)
    syndrome = np.asarray([1], dtype=np.uint8)
    raw_prior = np.zeros((2, 32), dtype=np.float64)
    raw_prior[0, 0] = 1.0
    raw_prior[1, 1] = 1.0
    untouched = raw_prior.copy()
    delegate_calls = []

    def spy_v35(h_matrix, delegated_prior, syndromes, **kwargs):
        delegate_calls.append(delegated_prior)
        return v35.decode_row_layered_fftqspa(
            h_matrix, delegated_prior, syndromes, **kwargs
        )

    raw_result, state = capture_reference_state(
        h, raw_prior, syndrome, max_iter=0, decode_fn=spy_v35
    )

    assert len(delegate_calls) == 1
    assert delegate_calls[0] is raw_prior
    np.testing.assert_array_equal(delegate_calls[0], untouched)
    np.testing.assert_array_equal(raw_prior, untouched)
    expected_clean = edge_state.clean_prior(untouched, n=2, q=32)
    np.testing.assert_array_equal(state.log_prior, np.log(expected_clean))
    np.testing.assert_array_equal(state.beliefs, np.log(expected_clean))
    assert state.completed_sweeps == raw_result.iterations == 0
    assert state.stopped_exact is raw_result.syndrome_ok is True
    assert all(np.count_nonzero(row) == 0 for row in state.check_to_var)


def test_saved_v1_first_frame_raw_prior_capture_and_zero_loop_match_bare_v35():
    """Read-only deterministic implementation regression; never runs the batch."""
    fixture = (Path(__file__).resolve().parents[2]
               / "workspace" / "gf32_edge_state_3a9f426e" / "diagnostics.npz")
    assert fixture.is_file(), f"authorized saved synthetic fixture is missing: {fixture}"
    with np.load(fixture, allow_pickle=False) as saved:
        h = np.asarray(saved["source_H"][0], dtype=np.uint8).copy()
        raw_prior = np.asarray(saved["original_prior"], dtype=np.float64).copy()
        syndrome = np.asarray(saved["pair_syndrome"][0], dtype=np.uint8).copy()
        assert int(saved["source_graph_id"][0]) == int(saved["pair_graph_id"][0])

    assert h.shape == (52, 128)
    assert raw_prior.shape == (128, 32)
    assert syndrome.shape == (52,)
    assert np.any(raw_prior == 0.0)
    untouched_prior = raw_prior.copy()
    delegate_priors = []
    start = time.perf_counter()

    # Three and only three decoder calls: the unchanged raw-prior baseline,
    # one captured v35 reference, and one zero-state edge loop.
    bare_reference = v35.decode_row_layered_fftqspa(
        h, raw_prior, syndrome, max_iter=90, damping_alpha=1.0,
        warm_beliefs=None, field=None,
    )

    def recording_v35(h_matrix, delegated_prior, syndromes, **kwargs):
        delegate_priors.append(delegated_prior)
        return v35.decode_row_layered_fftqspa(
            h_matrix, delegated_prior, syndromes, **kwargs
        )

    captured_reference, captured_state = capture_reference_state(
        h, raw_prior, syndrome, max_iter=90, damping_alpha=1.0,
        decode_fn=recording_v35,
    )
    zero_state = decode_row_layered_edge_state(
        h, raw_prior, syndrome, max_iter=90, damping_alpha=1.0,
    )
    elapsed = time.perf_counter() - start

    assert len(delegate_priors) == 1
    assert delegate_priors[0] is raw_prior
    np.testing.assert_array_equal(delegate_priors[0], untouched_prior)
    np.testing.assert_array_equal(raw_prior, untouched_prior)
    clean_once = edge_state.clean_prior(untouched_prior, n=128, q=32)
    np.testing.assert_array_equal(captured_state.log_prior, np.log(clean_once))
    assert bare_reference.iterations <= 90
    assert captured_reference.iterations == bare_reference.iterations
    assert zero_state.iterations == bare_reference.iterations
    assert captured_state.completed_sweeps == bare_reference.iterations
    assert captured_reference.status == bare_reference.status == zero_state.status
    assert captured_reference.syndrome_ok == bare_reference.syndrome_ok == zero_state.syndrome_ok
    assert captured_state.stopped_exact == bare_reference.syndrome_ok
    np.testing.assert_array_equal(captured_reference.x_hat, bare_reference.x_hat)
    np.testing.assert_array_equal(zero_state.x_hat, bare_reference.x_hat)
    np.testing.assert_array_equal(
        v35.syndrome_of_gf32(h, bare_reference.x_hat), syndrome
    )
    np.testing.assert_allclose(
        captured_reference.final_beliefs, bare_reference.final_beliefs,
        atol=ATOL, rtol=0.0,
    )
    np.testing.assert_allclose(
        zero_state.final_beliefs, bare_reference.final_beliefs,
        atol=ATOL, rtol=0.0,
    )
    np.testing.assert_allclose(
        captured_state.beliefs, bare_reference.final_beliefs,
        atol=ATOL, rtol=0.0,
    )
    assert elapsed < 30.0, f"three-call saved-fixture regression took {elapsed:.3f}s"
