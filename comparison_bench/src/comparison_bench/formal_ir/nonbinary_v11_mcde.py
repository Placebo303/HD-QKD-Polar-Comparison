"""V11 full-vector spatially coupled QSC Monte-Carlo density evolution kernel
(``formal-nonbinary-ldpc-v11-sc-de-gate``, Stage E engineering, V11-20.1;
additive layer, frozen semantics).

Every message is a length-q probability vector — never a scalar reliability.
The variable/check/belief update semantics are exactly the accepted V8/V9
full-vector MC-DE semantics (``nonbinary_v8_mcde`` / ``nonbinary_v9_mcde`` are
read-only semantic references; this module does not import them):

- variable update: a FRESH QSC channel row times the pointwise product of
  ``dv - 1`` iid incoming check rows, ``1e-300`` floor, fail-closed row
  normalization (V9 convention);
- check update: ``dc - 1`` iid incoming rows XOR-convolved via the own batched
  WHT (all-unity coefficients, zero syndrome — the DE check-node message),
  ``1e-300`` floor, fail-closed row normalization;
- belief update: channel row times all ``dv`` incident check rows;
- convergence observable: mean base-q entropy of the check-message population
  below ``entropy_tol`` for ``streak`` consecutive iterations;
- RNG draw order (frozen): degrees first, then one
  ``rng.integers(0, N, N)`` draw per product/convolution slot — the ``w=0``
  single-position run is byte-identical to the V9 uncoupled run with the same
  seed (and matches the V8 run within float tolerance, which is also covered
  by tests).

Spatial coupling (terminated chain; design.md §2 R2, §3, §4):

- chain length ``L >= 1`` variable-node (column) positions ``0..L-1`` and
  ``L + w`` check-node positions ``0..L-1+w``; a check at position ``r``
  connects to the variable positions ``r-w..r`` (truncated at the chain
  boundaries) — the standard terminated SC-LDPC structure;
- uniform edge spreading (frozen rule, design.md §3): every edge independently
  picks a target offset uniform over ``0..w``; at a check position the
  incoming-message mixture is therefore uniform over its valid variable
  positions;
- coupling width ``w`` in ``0..L-1``: ``w = 0`` decouples the chain into
  independent single-position systems with the exact V8/V9 uncoupled update
  semantics (V11-A03 collapse);
- decoding window ``W`` in ``1..L`` (counts spatial column blocks; ``W = L``
  is the full chain): the DE tracks a terminated sub-chain of length ``W`` —
  the active structure of the AEIT 2019 fixed window ``B[1:5W, 1:W]`` — while
  the check distribution is fixed by the full-chain rate contract;
- boundary termination: an offset draw at a position whose neighbors fall
  outside the chain is skipped; the mixture covers only valid positions.

Rate contract (design.md §3): for the uncoupled effective rate ``R_eff``,
``R_base = 1 - (L/(L+w))(1 - R_eff)`` and ``R_L = 1 - ((L+w)/L)(1 - R_base)``;
the check distribution is reconstructed harmonically at ``R_base`` (the
``nonbinary_v10_common.concentrated_check_distribution`` semantics, reused
read-only) and :func:`rate_contract` verifies that ``R_L`` recovers ``R_eff``
within ``HARMONIC_TOL = 1e-12`` (V11-A05).

Variable-node edge distribution (V11-A06): the frozen V10 S1/S3 winners are
embedded below as read-only constants (``V10_WINNER_S1`` / ``V10_WINNER_S3``;
provenance: archived change evidence
``openspec/changes/archive/2026-08-06-formal-nonbinary-ldpc-v10-de-peg-fftqspa/evidence/v10a_execute_results.json``).
V11 never reoptimizes them.  The run accepts any frozen distribution injected
by the caller (the formal-plan stage injects the same winners).

Seed rule (frozen): ``v11_seed(tag) = int(sha256(f"V11:{tag}")[0:8], 16)`` —
the V11 prefix (``202611``) keeps every derived seed disjoint from V8
(``20260804xx``), V9 (``20260901xx``) and V10 (``202610xx``) by construction.

Imports: standard library, numpy, numba, and the accepted V10 shared helpers
(``nonbinary_v10_common``) only — never any V8/V9/V10-DE module, never a
decoder.

Numba integration (amendment ``evidence/resource/v11_budget_amendment.json``,
AMEND-2026-08-06-01): numba (already a root requirements.txt dependency) is
authorized for THIS module's hot kernels only — the XOR-order WHT butterfly
(``_wht_row_jit`` / ``_wht_rows_jit``), the check-node convolution
(``_check_conv_jit``), the variable/belief product updates
(``_product_update_jit``) and the floored row normalization inside the same
kernels.  Import discipline: no other V11 module (``nonbinary_v11_smp_de``,
the microbench, the CLI) and no other formal-IR module receives numba.  No
new dependency is installed.  ``cache=True`` is intentionally NOT used so no
``.npyc`` files are produced; nopython mode only.  The kernels are
value-identical to the previous numpy semantics (tests assert
``allclose(rtol=1e-12)`` against small pure-numpy references plus a
known-answer delta -> all-ones butterfly regression).  The RNG stays entirely
in numpy PCG64 with the frozen draw order (degrees first, then one
``rng.integers(0, N, N)`` draw per product/convolution slot) — the kernels
only consume pre-drawn index arrays, so the RNG trajectory is unchanged and
the ``w=0`` collapse to the V8/V9 uncoupled run stays byte-identical.
"""
from __future__ import annotations

import hashlib
import math
from numbers import Integral
from typing import Any, Mapping

import numpy as np
from numba import njit

from . import nonbinary_v10_common as common

__all__ = [
    "V11_SEED_PREFIX",
    "V11_DRY_RUN_SEED",
    "FROZEN_GEOMETRIES",
    "HARMONIC_TOL",
    "V10_WINNER_S1",
    "V10_WINNER_S3",
    "V10_WINNER_S1_RATE",
    "V10_WINNER_S3_RATE",
    "v11_seed",
    "parse_degree_hist",
    "fwht_batched",
    "entropy_base_q",
    "chain_structure",
    "variable_update_coupled",
    "check_update_coupled",
    "belief_update_coupled",
    "run_coupled_mcde",
    "terminated_rate",
    "base_rate",
    "rate_contract",
    "lambda_validate",
    "concentrated_check_distribution",
    "reconstructed_rate",
    "qsc_channel_message",
    "edge_mean_inverse",
]

#: V11 seed prefix (frozen): 202611xx, provably disjoint from V8 (20260804xx),
#: V9 (20260901xx) and V10 (202610xx).
V11_SEED_PREFIX = "202611"
#: Frozen numeric seed root for engineering dry runs (disjoint prefix).
V11_DRY_RUN_SEED = 2026110101
#: Harmonic rate-contract tolerance (design.md §3: 1e-12).
HARMONIC_TOL = 1e-12
#: Upper bound on any degree in an edge-perspective histogram (V8/V9 rule).
DEGREE_MAX = 64
#: Positivity floor for probability-domain products (V9/V10 convention).
_FLOOR = 1e-300
#: Tolerance for "normalized" input single vectors (V9 rule).
_NORM_TOL = 1e-9

# --------------------------------------------------------------------------- #
# frozen V10 S1/S3 winner distributions (V11-A06: reused, never reoptimized)
# --------------------------------------------------------------------------- #
# Verbatim from the archived V10 execution evidence
# (v10a_execute_results.json, per_search entries "S1" and "S3", key "winner":
# "lambda"): the DE/rand/1/bin winners for the robust f=1.15 strata at
# q=1024.  R_eff is the archived rate_m.R of the same evidence (the exact
# 1 - f*H_q(p) effective rate).  V11 must not reoptimize these.

#: Frozen V10 S1 winner (p=.20 robust, f=1.15) edge-perspective lambda.
V10_WINNER_S1 = {
    2: 0.24743292985233187,
    4: 0.38007906714020584,
    6: 0.03289326150564248,
    10: 0.05380096037231538,
    15: 0.02476575210263755,
    21: 0.11903099781604107,
    25: 0.11735076249858628,
    28: 0.02464626871223953,
}
#: Frozen V10 S1 effective rate (q=1024, f=1.15, p=.20).
V10_WINNER_S1_RATE = 0.6870106892038108

#: Frozen V10 S3 winner (p=.30 robust, f=1.15) edge-perspective lambda.
V10_WINNER_S3 = {
    2: 0.2156204508044688,
    3: 0.2637474167920141,
    12: 0.08280219128587486,
    14: 0.15172808033189372,
    26: 0.058799064193524334,
    27: 0.026187727494643633,
    34: 0.16130785072054216,
    40: 0.039807218377038434,
}
#: Frozen V10 S3 effective rate (q=1024, f=1.15, p=.30).
V10_WINNER_S3_RATE = 0.5537001767622565

#: The exactly three frozen coupled geometries (design.md §4; V11-A07).  No
#: geometry may be added, removed, or changed after the formal plan is frozen.
FROZEN_GEOMETRIES = {
    "G1": {"w": 1, "L": 32, "W": 8},    # low-latency primary
    "G2": {"w": 2, "L": 32, "W": 16},   # wider-coupling sensitivity
    "G3": {"w": 2, "L": 32, "W": 32},   # full-chain control
}


# --------------------------------------------------------------------------- #
# seed derivation (frozen V11 rule)
# --------------------------------------------------------------------------- #


def v11_seed(tag: str) -> int:
    """``int(sha256(f"V11:{tag}")[0:8], 16)`` — frozen V11 derived-seed rule.

    The ``V11:`` prefix keeps every derived seed disjoint from the V8
    (20260804xx), V9 (20260901xx) and V10 (202610xx) seed families by
    construction (same rule shape as ``nonbinary_v10_common.v10_seed``).
    """
    if not isinstance(tag, str):
        raise ValueError("tag must be a string")
    digest = hashlib.sha256(f"V11:{tag}".encode("utf-8")).hexdigest()
    return int(digest[0:8], 16)


# --------------------------------------------------------------------------- #
# degree-distribution helpers (V9 semantics)
# --------------------------------------------------------------------------- #


def parse_degree_hist(hist: Mapping[Any, Any], name: str,
                      degree_max: int) -> tuple[np.ndarray, np.ndarray]:
    """Validate an edge-perspective degree histogram -> ``(degrees, probs)``.

    Accepts a mapping ``degree -> positive finite weight`` (any positive sum;
    the weights are normalized here), rejects empty maps, non-positive /
    non-finite weights and degrees outside ``[1, degree_max]`` (V8/V9
    semantics).
    """
    if isinstance(degree_max, bool) or not isinstance(degree_max, Integral) or int(degree_max) < 2:
        raise ValueError("degree_max must be an integer >= 2")
    degree_max = int(degree_max)
    if not isinstance(hist, Mapping):
        raise ValueError(f"{name} must be a mapping")
    degrees: list[int] = []
    weights: list[float] = []
    for key, value in hist.items():
        if isinstance(key, bool) or not isinstance(key, Integral):
            raise ValueError(f"{name} degrees must be integers")
        degree = int(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or not math.isfinite(float(value)) or float(value) <= 0.0:
            raise ValueError(f"{name} requires positive finite weights")
        if not 1 <= degree <= degree_max:
            raise ValueError(f"{name} degree outside 1..{degree_max}")
        degrees.append(degree)
        weights.append(float(value))
    if not degrees:
        raise ValueError(f"{name} is empty")
    order = np.argsort(degrees)
    degree_array = np.asarray(degrees, dtype=np.int64)[order]
    weight_array = np.asarray(weights, dtype=np.float64)[order]
    total = float(weight_array.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError(f"{name} weights have invalid total")
    return degree_array, weight_array / total


def _as_mapping(degrees: Any, probs: Any) -> dict[int, float]:
    return {int(degree): float(prob) for degree, prob in zip(degrees, probs)}


# --------------------------------------------------------------------------- #
# Walsh-Hadamard transform (V9 own-butterfly semantics)
# --------------------------------------------------------------------------- #


def fwht_batched(values: Any) -> np.ndarray:
    """Unnormalized XOR-order WHT along the last axis, vectorized over the
    leading axes (own implementation of the accepted butterfly; ``WHT(WHT(f))
    = q*f``).

    ``q = values.shape[-1]`` must be a power of two >= 2; the result is
    ``WHT(f)``.  The butterfly itself runs in the njit kernel
    :func:`_wht_rows_jit` (value-identical to the numpy semantics,
    AMEND-2026-08-06-01); validation stays here fail-closed.
    """
    out = np.asarray(values, dtype=np.float64)
    if out.ndim < 1:
        raise ValueError("fwht_batched requires at least one axis")
    q = out.shape[-1]
    if q < 2 or q & (q - 1):
        raise ValueError("last axis size must be a power of two >= 2")
    if not np.all(np.isfinite(out)):
        raise ValueError("fwht_batched inputs must be finite")
    block = np.ascontiguousarray(out.reshape(-1, q))
    return _wht_rows_jit(block).reshape(out.shape)


# --------------------------------------------------------------------------- #
# numba njit hot kernels (AMEND-2026-08-06-01)
# --------------------------------------------------------------------------- #
# numba (already a root requirements.txt dependency, no new dependency)
# accelerates the per-sample MC-DE hot loops below.  cache=True is
# intentionally NOT used so no .npyc files are produced; nopython mode only.
# The kernels are value-identical to the numpy reference semantics (tests
# assert allclose(rtol=1e-12) plus a known-answer delta -> all-ones butterfly
# regression).  The RNG stays entirely in numpy PCG64 with the frozen draw
# order — the kernels only consume pre-drawn index arrays.


@njit(cache=False)
def _wht_row_jit(row: np.ndarray) -> None:
    """In-place unnormalized XOR-order WHT of a single row (own butterfly)."""
    q = row.shape[0]
    width = 1
    while width < q:
        for j in range(0, q, 2 * width):
            for k in range(j, j + width):
                a = row[k]
                b = row[k + width]
                row[k] = a + b
                row[k + width] = a - b
        width *= 2


@njit(cache=False)
def _wht_rows_jit(block: np.ndarray) -> np.ndarray:
    """Unnormalized XOR-order WHT of every row of a 2-D ``(n, q)`` block."""
    out = block.copy()
    for i in range(out.shape[0]):
        _wht_row_jit(out[i])
    return out


@njit(cache=False)
def _check_conv_jit(v2c: np.ndarray, pos: np.ndarray, idx: np.ndarray,
                    draws: np.ndarray) -> np.ndarray:
    """njit check-node convolution over a stacked mixture (V11 semantics).

    ``v2c`` is the stacked ``(npos, n, q)`` mixture; ``pos[d, i]`` is the
    population slot (offset within the stack) and ``idx[d, i]`` the row drawn
    for sample ``i`` at draw slot ``d`` (both pre-drawn by numpy in the
    frozen RNG order).  Per slot: gather the row, WHT it, multiply into the
    accumulated spectrum (delta-at-0 spectrum starts at all ones) only for
    samples whose degree exceeds the slot; then inverse WHT, ``/ q``,
    ``1e-300`` floor and row normalization — all inside the kernel.
    """
    n = v2c.shape[1]
    q = v2c.shape[2]
    acc = np.ones((n, q))  # spectrum of delta at 0 = all ones
    tmp = np.empty(q)
    for d in range(idx.shape[0]):
        for i in range(n):
            if draws[i] > d:
                tmp[:] = v2c[pos[d, i], idx[d, i]]
                _wht_row_jit(tmp)
                for j in range(q):
                    acc[i, j] *= tmp[j]
    for i in range(n):
        _wht_row_jit(acc[i])
    for i in range(n):
        s = 0.0
        for j in range(q):
            v = acc[i, j] / q
            if v < _FLOOR:
                v = _FLOOR
            acc[i, j] = v
            s += v
        for j in range(q):
            acc[i, j] /= s
    return acc


@njit(cache=False)
def _product_update_jit(c2v: np.ndarray, channel: np.ndarray, pos: np.ndarray,
                        idx: np.ndarray, draws: np.ndarray) -> np.ndarray:
    """njit variable/belief product update over a stacked mixture.

    ``c2v`` is the stacked ``(npos, n, q)`` mixture; ``pos``/``idx`` are the
    pre-drawn population slots / row indices (frozen RNG order).  Starts from
    the channel row; per draw slot ``d`` multiply in the pre-drawn incoming
    row for samples whose degree exceeds the slot (``draws = degrees - 1``
    for the variable update, ``draws = degrees`` for the belief update);
    then ``1e-300`` floor and row normalization — all inside the kernel.
    """
    n = channel.shape[0]
    q = channel.shape[1]
    product = channel.copy()
    for d in range(idx.shape[0]):
        for i in range(n):
            if draws[i] > d:
                row = c2v[pos[d, i], idx[d, i]]
                for j in range(q):
                    product[i, j] *= row[j]
    for i in range(n):
        s = 0.0
        for j in range(q):
            v = product[i, j]
            if v < _FLOOR:
                v = _FLOOR
            product[i, j] = v
            s += v
        for j in range(q):
            product[i, j] /= s
    return product


# --------------------------------------------------------------------------- #
# population validation and normalization (fail-closed, V9 semantics)
# --------------------------------------------------------------------------- #


def _qint(q: Any) -> int:
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or int(q) & (int(q) - 1) \
            or int(q) > 1024:
        raise ValueError("V11 requires a power-of-two GF(q) with 2 <= q <= 1024")
    return int(q)


def _validate_pop(pop: Any, n: int, q: int, name: str) -> np.ndarray:
    array = np.asarray(pop, dtype=np.float64)
    if array.shape != (n, q):
        raise ValueError(f"{name} must have shape ({n}, {q})")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    if np.any(array < 0.0):
        raise ValueError(f"{name} must be non-negative")
    totals = array.sum(axis=1)
    if not np.all(np.isfinite(totals)) or np.any(totals <= 0.0):
        raise ValueError(f"{name} must have positive row mass")
    return array


def _validate_normalized(pop: np.ndarray, name: str) -> np.ndarray:
    """Fail-closed validation of a kernel-normalized population.

    The njit kernels already apply the ``1e-300`` floor and the row
    normalization inside the compiled code (AMEND-2026-08-06-01); this
    re-checks the invariants so a NaN/Inf propagating through a kernel is
    still caught and raised (fail-closed) instead of silently flowing into
    the run.
    """
    if not np.all(np.isfinite(pop)):
        raise ValueError(f"{name}: non-finite mass")
    if np.any(pop < -1e-12):
        raise ValueError(f"{name}: negative mass")
    totals = pop.sum(axis=1)
    if not np.all(np.isfinite(totals)) or np.any(totals <= 0.0):
        raise ValueError(f"{name}: zero or non-finite total mass")
    return pop


# --------------------------------------------------------------------------- #
# chain structure (frozen terminated SC-LDPC geometry)
# --------------------------------------------------------------------------- #


def chain_structure(window: int, w: int) -> dict[str, Any]:
    """Terminated SC-LDPC chain structure for a window of ``window`` column
    blocks and coupling width ``w``.

    Returns ``n_vn`` (variable positions ``0..window-1``), ``n_check``
    (check positions ``0..window-1+w``), the per-variable neighbor check
    positions ``vn_neighbors[c] = c..c+w`` (always full inside the window)
    and the per-check neighbor variable positions
    ``check_neighbors[r] = max(0, r-w)..min(r, window-1)`` (boundary-
    truncated).  A check at position ``r`` connects to a variable at ``c``
    iff ``0 <= r - c <= w`` — the frozen terminated SC base-matrix rule.
    """
    if isinstance(window, bool) or not isinstance(window, Integral) or int(window) < 1:
        raise ValueError("window must be a positive integer")
    if isinstance(w, bool) or not isinstance(w, Integral) or int(w) < 0:
        raise ValueError("w must be a non-negative integer")
    window, w = int(window), int(w)
    if w >= window:
        raise ValueError("w must be < window for a terminated chain window")
    n_vn = window
    n_check = window + w
    vn_neighbors = {c: list(range(c, c + w + 1)) for c in range(window)}
    check_neighbors = {}
    for r in range(n_check):
        lo = max(0, r - w)
        hi = min(r, window - 1)
        check_neighbors[r] = list(range(lo, hi + 1))
    return {
        "n_vn": n_vn,
        "n_check": n_check,
        "w": w,
        "vn_neighbors": vn_neighbors,
        "check_neighbors": check_neighbors,
    }


# --------------------------------------------------------------------------- #
# coupled MC-DE update steps (every message is a length-q vector)
# --------------------------------------------------------------------------- #


def _draw_mixture_indices(rng: np.random.Generator, n: int, npos: int,
                          max_draws: int) -> tuple[np.ndarray, np.ndarray]:
    """Pre-draw the frozen RNG sequence for the uniform mixture gather.

    Returns ``(pos, idx)``, both ``(max_draws, n)`` int64: ``pos[d, i]`` is
    the population slot (offset ``0..npos-1``) and ``idx[d, i]`` the row
    index drawn for sample ``i`` at draw slot ``d``.

    Frozen draw order (unchanged from the numpy ``_gather_mixture``
    semantics): when ``npos == 1`` the position draw is skipped so the RNG
    trajectory of a w=0 single-position update is byte-identical to the
    V8/V9 uncoupled update; otherwise one ``rng.integers(0, npos, n)``
    position draw per slot, then one ``rng.integers(0, n, k)`` row draw per
    occupied position (``k`` = count in that position).  The RNG itself
    stays in numpy PCG64; the kernels only consume the drawn indices.
    """
    idx = np.empty((max_draws, n), dtype=np.int64)
    pos = np.zeros((max_draws, n), dtype=np.int64)
    for draw in range(max_draws):
        if npos == 1:
            idx[draw] = rng.integers(0, n, size=n)
        else:
            offsets = rng.integers(0, npos, size=n)
            for offset in range(npos):
                selected = offsets == offset
                k = int(selected.sum())
                if k:
                    idx[draw][selected] = rng.integers(0, n, size=k)
                    pos[draw][selected] = offset
    return pos, idx


def variable_update_coupled(c2v: Any, position: int, dv_degrees: Any, dv_probs: Any,
                            channel: Any, rng: np.random.Generator, q: int, *,
                            w: int, window: int) -> np.ndarray:
    """Variable-node update at one spatial position (V8/V9 full-vector
    semantics).

    Per sample: sample the exact variable degree, multiply in a FRESH channel
    row and ``dv - 1`` iid incoming check rows drawn from the uniform mixture
    over check positions ``position..position+w`` (uniform edge spreading),
    floor and normalize.  RNG draw order (frozen): degrees first, then one
    ``rng.integers(0, N, N)`` draw per product slot; at ``w = 0`` the single
    position is drawn with the exact V8/V9 trajectory.  The product math and
    the floored normalization run in the njit kernel
    :func:`_product_update_jit` (AMEND-2026-08-06-01); the numpy PCG64 draws
    are byte-for-byte unchanged.
    """
    q = _qint(q)
    c2v_list = [np.asarray(pop, dtype=np.float64) for pop in c2v]
    if isinstance(position, bool) or not isinstance(position, Integral) or not 0 <= int(position) < window:
        raise ValueError("position outside the variable-node range")
    position = int(position)
    if isinstance(w, bool) or not isinstance(w, Integral) or int(w) < 0:
        raise ValueError("w must be a non-negative integer")
    if isinstance(window, bool) or not isinstance(window, Integral) or int(window) < 1:
        raise ValueError("window must be a positive integer")
    w, window = int(w), int(window)
    if position + w >= len(c2v_list):
        raise ValueError("c2v does not cover the check neighborhood of the position")
    n = c2v_list[0].shape[0]
    for index in range(position, position + w + 1):
        _validate_pop(c2v_list[index], n, q, f"c2v[{index}]")
    channel = _validate_pop(channel, n, q, "channel")
    dv_degrees, dv_probs = parse_degree_hist(_as_mapping(dv_degrees, dv_probs),
                                             "dv_degrees", DEGREE_MAX)
    npos = w + 1
    degrees = rng.choice(dv_degrees, size=n, p=dv_probs)
    draws = degrees - 1
    max_draws = int(draws.max())
    pos, idx = _draw_mixture_indices(rng, n, npos, max_draws)
    mixture = np.stack([c2v_list[index] for index in range(position, position + w + 1)])
    product = _product_update_jit(mixture, channel, pos, idx, draws)
    return _validate_normalized(product, "variable update")


def check_update_coupled(v2c: Any, position: int, dc_degrees: Any, dc_probs: Any,
                         rng: np.random.Generator, q: int, *,
                         w: int, window: int) -> np.ndarray:
    """Check-node update at one spatial position (V8/V9 full-vector
    semantics).

    Per sample: sample the exact check degree, draw ``dc - 1`` iid incoming
    rows from the uniform mixture over the valid variable positions
    ``max(0, position-w)..min(position, window-1)`` (boundary-truncated),
    XOR-convolve them via the batched WHT (all-unity coefficients, zero
    syndrome), floor and normalize.  RNG draw order (frozen): degrees first,
    then one ``rng.integers(0, N, N)`` draw per convolution slot; at ``w = 0``
    the single position is drawn with the exact V8/V9 trajectory.  The
    convolution and the floored normalization run in the njit kernel
    :func:`_check_conv_jit` (AMEND-2026-08-06-01); the numpy PCG64 draws are
    byte-for-byte unchanged.
    """
    q = _qint(q)
    v2c_list = [np.asarray(pop, dtype=np.float64) for pop in v2c]
    if isinstance(position, bool) or not isinstance(position, Integral) or not 0 <= int(position) < window + int(w):
        raise ValueError("position outside the check-node range")
    position = int(position)
    if isinstance(w, bool) or not isinstance(w, Integral) or int(w) < 0:
        raise ValueError("w must be a non-negative integer")
    if isinstance(window, bool) or not isinstance(window, Integral) or int(window) < 1:
        raise ValueError("window must be a positive integer")
    w, window = int(w), int(window)
    n = v2c_list[0].shape[0]
    base = max(0, position - w)
    top = min(position, window - 1)
    npos = top - base + 1
    for index in range(base, top + 1):
        _validate_pop(v2c_list[index], n, q, f"v2c[{index}]")
    dc_degrees, dc_probs = parse_degree_hist(_as_mapping(dc_degrees, dc_probs),
                                             "dc_degrees", DEGREE_MAX)
    degrees = rng.choice(dc_degrees, size=n, p=dc_probs)
    draws = degrees - 1
    max_draws = int(draws.max())
    pos, idx = _draw_mixture_indices(rng, n, npos, max_draws)
    mixture = np.stack(v2c_list[base:top + 1])
    conv = _check_conv_jit(mixture, pos, idx, draws)
    return _validate_normalized(conv, "check update")


def belief_update_coupled(c2v: Any, position: int, dv_degrees: Any, dv_probs: Any,
                          channel: Any, rng: np.random.Generator, q: int, *,
                          w: int, window: int) -> np.ndarray:
    """Belief population at one spatial position: channel row times all ``dv``
    incident check rows (uniform mixture over ``position..position+w``),
    floored and normalized.  RNG draw order (frozen): degrees first, then one
    ``rng.integers(0, N, N)`` draw per product slot.  The product math and
    the floored normalization run in the njit kernel
    :func:`_product_update_jit` (AMEND-2026-08-06-01); the numpy PCG64 draws
    are byte-for-byte unchanged."""
    q = _qint(q)
    c2v_list = [np.asarray(pop, dtype=np.float64) for pop in c2v]
    if isinstance(position, bool) or not isinstance(position, Integral) or not 0 <= int(position) < window:
        raise ValueError("position outside the variable-node range")
    position = int(position)
    if isinstance(w, bool) or not isinstance(w, Integral) or int(w) < 0:
        raise ValueError("w must be a non-negative integer")
    if isinstance(window, bool) or not isinstance(window, Integral) or int(window) < 1:
        raise ValueError("window must be a positive integer")
    w, window = int(w), int(window)
    if position + w >= len(c2v_list):
        raise ValueError("c2v does not cover the check neighborhood of the position")
    n = c2v_list[0].shape[0]
    for index in range(position, position + w + 1):
        _validate_pop(c2v_list[index], n, q, f"c2v[{index}]")
    channel = _validate_pop(channel, n, q, "channel")
    dv_degrees, dv_probs = parse_degree_hist(_as_mapping(dv_degrees, dv_probs),
                                             "dv_degrees", DEGREE_MAX)
    npos = w + 1
    degrees = rng.choice(dv_degrees, size=n, p=dv_probs)
    draws = degrees
    max_draws = int(draws.max())
    pos, idx = _draw_mixture_indices(rng, n, npos, max_draws)
    mixture = np.stack([c2v_list[index] for index in range(position, position + w + 1)])
    product = _product_update_jit(mixture, channel, pos, idx, draws)
    return _validate_normalized(product, "belief update")


def entropy_base_q(pop: Any) -> float:
    """Mean row entropy in base q: ``mean over rows of -sum p*log_q(p)``
    (0 for a degenerate deterministic mass).  Zero-mass rows are rejected
    fail-closed (V8/V9 semantics)."""
    array = np.asarray(pop, dtype=np.float64)
    if array.ndim != 2:
        raise ValueError("pop must be a 2-D (N, q) array")
    q = array.shape[-1]
    q = _qint(q)
    if not np.all(np.isfinite(array)):
        raise ValueError("pop must be finite")
    if np.any(array < 0.0):
        raise ValueError("pop must be non-negative")
    totals = array.sum(axis=1)
    if not np.all(np.isfinite(totals)) or np.any(totals <= 0.0):
        raise ValueError("pop rows must have positive total mass")
    logq = math.log(q)
    terms = np.zeros_like(array)
    nonzero = array > 0.0
    terms[nonzero] = -array[nonzero] * np.log(array[nonzero]) / logq
    return float(np.mean(terms.sum(axis=1)))


# --------------------------------------------------------------------------- #
# deterministic coupled runs
# --------------------------------------------------------------------------- #


def run_coupled_mcde(q: int, lambda_edge: Mapping[Any, Any], rho_edge: Mapping[Any, Any],
                     p: float, *, L: int, w: int, W: int, n_samples: int, max_iter: int,
                     seed: int, entropy_tol: float = 0.01, streak: int = 20) -> dict:
    """One deterministic full-vector spatially coupled MC-DE run.

    The DE tracks a terminated chain of ``window = W`` column blocks (checks
    ``0..W-1+w``) with the V8/V9 iteration order (frozen): per iteration draw
    the channel rows for every variable position, then all variable updates,
    then all check updates, then all beliefs; the recorded ``entropy`` is the
    mean base-q entropy of the check-message population over all tracked
    positions and ``error_prob`` the fraction of belief argmax symbols != 0
    (mean over positions).  Converges when ``entropy < entropy_tol`` for
    ``streak`` consecutive iterations.  At ``L=1, w=0, W=1`` the RNG draw
    sequence and the arithmetic are byte-identical to the V9 uncoupled run
    with the same seed.  All parameters are validated fail-closed.
    """
    q = _qint(q)
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) \
            or not 0.0 < float(p) < (q - 1.0) / q:
        raise ValueError("q-ary symmetric p is outside the frozen open domain")
    p = float(p)
    if isinstance(L, bool) or not isinstance(L, Integral) or int(L) < 1:
        raise ValueError("L must be an integer >= 1")
    if isinstance(w, bool) or not isinstance(w, Integral) or not 0 <= int(w) < int(L):
        raise ValueError("w must be an integer in 0..L-1")
    if isinstance(W, bool) or not isinstance(W, Integral) or not 1 <= int(W) <= int(L):
        raise ValueError("W must be an integer in 1..L")
    if isinstance(n_samples, bool) or not isinstance(n_samples, Integral) or int(n_samples) < 100:
        raise ValueError("n_samples must be an integer >= 100")
    if isinstance(max_iter, bool) or not isinstance(max_iter, Integral) or not 1 <= int(max_iter) <= 2000:
        raise ValueError("max_iter must be an integer in 1..2000")
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ValueError("seed must be an integer")
    if isinstance(entropy_tol, bool) or not isinstance(entropy_tol, (int, float)) \
            or not math.isfinite(float(entropy_tol)) or float(entropy_tol) <= 0.0:
        raise ValueError("entropy_tol must be positive and finite")
    if isinstance(streak, bool) or not isinstance(streak, Integral) or int(streak) < 1:
        raise ValueError("streak must be a positive integer")
    L, w, W = int(L), int(w), int(W)
    n_samples, max_iter, seed, streak = int(n_samples), int(max_iter), int(seed), int(streak)
    entropy_tol = float(entropy_tol)
    dv_degrees, dv_probs = parse_degree_hist(lambda_edge, "lambda_edge", DEGREE_MAX)
    dc_degrees, dc_probs = parse_degree_hist(rho_edge, "rho_edge", DEGREE_MAX)
    window = W
    rng = np.random.default_rng(seed)
    symbol_probs = np.full(q, p / (q - 1.0), dtype=np.float64)
    symbol_probs[0] = 1.0 - p
    c2v = [np.full((n_samples, q), 1.0 / q, dtype=np.float64)
           for _ in range(window + w)]
    entropy_trace: list[float] = []
    error_trace: list[float] = []
    converged = False
    iterations = 0
    converged_streak = 0
    for iteration in range(1, max_iter + 1):
        channels: list[np.ndarray] = []
        for _ in range(window):
            symbols = rng.choice(q, size=n_samples, p=symbol_probs)
            channel = np.full((n_samples, q), p / (q - 1.0), dtype=np.float64)
            channel[np.arange(n_samples), symbols] = 1.0 - p
            channels.append(channel)
        v2c = [variable_update_coupled(c2v, c, dv_degrees, dv_probs, channels[c], rng, q,
                                       w=w, window=window)
               for c in range(window)]
        c2v = [check_update_coupled(v2c, r, dc_degrees, dc_probs, rng, q, w=w, window=window)
               for r in range(window + w)]
        beliefs = [belief_update_coupled(c2v, c, dv_degrees, dv_probs, channels[c], rng, q,
                                         w=w, window=window)
                   for c in range(window)]
        per_position = [entropy_base_q(pop) for pop in c2v]
        entropy = float(np.mean(per_position))
        error_prob = float(np.mean([
            np.mean(np.argmax(beliefs[c], axis=1) != 0) for c in range(window)]))
        entropy_trace.append(entropy)
        error_trace.append(error_prob)
        iterations = iteration
        converged_streak = converged_streak + 1 if entropy < entropy_tol else 0
        if converged_streak >= streak:
            converged = True
            break
    return {
        "schema": "v11_coupled_mcde_run_v1",
        "converged": converged,
        "iterations": iterations,
        "entropy_trace": entropy_trace,
        "error_trace": error_trace,
        "final_per_position_entropy": per_position,
        "q": q, "p": p, "L": L, "w": w, "W": W, "window": window,
        "n_samples": n_samples, "max_iter": max_iter, "seed": seed,
        "entropy_tol": entropy_tol, "streak": streak,
        "lambda": {int(k): float(v) for k, v in lambda_edge.items()},
        "rho": {int(k): float(v) for k, v in rho_edge.items()},
    }


# --------------------------------------------------------------------------- #
# terminated rate contract (design.md §3)
# --------------------------------------------------------------------------- #


def _validate_chain_params(L: Any, w: Any) -> tuple[int, int]:
    if isinstance(L, bool) or not isinstance(L, Integral) or int(L) < 1:
        raise ValueError("L must be an integer >= 1")
    if isinstance(w, bool) or not isinstance(w, Integral) or not 0 <= int(w) < int(L):
        raise ValueError("w must be an integer in 0..L-1")
    return int(L), int(w)


def terminated_rate(L: Any, w: Any, R_base: Any) -> float:
    """``R_L = 1 - ((L+w)/L)(1 - R_base)`` — the terminated-chain rate."""
    L, w = _validate_chain_params(L, w)
    if isinstance(R_base, bool) or not isinstance(R_base, (int, float)) \
            or not math.isfinite(float(R_base)) or not 0.0 < float(R_base) < 1.0:
        raise ValueError("R_base must be finite and in (0, 1)")
    return 1.0 - ((L + w) / L) * (1.0 - float(R_base))


def base_rate(L: Any, w: Any, R_eff: Any) -> float:
    """``R_base = 1 - (L/(L+w))(1 - R_eff)`` — the interior/base rate."""
    L, w = _validate_chain_params(L, w)
    if isinstance(R_eff, bool) or not isinstance(R_eff, (int, float)) \
            or not math.isfinite(float(R_eff)) or not 0.0 < float(R_eff) < 1.0:
        raise ValueError("R_eff must be finite and in (0, 1)")
    return 1.0 - (L / (L + w)) * (1.0 - float(R_eff))


def rate_contract(L: Any, w: Any, R_eff: Any, lambda_edge: Mapping[Any, Any], *,
                  rho_edge: Mapping[Any, Any] | None = None,
                  tol: float = HARMONIC_TOL) -> dict[str, Any]:
    """Full terminated-rate contract for one ``(L, w)`` geometry (design.md
    §3).

    ``R_base = 1 - (L/(L+w))(1 - R_eff)``; the check distribution is
    reconstructed harmonically at ``R_base`` (``rho_edge``, or built with the
    ``nonbinary_v10_common`` harmonic-exact formula when omitted) and the
    reconstructed base rate plus the terminated rate ``R_L =
    1 - ((L+w)/L)(1 - R_base)`` are compared against ``R_base`` and ``R_eff``.
    ``ok`` is True iff both differences are below ``tol`` (1e-12).
    """
    L, w = _validate_chain_params(L, w)
    if isinstance(R_eff, bool) or not isinstance(R_eff, (int, float)) \
            or not math.isfinite(float(R_eff)) or not 0.0 < float(R_eff) < 1.0:
        raise ValueError("R_eff must be finite and in (0, 1)")
    if isinstance(tol, bool) or not isinstance(tol, (int, float)) \
            or not math.isfinite(float(tol)) or float(tol) <= 0.0:
        raise ValueError("tol must be positive and finite")
    R_eff = float(R_eff)
    tol = float(tol)
    R_base = base_rate(L, w, R_eff)
    if rho_edge is None:
        concentrated = common.concentrated_check_distribution(R_base, lambda_edge)
        rho_edge = {int(degree): float(weight) for degree, weight in (
            (concentrated["dc_lo"], concentrated["w_lo"]),
            (concentrated["dc_hi"], concentrated["w_hi"])) if float(weight) > 0.0}
    reconstructed_base = common.reconstructed_rate(lambda_edge, rho_edge)
    R_L = terminated_rate(L, w, R_base)
    diff_reconstructed = abs(reconstructed_base - R_base)
    diff_terminated = abs(R_L - R_eff)
    return {
        "L": L, "w": w, "R_eff": R_eff,
        "R_base": R_base, "R_L": R_L,
        "rho": {int(k): float(v) for k, v in rho_edge.items()},
        "rate_reconstructed_base": reconstructed_base,
        "diff_reconstructed_vs_base": diff_reconstructed,
        "diff_terminated_vs_eff": diff_terminated,
        "tol": tol,
        "ok": diff_reconstructed < tol and diff_terminated < tol,
    }


# Re-exported V10 helpers (read-only reuse, V11-A06/A05).
lambda_validate = common.lambda_validate
concentrated_check_distribution = common.concentrated_check_distribution
reconstructed_rate = common.reconstructed_rate
qsc_channel_message = common.qsc_channel_message
edge_mean_inverse = common.edge_mean_inverse


# --------------------------------------------------------------------------- #
# module self-check (engineering scope: rate contract + one tiny coupled run)
# --------------------------------------------------------------------------- #


def _self_check() -> None:
    """Engineering self-check: the frozen G1-G3 x S1/S3 rate contract must
    pass at 1e-12 and one tiny deterministic coupled run must execute."""
    import json
    checks: list[dict[str, Any]] = []
    for stratum, winner, rate in (("S1", V10_WINNER_S1, V10_WINNER_S1_RATE),
                                  ("S3", V10_WINNER_S3, V10_WINNER_S3_RATE)):
        for geometry, params in FROZEN_GEOMETRIES.items():
            contract = rate_contract(params["L"], params["w"], rate, winner)
            checks.append({"stratum": stratum, "geometry": geometry, **contract})
    all_ok = all(check["ok"] for check in checks)
    result = {
        "schema": "v11_mcde_self_check_v1",
        "rate_contract_ok": all_ok,
        "geometries": FROZEN_GEOMETRIES,
        "checks": checks,
    }
    if all_ok:
        rho = rate_contract(4, 1, V10_WINNER_S1_RATE, V10_WINNER_S1)["rho"]
        run = run_coupled_mcde(8, V10_WINNER_S1, rho, 0.15, L=4, w=1, W=4,
                               n_samples=100, max_iter=3, seed=V11_DRY_RUN_SEED)
        result["dry_run"] = {key: run[key] for key in
                             ("converged", "iterations", "q", "L", "w", "W",
                              "final_per_position_entropy")}
    print(json.dumps(result, indent=2, sort_keys=True))
    if not all_ok:
        raise SystemExit(f"self-check failed: rate contract violated")
    if "dry_run" not in result:
        raise SystemExit("self-check failed: dry run did not execute")


if __name__ == "__main__":
    _self_check()
