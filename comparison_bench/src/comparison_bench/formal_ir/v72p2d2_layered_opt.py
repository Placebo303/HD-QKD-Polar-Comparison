"""V72P2D2 layered equivalent optimization (synthetic benchmark only).

Equivalent to v72p2d2_orthogonal_triage.run_layered_decoder in math order:
row-serial layered sweeps, same prior/clip/tol/mother, same checkpoint
contract, same diagnostic counters. Optimizations only (no damping, no
flooding, no ckpt/sweep reduction, no clip/tol/prior/mother change):

- numba SPA row kernel (same clip/flip/epsilon as _spa_row)
- cache row->symbols once per decoder call (no per-row np.unique)
- precomputed edge->var flat views, reused workspace (no per-row reshape alloc)
- in-place per-symbol 10-target factor batch (no full (1024,10) out per row)
- skip per-row full app_raw rebuild (dead work; final app identical)
- metrics still once per checkpoint via run_arm_synthetic (unchanged)
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from comparison_bench.formal_ir import v72p2d2_orthogonal_triage as base

Q = base.Q
LLR_CLIP = base.LLR_CLIP
CONVERGENCE_TOL = base.CONVERGENCE_TOL
MAX_TOTAL_SWEEPS = base.MAX_TOTAL_SWEEPS
B_BITS = base.B_BITS

try:
    import numba as _numba

    HAS_NUMBA = bool(base.HAS_NUMBA)
except ImportError:  # pragma: no cover
    _numba = None
    HAS_NUMBA = False

if HAS_NUMBA:

    @_numba.njit(cache=False)
    def _spa_row_numba(v2c, syndrome, out):
        d = v2c.shape[0]
        if d == 0:
            return out
        flip = -1.0 if int(syndrome) else 1.0
        if d % 2 == 1:
            flip = -flip
        for i in range(d):
            if d == 1:
                prod = 1.0
            else:
                prod = 1.0
                for j in range(d):
                    if j == i:
                        continue
                    t = math.tanh(float(v2c[j]) / 2.0)
                    if t > 0.999999999999:
                        t = 0.999999999999
                    elif t < -0.999999999999:
                        t = -0.999999999999
                    prod *= t
            prod = flip * prod
            eps = 1e-12
            if prod > 1.0 - eps:
                prod = 1.0 - eps
            elif prod < -1.0 + eps:
                prod = -1.0 + eps
            v = 2.0 * 0.5 * math.log((1.0 + prod) / (1.0 - prod))
            if v > 20.0:
                v = 20.0
            elif v < -20.0:
                v = -20.0
            out[i] = v
        return out

    @_numba.njit(cache=False)
    def _factor_update_inplace_numba(prior, btf, f2b, symbols, b_bits, term):
        # 10-target batch per symbol; same math as base._factor_symbols_numba.
        for si in range(symbols.shape[0]):
            sym = int(symbols[si])
            for a in range(1024):
                value = 0.0
                for b in range(10):
                    value += float(b_bits[a, b]) * float(btf[sym, b])
                term[a] = value
            for b in range(10):
                max1 = -1.0e300
                max0 = -1.0e300
                for a in range(1024):
                    value = float(prior[sym, a]) + term[a] - float(b_bits[a, b]) * float(btf[sym, b])
                    if b_bits[a, b] == 1:
                        if value > max1:
                            max1 = value
                    elif value > max0:
                        max0 = value
                sum1 = 0.0
                sum0 = 0.0
                for a in range(1024):
                    value = float(prior[sym, a]) + term[a] - float(b_bits[a, b]) * float(btf[sym, b])
                    if b_bits[a, b] == 1:
                        sum1 += math.exp(value - max1)
                    else:
                        sum0 += math.exp(value - max0)
                value = (max1 + math.log(sum1)) - (max0 + math.log(sum0))
                if value > 20.0:
                    value = 20.0
                elif value < -20.0:
                    value = -20.0
                f2b[sym, b] = value
        return f2b


def run_layered_decoder_opt(
    prior_logp: np.ndarray,
    syndrome_target: np.ndarray,
    indptr: np.ndarray,
    indices: np.ndarray,
    max_sweeps: int,
    warm_start_c2v: np.ndarray,
) -> dict[str, Any]:
    """Drop-in equivalent of base.run_layered_decoder (same keys/counters)."""
    prior = base._validate_prior(prior_logp)
    syndrome = np.asarray(syndrome_target, dtype=np.uint8)
    indptr = np.asarray(indptr, dtype=np.int32)
    indices = np.asarray(indices, dtype=np.int32)
    nbit = prior.shape[0] * 10
    base._validate_csr(indptr, indices, nbit)
    if syndrome.shape != (indptr.size - 1,):
        raise ValueError("syndrome length must equal active row count")
    c2v = np.asarray(warm_start_c2v, dtype=np.float64).copy()
    if c2v.shape != (indices.size,):
        raise ValueError("warm_start_c2v shape must equal len(indices)")
    if int(max_sweeps) < 0:
        raise ValueError("max_sweeps must be nonnegative")

    edge_vars = indices.astype(np.int64, copy=False)
    state = base.rebuild_factor_state(prior, c2v, indptr, indices)
    btf = state["bit_to_factor"]
    f2b = state["factor_to_bit"]
    app_raw = state["app_raw"]
    pre_state = {
        "bit_to_factor": btf.copy(),
        "factor_to_bit": f2b.copy(),
        "app_raw": app_raw.copy(),
    }

    nrows = int(indptr.size - 1)
    # Cache row->symbols once per call (no per-row np.unique in sweeps).
    row_syms: list[np.ndarray] = [np.empty(0, dtype=np.int32)] * nrows
    for row in range(nrows):
        start, end = int(indptr[row]), int(indptr[row + 1])
        if end == start:
            row_syms[row] = np.empty(0, dtype=np.int32)
        else:
            row_syms[row] = np.unique((edge_vars[start:end] // 10).astype(np.int64)).astype(np.int32)

    btf_flat = btf.reshape(-1)  # persistent views, no per-row reshape alloc
    f2b_flat = f2b.reshape(-1)
    term = np.empty(1024, dtype=np.float64)
    max_deg = int(np.max(np.diff(indptr).astype(np.int64))) if nrows else 0
    v2c_buf = np.empty(max_deg, dtype=np.float64)
    new_buf = np.empty(max_deg, dtype=np.float64)
    old_buf = np.empty(max_deg, dtype=np.float64)

    residuals: list[float] = []
    edge_updates = 0
    local_targets = 0
    converged = False
    variable_to_check = np.zeros(indices.size, dtype=np.float64)

    for _sweep in range(min(int(max_sweeps), MAX_TOTAL_SWEEPS)):
        sweep_start = c2v.copy()
        for row in range(nrows):
            start, end = int(indptr[row]), int(indptr[row + 1])
            d = end - start
            if d == 0:
                continue
            old_buf[:d] = c2v[start:end]
            old_row = old_buf[:d]
            variables = edge_vars[start:end]  # view
            # v2c gather without per-row reshape objects.
            v2c = f2b_flat[variables] + btf_flat[variables] - old_row
            v2c_buf[:d] = v2c
            variable_to_check[start:end] = v2c_buf[:d]
            if HAS_NUMBA:
                _spa_row_numba(v2c_buf[:d], int(syndrome[row]), new_buf[:d])
                new_row = new_buf[:d]
            else:
                new_row = base._spa_row(v2c_buf[:d], int(syndrome[row]))
            c2v[start:end] = new_row
            delta = new_row - old_row
            # Vectorized b2f commit (same as per-edge loop; distinct vars).
            btf_flat[variables] += delta
            affected = row_syms[row]
            if affected.size:
                if HAS_NUMBA:
                    _factor_update_inplace_numba(prior, btf, f2b, affected, B_BITS, term)
                else:
                    updated = base._factor_batch(prior, btf, affected)
                    f2b[affected] = updated[affected]
                local_targets += 10 * int(affected.size)
            # No per-row app_raw rebuild (dead work); final app computed once.
        residual = float(np.max(np.abs(c2v - sweep_start))) if c2v.size else 0.0
        residuals.append(residual)
        edge_updates += int(c2v.size)
        if residual < CONVERGENCE_TOL:
            converged = True
            break

    # Single final app from converged state (identical to per-row rebuild's last value).
    app_raw = (f2b_flat + btf_flat).astype(np.float64, copy=True)
    if indices.size:
        sums = btf_flat[edge_vars]
        variable_to_check = f2b_flat[edge_vars] + sums - c2v
    app_clipped = np.clip(app_raw, -LLR_CLIP, LLR_CLIP)
    hard_bits, hard_symbols, syndrome_observed = base._hard_readout(app_clipped, indptr, indices)
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
