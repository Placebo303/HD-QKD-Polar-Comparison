"""Fake-census and tiny-math tests for source-aware cycle overlaps."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_cycle_census as census
from comparison_bench.cli import nbldpc_gf32_cycle_source_overlap as probe


def _unit_arm(ell: int) -> dict:
    return {
        "numerator_coefficients": [1] * ell,
        "denominator_coefficients": [1] * ell,
        "product": 1,
        "unit": True,
        "witness_values": [1] * ell,
    }


def _nonunit_arm() -> dict:
    return {
        "numerator_coefficients": [2, 1],
        "denominator_coefficients": [1, 1],
        "product": 2,
        "unit": False,
        "witness_values": None,
    }


def _cycle_row(seed: int, rows: list[int], variables: list[int],
               control: dict, candidate: dict) -> dict:
    key = census.canonical_cycle_key(rows, variables)
    cycle = {"rows": rows, "variables": variables, "key": key}
    return census._csv_record(seed, cycle, control, candidate)


def _rows_for_seed(seed: int) -> list[dict]:
    # Two distinct simple-cycle records share the same normalized local word.
    return [
        _cycle_row(seed, [0, 1], [3, 4], _nonunit_arm(), _nonunit_arm()),
        _cycle_row(seed, [0, 1, 2], [0, 1, 2], _unit_arm(3), _unit_arm(3)),
        _cycle_row(seed, [0, 1, 2], [0, 2, 1], _unit_arm(3), _unit_arm(3)),
    ]


def _write_fake_census(repo: Path, *, empty: bool = False,
                       row_cap: bool = False) -> tuple[Path, list[dict]]:
    root = repo / probe.REFERENCE_ROOT_RELATIVE
    root.mkdir(parents=True)
    graph_rows = {seed: ([] if empty else _rows_for_seed(seed))
                  for seed in probe.GRAPH_SEEDS}
    graph_diags = [{"graph_seed": seed, "status": "ok", "admitted": True,
                    "gf32_rank": 52} for seed in probe.GRAPH_SEEDS]
    candidate_diags = [{"graph_seed": seed, "control_admitted": True,
                        "candidate_admitted": True,
                        "construction_stop": False}
                       for seed in probe.GRAPH_SEEDS]
    manifest = {
        "batch_uuid": probe.REFERENCE_BATCH_UUID,
        "reference_batch_uuid": probe.EDGE_BATCH_UUID,
        "status": "INVENTORY_COMPLETE", "batch_complete": True,
        "graph_seeds": list(probe.GRAPH_SEEDS),
        "decoder_calls": 0, "sampled_frames": 0,
        "truth_prior_or_conditional_arrays_saved": False,
        "graph_diagnostics": graph_diags,
        "candidate_diagnostics": candidate_diags,
    }
    per_graph = {}
    for seed in probe.GRAPH_SEEDS:
        by_ell = {str(ell): {"cycle_count": sum(
            int(row["ell"]) == ell for row in graph_rows[seed])}
            for ell in range(probe.MIN_ELL, probe.MAX_ELL + 1)}
        if row_cap and seed == probe.GRAPH_SEEDS[0]:
            by_ell[str(probe.MIN_ELL)]["cycle_count"] = probe.MAX_CYCLE_ROWS + 1
        per_graph[str(seed)] = {
            "status": "COMPLETE", "by_ell": by_ell,
            "cycle_count": sum(cell["cycle_count"] for cell in by_ell.values()),
        }
    totals_by_ell = {
        str(ell): {"cycle_count": sum(
            per_graph[str(seed)]["by_ell"][str(ell)]["cycle_count"]
            for seed in probe.GRAPH_SEEDS)}
        for ell in range(probe.MIN_ELL, probe.MAX_ELL + 1)
    }
    summary = {
        "batch_uuid": probe.REFERENCE_BATCH_UUID,
        "terminal_status": "INVENTORY_COMPLETE", "batch_complete": True,
        "graph_seeds": list(probe.GRAPH_SEEDS),
        "ell_range": [probe.MIN_ELL, probe.MAX_ELL],
        "truth_prior_or_conditional_arrays_saved": False,
        "per_graph": per_graph, "totals_by_ell": totals_by_ell,
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    all_rows = [row for seed in probe.GRAPH_SEEDS for row in graph_rows[seed]]
    with (root / "cycles.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=census.CYCLE_COLUMNS)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)
    return root, all_rows


class _Clock:
    def __init__(self, start: float = 0.0, step: float = 0.01):
        self.value = start
        self.step = step

    def __call__(self) -> float:
        value = self.value
        self.value += self.step
        return value


def _execute(repo: Path, reference: Path, *, now=None, rss_fn=None) -> dict:
    (repo / "workspace").mkdir(exist_ok=True)
    return probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE, repo_root=repo,
        reference_root=reference, now=now or _Clock(),
        rss_fn=rss_fn or (lambda: 1234),
    )


def test_frozen_profile_dry_run_and_root_refusal(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "workspace").mkdir(parents=True)
    assert probe.P0 == 0.55
    assert probe.SHAPE_COUNTS == ((1, 2295), (3, 1126), (7, 557),
                                  (15, 304), (31, 146))
    assert probe.GRAPH_SEEDS == tuple(range(2026093901, 2026093907))
    assert probe.REFERENCE_BATCH_UUID == "475c2ad3-bd5a-4000-8498-ea989bad1bba"

    def forbidden(*_args, **_kwargs):
        pytest.fail("dry-run must not read census artifacts or compute source overlaps")

    monkeypatch.setattr(probe, "load_predecessor", forbidden)
    monkeypatch.setattr(probe, "verify_cycle_row", forbidden)
    result = probe.dry_run(probe.OUT_ROOT_RELATIVE, repo_root=repo)
    assert result["status"] == "DRY_RUN"
    assert result["census_artifact_reads"] == result["cycle_rows_read"] == 0
    assert result["graph_constructions"] == result["decoder_calls"] == 0
    assert result["writes"] == 0
    assert not (repo / probe.OUT_ROOT_RELATIVE).exists()
    with pytest.raises(ValueError, match="frozen fresh root"):
        probe.validate_out_root("workspace/other", repo_root=repo)
    (repo / probe.OUT_ROOT_RELATIVE).mkdir()
    with pytest.raises(FileExistsError, match="refusing existing"):
        probe.validate_out_root(probe.OUT_ROOT_RELATIVE, repo_root=repo)


def test_bhattacharyya_direct_factorization_and_limits():
    pmf = np.zeros(32, dtype=np.float64)
    pmf[[0, 1, 3, 7]] = [0.4, 0.3, 0.2, 0.1]
    values = probe.bhattacharyya_values(pmf)
    assert values[0] == 1.0
    assert np.all((values >= 0.0) & (values <= 1.0 + 1e-15))
    for z0, z1 in ((0, 0), (1, 3), (7, 31), (12, 5)):
        direct = probe.direct_two_symbol_overlap(pmf, (z0, z1))
        assert direct == pytest.approx(values[z0] * values[z1], abs=2e-15)

    delta = np.zeros(32)
    delta[0] = 1.0
    delta_b = probe.bhattacharyya_values(delta)
    assert np.array_equal(delta_b[1:], np.zeros(31))
    uniform_b = probe.bhattacharyya_values(np.full(32, 1 / 32))
    assert np.allclose(uniform_b, 1.0)
    with pytest.raises(ValueError, match="sum to one"):
        probe.bhattacharyya_values(np.ones(32))


def test_unit_orbit_scalar_order_invariance_and_zero_vs_positive_overlap():
    orbit = ((3, 1), (8, 4), (12, 7))
    b_uniform = np.ones(32)
    baseline = probe.overlap_for_orbit(orbit, b_uniform)
    assert baseline["W"] == 31.0
    assert baseline["positive_overlap_terms"] == 31
    assert baseline["source_status"] == "POSITIVE_OVERLAP"

    scale = 9
    scaled = tuple((variable, probe.layout.gf32_mul(scale, symbol))
                   for variable, symbol in reversed(orbit))
    normalized = probe.normalize_orbit(
        [variable for variable, _ in scaled], [symbol for _, symbol in scaled])
    assert normalized == probe.normalize_orbit(
        [variable for variable, _ in orbit], [symbol for _, symbol in orbit])
    assert probe.overlap_for_orbit(normalized, b_uniform)["W"] == 31.0

    delta = np.zeros(32)
    delta[0] = 1.0
    zero = probe.overlap_for_orbit(orbit, probe.bhattacharyya_values(delta))
    assert zero["W"] == 0.0
    assert zero["positive_overlap_terms"] == 0
    assert zero["source_status"] == "ZERO_SOURCE_OVERLAP"


def test_complete_fake_census_keeps_duplicate_zero_and_nonunit_distinct(
        tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "workspace").mkdir(parents=True)
    reference, rows = _write_fake_census(repo)
    delta = np.zeros(32)
    delta[0] = 1.0
    monkeypatch.setattr(probe, "source_pmf", lambda: delta.copy())
    result = _execute(repo, reference)

    assert result["terminal_status"] == "OVERLAP_COMPLETE"
    assert result["batch_complete"] is True
    assert result["reference_rows_expected"] == result["input_rows_processed"] == 18
    assert result["decoder_calls"] == result["graph_constructions"] == 0
    assert set(path.name for path in (repo / probe.OUT_ROOT_RELATIVE).iterdir()) == {
        "manifest.json", "source_overlap.csv", "summary.json", "EXPLORATION_LOG.md"}
    assert len(rows) == 18

    totals = result["matrix_totals"]
    for arm in ("control", "edge_candidate"):
        values = totals[arm]
        assert values["cycle_rows"] == 18
        assert values["unit_cycle_rows"] == 12
        assert values["nonunit_cycle_rows"] == 6
        assert values["unique_unit_orbits"] == 6
        assert values["duplicate_unit_rows"] == 6
        assert values["zero_source_overlap_orbits"] == 6
        assert values["positive_overlap_orbits"] == 0
        assert values["sum_W_unique_orbits"] == 0.0
        assert values["source_overlap_outcome"] == "ZERO_SOURCE_OVERLAP_ONLY"
    assert len(result["completed_graphs"]) == 6
    for seed in probe.GRAPH_SEEDS:
        graph = result["per_graph"][str(seed)]
        assert graph["status"] == "COMPLETE"
        assert graph["by_ell"]["2"]["control"]["nonunit_cycle_rows"] == 1
        assert graph["by_ell"]["3"]["control"]["unique_unit_orbits"] == 1
        assert graph["by_ell"]["3"]["control"]["duplicate_unit_rows"] == 1

    with (repo / probe.OUT_ROOT_RELATIVE / "source_overlap.csv").open(
            newline="", encoding="utf-8") as handle:
        output_rows = list(csv.DictReader(handle))
    assert output_rows[0]["control_W"] == ""
    assert output_rows[0]["control_source_status"] == "NONUNIT_NO_LOCAL_CODEWORD"
    assert output_rows[1]["control_W"] == "0.0"
    assert output_rows[1]["control_source_status"] == "ZERO_SOURCE_OVERLAP"
    assert output_rows[2]["control_duplicate_orbit"] == "True"

    obs = result["resource_observations"]
    assert obs["check_count"] == 3
    assert obs["max_sampled_rss_bytes"] == 1234
    assert obs["last_sampled_rss_bytes"] == 1234
    assert obs["final_elapsed_s"] >= obs["last_elapsed_s"]


def test_complete_empty_census_is_valid_zero_inventory(tmp_path):
    repo = tmp_path / "repo"
    (repo / "workspace").mkdir(parents=True)
    reference, _ = _write_fake_census(repo, empty=True)
    result = _execute(repo, reference)
    assert result["terminal_status"] == "OVERLAP_COMPLETE"
    assert result["batch_complete"] is True
    assert result["input_rows_processed"] == 0
    assert result["completed_graphs"] == list(probe.GRAPH_SEEDS)
    for matrix in result["matrix_totals"].values():
        assert matrix["unique_unit_orbits"] == 0
        assert matrix["source_overlap_outcome"] == "NO_UNIT_ORBITS_IN_CENSUS"


def test_invalid_witness_retains_partial_rows_and_null_totals(tmp_path,
                                                              monkeypatch):
    repo = tmp_path / "repo"
    (repo / "workspace").mkdir(parents=True)
    reference, _ = _write_fake_census(repo)
    cycle_path = reference / "cycles.csv"
    with cycle_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows[1]["control_witness_values_json"] = "[2,1,1]"
    with cycle_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=census.CYCLE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    monkeypatch.setattr(probe, "source_pmf", lambda: np.eye(1, 32, 0).ravel())
    rss_values = iter((100, 100, probe.RSS_CAP_BYTES))
    result = _execute(repo, reference, rss_fn=lambda: next(rss_values))
    assert result["terminal_status"] == "INVALID_WITNESS_STOP"
    assert result["input_rows_attempted"] == 2
    assert result["input_rows_processed"] == 1
    assert result["totals_by_ell"] is None
    assert result["matrix_totals"] is None
    assert "witness" in result["stop_reason"]
    assert result["resource_observations"]["terminal_sampled"] is True
    assert result["resource_observations"]["terminal_sample_stop_reason"] == "rss_cap"
    assert result["resource_observations"]["check_count"] == 3
    assert result["resource_observations"]["last_elapsed_s"] is not None
    assert result["resource_observations"]["final_elapsed_s"] >= result[
        "resource_observations"]["last_elapsed_s"]
    assert result["resource_observations"]["last_sampled_rss_bytes"] == probe.RSS_CAP_BYTES
    assert result["resource_observations"]["max_sampled_rss_bytes"] == probe.RSS_CAP_BYTES
    with (repo / probe.OUT_ROOT_RELATIVE / "source_overlap.csv").open(
            newline="", encoding="utf-8") as handle:
        output_rows = list(csv.DictReader(handle))
    assert output_rows[-1]["row_status"] == "INVALID_WITNESS_STOP"
    assert "witness" in output_rows[-1]["failure_reason"]


def test_outer_exception_preserves_error_and_persists_terminal_rss_sample(
        tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "workspace").mkdir(parents=True)
    reference, _ = _write_fake_census(repo)
    delta = np.zeros(32)
    delta[0] = 1.0
    monkeypatch.setattr(probe, "source_pmf", lambda: delta.copy())

    def fail_finalize(_summary):
        raise RuntimeError("synthetic finalize failure")

    monkeypatch.setattr(probe, "_finalize_summary", fail_finalize)
    rss_values = iter((100, 100, 100, probe.RSS_CAP_BYTES))
    result = _execute(repo, reference, rss_fn=lambda: next(rss_values))
    assert result["terminal_status"] == "IMPLEMENTATION_STOP"
    assert "RuntimeError:synthetic finalize failure" in result["stop_reason"]
    observations = result["resource_observations"]
    assert observations["terminal_sampled"] is True
    assert observations["terminal_sample_stop_reason"] == "rss_cap"
    assert observations["check_count"] == 4
    assert observations["last_elapsed_s"] is not None
    assert observations["final_elapsed_s"] >= observations["last_elapsed_s"]
    assert observations["last_sampled_rss_bytes"] == probe.RSS_CAP_BYTES
    assert observations["max_sampled_rss_bytes"] == probe.RSS_CAP_BYTES

    output_root = repo / probe.OUT_ROOT_RELATIVE
    manifest = json.loads((output_root / "manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((output_root / "summary.json").read_text(encoding="utf-8"))
    for artifact in (manifest, summary):
        assert artifact["stop_reason"] == result["stop_reason"]
        assert artifact["resource_observations"]["terminal_sampled"] is True
        assert artifact["resource_observations"]["terminal_sample_stop_reason"] == "rss_cap"
        assert artifact["resource_observations"]["last_sampled_rss_bytes"] == probe.RSS_CAP_BYTES


@pytest.mark.parametrize("mode,expected", [
    ("missing", "PREDECESSOR_INCOMPLETE_STOP"),
    ("incomplete", "PREDECESSOR_INCOMPLETE_STOP"),
    ("row_cap", "ROW_CAP_STOP"),
])
def test_predecessor_and_row_cap_stops(tmp_path, mode, expected):
    repo = tmp_path / "repo"
    (repo / "workspace").mkdir(parents=True)
    if mode == "missing":
        reference = repo / probe.REFERENCE_ROOT_RELATIVE
        reference.mkdir()
    else:
        reference, _ = _write_fake_census(repo, row_cap=(mode == "row_cap"))
        if mode == "incomplete":
            path = reference / "manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["batch_complete"] = False
            path.write_text(json.dumps(manifest), encoding="utf-8")
    result = _execute(repo, reference)
    assert result["terminal_status"] == expected
    assert result["totals_by_ell"] is None
    assert result["input_rows_processed"] == 0
    assert result["resource_observations"]["terminal_sampled"] is True
    assert result["resource_observations"]["check_count"] == 2


@pytest.mark.parametrize("mode,expected", [
    ("wall", "total_wall_cap"),
    ("rss", "rss_cap"),
    ("rss_error", "resource_check_exception"),
])
def test_resource_stops_are_recorded_before_reading_cycles(tmp_path, mode, expected):
    repo = tmp_path / "repo"
    (repo / "workspace").mkdir(parents=True)
    reference, _ = _write_fake_census(repo)
    if mode == "wall":
        clock = _Clock(start=0.0, step=probe.WALL_CAP_S + 1)
        rss_fn = lambda: 100
    elif mode == "rss":
        clock = _Clock()
        rss_fn = lambda: probe.RSS_CAP_BYTES
    else:
        clock = _Clock()

        def rss_fn():
            raise OSError("synthetic rss failure")

    result = _execute(repo, reference, now=clock, rss_fn=rss_fn)
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert expected in result["stop_reason"]
    assert result["input_rows_processed"] == 0
    assert result["resource_observations"]["check_count"] == 1
    assert result["resource_observations"]["terminal_sampled"] is False
    assert result["resource_observations"]["last_elapsed_s"] is not None
    if mode == "rss":
        assert result["resource_observations"]["max_sampled_rss_bytes"] == probe.RSS_CAP_BYTES
    if mode == "rss_error":
        assert result["resource_observations"]["max_sampled_rss_bytes"] is None

