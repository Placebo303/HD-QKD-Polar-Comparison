"""Focused tests for the R7 synthetic DE rate-scan module + runner.

Fresh ``tmp_path`` roots only; zero scientific DE calls; zero production
decoder calls; zero graph construction; the frozen future root is never
created. Sweep tests inject a fake DE callable + fake L2-only channel +
real D9/D17 arithmetic; the production binder is never touched.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

MODULE_PATH = (SRC / "comparison_bench" / "formal_ir"
               / "v72p2r7_rate_scan.py")
RUNNER_PATH = (ROOT / "scripts" / "v72p2r7_rate_scan.py")


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = _load_module("v72p2r7_runner_test", RUNNER_PATH)
r7 = runner.r7
d18 = r7.d18
d17 = r7.d17


def _fake_channel():
    def _l2(*args, **kwargs):
        raise AssertionError("fake L2 sampler must never be invoked")
    _l2._d17_layer = "L2"  # layer tag required by resolve_sampler
    return {"L2": _l2}


def _fake_de_call(converged=True):
    tail = 1e-9 if converged else 5.0

    def _call(lambda_edge, rho_edge, channel_sampler, seed, n_samples):
        assert channel_sampler is _fake_channel_singleton[0]
        trace = [5.0 - 0.05 * t for t in range(60)]
        trace[-1] = tail
        return {"entropy_trace_bits": list(trace)}
    return _call


_fake_channel_singleton = []


def _run_fake(tmp_path, converged=True, **kw):
    chan = _fake_channel()
    _fake_channel_singleton[:] = [chan["L2"]]
    return r7.run_r7_sweep(
        str(tmp_path / "root"), "model-f-root-unused",
        channel=chan, de_call=_fake_de_call(converged),
        rho_fn=lambda cid, m: d18.rho_for(cid, int(m)), **kw)


def test_frozen_grid_winner_seeds_cap():
    assert r7.R7_GRID_M == (100, 104, 108, 112, 116, 120, 124, 128)
    assert r7.WINNER_ID == "lam_d2_0.20_d3_0.80" and r7.WINNER_X == 0.20
    assert len(r7.R7_DE_SEEDS) == 8 and len(set(r7.R7_DE_SEEDS)) == 8
    assert list(r7.R7_POPS) == [4000, 16000]
    assert r7.R7_PLANNED_CALLS == 128 and r7.R7_DE_CAP == 200
    assert r7.R7_PLANNED_CALLS <= r7.R7_DE_CAP
    assert r7.R7_PLANNED_CALLS + r7.R7_PLANNED_CALLS > r7.R7_DE_CAP  # DV3 drop
    assert r7.MARGIN_DELTA == 0.0390625 == d18.ROW_STEP
    assert d17.DECODER_MAX_ITER == 90 and d17.DAMPING_ALPHA == 1.0


def test_feasibility_all_executable_zero_calls():
    feas = r7.feasibility_table()
    assert len(feas) == 8
    assert all(f["executable"] and f["refusal_reason"] is None for f in feas)
    assert {f["m"] for f in feas} == set(r7.R7_GRID_M)
    plan = r7.build_r7_plan(feas)
    assert len(plan) == 128
    assert [e["call_idx"] for e in plan] == list(range(128))
    assert sum(1 for e in plan if e["refused"]) == 0


def test_bracket_verbatim_on_d18_and_d17_grids():
    grid = (89, 94, 99, 104, 109)
    cases = [
        ({89: 0, 94: 8, 99: 8, 104: 8, 109: 8}, None),
        ({89: 0, 94: 0, 99: 8, 104: 8, 109: 8}, None),
        ({89: 0, 94: 4, 99: 8, 104: 8, 109: 8}, None),
        ({89: 8, 94: 8, 99: 8, 104: 8, 109: 8}, None),
        ({89: 0, 94: 0, 99: 0, 104: 0, 109: 0}, None),
        ({89: 0, 94: 8, 99: 8, 104: 8, 109: 8},
         {89: 0, 94: 0, 99: 8, 104: 8, 109: 8}),
    ]
    for s16, s4 in cases:
        got = r7.r7_bracket(dict(s16), dict(s4) if s4 else None, grid=grid)
        ref18 = d18.candidate_bracket(dict(s16), dict(s4) if s4 else None)
        ref17 = d17.bracket_delta_de("L2", dict(s16), dict(s4) if s4 else None)
        for ref in (ref18, ref17):
            assert got["flag"] == ref["flag"]
            assert got["lo_m"] == ref["lo_m"] and got["hi_m"] == ref["hi_m"]
            assert got["flags"] == ref["flags"]
            if got["delta_de"] is None:
                assert ref["delta_de"] is None
            else:
                assert abs(got["delta_de"] - ref["delta_de"]) == 0.0


def test_bar_strict_direction_and_tail_bracketing():
    bar = r7.bar_value()
    thr = bar - 1e-6
    s = {m: 8 for m in r7.R7_GRID_M}
    out = r7.apply_bar({"delta_de": thr}, dict(s), dict(s))
    assert out["bar_holds"] and out["min_m"] == 100
    assert all(out["pass"].values())
    out = r7.apply_bar({"delta_de": bar}, dict(s), dict(s))
    assert not out["bar_holds"] and out["min_m"] is None  # strict: equal FAILS
    out = r7.apply_bar({"delta_de": bar + 1.0}, dict(s), dict(s))
    assert not out["bar_holds"]
    out = r7.apply_bar({"delta_de": None, "flag": "NO_BRACKET"}, dict(s), dict(s))
    assert not out["bar_holds"] and out["terminal_m"] == "NO-FEASIBLE-m"
    s2 = dict(s)
    s2[128] = 0  # top-m unconverged breaks every tail
    out = r7.apply_bar({"delta_de": thr}, dict(s2), dict(s2))
    assert out["bar_holds"] and out["min_m"] is None
    assert not any(out["pass"].values())


def test_seed_disjointness_includes_g6():
    assert 2026094601 in r7.PRIOR_SEED_RANGES["g6_graphs"]
    assert 2026094602 in r7.PRIOR_SEED_RANGES["g6_graphs"]
    rep = r7.verify_seed_disjointness()
    assert rep["passed"]


def test_fake_full_sweep_ledger_and_min_m(tmp_path):
    bundle = _run_fake(tmp_path)
    assert bundle["terminal"] == r7.T_COMPLETE
    assert bundle["ledger"]["consumed"] == 128
    assert [r["ledger_after"] for r in bundle["records"]] == list(range(1, 129))
    assert bundle["bracket"]["flag"] == d17.F_ONE_SIDED_LOW
    assert bundle["bracket"]["hi_m"] == 100
    assert bundle["bar"]["bar_holds"] and bundle["min_m"] == 100
    assert bundle["decoder_calls"] == 0 and bundle["graphs_constructed"] == 0
    summary = r7.write_r7_root(bundle)
    assert summary["s7_min"] == 100
    assert summary["s7_dv3"]["ran"] is False
    assert len(summary["s7_arith"]["sheets"]) == 8
    assert sum(len(v) for v in
               summary["s7_arith"]["graph_assignment"].values()) <= 9
    assert r7.verify_r7_root(str(tmp_path / "root"))


def test_cap_halt_path_and_refusal(tmp_path, monkeypatch):
    monkeypatch.setattr(r7, "R7_DE_CAP", 5)
    bundle = _run_fake(tmp_path)
    assert bundle["terminal"] == r7.T_INCOMPLETE_CAP
    assert bundle["ledger"]["consumed"] == 5
    assert bundle["halted"].startswith("CAP_HIT")
    assert bundle["min_m"] == "INCOMPLETE-cap"
    rc = runner.main(["--de-sweep", "--out-root",
                      str(tmp_path / "never")])
    assert rc == 2
    assert not (tmp_path / "never").exists()


def test_m_grid_override_low_branch_and_default_unchanged(tmp_path, capsys):
    # Default grid/cap frozen: override path must not move them.
    assert r7.R7_GRID_M == (100, 104, 108, 112, 116, 120, 124, 128)
    assert r7.R7_DE_CAP == 200 and r7.R7_PLANNED_CALLS == 128
    assert r7.R8_GRID_M == (88, 92, 96) and r7.R8_DE_CAP == 60
    assert r7.R8_PLANNED_CALLS == 48
    prof = r7.describe_plan()
    assert prof["grid_m"] == list(r7.R7_GRID_M) and prof["cap"] == 200
    # Override works end-to-end on fakes: 3x8x2 = 48 calls, cap 60.
    chan = _fake_channel()
    _fake_channel_singleton[:] = [chan["L2"]]
    bundle = r7.run_r7_sweep(
        str(tmp_path / "low"), "model-f-root-unused",
        channel=chan, de_call=_fake_de_call(True),
        rho_fn=lambda cid, m: d18.rho_for(cid, int(m)),
        grid=(88, 92, 96), cap=60)
    assert bundle["terminal"] == r7.T_COMPLETE
    assert bundle["ledger"] == {"cap": 60, "consumed": 48}
    assert sorted(bundle["table"]) == ["88", "92", "96"]
    assert bundle["bracket"]["hi_m"] == 88  # all-converged: one-sided low
    summary = r7.write_r7_root(bundle)
    assert summary["s7_min"] == 88 and summary["s7_ledger"]["cap"] == 60
    assert r7.verify_r7_root(str(tmp_path / "low"))
    # Runner flag threads the same override into profile-only (zero calls).
    rc = runner.main(["--profile-only", "--m-grid", "88,92,96",
                      "--de-cap", "60"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["grid_m"] == [88, 92, 96] and out["cap"] == 60
    assert out["planned_calls"] == 48 and out["within_cap"] is True
