"""Focused D06 validation for the D17 descaling readiness module + runner.

Fresh ``workspace/<task>/<uuid>`` basetemps (``-p no:cacheprovider``); zero
scientific DE calls; zero production decoder calls; the frozen future DE
root and the D16 official root are never created. The DE batch tests inject
a fake DE callable + fake rho/channel; the production binder is monkeypatched
to fail if touched on the refusal/PROFILE_ONLY paths.
"""

from __future__ import annotations

import csv
import importlib.util
import inspect
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

MODULE_PATH = (SRC / "comparison_bench" / "formal_ir"
               / "v72p2d17_descaling.py")
RUNNER_PATH = (ROOT / "scripts" / "v72p2d17_scaling_development.py")


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = _load_module("v72p2d17_runner_test", RUNNER_PATH)
d17 = runner.d17
assert Path(d17.__file__).resolve() == MODULE_PATH


def _boom(*_args, **_kwargs):
    raise AssertionError("production path must not be entered")


# --------------------------------------------------------------------------- #
# Fake DE machinery (deterministic; injected, never the V26 kernel)
# --------------------------------------------------------------------------- #
_FAKE_RHO = {"L045": {2: 0.25, 3: 0.75}, "L055": {2: 0.3, 3: 0.7},
             "L2": {3: 0.4, 4: 0.6}}


def _fake_rho_fn(profile, m):
    assert (str(profile), int(m)) in [
        (p, mm) for p in d17.DE_PROFILES for mm in d17.DE_GRID_M[p]]
    return dict(_FAKE_RHO[str(profile)])


class _FakeDE:
    """Stateful fake: convergence decided per (profile, m); traces length 60."""

    def __init__(self, schedule):
        self.schedule = schedule
        self.calls = []

    def __call__(self, lambda_edge, rho_edge, channel, seed, n_samples):
        assert channel == {"fake": "channel"}
        match = [p for p, rho in _FAKE_RHO.items()
                 if set(rho_edge) == set(rho)
                 and all(abs(rho_edge[k] - rho[k]) < 1e-15 for k in rho)]
        assert len(match) == 1, rho_edge
        self.calls.append((match[0], int(seed), int(n_samples)))
        # The orchestrator iterates plan order; recover m from call order.
        idx = len(self.calls) - 1
        entry = d17.build_de_plan()[idx]
        assert entry["profile"] == match[0] and int(entry["seed"]) == int(seed)
        converged = bool(self.schedule[(match[0], int(entry["m"]))])
        final = 1e-6 if converged else 0.5
        trace = [max(final, 5.0 - 0.2 * t) for t in range(1, 60)] + [final]
        return {"entropy_trace_bits": trace,
                "channel_entropy_trace_bits": [5.0] * 60}


def _clean_bracket_schedule():
    above = {}
    grids = {"L045": (106, 110, 114, 118, 122),
             "L055": (116, 119, 122, 124, 126),
             "L2": (89, 94, 99, 104, 109)}
    cuts = {"L045": 114, "L055": 122, "L2": 99}
    for p, ms in grids.items():
        for m in ms:
            above[(p, m)] = m >= cuts[p]
    # Soften one low-side point per profile to exercise S in {1, 2}.
    return above


# --------------------------------------------------------------------------- #
# T0 frozen constants / exact future command
# --------------------------------------------------------------------------- #
def test_t0_frozen_channel_decoder_constants():
    assert d17.H_L1 == 4.286720430201375
    assert d17.H_L2 == 3.222719884634378
    assert d17.LOAD_L1 == 548.700215065776
    assert d17.LOAD_L2 == 412.508145233200
    assert d17.LAMBDA_STAR == 137.3823795883263870
    assert d17.PRIOR_FLOOR == 1e-300
    assert d17.Q == 32 and d17.POLY == 37
    assert d17.DECODER_MAX_ITER == 90 and d17.DAMPING_ALPHA == 1.0
    assert d17.DECODER_FLOOR == 1e-15
    assert d17.MODEL_F_INPUT_ROOT == \
        "workspace/v72p2d5_model_f_input/20260907_r1"
    assert d17.TRACK == "implementation/readiness"


def test_t0_frozen_command_and_budgets():
    assert d17.FROZEN_COMMAND == (
        ".venv/bin/python scripts/v72p2d17_scaling_development.py --de-batch "
        "--execution-authorized --model-f-root "
        "workspace/v72p2d5_model_f_input/20260907_r1 --out-root "
        "workspace/d17_current_channel_asymptotic_de_"
        "7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718")
    assert runner.FROZEN_COMMAND == d17.FROZEN_COMMAND
    assert d17.DE_CALL_CEILING == 240 and d17.SETUP_CEILING == 12
    assert d17.SETUP_UNITS == 4
    assert d17.WALL_BUDGET_S == 1200.0 and d17.PER_CALL_BUDGET_S == 300.0
    assert d17.RSS_BUDGET_BYTES == 2 * 1024 ** 3
    assert tuple(runner.EVIDENCE_FILES) == (
        "manifest.json", "de_plan.csv", "de_records.csv", "de_traces.csv",
        "summary.json", "command_log.txt")
    parser = runner.build_parser()
    args = parser.parse_args(["--profile-only"])
    assert args.execution_authorized is False


def test_t0_grid_points_and_seeds():
    assert d17.DE_GRID_M == {
        "L045": (106, 110, 114, 118, 122),
        "L055": (116, 119, 122, 124, 126),
        "L2": (89, 94, 99, 104, 109)}
    assert d17.DE_SEEDS == tuple(range(2026094201, 2026094209))
    assert d17.DE_POPULATIONS == (4000, 16000)
    assert d17.DE_MAX_ITER == 60 and d17.DE_ENTROPY_TOL_BITS == 1e-4
    assert d17.DE_STREAK == 20
    assert d17.VAR_SIDES == {"L045": {2: 71, 3: 57},
                             "L055": {2: 83, 3: 45}, "L2": {3: 128}}
    assert d17.EDGE_TOTALS == {"L045": 313, "L055": 301, "L2": 384}
    assert d17.D16_GRAPH_SEEDS == tuple(range(2026094001, 2026094013))
    assert d17.D16_BLOCK_SEEDS == tuple(range(2026094101, 2026094109))
    assert d17.D16_OFFICIAL_ROOT == (
        "workspace/d16_matched_backoff_discriminator_"
        "b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a")
    assert d17.FAKE_SCRATCH_ROOT == "workspace/d16_align_20260915_a/"
    assert d17.EPS_PRIMARY == 0.10 and d17.EPS_SENSITIVITY == 0.01
    assert d17.M0_BASELINE == {"L1": {64: 55, 128: 110, 256: 220},
                               "L2": {64: 42, 128: 83, 256: 166}}


# --------------------------------------------------------------------------- #
# Math / channel-equivalence fixtures
# --------------------------------------------------------------------------- #
def test_delta_spot_recompute():
    assert abs(d17.delta_of(118, 128, "L1") - 0.322654569798625) < 1e-12
    assert abs(d17.delta_of(86, 128, "L2") - 0.136655115365622) < 1e-12
    assert abs(d17.delta_of(110, 128, "L1") - 0.010154569798625) < 1e-12
    assert abs(d17.delta_of(125, 128, "L1") - 0.596092069798625) < 1e-12
    assert abs(d17.delta_of(94, 128, "L2") - 0.449155115365622) < 1e-12
    assert abs(d17.rate_of(106) - 0.171875) < 1e-15
    assert abs(d17.rate_of(122) - 0.046875) < 1e-15
    assert abs(d17.rate_of(126) - 0.015625) < 1e-15
    assert abs(d17.rate_of(89) - 0.3046875) < 1e-12


def test_m0_baselines_recompute():
    for layer, table in (("L1", {64: 55, 128: 110, 256: 220}),
                         ("L2", {64: 42, 128: 83, 256: 166})):
        for n, want in table.items():
            assert d17.baseline_m0(layer, n) == want


def test_check_allocation_worked_examples():
    assert d17.check_allocation(313, 110) == {2: 17, 3: 93}
    assert d17.check_allocation(301, 122) == {2: 65, 3: 57}
    assert d17.check_allocation(384, 99) == {3: 12, 4: 87}
    cell = d17.degree_cell("L045", 110)
    assert cell["E"] == 313 and cell["rate"] == 1.0 - 110 / 128
    with pytest.raises(KeyError):
        d17.degree_cell("L045", 125)  # outside the frozen DE grid
    with pytest.raises(KeyError):
        d17.degree_cell("L050", 118)


def test_accepted_degree_helper_agrees():
    d9 = d17._load_sibling("v72p2d9_de_decoder_calibration")
    cases = [("L045", {2: 0.45, 3: 0.55}, 110, 71, 57, 313, {2: 17, 3: 93}),
             ("L055", {2: 0.55, 3: 0.45}, 122, 83, 45, 301, {2: 65, 3: 57}),
             ("L2", {3: 1.0}, 99, 0, 128, 384, {3: 12, 4: 87})]
    for profile, lam, m, n2, n3, E, alloc in cases:
        got = d9.graph_realization_cell(lam, 128, m, candidate_id=profile,
                                        condition="d17-fixture")
        assert (got["n2"], got["n3"], got["E"]) == (n2, n3, E)
        assert got["check_degree_allocation"] == alloc
        cell = d17.degree_cell(profile, m)
        assert cell["check_counts"] == alloc and cell["E"] == E


def test_channel_identity_vs_live_predecessors():
    report = d17.verify_channel_identity()
    assert report["passed"] is True, report["checks"]
    assert all(report["checks"].values())


def test_monotonic_limits_and_stop():
    assert d17.check_monotonic_limits(0.15, 0.6, 0.25) is True
    assert abs(float(d17.p_success(128, 0.15, 0.15, 0.6, 0.0)) - 0.5) < 1e-12
    with pytest.raises(ValueError):
        d17.check_monotonic_limits(0.15, 0.0, 0.25)
    with pytest.raises(ValueError):
        d17.check_monotonic_limits(0.15, -1.0, 0.25)
    assert abs(d17.ndtri(0.9) - 1.2815515655446004) < 1e-9
    assert abs(d17.ndtri(0.99) - 2.3263478740408408) < 1e-9
    assert abs(d17.ndtri(0.5)) < 1e-12


# --------------------------------------------------------------------------- #
# Plan / grid arithmetic
# --------------------------------------------------------------------------- #
def test_plan_240_frozen_order():
    plan = d17.build_de_plan()
    assert len(plan) == 240 == d17.planned_de_calls()
    assert [e["call_idx"] for e in plan] == list(range(240))
    assert d17.build_de_plan() == d17.build_de_plan()  # deterministic
    index = d17.expected_call_index(plan)
    assert sorted(index.values()) == list(range(240))
    first = plan[0]
    assert (first["profile"], first["m"], first["population"],
            first["seed"]) == ("L045", 106, 4000, 2026094201)
    last = plan[-1]
    assert (last["profile"], last["m"], last["population"],
            last["seed"]) == ("L2", 109, 16000, 2026094208)
    for entry in plan:
        assert entry["seed"] in d17.DE_SEEDS
        assert entry["E"] == d17.EDGE_TOTALS[entry["profile"]]
    deltas = {(e["profile"], e["m"]): round(e["delta"], 5) for e in plan}
    assert deltas[("L045", 106)] == -0.14610
    assert deltas[("L045", 122)] == 0.47890
    assert deltas[("L055", 116)] == 0.24453
    assert deltas[("L055", 126)] == 0.63515
    assert deltas[("L2", 89)] == 0.25384
    assert deltas[("L2", 109)] == 1.03509


def test_bracket_rule_and_edge_flags():
    out = d17.bracket_delta_de(
        "L045", {106: 0, 110: 1, 114: 8, 118: 8, 122: 8},
        {106: 0, 110: 1, 114: 8, 118: 8, 122: 8})
    assert out["lo_m"] == 110 and out["hi_m"] == 114
    assert abs(out["delta_de"] - (0.010154569798625 + 0.166404569798625) / 2) \
        < 1e-12
    assert out["flags"] == [d17.F_BRACKET]
    assert abs(out["h"] - (0.166404569798625 - 0.010154569798625) / 2) < 1e-12
    soft = d17.bracket_delta_de(
        "L055", {116: 0, 119: 4, 122: 7, 124: 8, 126: 8})
    assert soft["lo_m"] == 116 and soft["hi_m"] == 122
    assert soft["flags"] == [d17.F_SOFT_BRACKET]
    low = d17.bracket_delta_de("L2", {89: 8, 94: 8, 99: 8, 104: 8, 109: 8})
    assert low["flag"] == d17.F_ONE_SIDED_LOW
    high = d17.bracket_delta_de("L2", {89: 0, 94: 1, 99: 2, 104: 3, 109: 0})
    assert high["flag"] == d17.F_ONE_SIDED_HIGH
    unstable = d17.bracket_delta_de(
        "L045", {106: 0, 110: 1, 114: 8, 118: 8, 122: 8},
        {106: 0, 110: 7, 114: 8, 118: 8, 122: 8})
    assert unstable["flags"] == [d17.F_BRACKET, d17.F_POP_UNSTABLE]
    with pytest.raises(ValueError):
        d17.bracket_delta_de("L045", {106: 4, 110: 5, 114: 4, 118: 5,
                                      122: 4})  # no pair: never re-grid
    with pytest.raises(ValueError):
        d17.bracket_delta_de("L045", {106: 8, 110: 8, 114: 0, 118: 0,
                                      122: 0})  # non-monotone: fail-closed


def test_seed_disjointness_and_banned_sets():
    report = d17.verify_seed_disjointness()
    assert report["passed"] is True, report
    assert report["de_hits_prior"] == [] and report["de_hits_d16"] == []
    assert set(d17.BANNED_SEEDS) == set(d17.D16_GRAPH_SEEDS) | set(
        d17.D16_BLOCK_SEEDS)
    assert set(d17.DE_SEEDS).isdisjoint(d17.BANNED_SEEDS)


# --------------------------------------------------------------------------- #
# Fake DE dispatch / authorization refusal / verify
# --------------------------------------------------------------------------- #
def _run_fake_batch(out, schedule=None):
    fake = _FakeDE(schedule or _clean_bracket_schedule())
    bundle = d17.run_de_batch(
        str(out), "workspace/nonexistent_model_f",
        channel={"fake": "channel"}, de_call=fake, rho_fn=_fake_rho_fn)
    summary = d17.write_de_root(bundle)
    return fake, bundle, summary


def test_fake_batch_roundtrip_and_verify(tmp_path, monkeypatch):
    monkeypatch.setattr(d17, "bind_production_de", _boom)
    out = tmp_path / "de_root"
    fake, bundle, summary = _run_fake_batch(out)
    assert summary["terminal"] == "DE_COMPLETE"
    assert summary["scientific_calls"] == 240
    assert summary["setup_calls"] == d17.SETUP_UNITS == 4
    assert len(fake.calls) == 240  # one attempt per planned call, no retry
    assert sorted(p.name for p in out.iterdir()) == sorted(
        runner.EVIDENCE_FILES)
    manifest = json.loads((out / "manifest.json").read_text("utf-8"))
    assert manifest["command"] == runner.FROZEN_COMMAND
    brackets = summary["brackets"]
    assert set(brackets) == {"L045", "L055", "L2"}
    assert brackets["L045"]["lo_m"] == 110
    assert brackets["L045"]["hi_m"] == 114
    assert brackets["L055"]["lo_m"] == 119
    assert brackets["L055"]["hi_m"] == 122
    assert brackets["L2"]["lo_m"] == 94
    assert brackets["L2"]["hi_m"] == 99
    assert d17.verify_de_root(str(out), rho_fn=_fake_rho_fn) is True
    assert runner.main(["--verify", "--out-root", str(out)],
                       adapters_override={"rho_fn": _fake_rho_fn}) == 0
    assert runner.main(["--verify", "--out-root", str(out)]) == 0
    assert runner.main(["--verify", "--out-root",
                        str(tmp_path / "missing")]) == 1


def test_verify_detects_tampered_record_and_rho(tmp_path, monkeypatch):
    monkeypatch.setattr(d17, "bind_production_de", _boom)
    out = tmp_path / "de_root"
    _run_fake_batch(out)
    assert d17.verify_de_root(str(out), rho_fn=_fake_rho_fn) is True
    rows = d17._read_csv(out / "de_records.csv")
    rows[0]["final_entropy_bits"] = str(float(rows[0][
        "final_entropy_bits"]) + 1.0)
    d17._write_csv(out / "de_records.csv", d17.DE_RECORD_COLUMNS, rows)
    assert d17.verify_de_root(str(out), rho_fn=_fake_rho_fn) is False

    def _wrong_rho(profile, m):
        return {2: 0.5, 3: 0.5} if profile != "L2" else {3: 0.5, 4: 0.5}

    out2 = tmp_path / "de_root2"
    _run_fake_batch(out2)
    assert d17.verify_de_root(str(out2), rho_fn=_wrong_rho) is False


def test_failure_retention_no_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(d17, "bind_production_de", _boom)
    attempts = []

    def flaky(lambda_edge, rho_edge, channel, seed, n_samples):
        attempts.append((int(seed), int(n_samples)))
        if len(attempts) >= 5:
            raise RuntimeError("injected DE failure")
        trace = [0.5] * 59 + [0.5]
        return {"entropy_trace_bits": trace,
                "channel_entropy_trace_bits": [5.0] * 60}

    out = tmp_path / "de_root"
    bundle = d17.run_de_batch(
        str(out), "workspace/nonexistent_model_f",
        channel={"fake": "channel"}, de_call=flaky, rho_fn=_fake_rho_fn)
    summary = d17.write_de_root(bundle)
    assert summary["terminal"] == "DE_ENGINEERING_BLOCKED"
    assert summary["scientific_calls"] == 4
    assert len(attempts) == 5  # one attempt per planned call, no retry
    assert sorted(p.name for p in out.iterdir()) == sorted(
        runner.EVIDENCE_FILES)
    assert d17.verify_de_root(str(out), rho_fn=_fake_rho_fn) is False


def test_refusal_before_root_bind_load(tmp_path, monkeypatch):
    monkeypatch.setattr(d17, "_load_sibling", _boom)
    monkeypatch.setattr(d17, "bind_production_de", _boom)
    fresh = tmp_path / "fresh"
    rc = runner.main(["--de-batch", "--out-root", str(fresh)])
    assert rc == 2
    assert not fresh.exists()
    assert runner.main(["--profile-only"]) == 0  # PROFILE_ONLY never binds


def test_profile_only_content(capsys):
    desc = d17.describe_plan()
    assert desc["grid_points"] == 15
    assert desc["planned_de_calls"] == 240
    assert desc["future_root_absent"] is True
    assert desc["de_calls"] == 0 and desc["decoder_calls"] == 0
    assert desc["frozen_command"] == runner.FROZEN_COMMAND
    assert runner.main(["--profile-only"]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["planned_de_calls"] == 240
    assert printed["cells"][0] == {
        "E": 313, "check_counts": {"2": 5, "3": 101}, "delta": d17.delta_of(
            106, 128, "L1"), "m": 106, "profile": "L045", "rate": d17.rate_of(
            106)}
    l045_m110 = next(c for c in printed["cells"]
                     if c["profile"] == "L045" and c["m"] == 110)
    assert l045_m110["check_counts"] == {"2": 17, "3": 93}


# --------------------------------------------------------------------------- #
# Scaling fit: synthetic recovery + identifiability ladder
# --------------------------------------------------------------------------- #
def _synthetic_clusters(profile, ns, deltas, t=400, graphs=3, seed=7):
    rng = np.random.default_rng(seed)
    clusters = []
    for n in ns:
        for delta in deltas:
            p = float(d17.p_success(n, delta, 0.15, 0.6, 0.25))
            for g in range(graphs):
                y = int(rng.binomial(t // graphs, p))
                clusters.append({"profile": profile, "n": n, "delta": delta,
                                 "y": y, "t": t // graphs,
                                 "graph_id": "g%d@n%d" % (g, n),
                                 "root": "SYNTH"})
    return clusters


def test_synthetic_recovery_two_param():
    clusters = _synthetic_clusters(
        "L045", (64, 128, 256),
        (-0.05, 0.05, 0.15, 0.25, 0.35, 0.45))
    d17.assert_no_residual_covariates(clusters)
    out = d17.fit_with_ladder(clusters, 0.15, B=60, seed=11)
    assert out["model"] == "two_param", out
    assert abs(out["fit"]["alpha"] - 0.6) / 0.6 < 0.35, out["fit"]
    assert abs(out["fit"]["beta"] - 0.25) < 0.15, out["fit"]
    boot = d17.cluster_bootstrap(clusters, 0.15, B=60, seed=11)
    assert boot["n_ok"] == 60
    lo = d17.loo_range(clusters, 0.15, beta_fixed=None)
    assert lo["n_graphs"] == 9


def test_single_width_forces_one_param_primary():
    clusters = [{"profile": "L2", "n": 128, "delta": d, "y": y, "t": 32,
                 "graph_id": "g%d" % i, "root": "SYNTH"}
                for i, (d, y) in enumerate([(0.01947, 0), (0.13666, 0),
                                            (0.25384, 0), (0.83978, 21)])]
    out = d17.fit_with_ladder(clusters, 0.5, B=40, seed=5)
    assert out["model"] == "one_param", out
    assert out["beta_fixed"] == 0.0
    assert out["reason"].startswith("predeclared single-width")


def test_degenerate_fixture_not_identifiable():
    clusters = [{"profile": "L045", "n": 128, "delta": 0.01, "y": 0, "t": 32,
                 "graph_id": "g%d" % i, "root": "SYNTH"} for i in range(4)]
    out = d17.fit_with_ladder(clusters, 0.3, B=40, seed=5)
    assert out["model"] == d17.MODEL_NOT_IDENTIFIABLE, out


def test_delta_de_slot_enforced():
    clusters = _synthetic_clusters("L045", (128,), (0.1,), t=96,
                                   graphs=2)
    with pytest.raises(ValueError):
        d17.fit_profile(clusters, None)
    with pytest.raises(ValueError):
        d17.binomial_nll(clusters, None, 0.6, 0.25)
    with pytest.raises(ValueError):
        d17.fit_with_ladder(clusters, None)
    params = list(inspect.signature(d17.fit_profile).parameters)
    assert params[1] == "delta_de"  # required slot, never refit


def test_logistic_descriptive_only():
    ps = [d17.logistic_p(128, d, 0.15, 0.6, 0.25)
          for d in (-1.0, 0.0, 0.15, 0.5, 2.0)]
    assert all(0.0 < p < 1.0 for p in ps)
    assert all(b > a for a, b in zip(ps, ps[1:]))
    assert abs(d17.logistic_p(128, 0.15, 0.15, 0.6, 0.0) - 0.5) < 1e-12


def test_inversion_integers_and_ordering():
    back10 = d17.row_backoff(128, 0.10, 0.15, 0.6, 0.25, "L1")
    back01 = d17.row_backoff(128, 0.01, 0.15, 0.6, 0.25, "L1")
    assert isinstance(back10, int) and isinstance(back01, int)
    assert back01 >= back10
    assert d17.m_star(128, 0.10, 0.15, 0.6, 0.25, "L1") \
        - d17.baseline_m0("L1", 128) == back10
    lo, hi = d17.predict_interval(
        128, 0.3, [(0.6, 0.25)], [0.10, 0.15, 0.20])
    point = float(d17.p_success(128, 0.3, 0.15, 0.6, 0.25))
    assert lo <= point <= hi and hi > lo


# --------------------------------------------------------------------------- #
# Eligibility isolation + holdout gates
# --------------------------------------------------------------------------- #
def test_eligibility_classes():
    assert d17.classify_observation(source="D15", layer="L1",
                                    profile="L045") == "FIT_L045"
    assert d17.classify_observation(source="D10-A1", layer="L1",
                                    profile="MIX-0.45") == "FIT_L045"
    assert d17.classify_observation(source="D15", layer="L1",
                                    profile="L055") == "FIT_L055"
    assert d17.classify_observation(source="D14N", layer="L2",
                                    profile="L2-ORACLE",
                                    oracle=True) == "FIT_L2"
    assert d17.classify_observation(source="D11", layer="L1",
                                    profile="REPLAY") == "VALIDATION_ONLY"
    assert d17.classify_observation(source="D11", layer="L2",
                                    profile="L2-ORACLE",
                                    oracle=True) == "VALIDATION_ONLY"
    assert d17.classify_observation(source="D16", layer="L1",
                                    profile="L045") == "VALIDATION_ONLY"
    assert d17.classify_observation(source="D12", layer="L1",
                                    profile="L050") == "DESCRIPTIVE_ONLY"
    assert d17.classify_observation(source="D10-A1", layer="L1",
                                    profile="DV3") == "DESCRIPTIVE_ONLY"
    assert d17.classify_observation(source="D11", layer="L1",
                                    profile="APP", joint=True) == \
        "EXCLUDED_APP_JOINT"
    assert d17.classify_observation(source="D14N", layer="L2",
                                    profile="L2-APP",
                                    joint=True) == "EXCLUDED_APP_JOINT"
    assert d17.classify_observation(source="D15", layer="L1",
                                    profile="L2-ORACLE",
                                    oracle=True) == "EXCLUDED_ORACLE_MISPLACED"


def test_fit_eligibility_gates():
    good = {"source": "D15", "layer": "L1", "profile": "L045",
            "graph_seed": 2026093801, "block_seed": 2026093901,
            "source_path": "workspace/d15_finite_margin_curve_8c1e4f2a/"}
    assert d17.assert_fit_eligible(dict(good)) == "FIT_L045"
    app = dict(good, profile="APP", joint=True)
    with pytest.raises(ValueError):
        d17.assert_fit_eligible(app)
    banned = dict(good, graph_seed=2026094003)
    with pytest.raises(ValueError):
        d17.assert_fit_eligible(banned)
    banned_b = dict(good, block_seed=2026094105)
    with pytest.raises(ValueError):
        d17.assert_fit_eligible(banned_b)
    fake = dict(good, source_path="workspace/d16_align_20260915_a/"
                                  "test_d16_x/decoder_records.csv")
    with pytest.raises(ValueError):
        d17.assert_fit_eligible(fake)
    d16row = dict(good, source="D16", profile="L045",
                  graph_seed=2026094001)
    with pytest.raises(ValueError):
        d17.assert_fit_eligible(d16row)
    with pytest.raises(ValueError):
        d17.assert_no_banned_seeds([{"graph_seed": 2026094012}])
    assert d17.assert_no_banned_seeds([{"graph_seed": 2026094201}]) is True


def test_d16_root_absent_and_blank_predictions(tmp_path):
    assert not (ROOT / d17.D16_OFFICIAL_ROOT).exists()
    assert not (ROOT / d17.FUTURE_ROOT).exists()
    with pytest.raises(FileExistsError):
        d17.assert_d16_root_absent(tmp_path)  # gate logic on existing paths
    preds = [d17.blank_prediction(p, m) for p, m, _ in d17.D16_CELLS]
    assert len(preds) == 3
    for pred in preds:
        assert pred["schema"] == "d16_holdout_prediction_v1"
        assert all(v == "BLANK" for v in pred["outcome"].values())
        assert pred["gate"] == {"fail_if_d16_root_exists": True,
                                "predictions_frozen_before_run": True}
    names = d17.write_predictions(tmp_path / "preds", preds)
    assert names == ["d16_prediction_L045_m125.json",
                     "d16_prediction_L055_m125.json",
                     "d16_prediction_L2_m94.json"]
    stored = json.loads((tmp_path / "preds" / names[0]).read_text("utf-8"))
    assert stored["outcome"]["pool"] == "BLANK"
    dirty = dict(preds[0])
    dirty["outcome"] = dict(dirty["outcome"], pool=20)
    with pytest.raises(ValueError):
        d17.write_predictions(tmp_path / "preds2", [dirty])
    with pytest.raises(KeyError):
        d17.blank_prediction("L050", 118)


def test_residual_separation():
    rec = d17.residual_record(admission="A1-A6", iterations=90)
    assert rec["descriptive_only"] is True
    assert set(rec) == set(d17.RESIDUAL_FIELDS) | {"descriptive_only"}
    fit_inputs = [{"profile": "L045", "n": 128, "delta": 0.1, "y": 1,
                   "t": 32, "graph_id": "g0"}]
    assert d17.assert_no_residual_covariates(fit_inputs) is True
    with pytest.raises(ValueError):
        d17.assert_no_residual_covariates(
            [dict(fit_inputs[0], iterations=90)])


# --------------------------------------------------------------------------- #
# Audit artifact
# --------------------------------------------------------------------------- #
def test_audit_artifact_inventory(tmp_path):
    names = d17.build_audit_artifacts(tmp_path)
    assert names == ["d17_audit_inventory.csv", "d17_audit_inventory.json",
                     "d17_audit_report.txt"]
    with open(tmp_path / "d17_audit_inventory.csv", encoding="utf-8",
              newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(d17.AUDIT_SOURCE_ROWS)
    by_fid = {r["fid"]: r for r in rows}
    assert by_fid["F3"]["delta"] == "0.32265"
    assert by_fid["F16"]["delta"] == "0.83978"
    assert by_fid["F19b"]["delta"] == "0.13666"
    assert by_fid["H1"]["exact"] == ""
    payload = json.loads((tmp_path / "d17_audit_inventory.json").read_text(
        "utf-8"))
    assert payload["schema"] == "v72p2d17_audit_inventory_v1"
    assert payload["channel"]["H_L1"] == d17.H_L1
    assert payload["decoder"]["max_iter"] == 90
    assert "D9 thresholds/verdicts" in payload["de_transfer"][
        "no_numeric_transfer"]
    assert any("PROVISIONAL" in r["note"] or "D02" in r["note"]
               for r in rows)
    report = (tmp_path / "d17_audit_report.txt").read_text("utf-8")
    assert "empirical calibration" in report


# --------------------------------------------------------------------------- #
# No-production evidence
# --------------------------------------------------------------------------- #
def test_no_production_refs_in_source():
    for source in (MODULE_PATH.read_text(encoding="utf-8"),
                   RUNNER_PATH.read_text(encoding="utf-8")):
        assert "decode_row_layered_fftqspa" not in source
        assert "decode_flooding_fftqspa" not in source
        assert "run_mcde_posterior" not in source
        assert "nonbinary_v26_mcde" not in source
        assert "import numba" not in source
        assert "njit" not in source


def test_zero_scientific_counters_on_readiness_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(d17, "bind_production_de", _boom)
    monkeypatch.setattr(d17, "_load_sibling", _boom)
    desc = d17.describe_plan()
    assert desc["de_calls"] == 0 and desc["decoder_calls"] == 0
    assert runner.main(["--profile-only"]) == 0
    fresh = tmp_path / "fresh"
    assert runner.main(["--de-batch", "--out-root", str(fresh)]) == 2
    assert not fresh.exists()
