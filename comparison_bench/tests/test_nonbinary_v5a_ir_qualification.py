from __future__ import annotations
import json
import uuid
from pathlib import Path
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v5_runtime as runtime
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v5a_ir_qualification as q

def _out(name):
    root = Path("workspace") / "nbldpc_v5a_ir_tests" / uuid.uuid4().hex / name
    root.parent.mkdir(parents=True, exist_ok=True)
    return root

def failed(state, mats, stage): return {"status": "decode_failed", "iterations": 1}
def success(state, mats, stage):
    return {"status": "syndrome_consistent", "iterations": 1, "decoded_symbols": state.bob}

def _noiseless(runtime_module, monkeypatch):
    original = runtime_module._frame
    def noiseless(config, p, role, index):
        row = original(config, p, role, index)
        row["alice"] = [0] * 64
        row["bob"] = [0] * 64
        return row
    monkeypatch.setattr(runtime_module, "_frame", noiseless)

def test_plan_is_development_only_and_fake_runner_is_explicit():
    out = _out("plan")
    plan = q.create_plan(out, _test_only=True)
    assert len(plan["frames"]) == 128 and "confirmation" not in str(plan["frames"])
    assert len(plan["development_toeplitz_seeds"]) == 576  # ir48: 2 slots, ir56: 2+3 slots x 64 x 2 strata
    assert not any(plan["identity_overlap"].values())
    with pytest.raises(ValueError, match="explicit verifier_runner"):
        q.verify(out, _test_only=True)
    assert q.verify(out, verifier_runner=failed, _test_only=True)["plan_only"]
    with pytest.raises(ValueError, match="explicit runner"):
        q.run(out, _test_only=True)

def test_fake_development_run_replays_and_does_not_materialize_confirmation():
    out = _out("run")
    q.create_plan(out, _test_only=True)
    got = q.run(out, runner=failed, _test_only=True)
    assert got["run_status"] == "non_promoted_development"
    assert q.verify(out, verifier_runner=failed, _test_only=True)["verified"]

def test_three_level_failed_lane_emits_full_transcript():
    out = _out("three_level")
    q.create_plan(out, _test_only=True)
    q.run(out, runner=failed, _test_only=True)
    rows = runtime._rows(out / "formal_frame_outcomes.csv")
    assert len(rows) == 256
    assert sum(row["status"] == "decode_failed" for row in rows) == 256
    # ir56 p=.30 rows (indices 64..127 in policy order) run exactly 3 stages.
    ir56_p30 = [r for r in rows if r["policy_id"] == "nbldpc_v5a_ir56" and r["stratum_p"] == "0.3"]
    assert all(r["extension_used"] == "True" and r["final_prefix"] == "56" and r["stage3_iterations"] == "1"
               for r in ir56_p30)
    ir48_p30 = [r for r in rows if r["policy_id"] == "nbldpc_v5a_ir48" and r["stratum_p"] == "0.3"]
    assert all(r["final_prefix"] == "48" and r["stage3_iterations"] == "0" for r in ir48_p30)
    assert all(r["verification_attempts"] == "0" for r in rows)
    events = [json.loads(line) for line in (out / "formal_transcript.jsonl").read_bytes().splitlines()]
    assert len(events) == 1728  # 64 x (6 + 9 + 6 + 6) events, zero verification tags
    assert sum(e["event_type"] == "SYNDROME_EXTENSION" for e in events) == 320
    assert sum(e["event_type"] == "DECODER_STAGE3" for e in events) == 64
    assert sum(e["event_type"] == "VERIFICATION_TAG_STAGE1" for e in events) == 0
    assert q.verify(out, verifier_runner=failed, _test_only=True)["verified"]

def test_forbidden_diagnostic_is_rejected():
    out = _out("diagnostic")
    q.create_plan(out, _test_only=True)
    q.run(out, runner=failed, _test_only=True)
    path = out / "formal_candidate_manifest.json"
    data = json.loads(path.read_text())
    data["posterior_summary"] = "no"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        q.verify(out, verifier_runner=failed, _test_only=True)

def test_ready_materialization_uses_real_tag_comparison(monkeypatch):
    _noiseless(runtime, monkeypatch)
    out = _out("ready")
    q.create_plan(out, _test_only=True)
    got = q.run(out, runner=success, _test_only=True)
    assert got["readiness"] and got["promoted"]
    doc = json.loads((out / "formal_policy_manifest.json").read_text())
    assert len(doc["confirmation_material"]["frames"]) == 256
    assert len(runtime._rows(out / "formal_frame_outcomes.csv")) == 512
    assert q.verify(out, verifier_runner=success, _test_only=True)["promoted"]

def test_selection_prefers_verified_candidate_policy(monkeypatch):
    _noiseless(runtime, monkeypatch)
    def selective(state, mats, stage):
        return success(state, mats, stage) if state.policy_id == "nbldpc_v5a_ir56" else failed(state, mats, stage)
    out = _out("selective")
    q.create_plan(out, _test_only=True)
    q.run(out, runner=selective, _test_only=True)
    doc = json.loads((out / "formal_policy_manifest.json").read_text())
    assert doc["selection"]["selected_policy"]["policy_id"] == "nbldpc_v5a_ir56"
    assert doc["selection"]["reason"] == "development_rank"
    assert q.verify(out, verifier_runner=selective, _test_only=True)["promoted"]

def test_strict_replay_uses_verifier_runner_and_rejects_event_tamper(monkeypatch):
    _noiseless(runtime, monkeypatch)
    out = _out("strict")
    q.create_plan(out, _test_only=True)
    q.run(out, runner=success, _test_only=True)
    with pytest.raises(ValueError, match="semantic replay"):
        q.verify(out, verifier_runner=failed, _test_only=True)
    events = (out / "formal_transcript.jsonl").read_text().splitlines()
    first = json.loads(events[0])
    first["payload"]["syndrome"][0] = 1
    events[0] = json.dumps(first)
    path = out / "formal_transcript.jsonl"
    path.unlink()
    path.write_text("\n".join(events) + "\n")
    _resign(out)
    with pytest.raises(ValueError, match="semantic replay"):
        q.verify(out, verifier_runner=success, _test_only=True)

def _resign(out):
    manifest_path = out / "formal_run_manifest.json"
    report_path = out / "formal_qualification_report.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["artifacts"] = runtime._artifact_hashes(out)
    manifest_path.write_text(json.dumps(manifest))
    report = json.loads(report_path.read_text())
    report["formal_run_manifest_sha256"] = runtime._sha(manifest_path.read_bytes())
    report_path.write_text(json.dumps(report))

def test_fatal_hook_retains_partial_rows_and_strictly_replays():
    out = _out("partial")
    q.create_plan(out, _test_only=True)
    def hook(count):
        if count == 5:
            raise RuntimeError("fatal hook")
    with pytest.raises(RuntimeError, match="fatal hook"):
        q.run(out, runner=failed, _test_only=True, fatal_hook=hook)
    assert len(runtime._rows(out / "formal_frame_outcomes.csv")) == 5
    assert {p.name for p in out.iterdir()} == set(runtime.ARTIFACTS)
    assert q.verify(out, verifier_runner=failed, _test_only=True)["run_status"] == "invalid_run"
    rows = runtime._rows(out / "formal_frame_outcomes.csv")
    rows[0]["status"] = "verify_failed"
    (out / "formal_frame_outcomes.csv").unlink()
    runtime._csv(out / "formal_frame_outcomes.csv", rows)
    _resign(out)
    with pytest.raises(ValueError, match="invalid partial replay"):
        q.verify(out, verifier_runner=failed, _test_only=True)

def test_semantic_tamper_matrix_rejects_even_when_rehashed(monkeypatch):
    _noiseless(runtime, monkeypatch)
    out = _out("candidate")
    q.create_plan(out, _test_only=True)
    q.run(out, runner=success, _test_only=True)
    path = out / "formal_candidate_manifest.json"
    data = json.loads(path.read_text())
    data["method"] = "forged"
    path.write_text(json.dumps(data))
    _resign(out)
    with pytest.raises(ValueError, match="candidate/codebook replay"):
        q.verify(out, verifier_runner=success, _test_only=True)

def test_rejects_reserved_decision_after_coherent_rehash(monkeypatch):
    _noiseless(runtime, monkeypatch)
    out = _out("decision")
    q.create_plan(out, _test_only=True)
    q.run(out, runner=success, _test_only=True)
    events = [json.loads(line) for line in (out / "formal_transcript.jsonl").read_bytes().splitlines()]
    next(e for e in events if e["event_type"] == "STAGE_DECISION_STAGE1")["payload"]["reason"] = "11"
    (out / "formal_transcript.jsonl").write_bytes(b"".join(runtime.canonical_event(e) for e in events))
    _resign(out)
    with pytest.raises(ValueError, match="semantic replay"):
        q.verify(out, verifier_runner=success, _test_only=True)

def test_rehashed_transcript_and_selection_matrix_is_semantically_rejected():
    out = _out("matrix")
    q.create_plan(out, _test_only=True)
    q.run(out, runner=failed, _test_only=True)
    events = [json.loads(line) for line in (out / "formal_transcript.jsonl").read_bytes().splitlines()]
    suffix = next(e for e in events if e["event_type"] == "SYNDROME_EXTENSION")
    suffix["payload"]["syndrome"][0] ^= 1
    (out / "formal_transcript.jsonl").write_bytes(b"".join(runtime.canonical_event(e) for e in events))
    _resign(out)
    with pytest.raises(ValueError, match="semantic replay"):
        q.verify(out, verifier_runner=failed, _test_only=True)

def test_fake_runner_does_not_fall_back_to_production(monkeypatch):
    from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v5a_multistage as core
    out = _out("trap")
    q.create_plan(out, _test_only=True)
    def trap(*args, **kwargs):
        raise AssertionError("production")
    monkeypatch.setattr(core, "production_runner", trap)
    assert q.run(out, runner=failed, _test_only=True)["run_status"] == "non_promoted_development"
    assert q.verify(out, verifier_runner=failed, _test_only=True)["verified"]

@pytest.mark.parametrize("stop,runner", [(1, failed), (255, failed), (256, failed), (257, success)])
def test_invalid_boundaries_replay_without_empty_forgery(monkeypatch, stop, runner):
    if runner is success:
        _noiseless(runtime, monkeypatch)
    out = _out(f"boundary_{stop}")
    q.create_plan(out, _test_only=True)
    def hook(count):
        if count == stop:
            raise RuntimeError(f"stop {stop}")
    with pytest.raises(RuntimeError):
        q.run(out, runner=runner, _test_only=True, fatal_hook=hook)
    assert q.verify(out, verifier_runner=runner, _test_only=True)["run_status"] == "invalid_run"
    if stop == 1:
        (out / "formal_frame_outcomes.csv").unlink()
        runtime._csv(out / "formal_frame_outcomes.csv", [])
        (out / "formal_transcript.jsonl").write_bytes(b"")
        _resign(out)
        with pytest.raises(ValueError):
            q.verify(out, verifier_runner=runner, _test_only=True)

def test_run_requires_plan_only_directory():
    out = _out("twice")
    q.create_plan(out, _test_only=True)
    q.run(out, runner=failed, _test_only=True)
    with pytest.raises(ValueError, match="plan-only"):
        q.run(out, runner=failed, _test_only=True)

def test_production_api_rejects_injected_runner():
    with pytest.raises(ValueError, match="production run"):
        q.run(Path("unused"), runner=failed, _test_only=False)
    with pytest.raises(ValueError, match="production verify"):
        q.verify(Path("unused"), verifier_runner=failed, _test_only=False)

def test_package_directory_self_exclusion_and_predecode_identity_abort(monkeypatch):
    root = _out("formal_ir_methods") / "formal_ir_methods" / "run"
    nested = root / "formal_policy_manifest.json"
    nested.parent.mkdir(parents=True)
    nested.write_text("{}")
    assert runtime._excluded(nested, root)
    assert not runtime._excluded(nested, root / "pre_run_plan.json")
    _noiseless(runtime, monkeypatch)
    calls = {"n": 0}
    original_overlap = runtime._identity_overlap
    def overlap(config, frames, **kwargs):
        calls["n"] += 1
        if calls["n"] == 4:
            return {"roots": ["forged"], "frame_ids": [], "array_sha256": [], "atomic_keys": []}
        return original_overlap(config, frames, **kwargs)
    monkeypatch.setattr(runtime, "_identity_overlap", overlap)
    out = _out("predecode_abort")
    q.create_plan(out, _test_only=True)
    with pytest.raises(ValueError, match="confirmation identity isolation"):
        q.run(out, runner=success, _test_only=True)
    rows = runtime._rows(out / "formal_frame_outcomes.csv")
    assert len(rows) == 256
    assert not any(row["qualification_role"] == "confirmation" for row in rows)
