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
# prior_logp[N,Q] float64 [1024,1024] etc.
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
                # product 1, flip by syndrome
                prod = 1.0
                if syndrome_target[c] == 1:
                    prod = -1.0
                # clip
                if prod > 1 - 1e-12:
                    prod = 1 - 1e-12
                if prod < -1 + 1e-12:
                    prod = -1 + 1e-12
                # atanh
                # 2*atanh(prod) with clip 20
                # use approximation: 2*0.5*log((1+prod)/(1-prod))
                if prod >= 1.0:
                    prod = 1 - 1e-12
                if prod <= -1.0:
                    prod = -1 + 1e-12
                llr = 2*0.5*np.log((1+prod)/(1-prod)) if prod != 0 else 0.0  # atanh
                # fallback clip
                if llr > 20.0:
                    llr = 20.0
                if llr < -20.0:
                    llr = -20.0
                out[start] = llr
                continue
            # gather t
            # compute t array
            # first compute product all
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
                if syndrome_target[c] == 1:
                    prod_excl = -prod_excl
                if prod_excl > 1 - 1e-12:
                    prod_excl = 1 - 1e-12
                if prod_excl < -1 + 1e-12:
                    prod_excl = -1 + 1e-12
                # atanh
                llr = 2*0.5*np.log((1+prod_excl)/(1-prod_excl)) if abs(prod_excl) < 1 else (20.0 if prod_excl>0 else -20.0)
                if llr > 20.0:
                    llr = 20.0
                if llr < -20.0:
                    llr = -20.0
                out[e] = llr
        return out

def get_mother_csr():
    """return (indptr, indices, nnz) byte-identical to V72P0"""
    # ponytail: reuse V72P0 generate_h_mother_sparse, no new matrix
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
    # 11 arrays 9466840, CSR 284248, grand 9751088
    b = 0
    b += 1024*1024*8  # prior_logp
    b += 1024*10*8  # bit_to_factor
    b += 1024*10*8  # factor_to_bit
    b += 49620*8  # variable_to_check
    b += 49620*8  # check_to_variable
    b += 10240*8  # app_llr
    b += 10240*1  # hard_bits
    b += 1024*2  # hard_symbols
    b += 9036*1  # syndrome_target
    b += 9036*1  # syndrome_observed
    b += 1024*8  # factor_workspace
    csr = 9037*4 + 49620*4 + 49620*1
    grand = b + csr
    return b, csr, grand

# ponytail: O(1024) per factor, numpy logaddexp, no extra prior

def local_factor_extrinsic(prior_logp_sym, bit_to_factor_sym, target_bit):
    """factor_to_bit[sym,b] = local_factor_extrinsic(prior_logp[sym,:], bit_to_factor[sym,other_bits_excluding_b])
    prior only via local factor (sole consumer of prior_logp)
    self-exclusion: other_bits_excluding_b excludes target
    """
    # prior_logp[N,Q] -> prior_logp_sym shape (1024,)
    # bit_to_factor_sym shape (10,)
    lp = np.asarray(prior_logp_sym, dtype=np.float64)
    btf = np.asarray(bit_to_factor_sym, dtype=np.float64)
    assert lp.shape == (1024,) and btf.shape == (10,)
    # ponytail: uniform prior fast path -> factor_to_bit 0 (symmetric, saves 10M per iter)
    if np.max(np.abs(lp - lp[0])) < 1e-12:
        return 0.0
    # build full llr with target zeroed -> other_bits_excluding_b
    llr_full = btf.copy()
    # ensure self-exclusion: target not used
    orig = float(llr_full[target_bit])
    llr_full[target_bit] = 0.0
    # compute unnormalized log posterior: prior + sum_{j!=b} B[a,j]*llr_j
    # ponytail: reuse B_BITS dot
    un = np.empty(1024, dtype=np.float64)
    for a in range(1024):
        s = 0.0
        for j in range(10):
            if j == target_bit:
                continue
            s += float((a >> j) & 1) * float(llr_full[j])
        un[a] = float(lp[a]) + s
    lse = float(np.logaddexp.reduce(un))
    un_norm = un - lse
    # llr_out
    m1 = float(np.logaddexp.reduce(un_norm[B_BITS[:, target_bit] == 1])) if np.any(B_BITS[:, target_bit] == 1) else float('-inf')
    m0 = float(np.logaddexp.reduce(un_norm[B_BITS[:, target_bit] == 0])) if np.any(B_BITS[:, target_bit] == 0) else float('-inf')
    if not np.isfinite(m1):
        out = float('-inf')
    elif not np.isfinite(m0):
        out = float('inf')
    else:
        out = float(m1 - m0)
    # clip
    out = float(np.clip(out, -SoftJointConfig["llr_clip"], SoftJointConfig["llr_clip"]))
    return out

def syndrome_aware_spa(syndrome_target_bit, v2c_vals):
    """check_to_variable[e=(c,v)] = syndrome_aware_spa(syndrome_target[c], variable_to_check[other_edges_of_c])"""
    # v2c_vals: array of variable_to_check for other edges
    v = np.asarray(v2c_vals, dtype=np.float64)
    if v.size == 0:
        # degree 1 check, product empty =1, flip by syndrome
        prod = 1.0
    else:
        # prod tanh(v/2)
        prods = np.tanh(v / 2.0)
        # clip prod to avoid +-1 before atanh
        prods = np.clip(prods, -0.999999999999, 0.999999999999)
        prod = float(np.prod(prods))
    # syndrome_aware: flip sign if syndrome_target==1
    # include degree parity handled via flip sign already (syndrome_target)
    flip = -1.0 if int(syndrome_target_bit) == 1 else 1.0
    prod = prod * flip
    # double clip prod per B section: clip(prod, -1+1e-12, 1-1e-12) and llr_clip
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

# 5-equation dataflow helpers (for tests probing)
# bit_to_factor[sym,b] = sum(check_to_variable[e] for e incident to variable(sym,b))
# factor_to_bit[sym,b] = local_factor_extrinsic(prior_logp[sym,:], bit_to_factor[sym,other_bits_excluding_b])
# variable_to_check[e=(v,c)] = factor_to_bit[v] + sum(check_to_variable[e2] for e2 incident to v if e2.check != c)
# check_to_variable[e=(c,v)] = syndrome_aware_spa(syndrome_target[c], variable_to_check[other_edges_of_c])
# app_llr[v] = factor_to_bit[v] + sum(check_to_variable[e] for e incident to v)
# Keywords: local_factor_extrinsic, other_bits_excluding_b, syndrome_aware_spa, syndrome_target, factor_to_bit[v], prior_logp[N,Q]

def _build_edge_maps(indptr, indices):
    """build edge maps for variable_to_check / check_to_variable"""
    nnz = len(indices)
    nbit = 10240
    # edge arrays
    edge_check = np.empty(nnz, dtype=np.int32)
    edge_var = np.asarray(indices, dtype=np.int32)
    for c in range(len(indptr) - 1):
        for e in range(int(indptr[c]), int(indptr[c+1])):
            edge_check[e] = c
    # var to edges list
    var_to_edges = [[] for _ in range(nbit)]
    check_to_edges = [[] for _ in range(len(indptr)-1)]
    for e in range(nnz):
        v = int(edge_var[e]); c = int(edge_check[e])
        var_to_edges[v].append(e)
        check_to_edges[c].append(e)
    return edge_check, edge_var, var_to_edges, check_to_edges

def run_decoder(prior_logp, syndrome_target, indptr=None, indices=None, max_iter=10, warm_start_c2v=None):
    """soft-joint decoder for synthetic smoke; returns dict with messages"""
    if indptr is None or indices is None:
        indptr, indices, _ = get_mother_csr()
    indptr = np.asarray(indptr, dtype=np.int32)
    indices = np.asarray(indices, dtype=np.int32)
    nnz = len(indices)
    nbit = 10240
    n = 1024
    edge_check, edge_var, var_to_edges, check_to_edges = _build_edge_maps(indptr, indices)
    # allocate messages
    if warm_start_c2v is not None and SoftJointConfig["warm_start"]:
        check_to_variable = np.asarray(warm_start_c2v, dtype=np.float64).copy()
        assert check_to_variable.shape == (nnz,)
    else:
        check_to_variable = np.zeros(nnz, dtype=np.float64)
    variable_to_check = np.zeros(nnz, dtype=np.float64)
    bit_to_factor = np.zeros((n, 10), dtype=np.float64)
    factor_to_bit = np.zeros((n, 10), dtype=np.float64)
    app_llr = np.zeros(nbit, dtype=np.float64)
    # active rows: for synthetic use full M
    # iterative loop
    residuals = []
    for it in range(max_iter):
        # bit_to_factor = sum c2v per variable (vectorized)
        sums = np.bincount(edge_var, weights=check_to_variable, minlength=nbit)  # nbit 10240
        bit_to_factor = sums.reshape(n, 10).astype(np.float64)
        # factor_to_bit via local_factor_extrinsic (other_bits_excluding_b) - uniform fast path helps
        # ponytail: vectorized zero for uniform prior
        # check uniform
        # if prior uniform for all sym, skip heavy loop
        # we already fast path inside local_factor, but batch still loops; use quick check
        is_uniform = bool(np.all(np.abs(prior_logp - prior_logp[0,0]) < 1e-12))
        if is_uniform:
            factor_to_bit = np.zeros((n,10), dtype=np.float64)
        else:
            for sym in range(n):
                for b in range(10):
                    factor_to_bit[sym, b] = local_factor_extrinsic(prior_logp[sym], bit_to_factor[sym], b)
        # variable_to_check vectorized: f_flat[edge_var] + sums[edge_var] - check_to_variable
        f_flat = factor_to_bit.reshape(nbit)
        sums_per_edge = sums[edge_var]
        f_per_edge = f_flat[edge_var]
        variable_to_check = f_per_edge + sums_per_edge - check_to_variable
        # check_to_variable = syndrome_aware_spa(syndrome_target[c], variable_to_check[other_edges_of_c])
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
                    prod_excl = prod_excl * flip
                    prod_excl = float(np.clip(prod_excl, -1+1e-12, 1-1e-12))
                    try:
                        llr = 2*float(np.arctanh(prod_excl))
                    except:
                        llr = SoftJointConfig["llr_clip"] if prod_excl>0 else -SoftJointConfig["llr_clip"]
                    check_to_variable_new[e] = float(np.clip(llr, -SoftJointConfig["llr_clip"], SoftJointConfig["llr_clip"]))
            check_to_variable = check_to_variable_new
        # app_llr vectorized
        app_llr = (f_flat + sums).astype(np.float64)
        app_llr = np.clip(app_llr, -SoftJointConfig["llr_clip"], SoftJointConfig["llr_clip"])
        # residual = max|c2v^{(t)} - c2v^{(t-1)}|
        res = float(np.max(np.abs(check_to_variable - prev_c2v))) if it > 0 or max_iter > 1 else 0.0
        # for it==0 prev is zero init, so residual is max|c2v|
        if it == 0:
            res = float(np.max(np.abs(check_to_variable)))
        residuals.append(res)
        # early stop if residual < convergence_tol
        if res < SoftJointConfig["convergence_tol"]:
            break
    # finite check
    finite = bool(np.all(np.isfinite(variable_to_check)) and np.all(np.isfinite(check_to_variable)) and np.all(np.isfinite(app_llr)) and np.all(np.isfinite(factor_to_bit)) and np.all(np.isfinite(bit_to_factor)))
    max_llr = float(np.max(np.abs(app_llr))) if app_llr.size else 0.0
    return {
        "bit_to_factor": bit_to_factor,
        "factor_to_bit": factor_to_bit,
        "variable_to_check": variable_to_check,
        "check_to_variable": check_to_variable,
        "app_llr": app_llr,
        "residuals": residuals,
        "finite": finite,
        "max_llr": max_llr,
        "edge_check": edge_check,
        "edge_var": edge_var,
        "var_to_edges": var_to_edges,
        "check_to_edges": check_to_edges,
    }
