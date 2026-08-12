"""NBLDPC7 R1B: one-multiplicative-repetition prior-combining decoder for
``nbldpc_formal_v7_r1b_mr1``.

R1B never builds a second dense Tanner graph.  Instead the repeated q-ary
observation of every variable is *multiply-aligned* by the inverse of the
variable's deterministic public GF(1024) multiplier and combined into the
variable's prior before the exact R1A mother decoding:

- mother observation ``b_v = x_v xor e_v`` (q-ary symmetric noise ``p``);
- repeated observation ``z_v = mult_v * x_v xor e'_v`` (independent q-ary
  symmetric noise ``p``);
- aligned repetition ``a_v = inv(mult_v) * z_v = x_v xor inv(mult_v) * e'_v``,
  which is again q-ary symmetric noise ``p`` on ``x_v`` (multiplication by a
  fixed nonzero constant permutes the nonzero field elements);
- combined prior ``P(x_v = s) ∝ QSC_p(b_v, s) * QSC_p(a_v, s)`` — the exact
  brute-force posterior combination of two independent observations
  (exhaustively oracle-tested on GF(4)/GF(8) in T1).

The combined prior is then decoded by the *accepted R1A core*: the flooding
FFT-QSPA is the literature-reference schedule and the primary production
decoder; layered FFT-QSPA is the frozen same-code diagnostic.  Both are
deterministic (workers=1), ``max_iter=100``, damping ``lambda=.75`` (layered
only; flooding is undamped, matching the accepted R1A schedule).  The
check-update semantics, the message layout and the fail-closed contracts
(NaN/Inf rejection, wrong length/domain ``invalid_input``, allocation cap
``aborted_resource_limit`` before any dense-message allocation, no fallback
between schedules) are inherited from the accepted R1A module.

Disclosure accounting: the same mother syndrome of ``10*m = 1700`` bits plus an
invoked 64-bit Toeplitz tag.  R1B is the final repetition depth.
"""
from __future__ import annotations

import math
from functools import lru_cache
from numbers import Integral
from typing import Any, Mapping

import numpy as np

from .nonbinary_field import GF2mField
from .nonbinary_qspa import (_declared_dense_bytes, _normalise, _result, _symbols,
                             nonbinary_syndrome, qsc_symbol_priors)
from . import nonbinary_v7_r1a_long as v7_long
from . import nonbinary_v7_r1b_codebook as v7_r1b_cb

METHOD = "nbldpc_formal_v7_r1b_mr1"
_Q, _N, _M, _MAX_ITER, _LAMBDA = 1024, 256, 170, 100, 0.75
_SCHEDULES = ("flooding", "layered")
# Frozen primary decoder choice: flooding FFT-QSPA (accepted R1A schedule).
_PRIMARY_SCHEDULE = "flooding"
_MAX_DENSE_BYTES = 16 * 1024 * 1024
_SYNDROME_DISCLOSURE_BITS = 10 * _M  # 1700, the frozen mother syndrome.
# The accepted R1A check-update semantics are reused verbatim (identity, not a
# copy): layered schedule invokes exactly this function through the core.
check_update_fft_qspa = v7_long.check_update_fft_qspa


def _q_spec(q: Any) -> int:
    if q != 1024:
        raise ValueError("unsupported GF(q) domain")
    return 1024


def _multipliers_from_manifest(manifest: Mapping[str, Any]) -> tuple[int, ...]:
    values = manifest.get("multipliers")
    if not isinstance(values, (tuple, list)) or len(values) != _N:
        raise ValueError("multipliers missing from manifest")
    answer = tuple(int(value) for value in values)
    if any(not 1 <= value < _Q for value in answer):
        raise ValueError("multiplier outside nonzero field domain")
    return answer


def aligned_observation(repeated_symbols: Any, multipliers: Any, field: GF2mField) -> tuple[int, ...]:
    """Multiply-align a repetition observation into the mother symbol domain.

    ``a_v = inv(mult_v) * z_v``.  This is the exact alignment step the
    prior-combining formula uses; it is exposed as a small public helper so the
    T1 small-field oracle can verify ``field.mul(mult_v, a_v) == z_v`` and the
    combined posterior equality independently.
    """
    repeated = _symbols(repeated_symbols, field.q)
    values = tuple(int(value) for value in multipliers)
    if len(values) != len(repeated):
        raise ValueError("repetition and multiplier lengths differ")
    aligned = []
    for value, multiplier in zip(repeated, values):
        if multiplier == 0:
            raise ValueError("zero multiplier has no inverse")
        aligned.append(field.mul(field.inverse(multiplier), value))
    return tuple(aligned)


def combined_qsc_priors(bob_symbols: Any, repeated_symbols: Any, multipliers: Any,
                        q: int, p: float) -> np.ndarray:
    """Combine the mother and multiply-aligned repetition observations into one
    normalized q-ary prior per variable (the exact brute-force posterior
    combination of two independent QSC observations)."""
    field = GF2mField.create(q)
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) \
            or not 0.0 < float(p) < (q - 1) / q:
        raise ValueError("q-ary symmetric p is outside the frozen open domain")
    bob = _symbols(bob_symbols, q, expected=_N if q == 1024 else None)
    aligned = aligned_observation(repeated_symbols, multipliers, field)
    mother_prior = qsc_symbol_priors(bob, q, p)
    repetition_prior = qsc_symbol_priors(aligned, q, p)
    combined = mother_prior * repetition_prior
    out = np.empty_like(combined)
    for index in range(combined.shape[0]):
        normal = _normalise(combined[index])
        if normal is None:
            raise ValueError("combined prior normalisation failure")
        out[index] = normal
    return out


@lru_cache(maxsize=1)
def _declared_dense_bytes_r1b() -> int:
    # Mother graph: (2*n + 2*edges)*q*8; the repetition is combined into the
    # prior before decoding, so no second dense message family exists.
    return _declared_dense_bytes(_N, 2 * _N, _Q)


def decode_nbldpc_v7_r1b(bob_symbols: Any, repeated_symbols: Any, syndrome: Any,
                         manifest: Mapping[str, Any], matrices: Any, *, check_count: int,
                         p: float, schedule: str = _PRIMARY_SCHEDULE,
                         max_iter: int = _MAX_ITER) -> dict[str, Any]:
    """Decode one n=256 frame using public inputs only (mother observation,
    repeated observation, public syndrome, verified R1B codebook).

    ``check_count`` must be 170 and ``p`` one of the two frozen strata (.20 /
    .30).  ``schedule`` is ``"flooding"`` (primary) or ``"layered"`` (frozen
    same-code diagnostic).  All validation fails closed before any
    verification or allocation; there is no fallback between schedules.
    """
    q: int | None = None
    try:
        q = _q_spec(manifest.get("q") if isinstance(manifest, Mapping) else None)
    except ValueError:
        return _result("unsupported_domain", reason="manifest q outside NBLDPC7R1B domain")
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
        _symbols(repeated_symbols, q, expected=_N)
        disclosed = _symbols(syndrome, q, expected=check_count)
    except ValueError as exc:
        return _result("invalid_input", q=q, n=_N, check_count=check_count, reason=str(exc))
    verified = v7_r1b_cb.verify_nbldpc_v7_r1b_codebook(manifest, matrices)
    if verified.get("status") != "ok":
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count,
                       field_id=field.spec.field_id, reason="NBLDPC7R1B manifest or matrix failed verification")
    try:
        multipliers = _multipliers_from_manifest(manifest)
    except ValueError:
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count,
                       field_id=field.spec.field_id, reason="multiplier contract")
    try:
        matrix = tuple(tuple(int(value) for value in row) for row in matrices)
    except (KeyError, TypeError, ValueError):
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id)
    if len(matrix) != check_count or any(len(row) != _N for row in matrix):
        return _result("codebook_invalid", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       reason="matrix dimensions")
    checks, variables = v7_long._matrix_edges(matrix)
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
    try:
        priors = combined_qsc_priors(bob, repeated_symbols, multipliers, q, p)
    except ValueError as exc:
        return _result("decoder_error", q=q, n=_N, check_count=check_count, field_id=field.spec.field_id,
                       codebook_id=codebook_id, declared_dense_message_bytes=declared,
                       reason=f"prior_combination_{exc}")
    if schedule == "flooding":
        return v7_long._decode_flooding(bob, disclosed, matrix, checks, variables, priors, field,
                                        check_count, codebook_id, declared, max_iter=int(max_iter))
    return v7_long._decode_layered(bob, disclosed, matrix, checks, variables, priors, field,
                                   check_count, codebook_id, declared, max_iter=int(max_iter))


def production_runner(bob_symbols: Any, repeated_symbols: Any, syndrome: Any,
                      manifest: Mapping[str, Any], matrices: Any, *,
                      check_count: int, p: float) -> dict[str, Any]:
    """Production development-run adapter: the primary flooding decoder."""
    return decode_nbldpc_v7_r1b(bob_symbols, repeated_symbols, syndrome, manifest, matrices,
                                check_count=check_count, p=p, schedule=_PRIMARY_SCHEDULE)
