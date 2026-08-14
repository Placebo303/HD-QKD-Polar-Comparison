"""V14 frozen channel model for the q=1024 efficiency gate
(``formal-nonbinary-ldpc-v14-efficiency-gate``, additive layer).

The channel prior is an empirical symbol-difference distribution
``w[d] = P(alice XOR bob = d)`` over GF(1024), recomputed **read-only** from
the V13 characterization frames (D01 aggregate: all 1024 bins are recomputed
here because the D01 package only persists the 32-bin bucket).  This
recomputation is a D01-neighbour aggregation; it never executes a decoder.

Frozen rule (design.md section 1):

- ``w_emp`` = normalized 1024-bin histogram of ``alice XOR bob`` over all
  frame symbols;
- ``w' = (1 - lam) * w_emp + lam * u``, ``u`` the GF(1024) uniform
  distribution, ``lam = 1e-3`` (floor purpose; frozen, never tuned);
- cross-fit discipline: only characterization frames fit the model;
  development/audit frames and audit truth never participate;
- ``entropy_bits(w) = -sum_{w>0} w * log2(w)`` (bit units);
- folding homomorphism ``phi_m(d) = d mod 2^m`` (XOR bit-order preserving):
  ``w_small[d'] = sum_{a : phi_m(a) = d'} w[a]``;
- Channel-model doc schema: ``nbldpc_v14_channel_model_v1``, labelled
  ``diagnostic_only``.

The real characterization-frame loader is imported **lazily** inside
:func:`load_production_frames` and requires the explicit
``production_authorized`` flag; the verifier and test lanes never enter a real
source loader.
"""
from __future__ import annotations

import math
from numbers import Integral
from typing import Any

import numpy as np

#: Schema of the V14 structured channel model doc.
CHANNEL_MODEL_SCHEMA = "nbldpc_v14_channel_model_v1"

#: Default GF cardinality for the full-purpose channel prior.
Q = 1024

#: Frozen smoothing floor: ``w' = (1-lam)*w_emp + lam/q`` (design section 1).
SMOOTHING_LAMBDA = 1e-3

#: The 128-frame / 32768-symbol characterization aggregate is 1024 bins.
Q_BINS = 1024

#: Frozen default folding field sizes (design section 1 m in {2,3,4}).
DEFAULT_M_BITS = (2, 3, 4)


def build_diff_distribution(frames: Any, q: int = Q) -> np.ndarray:
    """Normalized 1024-bin histogram of ``alice XOR bob`` over all frame
    symbols.  ``frames`` is an iterable of dicts with ``'alice'``/``'bob'``
    numpy integer arrays (equal length per frame).
    """
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or int(q) & (int(q) - 1):
        raise ValueError("q must be a power of two >= 2")
    q = int(q)
    if frames is None:
        raise ValueError("frames must be provided")
    counts = np.zeros(q, dtype=np.float64)
    total = 0
    for frame in frames:
        alice = np.asarray(frame["alice"])
        bob = np.asarray(frame["bob"])
        if alice.shape != bob.shape or alice.size == 0:
            raise ValueError("frame alice/bob arrays must be equal-length and non-empty")
        if not np.all(np.isfinite(alice)) or not np.all(np.isfinite(bob)):
            raise ValueError("frame symbols must be finite")
        if np.any(alice < 0) or np.any(alice >= q) or np.any(bob < 0) or np.any(bob >= q):
            raise ValueError("frame symbols must lie in [0, q)")
        counts += np.bincount((np.asarray(alice, dtype=np.int64)
                               ^ np.asarray(bob, dtype=np.int64)), minlength=q).astype(np.float64)
        total += int(alice.size)
    if total <= 0:
        raise ValueError("no frame symbols to aggregate")
    normalized = counts / total
    if not np.all(np.isfinite(normalized)) or not math.isclose(float(normalized.sum()), 1.0,
                                                                abs_tol=1e-9):
        raise ValueError("difference histogram must be finite and sum to 1")
    return normalized


def smooth(w_emp: Any, q: int = Q, lam: float = SMOOTHING_LAMBDA) -> np.ndarray:
    """``w' = (1 - lam) * w_emp + lam / q`` (frozen smoothing floor)."""
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or int(q) & (int(q) - 1):
        raise ValueError("q must be a power of two >= 2")
    q = int(q)
    if isinstance(lam, bool) or not isinstance(lam, (int, float)) \
            or not math.isfinite(float(lam)) or not 0.0 <= float(lam) < 1.0:
        raise ValueError("lam must be finite in [0, 1)")
    w = np.asarray(w_emp, dtype=np.float64)
    if w.shape != (q,) or not np.all(np.isfinite(w)) or np.any(w < 0.0):
        raise ValueError("w_emp must be a finite non-negative length-q vector")
    total = float(w.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("w_emp must have positive total mass")
    if not math.isclose(total, 1.0, abs_tol=1e-6):
        w = w / total  # tolerate a tiny rounding drift on caller-normalized input
    return (1.0 - float(lam)) * w + float(lam) / float(q)


def entropy_bits(w: Any) -> float:
    """Shannon entropy in bits: ``- sum_{w>0} w * log2(w)``."""
    vector = np.asarray(w, dtype=np.float64)
    if vector.ndim != 1 or not np.all(np.isfinite(vector)) or np.any(vector < 0.0):
        raise ValueError("w must be a finite non-negative vector")
    total = float(vector.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("w must have positive total mass")
    if not math.isclose(total, 1.0, abs_tol=1e-6):
        vector = vector / total
    positive = vector > 0.0
    if not positive.any():
        return 0.0
    return float(-np.sum(vector[positive] * np.log2(vector[positive])))


def fold(w: Any, m_bits: int) -> np.ndarray:
    """Fold ``w`` (over GF(2**log2(len(w)))) down to GF(2**m_bits) via the
    bit-order-preserving homomorphism ``phi(d) = d mod 2^m``:
    ``w_small[d'] = sum_{a : (a % 2**m) == d'} w[a]``.
    """
    if isinstance(m_bits, bool) or not isinstance(m_bits, Integral) or int(m_bits) < 1:
        raise ValueError("m_bits must be a positive integer")
    m_bits = int(m_bits)
    vector = np.asarray(w, dtype=np.float64)
    if vector.ndim != 1 or vector.size == 0 or vector.size & (vector.size - 1):
        raise ValueError("w must be a non-empty power-of-two-length vector")
    if not np.all(np.isfinite(vector)) or np.any(vector < 0.0):
        raise ValueError("w must be a finite non-negative vector")
    q = vector.size
    small_q = 1 << m_bits
    if small_q > q:
        raise ValueError("m_bits must not exceed log2(len(w))")
    if small_q == q:
        return vector.copy()
    w_small = np.zeros(small_q, dtype=np.float64)
    for a in range(q):
        w_small[a % small_q] += vector[a]
    total = float(w_small.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("folded distribution has invalid total mass")
    if not math.isclose(total, 1.0, abs_tol=1e-6):
        w_small = w_small / total
    return w_small


def _validate_qsc_consistent(w_small: Any, q_small: int, p: float) -> bool:
    """QSC-limit check (test convenience): whether a folded small-q
    distribution equals an exact q-ary symmetric channel with the same ``p``."""
    vector = np.asarray(w_small, dtype=np.float64)
    if vector.shape != (q_small,):
        return False
    if not math.isclose(float(vector.sum()), 1.0, abs_tol=1e-9):
        return False
    if not math.isclose(float(vector[0]), 1.0 - float(p), abs_tol=1e-9):
        return False
    off = float(p) / (q_small - 1.0)
    return all(math.isclose(float(vector[i]), off, abs_tol=1e-9)
               for i in range(1, q_small))


def build_channel_model_doc(w_smooth: Any, frames_used: int, *,
                            m_bits: tuple[int, ...] = DEFAULT_M_BITS,
                            run_id: str = "v14_channel") -> dict[str, Any]:
    """Build the ``v14_structured_channel_model.json`` doc (schema
    ``nbldpc_v14_channel_model_v1``).

    ``w_smooth`` is the smoothed full-purpose (q=1024) distribution; the doc
    embeds the frozen lambda, ``entropy_bits``, and the per-m folding (q,
    ``w_small``, ``entropy_bits``).  ``diagnostic_only`` is always true.
    """
    w = np.asarray(w_smooth, dtype=np.float64)
    if w.shape != (Q_BINS,) or not np.all(np.isfinite(w)) or np.any(w < 0.0):
        raise ValueError("w_smooth must be a finite non-negative 1024-vector")
    if not math.isclose(float(w.sum()), 1.0, abs_tol=1e-6):
        w = w / float(w.sum())
    if not isinstance(frames_used, Integral) or int(frames_used) < 0:
        raise ValueError("frames_used must be a non-negative integer")
    if not m_bits:
        raise ValueError("m_bits must be non-empty")
    folding = []
    for m in m_bits:
        if isinstance(m, bool) or not isinstance(m, Integral) or int(m) < 1:
            raise ValueError("m_bits entries must be positive integers")
        m = int(m)
        w_small = fold(w, m)
        folding.append({
            "m_bits": m,
            "q": int(1 << m),
            "w_small": [float(x) for x in w_small],
            "entropy_bits": float(entropy_bits(w_small)),
        })
    return {
        "schema": CHANNEL_MODEL_SCHEMA,
        "run_id": str(run_id),
        "q": Q_BINS,
        "smoothing_lambda": SMOOTHING_LAMBDA,
        "w": [float(x) for x in w],
        "entropy_bits": float(entropy_bits(w)),
        "folding": folding,
        "fit_frames": int(frames_used),
        "fit_source": "v13 characterization frames",
        "diagnostic_only": True,
    }


def load_production_frames(*, production_authorized: bool = False,
                           discovery_root: str | None = None,
                           run_id: str = "v14_channel",
                           stratum: str = "d1024_bw200") -> list[dict[str, Any]]:
    """Lazy production loader for the V13 characterization frames.

    Imports ``nonbinary_v13_diagnostics`` lazily (never at import time),
    builds the production role ledger from ``discovery_root`` (default
    ``comparison_bench/outputs_comparison/formal_ir_methods``) and returns the
    characterization frames for the frozen stratum ``d1024_bw200``.  This is
    execute-only: a call without ``production_authorized=True`` is a hard stop.
    """
    if not production_authorized:
        raise ValueError("load_production_frames requires production_authorized=True")
    from . import nonbinary_v13_diagnostics as diagnostics

    if discovery_root is None:
        import os
        _here = os.path.dirname(os.path.abspath(__file__))  # .../formal_ir
        discovery_root = os.path.abspath(os.path.join(
            _here, "..", "..", "..", "..", "comparison_bench",
            "outputs_comparison", "formal_ir_methods"))
    ledger = diagnostics.build_production_ledger(discovery_root, run_id=run_id)
    return diagnostics.load_production_characterization_frames(ledger, stratum=stratum)
