"""Fake-only tests for the fixed-graph GF(32) search-depth EXPLORE runner."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_search_depth_probe as probe
from comparison_bench.cli import nbldpc_gf32_label_replica_probe as replica_runner
from comparison_bench.formal_ir import nbldpc_gf32_label_alignment as alignment
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout


def _fake_dense() -> np.ndarray:
    """A deterministic test matrix with the frozen 128/52/256 profile."""
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


def _fake_candidate_pair(h0: np.ndarray, pmf: np.ndarray,
                         graph_seed: int, *, deep_equal: bool = False):
    """Return two explicitly fake H0D candidates without production search."""
    onepass_labels = np.full(probe.N, 2, dtype=np.int64)
    deep_labels = onepass_labels.copy() if deep_equal else np.full(
        probe.N, 3, dtype=np.int64
    )
    onepass = alignment.scale_columns(h0, onepass_labels)
    deep = alignment.scale_columns(h0, deep_labels)
    diagnostic = {
        "graph_seed": int(graph_seed),
        "candidate_admitted": True,
        "deep_candidate_admitted": True,
        "construction_stop": False,
        "first_pass_match": True,
        "deep_support_equal": True,
        "deep_degrees_equal": True,
        "deep_gauge_equal": True,
        "deep_baseline_rank": probe.M,
        "deep_candidate_rank": probe.M,
        "onepass_labels": onepass_labels.tolist(),
        "deep_labels": deep_labels.tolist(),
        "onepass_J_bits": 1.0,
        "deep_J_bits": 1.0 if deep_equal else 2.0,
        "sweeps": [{
            "sweep": 1, "j_bits": 1.0 if deep_equal else 2.0,
            "changed_labels": 0 if deep_equal else 1,
            "j_drift_bits": 0.0, "reference_drift_bits": 0.0,
        }],
        "sweep_count": 1,
        "termination": "NO_CHANGE" if deep_equal else "MAX_SWEEPS",
        "search_saturated": bool(deep_equal),
    }
    return onepass, deep, diagnostic


def _test_repo(path: Path) -> tuple[Path, Path]:
    repo = path / "repo"
    (repo / "workspace").mkdir(parents=True)
    return repo, probe.OUT_ROOT_RELATIVE


def _assert_partial_unknowns(summary: dict) -> None:
    assert summary["holdout_complete"] is False
    assert summary["control_exact"] is None
    assert summary["candidate_exact"] is None
    assert summary["delta"] is None
    assert summary["paired_states"] is None
    assert set(summary["delta_by_graph"]) == {
        str(seed) for seed in probe.GRAPH_SEEDS
    }
    for graph in summary["delta_by_graph"].values():
        assert graph["control_exact"] is None
        assert graph["candidate_exact"] is None
        assert graph["delta_g"] is None


def _complete_rows(control_total: int, graph_deltas: list[int]):
    """Create deterministic in-memory paired rows for screen boundaries."""
    _, holdouts = probe.seed_plan()
    pmf = probe.shape_pmf_grid()[0]
    base, remainder = divmod(control_total, len(probe.GRAPH_SEEDS))
    control_counts = [base + (index < remainder)
                      for index in range(len(probe.GRAPH_SEEDS))]
    rows = []
    pairs = []
    for pair_index, (graph_seed, stream, frame, seed) in enumerate(holdouts):
        graph_index = graph_seed - probe.GRAPH_SEEDS[0]
        pair_slot = stream * probe.HOLDOUT_FRAMES_PER_STREAM + frame
        control_exact = pair_slot < control_counts[graph_index]
        candidate_exact = pair_slot < (
            control_counts[graph_index] + graph_deltas[graph_index]
        )
        # A syndrome-consistent wrong control estimate remains a failure.
        wrong = graph_index == 0 and pair_slot == 31
        for arm, exact, is_wrong in (
            ("control", control_exact, wrong),
            ("candidate", candidate_exact, False),
        ):
            rows.append(probe.fine_runner.predecessor._record_row(
                phase="holdout", pmf=pmf, graph_seed=graph_seed,
                stream=stream, frame=frame, seed=seed,
                call_index=2 * pair_index + (1 if arm == "control" else 2),
                arm=arm,
                observed={
                    "exact": bool(exact),
                    "syndrome_accept": bool(exact or is_wrong),
                    "syndrome_consistent_wrong": bool(is_wrong),
                    "status": "fake", "iterations": 1,
                    "wall_s": 0.0, "rss_b": 0,
                },
            ))
        pairs.append({
            "graph_seed": graph_seed, "stream": stream, "frame": frame,
            "control_exact": bool(control_exact),
            "candidate_exact": bool(candidate_exact),
        })
    return rows, pairs


def _install_tiny_onepass(monkeypatch, h0: np.ndarray, pmf: np.ndarray):
    labels = np.full(h0.shape[1], 2, dtype=np.int64)
    matrix = alignment.scale_columns(h0, labels)
    j0, _ = alignment.marginal_score(h0, pmf)
    jc, _ = alignment.marginal_score(matrix, pmf)

    def candidate_builder(dense, actual_pmf, graph_seed):
        assert int(graph_seed) == 17
        np.testing.assert_array_equal(dense, h0)
        np.testing.assert_array_equal(actual_pmf, pmf)
        return matrix.copy(), {
            "labels": labels.tolist(), "J0_bits": j0, "Jc_bits": jc,
            "candidate_admitted": True,
        }

    monkeypatch.setattr(probe, "_candidate_for_graph", candidate_builder)
    monkeypatch.setattr(probe.d10, "gf32_row_rank", lambda _matrix: probe.M)
    return labels, matrix, jc


def test_frozen_source_graph_seeds_namespace_and_pair_plan():
    grid = probe.shape_pmf_grid()
    assert len(grid) == 1
    assert grid[0]["index"] == 0
    assert grid[0]["p0"] == 0.55
    pmf = grid[0]["pmf"]
    assert np.flatnonzero(pmf).tolist() == [0, 1, 3, 7, 15, 31]
    assert pmf[0] == pytest.approx(0.55)
    assert float(pmf.sum()) == pytest.approx(1.0, abs=1e-12)
    for symbol, count in ((1, 2295), (3, 1126), (7, 557),
                          (15, 304), (31, 146)):
        assert pmf[symbol] == pytest.approx(0.45 * count / 4428, abs=1e-12)
    assert np.count_nonzero(pmf[2:]) == 4

    assert probe.GRAPH_SEEDS == tuple(range(2026093901, 2026093907))
    assert probe.SEED_PREFIX == "gf32-search-depth-v1"
    pilots, holdouts = probe.seed_plan()
    assert pilots == []
    assert len(holdouts) == probe.HOLDOUT_PAIRS == 192
    seeds = [row[3] for row in holdouts]
    assert len(set(seeds)) == 192
    assert holdouts[0] == (
        probe.GRAPH_SEEDS[0], 0, 0,
        probe.common.v10_seed(
            f"gf32-search-depth-v1:holdout:{probe.GRAPH_SEEDS[0]}:0:0"
        ),
    )
    old_seed_sets = []
    for old_plan in (
        probe.prior_runner._seed_plan(),
        probe.fine_runner.predecessor.seed_plan(),
        probe.fine_runner.seed_plan(),
        replica_runner.seed_plan(),
    ):
        old_seed_sets.extend(row[3] for group in old_plan for row in group)
    assert set(seeds).isdisjoint(old_seed_sets)
    assert probe.arm_order(0) == ("control", "candidate")
    assert probe.arm_order(1) == ("candidate", "control")
    assert probe.MAX_SWEEPS == 8
    assert probe.MAX_CALLS == 384


def test_absolute_coordinate_sweep_matches_accepted_first_pass_and_ties():
    h0 = np.asarray([[1, 2, 0], [3, 0, 5]], dtype=np.int64)
    pmf = probe.shape_pmf_grid()[0]["pmf"]
    expected = alignment.align_labels(h0, pmf)
    first = probe.coordinate_sweep(h0, pmf, np.ones(h0.shape[1], dtype=np.int64))
    np.testing.assert_array_equal(first["labels"], expected["labels"])
    np.testing.assert_array_equal(first["matrix"], expected["candidate"])
    assert first["J_bits"] == pytest.approx(expected["Jc"], abs=1e-12)
    assert first["changed_labels"] == int(np.count_nonzero(expected["labels"] != 1))

    # A uniform PMF makes every absolute beta tied. The current absolute D
    # must remain selected; beta is never interpreted as a multiplier of D.
    uniform = np.full(32, 1.0 / 32.0)
    current = np.asarray([2, 3, 7], dtype=np.int64)
    tied = probe.coordinate_sweep(h0, uniform, current)
    np.testing.assert_array_equal(tied["labels"], current)
    np.testing.assert_array_equal(
        tied["matrix"], alignment.scale_columns(h0, current)
    )
    assert tied["changed_labels"] == 0


def test_tiny_search_stops_on_no_change_and_retains_equal_candidate(monkeypatch):
    h0 = np.asarray([[1, 2, 0], [3, 0, 5]], dtype=np.int64)
    uniform = np.full(32, 1.0 / 32.0)
    labels, expected_onepass, _ = _install_tiny_onepass(
        monkeypatch, h0, uniform
    )
    onepass, deep, diagnostic = probe.build_candidate_pair(
        h0, uniform, graph_seed=17
    )
    np.testing.assert_array_equal(onepass, expected_onepass)
    np.testing.assert_array_equal(onepass, deep)
    assert diagnostic["onepass_labels"] == labels.tolist()
    assert diagnostic["first_pass_match"] is True
    assert diagnostic["termination"] == "NO_CHANGE"
    assert diagnostic["sweep_count"] == 2
    assert diagnostic["sweeps"][0]["changed_labels"] == h0.shape[1]
    assert diagnostic["sweeps"][1]["changed_labels"] == 0
    assert diagnostic["search_saturated"] is True
    assert diagnostic["deep_J_bits"] == pytest.approx(
        diagnostic["onepass_J_bits"], abs=1e-12
    )


def test_tiny_search_respects_eight_sweep_cap(monkeypatch):
    h0 = np.asarray([[1, 2, 0], [3, 0, 5]], dtype=np.int64)
    pmf = probe.shape_pmf_grid()[0]["pmf"]
    _, _, first_j = _install_tiny_onepass(monkeypatch, h0, pmf)
    sweep_calls = []

    def keep_changing(dense, actual_pmf, current_labels):
        labels = np.asarray(current_labels, dtype=np.int64).copy()
        labels[0] = labels[0] + 1 if labels[0] < 31 else 1
        matrix = alignment.scale_columns(dense, labels)
        sweep_calls.append(labels.copy())
        j_bits = first_j + len(sweep_calls)
        return {
            "labels": labels, "matrix": matrix,
            "J_bits": j_bits, "adjacent_J_bits": j_bits,
            "reference_drift_bits": 0.0, "changed_labels": 1,
        }

    monkeypatch.setattr(probe, "coordinate_sweep", keep_changing)
    onepass, deep, diagnostic = probe.build_candidate_pair(
        h0, pmf, graph_seed=17
    )
    assert len(sweep_calls) == probe.MAX_SWEEPS - 1
    assert diagnostic["sweep_count"] == probe.MAX_SWEEPS == 8
    assert len(diagnostic["sweeps"]) == 8
    assert diagnostic["termination"] == "MAX_SWEEPS"
    assert diagnostic["construction_stop"] is False
    assert diagnostic["search_saturated"] is False
    assert not np.array_equal(onepass, deep)
    np.testing.assert_array_equal(
        deep, alignment.scale_columns(h0, diagnostic["deep_labels"])
    )


def test_small_j_drift_is_recorded_without_rolling_back(monkeypatch):
    h0 = np.asarray([[1, 2, 0], [3, 0, 5]], dtype=np.int64)
    pmf = probe.shape_pmf_grid()[0]["pmf"]
    _, _, first_j = _install_tiny_onepass(monkeypatch, h0, pmf)
    call_index = {"value": 0}

    def tolerance_level_decrease(dense, actual_pmf, current_labels):
        labels = np.asarray(current_labels, dtype=np.int64).copy()
        call_index["value"] += 1
        if call_index["value"] == 1:
            labels[0] = labels[0] + 1
            changed = 1
            j_bits = first_j - 5e-11
        else:
            changed = 0
            j_bits = first_j - 5e-11
        return {
            "labels": labels,
            "matrix": alignment.scale_columns(dense, labels),
            "J_bits": j_bits, "adjacent_J_bits": j_bits,
            "reference_drift_bits": 0.0,
            "changed_labels": changed,
        }

    monkeypatch.setattr(probe, "coordinate_sweep", tolerance_level_decrease)
    onepass, deep, diagnostic = probe.build_candidate_pair(
        h0, pmf, graph_seed=17
    )
    assert diagnostic["construction_stop"] is False
    assert diagnostic["termination"] == "NO_CHANGE"
    assert diagnostic["sweeps"][1]["j_drift_bits"] == pytest.approx(-5e-11)
    assert diagnostic["deep_labels"][0] != diagnostic["onepass_labels"][0]
    assert not np.array_equal(onepass, deep)


@pytest.mark.parametrize("stop_kind", ["material_decrease", "reference_drift"])
def test_material_j_or_reference_drift_stops_construction(monkeypatch, stop_kind):
    h0 = np.asarray([[1, 2, 0], [3, 0, 5]], dtype=np.int64)
    pmf = probe.shape_pmf_grid()[0]["pmf"]
    _, onepass, first_j = _install_tiny_onepass(monkeypatch, h0, pmf)

    def drifting_sweep(dense, actual_pmf, current_labels):
        labels = np.asarray(current_labels, dtype=np.int64).copy()
        matrix = alignment.scale_columns(dense, labels)
        j_bits = first_j - 2e-10 if stop_kind == "material_decrease" else first_j
        ref_drift = 0.0 if stop_kind == "material_decrease" else 2e-10
        return {
            "labels": labels, "matrix": matrix,
            "J_bits": j_bits, "adjacent_J_bits": j_bits - ref_drift,
            "reference_drift_bits": ref_drift, "changed_labels": 0,
        }

    monkeypatch.setattr(probe, "coordinate_sweep", drifting_sweep)
    returned_onepass, deep, diagnostic = probe.build_candidate_pair(
        h0, pmf, graph_seed=17
    )
    np.testing.assert_array_equal(returned_onepass, onepass)
    assert diagnostic["construction_stop"] is True
    assert diagnostic["termination"] == "J_REFERENCE_DRIFT_STOP"
    assert diagnostic["sweep_count"] == 2
    # A STOP retains the computed state for diagnosis; it is not silently
    # replaced with a previous candidate.
    np.testing.assert_array_equal(deep, onepass)


@pytest.mark.parametrize(
    ("control_total", "graph_deltas", "classification"),
    [
        (39, [3, 3, 3, 3, 0, 0], "MECHANISM_SIGNAL"),
        (39, [3, 3, 3, 2, 0, 0], "NO_SUFFICIENT_SIGNAL"),
        (39, [4, 4, 4, 0, 0, 0], "NO_SUFFICIENT_SIGNAL"),
        (38, [3, 3, 3, 3, 0, 0], "CONTROL_RANGE_UNINFORMATIVE"),
        (153, [3, 3, 3, 3, 0, 0], "MECHANISM_SIGNAL"),
        (154, [3, 3, 3, 3, 0, 0], "CONTROL_RANGE_UNINFORMATIVE"),
    ],
)
def test_complete_summary_screen_boundaries_and_wrong_isolation(
        control_total, graph_deltas, classification
):
    rows, pairs = _complete_rows(control_total, graph_deltas)
    summary = probe._summarize(rows, pairs, "")
    assert summary["holdout_complete"] is True
    assert summary["holdout_pairs_completed"] == 192
    assert summary["control_exact"] == control_total
    assert summary["candidate_exact"] == control_total + sum(graph_deltas)
    assert summary["delta"] == sum(graph_deltas)
    assert [summary["delta_by_graph"][str(seed)]["delta_g"]
            for seed in probe.GRAPH_SEEDS] == graph_deltas
    assert sum(value["delta_g"] > 0
               for value in summary["delta_by_graph"].values()) == sum(
                   value > 0 for value in graph_deltas
               )
    assert sum(summary["paired_states"].values()) == 192
    assert summary["paired_states"]["both"] == control_total
    assert summary["paired_states"]["candidate_only"] == sum(graph_deltas)
    assert summary["paired_states"]["control_only"] == 0
    assert summary["paired_states"]["neither"] == (
        192 - control_total - sum(graph_deltas)
    )
    assert summary["syndrome_consistent_wrong_rows"] == 1
    assert summary["syndrome_consistent_wrong_by_arm"] == {
        "control": 1, "candidate": 0,
    }
    assert summary["integrity_violations"] == 0
    assert summary["resource_violations"] == 0
    assert summary["authorization_violations"] == 0
    assert summary["classification"] == classification
    assert summary["syndrome_bits_per_attempt"] == 260
    assert summary["tag_bits"] == 0
    assert summary["verification_status"] == "NOT_IMPLEMENTED"
    assert summary["undetected_status"] == "NOT_MEASURED"
    assert summary["FER"] is summary["f_eff"] is summary["SKR"] is None


def test_dry_run_is_no_write_and_frozen_root_is_refused(tmp_path, monkeypatch):
    repo, out_root = _test_repo(tmp_path)
    for obj, name, label in (
        (probe, "build_profile_graph", "graph construction"),
        (probe, "_candidate_for_graph", "one-pass candidate construction"),
        (probe, "_candidate_pair_for_graph", "deep candidate construction"),
        (probe.prior_runner, "sample_error", "sampled input"),
        (probe.prior_runner, "decode_observation", "decoder observation"),
        (probe.d10, "build_degree_sequence_peg", "D10 graph constructor"),
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
    assert result["pilot_seed_count"] == result["pilot_call_ceiling"] == 0
    assert result["holdout_pair_count"] == 192
    assert result["holdout_call_count"] == result["maximum_call_count"] == 384
    assert result["max_total_label_sweeps_per_graph"] == 8
    assert result["holdout_seeds_disjoint_from_prior_batches"] is True
    assert not (repo / out_root).exists()

    assert probe.validate_out_root(out_root, repo_root=repo) == repo / out_root
    with pytest.raises(ValueError, match="frozen fresh root"):
        probe.validate_out_root("workspace/unrelated", repo_root=repo)
    (repo / out_root).mkdir()
    with pytest.raises(FileExistsError, match="refusing existing output root"):
        probe.validate_out_root(out_root, repo_root=repo)


@pytest.mark.parametrize("deep_equal", [False, True])
def test_full_fake_pairing_alternates_and_never_shortcuts_equal_candidates(
        tmp_path, monkeypatch, deep_equal
):
    repo, out_root = _test_repo(tmp_path)
    _, holdouts = probe.seed_plan()
    holdout_by_seed = {
        seed: (graph_seed, stream, frame)
        for graph_seed, stream, frame, seed in holdouts
    }
    current = {"graph_seed": None, "stream": None, "frame": None,
               "truth": None, "arm_index": 0}
    graphs = {}
    candidate_matrices = {}
    graph_calls = []
    candidate_calls = []
    decoder_calls = []
    pair_checks = []
    arm_orders = []
    decoded_arm_order = []

    def sample(seed, pmf, width=probe.N):
        graph_seed, stream, frame = holdout_by_seed[seed]
        truth = np.zeros(width, dtype=np.int64)
        truth[0] = 1
        current.update(graph_seed=graph_seed, stream=stream,
                       frame=frame, truth=truth.copy(), arm_index=0)
        np.testing.assert_array_equal(pmf, probe.shape_pmf_grid()[0]["pmf"])
        return truth

    monkeypatch.setattr(probe.prior_runner, "sample_error", sample)

    def graph_builder(seed):
        graph_calls.append(seed)
        graph = _fake_graph(seed)
        graphs[seed] = graph["dense"].copy()
        return graph

    def candidate_builder(dense, pmf, graph_seed):
        candidate_calls.append(graph_seed)
        onepass, deep, diagnostic = _fake_candidate_pair(
            dense, pmf, graph_seed, deep_equal=deep_equal
        )
        candidate_matrices[graph_seed] = (onepass.copy(), deep.copy())
        return onepass, deep, diagnostic

    original_pair = probe.prior_runner.paired_arm_data

    def inspect_pair(onepass, deep, truth, prior):
        pair = original_pair(onepass, deep, truth, prior)
        np.testing.assert_array_equal(pair["control"]["truth"], truth)
        np.testing.assert_array_equal(pair["candidate"]["truth"], truth)
        assert pair["control"]["prior"] is prior
        assert pair["candidate"]["prior"] is prior
        np.testing.assert_array_equal(
            pair["control"]["syndrome"], layout.gf32_syndrome(onepass, truth)
        )
        np.testing.assert_array_equal(
            pair["candidate"]["syndrome"], layout.gf32_syndrome(deep, truth)
        )
        if not deep_equal:
            assert not np.array_equal(
                pair["control"]["syndrome"],
                pair["candidate"]["syndrome"],
            )
        pair_checks.append(True)
        return pair

    monkeypatch.setattr(probe.prior_runner, "paired_arm_data", inspect_pair)
    original_order = probe.arm_order

    def record_order(frame):
        order = original_order(frame)
        arm_orders.append((current["graph_seed"], current["stream"], frame, order))
        return order

    monkeypatch.setattr(probe, "arm_order", record_order)
    for obj, name, label in (
        (probe, "build_profile_graph", "production graph builder"),
        (probe, "_candidate_for_graph", "production one-pass candidate"),
        (probe, "_candidate_pair_for_graph", "production search builder"),
        (probe.d10, "build_degree_sequence_peg", "D10 graph constructor"),
    ):
        monkeypatch.setattr(
            obj, name,
            lambda *args, _label=label, **kwargs: pytest.fail(
                f"fake execute reached {_label}"
            ),
        )

    def fake_decode(dense, prior, syndrome):
        decoder_calls.append(1)
        np.testing.assert_array_equal(
            prior[0], probe.shape_pmf_grid()[0]["pmf"]
        )
        truth = current["truth"]
        np.testing.assert_array_equal(
            syndrome, layout.gf32_syndrome(dense, truth)
        )
        expected_arm = original_order(current["frame"])[current["arm_index"]]
        current["arm_index"] += 1
        if not deep_equal:
            onepass, deep = candidate_matrices[current["graph_seed"]]
            if np.array_equal(dense, onepass):
                actual_arm = "control"
            else:
                np.testing.assert_array_equal(dense, deep)
                actual_arm = "candidate"
            assert actual_arm == expected_arm
            decoded_arm_order.append(actual_arm)
        return SimpleNamespace(
            x_hat=truth.copy(), syndrome_ok=True,
            iterations=1, status="fake",
        )

    result = probe.execute_batch(
        out_root=out_root, decode_fn=fake_decode, graph_builder=graph_builder,
        candidate_builder=candidate_builder, repo_root=repo,
        now=lambda: 0.0, rss_fn=lambda: 0,
    )

    assert graph_calls == list(probe.GRAPH_SEEDS)
    assert candidate_calls == list(probe.GRAPH_SEEDS)
    assert len(decoder_calls) == probe.MAX_CALLS == 384
    assert len(pair_checks) == probe.HOLDOUT_PAIRS == 192
    assert len(arm_orders) == 192
    if not deep_equal:
        assert len(decoded_arm_order) == 384
        assert decoded_arm_order[:4] == ["control", "candidate",
                                         "candidate", "control"]
    assert all(order == original_order(frame)
               for _, _, frame, order in arm_orders)
    assert [order for _, _, frame, order in arm_orders[:2]] == [
        original_order(0), original_order(1)
    ]
    assert result["holdout_complete"] is True
    assert result["attempted_call_counts"] == {
        "pilot": 0, "holdout": 384, "total": 384,
    }
    assert result["control_exact"] == result["candidate_exact"] == 192
    assert result["delta"] == 0
    assert result["classification"] == "CONTROL_RANGE_UNINFORMATIVE"
    assert result["actual_syndrome_disclosure_bits"] == 384 * 260
    assert result["syndrome_bits_per_attempt"] == 260
    assert result["verification_status"] == "NOT_IMPLEMENTED"
    assert result["undetected_status"] == "NOT_MEASURED"
    assert result["FER"] is result["f_eff"] is result["SKR"] is None
    assert result["search_saturated"] is deep_equal
    assert result["search_by_graph"]
    assert [result["delta_by_graph"][str(seed)]["delta_g"]
            for seed in probe.GRAPH_SEEDS] == [0] * 6
    assert [result["delta_by_graph"][str(seed)]["completed_pairs"]
            for seed in probe.GRAPH_SEEDS] == [32] * 6

    root = repo / out_root
    assert sorted(path.name for path in root.iterdir()) == [
        "EXPLORATION_LOG.md", "frame_records.csv", "manifest.json",
        "summary.json",
    ]
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["batch_uuid"] == probe.BATCH_UUID
    assert manifest["seed_namespace"] == probe.SEED_PREFIX
    assert manifest["graph_profile"]["graph_seeds"] == list(probe.GRAPH_SEEDS)
    assert manifest["label_search"]["max_total_sweeps"] == 8
    assert manifest["budgets"]["max_decoder_calls"] == 384
    assert manifest["arm_mapping"] == {
        "control": "accepted onepass H0D",
        "candidate": "deep H0D, up to eight total sweeps",
    }
    with (root / "frame_records.csv").open(newline="") as stream:
        records = list(csv.DictReader(stream))
    assert len(records) == 384
    assert {row["phase"] for row in records} == {"holdout"}
    assert {int(row["syndrome_bits"]) for row in records} == {260}
    assert {int(row["graph_seed"]) for row in records} == set(probe.GRAPH_SEEDS)
    assert not ({"truth", "prior", "truth_array", "prior_array"}
                & set(records[0]))


def test_graph_and_search_admission_stops_keep_comparison_unknown(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path / "graph-stop")
    graph_calls = []
    candidate_calls = []
    decoder_calls = []

    def bad_graph(seed):
        graph_calls.append(seed)
        graph = _fake_graph(seed)
        if seed == probe.GRAPH_SEEDS[0]:
            graph["dense"][0, 0] = 0
        return graph

    graph_result = probe.execute_batch(
        out_root=out_root,
        decode_fn=lambda *args: decoder_calls.append(1),
        graph_builder=bad_graph,
        candidate_builder=lambda *args: candidate_calls.append(1),
        repo_root=repo, now=lambda: 0.0, rss_fn=lambda: 0,
    )
    assert graph_result["terminal_status"] == "GRAPH_PREFLIGHT_FAILED"
    assert graph_result["attempted_call_counts"] == {
        "pilot": 0, "holdout": 0, "total": 0,
    }
    assert graph_calls == list(probe.GRAPH_SEEDS)
    assert candidate_calls == decoder_calls == []
    _assert_partial_unknowns(graph_result)

    repo2, out_root2 = _test_repo(tmp_path / "candidate-stop")
    candidate_calls = []

    def rejected_candidate(dense, pmf, graph_seed):
        candidate_calls.append(graph_seed)
        return None, None, {
            "graph_seed": graph_seed,
            "candidate_admitted": False,
            "deep_candidate_admitted": False,
            "construction_stop": False,
            "failure_reason": "fake onepass admission stop",
        }

    candidate_result = probe.execute_batch(
        out_root=out_root2, decode_fn=lambda *args: decoder_calls.append(1),
        graph_builder=_fake_graph, candidate_builder=rejected_candidate,
        repo_root=repo2, now=lambda: 0.0, rss_fn=lambda: 0,
    )
    assert candidate_result["terminal_status"] == \
        "NO_NONTRIVIAL_LABEL_CANDIDATE"
    assert candidate_result["attempted_call_counts"] == {
        "pilot": 0, "holdout": 0, "total": 0,
    }
    assert candidate_calls == [probe.GRAPH_SEEDS[0]]
    assert decoder_calls == []
    _assert_partial_unknowns(candidate_result)


def test_partial_pair_plus_orphan_keeps_rows_but_masks_all_aggregates(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path)
    _, holdouts = probe.seed_plan()
    holdout_by_seed = {
        seed: (graph_seed, stream, frame)
        for graph_seed, stream, frame, seed in holdouts
    }
    current = {"truth": None}
    decoder_calls = []
    monkeypatch.setattr(
        probe.prior_runner, "sample_error",
        lambda seed, pmf, width=probe.N: (
            current.update(truth=np.zeros(width, dtype=np.int64))
            or np.zeros(width, dtype=np.int64)
        ),
    )

    def decode(dense, prior, syndrome):
        decoder_calls.append(1)
        truth = current["truth"]
        return SimpleNamespace(
            x_hat=truth.copy(),
            syndrome_ok=bool(np.array_equal(
                layout.gf32_syndrome(dense, truth), syndrome)),
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
        candidate_builder=lambda h, p, seed: _fake_candidate_pair(
            h, p, seed, deep_equal=False
        ),
        repo_root=repo, now=lambda: 0.0, rss_fn=lambda: 0,
    )
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert result["stop_reason"] == "total_wall_cap_before_next_call"
    assert result["attempted_call_counts"] == {
        "pilot": 0, "holdout": 3, "total": 3,
    }
    assert result["holdout_pairs_completed"] == 1
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
        "control", "candidate", "candidate",
    ]


@pytest.mark.parametrize(
    ("resource_case", "expected_reason", "expected_wall"),
    [
        ("call_wall", "decoder_call_wall_cap_after_return", 121.0),
        ("total_wall", "total_wall_cap_after_call", 20.0),
        ("rss", "rss_cap_after_call", 0.0),
    ],
)
def test_exception_after_resource_overrun_retains_row_and_stops(
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
        lambda seed, pmf, width=probe.N: np.zeros(width, dtype=np.int64),
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
        return _fake_candidate_pair(dense, pmf, graph_seed, deep_equal=False)

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
        "pilot": 0, "holdout": 1, "total": 1,
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


def test_resource_gates_stop_before_the_next_operation():
    assert probe._resource_stop(
        0.0, now=lambda: probe.WALL_CAP_S, rss_fn=lambda: 0
    ) == "total_wall_cap_before_next_call"
    assert probe._resource_stop(
        0.0, now=lambda: 0.0,
        rss_fn=lambda: probe.RSS_CAP_BYTES,
    ) == "rss_cap_before_next_call"

