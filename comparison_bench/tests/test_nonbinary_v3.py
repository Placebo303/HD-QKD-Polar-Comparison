from __future__ import annotations
import inspect
from copy import deepcopy
import numpy as np
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v3 as v3
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_qspa import nonbinary_syndrome

def test_covered_codebook_reconstructs_and_preflights_every_prefix():
    manifest,mats=v3.build_nbldpc_v3_codebook();again,again_mats=v3.build_nbldpc_v3_codebook()
    assert manifest==again and mats==again_mats and manifest["accepted_salt"]==0
    assert v3.verify_nbldpc_v3_codebook(manifest,mats)["status"]=="ok"
    assert manifest["shift_direction"]=="col=8*b+((i+shift)%8)"
    assert "SHA256" in manifest["coefficient_derivation"] and "big" in manifest["coefficient_derivation"]
    assert manifest["coefficient_table"]==[list(row) for row in v3._coefficient_table(manifest["accepted_salt"])]
    for entry in manifest["ordered_entries"]:
        assert entry["rank"]==entry["check_count"] and entry["cycle_count"]==0
        assert min(entry["column_degrees"])>=2 and entry["pair_proxy_passed"]

def test_codebook_tamper_and_fixed_seed_fail_closed():
    manifest,mats=v3.build_nbldpc_v3_codebook(); bad=deepcopy(manifest);bad["accepted_salt"]=1
    assert v3.verify_nbldpc_v3_codebook(bad,mats)["status"]=="codebook_invalid"
    with pytest.raises(ValueError):v3.build_nbldpc_v3_codebook(construction_seed=1)
    for value in (True, 2026072803.0, "2026072803"):
        with pytest.raises(ValueError):v3.build_nbldpc_v3_codebook(construction_seed=value)
    for key,value in (("shift_direction","reversed"),("coefficient_derivation","forged"),("coefficient_table",[[1]])):
        forged=deepcopy(manifest);forged[key]=value
        assert v3.verify_nbldpc_v3_codebook(forged,mats)["status"]=="codebook_invalid"

def test_layered_decoder_is_public_only_and_bounded(monkeypatch):
    assert not any(x in n.lower() for n in inspect.signature(v3.decode_nbldpc_v3).parameters for x in ("alice","truth","callback"))
    manifest,mats=v3.build_nbldpc_v3_codebook(); zero=(0,)*64; syndrome=nonbinary_syndrome(mats[24],zero,GF2mField.create(1024))
    for candidate in v3.CANDIDATE_IDS:
        assert v3.decode_nbldpc_v3(candidate,zero,syndrome,manifest,mats,check_count=24,p=.2,max_iter=1)["status"]=="syndrome_consistent"
    assert v3.decode_nbldpc_v3(v3.CANDIDATE_IDS[0],zero,syndrome,manifest,mats,check_count=24,p=.2,max_iter=13)["status"]=="aborted_resource_limit"
    monkeypatch.setattr(v3,"_MAX_BYTES",1)
    assert v3.decode_nbldpc_v3(v3.CANDIDATE_IDS[0],zero,syndrome,manifest,mats,check_count=24,p=.2)["status"]=="aborted_resource_limit"

def test_q4_check_convolution_matches_bruteforce():
    import numpy as np
    field=GF2mField.create(4); messages=[np.array([.1,.2,.3,.4]),np.array([.4,.3,.2,.1]),np.array([.2,.1,.4,.3])]; coefficients=[2,3,1]; target=1; syndrome=3
    brute=np.array([sum(messages[0][a]*messages[2][b] for a in range(4) for b in range(4) if field.add(field.mul(coefficients[0],a),field.mul(coefficients[2],b))==field.add(syndrome,field.mul(coefficients[target],s))) for s in range(4)])
    brute=brute/brute.sum()
    assert np.allclose(v3._check_update_qspa(messages,coefficients,target,syndrome,field),brute)

def test_later_row_reads_the_message_written_by_an_earlier_row(monkeypatch):
    manifest,mats=v3.build_nbldpc_v3_codebook(); field=GF2mField.create(1024)
    bob=(0,)*64; syndrome=nonbinary_syndrome(mats[24],bob,field); original=v3._row_extrinsic; observations=[]
    def observed(prior, variable_edges, messages, current):
        if current[0] > 0:
            previous=[messages[e].copy() for e in variable_edges if e[0] < current[0]]
            if previous: observations.append(previous)
        return original(prior,variable_edges,messages,current)
    monkeypatch.setattr(v3,"_row_extrinsic",observed)
    result=v3.decode_nbldpc_v3(v3.CANDIDATE_IDS[0],bob,syndrome,manifest,mats,check_count=24,p=.2,max_iter=1)
    assert result["status"] == "syndrome_consistent"
    uniform=np.full(1024,1/1024)
    assert any(any(not np.allclose(message,uniform) for message in group) for group in observations)
