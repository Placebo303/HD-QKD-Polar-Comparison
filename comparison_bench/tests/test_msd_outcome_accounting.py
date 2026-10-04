import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir.msd_outcome_accounting import (
    OUTCOMES,
    aggregate_native_ledgers,
    compare_paired_native_ledgers,
    evaluate_block_outcome,
    native_block_ledger,
)


def _byte_tag(symbols):
    return bytes(int(symbol) for symbol in symbols)


def _outcome(alice, candidate, *, syndrome_ok=True, tag_function=_byte_tag, alphabet_size=8):
    return evaluate_block_outcome(
        alice,
        candidate,
        alphabet_size=alphabet_size,
        syndrome_ok=syndrome_ok,
        tag_function=tag_function,
    )


def _ledger(
    n,
    *,
    alice=None,
    candidate=None,
    syndrome_ok=True,
    tag_function=_byte_tag,
    H_A=0.5,
    H_AB=0.4,
    disclosure=0,
    tag_bits=0,
):
    if alice is None:
        alice = np.arange(n, dtype=np.int64) % 8
    if candidate is None and syndrome_ok:
        candidate = np.array(alice, copy=True)
    classification = _outcome(
        alice, candidate, syndrome_ok=syndrome_ok, tag_function=tag_function
    )
    return native_block_ledger(
        N_symbols=n,
        H_A_bits_per_symbol=H_A,
        H_A_given_B_bits_per_symbol=H_AB,
        disclosure_bits=disclosure,
        tag_bits=tag_bits,
        classification=classification,
    )


def test_l1_distinguishes_verified_exact_tag_rejection_and_wrong_collision():
    alice = np.array([1, 2, 3], dtype=np.int64)
    exact = _outcome(alice, np.array([1, 2, 3], dtype=np.int32))
    rejected = _outcome(alice, np.array([1, 2, 4], dtype=np.int64))
    collision = _outcome(
        alice,
        np.array([0, 0, 0], dtype=np.int64),
        tag_function=lambda _symbols: b"same-tag",
    )

    assert exact.outcome == "verified_exact"
    assert (exact.exact_match, exact.tag_match, exact.operationally_accepted) == (
        True,
        True,
        True,
    )
    assert rejected.outcome == "tag_rejected"
    assert (rejected.exact_match, rejected.tag_match, rejected.operationally_accepted) == (
        False,
        False,
        False,
    )
    assert collision.outcome == "accepted_wrong"
    assert (collision.exact_match, collision.tag_match, collision.operationally_accepted) == (
        False,
        True,
        True,
    )
    assert set(OUTCOMES) == {
        "syndrome_rejected",
        "tag_rejected",
        "verified_exact",
        "accepted_wrong",
    }


def test_syndrome_rejection_needs_no_candidate_and_is_not_tag_acceptance():
    result = _outcome(
        np.array([1, 2], dtype=np.int64), None, syndrome_ok=False
    )
    assert result.outcome == "syndrome_rejected"
    assert result.syndrome_ok is False
    assert result.exact_match is None
    assert result.tag_match is None
    assert result.operationally_accepted is False
    with pytest.raises(ValueError, match="requires a complete receiver candidate"):
        _outcome(np.array([1], dtype=np.int64), None, syndrome_ok=True)


def test_tag_callback_gets_int64_copies_and_cannot_mutate_inputs_or_classification():
    alice = np.array([1, 2, 3], dtype=np.int16)
    candidate = np.array([1, 2, 4], dtype=np.uint8)
    original_alice = alice.copy()
    original_candidate = candidate.copy()
    seen = []

    def mutating_tag(symbols):
        seen.append((symbols.dtype, symbols.ndim, symbols.copy()))
        symbols[:] = 0
        return bytes(int(symbol) for symbol in seen[-1][2])

    result = _outcome(alice, candidate, tag_function=mutating_tag)

    assert result.outcome == "tag_rejected"
    assert result.exact_match is False
    assert result.tag_match is False
    assert all(dtype == np.dtype(np.int64) and ndim == 1 for dtype, ndim, _ in seen)
    assert len(seen) == 2
    assert not np.shares_memory(seen[0][2], seen[1][2])
    np.testing.assert_array_equal(alice, original_alice)
    np.testing.assert_array_equal(candidate, original_candidate)


@pytest.mark.parametrize(
    "alice,candidate,alphabet_size,syndrome_ok,tag_function",
    [
        (np.array([[1, 2]]), np.array([1, 2]), 8, True, _byte_tag),
        (np.array([1.0, 2.0]), np.array([1, 2]), 8, True, _byte_tag),
        (np.array([-1, 2]), np.array([1, 2]), 8, True, _byte_tag),
        (np.array([1, 8]), np.array([1, 2]), 8, True, _byte_tag),
        (np.array([1], dtype=np.uint64) * np.uint64(2**63), np.array([1]), 8, True, _byte_tag),
        (np.array([1, 2]), np.array([1]), 8, True, _byte_tag),
        (np.array([1]), np.array([1]), 2**63, True, _byte_tag),
        (np.array([1]), np.array([1]), 8, 1, _byte_tag),
        (np.array([1]), np.array([1]), 8, True, None),
        (
            np.array([1]),
            np.array([1]),
            8,
            True,
            lambda _symbols: bytearray(b"not bytes"),
        ),
    ],
)
def test_l1_rejects_invalid_inputs_and_tag_output(
    alice, candidate, alphabet_size, syndrome_ok, tag_function
):
    with pytest.raises(ValueError):
        evaluate_block_outcome(
            alice,
            candidate,
            alphabet_size=alphabet_size,
            syndrome_ok=syndrome_ok,
            tag_function=tag_function,
        )


def test_l2_uses_actual_costs_and_kept_bits_failure_penalty():
    rejected = _ledger(
        100,
        alice=np.arange(100, dtype=np.int64) % 8,
        candidate=(np.arange(100, dtype=np.int64) + 1) % 8,
        H_A=0.5,
        H_AB=0.4,
        disclosure=30,
        tag_bits=3,
    )
    assert rejected.outcome == "tag_rejected"
    assert rejected.H_A_total_bits == 50
    assert rejected.kept_bits == 20
    assert rejected.failure_indicator == 1
    assert rejected.failure_penalty_bits == 20
    assert rejected.Y_expected_bits == -3
    assert rejected.expected_f_numerator_bits == 53
    assert rejected.H_A_given_B_total_bits == 40
    assert rejected.f_expected_dimensionless == pytest.approx(53 / 40)
    assert rejected.valid_yield is True

    wrong = _ledger(
        2,
        alice=np.array([1, 2]),
        candidate=np.array([0, 0]),
        tag_function=lambda _symbols: b"collision",
        H_A=0.5,
        H_AB=0.25,
        disclosure=0,
        tag_bits=1,
    )
    assert wrong.outcome == "accepted_wrong"
    assert wrong.failure_indicator == 1
    assert wrong.failure_penalty_bits == wrong.kept_bits


def test_l2_negative_kept_and_zero_denominator_are_explicit():
    exact = _outcome(np.array([1, 2]), np.array([1, 2]))
    negative = native_block_ledger(
        N_symbols=2,
        H_A_bits_per_symbol=0.5,
        H_A_given_B_bits_per_symbol=0.25,
        disclosure_bits=2,
        tag_bits=0,
        classification=exact,
    )
    assert negative.kept_bits == -1
    assert negative.Y_expected_bits == -1
    assert negative.valid_yield is False
    assert negative.f_expected_dimensionless is None

    zero_denominator = native_block_ledger(
        N_symbols=2,
        H_A_bits_per_symbol=0.5,
        H_A_given_B_bits_per_symbol=0.0,
        disclosure_bits=0,
        tag_bits=0,
        classification=exact,
    )
    assert zero_denominator.valid_yield is True
    assert zero_denominator.H_A_given_B_total_bits == 0
    assert zero_denominator.f_expected_dimensionless is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"N_symbols": 0},
        {"N_symbols": 3},
    ],
)
def test_l2_requires_positive_native_volume_matching_l1(kwargs):
    classification = _outcome(np.array([1, 2]), np.array([1, 2]))
    with pytest.raises(ValueError, match="N_symbols"):
        native_block_ledger(
            N_symbols=kwargs["N_symbols"],
            H_A_bits_per_symbol=0.5,
            H_A_given_B_bits_per_symbol=0.25,
            disclosure_bits=0,
            tag_bits=0,
            classification=classification,
        )


def test_l2_rejects_invalid_entropy_and_actual_costs():
    classification = _outcome(np.array([1, 2]), np.array([1, 2]))
    for H_A, H_AB, disclosure, tag_bits in [
        (0.5, 0.6, 0, 0),
        (-0.1, 0.0, 0, 0),
        (0.5, 0.2, -1, 0),
        (0.5, 0.2, 0, 1.5),
    ]:
        with pytest.raises(ValueError):
            native_block_ledger(
                N_symbols=2,
                H_A_bits_per_symbol=H_A,
                H_A_given_B_bits_per_symbol=H_AB,
                disclosure_bits=disclosure,
                tag_bits=tag_bits,
                classification=classification,
            )


def test_l3_aggregates_weight_each_block_failure_and_count_all_outcomes():
    exact = _ledger(100, H_A=0.5, H_AB=0.4, disclosure=0, tag_bits=2)
    failed = _ledger(
        100,
        candidate=(np.arange(100, dtype=np.int64) + 1) % 8,
        H_A=0.5,
        H_AB=0.4,
        disclosure=30,
        tag_bits=3,
    )
    collision = _ledger(
        1,
        alice=np.array([1]),
        candidate=np.array([0]),
        tag_function=lambda _symbols: b"same",
    )
    rejected = _ledger(1, candidate=None, syndrome_ok=False)
    aggregate = aggregate_native_ledgers((exact, failed, collision, rejected))

    assert aggregate.block_count == 4
    assert aggregate.N_symbols == 202
    assert dict(aggregate.outcome_counts) == {
        "syndrome_rejected": 1,
        "tag_rejected": 1,
        "verified_exact": 1,
        "accepted_wrong": 1,
    }
    assert aggregate.failure_indicator_sum == 3
    assert aggregate.failure_penalty_bits == pytest.approx(20 + 0.5 + 0.5)
    naive_mean_product = aggregate.kept_bits * (aggregate.failure_indicator_sum / 4)
    assert aggregate.failure_penalty_bits != pytest.approx(naive_mean_product)
    assert aggregate.expected_f_numerator_bits == pytest.approx(
        aggregate.disclosure_bits + aggregate.tag_bits + aggregate.failure_penalty_bits
    )
    assert aggregate.Y_expected_bits == pytest.approx(
        aggregate.kept_bits - aggregate.tag_bits - aggregate.failure_penalty_bits
    )


def test_l3_paired_native_short_controls_match_common_long_volume_and_actual_tags():
    long = [
        _ledger(200, H_A=0.5, H_AB=0.4, disclosure=30, tag_bits=40),
    ]
    control = [
        _ledger(100, H_A=0.5, H_AB=0.4, disclosure=15, tag_bits=32),
        _ledger(100, H_A=0.5, H_AB=0.4, disclosure=15, tag_bits=32),
    ]
    comparison = compare_paired_native_ledgers(long, control)

    assert comparison.long.N_symbols == comparison.control.N_symbols == 200
    assert comparison.long.tag_bits == 40
    assert comparison.control.tag_bits == 64
    assert comparison.long.H_A_total_bits == comparison.control.H_A_total_bits == 100
    assert comparison.long.H_A_given_B_total_bits == comparison.control.H_A_given_B_total_bits == 80
    assert comparison.f_difference_long_minus_control == pytest.approx(
        comparison.long.f_expected_dimensionless - comparison.control.f_expected_dimensionless
    )


def test_l3_rejects_empty_or_unequal_pair_volume_and_entropy():
    base = _ledger(100, H_A=0.5, H_AB=0.4)
    with pytest.raises(ValueError, match="at least one"):
        aggregate_native_ledgers(())
    with pytest.raises(ValueError, match="equal complete-symbol volume"):
        compare_paired_native_ledgers((base,), (_ledger(99),))
    with pytest.raises(ValueError, match="common H_A_total_bits"):
        compare_paired_native_ledgers((base,), (_ledger(100, H_A=0.49, H_AB=0.4),))
    with pytest.raises(ValueError, match="common H_A_given_B_total_bits"):
        compare_paired_native_ledgers((base,), (_ledger(100, H_A=0.5, H_AB=0.39),))
