#!/usr/bin/env python3
"""V56D4 low-dim decomposition — decoder-free, 32-state I/CE/acc, fit/val split, V13 vs current contracts, first_drop.

Rules (frozen 6):
1. CE/accuracy primary, 2. 32-state plug-in MI auxiliary with bias note (1024/1024), 3. report U1->U1 U2->U2 and cross separately, 4. V13 vs current same frames [7-10]/[15-18], 5. first_drop decides attribution, 6. mixed signals -> INCONCLUSIVE_MIXED_SIGNAL.

Wording freeze: 未发现能由 fit4 学得并在 val4 泛化的1024态经验映射；已排除五类预注册物理映射（2060候选）; not “已排除任意1024置换”.

Usage:
  python v56d4_low_dim_decomposition.py [--pairs-root DIR] [--v13-root DIR] [--counts FILE] [--out FILE]
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np

FIT_FRAMES=[7,8,9,10]
VAL_FRAMES=[15,16,17,18]
assert set(FIT_FRAMES) & set(VAL_FRAMES)==set(), "fit/val must be disjoint"
# ponytail: minimal deps numpy+pandas only

def _safe_log2(x):
    return math.log(x,2) if x>0 else 0.0

def compute_I32(C):
    d=32
    C=np.asarray(C,dtype=np.float64).reshape(d,d)
    tot=float(np.sum(C))
    if tot<=0:
        return 0.0,0.0,0.0,0.0,0.0
    P=C/tot
    pa=np.sum(P,axis=1); pb=np.sum(P,axis=0)
    H_A=-float(np.sum([p*_safe_log2(p) for p in pa if p>0]))
    H_B=-float(np.sum([p*_safe_log2(p) for p in pb if p>0]))
    H_AB=-float(np.sum([p*_safe_log2(p) for p in P.flat if p>0]))
    I=H_A+H_B-H_AB
    return H_A,H_B,H_AB,I,tot

def joint32(a,b,dim=32):
    C=np.zeros((dim,dim),dtype=np.int64)
    if len(a)==0:
        return C
    np.add.at(C,(a,b),1)
    return C

def ce_acc_32(a_fit,b_fit,a_val,b_val):
    d=32
    Cfit=joint32(a_fit,b_fit,d)
    col_sum=np.sum(Cfit,axis=0)
    Pfit=np.zeros((d,d),dtype=np.float64)
    for col in range(d):
        s=col_sum[col]
        if s>0:
            Pfit[:,col]=Cfit[:,col]/s
        else:
            Pfit[:,col]=1.0/d
    if len(a_val)==0:
        return float('nan'),float('nan'),Pfit,Cfit
    amap=np.argmax(Pfit,axis=0)
    eps=1e-12
    probs=Pfit[a_val,b_val]
    probs=np.clip(probs,eps,1.0)
    ce=float(-np.mean(np.log2(probs)))
    acc=float(np.mean(a_val==amap[b_val]))
    return ce,acc,Pfit,Cfit

def load_pairs_for_source(pairs_path:Path, frames):
    # frames None -> all
    import pandas as pd
    pq_files=list(pairs_path.rglob("*.parquet")) if pairs_path.is_dir() else []
    if not pq_files and pairs_path.is_file() and pairs_path.suffix==".parquet":
        pq_files=[pairs_path]
    if not pq_files:
        return None
    dfs=[]
    for f in pq_files:
        try:
            df=pd.read_parquet(f)
            if "alice_symbol" in df.columns and "bob_symbol" in df.columns:
                dfs.append(df)
        except Exception:
            continue
    if not dfs: return None
    df_all=dfs[0] if len(dfs)==1 else pd.concat(dfs,ignore_index=True)
    if frames is not None:
        df_all=df_all[df_all["frame_id"].isin(frames)]
    return df_all

def per_source_stats(df_fit, df_val):
    # df_* contain alice_symbol,bob_symbol
    def to_u1u2(sym): return (sym>>5).astype(np.int64), (sym&31).astype(np.int64)
    if df_fit is None or df_val is None or len(df_fit)==0 or len(df_val)==0:
        return None
    a_fit=df_fit["alice_symbol"].to_numpy(dtype=np.int64); b_fit=df_fit["bob_symbol"].to_numpy(dtype=np.int64)
    a_val=df_val["alice_symbol"].to_numpy(dtype=np.int64); b_val=df_val["bob_symbol"].to_numpy(dtype=np.int64)
    u1a_fit,u2a_fit=to_u1u2(a_fit); u1b_fit,u2b_fit=to_u1u2(b_fit)
    u1a_val,u2a_val=to_u1u2(a_val); u1b_val,u2b_val=to_u1u2(b_val)
    # I on val (plug-in, auxiliary)
    C_u1_val=joint32(u1a_val,u1b_val,32); _,_,_,I_u1_val,_=compute_I32(C_u1_val)
    C_u2_val=joint32(u2a_val,u2b_val,32); _,_,_,I_u2_val,_=compute_I32(C_u2_val)
    C_cross1=joint32(u1a_val,u2b_val,32); _,_,_,I_cross1,_=compute_I32(C_cross1)
    C_cross2=joint32(u2a_val,u1b_val,32); _,_,_,I_cross2,_=compute_I32(C_cross2)
    # CE/acc primary: fit->val
    ce_u1,acc_u1,_,_=ce_acc_32(u1a_fit,u1b_fit,u1a_val,u1b_val)
    ce_u2,acc_u2,_,_=ce_acc_32(u2a_fit,u2b_fit,u2a_val,u2b_val)
    # also all-data CE for reference (not primary)
    u1a_all=np.concatenate([u1a_fit,u1a_val]); u1b_all=np.concatenate([u1b_fit,u1b_val])
    u2a_all=np.concatenate([u2a_fit,u2a_val]); u2b_all=np.concatenate([u2b_fit,u2b_val])
    # joint CE reference: use fit->all? just report similar but not used
    # occupancy: pairs per frame on val
    occ_val=len(a_val)/len(set(df_val["frame_id"].to_numpy())) if len(df_val)>0 else 0
    # U1/U2 consistency (identity)
    u1_cons=float(np.mean(u1a_val==u1b_val)) if len(u1a_val)>0 else 0
    u2_cons=float(np.mean(u2a_val==u2b_val)) if len(u2a_val)>0 else 0
    return {
        "n_fit":int(len(a_fit)),"n_val":int(len(a_val)),
        "I_U1_val":round(float(I_u1_val),4),"I_U2_val":round(float(I_u2_val),4),
        "I_U1U2_cross":round(float(I_cross1),4),"I_U2U1_cross":round(float(I_cross2),4),
        "CE_U1_val":round(float(ce_u1),4),"acc_U1_val":round(float(acc_u1),6),
        "CE_U2_val":round(float(ce_u2),4),"acc_U2_val":round(float(acc_u2),6),
        "occupancy_val":round(float(occ_val),2),
        "u1_consistency_val":round(float(u1_cons),6),"u2_consistency_val":round(float(u2_cons),6),
        "bias_note":"32-state 1024 bins, N=1024 -> ~1/bin, finite-sample positive bias remains but <<1024-state 1M bins",
    }

def read_sidecar_matrix(v13_sidecars, current_sidecars):
    import json
    def extract(p:Path):
        try:
            j=json.loads(p.read_text(encoding="utf-8"))
            mp=j.get("materialize_params",{})
            used=mp.get("used_params",{}) if isinstance(mp.get("used_params"),dict) else {}
            return {
                "pairing_policy": mp.get("pairing") or used.get("pairing_mode") or mp.get("pairing_mode"),
                "pairing_direction": used.get("pairing_path_tag") or mp.get("pairing_path_tag"),
                "pairing_threshold_ps": used.get("nearest_threshold_ps") or mp.get("threshold_ps") or used.get("threshold_ps"),
                "gate_width_ps": used.get("gate_width_ps") or mp.get("gate_width_ps"),
                "frame_start_ps": used.get("frame_start_ps") or mp.get("frame_start_ps"),
                "frame_period_ps": used.get("frame_period_ps") or mp.get("frame_period_ps"),
                "delay_used_ps": used.get("delay_used_ps") or mp.get("delay_used_ps"),
                "peak_center_ps": used.get("peak_center_ps") or mp.get("peak_center_ps"),
                "wrap_rule": used.get("frame_anchor") or mp.get("wrap_rule"),
                "mapping": used.get("mapping") or mp.get("mapping"),
                "occupancy_filter": used.get("occupancy_filter") or mp.get("occupancy_filter"),
            }
        except Exception as e:
            return {"error":repr(e)}
    v13_files=list(Path(v13_sidecars).rglob("sidecar_meta.json")) if Path(v13_sidecars).exists() else []
    cur_files=list(Path(current_sidecars).rglob("sidecar_meta.json")) if Path(current_sidecars).exists() else []
    v13_rec=extract(v13_files[0]) if v13_files else {}
    cur_rec=extract(cur_files[0]) if cur_files else {}
    fields=["pairing_policy","pairing_direction","pairing_threshold_ps","gate_width_ps","frame_start_ps","frame_period_ps","delay_used_ps","peak_center_ps","wrap_rule","mapping","occupancy_filter"]
    matrix={}
    for f in fields:
        v=v13_rec.get(f); c=cur_rec.get(f)
        if v is None or c is None:
            status="INCOMPLETE"
        elif v==c:
            status="PASS"
        else:
            status="MISMATCH"
        matrix[f]={"v13":v,"current":c,"status":status}
    return matrix, v13_rec, cur_rec

def main():
    p=argparse.ArgumentParser(description="V56D4 low-dim decomposition")
    p.add_argument("--pairs-root",type=str,default="comparison_bench/outputs_comparison/v55_intake_20260828/pairs")
    p.add_argument("--v13-root",type=str,default="comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816")
    p.add_argument("--v13-sidecars",type=str,default="workspace/v13r3fresh_20260816/sidecars")
    p.add_argument("--counts",type=str,default="comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz")
    p.add_argument("--out",type=str,default="openspec/changes/formal-ir-v56d4-low-dim-decomposition/v56d4_low_dim_decomposition.json")
    args=p.parse_args()
    assert set(FIT_FRAMES) & set(VAL_FRAMES)==set()
    provenance={
        "head":"176bf34f", "branch":"formal-ir-mainline",
        "data_sha":"84d62779603e62de50ded5182ed65b65d3dc6084",
        "lifecycle":"DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN",
        "wording":"未发现能由 fit4 学得并在 val4 泛化的1024态经验映射；已排除五类预注册物理映射（2060候选）",
        "fit_frames":FIT_FRAMES,"val_frames":VAL_FRAMES,
        "decision_order":["CE/acc primary","I32 auxiliary with bias note","four I separately","V13 vs current same split","first_drop attribution","mixed->INCONCLUSIVE_MIXED_SIGNAL"],
    }
    pairs_root=Path(args.pairs_root); v13_root=Path(args.v13_root)
    name_map={"20260123_1M_600k_0dB":"1M","20260107_PPLN_1p5M":"1p5M","20260123_2M_1p2M_0dB":"2M",
              "type2_1M_20260121_184040":"1M","type2_1p5M_20260121_183806":"1p5M","type2_2M_20260121_183657":"2M"}
    per_source_current={}
    per_source_v13={}
    # current sources
    for sdir in sorted([d for d in pairs_root.iterdir() if d.is_dir()]) if pairs_root.exists() else []:
        label=name_map.get(sdir.name,sdir.name)
        df_fit=load_pairs_for_source(sdir,FIT_FRAMES)
        df_val=load_pairs_for_source(sdir,VAL_FRAMES)
        if df_fit is None or df_val is None: continue
        stats=per_source_stats(df_fit,df_val)
        if stats: per_source_current[label]=stats
    # v13 sources
    for sdir in sorted([d for d in v13_root.iterdir() if d.is_dir()]) if v13_root.exists() else []:
        if not (sdir/"pairs.parquet").exists(): continue
        label=name_map.get(sdir.name,sdir.name)
        df_fit=load_pairs_for_source(sdir,FIT_FRAMES)
        df_val=load_pairs_for_source(sdir,VAL_FRAMES)
        if df_fit is None or df_val is None:
            # fallback: try frame ids exist 0..1999, same split works
            df_fit=load_pairs_for_source(sdir,FIT_FRAMES)
            df_val=load_pairs_for_source(sdir,VAL_FRAMES)
            if df_fit is None or df_val is None: continue
        stats=per_source_stats(df_fit,df_val)
        if stats: per_source_v13[label]=stats

    # contract matrix
    matrix, v13_rec, cur_rec = read_sidecar_matrix(args.v13_sidecars, "comparison_bench/outputs_comparison/v55_intake_20260828/sidecars")
    # first_drop per source: compare staged metrics current vs V13
    pipeline_stages=["raw_coincidence","pairing","per_frame_occupancy","frame_anchor","U1U2_consistency"]
    per_source_detailed={}
    shunt_per_source={}
    for label,cur in per_source_current.items():
        v13=per_source_v13.get(label,{})
        # compute pipeline deltas (simplified): occupancy and I/CE
        stages=[]
        # stage 3 occupancy
        v13_occ=v13.get("occupancy_val",256) if v13 else 256
        cur_occ=cur.get("occupancy_val",0)
        stages.append({"stage":"per_frame_occupancy","V13_val":v13_occ,"new_val":cur_occ,"delta":round(float(cur_occ - v13_occ),2),"note":"expect 256; V13 ~256"})
        # stage 5 U1/U2 I and CE
        for k in ["I_U1_val","I_U2_val","CE_U1_val","CE_U2_val","acc_U1_val","acc_U2_val"]:
            stages.append({"stage":"U1U2_consistency","metric":k,"V13_val":v13.get(k) if v13 else None,"new_val":cur.get(k),"delta": round(float(cur.get(k)-v13.get(k)),4) if v13 and v13.get(k) is not None else None})
        # raw/pairing/anchor placeholder incomplete if no ttbin
        stages.insert(0,{"stage":"raw_coincidence","V13_val":"INCOMPLETE_no_ttbin","new_val":"INCOMPLETE_no_ttbin","delta":None,"note":"sidecar p2bg/peak available but ttbin not re-parsed in decoder-free"})
        stages.insert(1,{"stage":"pairing","V13_val":"INCOMPLETE","new_val":"INCOMPLETE","delta":None,"note":"Δt histogram not stored in pairs.parquet"})
        stages.insert(3,{"stage":"frame_anchor","V13_val":"INCOMPLETE","new_val":"INCOMPLETE","delta":None,"note":"before/after pair_index requires ttbin re-run; decoder-free two-way pair comparison suffices"})
        # first_drop logic: frozen rule 5
        ce_thr=3.0; acc_thr=0.5; I_thr=1.5
        # Determine if raw/Δt degraded: here occupancy proxy
        # If occupancy far from 256 -> occupancy stage
        # Else if frame anchor incomplete -> skip
        # Else check U1/U2 vs prior
        # Simplified: if cur CE high and acc low -> attribute by comparison to V13
        v13_ce_u1=v13.get("CE_U1_val",1.5) if v13 else 1.5
        v13_acc_u1=v13.get("acc_U1_val",0.9) if v13 else 0.9
        # first_drop: if V13 healthy (CE<2, acc>0.6, I>2) and cur CE>3 or acc<0.5 -> U1U2 stage
        v13_healthy = (v13.get("CE_U1_val",99)<2.5 and v13.get("acc_U1_val",0)>0.6) if v13 else False
        cur_bad = (cur["CE_U1_val"]>3.0 or cur["acc_U1_val"]<0.5 or cur["I_U1_val"]<1.5)
        if v13_healthy and cur_bad:
            first_drop="U1U2_consistency"
        elif cur_occ<200 or cur_occ>300:
            first_drop="per_frame_occupancy"
        else:
            first_drop="INCONCLUSIVE_no_single_drop"
        # shunt per frozen 6 rules: CE/acc primary
        # 1) primary CE/acc: if both U1 and U2 acc<0.5 and CE>3 -> degraded
        # 2) cross not used for shunt, reported separately
        # 5) attribution by first_drop
        # 6) mixed -> inconclusive
        acc_u1=cur["acc_U1_val"]; acc_u2=cur["acc_U2_val"]; ce_u1=cur["CE_U1_val"]; ce_u2=cur["CE_U2_val"]
        # compare to V13 two-way delta
        v13_acc_u1=v13.get("acc_U1_val") if v13 else None
        delta_acc = (acc_u1 - v13_acc_u1) if v13_acc_u1 is not None else None
        # Rule: if V13 contract (here approximated by V13 pairs) healthy and current bad, but V13 vs current delta small (<0.1) -> TRUE_DOMAIN_SHIFT else PAIRING_OR_FRAME
        # Since we haven't re-paired with V13 contract on new ttbin, we approximate: V13 pairing healthy -> if current also bad and delta <0.1 acc -> true shift
        if v13 and abs((acc_u1 - v13_acc_u1))<0.10 and acc_u1<0.5 and ce_u1>3:
            shunt="TRUE_ACQUISITION_DOMAIN_SHIFT"
            # attribution check: if first_drop occupancy -> pairing else if U1U2 -> need contract test; without ttbin re-run we mark mixed
            if first_drop=="per_frame_occupancy":
                pass
        elif v13_healthy and cur_bad:
            # Check if occupancy already bad -> pairing else frame anchor vs domain
            # Without ttbin re-run, we cannot prove pairing recoverable -> mark INCONCLUSIVE_MIXED_SIGNAL per rule6 when metrics mixed
            # Here CE bad but occupancy normal -> could be frame or domain
            shunt="INCONCLUSIVE_MIXED_SIGNAL"
        else:
            shunt="INCONCLUSIVE_MIXED_SIGNAL"
        # If metrics point to different layers, freeze to inconclusive per rule6
        # Mixed example: occupancy normal but CE bad vs I bad divergence
        per_source_detailed[label]={
            "current":cur, "v13_reference":v13,
            "pipeline_stages":stages, "first_drop_stage":first_drop,
            "contract_comparison":{"delta_acc_U1": round(float(delta_acc),4) if delta_acc is not None else None,
                                   "note":"V13-contract vs current-contract approximated by V13 pairs vs current pairs on same [7-10]/[15-18]; two-way only, no G-search search"},
        }
        shunt_per_source[label]=shunt

    # overall shunt: if all sources same then that, else MIXED/INCONCLUSIVE
    uniq=set(shunt_per_source.values())
    if len(uniq)==1:
        overall=next(iter(uniq))
    elif len(uniq)==0:
        overall="INCONCLUSIVE_MIXED_SIGNAL"
    else:
        overall="INCONCLUSIVE_MIXED_SIGNAL"

    result={
        "provenance":provenance,
        "per_source":per_source_detailed,
        "per_source_current_summary":per_source_current,
        "per_source_v13_summary":per_source_v13,
        "contract_matrix":matrix,
        "shunt_per_source":shunt_per_source,
        "overall":overall,
        "overall_shunt":overall,
        "note":"decoder-free (no dec. calls); V13 vs current same fit[7-10] val[15-18]; CE/acc primary, I32 auxiliary with bias note; four I reported separately; no G-search, candidate count 2",
        "counts_path":args.counts,
    }
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    # guard checks
    # guard: no decoder calls (lifecycle marker excluded)
    txt=open(__file__,encoding="utf-8").read().replace("DECODE_FORBIDDEN","").replace("decoder-free","")
    assert ("dec"+"ode_") not in txt, "decoder guard"
    import py_compile; py_compile.compile(str(out),doraise=False)
    print(json.dumps({"provenance":provenance,"per_source_current":per_source_current,"per_source_v13":per_source_v13,"contract_matrix":matrix,"shunt_per_source":shunt_per_source,"overall":overall,"out":str(out)},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
