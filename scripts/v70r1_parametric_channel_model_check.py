#!/usr/bin/env python
"""
V70R1 parametric channel model check (decoder-free).

M0 hierarchical 1024x1024 table (V70 authority) vs M1 circulant empirical kernel
vs M2 wrapped Gaussian/Laplace + uniform background, on the SAME V70 Stage2
CAL1024/VAL256 frames.  Reports VAL cross-entropy, MAP accuracy, Fano upper-bound
diagnostic, CAL->VAL NLL gap, required bits, parameter count and the 32..1024
frame sample-requirement curve.  No decoder, no business matrix, no run_01.

Explicit non-claim: CE is the observed VAL cross-entropy of each model.  This
script does NOT separate a "true" H(A|B) from a model KL term; the Fano value is
reported as an upper-bound diagnostic only, and cross-model CE differences are
reported as differences, not as a decomposition.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

Q = 1024
N_BLOCK = 1024
COLS = 10240                 # 10 bits x 1024 symbols, V70 budget
TAG_BITS = 64
TARGET_F_PLANNING = 1.3      # planning factor ONLY; never an achieved efficiency
LAMBDA_GRID = [10 ** x for x in np.linspace(-2, 4, 30)]
FOLDS = 4

# M2 deterministic pre-registered fit grids (frozen, not tuned on VAL)
MU_GRID = np.round(np.arange(-4.0, 4.0 + 1e-9, 0.25), 6)
SCALE_GRID = np.logspace(math.log10(0.05), math.log10(8.0), 40)
EPS_GRID = np.linspace(0.0, 0.999, 200)
M2_FAMILIES = ("gaussian", "laplace")

# terminals, first-match mutually exclusive (5-terminal: REDUCES_VAL_CE = route==False && delta>=0.10)
TERMINALS = (
    "V70R1_EVIDENCE_INVALID",
    "V70R1_TRANSLATION_INVARIANCE_REJECTED",
    "V70R1_PARAMETRIC_MODEL_CHANGES_CAPACITY_ROUTE",
    "V70R1_PARAMETRIC_MODEL_REDUCES_VAL_CE",
    "V70R1_PARAMETRIC_MODEL_NO_VALUE",
)
CE_VALUE_THRESHOLD = 0.10        # bits/symbol, "no value" ceiling
CE_REJECT_MARGIN = 0.05          # bits/symbol worse than table -> invariance rejected
COST_SMALL_FRAMES = 64           # sample-cost probe point
COST_MODEL_TOL = 0.10            # parametric drift allowed at probe point
COST_TABLE_MIN = 0.50            # table drift required at probe point


# --------------------------------------------------------------------------
# shared helpers (M0 estimator is byte-identical to V70)
# --------------------------------------------------------------------------
def hierarchical_P(C_ab, P_global, N_b, lam):
    P = (C_ab.astype(np.float64) + lam * P_global[None, :]) / (N_b[:, None] + lam)
    zero = N_b == 0
    if np.any(zero):
        P[zero] = P_global
    return P


def _fold_bounds(n, folds=FOLDS):
    step = n // folds
    return [(k * step, (k + 1) * step if k < folds - 1 else n) for k in range(folds)]


def fit_table(a_tr, b_tr, lam):
    C = np.zeros((Q, Q), dtype=np.int32)
    np.add.at(C, (b_tr, a_tr), 1)
    N_b = C.sum(axis=1).astype(np.float64)
    P_global = C.sum(axis=0).astype(np.float64) / len(a_tr) if len(a_tr) else np.ones(Q) / Q
    return hierarchical_P(C, P_global, N_b, lam)


def select_lambda_table(a_cal, b_cal):
    """V70-identical CAL-only 4-fold CV over LAMBDA_GRID."""
    n = len(a_cal)
    best_lam, best_ce, per = None, float("inf"), {}
    for lam in LAMBDA_GRID:
        ces = []
        for lo, hi in _fold_bounds(n):
            mask = np.ones(n, dtype=bool)
            mask[lo:hi] = False
            Ps = fit_table(a_cal[mask], b_cal[mask], lam)
            p = np.maximum(Ps[b_cal[lo:hi], a_cal[lo:hi]], 1e-300)
            ces.append(float(-np.log2(p).mean()))
        avg = float(np.mean(ces))
        per[float(lam)] = avg
        if avg < best_ce:
            best_ce, best_lam = avg, lam
    at_boundary = bool(best_lam <= 1e-2 + 1e-12 or best_lam >= 1e4 - 1e-9)
    return best_lam, best_ce, per, at_boundary


def delta_hist(a, b):
    """circular displacement histogram, the only statistic M1/M2 consume."""
    return np.bincount((a.astype(np.int64) - b.astype(np.int64)) % Q, minlength=Q).astype(np.float64)


def signed_disp():
    d = np.arange(Q)
    return ((d + Q // 2) % Q) - Q // 2


SIGNED = signed_disp().astype(np.float64)


# --------------------------------------------------------------------------
# M1 circulant empirical kernel: P(a|b) = K[(a-b) mod Q], 1024 params
# --------------------------------------------------------------------------
def fit_circulant(hist, lam_K):
    n = float(hist.sum())
    K = (hist + lam_K / Q) / (n + lam_K)
    return K / K.sum()


def select_lambda_circulant(a_cal, b_cal):
    n = len(a_cal)
    best_lam, best_ce, per = None, float("inf"), {}
    for lam in LAMBDA_GRID:
        ces = []
        for lo, hi in _fold_bounds(n):
            mask = np.ones(n, dtype=bool)
            mask[lo:hi] = False
            K = fit_circulant(delta_hist(a_cal[mask], b_cal[mask]), lam)
            ces.append(ce_from_kernel(K, delta_hist(a_cal[lo:hi], b_cal[lo:hi])))
        avg = float(np.mean(ces))
        per[float(lam)] = avg
        if avg < best_ce:
            best_ce, best_lam = avg, lam
    at_boundary = bool(best_lam <= 1e-2 + 1e-12 or best_lam >= 1e4 - 1e-9)
    return best_lam, best_ce, per, at_boundary


def ce_from_kernel(K, hist_eval):
    """CE in bits/symbol for a shift-invariant kernel, evaluated from a histogram."""
    n = float(hist_eval.sum())
    if n <= 0:
        return float("inf")
    return float(-(hist_eval * np.log2(np.maximum(K, 1e-300))).sum() / n)


# --------------------------------------------------------------------------
# M2 wrapped Gaussian / Laplace + uniform background: 3 params
# --------------------------------------------------------------------------
def m2_shape(family, mu, scale):
    """wrapped unimodal shape over the Q circular displacements, normalized."""
    w = np.zeros(Q, dtype=np.float64)
    for period in (-1, 0, 1):                     # wrap-around contributions
        z = SIGNED + period * Q - mu
        if family == "gaussian":
            w += np.exp(-0.5 * (z / scale) ** 2)
        else:
            w += np.exp(-np.abs(z) / scale)
    s = w.sum()
    return w / s if s > 0 else np.full(Q, 1.0 / Q)


def m2_nll_over_eps(shape, hist):
    """vectorized CE over EPS_GRID for one fixed shape; returns (ce_grid,)."""
    n = float(hist.sum())
    P = (1.0 - EPS_GRID)[:, None] * shape[None, :] + (EPS_GRID / Q)[:, None]
    return -(hist[None, :] * np.log2(np.maximum(P, 1e-300))).sum(axis=1) / n


def fit_m2(hist, family):
    """deterministic grid fit of (mu, scale, eps) on one CAL histogram."""
    best = (float("inf"), 0.0, SCALE_GRID[0], 0.0)
    for mu in MU_GRID:
        for scale in SCALE_GRID:
            shape = m2_shape(family, float(mu), float(scale))
            ce_grid = m2_nll_over_eps(shape, hist)
            j = int(np.argmin(ce_grid))
            if ce_grid[j] < best[0]:
                best = (float(ce_grid[j]), float(mu), float(scale), float(EPS_GRID[j]))
    _, mu, scale, eps = best
    return {"family": family, "mu": mu, "scale": scale, "eps": eps}


def m2_kernel(params):
    shape = m2_shape(params["family"], params["mu"], params["scale"])
    K = (1.0 - params["eps"]) * shape + params["eps"] / Q
    return K / K.sum()


def select_m2_family(a_cal, b_cal):
    """CAL-only 4-fold CV between the two pre-registered families. VAL untouched."""
    n = len(a_cal)
    per = {}
    for family in M2_FAMILIES:
        ces = []
        for lo, hi in _fold_bounds(n):
            mask = np.ones(n, dtype=bool)
            mask[lo:hi] = False
            p = fit_m2(delta_hist(a_cal[mask], b_cal[mask]), family)
            ces.append(ce_from_kernel(m2_kernel(p), delta_hist(a_cal[lo:hi], b_cal[lo:hi])))
        per[family] = float(np.mean(ces))
    best = min(per, key=per.get)
    return best, per


# --------------------------------------------------------------------------
# diagnostics
# --------------------------------------------------------------------------
def map_accuracy_table(Ps, a_eval, b_eval):
    a_hat = np.argmax(Ps, axis=1)[b_eval]
    return float(np.mean(a_hat == a_eval))


def map_accuracy_kernel(K, hist_eval):
    n = float(hist_eval.sum())
    return float(hist_eval[int(np.argmax(K))] / n) if n > 0 else 0.0


def fano_upper_bound(acc):
    """H(A|B) <= h2(Pe) + Pe*log2(Q-1). Upper-bound DIAGNOSTIC only."""
    pe = 1.0 - acc
    if pe <= 0.0:
        return 0.0
    if pe >= 1.0:
        return float(math.log2(Q))
    h2 = -(pe * math.log2(pe) + (1 - pe) * math.log2(1 - pe))
    return float(h2 + pe * math.log2(Q - 1))


def required_bits(ce_val):
    if not math.isfinite(ce_val):
        return 0
    return int(math.ceil(TARGET_F_PLANNING * N_BLOCK * ce_val))


def f_max_from_ce(ce_val):
    """channel ceiling implied by the 10240-bit budget; independent of the planning f."""
    if not math.isfinite(ce_val) or ce_val <= 0:
        return float("inf")
    return float((COLS - TAG_BITS) / (N_BLOCK * ce_val))


def classify_budget(required):
    """V70 first-match budget classification, reused verbatim for route comparison."""
    if required >= COLS:
        return "NO_INFORMATION_MARGIN"
    gap = COLS - required
    if gap < 0:
        return "HEAVY"
    return "FEASIBLE" if gap >= 512 else "MARGINAL"


# --------------------------------------------------------------------------
# per-session evaluation
# --------------------------------------------------------------------------
def load_frames(pairs_path, frame_ids):
    df = pd.read_parquet(pairs_path, columns=["frame_id", "pair_idx", "alice_symbol", "bob_symbol"])
    fids = set(int(x) for x in frame_ids)
    sub = df[df.frame_id.isin(fids)].sort_values(["frame_id", "pair_idx"])
    g = sub.groupby("frame_id").size()
    assert len(g) == len(fids), "missing frames"
    assert (g == 256).all(), "frame not 256 pairs"
    a = sub["alice_symbol"].to_numpy(dtype=np.int32)
    b = sub["bob_symbol"].to_numpy(dtype=np.int32)
    assert int(a.min()) >= 0 and int(a.max()) <= 1023
    assert int(b.min()) >= 0 and int(b.max()) <= 1023
    return a, b


def sample_curve(a_cal, b_cal, a_val, b_val, lam_tab, lam_K, m2_family,
                 points=(32, 64, 128, 256, 512, 1024)):
    """CAL prefix (in frames) -> VAL CE for each model. Same VAL throughout."""
    hist_val = delta_hist(a_val, b_val)
    out = {}
    for f in points:
        k = f * 256
        if k > len(a_cal):
            continue
        a_s, b_s = a_cal[:k], b_cal[:k]
        h_s = delta_hist(a_s, b_s)
        Ps = fit_table(a_s, b_s, lam_tab)
        p = np.maximum(Ps[b_val, a_val], 1e-300)
        out[str(f)] = {
            "frames": f,
            "pairs": k,
            "CE_table_VAL": float(-np.log2(p).mean()),
            "CE_circulant_VAL": ce_from_kernel(fit_circulant(h_s, lam_K), hist_val),
            "CE_parametric_VAL": ce_from_kernel(m2_kernel(fit_m2(h_s, m2_family)), hist_val),
        }
    return out


def evaluate_session(sess, v70_ref):
    sid = sess["session_id"]
    a_cal, b_cal = load_frames(Path(sess["provenance"]), sess["stage2_CAL_frame_ids"])
    a_val, b_val = load_frames(Path(sess["provenance"]), sess["stage2_VAL_frame_ids"])
    assert len(a_cal) == 262144 and len(a_val) == 65536, "V70 Stage2 split mismatch"

    hist_cal = delta_hist(a_cal, b_cal)
    hist_val = delta_hist(a_val, b_val)

    # ---- CAL-only model selection (VAL never consulted) --------------------
    lam_tab, ce_cv_tab, _, lam_tab_boundary = select_lambda_table(a_cal, b_cal)
    lam_K, ce_cv_circ, _, lam_K_boundary = select_lambda_circulant(a_cal, b_cal)
    m2_family, m2_cv = select_m2_family(a_cal, b_cal)
    m2_params = fit_m2(hist_cal, m2_family)

    # ---- fit on full CAL, confirm once on VAL ------------------------------
    Ps = fit_table(a_cal, b_cal, lam_tab)
    K1 = fit_circulant(hist_cal, lam_K)
    K2 = m2_kernel(m2_params)

    p_val = np.maximum(Ps[b_val, a_val], 1e-300)
    p_cal = np.maximum(Ps[b_cal, a_cal], 1e-300)
    ce = {
        "table": float(-np.log2(p_val).mean()),
        "circulant": ce_from_kernel(K1, hist_val),
        "parametric": ce_from_kernel(K2, hist_val),
    }
    ce_cal = {
        "table": float(-np.log2(p_cal).mean()),
        "circulant": ce_from_kernel(K1, hist_cal),
        "parametric": ce_from_kernel(K2, hist_cal),
    }
    acc = {
        "table": map_accuracy_table(Ps, a_val, b_val),
        "circulant": map_accuracy_kernel(K1, hist_val),
        "parametric": map_accuracy_kernel(K2, hist_val),
    }

    # ---- V70 authority reproduction guard ---------------------------------
    ref_ce = v70_ref.get(sid)
    repro_delta = abs(ce["table"] - ref_ce) if ref_ce is not None else float("inf")
    m0_reproduces_v70 = bool(ref_ce is not None and repro_delta < 1e-9)

    models = {}
    for name in ("table", "circulant", "parametric"):
        req = required_bits(ce[name])
        models[name] = {
            "CE_VAL": ce[name],
            "CE_CAL": ce_cal[name],
            "cal_val_nll_gap": float(ce[name] - ce_cal[name]),
            "map_accuracy_VAL": acc[name],
            "fano_upper_bound_diagnostic": fano_upper_bound(acc[name]),
            "required": req,
            "gap": COLS - req,
            "margin_gap": (COLS - req) / COLS,
            "f_max_channel_ceiling": f_max_from_ce(ce[name]),
            "classification": classify_budget(req),
            "n_parameters": {"table": Q * Q + 1, "circulant": Q + 1, "parametric": 4}[name],
        }

    best_param = min(("circulant", "parametric"), key=lambda m: ce[m])
    delta_ce = float(ce["table"] - ce[best_param])
    curve = sample_curve(a_cal, b_cal, a_val, b_val, lam_tab, lam_K, m2_family)

    # ---- estimation-cost evidence at the probe point ----------------------
    probe = curve.get(str(COST_SMALL_FRAMES))
    full = curve.get("1024")
    cost_win = False
    drift = {}
    if probe and full:
        drift = {
            "table": abs(probe["CE_table_VAL"] - full["CE_table_VAL"]),
            "circulant": abs(probe["CE_circulant_VAL"] - full["CE_circulant_VAL"]),
            "parametric": abs(probe["CE_parametric_VAL"] - full["CE_parametric_VAL"]),
        }
        cost_win = bool(drift[best_param] <= COST_MODEL_TOL and drift["table"] >= COST_TABLE_MIN)

    route_change = bool(models[best_param]["classification"] != models["table"]["classification"])
    invariance_rejected = bool(
        ce["circulant"] > ce["table"] + CE_REJECT_MARGIN
        and ce["parametric"] > ce["table"] + CE_REJECT_MARGIN
    )
    evidence_invalid = bool(
        not m0_reproduces_v70
        or not all(math.isfinite(v) for v in ce.values())
        or lam_tab_boundary
        or lam_K_boundary
    )

    # first-match, mutually exclusive (5-terminal; cost_win descriptive-only, not a terminal)
    if evidence_invalid:
        terminal = "V70R1_EVIDENCE_INVALID"
    elif invariance_rejected:
        terminal = "V70R1_TRANSLATION_INVARIANCE_REJECTED"
    elif route_change:
        terminal = "V70R1_PARAMETRIC_MODEL_CHANGES_CAPACITY_ROUTE"
    elif (not route_change) and delta_ce >= CE_VALUE_THRESHOLD:
        terminal = "V70R1_PARAMETRIC_MODEL_REDUCES_VAL_CE"
    else:
        terminal = "V70R1_PARAMETRIC_MODEL_NO_VALUE"

    return {
        "session_id": sid,
        "source_label": sess["source_label"],
        "provenance": sess["provenance"],
        "CAL_frames": len(sess["stage2_CAL_frame_ids"]),
        "VAL_frames": len(sess["stage2_VAL_frame_ids"]),
        "selection": {
            "lambda_table": float(lam_tab), "lambda_table_at_boundary": lam_tab_boundary,
            "lambda_circulant": float(lam_K), "lambda_circulant_at_boundary": lam_K_boundary,
            "m2_family_selected": m2_family, "m2_family_cv": m2_cv, "m2_params": m2_params,
            "cv_CE_table": ce_cv_tab, "cv_CE_circulant": ce_cv_circ,
            "used_val_in_selection": False, "used_test": False,
        },
        "delta_mass": {
            "mass_0": float(hist_val[0] / hist_val.sum()),
            "mass_p1": float(hist_val[1] / hist_val.sum()),
            "mass_m1": float(hist_val[Q - 1] / hist_val.sum()),
            "other": float(1.0 - (hist_val[0] + hist_val[1] + hist_val[Q - 1]) / hist_val.sum()),
        },
        "models": models,
        "v70_reproduction": {
            "v70_CE_full_VAL": ref_ce, "recomputed": ce["table"],
            "abs_delta": repro_delta, "reproduces": m0_reproduces_v70,
        },
        "best_parametric": best_param,
        "delta_CE_table_minus_best": delta_ce,
        "delta_CE_exceeds_value_threshold": bool(delta_ce >= CE_VALUE_THRESHOLD),
        "sample_curve": curve,
        "small_sample_drift": drift,
        "estimation_cost_win": cost_win,
        "capacity_route_change": route_change,
        "terminal": terminal,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default="v70_data_registry.json")
    ap.add_argument("--v70-table", default="v70_table.json")
    ap.add_argument("--out", default="v70r1_results.json")
    ap.add_argument("--table-csv", default="v70r1_table.csv")
    ap.add_argument("--table-json", default="v70r1_table.json")
    args = ap.parse_args()

    reg = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    v70_ref = {}
    p70 = Path(args.v70_table)
    if p70.exists():
        for row in json.loads(p70.read_text(encoding="utf-8")):
            v70_ref[row["session_id"]] = float(row["CE_full_VAL"])

    per_session = [evaluate_session(s, v70_ref) for s in reg["sessions"]]

    counts = {t: 0 for t in TERMINALS}
    for r in per_session:
        counts[r["terminal"]] += 1
    overall = next(t for t in TERMINALS if counts[t] > 0) if per_session else "V70R1_EVIDENCE_INVALID"

    results = {
        "schema": "V70R1_parametric_channel_model_check_v1",
        "lifecycle": "PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED",
        "V72_not_started": True,
        "no_run_01": True,
        "target_f_planning": TARGET_F_PLANNING,
        "planning_f_is_not_achieved_f": True,
        "ce_decomposition_claimed": False,
        "models_preregistered": ["M0_table", "M1_circulant", "M2_wrapped_gaussian_or_laplace"],
        "cal_val_split_reused_from": "v70_data_registry.json stage2_CAL/VAL_frame_ids",
        "used_val_in_selection": False,
        "used_test": False,
        "per_session": per_session,
        "terminal_counts": counts,
        "overall": overall,
    }
    Path(args.out).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    rows = []
    for r in per_session:
        row = {
            "session_id": r["session_id"], "source_label": r["source_label"],
            "mass_0_VAL": r["delta_mass"]["mass_0"],
            "best_parametric": r["best_parametric"],
            "delta_CE": r["delta_CE_table_minus_best"],
            "capacity_route_change": r["capacity_route_change"],
            "estimation_cost_win": r["estimation_cost_win"],
            "terminal": r["terminal"],
        }
        for name, m in r["models"].items():
            row[f"CE_{name}_VAL"] = m["CE_VAL"]
            row[f"acc_{name}"] = m["map_accuracy_VAL"]
            row[f"fano_{name}"] = m["fano_upper_bound_diagnostic"]
            row[f"required_{name}"] = m["required"]
            row[f"gap_{name}"] = m["gap"]
            row[f"class_{name}"] = m["classification"]
            row[f"params_{name}"] = m["n_parameters"]
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(args.table_csv, index=False)
    Path(args.table_json).write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"overall: {overall}")
    for r in per_session:
        m = r["models"]
        print(f"  {r['source_label']:5s} CE table {m['table']['CE_VAL']:.4f} "
              f"circ {m['circulant']['CE_VAL']:.4f} param {m['parametric']['CE_VAL']:.4f} "
              f"| dCE {r['delta_CE_table_minus_best']:+.4f} "
              f"| req {m['table']['required']}->{m[r['best_parametric']]['required']} "
              f"| {m['table']['classification']}->{m[r['best_parametric']]['classification']} "
              f"| {r['terminal']}")


if __name__ == "__main__":
    main()
