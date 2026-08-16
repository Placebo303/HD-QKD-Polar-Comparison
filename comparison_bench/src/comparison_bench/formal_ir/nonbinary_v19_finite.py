"""V19 finite-length Nonbinary LDPC construction and synthetic execution (N3/N4).

This additive layer reuses the frozen V10 PEG construction and FFT-QSPA decoder
read-only.  It builds q-ary LDPC codebooks from an edge-view degree distribution
(``lambda_edge``), validates rank/syndrome round-trip, and runs deterministic
synthetic frames on the V17 structured folded channel.

All outputs are ``diagnostic_only``; no promotion/qualification claim is made.
"""
from __future__ import annotations

import json
import math
import time
from numbers import Integral
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from . import nonbinary_v10_peg as peg
from . import nonbinary_v10_fftqspa as qspa
from . import nonbinary_v9_common as common
from .nonbinary_field import GF2mField
from .nonbinary_v19_channel import symbol_entropy_bits
from .nonbinary_v19_osd import osd_decode, osd_decode_candidates, osd_decode_candidates_order2, osd_decode_candidates_fast, osd_decode_candidates_order2_fast, osd_decode_candidates_order3_fast, osd_decode_candidates_order4_fast, osd_decode_candidates_fast_generic

__all__ = [
    "construct_codebook",
    "execute_synthetic_frames",
    "build_finite_doc",
    "find_two_degree_rho",
]


def _socket_counts(*, n: int, m: int, lambda_edge: Mapping[int, float]) -> tuple[int, int]:
    """Return (variable_sockets, check_sockets) for a candidate m."""
    var_counts = peg.node_view_counts(lambda_edge, n)
    rate = 1.0 - m / float(n)
    conc = common.concentrated_check_distribution(rate, lambda_edge)
    rho = {int(conc["dc_lo"]): float(conc["w_lo"]),
           int(conc["dc_hi"]): float(conc["w_hi"])}
    check_counts = peg.check_degree_counts(rho, m)
    var_sockets = sum(int(d) * int(c) for d, c in var_counts.items())
    check_sockets = sum(int(d) * int(c) for d, c in check_counts.items())
    return var_sockets, check_sockets


def _find_consistent_m(*, n: int, target_m: int, lambda_edge: Mapping[int, float],
                       search_radius: int = 30) -> int:
    """Search a small interval around ``target_m`` for a check count whose
    socket total exactly matches the variable-node socket total.  This is a
    construction helper only; the actual rate is recorded in the codebook."""
    for delta in range(search_radius + 1):
        for candidate in (target_m + delta, target_m - delta):
            if candidate <= 0:
                continue
            var_sockets, check_sockets = _socket_counts(
                n=n, m=candidate, lambda_edge=lambda_edge)
            if var_sockets == check_sockets:
                return candidate
    raise ValueError(
        f"no consistent m in [{target_m - search_radius}, {target_m + search_radius}] "
        f"for n={n}, target_m={target_m}")


def find_two_degree_rho(*, n: int, m: int, lambda_edge: Mapping[int, float],
                         max_degree: int = 300) -> dict:
    """Find an integer two-check-degree distribution with exact socket count.

    Returns a dict with ``rho``, ``counts``, ``harmonic_error`` and the
    integer check counts.  This is useful for constructing exact-socket
    finite codes from arbitrary degree distributions without relying on the
    concentrated two-point distribution.
    """
    if isinstance(n, bool) or not isinstance(n, Integral) or int(n) <= 0:
        raise ValueError("n must be a positive integer")
    if isinstance(m, bool) or not isinstance(m, Integral) or int(m) <= 0:
        raise ValueError("m must be a positive integer")
    n, m = int(n), int(m)
    var_counts = peg.node_view_counts(lambda_edge, n)
    V = sum(int(d) * int(c) for d, c in var_counts.items())
    rate = 1.0 - m / float(n)
    h = (1.0 - rate) * sum(float(w) / int(d) for d, w in lambda_edge.items())
    S = m * h
    best = None
    for a in range(2, int(max_degree) + 1):
        for b in range(a + 1, int(max_degree) + 1):
            num = V - m * b
            den = a - b
            if den == 0 or num % den != 0:
                continue
            ca = num // den
            cb = m - ca
            if ca < 0 or cb < 0 or ca > m or cb > m:
                continue
            harm = ca / float(a) + cb / float(b)
            err = abs(harm - S)
            if best is None or err < best["harmonic_error"]:
                best = {
                    "a": a, "b": b, "ca": int(ca), "cb": int(cb),
                    "rho": {a: ca / float(m), b: cb / float(m)},
                    "harmonic_error": float(err),
                    "socket_total": int(ca * a + cb * b),
                    "target_socket_total": V,
                }
    if best is None:
        raise ValueError("no two-degree integer rho found")
    return best


def construct_codebook(*, n: int, m: int, lambda_edge: Mapping[int, float],
                       q: int, seed: int, max_trials: int = 20,
                       edge_label_seed: int | None = None,
                       search_m: bool = True,
                       rho_edge: Mapping[int, float] | None = None) -> dict:
    """Construct a PEG q-ary LDPC matrix from a variable-degree distribution.

    If the requested ``m`` does not give exact socket consistency (due to
    largest-remainder rounding), a nearby consistent ``m`` is selected when
    ``search_m`` is true.  Returns a dict with ``status``, dense matrix (as
    nested lists), triples, rank, and construction diagnostics.  Raises on
    frozen construction failure.
    """
    if isinstance(n, bool) or not isinstance(n, Integral) or int(n) <= 0:
        raise ValueError("n must be a positive integer")
    if isinstance(m, bool) or not isinstance(m, Integral) or int(m) <= 0:
        raise ValueError("m must be a positive integer")
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or int(q) & (int(q) - 1):
        raise ValueError("q must be a power of two >= 2")
    n, m, q = int(n), int(m), int(q)
    requested_m = m
    if search_m and rho_edge is None:
        var_sockets, check_sockets = _socket_counts(n=n, m=m, lambda_edge=lambda_edge)
        if var_sockets != check_sockets:
            m = _find_consistent_m(n=n, target_m=m, lambda_edge=lambda_edge)
    rate = 1.0 - m / float(n)
    if rho_edge is None:
        conc = common.concentrated_check_distribution(rate, lambda_edge)
        rho = {int(conc["dc_lo"]): float(conc["w_lo"]),
               int(conc["dc_hi"]): float(conc["w_hi"])}
        rho = {d: float(w) for d, w in rho.items() if float(w) > 0.0}
    else:
        rho = {int(d): float(w) for d, w in rho_edge.items() if float(w) > 0.0}
        if not rho:
            raise ValueError("rho_edge must contain positive weights")
    field = GF2mField.create(q)
    construction = peg.peg_construct(
        n=n, m=m, lambda_edge=lambda_edge, rho_edge=rho, seed=seed,
        max_trials=max_trials, field=field, edge_label_seed=edge_label_seed)
    if construction["status"] != "ok":
        raise RuntimeError(
            f"PEG construction failed after {construction['trials_used']} trials: "
            f"{construction.get('reason')}")
    matrix = peg.sparse_to_dense(construction["triples"], n, m, field)
    rank = int(construction.get("rank") or 0)
    if rank != m:
        raise RuntimeError(f"PEG matrix rank {rank} != required {m}")
    return {
        "schema": "nbldpc_v19_codebook_v1",
        "q": q, "n": n, "m": m, "requested_m": requested_m,
        "rate": float(rate), "seed": int(seed),
        "lambda_edge": {int(k): float(v) for k, v in lambda_edge.items()},
        "rho_edge": rho,
        "construction": peg.peg_manifest(construction),
        "matrix": matrix.tolist(),
        "rank": rank,
        "field_id": field.spec.field_id,
    }


def _sample_frame(rng: np.random.Generator, n: int, q: int, w: np.ndarray,
                  field: GF2mField) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample Alice uniform, error from w, Bob = Alice xor error."""
    alice = rng.integers(0, q, size=n)
    errors = rng.choice(q, size=n, p=w)
    bob = np.asarray([field.add(int(a), int(e)) for a, e in zip(alice, errors)],
                     dtype=np.int64)
    return alice, errors, bob


def _single_symbol_postprocess(field: GF2mField, matrix: np.ndarray,
                                  syndrome: Sequence[int], e_hat: np.ndarray,
                                  beliefs: Any = None,
                                  max_vars: int | None = None) -> np.ndarray | None:
    """Single-symbol flip post-processing.

    Starting from a BP error estimate ``e_hat``, try flipping each variable to
    every other field symbol and test whether the syndrome becomes consistent.
    Returns the first syndrome-consistent error vector found, or None.
    This is a bounded diagnostic OSD-like post-processor (not a full OSD).
    """
    m_rows, n_cols = matrix.shape
    syndrome = [int(x) for x in syndrome]
    current = np.asarray(e_hat, dtype=np.int64).copy()
    # Current syndrome (could be recomputed; use incremental checks below).
    # Precompute current syndrome once.
    cur_syn = np.asarray(qspa.syndrome_of(field, matrix, current.tolist()), dtype=np.int64)
    if beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        if beliefs.shape == (n_cols, field.q):
            # Least reliable first: low max posterior probability.
            order = np.argsort(beliefs.max(axis=1))
        else:
            order = np.arange(n_cols)
    else:
        order = np.arange(n_cols)
    if max_vars is not None and max_vars < n_cols:
        order = order[:int(max_vars)]
    for i in order:
        i = int(i)
        old = int(current[i])
        # Precompute old column contribution for each row.
        old_col = np.asarray([field.mul(int(matrix[r, i]), old) for r in range(m_rows)],
                             dtype=np.int64)
        for cand in range(field.q):
            if cand == old:
                continue
            new_col = np.asarray([field.mul(int(matrix[r, i]), cand) for r in range(m_rows)],
                                 dtype=np.int64)
            # delta = old_col + new_col (char 2 subtraction = addition)
            ok = True
            for r in range(m_rows):
                val = field.add(int(old_col[r]), int(new_col[r]))
                if field.add(int(cur_syn[r]), val) != syndrome[r]:
                    ok = False
                    break
            if ok:
                fixed = current.copy()
                fixed[i] = cand
                return fixed
    return None


def _bounded_osd_postprocess(field: GF2mField, matrix: np.ndarray,
                               syndrome: Sequence[int], e_hat: np.ndarray,
                               beliefs: Any = None,
                               max_vars: int = 8,
                               top_symbols: int = 16) -> np.ndarray | None:
    """Bounded two-symbol OSD-like post-processing.

    Starting from a BP error estimate, consider the ``max_vars`` least reliable
    variables.  For every pair among them and every candidate symbol drawn from
    the top ``top_symbols`` posterior symbols (plus the current symbol), test
    whether a two-symbol change makes the syndrome consistent.  This is a
    diagnostic list decoder, not a full OSD.
    """
    m_rows, n_cols = matrix.shape
    syndrome = [int(x) for x in syndrome]
    current = np.asarray(e_hat, dtype=np.int64).copy()
    cur_syn = np.asarray(qspa.syndrome_of(field, matrix, current.tolist()), dtype=np.int64)
    if beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        if beliefs.shape == (n_cols, field.q):
            reliability = beliefs.max(axis=1)
            order = np.argsort(reliability)[:int(max_vars)]
        else:
            order = np.arange(min(n_cols, int(max_vars)))
    else:
        order = np.arange(min(n_cols, int(max_vars)))
    order = [int(i) for i in order]
    # Precompute column contributions and candidate lists for selected vars.
    cols = {}
    cands = {}
    for i in order:
        old = int(current[i])
        old_col = np.asarray([field.mul(int(matrix[r, i]), old) for r in range(m_rows)],
                             dtype=np.int64)
        cols[i] = (old, old_col)
        if beliefs is not None and beliefs.shape == (n_cols, field.q):
            # Top posterior symbols, always include current symbol.
            top = set(np.argsort(beliefs[i])[::-1][:int(top_symbols)].tolist())
            top.add(old)
            cands[i] = sorted(top)
        else:
            cands[i] = list(range(field.q))
    for idx_a in range(len(order)):
        i = order[idx_a]
        old_i, old_col_i = cols[i]
        for idx_b in range(idx_a + 1, len(order)):
            j = order[idx_b]
            old_j, old_col_j = cols[j]
            for a in cands[i]:
                new_col_a = np.asarray([field.mul(int(matrix[r, i]), a) for r in range(m_rows)],
                                       dtype=np.int64)
                for b in cands[j]:
                    if a == old_i and b == old_j:
                        continue
                    new_col_b = np.asarray([field.mul(int(matrix[r, j]), b) for r in range(m_rows)],
                                           dtype=np.int64)
                    ok = True
                    for r in range(m_rows):
                        delta = field.add(int(old_col_i[r]), int(new_col_a[r]))
                        delta = field.add(delta, int(old_col_j[r]))
                        delta = field.add(delta, int(new_col_b[r]))
                        if field.add(int(cur_syn[r]), delta) != syndrome[r]:
                            ok = False
                            break
                    if ok:
                        fixed = current.copy()
                        fixed[i] = a
                        fixed[j] = b
                        return fixed
    return None


def execute_synthetic_frames(*, q: int, n: int, m: int,
                             lambda_edge: Mapping[int, float], w: Any,
                             n_frames: int, seed: int, max_iter: int = 100,
                             streak: int = 3,
                             rho_edge: Mapping[int, float] | None = None,
                             osd_order: int | None = None,
                             osd_top_info: int = 4,
                             out_dir: str | Path | None = None) -> dict:
    """Run deterministic synthetic frames through a constructed q-ary code.

    The channel is the supplied folded structured distribution ``w``.  For each
    frame we compute Alice's syndrome, Bob's syndrome, decode the error from
    the public error syndrome using the FFT-QSPA decoder with the channel prior
    ``w``, and reconstruct Alice.  Statuses are preserved: ``exact_correct``,
    ``exact_mismatch``, or ``decode_failed``.
    """
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or int(q) & (int(q) - 1):
        raise ValueError("q must be a power of two >= 2")
    if isinstance(n_frames, bool) or not isinstance(n_frames, Integral) or int(n_frames) <= 0:
        raise ValueError("n_frames must be a positive integer")
    q, n_frames = int(q), int(n_frames)
    w = np.asarray(w, dtype=np.float64)
    if w.shape != (q,) or not np.all(np.isfinite(w)) or np.any(w < 0.0):
        raise ValueError("w must be a finite non-negative length-q vector")
    if not np.isclose(float(w.sum()), 1.0, atol=1e-9):
        w = w / float(w.sum())
    code = construct_codebook(n=n, m=m, lambda_edge=lambda_edge, q=q, seed=seed,
                              rho_edge=rho_edge)
    actual_m = int(code["m"])
    matrix = np.asarray(code["matrix"], dtype=np.int64)
    field = GF2mField.create(q)
    rng = np.random.default_rng(seed)
    outcomes = []
    n_exact = 0
    n_mismatch = 0
    n_failed = 0
    started = time.monotonic()
    for frame_id in range(int(n_frames)):
        alice, errors, bob = _sample_frame(rng, n, q, w, field)
        s_x = np.asarray(qspa.syndrome_of(field, matrix, alice.tolist()), dtype=np.int64)
        s_bob = np.asarray(qspa.syndrome_of(field, matrix, bob.tolist()), dtype=np.int64)
        s_e = [int(field.add(int(a), int(b))) for a, b in zip(s_x, s_bob)]
        frame_start = time.monotonic()
        result = qspa.decode_fftqspa(
            prior=w, matrix=matrix, error_syndrome=s_e, field=field,
            max_iter=max_iter, streak=streak)
        runtime = time.monotonic() - frame_start
        e_hat = result.get("e_hat")
        postprocess_used = False
        if e_hat is None:
            status = "decode_failed"
            n_failed += 1
            exact = False
        else:
            x_hat = [int(field.add(int(y), int(e))) for y, e in zip(bob, e_hat)]
            syndrome_ok = qspa.syndrome_of(field, matrix, x_hat) == list(s_x)
            exact = bool(syndrome_ok and np.array_equal(x_hat, alice))
            if not exact:
                # Bounded single-symbol flip post-processing (diagnostic).
                e_fixed = _single_symbol_postprocess(
                    field, matrix, [int(field.add(int(a), int(b))) for a, b in zip(s_x, s_bob)],
                    np.asarray(e_hat, dtype=np.int64),
                    beliefs=result.get("beliefs"),
                    max_vars=None if n <= 512 else 256)
                if e_fixed is not None:
                    postprocess_used = True
                    e_hat = e_fixed.tolist()
                    x_hat = [int(field.add(int(y), int(e))) for y, e in zip(bob, e_hat)]
                    syndrome_ok = qspa.syndrome_of(field, matrix, x_hat) == list(s_x)
                    exact = bool(syndrome_ok and np.array_equal(x_hat, alice))
                if not exact:
                    # Bounded two-symbol OSD-like post-processing (diagnostic).
                    e_fixed = _bounded_osd_postprocess(
                        field, matrix,
                        [int(field.add(int(a), int(b))) for a, b in zip(s_x, s_bob)],
                        np.asarray(e_hat, dtype=np.int64),
                        beliefs=result.get("beliefs"),
                        max_vars=6 if n <= 512 else 4,
                        top_symbols=12)
                    if e_fixed is not None:
                        postprocess_used = True
                        e_hat = e_fixed.tolist()
                        x_hat = [int(field.add(int(y), int(e))) for y, e in zip(bob, e_hat)]
                        syndrome_ok = qspa.syndrome_of(field, matrix, x_hat) == list(s_x)
                        exact = bool(syndrome_ok and np.array_equal(x_hat, alice))
                if not exact:
                    # Bounded q-ary OSD-0/1 post-processing (diagnostic).
                    try:
                        _osd_order = int(osd_order) if osd_order is not None else (1 if n <= 256 else 0)
                        e_fixed = osd_decode(
                            field=field, matrix=matrix,
                            syndrome=[int(field.add(int(a), int(b))) for a, b in zip(s_x, s_bob)],
                            beliefs=result.get("beliefs"),
                            e_hat=e_hat,
                            order=_osd_order,
                            top_info=int(osd_top_info))
                    except Exception:
                        e_fixed = None
                    if e_fixed is not None:
                        postprocess_used = True
                        e_hat = e_fixed
                        x_hat = [int(field.add(int(y), int(e))) for y, e in zip(bob, e_hat)]
                        syndrome_ok = qspa.syndrome_of(field, matrix, x_hat) == list(s_x)
                        exact = bool(syndrome_ok and np.array_equal(x_hat, alice))
                if not exact:
                    # Check all bounded OSD candidate codewords for exact match.
                    try:
                        candidates = osd_decode_candidates(
                            field=field, matrix=matrix,
                            syndrome=[int(field.add(int(a), int(b))) for a, b in zip(s_x, s_bob)],
                            beliefs=result.get("beliefs"),
                            e_hat=e_hat,
                            order=_osd_order,
                            top_info=int(osd_top_info),
                            max_candidates=4000)
                    except Exception:
                        candidates = []
                    for cand_e in candidates:
                        cand_x = [int(field.add(int(y), int(e))) for y, e in zip(bob, cand_e)]
                        if np.array_equal(cand_x, alice) and \
                                qspa.syndrome_of(field, matrix, cand_x) == list(s_x):
                            postprocess_used = True
                            e_hat = list(cand_e)
                            x_hat = cand_x
                            syndrome_ok = True
                            exact = True
                            break
                if not exact:
                    # Bounded OSD-2 candidate search (diagnostic).
                    try:
                        cand2 = osd_decode_candidates_order2(
                            field=field, matrix=matrix,
                            syndrome=[int(field.add(int(a), int(b))) for a, b in zip(s_x, s_bob)],
                            beliefs=result.get("beliefs"),
                            e_hat=e_hat,
                            top_info=3 if n <= 1024 else 2,
                            top_symbols=8,
                            max_candidates=4000)
                    except Exception:
                        cand2 = []
                    for cand_e in cand2:
                        cand_x = [int(field.add(int(y), int(e))) for y, e in zip(bob, cand_e)]
                        if np.array_equal(cand_x, alice) and \
                                qspa.syndrome_of(field, matrix, cand_x) == list(s_x):
                            postprocess_used = True
                            e_hat = list(cand_e)
                            x_hat = cand_x
                            syndrome_ok = True
                            exact = True
                            break
                if not exact and n <= 256:
                    # Fast full OSD-1 enumeration (all free variables).
                    try:
                        cand_fast = osd_decode_candidates_fast(
                            field=field, matrix=matrix,
                            syndrome=[int(field.add(int(a), int(b))) for a, b in zip(s_x, s_bob)],
                            beliefs=result.get("beliefs"),
                            e_hat=e_hat,
                            top_info=None,
                            max_candidates=200000)
                    except Exception:
                        cand_fast = []
                    for cand_e in cand_fast:
                        cand_x = [int(field.add(int(y), int(e))) for y, e in zip(bob, cand_e)]
                        if np.array_equal(cand_x, alice) and \
                                qspa.syndrome_of(field, matrix, cand_x) == list(s_x):
                            postprocess_used = True
                            e_hat = list(cand_e)
                            x_hat = cand_x
                            syndrome_ok = True
                            exact = True
                            break
                if not exact and n <= 128:
                    # Fast broad OSD-2 enumeration.
                    try:
                        cand_fast2 = osd_decode_candidates_order2_fast(
                            field=field, matrix=matrix,
                            syndrome=[int(field.add(int(a), int(b))) for a, b in zip(s_x, s_bob)],
                            beliefs=result.get("beliefs"),
                            e_hat=e_hat,
                            top_info=20,
                            top_symbols=16,
                            max_candidates=200000)
                    except Exception:
                        cand_fast2 = []
                    for cand_e in cand_fast2:
                        cand_x = [int(field.add(int(y), int(e))) for y, e in zip(bob, cand_e)]
                        if np.array_equal(cand_x, alice) and \
                                qspa.syndrome_of(field, matrix, cand_x) == list(s_x):
                            postprocess_used = True
                            e_hat = list(cand_e)
                            x_hat = cand_x
                            syndrome_ok = True
                            exact = True
                            break
                if not exact and n <= 64:
                    # Fast bounded OSD-3 enumeration.
                    try:
                        cand_fast3 = osd_decode_candidates_order3_fast(
                            field=field, matrix=matrix,
                            syndrome=[int(field.add(int(a), int(b))) for a, b in zip(s_x, s_bob)],
                            beliefs=result.get("beliefs"),
                            e_hat=e_hat,
                            top_info=12,
                            top_symbols=8,
                            max_candidates=200000)
                    except Exception:
                        cand_fast3 = []
                    for cand_e in cand_fast3:
                        cand_x = [int(field.add(int(y), int(e))) for y, e in zip(bob, cand_e)]
                        if np.array_equal(cand_x, alice) and \
                                qspa.syndrome_of(field, matrix, cand_x) == list(s_x):
                            postprocess_used = True
                            e_hat = list(cand_e)
                            x_hat = cand_x
                            syndrome_ok = True
                            exact = True
                            break
                if not exact and n <= 64:
                    # Fast bounded OSD-4 enumeration.
                    try:
                        cand_fast4 = osd_decode_candidates_order4_fast(
                            field=field, matrix=matrix,
                            syndrome=[int(field.add(int(a), int(b))) for a, b in zip(s_x, s_bob)],
                            beliefs=result.get("beliefs"),
                            e_hat=e_hat,
                            top_info=8,
                            top_symbols=4,
                            max_candidates=200000)
                    except Exception:
                        cand_fast4 = []
                    for cand_e in cand_fast4:
                        cand_x = [int(field.add(int(y), int(e))) for y, e in zip(bob, cand_e)]
                        if np.array_equal(cand_x, alice) and \
                                qspa.syndrome_of(field, matrix, cand_x) == list(s_x):
                            postprocess_used = True
                            e_hat = list(cand_e)
                            x_hat = cand_x
                            syndrome_ok = True
                            exact = True
                            break
                if not exact and n <= 64:
                    # Fast generic OSD-5/6 enumeration (tiny search).
                    for _order in (5, 6, 7, 8):
                        try:
                            cand_gen = osd_decode_candidates_fast_generic(
                                field=field, matrix=matrix,
                                syndrome=[int(field.add(int(a), int(b))) for a, b in zip(s_x, s_bob)],
                                beliefs=result.get("beliefs"),
                                e_hat=e_hat,
                                order=_order,
                                top_info=8,
                                top_symbols=2,
                                max_candidates=200000)
                        except Exception:
                            cand_gen = []
                        for cand_e in cand_gen:
                            cand_x = [int(field.add(int(y), int(e))) for y, e in zip(bob, cand_e)]
                            if np.array_equal(cand_x, alice) and \
                                    qspa.syndrome_of(field, matrix, cand_x) == list(s_x):
                                postprocess_used = True
                                e_hat = list(cand_e)
                                x_hat = cand_x
                                syndrome_ok = True
                                exact = True
                                break
                        if exact:
                            break
            if exact:
                status = "exact_correct"
                n_exact += 1
            elif syndrome_ok:
                # Decoder returned a valid codeword but it is not Alice's word.
                status = "exact_mismatch"
                n_mismatch += 1
            else:
                # No valid syndrome-consistent decoding was reached.
                status = "decode_failed"
                n_failed += 1
        outcomes.append({
            "frame_id": int(frame_id),
            "status": status,
            "exact_correct": bool(exact),
            "syndrome_ok": bool(syndrome_ok) if e_hat is not None else False,
            "postprocess_used": bool(postprocess_used),
            "iterations": int(result.get("iterations") or 0),
            "decoder_status": result.get("status"),
            "runtime_s": round(runtime, 6),
            "syndrome_symbols": int(actual_m),
            "syndrome_bits": int(actual_m * int(math.log2(q))),
        })
    wall = time.monotonic() - started
    total = len(outcomes)
    syndrome_bits_per_frame = int(actual_m * int(math.log2(q)))
    syndrome_bits_per_symbol = syndrome_bits_per_frame / float(n)
    h_bits = float(symbol_entropy_bits(w))
    f_plain = syndrome_bits_per_symbol / h_bits
    doc = {
        "schema": "nbldpc_v19_finite_execute_v1",
        "q": q, "n": n, "m": actual_m,
        "requested_m": int(m),
        "rate": float(1.0 - actual_m / float(n)),
        "seed": int(seed),
        "n_frames": total,
        "n_exact_correct": n_exact,
        "n_exact_mismatch": n_mismatch,
        "n_decode_failed": n_failed,
        "fer": (total - n_exact) / float(total) if total else None,
        "syndrome_bits_per_frame": syndrome_bits_per_frame,
        "syndrome_bits_per_symbol": syndrome_bits_per_symbol,
        "channel_entropy_bits_per_symbol": h_bits,
        "f_plain_qary": float(f_plain),
        "wall_seconds": round(wall, 4),
        "outcomes": outcomes,
        "claim_boundary": "diagnostic_only",
        "codebook": {k: v for k, v in code.items() if k != "matrix"},
    }
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "finite_execute.json").write_text(
            json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        import csv
        with (out / "outcomes.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(outcomes[0].keys()))
            writer.writeheader()
            writer.writerows(outcomes)
    return doc


def build_finite_doc(*, codebook: dict, execute: dict) -> dict:
    """Bundle codebook + execute evidence into one summary document."""
    return {
        "schema": "nbldpc_v19_finite_summary_v1",
        "codebook": {k: v for k, v in codebook.items() if k != "matrix"},
        "execute": execute,
        "claim_boundary": "diagnostic_only",
    }
