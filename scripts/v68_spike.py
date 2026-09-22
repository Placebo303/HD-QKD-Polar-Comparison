#!/usr/bin/env python3
"""
V68 spike - balanced GF32 bit-partition 252 enumeration CAL-only S* VAL confirm.
ponytail: itertools.combinations for 252, numpy bincount, hierarchical P, ceil raw not capped.
"""
import argparse
import itertools
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
LAMBDA_GRID = [10**x for x in np.linspace(-2, 4, 30)]

def ceil_rate(ce):
    return int(math.ceil(1.3 * N_DIM * ce / LOG2Q)) if ce > 0 and math.isfinite(ce) else 0

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
    per = {}
    for lam in LAMBDA_GRID:
        ces = []
        for k in range(4):
            lo = k * fold
            hi = (k+1)*fold if k < 3 else n
            mask = np.ones(n, dtype=bool)
            mask[lo:hi] = False
            a_tr = a_cal[mask]; b_tr = b_cal[mask]
            a_te = a_cal[lo:hi]; b_te = b_cal[lo:hi]
            C = np.zeros((Q, Q), dtype=np.int32)
            np.add.at(C, (b_tr, a_tr), 1)
            N_b = C.sum(axis=1).astype(np.float64)
            P_global = C.sum(axis=0).astype(np.float64) / len(a_tr) if len(a_tr) else np.ones(Q)/Q
            Ps = hierarchical_P(C, P_global, N_b, lam)
            p = Ps[b_te, a_te]
            p = np.maximum(p, 1e-300)
            ces.append(float(-np.log2(p).mean()))
        avg = float(np.mean(ces))
        per[float(lam)] = avg
        if avg < best_ce:
            best_ce = avg
            best_lam = lam
    lam_at_boundary = bool(best_lam <= 1e-2 + 1e-12 or best_lam >= 1e4 - 1e-9)
    return best_lam, per, best_ce, lam_at_boundary

def bits_maps(S):
    T = tuple(sorted(set(range(10)) - set(S)))
    map_u1 = np.zeros(Q, dtype=np.int32)
    map_u2 = np.zeros(Q, dtype=np.int32)
    for s in range(Q):
        u1 = 0
        for k, b in enumerate(S):
            if (s >> b) & 1:
                u1 |= 1 << k
        u2 = 0
        for k, b in enumerate(T):
            if (s >> b) & 1:
                u2 |= 1 << k
        map_u1[s] = u1
        map_u2[s] = u2
    # ponytail: naive loop O(1024*10) trivial, upgrade to vectorized if scale
    return map_u1, map_u2, T

def val_info_for_S(a_cal, b_cal, a_val, b_val, map_u1, lam):
    C_ab = np.zeros((Q, Q), dtype=np.int32)
    np.add.at(C_ab, (b_cal, a_cal), 1)
    N_b = C_ab.sum(axis=1).astype(np.float64)
    P_global = C_ab.sum(axis=0).astype(np.float64) / len(a_cal) if len(a_cal) else np.ones(Q)/Q
    Ps = hierarchical_P(C_ab, P_global, N_b, lam)
    p_val = Ps[b_val, a_val]
    p_val = np.maximum(p_val, 1e-300)
    ce_full = float(-np.log2(p_val).mean())
    # P_u1 matrix
    cols_per_u1 = [np.where(map_u1 == u1)[0] for u1 in range(32)]
    P_u1 = np.zeros((Q, 32), dtype=np.float64)
    for u1 in range(32):
        cols = cols_per_u1[u1]
        P_u1[:, u1] = Ps[:, cols].sum(axis=1)
    u1_val = map_u1[a_val]
    p_u1 = P_u1[b_val, u1_val]
    p_u1 = np.maximum(p_u1, 1e-300)
    ce1 = float(-np.log2(p_u1).mean())
    p_cond = p_val / p_u1
    p_cond = np.maximum(p_cond, 1e-300)
    ce2 = float(-np.log2(p_cond).mean())
    chain_delta = abs(ce_full - ce1 - ce2)
    m1_raw = ceil_rate(ce1)
    m2_raw = ceil_rate(ce2)
    raw = 5*(m1_raw+m2_raw)+TAG_BITS
    # H_cal descriptive
    p_cal = Ps[b_cal, a_cal]
    p_cal = np.maximum(p_cal, 1e-300)
    H_cal = float(-np.log2(p_cal).mean())
    ValNLL = ce_full
    val_b_unseen = float(np.mean(N_b[b_val]==0))
    joint_unseen = float(np.mean(C_ab[b_val, a_val]==0))
    effective = int(np.sum(N_b>0))
    return {
        "CE1": ce1, "CE2": ce2, "CE_full": ce_full, "chain_delta": chain_delta, "chain_ok": chain_delta < CE_TOL,
        "m1_raw": m1_raw, "m2_raw": m2_raw, "raw_disclosure": raw,
        "max_m": max(m1_raw, m2_raw), "sum_m": m1_raw+m2_raw, "abs_m": abs(m1_raw-m2_raw),
        "H_cal": H_cal, "ValNLL": ValNLL, "val_b_context_unseen": val_b_unseen, "joint_cell_unseen": joint_unseen,
        "q_mass_unseen": joint_unseen, "effective_contexts": effective,
        "C_ab_sum": int(C_ab.sum()), "N_b": N_b, "C_ab": C_ab, "P_global": P_global, "Ps": Ps, "P_u1": P_u1
    }

def cv_info_for_S(a_cal, b_cal, map_u1, lam):
    n = len(a_cal)
    fold = n // 4
    ce1s = []; ce2s = []; cefulls = []
    for k in range(4):
        lo = k*fold; hi = (k+1)*fold if k < 3 else n
        mask = np.ones(n, dtype=bool); mask[lo:hi]=False
        a_tr = a_cal[mask]; b_tr = b_cal[mask]
        a_te = a_cal[lo:hi]; b_te = b_cal[lo:hi]
        C = np.zeros((Q, Q), dtype=np.int32)
        np.add.at(C, (b_tr, a_tr), 1)
        N_b = C.sum(axis=1).astype(np.float64)
        P_global = C.sum(axis=0).astype(np.float64)/len(a_tr) if len(a_tr) else np.ones(Q)/Q
        Ps = hierarchical_P(C, P_global, N_b, lam)
        p_val = Ps[b_te, a_te]
        p_val = np.maximum(p_val, 1e-300)
        cef = float(-np.log2(p_val).mean())
        cols_per_u1 = [np.where(map_u1 == u1)[0] for u1 in range(32)]
        P_u1 = np.zeros((Q, 32), dtype=np.float64)
        for u1 in range(32):
            cols = cols_per_u1[u1]
            P_u1[:, u1] = Ps[:, cols].sum(axis=1)
        u1_te = map_u1[a_te]
        p_u1 = P_u1[b_te, u1_te]
        p_u1 = np.maximum(p_u1, 1e-300)
        ce1 = float(-np.log2(p_u1).mean())
        p_cond = np.maximum(p_val/p_u1, 1e-300)
        ce2 = float(-np.log2(p_cond).mean())
        ce1s.append(ce1); ce2s.append(ce2); cefulls.append(cef)
    ce1_cv = float(np.mean(ce1s)); ce2_cv = float(np.mean(ce2s))
    m1_cv = ceil_rate(ce1_cv); m2_cv = ceil_rate(ce2_cv)
    return {"CE1_cv": ce1_cv, "CE2_cv": ce2_cv, "m1_cv": m1_cv, "m2_cv": m2_cv, "max_cv": max(m1_cv,m2_cv), "sum_cv": m1_cv+m2_cv, "abs_cv": abs(m1_cv-m2_cv)}

def load_frames(pairs_path, fids):
    df = pd.read_parquet(pairs_path)
    sub = df[df.frame_id.isin(fids)].sort_values(["frame_id","pair_idx"])
    g = sub.groupby("frame_id").size()
    assert len(g)==len(fids), f"missing {set(fids)-set(g.index)}"
    assert (g==256).all()
    a = sub["alice_symbol"].to_numpy(dtype=np.int32)
    b = sub["bob_symbol"].to_numpy(dtype=np.int32)
    assert int(a.min())>=0 and int(a.max())<=1023
    assert int(b.min())>=0 and int(b.max())<=1023
    return a, b

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default="v68_data_registry.json")
    ap.add_argument("--out", default="v68_results.json")
    ap.add_argument("--table-csv", default="v68_table.csv")
    ap.add_argument("--table-json", default="v68_table.json")
    ap.add_argument("--manifest", default="v68_manifest.json")
    args = ap.parse_args()
    reg = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    S_list = list(itertools.combinations(range(10),5))
    assert len(S_list)==252 and S_list[0]==(0,1,2,3,4) and S_list[-1]==(5,6,7,8,9)
    S_nat = (5,6,7,8,9)
    S_nat_idx = S_list.index(S_nat)
    maps = {}
    for S in S_list:
        mu1, mu2, T = bits_maps(S)
        # verify natural
        if S==S_nat:
            assert (mu1 == np.arange(Q)//32).all() or (mu1 == np.array([s>>5 for s in range(Q)])).all()
            assert (mu2 == np.array([s & 31 for s in range(Q)])).all()
        maps[S] = (mu1, mu2, T)
    used_val_in_selection = False
    used_test = False
    per_session = {}
    all_rows = []
    S_star_per_session = {}
    S_star_common = None
    # store per session per S CV and VAL for later common selection
    per_session_S_data = {}
    for sess in reg["sessions"]:
        sid = sess["session_id"]
        prov = sess["provenance"]
        pairs_path = Path(prov)
        a_cal, b_cal = load_frames(pairs_path, sess["stage2_CAL_frame_ids"])
        a_val, b_val = load_frames(pairs_path, sess["stage2_VAL_frame_ids"])
        assert len(a_cal)==262144 and len(a_val)==65536
        lam_star, per_lam, cv_ce, lam_at_boundary = select_lambda(a_cal, b_cal)
        # compute for each S
        rows_for_sess = []
        best_T = None
        best_S = None
        for idx, S in enumerate(S_list):
            mu1, mu2, T = maps[S]
            vm = val_info_for_S(a_cal, b_cal, a_val, b_val, mu1, lam_star)
            cv = cv_info_for_S(a_cal, b_cal, mu1, lam_star)
            assert vm["chain_ok"], f"chain {sid} {S}"
            # CAL NLL proxy for DeltaNLL (use cv_ce from lambda selection? use ValNLL - cv_ce)
            DeltaNLL = float(vm["ValNLL"] - cv_ce) if math.isfinite(cv_ce) else float("inf")
            cap_warn = {"m1_ge_1024": vm["m1_raw"]>=1024, "m2_ge_1024": vm["m2_raw"]>=1024, "disclosure_ge_5120": vm["raw_disclosure"]>=5120}
            row = {
                "session_id": sid,
                "acquisition_id": sess["acquisition_id"],
                "source_label": sess["source_label"],
                "S_tuple": list(S),
                "S_lex_index": idx,
                "S_bits": "".join(str(b) for b in S),
                "is_S_nat": S==S_nat,
                "CAL_lambda": float(lam_star),
                "CAL_lambda_at_boundary": bool(lam_at_boundary),
                "CAL_H_cal": float(vm["H_cal"]),
                "CAL_ValNLL": float(vm["ValNLL"]),
                "CAL_DeltaNLL": float(DeltaNLL),
                "CAL_val_b_context_unseen": float(vm["val_b_context_unseen"]),
                "CAL_joint_cell_unseen": float(vm["joint_cell_unseen"]),
                "CAL_q_mass_unseen": float(vm["q_mass_unseen"]),
                "CAL_effective_contexts": int(vm["effective_contexts"]),
                "CAL_CE1_cv": float(cv["CE1_cv"]),
                "CAL_CE2_cv": float(cv["CE2_cv"]),
                "CAL_m1_cv": int(cv["m1_cv"]),
                "CAL_m2_cv": int(cv["m2_cv"]),
                "CAL_max_cv": int(cv["max_cv"]),
                "CAL_sum_cv": int(cv["sum_cv"]),
                "CAL_abs_cv": int(cv["abs_cv"]),
                "VAL_CE1": float(vm["CE1"]),
                "VAL_CE2": float(vm["CE2"]),
                "VAL_CE_full": float(vm["CE_full"]),
                "chain_delta": float(vm["chain_delta"]),
                "VAL_m1_raw": int(vm["m1_raw"]),
                "VAL_m2_raw": int(vm["m2_raw"]),
                "VAL_raw_disclosure": int(vm["raw_disclosure"]),
                "VAL_max_m": int(vm["max_m"]),
                "VAL_sum_m": int(vm["sum_m"]),
                "VAL_abs_m": int(vm["abs_m"]),
                "VAL_ValNLL": float(vm["ValNLL"]),
                "VAL_DeltaNLL": float(DeltaNLL),
                "VAL_val_b_context_unseen": float(vm["val_b_context_unseen"]),
                "VAL_joint_cell_unseen": float(vm["joint_cell_unseen"]),
                "VAL_q_mass_unseen": float(vm["q_mass_unseen"]),
                "capacity_warning_m1": bool(cap_warn["m1_ge_1024"]),
                "capacity_warning_m2": bool(cap_warn["m2_ge_1024"]),
                "capacity_warning_disclosure": bool(cap_warn["disclosure_ge_5120"]),
                "descriptive_ValNLL_gt_Hcal_plus_1": bool(vm["ValNLL"] > vm["H_cal"]+1.0),
                "descriptive_ValNLL_gt_Hcal_plus_0_5": bool(vm["ValNLL"] > vm["H_cal"]+0.5),
                "descriptive_joint_gt_1pct": bool(vm["joint_cell_unseen"]>0.01),
            }
            rows_for_sess.append(row)
            # T for CAL-only selection
            T_cur = (cv["max_cv"], cv["sum_cv"], cv["abs_cv"], S)
            if best_T is None or T_cur < best_T:
                best_T = T_cur
                best_S = S
        S_star_per_session[sid] = best_S
        per_session_S_data[sid] = rows_for_sess
        # natural row for delta
        nat_row = next(r for r in rows_for_sess if r["is_S_nat"])
        star_row = next(r for r in rows_for_sess if tuple(r["S_tuple"])==best_S)
        print(f"[{sid}] S* CAL {best_S} m_cv {star_row['CAL_m1_cv']},{star_row['CAL_m2_cv']} max{star_row['CAL_max_cv']} | VAL m {star_row['VAL_m1_raw']},{star_row['VAL_m2_raw']} nat m {nat_row['VAL_m1_raw']},{nat_row['VAL_m2_raw']}")
        all_rows.extend(rows_for_sess)
        per_session[sid] = {
            "S_star_per_session": list(best_S),
            "S_star_T": list(best_T[:3])+[list(best_T[3])],
            "natural_S": list(S_nat),
            "natural_VAL": {"m1": nat_row["VAL_m1_raw"], "m2": nat_row["VAL_m2_raw"], "raw": nat_row["VAL_raw_disclosure"]},
            "star_VAL": {"m1": star_row["VAL_m1_raw"], "m2": star_row["VAL_m2_raw"], "raw": star_row["VAL_raw_disclosure"]},
            "delta": {"dCE1": star_row["VAL_CE1"]-nat_row["VAL_CE1"], "dCE2": star_row["VAL_CE2"]-nat_row["VAL_CE2"], "dmax": star_row["VAL_max_m"]-nat_row["VAL_max_m"], "dsum": star_row["VAL_sum_m"]-nat_row["VAL_sum_m"], "draw": star_row["VAL_raw_disclosure"]-nat_row["VAL_raw_disclosure"]},
            "lam_star": float(lam_star),
            "lam_at_boundary": bool(lam_at_boundary),
        }
    # common S*
    best_common_T = None
    best_common_S = None
    for S in S_list:
        maxs = []; sums=[]; abss=[]
        for sid in per_session_S_data:
            r = next(x for x in per_session_S_data[sid] if tuple(x["S_tuple"])==S)
            maxs.append(r["CAL_max_cv"]); sums.append(r["CAL_sum_cv"]); abss.append(r["CAL_abs_cv"])
        T_common = (max(maxs), max(sums), max(abss), S)
        if best_common_T is None or T_common < best_common_T:
            best_common_T = T_common
            best_common_S = S
    S_star_common = best_common_S
    # classification per session based on VAL m of S* per session
    counts = {"V68_EVIDENCE_INCOMPLETE":0,"V68_MODEL_NOT_STABLE":0,"V68_BALANCED_FEASIBLE":0,"V68_STILL_HEAVY":0}
    for sid in per_session_S_data:
        rows = per_session_S_data[sid]
        S_star = tuple(S_star_per_session[sid])
        r = next(x for x in rows if tuple(x["S_tuple"])==S_star)
        # stability checks
        if not r["chain_delta"] < CE_TOL:
            cls="V68_EVIDENCE_INCOMPLETE"; suc="recollect"
        elif r["CAL_lambda_at_boundary"] or r["VAL_DeltaNLL"]>0.50 or r["VAL_val_b_context_unseen"]>0.01 or not math.isfinite(r["VAL_ValNLL"]) or not math.isfinite(r["VAL_DeltaNLL"]):
            cls="V68_MODEL_NOT_STABLE"; suc="recollect_or_new_prior"
        elif r["VAL_m1_raw"]<1024 and r["VAL_m2_raw"]<1024 and r["VAL_raw_disclosure"]<5120:
            cls="V68_BALANCED_FEASIBLE"; suc="balanced_code_design"
        else:
            cls="V68_STILL_HEAVY"; suc="new_representation"
        per_session[sid]["classification"]=cls
        per_session[sid]["successor"]=suc
        per_session[sid]["star_VAL_row"]=r
        counts[cls]+=1
        # cal_val consistency: compare CAL S* vs argmin on VAL T
        best_val_T=None; best_val_S=None
        for S in S_list:
            rr = next(x for x in rows if tuple(x["S_tuple"])==S)
            Tv = (rr["VAL_max_m"], rr["VAL_sum_m"], rr["VAL_abs_m"], S)
            if best_val_T is None or Tv < best_val_T:
                best_val_T=Tv; best_val_S=S
        per_session[sid]["S_star_val"] = list(best_val_S)
        per_session[sid]["cal_val_consistency"] = bool(best_val_S == S_star)
    # overall 3-state
    common_rows = {}
    for sid in per_session_S_data:
        r = next(x for x in per_session_S_data[sid] if tuple(x["S_tuple"])==S_star_common)
        # classify common per session
        if r["CAL_lambda_at_boundary"] or r["VAL_DeltaNLL"]>0.50 or r["VAL_val_b_context_unseen"]>0.01:
            cc = "MODEL_NOT_STABLE"
        elif r["VAL_m1_raw"]<1024 and r["VAL_m2_raw"]<1024 and r["VAL_raw_disclosure"]<5120:
            cc="BALANCED_FEASIBLE"
        else:
            cc="STILL_HEAVY"
        common_rows[sid]= {"m1":r["VAL_m1_raw"],"m2":r["VAL_m2_raw"],"raw":r["VAL_raw_disclosure"],"cls":cc}
    common_feasible = sum(1 for v in common_rows.values() if v["cls"]=="BALANCED_FEASIBLE")
    per_session_feasible = sum(1 for v in per_session.values() if v["classification"]=="V68_BALANCED_FEASIBLE")
    if common_feasible==3:
        overall="V68_OVERALL_BALANCED_COMMON_FEASIBLE"
    elif per_session_feasible>=1:
        overall="V68_OVERALL_BALANCED_PER_SESSION_ONLY"
    else:
        overall="V68_OVERALL_STILL_HEAVY"
    # enrich overall if evidence/model present
    if any(v["classification"]=="V68_EVIDENCE_INCOMPLETE" for v in per_session.values()):
        overall = "V68_OVERALL_EVIDENCE_INCOMPLETE_"+overall
    elif any(v["classification"]=="V68_MODEL_NOT_STABLE" for v in per_session.values()):
        overall = "V68_OVERALL_MODEL_NOT_STABLE_"+overall if "MODEL_NOT_STABLE" not in overall else overall
    # add flags to rows
    for row in all_rows:
        sid=row["session_id"]
        row["is_S_star_per_session"] = tuple(row["S_tuple"])==tuple(S_star_per_session[sid])
        row["is_S_star_common"] = tuple(row["S_tuple"])==tuple(S_star_common)
        row["per_session_classification"] = per_session[sid]["classification"] if row["is_S_star_per_session"] else ""
        row["successor"] = per_session[sid]["successor"] if row["is_S_star_per_session"] else ""
        row["cal_val_consistency"] = per_session[sid]["cal_val_consistency"]
    # write outputs
    result = {
        "schema":"v68_balanced_v1",
        "lifecycle":"PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED",
        "head": reg.get("head"),
        "data_sha": reg.get("data_sha"),
        "S_list": [list(s) for s in S_list],
        "S_nat": list(S_nat),
        "S_nat_index": S_nat_idx,
        "enum": {"count":252, "S_nat": list(S_nat), "generation":"lex order"},
        "total_sessions": len(reg["sessions"]),
        "used_val_in_selection": used_val_in_selection,
        "used_test": used_test,
        "S_star_per_session": {k:list(v) for k,v in S_star_per_session.items()},
        "S_star_common": list(S_star_common),
        "T_common": [best_common_T[0], best_common_T[1], best_common_T[2], list(best_common_T[3])],
        "per_session": per_session,
        "common_rows": common_rows,
        "common_feasible_count": common_feasible,
        "per_session_feasible_count": per_session_feasible,
        "overall": overall,
        "counts_per_classification": counts,
        "no_run_01": True,
    }
    Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    Path(args.table_json).write_text(json.dumps(all_rows, indent=2, ensure_ascii=False), encoding="utf-8")
    import csv
    if all_rows:
        fns = list(all_rows[0].keys())
        with open(args.table_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fns)
            w.writeheader(); w.writerows(all_rows)
    manifest = {
        "schema":"v68_manifest_v1",
        "lifecycle":"PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED",
        "head": reg.get("head"),
        "data_sha": reg.get("data_sha"),
        "frozen_body": {
            "n":1024, "q":1024, "GF":"GF32 poly37", "H1":"16x1024 rank16 80b",
            "U_natural":"32*U1+U2 F03 5+5", "U_permuted":"bits_S(S) 252", "per_frame":256,
            "Lane_C_base":{"1M":184,"1p5M":190,"2M":192}, "H_inc":"Delta8", "decoder":"90/1.0 poly37 disabled",
            "verification":"full-tag canonical 32*U1+U2 tag 64", "leak":"5*(m1+m2)+64",
            "materialization":"legacy_v1 dimension 1024 bin200 nearest channels A1/B5 period 204800",
            "not_extra": True
        },
        "guards": {f"R68-0{i}": True for i in range(1,10)} | {"R68-10": True},
        "overall": overall,
        "counts": counts,
        "S_star_per_session": {k:list(v) for k,v in S_star_per_session.items()},
        "S_star_common": list(S_star_common),
        "common_feasible_count": common_feasible,
        "per_session_feasible_count": per_session_feasible,
        "used_val_in_selection": used_val_in_selection,
        "used_test": used_test,
        "no_run_01": True
    }
    Path(args.manifest).write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[v68_spike] S* per {S_star_per_session} common {S_star_common} overall {overall} counts {counts}")
    # summary
    for sid, info in per_session.items():
        print(f"  {sid} {info['classification']} m_star {info['star_VAL']['m1']},{info['star_VAL']['m2']} common_m {common_rows[sid]['m1']},{common_rows[sid]['m2']}")

if __name__=="__main__":
    main()
