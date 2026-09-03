"""V72P2D2 orthogonal one-block triage primitives.

This module contains the smallest reusable implementation for the accepted
diagnostic plan.  It deliberately has no data loading or production-output
side effects; the command-line wrapper owns those boundaries.
"""
from __future__ import annotations

import importlib.util
import math
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np


Q = 1024
N = 1024
NBIT = 10240
M = 9036
NNZ = 49620
INFO_END = 1204
SEED = 20260902
LLR_CLIP = 20.0
CONVERGENCE_TOL = 1e-6
MAX_SWEEPS_PER_CHECKPOINT = 10
MAX_TOTAL_SWEEPS = 720
CHECKPOINT_ROWS = tuple(list(range(160, 8993, 128)) + [9032, 9036])
QUANTILES = np.asarray([0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0])
ZERO_TOL = 1e-15
M0_LAMBDA = 221.22162910704503
M0_CE_CAL_CV = 7.135005172802673
M2_HISTORICAL_CE = 6.787126437359054
LAYERED_ACTIVE_ROW_SUM = 338388
LAYERED_TARGET_UPPER_BOUND = LAYERED_ACTIVE_ROW_SUM * 6 * 10 * 10
LAYERED_STATE_UPPER_BOUND = Q * LAYERED_TARGET_UPPER_BOUND
M2_PARAMS = {
    "family": "laplace",
    "mu": 0.0,
    "scale": 0.2714417616594907,
    "eps": 0.562251256281407,
    "Q": Q,
}

B_BITS = ((np.arange(Q)[:, None] >> np.arange(10)[None, :]) & 1).astype(np.int8)

try:
    import numba as _numba

    HAS_NUMBA = True
except ImportError:  # pragma: no cover - exercised on minimal installations
    _numba = None
    HAS_NUMBA = False


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_v72p1_adapter():
    path = _repo_root() / "comparison_bench" / "src" / "comparison_bench" / "formal_ir" / "v72p1_soft_joint_adapter.py"
    spec = importlib.util.spec_from_file_location("v72p1_adapter_for_v72p2d2", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load adapter: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_mother_csr() -> tuple[np.ndarray, np.ndarray, int]:
    """Reuse the accepted V72P0/V72P1 mother without changing it."""
    return _load_v72p1_adapter().get_mother_csr()


def get_flooding_decoder() -> Callable[..., Mapping[str, Any]]:
    """Return the existing V72P1 flooding decoder for I/P callers."""
    return _load_v72p1_adapter().run_decoder


def _validate_csr(indptr: np.ndarray, indices: np.ndarray, n_vars: int) -> None:
    if indptr.ndim != 1 or indices.ndim != 1:
        raise ValueError("CSR arrays must be one-dimensional")
    if indptr.size == 0 or int(indptr[0]) != 0:
        raise ValueError("CSR indptr must start at zero")
    if np.any(np.diff(indptr) < 0) or int(indptr[-1]) != indices.size:
        raise ValueError("invalid CSR offsets")
    if indices.size and (int(indices.min()) < 0 or int(indices.max()) >= n_vars):
        raise ValueError("CSR variable index outside prior shape")


def _validate_prior(prior_logp: np.ndarray) -> np.ndarray:
    prior = np.asarray(prior_logp, dtype=np.float64)
    if prior.ndim != 2 or prior.shape[1] != Q or prior.shape[0] <= 0:
        raise ValueError("prior_logp must have shape (n_symbols,1024)")
    if not np.all(np.isfinite(prior)):
        raise ValueError("prior_logp must be finite")
    return prior


def _pack_symbols(bits: np.ndarray) -> np.ndarray:
    values = np.asarray(bits, dtype=np.uint8).reshape(-1)
    if values.size % 10:
        raise ValueError("bit array length must be divisible by ten")
    return np.asarray(
        [sum(int(values[10 * sym + bit]) << bit for bit in range(10)) for sym in range(values.size // 10)],
        dtype=np.uint16,
    )


def _syndrome_from_bits(bits: np.ndarray, indptr: np.ndarray, indices: np.ndarray) -> np.ndarray:
    values = np.asarray(bits, dtype=np.uint8).reshape(-1)
    indptr = np.asarray(indptr, dtype=np.int64)
    indices = np.asarray(indices, dtype=np.int64)
    _validate_csr(indptr, indices, values.size)
    observed = np.zeros(indptr.size - 1, dtype=np.uint8)
    for row in range(observed.size):
        observed[row] = np.uint8(int(np.sum(values[indices[indptr[row] : indptr[row + 1]]])) & 1)
    return observed


def _factor_extrinsic(prior_row: np.ndarray, bit_to_factor_row: np.ndarray, target_bit: int) -> float:
    """Compute one target bit marginal with target-bit self-exclusion."""
    prior_row = np.asarray(prior_row, dtype=np.float64)
    bit_to_factor_row = np.asarray(bit_to_factor_row, dtype=np.float64)
    if prior_row.shape != (Q,) or bit_to_factor_row.shape != (10,):
        raise ValueError("factor state must have shapes (1024,) and (10,)")
    if not 0 <= int(target_bit) < 10:
        raise ValueError("target bit outside 0..9")
    llr = bit_to_factor_row.copy()
    llr[int(target_bit)] = 0.0
    unnormalized = prior_row + B_BITS.dot(llr)
    normalizer = float(np.logaddexp.reduce(unnormalized))
    normalized = unnormalized - normalizer
    one = B_BITS[:, int(target_bit)] == 1
    m1 = float(np.logaddexp.reduce(normalized[one]))
    m0 = float(np.logaddexp.reduce(normalized[~one]))
    return float(np.clip(m1 - m0, -LLR_CLIP, LLR_CLIP))


def local_factor_extrinsic(prior_logp_sym: np.ndarray, bit_to_factor_sym: np.ndarray, target_bit: int) -> float:
    """Public name for the natural-log local factor marginal."""
    return _factor_extrinsic(prior_logp_sym, bit_to_factor_sym, target_bit)


if HAS_NUMBA:

    @_numba.njit(cache=False)
    def _factor_symbols_numba(prior, bit_to_factor, symbols, out, b_bits):
        for si in range(symbols.shape[0]):
            sym = int(symbols[si])
            term = np.empty(1024, dtype=np.float64)
            for a in range(1024):
                value = 0.0
                for b in range(10):
                    value += float(b_bits[a, b]) * float(bit_to_factor[sym, b])
                term[a] = value
            for b in range(10):
                max1 = -1.0e300
                max0 = -1.0e300
                for a in range(1024):
                    value = float(prior[sym, a]) + term[a] - float(b_bits[a, b]) * float(bit_to_factor[sym, b])
                    if b_bits[a, b] == 1:
                        if value > max1:
                            max1 = value
                    elif value > max0:
                        max0 = value
                sum1 = 0.0
                sum0 = 0.0
                for a in range(1024):
                    value = float(prior[sym, a]) + term[a] - float(b_bits[a, b]) * float(bit_to_factor[sym, b])
                    if b_bits[a, b] == 1:
                        sum1 += math.exp(value - max1)
                    else:
                        sum0 += math.exp(value - max0)
                value = (max1 + math.log(sum1)) - (max0 + math.log(sum0))
                if value > 20.0:
                    value = 20.0
                elif value < -20.0:
                    value = -20.0
                out[sym, b] = value
        return out


def _factor_batch(
    prior_logp: np.ndarray,
    bit_to_factor: np.ndarray,
    symbols: np.ndarray | None = None,
) -> np.ndarray:
    """Compute f2b for selected symbols; one row contains all ten targets."""
    prior = _validate_prior(prior_logp)
    btf = np.asarray(bit_to_factor, dtype=np.float64)
    if prior.ndim != 2 or prior.shape[1] != Q or btf.shape != (prior.shape[0], 10):
        raise ValueError("prior/factor shapes are incompatible")
    out = np.zeros((prior.shape[0], 10), dtype=np.float64)
    if symbols is None:
        selected = np.arange(prior.shape[0], dtype=np.int32)
    else:
        selected = np.asarray(symbols, dtype=np.int32)
        if selected.size and (int(selected.min()) < 0 or int(selected.max()) >= prior.shape[0]):
            raise ValueError("selected symbol outside prior")
    if HAS_NUMBA and selected.size:
        return _factor_symbols_numba(prior, btf, selected, out, B_BITS)
    for sym in selected.tolist():
        for bit in range(10):
            out[sym, bit] = _factor_extrinsic(prior[sym], btf[sym], bit)
    return out


def factor_batch(prior_logp: np.ndarray, bit_to_factor: np.ndarray) -> np.ndarray:
    """Public complete factor batch used by diagnostics and tests."""
    return _factor_batch(prior_logp, bit_to_factor)


def rebuild_factor_state(
    prior_logp: np.ndarray, check_to_variable: np.ndarray, indptr: np.ndarray, indices: np.ndarray
) -> dict[str, np.ndarray]:
    """Rebuild b2f/f2b/APP from an active c2v state without a decoder update."""
    prior = _validate_prior(prior_logp)
    indptr = np.asarray(indptr, dtype=np.int32)
    indices = np.asarray(indices, dtype=np.int32)
    c2v = np.asarray(check_to_variable, dtype=np.float64)
    nbit = prior.shape[0] * 10
    _validate_csr(indptr, indices, nbit)
    if c2v.shape != (indices.size,):
        raise ValueError("c2v shape must equal active edge count")
    edge_vars = indices.astype(np.int64, copy=False)
    btf_flat = np.bincount(edge_vars, weights=c2v, minlength=nbit).astype(np.float64)
    btf = btf_flat.reshape(prior.shape[0], 10)
    f2b = _factor_batch(prior, btf)
    app_raw = f2b.reshape(-1) + btf_flat
    return {"bit_to_factor": btf, "factor_to_bit": f2b, "app_raw": app_raw, "b2f": btf}


def _spa_row(v2c: np.ndarray, syndrome: int) -> np.ndarray:
    vals = np.asarray(v2c, dtype=np.float64)
    d = vals.size
    if d == 0:
        return np.empty(0, dtype=np.float64)
    tanh_vals = np.clip(np.tanh(vals / 2.0), -0.999999999999, 0.999999999999)
    out = np.empty(d, dtype=np.float64)
    flip = -1.0 if int(syndrome) else 1.0
    if d % 2:
        flip = -flip
    for i in range(d):
        if d == 1:
            product = 1.0
        else:
            product = float(np.prod(np.delete(tanh_vals, i)))
        product = float(np.clip(flip * product, -1.0 + 1e-12, 1.0 - 1e-12))
        out[i] = float(np.clip(2.0 * np.arctanh(product), -LLR_CLIP, LLR_CLIP))
    return out


def _hard_readout(app_raw: np.ndarray, indptr: np.ndarray, indices: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    nbit = app_raw.size
    hard_bits = (np.asarray(app_raw) > 0.0).astype(np.uint8)
    hard_symbols = _pack_symbols(hard_bits)
    observed = _syndrome_from_bits(hard_bits, indptr, indices)
    return hard_bits, hard_symbols, observed


def run_layered_decoder(
    prior_logp: np.ndarray,
    syndrome_target: np.ndarray,
    indptr: np.ndarray,
    indices: np.ndarray,
    max_sweeps: int,
    warm_start_c2v: np.ndarray,
) -> dict[str, Any]:
    """Run a true row-serial layered sweep on the supplied active CSR prefix."""
    prior = _validate_prior(prior_logp)
    syndrome = np.asarray(syndrome_target, dtype=np.uint8)
    indptr = np.asarray(indptr, dtype=np.int32)
    indices = np.asarray(indices, dtype=np.int32)
    nbit = prior.shape[0] * 10
    _validate_csr(indptr, indices, nbit)
    if syndrome.shape != (indptr.size - 1,):
        raise ValueError("syndrome length must equal active row count")
    c2v = np.asarray(warm_start_c2v, dtype=np.float64).copy()
    if c2v.shape != (indices.size,):
        raise ValueError("warm_start_c2v shape must equal len(indices)")
    if int(max_sweeps) < 0:
        raise ValueError("max_sweeps must be nonnegative")

    edge_vars = indices.astype(np.int64, copy=False)
    state = rebuild_factor_state(prior, c2v, indptr, indices)
    btf = state["bit_to_factor"]
    f2b = state["factor_to_bit"]
    app_raw = state["app_raw"]
    # This is the one complete checkpoint rebuild.  Keep a private snapshot so
    # the runner can report F/S/A pre-metrics without rebuilding it a second
    # time (the private key is never written to an output artifact).
    pre_state = {
        "bit_to_factor": btf.copy(),
        "factor_to_bit": f2b.copy(),
        "app_raw": app_raw.copy(),
    }
    residuals: list[float] = []
    edge_updates = 0
    local_targets = 0
    converged = False
    variable_to_check = np.zeros(indices.size, dtype=np.float64)

    for _sweep in range(min(int(max_sweeps), MAX_TOTAL_SWEEPS)):
        sweep_start = c2v.copy()
        for row in range(indptr.size - 1):
            start, end = int(indptr[row]), int(indptr[row + 1])
            if end == start:
                continue
            old_row = c2v[start:end].copy()
            variables = edge_vars[start:end]
            btf_flat = btf.reshape(-1)
            v2c = f2b.reshape(-1)[variables] + btf_flat[variables] - old_row
            variable_to_check[start:end] = v2c
            new_row = _spa_row(v2c, int(syndrome[row]))
            c2v[start:end] = new_row
            for offset, variable in enumerate(variables.tolist()):
                btf_flat[int(variable)] += float(new_row[offset] - old_row[offset])
            affected = np.unique((variables // 10).astype(np.int32))
            updated_f2b = _factor_batch(prior, btf, affected)
            # Selected rows are the only rows changed by this row commit;
            # preserve the factor messages for all other symbols.
            if affected.size:
                f2b[affected] = updated_f2b[affected]
            app_raw = f2b.reshape(-1) + btf_flat
            local_targets += 10 * int(affected.size)
        residual = float(np.max(np.abs(c2v - sweep_start))) if c2v.size else 0.0
        residuals.append(residual)
        edge_updates += int(c2v.size)
        if residual < CONVERGENCE_TOL:
            converged = True
            break

    # Return v2c for the final state, not the last row-start values.
    if indices.size:
        sums = btf.reshape(-1)[edge_vars]
        variable_to_check = f2b.reshape(-1)[edge_vars] + sums - c2v
    app_clipped = np.clip(app_raw, -LLR_CLIP, LLR_CLIP)
    hard_bits, hard_symbols, syndrome_observed = _hard_readout(app_clipped, indptr, indices)
    finite = bool(
        np.all(np.isfinite(prior))
        and np.all(np.isfinite(btf))
        and np.all(np.isfinite(f2b))
        and np.all(np.isfinite(variable_to_check))
        and np.all(np.isfinite(c2v))
        and np.all(np.isfinite(app_raw))
    )
    diagnostic_rebuild_targets = int(prior.shape[0] * 10)
    core_state = int(Q * local_targets)
    diagnostic_state = int(Q * diagnostic_rebuild_targets)
    diagnostic_factor_targets = diagnostic_rebuild_targets
    total_targets = local_targets + diagnostic_factor_targets
    return {
        "bit_to_factor": np.asarray(btf, dtype=np.float64),
        "factor_to_bit": np.asarray(f2b, dtype=np.float64),
        "variable_to_check": np.asarray(variable_to_check, dtype=np.float64),
        "check_to_variable": np.asarray(c2v, dtype=np.float64),
        "app_llr": np.asarray(app_clipped, dtype=np.float64),
        "app_raw": np.asarray(app_raw, dtype=np.float64),
        "hard_bits": hard_bits,
        "hard_symbols": hard_symbols,
        "syndrome_observed": syndrome_observed,
        "finite": finite,
        "residuals": residuals,
        "converged": bool(converged),
        "max_llr": float(np.max(np.abs(app_clipped))) if app_clipped.size else 0.0,
        "sweeps": int(len(residuals)),
        "edge_updates": int(edge_updates),
        "local_factor_target_updates": int(local_targets),
        "state_evaluations": core_state,
        "diagnostic_L0_target_updates": 0,
        "diagnostic_checkpoint_rebuild_target_updates": diagnostic_rebuild_targets,
        "diagnostic_final_readout_target_updates": 0,
        "diagnostic_factor_target_updates": diagnostic_factor_targets,
        "diagnostic_state_evaluations": diagnostic_state,
        "diagnostic_readout_evaluations": int(app_clipped.size),
        "total_target_updates": int(total_targets),
        "total_state_evaluations": int(Q * total_targets),
        "_pre_state": pre_state,
    }


def build_degree_balanced_interleaver(
    indptr: np.ndarray,
    indices: np.ndarray,
    n_vars: int = NBIT,
    n_symbols: int = N,
    info_end: int = INFO_END,
    seed: int = SEED,
) -> dict[str, Any]:
    """Build the frozen full-column degree-balanced physical permutation."""
    indptr = np.asarray(indptr, dtype=np.int32)
    indices = np.asarray(indices, dtype=np.int32)
    _validate_csr(indptr, indices, n_vars)
    if n_vars != n_symbols * 10:
        raise ValueError("physical layout requires ten bits per symbol")
    if n_symbols <= 0 or int(info_end) < 0 or int(info_end) > n_vars:
        raise ValueError("invalid symbol or high-column dimensions")
    high_end = int(info_end)
    degrees = np.bincount(indices.astype(np.int64), minlength=n_vars).astype(np.int64)
    old_to_phys = np.full(n_vars, -1, dtype=np.int32)
    info_count = np.zeros(n_symbols, dtype=np.int32)
    info_load = np.zeros(n_symbols, dtype=np.int64)
    high_columns = sorted(range(high_end), key=lambda col: (-int(degrees[col]), col))
    for old_col in high_columns:
        candidates = [sym for sym in range(n_symbols) if info_count[sym] < 2]
        if not candidates:
            raise ValueError("high-column assignment exhausted symbol slots")
        sym = min(candidates, key=lambda item: (int(info_load[item]), int(info_count[item]), item))
        bit = int(info_count[sym])
        old_to_phys[old_col] = np.int32(10 * sym + bit)
        info_count[sym] += 1
        info_load[sym] += int(degrees[old_col])
    assigned_phys = np.zeros(n_vars, dtype=bool)
    assigned_phys[old_to_phys[old_to_phys >= 0]] = True
    remaining_slots = [
        (sym, bit)
        for sym in range(n_symbols)
        for bit in range(10)
        if not assigned_phys[10 * sym + bit]
    ]
    parity_columns = list(range(high_end, n_vars))
    rng = np.random.default_rng(int(seed))
    parity_order = np.asarray(parity_columns, dtype=np.int32)[rng.permutation(len(parity_columns))]
    if len(parity_order) != len(remaining_slots):
        raise ValueError("high/parity slot accounting mismatch")
    for old_col, (sym, bit) in zip(parity_order.tolist(), remaining_slots):
        old_to_phys[int(old_col)] = np.int32(10 * sym + bit)
    if np.any(old_to_phys < 0) or np.unique(old_to_phys).size != n_vars:
        raise ValueError("interleaver is not a full bijection")
    phys_to_old = np.empty(n_vars, dtype=np.int32)
    phys_to_old[old_to_phys] = np.arange(n_vars, dtype=np.int32)
    high_symbol_counts = np.bincount(old_to_phys[:high_end] // 10, minlength=n_symbols).astype(np.int32)
    return {
        "old_to_phys": old_to_phys,
        "phys_to_old": phys_to_old,
        "degrees": degrees,
        "info_count": info_count,
        "info_load": info_load,
        "high_columns": np.asarray(high_columns, dtype=np.int32),
        "high_symbol_counts": high_symbol_counts,
        "seed": int(seed),
    }


def remap_csr(indices: np.ndarray, old_to_phys: np.ndarray) -> np.ndarray:
    indices = np.asarray(indices, dtype=np.int32)
    mapping = np.asarray(old_to_phys, dtype=np.int32)
    return mapping[indices.astype(np.int64)].astype(np.int32, copy=False)


def csr_row_degrees(indptr: np.ndarray) -> np.ndarray:
    indptr = np.asarray(indptr, dtype=np.int64)
    return np.diff(indptr).astype(np.int64)


def csr_column_degrees(indices: np.ndarray, n_vars: int = NBIT) -> np.ndarray:
    return np.bincount(np.asarray(indices, dtype=np.int64), minlength=n_vars).astype(np.int64)


def _validate_mother_contract(indptr: np.ndarray, indices: np.ndarray) -> None:
    indptr = np.asarray(indptr, dtype=np.int32)
    indices = np.asarray(indices, dtype=np.int32)
    if indptr.shape != (M + 1,) or indices.shape != (NNZ,):
        raise ValueError("mother dimensions do not match the frozen contract")
    _validate_csr(indptr, indices, NBIT)
    row_degrees = csr_row_degrees(indptr)
    unique, counts = np.unique(row_degrees, return_counts=True)
    observed = {int(key): int(value) for key, value in zip(unique.tolist(), counts.tolist())}
    if observed != {4: 1, 5: 4594, 6: 4441}:
        raise ValueError(f"mother check-degree distribution mismatch: {observed}")
    if int(np.count_nonzero(csr_column_degrees(indices, NBIT) == 2)) != 9035:
        raise ValueError("mother degree-2 column count mismatch")


def gf2_rank_csr(indptr: np.ndarray, indices: np.ndarray) -> int:
    """Compute rank using Python integer bitsets; suitable for this one graph."""
    basis: dict[int, int] = {}
    rank = 0
    for row in range(len(indptr) - 1):
        bits = 0
        for col in np.asarray(indices[int(indptr[row]) : int(indptr[row + 1])], dtype=np.int64).tolist():
            bits ^= 1 << int(col)
        while bits:
            pivot = bits.bit_length() - 1
            previous = basis.get(pivot)
            if previous is None:
                basis[pivot] = bits
                rank += 1
                break
            bits ^= previous
    return rank


def pure_h_cycle_stats(indptr: np.ndarray, indices: np.ndarray) -> dict[str, int]:
    """Count ordinary binary-H check-pair four-cycles and collisions."""
    indptr = np.asarray(indptr, dtype=np.int64)
    indices = np.asarray(indices, dtype=np.int64)
    if indices.size == 0:
        return {"four_cycles": 0, "collision_pairs": 0}
    n_vars = int(indices.max()) + 1
    var_to_checks: list[list[int]] = [[] for _ in range(n_vars)]
    for row in range(indptr.size - 1):
        for variable in indices[indptr[row] : indptr[row + 1]].tolist():
            var_to_checks[int(variable)].append(row)
    pair_counts: dict[tuple[int, int], int] = {}
    for checks in var_to_checks:
        for left in range(len(checks)):
            for right in range(left + 1, len(checks)):
                pair = (min(checks[left], checks[right]), max(checks[left], checks[right]))
                pair_counts[pair] = pair_counts.get(pair, 0) + 1
    return {
        "four_cycles": int(sum(k * (k - 1) // 2 for k in pair_counts.values())),
        "collision_pairs": int(sum(k >= 2 for k in pair_counts.values())),
    }


def symbol_factor_stats(
    indptr: np.ndarray, indices: np.ndarray, n_vars: int = NBIT, n_symbols: int | None = None
) -> dict[str, Any]:
    """Recount symbol-factor collisions separately from pure-H cycles."""
    indptr = np.asarray(indptr, dtype=np.int64)
    indices = np.asarray(indices, dtype=np.int64)
    if n_symbols is None:
        n_symbols = int(n_vars) // 10
    _validate_csr(indptr, indices, int(n_vars))
    sigma_c2 = 0
    collision_rows = 0
    for row in range(indptr.size - 1):
        symbols = indices[indptr[row] : indptr[row + 1]] // 10
        if symbols.size == 0:
            continue
        counts = np.bincount(symbols, minlength=int(n_symbols))
        repeated = counts[counts >= 2]
        sigma_c2 += int(np.sum(repeated * (repeated - 1) // 2))
        collision_rows += int(repeated.size > 0)
    symbol_edges = np.bincount(indices // 10, minlength=int(n_symbols)).astype(np.int64)
    if symbol_edges.size:
        edge_summary = {
            "min": int(np.min(symbol_edges)),
            "median": float(np.median(symbol_edges)),
            "max": int(np.max(symbol_edges)),
        }
    else:
        edge_summary = {"min": 0, "median": 0.0, "max": 0}
    return {
        "symbol_edge_counts": symbol_edges,
        "symbol_edges_min": edge_summary["min"],
        "symbol_edges_median": edge_summary["median"],
        "symbol_edges_max": edge_summary["max"],
        "symbol_sigma_c2": int(sigma_c2),
        "symbol_collision_rows": int(collision_rows),
    }


def verify_interleaver(
    indptr: np.ndarray,
    indices: np.ndarray,
    mapping: Mapping[str, Any],
    n_vars: int = NBIT,
    n_symbols: int | None = None,
    info_end: int = INFO_END,
) -> dict[str, Any]:
    old_to_phys = np.asarray(mapping["old_to_phys"], dtype=np.int32)
    phys_to_old = np.asarray(mapping["phys_to_old"], dtype=np.int32)
    if n_symbols is None:
        n_symbols = int(n_vars) // 10
    if old_to_phys.shape != (n_vars,) or phys_to_old.shape != (n_vars,):
        raise ValueError("interleaver mappings must cover every variable")
    mapped_indices = remap_csr(indices, old_to_phys)
    old_rows = csr_row_degrees(indptr)
    new_rows = csr_row_degrees(indptr)
    old_cols = csr_column_degrees(indices, n_vars)
    new_cols = csr_column_degrees(mapped_indices, n_vars)
    inverse = bool(
        old_to_phys.shape == (n_vars,)
        and phys_to_old.shape == (n_vars,)
        and np.array_equal(phys_to_old[old_to_phys], np.arange(n_vars))
        and np.array_equal(old_to_phys[phys_to_old], np.arange(n_vars))
    )
    symbol_counts = np.bincount(old_to_phys // 10, minlength=n_symbols)
    mapped_high_columns = np.asarray(mapping.get("high_columns", ()), dtype=np.int32)
    high_end = int(mapped_high_columns.size) if mapped_high_columns.size else min(int(info_end), n_vars)
    high_symbol_counts = np.bincount(old_to_phys[:high_end] // 10, minlength=n_symbols)
    old_rank = gf2_rank_csr(indptr, indices)
    new_rank = gf2_rank_csr(indptr, mapped_indices)
    old_pure = pure_h_cycle_stats(indptr, indices)
    new_pure = pure_h_cycle_stats(indptr, mapped_indices)
    old_symbol = symbol_factor_stats(indptr, indices, n_vars, n_symbols)
    new_symbol = symbol_factor_stats(indptr, mapped_indices, n_vars, n_symbols)
    prefix_nesting = bool(
        np.array_equal(np.cumsum(old_rows, dtype=np.int64), np.cumsum(new_rows, dtype=np.int64))
        and np.all(np.diff(indptr) >= 0)
    )
    shape_preserved = bool(
        old_to_phys.size == int(n_vars)
        and phys_to_old.size == int(n_vars)
        and mapped_indices.shape == indices.shape
        and indptr.size >= 1
    )
    return {
        "bijection": inverse,
        "shape_preserved": shape_preserved,
        "row_degree_multiset_preserved": bool(np.array_equal(np.sort(old_rows), np.sort(new_rows))),
        "column_degree_multiset_preserved": bool(np.array_equal(np.sort(old_cols), np.sort(new_cols))),
        "symbol_slot_counts": symbol_counts.astype(int).tolist(),
        "all_symbols_have_ten_slots": bool(np.all(symbol_counts == 10)),
        "high_symbol_counts": high_symbol_counts.astype(int).tolist(),
        "high_distribution_valid": bool(np.all(np.isin(high_symbol_counts, (1, 2))),),
        "rank_old": int(old_rank),
        "rank_new": int(new_rank),
        "rank_preserved": bool(old_rank == new_rank),
        "prefix_nesting_preserved": prefix_nesting,
        "old_pure_h_four_cycles": old_pure["four_cycles"],
        "new_pure_h_four_cycles": new_pure["four_cycles"],
        "old_pure_h_collision_pairs": old_pure["collision_pairs"],
        "new_pure_h_collision_pairs": new_pure["collision_pairs"],
        "pure_h_four_cycles": new_pure["four_cycles"],
        "pure_h_collision_pairs": new_pure["collision_pairs"],
        "symbol_sigma_c2": new_symbol["symbol_sigma_c2"],
        "symbol_collision_rows": new_symbol["symbol_collision_rows"],
        "old_symbol_stats": old_symbol,
        "new_symbol_stats": new_symbol,
        "mapped_indices": mapped_indices,
    }


def wrapped_laplace_kernel(
    mu: float = float(M2_PARAMS["mu"]),
    scale: float = float(M2_PARAMS["scale"]),
    eps: float = float(M2_PARAMS["eps"]),
    q: int = Q,
) -> np.ndarray:
    if int(q) != Q or float(scale) <= 0.0 or not 0.0 <= float(eps) <= 1.0:
        raise ValueError("M2 parameters do not match the frozen positive model")
    d = np.arange(q, dtype=np.float64)
    signed = ((d + q // 2) % q) - q // 2
    shape = sum(np.exp(-np.abs(signed + period * q - float(mu)) / float(scale)) for period in (-1, 0, 1))
    shape = shape / np.sum(shape)
    kernel = (1.0 - float(eps)) * shape + float(eps) / q
    return kernel / np.sum(kernel)


def m2_conditional_probabilities(bob_symbols: np.ndarray) -> np.ndarray:
    """Return P(a|b) rows in physical symbol order, before log protection."""
    bob = np.asarray(bob_symbols, dtype=np.int64)
    if bob.ndim != 1 or np.any(bob < 0) or np.any(bob >= Q):
        raise ValueError("bob_symbols must be a one-dimensional array in [0,1023]")
    kernel = wrapped_laplace_kernel()
    states = np.arange(Q, dtype=np.int64)
    probabilities = kernel[(states[None, :] - bob[:, None]) % Q]
    if not np.all(np.isfinite(probabilities)) or np.any(probabilities <= 0.0):
        raise ValueError("M2 conditional probabilities must be finite and positive")
    probabilities = probabilities / probabilities.sum(axis=1, keepdims=True)
    return probabilities


def build_m2_prior_logp(bob_symbols: np.ndarray) -> np.ndarray:
    """Build the frozen M2 prior from Bob symbols only."""
    probabilities = m2_conditional_probabilities(bob_symbols)
    # The floor protects only the log operation; do not renormalize after it.
    out = np.log(np.maximum(probabilities, 1e-300))
    if not np.all(np.isfinite(out)):
        raise ValueError("M2 prior log probabilities must be finite")
    return out


def build_m0_prior_logp(bob_symbols: np.ndarray, probabilities: np.ndarray | None = None) -> np.ndarray:
    """Build a supplied CAL-fitted M0 table, with no Alice input."""
    bob = np.asarray(bob_symbols, dtype=np.int64)
    if probabilities is None:
        probabilities = np.full((Q, Q), 1.0 / Q, dtype=np.float64)
    table = np.asarray(probabilities, dtype=np.float64)
    if table.shape != (Q, Q) or np.any(table <= 0) or not np.all(np.isfinite(table)):
        raise ValueError("M0 probability table must be positive finite (1024,1024)")
    table = table / table.sum(axis=1, keepdims=True)
    if bob.ndim != 1 or np.any(bob < 0) or np.any(bob >= Q):
        raise ValueError("bob_symbols must be a one-dimensional array in [0,1023]")
    return np.log(table[bob])


def summarize_values(values: np.ndarray) -> dict[str, Any]:
    arr = np.asarray(values, dtype=np.float64).reshape(-1)
    if arr.size == 0:
        return {
            "signed_quantiles": [0.0] * len(QUANTILES),
            "abs_quantiles": [0.0] * len(QUANTILES),
            "max_abs": 0.0,
            "zero_count": 0,
        }
    return {
        "signed_quantiles": np.quantile(arr, QUANTILES).astype(float).tolist(),
        "abs_quantiles": np.quantile(np.abs(arr), QUANTILES).astype(float).tolist(),
        "max_abs": float(np.max(np.abs(arr))),
        "zero_count": int(np.count_nonzero(np.abs(arr) <= ZERO_TOL)),
    }


def sign_values(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    return np.where(arr < -ZERO_TOL, 0, np.where(arr > ZERO_TOL, 2, 1)).astype(np.int8)


def sign_transition(before: np.ndarray, after: np.ndarray) -> list[list[int]]:
    lhs = sign_values(before).reshape(-1)
    rhs = sign_values(after).reshape(-1)
    table = np.zeros((3, 3), dtype=np.int64)
    for a, b in zip(lhs.tolist(), rhs.tolist()):
        table[int(a), int(b)] += 1
    return table.tolist()


def _incident_sum(check_to_variable: np.ndarray, indices: np.ndarray, nbit: int) -> np.ndarray:
    return np.bincount(np.asarray(indices, dtype=np.int64), weights=np.asarray(check_to_variable, dtype=np.float64), minlength=nbit).astype(np.float64)


def checkpoint_metrics(
    prior_logp: np.ndarray,
    pre_c2v: np.ndarray,
    post: Mapping[str, Any],
    indptr: np.ndarray,
    indices: np.ndarray,
    syndrome_target: np.ndarray,
    bob_bits: np.ndarray,
    core_target_updates: int,
    diagnostic_target_updates: int,
    diagnostic_readout_evaluations: int,
    l0_values: np.ndarray | None = None,
    pre_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    prior = _validate_prior(prior_logp)
    indptr = np.asarray(indptr, dtype=np.int32)
    indices = np.asarray(indices, dtype=np.int32)
    if pre_state is None:
        pre = rebuild_factor_state(prior, pre_c2v, indptr, indices)
    else:
        pre = {
            "bit_to_factor": np.asarray(pre_state["bit_to_factor"], dtype=np.float64),
            "factor_to_bit": np.asarray(pre_state["factor_to_bit"], dtype=np.float64),
            "app_raw": np.asarray(pre_state["app_raw"], dtype=np.float64),
        }
        if pre["bit_to_factor"].shape != (prior.shape[0], 10) or pre["factor_to_bit"].shape != (prior.shape[0], 10):
            raise ValueError("pre_state factor arrays have incompatible shapes")
        if pre["app_raw"].shape != (prior.shape[0] * 10,):
            raise ValueError("pre_state app_raw has incompatible shape")
    post_c2v = np.asarray(post["check_to_variable"], dtype=np.float64)
    post_f2b = np.asarray(post["factor_to_bit"], dtype=np.float64)
    post_btf = np.asarray(post["bit_to_factor"], dtype=np.float64)
    post_app_raw = np.asarray(post["app_raw"], dtype=np.float64)
    nbit = post_app_raw.size
    if nbit != prior.shape[0] * 10 or post_f2b.shape != (prior.shape[0], 10) or post_btf.shape != (prior.shape[0], 10):
        raise ValueError("post factor state shapes are incompatible")
    f_pre = pre["factor_to_bit"].reshape(-1)
    f_post = post_f2b.reshape(-1)
    s_pre = _incident_sum(pre_c2v, indices, nbit)
    s_post = _incident_sum(post_c2v, indices, nbit)
    a_pre = f_pre + s_pre
    a_post = f_post + s_post
    if l0_values is None:
        l0 = _factor_batch(prior, np.zeros((prior.shape[0], 10), dtype=np.float64)).reshape(-1)
    else:
        l0 = np.asarray(l0_values, dtype=np.float64).reshape(-1)
        if l0.shape != (nbit,):
            raise ValueError("l0_values shape mismatch")
    hard_bits = np.asarray(post["hard_bits"], dtype=np.uint8)
    target = np.asarray(syndrome_target, dtype=np.uint8)
    if hard_bits.shape != (nbit,):
        raise ValueError("hard_bits shape mismatch")
    # Recompute the candidate syndrome from H_arm; a caller-provided observed
    # array is a readout convenience, not the diagnostic source of truth.
    observed = _syndrome_from_bits(hard_bits, indptr, indices)
    if target.shape != observed.shape:
        raise ValueError("syndrome_target shape mismatch")
    violation = int(np.count_nonzero(observed ^ target))
    bob = np.asarray(bob_bits, dtype=np.uint8)
    if bob.shape != hard_bits.shape:
        raise ValueError("bob_bits shape mismatch")
    hard_symbols = _pack_symbols(hard_bits)
    bob_symbols = _pack_symbols(bob)
    clip_counts = {
        "c2v_at_clip": int(np.count_nonzero(np.abs(post_c2v) >= LLR_CLIP - 1e-12)),
        "f2b_at_clip": int(np.count_nonzero(np.abs(post_f2b) >= LLR_CLIP - 1e-12)),
        "app_preclip_exceed": int(np.count_nonzero(np.abs(post_app_raw) > LLR_CLIP)),
    }
    return {
        "L0": summarize_values(l0),
        "F_pre": summarize_values(f_pre),
        "F_post": summarize_values(f_post),
        "S_pre": summarize_values(s_pre),
        "S_post": summarize_values(s_post),
        "A_raw_pre": summarize_values(a_pre),
        "A_raw_post": summarize_values(a_post),
        "delta_app": summarize_values(a_post - a_pre),
        "sign_L0_to_F_post": sign_transition(l0, f_post),
        "sign_F_post_to_A_raw_post": sign_transition(f_post, a_post),
        "candidate_syndrome_violation": violation,
        "candidate_vs_bob_bit_flips": int(np.count_nonzero(hard_bits != bob)),
        "candidate_vs_bob_symbol_flips": int(np.count_nonzero(hard_symbols != bob_symbols)),
        "residual": float(post["residuals"][-1]) if len(post["residuals"]) else 0.0,
        "sweeps": int(len(post["residuals"])),
        "edge_updates": int(post["edge_updates"]),
        "converged": bool(post["converged"]),
        "finite": bool(post["finite"]),
        "max_llr": float(post["max_llr"]),
        "max_abs_c2v": float(np.max(np.abs(post_c2v))) if post_c2v.size else 0.0,
        "max_abs_incident_c2v_sum": float(np.max(np.abs(s_post))) if s_post.size else 0.0,
        "clip_counts": clip_counts,
        "c2v_at_clip_count": clip_counts["c2v_at_clip"],
        "f2b_at_clip_count": clip_counts["f2b_at_clip"],
        "app_preclip_exceed_count": clip_counts["app_preclip_exceed"],
        "local_factor_target_updates": int(core_target_updates),
        "state_evaluations": int(Q * core_target_updates),
        "diagnostic_factor_target_updates": int(diagnostic_target_updates),
        "diagnostic_state_evaluations": int(Q * diagnostic_target_updates),
        "diagnostic_readout_evaluations": int(diagnostic_readout_evaluations),
        "syndrome_satisfied": bool(bool(post["finite"]) and violation == 0),
        "tag_bits": 0,
        "tag_ok": "NOT_APPLICABLE",
        "oracle_exact": None,
        "not_recorded_reason": "oracle_runs_after_arm_end",
    }


def new_accounting() -> dict[str, int]:
    return {
        "syndrome_rows_published": 0,
        "syndrome_bits_published": 0,
        "tag_bits_published": 0,
        "control_bits_sent": 0,
        "disclosed_rows": 0,
        "public_disclosure_bits": 0,
    }


def publish_checkpoint(accounting: dict[str, int], checkpoint_rows: int, first: bool) -> dict[str, int]:
    rows = int(checkpoint_rows)
    previous = int(accounting["disclosed_rows"])
    if rows < previous:
        raise ValueError("checkpoint rows must be monotone")
    if not first:
        accounting["control_bits_sent"] += 1
    accounting["syndrome_rows_published"] += rows - previous
    accounting["syndrome_bits_published"] += rows - previous
    accounting["disclosed_rows"] = rows
    accounting["public_disclosure_bits"] = accounting["syndrome_bits_published"] + accounting["control_bits_sent"]
    if accounting["disclosed_rows"] != accounting["syndrome_rows_published"] or accounting["disclosed_rows"] != accounting["syndrome_bits_published"]:
        raise AssertionError("syndrome accounting diverged")
    return accounting


def _arm_counters() -> dict[str, int]:
    return {
        "local_factor_target_updates": 0,
        "state_evaluations": 0,
        "diagnostic_L0_target_updates": 0,
        "diagnostic_checkpoint_rebuild_target_updates": 0,
        "diagnostic_final_readout_target_updates": 0,
        "diagnostic_factor_target_updates": 0,
        "diagnostic_state_evaluations": 0,
        "diagnostic_readout_evaluations": 0,
        "total_target_updates": 0,
        "total_state_evaluations": 0,
    }


def _finish_counters(counters: dict[str, int]) -> None:
    counters["diagnostic_factor_target_updates"] = (
        counters["diagnostic_L0_target_updates"]
        + counters["diagnostic_checkpoint_rebuild_target_updates"]
        + counters["diagnostic_final_readout_target_updates"]
    )
    counters["diagnostic_state_evaluations"] = Q * counters["diagnostic_factor_target_updates"]
    counters["total_target_updates"] = counters["local_factor_target_updates"] + counters["diagnostic_factor_target_updates"]
    counters["total_state_evaluations"] = counters["state_evaluations"] + counters["diagnostic_state_evaluations"]


def run_arm_synthetic(
    arm_id: str,
    prior_logp: np.ndarray,
    syndrome_full: np.ndarray,
    alice_bits: np.ndarray,
    bob_bits: np.ndarray,
    indptr_full: np.ndarray,
    indices_full: np.ndarray,
    decoder: Callable[..., Mapping[str, Any]],
    schedule: str,
    checkpoint_rows: Sequence[int] = CHECKPOINT_ROWS,
    max_per_checkpoint: int = MAX_SWEEPS_PER_CHECKPOINT,
    max_total: int = MAX_TOTAL_SWEEPS,
) -> dict[str, Any]:
    """Run one fully synthetic arm; retained for T2 fake-runner tests."""
    prior = _validate_prior(prior_logp)
    syndrome = np.asarray(syndrome_full, dtype=np.uint8)
    alice = np.asarray(alice_bits, dtype=np.uint8)
    bob = np.asarray(bob_bits, dtype=np.uint8)
    indptr_full = np.asarray(indptr_full, dtype=np.int32)
    indices_full = np.asarray(indices_full, dtype=np.int32)
    if schedule not in {"layered", "flooding"}:
        raise ValueError("schedule must be 'layered' or 'flooding'")
    if int(max_per_checkpoint) < 0 or int(max_total) < 0:
        raise ValueError("update budgets must be nonnegative")
    if syndrome.shape != (len(indptr_full) - 1,) or alice.shape != bob.shape or alice.shape != (prior.shape[0] * 10,):
        raise ValueError("synthetic arm shapes are inconsistent")
    _validate_csr(indptr_full, indices_full, prior.shape[0] * 10)
    checkpoint_tuple = tuple(int(x) for x in checkpoint_rows)
    if any(x < 0 or x >= len(indptr_full) for x in checkpoint_tuple) or any(
        right <= left for left, right in zip(checkpoint_tuple, checkpoint_tuple[1:])
    ):
        raise ValueError("checkpoint rows must be strictly increasing and inside the CSR")
    counters = _arm_counters()
    accounting = new_accounting()
    checkpoint_metrics_list: list[dict[str, Any]] = []
    total_used = 0
    decoder_calls = 0
    previous_c2v = np.zeros(0, dtype=np.float64)
    previous_nnz = 0
    first_satisfied: int | None = None
    final_candidate: np.ndarray | None = None
    final_syndrome_satisfied: bool | None = None
    final_checkpoint: int | None = None
    status = "LADDER_EXHAUSTED"
    stop_reason = "ladder_exhausted"
    l0_values: np.ndarray | None = None
    budget_limit = min(int(max_total), MAX_TOTAL_SWEEPS)
    for checkpoint_index, rows in enumerate(checkpoint_tuple):
        remaining = budget_limit - total_used
        if remaining <= 0:
            status = "BUDGET_EXHAUSTED"
            stop_reason = "budget_exhausted_normal"
            break
        max_updates = min(int(max_per_checkpoint), MAX_SWEEPS_PER_CHECKPOINT, remaining)
        if max_updates <= 0:
            status = "BUDGET_EXHAUSTED"
            stop_reason = "budget_exhausted_normal"
            break
        # L0 is a single per-arm diagnostic stage.  Delay it until a real
        # checkpoint is about to run so a zero-budget arm has no work/counts.
        if l0_values is None:
            l0_values = _factor_batch(prior, np.zeros((prior.shape[0], 10), dtype=np.float64)).reshape(-1)
            # The legacy flooding adapter's diagnostic contract is defined
            # over the frozen full block, even when this synthetic fixture
            # uses a smaller prior.  Layered owns its actual symbol count.
            counters["diagnostic_L0_target_updates"] = NBIT if schedule == "flooding" else int(prior.shape[0] * 10)
        active_nnz = int(indptr_full[rows])
        indptr = indptr_full[: rows + 1]
        indices = indices_full[:active_nnz]
        warm = np.zeros(active_nnz, dtype=np.float64)
        if previous_nnz:
            warm[:previous_nnz] = previous_c2v[:previous_nnz]
        publish_checkpoint(accounting, rows, first=(checkpoint_index == 0))
        accounting_snapshot = dict(accounting)
        pre_c2v = warm.copy()
        try:
            if schedule == "layered":
                result = decoder(prior, syndrome[:rows], indptr, indices, max_updates, warm)
            else:
                result = decoder(
                    prior,
                    syndrome[:rows],
                    indptr=indptr,
                    indices=indices,
                    max_iter=max_updates,
                    warm_start_c2v=warm,
                )
            decoder_calls += 1
        except TimeoutError:
            status = "BLOCKED"
            stop_reason = "timeout"
            break
        except Exception:
            status = "BLOCKED"
            stop_reason = "exception"
            break
        # The frozen flooding adapter predates the diagnostic counter fields.
        # Derive those fields once from its explicit final arrays/iteration
        # count; the layered API must provide them natively.
        try:
            result = dict(result)
        except Exception:
            status = "BLOCKED"
            stop_reason = "decoder_result_not_mapping"
            break
        if schedule == "flooding":
            # Do not trust a counter emitted by the old/fake flooding
            # adapter: each flooding iteration evaluates every frozen-block
            # factor target, i.e. NBIT targets.
            result["local_factor_target_updates"] = len(result["residuals"]) * NBIT
            result["diagnostic_readout_evaluations"] = int(np.asarray(result["hard_bits"]).size)
            result["app_raw"] = np.asarray(result["factor_to_bit"], dtype=np.float64).reshape(-1) + np.asarray(
                result["bit_to_factor"], dtype=np.float64
            ).reshape(-1)
            result["edge_updates"] = len(result["residuals"]) * int(indices.size)
            result["max_llr"] = float(np.max(np.abs(np.asarray(result["app_llr"], dtype=np.float64)))) if np.asarray(result["app_llr"]).size else 0.0
            result["converged"] = bool(len(result["residuals"]) > 0 and float(result["residuals"][-1]) < CONVERGENCE_TOL)
        required = {
            "residuals",
            "finite",
            "hard_bits",
            "hard_symbols",
            "syndrome_observed",
            "check_to_variable",
            "factor_to_bit",
            "bit_to_factor",
            "local_factor_target_updates",
            "diagnostic_readout_evaluations",
            "converged",
            "edge_updates",
            "max_llr",
        }
        if schedule == "layered":
            required.update({"app_raw", "_pre_state", "diagnostic_checkpoint_rebuild_target_updates"})
        missing = sorted(key for key in required if key not in result)
        if missing:
            status = "BLOCKED"
            stop_reason = "decoder_result_missing_required_fields"
            break
        residuals = result["residuals"]
        try:
            used = int(len(residuals))
        except Exception:
            status = "BLOCKED"
            stop_reason = "decoder_result_invalid_residuals"
            break
        if used < 0 or used > max_updates or total_used + used > budget_limit or total_used + used > MAX_TOTAL_SWEEPS:
            status = "BLOCKED"
            stop_reason = "budget_guard_failed"
            break
        total_used += used
        if schedule == "layered":
            checkpoint_diag = int(result["diagnostic_checkpoint_rebuild_target_updates"])
            if checkpoint_diag != prior.shape[0] * 10:
                status = "BLOCKED"
                stop_reason = "diagnostic_counter_mismatch"
                break
            counters["diagnostic_checkpoint_rebuild_target_updates"] += checkpoint_diag
            core_delta = int(result["local_factor_target_updates"])
            pre_state = result["_pre_state"]
            diag_delta = checkpoint_diag
        else:
            core_delta = used * NBIT
            if int(result["local_factor_target_updates"]) != core_delta:
                status = "BLOCKED"
                stop_reason = "core_counter_mismatch"
                break
            counters["diagnostic_final_readout_target_updates"] += NBIT
            pre_state = None
            diag_delta = NBIT
        if core_delta < 0:
            status = "BLOCKED"
            stop_reason = "core_counter_invalid"
            break
        counters["local_factor_target_updates"] += core_delta
        counters["state_evaluations"] = Q * counters["local_factor_target_updates"]
        readout_delta = int(result["diagnostic_readout_evaluations"])
        if readout_delta < 0:
            status = "BLOCKED"
            stop_reason = "readout_counter_invalid"
            break
        counters["diagnostic_readout_evaluations"] += readout_delta
        if not bool(result["finite"]):
            status = "BLOCKED"
            stop_reason = "nonfinite"
        try:
            metrics = checkpoint_metrics(
                prior,
                pre_c2v,
                result,
                indptr,
                indices,
                syndrome[:rows],
                bob,
                core_delta,
                diag_delta,
                readout_delta,
                l0_values=l0_values,
                pre_state=pre_state,
            )
        except Exception:
            status = "BLOCKED"
            stop_reason = "metrics_failed"
            break
        metrics["checkpoint_rows"] = rows
        metrics["active_rows"] = rows
        metrics["iterations"] = used
        metrics["final_checkpoint_rows"] = None
        metrics["final_syndrome_satisfied"] = None
        metrics["final_oracle_exact"] = None
        metrics["diagnostic_exact"] = None
        metrics["syndrome_collision_wrong"] = None
        metrics["accounting"] = accounting_snapshot
        checkpoint_metrics_list.append(metrics)
        if metrics["syndrome_satisfied"] and first_satisfied is None:
            first_satisfied = rows
        final_candidate = np.asarray(result["hard_bits"], dtype=np.uint8).copy()
        final_syndrome_satisfied = bool(metrics["syndrome_satisfied"])
        final_checkpoint = rows
        previous_c2v = np.asarray(result["check_to_variable"], dtype=np.float64).copy()
        previous_nnz = active_nnz
        if status == "BLOCKED":
            break
    _finish_counters(counters)
    if final_candidate is None:
        final_oracle = None
        diagnostic_exact = None
        collision_wrong = None
    else:
        final_oracle = bool(np.array_equal(final_candidate, alice))
        diagnostic_exact = bool(bool(final_syndrome_satisfied) and final_oracle)
        collision_wrong = bool(bool(final_syndrome_satisfied) and not final_oracle)
    if status == "LADDER_EXHAUSTED" and total_used >= budget_limit:
        status = "BUDGET_EXHAUSTED"
        stop_reason = "budget_exhausted_normal"
    accounting["public_disclosure_bits"] = accounting["syndrome_bits_published"] + accounting["control_bits_sent"]
    return {
        "arm_id": arm_id,
        "status": status,
        "graph_id": "original",
        "prior_id": "synthetic",
        "schedule_id": schedule,
        "attempted_checkpoints": len(checkpoint_metrics_list),
        "stop_reason": stop_reason,
        "first_syndrome_satisfied_ckpt": first_satisfied,
        "final_checkpoint_rows": final_checkpoint,
        "final_syndrome_satisfied": final_syndrome_satisfied,
        "final_oracle_exact": final_oracle,
        "diagnostic_exact": diagnostic_exact,
        "syndrome_collision_wrong": collision_wrong,
        "sweeps_used": total_used,
        "decoder_calls": decoder_calls,
        "edge_updates": int(sum(x["edge_updates"] for x in checkpoint_metrics_list)),
        **counters,
        "accounting": accounting,
        "checkpoint_metrics": checkpoint_metrics_list,
        "common_metrics": {},
        "new_metric_fields": ["L0", "F", "S", "A_raw"],
        "posthoc_oracle": {"runs_after_arm_end": True, "final_oracle_exact": final_oracle},
        "tag_bits": 0,
        "tag_ok": "NOT_APPLICABLE",
    }


def _distinct_symbol_work(indptr: np.ndarray, indices: np.ndarray, rows: int) -> int:
    total = 0
    for row in range(int(rows)):
        start, end = int(indptr[row]), int(indptr[row + 1])
        total += int(np.unique(np.asarray(indices[start:end], dtype=np.int64) // 10).size)
    return total


def current_rss_bytes() -> int:
    import os

    try:
        import psutil
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("psutil is required for the frozen RSS sampling contract") from exc
    return int(psutil.Process(os.getpid()).memory_info().rss)


def cost_preflight(
    indptr: np.ndarray,
    indices: np.ndarray,
    representative_rows: Sequence[int] = (160, 2048, 4096, 8192, 9036),
    seed: int = SEED,
) -> dict[str, Any]:
    """Measure the synthetic layered kernel and compute the frozen projection."""
    indptr = np.asarray(indptr, dtype=np.int32)
    indices = np.asarray(indices, dtype=np.int32)
    _validate_mother_contract(indptr, indices)
    representative_tuple = tuple(int(row) for row in representative_rows)
    if representative_tuple != (160, 2048, 4096, 8192, 9036):
        raise ValueError("cost preflight representative rows are frozen")
    rng = np.random.default_rng(int(seed))
    bob = rng.integers(0, Q, size=N, dtype=np.uint16)
    prior = build_m2_prior_logp(bob)
    syndrome = rng.integers(0, 2, size=M, dtype=np.uint8)

    # Compile/lazily initialize every kernel used by the timed path before
    # collecting rates.  Compilation is a one-time environment cost, whereas
    # the projection estimates repeated checkpoint work in one invocation.
    warm_rows = representative_tuple[0]
    warm_nnz = int(indptr[warm_rows])
    warm_indptr = indptr[: warm_rows + 1]
    warm_indices = indices[:warm_nnz]
    warm_c2v = np.zeros(warm_nnz, dtype=np.float64)
    rebuild_factor_state(prior, warm_c2v, warm_indptr, warm_indices)
    run_layered_decoder(
        prior,
        syndrome[:warm_rows],
        warm_indptr,
        warm_indices,
        1,
        warm_c2v,
    )

    samples: list[dict[str, Any]] = []
    rebuild_rates: list[float] = []
    overhead_samples: list[float] = []
    rss_samples = [current_rss_bytes()]
    for index, rows in enumerate(tuple(int(x) for x in representative_rows)):
        active_nnz = int(indptr[rows])
        active_indptr = indptr[: rows + 1]
        active_indices = indices[:active_nnz]
        warm = np.zeros(active_nnz, dtype=np.float64)
        if index % 2:
            warm = np.linspace(-0.05, 0.05, active_nnz, dtype=np.float64)
        rss_samples.append(current_rss_bytes())
        rebuild_start = time.perf_counter()
        rebuild_factor_state(prior, warm, active_indptr, active_indices)
        rebuild_seconds = float(time.perf_counter() - rebuild_start)
        start = time.perf_counter()
        result = run_layered_decoder(prior, syndrome[:rows], active_indptr, active_indices, 1, warm)
        full_elapsed = float(time.perf_counter() - start)
        # run_layered_decoder performs the required checkpoint rebuild before
        # its first sweep.  Remove the independently timed rebuild so tau is a
        # core-kernel rate, while tau_diag is measured from that rebuild alone.
        elapsed = max(0.0, full_elapsed - rebuild_seconds)
        rss_samples.append(current_rss_bytes())
        work = 10 * _distinct_symbol_work(indptr, indices, rows)
        if work <= 0:
            raise ValueError("representative point has no layered work")
        if len(result["residuals"]) != 1:
            raise ValueError("cost preflight must execute exactly one complete sweep per point")
        rebuild_rates.append(rebuild_seconds / float(N * 10))
        overhead_start = time.perf_counter()
        # Non-core fixed work represented by each checkpoint: slice the active
        # CSR/syndrome and allocate the carried state.  Keep this timer
        # separate from both the decoder and factor rebuild timers.
        _ = (active_indptr.copy(), active_indices.copy(), np.asarray(syndrome[:rows], dtype=np.uint8).copy(), np.zeros(active_nnz, dtype=np.float64))
        overhead_samples.append(max(0.0, float(time.perf_counter() - overhead_start)))
        samples.append(
            {
                "active_rows": int(rows),
                "active_nnz": active_nnz,
                "target_work_U_r": int(work),
                "elapsed_s": elapsed,
                "full_decoder_elapsed_s": full_elapsed,
                "actual_sweeps": len(result["residuals"]),
                "local_factor_target_updates": int(result["local_factor_target_updates"]),
                "state_evaluations": int(result["state_evaluations"]),
                "warm_state": "zero" if index % 2 == 0 else "nonzero",
                "rss_before_after": [rss_samples[-2], rss_samples[-1]],
                "rebuild_seconds": rebuild_seconds,
                "noncore_overhead_s": overhead_samples[-1],
            }
        )
    tau = max(float(sample["elapsed_s"]) / float(sample["target_work_U_r"]) for sample in samples)
    tau_diag = max(rebuild_rates)
    h = max(overhead_samples)
    work_ladder = sum(10 * _distinct_symbol_work(indptr, indices, rows) for rows in CHECKPOINT_ROWS)
    diagnostic_targets = N * 10 * (1 + len(CHECKPOINT_ROWS))
    projected = (tau * work_ladder + tau_diag * diagnostic_targets + len(CHECKPOINT_ROWS) * h) * 1.2
    return {
        "status": "PASS" if projected <= 600.0 else "PLAN_REVISE_REQUIRED",
        "representative_rows": list(map(int, representative_rows)),
        "samples": samples,
        "tau_s_per_target": float(tau),
        "tau_diag_s_per_target": float(tau_diag),
        "h_s": float(h),
        "W_targets": int(work_ladder),
        "D_targets": int(diagnostic_targets),
        "projected_L_wall_s": float(projected),
        "core_timer_excludes_rebuild": True,
        "diagnostic_rebuild_timer": "one independently timed rebuild per representative point",
        "static_target_upper_bound": int(LAYERED_TARGET_UPPER_BOUND),
        "static_state_upper_bound": int(LAYERED_STATE_UPPER_BOUND),
        "rss_sampling": "psutil.Process(os.getpid()).memory_info().rss at prep and each representative point",
        "peak_rss_bytes": int(max(rss_samples)),
        "rss_samples": [int(x) for x in rss_samples],
        "synthetic_only": True,
        "real_decoder_executed": False,
        "timing_warmup_excluded": True,
    }


__all__ = [
    "B_BITS",
    "CHECKPOINT_ROWS",
    "CONVERGENCE_TOL",
    "INFO_END",
    "LLR_CLIP",
    "LAYERED_ACTIVE_ROW_SUM",
    "LAYERED_TARGET_UPPER_BOUND",
    "LAYERED_STATE_UPPER_BOUND",
    "M0_CE_CAL_CV",
    "M0_LAMBDA",
    "M2_PARAMS",
    "M2_HISTORICAL_CE",
    "MAX_SWEEPS_PER_CHECKPOINT",
    "MAX_TOTAL_SWEEPS",
    "N",
    "NBIT",
    "Q",
    "build_degree_balanced_interleaver",
    "build_m0_prior_logp",
    "build_m2_prior_logp",
    "m2_conditional_probabilities",
    "checkpoint_metrics",
    "cost_preflight",
    "csr_column_degrees",
    "csr_row_degrees",
    "factor_batch",
    "gf2_rank_csr",
    "get_flooding_decoder",
    "get_mother_csr",
    "new_accounting",
    "publish_checkpoint",
    "rebuild_factor_state",
    "remap_csr",
    "run_arm_synthetic",
    "run_layered_decoder",
    "sign_transition",
    "local_factor_extrinsic",
    "pure_h_cycle_stats",
    "symbol_factor_stats",
    "summarize_values",
    "verify_interleaver",
    "wrapped_laplace_kernel",
]
