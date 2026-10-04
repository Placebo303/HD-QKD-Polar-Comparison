"""Focused fake-only tests for the matched GF32 degree-profile probe."""
from __future__ import annotations

import csv
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_degree_probe as probe
from comparison_bench.formal_ir import v72p2d10_mixed_degree_l1 as d10
from comparison_bench.formal_ir import nbldpc_gf32_label_alignment as alignment
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from comparison_bench.formal_ir import nonbinary_v10_common as common


def _profile_edges(profile_id: str) -> list[tuple[int, int]]:
    """Build tiny deterministic incidence fixtures with the frozen profiles."""
    if profile_id == "control":
        # A 52-check cycle makes the Tanner incidence connected.  Its 52
        # degree-two variables leave the exact 4/5 check-degree residuals.
        edges = []
        for row in range(52):
            edges.extend(((row, row), (row, (row + 1) % 52)))
        residual = [2] * 4 + [3] * 48
        for variable in range(52, 128):
            left = max(range(52), key=lambda row: (residual[row], -row))
            residual[left] -= 1
            right = max((row for row in range(52) if row != left),
                        key=lambda row: (residual[row], -row))
            residual[right] -= 1
            edges.extend(((variable, left), (variable, right)))
        assert residual == [0] * 52
    elif profile_id == "candidate":
        # Three cyclic offsets cover all checks; the resulting row histogram
        # is 32 degree-seven and 20 degree-eight checks.
        edges = [
            (variable, (variable + offset) % 52)
            for variable in range(128)
            for offset in (0, 17, 34)
        ]
    else:
        raise AssertionError(f"unknown test profile {profile_id!r}")
    return sorted(edges)


def _graph_record(profile: dict, graph_seed: int) -> dict:
    """Make a fake graph record, using only D10's pure structure checker."""
    edges = _profile_edges(str(profile["profile_id"]))
    coefficient_seed = 112233 if profile["profile_id"] == "control" else 445566
    coefficients = np.random.default_rng(coefficient_seed).integers(
        1, 32, size=len(edges), dtype=np.int64)
    h = d10.dense_from_edges(128, 52, edges, coefficients)
    structure = d10.structural_record(
        h, profile["variable_counts"], profile["check_counts"])
    assert structure["gf32_rank"] == 52
    assert structure["connected_components"] == 1
    assert structure["admitted"] is True
    return {
        "profile_id": profile["profile_id"], "graph_seed": int(graph_seed),
        "n": 128, "m": 52, "E": len(edges), "edges": edges,
        "coefficients": coefficients.tolist(), "H": h,
        "structure": structure, "status": "ok", "admitted": True,
        "failure_reason": "",
    }


def _scaled_pair(h: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    labels_one = np.ones(128, dtype=np.int64)
    labels_one[0] = 2
    labels_deep = labels_one.copy()
    labels_deep[1] = 3
    return (alignment.scale_columns(h, labels_one),
            alignment.scale_columns(h, labels_deep))


def _fake_builders():
    """Explicit synthetic graph/label seams for execute_batch tests."""
    graphs: dict[str, dict] = {}
    graph_calls: list[tuple[str, int]] = []
    candidate_calls: list[tuple[int, np.ndarray, np.ndarray]] = []

    def graph_builder(profile: dict, graph_seed: int) -> dict:
        profile_id = str(profile["profile_id"])
        if profile_id not in graphs:
            graphs[profile_id] = _graph_record(profile, graph_seed)
        graph_calls.append((profile_id, int(graph_seed)))
        return {**graphs[profile_id], "graph_seed": int(graph_seed)}

    def candidate_builder(h: np.ndarray, pmf: np.ndarray, graph_seed: int):
        onepass, deep = _scaled_pair(np.asarray(h))
        candidate_calls.append((int(graph_seed), onepass.copy(), deep.copy()))
        diagnostics = {
            "construction_stop": False,
            "candidate_admitted": True,
            "deep_candidate_admitted": True,
            "deep_baseline_rank": d10.gf32_row_rank(h),
            "deep_candidate_rank": d10.gf32_row_rank(deep),
            "deep_support_equal": bool(np.array_equal(h != 0, deep != 0)),
            "deep_degrees_equal": bool(
                np.array_equal(np.count_nonzero(h, axis=0),
                               np.count_nonzero(deep, axis=0))
                and np.array_equal(np.count_nonzero(h, axis=1),
                                   np.count_nonzero(deep, axis=1))),
            "deep_gauge_equal": True,
        }
        return onepass, deep, diagnostics

    return graph_builder, candidate_builder, graph_calls, candidate_calls


def _fake_decode(call_log: list[dict], arm: str):
    """Truth-blind decoder fake returning the zero word and its actual flag."""
    def decode(h: np.ndarray, prior: np.ndarray, syndrome: np.ndarray):
        x_hat = np.zeros(128, dtype=np.int64)
        call_log.append({"arm": arm, "H": h.copy(), "prior": prior.copy(),
                         "syndrome": syndrome.copy()})
        return SimpleNamespace(
            x_hat=x_hat,
            syndrome_ok=bool(layout.syndrome_ok(h, x_hat, syndrome)),
            iterations=90,
            status="fake_at_cap",
        )
    return decode


def _fresh_test_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                     name: str) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    (repo / "workspace").mkdir(parents=True)
    root_relative = Path("workspace") / name
    monkeypatch.setattr(probe, "OUT_ROOT_RELATIVE", root_relative)
    return repo, root_relative


def _diagnostic_artifacts(root: Path) -> dict:
    with np.load(root / "diagnostics.npz", allow_pickle=False) as loaded:
        return {key: loaded[key].copy() for key in loaded.files}


def test_frozen_profile_matrices_and_deep_coefficients_are_distinct():
    control_spec = probe.PROFILES["control"]
    candidate_spec = probe.PROFILES["candidate"]
    control = _graph_record(control_spec, probe.GRAPH_SEEDS[0])
    candidate = _graph_record(candidate_spec, probe.GRAPH_SEEDS[0])
    control_onepass, control_deep = _scaled_pair(control["H"])
    candidate_onepass, candidate_deep = _scaled_pair(candidate["H"])

    assert probe.PROFILE_ORDER == ("control", "candidate")
    assert control["E"] == 256 and candidate["E"] == 384
    assert control["structure"]["variable_degree_histogram"] == {2: 128}
    assert control["structure"]["check_degree_histogram"] == {4: 4, 5: 48}
    assert candidate["structure"]["variable_degree_histogram"] == {3: 128}
    assert candidate["structure"]["check_degree_histogram"] == {7: 32, 8: 20}
    assert not np.array_equal(control["H"], candidate["H"])
    for base, onepass, deep in (
            (control["H"], control_onepass, control_deep),
            (candidate["H"], candidate_onepass, candidate_deep)):
        assert not np.array_equal(base, onepass)
        assert not np.array_equal(base, deep)
        assert not np.array_equal(onepass, deep)
        assert d10.gf32_row_rank(deep) == 52


def test_profile_preflight_uses_selected_histograms_rank_and_coefficients():
    control_spec = probe.PROFILES["control"]
    candidate_spec = probe.PROFILES["candidate"]
    control = _graph_record(control_spec, probe.GRAPH_SEEDS[0])
    candidate = _graph_record(candidate_spec, probe.GRAPH_SEEDS[0])

    for spec, graph in ((control_spec, control), (candidate_spec, candidate)):
        admitted, diagnostic = probe.profile_preflight(
            spec, graph, probe.GRAPH_SEEDS[0])
        assert admitted
        assert all(diagnostic["checks"].values())

    admitted, wrong_profile = probe.profile_preflight(
        candidate_spec, control, probe.GRAPH_SEEDS[0])
    assert not admitted
    assert not wrong_profile["checks"]["profile_id"]
    assert not wrong_profile["checks"]["edge_count"]
    assert not wrong_profile["checks"]["variable_histogram"]

    bad_rank = deepcopy(candidate)
    bad_rank["structure"]["gf32_rank"] = 51
    admitted, rank_diagnostic = probe.profile_preflight(
        candidate_spec, bad_rank, probe.GRAPH_SEEDS[0])
    assert not admitted
    assert not rank_diagnostic["checks"]["gf32_rank"]

    bad_coeff = deepcopy(control)
    bad_coeff["coefficients"][0] = 0
    admitted, coefficient_diagnostic = probe.profile_preflight(
        control_spec, bad_coeff, probe.GRAPH_SEEDS[0])
    assert not admitted
    assert not coefficient_diagnostic["checks"]["nonzero_coefficients"]


def test_new_frame_seed_namespace_and_alternating_pair_order():
    plan = probe.seed_plan()
    assert probe.GRAPH_SEEDS == tuple(range(2026093901, 2026093907))
    assert len(plan) == probe.HOLDOUT_PAIRS == 192
    assert len({(graph, stream, frame) for graph, stream, frame, _ in plan}) == 192
    assert len({seed for _, _, _, seed in plan}) == 192
    for graph, stream, frame, seed in plan:
        expected = common.v10_seed(
            f"gf32-degree-v1:holdout:{graph}:{stream}:{frame}")
        assert seed == expected
    assert probe.arm_order(0) == ("control", "candidate")
    assert probe.arm_order(1) == ("candidate", "control")


def test_t0_and_dry_run_do_not_touch_graphs_or_artifacts(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    checks = probe.verify_t0()
    assert checks["degree_profiles_fixed"]
    assert checks["degree_pmf_exact"]
    assert checks["degree_seed_plan_disjoint"]
    assert checks["edge_update_proxy_cap"]
    assert probe.EDGE_UPDATE_PROXY_CAP == 11_059_200

    repo = tmp_path / "repo"
    (repo / "workspace").mkdir(parents=True)
    root_relative = Path("workspace") / "degree-dry-run"
    monkeypatch.setattr(probe, "OUT_ROOT_RELATIVE", root_relative)
    result = probe.dry_run(root_relative, repo_root=repo)
    assert result["status"] == "DRY_RUN"
    assert result["writes"] == 0
    assert result["artifact_reads"] == 0
    assert result["graph_build_calls"] == 0
    assert result["label_calls"] == 0
    assert result["decoder_calls"] == 0
    assert result["holdout_pairs"] == 192
    assert result["maximum_decoder_calls"] == 384
    assert not (repo / root_relative).exists()


def test_output_root_refuses_existing_target(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = tmp_path / "repo"
    root_relative = Path("workspace") / "degree-existing"
    target = repo / root_relative
    target.mkdir(parents=True)
    monkeypatch.setattr(probe, "OUT_ROOT_RELATIVE", root_relative)
    with pytest.raises(FileExistsError):
        probe.validate_out_root(root_relative, repo_root=repo)


def test_fake_entry_runs_192_pairs_and_rechecks_profile_vector_lineage(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo, root_relative = _fresh_test_root(tmp_path, monkeypatch, "degree-full")
    graph_builder, candidate_builder, graph_calls, candidate_calls = _fake_builders()
    decoder_calls: list[dict] = []
    sampled: list[tuple[int, np.ndarray]] = []
    real_sampler = probe.prior_runner.sample_error

    def sampler_spy(seed: int, pmf: np.ndarray, width: int = 128):
        truth = real_sampler(seed, pmf, width=width)
        sampled.append((int(seed), np.asarray(truth).copy()))
        return truth

    monkeypatch.setattr(probe.prior_runner, "sample_error", sampler_spy)
    summary = probe.execute_batch(
        out_root=root_relative,
        repo_root=repo,
        decode_fns={"control": _fake_decode(decoder_calls, "control"),
                    "candidate": _fake_decode(decoder_calls, "candidate")},
        graph_builder=graph_builder,
        candidate_builder=candidate_builder,
        profile_preflight_fn=probe.profile_preflight,
        rss_fn=lambda: 0,
        command="fake-only test entry",
    )

    root = repo / root_relative
    assert summary["complete"] is True
    assert summary["terminal_status"] == "COMPLETE"
    assert summary["batch_uuid"] == probe.BATCH_UUID
    assert summary["contract"] == probe.CONTRACT
    assert summary["seed_namespace"] == probe.SEED_PREFIX
    assert summary["attempted_decoder_calls"] == 384
    assert summary["attempted_frame_rows"] == 384
    assert len(graph_calls) == 12
    assert len(candidate_calls) == 12
    assert len(sampled) == 192
    assert len({seed for seed, _ in sampled}) == 192
    assert len(decoder_calls) == 384
    assert summary["attempted_edge_update_proxy"] == {
        "control": 4_423_680, "candidate": 6_635_520}
    assert summary["edge_update_proxy"] == summary["attempted_edge_update_proxy"]
    assert summary["edge_update_proxy_is_measured_operations"] is False
    assert {"manifest.json", "frame_records.csv", "summary.json",
            "diagnostics.npz", "EXPLORATION_LOG.md"} == {
                path.name for path in root.iterdir()}

    with (root / "frame_records.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    arrays = _diagnostic_artifacts(root)
    assert len(rows) == 384
    assert all(row["batch_uuid"] == probe.BATCH_UUID for row in rows)
    assert all(row["contract"] == probe.CONTRACT for row in rows)
    assert all(row["seed_namespace"] == probe.SEED_PREFIX for row in rows)
    assert arrays["batch_uuid"].tolist() == [probe.BATCH_UUID]
    assert arrays["contract"].tolist() == [probe.CONTRACT]
    assert arrays["seed_namespace"].tolist() == [probe.SEED_PREFIX]
    assert arrays["profile_order"].tolist() == ["control", "candidate"]
    assert arrays["pair_index"].tolist() == list(range(192))
    assert arrays["pair_truth"].shape == (192, 128)
    assert arrays["pair_syndrome"].shape == (192, 2, 52)
    assert arrays["H_constructor"].shape == (12, 52, 128)
    assert arrays["H_deep"].shape == (12, 52, 128)
    assert arrays["raw_x_hat"].shape == (384, 128)
    assert arrays["call_vector_index"].tolist() == list(range(384))
    assert arrays["vector_call_index"].tolist() == list(range(384))
    with (root / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    assert manifest["batch_uuid"] == probe.BATCH_UUID
    assert manifest["contract"] == probe.CONTRACT
    assert manifest["seed_namespace"] == probe.SEED_PREFIX
    log = (root / "EXPLORATION_LOG.md").read_text(encoding="utf-8")
    assert probe.BATCH_UUID in log
    assert probe.CONTRACT in log
    assert probe.SEED_PREFIX in log
    assert [int(row["seed"]) for row in rows[::2]] == [
        int(row["seed"]) for row in rows[1::2]]
    for pair_index, ((graph_seed, stream_id, frame_id, seed),
                     (sampled_seed, truth)) in enumerate(zip(
                         probe.seed_plan(), sampled)):
        assert sampled_seed == seed
        assert int(arrays["pair_graph_seed"][pair_index]) == graph_seed
        assert int(arrays["graph_seed"][arrays["pair_graph_index"][pair_index]]) == graph_seed
        assert int(arrays["pair_stream"][pair_index]) == stream_id
        assert int(arrays["pair_frame"][pair_index]) == frame_id
        assert int(arrays["pair_seed"][pair_index]) == seed
        assert np.array_equal(arrays["pair_truth"][pair_index], truth)
        expected_order = probe.arm_order(frame_id)
        pair_rows = rows[2 * pair_index:2 * pair_index + 2]
        assert tuple(row["arm"] for row in pair_rows) == expected_order
        assert all(row["profile_id"] == row["arm"] for row in pair_rows)
        assert np.array_equal(
            arrays["pair_syndrome"][pair_index, 0],
            layout.gf32_syndrome(
                arrays["H_deep"][
                    np.flatnonzero((arrays["deep_profile_index"] == 0)
                                   & (arrays["deep_graph_index"] ==
                                      arrays["pair_graph_index"][pair_index]))[0]],
                truth))
        assert np.array_equal(
            arrays["pair_syndrome"][pair_index, 1],
            layout.gf32_syndrome(
                arrays["H_deep"][
                    np.flatnonzero((arrays["deep_profile_index"] == 1)
                                   & (arrays["deep_graph_index"] ==
                                      arrays["pair_graph_index"][pair_index]))[0]],
                truth))
        for arm_index, arm in enumerate(("control", "candidate")):
            graph_index = int(arrays["pair_graph_index"][pair_index])
            constructor_i = np.flatnonzero(
                (arrays["constructor_profile_index"] == arm_index)
                & (arrays["constructor_graph_index"] == graph_index))[0]
            deep_i = np.flatnonzero(
                (arrays["deep_profile_index"] == arm_index)
                & (arrays["deep_graph_index"] == graph_index))[0]
            assert not np.array_equal(arrays["H_constructor"][constructor_i],
                                      arrays["H_deep"][deep_i])
            call_index = 2 * pair_index + expected_order.index(arm)
            call = decoder_calls[call_index]
            row = rows[call_index]
            assert call["arm"] == arm
            assert np.array_equal(call["H"], arrays["H_deep"][deep_i])
            assert np.array_equal(
                call["syndrome"], arrays["pair_syndrome"][pair_index, arm_index])
            assert np.array_equal(
                call["prior"], np.tile(probe.search_runner.shape_pmf_grid()[0]["pmf"],
                                        (128, 1)))
            assert row["raw_vector_saved"] == "True"
            vector_index = int(arrays["call_vector_index"][call_index])
            raw = arrays["raw_x_hat"][vector_index]
            exact_raw = bool(np.array_equal(raw, truth))
            syndrome_ok = bool(layout.syndrome_ok(
                call["H"], raw, arrays["pair_syndrome"][pair_index, arm_index]))
            assert (row["raw_symbols_equal"] == "True") is exact_raw
            assert (row["syndrome_accept"] == "True") is syndrome_ok
            assert (row["base_syndrome_accept"] == "True") is syndrome_ok
            assert (row["exact"] == "True") is (exact_raw and syndrome_ok)
            assert (row["syndrome_consistent_wrong"] == "True") is (
                syndrome_ok and not exact_raw)
            assert 0 <= int(row["iterations"]) <= 90
            if not syndrome_ok:
                assert int(row["iterations"]) == 90


def test_summary_keeps_valid_wrong_separate_and_uses_control_range_screen():
    rows = [
        {"pair_index": 0, "graph_seed": probe.GRAPH_SEEDS[0], "arm": "control",
         "exact": False, "syndrome_accept": False,
         "base_syndrome_accept": False, "syndrome_consistent_wrong": False,
         "iterations": 90, "wall_s": 0.0, "rss_b": 0},
        {"pair_index": 0, "graph_seed": probe.GRAPH_SEEDS[0], "arm": "candidate",
         "exact": True, "syndrome_accept": True,
         "base_syndrome_accept": True, "syndrome_consistent_wrong": False,
         "iterations": 7, "wall_s": 0.0, "rss_b": 0},
        {"pair_index": 1, "graph_seed": probe.GRAPH_SEEDS[0], "arm": "control",
         "exact": False, "syndrome_accept": False,
         "base_syndrome_accept": False, "syndrome_consistent_wrong": False,
         "iterations": 90, "wall_s": 0.0, "rss_b": 0},
        {"pair_index": 1, "graph_seed": probe.GRAPH_SEEDS[0], "arm": "candidate",
         "exact": False, "syndrome_accept": True,
         "base_syndrome_accept": True, "syndrome_consistent_wrong": True,
         "iterations": 11, "wall_s": 0.0, "rss_b": 0},
    ]
    summary = probe.base_runner._summarize(rows, expected_pairs=2)

    assert summary["complete"] is True
    assert summary["classification"] == "CONTROL_RANGE_UNINFORMATIVE"
    assert summary["control_exact"] == 0
    assert summary["candidate_exact"] == 1
    assert summary["paired"] == {
        "both": 0, "control_only": 0, "candidate_only": 1, "neither": 1}
    assert summary["per_arm_outcomes"]["candidate"]["exact_and_syndrome"] == 1
    assert summary["per_arm_outcomes"]["candidate"]["syndrome_valid_wrong"] == 1
    assert summary["transitions"]["control_raw_fail_to_candidate_exact"] == 1
    assert summary["transitions"]["control_raw_fail_to_candidate_valid_wrong"] == 1


def test_profile_admission_stop_retains_matrices_and_never_falls_back_to_BP(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo, root_relative = _fresh_test_root(tmp_path, monkeypatch, "degree-admission")
    graph_builder, candidate_builder, graph_calls, candidate_calls = _fake_builders()
    decoder_calls: list[dict] = []
    preflight_calls: list[str] = []

    def rejecting_preflight(profile: dict, graph: dict, graph_seed: int):
        preflight_calls.append(str(profile["profile_id"]))
        admitted, diagnostic = probe.profile_preflight(profile, graph, graph_seed)
        if profile["profile_id"] == "candidate":
            return False, {"checks": diagnostic["checks"], "fixture_rejection": True}
        return admitted, diagnostic

    summary = probe.execute_batch(
        out_root=root_relative, repo_root=repo,
        decode_fns={"control": _fake_decode(decoder_calls, "control"),
                    "candidate": _fake_decode(decoder_calls, "candidate")},
        graph_builder=graph_builder, candidate_builder=candidate_builder,
        profile_preflight_fn=rejecting_preflight, rss_fn=lambda: 0,
        command="fake profile admission stop",
    )

    root = repo / root_relative
    assert summary["terminal_status"] == "STOP"
    assert summary["complete"] is False
    assert summary["per_arm_outcomes"] is None
    assert summary["stop_reason"].startswith("profile_construction_or_admission_stop:")
    assert preflight_calls == ["control", "candidate"]
    assert len(graph_calls) == 2
    assert candidate_calls == []
    assert decoder_calls == []
    arrays = _diagnostic_artifacts(root)
    assert arrays["H_constructor"].shape == (2, 52, 128)
    assert arrays["constructor_profile_index"].tolist() == [0, 1]
    assert arrays["constructor_graph_index"].tolist() == [0, 0]
    assert arrays["H_deep"].shape == (0, 52, 128)
    assert arrays["pair_truth"].shape == (0, 128)
    assert arrays["raw_x_hat"].shape == (0, 128)
    with (root / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    assert len(manifest["graph_diagnostics"]) == 2
    assert manifest["graph_diagnostics"][1]["admitted"] is False
    assert {"manifest.json", "frame_records.csv", "summary.json",
            "diagnostics.npz", "EXPLORATION_LOG.md"} == {
                path.name for path in root.iterdir()}


def test_second_arm_decoder_exception_retains_first_vector_and_stops(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo, root_relative = _fresh_test_root(tmp_path, monkeypatch, "degree-exception")
    graph_builder, candidate_builder, _, _ = _fake_builders()
    decoder_calls: list[dict] = []

    def second_arm_raises(h: np.ndarray, prior: np.ndarray, syndrome: np.ndarray):
        decoder_calls.append({"arm": "candidate", "H": h.copy(),
                              "prior": prior.copy(), "syndrome": syndrome.copy()})
        raise RuntimeError("fake second arm")

    summary = probe.execute_batch(
        out_root=root_relative, repo_root=repo,
        decode_fns={"control": _fake_decode(decoder_calls, "control"),
                    "candidate": second_arm_raises},
        graph_builder=graph_builder, candidate_builder=candidate_builder,
        profile_preflight_fn=probe.profile_preflight, rss_fn=lambda: 0,
        command="fake second-arm exception",
    )

    root = repo / root_relative
    assert summary["terminal_status"] == "STOP"
    assert summary["complete"] is False
    assert summary["per_arm_outcomes"] is None
    assert summary["attempted_decoder_calls"] == 2
    assert summary["stop_reason"] == "decoder_exception"
    assert [call["arm"] for call in decoder_calls] == ["control", "candidate"]
    arrays = _diagnostic_artifacts(root)
    assert arrays["call_vector_index"].tolist() == [0, -1]
    assert arrays["vector_call_index"].tolist() == [0]
    assert arrays["vector_pair_index"].tolist() == [0]
    assert arrays["vector_profile_index"].tolist() == [0]
    assert arrays["raw_x_hat"].shape == (1, 128)
    with (root / "frame_records.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2
    assert rows[0]["raw_vector_saved"] == "True"
    assert rows[1]["raw_vector_saved"] == "False"
    assert rows[1]["failure_reason"] == "decoder_exception"
    assert {"manifest.json", "frame_records.csv", "summary.json",
            "diagnostics.npz", "EXPLORATION_LOG.md"} == {
                path.name for path in root.iterdir()}


def test_observer_rss_exception_retains_returned_vector_and_stops_next_call(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo, root_relative = _fresh_test_root(tmp_path, monkeypatch, "degree-rss-stop")
    graph_builder, candidate_builder, _, _ = _fake_builders()
    decoder_calls: list[dict] = []
    decoder_returned = False
    after_decode_rss = 0

    def successful_first_arm(h: np.ndarray, prior: np.ndarray, syndrome: np.ndarray):
        nonlocal decoder_returned
        decoded = _fake_decode(decoder_calls, "control")(h, prior, syndrome)
        decoder_returned = True
        return decoded

    def stateful_rss():
        nonlocal after_decode_rss
        if decoder_returned:
            after_decode_rss += 1
            if after_decode_rss == 1:
                raise OSError("injected observer RSS failure")
        return 0

    summary = probe.execute_batch(
        out_root=root_relative, repo_root=repo,
        decode_fns={"control": successful_first_arm,
                    "candidate": _fake_decode(decoder_calls, "candidate")},
        graph_builder=graph_builder, candidate_builder=candidate_builder,
        profile_preflight_fn=probe.profile_preflight, rss_fn=stateful_rss,
        command="fake observer RSS recovery",
    )

    root = repo / root_relative
    assert summary["terminal_status"] == "STOP"
    assert summary["complete"] is False
    assert summary["control_exact"] is None
    assert summary["candidate_exact"] is None
    assert summary["per_arm_outcomes"] is None
    assert summary["attempted_decoder_calls"] == 1
    assert len(decoder_calls) == 1
    assert summary["resource_stop_markers"] == [
        "rss_monitor_exception:OSError:injected observer RSS failure"]
    arrays = _diagnostic_artifacts(root)
    assert arrays["call_vector_index"].tolist() == [0]
    assert arrays["vector_call_index"].tolist() == [0]
    assert arrays["raw_x_hat"].shape == (1, 128)
    with (root / "frame_records.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert rows[0]["raw_vector_saved"] == "True"
    assert rows[0]["status"] == "resource_abort"
    assert "rss_monitor_exception" in rows[0]["failure_reason"]
    assert {"manifest.json", "frame_records.csv", "summary.json",
            "diagnostics.npz", "EXPLORATION_LOG.md"} == {
                path.name for path in root.iterdir()}


def test_diagnostics_cap_retains_stop_record_and_existing_root_is_not_touched(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo, root_relative = _fresh_test_root(tmp_path, monkeypatch, "degree-artifact-cap")
    graph_builder, candidate_builder, _, _ = _fake_builders()
    decoder_calls: list[dict] = []
    monkeypatch.setattr(probe, "ARTIFACT_LIMIT_BYTES", 1)

    def reject_control(profile: dict, graph: dict, graph_seed: int):
        admitted, diagnostic = probe.profile_preflight(profile, graph, graph_seed)
        return False if profile["profile_id"] == "control" else admitted, diagnostic

    summary = probe.execute_batch(
        out_root=root_relative, repo_root=repo,
        decode_fns={"control": _fake_decode(decoder_calls, "control"),
                    "candidate": _fake_decode(decoder_calls, "candidate")},
        graph_builder=graph_builder, candidate_builder=candidate_builder,
        profile_preflight_fn=reject_control, rss_fn=lambda: 0,
        command="fake diagnostics cap",
    )

    root = repo / root_relative
    assert summary["terminal_status"] == "STOP"
    assert summary["complete"] is False
    assert summary["control_exact"] is None
    assert summary["per_arm_outcomes"] is None
    assert summary["attempted_decoder_calls"] == 0
    assert summary["npz_bytes"] is None
    assert any(marker.startswith("diagnostics_cap:")
               for marker in summary["resource_stop_markers"])
    assert decoder_calls == []
    assert not (root / "diagnostics.npz").exists()
    assert (root / "manifest.json").exists()
    assert (root / "frame_records.csv").exists()
    assert (root / "summary.json").exists()
    assert (root / "EXPLORATION_LOG.md").exists()
