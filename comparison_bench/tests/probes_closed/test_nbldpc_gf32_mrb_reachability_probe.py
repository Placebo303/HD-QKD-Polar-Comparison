from __future__ import annotations

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli.probes_closed import nbldpc_gf32_mrb_reachability_probe as probe
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from comparison_bench.formal_ir.nonbinary_field import GF2mField


def _beliefs_with_gaps(gaps: list[float]) -> np.ndarray:
    beliefs = np.zeros((len(gaps), 32), dtype=np.float64)
    for row, gap in enumerate(gaps):
        beliefs[row, 0] = gap
    return beliefs


def _syndrome(field: GF2mField, matrix: np.ndarray,
              vector: list[int]) -> list[int]:
    result = []
    for row in matrix:
        total = 0
        for coefficient, symbol in zip(row, vector):
            if int(coefficient) and int(symbol):
                total = field.add(
                    total, field.mul(int(coefficient), int(symbol)))
        result.append(total)
    return result


@pytest.mark.parametrize(
    ("truth", "expected_distance"),
    [([2, 2, 4], 0), ([7, 7, 4], 1), ([7, 7, 9], 2)],
)
def test_tiny_gf32_reachability_distances_use_permuted_free_columns(
        truth: list[int], expected_distance: int) -> None:
    field = GF2mField.create(32)
    matrix = np.asarray([[1, 1, 0]], dtype=np.int64)
    syndrome = _syndrome(field, matrix, truth)
    raw_hard = np.asarray([2, 0, 4], dtype=np.int64)
    beliefs = _beliefs_with_gaps([0.2, 0.1, 0.3])
    beliefs_before = beliefs.copy()

    result = probe._mrb_reachability_diagnostic(
        field=field, matrix=matrix, syndrome=syndrome,
        final_beliefs=beliefs, raw_hard=raw_hard, truth=truth)

    assert result["permutation"] == [1, 0, 2]
    assert result["pivot_cols"] == [0]
    # The reliability permutation makes original column 1 the pivot; without
    # it, the first pivot would be original column 0.
    assert result["pivot_original_cols"] == [1]
    assert result["free_cols"] == [1, 2]
    assert result["rank"] == 1
    assert result["free_count"] == 2
    assert result["D_free"] == expected_distance
    assert result["raw_free_base"] == [2, 2, 4]
    assert result["raw_free_base"] != [0, 0, 4]
    assert result["truth_reconstructed"] == truth
    assert result["truth_syndrome_ok"]
    assert result["truth_reconstruction_ok"]
    assert result["base_syndrome_ok"]
    assert result["base_equals_truth"] is (expected_distance == 0)
    assert np.array_equal(beliefs, beliefs_before)


def test_tiny_gf32_reachability_keeps_stable_original_order_for_ties() -> None:
    field = GF2mField.create(32)
    matrix = np.asarray([[1, 1, 0]], dtype=np.int64)
    beliefs = _beliefs_with_gaps([0.1, 0.1, 0.3])
    result = probe._mrb_reachability_diagnostic(
        field=field, matrix=matrix, syndrome=[0],
        final_beliefs=beliefs, raw_hard=[0, 0, 0], truth=[0, 0, 0])
    assert result["permutation"] == [0, 1, 2]
    assert result["pivot_original_cols"] == [0]


def test_tiny_gf32_reachability_stops_on_rank_or_nonfinite_beliefs() -> None:
    field = GF2mField.create(32)
    dependent_matrix = np.asarray(
        [[1, 1, 0], [2, 2, 0]], dtype=np.int64)
    with pytest.raises(ValueError, match="rank"):
        probe._mrb_reachability_diagnostic(
            field=field, matrix=dependent_matrix, syndrome=[0, 0],
            final_beliefs=np.zeros((3, 32)), raw_hard=[0, 0, 0],
            truth=[0, 0, 0])

    beliefs = np.zeros((3, 32), dtype=np.float64)
    beliefs[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        probe._mrb_reachability_diagnostic(
            field=field, matrix=dependent_matrix[:1], syndrome=[0],
            final_beliefs=beliefs, raw_hard=[0, 0, 0],
            truth=[0, 0, 0])


class _Clock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value


def _fake_graph() -> np.ndarray:
    matrix = np.zeros((probe.M, probe.N), dtype=np.int64)
    matrix[np.arange(probe.M), np.arange(probe.M)] = 1
    return matrix


def _fake_callbacks(*, matrix: np.ndarray | None = None,
                    graph_calls: list[int] | None = None,
                    candidate_calls: list[int] | None = None):
    dense = _fake_graph() if matrix is None else np.asarray(matrix).copy()
    graph_calls = [] if graph_calls is None else graph_calls
    candidate_calls = [] if candidate_calls is None else candidate_calls

    def graph_builder(seed):
        graph_calls.append(int(seed))
        return {"dense": dense.copy()}

    def preflight(graph, seed):
        return True, {"graph_seed": int(seed), "status": "fake"}

    def candidate_builder(graph_h, pmf, seed):
        candidate_calls.append(int(seed))
        return dense.copy(), dense.copy(), {
            "candidate_admitted": True,
            "deep_candidate_admitted": True,
            "construction_stop": False,
        }

    return dense, graph_builder, preflight, candidate_builder


def _test_repo(tmp_path: Path, monkeypatch,
               root_name: str = "reachability-test-root") -> tuple[Path, Path]:
    repo = tmp_path / ("repo-" + root_name)
    (repo / "workspace").mkdir(parents=True)
    relative = Path("workspace") / root_name
    monkeypatch.setattr(probe, "OUT_ROOT_RELATIVE", relative)
    return repo, relative


def _load_csv(root: Path) -> list[dict[str, str]]:
    with (root / "frame_records.csv").open(
            encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def test_dry_run_is_no_write_and_refuses_existing_or_wrong_root(
        tmp_path: Path, monkeypatch) -> None:
    repo, relative = _test_repo(tmp_path, monkeypatch)
    result = probe.dry_run(relative, repo_root=repo)
    assert result["status"] == "DRY_RUN"
    assert result["writes"] == result["artifact_reads"] == 0
    assert result["graph_construction_calls"] == 0
    assert result["decoder_calls"] == result["osd_calls"] == 0
    assert result["holdout_call_count"] == probe.MAX_CALLS
    assert not (repo / relative).exists()

    (repo / relative).mkdir()
    with pytest.raises(FileExistsError, match="existing output root"):
        probe.dry_run(relative, repo_root=repo)
    with pytest.raises(ValueError, match="frozen fresh root"):
        probe.dry_run(Path("workspace") / "wrong", repo_root=repo)


def test_full_fake_batch_persists_post_bp_mapping_strata_and_disclosure(
        tmp_path: Path, monkeypatch) -> None:
    repo, relative = _test_repo(tmp_path, monkeypatch)
    graph_calls: list[int] = []
    candidate_calls: list[int] = []
    dense, graph_builder, preflight, candidate_builder = _fake_callbacks(
        graph_calls=graph_calls, candidate_calls=candidate_calls)

    original_sample = probe.source_runner.prior_runner.prior_runner.sample_error
    sampled: list[tuple[int, np.ndarray]] = []

    def sample_spy(seed, pmf, width):
        truth = np.asarray(original_sample(seed, pmf, width=width),
                           dtype=np.int64)
        sampled.append((int(seed), truth.copy()))
        return truth.copy()

    monkeypatch.setattr(probe.source_runner.prior_runner.prior_runner,
                        "sample_error", sample_spy)
    bp_calls: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
    raw_outputs: list[np.ndarray] = []

    def fake_decode(h, prior, syndrome):
        assert np.asarray(h).shape == (probe.M, probe.N)
        assert np.asarray(prior).shape == (probe.N, 32)
        assert np.asarray(syndrome).shape == (probe.M,)
        call = len(bp_calls)
        bp_calls.append((np.asarray(h).copy(), np.asarray(prior).copy(),
                         np.asarray(syndrome).copy()))
        raw_hard = np.zeros(probe.N, dtype=np.int64)
        if call % 2 == 0:
            raw_hard[:probe.M] = np.asarray(syndrome, dtype=np.int64)
        raw_outputs.append(raw_hard.copy())
        return SimpleNamespace(
            x_hat=raw_hard,
            syndrome_ok=layout.syndrome_ok(h, raw_hard, syndrome),
            iterations=1,
            status="fake-bp",
            final_beliefs=np.zeros((probe.N, 32), dtype=np.float64),
        )

    clock = _Clock()
    monkeypatch.setattr(probe, "_bind_production_decoder",
                        lambda: pytest.fail("production decoder was bound"))
    monkeypatch.setattr(probe.search_runner, "build_profile_graph",
                        lambda *args, **kwargs: pytest.fail("production graph built"))
    monkeypatch.setattr(probe.search_runner, "_candidate_pair_for_graph",
                        lambda *args, **kwargs: pytest.fail("production candidate built"))

    result = probe.execute_batch(
        out_root=relative, decode_fn=fake_decode, graph_builder=graph_builder,
        candidate_builder=candidate_builder, preflight_fn=preflight,
        repo_root=repo, now=clock, rss_fn=lambda: 100)

    root = repo / relative
    assert {path.name for path in root.iterdir()} == set(probe.ARTIFACTS)
    assert result["status"] == "REACHABILITY_DIAGNOSTIC_COMPLETE"
    assert result["attempted_decoder_calls"] == probe.MAX_CALLS == len(bp_calls)
    assert result["completed_diagnostic_rows"] == probe.MAX_CALLS
    assert result["disclosure_bits_actual"] == 49_920
    assert result["disclosure_bits_complete_contract"] == 49_920
    assert result["tag_bits"] == 0
    assert result["verification"] == "NOT_IMPLEMENTED"
    assert result["undetected"] == "NOT_MEASURED"
    assert graph_calls == candidate_calls == list(probe.GRAPH_SEEDS)
    assert len(sampled) == len(bp_calls) == len(raw_outputs) == probe.MAX_CALLS
    assert len({seed for seed, _ in sampled}) == probe.MAX_CALLS
    assert "sampled" not in fake_decode.__code__.co_freevars
    expected_prior = np.tile(probe._shape_record()["pmf"], (probe.N, 1))
    assert all(np.array_equal(call[1], expected_prior) for call in bp_calls)

    rows = _load_csv(root)
    plan = probe._seed_plan()
    assert len(rows) == probe.MAX_CALLS
    assert [int(row["call_index"]) for row in rows] == list(
        range(1, probe.MAX_CALLS + 1))
    assert [(int(row["graph_seed"]), int(row["stream"]),
             int(row["frame"]), int(row["seed"])) for row in rows] == plan
    assert all(row["status"] == "COMPLETE" for row in rows)
    assert {row["raw_stratum"] for row in rows} <= {
        "raw_exact", "raw_syndrome_valid_wrong", "raw_syndrome_fail"}
    assert all(int(row["diagnostic_array_index"]) == i
               for i, row in enumerate(rows))

    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    aggregates = summary[
        "counts_and_distance_histograms_by_stratum_graph_and_total"]
    assert summary["primary_denominator_raw_syndrome_fail"] == sum(
        row["raw_stratum"] == "raw_syndrome_fail" for row in rows)
    assert set(aggregates) == {"total", *(
        "graph_seed=%d" % seed for seed in probe.GRAPH_SEEDS)}
    for group in aggregates.values():
        for stratum in ("raw_exact", "raw_syndrome_valid_wrong",
                        "raw_syndrome_fail"):
            record = group[stratum]
            assert record["D0"] + record["D1"] + record["D_ge_2"] == record[
                "denominator"]
            assert set(record["distance_histogram"]) == {
                str(value) for value in range(probe.N - probe.M + 1)}
            assert sum(record["distance_histogram"].values()) == record[
                "denominator"]

    with np.load(root / "diagnostics.npz", allow_pickle=False) as arrays:
        assert set(arrays.files) == {
            "graph_seed", "H", "truth", "raw_hard", "syndrome",
            "final_beliefs", "frame_call_index", "frame_graph_index",
            "frame_graph_seed", "frame_stream", "frame_index", "frame_seed",
        }
        assert arrays["H"].shape == (len(probe.GRAPH_SEEDS), probe.M, probe.N)
        assert arrays["truth"].shape == arrays["raw_hard"].shape == (
            probe.MAX_CALLS, probe.N)
        assert arrays["syndrome"].shape == (probe.MAX_CALLS, probe.M)
        assert arrays["final_beliefs"].shape == (probe.MAX_CALLS, probe.N, 32)
        assert arrays["frame_call_index"].tolist() == list(
            range(1, probe.MAX_CALLS + 1))
        assert arrays["frame_graph_seed"].tolist() == [r[0] for r in plan]
        assert arrays["frame_stream"].tolist() == [r[1] for r in plan]
        assert arrays["frame_index"].tolist() == [r[2] for r in plan]
        assert arrays["frame_seed"].tolist() == [r[3] for r in plan]
        assert arrays["frame_graph_index"].tolist() == [
            list(probe.GRAPH_SEEDS).index(r[0]) for r in plan]
        assert arrays["graph_seed"].tolist() == list(probe.GRAPH_SEEDS)
        for index, ((seed, truth), row, raw_hard) in enumerate(
                zip(sampled, rows, raw_outputs)):
            assert seed == int(row["seed"])
            assert np.array_equal(arrays["truth"][index], truth)
            assert np.array_equal(arrays["raw_hard"][index], raw_hard)
            assert arrays["syndrome"][index].tolist() == layout.gf32_syndrome(
                dense, truth)
            assert len(bp_calls[index]) == 3  # H, prior, syndrome; no truth arg.
            symbols_equal = np.array_equal(raw_hard, truth)
            syndrome_ok = layout.syndrome_ok(dense, raw_hard,
                                              arrays["syndrome"][index])
            assert row["raw_symbols_equal"] == str(symbols_equal)
            assert row["raw_syndrome_ok"] == str(syndrome_ok)
            assert row["raw_exact"] == str(symbols_equal and syndrome_ok)
            assert int(row["D_free"]) == int(np.count_nonzero(
                raw_hard[probe.M:] != truth[probe.M:]))


def test_partial_exception_keeps_raw_row_but_nulls_aggregates_and_maps(
        tmp_path: Path, monkeypatch) -> None:
    repo, relative = _test_repo(tmp_path, monkeypatch)
    _, graph_builder, preflight, candidate_builder = _fake_callbacks()
    clock = _Clock()
    calls = 0

    def fake_decode(h, prior, syndrome):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise RuntimeError("fake decode stop")
        raw_hard = np.zeros(probe.N, dtype=np.int64)
        raw_hard[:probe.M] = syndrome
        return SimpleNamespace(
            x_hat=raw_hard,
            syndrome_ok=layout.syndrome_ok(h, raw_hard, syndrome),
            iterations=0, status="fake-bp",
            final_beliefs=np.zeros((probe.N, 32), dtype=np.float64))

    result = probe.execute_batch(
        out_root=relative, decode_fn=fake_decode, graph_builder=graph_builder,
        candidate_builder=candidate_builder, preflight_fn=preflight,
        repo_root=repo, now=clock, rss_fn=lambda: 100)
    rows = _load_csv(repo / relative)
    assert calls == 3
    assert len(rows) == 3
    assert rows[-1]["status"] == "BP_EXCEPTION_STOP"
    assert rows[-1]["failure_reason"] == "RuntimeError:fake decode stop"
    assert rows[-1]["diagnostic_array_index"] == ""
    assert result["status"] == "BP_EXCEPTION_STOP"
    assert result["attempted_decoder_calls"] == 3
    assert result["completed_diagnostic_rows"] == 2
    assert result["disclosure_bits_actual"] == 780
    assert result["disclosure_bits_complete_contract"] is None
    assert result["primary_denominator_raw_syndrome_fail"] is None
    assert result[
        "counts_and_distance_histograms_by_stratum_graph_and_total"] is None
    with np.load(repo / relative / "diagnostics.npz", allow_pickle=False) as arrays:
        assert arrays["truth"].shape == (2, probe.N)
        assert arrays["final_beliefs"].shape == (2, probe.N, 32)
        assert arrays["frame_call_index"].tolist() == [1, 2]


def test_resource_cap_after_decoder_exception_stops_and_retains_failure(
        tmp_path: Path, monkeypatch) -> None:
    repo, relative = _test_repo(tmp_path, monkeypatch)
    _, graph_builder, preflight, candidate_builder = _fake_callbacks()
    clock = _Clock()
    calls = 0

    def slow_exception(h, prior, syndrome):
        nonlocal calls
        calls += 1
        clock.value += probe.CALL_CAP_S + 1
        raise RuntimeError("over-cap fake failure")

    result = probe.execute_batch(
        out_root=relative, decode_fn=slow_exception, graph_builder=graph_builder,
        candidate_builder=candidate_builder, preflight_fn=preflight,
        repo_root=repo, now=clock, rss_fn=lambda: 100)
    row = _load_csv(repo / relative)[0]
    assert calls == 1
    assert row["status"] == "BP_EXCEPTION_STOP"
    assert row["failure_reason"] == "RuntimeError:over-cap fake failure"
    assert float(row["arm_wall_s"]) == probe.CALL_CAP_S + 1
    assert result["status"] == "RESOURCE_STOP"
    assert "decoder_diagnostic_call_wall_cap" in result["stop_reason"]
    assert result["attempted_decoder_calls"] == 1


def test_rss_cap_after_decoder_stops_before_diagnostic(
        tmp_path: Path, monkeypatch) -> None:
    repo, relative = _test_repo(tmp_path, monkeypatch)
    _, graph_builder, preflight, candidate_builder = _fake_callbacks()
    current_rss = 0
    calls = 0

    def fake_decode(h, prior, syndrome):
        nonlocal current_rss, calls
        calls += 1
        current_rss = probe.RSS_CAP_BYTES
        raw_hard = np.zeros(probe.N, dtype=np.int64)
        raw_hard[:probe.M] = syndrome
        return SimpleNamespace(
            x_hat=raw_hard,
            syndrome_ok=layout.syndrome_ok(h, raw_hard, syndrome),
            iterations=1, status="fake-bp",
            final_beliefs=np.zeros((probe.N, 32), dtype=np.float64))

    result = probe.execute_batch(
        out_root=relative, decode_fn=fake_decode, graph_builder=graph_builder,
        candidate_builder=candidate_builder, preflight_fn=preflight,
        repo_root=repo, now=_Clock(), rss_fn=lambda: current_rss)
    row = _load_csv(repo / relative)[0]
    assert calls == result["attempted_decoder_calls"] == 1
    assert result["status"] == row["status"] == "RESOURCE_STOP"
    assert "rss_cap" in result["stop_reason"]
    assert row["diagnostic_array_index"] == ""
    assert result["completed_diagnostic_rows"] == 0


def test_post_diagnostic_and_npz_write_wall_caps_are_retained(
        tmp_path: Path, monkeypatch) -> None:
    repo, relative = _test_repo(tmp_path, monkeypatch)
    _, graph_builder, preflight, candidate_builder = _fake_callbacks()
    clock = _Clock()

    def fake_decode(h, prior, syndrome):
        raw_hard = np.zeros(probe.N, dtype=np.int64)
        raw_hard[:probe.M] = syndrome
        return SimpleNamespace(
            x_hat=raw_hard,
            syndrome_ok=layout.syndrome_ok(h, raw_hard, syndrome),
            iterations=1, status="fake-bp",
            final_beliefs=np.zeros((probe.N, 32), dtype=np.float64))

    original_diagnostic = probe._mrb_reachability_diagnostic

    def late_diagnostic(**kwargs):
        diagnostic = original_diagnostic(**kwargs)
        clock.value += probe.CALL_CAP_S + 1
        return diagnostic

    monkeypatch.setattr(probe, "_mrb_reachability_diagnostic", late_diagnostic)
    result = probe.execute_batch(
        out_root=relative, decode_fn=fake_decode, graph_builder=graph_builder,
        candidate_builder=candidate_builder, preflight_fn=preflight,
        repo_root=repo, now=clock, rss_fn=lambda: 100)
    row = _load_csv(repo / relative)[0]
    assert result["status"] == "RESOURCE_STOP"
    assert "decoder_diagnostic_call_wall_cap" in result["stop_reason"]
    assert row["status"] == "RESOURCE_STOP"
    assert row["diagnostic_array_index"] == "0"
    assert result["completed_diagnostic_rows"] == 1

    # A fresh root isolates the resource check after NPZ writing.
    repo2, relative2 = _test_repo(tmp_path, monkeypatch, "reachability-write-cap")
    clock2 = _Clock()
    calls = 0

    def full_fake_decode(h, prior, syndrome):
        nonlocal calls
        calls += 1
        raw_hard = np.zeros(probe.N, dtype=np.int64)
        raw_hard[:probe.M] = syndrome
        return SimpleNamespace(
            x_hat=raw_hard,
            syndrome_ok=layout.syndrome_ok(h, raw_hard, syndrome),
            iterations=1, status="fake-bp",
            final_beliefs=np.zeros((probe.N, 32), dtype=np.float64))

    original_write = probe._write_diagnostics_npz

    def late_npz_write(root, arrays):
        size = original_write(root, arrays)
        clock2.value = probe.WALL_CAP_S + 1
        return size

    monkeypatch.setattr(probe, "_write_diagnostics_npz", late_npz_write)
    result2 = probe.execute_batch(
        out_root=relative2, decode_fn=full_fake_decode,
        graph_builder=graph_builder, candidate_builder=candidate_builder,
        preflight_fn=preflight, repo_root=repo2, now=clock2, rss_fn=lambda: 100)
    assert calls == probe.MAX_CALLS
    assert result2["status"] == "RESOURCE_STOP"
    assert result2["stop_reason"] == "total_wall_cap"
    assert result2["resource_measurement"][
        "batch_wall_s_before_terminal_summary_manifest_log"] == probe.WALL_CAP_S + 1

    # A prior BP failure remains the primary stop while later artifact cost is
    # still recorded as a resource violation.
    repo3, relative3 = _test_repo(tmp_path, monkeypatch,
                                  "reachability-failure-write-cap")
    clock3 = _Clock()
    failure_calls = 0

    def early_bp_failure(h, prior, syndrome):
        nonlocal failure_calls
        failure_calls += 1
        raise RuntimeError("bp failed before terminal write")

    def late_npz_after_failure(root, arrays):
        size = original_write(root, arrays)
        clock3.value = probe.WALL_CAP_S + 1
        return size

    monkeypatch.setattr(probe, "_write_diagnostics_npz",
                        late_npz_after_failure)
    result3 = probe.execute_batch(
        out_root=relative3, decode_fn=early_bp_failure,
        graph_builder=graph_builder, candidate_builder=candidate_builder,
        preflight_fn=preflight, repo_root=repo3, now=clock3, rss_fn=lambda: 100)
    row3 = _load_csv(repo3 / relative3)[0]
    assert failure_calls == 1
    assert row3["failure_reason"] == "RuntimeError:bp failed before terminal write"
    assert result3["status"] == "BP_EXCEPTION_STOP"
    assert result3["stop_reason"] == row3["failure_reason"]
    resource = result3["resource_measurement"]
    assert "total_wall_cap" in resource["resource_stop_reasons"]
    assert resource["resource_violation_count"] > 0
