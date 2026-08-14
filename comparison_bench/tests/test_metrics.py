from __future__ import annotations

import numpy as np

from comparison_bench.src.comparison_bench.metrics.leakage import compute_beta_eff_empirical, estimate_cascade_leak_bits, estimate_ldpc_leak_bits
from comparison_bench.src.comparison_bench.metrics.verification import verify_frames_crc32, verify_frames_hash


def test_leakage_calculations():
    assert estimate_cascade_leak_bits(10, 32) == 42.0
    assert estimate_ldpc_leak_bits(20, 32, 2) == 54.0
    beta = compute_beta_eff_empirical(10, 1000, 0.05)
    assert 0.0 < beta < 1.0


def test_verification():
    a = np.asarray([[0, 1, 1, 0], [1, 0, 0, 1]], dtype=np.uint8)
    b = a.copy()
    b[1, 0] = 0
    assert verify_frames_crc32(a, b).tolist() == [True, False]
    assert verify_frames_hash(a, b, truncate_bits=16).tolist() == [True, False]
