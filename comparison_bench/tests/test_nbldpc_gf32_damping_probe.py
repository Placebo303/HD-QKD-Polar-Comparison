"""Fake-only tests for the fixed-alpha GF(32) damping EXPLORE runner."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_damping_probe as probe
from comparison_bench.cli import nbldpc_gf32_label_replica_probe as replica_runner
from comparison_bench.cli import nbldpc_gf32_search_depth_probe as depth_runner
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout


def _fake_dense() -> np.ndarray:
    row_degrees = [4] * 4 + [5] * 48
    sockets = [row for layer in range(5)
               for row, degree in enumerate(row_degrees) if degree > layer]
    dense = np.zeros((probe.M, probe.N), dtype=np.int64)
    for column in range(probe.N):
        first, second = sockets[2 * column:2 * column + 2]
        assert first != second
        dense[first, column] = 1
        dense[second, column] = 2
    assert int(np.count_nonzero(dense)) == probe.EDGE_COUNT
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


def _fake_deep_candidate(h: np.ndarray, pmf: np.ndarray, seed: int):
    del pmf
    common_h = np.asarray(h, dtype=np.int64).copy()
    diagnostic = {
        "graph_seed": int(seed), "candidate_admitted": True,
        "deep_candidate_admitted": True, "construction_stop": False,
        "deep_baseline_rank": probe.M, "deep_candidate_rank": probe.M,
        "deep_support_equal": True, "deep_degrees_equal": True,
        "deep_gauge_equal": True, "sweep_count": 4,
        "termination": "NO_CHANGE",
    }
    return common_h.copy(), common_h, diagnostic


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
    base, remainder = divmod(control_total, len(probe.GRAPH_SEEDS))
    control_by_graph = [base + (i < remainder)
                        for i in range(len(probe.GRAPH_SEEDS))]
    rows: list[dict] = []
    pairs: list[dict] = []
    wrong_added = False
    for graph_seed, control_n, delta_g in zip(
            probe.GRAPH_SEEDS, control_by_graph, graph_deltas):
        candidate_n = control_n + delta_g
        assert 0 <= control_n <= 32 and 0 <= candidate_n <= 32
        for index in range(32):
            control_success = index < control_n
            candidate_success = index < candidate_n
            pair = {
                "graph_seed": int(graph_seed), "stream": index // 16,
                "frame": index % 16,
                "control_success": control_success,
                "candidate_success": candidate_success,
            }
            pairs.append(pair)
            for arm, exact in (("control", control_success),
                               ("candidate", candidate_success)):
                wrong = bool(arm == "control" and not exact and not wrong_added)
                wrong_added = wrong_added or wrong
                rows.append({
                    "phase": "holdout", "arm": arm,
                    "graph_seed": int(graph_seed),
                    "exact": bool(exact), "syndrome_accept": bool(exact or wrong),
                    "syndrome_consistent_wrong": wrong,
                    # The status string is descriptive; it must not define truth.
                    "status": "converged_exact", "iterations": 0,
                    "wall_s": 0.125,
                })
    return rows, pairs


@pytest.mark.parametrize(
    ("control", "deltas", "classification"),
    [
        (39, [3, 3, 3, 3, 0, 0], "MECHANISM_SIGNAL"),
        (39, [3, 3, 3, 2, 0, 0], "NO_SUFFICIENT_SIGNAL"),
        (39, [4, 4, 4, 0, 0, 0], "NO_SUFFICIENT_SIGNAL"),
        (38, [3, 3, 3, 3, 0, 0], "CONTROL_RANGE_UNINFORMATIVE"),
        (153, [3, 3, 3, 3, 0, 0], "MECHANISM_SIGNAL"),
        (154, [3, 3, 3, 3, 0, 0], "CONTROL_RANGE_UNINFORMATIVE"),
    ],
)
def test_frozen_screen_boundaries_wrong_isolation_and_status_not_truth(
        control, deltas, classification
):
    rows, pairs = _complete_rows(control, deltas)
    summary = probe._summarize(rows, pairs, "")
    assert summary["holdout_complete"] is True
    assert summary["holdout_pairs_completed"] == 192
    assert summary["control_exact"] == control
    assert summary["candidate_exact"] == control + sum(deltas)
    assert summary["delta"] == sum(deltas)
    assert [summary["delta_by_graph"][str(seed)]["delta_g"]
            for seed in probe.GRAPH_SEEDS] == deltas
    assert sum(item["delta_g"] > 0
               for item in summary["delta_by_graph"].values()) == sum(
                   value > 0 for value in deltas)
    assert sum(summary["paired_states"].values()) == 192
    assert summary["syndrome_consistent_wrong_rows"] == 1
    assert summary["syndrome_consistent_wrong_by_arm"] == {
        "control": 1, "candidate": 0,
    }
    assert summary["integrity_violations"] == 0
    assert summary["resource_violations"] == 0
    assert summary["authorization_violations"] == 0
    assert summary["classification"] == classification
    assert summary["syndrome_bits_per_attempt"] == 260
    assert summary["actual_syndrome_disclosure_bits"] == 99840
    assert summary["tag_bits"] == 0
    assert summary["verification_status"] == "NOT_IMPLEMENTED"
    assert summary["undetected_status"] == "NOT_MEASURED"
    assert summary["FER"] is summary["f_eff"] is summary["SKR"] is None


def test_v35_adapters_pass_only_frozen_alpha_and_preserve_raw_result():
    raw = object()
    calls = []

    def v35_decode(*args, **kwargs):
        calls.append((args, kwargs))
        return raw

    control = probe._decoder_adapter(v35_decode, 1.0)
    candidate = probe._decoder_adapter(v35_decode, 0.5)
    h = np.zeros((probe.M, probe.N), dtype=np.int64)
    prior = np.ones((probe.N, 32), dtype=np.float64) / 32
    syndrome = np.zeros(probe.M, dtype=np.int64)
    assert control(h, prior, syndrome) is raw
    assert candidate(h, prior, syndrome) is raw
    assert calls[0][0] == calls[1][0] == (h, prior, syndrome)
    assert calls[0][1] == {
        "max_iter": 90, "damping_alpha": 1.0,
        "warm_beliefs": None, "field": None,
    }
    assert calls[1][1] == {
        "max_iter": 90, "damping_alpha": 0.5,
        "warm_beliefs": None, "field": None,
    }
    assert set(calls[0][1]) == set(calls[1][1])
    assert probe._initial_manifest("test")["decoder"]["probability_mixing"] == (
        "p_damped=(1-alpha)*softmax(old)+alpha*softmax(new); "
        "then existing 1e-15 floor, normalization and log")


def test_seed_namespace_and_dry_run_do_not_reach_graph_decoder_or_writes(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path)
    _, holdouts = probe.seed_plan()
    assert len(holdouts) == 192
    assert len({row[3] for row in holdouts}) == 192
    assert probe.holdout_seed(*holdouts[0][:3]) == holdouts[0][3]
    assert probe.SEED_PREFIX == "gf32-damping-v1"

    prior_seeds = {
        int(row[3])
        for plan in (depth_runner.seed_plan(), replica_runner.seed_plan())
        for rows in plan for row in rows
    }
    assert not ({row[3] for row in holdouts} & prior_seeds)
    for obj, name, label in (
        (depth_runner, "build_profile_graph", "graph construction"),
        (depth_runner, "_candidate_pair_for_graph", "deep construction"),
        (probe.prior_runner, "sample_error", "sampled error"),
        (probe.prior_runner, "decode_observation", "decoder observation"),
        (probe, "_bind_production_decoders", "production decoder binding"),
    ):
        monkeypatch.setattr(
            obj, name,
            lambda *args, _label=label, **kwargs: pytest.fail(
                f"dry-run reached {_label}"),
        )
    result = probe.dry_run(out_root, repo_root=repo)
    assert result["status"] == "DRY_RUN"
    assert result["writes"] == result["empirical_input_reads"] == 0
    assert result["graph_construction_calls"] == 0
    assert result["candidate_construction_calls"] == 0
    assert result["decoder_calls"] == 0
    assert result["holdout_pair_count"] == 192
    assert result["holdout_call_count"] == result["maximum_call_count"] == 384
    assert result["control_damping_alpha"] == 1.0
    assert result["candidate_damping_alpha"] == 0.5
    assert result["max_iter"] == 90
    assert result["holdout_seeds_disjoint_from_prior_batches"] is True
    assert not (repo / out_root).exists()
    assert probe.validate_out_root(out_root, repo_root=repo) == repo / out_root
    with pytest.raises(ValueError, match="frozen fresh root"):
        probe.validate_out_root("workspace/unrelated", repo_root=repo)
    (repo / out_root).mkdir()
    with pytest.raises(FileExistsError, match="refusing existing output root"):
        probe.validate_out_root(out_root, repo_root=repo)


def test_full_fake_batch_uses_one_deep_matrix_and_explicit_arm_dispatch(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path)
    _, holdouts = probe.seed_plan()
    holdout_by_seed = {row[3]: row[:3] for row in holdouts}
    control_per_graph = [7, 7, 7, 6, 6, 6]
    candidate_per_graph = [10, 10, 10, 9, 6, 6]
    successful_pairs = {}
    for seed, c, k in zip(probe.GRAPH_SEEDS,
                          control_per_graph, candidate_per_graph):
        for index in range(32):
            successful_pairs[(seed, index // 16, index % 16)] = {
                "control": index < c, "candidate": index < k,
            }

    current = {"key": None, "truth": None}
    clock = {"value": 100.0}
    graph_calls = []
    candidate_calls = []
    decode_calls = []
    pair_checks = []
    deep_by_seed = {}

    def sample(seed, pmf, width=probe.N):
        key = holdout_by_seed[int(seed)]
        current["key"] = key
        truth = np.zeros(width, dtype=np.int64)
        truth[0] = int(seed) % 31 + 1
        current["truth"] = truth.copy()
        np.testing.assert_array_equal(pmf, probe.shape_pmf_grid()[0]["pmf"])
        return truth

    monkeypatch.setattr(probe.prior_runner, "sample_error", sample)

    def graph_builder(seed):
        graph_calls.append(int(seed))
        return _fake_graph(seed)

    def candidate_builder(h, pmf, seed):
        candidate_calls.append(int(seed))
        control = h.copy()
        deep = h.copy()
        deep[0, 0] = 2 if deep[0, 0] != 2 else 3
        # Keep the fake construct separate; the runner must pass only deep to
        # both arms and never infer an arm from matrix content.
        deep_by_seed[int(seed)] = deep.copy()
        diagnostic = {
            "graph_seed": int(seed), "candidate_admitted": True,
            "deep_candidate_admitted": True, "construction_stop": False,
            "deep_candidate_rank": probe.M,
        }
        return control, deep, diagnostic

    original_pair = probe.prior_runner.paired_arm_data

    def inspect_pair(control_h, candidate_h, truth, prior):
        np.testing.assert_array_equal(control_h, candidate_h)
        np.testing.assert_array_equal(control_h, deep_by_seed[current["key"][0]])
        pair = original_pair(control_h, candidate_h, truth, prior)
        assert pair["control"]["prior"] is prior
        assert pair["candidate"]["prior"] is prior
        assert pair["control"]["truth"] is pair["candidate"]["truth"]
        np.testing.assert_array_equal(pair["control"]["truth"], current["truth"])
        np.testing.assert_array_equal(pair["candidate"]["truth"], current["truth"])
        np.testing.assert_array_equal(pair["control"]["syndrome"],
                                      pair["candidate"]["syndrome"])
        pair_checks.append(True)
        return pair

    monkeypatch.setattr(probe.prior_runner, "paired_arm_data", inspect_pair)

    def make_decoder(arm):
        def decode(h, prior, syndrome):
            key = current["key"]
            decode_calls.append((arm, key))
            clock["value"] += 0.25
            assert key is not None
            success = successful_pairs[key][arm]
            truth = current["truth"].copy()
            estimate = truth if success else truth.copy()
            if not success:
                estimate[0] = (int(estimate[0]) + 1) % 32
            return SimpleNamespace(
                x_hat=estimate,
                syndrome_ok=layout.syndrome_ok(h, estimate, syndrome),
                iterations=0 if success else 1,
                status="converged_exact" if success else "max_iter",
            )
        return decode

    decode_fns = {arm: make_decoder(arm) for arm in ("control", "candidate")}
    for obj, name, label in (
        (depth_runner, "build_profile_graph", "production graph builder"),
        (depth_runner, "_candidate_pair_for_graph", "production deep builder"),
        (depth_runner.d10, "build_degree_sequence_peg", "D10 graph constructor"),
    ):
        monkeypatch.setattr(
            obj, name,
            lambda *args, _label=label, **kwargs: pytest.fail(
                f"fake batch reached {_label}"),
        )

    result = probe.execute_batch(
        out_root=out_root, decode_fns=decode_fns,
        graph_builder=graph_builder, candidate_builder=candidate_builder,
        repo_root=repo, now=lambda: clock["value"], rss_fn=lambda: 123,
    )
    assert graph_calls == candidate_calls == list(probe.GRAPH_SEEDS)
    assert len(pair_checks) == 192
    assert len(decode_calls) == 384
    assert decode_calls[:4] == [
        ("control", holdouts[0][:3]), ("candidate", holdouts[0][:3]),
        ("candidate", holdouts[1][:3]), ("control", holdouts[1][:3]),
    ]
    assert result["terminal_status"] == "MECHANISM_SIGNAL"
    assert result["holdout_pairs_completed"] == 192
    assert (result["control_exact"], result["candidate_exact"],
            result["delta"]) == (39, 51, 12)
    assert [result["delta_by_graph"][str(seed)]["delta_g"]
            for seed in probe.GRAPH_SEEDS] == [3, 3, 3, 3, 0, 0]
    assert result["resource_violations"] == result["integrity_violations"] == 0
    assert result["actual_syndrome_disclosure_bits"] == 384 * 260
    assert result["resource_measurement"]["batch_wall_s"] == pytest.approx(96.0)
    assert result["resource_measurement"]["max_call_wall_s"] == pytest.approx(0.25)
    assert result["resource_measurement"]["max_rss_bytes"] == 123

    root = repo / out_root
    assert {path.name for path in root.iterdir()} == {
        "manifest.json", "frame_records.csv", "summary.json",
        "EXPLORATION_LOG.md",
    }
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["batch_uuid"] == probe.BATCH_UUID
    assert manifest["seed_namespace"] == probe.SEED_PREFIX
    assert manifest["graph_profile"]["graph_seeds"] == list(probe.GRAPH_SEEDS)
    assert manifest["arm_mapping"] == {
        "control": "same accepted deep H0D; damping_alpha=1.0",
        "candidate": "same accepted deep H0D; damping_alpha=0.5",
    }
    assert manifest["decoder"]["only_arm_difference"] == "damping_alpha"
    assert manifest["attempted_call_counts"]["total"] == 384
    assert manifest["resource_measurement"]["batch_wall_s"] == pytest.approx(96.0)
    with (root / "frame_records.csv").open(newline="") as stream:
        records = list(csv.DictReader(stream))
    assert len(records) == 384
    assert {row["decoder_branch"] for row in records} == {"control", "candidate"}
    assert {float(row["damping_alpha"]) for row in records} == {1.0, 0.5}
    assert {int(row["max_iter"]) for row in records} == {90}
    assert all(int(row["iterations"]) in (0, 1) for row in records)
    assert all(int(row["syndrome_bits"]) == 260 for row in records)
    assert not ({"truth", "prior", "syndrome_array"} & set(records[0]))


def test_graph_and_deep_candidate_stops_do_not_create_performance_claims(
        tmp_path
):
    repo, out_root = _test_repo(tmp_path / "graph-stop")
    decoders = {"control": lambda *args: pytest.fail("decoder called"),
                "candidate": lambda *args: pytest.fail("decoder called")}
    graph_result = probe.execute_batch(
        out_root=out_root, decode_fns=decoders,
        graph_builder=lambda seed: {**_fake_graph(seed), "admitted": False},
        candidate_builder=lambda *args: pytest.fail("candidate called"),
        repo_root=repo, now=lambda: 0.0, rss_fn=lambda: 17,
    )
    assert graph_result["terminal_status"] == "GRAPH_PREFLIGHT_FAILED"
    assert graph_result["attempted_decoder_calls"] == 0
    _assert_partial_unknowns(graph_result)

    repo2, out_root2 = _test_repo(tmp_path / "candidate-stop")
    candidate_calls = []

    def rejected(*args):
        candidate_calls.append(1)
        return None, None, {
            "candidate_admitted": False,
            "deep_candidate_admitted": False,
            "construction_stop": True,
            "failure_reason": "fake deep admission stop",
        }

    candidate_result = probe.execute_batch(
        out_root=out_root2, decode_fns=decoders,
        graph_builder=_fake_graph, candidate_builder=rejected,
        repo_root=repo2, now=lambda: 0.0, rss_fn=lambda: 17,
    )
    assert candidate_result["terminal_status"] == "DEEP_CANDIDATE_ADMISSION_STOP"
    assert candidate_result["attempted_decoder_calls"] == 0
    assert candidate_calls == [1]
    _assert_partial_unknowns(candidate_result)


def test_complete_pair_then_orphan_attempt_keeps_rows_but_masks_comparison(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path)
    _, holdouts = probe.seed_plan()
    holdout_by_seed = {row[3]: row[:3] for row in holdouts}
    current = {"key": None, "truth": None}
    clock = {"value": 0.0}
    decoder_calls = []
    monkeypatch.setattr(
        probe.prior_runner, "sample_error",
        lambda seed, pmf, width=probe.N: (
            current.update(key=holdout_by_seed[int(seed)],
                           truth=np.zeros(width, dtype=np.int64))
            or np.zeros(width, dtype=np.int64)),
    )

    def graph_builder(seed):
        graph = _fake_graph(seed)
        if int(seed) == probe.GRAPH_SEEDS[-1]:
            clock["value"] = 1790.0
        return graph

    def decode_for(arm):
        def decode(h, prior, syndrome):
            decoder_calls.append((arm, current["key"]))
            clock["value"] += 1.0 if len(decoder_calls) < 3 else 8.0
            truth = current["truth"].copy()
            return SimpleNamespace(
                x_hat=truth, syndrome_ok=layout.syndrome_ok(h, truth, syndrome),
                iterations=0, status="initial_syndrome_hit",
            )
        return decode

    result = probe.execute_batch(
        out_root=out_root,
        decode_fns={arm: decode_for(arm) for arm in ("control", "candidate")},
        graph_builder=graph_builder, candidate_builder=_fake_deep_candidate,
        repo_root=repo, now=lambda: clock["value"], rss_fn=lambda: 10,
    )
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert result["holdout_pairs_completed"] == 1
    assert result["attempted_decoder_calls"] == 3
    assert result["resource_violations"] == 1
    assert result["resource_measurement"]["max_call_wall_s"] == pytest.approx(8.0)
    _assert_partial_unknowns(result)
    item = result["delta_by_graph"][str(probe.GRAPH_SEEDS[0])]
    assert item["completed_pairs"] == 1
    assert item["control_attempts"] == 1
    assert item["candidate_attempts"] == 2
    assert len(decoder_calls) == 3
    with (repo / out_root / "frame_records.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 3
    assert [row["arm"] for row in rows] == ["control", "candidate", "candidate"]
    assert all("resource_abort:total_wall_cap_after_call" in row["status"]
               for row in rows[-1:])


@pytest.mark.parametrize(
    ("case", "expected_reason", "expected_call_wall", "expected_total_wall"),
    [
        ("call_wall", "decoder_call_wall_cap_after_return", 121.0, 121.0),
        ("total_wall", "total_wall_cap_after_call", 20.0, 1810.0),
        ("rss", "rss_cap_after_call", 0.0, 0.0),
    ],
)
def test_exception_after_each_resource_overrun_is_persisted_and_stops(
        tmp_path, case, expected_reason, expected_call_wall, expected_total_wall
):
    repo, out_root = _test_repo(tmp_path)
    clock = {"value": 0.0}
    rss = {"value": 64}
    decoder_calls = []

    def graph_builder(seed):
        if case == "total_wall" and int(seed) == probe.GRAPH_SEEDS[-1]:
            clock["value"] = 1790.0
        return _fake_graph(seed)

    def overrun_then_raise(h, prior, syndrome):
        decoder_calls.append(1)
        if case == "call_wall":
            clock["value"] += 121.0
        elif case == "total_wall":
            clock["value"] += 20.0
        else:
            rss["value"] = probe.RSS_CAP_BYTES + 1
        raise RuntimeError("fake resource boundary")

    result = probe.execute_batch(
        out_root=out_root,
        decode_fns={"control": overrun_then_raise,
                    "candidate": lambda *args: pytest.fail("next call ran")},
        graph_builder=graph_builder, candidate_builder=_fake_deep_candidate,
        repo_root=repo, now=lambda: clock["value"], rss_fn=lambda: rss["value"],
    )
    assert len(decoder_calls) == 1
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert result["attempted_decoder_calls"] == 1
    assert result["holdout_pairs_completed"] == 0
    assert result["resource_violations"] == 1
    assert expected_reason in result["stop_reason"]
    assert result["resource_measurement"]["batch_wall_s"] == pytest.approx(
        expected_total_wall)
    assert result["resource_measurement"]["max_call_wall_s"] == pytest.approx(
        expected_call_wall)
    if case == "rss":
        assert result["resource_measurement"]["max_rss_bytes"] == \
            probe.RSS_CAP_BYTES + 1
    else:
        assert result["resource_measurement"]["max_rss_bytes"] == 64
    _assert_partial_unknowns(result)
    with (repo / out_root / "frame_records.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert rows[0]["status"].startswith("decoder_exception:RuntimeError")
    assert "resource_abort:" + expected_reason in rows[0]["status"]
    manifest = json.loads((repo / out_root / "manifest.json").read_text())
    assert manifest["resource_measurement"]["batch_wall_s"] == pytest.approx(
        expected_total_wall)
    assert manifest["resource_measurement"]["max_call_wall_s"] == pytest.approx(
        expected_call_wall)


def test_execute_requires_both_explicit_fake_decoder_callbacks(tmp_path):
    repo, out_root = _test_repo(tmp_path)
    with pytest.raises(ValueError, match="explicit control and candidate"):
        probe.execute_batch(
            out_root=out_root, decode_fns={"control": lambda *args: None},
            graph_builder=_fake_graph, repo_root=repo,
            now=lambda: 0.0, rss_fn=lambda: 0,
        )
    assert not (repo / out_root).exists()


def test_exactly_max_iter_90_is_valid_and_accounted_as_observed_success(
        tmp_path, monkeypatch
):
    repo, out_root = _test_repo(tmp_path)
    clock = {"value": 10.0}
    decode_calls = {"control": 0, "candidate": 0}

    def sample(seed, pmf, width=probe.N):
        del seed, pmf
        return np.zeros(width, dtype=np.int64)

    monkeypatch.setattr(probe.prior_runner, "sample_error", sample)

    def make_decoder(arm):
        def decode(h, prior, syndrome):
            del prior
            estimate = np.zeros(probe.N, dtype=np.int64)
            decode_calls[arm] += 1
            clock["value"] += 0.01
            return SimpleNamespace(
                x_hat=estimate,
                syndrome_ok=layout.syndrome_ok(h, estimate, syndrome),
                iterations=90,
                # Status alone must not override exact/syndrome accounting.
                status="max_iter",
            )
        return decode

    result = probe.execute_batch(
        out_root=out_root,
        decode_fns={arm: make_decoder(arm) for arm in decode_calls},
        graph_builder=_fake_graph,
        candidate_builder=_fake_deep_candidate,
        repo_root=repo, now=lambda: clock["value"], rss_fn=lambda: 123,
    )

    assert result["terminal_status"] == "CONTROL_RANGE_UNINFORMATIVE"
    assert result["holdout_complete"] is True
    assert result["holdout_pairs_completed"] == 192
    assert decode_calls == {"control": 192, "candidate": 192}
    assert (result["control_exact"], result["candidate_exact"],
            result["delta"]) == (192, 192, 0)
    assert result["paired_states"] == {
        "control_only": 0, "candidate_only": 0, "both": 192, "neither": 0,
    }
    assert result["decoder_iterations_by_arm"] == {
        "control": 192 * 90, "candidate": 192 * 90,
    }
    assert result["actual_syndrome_disclosure_bits"] == 384 * 260
    assert result["tag_bits"] == 0
    assert result["integrity_violations"] == 0
    assert result["resource_violations"] == 0
    assert result["authorization_violations"] == 0
    assert result["verification_status"] == "NOT_IMPLEMENTED"
    assert result["undetected_status"] == "NOT_MEASURED"
    assert result["FER"] is result["f_eff"] is result["SKR"] is None

    root = repo / out_root
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["decoder"]["max_iter"] == 90
    with (root / "frame_records.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 384
    assert {int(row["max_iter"]) for row in rows} == {90}
    assert {int(row["iterations"]) for row in rows} == {90}
    assert {row["status"] for row in rows} == {"max_iter"}
    assert {row["exact"] for row in rows} == {"True"}
    assert {row["syndrome_accept"] for row in rows} == {"True"}
