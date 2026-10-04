"""Focused arithmetic checks for conditional information-budget scenarios."""

from __future__ import annotations

import math

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import msd_information_budget as msd


def _parity_counts() -> np.ndarray:
    counts = np.zeros((4, 4), dtype=np.float64)
    for alice in range(4):
        parity = (alice & 1) ^ ((alice >> 1) & 1)
        counts[alice, parity] = 1.0
    return counts


def test_perfect_correlation_has_zero_conditional_information() -> None:
    result = msd.analyze_joint_counts([[5, 0], [0, 7]])

    assert result["H_A_given_B_bits_per_symbol"] == pytest.approx(0.0)
    assert result["V_A_given_B_bits_squared_per_symbol"] == pytest.approx(0.0)
    assert result["sum_chain_H_bit_given_B_prefix_bits_per_symbol"] == pytest.approx(0.0)
    assert result["planes"][0]["V_bit_given_B_prefix_bits_squared_per_symbol"] == pytest.approx(0.0)


def test_independent_uniform_binary_symbols_have_one_bit_conditional_entropy() -> None:
    result = msd.analyze_joint_counts(np.ones((2, 2)))

    assert result["H_A_bits_per_symbol"] == pytest.approx(1.0)
    assert result["H_A_given_B_bits_per_symbol"] == pytest.approx(1.0)
    assert result["V_A_given_B_bits_squared_per_symbol"] == pytest.approx(0.0)
    assert result["planes"][0]["H_bit_given_B_prefix_bits_per_symbol"] == pytest.approx(1.0)
    assert result["planes"][0]["H_bit_given_B_bits_per_symbol"] == pytest.approx(1.0)


def test_dependent_planes_close_chain_and_order_changes_allocation() -> None:
    counts = _parity_counts()
    lsb_first = msd.analyze_joint_counts(counts, "LSB_FIRST")
    msb_first = msd.analyze_joint_counts(counts, "MSB_FIRST")

    assert lsb_first["H_A_given_B_bits_per_symbol"] == pytest.approx(1.0)
    assert msb_first["H_A_given_B_bits_per_symbol"] == pytest.approx(1.0)
    assert lsb_first["sum_chain_H_bit_given_B_prefix_bits_per_symbol"] == pytest.approx(1.0)
    assert msb_first["sum_chain_H_bit_given_B_prefix_bits_per_symbol"] == pytest.approx(1.0)
    assert lsb_first["sum_H_bit_given_B_bits_per_symbol"] == pytest.approx(2.0)
    assert msb_first["sum_H_bit_given_B_bits_per_symbol"] == pytest.approx(2.0)

    lsb_allocation = {
        plane["alice_bit_index_from_lsb"]: plane["H_bit_given_B_prefix_bits_per_symbol"]
        for plane in lsb_first["planes"]
    }
    msb_allocation = {
        plane["alice_bit_index_from_lsb"]: plane["H_bit_given_B_prefix_bits_per_symbol"]
        for plane in msb_first["planes"]
    }
    assert lsb_allocation == pytest.approx({0: 1.0, 1: 0.0})
    assert msb_allocation == pytest.approx({0: 0.0, 1: 1.0})


def test_scenario_charges_tag_once_and_failure_penalty_in_expected_f() -> None:
    result = msd.finite_length_scenario(
        [[9, 1], [1, 9]],
        "MSB_FIRST",
        N=10_000,
        joint_failure_assumption=0.1,
        tag_bits=7,
        budget_bits=9_000,
    )

    kept = result["H_A_total_bits"] - result["L_EC_bits"]
    failure_penalty = kept * 0.1
    expected_numerator = result["L_EC_bits"] + 7 + failure_penalty
    assert result["scenario_kind"] == "NORMAL_APPROX_SCENARIO"
    assert result["expected_failure_penalty_bits"] == pytest.approx(failure_penalty)
    assert result["Y_expected_bits"] == pytest.approx(kept - 7 - failure_penalty)
    assert result["expected_f_numerator_bits"] == pytest.approx(expected_numerator)
    assert result["budget_slack_expected_numerator_bits"] == pytest.approx(
        9_000 - expected_numerator
    )
    assert result["f_expected_dimensionless"] == pytest.approx(
        expected_numerator / result["H_A_given_B_total_bits"]
    )


def test_upper_clip_is_reported() -> None:
    result = msd.finite_length_scenario(
        [[9, 1], [1, 9]],
        "MSB_FIRST",
        N=1,
        joint_failure_assumption=0.1,
        tag_bits=0,
        budget_bits=1,
    )

    plane = result["planes"][0]
    assert plane["m_unclipped_bits"] > 1
    assert plane["m_bits"] == 1
    assert plane["clipped"] is True


def test_negative_kept_bits_remain_visible_and_invalidate_yield() -> None:
    result = msd.finite_length_scenario(
        [[9, 0], [1, 0]],
        "MSB_FIRST",
        N=1,
        joint_failure_assumption=0.1,
        tag_bits=0,
        budget_bits=1,
    )

    assert result["kept_bits"] < 0
    assert result["valid_yield"] is False
    assert result["f_expected_dimensionless"] is None


def test_zero_conditional_entropy_has_no_finite_f_scenario() -> None:
    result = msd.finite_length_scenario(
        [[4, 0], [0, 4]],
        "MSB_FIRST",
        N=100,
        joint_failure_assumption=0.1,
        tag_bits=2,
        budget_bits=10,
    )

    assert result["valid_yield"] is True
    assert result["f_expected_dimensionless"] is None


@pytest.mark.parametrize(
    "counts",
    [
        [[0, 0], [0, 0]],
        [[1, -1], [0, 1]],
        [[1, math.nan], [0, 1]],
        [[1, math.inf], [0, 1]],
        [[1, 2, 3], [4, 5, 6]],
        np.ones((3, 3)),
    ],
)
def test_invalid_count_tables_are_rejected(counts: object) -> None:
    with pytest.raises(ValueError):
        msd.validate_counts(counts)


@pytest.mark.parametrize("order", [[0, 0], [0], "SIDEWAYS"])
def test_incomplete_or_duplicate_bit_orders_are_rejected(order: object) -> None:
    with pytest.raises(ValueError):
        msd.analyze_joint_counts(np.ones((4, 4)), order=order)
