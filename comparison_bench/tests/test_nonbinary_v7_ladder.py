"""V7 shared ladder controller acceptance (V7-01/V7-02): state transitions,
hash-bound immutable verified reports, crash/resume from immutable artifacts,
exactly-once execute/replay, no-rerun, freshness, fake-runner advance from a
verified report, and the frozen canary/development gates."""
from __future__ import annotations
import json
import uuid
from pathlib import Path
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_ladder as ladder
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_development as lane


def _report(event, payload):
    return {"event": event, "payload": payload, "report_sha256": ladder._sha(ladder._compact(payload))}


def _engineered():
    return _report("engineered", {"engineering_acceptance_sha256": "e" * 64,
                                  "tiers": {t: {"passed": 1, "failed": 0}
                                            for t in ("T0", "T1", "T2", "T3")}})


def _planned_canary():
    return _report("planned", {"stage": "canary", "plan_sha256": "p" * 64, "frame_count": 8,
                               "roots": {"development|0.2": 202608047000, "development|0.3": 202608047100}})


def _executed(manifest="r"):
    return _report("executed", {"run_manifest_sha256": manifest * 64})


def _verified(replay="v"):
    return _report("verified", {"replay_report_sha256": replay * 64})


def _planned_development(replay="v"):
    return _report("planned", {"stage": "development", "plan_sha256": "q" * 64, "frame_count": 32,
                               "roots": {"development|0.2": 202608048000, "development|0.3": 202608048100},
                               "per_stratum": {f"{p:.2f}": {"frames": 4, "verified_success": 4,
                                                            "forbidden_failures": 0}
                                               for p in (0.20, 0.30)},
                               "replay_report_sha256": replay * 64})


def _canary_gate_payload(replay="v", per_stratum=None):
    per = per_stratum or {f"{p:.2f}": {"frames": 4, "verified_success": 4, "forbidden_failures": 0}
                          for p in (0.20, 0.30)}
    return {"stage": "canary", "per_stratum": per, "strict_replay_verified": True,
            "median_runtime_seconds": 10.0, "replay_report_sha256": replay * 64}


def _development_gate_payload(replay="v", *, per_stratum=None, strict=True, median=10.0):
    per = per_stratum or {f"{p:.2f}": {"frames": 16, "verified_success": 16, "forbidden_failures": 0,
                                       "key_dependent_bits_excluding_tag": 1700, "symbols_per_frame": 256}
                          for p in (0.20, 0.30)}
    return {"stage": "development", "per_stratum": per, "strict_replay_verified": strict,
            "median_runtime_seconds": median, "replay_report_sha256": replay * 64}


def _stratum(frames, verified, forbidden=0, disclosure=1700, symbols=256):
    return {"frames": frames, "verified_success": verified, "forbidden_failures": forbidden,
            "key_dependent_bits_excluding_tag": disclosure, "symbols_per_frame": symbols}


def _tmp(name):
    root = Path("workspace") / "nbldpc_v7_r1a" / uuid.uuid4().hex / name
    root.parent.mkdir(parents=True, exist_ok=True)
    return root


# ---------------------------------------------------------------- transitions

def test_initial_state_and_statuses_and_no_confirmation_status():
    state = ladder.initial_state("r1a")
    assert state["status"] == "pending" and state["stage"] is None
    assert state["execute_count"] == 0 and state["replay_count"] == 0
    assert ladder.statuses(ladder.initial_ladder()) == {r: "pending" for r in ladder.ROUTES}
    assert "confirmed" not in ladder.STATUSES
    assert not any("confirm" in event for successors in ladder.TRANSITIONS.values() for event in successors)
    for route in ladder.ROUTES:
        assert ladder.initial_state(route)["status"] == "pending"


def test_hash_bound_report_is_required():
    state = ladder.initial_state("r1a")
    report = _engineered()
    report["report_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash binding"):
        ladder.advance(state, report)
    tampered = _engineered()
    tampered["payload"] = dict(tampered["payload"], engineering_acceptance_sha256="1" * 64)
    with pytest.raises(ValueError, match="hash binding"):
        ladder.advance(state, tampered)
    with pytest.raises(ValueError, match="report must contain"):
        ladder.advance(state, {"event": "engineered"})
    # a valid report must not mutate the caller's state.
    advanced = ladder.advance(state, _engineered())
    assert state["status"] == "pending" and advanced["status"] == "engineered"


def test_invalid_transitions_rejected():
    state = ladder.initial_state("r1a")
    with pytest.raises(ValueError, match="invalid transition"):
        ladder.advance(state, _planned_canary())
    state = ladder.advance(state, _engineered())
    with pytest.raises(ValueError, match="invalid transition"):
        ladder.advance(state, _executed())
    state = ladder.advance(state, _planned_canary())
    with pytest.raises(ValueError, match="invalid transition"):
        ladder.advance(state, _verified())
    # engineered payload structure is enforced.
    state = ladder.initial_state("r1a")
    with pytest.raises(ValueError, match="tier"):
        ladder.advance(state, _report("engineered", {"engineering_acceptance_sha256": "e" * 64,
                                                     "tiers": {"T0": {"passed": 1, "failed": 1}}}))
    # first plan must be the 4+4 canary.
    engineered = ladder.advance(ladder.initial_state("r1a"), _engineered())
    with pytest.raises(ValueError, match="4\\+4 canary"):
        ladder.advance(engineered, _planned_development())


def test_full_transition_chain_to_ready():
    state = ladder.initial_state("r1a")
    state = ladder.advance(state, _engineered())
    state = ladder.advance(state, _planned_canary())
    state = ladder.advance(state, _executed())
    state = ladder.advance(state, _verified())
    assert state["status"] == "verified" and state["stage"] == "canary"
    assert state["execute_count"] == 1 and state["replay_count"] == 1
    # canary passed (4/4 both strata) -> development plan.
    state = ladder.advance(state, _planned_development())
    assert state["status"] == "planned" and state["stage"] == "development" and state["stage_count"] == 2
    state = ladder.advance(state, _executed(manifest="s"))
    state = ladder.advance(state, _verified(replay="w"))
    state = ladder.advance(state, _report("ready", _development_gate_payload(replay="w")))
    assert state["status"] == "ready"
    assert state["artifacts"]["canary_plan"] == "p" * 64
    assert state["artifacts"]["development_replay"] == "w" * 64


def test_exactly_once_execute_and_replay():
    state = ladder.advance(ladder.advance(ladder.advance(ladder.initial_state("r1a"), _engineered()),
                                          _planned_canary()), _executed())
    # a second execute on the executed status is structurally invalid (the
    # exactly-once budget is enforced by the frozen transition table).
    with pytest.raises(ValueError, match="invalid transition"):
        ladder.advance(state, _executed())
    state = ladder.advance(state, _verified())
    with pytest.raises(ValueError, match="invalid transition"):
        ladder.advance(state, _verified())
    # exactly-once planning is structural: a second planned on a planned
    # status is an invalid transition.
    engineered = ladder.advance(ladder.initial_state("r1a"), _engineered())
    state = ladder.advance(engineered, _planned_canary())
    with pytest.raises(ValueError, match="invalid transition"):
        ladder.advance(state, _planned_canary())


def test_no_rerun_after_terminal_status():
    failed = ladder.advance(ladder.advance(ladder.advance(
        ladder.advance(ladder.initial_state("r1a"), _engineered()), _planned_canary()),
        _executed()), _verified())
    failed = ladder.advance(failed, _report("failed_canary", _canary_gate_payload(per_stratum={
        f"{p:.2f}": {"frames": 4, "verified_success": 0, "forbidden_failures": 0} for p in (0.20, 0.30)})))
    assert failed["status"] == "failed_canary"
    with pytest.raises(ValueError, match="invalid transition"):
        ladder.advance(failed, _engineered())
    blocked = ladder.advance(ladder.initial_state("r1a"),
                             _report("blocked", {"blocker": "density evolution oracle unavailable"}))
    assert blocked["status"] == "blocked" and blocked["blocker"].startswith("density")
    with pytest.raises(ValueError, match="invalid transition"):
        ladder.advance(blocked, _planned_canary())
    with pytest.raises(ValueError, match="blocker"):
        ladder.advance(ladder.initial_state("r1a"), _report("blocked", {"blocker": ""}))


# ---------------------------------------------------------------- gates

def test_canary_zero_of_four_gate_fires_failed_canary():
    zero_stratum = {f"{p:.2f}": {"frames": 4, "verified_success": 0, "forbidden_failures": 0}
                    for p in (0.20, 0.30)}
    assert ladder.canary_gate_failed(_canary_gate_payload(per_stratum=zero_stratum))
    state = ladder.advance(ladder.advance(ladder.advance(
        ladder.advance(ladder.initial_state("r1a"), _engineered()), _planned_canary()),
        _executed()), _verified())
    state = ladder.advance(state, _report("failed_canary", _canary_gate_payload(per_stratum=zero_stratum)))
    assert state["status"] == "failed_canary"
    # a 1/4 canary is NOT failed and must not be labelled failed_canary.
    one_stratum = {f"{p:.2f}": {"frames": 4, "verified_success": 1, "forbidden_failures": 0}
                   for p in (0.20, 0.30)}
    assert not ladder.canary_gate_failed(_canary_gate_payload(per_stratum=one_stratum))
    passed = ladder.advance(ladder.advance(ladder.advance(
        ladder.advance(ladder.initial_state("r1a"), _engineered()), _planned_canary()),
        _executed()), _verified())
    with pytest.raises(ValueError, match="0/4-in-either-stratum"):
        ladder.advance(passed, _report("failed_canary", _canary_gate_payload(per_stratum=one_stratum)))


def test_canary_with_successes_advances_to_development_plan():
    state = ladder.advance(ladder.advance(ladder.advance(
        ladder.advance(ladder.initial_state("r1a"), _engineered()), _planned_canary()),
        _executed()), _verified())
    state = ladder.advance(state, _planned_development())
    assert state["status"] == "planned" and state["stage"] == "development"


def test_development_ready_gate():
    ready = {"stage": "development", "per_stratum": {
        f"{p:.2f}": _stratum(16, 15 if p == 0.20 else 16) for p in (0.20, 0.30)},
        "strict_replay_verified": True, "median_runtime_seconds": 119.9,
        "replay_report_sha256": "w" * 64}
    assert ladder.development_ready(ready)
    state = ladder.advance(ladder.advance(ladder.advance(ladder.advance(
        ladder.advance(ladder.advance(ladder.initial_state("r1a"), _engineered()),
                       _planned_canary()), _executed()), _verified()), _planned_development()),
        _executed(manifest="s"))
    state = ladder.advance(state, _verified(replay="w"))
    state = ladder.advance(state, _report("ready", ready))
    assert state["status"] == "ready"


def test_development_gate_failures_map_to_non_ready():
    base = {f"{p:.2f}": _stratum(16, 16) for p in (0.20, 0.30)}
    cases = {
        "insufficient_success": {f"{p:.2f}": _stratum(16, 16 if p == 0.20 else 14) for p in (0.20, 0.30)},
        "forbidden_failure": {f"{p:.2f}": _stratum(16, 15, forbidden=1 if p == 0.20 else 0) for p in (0.20, 0.30)},
        "disclosure_over": {f"{p:.2f}": _stratum(16, 16, disclosure=2243) for p in (0.20, 0.30)},
    }
    for name, per in cases.items():
        payload = _development_gate_payload("w", per_stratum=per)
        assert not ladder.development_ready(payload), name
        state = ladder.advance(ladder.advance(ladder.advance(ladder.advance(
            ladder.advance(ladder.advance(ladder.initial_state("r1a"), _engineered()),
                           _planned_canary()), _executed()), _verified()), _planned_development()),
            _executed(manifest="s"))
        state = ladder.advance(state, _verified(replay="w"))
        state = ladder.advance(state, _report("non_ready", payload))
        assert state["status"] == "non_ready", name
    # strict replay missing and median runtime breach are also non-ready.
    for kwargs in ({"strict": False}, {"median": 121.0}):
        payload = _development_gate_payload("w", per_stratum=base, **kwargs)
        assert not ladder.development_ready(payload)
    # a gate event that passes must not be labelled non_ready.
    state = ladder.advance(ladder.advance(ladder.advance(ladder.advance(
        ladder.advance(ladder.advance(ladder.initial_state("r1a"), _engineered()),
                       _planned_canary()), _executed()), _verified()), _planned_development()),
        _executed(manifest="s"))
    state = ladder.advance(state, _verified(replay="w"))
    with pytest.raises(ValueError, match="development gate miss"):
        ladder.advance(state, _report("non_ready", _development_gate_payload("w")))


# ---------------------------------------------------------------- persistence

def test_crash_resume_roundtrip_from_immutable_artifact():
    state = ladder.advance(ladder.advance(ladder.initial_state("r1a"), _engineered()), _planned_canary())
    path = _tmp("state") / "ladder_state.json"
    state_hash = ladder.save_state(state, path)
    resumed = ladder.load_state(path)
    assert resumed == state
    assert state_hash == ladder._sha(ladder._compact(state))
    # byte tamper of the persisted artifact is rejected.
    document = json.loads(path.read_text())
    document["state"]["status"] = "verified"
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="hash binding"):
        ladder.load_state(path)


def test_ladder_persistence_roundtrip():
    ladder_state = ladder.initial_ladder()
    path = _tmp("ladder") / "ladder.json"
    ladder_hash = ladder.save_ladder(ladder_state, path)
    resumed = ladder.load_ladder(path)
    assert resumed == ladder_state
    assert ladder_hash == ladder._sha(ladder._compact(ladder_state))
    document = json.loads(path.read_text())
    document["ladder"]["r1a"]["status"] = "ready"
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="hash binding"):
        ladder.load_ladder(path)


def test_advance_ladder_preserves_other_subroutes():
    states = ladder.initial_ladder()
    states = ladder.advance_ladder(states, "r1a", _engineered())
    assert states["r1a"]["status"] == "engineered"
    assert states["r1b"]["status"] == "pending" and states["r2"]["status"] == "pending"
    with pytest.raises(ValueError, match="unknown subroute"):
        ladder.advance_ladder(states, "r9", _engineered())


def test_ladder_records_r1a_failed_canary_and_r1b_engineered():
    # R1B is authorized only after the R1A canary gate fires (V7-14): the
    # ladder must be able to hold R1A=failed_canary and R1B=engineered
    # simultaneously, with R2/R3 still pending.
    states = ladder.initial_ladder()
    states = ladder.advance_ladder(states, "r1a", _engineered())
    states = ladder.advance_ladder(states, "r1a", _planned_canary())
    states = ladder.advance_ladder(states, "r1a", _executed())
    states = ladder.advance_ladder(states, "r1a", _verified())
    failed_payload = _canary_gate_payload(per_stratum={
        f"{p:.2f}": {"frames": 4, "verified_success": 0, "forbidden_failures": 0} for p in (0.20, 0.30)})
    states = ladder.advance_ladder(states, "r1a", _report("failed_canary", failed_payload))
    states = ladder.advance_ladder(states, "r1b", _engineered())
    assert states["r1a"]["status"] == "failed_canary"
    assert states["r1b"]["status"] == "engineered"
    assert states["r1b"]["artifacts"]["engineering_acceptance"] == "e" * 64
    assert states["r2"]["status"] == "pending" and states["r3"]["status"] == "pending"
    # R1A is terminal: the ladder cannot plan/execute R1A development after
    # the failed canary; R1B cannot jump straight to execute before planning.
    with pytest.raises(ValueError, match="invalid transition"):
        ladder.advance_ladder(states, "r1a", _planned_development())
    with pytest.raises(ValueError, match="invalid transition"):
        ladder.advance_ladder(states, "r1b", _executed())


def test_ladder_records_r1a_r1b_failed_canary_and_r2_engineered():
    # R2 is authorized only after both R1A and R1B canary gates fire (V7-20):
    # the ladder must hold R1A=failed_canary, R1B=failed_canary and
    # R2=engineered simultaneously, with R3 still pending.
    states = ladder.initial_ladder()
    for route in ("r1a", "r1b"):
        states = ladder.advance_ladder(states, route, _engineered())
        states = ladder.advance_ladder(states, route, _planned_canary())
        states = ladder.advance_ladder(states, route, _executed())
        states = ladder.advance_ladder(states, route, _verified())
        failed_payload = _canary_gate_payload(per_stratum={
            f"{p:.2f}": {"frames": 4, "verified_success": 0, "forbidden_failures": 0}
            for p in (0.20, 0.30)})
        states = ladder.advance_ladder(states, route, _report("failed_canary", failed_payload))
    states = ladder.advance_ladder(states, "r2", _engineered())
    assert states["r1a"]["status"] == "failed_canary"
    assert states["r1b"]["status"] == "failed_canary"
    assert states["r2"]["status"] == "engineered"
    assert states["r2"]["artifacts"]["engineering_acceptance"] == "e" * 64
    assert states["r3"]["status"] == "pending"
    # both R1 routes are terminal: no development plan may follow.
    with pytest.raises(ValueError, match="invalid transition"):
        ladder.advance_ladder(states, "r1b", _planned_development())
    with pytest.raises(ValueError, match="invalid transition"):
        ladder.advance_ladder(states, "r2", _executed())


def test_ladder_records_r1a_r1b_r2_failed_canary_and_r3_engineered():
    # R3 is authorized only after the R1A, R1B and R2 canary gates all fire
    # (V7-30): the ladder must hold R1A=failed_canary, R1B=failed_canary,
    # R2=failed_canary and R3=engineered simultaneously.
    states = ladder.initial_ladder()
    for route in ("r1a", "r1b", "r2"):
        states = ladder.advance_ladder(states, route, _engineered())
        states = ladder.advance_ladder(states, route, _planned_canary())
        states = ladder.advance_ladder(states, route, _executed())
        states = ladder.advance_ladder(states, route, _verified())
        failed_payload = _canary_gate_payload(per_stratum={
            f"{p:.2f}": {"frames": 4, "verified_success": 0, "forbidden_failures": 0}
            for p in (0.20, 0.30)})
        states = ladder.advance_ladder(states, route, _report("failed_canary", failed_payload))
    states = ladder.advance_ladder(states, "r3", _engineered())
    assert states["r1a"]["status"] == "failed_canary"
    assert states["r1b"]["status"] == "failed_canary"
    assert states["r2"]["status"] == "failed_canary"
    assert states["r3"]["status"] == "engineered"
    assert states["r3"]["artifacts"]["engineering_acceptance"] == "e" * 64
    # every failed R1/R2 route is terminal: no development plan may follow,
    # and R3 cannot jump straight to execute before planning.
    with pytest.raises(ValueError, match="invalid transition"):
        ladder.advance_ladder(states, "r2", _planned_development())
    with pytest.raises(ValueError, match="invalid transition"):
        ladder.advance_ladder(states, "r3", _executed())


# ---------------------------------------------------------------- freshness

def test_freshness_roots_and_seeds_disjoint_from_all_prior_evidence():
    canary_roots = {str(x) for x in lane.CANARY.roots.values()}
    development_roots = {str(x) for x in lane.DEVELOPMENT.roots.values()}
    assert canary_roots.isdisjoint(development_roots)
    prior = lane._prior_identities()
    assert canary_roots.isdisjoint(prior["roots"])
    assert development_roots.isdisjoint(prior["roots"])
    frames = [lane._frame(lane.CANARY, p, i) for p in lane.CANARY.ps
              for i in range(lane.CANARY.development_frames)]
    assert not any(lane._identity_overlap(lane.CANARY, frames).values())
    plan = lane.expected_plan(lane.CANARY)
    ids = {record["seed_id"] for record in plan["development_toeplitz_seeds"].values()}
    assert len(ids) == 8
    assert ids.isdisjoint(lane._prior_seed_ids())
    development_plan = lane.expected_plan(lane.DEVELOPMENT)
    dev_ids = {record["seed_id"] for record in development_plan["development_toeplitz_seeds"].values()}
    assert len(dev_ids) == 32
    assert dev_ids.isdisjoint(lane._prior_seed_ids())
    assert ids.isdisjoint(dev_ids)


# ---------------------------------------------------------------- fake lifecycle -> controller (T2)

def _fake_canary_verified_chain(monkeypatch, runner, trap_production=True):
    """Build one complete fake canary package (4+4) under a fresh workspace
    root and advance the controller through the full immutable chain to the
    verified report; returns (controller_state, payload, package_dir)."""
    if trap_production:
        def trap(*args, **kwargs):
            raise AssertionError("production decoder entered")
        monkeypatch.setattr(lane, "production_runner", trap)
    out = _tmp("fake_canary") / "pkg"
    lane.create_plan(out, config=lane.CANARY, _test_only=True)
    assert lane.run(out, config=lane.CANARY, runner=runner, _test_only=True)["run_status"] == "development_completed"
    replay = lane.verify(out, config=lane.CANARY, verifier_runner=runner, _test_only=True)
    assert replay["verified"]
    replay_sha = ladder._sha(ladder._compact(replay))
    payload = lane.verified_report_payload(lane.CANARY, out, replay_report_sha256=replay_sha)
    state = ladder.initial_state("r1a")
    state = ladder.advance(state, _engineered())
    state = ladder.advance(state, _planned_canary())
    state = ladder.advance(state, _executed(manifest="m"))
    state = ladder.advance(state, _report("verified", {"replay_report_sha256": replay_sha}))
    assert state["status"] == "verified" and state["stage"] == "canary"
    return state, payload, out


def test_t2_fake_failed_canary_advances_controller_to_failed_canary(monkeypatch):
    def failed(bob, syndrome, manifest, matrices, *, check_count, p):
        return {"status": "decode_failed", "iterations": 1}
    state, payload, _ = _fake_canary_verified_chain(monkeypatch, failed)
    assert ladder.canary_gate_failed(payload)
    state = ladder.advance(state, _report("failed_canary", payload))
    assert state["status"] == "failed_canary"


def test_t2_fake_success_canary_advances_controller_to_development_plan(monkeypatch):
    def success(bob, syndrome, manifest, matrices, *, check_count, p):
        return {"status": "syndrome_consistent", "iterations": 1, "decoded_symbols": tuple(bob)}
    original = lane._frame
    def noiseless(config, p, index):
        row = original(config, p, index)
        row["alice"] = [0] * 256
        row["bob"] = [0] * 256
        return row
    monkeypatch.setattr(lane, "_frame", noiseless)
    state, payload, _ = _fake_canary_verified_chain(monkeypatch, success)
    assert not ladder.canary_gate_failed(payload)
    development_plan = {"stage": "development", "plan_sha256": "q" * 64, "frame_count": 32,
                        "roots": {"development|0.2": 202608048000, "development|0.3": 202608048100},
                        "per_stratum": {f"{p:.2f}": {"frames": 4, "verified_success": 4,
                                                     "forbidden_failures": 0}
                                        for p in (0.20, 0.30)},
                        "replay_report_sha256": payload["replay_report_sha256"]}
    state = ladder.advance(state, _report("planned", development_plan))
    assert state["status"] == "planned" and state["stage"] == "development"
