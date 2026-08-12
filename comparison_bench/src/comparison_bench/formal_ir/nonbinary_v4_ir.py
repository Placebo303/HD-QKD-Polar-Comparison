"""Public-input-only two-stage incremental-redundancy NBLDPC v4 core.

This is intentionally an in-memory state machine.  Qualification, Alice-side
tags, and files live in :mod:`nonbinary_v4_ir_qualification`.
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
from . import nonbinary_v3 as v3

METHOD = "nbldpc_formal_v4_ir"
POLICIES = ("nbldpc_v4_control", "nbldpc_v4_ir_warm", "nbldpc_v4_ir_restart")
Q, N, STAGE_ITERATIONS, MAX_BYTES = 1024, 64, 12, 24 * 1024 * 1024
PREFIXES = {0.20: (32, 40), 0.30: (40, 48)}


@lru_cache(maxsize=1)
def _codebook_cached() -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    """Reconstruct exactly (rather than import artifacts from) the v3 family."""
    return v3.build_nbldpc_v3_codebook()

def codebook() -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    """Fresh manifest container over a cached deterministic reconstruction."""
    manifest, matrices = _codebook_cached()
    return dict(manifest), matrices


def policy_spec(policy_id: str, p: float) -> dict[str, Any]:
    if policy_id not in POLICIES or float(p) not in PREFIXES:
        raise ValueError("invalid v4 policy/stratum")
    initial, final = PREFIXES[float(p)]
    return {"policy_id": policy_id, "p": float(p), "initial_checks": initial,
            "final_checks": final, "lambda": .75, "stage_iterations": STAGE_ITERATIONS}


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
    if policy_id not in POLICIES or float(p) not in PREFIXES or checks not in (32, 40, 48):
        return _result("invalid_input", q=Q, n=N, check_count=checks, reason="policy_or_prefix")
    cb, matrices = codebook()
    # `codebook()` is independently reconstructed/cached once; equality binds
    # the entire canonical v3 manifest without repeating its salt search per
    # frame.
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
    """Complete product; specifically does not retain/reuse a stage-1 cache."""
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
    field = GF2mField.create(Q); rows, variables = _edges(matrices[state.active_checks]); priors = qsc_symbol_priors(state.bob, Q, state.p)
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
        return _result("decode_failed", q=Q, n=N, check_count=state.active_checks, iterations=int(iterations), reason="iteration_limit")
    except (ArithmeticError, FloatingPointError, KeyError, ValueError, OverflowError):
        return _result("decoder_error", q=Q, n=N, check_count=state.active_checks, reason="numerical_or_field_failure")


def _stage(state: DecoderState, matrices: Mapping[int, Any], stage: int, stage_runner=None) -> dict[str, Any]:
    """The only test seam: it receives live state, never Alice/tag truth."""
    result = _run(state, matrices) if stage_runner is None else dict(stage_runner(state, matrices, stage))
    permitted={"syndrome_consistent","decode_failed","decoder_error","codebook_invalid","invalid_input","unsupported_domain","aborted_resource_limit"}
    if result.get("status") not in permitted:
        return _result("decoder_error", q=Q,n=N,check_count=state.active_checks,reason="unknown_stage_status")
    if result.get("status")=="syndrome_consistent":
        try: result["decoded_symbols"]=tuple(_symbols(result["decoded_symbols"],Q,expected=N))
        except (KeyError,TypeError,ValueError,OverflowError): return _result("decoder_error",q=Q,n=N,check_count=state.active_checks,reason="missing_decoded_symbols")
    result["iterations"]=int(result.get("iterations",0))
    if result["iterations"]<0 or result["iterations"]>STAGE_ITERATIONS:return _result("aborted_resource_limit",q=Q,n=N,check_count=state.active_checks,reason="stage_iterations")
    return result


def start(policy_id: str, bob: Any, syndrome: Any, manifest: Mapping[str, Any], *, p: float, stage_runner=None) -> tuple[DecoderState, dict[str, Any], dict[int, Any]] | dict[str, Any]:
    initial, _ = PREFIXES.get(float(p), (None, None))
    if initial is None: return _result("invalid_input", q=Q, n=N, reason="p")
    bound = _bound(policy_id, bob, syndrome, manifest, p=float(p), checks=initial)
    if isinstance(bound, dict): return bound
    state, matrices, _, _ = bound
    return state, _stage(state, matrices, 1, stage_runner), matrices


def extend(state: DecoderState, extension_syndrome: Any, matrices: Mapping[int, Any], *, mode: str) -> DecoderState | dict[str, Any]:
    """One legal extension.  `mode` is frozen to warm/restart and fails closed."""
    if mode not in {"warm", "restart"} or state.policy_id not in {"nbldpc_v4_ir_warm", "nbldpc_v4_ir_restart"}:
        return _result("invalid_input", q=Q, n=N, check_count=state.active_checks, reason="extension_mode")
    expected_mode = "warm" if state.policy_id.endswith("warm") else "restart"
    if mode != expected_mode or state.active_checks != PREFIXES[state.p][0]:
        return _result("invalid_input", q=Q, n=N, check_count=state.active_checks, reason="second_extension")
    final = PREFIXES[state.p][1]
    try:
        suffix = tuple(_symbols(extension_syndrome, Q, expected=final - state.active_checks))
        if mode == "restart":
            result = _bound(state.policy_id, state.bob, state.syndrome + suffix, {**codebook()[0]}, p=state.p, checks=final)
            if isinstance(result, dict): return result
            return result[0]
        old = dict(state.messages); state.active_checks = final; state.syndrome = state.syndrome + suffix
        rows, _ = _edges(matrices[final]); state.messages = {(r, v): old[(r, v)].copy() if (r, v) in old else np.full(Q, 1.0 / Q)
                                                              for r, es in enumerate(rows) for v, _ in es}
        reconstruct_beliefs(state, matrices)  # proves all active messages are used before stage 2
        return state
    except (TypeError, ValueError, OverflowError):
        return _result("invalid_input", q=Q, n=N, check_count=final, reason="extension_syndrome")


def run_stage2(state: DecoderState, matrices: Mapping[int, Any], *, stage_runner=None) -> dict[str, Any]:
    return _stage(state, matrices, 2, stage_runner)
