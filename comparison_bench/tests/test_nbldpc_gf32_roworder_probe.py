"""Fake-only contract tests for the fixed GF32 row-order probe."""
from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_roworder_probe as probe
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout


def _identity_checks() -> np.ndarray:
    """A compact, truth-blind decoder fixture: 52 checks on 128 symbols."""
    h = np.zeros((52, 128), dtype=np.int64)
    h[np.arange(52), np.arange(52)] = 1
    return h


def _repo_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
               name: str) -> tuple[Path, Path]:
    repo = tmp_path / f"repo-{name}"
    (repo / "workspace").mkdir(parents=True)
    relative = Path("workspace") / name
    monkeypatch.setattr(probe, "OUT_ROOT_RELATIVE", relative)
    return repo, relative


def _fake_builders(h: np.ndarray, *, deep_h: np.ndarray | None = None,
                   graph_calls=None, candidate_calls=None):
    graph_calls = [] if graph_calls is None else graph_calls
    candidate_calls = [] if candidate_calls is None else candidate_calls
    deep = h if deep_h is None else np.asarray(deep_h, dtype=np.int64)

    def graph_builder(graph_seed: int) -> dict:
        graph_calls.append(int(graph_seed))
        return {"dense": h.copy(), "graph_seed": int(graph_seed)}

    def preflight_fn(graph, graph_seed: int):
        assert int(graph_seed) in probe.GRAPH_SEEDS
        return True, {"fake_preflight": True}

    def candidate_builder(dense, pmf, graph_seed: int):
        candidate_calls.append(int(graph_seed))
        np.testing.assert_array_equal(dense, h)
        assert np.asarray(pmf).shape == (32,)
        assert np.isclose(np.asarray(pmf).sum(), 1.0)
        return h.copy(), deep.copy(), {
            "candidate_admitted": True,
            "deep_candidate_admitted": True,
            "construction_stop": False,
        }

    return graph_builder, candidate_builder, preflight_fn


def _syndrome_only_decoder(calls: list[dict], arm: str):
    """Return a valid word from H and syndrome only; truth is never passed."""
    def decode(h, prior, syndrome):
        h = np.asarray(h, dtype=np.int64)
        prior = np.asarray(prior, dtype=np.float64)
        syndrome = np.asarray(syndrome, dtype=np.int64).ravel()
        calls.append({"arm": arm, "H": h.copy(), "prior": prior.copy(),
                      "syndrome": syndrome.copy()})
        estimate = np.zeros(h.shape[1], dtype=np.int64)
        for row_index, row in enumerate(h):
            nonzero = np.flatnonzero(row)
            if nonzero.size:
                assert nonzero.size == 1
                coefficient = int(row[nonzero[0]])
                inverse = next(
                    value for value in range(1, 32)
                    if layout.gf32_mul(coefficient, value) == 1)
                estimate[int(nonzero[0])] = layout.gf32_mul(
                    int(syndrome[row_index]), inverse)
        return SimpleNamespace(x_hat=estimate, syndrome_ok=True,
                               iterations=1, status="fake_syndrome_solution")
    return decode


def _execute_kwargs(h: np.ndarray, calls: list[dict], *, deep_h=None,
                    graph_calls=None, candidate_calls=None):
    graph_builder, candidate_builder, preflight_fn = _fake_builders(
        h, deep_h=deep_h, graph_calls=graph_calls,
        candidate_calls=candidate_calls)
    decode_fns = {
        "control": _syndrome_only_decoder(calls, "control"),
        "candidate": _syndrome_only_decoder(calls, "candidate"),
    }
    return {"decode_fns": decode_fns, "graph_builder": graph_builder,
            "candidate_builder": candidate_builder,
            "preflight_fn": preflight_fn}


def test_degree_block_reversal_is_a_bijection_with_synchronized_syndrome():
    h = np.asarray([
        [1, 2, 0, 0, 0],
        [0, 3, 0, 0, 0],
        [0, 0, 4, 5, 0],
        [0, 0, 0, 0, 6],
    ], dtype=np.int64)
    pi = np.asarray(probe.row_permutation(h), dtype=np.int64)
    np.testing.assert_array_equal(pi, [2, 0, 3, 1])
    np.testing.assert_array_equal(np.sort(pi), np.arange(h.shape[0]))

    truth = np.asarray([2, 7, 1, 4, 9], dtype=np.int64)
    base_syndrome = np.asarray(layout.gf32_syndrome(h, truth), dtype=np.int64)
    candidate_syndrome = np.asarray(
        layout.gf32_syndrome(h[pi], truth), dtype=np.int64)
    np.testing.assert_array_equal(candidate_syndrome, base_syndrome[pi])


def test_production_binding_is_lazy_and_keeps_the_frozen_v35_profile(
        monkeypatch: pytest.MonkeyPatch):
    from comparison_bench.formal_ir import v35_algorithm_development as v35

    calls: list[dict] = []

    def decoder_spy(h, prior, syndrome, **kwargs):
        calls.append({"H": np.asarray(h).copy(),
                      "prior": np.asarray(prior).copy(),
                      "syndrome": np.asarray(syndrome).copy(),
                      "kwargs": dict(kwargs)})
        return SimpleNamespace(x_hat=np.zeros(128, dtype=np.int64),
                               syndrome_ok=False, iterations=90,
                               status="binding_spy")

    monkeypatch.setattr(v35, "decode_row_layered_fftqspa", decoder_spy)
    bound = probe._bind_production()
    assert set(bound) == {"decode_fns", "graph_builder",
                          "candidate_builder", "preflight_fn"}
    control = bound["decode_fns"]["control"]
    candidate = bound["decode_fns"]["candidate"]
    assert control is candidate
    h = _identity_checks()
    prior = np.full((128, 32), 1.0 / 32.0)
    syndrome = np.zeros(52, dtype=np.int64)
    control(h, prior, syndrome)
    candidate(h[::-1], prior, syndrome[::-1])
    assert len(calls) == 2
    for call in calls:
        assert call["kwargs"] == {
            "max_iter": 90, "damping_alpha": 1.0,
            "warm_beliefs": None, "field": None,
        }
    np.testing.assert_array_equal(calls[0]["H"], h)
    np.testing.assert_array_equal(calls[1]["H"], h[::-1])


def test_t0_and_dry_run_have_no_science_or_artifact_side_effects(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo, relative = _repo_root(tmp_path, monkeypatch, "dry-run")
    result = probe.dry_run(relative, repo_root=repo)
    assert result["status"] == "DRY_RUN"
    assert result["exists"] is False
    assert result["holdout_pairs"] == 192
    assert result["maximum_decoder_calls"] == 384
    assert result["t0"] and all(result["t0"].values())
    zero_counters = (
        "attempted_decoder_calls", "writes", "artifact_reads", "graph_calls",
        "preflight_calls", "candidate_calls", "sampler_calls",
        "decoder_calls", "osd_calls",
    )
    assert all(result[key] == 0 for key in zero_counters)
    assert not (repo / relative).exists()


def test_full_entry_uses_real_sampler_once_per_pair_and_keeps_pair_lineage(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    h = _identity_checks()
    deep_h = h.copy()
    deep_h[np.arange(52), np.arange(52)] = (
        np.arange(52, dtype=np.int64) % 31) + 1
    assert np.any(deep_h != h)
    np.testing.assert_array_equal(deep_h != 0, h != 0)
    repo, relative = _repo_root(tmp_path, monkeypatch, "full-fake")
    graph_calls: list[int] = []
    candidate_calls: list[int] = []
    calls: list[dict] = []
    kwargs = _execute_kwargs(h, calls, deep_h=deep_h,
                             graph_calls=graph_calls,
                             candidate_calls=candidate_calls)

    original_sample = probe.prior_runner.sample_error
    sampled: list[tuple[int, np.ndarray]] = []

    def sample_spy(seed, pmf, width=128):
        truth = np.asarray(original_sample(seed, pmf, width=width),
                           dtype=np.int64)
        sampled.append((int(seed), truth.copy()))
        return truth

    monkeypatch.setattr(probe.prior_runner, "sample_error", sample_spy)
    result = probe.execute_batch(
        out_root=relative, repo_root=repo, now=lambda: 1.0,
        rss_fn=lambda: 0, **kwargs)
    assert result["complete"] is True
    assert len(calls) == 384
    assert len(sampled) == probe.HOLDOUT_PAIRS == 192
    assert len(graph_calls) == len(probe.GRAPH_SEEDS)
    assert len(candidate_calls) == len(probe.GRAPH_SEEDS)

    with (repo / relative / "frame_records.csv").open(
            newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 384
    with np.load(repo / relative / "diagnostics.npz", allow_pickle=False) as data:
        arrays = {key: data[key].copy() for key in data.files}

    required = {
        "graph_seed", "H_base", "H_candidate", "row_permutation",
        "pair_index", "pair_graph_index", "pair_graph_seed", "pair_stream",
        "pair_frame", "pair_seed", "pair_truth", "pair_syndrome_base",
        "pair_syndrome_candidate", "call_index", "call_pair_index",
        "call_arm", "call_vector_index", "vector_call_index",
        "vector_pair_index", "vector_arm", "vector_graph_seed",
        "vector_stream", "vector_frame", "vector_seed", "raw_x_hat",
    }
    assert required <= set(arrays)
    assert len(arrays["pair_index"]) == probe.HOLDOUT_PAIRS
    assert len(arrays["call_index"]) == len(arrays["call_vector_index"]) == 384
    assert len(arrays["vector_call_index"]) == arrays["raw_x_hat"].shape[0] == 384
    np.testing.assert_array_equal(
        arrays["graph_seed"][arrays["pair_graph_index"]],
        arrays["pair_graph_seed"])
    assert len(set(int(v) for v in arrays["pair_seed"])) == probe.HOLDOUT_PAIRS
    assert [seed for seed, _ in sampled] == [int(v) for v in arrays["pair_seed"]]

    graph_positions = {
        int(seed): index for index, seed in enumerate(arrays["graph_seed"])}
    for pair_index in range(probe.HOLDOUT_PAIRS):
        graph_seed = int(arrays["pair_graph_seed"][pair_index])
        graph_index = int(arrays["pair_graph_index"][pair_index])
        assert graph_positions[graph_seed] == graph_index
        base_h = arrays["H_base"][graph_index]
        mapped_deep_h = arrays["H_candidate"][graph_index]
        pi = arrays["row_permutation"][graph_index]
        np.testing.assert_array_equal(mapped_deep_h, deep_h)
        np.testing.assert_array_equal(mapped_deep_h != 0, base_h != 0)
        assert np.any(mapped_deep_h != base_h)
        np.testing.assert_array_equal(
            pi, probe.row_permutation(mapped_deep_h))
        candidate_h = mapped_deep_h[pi]
        truth = arrays["pair_truth"][pair_index]
        base_syn = np.asarray(
            layout.gf32_syndrome(mapped_deep_h, truth), dtype=np.int64)
        candidate_syn = np.asarray(
            layout.gf32_syndrome(candidate_h, truth), dtype=np.int64)
        np.testing.assert_array_equal(base_syn,
                                      arrays["pair_syndrome_base"][pair_index])
        np.testing.assert_array_equal(
            candidate_syn, arrays["pair_syndrome_candidate"][pair_index])
        np.testing.assert_array_equal(candidate_syn, base_syn[pi])

        first, second = calls[2 * pair_index:2 * pair_index + 2]
        expected_arms = (("control", "candidate")
                         if int(arrays["pair_frame"][pair_index]) % 2 == 0
                         else ("candidate", "control"))
        assert (first["arm"], second["arm"]) == expected_arms
        by_arm = {call["arm"]: call for call in (first, second)}
        np.testing.assert_array_equal(by_arm["control"]["H"], mapped_deep_h)
        np.testing.assert_array_equal(by_arm["candidate"]["H"], candidate_h)
        np.testing.assert_array_equal(by_arm["control"]["syndrome"], base_syn)
        np.testing.assert_array_equal(
            by_arm["candidate"]["syndrome"], candidate_syn)
        np.testing.assert_array_equal(by_arm["control"]["prior"],
                                      by_arm["candidate"]["prior"])
        np.testing.assert_array_equal(by_arm["control"]["prior"],
                                      np.tile(by_arm["control"]["prior"][0],
                                              (128, 1)))

    assert all(row["raw_vector_saved"] == "True" for row in rows)
    for call_index, row in enumerate(rows):
        assert int(row["call_index"]) == call_index
        assert row["arm"] == str(arrays["call_arm"][call_index])
        assert int(arrays["call_vector_index"][call_index]) >= 0


def test_second_arm_failure_retains_first_vector_and_stops_batch(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    h = _identity_checks()
    repo, relative = _repo_root(tmp_path, monkeypatch, "partial")
    calls: list[dict] = []
    kwargs = _execute_kwargs(h, calls)

    def candidate_raises(h_matrix, prior, syndrome):
        raise RuntimeError("fake second-arm failure")

    kwargs["decode_fns"]["candidate"] = candidate_raises
    result = probe.execute_batch(out_root=relative, repo_root=repo,
                                 now=lambda: 1.0, rss_fn=lambda: 0, **kwargs)
    assert result["complete"] is False
    assert len(calls) == 1
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    assert result["delta"] is None
    with (repo / relative / "frame_records.csv").open(
            newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert rows[0]["arm"] == "control"
    assert rows[0]["raw_vector_saved"] == "True"
    assert rows[1]["arm"] == "candidate"
    assert rows[1]["raw_vector_saved"] == "False"
    with np.load(repo / relative / "diagnostics.npz", allow_pickle=False) as data:
        assert len(data["call_index"]) == 2
        assert data["call_vector_index"].tolist() == [0, -1]
        assert data["vector_call_index"].tolist() == [0]
        assert data["raw_x_hat"].shape == (1, 128)


def test_second_arm_rss_stop_retains_returned_vectors_and_stops_batch(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    h = _identity_checks()
    repo, relative = _repo_root(tmp_path, monkeypatch, "rss-partial")
    calls: list[dict] = []
    kwargs = _execute_kwargs(h, calls)
    rss_high = {"value": False}
    candidate = kwargs["decode_fns"]["candidate"]

    def candidate_then_rss_cap(h_matrix, prior, syndrome):
        result = candidate(h_matrix, prior, syndrome)
        rss_high["value"] = True
        return result

    kwargs["decode_fns"]["candidate"] = candidate_then_rss_cap
    result = probe.execute_batch(
        out_root=relative, repo_root=repo, now=lambda: 1.0,
        rss_fn=lambda: probe.RSS_CAP_BYTES + 1 if rss_high["value"] else 0,
        **kwargs)
    assert result["complete"] is False
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert len(calls) == 2
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    assert result["delta"] is None
    assert result["resource_stop_markers"]
    with (repo / relative / "frame_records.csv").open(
            newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert all(row["raw_vector_saved"] == "True" for row in rows)
    with np.load(repo / relative / "diagnostics.npz", allow_pickle=False) as data:
        assert data["call_vector_index"].tolist() == [0, 1]
        assert data["vector_call_index"].tolist() == [0, 1]
        assert data["raw_x_hat"].shape == (2, 128)


def test_call_count_cap_stops_before_the_next_arm(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    h = _identity_checks()
    repo, relative = _repo_root(tmp_path, monkeypatch, "call-cap")
    calls: list[dict] = []
    kwargs = _execute_kwargs(h, calls)
    monkeypatch.setattr(probe, "MAX_CALLS", 1)
    monkeypatch.setattr(probe, "verify_t0", lambda: {"fake_t0": True})

    result = probe.execute_batch(out_root=relative, repo_root=repo,
                                 now=lambda: 1.0, rss_fn=lambda: 0, **kwargs)
    assert result["complete"] is False
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert len(calls) == 1
    assert result["resource_stop_markers"] == [
        "decoder_call_count_cap_before_next_call"]
    with np.load(repo / relative / "diagnostics.npz", allow_pickle=False) as data:
        assert data["call_index"].tolist() == [0]
        assert data["call_vector_index"].tolist() == [0]
        assert data["vector_call_index"].tolist() == [0]


@pytest.mark.parametrize(
    ("iterations", "expected_issue"),
    [(89, "raw_failure_not_at_cap"),
     (90, ""),
     (91, "iteration_count_integrity")],
)
def test_iteration_cap_and_fail_at_cap_are_observed_from_returned_vector(
        iterations: int, expected_issue: str):
    h = _identity_checks()
    truth = np.zeros(128, dtype=np.int64)
    syndrome = np.asarray(layout.gf32_syndrome(h, truth), dtype=np.int64)
    estimate = np.zeros_like(truth)
    estimate[0] = 1
    result = SimpleNamespace(
        x_hat=estimate, syndrome_ok=False, iterations=iterations,
        status="fake_raw_syndrome_fail")
    row, raw, issue = probe._observe_call(
        lambda _h, _prior, _syn: result, h, np.full((128, 32), 1.0 / 32),
        syndrome, truth, h, syndrome, now=lambda: 1.0,
        rss_fn=lambda: 0, arm="control")
    assert raw is not None
    assert row["syndrome_accept"] is False
    assert row["base_syndrome_accept"] is False
    assert row["exact"] is False
    assert expected_issue in issue


def test_summary_keeps_syndrome_valid_wrong_separate_from_exact():
    def row(pair_index, arm, *, exact, syndrome, wrong=False):
        return {
            "pair_index": pair_index, "graph_seed": probe.GRAPH_SEEDS[0],
            "arm": arm, "exact": exact, "syndrome_accept": syndrome,
            "base_syndrome_accept": syndrome,
            "syndrome_consistent_wrong": wrong, "iterations": 90,
            "wall_s": 0.1, "rss_b": 10,
        }

    rows = [
        row(0, "control", exact=True, syndrome=True),
        row(0, "candidate", exact=True, syndrome=True),
        row(1, "control", exact=True, syndrome=True),
        row(1, "candidate", exact=False, syndrome=False),
        row(2, "control", exact=False, syndrome=False),
        row(2, "candidate", exact=True, syndrome=True),
        row(3, "control", exact=False, syndrome=False),
        row(3, "candidate", exact=False, syndrome=True, wrong=True),
        row(4, "control", exact=False, syndrome=False),
        row(4, "candidate", exact=False, syndrome=False),
    ]
    result = probe._summarize(rows, expected_pairs=5)
    assert result["complete"] is True
    assert result["paired"] == {
        "both": 1, "control_only": 1, "candidate_only": 1, "neither": 2,
    }
    assert result["candidate_exact"] == 2
    assert result["control_exact"] == 2
    assert result["delta"] == 0
    assert result["per_arm_outcomes"]["candidate"]["syndrome_valid_wrong"] == 1
    assert result["transitions"] == {
        "control_raw_fail_to_candidate_exact": 1,
        "control_raw_fail_to_candidate_valid_wrong": 1,
        "control_raw_fail_to_candidate_still_fail": 1,
    }


def test_summary_applies_frozen_screen_at_control_minimum_and_delta_edge():
    rows = []
    capacities = (8, 8, 8, 9, 9, 9)
    control_successes = (6, 6, 6, 7, 7, 7)
    pair_index = 0
    for graph_seed, capacity, control_success in zip(
            probe.GRAPH_SEEDS, capacities, control_successes):
        for frame in range(capacity):
            rows.append({
                "pair_index": pair_index, "graph_seed": graph_seed,
                "arm": "control", "exact": frame < control_success,
                "syndrome_accept": frame < control_success,
                "base_syndrome_accept": frame < control_success,
                "syndrome_consistent_wrong": False,
                "iterations": 90, "wall_s": 0.1, "rss_b": 10,
            })
            rows.append({
                "pair_index": pair_index, "graph_seed": graph_seed,
                "arm": "candidate", "exact": True,
                "syndrome_accept": True, "base_syndrome_accept": True,
                "syndrome_consistent_wrong": False,
                "iterations": 90, "wall_s": 0.1, "rss_b": 10,
            })
            pair_index += 1
    result = probe._summarize(rows, expected_pairs=pair_index)
    assert result["complete"] is True
    assert result["control_exact"] == probe.CONTROL_MIN == 39
    assert result["candidate_exact"] == 51
    assert result["delta"] == probe.SIGNAL_DELTA == 12
    assert result["positive_graphs"] == len(probe.GRAPH_SEEDS)
    assert result["classification"] == "MECHANISM_SIGNAL"


def test_diagnostics_size_cap_refuses_to_write_oversized_payload(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / "cap-root"
    root.mkdir()
    monkeypatch.setattr(probe, "ARTIFACT_LIMIT_BYTES", 0)
    with pytest.raises(ValueError, match="payload exceeds"):
        probe._write_diagnostics(root, {"x": np.asarray([1], dtype=np.uint8)})
    assert not (root / "diagnostics.npz").exists()


def test_existing_output_root_is_refused_before_any_fake_callback(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    h = _identity_checks()
    repo, relative = _repo_root(tmp_path, monkeypatch, "already-there")
    target = repo / relative
    target.mkdir(parents=True)
    sentinel = target / "sentinel.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    calls: list[dict] = []
    graph_calls: list[int] = []
    candidate_calls: list[int] = []
    kwargs = _execute_kwargs(h, calls, graph_calls=graph_calls,
                             candidate_calls=candidate_calls)

    with pytest.raises(FileExistsError):
        probe.execute_batch(out_root=relative, repo_root=repo,
                            now=lambda: 1.0, rss_fn=lambda: 0, **kwargs)
    assert calls == []
    assert graph_calls == []
    assert candidate_calls == []
    assert sentinel.read_text(encoding="utf-8") == "preserve"
