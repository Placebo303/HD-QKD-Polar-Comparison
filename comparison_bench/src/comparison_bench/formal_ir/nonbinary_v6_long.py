"""Bounded n=1024 layered FFT-QSPA decoder for ``nbldpc_formal_v6_long``.

This module owns n=1024 dense-message storage for the two frozen NBLDPC6
codebooks and is deliberately pure and in-memory.  It never receives Alice's
symbol vector: only the public syndrome and Bob's side information enter the
decoder, and a ``syndrome_consistent`` result is deliberately not a
verification claim.

Decoder contract (frozen):

1. form q-ary symmetric priors from Bob symbols and the frozen stratum ``p``;
2. run ascending-row layered FFT-QSPA with lambda=.75 and at most 50 complete
   iterations (workers=1 semantics; deterministic ordering);
3. normalize every message, reject NaN/Inf/negative mass, and fail closed on
   an all-zero normalization constant;
4. check the complete syndrome after every full iteration;
5. stop at syndrome consistency or the iteration cap;
6. verification is never entered here — the development harness invokes the
   locked 64-bit Toeplitz verifier only after consistency.

Message layout: one check-to-variable message per directed edge
``{(row, variable): float64[q]}``; variable-to-check extrinsics are
recomputed from the prior and the stored messages (the accepted v3/v5
pattern), so the dense budget is bounded by the exact edge count (2048).

The check update is the accepted FFT-QSPA convolution (``nonbinary_v3``
semantics) implemented with precomputed field-multiplication permutations so
the q=1024 inner loops are vectorized.  :func:`check_update_fft_qspa` is
field-parameterized and is the exact oracle target for exhaustive GF(4)/GF(8)
posterior enumeration.
"""
from __future__ import annotations

import hashlib
from functools import lru_cache
from numbers import Integral
from typing import Any, Mapping

import numpy as np

from .nonbinary_field import GF2mField
from .nonbinary_qspa import (_declared_dense_bytes, _fwht, _normalise, _result,
                             _symbols, nonbinary_syndrome, qsc_symbol_priors)
from . import nonbinary_v6_codebook as v6_cb

METHOD = "nbldpc_formal_v6_long"
_Q, _N, _MAX_ITER, _LAMBDA = 1024, 1024, 50, 0.75
_CHECK_COUNTS = (320, 480)
_STRATUM_P = {320: 0.20, 480: 0.30}
# The declared dense budget `(2*n + 2*edges) * q * 8` is 50_331_648 bytes at
# n=1024/edges=2048/q=1024; the cap is asserted before any allocation.
_MAX_DENSE_BYTES = 64 * 1024 * 1024


def _q_spec(q: Any) -> int:
    if q != 1024:
        raise ValueError("unsupported GF(q) domain")
    return 1024


def _permutation(field: GF2mField, coefficient: int) -> np.ndarray:
    """Multiplication-by-``coefficient`` permutation over GF(q)."""
    return np.asarray([field.mul(coefficient, s) for s in range(field.q)], dtype=np.intp)


@lru_cache(maxsize=4096)
def _inverse_permutation(q: int, coefficient: int) -> np.ndarray:
    """Multiplication-by-``coefficient^{-1}`` permutation over GF(q).

    The cache key includes the pinned q so GF(4)/GF(8) oracle graphs never
    share permutations with the GF(1024) production path.
    """
    if coefficient < 1:
        raise ValueError("coefficient must be nonzero")
    field = GF2mField.create(q)
    return _permutation(field, field.inverse(coefficient))


@lru_cache(maxsize=4096)
def _forward_permutation(q: int, coefficient: int) -> np.ndarray:
    if coefficient < 1:
        raise ValueError("coefficient must be nonzero")
    return _permutation(GF2mField.create(q), coefficient)


def check_update_fft_qspa(extrinsics: list[np.ndarray], coefficients: list[int],
                          target: int, syndrome: int, field: GF2mField) -> np.ndarray | None:
    """One exact coefficient-aware XOR-domain check update (FFT-QSPA).

    Mathematically identical to the accepted ``nonbinary_v3._check_update_qspa``:
    ``scaled[c*x] = msg[x]`` is realized by the inverse multiplication
    permutation, spectra are Walsh-Hadamard products over the XOR domain, and
    the outgoing message is ``convolved[syndrome ^ c_t*s]`` normalized.
    Returns ``None`` on any invalid mass so callers fail closed.
    """
    q = field.q
    spectra: list[np.ndarray] = []
    for message, coefficient in zip(extrinsics, coefficients):
        scaled = message[_inverse_permutation(q, coefficient)]
        spectra.append(_fwht(scaled))
    product = np.ones(q, dtype=np.float64)
    for index, spectrum in enumerate(spectra):
        if index != target:
            product *= spectrum
    convolved = _fwht(product) / q
    coefficient = coefficients[target]
    outgoing = convolved[np.bitwise_xor(_forward_permutation(q, coefficient), syndrome)]
    return _normalise(outgoing)


def edge_extrinsic(prior: np.ndarray, variable_edges: list[tuple[int, int]],
                   messages: Mapping[tuple[int, int], np.ndarray], current: tuple[int, int]) -> np.ndarray | None:
    """Exact product of the prior and all stored *other* check messages.

    A small helper mirroring ``nonbinary_v3._row_extrinsic`` so the layered
    contract (row r+1 reads a message written by row r) is directly testable.
    """
    value = prior.copy()
    for edge in variable_edges:
        if edge != current:
            value *= messages[edge]
    return _normalise(value)


def _matrix_edges(matrix: Any) -> tuple[list[tuple[tuple[int, int], ...]], list[list[tuple[int, int]]]]:
    checks = [tuple((column, int(value)) for column, value in enumerate(row) if value) for row in matrix]
    variables: list[list[tuple[int, int]]] = [[] for _ in range(_N)]
    for row, row_edges in enumerate(checks):
        for column, _ in row_edges:
            variables[column].append((row, column))
    return checks, variables


def decode_nbldpc_v6_long(bob_symbols: Any, syndrome: Any, manifest: Mapping[str, Any],
                          matrices: Mapping[int, Any], *, check_count: int, p: float,
                          max_iter: int = _MAX_ITER) -> dict[str, Any]:
    """Decode one n=1024 frame using public inputs only.

    ``check_count`` must be 320 (p=.20) or 480 (p=.30); ``p`` must equal the
    frozen stratum of that matrix.  All validation fails closed before any
    verification or allocation.
    """
    q: int | None = None
    try:
        q = _q_spec(manifest.get("q") if isinstance(manifest, Mapping) else None)
    except ValueError:
        return _result("unsupported_domain", reason="manifest q outside NBLDPC6 domain")
    if isinstance(check_count, bool) or not isinstance(check_count, Integral) or int(check_count) not in _CHECK_COUNTS:
        return _result("invalid_input", q=q, check_count=int(check_count) if isinstance(check_count, Integral) else None,
                       reason="unsupported check count")
    check_count = int(check_count)
    if float(p) != _STRATUM_P[check_count]:
        return _result("invalid_input", q=q, check_count=check_count, reason="stratum p mismatch")
    if isinstance(max_iter, bool) or not isinstance(max_iter, Integral):
        return _result("invalid_input", q=q, check_count=check_count, reason="max_iter must be an integer")
    if not 1 <= int(max_iter) <= _MAX_ITER:
        return _result("aborted_resource_limit", q=q, check_count=check_count, reason="max_iter")
    try:
        field = GF2mField.create(q)
        bob = _symbols(bob_symbols, q, expected=_N)
        disclosed = _symbols(syndrome, q, expected=check_count)
        priors = qsc_symbol_priors(bob, q, p)
    except ValueError as exc:
        return _result("invalid_input", q=q, n=_N, check_count=check_count, reason=str(exc))
    verified = v6_cb.verify_nbldpc_v6_codebook(manifest, matrices)
    if verified.get("status") != "ok":
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count,
                       field_id=field.spec.field_id, reason="NBLDPC6 manifest or matrices failed verification")
    try:
        matrix = tuple(tuple(int(value) for value in row) for row in matrices[check_count])
    except (KeyError, TypeError, ValueError):
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id)
    if len(matrix) != check_count or any(len(row) != _N for row in matrix):
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       reason="matrix dimensions")
    checks, variables = _matrix_edges(matrix)
    edge_count = sum(map(len, checks))
    if edge_count != 2 * _N or any(len(row_edges) not in (4, 5, 6, 7) for row_edges in checks):
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       reason="edge topology")
    declared = _declared_dense_bytes(_N, edge_count, q)
    if q > 1024 or declared > _MAX_DENSE_BYTES:
        return _result("aborted_resource_limit", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       declared_dense_message_bytes=declared, reason="dense_message_storage")
    codebook_id = next((entry.get("canonical_sha256") for entry in manifest.get("ordered_entries", [])
                        if entry.get("check_count") == check_count), None)
    if not isinstance(codebook_id, str):
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       declared_dense_message_bytes=declared, reason="missing codebook id")

    messages: dict[tuple[int, int], np.ndarray] = {
        (row, column): np.full(q, 1.0 / q, dtype=np.float64)
        for row, row_edges in enumerate(checks) for column, _ in row_edges}
    belief = [priors[column].copy() for column in range(_N)]
    try:
        for iteration in range(1, int(max_iter) + 1):
            for row, row_edges in enumerate(checks):
                extrinsics: list[np.ndarray] = []
                for column, _ in row_edges:
                    extrinsic = edge_extrinsic(priors[column], variables[column], messages, (row, column))
                    if extrinsic is None:
                        return _result("decoder_error", q=q, n=_N, check_count=check_count, iterations=iteration,
                                       field_id=field.spec.field_id, codebook_id=codebook_id,
                                       declared_dense_message_bytes=declared, reason="extrinsic_normalisation")
                    extrinsics.append(extrinsic)
                coefficients = [coefficient for _, coefficient in row_edges]
                for target, (column, _) in enumerate(row_edges):
                    fresh = check_update_fft_qspa(extrinsics, coefficients, target, disclosed[row], field)
                    if fresh is None:
                        return _result("decoder_error", q=q, n=_N, check_count=check_count, iterations=iteration,
                                       field_id=field.spec.field_id, codebook_id=codebook_id,
                                       declared_dense_message_bytes=declared, reason="check_message_normalisation")
                    updated = _normalise(_LAMBDA * fresh + (1.0 - _LAMBDA) * messages[row, column])
                    if updated is None:
                        return _result("decoder_error", q=q, n=_N, check_count=check_count, iterations=iteration,
                                       field_id=field.spec.field_id, codebook_id=codebook_id,
                                       declared_dense_message_bytes=declared, reason="damping_normalisation")
                    messages[row, column] = updated
                    belief_value = _normalise(extrinsics[target] * updated)
                    if belief_value is None:
                        return _result("decoder_error", q=q, n=_N, check_count=check_count, iterations=iteration,
                                       field_id=field.spec.field_id, codebook_id=codebook_id,
                                       declared_dense_message_bytes=declared, reason="belief_normalisation")
                    belief[column] = belief_value
            decoded = tuple(int(np.argmax(belief[column])) for column in range(_N))
            if nonbinary_syndrome(matrix, decoded, field) == disclosed:
                return _result("syndrome_consistent", q=q, n=_N, check_count=check_count, iterations=iteration,
                               syndrome_consistent=True, field_id=field.spec.field_id, codebook_id=codebook_id,
                               declared_dense_message_bytes=declared, decoded_symbols=decoded)
    except (ArithmeticError, FloatingPointError, KeyError, OverflowError, ValueError):
        return _result("decoder_error", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       codebook_id=codebook_id, declared_dense_message_bytes=declared,
                       reason="numerical_or_field_failure")
    return _result("decode_failed", q=q, n=_N, check_count=check_count, iterations=int(max_iter),
                   field_id=field.spec.field_id, codebook_id=codebook_id,
                   declared_dense_message_bytes=declared, reason="iteration_limit")


def production_runner(bob_symbols: Any, syndrome: Any, manifest: Mapping[str, Any],
                      matrices: Mapping[int, Any], *, check_count: int, p: float) -> dict[str, Any]:
    """Production development-run adapter: the real n=1024 decoder."""
    return decode_nbldpc_v6_long(bob_symbols, syndrome, manifest, matrices,
                                 check_count=check_count, p=p)
