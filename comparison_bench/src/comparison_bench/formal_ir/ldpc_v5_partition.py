"""Read-only v5 development/confirmation partition lock."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any,Mapping
import numpy as np
from . import ldpc_v4_10db_source as source
from .ldpc_v5_predecessors import build_predecessor_binding

STRATA=source.STRATA; N=256; Q=1024
def _c(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")
def _s(v:Any)->str:return hashlib.sha256(v if isinstance(v,bytes) else _c(v)).hexdigest()
def _source_binding(lock:Mapping[str,Any])->dict[str,Any]:
    return {"source_adapter":"comparison_bench.formal_ir.ldpc_v4_10db_source.build_source_lock","source_adapter_sha256":_s(Path(source.__file__).read_bytes()),"source_lock_schema":lock["schema"],"source_lock_sha256":lock["lock_sha256"],"source_lock_file_sha256":_s(_c(lock)),"raw_main_sha256":lock["raw_main"]["sha256"],"raw_chunk_sha256":lock["raw_chunk"]["sha256"]}
def _all_rows(lock:Mapping[str,Any])->list[dict[str,Any]]:
    acq=_s({"main":lock["raw_main"]["sha256"],"chunk":lock["raw_chunk"]["sha256"]})
    rows=[]
    for ds in lock["datasets"]:
        d=Path(ds["sidecar_dir"]); a=np.load(d/"a_eff.npy",allow_pickle=False); b=np.load(d/"b_eff.npy",allow_pickle=False)
        for frame_id in range(ds["complete_frames"]):
            fid,pid=source._identity(acq,ds["stratum"],frame_id,a,b)
            rows.append({"stratum":ds["stratum"],"frame_id":frame_id,"frame_identity":fid,"payload_identity":pid,"source_record_sha256":ds["source_record_sha256"],"source_pair_start":frame_id*N,"source_pair_end":(frame_id+1)*N})
    return rows
def build_partition_lock() -> dict:
    src=source.build_source_lock(); rows=_all_rows(src)
    root=Path("comparison_bench/outputs_comparison/formal_ir_methods")
    binding=build_predecessor_binding(root)
    v1=json.loads((root/"20260729_v1_binary_ldpc_v4_10db_transfer"/"real_data_lock.json").read_bytes())
    v2=json.loads((root/"20260729_v2_binary_ldpc_v4_10db_transfer"/"real_data_lock.json").read_bytes())
    raw1=(root/"20260729_v1_binary_ldpc_v4_10db_transfer"/"real_data_lock.json").read_bytes(); raw2=(root/"20260729_v2_binary_ldpc_v4_10db_transfer"/"real_data_lock.json").read_bytes()
    chosen=v1["selected_frames"]
    if raw1!=raw2 or chosen!=v2["selected_frames"]:raise ValueError("predecessor lock mismatch")
    excluded={x["frame_identity"] for x in chosen}; payloads={x["payload_identity"] for x in chosen}
    if len(excluded)!=384 or len(payloads)!=384:raise ValueError("predecessor selection uniqueness")
    role=[]
    for st in STRATA:
        eligible=[x for x in rows if x["stratum"]==st and x["frame_identity"] not in excluded]
        rank=sorted((hashlib.sha256(f"binary_ldpc_v5_10db_partition_v1|{st}|{x['frame_identity']}".encode("ascii")).hexdigest(),x) for x in eligible)
        if len(rank)<640:raise ValueError("partition capacity")
        for i,(digest,x) in enumerate(rank[:640]):
            role_name="confirmation" if i<128 else "development"; rr=i if i<128 else i-128
            role.append({"role":role_name,"stratum":st,"partition_rank":i,"role_rank":rr,"ranking_sha256":digest,**x})
    confirmation=[x for x in role if x["role"]=="confirmation"]; development=[x for x in role if x["role"]=="development"]
    if len(confirmation)!=384 or len(development)!=1536 or len({x["frame_identity"] for x in role})!=len(role) or len({x["payload_identity"] for x in role})!=len(role):raise ValueError("partition overlap")
    by=lambda z:[x[z] for x in rows]
    pred={"v1_lock_file_sha256":_s(raw1),"v2_lock_file_sha256":_s(raw2),"lock_bytes_identical":True,"identity_count":384,"frame_identities_sha256":_s(sorted(excluded)),"payload_identities_sha256":_s(sorted(payloads)),"counts_by_stratum":{s:sum(x["stratum"]==s for x in chosen) for s in STRATA}}
    base={"schema":"binary_ldpc_v5_10db_partition_lock_v1","source_binding":_source_binding(src),"predecessor_binding":binding,"predecessor_selection":pred,"partition_policy":{"selection_domain":"binary_ldpc_v5_10db_partition_v1","ranking":"SHA256(binary_ldpc_v5_10db_partition_v1|stratum|frame_identity)","tie_breaker":"frame_identity","confirmation_partition_ranks":[0,127],"development_partition_ranks":[128,639],"frame_len_symbols":256,"dimension":1024,"mapping":"gray"},"pool_summary":{"complete_frames_by_stratum":{s:sum(x["stratum"]==s for x in rows) for s in STRATA},"excluded_frames_by_stratum":{s:sum(x["stratum"]==s for x in chosen) for s in STRATA},"eligible_frames_by_stratum":{s:sum(x["stratum"]==s and x["frame_identity"] not in excluded for x in rows) for s in STRATA},"all_frame_identities_sha256":_s(by("frame_identity")),"all_payload_identities_sha256":_s(by("payload_identity")),"eligible_frame_identities_sha256":_s([x["frame_identity"] for x in rows if x["frame_identity"] not in excluded]),"eligible_payload_identities_sha256":_s([x["payload_identity"] for x in rows if x["frame_identity"] not in excluded])},"role_rows":role,"role_digests":{"confirmation_count":384,"development_count":1536,"confirmation_rows_sha256":_s(confirmation),"development_rows_sha256":_s(development),"all_role_rows_sha256":_s(role)},"access_contract":{"confirmation_api":"absent_phase1","confirmation_decoding_authorized":False,"development_api":"development_arrays_for_frame_v1","role_enforcement":"exact_locked_row_membership_before_array_load"}}
    return {**base,"partition_sha256":_s(base)}
def validate_partition_lock(lock:Mapping)->None:
    if not isinstance(lock,Mapping):raise ValueError("partition lock")
    got=dict(lock); digest=got.pop("partition_sha256",None)
    if not isinstance(digest,str) or _s(got)!=digest:raise ValueError("partition self hash")
    if dict(lock)!=build_partition_lock():raise ValueError("partition reconstruction")
def write_partition_lock(path:Path)->dict:
    lock=build_partition_lock(); validate_partition_lock(lock)
    with Path(path).open("x",encoding="ascii",newline="\n") as f:f.write(_c(lock).decode("ascii"))
    return lock
def development_rows(lock:Mapping)->list[dict]:
    validate_partition_lock(lock); return [dict(x) for x in lock["role_rows"] if x["role"]=="development"]
def development_arrays_for_frame(lock:Mapping,row:Mapping)->tuple[np.ndarray,np.ndarray]:
    validate_partition_lock(lock)
    candidates=[x for x in lock["role_rows"] if x["role"]=="development" and dict(x)==dict(row)]
    if len(candidates)!=1:raise ValueError("development locked-row membership")
    src=source.build_source_lock(); frame={k:row[k] for k in ("stratum","frame_id")}
    a,b=source.arrays_for_frame(src,frame)
    if a.shape!=(N,) or b.shape!=(N,) or np.any(a<0) or np.any(a>=Q) or np.any(b<0) or np.any(b>=Q):raise ValueError("development arrays")
    return a.copy(),b.copy()
