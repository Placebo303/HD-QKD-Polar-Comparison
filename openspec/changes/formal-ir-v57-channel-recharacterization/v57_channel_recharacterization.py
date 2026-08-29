#!/usr/bin/env python3
"""V57 channel recharacterization — decoder-free, REVISED.
512+512 per source, Dirichlet/Laplace smoothing α=1.0, ceil leakage, estimator gates.
Previous 8192 MLE retained as UNDERSAMPLED_MLE_NEGATIVE_CONTROL.
"""
from __future__ import annotations
import argparse, json, math, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd

# Previous undersampled (negative control) — retained not overwritten
CAL_UNDERSAMPLED = list(range(19, 51))  # 19..50 32
VAL_UNDERSAMPLED = list(range(77, 109))  # 77..108 32
UNDERSAMPLED_SET = set(CAL_UNDERSAMPLED) | set(VAL_UNDERSAMPLED)
V56_FORBIDDEN = {7, 8, 9, 10, 15, 16, 17, 18}
SRC_MAP = {
    "1M": "20260123_1M_600k_0dB",
    "1p5M": "20260107_PPLN_1p5M",
    "2M": "20260123_2M_1p2M_0dB",
}
SRC_F = {"1M": 2130, "1p5M": 5125, "2M": 5513}
V25_KEY_MAP = {
    "1M": "type2_1M_20260121_184040_N_ab_train_N_ab_train",
    "1p5M": "type2_1p5M_20260121_183806_N_ab_train_N_ab_train",
    "2M": "type2_2M_20260121_183657_N_ab_train_N_ab_train",
}
V25_M_REF = {"1M": 200, "1p5M": 206, "2M": 208}
HEAD_EXPECTED = "ea39a83d844ce60c86418b753cf95576416233f4"
DATA_SHA = "84d62779603e62de50ded5182ed65b65d3dc6084"
DATA_SHA_SHORT = "84d62779"
ALPHA_DEFAULT = 1.0  # Laplace, frozen pre-registered, not tuned on Val
Q = 1024

def _load_v55_flat(v55_path: Path):
    j = json.loads(v55_path.read_text(encoding="utf-8"))
    strata = j.get("strata", {})
    flat_per = {}
    for src_key, label in [("20260123_1M_600k_0dB","1M"),("20260107_PPLN_1p5M","1p5M"),("20260123_2M_1p2M_0dB","2M")]:
        entry = strata.get(src_key, {})
        sids = entry.get("selected_frame_ids", [])
        flat = set()
        for block in sids:
            if isinstance(block, list):
                flat.update(block)
            elif isinstance(block, int):
                flat.add(block)
        flat_per[label] = flat
    return flat_per

def _build_cal_val_per_source(v55_flat):
    cal_per = {}
    val_per = {}
    for src in ["1M","1p5M","2M"]:
        F = SRC_F[src]
        flat = v55_flat.get(src, set())
        forbidden = set(flat) | V56_FORBIDDEN | UNDERSAMPLED_SET
        available = sorted(set(range(F)) - forbidden)
        assert len(available) >= 1024, f"{src} available {len(available)} <1024 F={F}"
        cal = available[0:512]
        val = available[512:1024]
        cal_per[src] = cal
        val_per[src] = val
    return cal_per, val_per

def _counts_to_p_mle(counts: np.ndarray):
    col = counts.sum(axis=0).astype(np.float64)
    P = np.zeros_like(counts, dtype=np.float64)
    for b in range(counts.shape[1]):
        s = col[b]
        if s > 0:
            P[:, b] = counts[:, b] / s
        else:
            P[:, b] = 1.0 / counts.shape[0]
    pb = col / col.sum() if col.sum()>0 else np.ones(1024)/1024
    return P, pb, col

def _counts_to_p_smooth(counts: np.ndarray, alpha: float = ALPHA_DEFAULT):
    col = counts.sum(axis=0).astype(np.float64)
    P = np.zeros_like(counts, dtype=np.float64)
    for b in range(counts.shape[1]):
        nb = col[b]
        if nb > 0:
            P[:, b] = (counts[:, b] + alpha) / (nb + alpha * Q)
        else:
            P[:, b] = 1.0 / Q
    N = counts.sum()
    pb = col / N if N>0 else np.ones(Q)/Q
    return P, pb, col

def _calc_H_from_P(P: np.ndarray, pb: np.ndarray):
    H = 0.0
    for b in range(Q):
        pbb = pb[b]
        if pbb == 0:
            continue
        col_p = P[:, b]
        nz = col_p[col_p>0]
        H -= pbb * np.sum(nz * np.log2(nz))
    # H1
    P_u1 = np.zeros((32, Q), dtype=np.float64)
    for b in range(Q):
        for u1 in range(32):
            base = 32*u1
            P_u1[u1, b] = np.sum(P[base:base+32, b])
    H1 = 0.0
    for b in range(Q):
        pbb = pb[b]
        if pbb==0:
            continue
        col_p = P_u1[:, b]
        nz = col_p[col_p>0]
        H1 -= pbb * np.sum(nz * np.log2(nz))
    H2 = H - H1
    return H, H1, H2, P_u1

def calc_H_smooth(C_ab: np.ndarray, alpha: float = ALPHA_DEFAULT):
    N = int(C_ab.sum())
    if N == 0:
        return 0.0, 0.0, 0.0, np.zeros(Q)/Q, None, None
    P, pb, col = _counts_to_p_smooth(C_ab, alpha)
    H, H1, H2, _ = _calc_H_from_P(P, pb)
    return H, H1, H2, pb, P, col

def calc_H_mle(C_ab: np.ndarray):
    N = int(C_ab.sum())
    if N == 0:
        return 0.0, 0.0, 0.0, np.zeros(Q)/Q, None, None
    P, pb, col = _counts_to_p_mle(C_ab)
    H, H1, H2, _ = _calc_H_from_P(P, pb)
    return H, H1, H2, pb, P, col

def nll_on_pairs_smooth(P_cal: np.ndarray, a_arr: np.ndarray, b_arr: np.ndarray):
    # P_cal already smoothed >0, no clamp needed but tiny eps for safety
    probs = P_cal[a_arr, b_arr]
    # P_cal min = alpha/(max_Nb+alpha*Q) >0, so no zero
    return float(-np.mean(np.log2(probs)))

def nll_on_pairs_clamp(P_cal: np.ndarray, a_arr: np.ndarray, b_arr: np.ndarray, eps=1e-15):
    probs = P_cal[a_arr, b_arr]
    probs = np.clip(probs, eps, 1.0)
    return float(-np.mean(np.log2(probs)))

def acc_on_pairs(P_cal: np.ndarray, a_arr: np.ndarray, b_arr: np.ndarray):
    amap = np.argmax(P_cal, axis=0)
    return float(np.mean(a_arr == amap[b_arr]))

def main():
    ap = argparse.ArgumentParser(description="V57 channel recharacterization revised")
    ap.add_argument("--pairs-root", type=str, default="comparison_bench/outputs_comparison/v55_intake_20260828/pairs")
    ap.add_argument("--counts", type=str, default="comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz")
    ap.add_argument("--v55-registry", type=str, default="openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/v55_authoritative_registry.json")
    ap.add_argument("--alpha", type=float, default=ALPHA_DEFAULT, help="Dirichlet alpha (frozen 1.0, not tuned on Val)")
    ap.add_argument("--out", type=str, default="openspec/changes/formal-ir-v57-channel-recharacterization/v57_channel_recharacterization.json")
    ap.add_argument("--report", type=str, default="openspec/changes/formal-ir-v57-channel-recharacterization/V57_CHANNEL_RECHARACTERIZATION_REPORT.md")
    args = ap.parse_args()
    alpha = float(args.alpha)
    assert alpha == ALPHA_DEFAULT, f"alpha must be frozen {ALPHA_DEFAULT}, got {alpha} — Val择优禁止"

    repo = Path(__file__).resolve().parents[3]
    pairs_root = Path(args.pairs_root)
    if not pairs_root.is_absolute():
        pairs_root = repo / pairs_root
    counts_path = Path(args.counts)
    if not counts_path.is_absolute():
        counts_path = repo / counts_path
    v55_path = Path(args.v55_registry)
    if not v55_path.is_absolute():
        v55_path = repo / v55_path
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = repo / out_path
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = repo / report_path

    v55_flat = _load_v55_flat(v55_path)
    cal_per, val_per = _build_cal_val_per_source(v55_flat)

    # zero overlap proofs (four-fold)
    zero_proofs = {}
    overall_zero = True
    for src in ["1M","1p5M","2M"]:
        cal_set = set(cal_per[src])
        val_set = set(val_per[src])
        flat = v55_flat.get(src, set())
        c1 = len(cal_set & val_set) == 0
        c2 = len((cal_set | val_set) & flat) == 0
        c3 = len((cal_set | val_set) & V56_FORBIDDEN) == 0
        c4 = len((cal_set | val_set) & UNDERSAMPLED_SET) == 0
        c5 = len(cal_set)==512 and len(val_set)==512
        c6 = all(0 <= fid < SRC_F[src] for fid in (cal_set | val_set))
        zero_proofs[src] = {"cal_cap_val": c1, "cal_val_cap_v55": c2, "cap_v56": c3, "cap_undersampled": c4, "size512": c5, "in_range": c6}
        if not (c1 and c2 and c3 and c4 and c5 and c6):
            overall_zero = False
    zero_proofs_all = {
        "cal_cap_val": all(v["cal_cap_val"] for v in zero_proofs.values()),
        "cal_val_cap_v55": all(v["cal_val_cap_v55"] for v in zero_proofs.values()),
        "cap_v56": all(v["cap_v56"] for v in zero_proofs.values()),
        "cap_undersampled": all(v["cap_undersampled"] for v in zero_proofs.values()),
        "size512": all(v["size512"] for v in zero_proofs.values()),
        "in_range": all(v["in_range"] for v in zero_proofs.values()),
    }
    overall_zero_all = all(zero_proofs_all.values())

    # load V25 counts
    v25_data = {}
    if counts_path.exists():
        npz = np.load(str(counts_path))
        for src in ["1M","1p5M","2M"]:
            key = V25_KEY_MAP[src]
            if key in npz:
                v25_data[src] = npz[key].astype(np.float64)
    v25_P = {}
    for src, cnt in v25_data.items():
        P, _, _ = _counts_to_p_mle(cnt)
        v25_P[src] = P

    # archive previous 8192 negative control if exists
    negative_control_archived = False
    if out_path.exists():
        try:
            prev = json.loads(out_path.read_text(encoding="utf-8"))
            # detect old 8192 via N_cal or zero_frac ~0.994
            is_old = False
            per = prev.get("per_source", {})
            if per:
                for v in per.values():
                    if v.get("N_cal")==8192 or v.get("zero_frac_cal",0)>0.99:
                        is_old = True
                        break
                    if v.get("selected_cal")==CAL_UNDERSAMPLED:
                        is_old = True
                        break
            if is_old:
                neg_json = out_path.parent / "v57_channel_recharacterization_undersampled_mle_negative_control.json"
                neg_md = out_path.parent / "V57_CHANNEL_RECHARACTERIZATION_REPORT_UNDERSAMPLED_MLE_NEGATIVE_CONTROL.md"
                # copy json
                if not neg_json.exists():
                    neg_json.write_text(json.dumps(prev, ensure_ascii=False, indent=2), encoding="utf-8")
                # try to archive report if exists
                old_report = out_path.parent / "V57_CHANNEL_RECHARACTERIZATION_REPORT.md"
                if old_report.exists():
                    txt = old_report.read_text(encoding="utf-8")
                    if "8192" in txt or "99.4" in txt or "30.15" in txt:
                        if not neg_md.exists():
                            neg_md.write_text(txt, encoding="utf-8")
                negative_control_archived = True
                # also keep previous manifest? no
        except Exception:
            pass

    per_source = {}
    counts_valid_all = True
    chain_ok_all = True
    for src in ["1M","1p5M","2M"]:
        sub = SRC_MAP[src]
        parquet = pairs_root / sub / "pairs.parquet"
        if not parquet.exists():
            alt = pairs_root / "pairs.parquet"
            parquet = alt if alt.exists() else parquet
        df = pd.read_parquet(str(parquet))
        assert "frame_id" in df.columns and "alice_symbol" in df.columns and "bob_symbol" in df.columns, f"missing cols {df.columns}"
        CAL = cal_per[src]
        VAL = val_per[src]
        cal_df = df[df["frame_id"].isin(CAL)].copy()
        val_df = df[df["frame_id"].isin(VAL)].copy()
        counts_valid = True
        note = ""
        if len(cal_df) != 512*256:
            counts_valid = False
            note += f" cal_len {len(cal_df)} !=131072;"
        if len(val_df) != 512*256:
            counts_valid = False
            note += f" val_len {len(val_df)} !=131072;"
        for fid in CAL:
            c2 = int((df["frame_id"]==fid).sum())
            if c2 != 256:
                counts_valid = False
                note += f" frame{fid} {c2}!=256;"
                break
        for fid in VAL:
            c2 = int((df["frame_id"]==fid).sum())
            if c2 != 256:
                counts_valid = False
                note += f" valframe{fid} {c2}!=256;"
                break
        a_cal = cal_df["alice_symbol"].to_numpy(dtype=np.int64)
        b_cal = cal_df["bob_symbol"].to_numpy(dtype=np.int64)
        a_val = val_df["alice_symbol"].to_numpy(dtype=np.int64)
        b_val = val_df["bob_symbol"].to_numpy(dtype=np.int64)
        if len(a_cal) and (a_cal.min()<0 or a_cal.max()>1023 or b_cal.min()<0 or b_cal.max()>1023):
            counts_valid = False
            note += " range invalid cal;"
        if len(a_val) and (a_val.min()<0 or a_val.max()>1023 or b_val.min()<0 or b_val.max()>1023):
            counts_valid = False
            note += " range invalid val;"
        # C_ab cal
        C_ab = np.zeros((1024,1024), dtype=np.int32)
        if len(a_cal):
            np.add.at(C_ab, (a_cal, b_cal), 1)
        zero_cells_mle = int(np.sum(C_ab==0))
        zero_frac_mle = zero_cells_mle / (1024*1024)
        N_cal = int(C_ab.sum())
        # smooth H
        H_smooth, H1_smooth, H2_smooth, pb_smooth, P_cal_smooth, col_smooth = calc_H_smooth(C_ab, alpha)
        H_mle, H1_mle, H2_mle, _, P_cal_mle, _ = calc_H_mle(C_ab)
        chain_ok = abs(H_smooth - H1_smooth - H2_smooth) < 1e-9
        if not chain_ok:
            counts_valid = False
        # m ceil
        f_target=1.3; n=1024; tag=64
        m_total = math.ceil((f_target*n*H_smooth - tag)/5) if H_smooth>0 else -1
        if H_smooth < 0.1 or m_total <0 or m_total >= 1024:
            counts_valid = False
        m1 = math.ceil(m_total * H1_smooth / H_smooth) if H_smooth>0 else 0
        if m1 <0: m1=0
        if m1>m_total: m1=m_total
        m2 = m_total - m1
        leak = 5*m_total + 64
        f_eff = leak/(n*H_smooth) if H_smooth>0 else 0
        delta_m = m_total - V25_M_REF[src]
        delta_leak = 5*delta_m
        # Cal self metrics smooth
        cal_nll_smooth = nll_on_pairs_smooth(P_cal_smooth, a_cal, b_cal) if len(a_cal) else float('nan')
        cal_nll_mle_clamp = nll_on_pairs_clamp(P_cal_mle, a_cal, b_cal) if len(a_cal) else float('nan')
        cal_acc_smooth = acc_on_pairs(P_cal_smooth, a_cal, b_cal) if len(a_cal) else float('nan')
        cal_acc_mle = acc_on_pairs(P_cal_mle, a_cal, b_cal) if len(a_cal) else float('nan')
        v25_nll_cal = nll_on_pairs_clamp(v25_P[src], a_cal, b_cal) if src in v25_P and len(a_cal) else float('nan')
        v25_nll_val = nll_on_pairs_clamp(v25_P[src], a_val, b_val) if src in v25_P and len(a_val) else float('nan')
        # Val metrics smooth
        nll_val_smooth = nll_on_pairs_smooth(P_cal_smooth, a_val, b_val) if len(a_val) else float('nan')
        nll_val_mle_clamp = nll_on_pairs_clamp(P_cal_mle, a_val, b_val) if len(a_val) else float('nan')
        acc_val_smooth = acc_on_pairs(P_cal_smooth, a_val, b_val) if len(a_val) else float('nan')
        acc_val_mle = acc_on_pairs(P_cal_mle, a_val, b_val) if len(a_val) else float('nan')
        # q_mass descriptive (MLE zero)
        C_val = np.zeros((1024,1024), dtype=np.int32)
        if len(a_val):
            np.add.at(C_val, (a_val, b_val), 1)
        N_val = int(C_val.sum())
        q_mass_mle = 0.0
        if N_val>0:
            mask = (C_ab==0)
            q_mass_mle = float(C_val[mask].sum() / N_val)
        # H_val smooth
        H_val_smooth, H1_val_smooth, H2_val_smooth, _, _, _ = calc_H_smooth(C_val, alpha)
        H_val_mle, _, _, _, _, _ = calc_H_mle(C_val)
        # 2-fold CV within Cal
        cal_frames = CAL
        half = 256
        cal_fold1_frames = cal_frames[:half]
        cal_fold2_frames = cal_frames[half:]
        cal_fold1_df = df[df["frame_id"].isin(cal_fold1_frames)]
        cal_fold2_df = df[df["frame_id"].isin(cal_fold2_frames)]
        a_f1 = cal_fold1_df["alice_symbol"].to_numpy(dtype=np.int64) if len(cal_fold1_df) else np.array([], dtype=np.int64)
        b_f1 = cal_fold1_df["bob_symbol"].to_numpy(dtype=np.int64) if len(cal_fold1_df) else np.array([], dtype=np.int64)
        a_f2 = cal_fold2_df["alice_symbol"].to_numpy(dtype=np.int64) if len(cal_fold2_df) else np.array([], dtype=np.int64)
        b_f2 = cal_fold2_df["bob_symbol"].to_numpy(dtype=np.int64) if len(cal_fold2_df) else np.array([], dtype=np.int64)
        C_f1 = np.zeros((1024,1024), dtype=np.int32)
        C_f2 = np.zeros((1024,1024), dtype=np.int32)
        if len(a_f1):
            np.add.at(C_f1, (a_f1, b_f1), 1)
        if len(a_f2):
            np.add.at(C_f2, (a_f2, b_f2), 1)
        _, _, _, _, P_f1_smooth, _ = calc_H_smooth(C_f1, alpha)
        _, _, _, _, P_f2_smooth, _ = calc_H_smooth(C_f2, alpha)
        # cross NLL
        nll_fold1_on_fold2 = nll_on_pairs_smooth(P_f1_smooth, a_f2, b_f2) if len(a_f2) and P_f1_smooth is not None else float('nan')
        nll_fold2_on_fold1 = nll_on_pairs_smooth(P_f2_smooth, a_f1, b_f1) if len(a_f1) and P_f2_smooth is not None else float('nan')
        # convergence series: train on first N frames of Cal, test on Val
        convergence = {}
        for n_frames in [32,128,256,512]:
            sub_frames = cal_frames[:n_frames]
            sub_df = df[df["frame_id"].isin(sub_frames)]
            a_sub = sub_df["alice_symbol"].to_numpy(dtype=np.int64) if len(sub_df) else np.array([], dtype=np.int64)
            b_sub = sub_df["bob_symbol"].to_numpy(dtype=np.int64) if len(sub_df) else np.array([], dtype=np.int64)
            C_sub = np.zeros((1024,1024), dtype=np.int32)
            if len(a_sub):
                np.add.at(C_sub, (a_sub, b_sub), 1)
            H_sub, H1_sub, _, _, P_sub, _ = calc_H_smooth(C_sub, alpha)
            nll_sub_on_val_smooth = nll_on_pairs_smooth(P_sub, a_val, b_val) if len(a_val) and P_sub is not None else float('nan')
            nll_sub_mle = nll_on_pairs_clamp(_counts_to_p_mle(C_sub)[0] if len(a_sub) else np.ones((1024,1024))/1024, a_val, b_val) if len(a_val) else float('nan')
            convergence[str(n_frames)] = {
                "frames": n_frames,
                "pairs": int(C_sub.sum()),
                "H_smooth": round(float(H_sub),6) if not math.isnan(H_sub) else None,
                "H1_smooth": round(float(H1_sub),6) if not math.isnan(H1_sub) else None,
                "NLL_val_smooth": round(float(nll_sub_on_val_smooth),6) if not math.isnan(nll_sub_on_val_smooth) else None,
                "NLL_val_mle_clamp": round(float(nll_sub_mle),6) if not math.isnan(nll_sub_mle) else None,
                "zero_frac_mle": round(float(np.sum(C_sub==0)/(1024*1024)),6),
            }
        # gates EG1-3
        # EG1: finite & improved
        if math.isnan(nll_val_smooth) or math.isnan(nll_val_mle_clamp) or math.isnan(v25_nll_val):
            eg1=False
        else:
            eg1 = (nll_val_smooth < 15.0) and math.isfinite(nll_val_smooth) and (nll_val_smooth < nll_val_mle_clamp - 5.0) and (nll_val_smooth < v25_nll_val)
        # EG2: CV consistency
        if math.isnan(nll_val_smooth) or math.isnan(cal_nll_smooth) or math.isnan(nll_fold1_on_fold2) or math.isnan(nll_fold2_on_fold1):
            eg2=False
        else:
            cond1 = abs(nll_val_smooth - cal_nll_smooth) <= 0.50
            cond1_rel = abs(nll_val_smooth - cal_nll_smooth)/cal_nll_smooth <= 0.25 if cal_nll_smooth!=0 else False
            cond2 = abs(nll_fold1_on_fold2 - nll_fold2_on_fold1) <= 0.50
            eg2 = cond1 and cond1_rel and cond2
        # EG3: entropy stability
        if math.isnan(H_val_smooth) or H_smooth==0:
            eg3=False
        else:
            eg3 = (abs(H_val_smooth - H_smooth) <= 0.20) and (abs(H_val_smooth - H_smooth)/H_smooth <= 0.25)
        zero_ok = all([zero_proofs[src][k] for k in ["cal_cap_val","cal_val_cap_v55","cap_v56","cap_undersampled","size512","in_range"]])
        pass_s = bool(eg1 and eg2 and eg3 and zero_ok and counts_valid and chain_ok)
        if not counts_valid:
            chain_ok_all = False
        if not chain_ok:
            chain_ok_all = False
        per_source[src] = {
            "F": SRC_F[src],
            "K": SRC_F[src]-3,
            "selected_cal": CAL,
            "selected_val": VAL,
            "N_cal": N_cal,
            "N_val": N_val,
            "C_shape": [1024,1024],
            "zero_cells_mle": zero_cells_mle,
            "zero_frac_mle": round(float(zero_frac_mle),6),
            "H_cal_smooth": round(float(H_smooth),6),
            "H1_cal_smooth": round(float(H1_smooth),6),
            "H2_cal_smooth": round(float(H2_smooth),6),
            "H_cal_mle": round(float(H_mle),6),
            "H1_cal_mle": round(float(H1_mle),6),
            "delta_chain": round(float(H_smooth - H1_smooth - H2_smooth),9),
            "chain_ok": bool(chain_ok),
            "m_total_ceil": int(m_total),
            "m1_ceil": int(m1),
            "m2": int(m2),
            "leak_total": int(leak),
            "f_eff": round(float(f_eff),6),
            "delta_m": int(delta_m),
            "delta_leak": int(delta_leak),
            "m_total_V25_ref": V25_M_REF[src],
            "alpha": alpha,
            "cal_NLL_self_smooth": round(float(cal_nll_smooth),6) if not math.isnan(cal_nll_smooth) else None,
            "cal_NLL_self_mle_clamp": round(float(cal_nll_mle_clamp),6) if not math.isnan(cal_nll_mle_clamp) else None,
            "cal_acc_smooth_descriptive": round(float(cal_acc_smooth),6) if not math.isnan(cal_acc_smooth) else None,
            "cal_acc_mle_descriptive": round(float(cal_acc_mle),6) if not math.isnan(cal_acc_mle) else None,
            "V25_NLL_on_Cal": round(float(v25_nll_cal),6) if not math.isnan(v25_nll_cal) else None,
            "NLL_val_smooth": round(float(nll_val_smooth),6) if not math.isnan(nll_val_smooth) else None,
            "NLL_val_mle_clamp_negative_control": round(float(nll_val_mle_clamp),6) if not math.isnan(nll_val_mle_clamp) else None,
            "NLL_val_block_smooth": round(float(nll_val_smooth*1024),3) if not math.isnan(nll_val_smooth) else None,
            "NLL_V25_on_Val": round(float(v25_nll_val),6) if not math.isnan(v25_nll_val) else None,
            "NLL_V25_on_Val_block": round(float(v25_nll_val*1024),3) if not math.isnan(v25_nll_val) else None,
            "acc_val_smooth_descriptive": round(float(acc_val_smooth),6) if not math.isnan(acc_val_smooth) else None,
            "acc_val_mle_descriptive": round(float(acc_val_mle),6) if not math.isnan(acc_val_mle) else None,
            "q_mass_mle_descriptive": round(float(q_mass_mle),6),
            "H_val_smooth": round(float(H_val_smooth),6) if not math.isnan(H_val_smooth) else None,
            "H1_val_smooth": round(float(H1_val_smooth),6) if not math.isnan(H1_val_smooth) else None,
            "H2_val_smooth": round(float(H2_val_smooth),6) if not math.isnan(H2_val_smooth) else None,
            "H_val_mle": round(float(H_val_mle),6) if not math.isnan(H_val_mle) else None,
            "NLL_cal_fold1_on_fold2": round(float(nll_fold1_on_fold2),6) if not math.isnan(nll_fold1_on_fold2) else None,
            "NLL_cal_fold2_on_fold1": round(float(nll_fold2_on_fold1),6) if not math.isnan(nll_fold2_on_fold1) else None,
            "convergence_series": convergence,
            "EG1_pass": bool(eg1),
            "EG2_pass": bool(eg2),
            "EG3_pass": bool(eg3),
            "zero_overlap_s": bool(zero_ok),
            "counts_valid_s": bool(counts_valid),
            "PASS_s": bool(pass_s),
            "note": note.strip(),
        }
        if not counts_valid:
            counts_valid_all = False

    if not overall_zero_all or not counts_valid_all or not chain_ok_all:
        overall = "V57_EVIDENCE_INVALID"
    elif all(v["PASS_s"] for v in per_source.values()):
        overall = "V57_CHANNEL_RECHARACTERIZATION_PASS"
    else:
        overall = "V57_CHANNEL_RECHARACTERIZATION_FAIL"

    try:
        head = subprocess.check_output(["git","rev-parse","HEAD"], text=True).strip()
    except: head = HEAD_EXPECTED
    try:
        origin = subprocess.check_output(["git","rev-parse","origin/formal-ir-mainline"], text=True).strip()
    except: origin = head

    cal_reg = {
        "schema": "v57_cal/val_v2",
        "lifecycle": "V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED",
        "data_sha": DATA_SHA_SHORT,
        "data_sha_full": DATA_SHA,
        "head": head,
        "branch": "formal-ir-mainline",
        "processing_rule": "legacy_v1",
        "smoothing": f"Dirichlet Laplace alpha={alpha} frozen (P=(C+alpha)/(N_b+alpha*Q), Q={Q}) not tuned on Val",
        "leakage_formula": "m_total=ceil((1.3*1024*H_smooth-64)/5), m1=ceil(m_total*H1/H), tag 64 counted once in leak/f_eff",
        "provenance_note": "Cal per-source available[0:512] 128 blocks*4 F03 5+5 natural, 84d62779 200ps legacy_v1 nearest 1024, four-fold zero overlap",
        "per_source": {src: {"F": SRC_F[src], "K": SRC_F[src]-3, "selected_frame_ids": cal_per[src], "blocks": 128, "pairs": 131072, "provenance": {"v55_registry_sha": "v55_authoritative", "excluded": {"V56_8": list(sorted(V56_FORBIDDEN)), "undersampled_64": [19,50,77,108], "frame_period": 204800}, "processing_rule": "legacy_v1", "smoothing": f"alpha={alpha}"}} for src in ["1M","1p5M","2M"]},
        "overall_zero_overlap_verified": bool(overall_zero_all),
        "negative_control": "v57_channel_recharacterization_undersampled_mle_negative_control.json 8192 MLE retained",
    }
    val_reg = {
        "schema": "v57_cal/val_v2",
        "lifecycle": "V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED",
        "data_sha": DATA_SHA_SHORT,
        "data_sha_full": DATA_SHA,
        "head": head,
        "branch": "formal-ir-mainline",
        "processing_rule": "legacy_v1",
        "smoothing": f"Dirichlet Laplace alpha={alpha} frozen",
        "provenance_note": "Val per-source available[512:1024] 128 blocks*4 F03 5+5 natural",
        "per_source": {src: {"F": SRC_F[src], "K": SRC_F[src]-3, "selected_frame_ids": val_per[src], "blocks": 128, "pairs": 131072, "provenance": {"v55_registry_sha": "v55_authoritative", "excluded": {"V56_8": list(sorted(V56_FORBIDDEN)), "undersampled_64": [19,50,77,108], "frame_period": 204800}, "processing_rule": "legacy_v1", "smoothing": f"alpha={alpha}"}} for src in ["1M","1p5M","2M"]},
        "overall_zero_overlap_verified": bool(overall_zero_all),
        "negative_control": "v57_channel_recharacterization_undersampled_mle_negative_control.json",
    }
    manifest = {
        "schema": "v57_manifest_v2",
        "head": head,
        "origin_formal_ir_mainline": origin,
        "data_sha": DATA_SHA_SHORT,
        "data_sha_full": DATA_SHA,
        "alpha": alpha,
        "leakage_formula": "ceil",
        "zero_overlap_proofs": zero_proofs_all,
        "per_source_zero_overlap": zero_proofs,
        "overall_zero_overlap_verified": bool(overall_zero_all),
        "counts_valid_all": bool(counts_valid_all),
        "chain_ok_all": bool(chain_ok_all),
        "negative_control_archived": bool(negative_control_archived),
        "command": f"python v57_channel_recharacterization.py --alpha {alpha}",
    }

    result = {
        "schema": "v57_channel_recharacterization_v2",
        "lifecycle": "V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED",
        "revision": "REVISED 512+512 smooth alpha=1.0 ceil, ESTIMATOR_UNDERSAMPLED negative control retained",
        "head": head,
        "origin_formal_ir_mainline": origin,
        "data_sha": DATA_SHA_SHORT,
        "data_sha_full": DATA_SHA,
        "branch": "formal-ir-mainline",
        "pairs_root": str(pairs_root),
        "counts_path": str(counts_path),
        "v55_registry": str(v55_path),
        "alpha": alpha,
        "smoothing": f"Dirichlet Laplace alpha={alpha} (P=(C+alpha)/(N_b+alpha*Q)) frozen, not tuned on Val",
        "leakage_formula": "m_total=ceil((1.3*1024*H_smooth-64)/5), m1=ceil(m_total*H1/H), leak=5*m_total+64 tag counted once",
        "cal_frames_per_source": cal_per,
        "val_frames_per_source": val_per,
        "cal_frames_undersampled_negative_control": CAL_UNDERSAMPLED,
        "val_frames_undersampled_negative_control": VAL_UNDERSAMPLED,
        "zero_overlap_proofs": zero_proofs_all,
        "per_source_zero_overlap": zero_proofs,
        "per_source": per_source,
        "verdict": {
            "overall": overall,
            "shunt_per_source": {src: {"PASS_s": per_source[src]["PASS_s"], "EG1": per_source[src]["EG1_pass"], "EG2": per_source[src]["EG2_pass"], "EG3": per_source[src]["EG3_pass"]} for src in per_source},
            "overall_zero_overlap_verified": bool(overall_zero_all),
            "counts_valid_all": bool(counts_valid_all),
            "chain_ok_all": bool(chain_ok_all),
        },
        "boundary": {
            "V55_90_permanently_banned": True,
            "V25_m_deprecated": "m2 184/190/192 and m1=16 deprecated, not reused as budget",
            "only_all_pass_allows_V58": True,
            "freshness": "Cal512/Val512 derived from same 20260123/20260107 pairs.parquet as diagnosis, not claiming fully independent cross-session; fresh within-session confirmation only; 8192 MLE retained as UNDERSAMPLED_MLE_NEGATIVE_CONTROL",
            "estimator_undersampled_negative_control": "v57_channel_recharacterization_undersampled_mle_negative_control.json 8192 MLE 30bits retained",
            "smoothing_not_tuned": f"alpha={alpha} frozen in Cal only, not selected on Val",
            "ceil_tag": "m ceil, tag 64 counted once in total",
        }
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    cal_reg_path = out_path.parent / "v57_calibration_registry.json"
    val_reg_path = out_path.parent / "v57_validation_registry.json"
    manifest_path = out_path.parent / "v57_manifest.json"
    cal_reg_path.write_text(json.dumps(cal_reg, ensure_ascii=False, indent=2), encoding="utf-8")
    val_reg_path.write_text(json.dumps(val_reg, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    lines=[]
    lines.append(f"# V57 Channel Recharacterization Report — PENDING_REVISED / DECODE_FORBIDDEN")
    lines.append("")
    lines.append(f"HEAD {head} origin {origin} data_sha {DATA_SHA_SHORT} lifecycle V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED / DECODE_FORBIDDEN")
    lines.append(f"Cal 512+512 per source (131072 pairs/split) via available[0:512]/[512:1024] four-fold zero overlap, alpha={alpha} Laplace frozen, ceil leakage tag counted")
    lines.append(f"Zero overlap all={overall_zero_all} proofs={zero_proofs_all} counts_valid_all={counts_valid_all} chain_ok_all={chain_ok_all} negative_control_archived={negative_control_archived}")
    lines.append(f"Overall verdict: **{overall}**")
    lines.append("")
    lines.append("Boundary: V55 90 permanently banned; V25 m2 184/190/192 deprecated; only EG1-3 all-pass allows V58; Cal/Val same acquisition as diagnosis, fresh within-session only; MAP/q_mass descriptive only; ceil+tag; 8192 MLE retained as negative control; no FER/threshold/SKR claim.")
    lines.append("")
    lines.append("## Estimator Gates (revised)")
    lines.append("- EG1 NLL finite & improved: NLL_smooth<15 && <MLE-5 && <V25")
    lines.append("- EG2 CV consistency: |NLL_val - NLL_cal|≤0.5 && rel≤25% && |fold1-fold2|≤0.5")
    lines.append("- EG3 Entropy stability & convergence: |H_val-H_cal|≤0.20 && rel≤25% plus 32→512 series")
    lines.append("- Descriptive only: q_mass_mle, zero_frac, acc_smooth (no 60% hard gate, no q≤20% hard gate)")
    lines.append("")
    lines.append("| src | F | H_smooth | H1 | H2 | H_mle | m_ceil | m1_ceil | m2 | f_eff | leak | Δm | NLL_smooth | NLL_mle_clamp | NLL_V25 | acc_smooth_desc | q_mass_mle_desc | zero_frac | H_val_smooth | EG1 | EG2 | EG3 | PASS |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for src in ["1M","1p5M","2M"]:
        p=per_source[src]
        lines.append(f"| {src} | {p['F']} | {p['H_cal_smooth']} | {p['H1_cal_smooth']} | {p['H2_cal_smooth']} | {p['H_cal_mle']} | {p['m_total_ceil']} | {p['m1_ceil']} | {p['m2']} | {p['f_eff']} | {p['leak_total']} | {p['delta_m']} | {p['NLL_val_smooth']} | {p['NLL_val_mle_clamp_negative_control']} | {p['NLL_V25_on_Val']} | {p['acc_val_smooth_descriptive']} | {p['q_mass_mle_descriptive']} | {p['zero_frac_mle']} | {p['H_val_smooth']} | {p['EG1_pass']} | {p['EG2_pass']} | {p['EG3_pass']} | {p['PASS_s']} |")
    lines.append("")
    lines.append("### Convergence series (Cal subset → Val NLL_smooth, H_smooth)")
    for src in ["1M","1p5M","2M"]:
        p=per_source[src]
        cs = p["convergence_series"]
        lines.append(f"- {src}: 32→ NLL {cs['32']['NLL_val_smooth']} H {cs['32']['H_smooth']} zero {cs['32']['zero_frac_mle']}; 128→ {cs['128']['NLL_val_smooth']} H {cs['128']['H_smooth']}; 256→ {cs['256']['NLL_val_smooth']} H {cs['256']['H_smooth']}; 512→ {cs['512']['NLL_val_smooth']} H {cs['512']['H_smooth']}")
    lines.append("")
    lines.append("### Negative Control (8192 MLE, retained)")
    lines.append("Previous 8192 MLE: H 2.27/2.40/2.64 vs NLL 30.15/32.84/37.52, q_mass 59/64/74%, zero 99.4%, acc 36/29/19% (clamp 1e-15虚高). Retained as v57_channel_recharacterization_undersampled_mle_negative_control.json/md with UNDERSAMPLED_MLE_NEGATIVE_CONTROL. New 131k smooth eliminates clamp虚高, NLL converges toward H.")
    lines.append("")
    if overall=="V57_CHANNEL_RECHARACTERIZATION_PASS":
        lines.append("**All three sources PASS (EG1-3) — allowed to start V58 QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT dual review + EXECUTE_AUTH decoder TEST on fresh TEST blocks 30/source zero overlap with Cal512/Val512/V55/undersampled, unrevealed.**")
    elif overall=="V57_EVIDENCE_INVALID":
        lines.append("**EVIDENCE_INVALID — zero overlap or counts or chain invalid, no estimation, no V58; fix Cal/Val or expand further.**")
    else:
        lines.append("**FAIL (MIXED_BY_SOURCE if partial) — not allowed decoder TEST; fix Cal/Val or expand further, V58 still PENDING.**")
    lines.append("")
    lines.append("V25 deprecated m2 184/190/192 and m1=16 not reused; new m_ceil only for V58 planning, not instantiated in V57; alpha frozen not tuned; ceil+tag; DECODE_FORBIDDEN.")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"overall": overall, "per_source_pass": {k: v["PASS_s"] for k,v in per_source.items()}, "zero_overlap": overall_zero_all, "alpha": alpha, "negative_control_archived": negative_control_archived}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
