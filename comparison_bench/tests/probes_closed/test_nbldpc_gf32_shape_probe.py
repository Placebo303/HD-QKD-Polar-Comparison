"""Fake-only checks for the frozen GF32 source-shape EXPLORE runner."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli.probes_closed import nbldpc_gf32_shape_probe as probe
from comparison_bench.cli.probes_closed import nbldpc_gf32_label_probe as prior_runner
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout


def _fake_dense() -> np.ndarray:
    """A hand-built test socket matrix; never calls the production builder."""
    row_degrees = [4] * 4 + [5] * 48
    sockets = [row for layer in range(5)
               for row, degree in enumerate(row_degrees)
               if degree > layer]
    assert len(sockets) == probe.EDGE_COUNT
    dense = np.zeros((probe.M, probe.N), dtype=np.int64)
    for column in range(probe.N):
        first, second = sockets[2 * column:2 * column + 2]
        assert first != second
        dense[first, column] = 1
        dense[second, column] = 2
    return dense


def _fake_graph(seed: int) -> dict:
    dense = _fake_dense()
    return {
        "status": "ok", "graph_seed": int(seed), "n": probe.N,
        "m": probe.M, "E": probe.EDGE_COUNT, "dense": dense,
        "admitted": True, "failure_reason": "",
        "structure": {
            "admitted": True,
            "admission": {"profile": True, "connected": True,
                          "full_rank": True},
            "gf32_rank": probe.M, "structural_rank": probe.M,
            "connected_components": 1, "duplicate_edges": 0,
        },
    }


def _new_repo_root(path: Path) -> tuple[Path, Path]:
    repo = path / "repo"
    (repo / "workspace").mkdir(parents=True)
    return repo, Path("workspace") / "gf32_shape_fd01e03e"


def _admit_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_align(dense, pmf):
        labels = np.full(probe.N, 2, dtype=np.int64)
        candidate = probe.alignment.scale_columns(dense, labels)
        return {
            "candidate": candidate, "labels": labels,
            "gauge_equal": True, "support_equal": True,
            "J0": 0.0, "Jc": 1.0, "candidate_admitted": True,
        }

    monkeypatch.setattr(probe.alignment, "align_labels", fake_align)
    # Rank is a structural fact supplied by this fake fixture, not a graph build.
    monkeypatch.setattr(probe.d10, "gf32_row_rank", lambda matrix: probe.M)


def test_sparse_shape_grid_preserves_zeros_and_frozen_order():
    grid = probe.shape_pmf_grid()
    assert [row["p0"] for row in grid] == [0.85, 0.65, 0.45, 0.25]
    assert [row["index"] for row in grid] == [0, 1, 2, 3]
    assert probe.SHAPE_COUNTS == ((1, 2295), (3, 1126), (7, 557),
                                  (15, 304), (31, 146))
    assert sum(count for _, count in probe.SHAPE_COUNTS) == 4428
    for row in grid:
        pmf = row["pmf"]
        assert np.flatnonzero(pmf).tolist() == [0, 1, 3, 7, 15, 31]
        assert pmf[0] == row["p0"]
        assert np.isclose(pmf.sum(), 1.0, rtol=0.0, atol=1e-12)
        for symbol, count in probe.SHAPE_COUNTS:
            assert pmf[symbol] == pytest.approx(
                (1.0 - row["p0"]) * count / probe.SHAPE_TOTAL)
    assert probe.verify_t0()["sparse_shape_grid"] is True


def test_seed_namespaces_counts_and_alternating_pair_order():
    pilots, holdouts = probe.seed_plan()
    assert len(pilots) == 96
    assert len(holdouts) == 192
    assert len({row[3] for row in pilots}) == len(pilots)
    assert len({row[3] for row in holdouts}) == len(holdouts)
    assert {row[3] for row in pilots}.isdisjoint(row[3] for row in holdouts)
    assert pilots[0] == (0, probe.GRAPH_SEEDS[0], 0,
                         probe.pilot_seed(0, probe.GRAPH_SEEDS[0], 0))
    assert holdouts[0] == (probe.GRAPH_SEEDS[0], 0, 0,
                           probe.holdout_seed(probe.GRAPH_SEEDS[0], 0, 0))
    assert probe.arm_order(0) == ("control", "candidate")
    assert probe.arm_order(1) == ("candidate", "control")


def test_paired_arm_data_shares_error_prior_and_recomputes_syndromes():
    control = _fake_dense()
    labels = np.full(probe.N, 2, dtype=np.int64)
    candidate = probe.alignment.scale_columns(control, labels)
    truth = np.arange(probe.N, dtype=np.int64) % 3
    prior = np.tile(probe.shape_pmf_grid()[1]["pmf"], (probe.N, 1))
    arms = prior_runner.paired_arm_data(control, candidate, truth, prior)
    np.testing.assert_array_equal(arms["control"]["truth"], truth)
    np.testing.assert_array_equal(arms["candidate"]["truth"], truth)
    np.testing.assert_array_equal(arms["control"]["prior"], prior)
    np.testing.assert_array_equal(arms["candidate"]["prior"], prior)
    np.testing.assert_array_equal(
        arms["control"]["syndrome"], layout.gf32_syndrome(control, truth))
    np.testing.assert_array_equal(
        arms["candidate"]["syndrome"], layout.gf32_syndrome(candidate, truth))


def test_graph_preflight_checks_sockets_and_candidate_gauge(monkeypatch):
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

    _admit_candidate(monkeypatch)
    candidate, detail = probe._candidate_for_graph(
        graph["dense"], probe.shape_pmf_grid()[0]["pmf"],
        probe.GRAPH_SEEDS[0])
    assert candidate is not None
    assert detail["candidate_admitted"] is True
    assert detail["nontrivial"] is True
    assert detail["gauge_equal"] is True


def test_trivial_candidate_is_rejected_even_with_score_gain(monkeypatch):
    dense = _fake_dense()
    monkeypatch.setattr(probe.d10, "gf32_row_rank", lambda matrix: probe.M)
    monkeypatch.setattr(probe.alignment, "align_labels", lambda h, p: {
        "candidate": np.asarray(h), "labels": np.ones(probe.N, dtype=np.int64),
        "gauge_equal": True, "support_equal": True,
        "J0": 0.0, "Jc": 1.0, "candidate_admitted": True,
    })
    candidate, detail = probe._candidate_for_graph(
        dense, probe.shape_pmf_grid()[0]["pmf"], probe.GRAPH_SEEDS[0])
    assert candidate is None
    assert detail["candidate_admitted"] is False
    assert detail["nontrivial"] is False


def test_wrong_syndrome_consistent_rows_do_not_count_as_success():
    pmf = {"index": 0, "p0": 0.85}
    rows = []
    pairs = []
    for index in range(probe.HOLDOUT_PAIRS):
        c_success = index != 0
        k_success = True
        common = dict(
            phase="holdout", pmf=pmf, graph_seed=probe.GRAPH_SEEDS[
                index // 32], stream=(index // 16) % 2, frame=index % 16,
            seed=index,
        )
        rows.append(probe._record_row(
            **common, call_index=2 * index + 1, arm="control", observed={
                "exact": c_success, "syndrome_accept": True,
                "syndrome_consistent_wrong": not c_success,
                "status": "ok", "iterations": 1, "wall_s": 0.0,
                "rss_b": 0,
            }))
        rows.append(probe._record_row(
            **common, call_index=2 * index + 2, arm="candidate", observed={
                "exact": k_success, "syndrome_accept": True,
                "syndrome_consistent_wrong": False,
                "status": "ok", "iterations": 1, "wall_s": 0.0,
                "rss_b": 0,
            }))
        pairs.append({
            "graph_seed": probe.GRAPH_SEEDS[index // 32],
            "control_exact": c_success, "candidate_exact": k_success,
        })
    summary = probe._summarize(rows, pairs, [], "")
    assert summary["control_exact"] == 191
    assert summary["candidate_exact"] == 192
    assert summary["syndrome_consistent_wrong_rows"] == 1
    assert summary["paired_states"]["candidate_only"] == 1


def test_dry_run_is_pure_and_does_not_construct_or_decode(tmp_path, monkeypatch):
    repo, out_root = _new_repo_root(tmp_path)
    monkeypatch.setattr(probe, "build_profile_graph",
                        lambda seed: pytest.fail("dry-run built a graph"))
    monkeypatch.setattr(probe, "_bind_production_decoder",
                        lambda: pytest.fail("dry-run bound the decoder"))
    result = probe.dry_run(out_root, repo_root=repo)
    assert result["status"] == "DRY_RUN"
    assert result["writes"] == result["empirical_input_reads"] == 0
    assert result["graph_construction_calls"] == result["decoder_calls"] == 0
    assert result["maximum_call_count"] == 480
    assert not (repo / out_root).exists()


def test_execute_fake_runs_control_pilot_then_192_paired_holdouts(
        tmp_path, monkeypatch):
    repo, out_root = _new_repo_root(tmp_path)
    _admit_candidate(monkeypatch)
    monkeypatch.setattr(
        prior_runner, "sample_error",
        lambda seed, pmf, width=probe.N: np.zeros(width, dtype=np.int64))

    built = []

    def fake_builder(seed):
        built.append(seed)
        return _fake_graph(seed)

    calls = []

    def fake_decoder(dense, prior, syndrome):
        calls.append((np.asarray(dense).copy(), np.asarray(prior).copy(),
                      np.asarray(syndrome).copy()))
        # First p0 has 12/24 exact control successes, selecting it. The
        # remaining fake holdout decisions are exact in both arms.
        if len(calls) <= 12 or len(calls) > 24:
            estimate = np.zeros(probe.N, dtype=np.int64)
        else:
            estimate = np.ones(probe.N, dtype=np.int64)
        accepted = bool(np.array_equal(
            layout.gf32_syndrome(dense, estimate), syndrome))
        return SimpleNamespace(x_hat=estimate, syndrome_ok=accepted,
                               iterations=1, status="fake")

    result = probe.execute_batch(
        out_root=out_root, decode_fn=fake_decoder, graph_builder=fake_builder,
        repo_root=repo, rss_fn=lambda: 0)
    assert built == list(probe.GRAPH_SEEDS)
    assert len(calls) == 24 + probe.MAX_HOLDOUT_CALLS == 408
    assert result["pilot_control_exact_by_pmf"] == {"0": 12}
    assert result["selected_pmf_index"] == 0
    assert result["holdout_pairs_completed"] == 192
    assert result["attempted_call_counts"] == {
        "pilot": 24, "holdout": 384, "total": 408}
    assert result["syndrome_bits_per_attempt"] == 260
    assert result["classification"] == "CONTROL_RANGE_UNINFORMATIVE"
    assert result["FER"] is result["f_eff"] is result["SKR"] is None
    output = repo / out_root
    assert sorted(path.name for path in output.iterdir()) == [
        "EXPLORATION_LOG.md", "frame_records.csv", "manifest.json",
        "summary.json",
    ]
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["track"] == "EXPLORE"
    assert manifest["batch_uuid"] == probe.BATCH_UUID
    assert manifest["source_shape_proxy"]["not_conditional_channel_reconstruction"]
    assert manifest["accounting"]["verification_status"] == "NOT_IMPLEMENTED"
    with (output / "frame_records.csv").open(newline="") as stream:
        records = list(csv.DictReader(stream))
    assert len(records) == 408
    assert {int(row["syndrome_bits"]) for row in records} == {260}


def test_pilot_without_control_point_stops_without_candidates(
        tmp_path, monkeypatch):
    repo, out_root = _new_repo_root(tmp_path)
    built = []

    def fake_builder(seed):
        built.append(seed)
        return _fake_graph(seed)

    calls = []

    def fake_decoder(dense, prior, syndrome):
        calls.append(1)
        estimate = np.ones(probe.N, dtype=np.int64)
        accepted = bool(np.array_equal(
            layout.gf32_syndrome(dense, estimate), syndrome))
        return SimpleNamespace(x_hat=estimate, syndrome_ok=accepted,
                               iterations=1, status="fake")

    monkeypatch.setattr(
        prior_runner, "sample_error",
        lambda seed, pmf, width=probe.N: np.zeros(width, dtype=np.int64))
    monkeypatch.setattr(probe, "_candidate_for_graph",
                        lambda *args: pytest.fail("candidate built without pilot point"))
    result = probe.execute_batch(
        out_root=out_root, decode_fn=fake_decoder, graph_builder=fake_builder,
        repo_root=repo, rss_fn=lambda: 0)
    assert len(built) == 6
    assert len(calls) == probe.MAX_PILOT_CALLS == 96
    assert result["terminal_status"] == "CONTROL_RANGE_UNINFORMATIVE"
    assert result["stop_reason"] == "CONTROL_RANGE_UNINFORMATIVE"
    assert result["attempted_call_counts"] == {
        "pilot": 96, "holdout": 0, "total": 96}


def test_candidate_failure_and_resource_gate_stop_before_holdout(
        tmp_path, monkeypatch):
    repo, out_root = _new_repo_root(tmp_path)
    _admit_candidate(monkeypatch)
    monkeypatch.setattr(
        prior_runner, "sample_error",
        lambda seed, pmf, width=probe.N: np.zeros(width, dtype=np.int64))
    calls = []

    def fake_decoder(dense, prior, syndrome):
        calls.append(1)
        estimate = (np.zeros(probe.N, dtype=np.int64) if len(calls) <= 12
                    else np.ones(probe.N, dtype=np.int64))
        accepted = bool(np.array_equal(
            layout.gf32_syndrome(dense, estimate), syndrome))
        return SimpleNamespace(x_hat=estimate, syndrome_ok=accepted,
                               iterations=1, status="fake")

    monkeypatch.setattr(probe, "_candidate_for_graph",
                        lambda *args: (None, {"candidate_admitted": False,
                                              "J0_bits": 0.0, "Jc_bits": 0.0}))
    result = probe.execute_batch(
        out_root=out_root, decode_fn=fake_decoder,
        graph_builder=_fake_graph, repo_root=repo, rss_fn=lambda: 0)
    assert result["terminal_status"] == "NO_NONTRIVIAL_LABEL_CANDIDATE"
    assert result["attempted_call_counts"]["holdout"] == 0
    assert len(calls) == 24

    repo2, out_root2 = _new_repo_root(tmp_path / "budget")
    time_calls = 0

    def expired_clock():
        nonlocal time_calls
        time_calls += 1
        return 0.0 if time_calls == 1 else probe.WALL_CAP_S

    result2 = probe.execute_batch(
        out_root=out_root2,
        decode_fn=lambda *args: pytest.fail("expired batch decoded a frame"),
        graph_builder=lambda seed: pytest.fail("expired batch built a graph"),
        repo_root=repo2, now=expired_clock, rss_fn=lambda: 0)
    assert result2["terminal_status"] == "RESOURCE_STOP"
    assert result2["stop_reason"] == "total_wall_cap_before_next_call"
    assert result2["attempted_decoder_calls"] == 0


def test_fresh_root_refusal(tmp_path):
    repo, out_root = _new_repo_root(tmp_path)
    assert probe.validate_out_root(out_root, repo_root=repo) == repo / out_root
    with pytest.raises(ValueError, match="frozen fresh root"):
        probe.validate_out_root("workspace/other", repo_root=repo)
    target = repo / out_root
    target.mkdir()
    with pytest.raises(FileExistsError, match="refusing existing output root"):
        probe.validate_out_root(out_root, repo_root=repo)
