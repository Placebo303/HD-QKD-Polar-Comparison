"""Read-only verifier for the versioned backend-correction development package."""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
from typing import Any
from . import run_ldpc_v4_development_v2 as lane
from . import run_ldpc_v4_development as v1_test_helpers
from ..formal_ir.codebook_v4 import candidate_entry,candidate_manifest,verify_candidate_manifest
from ..formal_ir.ldpc_v4_channel import build_adjacent_channel_model,verify_adjacent_channel_model
from ..formal_ir.ldpc_v4_development_v2 import STRATA,aggregate_frame_development,generate_sacrificed_development,select_candidates

def _json(p:Path)->dict[str,Any]:
 raw=p.read_bytes();v=json.loads(raw)
 if not isinstance(v,dict) or lane._compact(v)!=raw:raise ValueError("noncanonical json")
 return v
def _rows(p:Path)->list[dict[str,Any]]:
 raw=p.read_bytes()
 if not raw.endswith(b"\n") or b"\r" in raw:raise ValueError("csv canonical bytes")
 out=[]
 for r in csv.DictReader(raw.decode("utf-8").splitlines()):
  if list(r)!=list(lane.FIELDS) or any(v is None for v in r.values()):raise ValueError("csv schema")
  try:
   x={"role":r["role"],"stratum_id":r["stratum_id"],"plane_id":int(r["plane_id"]),"candidate_id":int(r["candidate_id"]),"channel_model_sha256":r["channel_model_sha256"],"policy_sha256":r["policy_sha256"],"matrix_sha256":r["matrix_sha256"],"candidate_valid":r["candidate_valid"]=="true","backend_identity":r["backend_identity"],"frame_id":r["frame_id"],"attempted":r["attempted"]=="true","status":r["status"],"exact_match":r["exact_match"]=="true","syndrome_bits_disclosed":int(r["syndrome_bits_disclosed"]),"runtime_s":float(r["runtime_s"]),"source_sha256":r["source_sha256"]}
   if r["candidate_valid"] not in ("true","false") or r["attempted"] not in ("true","false") or r["exact_match"] not in ("true","false"):raise ValueError
  except Exception as e:raise ValueError("csv encoding") from e
  if not math.isfinite(x["runtime_s"]) or x["runtime_s"]<0:raise ValueError("runtime")
  if lane._csv([x]).split(b"\n",1)[1].split(b"\n",1)[0] != raw.splitlines()[len(out)+1]:raise ValueError("csv noncanonical row")
  out.append(x)
 return out
def _hashed(doc:dict[str,Any],key:str)->bool:
 base=dict(doc);got=base.pop(key,None);return isinstance(got,str) and got==lane._sha(lane._compact(base))
def verify_output(output_dir:Path,*,_private_test_only:bool=False)->dict[str,Any]:
 if not output_dir.is_dir() or {x.name for x in output_dir.iterdir()}!=set(lane.ARTIFACTS):raise ValueError("seven artifact contract")
 plan=_json(output_dir/lane.ARTIFACTS[0]);lane._validate_plan(plan,test_only=_private_test_only)
 manifest=_json(output_dir/lane.ARTIFACTS[1]);verify_candidate_manifest(manifest)
 if manifest!=candidate_manifest() or manifest["manifest_sha256"]!=plan["candidate_manifest_sha256"]:raise ValueError("codebook DAG")
 model=_json(output_dir/lane.ARTIFACTS[2]);verify_adjacent_channel_model(model,plan["locked_data"])
 if model["model_sha256"]!=plan["channel_model_sha256"]:raise ValueError("model DAG")
 rows=_rows(output_dir/lane.ARTIFACTS[3]);selection=_json(output_dir/lane.ARTIFACTS[4]);run=_json(output_dir/lane.ARTIFACTS[5]);report=_json(output_dir/lane.ARTIFACTS[6])
 if len(rows)>plan["expected_plane_outcomes"]:raise ValueError("too many outcomes")
 expected=[(s,p,c,f"v4dev_{s}_f{i:03d}") for s,p,c in plan["execution_order"] for i in range(plan["frame_count_per_stratum"])]
 if [(r["stratum_id"],r["plane_id"],r["candidate_id"],r["frame_id"]) for r in rows]!=expected[:len(rows)]:raise ValueError("execution order")
 sources={s:generate_sacrificed_development(model,s) for s in STRATA}
 for r in rows:
  e=candidate_entry(r["plane_id"],r["candidate_id"])
  nonattempt=r["status"] in {"development_backend_unavailable","development_backend_mismatch"}
  if r["stratum_id"] not in plan["strata"] or r["plane_id"] not in plan["plane_ids"] or r["candidate_id"] not in plan["candidate_ids"] or r["status"] not in {"development_exact_success","development_decode_failed","development_syndrome_inconsistent","development_decoder_error","development_backend_unavailable","development_timeout","development_backend_mismatch","development_malformed_output"} or r["role"]!=lane.ROLE or r["channel_model_sha256"]!=model["model_sha256"] or r["policy_sha256"]!=plan["development_policy"]["policy_sha256"] or r["matrix_sha256"]!=e["canonical_bytes_sha256"] or r["candidate_valid"]!=e["valid"] or r["source_sha256"]!=sources[r["stratum_id"]]["source_sha256"] or r["exact_match"]!=(r["status"]=="development_exact_success") or r["backend_identity"]!=("test_injected" if _private_test_only else "ldpc==2.4.1") or r["attempted"]==nonattempt or r["syndrome_bits_disclosed"]!=(0 if nonattempt else e["shape"][0]):raise ValueError("outcome binding")
 complete=len(rows)==plan["expected_plane_outcomes"];aggregate=None
 if complete:
  if _private_test_only:rebuilt,aggregate=v1_test_helpers._test_selection_aggregation(rows,model)
  else:rebuilt=select_candidates(rows,model,codebook_manifest=manifest);aggregate=aggregate_frame_development(rows,rebuilt,model)
  if selection!=rebuilt:raise ValueError("selection reconstruction")
 else:
  if selection!={"schema":"binary_ldpc_v4_selection_partial_v2","selection_status":"incomplete","observed_plane_outcomes":len(rows)}:raise ValueError("partial selection")
 index={n:{"sha256":lane._sha((output_dir/n).read_bytes()),"bytes":(output_dir/n).stat().st_size} for n in lane.ARTIFACTS[:5]}
 if set(run)!={"schema","run_id","run_status","stop_reason","plan_sha256","observed_plane_outcomes","expected_plane_outcomes","artifact_index","decoder_reexecution","manifest_sha256"} or not _hashed(run,"manifest_sha256") or run.get("schema")!="binary_ldpc_v4_development_run_manifest_v2" or run.get("run_id")!=lane.RUN_ID or run.get("artifact_index")!=index or run.get("plan_sha256")!=plan["plan_sha256"] or run.get("observed_plane_outcomes")!=len(rows) or run.get("expected_plane_outcomes")!=plan["expected_plane_outcomes"] or run.get("decoder_reexecution") is not False or run.get("run_status") not in {"completed","failed"}:raise ValueError("run manifest")
 if (run["run_status"]=="completed") != (complete and run.get("stop_reason")=="completed"):raise ValueError("completion")
 if set(report)!={"schema","run_id","run_status","stop_reason","ready_for_synthetic_prepare","readiness_gate","selection_sha256","plan_sha256","run_manifest_sha256","decoder_reexecution","report_sha256"} or not _hashed(report,"report_sha256") or report.get("schema")!="binary_ldpc_v4_development_report_v2" or report.get("run_id")!=lane.RUN_ID or report.get("run_status")!=run["run_status"] or report.get("stop_reason")!=run["stop_reason"] or report.get("plan_sha256")!=plan["plan_sha256"] or report.get("run_manifest_sha256")!=lane._sha((output_dir/lane.ARTIFACTS[5]).read_bytes()) or report.get("decoder_reexecution") is not False:raise ValueError("report DAG")
 ready=False if aggregate is None else bool(aggregate["ready_for_synthetic_prepare"])
 if report.get("selection_sha256")!=selection.get("selection_sha256") or report.get("ready_for_synthetic_prepare")!=ready or report.get("readiness_gate")!=(None if aggregate is None else lane._gate(aggregate,plan["readiness_floor"])):raise ValueError("readiness reconstruction")
 return {"status":"verified","run_status":run["run_status"],"ready_for_synthetic_prepare":ready,"decoder_reexecution":False,"scope":"predecessor_source_model_codebook_development_selection_accounting"}
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--output-dir",type=Path,required=True);a=p.parse_args();print(lane._compact(verify_output(a.output_dir)).decode());return 0
if __name__=="__main__":raise SystemExit(main())
