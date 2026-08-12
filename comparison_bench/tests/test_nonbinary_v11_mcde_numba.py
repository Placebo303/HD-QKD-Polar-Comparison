"""V11 numba hot-kernel correctness tests (AMEND-2026-08-06-01, T1/T0).

Verification families for the njit kernels integrated into
``nonbinary_v11_mcde.py`` (authorized by AMEND-2026-08-06-01, exactly this
module only):

- **known-answer butterfly regression**: a delta (unit impulse) input must
  transform to all ones, and a delta at ``q/2`` to the alternating ``+1/-1``
  pattern — either catches the half-block butterfly bug (a butterfly that
  only touches half the pairs leaves the output non-constant);
- **numpy references**: the njit WHT, check convolution, product
  (variable/belief) updates and the floored normalization must agree with
  small in-test pure-numpy references within ``allclose(rtol=1e-12)``;
- **frozen RNG draw order**: the njit-backed public coupled updates must
  consume the RNG in the same order as the previous numpy implementation
  (mixture position draw per slot, then per-position row draws) — verified
  by replaying the identical RNG state through a numpy reference and
  comparing outputs;
- **import discipline**: among the V11 modules (mcde / smp_de / microbench
  / CLI), only ``nonbinary_v11_mcde.py`` may import numba.

The existing 24 tests in ``test_nonbinary_v11_mcde.py`` (w=0 byte-identity
to V9, V8 oracle, normalization, rate contract) continue to run unchanged.
"""
from __future__ import annotations

import os
import re

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v11_mcde as v11

_FLOOR = 1e-300


# --------------------------------------------------------------------------- #
# in-test pure-numpy references (test-only; mirror the previous numpy
# semantics of nonbinary_v11_mcde.py)
# --------------------------------------------------------------------------- #


def _numpy_wht_reference(block: np.ndarray) -> np.ndarray:
    """Unnormalized XOR-order WHT, numpy butterfly (the previous ``fwht_batched``
    implementation: per stage read the original halves, write sums/diffs)."""
    array = np.asarray(block, dtype=np.float64)
    q = array.shape[-1]
    out = array.reshape(-1, q).copy()
    width = 1
    while width < q:
        paired = out.reshape(-1, 2 * width)
        left = paired[:, :width].copy()
        right = paired[:, width:].copy()
        paired[:, :width] = left + right
        paired[:, width:] = left - right
        width *= 2
    return out.reshape(array.shape)


def _numpy_check_conv_reference(v2c: np.ndarray, pos: np.ndarray, idx: np.ndarray,
                                draws: np.ndarray) -> np.ndarray:
    """Check-node convolution in pure numpy (the previous ``check_update_coupled``
    semantics: accumulate the WHT spectra, inverse WHT, ``/q``, floor,
    normalize).  ``v2c`` is the stacked ``(npos, n, q)`` mixture."""
    n, q = v2c.shape[1], v2c.shape[2]
    acc = np.ones((n, q))  # spectrum of delta at 0 = all ones
    for d in range(idx.shape[0]):
        incoming = np.empty((n, q), dtype=np.float64)
        for i in range(n):
            incoming[i] = v2c[pos[d, i], idx[d, i]]
        mask = draws > d
        acc = np.where(mask[:, None], acc * _numpy_wht_reference(incoming), acc)
    conv = _numpy_wht_reference(acc) / q
    floored = np.maximum(conv, _FLOOR)
    return floored / floored.sum(axis=1, keepdims=True)


def _numpy_product_reference(c2v: np.ndarray, channel: np.ndarray, pos: np.ndarray,
                             idx: np.ndarray, draws: np.ndarray) -> np.ndarray:
    """Variable/belief product update in pure numpy (the previous numpy
    semantics: pointwise products per draw slot, floor, normalize)."""
    n, q = channel.shape
    product = channel.copy()
    for d in range(idx.shape[0]):
        incoming = np.empty((n, q), dtype=np.float64)
        for i in range(n):
            incoming[i] = c2v[pos[d, i], idx[d, i]]
        mask = draws > d
        product = np.where(mask[:, None], product * incoming, product)
    floored = np.maximum(product, _FLOOR)
    return floored / floored.sum(axis=1, keepdims=True)


def _numpy_gather_mixture(populations, base, npos, rng, n, q) -> np.ndarray:
    """The previous numpy ``_gather_mixture`` (frozen RNG draw order)."""
    if npos == 1:
        return populations[base][rng.integers(0, n, size=n)]
    offsets = rng.integers(0, npos, size=n)
    incoming = np.empty((n, q), dtype=np.float64)
    for offset in range(npos):
        selected = offsets == offset
        if not selected.any():
            continue
        incoming[selected] = populations[base + offset][
            rng.integers(0, n, size=int(selected.sum()))]
    return incoming


def _numpy_variable_update_ref(c2v, position, dv_degrees, dv_probs, channel,
                               rng, q, *, w, window) -> np.ndarray:
    c2v_list = [np.asarray(pop, dtype=np.float64) for pop in c2v]
    n = c2v_list[0].shape[0]
    npos = w + 1
    degrees = rng.choice(dv_degrees, size=n, p=dv_probs)
    draws = degrees - 1
    product = channel.copy()
    for draw in range(int(draws.max())):
        mask = draws > draw
        incoming = _numpy_gather_mixture(c2v_list, position, npos, rng, n, q)
        product = np.where(mask[:, None], product * incoming, product)
    floored = np.maximum(product, _FLOOR)
    return floored / floored.sum(axis=1, keepdims=True)


def _numpy_belief_update_ref(c2v, position, dv_degrees, dv_probs, channel,
                             rng, q, *, w, window) -> np.ndarray:
    c2v_list = [np.asarray(pop, dtype=np.float64) for pop in c2v]
    n = c2v_list[0].shape[0]
    npos = w + 1
    degrees = rng.choice(dv_degrees, size=n, p=dv_probs)
    draws = degrees
    product = channel.copy()
    for draw in range(int(draws.max())):
        mask = draws > draw
        incoming = _numpy_gather_mixture(c2v_list, position, npos, rng, n, q)
        product = np.where(mask[:, None], product * incoming, product)
    floored = np.maximum(product, _FLOOR)
    return floored / floored.sum(axis=1, keepdims=True)


def _numpy_check_update_ref(v2c, position, dc_degrees, dc_probs, rng, q, *,
                            w, window) -> np.ndarray:
    v2c_list = [np.asarray(pop, dtype=np.float64) for pop in v2c]
    n = v2c_list[0].shape[0]
    base = max(0, position - w)
    top = min(position, window - 1)
    npos = top - base + 1
    degrees = rng.choice(dc_degrees, size=n, p=dc_probs)
    draws = degrees - 1
    acc = np.ones((n, q), dtype=np.float64)
    for draw in range(int(draws.max())):
        mask = draws > draw
        incoming = _numpy_gather_mixture(v2c_list, base, npos, rng, n, q)
        acc = np.where(mask[:, None], acc * _numpy_wht_reference(incoming), acc)
    conv = _numpy_wht_reference(acc) / q
    floored = np.maximum(conv, _FLOOR)
    return floored / floored.sum(axis=1, keepdims=True)


def _unit_rows(rng: np.random.Generator, shape: tuple) -> np.ndarray:
    rows = rng.random(shape)
    return rows / rows.sum(axis=1, keepdims=True)


# --------------------------------------------------------------------------- #
# known-answer butterfly regression (half-block butterfly bug catcher)
# --------------------------------------------------------------------------- #


def test_numba_wht_known_answer():
    """Delta input -> all-ones output; delta at q/2 -> alternating +/-1."""
    for q in (4, 8, 1024):
        delta = np.zeros(q)
        delta[0] = 1.0
        out = v11.fwht_batched(delta)
        assert np.array_equal(out, np.ones(q)), (q, out[:8])
        delta_mid = np.zeros(q)
        delta_mid[q // 2] = 1.0
        out_mid = v11.fwht_batched(delta_mid)
        expect = np.where((np.arange(q) & (q // 2)) != 0, -1.0, 1.0)
        assert np.array_equal(out_mid, expect), (q, out_mid[:8], expect[:8])
    # batch form exercises the same njit kernel entry point.
    batch = np.zeros((3, 8))
    batch[:, 0] = 1.0
    assert np.array_equal(v11.fwht_batched(batch), np.ones((3, 8)))
    assert np.array_equal(v11._wht_rows_jit(batch), np.ones((3, 8)))
    # the private single-row kernel itself.
    row = np.zeros(8)
    row[0] = 1.0
    v11._wht_row_jit(row)
    assert np.array_equal(row, np.ones(8))


# --------------------------------------------------------------------------- #
# njit vs pure-numpy references (allclose rtol=1e-12)
# --------------------------------------------------------------------------- #


def test_numba_wht_matches_numpy_reference():
    """njit WHT vs the in-test pure-numpy reference: allclose(rtol=1e-12)."""
    rng = np.random.default_rng(2026110401)
    for q in (4, 8, 16, 1024):
        block = rng.random((5, q))
        ref = _numpy_wht_reference(block)
        jit = v11._wht_rows_jit(np.ascontiguousarray(block))
        assert np.allclose(jit, ref, rtol=1e-12, atol=0.0), (q, np.max(np.abs(jit - ref)))
        assert np.max(np.abs(jit - ref)) < 1e-15
        assert np.allclose(v11.fwht_batched(block), ref, rtol=1e-12, atol=0.0)


def test_numba_check_conv_matches_numpy_reference():
    """njit check convolution vs the numpy reference (incl. the per-sample
    degree mask path and the mixture gather): allclose(rtol=1e-12)."""
    rng = np.random.default_rng(2026110402)
    n, q = 40, 16
    v2c = np.stack([_unit_rows(rng, (n, q)) for _ in range(3)])
    cases = [
        rng.integers(1, 4, size=n),        # mixed mask
        np.full(n, 3, dtype=np.int64),     # full mask
        np.full(n, 1, dtype=np.int64),     # degree-2 all draw
        np.zeros(n, dtype=np.int64),       # no draw slots at all
    ]
    for draws in cases:
        max_draws = int(draws.max())
        pos = rng.integers(0, 3, size=(max_draws, n))
        idx = rng.integers(0, n, size=(max_draws, n))
        ref = _numpy_check_conv_reference(v2c, pos, idx, draws)
        jit = v11._check_conv_jit(v2c, pos, idx, draws)
        assert np.allclose(jit, ref, rtol=1e-12, atol=0.0), np.max(np.abs(jit - ref))
    # q=1024 with a high-degree mask path (exercises the skip-optimized
    # masked branch at the formal q).
    n2, q2 = 30, 1024
    v2c2 = np.stack([_unit_rows(rng, (n2, q2)) for _ in range(2)])
    draws2 = rng.integers(1, 6, size=n2)
    max_draws2 = int(draws2.max())
    pos2 = rng.integers(0, 2, size=(max_draws2, n2))
    idx2 = rng.integers(0, n2, size=(max_draws2, n2))
    ref2 = _numpy_check_conv_reference(v2c2, pos2, idx2, draws2)
    jit2 = v11._check_conv_jit(v2c2, pos2, idx2, draws2)
    assert np.allclose(jit2, ref2, rtol=1e-12, atol=0.0), np.max(np.abs(jit2 - ref2))


def test_numba_product_update_matches_numpy_reference():
    """njit variable/belief product update (incl. the floored normalization)
    vs the numpy reference: allclose(rtol=1e-12)."""
    rng = np.random.default_rng(2026110403)
    n, q = 40, 16
    c2v = np.stack([_unit_rows(rng, (n, q)) for _ in range(3)])
    channel = _unit_rows(rng, (n, q))
    for draws in (rng.integers(0, 4, size=n),      # variable-style draws-1
                  rng.integers(1, 5, size=n),      # belief-style draws
                  np.zeros(n, dtype=np.int64),     # no draw slots at all
                  np.full(n, 1, dtype=np.int64)):  # single slot
        max_draws = int(draws.max())
        pos = rng.integers(0, 3, size=(max_draws, n))
        idx = rng.integers(0, n, size=(max_draws, n))
        ref = _numpy_product_reference(c2v, channel, pos, idx, draws)
        jit = v11._product_update_jit(c2v, channel, pos, idx, draws)
        assert np.allclose(jit, ref, rtol=1e-12, atol=0.0), np.max(np.abs(jit - ref))
    # q=1024 path.
    n2, q2 = 30, 1024
    c2v2 = np.stack([_unit_rows(rng, (n2, q2)) for _ in range(2)])
    channel2 = _unit_rows(rng, (n2, q2))
    draws2 = rng.integers(0, 6, size=n2)
    max_draws2 = int(draws2.max())
    pos2 = rng.integers(0, 2, size=(max_draws2, n2))
    idx2 = rng.integers(0, n2, size=(max_draws2, n2))
    ref2 = _numpy_product_reference(c2v2, channel2, pos2, idx2, draws2)
    jit2 = v11._product_update_jit(c2v2, channel2, pos2, idx2, draws2)
    assert np.allclose(jit2, ref2, rtol=1e-12, atol=0.0), np.max(np.abs(jit2 - ref2))


def test_numba_normalization_invariants():
    """The kernels leave rows floored at 1e-300, finite, non-negative and
    normalized (row sums 1 within 1e-9) — incl. a row that collapses to
    sub-floor mass (delta-ish input), where the floor must prevent a zero
    row sum."""
    rng = np.random.default_rng(2026110404)
    n, q = 16, 8
    c2v = np.stack([_unit_rows(rng, (n, q)) for _ in range(2)])
    channel = _unit_rows(rng, (n, q))
    draws = np.full(n, 3, dtype=np.int64)
    pos = np.zeros((3, n), dtype=np.int64)
    idx = rng.integers(0, n, size=(3, n))
    out = v11._product_update_jit(c2v, channel, pos, idx, draws)
    assert np.all(np.isfinite(out)) and np.all(out >= 0.0)
    assert np.max(np.abs(out.sum(axis=1) - 1.0)) < 1e-9
    assert np.min(out) >= _FLOOR
    # check-conv output keeps the same invariants.
    conv = v11._check_conv_jit(c2v, pos, idx, draws)
    assert np.all(np.isfinite(conv)) and np.all(conv >= 0.0)
    assert np.max(np.abs(conv.sum(axis=1) - 1.0)) < 1e-9
    assert np.min(conv) >= _FLOOR


# --------------------------------------------------------------------------- #
# frozen RNG draw order: njit-backed public updates vs the numpy reference
# --------------------------------------------------------------------------- #


def test_coupled_updates_match_numpy_reference_draw_order():
    """The njit-backed public coupled updates (w=1 mixture) consume the RNG
    in the same frozen order as the previous numpy implementation: replaying
    the identical RNG state through the numpy reference yields identical
    outputs within allclose(rtol=1e-12)."""
    q, n = 8, 64
    rng = np.random.default_rng(2026110405)
    c2v = [_unit_rows(np.random.default_rng(2026110406 + i), (n, q)) for i in range(4)]
    v2c = c2v
    channel = _unit_rows(np.random.default_rng(2026110410), (n, q))
    # variable update at position 1, w=1 -> uniform mixture over positions 1..2.
    state = rng.bit_generator.state
    out_jit = v11.variable_update_coupled(c2v, 1, [3, 4], [0.5, 0.5], channel, rng, q,
                                          w=1, window=4)
    rng.bit_generator.state = state
    out_ref = _numpy_variable_update_ref(c2v, 1, [3, 4], [0.5, 0.5], channel, rng, q,
                                         w=1, window=4)
    assert np.allclose(out_jit, out_ref, rtol=1e-12, atol=0.0)
    # belief update at position 2, w=1 -> mixture over positions 2..3.
    state = rng.bit_generator.state
    out_jit = v11.belief_update_coupled(c2v, 2, [3, 4], [0.5, 0.5], channel, rng, q,
                                        w=1, window=4)
    rng.bit_generator.state = state
    out_ref = _numpy_belief_update_ref(c2v, 2, [3, 4], [0.5, 0.5], channel, rng, q,
                                       w=1, window=4)
    assert np.allclose(out_jit, out_ref, rtol=1e-12, atol=0.0)
    # check update at position 1, w=1 -> boundary-truncated mixture over v2c[0:2].
    state = rng.bit_generator.state
    out_jit = v11.check_update_coupled(v2c, 1, [3, 4], [0.5, 0.5], rng, q,
                                       w=1, window=4)
    rng.bit_generator.state = state
    out_ref = _numpy_check_update_ref(v2c, 1, [3, 4], [0.5, 0.5], rng, q,
                                      w=1, window=4)
    assert np.allclose(out_jit, out_ref, rtol=1e-12, atol=0.0)


def test_coupled_w0_updates_match_numpy_reference_draw_order():
    """w=0 single-position updates skip the position draw (frozen V8/V9
    trajectory); the njit path must match the numpy reference bit-for-bit at
    q=4 (the frozen byte-identity regime, cf. the V9 collapse test) and
    within allclose(rtol=1e-12) at q=8 (numpy row-sum vs kernel-sequential
    summation may differ in the last ulp)."""
    q, n = 4, 64
    rng = np.random.default_rng(2026110411)
    pop = _unit_rows(np.random.default_rng(2026110412), (n, q))
    channel = _unit_rows(np.random.default_rng(2026110413), (n, q))
    state = rng.bit_generator.state
    out_jit = v11.variable_update_coupled([pop], 0, [3, 4], [0.5, 0.5], channel, rng, q,
                                          w=0, window=1)
    rng.bit_generator.state = state
    out_ref = _numpy_variable_update_ref([pop], 0, [3, 4], [0.5, 0.5], channel, rng, q,
                                         w=0, window=1)
    assert np.array_equal(out_jit, out_ref)
    state = rng.bit_generator.state
    out_jit = v11.check_update_coupled([pop], 0, [3, 4], [0.5, 0.5], rng, q,
                                       w=0, window=1)
    rng.bit_generator.state = state
    out_ref = _numpy_check_update_ref([pop], 0, [3, 4], [0.5, 0.5], rng, q,
                                      w=0, window=1)
    assert np.array_equal(out_jit, out_ref)
    # q=8: bit-identity is not guaranteed (row-sum reduction order), but the
    # amendment tolerance must hold.
    q8, n8 = 8, 64
    rng8 = np.random.default_rng(2026110415)
    pop8 = _unit_rows(np.random.default_rng(2026110416), (n8, q8))
    ch8 = _unit_rows(np.random.default_rng(2026110417), (n8, q8))
    state = rng8.bit_generator.state
    out8 = v11.variable_update_coupled([pop8], 0, [3, 4], [0.5, 0.5], ch8, rng8, q8,
                                       w=0, window=1)
    rng8.bit_generator.state = state
    ref8 = _numpy_variable_update_ref([pop8], 0, [3, 4], [0.5, 0.5], ch8, rng8, q8,
                                      w=0, window=1)
    assert np.allclose(out8, ref8, rtol=1e-12, atol=0.0)


# --------------------------------------------------------------------------- #
# import discipline (AMEND-2026-08-06-01)
# --------------------------------------------------------------------------- #

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FORMAL_IR_DIR = os.path.join(_REPO_ROOT, "src", "comparison_bench", "formal_ir")
_CLI_DIR = os.path.join(_REPO_ROOT, "src", "comparison_bench", "cli")


def test_numba_import_discipline():
    """Among the V11 modules (mcde / smp_de / microbench / microbench CLI),
    only ``nonbinary_v11_mcde.py`` imports numba."""
    numba_import = re.compile(r"^\s*(from\s+numba\s+import|import\s+numba)", re.MULTILINE)
    allowed = {"nonbinary_v11_mcde.py"}
    files = (
        "nonbinary_v11_mcde.py",
        "nonbinary_v11_smp_de.py",
        "nonbinary_v11_microbench.py",
        os.path.join(_CLI_DIR, "run_formal_nonbinary_v11_microbench.py"),
    )
    for name in files:
        path = name if os.path.isabs(name) else os.path.join(_FORMAL_IR_DIR, name)
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        has_numba = bool(numba_import.search(source))
        base = os.path.basename(name)
        if base in allowed:
            assert has_numba, f"{name} must import numba (amendment authorization)"
        else:
            assert not has_numba, f"{name} must NOT import numba (import discipline)"


def test_fail_closed_still_raised_after_numba():
    """The njit kernels do not weaken the fail-closed convention: all-zero /
    non-finite inputs are still rejected by the public update functions."""
    q, n = 4, 64
    rng = np.random.default_rng(2026110414)
    zero = np.zeros((n, q))
    good = np.full((n, q), 0.25)
    with pytest.raises(ValueError):
        v11.variable_update_coupled([good], 0, [3], [1.0], zero, rng, q, w=0, window=1)
    with pytest.raises(ValueError):
        v11.check_update_coupled([zero], 0, [3], [1.0], rng, q, w=0, window=1)
    with pytest.raises(ValueError):
        v11.belief_update_coupled([good], 0, [3], [1.0], zero, rng, q, w=0, window=1)
