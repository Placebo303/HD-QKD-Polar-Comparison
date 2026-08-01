from __future__ import annotations
import uuid
import json
from pathlib import Path
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v4_ir_qualification as q

def _out(name):
    root=Path("workspace")/"nbldpc_v4_ir_tests"/uuid.uuid4().hex/root_name(name)
    root.parent.mkdir(parents=True,exist_ok=True);return root
def root_name(name): return name
def failed(state,mats,stage): return {"status":"decode_failed","iterations":1}
def success(state,mats,stage): return {"status":"syndrome_consistent","iterations":1,"decoded_symbols":state.bob}

def test_plan_is_development_only_and_fake_runner_is_explicit():
    out=_out("plan"); plan=q.create_plan(out,_test_only=True)
    assert len(plan["frames"])==128 and "confirmation" not in str(plan["frames"])
    with pytest.raises(ValueError,match="explicit verifier_runner"): q.verify(out,_test_only=True)
    assert q.verify(out,verifier_runner=failed,_test_only=True)["plan_only"]
    with pytest.raises(ValueError,match="explicit runner"):q.run(out,_test_only=True)

def test_fake_development_run_replays_and_does_not_materialize_confirmation():
    out=_out("run");q.create_plan(out,_test_only=True); got=q.run(out,runner=failed,_test_only=True)
    assert got["run_status"]=="non_promoted_development"
    assert q.verify(out,verifier_runner=failed,_test_only=True)["verified"]

def test_forbidden_diagnostic_is_rejected():
    out=_out("diagnostic");q.create_plan(out,_test_only=True);q.run(out,runner=failed,_test_only=True)
    path=out/"formal_candidate_manifest.json";data=__import__("json").loads(path.read_text());data["posterior_summary"]="no";path.unlink();path.write_text(__import__("json").dumps(data))
    with pytest.raises(ValueError):q.verify(out,verifier_runner=failed,_test_only=True)

def test_ready_materialization_uses_real_tag_comparison(monkeypatch):
    original=q._frame
    def noiseless(p,role,index):
        row=original(p,role,index);row["alice"]=[0]*64;row["bob"]=[0]*64;return row
    monkeypatch.setattr(q,"_frame",noiseless)
    out=_out("ready");q.create_plan(out,_test_only=True);got=q.run(out,runner=success,_test_only=True)
    assert got["readiness"] and got["promoted"]
    doc=__import__("json").loads((out/"formal_policy_manifest.json").read_text())
    assert len(doc["confirmation_material"]["frames"])==256
    assert q.verify(out,verifier_runner=success,_test_only=True)["promoted"]

def test_strict_replay_uses_verifier_runner_and_rejects_event_tamper(monkeypatch):
    original=q._frame
    def noiseless(p,role,index):
        row=original(p,role,index);row["alice"]=[0]*64;row["bob"]=[0]*64;return row
    monkeypatch.setattr(q,"_frame",noiseless)
    out=_out("strict");q.create_plan(out,_test_only=True);q.run(out,runner=success,_test_only=True)
    with pytest.raises(ValueError,match="semantic replay"):q.verify(out,verifier_runner=failed,_test_only=True)
    events=(out/"formal_transcript.jsonl").read_text().splitlines();first=__import__("json").loads(events[0]);first["payload"]["syndrome"][0]=1;events[0]=__import__("json").dumps(first)
    path=out/"formal_transcript.jsonl";path.unlink();path.write_text("\n".join(events)+"\n")
    manifest=__import__("json").loads((out/"formal_run_manifest.json").read_text());manifest["artifacts"]=q._artifact_hashes(out);mp=out/"formal_run_manifest.json";mp.write_text(__import__("json").dumps(manifest));rp=out/"formal_qualification_report.json";report=__import__("json").loads(rp.read_text());report["formal_run_manifest_sha256"]=q._sha(mp.read_bytes());rp.write_text(__import__("json").dumps(report))
    with pytest.raises(ValueError,match="semantic replay"):q.verify(out,verifier_runner=success,_test_only=True)

def _resign(out):
    manifest_path=out/"formal_run_manifest.json"; report_path=out/"formal_qualification_report.json"
    manifest=json.loads(manifest_path.read_text());manifest["artifacts"]=q._artifact_hashes(out);manifest_path.write_text(json.dumps(manifest))
    report=json.loads(report_path.read_text());report["formal_run_manifest_sha256"]=q._sha(manifest_path.read_bytes());report_path.write_text(json.dumps(report))

def test_fatal_hook_retains_partial_rows_and_strictly_replays():
    out=_out("partial")
    q.create_plan(out,_test_only=True)
    def hook(count):
        if count==5: raise RuntimeError("fatal hook")
    with pytest.raises(RuntimeError,match="fatal hook"):
        q.run(out,runner=failed,_test_only=True,fatal_hook=hook)
    assert len(q._rows(out/"formal_frame_outcomes.csv"))==5
    assert {p.name for p in out.iterdir()}==set(q.ARTIFACTS)
    assert q.verify(out,verifier_runner=failed,_test_only=True)["run_status"]=="invalid_run"
    rows=q._rows(out/"formal_frame_outcomes.csv");rows[0]["status"]="verify_failed"; (out/"formal_frame_outcomes.csv").unlink();q._csv(out/"formal_frame_outcomes.csv",rows);_resign(out)
    with pytest.raises(ValueError,match="invalid partial replay"):
        q.verify(out,verifier_runner=failed,_test_only=True)

def test_semantic_tamper_matrix_rejects_even_when_rehashed(monkeypatch):
    original=q._frame
    def noiseless(p,role,index):
        row=original(p,role,index);row["alice"]=[0]*64;row["bob"]=[0]*64;return row
    monkeypatch.setattr(q,"_frame",noiseless)
    # Separate packages avoid interactions between independent corruptions.
    cases=(("candidate",lambda out: (lambda x: (x.update(method="forged"),x)[1])(json.loads((out/"formal_candidate_manifest.json").read_text()))),)
    for name,_ in cases:
        out=_out(name);q.create_plan(out,_test_only=True);q.run(out,runner=success,_test_only=True)
        path=out/"formal_candidate_manifest.json";data=json.loads(path.read_text());data["method"]="forged";path.write_text(json.dumps(data));_resign(out)
        with pytest.raises(ValueError,match="candidate/codebook replay"):q.verify(out,verifier_runner=success,_test_only=True)

def test_rejects_reserved_decision_or_orphan_event_after_coherent_rehash(monkeypatch):
    original=q._frame
    def noiseless(p,role,index):
        row=original(p,role,index);row["alice"]=[0]*64;row["bob"]=[0]*64;return row
    monkeypatch.setattr(q,"_frame",noiseless)
    out=_out("decision");q.create_plan(out,_test_only=True);q.run(out,runner=success,_test_only=True)
    events=[json.loads(line) for line in (out/"formal_transcript.jsonl").read_bytes().splitlines()]
    next(event for event in events if event["event_type"]=="STAGE_DECISION_STAGE1")["payload"]["reason"]="11"
    (out/"formal_transcript.jsonl").write_bytes(b"".join(q.canonical_event(event) for event in events));_resign(out)
    with pytest.raises(ValueError,match="semantic replay"):q.verify(out,verifier_runner=success,_test_only=True)

def test_rehashed_transcript_and_selection_matrix_is_semantically_rejected():
    # A failed IR lane still emits a stage-2 suffix and both decisions, so this
    # compact fake package covers disclosure and lineage without production work.
    out=_out("matrix");q.create_plan(out,_test_only=True);q.run(out,runner=failed,_test_only=True)
    events=[json.loads(line) for line in (out/"formal_transcript.jsonl").read_bytes().splitlines()]
    suffix=next(event for event in events if event["event_type"]=="SYNDROME_EXTENSION")
    suffix["payload"]["syndrome"][0]^=1
    (out/"formal_transcript.jsonl").write_bytes(b"".join(q.canonical_event(event) for event in events));_resign(out)
    with pytest.raises(ValueError,match="semantic replay"):q.verify(out,verifier_runner=failed,_test_only=True)

def test_fake_runner_does_not_fall_back_to_production(monkeypatch):
    out=_out("trap");q.create_plan(out,_test_only=True)
    monkeypatch.setattr(q,"production_runner",lambda *_: (_ for _ in ()).throw(AssertionError("production")))
    assert q.run(out,runner=failed,_test_only=True)["run_status"]=="non_promoted_development"
    assert q.verify(out,verifier_runner=failed,_test_only=True)["verified"]

@pytest.mark.parametrize("stop,runner",[(1,failed),(383,failed),(384,failed),(385,success)])
def test_invalid_boundaries_replay_without_empty_forgery(monkeypatch,stop,runner):
    if runner is success:
        original=q._frame
        def noiseless(p,role,index):
            row=original(p,role,index);row["alice"]=[0]*64;row["bob"]=[0]*64;return row
        monkeypatch.setattr(q,"_frame",noiseless)
    out=_out(f"boundary_{stop}");q.create_plan(out,_test_only=True)
    def hook(count):
        if count==stop:raise RuntimeError(f"stop {stop}")
    with pytest.raises(RuntimeError):q.run(out,runner=runner,_test_only=True,fatal_hook=hook)
    assert q.verify(out,verifier_runner=runner,_test_only=True)["run_status"]=="invalid_run"
    if stop==1:
        # Coherent rehash cannot turn retained evidence into a sentinel package.
        (out/"formal_frame_outcomes.csv").unlink();q._csv(out/"formal_frame_outcomes.csv",[])
        (out/"formal_transcript.jsonl").write_bytes(b"")
        _resign(out)
        with pytest.raises(ValueError):q.verify(out,verifier_runner=runner,_test_only=True)

def test_production_api_rejects_injected_runner():
    with pytest.raises(ValueError,match="production run"):q.run(Path("unused"),runner=failed,_test_only=False)
    with pytest.raises(ValueError,match="production verify"):q.verify(Path("unused"),verifier_runner=failed,_test_only=False)

def test_package_directory_self_exclusion_and_predecode_identity_abort(monkeypatch):
    # The helper distinguishes a plan-file exclusion from a package-directory
    # exclusion; the latter is required once formal artifacts are beneath a
    # formal_ir_methods/<run> package.
    root=_out("formal_ir_methods")/"formal_ir_methods"/"run"; nested=root/"formal_policy_manifest.json";nested.parent.mkdir(parents=True);nested.write_text("{}")
    assert q._excluded(nested,root) and not q._excluded(nested,root/"pre_run_plan.json")
    original=q._frame
    def noiseless(p,role,index):
        row=original(p,role,index);row["alice"]=[0]*64;row["bob"]=[0]*64;return row
    monkeypatch.setattr(q,"_frame",noiseless)
    calls={"n":0}; original_overlap=q._identity_overlap
    def overlap(frames,**kwargs):
        calls["n"]+=1
        return {"roots":["forged"],"frame_ids":[],"array_sha256":[],"atomic_keys":[]} if calls["n"]==4 else original_overlap(frames,**kwargs)
    monkeypatch.setattr(q,"_identity_overlap",overlap)
    out=_out("predecode_abort");q.create_plan(out,_test_only=True)
    with pytest.raises(ValueError,match="confirmation identity isolation"):q.run(out,runner=success,_test_only=True)
    rows=q._rows(out/"formal_frame_outcomes.csv")
    assert len(rows)==384 and not any(row["qualification_role"]=="confirmation" for row in rows)
