"""Fake-only tests for the decoder-free GF(32) short-cycle census."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.cli.probes_closed import nbldpc_gf32_cycle_census as probe
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout


def _ring_matrix(ell: int, coefficients: tuple[int, ...] | None = None
                 ) -> np.ndarray:
    matrix = np.zeros((ell, ell), dtype=np.int64)
    values = coefficients or (1,) * ell
    for index in range(ell):
        matrix[index, index] = int(values[index])
        matrix[(index + 1) % ell, index] = 1
    return matrix


def _k4_matrix() -> np.ndarray:
    matrix = np.zeros((4, 6), dtype=np.int64)
    column = 0
    for first in range(4):
        for second in range(first + 1, 4):
            matrix[first, column] = 1
            matrix[second, column] = 1
            column += 1
    return matrix


def _scale_rows(matrix: np.ndarray, scales: list[int]) -> np.ndarray:
    return np.asarray([
        [layout.gf32_mul(scales[row], int(value)) for value in values]
        for row, values in enumerate(matrix)
    ], dtype=np.int64)


def _scale_columns(matrix: np.ndarray, scales: list[int]) -> np.ndarray:
    return np.asarray([
        [layout.gf32_mul(int(value), scales[column])
         for column, value in enumerate(values)]
        for values in matrix
    ], dtype=np.int64)


def _graph(seed: int, matrix: np.ndarray) -> dict:
    return {"graph_seed": int(seed), "dense": matrix.copy(), "status": "ok"}


def _graph_diag(seed: int) -> dict:
    return {"graph_seed": int(seed), "admitted": True,
            "profile": True, "failure_reason": ""}


def _candidate_diag(seed: int, control: np.ndarray,
                    candidate: np.ndarray) -> dict:
    gauge = probe.edge_runner.gauge_diagnostics(control, candidate)
    return {
        "graph_seed": int(seed),
        "control_admitted": True,
        "candidate_admitted": True,
        "construction_stop": False,
        "control_J_bits": 1.25,
        "candidate_J_initial_bits": 1.25,
        "candidate_J_bits": 1.75,
        "candidate_J_gain_bits": 0.5,
        "control_rank": int(layout.gf32_row_rank(control)),
        "candidate_rank": int(layout.gf32_row_rank(candidate)),
        "support_equal": bool(np.array_equal(control != 0, candidate != 0)),
        "degrees_equal": True,
        "candidate_nontrivial": bool(np.any(control != candidate)),
        "edge_sweep": {
            "initial_J_bits": 1.25,
            "J_bits": 1.75,
            "J_change_bits": 0.5,
            "accumulated_J_bits": 1.75,
            "reference_drift_bits": 0.0,
            "changed_edge_count": int(np.count_nonzero(control != candidate)),
            "sweep_count": 1,
            "construction_stop": False,
            "failure_reason": "",
            "updates": [],
        },
        "gauge": gauge,
    }


def _edge_projection(diagnostic: dict) -> dict:
    edge = diagnostic["edge_sweep"]
    return {
        "control_J_bits": diagnostic["control_J_bits"],
        "candidate_initial_J_bits": diagnostic["candidate_J_initial_bits"],
        "candidate_final_J_bits": diagnostic["candidate_J_bits"],
        "candidate_J_gain_bits": diagnostic["candidate_J_gain_bits"],
        "changed_edge_count": edge["changed_edge_count"],
        "edge_sweep_count": edge["sweep_count"],
        "construction_stop": diagnostic["construction_stop"],
    }


def _fake_builders(matrix: np.ndarray, flip_candidate: bool = True):
    def graph_builder(seed: int) -> dict:
        return _graph(seed, matrix)

    def candidate_builder(dense: np.ndarray, _pmf: np.ndarray, seed: int):
        control = np.asarray(dense, dtype=np.int64).copy()
        candidate = control.copy()
        if flip_candidate:
            row, column = next(zip(*np.nonzero(candidate)))
            candidate[row, column] = 2
        return control, candidate, _candidate_diag(seed, control, candidate)

    def preflight(graph: dict, seed: int):
        return True, _graph_diag(seed)

    return graph_builder, candidate_builder, preflight


def _write_reference(repo: Path, matrix: np.ndarray,
                     candidate_builder=None) -> Path:
    reference = repo / probe.REFERENCE_ROOT_RELATIVE
    reference.mkdir(parents=True)
    if candidate_builder is None:
        _, candidate_builder, _ = _fake_builders(matrix)
    graph_diags = []
    candidate_diags = []
    for seed in probe.GRAPH_SEEDS:
        graph_diags.append(_graph_diag(seed))
        control, candidate, diagnostic = candidate_builder(
            matrix.copy(), np.zeros(32, dtype=np.float64), seed)
        candidate_diags.append(diagnostic)
    manifest = {
        "batch_uuid": probe.REFERENCE_BATCH_UUID,
        "attempted_decoder_calls": 384,
        "arm_mapping": {
            "control": "accepted deep H0D rebuilt by search-depth helper",
            "candidate": "one row-major absolute edge-label sweep from control",
        },
        "graph_diagnostics": graph_diags,
        "candidate_diagnostics": candidate_diags,
    }
    summary = {
        "batch_uuid": probe.REFERENCE_BATCH_UUID,
        "holdout_complete": True,
        "holdout_pairs_completed": 192,
        "search_diagnostics": candidate_diags,
        "edge_diagnostics_by_graph": {
            str(seed): _edge_projection(diag)
            for seed, diag in zip(probe.GRAPH_SEEDS, candidate_diags)
        },
        "gauge_by_graph": {
            str(seed): diag["gauge"]
            for seed, diag in zip(probe.GRAPH_SEEDS, candidate_diags)
        },
    }
    (reference / "manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8")
    (reference / "summary.json").write_text(
        json.dumps(summary), encoding="utf-8")
    return reference


def _prepare_repo(tmp_path: Path, matrix: np.ndarray,
                  candidate_builder=None):
    repo = tmp_path / "repo"
    (repo / "workspace").mkdir(parents=True)
    reference = _write_reference(repo, matrix, candidate_builder)
    builders = _fake_builders(matrix)
    return repo, reference, builders


def _all_four_outputs(root: Path) -> set[str]:
    return {path.name for path in root.iterdir()}


def test_frozen_constants_dry_run_and_root_policy(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "workspace").mkdir(parents=True)
    assert probe.BATCH_UUID == "475c2ad3-bd5a-4000-8498-ea989bad1bba"
    assert probe.OUT_ROOT_RELATIVE == Path("workspace/gf32_cycle_census_475c2ad3")
    assert probe.GRAPH_SEEDS == (2026093901, 2026093902, 2026093903,
                                 2026093904, 2026093905, 2026093906)
    assert (probe.N, probe.M, probe.EDGE_COUNT, probe.POLY) == (128, 52, 256, 37)
    assert (probe.MIN_ELL, probe.MAX_ELL) == (2, 6)
    assert probe.MAX_DFS_STATES == 2_000_000
    assert probe.MAX_CYCLES_PER_GRAPH == 100_000

    def forbidden(*_args, **_kwargs):
        pytest.fail("dry-run entered graph, input, or enumeration work")

    monkeypatch.setattr(probe, "enumerate_cycles", forbidden)
    monkeypatch.setattr(probe, "_read_reference", forbidden)
    monkeypatch.setattr(probe.edge_runner, "build_profile_graph", forbidden)
    result = probe.dry_run(probe.OUT_ROOT_RELATIVE, repo_root=repo)
    assert result["status"] == "DRY_RUN"
    assert result["decoder_calls"] == result["graph_construction_calls"] == 0
    assert result["candidate_reconstruction_calls"] == 0
    assert result["cycle_enumerations"] == result["reference_artifact_reads"] == 0
    assert result["writes"] == 0
    assert not (repo / probe.OUT_ROOT_RELATIVE).exists()
    with pytest.raises(ValueError, match="frozen fresh root"):
        probe.validate_out_root("workspace/not-the-census-root", repo_root=repo)
    (repo / probe.OUT_ROOT_RELATIVE).mkdir()
    with pytest.raises(FileExistsError, match="refusing existing"):
        probe.validate_out_root(probe.OUT_ROOT_RELATIVE, repo_root=repo)


def test_simple_cycle_enumeration_canonical_counts_and_ell_ceiling():
    parallel = np.asarray([[1, 1], [1, 1]], dtype=np.int64)
    result2 = probe.enumerate_cycles(parallel)
    assert result2["stop_reason"] == ""
    assert [(len(row["rows"]), row["rows"], row["variables"])
            for row in result2["cycles"]] == [(2, [0, 1], [0, 1])]

    triangle = probe.enumerate_cycles(_ring_matrix(3))
    assert [len(cycle["rows"]) for cycle in triangle["cycles"]] == [3]
    six = probe.enumerate_cycles(_ring_matrix(6))
    assert [len(cycle["rows"]) for cycle in six["cycles"]] == [6]
    seven = probe.enumerate_cycles(_ring_matrix(7))
    assert seven["cycles"] == []

    k4 = probe.enumerate_cycles(_k4_matrix())
    assert [len(cycle["rows"]) for cycle in k4["cycles"]].count(3) == 4
    assert [len(cycle["rows"]) for cycle in k4["cycles"]].count(4) == 3
    assert len(k4["cycles"]) == 7
    keys = [tuple(cycle["key"]) for cycle in k4["cycles"]]
    assert keys == sorted(keys) and len(set(keys)) == len(keys)
    for cycle in k4["cycles"]:
        assert cycle["rows"][0] == min(cycle["rows"])
        assert len(set(cycle["rows"])) == len(cycle["rows"])
        assert len(set(cycle["variables"])) == len(cycle["variables"])

    original = probe.canonical_cycle_key((0, 1, 2, 3), (0, 1, 2, 3))
    rotated = probe.canonical_cycle_key((2, 3, 0, 1), (2, 3, 0, 1))
    reversed_key = probe.canonical_cycle_key((0, 3, 2, 1), (3, 2, 1, 0))
    assert original == rotated == reversed_key


def test_gf32_cycle_product_witness_rank_and_gauge_invariance():
    control = _ring_matrix(3)
    rows, variables = (0, 1, 2), (0, 1, 2)
    unit = probe.cycle_matrix_facts(control, rows, variables)
    assert unit["product"] == 1 and unit["unit"] is True
    assert unit["cycle_submatrix_rank"] == 2
    assert unit["witness_values"] == [1, 1, 1]
    for index, row in enumerate(rows):
        prev = (index - 1) % 3
        assert (layout.gf32_mul(int(control[row, variables[prev]]),
                                unit["witness_values"][prev])
                ^ layout.gf32_mul(int(control[row, variables[index]]),
                                  unit["witness_values"][index])) == 0

    row_gauge = _scale_rows(control, [2, 7, 11])
    col_gauge = _scale_columns(control, [3, 9, 13])
    row_col_gauge = _scale_columns(row_gauge, [5, 4, 8])
    for transformed in (row_gauge, col_gauge, row_col_gauge):
        facts = probe.cycle_matrix_facts(transformed, rows, variables)
        assert facts["product"] == 1 and facts["unit"] is True
        assert facts["cycle_submatrix_rank"] == 2
        assert all(value != 0 for value in facts["witness_values"])

    changed = control.copy()
    changed[0, 0] = 2
    nonunit = probe.cycle_matrix_facts(changed, rows, variables)
    assert nonunit["product"] != 1 and nonunit["unit"] is False
    assert nonunit["witness_values"] is None
    assert nonunit["cycle_submatrix_rank"] == 3

    # The reporting ceiling deliberately does not imply a global/composite
    # support-distance result from a local cycle inventory.
    summary = probe._base_summary()
    assert "composite-support" in summary["claim_ceiling"]
    assert "minimum_distance" not in summary


def test_enumeration_caps_and_resource_checkpoint_retain_partial_cycles():
    k4 = _k4_matrix()
    by_cycles = probe.enumerate_cycles(k4, max_cycles=1)
    assert by_cycles["stop_reason"] == "ENUMERATION_CAP_STOP:unique_cycles"
    assert len(by_cycles["cycles"]) == 1

    by_states = probe.enumerate_cycles(k4, max_states=2)
    assert by_states["stop_reason"] == "ENUMERATION_CAP_STOP:dfs_states"
    assert by_states["dfs_states"] == 2

    checked = []

    def stop_at_checkpoint(states: int, cycles: int):
        checked.append((states, cycles))
        return "test_wall_cap"

    # A tiny complete check graph gives enough simple paths to hit the interval.
    dense = np.zeros((8, 28), dtype=np.int64)
    column = 0
    for first in range(8):
        for second in range(first + 1, 8):
            dense[first, column] = 1
            dense[second, column] = 1
            column += 1
    inventory = probe.enumerate_cycles(
        dense, max_states=3000, checkpoint=stop_at_checkpoint)
    assert checked and checked[0][0] == probe.RESOURCE_CHECK_STATES
    assert inventory["stop_reason"] == "RESOURCE_STOP:test_wall_cap"
    assert inventory["dfs_states"] == probe.RESOURCE_CHECK_STATES


def test_complete_fake_batch_writes_four_files_and_per_graph_inventory(tmp_path):
    matrix = _ring_matrix(3)
    repo, reference, builders = _prepare_repo(tmp_path, matrix)
    graph_builder, candidate_builder, preflight = builders
    graph_calls: list[int] = []
    candidate_calls: list[int] = []

    def counted_graph(seed: int):
        graph_calls.append(seed)
        return graph_builder(seed)

    def counted_candidate(dense, pmf, seed):
        candidate_calls.append(seed)
        return candidate_builder(dense, pmf, seed)

    result = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE, repo_root=repo,
        reference_root=reference, graph_builder=counted_graph,
        candidate_builder=counted_candidate,
        graph_preflight_fn=preflight, now=lambda: 10.0, rss_fn=lambda: 0,
    )
    root = repo / probe.OUT_ROOT_RELATIVE
    assert result["terminal_status"] == "INVENTORY_COMPLETE"
    assert result["batch_complete"] is True
    assert result["decoder_calls"] == result["sampled_frames"] == 0
    assert result["completed_graphs"] == list(probe.GRAPH_SEEDS)
    assert graph_calls == candidate_calls == list(probe.GRAPH_SEEDS)
    assert _all_four_outputs(root) == {
        "manifest.json", "summary.json", "cycles.csv", "EXPLORATION_LOG.md"
    }
    assert result["totals_by_ell"]["3"]["cycle_count"] == 6
    assert result["totals_by_ell"]["3"]["control_unit_count"] == 6
    assert result["totals_by_ell"]["3"]["edge_candidate_unit_count"] == 0
    assert result["totals_by_ell"]["3"]["unit_to_nonunit"] == 6
    assert result["control_matrix_outcome"] == "UNIT_PRESENT_IN_RANGE"
    assert result["edge_candidate_matrix_outcome"] == "NO_UNIT_CYCLE_IN_RANGE"
    with (root / "cycles.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 6
    assert all(row["control_product"] == "1" and row["control_unit"] == "True"
               for row in rows)
    assert all(row["candidate_unit"] == "False"
               and row["state_transition"] == "unit_to_nonunit" for row in rows)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["truth_prior_or_conditional_arrays_saved"] is False
    assert manifest["decoder_calls"] == manifest["sampled_frames"] == 0


def test_reference_mismatch_stops_before_inventory_and_keeps_four_outputs(tmp_path,
                                                                          monkeypatch):
    matrix = _ring_matrix(3)
    repo, reference, builders = _prepare_repo(tmp_path, matrix)
    graph_builder, _, preflight = builders
    calls: list[int] = []

    def altered_candidate(dense, pmf, seed):
        calls.append(seed)
        control = dense.copy()
        candidate = control.copy()
        candidate[0, 0] = 3
        diagnostic = _candidate_diag(seed, control, candidate)
        diagnostic["candidate_J_gain_bits"] += 0.1
        return control, candidate, diagnostic

    def forbidden(*_args, **_kwargs):
        pytest.fail("reference mismatch must stop before enumeration")

    monkeypatch.setattr(probe, "enumerate_cycles", forbidden)
    result = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE, repo_root=repo,
        reference_root=reference, graph_builder=graph_builder,
        candidate_builder=altered_candidate,
        graph_preflight_fn=preflight, now=lambda: 0.0, rss_fn=lambda: 0,
    )
    root = repo / probe.OUT_ROOT_RELATIVE
    assert result["terminal_status"] == "REFERENCE_MISMATCH_STOP"
    assert "candidate_J_gain_bits" in result["stop_reason"]
    assert calls == [probe.GRAPH_SEEDS[0]]
    assert result["completed_graphs"] == []
    assert _all_four_outputs(root) == {
        "manifest.json", "summary.json", "cycles.csv", "EXPLORATION_LOG.md"
    }


def test_partial_cycle_cap_retains_rows_nulls_batch_totals_and_stops_next_graph(
        tmp_path, monkeypatch):
    matrix = _k4_matrix()
    repo, reference, builders = _prepare_repo(tmp_path, matrix)
    graph_builder, candidate_builder, preflight = builders
    graph_calls: list[int] = []

    def counted_graph(seed: int):
        graph_calls.append(seed)
        return graph_builder(seed)

    monkeypatch.setattr(probe, "MAX_CYCLES_PER_GRAPH", 1)
    result = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE, repo_root=repo,
        reference_root=reference, graph_builder=counted_graph,
        candidate_builder=candidate_builder,
        graph_preflight_fn=preflight, now=lambda: 0.0, rss_fn=lambda: 0,
    )
    root = repo / probe.OUT_ROOT_RELATIVE
    assert result["terminal_status"] == "ENUMERATION_CAP_STOP"
    assert result["completed_graphs"] == []
    assert result["attempted_graphs"] == [probe.GRAPH_SEEDS[0]]
    assert graph_calls == [probe.GRAPH_SEEDS[0]]
    assert result["totals_by_ell"] is None
    assert result["control_matrix_outcome"] is None
    assert result["edge_candidate_matrix_outcome"] is None
    assert result["per_graph"][str(probe.GRAPH_SEEDS[0])]["status"] == "PARTIAL_STOP"
    assert result["per_graph"][str(probe.GRAPH_SEEDS[0])]["cycle_count"] == 1
    with (root / "cycles.csv").open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 1


def test_wall_rss_and_exception_stops_do_not_start_the_next_graph(tmp_path):
    matrix = _ring_matrix(3)

    repo_rss, reference_rss, builders_rss = _prepare_repo(
        tmp_path / "rss", matrix)
    rss_graph, rss_candidate, rss_preflight = builders_rss
    rss_calls: list[int] = []

    def counted_rss_graph(seed: int):
        rss_calls.append(seed)
        return rss_graph(seed)

    rss_result = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE, repo_root=repo_rss,
        reference_root=reference_rss, graph_builder=counted_rss_graph,
        candidate_builder=rss_candidate, graph_preflight_fn=rss_preflight,
        now=lambda: 0.0, rss_fn=lambda: probe.RSS_CAP_BYTES,
    )
    assert rss_result["terminal_status"] == "RESOURCE_STOP"
    assert rss_result["stop_reason"] == "rss_cap"
    assert rss_calls == []
    assert rss_result["totals_by_ell"] is None

    repo_wall, reference_wall, builders_wall = _prepare_repo(
        tmp_path / "wall", matrix)
    wall_graph, wall_candidate, wall_preflight = builders_wall
    clock = {"now": 0.0}
    wall_calls: list[int] = []

    def overrun_graph(seed: int):
        wall_calls.append(seed)
        clock["now"] = probe.WALL_CAP_S + 1.0
        return wall_graph(seed)

    wall_result = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE, repo_root=repo_wall,
        reference_root=reference_wall, graph_builder=overrun_graph,
        candidate_builder=wall_candidate,
        graph_preflight_fn=wall_preflight,
        now=lambda: clock["now"], rss_fn=lambda: 0,
    )
    assert wall_result["terminal_status"] == "RESOURCE_STOP"
    assert wall_result["stop_reason"] == "total_wall_cap"
    assert wall_calls == [probe.GRAPH_SEEDS[0]]
    assert wall_result["totals_by_ell"] is None

    repo_exc, reference_exc, builders_exc = _prepare_repo(
        tmp_path / "exception", matrix)
    _, exc_candidate, exc_preflight = builders_exc
    exception_calls: list[int] = []

    def fail_graph(seed: int):
        exception_calls.append(seed)
        raise RuntimeError("fake graph construction failure")

    exception_result = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE, repo_root=repo_exc,
        reference_root=reference_exc, graph_builder=fail_graph,
        candidate_builder=exc_candidate, graph_preflight_fn=exc_preflight,
        now=lambda: 0.0, rss_fn=lambda: 0,
    )
    assert exception_result["terminal_status"] == "IMPLEMENTATION_STOP"
    assert "fake graph construction failure" in exception_result["stop_reason"]
    assert exception_calls == [probe.GRAPH_SEEDS[0]]

