"""A3 ``GF(q)`` LDPC for the C-1 comparison batch (OP1).

Frozen packet ``docs/research_cycles/C-BATCH/C1_PACKET.md`` §3.2
(``k = 1, 2, 3`` -> ``q = 3, 5, 7``; any prime ``q >= 3`` is accepted
since the field arithmetic below only needs primality).

Construction: the binary skeleton comes from
``msd_peg_code.build_peg_code`` (deterministic PEG edge placement, no
RNG inside) —出处: ``comparison_bench/src/comparison_bench/formal_ir/
msd_peg_code.py`` — and every skeleton edge is then assigned an
independent uniform nonzero field element from ``{1..q-1}`` drawn with
``numpy.random.default_rng(seed)``. No existing ``GF(32)`` codec is
reused or moved here; the main path below is new code. The stored matrix
is structurally sparse (variable degree 3); it is held dense because
this batch only decodes ``N <= 256``.

Conventions: codewords ``a`` are length-``n`` vectors over ``F_q``; the
syndrome is ``s = H·a mod q``; the channel is additive,
``b = a + e mod q`` with ``prior_g[e] = P(symbol error = e)``. Success
is declared by exact syndrome match ``H·ahat = s``; the runner re-checks
success with its tag, not this module. Decode failure returns ``None``
(never raises); only malformed inputs raise ``ValueError``.

Disclosure cost: ``bits = ceil(m·log2(q))`` symbol-to-bit conversion of
the ``m`` syndrome symbols; ``m·log2(q)`` is never an integer for
``q in {3, 5, 7}`` (``log2`` is irrational there), so the ceiling always
rounds up by a fraction of a bit — noted per the packet.

Decoder: log-domain sum-product (QSPA). Variable updates stay in the log
domain with max-normalization; check updates run forward-backward cyclic
convolutions in the probability domain with per-step sum-normalization
and a ``1e-300`` floor before taking logs — the minimal overflow
handling needed. Check-node cost is ``O(d·q²)`` per check, fine for
``q <= 7``.
"""

from __future__ import annotations

import math
import operator
from dataclasses import dataclass, field

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (
    build_peg_code,
)

__all__ = ["GFqLDPCCode", "construct", "disclose", "decode"]

_LOG_FLOOR = 1e-300
_DEFAULT_MAX_ITER = 50
_VARIABLE_DEGREE = 3


def _explicit_integer(value: object, name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer, not bool")
    try:
        return operator.index(value)
    except TypeError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _is_prime(q: int) -> bool:
    if q < 2:
        return False
    if q % 2 == 0:
        return q == 2
    r = int(math.isqrt(q))
    for d in range(3, r + 1, 2):
        if q % d == 0:
            return False
    return True


def _cyclic_conv(u: np.ndarray, v: np.ndarray, q: int) -> np.ndarray:
    """Cyclic convolution ``(u * v)[k] = Σ_a u[a]·v[(k-a) mod q]``."""
    out = np.zeros(q)
    for a in range(q):
        ua = u[a]
        if ua == 0.0:
            continue
        for b in range(q):
            out[(a + b) % q] += ua * v[b]
    return out


@dataclass
class GFqLDPCCode:
    """A ``GF(q)`` LDPC code: parity-check matrix plus adjacency lists."""

    n: int
    m: int
    q: int
    seed: object
    H: np.ndarray
    variable_degree: int = _VARIABLE_DEGREE
    # Per-variable ``[(check, weight)]`` and per-check ``[(var, weight)]``.
    var_neighbors: list[list[tuple[int, int]]] = field(default_factory=list)
    chk_neighbors: list[list[tuple[int, int]]] = field(default_factory=list)

    def disclose(self, a_symbols: object) -> tuple[np.ndarray, int]:
        """See module-level :func:`disclose`."""
        return disclose(self, a_symbols)

    def decode(
        self,
        b_symbols: object,
        syndrome: object,
        prior_g: object,
        max_iter: int = _DEFAULT_MAX_ITER,
    ) -> np.ndarray | None:
        """See module-level :func:`decode`."""
        return decode(self, b_symbols, syndrome, prior_g, max_iter)


def construct(n: int, m: int, q: int, seed: object) -> GFqLDPCCode:
    """Build a deterministic ``GF(q)`` sparse parity-check code.

    Skeleton: ``msd_peg_code.build_peg_code`` with variable degree
    ``min(3, m)``; nonzero entries: i.i.d. uniform over ``{1..q-1}``
    from ``default_rng(seed)``. Same ``seed`` reproduces the same ``H``.
    Requires ``1 <= m < n`` and prime ``q >= 3``.
    """
    n = _explicit_integer(n, "n")
    m = _explicit_integer(m, "m")
    q = _explicit_integer(q, "q")
    if n < 2:
        raise ValueError("n must be at least 2")
    if not 1 <= m < n:
        raise ValueError("m must satisfy 1 <= m < n")
    if q < 3 or not _is_prime(q):
        raise ValueError("q must be a prime >= 3")
    degree = min(_VARIABLE_DEGREE, m)
    skeleton = build_peg_code(n=n, m=m, variable_degree=degree)
    coo = skeleton.parity_check_matrix.tocoo()
    rng = np.random.default_rng(seed)
    values = rng.integers(1, q, size=coo.nnz)
    H = np.zeros((m, n), dtype=np.int64)
    H[coo.row, coo.col] = values
    var_neighbors: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    chk_neighbors: list[list[tuple[int, int]]] = [[] for _ in range(m)]
    for c, v, w in zip(coo.row.tolist(), coo.col.tolist(), values.tolist()):
        var_neighbors[v].append((c, w))
        chk_neighbors[c].append((v, w))
    return GFqLDPCCode(
        n=n,
        m=m,
        q=q,
        seed=seed,
        H=H,
        variable_degree=degree,
        var_neighbors=var_neighbors,
        chk_neighbors=chk_neighbors,
    )


def _as_symbol_vector(values: object, length: int, q: int, name: str) -> np.ndarray:
    arr = np.asarray(values, dtype=np.int64)
    if arr.shape != (length,):
        raise ValueError(f"{name} must have shape ({length},)")
    if arr.min() < 0 or arr.max() >= q:
        raise ValueError(f"{name} entries must lie in [0, {q})")
    return arr


def _as_prior(prior_g: object, q: int) -> np.ndarray:
    g = np.asarray(prior_g, dtype=float)
    if g.shape != (q,):
        raise ValueError(f"prior_g must have shape ({q},)")
    if np.any(~np.isfinite(g)) or np.any(g < 0.0):
        raise ValueError("prior_g must be finite and nonnegative")
    total = g.sum()
    if total <= 0.0:
        raise ValueError("prior_g must have positive total mass")
    return g / total


def disclose(code: GFqLDPCCode, a_symbols: object) -> tuple[np.ndarray, int]:
    """Disclose the syndrome of ``a_symbols`` under ``code``.

    Returns ``(syndrome_symbols, bits)`` with ``syndrome = H·a mod q``
    and ``bits = ceil(m·log2(q))``.
    """
    a = _as_symbol_vector(a_symbols, code.n, code.q, "a_symbols")
    syndrome = (code.H @ a) % code.q
    bits = int(math.ceil(code.m * math.log2(code.q)))
    return (syndrome.astype(np.int64), bits)


def _to_log_domain(prob: np.ndarray) -> np.ndarray:
    msg = np.log(np.maximum(prob, _LOG_FLOOR))
    return msg - msg.max()


def _check_to_var(
    incoming: list[np.ndarray],
    weights: list[int],
    syndrome_value: int,
    q: int,
) -> list[np.ndarray]:
    """Forward-backward check-node update; returns one message per edge."""
    d = len(incoming)
    # Weighted permutation: z = w·a  =>  Pz[z] = Pv[w^{-1}·z].
    weighted: list[np.ndarray] = []
    for msg, w in zip(incoming, weights):
        prob = np.exp(msg - msg.max())
        prob = prob / prob.sum()
        winv = pow(w, q - 2, q)
        pz = np.zeros(q)
        for z in range(q):
            pz[z] = prob[(winv * z) % q]
        weighted.append(pz)
    forward: list[np.ndarray] = [np.zeros(q) for _ in range(d + 1)]
    forward[0][0] = 1.0
    for t in range(d):
        conv = _cyclic_conv(forward[t], weighted[t], q)
        forward[t + 1] = conv / conv.sum()
    backward: list[np.ndarray] = [np.zeros(q) for _ in range(d + 1)]
    backward[d][0] = 1.0
    for t in range(d - 1, -1, -1):
        conv = _cyclic_conv(backward[t + 1], weighted[t], q)
        backward[t] = conv / conv.sum()
    out: list[np.ndarray] = []
    for t in range(d):
        joint = _cyclic_conv(forward[t], backward[t + 1], q)
        joint = joint / joint.sum()
        # Edge t carries z_t with Σ z = s: message for z is joint[s - z].
        mz = np.zeros(q)
        for z in range(q):
            mz[z] = joint[(syndrome_value - z) % q]
        w = weights[t]
        c2v = np.zeros(q)
        for a in range(q):
            c2v[a] = mz[(w * a) % q]
        c2v = c2v / c2v.sum()
        out.append(_to_log_domain(c2v))
    return out


def decode(
    code: GFqLDPCCode,
    b_symbols: object,
    syndrome: object,
    prior_g: object,
    max_iter: int = _DEFAULT_MAX_ITER,
) -> np.ndarray | None:
    """Decode ``b = a + e`` given ``syndrome = H·a`` and error prior ``prior_g``.

    Log-domain sum-product (QSPA). Returns the recovered word when its
    syndrome matches exactly, else ``None`` after ``max_iter`` rounds.
    """
    b = _as_symbol_vector(b_symbols, code.n, code.q, "b_symbols")
    s = _as_symbol_vector(syndrome, code.m, code.q, "syndrome")
    g = _as_prior(prior_g, code.q)
    max_iter = _explicit_integer(max_iter, "max_iter")
    if max_iter < 0:
        raise ValueError("max_iter must be nonnegative")
    q = code.q
    log_g = np.log(np.maximum(g, _LOG_FLOOR))
    # Channel log-prior per variable: P(a = x | b) ∝ g[(b - x) mod q].
    channel = np.zeros((code.n, q))
    for i in range(code.n):
        for x in range(q):
            channel[i, x] = log_g[(int(b[i]) - x) % q]
        channel[i] -= channel[i].max()

    def hard_decision(posterior: np.ndarray) -> np.ndarray:
        return np.argmax(posterior, axis=1).astype(np.int64)

    def syndrome_ok(word: np.ndarray) -> bool:
        return bool(np.array_equal((code.H @ word) % q, s))

    # Round 0: channel hard decision already satisfies noiseless inputs.
    post0 = channel.copy()
    word0 = hard_decision(post0)
    if syndrome_ok(word0):
        return word0

    # v2c[i]: {check -> log message}; c2v[j]: {var -> log message}.
    v2c: list[dict[int, np.ndarray]] = [{} for _ in range(code.n)]
    for i in range(code.n):
        for (j, _w) in code.var_neighbors[i]:
            v2c[i][j] = channel[i].copy()
    for _ in range(max_iter):
        # Check-node updates.
        c2v: list[dict[int, np.ndarray]] = [{} for _ in range(code.m)]
        for j in range(code.m):
            edges = code.chk_neighbors[j]
            if not edges:
                continue
            incoming = [v2c[i][j] for (i, _w) in edges]
            weights = [_w for (_i, _w) in edges]
            msgs = _check_to_var(incoming, weights, int(s[j]), q)
            for (i, _w), msg in zip(edges, msgs):
                c2v[j][i] = msg
        # Variable-node updates + hard decision.
        posterior = np.zeros((code.n, q))
        for i in range(code.n):
            acc = channel[i].copy()
            for (j, _w) in code.var_neighbors[i]:
                if i in c2v[j]:
                    acc = acc + c2v[j][i]
            acc -= acc.max()
            posterior[i] = acc
            for (j, _w) in code.var_neighbors[i]:
                if i in c2v[j]:
                    out = acc - c2v[j][i]
                    v2c[i][j] = out - out.max()
        word = hard_decision(posterior)
        if syndrome_ok(word):
            return word
    return None
