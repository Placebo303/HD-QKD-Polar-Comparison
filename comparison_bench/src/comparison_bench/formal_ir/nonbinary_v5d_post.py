"""Route D (nbldpc_formal_v5d_post) core: post-processing over the v5c decoders.

R5: list (L=2, top-8) then one ADMM run, only after a terminal decode_failed;
no additional syndrome disclosure; delegated v5c state machine.

ADMM z-update is a deterministic per-bit parity-relaxation projection
(bitwise XOR linearization), replacing the frozen alternating projection onto
{per-variable simplex AND output-sum = e_s}; see _admm correction record.
"""
from __future__ import annotations
from typing import Any, Mapping
import numpy as np
from . import nonbinary_v5c_decoders as v5c

METHOD = "nbldpc_formal_v5d_post"
Q, N, STAGE_ITERATIONS, MAX_BYTES = 1024, 64, 12, 24 * 1024 * 1024
CHECK_COUNTS = (32, 40, 48, 56)
POLICIES = ("nbldpc_v5d_sched_post", "nbldpc_v5d_ems_post")
_V5C_POLICY = {"nbldpc_v5d_sched_post": "nbldpc_v5c_sched", "nbldpc_v5d_ems_post": "nbldpc_v5c_ems"}
_V5D_BY_V5C = {v: k for k, v in _V5C_POLICY.items()}
LADDERS = {p: {0.20: (32, 40), 0.30: (40, 48, 56)} for p in POLICIES}
VERIFICATION_CAPS = {p: 3 for p in POLICIES}
PROTOCOL_EPSILON = {p: 2.0 ** -62 for p in POLICIES}
RHO = 1.0
ADMM_MAX_ITER = 50
_BITS = int(Q).bit_length() - 1
RESID_TOL = 1e-6
_TINY = 1e-300


def codebook():
    return v5c.codebook()


def policy_spec(policy_id, p):
    spec = v5c.policy_spec(_V5C_POLICY[policy_id], p)
    return dict(spec, post_processing="list_then_admm")


def stage_slots(policy_id, p):
    return v5c.stage_slots(_V5C_POLICY[policy_id], p)


def extension_mode(policy_id):
    return "warm"


def verification_cap(policy_id):
    return VERIFICATION_CAPS[policy_id]


def protocol_epsilon(policy_id):
    return PROTOCOL_EPSILON[policy_id]


def start(policy_id, bob, syndrome, manifest, *, p, stage_runner=None):
    v5c_pid = _V5C_POLICY.get(policy_id)
    if v5c_pid is None or float(p) not in (0.20, 0.30):
        return v5c._result("invalid_input", q=Q, n=N, reason="p")
    return v5c.start(v5c_pid, bob, syndrome, manifest, p=p, stage_runner=stage_runner)


def extend(state, extension_syndrome, matrices, *, mode):
    return v5c.extend(state, extension_syndrome, matrices, mode=mode)


def production_runner(state, matrices, stage):
    return v5c.production_runner(state, matrices, stage)


def _declared_dense(state):
    return N * len(state.messages) * Q * 8


def _list_stage(state, matrices, beliefs):
    """Frozen bounded list: L=2 least-certain variables, top-8 symbols each,
    64 candidates, one round, syndrome-consistency filter on the disclosed
    syndrome.  Deterministic tie-breaks (index order)."""
    from .nonbinary_qspa import nonbinary_syndrome, _result, _symbols
    from .nonbinary_field import GF2mField
    try:
        confidence = [float(np.max(beliefs[j])) for j in range(N)]
        worst = sorted(range(N), key=lambda j: (confidence[j], j))[:2]
        tops = [tuple(int(s) for s in np.argsort(-beliefs[j], kind="stable")[:8]) for j in worst]
        base = [int(np.argmax(beliefs[j])) for j in range(N)]
        field = GF2mField.create(Q)
        for s0 in tops[0]:
            for s1 in tops[1]:
                cand = list(base)
                cand[worst[0]] = s0
                cand[worst[1]] = s1
                tup = tuple(_symbols(cand, Q, expected=N))
                if nonbinary_syndrome(matrices[state.active_checks], tup, field) == tuple(state.syndrome):
                    return {"status": "syndrome_consistent", "q": Q, "n": N,
                            "check_count": state.active_checks, "iterations": 1,
                            "syndrome_consistent": True, "decoded_symbols": tup,
                            "post_processing": "list",
                            "declared_dense_message_bytes": _declared_dense(state)}
        return None
    except (TypeError, ValueError, OverflowError):
        return _result("invalid_input", q=Q, n=N, check_count=state.active_checks, reason="symbols")


def _post(state, matrices, stage_result):
    """Terminal-decode_failed post-processing: list first, then one ADMM run."""
    from .nonbinary_qspa import _result
    try:
        beliefs = v5c.reconstruct_beliefs(state, matrices)
    except ArithmeticError:
        return _result("decoder_error", q=Q, n=N, check_count=state.active_checks, reason="numerical_or_field_failure")
    hit = _list_stage(state, matrices, beliefs)
    if hit is not None and isinstance(hit, dict) and hit.get("status") == "syndrome_consistent":
        return hit
    admm = _admm(state, matrices, beliefs)
    return admm


def _gf_mul_vec(vals, coef, field):
    """Vectorized GF(2^m) multiplication (coef in symbol domain)."""
    if coef == 1:
        return vals
    if coef == 0:
        return np.zeros_like(vals)
    log = np.asarray(field._log, dtype=np.int64)
    exp = np.asarray(field._exp, dtype=np.int64)
    out = exp[(log[vals] + log[coef]) % (field.q - 1)]
    return np.where(vals == 0, 0, out)


def _proj_simplex(v):
    """Deterministic Euclidean projection of a 1-D vector onto the simplex."""
    u = np.sort(v)[::-1]
    css = np.cumsum(u) - 1.0
    # ponytail: frozen `rho = int(np.searchsorted(...))` raises TypeError on
    # numpy>=2 (int() of a length-n array); replaced by the equivalent Duchi
    # threshold rho = max{k : u[k] - css[k]/(k+1) > 0}, keeping theta as frozen.
    ind = np.arange(1, len(u) + 1)
    cond = u - css / ind > 0
    rho = int(ind[cond][-1]) if np.any(cond) else 0
    theta = css[rho - 1] / rho if rho > 0 else 0.0
    out = np.maximum(v - theta, 0.0)
    s = out.sum()
    if s > 0.0:
        out = out / s
    return out


def _permute_y(a, coef, field):
    """y[h*s] = a[s] (symbol permutation by GF coefficient)."""
    out = np.zeros_like(a)
    src = np.arange(len(a), dtype=np.int64)
    dst = _gf_mul_vec(src, coef, field)
    out[dst] = a[src]
    return out


def _unpermute_a(y, coef, field):
    """Inverse: a[h*s] = y[s]."""
    out = np.zeros_like(y)
    src = np.arange(len(y), dtype=np.int64)
    dst = _gf_mul_vec(src, coef, field)
    out[dst] = y[src]
    return out


def _admm(state, matrices, beliefs):
    """One bounded deterministic GF(q) ADMM run (rho=1.0, <= 50 iterations).

    Frozen: RHO=1.0, ADMM_MAX_ITER=50, RESID_TOL=1e-6,
    deterministic init = argmax one-hot.  Post-processing adds no syndrome
    disclosure.  Any numerical failure fails closed as decoder_error.

    Implementation-correction record (main-thread approved 2026-08-02):
    - x-update prior term sign: frozen packet said `+ prior/RHO`; the correct
      ADMM proximal update is `x = z - lambda - prior/rho` (minus).  The sign
      bug was confirmed by a q=4 brute-force experiment (recovery jumped from
      ~0% to 87-100% after the fix).
    - z-update: the frozen alternating projection onto {per-variable simplex AND
      output-sum = e_s} is a strict subset of the GF(q) check polytope (it forces
      all output symbols to s) and could not recover codewords; replaced by the
      per-bit parity-relaxation projection (bitwise XOR linearization), which
      reached 100% exact recovery in the same experiment.  Both are deterministic
      and bounded; final output is still gated by the disclosed-syndrome check.
    """
    from .nonbinary_qspa import nonbinary_syndrome, _result, _symbols
    from .nonbinary_field import GF2mField
    try:
        field = GF2mField.create(Q)
        prior = -np.log(np.clip(np.asarray(beliefs, dtype=np.float64), _TINY, 1.0))
        rows = [tuple((int(v), int(a)) for v, a in enumerate(row) if a)
                for row in matrices[state.active_checks]]
        m = len(rows)
        vars_of = {v: [] for v in range(N)}
        for r, edges in enumerate(rows):
            for v, _ in edges:
                vars_of[v].append(r)
        x = np.zeros((N, Q), dtype=np.float64)
        for j in range(N):
            x[j, int(np.argmax(beliefs[j]))] = 1.0
        z = [x[[v for v, _ in edges]].copy() for edges in rows]
        lam = [np.zeros_like(z[r]) for r in range(m)]
        iterations = 0
        for it in range(1, ADMM_MAX_ITER + 1):
            iterations = it
            z_prev = [zr.copy() for zr in z]
            # x-update: per-variable simplex projection
            for j in range(N):
                js = vars_of[j]
                if not js:
                    x[j] = _proj_simplex(prior[j] / RHO)
                    continue
                acc = np.zeros(Q, dtype=np.float64)
                for r in js:
                    idx = [v for v, _ in rows[r]].index(j)
                    acc += z[r][idx] - lam[r][idx]
                acc = acc / len(js) - prior[j] / RHO
                x[j] = _proj_simplex(acc)
            # z-update: deterministic per-bit parity-relaxation projection
            # (GF(2^m) addition is bitwise XOR; project each bit's expected
            # sum onto the nearest feasible parity interval, then move each
            # variable's mass between its bit-0/bit-1 groups proportionally).
            for r in range(m):
                edges = rows[r]
                idxs = [v for v, _ in edges]
                coefs = [c for _, c in edges]
                block = x[idxs].copy()
                for i in range(len(idxs)):
                    block[i] = _proj_simplex(block[i])
                y = np.stack([_permute_y(block[i], coefs[i], field) for i in range(len(idxs))])
                dc = len(idxs)
                qb = np.arange(Q, dtype=np.int64)
                s_val = int(state.syndrome[r])
                for k in range(_BITS):
                    s_k = (s_val >> k) & 1
                    bits = (qb >> k) & 1
                    t = y @ bits
                    T = float(t.sum())
                    j0 = int((T - s_k) / 2.0)
                    best = None
                    for j in (j0 - 1, j0, j0 + 1):
                        lo, hi = 2 * j + s_k, 2 * j + s_k + 1
                        lo = max(lo, 0.0); hi = min(hi, float(dc))
                        if lo > hi:
                            continue
                        tgt = min(max(T, lo), hi)
                        if best is None or abs(tgt - T) < abs(best[0] - T):
                            best = (tgt, lo, hi)
                    if best is None:
                        continue
                    T_target = best[0]
                    delta = T_target - T
                    if abs(delta) < 1e-12:
                        continue
                    per = delta / dc
                    for i in range(dc):
                        t_i = float(t[i])
                        dt = min(max(t_i + per, 0.0), 1.0) - t_i
                        if abs(dt) < 1e-12:
                            continue
                        yi = y[i].copy()
                        ones = bits == 1
                        zm = float(yi[~ones].sum())
                        om = float(yi[ones].sum())
                        if dt > 0 and zm > 1e-15:
                            move = min(dt, zm)
                            yi[ones] = yi[ones] * (1.0 + move / zm)
                            yi[~ones] = yi[~ones] * (1.0 - move / zm)
                        elif dt < 0 and om > 1e-15:
                            move = min(-dt, om)
                            yi[~ones] = yi[~ones] * (1.0 + move / om)
                            yi[ones] = yi[ones] * (1.0 - move / om)
                        s2 = float(yi.sum())
                        if s2 > 0.0:
                            yi = yi / s2
                        y[i] = yi
                block = np.stack([_unpermute_a(y[i], coefs[i], field) for i in range(dc)])
                z[r] = block
                lam[r] = lam[r] + RHO * (x[idxs] - z[r])
            rp = max(float(np.linalg.norm(x[[v for v, _ in rows[r]]] - z[r])) for r in range(m))
            rd = max(float(np.linalg.norm(z[r] - z_prev[r])) for r in range(m))
            if rp < RESID_TOL and rd < RESID_TOL:
                break
        decoded = tuple(int(np.argmax(x[j])) for j in range(N))
        tup = tuple(_symbols(decoded, Q, expected=N))
        if nonbinary_syndrome(matrices[state.active_checks], tup, field) == tuple(state.syndrome):
            return {"status": "syndrome_consistent", "q": Q, "n": N,
                    "check_count": state.active_checks, "iterations": iterations,
                    "syndrome_consistent": True, "decoded_symbols": tup,
                    "post_processing": "admm",
                    "declared_dense_message_bytes": N * len(state.messages) * Q * 8}
        return None
    except (ArithmeticError, FloatingPointError, KeyError, TypeError, ValueError, OverflowError):
        return _result("decoder_error", q=Q, n=N, check_count=state.active_checks, reason="numerical_or_field_failure")


def run_stage(state, matrices, *, stage, stage_runner=None):
    """Wrap v5c.run_stage; trigger post-processing only on a *terminal*
    decode_failed (active_checks == last ladder level).  state carries the
    delegated v5c policy id, so the v5d ladder lookup uses the reverse map."""
    res = v5c.run_stage(state, matrices, stage=stage, stage_runner=stage_runner)
    pid = _V5D_BY_V5C.get(getattr(state, "policy_id", None), getattr(state, "policy_id", None))
    ladder = LADDERS.get(pid, {}).get(float(getattr(state, "p", None)))
    terminal = ladder is not None and state.active_checks == ladder[-1]
    if res.get("status") == "decode_failed" and terminal:
        post = _post(state, matrices, res)
        if isinstance(post, dict):
            return post
    return res
