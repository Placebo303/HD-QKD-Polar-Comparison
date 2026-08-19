"""V26 M1 mechanism reference tests (read-only, no production DE).

Independent acceptance of the posterior-population MC-DE extension:
- GF2 BSC/reference sanity (degenerecense; entropy-reduction only-as-feasible).
- GF4 / GF8 small brute-force check-node update vs the jitted WHT coeff kernel.
- Random nonzero coefficient permutation equal to brute force.
- All-one coefficient degeneracy -> standard (no-coeff) XOR convolution.
- Channel-adapter input entropy equals MC-DE iteration-0 mean entropy.
- Fixed-seed replay identical.

These are pure deterministic checks; they do not run the V26 screen.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
from numba import njit

from .nonbinary_field import GF2mField
from .nonbinary_v26_mcde import (_check_update_coeff_jit, build_gf_perm_table,
                                 mean_bits_entropy, run_mcde_posterior,
                                 target_rate_layer, make_rho, _variable_or_belief_jit)

__all__ = [
    "bruteforce_check_node", "check_update_bruteforce_matches",
    "all_one_matches_v14",
    "gf2_bsc_reference", "run_m1_mechanism_tests",
]


def bruteforce_check_node(incoming: list[np.ndarray], coeff: list[int]) -> np.ndarray:
    """Brute-force check-node outgoing message over GF(q) with a zero (identity)
    remaining edge.

    Constraint: ``x_0 = sum_{e} h_e x_e`` (so ``h_0=1``).  The outgoing
    message on edge 0 is ``out[x_0] = sum_{{x_e}} [x_0=sum h_e x_e] prod m_e[x_e]``.
    ``incoming`` are the ``k`` variable messages (length-q), ``coeff`` their
    coefficients.  Exhaustive over the k variables (small q, small k only).
    """
    q = len(incoming[0])
    field = GF2mField.create(q)
    out = np.zeros(q, dtype=np.float64)
    # recursive enumeration
    def rec(ee: int, acc: list[int], w: float):
        if ee == len(incoming):
            # acc = list of x_e; compute sum h_e x_e
            total = 0
            for e in range(len(incoming)):
                total = field.add(total, field.mul(coeff[e], acc[e]))
            out[total] += w
            return
        for v in range(q):
            rec(ee + 1, acc + [v], w * (incoming[ee][v] if incoming[ee][v] > 0 else 0.0))
    rec(0, [], 1.0)
    return out


def check_update_bruteforce_matches(q: int, k: int, seed: int = 7,
                                    tol: float = 1e-9) -> dict[str, Any]:
    """Compare the jitted coeff WHT check kernel to brute force for GF(q), a
    check node with ``k`` incoming edges.

    Kernel setup: the population has ``k`` rows (the ``k`` messages); we keep
    sample 0 active with ``draws[0]=k`` (slots 0..k-1 pick rows 0..k-1 with their
    coefficients); samples 1..k-1 have ``draws[i]=0`` so they contribute a
    delta (uniform after inverse WHT) and are ignored."""
    rng = np.random.default_rng(seed)
    field = GF2mField.create(q)
    perm, nonzero = build_gf_perm_table(q)
    # generate k random but normalized incoming messages (some structured mass)
    msgs = []
    for _ in range(k):
        m = np.full(q, 0.4 / (q - 1), dtype=np.float64)
        m[0] = 0.6
        m += rng.uniform(0, 0.05, size=q)
        m /= m.sum()
        msgs.append(m)
    coeffs = rng.choice(nonzero, size=k, replace=True).astype(np.int64)

    # brute force
    bf = bruteforce_check_node(msgs, coeffs.tolist())
    bf = bf / bf.sum()

    # kernel: n = k population rows (samples), only sample 0 active with all k
    # incoming messages (rows 0..k-1) and their coefficients.
    n = k
    v2c = np.stack(msgs)  # (k, q)
    idx = np.zeros((k, n), dtype=np.int64)
    for d in range(k):
        idx[d, 0] = d  # sample 0, slot d -> message d
    coeff_arr = np.zeros((k, n), dtype=np.int64)
    for d in range(k):
        coeff_arr[d, 0] = coeffs[d]
    draws = np.zeros(n, dtype=np.int64)
    draws[0] = k
    kern = _check_update_coeff_jit(v2c, draws, idx, coeff_arr, perm)
    got = kern[0] / kern[0].sum()
    maxerr = float(np.max(np.abs(got - bf)))
    ok = maxerr <= tol
    return {"q": q, "k": k, "maxerr": maxerr, "ok": ok, "bruteforce": bf,
            "kernel": got, "coeffs": coeffs.tolist()}


def all_one_degeneracy(q: int, k: int, seed: int = 11) -> dict[str, Any]:
    """All-one coefficients must reduce to the standard no-coefficient XOR
    convolution.  Compare coeff-kernel (all h=1) vs direct FFT convolution."""
    rng = np.random.default_rng(seed)
    perm, nonzero = build_gf_perm_table(q)
    v2c = rng.uniform(0, 1, size=(k, q))
    v2c /= v2c.sum(axis=1, keepdims=True)
    n = k
    idx = np.zeros((k, n), dtype=np.int64)
    for d in range(k):
        idx[d, 0] = d
    coeff_arr = np.ones((k, n), dtype=np.int64)
    draws = np.zeros(n, dtype=np.int64)
    draws[0] = k
    got = _check_update_coeff_jit(v2c, draws, idx, coeff_arr, perm)[0]
    got = got / got.sum()
    # reference: brute-force check node with all coefficients = 1 (XOR
    # convolution is exactly the additive-group convolution the kernel does).
    ref = bruteforce_check_node([v2c[e] for e in range(k)], [1] * k)
    ref = ref / ref.sum()
    maxerr = float(np.max(np.abs(got - ref)))
    return {"q": q, "k": k, "maxerr": maxerr, "ok": maxerr <= 1e-9}


def all_one_matches_v14(q: int, k: int, seed: int = 31) -> dict[str, Any]:
    """All-one coefficients must reproduce V14's established no-coefficient
    check-node kernel (``_check_update_jit``) at the actual screen domains
    (GF(32), GF(512))."""
    from .nonbinary_v14_mcde import _check_update_jit
    rng = np.random.default_rng(seed)
    perm, nonzero = build_gf_perm_table(q)
    v2c = rng.uniform(0, 1, size=(k, q))
    v2c /= v2c.sum(axis=1, keepdims=True)
    n = k
    idx = np.zeros((k, n), dtype=np.int64)
    for d in range(k):
        idx[d, 0] = d
    coeff_arr = np.ones((k, n), dtype=np.int64)
    draws = np.zeros(n, dtype=np.int64)
    draws[0] = k
    got = _check_update_coeff_jit(v2c, draws, idx, coeff_arr, perm)[0]
    got = got / got.sum()
    ref = _check_update_jit(v2c, draws, idx)[0]
    ref = ref / ref.sum()
    maxerr = float(np.max(np.abs(got - ref)))
    return {"q": q, "k": k, "maxerr": maxerr, "ok": maxerr <= 1e-9}


def _bsc_sampler_varied(eps: float, q: int = 2):
    """Per-sample BSC posterior population: each sample independently observes a
    flip with prob ``eps``, so rows vary ``[1-eps,eps]`` (no flip) /
    ``[eps,1-eps]`` (flip).  This preserves the per-observation variation that a
    real MC-DE channel population must carry (a degenerate all-identical
    sampler spuriously converges)."""
    def sampler(n: int, rng: np.random.Generator):
        rows = np.tile(np.array([1 - eps, eps], dtype=np.float64), (n, 1))
        flips = rng.random(n) < eps
        if flips.any():
            rows[flips] = rows[flips][:, ::-1]
        return rows
    return sampler


def gf2_bsc_reference() -> dict[str, Any]:
    """Correct centered GF(2) BSC reference for the posterior-population DE.

    A *clearly-decided* reference (never "both non-converge = agree"):
      1. Noiseless BSC (eps=0): the centered posterior is degenerate ``[1,0]``
         for every sample, so the DE **must** converge immediately.
      2. PASS noisy BSC: eps=0.05 at f=2.0 (rate=0.427, dc 3/4) sits well below
         both capacity (0.714) and the (2,dc) concentrated-check ensemble
         threshold, so **both** the V26 posterior-mode DE and the frozen V14
         QSC kernel must converge.
      3. FAIL noisy BSC: eps=0.05 at f=1.0 (rate=0.714, at capacity, dc 6/7) is
         above the degree-2 ensemble threshold, so **neither** must converge
         (guards against spurious convergence; a "fail" here is a correct
         negative verdict, not an unexplained one).

    The channel population ``_bsc_sampler_varied`` is exactly the true-symbol
    centered BSC posterior (rows ``[1-eps,eps]`` / ``[eps,1-eps]``), which is
    the same distribution the V14 QSC mode constructs at q=2.
    """
    import numpy as np
    from .nonbinary_v14_mcde import run_mcde as v14_run_mcde
    q = 2
    lam = {2: 1.0}
    n = 400
    max_iter = 120

    def _run(eps: float, f: float, seed: int) -> tuple[dict, dict]:
        h = -eps*math.log2(eps) - (1-eps)*math.log2(1-eps)
        rate = target_rate_layer(f, h, 1)
        rho = make_rho(rate, lam)
        sp = _bsc_sampler_varied(eps, q)
        mine = run_mcde_posterior(q, lam, rho, channel_sampler=sp,
                                  n_samples=n, max_iter=max_iter, seed=seed,
                                  entropy_tol_bits=0.01, streak=20)
        v14 = v14_run_mcde(q=q, lambda_edge=lam, rho_edge=rho, n_samples=n,
                           max_iter=max_iter, seed=seed, channel_mode="qsc",
                           p=eps, entropy_tol=0.01, streak=20)
        return mine, v14, h, rate, rho

    # 2) PASS noisy: well below ensemble threshold -> both modes converge
    eps = 0.05
    mp, vp, h_pass, rate_pass, rho_pass = _run(eps, 2.0, seed=123)
    pass_mine_conv = bool(mp["converged"])
    pass_v14_conv = bool(vp["converged"])

    # 1) noiseless degeneracy with a *feasible* rho (dc 3/4 from the PASS code):
    #    the degenerate ``[1,0]`` posterior must converge immediately (streak 20).
    nodal = run_mcde_posterior(q, lam, rho_pass, channel_sampler=_bsc_sampler_varied(0.0, q),
                               n_samples=n, max_iter=30, seed=1,
                               entropy_tol_bits=0.01, streak=20)
    noiseless_conv = bool(nodal["converged"])
    noiseless_iters = int(nodal["iterations"])

    # 3) FAIL noisy: at capacity -> both modes must NOT spuriously converge
    mf, vf, h_fail, rate_fail, rho_fail = _run(eps, 1.0, seed=123)
    fail_mine_conv = bool(mf["converged"])
    fail_v14_conv = bool(vf["converged"])

    # cross-mode verdict agreement is kept as an observational field only
    agree_pass = bool(pass_mine_conv == pass_v14_conv)
    agree_fail = bool(fail_mine_conv == fail_v14_conv)

    ok = bool(
        noiseless_conv                       # noiseless must converge
        and pass_mine_conv and pass_v14_conv  # feasible rate must converge
        and (not fail_mine_conv) and (not fail_v14_conv)  # and a hard rate must fail
    )
    return {
        "h_bsc_pass": h_pass, "rate_pass": rate_pass,
        "h_bsc_fail": h_fail, "rate_fail": rate_fail,
        "rho_pass_dc": sorted(int(k) for k in rho_pass),
        "rho_fail_dc": sorted(int(k) for k in rho_fail),
        "noiseless_conv": noiseless_conv, "noiseless_iters": noiseless_iters,
        "pass_mine_conv": pass_mine_conv, "pass_v14_conv": pass_v14_conv,
        "pass_iters_mine": int(mp["iterations"]), "pass_iters_v14": int(vp["iterations"]),
        "fail_mine_conv": fail_mine_conv, "fail_v14_conv": fail_v14_conv,
        "agree_with_v14": bool(agree_pass and agree_fail),
        "agree_pass": bool(agree_pass), "agree_fail": bool(agree_fail),
        "ok": ok,
    }


def adapter_input_entropy_matches_iter0(q: int, lam_any: dict, rho_any: dict,
                                        sampler, seed: int = 99,
                                        n_samples: int = 2000) -> dict[str, Any]:
    """The MC-DE **iteration-0 channel entropy** equals the adapter's centered
    posterior channel entropy (distributional), and is genuinely fed from the
    adapter's centered posterior population (deterministic identity).

    Enters the real MC-DE first round (``max_iter=1``) with
    ``record_channel_entropy=True`` and reads the mean bits/symbol entropy of
    the channel population the kernel actually consumed at iteration 0.  This
    is *not* a sampler-replay tautology:
      - ``err_replay``: replaying the exact first channel draw with the same
        PCG64 seed must reproduce the DE's own recorded channel entropy
        (consistency, 0 to float roundoff);
      - ``err_model``: an independent large draw from the adapter model must
        match the DE iteration-0 channel entropy within finite-sample sampling
        tolerance (distributional equality).
    """
    run = run_mcde_posterior(q, lam_any, rho_any, channel_sampler=sampler,
                             n_samples=n_samples, max_iter=1, seed=seed,
                             entropy_tol_bits=0.01, streak=20,
                             record_channel_entropy=True)
    iter0_H = float(run["channel_entropy_trace_bits"][0])
    # exact channel population the DE consumed at iteration 0 (same seed)
    rng_re = np.random.default_rng(seed)
    replay_H = mean_bits_entropy(_channel_rows(sampler, n_samples, rng_re), q)
    err_replay = abs(iter0_H - replay_H)
    # independent adapter-model draw (distributional reference)
    rng_mod = np.random.default_rng(seed + 1_000_003)
    model_H = mean_bits_entropy(_channel_rows(sampler, n_samples, rng_mod), q)
    err_model = abs(iter0_H - model_H)
    # ~3x the observed finite-sample std of the per-2000 mean for q=2 (0.0084);
    # 0.03 bits/symbol is conservative and robust for the q=2 A01 L2 channel.
    sampling_tol = 0.03
    ok = bool(err_replay <= 1e-10 and err_model <= sampling_tol)
    return {"iter0_H_bits": iter0_H, "replay_H_bits": replay_H,
            "model_H_bits": model_H, "err_replay": err_replay,
            "err_model": err_model, "n_samples": n_samples,
            "sampling_tol": sampling_tol, "ok": bool(ok)}


def _channel_rows(sampler, n, rng):
    return np.asarray(sampler(n, rng), dtype=np.float64)


def seed_replay_identical(q: int, lam_any: dict, rho_any: dict, sampler,
                          seed: int = 77) -> dict[str, Any]:
    r1 = run_mcde_posterior(q, lam_any, rho_any, channel_sampler=sampler,
                            n_samples=200, max_iter=8, seed=seed,
                            entropy_tol_bits=0.01, streak=20)
    r2 = run_mcde_posterior(q, lam_any, rho_any, channel_sampler=sampler,
                            n_samples=200, max_iter=8, seed=seed,
                            entropy_tol_bits=0.01, streak=20)
    same = (r1["entropy_trace_bits"] == r2["entropy_trace_bits"]) and \
           (r1["converged"] == r2["converged"])
    return {"same_trace": bool(same), "ok": bool(same)}


def run_m1_mechanism_tests(adapter) -> dict[str, Any]:
    """Run the full M1 mechanism reference suite against a ChannelAdapter.

    Returns a report with per-test ``ok`` flags and a top-level ``all_ok``.
    """
    # helper for a lightweight default channel (L1 is cheap for small q only at
    # GF2; use L2 of A01).  Use an arbitrary layer with its own sampler.
    sampler_l2 = adapter.make_channel_sampler("L2")  # GF2 for A01
    q_l2 = 2
    H = adapter.H_bits["L2"]
    lam = {2: 1.0}
    rho_l2 = make_rho(target_rate_layer(1.3, H, 1), lam)

    tests: dict[str, dict[str, Any]] = {}
    # 1-3 brute force GF4 / GF8
    for q in (4, 8):
        for k in (2, 3):
            r = check_update_bruteforce_matches(q, k, seed=q * 100 + k)
            tests[f"bruteforce_gf{q}_k{k}"] = {"ok": bool(r["ok"]), "maxerr": r["maxerr"]}
    # 4 all-one degeneracy (small q brute force + actual screen domains vs V14)
    for q in (4, 8):
        r = all_one_degeneracy(q, 3, seed=q + 20)
        tests[f"all_one_gf{q}"] = {"ok": bool(r["ok"]), "maxerr": r["maxerr"]}
    for q in (32, 512):
        r = all_one_matches_v14(q, 3, seed=q + 50)
        tests[f"all_one_gf{q}_vs_v14"] = {"ok": bool(r["ok"]), "maxerr": r["maxerr"]}
    # 5 adapter input entropy == MC-DE iteration-0 channel entropy (real first round)
    ia = adapter_input_entropy_matches_iter0(q_l2, lam, rho_l2, sampler_l2, seed=99)
    tests["adapter_entropy_iter0"] = {"ok": bool(ia["ok"]),
                                      "err_replay": ia["err_replay"],
                                      "err_model": ia["err_model"],
                                      "sampling_tol": ia["sampling_tol"],
                                      "iter0_H": ia["iter0_H_bits"],
                                      "model_H": ia["model_H_bits"]}
    # 6 fixed-seed replay identical
    rp = seed_replay_identical(q_l2, lam, rho_l2, sampler_l2, seed=77)
    tests["seed_replay"] = {"ok": bool(rp["ok"]), "same": rp["same_trace"]}
    # 7 centered GF2 BSC reference (noiseless must converge; noisy clearly decided)
    bsc = gf2_bsc_reference()
    tests["gf2_bsc_reference"] = {"ok": bool(bsc["ok"]),
                                  "scheme": "noiseless_conv+pass_conv+fail_no_conv",
                                  "noiseless_conv": bsc["noiseless_conv"],
                                  "pass_mine_conv": bsc["pass_mine_conv"],
                                  "pass_v14_conv": bsc["pass_v14_conv"],
                                  "fail_mine_conv": bsc["fail_mine_conv"],
                                  "fail_v14_conv": bsc["fail_v14_conv"],
                                  "rate_pass": bsc["rate_pass"],
                                  "rate_fail": bsc["rate_fail"],
                                  "agree_with_v14": bsc["agree_with_v14"]}

    all_ok = all(t["ok"] for t in tests.values())
    return {"schema": "nbldpc_v26_m1_mechanism_v1", "all_ok": bool(all_ok),
            "tests": tests}
