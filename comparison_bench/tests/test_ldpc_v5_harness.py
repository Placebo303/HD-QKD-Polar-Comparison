import hashlib
import json
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.codebook_v5_h2 import h2_manifest
from comparison_bench.src.comparison_bench.formal_ir.ldpc_v5 import build_v5_policy_manifest
from comparison_bench.src.comparison_bench.formal_ir.ldpc_v5_test_harness import run_test_development_batch, verify_test_development_batch
from comparison_bench.src.comparison_bench.formal_ir.shared import seed_record


class _ZeroDecoder:
    def decode(self, syndrome):
        return np.zeros(256, dtype=np.uint8)


def _objects():
    root=Path("comparison_bench/outputs_comparison/formal_ir_methods")
    selection=json.loads((root/"20260728_v2_binary_ldpc_v4_synthetic"/"formal_selection_manifest.json").read_text())
    channel=json.loads((root/"20260729_v2_binary_ldpc_v4_10db_transfer"/"formal_channel_model.json").read_text())
    selected=[x["candidate_id"] for x in selection["plane_selections"]]
    h2=h2_manifest(selected,h1_codebook_manifest_sha256=selection["codebook_manifest_sha256"],h1_selection_sha256=selection["selection_sha256"])
    policy=build_v5_policy_manifest(selected_candidates=selected,selection_sha256=selection["selection_sha256"],codebook_manifest_sha256=selection["codebook_manifest_sha256"],channel_model_sha256=selection["channel_model_sha256"],h2_manifest=h2)
    rows=[]; seeds={}
    for s in ("bw120","bw180","bw200"):
        for rank in range(512):
            a=np.zeros(256,dtype=np.uint16); b=a.copy(); indices=np.arange(256,dtype=np.int64)
            rows.append({"role":"development","stratum":s,"role_rank":rank,"plan_frame_id":f"{s}-{rank}","dataset_id":s,"frame_id":str(rank),"alice":a,"bob":b,"pair_idx_sequence":indices,"alice_sha256":hashlib.sha256(a.astype("<u2").tobytes()).hexdigest(),"bob_sha256":hashlib.sha256(b.astype("<u2").tobytes()).hexdigest()})
            for candidate_index,candidate in enumerate(("V5-C0","V5-C1","V5-C2")):
                # Domain-separated fixed test seeds; all 9,216 ids are unique.
                first=np.zeros(2623,dtype=np.uint8); second=np.zeros(2623,dtype=np.uint8)
                value=(candidate_index*1536 + ("bw120","bw180","bw200").index(s)*512 + rank)*2
                for bit in range(15): first[bit]=(value>>bit)&1; second[bit]=((value+1)>>bit)&1
                seeds[f"{candidate}|{s}|{rank}"]=[seed_record(first),seed_record(second)]
    return rows,policy,selection,channel,h2,seeds


def test_full_in_memory_phase1_harness_and_read_only_verify():
    rows,policy,selection,channel,h2,seeds=_objects()
    constructed=[]
    def nullspace(h):
        a=np.asarray(h,dtype=np.uint8).copy(); piv=[]; row=0
        for col in range(a.shape[1]):
            found=next((i for i in range(row,a.shape[0]) if a[i,col]),None)
            if found is None: continue
            a[[row,found]]=a[[found,row]]; piv.append(col)
            for i in range(a.shape[0]):
                if i != row and a[i,col]: a[i] ^= a[row]
            row += 1
        free=next(x for x in range(256) if x not in piv); out=np.zeros(256,dtype=np.uint8); out[free]=1
        for r,col in reversed(list(enumerate(piv))): out[col]=int(np.dot(a[r],out)%2)
        return out
    class _StateDecoder:
        mode="ok"; calls=0
        @classmethod
        def begin_attempt(cls,candidate,stratum,rank):
            cls.calls=0
            cls.mode = ({("V5-C0","bw120",0):"exception",("V5-C0","bw120",1):"malformed",("V5-C0","bw120",2):"inconsistent",("V5-C0","bw120",3):"mismatch",("V5-C2","bw120",4):"fallback"}.get((candidate,stratum,rank),"ok"))
        def __init__(self,h,**kwargs): self.h=h
        def decode(self,syndrome):
            self.__class__.calls += 1
            if self.mode == "exception": raise RuntimeError("deterministic decoder exception")
            if self.mode == "malformed": return np.zeros(255,dtype=np.uint8)
            if self.mode == "inconsistent": return np.ones(256,dtype=np.uint8)
            if self.mode == "mismatch": return nullspace(self.h)
            if self.mode == "fallback" and self.calls <= 10: return nullspace(self.h)
            return np.zeros(256,dtype=np.uint8)
    def clocks(candidate,stratum,rank):
        if (candidate,stratum,rank) == ("V5-C0","bw120",5):
            values=iter((0.0,11.0)); return lambda: next(values,11.0)
        return __import__("time").monotonic
    batch=run_test_development_batch(rows,policies=policy["candidates"],policy_manifest=policy,selection_manifest=selection,channel_model=channel,h2_manifest=h2,seed_records=seeds,decoder_factory=_StateDecoder,preflight_result={"status":"ok"},clock_factory=clocks)
    assert verify_test_development_batch(batch,frame_records=rows,policies=policy["candidates"],policy_manifest=policy,selection_manifest=selection,channel_model=channel,h2_manifest=h2,seed_records=seeds)=={"status":"verified","test_only":True,"outcomes":4608,"decoder_reexecution":False}
    statuses={row["status"] for row in batch["outcomes"]}
    assert {"verified_success","verify_failed","decoder_error","syndrome_inconsistent"} <= statuses
    assert any(row["status"] == "aborted_resource_limit" and row["failure_reason"] == "wall_s" for row in batch["outcomes"])
    assert any(row["candidate_id"] == "V5-C2" and row["fallback_invoked"] and row["status"] == "verified_success" for row in batch["outcomes"])
    batch["outcomes"][0]["status"]="verified_success" if batch["outcomes"][0]["status"] != "verified_success" else "verify_failed"
    with __import__("pytest").raises(ValueError):
        verify_test_development_batch(batch,frame_records=rows,policies=policy["candidates"],policy_manifest=policy,selection_manifest=selection,channel_model=channel,h2_manifest=h2,seed_records=seeds)
