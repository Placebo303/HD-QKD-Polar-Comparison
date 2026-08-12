"""NBLDPC7 R3: bounded two-layer GF(32) EMS decoder for
``nbldpc_formal_v7_r3_gf32x2``.

The module owns the single frozen R3 production decoder: layer 0 (high 5-bit
words) is decoded FIRST by EMS with the frozen ``nm=32`` (which equals the
GF(32) alphabet, so the extended-min-sum check/variable operations are the
exact full min-sum; no truncation), then -- only if layer 0 is
syndrome-consistent -- layer 1 (low 5-bit words) is decoded with priors
restricted to Bob data, public model data and the verified layer-0 output
(``conditional_layer1_priors``, the exact QSC-consistent conditional prior;
see its docstring for the derivation).  A frame is successful only when BOTH
layers are syndrome-consistent; the reconstructed 10-bit symbols are then
returned for the single 64-bit Toeplitz tag in the harness.  A failed layer 0
short-circuits: layer 1 is not invoked and no verification happens.

The exact FFT-QSPA decoder (``decode_nbldpc_v7_r3_fft_qspa``) is the
small-field sum-product ORACLE (reusing the ACCEPTED check-update semantics by
identity, ``nonbinary_v7_r1a_long.check_update_fft_qspa``); it is test-only
and is NEVER a production fallback.  Production uses only the frozen EMS
schedule (``_SCHEDULE = "flooding"``, damped min-sum with ``lambda=.75``, workers=1 by
construction, ``max_iter=100``).

Fail-closed contracts (frozen):

- NaN/Inf/non-finite costs are rejected (``decoder_error``) and every message
  is clipped to the frozen ``_COST_CLIP = 100.0`` bound before use;
- wrong symbol/syndrome lengths, out-of-domain symbols, wrong strata/check
  counts and malformed manifests fail closed (``invalid_input`` /
  ``unsupported_domain`` / ``codebook_invalid``);
- an allocation breach aborts with ``aborted_resource_limit`` before any
  dense-message allocation;
- no fallback: an invalid result is never silently replaced by another
  schedule or by the oracle decoder.

Message layout: one length-32 cost vector per directed edge per layer
(``{(row, variable): float64[32]}``); the two-layer dense budget is exactly
``2 * (2*n + 2*edges) * 32 * 8`` with edges = 3*1024 per layer:
``2 * (2*1024 + 2*3072) * 32 * 8 = 4_194_304`` bytes, below the frozen
``_MAX_DENSE_BYTES = 8 MiB`` cap.  The public signature contains no Alice
truth or callback.
"""
from __future__ import annotations

from functools import lru_cache
from numbers import Integral
from typing import Any, Mapping

import numpy as np

from .nonbinary_field import GF2mField
from .nonbinary_qspa import (_declared_dense_bytes, _normalise, _result, _symbols,
                             nonbinary_syndrome, qsc_symbol_priors)
from . import nonbinary_v7_r1a_long as v7_long
from . import nonbinary_v7_r3_codebook as v7_r3_cb

METHOD = "nbldpc_formal_v7_r3_gf32x2"
_Q, _N, _MAX_ITER, _NM = 32, 1024, 100, 32
_CHECK_COUNTS = {0.20: 404, 0.30: 558}
# Frozen primary decoder choice: flooding damped EMS with nm=32 (= q, so the
# EMS operations are the exact full min-sum); the FFT-QSPA decoder is the
# small-field oracle only.  Damping lambda=.75 (the frozen R1A/R2 value)
# stabilizes the min-sum fixed point (undamped flooding oscillates between
# near-codeword states on this graph).
_SCHEDULE = "flooding"
_LAMBDA = 0.75
# Two layers of the same n=1024 / edges=3072 graph: the declared budget is
# 2 * (2*n + 2*edges) * q * 8 = 4_194_304 bytes <= 8 MiB.
_MAX_DENSE_BYTES = 8 * 1024 * 1024
# Frozen fail-closed cost bound: no message entry may exceed it; it is far
# above any achievable path cost for the frozen QSC/conditional priors, so it
# never changes an argmin while guaranteeing finiteness.
_COST_CLIP = 100.0

# The accepted check-update semantics are reused verbatim (identity, not a
# copy): the small-field FFT-QSPA oracle at q=32 uses exactly this function.
check_update_fft_qspa = v7_long.check_update_fft_qspa


def _q_spec(q: Any) -> int:
    if q != 32:
        raise ValueError("unsupported GF(q) domain")
    return 32


@lru_cache(maxsize=4096)
def _inverse_permutation(q: int, coefficient: int) -> np.ndarray:
    """Multiplication-by-``coefficient^{-1}`` permutation over GF(q)."""
    if coefficient < 1:
        raise ValueError("coefficient must be nonzero")
    field = GF2mField.create(q)
    return np.asarray([field.mul(field.inverse(coefficient), s) for s in range(q)], dtype=np.intp)


@lru_cache(maxsize=4096)
def _forward_permutation(q: int, coefficient: int) -> np.ndarray:
    if coefficient < 1:
        raise ValueError("coefficient must be nonzero")
    field = GF2mField.create(q)
    return np.asarray([field.mul(coefficient, s) for s in range(q)], dtype=np.intp)


@lru_cache(maxsize=1)
def _xor_tables() -> tuple[np.ndarray, np.ndarray]:
    """``U[t, v] = t ^ v`` and ``V[t, v] = v`` for t, v in [0, q): the index
    tables turn the pairwise min-plus XOR convolution into two vectorized
    numpy operations."""
    q = _Q
    return (np.asarray([[t ^ v for v in range(q)] for t in range(q)], dtype=np.intp),
            np.asarray([[v for v in range(q)] for t in range(q)], dtype=np.intp))


def min_plus_convolution(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Exact pairwise min-plus XOR convolution ``(a o b)[t] = min_u a[u] +
    b[t ^ u]`` over GF(32).  Exposed so the T1 oracle tests can verify it
    against brute-force enumeration."""
    table = left[:, None] + right[None, :]
    U, V = _xor_tables()
    return table[U, V].min(axis=1)


def _costs(priors: np.ndarray) -> np.ndarray:
    """Deterministic cost conversion ``-log(p)`` with zeros mapped to the
    frozen clip bound (the conditional layer-1 prior contains exact zeros)."""
    positive = np.maximum(priors, np.finfo(np.float64).tiny)
    costs = np.where(priors > 0.0, -np.log(positive), _COST_CLIP)
    return np.minimum(costs, _COST_CLIP)


def _layer_result(status: str, **kwargs: Any) -> dict[str, Any]:
    """``_result`` plus the frozen per-layer provenance keys.  The layer keys
    are informational booleans the harness uses for the short-circuit /
    conditional-prior events; they never carry symbols."""
    result = _result(status, **{key: value for key, value in kwargs.items()
                                if key not in ("layer0_consistent", "layer1_consistent", "layer1_invoked")})
    for key in ("layer0_consistent", "layer1_consistent", "layer1_invoked"):
        if key in kwargs:
            result[key] = kwargs[key]
    return result


def check_update_min_sum(extrinsics: list[np.ndarray], coefficients: list[int],
                         syndrome: int, field: GF2mField) -> list[np.ndarray] | None:
    """Exact min-sum check update for one GF(q) check (EMS with nm=q).

    ``scaled_w(z) = m_w(h_w^{-1} z)``; the others' configuration cost is the
    min-plus XOR convolution of the scaled messages; the outgoing message to
    target ``v`` is ``conv_others[syndrome ^ h_v * x]``.  Returns ``None`` on
    any non-finite mass so callers fail closed.  The q=32 index tables are
    pinned to the production alphabet.
    """
    q = field.q
    if q != _Q:
        raise ValueError("min-sum check update is pinned to GF(32)")
    scaled = [message[_inverse_permutation(q, int(coefficient))]
              for message, coefficient in zip(extrinsics, coefficients)]
    degree = len(scaled)
    if degree < 1:
        raise ValueError("empty check update")
    if any(not np.all(np.isfinite(message)) for message in scaled):
        return None
    if degree == 1:
        others = [np.full(q, _COST_CLIP, dtype=np.float64)]
        others[0][0] = 0.0
    else:
        forward = [scaled[0]]
        for index in range(1, degree):
            forward.append(min_plus_convolution(forward[-1], scaled[index]))
        backward: list[np.ndarray | None] = [None] * degree
        backward[-1] = scaled[-1]
        for index in range(degree - 2, -1, -1):
            backward[index] = min_plus_convolution(scaled[index], backward[index + 1])
        others = []
        for target in range(degree):
            if target == 0:
                others.append(backward[1])  # type: ignore[arg-type]
            elif target == degree - 1:
                others.append(forward[degree - 2])
            else:
                others.append(min_plus_convolution(forward[target - 1], backward[target + 1]))  # type: ignore[arg-type]
    outgoing: list[np.ndarray] = []
    for target, coefficient in enumerate(coefficients):
        permutation = _forward_permutation(q, int(coefficient))
        message = np.asarray([others[target][syndrome ^ int(index)] for index in permutation],
                             dtype=np.float64)
        if not np.all(np.isfinite(message)):
            return None
        normalised = message - float(message.min())
        outgoing.append(np.minimum(normalised, _COST_CLIP))
    return outgoing


def _matrix_edges(matrix: Any) -> tuple[list[tuple[tuple[int, int], ...]], list[list[tuple[int, int]]]]:
    checks = [tuple((column, int(value)) for column, value in enumerate(row) if value) for row in matrix]
    variables: list[list[tuple[int, int]]] = [[] for _ in range(_N)]
    for row, row_edges in enumerate(checks):
        for column, _ in row_edges:
            variables[column].append((row, column))
    return checks, variables


def _decode_layer_min_sum(words: Any, syndrome: Any, matrix: Any, field: GF2mField,
                          priors: np.ndarray, max_iter: int) -> dict[str, Any]:
    """Flooding damped EMS (nm=32 = q) over one GF(32) layer; returns
    ``{"status", "decoded", "iterations"}`` with a syndrome check after every
    full iteration.  Fail-closed on any non-finite message."""
    checks, variables = _matrix_edges(matrix)
    edge_keys = [(row, column) for row, row_edges in enumerate(checks) for column, _ in row_edges]
    prior_cost = _costs(priors)
    c_to_v: dict[tuple[int, int], np.ndarray] = {
        edge: np.zeros(_Q, dtype=np.float64) for edge in edge_keys}
    try:
        for iteration in range(1, int(max_iter) + 1):
            v_to_c: dict[tuple[int, int], np.ndarray] = {}
            for edge in edge_keys:
                value = prior_cost[edge[1]].copy()
                for other in variables[edge[1]]:
                    if other != edge:
                        value += c_to_v[other]
                if not np.all(np.isfinite(value)):
                    return {"status": "decoder_error", "decoded": None, "iterations": iteration}
                v_to_c[edge] = np.minimum(value, _COST_CLIP)
            next_c_to_v: dict[tuple[int, int], np.ndarray] = {}
            for row, row_edges in enumerate(checks):
                updates = check_update_min_sum([v_to_c[(row, column)] for column, _ in row_edges],
                                               [coefficient for _, coefficient in row_edges],
                                               int(syndrome[row]), field)
                if updates is None:
                    return {"status": "decoder_error", "decoded": None, "iterations": iteration}
                for target, (column, _) in enumerate(row_edges):
                    fresh = updates[target]
                    if not np.all(np.isfinite(fresh)):
                        return {"status": "decoder_error", "decoded": None, "iterations": iteration}
                    next_c_to_v[(row, column)] = _LAMBDA * fresh + (1.0 - _LAMBDA) * c_to_v[(row, column)]
            c_to_v = next_c_to_v
            decoded: list[int] = []
            for column in range(_N):
                belief = prior_cost[column].copy()
                for edge in variables[column]:
                    belief += c_to_v[edge]
                if not np.all(np.isfinite(belief)):
                    return {"status": "decoder_error", "decoded": None, "iterations": iteration}
                decoded.append(int(np.argmin(belief)))
            decoded_tuple = tuple(decoded)
            if nonbinary_syndrome(matrix, decoded_tuple, field) == syndrome:
                return {"status": "syndrome_consistent", "decoded": decoded_tuple, "iterations": iteration}
    except (ArithmeticError, FloatingPointError, KeyError, OverflowError, ValueError):
        return {"status": "decoder_error", "decoded": None, "iterations": iteration}
    return {"status": "decode_failed", "decoded": None, "iterations": int(max_iter)}


def _decode_layer_fft_qspa(words: Any, syndrome: Any, matrix: Any, field: GF2mField,
                           priors: np.ndarray, max_iter: int) -> dict[str, Any]:
    """Exact small-field sum-product layer decoder (the frozen ORACLE) using
    the accepted check-update semantics by identity; flooding, undamped,
    matching the accepted R1A flooding reference schedule."""
    q = field.q
    checks, variables = _matrix_edges(matrix)
    edge_keys = [(row, column) for row, row_edges in enumerate(checks) for column, _ in row_edges]
    v_to_c: dict[tuple[int, int], np.ndarray] = {
        (row, column): priors[column].copy() for row, column in edge_keys}
    c_to_v: dict[tuple[int, int], np.ndarray] = {
        (row, column): np.full(q, 1.0 / q, dtype=np.float64) for row, column in edge_keys}
    try:
        for iteration in range(1, int(max_iter) + 1):
            next_c_to_v: dict[tuple[int, int], np.ndarray] = {}
            for row, row_edges in enumerate(checks):
                extrinsics = [v_to_c[(row, column)] for column, _ in row_edges]
                coefficients = [coefficient for _, coefficient in row_edges]
                for target, (column, _) in enumerate(row_edges):
                    fresh = check_update_fft_qspa(extrinsics, coefficients, target,
                                                  int(syndrome[row]), field)
                    if fresh is None:
                        return {"status": "decoder_error", "decoded": None, "iterations": iteration}
                    next_c_to_v[(row, column)] = fresh
            c_to_v = next_c_to_v
            beliefs: list[np.ndarray] = []
            for column in range(_N):
                belief = priors[column].copy()
                for edge in variables[column]:
                    belief *= c_to_v[edge]
                normal = _normalise(belief)
                if normal is None:
                    return {"status": "decoder_error", "decoded": None, "iterations": iteration}
                beliefs.append(normal)
            decoded_tuple = tuple(int(np.argmax(beliefs[column])) for column in range(_N))
            if nonbinary_syndrome(matrix, decoded_tuple, field) == syndrome:
                return {"status": "syndrome_consistent", "decoded": decoded_tuple, "iterations": iteration}
    except (ArithmeticError, FloatingPointError, KeyError, OverflowError, ValueError):
        return {"status": "decoder_error", "decoded": None, "iterations": iteration}
    return {"status": "decode_failed", "decoded": None, "iterations": int(max_iter)}


def conditional_layer1_priors(low_words: Any, high_words: Any, decoded_high: Any,
                              q: int, p: float) -> np.ndarray:
    """Exact layer-1 priors: Bob low words + public model data + the verified
    layer-0 output only.

    Under the frozen public model (a q-ary-symmetric channel with parameter
    ``p`` on the full 10-bit symbol, exactly the accepted
    ``qsc_symbol_priors`` mass function) the conditional law of Alice's low
    word given Bob's two words and the verified layer-0 high word is

    ``P(alice_low = s) ∝ QSC_p((decoded_high << 5) | s, bob)``:

    - when ``decoded_high == high_words`` the candidate ``s == low_words``
      makes Alice's full symbol equal Bob's (mass ``1 - p``), every other
      ``s`` carries the flat ``p/1023`` mass (mass ``31*p/1023`` total);
    - otherwise every ``s`` carries the flat ``p/1023`` mass (uniform).

    The conditioning therefore concentrates the low-word belief on Bob's low
    word exactly when layer 0 agrees with Bob's high word, and degenerates to
    a uniform prior otherwise -- the honest behaviour of the conditional layer
    model under the frozen QSC channel.  The function is exposed so the T1
    small-field oracle can verify the exact formula independently.
    """
    if isinstance(p, bool) or not isinstance(p, (int, float)):
        raise ValueError("q-ary symmetric p is outside the frozen open domain")
    low = _symbols(low_words, q)
    high = _symbols(high_words, q)
    decoded = _symbols(decoded_high, q)
    if len(low) != len(high) or len(low) != len(decoded):
        raise ValueError("layer vectors must have equal length")
    flat = float(p) / 1023.0
    mass = np.full((len(low), q), flat, dtype=np.float64)
    for index in range(len(low)):
        if int(decoded[index]) == int(high[index]):
            mass[index, int(low[index])] = 1.0 - float(p)
    total = mass.sum(axis=1, keepdims=True)
    if not np.all(np.isfinite(mass)) or np.any(total <= 0.0):
        raise ValueError("conditional layer-1 prior normalisation failure")
    return mass / total


def decode_nbldpc_v7_r3(bob_symbols: Any, syndrome0: Any, syndrome1: Any,
                        manifest: Mapping[str, Any], matrices: Mapping[Any, Any], *,
                        check_count: int, p: float, max_iter: int = _MAX_ITER) -> dict[str, Any]:
    """Decode one n=1024 frame using public inputs only: Bob's 10-bit symbols,
    the layer-0 and layer-1 GF(32) syndromes, and the verified R3 codebook.

    ``check_count`` must equal ``m0 + m1`` for the frozen stratum and ``p`` one
    of the two frozen strata.  Layer 0 (high words) is decoded first; layer 1
    (low words) is invoked only when layer 0 is syndrome-consistent, with
    priors restricted to Bob data, public model data and the verified layer-0
    output.  Success requires BOTH layers syndrome-consistent; the
    reconstructed 10-bit symbols are returned for the single 64-bit tag.
    There is no fallback to the oracle.
    """
    q: int | None = None
    try:
        q = _q_spec(manifest.get("q") if isinstance(manifest, Mapping) else None)
    except ValueError:
        return _layer_result("unsupported_domain", reason="manifest q outside NBLDPC7R3 domain")
    if isinstance(check_count, bool) or not isinstance(check_count, Integral) \
            or int(check_count) not in {2 * m for m in _CHECK_COUNTS.values()}:
        return _layer_result("invalid_input", q=q, check_count=int(check_count) if isinstance(check_count, Integral) else None,
                       reason="unsupported check count")
    check_count = int(check_count)
    if float(p) not in _CHECK_COUNTS or 2 * _CHECK_COUNTS[float(p)] != check_count:
        return _layer_result("invalid_input", q=q, check_count=check_count, reason="stratum p mismatch")
    if isinstance(max_iter, bool) or not isinstance(max_iter, Integral):
        return _layer_result("invalid_input", q=q, check_count=check_count, reason="max_iter must be an integer")
    if not 1 <= int(max_iter) <= _MAX_ITER:
        return _layer_result("aborted_resource_limit", q=q, check_count=check_count, reason="max_iter")
    try:
        field = GF2mField.create(q)
        bob = _symbols(bob_symbols, 1024, expected=_N)
        disclosed0 = _symbols(syndrome0, q, expected=_CHECK_COUNTS[float(p)])
        disclosed1 = _symbols(syndrome1, q, expected=_CHECK_COUNTS[float(p)])
    except ValueError as exc:
        return _layer_result("invalid_input", q=q, n=_N, check_count=check_count, reason=str(exc))
    verified = v7_r3_cb.verify_nbldpc_v7_r3_codebook(manifest, matrices)
    if verified.get("status") != "ok":
        return _layer_result("codebook_invalid", q=q, n=_N, check_count=check_count,
                       field_id=field.spec.field_id, reason="NBLDPC7R3 manifest or matrices failed verification")
    m = _CHECK_COUNTS[float(p)]
    try:
        matrix0 = tuple(tuple(int(value) for value in row) for row in matrices[(m, 0)])
        matrix1 = tuple(tuple(int(value) for value in row) for row in matrices[(m, 1)])
    except (KeyError, TypeError, ValueError):
        return _layer_result("codebook_invalid", q=q, n=_N, check_count=check_count,
                       field_id=field.spec.field_id, reason="missing layer matrices")
    if len(matrix0) != m or len(matrix1) != m or any(len(row) != _N for row in matrix0 + matrix1):
        return _layer_result("codebook_invalid", q=q, n=_N, check_count=check_count,
                       field_id=field.spec.field_id, reason="matrix dimensions")
    checks0, variables0 = _matrix_edges(matrix0)
    checks1, variables1 = _matrix_edges(matrix1)
    edge_count = sum(map(len, checks0))
    if edge_count != 3 * _N or edge_count != sum(map(len, checks1)) \
            or any(len(row_edges) < 2 for row_edges in checks0 + checks1) \
            or any(degree != 3 for degree in (len(variables0[col]) for col in range(_N))) \
            or any(degree != 3 for degree in (len(variables1[col]) for col in range(_N))):
        return _layer_result("codebook_invalid", q=q, n=_N, check_count=check_count,
                       field_id=field.spec.field_id, reason="edge topology")
    declared = 2 * _declared_dense_bytes(_N, edge_count, q)
    if q > 32 or declared > _MAX_DENSE_BYTES:
        return _layer_result("aborted_resource_limit", q=q, n=_N, check_count=check_count,
                       field_id=field.spec.field_id, declared_dense_message_bytes=declared,
                       reason="dense_message_storage")
    codebook_id = manifest.get("manifest_id")
    if not isinstance(codebook_id, str):
        return _layer_result("codebook_invalid", q=q, n=_N, check_count=check_count,
                       field_id=field.spec.field_id, declared_dense_message_bytes=declared,
                       reason="missing codebook id")
    high, low = v7_r3_cb.split_vector(bob)
    layer0_priors = qsc_symbol_priors(high, q, float(p))
    layer0 = _decode_layer_min_sum(high, disclosed0, matrix0, field, layer0_priors, int(max_iter))
    if layer0["status"] != "syndrome_consistent":
        return _layer_result(layer0["status"], q=q, n=_N, check_count=check_count,
                       iterations=int(layer0["iterations"]), field_id=field.spec.field_id,
                       codebook_id=codebook_id, declared_dense_message_bytes=declared,
                       reason="layer0_failed_short_circuit", layer0_consistent=False,
                       layer1_invoked=False)
    layer1_priors = conditional_layer1_priors(low, high, layer0["decoded"], q, float(p))
    layer1 = _decode_layer_min_sum(low, disclosed1, matrix1, field, layer1_priors, int(max_iter))
    if layer1["status"] != "syndrome_consistent":
        return _layer_result(layer1["status"], q=q, n=_N, check_count=check_count,
                       iterations=int(layer0["iterations"]) + int(layer1["iterations"]),
                       field_id=field.spec.field_id, codebook_id=codebook_id,
                       declared_dense_message_bytes=declared, reason="layer1_failed",
                       layer0_consistent=True, layer1_consistent=False, layer1_invoked=True)
    reconstructed = v7_r3_cb.join_vector(layer0["decoded"], layer1["decoded"])
    return _layer_result("syndrome_consistent", q=q, n=_N, check_count=check_count,
                   iterations=int(layer0["iterations"]) + int(layer1["iterations"]),
                   syndrome_consistent=True, field_id=field.spec.field_id, codebook_id=codebook_id,
                   declared_dense_message_bytes=declared, decoded_symbols=reconstructed,
                   layer0_consistent=True, layer1_consistent=True, layer1_invoked=True)


def decode_nbldpc_v7_r3_fft_qspa(bob_symbols: Any, syndrome0: Any, syndrome1: Any,
                                 manifest: Mapping[str, Any], matrices: Mapping[Any, Any], *,
                                 check_count: int, p: float, max_iter: int = _MAX_ITER) -> dict[str, Any]:
    """Small-field exact FFT-QSPA ORACLE for the same two-layer scheme.

    Test-only: identical public contract and two-layer flow, but every check
    update is the exact sum-product convolution via the accepted
    ``check_update_fft_qspa``.  NEVER used by production and NEVER a fallback.
    """
    q: int | None = None
    try:
        q = _q_spec(manifest.get("q") if isinstance(manifest, Mapping) else None)
    except ValueError:
        return _layer_result("unsupported_domain", reason="manifest q outside NBLDPC7R3 domain")
    if isinstance(check_count, bool) or not isinstance(check_count, Integral) \
            or int(check_count) not in {2 * m for m in _CHECK_COUNTS.values()}:
        return _layer_result("invalid_input", q=q, check_count=int(check_count) if isinstance(check_count, Integral) else None,
                       reason="unsupported check count")
    check_count = int(check_count)
    if float(p) not in _CHECK_COUNTS or 2 * _CHECK_COUNTS[float(p)] != check_count:
        return _layer_result("invalid_input", q=q, check_count=check_count, reason="stratum p mismatch")
    if isinstance(max_iter, bool) or not isinstance(max_iter, Integral) \
            or not 1 <= int(max_iter) <= _MAX_ITER:
        return _layer_result("aborted_resource_limit", q=q, check_count=check_count, reason="max_iter")
    try:
        field = GF2mField.create(q)
        bob = _symbols(bob_symbols, 1024, expected=_N)
        disclosed0 = _symbols(syndrome0, q, expected=_CHECK_COUNTS[float(p)])
        disclosed1 = _symbols(syndrome1, q, expected=_CHECK_COUNTS[float(p)])
    except ValueError as exc:
        return _layer_result("invalid_input", q=q, n=_N, check_count=check_count, reason=str(exc))
    verified = v7_r3_cb.verify_nbldpc_v7_r3_codebook(manifest, matrices)
    if verified.get("status") != "ok":
        return _layer_result("codebook_invalid", q=q, n=_N, check_count=check_count,
                       field_id=field.spec.field_id, reason="NBLDPC7R3 manifest or matrices failed verification")
    m = _CHECK_COUNTS[float(p)]
    try:
        matrix0 = tuple(tuple(int(value) for value in row) for row in matrices[(m, 0)])
        matrix1 = tuple(tuple(int(value) for value in row) for row in matrices[(m, 1)])
    except (KeyError, TypeError, ValueError):
        return _layer_result("codebook_invalid", q=q, n=_N, check_count=check_count,
                       field_id=field.spec.field_id, reason="missing layer matrices")
    high, low = v7_r3_cb.split_vector(bob)
    layer0 = _decode_layer_fft_qspa(high, disclosed0, matrix0, field,
                                    qsc_symbol_priors(high, q, float(p)), int(max_iter))
    if layer0["status"] != "syndrome_consistent":
        return _layer_result(layer0["status"], q=q, n=_N, check_count=check_count,
                       iterations=int(layer0["iterations"]), field_id=field.spec.field_id,
                       codebook_id=manifest.get("manifest_id"), reason="layer0_failed_short_circuit",
                       layer0_consistent=False, layer1_invoked=False)
    layer1_priors = conditional_layer1_priors(low, high, layer0["decoded"], q, float(p))
    layer1 = _decode_layer_fft_qspa(low, disclosed1, matrix1, field, layer1_priors, int(max_iter))
    if layer1["status"] != "syndrome_consistent":
        return _layer_result(layer1["status"], q=q, n=_N, check_count=check_count,
                       iterations=int(layer0["iterations"]) + int(layer1["iterations"]),
                       field_id=field.spec.field_id, codebook_id=manifest.get("manifest_id"),
                       reason="layer1_failed", layer0_consistent=True,
                       layer1_consistent=False, layer1_invoked=True)
    reconstructed = v7_r3_cb.join_vector(layer0["decoded"], layer1["decoded"])
    return _layer_result("syndrome_consistent", q=q, n=_N, check_count=check_count,
                   iterations=int(layer0["iterations"]) + int(layer1["iterations"]),
                   syndrome_consistent=True, field_id=field.spec.field_id,
                   codebook_id=manifest.get("manifest_id"), decoded_symbols=reconstructed,
                   layer0_consistent=True, layer1_consistent=True, layer1_invoked=True)


def production_runner(bob_symbols: Any, syndrome0: Any, syndrome1: Any,
                      manifest: Mapping[str, Any], matrices: Mapping[Any, Any], *,
                      check_count: int, p: float) -> dict[str, Any]:
    """Production development-run adapter: the frozen flooding EMS."""
    return decode_nbldpc_v7_r3(bob_symbols, syndrome0, syndrome1, manifest, matrices,
                               check_count=check_count, p=p)


def declared_dense_bytes() -> int:
    """Exact two-layer dense-message budget of the frozen graphs."""
    return 2 * _declared_dense_bytes(_N, 3 * _N, _Q)
