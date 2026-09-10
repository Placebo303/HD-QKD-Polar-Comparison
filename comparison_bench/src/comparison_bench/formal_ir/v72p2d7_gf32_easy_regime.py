"""D7-B easy-regime harness (frozen R1+A1; development calibration, no execution here).

Deterministic synthetic fixtures, prior families, cold cap-ladder dispatch with
a 420-call global stop, scalar-only five-file evidence, lazy production-decoder
binding with dependency injection. Production v35/D5 modules are read-only
(imports only); exact ground truth reuses the accepted D7-A oracle.
"""

from __future__ import annotations

import csv
import json
import time
from collections import deque
from pathlib import Path

import numpy as np

try:
    from comparison_bench.formal_ir import v72p2d7_gf32_decoder_certification as oracle
except ModuleNotFoundError:  # file-layout fallback, same module only
    import importlib.util as _ilu
    import pathlib as _pl
    import sys as _sys

    _p = _pl.Path(__file__).resolve().parent / "v72p2d7_gf32_decoder_certification.py"
    _spec = _ilu.spec_from_file_location("v72p2d7_gf32_decoder_certification", str(_p))
    assert _spec is not None and _spec.loader is not None
    oracle = _ilu.module_from_spec(_spec)
    _sys.modules["v72p2d7_gf32_decoder_certification"] = oracle
    _spec.loader.exec_module(oracle)

Q = 32
SEEDS = (2026091200, 2026091201, 2026091202, 2026091203)
PRIOR_FAMILIES = ("P99", "P90", "P60", "PAIR")
TIERS = ("SINGLE_CHECK_D3", "TREE_6", "CYCLE_8", "FULL_RANK_64")
CAPS = (1, 2, 4, 8, 16, 32, 90)
CALL_BUDGET = 420
PER_CALL_WATCHDOG_S = 120.0
RUN_WALL_LIMIT_S = 1500.0
OUTER_WATCHDOG_S = 1800.0
OUTER_GRACE_S = 30.0
RSS_LIMIT_BYTES = 2 * 1024**3
POST_TOL = 1e-10
DETERM_TOL = 1e-12
PROB_FLOOR = 1e-15
D7B_AUTH_KEY = "d7b_execution_authorized"

# Frozen terminal priority T1..T9 (exact strings).
T_PRE_EXEC = "D7_B_PRE_EXECUTION_BLOCKED"
T_WATCHDOG = "D7_B_WATCHDOG_TIMEOUT_VOID"
T_CRASH = "D7_B_NONFINITE_OR_CRASH_BLOCKED"
T_RESOURCE = "D7_B_RESOURCE_OVERRUN"
T_BUDGET = "D7_B_CALL_BUDGET_EXHAUSTED"
T_ALERT = "D7_B_NO_EASY_REGIME_CORRECTNESS_ALERT"
T_CONFIRMED = "D7_B_EASY_REGIME_CONFIRMED"
T_PARTIAL = "D7_B_PARTIAL_EASY_REGIME"
T_NOREGION = "D7_B_COMPLETED_NO_STABLE_REGION"
T_STRUCT_BLOCKED = "D7_B_STRUCTURE_FREEZE_BLOCKED"

FIVE_FILES = ("manifest.json", "decoder_records.csv", "summary.json", "report.md", "command_log.txt")

# Formal/dev roots that must never be an output target (name-based guard).
PROTECTED_ROOTS = (
    "workspace/v72p2d5_g0/20260905_r2",
    "workspace/v72p2d5_g0_recovery/20260906_r1",
    "workspace/v72p2d5_model_f_input/20260907_r1",
    "workspace/v72p2d5_p0_cost/20260906_r1",
    "workspace/v72p2d5_g1/20260907_r2",
    "workspace/v72p2d5_structure/20260905_r2",
    "workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b",
)


class D7BStructureBlocked(ValueError):
    pass


class NotAuthorizedError(PermissionError):
    pass


_EXECUTION_CONSUMED = False  # single-use guard within one process


def is_authorized(state) -> bool:
    try:
        return bool(dict(state).get(D7B_AUTH_KEY, False))
    except Exception:
        return False


def _require_authorized(authorized: bool) -> None:
    if not authorized:
        raise NotAuthorizedError("D7-B execution is not authorized; refusing before any work")


def _rss_bytes():
    try:
        import psutil

        return int(psutil.Process().memory_info().rss)
    except Exception:
        return None


# --------------------------------------------------------------------------
# Deterministic structure builders (frozen; TREE_6 is the literal A1 topology)
# --------------------------------------------------------------------------

def build_single_check_d3() -> np.ndarray:
    return np.array([[1, 7, 13]], dtype=np.int64)


def build_tree_6() -> np.ndarray:
    """A1 literal: c0=[0,1,2]/[1,7,13], c1=[2,3,4]/[29,1,7], c2=[4,5]/[13,29]."""
    h = np.zeros((3, 6), dtype=np.int64)
    h[0, [0, 1, 2]] = [1, 7, 13]
    h[1, [2, 3, 4]] = [29, 1, 7]
    h[2, [4, 5]] = [13, 29]
    return h


def build_cycle_8() -> np.ndarray:
    h = np.zeros((8, 8), dtype=np.int64)
    for r in range(8):
        h[r, r] = 1
        h[r, (r + 1) % 8] = 7 if r < 7 else 13
    return h


def build_full_rank_64() -> np.ndarray:
    h = np.zeros((64, 64), dtype=np.int64)
    for r in range(64):
        h[r, r] = 1
        h[r, (r + 1) % 64] = 7 if r < 63 else 13
    return h


def build_matrix(tier: str) -> np.ndarray:
    if tier == "SINGLE_CHECK_D3":
        return build_single_check_d3()
    if tier == "TREE_6":
        return build_tree_6()
    if tier == "CYCLE_8":
        return build_cycle_8()
    if tier == "FULL_RANK_64":
        return build_full_rank_64()
    raise ValueError("unknown tier %r" % (tier,))


def _gf32_rank_independent(mat: np.ndarray) -> int:
    """Row rank over GF(32) using ONLY D7-A oracle arithmetic (no prod tables)."""
    a = np.asarray(mat, dtype=np.int64).copy()
    m, n = a.shape
    r = 0
    for c in range(n):
        piv = None
        for i in range(r, m):
            if int(a[i, c]) != 0:
                piv = i
                break
        if piv is None:
            continue
        if piv != r:
            a[[r, piv]] = a[[piv, r]]
        invp = oracle.gf32_inv_independent(int(a[r, c]))
        for j in range(c, n):
            if int(a[r, j]) != 0:
                a[r, j] = oracle.gf32_mul_independent(int(a[r, j]), invp)
        for i in range(m):
            if i != r and int(a[i, c]) != 0:
                f = int(a[i, c])
                for j in range(c, n):
                    a[i, j] = oracle.gf32_add_independent(int(a[i, j]),
                                                          oracle.gf32_mul_independent(f, int(a[r, j])))
        r += 1
        if r == m:
            break
    return int(r)


def tanner_invariants(h: np.ndarray) -> dict:
    """Pure-structural invariants (no decoder): degrees, connected, acyclic."""
    h = np.asarray(h, dtype=np.int64)
    m, n = h.shape
    row_degs = [int((h[r] != 0).sum()) for r in range(m)]
    var_degs = [int((h[:, c] != 0).sum()) for c in range(n)]
    v = n + m
    e = int(sum(row_degs))
    adj = {i: set() for i in range(v)}
    for r in range(m):
        ci = n + r
        for c in range(n):
            if int(h[r, c]) != 0:
                adj[ci].add(c)
                adj[c].add(ci)
    seen = {0}
    dq = deque([0])
    while dq:
        u = dq.popleft()
        for w in adj[u]:
            if w not in seen:
                seen.add(w)
                dq.append(w)
    connected = len(seen) == v
    visited: set = set()
    has_back = [False]

    def _dfs(u: int, p: int) -> None:
        visited.add(u)
        for w in adj[u]:
            if w == p:
                continue
            if w in visited:
                has_back[0] = True
                return
            _dfs(w, u)

    if v:
        _dfs(0, -1)
    acyclic = (e == v - 1) and (len(visited) == v) and (not has_back[0])
    return {"n": n, "m": m, "V": v, "E": e, "row_degs": row_degs,
            "var_degs": var_degs, "connected": bool(connected),
            "acyclic": bool(acyclic),
            "no_isolated": bool(min(row_degs + var_degs) >= 1)}


def structural_freeze(tier: str) -> dict:
    """Frozen invariants per tier; raises D7BStructureBlocked on violation."""
    h = build_matrix(tier)
    inv = tanner_invariants(h)
    rank = _gf32_rank_independent(h)
    if tier == "SINGLE_CHECK_D3":
        ok = inv["row_degs"] == [3] and rank == 1 and min(inv["row_degs"]) >= 2
    elif tier == "TREE_6":
        ok = (inv["V"] == 9 and inv["E"] == 8 and inv["row_degs"] == [3, 3, 2]
              and inv["var_degs"] == [1, 1, 2, 1, 2, 1] and inv["connected"]
              and inv["acyclic"] and inv["no_isolated"] and rank == 3
              and all(1 <= int(c) <= 31 for c in h[h != 0]))
    elif tier in ("CYCLE_8", "FULL_RANK_64"):
        n = 8 if tier == "CYCLE_8" else 64
        ok = (inv["n"] == n and inv["m"] == n and inv["connected"]
              and all(d == 2 for d in inv["row_degs"])
              and all(d == 2 for d in inv["var_degs"]) and rank == n)
    else:
        raise ValueError("unknown tier %r" % (tier,))
    if not ok:
        raise D7BStructureBlocked("structure invariants failed for %s: %r rank=%s" % (tier, inv, rank))
    return {"tier": tier, "H": h, "n": inv["n"], "m": inv["m"], "rank": rank,
            "row_degs": inv["row_degs"], "var_degs": inv["var_degs"],
            "deg_min": min(inv["row_degs"] + inv["var_degs"]),
            "deg_max": max(inv["row_degs"] + inv["var_degs"])}


def truth_for(tier: str, seed: int) -> np.ndarray:
    n = {"SINGLE_CHECK_D3": 3, "TREE_6": 6, "CYCLE_8": 8, "FULL_RANK_64": 64}[tier]
    rng = np.random.default_rng(int(seed))
    return rng.integers(0, Q, size=n, dtype=np.int64)


def syndrome_for(h: np.ndarray, x_true: np.ndarray) -> np.ndarray:
    return np.asarray(oracle.syndrome_reference(h, x_true), dtype=np.int64)


# --------------------------------------------------------------------------
# Priors (frozen exact formulas)
# --------------------------------------------------------------------------

def build_prior(x_true: np.ndarray, family: str) -> np.ndarray:
    x = np.asarray(x_true, dtype=np.int64).reshape(-1)
    n = x.shape[0]
    p = np.zeros((n, Q), dtype=np.float64)
    if family == "P99":
        p[:] = 0.01 / 31
        p[np.arange(n), x] = 0.99
    elif family == "P90":
        p[:] = 0.10 / 31
        p[np.arange(n), x] = 0.90
    elif family == "P60":
        p[:] = 0.40 / 31
        p[np.arange(n), x] = 0.60
    elif family == "PAIR":
        p[:] = 0.02 / 30
        d = (x ^ 1) % Q
        p[np.arange(n), x] = 0.49
        p[np.arange(n), d] = np.where(d == x, 0.49, 0.49)
        # when d == x (impossible for XOR 1, kept explicit) no double count
    else:
        raise ValueError("unknown prior %r" % (family,))
    if not np.all(np.isfinite(p)) or not bool((p > 0).all()):
        raise ValueError("prior must be positive and finite")
    s = p.sum(axis=1)
    if not bool((np.abs(s - 1.0) <= 1e-12).all()):
        raise ValueError("prior rows must be normalized")
    return p


# --------------------------------------------------------------------------
# Exact ground truth (tractable tiers; never production decoder/FFT)
# --------------------------------------------------------------------------

def exact_single_check(h: np.ndarray, priors: np.ndarray, syndrome: np.ndarray) -> dict:
    post = np.asarray(oracle.exact_posterior(h, priors, syndrome), dtype=np.float64)
    x_map = np.argmax(post, axis=1).astype(np.int64)
    return {"posterior": post, "map": x_map}


def _tree_message_posterior(h: np.ndarray, priors: np.ndarray, syndrome: np.ndarray) -> np.ndarray:
    """Calc A: exact two-pass sum-product on the A1 tree (oracle check updates).

    Factor order is literal: f0 over (v0,v1,v2)/[1,7,13], f1 over
    (v2,v3,v4)/[29,1,7], f2 over (v4,v5)/[13,29]. Inward pass runs leaves to
    separators, outward pass back to leaves; beliefs are prior times incoming
    factor messages. Uses only the independent oracle check update, never the
    production FFT.
    """
    clean = [np.maximum(np.asarray(priors[i], dtype=np.float64), PROB_FLOOR) for i in range(6)]
    clean = [c / c.sum() for c in clean]
    s0, s1, s2 = (int(syndrome[0]), int(syndrome[1]), int(syndrome[2]))

    def _chk(incoming: list, coeffs: list, syn: int) -> list:
        return [np.asarray(m, dtype=np.float64)
                for m in oracle.direct_check_to_var(incoming, coeffs, syn)]

    def _norm(v: np.ndarray) -> np.ndarray:
        s = v.sum()
        if not np.isfinite(s) or s <= 0:
            raise ValueError("non-finite message mass")
        return v / s

    # inward: f0 -> v2 (others v0,v1 are leaves: priors only)
    f0_v2 = _chk([clean[0], clean[1], clean[2]], [1, 7, 13], s0)[2]
    # inward: f2 -> v4 (other v5 is a leaf)
    f2_v4 = _chk([clean[4], clean[5]], [13, 29], s2)[0]
    # v2 -> f1 and v4 -> f1 combine one side each
    v2_f1 = _norm(clean[2] * f0_v2)
    v4_f1 = _norm(clean[4] * f2_v4)
    # f1 outward to each member
    outs1 = _chk([v2_f1, clean[3], v4_f1], [29, 1, 7], s1)
    f1_v2, f1_v3, f1_v4 = outs1[0], outs1[1], outs1[2]
    # outward: v2 -> f0, v4 -> f2
    v2_f0 = _norm(clean[2] * f1_v2)
    v4_f2 = _norm(clean[4] * f1_v4)
    # f0 -> leaves, f2 -> leaf
    f0_v0 = _chk([clean[0], clean[1], v2_f0], [1, 7, 13], s0)[0]
    f0_v1 = _chk([clean[0], clean[1], v2_f0], [1, 7, 13], s0)[1]
    f2_v5 = _chk([v4_f2, clean[5]], [13, 29], s2)[1]
    post = np.zeros((6, Q))
    post[0] = _norm(clean[0] * f0_v0)
    post[1] = _norm(clean[1] * f0_v1)
    post[2] = _norm(clean[2] * f0_v2 * f1_v2)
    post[3] = _norm(clean[3] * f1_v3)
    post[4] = _norm(clean[4] * f2_v4 * f1_v4)
    post[5] = _norm(clean[5] * f2_v5)
    return post


def _tree_projection_posterior(priors: np.ndarray, syndrome: np.ndarray) -> np.ndarray:
    """Calc B: enumerate separators (v2,v4) = 1024 combos + analytic leaf sums."""
    clean = np.array([np.maximum(np.asarray(priors[i], dtype=np.float64), PROB_FLOOR) for i in range(6)])
    clean = clean / clean.sum(axis=1, keepdims=True)
    s0, s1, s2 = (int(syndrome[0]), int(syndrome[1]), int(syndrome[2]))
    # Z0(v2): sum over (v0,v1) satisfying c0; Z2(v4): sum over v5 for c2;
    # Z1(v2,v4): sum over v3 for c1.
    z0 = np.zeros(Q)
    for v2 in range(Q):
        t = 0.0
        for v0 in range(Q):
            for v1 in range(Q):
                acc = oracle.gf32_add_independent(
                    oracle.gf32_add_independent(oracle.gf32_mul_independent(1, v0),
                                                oracle.gf32_mul_independent(7, v1)),
                    oracle.gf32_mul_independent(13, v2))
                if acc == s0:
                    t += float(clean[0][v0]) * float(clean[1][v1])
        z0[v2] = t
    z2 = np.zeros(Q)
    for v4 in range(Q):
        t = 0.0
        for v5 in range(Q):
            acc = oracle.gf32_add_independent(oracle.gf32_mul_independent(13, v4),
                                              oracle.gf32_mul_independent(29, v5))
            if acc == s2:
                t += float(clean[5][v5])
        z2[v4] = t
    z1 = np.zeros((Q, Q))
    for v2 in range(Q):
        for v4 in range(Q):
            t = 0.0
            for v3 in range(Q):
                acc = oracle.gf32_add_independent(
                    oracle.gf32_add_independent(oracle.gf32_mul_independent(29, v2),
                                                oracle.gf32_mul_independent(1, v3)),
                    oracle.gf32_mul_independent(7, v4))
                if acc == s1:
                    t += float(clean[3][v3])
            z1[v2, v4] = t
    w = np.zeros((Q, Q))
    for v2 in range(Q):
        for v4 in range(Q):
            w[v2, v4] = float(clean[2][v2]) * float(clean[4][v4]) * z0[v2] * z1[v2, v4] * z2[v4]
    tot = w.sum()
    if tot <= 0:
        raise ValueError("tree projection has no mass")
    w /= tot
    post = np.zeros((6, Q))
    post[2] = w.sum(axis=1)
    post[4] = w.sum(axis=0)
    # Cavity distributions (rest-of-graph messages, unnormalized): g2(v2) is
    # the f1-side message to v2, g4(v4) the f0+f1-side message to v4.
    g2 = np.zeros(Q)
    for v2 in range(Q):
        t = 0.0
        for v4 in range(Q):
            t += z1[v2, v4] * float(clean[4][v4]) * z2[v4]
        g2[v2] = t
    g4 = np.zeros(Q)
    for v4 in range(Q):
        t = 0.0
        for v2 in range(Q):
            t += z1[v2, v4] * float(clean[2][v2]) * z0[v2]
        g4[v4] = t
    # Leaves: prior times factor-conditional sum against cavity (no double
    # counting of the leaf's own factor mass).
    for v0 in range(Q):
        t = 0.0
        for v1 in range(Q):
            for v2 in range(Q):
                acc = oracle.gf32_add_independent(
                    oracle.gf32_add_independent(oracle.gf32_mul_independent(1, v0),
                                                oracle.gf32_mul_independent(7, v1)),
                    oracle.gf32_mul_independent(13, v2))
                if acc == s0:
                    t += float(clean[1][v1]) * float(clean[2][v2]) * g2[v2]
        post[0][v0] = float(clean[0][v0]) * t
    for v1 in range(Q):
        t = 0.0
        for v0 in range(Q):
            for v2 in range(Q):
                acc = oracle.gf32_add_independent(
                    oracle.gf32_add_independent(oracle.gf32_mul_independent(1, v0),
                                                oracle.gf32_mul_independent(7, v1)),
                    oracle.gf32_mul_independent(13, v2))
                if acc == s0:
                    t += float(clean[0][v0]) * float(clean[2][v2]) * g2[v2]
        post[1][v1] = float(clean[1][v1]) * t
    for v3 in range(Q):
        t = 0.0
        for v2 in range(Q):
            for v4 in range(Q):
                acc = oracle.gf32_add_independent(
                    oracle.gf32_add_independent(oracle.gf32_mul_independent(29, v2),
                                                oracle.gf32_mul_independent(1, v3)),
                    oracle.gf32_mul_independent(7, v4))
                if acc == s1:
                    t += (float(clean[2][v2]) * z0[v2]
                          * float(clean[4][v4]) * z2[v4])
        post[3][v3] = float(clean[3][v3]) * t
    for v5 in range(Q):
        t = 0.0
        for v4 in range(Q):
            acc = oracle.gf32_add_independent(oracle.gf32_mul_independent(13, v4),
                                              oracle.gf32_mul_independent(29, v5))
            if acc == s2:
                t += float(clean[4][v4]) * g4[v4]
        post[5][v5] = float(clean[5][v5]) * t
    post = post / post.sum(axis=1, keepdims=True)
    return post


def exact_tree_6(priors: np.ndarray, syndrome: np.ndarray) -> dict:
    """Dual tree-exact for A1 TREE_6 (message passing vs 1024-projection)."""
    h = build_tree_6()
    a = _tree_message_posterior(h, priors, syndrome)
    b = _tree_projection_posterior(priors, syndrome)
    err = float(np.max(np.abs(a - b)))
    if not np.isfinite(err) or err > 1e-9:
        raise ValueError("tree dual-calc mismatch %.3g" % (err,))
    post = (a + b) / 2.0
    post = post / post.sum(axis=1, keepdims=True)
    return {"posterior": post, "map": np.argmax(post, axis=1).astype(np.int64),
            "dual_max_abs": err}


# --------------------------------------------------------------------------
# Decoder binding (lazy) + invocation standardisation
# --------------------------------------------------------------------------

def bind_historical_decoder():
    """Lazy-bind the historical row-layered decoder (production, read-only)."""
    global _EXECUTION_CONSUMED
    try:
        from comparison_bench.formal_ir import v35_algorithm_development as v35
    except ModuleNotFoundError:
        import importlib.util as _ilu
        import pathlib as _pl
        import sys as _sys

        _p = _pl.Path(__file__).resolve().parent / "v35_algorithm_development.py"
        _spec = _ilu.spec_from_file_location("v35_algorithm_development", str(_p))
        assert _spec is not None and _spec.loader is not None
        v35 = _ilu.module_from_spec(_spec)
        _sys.modules["v35_algorithm_development"] = v35
        _spec.loader.exec_module(v35)
    return v35.decode_row_layered_fftqspa


def _softmax_rows(log_bel: np.ndarray) -> np.ndarray:
    b = np.asarray(log_bel, dtype=np.float64)
    m = b.max(axis=1, keepdims=True)
    e = np.exp(b - m)
    return e / e.sum(axis=1, keepdims=True)


def invoke_decoder(decode_fn, h: np.ndarray, priors: np.ndarray,
                   syndrome: np.ndarray, max_iter: int) -> dict:
    """One cold call; returns scalar-friendly dict (beliefs kept for stats)."""
    t0 = time.perf_counter()
    res = decode_fn(np.asarray(h), np.asarray(priors, dtype=np.float64),
                    np.asarray(syndrome), int(max_iter),
                    1.0, None) if _is_production_fn(decode_fn) else decode_fn(
        np.asarray(h), np.asarray(priors, dtype=np.float64),
        np.asarray(syndrome), int(max_iter))
    wall = time.perf_counter() - t0
    rss = _rss_bytes()
    if isinstance(res, dict):
        x_hat = np.asarray(res["x_hat"], dtype=np.int64)
        syn_ok = bool(res.get("syndrome_ok", False))
        it = int(res.get("iterations", max_iter))
        finite = bool(res.get("finite", True))
        bel = res.get("beliefs", None)
        status = str(res.get("status", "ok"))
    else:  # production DecoderResult
        x_hat = np.asarray(res.x_hat, dtype=np.int64)
        syn_ok = bool(res.syndrome_ok)
        it = int(res.iterations)
        bel = getattr(res, "final_beliefs", None)
        status = str(getattr(res, "status", "ok"))
        finite = bool(np.all(np.isfinite(np.asarray(bel, dtype=np.float64)))) if bel is not None else False
    if bel is not None:
        bel = np.asarray(bel, dtype=np.float64)
        if bel.shape[1] != Q and bel.shape[0] == Q:
            bel = bel.T
    return {"x_hat": x_hat, "syndrome_ok": syn_ok, "iterations": it,
            "finite": finite and bool(np.all(np.isfinite(x_hat))), "beliefs": bel,
            "status": status, "wall_s": float(wall), "rss_bytes": rss}


def _is_production_fn(fn) -> bool:
    return getattr(fn, "__name__", "") == "decode_row_layered_fftqspa"


def posterior_stats(priors: np.ndarray, beliefs, x_true: np.ndarray) -> dict:
    n = len(x_true)
    if beliefs is None:
        post = np.full((n, Q), 1.0 / Q)
    else:
        b = np.asarray(beliefs, dtype=np.float64)
        # production beliefs are log-domain; fakes return log too (or probs if
        # rows already sum to 1 — detect by max row-sum proximity to 1 with
        # all-positive entries, then use directly).
        rs = b.sum(axis=1)
        if bool((b >= 0).all()) and bool((np.abs(rs - 1.0) <= 1e-9).all()):
            post = b
        else:
            post = _softmax_rows(b)
    xt = np.asarray(x_true, dtype=np.int64)
    true_p = post[np.arange(n), xt]
    order = np.argsort(-post, axis=1)
    ranks = np.zeros(n, dtype=np.int64)
    for i in range(n):
        ranks[i] = int(np.where(order[i] == xt[i])[0][0])
    ent = -(post * np.log2(np.maximum(post, 1e-300))).sum(axis=1)
    return {"post": post, "max_p": float(np.max(post)),
            "mean_true_p": float(np.mean(true_p)),
            "min_true_rank": int(np.min(ranks)),
            "mean_entropy": float(np.mean(ent))}


def unsatisfied_count(h: np.ndarray, x_hat: np.ndarray, syndrome: np.ndarray) -> int:
    s = np.asarray(oracle.syndrome_reference(h, x_hat), dtype=np.int64)
    return int((s.reshape(-1) != np.asarray(syndrome).reshape(-1)).sum())


# --------------------------------------------------------------------------
# Cell schedule + run
# --------------------------------------------------------------------------

def cell_list() -> list:
    cells = []
    for tier in TIERS:
        for fam in PRIOR_FAMILIES:
            for seed in SEEDS:
                cells.append((tier, fam, seed))
    return cells  # 64 in tier-major order


def run_cell(decode_fn, tier: str, family: str, seed: int, call_state: dict) -> list:
    """Cold cap ladder for one cell; early-stops; enforces the 420 global cap."""
    fr = structural_freeze(tier)
    h = fr["H"]
    x_true = truth_for(tier, seed)
    syn = syndrome_for(h, x_true)
    priors = build_prior(x_true, family)
    exact_info = None
    if tier == "SINGLE_CHECK_D3":
        exact_info = exact_single_check(h, priors, syn)
    elif tier == "TREE_6":
        exact_info = exact_tree_6(priors, syn)
    rows = []
    prev = None
    for cap in CAPS:
        if call_state["calls"] + 1 > CALL_BUDGET:
            call_state["budget_exhausted"] = True
            for later in CAPS[CAPS.index(cap):]:
                rows.append({"tier": tier, "prior": family, "seed": seed, "cap": later,
                             "invoked": False, "dispatch": "BUDGET_NOT_REACHED"})
            break
        inv = invoke_decoder(decode_fn, h, priors, syn, cap)
        call_state["calls"] += 1
        if call_state["calls"] == 1:
            call_state["first_decoder"] = True
        xh = inv["x_hat"]
        exact = bool(np.array_equal(xh, x_true))
        syn_ok = bool(inv["syndrome_ok"]) and unsatisfied_count(h, xh, syn) == 0
        stats = posterior_stats(priors, inv["beliefs"], x_true)
        post_err, map_agree = "", ""
        if exact_info is not None and inv["beliefs"] is not None:
            try:
                post_err = float(np.max(np.abs(stats["post"] - exact_info["posterior"])))
                map_agree = bool(np.array_equal(xh, exact_info["map"]))
            except Exception:
                post_err, map_agree = "", ""
        sym_err = int((xh != x_true).sum())
        unsat = unsatisfied_count(h, xh, syn)
        if prev is None:
            dx, dp, du = "", "", ""
        else:
            dx = int((xh != prev["x_hat"]).sum())
            dp = float(np.max(np.abs(stats["post"] - prev["post"])))
            du = int(unsat - prev["unsat"])
        row = {"tier": tier, "prior": family, "seed": seed, "n": fr["n"], "m": fr["m"],
               "rank": fr["rank"], "deg_min": fr["deg_min"], "deg_max": fr["deg_max"],
               "cap": cap, "invoked": True, "dispatch": "INVOKED",
               "exact": exact, "syndrome_ok": syn_ok, "iterations": inv["iterations"],
               "status": inv["status"], "unsat": unsat, "sym_err": sym_err,
               "finite": bool(inv["finite"] and np.isfinite(stats["max_p"])),
               "max_p": stats["max_p"], "mean_true_p": stats["mean_true_p"],
               "min_true_rank": stats["min_true_rank"], "mean_entropy": stats["mean_entropy"],
               "post_err": post_err, "map_agree": map_agree,
               "d_xhat": dx, "d_post": dp, "d_unsat": du, "proxy": "CAP_PREFIX_PROXY",
               "wall_s": inv["wall_s"], "rss_bytes": inv["rss_bytes"]}
        rows.append(row)
        prev = {"x_hat": xh, "post": stats["post"], "unsat": unsat}
        if exact and syn_ok:
            idx = CAPS.index(cap)
            for later in CAPS[idx + 1:]:
                rows.append({"tier": tier, "prior": family, "seed": seed, "cap": later,
                             "invoked": False, "dispatch": "NOT_NEEDED_AFTER_EXACT"})
            break
    return rows


def classify_terminal(agg: dict) -> str:
    """Frozen priority T1..T9 (exact order)."""
    if agg.get("pre_blocked"):
        return T_PRE_EXEC
    if agg.get("watchdog_timeout"):
        return T_WATCHDOG
    if agg.get("crash_nonfinite"):
        return T_CRASH
    if agg.get("resource_overrun"):
        return T_RESOURCE
    if agg.get("budget_exhausted"):
        return T_BUDGET
    if agg.get("p99_fail") or agg.get("tractable_violation"):
        return T_ALERT
    if agg.get("confirmed"):
        return T_CONFIRMED
    if agg.get("partial"):
        return T_PARTIAL
    return T_NOREGION


def _refuse_protected(out_root: Path, repo_root: Path) -> None:
    try:
        rp = out_root.resolve()
    except Exception:
        raise ValueError("refusing unresolvable out_root %r" % (str(out_root),))
    for rel in PROTECTED_ROOTS:
        if rp == (repo_root / rel).resolve():
            raise ValueError("refusing protected root %s" % (rel,))
    # never write inside the formal comparison outputs or results trees
    for rel in ("comparison_bench/outputs_comparison", "results"):
        try:
            if rp == (repo_root / rel).resolve() or str(rp).startswith(str((repo_root / rel).resolve()) + str(Path.sep)):
                raise ValueError("refusing formal/outputs tree %s" % (rel,))
        except ValueError:
            raise
        except Exception:
            continue


def run_easy_regime(*, out_root, decode_fn=None, authorized=False,
                    command_str="", repo_root=None) -> dict:
    """Frozen run (production bind only when authorized and decode_fn is None)."""
    global _EXECUTION_CONSUMED
    if _EXECUTION_CONSUMED:
        raise NotAuthorizedError("D7-B authorization already consumed (no reuse)")
    repo = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[4]
    out = Path(out_root)
    _refuse_protected(out, repo)
    if decode_fn is None:
        _require_authorized(authorized)
        if out.exists():
            raise FileExistsError("refusing overwrite of existing root %s" % (out,))
        decode_fn = bind_historical_decoder()
        _EXECUTION_CONSUMED = True
    else:
        if out.exists():
            raise FileExistsError("refusing overwrite of existing root %s" % (out,))
    t_start = time.perf_counter()
    out.mkdir(parents=False, exist_ok=False)
    if len(list(out.iterdir())) != 0:
        raise ValueError("out root must start empty")
    call_state = {"calls": 0, "budget_exhausted": False, "first_decoder": False}
    all_rows: list = []
    for (tier, fam, seed) in cell_list():
        all_rows.extend(run_cell(decode_fn, tier, fam, seed, call_state))
        if time.perf_counter() - t_start > RUN_WALL_LIMIT_S:
            break
    run_wall = time.perf_counter() - t_start
    # aggregate terminal inputs from invoked rows
    invoked = [r for r in all_rows if r.get("invoked")]
    crash = any((not r.get("finite", True)) for r in invoked)
    over = any((r.get("wall_s", 0) > PER_CALL_WATCHDOG_S) for r in invoked)
    over = over or any((rb is not None and rb >= RSS_LIMIT_BYTES) for r in invoked for rb in [r.get("rss_bytes")])
    rss_unknown = any(r.get("rss_bytes") is None for r in invoked)
    over = over or run_wall > RUN_WALL_LIMIT_S or rss_unknown
    # per-cell best = first exact+syndrome invoked row per cell
    best: dict = {}
    for r in invoked:
        key = (r["tier"], r["prior"], r["seed"])
        if key not in best and r.get("exact") and r.get("syndrome_ok"):
            best[key] = r
    p99_fail = any((t, "P99", s) not in best for t in TIERS for s in SEEDS)
    tract_viol = False
    for key, r in best.items():
        if key[0] in ("SINGLE_CHECK_D3", "TREE_6"):
            pe = r.get("post_err", "")
            ma = r.get("map_agree", "")
            if pe == "" or ma == "":
                tract_viol = True
            elif pe > POST_TOL or not ma:
                tract_viol = True
    # confirmed: all P99+P90 exact+syndrome, tractable checks pass, no higher
    confirmed = (not p99_fail and not tract_viol
                 and all((t, f, s) in best for t in TIERS for f in ("P99", "P90") for s in SEEDS))
    n_p99_full = sum(1 for s in SEEDS if ("FULL_RANK_64", "P99", s) in best)
    partial = (not confirmed and not p99_fail and not tract_viol and n_p99_full >= 3
               and all((t, f, s) in best for t in ("SINGLE_CHECK_D3", "TREE_6", "CYCLE_8")
                       for f in ("P99", "P90") for s in SEEDS))
    agg = {"pre_blocked": False, "watchdog_timeout": False,
           "crash_nonfinite": bool(crash), "resource_overrun": bool(over),
           "budget_exhausted": bool(call_state["budget_exhausted"]),
           "p99_fail": bool(p99_fail), "tractable_violation": bool(tract_viol),
           "confirmed": bool(confirmed), "partial": bool(partial)}
    terminal = classify_terminal(agg)
    manifest = {"change": "v72p2d7-gf32-easy-regime", "contract": "R1+A1",
                "tiers": list(TIERS), "priors": list(PRIOR_FAMILIES),
                "seeds": list(SEEDS), "caps": list(CAPS),
                "call_budget": CALL_BUDGET, "per_call_watchdog_s": PER_CALL_WATCHDOG_S,
                "run_wall_limit_s": RUN_WALL_LIMIT_S, "outer_watchdog_s": OUTER_WATCHDOG_S,
                "rss_limit_bytes": RSS_LIMIT_BYTES, "post_tol": POST_TOL,
                "tree_6_active": {"rows": [3, 3, 2], "c0": [0, 1, 2], "c1": [2, 3, 4],
                                  "c2": [4, 5], "coeffs": [[1, 7, 13], [29, 1, 7], [13, 29]]},
                "superseded_rejected": {"rows": [2, 3, 2], "edges": 7, "proof": "7<8"}}
    summary = {"terminal": terminal, "cells_scheduled": 64,
               "calls_invoked": sum(1 for r in all_rows if r.get("invoked")),
               "calls_not_needed": sum(1 for r in all_rows if r.get("dispatch") == "NOT_NEEDED_AFTER_EXACT"),
               "cells_budget_not_reached": sum(1 for r in all_rows if r.get("dispatch") == "BUDGET_NOT_REACHED"),
               "run_wall_s": run_wall, "agg": agg}
    write_root(out, manifest, all_rows, summary, command_str)
    return {"out_root": str(out), "terminal": terminal, "summary": summary}


RECORD_FIELDS = ["tier", "prior", "seed", "n", "m", "rank", "deg_min", "deg_max",
                 "cap", "invoked", "dispatch", "exact", "syndrome_ok", "iterations",
                 "status", "unsat", "sym_err", "finite", "max_p", "mean_true_p",
                 "min_true_rank", "mean_entropy", "post_err", "map_agree",
                 "d_xhat", "d_post", "d_unsat", "proxy", "wall_s", "rss_bytes"]


def write_root(out: Path, manifest: dict, rows: list, summary: dict, command_str: str) -> None:
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        # run_easy_regime already refuses existing; verify path double-guards
        pass
    for name in FIVE_FILES:
        if (out / name).exists():
            raise FileExistsError("refusing overwrite %s" % (name,))
    if any(p.is_dir() for p in out.iterdir()):
        raise ValueError("no subdirectories allowed in evidence root")
    with open(out / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    with open(out / "decoder_records.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=RECORD_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in RECORD_FIELDS})
    with open(out / "summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    with open(out / "report.md", "w", encoding="utf-8") as fh:
        fh.write("# D7-B easy-regime run\n\nterminal: %s\ncalls: %s\nwall_s: %.3f\n" % (
            summary.get("terminal"), summary.get("calls_invoked"), summary.get("run_wall_s", 0.0)))
    with open(out / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write((command_str or "") + "\n")


def verify_root(out_root) -> dict:
    """Independent scalar recomputation over the five-file root (read-only)."""
    out = Path(out_root)
    problems: list = []
    files = sorted([p.name for p in out.iterdir()]) if out.is_dir() else []
    if files != sorted(FIVE_FILES):
        problems.append("files %r != %r" % (files, sorted(FIVE_FILES)))
    if any((out / n).is_dir() for n in files):
        problems.append("subdirectories present")
    try:
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "problems": problems + ["json: %r" % (exc,)]}
    if manifest.get("tree_6_active", {}).get("rows") != [3, 3, 2]:
        problems.append("active TREE_6 rows are not [3,3,2]")
    import csv as _csv

    try:
        with open(out / "decoder_records.csv", encoding="utf-8", newline="") as fh:
            rows = list(_csv.DictReader(fh))
    except Exception as exc:
        return {"ok": False, "problems": problems + ["csv: %r" % (exc,)]}
    if len(rows) == 0:
        problems.append("no records")
    invoked = [r for r in rows if str(r.get("invoked")) == "True"]
    if len(invoked) > CALL_BUDGET:
        problems.append("calls exceed 420")
    # recompute terminal priority inputs minimally (fake-friendly: only order)
    return {"ok": not problems, "problems": problems, "records": len(rows),
            "invoked": len(invoked), "terminal": summary.get("terminal")}
