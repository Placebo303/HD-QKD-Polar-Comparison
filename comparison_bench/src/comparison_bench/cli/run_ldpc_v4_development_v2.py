"""Immutable v2 development package for the backend-corrected LDPC v4 evaluator."""
from __future__ import annotations
import argparse, csv, hashlib, importlib.metadata, json, time
from pathlib import Path
from typing import Any, Callable, Mapping
from ..formal_ir import ldpc_v3_ttbin_data as source_data
from ..formal_ir.codebook_v4 import candidate_manifest, candidate_entry
from ..formal_ir.ldpc_v4_channel import build_adjacent_channel_model
from ..formal_ir.ldpc_v4_development_v2 import (FRAME_COUNT, READINESS_FLOOR, ROLE, STRATA, aggregate_frame_development, canonical_development_policy, evaluate_candidate, generate_sacrificed_development, select_candidates)
from . import run_ldpc_v4_development as v1_test_helpers

ARTIFACTS=("pre_run_plan.json","v4_candidate_manifest.json","v4_channel_model.json","development_plane_outcomes.csv","development_selection.json","development_run_manifest.json","development_report.json")
RUN_ID="binary_ldpc_v4_development_v2"
FIELDS=("role","stratum_id","plane_id","candidate_id","channel_model_sha256","policy_sha256","matrix_sha256","candidate_valid","backend_identity","frame_id","attempted","status","exact_match","syndrome_bits_disclosed","runtime_s","source_sha256")
PREDECESSOR_RUN_ID="binary_ldpc_v4_development_v1"
PREDECESSOR_SHA256={"pre_run_plan.json":"493e98c6b6492f9216204be63f4bec10d0c6aa817e4302dfc5de7ee3c0401ac7","development_plane_outcomes.csv":"4c59e156b3a90a1554b117a5371f5c6ce6f50a9d9bf3258bbe236a76dbbca8b9","development_report.json":"55c56b6764eca9511aab8e30f491ffcc664872faa453cc33de2ab933dcaa4dd6"}

def _compact(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")
def _sha(v:bytes)->str:return hashlib.sha256(v).hexdigest()
def _json(p:Path,v:Any)->None:p.open("xb").write(_compact(v))
def _write(p:Path,v:bytes)->None:p.open("xb").write(v)
def _self(v:dict[str,Any],k:str)->dict[str,Any]:return {**v,k:_sha(_compact(v))}
def _hashes()->dict[str,str]:
 root=Path(__file__).resolve().parents[1]; names={"runner.py":"cli/run_ldpc_v4_development_v2.py","verifier.py":"cli/verify_ldpc_v4_development_v2.py","development.py":"formal_ir/ldpc_v4_development_v2.py","channel.py":"formal_ir/ldpc_v4_channel.py","codebook.py":"formal_ir/codebook_v4.py","v3_data.py":"formal_ir/ldpc_v3_ttbin_data.py","method.py":"formal_ir/ldpc_v4.py"}
 return {k:_sha((root/p).read_bytes()) for k,p in names.items()}
def _predecessor(p:Path)->dict[str,Any]:
 if not p.is_dir():raise ValueError("predecessor package required")
 names=("pre_run_plan.json","development_plane_outcomes.csv","development_report.json")
 if not all((p/n).is_file() for n in names):raise ValueError("predecessor artifacts")
 got={n:_sha((p/n).read_bytes()) for n in names}
 if got!=PREDECESSOR_SHA256:raise ValueError("predecessor hash binding")
 return {"run_id":PREDECESSOR_RUN_ID,"artifact_sha256":got}
def _lock_from_v3_plan(p:Path)->dict[str,Any]:
 d=json.loads(p.read_text(encoding="utf-8")); l=d.get("locked_data")
 if not isinstance(l,dict):raise ValueError("v3 plan has no locked_data")
 source_data.verify_locked_data(l);return l
def _plan(lock:Mapping[str,Any],pre:Mapping[str,Any],*,test_only:bool=False)->dict[str,Any]:
 source_data.verify_locked_data(lock); model=build_adjacent_channel_model(lock); manifest=candidate_manifest(); n=2 if test_only else FRAME_COUNT
 base={"schema":"binary_ldpc_v4_development_plan_v2","run_id":RUN_ID,"role":ROLE,"method_id":"ldpc_formal_v4","dimension":1024,"mapping":"gray_msb_first","frame_len_symbols":256,"frame_count_per_stratum":n,"strata":list(STRATA),"candidate_ids":[0,1,2,3],"plane_ids":list(range(10)),"readiness_floor":2 if test_only else READINESS_FLOOR,"locked_data":dict(lock),"locked_data_sha256":lock["lock_sha256"],"source_manifest_sha256":lock["source_manifest_sha256"],"predecessor":dict(pre),"channel_model_sha256":model["model_sha256"],"candidate_manifest_sha256":manifest["manifest_sha256"],"development_policy":canonical_development_policy(),"execution_order":[[s,p,c] for s in STRATA for p in range(10) for c in range(4)],"expected_plane_outcomes":len(STRATA)*10*4*n,"expected_frame_outcomes":len(STRATA)*n,"caps":{"complete_run_s":1800,"per_frame_s":5.0},"failure_finalizer":"seven_file_failure_retention_v2","scoped_source_sha256":_hashes(),"backend_requirement":"ldpc==2.4.1","_test_only":bool(test_only)}
 return _self(base,"plan_sha256")
def _validate_plan(plan:Mapping[str,Any],*,test_only:bool)->dict[str,Any]:
 if not isinstance(plan,dict) or plan.get("plan_sha256")!=_sha(_compact({k:v for k,v in plan.items() if k!="plan_sha256"})):raise ValueError("plan self hash")
 if bool(plan.get("_test_only"))!=test_only:raise ValueError("test-only plan")
 source_data.verify_locked_data(plan["locked_data"]);model=build_adjacent_channel_model(plan["locked_data"])
 if plan["locked_data_sha256"]!=plan["locked_data"]["lock_sha256"] or plan["channel_model_sha256"]!=model["model_sha256"] or plan["candidate_manifest_sha256"]!=candidate_manifest()["manifest_sha256"]:raise ValueError("plan lock binding")
 expected_pre={"run_id":PREDECESSOR_RUN_ID,"artifact_sha256":{} if test_only else PREDECESSOR_SHA256}
 if plan.get("predecessor")!=expected_pre:raise ValueError("predecessor binding")
 order=[[s,p,c] for s in STRATA for p in range(10) for c in range(4)]
 if plan["development_policy"]!=canonical_development_policy() or plan["execution_order"]!=order or plan["frame_count_per_stratum"]!=(2 if test_only else FRAME_COUNT):raise ValueError("plan frozen order")
 if set(plan)!={"schema","run_id","role","method_id","dimension","mapping","frame_len_symbols","frame_count_per_stratum","strata","candidate_ids","plane_ids","readiness_floor","locked_data","locked_data_sha256","source_manifest_sha256","predecessor","channel_model_sha256","candidate_manifest_sha256","development_policy","execution_order","expected_plane_outcomes","expected_frame_outcomes","caps","failure_finalizer","scoped_source_sha256","backend_requirement","_test_only","plan_sha256"}:raise ValueError("plan keys")
 if plan!=_plan(plan["locked_data"],expected_pre,test_only=test_only):raise ValueError("plan frozen equality")
 if not test_only and (plan["scoped_source_sha256"]!=_hashes() or importlib.metadata.version("ldpc")!="2.4.1"):raise ValueError("production source/backend drift")
 return dict(plan)
def prepare_plan(output_dir:Path,v3_plan:Path,predecessor_dir:Path)->dict[str,Any]:
 if output_dir.exists():raise FileExistsError("fresh output directory required")
 plan=_plan(_lock_from_v3_plan(v3_plan),_predecessor(predecessor_dir));output_dir.mkdir(parents=True);_json(output_dir/ARTIFACTS[0],plan);return plan
def _prepare_test_plan(output_dir:Path,lock:Mapping[str,Any],pre:Mapping[str,Any]|None=None)->dict[str,Any]:
 if output_dir.exists():raise FileExistsError("fresh output directory required")
 plan=_plan(lock,{"run_id":PREDECESSOR_RUN_ID,"artifact_sha256":{}} if pre is None else pre,test_only=True);output_dir.mkdir(parents=True);_json(output_dir/ARTIFACTS[0],plan);return plan
def _csv(rows:list[Mapping[str,Any]])->bytes:
 import io
 f=io.StringIO(newline="");w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator="\n",extrasaction="raise");w.writeheader()
 for r in rows:
  if set(r)!=set(FIELDS):raise ValueError("outcome schema")
  w.writerow({k:("true" if r[k] else "false") if k in {"candidate_valid","attempted","exact_match"} else repr(float(r[k])) if k=="runtime_s" else r[k] for k in FIELDS})
 return f.getvalue().encode("utf-8")
def _gate(a:Mapping[str,Any],floor:int)->dict[str,Any]:return {"readiness_floor":floor,"strata":{s:dict(a["stratum_aggregates"][s]) for s in STRATA},"ready":bool(a["ready_for_synthetic_prepare"])}
def _finalize(out:Path,plan:Mapping[str,Any],rows:list[dict[str,Any]],reason:str,status:str)->None:
 model=build_adjacent_channel_model(plan["locked_data"]); manifest=candidate_manifest()
 for n,v in ((ARTIFACTS[1],manifest),(ARTIFACTS[2],model)):
  if not (out/n).exists():_json(out/n,v)
 if not (out/ARTIFACTS[3]).exists():_write(out/ARTIFACTS[3],_csv(rows))
 selection=None;aggregate=None
 try:
  if len(rows)==plan["expected_plane_outcomes"]:
   if plan["_test_only"]:selection,aggregate=v1_test_helpers._test_selection_aggregation(rows,model)
   else:selection=select_candidates(rows,model,codebook_manifest=manifest);aggregate=aggregate_frame_development(rows,selection,model)
 except Exception:
  if status=="completed":raise
 if selection is None:selection={"schema":"binary_ldpc_v4_selection_partial_v2","selection_status":"incomplete","observed_plane_outcomes":len(rows)}
 if not (out/ARTIFACTS[4]).exists():_json(out/ARTIFACTS[4],selection)
 index={n:{"sha256":_sha((out/n).read_bytes()),"bytes":(out/n).stat().st_size} for n in ARTIFACTS[:5]}
 man=_self({"schema":"binary_ldpc_v4_development_run_manifest_v2","run_id":RUN_ID,"run_status":status,"stop_reason":reason,"plan_sha256":plan["plan_sha256"],"observed_plane_outcomes":len(rows),"expected_plane_outcomes":plan["expected_plane_outcomes"],"artifact_index":index,"decoder_reexecution":False},"manifest_sha256")
 if not (out/ARTIFACTS[5]).exists():_json(out/ARTIFACTS[5],man)
 rep=_self({"schema":"binary_ldpc_v4_development_report_v2","run_id":RUN_ID,"run_status":status,"stop_reason":reason,"ready_for_synthetic_prepare":False if aggregate is None else bool(aggregate["ready_for_synthetic_prepare"]),"readiness_gate":None if aggregate is None else _gate(aggregate,plan["readiness_floor"]),"selection_sha256":selection.get("selection_sha256"),"plan_sha256":plan["plan_sha256"],"run_manifest_sha256":_sha((out/ARTIFACTS[5]).read_bytes()),"decoder_reexecution":False},"report_sha256")
 if not (out/ARTIFACTS[6]).exists():_json(out/ARTIFACTS[6],rep)
def _execute(out:Path,factory:Callable[...,Any]|None,*,test_only:bool)->None:
 if not out.is_dir() or {x.name for x in out.iterdir()}!={ARTIFACTS[0]}:raise ValueError("execute requires only reviewed plan")
 plan=_validate_plan(json.loads((out/ARTIFACTS[0]).read_bytes()),test_only=test_only);rows=[];started=time.monotonic()
 try:
  model=build_adjacent_channel_model(plan["locked_data"])
  for s,p,c in plan["execution_order"]:
   if time.monotonic()-started>plan["caps"]["complete_run_s"]:raise TimeoutError("complete_run_cap")
   d=generate_sacrificed_development(model,s);got=evaluate_candidate(d["alice_frames"],d["bob_frames"],model=model,plane_id=p,candidate_id=c,stratum=s,frame_ids=d["frame_ids"],decoder_factory=factory,max_runtime_s=plan["caps"]["per_frame_s"])
   for r in got:r["source_sha256"]=d["source_sha256"]
   rows.extend(got[:plan["frame_count_per_stratum"]])
  if len(rows)!=plan["expected_plane_outcomes"]:raise RuntimeError("outcome accounting")
  _finalize(out,plan,rows,"completed","completed")
 except Exception as exc:
  _finalize(out,plan,rows,f"{type(exc).__name__}:{exc}","failed")
  if not test_only:raise
def execute_plan(output_dir:Path)->None:_execute(output_dir,None,test_only=False)
def _execute_test_plan(output_dir:Path,factory:Callable[...,Any])->None:_execute(output_dir,factory,test_only=True)
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--output-dir",type=Path,required=True);p.add_argument("--mode",choices=("prepare","execute"),required=True);p.add_argument("--v3-plan",type=Path);p.add_argument("--predecessor-dir",type=Path);a=p.parse_args()
 if a.mode=="prepare":
  if a.v3_plan is None or a.predecessor_dir is None:p.error("--v3-plan and --predecessor-dir required for prepare")
  prepare_plan(a.output_dir,a.v3_plan,a.predecessor_dir)
 else:execute_plan(a.output_dir)
 return 0
if __name__=="__main__":raise SystemExit(main())
