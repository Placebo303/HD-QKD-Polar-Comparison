"""Focused E06/E07 tests for the D18 L2-ensemble readiness module + runner.

Fresh ``tmp_path`` roots; zero scientific DE calls; zero production decoder
calls; the frozen future root is never created. All sweep tests inject a
fake DE callable + fake L2-only channel + real D9 rho arithmetic; the
production binder is monkeypatched to fail if touched on refusal,
PROFILE_ONLY, and fake paths.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

MODULE_PATH = (SRC / "comparison_bench" / "formal_ir"
               / "v72p2d18_l2_ensemble_de.py")
RUNNER_PATH = (ROOT / "scripts" / "v72p2d18_ensemble_development.py")


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = _load_module("v72p2d18_runner_test", RUNNER_PATH)
d18 = runner.d18
assert Path(d18.__file__).resolve() == MODULE_PATH


def _boom(*_args, **_kwargs):
    raise AssertionError("production path must not be entered")


# --------------------------------------------------------------------------- #
# Fake machinery (deterministic; injected, never the V26 kernel)
# --------------------------------------------------------------------------- #
def _tagged_fake_sampler(peak=0.7):
    def sampler(n, rng):
        k = int(n)
        rows = np.full((k, 32), (1.0 - float(peak)) / 31.0)
        rows[:, 0] = float(peak)
        return rows

    sampler._d17_layer = "L2"
    return sampler


class _SchedFakeDE:
    """Stateful fake: convergence per (candidate_id, m); 60-traces."""

    def __init__(self, schedule):
        self.schedule = dict(schedule)
        self.calls = []
        self.keys = []

    def __call__(self, lambda_edge, rho_edge, channel, seed, n_samples):
        assert callable(channel)
        assert getattr(channel, "_d17_layer", None) == "L2"
        self.calls.append(channel)
        x = float(dict(lambda_edge).get(2, 0.0))
        cid = "lam_d2_%.2f_d3_%.2f" % (x, 1.0 - x)
        # m is recovered from rho identity against the frozen table.
        m = self._m_of(cid, rho_edge)
        self.keys.append((cid, int(m), int(n_samples), int(seed)))
        converged = bool(self.schedule[(cid, int(m))])
        final = 1e-6 if converged else 0.5
        trace = [max(final, 5.0 - 0.2 * t) for t in range(1, 60)] + [final]
        return {"entropy_trace_bits": trace,
                "channel_entropy_trace_bits": [5.0] * 60}

    @staticmethod
    def _m_of(cid, rho_edge):
        for m in d18.GRID_M:
            rho = d18.rho_for(cid, m)
            if set(rho_edge) == set(rho) and all(
                    abs(rho_edge[k] - rho[k]) < 1e-12 for k in rho):
                return int(m)
        raise AssertionError("rho outside the frozen table")


def _fakes(schedule):
    l2 = _tagged_fake_sampler()
    return {"channel": {"L2": l2}, "de_call": _SchedFakeDE(schedule),
            "rho_fn": d18.rho_for,
            "now_fn": None, "rss_fn": lambda: 0}


WINNER = "lam_d2_0.55_d3_0.45"


def _select_one_schedule():
    sched = {}
    for cand in d18.enumerate_candidates():
        cid = cand["candidate_id"]
        for m in d18.GRID_M:
            if cid == d18.DV3_CONTROL_ID:
                sched[(cid, m)] = m >= 99  # lo94/hi99 clean DV3
            elif cid == WINNER:
                sched[(cid, m)] = m >= 94  # lo89/hi94 eligible winner
            else:
                sched[(cid, m)] = m >= 104  # lo99/hi104 ineligible
    return sched


def _no_improving_schedule():
    sched = {}
    for cand in d18.enumerate_candidates():
        cid = cand["candidate_id"]
        for m in d18.GRID_M:
            if cid == d18.DV3_CONTROL_ID:
                sched[(cid, m)] = m >= 99
            else:
                sched[(cid, m)] = m >= 109  # lo104/hi109 ineligible
    return sched


def _drift_schedule():
    sched = _select_one_schedule()
    for m in d18.GRID_M:
        sched[(d18.DV3_CONTROL_ID, m)] = m >= 104  # lo99/hi104 drift
    return sched


def _run_fake(schedule, tmp_path, monkeypatch):
    monkeypatch.setattr(d18.d17, "bind_production_de", _boom)
    monkeypatch.setattr(d18.d17, "build_production_channels", _boom)
    out = tmp_path / "fake_root"
    inj = _fakes(schedule)
    bundle = d18.run_de_sweep(str(out), d18.MODEL_F_INPUT_ROOT, **inj)
    summary = d18.write_de_root(bundle)
    return bundle, summary, inj, out


# --------------------------------------------------------------------------- #
# T0 frozen constants / reuse / budgets
# --------------------------------------------------------------------------- #
def test_t0_adjudication_frozen():
    assert d18.L055_VERDICT == "FALSIFIED"
    assert d18.L055_OBSERVED == (27, 32)
    assert d18.P_LO == 0.8899387155669418
    assert d18.P_HI == 0.9955050869733582
    assert d18.L055_PER_GRAPH == (7, 7, 6, 7)
    rec = d18.adjudication_record()
    assert rec["l055_verdict"] == "FALSIFIED"
    assert "NOT an L1-construction failure" in rec["interpretation_ceiling"]
    assert "NOT recomputed" in rec["methodology_amendment"]


def test_t0_family_grid_ids():
    cands = d18.enumerate_candidates()
    assert len(cands) == 21
    assert [c["candidate_id"] for c in cands] == [
        "lam_d2_%.2f_d3_%.2f" % (x, 1.0 - x) for x in d18.candidate_xs()]
    assert d18.DV3_CONTROL_ID == "lam_d2_0.00_d3_1.00"
    assert sum(1 for c in cands if c["is_dv3_control"]) == 1
    assert cands[0]["lambda_edge"] == {3: 1.0}
    assert cands[-1]["lambda_edge"] == {2: 1.0}
    for c in cands:
        assert set(c["lambda_edge"]) <= {2, 3}  # no CE/f labels
        assert abs(sum(c["lambda_edge"].values()) - 1.0) < 1e-9
    assert d18.GRID_M == (89, 94, 99, 104, 109)
    assert d18.STAGE_S_M == (94, 104)


def test_t0_threshold_arithmetic():
    assert d18.DV3_BASELINE_DELTA_DE == 0.5468113653656221
    assert d18.DV3_BASELINE_DELTA_DE == d18.d17.A3_DELTA_DE["L2"][0]
    assert d18.ROW_STEP == 5.0 / 128.0 == 0.0390625
    assert d18.ELIGIBILITY_DELTA_DE == 0.5077488653656221
    assert abs((d18.DV3_BASELINE_DELTA_DE - d18.ROW_STEP)
               - d18.ELIGIBILITY_DELTA_DE) < 1e-18


def test_t0_reuse_identity(monkeypatch):
    import comparison_bench.formal_ir.v72p2d17_descaling as live_d17
    import comparison_bench.formal_ir.v72p2d9_de_decoder_calibration as live_d9
    import comparison_bench.formal_ir.v37_degree_feasibility as live_v37f
    assert d18.d17 is live_d17 and d18.d9 is live_d9 and d18.v37f is live_v37f
    assert (d18.d9.Q, d18.d9.POLY) == (32, 37)
    assert (d18.DE_MAX_ITER, d18.DE_ENTROPY_TOL_BITS, d18.DE_STREAK) == (60, 1e-4, 20)
    proof = d18.verify_reuse_identity()
    assert proof["passed"], proof["checks"]
    assert "oracle_prior_fn(p2, b, u1)" in inspect.getsource(
        d18.d17.build_l2_oracle_sampler)  # true-U1 conditioning provenance
    assert "XOR" in inspect.getsource(d18.d17.build_l2_oracle_sampler)


def test_t0_budgets_command():
    assert d18.MAX_DE_CALLS == 456 and d18.MAX_SETUP_CALLS == 16
    assert d18.SETUP_UNITS == 4
    assert d18.WALL_BUDGET_S == 1800.0 and d18.PER_CALL_BUDGET_S == 300.0
    assert d18.RSS_BUDGET_BYTES == 2 * 1024 ** 3
    assert d18.FROZEN_COMMAND == (
        ".venv/bin/python scripts/v72p2d18_ensemble_development.py --de-sweep "
        "--execution-authorized --model-f-root "
        "workspace/v72p2d5_model_f_input/20260907_r1 --out-root "
        "workspace/d18_l2_ensemble_de_"
        "98abed5a-af4f-4780-9e83-54cccba28901")
    assert runner.FROZEN_COMMAND == d18.FROZEN_COMMAND
    assert tuple(runner.EVIDENCE_FILES) == (
        "manifest.json", "de_plan.csv", "de_records.csv", "de_traces.csv",
        "summary.json", "command_log.txt")
    assert d18.FUTURE_ROOT.startswith("workspace/d18_l2_ensemble_de_")
    assert not Path(d18.FUTURE_ROOT).exists()
    parser = runner.build_parser()
    assert parser.parse_args(["--profile-only"]).execution_authorized is False


def test_t0_seeds_frozen():
    assert d18.STAGE_S_SEEDS == tuple(range(2026094301, 2026094305))
    assert d18.STAGE_C_SEEDS == tuple(range(2026094301, 2026094309))
    assert d18.STAGE_S_POP == 4000 and d18.STAGE_C_POPS == (4000, 16000)


# --------------------------------------------------------------------------- #
# T1 feasibility / plans / selection / dispatch
# --------------------------------------------------------------------------- #
def test_feasibility_all_executable():
    feas = d18.feasibility_table()
    assert len(feas) == 105  # 21 x 5
    assert sum(1 for r in feas if r["executable"]) == 105
    assert sum(1 for r in feas if not r["executable"]) == 0
    want_delta = {89: 0.25384, 94: 0.44916, 99: 0.64447, 104: 0.83978,
                  109: 1.03509}
    for r in feas:
        assert abs(sum(r["rho"].values()) - 1.0) < 1e-9
        assert r["check_counts"] and min(r["check_counts"]) >= 2
        assert r["max_check_degree"] <= 8
        assert round(r["delta"], 5) == want_delta[r["m"]]
        assert abs(r["rate"] - (1.0 - r["m"] / 128.0)) < 1e-18


def test_gate_refusal_cases():
    ok, _ = d18.gate_cell(307, 104, d18.rho_for("lam_d2_0.50_d3_0.50", 104))
    assert ok
    ok, reason = d18.gate_cell(100, 89, {2: 0.5, 3: 0.5})
    assert not ok and "min_dc<2" in reason
    ok, reason = d18.gate_cell(800, 89, {4: 0.5, 5: 0.5})
    assert not ok and "max_dc>8" in reason
    ok, reason = d18.gate_cell(300, 100, {3: 0.2})
    assert not ok and "rho_unnormalized" in reason
    ok, reason = d18.gate_cell(0, 89, {})
    assert not ok and "invalid_realization" in reason


def test_stage_s_plan_counts_order():
    plan = d18.build_stage_s_plan()
    assert len(plan) == 168
    assert [e["call_idx"] for e in plan] == list(range(168))
    first, last = plan[0], plan[-1]
    assert (first["candidate_id"], first["m"], first["seed"]) == (
        "lam_d2_0.00_d3_1.00", 94, 2026094301)
    assert (last["candidate_id"], last["m"], last["seed"]) == (
        "lam_d2_1.00_d3_0.00", 104, 2026094304)
    assert all(e["layer"] == "L2" and e["population"] == 4000 for e in plan)
    assert all(not e["refused"] for e in plan)


def test_stage_c_plan_overlap_dedup():
    selected = [c["candidate_id"] for c in d18.enumerate_candidates()[:4]]
    plan_c = d18.build_stage_c_plan(selected)
    assert len(plan_c) == 320  # 4 x 5 x 8 x 2
    reused = [e for e in plan_c if e["reused"]]
    assert len(reused) == 32  # 4 x 2 x 4 x 1
    assert len(plan_c) - len(reused) == 288
    assert d18.stage_counts() == {
        "stage_s_max": 168, "stage_c_identities": 320,
        "overlap_reused": 32, "stage_c_new_max": 288, "total_ceiling": 456}
    s_ids = {d18.stage_s_identity(e) for e in d18.build_stage_s_plan()
             if e["candidate_id"] in set(selected)}
    assert {(e["candidate_id"], e["m"], e["population"], e["seed"])
            for e in reused} == s_ids
    with pytest.raises(ValueError):
        d18.build_stage_c_plan(selected[:3])


def _summaries_for(order_ids, s94=4, s104=4, h94=1e-6, h104=1e-6):
    return {cid: {"candidate_id": cid, "S_m94": s94, "S_m104": s104,
                  "calls_m94": 4, "calls_m104": 4,
                  "worst_H60_m94": h94, "worst_H60_m104": h104}
            for cid in order_ids}


def test_selection_ties_and_composition():
    ids = [c["candidate_id"] for c in d18.enumerate_candidates()]
    summaries = _summaries_for(ids)  # full tie -> id-ascending top 3 + DV3
    sel = d18.select_stage_s(summaries, ids)
    assert sel["terminal"] is None
    assert sel["selected"] == sorted(
        c for c in ids if c != d18.DV3_CONTROL_ID)[:3] + [d18.DV3_CONTROL_ID]
    # Worst-H60 tiebreak: equal S, lower worst wins over id order.
    summaries["lam_d2_1.00_d3_0.00"]["worst_H60_m94"] = 1e-7
    sel = d18.select_stage_s(summaries, ids)
    assert sel["selected"][0] == "lam_d2_1.00_d3_0.00"


def test_selection_blocked_edges():
    ids = [c["candidate_id"] for c in d18.enumerate_candidates()]
    summaries = _summaries_for(ids)
    sel = d18.select_stage_s(summaries, ids[:2] + [d18.DV3_CONTROL_ID])
    assert sel["terminal"] == d18.T_ENGINEERING_BLOCKED
    sel = d18.select_stage_s(
        summaries, [c for c in ids if c != d18.DV3_CONTROL_ID])
    assert sel["terminal"] == d18.T_ENGINEERING_BLOCKED  # DV3 refused
    bad = _summaries_for(ids)
    bad[ids[0]]["calls_m94"] = 3
    with pytest.raises(ValueError):
        d18.rank_stage_s(bad, ids)


def test_bracket_identity_with_d17():
    s16 = {89: 0, 94: 0, 99: 8, 104: 8, 109: 8}
    s4 = dict(s16)
    got = d18.candidate_bracket(s16, s4)
    want = d18.d17.bracket_delta_de("L2", s16, s4)
    assert got["flag"] == want["flag"] == "DE_BRACKET"
    assert (got["lo_m"], got["hi_m"]) == (want["lo_m"], want["hi_m"]) == (94, 99)
    assert abs(got["delta_de"] - want["delta_de"]) < 1e-18
    assert got["flags"] == want["flags"]
    assert abs(got["delta_de"] - d18.DV3_BASELINE_DELTA_DE) < 1e-18


def test_sampler_dispatch_l2_only():
    l2 = _tagged_fake_sampler()
    assert d18.resolve_sampler({"L2": l2}) is l2
    assert d18.resolve_sampler({"L2": l2}, "L2") is l2
    with pytest.raises(ValueError):
        d18.resolve_sampler({"L2": l2}, "APP")
    with pytest.raises(ValueError):
        d18.resolve_sampler({"L2": l2}, "L045")
    with pytest.raises(ValueError):
        d18.resolve_sampler({})
    with pytest.raises(ValueError):
        d18.resolve_sampler({"L2": lambda n, rng: np.zeros((n, 32))})
    shared = _tagged_fake_sampler()
    with pytest.raises(ValueError):
        d18.resolve_sampler({"L2": shared, "L045": shared})


def test_app_l1_exclusion():
    for e in d18.build_stage_s_plan():
        assert e["layer"] == "L2" and "APP" not in str(e)
    for r in d18.feasibility_table():
        assert set(r) == {"candidate_id", "x", "m", "rate", "delta", "n2",
                          "n3", "E", "check_counts", "max_check_degree",
                          "rho", "executable", "refusal_reason"}


def test_descriptive_tail_values():
    t_lo = d18.binomial_tail(d18.P_LO)
    t_hi = d18.binomial_tail(d18.P_HI)
    assert abs(t_lo - 0.2730308351705778) < 1e-12  # descriptive only
    assert abs(t_hi - 3.3394200787523175e-07) < 1e-16  # descriptive only
    assert d18.L055_VERDICT == "FALSIFIED"  # never revised by description


def test_seed_disjointness():
    proof = d18.verify_seed_disjointness()
    assert proof["passed"], proof["hits"]
    assert proof["de_seeds"] == list(range(2026094301, 2026094309))
    assert all(not hits for hits in proof["hits"].values())


def test_no_exact_syndrome_undetected_merge():
    assert tuple(d18.DE_RECORD_COLUMNS) == (
        "call_idx", "stage", "candidate_id", "m", "rate", "population",
        "seed", "converged", "iterations", "h60", "reused", "wall_s")
    assert not {"exact", "syndrome", "undetected"} & set(d18.DE_RECORD_COLUMNS)


# --------------------------------------------------------------------------- #
# Fake complete runs (zero production entry; overlap never rerun)
# --------------------------------------------------------------------------- #
def test_fake_select_one(tmp_path, monkeypatch):
    bundle, summary, inj, out = _run_fake(_select_one_schedule(), tmp_path,
                                          monkeypatch)
    assert summary["terminal"] == d18.T_SELECT_ONE
    assert summary["winner_candidate_id"] == WINNER
    assert summary["scientific_calls"] == 456  # 168 + 288 new
    assert len(inj["de_call"].calls) == 456
    s_ids = {d18.stage_s_identity(e) for e in bundle["plan_s"]
             if not e["refused"]}
    assert set(inj["de_call"].keys[:168]) == s_ids  # Stage S in plan order
    c_new_ids = {(e["candidate_id"], e["m"], e["population"], e["seed"])
                 for e in bundle["plan_c"]
                 if not e["refused"] and not e["reused"]}
    assert len(c_new_ids) == 288
    assert set(inj["de_call"].keys[168:]) == c_new_ids
    assert not (set(inj["de_call"].keys[168:]) & s_ids)  # 32 never rerun
    assert all(s is inj["channel"]["L2"] for s in inj["de_call"].calls)
    assert d18.verify_de_root(str(out)) is True


def test_fake_no_improving(tmp_path, monkeypatch):
    bundle, summary, inj, out = _run_fake(_no_improving_schedule(), tmp_path,
                                          monkeypatch)
    assert summary["terminal"] == d18.T_NO_IMPROVING
    assert summary["winner_candidate_id"] is None
    assert summary["scientific_calls"] == 456
    assert d18.verify_de_root(str(out)) is True


def test_fake_baseline_drift(tmp_path, monkeypatch):
    bundle, summary, inj, out = _run_fake(_drift_schedule(), tmp_path,
                                          monkeypatch)
    assert summary["terminal"] == d18.T_BASELINE_DRIFT
    assert summary["winner_candidate_id"] is None
    assert summary["decision"]["baseline_drift"] is True


def test_fake_engineering_blocked_on_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(d18.d17, "bind_production_de", _boom)
    sched = _select_one_schedule()

    class _Crash(_SchedFakeDE):
        def __call__(self, lambda_edge, rho_edge, channel, seed, n_samples):
            if len(self.calls) == 10:
                raise RuntimeError("synthetic crash")
            return super().__call__(lambda_edge, rho_edge, channel, seed,
                                    n_samples)

    l2 = _tagged_fake_sampler()
    out = tmp_path / "blocked_root"
    bundle = d18.run_de_sweep(
        str(out), d18.MODEL_F_INPUT_ROOT, channel={"L2": l2},
        de_call=_Crash(sched), rho_fn=d18.rho_for,
        rss_fn=lambda: 0)
    assert bundle["summary"]["terminal"] == d18.T_ENGINEERING_BLOCKED
    assert bundle["summary"]["scientific_calls"] == 10
    summary = d18.write_de_root(bundle)
    assert summary["terminal"] == d18.T_ENGINEERING_BLOCKED
    assert d18.verify_de_root(str(out)) is False  # blocked never PASSes


# --------------------------------------------------------------------------- #
# Runner: refusal / no-overwrite / tamper / profile-only
# --------------------------------------------------------------------------- #
def test_runner_refusal_before_root_bind(tmp_path, monkeypatch):
    monkeypatch.setattr(d18.d17, "bind_production_de", _boom)
    monkeypatch.setattr(d18.d17, "build_production_channels", _boom)
    out = tmp_path / "must_not_exist"
    assert runner.main(["--de-sweep", "--out-root", str(out)]) == 2
    assert not out.exists()
    assert not Path(d18.FUTURE_ROOT).exists()


def test_runner_no_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(d18.d17, "bind_production_de", _boom)
    out = tmp_path / "existing"
    out.mkdir()
    (out / "sentinel.txt").write_text("keep", encoding="utf-8")
    inj = _fakes(_select_one_schedule())
    with pytest.raises((FileExistsError, ValueError)):
        d18.run_de_sweep(str(out), d18.MODEL_F_INPUT_ROOT, **inj)
    assert (out / "sentinel.txt").read_text(encoding="utf-8") == "keep"


def test_verify_tamper_and_read_only(tmp_path, monkeypatch):
    bundle, summary, inj, out = _run_fake(_select_one_schedule(), tmp_path,
                                          monkeypatch)
    before = {p.name: (out / p.name).read_bytes() for p in out.iterdir()}
    assert d18.verify_de_root(str(out)) is True
    assert {p.name: (out / p.name).read_bytes() for p in out.iterdir()} == before
    rec_path = out / "de_records.csv"
    text = rec_path.read_text(encoding="utf-8")
    tampered = text.replace("1e-06", "0.5", 1)
    assert tampered != text
    rec_path.write_text(tampered, encoding="utf-8")
    assert d18.verify_de_root(str(out)) is False


def test_e07_profile_only_zero_calls(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(d18.d17, "bind_production_de", _boom)
    monkeypatch.setattr(d18.d17, "build_production_channels", _boom)
    assert runner.main(["--profile-only"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["counts"] == {
        "stage_s_max": 168, "stage_c_identities": 320,
        "overlap_reused": 32, "stage_c_new_max": 288, "total_ceiling": 456}
    assert len(payload["candidates"]) == 21
    assert payload["executable_cells"] == 105 and payload["refused_cells"] == 0
    assert payload["de_calls"] == 0 and payload["decoder_calls"] == 0
    assert payload["future_root_absent"] is True
    assert payload["adjudication"]["l055_verdict"] == "FALSIFIED"
    assert not Path(d18.FUTURE_ROOT).exists()
