"""Fake-only tests for the frozen GF32 fine-grid EXPLORE runner."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli.probes_closed import nbldpc_gf32_shape_fine_probe as probe
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
        "status": "ok",
        "graph_seed": int(seed),
        "n": probe.N,
        "m": probe.M,
        "E": probe.EDGE_COUNT,
        "dense": _fake_dense(),
        "admitted": True,
        "failure_reason": "",
        "structure": {
            "admitted": True,
            "admission": {
                "profile": True,
                "connected": True,
                "full_rank": True,
            },
            "gf32_rank": probe.M,
            "structural_rank": probe.M,
            "connected_components": 1,
            "duplicate_edges": 0,
        },
    }


def _test_repo(path: Path) -> tuple[Path, Path]:
    repo = path / "repo"
    (repo / "workspace").mkdir(parents=True)
    return repo, probe.OUT_ROOT_RELATIVE


def _fake_candidate(dense: np.ndarray, pmf: np.ndarray, graph_seed: int):
    labels = np.full(probe.N, 2, dtype=np.int64)
    candidate = probe.predecessor.alignment.scale_columns(dense, labels)
    return candidate, {
        "graph_seed": int(graph_seed),
        "candidate_admitted": True,
        "J0_bits": 0.0,
        "Jc_bits": 1.0,
        "gauge_equal": True,
        "support_equal": True,
        "nontrivial": True,
    }


def _recorded_decoder(estimate_fn, calls: list, current: dict):
    def decode(dense, prior, syndrome):
        estimate = np.asarray(estimate_fn(), dtype=np.int64)
        accepted = bool(np.array_equal(
            layout.gf32_syndrome(dense, estimate), syndrome
        ))
        calls.append({
            "dense": np.asarray(dense).copy(),
            "prior_row": np.asarray(prior)[0].copy(),
            "syndrome": np.asarray(syndrome).copy(),
            "truth": np.asarray(current["truth"]).copy(),
            "estimate": estimate.copy(),
        })
        return SimpleNamespace(
            x_hat=estimate,
            syndrome_ok=accepted,
            iterations=1,
            status="fake",
        )
    return decode


def test_fine_grid_sparse_shape_and_seed_namespace():
    grid = probe.shape_pmf_grid()
    assert [row["p0"] for row in grid] == [
        0.625, 0.600, 0.575, 0.550, 0.525, 0.500, 0.475
    ]
    assert [row["index"] for row in grid] == list(range(7))
    assert probe.SEED_PREFIX == "gf32-shape-fine-v1"
    assert probe.SHAPE_COUNTS == (
        (1, 2295), (3, 1126), (7, 557), (15, 304), (31, 146)
    )
    assert sum(count for _, count in probe.SHAPE_COUNTS) == 4428
    for row in grid:
        pmf = row["pmf"]
        assert np.flatnonzero(pmf).tolist() == [0, 1, 3, 7, 15, 31]
        assert pmf[0] == row["p0"]
        assert float(pmf.sum()) == pytest.approx(1.0, abs=1e-12)
        for symbol, count in probe.SHAPE_COUNTS:
            assert pmf[symbol] == pytest.approx(
                (1.0 - row["p0"]) * count / probe.SHAPE_TOTAL
            )
        assert row["entropy_bits"] == pytest.approx(
            probe.predecessor.alignment.entropy_bits(pmf), abs=1e-12
        )
    assert probe.verify_t0()["fine_sparse_shape_grid"] is True

    pilot, holdout = probe.seed_plan()
    assert len(pilot) == probe.MAX_PILOT_CALLS == 168
    assert len(holdout) == probe.HOLDOUT_PAIRS == 192
    pilot_seeds = [item[3] for item in pilot]
    holdout_seeds = [item[3] for item in holdout]
    assert len(set(pilot_seeds)) == len(pilot_seeds)
    assert len(set(holdout_seeds)) == len(holdout_seeds)
    assert set(pilot_seeds).isdisjoint(holdout_seeds)
    old_pilot, old_holdout = probe.predecessor.seed_plan()
    old_seeds = {item[3] for item in old_pilot + old_holdout}
    assert set(pilot_seeds + holdout_seeds).isdisjoint(old_seeds)
    assert pilot[0] == (
        0, probe.GRAPH_SEEDS[0], 0,
        probe.common.v10_seed(
            f"{probe.SEED_PREFIX}:pilot:0:{probe.GRAPH_SEEDS[0]}:0"
        ),
    )
    assert holdout[0] == (
        probe.GRAPH_SEEDS[0], 0, 0,
        probe.common.v10_seed(
            f"{probe.SEED_PREFIX}:holdout:{probe.GRAPH_SEEDS[0]}:0:0"
        ),
    )
    assert probe.arm_order(0) == ("control", "candidate")
    assert probe.arm_order(1) == ("candidate", "control")

    # Importing and using the successor leaves predecessor constants intact.
    assert tuple(probe.predecessor.P0_GRID) == (0.85, 0.65, 0.45, 0.25)
    assert probe.predecessor.OUT_ROOT_RELATIVE.as_posix() == \
        "workspace/gf32_shape_fd01e03e"
    assert old_pilot[0][3] == probe.common.v10_seed(
        f"gf32-shape-v1:pilot:0:{probe.predecessor.GRAPH_SEEDS[0]}:0"
    )
    assert probe.predecessor.OUT_ROOT_RELATIVE == Path(
        "workspace/gf32_shape_fd01e03e"
    )


def test_dry_run_and_fresh_root_are_no_write(tmp_path, monkeypatch):
    repo, out_root = _test_repo(tmp_path)
    monkeypatch.setattr(
        probe, "build_profile_graph",
        lambda seed: pytest.fail("dry-run built a graph")
    )
    monkeypatch.setattr(
        probe, "_candidate_for_graph",
        lambda *args: pytest.fail("dry-run built a candidate")
    )
    monkeypatch.setattr(
        probe.prior_runner, "decode_observation",
        lambda *args, **kwargs: pytest.fail("dry-run decoded")
    )
    result = probe.dry_run(out_root, repo_root=repo)
    assert result["status"] == "DRY_RUN"
    assert result["writes"] == result["empirical_input_reads"] == 0
    assert result["graph_construction_calls"] == result["decoder_calls"] == 0
    assert result["p0_grid"] == list(probe.P0_GRID)
    assert result["pilot_call_ceiling"] == 168
    assert result["holdout_pair_count"] == 192
    assert result["holdout_call_count"] == 384
    assert result["maximum_call_count"] == 552
    assert result["pilot_holdout_seed_disjoint"] is True
    assert result["seeds_disjoint_from_fd01"] is True
    assert not (repo / out_root).exists()

    assert probe.validate_out_root(out_root, repo_root=repo) == repo / out_root
    with pytest.raises(ValueError, match="frozen fresh root"):
        probe.validate_out_root("workspace/other", repo_root=repo)
    (repo / out_root).mkdir()
    with pytest.raises(FileExistsError, match="refusing existing output root"):
        probe.validate_out_root(out_root, repo_root=repo)


def test_fake_graph_preflight_and_candidate_gauge(monkeypatch):
    graph = _fake_graph(probe.GRAPH_SEEDS[0])
    admitted, diagnostic = probe.graph_preflight(graph, probe.GRAPH_SEEDS[0])
    assert admitted is True
    assert diagnostic["E"] == 256
    assert diagnostic["variable_degree_histogram"] == {2: 128}
    assert diagnostic["check_degree_histogram"] == {4: 4, 5: 48}

    broken = dict(graph)
    broken["dense"] = graph["dense"].copy()
    broken["dense"][0, 0] = 0
    assert probe.graph_preflight(broken, probe.GRAPH_SEEDS[0])[0] is False

    def fake_align(dense, pmf):
        labels = np.full(probe.N, 2, dtype=np.int64)
        return {
            "candidate": probe.predecessor.alignment.scale_columns(
                dense, labels
            ),
            "labels": labels,
            "gauge_equal": True,
            "support_equal": True,
            "J0": 0.0,
            "Jc": 1.0,
            "candidate_admitted": True,
        }

    monkeypatch.setattr(
        probe.predecessor.alignment, "align_labels", fake_align
    )
    monkeypatch.setattr(
        probe.predecessor.d10, "gf32_row_rank",
        lambda matrix: probe.M
    )
    candidate, detail = probe._candidate_for_graph(
        graph["dense"], probe.shape_pmf_grid()[0]["pmf"],
        probe.GRAPH_SEEDS[0]
    )
    assert candidate is not None
    assert detail["candidate_admitted"] is True
    assert detail["nontrivial"] is True
    assert detail["gauge_equal"] is True
    assert detail["support_equal"] is True
    assert detail["degrees_equal"] is True
    assert detail["baseline_rank"] == detail["candidate_rank"] == probe.M


def test_no_eligible_control_point_stops_after_full_grid(tmp_path, monkeypatch):
    repo, out_root = _test_repo(tmp_path)
    graph_calls = []
    decoder_calls = []

    def graph_builder(seed):
        graph_calls.append(seed)
        return _fake_graph(seed)

    monkeypatch.setattr(
        probe.prior_runner, "sample_error",
        lambda seed, pmf, width=probe.N: np.zeros(width, dtype=np.int64)
    )

    def decode(dense, prior, syndrome):
        decoder_calls.append(1)
        estimate = np.zeros(probe.N, dtype=np.int64)
        accepted = bool(np.array_equal(
            layout.gf32_syndrome(dense, estimate), syndrome
        ))
        return SimpleNamespace(
            x_hat=estimate, syndrome_ok=accepted,
            iterations=1, status="fake"
        )

    def forbidden_candidate(*args):
        pytest.fail("candidate must not be built without an eligible point")

    result = probe.execute_batch(
        out_root=out_root,
        decode_fn=decode,
        graph_builder=graph_builder,
        candidate_builder=forbidden_candidate,
        repo_root=repo,
        rss_fn=lambda: 0,
    )
    assert graph_calls == list(probe.GRAPH_SEEDS)
    assert len(decoder_calls) == probe.MAX_PILOT_CALLS == 168
    assert result["terminal_status"] == "CONTROL_RANGE_UNINFORMATIVE"
    assert result["selected_pmf_index"] is None
    assert result["pilot_control_exact_by_pmf"] == {
        str(i): 24 for i in range(7)
    }
    assert result["attempted_call_counts"] == {
        "pilot": 168, "holdout": 0, "total": 168
    }
    assert result["holdout_complete"] is False
    assert result["holdout_pairs_completed"] == 0
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    assert result["delta"] is None
    assert result["paired_states"] is None
    assert all(
        item["control_exact"] is item["candidate_exact"] is item["delta_g"] is None
        for item in result["delta_by_graph"].values()
    )
    assert result["resource_violations"] == 0

    root = repo / out_root
    assert sorted(path.name for path in root.iterdir()) == [
        "EXPLORATION_LOG.md", "frame_records.csv", "manifest.json",
        "summary.json"
    ]
    with (root / "frame_records.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 168
    assert {row["phase"] for row in rows} == {"pilot"}
    assert {row["arm"] for row in rows} == {"control"}
    assert {int(row["syndrome_bits"]) for row in rows} == {260}
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["batch_uuid"] == probe.BATCH_UUID
    assert manifest["seed_namespace"] == "gf32-shape-fine-v1"
    assert [row["p0"] for row in manifest["pmf_grid"]] == list(probe.P0_GRID)
    assert manifest["candidate_diagnostics"] == []


def test_graph_and_candidate_admission_fail_before_holdout(tmp_path, monkeypatch):
    repo, out_root = _test_repo(tmp_path / "graph")
    graph_calls = []

    def bad_graph(seed):
        graph_calls.append(seed)
        graph = _fake_graph(seed)
        graph["dense"][0, 0] = 0
        return graph

    result = probe.execute_batch(
        out_root=out_root,
        decode_fn=lambda *args: pytest.fail("invalid graph reached decoder"),
        graph_builder=bad_graph,
        candidate_builder=lambda *args: pytest.fail(
            "invalid graph reached candidate"
        ),
        repo_root=repo,
        rss_fn=lambda: 0,
    )
    assert result["terminal_status"] == "GRAPH_PREFLIGHT_FAILED"
    assert result["attempted_decoder_calls"] == 0
    assert result["holdout_pairs_completed"] == 0

    repo2, out_root2 = _test_repo(tmp_path / "candidate")
    current = {"seed": None}
    pilot, _ = probe.seed_plan()
    pilot_by_seed = {item[3]: item[:3] for item in pilot}
    monkeypatch.setattr(
        probe.prior_runner, "sample_error",
        lambda seed, pmf, width=probe.N: np.zeros(width, dtype=np.int64)
    )

    def controlled_decoder(dense, prior, syndrome):
        nonlocal_calls[0] += 1
        estimate = (
            np.zeros(probe.N, dtype=np.int64)
            if nonlocal_calls[0] <= 12
            else np.ones(probe.N, dtype=np.int64)
        )
        accepted = bool(np.array_equal(
            layout.gf32_syndrome(dense, estimate), syndrome
        ))
        return SimpleNamespace(
            x_hat=estimate, syndrome_ok=accepted,
            iterations=1, status="fake"
        )

    nonlocal_calls = [0]

    def candidate_fails(dense, pmf, graph_seed):
        return None, {
            "graph_seed": graph_seed, "candidate_admitted": False,
            "J0_bits": 0.0, "Jc_bits": 0.0,
        }

    result2 = probe.execute_batch(
        out_root=out_root2,
        decode_fn=controlled_decoder,
        graph_builder=_fake_graph,
        candidate_builder=candidate_fails,
        repo_root=repo2,
        rss_fn=lambda: 0,
    )
    assert result2["terminal_status"] == "NO_NONTRIVIAL_LABEL_CANDIDATE"
    assert result2["selected_pmf_index"] == 0
    assert result2["attempted_call_counts"] == {
        "pilot": 24, "holdout": 0, "total": 24
    }
    assert result2["control_exact"] is None
    assert result2["candidate_exact"] is None
    assert result2["delta"] is None


def test_complete_fake_run_selects_first_eligible_and_reaches_552_cap(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path)
    pilot, holdout = probe.seed_plan()
    pilot_by_seed = {item[3]: item[:3] for item in pilot}
    holdout_seeds = {item[3] for item in holdout}
    current = {"seed": None, "truth": None}
    control_graphs = {}
    candidate_graphs = {}
    decoder_inputs = []
    pair_checks = []

    def sample(seed, pmf, width=probe.N):
        current["seed"] = seed
        truth = np.zeros(width, dtype=np.int64)
        if seed in holdout_seeds:
            truth[0] = 1
        current["truth"] = truth.copy()
        return truth

    monkeypatch.setattr(probe.prior_runner, "sample_error", sample)

    def graph_builder(seed):
        graph = _fake_graph(seed)
        control_graphs[seed] = graph["dense"].copy()
        return graph

    def candidate_builder(dense, pmf, graph_seed):
        candidate, diagnostic = _fake_candidate(dense, pmf, graph_seed)
        candidate_graphs[graph_seed] = candidate.copy()
        return candidate, diagnostic

    original_pair = probe.prior_runner.paired_arm_data

    def inspect_pair(control, candidate, truth, prior):
        pair = original_pair(control, candidate, truth, prior)
        np.testing.assert_array_equal(pair["control"]["truth"], truth)
        np.testing.assert_array_equal(pair["candidate"]["truth"], truth)
        np.testing.assert_array_equal(pair["control"]["prior"], prior)
        np.testing.assert_array_equal(pair["candidate"]["prior"], prior)
        np.testing.assert_array_equal(
            pair["control"]["syndrome"],
            layout.gf32_syndrome(control, truth),
        )
        np.testing.assert_array_equal(
            pair["candidate"]["syndrome"],
            layout.gf32_syndrome(candidate, truth),
        )
        pair_checks.append(True)
        return pair

    monkeypatch.setattr(
        probe.prior_runner, "paired_arm_data", inspect_pair
    )

    def estimate():
        seed = current["seed"]
        if seed in pilot_by_seed:
            index, graph_seed, frame = pilot_by_seed[seed]
            # Earlier points are deliberately above the selector range.
            # At the last point, two frames per graph yield 12/24.
            if index < 6 or frame < 2:
                return np.zeros(probe.N, dtype=np.int64)
            return np.ones(probe.N, dtype=np.int64)
        return np.asarray(current["truth"], dtype=np.int64)

    calls = []
    decode = _recorded_decoder(estimate, calls, current)
    result = probe.execute_batch(
        out_root=out_root,
        decode_fn=decode,
        graph_builder=graph_builder,
        candidate_builder=candidate_builder,
        repo_root=repo,
        rss_fn=lambda: 0,
    )

    assert result["selected_pmf_index"] == 6
    assert result["p0_grid"] == list(probe.P0_GRID)
    assert result["pilot_control_exact_by_pmf"] == {
        **{str(i): 24 for i in range(6)}, "6": 12
    }
    assert result["attempted_call_counts"] == {
        "pilot": 168, "holdout": 384, "total": 552
    }
    assert len(calls) == probe.MAX_CALLS == 552
    assert result["holdout_complete"] is True
    assert result["holdout_pairs_completed"] == 192
    assert result["control_exact"] == 192
    assert result["candidate_exact"] == 192
    assert result["delta"] == 0
    assert result["paired_states"] == {
        "both": 192, "control_only": 0, "candidate_only": 0, "neither": 0
    }
    assert len(pair_checks) == 192
    assert result["syndrome_bits_per_attempt"] == 260
    assert result["resource_violations"] == 0
    assert result["authorization_violations"] == 0
    assert result["integrity_violations"] == 0

    # 168 pilot decodes precede holdout; frame 0 uses control first and frame 1
    # candidate first. Both arms receive the same repeated prior and sampled error.
    first_control = control_graphs[probe.GRAPH_SEEDS[0]]
    first_candidate = candidate_graphs[probe.GRAPH_SEEDS[0]]
    np.testing.assert_array_equal(calls[168]["dense"], first_control)
    np.testing.assert_array_equal(calls[169]["dense"], first_candidate)
    np.testing.assert_array_equal(calls[170]["dense"], first_candidate)
    np.testing.assert_array_equal(calls[171]["dense"], first_control)
    np.testing.assert_array_equal(
        calls[168]["prior_row"], probe.shape_pmf_grid()[6]["pmf"]
    )
    assert not np.array_equal(calls[168]["truth"], np.zeros(probe.N))
    assert calls[168]["syndrome"].shape == (probe.M,)

    root = repo / out_root
    assert sorted(path.name for path in root.iterdir()) == [
        "EXPLORATION_LOG.md", "frame_records.csv", "manifest.json",
        "summary.json"
    ]
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["batch_uuid"] == probe.BATCH_UUID
    assert manifest["seed_namespace"] == "gf32-shape-fine-v1"
    assert manifest["seed_plan_disjoint_from_fd01"] is True
    assert manifest["budgets"]["max_decoder_calls"] == 552
    with (root / "frame_records.csv").open(newline="") as stream:
        records = list(csv.DictReader(stream))
    assert len(records) == 552
    assert {int(row["syndrome_bits"]) for row in records} == {260}
    assert {row["phase"] for row in records} == {"pilot", "holdout"}


def test_partial_holdout_masks_performance_after_orphan_arm(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path)
    pilot, _ = probe.seed_plan()
    pilot_by_seed = {item[3]: item[:3] for item in pilot}
    current = {"seed": None, "truth": None}
    decoder_calls = []
    monkeypatch.setattr(
        probe.prior_runner, "sample_error",
        lambda seed, pmf, width=probe.N: (
            current.update(seed=seed, truth=np.zeros(width, dtype=np.int64))
            or current["truth"].copy()
        ),
    )

    def decode(dense, prior, syndrome):
        decoder_calls.append(1)
        seed = current["seed"]
        index, _, frame = pilot_by_seed.get(seed, (-1, -1, -1))
        estimate = (
            np.zeros(probe.N, dtype=np.int64)
            if index == 0 and frame < 2
            else np.ones(probe.N, dtype=np.int64)
            if index == 0
            else np.zeros(probe.N, dtype=np.int64)
        )
        accepted = bool(np.array_equal(
            layout.gf32_syndrome(dense, estimate), syndrome
        ))
        return SimpleNamespace(
            x_hat=estimate, syndrome_ok=accepted,
            iterations=1, status="fake"
        )

    original_stop = probe._resource_stop

    def stop_after_one_orphan(started, now, rss_fn):
        if len(decoder_calls) >= 27:
            return "total_wall_cap_before_next_call"
        return original_stop(started, now, rss_fn)

    monkeypatch.setattr(probe, "_resource_stop", stop_after_one_orphan)
    result = probe.execute_batch(
        out_root=out_root,
        decode_fn=decode,
        graph_builder=_fake_graph,
        candidate_builder=_fake_candidate,
        repo_root=repo,
        rss_fn=lambda: 0,
    )
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert result["attempted_call_counts"] == {
        "pilot": 24, "holdout": 3, "total": 27
    }
    assert result["holdout_pairs_completed"] == 1
    assert result["holdout_complete"] is False
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    assert result["delta"] is None
    assert result["paired_states"] is None
    for graph in result["delta_by_graph"].values():
        assert graph["control_exact"] is None
        assert graph["candidate_exact"] is None
        assert graph["delta_g"] is None
    first_graph = result["delta_by_graph"][str(probe.GRAPH_SEEDS[0])]
    assert first_graph["completed_pairs"] == 1
    assert first_graph["control_attempts"] == 1
    assert first_graph["candidate_attempts"] == 2
    assert len(decoder_calls) == 27


def test_decoder_exception_over_call_cap_is_retained_and_stops(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path)
    graph_calls = []
    decoder_calls = []
    clock = {"value": 0.0}
    monkeypatch.setattr(
        probe.prior_runner, "sample_error",
        lambda seed, pmf, width=probe.N: np.zeros(width, dtype=np.int64)
    )

    def graph_builder(seed):
        graph_calls.append(seed)
        return _fake_graph(seed)

    def raise_after_call_cap(dense, prior, syndrome):
        decoder_calls.append(1)
        clock["value"] = probe.CALL_CAP_S + 1.0
        raise RuntimeError("fake_overrun")

    result = probe.execute_batch(
        out_root=out_root,
        decode_fn=raise_after_call_cap,
        graph_builder=graph_builder,
        candidate_builder=lambda *args: pytest.fail(
            "overrun should stop before candidate"
        ),
        repo_root=repo,
        now=lambda: clock["value"],
        rss_fn=lambda: 0,
    )
    assert graph_calls == list(probe.GRAPH_SEEDS)
    assert len(decoder_calls) == 1
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert result["attempted_call_counts"] == {
        "pilot": 1, "holdout": 0, "total": 1
    }
    assert result["resource_violations"] == 1
    assert "decoder_call_wall_cap_after_return" in result["stop_reason"]
    root = repo / out_root
    with (root / "frame_records.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert "decoder_exception:RuntimeError" in rows[0]["status"]
    assert "resource_abort:" in rows[0]["status"]


@pytest.mark.parametrize("resource_case", ["rss_exception", "batch_wall"])
def test_postcall_rss_and_total_wall_caps_retain_row_and_stop(
        tmp_path, monkeypatch, resource_case
):
    repo, out_root = _test_repo(tmp_path)
    clock = {"value": 0.0}
    rss = {"value": 0}
    rss_reads = []
    graph_calls = []
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
        if resource_case == "batch_wall" and seed == probe.GRAPH_SEEDS[-1]:
            # Leave ten seconds of batch budget before the first fake call.
            clock["value"] = probe.WALL_CAP_S - 10.0
        return graph

    def decode(dense, prior, syndrome):
        decoder_calls.append(1)
        if resource_case == "rss_exception":
            assert rss["value"] < probe.RSS_CAP_BYTES
            rss["value"] = probe.RSS_CAP_BYTES + 1
            raise RuntimeError("fake_rss_overrun")
        assert clock["value"] == probe.WALL_CAP_S - 10.0
        clock["value"] += 20.0
        estimate = np.zeros(probe.N, dtype=np.int64)
        accepted = bool(np.array_equal(
            layout.gf32_syndrome(dense, estimate), syndrome
        ))
        return SimpleNamespace(
            x_hat=estimate, syndrome_ok=accepted,
            iterations=1, status="fake"
        )

    result = probe.execute_batch(
        out_root=out_root,
        decode_fn=decode,
        graph_builder=graph_builder,
        candidate_builder=lambda *args: pytest.fail(
            "resource cap should stop before candidate construction"
        ),
        repo_root=repo,
        now=lambda: clock["value"],
        rss_fn=rss_fn,
    )

    assert graph_calls == list(probe.GRAPH_SEEDS)
    assert len(decoder_calls) == 1
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert result["attempted_call_counts"] == {
        "pilot": 1, "holdout": 0, "total": 1
    }
    assert result["resource_violations"] == 1
    assert len(rss_reads) >= 1 and rss_reads[0] == 0

    root = repo / out_root
    with (root / "frame_records.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    if resource_case == "rss_exception":
        assert rss["value"] == probe.RSS_CAP_BYTES + 1
        assert "decoder_exception:RuntimeError" in rows[0]["status"]
        assert "resource_abort:rss_cap_after_call" in rows[0]["status"]
        assert int(rows[0]["rss_b"]) == probe.RSS_CAP_BYTES + 1
        assert "decoder_exception" in result["stop_reason"]
        assert "rss_cap_after_call" in result["stop_reason"]
    else:
        assert clock["value"] == probe.WALL_CAP_S + 10.0
        assert float(rows[0]["wall_s"]) == 20.0
        assert "resource_abort:total_wall_cap_after_call" in rows[0]["status"]
        assert "total_wall_cap_after_call" in result["stop_reason"]
        assert "decoder_call_wall_cap_after_return" not in rows[0]["status"]
        assert "decoder_call_wall_cap_after_return" not in result["stop_reason"]


def test_success_requires_exact_and_syndrome_and_wrong_is_separate():
    pmf = {"index": 0, "p0": probe.P0_GRID[0]}
    rows = []
    pairs = []
    for index in range(probe.HOLDOUT_PAIRS):
        graph_seed = probe.GRAPH_SEEDS[index // 32]
        stream = (index // 16) % 2
        frame = index % 16
        common = {
            "phase": "holdout", "pmf": pmf, "graph_seed": graph_seed,
            "stream": stream, "frame": frame, "seed": index,
        }
        control_exact = index != 0
        control_accept = index != 1
        control_wrong = not control_exact and control_accept
        candidate_exact = True
        candidate_accept = True
        rows.append(probe.predecessor._record_row(
            **common, call_index=2 * index + 1, arm="control",
            observed={
                "exact": control_exact,
                "syndrome_accept": control_accept,
                "syndrome_consistent_wrong": control_wrong,
                "status": "fake", "iterations": 1, "wall_s": 0.0,
                "rss_b": 0,
            },
        ))
        rows.append(probe.predecessor._record_row(
            **common, call_index=2 * index + 2, arm="candidate",
            observed={
                "exact": candidate_exact,
                "syndrome_accept": candidate_accept,
                "syndrome_consistent_wrong": False,
                "status": "fake", "iterations": 1, "wall_s": 0.0,
                "rss_b": 0,
            },
        ))
        pairs.append({
            "graph_seed": graph_seed, "stream": stream, "frame": frame,
            "control_exact": bool(control_exact and control_accept),
            "candidate_exact": True,
        })
    summary = probe._summarize(rows, pairs, [], "")
    assert summary["holdout_complete"] is True
    assert summary["control_exact"] == 190
    assert summary["candidate_exact"] == 192
    assert summary["delta"] == 2
    assert summary["syndrome_consistent_wrong_rows"] == 1
    assert summary["paired_states"]["candidate_only"] == 2

