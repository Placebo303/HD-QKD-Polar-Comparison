"""Focused fake-only tests for the frozen GF(32) kernel-hotspot replay."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli.probes_closed import nbldpc_gf32_kernel_hotspots as probe
from comparison_bench.formal_ir import v35_algorithm_development as v35


GRAPH_IDS = tuple(range(2026093901, 2026093907))
PARENT_UUID = "cbe151fe-25f7-4990-8895-858091467e2b"
PARENT_CONTRACT = "NBLDPC-GF32-SOFT-PRIOR-REPLICA-20261001/PREREG_AND_AUTH.md"
PARENT_NAMESPACE = "gf32-softprior-replica-v1"
SOURCE_UUID = "a9352bc1-ae56-443b-ae93-9dcfa85d4229"
SOURCE_CONTRACT = "NBLDPC-GF32-DEGREE-ADMITTED-20261001/PREREG_AND_AUTH.md"
SOURCE_NAMESPACE = "gf32-degree-admitted-v1"


def _fake_h() -> np.ndarray:
    """Small-support matrix embedded in the accepted 52 x 128 source shape."""
    h = np.zeros((52, 128), dtype=np.uint8)
    h[0, 0] = 1
    h[0, 1] = 1
    return h


def _fake_parent() -> tuple[dict, list[dict]]:
    """Build six mapped graphs and 18 selected source-call records, all fake."""
    graph_matrices = np.stack([_fake_h() for _ in GRAPH_IDS])
    prior_row = np.zeros(32, dtype=np.float64)
    prior_row[[0, 1, 3, 7, 15, 31]] = [0.55, 0.12, 0.10, 0.09, 0.08, 0.06]
    original_prior = np.tile(prior_row, (128, 1))

    pair_index: list[int] = []
    pair_graph_id: list[int] = []
    pair_syndrome: list[np.ndarray] = []
    pair_truth: list[np.ndarray] = []
    pair_baseline_call_index: list[int] = []
    pair_candidate_selected_call_index: list[int] = []
    pair_selected_variable: list[int] = []
    call_index: list[int] = []
    call_pair_index: list[int] = []
    call_graph_id: list[int] = []
    call_role: list[str] = []
    call_branch_index: list[int] = []
    call_guess_symbol: list[int] = []
    call_selected_variable: list[int] = []
    call_status: list[str] = []
    call_decoder_status: list[str] = []
    call_iterations: list[int] = []
    call_syndrome_valid: list[bool] = []
    call_syndrome_ok_reported: list[bool] = []
    call_syndrome_ok_reported_available: list[bool] = []
    call_raw_vector_index: list[int] = []
    saved_vectors: dict[int, np.ndarray] = {}
    belief_call_index: list[int] = []
    selector_call_index: list[int] = []

    for graph_pos, graph_id in enumerate(GRAPH_IDS):
        valid_pair = 2 * graph_pos
        failed_pair = valid_pair + 1
        valid_call, failed_call, restart_call = 1000 + 3 * graph_pos, 1001 + 3 * graph_pos, 1002 + 3 * graph_pos

        pair_index.extend((valid_pair, failed_pair))
        pair_graph_id.extend((graph_id, graph_id))
        syn_valid = np.zeros(52, dtype=np.uint8)
        syn_failed = np.zeros(52, dtype=np.uint8)
        syn_failed[0] = 1
        pair_syndrome.extend((syn_valid, syn_failed))
        # Truth is deliberately not used to select any of the 18 cases.  The
        # failed pair truth uses column 1; its selected restart uses column 0,
        # producing a syndrome-valid wrong vector through the fake nullspace.
        failed_truth = np.zeros(128, dtype=np.uint8)
        failed_truth[1] = 1
        pair_truth.extend((np.zeros(128, dtype=np.uint8), failed_truth))
        pair_baseline_call_index.extend((valid_call, failed_call))
        # Baseline-valid candidates are pass-through pointers to the baseline
        # row; failed baselines point to their selected soft-prior restart.
        pair_candidate_selected_call_index.extend((valid_call, restart_call))
        pair_selected_variable.extend((-1, 0))

        restart_vector = np.zeros(128, dtype=np.uint8)
        restart_vector[0] = 1
        vectors = {
            valid_call: np.zeros(128, dtype=np.uint8),
            failed_call: np.zeros(128, dtype=np.uint8),
            restart_call: restart_vector,
        }
        rows = (
            (valid_call, valid_pair, "baseline", -1, -1, -1,
             "saved-valid", 7, True, True, vectors[valid_call]),
            (failed_call, failed_pair, "baseline", -1, -1, 0,
             "saved-failed", 90, False, False, vectors[failed_call]),
            (restart_call, failed_pair, "soft_prior", 1, 1, 0,
             "saved-restart", 5, True, True, vectors[restart_call]),
        )
        for (source_call, pair_id, role, branch_i, guess, selected,
             decoder_status, iterations, valid, reported, vector) in rows:
            call_index.append(source_call)
            call_pair_index.append(pair_id)
            call_graph_id.append(graph_id)
            call_role.append(role)
            call_branch_index.append(branch_i)
            call_guess_symbol.append(guess)
            call_selected_variable.append(selected)
            # Intentionally distinguish wrapper status from decoder status.
            call_status.append("COMPLETE")
            call_decoder_status.append(decoder_status)
            call_iterations.append(iterations)
            call_syndrome_valid.append(valid)
            call_syndrome_ok_reported.append(reported)
            call_syndrome_ok_reported_available.append(True)
            call_raw_vector_index.append(-1)  # replaced after raw rows are shuffled
            saved_vectors[source_call] = vector
        belief_call_index.append(failed_call)
        selector_call_index.append(failed_call)

    # Physical vector storage is reversed; all references must be resolved by
    # raw_vector_call_index, rather than relying on matching array positions.
    raw_vector_call_index = np.asarray(call_index[::-1], dtype=np.int64)
    raw_x_hat = np.stack([saved_vectors[i] for i in raw_vector_call_index])
    raw_pos = {int(call_id): pos for pos, call_id in enumerate(raw_vector_call_index)}
    call_raw_vector_index = [raw_pos[call_id] for call_id in call_index]

    diagnostics = {
        "source_batch_uuid": np.asarray([SOURCE_UUID]),
        "source_contract": np.asarray([SOURCE_CONTRACT]),
        "source_seed_namespace": np.asarray([SOURCE_NAMESPACE]),
        "source_graph_input_kind": np.asarray(["admitted_source"]),
        "source_graph_id": np.asarray(GRAPH_IDS, dtype=np.int64),
        "source_graph_seed": np.asarray([101, 102, 103, 104, 105, 106], dtype=np.int64),
        "source_profile_index": np.ones(6, dtype=np.int64),
        "source_graph_index": np.arange(6, dtype=np.int64),
        "source_constructor_uuid": np.asarray(["a9a18abe-3547-4d16-aa50-1f7150182f31"] * 6),
        "source_constructor_path": np.asarray(["workspace/gf32_construct_a9a18abe/constructions.json"] * 6),
        "source_constructor_matrix_index": np.asarray([0, 2, 4, 6, 9, 11], dtype=np.int64),
        "source_constructor_attempt_j": np.asarray([0, 0, 0, 0, 1, 0], dtype=np.int64),
        "source_constructor_seed": np.asarray([2026093901, 2026093902, 2026093903,
                                                2026093904, 2560859716, 2026093906],
                                               dtype=np.int64),
        "source_constructor_graph_id": np.asarray(GRAPH_IDS, dtype=np.int64),
        "H_deep": graph_matrices,
        "original_prior": original_prior,
        "pair_index": np.asarray(pair_index, dtype=np.int64),
        "pair_graph_id": np.asarray(pair_graph_id, dtype=np.int64),
        "pair_syndrome": np.stack(pair_syndrome),
        "pair_truth": np.stack(pair_truth),
        "pair_baseline_call_index": np.asarray(pair_baseline_call_index, dtype=np.int64),
        "pair_candidate_selected_call_index": np.asarray(pair_candidate_selected_call_index, dtype=np.int64),
        "pair_selected_variable": np.asarray(pair_selected_variable, dtype=np.int64),
        "call_index": np.asarray(call_index, dtype=np.int64),
        "call_pair_index": np.asarray(call_pair_index, dtype=np.int64),
        "call_graph_id": np.asarray(call_graph_id, dtype=np.int64),
        "call_role": np.asarray(call_role),
        "call_branch_index": np.asarray(call_branch_index, dtype=np.int64),
        "call_guess_symbol": np.asarray(call_guess_symbol, dtype=np.int64),
        "call_selected_variable": np.asarray(call_selected_variable, dtype=np.int64),
        "call_status": np.asarray(call_status),
        "call_decoder_status": np.asarray(call_decoder_status),
        "call_iterations": np.asarray(call_iterations, dtype=np.int64),
        "call_syndrome_valid": np.asarray(call_syndrome_valid, dtype=np.bool_),
        "call_syndrome_ok_reported": np.asarray(call_syndrome_ok_reported, dtype=np.bool_),
        "call_syndrome_ok_reported_available": np.asarray(call_syndrome_ok_reported_available, dtype=np.bool_),
        "call_raw_vector_index": np.asarray(call_raw_vector_index, dtype=np.int64),
        "raw_vector_call_index": raw_vector_call_index,
        "raw_x_hat": raw_x_hat,
        "belief_call_index": np.asarray(belief_call_index, dtype=np.int64),
        "baseline_failure_belief_provenance": np.asarray(["CHECK_UPDATED"] * 6),
        "baseline_failure_beliefs": np.zeros((6, 128, 32), dtype=np.float64),
        "selector_call_index": np.asarray(selector_call_index, dtype=np.int64),
        "selector_selected_column": np.zeros(6, dtype=np.int64),
    }
    parent_identity = {
        "batch_uuid": PARENT_UUID,
        "contract": PARENT_CONTRACT,
        "seed_namespace": PARENT_NAMESPACE,
        "status": "COMPLETE",
        "classification": "MECHANISM_SIGNAL",
    }
    manifest = {
        **parent_identity,
        "source_identity": {
            "batch_uuid": SOURCE_UUID,
            "contract": SOURCE_CONTRACT,
            "seed_namespace": SOURCE_NAMESPACE,
            "graph_input_kind": "admitted_source",
        },
    }
    summary = dict(parent_identity)
    return {"manifest": manifest, "summary": summary, "diagnostics": diagnostics}, [
        {
            "source_call_index": call_index[pos],
            "pair_index": call_pair_index[pos],
            "graph_id": call_graph_id[pos],
            "role": "baseline_valid" if pos % 3 == 0 else
                    "baseline_failed" if pos % 3 == 1 else "selected_rescue",
            "H": graph_matrices[GRAPH_IDS.index(call_graph_id[pos])].copy(),
            "prior": original_prior.copy(),
            "syndrome": pair_syndrome[pair_index.index(call_pair_index[pos])].copy(),
            "x_hat": saved_vectors[call_index[pos]].copy(),
            "iterations": call_iterations[pos],
            "decoder_status": call_decoder_status[pos],
            "beliefs": np.zeros((128, 32), dtype=np.float64),
            "syndrome_valid": call_syndrome_valid[pos],
            "selected_variable": call_selected_variable[pos],
            "guess_symbol": call_guess_symbol[pos],
            "raw_vector_index": call_raw_vector_index[pos],
        }
        for pos in range(len(call_index))
    ]


def _adapters(source: dict, cases: list[dict], *,
              source_mismatch: bool = False,
              clock_overshoot_call: int | None = None,
              rss_over_call: int | None = None,
              mismatch_vector_call: int | None = None) -> dict:
    state = {"source_reads": 0, "decoder_calls": 0, "clock": 0.0,
             "decoder_inputs": []}
    if source_mismatch:
        source["manifest"]["source_identity"]["batch_uuid"] = "wrong-source"

    def source_reader():
        state["source_reads"] += 1
        return source

    def decoder(h, prior, syndrome, *, max_iter, damping_alpha,
                warm_beliefs, field):
        call_no = state["decoder_calls"]
        state["decoder_calls"] += 1
        case_no = call_no % len(cases)
        expected = cases[case_no]
        assert max_iter == 90
        assert damping_alpha == 1.0
        assert warm_beliefs is None
        assert field is None
        np.testing.assert_array_equal(h, expected["H"])
        np.testing.assert_array_equal(syndrome, expected["syndrome"])
        submitted_prior = np.asarray(prior, dtype=np.float64).copy()
        if expected["role"] == "selected_rescue":
            wanted = expected["prior"].copy()
            wanted[expected["selected_variable"], :] = 0.0
            wanted[expected["selected_variable"], expected["guess_symbol"]] = 1.0
            np.testing.assert_array_equal(submitted_prior, wanted)
        else:
            np.testing.assert_array_equal(submitted_prior, expected["prior"])
        state["decoder_inputs"].append((expected["source_call_index"],
                                         submitted_prior, np.asarray(h).copy(),
                                         np.asarray(syndrome).copy()))
        if mismatch_vector_call is not None and case_no == mismatch_vector_call:
            x_hat = expected["x_hat"].copy()
            x_hat[0] = (int(x_hat[0]) + 1) % 32
        else:
            x_hat = expected["x_hat"].copy()
        if clock_overshoot_call is not None and case_no == clock_overshoot_call:
            state["clock"] += 121.0
        if rss_over_call is not None and case_no >= rss_over_call:
            state["rss_over"] = True
        return SimpleNamespace(
            x_hat=x_hat,
            iterations=expected["iterations"],
            status=expected["decoder_status"],
            syndrome_ok=expected["syndrome_valid"],
            final_beliefs=expected["beliefs"].copy(),
            belief_provenance="CHECK_UPDATED",
        )

    def now():
        return state["clock"]

    def rss_fn():
        if state.get("rss_over"):
            return (1 << 30) + 1
        return 1_000_000

    return {
        "source_reader": source_reader,
        "decoder": decoder,
        "repo_root": Path.cwd(),
        "now": now,
        "rss_fn": rss_fn,
        "command": "explicit fake-only kernel hotspot test",
        "state": state,
    }


def _run(execute: dict, root_base: Path, *, out_root=None):
    if out_root is None:
        out_root = probe.OUT_ROOT_RELATIVE
    return probe.execute_batch(
        source_reader=execute["source_reader"], decoder=execute["decoder"],
        out_root=out_root, repo_root=root_base, now=execute["now"],
        rss_fn=execute["rss_fn"], command=execute["command"],
    )


def _records(result: dict) -> list[dict]:
    if "call_records" in result:
        return list(result["call_records"])
    with Path(result["artifacts"]["call_records.csv"]).open(
            newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _flag(value) -> bool:
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def _assert_partial_totals_are_null(summary: dict) -> None:
    for key in ("rounds", "roundtrip_checks", "roundtrip_match_count",
                "exact_count", "valid_wrong_count", "mean_call_wall_s",
                "profiled_call_wall_s"):
        assert summary[key] is None, key


def test_t0_and_dry_run_are_source_free_and_keep_official_root_absent(
        tmp_path: Path):
    t0 = probe.verify_t0(out_root=probe.OUT_ROOT_RELATIVE, repo_root=tmp_path)
    dry = probe.dry_run(out_root=probe.OUT_ROOT_RELATIVE, repo_root=tmp_path)
    assert t0["source_reads"] == t0["decoder_calls"] == 0
    assert t0["sampler_calls"] == t0["writes"] == 0
    assert dry["source_reads"] == dry["decoder_calls"] == 0
    assert dry["sampler_calls"] == dry["writes"] == 0
    assert not (tmp_path / probe.OUT_ROOT_RELATIVE).exists()


def test_fake_18_cases_round_trip_in_two_plain_rounds_and_decoder_profile(
        tmp_path: Path):
    source, cases = _fake_parent()
    adapters = _adapters(source, cases)
    # Use an isolated test repository root; never touch the frozen evidence root.
    adapters["repo_root"] = tmp_path
    result = _run(adapters, tmp_path)

    assert adapters["state"]["source_reads"] == result["source_reads"] == 1
    assert adapters["state"]["decoder_calls"] == result["decoder_calls"] == 54
    assert result["sampler_calls"] == 0
    assert result["status"] == "KERNEL_HOTSPOT_PROFILE_COMPLETE"
    expected_order = [case["source_call_index"] for case in cases]
    assert [call[0] for call in adapters["state"]["decoder_inputs"]] == (
        expected_order * 3)

    records = _records(result)
    assert len(records) == 54
    assert [row["round"] for row in records] == (
        [1] * 18 + [2] * 18 + [3] * 18)
    assert [row["profile_mode"] for row in records] == (
        ["unprofiled"] * 36 + ["cProfile"] * 18)
    assert [int(row["call_index"]) for row in records] == expected_order * 3
    assert [int(row["raw_vector_index"]) for row in records] == (
        [case["raw_vector_index"] for case in cases] * 3)
    assert all(_flag(row["replay_match_vector"]) for row in records)
    assert all(_flag(row["replay_match_iterations"]) for row in records)
    assert all(_flag(row["replay_match_status"]) for row in records)
    assert all(_flag(row["syndrome_valid"]) ==
               bool(cases[i % 18]["syndrome_valid"])
               for i, row in enumerate(records))
    # Truth is used only to label post-replay outcomes; the fixed selected
    # rescue pointers still replay the syndrome-valid but wrong saved vectors.
    rescue_rows = [row for row in records
                   if row["selection_role"] == "selected_rescue"]
    assert len(rescue_rows) == 18
    assert all(_flag(row["valid_wrong"]) for row in rescue_rows)
    assert all(row["call_role"] == "soft_prior" for row in rescue_rows)
    assert all(row["decoder_status"] == "saved-restart" for row in rescue_rows)
    assert result["summary"]["roundtrip_checks"] == 54
    assert result["summary"]["roundtrip_match_count"] == 54
    assert {key: value["calls"] for key, value in
            result["summary"]["rounds"].items()} == {"1": 18, "2": 18, "3": 18}
    assert all(value["wall_s"] == 0.0
               for value in result["summary"]["rounds"].values())
    assert result["summary"]["exact_count"] == 18
    assert result["summary"]["valid_wrong_count"] == 18

    for case in cases:
        expected_syndrome = v35.syndrome_of_gf32(case["H"], case["x_hat"])
        assert np.array_equal(expected_syndrome, case["syndrome"]) == case["syndrome_valid"]
        if case["role"] == "baseline_failed":
            assert np.allclose(case["beliefs"], 0.0, rtol=0.0, atol=1e-12)
    np.testing.assert_array_equal(
        source["diagnostics"]["original_prior"], cases[0]["prior"])

    artifacts = result["artifacts"]
    assert set(artifacts) >= {
        "manifest.json", "summary.json", "call_records.csv",
        "profile.txt", "EXPLORATION_LOG.md",
    }
    profile_path = Path(artifacts["profile.txt"])
    assert profile_path.exists()
    profile_text = profile_path.read_text(encoding="utf-8").lower()
    decoder_stats = [line.split() for line in profile_text.splitlines()
                     if "test_nbldpc_gf32_kernel_hotspots.py" in line
                     and "(decoder)" in line]
    assert any(fields and fields[0] == "18" for fields in decoder_stats)
    assert "(resource_check)" not in profile_text
    assert "(execute_batch)" not in profile_text
    assert result["summary"]["profiled_decoder_calls"] == 18


def test_existing_root_refuses_before_source_or_decoder(tmp_path: Path):
    source, cases = _fake_parent()
    adapters = _adapters(source, cases)
    adapters["repo_root"] = tmp_path
    existing = tmp_path / probe.OUT_ROOT_RELATIVE
    existing.mkdir(parents=True)
    with pytest.raises(FileExistsError):
        _run(adapters, tmp_path)
    assert adapters["state"]["source_reads"] == 0
    assert adapters["state"]["decoder_calls"] == 0


@pytest.mark.parametrize("cap", ["wall", "rss"])
def test_single_return_over_cap_is_retained_and_stops_without_retry(
        tmp_path: Path, cap: str):
    source, cases = _fake_parent()
    if cap == "wall":
        adapters = _adapters(source, cases, clock_overshoot_call=0)
    else:
        adapters = _adapters(source, cases, rss_over_call=0)
    adapters["repo_root"] = tmp_path
    result = _run(adapters, tmp_path)

    assert adapters["state"]["decoder_calls"] == result["decoder_calls"] == 1
    assert len(_records(result)) == 1
    assert result["status"] != "KERNEL_HOTSPOT_PROFILE_COMPLETE"
    assert result["summary"]["resource_events"]
    assert result["summary"]["stop_reasons"]
    _assert_partial_totals_are_null(result["summary"])


@pytest.mark.parametrize("mutation", ["source_identity", "missing_stratum", "bad_vector_pointer"])
def test_source_selection_mismatch_stops_before_bp(
        tmp_path: Path, mutation: str):
    source, cases = _fake_parent()
    if mutation == "source_identity":
        source["manifest"]["source_identity"]["batch_uuid"] = "wrong-source"
    elif mutation == "missing_stratum":
        diag = source["diagnostics"]
        # Remove the first graph's baseline-valid case without changing pair order.
        source_call = int(diag["pair_baseline_call_index"][0])
        row = int(np.flatnonzero(diag["call_index"] == source_call)[0])
        diag["call_syndrome_valid"][row] = False
    else:
        diag = source["diagnostics"]
        source_call = int(diag["pair_candidate_selected_call_index"][1])
        row = int(np.flatnonzero(diag["call_index"] == source_call)[0])
        diag["call_raw_vector_index"][row] = int(
            diag["call_raw_vector_index"][row - 1])
    adapters = _adapters(source, cases)
    adapters["repo_root"] = tmp_path
    result = _run(adapters, tmp_path)

    assert adapters["state"]["source_reads"] == 1
    assert adapters["state"]["decoder_calls"] == result["decoder_calls"] == 0
    assert result["status"] != "KERNEL_HOTSPOT_PROFILE_COMPLETE"
    _assert_partial_totals_are_null(result["summary"])
    assert result["summary"]["stop_reasons"]


def test_round_trip_vector_mismatch_retains_actual_call_and_stops(
        tmp_path: Path):
    source, cases = _fake_parent()
    adapters = _adapters(source, cases, mismatch_vector_call=0)
    adapters["repo_root"] = tmp_path
    result = _run(adapters, tmp_path)

    assert adapters["state"]["decoder_calls"] == result["decoder_calls"] == 1
    assert len(_records(result)) == 1
    assert result["status"] != "KERNEL_HOTSPOT_PROFILE_COMPLETE"
    assert "saved_call_roundtrip_mismatch" in result["call_records"][0]["failure_reason"]
    _assert_partial_totals_are_null(result["summary"])
    assert result["summary"]["stop_reasons"]


def test_exact_requires_truth_match_and_independent_syndrome(
        tmp_path: Path):
    source, cases = _fake_parent()
    diagnostics = source["diagnostics"]
    failed_pair_pos = int(np.flatnonzero(diagnostics["pair_index"] == 1)[0])
    # Deliberately corrupt only fake truth so it equals the failed baseline's
    # all-zero estimate despite that estimate violating the given syndrome.
    diagnostics["pair_truth"][failed_pair_pos, :] = 0
    adapters = _adapters(source, cases, clock_overshoot_call=1)
    adapters["repo_root"] = tmp_path
    result = _run(adapters, tmp_path)

    records = _records(result)
    assert len(records) == adapters["state"]["decoder_calls"] == 2
    failed = records[1]
    assert failed["selection_role"] == "baseline_failed"
    assert not _flag(failed["syndrome_valid"])
    assert not _flag(failed["exact"])
    assert not _flag(failed["valid_wrong"])
    _assert_partial_totals_are_null(result["summary"])


def test_linux_rss_high_water_kib_is_reported_as_bytes(
        monkeypatch: pytest.MonkeyPatch):
    import resource

    monkeypatch.setattr(resource, "getrusage",
                        lambda who: SimpleNamespace(ru_maxrss=33072))
    assert probe._rss_bytes() == 33_865_728


