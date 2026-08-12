"""V8 independent direct probability-domain oracle (additive reference layer).

This module is a deliberately slow, direct, normalized probability-domain
oracle for check-node messages, variable/belief updates and tiny-code
brute-force posterior/MAP enumeration over GF(q).

Independence contract (frozen):

- It MAY import only the accepted field tables (``GF2mField``).
- It MUST NOT import or call any V1-V7 FFT/FWHT/check-update/decoder module
  and MUST NOT use ``numpy.fft`` or any Walsh-Hadamard transform: the check
  convolution is computed by direct XOR convolution (pairwise O(q^2)
  accumulation) using the field's ``add``/``mul``.
- :func:`assert_oracle_independent` scans this module's own source and the
  modules bound in its namespace for the forbidden tokens and returns any
  violations (an empty list means independent).

Fail-closed contract: invalid *inputs* (wrong shapes, non-finite or negative
or unnormalized mass, out-of-domain symbols/coefficients, unboundable
enumerations) raise ``ValueError``; an *emergent* invalid mass during
normalization returns ``None`` exactly like the accepted V1-V7 ``_normalise``
contract, so callers fail closed on either path.
"""
from __future__ import annotations

import inspect
import itertools
import math
import sys
import types
from numbers import Integral
from typing import Any, Sequence

import numpy as np

from .nonbinary_field import GF2mField

__all__ = [
    "oracle_check_update_dense",
    "oracle_check_update_sparse",
    "oracle_variable_update",
    "oracle_belief",
    "bruteforce_coset_map",
    "bruteforce_error_map",
    "assert_oracle_independent",
]

# Bounds frozen by the V8 spec.
_MAX_SPARSE_COMBOS = 2_000_000
_MAX_COSET_VECTORS = 4096

# The forbidden tokens are assembled from fragments so that the source scan
# (which searches for these very tokens) does not trivially match its own
# definition.
_FORBIDDEN_TOKENS = (
    "fw" + "ht",
    "nonbinary_" + "qspa",
    "nonbinary_v" + "7",
    "nonbinary_v" + "6",
    "decode" + "_",
    "pro" + "duction",
)


def _validate_field(field: Any) -> GF2mField:
    if not isinstance(field, GF2mField):
        raise ValueError("field must be a pinned GF2mField")
    return field


def _validate_qvec(values: Any, q: int, name: str) -> np.ndarray:
    """Fail-closed message validation: shape (q,), finite, non-negative, and
    NORMALIZED (sums to 1 within 1e-9).  An unnormalized vector is rejected:
    the frozen oracle contract requires probability vectors on input."""
    vector = np.asarray(values, dtype=np.float64)
    if vector.shape != (q,):
        raise ValueError(f"{name} must be a length-{q} vector")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must be finite")
    if np.any(vector < 0.0):
        raise ValueError(f"{name} must be non-negative")
    total = float(vector.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError(f"{name} must have positive total mass")
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"{name} must be normalized (sums to 1)")
    return vector


def _normalise(values: np.ndarray) -> np.ndarray | None:
    """Production-identical normalization: reject meaningful negatives,
    clip roundoff, return ``None`` on invalid mass (fail closed)."""
    if not np.all(np.isfinite(values)):
        return None
    if np.any(values < -1e-12):
        return None
    clipped = np.maximum(values, 0.0)
    total = float(clipped.sum())
    if not math.isfinite(total) or total <= 0.0:
        return None
    return clipped / total


def _scale_message(field: GF2mField, message: np.ndarray, coefficient: int) -> np.ndarray:
    """``f[c*x] = m[x]`` — coefficient scaling by field multiplication."""
    scaled = np.zeros(field.q, dtype=np.float64)
    for symbol in range(field.q):
        scaled[field.mul(coefficient, symbol)] = message[symbol]
    return scaled


def _validate_coefficient(field: GF2mField, coefficient: Any) -> int:
    """Fail-closed coefficient validation: nonzero field symbol."""
    field.mul(coefficient, 0)  # raises on non-Integral / out-of-domain
    value = int(coefficient)
    if value == 0:
        raise ValueError("check coefficients must be nonzero")
    return value


def _xor_conv_pair(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Direct pairwise XOR convolution of two length-q vectors: O(q^2)."""
    q = a.shape[0]
    out = np.zeros(q, dtype=np.float64)
    indices = np.arange(q)
    for i in range(q):
        ai = a[i]
        if ai == 0.0:
            continue
        out[i ^ indices] += ai * b
    return out


def oracle_check_update_dense(messages: Sequence[np.ndarray], coefficients: Sequence[int],
                              target: int, syndrome: int,
                              field: GF2mField) -> np.ndarray | None:
    """Direct dense check-to-variable update (pairwise XOR convolution).

    ``out[v]`` is proportional to the mass of configurations where
    ``sum_{j != t} c_j * x_j = syndrome + c_t * v`` over the coefficient-scaled
    incoming message distributions, normalized.  O((dc-1) * q^2).
    """
    field = _validate_field(field)
    q = field.q
    dc = len(messages)
    if dc < 2:
        raise ValueError("check update requires at least two messages")
    if isinstance(target, bool) or not isinstance(target, Integral) or not 0 <= int(target) < dc:
        raise ValueError("target outside the message range")
    target = int(target)
    syndrome = field.mul(1, syndrome)  # validates the syndrome symbol
    if len(coefficients) != dc:
        raise ValueError("coefficients must match the message count")
    scaled: list[np.ndarray] = []
    for index, (message, coefficient) in enumerate(zip(messages, coefficients)):
        vector = _validate_qvec(message, q, f"message[{index}]")
        coefficient = _validate_coefficient(field, coefficient)
        scaled.append(_scale_message(field, vector, coefficient))
    others = [index for index in range(dc) if index != target]
    conv = scaled[others[0]].copy()
    for other in others[1:]:
        conv = _xor_conv_pair(conv, scaled[other])
    coefficient = int(coefficients[target])
    outgoing = np.empty(q, dtype=np.float64)
    for v in range(q):
        outgoing[v] = conv[field.add(syndrome, field.mul(coefficient, v))]
    return _normalise(outgoing)


def oracle_check_update_sparse(messages: Sequence[np.ndarray], coefficients: Sequence[int],
                               target: int, syndrome: int,
                               field: GF2mField) -> np.ndarray:
    """Exact support-product check update.

    Enumerates only the support of each incoming message.  For dense inputs
    this is q^(dc-1) combinations and raises ``ValueError`` when that exceeds
    the frozen bound 2_000_000 (bounded).
    """
    field = _validate_field(field)
    q = field.q
    dc = len(messages)
    if dc < 2:
        raise ValueError("check update requires at least two messages")
    if isinstance(target, bool) or not isinstance(target, Integral) or not 0 <= int(target) < dc:
        raise ValueError("target outside the message range")
    target = int(target)
    syndrome = field.mul(1, syndrome)
    if len(coefficients) != dc:
        raise ValueError("coefficients must match the message count")
    vectors: list[np.ndarray] = []
    for index, (message, coefficient) in enumerate(zip(messages, coefficients)):
        vector = _validate_qvec(message, q, f"message[{index}]")
        coefficient = _validate_coefficient(field, coefficient)
        vectors.append(vector)
    supports: list[list[int]] = []
    combos = 1
    for other in range(dc):
        if other == target:
            continue
        support = [symbol for symbol in range(q) if vectors[other][symbol] > 0.0]
        supports.append(support)
        combos *= len(support)
        if combos > _MAX_SPARSE_COMBOS:
            raise ValueError(
                f"sparse enumeration unboundable: {combos} > {_MAX_SPARSE_COMBOS} combinations")
    conv = np.zeros(q, dtype=np.float64)
    for combo in itertools.product(*supports):
        ssum = 0
        mass = 1.0
        cursor = 0
        for other in range(dc):
            if other == target:
                continue
            symbol = combo[cursor]
            cursor += 1
            mass *= vectors[other][symbol]
            ssum = field.add(ssum, field.mul(int(coefficients[other]), symbol))
        conv[ssum] += mass
    coefficient = int(coefficients[target])
    outgoing = np.empty(q, dtype=np.float64)
    for v in range(q):
        outgoing[v] = conv[field.add(syndrome, field.mul(coefficient, v))]
    normal = _normalise(outgoing)
    if normal is None:
        raise ValueError("sparse check update produced invalid mass")
    return normal


def oracle_variable_update(prior: np.ndarray, check_messages: Sequence[np.ndarray]) -> np.ndarray | None:
    """Pointwise product of the prior with every supplied check message,
    normalized (the variable-node extrinsic/edge or full belief product)."""
    prior_vec = _validate_qvec(prior, len(prior), "prior")
    product = prior_vec.copy()
    for index, message in enumerate(check_messages):
        _validate_qvec(message, product.shape[0], f"check_message[{index}]")
        product *= np.asarray(message, dtype=np.float64)
    return _normalise(product)


def oracle_belief(prior: np.ndarray, check_messages: Sequence[np.ndarray]) -> np.ndarray | None:
    """Belief = prior x all check messages, normalized (identical algebra to
    :func:`oracle_variable_update`; kept as a separately named API because the
    V8 spec freezes both names)."""
    return oracle_variable_update(prior, check_messages)


def _syndrome_of(field: GF2mField, rows: tuple[tuple[int, ...], ...],
                 candidate: tuple[int, ...]) -> tuple[int, ...]:
    """Direct H*candidate by field add/mul (row order preserved)."""
    result: list[int] = []
    for row in rows:
        total = 0
        for coefficient, symbol in zip(row, candidate):
            total = field.add(total, field.mul(coefficient, symbol))
        result.append(total)
    return tuple(result)


def _enumerate_symbols(q: int, n: int) -> itertools.product:
    return itertools.product(range(q), repeat=n)


def _coset_posteriors(field: GF2mField, matrix: Any, syndrome: Any,
                      priors: Sequence[np.ndarray]) -> dict:
    """Exhaustive posterior over the coset {x : H*x == syndrome}."""
    q = field.q
    rows = tuple(tuple(int(v) for v in row) for row in matrix)
    if any(len(row) != len(priors) for row in rows):
        raise ValueError("matrix width does not match the prior count")
    s = tuple(int(v) for v in syndrome)
    if len(s) != len(rows):
        raise ValueError("syndrome length does not match the matrix row count")
    for index, prior in enumerate(priors):
        _validate_qvec(prior, q, f"prior[{index}]")
    n = len(priors)
    if q ** n > _MAX_COSET_VECTORS:
        raise ValueError(f"coset enumeration unboundable: q^n = {q ** n} > {_MAX_COSET_VECTORS}")
    posteriors: dict[tuple[int, ...], float] = {}
    argmax_vector: tuple[int, ...] | None = None
    argmax_posterior = -1.0
    for candidate in _enumerate_symbols(q, n):
        if _syndrome_of(field, rows, candidate) == s:
            mass = 1.0
            for index, symbol in enumerate(candidate):
                mass *= float(priors[index][symbol])
            posteriors[candidate] = mass
            if mass > argmax_posterior:
                argmax_posterior = mass
                argmax_vector = candidate
    coset_total = sum(posteriors.values())
    if not math.isfinite(coset_total) or coset_total <= 0.0:
        raise ValueError("coset posterior has invalid total mass")
    return {
        "map_symbols": argmax_vector,
        "marginals": {vector: mass / coset_total for vector, mass in posteriors.items()},
        "coset_size": len(posteriors),
    }


def bruteforce_coset_map(field: GF2mField, matrix: Any, syndrome: Any,
                         priors: Sequence[np.ndarray]) -> dict:
    """MAP decode under the given symbol priors constrained to H*x == syndrome.

    Returns ``{"map_symbols", "marginals", "coset_size"}`` where ``marginals``
    maps each coset member symbol vector to its normalized posterior over the
    coset.  Bounded to ``q^n <= 4096`` else ``ValueError``.
    """
    field = _validate_field(field)
    return _coset_posteriors(field, matrix, syndrome, list(priors))


def bruteforce_error_map(field: GF2mField, matrix: Any, error_syndrome: Any,
                         error_priors: Sequence[np.ndarray], y: Any) -> dict:
    """Error-domain MAP: decode ``e_hat`` under ``error_priors`` constrained to
    ``H*e == error_syndrome``, then reconstruct ``x_hat = y + e_hat``.

    Returns ``{"e_hat", "x_hat", "coset_size"}`` (``coset_size`` may be 0 when
    the error syndrome has no preimage; ``e_hat``/``x_hat`` are then None).
    """
    field = _validate_field(field)
    q = field.q
    result = _coset_posteriors(field, matrix, error_syndrome, list(error_priors))
    if result["map_symbols"] is None:
        return {"e_hat": None, "x_hat": None, "coset_size": result["coset_size"]}
    e_hat = tuple(int(v) for v in result["map_symbols"])
    y_vec = tuple(int(v) for v in y)
    if len(y_vec) != len(e_hat):
        raise ValueError("y length does not match the error vector length")
    x_hat = tuple(field.add(a, b) for a, b in zip(y_vec, e_hat))
    return {"e_hat": e_hat, "x_hat": x_hat, "coset_size": result["coset_size"]}


def assert_oracle_independent() -> list[str]:
    """Return any forbidden-token violations for this module (empty = ok).

    Scans (a) this module's own source via ``inspect.getsource`` and (b) the
    modules bound in this module's namespace (found through ``sys.modules``),
    for the frozen tokens.  The namespace scan is scoped to modules this
    module actually imported, so unrelated test-process imports of V1-V7
    modules cannot create false positives.
    """
    module = sys.modules[__name__]
    violations: list[str] = []
    source = inspect.getsource(module)
    for token in _FORBIDDEN_TOKENS:
        if token in source:
            violations.append(f"source token {token!r}")
    for value in vars(module).values():
        if isinstance(value, types.ModuleType):
            for token in _FORBIDDEN_TOKENS:
                if token in value.__name__:
                    violations.append(f"bound module {value.__name__}")
    return sorted(set(violations))
