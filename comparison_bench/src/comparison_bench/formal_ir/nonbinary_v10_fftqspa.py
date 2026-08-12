"""V10 error-domain log-domain FFT-QSPA decoder
(``formal-nonbinary-ldpc-v10-de-peg-fftqspa``, additive layer; frozen
semantics per design section 10).

Scientific contract: the decoder operates on Bob's received ``y`` (or the
per-symbol error prior), the error-domain syndrome ``s_e = s_x + H*y``, the
parity matrix ``H``, the frozen QSC ``p`` and public configuration.  It never
reads Alice truth ``x`` or the real error ``e`` — the public signatures take
no such parameter (tested).

Implementation:

- QSC error prior ``P(e=0)=1-p``, ``P(e=a)=p/(q-1)``;
- log-domain messages (probability floor ``1e-15`` in log domain, i.e. log
  values floored at ``log(1e-15)``);
- variable -> check messages: log-domain product (sum) of the prior log and
  the incoming check logs (excluding the target check);
- GF(q) edge-coefficient permutation: message element ``s`` at edge
  coefficient ``c`` maps to position ``c (x) s`` (field multiplication), done
  in the log domain before the probability-domain FWHT convolution;
- check -> variable messages: coefficient-permuted probability vectors,
  batched XOR-order unnormalized WHT (own implementation, ``/q`` inverse),
  pointwise spectrum product excluding the target edge, syndrome shift
  ``outgoing[s] = conv[syndrome XOR c_t (x) s]``, fail-closed normalization,
  back to log domain with the floor;
- flooding schedule; per-iteration full syndrome check ``H*e_hat == s_e``
  (early success); ``e_hat`` stability over ``streak`` consecutive iterations
  (converged without syndrome); frozen ``max_iter``; fail-closed NaN/Inf
  -> ``decode_failed``; optional RSS guard (watcher provided by the caller);
- exact iteration transcript: per-iteration mean base-q belief entropy,
  syndrome-check result, e_hat stability;
- ``decode_error_domain`` reconstructs ``x_hat = y + e_hat`` and verifies
  ``H*x_hat == s_x``.

Imports: standard library, numpy, ``nonbinary_v10_common`` and the accepted
field tables only.  Never imports any V8 module (V8 is a test-only oracle).
"""
from __future__ import annotations

import math
from numbers import Integral
from typing import Any, Mapping, Sequence

import numpy as np

from . import nonbinary_v10_common as common
from .nonbinary_field import GF2mField

__all__ = [
    "fwht_batched",
    "LOG_FLOOR",
    "check_update_log",
    "syndrome_of",
    "decode_fftqspa",
    "decode_error_domain",
    "STATUS_SUCCESS",
    "STATUS_CONVERGED_NO_SYNDROME",
    "STATUS_MAX_ITER",
    "STATUS_DECODE_FAILED",
    "STATUS_RESOURCE_ABORT",
]

#: Probability floor (log-domain value): log(1e-15).
LOG_FLOOR = math.log(1e-15)
#: Frozen default convergence streak (iterations with identical e_hat).
DEFAULT_STREAK = 3

STATUS_SUCCESS = "success"
STATUS_CONVERGED_NO_SYNDROME = "converged_no_syndrome"
STATUS_MAX_ITER = "max_iter_reached"
STATUS_DECODE_FAILED = "decode_failed"
STATUS_RESOURCE_ABORT = "aborted_resource_limit"

#: Cache of numpy field arithmetic tables keyed by the field id.
_TABLES_CACHE: dict[str, tuple[np.ndarray, np.ndarray]] = {}


def _tables(field: GF2mField) -> tuple[np.ndarray, np.ndarray]:
    """(mul_table, add_table) as uint16 numpy arrays, cached per field id."""
    if not isinstance(field, GF2mField):
        raise ValueError("field must be a pinned GF2mField")
    field_id = field.spec.field_id
    cached = _TABLES_CACHE.get(field_id)
    if cached is not None:
        return cached
    q = field.q
    mul_table = np.zeros((q, q), dtype=np.uint16)
    add_table = np.zeros((q, q), dtype=np.uint16)
    for left in range(q):
        for right in range(q):
            mul_table[left, right] = field.mul(left, right)
            add_table[left, right] = field.add(left, right)
    _TABLES_CACHE[field_id] = (mul_table, add_table)
    return mul_table, add_table


# --------------------------------------------------------------------------- #
# own Walsh-Hadamard transform (XOR order, unnormalized)
# --------------------------------------------------------------------------- #


def fwht_batched(values: Any) -> np.ndarray:
    """Unnormalized XOR-order WHT along the last axis, vectorized over the
    leading axes (own implementation of the accepted butterfly).

    ``q = values.shape[-1]`` must be a power of two >= 2; the result is
    ``WHT(f)`` with ``WHT(WHT(f)) = q * f``.
    """
    out = np.asarray(values, dtype=np.float64)
    if out.ndim < 1:
        raise ValueError("fwht_batched requires at least one axis")
    q = out.shape[-1]
    if q < 2 or q & (q - 1):
        raise ValueError("last axis size must be a power of two >= 2")
    if not np.all(np.isfinite(out)):
        raise ValueError("fwht_batched inputs must be finite")
    out = out.copy()
    width = 1
    while width < q:
        paired = out.reshape(-1, 2 * width)
        left = paired[:, :width].copy()
        right = paired[:, width:].copy()
        paired[:, :width] = left + right
        paired[:, width:] = left - right
        width *= 2
    return out


def _validate_qvec(message: Any, q: int, name: str) -> np.ndarray:
    vector = np.asarray(message, dtype=np.float64)
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


def _content_valid(vector: Any, q: int) -> bool:
    """Fail-closed prior content check (finite, non-negative, positive total,
    normalized within 1e-9)."""
    values = np.asarray(vector, dtype=np.float64)
    if values.shape != (q,):
        return False
    if not np.all(np.isfinite(values)):
        return False
    if np.any(values < 0.0):
        return False
    total = float(values.sum())
    if not math.isfinite(total) or total <= 0.0:
        return False
    return abs(total - 1.0) <= 1e-9


def _validate_coefficient(field: GF2mField, coefficient: Any) -> int:
    field.mul(coefficient, 0)  # raises on non-Integral / out-of-domain
    value = int(coefficient)
    if value == 0:
        raise ValueError("check coefficients must be nonzero")
    return value


def _normalize_qvec_fc(values: np.ndarray, name: str) -> np.ndarray:
    """Fail-closed normalization of a probability vector (floor 1e-15)."""
    if values.ndim != 1:
        raise ValueError(f"{name} must be a 1-D vector")
    if not np.all(np.isfinite(values)):
        raise ValueError(f"{name}: non-finite mass")
    if np.any(values < -1e-12):
        raise ValueError(f"{name}: negative mass")
    floored = np.maximum(values, 1e-15)
    total = float(floored.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError(f"{name}: zero or non-finite total mass")
    return floored / total


def _scale_log_by_coefficient(field: GF2mField, log_message: np.ndarray,
                              coefficient: int) -> np.ndarray:
    """``scaled_log[c (x) s] = log_message[s]`` — coefficient permutation in
    the log domain (exact)."""
    q = field.q
    scaled = np.full(q, LOG_FLOOR, dtype=np.float64)
    mul_table, _ = _tables(field)
    positions = mul_table[coefficient, :]
    scaled[positions] = log_message
    return scaled


# --------------------------------------------------------------------------- #
# check-node update (FFT-QSPA route, log-domain interface)
# --------------------------------------------------------------------------- #


def check_update_log(log_messages: Sequence[Any], coefficients: Sequence[int],
                     target: int, syndrome: int, field: GF2mField) -> np.ndarray:
    """Coefficient-correct check-to-variable update, log-domain interface.

    ``outgoing_log[v]`` is the log of the mass of configurations where
    ``sum_{j != t} c_j (x) x_j = syndrome XOR (c_t (x) v)`` over the
    coefficient-permuted incoming log-message distributions: log-domain
    permutation, exp (with the 1e-15 floor), normalization, batched WHT,
    pointwise spectrum product excluding the target, inverse WHT ``/q``,
    syndrome shift, fail-closed normalization, back to log with the floor.
    Must agree with the independent V8 dense oracle within 1e-9 after
    exp() (tests; V8 is a test-only oracle).
    """
    if not isinstance(field, GF2mField):
        raise ValueError("field must be a pinned GF2mField")
    q = field.q
    dc = len(log_messages)
    if dc < 2:
        raise ValueError("check update requires at least two messages")
    if isinstance(target, bool) or not isinstance(target, Integral) or not 0 <= int(target) < dc:
        raise ValueError("target outside the message range")
    target = int(target)
    syndrome = field.mul(1, syndrome)  # validates the syndrome symbol
    if len(coefficients) != dc:
        raise ValueError("coefficients must match the message count")
    mul_table, add_table = _tables(field)
    scaled: list[np.ndarray] = []
    for index, (message, coefficient) in enumerate(zip(log_messages, coefficients)):
        log_vector = np.asarray(message, dtype=np.float64)
        if log_vector.shape != (q,):
            raise ValueError(f"log_message[{index}] must be a length-{q} vector")
        if not np.all(np.isfinite(log_vector)):
            raise ValueError(f"log_message[{index}] must be finite")
        coefficient = _validate_coefficient(field, coefficient)
        log_scaled = _scale_log_by_coefficient(field, log_vector, coefficient)
        prob = _normalize_qvec_fc(np.exp(log_scaled), f"scaled message[{index}]")
        scaled.append(prob)
    others = [index for index in range(dc) if index != target]
    spectra = fwht_batched(np.stack(scaled))  # (dc, q)
    product = np.prod(spectra[others], axis=0)
    conv = fwht_batched(product) / q
    coefficient = int(coefficients[target])
    outgoing = np.empty(q, dtype=np.float64)
    shifted_positions = add_table[syndrome, mul_table[coefficient, :]]
    for index, symbol in enumerate(shifted_positions):
        outgoing[index] = conv[symbol]
    normalized = _normalize_qvec_fc(outgoing, "check update")
    return np.log(np.maximum(normalized, 1e-15))


# --------------------------------------------------------------------------- #
# syndrome helpers
# --------------------------------------------------------------------------- #


def syndrome_of(field: GF2mField, matrix: Any, vector: Any) -> list[int]:
    """``H * vector`` over GF(q) for a dense (m, n) matrix (numpy-vectorized
    XOR-reduce over each row's nonzero entries)."""
    if not isinstance(field, GF2mField):
        raise ValueError("field must be a pinned GF2mField")
    dense = np.asarray(matrix, dtype=np.int64)
    if dense.ndim != 2:
        raise ValueError("matrix must be 2-D")
    values = np.asarray(vector, dtype=np.int64)
    if values.ndim != 1 or values.shape[0] != dense.shape[1]:
        raise ValueError("vector length must match the matrix width")
    mul_table, add_table = _tables(field)
    m = dense.shape[0]
    out: list[int] = []
    for row_index in range(m):
        row = dense[row_index]
        nonzero = np.nonzero(row)[0]
        if nonzero.size == 0:
            out.append(0)
            continue
        contributions = mul_table[row[nonzero], values[nonzero]]
        acc = 0
        for contribution in contributions:
            acc = add_table[acc, contribution]
        out.append(int(acc))
    return out


# --------------------------------------------------------------------------- #
# flooding FFT-QSPA decoder
# --------------------------------------------------------------------------- #


def _build_edge_lists(matrix: Any, field: GF2mField) -> tuple[list[list[tuple[int, int]]],
                                                              list[list[tuple[int, int]]]]:
    dense = np.asarray(matrix, dtype=np.int64)
    if dense.ndim != 2:
        raise ValueError("matrix must be 2-D")
    m, n = dense.shape
    check_edges: list[list[tuple[int, int]]] = [[] for _ in range(m)]
    var_edges: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for check in range(m):
        row = dense[check]
        nonzero = np.nonzero(row)[0]
        for col in nonzero:
            coefficient = _validate_coefficient(field, int(row[col]))
            check_edges[check].append((int(col), coefficient))
            var_edges[int(col)].append((check, coefficient))
    return check_edges, var_edges


def decode_fftqspa(prior: Any, matrix: Any, error_syndrome: Sequence[int],
                   field: GF2mField, max_iter: int, *, streak: int = DEFAULT_STREAK,
                   rss_watcher: Any = None) -> dict[str, Any]:
    """Error-domain log-domain FFT-QSPA decoder (flooding schedule).

    ``prior`` is either a length-q probability vector (identical QSC prior for
    every variable) or an (n, q) matrix of per-variable priors.  ``matrix`` is
    the dense (m, n) parity matrix over GF(q), ``error_syndrome`` the length-m
    syndrome of the error (``s_e``).  Deterministic — no RNG anywhere; NaN/Inf
    in any message fails closed to ``decode_failed``.  The optional
    ``rss_watcher`` (caller-owned) is polled each iteration via
    ``cap_exceeded`` -> ``aborted_resource_limit``.  Returns status, ``e_hat``,
    iterations used and the exact per-iteration transcript.
    """
    if not isinstance(field, GF2mField):
        raise ValueError("field must be a pinned GF2mField")
    q = field.q
    if isinstance(max_iter, bool) or not isinstance(max_iter, Integral) or int(max_iter) < 1:
        raise ValueError("max_iter must be a positive integer")
    max_iter = int(max_iter)
    if isinstance(streak, bool) or not isinstance(streak, Integral) or int(streak) < 1:
        raise ValueError("streak must be a positive integer")
    streak = int(streak)
    prior_array = np.asarray(prior, dtype=np.float64)
    dense = np.asarray(matrix, dtype=np.int64)
    if dense.ndim != 2:
        raise ValueError("matrix must be 2-D")
    m, n = dense.shape
    if prior_array.shape == (q,):
        per_variable = np.repeat(prior_array[None, :], n, axis=0)
    elif prior_array.shape == (n, q):
        per_variable = prior_array
    else:
        raise ValueError("prior must be a length-q vector or an (n, q) matrix")
    # Fail-closed content validation: a non-finite / invalid prior returns
    # ``decode_failed`` (no recovery attempt), it never raises.
    for row_index in range(n):
        if not _content_valid(per_variable[row_index], q):
            return _failure_result(STATUS_DECODE_FAILED, n, 0, [])
    syndrome = [int(value) for value in error_syndrome]
    if len(syndrome) != m:
        raise ValueError("error_syndrome length must match the matrix row count")
    for value in syndrome:
        field.mul(1, value)  # validates the symbol domain
    check_edges, var_edges = _build_edge_lists(dense, field)
    if not any(check_edges):
        raise ValueError("matrix must have at least one nonzero edge")
    total_edges = sum(len(edges) for edges in check_edges)
    log_prior = np.log(np.maximum(per_variable, 1e-15))  # (n, q)
    v2c = [np.full(q, LOG_FLOOR, dtype=np.float64) for _ in range(total_edges)]
    c2v = [np.full(q, LOG_FLOOR, dtype=np.float64) for _ in range(total_edges)]
    # edge index maps: (check, variable) -> edge id
    edge_index: dict[tuple[int, int], int] = {}
    edge_id = 0
    for check in range(m):
        for variable, _ in check_edges[check]:
            edge_index[(check, variable)] = edge_id
            edge_id += 1
    check_edge_ids = [[] for _ in range(m)]
    var_edge_ids = [[] for _ in range(n)]
    for check in range(m):
        for variable, _ in check_edges[check]:
            check_edge_ids[check].append(edge_index[(check, variable)])
    for variable in range(n):
        for check, _ in var_edges[variable]:
            var_edge_ids[variable].append(edge_index[(check, variable)])

    def fail_closed(value: float) -> bool:
        return not math.isfinite(float(value))

    e_hat = np.zeros(n, dtype=np.int64)
    previous_e_hat = np.zeros(n, dtype=np.int64)
    stability_streak = 0
    status = STATUS_MAX_ITER
    iterations_used = 0
    transcript: list[dict[str, Any]] = []
    for iteration in range(1, max_iter + 1):
        # variable -> check (log-domain product, excluding the target check)
        for check in range(m):
            for edge_pos, edge in enumerate(check_edge_ids[check]):
                variable, coefficient = check_edges[check][edge_pos]
                log_message = log_prior[variable].copy()
                for other_edge in var_edge_ids[variable]:
                    if other_edge == edge:
                        continue
                    log_message += c2v[other_edge]
                if fail_closed(float(log_message.max())):
                    return _failure_result("decode_failed", n, iteration, transcript)
                v2c[edge] = log_message
        # check -> variable (FFT-QSPA)
        for check in range(m):
            incident = check_edges[check]
            dc = len(incident)
            if dc < 2:
                continue  # degree-1 checks contribute nothing (no constraint)
            for edge_pos, edge in enumerate(check_edge_ids[check]):
                coefficient = incident[edge_pos][1]
                outgoing = check_update_log(
                    [v2c[other] for other in check_edge_ids[check]],
                    [incident[pos][1] for pos in range(dc)],
                    edge_pos, syndrome[check], field)
                if fail_closed(float(outgoing.max())):
                    return _failure_result("decode_failed", n, iteration, transcript)
                c2v[edge] = outgoing
        # belief + decision
        for variable in range(n):
            log_belief = log_prior[variable].copy()
            for edge in var_edge_ids[variable]:
                log_belief += c2v[edge]
            if fail_closed(float(log_belief.max())):
                return _failure_result("decode_failed", n, iteration, transcript)
            e_hat[variable] = int(np.argmax(log_belief))
        # observables
        belief_probs = _belief_probabilities(log_prior, c2v, var_edge_ids, n, q)
        mean_entropy = float(np.mean([
            common.entropy_base_q(belief_probs[variable], q) for variable in range(n)]))
        syndrome_ok = syndrome_of(field, dense, e_hat.tolist()) == list(syndrome)
        e_hat_stable = bool(np.array_equal(e_hat, previous_e_hat))
        stability_streak = stability_streak + 1 if e_hat_stable else 0
        transcript.append({
            "iteration": iteration,
            "mean_entropy": mean_entropy,
            "syndrome_ok": syndrome_ok,
            "e_hat_stable": e_hat_stable,
            "e_hat": e_hat.tolist(),
        })
        iterations_used = iteration
        if syndrome_ok:
            status = STATUS_SUCCESS
            break
        if stability_streak >= streak:
            status = STATUS_CONVERGED_NO_SYNDROME
            break
        previous_e_hat = e_hat.copy()
        if rss_watcher is not None and getattr(rss_watcher, "cap_exceeded", False):
            status = STATUS_RESOURCE_ABORT
            break
    final_beliefs = None
    if e_hat is not None:
        final_beliefs = _belief_probabilities(log_prior, c2v, var_edge_ids, n, q)
    return {
        "status": status,
        "e_hat": e_hat.tolist(),
        "beliefs": final_beliefs,
        "iterations": iterations_used,
        "final_mean_entropy": (transcript[-1]["mean_entropy"] if transcript else None),
        "transcript": transcript,
        "q": q, "n": n, "m": m, "max_iter": max_iter, "streak": streak,
    }


def _belief_probabilities(log_prior: np.ndarray, c2v: Sequence[np.ndarray],
                          var_edge_ids: Sequence[Sequence[int]], n: int, q: int) -> np.ndarray:
    out = np.zeros((n, q), dtype=np.float64)
    for variable in range(n):
        log_belief = log_prior[variable].copy()
        for edge in var_edge_ids[variable]:
            log_belief += c2v[edge]
        shifted = log_belief - log_belief.max()
        out[variable] = np.exp(shifted)
        total = float(out[variable].sum())
        if not math.isfinite(total) or total <= 0.0:
            raise ValueError("belief produced invalid mass")
        out[variable] /= total
    return out


def _failure_result(status: str, n: int, iteration: int,
                    transcript: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": status,
        "e_hat": None,
        "iterations": iteration,
        "final_mean_entropy": None,
        "transcript": transcript,
        "note": "fail-closed on non-finite message mass",
    }


# --------------------------------------------------------------------------- #
# error-domain wrapper (syndrome derivation + reconstruction)
# --------------------------------------------------------------------------- #


def decode_error_domain(y: Sequence[int], matrix: Any, s_x: Sequence[int], p: float,
                        field: GF2mField, max_iter: int, *,
                        streak: int = DEFAULT_STREAK, rss_watcher: Any = None) -> dict[str, Any]:
    """Error-domain decode: ``s_e = s_x + H*y``, QSC prior from ``p``,
    :func:`decode_fftqspa`, then ``x_hat = y + e_hat`` and verification
    ``H*x_hat == s_x``.  No Alice truth enters anywhere.  Success requires the
    syndrome identity AND the reconstruction identity."""
    if not isinstance(field, GF2mField):
        raise ValueError("field must be a pinned GF2mField")
    dense = np.asarray(matrix, dtype=np.int64)
    if dense.ndim != 2:
        raise ValueError("matrix must be 2-D")
    m, n = dense.shape
    y_vec = [int(value) for value in y]
    if len(y_vec) != n:
        raise ValueError("y length must match the matrix width")
    for value in y_vec:
        field.mul(1, value)
    s_x_vec = [int(value) for value in s_x]
    if len(s_x_vec) != m:
        raise ValueError("s_x length must match the matrix row count")
    q = field.q
    prior = common.qsc_channel_message(q, p)
    h_y = syndrome_of(field, dense, y_vec)
    mul_add = _tables(field)[1]
    s_e = [int(mul_add[a, b]) for a, b in zip(s_x_vec, h_y)]
    result = decode_fftqspa(prior, dense, s_e, field, max_iter, streak=streak,
                            rss_watcher=rss_watcher)
    if result["e_hat"] is None:
        result["x_hat"] = None
        result["reconstruction_ok"] = False
        result["syndrome_ok"] = False
        return result
    e_hat = np.asarray(result["e_hat"], dtype=np.int64)
    add_table = _tables(field)[1]
    x_hat = [int(add_table[a, b]) for a, b in zip(y_vec, e_hat.tolist())]
    reconstruction_ok = syndrome_of(field, dense, x_hat) == list(s_x_vec)
    result["x_hat"] = x_hat
    result["reconstruction_ok"] = bool(reconstruction_ok)
    result["syndrome_ok"] = bool(result["status"] == STATUS_SUCCESS)
    return result
