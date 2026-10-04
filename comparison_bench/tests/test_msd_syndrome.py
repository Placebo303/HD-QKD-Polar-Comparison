"""Fixed fake-decoder tests for the MSD syndrome sender/receiver boundary."""

from __future__ import annotations

import inspect
import sys
from types import ModuleType

import numpy as np
import pytest
from scipy import sparse

from comparison_bench.src.comparison_bench.formal_ir import msd_conditional_prior as prior
from comparison_bench.src.comparison_bench.formal_ir import msd_syndrome as msd


def _model(encoding: str = "NATURAL", order: str = "LSB_FIRST"):
    return prior.build_conditional_prior_model(
        np.ones((4, 4), dtype=np.float64), encoding=encoding, order=order
    )


def _dependent_counts(encoding: str, order: str) -> np.ndarray:
    counts = np.zeros((4, 4), dtype=np.float64)
    order_bits = (0, 1) if order == "LSB_FIRST" else (1, 0)
    for natural_alice in range(4):
        label = (
            natural_alice ^ (natural_alice >> 1)
            if encoding == "GRAY"
            else natural_alice
        )
        first = (label >> order_bits[0]) & 1
        second = (label >> order_bits[1]) & 1
        if first == 0:
            weight = 9.0 if second == 0 else 1.0
        else:
            weight = 2.0 if second == 0 else 8.0
        counts[natural_alice, 0] = weight
    return counts


def _conditioned_q8_model():
    counts = np.zeros((8, 8), dtype=np.float64)
    counts[0, 0] = 1.0  # exact p_one=0
    counts[0, 1] = counts[1, 1] = 1.0  # ambiguous p_one=0.5
    counts[1, 2] = 1.0  # exact p_one=1
    counts[0, 3] = 1.0
    counts[1, 3] = 1e-12  # tiny, but strictly positive p_error
    # Bob symbol 4 has no support and must retain its uninformative p_error=0.5.
    return prior.build_conditional_prior_model(
        counts, encoding="NATURAL", order="LSB_FIRST"
    )


def _conditioned_csr_with_stored_zero() -> sparse.csr_matrix:
    # Row 0 contains an explicit stored zero in active column 1. Conditioning
    # must eliminate it on a copy before classifying zero rows.
    return sparse.csr_matrix(
        (
            np.array([1, 0, 1, 1, 1, 1, 1], dtype=np.uint8),
            np.array([0, 1, 1, 3, 2, 3, 4], dtype=np.int32),
            np.array([0, 2, 4, 5, 6, 7, 7], dtype=np.int32),
        ),
        shape=(6, 5),
    )


def _fake_factory(outputs, factory_calls, decode_inputs):
    def factory(*, parity_check_matrix, error_channel):
        stage = len(factory_calls)
        factory_calls.append(
            {
                "parity_check_matrix": parity_check_matrix,
                "error_channel": np.asarray(error_channel).copy(),
            }
        )

        class FakeDecoder:
            def decode(self, delta):
                decode_inputs.append(np.asarray(delta).copy())
                return outputs[stage]

        return FakeDecoder()

    return factory


def test_sender_counts_dependent_and_zero_rows_as_transmitted_bits() -> None:
    model = _model()
    alice = np.array([0, 1, 2, 3], dtype=np.uint8)
    matrices = (
        sparse.csr_matrix(
            [[1, 1, 0, 0], [1, 1, 0, 0], [0, 0, 0, 0]], dtype=np.uint8
        ),
        sparse.csr_matrix(
            [[0, 0, 1, 0], [0, 0, 1, 0], [0, 0, 0, 0]], dtype=np.uint8
        ),
    )

    disclosure = msd.disclose_syndromes(alice, model, matrices)

    assert len(disclosure.public_syndromes) == 2
    assert np.array_equal(disclosure.public_syndromes[0], [1, 1, 0])
    assert np.array_equal(disclosure.public_syndromes[1], [1, 1, 0])
    assert disclosure.transmitted_row_count_bits_per_block == 6


def test_receiver_corrects_nonzero_error_delta_with_fake_factory() -> None:
    model = prior.build_conditional_prior_model(
        np.ones((2, 2)), encoding="NATURAL", order="LSB_FIRST"
    )
    alice = np.array([1, 0, 1], dtype=np.uint8)
    bob = np.array([0, 0, 0], dtype=np.uint8)
    matrix = sparse.identity(3, format="csr", dtype=np.uint8)
    disclosure = msd.disclose_syndromes(alice, model, (matrix,))
    calls, deltas = [], []
    factory = _fake_factory([alice.copy()], calls, deltas)

    result = msd.receive_syndromes(
        model, bob, (matrix,), disclosure.public_syndromes, factory
    )

    assert np.array_equal(deltas[0], alice)
    assert np.array_equal(result.recovered_stage_bits[0], alice)
    assert np.array_equal(result.reconstructed_natural_symbols, alice)
    assert result.attempted_stage_syndrome_passed == (True,)
    assert calls[0]["error_channel"] == pytest.approx([0.5, 0.5, 0.5])
    assert result.transmitted_row_count_bits_per_block == 3


@pytest.mark.parametrize("encoding", ["NATURAL", "GRAY"])
@pytest.mark.parametrize("order", ["LSB_FIRST", "MSB_FIRST"])
def test_roundtrip_uses_recovered_prefix_not_alice_truth(encoding, order) -> None:
    model = prior.build_conditional_prior_model(
        _dependent_counts(encoding, order), encoding=encoding, order=order
    )
    alice = np.array([0, 0], dtype=np.uint8)
    bob = np.array([0, 0], dtype=np.uint8)
    matrices = (
        sparse.csr_matrix([[1, 1]], dtype=np.uint8),
        sparse.csr_matrix([[1, 1]], dtype=np.uint8),
    )
    disclosure = msd.disclose_syndromes(alice, model, matrices)
    calls, deltas = [], []
    factory = _fake_factory(
        [np.array([1, 1], dtype=np.uint8), np.array([0, 0], dtype=np.uint8)],
        calls,
        deltas,
    )

    result = msd.receive_syndromes(
        model, bob, matrices, disclosure.public_syndromes, factory
    )

    assert result.attempted_stage_syndrome_passed == (True, True)
    assert np.array_equal(result.recovered_stage_bits[0], [1, 1])
    assert calls[0]["error_channel"] == pytest.approx([0.5, 0.5])
    # The actual recovered first plane is 1, for which the next-stage p_error is 0.2.
    # Alice's fixture plane is 0 and would instead yield p_error 0.1.
    assert calls[1]["error_channel"] == pytest.approx([0.2, 0.2])
    assert np.array_equal(deltas[0], [0])
    assert np.array_equal(deltas[1], [0])
    # The recovered stage-0 bit sets the next MAP base to 1; the fake decoder
    # returns zero error, so both actual recovered planes are 1.
    expected = 3 if encoding == "NATURAL" else 2
    assert np.array_equal(result.reconstructed_natural_symbols, [expected, expected])
    assert not np.array_equal(result.reconstructed_natural_symbols, alice)
    assert result.transmitted_row_count_bits_per_block == 2


@pytest.mark.parametrize("encoding", ["NATURAL", "GRAY"])
@pytest.mark.parametrize("order", ["LSB_FIRST", "MSB_FIRST"])
def test_q8_identity_syndrome_roundtrip_all_encodings_and_orders(encoding, order) -> None:
    model = prior.build_conditional_prior_model(
        np.ones((8, 8), dtype=np.float64), encoding=encoding, order=order
    )
    alice = np.arange(8, dtype=np.uint8)
    bob = np.arange(7, -1, -1, dtype=np.uint8)
    matrices = tuple(
        sparse.identity(8, format="csr", dtype=np.uint8)
        for _ in model.stages
    )
    disclosure = msd.disclose_syndromes(alice, model, matrices)
    calls = []

    def identity_syndrome_factory(*, parity_check_matrix, error_channel):
        calls.append((parity_check_matrix, np.asarray(error_channel).copy()))

        class FakeDecoder:
            def decode(self, delta):
                return np.asarray(delta).copy()

        return FakeDecoder()

    result = msd.receive_syndromes(
        model, bob, matrices, disclosure.public_syndromes, identity_syndrome_factory
    )

    assert np.array_equal(result.reconstructed_natural_symbols, alice)
    assert len(result.recovered_stage_bits) == 3
    assert result.attempted_stage_syndrome_passed == (True, True, True)
    assert result.unsupported_counts_by_attempted_stage == (0, 0, 0)
    assert result.transmitted_row_count_bits_per_block == 24
    assert len(calls) == 3
    for matrix, error_channel in calls:
        assert matrix.shape == (8, 8)
        assert error_channel == pytest.approx(np.full(8, 0.5))


def test_receiver_forwards_bob_dependent_per_variable_error_probabilities() -> None:
    counts = np.array([[9.0, 1.0], [1.0, 4.0]])
    model = prior.build_conditional_prior_model(
        counts, encoding="NATURAL", order="LSB_FIRST"
    )
    alice = np.zeros(4, dtype=np.uint8)
    bob = np.array([0, 1, 0, 1], dtype=np.uint8)
    matrix = sparse.identity(4, format="csr", dtype=np.uint8)
    disclosure = msd.disclose_syndromes(alice, model, (matrix,))
    calls = []

    def delta_factory(*, parity_check_matrix, error_channel):
        calls.append(np.asarray(error_channel).copy())

        class FakeDecoder:
            def decode(self, delta):
                return np.asarray(delta).copy()

        return FakeDecoder()

    result = msd.receive_syndromes(
        model, bob, (matrix,), disclosure.public_syndromes, delta_factory
    )

    assert calls[0] == pytest.approx([0.1, 0.2, 0.1, 0.2])
    assert np.array_equal(result.reconstructed_natural_symbols, alice)
    assert result.attempted_stage_syndrome_passed == (True,)


def test_receiver_stops_after_first_failed_syndrome_check() -> None:
    model = _model()
    alice = np.array([0, 0], dtype=np.uint8)
    bob = np.array([0, 0], dtype=np.uint8)
    matrices = (
        sparse.csr_matrix([[1, 1]], dtype=np.uint8),
        sparse.csr_matrix([[1, 0]], dtype=np.uint8),
    )
    disclosure = msd.disclose_syndromes(alice, model, matrices)
    calls, deltas = [], []
    factory = _fake_factory([np.array([1, 0], dtype=np.uint8)], calls, deltas)

    result = msd.receive_syndromes(
        model, bob, matrices, disclosure.public_syndromes, factory
    )

    assert len(calls) == 1
    assert result.attempted_stage_syndrome_passed == (False,)
    assert len(result.recovered_stage_bits) == 1
    assert result.reconstructed_natural_symbols is None
    assert result.transmitted_row_count_bits_per_block == 2


@pytest.mark.parametrize("encoding", ["NATURAL", "GRAY"])
@pytest.mark.parametrize("order", ["LSB_FIRST", "MSB_FIRST"])
def test_exact_prior_bypass_for_all_encodings_and_orders(encoding, order) -> None:
    model = prior.build_conditional_prior_model(
        np.eye(4, dtype=np.float64), encoding=encoding, order=order
    )
    alice = np.arange(4, dtype=np.uint8)
    matrices = tuple(
        sparse.identity(4, format="csr", dtype=np.uint8)
        for _ in model.stages
    )
    disclosure = msd.disclose_syndromes(alice, model, matrices)
    factory_calls = []

    def forbidden_factory(**kwargs):
        factory_calls.append(kwargs)
        raise AssertionError("fully deterministic stage called the decoder factory")

    result = msd.receive_syndromes(
        model,
        alice,
        matrices,
        disclosure.public_syndromes,
        forbidden_factory,
        skip_fully_deterministic=np.bool_(True),
    )

    assert factory_calls == []
    assert np.array_equal(result.reconstructed_natural_symbols, alice)
    assert result.attempted_stage_syndrome_passed == (True, True)
    assert result.unsupported_counts_by_attempted_stage == (0, 0)
    assert result.transmitted_row_count_bits_per_block == 8


def test_mixed_ambiguous_then_deterministic_stage_uses_recovered_prefix() -> None:
    counts = np.zeros((4, 4), dtype=np.float64)
    counts[0, 0] = 1.0
    counts[3, 0] = 1.0
    model = prior.build_conditional_prior_model(
        counts, encoding="NATURAL", order="LSB_FIRST"
    )
    alice = np.array([0, 0], dtype=np.uint8)
    bob = np.array([0, 0], dtype=np.uint8)
    matrix = sparse.csr_matrix([[1, 1]], dtype=np.uint8)
    matrices = (matrix, matrix)
    disclosure = msd.disclose_syndromes(alice, model, matrices)
    calls, deltas = [], []

    def one_call_factory(*, parity_check_matrix, error_channel):
        calls.append(np.asarray(error_channel).copy())
        if len(calls) > 1:
            raise AssertionError("deterministic second stage called the factory")

        class FakeDecoder:
            def decode(self, delta):
                deltas.append(np.asarray(delta).copy())
                return np.array([1, 1], dtype=np.uint8)

        return FakeDecoder()

    result = msd.receive_syndromes(
        model,
        bob,
        matrices,
        disclosure.public_syndromes,
        one_call_factory,
        skip_fully_deterministic=True,
    )

    assert len(calls) == 1
    assert calls[0] == pytest.approx([0.5, 0.5])
    assert np.array_equal(deltas[0], [0])
    assert np.array_equal(result.recovered_stage_bits[0], [1, 1])
    # The recovered prefix 1 makes the next natural high bit exactly 1;
    # using Alice's truth prefix 0 would make that next bit 0.
    assert np.array_equal(result.recovered_stage_bits[1], [1, 1])
    assert np.array_equal(result.reconstructed_natural_symbols, [3, 3])
    assert result.attempted_stage_syndrome_passed == (True, True)
    assert result.transmitted_row_count_bits_per_block == 2


def test_exact_prior_syndrome_conflict_stops_without_factory_or_row_discount() -> None:
    model = prior.build_conditional_prior_model(
        np.eye(4, dtype=np.float64), encoding="NATURAL", order="LSB_FIRST"
    )
    bob = np.array([0], dtype=np.uint8)
    matrices = (
        sparse.csr_matrix([[1]], dtype=np.uint8),
        sparse.csr_matrix([[1]], dtype=np.uint8),
    )
    calls = []

    def forbidden_factory(**kwargs):
        calls.append(kwargs)
        raise AssertionError("exact-prior conflict must stop without a decoder")

    result = msd.receive_syndromes(
        model,
        bob,
        matrices,
        ([1], [0]),
        forbidden_factory,
        skip_fully_deterministic=True,
    )

    assert calls == []
    assert result.attempted_stage_syndrome_passed == (False,)
    assert np.array_equal(result.recovered_stage_bits[0], [0])
    assert result.reconstructed_natural_symbols is None
    assert result.transmitted_row_count_bits_per_block == 2


def test_exact_prior_mixed_zero_and_positive_vector_keeps_factory_path() -> None:
    counts = np.array([[1.0, 1.0], [0.0, 1.0]])
    model = prior.build_conditional_prior_model(
        counts, encoding="NATURAL", order="LSB_FIRST"
    )
    alice = np.array([0, 0], dtype=np.uint8)
    bob = np.array([0, 1], dtype=np.uint8)
    zero_row = sparse.csr_matrix([[0, 0]], dtype=np.uint8)
    disclosure = msd.disclose_syndromes(alice, model, (zero_row,))
    calls, deltas = [], []
    factory = _fake_factory([np.zeros(2, dtype=np.uint8)], calls, deltas)

    result = msd.receive_syndromes(
        model,
        bob,
        (zero_row,),
        disclosure.public_syndromes,
        factory,
        skip_fully_deterministic=True,
    )

    assert len(calls) == 1
    assert calls[0]["error_channel"] == pytest.approx([0.0, 0.5])
    assert np.array_equal(deltas[0], [0])
    assert result.attempted_stage_syndrome_passed == (True,)
    assert result.transmitted_row_count_bits_per_block == 1


def test_exact_prior_unsupported_half_probability_keeps_factory_path() -> None:
    counts = np.zeros((2, 2), dtype=np.float64)
    counts[0, 0] = 1.0
    model = prior.build_conditional_prior_model(
        counts, encoding="NATURAL", order="LSB_FIRST"
    )
    alice = np.array([0], dtype=np.uint8)
    bob = np.array([1], dtype=np.uint8)
    matrix = sparse.csr_matrix([[1]], dtype=np.uint8)
    disclosure = msd.disclose_syndromes(alice, model, (matrix,))
    calls, deltas = [], []
    factory = _fake_factory([np.zeros(1, dtype=np.uint8)], calls, deltas)

    result = msd.receive_syndromes(
        model,
        bob,
        (matrix,),
        disclosure.public_syndromes,
        factory,
        skip_fully_deterministic=True,
    )

    assert len(calls) == 1
    assert calls[0]["error_channel"] == pytest.approx([0.5])
    assert result.unsupported_counts_by_attempted_stage == (1,)
    assert result.attempted_stage_syndrome_passed == (True,)
    assert result.transmitted_row_count_bits_per_block == 1


@pytest.mark.parametrize(
    "flag_kwargs",
    [
        {},
        {"skip_fully_deterministic": False},
        {"skip_fully_deterministic": np.bool_(False)},
        {"condition_exact_variables": False},
        {"condition_exact_variables": np.bool_(False)},
    ],
)
def test_default_and_false_flag_keep_legacy_factory_calls(flag_kwargs) -> None:
    model = prior.build_conditional_prior_model(
        np.eye(4, dtype=np.float64), encoding="NATURAL", order="LSB_FIRST"
    )
    alice = np.arange(4, dtype=np.uint8)
    matrices = tuple(
        sparse.identity(4, format="csr", dtype=np.uint8)
        for _ in model.stages
    )
    disclosure = msd.disclose_syndromes(alice, model, matrices)
    calls, deltas = [], []
    factory = _fake_factory(
        [np.zeros(4, dtype=np.uint8), np.zeros(4, dtype=np.uint8)], calls, deltas
    )
    result = msd.receive_syndromes(
        model, alice, matrices, disclosure.public_syndromes, factory, **flag_kwargs
    )

    assert len(calls) == 2
    assert [call["error_channel"].tolist() for call in calls] == [
        [0.0] * 4,
        [0.0] * 4,
    ]
    assert result.attempted_stage_syndrome_passed == (True, True)
    assert result.transmitted_row_count_bits_per_block == 8
    assert inspect.signature(msd.receive_syndromes).parameters[
        "skip_fully_deterministic"
    ].default is False
    assert inspect.signature(msd.receive_syndromes).parameters[
        "condition_exact_variables"
    ].default is False


@pytest.mark.parametrize("invalid_flag", [0, 1, None, "true", np.int64(1)])
def test_invalid_exact_prior_flag_is_rejected_before_factory(invalid_flag) -> None:
    model = prior.build_conditional_prior_model(
        np.eye(4, dtype=np.float64), encoding="NATURAL", order="LSB_FIRST"
    )
    bob = np.array([0], dtype=np.uint8)
    matrix = sparse.csr_matrix([[1]], dtype=np.uint8)
    calls = []

    def factory(**kwargs):
        calls.append(kwargs)
        raise AssertionError("invalid flag must fail before the decoder factory")

    with pytest.raises(ValueError, match="skip_fully_deterministic must be bool"):
        msd.receive_syndromes(
            model,
            bob,
            (matrix, matrix),
            ([0], [0]),
            factory,
            skip_fully_deterministic=invalid_flag,
        )
    assert calls == []


@pytest.mark.parametrize("skip_flag", [False, True])
def test_condition_exact_variables_handles_all_fixed_stages_independently(
    skip_flag,
) -> None:
    model = prior.build_conditional_prior_model(
        np.eye(4, dtype=np.float64), encoding="NATURAL", order="LSB_FIRST"
    )
    alice = np.arange(4, dtype=np.uint8)
    matrices = tuple(
        sparse.identity(4, format="csr", dtype=np.uint8)
        for _ in model.stages
    )
    disclosure = msd.disclose_syndromes(alice, model, matrices)
    calls = []

    def forbidden_factory(**kwargs):
        calls.append(kwargs)
        raise AssertionError("all-fixed conditioning must not call the backend")

    result = msd.receive_syndromes(
        model,
        alice,
        matrices,
        disclosure.public_syndromes,
        forbidden_factory,
        skip_fully_deterministic=skip_flag,
        condition_exact_variables=np.bool_(True),
    )

    assert calls == []
    assert np.array_equal(result.reconstructed_natural_symbols, alice)
    assert result.attempted_stage_syndrome_passed == (True, True)
    assert result.transmitted_row_count_bits_per_block == 8


def test_conditioned_factory_gets_ordered_active_system_and_errors_scatter() -> None:
    model = _conditioned_q8_model()
    bob = np.array([0, 1, 2, 3, 4], dtype=np.uint8)
    alice = np.array([0, 1, 1, 1, 0], dtype=np.uint8)
    matrix = _conditioned_csr_with_stored_zero()
    empty = sparse.csr_matrix((0, bob.size), dtype=np.uint8)
    matrices = (matrix, empty, empty)
    disclosure = msd.disclose_syndromes(alice, model, matrices)
    bob_copy = bob.copy()
    syndrome_copies = tuple(value.copy() for value in disclosure.public_syndromes)
    matrix_copies = (matrix.data.copy(), matrix.indices.copy(), matrix.indptr.copy())
    model_copies = tuple(
        (stage.p_one_by_bob_prefix.copy(), stage.support_by_bob_prefix.copy())
        for stage in model.stages
    )
    calls, deltas = [], []

    def active_factory(*, parity_check_matrix, error_channel):
        calls.append(
            (parity_check_matrix, np.asarray(error_channel).copy())
        )

        class FakeDecoder:
            def decode(self, delta):
                deltas.append(np.asarray(delta).copy())
                return np.array([1, 1, 0], dtype=np.uint8)

        return FakeDecoder()

    result = msd.receive_syndromes(
        model,
        bob,
        matrices,
        disclosure.public_syndromes,
        active_factory,
        condition_exact_variables=True,
    )

    assert len(calls) == 1
    reduced, active_channel = calls[0]
    assert reduced is not matrix
    assert reduced.shape == (3, 3)
    expected_reduced = sparse.csr_matrix(
        [[1, 1, 0], [0, 1, 0], [0, 0, 1]], dtype=np.uint8
    )
    assert (reduced != expected_reduced).nnz == 0
    assert active_channel[0] == pytest.approx(0.5)
    assert active_channel[1] > 0.0
    assert active_channel[1] == pytest.approx(1e-12, rel=1e-9, abs=0.0)
    assert active_channel[2] == pytest.approx(0.5)  # unsupported Bob symbol
    assert np.array_equal(deltas[0], [0, 1, 0])
    assert np.array_equal(result.recovered_stage_bits[0], [0, 1, 1, 1, 0])
    assert result.attempted_stage_syndrome_passed == (True, True, True)
    assert result.unsupported_counts_by_attempted_stage[0] == 1
    assert result.transmitted_row_count_bits_per_block == 6
    assert np.array_equal(matrix.data, matrix_copies[0])
    assert np.array_equal(matrix.indices, matrix_copies[1])
    assert np.array_equal(matrix.indptr, matrix_copies[2])
    assert np.array_equal(bob, bob_copy)
    for actual, expected in zip(disclosure.public_syndromes, syndrome_copies):
        assert np.array_equal(actual, expected)
    for stage, (p_one, support) in zip(model.stages, model_copies):
        assert np.array_equal(stage.p_one_by_bob_prefix, p_one)
        assert np.array_equal(stage.support_by_bob_prefix, support)


def test_conditioned_next_stage_uses_actual_recovered_prefix() -> None:
    model = prior.build_conditional_prior_model(
        _dependent_counts("NATURAL", "LSB_FIRST"),
        encoding="NATURAL",
        order="LSB_FIRST",
    )
    alice = np.array([0, 0], dtype=np.uint8)
    bob = np.array([0, 0], dtype=np.uint8)
    matrices = (
        sparse.csr_matrix([[1, 1]], dtype=np.uint8),
        sparse.identity(2, format="csr", dtype=np.uint8),
    )
    disclosure = msd.disclose_syndromes(alice, model, matrices)
    calls = []

    def prefix_factory(*, parity_check_matrix, error_channel):
        calls.append(np.asarray(error_channel).copy())

        class FakeDecoder:
            def decode(self, delta):
                return np.array([1, 1], dtype=np.uint8)

        return FakeDecoder()

    result = msd.receive_syndromes(
        model,
        bob,
        matrices,
        disclosure.public_syndromes,
        prefix_factory,
        condition_exact_variables=True,
    )

    assert len(calls) == 2
    assert calls[0] == pytest.approx([0.5, 0.5])
    assert calls[1] == pytest.approx([0.2, 0.2])
    assert result.attempted_stage_syndrome_passed == (True, True)
    assert np.array_equal(result.recovered_stage_bits[0], [1, 1])
    assert np.array_equal(result.reconstructed_natural_symbols, [1, 1])
    assert not np.array_equal(result.reconstructed_natural_symbols, alice)


def test_conditioned_zero_row_conflict_stops_and_keeps_full_disclosure() -> None:
    model = _conditioned_q8_model()
    bob = np.array([0, 1, 2, 3, 4], dtype=np.uint8)
    alice = np.array([0, 1, 1, 1, 0], dtype=np.uint8)
    first = _conditioned_csr_with_stored_zero()
    future = sparse.csr_matrix(
        [[1, 0, 0, 0, 0], [0, 0, 0, 0, 1]], dtype=np.uint8
    )
    disclosure = msd.disclose_syndromes(alice, model, (first, future, future))
    conflicting = [value.copy() for value in disclosure.public_syndromes]
    conflicting[0][0] = 1  # row 0 becomes zero after exact-zero conditioning
    calls = []

    def forbidden_factory(**kwargs):
        calls.append(kwargs)
        raise AssertionError("a removed equation conflict must not call backend")

    result = msd.receive_syndromes(
        model,
        bob,
        (first, future, future),
        conflicting,
        forbidden_factory,
        condition_exact_variables=True,
    )

    assert calls == []
    assert result.attempted_stage_syndrome_passed == (False,)
    assert np.array_equal(result.recovered_stage_bits[0], [0, 0, 1, 0, 0])
    assert result.reconstructed_natural_symbols is None
    assert result.transmitted_row_count_bits_per_block == 10


def test_conditioned_empty_equations_keep_positive_probability_map_choices() -> None:
    model = _model()
    bob = np.array([0, 0], dtype=np.uint8)
    alice = np.array([0, 0], dtype=np.uint8)
    matrices = tuple(
        sparse.csr_matrix((0, 2), dtype=np.uint8) for _ in model.stages
    )
    disclosure = msd.disclose_syndromes(alice, model, matrices)
    calls = []

    def forbidden_factory(**kwargs):
        calls.append(kwargs)
        raise AssertionError("an empty equation system must not call backend")

    result = msd.receive_syndromes(
        model,
        bob,
        matrices,
        disclosure.public_syndromes,
        forbidden_factory,
        condition_exact_variables=True,
    )

    assert calls == []
    assert result.attempted_stage_syndrome_passed == (True, True)
    assert np.array_equal(result.reconstructed_natural_symbols, [0, 0])
    assert result.transmitted_row_count_bits_per_block == 0


def test_conditioned_invalid_reduced_decoder_output_is_rejected() -> None:
    model = prior.build_conditional_prior_model(
        np.array([[1.0, 1.0], [0.0, 1.0]]),
        encoding="NATURAL",
        order="LSB_FIRST",
    )
    bob = np.array([0, 1], dtype=np.uint8)
    matrix = sparse.csr_matrix([[1, 1]], dtype=np.uint8)
    calls = []

    def wrong_width_factory(*, parity_check_matrix, error_channel):
        calls.append((parity_check_matrix.copy(), np.asarray(error_channel).copy()))

        class FakeDecoder:
            def decode(self, delta):
                return np.zeros(2, dtype=np.uint8)

        return FakeDecoder()

    with pytest.raises(ValueError, match="length-1 binary vector"):
        msd.receive_syndromes(
            model,
            bob,
            (matrix,),
            ([0],),
            wrong_width_factory,
            condition_exact_variables=True,
        )

    assert len(calls) == 1
    assert calls[0][0].shape == (1, 1)
    assert calls[0][1] == pytest.approx([0.5])


@pytest.mark.parametrize("invalid_flag", [0, 1, None, "true", np.int64(1)])
def test_invalid_condition_exact_variables_flag_is_rejected_before_factory(
    invalid_flag,
) -> None:
    model = _model()
    bob = np.array([0], dtype=np.uint8)
    matrix = sparse.csr_matrix([[1]], dtype=np.uint8)
    calls = []

    def factory(**kwargs):
        calls.append(kwargs)
        raise AssertionError("invalid flag must fail before decoder factory")

    with pytest.raises(ValueError, match="condition_exact_variables must be bool"):
        msd.receive_syndromes(
            model,
            bob,
            (matrix, matrix),
            ([0], [0]),
            factory,
            condition_exact_variables=invalid_flag,
        )
    assert calls == []


def test_sender_rejects_invalid_alice_stage_and_matrix_inputs() -> None:
    model = _model()
    valid = (
        sparse.csr_matrix([[1, 0]], dtype=np.uint8),
        sparse.csr_matrix([[0, 1]], dtype=np.uint8),
    )
    with pytest.raises(ValueError, match="one-dimensional"):
        msd.disclose_syndromes([[0, 1]], model, valid)
    with pytest.raises(ValueError, match="integer symbols"):
        msd.disclose_syndromes([0.0, 1.0], model, valid)
    with pytest.raises(ValueError, match=r"lie in \[0, 4\)"):
        msd.disclose_syndromes([0, 4], model, valid)
    with pytest.raises(ValueError, match="one parity-check matrix"):
        msd.disclose_syndromes([0, 1], model, valid[:1])
    with pytest.raises(ValueError, match="CSR matrix"):
        msd.disclose_syndromes([0, 1], model, (np.array([[1, 0]]), valid[1]))
    with pytest.raises(ValueError, match="2 columns"):
        msd.disclose_syndromes(
            [0, 1], model, (sparse.csr_matrix([[1, 0, 0]]), valid[1])
        )
    with pytest.raises(ValueError, match="binary"):
        msd.disclose_syndromes(
            [0, 1],
            model,
            (sparse.csr_matrix([[2, 0]], dtype=np.int64), valid[1]),
        )


def test_receiver_rejects_invalid_public_syndromes_and_fake_output() -> None:
    model = prior.build_conditional_prior_model(
        np.ones((2, 2)), encoding="NATURAL", order="LSB_FIRST"
    )
    alice = np.array([0, 0], dtype=np.uint8)
    bob = np.array([0, 0], dtype=np.uint8)
    matrix = sparse.csr_matrix([[1, 0]], dtype=np.uint8)
    disclosure = msd.disclose_syndromes(alice, model, (matrix,))

    with pytest.raises(ValueError, match="one public syndrome"):
        msd.receive_syndromes(model, bob, (matrix,), (), lambda **kwargs: None)
    with pytest.raises(ValueError, match="length-1"):
        msd.receive_syndromes(
            model, bob, (matrix,), ([0, 1],), lambda **kwargs: None
        )
    with pytest.raises(ValueError, match="binary values"):
        msd.receive_syndromes(
            model, bob, (matrix,), ([2],), lambda **kwargs: None
        )
    with pytest.raises(ValueError, match="explicitly callable"):
        msd.receive_syndromes(
            model, bob, (matrix,), disclosure.public_syndromes, None
        )
    with pytest.raises(ValueError, match="lie in "):
        msd.receive_syndromes(
            model, [2, 0], (matrix,), disclosure.public_syndromes, lambda **kwargs: None
        )

    for output in (np.array([0]), np.array([0, 2])):
        calls, deltas = [], []
        factory = _fake_factory([output], calls, deltas)
        with pytest.raises(ValueError, match="decoder output"):
            msd.receive_syndromes(
                model, bob, (matrix,), disclosure.public_syndromes, factory
            )


def test_bp_factory_is_lazy_and_receives_explicit_parallel_budget(monkeypatch) -> None:
    captured = {}

    class FakeBpDecoder:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    fake_package = ModuleType("ldpc")
    fake_package.BpDecoder = FakeBpDecoder
    monkeypatch.setitem(sys.modules, "ldpc", fake_package)

    matrix = sparse.csr_matrix([[1, 0, 1]], dtype=np.uint8)
    channel = np.array([0.1, 0.2, 0.3])
    decoder = msd.make_bp_decoder(
        parity_check_matrix=matrix,
        error_channel=channel,
        max_iter=17,
    )

    assert isinstance(decoder, FakeBpDecoder)
    assert captured["pcm"] is matrix
    assert captured["error_channel"] == pytest.approx(channel.tolist())
    assert captured["max_iter"] == 17
    assert captured["input_vector_type"] == "syndrome"
    assert captured["schedule"] == "parallel"
    assert captured["omp_thread_count"] == 1
    assert captured["random_serial_schedule"] is False
    assert inspect.signature(msd.receive_syndromes).parameters[
        "decoder_factory"
    ].default is inspect.Parameter.empty
    assert inspect.signature(msd.make_bp_decoder).parameters["max_iter"].default is inspect.Parameter.empty
