from __future__ import annotations
import json
import uuid
from copy import deepcopy
from pathlib import Path
import inspect
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v3_qualification as q
def _out(name):
    path=Path("workspace")/"nbv3_tests"/(name+"_"+uuid.uuid4().hex)
    path.parent.mkdir(parents=True,exist_ok=True);return path

def failed_runner(bob,syndrome,**kw):return {"status":"decode_failed","iterations":1}
def integrity_runner(bob,syndrome,**kw):return {"status":"decoder_error","iterations":1}

def test_plan_only_has_development_and_no_confirmation_material():
    out=_out("plan"); plan=q.create_plan(out,_test_only=True)
    assert {p.name for p in out.iterdir()}=={"pre_run_plan.json"}
    assert len(plan["frames"])==48 and {x["role"] for x in plan["frames"]}=={"development"}
    assert "confirmation_toeplitz_seeds" not in plan and not any("confirmation" in x["frame_id"] for x in plan["frames"])
    assert q.verify(out,_test_only=True)["verified"]

def test_nonready_null_selection_keeps_confirmation_unmaterialized():
    out=_out("stop");q.create_plan(out,_test_only=True);q.run(out,runner=integrity_runner,_test_only=True,clock=lambda:0.0)
    rows=q._rows(out/"formal_frame_outcomes.csv"); policy=json.loads((out/"formal_policy_manifest.json").read_text())
    assert len(rows)==192 and {x["qualification_role"] for x in rows}=={"development"}
    assert policy["selection"]=={"selected_policy":None,"selected_policy_sha256":None,"selection_key":None,"reason":"no_eligible_policy"}
    assert q.verify(out,verifier_runner=integrity_runner,_test_only=True)["run_status"]=="non_promoted_development"

def test_denominator_retained_and_tamper_rejected():
    out=_out("denominator");q.create_plan(out,_test_only=True);q.run(out,runner=failed_runner,_test_only=True,clock=lambda:0.0)
    assert all(x["denominator_included"]=="True" for x in q._rows(out/"formal_frame_outcomes.csv"))
    plan=json.loads((out/"pre_run_plan.json").read_text());plan["frames"].append({"role":"confirmation"});(out/"pre_run_plan.json").write_text(json.dumps(plan))
    try:q.verify(out,_test_only=True)
    except ValueError as exc:assert "confirmation leaked" in str(exc)
    else:raise AssertionError("tamper accepted")

def test_confirmation_is_created_only_after_ready_and_replays(monkeypatch):
    out=_out("ready")
    monkeypatch.setattr(q,"verify_nonbinary_symbols",lambda *a,**k:{"verified":True})
    def success(bob,syndrome,**kw):return {"status":"syndrome_consistent","decoded_symbols":tuple(bob),"iterations":1}
    q.create_plan(out,_test_only=True);q.run(out,runner=success,_test_only=True,clock=lambda:0.0)
    policy=json.loads((out/"formal_policy_manifest.json").read_text())
    assert policy["readiness"] and len(policy["confirmation_material"]["frames"])==64
    assert len(policy["confirmation_material"]["toeplitz_seeds"])==64
    assert q.verify(out,verifier_runner=success,_test_only=True)["promoted"]

def test_path_lock_no_overwrite_and_no_truth_cli():
    out=_out("locked");q.create_plan(out,_test_only=True)
    with pytest.raises(FileExistsError):q.create_plan(out,_test_only=True)
    with pytest.raises(ValueError):q.create_plan(_out("outside"))
    assert not any(word in name.lower() for name in inspect.signature(q.production_runner).parameters for word in ("alice","truth"))
    cli=(q._root()/"comparison_bench/src/comparison_bench/cli/run_formal_nonbinary_v3_qualification.py").read_text()
    assert "--output-dir" not in cli

def test_test_only_row_execution_requires_explicit_fake_runner(monkeypatch):
    def trap(*args,**kwargs):raise AssertionError("production runner called")
    out=_out("runner_trap_run");q.create_plan(out,_test_only=True);monkeypatch.setattr(q,"production_runner",trap)
    with pytest.raises(ValueError,match="explicit runner"):q.run(out,_test_only=True)
    assert {p.name for p in out.iterdir()}=={"pre_run_plan.json"}
    full=_out("runner_trap_verify");q.create_plan(full,_test_only=True);q.run(full,runner=integrity_runner,_test_only=True,clock=lambda:0.0)
    with pytest.raises(ValueError,match="explicit verifier_runner"):q.verify(full,_test_only=True)

def test_runner_exception_retains_invalid_package():
    out=_out("invalid");q.create_plan(out,_test_only=True)
    original=q._write_run
    def broken_write(*args,**kwargs):raise RuntimeError("fixture")
    q._write_run=broken_write
    with pytest.raises(RuntimeError):q.run(out,runner=failed_runner,_test_only=True,clock=lambda:0.0)
    q._write_run=original
    assert q.verify(out,verifier_runner=failed_runner,_test_only=True)["run_status"]=="invalid_run"

def test_partial_invalid_rows_replay_and_coherent_rehash_forgery_is_rejected(monkeypatch):
    out=_out("partial_invalid")
    monkeypatch.setattr(q,"verify_nonbinary_symbols",lambda *a,**k:{"verified":True})
    def success(bob,syndrome,**kw):return {"status":"syndrome_consistent","decoded_symbols":tuple(bob),"iterations":1}
    def fatal_after_five(count):
        if count==5:raise RuntimeError("test partial stop")
    class NonzeroClock:
        def __init__(self):self.value=0.0
        def __call__(self):
            self.value+=0.25
            return self.value
    q.create_plan(out,_test_only=True)
    with pytest.raises(RuntimeError,match="partial stop"):q.run(out,runner=success,_test_only=True,clock=NonzeroClock(),fatal_hook=fatal_after_five)
    assert len(q._rows(out/"formal_frame_outcomes.csv"))==5
    assert float(q._rows(out/"formal_frame_outcomes.csv")[0]["runtime_s"])>0
    assert q.verify(out,verifier_runner=success,_test_only=True)["run_status"]=="invalid_run"
    rows=q._rows(out/"formal_frame_outcomes.csv")
    events=[json.loads(x) for x in (out/"formal_transcript.jsonl").read_bytes().splitlines()]
    events[1]["payload"]["reason"]="forged"
    rows[0]["status"]="decode_failed"
    rows[0].update({k:str(v) for k,v in q.transcript_summary(events[:int(rows[0]["transcript_event_count"])]).items()})
    (out/"formal_frame_outcomes.csv").unlink()
    q._csv(out/"formal_frame_outcomes.csv",rows)
    (out/"formal_transcript.jsonl").write_bytes(b"".join(q.canonical_event(x) for x in events))
    manifest=json.loads((out/"formal_run_manifest.json").read_text());manifest["artifacts"]=q._artifact_hashes(out);(out/"formal_run_manifest.json").write_text(json.dumps(manifest))
    report=json.loads((out/"formal_qualification_report.json").read_text());report["formal_run_manifest_sha256"]=q._sha((out/"formal_run_manifest.json").read_bytes());(out/"formal_qualification_report.json").write_text(json.dumps(report))
    with pytest.raises(ValueError,match="invalid partial replay at 0"):q.verify(out,verifier_runner=success,_test_only=True)

def test_scoped_provenance_gates_every_field_but_allows_diagnostic_drift():
    plan=q.expected_plan(); gates=plan["provenance"]["gates"]
    assert set(gates)=={"source_sha256","cli_sha256","candidate_manifest_sha256","contract_sha256","environment","git_commit"}
    mutations=(("source_sha256",{}),("cli_sha256","x"),("candidate_manifest_sha256","x"),("contract_sha256","x"),("environment",{}),("git_commit","x"))
    for key,value in mutations:
        bad=deepcopy(plan);bad["provenance"]["gates"][key]=value
        with pytest.raises(ValueError,match="scoped provenance gates"):q._validate_plan(bad)
    diagnostic=deepcopy(plan);diagnostic["provenance"]["diagnostic"]["worktree_status_sha256"]="changed"
    assert q._validate_plan(diagnostic)

def test_complete_run_cap_aborts_remaining_confirmation_rows_and_replays(monkeypatch):
    out=_out("cap")
    monkeypatch.setattr(q,"verify_nonbinary_symbols",lambda *a,**k:{"verified":True})
    def success(bob,syndrome,**kw):return {"status":"syndrome_consistent","decoded_symbols":tuple(bob),"iterations":1}
    class Clock:
        def __init__(self):self.calls=0
        def __call__(self):
            self.calls+=1
            return 0.0 if self.calls<=193 else 10801.0
    q.create_plan(out,_test_only=True);q.run(out,runner=success,_test_only=True,clock=Clock())
    rows=q._rows(out/"formal_frame_outcomes.csv"); confirmation=[x for x in rows if x["qualification_role"]=="confirmation"]
    assert len(confirmation)==64 and all(x["status"]=="aborted_resource_limit" and x["denominator_included"]=="True" for x in confirmation)
    assert q.verify(out,verifier_runner=success,_test_only=True)["verified"]

def test_prior_seed_overlap_fails_before_directory_creation(monkeypatch):
    out=_out("prior_overlap");plan=q.expected_plan(); seed=next(iter(plan["development_toeplitz_seeds"].values()))["seed_id"]
    monkeypatch.setattr(q,"expected_plan",lambda:plan);monkeypatch.setattr(q,"_prior_seed_ids",lambda **kw:{seed})
    with pytest.raises(ValueError,match="prior seed overlap"):q.create_plan(out,_test_only=True)
    assert not out.exists()

def test_duplicate_development_seed_fails_before_directory_creation(monkeypatch):
    out=_out("duplicate_seed"); plan=q.expected_plan(); records=list(plan["development_toeplitz_seeds"])
    plan["development_toeplitz_seeds"][records[1]]=deepcopy(plan["development_toeplitz_seeds"][records[0]])
    monkeypatch.setattr(q,"expected_plan",lambda:plan)
    with pytest.raises(ValueError,match="development seed uniqueness"):q.create_plan(out,_test_only=True)
    assert not out.exists()

def test_identity_exclusion_covers_package_directory_and_other_package(monkeypatch):
    root=_out("identity_root"); base=root/"comparison_bench/outputs_comparison/formal_ir_methods"; own=base/"own"; other=base/"other"; own.mkdir(parents=True)
    plan=q.expected_plan(); provenance=plan["provenance"]
    own_plan=own/"pre_run_plan.json"; own_plan.write_text(json.dumps(plan))
    monkeypatch.setattr(q,"_root",lambda:root.resolve());monkeypatch.setattr(q,"_provenance",lambda:provenance)
    assert q._validate_plan(plan,plan_path=own_plan)
    confirmation=[q._frame(p,"confirmation",0) for p in q.PS]
    assert not any(q._identity_overlap(confirmation,exclude=own).values())
    other.mkdir();(other/"pre_run_plan.json").write_text(json.dumps(plan))
    with pytest.raises(ValueError,match="prior identity overlap"):q._validate_plan(plan,plan_path=own_plan)
    assert any(q._identity_overlap(confirmation,exclude=own).values())

def test_normal_package_shape_and_coherent_resigning_tamper_rejected():
    out=_out("normal_shape");q.create_plan(out,_test_only=True);q.run(out,runner=integrity_runner,_test_only=True,clock=lambda:0.0)
    assert q.verify(out,verifier_runner=integrity_runner,_test_only=True)["verified"]
    manifest_path=out/"formal_run_manifest.json";report_path=out/"formal_qualification_report.json"
    manifest=json.loads(manifest_path.read_text());report=json.loads(report_path.read_text())
    def resign():
        changed=json.loads(manifest_path.read_text());changed["artifacts"]=q._artifact_hashes(out);manifest_path.write_text(json.dumps(changed))
        changed_report=json.loads(report_path.read_text());changed_report["formal_run_manifest_sha256"]=q._sha(manifest_path.read_bytes());report_path.write_text(json.dumps(changed_report))
    extra=out/"unexpected.json";extra.write_text("{}")
    with pytest.raises(ValueError,match="normal artifact set"):q.verify(out,verifier_runner=integrity_runner,_test_only=True)
    extra.unlink()
    missing=out/"formal_candidate_manifest.json";held=out/"held_candidate.json";missing.rename(held)
    with pytest.raises(ValueError,match="normal artifact set"):q.verify(out,verifier_runner=integrity_runner,_test_only=True)
    held.rename(missing)
    for target,key,value,error in ((manifest_path,"run_id","forged","normal package identity"),(manifest_path,"run_status","completed","normal run status"),(report_path,"readiness",True,"normal run status"),(report_path,"run_status","completed","normal run status"),(manifest_path,"extra",1,"normal package shape"),(report_path,"extra",1,"normal package shape")):
        manifest_path.write_text(json.dumps(manifest));report_path.write_text(json.dumps(report))
        data=json.loads(target.read_text());data[key]=value;target.write_text(json.dumps(data));resign()
        with pytest.raises(ValueError,match=error):q.verify(out,verifier_runner=integrity_runner,_test_only=True)
    manifest_path.write_text(json.dumps(manifest));report_path.write_text(json.dumps(report))
    paths={name:out/name for name in q.ARTIFACTS};original={name:path.read_bytes() for name,path in paths.items()}
    def restore():
        for name,path in paths.items():path.write_bytes(original[name])
    def reject(error):
        resign()
        with pytest.raises(ValueError,match=error):q.verify(out,verifier_runner=integrity_runner,_test_only=True)
        restore()
    restore();paths["formal_candidate_manifest.json"].write_bytes(original["formal_candidate_manifest.json"]+b"\n")
    with pytest.raises(ValueError,match="artifact DAG"):q.verify(out,verifier_runner=integrity_runner,_test_only=True)
    restore()
    candidate=json.loads(paths["formal_candidate_manifest.json"].read_text());candidate["method"]="forged";paths["formal_candidate_manifest.json"].write_text(json.dumps(candidate));reject("candidate/codebook replay")
    codebook=json.loads(paths["formal_codebook_manifest.json"].read_text());codebook["canonical_sha256"]="forged";paths["formal_codebook_manifest.json"].write_text(json.dumps(codebook));reject("candidate/codebook replay")
    policy=json.loads(paths["formal_policy_manifest.json"].read_text());policy["selection"]["reason"]="forged";paths["formal_policy_manifest.json"].write_text(json.dumps(policy));reject("selection replay")
    changed_report=json.loads(paths["formal_qualification_report.json"].read_text());changed_report["promoted"]=True;paths["formal_qualification_report.json"].write_text(json.dumps(changed_report));reject("promotion gates")
    rows=q._rows(paths["formal_frame_outcomes.csv"]);rows[0],rows[1]=rows[1],rows[0];paths["formal_frame_outcomes.csv"].unlink();q._csv(paths["formal_frame_outcomes.csv"],rows);reject("development row order/count")
    paths["formal_transcript.jsonl"].write_bytes(original["formal_transcript.jsonl"]+original["formal_transcript.jsonl"].splitlines(keepends=True)[0]);reject("orphan transcript events")

def test_confirmation_seed_overlap_becomes_retained_invalid_run(monkeypatch):
    out=_out("confirm_overlap");q.create_plan(out,_test_only=True)
    plan=json.loads((out/"pre_run_plan.json").read_text()); collision=next(iter(plan["development_toeplitz_seeds"].values()))
    monkeypatch.setattr(q,"verify_nonbinary_symbols",lambda *a,**k:{"verified":True})
    monkeypatch.setattr(q,"materialize_seed_record",lambda bits:deepcopy(collision))
    def success(bob,syndrome,**kw):return {"status":"syndrome_consistent","decoded_symbols":tuple(bob),"iterations":1}
    with pytest.raises(RuntimeError,match="confirmation seed overlap"):q.run(out,runner=success,_test_only=True,clock=lambda:0.0)
    assert q.verify(out,verifier_runner=success,_test_only=True)["run_status"]=="invalid_run"

def test_coherent_rehash_cannot_hide_csv_or_selection_tamper():
    out2=_out("selection_tamper");q.create_plan(out2,_test_only=True);q.run(out2,runner=failed_runner,_test_only=True,clock=lambda:0.0)
    policy=json.loads((out2/"formal_policy_manifest.json").read_text());policy["selection"]["reason"]="forged";(out2/"formal_policy_manifest.json").write_text(json.dumps(policy))
    manifest=json.loads((out2/"formal_run_manifest.json").read_text());manifest["artifacts"]=q._artifact_hashes(out2);(out2/"formal_run_manifest.json").write_text(json.dumps(manifest))
    report=json.loads((out2/"formal_qualification_report.json").read_text());report["formal_run_manifest_sha256"]=q._sha((out2/"formal_run_manifest.json").read_bytes());(out2/"formal_qualification_report.json").write_text(json.dumps(report))
    with pytest.raises(ValueError,match="selection replay"):q.verify(out2,verifier_runner=failed_runner,_test_only=True)

def test_self_plan_seed_exclusion_and_other_plan_overlap(monkeypatch):
    out=_out("self");q.create_plan(out,_test_only=True);plan=json.loads((out/"pre_run_plan.json").read_text())
    assert q._validate_plan(plan,plan_path=out/"pre_run_plan.json")
    own=next(iter(plan["development_toeplitz_seeds"].values()))["seed_id"]
    monkeypatch.setattr(q,"_prior_seed_ids",lambda **kw:{own})
    with pytest.raises(ValueError,match="prior seed overlap"):q._validate_plan(plan,plan_path=out/"other_pre_run_plan.json")

def test_exact_tie_selects_lexically_lower_policy():
    grid=q.policy_grid(); rows={}
    for policy in grid:
        rows[policy["policy_sha256"]]=[{"frame_id":f"{q.METHOD}_q1024_p{int(p*100):02d}_development_{i:03d}","stratum_p":p,"status":"decode_failed","denominator_included":True,"key_dependent_disclosure_bits_total":1,"iterations":1} for p in q.PS for i in range(24)]
    selected=q._select(rows,grid)
    assert selected["selected_policy_sha256"]==min(x["policy_sha256"] for x in grid)
