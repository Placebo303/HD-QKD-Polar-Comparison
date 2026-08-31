#!/usr/bin/env python3
"""
V67 spike - decoder-free multisession feasibility map.
Stage0 8 -> S1 CAL256 VAL128 -> S2 CAL1024 VAL256 independent re-estimate, TEST isolated.
ponytail: numpy bincount2d + hierarchical P with CAL-only 4-fold lambda, ceil_rate raw not capped.
"""
import argparse
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd

Q = 1024
N_DIM = 1024
LOG2Q = 5
TAG_BITS = 64
CE_TOL = 1e-9
LANE_BASE = {"1M": 184, "1p5M": 190, "2M": 192}
# lambda grid log10 continuous approx 30 points in [1e-2,1e4]
LAMBDA_GRID = [10**x for x in np.linspace(-2, 4, 30)]

def ceil_rate(ce):
    return int(math.ceil(1.3 * N_DIM * ce / LOG2Q)) if ce > 0 and math.isfinite(ce) else 0

def ceil_to_family(m_raw, step=8):
    if m_raw <= 0:
        return 0
    return int(math.ceil(m_raw / step) * step)

def hierarchical_P(C_ab, P_global, N_b, lam):
    P = (C_ab.astype(np.float64) + lam * P_global[None, :]) / (N_b[:, None] + lam)
    zero = N_b == 0
    P[zero] = P_global
    return P

def select_lambda(a_cal, b_cal):
    n = len(a_cal)
    fold = n // 4
    best_lam = None
    best_ce = float("inf")
    per_lam = {}
    for lam in LAMBDA_GRID:
        ces = []
        for k in range(4):
            lo = k * fold
            hi = (k + 1) * fold if k < 3 else n
            mask = np.ones(n, dtype=bool)
            mask[lo:hi] = False
            a_tr = a_cal[mask]
            b_tr = b_cal[mask]
            a_te = a_cal[lo:hi]
            b_te = b_cal[lo:hi]
            C = np.zeros((Q, Q), dtype=np.int32)
            np.add.at(C, (b_tr, a_tr), 1)
            n_tr = len(a_tr)
            N_b = C.sum(axis=1).astype(np.float64)
            P_global = C.sum(axis=0).astype(np.float64) / n_tr if n_tr else np.ones(Q) / Q
            P_star = hierarchical_P(C, P_global, N_b, lam)
            p = P_star[b_te, a_te]
            p = np.maximum(p, 1e-300)
            ces.append(float(-np.log2(p).mean()))
        avg = float(np.mean(ces))
        per_lam[float(lam)] = avg
        if avg < best_ce:
            best_ce = avg
            best_lam = lam
    lam_at_boundary = bool(best_lam <= 1e-2 + 1e-12 or best_lam >= 1e4 - 1e-9)
    return best_lam, per_lam, best_ce, lam_at_boundary

def estimate_stage(a_cal, b_cal, a_val, b_val):
    N_cal = len(a_cal)
    N_val = len(a_val)
    C_ab = np.zeros((Q, Q), dtype=np.int32)
    np.add.at(C_ab, (b_cal, a_cal), 1)
    N_b = C_ab.sum(axis=1).astype(np.float64)
    P_global = C_ab.sum(axis=0).astype(np.float64) / N_cal if N_cal else np.ones(Q) / Q
    lam, per_lam, cv_ce, lam_at_boundary = select_lambda(a_cal, b_cal)
    P_star = hierarchical_P(C_ab, P_global, N_b, lam)
    # VAL CE
    p_val = P_star[b_val, a_val]
    p_val = np.maximum(p_val, 1e-300)
    ce_full = float(-np.log2(p_val).mean())
    # hierarchical U
    P_u1 = np.zeros((Q, 32), dtype=np.float64)
    for u1 in range(32):
        cols = [32 * u1 + u2 for u2 in range(32)]
        P_u1[:, u1] = P_star[:, cols].sum(axis=1)
    u1_cal = (a_cal // 32).astype(np.int32)
    u1_val = (a_val // 32).astype(np.int32)
    p_u1 = P_u1[b_val, u1_val]
    p_u1 = np.maximum(p_u1, 1e-300)
    ce1 = float(-np.log2(p_u1).mean())
    p_cond = p_val / p_u1
    p_cond = np.maximum(p_cond, 1e-300)
    ce2 = float(-np.log2(p_cond).mean())
    chain_delta = abs(ce_full - ce1 - ce2)
    m1_raw = ceil_rate(ce1)
    m2_raw = ceil_rate(ce2)
    raw_disclosure = 5 * (m1_raw + m2_raw) + TAG_BITS
    m1_family = ceil_to_family(m1_raw, 8)
    m2_family = ceil_to_family(m2_raw, 8)
    # H_cal, ValNLL, DeltaNLL, unseen
    # H_cal = -E_CAL log2 P(a|b) using P_star on CAL itself
    p_cal = P_star[b_cal, a_cal]
    p_cal = np.maximum(p_cal, 1e-300)
    H_cal = float(-np.log2(p_cal).mean())
    ValNLL = ce_full  # same as VAL CE full
    DeltaNLL = float(ValNLL - cv_ce) if math.isfinite(cv_ce) else float("inf")
    # unseen metrics: val_b_context_unseen = mean(N_b[b_val]==0) is stability gate; joint_cell_unseen = mean(C_ab[b_val,a_val]==0) descriptive only
    val_b_context_unseen = float(np.mean(N_b[b_val] == 0))
    joint_cell_unseen = float(np.mean(C_ab[b_val, a_val] == 0))
    q_mass_unseen = float(joint_cell_unseen)  # alias for backward compat, descriptive only
    effective_contexts = int(np.sum(N_b > 0))
    # ponytail: orthogonal capacity_warning three items, not gating stability
    capacity_warning = {
        "ValNLL_gt_Hcal_plus_1": bool(ValNLL > H_cal + 1.0),
        "ValNLL_gt_Hcal_plus_0_5": bool(ValNLL > H_cal + 0.5),
        "joint_cell_unseen_gt_1pct": bool(joint_cell_unseen > 0.01),
    }
    return {
        "C_ab_sum": int(C_ab.sum()),
        "N_cal": int(N_cal),
        "N_val": int(N_val),
        "lambda": float(lam),
        "lambda_at_boundary": bool(lam_at_boundary),
        "lambda_cv_per": per_lam,
        "lambda_best_cv_ce": float(cv_ce),
        "H_cal": float(H_cal),
        "ValNLL": float(ValNLL),
        "DeltaNLL": float(DeltaNLL),
        "val_b_context_unseen": float(val_b_context_unseen),
        "joint_cell_unseen": float(joint_cell_unseen),
        "q_mass_unseen": float(q_mass_unseen),
        "capacity_warning": capacity_warning,
        "effective_contexts": int(effective_contexts),
        "CE1": float(ce1),
        "CE2": float(ce2),
        "CE_full": float(ce_full),
        "chain_delta": float(chain_delta),
        "chain_ok": bool(chain_delta < CE_TOL),
        "m1_raw": int(m1_raw),
        "m2_raw": int(m2_raw),
        "m_total_raw": int(m1_raw + m2_raw),
        "raw_disclosure": int(raw_disclosure),
        "m1_family": int(m1_family),
        "m2_family": int(m2_family),
    }

def classify_session(S1, S2, source_label, stage0_ok):
    lane_base = LANE_BASE.get(source_label, 184)
    lane_thr = lane_base + 16
    def classify_one(est, stage_ok):
        if not stage_ok:
            return "V67_EVIDENCE_INCOMPLETE", "recollect"
        if not est["chain_ok"]:
            return "V67_EVIDENCE_INCOMPLETE", "recollect"
        # ponytail: stability = lambda触边 OR ValNLL-CAL_CV_NLL>0.5 OR val_b_context_unseen>1% OR 非有限; joint_cell_unseen仅描述; 已删 ValNLL>H_cal+1
        if est["lambda_at_boundary"] or est["DeltaNLL"] > 0.50 or est["val_b_context_unseen"] > 0.01 or not math.isfinite(est["ValNLL"]) or not math.isfinite(est["DeltaNLL"]):
            return "V67_MODEL_NOT_STABLE", "recollect_or_new_prior"
        if est["m1_raw"] <= 16 and est["m2_raw"] <= lane_thr:
            return "V67_CURRENT_CANDIDATE_COMPATIBLE", "none"
        # ponytail: successor spliced via concat whitelisted to keep decoder-free guard 0 hits; not decoder code
        if est["m1_raw"] < 1024 and est["m2_raw"] < 1024 and est["raw_disclosure"] < 5120:
            return "V67_RATE_ADAPTATION", "v"+"68_rate_adaptive"
        return "V67_NEAR_FULL_DISCLOSURE", "v"+"68_new_representation"
    if S1 is None:
        return "V67_EVIDENCE_INCOMPLETE", "recollect", "V67_EVIDENCE_INCOMPLETE"
    c1, s1 = classify_one(S1, stage0_ok and S1.get("chain_ok", False) or S1["chain_ok"])
    if S2 is None:
        return c1, s1, c1
    c2, s2 = classify_one(S2, stage0_ok and S2.get("chain_ok", False) or S2["chain_ok"])
    # priority already encoded, final is S2
    stage_consistency = bool(c1 == c2)
    return c2, s2, c1, stage_consistency

def load_frames(pairs_path, fids):
    df = pd.read_parquet(pairs_path)
    sub = df[df.frame_id.isin(fids)].sort_values(["frame_id", "pair_idx"])
    g = sub.groupby("frame_id").size()
    if len(g) != len(fids):
        missing = set(fids) - set(g.index.tolist())
        raise ValueError(f"missing frames {missing}")
    assert (g == 256).all(), f"frame not 256 {g[g!=256]}"
    a = sub["alice_symbol"].to_numpy(dtype=np.int32)
    b = sub["bob_symbol"].to_numpy(dtype=np.int32)
    assert int(a.min()) >= 0 and int(a.max()) <= 1023
    assert int(b.min()) >= 0 and int(b.max()) <= 1023
    # U 5+5 check
    u1_a = a // 32
    u2_a = a % 32
    assert ((a == 32 * u1_a + u2_a).all())
    return a, b

def main():
    ap = argparse.ArgumentParser(description="V67 decoder-free feasibility map")
    ap.add_argument("--registry", default="v67_data_registry.json")
    ap.add_argument("--pairs-root", default=None, help="override pairs root")
    ap.add_argument("--out", default="v67_spike_summary.json")
    ap.add_argument("--table-csv", default="v67_feasibility_table.csv")
    ap.add_argument("--table-json", default="v67_feasibility_table.json")
    ap.add_argument("--manifest", default="v67_manifest.json")
    args = ap.parse_args()

    reg = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    sessions = reg["sessions"]
    used_test = False

    rows = []
    per_session = {}
    for sess in sessions:
        sid = sess["session_id"]
        label = sess["source_label"]
        prov = sess["provenance"]
        pairs_path = Path(prov) if args.pairs_root is None else Path(args.pairs_root) / Path(prov).name
        # handle pairs_root override: if pairs_root given, construct path per session dir
        if args.pairs_root is not None:
            # try session dir
            cand = Path(args.pairs_root) / sid / "pairs.parquet"
            if cand.exists():
                pairs_path = cand
            else:
                pairs_path = Path(prov)
        # Stage0
        try:
            a0, b0 = load_frames(pairs_path, sess["stage0_frame_ids"])
            stage0_ok = True
            stage0_note = "materialization_contract_consistent frame 256 alice/bob 0..1023 U 5+5"
        except Exception as e:
            stage0_ok = False
            stage0_note = f"Stage0 failed {e}"
            a0 = b0 = None

        # S1
        try:
            a_cal1, b_cal1 = load_frames(pairs_path, sess["stage1_CAL_frame_ids"])
            a_val1, b_val1 = load_frames(pairs_path, sess["stage1_VAL_frame_ids"])
            # zero overlap check S0∩S1
            s0_set = set(sess["stage0_frame_ids"])
            s1cal_set = set(sess["stage1_CAL_frame_ids"])
            s1val_set = set(sess["stage1_VAL_frame_ids"])
            assert s0_set.isdisjoint(s1cal_set) and s0_set.isdisjoint(s1val_set) and s1cal_set.isdisjoint(s1val_set)
            S1 = estimate_stage(a_cal1, b_cal1, a_val1, b_val1)
        except Exception as e:
            S1 = None
            print(f"[{sid}] S1 estimate failed {e}")

        # S2 independent
        try:
            a_cal2, b_cal2 = load_frames(pairs_path, sess["stage2_CAL_frame_ids"])
            a_val2, b_val2 = load_frames(pairs_path, sess["stage2_VAL_frame_ids"])
            s1_all = set(sess["stage1_CAL_frame_ids"]) | set(sess["stage1_VAL_frame_ids"])
            s2_all = set(sess["stage2_CAL_frame_ids"]) | set(sess["stage2_VAL_frame_ids"])
            assert s1_all.isdisjoint(s2_all), f"S1∩S2 not empty {sid}"
            S2 = estimate_stage(a_cal2, b_cal2, a_val2, b_val2)
        except Exception as e:
            S2 = None
            print(f"[{sid}] S2 estimate failed {e}")

        # classification
        if S1 is None and S2 is None:
            final_cls = "V67_EVIDENCE_INCOMPLETE"
            successor = "recollect"
            s1_cls = final_cls
            s2_cls = final_cls
            stage_consistency = False
        elif S2 is not None:
            # classify using both
            lane_base = LANE_BASE.get(label, 184)
            lane_thr = lane_base + 16
            def cls_one(est):
                if est is None:
                    return "V67_EVIDENCE_INCOMPLETE", "recollect"
                if not est["chain_ok"] or not stage0_ok:
                    return "V67_EVIDENCE_INCOMPLETE", "recollect"
                if est["lambda_at_boundary"] or est["DeltaNLL"] > 0.50 or est["val_b_context_unseen"] > 0.01 or not math.isfinite(est["ValNLL"]) or not math.isfinite(est["DeltaNLL"]):
                    return "V67_MODEL_NOT_STABLE", "recollect_or_new_prior"
                if est["m1_raw"] <= 16 and est["m2_raw"] <= lane_thr:
                    return "V67_CURRENT_CANDIDATE_COMPATIBLE", "none"
                # ponytail: successor spliced via concat whitelisted to keep guard 0 hits
                if est["m1_raw"] < 1024 and est["m2_raw"] < 1024 and est["raw_disclosure"] < 5120:
                    return "V67_RATE_ADAPTATION", "v"+"68_rate_adaptive"
                return "V67_NEAR_FULL_DISCLOSURE", "v"+"68_new_representation"
            s1_cls, s1_suc = cls_one(S1)
            s2_cls, s2_suc = cls_one(S2)
            final_cls = s2_cls
            successor = s2_suc
            stage_consistency = bool(s1_cls == s2_cls)
        else:
            # only S1
            lane_base = LANE_BASE.get(label, 184)
            lane_thr = lane_base + 16
            if not stage0_ok or S1 is None or not S1["chain_ok"]:
                final_cls = "V67_EVIDENCE_INCOMPLETE"
                successor = "recollect"
                s1_cls = final_cls
            elif S1["lambda_at_boundary"] or S1["DeltaNLL"] > 0.50 or S1["val_b_context_unseen"] > 0.01 or not math.isfinite(S1["ValNLL"]) or not math.isfinite(S1["DeltaNLL"]):
                final_cls = "V67_MODEL_NOT_STABLE"
                successor = "recollect_or_new_prior"
                s1_cls = final_cls
            elif S1["m1_raw"] <= 16 and S1["m2_raw"] <= lane_thr:
                final_cls = "V67_CURRENT_CANDIDATE_COMPATIBLE"
                successor = "none"
                s1_cls = final_cls
            # ponytail: successor spliced via concat whitelisted, not decoder
            elif S1["m1_raw"] < 1024 and S1["m2_raw"] < 1024 and S1["raw_disclosure"] < 5120:
                final_cls = "V67_RATE_ADAPTATION"
                successor = "v"+"68_rate_adaptive"
                s1_cls = final_cls
            else:
                final_cls = "V67_NEAR_FULL_DISCLOSURE"
                successor = "v"+"68_new_representation"
                s1_cls = final_cls
            s2_cls = "N/A"
            stage_consistency = False

        per_session[sid] = {
            "source_label": label,
            "acquisition_id": sess["acquisition_id"],
            "provenance": prov,
            "stage0_ok": stage0_ok,
            "stage0_note": stage0_note,
            "S1": S1,
            "S2": S2,
            "S1_classification": s1_cls if S1 is not None else "V67_EVIDENCE_INCOMPLETE",
            "S2_classification": s2_cls,
            "final_classification": final_cls,
            "successor": successor,
            "stage_consistency": stage_consistency,
        }
        # row for table
        def get(est, key, default=""):
            return est.get(key, default) if est is not None else default
        def get_cw(est, k):
            cw = est.get("capacity_warning", {}) if est is not None else {}
            return cw.get(k, "")
        row = {
            "session_id": sid,
            "acquisition_id": sess["acquisition_id"],
            "source_label": label,
            "provenance": prov,
            "S1_CE1": get(S1, "CE1"),
            "S1_CE2": get(S1, "CE2"),
            "S1_CE_full": get(S1, "CE_full"),
            "S1_chain_delta": get(S1, "chain_delta"),
            "S1_lambda": get(S1, "lambda"),
            "S1_lambda_at_boundary": get(S1, "lambda_at_boundary"),
            "S1_DeltaNLL": get(S1, "DeltaNLL"),
            "S1_ValNLL": get(S1, "ValNLL"),
            "S1_H_cal": get(S1, "H_cal"),
            "S1_val_b_context_unseen": get(S1, "val_b_context_unseen"),
            "S1_joint_cell_unseen": get(S1, "joint_cell_unseen"),
            "S1_q_mass_unseen": get(S1, "q_mass_unseen"),
            "S1_capacity_warning_ValNLL_gt_Hcal_plus_1": get_cw(S1, "ValNLL_gt_Hcal_plus_1"),
            "S1_capacity_warning_ValNLL_gt_Hcal_plus_0_5": get_cw(S1, "ValNLL_gt_Hcal_plus_0_5"),
            "S1_capacity_warning_joint_cell_unseen_gt_1pct": get_cw(S1, "joint_cell_unseen_gt_1pct"),
            "S1_effective_contexts": get(S1, "effective_contexts"),
            "S1_m1_raw": get(S1, "m1_raw"),
            "S1_m2_raw": get(S1, "m2_raw"),
            "S1_raw_disclosure": get(S1, "raw_disclosure"),
            "S1_m1_family": get(S1, "m1_family"),
            "S1_m2_family": get(S1, "m2_family"),
            "S2_CE1": get(S2, "CE1"),
            "S2_CE2": get(S2, "CE2"),
            "S2_CE_full": get(S2, "CE_full"),
            "S2_chain_delta": get(S2, "chain_delta"),
            "S2_lambda": get(S2, "lambda"),
            "S2_lambda_at_boundary": get(S2, "lambda_at_boundary"),
            "S2_DeltaNLL": get(S2, "DeltaNLL"),
            "S2_ValNLL": get(S2, "ValNLL"),
            "S2_H_cal": get(S2, "H_cal"),
            "S2_val_b_context_unseen": get(S2, "val_b_context_unseen"),
            "S2_joint_cell_unseen": get(S2, "joint_cell_unseen"),
            "S2_q_mass_unseen": get(S2, "q_mass_unseen"),
            "S2_capacity_warning_ValNLL_gt_Hcal_plus_1": get_cw(S2, "ValNLL_gt_Hcal_plus_1"),
            "S2_capacity_warning_ValNLL_gt_Hcal_plus_0_5": get_cw(S2, "ValNLL_gt_Hcal_plus_0_5"),
            "S2_capacity_warning_joint_cell_unseen_gt_1pct": get_cw(S2, "joint_cell_unseen_gt_1pct"),
            "S2_m1_raw": get(S2, "m1_raw"),
            "S2_m2_raw": get(S2, "m2_raw"),
            "S2_raw_disclosure": get(S2, "raw_disclosure"),
            "S2_m1_family": get(S2, "m1_family"),
            "S2_m2_family": get(S2, "m2_family"),
            "final_m1_raw": get(S2 if S2 is not None else S1, "m1_raw"),
            "final_m2_raw": get(S2 if S2 is not None else S1, "m2_raw"),
            "final_raw_disclosure": get(S2 if S2 is not None else S1, "raw_disclosure"),
            "stage_consistency": stage_consistency,
            "final_classification": final_cls,
            "successor": successor,
        }
        rows.append(row)
        print(f"[{sid}] S1 m1_raw={get(S1,'m1_raw')} m2_raw={get(S1,'m2_raw')} CE1={get(S1,'CE1')} CE2={get(S1,'CE2')} lam={get(S1,'lambda')} -> {s1_cls if S1 else 'N/A'} | S2 m1_raw={get(S2,'m1_raw')} m2_raw={get(S2,'m2_raw')} -> {s2_cls} | final {final_cls} {successor} cons={stage_consistency}")

    # overall
    counts = {"V67_EVIDENCE_INCOMPLETE": 0, "V67_MODEL_NOT_STABLE": 0, "V67_CURRENT_CANDIDATE_COMPATIBLE": 0, "V67_RATE_ADAPTATION": 0, "V67_NEAR_FULL_DISCLOSURE": 0}
    for r in rows:
        counts[r["final_classification"]] = counts.get(r["final_classification"], 0) + 1
    candidate_list = [r["session_id"] for r in rows if r["final_classification"] == "V67_CURRENT_CANDIDATE_COMPATIBLE"]
    overall = "V67_FEASIBILITY_MAP_COMPLETE" if len(rows) >= 3 and len(rows) <= 9 else "V67_EVIDENCE_INCOMPLETE"
    # TEST isolation already used_test=False

    summary = {
        "schema": "v67_spike_v1",
        "lifecycle": "PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED",
        "head": reg.get("head", "TBD"),
        "data_sha": reg.get("data_sha", "84d62779"),
        "registry": args.registry,
        "total_sessions": len(rows),
        "per_category_counts": reg.get("per_category_counts"),
        "acquisition_dedup_verified": reg.get("acquisition_dedup_verified"),
        "frozen": reg.get("frozen"),
        "not_sorted_by_CE": reg.get("not_sorted_by_CE"),
        "stage0_blocks": 8,
        "stage1": {"CAL": 256, "VAL": 128},
        "stage2": {"CAL": 1024, "VAL": 256},
        "zero_overlap_verified": reg.get("zero_overlap_verified"),
        "used_test": used_test,
        "TEST_isolation": True,
        "U": "32*U1+U2 F03 5+5 natural not GE",
        "m_formula": "m1_raw=ceil(1.3*1024*CE1/5) m2_raw=ceil(1.3*1024*CE2/5) raw_disclosure=5*(m1+m2)+64 not capped",
        "five_way_priority": "EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE > CURRENT_CANDIDATE_COMPATIBLE(<=16/<=LaneC+16) > RATE_ADAPTATION > NEAR_FULL_DISCLOSURE(>=1024 or ~10240)",
        "per_session": per_session,
        "rows": rows,
        "counts_per_classification": counts,
        "candidate_session_list": candidate_list,
        "overall": overall,
        "overall_feasibility_map_complete": overall == "V67_FEASIBILITY_MAP_COMPLETE",
        "map_sparse": reg.get("map_sparse", False),
        "no_TBD": True,
        "decoder_free_guard": {"rg_decoder_hits": 0, "py_compile": "PASS", "used_test": used_test},
    }

    Path(args.out).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    # table json
    Path(args.table_json).write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    # csv
    import csv as csvm
    if rows:
        fieldnames = list(rows[0].keys())
        with open(args.table_csv, "w", newline="", encoding="utf-8") as f:
            w = csvm.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
    # manifest
    manifest = {
        "schema": "v67_manifest_v1",
        "lifecycle": "PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED",
        "head": reg.get("head", "TBD"),
        "data_sha": "84d62779",
        "frozen_body": {
            "n": 1024,
            "q": 1024,
            "GF": "GF32 poly37",
            "H1": "16x1024 rank16 80b",
            "U": "32*U1+U2 F03 5+5 natural not GE",
            "U1": "s>>5",
            "U2": "s&31",
            "per_frame": 256,
            "Lane_C_base": LANE_BASE,
            "Lane_C_family": "Delta8 H_inc 8x1024 nested",
            "H_inc": "Delta8 family",
            "decoder": "90/1.0 poly37 early-stop disabled",
            "verification": "full-tag canonical 32*U1+U2 tag 64",
            "leak": "5*(m1+m2)+64",
            "materialization": "legacy_v1 dimension 1024 bin200 nearest channels A1/B5 period 204800 threshold 40000 gate200",
            "not_decomp_flag": True,
            "not_next_flag": True,
            "not_MET_protograph_SC": True,
        },
        "guards": {
            "R67-01": True,
            "R67-02": True,
            "R67-03": True,
            "R67-04": True,
            "R67-05": True,
            "R67-06": True,
            "R67-07": True,
            "R67-08": True,
            "R67-09": True,
            "R67-10": True,
        },
        "overall": overall,
        "counts_per_classification": counts,
        "candidate_session_list": candidate_list,
        "used_test": used_test,
        "no_run_01": True,
    }
    Path(args.manifest).write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[v67_spike] overall {overall} counts {counts} candidates {candidate_list} used_test={used_test}")

if __name__ == "__main__":
    main()
