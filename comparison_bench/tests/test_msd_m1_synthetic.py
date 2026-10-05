"""Focused T0/T1 tests for the M1 synthetic runner (no decoder execution)."""

import math

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
    decode_error_min_sum_llr,
    disclosure_per_plane,
    wilson_upper,
)
from comparison_bench.src.comparison_bench.methods.binary_spa_numpy import (  # noqa: E402
    decode_error_numpy_min_sum,
)


def test_disclosure_rule_clamps():
    h = [0.0, 0.5, 0.999]
    m = disclosure_per_plane(h, 1024, 0.10)
    assert m[0] == math.ceil(1024 * 0.10)
    assert m[1] == math.ceil(1024 * 0.60)
    assert m[2] == 1023  # clamped to N-1
    assert all(1 <= v <= 1023 for v in m)


def test_wilson_upper_sanity():
    assert wilson_upper(0, 0) == 1.0
    assert 0.0 < wilson_upper(3, 300) < 0.05
    assert wilson_upper(3, 300) > 3 / 300
    assert wilson_upper(300, 300) > 0.99


def _tiny_h():
    return np.array([[1, 1, 0], [1, 0, 1], [0, 1, 1]], dtype=np.uint8)


def test_llr_kernel_matches_uniform_backend():
    """With a uniform LLR, the M1-local kernel must equal binary_spa_numpy exactly."""
    h = _tiny_h()
    llr0 = math.log((1 - 0.02) / 0.02)
    llr = np.full(3, llr0)
    for syndrome in (np.array([0, 0, 0], dtype=np.uint8), np.array([1, 0, 1], dtype=np.uint8)):
        ref = decode_error_numpy_min_sum(h, syndrome, max_iter=50, error_rate=0.02)
        got = decode_error_min_sum_llr(h, syndrome, llr, max_iter=50)
        assert ref[1] == got[1] and ref[2] == got[2]
        assert np.array_equal(ref[0], got[0])


def test_llr_kernel_rejects_bad_shapes():
    h = _tiny_h()
    try:
        decode_error_min_sum_llr(h, np.zeros(2, dtype=np.uint8), np.zeros(3))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
