"""Fake-only contract and production-binding tests for the GF32 cap probe."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_itercap_probe as probe
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout


def _fake_h() -> np.ndarray:
    h = np.zeros((probe.M, probe.N), dtype=np.int64)
    h[np.arange(probe.M), np.arange(probe.M)] = 1
    return h


def _fake_construction(h: np.ndarray, graph_calls: list[int],
                       candidate_calls: list[int], *,
                       deep_h: np.ndarray | None = None,
                       candidate_diagnostic: dict | None = None):
    deep = h if deep_h is None else np.asarray(deep_h, dtype=np.int64)
    diagnostic = candidate_diagnostic or {
        "candidate_admitted": True,
        "deep_candidate_admitted": True,
        "construction_stop": False,
    }

    def graph_builder(seed: int) -> dict:
        graph_calls.append(int(seed))
        return {"dense": h.copy()}

    def preflight_fn(graph: dict, seed: int) -> tuple[bool, dict]:
        assert int(seed) in probe.GRAPH_SEEDS
        return True, {"fake_preflight": True}

    def candidate_builder(dense, pmf, seed: int):
        candidate_calls.append(int(seed))
        np.testing.assert_array_equal(dense, h)
        assert np.asarray(pmf).shape == (32,)
        assert np.isclose(np.asarray(pmf).sum(), 1.0)
        return h.copy(), deep.copy(), dict(diagnostic)

    return graph_builder, preflight_fn, candidate_builder


def _install_sample_spy(monkeypatch: pytest.MonkeyPatch):
    original = probe.prior_runner.sample_error
    samples: list[tuple[int, np.ndarray]] = []

    def sample_spy(seed, pmf, width=probe.N):
        truth = np.asarray(original(seed, pmf, width=width), dtype=np.int64)
        samples.append((int(seed), truth.copy()))
        return truth

    monkeypatch.setattr(probe.prior_runner, "sample_error", sample_spy)
    return samples


def _test_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
               name: str) -> tuple[Path, Path]:
    repo = tmp_path / f"repo-{name}"
    (repo / "workspace").mkdir(parents=True)
    relative = Path("workspace") / name
    monkeypatch.setattr(probe, "OUT_ROOT_RELATIVE", relative)
    return repo, relative


def _csv_bool(value: str) -> bool | None:
    if value == "":
        return None
    return value == "True"


def _seed_values(plan):
    if isinstance(plan, (tuple, list)):
        if len(plan) == 4 and all(np.isscalar(value) for value in plan):
            return [int(plan[3])]
        return [seed for part in plan for seed in _seed_values(part)]
    return []


def test_production_decoder_adapters_change_only_max_iter() -> None:
    calls: list[tuple[np.ndarray, np.ndarray, np.ndarray, dict]] = []

    def decoder_spy(h, prior, syndrome, **kwargs):
        calls.append((np.asarray(h).copy(), np.asarray(prior).copy(),
                      np.asarray(syndrome).copy(), dict(kwargs)))
        return SimpleNamespace(
            x_hat=np.zeros(np.asarray(h).shape[1], dtype=np.int64),
            syndrome_ok=False, iterations=kwargs["max_iter"],
            status="binding-spy",
        )

    adapters = probe._bind_production_decoders(v35_decode=decoder_spy)
    assert set(adapters) == set(probe.ARM_MAX_ITER)

    h = np.asarray([[1, 0], [0, 1]], dtype=np.int64)
    prior = np.full((2, 32), 1.0 / 32.0, dtype=np.float64)
    syndrome = np.asarray([0, 0], dtype=np.int64)
    global_state = (dict(probe.ARM_MAX_ITER), probe.CONTROL_ALPHA,
                    probe.WARM_BELIEFS, probe.FIELD)

    for arm in ("control", "candidate"):
        result = adapters[arm](h, prior, syndrome)
        assert result.status == "binding-spy"

    assert len(calls) == 2
    np.testing.assert_array_equal(calls[0][0], h)
    np.testing.assert_array_equal(calls[1][0], h)
    np.testing.assert_array_equal(calls[0][1], prior)
    np.testing.assert_array_equal(calls[1][1], prior)
    np.testing.assert_array_equal(calls[0][2], syndrome)
    np.testing.assert_array_equal(calls[1][2], syndrome)
    control_kwargs, candidate_kwargs = calls[0][3], calls[1][3]
    assert control_kwargs["max_iter"] == 90
    assert candidate_kwargs["max_iter"] == 250
    assert control_kwargs.keys() == candidate_kwargs.keys()
    assert {
        key: value for key, value in control_kwargs.items()
        if key != "max_iter"
    } == {
        key: value for key, value in candidate_kwargs.items()
        if key != "max_iter"
    }
    assert control_kwargs["damping_alpha"] == 1.0
    assert control_kwargs["warm_beliefs"] is None
    assert control_kwargs["field"] is None
    assert (dict(probe.ARM_MAX_ITER), probe.CONTROL_ALPHA,
            probe.WARM_BELIEFS, probe.FIELD) == global_state


def test_t0_and_dry_run_are_read_only_and_do_not_bind_decoder(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    checks = probe.verify_t0()
    assert checks and all(checks.values())
    assert (probe.CALL_CAP_S, probe.WALL_CAP_S, probe.RSS_CAP_BYTES,
            probe.MAX_CALLS) == (120.0, 1800.0, 4 * 1024 ** 3, 384)

    repo = tmp_path / "repo"
    relative = Path("workspace") / "itercap-test-root"
    (repo / "workspace").mkdir(parents=True)
    monkeypatch.setattr(probe, "_repo_root", lambda: repo)
    monkeypatch.setattr(probe, "OUT_ROOT_RELATIVE", relative)
    monkeypatch.setattr(
        probe, "_bind_production_decoders",
        lambda *args, **kwargs: pytest.fail("dry-run bound decoder"),
    )
    monkeypatch.setattr(
        probe.search_runner, "build_profile_graph",
        lambda *args, **kwargs: pytest.fail("dry-run constructed graph"),
    )
    monkeypatch.setattr(
        probe.search_runner, "_candidate_pair_for_graph",
        lambda *args, **kwargs: pytest.fail("dry-run built candidate"),
    )
    monkeypatch.setattr(
        probe.prior_runner, "sample_error",
        lambda *args, **kwargs: pytest.fail("dry-run sampled source"),
    )

    result = probe.dry_run(relative, repo_root=repo)
    assert result["status"] == "DRY_RUN"
    assert result["exists"] is False
    assert result["writes"] == 0
    assert result["artifact_reads"] == 0
    assert result["graph_calls"] == 0
    assert result["decoder_calls"] == 0
    assert result["osd_calls"] == 0
    assert result["science_calls"] == 0
    assert result["attempted_decoder_calls"] == 0
    assert result["t0"] and all(result["t0"].values())
    assert not (repo / relative).exists()

    (repo / relative).mkdir()
    with pytest.raises(FileExistsError):
        probe.dry_run(relative, repo_root=repo)


def test_t0_rejects_weight_drift_with_same_p0_support_and_sum(
        monkeypatch: pytest.MonkeyPatch) -> None:
    source_grid = probe.search_runner.shape_pmf_grid()
    entry = dict(source_grid[0])
    changed = np.asarray(entry["pmf"], dtype=np.float64).copy()
    changed[1] += 0.001
    changed[3] -= 0.001
    assert changed[0] == np.asarray(entry["pmf"])[0]
    assert np.isclose(changed.sum(), 1.0, rtol=0.0, atol=1e-12)
    assert np.flatnonzero(changed).tolist() == [0, 1, 3, 7, 15, 31]
    entry["pmf"] = changed
    monkeypatch.setattr(
        probe.search_runner, "shape_pmf_grid", lambda: [entry])

    with pytest.raises(AssertionError, match="PMF"):
        probe.verify_t0()


def test_seed_plan_is_disjoint_from_accepted_predecessors_and_rejects_collision(
        monkeypatch: pytest.MonkeyPatch) -> None:
    old_plans = (
        probe.prior_runner._seed_plan(),
        probe.search_runner.fine_runner.predecessor.seed_plan(),
        probe.search_runner.fine_runner.seed_plan(),
        probe.search_runner.replica_runner.seed_plan(),
        probe.search_runner.seed_plan(),
        probe.resource_runner.seed_plan(),
    )
    old_seeds = {seed for plan in old_plans for seed in _seed_values(plan)}
    plan = probe.seed_plan()
    seeds = {int(row[3]) for row in plan}
    assert len(seeds) == probe.HOLDOUT_PAIRS == 192
    assert seeds.isdisjoint(old_seeds)

    colliding = list(plan)
    colliding[0] = (*colliding[0][:3], next(iter(old_seeds)))
    monkeypatch.setattr(probe, "seed_plan", lambda: colliding)
    with pytest.raises(AssertionError, match="prior-disjoint"):
        probe._validate_seed_plan()


def test_seed_namespace_rejects_suffix_drift(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(probe, "SEED_PREFIX", "gf32-itercap-v1-alt")
    with pytest.raises(AssertionError, match="seed namespace"):
        probe._validate_seed_plan()


@pytest.mark.parametrize("candidate_diagnostic", [
    {"candidate_admitted": True, "deep_candidate_admitted": False,
     "construction_stop": False},
    {"candidate_admitted": True, "deep_candidate_admitted": True,
     "construction_stop": True},
])
def test_candidate_diagnostic_stop_blocks_bp_even_with_matrices(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        candidate_diagnostic: dict) -> None:
    repo, relative = _test_root(
        tmp_path, monkeypatch,
        "itercap-admission-" + str(candidate_diagnostic["construction_stop"]))
    h = _fake_h()
    graph_calls: list[int] = []
    candidate_calls: list[int] = []
    graph_builder, preflight_fn, candidate_builder = _fake_construction(
        h, graph_calls, candidate_calls,
        candidate_diagnostic=candidate_diagnostic)
    decoder_calls: list[str] = []

    def forbidden_decoder(arm: str):
        def decode(*args):
            decoder_calls.append(arm)
            raise RuntimeError("decoder must not follow rejected candidate")
        return decode

    result = probe.execute_batch(
        out_root=relative,
        decode_fns={arm: forbidden_decoder(arm) for arm in probe.ARM_MAX_ITER},
        graph_builder=graph_builder,
        candidate_builder=candidate_builder,
        preflight_fn=preflight_fn,
        repo_root=repo,
        rss_fn=lambda: 1024,
    )

    assert decoder_calls == []
    assert candidate_calls == [probe.GRAPH_SEEDS[0]]
    assert result["complete"] is False
    assert result["attempted_call_counts"]["total"] == 0
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    assert result["per_graph"] is None
    assert result["paired"] is None
    assert result["transitions"] is None


def test_observer_and_summary_separate_outcomes_and_keep_frozen_screen_edges(
        ) -> None:
    h = np.asarray([[1, 0]], dtype=np.int64)
    truth = np.asarray([1, 2], dtype=np.int64)
    syndrome = layout.gf32_syndrome(h, truth)
    prior = np.full((2, 32), 1.0 / 32.0)
    estimates = (
        (truth.copy(), (True, True, False)),
        (np.asarray([1, 3]), (False, True, True)),
        (np.asarray([0, 0]), (False, False, False)),
    )
    for estimate, expected in estimates:
        calls: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []

        def decoder(h_arg, prior_arg, syndrome_arg):
            calls.append((np.asarray(h_arg).copy(),
                          np.asarray(prior_arg).copy(),
                          np.asarray(syndrome_arg).copy()))
            return SimpleNamespace(
                x_hat=estimate.copy(),
                syndrome_ok=layout.syndrome_ok(h_arg, estimate, syndrome_arg),
                iterations=1,
                status="observation-fixture",
            )

        observed, issue = probe.prior_runner.decode_observation(
            decoder, h, prior, truth, syndrome,
            now=lambda: 0.0, rss_fn=lambda: 100)
        assert issue == ""
        assert (observed["exact"], observed["syndrome_accept"],
                observed["syndrome_consistent_wrong"]) == expected
        assert len(calls) == 1
        np.testing.assert_array_equal(calls[0][0], h)
        np.testing.assert_array_equal(calls[0][1], prior)
        np.testing.assert_array_equal(calls[0][2], syndrome)

    control_counts = (7, 7, 7, 6, 6, 6)  # 39: inclusive CONTROL_MIN
    candidate_counts = (9, 9, 9, 8, 8, 8)  # delta=12, all 6 graphs positive
    rows: list[dict] = []
    for graph_index, graph_seed in enumerate(probe.GRAPH_SEEDS):
        for frame in range(32):
            pair_index = graph_index * 32 + frame
            control_exact = frame < control_counts[graph_index]
            candidate_exact = frame < candidate_counts[graph_index]
            control_fail = (not control_exact and
                            frame <= candidate_counts[graph_index] + 1)
            candidate_fail = (not candidate_exact and
                              frame == candidate_counts[graph_index] + 1)
            control_wrong = not control_exact and not control_fail
            candidate_wrong = (not candidate_exact and not candidate_fail)
            control = {
                "pair_index": pair_index, "graph_seed": graph_seed,
                "arm": "control", "exact": control_exact,
                "syndrome_accept": not control_fail,
                "syndrome_consistent_wrong": control_wrong,
                "iterations": 1, "wall_s": 0.01, "rss_b": 1024,
            }
            candidate = {
                "pair_index": pair_index, "graph_seed": graph_seed,
                "arm": "candidate", "exact": candidate_exact,
                "syndrome_accept": not candidate_fail,
                "syndrome_consistent_wrong": candidate_wrong,
                "iterations": 1, "wall_s": 0.01, "rss_b": 1024,
                "prefix_check": (
                    "PASS_CONTROL_SYNDROME_FAIL" if control_fail else
                    "PASS_CONTROL_SYNDROME_PASS"),
            }
            rows.extend((control, candidate))

    summary = probe._summarize(
        rows, complete=True, terminal_status="COMPLETE", stop_reason=None,
        resource_measurement={})
    assert summary["complete"] is True
    assert summary["classification"] == "MECHANISM_SIGNAL"
    assert summary["control_exact"] == 39
    assert summary["candidate_exact"] == 51
    assert summary["delta"] == 12
    assert summary["positive_graphs"] == 6
    assert summary["paired"] == {
        "both": 39, "control_only": 0, "candidate_only": 12, "neither": 141,
    }
    assert summary["transitions"] == {
        "control_raw_fail_to_candidate_exact": 12,
        "control_raw_fail_to_candidate_valid_wrong": 6,
        "control_raw_fail_to_candidate_still_fail": 6,
        "control_syndrome_pass_prefix_consistent": 168,
    }


def test_stateful_rss_failure_retains_first_arm_and_stops_before_second(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, relative = _test_root(tmp_path, monkeypatch, "itercap-rss-stop")
    h = _fake_h()
    graph_calls: list[int] = []
    candidate_calls: list[int] = []
    graph_builder, preflight_fn, candidate_builder = _fake_construction(
        h, graph_calls, candidate_calls)
    first_arm = probe.arm_order(0)[0]
    decode_calls: list[str] = []
    rss_state = {"armed": False, "post_arm_samples": 0}

    def rss_fn() -> int:
        if rss_state["armed"]:
            rss_state["post_arm_samples"] += 1
            if rss_state["post_arm_samples"] == 3:
                raise RuntimeError("scripted RSS monitor failure")
        return 1024

    def fake_decoder(arm: str):
        def decode(dense, prior, syndrome):
            decode_calls.append(arm)
            rss_state["armed"] = True
            estimate = np.zeros(probe.N, dtype=np.int64)
            estimate[:probe.M] = np.asarray(syndrome, dtype=np.int64)
            return SimpleNamespace(
                x_hat=estimate,
                syndrome_ok=layout.syndrome_ok(dense, estimate, syndrome),
                iterations=1,
                status="rss-stop-fixture",
            )
        return decode

    result = probe.execute_batch(
        out_root=relative,
        decode_fns={arm: fake_decoder(arm) for arm in probe.ARM_MAX_ITER},
        graph_builder=graph_builder,
        candidate_builder=candidate_builder,
        preflight_fn=preflight_fn,
        repo_root=repo,
        rss_fn=rss_fn,
    )

    root = repo / relative
    assert decode_calls == [first_arm]
    assert rss_state["post_arm_samples"] == 3
    assert {path.name for path in root.iterdir()} == {
        "manifest.json", "frame_records.csv", "summary.json",
        "EXPLORATION_LOG.md", "diagnostics.npz",
    }
    assert result["complete"] is False
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert result["attempted_call_counts"] == {
        first_arm: 1, "total": 1,
    } | {("candidate" if first_arm == "control" else "control"): 0}
    expected_marker = "rss_monitor_exception:RuntimeError:scripted RSS monitor failure"
    assert expected_marker in result["resource_stop_markers"]
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    assert result["paired"] is None
    with (root / "frame_records.csv").open(
            encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["arm"] == first_arm
    # This error arose in the pre-call RSS gate for the second arm, after the
    # first row had already been formed; its marker belongs to the batch stop.
    assert rows[0]["failure_reason"] == ""
    with np.load(root / "diagnostics.npz", allow_pickle=False) as data:
        assert len(data["call_arm"]) == 1
        assert data["call_vector_index"].tolist() == [0]
        assert data["vector_call_index"].tolist() == [0]
        assert data["vector_arm"].tolist() == [first_arm]
        assert data["raw_x_hat"].shape == (1, probe.N)


def test_prefix_violation_retains_both_rows_and_does_not_mutate_pair_inputs(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, relative = _test_root(tmp_path, monkeypatch, "itercap-prefix-stop")
    h = _fake_h()
    graph_calls: list[int] = []
    candidate_calls: list[int] = []
    graph_builder, preflight_fn, candidate_builder = _fake_construction(
        h, graph_calls, candidate_calls)
    assert probe.arm_order(0) == ("control", "candidate")
    seen: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}

    def decoder_for(arm: str):
        def decode(dense, prior, syndrome):
            seen[arm] = (np.asarray(dense).copy(), np.asarray(prior).copy(),
                         np.asarray(syndrome).copy())
            estimate = np.zeros(probe.N, dtype=np.int64)
            if arm == "candidate":
                estimate[:probe.M] = np.asarray(syndrome, dtype=np.int64)
            iterations = 90 if arm == "control" else 89
            return SimpleNamespace(
                x_hat=estimate,
                syndrome_ok=layout.syndrome_ok(dense, estimate, syndrome),
                iterations=iterations,
                status=f"prefix-{arm}",
            )
        return decode

    result = probe.execute_batch(
        out_root=relative,
        decode_fns={arm: decoder_for(arm) for arm in probe.ARM_MAX_ITER},
        graph_builder=graph_builder,
        candidate_builder=candidate_builder,
        preflight_fn=preflight_fn,
        repo_root=repo,
        rss_fn=lambda: 1024,
    )

    root = repo / relative
    assert set(seen) == {"control", "candidate"}
    for control_value, candidate_value in zip(seen["control"],
                                               seen["candidate"]):
        np.testing.assert_array_equal(control_value, candidate_value)
    assert result["terminal_status"] == "INTEGRITY_STOP"
    assert result["integrity_violations"] == 1
    assert result["complete"] is False
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    with (root / "frame_records.csv").open(
            encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    candidate_row = next(row for row in rows if row["arm"] == "candidate")
    assert candidate_row["prefix_check"] == "FAIL_CONTROL_SYNDROME_FAIL"
    assert "prefix_candidate_passed_by_control_cap" in candidate_row["failure_reason"]
    with np.load(root / "diagnostics.npz", allow_pickle=False) as data:
        assert data["call_vector_index"].tolist() == [0, 1]
        assert data["vector_call_index"].tolist() == [0, 1]


@pytest.mark.parametrize("failure", ["decoder_exception", "invalid_raw_vector"])
def test_second_arm_failure_retains_first_vector_and_unmapped_call(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    repo, relative = _test_root(tmp_path, monkeypatch,
                                f"itercap-second-arm-{failure}")
    h = _fake_h()
    graph_calls: list[int] = []
    candidate_calls: list[int] = []
    graph_builder, preflight_fn, candidate_builder = _fake_construction(
        h, graph_calls, candidate_calls)
    assert probe.arm_order(0) == ("control", "candidate")
    decode_calls: list[str] = []

    def decoder_for(arm: str):
        def decode(dense, prior, syndrome):
            decode_calls.append(arm)
            if arm == "candidate" and failure == "decoder_exception":
                raise RuntimeError("scripted second-arm decoder exception")
            estimate = np.zeros(probe.N, dtype=np.int64)
            estimate[:probe.M] = np.asarray(syndrome, dtype=np.int64)
            if arm == "candidate":
                estimate = estimate[:-1]
            return SimpleNamespace(
                x_hat=estimate,
                syndrome_ok=(layout.syndrome_ok(dense, estimate, syndrome)
                             if len(estimate) == probe.N else False),
                iterations=1,
                status=f"second-arm-{failure}",
            )
        return decode

    result = probe.execute_batch(
        out_root=relative,
        decode_fns={arm: decoder_for(arm) for arm in probe.ARM_MAX_ITER},
        graph_builder=graph_builder,
        candidate_builder=candidate_builder,
        preflight_fn=preflight_fn,
        repo_root=repo,
        rss_fn=lambda: 1024,
    )

    root = repo / relative
    assert decode_calls == ["control", "candidate"]
    assert result["terminal_status"] == "INTEGRITY_STOP"
    assert result["integrity_violations"] == 1
    assert result["complete"] is False
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    with (root / "frame_records.csv").open(
            encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert rows[0]["arm"] == "control"
    assert rows[0]["raw_vector_saved"] == "True"
    assert rows[1]["arm"] == "candidate"
    assert rows[1]["raw_vector_saved"] == "False"
    with np.load(root / "diagnostics.npz", allow_pickle=False) as data:
        assert data["call_vector_index"].tolist() == [0, -1]
        assert data["vector_call_index"].tolist() == [0]
        assert data["raw_x_hat"].shape == (1, probe.N)


def test_iteration_over_cap_stops_and_retains_the_returned_vector(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, relative = _test_root(tmp_path, monkeypatch, "itercap-over-cap")
    h = _fake_h()
    graph_calls: list[int] = []
    candidate_calls: list[int] = []
    graph_builder, preflight_fn, candidate_builder = _fake_construction(
        h, graph_calls, candidate_calls)
    calls: list[str] = []

    def decoder_for(arm: str):
        def decode(dense, prior, syndrome):
            calls.append(arm)
            estimate = np.zeros(probe.N, dtype=np.int64)
            estimate[:probe.M] = np.asarray(syndrome, dtype=np.int64)
            return SimpleNamespace(
                x_hat=estimate,
                syndrome_ok=layout.syndrome_ok(dense, estimate, syndrome),
                iterations=probe.ARM_MAX_ITER[arm] + 1,
                status="over-cap-fixture",
            )
        return decode

    result = probe.execute_batch(
        out_root=relative,
        decode_fns={arm: decoder_for(arm) for arm in probe.ARM_MAX_ITER},
        graph_builder=graph_builder,
        candidate_builder=candidate_builder,
        preflight_fn=preflight_fn,
        repo_root=repo,
        rss_fn=lambda: 1024,
    )

    root = repo / relative
    assert calls == ["control"]
    assert result["terminal_status"] == "INTEGRITY_STOP"
    assert result["integrity_violations"] == 1
    with (root / "frame_records.csv").open(
            encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert "decoder_iteration_count_out_of_arm_cap" in rows[0]["failure_reason"]
    assert rows[0]["raw_vector_saved"] == "True"
    with np.load(root / "diagnostics.npz", allow_pickle=False) as data:
        assert data["call_vector_index"].tolist() == [0]
        assert data["vector_call_index"].tolist() == [0]


def test_call_wall_cap_is_checked_after_return(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, relative = _test_root(tmp_path, monkeypatch, "itercap-call-wall")
    h = _fake_h()
    graph_calls: list[int] = []
    candidate_calls: list[int] = []
    graph_builder, preflight_fn, candidate_builder = _fake_construction(
        h, graph_calls, candidate_calls)
    clock = {"value": 0.0}
    calls: list[str] = []

    def decode(dense, prior, syndrome):
        calls.append("control")
        estimate = np.zeros(probe.N, dtype=np.int64)
        estimate[:probe.M] = np.asarray(syndrome, dtype=np.int64)
        clock["value"] = probe.CALL_CAP_S + 1.0
        return SimpleNamespace(
            x_hat=estimate,
            syndrome_ok=layout.syndrome_ok(dense, estimate, syndrome),
            iterations=1,
            status="call-wall-fixture",
        )

    decoders = {"control": decode, "candidate": decode}
    result = probe.execute_batch(
        out_root=relative,
        decode_fns=decoders,
        graph_builder=graph_builder,
        candidate_builder=candidate_builder,
        preflight_fn=preflight_fn,
        repo_root=repo,
        now=lambda: clock["value"],
        rss_fn=lambda: 1024,
    )

    assert calls == ["control"]
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert any("decoder_call_wall_cap_after_return" in marker
               for marker in result["resource_stop_markers"])
    assert result["attempted_call_counts"]["total"] == 1
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None


def test_total_wall_cap_stops_after_graph_before_decoder(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, relative = _test_root(tmp_path, monkeypatch, "itercap-total-wall")
    h = _fake_h()
    clock = {"value": 0.0}
    graph_calls: list[int] = []
    candidate_calls: list[int] = []
    graph_builder, preflight_fn, candidate_builder = _fake_construction(
        h, graph_calls, candidate_calls)

    def elapsed_graph(seed: int) -> dict:
        graph = graph_builder(seed)
        clock["value"] = probe.WALL_CAP_S + 1.0
        return graph

    decode_calls: list[str] = []
    result = probe.execute_batch(
        out_root=relative,
        decode_fns={arm: lambda *args: decode_calls.append(arm)
                    for arm in probe.ARM_MAX_ITER},
        graph_builder=elapsed_graph,
        candidate_builder=candidate_builder,
        preflight_fn=preflight_fn,
        repo_root=repo,
        now=lambda: clock["value"],
        rss_fn=lambda: 1024,
    )

    assert graph_calls == [probe.GRAPH_SEEDS[0]]
    assert candidate_calls == []
    assert decode_calls == []
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert any("total_wall_cap:" in marker
               for marker in result["resource_stop_markers"])
    assert result["attempted_call_counts"]["total"] == 0
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None


def test_primary_exception_and_post_diagnostics_rss_cap_are_both_retained(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, relative = _test_root(tmp_path, monkeypatch, "itercap-late-cap")
    h = _fake_h()
    graph_calls: list[int] = []
    candidate_calls: list[int] = []
    graph_builder, preflight_fn, candidate_builder = _fake_construction(
        h, graph_calls, candidate_calls)
    real_sample = probe.prior_runner.sample_error
    sample_count = 0
    rss_state = {"high": False}

    def failing_second_sample(seed, pmf, width=probe.N):
        nonlocal sample_count
        sample_count += 1
        if sample_count == 2:
            raise RuntimeError("scripted second-pair source failure")
        return real_sample(seed, pmf, width=width)

    monkeypatch.setattr(probe.prior_runner, "sample_error", failing_second_sample)
    write_diagnostics = probe._write_diagnostics

    def write_then_cross_rss_cap(root, arrays):
        size = write_diagnostics(root, arrays)
        rss_state["high"] = True
        return size

    monkeypatch.setattr(probe, "_write_diagnostics", write_then_cross_rss_cap)

    def fake_decoder(dense, prior, syndrome):
        estimate = np.zeros(probe.N, dtype=np.int64)
        estimate[:probe.M] = np.asarray(syndrome, dtype=np.int64)
        return SimpleNamespace(
            x_hat=estimate,
            syndrome_ok=layout.syndrome_ok(dense, estimate, syndrome),
            iterations=1,
            status="late-cap-fixture",
        )

    result = probe.execute_batch(
        out_root=relative,
        decode_fns={arm: fake_decoder for arm in probe.ARM_MAX_ITER},
        graph_builder=graph_builder,
        candidate_builder=candidate_builder,
        preflight_fn=preflight_fn,
        repo_root=repo,
        rss_fn=lambda: probe.RSS_CAP_BYTES if rss_state["high"] else 1024,
    )

    root = repo / relative
    primary = "implementation_exception:RuntimeError:scripted second-pair source failure"
    late_marker = "rss_cap:after_diagnostics_write"
    assert sample_count == 2
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert primary in result["stop_reasons"]
    assert late_marker in result["resource_stop_markers"]
    assert result["complete"] is False
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    assert {path.name for path in root.iterdir()} == {
        "manifest.json", "frame_records.csv", "summary.json",
        "EXPLORATION_LOG.md", "diagnostics.npz",
    }
    with (root / "frame_records.csv").open(
            encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    with np.load(root / "diagnostics.npz", allow_pickle=False) as data:
        assert data["call_vector_index"].tolist() == [0, 1]
        assert data["vector_call_index"].tolist() == [0, 1]


def test_diagnostics_payload_cap_stops_without_complete_metrics(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, relative = _test_root(tmp_path, monkeypatch, "itercap-payload-cap")
    h = _fake_h()
    graph_calls: list[int] = []
    candidate_calls: list[int] = []
    graph_builder, preflight_fn, candidate_builder = _fake_construction(
        h, graph_calls, candidate_calls)
    monkeypatch.setattr(probe, "ARTIFACT_LIMIT_BYTES", 0)
    decode_calls: list[str] = []

    def invalid_decoder(arm: str):
        def decode(*args):
            decode_calls.append(arm)
            return SimpleNamespace(
                x_hat=np.zeros(probe.N - 1, dtype=np.int64),
                syndrome_ok=False, iterations=1, status="payload-cap-fixture",
            )
        return decode

    result = probe.execute_batch(
        out_root=relative,
        decode_fns={arm: invalid_decoder(arm) for arm in probe.ARM_MAX_ITER},
        graph_builder=graph_builder,
        candidate_builder=candidate_builder,
        preflight_fn=preflight_fn,
        repo_root=repo,
        rss_fn=lambda: 1024,
    )

    root = repo / relative
    assert decode_calls == ["control"]
    assert result["terminal_status"] == "ARTIFACT_STOP"
    assert result["complete"] is False
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    assert any("diagnostics_write:ValueError" in reason
               for reason in result["stop_reasons"])
    assert "diagnostics.npz" not in {path.name for path in root.iterdir()}
    with (root / "frame_records.csv").open(
            encoding="utf-8", newline="") as handle:
        assert len(list(csv.DictReader(handle))) == 1


def test_full_fake_batch_uses_real_sampler_and_retains_same_return_vectors(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, relative = _test_root(tmp_path, monkeypatch, "itercap-full-fake")
    h = _fake_h()
    deep_h = h.copy()
    deep_h[0, probe.M] = 1
    graph_calls: list[int] = []
    candidate_calls: list[int] = []
    graph_builder, preflight_fn, candidate_builder = _fake_construction(
        h, graph_calls, candidate_calls, deep_h=deep_h)
    samples = _install_sample_spy(monkeypatch)
    calls: dict[str, list[tuple[np.ndarray, np.ndarray, np.ndarray]]] = {
        "control": [], "candidate": [],
    }

    def decoder_for(arm: str):
        cap = probe.ARM_MAX_ITER[arm]

        def fake_decoder(dense, prior, syndrome):
            dense = np.asarray(dense, dtype=np.int64)
            prior = np.asarray(prior, dtype=np.float64)
            syndrome = np.asarray(syndrome, dtype=np.int64)
            calls[arm].append((dense.copy(), prior.copy(), syndrome.copy()))
            mode = int(syndrome.sum()) % 3
            if mode == 0 or (mode == 1 and arm == "candidate"):
                estimate = np.zeros(probe.N, dtype=np.int64)
                estimate[:probe.M] = syndrome
                estimate[-1] = 1
                iterations = 3 if mode == 0 else 120
                status = "same-prefix" if mode == 0 else "late-valid"
            else:
                estimate = np.zeros(probe.N, dtype=np.int64)
                iterations = cap
                status = f"fake-fail-{cap}"
            return SimpleNamespace(
                x_hat=estimate,
                syndrome_ok=layout.syndrome_ok(dense, estimate, syndrome),
                iterations=iterations,
                status=status,
            )

        return fake_decoder

    decode_fns = {arm: decoder_for(arm) for arm in probe.ARM_MAX_ITER}
    monkeypatch.setattr(
        probe, "_bind_production_decoders",
        lambda *args, **kwargs: pytest.fail("fake execute bound production BP"),
    )
    monkeypatch.setattr(
        probe.search_runner, "build_profile_graph",
        lambda *args, **kwargs: pytest.fail("fake execute built production graph"),
    )
    monkeypatch.setattr(
        probe.search_runner, "_candidate_pair_for_graph",
        lambda *args, **kwargs: pytest.fail("fake execute built production candidate"),
    )

    result = probe.execute_batch(
        out_root=relative,
        decode_fns=decode_fns,
        graph_builder=graph_builder,
        candidate_builder=candidate_builder,
        preflight_fn=preflight_fn,
        repo_root=repo,
        rss_fn=lambda: 1024,
    )

    root = repo / relative
    expected_files = {
        "manifest.json", "frame_records.csv", "summary.json",
        "EXPLORATION_LOG.md", "diagnostics.npz",
    }
    assert {path.name for path in root.iterdir()} == expected_files
    assert result["complete"] is True
    assert result["terminal_status"] == "COMPLETE"
    assert result["classification"] == "CONTROL_RANGE_UNINFORMATIVE"
    assert result["attempted_call_counts"] == {
        "control": probe.HOLDOUT_PAIRS,
        "candidate": probe.HOLDOUT_PAIRS,
        "total": probe.MAX_CALLS,
    }
    assert result["disclosed_syndrome_bits"] == (
        probe.MAX_CALLS * probe.SYNDROME_BITS)
    assert result["tag_bits"] == 0
    assert result["verification"] == "NOT_IMPLEMENTED"
    assert result["undetected"] == "NOT_MEASURED"
    assert result["resource_measurement"]["max_rss_bytes"] == 1024

    plan = probe.seed_plan()
    assert graph_calls == candidate_calls == list(probe.GRAPH_SEEDS)
    assert len(samples) == probe.HOLDOUT_PAIRS == len(plan)
    assert [seed for seed, _ in samples] == [row[3] for row in plan]
    assert len({seed for seed, _ in samples}) == probe.HOLDOUT_PAIRS
    assert len(calls["control"]) == len(calls["candidate"]) == probe.HOLDOUT_PAIRS
    for control_input, candidate_input in zip(
            calls["control"], calls["candidate"]):
        np.testing.assert_array_equal(control_input[0], deep_h)
        for control_value, candidate_value in zip(
                control_input, candidate_input):
            np.testing.assert_array_equal(control_value, candidate_value)

    with (root / "frame_records.csv").open(
            encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == probe.MAX_CALLS
    assert [int(row["call_index"]) for row in rows] == list(
        range(probe.MAX_CALLS))
    assert [int(row["max_iter"]) for row in rows] == [
        probe.ARM_MAX_ITER[row["arm"]] for row in rows]
    grouped: dict[int, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(int(row["pair_index"]), []).append(row)
        assert row["status"] not in {"", "None"}
        assert 0 <= int(row["iterations"]) <= int(row["max_iter"])
        if _csv_bool(row["syndrome_accept"]) is False:
            assert int(row["iterations"]) == int(row["max_iter"])
    for pair_index, (graph_seed, stream, frame, seed) in enumerate(plan):
        pair_rows = sorted(grouped[pair_index], key=lambda row: int(row["call_index"]))
        assert [(row["arm"], int(row["max_iter"])) for row in pair_rows] == [
            (arm, probe.ARM_MAX_ITER[arm]) for arm in probe.arm_order(frame)]
        for row in pair_rows:
            assert (int(row["graph_seed"]), int(row["stream"]),
                    int(row["frame"]), int(row["seed"])) == (
                        graph_seed, stream, frame, seed)
    csv_by_call = {int(row["call_index"]): row for row in rows}
    assert any(_csv_bool(row["syndrome_accept"]) is False for row in rows)

    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    assert manifest["batch_uuid"] == summary["batch_uuid"] == probe.BATCH_UUID
    assert manifest["contract"] == summary["contract"] == probe.CONTRACT
    assert manifest["status"] == summary["terminal_status"] == "COMPLETE"
    with np.load(root / "diagnostics.npz", allow_pickle=False) as data:
        assert data["H"].shape == (len(probe.GRAPH_SEEDS), probe.M, probe.N)
        for matrix in data["H"]:
            np.testing.assert_array_equal(matrix, deep_h)
        assert data["pair_truth"].shape == (probe.HOLDOUT_PAIRS, probe.N)
        assert data["pair_syndrome"].shape == (probe.HOLDOUT_PAIRS, probe.M)
        assert data["raw_x_hat"].shape == (probe.MAX_CALLS, probe.N)
        assert np.array_equal(data["pair_truth"], np.stack(
            [truth for _, truth in samples]))
        assert np.array_equal(data["pair_seed"], np.asarray(
            [row[3] for row in plan], dtype=np.int64))
        assert np.all(data["call_vector_index"] >= 0)
        assert np.array_equal(data["vector_call_index"],
                              np.arange(probe.MAX_CALLS))
        pair_position = {
            int(pair_index): index
            for index, pair_index in enumerate(data["pair_index"])
        }
        for pair_index, (graph_seed, _stream, _frame, _seed) in enumerate(plan):
            pair_i = pair_position[pair_index]
            assert int(data["pair_graph_seed"][pair_i]) == graph_seed
            graph_i = int(data["pair_graph_index"][pair_i])
            assert int(data["graph_seed"][graph_i]) == graph_seed
        for call_index, row in csv_by_call.items():
            pair_index = int(row["pair_index"])
            pair_i = pair_position[pair_index]
            vector_i = int(data["call_vector_index"][call_index])
            raw = data["raw_x_hat"][vector_i].astype(np.int64)
            truth = data["pair_truth"][pair_i].astype(np.int64)
            syndrome = data["pair_syndrome"][pair_i].astype(np.int64)
            h_i = int(data["pair_graph_index"][pair_i])
            matrix = data["H"][h_i].astype(np.int64)
            equal = np.array_equal(raw, truth)
            syndrome_ok = layout.syndrome_ok(matrix, raw, syndrome)
            assert _csv_bool(row["raw_vector_saved"]) is True
            assert _csv_bool(row["raw_symbols_equal"]) is equal
            assert _csv_bool(row["syndrome_accept"]) is syndrome_ok
            assert _csv_bool(row["exact"]) is (equal and syndrome_ok)
            assert _csv_bool(row["syndrome_consistent_wrong"]) is (
                syndrome_ok and not equal)

    log = (root / "EXPLORATION_LOG.md").read_text(encoding="utf-8")
    assert f"terminal=COMPLETE" in log
