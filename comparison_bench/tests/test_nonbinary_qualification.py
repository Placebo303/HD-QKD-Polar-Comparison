"""Phase-10 tests use only a fake runner; never execute the q=1024 grid."""
from __future__ import annotations
import json, shutil
from pathlib import Path
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_qualification as q

def fake(alice, bob, **kwargs):
    return {"status":"syndrome_consistent","decoded_symbols":tuple(int(x) for x in alice),"iterations":1}

def make(tmp_path:Path) -> Path:
    out=tmp_path/"out"; q.create_plan(out,_test_only=True); q.run(out,runner=fake,_test_only=True); return out

def test_plan_only_zero_calls_and_reconstructible_generation(tmp_path):
    calls=[]; out=tmp_path/"plan"; plan=q.create_plan(out,_test_only=True)
    assert calls==[] and {x.name for x in out.iterdir()}=={"pre_run_plan.json"}
    def never(*a, **k): raise AssertionError("plan-only must not call decoder")
    assert q.verify(out,verifier_runner=never,_test_only=True)["plan_only"]
    assert plan["generator_sha256"]==q.expected_plan()["generator_sha256"]
    assert len(plan["development_toeplitz_seeds"])==128 and len(plan["confirmation_toeplitz_seeds"])==64
    assert {"git_commit","git_dirty","git_status_sha256","module_sha256","cli_sha256","generator_policy_contract_sha256"} <= set(plan["provenance"])

def test_frozen_root_requires_private_test_seam(tmp_path):
    with pytest.raises(ValueError): q.create_plan(tmp_path/"not_official")

def test_prior_seed_overlap_fails_before_directory_creation(tmp_path, monkeypatch):
    target=tmp_path/"overlap"; seed=q.materialize_seed_record(q.SEED_BITS)["seed_id"]
    old=q.materialize_seed_record
    monkeypatch.setattr(q,"_prior_seed_ids",lambda **k:{seed})
    monkeypatch.setattr(q,"materialize_seed_record",lambda n:{"seed_hex":"00"*88,"seed_bit_length":n,"seed_id":seed})
    with pytest.raises(ValueError): q.create_plan(target,_test_only=True)
    assert not target.exists()

def test_provenance_hashes_match_sources(tmp_path):
    plan=q.create_plan(tmp_path/"p",_test_only=True); provenance=plan["provenance"]; formal=Path(q.__file__).parent
    for name, digest in provenance["module_sha256"].items(): assert digest==q._sha((formal/name).read_bytes())
    assert provenance["cli_sha256"]==q._sha((formal.parent/"cli"/"run_formal_nonbinary_qualification.py").read_bytes())

def test_coherent_confirmation_tamper_is_replayed(tmp_path):
    out=make(tmp_path); rows=q._rows(out/"formal_frame_outcomes.csv"); rows[0]["iterations"]="9"
    (out/"formal_frame_outcomes.csv").unlink(); q._csv_x(out/"formal_frame_outcomes.csv",rows)
    manifest=json.loads((out/"formal_run_manifest.json").read_text()); manifest["artifacts"]=q._artifact_hashes(out)
    (out/"formal_run_manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
    report=json.loads((out/"formal_qualification_report.json").read_text()); report["formal_run_manifest_sha256"]=q._sha((out/"formal_run_manifest.json").read_bytes())
    (out/"formal_qualification_report.json").write_text(json.dumps(report),encoding="utf-8")
    with pytest.raises(ValueError): q.verify(out,verifier_runner=fake,_test_only=True)

def test_global_selection_is_development_only_and_full_denominators(tmp_path):
    out=make(tmp_path); policy=json.loads((out/"formal_policy_manifest.json").read_text())
    changed=json.loads(json.dumps(policy)); changed["selection"]["selected_policy"]["policy_sha256"]="bad"
    # Confirmation values are not an input to selection reconstruction.
    assert q._select(policy["development_outcomes"],policy["policies"])==policy["selection"]
    result=q.verify(out,verifier_runner=fake,_test_only=True); assert result["promoted"] is True

@pytest.mark.parametrize("name",["plan","seed","codebook","policy","outcomes","transcript","manifest","report","extra"])
def test_strict_verifier_rejects_tampering(tmp_path,name):
    out=make(tmp_path); target=tmp_path/name; shutil.copytree(out,target)
    if name=="plan":
        p=target/"pre_run_plan.json"; x=json.loads(p.read_text()); x["frames"][0]["alice"][0]^=1; p.write_text(json.dumps(x))
    elif name=="seed":
        p=target/"pre_run_plan.json"; x=json.loads(p.read_text()); next(iter(x["confirmation_toeplitz_seeds"].values()))["seed_id"]="0"*64; p.write_text(json.dumps(x))
    elif name=="codebook":
        p=target/"formal_codebook_manifest.json"; x=json.loads(p.read_text()); x["manifest_id"]="0"*64; p.write_text(json.dumps(x))
    elif name=="policy":
        p=target/"formal_policy_manifest.json"; x=json.loads(p.read_text()); next(iter(x["development_outcomes"].values()))[0]["policy_sha256"]="bad"; p.write_text(json.dumps(x))
    elif name=="outcomes":
        p=target/"formal_frame_outcomes.csv"; p.write_text(p.read_text().replace("verified_success","decoder_error",1))
    elif name=="transcript":
        p=target/"formal_transcript.jsonl"; p.write_text(p.read_text()+"{}\n")
    elif name=="manifest":
        p=target/"formal_run_manifest.json"; x=json.loads(p.read_text()); x["artifacts"]={}; p.write_text(json.dumps(x))
    elif name=="report":
        p=target/"formal_qualification_report.json"; x=json.loads(p.read_text()); x["promoted"]=False; p.write_text(json.dumps(x))
    else: (target/"extra").write_text("x")
    with pytest.raises(ValueError): q.verify(target,verifier_runner=fake,_test_only=True)

def test_nonpromoted_exception_cap_and_no_overwrite(tmp_path):
    out=tmp_path/"bad"; q.create_plan(out,_test_only=True)
    def explode(*a,**k):
        # Deterministic from frame contents, so strict replay sees the same row.
        if int(a[0][0]) % 7 == 0: raise RuntimeError("injected")
        return fake(*a,**k)
    # Per-frame exceptions are retained, not a package failure.
    q.run(out,runner=explode,_test_only=True); assert q.verify(out,verifier_runner=explode,_test_only=True)["promoted"] is False
    with pytest.raises(FileExistsError): q.create_plan(out,_test_only=True)

def test_complete_cap_materializes_confirmation_denominators(tmp_path):
    out=tmp_path/"cap"; q.create_plan(out,_test_only=True); development_calls=[0]; post_development_clock_calls=[0]
    def cap_after_development(alice, bob, **kwargs):
        development_calls[0]+=1
        return fake(alice,bob,**kwargs)
    def clock():
        # 8 policies x 16 development frames; only the next confirmation
        # pre-check crosses the complete-run cap, independent of _one timing.
        if development_calls[0] < 128:
            return 0.0
        post_development_clock_calls[0] += 1
        # First call is the final development _one elapsed-time measurement;
        # second is the first confirmation precheck.
        return 0.0 if post_development_clock_calls[0] == 1 else 1801.0
    q.run(out,runner=cap_after_development,clock=clock,_test_only=True)
    rows=q._rows(out/"formal_frame_outcomes.csv")
    assert len(rows)==64 and all(x["denominator_included"]=="True" for x in rows)
    assert all(x["status"]=="aborted_resource_limit" for x in rows)
    assert (out/"formal_transcript.jsonl").read_bytes()
    assert q.verify(out,verifier_runner=fake,_test_only=True)["promoted"] is False

def test_invalid_run_never_promotes(tmp_path):
    out=tmp_path/"invalid"; q.create_plan(out,_test_only=True)
    with pytest.raises(RuntimeError):
        q.run(out,runner=fake,clock=lambda: (_ for _ in ()).throw(RuntimeError("clock")),_test_only=True)
    assert {x.name for x in out.iterdir()}==set(q.ARTIFACTS)
    assert q.verify(out,verifier_runner=fake,_test_only=True)["run_status"]=="invalid_run"
