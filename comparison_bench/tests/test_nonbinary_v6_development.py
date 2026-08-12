"""NBLDPC6 development harness acceptance: development-only plans, explicit
fake-runner guards, one complete fake package with strict read-only replay,
invalid-run retention, and the layered tamper matrix (A05/A06/A07/A08)."""
from __future__ import annotations
import json
import uuid
from dataclasses import replace
from pathlib import Path
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v6_development as lane
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v6_long as v6_long


def _out(name):
    root = Path("workspace") / "nbldpc_v6_engineering" / uuid.uuid4().hex / name
    root.parent.mkdir(parents=True, exist_ok=True)
    return root


def _config(frames=8, source_files=lane._SRC):
    return lane.DevelopmentConfig(
        run_id="nbldpc_v6_development_engineering_test", canonical_schema="NBLDPC6DEV",
        method=lane.METHOD, q=1024, n=1024, ps=(.20, .30),
        roots={("development", .20): 202608029000, ("development", .30): 202608029100},
        caps=lane.CAPS, seed_bits=lane.SEED_BITS, development_frames=frames,
        source_files=tuple(source_files), contract=lane.CONTRACT)


TEST_CONFIG = _config()


def failed(bob, syndrome, manifest, matrices, *, check_count, p):
    return {"status": "decode_failed", "iterations": 1}


def success(bob, syndrome, manifest, matrices, *, check_count, p):
    return {"status": "syndrome_consistent", "iterations": 1, "decoded_symbols": tuple(bob)}


def wrong(bob, syndrome, manifest, matrices, *, check_count, p):
    return {"status": "syndrome_consistent", "iterations": 1,
            "decoded_symbols": tuple((int(x) + 1) % 1024 for x in bob)}


def _noiseless(monkeypatch):
    original = lane._frame
    def noiseless(config, p, index):
        row = original(config, p, index)
        row["alice"] = [0] * 1024
        row["bob"] = [0] * 1024
        return row
    monkeypatch.setattr(lane, "_frame", noiseless)


def _resign(out):
    manifest_path = out / "formal_run_manifest.json"
    report_path = out / "formal_qualification_report.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["artifacts"] = lane._artifact_hashes(out)
    manifest_path.write_text(json.dumps(manifest))
    report = json.loads(report_path.read_text())
    report["formal_run_manifest_sha256"] = lane._sha(manifest_path.read_bytes())
    report_path.write_text(json.dumps(report))


# ---------------------------------------------------------------- guards (A06)

def test_plan_is_development_only_and_fake_runner_is_explicit():
    out = _out("plan")
    plan = lane.create_plan(out, config=TEST_CONFIG, _test_only=True)
    assert len(plan["frames"]) == 16 and "confirmation" not in str(plan["frames"])
    assert set(plan["development_toeplitz_seeds"]) == {f["frame_id"] for f in plan["frames"]}
    assert not any(plan["identity_overlap"].values())
    with pytest.raises(ValueError, match="explicit verifier_runner"):
        lane.verify(out, config=TEST_CONFIG, _test_only=True)
    assert lane.verify(out, config=TEST_CONFIG, verifier_runner=failed, _test_only=True)["plan_only"]
    with pytest.raises(ValueError, match="explicit fake runner"):
        lane.run(out, config=TEST_CONFIG, _test_only=True)
    with pytest.raises(ValueError, match="not authorized"):
        lane.run(out, config=TEST_CONFIG, runner=failed, _test_only=False)
    with pytest.raises(ValueError, match="not authorized"):
        lane.run(Path("unused"), config=TEST_CONFIG, runner=failed, _test_only=False)


def test_official_root_is_locked_and_never_created():
    official = lane._official(TEST_CONFIG)
    assert not official.exists()
    with pytest.raises(ValueError, match="locked"):
        lane.create_plan(None, config=TEST_CONFIG, _test_only=False)
    with pytest.raises(ValueError, match="locked"):
        lane.create_plan(str(official), config=TEST_CONFIG, _test_only=True)
    assert not official.exists()


def test_fake_runner_does_not_fall_back_to_production(monkeypatch):
    out = _out("trap")
    lane.create_plan(out, config=TEST_CONFIG, _test_only=True)
    def trap(*args, **kwargs):
        raise AssertionError("production decoder entered")
    monkeypatch.setattr(lane, "production_runner", trap)
    assert lane.run(out, config=TEST_CONFIG, runner=failed, _test_only=True)["run_status"] == "development_completed"
    assert lane.verify(out, config=TEST_CONFIG, verifier_runner=failed, _test_only=True)["verified"]


# ---------------------------------------------------------------- fake lifecycle (A08, T2)

def test_complete_fake_package_and_strict_read_only_replay(monkeypatch):
    _noiseless(monkeypatch)
    out = _out("fake_success")
    lane.create_plan(out, config=TEST_CONFIG, _test_only=True)
    got = lane.run(out, config=TEST_CONFIG, runner=success, _test_only=True)
    assert got["run_status"] == "development_completed" and got["promoted"] is False
    assert {p.name for p in out.iterdir()} == set(lane.ARTIFACTS)
    rows = lane._rows(out / "formal_frame_outcomes.csv")
    assert len(rows) == 16
    assert all(r["status"] == "verified_success" for r in rows)
    # disclosure accounting: syndrome 10*m bits + one invoked 64-bit tag per frame.
    assert all(int(r["key_dependent_disclosure_bits_total"]) == 10 * int(r["check_count"]) + 64 for r in rows)
    assert all(int(r["public_control_bits_total"]) == lane.SEED_BITS + 2 for r in rows)
    report = json.loads((out / "formal_qualification_report.json").read_text())
    assert report["promoted"] is False
    assert report["per_stratum_verified_success"] == {"0.20": 8, "0.30": 8}
    # strict read-only replay passes without touching the production decoder.
    assert lane.verify(out, config=TEST_CONFIG, verifier_runner=success, _test_only=True)["verified"]


def test_fake_failed_lane_replays_and_reports_no_verification(monkeypatch):
    out = _out("fake_failed")
    lane.create_plan(out, config=TEST_CONFIG, _test_only=True)
    got = lane.run(out, config=TEST_CONFIG, runner=failed, _test_only=True)
    assert got["run_status"] == "development_completed"
    rows = lane._rows(out / "formal_frame_outcomes.csv")
    assert len(rows) == 16 and all(r["status"] == "decode_failed" for r in rows)
    assert all(r["verification_attempts"] == "0" for r in rows)
    assert all(int(r["key_dependent_disclosure_bits_total"]) == 10 * int(r["check_count"]) for r in rows)
    events = [json.loads(line) for line in (out / "formal_transcript.jsonl").read_bytes().splitlines()]
    assert len(events) == 16 * 3 and all(e["event_type"] != "VERIFICATION_TAG_STAGE1" for e in events)
    assert lane.verify(out, config=TEST_CONFIG, verifier_runner=failed, _test_only=True)["verified"]


def test_verify_failed_path_uses_real_tag_comparison(monkeypatch):
    _noiseless(monkeypatch)
    out = _out("verify_failed")
    lane.create_plan(out, config=TEST_CONFIG, _test_only=True)
    lane.run(out, config=TEST_CONFIG, runner=wrong, _test_only=True)
    rows = lane._rows(out / "formal_frame_outcomes.csv")
    assert len(rows) == 16 and all(r["status"] == "verify_failed" for r in rows)
    assert all(r["verification_attempts"] == "1" for r in rows)
    assert lane.verify(out, config=TEST_CONFIG, verifier_runner=wrong, _test_only=True)["verified"]


def test_fatal_hook_retains_invalid_package_and_replays_prefix():
    out = _out("partial")
    lane.create_plan(out, config=TEST_CONFIG, _test_only=True)
    def hook(count):
        if count == 5:
            raise RuntimeError("fatal hook")
    with pytest.raises(RuntimeError, match="fatal hook"):
        lane.run(out, config=TEST_CONFIG, runner=failed, _test_only=True, fatal_hook=hook)
    assert {p.name for p in out.iterdir()} == set(lane.ARTIFACTS)
    assert lane.verify(out, config=TEST_CONFIG, verifier_runner=failed, _test_only=True)["run_status"] == "invalid_run"
    assert len(lane._rows(out / "formal_frame_outcomes.csv")) == 5


def test_run_requires_plan_only_directory():
    out = _out("twice")
    lane.create_plan(out, config=TEST_CONFIG, _test_only=True)
    lane.run(out, config=TEST_CONFIG, runner=failed, _test_only=True)
    with pytest.raises(ValueError, match="plan-only"):
        lane.run(out, config=TEST_CONFIG, runner=failed, _test_only=True)


def test_fake_package_strict_replay_rejects_semantic_drift(monkeypatch):
    _noiseless(monkeypatch)
    out = _out("strict_drift")
    lane.create_plan(out, config=TEST_CONFIG, _test_only=True)
    lane.run(out, config=TEST_CONFIG, runner=success, _test_only=True)
    with pytest.raises(ValueError, match="semantic replay"):
        lane.verify(out, config=TEST_CONFIG, verifier_runner=failed, _test_only=True)


# ---------------------------------------------------------------- tamper matrix (A07)

def test_byte_tamper_of_codebook_manifest_is_rejected(monkeypatch):
    _noiseless(monkeypatch)
    out = _out("byte_tamper")
    lane.create_plan(out, config=TEST_CONFIG, _test_only=True)
    lane.run(out, config=TEST_CONFIG, runner=success, _test_only=True)
    path = out / "formal_codebook_manifest.json"
    data = json.loads(path.read_text())
    data["ordered_entries"][0]["rank"] = 0
    path.write_text(json.dumps(data))
    _resign(out)
    with pytest.raises(ValueError, match="candidate/codebook/policy replay"):
        lane.verify(out, config=TEST_CONFIG, verifier_runner=success, _test_only=True)


def test_semantic_self_hash_tamper_of_policy_is_rejected(monkeypatch):
    _noiseless(monkeypatch)
    out = _out("policy_tamper")
    lane.create_plan(out, config=TEST_CONFIG, _test_only=True)
    lane.run(out, config=TEST_CONFIG, runner=success, _test_only=True)
    path = out / "formal_policy_manifest.json"
    data = json.loads(path.read_text())
    data["max_iter"] = 1
    path.write_text(json.dumps(data))
    _resign(out)
    with pytest.raises(ValueError, match="candidate/codebook/policy replay"):
        lane.verify(out, config=TEST_CONFIG, verifier_runner=success, _test_only=True)


def test_manifest_link_tamper_is_rejected():
    out = _out("link_tamper")
    lane.create_plan(out, config=TEST_CONFIG, _test_only=True)
    lane.run(out, config=TEST_CONFIG, runner=failed, _test_only=True)
    # stale artifacts hash: the manifest is the link, and it is not re-signed
    # after the transcript bytes are replaced.
    events_path = out / "formal_transcript.jsonl"
    raw = events_path.read_bytes()
    first = raw.splitlines()[0]
    line = json.loads(first)
    line["payload"]["syndrome"][0] ^= 1
    events_path.write_bytes(lane.canonical_event(line) + raw[len(first) + 1:])
    with pytest.raises(ValueError, match="artifact DAG"):
        lane.verify(out, config=TEST_CONFIG, verifier_runner=failed, _test_only=True)


def test_source_identity_tamper_is_rejected():
    out = _out("source_tamper")
    probe_rel = Path("workspace") / "nbldpc_v6_engineering" / out.parent.name / "source_probe.txt"
    probe_abs = Path.cwd() / probe_rel
    probe_abs.parent.mkdir(parents=True, exist_ok=True)
    probe_abs.write_text("probe-v1")
    cfg = _config(source_files=lane._SRC + (str(probe_rel),))
    lane.create_plan(out, config=cfg, _test_only=True)
    probe_abs.write_text("probe-v2")
    with pytest.raises(ValueError, match="plan contract/provenance"):
        lane.verify(out, config=cfg, verifier_runner=failed, _test_only=True)


def test_transcript_tamper_even_when_recanonicalized_is_rejected(monkeypatch):
    _noiseless(monkeypatch)
    out = _out("transcript_tamper")
    lane.create_plan(out, config=TEST_CONFIG, _test_only=True)
    lane.run(out, config=TEST_CONFIG, runner=success, _test_only=True)
    events = [json.loads(line) for line in (out / "formal_transcript.jsonl").read_bytes().splitlines()]
    next(e for e in events if e["event_type"] == "SYNDROME_INITIAL")["payload"]["syndrome"][0] ^= 1
    (out / "formal_transcript.jsonl").write_bytes(b"".join(lane.canonical_event(e) for e in events))
    _resign(out)
    with pytest.raises(ValueError, match="semantic replay"):
        lane.verify(out, config=TEST_CONFIG, verifier_runner=success, _test_only=True)


def test_leakage_tamper_is_rejected():
    out = _out("leakage_tamper")
    lane.create_plan(out, config=TEST_CONFIG, _test_only=True)
    lane.run(out, config=TEST_CONFIG, runner=failed, _test_only=True)
    # inject a secret-bearing raw line into the transcript.
    secret = {"event_id": 999, "frame_key": "x", "method": "x", "event_type": "DECODER_STAGE1",
              "direction": "bob_local", "parent_event_id": 0, "pass_id": 999, "plane_id": "q1024",
              "key_dependent_bits": 0, "public_control_bits": 0,
              "payload": {"decoded_symbols": [1, 2, 3]}}
    with open(out / "formal_transcript.jsonl", "a", encoding="utf8") as handle:
        handle.write(json.dumps(secret, sort_keys=True) + "\n")
    _resign(out)
    with pytest.raises(ValueError, match="canonical|forbidden"):
        lane.verify(out, config=TEST_CONFIG, verifier_runner=failed, _test_only=True)
    # a non-secret but forbidden-diagnostic key is rejected by the scan.
    path = out / "formal_candidate_manifest.json"
    data = json.loads(path.read_text())
    data["alice_truth_note"] = "no"
    path.write_text(json.dumps(data))
    _resign(out)
    with pytest.raises(ValueError, match="forbidden diagnostic"):
        lane.verify(out, config=TEST_CONFIG, verifier_runner=failed, _test_only=True)


def test_gate_rebuilding_promoted_forgery_is_rejected(monkeypatch):
    _noiseless(monkeypatch)
    out = _out("gate_forgery")
    lane.create_plan(out, config=TEST_CONFIG, _test_only=True)
    lane.run(out, config=TEST_CONFIG, runner=success, _test_only=True)
    report_path = out / "formal_qualification_report.json"
    report = json.loads(report_path.read_text())
    report["promoted"] = True
    report_path.write_text(json.dumps(report))
    _resign(out)
    with pytest.raises(ValueError, match="artifact DAG"):
        lane.verify(out, config=TEST_CONFIG, verifier_runner=success, _test_only=True)


def test_identity_freshness_aborts_plan_creation(monkeypatch):
    original = lane._identity_overlap
    calls = {"n": 0}
    def forged(config, frames, *, exclude=None):
        calls["n"] += 1
        if calls["n"] == 2:
            return {"roots": ["forged"], "frame_ids": [], "array_sha256": [], "atomic_keys": []}
        return original(config, frames, exclude=exclude)
    monkeypatch.setattr(lane, "_identity_overlap", forged)
    out = _out("freshness")
    with pytest.raises(ValueError, match="identity freshness"):
        lane.create_plan(out, config=TEST_CONFIG, _test_only=True)


def test_seed_freshness_rejects_reused_seed_records(monkeypatch):
    # Forcing every materialized seed record to be identical (valid records,
    # same seed_id) must fail the duplicate-seed check.
    from comparison_bench.src.comparison_bench.formal_ir.shared import seed_record, unpack_bits_msb
    def fixed_record(bit_length):
        raw = bytes((bit_length + 7) // 8)
        return seed_record(unpack_bits_msb(raw, bit_length))
    monkeypatch.setattr(lane, "materialize_seed_record", fixed_record)
    out = _out("seed_reuse")
    with pytest.raises(ValueError, match="seed freshness"):
        lane.create_plan(out, config=TEST_CONFIG, _test_only=True)


# ---------------------------------------------------------------- V6-51 sacrificed canary

def test_canary_config_identity_matches_config_contract():
    canary = lane.CANARY
    assert canary.run_id == "20260802_v1_nbldpc_v6_canary"
    assert canary.canonical_schema == lane.CONFIG.canonical_schema
    assert canary.method == lane.CONFIG.method
    assert canary.q == lane.CONFIG.q and canary.n == lane.CONFIG.n
    assert canary.ps == lane.CONFIG.ps
    assert canary.caps == lane.CONFIG.caps
    assert canary.seed_bits == lane.CONFIG.seed_bits
    assert canary.development_frames == 4
    assert canary.roots == {("development", .20): 202608024000, ("development", .30): 202608024100}
    assert canary.roots != lane.CONFIG.roots


def test_canary_plan_is_development_only_8_frames():
    out = _out("canary_plan")
    plan = lane.create_plan(out, config=lane.CANARY, _test_only=True)
    assert plan["run_id"] == "20260802_v1_nbldpc_v6_canary"
    assert len(plan["frames"]) == 8
    assert [f["p"] for f in plan["frames"]] == [.2] * 4 + [.3] * 4
    assert all(f["role"] == "development" for f in plan["frames"])
    assert "confirmation" not in json.dumps(plan["frames"])
    assert not any(plan["identity_overlap"].values())


def test_canary_freshness_versus_config_and_prior_evidence():
    # Root freshness: disjoint from the CONFIG roots and from every prior
    # evidence root discovered by the lane's own scanner.
    canary_roots = {str(x) for x in lane.CANARY.roots.values()}
    config_roots = {str(x) for x in lane.CONFIG.roots.values()}
    prior = lane._prior_identities()
    assert canary_roots.isdisjoint(config_roots)
    assert canary_roots.isdisjoint(prior["roots"])
    # Identity freshness via the lane's own overlap checker.
    frames = [lane._frame(lane.CANARY, p, i) for p in lane.CANARY.ps
              for i in range(lane.CANARY.development_frames)]
    assert not any(lane._identity_overlap(lane.CANARY, frames).values())
    # Seed freshness: all 8 plan seed records are unique and disjoint from the
    # lane's own prior-seed-id scan of every official-root JSON.
    plan = lane.expected_plan(lane.CANARY)
    ids = {record["seed_id"] for record in plan["development_toeplitz_seeds"].values()}
    assert len(ids) == 8
    assert ids.isdisjoint(lane._prior_seed_ids())


def test_canary_official_root_is_locked():
    official = lane._official(lane.CANARY)
    assert not official.exists()
    with pytest.raises(ValueError, match="locked"):
        lane.create_plan(None, config=lane.CANARY, _test_only=False)
    with pytest.raises(ValueError, match="locked"):
        lane.create_plan(str(official), config=lane.CANARY, _test_only=True)
    assert not official.exists()


def test_config_production_run_still_blocked():
    with pytest.raises(ValueError, match="authorized only for the sacrificed CANARY"):
        lane.run(None, config=lane.CONFIG, runner=lane.production_runner,
                 production_authorized=True)
    with pytest.raises(ValueError, match="not authorized"):
        lane.run(Path("unused"), config=lane.CONFIG, runner=lane.production_runner,
                 _test_only=False)


def test_canary_production_run_guard_requires_output_and_runner():
    with pytest.raises(ValueError, match="explicit workspace output"):
        lane.run(None, config=lane.CANARY, runner=lane.production_runner,
                 production_authorized=True)
    with pytest.raises(ValueError, match="explicit production runner"):
        lane.run(Path("unused"), config=lane.CANARY, runner=None,
                 production_authorized=True)
    with pytest.raises(ValueError, match="not authorized"):
        lane.run(Path("unused"), config=lane.CANARY, runner=lane.production_runner,
                 _test_only=False)


def test_canary_fake_runner_never_enters_production_decoder(monkeypatch):
    out = _out("canary_trap")
    lane.create_plan(out, config=lane.CANARY, _test_only=True)
    def trap(*args, **kwargs):
        raise AssertionError("production decoder entered")
    monkeypatch.setattr(lane, "production_runner", trap)
    got = lane.run(out, config=lane.CANARY, runner=failed, _test_only=True)
    assert got["run_status"] == "development_completed"
    assert lane.verify(out, config=lane.CANARY, verifier_runner=failed, _test_only=True)["verified"]


def test_canary_fake_package_and_strict_replay(monkeypatch):
    _noiseless(monkeypatch)
    out = _out("canary_fake")
    lane.create_plan(out, config=lane.CANARY, _test_only=True)
    got = lane.run(out, config=lane.CANARY, runner=success, _test_only=True)
    assert got["run_status"] == "development_completed" and got["promoted"] is False
    assert {p.name for p in out.iterdir()} == set(lane.ARTIFACTS)
    rows = lane._rows(out / "formal_frame_outcomes.csv")
    assert len(rows) == 8
    assert all(r["status"] == "verified_success" for r in rows)
    report = json.loads((out / "formal_qualification_report.json").read_text())
    assert report["per_stratum_verified_success"] == {"0.20": 4, "0.30": 4}
    # strict read-only replay passes under the canary config.
    assert lane.verify(out, config=lane.CANARY, verifier_runner=success, _test_only=True)["verified"]
