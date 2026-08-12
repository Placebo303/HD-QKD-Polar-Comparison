"""NBLDPC7 R1A/R1B development harness acceptance: development-only plans,
explicit fake-runner guards, engineering-stage locks (no plan preparation, no
production execution), one complete fake package with strict read-only replay,
invalid-run retention, the layered tamper matrix, the controller-gate bridge,
and the R1B one-repetition lane (additive R1B tests at the end)."""
from __future__ import annotations
import json
import uuid
from pathlib import Path
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_development as lane
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_ladder as ladder
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r1b_codebook as r1b_cb


def _out(name):
    root = Path("workspace") / "nbldpc_v7_r1a" / uuid.uuid4().hex / name
    root.parent.mkdir(parents=True, exist_ok=True)
    return root


def _config(frames=8, source_files=lane._SRC):
    return lane.DevelopmentConfig(
        run_id="nbldpc_v7_r1a_development_engineering_test", canonical_schema="NBLDPC7DEV",
        method=lane.METHOD, q=1024, n=256, ps=(.20, .30),
        roots={("development", .20): 202608049000, ("development", .30): 202608049100},
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
        row["alice"] = [0] * 256
        row["bob"] = [0] * 256
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


# ---------------------------------------------------------------- guards

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


def test_plan_preparation_is_not_authorized_in_engineering_stage():
    # create no plan: the production plan path is a hard stop before V7-12.
    with pytest.raises(ValueError, match="plan preparation is not authorized"):
        lane.create_plan(Path("unused"), config=TEST_CONFIG, _test_only=False)
    with pytest.raises(ValueError, match="plan preparation is not authorized"):
        lane.create_plan(None, config=TEST_CONFIG, _test_only=False)
    with pytest.raises(ValueError, match="plan preparation is not authorized"):
        lane.create_plan(None, config=lane.CANARY, _test_only=False)
    with pytest.raises(ValueError, match="plan preparation is not authorized"):
        lane.create_plan(None, config=lane.DEVELOPMENT, _test_only=False)


def test_v7_12_canary_plan_authorization_is_canary_only_and_never_executes():
    # After the V7-12 main-thread review the sacrificed CANARY plan may be
    # prepared for real; the DEVELOPMENT plan path still refuses and execution
    # is still never authorized.
    out = _out("canary_authorized")
    plan = lane.create_plan(out, config=lane.CANARY, production_authorized=True)
    assert plan["run_id"] == "20260802_v1_nbldpc_v7_r1a_canary"
    assert len(plan["frames"]) == 8
    assert all(f["role"] == "development" for f in plan["frames"])
    assert not any(plan["identity_overlap"].values())
    assert {p.name for p in out.iterdir()} == {"pre_run_plan.json"}
    with pytest.raises(ValueError, match="not authorized"):
        lane.create_plan(_out("dev_authorized"), config=lane.DEVELOPMENT,
                         production_authorized=True)
    with pytest.raises(ValueError, match="not authorized"):
        lane.run(out, config=lane.CANARY, runner=failed, _test_only=False)


def test_v7_12_canary_production_execution_authorization_is_canary_only():
    # V7-12 second half: production execution is authorized only for the
    # sacrificed CANARY config, with an explicit non-official workspace
    # output and an explicit production runner.  The DEVELOPMENT config and
    # any bare (unauthorized) call still raise.
    with pytest.raises(ValueError, match="authorized only for the sacrificed CANARY"):
        lane.run(None, config=lane.DEVELOPMENT, runner=lane.production_runner,
                 production_authorized=True)
    with pytest.raises(ValueError, match="not authorized"):
        lane.run(Path("unused"), config=lane.DEVELOPMENT, runner=lane.production_runner,
                 _test_only=False)
    with pytest.raises(ValueError, match="explicit workspace output"):
        lane.run(None, config=lane.CANARY, runner=lane.production_runner,
                 production_authorized=True)
    with pytest.raises(ValueError, match="explicit production runner"):
        lane.run(Path("unused"), config=lane.CANARY, runner=None,
                 production_authorized=True)
    with pytest.raises(ValueError, match="not authorized"):
        lane.run(Path("unused"), config=lane.CANARY, runner=lane.production_runner,
                 _test_only=False)


def test_official_root_is_locked_and_never_created():
    for config in (TEST_CONFIG, lane.CANARY, lane.DEVELOPMENT):
        official = lane._official(config)
        assert not official.exists()
        with pytest.raises(ValueError, match="locked"):
            lane.create_plan(str(official), config=config, _test_only=True)
        assert not official.exists()


def test_fake_runner_does_not_fall_back_to_production(monkeypatch):
    out = _out("trap")
    lane.create_plan(out, config=TEST_CONFIG, _test_only=True)
    def trap(*args, **kwargs):
        raise AssertionError("production decoder entered")
    monkeypatch.setattr(lane, "production_runner", trap)
    assert lane.run(out, config=TEST_CONFIG, runner=failed, _test_only=True)["run_status"] == "development_completed"
    assert lane.verify(out, config=TEST_CONFIG, verifier_runner=failed, _test_only=True)["verified"]


# ---------------------------------------------------------------- fake lifecycle (T2)

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
    # disclosure accounting: syndrome 10*170 bits + one invoked 64-bit tag.
    assert all(int(r["key_dependent_disclosure_bits_total"]) == 10 * 170 + 64 for r in rows)
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
    assert all(int(r["key_dependent_disclosure_bits_total"]) == 10 * 170 for r in rows)
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


# ---------------------------------------------------------------- tamper matrix

def test_byte_tamper_of_codebook_manifest_is_rejected(monkeypatch):
    _noiseless(monkeypatch)
    out = _out("byte_tamper")
    lane.create_plan(out, config=TEST_CONFIG, _test_only=True)
    lane.run(out, config=TEST_CONFIG, runner=success, _test_only=True)
    path = out / "formal_codebook_manifest.json"
    data = json.loads(path.read_text())
    data["rank"] = 0
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
    probe_rel = Path("workspace") / "nbldpc_v7_r1a" / out.parent.name / "source_probe.txt"
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
    secret = {"event_id": 999, "frame_key": "x", "method": "x", "event_type": "DECODER_STAGE1",
              "direction": "bob_local", "parent_event_id": 0, "pass_id": 999, "plane_id": "q1024",
              "key_dependent_bits": 0, "public_control_bits": 0,
              "payload": {"decoded_symbols": [1, 2, 3]}}
    with open(out / "formal_transcript.jsonl", "a", encoding="utf8") as handle:
        handle.write(json.dumps(secret, sort_keys=True) + "\n")
    _resign(out)
    with pytest.raises(ValueError, match="canonical|forbidden"):
        lane.verify(out, config=TEST_CONFIG, verifier_runner=failed, _test_only=True)
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
    from comparison_bench.src.comparison_bench.formal_ir.shared import seed_record, unpack_bits_msb
    def fixed_record(bit_length):
        raw = bytes((bit_length + 7) // 8)
        return seed_record(unpack_bits_msb(raw, bit_length))
    monkeypatch.setattr(lane, "materialize_seed_record", fixed_record)
    out = _out("seed_reuse")
    with pytest.raises(ValueError, match="seed freshness"):
        lane.create_plan(out, config=TEST_CONFIG, _test_only=True)


# ---------------------------------------------------------------- V7 canary / development configs

def test_canary_and_development_config_identity_and_disjoint_roots():
    canary = lane.CANARY
    assert canary.run_id == "20260802_v1_nbldpc_v7_r1a_canary"
    assert canary.canonical_schema == lane.CONFIG.canonical_schema
    assert canary.method == lane.METHOD == "nbldpc_formal_v7_r1a_mr0"
    assert canary.q == 1024 and canary.n == 256 and canary.ps == (.20, .30)
    assert canary.caps == lane.CONFIG.caps and canary.seed_bits == lane.CONFIG.seed_bits
    assert canary.development_frames == 4
    development = lane.DEVELOPMENT
    assert development.run_id == "20260802_v1_nbldpc_v7_r1a_development"
    assert development.development_frames == 16
    assert canary.roots == {("development", .20): 202608047000, ("development", .30): 202608047100}
    assert development.roots == {("development", .20): 202608048000, ("development", .30): 202608048100}
    assert canary.roots != development.roots
    assert set(canary.roots.values()).isdisjoint(set(development.roots.values()))


def test_canary_plan_is_development_only_8_frames():
    out = _out("canary_plan")
    plan = lane.create_plan(out, config=lane.CANARY, _test_only=True)
    assert plan["run_id"] == "20260802_v1_nbldpc_v7_r1a_canary"
    assert len(plan["frames"]) == 8
    assert [f["p"] for f in plan["frames"]] == [.2] * 4 + [.3] * 4
    assert all(f["role"] == "development" for f in plan["frames"])
    assert "confirmation" not in json.dumps(plan["frames"])
    assert not any(plan["identity_overlap"].values())


def test_development_plan_is_development_only_32_frames():
    out = _out("development_plan")
    plan = lane.create_plan(out, config=lane.DEVELOPMENT, _test_only=True)
    assert plan["run_id"] == "20260802_v1_nbldpc_v7_r1a_development"
    assert len(plan["frames"]) == 32
    assert all(f["role"] == "development" for f in plan["frames"])
    assert "confirmation" not in json.dumps(plan["frames"])
    assert not any(plan["identity_overlap"].values())


def test_production_run_blocked_for_all_configs():
    for config in (lane.CANARY, lane.DEVELOPMENT, lane.CONFIG):
        with pytest.raises(ValueError, match="not authorized"):
            lane.run(Path("unused"), config=config, runner=lane.production_runner, _test_only=False)
        with pytest.raises(ValueError, match="not authorized"):
            lane.run(None, config=config, runner=lane.production_runner, _test_only=False)


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
    assert lane.verify(out, config=lane.CANARY, verifier_runner=success, _test_only=True)["verified"]


# ---------------------------------------------------------------- controller bridge (T2)

def test_verified_report_payload_feeds_the_controller_gate(monkeypatch):
    _noiseless(monkeypatch)
    out = _out("controller_bridge")
    lane.create_plan(out, config=lane.CANARY, _test_only=True)
    lane.run(out, config=lane.CANARY, runner=success, _test_only=True)
    replay = lane.verify(out, config=lane.CANARY, verifier_runner=success, _test_only=True)
    assert replay["verified"]
    payload = lane.verified_report_payload(lane.CANARY, out,
                                           replay_report_sha256=ladder._sha(ladder._compact(replay)))
    assert payload["stage"] == "canary"
    assert payload["per_stratum"] == {f"{p:.2f}": {"frames": 4, "verified_success": 4,
                                                   "forbidden_failures": 0,
                                                   "key_dependent_bits_excluding_tag": 1700,
                                                   "symbols_per_frame": 256}
                                      for p in (0.20, 0.30)}
    assert ladder.canary_gate_failed(payload) is False
    assert payload["median_runtime_seconds"] >= 0.0


# ---------------------------------------------------------------- R1B one-repetition lane (V7-14)

def _config_r1b(frames=8, source_files=lane._SRC_R1B):
    return lane.DevelopmentConfig(
        run_id="nbldpc_v7_r1b_development_engineering_test", canonical_schema="NBLDPC7R1BDEV",
        method=lane.METHOD_R1B, q=1024, n=256, ps=(.20, .30),
        roots={("development", .20): 202608049900, ("development", .30): 202608049910},
        caps=lane.CAPS, seed_bits=lane.SEED_BITS, development_frames=frames,
        source_files=tuple(source_files), contract=lane.CONTRACT)


TEST_CONFIG_R1B = _config_r1b()


def failed_r1b(bob, repeated, syndrome, manifest, matrices, *, check_count, p):
    return {"status": "decode_failed", "iterations": 1}


def success_r1b(bob, repeated, syndrome, manifest, matrices, *, check_count, p):
    return {"status": "syndrome_consistent", "iterations": 1, "decoded_symbols": tuple(bob)}


def _noiseless_r1b(monkeypatch):
    original = lane._frame
    def noiseless(config, p, index):
        row = original(config, p, index)
        row["alice"] = [0] * 256
        row["bob"] = [0] * 256
        row["repeated"] = [0] * 256
        return row
    monkeypatch.setattr(lane, "_frame", noiseless)


def test_r1b_config_identity_and_disjoint_roots():
    canary = lane.CANARY_R1B
    assert canary.run_id == "20260802_v1_nbldpc_v7_r1b_canary"
    assert canary.canonical_schema == "NBLDPC7R1BDEV"
    assert canary.method == lane.METHOD_R1B == "nbldpc_formal_v7_r1b_mr1"
    assert canary.development_frames == 4
    development = lane.DEVELOPMENT_R1B
    assert development.run_id == "20260802_v1_nbldpc_v7_r1b_development"
    assert development.development_frames == 16
    # R1B roots are disjoint from R1A canary/development roots and from each
    # other, and from the R1A engineering-test roots.
    r1b_roots = set(canary.roots.values()) | set(development.roots.values())
    r1a_roots = set(lane.CANARY.roots.values()) | set(lane.DEVELOPMENT.roots.values())
    assert r1b_roots.isdisjoint(r1a_roots)
    assert set(canary.roots.values()).isdisjoint(set(development.roots.values()))
    assert r1b_roots.isdisjoint({202608049000, 202608049100})
    assert set(canary.roots.values()) == {202608049500, 202608049600}
    assert set(development.roots.values()) == {202608049700, 202608049800}


def test_r1b_plan_is_development_only_with_repeated_observations():
    out = _out("r1b_plan")
    plan = lane.create_plan(out, config=lane.CANARY_R1B, _test_only=True)
    assert plan["run_id"] == "20260802_v1_nbldpc_v7_r1b_canary"
    assert len(plan["frames"]) == 8
    assert [f["p"] for f in plan["frames"]] == [.2] * 4 + [.3] * 4
    assert all(f["role"] == "development" for f in plan["frames"])
    assert all(len(f["repeated"]) == 256 for f in plan["frames"])
    assert "confirmation" not in json.dumps(plan["frames"])
    assert not any(plan["identity_overlap"].values())
    # the repeated observation is the deterministic public multiplier applied
    # to Alice's symbol with an independent error; the multiplier list is
    # public model data derived from the frozen R1B multiplier seed.
    assert plan["provenance"]["codebook_manifest_id"] == r1b_cb.build_nbldpc_v7_r1b_codebook()[0]["manifest_id"]
    assert r1b_cb.multiplier_spec_id() == r1b_cb.build_nbldpc_v7_r1b_codebook()[0]["multiplier_spec_id"]
    assert set(r1b_cb.multipliers()) <= set(range(1, 1024))


def test_r1b_plan_gate_canary_only_and_r1b_development_run_still_blocked():
    # V7-15: after the R1B canary plan review, CANARY_R1B plan preparation is
    # authorized; DEVELOPMENT_R1B still refuses.  R1B DEVELOPMENT production
    # execution is still never authorized (even with the production flag);
    # the R1B sacrificed CANARY may execute only through the canary-only
    # authorization test below (mirror of the R1A gate).
    out = _out("r1b_canary_authorized")
    plan = lane.create_plan(out, config=lane.CANARY_R1B, production_authorized=True)
    assert plan["run_id"] == "20260802_v1_nbldpc_v7_r1b_canary"
    assert not any(plan["identity_overlap"].values())
    with pytest.raises(ValueError, match="not authorized"):
        lane.create_plan(_out("r1b_dev_authorized"), config=lane.DEVELOPMENT_R1B,
                         production_authorized=True)
    # bare (no production flag) run() raises for every R1B config.
    for config in (lane.CANARY_R1B, lane.DEVELOPMENT_R1B, lane.CONFIG):
        with pytest.raises(ValueError, match="not authorized"):
            lane.run(Path("unused"), config=config, runner=failed_r1b, _test_only=False)
    # DEVELOPMENT_R1B production execution still raises even with the flag.
    with pytest.raises(ValueError, match="authorized only for the sacrificed CANARY"):
        lane.run(None, config=lane.DEVELOPMENT_R1B, runner=failed_r1b,
                 production_authorized=True)


def test_v7_15_r1b_canary_production_execution_authorization_is_canary_only():
    # V7-15 second half: R1B production execution is authorized only for the
    # sacrificed CANARY_R1B config, with an explicit non-official workspace
    # output and an explicit production runner.  The DEVELOPMENT_R1B config
    # and any bare (unauthorized) call still raise.
    with pytest.raises(ValueError, match="authorized only for the sacrificed CANARY"):
        lane.run(None, config=lane.DEVELOPMENT_R1B, runner=lane.production_runner_r1b,
                 production_authorized=True)
    with pytest.raises(ValueError, match="not authorized"):
        lane.run(Path("unused"), config=lane.DEVELOPMENT_R1B, runner=lane.production_runner_r1b,
                 _test_only=False)
    with pytest.raises(ValueError, match="explicit workspace output"):
        lane.run(None, config=lane.CANARY_R1B, runner=lane.production_runner_r1b,
                 production_authorized=True)
    with pytest.raises(ValueError, match="explicit production runner"):
        lane.run(Path("unused"), config=lane.CANARY_R1B, runner=None,
                 production_authorized=True)
    with pytest.raises(ValueError, match="not authorized"):
        lane.run(Path("unused"), config=lane.CANARY_R1B, runner=lane.production_runner_r1b,
                 _test_only=False)


def test_r1b_fake_canary_never_enters_production_decoder(monkeypatch):
    out = _out("r1b_trap")
    lane.create_plan(out, config=lane.CANARY_R1B, _test_only=True)
    def trap(*args, **kwargs):
        raise AssertionError("production decoder entered")
    monkeypatch.setattr(lane, "production_runner", trap)
    monkeypatch.setattr(lane, "production_runner_r1b", trap)
    got = lane.run(out, config=lane.CANARY_R1B, runner=failed_r1b, _test_only=True)
    assert got["run_status"] == "development_completed"
    assert lane.verify(out, config=lane.CANARY_R1B, verifier_runner=failed_r1b,
                       _test_only=True)["verified"]


def test_r1b_fake_canary_package_and_strict_replay(monkeypatch):
    _noiseless_r1b(monkeypatch)
    out = _out("r1b_fake_success")
    lane.create_plan(out, config=lane.CANARY_R1B, _test_only=True)
    got = lane.run(out, config=lane.CANARY_R1B, runner=success_r1b, _test_only=True)
    assert got["run_status"] == "development_completed" and got["promoted"] is False
    assert {p.name for p in out.iterdir()} == set(lane.ARTIFACTS)
    rows = lane._rows(out / "formal_frame_outcomes.csv")
    assert len(rows) == 8 and all(r["status"] == "verified_success" for r in rows)
    # disclosure accounting: the mother syndrome (1700 bits) plus one invoked
    # 64-bit tag; the multiplier identities are public control bits.
    assert all(int(r["key_dependent_disclosure_bits_total"]) == 10 * 170 + 64 for r in rows)
    assert all(int(r["public_control_bits_total"]) == lane.MULTIPLIER_CONTROL_BITS + lane.SEED_BITS + 2
               for r in rows)
    report = json.loads((out / "formal_qualification_report.json").read_text())
    assert report["per_stratum_verified_success"] == {"0.20": 4, "0.30": 4}
    assert lane.verify(out, config=lane.CANARY_R1B, verifier_runner=success_r1b,
                       _test_only=True)["verified"]


def test_r1b_transcript_records_multiplier_control_but_never_raw_symbols(monkeypatch):
    _noiseless_r1b(monkeypatch)
    out = _out("r1b_transcript")
    lane.create_plan(out, config=lane.CANARY_R1B, _test_only=True)
    lane.run(out, config=lane.CANARY_R1B, runner=failed_r1b, _test_only=True)
    events = [json.loads(line) for line in (out / "formal_transcript.jsonl").read_bytes().splitlines()]
    assert len(events) == 8 * 4
    multiplier_events = [e for e in events if e["event_type"] == "MULTIPLIER_REPETITION"]
    assert len(multiplier_events) == 8
    first = multiplier_events[0]
    # multiplier identities/control bits are recorded; raw or corrected
    # symbols are never recorded (v7 _FORBIDDEN discipline).
    assert first["direction"] == "control"
    assert first["key_dependent_bits"] == 0
    assert first["public_control_bits"] == lane.MULTIPLIER_CONTROL_BITS == 2560
    assert first["payload"]["matrix_id"] == r1b_cb.multiplier_spec_id()
    assert first["payload"]["value"] == list(r1b_cb.multipliers())
    # the v7 _FORBIDDEN discipline: raw or corrected symbols never enter any
    # transcript payload (only the public syndrome and multiplier identities);
    # the "alice_to_bob" direction label on SYNDROME_INITIAL is a direction
    # marker, not a symbol leak.
    assert "decoded_symbols" not in json.dumps(events)
    assert "repeated" not in json.dumps(events)
    for event in events:
        payload_text = json.dumps(event["payload"])
        assert "alice" not in payload_text and "bob" not in payload_text
    # strict replay reconstructs the same transcript.
    assert lane.verify(out, config=lane.CANARY_R1B, verifier_runner=failed_r1b,
                       _test_only=True)["verified"]


def test_r1b_codebook_multiplier_tamper_rejected_in_package(monkeypatch):
    _noiseless_r1b(monkeypatch)
    out = _out("r1b_mult_tamper")
    lane.create_plan(out, config=lane.CANARY_R1B, _test_only=True)
    lane.run(out, config=lane.CANARY_R1B, runner=failed_r1b, _test_only=True)
    path = out / "formal_codebook_manifest.json"
    data = json.loads(path.read_text())
    data["multipliers"] = list(data["multipliers"])
    data["multipliers"][0] = 1 if data["multipliers"][0] != 1 else 2
    data["multiplier_spec_id"] = "0" * 64
    path.write_text(json.dumps(data))
    _resign(out)
    with pytest.raises(ValueError, match="candidate/codebook/policy replay"):
        lane.verify(out, config=lane.CANARY_R1B, verifier_runner=failed_r1b, _test_only=True)


def test_r1b_verified_report_payload_feeds_controller_gate(monkeypatch):
    _noiseless_r1b(monkeypatch)
    out = _out("r1b_controller_bridge")
    lane.create_plan(out, config=lane.CANARY_R1B, _test_only=True)
    lane.run(out, config=lane.CANARY_R1B, runner=success_r1b, _test_only=True)
    replay = lane.verify(out, config=lane.CANARY_R1B, verifier_runner=success_r1b, _test_only=True)
    assert replay["verified"]
    payload = lane.verified_report_payload(lane.CANARY_R1B, out,
                                           replay_report_sha256=ladder._sha(ladder._compact(replay)))
    assert payload["stage"] == "canary"
    assert payload["per_stratum"] == {f"{p:.2f}": {"frames": 4, "verified_success": 4,
                                                   "forbidden_failures": 0,
                                                   "key_dependent_bits_excluding_tag": 1700,
                                                   "symbols_per_frame": 256}
                                      for p in (0.20, 0.30)}
    assert ladder.canary_gate_failed(payload) is False


# ---------------------------------------------------------------- R2 QSC-DE lane (V7-20)

def _config_r2(frames=8, source_files=lane._SRC_R2):
    return lane.DevelopmentConfig(
        run_id="nbldpc_v7_r2_development_engineering_test", canonical_schema="NBLDPC7R2DEV",
        method=lane.METHOD_R2, q=1024, n=1024, ps=(.20, .30),
        roots={("development", .20): 202608041400, ("development", .30): 202608041500},
        caps=lane.CAPS_R2, seed_bits=lane.SEED_BITS_R2, development_frames=frames,
        source_files=tuple(source_files), contract=lane.CONTRACT)


TEST_CONFIG_R2 = _config_r2()


def failed_r2(bob, syndrome, manifest, matrices, *, check_count, p):
    return {"status": "decode_failed", "iterations": 1}


def success_r2(bob, syndrome, manifest, matrices, *, check_count, p):
    return {"status": "syndrome_consistent", "iterations": 1, "decoded_symbols": tuple(bob)}


def _noiseless_r2(monkeypatch):
    original = lane._frame
    def noiseless(config, p, index):
        row = original(config, p, index)
        row["alice"] = [0] * 1024
        row["bob"] = [0] * 1024
        return row
    monkeypatch.setattr(lane, "_frame", noiseless)


def test_r2_config_identity_and_disjoint_roots():
    canary = lane.CANARY_R2
    assert canary.run_id == "20260802_v1_nbldpc_v7_r2_canary"
    assert canary.canonical_schema == "NBLDPC7R2DEV"
    assert canary.method == lane.METHOD_R2 == "nbldpc_formal_v7_r2_qsc_de"
    assert canary.q == 1024 and canary.n == 1024 and canary.ps == (.20, .30)
    assert canary.caps == lane.CAPS_R2 and canary.seed_bits == lane.SEED_BITS_R2 == 1024 * 10 + 63
    assert canary.development_frames == 4
    development = lane.DEVELOPMENT_R2
    assert development.run_id == "20260802_v1_nbldpc_v7_r2_development"
    assert development.development_frames == 16
    assert lane.check_count(.20, canary) == 321 and lane.check_count(.30, canary) == 458
    # R2 roots are disjoint from R1A/R1B roots and from each other.
    r2_roots = set(canary.roots.values()) | set(development.roots.values())
    r1_roots = set(lane.CANARY.roots.values()) | set(lane.DEVELOPMENT.roots.values()) \
        | set(lane.CANARY_R1B.roots.values()) | set(lane.DEVELOPMENT_R1B.roots.values())
    assert r2_roots.isdisjoint(r1_roots)
    assert set(canary.roots.values()).isdisjoint(set(development.roots.values()))
    assert set(canary.roots.values()) == {202608041000, 202608041100}
    assert set(development.roots.values()) == {202608041200, 202608041300}


def test_r2_plan_is_development_only_with_fresh_roots():
    out = _out("r2_plan")
    plan = lane.create_plan(out, config=lane.CANARY_R2, _test_only=True)
    assert plan["run_id"] == "20260802_v1_nbldpc_v7_r2_canary"
    assert len(plan["frames"]) == 8
    assert [f["p"] for f in plan["frames"]] == [.2] * 4 + [.3] * 4
    assert all(f["role"] == "development" for f in plan["frames"])
    assert all(len(f["alice"]) == 1024 and len(f["bob"]) == 1024 for f in plan["frames"])
    assert "confirmation" not in json.dumps(plan["frames"])
    assert not any(plan["identity_overlap"].values())
    assert plan["provenance"]["codebook_manifest_id"] == \
        lane.codebook(lane.CANARY_R2)[0]["manifest_id"]


def test_r2_plan_gate_canary_only_and_r2_development_run_still_blocked():
    # V7-22: after the R2 canary plan review, CANARY_R2 plan preparation is
    # authorized; DEVELOPMENT_R2 still refuses.  R2 DEVELOPMENT production
    # execution is still never authorized (even with the production flag);
    # the R2 sacrificed CANARY may execute only through the canary-only
    # authorization test below (mirror of the R1A/R1B gates).
    out = _out("r2_canary_authorized")
    plan = lane.create_plan(out, config=lane.CANARY_R2, production_authorized=True)
    assert plan["run_id"] == "20260802_v1_nbldpc_v7_r2_canary"
    assert not any(plan["identity_overlap"].values())
    with pytest.raises(ValueError, match="not authorized"):
        lane.create_plan(_out("r2_dev_authorized"), config=lane.DEVELOPMENT_R2,
                         production_authorized=True)
    # bare (no production flag) run() raises for every R2 config.
    with pytest.raises(ValueError, match="not authorized"):
        lane.run(Path("unused"), config=lane.CANARY_R2, runner=failed_r2, _test_only=False)
    with pytest.raises(ValueError, match="R2 development execution is blocked"):
        lane.run(Path("unused"), config=lane.DEVELOPMENT_R2, runner=failed_r2, _test_only=False)
    # DEVELOPMENT_R2 production execution still raises even with the flag.
    with pytest.raises(ValueError, match="R2 development execution is blocked"):
        lane.run(None, config=lane.DEVELOPMENT_R2, runner=failed_r2,
                 production_authorized=True)
    # non-R2 configs still hit the generic development-authorization gate.
    with pytest.raises(ValueError, match="not authorized"):
        lane.run(Path("unused"), config=lane.CONFIG, runner=failed_r2, _test_only=False)


def test_v7_22_r2_canary_production_execution_authorization_is_canary_only():
    # V7-22 second half: R2 production execution is authorized only for the
    # sacrificed CANARY_R2 config, with an explicit non-official workspace
    # output and an explicit production runner.  The DEVELOPMENT_R2 config
    # and any bare (unauthorized) call still raise.
    with pytest.raises(ValueError, match="R2 development execution is blocked"):
        lane.run(None, config=lane.DEVELOPMENT_R2, runner=lane.production_runner_r2,
                 production_authorized=True)
    with pytest.raises(ValueError, match="R2 development execution is blocked"):
        lane.run(Path("unused"), config=lane.DEVELOPMENT_R2, runner=lane.production_runner_r2,
                 _test_only=False)
    with pytest.raises(ValueError, match="explicit workspace output"):
        lane.run(None, config=lane.CANARY_R2, runner=lane.production_runner_r2,
                 production_authorized=True)
    with pytest.raises(ValueError, match="explicit production runner"):
        lane.run(Path("unused"), config=lane.CANARY_R2, runner=None,
                 production_authorized=True)
    with pytest.raises(ValueError, match="not authorized"):
        lane.run(Path("unused"), config=lane.CANARY_R2, runner=lane.production_runner_r2,
                 _test_only=False)


def test_r2_fake_canary_never_enters_production_decoder(monkeypatch):
    out = _out("r2_trap")
    lane.create_plan(out, config=lane.CANARY_R2, _test_only=True)
    def trap(*args, **kwargs):
        raise AssertionError("production decoder entered")
    monkeypatch.setattr(lane, "production_runner", trap)
    monkeypatch.setattr(lane, "production_runner_r2", trap)
    got = lane.run(out, config=lane.CANARY_R2, runner=failed_r2, _test_only=True)
    assert got["run_status"] == "development_completed"
    assert lane.verify(out, config=lane.CANARY_R2, verifier_runner=failed_r2,
                       _test_only=True)["verified"]


def test_r2_fake_canary_package_and_strict_replay(monkeypatch):
    _noiseless_r2(monkeypatch)
    out = _out("r2_fake_success")
    lane.create_plan(out, config=lane.CANARY_R2, _test_only=True)
    got = lane.run(out, config=lane.CANARY_R2, runner=success_r2, _test_only=True)
    assert got["run_status"] == "development_completed" and got["promoted"] is False
    assert {p.name for p in out.iterdir()} == set(lane.ARTIFACTS)
    rows = lane._rows(out / "formal_frame_outcomes.csv")
    assert len(rows) == 8 and all(r["status"] == "verified_success" for r in rows)
    # disclosure accounting: 10*m bits (3210 / 4580) plus one invoked 64-bit tag.
    assert all(int(r["key_dependent_disclosure_bits_total"]) == 10 * 321 + 64
               for r in rows if r["stratum_p"] == "0.2")
    assert all(int(r["key_dependent_disclosure_bits_total"]) == 10 * 458 + 64
               for r in rows if r["stratum_p"] == "0.3")
    report = json.loads((out / "formal_qualification_report.json").read_text())
    assert report["per_stratum_verified_success"] == {"0.20": 4, "0.30": 4}
    assert lane.verify(out, config=lane.CANARY_R2, verifier_runner=success_r2,
                       _test_only=True)["verified"]


def test_r2_policy_manifest_records_the_frozen_de_selection(monkeypatch):
    _noiseless_r2(monkeypatch)
    out = _out("r2_policy")
    lane.create_plan(out, config=lane.CANARY_R2, _test_only=True)
    lane.run(out, config=lane.CANARY_R2, runner=success_r2, _test_only=True)
    policy = json.loads((out / "formal_policy_manifest.json").read_text())
    assert policy["policy_id"] == "nbldpc_v7_r2_qsc_de"
    assert policy["selection"]["method"] == "qary_density_evolution"
    assert policy["selection"]["check_count_freeze"] == {"0.2": 321, "0.3": 458}
    assert policy["selection"]["threshold_proxies"] == {"0.2": 0.19058, "0.3": 0.29373}
    assert policy["selection"]["n_candidates_max"] == 32
    assert lane.verify(out, config=lane.CANARY_R2, verifier_runner=success_r2,
                       _test_only=True)["verified"]


def test_r2_codebook_tamper_rejected_in_package(monkeypatch):
    _noiseless_r2(monkeypatch)
    out = _out("r2_cb_tamper")
    lane.create_plan(out, config=lane.CANARY_R2, _test_only=True)
    lane.run(out, config=lane.CANARY_R2, runner=success_r2, _test_only=True)
    path = out / "formal_codebook_manifest.json"
    data = json.loads(path.read_text())
    data["ordered_entries"] = [dict(e) for e in data["ordered_entries"]]
    data["ordered_entries"][0]["construction_seed"] = 1
    path.write_text(json.dumps(data))
    _resign(out)
    with pytest.raises(ValueError, match="candidate/codebook/policy replay"):
        lane.verify(out, config=lane.CANARY_R2, verifier_runner=success_r2, _test_only=True)


def test_r2_verified_report_payload_feeds_controller_gate(monkeypatch):
    _noiseless_r2(monkeypatch)
    out = _out("r2_controller_bridge")
    lane.create_plan(out, config=lane.CANARY_R2, _test_only=True)
    lane.run(out, config=lane.CANARY_R2, runner=success_r2, _test_only=True)
    replay = lane.verify(out, config=lane.CANARY_R2, verifier_runner=success_r2, _test_only=True)
    assert replay["verified"]
    payload = lane.verified_report_payload(lane.CANARY_R2, out,
                                           replay_report_sha256=ladder._sha(ladder._compact(replay)))
    assert payload["stage"] == "canary"
    assert payload["per_stratum"] == {f"{p:.2f}": {"frames": 4, "verified_success": 4,
                                                   "forbidden_failures": 0,
                                                   "key_dependent_bits_excluding_tag": 3210 if p == 0.20 else 4580,
                                                   "symbols_per_frame": 1024}
                                      for p in (0.20, 0.30)}
    assert ladder.canary_gate_failed(payload) is False


# ---------------------------------------------------------------- R3 GF(32)xGF(32) multilevel lane (V7-30)

def _config_r3(frames=8, source_files=lane._SRC_R3):
    return lane.DevelopmentConfig(
        run_id="nbldpc_v7_r3_development_engineering_test", canonical_schema="NBLDPC7R3DEV",
        method=lane.METHOD_R3, q=1024, n=1024, ps=(.20, .30),
        roots={("development", .20): 202608050400, ("development", .30): 202608050500},
        caps=lane.CAPS_R3, seed_bits=lane.SEED_BITS_R3, development_frames=frames,
        source_files=tuple(source_files), contract=lane.CONTRACT)


TEST_CONFIG_R3 = _config_r3()


def failed_r3(bob, syndrome0, syndrome1, manifest, matrices, *, check_count, p):
    return {"status": "decode_failed", "iterations": 1,
            "layer0_consistent": False, "layer1_consistent": False, "layer1_invoked": False}


def failed_layer1_r3(bob, syndrome0, syndrome1, manifest, matrices, *, check_count, p):
    return {"status": "decode_failed", "iterations": 2,
            "layer0_consistent": True, "layer1_consistent": False, "layer1_invoked": True}


def success_r3(bob, syndrome0, syndrome1, manifest, matrices, *, check_count, p):
    return {"status": "syndrome_consistent", "iterations": 1, "decoded_symbols": tuple(bob)}


def _noiseless_r3(monkeypatch):
    original = lane._frame
    def noiseless(config, p, index):
        row = original(config, p, index)
        row["alice"] = [0] * 1024
        row["bob"] = [0] * 1024
        return row
    monkeypatch.setattr(lane, "_frame", noiseless)


def test_r3_config_identity_and_disjoint_roots():
    canary = lane.CANARY_R3
    assert canary.run_id == "20260802_v1_nbldpc_v7_r3_canary"
    assert canary.canonical_schema == "NBLDPC7R3DEV"
    assert canary.method == lane.METHOD_R3 == "nbldpc_formal_v7_r3_gf32x2"
    assert canary.q == 1024 and canary.n == 1024 and canary.ps == (.20, .30)
    assert canary.caps == lane.CAPS_R3 and canary.seed_bits == lane.SEED_BITS_R3 == 1024 * 10 + 63
    assert canary.development_frames == 4
    development = lane.DEVELOPMENT_R3
    assert development.run_id == "20260802_v1_nbldpc_v7_r3_development"
    assert development.development_frames == 16
    # R3 rows carry the TOTAL per-frame check count m0 + m1.
    assert lane.check_count(.20, canary) == 404 + 404 and lane.check_count(.30, canary) == 558 + 558
    # R3 roots are disjoint from every R1A/R1B/R2 root, from each other and
    # from the frozen R3 construction seeds (202608050001/202608050002).
    r3_roots = set(canary.roots.values()) | set(development.roots.values())
    prior_roots = (set(lane.CANARY.roots.values()) | set(lane.DEVELOPMENT.roots.values())
                   | set(lane.CANARY_R1B.roots.values()) | set(lane.DEVELOPMENT_R1B.roots.values())
                   | set(lane.CANARY_R2.roots.values()) | set(lane.DEVELOPMENT_R2.roots.values()))
    assert r3_roots.isdisjoint(prior_roots)
    assert set(canary.roots.values()).isdisjoint(set(development.roots.values()))
    assert set(canary.roots.values()) == {202608050000, 202608050100}
    assert set(development.roots.values()) == {202608050200, 202608050300}
    assert r3_roots.isdisjoint({202608050001, 202608050002})


def test_r3_plan_is_development_only_with_fresh_roots():
    out = _out("r3_plan")
    plan = lane.create_plan(out, config=lane.CANARY_R3, _test_only=True)
    assert plan["run_id"] == "20260802_v1_nbldpc_v7_r3_canary"
    assert len(plan["frames"]) == 8
    assert [f["p"] for f in plan["frames"]] == [.2] * 4 + [.3] * 4
    assert all(f["role"] == "development" for f in plan["frames"])
    assert all(len(f["alice"]) == 1024 and len(f["bob"]) == 1024 for f in plan["frames"])
    assert "confirmation" not in json.dumps(plan["frames"])
    assert not any(plan["identity_overlap"].values())
    assert plan["provenance"]["codebook_manifest_id"] == \
        lane.codebook(lane.CANARY_R3)[0]["manifest_id"]


def test_r3_plan_gate_canary_only_and_r3_development_run_still_blocked():
    # V7-32: after the R3 canary plan review, CANARY_R3 plan preparation is
    # authorized; DEVELOPMENT_R3 still refuses.  R3 DEVELOPMENT production
    # execution is still never authorized (even with the production flag);
    # the R3 sacrificed CANARY may execute only through the canary-only
    # authorization test below (mirror of the R1A/R1B/R2 gates).
    out = _out("r3_canary_authorized")
    plan = lane.create_plan(out, config=lane.CANARY_R3, production_authorized=True)
    assert plan["run_id"] == "20260802_v1_nbldpc_v7_r3_canary"
    assert not any(plan["identity_overlap"].values())
    with pytest.raises(ValueError, match="not authorized"):
        lane.create_plan(_out("r3_dev_authorized"), config=lane.DEVELOPMENT_R3,
                         production_authorized=True)
    # bare (no production flag) run() raises for every R3 config.
    with pytest.raises(ValueError, match="not authorized"):
        lane.run(Path("unused"), config=lane.CANARY_R3, runner=failed_r3, _test_only=False)
    with pytest.raises(ValueError, match="R3 development execution is blocked"):
        lane.run(Path("unused"), config=lane.DEVELOPMENT_R3, runner=failed_r3, _test_only=False)
    # DEVELOPMENT_R3 production execution still raises even with the flag.
    with pytest.raises(ValueError, match="R3 development execution is blocked"):
        lane.run(None, config=lane.DEVELOPMENT_R3, runner=failed_r3,
                 production_authorized=True)


def test_v7_32_r3_canary_production_execution_authorization_is_canary_only():
    # V7-32 second half: R3 production execution is authorized only for the
    # sacrificed CANARY_R3 config, with an explicit non-official workspace
    # output and an explicit production runner.  The DEVELOPMENT_R3 config
    # and any bare (unauthorized) call still raise (mirror of R1A/R1B/R2).
    with pytest.raises(ValueError, match="R3 development execution is blocked"):
        lane.run(None, config=lane.DEVELOPMENT_R3, runner=lane.production_runner_r3,
                 production_authorized=True)
    with pytest.raises(ValueError, match="R3 development execution is blocked"):
        lane.run(Path("unused"), config=lane.DEVELOPMENT_R3, runner=lane.production_runner_r3,
                 _test_only=False)
    with pytest.raises(ValueError, match="explicit workspace output"):
        lane.run(None, config=lane.CANARY_R3, runner=lane.production_runner_r3,
                 production_authorized=True)
    with pytest.raises(ValueError, match="explicit production runner"):
        lane.run(Path("unused"), config=lane.CANARY_R3, runner=None,
                 production_authorized=True)
    with pytest.raises(ValueError, match="not authorized"):
        lane.run(Path("unused"), config=lane.CANARY_R3, runner=lane.production_runner_r3,
                 _test_only=False)
    # (d) CANARY_R3 + production_authorized + explicit output + explicit fake
    # runner is NOT blocked by the R3 gate: the fake fails fast and the run
    # completes development_completed without ever entering the production
    # decoder (explicit fake runner, workspace fixture output only).
    out = _out("r3_canary_exec_auth")
    lane.create_plan(out, config=lane.CANARY_R3, production_authorized=True)
    got = lane.run(out, config=lane.CANARY_R3, runner=failed_r3, production_authorized=True)
    assert got["run_status"] == "development_completed" and got["outcome_count"] == 8


def test_r3_official_root_is_locked_and_never_created():
    for config in (TEST_CONFIG_R3, lane.CANARY_R3, lane.DEVELOPMENT_R3):
        official = lane._official(config)
        assert not official.exists()
        with pytest.raises(ValueError, match="locked"):
            lane.create_plan(str(official), config=config, _test_only=True)
        assert not official.exists()


def test_r3_fake_canary_never_enters_production_decoder(monkeypatch):
    out = _out("r3_trap")
    lane.create_plan(out, config=lane.CANARY_R3, _test_only=True)
    def trap(*args, **kwargs):
        raise AssertionError("production decoder entered")
    monkeypatch.setattr(lane, "production_runner", trap)
    monkeypatch.setattr(lane, "production_runner_r3", trap)
    got = lane.run(out, config=lane.CANARY_R3, runner=failed_r3, _test_only=True)
    assert got["run_status"] == "development_completed"
    assert lane.verify(out, config=lane.CANARY_R3, verifier_runner=failed_r3,
                       _test_only=True)["verified"]


def test_r3_fake_canary_package_and_strict_replay(monkeypatch):
    _noiseless_r3(monkeypatch)
    out = _out("r3_fake_success")
    lane.create_plan(out, config=lane.CANARY_R3, _test_only=True)
    got = lane.run(out, config=lane.CANARY_R3, runner=success_r3, _test_only=True)
    assert got["run_status"] == "development_completed" and got["promoted"] is False
    assert {p.name for p in out.iterdir()} == set(lane.ARTIFACTS)
    rows = lane._rows(out / "formal_frame_outcomes.csv")
    assert len(rows) == 8 and all(r["status"] == "verified_success" for r in rows)
    # joint tag accounting: BOTH layer syndromes count (5 bits per GF(32)
    # check) plus one invoked 64-bit tag: 5*808+64 = 4104 / 5*1116+64 = 5644.
    assert all(int(r["key_dependent_disclosure_bits_total"]) == 5 * 808 + 64
               for r in rows if r["stratum_p"] == "0.2")
    assert all(int(r["key_dependent_disclosure_bits_total"]) == 5 * 1116 + 64
               for r in rows if r["stratum_p"] == "0.3")
    report = json.loads((out / "formal_qualification_report.json").read_text())
    assert report["per_stratum_verified_success"] == {"0.20": 4, "0.30": 4}
    assert lane.verify(out, config=lane.CANARY_R3, verifier_runner=success_r3,
                       _test_only=True)["verified"]


def test_r3_failed_layer0_package_short_circuits_disclosure_and_events(monkeypatch):
    _noiseless_r3(monkeypatch)
    out = _out("r3_failed_layer0")
    lane.create_plan(out, config=lane.CANARY_R3, _test_only=True)
    lane.run(out, config=lane.CANARY_R3, runner=failed_r3, _test_only=True)
    rows = lane._rows(out / "formal_frame_outcomes.csv")
    assert len(rows) == 8 and all(r["status"] == "decode_failed" for r in rows)
    assert all(r["verification_attempts"] == "0" for r in rows)
    # failed layer 0 discloses ONLY the layer-0 syndrome (5*m0), never layer 1
    # and never the tag.
    assert all(int(r["key_dependent_disclosure_bits_total"]) == 5 * 404 for r in rows
               if r["stratum_p"] == "0.2")
    assert all(int(r["key_dependent_disclosure_bits_total"]) == 5 * 558 for r in rows
               if r["stratum_p"] == "0.3")
    events = [json.loads(line) for line in (out / "formal_transcript.jsonl").read_bytes().splitlines()]
    assert len(events) == 8 * 3
    assert all(e["event_type"] != "SYNDROME_INITIAL_LAYER1" for e in events)
    assert all(e["event_type"] != "DECODER_STAGE2" for e in events)
    assert all(e["event_type"] != "VERIFICATION_TAG_STAGE1" for e in events)
    assert lane.verify(out, config=lane.CANARY_R3, verifier_runner=failed_r3,
                       _test_only=True)["verified"]


def test_r3_failed_layer1_package_counts_both_layer_syndromes(monkeypatch):
    _noiseless_r3(monkeypatch)
    out = _out("r3_failed_layer1")
    lane.create_plan(out, config=lane.CANARY_R3, _test_only=True)
    lane.run(out, config=lane.CANARY_R3, runner=failed_layer1_r3, _test_only=True)
    rows = lane._rows(out / "formal_frame_outcomes.csv")
    assert len(rows) == 8 and all(r["status"] == "decode_failed" for r in rows)
    # layer 0 consistent -> BOTH layer syndromes count (5*(m0+m1)); no tag.
    assert all(int(r["key_dependent_disclosure_bits_total"]) == 5 * 808 for r in rows
               if r["stratum_p"] == "0.2")
    assert all(int(r["key_dependent_disclosure_bits_total"]) == 5 * 1116 for r in rows
               if r["stratum_p"] == "0.3")
    events = [json.loads(line) for line in (out / "formal_transcript.jsonl").read_bytes().splitlines()]
    assert len(events) == 8 * 5
    assert all(any(e["event_type"] == "SYNDROME_INITIAL_LAYER1" for e in events[i * 5:(i + 1) * 5])
               for i in range(8))
    assert all(e["event_type"] != "VERIFICATION_TAG_STAGE1" for e in events)
    assert lane.verify(out, config=lane.CANARY_R3, verifier_runner=failed_layer1_r3,
                       _test_only=True)["verified"]


def test_r3_transcript_never_records_cross_layer_symbols(monkeypatch):
    _noiseless_r3(monkeypatch)
    out = _out("r3_transcript")
    lane.create_plan(out, config=lane.CANARY_R3, _test_only=True)
    lane.run(out, config=lane.CANARY_R3, runner=success_r3, _test_only=True)
    events = [json.loads(line) for line in (out / "formal_transcript.jsonl").read_bytes().splitlines()]
    # both layer syndromes are recorded as public syndrome values only; raw
    # 10-bit symbols, high/low words, and corrected symbols never enter any
    # event payload (cross-layer leakage discipline).  The "high"/"low" words
    # inside the public layer-descriptor notes are labels, not symbol data.
    assert "decoded_symbols" not in json.dumps(events)
    for event in events:
        payload = event["payload"]
        assert not set(payload).intersection(lane._FORBIDDEN)
        for key in ("alice", "bob", "high", "low", "decoded"):
            assert key not in payload
        # the only symbol-length vectors ever recorded are the GF(32) layer
        # syndromes (m0 / m1 entries), never a 1024-entry 10-bit symbol vector.
        syndrome = payload.get("syndrome")
        if syndrome is not None:
            assert len(syndrome) in (404, 558)
    assert len([e for e in events if e["event_type"] == "SYNDROME_INITIAL"]) == 8
    assert len([e for e in events if e["event_type"] == "SYNDROME_INITIAL_LAYER1"]) == 8
    assert len([e for e in events if e["event_type"] == "VERIFICATION_TAG_STAGE1"]) == 8
    assert lane.verify(out, config=lane.CANARY_R3, verifier_runner=success_r3,
                       _test_only=True)["verified"]


def test_r3_policy_manifest_records_the_frozen_two_layer_choice(monkeypatch):
    _noiseless_r3(monkeypatch)
    out = _out("r3_policy")
    lane.create_plan(out, config=lane.CANARY_R3, _test_only=True)
    lane.run(out, config=lane.CANARY_R3, runner=success_r3, _test_only=True)
    policy = json.loads((out / "formal_policy_manifest.json").read_text())
    assert policy["policy_id"] == "nbldpc_v7_r3_gf32x2"
    assert policy["decoder"] == "ems_nm32_gf32_two_layer_flooding_l0_first_l1_conditional"
    assert policy["nm"] == 32 and policy["max_iter"] == 100 and policy["lambda"] == 0.75
    assert policy["schedule"] == "flooding" and policy["workers"] == 1
    assert policy["verification"] == "single_64_bit_toeplitz_tag_on_reconstructed_10_bit_symbols"
    assert policy["check_count_freeze"] == {"0.2": {"m0": 404, "m1": 404},
                                            "0.3": {"m0": 558, "m1": 558}}
    assert lane.verify(out, config=lane.CANARY_R3, verifier_runner=success_r3,
                       _test_only=True)["verified"]


def test_r3_codebook_tamper_rejected_in_package(monkeypatch):
    _noiseless_r3(monkeypatch)
    out = _out("r3_cb_tamper")
    lane.create_plan(out, config=lane.CANARY_R3, _test_only=True)
    lane.run(out, config=lane.CANARY_R3, runner=success_r3, _test_only=True)
    path = out / "formal_codebook_manifest.json"
    data = json.loads(path.read_text())
    data["ordered_entries"] = [dict(e) for e in data["ordered_entries"]]
    data["ordered_entries"][0]["construction_seed_0"] = 1
    path.write_text(json.dumps(data))
    _resign(out)
    with pytest.raises(ValueError, match="candidate/codebook/policy replay"):
        lane.verify(out, config=lane.CANARY_R3, verifier_runner=success_r3, _test_only=True)


def test_r3_verified_report_payload_feeds_controller_gate(monkeypatch):
    _noiseless_r3(monkeypatch)
    out = _out("r3_controller_bridge")
    lane.create_plan(out, config=lane.CANARY_R3, _test_only=True)
    lane.run(out, config=lane.CANARY_R3, runner=success_r3, _test_only=True)
    replay = lane.verify(out, config=lane.CANARY_R3, verifier_runner=success_r3, _test_only=True)
    assert replay["verified"]
    payload = lane.verified_report_payload(lane.CANARY_R3, out,
                                           replay_report_sha256=ladder._sha(ladder._compact(replay)))
    assert payload["stage"] == "canary"
    assert payload["per_stratum"] == {f"{p:.2f}": {"frames": 4, "verified_success": 4,
                                                   "forbidden_failures": 0,
                                                   "key_dependent_bits_excluding_tag": 4040 if p == 0.20 else 5580,
                                                   "symbols_per_frame": 1024}
                                      for p in (0.20, 0.30)}
    assert ladder.canary_gate_failed(payload) is False
