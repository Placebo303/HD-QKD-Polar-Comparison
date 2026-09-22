"""E08 focused tests for the D8 rate-aligned GF32 ensemble feasibility adapter
and runner.

Fresh ``workspace/<task>/<uuid>`` basetemps (``-p no:cacheprovider``); no
production decoder call; no DE scientific call; the frozen future root is never
created. The production decoder is neither bound nor called by the runner: the
sweep tests inject a fake DE callable and a synthetic tiny channel.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

ADAPTER_PATH = (SRC / "comparison_bench" / "formal_ir"
                / "v72p2d8_rate_aligned_ensemble.py")
RUNNER_PATH = ROOT / "scripts" / "v72p2d8_rate_aligned_ensemble_development.py"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = _load_module("v72p2d8_runner_test", RUNNER_PATH)
d8 = runner.d8
assert Path(d8.__file__).resolve() == ADAPTER_PATH


def _boom(*_args, **_kwargs):
    raise AssertionError("production path must not be entered")


def _tiny_fixture():
    """Synthetic tiny Model-F fixture: 1024 Alice (32 U1 x 32 U2), 4 Bob."""
    rng = np.random.default_rng(7)
    counts = rng.integers(0, 5, size=(1024, 4)).astype(np.float64)
    p_b = counts.sum(axis=0) / counts.sum()
    pb, p_f, p1 = d8.build_l1_channel_from_counts(counts, p_b)
    assert p1.shape == (d8.Q, 4)
    return pb, p_f, p1


def _fake_sweep(out, monkeypatch):
    """Run the full 126-call fake sweep (zero DE, zero decoder calls)."""
    monkeypatch.setattr(d8.v26, "run_mcde_posterior", _boom)
    calls = []

    def fake_de_call(lambda_edge, rho_edge, sampler, seed):
        calls.append((lambda_edge.get(2, 0.0), seed))
        scale = 1.0 - 0.5 * lambda_edge.get(2, 0.0)
        return {
            "entropy_trace_bits": [max(0.0, 5.0 - 0.2 * (t + 1)) * scale
                                   for t in range(60)],
            "channel_entropy_trace_bits": [5.0] * 60,
            "converged": True,
            "iterations": 60,
        }

    channel = _tiny_fixture()
    summary = runner.run_de_sweep("workspace/nonexistent_model_f", str(out),
                                  channel=channel, de_call=fake_de_call)
    return summary, calls


# --------------------------------------------------------------------------- #
# T0 constants
# --------------------------------------------------------------------------- #
def test_t0_frozen_constants():
    assert d8.Q == 32 and d8.POLY == 37
    assert d8.LAMBDA_STAR == 137.3823795883264
    assert d8.MODEL_F_INPUT_ROOT == "workspace/v72p2d5_model_f_input/20260907_r1"
    assert d8.mfi.MODEL_F_FORMAL_ROOT == d8.MODEL_F_INPUT_ROOT
    assert d8.SOLVER_ROOT == (
        "workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405")
    assert d8.DE_SEEDS == (2026091601, 2026091602, 2026091603)
    assert d8.N_SAMPLES == 4000 and d8.MAX_ITER == 60
    assert d8.ENTROPY_TOL_BITS == 1e-4 and d8.STREAK == 20
    assert d8.MAX_DE_CALLS == 126 and d8.MAX_SETUP_CALLS == 20
    assert d8.WALL_BUDGET_S == 1800.0 and d8.PER_CALL_BUDGET_S == 120.0
    assert d8.RSS_BUDGET_BYTES == 2 * 1024 ** 3
    assert d8.CONDITIONS == ("f1.2", "f1.0")
    assert d8.condition_m("f1.2") == 59 and d8.condition_m("f1.0") == 49
    assert tuple(runner.EVIDENCE_FILES) == (
        "manifest.json", "de_records.csv", "de_traces.csv",
        "candidate_summary.csv", "summary.json", "command_log.txt")
    assert set(d8.TERMINALS) == {
        "D8_DE_ADVANCE_ONE_ENSEMBLE", "D8_DE_NO_ADVANCE",
        "D8_DE_BASELINE_NOT_CONVERGED", "D8_DE_EVIDENCE_INVALID",
        "D8_DE_RESOURCE_BLOCKED", "D8_DE_NOT_RUN"}
    assert runner.FROZEN_COMMAND == (
        ".venv/bin/python scripts/v72p2d8_rate_aligned_ensemble_development.py "
        "--de-sweep --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 "
        "--out-root workspace/d8_rate_aligned_ensemble_"
        "5edf0630-f357-4a7e-b4c5-9ba955021405")


# --------------------------------------------------------------------------- #
# Channel sampler
# --------------------------------------------------------------------------- #
def test_sampler_rows_equal_floor_renorm_xor_centered_and_mass_one():
    pb, p_f, p1 = _tiny_fixture()
    sampler = d8.build_l1_sampler(pb, p_f, p1)
    n = 25
    rng_rows = np.random.default_rng(1234)
    rng_probe = np.random.default_rng(1234)
    rows = sampler(n, rng_rows)
    assert rows.shape == (n, d8.Q)
    assert np.allclose(rows.sum(axis=1), 1.0, rtol=0.0, atol=1e-12)
    assert np.all(rows >= 0.0)

    flat = (np.asarray(pb)[None, :] * np.asarray(p_f)).ravel()
    pick = rng_probe.choice(flat.size, size=n, p=flat)
    a = (pick // p_f.shape[1]).astype(np.int64)
    b = (pick % p_f.shape[1]).astype(np.int64)
    u = a // d8.Q
    idx = np.arange(d8.Q, dtype=np.int64)
    expected = np.empty((n, d8.Q), dtype=np.float64)
    for i in range(n):
        pr1 = d8.d5._floor_renorm(p1[:, b[i]].T, d8.DECODER_FLOOR)
        expected[i] = pr1[idx ^ u[i]]
    assert np.array_equal(rows, expected)


# --------------------------------------------------------------------------- #
# Rate / rho hand checks (design §3.5)
# --------------------------------------------------------------------------- #
def test_rate_rho_hand_checks():
    # (1) regular DV3 n64 L1 f1.2: target=59/192, dc=192/59, rho={3:11/16,4:5/16}
    conc = d8.v9.concentrated_check_distribution(5 / 64, {3: 1.0})
    assert conc["dc_lo"] == 3 and conc["dc_hi"] == 4
    assert conc["dc_mean"] == pytest.approx(192 / 59, abs=1e-12)
    assert conc["w_lo"] == pytest.approx(11 / 16, abs=1e-12)
    assert conc["w_hi"] == pytest.approx(5 / 16, abs=1e-12)
    assert conc["integral_rho"] == pytest.approx(59 / 192, abs=1e-12)

    # (2) regular DV3 n64 L1 f1.0: target=49/192, dc=192/49, rho={3:1/16,4:15/16}
    conc = d8.v9.concentrated_check_distribution(15 / 64, {3: 1.0})
    assert conc["dc_mean"] == pytest.approx(192 / 49, abs=1e-12)
    assert conc["w_lo"] == pytest.approx(1 / 16, abs=1e-12)
    assert conc["w_hi"] == pytest.approx(15 / 16, abs=1e-12)
    assert conc["integral_rho"] == pytest.approx(49 / 192, abs=1e-12)

    # (3) tiny ensemble A: n=8, m=5, lambda={2:1} -> R=3/8, rho={3:3/4,4:1/4}
    conc = d8.v9.concentrated_check_distribution(3 / 8, {2: 1.0})
    assert conc["dc_mean"] == pytest.approx(16 / 5, abs=1e-12)
    assert conc["w_lo"] == pytest.approx(3 / 4, abs=1e-12)
    assert conc["w_hi"] == pytest.approx(1 / 4, abs=1e-12)
    assert conc["integral_rho"] == pytest.approx(5 / 16, abs=1e-12)

    # (4) tiny ensemble B: n=9, m=6, lambda={3:1} -> R=1/3, rho={4:4/9,5:5/9}
    conc = d8.v9.concentrated_check_distribution(1 / 3, {3: 1.0})
    assert conc["dc_mean"] == pytest.approx(9 / 2, abs=1e-12)
    assert conc["w_lo"] == pytest.approx(4 / 9, abs=1e-12)
    assert conc["w_hi"] == pytest.approx(5 / 9, abs=1e-12)
    assert conc["integral_rho"] == pytest.approx(2 / 9, abs=1e-12)

    # (5) disclosure/efficiency: f = 5m/(n*H_L1) and R = 1 - f*H_L1/5
    h_l1 = 3.814742
    f12 = 5 * 59 / (64 * h_l1)
    f10 = 5 * 49 / (64 * h_l1)
    assert f12 == pytest.approx(1.20831, abs=1e-5)
    assert f10 == pytest.approx(1.00351, abs=1e-5)
    assert 1.0 - f12 * h_l1 / 5.0 == pytest.approx(5 / 64, abs=1e-12)
    assert d8.v26.target_rate_layer(f12, h_l1, 5) == pytest.approx(
        5 / 64, abs=1e-6)
    assert d8.v26.target_rate_layer(f10, h_l1, 5) == pytest.approx(
        15 / 64, abs=1e-6)


def test_baseline_regular_dv3_reproduction():
    lam = {3: 1.0}
    m, n = 59, 64
    rate, rho = d8.layer_rate_rho(m, n, lam)
    assert rate == 5 / 64
    assert d8.v9.edge_mean_inverse(lam) == pytest.approx(1 / 3, abs=1e-15)
    dbar_v = 1.0 / d8.v9.edge_mean_inverse(lam)
    dbar_c = dbar_v * n / m
    assert dbar_v == pytest.approx(3.0, abs=1e-12)
    assert dbar_c == pytest.approx(192 / 59, abs=1e-12)
    assert d8.v9.reconstructed_rate(lam, rho) == pytest.approx(
        5 / 64, abs=1e-12)
    assert set(rho) == {3, 4}
    assert rho[3] == pytest.approx(11 / 16, abs=1e-12)
    assert rho[4] == pytest.approx(5 / 16, abs=1e-12)


# --------------------------------------------------------------------------- #
# Enumeration / validation / refusal
# --------------------------------------------------------------------------- #
def test_candidate_enumeration_exactly_21_ascending_no_duplicates():
    cands = d8.enumerate_candidates()
    assert len(cands) == d8.CANDIDATE_COUNT == 21
    ids = [cand["candidate_id"] for cand in cands]
    assert len(set(ids)) == 21
    assert ids == sorted(ids)
    assert ids[0] == "lam_d2_0.00_d3_1.00"
    assert ids[-1] == "lam_d2_1.00_d3_0.00"
    assert [cand["lambda2"] for cand in cands] == [
        round(0.05 * i, 2) for i in range(21)]
    for cand in cands:
        assert set(cand["lambda_edge"]) <= {2, 3}
        assert sum(cand["lambda_edge"].values()) == pytest.approx(
            1.0, abs=1e-15)
        assert cand["candidate_id"] == "lam_d2_%.2f_d3_%.2f" % (
            cand["lambda2"], cand["lambda3"])
    plan = d8.build_candidate_plan()
    assert len(plan) == 42
    assert len({entry["candidate_id"] for entry in plan}) == 21
    assert all(entry["refused"] is False for entry in plan)
    assert d8.MAX_DE_CALLS == 21 * 2 * 3 == 126
    assert sum(1 for entry in plan if not entry["refused"]) * 3 == 126


def test_realized_max_check_degree_le_4_at_both_conditions():
    """E12/F1: realized check degree of the frozen grid <= 4 (spec bound 8).

    design.md §4 and spec.md state the actual maximum realized check degree of
    the frozen 21-candidate grid at both conditions is <= 4; the realization is
    the design §3 integer allocation (``d_lo``/``d_hi`` carry the positive rho
    weights). No other test asserted this realized maximum.
    """
    plan = d8.build_candidate_plan()
    assert len(plan) == 42
    for condition in d8.CONDITIONS:
        entries = [entry for entry in plan if entry["condition"] == condition]
        assert len(entries) == 21 and all(
            entry["refused"] is False for entry in entries)
        realized_max = max(
            max(int(degree) for degree, weight in entry["rho"].items()
                if weight > 0.0)
            for entry in entries)
        assert realized_max <= 4  # design.md:141 / spec.md:38
        assert realized_max <= 8  # spec.md:37 bound


@pytest.mark.parametrize("bad", [
    {1: 0.5, 3: 0.5},    # degree 1
    {2: -0.5, 3: 1.5},   # negative weight
    {2: 0.4, 3: 0.4},    # non-unit sum
    {4: 0.5, 3: 0.5},    # support outside {2,3}
])
def test_invalid_lambda_refused(bad):
    with pytest.raises(ValueError):
        d8.validate_lambda_edge(bad)
    assert d8.validate_lambda_edge({3: 1.0}) == {3: 1.0}
    assert d8.validate_lambda_edge({2: 0.25, 3: 0.75}) == {2: 0.25, 3: 0.75}


def test_make_rho_refusal_recorded_not_silently_dropped(monkeypatch):
    real_make_rho = d8.make_rho

    def flaky_make_rho(rate, lambda_edge):
        if lambda_edge.get(2) == 0.25:
            raise ValueError("implied mean check degree must be >= 2")
        return real_make_rho(rate, lambda_edge)

    monkeypatch.setattr(d8, "make_rho", flaky_make_rho)
    plan = d8.build_candidate_plan()
    assert len(plan) == 42  # no silent drop
    refused = [entry for entry in plan if entry["refused"]]
    assert len(refused) == 2
    assert all(entry["candidate_id"] == "lam_d2_0.25_d3_0.75"
               for entry in refused)
    assert all("implied mean check degree" in entry["refusal_reason"]
               for entry in refused)
    assert all(entry["rho"] is None and entry["rate"] is None
               for entry in refused)
    assert len([entry for entry in plan if not entry["refused"]]) == 40


# --------------------------------------------------------------------------- #
# Cross-kernel exact check
# --------------------------------------------------------------------------- #
def test_cross_kernel_unit_coefficients_equal_v14():
    v14 = d8._load_sibling("nonbinary_v14_mcde")
    rng = np.random.default_rng(11)
    n, q, max_draws = 6, 4, 3
    v2c = rng.random((n, q))
    v2c = v2c / v2c.sum(axis=1, keepdims=True)
    draws = np.array([3, 2, 1, 3, 2, 0], dtype=np.int64)
    idx = rng.integers(0, n, size=(max_draws, n)).astype(np.int64)
    perm, nonzero = d8.v26.build_gf_perm_table(q)
    assert len(nonzero) == q - 1
    coeff = np.ones((max_draws, n), dtype=np.int64)
    got = d8.v26._check_update_coeff_jit(v2c, draws, idx, coeff, perm)
    want = v14._check_update_jit(v2c, draws, idx)
    assert np.array_equal(got, want)


# --------------------------------------------------------------------------- #
# Fresh-root / no-overwrite refusal
# --------------------------------------------------------------------------- #
def test_fresh_root_and_protected_root_refusal(tmp_path):
    existing = tmp_path / "exists"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        runner.refuse_out_root(existing)
    for bad in ("workspace/v72p2d5_model_f_input/20260907_r1",
                "workspace/v72p2d5_g2/20260906_r1",
                "workspace/d6_graph_mother_r1c_"
                "dd8c4defe67742a8b2bc1b634c116d6b",
                "workspace/d7_r1_multigraph_20260913_r1",
                "comparison_bench/outputs_comparison/d8_probe"):
        with pytest.raises(ValueError):
            runner.refuse_out_root(bad)
    fresh = tmp_path / "fresh"
    assert runner.refuse_out_root(fresh) == fresh.resolve()
    assert not fresh.exists()
    rc = runner.main(["--de-sweep", "--model-f-root", str(tmp_path / "nope"),
                      "--out-root", str(existing)])
    assert rc == 2


# --------------------------------------------------------------------------- #
# Fake-runner isolation / full fake sweep / verify
# --------------------------------------------------------------------------- #
def test_fake_runner_isolation_full_sweep(tmp_path, monkeypatch):
    for source in (ADAPTER_PATH.read_text(encoding="utf-8"),
                   RUNNER_PATH.read_text(encoding="utf-8")):
        assert "decode_row_layered" not in source
        assert "v35_algorithm_development" not in source
    v35 = d8._load_sibling("v35_algorithm_development")
    monkeypatch.setattr(v35, "decode_row_layered_fftqspa", _boom)

    out = tmp_path / "sweep_root"
    summary, calls = _fake_sweep(out, monkeypatch)
    assert len(calls) == 126
    assert sorted(path.name for path in out.iterdir()) == sorted(
        runner.EVIDENCE_FILES)
    assert summary["terminal"] == d8.T_ADVANCE
    assert summary["winner_candidate_id"] == "lam_d2_1.00_d3_0.00"
    assert summary["de_calls"] == 126 and summary["setup_calls"] == 0
    assert summary["baseline_converged"] is True
    assert summary["baseline_primary_worst_aut_30"] == pytest.approx(
        65.0, abs=1e-12)
    assert "lam_d2_0.00_d3_1.00" not in summary["eligible_candidate_ids"]
    assert runner.verify_command(str(out)) is True
    assert runner.main(["--verify", "--out-root", str(out)]) == 0


def test_verify_detects_tampered_trace(tmp_path, monkeypatch):
    out = tmp_path / "sweep_root"
    _fake_sweep(out, monkeypatch)
    assert runner.verify_command(str(out)) is True
    rows = runner._read_csv(out / "de_traces.csv")
    trace = json.loads(rows[0]["entropy_trace_bits"])
    trace[10] = trace[10] + 1.0
    rows[0]["entropy_trace_bits"] = json.dumps(trace)
    runner._write_csv(out / "de_traces.csv", runner.DE_TRACE_COLUMNS, rows)
    assert runner.verify_command(str(out)) is False
