"""Route C (nbldpc_formal_v5c_decoder) public-input-only core: two bounded decoders.

Route C freezes the NBLDPC5B mother code (Route B ran and is non-promoted) and
compares, inside the identical three-level warm state machine, two decoder
policies:

- ``nbldpc_v5c_sched`` — probability-domain row-layered FFT-QSPA with a frozen
  damping schedule per 12-iteration stage: lambda ``0.5`` for iterations 1..4,
  ``0.75`` for 5..8, ``0.90`` for 9..12 (applies at every stage; deterministic,
  no oracle).  With the constant lambda ``.75`` it is exactly the v4 warm
  decoder on identical inputs (pure in-memory equivalence test).
- ``nbldpc_v5c_ems`` — LLR-domain Extended Min-Sum (Declercq & Fossorier,
  IEEE TCOM 2007) with messages truncated to the frozen ``nm=64`` most
  reliable symbols, min-sum check updates with the frozen correction factor
  ``alpha=0.8``, deterministically sorted messages, and the same per-stage
  iteration cap.  Syndrome consistency is checked on the decoded hard vector
  as usual.

Both policies keep public-input-only signatures, the exact
``syndrome_consistent`` semantics, three-level IR framework
(p=.20 32->40, p=.30 40->48->56), warm retention across extensions, at most
3 verification attempts per frame, and ``protocol_epsilon_ec_bound = 2^-62``.
This module is a Route-C-specific binding: it does not modify any Route A/B
file.  Qualification, tags, and files live in the shared runtime
(:mod:`nonbinary_v5_runtime`) bound through
:mod:`nonbinary_v5c_ir_qualification`.
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
from . import nonbinary_v5b_mother as v5b_cb
from . import nonbinary_v3 as v3

METHOD = "nbldpc_formal_v5c_decoder"
POLICIES = ("nbldpc_v5c_sched", "nbldpc_v5c_ems")
Q, N, STAGE_ITERATIONS, MAX_BYTES = 1024, 64, 12, 24 * 1024 * 1024
CHECK_COUNTS = (32, 40, 48, 56)
NM = 64          # frozen EMS truncation depth
ALPHA = 0.8      # frozen EMS min-sum correction factor
SCHEDULE = (0.5, 0.75, 0.90)  # per 4-iteration quartile
LADDERS = {policy: {0.20: (32, 40), 0.30: (40, 48, 56)} for policy in POLICIES}
VERIFICATION_CAPS = {policy: 3 for policy in POLICIES}
PROTOCOL_EPSILON = {policy: 2.0 ** -62 for policy in POLICIES}
_NEG = -1e30  # clipped LLR floor; finite, so inf/nan can never enter sums


def codebook() -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    """Route C identity fixed at plan freeze: NBLDPC5B (B ran, non-promoted)."""
    return v5b_cb.codebook()

def policy_spec(policy_id: str, p: float) -> dict[str, Any]:
    if policy_id not in POLICIES or float(p) not in (0.20, 0.30):
        raise ValueError("invalid v5c policy/stratum")
    ladder = LADDERS[policy_id][float(p)]
    spec = {"policy_id": policy_id, "p": float(p), "initial_checks": ladder[0],
            "final_checks": ladder[-1], "ladder": list(ladder),
            "stage_iterations": STAGE_ITERATIONS}
    if policy_id == "nbldpc_v5c_sched":
        spec["decoder"] = "damped_fft_qspa"
        spec["damping_schedule"] = list(SCHEDULE)
    else:
        spec["decoder"] = "ems"
        spec["nm"] = NM
        spec["alpha"] = ALPHA
    return spec

def stage_slots(policy_id: str, p: float) -> tuple[int, ...]:
    """Seed-record slots per (policy, stratum): one per ladder level."""
    return tuple(range(len(LADDERS[policy_id][float(p)])))

def extension_mode(policy_id: str) -> str:
    if policy_id not in POLICIES:
        raise ValueError("invalid v5c policy")
    return "warm"  # both v5c policies are warm-retention policies

def verification_cap(policy_id: str) -> int:
    if policy_id not in POLICIES:
        raise ValueError("invalid v5c policy")
    return VERIFICATION_CAPS[policy_id]

def protocol_epsilon(policy_id: str) -> float:
    if policy_id not in POLICIES:
        raise ValueError("invalid v5c policy")
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
        if policy_id == "nbldpc_v5c_ems":
            # LLR domain: 0.0 means uniform; only the top-nm symbols stay finite.
            messages = {(r, v): np.full(Q, _NEG, dtype=np.float64) for r, es in enumerate(row_edges) for v, _ in es}
            for r, es in enumerate(row_edges):
                for v, _ in es:
                    messages[r, v][:min(NM, Q)] = 0.0  # deterministic canonical top-nm tie break
        else:
            messages = {(r, v): np.full(Q, 1.0 / Q, dtype=np.float64) for r, es in enumerate(row_edges) for v, _ in es}
        state = DecoderState(METHOD, policy_id, cb["canonical_sha256"], float(p), checks, s, b, messages)
        return state, matrices, row_edges, variable_edges
    except (TypeError, ValueError, OverflowError):
        return _result("invalid_input", q=Q, n=N, check_count=checks, reason="symbols")


def _llr_priors(bob: Any, q: int, p: float) -> np.ndarray:
    """Log-likelihood form of the q-ary-symmetric priors, max normalized to 0."""
    probs = qsc_symbol_priors(bob, q, p)
    with np.errstate(divide="ignore"):
        llr = np.log(probs)
    llr -= np.max(llr, axis=1, keepdims=True)
    return np.clip(llr, _NEG, 0.0)


def _top_nm(values: np.ndarray) -> np.ndarray:
    """Deterministic truncation: keep the nm largest *real* entries, clip the rest.

    Floor entries (== _NEG) never win a slot; ties among the nm-largest real
    values keep the lowest symbol indices (stable order), so the truncation
    is fully deterministic.
    """
    real = values > _NEG
    count = int(real.sum())
    if count <= NM:
        return values.copy()
    keep = np.flatnonzero(real)[np.argsort(-values[real], kind="stable")[:NM]]
    out = np.full(Q, _NEG, dtype=np.float64)
    out[keep] = values[keep]
    return out


def _llr_sum(*terms: np.ndarray) -> np.ndarray:
    """Sum LLR terms with EMS truncated-message semantics.

    A floor entry (== _NEG) means "symbol absent from this message's top-nm":
    it contributes *nothing* (standard EMS variable-node update), it must not
    drag the sum down.  Only real entries are added, so an extension edge
    that starts floored never drowns the prior signal.
    """
    out = np.zeros_like(terms[0])
    for term in terms:
        out = out + np.where(term > _NEG, term, 0.0)
    return np.where(np.isnan(out), _NEG, out)


def _reconstruct_llr(state: DecoderState, matrices: Mapping[int, Any]) -> list[np.ndarray]:
    """Complete LLR posteriors for the EMS policy."""
    priors = _llr_priors(state.bob, Q, state.p)
    _, variables = _edges(matrices[state.active_checks])
    out = []
    for variable, prior in enumerate(priors):
        out.append(_llr_sum(prior, *(state.messages[edge] for edge in variables[variable])))
    return out


def reconstruct_beliefs(state: DecoderState, matrices: Mapping[int, Any]) -> list[np.ndarray]:
    """Complete product (sched) or LLR posterior (ems); never reuses a stage cache."""
    if state.policy_id == "nbldpc_v5c_ems":
        return _reconstruct_llr(state, matrices)
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


def _damping(iteration: int) -> float:
    """Frozen damping schedule: quartiles of the 12-iteration stage."""
    return SCHEDULE[min((int(iteration) - 1) // 4, 2)]


def _run_sched(state: DecoderState, matrices: Mapping[int, Any], *, iterations: int = STAGE_ITERATIONS) -> dict[str, Any]:
    """Row-layered probability-domain FFT-QSPA with the frozen damping schedule.

    With a constant lambda of .75 this is byte-identical to the v4 warm
    decoder on identical inputs (v4's frozen update formula is the same
    ``v3._check_update_qspa`` plus the same damping blend).
    """
    if not 1 <= int(iterations) <= STAGE_ITERATIONS:
        return _result("aborted_resource_limit", q=Q, n=N, check_count=state.active_checks, reason="stage_iterations")
    field = GF2mField.create(Q); rows, variables = _edges(matrices[state.active_checks])
    priors = qsc_symbol_priors(state.bob, Q, state.p)
    try:
        for it in range(1, int(iterations) + 1):
            lam = _damping(it)
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
                    updated = _normalise(lam * fresh + (1.0 - lam) * state.messages[r, v])
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


def _gf_mul(values: np.ndarray, coef: int, field: GF2mField) -> np.ndarray:
    """Vectorized GF(2^m) multiplication for the permutation step (coef in symbols)."""
    if coef == 1:
        return values
    if coef == 0:
        return np.zeros_like(values)
    log = np.asarray(field._log, dtype=np.int64)
    exp = np.asarray(field._exp, dtype=np.int64)
    out = exp[(log[values] + log[coef]) % (field.q - 1)]
    return np.where(values == 0, 0, out)


def _ems_check_update(state: DecoderState, matrices: Mapping[int, Any], row_edges: list[tuple[tuple[int, int], ...]],
                      variables: list[list[tuple[int, int]]], *, r: int, field: GF2mField) -> None:
    """Min-sum check update (EMS) for one check row, alpha-corrected.

    Messages are truncated to the frozen ``nm=64`` most reliable symbols and
    kept deterministically sorted.  The min-plus convolution runs over the
    truncated symbol sets only, so complexity is bounded by
    O(dc * nm^2) per row (row weight dc <= 6).
    """
    edges = row_edges[r]
    priors = _llr_priors(state.bob, Q, state.p)
    alpha = ALPHA
    for target, (v, _) in enumerate(edges):
        # extrinsic for (r, v): prior + all check messages except this edge
        ext = _llr_sum(priors[v], *(state.messages[edge] for edge in variables[v] if edge != (r, v)))
        others = []
        for u, (other_v, coef) in enumerate(edges):
            if u == target:
                continue
            # variable->check message: prior plus every check message except
            # the one on this edge (layered EMS extrinsic).
            m = _llr_sum(priors[other_v],
                         *(state.messages[edge] for edge in variables[other_v] if edge != (r, other_v)))
            if coef != 1:
                # permutation: message over coefficient-scaled symbols
                perm = np.empty_like(m)
                perm[_gf_mul(np.arange(Q, dtype=np.int64), coef, field)] = m
                m = perm
            others.append(m)
        # min-sum convolution of the truncated other messages: LLR values are
        # largest-is-most-likely, so the check message is the *maximum* total
        # reliability over all coefficient-consistent combinations.  The
        # convolution accumulator stays on the full GF(q) domain (truncating
        # it would drop the correct combination's syndrome symbol); only the
        # final check message is truncated to nm.
        acc = None
        for m in others:
            top = _top_nm(m)
            if acc is None:
                acc = top
                continue
            a_idx = np.flatnonzero(acc > _NEG)
            b_idx = np.flatnonzero(top > _NEG)
            if a_idx.size == 0 or b_idx.size == 0:
                acc = np.full(Q, _NEG, dtype=np.float64)
                break
            comb = acc[a_idx][:, None] + top[b_idx][None, :]  # (na, nb)
            syms = (a_idx[:, None] ^ b_idx[None, :]).astype(np.int64)  # GF(2^m) addition is XOR
            best = np.full(Q, _NEG, dtype=np.float64)
            np.maximum.at(best, syms.ravel(), comb.ravel())
            # full-domain accumulator, never truncated mid-convolution: the
            # correct combination's syndrome symbol may rank below the top-nm
            # at intermediate steps, so truncating here loses it permanently.
            acc = best
        if acc is None:
            acc = np.full(Q, _NEG, dtype=np.float64)
        # map the accumulated syndrome-domain cost back to the target variable
        # domain: msg[a] = acc[syndrome ^ (h_t * a)]; alpha-corrected.
        shifted = acc[np.arange(Q, dtype=np.int64) ^ int(state.syndrome[r])]
        h_t = edges[target][1]
        if h_t != 1:
            # take values: msg[a] = shifted[h_t * a]
            shifted = shifted[_gf_mul(np.arange(Q, dtype=np.int64), h_t, field)]
        real = shifted > _NEG
        # keep the full-domain reliability vector (truncation is applied to
        # the *convolution inputs* below, never to the stored message, so the
        # correct symbol's evidence survives across iterations); the floor
        # marker is never scaled.
        state.messages[r, v] = np.where(real, np.clip(alpha * shifted, _NEG, 0.0), shifted)


def _run_ems(state: DecoderState, matrices: Mapping[int, Any], *, iterations: int = STAGE_ITERATIONS) -> dict[str, Any]:
    """LLR-domain Extended Min-Sum with nm=64 truncation and alpha=0.8."""
    if not 1 <= int(iterations) <= STAGE_ITERATIONS:
        return _result("aborted_resource_limit", q=Q, n=N, check_count=state.active_checks, reason="stage_iterations")
    field = GF2mField.create(Q); rows, variables = _edges(matrices[state.active_checks])
    priors = _llr_priors(state.bob, Q, state.p)
    try:
        for it in range(1, int(iterations) + 1):
            for r in range(len(rows)):
                _ems_check_update(state, matrices, rows, variables, r=r, field=field)
            beliefs = _reconstruct_llr(state, matrices)
            decoded = tuple(int(np.argmax(x)) for x in beliefs)
            if nonbinary_syndrome(matrices[state.active_checks], decoded, field) == state.syndrome:
                return _result("syndrome_consistent", q=Q, n=N, check_count=state.active_checks,
                               iterations=it, syndrome_consistent=True, decoded_symbols=decoded,
                               declared_dense_message_bytes=_declared_dense_bytes(N, len(state.messages), Q))
        return _result("decode_failed", q=Q, n=N, check_count=state.active_checks,
                       iterations=int(iterations), reason="iteration_limit")
    except (ArithmeticError, FloatingPointError, KeyError, ValueError, OverflowError):
        return _result("decoder_error", q=Q, n=N, check_count=state.active_checks, reason="numerical_or_field_failure")


def _run(state: DecoderState, matrices: Mapping[int, Any], *, iterations: int = STAGE_ITERATIONS) -> dict[str, Any]:
    if state.policy_id == "nbldpc_v5c_ems":
        return _run_ems(state, matrices, iterations=iterations)
    return _run_sched(state, matrices, iterations=iterations)


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
        state.messages = {(r, v): old[(r, v)].copy() if (r, v) in old else np.full(Q, 1.0 / Q if state.policy_id != "nbldpc_v5c_ems" else _NEG, dtype=np.float64)
                          for r, es in enumerate(rows) for v, _ in es}
        if state.policy_id == "nbldpc_v5c_ems":
            for r, es in enumerate(rows):
                for v, _ in es:
                    if (r, v) not in old:
                        state.messages[r, v][:min(NM, Q)] = 0.0
        reconstruct_beliefs(state, matrices)  # proves all active messages are used before the next stage
        return state
    except (TypeError, ValueError, OverflowError):
        return _result("invalid_input", q=Q, n=N, check_count=final, reason="extension_syndrome")


def run_stage(state: DecoderState, matrices: Mapping[int, Any], *, stage: int, stage_runner=None) -> dict[str, Any]:
    if not isinstance(stage, Integral) or int(stage) < 2:
        return _result("invalid_input", q=Q, n=N, check_count=state.active_checks, reason="stage")
    return _stage(state, matrices, int(stage), stage_runner)


def production_runner(state, matrices, stage):
    """Production adapter: the live v5c state machine is the decoder."""
    return _run(state, matrices)
