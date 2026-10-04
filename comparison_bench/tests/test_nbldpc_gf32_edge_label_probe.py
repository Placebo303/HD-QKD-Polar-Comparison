"""Fake-only tests for the fixed-graph GF(32) edge-label EXPLORE probe."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_edge_label_probe as probe
from comparison_bench.formal_ir import nbldpc_gf32_label_alignment as alignment
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout


def _fake_dense() -> np.ndarray:
    """Small deterministic fixture with the frozen 128/52/256 profile."""
    row_degrees = [4] * 4 + [5] * 48
    dense = np.zeros((probe.M, probe.N), dtype=np.int64)
    # A row-cycle makes the bipartite support connected. Pair the remaining
    # row sockets in round-robin layers so each variable still has degree two.
    column = 0
    for row in range(probe.M):
        next_row = (row + 1) % probe.M
        dense[row, column] = 1
        dense[next_row, column] = 2
        column += 1
    residual = [degree - 2 for degree in row_degrees]
    sockets = [
        row for layer in range(max(residual))
        for row, count in enumerate(residual) if count > layer
    ]
    assert len(sockets) == 2 * (probe.N - probe.M)
    for index in range(0, len(sockets), 2):
        first, second = sockets[index:index + 2]
        assert first != second
        dense[first, column] = 1
        dense[second, column] = 2
        column += 1
    assert column == probe.N
    assert np.count_nonzero(dense) == probe.EDGE_COUNT == 256
    return dense


def _fake_graph(seed: int) -> dict:
    return {
        "status": "ok", "graph_seed": int(seed),
        "n": probe.N, "m": probe.M, "E": probe.EDGE_COUNT,
        "dense": _fake_dense(), "admitted": True, "failure_reason": "",
        "structure": {
            "admitted": True,
            "admission": {"profile": True, "connected": True,
                          "full_rank": True},
            "gf32_rank": probe.M, "structural_rank": probe.M,
            "connected_components": 1, "duplicate_edges": 0,
        },
    }


def _test_repo(path: Path) -> tuple[Path, Path]:
    repo = path / "repo"
    (repo / "workspace").mkdir(parents=True)
    return repo, probe.OUT_ROOT_RELATIVE


def _mul(a: int, b: int) -> int:
    return int(layout.gf32_mul(int(a), int(b)))


def _row_scaled(matrix: np.ndarray, scales: list[int]) -> np.ndarray:
    return np.asarray([
        [_mul(scales[row], int(value)) for value in values]
        for row, values in enumerate(matrix)
    ], dtype=np.int64)


def _column_scaled(matrix: np.ndarray, scales: list[int]) -> np.ndarray:
    return np.asarray([
        [_mul(int(value), scales[column]) for column, value in enumerate(row)]
        for row in matrix
    ], dtype=np.int64)


def _gauge_summary(graph_seed: int, changed: bool) -> dict:
    base = np.ones((2, 2), dtype=np.int64)
    candidate = base.copy()
    if changed:
        candidate[1, 1] = 2
    gauge = probe.gauge_diagnostics(base, candidate)
    return {
        "graph_seed": int(graph_seed),
        "control_admitted": True, "candidate_admitted": True,
        "construction_stop": False,
        "gauge": gauge,
        "row_column_gauge_equivalent": gauge["row_column_gauge_equivalent"],
        "cycle_class_changed": gauge["cycle_class_changed"],
        "nonunit_residual_count": gauge["nonunit_residual_count"],
        "gauge_witness": gauge["witness"],
    }


def _complete_rows(control_by_graph: list[int],
                   delta_by_graph: list[int],
                   cycle_changed_graphs: set[int]):
    """Make the complete frozen denominator without running a decoder."""
    _, holdouts = probe.seed_plan()
    pmf = probe.shape_pmf_grid()[0]
    rows = []
    pairs = []
    for pair_index, (graph_seed, stream, frame, seed) in enumerate(holdouts):
        graph_index = probe.GRAPH_SEEDS.index(graph_seed)
        pair_slot = stream * probe.HOLDOUT_FRAMES_PER_STREAM + frame
        control_exact = pair_slot < control_by_graph[graph_index]
        candidate_exact = pair_slot < (
            control_by_graph[graph_index] + delta_by_graph[graph_index]
        )
        pair_outcomes = {"control": control_exact,
                         "candidate": candidate_exact}
        for offset, arm in enumerate(probe.arm_order(frame), start=1):
            exact = pair_outcomes[arm]
            # Keep one syndrome-consistent wrong estimate isolated from exact
            # success; it is deliberately placed on a control failure.
            wrong = bool(
                graph_index == 0 and stream == 1 and frame == 15
                and arm == "control" and not exact
            )
            rows.append(probe.predecessor._record_row(
                phase="holdout", pmf=pmf, graph_seed=graph_seed,
                stream=stream, frame=frame, seed=seed,
                call_index=2 * pair_index + offset, arm=arm,
                observed={
                    "exact": bool(exact),
                    "syndrome_accept": bool(exact or wrong),
                    "syndrome_consistent_wrong": wrong,
                    "status": "fake", "iterations": 1,
                    "wall_s": 0.0, "rss_b": 0,
                },
            ))
        pairs.append({
            "graph_seed": graph_seed, "stream": stream, "frame": frame,
            "control_exact": bool(control_exact),
            "candidate_exact": bool(candidate_exact),
        })
    diagnostics = [
        _gauge_summary(seed, index in cycle_changed_graphs)
        for index, seed in enumerate(probe.GRAPH_SEEDS)
    ]
    return rows, pairs, diagnostics


def _summary(control_by_graph: list[int], delta_by_graph: list[int],
             cycle_changed_graphs: set[int]) -> dict:
    rows, pairs, diagnostics = _complete_rows(
        control_by_graph, delta_by_graph, cycle_changed_graphs
    )
    return probe._summarize(rows, pairs, "", diagnostics)


def _fake_batch_candidate(dense: np.ndarray, pmf: np.ndarray,
                          graph_seed: int):
    """Inject equal candidates on two graphs and one-edge candidates on four."""
    control = np.asarray(dense, dtype=np.int64).copy()
    candidate = control.copy()
    graph_index = probe.GRAPH_SEEDS.index(int(graph_seed))
    if graph_index < 4:
        base_gauge = probe.gauge_diagnostics(control, control)
        tree = {tuple(edge) for edge in base_gauge["tree_edges"]}
        closing_edge = next(
            (row, column)
            for row in range(control.shape[0])
            for column in range(control.shape[1])
            if control[row, column] != 0 and (row, column) not in tree
        )
        old = int(candidate[closing_edge])
        candidate[closing_edge] = old % 31 + 1
    gauge = probe.gauge_diagnostics(control, candidate)
    diagnostic = {
        "graph_seed": int(graph_seed),
        "control_admitted": True, "candidate_admitted": True,
        # Keep the predecessor seam aliases true for the test injection.
        "deep_candidate_admitted": True,
        "construction_stop": False,
        "control_rank": probe.M, "candidate_rank": probe.M,
        "support_equal": True, "degrees_equal": True,
        "candidate_nontrivial": bool(np.any(candidate != control)),
        "gauge": gauge,
        "row_column_gauge_equivalent": gauge["row_column_gauge_equivalent"],
        "cycle_class_changed": gauge["cycle_class_changed"],
        "nonunit_residual_count": gauge["nonunit_residual_count"],
        "gauge_witness": gauge["witness"],
    }
    return control, candidate, diagnostic


def test_frozen_seed_contract_pmf_dry_run_and_fresh_root(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path)
    assert probe.BATCH_UUID == "1efed423-10c8-4c51-a119-844f2b922ab5"
    assert probe.SEED_PREFIX == "gf32-edge-label-v1"
    assert probe.OUT_ROOT_RELATIVE == Path(
        "workspace/gf32_edge_label_1efed423"
    )
    assert probe.P0_GRID == (0.550,)
    assert probe.MAX_PILOT_CALLS == 0
    assert probe.HOLDOUT_PAIRS == 192
    assert probe.MAX_HOLDOUT_CALLS == probe.MAX_CALLS == 384
    assert (probe.N, probe.M, probe.EDGE_COUNT) == (128, 52, 256)

    grid = probe.shape_pmf_grid()
    assert len(grid) == 1 and grid[0]["index"] == 0
    assert grid[0]["p0"] == 0.550
    assert np.flatnonzero(grid[0]["pmf"]).tolist() == [0, 1, 3, 7, 15, 31]
    assert grid[0]["pmf"].sum() == pytest.approx(1.0, abs=1e-12)
    pilots, holdouts = probe._validate_seed_plan()
    assert pilots == [] and len(holdouts) == 192
    assert len({row[3] for row in holdouts}) == 192
    assert all(probe.holdout_seed(g, s, f) == seed
               for g, s, f, seed in holdouts)

    def forbidden(*_args, **_kwargs):
        pytest.fail("dry-run entered graph, sample, or decoder work")

    monkeypatch.setattr(probe, "build_profile_graph", forbidden)
    monkeypatch.setattr(probe.prior_runner, "sample_error", forbidden)
    monkeypatch.setattr(probe.prior_runner, "decode_observation", forbidden)
    monkeypatch.setattr(probe.d10, "build_degree_sequence_peg", forbidden)
    result = probe.dry_run(out_root, repo_root=repo)
    assert result["status"] == "DRY_RUN"
    assert result["writes"] == result["empirical_input_reads"] == 0
    assert result["graph_construction_calls"] == result["decoder_calls"] == 0
    assert result["pilot_call_ceiling"] == 0
    assert result["holdout_pair_count"] == 192
    assert result["holdout_call_count"] == result["maximum_call_count"] == 384
    assert result["holdout_seeds_disjoint_from_prior_batches"] is True
    assert not (repo / out_root).exists()

    assert probe.validate_out_root(out_root, repo_root=repo) == repo / out_root
    with pytest.raises(ValueError, match="frozen"):
        probe.validate_out_root("workspace/other", repo_root=repo)
    (repo / out_root).mkdir()
    with pytest.raises(FileExistsError, match="refusing existing"):
        probe.validate_out_root(out_root, repo_root=repo)


def test_edge_sweep_is_deterministic_absolute_beta_row_major_and_unfiltered(
        monkeypatch
):
    h = np.asarray([[1, 2, 0], [3, 0, 5]], dtype=np.int64)
    pmf = probe.shape_pmf_grid()[0]["pmf"]
    expected_order = [(0, 0), (0, 1), (1, 0), (1, 2)]
    beta_calls = []
    choose = alignment.choose_label

    def checked_choose(scores, current, tolerance):
        beta_calls.append((list(scores), int(current), float(tolerance)))
        return choose(scores, current, tolerance)

    monkeypatch.setattr(alignment, "choose_label", checked_choose)
    monkeypatch.setattr(
        probe.d10, "gf32_row_rank",
        lambda *_args, **_kwargs: pytest.fail(
            "rank must not filter labels during the coordinate sweep"
        ),
    )
    first = probe.edge_sweep(h, pmf)
    second = probe.edge_sweep(h, pmf)
    assert first["sweep_count"] == 1
    assert len(first["updates"]) == int(np.count_nonzero(h))
    assert [(item["row"], item["column"])
            for item in first["updates"]] == expected_order
    assert all([beta for beta, _ in scores] == list(range(1, 32))
               for scores, _, _ in beta_calls)
    assert all(tolerance == pytest.approx(alignment.TIE_TOL)
               for _, _, tolerance in beta_calls)
    np.testing.assert_array_equal(first["matrix"], second["matrix"])
    assert first["updates"] == second["updates"]
    assert first["initial_J_bits"] == pytest.approx(
        alignment.marginal_score(h, pmf)[0], abs=1e-12
    )
    assert first["J_bits"] == pytest.approx(
        alignment.marginal_score(first["matrix"], pmf)[0], abs=1e-12
    )
    assert first["reference_drift_bits"] == pytest.approx(0.0, abs=1e-10)
    assert first["construction_stop"] is False
    np.testing.assert_array_equal(first["matrix"] != 0, h != 0)
    np.testing.assert_array_equal(
        np.count_nonzero(first["matrix"], axis=0), np.count_nonzero(h, axis=0)
    )
    np.testing.assert_array_equal(
        np.count_nonzero(first["matrix"], axis=1), np.count_nonzero(h, axis=1)
    )
    assert all(1 <= int(item["chosen"]) <= 31 for item in first["updates"])

    # Uniform errors make every absolute beta tie; the current edge coefficient
    # is retained when it belongs to the tie set.
    tied = probe.edge_sweep(h, np.full(32, 1.0 / 32.0))
    np.testing.assert_array_equal(tied["matrix"], h)
    assert tied["changed_edge_count"] == 0
    assert all(item["chosen"] == item["old"] for item in tied["updates"])


def test_tie_rule_keeps_current_else_uses_smallest_absolute_beta():
    scores = [(7, 1.0), (3, 1.0), (5, 1.0), (2, 0.9)]
    assert alignment.choose_label(scores, current=5, tolerance=1e-12) == 5
    assert alignment.choose_label(scores, current=9, tolerance=1e-12) == 3


@pytest.mark.parametrize("stop_kind", ["full_j_drift", "material_decrease"])
def test_edge_sweep_reports_drift_and_j_decrease_stop(
        monkeypatch, stop_kind
):
    h = np.asarray([[1, 2, 0], [3, 0, 5]], dtype=np.int64)
    pmf = probe.shape_pmf_grid()[0]["pmf"]
    original = alignment.marginal_score
    calls = {"count": 0}

    def perturbed_score(matrix, actual_pmf):
        score, rows = original(matrix, actual_pmf)
        calls["count"] += 1
        if stop_kind == "full_j_drift" and calls["count"] == 2:
            score += 1e-5
        elif stop_kind == "material_decrease":
            score += 1e3 if calls["count"] == 1 else -1e3
        return score, rows

    monkeypatch.setattr(alignment, "marginal_score", perturbed_score)
    result = probe.edge_sweep(h, pmf)
    assert result["construction_stop"] is True
    if stop_kind == "full_j_drift":
        assert abs(result["reference_drift_bits"]) > 1e-10
        assert "FULL_J_INCREMENT_DRIFT" in result["failure_reason"]
    else:
        assert result["J_change_bits"] < -1e-10
        assert "MATERIAL_J_DECREASE" in result["failure_reason"]


def test_candidate_builder_starts_at_deep_control_and_keeps_equal_candidate(
        monkeypatch
):
    h0 = _fake_dense()
    pmf = probe.shape_pmf_grid()[0]["pmf"]
    onepass = alignment.scale_columns(h0, np.full(probe.N, 2))
    control = alignment.scale_columns(h0, np.full(probe.N, 3))
    search_calls = []

    def fake_control(matrix, actual_pmf, graph_seed):
        search_calls.append((matrix.copy(), actual_pmf.copy(), graph_seed))
        return onepass.copy(), control.copy(), {
            "graph_seed": int(graph_seed), "construction_stop": False,
            "deep_candidate_admitted": True,
        }

    rank_phase = {"edge_done": False, "calls": []}

    def same_edge_start(matrix, actual_pmf):
        np.testing.assert_array_equal(matrix, control)
        np.testing.assert_array_equal(actual_pmf, pmf)
        assert rank_phase["calls"] == []
        rank_phase["edge_done"] = True
        j = float(alignment.marginal_score(matrix, actual_pmf)[0])
        return {
            "matrix": matrix.copy(), "initial_J_bits": j, "J_bits": j,
            "accumulated_J_bits": j, "reference_drift_bits": 0.0,
            "J_change_bits": 0.0, "updates": [],
            "changed_edge_count": 0, "sweep_count": 1,
            "construction_stop": False, "failure_reason": "",
        }

    def fake_rank(matrix):
        assert rank_phase["edge_done"]
        rank_phase["calls"].append(np.asarray(matrix).shape)
        return probe.M

    monkeypatch.setattr(probe.search_depth, "build_candidate_pair", fake_control)
    monkeypatch.setattr(probe, "edge_sweep", same_edge_start)
    monkeypatch.setattr(probe.d10, "gf32_row_rank", fake_rank)
    returned_control, candidate, diagnostic = probe.candidate_builder(
        h0, pmf, 17
    )
    assert len(search_calls) == 1
    np.testing.assert_array_equal(search_calls[0][0], h0)
    assert search_calls[0][2] == 17
    np.testing.assert_array_equal(returned_control, control)
    np.testing.assert_array_equal(candidate, control)
    assert diagnostic["control_admitted"] is True
    assert diagnostic["candidate_admitted"] is True
    assert diagnostic["candidate_nontrivial"] is False
    assert diagnostic["row_column_gauge_equivalent"] is True
    assert diagnostic["candidate_J_gain_bits"] == pytest.approx(0.0)
    assert diagnostic["construction_stop"] is False
    assert len(rank_phase["calls"]) == 2


def test_final_rank_failure_stops_only_after_the_sweep(monkeypatch):
    h0 = _fake_dense()
    pmf = probe.shape_pmf_grid()[0]["pmf"]
    onepass = alignment.scale_columns(h0, np.full(probe.N, 2))
    control = alignment.scale_columns(h0, np.full(probe.N, 3))
    edge_ran = []
    rank_calls = []

    monkeypatch.setattr(
        probe.search_depth, "build_candidate_pair",
        lambda *_args: (onepass.copy(), control.copy(), {
            "construction_stop": False, "deep_candidate_admitted": True,
        }),
    )

    def fake_edge(matrix, _pmf):
        np.testing.assert_array_equal(matrix, control)
        assert rank_calls == []
        edge_ran.append(True)
        j = float(alignment.marginal_score(matrix, pmf)[0])
        return {
            "matrix": matrix.copy(), "initial_J_bits": j, "J_bits": j,
            "accumulated_J_bits": j, "reference_drift_bits": 0.0,
            "J_change_bits": 0.0, "updates": [],
            "changed_edge_count": 0, "sweep_count": 1,
            "construction_stop": False, "failure_reason": "",
        }

    def rank_after_sweep(matrix):
        rank_calls.append(np.asarray(matrix).shape)
        return probe.M if len(rank_calls) == 1 else probe.M - 1

    monkeypatch.setattr(probe, "edge_sweep", fake_edge)
    monkeypatch.setattr(probe.d10, "gf32_row_rank", rank_after_sweep)
    control_matrix, candidate_matrix, diagnostic = probe.candidate_builder(
        h0, pmf, 17
    )
    assert edge_ran == [True]
    assert len(rank_calls) == 2
    np.testing.assert_array_equal(control_matrix, control)
    np.testing.assert_array_equal(candidate_matrix, control)
    assert diagnostic["candidate_rank"] == probe.M - 1
    assert diagnostic["candidate_admitted"] is False
    assert diagnostic["construction_stop"] is True


def test_full_row_column_gauge_witnesses_and_closing_edge_change():
    base = np.asarray([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.int64)
    expected_tree = [[0, 0], [0, 1], [0, 2], [1, 0], [2, 0]]
    identity = probe.gauge_diagnostics(base, base)
    assert identity["construction_stop"] is False
    assert identity["row_column_gauge_equivalent"] is True
    assert identity["cycle_class_changed"] is False
    assert identity["tree_edges"] == expected_tree
    assert len(identity["non_tree_residuals"]) == 4
    assert all(item["residual"] == 1
               for item in identity["non_tree_residuals"])

    transforms = [
        _column_scaled(base, [3, 5, 7]),
        _row_scaled(base, [2, 3, 5]),
        _row_scaled(_column_scaled(base, [3, 5, 7]), [2, 3, 5]),
    ]
    for transformed in transforms:
        diagnostic = probe.gauge_diagnostics(base, transformed)
        assert diagnostic["construction_stop"] is False
        assert diagnostic["row_column_gauge_equivalent"] is True
        assert diagnostic["cycle_class_changed"] is False
        assert diagnostic["tree_edges"] == expected_tree
        assert diagnostic["nonunit_residual_count"] == 0
        assert all(item["residual"] == 1
                   for item in diagnostic["non_tree_residuals"])

    changed = base.copy()
    changed[1, 1] = 2
    cycle = probe.gauge_diagnostics(base, changed)
    assert cycle["construction_stop"] is False
    assert cycle["row_column_gauge_equivalent"] is False
    assert cycle["cycle_class_changed"] is True
    assert cycle["tree_edges"] == expected_tree
    assert cycle["nonunit_residual_count"] == 1
    expected_ratio = probe._gf32_div(2, 5)
    assert cycle["witness"] == {
        "row": 1, "column": 1,
        "ratio": expected_ratio, "predicted": 1,
        "residual": expected_ratio,
    }


@pytest.mark.parametrize(
    ("control", "candidate", "reason"),
    [
        (np.asarray([[1, 2], [3, 4]]),
         np.asarray([[1, 0], [3, 4]]), "GAUGE_SUPPORT_MISMATCH"),
        (np.zeros((2, 2), dtype=np.int64),
         np.zeros((2, 2), dtype=np.int64), "GAUGE_ZERO_SUPPORT"),
        (np.asarray([[1, 0], [0, 2]]),
         np.asarray([[1, 0], [0, 2]]), "GAUGE_UNREACHED_SUPPORT_VERTEX"),
    ],
)
def test_gauge_diagnostic_stops_on_support_zero_or_disconnected(
        control, candidate, reason
):
    result = probe.gauge_diagnostics(control, candidate)
    assert result["construction_stop"] is True
    assert result["failure_reason"] == reason
    assert result["row_column_gauge_equivalent"] is None


@pytest.mark.parametrize(
    ("delta_by_graph", "cycle_indices", "control", "classification"),
    [
        # Four positive graphs and four changed-cycle graphs are independent
        # gates; only two graphs overlap, which must not add another gate.
        ([3, 3, 3, 3, 0, 0], {2, 3, 4, 5}, 90, "MECHANISM_SIGNAL"),
        ([3, 3, 3, 3, 0, 0], {2, 3, 4, 5}, 39, "MECHANISM_SIGNAL"),
        ([3, 3, 3, 3, 0, 0], {2, 3, 4, 5}, 153, "MECHANISM_SIGNAL"),
        ([3, 3, 3, 2, 0, 0], {0, 1, 2, 3}, 90,
         "NO_SUFFICIENT_SIGNAL"),  # Delta 11
        ([4, 4, 4, 0, 0, 0], {0, 1, 2, 3}, 90,
         "NO_SUFFICIENT_SIGNAL"),  # only three positive graphs
        ([3, 3, 3, 3, 0, 0], {0, 1, 2}, 90,
         "NO_SUFFICIENT_SIGNAL"),  # only three changed-cycle graphs
        ([3, 3, 3, 3, 0, 0], {0, 1, 2, 3}, 38,
         "CONTROL_RANGE_UNINFORMATIVE"),
        ([3, 3, 3, 3, 0, 0], {0, 1, 2, 3}, 154,
         "CONTROL_RANGE_UNINFORMATIVE"),
    ],
)
def test_complete_screen_separates_delta_positive_control_and_cycle_gates(
        delta_by_graph, cycle_indices, control, classification
):
    quotient, remainder = divmod(control, len(probe.GRAPH_SEEDS))
    controls = [quotient + (index < remainder)
                for index in range(len(probe.GRAPH_SEEDS))]
    summary = _summary(controls, delta_by_graph, cycle_indices)
    assert summary["holdout_complete"] is True
    assert summary["holdout_pairs_completed"] == 192
    assert summary["control_exact"] == control
    assert summary["candidate_exact"] == control + sum(delta_by_graph)
    assert summary["delta"] == sum(delta_by_graph)
    assert summary["classification"] == classification
    assert summary["syndrome_bits_per_attempt"] == 260
    assert summary["tag_bits"] == 0
    assert summary["verification_status"] == "NOT_IMPLEMENTED"
    assert summary["undetected_status"] == "NOT_MEASURED"
    assert summary["FER"] is summary["f_eff"] is summary["SKR"] is None
    assert sum(summary["paired_states"].values()) == 192
    assert summary["syndrome_consistent_wrong_rows"] == 1
    assert summary["syndrome_consistent_wrong_by_arm"] == {
        "control": 1, "candidate": 0,
    }
    assert summary["cycle_changed_graphs"] == len(cycle_indices)
    assert [summary["delta_by_graph"][str(seed)]["delta_g"]
            for seed in probe.GRAPH_SEEDS] == delta_by_graph
    assert [summary["delta_by_graph"][str(seed)]["cycle_class_changed"]
            for seed in probe.GRAPH_SEEDS] == [
                index in cycle_indices for index in range(6)
            ]
    for index, seed in enumerate(probe.GRAPH_SEEDS):
        row = summary["delta_by_graph"][str(seed)]
        assert row["positive_delta_without_cycle_change"] is bool(
            delta_by_graph[index] > 0 and index not in cycle_indices
        )
    assert summary["integrity_violations"] == 0
    assert summary["resource_violations"] == 0
    assert summary["authorization_violations"] == 0


def test_full_fake_batch_pairs_shared_truth_own_syndromes_and_unchanged_graphs(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path)
    _, holdouts = probe.seed_plan()
    key_by_seed = {seed: (graph, stream, frame)
                   for graph, stream, frame, seed in holdouts}
    state = {"key": None, "truth": None}
    calls = []
    graph_calls = []
    candidate_calls = []

    def graph_builder(seed):
        graph_calls.append(int(seed))
        return _fake_graph(seed)

    def sample_error(seed, pmf, width=probe.N):
        state["key"] = key_by_seed[int(seed)]
        truth = (np.arange(width, dtype=np.int64) + int(seed) % 32) % 32
        state["truth"] = truth.copy()
        return truth

    def decoder(dense, prior, syndrome):
        calls.append({
            "key": state["key"], "dense": np.asarray(dense).copy(),
            "prior": np.asarray(prior).copy(),
            "syndrome": np.asarray(syndrome).copy(),
            "truth": state["truth"].copy(),
        })
        return SimpleNamespace(
            x_hat=state["truth"].copy(), syndrome_ok=True,
            iterations=1, status="fake_exact",
        )

    def candidate_builder(dense, pmf, graph_seed):
        candidate_calls.append(int(graph_seed))
        return _fake_batch_candidate(dense, pmf, graph_seed)

    monkeypatch.setattr(probe.prior_runner, "sample_error", sample_error)
    # Tests always supply both fake construction and fake decoding seams.
    result = probe.execute_batch(
        out_root=out_root, decode_fn=decoder, graph_builder=graph_builder,
        candidate_builder=candidate_builder, repo_root=repo,
        now=lambda: 0.0, rss_fn=lambda: 0,
    )
    assert graph_calls == list(probe.GRAPH_SEEDS)
    assert candidate_calls == list(probe.GRAPH_SEEDS)
    assert len(calls) == probe.MAX_CALLS == 384
    assert result["attempted_decoder_calls"] == 384
    assert result["attempted_frame_rows"] == 384
    assert result["attempted_call_counts"] == {
        "pilot": 0, "holdout": 384, "total": 384,
    }
    assert result["actual_syndrome_disclosure_bits"] == 384 * 260
    assert result["holdout_complete"] is True
    assert result["holdout_pairs_completed"] == 192
    assert result["resource_violations"] == result["integrity_violations"] == 0

    paired = defaultdict(list)
    for call in calls:
        paired[call["key"]].append(call)
        np.testing.assert_array_equal(
            call["syndrome"], layout.gf32_syndrome(
                call["dense"], call["truth"]
            )
        )
    different_arm_syndromes = 0
    for (graph, stream, frame), arms in paired.items():
        assert len(arms) == 2
        assert [arm["key"] for arm in arms] == [(graph, stream, frame)] * 2
        np.testing.assert_array_equal(arms[0]["truth"], arms[1]["truth"])
        np.testing.assert_array_equal(arms[0]["prior"], arms[1]["prior"])
        expected_order = probe.arm_order(frame)
        # CSV output is the authoritative arm label for each paired call.
        assert len(expected_order) == 2
        if not np.array_equal(arms[0]["dense"], arms[1]["dense"]):
            different_arm_syndromes += int(
                not np.array_equal(arms[0]["syndrome"], arms[1]["syndrome"])
            )
    assert different_arm_syndromes > 0

    root = repo / out_root
    assert sorted(path.name for path in root.iterdir()) == [
        "EXPLORATION_LOG.md", "frame_records.csv", "manifest.json",
        "summary.json",
    ]
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["batch_uuid"] == probe.BATCH_UUID
    assert manifest["seed_namespace"] == probe.SEED_PREFIX
    assert manifest["seed_plan_counts"] == {"pilot": 0, "holdout_pairs": 192}
    with (root / "frame_records.csv").open(newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = set(reader.fieldnames or [])
    assert len(rows) == 384
    assert not fields.intersection({"truth", "prior", "error", "input"})
    recorded_order = defaultdict(list)
    for row in rows:
        key = (int(row["graph_seed"]), int(row["stream"]), int(row["frame"]))
        recorded_order[key].append((int(row["call_index"]), row["arm"]))
    for (graph, stream, frame), attempts in recorded_order.items():
        arms = [arm for _, arm in sorted(attempts)]
        assert tuple(arms) == probe.arm_order(frame)
    for seed in probe.GRAPH_SEEDS[4:]:
        graph_summary = result["delta_by_graph"][str(seed)]
        assert graph_summary["control_attempts"] == 32
        assert graph_summary["candidate_attempts"] == 32
        assert graph_summary["completed_pairs"] == 32
        diagnostic = next(item for item in result["search_diagnostics"]
                          if item["graph_seed"] == seed)
        assert diagnostic["candidate_nontrivial"] is False
    for index, seed in enumerate(probe.GRAPH_SEEDS):
        diagnostic = next(item for item in result["search_diagnostics"]
                          if item["graph_seed"] == seed)
        gauge = diagnostic["gauge"]
        assert len(gauge["tree_edges"]) == probe.M + probe.N - 1 == 179
        assert len(gauge["non_tree_residuals"]) == (
            probe.EDGE_COUNT - (probe.M + probe.N - 1)
        ) == 77
        assert gauge["cycle_class_changed"] is (index < 4)
        if index < 4:
            nonunit = [item for item in gauge["non_tree_residuals"]
                       if item["residual"] != 1]
            assert len(nonunit) == gauge["nonunit_residual_count"] == 1
            assert gauge["witness"] == nonunit[0]


def test_globally_unchanged_candidate_still_runs_all_holdout_pairs(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path)
    candidate_seeds = []
    decoder_calls = []
    monkeypatch.setattr(
        probe.prior_runner, "sample_error",
        lambda _seed, _pmf, width=probe.N: np.zeros(width, dtype=np.int64),
    )

    def candidate_builder(dense, _pmf, graph_seed):
        candidate_seeds.append(int(graph_seed))
        control = np.asarray(dense, dtype=np.int64).copy()
        gauge = probe.gauge_diagnostics(control, control)
        return control, control.copy(), {
            "graph_seed": int(graph_seed), "control_admitted": True,
            "candidate_admitted": True, "construction_stop": False,
            "candidate_nontrivial": False,
            "row_column_gauge_equivalent": True,
            "cycle_class_changed": False, "nonunit_residual_count": 0,
            "gauge_witness": None, "gauge": gauge,
        }

    def decoder(_dense, _prior, _syndrome):
        decoder_calls.append(1)
        return SimpleNamespace(
            x_hat=np.zeros(probe.N, dtype=np.int64), syndrome_ok=True,
            iterations=1, status="fake_exact",
        )

    result = probe.execute_batch(
        out_root=out_root, decode_fn=decoder, graph_builder=_fake_graph,
        candidate_builder=candidate_builder, repo_root=repo,
        now=lambda: 0.0, rss_fn=lambda: 0,
    )
    assert candidate_seeds == list(probe.GRAPH_SEEDS)
    assert len(decoder_calls) == 384
    assert result["attempted_decoder_calls"] == 384
    assert result["holdout_pairs_completed"] == 192
    assert result["holdout_complete"] is True
    assert result["candidate_exact"] == result["control_exact"] == 192
    assert result["delta"] == 0
    assert result["cycle_changed_graphs"] == 0


def _assert_partial_unknowns(result: dict) -> None:
    assert result["holdout_complete"] is False
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    assert result["delta"] is None
    assert result["paired_states"] is None
    assert set(result["delta_by_graph"]) == {
        str(seed) for seed in probe.GRAPH_SEEDS
    }
    for graph in result["delta_by_graph"].values():
        assert graph["control_exact"] is None
        assert graph["candidate_exact"] is None
        assert graph["delta_g"] is None


def test_graph_and_candidate_stop_keep_comparison_unknown(tmp_path, monkeypatch):
    repo, out_root = _test_repo(tmp_path / "graph")
    calls = []

    def bad_graph(seed):
        graph = _fake_graph(seed)
        graph["dense"][0, 0] = 0
        return graph

    graph_result = probe.execute_batch(
        out_root=out_root,
        decode_fn=lambda *_args: pytest.fail("bad graph reached decoder"),
        graph_builder=bad_graph,
        candidate_builder=lambda *_args: pytest.fail(
            "bad graph reached candidate builder"
        ),
        repo_root=repo, now=lambda: 0.0, rss_fn=lambda: 0,
    )
    assert graph_result["terminal_status"] == "GRAPH_PREFLIGHT_FAILED"
    assert graph_result["attempted_decoder_calls"] == 0
    _assert_partial_unknowns(graph_result)

    repo2, out_root2 = _test_repo(tmp_path / "candidate")

    def failed_candidate(dense, _pmf, graph_seed):
        return np.asarray(dense).copy(), None, {
            "graph_seed": int(graph_seed), "control_admitted": True,
            "candidate_admitted": False, "construction_stop": False,
            "failure_reason": "FAKE_EDGE_ADMISSION_STOP",
        }

    candidate_result = probe.execute_batch(
        out_root=out_root2,
        decode_fn=lambda *_args: calls.append(1),
        graph_builder=_fake_graph, candidate_builder=failed_candidate,
        repo_root=repo2, now=lambda: 0.0, rss_fn=lambda: 0,
    )
    assert candidate_result["terminal_status"] in {
        "CANDIDATE_CONSTRUCTION_STOP", "EDGE_CANDIDATE_ADMISSION_STOP",
        "NO_EDGE_CANDIDATE",
    }
    assert candidate_result["attempted_decoder_calls"] == 0
    assert calls == []
    _assert_partial_unknowns(candidate_result)


def test_partial_pair_plus_orphan_retains_rows_and_masks_aggregates(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path)
    _, holdouts = probe.seed_plan()
    key_by_seed = {seed: (graph, stream, frame)
                   for graph, stream, frame, seed in holdouts}
    current = {"key": None, "truth": None}
    decoder_calls = []

    def sample_error(seed, _pmf, width=probe.N):
        current["key"] = key_by_seed[int(seed)]
        current["truth"] = np.zeros(width, dtype=np.int64)
        return current["truth"].copy()

    def decoder(_dense, _prior, _syndrome):
        decoder_calls.append(1)
        return SimpleNamespace(
            x_hat=current["truth"].copy(), syndrome_ok=True,
            iterations=1, status="fake",
        )

    original_stop = probe._resource_stop

    def stop_after_orphan(started, now, rss_fn):
        if len(decoder_calls) >= 3:
            return "total_wall_cap_before_next_call"
        return original_stop(started, now, rss_fn)

    monkeypatch.setattr(probe.prior_runner, "sample_error", sample_error)
    monkeypatch.setattr(probe, "_resource_stop", stop_after_orphan)
    result = probe.execute_batch(
        out_root=out_root, decode_fn=decoder, graph_builder=_fake_graph,
        candidate_builder=_fake_batch_candidate, repo_root=repo,
        now=lambda: 0.0, rss_fn=lambda: 0,
    )
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert result["attempted_decoder_calls"] == 3
    assert result["attempted_frame_rows"] == 3
    assert result["attempted_call_counts"] == {
        "pilot": 0, "holdout": 3, "total": 3,
    }
    assert result["holdout_pairs_completed"] == 1
    assert result["holdout_complete"] is False
    _assert_partial_unknowns(result)
    first_graph = result["delta_by_graph"][str(probe.GRAPH_SEEDS[0])]
    assert first_graph["completed_pairs"] == 1
    assert first_graph["control_attempts"] + first_graph["candidate_attempts"] == 3
    root = repo / out_root
    with (root / "frame_records.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 3
    assert {row["phase"] for row in rows} == {"holdout"}


@pytest.mark.parametrize(
    ("case", "expected_marker"),
    [
        ("call_wall_exception", "decoder_call_wall_cap_after_return"),
        ("total_wall", "total_wall_cap_after_call"),
        ("rss_exception", "rss_cap_after_call"),
    ],
)
def test_postreturn_resource_caps_preserve_attempt_and_stop(
        tmp_path, monkeypatch, case, expected_marker
):
    repo, out_root = _test_repo(tmp_path)
    clock = {"value": 0.0}
    rss = {"value": 0}
    decoder_calls = []
    monkeypatch.setattr(
        probe.prior_runner, "sample_error",
        lambda _seed, _pmf, width=probe.N: np.zeros(width, dtype=np.int64),
    )

    def graph_builder(seed):
        graph = _fake_graph(seed)
        if case == "total_wall" and seed == probe.GRAPH_SEEDS[-1]:
            clock["value"] = probe.WALL_CAP_S - 10.0
        return graph

    def decoder(_dense, _prior, _syndrome):
        decoder_calls.append(1)
        if case == "call_wall_exception":
            clock["value"] = probe.CALL_CAP_S + 1.0
            raise RuntimeError("fake_call_overrun")
        if case == "rss_exception":
            rss["value"] = probe.RSS_CAP_BYTES + 1
            raise RuntimeError("fake_rss_overrun")
        clock["value"] += 20.0
        return SimpleNamespace(
            x_hat=np.zeros(probe.N, dtype=np.int64), syndrome_ok=True,
            iterations=1, status="fake",
        )

    result = probe.execute_batch(
        out_root=out_root, decode_fn=decoder, graph_builder=graph_builder,
        candidate_builder=_fake_batch_candidate, repo_root=repo,
        now=lambda: clock["value"], rss_fn=lambda: rss["value"],
    )
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert len(decoder_calls) == result["attempted_decoder_calls"] == 1
    assert result["attempted_call_counts"]["holdout"] == 1
    assert result["resource_violations"] == 1
    assert result["holdout_pairs_completed"] == 0
    _assert_partial_unknowns(result)
    root = repo / out_root
    with (root / "frame_records.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert expected_marker in rows[0]["status"]
    assert expected_marker in result["stop_reason"]
    if case != "total_wall":
        assert "decoder_exception:RuntimeError" in rows[0]["status"]
        assert "resource_abort:" in rows[0]["status"]
    if case == "total_wall":
        assert float(rows[0]["wall_s"]) == pytest.approx(20.0)
        assert "decoder_call_wall_cap_after_return" not in rows[0]["status"]
