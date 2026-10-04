"""Focused fake-only tests for the post-hoc GF(32) soft-prior cost profile."""
from __future__ import annotations

import csv
import inspect
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli.probes_closed import nbldpc_gf32_softprior_cost_profile as profile
from comparison_bench.cli.probes_closed import nbldpc_gf32_softprior_replica as replica
from comparison_bench.cli.probes_closed import nbldpc_gf32_softprior_rescue as rescue
from .test_nbldpc_gf32_softprior_rescue import (
    _fake_source_arrays, _original_prior, _truth,
)


SUPPORT = (0, 1, 3, 7, 15, 31)


def _probability_map(ordered_symbols, probabilities):
    if hasattr(probabilities, "items"):
        return {int(symbol): float(value)
                for symbol, value in probabilities.items()}
    return {int(symbol): float(value)
            for symbol, value in zip(ordered_symbols, probabilities)}


def _fake_parent_artifact(parent_index: int) -> dict:
    """Build an in-memory saved-parent-shaped fixture; it reads no artifacts."""
    parent_uuid, parent_contract, namespace, parent_root, classification = (
        profile.PARENT_SPECS[parent_index])
    parent_module = rescue if parent_index == 0 else replica
    identity, selected_sources = rescue.select_sources(_fake_source_arrays())
    source_maps = [{key: value for key, value in row.items() if key != "H"}
                   for row in selected_sources]
    graph_rows = {int(row["graph_id"]): row for row in selected_sources}
    graph_ids = list(profile.GRAPH_IDS)
    if parent_index == 0:
        control_successes = [27, 26, 26, 26, 25, 25]
        recoveries = [2, 2, 2, 2, 2, 2]
    else:
        control_successes = [24, 24, 24, 24, 23, 23]
        recoveries = [3, 3, 2, 3, 1, 2]

    original_prior = _original_prior()
    truth = _truth()
    zero = np.zeros(128, dtype=np.uint8)
    graph_pair_counts = {graph_id: 0 for graph_id in graph_ids}
    graph_failure_counts = {graph_id: 0 for graph_id in graph_ids}
    pair_arrays = {key: [] for key in (
        "pair_index", "pair_graph_id", "pair_stream", "pair_frame", "pair_seed",
        "pair_truth", "pair_syndrome", "pair_completed",
        "pair_baseline_call_index", "pair_candidate_selected_call_index",
        "pair_selected_variable",
    )}
    call_arrays = {key: [] for key in (
        "call_index", "call_pair_index", "call_graph_id", "call_stream",
        "call_frame", "call_seed", "call_role", "call_branch_index",
        "call_guess_symbol", "call_selected_variable", "call_status",
        "call_iterations", "call_decoder_runtime_s", "call_wall_s",
        "call_syndrome_valid", "call_raw_vector_index",
        "call_score_original_prior", "call_candidate_selected_call_index",
    )}
    raw_call_indices, raw_vectors = [], []
    belief_calls, belief_rows, selector_calls = [], [], []
    selector_columns = []

    def append_call(pair_index, graph_id, stream, frame, seed, role,
                    branch_index, guess_symbol, selected_variable, vector,
                    syndrome, iterations, score):
        call_index = len(call_arrays["call_index"])
        h = graph_rows[graph_id]["H"]
        syndrome_valid = np.array_equal(
            np.asarray(rescue.layout.gf32_syndrome(h, vector)).ravel(), syndrome)
        vector_index = len(raw_vectors)
        raw_vectors.append(np.asarray(vector, dtype=np.uint8).copy())
        raw_call_indices.append(call_index)
        values = {
            "call_index": call_index, "call_pair_index": pair_index,
            "call_graph_id": graph_id, "call_stream": stream,
            "call_frame": frame, "call_seed": seed, "call_role": role,
            "call_branch_index": branch_index, "call_guess_symbol": guess_symbol,
            "call_selected_variable": selected_variable,
            "call_status": "COMPLETE", "call_iterations": iterations,
            "call_decoder_runtime_s": 0.001,
            "call_wall_s": 0.002 + 0.001 * max(branch_index, 0),
            "call_syndrome_valid": syndrome_valid,
            "call_raw_vector_index": vector_index,
            "call_score_original_prior": score,
            "call_candidate_selected_call_index": -1,
        }
        for key, value in values.items():
            call_arrays[key].append(value)
        return call_index, syndrome_valid

    plan = parent_module.build_seed_plan()
    for pair_index, (graph_id_raw, stream_raw, frame_raw, seed_raw) in enumerate(plan):
        graph_id, stream, frame, seed = map(
            int, (graph_id_raw, stream_raw, frame_raw, seed_raw))
        within_graph = graph_pair_counts[graph_id]
        graph_pair_counts[graph_id] += 1
        control_ok = within_graph < control_successes[graph_ids.index(graph_id)]
        failure_number = graph_failure_counts[graph_id]
        recover = (not control_ok and
                   failure_number < recoveries[graph_ids.index(graph_id)])
        if not control_ok:
            graph_failure_counts[graph_id] += 1
        h = graph_rows[graph_id]["H"]
        syndrome = np.asarray(
            rescue.layout.gf32_syndrome(h, truth), dtype=np.uint8).ravel()
        begin_call = len(call_arrays["call_index"])
        baseline_vector = truth if control_ok else zero
        baseline_call, baseline_valid = append_call(
            pair_index, graph_id, stream, frame, seed, "baseline", -1, -1,
            -1, baseline_vector, syndrome, 7 if control_ok else 90, np.nan)
        assert baseline_valid is control_ok
        branch_calls = []
        if not control_ok:
            belief_calls.append(baseline_call)
            belief_rows.append(np.zeros((128, 32), dtype=np.float64))
            selector_calls.append(baseline_call)
            selector_columns.append(0)
            for branch_index, guess_symbol in enumerate(SUPPORT):
                if recover and branch_index < 5:
                    vector = truth.copy()
                    vector[:3] = (1, 3, 7, 15, 31)[branch_index]
                elif recover:
                    vector = truth.copy()
                else:
                    vector = zero
                valid = np.array_equal(
                    np.asarray(rescue.layout.gf32_syndrome(h, vector)).ravel(), syndrome)
                if valid:
                    effective = np.maximum(original_prior, 1e-15)
                    score = float(np.log(
                        effective[np.arange(128), vector.astype(np.int64)]).sum())
                else:
                    score = np.nan
                branch_call, branch_valid = append_call(
                    pair_index, graph_id, stream, frame, seed, "soft_prior",
                    branch_index, guess_symbol, 0, vector, syndrome,
                    5 + branch_index, score)
                assert branch_valid is valid
                branch_calls.append(branch_call)

        candidate_call = (branch_calls[5] if recover else baseline_call)
        for call_index in range(begin_call, len(call_arrays["call_index"])):
            call_arrays["call_candidate_selected_call_index"][call_index] = candidate_call
        pair_arrays["pair_index"].append(pair_index)
        pair_arrays["pair_graph_id"].append(graph_id)
        pair_arrays["pair_stream"].append(stream)
        pair_arrays["pair_frame"].append(frame)
        pair_arrays["pair_seed"].append(seed)
        pair_arrays["pair_truth"].append(truth.copy())
        pair_arrays["pair_syndrome"].append(syndrome)
        pair_arrays["pair_completed"].append(True)
        pair_arrays["pair_baseline_call_index"].append(baseline_call)
        pair_arrays["pair_candidate_selected_call_index"].append(candidate_call)
        pair_arrays["pair_selected_variable"].append(-1 if control_ok else 0)

    diagnostics = {
        "source_batch_uuid": np.asarray([profile.SOURCE_EXPECTED["batch_uuid"]]),
        "source_contract": np.asarray([profile.SOURCE_EXPECTED["contract"]]),
        "source_seed_namespace": np.asarray([profile.SOURCE_EXPECTED["seed_namespace"]]),
        "source_graph_input_kind": np.asarray([profile.SOURCE_EXPECTED["graph_input_kind"]]),
        "source_graph_id": np.asarray([row["graph_id"] for row in selected_sources], dtype=np.int64),
        "source_graph_seed": np.asarray([row["graph_seed"] for row in selected_sources], dtype=np.int64),
        "source_profile_index": np.asarray([row["profile_index"] for row in selected_sources], dtype=np.int64),
        "source_graph_index": np.asarray([row["graph_index"] for row in selected_sources], dtype=np.int64),
        "source_constructor_uuid": np.asarray([
            row["source_lineage"]["source_uuid"] for row in selected_sources]),
        "source_constructor_path": np.asarray([
            row["source_lineage"]["source_path"] for row in selected_sources]),
        "source_constructor_matrix_index": np.asarray([
            row["source_lineage"]["source_matrix_index"] for row in selected_sources], dtype=np.int64),
        "source_constructor_attempt_j": np.asarray([
            row["source_lineage"]["source_attempt_j"] for row in selected_sources], dtype=np.int64),
        "source_constructor_seed": np.asarray([
            row["source_lineage"]["source_construction_seed"] for row in selected_sources], dtype=np.int64),
        "source_constructor_graph_id": np.asarray([
            row["source_lineage"]["source_graph_id"] for row in selected_sources], dtype=np.int64),
        "H_deep": np.stack([row["H"] for row in selected_sources]),
        "original_prior": original_prior,
        **{key: np.asarray(value) for key, value in pair_arrays.items()},
        **{key: np.asarray(value) for key, value in call_arrays.items()},
        "raw_vector_call_index": np.asarray(raw_call_indices, dtype=np.int64),
        "raw_x_hat": np.stack(raw_vectors),
        "belief_call_index": np.asarray(belief_calls, dtype=np.int64),
        "baseline_failure_belief_provenance": np.asarray(["CHECK_UPDATED"] * len(belief_calls)),
        "baseline_failure_beliefs": (np.stack(belief_rows) if belief_rows
                                      else np.empty((0, 128, 32), dtype=np.float64)),
        "selector_call_index": np.asarray(selector_calls, dtype=np.int64),
        "selector_selected_column": np.asarray(selector_columns, dtype=np.int64),
    }
    assert set(diagnostics) == set(profile.PARENT_DIAGNOSTIC_KEYS)
    control_exact = sum(control_successes)
    candidate_exact = control_exact + sum(recoveries)
    failure_count = 192 - control_exact
    branch_calls = 6 * failure_count
    summary = {
        "batch_uuid": parent_uuid, "contract": parent_contract,
        "seed_namespace": namespace, "status": "COMPLETE",
        "classification": classification, "completed_pairs": 192,
        "baseline_calls": 192, "branch_calls": branch_calls,
        "attempted_physical_calls": 192 + branch_calls,
        "control_exact": control_exact,
        "candidate_exact": candidate_exact,
        "delta_exact": candidate_exact - control_exact,
        "syndrome_valid_wrong_control": 0,
        "syndrome_valid_wrong_candidate": 0,
        "syndrome_failed_control": failure_count,
        "syndrome_failed_candidate": failure_count - sum(recoveries),
    }
    manifest = {
        "batch_uuid": parent_uuid, "contract": parent_contract,
        "seed_namespace": namespace, "status": "COMPLETE",
        "classification": classification,
        "source_expected": dict(profile.SOURCE_EXPECTED),
        "source_identity": dict(identity), "source_maps": source_maps,
    }
    return {"manifest": manifest, "summary": summary,
            "diagnostics": diagnostics, "root": parent_root}


def test_rank_allowed_guesses_uses_all32_softmax_and_stable_support_ties():
    log_beliefs = np.zeros((128, 32), dtype=np.float64)
    log_beliefs[4] = np.linspace(-2.0, 2.0, 32)
    ordered, probabilities = profile.rank_allowed_guesses(log_beliefs, 4)

    all32 = np.exp(log_beliefs[4] - np.max(log_beliefs[4]))
    all32 /= all32.sum()
    expected = {symbol: float(all32[symbol]) for symbol in SUPPORT}
    assert set(map(int, ordered)) == set(SUPPORT)
    assert list(map(int, ordered)) == sorted(SUPPORT, key=lambda s: (-expected[s], s))
    actual = _probability_map(ordered, probabilities)
    assert actual.keys() == expected.keys()
    np.testing.assert_allclose([actual[s] for s in SUPPORT],
                               [expected[s] for s in SUPPORT],
                               rtol=0.0, atol=1e-15)
    assert sum(actual.values()) < 1.0  # excluded symbols remain in denominator

    tied, tied_probabilities = profile.rank_allowed_guesses(
        np.zeros((128, 32), dtype=np.float64), 4)
    assert list(map(int, tied)) == list(SUPPORT)
    tied_map = _probability_map(tied, tied_probabilities)
    np.testing.assert_allclose([tied_map[s] for s in SUPPORT],
                               [1.0 / 32.0] * len(SUPPORT),
                               rtol=0.0, atol=1e-15)


def test_parent_choice_is_truth_blind_uses_original_prior_and_falls_back():
    # The lower-score branch is truth-correct, but selection must use only the
    # frozen validity and original-prior score fields.
    branch_rows = [
        {"call_index": 12, "branch_index": 0, "guess_symbol": 0,
         "syndrome_valid": True, "score_original_prior": -1.0,
         "raw_vector_index": 4},
        {"call_index": 13, "branch_index": 1, "guess_symbol": 1,
         "syndrome_valid": True, "score_original_prior": -0.25,
         "raw_vector_index": 5},
        {"call_index": 14, "branch_index": 2, "guess_symbol": 3,
         "syndrome_valid": False, "score_original_prior": 0.0,
         "raw_vector_index": 6},
    ]
    selector_parameters = inspect.signature(
        profile.choose_parent_candidate).parameters
    assert "truth" not in selector_parameters

    # Independent post-selection evaluation: call 13 is valid but wrong.
    truth_by_call = {12: True, 13: False, 14: False}
    selected = profile.choose_parent_candidate(7, (0, 1, 3), branch_rows)
    assert selected["candidate_call_index"] == 13
    assert selected["selected_branch_index"] == 1
    assert selected["selected_guess_symbol"] == 1
    assert selected["fallback"] is False
    assert truth_by_call[selected["candidate_call_index"]] is False

    tied = [
        {"call_index": 20, "branch_index": 4, "guess_symbol": 15,
         "syndrome_valid": True, "score_original_prior": -0.5,
         "raw_vector_index": 7},
        {"call_index": 21, "branch_index": 2, "guess_symbol": 3,
         "syndrome_valid": True, "score_original_prior": -0.5 + 5e-13,
         "raw_vector_index": 8},
    ]
    tie_result = profile.choose_parent_candidate(9, (3, 15), tied)
    assert tie_result["candidate_call_index"] == 21
    assert tie_result["selected_branch_index"] == 2

    fallback = profile.choose_parent_candidate(
        33, (0, 1), [dict(row, syndrome_valid=False) for row in branch_rows[:2]])
    assert fallback["candidate_call_index"] == 33
    assert fallback["selected_branch_index"] is None
    assert fallback["selected_guess_symbol"] is None
    assert fallback["fallback"] is True


def test_t0_and_dry_run_are_source_free_and_leave_official_root_absent(
        tmp_path: Path):
    t0 = profile.verify_t0(repo_root=tmp_path)
    dry = profile.dry_run(repo_root=tmp_path)
    expected_root = tmp_path / profile.OUT_ROOT_RELATIVE

    assert t0["status"] == "PASS"
    assert t0["batch_uuid"] == profile.BATCH_UUID
    assert t0["contract_id"] == profile.CONTRACT
    assert t0["source_reads"] == 0
    assert t0["decoder_calls"] == 0
    assert t0["sampler_calls"] == 0
    assert t0["writes"] == 0
    assert dry["status"] == "DRY_RUN"
    assert dry["batch_uuid"] == profile.BATCH_UUID
    assert dry["contract_id"] == profile.CONTRACT
    assert dry["source_reads"] == 0
    assert dry["decoder_calls"] == 0
    assert dry["sampler_calls"] == 0
    assert dry["writes"] == 0
    assert not expected_root.exists()


def test_wrong_or_existing_output_root_refuses_before_reader(tmp_path: Path):
    reads = []

    def source_reader(_path):
        reads.append(1)
        raise AssertionError("root preflight must precede source reads")

    common = {"source_reader": source_reader, "repo_root": tmp_path}
    with pytest.raises(ValueError):
        profile.execute_batch(out_root="workspace/not-the-frozen-root", **common)
    assert reads == []

    official_root = tmp_path / profile.OUT_ROOT_RELATIVE
    official_root.mkdir(parents=True)
    with pytest.raises(FileExistsError):
        profile.execute_batch(out_root=profile.OUT_ROOT_RELATIVE, **common)
    assert reads == []


def test_linux_rss_helper_returns_bytes_from_getrusage_kib(
        monkeypatch: pytest.MonkeyPatch):
    queried = []
    fake_resource = SimpleNamespace(
        RUSAGE_SELF="self",
        getrusage=lambda who: queried.append(who)
        or SimpleNamespace(ru_maxrss=33072),
    )
    monkeypatch.setitem(sys.modules, "resource", fake_resource)

    assert profile._rss_bytes() == 33_865_728
    assert queried == ["self"]


def _fake_profile_adapters(tmp_path: Path, *, resource_overrun: bool = False,
                           wrong_first_anchor: bool = False,
                           source_identity_mismatch: bool = False) -> dict:
    parents = [_fake_parent_artifact(i) for i in range(2)]
    by_root = {Path(row["root"]).name: row for row in parents}
    if wrong_first_anchor:
        bad = parents[0]["diagnostics"]
        other_pair_call = int(bad["pair_baseline_call_index"][1])
        bad["pair_candidate_selected_call_index"][0] = other_pair_call
    if source_identity_mismatch:
        parents[0]["diagnostics"]["source_batch_uuid"] = np.asarray(["bad-source-uuid"])
    state = {"source_reads": 0, "clock": 0.0}

    def source_reader(parent_root):
        state["source_reads"] += 1
        return by_root[parent_root.name]

    def now():
        state["clock"] += 0.001
        return state["clock"]

    def rss_fn():
        if resource_overrun and state["source_reads"] >= 1:
            return profile.RSS_CAP_BYTES + 1
        return 100_000

    return {
        "source_reader": source_reader, "repo_root": tmp_path,
        "now": now, "rss_fn": rss_fn, "command": "fake-only cost profile",
        "state": state, "parents": parents,
    }


def test_fake_two_parent_profiles_charge_all_topk_calls_and_keep_truth_after_selection(
        tmp_path: Path):
    adapters = _fake_profile_adapters(tmp_path)
    state = adapters.pop("state")
    fake_parents = adapters.pop("parents")
    call_costs = {}
    for parent in fake_parents:
        diag = parent["diagnostics"]
        call_ids = diag["call_index"].astype(int)
        call_costs[parent["manifest"]["batch_uuid"]] = {
            int(call_id): {
                "iterations": int(diag["call_iterations"][index]),
                "runtime": float(diag["call_decoder_runtime_s"][index]),
                "wall": float(diag["call_wall_s"][index]),
            }
            for index, call_id in enumerate(call_ids)
        }

    result = profile.execute_batch(
        out_root=profile.OUT_ROOT_RELATIVE, **adapters)
    output_root = tmp_path / profile.OUT_ROOT_RELATIVE

    assert result["status"] == "POSTHOC_COUNTERFACTUAL_PROFILE_COMPLETE"
    assert state["source_reads"] == result["source_reads"] == 2
    assert result["decoder_calls"] == result["sampler_calls"] == 0
    assert result["summary"]["selection_truth_used"] is False
    assert result["summary"]["completed_parent_count"] == 2
    assert len(result["pair_records"]) == 2 * 4 * 192
    assert set(path.name for path in output_root.iterdir()) == {
        "manifest.json", "summary.json", "pair_records.csv", "EXPLORATION_LOG.md",
    }

    accepted_parent_counts = {
        profile.PARENT_SPECS[0][0]: (37, 155, 167),
        profile.PARENT_SPECS[1][0]: (50, 142, 156),
    }
    for parent_uuid, (failure_count, control_exact, parent_candidate_exact) in (
            accepted_parent_counts.items()):
        profiles = result["parent_profiles"][parent_uuid]
        parent_rows = [row for row in result["pair_records"]
                       if row["parent_uuid"] == parent_uuid]
        assert len(parent_rows) == 4 * 192
        costs = call_costs[parent_uuid]
        baseline_ids = {int(row["control_call_index"]) for row in parent_rows}
        assert len(baseline_ids) == 192
        for k in profile.K_VALUES:
            k_rows = [row for row in parent_rows if row["k"] == k]
            item = profiles[str(k)]
            retained_ids = {int(call_id) for row in k_rows
                            for call_id in row["retained_branch_call_indices"]}
            assert item["completed_pairs"] == 192
            assert item["baseline_failures"] == failure_count
            assert item["retained_branch_attempts"] == failure_count * k
            assert item["logical_control_calls"] == 192
            assert item["logical_candidate_calls"] == 192 + failure_count * k
            assert item["logical_control_iterations"] == sum(
                costs[call_id]["iterations"] for call_id in baseline_ids)
            assert item["logical_candidate_iterations"] == sum(
                costs[call_id]["iterations"] for call_id in baseline_ids | retained_ids)
            assert item["logical_candidate_decoder_runtime_s"] == pytest.approx(sum(
                costs[call_id]["runtime"] for call_id in baseline_ids | retained_ids))
            assert item["logical_candidate_recorded_wall_s"] == pytest.approx(sum(
                costs[call_id]["wall"] for call_id in baseline_ids | retained_ids))
            assert item["profile_execution_decoder_calls"] == 0
            assert item["profile_execution_sampler_calls"] == 0
            assert item["disclosure_bits_per_method"] == 192 * 260
            assert item["verification"] == "NOT_IMPLEMENTED"
            assert item["undetected"] == "NOT_MEASURED"
        assert profiles["6"]["candidate_exact"] == parent_candidate_exact
        assert profiles["6"]["control_exact"] == control_exact
        assert profiles["6"]["syndrome_valid_wrong_candidate"] == 0

        rescue_pair = next(row for row in parent_rows
                           if row["k"] == 1 and row["selection_fallback_to_baseline"] is False
                           and row["candidate_valid_wrong"])
        assert rescue_pair["candidate_syndrome_valid"] is True
        assert rescue_pair["candidate_exact"] is False
        assert rescue_pair["selected_branch_index"] == 0
        full_pair = next(row for row in parent_rows
                         if row["k"] == 6 and row["pair_index"] == rescue_pair["pair_index"])
        assert full_pair["candidate_exact"] is True
        assert full_pair["selected_branch_index"] == 5
        parent_index = 0 if parent_uuid == profile.PARENT_SPECS[0][0] else 1
        parent_diagnostics = fake_parents[parent_index]["diagnostics"]
        raw_call_ids = parent_diagnostics["raw_vector_call_index"]
        chosen_call = int(rescue_pair["candidate_call_index"])
        assert chosen_call in set(map(int, raw_call_ids))
        chosen_vector_index = int(np.flatnonzero(raw_call_ids == chosen_call)[0])
        assert int(rescue_pair["selected_raw_vector_index"]) == chosen_vector_index
        assert not np.array_equal(
            parent_diagnostics["raw_x_hat"][chosen_vector_index],
            parent_diagnostics["pair_truth"][rescue_pair["pair_index"]])
        full_vector_index = int(full_pair["selected_raw_vector_index"])
        assert np.array_equal(
            parent_diagnostics["raw_x_hat"][full_vector_index],
            parent_diagnostics["pair_truth"][full_pair["pair_index"]])

    csv_path = Path(result["artifacts"]["pair_records"])
    with csv_path.open(encoding="utf-8", newline="") as stream:
        csv_rows = list(csv.DictReader(stream))
    assert len(csv_rows) == 2 * 4 * 192
    assert "selected_raw_vector_index" in csv_rows[0]
    assert "pair_truth" not in csv_rows[0]
    persisted = json.loads(Path(result["artifacts"]["summary"]).read_text(
        encoding="utf-8"))
    assert persisted["status"] == result["status"]
    assert persisted["source_reads"] == 2


def test_fake_partial_rss_stop_nulls_profile_totals_and_missing_anchor_stops(
        tmp_path: Path):
    adapters = _fake_profile_adapters(tmp_path, resource_overrun=True)
    state = adapters.pop("state")
    adapters.pop("parents")
    result = profile.execute_batch(
        out_root=profile.OUT_ROOT_RELATIVE, **adapters)
    first_uuid = profile.PARENT_SPECS[0][0]
    assert state["source_reads"] == result["source_reads"] == 1
    assert result["status"] == "INCOMPLETE"
    assert first_uuid in result["parent_profiles"]
    for item in result["parent_profiles"][first_uuid].values():
        assert item["status"] == "INCOMPLETE"
        assert item["control_exact"] is item["candidate_exact"] is None
        assert item["delta_exact"] is item["paired"] is item["per_graph"] is None
    assert result["summary"]["resource_events"]

    bad_root = tmp_path / "bad-anchor-case"
    bad_root.mkdir()
    adapters = _fake_profile_adapters(
        bad_root, wrong_first_anchor=True)
    state = adapters.pop("state")
    adapters.pop("parents")
    stopped = profile.execute_batch(
        out_root=profile.OUT_ROOT_RELATIVE, **adapters)
    assert state["source_reads"] == stopped["source_reads"] == 1
    assert stopped["status"] == "STOP"
    assert stopped["decoder_calls"] == stopped["sampler_calls"] == 0
    assert stopped["parent_profiles"] == {}
    assert "accepted_candidate_call_map_mismatch" in " ".join(
        stopped["summary"]["stop_reasons"])

    source_root = tmp_path / "bad-source-case"
    source_root.mkdir()
    adapters = _fake_profile_adapters(
        source_root, source_identity_mismatch=True)
    state = adapters.pop("state")
    adapters.pop("parents")
    source_stop = profile.execute_batch(
        out_root=profile.OUT_ROOT_RELATIVE, **adapters)
    assert state["source_reads"] == source_stop["source_reads"] == 1
    assert source_stop["status"] == "STOP"
    assert source_stop["decoder_calls"] == source_stop["sampler_calls"] == 0
    assert source_stop["parent_profiles"] == {}
    assert source_stop["summary"]["parents"][0]["status"] == "STOP"
    assert "source_batch_uuid_mismatch" in " ".join(
        source_stop["summary"]["stop_reasons"])
    log_text = Path(source_stop["artifacts"]["exploration_log"]).read_text(
        encoding="utf-8")
    assert "FINAL_STATUS=STOP" in log_text
