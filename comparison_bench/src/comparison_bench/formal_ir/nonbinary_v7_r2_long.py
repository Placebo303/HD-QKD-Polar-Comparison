"""Bounded n=1024 layered FFT-QSPA decoder for ``nbldpc_formal_v7_r2_qsc_de``.

This module owns the single frozen R2 decoder: ascending-row layered FFT-QSPA
(workers=1 semantics, deterministic ordering), ``max_iter=100``, damping
``lambda=.75``, whole-graph syndrome check after every full iteration,
fail-closed on every numerical or structural contract, and NO fallback.  The
schedule is the fixed choice frozen before any canary (design.md R2: "layered
FFT-QSPA, max_iter=100, fixed schedule selected before any canary").

The check update reuses the ACCEPTED check-update semantics by identity
(``nonbinary_v7_r1a_long.check_update_fft_qspa``, mathematically identical to
the accepted ``nonbinary_v6_long`` / ``nonbinary_v3`` convolution), so the
exhaustive GF(4)/GF(8) oracle tests of that function cover this decoder.

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
recomputed from the prior and the stored messages (accepted v3/v5/v6 pattern),
so the dense budget is bounded by the exact edge count (3072 = 3*1024):

``_declared_dense_bytes(1024, 3072, 1024) = (2*1024 + 2*3072)*1024*8 =
67_108_864`` bytes, below the frozen ``_MAX_DENSE_BYTES = 80 MiB`` cap.
"""
from __future__ import annotations

from functools import lru_cache
from numbers import Integral
from typing import Any, Mapping

import numpy as np

from .nonbinary_field import GF2mField
from .nonbinary_qspa import (_declared_dense_bytes, _normalise, _result,
                             _symbols, nonbinary_syndrome, qsc_symbol_priors)
from . import nonbinary_v7_r1a_long as v7_long
from . import nonbinary_v7_r2_codebook as v7_r2_cb
from . import nonbinary_v7_r2_de as de

METHOD = "nbldpc_formal_v7_r2_qsc_de"
_Q, _N, _MAX_ITER, _LAMBDA = 1024, 1024, 100, 0.75
_CHECK_COUNTS = {0.20: 321, 0.30: 458}
# Frozen primary decoder choice: layered FFT-QSPA is the single R2 schedule
# (selected before any canary).
_SCHEDULE = "layered"
# The declared dense budget `(2*n + 2*edges) * q * 8` is 67_108_864 bytes at
# n=1024/edges=3072/q=1024; the cap is asserted before any allocation.
_MAX_DENSE_BYTES = 80 * 1024 * 1024

# The accepted check-update semantics are reused verbatim (identity, not a
# copy): the same function oracle-tested exhaustively on GF(4)/GF(8).
check_update_fft_qspa = v7_long.check_update_fft_qspa


def _q_spec(q: Any) -> int:
    if q != 1024:
        raise ValueError("unsupported GF(q) domain")
    return 1024


def edge_extrinsic(prior: np.ndarray, variable_edges: list[tuple[int, int]],
                   messages: Mapping[tuple[int, int], np.ndarray], current: tuple[int, int]) -> np.ndarray | None:
    """Exact product of the prior and all stored *other* check messages.

    Mirrors the accepted ``nonbinary_v6_long.edge_extrinsic`` so the layered
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


def decode_nbldpc_v7_r2(bob_symbols: Any, syndrome: Any, manifest: Mapping[str, Any],
                         matrices: Mapping[int, Any], *, check_count: int, p: float,
                         max_iter: int = _MAX_ITER) -> dict[str, Any]:
    """Decode one n=1024 frame using public inputs only.

    ``check_count`` must be 321 (p=.20) or 458 (p=.30); ``p`` must equal the
    frozen stratum of that matrix.  All validation fails closed before any
    verification or allocation; there is no fallback.
    """
    q: int | None = None
    try:
        q = _q_spec(manifest.get("q") if isinstance(manifest, Mapping) else None)
    except ValueError:
        return _result("unsupported_domain", reason="manifest q outside NBLDPC7R2 domain")
    if isinstance(check_count, bool) or not isinstance(check_count, Integral) \
            or int(check_count) not in _CHECK_COUNTS.values():
        return _result("invalid_input", q=q, check_count=int(check_count) if isinstance(check_count, Integral) else None,
                       reason="unsupported check count")
    check_count = int(check_count)
    if float(p) not in _CHECK_COUNTS or _CHECK_COUNTS[float(p)] != check_count:
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
    verified = v7_r2_cb.verify_nbldpc_v7_r2_codebook(manifest, matrices)
    if verified.get("status") != "ok":
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count,
                       field_id=field.spec.field_id, reason="NBLDPC7R2 manifest or matrices failed verification")
    try:
        matrix = tuple(tuple(int(value) for value in row) for row in matrices[check_count])
    except (KeyError, TypeError, ValueError):
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id)
    if len(matrix) != check_count or any(len(row) != _N for row in matrix):
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       reason="matrix dimensions")
    checks, variables = _matrix_edges(matrix)
    edge_count = sum(map(len, checks))
    column_degrees = [len(variables[col]) for col in range(_N)]
    if edge_count != 3 * _N or any(len(row_edges) < 2 or len(row_edges) > de.CHECK_DEGREE_MAX
                                   for row_edges in checks) \
            or any(degree < de.DEGREE_MIN or degree > de.DEGREE_MAX for degree in column_degrees):
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
    """Production development-run adapter: the frozen layered FFT-QSPA."""
    return decode_nbldpc_v7_r2(bob_symbols, syndrome, manifest, matrices,
                               check_count=check_count, p=p)


def declared_dense_bytes() -> int:
    """Exact dense-message budget of the frozen n=1024 / edges=3072 graph."""
    return _declared_dense_bytes(_N, 3 * _N, _Q)
