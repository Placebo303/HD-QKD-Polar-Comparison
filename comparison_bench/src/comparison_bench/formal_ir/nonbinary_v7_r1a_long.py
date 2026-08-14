"""Bounded n=256 FFT-QSPA decoders for ``nbldpc_formal_v7_r1a_mr0``.

This module owns the two deterministic decoders of the frozen R1A mother:

- **flooding FFT-QSPA** — the literature-reference schedule and the *primary*
  decoder (``production_runner``); all check messages of an iteration are
  computed from the previous iteration's variable messages, then all variable
  messages are recomputed (the accepted ``nonbinary_qspa`` flooding semantics).
- **layered FFT-QSPA** — a frozen same-code *diagnostic*; ascending-row
  in-place updates so row ``r+1`` reads a message written by row ``r`` (the
  accepted ``nonbinary_v3``/``nonbinary_v6_long`` semantics).

Both decoders are deterministic (workers=1 by construction) with
``max_iter=100`` and damping ``lambda=.75`` (layered only; flooding is
undamped, matching the literature-reference schedule).  The complete
syndrome is checked after every full iteration; the first consistent
iteration stops the decoder.

The module is deliberately pure and in-memory.  It never receives Alice's
symbol vector: only the public syndrome and Bob's side information enter the
decoder, and a ``syndrome_consistent`` result is deliberately not a
verification claim.  Fail-closed contracts (frozen):

- NaN/Inf/negative-mass messages are rejected by normalization;
- wrong symbol/syndrome lengths, malformed syndromes and out-of-domain
  symbols raise ``invalid_input``;
- an allocation breach aborts with ``aborted_resource_limit`` before any
  dense-message allocation;
- no fallback: an invalid result is never silently replaced by another
  schedule or by a lower-cost decoder.

Message layout: one check-to-variable message per directed edge
``{(row, variable): float64[q]}``; variable-to-check extrinsics are
recomputed from the prior and the stored messages (accepted v3/v5/v6
pattern), so the dense budget is bounded by the exact edge count (512):

``_declared_dense_bytes(256, 512, 1024) = (2*256 + 2*512)*1024*8 =
12_582_912`` bytes, below the frozen ``_MAX_DENSE_BYTES = 16 MiB`` cap.

The check update is the accepted FFT-QSPA convolution (``nonbinary_v3``
semantics) implemented with precomputed field-multiplication permutations;
:func:`check_update_fft_qspa` is field-parameterized and is the exact oracle
target for exhaustive GF(4)/GF(8) posterior enumeration (identical to the
accepted ``nonbinary_v6_long.check_update_fft_qspa``).
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
from . import nonbinary_v7_r1a_codebook as v7_cb

METHOD = "nbldpc_formal_v7_r1a_mr0"
_Q, _N, _M, _MAX_ITER, _LAMBDA = 1024, 256, 170, 100, 0.75
_SCHEDULES = ("flooding", "layered")
# Frozen primary decoder choice: flooding FFT-QSPA is the literature-reference
# schedule; layered FFT-QSPA is the frozen same-code diagnostic.
_PRIMARY_SCHEDULE = "flooding"
# The declared dense budget `(2*n + 2*edges) * q * 8` is 12_582_912 bytes at
# n=256/edges=512/q=1024; the cap is asserted before any allocation.
_MAX_DENSE_BYTES = 16 * 1024 * 1024


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

    Mathematically identical to the accepted ``nonbinary_v3._check_update_qspa``
    and ``nonbinary_v6_long.check_update_fft_qspa``: ``scaled[c*x] = msg[x]``
    is realized by the inverse multiplication permutation, spectra are
    Walsh-Hadamard products over the XOR domain, and the outgoing message is
    ``convolved[syndrome ^ c_t*s]`` normalized.  Returns ``None`` on any
    invalid mass so callers fail closed.
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

    A small helper mirroring ``nonbinary_v3._row_extrinsic`` /
    ``nonbinary_v6_long.edge_extrinsic`` so the layered contract (row r+1
    reads a message written by row r) is directly testable.
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


def decode_nbldpc_v7_r1a(bob_symbols: Any, syndrome: Any, manifest: Mapping[str, Any],
                          matrices: Any, *, check_count: int, p: float,
                          schedule: str = _PRIMARY_SCHEDULE, max_iter: int = _MAX_ITER) -> dict[str, Any]:
    """Decode one n=256 frame using public inputs only.

    ``check_count`` must be 170 and ``p`` one of the two frozen strata (.20 /
    .30).  ``schedule`` is ``"flooding"`` (primary) or ``"layered"`` (frozen
    same-code diagnostic).  All validation fails closed before any
    verification or allocation; there is no fallback between schedules.
    """
    q: int | None = None
    try:
        q = _q_spec(manifest.get("q") if isinstance(manifest, Mapping) else None)
    except ValueError:
        return _result("unsupported_domain", reason="manifest q outside NBLDPC7 domain")
    if isinstance(check_count, bool) or not isinstance(check_count, Integral) or int(check_count) != _M:
        return _result("invalid_input", q=q, check_count=int(check_count) if isinstance(check_count, Integral) else None,
                       reason="unsupported check count")
    check_count = int(check_count)
    if float(p) not in (0.20, 0.30):
        return _result("invalid_input", q=q, check_count=check_count, reason="stratum p mismatch")
    if schedule not in _SCHEDULES:
        return _result("invalid_input", q=q, check_count=check_count, reason="unsupported schedule")
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
    verified = v7_cb.verify_nbldpc_v7_r1a_codebook(manifest, matrices)
    if verified.get("status") != "ok":
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count,
                       field_id=field.spec.field_id, reason="NBLDPC7 manifest or matrix failed verification")
    try:
        matrix = tuple(tuple(int(value) for value in row) for row in matrices)
    except (KeyError, TypeError, ValueError):
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id)
    if len(matrix) != check_count or any(len(row) != _N for row in matrix):
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       reason="matrix dimensions")
    checks, variables = _matrix_edges(matrix)
    edge_count = sum(map(len, checks))
    if edge_count != 2 * _N or any(len(row_edges) not in (3, 4) for row_edges in checks):
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       reason="edge topology")
    declared = _declared_dense_bytes(_N, edge_count, q)
    if q > 1024 or declared > _MAX_DENSE_BYTES:
        return _result("aborted_resource_limit", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       declared_dense_message_bytes=declared, reason="dense_message_storage")
    codebook_id = manifest.get("canonical_sha256")
    if not isinstance(codebook_id, str):
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       declared_dense_message_bytes=declared, reason="missing codebook id")
    if schedule == "flooding":
        return _decode_flooding(bob, disclosed, matrix, checks, variables, priors, field,
                                check_count, codebook_id, declared, max_iter=int(max_iter))
    return _decode_layered(bob, disclosed, matrix, checks, variables, priors, field,
                           check_count, codebook_id, declared, max_iter=int(max_iter))


def _decode_flooding(bob, disclosed, matrix, checks, variables, priors, field,
                     check_count, codebook_id, declared, *, max_iter):
    """Literature-reference flooding FFT-QSPA (primary schedule).

    All check messages of iteration ``i`` are computed from the variable
    messages of iteration ``i-1``; all variable messages are then recomputed
    from the fresh check messages; damping is not applied (undamped flooding,
    matching the accepted ``nonbinary_qspa`` reference schedule).
    """
    q = field.q
    edge_keys = [(row, column, coefficient) for row, row_edges in enumerate(checks)
                 for column, coefficient in row_edges]
    v_to_c = {(row, column): priors[column].copy() for row, column, _ in edge_keys}
    c_to_v = {(row, column): np.full(q, 1.0 / q, dtype=np.float64) for row, column, _ in edge_keys}
    try:
        for iteration in range(1, int(max_iter) + 1):
            next_c_to_v: dict[tuple[int, int], np.ndarray] = {}
            for row, row_edges in enumerate(checks):
                spectra: list[np.ndarray] = []
                for column, coefficient in row_edges:
                    scaled = v_to_c[(row, column)][_inverse_permutation(q, coefficient)]
                    spectra.append(_fwht(scaled))
                for target, (column, coefficient) in enumerate(row_edges):
                    product = np.ones(q, dtype=np.float64)
                    for other, spectrum in enumerate(spectra):
                        if other != target:
                            product *= spectrum
                    convolved = _fwht(product) / q
                    outgoing = convolved[np.bitwise_xor(_forward_permutation(q, coefficient), disclosed[row])]
                    normal = _normalise(outgoing)
                    if normal is None:
                        return _result("decoder_error", q=q, n=_N, check_count=check_count, iterations=iteration,
                                       field_id=field.spec.field_id, codebook_id=codebook_id,
                                       declared_dense_message_bytes=declared, reason="check_message_normalisation")
                    next_c_to_v[(row, column)] = normal
            c_to_v = next_c_to_v
            beliefs: list[np.ndarray] = []
            for column in range(_N):
                belief = priors[column].copy()
                for edge in variables[column]:
                    belief *= c_to_v[edge]
                normal = _normalise(belief)
                if normal is None:
                    return _result("decoder_error", q=q, n=_N, check_count=check_count, iterations=iteration,
                                   field_id=field.spec.field_id, codebook_id=codebook_id,
                                   declared_dense_message_bytes=declared, reason="belief_normalisation")
                beliefs.append(normal)
            decoded = tuple(int(np.argmax(beliefs[column])) for column in range(_N))
            if nonbinary_syndrome(matrix, decoded, field) == disclosed:
                return _result("syndrome_consistent", q=q, n=_N, check_count=check_count, iterations=iteration,
                               syndrome_consistent=True, field_id=field.spec.field_id, codebook_id=codebook_id,
                               declared_dense_message_bytes=declared, decoded_symbols=decoded)
            next_v_to_c: dict[tuple[int, int], np.ndarray] = {}
            for row, column, _ in edge_keys:
                message = priors[column].copy()
                for other in variables[column]:
                    if other != (row, column):
                        message *= c_to_v[other]
                normal = _normalise(message)
                if normal is None:
                    return _result("decoder_error", q=q, n=_N, check_count=check_count, iterations=iteration,
                                   field_id=field.spec.field_id, codebook_id=codebook_id,
                                   declared_dense_message_bytes=declared, reason="variable_message_normalisation")
                next_v_to_c[(row, column)] = normal
            v_to_c = next_v_to_c
    except (ArithmeticError, FloatingPointError, KeyError, OverflowError, ValueError):
        return _result("decoder_error", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       codebook_id=codebook_id, declared_dense_message_bytes=declared,
                       reason="numerical_or_field_failure")
    return _result("decode_failed", q=q, n=_N, check_count=check_count, iterations=int(max_iter),
                   field_id=field.spec.field_id, codebook_id=codebook_id,
                   declared_dense_message_bytes=declared, reason="iteration_limit")


def _decode_layered(bob, disclosed, matrix, checks, variables, priors, field,
                    check_count, codebook_id, declared, *, max_iter):
    """Frozen same-code diagnostic: ascending-row layered FFT-QSPA."""
    q = field.q
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
                      matrices: Any, *, check_count: int, p: float) -> dict[str, Any]:
    """Production development-run adapter: the primary flooding decoder."""
    return decode_nbldpc_v7_r1a(bob_symbols, syndrome, manifest, matrices,
                                check_count=check_count, p=p, schedule=_PRIMARY_SCHEDULE)
