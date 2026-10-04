"""Fake-only/tiny tests for the source-aware GF(32) label EXPLORE probe."""
from __future__ import annotations

import math
import csv
import inspect
import json
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli.probes_closed import nbldpc_gf32_source_label_probe as probe
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout


def _mul(a: int, b: int) -> int:
    return int(layout.gf32_mul(int(a), int(b)))


def _inv(a: int) -> int:
    return int(probe.census._gf32_inverse(int(a)))


def _div(a: int, b: int) -> int:
    return _mul(a, _inv(b))


def _fake_dense() -> np.ndarray:
    """Deterministic 52x128, E=256 connected-support fake graph."""
    row_degrees = [4] * 4 + [5] * 48
    dense = np.zeros((probe.M, probe.N), dtype=np.int64)
    column = 0
    for row in range(probe.M):
        next_row = (row + 1) % probe.M
        dense[row, column] = 1
        dense[next_row, column] = 2
        column += 1
    residual = [degree - 2 for degree in row_degrees]
    sockets = [row for layer in range(max(residual))
               for row, count in enumerate(residual) if count > layer]
    assert len(sockets) == 2 * (probe.N - probe.M)
    for index in range(0, len(sockets), 2):
        first, second = sockets[index:index + 2]
        assert first != second
        dense[first, column] = 1
        dense[second, column] = 2
        column += 1
    assert column == probe.N
    assert int(np.count_nonzero(dense)) == probe.EDGE_COUNT
    return dense


def _fake_graph(seed: int) -> dict:
    return {"graph_seed": int(seed), "dense": _fake_dense()}


def _test_repo(path: Path) -> tuple[Path, Path]:
    repo = path / "repo"
    (repo / "workspace").mkdir(parents=True)
    return repo, probe.OUT_ROOT_RELATIVE


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _write_header_csv(path: Path, columns) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        csv.DictWriter(stream, fieldnames=columns).writeheader()


def _fake_cycle(seed: int) -> dict:
    # Columns 0 and 52 form a unit 2-cycle in the fake control graph.
    return {"graph_seed": int(seed), "ell": 2,
            "cycle_key": [0, 52, 1, 53],
            "rows": [0, 1], "variables": [0, 52]}


def _fake_control_builder(dense, _pmf, _seed):
    matrix = np.asarray(dense, dtype=np.int64).copy()
    return matrix.copy(), matrix, {
        "deep_candidate_admitted": True, "construction_stop": False,
    }


def _fake_preflight(graph, seed):
    return True, {"graph_seed": int(seed), "admitted": True,
                  "fake_only": True}


def _fake_cycle_loader(_repo_root, controls):
    return {int(seed): [_fake_cycle(seed)] for seed in controls}


def _fake_candidate_builder(control, cycles, b_values, *, checkpoint=None,
                            counters=None, graph_seed=-1):
    matrix = np.asarray(control, dtype=np.int64).copy()
    graph_index = probe.GRAPH_SEEDS.index(int(graph_seed))
    if graph_index < 4:
        matrix[0, 0] = 3
    before, _ = probe._full_reference(control, cycles, b_values)
    after, _ = probe._full_reference(matrix, cycles, b_values)
    return {
        "matrix": matrix, "graph_seed": int(graph_seed),
        "F_reduction": float(before - after),
        "construction_stop": False, "failure_reason": "",
        "coordinate_count": int(np.count_nonzero(control)),
        "counters": dict(counters or {}),
    }


def _summary_fixture(control_by_graph, delta_by_graph, reduced_graphs):
    _, holdouts = probe.seed_plan()
    rows, pairs = [], []
    for graph_seed, stream, frame, seed in holdouts:
        graph_index = probe.GRAPH_SEEDS.index(graph_seed)
        slot = stream * probe.HOLDOUT_FRAMES_PER_STREAM + frame
        outcomes = {
            "control": slot < control_by_graph[graph_index],
            "candidate": slot < (control_by_graph[graph_index]
                                 + delta_by_graph[graph_index]),
        }
        for arm in probe.arm_order(frame):
            exact = outcomes[arm]
            wrong = (arm == "control" and graph_index == 0 and slot == 7
                     and not exact)
            rows.append({
                "phase": "holdout", "arm": arm,
                "graph_seed": int(graph_seed), "exact": bool(exact),
                "syndrome_accept": bool(exact or wrong),
                "syndrome_consistent_wrong": bool(wrong), "status": "fake",
                "wall_s": 0.0, "iterations": 1,
            })
        pairs.append({
            "graph_seed": int(graph_seed),
            "control_success": bool(outcomes["control"]),
            "candidate_success": bool(outcomes["candidate"]),
        })
    diagnostics = [
        {"graph_seed": int(seed),
         "F_reduction": 0.1 if index < reduced_graphs else 0.0}
        for index, seed in enumerate(probe.GRAPH_SEEDS)
    ]
    return probe._summarize(rows, pairs, diagnostics, "")


def _tiny_cycle_2() -> tuple[np.ndarray, dict]:
    # The local unit witness is [1, 7]; changing the first absolute label
    # away from 7 breaks the unit product and changes W to the nonunit null.
    matrix = np.asarray([[7, 1], [1, _inv(7)]], dtype=np.int64)
    cycle = {
        "graph_seed": 17, "ell": 2, "cycle_key": [0, 2, 1, 3],
        "rows": [0, 1], "variables": [0, 1],
    }
    return matrix, cycle


def _tiny_zero_overlap_cycle() -> tuple[np.ndarray, dict]:
    # This four-symbol unit witness has W=0 under the frozen sparse PMF.
    matrix = np.zeros((4, 4), dtype=np.int64)
    matrix[0, 0] = 1
    matrix[1, 0] = 2
    matrix[1, 1] = 1
    matrix[2, 1] = 3
    matrix[2, 2] = 2
    matrix[3, 2] = 5
    matrix[3, 3] = 3
    numerator_product = _mul(_mul(matrix[0, 0], matrix[1, 1]),
                             _mul(matrix[2, 2], matrix[3, 3]))
    denominator_product = _mul(_mul(matrix[1, 0], matrix[2, 1]),
                               matrix[3, 2])
    matrix[0, 3] = _div(numerator_product, denominator_product)
    cycle = {
        "graph_seed": 17, "ell": 4, "cycle_key": [0, 4, 1, 5, 2, 6, 3, 7],
        "rows": [0, 1, 2, 3], "variables": [0, 1, 2, 3],
    }
    return matrix, cycle


def test_tiny_cycle_w_matches_direct_31_scalar_sum_and_is_orbit_invariant():
    matrix, cycle = _tiny_cycle_2()
    b_values = probe.source_overlap.bhattacharyya_values(probe.source_pmf())
    state = probe._cycle_state(matrix, cycle, b_values)

    assert state["product"] == 1
    assert state["unit"] is True
    assert state["witness_values"] == [1, 7]
    expected = math.fsum(
        float(b_values[_mul(scalar, 1)])
        * float(b_values[_mul(scalar, 7)])
        for scalar in range(1, 32)
    )
    assert state["W"] == pytest.approx(expected, abs=1e-15)
    assert state["source_status"] == "POSITIVE_OVERLAP"

    orbit = probe.source_overlap.normalize_orbit([0, 1], [1, 7])
    scaled_orbit = probe.source_overlap.normalize_orbit(
        [0, 1], [_mul(11, 1), _mul(11, 7)])
    assert scaled_orbit == orbit
    scaled = probe.source_overlap.overlap_for_orbit(scaled_orbit, b_values)
    assert scaled["W"] == pytest.approx(state["W"], abs=1e-15)


def test_unit_zero_overlap_is_distinct_from_nonunit_null():
    matrix, cycle = _tiny_zero_overlap_cycle()
    b_values = probe.source_overlap.bhattacharyya_values(probe.source_pmf())
    state = probe._cycle_state(matrix, cycle, b_values)
    assert state["product"] == 1
    assert state["witness_values"] == [1, 2, 3, 5]
    assert state["unit"] is True
    assert state["W"] == 0.0
    assert state["source_status"] == "ZERO_SOURCE_OVERLAP"
    assert probe._cycle_cost(state) == 0.0

    nonunit = matrix.copy()
    nonunit[0, 0] = _mul(2, int(nonunit[0, 0]))
    nonunit_state = probe._cycle_state(nonunit, cycle, b_values)
    assert nonunit_state["product"] != 1
    assert nonunit_state["unit"] is False
    assert nonunit_state["W"] is None
    assert nonunit_state["source_status"] == "NONUNIT_NO_LOCAL_CODEWORD"
    assert probe._cycle_cost(nonunit_state) == 0.0


def test_coordinate_pass_scans_all_31_absolute_labels_and_keeps_counters():
    matrix, cycle = _tiny_cycle_2()
    b_values = probe.source_overlap.bhattacharyya_values(probe.source_pmf())

    def stop_after_first_coordinate(stage, row, column):
        if stage == "after_coordinate" and (row, column) == (0, 0):
            return "FAKE_STOP_AFTER_FIRST_COORDINATE"
        return None

    result = probe.coordinate_pass(
        matrix, [cycle], b_values, graph_seed=17,
        checkpoint=stop_after_first_coordinate,
    )

    assert result["construction_stop"] is True
    assert result["failure_reason"] == "FAKE_STOP_AFTER_FIRST_COORDINATE"
    assert result["graph_seed"] == 17
    assert len(result["coordinate_updates"]) == 1
    update = result["coordinate_updates"][0]
    assert (update["row"], update["column"]) == (0, 0)
    assert update["old_beta"] == 7
    assert update["chosen_beta"] == 1  # absolute beta, not a multiplier
    assert update["committed"] is True
    trials = update["trial_F_by_beta"]
    assert [item["beta"] for item in trials] == list(range(1, 32))
    for item in trials:
        trial_matrix = matrix.copy()
        trial_matrix[0, 0] = item["beta"]
        expected_state = probe._cycle_state(trial_matrix, cycle, b_values)
        assert item["F"] == pytest.approx(
            probe._cycle_cost(expected_state), abs=1e-15)
    np.testing.assert_array_equal(result["matrix"][0, 0], 1)
    assert result["counters"] == {
        "label_trials": 31,
        "affected_cycle_evaluations": 31,
        "reference_cycle_evaluations": 2,
    }


def test_absolute_beta_ties_retain_current_then_choose_smallest():
    assert probe._choose_beta(
        {7: probe.TIE_TOL, 5: probe.TIE_TOL / 2, 3: 0.0}, current=7
    ) == 7
    assert probe._choose_beta(
        {9: 1.1 * probe.TIE_TOL, 5: probe.TIE_TOL / 2, 3: 0.0},
        current=9,
    ) == 3


def test_empty_cycle_pass_checks_each_edge_but_makes_no_change():
    matrix = np.asarray([[7, 0, 0], [0, 2, 3]], dtype=np.int64)
    result = probe.coordinate_pass(matrix, [], probe.source_overlap.bhattacharyya_values(
        probe.source_pmf()), graph_seed=41)
    np.testing.assert_array_equal(result["matrix"], matrix)
    assert result["graph_seed"] == 41
    assert result["construction_stop"] is False
    assert result["changed_edges"] == 0
    assert result["coordinate_count"] == 3
    assert result["counters"] == {
        "label_trials": 3 * 31,
        "affected_cycle_evaluations": 0,
        "reference_cycle_evaluations": 0,
    }
    assert all(update["chosen_beta"] == update["old_beta"]
               for update in result["coordinate_updates"])


@pytest.mark.parametrize(
    ("drift", "expected_reason"),
    [
        (probe.REFERENCE_TOL, "FAKE_STOP_AFTER_REFERENCE_BOUNDARY"),
        (2 * probe.REFERENCE_TOL, "FULL_REFERENCE_DRIFT"),
    ],
)
def test_reference_drift_tolerance_boundary_and_no_rollback(
        monkeypatch, drift, expected_reason
):
    matrix, cycle = _tiny_cycle_2()
    b_values = probe.source_overlap.bhattacharyya_values(probe.source_pmf())
    original = probe._full_reference
    calls = {"count": 0}

    def perturbed_reference(candidate, cycles, actual_b, *, verify_rank=False):
        value, states = original(candidate, cycles, actual_b,
                                 verify_rank=verify_rank)
        calls["count"] += 1
        if calls["count"] == 2:
            value += drift
        return value, states

    monkeypatch.setattr(probe, "_full_reference", perturbed_reference)

    def stop_on_boundary(stage, row, column):
        if stage == "after_coordinate" and (row, column) == (0, 0):
            return "FAKE_STOP_AFTER_REFERENCE_BOUNDARY"
        return None

    result = probe.coordinate_pass(
        matrix, [cycle], b_values,
        checkpoint=stop_on_boundary, graph_seed=17,
    )
    update = result["coordinate_updates"][0]
    assert calls["count"] == 2
    assert update["reference_drift"] == pytest.approx(drift, abs=1e-15)
    assert result["matrix"][0, 0] == 1  # committed choice is not rolled back
    if drift == probe.REFERENCE_TOL:
        assert result["failure_reason"] == expected_reason
        assert result["counters"]["reference_cycle_evaluations"] == 2
    else:
        assert result["failure_reason"] == expected_reason
        assert result["construction_stop"] is True
        assert result["counters"]["reference_cycle_evaluations"] == 2


def test_fully_fake_batch_pairs_shared_error_and_own_syndromes(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path)
    _, holdouts = probe.seed_plan()
    key_by_seed = {seed: (graph, stream, frame)
                   for graph, stream, frame, seed in holdouts}
    state = {"key": None, "truth": None}
    decoder_calls = []
    control_by_graph = [7, 7, 7, 6, 6, 6]
    delta_by_graph = [3, 3, 3, 3, 0, 0]

    def sample_error(seed, _pmf, width=probe.N):
        state["key"] = key_by_seed[int(seed)]
        truth = np.zeros(width, dtype=np.int64)
        truth[11] = int(seed) % 31 + 1
        state["truth"] = truth
        return truth.copy()

    def make_decoder(arm):
        def decoder(dense, prior, syndrome):
            graph, stream, frame = state["key"]
            graph_index = probe.GRAPH_SEEDS.index(graph)
            slot = stream * probe.HOLDOUT_FRAMES_PER_STREAM + frame
            threshold = control_by_graph[graph_index]
            if arm == "candidate":
                threshold += delta_by_graph[graph_index]
            truth = state["truth"]
            success = slot < threshold
            wrong_control = (arm == "control"
                             and graph_index == 0 and slot == 7)
            estimate = truth.copy()
            if wrong_control:
                # These two equal control columns cancel in GF(32), while the
                # edge-label candidate changes H[0,0], so the wrong word is
                # syndrome-consistent only for the control arm.
                estimate[0] ^= 1
                estimate[52] ^= 1
            elif not success:
                estimate[127] ^= 1
            syndrome_ok = bool(layout.syndrome_ok(dense, estimate, syndrome))
            decoder_calls.append({
                "arm": arm, "key": state["key"],
                "dense": np.asarray(dense).copy(),
                "prior": np.asarray(prior).copy(),
                "syndrome": np.asarray(syndrome).copy(),
                "truth": truth.copy(), "estimate": estimate.copy(),
                "syndrome_ok": syndrome_ok,
            })
            return SimpleNamespace(
                x_hat=estimate, syndrome_ok=syndrome_ok, iterations=1,
                status="fake_wrong" if wrong_control else "fake",
            )
        return decoder

    monkeypatch.setattr(probe.prior_runner, "sample_error", sample_error)
    # Rank is a final structural gate; the fake 52x128 support is not sent to
    # the production rank implementation or any production constructor.
    monkeypatch.setattr(probe.d10, "gf32_row_rank", lambda _matrix: probe.M)
    result = probe.execute_batch(
        out_root=out_root,
        decode_fns={"control": make_decoder("control"),
                    "candidate": make_decoder("candidate")},
        graph_builder=_fake_graph,
        graph_preflight_fn=_fake_preflight,
        control_builder=_fake_control_builder,
        cycle_loader=_fake_cycle_loader,
        candidate_builder=_fake_candidate_builder,
        repo_root=repo, now=lambda: 0.0, rss_fn=lambda: 0,
    )

    assert result["classification"] == "MECHANISM_SIGNAL"
    assert result["terminal_status"] == "MECHANISM_SIGNAL"
    assert result["holdout_complete"] is True
    assert result["holdout_pairs_completed"] == 192
    assert result["attempted_decoder_calls"] == 384
    assert result["attempted_frame_rows"] == 384
    assert result["actual_syndrome_disclosure_bits"] == 384 * 260
    assert result["control_exact"] == 39
    assert result["candidate_exact"] == 51
    assert result["delta"] == 12
    assert result["positive_graphs"] == 4
    assert result["source_objective_reduced_graphs"] == 4
    assert result["integrity_violations"] == result["resource_violations"] == 0
    assert result["authorization_violations"] == result["tag_bits"] == 0
    assert result["verification_status"] == "NOT_IMPLEMENTED"
    assert result["undetected_status"] == "NOT_MEASURED"
    assert result["FER"] is result["f_eff"] is result["SKR"] is None
    assert len(decoder_calls) == 384

    paired = defaultdict(list)
    for call in decoder_calls:
        paired[call["key"]].append(call)
        np.testing.assert_array_equal(
            call["syndrome"],
            layout.gf32_syndrome(call["dense"], call["truth"]))
    for key, arms in paired.items():
        graph, stream, frame = key
        assert len(arms) == 2
        assert [item["arm"] for item in arms] == list(probe.arm_order(frame))
        np.testing.assert_array_equal(arms[0]["truth"], arms[1]["truth"])
        np.testing.assert_array_equal(arms[0]["prior"], arms[1]["prior"])
        for item in arms:
            assert bool(layout.syndrome_ok(
                item["dense"], item["estimate"], item["syndrome"])) \
                is item["syndrome_ok"]
    assert result["syndrome_consistent_wrong_rows"] == 1
    assert result["syndrome_consistent_wrong_by_arm"] == {
        "control": 1, "candidate": 0,
    }
    assert [result["delta_by_graph"][str(seed)]["delta_g"]
            for seed in probe.GRAPH_SEEDS] == [3, 3, 3, 3, 0, 0]
    assert all(result["source_objective_reductions_by_graph"][str(seed)]
               > probe.TIE_TOL for seed in probe.GRAPH_SEEDS[:4])
    assert all(result["source_objective_reductions_by_graph"][str(seed)]
               == 0.0 for seed in probe.GRAPH_SEEDS[4:])

    root = repo / out_root
    assert sorted(path.name for path in root.iterdir()) == [
        "EXPLORATION_LOG.md", "frame_records.csv", "manifest.json",
        "summary.json",
    ]
    with (root / "frame_records.csv").open(newline="") as stream:
        reader = csv.DictReader(stream)
        saved = list(reader)
        fields = set(reader.fieldnames or [])
    assert len(saved) == 384
    assert not fields.intersection({"truth", "prior", "error", "conditional"})
    by_pair = defaultdict(list)
    for row in saved:
        by_pair[(int(row["graph_seed"]), int(row["stream"]),
                 int(row["frame"]))].append(row)
    for (*_, frame), rows in by_pair.items():
        rows.sort(key=lambda row: int(row["call_index"]))
        assert tuple(row["arm"] for row in rows) == probe.arm_order(frame)
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["batch_uuid"] == probe.BATCH_UUID
    assert manifest["parent_batch_uuid"] == probe.PARENT_BATCH_UUID
    assert manifest["contract"] == probe.CONTRACT
    assert manifest["seed_namespace"] == probe.SEED_PREFIX
    assert manifest["seed_plan_counts"] == {"pilot": 0, "holdout_pairs": 192}
    saved_summary = json.loads((root / "summary.json").read_text())
    assert saved_summary["batch_uuid"] == probe.BATCH_UUID
    assert saved_summary["parent_batch_uuid"] == probe.PARENT_BATCH_UUID
    log = (root / "EXPLORATION_LOG.md").read_text()
    assert "source-aware edge-label R2" in log
    assert probe.BATCH_UUID in log and probe.PARENT_BATCH_UUID in log


@pytest.mark.parametrize(
    ("controls", "deltas", "reduced_graphs", "expected"),
    [
        ([7, 7, 7, 6, 6, 6], [3, 3, 3, 3, 0, 0], 4,
         "MECHANISM_SIGNAL"),
        ([7, 7, 7, 6, 6, 6], [3, 3, 3, 2, 0, 0], 4,
         "NO_SUFFICIENT_SIGNAL"),  # Δ=11
        ([7, 7, 7, 6, 6, 6], [4, 4, 4, 0, 0, 0], 4,
         "NO_SUFFICIENT_SIGNAL"),  # only 3 positive-Δ graphs
        ([7, 7, 7, 6, 6, 6], [3, 3, 3, 3, 0, 0], 3,
         "NO_SUFFICIENT_SIGNAL"),  # only 3 source-objective reductions
        ([5, 5, 5, 5, 5, 5], [3, 3, 3, 3, 0, 0], 4,
         "CONTROL_RANGE_UNINFORMATIVE"),
        ([30, 30, 30, 30, 30, 30], [1, 1, 0, 0, 0, 0], 4,
         "CONTROL_RANGE_UNINFORMATIVE"),
    ],
)
def test_complete_summary_enforces_frozen_screen_boundaries(
        controls, deltas, reduced_graphs, expected
):
    summary = _summary_fixture(controls, deltas, reduced_graphs)
    assert summary["classification"] == expected
    assert summary["holdout_complete"] is True
    assert summary["holdout_pairs_completed"] == 192
    assert summary["actual_syndrome_disclosure_bits"] == 384 * 260
    assert summary["control_exact"] == sum(controls)
    assert summary["candidate_exact"] == sum(controls) + sum(deltas)
    assert summary["delta"] == sum(deltas)
    assert summary["source_objective_reduced_graphs"] == reduced_graphs
    assert summary["FER"] is summary["f_eff"] is summary["SKR"] is None


def test_final_rank_failure_stops_before_any_decoder(tmp_path, monkeypatch):
    repo, out_root = _test_repo(tmp_path)
    rank_calls = []
    candidate_calls = []
    decoder_calls = []

    def fake_rank(_matrix):
        rank_calls.append(1)
        # Six control deep-H0D rank checks pass. The first final candidate
        # fails rank, proving rank is a final gate rather than search filter.
        return probe.M if len(rank_calls) <= 6 else probe.M - 1

    def candidate_builder(control, cycles, b_values, **kwargs):
        candidate_calls.append(kwargs["graph_seed"])
        return _fake_candidate_builder(
            control, cycles, b_values, **kwargs)

    monkeypatch.setattr(probe.d10, "gf32_row_rank", fake_rank)
    result = probe.execute_batch(
        out_root=out_root,
        decode_fns={"control": lambda *_: decoder_calls.append("control"),
                    "candidate": lambda *_: decoder_calls.append("candidate")},
        graph_builder=_fake_graph, graph_preflight_fn=_fake_preflight,
        control_builder=_fake_control_builder,
        cycle_loader=_fake_cycle_loader, candidate_builder=candidate_builder,
        repo_root=repo, now=lambda: 0.0, rss_fn=lambda: 0,
    )
    assert result["terminal_status"] == "CONSTRUCTION_STOP"
    assert "FINAL_SUPPORT_DEGREE_OR_RANK_GATE_FAILED" in result["stop_reason"]
    assert candidate_calls == [probe.GRAPH_SEEDS[0]]
    assert len(rank_calls) == 7
    assert decoder_calls == []
    assert result["attempted_decoder_calls"] == 0
    assert result["holdout_complete"] is False
    assert result["control_exact"] is result["candidate_exact"] is None


def test_partial_pair_and_orphan_keep_rows_but_mask_performance(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path)
    calls = []
    monkeypatch.setattr(
        probe.prior_runner, "sample_error",
        lambda _seed, _pmf, width=probe.N: np.zeros(width, dtype=np.int64),
    )

    def decoder(_dense, _prior, _syndrome):
        calls.append(1)
        return SimpleNamespace(x_hat=np.zeros(probe.N, dtype=np.int64),
                               syndrome_ok=True, iterations=1, status="fake")

    original_stop = probe._resource_stop

    def stop_before_fourth(started, now, rss_fn, call_count):
        if call_count >= 3:
            return "fake_stop_after_one_orphan_arm"
        return original_stop(started, now, rss_fn, call_count)

    monkeypatch.setattr(probe, "_resource_stop", stop_before_fourth)
    result = probe.execute_batch(
        out_root=out_root,
        decode_fns={"control": decoder, "candidate": decoder},
        graph_builder=_fake_graph, graph_preflight_fn=_fake_preflight,
        control_builder=_fake_control_builder,
        cycle_loader=_fake_cycle_loader, candidate_builder=_fake_candidate_builder,
        repo_root=repo, now=lambda: 0.0, rss_fn=lambda: 0,
    )
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert result["attempted_decoder_calls"] == len(calls) == 3
    assert result["attempted_frame_rows"] == 3
    assert result["holdout_pairs_completed"] == 1
    assert result["holdout_complete"] is False
    assert result["control_exact"] is result["candidate_exact"] is None
    assert result["delta"] is result["paired_states"] is None
    assert all(item["control_exact"] is None
               and item["candidate_exact"] is None
               and item["delta_g"] is None
               for item in result["delta_by_graph"].values())
    first = result["delta_by_graph"][str(probe.GRAPH_SEEDS[0])]
    assert first["completed_pairs"] == 1
    assert first["control_attempts"] + first["candidate_attempts"] == 3
    with (repo / out_root / "frame_records.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 3


@pytest.mark.parametrize(
    ("resource", "marker"),
    [("call_wall", "decoder_call_wall_cap_after_return"),
     ("total_wall", "total_wall_cap_after_call"),
     ("rss", "rss_cap_after_call")],
)
def test_postreturn_resource_exceptions_are_retained_and_stop(
        tmp_path, monkeypatch, resource, marker
):
    repo, out_root = _test_repo(tmp_path)
    clock = {"now": 0.0}
    rss = {"bytes": 0}
    calls = []
    monkeypatch.setattr(
        probe.prior_runner, "sample_error",
        lambda _seed, _pmf, width=probe.N: np.zeros(width, dtype=np.int64),
    )

    def graph_builder(seed):
        graph = _fake_graph(seed)
        if resource == "total_wall" and int(seed) == probe.GRAPH_SEEDS[-1]:
            clock["now"] = probe.WALL_CAP_S - 10.0
        return graph

    def decoder(_dense, _prior, _syndrome):
        calls.append(1)
        if resource == "call_wall":
            clock["now"] = probe.CALL_CAP_S + 1.0
        elif resource == "total_wall":
            clock["now"] += 20.0
        else:
            rss["bytes"] = probe.RSS_CAP_BYTES + 1
        raise RuntimeError("fake_resource_exception")

    result = probe.execute_batch(
        out_root=out_root,
        decode_fns={"control": decoder, "candidate": decoder},
        graph_builder=graph_builder, graph_preflight_fn=_fake_preflight,
        control_builder=_fake_control_builder,
        cycle_loader=_fake_cycle_loader, candidate_builder=_fake_candidate_builder,
        repo_root=repo, now=lambda: clock["now"],
        rss_fn=lambda: rss["bytes"],
    )
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert result["attempted_decoder_calls"] == len(calls) == 1
    assert result["resource_violations"] == 1
    assert result["holdout_pairs_completed"] == 0
    assert result["control_exact"] is result["candidate_exact"] is None
    with (repo / out_root / "frame_records.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert "decoder_exception:RuntimeError" in rows[0]["status"]
    assert "resource_abort:" in rows[0]["status"]
    assert marker in rows[0]["status"]
    assert marker in result["stop_reason"]


def test_dry_run_root_refusal_and_no_production_bindings(tmp_path, monkeypatch):
    repo, out_root = _test_repo(tmp_path)
    monkeypatch.setattr(probe, "_load_cycle_inventory", lambda *_: pytest.fail(
        "dry-run read a predecessor cycle inventory"))
    monkeypatch.setattr(probe.edge_runner, "build_profile_graph", lambda *_: pytest.fail(
        "dry-run built a production graph"))
    monkeypatch.setattr(probe.prior_runner, "_bind_production_decoder", lambda: pytest.fail(
        "dry-run bound a production decoder"))
    result = probe.dry_run(out_root, repo_root=repo)
    assert result["status"] == "DRY_RUN"
    assert result["writes"] == result["census_artifact_reads"] == 0
    assert result["cycle_rows_read"] == result["graph_construction_calls"] == 0
    assert result["decoder_calls"] == 0
    assert result["holdout_pairs"] == probe.HOLDOUT_PAIRS == 192
    assert result["holdout_calls"] == probe.MAX_CALLS == 384
    assert result["batch_uuid"] == probe.BATCH_UUID
    assert result["parent_batch_uuid"] == probe.PARENT_BATCH_UUID
    assert result["out_root"].endswith("gf32_source_label_r2_358c49ba")
    assert not (repo / out_root).exists()
    with pytest.raises(ValueError, match="frozen"):
        probe.dry_run("workspace/not-the-frozen-root", repo_root=repo)
    with pytest.raises(ValueError, match="frozen"):
        probe.validate_out_root(
            Path("workspace") / "gf32_source_label_f6fbf8cf",
            repo_root=repo,
        )

    (repo / out_root).mkdir()
    with pytest.raises(FileExistsError):
        probe.dry_run(out_root, repo_root=repo)


def test_actual_predecessor_loader_binds_six_graph_zero_cycle_artifacts(
        tmp_path, monkeypatch
):
    repo, _ = _test_repo(tmp_path)
    census_root = repo / probe.CENSUS_ROOT_RELATIVE
    overlap_root = repo / probe.OVERLAP_ROOT_RELATIVE
    census_root.mkdir(parents=True)
    overlap_root.mkdir(parents=True)

    graph_diags = [
        {"graph_seed": int(seed), "status": "ok", "admitted": True,
         "gf32_rank": probe.M}
        for seed in probe.GRAPH_SEEDS
    ]
    candidate_diags = [
        {"graph_seed": int(seed), "control_admitted": True,
         "candidate_admitted": True, "construction_stop": False}
        for seed in probe.GRAPH_SEEDS
    ]
    per_graph = {
        str(seed): {
            "status": "COMPLETE", "cycle_count": 0,
            "by_ell": {str(ell): {"cycle_count": 0}
                       for ell in range(probe.census.MIN_ELL,
                                        probe.census.MAX_ELL + 1)},
        }
        for seed in probe.GRAPH_SEEDS
    }
    totals_by_ell = {
        str(ell): {"cycle_count": 0}
        for ell in range(probe.census.MIN_ELL,
                         probe.census.MAX_ELL + 1)
    }
    _write_json(census_root / "manifest.json", {
        "batch_uuid": probe.census.BATCH_UUID,
        "status": "INVENTORY_COMPLETE", "batch_complete": True,
        "reference_batch_uuid": probe.census.REFERENCE_BATCH_UUID,
        "graph_seeds": list(probe.GRAPH_SEEDS),
        "decoder_calls": 0, "sampled_frames": 0,
        "truth_prior_or_conditional_arrays_saved": False,
        "graph_diagnostics": graph_diags,
        "candidate_diagnostics": candidate_diags,
    })
    _write_json(census_root / "summary.json", {
        "batch_uuid": probe.census.BATCH_UUID,
        "terminal_status": "INVENTORY_COMPLETE", "batch_complete": True,
        "graph_seeds": list(probe.GRAPH_SEEDS),
        "ell_range": [probe.census.MIN_ELL, probe.census.MAX_ELL],
        "truth_prior_or_conditional_arrays_saved": False,
        "per_graph": per_graph, "totals_by_ell": totals_by_ell,
    })
    _write_header_csv(census_root / "cycles.csv",
                      probe.census.CYCLE_COLUMNS)
    _write_json(overlap_root / "manifest.json", {
        "batch_uuid": probe.source_overlap.BATCH_UUID,
        "status": "OVERLAP_COMPLETE",
        "input_batch_uuid": probe.census.BATCH_UUID,
    })
    _write_json(overlap_root / "summary.json", {
        "batch_uuid": probe.source_overlap.BATCH_UUID,
        "terminal_status": "OVERLAP_COMPLETE", "batch_complete": True,
        "reference_batch_uuid": probe.census.BATCH_UUID,
        "input_rows_processed": 0,
    })
    _write_header_csv(overlap_root / "source_overlap.csv",
                      probe.source_overlap.SOURCE_COLUMNS)

    controls = {int(seed): _fake_dense() for seed in probe.GRAPH_SEEDS}
    actual_loader = probe.source_overlap.load_predecessor
    signature = inspect.signature(actual_loader)
    assert list(signature.parameters) == ["reference_root"]
    assert signature.parameters["reference_root"].default is inspect.Parameter.empty
    calls = []

    def observing_loader(reference_root):
        loaded = actual_loader(reference_root)
        calls.append((Path(reference_root).resolve(), loaded))
        return loaded

    monkeypatch.setattr(probe.source_overlap, "load_predecessor",
                        observing_loader)
    inventories = probe._load_cycle_inventory(repo, controls)

    assert len(calls) == 1
    loaded_root, accepted = calls[0]
    assert loaded_root == census_root.resolve()
    assert set(accepted) == {
        "root", "manifest", "summary", "expected_by_graph_ell",
        "expected_rows",
    }
    assert accepted["root"] == census_root
    assert accepted["expected_rows"] == 0
    assert accepted["expected_by_graph_ell"] == {
        int(seed): {ell: 0 for ell in range(probe.census.MIN_ELL,
                                           probe.census.MAX_ELL + 1)}
        for seed in probe.GRAPH_SEEDS
    }
    assert set(inventories) == set(probe.GRAPH_SEEDS)
    assert all(cycles == [] for cycles in inventories.values())
