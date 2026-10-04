"""Exact arithmetic tests for the opt-in NB-LDPC check-update candidate."""
from __future__ import annotations

import math

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v10_fftqspa as fft
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField


FIELD32 = GF2mField.create(32)


def _fixed_messages(degree: int, *, uniform: bool = False) -> list[np.ndarray]:
    if uniform:
        return [np.full(32, math.log(1.0 / 32.0), dtype=np.float64)
                for _ in range(degree)]

    symbols = np.arange(32, dtype=np.int64)
    asymmetric_a = -((symbols * 7 + 3) % 31).astype(np.float64) / 5.0
    zero_support_floor = np.full(32, fft.LOG_FLOOR, dtype=np.float64)
    zero_support_floor[[1, 7, 23]] = [0.0, -0.75, -2.5]
    asymmetric_b = -((symbols * symbols + 3) % 37).astype(np.float64) / 8.0
    patterns = [
        np.zeros(32, dtype=np.float64),
        asymmetric_a,
        zero_support_floor,
        asymmetric_b,
    ]
    return [patterns[index % len(patterns)].copy() for index in range(degree)]


@pytest.mark.parametrize("degree", [2, 3, 8])
@pytest.mark.parametrize("syndrome", [0, 9, 31])
@pytest.mark.parametrize("uniform", [False, True])
def test_all_targets_are_bitwise_equal_to_reference(degree, syndrome, uniform):
    messages = _fixed_messages(degree, uniform=uniform)
    coefficients = [1, 3, 5, 7, 11, 17, 23, 31][:degree]

    candidate = fft.check_update_all_log(messages, coefficients, syndrome, FIELD32)
    reference = [
        fft.check_update_log(messages, coefficients, target, syndrome, FIELD32)
        for target in range(degree)
    ]

    assert len(candidate) == degree
    for target, (actual, expected) in enumerate(zip(candidate, reference)):
        assert np.array_equal(actual, expected), (degree, syndrome, uniform, target)


def test_all_targets_preserve_explicit_input_errors():
    good = [np.zeros(32, dtype=np.float64), np.linspace(-2.0, 0.0, 32)]

    with pytest.raises(ValueError, match="pinned GF2mField"):
        fft.check_update_all_log(good, [1, 3], 0, object())
    with pytest.raises(ValueError, match="at least two"):
        fft.check_update_all_log(good[:1], [1], 0, FIELD32)
    with pytest.raises(ValueError, match="match the message count"):
        fft.check_update_all_log(good, [1], 0, FIELD32)
    with pytest.raises(ValueError, match="length-32"):
        fft.check_update_all_log([good[0], np.zeros(31)], [1, 3], 0, FIELD32)

    nonfinite = [good[0], good[1].copy()]
    nonfinite[1][4] = np.nan
    with pytest.raises(ValueError, match="must be finite"):
        fft.check_update_all_log(nonfinite, [1, 3], 0, FIELD32)
    with pytest.raises(ValueError, match="nonzero"):
        fft.check_update_all_log(good, [1, 0], 0, FIELD32)
    with pytest.raises(ValueError, match="symbol"):
        fft.check_update_all_log(good, [1, 3], 32, FIELD32)
