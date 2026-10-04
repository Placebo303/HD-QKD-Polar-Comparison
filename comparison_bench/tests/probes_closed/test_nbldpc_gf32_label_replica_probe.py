"""Fake-only tests for the fixed-PMF, new-graph GF32 replica EXPLORE runner."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli.probes_closed import nbldpc_gf32_label_replica_probe as probe
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout


def _fake_dense() -> np.ndarray:
    row_degrees = [4] * 4 + [5] * 48
    sockets = [
        row
        for layer in range(5)
        for row, degree in enumerate(row_degrees)
        if degree > layer
    ]
    assert len(sockets) == probe.EDGE_COUNT
    dense = np.zeros((probe.M, probe.N), dtype=np.int64)
    for column in range(probe.N):
        first, second = sockets[2 * column : 2 * column + 2]
        assert first != second
        dense[first, column] = 1
        dense[second, column] = 2
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


def _fake_candidate(dense: np.ndarray, pmf: np.ndarray, graph_seed: int):
    labels = np.full(probe.N, 2, dtype=np.int64)
    candidate = probe.predecessor.alignment.scale_columns(dense, labels)
    return candidate, {
        "graph_seed": int(graph_seed), "candidate_admitted": True,
        "J0_bits": 0.0, "Jc_bits": 1.0,
        "gauge_equal": True, "support_equal": True,
        "nontrivial": True, "degrees_equal": True,
        "baseline_rank": probe.M, "candidate_rank": probe.M,
    }


def _test_repo(path: Path) -> tuple[Path, Path]:
    repo = path / "repo"
    (repo / "workspace").mkdir(parents=True)
    return repo, probe.OUT_ROOT_RELATIVE


def _summary_pair_states(delta: int, graph_index: int, pair_slot: int):
    """Create fixed per-graph success masks for the +/-12 screen tests."""
    graph_deltas = ([3, 3, 3, 3, 0, 0] if delta == 12
                    else [3, 3, 3, 2, 0, 0])
    graph_delta = graph_deltas[graph_index]
    control_total = 16
    candidate_total = control_total + graph_delta
    both = 13 if graph_delta == 3 else 14 if graph_delta == 2 else 16
    control_only = control_total - both
    candidate_only = candidate_total - both
    if pair_slot < both:
        return True, True
    pair_slot -= both
    if pair_slot < control_only:
        return True, False
    pair_slot -= control_only
    if pair_slot < candidate_only:
        return False, True
    return False, False


def _summary_rows(delta: int):
    """Build result rows directly for complete-summary gate boundary tests."""
    _, holdout = probe.seed_plan()
    pmf = probe.shape_pmf_grid()[0]
    rows = []
    pairs = []
    for pair_index, (graph_seed, stream, frame, seed) in enumerate(holdout):
        graph_index = graph_seed - probe.GRAPH_SEEDS[0]
        pair_slot = stream * probe.HOLDOUT_FRAMES_PER_STREAM + frame
        control, candidate = _summary_pair_states(
            delta, graph_index, pair_slot
        )
        # Isolate one syndrome-consistent wrong control row. It remains a
        # failure because exact is false, even though the syndrome is accepted.
        wrong_control = (graph_index == 0 and pair_slot == 16)
        for arm, exact, wrong in (
            ("control", control, wrong_control),
            ("candidate", candidate, False),
        ):
            rows.append(probe.predecessor._record_row(
                phase="holdout", pmf=pmf, graph_seed=graph_seed,
                stream=stream, frame=frame, seed=seed,
                call_index=2 * pair_index + (1 if arm == "control" else 2),
                arm=arm,
                observed={
                    "exact": bool(exact),
                    "syndrome_accept": bool(exact or wrong),
                    "syndrome_consistent_wrong": bool(wrong),
                    "status": "fake", "iterations": 1,
                    "wall_s": 0.0, "rss_b": 0,
                },
            ))
        pairs.append({
            "graph_seed": graph_seed, "stream": stream, "frame": frame,
            "control_exact": bool(control),
            "candidate_exact": bool(candidate),
        })
    return rows, pairs


def _assert_partial_unknowns(summary):
    assert summary["holdout_complete"] is False
    assert summary["control_exact"] is None
    assert summary["candidate_exact"] is None
    assert summary["delta"] is None
    assert summary["paired_states"] is None
    assert set(summary["delta_by_graph"]) == {
        str(seed) for seed in probe.GRAPH_SEEDS
    }
    assert "2026093801" not in summary["delta_by_graph"]
    for graph in summary["delta_by_graph"].values():
        assert graph["control_exact"] is None
        assert graph["candidate_exact"] is None
        assert graph["delta_g"] is None


def test_fixed_pmf_new_graphs_and_disjoint_frame_seeds():
    grid = probe.shape_pmf_grid()
    assert probe.P0_GRID == (0.55,)
    assert len(grid) == 1
    assert grid[0]["index"] == 0
    assert grid[0]["p0"] == 0.55
    assert probe.GRAPH_SEEDS == tuple(range(2026093901, 2026093907))
    assert probe.SEED_PREFIX == "gf32-label-replica-v1"
    pmf = grid[0]["pmf"]
    assert np.flatnonzero(pmf).tolist() == [0, 1, 3, 7, 15, 31]
    assert pmf[0] == pytest.approx(0.55)
    assert float(pmf.sum()) == pytest.approx(1.0, abs=1e-12)
    assert grid[0]["formula"].startswith("p[0]=0.550; p[e]=0.450*")
    for symbol, count in probe.SHAPE_COUNTS:
        assert pmf[symbol] == pytest.approx(
            0.45 * count / probe.SHAPE_TOTAL, abs=1e-12
        )
    assert np.flatnonzero(pmf[2:]).tolist() == [1, 5, 13, 29]

    pilots, holdouts = probe.seed_plan()
    assert pilots == []
    assert len(holdouts) == probe.HOLDOUT_PAIRS == 192
    new_seeds = [row[3] for row in holdouts]
    assert len(set(new_seeds)) == 192
    assert holdouts[0] == (
        probe.GRAPH_SEEDS[0], 0, 0,
        probe.common.v10_seed(
            f"{probe.SEED_PREFIX}:holdout:{probe.GRAPH_SEEDS[0]}:0:0"
        ),
    )
    prior_seeds = {
        row[3] for plan in probe.prior_runner._seed_plan() for row in plan
    }
    shape_seeds = {
        row[3] for plan in probe.predecessor.seed_plan() for row in plan
    }
    fine_seeds = {
        row[3] for plan in probe.fine_runner.seed_plan() for row in plan
    }
    assert set(new_seeds).isdisjoint(prior_seeds | shape_seeds | fine_seeds)
    assert probe.arm_order(0) == ("control", "candidate")
    assert probe.arm_order(1) == ("candidate", "control")


def test_dry_run_and_fresh_root_are_no_write(tmp_path, monkeypatch):
    repo, out_root = _test_repo(tmp_path)
    for obj, name, label in (
        (probe, "build_profile_graph", "graph construction"),
        (probe, "_candidate_for_graph", "candidate construction"),
        (probe.prior_runner, "sample_error", "sampled input"),
        (probe.prior_runner, "decode_observation", "decoder"),
    ):
        monkeypatch.setattr(
            obj, name,
            lambda *args, _label=label, **kwargs: pytest.fail(
                f"dry-run reached {_label}"
            ),
        )
    result = probe.dry_run(out_root, repo_root=repo)
    assert result["status"] == "DRY_RUN"
    assert result["writes"] == result["empirical_input_reads"] == 0
    assert result["graph_construction_calls"] == result["decoder_calls"] == 0
    assert result["fixed_p0"] == 0.55
    assert result["pilot_call_ceiling"] == result["pilot_seed_count"] == 0
    assert result["holdout_pair_count"] == 192
    assert result["holdout_call_count"] == result["maximum_call_count"] == 384
    assert result["holdout_seeds_disjoint_from_prior_batches"] is True
    assert not (repo / out_root).exists()

    assert probe.validate_out_root(out_root, repo_root=repo) == repo / out_root
    with pytest.raises(ValueError, match="frozen fresh root"):
        probe.validate_out_root("workspace/other", repo_root=repo)
    (repo / out_root).mkdir()
    with pytest.raises(FileExistsError, match="refusing existing output root"):
        probe.validate_out_root(out_root, repo_root=repo)


@pytest.mark.parametrize(
    ("delta", "expected_classification", "expected_candidate", "states"),
    [
        (12, "MECHANISM_SIGNAL", 108,
         {"both": 84, "control_only": 12,
          "candidate_only": 24, "neither": 72}),
        (11, "NO_SUFFICIENT_SIGNAL", 107,
         {"both": 85, "control_only": 11,
          "candidate_only": 22, "neither": 74}),
    ],
)
def test_complete_summary_screen_boundary_and_wrong_isolation(
        delta, expected_classification, expected_candidate, states
):
    rows, pairs = _summary_rows(delta)
    summary = probe._summarize(rows, pairs, "")
    assert summary["holdout_complete"] is True
    assert summary["holdout_pairs_completed"] == 192
    assert summary["control_exact"] == 96
    assert summary["candidate_exact"] == expected_candidate
    assert summary["delta"] == delta
    assert summary["paired_states"] == states
    assert [summary["delta_by_graph"][str(seed)]["delta_g"]
            for seed in probe.GRAPH_SEEDS] == (
                [3, 3, 3, 3, 0, 0] if delta == 12
                else [3, 3, 3, 2, 0, 0]
            )
    assert sum(value["delta_g"] > 0
               for value in summary["delta_by_graph"].values()) == 4
    assert summary["syndrome_consistent_wrong_rows"] == 1
    assert summary["syndrome_consistent_wrong_by_arm"] == {
        "control": 1, "candidate": 0
    }
    assert summary["integrity_violations"] == 0
    assert summary["resource_violations"] == 0
    assert summary["classification"] == expected_classification
    assert summary["FER"] is summary["f_eff"] is summary["SKR"] is None


def test_full_fake_run_uses_only_new_graphs_and_384_holdout_calls(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path)
    pilots, holdouts = probe.seed_plan()
    assert pilots == []
    holdout_by_seed = {
        seed: (graph_seed, stream, frame)
        for graph_seed, stream, frame, seed in holdouts
    }
    current = {"seed": None, "graph_seed": None, "stream": None,
               "frame": None, "truth": None}
    graphs = {}
    candidates = {}
    graph_calls = []
    candidate_calls = []
    decode_calls = []
    pair_checks = []

    def sample(seed, pmf, width=probe.N):
        graph_seed, stream, frame = holdout_by_seed[seed]
        assert pmf[0] == pytest.approx(0.55)
        truth = np.zeros(width, dtype=np.int64)
        current.update(seed=seed, graph_seed=graph_seed, stream=stream,
                       frame=frame, truth=truth.copy())
        return truth

    monkeypatch.setattr(probe.prior_runner, "sample_error", sample)

    def graph_builder(seed):
        graph_calls.append(seed)
        graph = _fake_graph(seed)
        graphs[seed] = graph["dense"].copy()
        return graph

    def candidate_builder(dense, pmf, graph_seed):
        candidate_calls.append(graph_seed)
        candidate, diagnostic = _fake_candidate(dense, pmf, graph_seed)
        candidates[graph_seed] = candidate.copy()
        return candidate, diagnostic

    original_pair = probe.prior_runner.paired_arm_data

    def inspect_pair(control, candidate, truth, prior):
        pair = original_pair(control, candidate, truth, prior)
        np.testing.assert_array_equal(pair["control"]["truth"], truth)
        np.testing.assert_array_equal(pair["candidate"]["truth"], truth)
        np.testing.assert_array_equal(pair["control"]["prior"], prior)
        np.testing.assert_array_equal(pair["candidate"]["prior"], prior)
        np.testing.assert_array_equal(
            pair["control"]["syndrome"], layout.gf32_syndrome(control, truth)
        )
        np.testing.assert_array_equal(
            pair["candidate"]["syndrome"],
            layout.gf32_syndrome(candidate, truth),
        )
        pair_checks.append(True)
        return pair

    monkeypatch.setattr(probe.prior_runner, "paired_arm_data", inspect_pair)

    def decode(dense, prior, syndrome):
        decode_calls.append(1)
        graph_seed = current["graph_seed"]
        if np.array_equal(dense, candidates[graph_seed]):
            arm = "candidate"
        else:
            np.testing.assert_array_equal(dense, graphs[graph_seed])
            arm = "control"
        graph_index = graph_seed - probe.GRAPH_SEEDS[0]
        pair_slot = current["stream"] * probe.HOLDOUT_FRAMES_PER_STREAM \
            + current["frame"]
        control_ok, candidate_ok = _summary_pair_states(
            12, graph_index, pair_slot
        )
        exact = candidate_ok if arm == "candidate" else control_ok
        estimate = current["truth"].copy()
        if not exact:
            estimate[0] = (estimate[0] + 1) % 32
        accepted = bool(np.array_equal(
            layout.gf32_syndrome(dense, estimate), syndrome
        ))
        return SimpleNamespace(
            x_hat=estimate, syndrome_ok=accepted,
            iterations=1, status="fake",
        )

    result = probe.execute_batch(
        out_root=out_root, decode_fn=decode, graph_builder=graph_builder,
        candidate_builder=candidate_builder, repo_root=repo,
        rss_fn=lambda: 0,
    )

    assert graph_calls == list(probe.GRAPH_SEEDS)
    assert candidate_calls == list(probe.GRAPH_SEEDS)
    assert len(decode_calls) == probe.MAX_CALLS == 384
    assert len(pair_checks) == probe.HOLDOUT_PAIRS == 192
    assert result["terminal_status"] == "MECHANISM_SIGNAL"
    assert result["classification"] == "MECHANISM_SIGNAL"
    assert result["holdout_complete"] is True
    assert result["holdout_pairs_completed"] == 192
    assert result["fixed_p0"] == 0.55
    assert result["fixed_pmf_index"] == 0
    assert result["selected_pmf_index"] is None
    assert result["pilot_control_exact_by_pmf"] == {}
    assert result["attempted_call_counts"] == {
        "pilot": 0, "holdout": 384, "total": 384
    }
    assert result["control_exact"] == 96
    assert result["candidate_exact"] == 108
    assert result["delta"] == 12
    assert result["paired_states"] == {
        "both": 84, "control_only": 12,
        "candidate_only": 24, "neither": 72,
    }
    assert set(result["delta_by_graph"]) == {
        str(seed) for seed in probe.GRAPH_SEEDS
    }
    assert "2026093801" not in result["delta_by_graph"]
    assert [result["delta_by_graph"][str(seed)]["delta_g"]
            for seed in probe.GRAPH_SEEDS] == [3, 3, 3, 3, 0, 0]
    assert result["syndrome_bits_per_attempt"] == 260
    assert result["integrity_violations"] == 0
    assert result["resource_violations"] == 0
    assert result["authorization_violations"] == 0

    root = repo / out_root
    assert sorted(path.name for path in root.iterdir()) == [
        "EXPLORATION_LOG.md", "frame_records.csv", "manifest.json",
        "summary.json",
    ]
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["batch_uuid"] == probe.BATCH_UUID
    assert manifest["seed_namespace"] == probe.SEED_PREFIX
    assert manifest["pilot"] == "NOT_RUN_FIXED_PMF"
    assert manifest["graph_profile"]["graph_seeds"] == list(probe.GRAPH_SEEDS)
    assert manifest["seed_plan_counts"] == {"pilot": 0, "holdout_pairs": 192}
    assert manifest["budgets"]["max_decoder_calls"] == 384
    with (root / "frame_records.csv").open(newline="") as stream:
        records = list(csv.DictReader(stream))
    assert len(records) == 384
    assert {row["phase"] for row in records} == {"holdout"}
    assert {int(row["syndrome_bits"]) for row in records} == {260}
    assert {int(row["graph_seed"]) for row in records} == set(probe.GRAPH_SEEDS)
    assert {int(row["seed"]) for row in records} == set(holdout_by_seed)
    for graph_seed in probe.GRAPH_SEEDS:
        assert sum(row["graph_seed"] == str(graph_seed) for row in records) == 64


def test_graph_and_candidate_gates_stop_with_new_seed_summaries(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path / "graph")
    graph_calls = []

    def bad_graph(seed):
        graph_calls.append(seed)
        graph = _fake_graph(seed)
        if seed == probe.GRAPH_SEEDS[0]:
            graph["dense"][0, 0] = 0
        return graph

    graph_result = probe.execute_batch(
        out_root=out_root,
        decode_fn=lambda *args: pytest.fail("bad graph reached decoder"),
        graph_builder=bad_graph,
        candidate_builder=lambda *args: pytest.fail(
            "bad graph reached candidate builder"
        ),
        repo_root=repo, rss_fn=lambda: 0,
    )
    assert graph_result["terminal_status"] == "GRAPH_PREFLIGHT_FAILED"
    assert graph_result["attempted_call_counts"] == {
        "pilot": 0, "holdout": 0, "total": 0
    }
    _assert_partial_unknowns(graph_result)
    assert graph_calls == list(probe.GRAPH_SEEDS)
    graph_manifest = json.loads((repo / out_root / "manifest.json").read_text())
    assert [item["graph_seed"] for item in graph_manifest["graph_diagnostics"]] \
        == list(probe.GRAPH_SEEDS)

    repo2, out_root2 = _test_repo(tmp_path / "candidate")
    candidate_calls = []
    decode_calls = []
    monkeypatch.setattr(
        probe.prior_runner, "sample_error",
        lambda seed, pmf, width=probe.N: np.zeros(width, dtype=np.int64)
    )

    def candidate_builder(dense, pmf, graph_seed):
        candidate_calls.append(graph_seed)
        if graph_seed == probe.GRAPH_SEEDS[-1]:
            return None, {
                "graph_seed": graph_seed, "candidate_admitted": False,
                "J0_bits": 0.0, "Jc_bits": 0.0,
            }
        return _fake_candidate(dense, pmf, graph_seed)

    candidate_result = probe.execute_batch(
        out_root=out_root2,
        decode_fn=lambda *args: decode_calls.append(1),
        graph_builder=_fake_graph, candidate_builder=candidate_builder,
        repo_root=repo2, rss_fn=lambda: 0,
    )
    assert candidate_result["terminal_status"] == \
        "NO_NONTRIVIAL_LABEL_CANDIDATE"
    assert candidate_result["attempted_call_counts"] == {
        "pilot": 0, "holdout": 0, "total": 0
    }
    assert candidate_calls == list(probe.GRAPH_SEEDS)
    assert decode_calls == []
    _assert_partial_unknowns(candidate_result)


def test_partial_holdout_masks_metrics_after_one_pair_and_orphan_arm(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path)
    _, holdouts = probe.seed_plan()
    holdout_by_seed = {
        seed: (graph_seed, stream, frame)
        for graph_seed, stream, frame, seed in holdouts
    }
    current = {"graph_seed": None, "stream": None, "frame": None}
    decoder_calls = []
    monkeypatch.setattr(
        probe.prior_runner, "sample_error",
        lambda seed, pmf, width=probe.N: (
            current.update(graph_seed=holdout_by_seed[seed][0],
                           stream=holdout_by_seed[seed][1],
                           frame=holdout_by_seed[seed][2])
            or np.zeros(width, dtype=np.int64)
        ),
    )

    def decode(dense, prior, syndrome):
        decoder_calls.append(1)
        estimate = np.zeros(probe.N, dtype=np.int64)
        accepted = bool(np.array_equal(
            layout.gf32_syndrome(dense, estimate), syndrome
        ))
        return SimpleNamespace(
            x_hat=estimate, syndrome_ok=accepted,
            iterations=1, status="fake",
        )

    original_stop = probe._resource_stop

    def stop_after_orphan(started, now, rss_fn):
        if len(decoder_calls) >= 3:
            return "total_wall_cap_before_next_call"
        return original_stop(started, now, rss_fn)

    monkeypatch.setattr(probe, "_resource_stop", stop_after_orphan)
    result = probe.execute_batch(
        out_root=out_root, decode_fn=decode, graph_builder=_fake_graph,
        candidate_builder=_fake_candidate, repo_root=repo, rss_fn=lambda: 0,
    )
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert result["attempted_call_counts"] == {
        "pilot": 0, "holdout": 3, "total": 3
    }
    assert result["holdout_pairs_completed"] == 1
    assert result["stop_reason"] == "total_wall_cap_before_next_call"
    _assert_partial_unknowns(result)
    first_graph = result["delta_by_graph"][str(probe.GRAPH_SEEDS[0])]
    assert first_graph["completed_pairs"] == 1
    assert first_graph["control_attempts"] == 1
    assert first_graph["candidate_attempts"] == 2
    assert len(decoder_calls) == 3

    with (repo / out_root / "frame_records.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 3
    assert [row["arm"] for row in rows] == [
        "control", "candidate", "candidate"
    ]


@pytest.mark.parametrize(
    ("resource_case", "expected_reason", "expected_wall"),
    [
        ("call_wall", "decoder_call_wall_cap_after_return", 121.0),
        ("total_wall", "total_wall_cap_after_call", 20.0),
        ("rss", "rss_cap_after_call", 0.0),
    ],
)
def test_decoder_exception_postreturn_resource_caps_retain_and_stop(
        tmp_path, monkeypatch, resource_case, expected_reason, expected_wall
):
    repo, out_root = _test_repo(tmp_path)
    clock = {"value": 0.0}
    rss = {"value": 0}
    rss_reads = []
    graph_calls = []
    candidate_calls = []
    decoder_calls = []
    monkeypatch.setattr(
        probe.prior_runner, "sample_error",
        lambda seed, pmf, width=probe.N: np.zeros(width, dtype=np.int64)
    )

    def rss_fn():
        rss_reads.append(rss["value"])
        return rss["value"]

    def graph_builder(seed):
        graph_calls.append(seed)
        graph = _fake_graph(seed)
        if resource_case == "total_wall" and seed == probe.GRAPH_SEEDS[-1]:
            clock["value"] = probe.WALL_CAP_S - 10.0
        return graph

    def candidate_builder(dense, pmf, graph_seed):
        candidate_calls.append(graph_seed)
        return _fake_candidate(dense, pmf, graph_seed)

    def raise_over_cap(dense, prior, syndrome):
        decoder_calls.append(1)
        if resource_case == "call_wall":
            clock["value"] = probe.CALL_CAP_S + 1.0
        elif resource_case == "total_wall":
            assert clock["value"] == probe.WALL_CAP_S - 10.0
            clock["value"] += 20.0
        else:
            assert rss["value"] < probe.RSS_CAP_BYTES
            rss["value"] = probe.RSS_CAP_BYTES + 1
        raise RuntimeError("fake_resource_overrun")

    result = probe.execute_batch(
        out_root=out_root, decode_fn=raise_over_cap,
        graph_builder=graph_builder, candidate_builder=candidate_builder,
        repo_root=repo, now=lambda: clock["value"], rss_fn=rss_fn,
    )
    assert graph_calls == candidate_calls == list(probe.GRAPH_SEEDS)
    assert len(decoder_calls) == 1
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert result["attempted_call_counts"] == {
        "pilot": 0, "holdout": 1, "total": 1
    }
    assert result["holdout_pairs_completed"] == 0
    assert result["resource_violations"] == 1
    assert "decoder_exception" in result["stop_reason"]
    assert expected_reason in result["stop_reason"]
    _assert_partial_unknowns(result)
    assert rss_reads[0] == 0

    with (repo / out_root / "frame_records.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert rows[0]["phase"] == "holdout"
    assert "decoder_exception:RuntimeError" in rows[0]["status"]
    assert f"resource_abort:{expected_reason}" in rows[0]["status"]
    assert float(rows[0]["wall_s"]) == expected_wall
    if resource_case == "rss":
        assert int(rows[0]["rss_b"]) == probe.RSS_CAP_BYTES + 1
        assert rss_reads[-1] == probe.RSS_CAP_BYTES + 1
    else:
        assert int(rows[0]["rss_b"]) == 0
