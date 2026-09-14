"""Focused tests for the D9 GF32 DE-decoder calibration module and runner (C08).

Fresh ``workspace/<task>/<uuid>`` basetemps (``-p no:cacheprovider``); no
production/finite-length decoder call; no scientific DE call; the frozen future
root is never created. The calibration tests inject a fake DE callable and a
synthetic tiny channel; the production decoder entrypoints are monkeypatched to
fail if touched.
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

MODULE_PATH = (SRC / "comparison_bench" / "formal_ir"
               / "v72p2d9_de_decoder_calibration.py")
RUNNER_PATH = (ROOT / "scripts"
               / "v72p2d9_de_decoder_calibration_development.py")


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = _load_module("v72p2d9_runner_test", RUNNER_PATH)
d9 = runner.d9
assert Path(d9.__file__).resolve() == MODULE_PATH


def _boom(*_args, **_kwargs):
    raise AssertionError("production path must not be entered")


def _tiny_channel():
    """Synthetic tiny Model-F fixture: 1024 Alice (32 U1 x 32 U2), 4 Bob."""
    rng = np.random.default_rng(7)
    counts = rng.integers(0, 5, size=(1024, 4)).astype(np.float64)
    p_b = counts.sum(axis=0) / counts.sum()
    return d9.build_l1_channel_from_counts(counts, p_b)


_SPEED = {0.0: 0.18, 0.45: 0.26, 0.50: 0.30, 0.55: 0.22}


def _fake_de_call(lambda_edge, rho_edge, sampler, seed, n_samples):
    """Deterministic fake DE: DV3 never converges; 0.45/0.50 always; 0.55 7/8."""
    lam2 = lambda_edge.get(2, 0.0)
    rank = list(d9.DE_SEEDS).index(int(seed))
    if lam2 == 0.0:
        converged = False
    elif lam2 in (0.45, 0.50):
        converged = True
    else:
        converged = rank < 7
    final = 1e-6 if converged else 0.5
    speed = _SPEED[lam2] - 0.001 * rank
    trace = [max(final, 5.0 - speed * t) for t in range(1, 60)] + [final]
    return {"entropy_trace_bits": trace,
            "channel_entropy_trace_bits": [5.0] * 60,
            "converged": converged}


def _fake_calibration(out, monkeypatch, **seams):
    monkeypatch.setattr(d9.v26, "run_mcde_posterior", _boom)
    monkeypatch.setattr(d9.v35, "decode_row_layered_fftqspa", _boom)
    monkeypatch.setattr(d9.v35, "decode_flooding_fftqspa", _boom)
    channel = _tiny_channel()
    return runner.run_calibration("workspace/nonexistent_model_f", str(out),
                                  channel=channel, de_call=_fake_de_call,
                                  **seams)


def _synthetic_records(converged_by_candidate, aut_by_candidate):
    """96 synthetic records (8 seeds x 3 groups) for routing unit tests."""
    records = []
    for cand in d9.enumerate_candidates():
        cid = cand["candidate_id"]
        conv = converged_by_candidate[cid]
        aut = aut_by_candidate[cid]
        for condition, population in (("f1.2", 4000), ("f1.2", 16000),
                                      ("f1.0", 4000)):
            for idx, seed in enumerate(d9.DE_SEEDS):
                records.append({
                    "candidate_id": cid, "condition": condition,
                    "population": population, "seed": int(seed),
                    "converged": bool(conv[idx % len(conv)]),
                    "aut_30": float(aut), "t_001": 30})
    return records


# --------------------------------------------------------------------------- #
# T0 frozen constants / exact future command
# --------------------------------------------------------------------------- #
def test_t0_frozen_constants_and_command():
    assert d9.Q == 32 and d9.POLY == 37
    assert d9.LAMBDA_STAR == 137.3823795883264
    assert d9.MODEL_F_INPUT_ROOT == "workspace/v72p2d5_model_f_input/20260907_r1"
    assert d9.mfi.MODEL_F_FORMAL_ROOT == d9.MODEL_F_INPUT_ROOT
    assert d9.SOLVER_ROOT == (
        "workspace/d9_de_decoder_calibration_"
        "10076f83-d752-4bac-9161-d8b0907d951b")
    assert d9.D8_REPRODUCTION_SEEDS == (2026091601, 2026091602, 2026091603)
    assert d9.FRESH_SEEDS == (2026091801, 2026091802, 2026091803,
                              2026091804, 2026091805)
    assert d9.DE_SEEDS == (2026091601, 2026091602, 2026091603, 2026091801,
                           2026091802, 2026091803, 2026091804, 2026091805)
    assert d9.POPULATIONS_PRIMARY == (4000, 16000)
    assert d9.CONDITION_POPULATIONS == {"f1.2": (4000, 16000),
                                        "f1.0": (4000,)}
    assert d9.MAX_ITER == 60 and d9.ENTROPY_TOL_BITS == 1e-4
    assert d9.STREAK == 20
    assert d9.MAX_DE_CALLS == 96 and d9.MAX_SETUP_CALLS == 12
    assert d9.WALL_BUDGET_S == 1200.0 and d9.PER_CALL_BUDGET_S == 300.0
    assert d9.RSS_BUDGET_BYTES == 2 * 1024 ** 3
    assert d9.ADVANCE_MARGIN == 0.95 and d9.F1_0_CROSSING_MIN == 7
    assert d9.GRAPH_WIDTHS == (64, 128, 256)
    assert d9.CONDITION_ROLE == {"f1.2": "primary_gate",
                                 "f1.0": "boundary_diagnostic"}
    ids = [c["candidate_id"] for c in d9.enumerate_candidates()]
    assert ids == ["lam_d2_0.00_d3_1.00", "lam_d2_0.45_d3_0.55",
                   "lam_d2_0.50_d3_0.50", "lam_d2_0.55_d3_0.45"]
    roles = {c["candidate_id"]: c["role"] for c in d9.enumerate_candidates()}
    assert roles["lam_d2_0.55_d3_0.45"] == "upper_flank_control"
    assert d9.planned_de_calls() == 96
    assert set(d9.TERMINALS) == {
        "D9_DE_CALIBRATION_SELECT_ONE", "D9_DE_STABILITY_NOT_CONFIRMED",
        "D9_DE_BASELINE_CONVERGED_REVIEW", "D9_SEMANTICS_BLOCKED",
        "D9_GRAPH_REALIZATION_INVALID", "D9_DE_EVIDENCE_INVALID",
        "D9_DE_RESOURCE_BLOCKED", "D9_DE_NOT_RUN"}
    assert tuple(runner.EVIDENCE_FILES) == (
        "manifest.json", "de_records.csv", "de_traces.csv",
        "candidate_summary.csv", "summary.json", "command_log.txt")
    assert runner.FROZEN_COMMAND == (
        ".venv/bin/python scripts/"
        "v72p2d9_de_decoder_calibration_development.py --calibrate "
        "--model-f-root workspace/v72p2d5_model_f_input/20260907_r1 "
        "--out-root workspace/d9_de_decoder_calibration_"
        "10076f83-d752-4bac-9161-d8b0907d951b")


# --------------------------------------------------------------------------- #
# Channel centering / coefficient direction / primitive updates
# --------------------------------------------------------------------------- #
def test_channel_centering_equivalence():
    report = d9.certify_channel_centering()
    assert report["claim"] == d9.CLAIM_EQUIVALENCE_CERTIFIED
    assert report["passed"] is True and report["max_abs_diff"] <= d9.CERT_ATOL

    rng = np.random.default_rng(5)
    row = rng.random(d9.Q) * 1.5 + 0.05
    row = row / row.sum()
    u = 13
    centered = d9.de_center_row(row, u)
    assert centered[0] == row[u]
    assert np.array_equal(centered, row[np.arange(d9.Q) ^ u])
    assert abs(centered.sum() - 1.0) < 1e-12
    consumed = d9.v26._channel_rows_from_centered(centered[None, :])[0]
    assert np.allclose(consumed, centered, rtol=0.0, atol=1e-15)
    with pytest.raises(ValueError):
        d9.de_center_row(row, 32)


def test_coefficient_direction_equivalence():
    report = d9.certify_coefficient_direction()
    assert report["claim"] == d9.CLAIM_EQUIVALENCE_CERTIFIED
    assert report["passed"] is True and report["max_abs_diff"] == 0.0

    perm, nonzero = d9.v26.build_gf_perm_table(d9.Q)
    mul, add, inv = d9._field_tables()
    for h in nonzero:
        for y in range(d9.Q):
            assert perm[int(h), y] == mul[int(inv[int(h)]), y]
    probe = np.random.default_rng(9).random(d9.Q)
    h = 17
    tmp = probe[perm[h]]
    scaled = np.empty(d9.Q)
    scaled[mul[h, :]] = probe
    assert np.array_equal(tmp, scaled)
    shifted = add[0, mul[5, :]]
    assert len(set(shifted.tolist())) == d9.Q


def test_variable_check_belief_primitive_updates():
    report = d9.certify_primitives()
    assert report["semantics_pass"] is True
    assert report["ensemble_path_equivalence"] is False
    for name in ("channel_centering", "coefficient_direction",
                 "check_update_v26_vs_v35", "check_update_v35_vs_direct_sp",
                 "variable_update_v26_vs_logsum",
                 "belief_update_v26_vs_logsum"):
        check = report["checks"][name]
        assert check["claim"] == d9.CLAIM_EQUIVALENCE_CERTIFIED
        assert check["passed"] is True
        assert check["max_abs_diff"] <= d9.CERT_ATOL


def test_tree_equality_and_loopy_claim_ceiling():
    report = d9.certify_primitives()
    tree_checks = ("tree_v26_check_vs_direct_sp", "tree_v26_belief_vs_exact",
                   "tree_v35_flooding_vs_exact",
                   "tree_v26_belief_vs_v35_flooding")
    for name in tree_checks:
        check = report["checks"][name]
        assert check["claim"] == d9.CLAIM_EQUIVALENCE_CERTIFIED
        assert check["passed"] is True
        assert check["max_abs_diff"] <= d9.CERT_ATOL
        assert name in report["equivalence_claims"]
    for name in ("loopy_flooding_vs_exact", "loopy_flooding_vs_row_layered"):
        check = report["checks"][name]
        assert check["claim"] == d9.CLAIM_NON_EQUIVALENCE_DIAGNOSTIC
        assert check["passed"] is None
        assert name not in report["equivalence_claims"]
        assert name in report["non_equivalence_diagnostics"]
    metric = report["checks"]["de_metric_vs_decoder_terminal"]
    assert metric["claim"] == d9.CLAIM_MISMATCH_DIAGNOSTIC
    assert "no certified bridge" in metric["detail"]


# --------------------------------------------------------------------------- #
# Graph realization: integrality, design table, deterministic planning
# --------------------------------------------------------------------------- #
def _cell(audit, candidate_id, condition, width):
    for cell in audit["cells"]:
        if (cell["candidate_id"] == candidate_id
                and cell["condition"] == condition and cell["width"] == width):
            return cell
    raise AssertionError("cell not found")


def test_degree_integrality_and_design_table():
    audit = d9.audit_graph_realization()
    assert audit["valid"] is True and audit["violation_count"] == 0
    assert audit["cell_count"] == 4 * 2 * 3
    for cell in audit["cells"]:
        assert cell["realizable"] is True
        assert cell["n2"] + cell["n3"] == cell["width"]
        assert cell["E"] == 2 * cell["n2"] + 3 * cell["n3"]
        assert abs(cell["rate_realized"]
                   - (1.0 - cell["m"] / cell["width"])) <= 1e-12
        assert min(cell["check_degree_allocation"]) >= 2
        assert cell["realized_max_check_degree"] <= 4
        assert cell["N2_minus_m_minus_1"] == 0
        assert cell["rate_error"] <= 1e-12

    cell = _cell(audit, "lam_d2_0.45_d3_0.55", "f1.2", 64)
    assert (cell["n2"], cell["n3"], cell["E"]) == (35, 29, 157)
    assert cell["check_degree_allocation"] == {2: 20, 3: 39}
    assert abs(cell["lambda2_realized"] - 70 / 157) <= 1e-15
    assert cell["exact_nominal"] == {"n2_exact": "1728/49",
                                     "E_exact": "7680/49",
                                     "n2_integral": False,
                                     "E_integral": False}
    assert cell["de_rho"] == {2: pytest.approx(0.25859, abs=1e-5),
                              3: pytest.approx(0.74141, abs=1e-5)}

    dv3 = _cell(audit, "lam_d2_0.00_d3_1.00", "f1.2", 64)
    assert (dv3["n2"], dv3["n3"], dv3["E"]) == (0, 64, 192)
    assert dv3["check_degree_allocation"] == {3: 44, 4: 15}
    assert dv3["exact_nominal"]["E_exact"] == "192"

    cell = _cell(audit, "lam_d2_0.45_d3_0.55", "f1.0", 64)
    assert cell["check_degree_allocation"] == {3: 39, 4: 10}

    cell = _cell(audit, "lam_d2_0.55_d3_0.45", "f1.0", 256)
    assert (cell["n2"], cell["n3"], cell["E"]) == (166, 90, 602)
    assert cell["check_degree_allocation"] == {3: 182, 4: 14}

    cell = _cell(audit, "lam_d2_0.45_d3_0.55", "f1.2", 256)
    assert cell["lambda2_realized"] == pytest.approx(94 / 209, abs=1e-15)
    assert cell["exact_nominal"]["E_exact"] == "30720/49"

    assert d9.exact_nominal_sockets(0.50, 128)["E_exact"] == "1536/5"
    assert d9.exact_nominal_sockets(0.55, 64)["E_exact"] == "2560/17"


def test_deterministic_planning_all_candidates_and_widths():
    plan_a = d9.build_plan()
    plan_b = d9.build_plan()
    assert plan_a == plan_b
    assert len(plan_a) == 96
    assert all(entry["refused"] is False for entry in plan_a)
    keys = [(entry["candidate_id"], entry["condition"],
             entry["population"], entry["seed"]) for entry in plan_a]
    assert len(set(keys)) == 96
    assert keys[0] == ("lam_d2_0.00_d3_1.00", "f1.2", 4000, 2026091601)
    assert keys[-1] == ("lam_d2_0.55_d3_0.45", "f1.0", 4000, 2026091805)
    index = d9.expected_call_index(plan_a)
    assert list(index.values()) == list(range(96))
    assert index[keys[0]] == 0 and index[keys[-1]] == 95
    assert d9.planned_de_calls(plan_a) == d9.MAX_DE_CALLS == 96
    counts = {}
    for entry in plan_a:
        key = (entry["candidate_id"], entry["condition"])
        counts[key] = counts.get(key, 0) + 1
    assert counts[("lam_d2_0.50_d3_0.50", "f1.2")] == 16
    assert counts[("lam_d2_0.50_d3_0.50", "f1.0")] == 8

    audit_a = d9.audit_graph_realization()
    audit_b = d9.audit_graph_realization()
    assert json.dumps(audit_a, sort_keys=True) == json.dumps(audit_b,
                                                            sort_keys=True)
    combos = {(cell["candidate_id"], cell["condition"], cell["width"])
              for cell in audit_a["cells"]}
    assert len(combos) == 24
    for cand in d9.CANDIDATES:
        for condition in d9.CONDITIONS:
            for width in d9.GRAPH_WIDTHS:
                assert (cand["candidate_id"], condition, width) in combos


@pytest.mark.parametrize("bad", [
    {1: 0.5, 3: 0.5},
    {2: -0.5, 3: 1.5},
    {2: 0.4, 3: 0.4},
    {4: 0.5, 3: 0.5},
])
def test_invalid_lambda_refused(bad):
    with pytest.raises(ValueError):
        d9.validate_lambda_edge(bad)
    assert d9.validate_lambda_edge({3: 1.0}) == {3: 1.0}


def test_unrealizable_socket_and_forest_refusal():
    with pytest.raises(d9.GraphRealizationError) as err:
        d9.graph_realization_cell({2: 1.0}, 64, 100)
    assert "socket allocation infeasible" in str(err.value)
    with pytest.raises(d9.GraphRealizationError) as err:
        d9.graph_realization_cell({2: 1.0}, 64, 59)
    assert "forced degree-2 cycle component" in str(err.value)
    with pytest.raises(ValueError):
        d9.graph_realization_cell({1: 1.0}, 64, 59)


# --------------------------------------------------------------------------- #
# Fresh root / no overwrite
# --------------------------------------------------------------------------- #
def test_fresh_root_and_protected_root_refusal(tmp_path):
    existing = tmp_path / "exists"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        runner.refuse_out_root(existing)
    for bad in (d9.MODEL_F_INPUT_ROOT,
                "workspace/v72p2d5_g2/20260906_r1",
                "workspace/d6_graph_mother_r1c_"
                "dd8c4defe67742a8b2bc1b634c116d6b",
                "workspace/d7_r1_multigraph_20260913_r1",
                "workspace/d8_rate_aligned_ensemble_"
                "5edf0630-f357-4a7e-b4c5-9ba955021405",
                "comparison_bench/outputs_comparison/d9_probe",
                "results/d9_probe"):
        with pytest.raises(ValueError):
            runner.refuse_out_root(bad)
    fresh = tmp_path / "fresh"
    assert runner.refuse_out_root(fresh) == fresh.resolve()
    assert not fresh.exists()
    rc = runner.main(["--calibrate", "--model-f-root", str(tmp_path / "nope"),
                      "--out-root", str(existing)])
    assert rc == 2
    with pytest.raises(SystemExit) as exc:
        runner.main(["--out-root", str(fresh)])  # flag required
    assert exc.value.code == 2


# --------------------------------------------------------------------------- #
# No production decoder entry / fake-runner isolation
# --------------------------------------------------------------------------- #
def test_no_production_decoder_entry(tmp_path, monkeypatch):
    for source in (MODULE_PATH.read_text(encoding="utf-8"),
                   RUNNER_PATH.read_text(encoding="utf-8")):
        assert "decode_row_layered_fftqspa" not in source
        assert "decode_flooding_fftqspa" not in source
    out = tmp_path / "cal_root"
    summary = _fake_calibration(out, monkeypatch)
    assert summary["terminal"] == d9.T_SELECT
    assert summary["de_calls"] == 96 and summary["setup_calls"] == 4
    assert sorted(path.name for path in out.iterdir()) == sorted(
        runner.EVIDENCE_FILES)


def test_fake_runner_full_sweep_routing_and_verify(tmp_path, monkeypatch):
    out = tmp_path / "cal_root"
    summary = _fake_calibration(out, monkeypatch)
    assert summary["terminal"] == d9.T_SELECT
    assert summary["winner_candidate_id"] == "lam_d2_0.50_d3_0.50"
    assert summary["eligible_candidate_ids"] == ["lam_d2_0.45_d3_0.55",
                                                 "lam_d2_0.50_d3_0.50"]
    assert summary["boundary_crossing_ids"] == ["lam_d2_0.45_d3_0.55",
                                                "lam_d2_0.50_d3_0.50",
                                                "lam_d2_0.55_d3_0.45"]
    assert summary["baseline_stability"] == d9.STABLE_UNCONVERGED
    assert summary["semantics_pass"] is True and summary["graph_valid"] is True
    assert summary["de_calls"] == 96 and summary["setup_calls"] == 4
    assert summary["planned_de_calls"] == 96
    rows = {row["candidate_id"]: row
            for row in runner._read_csv(out / "candidate_summary.csv")}
    assert rows["lam_d2_0.55_d3_0.45"]["stability"] == d9.STABILITY_AMBIGUOUS
    assert rows["lam_d2_0.00_d3_1.00"]["stability"] == d9.STABLE_UNCONVERGED
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["command"] == runner.FROZEN_COMMAND
    assert manifest["budgets"]["max_de_calls"] == 96
    assert runner.verify_command(str(out)) is True
    assert runner.main(["--verify", "--out-root", str(out)]) == 0
    assert runner.main(["--verify", "--out-root",
                        str(tmp_path / "missing")]) == 1


def test_verify_detects_tampered_trace(tmp_path, monkeypatch):
    out = tmp_path / "cal_root"
    _fake_calibration(out, monkeypatch)
    assert runner.verify_command(str(out)) is True
    rows = runner._read_csv(out / "de_traces.csv")
    trace = json.loads(rows[0]["entropy_trace_bits"])
    trace[10] = trace[10] + 1.0
    rows[0]["entropy_trace_bits"] = json.dumps(trace)
    runner._write_csv(out / "de_traces.csv", runner.DE_TRACE_COLUMNS, rows)
    assert runner.verify_command(str(out)) is False


def test_failure_retention_no_retry(tmp_path, monkeypatch):
    attempts = []

    def flaky(lambda_edge, rho_edge, sampler, seed, n_samples):
        attempts.append((int(seed), int(n_samples)))
        if len(attempts) >= 5:
            raise RuntimeError("injected DE failure")
        return _fake_de_call(lambda_edge, rho_edge, sampler, seed, n_samples)

    monkeypatch.setattr(d9.v26, "run_mcde_posterior", _boom)
    channel = _tiny_channel()
    out = tmp_path / "cal_root"
    summary = runner.run_calibration("workspace/nonexistent_model_f", str(out),
                                     channel=channel, de_call=flaky)
    assert summary["terminal"] == d9.T_INVALID
    assert summary["de_calls"] == 4
    assert len(attempts) == 5  # one attempt per planned call, no retry
    assert sorted(path.name for path in out.iterdir()) == sorted(
        runner.EVIDENCE_FILES)
    log = (out / "command_log.txt").read_text(encoding="utf-8")
    assert "DE call failed" in log
    assert runner.verify_command(str(out)) is True


# --------------------------------------------------------------------------- #
# Routing arithmetic / stability labels / selection rank
# --------------------------------------------------------------------------- #
def _conv(*flags):
    return list(flags)


def test_routing_units_stability_and_selection():
    cands = [c["candidate_id"] for c in d9.enumerate_candidates()]
    base, c45, c50, c55 = cands
    all_conv = _conv(*([True] * 8))
    all_unconv = _conv(*([False] * 8))
    amb = _conv(True, True, True, True, True, True, True, False)

    records = _synthetic_records(
        {base: all_conv, c45: all_conv, c50: all_conv, c55: all_conv},
        {base: 90.0, c45: 70.0, c50: 60.0, c55: 80.0})
    adv = d9.compute_routing(True, True, records)
    assert adv["terminal"] == d9.T_BASELINE_CONVERGED
    assert adv["baseline_stability"] == d9.STABLE_CONVERGED

    records = _synthetic_records(
        {base: all_unconv, c45: all_unconv, c50: all_unconv, c55: all_unconv},
        {base: 90.0, c45: 70.0, c50: 60.0, c55: 80.0})
    adv = d9.compute_routing(True, True, records)
    assert adv["terminal"] == d9.T_STABILITY
    assert adv["eligible_candidate_ids"] == []

    records = _synthetic_records(
        {base: all_unconv, c45: all_conv, c50: all_conv, c55: amb},
        {base: 100.0, c45: 96.0, c50: 97.0, c55: 80.0})
    adv = d9.compute_routing(True, True, records)
    assert adv["terminal"] == d9.T_STABILITY  # 0.96/0.97 above the 0.95 margin
    assert adv["eligible_candidate_ids"] == []

    records = _synthetic_records(
        {base: all_unconv, c45: all_conv, c50: all_conv, c55: amb},
        {base: 100.0, c45: 90.0, c50: 89.0, c55: 80.0})
    adv = d9.compute_routing(True, True, records)
    assert adv["terminal"] == d9.T_SELECT
    assert adv["winner_candidate_id"] == c50
    assert adv["eligible_candidate_ids"] == [c45, c50]
    assert adv["baseline_stability"] == d9.STABLE_UNCONVERGED

    records = _synthetic_records(
        {base: all_unconv, c45: all_conv, c50: all_conv, c55: amb},
        {base: 100.0, c45: 90.0, c50: 90.0, c55: 80.0})
    adv = d9.compute_routing(True, True, records)
    assert adv["winner_candidate_id"] == c45  # lexicographic tie-break

    records = _synthetic_records(
        {base: amb, c45: all_conv, c50: all_conv, c55: amb},
        {base: 100.0, c45: 90.0, c50: 89.0, c55: 80.0})
    adv = d9.compute_routing(True, True, records)
    assert adv["terminal"] == d9.T_STABILITY  # DV3 ambiguity has no basis
    assert adv["baseline_stability"] == d9.STABILITY_AMBIGUOUS

    records = _synthetic_records(
        {base: all_unconv, c45: all_conv, c50: all_conv, c55: amb},
        {base: 100.0, c45: 90.0, c50: 89.0, c55: 80.0})
    assert d9.compute_routing(False, True, records)["terminal"] == d9.T_SEMANTICS
    assert d9.compute_routing(True, False, records)["terminal"] == d9.T_GRAPH


# --------------------------------------------------------------------------- #
# Blocked paths write six files and stay verifiable
# --------------------------------------------------------------------------- #
def test_semantics_blocked_path(tmp_path, monkeypatch):
    real_cert = d9.certify_primitives

    def failing_cert():
        report = real_cert()
        name = report["equivalence_claims"][0]
        report["checks"][name] = dict(report["checks"][name], passed=False,
                                      max_abs_diff=1.0)
        report["semantics_pass"] = False
        return report

    monkeypatch.setattr(d9.v26, "run_mcde_posterior", _boom)
    channel = _tiny_channel()
    out = tmp_path / "cal_root"
    summary = runner.run_calibration("workspace/nonexistent_model_f", str(out),
                                     channel=channel, de_call=_fake_de_call,
                                     certify=failing_cert)
    assert summary["terminal"] == d9.T_SEMANTICS
    assert summary["de_calls"] == 0
    assert summary["winner_candidate_id"] is None
    assert sorted(path.name for path in out.iterdir()) == sorted(
        runner.EVIDENCE_FILES)
    assert runner.verify_command(str(out)) is True


def test_graph_invalid_path(tmp_path, monkeypatch):
    def flaky_cell(*_args, **_kwargs):
        raise d9.GraphRealizationError("test-injected unrealizable cell")

    monkeypatch.setattr(d9, "graph_realization_cell", flaky_cell)
    monkeypatch.setattr(d9.v26, "run_mcde_posterior", _boom)
    channel = _tiny_channel()
    out = tmp_path / "cal_root"
    summary = runner.run_calibration("workspace/nonexistent_model_f", str(out),
                                     channel=channel, de_call=_fake_de_call)
    assert summary["terminal"] == d9.T_GRAPH
    assert summary["de_calls"] == 0
    assert summary["graph_valid"] is False
    assert sorted(path.name for path in out.iterdir()) == sorted(
        runner.EVIDENCE_FILES)
    assert runner.verify_command(str(out)) is True

