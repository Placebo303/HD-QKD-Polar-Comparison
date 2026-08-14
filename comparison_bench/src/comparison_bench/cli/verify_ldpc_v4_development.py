"""Read-only verifier for the seven-artifact LDPC v4 development package."""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
from typing import Any
from . import run_ldpc_v4_development as lane
from ..formal_ir.codebook_v4 import candidate_entry,candidate_manifest,verify_candidate_manifest
from ..formal_ir.ldpc_v4_channel import build_adjacent_channel_model,verify_adjacent_channel_model
from ..formal_ir.ldpc_v4_development import FRAME_COUNT,STRATA,_STATUSES,aggregate_frame_development,generate_sacrificed_development,select_candidates

def _json(p:Path)->dict[str,Any]:
 raw=p.read_bytes(); value=json.loads(raw)
 if not isinstance(value,dict) or lane._compact(value)!=raw:raise ValueError("noncanonical json")
 return value
def _rows(p:Path)->list[dict[str,Any]]:
 raw=p.read_bytes()
 if not raw.endswith(b"\n") or b"\r" in raw:raise ValueError("csv canonical bytes")
 result=[]
 for r in csv.DictReader(raw.decode("utf-8").splitlines()):
  if list(r)!=list(lane.FIELDS) or any(v is None for v in r.values()):raise ValueError("csv schema")
  try:
   if r["candidate_valid"] not in ("true","false") or r["attempted"] not in ("true","false") or r["exact_match"] not in ("true","false"):raise ValueError("boolean encoding")
   row={"role":r["role"],"stratum_id":r["stratum_id"],"plane_id":int(r["plane_id"]),"candidate_id":int(r["candidate_id"]),"channel_model_sha256":r["channel_model_sha256"],"policy_sha256":r["policy_sha256"],"matrix_sha256":r["matrix_sha256"],"candidate_valid":r["candidate_valid"]=="true","backend_identity":r["backend_identity"],"frame_id":r["frame_id"],"attempted":r["attempted"]=="true","status":r["status"],"exact_match":r["exact_match"]=="true","syndrome_bits_disclosed":int(r["syndrome_bits_disclosed"]),"runtime_s":float(r["runtime_s"]),"source_sha256":r["source_sha256"]}
  except Exception as e:raise ValueError("csv encoding") from e
  if lane._csv([row]).split(b"\n",1)[1].split(b"\n",1)[0] != raw.splitlines()[len(result)+1]:raise ValueError("csv noncanonical row")
  result.append(row)
 return result
def verify_output(output_dir:Path,*,_private_test_only:bool=False)->dict[str,Any]:
 if not output_dir.is_dir() or {x.name for x in output_dir.iterdir()}!=set(lane.ARTIFACTS):raise ValueError("seven artifact contract")
 plan=_json(output_dir/lane.ARTIFACTS[0]); lane._validate_plan(plan,test_only=_private_test_only)
 manifest=_json(output_dir/lane.ARTIFACTS[1]);verify_candidate_manifest(manifest)
 if manifest!=candidate_manifest() or manifest["manifest_sha256"]!=plan["candidate_manifest_sha256"]:raise ValueError("codebook DAG")
 model=_json(output_dir/lane.ARTIFACTS[2]);verify_adjacent_channel_model(model,plan["locked_data"])
 if model["model_sha256"]!=plan["channel_model_sha256"]:raise ValueError("model DAG")
 rows=_rows(output_dir/lane.ARTIFACTS[3]); selection=_json(output_dir/lane.ARTIFACTS[4]); run=_json(output_dir/lane.ARTIFACTS[5]); report=_json(output_dir/lane.ARTIFACTS[6])
 if len(rows)>plan["expected_plane_outcomes"]:raise ValueError("too many outcomes")
 expected=[(s,p,c,f"v4dev_{s}_f{i:03d}") for s,p,c in plan["execution_order"] for i in range(plan["frame_count_per_stratum"])]
 if [(r["stratum_id"],r["plane_id"],r["candidate_id"],r["frame_id"]) for r in rows]!=expected[:len(rows)]:raise ValueError("execution order")
 sources={s:generate_sacrificed_development(model,s) for s in STRATA}
 for r in rows:
  if r["role"]!=lane.ROLE or r["stratum_id"] not in plan["strata"] or r["plane_id"] not in plan["plane_ids"] or r["candidate_id"] not in plan["candidate_ids"] or r["channel_model_sha256"]!=model["model_sha256"] or r["policy_sha256"]!=plan["development_policy"]["policy_sha256"] or r["status"] not in _STATUSES or not math.isfinite(r["runtime_s"]) or r["runtime_s"]<0 or r["backend_identity"] != ("test_injected" if _private_test_only else "ldpc==2.4.1"):raise ValueError("outcome binding")
  e=candidate_entry(r["plane_id"],r["candidate_id"])
  if r["matrix_sha256"]!=e["canonical_bytes_sha256"] or r["candidate_valid"]!=e["valid"] or r["source_sha256"]!=sources[r["stratum_id"]]["source_sha256"] or r["exact_match"] != (r["status"]=="development_exact_success"):raise ValueError("outcome reconstruction")
  nonattempt=r["status"] in {"development_backend_unavailable","development_backend_mismatch"}
  if r["attempted"]==nonattempt or r["syndrome_bits_disclosed"] != (0 if nonattempt else e["shape"][0]):raise ValueError("attempt accounting")
 complete=len(rows)==plan["expected_plane_outcomes"]
 aggregation=None
 if complete:
  rebuilt,aggregation=(lane._test_selection_aggregation(rows,model) if _private_test_only else (select_candidates(rows,model,codebook_manifest=manifest),None))
  if selection!=rebuilt:raise ValueError("selection reconstruction")
  if not _private_test_only: aggregation=aggregate_frame_development(rows,selection,model)
 else:
  if selection!={"schema":"binary_ldpc_v4_selection_partial_v1","selection_status":"incomplete","observed_plane_outcomes":len(rows)}:raise ValueError("partial selection")
 index={n:{"sha256":lane._sha((output_dir/n).read_bytes()),"bytes":(output_dir/n).stat().st_size} for n in lane.ARTIFACTS[:5]}
 run_keys={"schema","run_id","run_status","stop_reason","plan_sha256","observed_plane_outcomes","expected_plane_outcomes","artifact_index","decoder_reexecution","manifest_sha256"}
 base=dict(run);digest=base.pop("manifest_sha256",None)
 if set(run)!=run_keys or digest!=lane._sha(lane._compact(base)) or run.get("schema")!="binary_ldpc_v4_development_run_manifest_v1" or run.get("run_id")!=lane.RUN_ID or run.get("artifact_index")!=index or run.get("plan_sha256")!=plan["plan_sha256"] or run.get("observed_plane_outcomes")!=len(rows) or run.get("expected_plane_outcomes")!=plan["expected_plane_outcomes"] or run.get("decoder_reexecution") is not False or run.get("run_status") not in {"completed","failed"} or (run.get("run_status")=="completed") != (len(rows)==plan["expected_plane_outcomes"] and run.get("stop_reason")=="completed") or (run.get("run_status")=="failed" and run.get("stop_reason")=="completed"):raise ValueError("run manifest")
 rb=dict(report);rd=rb.pop("report_sha256",None)
 report_keys={"schema","run_id","run_status","stop_reason","ready_for_synthetic_prepare","readiness_gate","selection_sha256","plan_sha256","run_manifest_sha256","decoder_reexecution","report_sha256"}
 if set(report)!=report_keys or rd!=lane._sha(lane._compact(rb)) or report.get("schema")!="binary_ldpc_v4_development_report_v1" or report.get("run_id")!=lane.RUN_ID or report.get("run_status")!=run["run_status"] or report.get("stop_reason")!=run["stop_reason"] or report.get("plan_sha256")!=plan["plan_sha256"] or report.get("decoder_reexecution") is not False or report.get("run_manifest_sha256")!=lane._sha((output_dir/lane.ARTIFACTS[5]).read_bytes()):raise ValueError("report DAG")
 ready=False if aggregation is None else bool(aggregation["ready_for_synthetic_prepare"])
 if report.get("selection_sha256")!=selection.get("selection_sha256") or report.get("ready_for_synthetic_prepare")!=ready or report.get("readiness_gate") != (None if aggregation is None else lane._gate(aggregation,plan["readiness_floor"])):raise ValueError("readiness reconstruction")
 return {"status":"verified","run_status":run["run_status"],"ready_for_synthetic_prepare":ready,"decoder_reexecution":False,"scope":"source_model_codebook_development_selection_accounting"}
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--output-dir",type=Path,required=True);a=p.parse_args();print(lane._compact(verify_output(a.output_dir)).decode());return 0
if __name__=="__main__":raise SystemExit(main())
