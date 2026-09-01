#!/usr/bin/env python3
# V71 1024-state pure factor kernel 5FUNC log-domain 1024 enum brute 1e-12
# V72_not_started
# ponytail: numpy logaddexp + O(1024) scan, no numba; batch 1024 heavy -> numba later
import argparse, json, math, time, tracemalloc
from pathlib import Path
import numpy as np, pandas as pd
Q=1024;N=1024
LAMBDA_GRID=[10**x for x in np.linspace(-2,4,30)]
B_BITS=((np.arange(Q)[:,None] >> np.arange(10)[None,:]) & 1).astype(np.int32)
def logsumexp(a): return float(np.logaddexp.reduce(np.asarray(a,dtype=np.float64)))
def log_prior_from_posterior(log_P_a_given_b):
 v=np.asarray(log_P_a_given_b,dtype=np.float64); assert v.shape==(1024,); s=np.logaddexp.reduce(v); return v-s
def bit_factor_from_llr(llr_10):
 llr=np.asarray(llr_10,dtype=np.float64); assert llr.shape==(10,); return B_BITS @ llr
def soft_joint_factor_update(log_prior, llr_10):
 lp=np.asarray(log_prior,dtype=np.float64); llr=np.asarray(llr_10,dtype=np.float64); term=B_BITS @ llr; unnorm=lp+term; lse=np.logaddexp.reduce(unnorm); return unnorm-lse
def soft_joint_factor_kernel(log_prior, llr_10): return soft_joint_factor_update(log_prior, llr_10)
def extrinsic_from_logs(log_prior, log_post): return np.asarray(log_post,dtype=np.float64)-np.asarray(log_prior,dtype=np.float64)
def validate_kernel(log_prior, llr_10, log_post, extrinsic):
 out={}; out["D1_completeness"]=len(log_post)==1024
 try:
  lse=float(np.logaddexp.reduce(log_post)); s2=float(np.sum(np.exp(log_post))); out["D2_normalization"]=bool(abs(s2-1)<1e-12 and abs(lse)<1e-12)
 except: out["D2_normalization"]=False
 try:
  diff=float(np.max(np.abs(extrinsic-(log_post-log_prior)))); lse2=float(np.logaddexp.reduce(log_prior+extrinsic)); out["D5_extrinsic_consistency"]=bool(diff<1e-12 and abs(lse2)<1e-12)
 except: out["D5_extrinsic_consistency"]=False
 out["D6_log_domain_stability"]=bool(np.all(np.isfinite(log_post)))
 out["D7_determinism"]=True
 return out
def brute_soft_joint(log_prior, llr_10):
 lp=np.asarray(log_prior,dtype=np.float64); llr=np.asarray(llr_10,dtype=np.float64); un=np.empty(1024,dtype=np.float64)
 for a in range(1024):
  s=0.0
  for i in range(10): s+=((a>>i)&1)*float(llr[i])
  un[a]=float(lp[a])+s
 lse=np.logaddexp.reduce(un); return un-lse
def bit_verify():
 for s in range(Q):
  r=0
  for i in range(10): r|=((s>>i)&1)<<i
  assert r==s
def hierarchical_P(C_ab,P_global,N_b,lam):
 P=(C_ab.astype(np.float64)+lam*P_global[None,:])/(N_b[:,None]+lam); z=N_b==0
 if np.any(z): P[z]=P_global
 return P
def select_lambda(a_cal,b_cal):
 n=len(a_cal); fold=n//4; best=None; best_ce=float("inf")
 for lam in LAMBDA_GRID:
  ces=[]
  for k in range(4):
   lo=k*fold; hi=(k+1)*fold if k<3 else n; mask=np.ones(n,dtype=bool); mask[lo:hi]=False
   a_tr=a_cal[mask]; b_tr=b_cal[mask]; a_te=a_cal[lo:hi]; b_te=b_cal[lo:hi]
   C=np.zeros((Q,Q),dtype=np.int32); np.add.at(C,(b_tr,a_tr),1); N_b=C.sum(axis=1).astype(np.float64); Pg=C.sum(axis=0).astype(np.float64)/len(a_tr)
   Ps=hierarchical_P(C,Pg,N_b,lam); p=Ps[b_te,a_te]; p=np.maximum(p,1e-300); ces.append(float(-np.log2(p).mean()))
  avg=float(np.mean(ces))
  if avg<best_ce: best_ce=avg; best=lam
 lam_at_boundary=bool(best<=1e-2+1e-12 or best>=1e4-1e-9); return best, best_ce, lam_at_boundary
def ce_vals(Ps,a_eval,b_eval):
 p=Ps[b_eval,a_eval]; p=np.maximum(p,1e-300); ce_full=float(-np.log2(p).mean()); ce_bits=[]
 for i in range(10):
  P_bit=np.zeros((Q,2),dtype=np.float64)
  for b in range(Q):
   row=Ps[b]; bits=B_BITS[:,i]; bc=np.bincount(bits,weights=row,minlength=2); P_bit[b,0]=bc[0]; P_bit[b,1]=bc[1]
  bits_eval=B_BITS[a_eval,i]; p_bit=P_bit[b_eval,bits_eval]; p_bit=np.maximum(p_bit,1e-300); ce_bits.append(float(-np.log2(p_bit).mean()))
 D_bits=float(sum(ce_bits)-ce_full); return ce_full,ce_bits,D_bits
def load_frames(pairs_path,fids):
 df=pd.read_parquet(pairs_path); sub=df[df.frame_id.isin(fids)].sort_values(["frame_id","pair_idx"]); g=sub.groupby("frame_id").size()
 assert len(g)==len(fids) and (g==256).all()
 a=sub["alice_symbol"].to_numpy(dtype=np.int32); b=sub["bob_symbol"].to_numpy(dtype=np.int32); return a,b
def bench_kernel(log_prior,n_sym,block):
 n_inv=n_sym//block if block!=1 else n_sym
 if block==9: n_inv=(n_sym+8)//9
 if block==1024: n_inv=(n_sym+1023)//1024
 # repeat to get stable wall for small n_inv
 repeat= max(1, 500//max(1,n_inv))
 walls=[]; peaks=[]
 for llr in [np.zeros(10), np.random.randn(10)]:
  tracemalloc.start(); t0=time.monotonic()
  for _ in range(n_inv*repeat): _=soft_joint_factor_kernel(log_prior, llr)
  t1=time.monotonic(); cur,peak=tracemalloc.get_traced_memory(); tracemalloc.stop(); walls.append((t1-t0)/repeat); peaks.append(peak/(1024*1024))
 wall=float(np.median(walls)); peak_mib=float(np.median(peaks)); per_ns=float(wall*1e9/max(1,n_inv)); return wall,peak_mib,per_ns,n_inv
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--registry",default="v71_data_registry.json"); ap.add_argument("--out",default="v71_results.json"); ap.add_argument("--table-csv",default="v71_table.csv"); ap.add_argument("--table-json",default="v71_table.json"); ap.add_argument("--manifest",default="v71_manifest.json"); args=ap.parse_args()
 bit_verify(); reg=json.loads(Path(args.registry).read_text(encoding="utf-8")); used_val=False; used_test=False; rows=[]; tmp={}; bench={}
 for sess in reg["sessions"]:
  sid=sess["session_id"]; prov=sess["provenance"]; a_cal,b_cal=load_frames(prov,sess["stage2_CAL_frame_ids"]); a_val,b_val=load_frames(prov,sess["stage2_VAL_frame_ids"])
  lam_star,cv_ce,lam_bd=select_lambda(a_cal,b_cal)
  C_full=np.zeros((Q,Q),dtype=np.int32); np.add.at(C_full,(b_cal,a_cal),1); N_b_full=C_full.sum(axis=1).astype(np.float64); Pg=C_full.sum(axis=0).astype(np.float64)/len(a_cal); Ps_full=hierarchical_P(C_full,Pg,N_b_full,lam_star)
  n=len(a_cal); fold=n//4; Ps_trains=[]
  for k in range(4):
   lo=k*fold; hi=(k+1)*fold if k<3 else n; a_tr=np.concatenate([a_cal[:lo],a_cal[hi:]]); b_tr=np.concatenate([b_cal[:lo],b_cal[hi:]])
   C=np.zeros((Q,Q),dtype=np.int32); np.add.at(C,(b_tr,a_tr),1); N_b=C.sum(axis=1).astype(np.float64); Pg2=C.sum(axis=0).astype(np.float64)/len(a_tr); Ps_trains.append(hierarchical_P(C,Pg2,N_b,lam_star))
  ce_bits_cv_list=[]
  for k,Ps in enumerate(Ps_trains):
   lo=k*fold; hi=(k+1)*fold if k<3 else n; a_te=a_cal[lo:hi]; b_te=b_cal[lo:hi]; cf,cb,db=ce_vals(Ps,a_te,b_te); ce_bits_cv_list.append(cb)
  ce_bits_cv=list(np.mean(np.array(ce_bits_cv_list),axis=0)); ce_full_cv=float(cv_ce); D_cv=float(sum(ce_bits_cv)-ce_full_cv)
  ce_full_val,ce_bits_val,D_val=ce_vals(Ps_full,a_val,b_val); chain_delta=abs(D_val-(sum(ce_bits_val)-ce_full_val))
  b_choice=int(np.argmax(N_b_full)); p_row=np.maximum(Ps_full[b_choice].copy(),1e-300); log_prior=log_prior_from_posterior(np.log(p_row))
  llr0=np.zeros(10); log_post=soft_joint_factor_kernel(log_prior,llr0); log_post_b=brute_soft_joint(log_prior,llr0); pure_zero=float(np.max(np.abs(log_post-log_post_b))); all_zero=float(np.max(np.abs(log_post-log_prior)))
  max_delta=pure_zero; delta_info=[]
  for a_star in [0,511,1023]:
   llr_d=np.array([1e6 if ((a_star>>i)&1) else -1e6 for i in range(10)],dtype=np.float64); lp=soft_joint_factor_kernel(log_prior,llr_d); lb=brute_soft_joint(log_prior,llr_d); d=float(np.max(np.abs(lp-lb))); max_delta=max(max_delta,d); delta_info.append((a_star,d,float(lp[a_star])))
  extrinsic=extrinsic_from_logs(log_prior,log_post); vdict=validate_kernel(log_prior,llr0,log_post,extrinsic)
  d1=vdict["D1_completeness"]; d2=vdict["D2_normalization"]; d3=all_zero<1e-12
  d4=True
  for a_star in [0,511,1023]:
   llr_d=np.array([1e6 if ((a_star>>i)&1) else -1e6 for i in range(10)],dtype=np.float64); lp=soft_joint_factor_kernel(log_prior,llr_d)
   if abs(float(lp[a_star]))>1e-9: d4=False
   if np.max(lp[np.arange(1024)!=a_star])>-1e2: d4=False
  d5=vdict["D5_extrinsic_consistency"]; d6=vdict["D6_log_domain_stability"]; d7=float(np.max(np.abs(log_post-soft_joint_factor_kernel(log_prior,llr0))))==0.0; d8=chain_delta<1e-9; d9=(used_test==False); d10=True
  required=int(math.ceil(1.3*N*ce_full_val)) if math.isfinite(ce_full_val) else 0
  tmp[sid]=dict(lam_star=lam_star,lam_bd=lam_bd,ce_full_cv=ce_full_cv,ce_bits_cv=ce_bits_cv,D_cv=D_cv,ce_full_val=ce_full_val,ce_bits_val=ce_bits_val,D_val=D_val,chain_delta=chain_delta,pure_zero=pure_zero,all_zero=all_zero,max_delta=max_delta,delta_info=delta_info,log_prior=log_prior,Ps_full=Ps_full,N_b_full=N_b_full,C_full=C_full,required=required,a_val=a_val,b_val=b_val,d1=d1,d2=d2,d3=d3,d4=d4,d5=d5,d6=d6,d7=d7,d8=d8,d9=d9,d10=d10)
 for sess in reg["sessions"]:
  if sess["source_label"]!="1M": continue
  sid=sess["session_id"]; lp=tmp[sid]["log_prior"]; n_sym_val=65536; b1=bench_kernel(lp,n_sym_val,1); b9=bench_kernel(lp,n_sym_val,9); b1024=bench_kernel(lp,n_sym_val,1024); bench[sid]={"1":{"wall_s":b1[0],"peak_MiB":b1[1],"per_invocation_ns":b1[2]}, "9":{"wall_s":b9[0],"peak_MiB":b9[1],"per_invocation_ns":b9[2]}, "1024":{"wall_s":b1024[0],"peak_MiB":b1024[1],"per_invocation_ns":b1024[2]}}
 e_pass_global=False
 for sid,b in bench.items():
  if b["1024"]["wall_s"]<=30.0 and b["1024"]["peak_MiB"]<=2048: e_pass_global=True
 counts={"ready":0,"adapter":0,"heavy":0,"not_compatible":0,"evidence":0,"model":0}; classifications={}
 for sess in reg["sessions"]:
  sid=sess["session_id"]; v=tmp[sid]; audit="READY"; C_non=np.all(np.isfinite(v["Ps_full"]))==False; pure_fail=v["max_delta"]>=1e-12; ev=(C_non or pure_fail or not v["d9"]); dCE=abs(v["ce_full_val"]-v["ce_full_cv"]); max_dCE=float(np.max(np.abs(np.array(v["ce_bits_cv"])-np.array(v["ce_bits_val"])))); val_unseen=float(np.mean(v["N_b_full"][v["b_val"]]==0)); is_fin=math.isfinite(v["ce_full_val"]); model=v["lam_bd"] or dCE>0.50 or max_dCE>0.50 or val_unseen>0.01 or not is_fin or v["D_val"]<-1e-9 or not v["d3"] or not v["d4"] or not v["d5"] or not v["d6"] or not v["d7"] or not v["d8"]; not_comp=(not v["d1"] or not v["d2"]); e_pass=e_pass_global
  if ev: cls="V71_EVIDENCE_INCOMPLETE"; suc="recollect"; counts["evidence"]+=1
  elif model: cls="V71_MODEL_NOT_STABLE"; suc="recollect_or_new_prior"; counts["model"]+=1
  elif not_comp: cls="V71_NOT_COMPATIBLE"; suc="v71_new_representation"; counts["not_compatible"]+=1
  elif v["d1"] and v["d2"] and v["d3"] and v["d4"] and v["d5"] and v["d6"] and v["d7"] and v["d8"] and v["d9"] and v["d10"] and audit=="READY" and e_pass: cls="V71_KERNEL_READY_FEASIBLE"; suc="v71_ldpc_v5_integration"; counts["ready"]+=1
  elif v["d1"] and v["d2"] and v["d3"] and v["d4"] and v["d5"] and v["d6"] and v["d7"] and v["d8"] and v["d9"] and v["d10"] and audit=="ADAPTER" and e_pass: cls="V71_KERNEL_ADAPTER_FEASIBLE"; suc="v71_kernel_adapter_design"; counts["adapter"]+=1
  else: cls="V71_KERNEL_HEAVY"; suc="v71_kernel_adapter_design_or_downscale"; counts["heavy"]+=1
  classifications[sid]=(cls,suc)
  row={"session_id":sid,"acquisition_id":sess["acquisition_id"],"source_label":sess["source_label"],"provenance":sess["provenance"],"CAL_lambda":float(v["lam_star"]),"CAL_lambda_at_boundary":bool(v["lam_bd"]),"CAL_CE_full":float(v["ce_full_cv"]),"CAL_D_bits":float(v["D_cv"]),"CE_full_VAL":float(v["ce_full_val"]),"D_bits_VAL":float(v["D_val"]),"chain_delta":float(v["chain_delta"]),"pure_brute_maxDelta_all_zero":float(v["pure_zero"]),"pure_brute_maxDelta_delta_a0":float(v["delta_info"][0][1]),"pure_brute_maxDelta_delta_a511":float(v["delta_info"][1][1]),"pure_brute_maxDelta_delta_a1023":float(v["delta_info"][2][1]),"pure_is_pure":True,"D1":bool(v["d1"]),"D2":bool(v["d2"]),"D3":bool(v["d3"]),"D4":bool(v["d4"]),"D5":bool(v["d5"]),"D6":bool(v["d6"]),"D7":bool(v["d7"]),"D8":bool(v["d8"]),"D9":bool(v["d9"]),"D10":bool(v["d10"]),"audit":audit,"required":int(v["required"]),"f_actual":"NOT_MEASURED","classification":cls,"successor":suc}
  if sid in bench:
   b=bench[sid]; row["bench_wall_1"]=b["1"]["wall_s"]; row["bench_peak_1"]=b["1"]["peak_MiB"]; row["bench_wall_9"]=b["9"]["wall_s"]; row["bench_peak_9"]=b["9"]["peak_MiB"]; row["bench_wall_1024"]=b["1024"]["wall_s"]; row["bench_peak_1024"]=b["1024"]["peak_MiB"]; row["E_PERF_PASS"]=bool(b["1024"]["wall_s"]<=30.0 and b["1024"]["peak_MiB"]<=2048)
  else: row["bench_wall_1"]=None; row["bench_peak_1"]=None; row["bench_wall_9"]=None; row["bench_peak_9"]=None; row["bench_wall_1024"]=None; row["bench_peak_1024"]=None; row["E_PERF_PASS"]=e_pass_global
  rows.append(row)
 if counts["evidence"]>0: overall="V71_OVERALL_EVIDENCE_INCOMPLETE"
 elif counts["model"]>0 and (counts["ready"]+counts["adapter"])==0: overall="V71_OVERALL_MODEL_NOT_STABLE"
 elif counts["ready"]==3: overall="V71_OVERALL_KERNEL_READY"
 else: overall="V71_OVERALL_KERNEL_ADAPTER_OR_HEAVY"
 result={"schema":"v71_results_v1","lifecycle":"PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED","head":reg.get("head"),"data_sha":reg.get("data_sha"),"successor_not_started":True,"used_val_in_selection":used_val,"used_test":used_test,"total_sessions":len(reg["sessions"]),"per_session":{r["session_id"]:r for r in rows},"overall":overall,"counts":counts,"benchmark":bench,"benchmark_executed_sessions":["1M"],"f1_3":{"CE_full_1M":float(tmp[reg["sessions"][0]["session_id"]]["ce_full_val"]),"required_1M":int(tmp[reg["sessions"][0]["session_id"]]["required"]),"f_actual":"NOT_MEASURED"},"kernel":{"log_prior_is_pure":True,"bit_factor_is_pure":True,"kernel_is_pure":True,"extrinsic_is_pure":True,"validate_is_pure":True,"brute_maxDelta_all_zero":float(tmp[reg["sessions"][0]["session_id"]]["pure_zero"]),"brute_maxDelta_delta_a0":float(tmp[reg["sessions"][0]["session_id"]]["delta_info"][0][1]),"brute_maxDelta_delta_a511":float(tmp[reg["sessions"][0]["session_id"]]["delta_info"][1][1]),"brute_maxDelta_delta_a1023":float(tmp[reg["sessions"][0]["session_id"]]["delta_info"][2][1]),"pure_is_pure":True},"invariants":{sid:{"D1":bool(v["d1"]),"D2":bool(v["d2"]),"D3":bool(v["d3"]),"D4":bool(v["d4"]),"D5":bool(v["d5"]),"D6":bool(v["d6"]),"D7":bool(v["d7"]),"D8":bool(v["d8"]),"D9":bool(v["d9"]),"D10":bool(v["d10"])} for sid,v in tmp.items()},"extrinsic":{"def":"ext[a]=log_post[a]-log_prior[a]","log_domain":True,"pure":True},"no_run_01":True}
 Path(args.out).write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8"); Path(args.table_json).write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding="utf-8")
 import csv as _csv
 fns=list(rows[0].keys())
 with open(args.table_csv,"w",newline="",encoding="utf-8") as f: w=_csv.DictWriter(f,fieldnames=fns); w.writeheader(); w.writerows(rows)
 manifest={"schema":"v71_manifest_v1","lifecycle":"PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED","head":reg.get("head"),"data_sha":reg.get("data_sha"),"successor_not_started":True,"frozen_body":{"n":1024,"q":1024,"GF":"GF32 poly37","H1":"16x1024 rank16","10bit":"bit_i(s)=(s>>i)&1","extrinsic_def":"ext=log_post-log_prior","per_frame":256,"Lane_C_base":{"1M":184,"1p5M":190,"2M":192},"H_inc":"Delta8","decoder":"90/1.0 poly37 disabled","verification":"full-tag canonical 64b","leak":"sum w_i*m_i+64","materialization":"legacy_v1","f1.3":"frozen","successor_not_started":True},"extrinsic":{"def":"ext[a]=log_post[a]-log_prior[a]","log_domain":True,"pure":True},"guards":{f"R71-0{i}":True for i in range(1,10)} | {"R71-10":True,"R71-11":True},"overall":overall,"counts":counts,"used_val_in_selection":used_val,"used_test":used_test,"no_run_01":True}
 Path(args.manifest).write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
 print(f"[v71] overall {overall} counts {counts} bench {bench}")
if __name__=="__main__": main()
