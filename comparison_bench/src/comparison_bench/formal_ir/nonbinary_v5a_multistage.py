"""Public-input-only three-level incremental-redundancy NBLDPC v5a core.

This is intentionally an in-memory state machine.  Qualification, Alice-side
tags, and files live in the shared runtime (:mod:`nonbinary_v5_runtime`) bound
through :mod:`nonbinary_v5a_ir_qualification`.

Policies (frozen):
- ``nbldpc_v5a_ir56`` (candidate): p=.20 two-level 32->40, p=.30 three-level
  40->48->56, warm retention across every extension, at most 3 verification
  attempts per frame (protocol epsilon union bound 2^-62).
- ``nbldpc_v5a_ir48`` (control): p=.20 two-level 32->40, p=.30 two-level
  40->48, warm retention — the v4-equivalent two-level behavior under the
  v5a identity and fresh data; at most 2 attempts (bound 2^-63).  It never
  extends beyond its frozen two levels.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from numbers import Integral
from typing import Any, Mapping

import numpy as np

from .nonbinary_field import GF2mField
from .nonbinary_qspa import (_declared_dense_bytes, _normalise, _result,
                             _symbols, nonbinary_syndrome, qsc_symbol_priors)
from . import nonbinary_v5a_codebook as v5a_cb
from . import nonbinary_v3 as v3

METHOD = "nbldpc_formal_v5a_multistage"
POLICIES = ("nbldpc_v5a_ir56", "nbldpc_v5a_ir48")
Q, N, STAGE_ITERATIONS, MAX_BYTES = 1024, 64, 12, 24 * 1024 * 1024
CHECK_COUNTS = (32, 40, 48, 56)
LADDERS = {"nbldpc_v5a_ir56": {0.20: (32, 40), 0.30: (40, 48, 56)},
           "nbldpc_v5a_ir48": {0.20: (32, 40), 0.30: (40, 48)}}
VERIFICATION_CAPS = {"nbldpc_v5a_ir56": 3, "nbldpc_v5a_ir48": 2}
PROTOCOL_EPSILON = {"nbldpc_v5a_ir56": 2.0 ** -62, "nbldpc_v5a_ir48": 2.0 ** -63}


def codebook() -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    return v5a_cb.codebook()

def policy_spec(policy_id: str, p: float) -> dict[str, Any]:
    if policy_id not in POLICIES or float(p) not in (0.20, 0.30):
        raise ValueError("invalid v5a policy/stratum")
    ladder = LADDERS[policy_id][float(p)]
    return {"policy_id": policy_id, "p": float(p), "initial_checks": ladder[0],
            "final_checks": ladder[-1], "ladder": list(ladder), "lambda": .75,
            "stage_iterations": STAGE_ITERATIONS}

def stage_slots(policy_id: str, p: float) -> tuple[int, ...]:
    """Seed-record slots per (policy, stratum): one per ladder level."""
    return tuple(range(len(LADDERS[policy_id][float(p)])))

def extension_mode(policy_id: str) -> str:
    if policy_id not in POLICIES:
        raise ValueError("invalid v5a policy")
    return "warm"  # both v5a policies are warm-retention policies

def verification_cap(policy_id: str) -> int:
    if policy_id not in POLICIES:
        raise ValueError("invalid v5a policy")
    return VERIFICATION_CAPS[policy_id]

def protocol_epsilon(policy_id: str) -> float:
    if policy_id not in POLICIES:
        raise ValueError("invalid v5a policy")
    return PROTOCOL_EPSILON[policy_id]


def _edges(matrix: Any) -> tuple[list[tuple[tuple[int, int], ...]], list[list[tuple[int, int]]]]:
    checks = [tuple((v, int(a)) for v, a in enumerate(row) if a) for row in matrix]
    variables = [[] for _ in range(N)]
    for row, row_edges in enumerate(checks):
        for variable, _ in row_edges:
            variables[variable].append((row, variable))
    return checks, variables


@dataclass
class DecoderState:
    method: str
    policy_id: str
    codebook_sha256: str
    p: float
    active_checks: int
    syndrome: tuple[int, ...]
    bob: tuple[int, ...]
    messages: dict[tuple[int, int], np.ndarray]

    def __getstate__(self):  # evidence must never serialize a resumable decoder
        raise TypeError("decoder state is not serializable")


def _bound(policy_id: str, bob: Any, syndrome: Any, manifest: Mapping[str, Any], *, p: float, checks: int) -> tuple[DecoderState, Any, Any, Any] | dict[str, Any]:
    if policy_id not in POLICIES or float(p) not in (0.20, 0.30) or checks not in CHECK_COUNTS:
        return _result("invalid_input", q=Q, n=N, check_count=checks, reason="policy_or_prefix")
    cb, matrices = codebook()
    if dict(manifest) != cb:
        return _result("codebook_invalid", q=Q, n=N, check_count=checks)
    try:
        b = tuple(_symbols(bob, Q, expected=N)); s = tuple(_symbols(syndrome, Q, expected=checks))
        row_edges, variable_edges = _edges(matrices[checks])
        if any(len(x) > 8 for x in row_edges):
            return _result("aborted_resource_limit", q=Q, n=N, check_count=checks, reason="row_weight")
        declared = _declared_dense_bytes(N, sum(map(len, row_edges)), Q)
        if declared > MAX_BYTES:
            return _result("aborted_resource_limit", q=Q, n=N, check_count=checks, reason="dense_message_storage")
        messages = {(r, v): np.full(Q, 1.0 / Q) for r, es in enumerate(row_edges) for v, _ in es}
        state = DecoderState(METHOD, policy_id, cb["canonical_sha256"], float(p), checks, s, b, messages)
        return state, matrices, row_edges, variable_edges
    except (TypeError, ValueError, OverflowError):
        return _result("invalid_input", q=Q, n=N, check_count=checks, reason="symbols")


def reconstruct_beliefs(state: DecoderState, matrices: Mapping[int, Any]) -> list[np.ndarray]:
    """Complete product; specifically does not retain/reuse a stage cache."""
    priors = qsc_symbol_priors(state.bob, Q, state.p)
    _, variables = _edges(matrices[state.active_checks])
    out = []
    for variable, prior in enumerate(priors):
        value = prior.copy()
        for edge in variables[variable]:
            value *= state.messages[edge]
        norm = _normalise(value)
        if norm is None:
            raise ArithmeticError("belief normalisation")
        out.append(norm)
    return out


def _run(state: DecoderState, matrices: Mapping[int, Any], *, iterations: int = STAGE_ITERATIONS) -> dict[str, Any]:
    if not 1 <= int(iterations) <= STAGE_ITERATIONS:
        return _result("aborted_resource_limit", q=Q, n=N, check_count=state.active_checks, reason="stage_iterations")
    field = GF2mField.create(Q); rows, variables = _edges(matrices[state.active_checks])
    priors = qsc_symbol_priors(state.bob, Q, state.p)
    try:
        for it in range(1, int(iterations) + 1):
            for r, edges in enumerate(rows):
                extra = []
                for v, _ in edges:
                    value = priors[v].copy()
                    for edge in variables[v]:
                        if edge != (r, v): value *= state.messages[edge]
                    value = _normalise(value)
                    if value is None: raise ArithmeticError("extrinsic")
                    extra.append(value)
                for target, (v, _) in enumerate(edges):
                    fresh = v3._check_update_qspa(extra, [a for _, a in edges], target, state.syndrome[r], field)
                    if fresh is None: raise ArithmeticError("check")
                    updated = _normalise(.75 * fresh + .25 * state.messages[r, v])
                    if updated is None: raise ArithmeticError("message")
                    state.messages[r, v] = updated
            beliefs = reconstruct_beliefs(state, matrices)
            decoded = tuple(int(np.argmax(x)) for x in beliefs)
            if nonbinary_syndrome(matrices[state.active_checks], decoded, field) == state.syndrome:
                return _result("syndrome_consistent", q=Q, n=N, check_count=state.active_checks,
                               iterations=it, syndrome_consistent=True, decoded_symbols=decoded,
                               declared_dense_message_bytes=_declared_dense_bytes(N, len(state.messages), Q))
        return _result("decode_failed", q=Q, n=N, check_count=state.active_checks,
                       iterations=int(iterations), reason="iteration_limit")
    except (ArithmeticError, FloatingPointError, KeyError, ValueError, OverflowError):
        return _result("decoder_error", q=Q, n=N, check_count=state.active_checks, reason="numerical_or_field_failure")


def _stage(state: DecoderState, matrices: Mapping[int, Any], stage: int, stage_runner=None) -> dict[str, Any]:
    """The only test seam: it receives live state, never Alice/tag truth."""
    result = _run(state, matrices) if stage_runner is None else dict(stage_runner(state, matrices, stage))
    permitted = {"syndrome_consistent", "decode_failed", "decoder_error", "codebook_invalid",
                 "invalid_input", "unsupported_domain", "aborted_resource_limit"}
    if result.get("status") not in permitted:
        return _result("decoder_error", q=Q, n=N, check_count=state.active_checks, reason="unknown_stage_status")
    if result.get("status") == "syndrome_consistent":
        try:
            result["decoded_symbols"] = tuple(_symbols(result["decoded_symbols"], Q, expected=N))
        except (KeyError, TypeError, ValueError, OverflowError):
            return _result("decoder_error", q=Q, n=N, check_count=state.active_checks, reason="missing_decoded_symbols")
    result["iterations"] = int(result.get("iterations", 0))
    if result["iterations"] < 0 or result["iterations"] > STAGE_ITERATIONS:
        return _result("aborted_resource_limit", q=Q, n=N, check_count=state.active_checks, reason="stage_iterations")
    return result


def start(policy_id: str, bob: Any, syndrome: Any, manifest: Mapping[str, Any], *, p: float, stage_runner=None) -> tuple[DecoderState, dict[str, Any], dict[int, Any]] | dict[str, Any]:
    ladder = LADDERS.get(policy_id, {}).get(float(p))
    if ladder is None:
        return _result("invalid_input", q=Q, n=N, reason="p")
    bound = _bound(policy_id, bob, syndrome, manifest, p=float(p), checks=ladder[0])
    if isinstance(bound, dict):
        return bound
    state, matrices, _, _ = bound
    return state, _stage(state, matrices, 1, stage_runner), matrices


def extend(state: DecoderState, extension_syndrome: Any, matrices: Mapping[int, Any], *, mode: str) -> DecoderState | dict[str, Any]:
    """One legal warm extension to the next ladder level; fails closed."""
    ladder = LADDERS.get(state.policy_id, {}).get(state.p)
    if mode != "warm" or ladder is None:
        return _result("invalid_input", q=Q, n=N, check_count=state.active_checks, reason="extension_mode")
    if state.active_checks not in ladder:
        return _result("invalid_input", q=Q, n=N, check_count=state.active_checks, reason="second_extension")
    index = ladder.index(state.active_checks)
    if index == len(ladder) - 1:
        return _result("invalid_input", q=Q, n=N, check_count=state.active_checks, reason="final_level")
    final = ladder[index + 1]
    try:
        suffix = tuple(_symbols(extension_syndrome, Q, expected=final - state.active_checks))
        old = dict(state.messages); state.active_checks = final
        state.syndrome = state.syndrome + suffix
        rows, _ = _edges(matrices[final])
        state.messages = {(r, v): old[(r, v)].copy() if (r, v) in old else np.full(Q, 1.0 / Q)
                          for r, es in enumerate(rows) for v, _ in es}
        reconstruct_beliefs(state, matrices)  # proves all active messages are used before the next stage
        return state
    except (TypeError, ValueError, OverflowError):
        return _result("invalid_input", q=Q, n=N, check_count=final, reason="extension_syndrome")


def run_stage(state: DecoderState, matrices: Mapping[int, Any], *, stage: int, stage_runner=None) -> dict[str, Any]:
    if not isinstance(stage, Integral) or int(stage) < 2:
        return _result("invalid_input", q=Q, n=N, check_count=state.active_checks, reason="stage")
    return _stage(state, matrices, int(stage), stage_runner)


def production_runner(state, matrices, stage):
    """Production adapter: the live v5a state machine is the decoder."""
    return _run(state, matrices)
