"""Deterministic mathematics tests for conditional MSD bit priors."""

from __future__ import annotations

import math

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import msd_conditional_prior as prior


def _parity_counts() -> np.ndarray:
    counts = np.zeros((4, 4), dtype=np.float64)
    for alice in range(4):
        bob = (alice & 1) ^ ((alice >> 1) & 1)
        counts[alice, bob] = 1.0
    return counts


def test_parity_tables_cover_both_complete_orders_and_exact_support() -> None:
    counts = _parity_counts()
    lsb = prior.build_conditional_prior_model(
        counts, encoding="NATURAL", order="LSB_FIRST"
    )
    msb = prior.build_conditional_prior_model(
        counts, encoding="NATURAL", order="MSB_FIRST"
    )

    assert lsb.bit_order_from_lsb == (0, 1)
    assert msb.bit_order_from_lsb == (1, 0)
    for model in (lsb, msb):
        first = model.query(0, [0, 1, 2], np.empty((0, 3), dtype=np.uint8))
        assert np.array_equal(first.p_one, [0.5, 0.5, 0.5])
        assert np.array_equal(first.unsupported, [False, False, True])

    second = lsb.query(
        1,
        [0, 0, 1, 1, 2],
        np.array([[0, 1, 0, 1, 0]], dtype=np.uint8),
    )
    assert np.array_equal(second.p_one, [0.0, 1.0, 1.0, 0.0, 0.5])
    assert np.array_equal(second.unsupported, [False, False, False, False, True])

    reversed_second = msb.query(
        1,
        [0, 0, 1, 1],
        np.array([[0, 1, 1, 0]], dtype=np.uint8),
    )
    assert np.array_equal(reversed_second.p_one, [0.0, 1.0, 0.0, 1.0])
    assert not np.any(reversed_second.unsupported)


def test_gray_labels_match_explicitly_relabelled_natural_rows() -> None:
    counts = np.arange(1, 17, dtype=np.float64).reshape(4, 4)
    natural_symbols = np.arange(4, dtype=np.int64)
    gray_labels = natural_symbols ^ (natural_symbols >> 1)
    relabelled_counts = np.zeros_like(counts)
    relabelled_counts[gray_labels] = counts

    gray = prior.build_conditional_prior_model(
        counts, encoding="GRAY", order="LSB_FIRST"
    )
    relabelled_natural = prior.build_conditional_prior_model(
        relabelled_counts, encoding="NATURAL", order="LSB_FIRST"
    )
    assert gray.encoding == "GRAY"
    assert gray.bit_order_from_lsb == relabelled_natural.bit_order_from_lsb
    for gray_stage, natural_stage in zip(gray.stages, relabelled_natural.stages):
        assert np.array_equal(
            gray_stage.p_one_by_bob_prefix,
            natural_stage.p_one_by_bob_prefix,
        )
        assert np.array_equal(
            gray_stage.support_by_bob_prefix,
            natural_stage.support_by_bob_prefix,
        )

    bob_symbols = [0, 2, 3]
    previous_bits = np.array([[1, 0, 1]], dtype=np.uint8)
    assert np.array_equal(
        gray.query(1, bob_symbols, previous_bits).p_one,
        relabelled_natural.query(1, bob_symbols, previous_bits).p_one,
    )


def test_nonuniform_conditional_probability_uses_full_natural_bob_symbol() -> None:
    counts = np.array([[3.0, 0.0], [1.0, 0.0]])
    model = prior.build_conditional_prior_model(
        counts, encoding="NATURAL", order="LSB_FIRST"
    )

    query = model.query(0, [0, 1], np.empty((0, 2), dtype=np.uint8))
    assert query.p_one[0] == pytest.approx(0.25)
    assert query.p_one[1] == 0.5
    assert np.array_equal(query.unsupported, [False, True])


def test_soft_error_adapter_preserves_map_tie_error_and_finite_llr() -> None:
    query = prior.PriorQuery(
        p_one=np.array([0.0, 0.25, 0.5, 0.75, 1.0]),
        unsupported=np.array([False, False, True, False, False]),
    )
    adapted = prior.adapt_soft_error_prior(query, llr_floor=1e-6)

    assert np.array_equal(adapted.base_bits, [0, 0, 0, 1, 1])
    assert np.array_equal(adapted.p_error, [0.0, 0.25, 0.5, 0.25, 0.0])
    assert adapted.llr_natural_log[0] == pytest.approx(-math.log(1e-6))
    assert adapted.llr_natural_log[1] == pytest.approx(math.log(3.0))
    assert adapted.llr_natural_log[2] == pytest.approx(0.0)
    assert adapted.llr_natural_log[3] == pytest.approx(-math.log(3.0))
    assert adapted.llr_natural_log[4] == pytest.approx(math.log(1e-6))
    assert np.all(np.isfinite(adapted.llr_natural_log))
    assert np.array_equal(adapted.unsupported, query.unsupported)


@pytest.mark.parametrize(
    "counts",
    [
        [[1, 2, 3], [4, 5, 6]],
        [[0, 0], [0, 0]],
        [[1, -1], [0, 1]],
        [[1, math.nan], [0, 1]],
    ],
)
def test_invalid_counts_are_rejected(counts: object) -> None:
    with pytest.raises(ValueError):
        prior.build_conditional_prior_model(
            counts, encoding="NATURAL", order="LSB_FIRST"
        )


@pytest.mark.parametrize("order", [[0, 0], [0], "SIDEWAYS"])
def test_incomplete_or_invalid_orders_are_rejected(order: object) -> None:
    with pytest.raises(ValueError):
        prior.build_conditional_prior_model(
            np.ones((4, 4)), encoding="NATURAL", order=order
        )


def test_invalid_encoding_query_domain_and_llr_inputs_are_rejected() -> None:
    counts = _parity_counts()
    with pytest.raises(ValueError, match="encoding"):
        prior.build_conditional_prior_model(
            counts, encoding="BINARY", order="LSB_FIRST"
        )

    model = prior.build_conditional_prior_model(
        counts, encoding="NATURAL", order="LSB_FIRST"
    )
    no_prefix = np.empty((0, 2), dtype=np.uint8)
    with pytest.raises(ValueError, match="stage_index"):
        model.query(True, [0, 1], no_prefix)
    with pytest.raises(ValueError, match="stage_index"):
        model.query(2, [0, 1], no_prefix)
    with pytest.raises(ValueError, match="one-dimensional"):
        model.query(0, [[0, 1]], no_prefix)
    with pytest.raises(ValueError, match="integer indices"):
        model.query(0, [0.0, 1.0], no_prefix)
    with pytest.raises(ValueError, match="integer indices"):
        model.query(0, np.array([True, False]), no_prefix)
    with pytest.raises(ValueError, match="outside the alphabet"):
        model.query(0, [0, 4], no_prefix)
    with pytest.raises(ValueError, match="outside the alphabet"):
        model.query(0, [-1], np.empty((0, 1), dtype=np.uint8))
    empty = model.query(0, [], np.empty((0, 0), dtype=np.uint8))
    assert empty.p_one.size == 0
    assert empty.unsupported.size == 0
    with pytest.raises(ValueError, match="shape"):
        model.query(1, [0, 1], no_prefix)
    with pytest.raises(ValueError, match="only 0 or 1"):
        model.query(1, [0, 1], np.array([[0, 2]], dtype=np.int64))
    with pytest.raises(ValueError, match="only 0 or 1"):
        model.query(1, [0, 1], np.array([[0, -1]], dtype=np.int64))

    valid_query = model.query(0, [0], np.empty((0, 1), dtype=np.uint8))
    for floor in (0.0, 0.5, math.nan, True):
        with pytest.raises(ValueError, match="llr_floor"):
            prior.adapt_soft_error_prior(valid_query, llr_floor=floor)
    with pytest.raises(ValueError, match="probabilities"):
        prior.adapt_soft_error_prior(
            prior.PriorQuery(np.array([1.1]), np.array([False])), llr_floor=1e-6
        )
