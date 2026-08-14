"""Read-only verifier for the immutable 10 dB transfer package."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from . import run_ldpc_v4_10db_transfer_qualification_v2 as lane
from . import run_ldpc_v4_synthetic_qualification as syn
from .verify_ldpc_v4_synthetic_qualification import _rows,verify_frame_public_payloads
from ..formal_ir.ldpc_v4 import validate_outcome_v4,validate_selection_binding
from ..formal_ir.codebook_v4 import verify_candidate_manifest
from ..formal_ir.ldpc_v4_channel import verify_adjacent_channel_model
from ..formal_ir.shared import canonical_event
def _json(p):return json.loads(Path(p).read_bytes())
def verify_output(output_dir,*,_private_test_only=False):
 out=Path(output_dir)
 if not out.is_dir() or {x.name for x in out.iterdir()}!=set(lane.ARTIFACTS):raise ValueError("nine artifact contract")
 for n in (lane.ARTIFACTS[0],lane.ARTIFACTS[1],*lane.ARTIFACTS[4:]):
  raw=(out/n).read_bytes()
  if raw!=lane._compact(json.loads(raw)):raise ValueError("noncanonical json")
 p=_json(out/lane.ARTIFACTS[0]);l=_json(out/lane.ARTIFACTS[1]);lane._validate(p,l,_private_test_only)
 bind=_json(Path(p["synthetic"]["path"])/"pre_run_plan.json")["development_binding"]
 if _json(out/lane.ARTIFACTS[4])!=bind["codebook"] or _json(out/lane.ARTIFACTS[5])!=bind["selection"] or _json(out/lane.ARTIFACTS[6])!=bind["channel_model"]:raise ValueError("method binding")
 verify_candidate_manifest(bind["codebook"]);validate_selection_binding(bind["selection"],bind["channel_model"])
 rows=_rows(out/lane.ARTIFACTS[2]);raw=(out/lane.ARTIFACTS[3]).read_bytes();events=[json.loads(x) for x in raw.splitlines()]
 if b"".join(canonical_event(x) for x in events)!=raw or len(rows)>3*p["frame_count_per_stratum"]:raise ValueError("transcript")
 if [x["plan_frame_id"] for x in rows]!=p["execution_order"][:len(rows)]:raise ValueError("order")
 cursor=0;groups={x:[] for x in lane.STRATA}
 with lane._replay_matrix_cache():
  for i,row in enumerate(rows):
   frame=l["selected_frames"][i];a,b=lane.source.arrays_for_frame(l,frame);st=frame["stratum"];begin=cursor;key=f"{st}:{row['plan_frame_id']}"
   while cursor<len(events) and events[cursor].get("frame_key")==key:cursor+=1
   ev=events[begin:cursor];o={k:row[k] for k in syn.OUTCOME_FIELDS if k not in {"stratum","plan_frame_id","alice_sha256","bob_sha256","transcript_bytes_len","transcript_bytes_sha256"}};validate_outcome_v4(o,ev)
   seed=p["roots"][st]["seeds"][sum(x["stratum"]==st for x in l["selected_frames"][:i])]
   verify_frame_public_payloads(alice_symbols=a,seed_record=seed,selection=bind["selection"],events=ev,outcome=o)
   blob=b"".join(canonical_event(x) for x in ev)
   if row["stratum"]!=st or row["alice_sha256"]!=lane._sha(a.astype("<u2").tobytes()) or row["bob_sha256"]!=lane._sha(b.astype("<u2").tobytes()) or (row["verification_seed_id"] if row["verification_invoked"] else "")!=(seed["seed_id"] if row["verification_invoked"] else "") or row["transcript_bytes_len"]!=len(blob) or row["transcript_bytes_sha256"]!=lane._sha(blob):raise ValueError("row provenance")
   groups[st].append(row)
 if cursor!=len(events):raise ValueError("event grouping")
 run=_json(out/lane.ARTIFACTS[7]);rep=_json(out/lane.ARTIFACTS[8]);idx={n:{"sha256":lane._sha((out/n).read_bytes()),"bytes":(out/n).stat().st_size} for n in lane.ARTIFACTS[:7]}
 if set(run)!={"schema","run_id","run_status","stop_reason","plan_sha256","outcome_count","artifact_index","decoder_reexecution","manifest_sha256"} or run.get("manifest_sha256")!=lane._sha(lane._compact({k:v for k,v in run.items() if k!="manifest_sha256"})) or run.get("schema")!="binary_ldpc_v4_10db_transfer_run_manifest_v2" or run.get("run_id")!=lane.RUN_ID or run.get("run_status") not in {"completed","failed"} or run.get("plan_sha256")!=p["plan_sha256"] or run.get("outcome_count")!=len(rows) or run.get("artifact_index")!=idx or run.get("decoder_reexecution") is not False or (run["run_status"]=="completed" and run["stop_reason"]) or (run["run_status"]=="failed" and not run["stop_reason"]):raise ValueError("run manifest")
 gates={s:syn._gate(groups[s],p["frame_count_per_stratum"],p["gate"]["verified_success_floor"]) for s in lane.STRATA}
 if set(rep)!={"schema","run_id","run_status","stop_reason","plan_sha256","run_manifest_sha256","promotion_gates","promoted","decoder_reexecution","source_relocation","report_sha256"} or rep.get("report_sha256")!=lane._sha(lane._compact({k:v for k,v in rep.items() if k!="report_sha256"})) or rep.get("schema")!="binary_ldpc_v4_10db_transfer_report_v2" or rep.get("run_id")!=lane.RUN_ID or rep.get("run_status")!=run["run_status"] or rep.get("stop_reason")!=run["stop_reason"] or rep.get("plan_sha256")!=p["plan_sha256"] or rep.get("run_manifest_sha256")!=lane._sha((out/lane.ARTIFACTS[7]).read_bytes()) or rep.get("promotion_gates")!=gates or rep.get("promoted") != (run.get("run_status")=="completed" and all(x["promoted"] for x in gates.values())) or rep.get("decoder_reexecution") is not False or rep.get("source_relocation") is not True:raise ValueError("report")
 if run["run_status"]=="completed" and (len(rows)!=3*p["frame_count_per_stratum"] or any(len(groups[s])!=p["frame_count_per_stratum"] or any(not r["denominator_included"] for r in groups[s]) for s in lane.STRATA)):raise ValueError("completed accounting")
 if run["run_status"]=="failed" and rep["promoted"]:raise ValueError("failed promotion")
 return {"status":"verified","run_status":run.get("run_status"),"promoted":rep.get("promoted"),"outcomes":len(rows),"decoder_reexecution":False,"source_relocation":True}
def main():
 p=argparse.ArgumentParser();p.add_argument("--output-dir",type=Path,required=True);a=p.parse_args();print(lane._compact(verify_output(a.output_dir)).decode());return 0
if __name__=="__main__":raise SystemExit(main())
