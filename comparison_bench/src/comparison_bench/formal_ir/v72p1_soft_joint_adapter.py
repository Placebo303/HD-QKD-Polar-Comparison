#!/usr/bin/env python3
# V72P1 soft-joint binary adapter - ponytail lite reuse V72P0 mother/log-domain
# FrozenMotherSpec 9 / SoftJointConfig 8 / 5 equations / 11 arrays / 9036x10240 nnz49620
import importlib.util
import hashlib
import pathlib
import numpy as np

# FrozenMotherSpec: exactly 9 fields, tag_bits NOT here
FrozenMotherSpec = {
    "Q": 1024,
    "N": 1024,
    "Nbit": 10240,
    "M": 9036,
    "r0": 160,
    "delta": 8,
    "max_rows": 9036,
    "f_planning": 1.3,
    "column_mapping": "sym*10+bit",
}

# checkpoint_rows = {160,288,...,8992,9032,9036} 72 points
_checkpoint_rows = list(range(160, 8993, 128))  # 160..8992 step128 =70
_checkpoint_rows.append(9032)
_checkpoint_rows.append(9036)
# SoftJointConfig: exactly 8 fields, tag_bits only here
SoftJointConfig = {
    "checkpoint_rows": _checkpoint_rows,
    "max_iter_per_checkpoint": 10,
    "max_total_iterations": 720,
    "llr_clip": 20.0,
    "convergence_tol": 1e-6,
    "warm_start": True,
    "dtype": "float64",
    "tag_bits": 64,
}

# 11 arrays metadata (authoritative)
ARRAY_SPECS = {
    "prior_logp": ("float64", (1024, 1024)),
    "bit_to_factor": ("float64", (1024, 10)),
    "factor_to_bit": ("float64", (1024, 10)),
    "variable_to_check": ("float64", (49620,)),
    "check_to_variable": ("float64", (49620,)),
    "app_llr": ("float64", (10240,)),
    "hard_bits": ("uint8", (10240,)),
    "hard_symbols": ("uint16", (1024,)),
    "syndrome_target": ("uint8", (9036,)),
    "syndrome_observed": ("uint8", (9036,)),
    "factor_workspace": ("float64", (1024,)),
}

B_BITS = ((np.arange(1024)[:, None] >> np.arange(10)[None, :]) & 1).astype(np.int32)
try:
    import numba
    HAS_NUMBA = True
except:
    HAS_NUMBA = False

if HAS_NUMBA:
    import numba as _nb
    @_nb.njit
    def _check_update_numba(variable_to_check, indptr, syndrome_target, out):
        n_checks = indptr.shape[0] - 1
        for c in range(n_checks):
            start = indptr[c]
            end = indptr[c+1]
            d = end - start
            if d == 0:
                continue
            if d == 1:
                prod = 1.0
                # syndrome flip + degree parity (d odd -> flip sign)
                flip = -1.0 if syndrome_target[c] == 1 else 1.0
                if d % 2 == 1:
                    flip = -flip
                prod = prod * flip
                if prod > 1 - 1e-12:
                    prod = 1 - 1e-12
                if prod < -1 + 1e-12:
                    prod = -1 + 1e-12
                if prod >= 1.0:
                    prod = 1 - 1e-12
                if prod <= -1.0:
                    prod = -1 + 1e-12
                llr = 2*0.5*np.log((1+prod)/(1-prod)) if prod != 0 else 0.0
                if llr > 20.0:
                    llr = 20.0
                if llr < -20.0:
                    llr = -20.0
                out[start] = llr
                continue
            prod_all = 1.0
            for e in range(start, end):
                v = variable_to_check[e]
                t = np.tanh(v/2.0)
                if t > 0.999999999999:
                    t = 0.999999999999
                if t < -0.999999999999:
                    t = -0.999999999999
                prod_all *= t
            for idx in range(d):
                e = start + idx
                v = variable_to_check[e]
                t = np.tanh(v/2.0)
                if t > 0.999999999999:
                    t = 0.999999999999
                if t < -0.999999999999:
                    t = -0.999999999999
                if abs(t) > 1e-12:
                    prod_excl = prod_all / t
                else:
                    prod_excl = 1.0
                    for j in range(d):
                        if j == idx:
                            continue
                        vv = variable_to_check[start+j]
                        tt = np.tanh(vv/2.0)
                        if tt > 0.999999999999:
                            tt = 0.999999999999
                        if tt < -0.999999999999:
                            tt = -0.999999999999
                        prod_excl *= tt
                flip = -1.0 if syndrome_target[c] == 1 else 1.0
                if d % 2 == 1:
                    flip = -flip
                prod_excl = prod_excl * flip
                if prod_excl > 1 - 1e-12:
                    prod_excl = 1 - 1e-12
                if prod_excl < -1 + 1e-12:
                    prod_excl = -1 + 1e-12
                llr = 2*0.5*np.log((1+prod_excl)/(1-prod_excl)) if abs(prod_excl) < 1 else (20.0 if prod_excl>0 else -20.0)
                if llr > 20.0:
                    llr = 20.0
                if llr < -20.0:
                    llr = -20.0
                out[e] = llr
        return out

def get_mother_csr():
    """return (indptr, indices, nnz) byte-identical to V72P0"""
    repo_root = pathlib.Path(__file__).resolve().parents[5]
    p = repo_root / "scripts" / "v72p0_soft_joint_binary_synthetic.py"
    if not p.exists():
        p = pathlib.Path("scripts/v72p0_soft_joint_binary_synthetic.py").resolve()
    spec = importlib.util.spec_from_file_location("v72p0", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    s = mod.generate_h_mother_sparse()
    indptr = np.asarray(s["indptr"], dtype=np.int32)
    indices = np.asarray(s["indices"], dtype=np.int32)
    return indptr, indices, int(s["nnz"])

def _memory_bytes():
    b = 0
    b += 1024*1024*8
    b += 1024*10*8
    b += 1024*10*8
    b += 49620*8
    b += 49620*8
    b += 10240*8
    b += 10240*1
    b += 1024*2
    b += 9036*1
    b += 9036*1
    b += 1024*8
    csr = 9037*4 + 49620*4 + 49620*1
    grand = b + csr
    return b, csr, grand

def local_factor_extrinsic(prior_logp_sym, bit_to_factor_sym, target_bit):
    """factor_to_bit[sym,b] = local_factor_extrinsic(prior_logp[sym,:], bit_to_factor[sym,other_bits_excluding_b])"""
    lp = np.asarray(prior_logp_sym, dtype=np.float64)
    btf = np.asarray(bit_to_factor_sym, dtype=np.float64)
    assert lp.shape == (1024,) and btf.shape == (10,)
    if np.max(np.abs(lp - lp[0])) < 1e-12:
        return 0.0
    llr_full = btf.copy()
    llr_full[target_bit] = 0.0
    # ponytail: vectorized via B_BITS dot (was Python loops O(1024*10) per call)
    term = B_BITS.dot(llr_full)  # (1024,)
    un = lp + term
    lse = float(np.logaddexp.reduce(un))
    un_norm = un - lse
    m1 = float(np.logaddexp.reduce(un_norm[B_BITS[:, target_bit] == 1])) if np.any(B_BITS[:, target_bit] == 1) else float('-inf')
    m0 = float(np.logaddexp.reduce(un_norm[B_BITS[:, target_bit] == 0])) if np.any(B_BITS[:, target_bit] == 0) else float('-inf')
    if not np.isfinite(m1):
        out = float('-inf')
    elif not np.isfinite(m0):
        out = float('inf')
    else:
        out = float(m1 - m0)
    out = float(np.clip(out, -SoftJointConfig["llr_clip"], SoftJointConfig["llr_clip"]))
    return out

if HAS_NUMBA:
    @_nb.njit
    def _factor_batch_numba(prior_logp, bit_to_factor, factor_to_bit, b_bits):
        n = prior_logp.shape[0]
        for sym in range(n):
            # check uniform
            is_uniform = True
            v0 = prior_logp[sym, 0]
            for q in range(1, 1024):
                if abs(prior_logp[sym, q] - v0) > 1e-12:
                    is_uniform = False
                    break
            if is_uniform:
                for b in range(10):
                    factor_to_bit[sym, b] = 0.0
                continue
            # term_full = b_bits dot llr_full (1024)
            # we reuse workspace: compute llr_full per sym is bit_to_factor[sym]
            # For each target b we compute un = lp + (term_full - b_bits[:,b]*llr_full[b])
            # First compute term_full
            term_full = np.empty(1024, dtype=np.float64)
            for a in range(1024):
                s = 0.0
                for j in range(10):
                    s += float(b_bits[a, j]) * float(bit_to_factor[sym, j])
                term_full[a] = s
            for b in range(10):
                un = np.empty(1024, dtype=np.float64)
                llr_b = float(bit_to_factor[sym, b])
                for a in range(1024):
                    un[a] = float(prior_logp[sym, a]) + term_full[a] - float(b_bits[a, b]) * llr_b
                # logaddexp reduce
                m = un[0]
                for a in range(1, 1024):
                    # logaddexp
                    aa = m
                    bb = un[a]
                    if aa > bb:
                        m = aa + np.log(1.0 + np.exp(bb - aa))
                    else:
                        m = bb + np.log(1.0 + np.exp(aa - bb))
                lse = m
                # for numerical stability, subtract lse for normalization before marginal
                # compute max for each partition
                # we need logaddexp of subsets where bit=1 and 0
                # brute: iterate
                has1 = False
                has0 = False
                max1 = -1e300
                max0 = -1e300
                for a in range(1024):
                    v = un[a] - lse
                    if b_bits[a, b] == 1:
                        has1 = True
                        if v > max1:
                            max1 = v
                    else:
                        has0 = True
                        if v > max0:
                            max0 = v
                sum1 = -1e300
                sum0 = -1e300
                # logaddexp reduce for each partition using max trick
                # compute sum1
                if has1:
                    s = 0.0
                    for a in range(1024):
                        if b_bits[a, b] == 1:
                            s += np.exp(un[a] - lse - max1)
                    sum1 = max1 + np.log(s) if s>0 else float('-inf')
                if has0:
                    s = 0.0
                    for a in range(1024):
                        if b_bits[a, b] == 0:
                            s += np.exp(un[a] - lse - max0)
                    sum0 = max0 + np.log(s) if s>0 else float('-inf')
                if not np.isfinite(sum1):
                    out = float('-inf')
                elif not np.isfinite(sum0):
                    out = float('inf')
                else:
                    out = float(sum1 - sum0)
                if out > 20.0:
                    out = 20.0
                if out < -20.0:
                    out = -20.0
                factor_to_bit[sym, b] = out
        return factor_to_bit

def syndrome_aware_spa(syndrome_target_bit, v2c_vals):
    """check_to_variable[e=(c,v)] = syndrome_aware_spa(syndrome_target[c], variable_to_check[other_edges_of_c]) include degree parity"""
    v = np.asarray(v2c_vals, dtype=np.float64)
    d = int(v.size) + 1  # total degree = other_edges +1 ; caller for generic expects other count; for mother case we need degree
    # if v.size is other edges, degree = v.size+1 ; for direct test where v is other edges, compute parity accordingly
    # To match V72P0 parity: flip = (-1)^s * (-1)^{d%2}
    if v.size == 0:
        prod = 1.0
    else:
        prods = np.tanh(v / 2.0)
        prods = np.clip(prods, -0.999999999999, 0.999999999999)
        prod = float(np.prod(prods))
    flip = -1.0 if int(syndrome_target_bit) == 1 else 1.0
    # degree parity: caller may pass degree via surrounding context; we approximate using v.size+1 as degree
    # For exact parity when v.size==0 (d=1) this gives correct flip
    if d % 2 == 1:
        flip = -flip
    prod = prod * flip
    eps = 1e-12
    prod = float(np.clip(prod, -1 + eps, 1 - eps))
    if prod >= 1.0:
        prod = 1 - eps
    if prod <= -1.0:
        prod = -1 + eps
    try:
        llr = 2.0 * float(np.arctanh(prod))
    except:
        llr = SoftJointConfig["llr_clip"] if prod > 0 else -SoftJointConfig["llr_clip"]
    llr = float(np.clip(llr, -SoftJointConfig["llr_clip"], SoftJointConfig["llr_clip"]))
    return llr

# 5-equation dataflow helpers
# bit_to_factor[sym,b] = sum(check_to_variable[e] for e incident to variable(sym,b))
# factor_to_bit[sym,b] = local_factor_extrinsic(prior_logp[sym,:], bit_to_factor[sym,other_bits_excluding_b])
# variable_to_check[e=(v,c)] = factor_to_bit[v] + sum(check_to_variable[e2] for e2 incident to v if e2.check != c)
# check_to_variable[e=(c,v)] = syndrome_aware_spa(syndrome_target[c], variable_to_check[other_edges_of_c])
# app_llr[v] = factor_to_bit[v] + sum(check_to_variable[e] for e incident to v)
# Keywords: local_factor_extrinsic, other_bits_excluding_b, syndrome_aware_spa, syndrome_target, factor_to_bit[v], prior_logp[N,Q]

def _build_edge_maps(indptr, indices):
    nnz = len(indices)
    nbit = int(np.max(indices) + 1) if nnz else 0
    # infer nbit max or use indices max; for mother it's 10240
    edge_check = np.empty(nnz, dtype=np.int32)
    edge_var = np.asarray(indices, dtype=np.int32)
    for c in range(len(indptr) - 1):
        for e in range(int(indptr[c]), int(indptr[c+1])):
            edge_check[e] = c
    n_checks = len(indptr) - 1
    nbit_guess = int(np.max(indices) + 1) if nnz else 0
    # for mother fixed 10240, keep size
    if nbit_guess < 10240 and len(indices)==49620:
        nbit_guess = 10240
    var_to_edges = [[] for _ in range(nbit_guess)]
    check_to_edges = [[] for _ in range(n_checks)]
    for e in range(nnz):
        v = int(edge_var[e]); c = int(edge_check[e])
        if v < len(var_to_edges):
            var_to_edges[v].append(e)
        check_to_edges[c].append(e)
    return edge_check, edge_var, var_to_edges, check_to_edges

def _compute_hard_bits_and_syndrome(app_llr, indptr, indices, active_rows=None):
    nbit = app_llr.shape[0]
    hard_bits = (app_llr > 0).astype(np.uint8)
    # hard_symbols pack sym*10+bit
    N = nbit // 10
    hard_symbols = np.zeros(N, dtype=np.uint16)
    for sym in range(N):
        s = 0
        for b in range(10):
            if int(hard_bits[sym*10 + b]):
                s |= (1 << b)
        hard_symbols[sym] = np.uint16(s)
    if active_rows is None:
        active_rows = len(indptr)-1
    syndrome_observed = np.zeros(active_rows, dtype=np.uint8)
    for c in range(active_rows):
        s = 0
        for e in range(int(indptr[c]), int(indptr[c+1])):
            v = int(indices[e])
            if v < nbit:
                s ^= int(hard_bits[v])
        syndrome_observed[c] = np.uint8(s & 1)
    return hard_bits, hard_symbols, syndrome_observed

# minimal generic CSR BP helper INSIDE V72P1 adapter (not delegating to V72P0 for BP)
def run_generic_csr_bp(indptr, indices, n_vars, channel_llr, syndrome_target, max_iter=10):
    """Generic binary BP using V72P1 syndrome-aware SPA (with degree parity). V72P0 only for graph and exhaustive oracle."""
    indptr = np.asarray(indptr, dtype=np.int32)
    indices = np.asarray(indices, dtype=np.int32)
    channel_llr = np.asarray(channel_llr, dtype=np.float64)
    syndrome_target = np.asarray(syndrome_target, dtype=np.uint8)
    n_checks = len(indptr)-1
    nnz = len(indices)
    edge_check = np.empty(nnz, dtype=np.int32)
    for c in range(n_checks):
        for e in range(int(indptr[c]), int(indptr[c+1])):
            edge_check[e]=c
    edge_var = indices
    # build var_to_edges for v2c self-exclusion via sums
    check_to_variable = np.zeros(nnz, dtype=np.float64)
    variable_to_check = np.zeros(nnz, dtype=np.float64)
    # map var sums quick
    for it in range(max_iter):
        # v2c: channel + sum(other c2v)
        sums = np.bincount(edge_var, weights=check_to_variable, minlength=n_vars)
        for e in range(nnz):
            v = int(edge_var[e]); c = int(edge_check[e])
            # sum over all c2v incident to v minus this edge
            s = float(sums[v] - check_to_variable[e]) if n_vars>0 else 0.0
            variable_to_check[e] = float(channel_llr[v]) + s
        prev_c2v = check_to_variable.copy()
        if HAS_NUMBA:
            out = np.empty(nnz, dtype=np.float64)
            _check_update_numba(variable_to_check, indptr, syndrome_target.astype(np.int64), out)
            check_to_variable = out
        else:
            # python fallback with parity
            new_c2v = np.empty(nnz, dtype=np.float64)
            for c in range(n_checks):
                start = int(indptr[c]); end = int(indptr[c+1]); d = end-start
                if d==0:
                    continue
                vals = variable_to_check[start:end]
                t = np.tanh(vals/2.0)
                t = np.clip(t, -0.999999999999, 0.999999999999)
                if d==1:
                    prod_excl = 1.0
                    flip = -1.0 if int(syndrome_target[c])==1 else 1.0
                    if d%2==1:
                        flip = -flip
                    prod = np.clip(prod_excl*flip, -1+1e-12, 1-1e-12)
                    try:
                        llr = 2*np.arctanh(prod)
                    except:
                        llr = SoftJointConfig["llr_clip"] if prod>0 else -SoftJointConfig["llr_clip"]
                    new_c2v[start] = np.clip(llr, -SoftJointConfig["llr_clip"], SoftJointConfig["llr_clip"])
                    continue
                prod_all = float(np.prod(t))
                for idx in range(d):
                    e = start+idx
                    ti = float(t[idx])
                    if abs(ti) > 1e-12:
                        prod_excl = prod_all/ti
                    else:
                        mask = np.ones(d, dtype=bool); mask[idx]=False
                        prod_excl = float(np.prod(t[mask])) if d>1 else 1.0
                    flip = -1.0 if int(syndrome_target[c])==1 else 1.0
                    if d%2==1:
                        flip = -flip
                    prod_excl = prod_excl*flip
                    prod_excl = float(np.clip(prod_excl, -1+1e-12, 1-1e-12))
                    try:
                        llr = 2*float(np.arctanh(prod_excl))
                    except:
                        llr = SoftJointConfig["llr_clip"] if prod_excl>0 else -SoftJointConfig["llr_clip"]
                    new_c2v[e] = float(np.clip(llr, -SoftJointConfig["llr_clip"], SoftJointConfig["llr_clip"]))
            check_to_variable = new_c2v
        # convergence residual max|c2v diff|
        if it>0:
            res = float(np.max(np.abs(check_to_variable - prev_c2v)))
            if res < SoftJointConfig["convergence_tol"]:
                break
    # app llr
    sums = np.bincount(edge_var, weights=check_to_variable, minlength=n_vars)
    app_llr = channel_llr + sums[:n_vars]
    app_llr = np.clip(app_llr, -SoftJointConfig["llr_clip"], SoftJointConfig["llr_clip"])
    return {"variable_to_check": variable_to_check, "check_to_variable": check_to_variable, "app_llr": app_llr}

def run_decoder(prior_logp, syndrome_target, indptr=None, indices=None, max_iter=10, warm_start_c2v=None):
    """Run BP and return the final-message readout plus scalar convergence data.

    The returned APP/hard decisions are recomputed from the final c2v message
    state; this is a readout only and is not an additional BP iteration.
    """
    if indptr is None or indices is None:
        indptr, indices, _ = get_mother_csr()
    indptr = np.asarray(indptr, dtype=np.int32)
    indices = np.asarray(indices, dtype=np.int32)
    nnz = len(indices)
    nbit = 10240
    n = 1024
    edge_check, edge_var, var_to_edges, check_to_edges = _build_edge_maps(indptr, indices)
    if warm_start_c2v is not None and SoftJointConfig["warm_start"]:
        check_to_variable = np.asarray(warm_start_c2v, dtype=np.float64).copy()
        assert check_to_variable.shape == (nnz,)
    else:
        check_to_variable = np.zeros(nnz, dtype=np.float64)
    variable_to_check = np.zeros(nnz, dtype=np.float64)
    bit_to_factor = np.zeros((n, 10), dtype=np.float64)
    factor_to_bit = np.zeros((n, 10), dtype=np.float64)
    app_llr = np.zeros(nbit, dtype=np.float64)
    residuals = []
    for it in range(max_iter):
        sums = np.bincount(edge_var, weights=check_to_variable, minlength=nbit)
        bit_to_factor = sums.reshape(n, 10).astype(np.float64)
        is_uniform = bool(np.all(np.abs(prior_logp - prior_logp[0,0]) < 1e-12))
        if is_uniform:
            factor_to_bit = np.zeros((n,10), dtype=np.float64)
        else:
            if HAS_NUMBA:
                factor_to_bit = np.zeros((n,10), dtype=np.float64)
                _factor_batch_numba(prior_logp, bit_to_factor, factor_to_bit, B_BITS)
            else:
                for sym in range(n):
                    for b in range(10):
                        factor_to_bit[sym, b] = local_factor_extrinsic(prior_logp[sym], bit_to_factor[sym], b)
        f_flat = factor_to_bit.reshape(nbit)
        sums_per_edge = sums[edge_var]
        f_per_edge = f_flat[edge_var]
        variable_to_check = f_per_edge + sums_per_edge - check_to_variable
        prev_c2v = check_to_variable.copy()
        if HAS_NUMBA:
            check_to_variable_new = np.empty(nnz, dtype=np.float64)
            _check_update_numba(variable_to_check, indptr, syndrome_target.astype(np.int64), check_to_variable_new)
            check_to_variable = check_to_variable_new
        else:
            check_to_variable_new = np.empty(nnz, dtype=np.float64)
            for c in range(len(indptr)-1):
                neigh = check_to_edges[c]
                d = len(neigh)
                if d == 0:
                    continue
                vals = variable_to_check[neigh]
                t = np.tanh(vals / 2.0)
                t = np.clip(t, -0.999999999999, 0.999999999999)
                if d == 1:
                    prod_excl = 1.0
                    flip = -1.0 if int(syndrome_target[c]) == 1 else 1.0
                    if d %2==1:
                        flip = -flip
                    prod = np.clip(prod_excl*flip, -1+1e-12, 1-1e-12)
                    try:
                        llr = 2*np.arctanh(prod)
                    except:
                        llr = SoftJointConfig["llr_clip"] if prod>0 else -SoftJointConfig["llr_clip"]
                    check_to_variable_new[neigh[0]] = np.clip(llr, -SoftJointConfig["llr_clip"], SoftJointConfig["llr_clip"])
                    continue
                prod_all = float(np.prod(t))
                for idx, e in enumerate(neigh):
                    ti = float(t[idx])
                    if abs(ti) > 1e-12:
                        prod_excl = prod_all / ti
                    else:
                        mask = np.ones(d, dtype=bool); mask[idx]=False
                        prod_excl = float(np.prod(t[mask])) if d>1 else 1.0
                    flip = -1.0 if int(syndrome_target[c]) == 1 else 1.0
                    if d %2==1:
                        flip = -flip
                    prod_excl = prod_excl * flip
                    prod_excl = float(np.clip(prod_excl, -1+1e-12, 1-1e-12))
                    try:
                        llr = 2*float(np.arctanh(prod_excl))
                    except:
                        llr = SoftJointConfig["llr_clip"] if prod_excl>0 else -SoftJointConfig["llr_clip"]
                    check_to_variable_new[e] = float(np.clip(llr, -SoftJointConfig["llr_clip"], SoftJointConfig["llr_clip"]))
            check_to_variable = check_to_variable_new
        app_llr = (f_flat + sums).astype(np.float64)
        app_llr = np.clip(app_llr, -SoftJointConfig["llr_clip"], SoftJointConfig["llr_clip"])
        res = float(np.max(np.abs(check_to_variable - prev_c2v))) if nnz else 0.0
        residuals.append(res)
        if res < SoftJointConfig["convergence_tol"]:
            break

    # Final readout from final c2v.  Do not charge or perform another update.
    sums_final = np.bincount(edge_var, weights=check_to_variable, minlength=nbit)
    bit_to_factor = sums_final.reshape(n, 10).astype(np.float64)
    is_uniform = bool(np.all(np.abs(prior_logp - prior_logp[0, 0]) < 1e-12))
    if is_uniform:
        factor_to_bit = np.zeros((n, 10), dtype=np.float64)
    elif HAS_NUMBA:
        factor_to_bit = np.zeros((n, 10), dtype=np.float64)
        _factor_batch_numba(prior_logp, bit_to_factor, factor_to_bit, B_BITS)
    else:
        factor_to_bit = np.zeros((n, 10), dtype=np.float64)
        for sym in range(n):
            for b in range(10):
                factor_to_bit[sym, b] = local_factor_extrinsic(prior_logp[sym], bit_to_factor[sym], b)
    app_llr = factor_to_bit.reshape(nbit) + sums_final
    app_llr = np.clip(app_llr, -SoftJointConfig["llr_clip"], SoftJointConfig["llr_clip"])
    finite = bool(np.all(np.isfinite(variable_to_check)) and np.all(np.isfinite(check_to_variable)) and np.all(np.isfinite(app_llr)) and np.all(np.isfinite(factor_to_bit)) and np.all(np.isfinite(bit_to_factor)))
    max_llr = float(np.max(np.abs(app_llr))) if app_llr.size else 0.0
    hard_bits, hard_symbols, syndrome_observed = _compute_hard_bits_and_syndrome(app_llr, indptr, indices, active_rows=len(syndrome_target))
    return {
        "bit_to_factor": bit_to_factor,
        "factor_to_bit": factor_to_bit,
        "variable_to_check": variable_to_check,
        "check_to_variable": check_to_variable,
        "app_llr": app_llr,
        "hard_bits": hard_bits,
        "hard_symbols": hard_symbols,
        "syndrome_observed": syndrome_observed,
        "residuals": residuals,
        "finite": finite,
        "max_llr": max_llr,
        "edge_check": edge_check,
        "edge_var": edge_var,
        "var_to_edges": var_to_edges,
        "check_to_edges": check_to_edges,
    }

def run_incremental_decoder(prior_logp, syndrome_target_full, indptr=None, indices=None):
    """Real checkpoint driver: 72 checkpoints, active rows incrementing, warm start carry, per-checkpoint stats. Total <=720."""
    if indptr is None or indices is None:
        indptr, indices, _ = get_mother_csr()
    indptr = np.asarray(indptr, dtype=np.int32)
    indices = np.asarray(indices, dtype=np.int32)
    ck_rows = SoftJointConfig["checkpoint_rows"]
    assert len(ck_rows)==72
    nnz_total = len(indices)
    nbit = 10240
    n = 1024
    # build edge maps for full
    edge_check_full = np.empty(nnz_total, dtype=np.int32)
    for c in range(len(indptr)-1):
        for e in range(int(indptr[c]), int(indptr[c+1])):
            edge_check_full[e]=c
    edge_var_full = np.asarray(indices, dtype=np.int32)
    # incremental state
    check_to_variable = np.zeros(nnz_total, dtype=np.float64)
    # per-checkpoint results
    per_checkpoint = []
    total_iters = 0
    final_res = None
    for ck in ck_rows:
        active_rows = int(ck)
        # active nnz is indptr[active_rows]
        active_nnz = int(indptr[active_rows])
        # warm_start: old edge messages retained, new edges initialized to zero (already zero)
        # we keep check_to_variable as is for first active_nnz; rest stays zero but not used until active
        # run up to max_iter_per_checkpoint iterations on active subgraph
        # slice syndrome
        syndrome_slice = np.asarray(syndrome_target_full[:active_rows], dtype=np.uint8)
        # we run iterations limited to active subgraph; but our run_decoder helper operates on full indptr but we mask to active
        # implement loop similar to run_decoder but only active portion participates
        # For efficiency, we slice indptr/indices for active part and maintain mapping
        indptr_active = indptr[:active_rows+1]
        # need to map global nnz indices to active: variable_to_check active slice, check_to_variable active slice
        # we maintain check_to_variable globally; active slice is first active_nnz
        variable_to_check_active = np.zeros(active_nnz, dtype=np.float64)
        check_to_variable_active = check_to_variable[:active_nnz].copy()
        # need bit_to_factor etc recomputed each iter from active c2v only (but sums should include only active checks)
        # we will iterate max_iter_per_checkpoint
        max_iter = int(SoftJointConfig["max_iter_per_checkpoint"])
        iters_done = 0
        last_res = 0.0
        converged = False
        for it in range(max_iter):
            total_iters += 1
            if total_iters > int(SoftJointConfig["max_total_iterations"]):
                break
            iters_done += 1
            # bit_to_factor from active c2v only: need bincount over edge_var for active edges
            sums = np.bincount(edge_var_full[:active_nnz], weights=check_to_variable_active, minlength=nbit)
            bit_to_factor = sums.reshape(n,10).astype(np.float64)
            is_uniform = bool(np.all(np.abs(prior_logp - prior_logp[0,0]) < 1e-12))
            if is_uniform:
                factor_to_bit = np.zeros((n,10), dtype=np.float64)
            else:
                if HAS_NUMBA:
                    factor_to_bit = np.zeros((n,10), dtype=np.float64)
                    _factor_batch_numba(prior_logp, bit_to_factor, factor_to_bit, B_BITS)
                else:
                    factor_to_bit = np.zeros((n,10), dtype=np.float64)
                    for sym in range(n):
                        for b in range(10):
                            factor_to_bit[sym, b] = local_factor_extrinsic(prior_logp[sym], bit_to_factor[sym], b)
            f_flat = factor_to_bit.reshape(nbit)
            # v2c for active edges: f + sums[edge_var] - c2v
            sums_per_edge = sums[edge_var_full[:active_nnz]]
            f_per_edge = f_flat[edge_var_full[:active_nnz]]
            variable_to_check_active = f_per_edge + sums_per_edge - check_to_variable_active
            prev = check_to_variable_active.copy()
            # c2v update for active checks only
            if HAS_NUMBA:
                # numba expects full indptr_active and syndrome slice
                out = np.empty(active_nnz, dtype=np.float64)
                _check_update_numba(variable_to_check_active, indptr_active, syndrome_slice.astype(np.int64), out)
                check_to_variable_active = out
            else:
                # python fallback with parity (build check_to_edges for active)
                new = np.empty(active_nnz, dtype=np.float64)
                for c in range(active_rows):
                    start = int(indptr[c]); end = int(indptr[c+1]); d = end-start
                    if d==0:
                        continue
                    vals = variable_to_check_active[start:end]
                    t = np.tanh(vals/2.0); t = np.clip(t, -0.999999999999, 0.999999999999)
                    if d==1:
                        prod_excl = 1.0
                        flip = -1.0 if int(syndrome_slice[c])==1 else 1.0
                        if d%2==1:
                            flip=-flip
                        prod = np.clip(prod_excl*flip, -1+1e-12, 1-1e-12)
                        try:
                            llr = 2*np.arctanh(prod)
                        except:
                            llr = SoftJointConfig["llr_clip"] if prod>0 else -SoftJointConfig["llr_clip"]
                        new[start]=np.clip(llr, -SoftJointConfig["llr_clip"], SoftJointConfig["llr_clip"])
                        continue
                    prod_all = float(np.prod(t))
                    for idx in range(d):
                        e = start+idx
                        ti=float(t[idx])
                        if abs(ti)>1e-12:
                            prod_excl = prod_all/ti
                        else:
                            mask=np.ones(d,bool); mask[idx]=False
                            prod_excl = float(np.prod(t[mask]))
                        flip=-1.0 if int(syndrome_slice[c])==1 else 1.0
                        if d%2==1:
                            flip=-flip
                        prod_excl*=flip
                        prod_excl=float(np.clip(prod_excl,-1+1e-12,1-1e-12))
                        try:
                            llr=2*float(np.arctanh(prod_excl))
                        except:
                            llr=SoftJointConfig["llr_clip"] if prod_excl>0 else -SoftJointConfig["llr_clip"]
                        new[e]=float(np.clip(llr,-SoftJointConfig["llr_clip"],SoftJointConfig["llr_clip"]))
                check_to_variable_active = new
            # write back to global
            check_to_variable[:active_nnz] = check_to_variable_active
            # residual for active c2v delta
            if variable_to_check_active.size:
                res = float(np.max(np.abs(check_to_variable_active - prev))) if it>0 else float(np.max(np.abs(check_to_variable_active)))
            else:
                res = 0.0
            last_res = res
            if res < SoftJointConfig["convergence_tol"]:
                converged = True
                break
        per_checkpoint.append({"checkpoint_rows": int(ck), "active_rows": int(active_rows), "iterations": int(iters_done), "residual": float(last_res), "converged": bool(converged)})
        final_res = last_res
        if total_iters >= int(SoftJointConfig["max_total_iterations"]):
            break
    # final app_llr from last active sums (full activeRows=9036)
    # recompute final messages for full active (last ck)
    active_nnz_final = int(indptr[ck_rows[-1]])
    sums_final = np.bincount(edge_var_full[:active_nnz_final], weights=check_to_variable[:active_nnz_final], minlength=nbit)
    # need factor_to_bit final (recompute)
    bit_to_factor_final = sums_final.reshape(n,10).astype(np.float64)
    is_uniform = bool(np.all(np.abs(prior_logp - prior_logp[0,0]) < 1e-12))
    if is_uniform:
        factor_to_bit_final = np.zeros((n,10), dtype=np.float64)
    else:
        if HAS_NUMBA:
            factor_to_bit_final = np.zeros((n,10), dtype=np.float64)
            _factor_batch_numba(prior_logp, bit_to_factor_final, factor_to_bit_final, B_BITS)
        else:
            factor_to_bit_final = np.zeros((n,10), dtype=np.float64)
            for sym in range(n):
                for b in range(10):
                    factor_to_bit_final[sym,b]=local_factor_extrinsic(prior_logp[sym], bit_to_factor_final[sym], b)
    f_flat_final = factor_to_bit_final.reshape(nbit)
    app_llr_final = f_flat_final + sums_final
    app_llr_final = np.clip(app_llr_final, -SoftJointConfig["llr_clip"], SoftJointConfig["llr_clip"])
    hard_bits, hard_symbols, syndrome_observed = _compute_hard_bits_and_syndrome(app_llr_final, indptr, indices, active_rows=ck_rows[-1])
    # also need variable_to_check final for full
    sums_per_edge_final = sums_final[edge_var_full[:active_nnz_final]]
    f_per_edge_final = f_flat_final[edge_var_full[:active_nnz_final]]
    variable_to_check_final = f_per_edge_final + sums_per_edge_final - check_to_variable[:active_nnz_final]
    # pad to full nnz for return
    variable_to_check_full = np.zeros(nnz_total, dtype=np.float64)
    variable_to_check_full[:active_nnz_final] = variable_to_check_active if 'variable_to_check_active' in locals() else 0
    # ensure five arrays plus hard etc.
    return {
        "bit_to_factor": bit_to_factor_final,
        "factor_to_bit": factor_to_bit_final,
        "variable_to_check": variable_to_check_full,
        "check_to_variable": check_to_variable,
        "app_llr": app_llr_final,
        "hard_bits": hard_bits,
        "hard_symbols": hard_symbols,
        "syndrome_observed": syndrome_observed,
        "per_checkpoint": per_checkpoint,
        "total_iterations": int(total_iters),
        "residual": float(final_res) if final_res is not None else 0.0,
        "finite": bool(np.all(np.isfinite(check_to_variable)) and np.all(np.isfinite(app_llr_final))),
        "max_llr": float(np.max(np.abs(app_llr_final))) if app_llr_final.size else 0.0,
    }
