"""Immutable sacrificed-development package for the frozen LDPC v4 contract.

The private helpers are test-only.  Production preparation receives the
already immutable v3 Phase-6 plan and rebuilds its locked calibration.
"""
from __future__ import annotations

import argparse, csv, hashlib, importlib.metadata, json, sys, time
from pathlib import Path
from typing import Any, Callable, Mapping

from ..formal_ir import ldpc_v3_ttbin_data as source_data
from ..formal_ir.codebook_v4 import candidate_manifest
from ..formal_ir.ldpc_v4_channel import build_adjacent_channel_model, verify_adjacent_channel_model
from ..formal_ir.ldpc_v4_development import (FRAME_COUNT, READINESS_FLOOR, ROLE, STRATA,
    aggregate_frame_development, canonical_development_policy, evaluate_candidate,
    generate_sacrificed_development, select_candidates)
from ..formal_ir.codebook_v4 import candidate_entry

ARTIFACTS=("pre_run_plan.json","v4_candidate_manifest.json","v4_channel_model.json",
           "development_plane_outcomes.csv","development_selection.json",
           "development_run_manifest.json","development_report.json")
RUN_ID="binary_ldpc_v4_development_v1"
FIELDS=("role","stratum_id","plane_id","candidate_id","channel_model_sha256","policy_sha256",
        "matrix_sha256","candidate_valid","backend_identity","frame_id","attempted","status",
        "exact_match","syndrome_bits_disclosed","runtime_s","source_sha256")

def _compact(v: Any) -> bytes: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")
def _sha(v: bytes) -> str: return hashlib.sha256(v).hexdigest()
def _json(path:Path,v:Any)->None: path.open("xb").write(_compact(v))
def _write(path:Path,v:bytes)->None: path.open("xb").write(v)
def _self(v:dict[str,Any], key:str)->dict[str,Any]: return {**v,key:_sha(_compact(v))}
def _hashes()->dict[str,str]:
    root=Path(__file__).resolve().parents[1]
    names={"runner.py":"cli/run_ldpc_v4_development.py","verifier.py":"cli/verify_ldpc_v4_development.py",
           "development.py":"formal_ir/ldpc_v4_development.py","channel.py":"formal_ir/ldpc_v4_channel.py",
           "codebook.py":"formal_ir/codebook_v4.py","v3_data.py":"formal_ir/ldpc_v3_ttbin_data.py",
           "method.py":"formal_ir/ldpc_v4.py"}
    return {k:_sha((root/p).read_bytes()) for k,p in names.items()}
def _lock_from_v3_plan(path:Path)->dict[str,Any]:
    doc=json.loads(path.read_text(encoding="utf-8")); lock=doc.get("locked_data")
    if not isinstance(lock,dict): raise ValueError("v3 plan has no locked_data")
    source_data.verify_locked_data(lock)
    return lock
def _plan(lock:Mapping[str,Any], *, test_only:bool=False)->dict[str,Any]:
    source_data.verify_locked_data(lock); model=build_adjacent_channel_model(lock); manifest=candidate_manifest()
    base={"schema":"binary_ldpc_v4_development_plan_v1","run_id":RUN_ID,"role":ROLE,"method_id":"ldpc_formal_v4",
      "dimension":1024,"mapping":"gray_msb_first","frame_len_symbols":256,"frame_count_per_stratum":2 if test_only else FRAME_COUNT,
      "strata":list(STRATA),"candidate_ids":[0,1,2,3],"plane_ids":list(range(10)),"readiness_floor":2 if test_only else READINESS_FLOOR,
      "locked_data":dict(lock),"locked_data_sha256":lock["lock_sha256"],"source_manifest_sha256":lock["source_manifest_sha256"],
      "channel_model_sha256":model["model_sha256"],"candidate_manifest_sha256":manifest["manifest_sha256"],
      "development_policy":canonical_development_policy(),"execution_order":[[s,p,c] for s in STRATA for p in range(10) for c in range(4)],
      "expected_plane_outcomes":len(STRATA)*10*4*(2 if test_only else FRAME_COUNT),"expected_frame_outcomes":len(STRATA)*(2 if test_only else FRAME_COUNT),
      "caps":{"complete_run_s":1800,"per_frame_s":5.0},"failure_finalizer":"seven_file_failure_retention_v1",
      "scoped_source_sha256":_hashes(),"backend_requirement":"ldpc==2.4.1","_test_only":bool(test_only)}
    return _self(base,"plan_sha256")
def _validate_plan(plan:Mapping[str,Any],*,test_only:bool)->dict[str,Any]:
    if not isinstance(plan,dict) or plan.get("plan_sha256")!=_sha(_compact({k:v for k,v in plan.items() if k!="plan_sha256"})): raise ValueError("plan self hash")
    if bool(plan.get("_test_only"))!=test_only: raise ValueError("test-only plan")
    source_data.verify_locked_data(plan["locked_data"]); model=build_adjacent_channel_model(plan["locked_data"])
    if plan["locked_data_sha256"]!=plan["locked_data"]["lock_sha256"] or plan["channel_model_sha256"]!=model["model_sha256"] or plan["candidate_manifest_sha256"]!=candidate_manifest()["manifest_sha256"]: raise ValueError("plan lock binding")
    expected_order=[[s,p,c] for s in STRATA for p in range(10) for c in range(4)]
    if plan["development_policy"]!=canonical_development_policy() or plan["execution_order"]!=expected_order or plan["frame_count_per_stratum"]!=(2 if test_only else FRAME_COUNT): raise ValueError("plan frozen order")
    if plan != _plan(plan["locked_data"],test_only=test_only): raise ValueError("plan frozen equality")
    if not test_only and (plan["scoped_source_sha256"]!=_hashes() or importlib.metadata.version("ldpc")!="2.4.1"): raise ValueError("production source/backend drift")
    return dict(plan)
def prepare_plan(output_dir:Path, v3_plan:Path)->dict[str,Any]:
    if output_dir.exists(): raise FileExistsError("fresh output directory required")
    plan=_plan(_lock_from_v3_plan(v3_plan)); output_dir.mkdir(parents=True); _json(output_dir/ARTIFACTS[0],plan); return plan
def _prepare_test_plan(output_dir:Path, lock:Mapping[str,Any])->dict[str,Any]:
    if output_dir.exists(): raise FileExistsError("fresh output directory required")
    plan=_plan(lock,test_only=True); output_dir.mkdir(parents=True); _json(output_dir/ARTIFACTS[0],plan); return plan
def _csv(rows:list[Mapping[str,Any]])->bytes:
    import io
    f=io.StringIO(newline=""); w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator="\n",extrasaction="raise");w.writeheader()
    for r in rows:
        if set(r)!=set(FIELDS): raise ValueError("outcome schema")
        w.writerow({k:("true" if r[k] else "false") if k in {"candidate_valid","attempted","exact_match"} else repr(float(r[k])) if k=="runtime_s" else r[k] for k in FIELDS})
    return f.getvalue().encode("utf-8")
def _gate(aggregation:Mapping[str,Any], readiness_floor:int=READINESS_FLOOR)->dict[str,Any]:
    strata={s:dict(aggregation["stratum_aggregates"][s]) for s in STRATA}
    return {"readiness_floor":readiness_floor,"strata":strata,"ready":bool(aggregation["ready_for_synthetic_prepare"])}
def _test_selection_aggregation(rows:list[dict[str,Any]],model:Mapping[str,Any])->tuple[dict[str,Any],dict[str,Any]]:
    selections=[]
    for plane in range(10):
        choices=[]
        for candidate in range(4):
            ns=sum(r["status"]=="development_exact_success" for r in rows if r["plane_id"]==plane and r["candidate_id"]==candidate and r["stratum_id"]==STRATA[0]); ss=sum(r["status"]=="development_exact_success" for r in rows if r["plane_id"]==plane and r["candidate_id"]==candidate and r["stratum_id"]==STRATA[1]); choices.append(([-min(ns,ss),-(ns+ss),candidate],candidate,ns,ss))
        key,candidate,ns,ss=min(choices); e=candidate_entry(plane,candidate); selections.append({"plane_id":plane,"candidate_id":candidate,"canonical_bytes_sha256":e["canonical_bytes_sha256"],"nominal_successes":ns,"stress_successes":ss,"selection_key":key})
    base={"schema":"binary_ldpc_v4_selection_v1","method_id":"ldpc_formal_v4","codebook_manifest_sha256":candidate_manifest()["manifest_sha256"],"channel_model_sha256":model["model_sha256"],"plane_selections":selections}; selection=_self(base,"selection_sha256")
    selected={x["plane_id"]:x["candidate_id"] for x in selections}; ag={}
    for s in STRATA:
        success=0
        for i in range(2): success+=all(next(r for r in rows if r["stratum_id"]==s and r["plane_id"]==p and r["candidate_id"]==selected[p] and r["frame_id"]==f"v4dev_{s}_f{i:03d}")["status"]=="development_exact_success" for p in range(10))
        ag[s]={"denominator_frames":2,"frame_exact_successes":success,"plane_status_counts":{},"forbidden_failure_count":0}
    return selection,{"stratum_aggregates":ag,"ready_for_synthetic_prepare":all(x["frame_exact_successes"]>=2 for x in ag.values())}
def _finalize(out:Path,plan:Mapping[str,Any],rows:list[dict[str,Any]],reason:str,status:str)->None:
    lock=plan["locked_data"]; model=build_adjacent_channel_model(lock); manifest=candidate_manifest()
    if not (out/ARTIFACTS[1]).exists(): _json(out/ARTIFACTS[1],manifest)
    if not (out/ARTIFACTS[2]).exists(): _json(out/ARTIFACTS[2],model)
    if not (out/ARTIFACTS[3]).exists(): _write(out/ARTIFACTS[3],_csv(rows))
    selection=None; aggregation=None
    try:
        if len(rows)==plan["expected_plane_outcomes"]:
            selection,aggregation=_test_selection_aggregation(rows,model) if plan["_test_only"] else (select_candidates(rows,model,codebook_manifest=manifest),None)
            if not plan["_test_only"]: aggregation=aggregate_frame_development(rows,selection,model)
    except Exception:
        if status=="completed": raise
        selection=None
    if selection is None: selection={"schema":"binary_ldpc_v4_selection_partial_v1","selection_status":"incomplete","observed_plane_outcomes":len(rows)}
    if not (out/ARTIFACTS[4]).exists(): _json(out/ARTIFACTS[4],selection)
    index={n:{"sha256":_sha((out/n).read_bytes()),"bytes":(out/n).stat().st_size} for n in ARTIFACTS[:5]}
    man=_self({"schema":"binary_ldpc_v4_development_run_manifest_v1","run_id":RUN_ID,"run_status":status,"stop_reason":reason,
               "plan_sha256":plan["plan_sha256"],"observed_plane_outcomes":len(rows),"expected_plane_outcomes":plan["expected_plane_outcomes"],
               "artifact_index":index,"decoder_reexecution":False},"manifest_sha256")
    if not (out/ARTIFACTS[5]).exists(): _json(out/ARTIFACTS[5],man)
    report=_self({"schema":"binary_ldpc_v4_development_report_v1","run_id":RUN_ID,"run_status":status,"stop_reason":reason,
                  "ready_for_synthetic_prepare":False if aggregation is None else bool(aggregation["ready_for_synthetic_prepare"]),
                  "readiness_gate":None if aggregation is None else _gate(aggregation,plan["readiness_floor"]),"selection_sha256":selection.get("selection_sha256"),
                  "plan_sha256":plan["plan_sha256"],"run_manifest_sha256":_sha((out/ARTIFACTS[5]).read_bytes()),"decoder_reexecution":False},"report_sha256")
    if not (out/ARTIFACTS[6]).exists(): _json(out/ARTIFACTS[6],report)
def _execute(out:Path, factory:Callable[...,Any]|None, *,test_only:bool)->None:
    if not out.is_dir() or {x.name for x in out.iterdir()}!={ARTIFACTS[0]}: raise ValueError("execute requires only reviewed plan")
    plan=_validate_plan(json.loads((out/ARTIFACTS[0]).read_bytes()),test_only=test_only); rows=[]; started=time.monotonic()
    try:
      model=build_adjacent_channel_model(plan["locked_data"])
      for stratum,plane,candidate in plan["execution_order"]:
        if time.monotonic()-started>plan["caps"]["complete_run_s"]: raise TimeoutError("complete_run_cap")
        d=generate_sacrificed_development(model,stratum)
        got=evaluate_candidate(d["alice_frames"],d["bob_frames"],model=model,plane_id=plane,candidate_id=candidate,stratum=stratum,frame_ids=d["frame_ids"],decoder_factory=factory,max_runtime_s=plan["caps"]["per_frame_s"])
        for row in got: row["source_sha256"]=d["source_sha256"]
        rows.extend(got[:plan["frame_count_per_stratum"]])
      if len(rows)!=plan["expected_plane_outcomes"]: raise RuntimeError("outcome accounting")
      _finalize(out,plan,rows,"completed","completed")
    except Exception as exc:
      _finalize(out,plan,rows,f"{type(exc).__name__}:{exc}","failed")
      if not test_only: raise
def execute_plan(output_dir:Path)->None: _execute(output_dir,None,test_only=False)
def _execute_test_plan(output_dir:Path,factory:Callable[...,Any])->None: _execute(output_dir,factory,test_only=True)
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--output-dir",type=Path,required=True);p.add_argument("--mode",choices=("prepare","execute"),required=True);p.add_argument("--v3-plan",type=Path)
 a=p.parse_args()
 if a.mode=="prepare":
  if a.v3_plan is None:p.error("--v3-plan required for prepare")
  prepare_plan(a.output_dir,a.v3_plan)
 else: execute_plan(a.output_dir)
 return 0
if __name__=="__main__": raise SystemExit(main())
