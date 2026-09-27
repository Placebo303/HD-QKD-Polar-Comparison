"""Binary SPA min-sum fallback (pure numpy; implementation-only, synthetic tiny).

Route-A explicit fallback for the M2LB arm when the frozen ``ldpc`` backend
(``ldpc.BpOsdDecoder``) is absent: syndrome-based binary min-sum on BSC
priors. Pure numpy, no new dependency (numba deliberately NOT required);
deterministic (fixed sweep order, no RNG); fail-closed on every input.

Claim ceiling: numbers produced through this backend carry the M2LB
``CLAIM_CEILING`` verbatim and are ``assumed``-prior, non-``ldpc`` results:
never comparable with, and never substitutable for, true-backend numbers.
See the comparison table in ``docs/research_cycles/M2-LAYEREDBIN-SYNTH/
APPENDIX_SPA_NUMPY_FALLBACK_COMPARISON.md`` (mirrored in the wrapper
docstring and the fallback test header).
"""

from __future__ import annotations

import math

import numpy as np

#: Exact backend identity literal (sidecar/log only, never an outcome key).
BACKEND_ID = "numpy-minsum-fallback (assumed, 非ldpc.BpOsdDecoder)"

#: BSC prior clamp interval for the channel LLR (mirrors the frozen backend).
_P_MIN, _P_MAX = 1e-4, 0.49

#: Pinning magnitude for degree-1 checks (finite stand-in for +/-inf).
_PIN_MAG = 1e6


def decode_error_numpy_min_sum(
    H: np.ndarray,
    syndrome_delta: np.ndarray,
    max_iter: int = 300,
    error_rate: float = 0.02,
) -> tuple[np.ndarray, bool, int]:
    """Estimate the binary error pattern with syndrome min-sum.

    Solves ``H @ err == syndrome_delta`` (mod 2) under a BSC(``error_rate``)
    prior: ``LLR0 = log((1-p)/p)`` with ``p`` clamped to ``[1e-4, 0.49]``.
    Check-to-variable min-sum update, variable-node accumulation, hard
    decision + syndrome early stop every round. Zero-error input converges
    with ``iters == 0`` (initial all-zero decision already consistent).

    Returns ``(err_hat, ok, iters)`` with ``ok`` iff ``H @ err == delta``.
    Every malformed input raises ``ValueError`` (fail closed, no defaults).
    """
    if isinstance(max_iter, bool) or not isinstance(max_iter, (int, np.integer)):
        raise ValueError("max_iter must be an int (fail closed)")
    max_iter = int(max_iter)
    if max_iter < 1:
        raise ValueError("max_iter must be >= 1 (fail closed)")
    if isinstance(error_rate, bool):
        raise ValueError("error_rate must be a float (fail closed)")
    try:
        p = float(error_rate)
    except Exception:  # noqa: BLE001 — fail closed, no defaults
        raise ValueError("error_rate not a float (fail closed)")
    if not math.isfinite(p):
        raise ValueError("error_rate not finite (fail closed)")
    p = min(max(p, _P_MIN), _P_MAX)
    try:
        h = np.asarray(H, dtype=np.uint8)
        d = np.asarray(syndrome_delta, dtype=np.uint8).reshape(-1)
    except Exception:  # noqa: BLE001 — fail closed, no defaults
        raise ValueError("H/syndrome_delta not array-like (fail closed)")
    if h.ndim != 2:
        raise ValueError("H must be 2-D (fail closed)")
    m, n = int(h.shape[0]), int(h.shape[1])
    if m < 1 or n < 1:
        raise ValueError("H must be non-empty (fail closed)")
    if bool(np.any((h != 0) & (h != 1))):
        raise ValueError("H must be binary (fail closed)")
    if d.shape != (m,):
        raise ValueError(f"syndrome len {d.shape} != H rows {m} (fail closed)")
    if bool(np.any((d != 0) & (d != 1))):
        raise ValueError("syndrome must be binary (fail closed)")

    llr0 = math.log((1.0 - p) / p)  # > 0: BSC prior favors 0
    chk_nb = [np.flatnonzero(h[c]).tolist() for c in range(m)]
    for c in range(m):
        if not chk_nb[c] and int(d[c]) != 0:
            raise ValueError(f"check {c} empty but syndrome 1 (fail closed)")

    v2c = np.where(h.astype(bool), llr0, 0.0)  # VN->CN, init to prior
    c2v = np.zeros((m, n), dtype=float)  # CN->VN accumulator
    tot = np.full(n, llr0, dtype=float)
    err = (tot < 0).astype(np.uint8)  # all-zero initial decision
    if bool(np.array_equal((h @ err) % 2, d)):
        return err, True, 0
    for it in range(1, max_iter + 1):
        for c in range(m):
            nb = chk_nb[c]
            if not nb:
                continue
            msgs = v2c[c, nb]
            signs = np.where(msgs < 0.0, -1.0, 1.0)  # exact 0 -> +1, deterministic
            mags = np.abs(msgs)
            flip = -1.0 if int(d[c]) == 1 else 1.0  # syndrome-sign rule
            for i, v in enumerate(nb):
                others = [k for k in range(len(nb)) if k != i]
                if not others:  # degree-1 check pins its sole variable
                    c2v[c, v] = flip * _PIN_MAG
                    continue
                s = flip
                for k in others:
                    s *= signs[k]
                c2v[c, v] = s * float(np.min(mags[others]))
        tot = np.full(n, llr0, dtype=float) + c2v.sum(axis=0)
        err = (tot < 0).astype(np.uint8)
        v2c = np.where(h.astype(bool), tot[None, :] - c2v, 0.0)  # extrinsic
        if bool(np.array_equal((h @ err) % 2, d)):
            return err, True, int(it)
    return err, False, int(max_iter)


__all__ = ["BACKEND_ID", "decode_error_numpy_min_sum"]
