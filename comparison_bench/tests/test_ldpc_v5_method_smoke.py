import hashlib
import json
import sys
import types
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir.codebook_v5_h2 import h2_manifest
from comparison_bench.src.comparison_bench.formal_ir import codebook_v4
from comparison_bench.src.comparison_bench.formal_ir.ldpc_v5 import (build_v5_policy_manifest, run_ldpc_formal_v5, validate_outcome_v5,
    verify_public_payload_v5, encode_outcome_csv_v5, decode_outcome_csv_v5, canonical_event_v5, _production_preflight)
from comparison_bench.src.comparison_bench.formal_ir.shared import seed_record, toeplitz_tag


class _ZeroDecoder:
    def decode(self, syndrome):
        return np.zeros(256, dtype=np.uint8)


def _objects():
    selected=[0,0,0,0,0,0,2,0,2,2]; channel=_channel()
    root=Path("comparison_bench/outputs_comparison/formal_ir_methods")
    selection=json.loads((root/"20260728_v2_binary_ldpc_v4_synthetic"/"formal_selection_manifest.json").read_text())
    h2=h2_manifest(selected,h1_codebook_manifest_sha256=selection["codebook_manifest_sha256"],h1_selection_sha256=selection["selection_sha256"])
    policy=build_v5_policy_manifest(selected_candidates=selected,selection_sha256=selection["selection_sha256"],codebook_manifest_sha256=selection["codebook_manifest_sha256"],channel_model_sha256=selection["channel_model_sha256"],h2_manifest=h2)
    seeds=[seed_record(np.ones(2623,dtype=np.uint8)),seed_record(np.r_[1,np.zeros(2622,dtype=np.uint8)])]
    return selected,channel,selection,h2,policy,seeds


def _call(policy_index, factory, **changes):
    _,channel,selection,h2,policy,seeds=_objects()
    args=dict(pair_idx_sequence=np.arange(256),dataset_id="test",frame_id="0",stratum="bw120",candidate_policy=policy["candidates"][policy_index],policy_manifest=policy,selection_manifest=selection,channel_model=channel,h2_manifest=h2,locked_seeds=seeds,_preflight_result={"status":"ok"},_decoder_factory=factory)
    args.update(changes)
    return run_ldpc_formal_v5(np.zeros(256,dtype=np.int64),np.zeros(256,dtype=np.int64),**args)


def _channel():
    root = Path("comparison_bench/outputs_comparison/formal_ir_methods")
    return json.loads((root / "20260729_v2_binary_ldpc_v4_10db_transfer" / "formal_channel_model.json").read_text())


def test_c0_fake_success_accounting():
    seed0 = seed_record(np.zeros(2623, dtype=np.uint8))
    seed1 = seed_record(np.r_[1, np.zeros(2622, dtype=np.uint8)])
    selected = [0, 0, 0, 0, 0, 0, 2, 0, 2, 2]
    channel = _channel()
    selection = json.loads((Path("comparison_bench/outputs_comparison/formal_ir_methods") / "20260728_v2_binary_ldpc_v4_synthetic" / "formal_selection_manifest.json").read_text())
    h2 = h2_manifest(selected, h1_codebook_manifest_sha256=selection["codebook_manifest_sha256"], h1_selection_sha256=selection["selection_sha256"])
    policies = build_v5_policy_manifest(selected_candidates=selected, selection_sha256=selection["selection_sha256"], codebook_manifest_sha256=selection["codebook_manifest_sha256"], channel_model_sha256=selection["channel_model_sha256"], h2_manifest=h2)
    result = run_ldpc_formal_v5(np.zeros(256, dtype=np.int64), np.zeros(256, dtype=np.int64),
        pair_idx_sequence=np.arange(256), dataset_id="test", frame_id="0", stratum="bw120", candidate_policy=policies["candidates"][0], policy_manifest=policies,
        selection_manifest=selection, channel_model=channel, h2_manifest=h2, locked_seeds=[seed0, seed1], _preflight_result={"status": "ok"},
        _decoder_factory=lambda *args, **kwargs: _ZeroDecoder())
    validate_outcome_v5(result["outcome"], result["events"])
    assert result["outcome"]["status"] == "verified_success"
    assert result["outcome"]["key_dependent_disclosure_bits_total"] == 648


def test_c0_c1_c2_round0_success_and_invalid_policy_are_nonattempted():
    for index in range(3):
        result=_call(index,lambda *a,**k:_ZeroDecoder())
        validate_outcome_v5(result["outcome"],result["events"])
        assert result["outcome"]["status"] == "verified_success"
        assert result["outcome"]["h1_syndrome_bits"] == 584
        assert result["outcome"]["h2_syndrome_bits"] == 0
        assert result["outcome"]["verification_check_count"] == 1
    _,channel,selection,h2,policy,seeds=_objects(); bad=dict(policy["candidates"][0]); bad["caps"]=dict(bad["caps"]); bad["caps"]["events"]=31
    result=run_ldpc_formal_v5(np.zeros(256),np.zeros(256),pair_idx_sequence=np.arange(256),dataset_id="t",frame_id="0",stratum="bw120",candidate_policy=bad,policy_manifest=policy,selection_manifest=selection,channel_model=channel,h2_manifest=h2,locked_seeds=seeds,_preflight_result={"status":"ok"},_decoder_factory=lambda *a,**k:_ZeroDecoder())
    assert result["events"] == [] and result["outcome"]["status"] == "invalid_input"


def _nullspace_vector(h):
    a=np.asarray(h,dtype=np.uint8).copy(); pivots=[]; row=0
    for col in range(a.shape[1]):
        found=next((i for i in range(row,a.shape[0]) if a[i,col]),None)
        if found is None: continue
        a[[row,found]]=a[[found,row]]; pivots.append(col)
        for i in range(a.shape[0]):
            if i != row and a[i,col]: a[i] ^= a[row]
        row += 1
        if row == a.shape[0]: break
    free=next(col for col in range(a.shape[1]) if col not in pivots)
    x=np.zeros(a.shape[1],dtype=np.uint8); x[free]=1
    for r,col in reversed(list(enumerate(pivots))): x[col]=int(np.dot(a[r],x)%2)
    assert np.any(x) and not np.any((h@x)%2)
    return x


def test_c2_fallback_two_round_accounting_and_decoder_failure():
    calls=[]
    class _FallbackDecoder:
        def __init__(self,h): self.h=h; self.index=len(calls); calls.append(h)
        def decode(self,syndrome): return _nullspace_vector(self.h) if self.index < 10 else np.zeros(256,dtype=np.uint8)
    selected=[0,0,0,0,0,0,2,0,2,2]
    expanded=np.column_stack([_nullspace_vector(codebook_v4.matrix_for(p,c)) for p,c in enumerate(selected)]).reshape(-1)
    seed0=next(seed_record(bits) for i in range(100) for bits in [np.random.Generator(np.random.PCG64(i)).integers(0,2,size=2623,dtype=np.uint8)] if np.any(np.frombuffer(toeplitz_tag(expanded,bits),dtype=np.uint8)))
    result=_call(2,lambda h,**k:_FallbackDecoder(h),locked_seeds=[seed0,seed_record(np.r_[1,np.zeros(2622,dtype=np.uint8)])])
    # The first ten H1 calls return exact null vectors; the next ten stacked
    # calls return zero, forcing and then resolving the fallback.
    validate_outcome_v5(result["outcome"],result["events"])
    assert result["outcome"]["status"] == "verified_success"
    assert result["outcome"]["fallback_invoked"] is True
    assert (result["outcome"]["h1_syndrome_bits"],result["outcome"]["h2_syndrome_bits"],result["outcome"]["verification_tag_bits"],result["outcome"]["public_control_bits_total"]) == (584,392,128,5247)
    class _Bad:
        def decode(self,syndrome): return np.zeros(255,dtype=np.uint8)
    failed=_call(0,lambda *a,**k:_Bad())
    assert failed["outcome"]["status"] == "decoder_error"


def test_locally_resigned_terminal_check_and_event_schema_tamper_rejected():
    result=_call(0,lambda *a,**k:_ZeroDecoder())
    events=json.loads(json.dumps(result["events"])); outcome=dict(result["outcome"])
    check=next(e for e in events if e["event_type"]=="FRAME_TAG_CHECK")
    check["payload"]["value"]="mismatch"
    from comparison_bench.src.comparison_bench.formal_ir.ldpc_v5 import canonical_event_v5
    outcome["transcript_sha256"]=__import__("hashlib").sha256(b"".join(canonical_event_v5(e) for e in events)).hexdigest()
    with pytest.raises(ValueError): validate_outcome_v5(outcome,events)


def test_public_payload_and_canonical_csv_reject_locally_resigned_payload_drift():
    _,channel,selection,h2,policy,seeds=_objects()
    result=_call(0,lambda *a,**k:_ZeroDecoder())
    kwargs=dict(alice_symbols=np.zeros(256,dtype=np.uint16),pair_idx_sequence=np.arange(256),stratum="bw120",candidate_policy=policy["candidates"][0],policy_manifest=policy,selection_manifest=selection,channel_model=channel,h2_manifest=h2,locked_seeds=seeds)
    assert verify_public_payload_v5(result["outcome"],result["events"],**kwargs)["status"] == "verified"
    events=json.loads(json.dumps(result["events"])); outcome=dict(result["outcome"])
    events[0]["payload"]["syndrome"]="ff"*len(bytes.fromhex(events[0]["payload"]["syndrome"]))
    outcome["transcript_sha256"]=hashlib.sha256(b"".join(canonical_event_v5(e) for e in events)).hexdigest()
    with pytest.raises(ValueError): verify_public_payload_v5(outcome,events,**kwargs)
    transcript=b"".join(canonical_event_v5(e) for e in result["events"])
    row={"role":"development","stratum":"bw120","plan_frame_id":"p","alice_sha256":"0"*64,"bob_sha256":"1"*64,"transcript_bytes_len":len(transcript),"transcript_bytes_sha256":hashlib.sha256(transcript).hexdigest(),**result["outcome"]}
    raw=encode_outcome_csv_v5([row]); assert decode_outcome_csv_v5(raw)==[row]
    with pytest.raises(ValueError): decode_outcome_csv_v5(raw.replace(b"true",b"True",1))


def test_production_preflight_pins_every_registered_matrix_and_decoder_exception_is_not_cap(monkeypatch):
    selected,channel,selection,h2,policy,seeds=_objects(); calls=[]
    class _Ctor:
        def __init__(self,h,**kwargs): calls.append((h.shape,kwargs["max_iter"],kwargs["osd_method"]))
        def decode(self, syndrome): raise RuntimeError("decoder blew up")
    monkeypatch.setattr("importlib.metadata.version",lambda name:"2.4.1")
    monkeypatch.setitem(sys.modules,"ldpc",types.SimpleNamespace(BpOsdDecoder=_Ctor))
    check=_production_preflight(policy["candidates"][2],selected,np.zeros(256,dtype=np.uint16),"bw120",channel)
    assert check["status"] == "ok" and len(calls) == 20 and calls[:10] and calls[10:]
    result=_call(0,lambda *a,**k:_Ctor(*a,**k))
    assert result["outcome"]["status"] == "decoder_error"
    assert result["outcome"]["failure_reason"] == "decoder_exception"


def test_partial_attempt_public_replay_accepts_real_decoder_exception_prefix():
    _,channel,selection,h2,policy,seeds=_objects()
    class _Boom:
        def decode(self, syndrome): raise RuntimeError("boom")
    result=_call(0,lambda *a,**k:_Boom())
    assert result["outcome"]["status"] == "decoder_error"
    verified=verify_public_payload_v5(result["outcome"],result["events"],alice_symbols=np.zeros(256,dtype=np.uint16),pair_idx_sequence=np.arange(256),stratum="bw120",candidate_policy=policy["candidates"][0],policy_manifest=policy,selection_manifest=selection,channel_model=channel,h2_manifest=h2,locked_seeds=seeds)
    assert verified["status"] == "verified" and verified["event_count"] == 1


def test_private_bound_policy_cap_seam_is_precise(monkeypatch):
    import comparison_bench.src.comparison_bench.formal_ir.ldpc_v5 as v5
    original=v5._bound_policy
    def run_with(caps):
        def bound(*args,**kwargs):
            cid,selected,policy=original(*args,**kwargs); policy=dict(policy); policy["caps"]=caps; return cid,selected,policy
        monkeypatch.setattr(v5,"_bound_policy",bound)
        return _call(0,lambda *a,**k:_ZeroDecoder())
    calls=run_with({"wall_s":10.0,"decoder_calls":1,"events":32})
    assert calls["outcome"]["status"] == "aborted_resource_limit" and calls["outcome"]["failure_reason"] == "decoder_calls"
    assert calls["events"][-1]["event_type"] == "ABORT" and calls["events"][-1]["payload"]["cap"] == "decoder_calls"
    events=run_with({"wall_s":10.0,"decoder_calls":10,"events":1})
    assert events["outcome"]["status"] == "aborted_resource_limit" and events["outcome"]["failure_reason"] == "events"


@pytest.mark.parametrize("field",["pair_idx_sequence","candidate_policy","selection_manifest","channel_model","h2_manifest"])
def test_invalid_none_inputs_are_nonattempted(field):
    _,channel,selection,h2,policy,seeds=_objects()
    args=dict(pair_idx_sequence=np.arange(256),dataset_id="t",frame_id="0",stratum="bw120",candidate_policy=policy["candidates"][0],policy_manifest=policy,selection_manifest=selection,channel_model=channel,h2_manifest=h2,locked_seeds=seeds,_preflight_result={"status":"ok"},_decoder_factory=lambda *a,**k:_ZeroDecoder())
    args[field]=None
    result=run_ldpc_formal_v5(np.zeros(256,dtype=np.uint16),np.zeros(256,dtype=np.uint16),**args)
    assert result["outcome"]["status"] == "invalid_input" and result["outcome"]["attempted"] is False and result["events"] == []
