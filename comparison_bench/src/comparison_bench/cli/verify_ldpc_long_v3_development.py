"""Read-only integrity verifier; it never re-executes a decoder."""
from __future__ import annotations

import argparse, csv, json, math, platform, re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from .run_ldpc_long_v3_development import ARTIFACTS, FIELDS, ROLE, _aggregate, _code_hashes, _compact, _sha, _valid_plan
from ..formal_ir.codebook_long_v3 import candidate_manifest, prefix_rows, verify_candidate_manifest
from ..formal_ir.long_v3_development import PREFIX_IDS, _ALLOWED_STATUSES, canonical_development_policy, generate_sacrificed_development, select_candidate

UTC=re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$")
def _json(path:Path)->dict[str,Any]:
    raw=path.read_bytes()
    try: value=json.loads(raw)
    except Exception as exc: raise ValueError("invalid json") from exc
    if not isinstance(value,dict) or _compact(value)!=raw: raise ValueError("noncanonical json")
    return value
def _self(doc:Mapping[str,Any],key:str)->None:
    if doc.get(key)!=_sha(_compact({k:v for k,v in doc.items() if k!=key})): raise ValueError("json self hash")
def _int(s:str)->int:
    if not s or str(int(s))!=s: raise ValueError("integer encoding")
    return int(s)
def _float(s:str)->float:
    x=float(s)
    if not math.isfinite(x) or s!=repr(float(x)): raise ValueError("float encoding")
    return x
def _bool(s:str)->bool:
    if s not in ("true","false"): raise ValueError("boolean encoding")
    return s=="true"
def _count(value:Any)->int:
    if not isinstance(value,int) or isinstance(value,bool) or value<0: raise ValueError("count type")
    return value
def _rows(path:Path)->list[dict[str,Any]]:
    raw=path.read_bytes()
    if not raw.endswith(b"\n") or b"\r" in raw: raise ValueError("csv terminator")
    records=list(csv.DictReader(raw.decode("utf-8").splitlines()))
    if (records and list(records[0])!=list(FIELDS)) or (not records and raw != (",".join(FIELDS)+"\n").encode()): raise ValueError("csv schema")
    out=[]
    for r in records:
        if list(r)!=list(FIELDS) or any(v is None for v in r.values()): raise ValueError("csv fields")
        out.append({"n":_int(r["n"]),"plane_id":_int(r["plane_id"]),"candidate_id":_int(r["candidate_id"]),"stratum_id":r["stratum_id"],"frame_id":r["frame_id"],"attempted":_bool(r["attempted"]),"status":r["status"],"terminal_prefix_id":r["terminal_prefix_id"],"rounds_attempted":_int(r["rounds_attempted"]),"syndrome_bits_disclosed":_int(r["syndrome_bits_disclosed"]),"exact_match":_bool(r["exact_match"]),"policy_id":r["policy_id"],"p_hat":_float(r["p_hat"]),"backend_identity":r["backend_identity"],"runtime_s":_float(r["runtime_s"]),"role":r["role"],"source_sha256":r["source_sha256"]})
    return out
def _row_ok(r:Mapping[str,Any], d:Mapping[str,Any], *, test_only:bool)->None:
    n=int(r["n"]); status=r["status"]; terminal=r["terminal_prefix_id"]
    if r["role"]!=ROLE or r["p_hat"]!=d["p_hat"] or r["source_sha256"]!=d["source_sha256"] or r["policy_id"]!=canonical_development_policy(n)["policy_id"] or r["backend_identity"] != ("test_injected" if test_only else "ldpc==2.4.1") or not math.isfinite(r["runtime_s"]) or r["runtime_s"]<0 or status not in _ALLOWED_STATUSES: raise ValueError("outcome metadata")
    if status=="development_backend_unavailable":
        if r["attempted"] or terminal or r["rounds_attempted"] or r["syndrome_bits_disclosed"] or r["exact_match"]: raise ValueError("backend outcome accounting")
    else:
        if not r["attempted"] or terminal not in PREFIX_IDS or r["rounds_attempted"]!=PREFIX_IDS.index(terminal)+1 or r["syndrome_bits_disclosed"]!=prefix_rows(n)[terminal] or r["exact_match"] != (status=="development_exact_success") or (status=="development_decode_failed" and terminal!="p0875"): raise ValueError("attempted outcome accounting")
def _verify(output:Path, *, test_only:bool)->dict[str,Any]:
    if not output.is_dir() or {p.name for p in output.iterdir()}!=set(ARTIFACTS): raise ValueError("top-level artifacts")
    plan=_json(output/ARTIFACTS[0]); _valid_plan(plan,test_only=test_only)
    cand_raw=(output/ARTIFACTS[1]).read_bytes(); cand=_json(output/ARTIFACTS[1]); verify_candidate_manifest(cand)
    if cand!=candidate_manifest() or _sha(cand_raw)!=plan["candidate_manifest_sha256"]: raise ValueError("candidate manifest DAG")
    rows=_rows(output/ARTIFACTS[2]); selections=_json(output/ARTIFACTS[3]); manifest=_json(output/ARTIFACTS[4]); report=_json(output/ARTIFACTS[5])
    sk={"schema_version","run_id","role","test_only","plan_sha256","outcomes_sha256","selection_count","selections","selections_sha256"}
    if set(selections)!=sk or selections["schema_version"]!="binary_ldpc_long_v3_development_selections_v1": raise ValueError("selections schema")
    _self(selections,"selections_sha256")
    if not isinstance(selections["selections"],list) or selections["test_only"] is not test_only or _count(selections["selection_count"])!=len(selections["selections"]) or selections["run_id"]!=plan["run_id"] or selections["role"]!=ROLE or selections["plan_sha256"]!=plan["plan_sha256"] or selections["outcomes_sha256"]!=_sha((output/ARTIFACTS[2]).read_bytes()): raise ValueError("selections DAG")
    expected=[]; sources={}
    for n in plan["grid"]["block_lengths"]:
      for plane in plan["grid"]["plane_ids"]:
       for st in plan["grid"]["stratum_ids"]: sources[n,plane,st]=generate_sacrificed_development(n,plane,.01 if st=="p001" else .02)
       for candidate in plan["grid"]["candidate_ids"]:
        for st in plan["grid"]["stratum_ids"]:
         d=sources[n,plane,st]
         expected += [(n,plane,candidate,st,f,d) for f in d["frame_ids"]]
    if len(rows)>len(expected) or [(r["n"],r["plane_id"],r["candidate_id"],r["stratum_id"],r["frame_id"]) for r in rows] != [x[:5] for x in expected[:len(rows)]]: raise ValueError("execution order")
    for r,item in zip(rows,expected): _row_ok(r,item[5],test_only=test_only)
    # Only exact completed n/plane blocks may be selected; failures may end in a partial block.
    rebuilt=[]
    for n in plan["grid"]["block_lengths"]:
      for plane in plan["grid"]["plane_ids"]:
       group=[r for r in rows if r["n"]==n and r["plane_id"]==plane]
       if group:
        if len(group)==128: rebuilt.append(select_candidate(group))
        elif len(group)>128: raise ValueError("group accounting")
    mk={"schema_version","run_id","role","test_only","status","stop_reason","utc_start","utc_end","actual_argv","backend_identity","python_version","numpy_version","dependency_version","process_elapsed_s","expected_outcome_count","observed_outcome_count","expected_selection_count","observed_selection_count","code_sha256","artifact_index","manifest_content_sha256"}
    if set(manifest)!=mk or manifest["schema_version"]!="binary_ldpc_long_v3_development_manifest_v1": raise ValueError("manifest schema")
    _self(manifest,"manifest_content_sha256")
    if (not isinstance(manifest["test_only"],bool) or not all(isinstance(manifest[k],str) for k in ("status","stop_reason","backend_identity","dependency_version","python_version","numpy_version","utc_start","utc_end")) or not UTC.match(manifest["utc_start"]) or not UTC.match(manifest["utc_end"])): raise ValueError("manifest types")
    start=datetime.strptime(manifest["utc_start"],"%Y-%m-%dT%H:%M:%S.%fZ"); end=datetime.strptime(manifest["utc_end"],"%Y-%m-%dT%H:%M:%S.%fZ")
    if end<start or not isinstance(manifest["actual_argv"],list) or not manifest["actual_argv"] or not all(isinstance(x,str) for x in manifest["actual_argv"]) or manifest["actual_argv"] != (["<test-helper>"] if test_only else manifest["actual_argv"]) or manifest["run_id"]!=plan["run_id"] or manifest["role"]!=ROLE or manifest["test_only"] is not test_only or manifest["backend_identity"] != ("test_injected" if test_only else "ldpc==2.4.1") or manifest["dependency_version"] != ("test_injected" if test_only else "2.4.1") or manifest["python_version"]!=platform.python_version() or manifest["numpy_version"]!=np.__version__ or manifest["code_sha256"]!=plan["code_sha256"] or manifest["code_sha256"]!=_code_hashes() or not isinstance(manifest["process_elapsed_s"],float) or not math.isfinite(manifest["process_elapsed_s"]) or manifest["process_elapsed_s"]<0 or _count(manifest["expected_outcome_count"])!=plan["expected_outcome_count"] or _count(manifest["expected_selection_count"])!=plan["expected_selection_count"] or _count(manifest["observed_outcome_count"])!=len(rows) or _count(manifest["observed_selection_count"])!=len(rebuilt): raise ValueError("manifest fields")
    index={n:{"sha256":_sha((output/n).read_bytes()),"bytes":(output/n).stat().st_size} for n in ARTIFACTS[:4]}
    if manifest["artifact_index"]!=index: raise ValueError("artifact index")
    success=manifest["status"]=="development_run_completed"
    expected_backend="test_injected" if test_only else "ldpc==2.4.1"
    if manifest["status"] not in {"development_run_completed","development_run_failed"} or (success and manifest["stop_reason"]!="completed") or (not success and not (manifest["stop_reason"]=="internal_cap_exceeded" or str(manifest["stop_reason"]).startswith("exception:"))) or (success and (len(rows)!=plan["expected_outcome_count"] or len(rebuilt)!=plan["expected_selection_count"] or any(r["backend_identity"]!=expected_backend or r["status"]=="development_backend_unavailable" for r in rows))): raise ValueError("run status")
    if rebuilt!=selections["selections"]: raise ValueError("selection reconstruction")
    rk={"schema_version","run_id","role","test_only","status","stop_reason","observed_outcome_count","observed_selection_count","aggregates","selected_candidates","development_only_not_qualification_or_promotion","plan_sha256","run_manifest_sha256","report_content_sha256"}
    if set(report)!=rk or report["schema_version"]!="binary_ldpc_long_v3_development_report_v1": raise ValueError("report schema")
    _self(report,"report_content_sha256")
    selected=[{"n":x["n"],"plane_id":x["plane_id"],"candidate_id":x["selected_candidate_id"],"selection_sha256":x["selection_sha256"]} for x in rebuilt]
    if not isinstance(report["test_only"],bool) or not isinstance(report["aggregates"],dict) or not isinstance(report["selected_candidates"],list) or _count(report["observed_outcome_count"])!=len(rows) or _count(report["observed_selection_count"])!=len(rebuilt) or report["run_id"]!=plan["run_id"] or report["role"]!=ROLE or report["test_only"] is not test_only or report["status"]!=manifest["status"] or report["stop_reason"]!=manifest["stop_reason"] or report["aggregates"]!=_aggregate(rows,rebuilt) or report["selected_candidates"]!=selected or report["development_only_not_qualification_or_promotion"] is not True or report["plan_sha256"]!=plan["plan_sha256"] or report["run_manifest_sha256"]!=_sha((output/ARTIFACTS[4]).read_bytes()): raise ValueError("report DAG")
    return {"status":"verified","run_status":manifest["status"],"outcome_count":len(rows),"selection_count":len(rebuilt),"manifest_sha256":_sha((output/ARTIFACTS[4]).read_bytes()),"report_sha256":_sha((output/ARTIFACTS[5]).read_bytes()),"decoder_reexecution":False,"scope":"artifact_integrity_and_selection_reconstruction_only"}
def verify_output(output_dir:Path)->dict[str,Any]: return _verify(output_dir,test_only=False)
def _verify_test_output(output_dir:Path)->dict[str,Any]: return _verify(output_dir,test_only=True)
def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--output-dir",type=Path,required=True); a=p.parse_args(); print(_compact(verify_output(a.output_dir)).decode()); return 0
if __name__=="__main__": raise SystemExit(main())
