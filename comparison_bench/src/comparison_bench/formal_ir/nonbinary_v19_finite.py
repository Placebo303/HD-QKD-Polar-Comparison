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

__all__ = [
    "construct_codebook",
    "execute_synthetic_frames",
    "build_finite_doc",
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


def execute_synthetic_frames(*, q: int, n: int, m: int,
                             lambda_edge: Mapping[int, float], w: Any,
                             n_frames: int, seed: int, max_iter: int = 100,
                             streak: int = 3,
                             rho_edge: Mapping[int, float] | None = None,
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
        if e_hat is None:
            status = "decode_failed"
            n_failed += 1
            exact = False
        else:
            x_hat = [int(field.add(int(y), int(e))) for y, e in zip(bob, e_hat)]
            syndrome_ok = qspa.syndrome_of(field, matrix, x_hat) == list(s_x)
            exact = bool(syndrome_ok and np.array_equal(x_hat, alice))
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
