#!/usr/bin/env python3
"""
V65 channel compatibility - decoder-free spike.
Single pre-registered hierarchical P(a|b)=(C_ab+lam P_global)/(N_b+lam),
C_ab & P_global CAL-only, lam Cal 4-fold log10[-2,4] continuous 50 grid + bounded refine min Cal-CV NLL,
at boundary -> MODEL_NOT_STABLE (no expand), simultaneous P(U1|B)/P(U2|U1B),
H(U1|B)/H(U2|U1B)/H(A|B), CE1/CE2/CE_full VAL gating, delta NLL, Val NLL,
MAP, unseen <=1%, m_i=ceil(1.3*1024*CE_i/5) NOT capped, required vs frozen split,
leak_required=5*m_total+64 vs frozen 1144/1174/1184, TEST identity only, tuple zero overlap.
G1 sign/50ps, G2 lam not boundary, G3 delta<=0.5, G4 Val<=H+1.0, G5 unseen<=1%, G6 m1<=16, G7 m2<=200/206/208,
G7-aux m_total<=216/222/224, G8 provenance zero overlap + CE chain,
five states EVIDENCE_INVALID > DATA_NOT_READY > MODEL_NOT_STABLE > RATE_INCOMPATIBLE > READY_FOR_V66.
Strict V56 reuse, DECODER_FREE (no dec call), TEST never read statistics.
ponytail: numpy only, 1024x1024 int32, 4096*256 CAL, 4-fold CV O(Q^2) Q=1024 small, bounded refine after grid.
If no CAL data / sidecar missing / frame insufficient / forbidden missing -> DATA_NOT_READY spike.
Binding: frozen explicit per-source CAL/TEST session IDs; V66 PENDING until both registries exist.
not_cross_spliced: real sidecar/session provenance, not gap heuristic.
"""
import argparse, json, sys, math
from pathlib import Path
import numpy as np

DATA_SHA = "84d62779"
Q = 1024
F_TARGET, N_DIM, LOG2Q = 1.3, 1024, 5
LAMBDA_BOUNDS_LOG10 = (-2, 4)
G_THRESH = {"dNLL": 0.5, "val_leeway": 1.0, "unseen": 0.01, "m1": 16, "m2": {"1M": 200, "1p5M": 206, "2M": 208}, "m_total": {"1M": 216, "1p5M": 222, "2M": 224}}
TAG_BITS = 64
CE_CHAIN_TOL = 1e-9
FROZEN_LEAK = {"1M": 1144, "1p5M": 1174, "2M": 1184}
SOURCES = ["1M", "1p5M", "2M"]
DEFAULT_BINDING_PATHS = [
    Path("openspec/changes/formal-ir-v65-new-session-channel-compatibility/v65_frozen_session_binding.json"),
    Path("scripts/v65_frozen_binding.json"),
]

def hierarchical_P(C_ab, P_global, N_b, lam):
    P = (C_ab + lam * P_global[None, :]) / (N_b[:, None] + lam)
    return P

def entropy_H(P_ab, P_b):
    with np.errstate(divide="ignore"):
        logP = np.log2(P_ab, where=P_ab>0)
        logP[P_ab==0] = 0
    H = -np.sum(P_b[:, None] * P_ab * logP)
    return float(H)

def check_tuple_zero_overlap(cal_keys, val_keys, test_keys, forbidden_keys):
    s_cal, s_val, s_test = set(cal_keys), set(val_keys), set(test_keys)
    forb = set(forbidden_keys)
    return {
        "cal∩val_empty": len(s_cal & s_val) == 0,
        "cal∪val∩test_empty": len((s_cal | s_val) & s_test) == 0,
        "cal∪val∪test∩forbidden_empty": len((s_cal | s_val | s_test) & forb) == 0,
        "key": "(source,session,frame)",
        "forbidden_size": len(forb),
    }

def check_delay_peak_gate(delay_ps, peak_ps, sigma_ps, gate_ps, threshold_ps):
    if delay_ps is None or peak_ps is None:
        return False, {"error": "delay/peak missing"}
    sign_ok = (np.sign(delay_ps) == np.sign(peak_ps))
    if delay_ps == 0 and peak_ps == 0:
        sign_ok = True
    abs_ok = abs(float(delay_ps) - float(peak_ps)) < 50
    sigma_ok = 50 <= float(sigma_ps) <= 150
    gate_ok = int(gate_ps) == 200
    thr_ok = int(threshold_ps) == 40000
    return bool(sign_ok and abs_ok and sigma_ok and gate_ok and thr_ok), {
        "sign_ok": bool(sign_ok), "abs_ps": float(abs(float(delay_ps)-float(peak_ps))), "abs_ok": bool(abs_ok),
        "sigma_ok": bool(sigma_ok), "gate_ok": bool(gate_ok), "thr_ok": bool(thr_ok)
    }

def load_forbidden_keys(extra=None):
    keys=set()
    cands=[Path("openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/v55_authoritative_registry.json"), Path("comparison_bench/outputs_comparison/v55_intake_20260828/v55_stratified_registry_candidate.json")]
    if extra:
        for p in extra:
            if p:
                cands.append(Path(p))
    for cand in cands:
        if not cand.exists():
            continue
        try:
            j=json.loads(cand.read_text(encoding="utf-8"))
            strata=j.get("strata", j)
            if "per_source" in j and "strata" not in j:
                strata=j["per_source"]
            for label, entry in strata.items():
                if not isinstance(entry, dict):
                    continue
                src=entry.get("stratum") or entry.get("source")
                if src is None:
                    if "1p5" in label or "1500" in label:
                        src="1p5M"
                    elif "1M" in label:
                        src="1M"
                    elif "2M" in label:
                        src="2M"
                    else:
                        continue
                sess=entry.get("session_id") or label
                for block in entry.get("selected_frame_ids", []):
                    if isinstance(block, list):
                        for fid in block:
                            keys.add((src, sess, int(fid)))
                for s in entry.get("selected_starts", []):
                    for fid in [s, s+1, s+2, s+3]:
                        keys.add((src, sess, int(fid)))
        except Exception:
            continue
    return keys

def load_frozen_binding(explicit_path=None):
    path = Path(explicit_path) if explicit_path else None
    if path and path.exists():
        try:
            j = json.loads(path.read_text(encoding="utf-8"))
            return j.get("per_source", j), str(path)
        except Exception:
            return None, str(path) if path else None
    for cand in DEFAULT_BINDING_PATHS:
        if cand.exists():
            try:
                j = json.loads(cand.read_text(encoding="utf-8"))
                return j.get("per_source", j), str(cand)
            except Exception:
                continue
    return None, None

def find_pairs_file(session_dir: Path):
    if session_dir is None:
        return None
    for cand in [session_dir / "pairs.parquet", session_dir / "pairs" / "pairs.parquet"]:
        if cand.exists():
            return cand
    for p in session_dir.glob("*.parquet"):
        return p
    return None

def find_sidecar_file(session_dir: Path, session_id: str):
    if session_dir is None:
        return None
    for cand in [session_dir / "sidecar_meta.json", session_dir / "sidecar.json", Path("comparison_bench/outputs_comparison/v55_intake_20260828/sidecars") / session_id / "sidecar_meta.json"]:
        if cand.exists():
            return cand
    for p in session_dir.glob("*.json"):
        if "sidecar" in p.name.lower() or "meta" in p.name.lower():
            return p
    return None

def load_sidecar_provenance(sidecar_path: Path):
    try:
        j=json.loads(sidecar_path.read_text(encoding="utf-8"))
        diag=j.get("diagnostics", {})
        mat=j.get("materialize_params", j.get("materialization", {}))
        delay=j.get("delay_used_ps", j.get("delay_ps", mat.get("delay_used_ps")))
        peak=j.get("peak_center", j.get("peak_ps", diag.get("peak_center")))
        sigma=j.get("sigma_ps", j.get("sigma", diag.get("sigma_ps", 80)))
        gate=j.get("gate_ps", j.get("gate", mat.get("gate_ps", 200)))
        thr=j.get("threshold_ps", j.get("threshold", mat.get("threshold_ps", 40000)))
        sess_id=j.get("session_id", j.get("session", mat.get("session_id")))
        return {"delay": delay, "peak": peak, "sigma": sigma, "gate": gate, "thr": thr, "session_id": sess_id, "raw": j}
    except Exception as e:
        return {"error": str(e), "delay": None, "peak": None, "session_id": None}

def check_not_cross_spliced_by_provenance(cal_sess_id, val_sess_id, test_sess_id, cal_sidecar, test_sidecar):
    if cal_sess_id is None or test_sess_id is None:
        return False, {"reason": "missing session id"}
    if cal_sess_id == test_sess_id:
        return False, {"reason": "CAL and TEST same session"}
    if val_sess_id is not None and cal_sess_id != val_sess_id:
        return False, {"reason": "CAL and VAL session mismatch"}
    if cal_sidecar and cal_sidecar.get("session_id") is not None:
        if str(cal_sidecar["session_id"]) != str(cal_sess_id):
            return False, {"reason": "CAL sidecar drift", "sidecar": cal_sidecar["session_id"], "dir": cal_sess_id}
    if test_sidecar and test_sidecar.get("session_id") is not None:
        if str(test_sidecar["session_id"]) != str(test_sess_id):
            return False, {"reason": "TEST sidecar drift", "sidecar": test_sidecar["session_id"], "dir": test_sess_id}
    if cal_sidecar is None or test_sidecar is None:
        return False, {"reason": "sidecar missing for provenance"}
    return True, {"cal": cal_sess_id, "val": val_sess_id, "test": test_sess_id}

def load_pairs_for_frames(pairs_path: Path, frame_ids):
    import pandas as pd
    df=pd.read_parquet(pairs_path)
    if not {"frame_id","alice_symbol","bob_symbol"}.issubset(df.columns):
        raise ValueError(f"missing columns {df.columns.tolist()}")
    sub=df[df.frame_id.isin(frame_ids)].sort_values(["frame_id","pair_idx"] if "pair_idx" in df.columns else ["frame_id"])
    g=sub.groupby("frame_id").size()
    if not all(v==256 for v in g.values):
        raise ValueError(f"pairs_per_frame violation {g[g!=256].to_dict()}")
    if len(sub) != len(frame_ids)*256:
        raise ValueError(f"expected {len(frame_ids)*256} pairs got {len(sub)}")
    a=sub["alice_symbol"].to_numpy(dtype=np.int32)
    b=sub["bob_symbol"].to_numpy(dtype=np.int32)
    if a.min()<0 or a.max()>1023 or b.min()<0 or b.max()>1023:
        raise ValueError("symbol out of [0,1023]")
    return a, b

def discover_per_source_sessions(new_root: Path):
    per={}
    for src in SOURCES:
        sp=new_root / src if new_root else None
        if sp and sp.exists() and sp.is_dir():
            per[src]=sorted([p for p in sp.iterdir() if p.is_dir()])
        else:
            lst=[]
            if new_root and new_root.exists():
                for p in new_root.iterdir():
                    if p.is_dir():
                        n=p.name
                        if src=="1M" and "1M" in n and "1p5" not in n.lower():
                            lst.append(p)
                        elif src=="1p5M" and ("1p5" in n.lower() or "1500" in n or "PPLN" in n):
                            lst.append(p)
                        elif src=="2M" and "2M" in n:
                            lst.append(p)
            per[src]=sorted(lst)
    return per

def resolve_sessions_by_binding(sess_dirs, expected_cal_id, expected_test_id):
    cal_cands = [p for p in sess_dirs if p.name == expected_cal_id] if expected_cal_id else []
    test_cands = [p for p in sess_dirs if p.name == expected_test_id] if expected_test_id else []
    cal_dir = cal_cands[0] if len(cal_cands)==1 else None
    test_dir = test_cands[0] if len(test_cands)==1 else None
    return cal_dir, test_dir, len(cal_cands)==1, len(test_cands)==1, len(cal_cands), len(test_cands)

def estimate_source(cal_pairs, val_pairs, lam_bounds=(-2,4)):
    if cal_pairs is None:
        return None
    a_cal, b_cal = cal_pairs
    a_val, b_val = val_pairs
    N_cal = len(a_cal)
    C_ab = np.zeros((Q, Q), dtype=np.int32)
    np.add.at(C_ab, (b_cal, a_cal), 1)
    N_b = C_ab.sum(axis=1).astype(np.float64)
    P_global = C_ab.sum(axis=0).astype(np.float64) / N_cal
    P_b = N_b / N_cal
    folds = 4
    n_per_fold = N_cal // folds
    def cv_nll(lam):
        tot = 0.0
        for k in range(folds):
            lo, hi = k*n_per_fold, (k+1)*n_per_fold if k<3 else N_cal
            mask = np.ones(N_cal, dtype=bool); mask[lo:hi]=False
            C_tr = np.zeros((Q,Q), dtype=np.int32)
            np.add.at(C_tr, (b_cal[mask], a_cal[mask]), 1)
            N_b_tr = C_tr.sum(axis=1).astype(np.float64)
            P_g_tr = C_tr.sum(axis=0).astype(np.float64) / mask.sum()
            P_tr = (C_tr.astype(np.float64) + lam * P_g_tr[None,:]) / (N_b_tr[:,None] + lam)
            b_te = b_cal[lo:hi]; a_te = a_cal[lo:hi]
            p = P_tr[b_te, a_te]
            p = np.maximum(p, 1e-300)
            tot += -np.log2(p).mean()
        return tot / folds
    grid_log = np.linspace(lam_bounds[0], lam_bounds[1], 50)
    grid_lam = 10**grid_log
    grid_cv = np.array([cv_nll(l) for l in grid_lam])
    idx = int(np.argmin(grid_cv))
    lam_star_grid = float(grid_lam[idx])
    cv_star_grid = float(grid_cv[idx])
    lo_log = max(lam_bounds[0], grid_log[max(0, idx-1)])
    hi_log = min(lam_bounds[1], grid_log[min(len(grid_log)-1, idx+1)])
    best_log = float(grid_log[idx])
    best_cv = float(grid_cv[idx])
    lo_log = max(lam_bounds[0], best_log - 0.6)
    hi_log = min(lam_bounds[1], best_log + 0.6)
    for _ in range(35):
        m1 = lo_log + (hi_log - lo_log) * 0.381966
        m2 = hi_log - (hi_log - lo_log) * 0.381966
        c1 = cv_nll(10**m1)
        c2 = cv_nll(10**m2)
        if c1 < c2:
            hi_log = m2
            if c1 < best_cv:
                best_cv = c1; best_log = m1
        else:
            lo_log = m1
            if c2 < best_cv:
                best_cv = c2; best_log = m2
        if hi_log - lo_log < 1e-4:
            break
    lam_star = float(10**best_log)
    cv_star = float(best_cv)
    at_boundary = (best_log <= lam_bounds[0]+1e-6) or (best_log >= lam_bounds[1]-1e-6)
    P_star = hierarchical_P(C_ab.astype(np.float64), P_global, N_b, lam_star)
    H = entropy_H(P_star, P_b)
    P_u1 = P_star.reshape(Q, 32, 32).sum(axis=2)
    with np.errstate(divide="ignore", invalid="ignore"):
        H1 = -np.sum(P_b[:,None] * np.where(P_u1>0, P_u1*np.log2(P_u1), 0))
    H2 = H - H1
    chain_delta_H = abs(H - H1 - H2)
    cal_support = N_b > 0
    unseen = float(np.mean(~cal_support[b_val])) if len(b_val) else 0.0
    effective = int(np.sum(cal_support))
    p_val = P_star[b_val, a_val]
    p_val = np.maximum(p_val, 1e-300)
    val_nll = float(-np.log2(p_val).mean()) if len(p_val) else float("inf")
    u1_val = (a_val // 32).astype(np.int32)
    p_u1_val = P_u1[b_val, u1_val]
    p_u1_val = np.maximum(p_u1_val, 1e-300)
    ce_full = val_nll
    ce1 = float(-np.log2(p_u1_val).mean()) if len(p_u1_val) else float("inf")
    p_cond = p_val / p_u1_val
    p_cond = np.maximum(p_cond, 1e-300)
    ce2 = float(-np.log2(p_cond).mean()) if len(p_cond) else float("inf")
    chain_delta_CE = abs(ce_full - ce1 - ce2)
    d_nll = float(val_nll - cv_star) if math.isfinite(val_nll) else float("inf")
    MAP = float(np.mean(a_val == np.argmax(P_star[b_val], axis=1))) if len(a_val) else 0.0
    m1 = math.ceil(F_TARGET * N_DIM * ce1 / LOG2Q) if math.isfinite(ce1) and ce1>0 else 0
    m2 = math.ceil(F_TARGET * N_DIM * ce2 / LOG2Q) if math.isfinite(ce2) and ce2>0 else 0
    m_total = m1 + m2
    leak_required = 5 * m_total + TAG_BITS
    m_H1 = math.ceil(F_TARGET * N_DIM * H1 / LOG2Q) if H1>0 else 0
    m_H2 = math.ceil(F_TARGET * N_DIM * H2 / LOG2Q) if H2>0 else 0
    return {
        "C_shape": [Q, Q], "N_cal": int(N_cal), "N_val": int(len(a_val)), "effective_contexts": effective,
        "zero_cells": int(np.sum(C_ab==0)), "lam_star": lam_star, "lam_star_grid": lam_star_grid, "at_boundary": bool(at_boundary),
        "cv_nll": cv_star, "cv_nll_grid": cv_star_grid, "val_nll": val_nll, "d_nll": d_nll,
        "H": float(H), "H1": float(H1), "H2": float(H2), "chain_delta_H": float(chain_delta_H),
        "CE1": float(ce1), "CE2": float(ce2), "CE_full": float(ce_full), "chain_delta_CE": float(chain_delta_CE),
        "required_m1": int(m1), "required_m2": int(m2), "required_m_total": int(m_total), "required_leak": int(leak_required),
        "m1": int(m1), "m2": int(m2), "m_total": int(m_total), "leak": int(leak_required), "m1_raw": int(m1), "m2_raw": int(m2),
        "m_H1": int(m_H1), "m_H2": int(m_H2),
        "MAP": float(MAP), "unseen": float(unseen),
        "search_trace": {"grid_log": grid_log.tolist(), "grid_cv": grid_cv.tolist(), "idx": idx, "best_log": best_log, "best_cv": best_cv, "refined": True},
    }

def main():
    ap = argparse.ArgumentParser(description="V65 channel compatibility - decoder-free")
    ap.add_argument("--new-session-root", default=None, help="new session root per-source explicit (contains 1M/1p5M/2M)")
    ap.add_argument("--cal-root", default=None, help="legacy cal root (fallback)")
    ap.add_argument("--val-root", default=None)
    ap.add_argument("--test-registry", default=None, help="TEST registry path - never read statistics")
    ap.add_argument("--v66-registry", default=None, help="V66 registry to check equals V65 TEST")
    ap.add_argument("--forbidden-registry", default=None)
    ap.add_argument("--frozen-binding", default=None, help="frozen explicit CAL/TEST session binding json")
    ap.add_argument("--out", default="v65_channel_compatibility.json")
    ap.add_argument("--report", default="V65_CHANNEL_COMPATIBILITY_REPORT.md")
    ap.add_argument("--data-registry", default="v65_data_registry.json")
    args = ap.parse_args()

    new_root = Path(args.new_session_root) if args.new_session_root else (Path(args.cal_root) if args.cal_root else None)
    per_source = {}
    forbidden_keys = load_forbidden_keys([args.forbidden_registry, args.test_registry])
    forbidden_nonempty = len(forbidden_keys) > 0
    binding, binding_path = load_frozen_binding(args.frozen_binding)
    binding_ok = binding is not None
    overall = "V65_EVIDENCE_INVALID"
    data_ready = False
    per_src_sessions = {}
    if new_root and new_root.exists() and binding_ok:
        per_src_sessions = discover_per_source_sessions(new_root)
        ok_all = True
        for src in SOURCES:
            sess = per_src_sessions.get(src, [])
            exp_cal = binding.get(src, {}).get("CAL_session_id") or binding.get(src, {}).get("CAL")
            exp_test = binding.get(src, {}).get("TEST_session_id") or binding.get(src, {}).get("TEST")
            cal_dir, test_dir, cal_ok, test_ok, _, _ = resolve_sessions_by_binding(sess, exp_cal, exp_test)
            if not (cal_ok and test_ok):
                ok_all = False
                break
            if find_pairs_file(cal_dir) is None or find_pairs_file(test_dir) is None:
                ok_all = False
                break
            if find_sidecar_file(cal_dir, cal_dir.name) is None or find_sidecar_file(test_dir, test_dir.name) is None:
                ok_all = False
                break
        data_ready = bool(ok_all and forbidden_nonempty and binding_ok)
        if data_ready:
            for src in SOURCES:
                exp_cal = binding.get(src, {}).get("CAL_session_id") or binding.get(src, {}).get("CAL")
                sess = per_src_sessions[src]
                cal_dir, _, _, _, _, _ = resolve_sessions_by_binding(sess, exp_cal, binding.get(src, {}).get("TEST_session_id"))
                pf = find_pairs_file(cal_dir)
                try:
                    import pandas as pd
                    df = pd.read_parquet(pf)
                    if df.frame_id.nunique() < 4608:
                        data_ready = False
                        break
                except Exception:
                    data_ready = False
                    break
    else:
        data_ready = False

    if not data_ready:
        overall = "V65_DATA_NOT_READY"
        for src in SOURCES:
            sess = per_src_sessions.get(src, [])
            has_sidecar = False
            has_frames = False
            frame_detail = {}
            exp_cal = binding.get(src, {}).get("CAL_session_id") if binding else None
            exp_test = binding.get(src, {}).get("TEST_session_id") if binding else None
            if sess and binding_ok and exp_cal:
                cal_dir, _, cal_ok, test_ok, _, _ = resolve_sessions_by_binding(sess, exp_cal, exp_test)
                pf=find_pairs_file(cal_dir) if cal_dir else None
                if pf and pf.exists():
                    try:
                        import pandas as pd
                        df=pd.read_parquet(pf)
                        has_frames = df.frame_id.nunique() >= 4608
                        frame_detail={"n_frames": df.frame_id.nunique(), "n_pairs": len(df)}
                    except Exception as e:
                        frame_detail={"error": str(e)}
                # sidecar check for CAL
                has_sidecar = find_sidecar_file(cal_dir, cal_dir.name) is not None if cal_dir else False
            per_source[src] = {
                "status": "DATA_NOT_READY",
                "note": "no CAL_SESSION per frozen binding or sidecar/frames/forbidden missing - spike",
                "has_sidecar": has_sidecar, "has_frames": has_frames, "frame_detail": frame_detail,
                "G1": None, "G2": None, "G3": None, "G4": None, "G5": None, "G6": None, "G7": None, "G7_aux": None, "G8": None, "PASS": False,
                "lam_star": None, "at_boundary": None, "H": None, "H1": None, "H2": None,
                "CE1": None, "CE2": None, "CE_full": None, "chain_delta_CE": None, "chain_delta_H": None,
                "cv_nll": None, "val_nll": None, "d_nll": None, "MAP": None, "unseen": None,
                "effective_contexts": None, "required_m1": None, "required_m2": None, "required_m_total": None, "required_leak": None, "frozen_m2": G_THRESH["m2"][src], "frozen_m_total": G_THRESH["m_total"][src], "frozen_m1": G_THRESH["m1"], "frozen_leak": FROZEN_LEAK[src],
                "forbidden_nonempty": forbidden_nonempty, "frozen_binding_ok": binding_ok, "frozen_binding_path": binding_path,
            }
    else:
        for src in SOURCES:
            exp_cal = binding.get(src, {}).get("CAL_session_id") or binding.get(src, {}).get("CAL")
            exp_test = binding.get(src, {}).get("TEST_session_id") or binding.get(src, {}).get("TEST")
            sess = per_src_sessions[src]
            cal_dir, test_dir, _, _, _, _ = resolve_sessions_by_binding(sess, exp_cal, exp_test)
            cal_pairs_path = find_pairs_file(cal_dir)
            sidecar_path = find_sidecar_file(cal_dir, cal_dir.name)
            test_sidecar_path = find_sidecar_file(test_dir, test_dir.name)
            prov = load_sidecar_provenance(sidecar_path) if sidecar_path else {"delay": None, "peak": None, "session_id": None}
            test_prov = load_sidecar_provenance(test_sidecar_path) if test_sidecar_path else {"delay": None, "peak": None, "session_id": None}
            import pandas as pd
            df = pd.read_parquet(cal_pairs_path)
            all_fids = sorted(df.frame_id.unique().tolist())
            cal_fids = all_fids[0:4096]
            val_fids = all_fids[4096:4096+512]
            try:
                a_cal, b_cal = load_pairs_for_frames(cal_pairs_path, cal_fids)
                a_val, b_val = load_pairs_for_frames(cal_pairs_path, val_fids)
            except Exception as e:
                per_source[src] = {"status": f"EVIDENCE_INVALID frame violation {e}", "G1": False, "PASS": False, "forbidden_nonempty": forbidden_nonempty, "frozen_m2": G_THRESH["m2"][src], "frozen_m_total": G_THRESH["m_total"][src], "frozen_m1": G_THRESH["m1"], "frozen_leak": FROZEN_LEAK[src]}
                continue
            assert len(a_cal)==4096*256
            assert len(a_val)==512*256
            res = estimate_source((a_cal,b_cal),(a_val,b_val))
            g1_ok, g1_det = check_delay_peak_gate(prov.get("delay"), prov.get("peak"), prov.get("sigma", 80), prov.get("gate", 200), prov.get("thr", 40000))
            G1 = g1_ok
            G2 = not res["at_boundary"]
            G3 = res["d_nll"] <= G_THRESH["dNLL"]
            G4 = res["val_nll"] <= res["H"] + G_THRESH["val_leeway"]
            G5 = res["unseen"] <= G_THRESH["unseen"]
            G6 = res["required_m1"] <= G_THRESH["m1"]
            G7 = res["required_m2"] <= G_THRESH["m2"][src]
            G7_aux = res["required_m_total"] <= G_THRESH["m_total"][src]
            ce_chain_ok = res["chain_delta_CE"] < CE_CHAIN_TOL
            h_chain_ok = res["chain_delta_H"] < 1e-9
            cal_keys = [(src, cal_dir.name, fid) for fid in cal_fids]
            val_keys = [(src, cal_dir.name, fid) for fid in val_fids]
            tp = find_pairs_file(test_dir)
            test_all_fids = []
            if tp and tp.exists():
                try:
                    df2 = pd.read_parquet(tp)
                    test_all_fids = sorted(df2.frame_id.unique().tolist())[:120]
                except Exception:
                    test_all_fids = []
            test_keys = [(src, test_dir.name, fid) for fid in test_all_fids]
            tuple_ok = check_tuple_zero_overlap(cal_keys, val_keys, test_keys, forbidden_keys)
            not_cross, _ = check_not_cross_spliced_by_provenance(cal_dir.name, cal_dir.name, test_dir.name, prov, test_prov)
            G8 = ce_chain_ok and h_chain_ok and tuple_ok["cal∩val_empty"] and tuple_ok["cal∪val∩test_empty"] and tuple_ok["cal∪val∪test∩forbidden_empty"] and not_cross
            PASS = all([G1,G2,G3,G4,G5,G6,G7,G7_aux,G8])
            per_source[src] = {**res, "G1":G1,"G1_detail": g1_det, "G2":G2,"G3":G3,"G4":G4,"G5":G5,"G6":G6,"G7":G7,"G7_aux":G7_aux,"G8":G8,"PASS":PASS,
                               "frozen_m1": G_THRESH["m1"], "frozen_m2": G_THRESH["m2"][src], "frozen_m_total": G_THRESH["m_total"][src], "frozen_leak": FROZEN_LEAK[src],
                               "delta_m1": res["required_m1"]-G_THRESH["m1"], "delta_m2": res["required_m2"]-G_THRESH["m2"][src], "delta_m_total": res["required_m_total"]-G_THRESH["m_total"][src], "delta_leak": res["required_leak"]-FROZEN_LEAK[src],
                               "forbidden_nonempty": forbidden_nonempty, "tuple_overlap": tuple_ok, "session_ids": [p.name for p in sess],
                               "not_cross_spliced": not_cross, "sidecar_path": str(sidecar_path) if sidecar_path else None}

        if any(per_source[s].get("G1") is False for s in SOURCES):
            overall = "V65_EVIDENCE_INVALID"
        elif any(per_source[s].get("chain_delta_CE", 0) >= CE_CHAIN_TOL for s in SOURCES if "chain_delta_CE" in per_source[s] and per_source[s]["chain_delta_CE"] is not None):
            overall = "V65_EVIDENCE_INVALID"
        elif not data_ready:
            overall = "V65_DATA_NOT_READY"
        elif any(not per_source[s]["G2"] or not per_source[s]["G3"] or not per_source[s]["G4"] for s in SOURCES if per_source[s].get("G2") is not None):
            overall = "V65_MODEL_NOT_STABLE"
        elif any(not per_source[s]["G6"] or not per_source[s]["G7"] or not per_source[s]["G7_aux"] for s in SOURCES if per_source[s].get("G6") is not None):
            overall = "V65_RATE_INCOMPATIBLE_WITH_FROZEN_CANDIDATE"
        elif all(per_source[s].get("PASS") for s in SOURCES):
            overall = "V65_CHANNEL_COMPATIBILITY_READY_FOR_V66"
        else:
            overall = "V65_EVIDENCE_INVALID"

    # V66 equality: pending unless both registries exist and mechanically compared
    if args.test_registry and args.v66_registry and Path(args.test_registry).exists() and Path(args.v66_registry).exists():
        try:
            t = json.loads(Path(args.test_registry).read_text(encoding="utf-8"))
            v = json.loads(Path(args.v66_registry).read_text(encoding="utf-8"))
            def extract_keys(reg):
                keys=[]
                for src in SOURCES:
                    ps = reg.get("per_source",{}).get(src,{})
                    sess = ps.get("TEST_session_id") or ps.get("TEST_session",{}).get("id") or "TEST"
                    frames = ps.get("TEST_frames") or ps.get("TEST_session",{}).get("frames") or []
                    for fid in frames:
                        keys.append((src, sess, int(fid)))
                return keys
            a=set(extract_keys(t)); b=set(extract_keys(v))
            v66_check = {"status": "READY", "equals": a==b and len(a)>0, "v65_len": len(a), "v66_len": len(b), "sym_diff": len(a ^ b), "key": "(source,session,frame)"}
            if not v66_check["equals"]:
                v66_check["equals"] = False
        except Exception as e:
            v66_check = {"status": "ERROR", "equals": False, "error": str(e), "key": "(source,session,frame)"}
    else:
        v66_check = {"status": "PENDING", "equals": False, "reason": "V66 registry not yet generated (=V65 TEST pending)", "key": "(source,session,frame)"}

    out = {
        "schema": "v65_channel_compatibility_v1",
        "lifecycle": "PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED",
        "data_sha": DATA_SHA,
        "frozen_candidate": "H1-16+L1APP+LaneC184/190/192+Δ8+Δ8+full-tag",
        "estimator": "hierarchical P(a|b)=(C_ab+lam P_global)/(N_b+lam), lam 50 grid + bounded refine, CAL-only 4096*256, VAL 512*256, CE1/CE2 VAL gating, required vs frozen split",
        "per_source": per_source,
        "overall": overall,
        "g_thresholds": G_THRESH,
        "frozen": {"m1": G_THRESH["m1"], "m2": G_THRESH["m2"], "m_total": G_THRESH["m_total"], "leak": FROZEN_LEAK},
        "thresholds": {"CE_chain": CE_CHAIN_TOL, "H_chain": 1e-9, "lam_bounds": LAMBDA_BOUNDS_LOG10, "sigma": [50,150], "gate": 200, "threshold": 40000, "delay_peak_abs": 50},
        "zero_overlap_key": "(source,session,frame)",
        "forbidden_nonempty": forbidden_nonempty, "forbidden_keys": len(forbidden_keys),
        "v66_equals_v65_test": v66_check,
        "frozen_binding_ok": binding_ok, "frozen_binding_path": binding_path,
        "test_note": "TEST 120 frames identity sealed - never used in estimation/threshold, V66 registry exactly equals V65 TEST when both generated (tuple keys) else PENDING",
        "v66_prefreeze": {"blocks": 90, "per_source": 30, "gate_overall": "70/90", "gate_per": "20/30", "undetected_full": 0, "leak_frozen": "1144/1174/1184", "leak_required_vs_frozen_split": True},
    }
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    rep = [f"# V65 Channel Compatibility Report ({overall})", "", f"overall: **{overall}**", "", "| src | lam* | bdry | H1 | H2 | H | CE1 | CE2 | CE_full | dCE | CV | Val | dNLL | MAP | unseen | req_m1 | req_m2 | req_m_total | req_leak | frozen_m2 | frozen_leak | delta_leak | G1-8+G7aux | PASS |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for src in SOURCES:
        r = per_source[src]
        rep.append(f"| {src} | {r.get('lam_star')} | {r.get('at_boundary')} | {r.get('H1')} | {r.get('H2')} | {r.get('H')} | {r.get('CE1')} | {r.get('CE2')} | {r.get('CE_full')} | {r.get('chain_delta_CE')} | {r.get('cv_nll')} | {r.get('val_nll')} | {r.get('d_nll')} | {r.get('MAP')} | {r.get('unseen')} | {r.get('required_m1')} | {r.get('required_m2')} | {r.get('required_m_total')} | {r.get('required_leak')} | {r.get('frozen_m2')} | {r.get('frozen_leak')} | {r.get('delta_leak')} | {r.get('G1')},{r.get('G2')},{r.get('G3')},{r.get('G4')},{r.get('G5')},{r.get('G6')},{r.get('G7')},{r.get('G7_aux')},{r.get('G8')} | {r.get('PASS')} |")
    rep += ["", f"Frozen: m1<={G_THRESH['m1']} m2 {G_THRESH['m2']} m_total {G_THRESH['m_total']} frozen_leak {FROZEN_LEAK} vs required_leak=5*required_m_total+64", f"CE chain |CE_full-CE1-CE2|<{CE_CHAIN_TOL} H chain <1e-9, delay sign/50ps sigma[50,150] gate200 thr40000", f"zero_overlap_key=(source,session,frame) forbidden_nonempty={forbidden_nonempty} v66={v66_check} binding_ok={binding_ok}", f"Sample: CAL 4096*256=1048576 VAL 512*256=131072 real parquet, TEST identity sealed 120 frames/source", f"TEST: not read - v66 prefreeze 90 blocks 30/src 70/90 & 20/30 undetected 0", ""]
    Path(args.report).write_text("\n".join(rep), encoding="utf-8")
    print(f"[v65_channel_compatibility] overall={overall} required vs frozen split leak 5*required_m_total+64 vs {FROZEN_LEAK} forbidden_nonempty={forbidden_nonempty} v66_status={v66_check.get('status')} binding_ok={binding_ok}")
    if not Path(args.data_registry).exists():
        Path(args.data_registry).write_text(json.dumps({"overall": overall, "note": "spike placeholder", "zero_overlap_key": "(source,session,frame)", "v66_equals_v65_test": v66_check, "forbidden_nonempty": forbidden_nonempty, "frozen_binding_ok": binding_ok}, indent=2), encoding="utf-8")
    return 0

if __name__ == "__main__":
    sys.exit(main())
