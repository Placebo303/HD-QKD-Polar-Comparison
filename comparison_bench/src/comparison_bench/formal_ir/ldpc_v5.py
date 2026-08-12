"""Formal v5 C0/C1/C2 frame state machine (no package I/O)."""
from __future__ import annotations
import csv
import importlib.metadata
import hashlib,json,time
from io import StringIO
from functools import lru_cache
from typing import Any,Mapping,Callable
import numpy as np
from ..utils.bitops import symbols_to_bits,frame_symbol_error_rate
from . import codebook_v4
from .codebook_v5_h2 import generate_h2,canonical_h2_bytes
from .ldpc_v4_channel import plane_error_channel
from .shared import locked_seed_bits,toeplitz_tag,sha256_bytes
METHOD="ldpc_formal_v5"; N=256; Q=1024; PLANES=tuple(range(10)); _NON={"invalid_input","unsupported_domain","backend_unavailable"}

def v5_plane_error_channel(bob_symbols: Any, plane_id: int, stratum: str, channel_model: Mapping[str, Any]) -> np.ndarray:
    """Frozen real-transfer adapter; never infer a source stratum."""
    if stratum not in {"bw120", "bw180", "bw200"}:
        raise ValueError("v5 source stratum")
    return plane_error_channel(bob_symbols, plane_id, "adjacent_nominal", channel_model)
def _c(x:Any)->bytes:return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")
def _s(x:bytes)->str:return hashlib.sha256(x).hexdigest()
def _hash_obj(x:Any)->str:return _s(_c(x))
def _decoder_binding(strong:bool)->dict[str,Any]:
    base={"max_iter":100 if strong else 50,"bp_method":"product_sum","schedule":"serial","omp_thread_count":1,"serial_schedule_order":list(range(N)),"osd_method":"OSD_CS" if strong else "OSD_0","osd_order":2 if strong else 0,"error_channel_source":"v4_bob_conditioned_per_position"}
    return {**base,"decoder_sha256":_hash_obj(base)}
def build_v5_policy_manifest(*,selected_candidates:list[int],selection_sha256:str,codebook_manifest_sha256:str,channel_model_sha256:str,h2_manifest:Mapping[str,Any])->dict[str,Any]:
    if len(selected_candidates)!=10:raise ValueError("v5 policy selection")
    h1hash=[_s(codebook_v4.canonical_matrix_bytes(codebook_v4.matrix_for(p,c),plane_id=p)) for p,c in enumerate(selected_candidates)]
    h2hash=[x["canonical_bytes_sha256"] for x in h2_manifest.get("candidates",[])]
    if len(h2hash)!=10:raise ValueError("v5 policy H2")
    policies=[]
    for cid,strong,fallback,active in (("V5-C0",False,False,False),("V5-C1",True,False,False),("V5-C2",False,True,True)):
        r0=_decoder_binding(strong); fb=_decoder_binding(True) if fallback else None; pre=[]
        for p in PLANES:pre.append({"candidate_id":cid,"pass_id":0,"plane_id":p,"matrix_kind":"H1","h_rows":codebook_v4.row_count(p),"h_cols":N,"matrix_sha256":h1hash[p],"decoder_sha256":r0["decoder_sha256"]})
        if fallback:
            for p in PLANES:
                h1=codebook_v4.matrix_for(p,selected_candidates[p]);h2,_=generate_h2(p,h1);h=np.vstack((h1,h2));raw=b"HGF2V5ST"+np.asarray([p,h.shape[0],N],dtype="<u4").tobytes()+h.astype(np.uint8).tobytes(order="C")
                pre.append({"candidate_id":cid,"pass_id":1,"plane_id":p,"matrix_kind":"H1_H2","h_rows":int(h.shape[0]),"h_cols":N,"matrix_sha256":_s(raw),"decoder_sha256":fb["decoder_sha256"]})
        base={"schema":"binary_ldpc_v5_policy_v1","candidate_id":cid,"method_id":METHOD,"h1_binding":{"selection_schema":"binary_ldpc_v4_selection_v1","selection_sha256":selection_sha256,"codebook_manifest_sha256":codebook_manifest_sha256,"channel_model_sha256":channel_model_sha256,"plane_matrix_sha256":h1hash},"h2_binding":{"active":active,"manifest_schema":"binary_ldpc_v5_h2_manifest_v1","manifest_sha256":h2_manifest["manifest_sha256"],"h2_row_counts":[16,16,16,24,24,32,48,80,88,48],"plane_matrix_sha256":h2hash},"round0_decoder":r0,"fallback_decoder":fb,"verification":{"locked_seed_count":2,"round0_tag_bits":64,"fallback_tag_bits":64 if fallback else 0,"max_checks":2 if fallback else 1,"epsilon_round0":"1/18446744073709551616","epsilon_fallback":"1/9223372036854775808" if fallback else None},"caps":{"wall_s":10.0,"decoder_calls":20 if fallback else 10,"events":32},"preflight":pre}
        policies.append({**base,"policy_sha256":_hash_obj(base)})
    base={"schema":"binary_ldpc_v5_policy_manifest_v1","method_id":METHOD,"h1_selection_sha256":selection_sha256,"h2_manifest_sha256":h2_manifest["manifest_sha256"],"candidates":policies}
    return {**base,"manifest_sha256":_hash_obj(base)}
def verify_v5_policy_manifest(manifest:Mapping[str,Any],**kwargs:Any)->None:
    supplied=dict(manifest);digest=supplied.pop("manifest_sha256",None)
    if not isinstance(digest,str) or _hash_obj(supplied)!=digest:raise ValueError("v5 policy manifest hash")
    if dict(manifest)!=build_v5_policy_manifest(**kwargs):raise ValueError("v5 policy manifest reconstruction")
def _syn(h,x):return (np.asarray(h,dtype=np.uint8)@np.asarray(x,dtype=np.uint8)%2).astype(np.uint8)
def canonical_event_v5(event:Mapping[str,Any])->bytes:
    required={"event_id","frame_key","method","event_type","direction","parent_event_id","pass_id","plane_id","key_dependent_bits","public_control_bits","payload"}
    if set(event)!=required or event["method"]!=METHOD or event["direction"] not in {"alice_to_bob","bob_to_alice","bob_local","control"}:raise ValueError("v5 event")
    return _c(dict(event))+b"\n"
def _events_hash(events):return _s(b"".join(canonical_event_v5(x) for x in events))
def _status_flags(s):
    if s not in {"invalid_input","unsupported_domain","backend_unavailable","aborted_resource_limit","decoder_error","syndrome_inconsistent","verify_failed","verified_success"}:raise ValueError("v5 status")
    return s not in _NON
OUTCOME_FIELDS=("dataset_id","frame_id","n_pairs","pair_idx_sequence_sha256","method","candidate_id","attempted","denominator_included","status","failure_reason","dimension","frame_len_symbols","raw_ser","fallback_invoked","rounds_attempted","verification_invoked","verification_seed_id_round0","verification_seed_id_round1","verification_tag_bits","epsilon_ec","key_dependent_disclosure_bits_total","public_control_bits_total","transcript_first_event_id","transcript_last_event_id","transcript_sha256","runtime_s","decoder_call_count","verification_check_count","ldpc_syndrome_bits","h1_syndrome_bits","h2_syndrome_bits","verification_tag_bits_component","feedback_control_bits","selection_sha256","channel_model_sha256","h1_codebook_manifest_sha256","h2_manifest_sha256","policy_sha256","mapping","leakage_comparison_policy","backend_name","backend_version")
CSV_PREFIX_FIELDS=("role","stratum","plan_frame_id","alice_sha256","bob_sha256","transcript_bytes_len","transcript_bytes_sha256")
CSV_FIELDS=CSV_PREFIX_FIELDS+OUTCOME_FIELDS
def validate_outcome_v5(row:Mapping[str,Any],events:list[Mapping[str,Any]]|None=None)->None:
    if tuple(row)!=OUTCOME_FIELDS or row["method"]!=METHOD or row["candidate_id"] not in {"V5-C0","V5-C1","V5-C2"} or row["n_pairs"]!=N or row["dimension"]!=Q or row["frame_len_symbols"]!=N or row["mapping"]!="gray":raise ValueError("v5 outcome identity")
    attempted=_status_flags(str(row["status"]))
    if (row["attempted"],row["denominator_included"]) != (attempted,attempted):raise ValueError("v5 outcome flags")
    if not attempted:
        if events:raise ValueError("v5 nonattempted events")
        return
    if row["fallback_invoked"] != (row["rounds_attempted"]==2) or row["rounds_attempted"] not in {1,2}:raise ValueError("v5 rounds")
    if row["verification_check_count"] not in {0,1,2} or row["verification_tag_bits"]!=64*row["verification_check_count"] or row["epsilon_ec"]!=row["verification_check_count"]*2.0**-64:raise ValueError("v5 verification accounting")
    if row["ldpc_syndrome_bits"] != row["h1_syndrome_bits"]+row["h2_syndrome_bits"] or row["key_dependent_disclosure_bits_total"] != row["ldpc_syndrome_bits"]+row["verification_tag_bits_component"]:raise ValueError("v5 disclosure accounting")
    if events is not None:
        if [e["event_id"] for e in events]!=list(range(1,len(events)+1)) or _events_hash(events)!=row["transcript_sha256"]:raise ValueError("v5 transcript")
        for e in events:canonical_event_v5(e)
        h1=sum(e["key_dependent_bits"] for e in events if e["event_type"]=="SYNDROME");h2=sum(e["key_dependent_bits"] for e in events if e["event_type"]=="INCREMENTAL_SYNDROME");tag=sum(e["key_dependent_bits"] for e in events if e["event_type"]=="VERIFICATION_TAG");control=sum(e["public_control_bits"] for e in events)
        if (h1,h2,tag,control)!=(row["h1_syndrome_bits"],row["h2_syndrome_bits"],row["verification_tag_bits_component"],row["public_control_bits_total"]):raise ValueError("v5 event accounting")
        checks=[e for e in events if e["event_type"]=="FRAME_TAG_CHECK"]
        seeds=[e for e in events if e["event_type"]=="VERIFICATION_SEED"]
        tags=[e for e in events if e["event_type"]=="VERIFICATION_TAG"]
        nacks=[e for e in events if e["event_type"]=="FALLBACK_NACK"]
        if len(checks)!=row["verification_check_count"] or len(seeds)!=len(tags)!=len(checks) or len(nacks)>1:raise ValueError("v5 event verification flow")
        for e in events:
            if e["event_type"]=="SYNDROME":
                if e["pass_id"]!=0 or e["direction"]!="alice_to_bob" or set(e["payload"])!={"syndrome"}:raise ValueError("v5 H1 event")
            elif e["event_type"]=="INCREMENTAL_SYNDROME":
                if e["pass_id"]!=1 or set(e["payload"])!={"h2_matrix_sha256","h2_rows","syndrome"}:raise ValueError("v5 H2 event")
            elif e["event_type"]=="VERIFICATION_SEED":
                if set(e["payload"])!={"seed_bit_length","seed_id","verification_round"} or e["payload"]["seed_bit_length"]!=2623:raise ValueError("v5 seed event")
            elif e["event_type"]=="VERIFICATION_TAG":
                if set(e["payload"])!={"tag","tag_bits","verification_round"} or e["payload"]["tag_bits"]!=64:raise ValueError("v5 tag event")
            elif e["event_type"]=="FRAME_TAG_CHECK":
                if set(e["payload"])!={"value","verification_round"} or e["payload"]["value"] not in {"match","mismatch"}:raise ValueError("v5 check event")
        if nacks:
            if len(checks)!=2 or row["fallback_invoked"] is not True or nacks[0]["parent_event_id"]!=checks[0]["event_id"]:raise ValueError("v5 fallback flow")
        elif len(checks) and checks[-1]["payload"]["value"]=="mismatch" and row["status"]!="verify_failed":raise ValueError("v5 terminal check")
def _selected_candidates(selection_manifest: Mapping[str, Any]) -> list[int]:
    """Return exactly the promoted-v4 plane selection, never caller knobs."""
    if set(selection_manifest) != {"channel_model_sha256", "codebook_manifest_sha256", "method_id", "plane_selections", "schema", "selection_sha256"}:
        raise ValueError("v5 selection schema")
    if selection_manifest["schema"] != "binary_ldpc_v4_selection_v1" or selection_manifest["method_id"] != "ldpc_formal_v4":
        raise ValueError("v5 selection identity")
    rows = selection_manifest["plane_selections"]
    if not isinstance(rows, list) or len(rows) != 10:
        raise ValueError("v5 selection planes")
    selected=[]
    for plane, row in enumerate(rows):
        if not isinstance(row, Mapping) or row.get("plane_id") != plane or type(row.get("candidate_id")) is not int:
            raise ValueError("v5 selection plane")
        matrix=codebook_v4.matrix_for(plane, row["candidate_id"])
        if row.get("canonical_bytes_sha256") != _s(codebook_v4.canonical_matrix_bytes(matrix, plane_id=plane)):
            raise ValueError("v5 selection matrix binding")
        selected.append(row["candidate_id"])
    payload=dict(selection_manifest); digest=payload.pop("selection_sha256")
    if not isinstance(digest,str) or _hash_obj(payload)!=digest:
        raise ValueError("v5 selection hash")
    return selected

@lru_cache(maxsize=32)
def _rebuild_bundle(selection_bytes: bytes, h2_bytes: bytes, policy_bytes: bytes, channel_sha: str) -> tuple[tuple[int, ...], dict[str, Any]]:
    selection_manifest=json.loads(selection_bytes.decode("ascii")); h2_manifest=json.loads(h2_bytes.decode("ascii")); policy_manifest=json.loads(policy_bytes.decode("ascii"))
    selected=_selected_candidates(selection_manifest)
    # Rebuild every policy-derived byte before disclosure.  The manifest builder
    # is intentionally pure and cannot consult a source or output path.
    kwargs={"selected_candidates":selected,"selection_sha256":selection_manifest["selection_sha256"],"codebook_manifest_sha256":selection_manifest["codebook_manifest_sha256"],"channel_model_sha256":selection_manifest["channel_model_sha256"],"h2_manifest":h2_manifest}
    verify_h2 = __import__(__package__ + ".codebook_v5_h2", fromlist=["verify_h2_manifest"]).verify_h2_manifest
    verify_h2(h2_manifest, selected)
    rebuilt=build_v5_policy_manifest(**kwargs)
    if dict(policy_manifest) != rebuilt or channel_sha != selection_manifest["channel_model_sha256"]:
        raise ValueError("v5 policy manifest binding")
    return tuple(selected), rebuilt

def _bound_policy(candidate_policy: Mapping[str, Any], policy_manifest: Mapping[str, Any], selection_manifest: Mapping[str, Any], channel_model: Mapping[str, Any], h2_manifest: Mapping[str, Any]) -> tuple[str,list[int],dict[str,Any]]:
    selected,reconstructed=_rebuild_bundle(_c(selection_manifest),_c(h2_manifest),_c(policy_manifest),str(channel_model.get("model_sha256", "")))
    if dict(policy_manifest) != reconstructed:
        raise ValueError("v5 policy manifest binding")
    candidates=policy_manifest["candidates"]
    if not isinstance(candidate_policy, Mapping) or sum(dict(x)==dict(candidate_policy) for x in candidates) != 1:
        raise ValueError("v5 candidate policy membership")
    if candidate_policy.get("candidate_id") not in {"V5-C0","V5-C1","V5-C2"}:
        raise ValueError("v5 candidate policy")
    # The channel object is bound by its canonical v4 hash field, not an
    # independently supplied string.
    if channel_model.get("model_sha256") != selection_manifest["channel_model_sha256"]:
        raise ValueError("v5 channel binding")
    return str(candidate_policy["candidate_id"]), list(selected), dict(candidate_policy)


def _production_preflight(policy: Mapping[str, Any], selected: list[int], bob_symbols: np.ndarray, stratum: str, channel_model: Mapping[str, Any]) -> dict[str, Any]:
    """Pin the real ldpc constructor for every registered pass/matrix."""
    try:
        if importlib.metadata.version("ldpc") != "2.4.1":
            return {"status":"backend_unavailable"}
        from ldpc import BpOsdDecoder  # type: ignore[import-not-found]
        entries=policy["preflight"]
        if not isinstance(entries,list) or not entries: raise ValueError("preflight entries")
        for entry in entries:
            p=entry["plane_id"]; h1=codebook_v4.matrix_for(p,selected[p])
            h=h1 if entry["matrix_kind"] == "H1" else np.vstack((h1,generate_h2(p,h1)[0])).astype(np.uint8)
            if h.shape != (entry["h_rows"],entry["h_cols"]): raise ValueError("preflight shape")
            strong=entry["decoder_sha256"] == policy.get("fallback_decoder",{}).get("decoder_sha256") or entry["decoder_sha256"] == policy["round0_decoder"]["decoder_sha256"] and policy["candidate_id"] == "V5-C1"
            params={"max_iter":100 if strong else 50,"bp_method":"product_sum","schedule":"serial","omp_thread_count":1,"serial_schedule_order":list(range(N)),"osd_method":"OSD_CS" if strong else "OSD_0","osd_order":2 if strong else 0,"error_channel":np.asarray(v5_plane_error_channel(bob_symbols,p,stratum,channel_model),dtype=np.float64).tolist()}
            BpOsdDecoder(h,**params)
        return {"status":"ok","dependency_version":"2.4.1","backend_name":"ldpc.BpOsdDecoder"}
    except Exception:
        return {"status":"backend_unavailable"}

def run_ldpc_formal_v5(alice_symbols:Any,bob_symbols:Any,*,pair_idx_sequence,dataset_id:str,frame_id:str,stratum:str,candidate_policy,policy_manifest,selection_manifest,channel_model,h2_manifest,locked_seeds,_decoder_factory=None,_preflight_result=None,_clock:Callable[[],float]=time.monotonic)->dict:
    """Execute one bound v5 frame; this function has no package or file I/O."""
    started=_clock(); events=[]; calls=checks=0; raw=float("nan"); cap={"wall_s":10.0,"decoder_calls":10,"events":32}; candidate_id=""
    class _CapSignal(Exception):
        def __init__(self, reason): self.reason=reason
    def add(t,d,p,payload,k=0,c=0,parent=None,pass_id=0):
        if len(events)>=int(cap["events"]):raise _CapSignal("events")
        e={"event_id":len(events)+1,"frame_key":f"{dataset_id}:{frame_id}","method":METHOD,"event_type":t,"direction":d,"parent_event_id":parent,"pass_id":pass_id,"plane_id":p,"key_dependent_bits":k,"public_control_bits":c,"payload":payload};canonical_event_v5(e);events.append(e);return True
    def finish(status,reason):
        if status=="aborted_resource_limit" and len(events)<int(cap["events"]):
            add("ABORT","control",-1,{"cap":reason,"reason":"resource_limit"})
        attempted=_status_flags(status); h1=sum(e["key_dependent_bits"] for e in events if e["event_type"]=="SYNDROME");h2=sum(e["key_dependent_bits"] for e in events if e["event_type"]=="INCREMENTAL_SYNDROME");tag=sum(e["key_dependent_bits"] for e in events if e["event_type"]=="VERIFICATION_TAG");control=sum(e["public_control_bits"] for e in events);fallback=any(e["event_type"]=="FALLBACK_NACK" for e in events)
        safe_pair=sha256_bytes(_c([int(x) for x in pair_idx_sequence])) if status not in _NON else sha256_bytes(_c([]))
        sel=selection_manifest if isinstance(selection_manifest,Mapping) else {}; chan=channel_model if isinstance(channel_model,Mapping) else {}; h2m=h2_manifest if isinstance(h2_manifest,Mapping) else {}; pol=candidate_policy if isinstance(candidate_policy,Mapping) else {}
        out={"dataset_id":str(dataset_id),"frame_id":str(frame_id),"n_pairs":N,"pair_idx_sequence_sha256":safe_pair,"method":METHOD,"candidate_id":candidate_id or "V5-C0","attempted":attempted,"denominator_included":attempted,"status":status,"failure_reason":reason,"dimension":Q,"frame_len_symbols":N,"raw_ser":raw,"fallback_invoked":fallback,"rounds_attempted":1+int(fallback),"verification_invoked":checks>0,"verification_seed_id_round0":next((e["payload"]["seed_id"] for e in events if e["event_type"]=="VERIFICATION_SEED" and e["pass_id"]==0),""),"verification_seed_id_round1":next((e["payload"]["seed_id"] for e in events if e["event_type"]=="VERIFICATION_SEED" and e["pass_id"]==1),""),"verification_tag_bits":tag,"epsilon_ec":checks*2.0**-64,"key_dependent_disclosure_bits_total":h1+h2+tag,"public_control_bits_total":control,"transcript_first_event_id":1 if events else None,"transcript_last_event_id":len(events) if events else None,"transcript_sha256":_events_hash(events),"runtime_s":max(0.,_clock()-started),"decoder_call_count":calls,"verification_check_count":checks,"ldpc_syndrome_bits":h1+h2,"h1_syndrome_bits":h1,"h2_syndrome_bits":h2,"verification_tag_bits_component":tag,"feedback_control_bits":sum(e["public_control_bits"] for e in events if e["event_type"]=="FALLBACK_NACK"),"selection_sha256":sel.get("selection_sha256", ""),"channel_model_sha256":str(chan.get("model_sha256","")),"h1_codebook_manifest_sha256":sel.get("codebook_manifest_sha256", ""),"h2_manifest_sha256":h2m.get("manifest_sha256", ""),"policy_sha256":pol.get("policy_sha256", ""),"mapping":"gray","leakage_comparison_policy":"method_specific_not_cross_ranked","backend_name":"ldpc.BpOsdDecoder" if _decoder_factory is None and status not in _NON else ("test_injected" if _decoder_factory else ""),"backend_version":"2.4.1" if status not in _NON else ""}
        return {"outcome":out,"events":events}
    try:
        candidate_id,selected_candidates,policy=_bound_policy(candidate_policy,policy_manifest,selection_manifest,channel_model,h2_manifest)
        cap=dict(policy["caps"])
        a=np.asarray(alice_symbols);b=np.asarray(bob_symbols); indices=np.asarray(pair_idx_sequence)
        if stratum not in {"bw120","bw180","bw200"} or a.shape!=(N,) or b.shape!=(N,) or indices.shape!=(N,) or not np.issubdtype(indices.dtype,np.integer) or np.any(a<0) or np.any(a>=Q) or np.any(b<0) or np.any(b>=Q):raise ValueError("input")
        seeds=[locked_seed_bits(x,2623) for x in locked_seeds]
        if len(seeds)!=2:raise ValueError("seeds")
    except Exception as e:return finish("invalid_input",str(e))
    raw=frame_symbol_error_rate(a,b);alice=symbols_to_bits(a,Q,"gray"); original=symbols_to_bits(b,Q,"gray"); bob=original.copy(); factory=_decoder_factory
    check=dict(_preflight_result) if _preflight_result is not None else _production_preflight(policy,selected_candidates,b,stratum,channel_model)
    if check.get("status")!="ok" or (_preflight_result is None and check.get("dependency_version")!="2.4.1"):return finish("backend_unavailable","ldpc pinned dependency/API unavailable")
    if factory is None:
        try:
            from ldpc import BpOsdDecoder  # type: ignore[import-not-found]
            factory=BpOsdDecoder
        except Exception:return finish("backend_unavailable","ldpc constructor unavailable")
    strong=candidate_id=="V5-C1"
    def decode(h,delta,p,force_strong):
        nonlocal calls
        if _clock()-started>=float(cap["wall_s"]):raise _CapSignal("wall_s")
        if calls>=int(cap["decoder_calls"]):raise _CapSignal("decoder_calls")
        calls+=1; params={"max_iter":100 if force_strong else 50,"bp_method":"product_sum","schedule":"serial","omp_thread_count":1,"serial_schedule_order":list(range(N)),"osd_method":"OSD_CS" if force_strong else "OSD_0","osd_order":2 if force_strong else 0,"error_channel":np.asarray(v5_plane_error_channel(b,p,stratum,channel_model),dtype=np.float64).tolist()};e=np.asarray(factory(h,**params).decode(delta)).reshape(-1)
        if e.size!=N or np.any((e!=0)&(e!=1)):raise ValueError("malformed_decoder_output")
        if not np.array_equal(_syn(h,e),delta):raise ArithmeticError("decoder_syndrome_mismatch")
        return e.astype(np.uint8)
    try:
        for p in PLANES:
            h=codebook_v4.matrix_for(p,selected_candidates[p]);s=_syn(h,alice[:,p]); add("SYNDROME","alice_to_bob",p,{"syndrome":np.packbits(s,bitorder="big").tobytes().hex()},len(s));bob[:,p]^=decode(h,s^_syn(h,original[:,p]),p,strong)
    except _CapSignal as exc:return finish("aborted_resource_limit",exc.reason)
    except ArithmeticError:return finish("syndrome_inconsistent","decoder_syndrome_mismatch")
    except ValueError:return finish("decoder_error","malformed_decoder_output")
    except Exception:return finish("decoder_error","decoder_exception")
    try:
        if _clock()-started>=float(cap["wall_s"]):raise _CapSignal("wall_s")
        tag=toeplitz_tag(alice.reshape(-1),seeds[0]).hex();add("VERIFICATION_SEED","control",-1,{"seed_bit_length":2623,"seed_id":locked_seeds[0]["seed_id"],"verification_round":0},0,2623);add("VERIFICATION_TAG","alice_to_bob",-1,{"tag":tag,"tag_bits":64,"verification_round":0},64);ok=toeplitz_tag(bob.reshape(-1),seeds[0]).hex()==tag;checks=1;add("FRAME_TAG_CHECK","bob_local",-1,{"value":"match" if ok else "mismatch","verification_round":0})
    except _CapSignal as exc:return finish("aborted_resource_limit",exc.reason)
    if ok or candidate_id!="V5-C2":return finish("verified_success" if ok else "verify_failed","" if ok else "toeplitz_mismatch")
    try: parent=events[-1]["event_id"];add("FALLBACK_NACK","bob_to_alice",-1,{"reason":"toeplitz_mismatch","value":"fallback_requested"},0,1,parent,1);bob=original.copy()
    except _CapSignal as exc:return finish("aborted_resource_limit",exc.reason)
    try:
        for p in PLANES:
            h1=codebook_v4.matrix_for(p,selected_candidates[p]);h2,_=generate_h2(p,h1);h=np.vstack((h1,h2)).astype(np.uint8);s2=_syn(h2,alice[:,p]);add("INCREMENTAL_SYNDROME","alice_to_bob",p,{"h2_matrix_sha256":_s(canonical_h2_bytes(h2,plane_id=p,h1=h1)),"h2_rows":h2.shape[0],"syndrome":np.packbits(s2,bitorder="big").tobytes().hex()},len(s2),0,parent,1); bob[:,p]^=decode(h,np.concatenate((_syn(h1,alice[:,p]),s2))^_syn(h,original[:,p]),p,True)
    except _CapSignal as exc:return finish("aborted_resource_limit",exc.reason)
    except ArithmeticError:return finish("syndrome_inconsistent","decoder_syndrome_mismatch")
    except Exception:return finish("decoder_error","decoder_exception")
    try:
        if _clock()-started>=float(cap["wall_s"]):raise _CapSignal("wall_s")
        tag=toeplitz_tag(alice.reshape(-1),seeds[1]).hex();add("VERIFICATION_SEED","control",-1,{"seed_bit_length":2623,"seed_id":locked_seeds[1]["seed_id"],"verification_round":1},0,2623,parent,1);add("VERIFICATION_TAG","alice_to_bob",-1,{"tag":tag,"tag_bits":64,"verification_round":1},64,0,parent,1);ok=toeplitz_tag(bob.reshape(-1),seeds[1]).hex()==tag;checks=2;add("FRAME_TAG_CHECK","bob_local",-1,{"value":"match" if ok else "mismatch","verification_round":1},0,0,parent,1)
    except _CapSignal as exc:return finish("aborted_resource_limit",exc.reason)
    return finish("verified_success" if ok else "verify_failed","" if ok else "toeplitz_mismatch")


def _is_hex(value: Any, width: int) -> bool:
    return isinstance(value, str) and len(value) == width and value == value.lower() and all(c in "0123456789abcdef" for c in value)


def _validate_event_flow_v5(events: list[Mapping[str, Any]], *, frame_key: str, candidate_id: str) -> None:
    """Validate the deliberately small v5 transcript grammar without a decoder."""
    if not isinstance(events, list):
        raise ValueError("v5 events list")
    checks=[]; i=0
    def expect(kind: str, pass_id: int, plane: int | None = None) -> Mapping[str, Any]:
        nonlocal i
        if i >= len(events): raise ValueError("v5 event truncation")
        e=events[i]; i += 1
        if e.get("event_type") != kind or e.get("pass_id") != pass_id or e.get("frame_key") != frame_key or e.get("method") != METHOD:
            raise ValueError("v5 event order")
        if plane is not None and e.get("plane_id") != plane: raise ValueError("v5 event plane")
        return e
    for p in PLANES:
        e=expect("SYNDROME",0,p)
        if e["direction"] != "alice_to_bob" or e["parent_event_id"] is not None or e["public_control_bits"] != 0 or e["key_dependent_bits"] != codebook_v4.row_count(p) or set(e["payload"]) != {"syndrome"} or not _is_hex(e["payload"]["syndrome"], 2*((codebook_v4.row_count(p)+7)//8)):
            raise ValueError("v5 H1 envelope")
    for kind in ("VERIFICATION_SEED","VERIFICATION_TAG","FRAME_TAG_CHECK"):
        e=expect(kind,0)
        if e["plane_id"] != -1 or e["parent_event_id"] is not None: raise ValueError("v5 round0 parent")
        checks.append(e if kind == "FRAME_TAG_CHECK" else None)
    seed, tag, check = events[i-3:i]
    if seed["direction"] != "control" or seed["key_dependent_bits"] != 0 or seed["public_control_bits"] != 2623 or set(seed["payload"]) != {"seed_bit_length","seed_id","verification_round"} or seed["payload"] != {"seed_bit_length":2623,"seed_id":seed["payload"].get("seed_id"),"verification_round":0} or not _is_hex(seed["payload"]["seed_id"],64): raise ValueError("v5 seed envelope")
    if tag["direction"] != "alice_to_bob" or tag["key_dependent_bits"] != 64 or tag["public_control_bits"] != 0 or set(tag["payload"]) != {"tag","tag_bits","verification_round"} or tag["payload"].get("tag_bits") != 64 or tag["payload"].get("verification_round") != 0 or not _is_hex(tag["payload"].get("tag"),16): raise ValueError("v5 tag envelope")
    if check["direction"] != "bob_local" or check["key_dependent_bits"] != 0 or check["public_control_bits"] != 0 or set(check["payload"]) != {"value","verification_round"} or check["payload"].get("verification_round") != 0: raise ValueError("v5 check envelope")
    if check["payload"].get("value") == "match":
        if i != len(events): raise ValueError("v5 event after terminal")
        return
    if check["payload"].get("value") != "mismatch": raise ValueError("v5 check value")
    if candidate_id != "V5-C2":
        if i != len(events): raise ValueError("v5 event after terminal")
        return
    nack=expect("FALLBACK_NACK",1)
    if nack["direction"] != "bob_to_alice" or nack["plane_id"] != -1 or nack["parent_event_id"] != check["event_id"] or nack["key_dependent_bits"] != 0 or nack["public_control_bits"] != 1 or nack["payload"] != {"reason":"toeplitz_mismatch","value":"fallback_requested"}: raise ValueError("v5 nack envelope")
    for p in PLANES:
        e=expect("INCREMENTAL_SYNDROME",1,p)
        if e["direction"] != "alice_to_bob" or e["parent_event_id"] != check["event_id"] or e["key_dependent_bits"] != [16,16,16,24,24,32,48,80,88,48][p] or e["public_control_bits"] != 0 or set(e["payload"]) != {"h2_matrix_sha256","h2_rows","syndrome"} or e["payload"].get("h2_rows") != e["key_dependent_bits"] or not _is_hex(e["payload"].get("h2_matrix_sha256"),64) or not _is_hex(e["payload"].get("syndrome"),2*((e["key_dependent_bits"]+7)//8)): raise ValueError("v5 H2 envelope")
    seed=expect("VERIFICATION_SEED",1); tag=expect("VERIFICATION_TAG",1); check1=expect("FRAME_TAG_CHECK",1)
    if any(e["parent_event_id"] != check["event_id"] for e in (seed,tag,check1)) or i != len(events): raise ValueError("v5 round1 parent/order")
    if seed["direction"] != "control" or seed["key_dependent_bits"] != 0 or seed["public_control_bits"] != 2623 or set(seed["payload"]) != {"seed_bit_length","seed_id","verification_round"} or seed["payload"].get("seed_bit_length") != 2623 or seed["payload"].get("verification_round") != 1 or not _is_hex(seed["payload"].get("seed_id"),64): raise ValueError("v5 seed1 envelope")
    if tag["direction"] != "alice_to_bob" or tag["key_dependent_bits"] != 64 or tag["public_control_bits"] != 0 or set(tag["payload"]) != {"tag","tag_bits","verification_round"} or tag["payload"].get("tag_bits") != 64 or tag["payload"].get("verification_round") != 1 or not _is_hex(tag["payload"].get("tag"),16): raise ValueError("v5 tag1 envelope")
    if check1["direction"] != "bob_local" or check1["key_dependent_bits"] != 0 or check1["public_control_bits"] != 0 or set(check1["payload"]) != {"value","verification_round"} or check1["payload"].get("verification_round") != 1 or check1["payload"].get("value") not in {"match","mismatch"}: raise ValueError("v5 check1 envelope")


def verify_public_payload_v5(outcome, events, *, alice_symbols, pair_idx_sequence, stratum: str, candidate_policy, policy_manifest, selection_manifest, channel_model, h2_manifest, locked_seeds) -> dict:
    """Read-only public-payload reconstruction; deliberately never decodes Bob."""
    candidate_id, selected, policy = _bound_policy(candidate_policy, policy_manifest, selection_manifest, channel_model, h2_manifest)
    a=np.asarray(alice_symbols); indices=np.asarray(pair_idx_sequence)
    if stratum not in {"bw120","bw180","bw200"} or a.shape != (N,) or indices.shape != (N,) or not np.issubdtype(indices.dtype,np.integer) or np.any(a < 0) or np.any(a >= Q): raise ValueError("v5 public input")
    if tuple(outcome) != OUTCOME_FIELDS or outcome["candidate_id"] != candidate_id or outcome["pair_idx_sequence_sha256"] != sha256_bytes(_c([int(x) for x in indices])): raise ValueError("v5 public outcome identity")
    validate_outcome_v5(outcome, events)
    if not outcome["attempted"]:
        if events: raise ValueError("v5 public nonattempted")
        return {"status":"verified","decoder_reexecution":False,"event_count":0,"transcript_sha256":outcome["transcript_sha256"],"key_dependent_disclosure_bits_total":0,"public_control_bits_total":0}
    seeds=[locked_seed_bits(x,2623) for x in locked_seeds]
    if len(seeds) != 2: raise ValueError("v5 public seeds")
    frame_key=f"{outcome['dataset_id']}:{outcome['frame_id']}"
    complete=outcome["status"] in {"verified_success","verify_failed"}
    if complete:
        _validate_event_flow_v5(events, frame_key=frame_key, candidate_id=candidate_id)
    else:
        # Retained attempted failures are legal prefixes, never synthetic full
        # rounds.  Canonical IDs/hash and the generic accounting validator have
        # already run; reject any non-prefix event sequence here.
        allowed=("SYNDROME","VERIFICATION_SEED","VERIFICATION_TAG","FRAME_TAG_CHECK","FALLBACK_NACK","INCREMENTAL_SYNDROME","ABORT")
        if any(e["frame_key"] != frame_key or e["event_type"] not in allowed for e in events): raise ValueError("v5 partial prefix")
        for pos,e in enumerate(events,1):
            if e["event_id"] != pos or e["method"] != METHOD: raise ValueError("v5 partial ids")
            if e["pass_id"] == 0 and e["parent_event_id"] is not None: raise ValueError("v5 partial parent")
            if e["event_type"] == "SYNDROME" and (e["pass_id"] != 0 or e["plane_id"] != sum(x["event_type"]=="SYNDROME" for x in events[:pos-1])): raise ValueError("v5 partial H1 order")
            if e["event_type"] == "INCREMENTAL_SYNDROME" and (e["pass_id"] != 1 or e["parent_event_id"] is None): raise ValueError("v5 partial H2 parent")
        if any(e["event_type"] == "ABORT" for e in events[:-1]): raise ValueError("v5 partial abort order")
    alice=symbols_to_bits(a,Q,"gray")
    for e in events:
        p=e["plane_id"]
        if e["event_type"] == "SYNDROME":
            h=codebook_v4.matrix_for(p,selected[p]); expected=np.packbits(_syn(h,alice[:,p]),bitorder="big").tobytes().hex()
            if e["payload"]["syndrome"] != expected: raise ValueError("v5 public H1 syndrome")
        elif e["event_type"] == "INCREMENTAL_SYNDROME":
            h1=codebook_v4.matrix_for(p,selected[p]); h2,_=generate_h2(p,h1); expected=np.packbits(_syn(h2,alice[:,p]),bitorder="big").tobytes().hex()
            if e["payload"]["syndrome"] != expected or e["payload"]["h2_matrix_sha256"] != _s(canonical_h2_bytes(h2,plane_id=p,h1=h1)): raise ValueError("v5 public H2 syndrome")
        elif e["event_type"] == "VERIFICATION_SEED":
            r=e["pass_id"]
            if e["payload"]["seed_id"] != locked_seeds[r].get("seed_id"): raise ValueError("v5 public seed identity")
        elif e["event_type"] == "VERIFICATION_TAG":
            r=e["pass_id"]
            if e["payload"]["tag"] != toeplitz_tag(alice.reshape(-1),seeds[r]).hex(): raise ValueError("v5 public tag")
    checks=[e for e in events if e["event_type"] == "FRAME_TAG_CHECK"]
    if complete:
        last_check=checks[-1]
        expected_status="verified_success" if last_check["payload"]["value"] == "match" else "verify_failed"
        if outcome["status"] != expected_status: raise ValueError("v5 public terminal status")
    return {"status":"verified","decoder_reexecution":False,"event_count":len(events),"transcript_sha256":outcome["transcript_sha256"],"key_dependent_disclosure_bits_total":outcome["key_dependent_disclosure_bits_total"],"public_control_bits_total":outcome["public_control_bits_total"]}


def _csv_scalar(name: str, value: Any) -> str:
    if name in {"attempted","denominator_included","fallback_invoked","verification_invoked"}:
        if type(value) is not bool: raise ValueError("v5 CSV boolean")
        return "true" if value else "false"
    if name in {"raw_ser","epsilon_ec","runtime_s"}:
        if not isinstance(value,(float,int)) or isinstance(value,bool) or not np.isfinite(value) or (name == "runtime_s" and value < 0): raise ValueError("v5 CSV float")
        return repr(float(value))
    if name in {"transcript_first_event_id","transcript_last_event_id"}:
        if value is None: return ""
        if type(value) is not int: raise ValueError("v5 CSV optional int")
        return str(value)
    if isinstance(value,(dict,list,tuple)) or value is None: raise ValueError("v5 CSV scalar")
    return str(value)


def encode_outcome_csv_v5(rows) -> bytes:
    if not isinstance(rows,(list,tuple)) or not rows: raise ValueError("v5 CSV rows")
    output=StringIO(newline="")
    writer=csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    for row in rows:
        if not isinstance(row,Mapping) or tuple(row) != CSV_FIELDS: raise ValueError("v5 CSV fields")
        formal={key:row[key] for key in OUTCOME_FIELDS}; validate_outcome_v5(formal)
        if row["role"] not in {"development","confirmation","real"} or row["stratum"] not in {"bw120","bw180","bw200"} or not _is_hex(row["alice_sha256"],64) or not _is_hex(row["bob_sha256"],64) or not _is_hex(row["transcript_bytes_sha256"],64) or type(row["transcript_bytes_len"]) is not int or row["transcript_bytes_len"] < 0: raise ValueError("v5 CSV prefix")
        writer.writerow({key:_csv_scalar(key,row[key]) for key in CSV_FIELDS})
    raw=output.getvalue().encode("utf-8")
    if b"\r" in raw: raise ValueError("v5 CSV CR")
    return raw


def decode_outcome_csv_v5(raw: bytes) -> list[dict]:
    if not isinstance(raw,bytes) or not raw or b"\r" in raw: raise ValueError("v5 CSV bytes")
    try: text=raw.decode("utf-8")
    except UnicodeDecodeError as exc: raise ValueError("v5 CSV utf8") from exc
    if not text.endswith("\n"): raise ValueError("v5 CSV LF")
    reader=csv.DictReader(StringIO(text,newline=""))
    if tuple(reader.fieldnames or ()) != CSV_FIELDS: raise ValueError("v5 CSV header")
    rows=[]
    int_fields={"n_pairs","dimension","frame_len_symbols","rounds_attempted","verification_tag_bits","key_dependent_disclosure_bits_total","public_control_bits_total","decoder_call_count","verification_check_count","ldpc_syndrome_bits","h1_syndrome_bits","h2_syndrome_bits","verification_tag_bits_component","feedback_control_bits","transcript_bytes_len"}
    bool_fields={"attempted","denominator_included","fallback_invoked","verification_invoked"}
    float_fields={"raw_ser","epsilon_ec","runtime_s"}
    opt_int={"transcript_first_event_id","transcript_last_event_id"}
    for wire in reader:
        if set(wire) != set(CSV_FIELDS) or None in wire: raise ValueError("v5 CSV row")
        row={}
        for key,value in wire.items():
            if key in bool_fields:
                if value not in {"true","false"}: raise ValueError("v5 CSV bool");
                row[key]=value == "true"
            elif key in float_fields:
                try: number=float(value)
                except ValueError as exc: raise ValueError("v5 CSV float parse") from exc
                if not np.isfinite(number) or (key == "runtime_s" and number < 0) or repr(number) != value: raise ValueError("v5 CSV float canonical")
                row[key]=number
            elif key in int_fields:
                if not value or str(int(value)) != value: raise ValueError("v5 CSV integer")
                row[key]=int(value)
            elif key in opt_int:
                if value == "": row[key]=None
                elif str(int(value)) == value: row[key]=int(value)
                else: raise ValueError("v5 CSV optional integer")
            else: row[key]=value
        rows.append(row)
    if not rows or encode_outcome_csv_v5(rows) != raw: raise ValueError("v5 CSV roundtrip")
    return rows
