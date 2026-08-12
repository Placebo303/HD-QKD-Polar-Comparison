"""Read-only verifier for the v4 real qualification package."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from typing import Any
from . import run_ldpc_v4_real_qualification as lane
from . import run_ldpc_v4_synthetic_qualification as syn
from .verify_ldpc_v4_synthetic_qualification import _rows, verify_frame_public_payloads
from ..formal_ir.ldpc_v4 import validate_outcome_v4, validate_selection_binding
from ..formal_ir.codebook_v4 import verify_candidate_manifest
from ..formal_ir.ldpc_v4_channel import verify_adjacent_channel_model
from ..formal_ir.shared import canonical_event
def _json(p:Path)->Any:return json.loads(p.read_bytes())
def verify_output(output_dir:Path,*,_private_test_only:bool=False)->dict[str,Any]:
 if not output_dir.is_dir() or {x.name for x in output_dir.iterdir()}!=set(lane.ARTIFACTS):raise ValueError("nine artifact contract")
 for name in (lane.ARTIFACTS[0],lane.ARTIFACTS[1],lane.ARTIFACTS[4],lane.ARTIFACTS[5],lane.ARTIFACTS[6],lane.ARTIFACTS[7],lane.ARTIFACTS[8]):
  raw=(output_dir/name).read_bytes();
  if raw!=lane._compact(json.loads(raw)):raise ValueError("noncanonical json")
 p=_json(output_dir/lane.ARTIFACTS[0]);l=_json(output_dir/lane.ARTIFACTS[1]);lane._validate(p,l,_private_test_only)
 bind=_json(Path(l["synthetic_binding"]["path"])/"pre_run_plan.json")["development_binding"]
 if _json(output_dir/lane.ARTIFACTS[4])!=bind["codebook"] or _json(output_dir/lane.ARTIFACTS[5])!=bind["selection"] or _json(output_dir/lane.ARTIFACTS[6])!=bind["channel_model"]:raise ValueError("bound method artifacts")
 verify_candidate_manifest(bind["codebook"]); devplan=_json(Path(l["synthetic_binding"]["path"])/"pre_run_plan.json")["development_prerequisite"];dplan=_json(Path(devplan["path"])/"pre_run_plan.json");verify_adjacent_channel_model(bind["channel_model"],dplan["locked_data"]);validate_selection_binding(bind["selection"],bind["channel_model"])
 rows=_rows(output_dir/lane.ARTIFACTS[2]);raw=(output_dir/lane.ARTIFACTS[3]).read_bytes();events=[json.loads(x) for x in raw.splitlines()]
 if b"".join(canonical_event(x) for x in events)!=raw or len(rows)>3*int(p["frame_count_per_stratum"]):raise ValueError("canonical transcript/outcome count")
 if [x["plan_frame_id"] for x in rows]!=p["execution_order"][:len(rows)]:raise ValueError("execution order")
 cursor=0;grouped={s:[] for s in lane.STRATA}
 for i,row in enumerate(rows):
  selected=l["selected_frames"][i];a,b=lane._arrays(l,selected);st=selected["dataset_id"];seed=l["toeplitz"]["roots"][st]["seeds"][i%int(p["frame_count_per_stratum"])]
  if row["stratum"]!=st or row["dataset_id"]!=st or row["frame_id"]!=row["plan_frame_id"] or row["alice_sha256"]!=lane._sha(a.astype("<u2").tobytes()) or row["bob_sha256"]!=lane._sha(b.astype("<u2").tobytes()) or (row["verification_seed_id"] if row["verification_invoked"] else "")!=(seed["seed_id"] if row["verification_invoked"] else ""):raise ValueError("row provenance")
  begin=cursor;key=f"{st}:{row['frame_id']}"
  while cursor<len(events) and events[cursor].get("frame_key")==key:cursor+=1
  ev=events[begin:cursor];o={k:row[k] for k in syn.OUTCOME_FIELDS if k not in {"stratum","plan_frame_id","alice_sha256","bob_sha256","transcript_bytes_len","transcript_bytes_sha256"}};validate_outcome_v4(o,ev);blob=b"".join(canonical_event(x) for x in ev)
  verify_frame_public_payloads(alice_symbols=a,seed_record=seed,selection=bind["selection"],events=ev,outcome=o)
  if row["transcript_bytes_len"]!=len(blob) or row["transcript_bytes_sha256"]!=lane._sha(blob):raise ValueError("transcript provenance")
  grouped[st].append(row)
 if cursor!=len(events):raise ValueError("event grouping")
 run=_json(output_dir/lane.ARTIFACTS[7]);rep=_json(output_dir/lane.ARTIFACTS[8]);index={n:{"sha256":lane._sha((output_dir/n).read_bytes()),"bytes":(output_dir/n).stat().st_size} for n in lane.ARTIFACTS[:7]};base={k:v for k,v in run.items() if k!="manifest_sha256"}
 if set(run)!={"schema","run_id","run_status","stop_reason","plan_sha256","outcome_count","artifact_index","decoder_reexecution","manifest_sha256"} or run.get("manifest_sha256")!=lane._sha(lane._compact(base)) or run.get("schema")!="binary_ldpc_v4_real_run_manifest_v2" or run.get("run_id")!=lane.RUN_ID or run.get("plan_sha256")!=p["plan_sha256"] or run.get("artifact_index")!=index or run.get("outcome_count")!=len(rows) or run.get("decoder_reexecution") is not False:raise ValueError("run manifest")
 floor=int(p["gate"]["verified_success_floor"]);gates={s:syn._gate(grouped[s],int(p["frame_count_per_stratum"]),floor) for s in lane.STRATA};base={k:v for k,v in rep.items() if k!="report_sha256"}
 if set(rep)!={"schema","run_id","run_status","stop_reason","plan_sha256","run_manifest_sha256","promotion_gates","promoted","decoder_reexecution","report_sha256"} or rep.get("report_sha256")!=lane._sha(lane._compact(base)) or rep.get("schema")!="binary_ldpc_v4_real_report_v2" or rep.get("run_id")!=lane.RUN_ID or rep.get("run_status")!=run.get("run_status") or rep.get("stop_reason")!=run.get("stop_reason") or rep.get("plan_sha256")!=p["plan_sha256"] or rep.get("run_manifest_sha256")!=lane._sha((output_dir/lane.ARTIFACTS[7]).read_bytes()) or rep.get("promotion_gates")!=gates or rep.get("promoted") != (run.get("run_status")=="completed" and all(x["promoted"] for x in gates.values())) or rep.get("decoder_reexecution") is not False:raise ValueError("report")
 if run.get("run_status") not in {"completed","failed"} or (run["run_status"]=="completed" and (run["stop_reason"] or len(rows)!=3*int(p["frame_count_per_stratum"]))) or (run["run_status"]=="failed" and (not run["stop_reason"] or rep["promoted"])):raise ValueError("finalization")
 return {"status":"verified","run_status":run["run_status"],"promoted":rep["promoted"],"outcomes":len(rows),"decoder_reexecution":False}
def main()->int:
 a=argparse.ArgumentParser();a.add_argument("--output-dir",type=Path,required=True);x=a.parse_args();print(lane._compact(verify_output(x.output_dir)).decode());return 0
if __name__=="__main__":raise SystemExit(main())
