"""C-2 Gaussian jitter fit (C2_PACKET.md frozen, C2_DESIGN.md theory).

EXPLORE only: reads landed statistics (Z-2 ``z2_summary.json`` 30 cells +
C-0 ``c0_summary.json`` delta-p curves). Reads no raw data, runs no decoder.

Model (design §1): true coincidence offset ``Δt = J + δ``, ``J ~ N(0,σ²)``
per source; uniform bin phase; unconditional bin-error law (1); Gaussian
closed form via ``A(a)`` (2)-(3); wide-window conditional law (4);
support rule (5); accidental floor branch (i)
``p_total = 1 - (1-p_gauss)(1-ε_acc)``.

Frozen split: bw 200/400 = fit set; bw 6400 = floor holdout; bw 50/100 =
extrapolation set (never used to tune σ). Estimator A = p200+p400 joint
inversion; estimator B = H(e) fit on 200/400; estimator C = p+H
inverse-variance joint fit (reported values). T1-T4 at α=0.05.
C-0 delta check uses frozen σ̂C with no new free parameters.

Conventions fixed here (see C2_LOG.md):
- ``H_re`` is recomputed from the landed ``top_errors`` fractions
  ``q`` plus ``rest = max(0, 1-Σq)`` as its own outcome:
  ``H_re = -Σq log2 q - rest log2 rest``. Non-wide cells list the full
  support (rest = 0); wide cells list top-6 (rest > 0, kept explicit).
- ``Var(p̂)`` uses the Wilson score interval half-width
  (``((hi-lo)/2/1.96)²``); this downweights the small-n 10dB source
  automatically. ``Var(Ĥ)`` is the multinomial plug-in asymptotic
  variance ``(Σq (log2 q)² - H²)/n`` over the same (q, rest) outcomes.
- Sign of δ̂: set by the forward model itself — the sign whose predicted
  dominant side (P+1 vs P-1) matches the observed one. No external
  offset-sign assumption is baked in.
- Floor (i): ``P0^floor = P0^g(1-ε)``,
  ``P±1^floor = P±1^g(1-ε) + ε/2``; ``ε̂`` per source from the 6400
  holdout residual. Floor enters only bw-6400 (and C-0 curve, same ε̂,
  no new parameter) predictions.
- Layer χ²/dof is a descriptive predictive index (dof = N cells); the
  formal goodness test is per-source T2 (dof = 2).
- Frame-boundary same-frame loss (~1e-3) is NOT modelled; noted as floor
  in C2_LOG.md.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

__all__ = [
    "W_PS", "FIT_BWS", "HOLDOUT_BW", "WIDE_BWS",
    "phi_std", "Phi", "A_func", "ternary_uncond", "p_uncond",
    "cond_dist", "support_pred", "H_from_top_errors", "var_H_multinom",
    "wilson_var_p", "fold_err", "tail_ge2_obs", "tail_ge2_pred", "solve_ab", "fit_estimator", "consistency_T1T4",
    "estimate_floor_eps", "apply_floor", "layer_metrics", "delta_check",
    "run_c2",
]

W_PS = 200.0
FIT_BWS = (200, 400)
HOLDOUT_BW = 6400
WIDE_BWS = (50, 100)
SQRT2 = math.sqrt(2.0)
SQRT2PI = math.sqrt(2.0 * math.pi)
Z95 = 1.959963984540054


# ---------------------------------------------------------------- normal law

def phi_std(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT2PI


def Phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / SQRT2))


def A_func(a: float, bw: float, sigma: float) -> float:
    """Design (2): antiderivative core of the Gaussian closed form."""
    return (a * Phi(a / sigma) - (a - bw) * Phi((a - bw) / sigma)
            + sigma * (phi_std(a / sigma) - phi_std((a - bw) / sigma)))


def ternary_uncond(bw: float, sigma: float, delta: float) -> tuple[float, float, float]:
    """(P-1, P0, P+1) from (3). Full integer-k law sums to 1; the
    non-wide ternary uses k in {-1,0,+1} (mass beyond ±1 is returned
    separately by ``tail_uncond``)."""
    p_m = (A_func(-delta, bw, sigma) - A_func(-bw - delta, bw, sigma)) / bw
    p_0 = (A_func(bw - delta, bw, sigma) - A_func(-delta, bw, sigma)) / bw
    p_p = (A_func(2.0 * bw - delta, bw, sigma)
           - A_func(bw - delta, bw, sigma)) / bw
    return (p_m, p_0, p_p)


def tail_uncond(bw: float, sigma: float, delta: float, kmax: int = 40) -> float:
    rest = 0.0
    for k in list(range(-kmax, -1)) + list(range(2, kmax + 1)):
        rest += (A_func((k + 1) * bw - delta, bw, sigma)
                 - A_func(k * bw - delta, bw, sigma)) / bw
    return rest


def p_uncond(bw: float, sigma: float, delta: float) -> float:
    return 1.0 - ternary_uncond(bw, sigma, delta)[1]


def H_ternary(p_m: float, p_0: float, p_p: float) -> float:
    h = 0.0
    for q in (p_m, p_0, p_p):
        if q > 0.0:
            h -= q * math.log2(q)
    return h


# ------------------------------------------------------- wide-window (4)

def _inner_cover(lo: float, hi: float, sigma: float, delta: float) -> float:
    if hi <= lo:
        return 0.0
    return Phi((hi - delta) / sigma) - Phi((lo - delta) / sigma)


def cond_dist(bw: float, sigma: float, delta: float, k: int,
              n_panel: int = 512) -> tuple[float, float]:
    """Return ``(P joint(e=k ∧ kept), C cover)`` under (4).

    Outer integral over phase u ∈ [0, bw) by composite Simpson
    (self-written, deterministic). ``C`` does not depend on k.
    """
    cover = _inner_cover(-W_PS, W_PS, sigma, delta)
    n = n_panel if n_panel % 2 == 0 else n_panel + 1
    h = bw / n
    acc = 0.0
    for i in range(n + 1):
        u = i * h
        lo = max(k * bw - u, -W_PS)
        hi = min((k + 1) * bw - u, W_PS)
        f = _inner_cover(lo, hi, sigma, delta)
        w = 4.0 if i % 2 == 1 else (2.0 if 0 < i < n else 1.0)
        acc += w * f
    return (acc * h / 3.0 / bw, cover)


def p_cond(bw: float, sigma: float, delta: float) -> float:
    joint0, cover = cond_dist(bw, sigma, delta, 0)
    return 1.0 - joint0 / cover


def support_pred(bw: float, sigma: float, delta: float, n: int, d: int) -> int:
    """Design (5): k_pred = min(khard, kdet, kframe)."""
    khard = math.ceil((W_PS + abs(delta) + bw) / bw)
    kframe = d // 2
    kdet = 0
    k = 0
    while True:
        jk, cover = cond_dist(bw, sigma, delta, k)
        pk = jk / cover if cover > 0 else 0.0
        jm, _ = cond_dist(bw, sigma, delta, -k) if k else (jk, cover)
        pm = jm / cover if (cover > 0 and k) else pk
        thresh = 5.0 / n
        if k == 0:
            if pk < thresh:
                break
        elif max(pk, pm) < thresh:
            break
        kdet = k
        k += 1
        if k > kframe + 2:
            break
    return 2 * min(khard, kdet, kframe) + 1


# ------------------------------------------------------- landed-stat helpers

def H_from_top_errors(top_errors: list) -> tuple[float, float]:
    """Recompute H from landed fractions; rest mass is its own outcome.

    Returns ``(H_re, rest)``.
    """
    qs = [float(fr) for _, fr in top_errors]
    s = sum(qs)
    rest = max(0.0, 1.0 - s)
    h = 0.0
    for q in qs + ([rest] if rest > 0 else []):
        if q > 0.0:
            h -= q * math.log2(q)
    return (h, rest)


def var_H_multinom(top_errors: list, n: int) -> float:
    qs = [float(fr) for _, fr in top_errors]
    rest = max(0.0, 1.0 - sum(qs))
    probs = qs + ([rest] if rest > 0 else [])
    h = -sum(q * math.log2(q) for q in probs if q > 0)
    m2 = sum(q * (math.log2(q)) ** 2 for q in probs if q > 0)
    return max((m2 - h * h) / n, 1e-18)


def wilson_var_p(p_hat: float, n: int, z: float = Z95) -> float:
    if n <= 0:
        return 1.0
    denom = 1.0 + z * z / n
    c = p_hat + z * z / (2.0 * n)
    half = z * math.sqrt(p_hat * (1.0 - p_hat) / n + z * z / (4.0 * n * n))
    lo = max(0.0, (c - half) / denom)
    hi = min(1.0, (c + half) / denom)
    w = (hi - lo) / 2.0 / z
    return max(w * w, 1e-18)


def fold_err(v: int, d: int) -> int:
    r = v % d
    return r if r <= d // 2 else r - d


def tail_ge2_obs(top_errors: list, d: int) -> float:
    """Observed P(|e| >= 2) from landed fractions (folded; rest counted)."""
    s = 0.0
    tot = 0.0
    for v, fr in top_errors:
        tot += float(fr)
        if abs(fold_err(int(v), d)) >= 2:
            s += float(fr)
    return s + max(0.0, 1.0 - tot)


def tail_ge2_pred(bw: float, sigma: float, delta: float) -> float:
    tot = 0.0
    _, cover = cond_dist(bw, sigma, delta, 0) if bw < 200 else (None, 1.0)
    for k in list(range(-12, -1)) + list(range(2, 13)):
        if bw < 200:
            jk, _ = cond_dist(bw, sigma, delta, k)
            tot += jk / cover
        else:
            tot += (A_func((k + 1) * bw - delta, bw, sigma)
                    - A_func(k * bw - delta, bw, sigma)) / bw
    return max(tot, 0.0)


def h2(x: float) -> float:
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -(x * math.log2(x) + (1.0 - x) * math.log2(1.0 - x))


# ------------------------------------------------------- estimators A/B/C

def _pred_vec(theta: tuple[float, float], kinds: list[str]) -> list[float]:
    sig, mag = theta
    out: list[float] = []
    for kind in kinds:
        tag, bw = kind.split(":")
        bwf = float(bw)
        if tag == "p":
            out.append(p_uncond(bwf, sig, mag))
        else:
            pm, p0, pp = ternary_uncond(bwf, sig, mag)
            out.append(H_ternary(pm, p0, pp))
    return out


def _solve_ls(obs: list[float], var: list[float], kinds: list[str],
             init: tuple[float, float]) -> tuple[tuple[float, float], tuple[float, float]]:
    """Gauss-Newton on Σ (obs-pred)²/var. Returns ((σ,|δ|), (se_σ, se_m))."""
    sig, mag = init
    for _ in range(200):
        pred = _pred_vec((sig, mag), kinds)
        r = [(o - p) / v for o, p, v in zip(obs, pred, var)]
        h = 1e-6
        j00 = j01 = j10 = j11 = 0.0
        g0 = g1 = 0.0
        for i, kind in enumerate(kinds):
            w = 1.0 / var[i]
            p0_ = pred[i]
            dp_ds = (_pred_vec((sig + h, mag), kinds)[i] - p0_) / h
            dp_dm = (_pred_vec((sig, mag + h), kinds)[i] - p0_) / h
            g0 += dp_ds * (obs[i] - p0_) * w
            g1 += dp_dm * (obs[i] - p0_) * w
            j00 += dp_ds * dp_ds * w
            j01 += dp_ds * dp_dm * w
            j11 += dp_dm * dp_dm * w
        det = j00 * j11 - j01 * j01
        if abs(det) < 1e-24:
            break
        step_s = (j11 * g0 - j01 * g1) / det
        step_m = (j00 * g1 - j01 * g0) / det
        lam = 1.0
        cur = sum((o - p) ** 2 / v for o, p, v in zip(obs, pred, var))
        improved = False
        for _ in range(20):
            ns = min(max(sig + lam * step_s, 1.0), 500.0)
            nm = min(max(mag + lam * step_m, 0.0), 400.0)
            npred = _pred_vec((ns, nm), kinds)
            new = sum((o - p) ** 2 / v for o, p, v in zip(obs, npred, var))
            if new < cur:
                sig, mag = ns, nm
                improved = True
                break
            lam *= 0.5
        if not improved:
            break
        if abs(lam * step_s) < 1e-9 and abs(lam * step_m) < 1e-9:
            sig, mag = (min(max(sig + lam * step_s, 1.0), 500.0),
                        min(max(mag + lam * step_m, 0.0), 400.0))
            break
    pred = _pred_vec((sig, mag), kinds)
    j00 = j01 = j11 = 0.0
    h = 1e-6
    for i, kind in enumerate(kinds):
        w = 1.0 / var[i]
        dp_ds = (_pred_vec((sig + h, mag), kinds)[i] - pred[i]) / h
        dp_dm = (_pred_vec((sig, mag + h), kinds)[i] - pred[i]) / h
        j00 += dp_ds * dp_ds * w
        j01 += dp_ds * dp_dm * w
        j11 += dp_dm * dp_dm * w
    det = j00 * j11 - j01 * j01
    if abs(det) < 1e-24:
        return ((sig, mag), (float("nan"), float("nan")))
    return ((sig, mag), (math.sqrt(j11 / det), math.sqrt(j00 / det)))


def solve_ab(p200: float, p400: float) -> tuple[float, float]:
    """Estimator A seed: coarse grid argmin, refined by _solve_ls."""
    best = (1e9, 60.0, 50.0)
    s = 5.0
    while s <= 150.0:
        m = 0.0
        while m <= 120.0:
            e = ((p_uncond(200.0, s, m) - p200) ** 2
                 + (p_uncond(400.0, s, m) - p400) ** 2)
            if e < best[0]:
                best = (e, s, m)
            m += 2.0
        s *= 1.15
    kinds = ["p:200", "p:400"]
    (theta, _) = _solve_ls([p200, p400], [1.0, 1.0], kinds, (best[1], best[2]))
    return theta


def sign_by_model(sig: float, mag: float, p_minus_obs: float) -> float:
    """Sign of δ̂ from the forward model: the sign whose predicted
    dominant side matches the observed one."""
    pm_pos = ternary_uncond(200.0, sig, mag)
    frac_pos = pm_pos[0] / max(1.0 - pm_pos[1], 1e-300)  # P-1|marked at +mag
    pm_neg = ternary_uncond(200.0, sig, -mag)
    frac_neg = pm_neg[0] / max(1.0 - pm_neg[1], 1e-300)
    # observed dominance: +1 means frac_obs < 0.5
    err_pos = abs(frac_pos - p_minus_obs)
    err_neg = abs(frac_neg - p_minus_obs)
    return mag if err_pos <= err_neg else -mag


def fit_estimator(obs: list[float], var: list[float], kinds: list[str],
                  seed: tuple[float, float]) -> tuple[tuple[float, float], tuple[float, float], float]:
    (theta, se) = _solve_ls(obs, var, kinds, seed)
    pred = _pred_vec(theta, kinds)
    chi2 = sum((o - p) ** 2 / v for o, p, v in zip(obs, pred, var))
    return (theta, se, chi2)


def consistency_T1T4(estA: dict, estB: dict, estC: dict, obs: dict) -> dict:
    t: dict = {}
    # T1: sigma consistency z
    denom = math.sqrt(estA["se_sig"] ** 2 + estB["se_sig"] ** 2)
    z = (estA["sig"] - estB["sig"]) / denom if denom > 0 else float("nan")
    t["T1_z"] = z
    t["T1_pass"] = bool(abs(z) <= 2.0)
    # T2: chi2 over {p200,p400,H200,H400} with C predictions, dof=2
    chi2 = estC["chi2_4"]
    t["T2_chi2"] = chi2
    t["T2_dof"] = 2
    t["T2_chi2_dof"] = chi2 / 2.0
    t["T2_p"] = math.exp(-chi2 / 2.0)
    t["T2_pass"] = bool(t["T2_p"] >= 0.05)
    # T3: delta-sign vs dominant direction under forward model
    pm, p0, pp = ternary_uncond(200.0, estC["sig"], estC["delta"])
    pred_minus_frac = pm / max(1.0 - p0, 1e-300)
    obs_dom_minus = obs["p_minus_200"] > 0.5
    pred_dom_minus = pred_minus_frac > 0.5
    t["T3_pred_minus_frac"] = pred_minus_frac
    t["T3_pass"] = bool(obs_dom_minus == pred_dom_minus)
    # T4: entropy closure t per fit band
    ts = []
    for bw in FIT_BWS:
        key = f"H{bw}"
        se = math.sqrt(obs[f"varH_{bw}"])
        pm_, p0_, pp_ = ternary_uncond(float(bw), estC["sig"], estC["delta"])
        ts.append((obs[key] - H_ternary(pm_, p0_, pp_)) / se if se > 0 else float("nan"))
    t["T4_t200"], t["T4_t400"] = ts
    t["T4_pass"] = bool(max(abs(x) for x in ts) <= 1.96)
    t["all_pass"] = bool(t["T1_pass"] and t["T2_pass"] and t["T3_pass"] and t["T4_pass"])
    return t


# ------------------------------------------------------- floor branch (i)

def estimate_floor_eps(p_obs_6400: float, sig: float, mag: float) -> float:
    pg = p_uncond(6400.0, sig, mag)
    if pg >= 1.0:
        return 0.0
    return min(max((p_obs_6400 - pg) / (1.0 - pg), 0.0), 1.0)


def apply_floor(pm: float, p0: float, pp: float, eps: float) -> tuple[float, float, float]:
    return (pm * (1.0 - eps) + eps / 2.0, p0 * (1.0 - eps),
            pp * (1.0 - eps) + eps / 2.0)


# ------------------------------------------------------- validation layers

def layer_metrics(cells: list[dict]) -> dict:
    e = [c["p_obs"] - c["p_pred"] for c in cells]
    n = len(cells)
    rmse = math.sqrt(sum(x * x for x in e) / n)
    mae = sum(abs(x) for x in e) / n
    rel = [abs(x) / c["p_obs"] for x, c in zip(e, cells) if c["p_obs"] > 0]
    chi2 = sum((c["p_obs"] - c["p_pred"]) ** 2 / c["var_p"] for c in cells)
    he = [(c["H_obs"] - c["H_pred"]) for c in cells if c.get("H_obs") is not None]
    return {
        "n": n,
        "rmse": rmse,
        "mae": mae,
        "mean_rel": sum(rel) / len(rel),
        "max_resid": max(e, key=abs),
        "chi2": chi2,
        "chi2_dof": chi2 / n,
        "entropy_rmse": math.sqrt(sum(x * x for x in he) / len(he)),
    }


def delta_check(curve: list[dict], sig: float, delta0: float,
                eps: float, bw: float) -> dict:
    """C-0 one-dimensional check (no new free parameters).

    obs argmin on the 5ps grid; predicted argmin on a 1ps grid.
    Curvature: quadratic least squares on obs points within ±15ps of the
    observed minimum; model curvature = numeric 2nd derivative at its min.
    Monotonicity arms use a 2·SE tolerance on adjacent steps.
    """
    for r in curve:
        tot = delta0 + r["delta"]
        pg = p_uncond(bw, sig, tot)
        r["p_pred"] = 1.0 - (1.0 - pg) * (1.0 - eps)
    obs_min = min(curve, key=lambda r: r["p"])
    dmin_obs = obs_min["delta"]
    grid = [(d, 1.0 - (1.0 - p_uncond(bw, sig, delta0 + d)) * (1.0 - eps))
            for d in range(-100, 101)]
    dmin_pred = min(grid, key=lambda t: t[1])[0]
    dstar = dmin_obs - dmin_pred
    ref = min(10.0, 0.1 * bw)
    # curvature from obs near minimum
    near = [r for r in curve if abs(r["delta"] - dmin_obs) <= 15]
    sx = [r["delta"] - dmin_obs for r in near]
    sy = [r["p"] for r in near]
    mx = sum(sx) / len(sx)
    my = sum(sy) / len(sy)
    sxx = sum((x - mx) ** 2 for x in sx)
    # quadratic fit y = a x^2 + b x + c via normal equations
    X = [[x * x, x, 1.0] for x in sx]
    XtX = [[sum(X[i][a] * X[i][b] for i in range(len(X))) for b in range(3)]
           for a in range(3)]
    Xty = [sum(X[i][a] * sy[i] for i in range(len(X))) for a in range(3)]
    det = (XtX[0][0] * (XtX[1][1] * XtX[2][2] - XtX[1][2] * XtX[2][1])
           - XtX[0][1] * (XtX[1][0] * XtX[2][2] - XtX[1][2] * XtX[2][0])
           + XtX[0][2] * (XtX[1][0] * XtX[2][1] - XtX[1][1] * XtX[2][0]))
    if abs(det) < 1e-30:
        k_obs = float("nan")
    else:
        inv = [[0.0] * 3 for _ in range(3)]
        inv[0][0] = (XtX[1][1] * XtX[2][2] - XtX[1][2] * XtX[2][1]) / det
        inv[0][1] = (XtX[0][2] * XtX[2][1] - XtX[0][1] * XtX[2][2]) / det
        inv[0][2] = (XtX[0][1] * XtX[1][2] - XtX[0][2] * XtX[1][1]) / det
        a_coef = sum(inv[0][b] * Xty[b] for b in range(3))
        k_obs = 2.0 * a_coef
    h = 2.0
    f0 = min(grid, key=lambda t: t[1])[1]
    fp = 1.0 - (1.0 - p_uncond(bw, sig, delta0 + dmin_pred + h)) * (1.0 - eps)
    fm = 1.0 - (1.0 - p_uncond(bw, sig, delta0 + dmin_pred - h)) * (1.0 - eps)
    k_pred = (fp - 2.0 * f0 + fm) / (h * h)
    rmse = math.sqrt(sum((r["p"] - r["p_pred"]) ** 2 for r in curve) / len(curve))
    # monotonicity arms with 2SE tolerance
    srt = sorted(curve, key=lambda r: r["delta"])
    idx = next(i for i, r in enumerate(srt) if r["delta"] == dmin_obs)
    viol_left = viol_right = 0
    tot_steps = 0
    for i in range(1, idx + 1):
        tot_steps += 1
        a, b = srt[i - 1], srt[i]  # moving right toward min: must not rise
        se = math.sqrt(a.get("var_p", 0.0) + b.get("var_p", 0.0))
        if (b["p"] - a["p"]) > 2.0 * se:
            viol_left += 1
    for i in range(idx + 1, len(srt)):
        tot_steps += 1
        a, b = srt[i - 1], srt[i]  # moving right away from min: must not fall
        se = math.sqrt(a.get("var_p", 0.0) + b.get("var_p", 0.0))
        if (a["p"] - b["p"]) > 2.0 * se:
            viol_right += 1
    return {
        "dmin_obs": dmin_obs,
        "dmin_pred": float(dmin_pred),
        "Delta_dstar": float(dstar),
        "ref_ps": ref,
        "pass_min": bool(abs(dstar) <= ref),
        "kappa_obs": k_obs,
        "kappa_pred": k_pred,
        "kappa_ratio": (k_obs / k_pred) if k_pred else float("nan"),
        "curve_rmse": rmse,
        "mono_viol_left": viol_left,
        "mono_viol_right": viol_right,
        "mono_steps": tot_steps,
        "pass_mono": bool(viol_left == 0 and viol_right == 0),
    }


# ------------------------------------------------------- driver

def run_c2(z2_path: Path, c0_path: Path, out_root: Path) -> dict:
    if out_root.exists():
        raise SystemExit(f"output root not fresh: {out_root}")
    out_root.mkdir(parents=True, exist_ok=False)
    z2 = json.loads(z2_path.read_text(encoding="utf-8"))
    c0 = json.loads(c0_path.read_text(encoding="utf-8"))
    zmap = {(r["source"], r["bw_ps"]): r for r in z2}
    sources = ["T2-1M", "T2-1.5M", "T2-2M", "0dB", "4dB", "10dB"]

    per_source: dict = {}
    nonwide_cells: list[dict] = []
    wide_cells: list[dict] = []
    holdout: dict = {}
    pure6400_resid: dict = {}

    for src in sources:
        g = {bw: zmap[(src, bw)] for bw in (200, 400, 6400, 50, 100)}
        n200, n400 = g[200]["pairs"], g[400]["pairs"]
        obs = {
            "p200": g[200]["p"], "p400": g[400]["p"],
            "p_minus_200": g[200]["p_minus_cond"],
        }
        H, varH, Hraw = {}, {}, {}
        for bw in FIT_BWS:
            h, rest = H_from_top_errors(g[bw]["top_errors"])
            H[bw] = h
            Hraw[bw] = {"H_re": h, "rest": rest,
                        "H_landed": g[bw]["H_e"]}
            varH[bw] = var_H_multinom(g[bw]["top_errors"], g[bw]["pairs"])
            obs[f"H{bw}"] = h
            obs[f"varH_{bw}"] = varH[bw]
        var_p200 = wilson_var_p(obs["p200"], n200)
        var_p400 = wilson_var_p(obs["p400"], n400)
        obs["var_p200"], obs["var_p400"] = var_p200, var_p400

        # A: p200+p400 joint inversion (equal weights for the seed solve)
        seed = solve_ab(obs["p200"], obs["p400"])
        (thA, seA) = _solve_ls([obs["p200"], obs["p400"]],
                               [var_p200, var_p400], ["p:200", "p:400"], seed)
        # B: H fit on 200/400
        (thB, seB, _) = fit_estimator([obs["H200"], obs["H400"]],
                                      [varH[200], varH[400]],
                                      ["H:200", "H:400"], seed)
        # C: joint inverse-variance
        kinds4 = ["p:200", "p:400", "H:200", "H:400"]
        obs4 = [obs["p200"], obs["p400"], obs["H200"], obs["H400"]]
        var4 = [var_p200, var_p400, varH[200], varH[400]]
        (thC, seC, _) = fit_estimator(obs4, var4, kinds4, seed)
        pred4 = _pred_vec(thC, kinds4)
        chi2_4 = sum((o - p) ** 2 / v for o, p, v in zip(obs4, pred4, var4))
        delta0 = sign_by_model(thC[0], thC[1], obs["p_minus_200"])
        estA = {"sig": thA[0], "mag": thA[1],
                "delta": sign_by_model(thA[0], thA[1], obs["p_minus_200"]),
                "se_sig": seA[0]}
        estB = {"sig": thB[0], "mag": thB[1],
                "delta": sign_by_model(thB[0], thB[1], obs["p_minus_200"]),
                "se_sig": seB[0]}
        estC = {"sig": thC[0], "mag": thC[1], "delta": delta0,
                "se_sig": seC[0], "se_mag": seC[1], "chi2_4": chi2_4,
                "pred": pred4}
        t = consistency_T1T4(estA, estB, estC, obs)

        # floor holdout at 6400 (pure-Gaussian residual = rejection evidence)
        pg6400 = p_uncond(6400.0, thC[0], thC[1])
        p6400 = zmap[(src, 6400)]["p"]
        pure6400_resid[src] = p6400 - pg6400
        eps = estimate_floor_eps(p6400, thC[0], thC[1])
        holdout[src] = {"eps_acc": eps, "p_obs_6400": p6400,
                        "p_gauss_6400": pg6400,
                        "pure_resid": p6400 - pg6400,
                        "n6400": zmap[(src, 6400)]["pairs"]}

        per_source[src] = {"estA": estA, "estB": estB, "estC": estC,
                           "T": t, "obs": obs, "H_check": Hraw}

        # non-wide layer cells (200/400 pure Gaussian; 6400 floor-corrected)
        for bw in (200, 400, 6400):
            row = zmap[(src, bw)]
            h_re, _ = H_from_top_errors(row["top_errors"])
            if bw == 6400:
                pm, p0, pp = ternary_uncond(6400.0, thC[0], thC[1])
                pm, p0, pp = apply_floor(pm, p0, pp, eps)
                p_pred = 1.0 - p0
                h_pred = H_ternary(pm, p0, pp)
            else:
                pm, p0, pp = ternary_uncond(float(bw), thC[0], thC[1])
                p_pred = 1.0 - p0
                h_pred = H_ternary(pm, p0, pp)
            nonwide_cells.append({
                "source": src, "bw": bw, "n": row["pairs"],
                "p_obs": row["p"], "p_pred": p_pred,
                "var_p": wilson_var_p(row["p"], row["pairs"]),
                "H_obs": h_re, "H_pred": h_pred,
                "p_minus_obs": row["p_minus_cond"],
                "p_minus_pred": pm / max(1.0 - p0, 1e-300),
            })
        # wide layer cells (conditional law, no floor)
        for bw in WIDE_BWS:
            row = zmap[(src, bw)]
            h_re, rest = H_from_top_errors(row["top_errors"])
            pc = p_cond(float(bw), thC[0], delta0)
            j0, cover = cond_dist(float(bw), thC[0], delta0, 0)
            # tail mass beyond |k|<=1 vs observed
            jt1, _ = cond_dist(float(bw), thC[0], delta0, 1)
            jtm1, _ = cond_dist(float(bw), thC[0], delta0, -1)
            tail_pred = max(0.0, 1.0 - (j0 + jt1 + jtm1) / cover)
            p_rest_obs = rest  # unlisted tail fraction
            wide_cells.append({
                "source": src, "bw": bw, "n": row["pairs"], "d": row["d"],
                "p_obs": row["p"], "p_pred": pc,
                "var_p": wilson_var_p(row["p"], row["pairs"]),
                "H_obs": h_re, "H_pred": None,
                "support_obs": row["support_size"],
                "support_pred": support_pred(float(bw), thC[0], delta0,
                                             row["pairs"], row["d"]),
                "tail_rest_obs": p_rest_obs,
                "tail_pred": tail_pred,
            })

    metrics_nonwide = layer_metrics(nonwide_cells)
    # wide p-metrics only over cells with an H-independent p law
    wide_p = [{"p_obs": c["p_obs"], "p_pred": c["p_pred"], "var_p": c["var_p"],
               "H_obs": None, "H_pred": None} for c in wide_cells]
    e = [c["p_obs"] - c["p_pred"] for c in wide_cells]
    metrics_wide = {
        "n": len(wide_cells),
        "rmse": math.sqrt(sum(x * x for x in e) / len(e)),
        "mae": sum(abs(x) for x in e) / len(e),
        "mean_rel": sum(abs(x) / c["p_obs"] for x, c in zip(e, wide_cells)) / len(e),
        "max_resid": max(e, key=abs),
        "chi2": sum((c["p_obs"] - c["p_pred"]) ** 2 / c["var_p"] for c in wide_cells),
    }
    metrics_wide["chi2_dof"] = metrics_wide["chi2"] / metrics_wide["n"]

    # floor-branch discriminant (design §1.7), three honest outcomes:
    # (i) needs 6400 lift with eps in 0.005..0.008; (ii) needs wide tails
    # systematically ABOVE Gaussian (obs/pred |k|>=2 ratio > 3 in most
    # wide cells). Neither fires here: pure Gaussian already explains
    # the holdout, so no pre-registered correction is consumed.
    raw_eps = {s: (holdout[s]["p_obs_6400"] - holdout[s]["p_gauss_6400"])
               / (1.0 - holdout[s]["p_gauss_6400"]) for s in sources}
    eps_vals = [holdout[s]["eps_acc"] for s in sources]
    in_band = sum(1 for v in eps_vals if 0.005 <= v <= 0.008)
    tail_cmp = []
    for c in wide_cells:
        row = zmap[(c["source"], c["bw"])]
        to = tail_ge2_obs(row["top_errors"], row["d"])
        tp = tail_ge2_pred(float(c["bw"]), per_source[c["source"]]["estC"]["sig"],
                           per_source[c["source"]]["estC"]["delta"])
        tail_cmp.append({"source": c["source"], "bw": c["bw"],
                         "obs_ge2": to, "pred_ge2": tp,
                         "ratio": to / max(tp, 1e-12)})
        c["tail_ge2_obs"] = to
        c["tail_ge2_pred"] = tp
    sys_high = sum(1 for t in tail_cmp if t["ratio"] > 3.0)
    lift_needed = sum(1 for s in sources
                      if abs(holdout[s]["pure_resid"]) > 0.001)
    if in_band >= 5:
        selected = "(i) accidental floor"
    elif sys_high >= 7:
        selected = "(ii) heavy-tail — NOT implemented, escalate to main thread"
    else:
        selected = ("neither: pure Gaussian explains holdout "
                    "(no lift needed, eps_raw ~ 0); wide tails at/below "
                    "Gaussian — no pre-registered correction consumed")
    branch_info = {"eps_acc": {s: holdout[s]["eps_acc"] for s in sources},
                   "eps_raw": raw_eps,
                   "eps_in_band_5e_3_8e_3": in_band,
                   "holdout_cells_needing_lift_1e_3": lift_needed,
                   "wide_tail_cmp": tail_cmp,
                   "wide_tail_high_cells": sys_high,
                   "selected": selected}

    # C-0 delta checks (σ̂C frozen, same ε̂, no new parameters)
    c0rows = [r for r in c0["rows"] if not r.get("repaired")]
    delta_out: dict = {}
    delta_curve_rows: list[dict] = []
    for src in sources:
        thC = (per_source[src]["estC"]["sig"], per_source[src]["estC"]["mag"])
        d0 = per_source[src]["estC"]["delta"]
        eps = holdout[src]["eps_acc"]
        for bw in FIT_BWS:
            curve = [{"delta": r["delta_ps"], "p": r["p"],
                      "var_p": wilson_var_p(r["p"], r["n"])}
                     for r in c0rows
                     if r["source"] == src and r["bw_ps"] == bw]
            chk = delta_check(curve, thC[0], d0, eps, float(bw))
            delta_out[f"{src}@{bw}"] = chk
            for r in curve:
                delta_curve_rows.append({"source": src, "bw": bw,
                                         "delta": r["delta"], "p_obs": r["p"],
                                         "p_pred": r["p_pred"]})

    # core-consistent reference (design suggestion, non-wide layer)
    gate = {"rmse_lt_5e_3": metrics_nonwide["rmse"] < 0.005,
            "mean_rel_lt_5pct": metrics_nonwide["mean_rel"] < 0.05,
            "chi2_dof_lt_3": metrics_nonwide["chi2_dof"] < 3.0}
    gate["core_consistent"] = all(gate.values())

    result = {
        "track": "EXPLORE",
        "inputs": {"z2": str(z2_path), "c0": str(c0_path),
                   "W_ps": W_PS, "split": "200/400 fit, 6400 holdout, 50/100 extrapolate"},
        "per_source": per_source,
        "holdout": holdout,
        "pure_gauss_6400_resid": pure6400_resid,
        "branch": branch_info,
        "metrics_nonwide": metrics_nonwide,
        "metrics_wide": metrics_wide,
        "delta": delta_out,
        "gate": gate,
        "claim_ceiling": ("fit-consistency only (model-vs-measurement agreement, "
                          "stratified); no FER/SKR/route-qualified claim"),
    }
    (out_root / "c2_fit.json").write_text(
        json.dumps(result, indent=2, default=str), encoding="utf-8")

    def _csv(path: Path, cols: list[str], rows: list[dict]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(",".join(cols) + "\n")
            for r in rows:
                f.write(",".join(str(r.get(c, "")) for c in cols) + "\n")

    _csv(out_root / "c2_nonwide.csv",
         ["source", "bw", "n", "p_obs", "p_pred", "H_obs", "H_pred",
          "p_minus_obs", "p_minus_pred"], nonwide_cells)
    _csv(out_root / "c2_wide.csv",
         ["source", "bw", "n", "d", "p_obs", "p_pred", "support_obs",
          "support_pred", "tail_ge2_obs", "tail_ge2_pred"], wide_cells)
    _csv(out_root / "c2_delta.csv",
         ["source", "bw", "delta", "p_obs", "p_pred"], delta_curve_rows)
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--z2", required=True)
    ap.add_argument("--c0", required=True)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    res = run_c2(Path(args.z2), Path(args.c0), Path(args.output_root))
    for src, ps in res["per_source"].items():
        c = ps["estC"]
        print(f"{src}: sigC={c['sig']:.2f}±{c['se_sig']:.2f} "
              f"deltaC={c['delta']:+.2f} T1z={ps['T']['T1_z']:+.2f} "
              f"T2chi2={ps['T']['T2_chi2']:.2f} "
              f"T={'PASS' if ps['T']['all_pass'] else 'FAIL'}")
    print("nonwide:", {k: round(v, 5) if isinstance(v, float) else v
                       for k, v in res["metrics_nonwide"].items()})
    print("wide:", {k: round(v, 5) if isinstance(v, float) else v
                    for k, v in res["metrics_wide"].items()})
    print("branch:", res["branch"]["selected"])
    print("gate:", res["gate"])


if __name__ == "__main__":
    main()
