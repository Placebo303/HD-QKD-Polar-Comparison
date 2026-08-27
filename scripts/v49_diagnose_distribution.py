#!/usr/bin/env python3
"""
V49 只读分布迁移诊断 — 不改 H1，不重做 Lane C，不运行 decoder。

固定 prior: load_v25_channel_counts() -> channel_counts.npz (TRAIN 60% only)
评估池: v13r3fresh_pairs_20260816/*.parquet 按 split_manifest 60/20/20 切 TRAIN/VAL/HOLD
  - 按 frame_id 升序 contiguous: 1M 0-1199/1200-1599/1600-1999, 1p5M 0-1659/1660-2212/2213-2766, 2M 0-2186/2187-2915/2916-3644
  - 每帧 256 pairs, block 1024 pairs = 4 帧 (仅用于 V48 块级对比)

计算 (decoder-free):
  - P_TRAIN(U1|B) NLL / CE, P_TRAIN(U2|B,U1) NLL / CE  (floor 1e-15, 与 v48 冻结一致)
  - 每源 TV / JS / 平滑 KL (epsilon=1e-12)
  - initial error (SER_total, U1_err, U2_err), 零计数/罕见 Bob bin 覆盖
  - V48 45 held-out 块: 成功(30) vs 失败(15) prior NLL/entropy/零计数率
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
    # (train_lo, train_hi, val_lo, val_hi, hold_lo, hold_hi) inclusive, from v48 TRAIN_FRAME_RANGES + manifest counts
    "1M": (0,1199,1200,1599,1600,1999),
    "1p5M": (0,1659,1660,2212,2213,2766),
    "2M": (0,2186,2187,2915,2916,3644),
}
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

def factorize(a,b):
    a=np.asarray(a,dtype=np.int64); b=np.asarray(b,dtype=np.int64)
    return (a>>5)&31, a&31, (b>>5)&31, b&31

def nll_u1(p_u1_given_b, bob, u1):
    # p_u1_given_b [32,1024]
    p = p_u1_given_b[u1, bob]  # advanced indexing: need per element
    # p_u1_given_b is [32,1024], pick column bob then row u1
    # vectorized: p = p_u1_given_b[u1, bob] not valid 2D; do:
    vals = p_u1_given_b[u1, bob] if False else np.array([p_u1_given_b[u1[i], bob[i]] for i in range(len(bob))], dtype=np.float64)
    vals=np.maximum(vals,FLOOR)
    return -np.log2(vals)

def nll_u2(resh, bob, u1, u2):
    # resh [32,32,1024]
    # P(U2|B,U1)= resh[u1,u2,B]/sum_{u2} resh[u1,:,B]
    vals=np.empty(len(bob),dtype=np.float64)
    for i in range(len(bob)):
        b=int(bob[i]); uu1=int(u1[i]); uu2=int(u2[i])
        row=resh[uu1,:,b]  # (32,)
        s=row.sum()
        if s<=0: vals[i]=1/32
        else: vals[i]= max(row[uu2]/s, FLOOR)
    return -np.log2(vals)

def eval_pool(priors, alice, bob):
    u1,a2,y1,y2 = factorize(alice,bob)  # actually u1=ax1, u2=ax2, y1=bx1, y2=...
    # rename: u1=u1_alice, u2=u2_alice, y1,y2 unused for NLL but for errors
    # need per source prior; this helper called per source
    raise NotImplementedError

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
    # NLLs
    # vectorized gather
    # p_u1: need p_mat[u1[i], bob[i]]
    p_u1_vals = p_mat[u1, bob]  # this works because p_mat is 2D, numpy advanced indexing yields array
    # Actually p_mat[u1, bob] where both are arrays does elementwise: p_mat[u1[i], bob[i]]
    # numpy does that for 2D: p_mat[u1, bob] -> array of same shape as u1,bob
    p_u1_vals = np.maximum(p_u1_vals, FLOOR)
    nll1 = -np.log2(p_u1_vals)
    # nll2
    nll2_vals=np.empty(len(bob),dtype=np.float64)
    for i in range(len(bob)):
        b=int(bob[i]); uu1=int(u1[i]); uu2=int(u2[i])
        row=resh[uu1,:,b]
        s=row.sum()
        if s<=0: pv=1/32
        else: pv= row[uu2]/s
        pv=max(pv,FLOOR)
        nll2_vals[i]= -np.log2(pv)
    # entropy of prior at those B's: H = -sum p log p per B, mean
    ent_vals=np.empty(len(bob),dtype=np.float64)
    for i,b in enumerate(bob):
        col=p_mat[:,int(b)]
        ent_vals[i]= -np.sum(col*np.log2(np.maximum(col,FLOOR)))
    # zero / rare Bob bins
    is_zero = den_b[bob]==0
    is_rare = (den_b[bob]>0) & (den_b[bob]<10)  # <10 TRAIN counts in that B bin (very rare)
    # errors
    ser = np.mean(alice!=bob)
    u1_err=np.mean(u1!=y1)
    u2_err=np.mean(u2!=y2)  # unconditional U2 mismatch
    return {
        "n": len(bob),
        "nll_u1_mean": float(nll1.mean()),
        "nll_u2_mean": float(nll2_vals.mean()),
        "nll_total_mean": float((nll1+nll2_vals).mean()),
        "ent_u1_mean": float(ent_vals.mean()),
        "kl_u1_mean": float((nll1 - ent_vals).mean()),  # CE - H = KL (approx, since CE = H+KL)
        "ser": float(ser), "u1_err": float(u1_err), "u2_err": float(u2_err),
        "zero_B_rate": float(is_zero.mean()), "rare_B_rate": float(is_rare.mean()),
        "zero_B_pairs": int(is_zero.sum()),
        "nll1": nll1, "nll2": nll2_vals, "ent": ent_vals,
        "alice": alice, "bob": bob, "u1": u1, "u2": u2,
    }

def tv_js_kl(p_train, p_eval):
    # both [32,1024] column-stochastic with floor
    # TV per B then mean weighted by eval B frequency? Here uniform over B bins that appear.
    # Use mean over 1024 bins (unweighted) as distribution distance.
    tv_per_b = 0.5*np.sum(np.abs(p_train - p_eval), axis=0)  # (1024,)
    tv_mean=float(tv_per_b.mean())
    tv_max=float(tv_per_b.max())
    # JS
    m=0.5*(p_train+p_eval)
    # KL with eps
    pt=np.maximum(p_train,EPS_KL); pe=np.maximum(p_eval,EPS_KL); mm=np.maximum(m,EPS_KL)
    kl_pm = np.sum(pt*np.log(pt/mm),axis=0) / np.log(2)  # bits, per B
    kl_qm = np.sum(pe*np.log(pe/mm),axis=0) / np.log(2)
    js_per_b=0.5*kl_pm+0.5*kl_qm
    js_mean=float(js_per_b.mean()); js_max=float(js_per_b.max())
    # smoothed KL TRAIN->EVAL mean
    kl_train_eval = np.sum(pt*np.log(pt/pe),axis=0)/np.log(2)
    kl_eval_train = np.sum(pe*np.log(pe/pt),axis=0)/np.log(2)
    return {"tv_mean":tv_mean,"tv_max":tv_max,"js_mean":js_mean,"js_max":js_max,
            "kl_te_mean":float(kl_train_eval.mean()),"kl_et_mean":float(kl_eval_train.mean())}

def main():
    if pd is None:
        raise RuntimeError("pandas required")
    counts=load_train_counts()
    priors=build_prior_mats(counts)
    out_rows=[]
    # load parquet once per source
    for src in SHORT:
        df=pd.read_parquet(PARQUET[src])
        lo_tr,hi_tr,lo_va,hi_va,lo_ho,hi_ho=FRAME_SPLIT[src]
        df_tr=df[(df["frame_id"]>=lo_tr)&(df["frame_id"]<=hi_tr)]
        df_va=df[(df["frame_id"]>=lo_va)&(df["frame_id"]<=hi_va)]
        df_ho=df[(df["frame_id"]>=lo_ho)&(df["frame_id"]<=hi_ho)]
        for split, d in [("TRAIN",df_tr),("VAL",df_va),("HOLD",df_ho)]:
            res=compute_for_split(priors,d,src)
            out_rows.append({"source":src,"split":split,"n":res["n"],
                             "nll_u1":res["nll_u1_mean"],"nll_u2":res["nll_u2_mean"],"nll_total":res["nll_total_mean"],
                             "ent":res["ent_u1_mean"],"kl":res["kl_u1_mean"],
                             "ser":res["ser"],"u1_err":res["u1_err"],"u2_err":res["u2_err"],
                             "zero_B":res["zero_B_rate"],"rare_B":res["rare_B_rate"]})
        # divergence TRAIN vs VAL/HOLD using empirical eval prior built from that split's counts
        for eval_name, d_eval in [("VAL",df_va),("HOLD",df_ho)]:
            # build empirical eval prior from d_eval histogram
            hist=np.zeros((1024,1024),dtype=np.float64)
            # hist[A,B] counts
            # use numpy bincount on combined index
            idx = d_eval["alice_symbol"].to_numpy(dtype=np.int64)*1024 + d_eval["bob_symbol"].to_numpy(dtype=np.int64)
            # faster via np.add.at
            flat=np.bincount(idx, minlength=1024*1024).reshape(1024,1024)
            resh_eval=flat.reshape(32,32,1024)
            den_eval=resh_eval.sum(axis=(0,1))
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
            div=tv_js_kl(priors[src]["p_u1_given_b"], p_eval)
            out_rows.append({"source":src,"split":f"TRAIN_vs_{eval_name}_div","n":int(len(d_eval)),
                             "tv_mean":div["tv_mean"],"tv_max":div["tv_max"],"js_mean":div["js_mean"],"js_max":div["js_max"],
                             "kl_te":div["kl_te_mean"],"kl_et":div["kl_et_mean"]})
    # TRAIN+VAL candidate vs HOLD NLL
    cand_rows=[]
    for src in SHORT:
        df=pd.read_parquet(PARQUET[src])
        lo_tr,hi_tr,lo_va,hi_va,lo_ho,hi_ho=FRAME_SPLIT[src]
        df_tr=df[(df["frame_id"]>=lo_tr)&(df["frame_id"]<=hi_tr)]
        df_va=df[(df["frame_id"]>=lo_va)&(df["frame_id"]<=hi_va)]
        df_ho=df[(df["frame_id"]>=lo_ho)&(df["frame_id"]<=hi_ho)]
        # build TRAIN+VAL counts
        def hist_of(d): 
            flat=np.bincount(d["alice_symbol"].to_numpy(dtype=np.int64)*1024 + d["bob_symbol"].to_numpy(dtype=np.int64), minlength=1024*1024).reshape(1024,1024)
            return flat
        train_hist=hist_of(df_tr)
        val_hist=hist_of(df_va)
        cand_hist=train_hist+val_hist
        # build cand prior
        resh_c=cand_hist.reshape(32,32,1024)
        den_c=resh_c.sum(axis=(0,1))
        num_u1_c=resh_c.sum(axis=1)
        p_c=np.zeros((32,1024))
        for b in range(1024):
            d=float(den_c[b])
            if d<=0: p_c[:,b]=1/32
            else:
                col=num_u1_c[:,b]/d; col=np.maximum(col,FLOOR); col/=col.sum(); p_c[:,b]=col
        # compute HOLD NLL under TRAIN and under CAND
        alice_h=df_ho["alice_symbol"].to_numpy(dtype=np.int64); bob_h=df_ho["bob_symbol"].to_numpy(dtype=np.int64)
        u1_h=(alice_h>>5)&31; u2_h=alice_h&31
        # TRAIN NLL already? recompute quickly
        p_train=priors[src]["p_u1_given_b"]; resh_train=priors[src]["resh"]
        nll1_train=-np.log2(np.maximum(p_train[u1_h,bob_h],FLOOR))
        nll2_train=np.array([ -np.log2(max(resh_train[int(u1_h[i]), int(u2_h[i]), int(bob_h[i])]/max(resh_train[int(u1_h[i]),:,int(bob_h[i])].sum(),1), FLOOR)) for i in range(len(bob_h))])
        nll1_cand=-np.log2(np.maximum(p_c[u1_h,bob_h],FLOOR))
        nll2_cand=np.array([ -np.log2(max(resh_c[int(u1_h[i]), int(u2_h[i]), int(bob_h[i])]/max(resh_c[int(u1_h[i]),:,int(bob_h[i])].sum(),1), FLOOR)) for i in range(len(bob_h))])
        cand_rows.append({"source":src,
                          "hold_nll_u1_train":float(nll1_train.mean()),"hold_nll_u1_cand":float(nll1_cand.mean()),"delta_u1":float(nll1_cand.mean()-nll1_train.mean()),
                          "hold_nll_u2_train":float(nll2_train.mean()),"hold_nll_u2_cand":float(nll2_cand.mean()),"delta_u2":float(nll2_cand.mean()-nll2_train.mean()),
                          "hold_nll_total_train":float((nll1_train+nll2_train).mean()),"hold_nll_total_cand":float((nll1_cand+nll2_cand).mean()),"delta_total":float((nll1_cand+nll2_cand).mean()-(nll1_train+nll2_train).mean())})
    # write outputs
    out_dir=REPO/"docs"/"v49_distribution_tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    import csv
    with open(out_dir/"v49_train_val_hold_nll.csv","w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["source","split","n","nll_u1","nll_u2","nll_total","ent","kl","ser","u1_err","u2_err","zero_B","rare_B","tv_mean","tv_max","js_mean","js_max","kl_te","kl_et"])
        w.writeheader()
        for r in out_rows: w.writerow({k:r.get(k,"") for k in w.fieldnames})
    with open(out_dir/"v49_train_vs_trainval_on_hold.csv","w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["source","hold_nll_u1_train","hold_nll_u1_cand","delta_u1","hold_nll_u2_train","hold_nll_u2_cand","delta_u2","hold_nll_total_train","hold_nll_total_cand","delta_total"])
        w.writeheader()
        for r in cand_rows: w.writerow(r)
    print("wrote", out_dir)
    # also print summary
    for r in out_rows: print(r)
    for r in cand_rows: print("CAND",r)

if __name__=="__main__":
    main()
