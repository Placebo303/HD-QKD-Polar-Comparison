"""Read-only reconstruction verifier for the v4 synthetic package."""
from __future__ import annotations
import argparse, csv, json, math
from pathlib import Path
from typing import Any
import numpy as np

from . import run_ldpc_v4_synthetic_qualification as lane
from . import verify_ldpc_v4_development_v2 as development_verify
from ..formal_ir.codebook_v4 import candidate_manifest, matrix_for, verify_candidate_manifest
from ..formal_ir.ldpc_v4 import validate_outcome_v4, validate_selection_binding
from ..formal_ir.ldpc_v4_channel import build_adjacent_channel_model, verify_adjacent_channel_model
from ..formal_ir.shared import canonical_event, locked_seed_bits, toeplitz_tag
from ..utils.bitops import symbols_to_bits

_BOOL={"attempted","denominator_included","verification_invoked"}
_INT={"n_pairs","dimension","frame_len_symbols","verification_tag_bits","key_dependent_disclosure_bits_total","public_control_bits_total","transcript_first_event_id","transcript_last_event_id","decoder_call_count","verification_check_count","ldpc_syndrome_bits","verification_tag_bits_component","transcript_bytes_len"}
_FLOAT={"raw_ser","epsilon_ec","runtime_s"}

def verify_frame_public_payloads(*, alice_symbols: Any, seed_record: dict[str,Any], selection: dict[str,Any], events: list[dict[str,Any]], outcome: dict[str,Any]) -> None:
    """Rebuild public LDPC/tag payloads without decoder reexecution.

    This intentionally validates only Alice-derived disclosure and the public
    tag.  It never reconstructs Bob corrections or invokes a decoder.
    """
    selected=validate_selection_binding(selection,{"model_sha256":outcome["channel_model_sha256"]})
    alice=np.asarray(alice_symbols,dtype=np.uint16)
    if alice.shape!=(256,): raise ValueError("alice payload source")
    bits=symbols_to_bits(alice.astype(np.int64),1024,"gray").astype(np.uint8)
    complete=outcome["status"] in {"verified_success","verify_failed"}
    event_types=[event["event_type"] for event in events]
    if complete:
        expected_types=["SYNDROME"] * 10 + ["VERIFICATION_SEED","VERIFICATION_TAG","FRAME_TAG_CHECK"]
        if event_types != expected_types: raise ValueError("complete public event order")
    else:
        expected_types=(["SYNDROME"] * (len(event_types)-1) + ["ABORT"]) if event_types and event_types[-1]=="ABORT" else ["SYNDROME"] * len(event_types)
        if event_types != expected_types: raise ValueError("early failure event order")
    syndrome=[event for event in events if event["event_type"]=="SYNDROME"]
    if [event["plane_id"] for event in syndrome] != list(range(len(syndrome))) or len(syndrome)>10: raise ValueError("syndrome public order")
    for plane,event in enumerate(syndrome):
        expected=np.packbits((matrix_for(plane,selected[plane]) @ bits[:,plane] % 2).astype(np.uint8),bitorder="big").tobytes().hex()
        if event["payload"] != {"syndrome":expected}: raise ValueError("syndrome public payload")
    if complete:
        seed=locked_seed_bits(seed_record,2623)
        expected_tag=toeplitz_tag(bits.reshape(-1),seed).hex()
        tail=events[10:]
        if tail[0]["payload"]!={"seed_id":seed_record["seed_id"],"seed_bit_length":2623}: raise ValueError("verification seed payload")
        if tail[1]["payload"]!={"tag":expected_tag}: raise ValueError("verification tag payload")
        expected_check="match" if outcome["status"]=="verified_success" else "mismatch"
        if tail[2]["payload"]!={"value":expected_check}: raise ValueError("frame tag check payload")
    else:
        if any(event["event_type"] in {"VERIFICATION_SEED","VERIFICATION_TAG","FRAME_TAG_CHECK"} for event in events): raise ValueError("early failure forged verification")

def _json(p: Path) -> dict[str,Any]:
    raw=p.read_bytes(); x=json.loads(raw)
    if not isinstance(x,dict) or lane._compact(x)!=raw: raise ValueError("noncanonical json")
    return x
def _rows(p:Path)->list[dict[str,Any]]:
    raw=p.read_bytes()
    if not raw.endswith(b"\n") or b"\r" in raw: raise ValueError("csv canonical")
    result=[]
    for row in csv.DictReader(raw.decode("utf-8").splitlines()):
        if list(row)!=list(lane.OUTCOME_FIELDS) or any(v is None for v in row.values()): raise ValueError("csv schema")
        x={}
        try:
            for k,v in row.items():
                if k in _BOOL:
                    if v not in ("true","false"): raise ValueError("bool")
                    x[k]=v=="true"
                elif k in _INT:
                    x[k]=None if k in {"transcript_first_event_id","transcript_last_event_id"} and v=="" else int(v)
                elif k in _FLOAT:
                    x[k]=float(v)
                    if not math.isfinite(x[k]) and k!="raw_ser": raise ValueError("float")
                else: x[k]=v
            # Strict formatting, not merely parseability.
            if lane._csv([x]).split(b"\n",1)[1].split(b"\n",1)[0] != raw.splitlines()[len(result)+1]: raise ValueError("csv representation")
        except Exception as exc: raise ValueError("csv encoding") from exc
        result.append(x)
    return result

def _verify_plan(plan:dict[str,Any], private:bool)->dict[str,Any]:
    checked=lane._validate_plan(plan,private=private)
    if not private:
        required={"schema","run_id","method_id","dimension","mapping","frame_len_symbols","frame_count_per_stratum","strata","caps","gate","development_prerequisite","development_binding","v3_seed_binding","development_root_binding","generator","source_sha256","backend_requirement","failure_finalizer","_test_only","execution_order","plan_sha256"}
        if set(plan)!=required or plan["gate"]!={"denominator":128,"verified_success_floor":lane.qualification_floor(128),"forbidden_statuses":sorted(lane.FORBIDDEN)}: raise ValueError("production plan schema")
    return checked

def verify_output(output_dir:Path, *, _private_test_only:bool=False)->dict[str,Any]:
    if not output_dir.is_dir() or {p.name for p in output_dir.iterdir()} != set(lane.ARTIFACTS): raise ValueError("eight artifact contract")
    plan=_verify_plan(_json(output_dir/lane.ARTIFACTS[0]),_private_test_only)
    # Reconstruct prerequisite and all bound public method identities.
    dev_path=Path(plan["development_prerequisite"]["path"]); development_verify.verify_output(dev_path,_private_test_only=_private_test_only)
    dev_plan=json.loads((dev_path/"pre_run_plan.json").read_bytes())
    bound=plan["development_binding"]
    verify_candidate_manifest(bound["codebook"]); verify_adjacent_channel_model(bound["channel_model"], dev_plan["locked_data"]); validate_selection_binding(bound["selection"], bound["channel_model"])
    for file,key in ((lane.ARTIFACTS[3],"codebook"),(lane.ARTIFACTS[4],"selection"),(lane.ARTIFACTS[5],"channel_model")):
        if _json(output_dir/file) != bound[key]: raise ValueError("bound artifact")
    rows=_rows(output_dir/lane.ARTIFACTS[1]); raw_events=(output_dir/lane.ARTIFACTS[2]).read_bytes()
    events=[json.loads(x) for x in raw_events.splitlines()]
    if b"".join(canonical_event(e) for e in events)!=raw_events: raise ValueError("transcript canonical")
    count=int(plan["frame_count_per_stratum"])
    if len(rows)>2*count or [r["plan_frame_id"] for r in rows] != plan["execution_order"][:len(rows)]: raise ValueError("execution order")
    generated={s:lane._generate(plan,s) for s in lane.STRATA}; cursor=0; grouped={s:[] for s in lane.STRATA}
    for row in rows:
        s,fid=row["plan_frame_id"].split(":f"); i=int(fid)
        if s not in grouped or row["stratum"]!=s or row["dataset_id"]!=f"synthetic_{s}" or row["frame_id"]!=row["plan_frame_id"]: raise ValueError("frame identity")
        alice,bob,seeds=generated[s]
        if row["alice_sha256"]!=lane._sha(alice[i].astype("<u2").tobytes()) or row["bob_sha256"]!=lane._sha(bob[i].astype("<u2").tobytes()): raise ValueError("frame provenance")
        expected_seed=seeds[i]["seed_id"] if row["verification_invoked"] else ""
        if row["verification_seed_id"]!=expected_seed: raise ValueError("seed binding")
        begin=cursor; key=f"{row['dataset_id']}:{row['frame_id']}"
        while cursor<len(events) and events[cursor].get("frame_key")==key: cursor+=1
        group=events[begin:cursor]; outcome={k:row[k] for k in lane.OUTCOME_FIELDS if k not in {"stratum","plan_frame_id","alice_sha256","bob_sha256","transcript_bytes_len","transcript_bytes_sha256"}}
        validate_outcome_v4(outcome,group)
        verify_frame_public_payloads(alice_symbols=alice[i],seed_record=seeds[i],selection=bound["selection"],events=group,outcome=outcome)
        blob=b"".join(canonical_event(e) for e in group)
        if row["transcript_bytes_len"]!=len(blob) or row["transcript_bytes_sha256"]!=lane._sha(blob): raise ValueError("transcript provenance")
        grouped[s].append(row)
    if cursor!=len(events): raise ValueError("transcript grouping")
    run=_json(output_dir/lane.ARTIFACTS[6]); report=_json(output_dir/lane.ARTIFACTS[7])
    expected_index={n:{"sha256":lane._sha((output_dir/n).read_bytes()),"bytes":(output_dir/n).stat().st_size} for n in lane.ARTIFACTS[:6]}
    run_base={k:v for k,v in run.items() if k!="manifest_sha256"}
    if set(run)!={"schema","run_id","run_status","stop_reason","plan_sha256","outcome_count","artifact_index","decoder_reexecution","manifest_sha256"} or run.get("manifest_sha256")!=lane._sha(lane._compact(run_base)) or run["schema"]!="binary_ldpc_v4_synthetic_run_manifest_v2" or run["run_id"]!=lane.RUN_ID or run["plan_sha256"]!=plan["plan_sha256"] or run["artifact_index"]!=expected_index or run["outcome_count"]!=len(rows) or run["decoder_reexecution"] is not False: raise ValueError("run manifest")
    floor=count if _private_test_only else lane.qualification_floor(count)
    if int(plan["gate"]["verified_success_floor"])!=floor: raise ValueError("recomputed qualification floor")
    gates={s:lane._gate(grouped[s],count,floor) for s in lane.STRATA}
    report_base={k:v for k,v in report.items() if k!="report_sha256"}
    if set(report)!={"schema","run_id","run_status","stop_reason","plan_sha256","run_manifest_sha256","promotion_gates","promoted","decoder_reexecution","report_sha256"} or report.get("report_sha256")!=lane._sha(lane._compact(report_base)) or report["schema"]!="binary_ldpc_v4_synthetic_report_v2" or report["run_id"]!=lane.RUN_ID or report["run_status"]!=run["run_status"] or report["stop_reason"]!=run["stop_reason"] or report["plan_sha256"]!=plan["plan_sha256"] or report["run_manifest_sha256"]!=lane._sha((output_dir/lane.ARTIFACTS[6]).read_bytes()) or report["promotion_gates"]!=gates or report["promoted"] != (run["run_status"]=="completed" and all(g["promoted"] for g in gates.values())) or report["decoder_reexecution"] is not False: raise ValueError("report")
    if run["run_status"] not in {"completed","failed"}: raise ValueError("run finalization")
    if run["run_status"]=="completed" and (run["stop_reason"] or len(rows)!=2*count): raise ValueError("completed finalization")
    if run["run_status"]=="failed" and (not run["stop_reason"] or report["promoted"]): raise ValueError("failed finalization")
    return {"status":"verified","run_status":run["run_status"],"promoted":report["promoted"],"outcomes":len(rows),"decoder_reexecution":False}

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--output-dir",type=Path,required=True);a=p.parse_args();print(lane._compact(verify_output(a.output_dir)).decode());return 0
if __name__=="__main__":raise SystemExit(main())
