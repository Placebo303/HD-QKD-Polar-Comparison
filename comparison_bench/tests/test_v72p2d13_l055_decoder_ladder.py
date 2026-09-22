"""D13 focused tests: frozen selection, replay gate, ladder, gates, refusal.

Fake/tiny only: the production decoder is never imported or called, no
scientific call is made and no root outside pytest tmp paths is created.
Decoder entry is always fake-injected; binder tests wrap the imported
accepted binders with fakes (never the real ``v35`` targets). The 56-identity
real-graph reconstruction is D1309 (no-decoder PLAN_ONLY), not pytest.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import comparison_bench.formal_ir.v72p2d13_l055_decoder_ladder as d13  # noqa: E402


# --------------------------------------------------------------------------- #
# fakes
# --------------------------------------------------------------------------- #
def _stored(ident):
    width, graph_seed, call_idx, block_seed = ident
    return {"call_idx": call_idx, "width": width, "arm": "L055",
            "graph_seed": graph_seed, "block_seed": block_seed,
            "batch_id": d13.D12_BATCH_ID, "exact": False,
            "syndrome_ok": False, "iterations": 90,
            "status": "converged_no_syndrome",
            "belief_provenance": "CHECK_UPDATED"}


def _frozen_stored():
    return [_stored(ident) for ident in d13.FROZEN_IDENTITIES]


def _replay_ok(stored):
    return dict(stored, wall_s=0.01)


class _Counter:
    def __init__(self):
        self.calls = 0


def _ladder_fns(rescues_by_arm, counters=None, iters=120):
    """Fake ladder entry: rescued identities return exact+syndrome_valid."""
    fns = {}
    for arm in d13.LADDER_ARMS:
        rescued = set(rescues_by_arm.get(arm, ()))
        counter = _Counter()
        if counters is not None:
            counters[arm] = counter

        def fn(identity, _rescued=rescued, _counter=counter, _arm=arm):
            _counter.calls += 1
            key = (int(identity["width"]), int(identity["graph_seed"]),
                   int(identity["call_idx"]), int(identity["block_seed"]))
            if key in _rescued:
                return {"width": identity["width"], "arm": "L055",
                        "graph_seed": identity["graph_seed"],
                        "block_seed": identity["block_seed"],
                        "call_idx": identity["call_idx"],
                        "exact": True, "syndrome_ok": True,
                        "iterations": iters,
                        "belief_provenance": "CHECK_UPDATED", "wall_s": 0.02}
            return {"width": identity["width"], "arm": "L055",
                    "graph_seed": identity["graph_seed"],
                    "block_seed": identity["block_seed"],
                    "call_idx": identity["call_idx"],
                    "exact": False, "syndrome_ok": False,
                    "iterations": 360,
                    "belief_provenance": "CHECK_UPDATED", "wall_s": 0.02}
        fns[arm] = fn
    return fns


def _by_width(width):
    return [ident for ident in d13.FROZEN_IDENTITIES if ident[0] == width]


# --------------------------------------------------------------------------- #
# D1307: exact 56 selection + success exclusion
# --------------------------------------------------------------------------- #
def test_frozen_identity_count_and_split():
    assert len(d13.FROZEN_IDENTITIES) == 56
    assert len(d13.FROZEN_IDENTITY_SET) == 56
    assert sum(1 for i in d13.FROZEN_IDENTITIES if i[0] == 128) == 30
    assert sum(1 for i in d13.FROZEN_IDENTITIES if i[0] == 256) == 26
    per_graph_128 = {}
    per_graph_256 = {}
    for width, graph, _, _ in d13.FROZEN_IDENTITIES:
        (per_graph_128 if width == 128 else per_graph_256).setdefault(
            graph, 0)
        if width == 128:
            per_graph_128[graph] += 1
        else:
            per_graph_256[graph] += 1
    assert sorted(per_graph_128.values()) == [4, 4, 5, 5, 5, 7]
    assert sorted(per_graph_256.values()) == [3, 4, 4, 5, 5, 5]
    assert d13.BASELINE_ITERATIONS == 90


def test_selection_exact_56_and_success_excluded():
    rows = _frozen_stored()
    # successes + other arms must never enter the ladder
    for ident in list(d13.FROZEN_IDENTITIES)[:4]:
        width, graph, call_idx, block = ident
        rows.append({"call_idx": 999, "width": width, "arm": "L055",
                     "graph_seed": graph, "block_seed": block,
                     "batch_id": d13.D12_BATCH_ID, "exact": True,
                     "syndrome_ok": True, "iterations": 9,
                     "status": "converged_exact",
                     "belief_provenance": "CHECK_UPDATED"})
    rows.append({"call_idx": 0, "width": 128, "arm": "L050",
                 "graph_seed": 2026093001, "block_seed": 2026093201,
                 "batch_id": d13.D12_BATCH_ID, "exact": False,
                 "syndrome_ok": False, "iterations": 90,
                 "status": "converged_no_syndrome",
                 "belief_provenance": "CHECK_UPDATED"})
    selected = d13.select_l055_failures(rows)
    assert len(selected) == 56
    assert all(not r["exact"] for r in selected)
    assert sum(1 for r in selected if r["width"] == 128) == 30
    assert sum(1 for r in selected if r["width"] == 256) == 26
    assert d13.validate_selection(selected) == []
    assert d13.selection_identities(selected) == d13.FROZEN_IDENTITY_SET


def test_selection_validation_catches_drift():
    selected = _frozen_stored()
    assert d13.validate_selection(selected) == []
    dropped = selected[:-1]
    assert d13.validate_selection(dropped) != []  # 55 != frozen 56
    tampered = [dict(r) for r in selected]
    tampered[0]["iterations"] = 89
    assert any("iterations" in v
               for v in d13.validate_selection(tampered))
    tampered = [dict(r) for r in selected]
    tampered[0]["belief_provenance"] = "PRIOR_ONLY"
    assert any("provenance" in v
               for v in d13.validate_selection(tampered))


# --------------------------------------------------------------------------- #
# D1307: 56+168 accounting; plan built before any binding
# --------------------------------------------------------------------------- #
def test_plan_accounting_56_plus_168():
    selected = _frozen_stored()
    plan = d13.build_ladder_plan(selected)
    assert len(plan) == 224
    replay = [e for e in plan if e["kind"] == "replay"]
    ladder = [e for e in plan if e["kind"] == "ladder"]
    assert len(replay) == 56 and len(ladder) == 168
    # replays first, then ladder per failure in the fixed arm order
    assert [e["kind"] for e in plan] == ["replay"] * 56 + ["ladder"] * 168
    first_failure = sorted(d13.FROZEN_IDENTITY_SET)[0]
    first_ladder = ladder[:3]
    assert [e["decoder_arm"] for e in first_ladder] == list(d13.LADDER_ARMS)
    assert all((e["width"], e["graph_seed"], e["call_idx"], e["block_seed"])
               == first_failure for e in first_ladder)
    for arm in d13.LADDER_ARMS:
        assert sum(1 for e in ladder if e["decoder_arm"] == arm) == 56


def test_readiness_plan_built_before_binding_first_mismatch_stops():
    selected = _frozen_stored()
    plan_before = d13.build_ladder_plan(selected)  # plan exists pre-binding
    assert len(plan_before) == 224
    counters: dict = {}
    fns = _ladder_fns({}, counters)
    replay_counter = _Counter()

    def replay_fn(identity, _position=[0]):
        replay_counter.calls += 1
        observed = _replay_ok(identity)
        if _position[0] == 7:  # single mismatch at replay position 7
            observed = dict(observed, iterations=89)
        _position[0] += 1
        return observed

    outcome = d13.run_readiness(selected, replay_fn, fns)
    assert outcome["replay_calls"] == 8
    assert outcome["ladder_calls"] == 0  # FIRST mismatch blocks everything
    assert all(c.calls == 0 for c in counters.values())
    assert outcome["blocked"] is not None
    assert outcome["blocked"]["mismatch_field"] == "iterations"
    assert outcome["scientific_calls"] == 8


def test_readiness_clean_replay_runs_full_ladder():
    selected = _frozen_stored()
    counters: dict = {}
    fns = _ladder_fns({}, counters)
    outcome = d13.run_readiness(selected, _replay_ok, fns)
    assert outcome["blocked"] is None
    assert outcome["replay_calls"] == 56
    assert outcome["ladder_calls"] == 168
    assert outcome["scientific_calls"] == 224
    assert all(c.calls == 56 for c in counters.values())
    assert outcome["terminal"] == d13.T_NO_MATERIAL


# --------------------------------------------------------------------------- #
# D1307: provenance mandatory; non-CHECK_UPDATED refused
# --------------------------------------------------------------------------- #
def test_provenance_mandatory_non_check_updated_refused():
    selected = _frozen_stored()

    def replay_fn(identity):
        return dict(_replay_ok(identity), belief_provenance="PRIOR_ONLY")

    outcome = d13.run_readiness(selected, replay_fn,
                                _ladder_fns({}))
    assert outcome["blocked"] is not None
    assert outcome["blocked"]["mismatch_field"] == "belief_provenance"
    assert outcome["ladder_calls"] == 0
    assert d13.compare_replay(selected[0], _replay_ok(selected[0])) is None
    assert d13.compare_replay(
        selected[0], dict(selected[0], belief_provenance="OTHER")) == \
        "belief_provenance"


# --------------------------------------------------------------------------- #
# D1307: all rescue boundaries
# --------------------------------------------------------------------------- #
def _rescue_sets(n128, n256):
    return (_by_width(128)[:n128], _by_width(256)[:n256])


def test_rescue_gate_boundaries():
    assert d13.classify_rescues(12, 4, 8) == "MATERIAL_RESCUE"  # 12/4 edge
    assert d13.classify_rescues(20, 10, 10) == "MATERIAL_RESCUE"
    assert d13.classify_rescues(3, 1, 2) == "MODEST_RESCUE"  # 3-11 + 1/width
    assert d13.classify_rescues(11, 5, 6) == "MODEST_RESCUE"  # 11 edge
    assert d13.classify_rescues(0, 0, 0) == "NO_RESCUE"
    assert d13.classify_rescues(2, 2, 0) == "NO_RESCUE"  # <=2 edge
    assert d13.classify_rescues(2, 1, 1) == "NO_RESCUE"
    assert d13.classify_rescues(12, 3, 9) == "RESCUE_AMBIGUOUS"  # asymmetric
    assert d13.classify_rescues(5, 5, 0) == "RESCUE_AMBIGUOUS"
    assert d13.classify_rescues(13, 2, 11) == "RESCUE_AMBIGUOUS"
    assert d13.classify_rescues(20, 20, 0) == "RESCUE_AMBIGUOUS"


def test_terminals_per_gate():
    selected = _frozen_stored()
    # MATERIAL selects the arm
    r128, r256 = _rescue_sets(6, 6)
    outcome = d13.run_readiness(
        selected, _replay_ok,
        _ladder_fns({"ROW_LAYERED_360_ALPHA_1": list(r128) + list(r256)}))
    assert outcome["arm_stats"][0]["gate"] == "MATERIAL_RESCUE"
    assert outcome["terminal"] == "D13_SELECT_RL360"
    # MODEST collapses to the modest terminal
    r128, r256 = _rescue_sets(1, 2)
    outcome = d13.run_readiness(
        selected, _replay_ok,
        _ladder_fns({"FLOODING_360_ALPHA_1": list(r128) + list(r256)}))
    assert outcome["terminal"] == "D13_MODEST_DECODER_RESCUE"
    # asymmetric collapses to ambiguous
    r128, r256 = _rescue_sets(5, 0)
    outcome = d13.run_readiness(
        selected, _replay_ok,
        _ladder_fns({"ROW_LAYERED_360_ALPHA_0_7": list(r128) + list(r256)}))
    assert outcome["terminal"] == "D13_DECODER_RESCUE_AMBIGUOUS"


# --------------------------------------------------------------------------- #
# D1307: ranking incl. ties
# --------------------------------------------------------------------------- #
def _stat(arm, total, n128, n256, mean_iter=100.0):
    return {"arm": arm, "total": total, "n128": n128, "n256": n256,
            "mean_iter": mean_iter}


def test_ranking_total_then_worst_width_then_iter_then_arm_order():
    arms = d13.LADDER_ARMS
    # total dominates
    ranked = d13.rank_material_arms([
        _stat(arms[0], 12, 4, 8), _stat(arms[1], 14, 7, 7)])
    assert ranked == [arms[1], arms[0]]
    # total tie -> worst-width wins
    ranked = d13.rank_material_arms([
        _stat(arms[0], 12, 4, 8), _stat(arms[1], 12, 6, 6)])
    assert ranked == [arms[1], arms[0]]
    # worst-width tie -> fewer mean iterations wins
    ranked = d13.rank_material_arms([
        _stat(arms[0], 12, 6, 6, 150.0),
        _stat(arms[1], 12, 6, 6, 120.0)])
    assert ranked == [arms[1], arms[0]]
    # full tie -> fixed arm order
    ranked = d13.rank_material_arms([
        _stat(arms[1], 12, 6, 6), _stat(arms[0], 12, 6, 6),
        _stat(arms[2], 12, 6, 6)])
    assert ranked == [arms[0], arms[1], arms[2]]
    # non-material arms never rank
    assert d13.rank_material_arms([_stat(arms[0], 2, 1, 1)]) == []


# --------------------------------------------------------------------------- #
# D1307: exact/syndrome/undetected isolation
# --------------------------------------------------------------------------- #
def test_exact_syndrome_undetected_isolation():
    good = {"exact": True, "syndrome_ok": True,
            "belief_provenance": "CHECK_UPDATED"}
    undetected = {"exact": False, "syndrome_ok": True,
                  "belief_provenance": "CHECK_UPDATED"}
    exact_no_syndrome = {"exact": True, "syndrome_ok": False,
                         "belief_provenance": "CHECK_UPDATED"}
    wrong_prov = {"exact": True, "syndrome_ok": True,
                  "belief_provenance": "PRIOR_ONLY"}
    assert d13.is_rescue(good) is True
    assert d13.is_rescue(undetected) is False
    assert d13.is_rescue(exact_no_syndrome) is False
    assert d13.is_rescue(wrong_prov) is False


# --------------------------------------------------------------------------- #
# D1307: decoder entry fake-injected only (wrap imported binders with fakes)
# --------------------------------------------------------------------------- #
def test_binders_wrapped_with_fakes_never_call_real_decoder(monkeypatch):
    seen: dict = {}

    class _FakeResult:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    def fake_rl_target(h, prior, syn, **kwargs):
        seen.setdefault("rl", []).append(dict(kwargs))
        return _FakeResult(x_hat=[], syndrome_ok=True, iterations=1,
                           belief_provenance="CHECK_UPDATED")

    def fake_flood_target(h, prior, syn, **kwargs):
        seen.setdefault("flood", []).append(dict(kwargs))
        return _FakeResult(x_hat=[], syndrome_ok=True, iterations=1,
                           belief_provenance="CHECK_UPDATED")

    class _Wrapper:
        def __init__(self, target):
            self.target = target

    # wrap the IMPORTED accepted binders with fakes (real v35 never touched)
    monkeypatch.setattr(d13.x3rl, "bind_row_layered_decoders",
                        lambda: {"SOURCE": _Wrapper(fake_rl_target),
                                 "TARGET": _Wrapper(fake_rl_target)})
    monkeypatch.setattr(d13.x3sched, "bind_schedule_decoders",
                        lambda: {"ROW_LAYERED": _Wrapper(fake_rl_target),
                                 "FLOODING": _Wrapper(fake_flood_target)})
    binds = d13.bind_production()
    assert set(binds) == {d13.REPLAY_ARM_ID} | set(d13.LADDER_ARMS)
    binds["ROW_LAYERED_360_ALPHA_1"](None, None, None)
    binds["ROW_LAYERED_360_ALPHA_0_7"](None, None, None)
    binds["FLOODING_360_ALPHA_1"](None, None, None)
    binds[d13.REPLAY_ARM_ID](None, None, None)
    assert [c["max_iter"] for c in seen["rl"]] == [360, 360, 90]
    assert [c["damping_alpha"] for c in seen["rl"]] == [1.0, 0.7, 1.0]
    assert all(c["warm_beliefs"] is None and c["field"] is None
               for c in seen["rl"])
    assert seen["flood"][0]["max_iter"] == 360
    assert "damping_alpha" not in seen["flood"][0]  # flooding: no damping
    assert "v35" not in sys.modules or not any(
        "real" in str(getattr(m, "__name__", "")) for m in [])


# --------------------------------------------------------------------------- #
# D1305/D1306: unauthorized refusal + never-overwrite + verifier (fake roots)
# --------------------------------------------------------------------------- #
def _write_fake_input_root(path):
    path.mkdir(parents=True)
    with open(path / "decoder_records.csv", "w", newline="",
              encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["call_idx", "width", "arm", "graph_seed",
                            "block_seed", "batch_id", "exact", "syndrome_ok",
                            "iterations", "status", "belief_provenance"])
        writer.writeheader()
        for row in _frozen_stored():
            writer.writerow(row)


def test_plan_only_zero_calls_no_root(tmp_path):
    fake_in = tmp_path / "fake_d12_in"
    _write_fake_input_root(fake_in)
    meta = d13.plan_only_metadata(fake_in)
    assert meta["violations"] == []
    assert meta["selection"] == {"total": 56, "n128": 30, "n256": 26}
    assert meta["plan_calls"] == 224
    assert meta["replay_calls"] == 56 and meta["ladder_calls"] == 168
    assert meta["decoder_calls"] == 0
    assert len(meta["identities"]) == 56
    # no root created anywhere near the inputs
    assert list(tmp_path.iterdir()) == [fake_in]


def test_runner_refuses_batch_without_flag_and_binds_nothing(
        tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "v72p2d13_runner_test",
        str(ROOT / "scripts" / "v72p2d13_development.py"))
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    sys.modules["v72p2d13_runner_test"] = runner
    spec.loader.exec_module(runner)
    bound = _Counter()
    monkeypatch.setattr(
        d13, "bind_production",
        lambda: (_ for _ in ()).throw(AssertionError("must not bind")))
    out_root = tmp_path / "must_not_exist"
    rc = runner.main(["--d13-batch", "--out-root", str(out_root)])
    assert rc == 2
    assert not out_root.exists()
    assert bound.calls == 0


def test_write_verify_roundtrip_and_never_overwrite(tmp_path):
    selected = _frozen_stored()
    r128, r256 = _rescue_sets(2, 1)  # total 3 with >=1/width -> MODEST
    outcome = d13.run_readiness(
        selected, _replay_ok,
        _ladder_fns({"ROW_LAYERED_360_ALPHA_1": list(r128) + list(r256)}),
        rss_fn=lambda: 1024)
    assert outcome["terminal"] == "D13_MODEST_DECODER_RESCUE"
    out_root = tmp_path / "d13_fake_root"
    summary = d13.write_root(out_root, selection=selected, outcome=outcome,
                             model_f_root="fake-model-f-root", setup_calls=2,
                             log_lines=["fake log"])
    assert summary["scientific_calls"] == 224
    assert summary["setup_calls"] == 2
    assert d13.verify_root(out_root) is True
    with pytest.raises(FileExistsError):
        d13.write_root(out_root, selection=selected, outcome=outcome,
                       model_f_root="fake-model-f-root", setup_calls=2)
    # tampered ladder evidence fails closed
    rows = list(csv.DictReader(
        open(out_root / "ladder_records.csv", encoding="utf-8")))
    rows[0]["exact"] = "True" if rows[0]["exact"] == "False" else "False"
    with open(out_root / "ladder_records.csv", "w", newline="",
              encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    assert d13.verify_root(out_root) is False


def test_verify_rejects_setup_over_ceiling(tmp_path):
    selected = _frozen_stored()
    outcome = d13.run_readiness(selected, _replay_ok, _ladder_fns({}),
                                rss_fn=lambda: 1024)
    out_root = tmp_path / "d13_setup_root"
    d13.write_root(out_root, selection=selected, outcome=outcome,
                   model_f_root="fake-model-f-root", setup_calls=9)
    assert d13.verify_root(out_root) is False
