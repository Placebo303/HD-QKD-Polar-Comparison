"""Bounded N2 full-message FFT-QSPA feasibility helpers for ``nbldpc_formal_v1``.

This module is deliberately pure and in-memory.  It is not a qualification
runner and it never receives Alice's symbol vector: only the public syndrome
and Bob's side information enter the decoder.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from numbers import Integral
from typing import Any

import numpy as np

from .nonbinary_codebook import verify_nonbinary_codebook_family
from .nonbinary_field import GF2mField, get_field_spec
from .shared import verification_result


_N = 64
_CHECK_COUNTS = (16, 24, 32)
_ROW_WEIGHT = 4
_MAX_ITER = 20
_MAX_DENSE_BYTES = 16 * 1024 * 1024


def _symbols(values: Any, q: int, *, expected: int | None = None) -> tuple[int, ...]:
    try:
        answer = tuple(values)
    except TypeError as exc:
        raise ValueError("symbols must be an iterable") from exc
    if expected is not None and len(answer) != expected:
        raise ValueError("symbols have wrong length")
    if any(isinstance(value, bool) or not isinstance(value, Integral) or not 0 <= int(value) < q for value in answer):
        raise ValueError("symbol outside pinned field domain")
    return tuple(int(value) for value in answer)


def _q(q: Any) -> int:
    try:
        return get_field_spec(q).q
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("unsupported GF(q) domain") from exc


def _exact_bool(value: Any, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a built-in bool")
    return value


def qsc_symbol_priors(bob_symbols: Any, q: int, p: float) -> np.ndarray:
    """Return normalized q-ary-symmetric probabilities in canonical symbol order."""
    q = _q(q)
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) or not 0.0 < float(p) < (q - 1) / q:
        raise ValueError("q-ary symmetric p is outside the frozen open domain")
    bob = _symbols(bob_symbols, q)
    prior = np.full((len(bob), q), float(p) / (q - 1), dtype=np.float64)
    prior[np.arange(len(bob)), np.asarray(bob, dtype=np.intp)] = 1.0 - float(p)
    return prior


def nonbinary_syndrome(matrix: Any, symbols: Any, field: GF2mField) -> tuple[int, ...]:
    """Compute ``H x`` over the pinned field, preserving matrix row order."""
    if not isinstance(field, GF2mField):
        raise ValueError("field must be a pinned GF2mField")
    vector = _symbols(symbols, field.q)
    try:
        rows = tuple(tuple(row) for row in matrix)
    except TypeError as exc:
        raise ValueError("matrix must be rectangular") from exc
    if any(len(row) != len(vector) for row in rows):
        raise ValueError("matrix width does not match symbols")
    result: list[int] = []
    for row in rows:
        total = 0
        for coefficient, symbol in zip(row, vector):
            total = field.add(total, field.mul(coefficient, symbol))
        result.append(total)
    return tuple(result)


def _fwht(values: np.ndarray) -> np.ndarray:
    """Unnormalised XOR-order Walsh-Hadamard transform on a copied vector."""
    out = np.asarray(values, dtype=np.float64).copy()
    width = 1
    while width < out.size:
        paired = out.reshape(-1, 2 * width)
        left, right = paired[:, :width].copy(), paired[:, width:].copy()
        paired[:, :width] = left + right
        paired[:, width:] = left - right
        width *= 2
    return out


def _normalise(values: np.ndarray) -> np.ndarray | None:
    if not np.all(np.isfinite(values)):
        return None
    # Only inverse-transform roundoff may be negative; meaningful negative
    # probabilities are rejected rather than silently repaired.
    if np.any(values < -1e-12):
        return None
    clipped = np.maximum(values, 0.0)
    total = float(clipped.sum())
    if not math.isfinite(total) or total <= 0.0:
        return None
    return clipped / total


def _declared_dense_bytes(n: int, edges: int, q: int) -> int:
    # Priors + posterior beliefs + both directed edge-message families.
    return (2 * n + 2 * edges) * q * np.dtype(np.float64).itemsize


def _result(status: str, *, q: int | None = None, n: int | None = None, check_count: int | None = None,
            iterations: int = 0, syndrome_consistent: bool = False, field_id: str | None = None,
            codebook_id: str | None = None, declared_dense_message_bytes: int = 0,
            reason: str = "", decoded_symbols: tuple[int, ...] | None = None) -> dict[str, Any]:
    return {"status": status, "iterations": iterations, "syndrome_consistent": syndrome_consistent,
            "q": q, "n": n, "check_count": check_count, "field_id": field_id,
            "codebook_id": codebook_id, "declared_dense_message_bytes": declared_dense_message_bytes,
            "reason": reason, "decoded_symbols": decoded_symbols}


def decode_nonbinary_fft_qspa(bob_symbols: Any, syndrome: Any, manifest: Mapping[str, Any], matrices: Mapping[int, Any], *,
                              check_count: int, p: float, max_iter: int = _MAX_ITER) -> dict[str, Any]:
    """Decode a verified N1 coset using deterministic flooding FFT-QSPA.

    A ``syndrome_consistent`` result is deliberately not a verification claim.
    """
    q: int | None = None
    try:
        q = _q(manifest.get("q") if isinstance(manifest, Mapping) else None)
    except ValueError:
        return _result("unsupported_domain", reason="manifest q outside N0 domain")
    if isinstance(check_count, bool) or not isinstance(check_count, Integral) or int(check_count) not in _CHECK_COUNTS:
        return _result("invalid_input", q=q, check_count=int(check_count) if isinstance(check_count, Integral) else None, reason="unsupported N1 check count")
    check_count = int(check_count)
    if isinstance(max_iter, bool) or not isinstance(max_iter, Integral):
        return _result("invalid_input", q=q, check_count=check_count, reason="max_iter must be an integer")
    if not 1 <= int(max_iter) <= _MAX_ITER:
        return _result("aborted_resource_limit", q=q, check_count=check_count, reason="max_iter")
    try:
        field = GF2mField(get_field_spec(q))
        bob = _symbols(bob_symbols, q, expected=_N)
        disclosed = _symbols(syndrome, q, expected=check_count)
        priors = qsc_symbol_priors(bob, q, p)
    except ValueError as exc:
        return _result("invalid_input", q=q, n=_N, check_count=check_count, reason=str(exc))
    verified = verify_nonbinary_codebook_family(manifest, matrices)
    if verified.get("status") != "ok":
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       reason="N1 manifest or matrices failed verification")
    try:
        matrix = tuple(tuple(int(value) for value in row) for row in matrices[check_count])
    except (KeyError, TypeError, ValueError):
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id)
    if len(matrix) != check_count or any(len(row) != _N for row in matrix):
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id, reason="matrix dimensions")
    checks = [tuple((column, value) for column, value in enumerate(row) if value) for row in matrix]
    if any(len(edges) != _ROW_WEIGHT for edges in checks):
        return _result("aborted_resource_limit", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id, reason="row_weight")
    edge_count = check_count * _ROW_WEIGHT
    declared = _declared_dense_bytes(_N, edge_count, q)
    if q > 1024 or declared > _MAX_DENSE_BYTES:
        return _result("aborted_resource_limit", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       declared_dense_message_bytes=declared, reason="dense_message_storage")
    codebook_id = next((entry.get("codebook_id") for entry in manifest.get("ordered_entries", [])
                        if entry.get("check_count") == check_count), None)
    if not isinstance(codebook_id, str):
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       declared_dense_message_bytes=declared, reason="missing codebook id")

    edge_keys = [(row, column, coefficient) for row, row_edges in enumerate(checks) for column, coefficient in row_edges]
    v_to_c = {(row, column): priors[column].copy() for row, column, _ in edge_keys}
    c_to_v = {(row, column): np.full(q, 1.0 / q, dtype=np.float64) for row, column, _ in edge_keys}
    variable_edges: list[list[tuple[int, int]]] = [[] for _ in range(_N)]
    for row, column, _ in edge_keys:
        variable_edges[column].append((row, column))

    try:
        for iteration in range(1, int(max_iter) + 1):
            next_c_to_v: dict[tuple[int, int], np.ndarray] = {}
            for row, row_edges in enumerate(checks):
                transformed: list[np.ndarray] = []
                for column, coefficient in row_edges:
                    scaled = np.empty(q, dtype=np.float64)
                    for symbol in range(q):
                        scaled[field.mul(coefficient, symbol)] = v_to_c[(row, column)][symbol]
                    transformed.append(_fwht(scaled))
                for target, (column, coefficient) in enumerate(row_edges):
                    product = np.ones(q, dtype=np.float64)
                    for other, spectrum in enumerate(transformed):
                        if other != target:
                            product *= spectrum
                    convolved = _fwht(product) / q
                    outgoing = np.empty(q, dtype=np.float64)
                    for symbol in range(q):
                        outgoing[symbol] = convolved[disclosed[row] ^ field.mul(coefficient, symbol)]
                    normal = _normalise(outgoing)
                    if normal is None:
                        return _result("decoder_error", q=q, n=_N, check_count=check_count, iterations=iteration,
                                       field_id=field.spec.field_id, codebook_id=codebook_id,
                                       declared_dense_message_bytes=declared, reason="check_message_normalisation")
                    next_c_to_v[(row, column)] = normal
            c_to_v = next_c_to_v
            beliefs = np.empty((_N, q), dtype=np.float64)
            for column in range(_N):
                belief = priors[column].copy()
                for edge in variable_edges[column]:
                    belief *= c_to_v[edge]
                normal = _normalise(belief)
                if normal is None:
                    return _result("decoder_error", q=q, n=_N, check_count=check_count, iterations=iteration,
                                   field_id=field.spec.field_id, codebook_id=codebook_id,
                                   declared_dense_message_bytes=declared, reason="belief_normalisation")
                beliefs[column] = normal
            decoded = tuple(int(np.argmax(beliefs[column])) for column in range(_N))
            consistent = nonbinary_syndrome(matrix, decoded, field) == disclosed
            if consistent:
                return _result("syndrome_consistent", q=q, n=_N, check_count=check_count, iterations=iteration,
                               syndrome_consistent=True, field_id=field.spec.field_id, codebook_id=codebook_id,
                               declared_dense_message_bytes=declared, decoded_symbols=decoded)
            next_v_to_c: dict[tuple[int, int], np.ndarray] = {}
            for row, column, _ in edge_keys:
                message = priors[column].copy()
                for other in variable_edges[column]:
                    if other != (row, column):
                        message *= c_to_v[other]
                normal = _normalise(message)
                if normal is None:
                    return _result("decoder_error", q=q, n=_N, check_count=check_count, iterations=iteration,
                                   field_id=field.spec.field_id, codebook_id=codebook_id,
                                   declared_dense_message_bytes=declared, reason="variable_message_normalisation")
                next_v_to_c[(row, column)] = normal
            v_to_c = next_v_to_c
    except (ArithmeticError, FloatingPointError, OverflowError, ValueError):
        return _result("decoder_error", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       codebook_id=codebook_id, declared_dense_message_bytes=declared, reason="numerical_or_field_failure")
    return _result("decode_failed", q=q, n=_N, check_count=check_count, iterations=int(max_iter),
                   field_id=field.spec.field_id, codebook_id=codebook_id,
                   declared_dense_message_bytes=declared, reason="iteration_limit")


def symbols_to_msb_bits(symbols: Any, q: int) -> np.ndarray:
    """Map polynomial-basis symbol integers to fixed-width MSB-first bits."""
    q = _q(q)
    values = _symbols(symbols, q)
    width = q.bit_length() - 1
    return np.asarray([bit for value in values for bit in range(width - 1, -1, -1) for bit in ((value >> bit) & 1,)], dtype=np.uint8)


def nonbinary_disclosure_accounting(check_count: int, q: int, *, verification_invoked: bool,
                                    verification_tag_bits: int = 64, public_control_bits: int = 0) -> dict[str, int]:
    """Return exact, separate syndrome/tag and public-control disclosure counters."""
    q = _q(q)
    verification_invoked = _exact_bool(verification_invoked, "verification_invoked")
    if isinstance(check_count, bool) or not isinstance(check_count, Integral) or int(check_count) < 0:
        raise ValueError("check_count must be a non-negative integer")
    for name, value in (("verification_tag_bits", verification_tag_bits), ("public_control_bits", public_control_bits)):
        if isinstance(value, bool) or not isinstance(value, Integral) or int(value) < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    syndrome_bits = int(check_count) * (q.bit_length() - 1)
    tag_bits = int(verification_tag_bits) if verification_invoked else 0
    return {"syndrome_disclosure_bits": syndrome_bits, "verification_tag_bits": tag_bits,
            "key_dependent_disclosure_bits_total": syndrome_bits + tag_bits,
            "public_control_bits": int(public_control_bits)}


def verify_nonbinary_symbols(alice_symbols: Any, bob_symbols: Any, q: int, locked_seed: Mapping[str, Any], *, invoked: bool) -> dict[str, Any]:
    """Invoke the locked Toeplitz verifier after the common MSB-first mapping."""
    invoked = _exact_bool(invoked, "invoked")
    q = _q(q)
    alice, bob = _symbols(alice_symbols, q), _symbols(bob_symbols, q)
    if len(alice) != len(bob):
        raise ValueError("verification symbol vectors must have equal length")
    return verification_result(symbols_to_msb_bits(alice, q), symbols_to_msb_bits(bob, q), locked_seed, invoked=invoked)
