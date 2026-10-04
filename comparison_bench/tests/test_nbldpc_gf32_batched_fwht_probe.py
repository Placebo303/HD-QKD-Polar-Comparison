"""Focused mathematical and fake-only tests for the batched GF(32) probe."""
from __future__ import annotations

import inspect
import csv
from types import SimpleNamespace
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_batched_fwht_probe as probe
from comparison_bench.formal_ir import (
    nbldpc_gf32_batched_check as batched_check,
    v35_algorithm_development as v35,
)
from comparison_bench.formal_ir.nonbinary_field import GF2mField
from test_nbldpc_gf32_kernel_hotspots import _fake_parent


def _messages(degree: int, kind: str, q: int = 32) -> list[np.ndarray]:
    if kind == "uniform":
        return [np.zeros(q, dtype=np.float64) for _ in range(degree)]
    result = []
    for edge in range(degree):
        values = np.full(q, -700.0 if kind == "extreme" else -80.0,
                         dtype=np.float64)
        values[(edge * 7 + 3) % q] = 0.0
        if kind == "extreme":
            values[(edge * 11 + 5) % q] = -350.0
        result.append(values)
    return result


@pytest.mark.parametrize("degree", [4, 5])
@pytest.mark.parametrize("kind", ["uniform", "peaked", "extreme"])
def test_batched_helper_matches_reference_and_returns_normalized_finite_logs(
        degree: int, kind: str):
    field = GF2mField.create(32)
    tables = v35._get_gf32_tables(field)
    messages = _messages(degree, kind)
    coefficients = [1, 3, 7, 11, 19][:degree]
    syndrome = 23

    expected = v35._check_update_log_batch(
        messages, coefficients, syndrome, field, tables)
    actual = batched_check.batched_check_update_log_batch(
        messages, coefficients, syndrome, field, tables)

    assert len(actual) == degree
    for got, want in zip(actual, expected):
        assert got.shape == (32,)
        assert np.all(np.isfinite(got))
        np.testing.assert_allclose(got, want, atol=1e-12, rtol=0.0)
        np.testing.assert_allclose(np.exp(got).sum(), 1.0, atol=1e-12,
                                   rtol=0.0)


def test_batched_helper_preserves_degree_error_and_nonfinite_input_fallback():
    field = GF2mField.create(32)
    tables = v35._get_gf32_tables(field)
    one = [np.zeros(32, dtype=np.float64)]
    with pytest.raises(ValueError, match="degree >= 2"):
        v35._check_update_log_batch(one, [1], 7, field, tables)
    with pytest.raises(ValueError, match="degree >= 2"):
        batched_check.batched_check_update_log_batch(one, [1], 7, field, tables)

    messages = [np.full(32, np.nan), np.zeros(32), np.linspace(-4.0, 0.0, 32)]
    coefficients = [1, 5, 9]
    expected = v35._check_update_log_batch(
        messages, coefficients, 17, field, tables)
    actual = batched_check.batched_check_update_log_batch(
        messages, coefficients, 17, field, tables)
    for got, want in zip(actual, expected):
        assert np.all(np.isfinite(got))
        np.testing.assert_allclose(got, want, atol=1e-12, rtol=0.0)


def test_batched_helper_uses_two_fwht_calls_for_outgoing_batch(
        monkeypatch: pytest.MonkeyPatch):
    field = GF2mField.create(32)
    tables = v35._get_gf32_tables(field)
    original = batched_check.fwht_batched
    seen_shapes: list[tuple[int, ...]] = []

    def counted(values):
        seen_shapes.append(np.asarray(values).shape)
        return original(values)

    monkeypatch.setattr(batched_check, "fwht_batched", counted)
    batched_check.batched_check_update_log_batch(
        _messages(4, "peaked"), [1, 3, 7, 11], 29, field, tables)
    assert seen_shapes == [(4, 32), (4, 32)]

    old_shapes: list[tuple[int, ...]] = []
    old_original = v35.fwht_batched

    def old_counted(values):
        old_shapes.append(np.asarray(values).shape)
        return old_original(values)

    monkeypatch.setattr(v35, "fwht_batched", old_counted)
    v35._check_update_log_batch(
        _messages(4, "peaked"), [1, 3, 7, 11], 29, field, tables)
    assert old_shapes == [(4, 32), (32,), (32,), (32,), (32,)]


def test_decoder_keeps_old_default_and_accepts_keyword_only_injection(
        monkeypatch: pytest.MonkeyPatch):
    signature = inspect.signature(v35.decode_row_layered_fftqspa)
    assert signature.parameters["check_update_fn"].default is None
    assert signature.parameters["check_update_fn"].kind is inspect.Parameter.KEYWORD_ONLY

    field = GF2mField.create(32)
    h = np.asarray([[1, 3]], dtype=np.uint8)
    prior = np.full((2, 32), 1.0 / 32.0, dtype=np.float64)
    prior[0] = 0.0
    prior[0, 2] = 1.0
    prior[1] = 0.0
    prior[1, 7] = 1.0
    syndrome = np.asarray([0], dtype=np.uint8)
    old_calls = 0
    batched_calls = 0
    old_impl = v35._check_update_log_batch
    batched_impl = batched_check.batched_check_update_log_batch

    def old_spy(*args, **kwargs):
        nonlocal old_calls
        old_calls += 1
        return old_impl(*args, **kwargs)

    def batched_spy(*args, **kwargs):
        nonlocal batched_calls
        batched_calls += 1
        return batched_impl(*args, **kwargs)

    # The default route dispatches through the original implementation.
    monkeypatch.setattr(v35, "_check_update_log_batch", old_spy)
    default = v35.decode_row_layered_fftqspa(
        h, prior, syndrome, max_iter=1, field=field)
    assert old_calls > 0
    assert batched_calls == 0

    # The opt-in route dispatches through the injected batched helper and keeps
    # the same decoder outputs within the frozen numerical tolerance.
    injected = v35.decode_row_layered_fftqspa(
        h, prior, syndrome, max_iter=1, field=field,
        check_update_fn=batched_spy)
    assert batched_calls > 0
    np.testing.assert_array_equal(injected.x_hat, default.x_hat)
    assert injected.iterations == default.iterations
    assert injected.status == default.status
    assert injected.syndrome_ok == default.syndrome_ok
    np.testing.assert_allclose(injected.final_beliefs, default.final_beliefs,
                               atol=1e-12, rtol=0.0)


def _fake_adapters(*, candidate_belief_mismatch: bool = False,
                   source_vector_mismatch: bool = False,
                   wall_over_cap: bool = False,
                   rss_over_cap: bool = False):
    source, cases = _fake_parent()
    state = {"source_reads": 0, "calls": [],
             "path_calls": {"reference": 0, "candidate": 0},
             "clock_calls": 0, "rss_calls": 0}

    def source_reader():
        state["source_reads"] += 1
        return source

    def make_decoder(path: str):
        def decoder(h_matrix=None, priors=None, syndromes=None, *args,
                    max_iter=90, damping_alpha=1.0, warm_beliefs=None,
                    field=None, **kwargs):
            if h_matrix is None:
                h_matrix, priors, syndromes = args[:3]
            call_no = state["path_calls"][path]
            state["path_calls"][path] += 1
            case_index = call_no % len(cases)
            case = cases[case_index]
            assert max_iter == 90
            assert damping_alpha == 1.0
            assert warm_beliefs is None
            assert field is None
            np.testing.assert_array_equal(h_matrix, case["H"])
            np.testing.assert_array_equal(syndromes, case["syndrome"])
            wanted_prior = case["prior"].copy()
            if case["role"] == "selected_rescue":
                wanted_prior[case["selected_variable"], :] = 0.0
                wanted_prior[case["selected_variable"], case["guess_symbol"]] = 1.0
            np.testing.assert_array_equal(priors, wanted_prior)
            state["calls"].append((path, case_index))

            x_hat = case["x_hat"].copy()
            beliefs = case["beliefs"].copy()
            if source_vector_mismatch and not state.get("did_source_vector_mismatch"):
                x_hat[0] = (int(x_hat[0]) + 1) % 32
                state["did_source_vector_mismatch"] = True
            if (candidate_belief_mismatch and path == "candidate"
                    and case_index == 0):
                beliefs[0, 0] += 1e-4
            return SimpleNamespace(
                x_hat=x_hat,
                iterations=case["iterations"],
                status=case["decoder_status"],
                syndrome_ok=case["syndrome_valid"],
                final_beliefs=beliefs,
                runtime_s=0.001,
            )
        return decoder

    def now():
        state["clock_calls"] += 1
        if wall_over_cap and state["clock_calls"] >= 7:
            return 121.0
        return 0.001 * state["clock_calls"]

    def rss_fn():
        state["rss_calls"] += 1
        if rss_over_cap and state["rss_calls"] >= 2:
            return probe.RSS_CAP_BYTES + 1
        return 1_000_000

    return {
        "source": source,
        "cases": cases,
        "state": state,
        "source_reader": source_reader,
        "reference_decoder": make_decoder("reference"),
        "candidate_decoder": make_decoder("candidate"),
        "now": now,
        "rss_fn": rss_fn,
    }


def _execute_fake(adapters: dict, root: Path):
    return probe.execute_batch(
        source_reader=adapters["source_reader"],
        reference_decoder=adapters["reference_decoder"],
        candidate_decoder=adapters["candidate_decoder"],
        out_root=probe.OUT_ROOT_RELATIVE,
        repo_root=root,
        now=adapters["now"],
        rss_fn=adapters["rss_fn"],
        command="explicit fake-only batched FWHT test",
    )


def _assert_null_paired_totals(summary: dict) -> None:
    for key in ("rounds", "paired_totals", "exact_counts", "valid_wrong_counts",
                "paired_wall_ratio_candidate_over_reference"):
        assert summary[key] is None, key


def test_t0_and_dry_run_are_source_free_and_keep_root_absent(tmp_path: Path):
    t0 = probe.verify_t0(out_root=probe.OUT_ROOT_RELATIVE, repo_root=tmp_path)
    dry = probe.dry_run(out_root=probe.OUT_ROOT_RELATIVE, repo_root=tmp_path)
    for result in (t0, dry):
        assert result["source_reads"] == result["decoder_calls"] == 0
        assert result.get("sampler_calls", 0) == 0
        assert result["writes"] == 0
    assert not (tmp_path / probe.OUT_ROOT_RELATIVE).exists()


def test_full_fake_18_cases_run_both_orders_and_record_all_72_calls(
        tmp_path: Path):
    adapters = _fake_adapters()
    result = _execute_fake(adapters, tmp_path)

    assert result["status"] == "BATCHED_FWHT_FIXED_CASES_MATCH"
    assert result["source_reads"] == adapters["state"]["source_reads"] == 1
    assert result["decoder_calls"] == 72
    assert adapters["state"]["path_calls"] == {"reference": 36, "candidate": 36}
    expected = []
    for case_index in range(18):
        expected.extend((("reference", case_index), ("candidate", case_index)))
    for case_index in range(18):
        expected.extend((("candidate", case_index), ("reference", case_index)))
    assert adapters["state"]["calls"] == expected

    rows = result["call_records"]
    assert len(rows) == 72
    assert [int(row["round"]) for row in rows] == (
        [1] * 36 + [2] * 36)
    assert [row["path"] for row in rows] == [path for path, _ in expected]
    assert [int(row["order_position"]) for row in rows] == (
        [position for _ in range(18) for position in (1, 2)] * 2)
    for row in rows:
        assert row["source_replay_match"] is True
        assert row["own_syndrome_valid"] in (True, False)
        assert row["iterations"] is not None
        assert row["wall_s"] is not None
    for round_info in result["summary"]["rounds"].values():
        assert round_info["calls"] == 36
        assert round_info["paths"]["reference"]["calls"] == 18
        assert round_info["paths"]["candidate"]["calls"] == 18
    assert result["summary"]["paired_totals"]["reference"]["calls"] == 36
    assert result["summary"]["paired_totals"]["candidate"]["calls"] == 36
    assert result["summary"]["source_reads"] == 1
    assert result["summary"]["sampler_calls"] == 0
    assert result["summary"]["search_calls"] == 0
    assert result["summary"]["graph_build_calls"] == 0
    assert result["summary"]["source_load_and_case_setup_wall_s"] is not None
    for row in rows:
        assert row["source_status_match"] is True
        assert row["source_report_match"] is True
        assert row["source_syndrome_label_match"] is True
        assert row["paired_vector_match"] is True
        assert row["paired_iterations_match"] is True
        assert row["paired_status_match"] is True
        assert row["paired_report_match"] is True
        assert row["paired_beliefs_match"] is True
        assert row["paired_beliefs_max_abs_diff"] == 0.0
        assert row["runtime_s"] == pytest.approx(0.001)
        assert row["wall_s"] is not None
        if row["selection_role"] == "baseline_failed":
            assert row["source_beliefs_match"] is True
            assert row["source_beliefs_max_abs_diff"] <= 1e-12
    assert sum(bool(row["is_first_decoder_call"]) for row in rows) == 1
    assert sum(bool(row["is_first_for_path"]) for row in rows) == 2
    for round_key in ("1", "2"):
        assert result["summary"]["exact_counts"][round_key] == {
            "reference": 6, "candidate": 6}
        assert result["summary"]["valid_wrong_counts"][round_key] == {
            "reference": 6, "candidate": 6}
    for round_info in result["summary"]["rounds"].values():
        for role in ("baseline_valid", "baseline_failed", "selected_rescue"):
            assert round_info["groups"][role]["reference"]["calls"] == 6
            assert round_info["groups"][role]["candidate"]["calls"] == 6
        assert round_info["paths"]["reference"]["wall_s"] > 0.0
        assert round_info["paths"]["candidate"]["wall_s"] > 0.0
    assert set(result["artifacts"]) == {
        "manifest.json", "summary.json", "call_records.csv", "EXPLORATION_LOG.md"}
    with Path(result["artifacts"]["call_records.csv"]).open(
            newline="", encoding="utf-8") as stream:
        saved_rows = list(csv.DictReader(stream))
    assert len(saved_rows) == 72
    assert saved_rows[0]["path"] == "reference"
    assert saved_rows[1]["path"] == "candidate"


def test_existing_output_root_refuses_before_source_or_decoder(tmp_path: Path):
    adapters = _fake_adapters()
    (tmp_path / probe.OUT_ROOT_RELATIVE).mkdir(parents=True)
    with pytest.raises(FileExistsError):
        _execute_fake(adapters, tmp_path)
    assert adapters["state"]["source_reads"] == 0
    assert adapters["state"]["calls"] == []


@pytest.mark.parametrize("mutation", ["source_identity", "missing_stratum", "bad_vector_pointer"])
def test_source_identity_selection_or_pointer_failure_stops_before_decoder(
        tmp_path: Path, mutation: str):
    adapters = _fake_adapters()
    diagnostics = adapters["source"]["diagnostics"]
    if mutation == "source_identity":
        adapters["source"]["manifest"]["source_identity"]["batch_uuid"] = "wrong-source"
    elif mutation == "missing_stratum":
        row = int(np.flatnonzero(diagnostics["call_role"] == "baseline")[0])
        # The first graph's first saved valid baseline no longer qualifies.
        diagnostics["call_syndrome_valid"][row] = False
    else:
        diagnostics["call_raw_vector_index"][0] = len(diagnostics["raw_vector_call_index"])

    result = _execute_fake(adapters, tmp_path)
    assert result["status"] == "STOP"
    assert result["source_reads"] == adapters["state"]["source_reads"] == 1
    assert result["decoder_calls"] == 0
    assert result["call_records"] == []
    assert result["summary"]["stop_reasons"]
    _assert_null_paired_totals(result["summary"])


@pytest.mark.parametrize("cap", ["wall", "rss"])
def test_resource_cap_retains_one_call_and_nulls_complete_paired_totals(
        tmp_path: Path, cap: str):
    adapters = _fake_adapters(wall_over_cap=(cap == "wall"),
                               rss_over_cap=(cap == "rss"))
    result = _execute_fake(adapters, tmp_path)
    assert result["status"] == "INCOMPLETE"
    assert result["decoder_calls"] == 1
    assert len(result["call_records"]) == 1
    assert result["summary"]["resource_events"]
    assert any(event["reason"] == f"{cap}_cap"
               for event in result["summary"]["resource_events"])
    _assert_null_paired_totals(result["summary"])


def test_source_roundtrip_mismatch_retains_actual_row_and_stops(
        tmp_path: Path):
    adapters = _fake_adapters(source_vector_mismatch=True)
    result = _execute_fake(adapters, tmp_path)
    assert result["status"] == "STOP"
    assert result["decoder_calls"] == 1
    assert len(result["call_records"]) == 1
    row = result["call_records"][0]
    assert row["source_vector_match"] is False
    assert row["source_replay_match"] is False
    assert row["failure_reason"]
    assert result["summary"]["stop_reasons"]
    _assert_null_paired_totals(result["summary"])


def test_paired_belief_mismatch_stops_after_both_real_fake_returns(
        tmp_path: Path):
    adapters = _fake_adapters(candidate_belief_mismatch=True)
    result = _execute_fake(adapters, tmp_path)
    assert result["status"] == "STOP"
    assert result["decoder_calls"] == 2
    assert len(result["call_records"]) == 2
    assert all(row["source_replay_match"] is True
               for row in result["call_records"])
    assert all(row["paired_beliefs_match"] is False
               for row in result["call_records"])
    assert all(row["paired_beliefs_max_abs_diff"] == pytest.approx(1e-4)
               for row in result["call_records"])
    _assert_null_paired_totals(result["summary"])


def test_invalid_decoder_injection_fails_before_source_or_root_creation(
        tmp_path: Path):
    adapters = _fake_adapters()
    with pytest.raises(ValueError, match="explicit source_reader"):
        probe.execute_batch(
            source_reader=adapters["source_reader"],
            reference_decoder=adapters["reference_decoder"],
            candidate_decoder=None,
            out_root=probe.OUT_ROOT_RELATIVE,
            repo_root=tmp_path,
            now=adapters["now"], rss_fn=adapters["rss_fn"],
        )
    assert adapters["state"]["source_reads"] == 0
    assert adapters["state"]["calls"] == []
    assert not (tmp_path / probe.OUT_ROOT_RELATIVE).exists()


def test_linux_rss_high_water_kib_is_converted_to_bytes(
        monkeypatch: pytest.MonkeyPatch):
    import resource

    monkeypatch.setattr(resource, "getrusage",
                        lambda who: SimpleNamespace(ru_maxrss=33072))
    assert probe.hotspots._rss_bytes() == 33_865_728

