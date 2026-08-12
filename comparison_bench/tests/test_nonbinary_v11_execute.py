"""T0/T1 deterministic tests for the V11 Stage X scientific executor
(``formal-nonbinary-ldpc-v11-sc-de-gate``, design.md §5 Stage X / §6 gate,
V11-40.2).

Scope: executor structure only.  Every test is small-scale synthetic — no
GF(1024) scientific matrix is executed (q is never 1024 for any kernel run,
and the binary-search tests use deterministic fake probe runners).

Covers:
- threshold-search wrapper correctness (known monotone scenarios locate the
  threshold within SEARCH_P_TOL; statuses valid / not_converged / invalid)
- paired-arm logic (coupled/control pair by seed index n, distinct derived
  integers, control = single-position w=0/W=1 run)
- conservative aggregation (min of 5 seeds; below_range unless all valid +
  converged)
- gate decision (the four states + smallest-W-then-smallest-w selection)
- seed-derivation determinism (same tag twice; 60 distinct; agreement with
  formal_matrix_run_specs)
- module self-check / dry-run evidence writer (structure-only)
"""
from __future__ import annotations

import json
import os

import pytest

from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v11_execute import (
    GATE_S1,
    GATE_S3,
    PAIRED_GAIN_MIN,
    PROBE_RANGES,
    aggregate_conservative,
    gate_decision,
    paired_gain,
    seed_integers,
    threshold_search_run,
)
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v11_mcde import (
    FROZEN_GEOMETRIES,
    V10_WINNER_S1,
    V10_WINNER_S1_RATE,
    rate_contract,
    run_coupled_mcde,
    v11_seed,
)
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v11_microbench import (
    FORMAL_N_SEEDS,
    FORMAL_STRATA,
    SEARCH_P_TOL,
    probe_count,
)
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v11_parallel import (
    RunSpec,
    formal_matrix_run_specs,
)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _fake_search(threshold: float | None, *, stratum: str, geometry_id: str,
                 arm: str, status: str = "valid") -> dict:
    """A minimal per-seed search dict (same shape the executor consumes)."""
    return {
        "stratum": stratum,
        "geometry_id": geometry_id,
        "arm": arm,
        "status": status,
        "threshold_estimate": threshold,
    }


def _monotone_runner(threshold: float):
    """A deterministic fake probe runner with a KNOWN monotone threshold:
    converges iff ``p <= threshold`` (lower channel error converges more
    easily — the frozen DE's monotone-decreasing regime)."""
    def runner(spec: RunSpec, p: float) -> dict:
        converged = float(p) <= float(threshold)
        return {
            "converged": converged,
            "iterations": 3 if converged else 150,
            "entropy": 0.005 if converged else 0.5,
            "error_prob": 0.0 if converged else 0.3,
        }
    return runner


def _tiny_spec(stratum: str = "S1") -> RunSpec:
    """A tiny non-scientific RunSpec (q=8) for kernel-wiring smoke tests."""
    L, w, W = 4, 1, 4
    contract = rate_contract(L, w, V10_WINNER_S1_RATE, V10_WINNER_S1)
    rho = {int(k): float(v) for k, v in contract["rho"].items()}
    return RunSpec(
        run_id="tiny_execute_smoke",
        stratum=stratum, geometry_id="G1",
        seed=v11_seed(f"tiny:execute:test:{stratum}"),
        arm="coupled", w=w, W=W, n_samples=100, max_iter=2,
        lambda_edge={int(k): float(v) for k, v in V10_WINNER_S1.items()},
        rho_edge=rho, p=0.15, L=L, q=8)


def _passing_gate_inputs() -> tuple[dict, dict, dict]:
    """All-pass conservative/gains/seeds_ok data over the frozen cells."""
    conservative, gains, seeds_ok = {}, {}, {}
    for s, gate in (("S1", GATE_S1), ("S3", GATE_S3)):
        conservative[s], gains[s], seeds_ok[s] = {}, {}, {}
        for g in FROZEN_GEOMETRIES:
            conservative[s][g] = {"coupled": gate + 0.02, "control": gate - 0.005}
            gains[s][g] = 0.025
            seeds_ok[s][g] = True
    return conservative, gains, seeds_ok


_OK_CHECKS = dict(rate_ok=True, resource_ok=True, replay_ok=True,
                  structured_ok=True, semantic_ok=True)


# --------------------------------------------------------------------------- #
# T0: threshold-search wrapper (binary search) with known monotone scenarios
# --------------------------------------------------------------------------- #


def test_threshold_search_located_within_tolerance():
    """A known monotone threshold inside the S1 range must be located within
    SEARCH_P_TOL; the interval must shrink to width <= tol; the estimate must
    be the largest probed converged p."""
    true_threshold = 0.2113
    spec = _tiny_spec()
    search = threshold_search_run(
        spec, runner=_monotone_runner(true_threshold),
        probe_range=PROBE_RANGES["S1"], search_tol=SEARCH_P_TOL)
    assert search["status"] == "valid"
    assert search["probe_count_total"] == probe_count(0.18, 0.26, SEARCH_P_TOL) == 7
    assert len(search["probes"]) == 7
    assert abs(search["threshold_estimate"] - true_threshold) <= SEARCH_P_TOL
    # interval bracketing the estimate has width <= tol
    conv = [p["p"] for p in search["probes"] if p["converged"]]
    nonconv = [p["p"] for p in search["probes"] if not p["converged"]]
    bracket_hi = min(nonconv) if nonconv else max(conv)
    assert bracket_hi - search["threshold_estimate"] <= SEARCH_P_TOL + 1e-12
    # monotone: all probed p <= estimate converge, all above do not
    for probe in search["probes"]:
        if probe["p"] <= search["threshold_estimate"] + 1e-12:
            assert probe["converged"] is True
        else:
            assert probe["converged"] is False
    # estimate is the largest probed converged p
    converged_p = [p["p"] for p in search["probes"] if p["converged"]]
    assert search["threshold_estimate"] == max(converged_p)


def test_threshold_search_gate_aligned_estimate():
    """Threshold exactly at the S1 absolute gate .22 is found at the first
    probe (midpoint of [0.18, 0.26]); estimate == .22 exactly."""
    spec = _tiny_spec()
    search = threshold_search_run(
        spec, runner=_monotone_runner(GATE_S1),
        probe_range=PROBE_RANGES["S1"], search_tol=SEARCH_P_TOL)
    assert search["status"] == "valid"
    assert search["threshold_estimate"] == GATE_S1
    assert search["probes"][0]["p"] == GATE_S1
    assert search["probes"][0]["converged"] is True


def test_threshold_search_not_converged():
    """No probe converges -> status not_converged, threshold_below_range,
    threshold_estimate None, full probe table retained."""
    def never(spec: RunSpec, p: float) -> dict:
        return {"converged": False, "iterations": 150,
                "entropy": 0.5, "error_prob": 0.3}
    spec = _tiny_spec()
    search = threshold_search_run(
        spec, runner=never, probe_range=PROBE_RANGES["S1"],
        search_tol=SEARCH_P_TOL)
    assert search["status"] == "not_converged"
    assert search["threshold_below_range"] is True
    assert search["threshold_estimate"] is None
    assert len(search["probes"]) == 7


def test_threshold_search_invalid_retains_probes_before_failure():
    """A fail-closed ValueError from the runner marks the run invalid, records
    the error, and retains the probes executed before the failure."""
    calls = {"n": 0}

    def flaky(spec: RunSpec, p: float) -> dict:
        calls["n"] += 1
        if calls["n"] == 3:
            raise ValueError("fail-closed validation boom")
        return {"converged": True, "iterations": 3,
                "entropy": 0.005, "error_prob": 0.0}

    spec = _tiny_spec()
    search = threshold_search_run(
        spec, runner=flaky, probe_range=PROBE_RANGES["S1"],
        search_tol=SEARCH_P_TOL)
    assert search["status"] == "invalid"
    # estimate from probes before the failure is retained as evidence only;
    # an invalid run counts as neither converged nor non-converged
    assert search["threshold_estimate"] == 0.24
    assert search["invalid_error"]["type"] == "ValueError"
    assert len(search["probes"]) == 3
    assert search["probes"][0]["valid"] is True
    assert search["probes"][0]["converged"] is True
    assert search["probes"][2]["valid"] is False
    assert search["probes"][2]["error"]["message"] == "fail-closed validation boom"


def test_threshold_search_spec_and_range_validation():
    with pytest.raises(ValueError):
        threshold_search_run(object())  # not a RunSpec
    spec = _tiny_spec()
    with pytest.raises(ValueError):
        threshold_search_run(spec, probe_range=(0.2, 0.1))  # lo >= hi
    with pytest.raises(ValueError):
        threshold_search_run(spec, search_tol=-1.0)  # bad tol
    with pytest.raises(ValueError):
        threshold_search_run(_tiny_spec(stratum="NO_SUCH_STRATUM"))  # no frozen range


def test_threshold_search_real_kernel_tiny_q8_smoke():
    """The default probe runner wires the frozen run_coupled_mcde kernel: a
    tiny q=8 run (never the GF(1024) matrix) produces complete probe dicts
    with finite entropy/error values and a bool converged flag."""
    spec = _tiny_spec()
    search = threshold_search_run(spec, search_tol=SEARCH_P_TOL)
    assert search["status"] in ("valid", "not_converged")
    assert len(search["probes"]) == 7
    for probe in search["probes"]:
        assert probe["valid"] is True
        assert isinstance(probe["converged"], bool)
        assert probe["iterations"] >= 1
        assert probe["entropy"] is not None
        assert probe["error_prob"] is not None
        assert 0.0 <= probe["entropy"] <= 1.0


# --------------------------------------------------------------------------- #
# T0: paired-arm logic (design.md §4 control contract)
# --------------------------------------------------------------------------- #


def test_paired_arms_share_seed_index():
    """Every (stratum, geometry, seed_n) has exactly one coupled and one
    control spec; the arms pair by seed index n (distinct derived integer
    seeds per arm tag, per the frozen tag pattern); the control is the
    single-position run (w=0, W=1)."""
    entries = seed_integers()
    specs_by_id = {s.run_id: s for s in formal_matrix_run_specs()}
    by_key: dict[tuple, dict] = {}
    for e in entries:
        by_key.setdefault((e["stratum"], e["geometry_id"], e["seed_n"]), {})[
            e["arm"]] = e
    assert len(by_key) == len(FORMAL_STRATA) * len(FROZEN_GEOMETRIES) * FORMAL_N_SEEDS == 30
    for key, arms in by_key.items():
        assert set(arms) == {"coupled", "control"}
        coupled, control = arms["coupled"], arms["control"]
        assert coupled["seed"] != control["seed"], \
            "arms derive distinct integers (pair by seed index, not value)"
        c_spec = specs_by_id[coupled["run_id"]]
        o_spec = specs_by_id[control["run_id"]]
        assert o_spec.w == 0 and o_spec.W == 1, "control = single-position run"
        assert c_spec.w == FROZEN_GEOMETRIES[c_spec.geometry_id]["w"]
        assert c_spec.W == FROZEN_GEOMETRIES[c_spec.geometry_id]["W"]
        assert coupled["run_id"] != control["run_id"]
        assert coupled["tag"].endswith(f":{key[2]}")
        assert control["tag"].endswith(f":{key[2]}")


def test_paired_gain_arithmetic():
    assert paired_gain(0.25, 0.22) == 0.03
    assert paired_gain(None, 0.22) is None
    assert paired_gain(0.25, None) is None


# --------------------------------------------------------------------------- #
# T1: conservative aggregation (design.md §6, 5-seed min)
# --------------------------------------------------------------------------- #


def test_aggregate_conservative_min_semantics():
    fake = [_fake_search(t, stratum="S1", geometry_id="G1", arm="coupled")
            for t in [0.21, 0.20, 0.22, 0.19, 0.21]]
    agg = aggregate_conservative(fake, stratum="S1", geometry_id="G1", arm="coupled")
    assert agg["conservative_threshold"] == 0.19, "conservative = min of 5 seeds"
    assert agg["seeds_valid"] is True
    assert agg["seeds_converged"] is True
    assert agg["below_range"] is False
    assert agg["seed_thresholds"] == [0.21, 0.20, 0.22, 0.19, 0.21]


def test_aggregate_conservative_not_converged_seed_below_range():
    fake = [_fake_search(t, stratum="S1", geometry_id="G1", arm="coupled")
            for t in [0.21, 0.20, None, 0.19, 0.21]]
    agg = aggregate_conservative(fake, stratum="S1", geometry_id="G1", arm="coupled")
    assert agg["conservative_threshold"] is None
    assert agg["seeds_converged"] is False
    assert agg["below_range"] is True, "a non-converged seed marks the cell below range"


def test_aggregate_conservative_invalid_seed():
    fake = [_fake_search(t, stratum="S1", geometry_id="G1", arm="coupled")
            for t in [0.21, 0.20, 0.22, 0.19, 0.21]]
    fake[2] = _fake_search(None, stratum="S1", geometry_id="G1", arm="coupled",
                           status="invalid")
    agg = aggregate_conservative(fake, stratum="S1", geometry_id="G1", arm="coupled")
    assert agg["seeds_valid"] is False
    assert agg["conservative_threshold"] is None


def test_aggregate_conservative_validation():
    fake = [_fake_search(0.2, stratum="S1", geometry_id="G1", arm="coupled")
            for _ in range(5)]
    with pytest.raises(ValueError):
        aggregate_conservative(fake[:4], stratum="S1", geometry_id="G1", arm="coupled")
    mismatched = list(fake)
    mismatched[0] = _fake_search(0.2, stratum="S3", geometry_id="G1", arm="coupled")
    with pytest.raises(ValueError):
        aggregate_conservative(mismatched, stratum="S1", geometry_id="G1", arm="coupled")


# --------------------------------------------------------------------------- #
# T1: gate decision (four states + selection rule)
# --------------------------------------------------------------------------- #


def test_gate_ready_selects_smallest_w_then_smallest_w():
    conservative, gains, seeds_ok = _passing_gate_inputs()
    decision = gate_decision(conservative=conservative, gains=gains,
                             seeds_ok=seeds_ok, **_OK_CHECKS)
    assert decision["state"] == "ready_for_finite_length"
    # selection key = (W, w) over FROZEN_GEOMETRIES; G1=(8,1) < G2=(16,2) < G3=(32,2)
    expected = min(FROZEN_GEOMETRIES,
                   key=lambda g: (int(FROZEN_GEOMETRIES[g]["W"]),
                                  int(FROZEN_GEOMETRIES[g]["w"])))
    assert decision["selected_geometry"] == expected == "G1"
    assert decision["note"]


def test_gate_selection_skips_failed_geometry():
    """G1 below the S1 absolute gate -> G2 (next smallest W) is selected."""
    conservative, gains, seeds_ok = _passing_gate_inputs()
    conservative["S1"]["G1"] = {"coupled": GATE_S1 - 0.01, "control": GATE_S1 - 0.02}
    decision = gate_decision(conservative=conservative, gains=gains,
                             seeds_ok=seeds_ok, **_OK_CHECKS)
    assert decision["state"] == "ready_for_finite_length"
    assert decision["selected_geometry"] == "G2"
    assert decision["per_geometry"]["G1"]["passes"] is False
    assert decision["per_geometry"]["G2"]["passes"] is True


def test_gate_failed_coupling_when_none_pass():
    conservative, gains, seeds_ok = _passing_gate_inputs()
    for s, gate in (("S1", GATE_S1), ("S3", GATE_S3)):
        for g in FROZEN_GEOMETRIES:
            conservative[s][g] = {"coupled": gate - 0.01, "control": gate - 0.02}
    decision = gate_decision(conservative=conservative, gains=gains,
                             seeds_ok=seeds_ok, **_OK_CHECKS)
    assert decision["state"] == "failed_coupling"
    assert decision["selected_geometry"] is None


def test_gate_resource_blocked():
    conservative, gains, seeds_ok = _passing_gate_inputs()
    decision = gate_decision(conservative=conservative, gains=gains,
                             seeds_ok=seeds_ok,
                             **dict(_OK_CHECKS, resource_ok=False))
    assert decision["state"] == "resource_blocked"
    assert decision["selected_geometry"] is None


def test_gate_failed_reference_any_check():
    for check in ("rate_ok", "replay_ok", "structured_ok", "semantic_ok"):
        conservative, gains, seeds_ok = _passing_gate_inputs()
        decision = gate_decision(conservative=conservative, gains=gains,
                                 seeds_ok=seeds_ok,
                                 **dict(_OK_CHECKS, **{check: False}))
        assert decision["state"] == "failed_reference", check
        assert check in decision["reason"]


def test_gate_seeds_not_all_valid_fails_geometry():
    conservative, gains, seeds_ok = _passing_gate_inputs()
    seeds_ok["S1"]["G1"] = False
    decision = gate_decision(conservative=conservative, gains=gains,
                             seeds_ok=seeds_ok, **_OK_CHECKS)
    assert decision["per_geometry"]["G1"]["passes"] is False
    assert "seeds" in decision["per_geometry"]["G1"]["failure_reason"]
    assert decision["selected_geometry"] == "G2"


def test_gate_paired_gain_below_min_fails_geometry():
    conservative, gains, seeds_ok = _passing_gate_inputs()
    gains["S1"]["G1"] = PAIRED_GAIN_MIN / 2.0
    decision = gate_decision(conservative=conservative, gains=gains,
                             seeds_ok=seeds_ok, **_OK_CHECKS)
    assert decision["per_geometry"]["G1"]["passes"] is False
    assert "paired gain" in decision["per_geometry"]["G1"]["failure_reason"]


def test_gate_missing_cell_raises():
    conservative, gains, seeds_ok = _passing_gate_inputs()
    del conservative["S1"]["G2"]
    with pytest.raises(ValueError):
        gate_decision(conservative=conservative, gains=gains,
                      seeds_ok=seeds_ok, **_OK_CHECKS)


# --------------------------------------------------------------------------- #
# T0: seed-derivation determinism (frozen v11_seed rule)
# --------------------------------------------------------------------------- #


def test_v11_seed_same_tag_twice():
    assert v11_seed("S1:G1:coupled:1") == v11_seed("S1:G1:coupled:1")
    assert v11_seed("S3:G3:control:5") == 660002917


def test_seed_integers_deterministic_and_distinct():
    first, second = seed_integers(), seed_integers()
    assert first == second, "seed derivation must be deterministic"
    assert len(first) == 60
    assert len({e["seed"] for e in first}) == 60, "60 distinct seed integers"
    assert len({e["run_id"] for e in first}) == 60, "60 unique run ids"
    required = {"run_id", "stratum", "geometry_id", "seed_n", "arm", "tag", "seed"}
    for entry in first:
        assert required <= set(entry), entry["run_id"]


def test_seed_integers_agree_with_run_specs():
    entries = seed_integers()
    specs = formal_matrix_run_specs()
    assert [e["seed"] for e in entries] == [int(s.seed) for s in specs]
    assert [e["run_id"] for e in entries] == [s.run_id for s in specs]
    assert [e["stratum"] for e in entries] == [s.stratum for s in specs]
    assert [e["arm"] for e in entries] == [s.arm for s in specs]
    # every seed matches its own tag under the frozen derivation rule
    for e in entries:
        assert v11_seed(e["tag"]) == e["seed"], e["run_id"]


def test_seed_integers_frozen_order():
    entries = seed_integers()
    strata = [e["stratum"] for e in entries]
    assert strata[:30] == ["S1"] * 30 and strata[30:] == ["S3"] * 30, \
        "stratum-major"
    g1 = [e for e in entries if e["stratum"] == "S1"]
    geom = [e["geometry_id"] for e in g1]
    assert geom[:10] == ["G1"] * 10 and geom[10:20] == ["G2"] * 10 \
        and geom[20:30] == ["G3"] * 10, "geometry-major"
    arms = [e["arm"] for e in g1[:2]]
    assert arms == ["coupled", "control"], "seed-major -> arm-major"


# --------------------------------------------------------------------------- #
# T0: module structure (self-check + dry-run evidence writer)
# --------------------------------------------------------------------------- #


def test_module_self_check_passes():
    """The module's own structural self-check must pass (no kernel run)."""
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v11_execute as ex
    ex._self_check()  # asserts internally; raises on failure


def test_dry_run_writes_structure_evidence(tmp_path):
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v11_execute as ex
    out_dir = str(tmp_path / "dryrun")
    summary = ex._dry_run(out_dir)
    assert summary["schema"] == "v11_execute_dry_run_v1"
    assert summary["scientific_executed"] is False
    assert summary["n_specs"] == 60 and summary["n_seeds"] == 60
    evidence_path = os.path.join(out_dir, "formal_matrix_dry_run.json")
    assert os.path.isfile(evidence_path)
    with open(evidence_path, encoding="utf-8") as handle:
        payload = json.load(handle)
    assert payload["schema"] == "v11_execute_dry_run_v1"
    assert payload["scientific_executed"] is False
    assert len(payload["seed_integers"]) == 60


# --------------------------------------------------------------------------- #
# T0/T1: execution bookkeeping (progress / heartbeat / resume / status)
# --------------------------------------------------------------------------- #


def test_progress_init_write_load_roundtrip(tmp_path):
    """The 60-entry progress table initializes all-pending, round-trips
    through write_progress/load_progress, and is persisted atomically."""
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v11_execute as ex
    root = str(tmp_path / "exec")
    progress = ex._init_progress(root)
    assert len(progress) == 60
    assert all(e["state"] == "pending" for e in progress.values())
    ex.write_progress(root, progress)
    assert ex.load_progress(root) == progress
    assert os.path.isfile(os.path.join(root, "progress.json"))
    assert not os.path.isfile(os.path.join(root, "progress.json.tmp")), \
        "temp file must be renamed away"


def test_progress_state_mapping():
    """valid -> done; invalid / not_converged pass through to terminal."""
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v11_execute as ex
    assert ex._progress_state_for("valid") == "done"
    assert ex._progress_state_for("invalid") == "invalid"
    assert ex._progress_state_for("not_converged") == "not_converged"


def test_completed_run_outcome_and_resume_scan(tmp_path):
    """The resume skip set covers complete parseable evidence of ANY terminal
    scientific status (done/invalid/not_converged — immutable evidence is
    never re-run); missing or torn evidence stays re-executable."""
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v11_execute as ex
    root = str(tmp_path / "exec")
    specs = formal_matrix_run_specs(out_root=root)
    ex._write_fake_run_evidence(root, specs[0])                       # valid
    ex._write_fake_run_evidence(root, specs[1], status="not_converged",
                                threshold=None)
    ex._write_fake_run_evidence(root, specs[2], status="invalid",
                                threshold=None)
    torn_dir = os.path.join(root, specs[3].run_id)                    # torn JSON
    os.makedirs(torn_dir, exist_ok=True)
    with open(os.path.join(torn_dir, "threshold_search.json"), "w",
              encoding="utf-8") as handle:
        handle.write("{not valid json")
    with open(os.path.join(torn_dir, "run_measurement.json"), "w",
              encoding="utf-8") as handle:
        handle.write("{")
    completed, outcomes = ex.scan_completed_runs(
        root, [spec.run_id for spec in specs])
    assert set(completed) == {specs[0].run_id, specs[1].run_id, specs[2].run_id}
    assert specs[3].run_id not in completed, "torn evidence is re-executable"
    assert specs[4].run_id not in completed, "missing evidence is re-executable"
    assert set(outcomes) == set(completed)
    assert ex.completed_run_outcome(root, specs[4].run_id) is None


def test_status_summary_distribution_and_heartbeat(tmp_path):
    """--status summary reports total/terminal counts, per-cell distribution,
    currently-running runs, and the heartbeat."""
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v11_execute as ex
    root = str(tmp_path / "exec")
    specs = formal_matrix_run_specs(out_root=root)
    progress = ex._init_progress(root)
    for spec in specs[:4]:  # 4 done runs, all in S1/G1
        ex._write_fake_run_evidence(root, spec)
        progress[spec.run_id].update(
            state=ex._progress_state_for("valid"), finished_at=ex._utc_timestamp(),
            results_file=os.path.join(spec.run_id, "threshold_search.json"),
            probes_executed=7)
    progress[specs[4].run_id].update(state="running",
                                     started_at=ex._utc_timestamp())
    ex.write_progress(root, progress)
    ex.write_heartbeat(root, runs_done=4, runs_running=1)
    status = ex.summarize_status(root)
    assert status["schema"] == "v11_execute_status_v1"
    assert status["n_total"] == 60
    assert status["n_terminal"] == 4
    assert status["by_state"]["done"] == 4
    assert status["by_state"]["running"] == 1
    assert specs[4].run_id in status["currently_running"]
    assert status["per_cell"]["S1/G1"] == {"total": 10, "done": 4}
    assert status["heartbeat"]["runs_done"] == 4
    assert status["heartbeat_age_seconds"] is not None
    assert status["stale_running"] == [], "fresh heartbeat -> not stale"


def test_status_summary_flags_stale_running(tmp_path):
    """Running entries with a missing/aged heartbeat are flagged stale."""
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v11_execute as ex
    root = str(tmp_path / "exec")
    specs = formal_matrix_run_specs(out_root=root)
    progress = ex._init_progress(root)
    progress[specs[0].run_id].update(state="running",
                                     started_at=ex._utc_timestamp())
    ex.write_progress(root, progress)
    status = ex.summarize_status(root)  # no heartbeat file at all
    assert specs[0].run_id in status["currently_running"]
    assert specs[0].run_id in status["stale_running"], \
        "missing heartbeat -> stale"
    assert status["heartbeat"] is None


def test_execute_formal_matrix_resume_skips_evidenced_runs(tmp_path):
    """Full resume simulation through execute_formal_matrix (fake runner, no
    kernel): pre-completed runs are loaded from evidence, never re-executed;
    the remaining runs execute; the merged summary is complete and the
    bookkeeping block records the skip set."""
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v11_execute as ex
    root = str(tmp_path / "exec")
    specs = formal_matrix_run_specs(out_root=root)
    for spec in specs[:2]:
        ex._write_fake_run_evidence(root, spec)
    called: list[str] = []

    def fake_runner(spec: RunSpec, p: float) -> dict:
        called.append(spec.run_id)
        return {"converged": True, "iterations": 3, "entropy": 0.005,
                "error_prob": 0.0}

    summary = ex.execute_formal_matrix(
        out_root=root, workers=2, serial=True, runner=fake_runner,
        resume=True, heartbeat_interval=0.05)
    assert summary["status"] == "completed"
    assert summary["n_runs_total"] == 60
    assert summary["n_runs_completed"] == 60
    assert len(summary["runs"]) == 60
    assert not summary["incomplete_runs"]
    assert specs[0].run_id not in called and specs[1].run_id not in called, \
        "evidenced runs must not be re-executed"
    assert len(set(called)) == 58, "58 distinct runs executed (7 probes each)"
    assert summary["bookkeeping"]["n_skipped_completed"] == 2
    assert sorted(summary["bookkeeping"]["skipped_run_ids"]) == sorted(
        [specs[0].run_id, specs[1].run_id])
    assert summary["bookkeeping"]["session_n_runs_executed"] == 58
    assert os.path.isfile(os.path.join(root, "progress.json"))
    assert os.path.isfile(os.path.join(root, "heartbeat.json"))
    progress = ex.load_progress(root)
    assert all(progress[run_id]["state"] in ("done", "invalid", "not_converged")
               for run_id in progress), "all 60 runs terminal after completion"
