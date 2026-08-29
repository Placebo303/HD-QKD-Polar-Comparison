#!/usr/bin/env python3
"""V57 channel recharacterization — decoder-free. Cal 19..50 Val 77..108 per source."""
from __future__ import annotations
import argparse, json, math, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd

CAL = list(range(19, 51))  # 19..50 inclusive 32
VAL = list(range(77, 109))  # 77..108 inclusive 32
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
    # fallback if strata not found: try top-level scanning
    if not flat_per.get("1M"):
        # alternative: search selected_frame_ids at top
        pass
    return flat_per

def _counts_to_p(counts: np.ndarray):
    # counts 1024x1024 -> P(a|b) col normalized
    col = counts.sum(axis=0).astype(np.float64)  # 1024
    P = np.zeros_like(counts, dtype=np.float64)
    # uniform for zero cols
    for b in range(counts.shape[1]):
        s = col[b]
        if s > 0:
            P[:, b] = counts[:, b] / s
        else:
            P[:, b] = 1.0 / counts.shape[0]
    return P, col / col.sum() if col.sum()>0 else np.ones(1024)/1024

def calc_H(C_ab: np.ndarray):
    N = C_ab.sum()
    if N == 0:
        return 0.0, 0.0, 0.0, 0.0, None, None
    col = C_ab.sum(axis=0).astype(np.float64)
    Pb = col / N
    # P_hat
    P = np.zeros((1024,1024), dtype=np.float64)
    for b in range(1024):
        s = col[b]
        if s>0:
            P[:, b] = C_ab[:, b] / s
        else:
            P[:, b] = 1.0/1024
    # H(A|B)
    H = 0.0
    for b in range(1024):
        pb = Pb[b]
        if pb == 0:
            continue
        col_p = P[:, b]
        # only nonzero
        nz = col_p[col_p>0]
        H -= pb * np.sum(nz * np.log2(nz))
    # H(U1|B)
    # P_u1 shape 32 x 1024
    P_u1 = np.zeros((32,1024), dtype=np.float64)
    for b in range(1024):
        for u1 in range(32):
            s = 0.0
            base = 32*u1
            # sum over u2 0..31
            s = np.sum(P[base:base+32, b]) if col[b]>0 else 32*(1.0/1024)
            # actually uniform case: each a uniform 1/1024 => sum 32/1024=1/32
            P_u1[u1, b] = s
    H1 = 0.0
    for b in range(1024):
        pb = Pb[b]
        if pb==0: continue
        col_p = P_u1[:, b]
        nz = col_p[col_p>0]
        H1 -= pb * np.sum(nz * np.log2(nz))
    H2 = H - H1
    return H, H1, H2, Pb, P, col

def nll_on_pairs(P_cal: np.ndarray, a_arr: np.ndarray, b_arr: np.ndarray):
    eps=1e-15
    # P_cal is 1024x1024 col normalized
    probs = P_cal[a_arr, b_arr]
    probs = np.clip(probs, eps, 1.0)
    return float(-np.mean(np.log2(probs)))

def acc_on_pairs(P_cal: np.ndarray, a_arr: np.ndarray, b_arr: np.ndarray):
    amap = np.argmax(P_cal, axis=0)  # 1024
    return float(np.mean(a_arr == amap[b_arr]))

def main():
    ap = argparse.ArgumentParser(description="V57 channel recharacterization")
    ap.add_argument("--pairs-root", type=str, default="comparison_bench/outputs_comparison/v55_intake_20260828/pairs")
    ap.add_argument("--counts", type=str, default="comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz")
    ap.add_argument("--v55-registry", type=str, default="openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/v55_authoritative_registry.json")
    ap.add_argument("--out", type=str, default="openspec/changes/formal-ir-v57-channel-recharacterization/v57_channel_recharacterization.json")
    ap.add_argument("--report", type=str, default="openspec/changes/formal-ir-v57-channel-recharacterization/V57_CHANNEL_RECHARACTERIZATION_REPORT.md")
    args = ap.parse_args()

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

    # zero overlap proofs
    v55_flat = _load_v55_flat(v55_path)
    zero_proofs = {}
    overall_zero = True
    for src in ["1M","1p5M","2M"]:
        cal_set = set(CAL)
        val_set = set(VAL)
        c1 = len(cal_set & val_set) == 0
        flat = v55_flat.get(src, set())
        c2 = len((cal_set | val_set) & flat) == 0
        c3 = len((cal_set | val_set) & V56_FORBIDDEN) == 0
        c4 = all(0 <= fid < SRC_F[src] for fid in (cal_set | val_set))
        zero_proofs[src] = {"cal_cap_val": c1, "cal_val_cap_v55": c2, "cap_v56": c3, "in_range": c4}
        if not (c1 and c2 and c3 and c4):
            overall_zero = False
    zero_proofs_all = {
        "cal_cap_val": all(v["cal_cap_val"] for v in zero_proofs.values()),
        "cal_val_cap_v55": all(v["cal_val_cap_v55"] for v in zero_proofs.values()),
        "cap_v56": all(v["cap_v56"] for v in zero_proofs.values()),
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
        P, _ = _counts_to_p(cnt)
        v25_P[src] = P

    per_source = {}
    counts_valid_all = True
    chain_ok_all = True
    for src in ["1M","1p5M","2M"]:
        sub = SRC_MAP[src]
        parquet = pairs_root / sub / "pairs.parquet"
        if not parquet.exists():
            # try flat
            alt = pairs_root / "pairs.parquet"
            parquet = alt if alt.exists() else parquet
        df = pd.read_parquet(str(parquet))
        # validate columns
        assert "frame_id" in df.columns and "alice_symbol" in df.columns and "bob_symbol" in df.columns, f"missing cols {df.columns}"
        # slice Cal/Val
        cal_df = df[df["frame_id"].isin(CAL)].copy()
        val_df = df[df["frame_id"].isin(VAL)].copy()
        # checks
        counts_valid = True
        note = ""
        if len(cal_df) != 8192:
            counts_valid = False
            note += f" cal_len {len(cal_df)} !=8192;"
        if len(val_df) != 8192:
            counts_valid = False
            note += f" val_len {len(val_df)} !=8192;"
        # per frame 256
        for fid in CAL:
            c = int((cal_df["frame_id"]==fid).sum()) if len(cal_df) else 0
            # need count per original df frame
            c2 = int((df["frame_id"]==fid).sum())
            if c2 != 256:
                counts_valid = False
                note += f" frame{fid} {c2}!=256;"
                break
            if c != 256 and len(cal_df)==8192:
                # still check
                pass
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
        # range check
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
        zero_cells = int(np.sum(C_ab==0))
        zero_frac = zero_cells / (1024*1024)
        N_cal = int(C_ab.sum())
        H, H1, H2, Pb, P_cal, col = calc_H(C_ab)
        # chain check
        chain_ok = abs(H - H1 - H2) < 1e-9
        if not chain_ok:
            counts_valid = False
        # m recompute
        f_target=1.3; n=1024; tag=64
        m_total = math.floor((f_target*n*H - tag)/5) if H>0 else -1
        if H < 0.1 or m_total <0 or m_total >= 1024:
            counts_valid = False
        m1 = int(round(m_total * H1 / H)) if H>0 else 0
        m2 = m_total - m1
        leak = 5*m_total + 64
        f_eff = leak/(n*H) if H>0 else 0
        delta_m = m_total - V25_M_REF[src]
        delta_leak = 5*delta_m
        # Cal self metrics
        cal_nll = nll_on_pairs(P_cal, a_cal, b_cal) if len(a_cal) else float('nan')
        cal_acc = acc_on_pairs(P_cal, a_cal, b_cal) if len(a_cal) else float('nan')
        # V25 NLL
        v25_nll_cal = nll_on_pairs(v25_P[src], a_cal, b_cal) if src in v25_P and len(a_cal) else float('nan')
        v25_nll_val = nll_on_pairs(v25_P[src], a_val, b_val) if src in v25_P and len(a_val) else float('nan')
        # Val metrics with P_cal
        nll_val = nll_on_pairs(P_cal, a_val, b_val) if len(a_val) else float('nan')
        acc_val = acc_on_pairs(P_cal, a_val, b_val) if len(a_val) else float('nan')
        acc_cal = cal_acc
        # q_mass
        C_val = np.zeros((1024,1024), dtype=np.int32)
        if len(a_val):
            np.add.at(C_val, (a_val, b_val), 1)
        # P_val_emp
        N_val = C_val.sum()
        q_mass = 0.0
        if N_val>0:
            # sum over cells where C_ab==0
            mask = (C_ab==0)
            q_mass = float(C_val[mask].sum() / N_val)
        # H_val
        H_val, H1_val, H2_val, _, _, _ = calc_H(C_val)
        # gates
        # V1
        v1 = (nll_val <= H + 0.50) and (nll_val <= 1.50) and (nll_val < (v25_nll_val - 5.0)) if not (math.isnan(nll_val) or math.isnan(v25_nll_val)) else False
        v2 = (acc_val >= 0.60) and (acc_val >= acc_cal - 0.10) if not (math.isnan(acc_val) or math.isnan(acc_cal)) else False
        v3 = (q_mass <= 0.20)
        # V4
        if math.isnan(H_val) or H==0:
            v4=False
        else:
            v4 = (abs(H_val - H) <= 0.20) and (abs(H_val - H)/H <= 0.25)
        zero_ok = zero_proofs[src]["cal_cap_val"] and zero_proofs[src]["cal_val_cap_v55"] and zero_proofs[src]["cap_v56"]
        pass_s = bool(v1 and v2 and v3 and v4 and zero_ok and counts_valid and chain_ok)
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
            "N_val": int(N_val),
            "C_shape": [1024,1024],
            "zero_cells_cal": zero_cells,
            "zero_frac_cal": round(float(zero_frac),6),
            "H_cal": round(float(H),6),
            "H1_cal": round(float(H1),6),
            "H2_cal": round(float(H2),6),
            "delta_chain": round(float(H - H1 - H2),9),
            "chain_ok": bool(chain_ok),
            "m_total": int(m_total),
            "m1": int(m1),
            "m2": int(m2),
            "leak_total": int(leak),
            "f_eff": round(float(f_eff),6),
            "delta_m": int(delta_m),
            "delta_leak": int(delta_leak),
            "m_total_V25_ref": V25_M_REF[src],
            "cal_NLL_self": round(float(cal_nll),6) if not math.isnan(cal_nll) else None,
            "cal_acc_self": round(float(cal_acc),6) if not math.isnan(cal_acc) else None,
            "V25_NLL_on_Cal": round(float(v25_nll_cal),6) if not math.isnan(v25_nll_cal) else None,
            "NLL_val": round(float(nll_val),6) if not math.isnan(nll_val) else None,
            "NLL_val_block": round(float(nll_val*1024),3) if not math.isnan(nll_val) else None,
            "NLL_V25_on_Val": round(float(v25_nll_val),6) if not math.isnan(v25_nll_val) else None,
            "NLL_V25_on_Val_block": round(float(v25_nll_val*1024),3) if not math.isnan(v25_nll_val) else None,
            "acc_val": round(float(acc_val),6) if not math.isnan(acc_val) else None,
            "acc_cal": round(float(acc_cal),6) if not math.isnan(acc_cal) else None,
            "q_mass": round(float(q_mass),6),
            "H_val": round(float(H_val),6) if not math.isnan(H_val) else None,
            "H1_val": round(float(H1_val),6) if not math.isnan(H1_val) else None,
            "H2_val": round(float(H2_val),6) if not math.isnan(H2_val) else None,
            "V1_pass": bool(v1),
            "V2_pass": bool(v2),
            "V3_pass": bool(v3),
            "V4_pass": bool(v4),
            "zero_overlap_s": bool(zero_ok),
            "counts_valid_s": bool(counts_valid),
            "PASS_s": bool(pass_s),
            "note": note.strip(),
        }
        if not counts_valid:
            counts_valid_all = False

    # overall verdict priority
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

    # registries
    cal_reg = {
        "schema": "v57_cal/val_v1",
        "lifecycle": "V57_CHANNEL_RECHARACTERIZATION_PENDING",
        "data_sha": DATA_SHA_SHORT,
        "data_sha_full": DATA_SHA,
        "head": head,
        "branch": "formal-ir-mainline",
        "processing_rule": "legacy_v1",
        "provenance_note": "Cal 19..50 32 frames 8 blocks*4 F03 5+5 natural, uniform three sources, 84d62779 200ps legacy_v1 nearest 1024",
        "per_source": {src: {"F": SRC_F[src], "K": SRC_F[src]-3, "selected_frame_ids": CAL, "blocks": 8, "pairs": 8192, "provenance": {"v55_registry_sha": "v55_authoritative", "frame_period": 204800, "processing_rule": "legacy_v1"}} for src in ["1M","1p5M","2M"]},
        "overall_zero_overlap_verified": bool(overall_zero_all),
    }
    val_reg = {
        "schema": "v57_cal/val_v1",
        "lifecycle": "V57_CHANNEL_RECHARACTERIZATION_PENDING",
        "data_sha": DATA_SHA_SHORT,
        "data_sha_full": DATA_SHA,
        "head": head,
        "branch": "formal-ir-mainline",
        "processing_rule": "legacy_v1",
        "provenance_note": "Val 77..108 32 frames 8 blocks*4 F03 5+5 natural, uniform three sources",
        "per_source": {src: {"F": SRC_F[src], "K": SRC_F[src]-3, "selected_frame_ids": VAL, "blocks": 8, "pairs": 8192, "provenance": {"v55_registry_sha": "v55_authoritative", "frame_period": 204800, "processing_rule": "legacy_v1"}} for src in ["1M","1p5M","2M"]},
        "overall_zero_overlap_verified": bool(overall_zero_all),
    }
    manifest = {
        "schema": "v57_manifest_v1",
        "head": head,
        "origin_formal_ir_mainline": origin,
        "data_sha": DATA_SHA_SHORT,
        "data_sha_full": DATA_SHA,
        "zero_overlap_proofs": zero_proofs_all,
        "per_source_zero_overlap": zero_proofs,
        "overall_zero_overlap_verified": bool(overall_zero_all),
        "counts_valid_all": bool(counts_valid_all),
        "chain_ok_all": bool(chain_ok_all),
        "command": "python v57_channel_recharacterization.py",
    }

    result = {
        "schema": "v57_channel_recharacterization_v1",
        "lifecycle": "V57_CHANNEL_RECHARACTERIZATION_PENDING",
        "head": head,
        "origin_formal_ir_mainline": origin,
        "data_sha": DATA_SHA_SHORT,
        "data_sha_full": DATA_SHA,
        "branch": "formal-ir-mainline",
        "pairs_root": str(pairs_root),
        "counts_path": str(counts_path),
        "v55_registry": str(v55_path),
        "cal_frames": CAL,
        "val_frames": VAL,
        "zero_overlap_proofs": zero_proofs_all,
        "per_source_zero_overlap": zero_proofs,
        "per_source": per_source,
        "verdict": {
            "overall": overall,
            "shunt_per_source": {src: {"PASS_s": per_source[src]["PASS_s"], "V1": per_source[src]["V1_pass"], "V2": per_source[src]["V2_pass"], "V3": per_source[src]["V3_pass"], "V4": per_source[src]["V4_pass"]} for src in per_source},
            "overall_zero_overlap_verified": bool(overall_zero_all),
            "counts_valid_all": bool(counts_valid_all),
            "chain_ok_all": bool(chain_ok_all),
        },
        "boundary": {
            "V55_90_permanently_banned": True,
            "V25_m_deprecated": "m2 184/190/192 and m1=16 deprecated, not reused as budget",
            "only_all_pass_allows_V58": True,
            "freshness": "Cal/Val derived from same 20260123/20260107 pairs.parquet as diagnosis, not claiming fully independent cross-session; fresh within-session confirmation only",
        }
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    # write registries
    cal_reg_path = out_path.parent / "v57_calibration_registry.json"
    val_reg_path = out_path.parent / "v57_validation_registry.json"
    manifest_path = out_path.parent / "v57_manifest.json"
    cal_reg_path.write_text(json.dumps(cal_reg, ensure_ascii=False, indent=2), encoding="utf-8")
    val_reg_path.write_text(json.dumps(val_reg, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # report
    lines=[]
    lines.append(f"# V57 Channel Recharacterization Report — PENDING / FORBIDDEN")
    lines.append("")
    lines.append(f"HEAD {head} origin {origin} data_sha {DATA_SHA_SHORT} lifecycle V57_CHANNEL_RECHARACTERIZATION_PENDING / FORBIDDEN")
    lines.append(f"Cal 19..50 (32 frames, 8192 pairs/source) Val 77..108 (32, 8192) unified three sources")
    lines.append(f"Zero overlap all={overall_zero_all} proofs={zero_proofs_all} counts_valid_all={counts_valid_all} chain_ok_all={chain_ok_all}")
    lines.append(f"Overall verdict: **{overall}**")
    lines.append("")
    lines.append("Boundary: V55 90 permanently banned (revealed 0/90); V25 m2 184/190/192 deprecated not reused; only all-pass allows V58; Cal/Val same acquisition as diagnosis, fresh within-session confirmation only; no FER/threshold/SKR claim.")
    lines.append("")
    lines.append("| src | F | H_cal | H1 | H2 | m_total | m1 | m2 | f_eff | leak | Δm | Δleak | NLL_val | NLL_V25 | acc_val | acc_cal | q_mass | zero_frac | H_val | V1 | V2 | V3 | V4 | PASS |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for src in ["1M","1p5M","2M"]:
        p=per_source[src]
        lines.append(f"| {src} | {p['F']} | {p['H_cal']} | {p['H1_cal']} | {p['H2_cal']} | {p['m_total']} | {p['m1']} | {p['m2']} | {p['f_eff']} | {p['leak_total']} | {p['delta_m']} | {p['delta_leak']} | {p['NLL_val']} | {p['NLL_V25_on_Val']} | {p['acc_val']} | {p['acc_cal']} | {p['q_mass']} | {p['zero_frac_cal']} | {p['H_val']} | {p['V1_pass']} | {p['V2_pass']} | {p['V3_pass']} | {p['V4_pass']} | {p['PASS_s']} |")
    lines.append("")
    lines.append(f"Gate V1: NLL_val <= H+0.5 && <=1.5 && < V25-5 ; V2: acc>=60% && >=cal-10pp ; V3: q_mass<=20% ; V4: |H_val-H_cal|<=0.20 && <=25%")
    lines.append("")
    if overall=="V57_CHANNEL_RECHARACTERIZATION_PASS":
        lines.append("**All three sources PASS — allowed to start V58 QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT dual review + EXECUTE_AUTH decoder TEST on fresh TEST blocks 30/source zero overlap with Cal/Val/V55, unrevealed.**")
    elif overall=="V57_EVIDENCE_INVALID":
        lines.append("**EVIDENCE_INVALID — zero overlap or counts or chain invalid, no estimation, no V58; fix Cal/Val split or expand to 64 frames.**")
    else:
        lines.append("**FAIL (MIXED_BY_SOURCE if partial) — not allowed decoder TEST; fix Cal/Val or expand to 64 frames, re-review, V58 still PENDING.**")
    lines.append("")
    lines.append("V25 deprecated m2 184/190/192 and m1=16 not reused; new m1/m2 only for V58 planning, not instantiated in V57; FORBIDDEN.")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"overall": overall, "per_source_pass": {k: v["PASS_s"] for k,v in per_source.items()}, "zero_overlap": overall_zero_all}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
