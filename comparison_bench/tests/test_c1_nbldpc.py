"""C-1 A3 GF(q) LDPC tests (OP1): C1-A3-01.

Packet §3.2/§4 T0+T1: construct/disclose/decode API, exact small-case
assertions (shape, alphabet, syndrome arithmetic, disclosure bits),
noiseless q=3 roundtrip at a fixed seed, small-noise run with nonzero
success count, and decode-failure-returns-None semantics.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir.msd_c1_nbldpc import (
    construct,
    decode,
    disclose,
)


def test_construct_shape_alphabet_and_determinism() -> None:
    code = construct(24, 12, 3, seed=7)
    assert code.H.shape == (12, 24)
    assert int(code.H.min()) >= 0 and int(code.H.max()) < 3
    # PEG skeleton with variable degree 3, all edges carry nonzero values.
    col_counts = np.count_nonzero(code.H, axis=0)
    assert col_counts.tolist() == [3] * 24
    assert code.n == 24 and code.m == 12 and code.q == 3
    same = construct(24, 12, 3, seed=7)
    assert np.array_equal(same.H, code.H)
    other = construct(24, 12, 3, seed=8)
    assert not np.array_equal(other.H, code.H)


def test_construct_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError):  # composite q is not a field
        construct(24, 12, 4, seed=1)
    with pytest.raises(ValueError):  # binary out of scope for this module
        construct(24, 12, 2, seed=1)
    with pytest.raises(ValueError):  # degenerate rate
        construct(12, 12, 3, seed=1)
    with pytest.raises(ValueError):
        construct(1, 1, 3, seed=1)


def test_disclose_exact_and_bits() -> None:
    code = construct(12, 6, 3, seed=11)
    a = np.arange(12) % 3
    syndrome, bits = disclose(code, a)
    assert np.array_equal(syndrome, (code.H @ a) % 3)
    # ceil(6 * log2(3)) = ceil(9.5097) = 10.
    assert bits == 10
    assert bits == math.ceil(6 * math.log2(3))
    # Method form agrees with module form.
    syndrome2, bits2 = code.disclose(a)
    assert np.array_equal(syndrome2, syndrome) and bits2 == bits


def test_noiseless_roundtrip_q3_fixed_seed() -> None:
    code = construct(48, 24, 3, seed=1234)
    rng = np.random.default_rng(20261008)
    a = rng.integers(0, 3, size=48)
    syndrome, _ = disclose(code, a)
    recovered = decode(code, a.copy(), syndrome, [1.0, 0.0, 0.0], 50)
    assert recovered is not None
    assert np.array_equal(recovered, a)


def test_small_noise_success_nonzero() -> None:
    # T1: q=3, p≈0.05, N=128 ≤ 256, fixed seeds; must run clean and
    # recover a nonzero number of blocks.
    n, m, q = 128, 64, 3
    code = construct(n, m, q, seed=999)
    prior_g = [0.95, 0.025, 0.025]
    msg_rng = np.random.default_rng(4242)
    err_rng = np.random.default_rng(777)
    errors = err_rng.choice(3, size=(8, n), p=prior_g)
    wins = 0
    for t in range(8):
        a = msg_rng.integers(0, 3, size=n)
        syndrome, _ = disclose(code, a)
        b = (a + errors[t]) % q
        recovered = code.decode(b, syndrome, prior_g, 50)
        assert recovered is None or recovered.shape == (n,)
        if recovered is not None and np.array_equal(recovered, a):
            wins += 1
    assert wins >= 5


def test_decode_failure_returns_none() -> None:
    code = construct(32, 16, 3, seed=5)
    rng = np.random.default_rng(13)
    a = rng.integers(0, 3, size=32)
    syndrome, _ = disclose(code, a)
    b = (a + 1) % 3
    assert not np.array_equal((code.H @ b) % 3, syndrome)
    assert decode(code, b, syndrome, [0.9, 0.05, 0.05], 0) is None


def test_decode_validates_inputs() -> None:
    code = construct(16, 8, 3, seed=3)
    good = np.zeros(16, dtype=int)
    syndrome, _ = disclose(code, good)
    with pytest.raises(ValueError):
        decode(code, np.zeros(15, dtype=int), syndrome, [0.9, 0.05, 0.05], 5)
    with pytest.raises(ValueError):
        decode(code, good, syndrome, [0.5, 0.5], 5)
    with pytest.raises(ValueError):
        decode(code, good, syndrome, [0.9, 0.05, 0.05], -1)
