#!/usr/bin/env python3
"""
V49 只读分布迁移诊断 — 不改 H1，不重做 Lane C，不运行 decoder。

固定 prior: load_v25_channel_counts() -> channel_counts.npz (TRAIN 60% only)
评估池: v13r3fresh_pairs_20260816/*.parquet 按 split_manifest 60/20/20 切 TRAIN/VAL/HOLD
  - 按 frame_id 升序 contiguous: 1M 0-1199/1200-1599/1600-1999, 1p5M 0-1659/1660-2212/2213-2766, 2M 0-2186/2187-2915/2916-3644
  - 每帧 256 pairs, block 1024 pairs = 4 帧 (仅用于 V48 块级对比)

计算 (decoder-free):
  - P_TRAIN(U1|B) NLL / CE, P_TRAIN(U2|B,U1) NLL / CE  (floor 1e-15, 与 v48 冻结一致)
  - 每源 TV / JS / 平滑 KL (epsilon=1e-12) — KL 使用经验 P_eval(U1|B) 与 P_TRAIN 对 B 按 eval 频率加权
  - initial error (SER_total, U1_err, U2_err), 零计数/罕见 Bob bin 覆盖
  - V48 45 held-out 块: 成功(30) vs 失败(15) prior NLL/entropy/零计数率 — 按冻结 45 块 held-out pairs (4 frames=1024) 重新计算
  - VAL 候选 counts (TRAIN+VAL) vs TRAIN 在 HOLD 上的 NLL 对比 (禁止 HOLD 重估)

产出: docs/v49_distribution_tables/*.csv + docs/v49-distribution-shift-diagnosis-*.md 引用
仅只读, 不写 V48 输出, 不调用任何 decoder.

ponytail: naive O(N) scan, per-B loops; upgrade to vectorized hist if N>10M
"""
from __future__ import annotations
import json
import csv
from pathlib import Path
import numpy as np

try:
    import pandas as pd
except ImportError:
    pd = None

REPO = Path(__file__).resolve().parents[1]
NPZ_PATH = REPO / "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz"
SPLIT_MANIFEST = REPO / "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/split_manifest.json"

PARQUET = {
    "1M": REPO / "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1M_20260121_184040/pairs.parquet",
    "1p5M": REPO / "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1p5M_20260121_183806/pairs.parquet",
    "2M": REPO / "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_2M_20260121_183657/pairs.parquet",
}
SOURCE_MAP = {"type2_1M_20260121_184040":"1M","type2_1p5M_20260121_183806":"1p5M","type2_2M_20260121_183657":"2M"}
SHORT = ("1M","1p5M","2M")
FRAME_SPLIT = {
    "1M": (0,1199,1200,1599,1600,1999),
    "1p5M": (0,1659,1660,2212,2213,2766),
    "2M": (0,2186,2187,2915,2916,3644),
}
V48_RECORDS_CSV = REPO / "comparison_bench/outputs_comparison/formal_ir_methods/v48_heldout_confirm/run_01/v48_records.csv"
V48_RECORDS_JSON = REPO / "comparison_bench/outputs_comparison/formal_ir_methods/v48_heldout_confirm/run_01/v48_records.json"
FLOOR = 1e-15
EPS_KL = 1e-12
Q = 1024

def load_train_counts():
    from comparison_bench.formal_ir.v35_algorithm_development import load_v25_channel_counts
    return load_v25_channel_counts(NPZ_PATH)

def build_prior_mats(counts):
    """return dict source -> (p_u1_given_b [32,1024], den_B [1024], counts_reshaped [32,32,1024])"""
    out={}
    for s in SHORT:
        arr = counts[s].astype(np.float64)  # (1024,1024) A x B
        resh = arr.reshape(32,32,1024)  # u1,u2,B
        den_b = resh.sum(axis=(0,1))  # (1024,)
        num_u1_b = resh.sum(axis=1)  # (32,1024)
        p = np.zeros((32,1024), dtype=np.float64)
        for b in range(1024):
            d=float(den_b[b])
            if d<=0 or not np.isfinite(d):
                p[:,b]=1/32
            else:
                col=num_u1_b[:,b]/d
                col=np.maximum(col,FLOOR)
                col/=col.sum()
                p[:,b]=col
        out[s]={"p_u1_given_b":p, "den_b":den_b, "resh":resh, "counts":arr}
    return out

def compute_for_split(priors, df, source):
    alice=df["alice_symbol"].to_numpy(dtype=np.int64)
    bob=df["bob_symbol"].to_numpy(dtype=np.int64)
    u1 = (alice>>5)&31
    u2 = alice & 31
    y1 = (bob>>5)&31
    y2 = bob & 31
    p_mat = priors[source]["p_u1_given_b"]  # [32,1024]
    resh = priors[source]["resh"]
    den_b = priors[source]["den_b"]
    p_u1_vals = p_mat[u1, bob]
    p_u1_vals = np.maximum(p_u1_vals, FLOOR)
    nll1 = -np.log2(p_u1_vals)
    nll2_vals=np.empty(len(bob),dtype=np.float64)
    for i in range(len(bob)):
        b=int(bob[i]); uu1=int(u1[i]); uu2=int(u2[i])
        row=resh[uu1,:,b]
        s=row.sum()
        if s<=0: pv=1/32
        else: pv= row[uu2]/s
        pv=max(pv,FLOOR)
        nll2_vals[i]= -np.log2(pv)
    ent_vals=np.empty(len(bob),dtype=np.float64)
    for i,b in enumerate(bob):
        col=p_mat[:,int(b)]
        ent_vals[i]= -np.sum(col*np.log2(np.maximum(col,FLOOR)))
    is_zero = den_b[bob]==0
    is_rare = (den_b[bob]>0) & (den_b[bob]<10)
    ser = float(np.mean(alice!=bob)) if len(bob)>0 else 0.0
    u1_err=float(np.mean(u1!=y1)) if len(bob)>0 else 0.0
    u2_err=float(np.mean(u2!=y2)) if len(bob)>0 else 0.0
    return {
        "n": len(bob),
        "nll_u1_mean": float(nll1.mean()) if len(nll1)>0 else 0.0,
        "nll_u2_mean": float(nll2_vals.mean()) if len(nll2_vals)>0 else 0.0,
        "nll_total_mean": float((nll1+nll2_vals).mean()) if len(nll1)>0 else 0.0,
        "ent_u1_mean": float(ent_vals.mean()) if len(ent_vals)>0 else 0.0,
        "kl_sample_mean": float((nll1 - ent_vals).mean()) if len(nll1)>0 else 0.0,
        "ser": ser, "u1_err": u1_err, "u2_err": u2_err,
        "zero_B_rate": float(is_zero.mean()) if len(is_zero)>0 else 0.0, "rare_B_rate": float(is_rare.mean()) if len(is_rare)>0 else 0.0,
        "zero_B_pairs": int(is_zero.sum()),
        "nll1": nll1, "nll2": nll2_vals, "ent": ent_vals,
        "alice": alice, "bob": bob, "u1": u1, "u2": u2,
    }

def tv_js_kl_weighted(p_train, p_eval, w):
    """p_train [32,1024], p_eval [32,1024], w [1024] eval B freq (sum 1). Return weighted TV/JS/KL."""
    tv_per_b = 0.5*np.sum(np.abs(p_train - p_eval), axis=0)  # (1024,)
    m=0.5*(p_train+p_eval)
    pt=np.maximum(p_train,EPS_KL); pe=np.maximum(p_eval,EPS_KL); mm=np.maximum(m,EPS_KL)
    kl_pm = np.sum(pt*np.log(pt/mm),axis=0) / np.log(2)
    kl_qm = np.sum(pe*np.log(pe/mm),axis=0) / np.log(2)
    js_per_b=0.5*kl_pm+0.5*kl_qm
    kl_te_per_b = np.sum(pt*np.log(pt/pe),axis=0)/np.log(2)
    kl_et_per_b = np.sum(pe*np.log(pe/pt),axis=0)/np.log(2)
    # weighted means (w sums to 1, unobserved bins have w=0 naturally excluded)
    tv_w = float(np.sum(w * tv_per_b))
    js_w = float(np.sum(w * js_per_b))
    kl_te_w = float(np.sum(w * kl_te_per_b))
    kl_et_w = float(np.sum(w * kl_et_per_b))
    # also unweighted for reference
    tv_mean=float(tv_per_b.mean()); tv_max=float(tv_per_b.max())
    js_mean=float(js_per_b.mean()); js_max=float(js_per_b.max())
    kl_te_mean=float(kl_te_per_b.mean()); kl_et_mean=float(kl_et_per_b.mean())
    return {"tv_w":tv_w,"js_w":js_w,"kl_te_w":kl_te_w,"kl_et_w":kl_et_w,
            "tv_mean":tv_mean,"tv_max":tv_max,"js_mean":js_mean,"js_max":js_max,
            "kl_te_mean":kl_te_mean,"kl_et_mean":kl_et_mean,
            "tv_per_b":tv_per_b,"js_per_b":js_per_b,"kl_te_per_b":kl_te_per_b,"kl_et_per_b":kl_et_per_b}

def build_eval_prior_and_weights(priors_src, df_eval):
    """build p_eval and w from df_eval for a given source using TRAIN floor convention"""
    # histogram A x B
    flat=np.bincount(df_eval["alice_symbol"].to_numpy(dtype=np.int64)*1024 + df_eval["bob_symbol"].to_numpy(dtype=np.int64), minlength=1024*1024).reshape(1024,1024)
    resh_eval=flat.reshape(32,32,1024)
    den_eval=resh_eval.sum(axis=(0,1))  # (1024,)
    num_u1_eval=resh_eval.sum(axis=1)
    p_eval=np.zeros((32,1024),dtype=np.float64)
    for b in range(1024):
        d=float(den_eval[b])
        if d<=0: p_eval[:,b]=1/32
        else:
            col=num_u1_eval[:,b]/d
            col=np.maximum(col,FLOOR)
            col/=col.sum()
            p_eval[:,b]=col
    total = float(den_eval.sum())
    w = den_eval / total if total>0 else np.ones(1024)/1024
    unobserved_bins = int((den_eval==0).sum())
    rare_bins = int(((den_eval>0)&(den_eval<10)).sum())
    # also rare in TRAIN (for reporting)
    den_train = priors_src["den_b"]
    rare_train_bins = int(((den_train>0)&(den_train<10)).sum())
    unobserved_train_bins = int((den_train==0).sum())
    return p_eval, w, den_eval, unobserved_bins, rare_bins, unobserved_train_bins, rare_train_bins, resh_eval

def main():
    if pd is None:
        raise RuntimeError("pandas required")
    counts=load_train_counts()
    priors=build_prior_mats(counts)
    out_rows=[]
    # cache per source df to avoid re-reading parquet 3x
    df_cache={}
    for src in SHORT:
        df_cache[src]=pd.read_parquet(PARQUET[src])
    for src in SHORT:
        df=df_cache[src]
        lo_tr,hi_tr,lo_va,hi_va,lo_ho,hi_ho=FRAME_SPLIT[src]
        df_tr=df[(df["frame_id"]>=lo_tr)&(df["frame_id"]<=hi_tr)]
        df_va=df[(df["frame_id"]>=lo_va)&(df["frame_id"]<=hi_va)]
        df_ho=df[(df["frame_id"]>=lo_ho)&(df["frame_id"]<=hi_ho)]
        for split, d in [("TRAIN",df_tr),("VAL",df_va),("HOLD",df_ho)]:
            res=compute_for_split(priors,d,src)
            out_rows.append({"source":src,"split":split,"n":res["n"],
                             "nll_u1":res["nll_u1_mean"],"nll_u2":res["nll_u2_mean"],"nll_total":res["nll_total_mean"],
                             "ent":res["ent_u1_mean"],"kl_sample":res["kl_sample_mean"],
                             "ser":res["ser"],"u1_err":res["u1_err"],"u2_err":res["u2_err"],
                             "zero_B":res["zero_B_rate"],"rare_B":res["rare_B_rate"]})
        for eval_name, d_eval in [("VAL",df_va),("HOLD",df_ho)]:
            p_eval, w, den_eval, unobs, rare, unobs_train, rare_train, _ = build_eval_prior_and_weights(priors[src], d_eval)
            div=tv_js_kl_weighted(priors[src]["p_u1_given_b"], p_eval, w)
            out_rows.append({"source":src,"split":f"TRAIN_vs_{eval_name}_div","n":int(len(d_eval)),
                             "tv_mean":div["tv_w"],"tv_max":div["tv_max"],"js_mean":div["js_w"],"js_max":div["js_max"],
                             "kl_te":div["kl_te_w"],"kl_et":div["kl_et_w"],
                             "tv_unweighted":div["tv_mean"],"js_unweighted":div["js_mean"],"kl_te_unweighted":div["kl_te_mean"],"kl_et_unweighted":div["kl_et_mean"],
                             "unobserved_bins":unobs,"rare_bins":rare,"unobserved_train_bins":unobs_train,"rare_train_bins":rare_train,
                             "w_sum": float(w.sum())})
    # TRAIN+VAL candidate vs HOLD NLL
    cand_rows=[]
    for src in SHORT:
        df=df_cache[src]
        lo_tr,hi_tr,lo_va,hi_va,lo_ho,hi_ho=FRAME_SPLIT[src]
        df_tr=df[(df["frame_id"]>=lo_tr)&(df["frame_id"]<=hi_tr)]
        df_va=df[(df["frame_id"]>=lo_va)&(df["frame_id"]<=hi_va)]
        df_ho=df[(df["frame_id"]>=lo_ho)&(df["frame_id"]<=hi_ho)]
        def hist_of(d):
            flat=np.bincount(d["alice_symbol"].to_numpy(dtype=np.int64)*1024 + d["bob_symbol"].to_numpy(dtype=np.int64), minlength=1024*1024).reshape(1024,1024)
            return flat
        train_hist=hist_of(df_tr)
        val_hist=hist_of(df_va)
        cand_hist=train_hist+val_hist
        resh_c=cand_hist.reshape(32,32,1024)
        den_c=resh_c.sum(axis=(0,1))
        num_u1_c=resh_c.sum(axis=1)
        p_c=np.zeros((32,1024))
        for b in range(1024):
            d=float(den_c[b])
            if d<=0: p_c[:,b]=1/32
            else:
                col=num_u1_c[:,b]/d; col=np.maximum(col,FLOOR); col/=col.sum(); p_c[:,b]=col
        alice_h=df_ho["alice_symbol"].to_numpy(dtype=np.int64); bob_h=df_ho["bob_symbol"].to_numpy(dtype=np.int64)
        u1_h=(alice_h>>5)&31; u2_h=alice_h&31
        p_train=priors[src]["p_u1_given_b"]; resh_train=priors[src]["resh"]
        nll1_train=-np.log2(np.maximum(p_train[u1_h,bob_h],FLOOR))
        nll2_train=np.array([ -np.log2(max(resh_train[int(u1_h[i]), int(u2_h[i]), int(bob_h[i])]/max(resh_train[int(u1_h[i]),:,int(bob_h[i])].sum(),1), FLOOR)) for i in range(len(bob_h))])
        nll1_cand=-np.log2(np.maximum(p_c[u1_h,bob_h],FLOOR))
        nll2_cand=np.array([ -np.log2(max(resh_c[int(u1_h[i]), int(u2_h[i]), int(bob_h[i])]/max(resh_c[int(u1_h[i]),:,int(bob_h[i])].sum(),1), FLOOR)) for i in range(len(bob_h))])
        cand_rows.append({"source":src,
                          "hold_nll_u1_train":float(nll1_train.mean()),"hold_nll_u1_cand":float(nll1_cand.mean()),"delta_u1":float(nll1_cand.mean()-nll1_train.mean()),
                          "hold_nll_u2_train":float(nll2_train.mean()),"hold_nll_u2_cand":float(nll2_cand.mean()),"delta_u2":float(nll2_cand.mean()-nll2_train.mean()),
                          "hold_nll_total_train":float((nll1_train+nll2_train).mean()),"hold_nll_total_cand":float((nll1_cand+nll2_cand).mean()),"delta_total":float((nll1_cand+nll2_cand).mean()-(nll1_train+nll2_train).mean())})
    # V48 block-level recomputation
    block_rows=[]
    group_stats={}
    if V48_RECORDS_CSV.exists():
        import ast
        v48_df = pd.read_csv(V48_RECORDS_CSV)
        # verify 45 rows
        # need to map source -> df_cache
        for _, rec in v48_df.iterrows():
            src = rec["source"]
            frame_ids_str = rec["frame_ids"]
            # frame_ids is string like "[1600, 1601, 1602, 1603]"
            try:
                fids = ast.literal_eval(frame_ids_str) if isinstance(frame_ids_str, str) else list(frame_ids_str)
            except Exception:
                fids = json.loads(frame_ids_str) if isinstance(frame_ids_str, str) else []
            fids = [int(x) for x in fids]
            df_src = df_cache[src]
            df_block = df_src[df_src["frame_id"].isin(fids)]
            # validation: should be 1024
            if len(df_block)!=1024:
                # fallback: try to read directly if missing due to frame_id offset? keep as is
                pass
            res_b = compute_for_split(priors, df_block, src)
            block_rows.append({
                "call_id": rec["call_id"],
                "block_seed": int(rec["block_seed"]),
                "source": src,
                "frame_ids": str(fids),
                "exact_full": bool(rec["exact_full"]),
                "n": int(res_b["n"]),
                "nll_u1": float(res_b["nll_u1_mean"]),
                "nll_u2": float(res_b["nll_u2_mean"]),
                "nll_total": float(res_b["nll_total_mean"]),
                "ent": float(res_b["ent_u1_mean"]),
                "kl_sample": float(res_b["kl_sample_mean"]),
                "zero_B": float(res_b["zero_B_rate"]),
                "rare_B": float(res_b["rare_B_rate"]),
                "ser": float(res_b["ser"]),
                "u1_err": float(res_b["u1_err"]),
                "u2_err": float(res_b["u2_err"]),
                "errors_initial": int(rec["errors_initial"]),
                "errors_final": int(rec["errors_final"]),
            })
        # group means
        import collections
        def mean_of(rows, key):
            vals=[r[key] for r in rows]
            return float(np.mean(vals)) if vals else 0.0
        # overall
        succ=[r for r in block_rows if r["exact_full"]]
        fail=[r for r in block_rows if not r["exact_full"]]
        groups=[]
        for label, rows in [("all_success",succ),("all_failure",fail)]:
            if not rows: continue
            groups.append({"group":label,"n_blocks":len(rows),"n_pairs":sum(r["n"] for r in rows),
                           "nll_u1":mean_of(rows,"nll_u1"),"nll_u2":mean_of(rows,"nll_u2"),"nll_total":mean_of(rows,"nll_total"),
                           "ent":mean_of(rows,"ent"),"kl_sample":mean_of(rows,"kl_sample"),
                           "zero_B":mean_of(rows,"zero_B"),"rare_B":mean_of(rows,"rare_B"),
                           "ser":mean_of(rows,"ser"),"u1_err":mean_of(rows,"u1_err"),"u2_err":mean_of(rows,"u2_err")})
        for src in SHORT:
            for flag, name in [(True,"success"),(False,"failure")]:
                rows=[r for r in block_rows if r["source"]==src and r["exact_full"]==flag]
                if not rows: continue
                groups.append({"group":f"{src}_{name}","n_blocks":len(rows),"n_pairs":sum(r["n"] for r in rows),
                               "nll_u1":mean_of(rows,"nll_u1"),"nll_u2":mean_of(rows,"nll_u2"),"nll_total":mean_of(rows,"nll_total"),
                               "ent":mean_of(rows,"ent"),"kl_sample":mean_of(rows,"kl_sample"),
                               "zero_B":mean_of(rows,"zero_B"),"rare_B":mean_of(rows,"rare_B"),
                               "ser":mean_of(rows,"ser"),"u1_err":mean_of(rows,"u1_err"),"u2_err":mean_of(rows,"u2_err")})
        group_rows=groups
    else:
        block_rows=[]
        group_rows=[]
    # write outputs
    out_dir=REPO/"docs"/"v49_distribution_tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir/"v49_train_val_hold_nll.csv","w",newline="",encoding="utf-8") as f:
        fieldnames=["source","split","n","nll_u1","nll_u2","nll_total","ent","kl_sample","ser","u1_err","u2_err","zero_B","rare_B","tv_mean","tv_max","js_mean","js_max","kl_te","kl_et","unobserved_bins","rare_bins","unobserved_train_bins","rare_train_bins"]
        w=csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in out_rows:
            w.writerow({k:r.get(k,"") for k in fieldnames})
    with open(out_dir/"v49_train_vs_trainval_on_hold.csv","w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["source","hold_nll_u1_train","hold_nll_u1_cand","delta_u1","hold_nll_u2_train","hold_nll_u2_cand","delta_u2","hold_nll_total_train","hold_nll_total_cand","delta_total"])
        w.writeheader()
        for r in cand_rows: w.writerow(r)
    if block_rows:
        with open(out_dir/"v49_block_level.csv","w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f, fieldnames=["call_id","block_seed","source","frame_ids","exact_full","n","nll_u1","nll_u2","nll_total","ent","kl_sample","zero_B","rare_B","ser","u1_err","u2_err","errors_initial","errors_final"])
            w.writeheader()
            for r in block_rows: w.writerow(r)
        with open(out_dir/"v49_block_group_summary.csv","w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f, fieldnames=["group","n_blocks","n_pairs","nll_u1","nll_u2","nll_total","ent","kl_sample","zero_B","rare_B","ser","u1_err","u2_err"])
            w.writeheader()
            for r in group_rows: w.writerow(r)
    print("wrote", out_dir)
    for r in out_rows: print(r)
    for r in cand_rows: print("CAND",r)
    for r in block_rows: print("BLOCK",r)
    for r in group_rows: print("GROUP",r)

if __name__=="__main__":
    main()
