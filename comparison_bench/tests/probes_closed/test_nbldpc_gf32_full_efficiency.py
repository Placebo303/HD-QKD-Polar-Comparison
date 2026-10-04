"""Focused callback-only tests for the frozen GF(32) efficiency replay."""
from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli.probes_closed import nbldpc_gf32_full_efficiency as probe
from comparison_bench.cli.probes_closed import nbldpc_gf32_kernel_hotspots as hotspots


GRAPH_IDS = tuple(range(2026093901, 2026093907))
PARENT_UUID = "cbe151fe-25f7-4990-8895-858091467e2b"
PARENT_CONTRACT = "NBLDPC-GF32-SOFT-PRIOR-REPLICA-20261001/PREREG_AND_AUTH.md"
PARENT_NAMESPACE = "gf32-softprior-replica-v1"
SOURCE_UUID = "a9352bc1-ae56-443b-ae93-9dcfa85d4229"
SOURCE_CONTRACT = "NBLDPC-GF32-DEGREE-ADMITTED-20261001/PREREG_AND_AUTH.md"
SOURCE_NAMESPACE = "gf32-degree-admitted-v1"
GUESSES = (0, 1, 3, 7, 15, 31)


def _fake_h() -> np.ndarray:
    h = np.zeros((52, 128), dtype=np.uint8)
    h[0, 0] = 1
    h[0, 1] = 1
    return h


def _fake_source() -> dict:
    """Construct the complete 192-pair/492-call accepted source shape in memory."""
    h_by_graph = {graph: _fake_h() for graph in GRAPH_IDS}
    original_prior = np.full((128, 32), 1.0 / 32.0, dtype=np.float64)
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
    call_raw_vector_index: list[int] = []
    raw_vectors_by_call: dict[int, np.ndarray] = {}
    branch_score_call_index: list[int] = []
    branch_score_branch_index: list[int] = []
    branch_score_guess_symbol: list[int] = []
    branch_score_original_prior: list[float] = []
    branch_score_available: list[bool] = []
    branch_score_syndrome_valid: list[bool] = []

    call_id = 10_000
    failed_ordinal_by_graph = {graph: 0 for graph in GRAPH_IDS}
    rescued_ordinal = 0
    for pair_id in range(192):
        graph_pos = pair_id // 32
        graph_id = GRAPH_IDS[graph_pos]
        local_pair = pair_id % 32
        failed_limit = 8 if graph_pos < 4 else 9
        baseline_failed = local_pair >= 32 - failed_limit
        syndrome = np.zeros(52, dtype=np.uint8)
        truth = np.zeros(128, dtype=np.uint8)
        if baseline_failed:
            syndrome[0] = 2
            failed_ordinal = failed_ordinal_by_graph[graph_id]
            failed_ordinal_by_graph[graph_id] += 1
            baseline = np.zeros(128, dtype=np.uint8)
            baseline[0] = 1
            branch_valid = failed_ordinal < (4 if graph_pos < 5 else 3)
            if branch_valid:
                if rescued_ordinal < 14:
                    truth[0], truth[1] = 0, 2  # branch 0 is exact
                elif rescued_ordinal < 23:
                    truth[0], truth[1] = 3, 1  # unselected branch 2 is exact
                else:
                    raise AssertionError("fake rescue allocation exceeded 23")
                rescued_ordinal += 1
            else:
                truth[0], truth[1] = 0, 2
        else:
            baseline = np.zeros(128, dtype=np.uint8)
            branch_valid = False

        pair_index.append(pair_id)
        pair_graph_id.append(graph_id)
        pair_syndrome.append(syndrome)
        pair_truth.append(truth)
        baseline_id = call_id
        pair_baseline_call_index.append(baseline_id)
        pair_selected_variable.append(0 if baseline_failed else -1)

        def append_call(*, role: str, branch: int, guess: int, selected: int,
                        vector: np.ndarray, iterations: int) -> int:
            nonlocal call_id
            current_id = call_id
            call_id += 1
            valid = bool(np.array_equal(
                hotspots.layout.gf32_syndrome(h_by_graph[graph_id], vector), syndrome))
            call_index.append(current_id)
            call_pair_index.append(pair_id)
            call_graph_id.append(graph_id)
            call_role.append(role)
            call_branch_index.append(branch)
            call_guess_symbol.append(guess)
            call_selected_variable.append(selected)
            call_status.append("COMPLETE")
            call_decoder_status.append("fake-valid" if valid else "fake-invalid")
            call_iterations.append(iterations)
            call_syndrome_valid.append(valid)
            call_syndrome_ok_reported.append(valid)
            raw_vectors_by_call[current_id] = vector.copy()
            return current_id

        append_call(
            role="baseline", branch=-1, guess=-1,
            selected=0 if baseline_failed else -1, vector=baseline,
            iterations=90 if baseline_failed else 7)

        selected_source_call = baseline_id
        if baseline_failed:
            for branch, guess in enumerate(GUESSES):
                vector = np.zeros(128, dtype=np.uint8)
                if branch_valid:
                    vector[0] = guess
                    vector[1] = guess ^ 2
                branch_id = append_call(
                    role="soft_prior", branch=branch, guess=guess, selected=0,
                    vector=vector, iterations=5 + branch)
                branch_score_call_index.append(branch_id)
                branch_score_branch_index.append(branch)
                branch_score_guess_symbol.append(guess)
                branch_score_original_prior.append(
                    float(128 * np.log(1.0 / 32.0)) if branch_valid else float("nan"))
                branch_score_available.append(branch_valid)
                branch_score_syndrome_valid.append(branch_valid)
                if branch == 0 and branch_valid:
                    selected_source_call = branch_id
        pair_candidate_selected_call_index.append(selected_source_call)

    if call_id != 10_492 or len(call_index) != 492 or rescued_ordinal != 23:
        raise AssertionError("fake source construction did not reach the frozen counts")

    # Store vectors physically in reverse call order to exercise source ID maps.
    raw_vector_call_index = np.asarray(call_index[::-1], dtype=np.int64)
    raw_x_hat = np.stack([raw_vectors_by_call[int(source_id)]
                          for source_id in raw_vector_call_index])
    raw_pos = {int(source_id): pos for pos, source_id in enumerate(raw_vector_call_index)}
    call_raw_vector_index = [raw_pos[source_id] for source_id in call_index]
    failed_baseline_ids = [
        int(pair_baseline_call_index[i]) for i, selected in enumerate(pair_selected_variable)
        if selected >= 0
    ]
    diagnostic_graphs = np.stack([h_by_graph[graph] for graph in GRAPH_IDS])
    diagnostics = {
        "source_batch_uuid": np.asarray([SOURCE_UUID]),
        "source_contract": np.asarray([SOURCE_CONTRACT]),
        "source_seed_namespace": np.asarray([SOURCE_NAMESPACE]),
        "source_graph_input_kind": np.asarray(["admitted_source"]),
        "source_graph_id": np.asarray(GRAPH_IDS, dtype=np.int64),
        "source_graph_seed": np.arange(101, 107, dtype=np.int64),
        "source_profile_index": np.ones(6, dtype=np.int64),
        "source_graph_index": np.arange(6, dtype=np.int64),
        "source_constructor_uuid": np.asarray(["fake-constructor"] * 6),
        "source_constructor_path": np.asarray(["workspace/fake/constructions.json"] * 6),
        "source_constructor_matrix_index": np.arange(6, dtype=np.int64),
        "source_constructor_attempt_j": np.zeros(6, dtype=np.int64),
        "source_constructor_seed": np.arange(201, 207, dtype=np.int64),
        "source_constructor_graph_id": np.asarray(GRAPH_IDS, dtype=np.int64),
        "H_deep": diagnostic_graphs,
        "original_prior": original_prior,
        "pair_index": np.asarray(pair_index, dtype=np.int64),
        "pair_graph_id": np.asarray(pair_graph_id, dtype=np.int64),
        "pair_syndrome": np.stack(pair_syndrome),
        "pair_truth": np.stack(pair_truth),
        "pair_baseline_call_index": np.asarray(pair_baseline_call_index, dtype=np.int64),
        "pair_candidate_selected_call_index": np.asarray(
            pair_candidate_selected_call_index, dtype=np.int64),
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
        "call_syndrome_ok_reported_available": np.ones(492, dtype=np.bool_),
        "call_raw_vector_index": np.asarray(call_raw_vector_index, dtype=np.int64),
        "raw_vector_call_index": raw_vector_call_index,
        "raw_x_hat": raw_x_hat,
        "belief_call_index": np.asarray(failed_baseline_ids, dtype=np.int64),
        "baseline_failure_belief_provenance": np.asarray(
            ["CHECK_UPDATED"] * len(failed_baseline_ids)),
        "baseline_failure_beliefs": np.zeros((50, 128, 32), dtype=np.float64),
        "selector_call_index": np.asarray(failed_baseline_ids, dtype=np.int64),
        "selector_selected_column": np.zeros(50, dtype=np.int64),
        "branch_score_call_index": np.asarray(branch_score_call_index, dtype=np.int64),
        "branch_score_branch_index": np.asarray(branch_score_branch_index, dtype=np.int64),
        "branch_score_guess_symbol": np.asarray(branch_score_guess_symbol, dtype=np.int64),
        "branch_score_original_prior": np.asarray(branch_score_original_prior, dtype=np.float64),
        "branch_score_available": np.asarray(branch_score_available, dtype=np.bool_),
        "branch_score_syndrome_valid": np.asarray(branch_score_syndrome_valid, dtype=np.bool_),
    }
    parent_identity = {
        "batch_uuid": PARENT_UUID, "contract": PARENT_CONTRACT,
        "seed_namespace": PARENT_NAMESPACE, "status": "COMPLETE",
        "classification": "MECHANISM_SIGNAL",
    }
    source_identity = {
        "batch_uuid": SOURCE_UUID, "contract": SOURCE_CONTRACT,
        "seed_namespace": SOURCE_NAMESPACE, "graph_input_kind": "admitted_source",
    }
    manifest = {**parent_identity, "source_identity": source_identity}
    summary = {
        **parent_identity, "completed_pairs": 192,
        "baseline_exact": 142, "selected_exact": 156,
    }
    return {"manifest": manifest, "summary": summary, "diagnostics": diagnostics}


def _adapters(source: dict, *, mismatch_vector_call: int | None = None,
              mismatch_belief_call: int | None = None,
              mismatch_path: str = "reference",
              wall_over_call: int | None = None,
              rss_over_call: int | None = None) -> dict:
    diagnostics = source["diagnostics"]
    call_ids = [int(value) for value in diagnostics["call_index"]]
    id_to_off = {call_id: pos for pos, call_id in enumerate(call_ids)}
    pair_pos = {int(value): pos for pos, value in enumerate(diagnostics["pair_index"])}
    graph_pos = {int(value): pos for pos, value in enumerate(diagnostics["source_graph_id"])}
    raw_by_call = {
        int(call_id): np.asarray(vector, dtype=np.uint8)
        for call_id, vector in zip(diagnostics["raw_vector_call_index"], diagnostics["raw_x_hat"])
    }
    belief_by_call = {
        int(call_id): np.asarray(beliefs, dtype=np.float64)
        for call_id, beliefs in zip(diagnostics["belief_call_index"],
                                    diagnostics["baseline_failure_beliefs"])
    }
    state = {
        "source_reads": 0, "decoder_calls": 0,
        "cursor": {"reference": 0, "candidate": 0},
        "clock": 0.0, "rss_over": False, "events": [],
    }

    def source_reader():
        state["source_reads"] += 1
        return source

    def make_decoder(path: str):
        def decoder(h, prior, syndrome, *, max_iter, damping_alpha,
                    warm_beliefs, field):
            offset = state["cursor"][path]
            call_id = call_ids[offset]
            state["cursor"][path] += 1
            state["decoder_calls"] += 1
            state["events"].append((call_id, path))
            call_off = id_to_off[call_id]
            pair_id = int(diagnostics["call_pair_index"][call_off])
            graph_id = int(diagnostics["call_graph_id"][call_off])
            role = str(diagnostics["call_role"][call_off])
            expected_h = diagnostics["H_deep"][graph_pos[graph_id]]
            expected_syndrome = diagnostics["pair_syndrome"][pair_pos[pair_id]]
            expected_prior = np.asarray(diagnostics["original_prior"], dtype=np.float64).copy()
            if role == "soft_prior":
                selected = int(diagnostics["call_selected_variable"][call_off])
                guess = int(diagnostics["call_guess_symbol"][call_off])
                expected_prior[selected, :] = 0.0
                expected_prior[selected, guess] = 1.0
            assert max_iter == 90
            assert damping_alpha == 1.0
            assert warm_beliefs is None
            assert field is None
            np.testing.assert_array_equal(h, expected_h)
            np.testing.assert_array_equal(syndrome, expected_syndrome)
            np.testing.assert_array_equal(prior, expected_prior)

            vector = raw_by_call[call_id].copy()
            if mismatch_vector_call == call_id and mismatch_path == path:
                vector[0] = (int(vector[0]) + 1) % 32
            beliefs = belief_by_call.get(call_id, np.zeros((128, 32), dtype=np.float64)).copy()
            if mismatch_belief_call == call_id and mismatch_path == path:
                beliefs[0, 0] = 1.0
            if wall_over_call == call_id:
                state["clock"] += probe.WALL_CAP_S + 1.0
            else:
                state["clock"] += 0.0001
            if rss_over_call == call_id:
                state["rss_over"] = True
            valid = bool(diagnostics["call_syndrome_valid"][call_off])
            return SimpleNamespace(
                x_hat=vector,
                iterations=int(diagnostics["call_iterations"][call_off]),
                status=str(diagnostics["call_decoder_status"][call_off]),
                syndrome_ok=valid,
                runtime_s=0.001 if path == "reference" else 0.0015,
                final_beliefs=beliefs,
            )
        return decoder

    def now():
        return state["clock"]

    def rss_fn():
        return (probe.RSS_CAP_BYTES + 1) if state["rss_over"] else 50_000_000

    return {
        "source_reader": source_reader,
        "reference_decoder": make_decoder("reference"),
        "candidate_decoder": make_decoder("candidate"),
        "now": now, "rss_fn": rss_fn, "state": state,
        "call_ids": call_ids,
    }


def _run(adapters: dict, repo_root: Path):
    return probe.execute_batch(
        source_reader=adapters["source_reader"],
        reference_decoder=adapters["reference_decoder"],
        candidate_decoder=adapters["candidate_decoder"],
        out_root=probe.OUT_ROOT_RELATIVE, repo_root=repo_root,
        now=adapters["now"], rss_fn=adapters["rss_fn"],
        command="fake-only full efficiency test",
    )


def _null_full_totals(summary: dict) -> None:
    for key in (
        "baseline_calls_per_path", "branch_calls_per_path", "iterations_by_path",
        "decoder_runtime_s_by_path", "outer_wall_s_by_path", "control_wall_s",
        "candidate_pipeline_wall_s", "baseline_exact_by_path", "selected_exact_by_path",
        "selected_valid_wrong_by_path", "raw_branch_valid_wrong_by_path",
        "selected_pointer_matches_source_by_path", "source_roundtrip_matches",
        "paired_matches", "max_final_belief_abs_diff", "per_graph",
        "paired_class_counts", "delta_exact_by_path",
    ):
        assert summary[key] is None, key


def test_t0_and_dry_run_are_callback_free_and_leave_the_official_root_absent(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(probe, "_bind_production",
                        lambda *args, **kwargs: pytest.fail("production binding called"))
    t0 = probe.verify_t0(repo_root=tmp_path)
    dry = probe.dry_run(repo_root=tmp_path)
    assert (t0["source_reads"], t0["decoder_calls"], t0["sampler_calls"], t0["writes"]) == (
        0, 0, 0, 0)
    assert (dry["source_reads"], dry["decoder_calls"], dry["sampler_calls"], dry["writes"]) == (
        0, 0, 0, 0)
    assert not (tmp_path / probe.OUT_ROOT_RELATIVE).exists()


def test_full_fake_984_call_replay_preserves_maps_choices_and_cost_roles(tmp_path: Path):
    source = _fake_source()
    adapters = _adapters(source)
    result = _run(adapters, tmp_path)
    summary = result["summary"]

    assert result["status"] == "FULL_SOFTPRIOR_IMPLEMENTATION_MATCH"
    assert adapters["state"]["source_reads"] == result["source_reads"] == 1
    assert adapters["state"]["decoder_calls"] == result["decoder_calls"] == 984
    assert summary["source_pairs"] == 192
    assert summary["source_calls"] == 492
    assert summary["calls_complete"] == 984
    assert summary["paired_call_ids_complete"] == summary["paired_matches"] == 492
    assert summary["source_roundtrip_matches"] == 984
    assert summary["baseline_calls_per_path"] == {"reference": 192, "candidate": 192}
    assert summary["branch_calls_per_path"] == {"reference": 300, "candidate": 300}
    assert summary["baseline_exact_by_path"] == {"reference": 142, "candidate": 142}
    assert summary["selected_exact_by_path"] == {"reference": 156, "candidate": 156}
    assert summary["selected_valid_wrong_by_path"] == {"reference": 9, "candidate": 9}
    assert summary["raw_branch_valid_wrong_by_path"] == {"reference": 115, "candidate": 115}
    assert summary["selected_pointer_matches_source_by_path"] == {
        "reference": 192, "candidate": 192}
    assert summary["control_wall_s"] > 0.0
    assert summary["candidate_pipeline_wall_s"] > summary["control_wall_s"]
    assert summary["candidate_pipeline_to_control_wall_ratio"] == pytest.approx(2.5625)
    assert summary["timing_by_path"]["reference"]["by_role"]["baseline"]["calls"] == 192
    assert summary["timing_by_path"]["candidate"]["by_role"]["baseline"]["calls"] == 192
    assert summary["public_syndrome_bits_per_method"] == 49_920
    assert summary["internal_branch_disclosure_bits"] == 0
    assert summary["replay_new_disclosure_bits"] == 0
    assert summary["verification_status"] == "NOT_IMPLEMENTED"
    assert summary["undetected_status"] == "NOT_MEASURED"
    assert len(result["frame_records"]) == 192
    assert len(result["call_records"]) == 984

    expected_events = []
    for call_id in adapters["call_ids"]:
        order = ("reference", "candidate") if call_id % 2 == 0 else (
            "candidate", "reference")
        expected_events.extend((call_id, path) for path in order)
    assert adapters["state"]["events"] == expected_events
    assert all(row["source_vector_match"] and row["source_iterations_match"]
               and row["source_status_match"] and row["source_syndrome_match"]
               and row["pair_vector_match"] and row["pair_iterations_match"]
               and row["pair_status_match"] and row["pair_belief_match"]
               for row in result["call_records"])

    frames_by_id = {int(row["pair_index"]): row for row in result["frame_records"]}
    diagnostics = source["diagnostics"]
    pair_pos = {int(pair_id): pos for pos, pair_id in enumerate(diagnostics["pair_index"])}
    call_off = {int(call_id): pos for pos, call_id in enumerate(diagnostics["call_index"])}
    wrong_selected = [row for row in result["frame_records"]
                      if row["selected_valid_wrong_reference"]]
    assert len(wrong_selected) == 9
    for frame in wrong_selected:
        assert frame["reference_selected_branch_index"] == 0
        pair_id = int(frame["pair_index"])
        truth = diagnostics["pair_truth"][pair_pos[pair_id]]
        branch2_call = next(
            int(diagnostics["call_index"][off])
            for off, p in enumerate(diagnostics["call_pair_index"])
            if int(p) == pair_id and int(diagnostics["call_branch_index"][off]) == 2)
        raw_pos = int(diagnostics["call_raw_vector_index"][call_off[branch2_call]])
        np.testing.assert_array_equal(diagnostics["raw_x_hat"][raw_pos], truth)
    fallback = [row for row in result["frame_records"]
                if not row["baseline_syndrome_valid"]
                and row["reference_selected_branch_index"] is None]
    assert len(fallback) == 27
    assert all(row["reference_selected_call_index"] == row["baseline_call_index"]
               for row in fallback)

    expected_path_by_id = {
        (int(row["source_call_index"]), str(row["path"])): (int(row["pair_index"]),
                                                              int(row["path_code"]))
        for row in result["call_records"]
    }
    with np.load(result["artifacts"]["outputs.npz"], allow_pickle=False) as archive:
        assert set(archive.files) == {"x_hat", "source_call_index", "pair_index", "path_code"}
        assert archive["x_hat"].dtype == np.uint8
        assert archive["x_hat"].shape == (984, 128)
        for vector, source_call, pair_id, path_code in zip(
                archive["x_hat"], archive["source_call_index"],
                archive["pair_index"], archive["path_code"]):
            matching = next(row for row in result["call_records"]
                            if int(row["source_call_index"]) == int(source_call)
                            and int(row["path_code"]) == int(path_code))
            assert int(matching["pair_index"]) == int(pair_id)
            raw_pos = int(diagnostics["call_raw_vector_index"][
                call_off[int(source_call)]])
            np.testing.assert_array_equal(vector, diagnostics["raw_x_hat"][raw_pos])
    assert result["first_pass_output_bytes"] <= probe.ARTIFACT_CAP_BYTES
    assert result["terminal_artifact_bytes"] <= probe.ARTIFACT_CAP_BYTES


@pytest.mark.parametrize("mutation", ["identity", "missing_branch"])
def test_source_identity_or_branch_coverage_mismatch_stops_before_decoder(
        tmp_path: Path, mutation: str):
    source = _fake_source()
    diagnostics = source["diagnostics"]
    if mutation == "identity":
        source["manifest"]["source_identity"]["batch_uuid"] = "wrong-source"
    else:
        branch_off = int(np.flatnonzero(diagnostics["call_role"] == "soft_prior")[0])
        diagnostics["call_branch_index"][branch_off] = 6
    adapters = _adapters(source)
    result = _run(adapters, tmp_path)
    assert result["status"] == "STOP"
    assert adapters["state"]["decoder_calls"] == result["decoder_calls"] == 0
    assert result["summary"]["source_reads"] == 1
    _null_full_totals(result["summary"])


def test_existing_output_root_refuses_before_all_callbacks(tmp_path: Path):
    output_root = tmp_path / probe.OUT_ROOT_RELATIVE
    output_root.mkdir(parents=True)
    calls = {"source": 0, "reference": 0, "candidate": 0}

    def forbidden(key):
        def callback(*args, **kwargs):
            calls[key] += 1
            raise AssertionError("callback should not run")
        return callback

    with pytest.raises(FileExistsError):
        probe.execute_batch(
            source_reader=forbidden("source"),
            reference_decoder=forbidden("reference"),
            candidate_decoder=forbidden("candidate"),
            out_root=probe.OUT_ROOT_RELATIVE, repo_root=tmp_path,
        )
    assert calls == {"source": 0, "reference": 0, "candidate": 0}


@pytest.mark.parametrize("mutation", ["pointer", "score", "selected_anchor"])
def test_full_run_selection_or_score_mismatch_stops_with_partial_totals_null(
        tmp_path: Path, mutation: str):
    source = _fake_source()
    diagnostics = source["diagnostics"]
    if mutation == "pointer":
        failed_pair_pos = int(np.flatnonzero(diagnostics["pair_selected_variable"] >= 0)[0])
        pair_id = int(diagnostics["pair_index"][failed_pair_pos])
        branch2_off = next(
            off for off, source_pair in enumerate(diagnostics["call_pair_index"])
            if int(source_pair) == pair_id and int(diagnostics["call_branch_index"][off]) == 2)
        diagnostics["pair_candidate_selected_call_index"][failed_pair_pos] = (
            diagnostics["call_index"][branch2_off])
    elif mutation == "score":
        diagnostics["branch_score_original_prior"][0] += 0.01
    else:
        pair_pos = 0  # a baseline-valid row; preserve its zero syndrome
        diagnostics["pair_truth"][pair_pos, 0] = 1
        diagnostics["pair_truth"][pair_pos, 1] = 1

    adapters = _adapters(source)
    result = _run(adapters, tmp_path)
    assert result["status"] == "STOP"
    assert adapters["state"]["decoder_calls"] == result["decoder_calls"] == 984
    assert len(result["call_records"]) == 984
    assert result["summary"]["source_pairs"] == 192
    assert result["summary"]["source_calls"] == 492
    _null_full_totals(result["summary"])
    reasons = " ".join(result["summary"]["stop_reasons"])
    if mutation == "pointer":
        assert "pointer" in reasons or "score" in reasons
    elif mutation == "score":
        assert "score" in reasons
    else:
        assert "C142_K156" in reasons


@pytest.mark.parametrize("mismatch", ["vector", "belief"])
def test_decoder_vector_or_baseline_belief_mismatch_retains_observations(
        tmp_path: Path, mismatch: str):
    source = _fake_source()
    diagnostics = source["diagnostics"]
    if mismatch == "vector":
        mismatch_id = int(diagnostics["call_index"][0])
        adapters = _adapters(source, mismatch_vector_call=mismatch_id)
    else:
        mismatch_id = int(diagnostics["belief_call_index"][0])
        adapters = _adapters(source, mismatch_belief_call=mismatch_id)
    result = _run(adapters, tmp_path)
    assert result["status"] == "STOP"
    assert 0 < result["decoder_calls"] < 984
    assert len(result["call_records"]) == result["decoder_calls"]
    _null_full_totals(result["summary"])
    with np.load(result["artifacts"]["outputs.npz"], allow_pickle=False) as archive:
        assert len(archive["x_hat"]) == result["decoder_calls"]
        assert len(archive["source_call_index"]) == len(archive["x_hat"])
        if mismatch == "vector":
            raw_pos = int(diagnostics["call_raw_vector_index"][0])
            assert not np.array_equal(archive["x_hat"][0], diagnostics["raw_x_hat"][raw_pos])
        else:
            for vector, source_call in zip(archive["x_hat"], archive["source_call_index"]):
                call_off = int(np.flatnonzero(
                    diagnostics["call_index"] == int(source_call))[0])
                raw_pos = int(diagnostics["call_raw_vector_index"][call_off])
                np.testing.assert_array_equal(vector, diagnostics["raw_x_hat"][raw_pos])


@pytest.mark.parametrize("cap", ["wall", "rss"])
def test_resource_cap_stops_after_call_and_retains_returned_vector(
        tmp_path: Path, cap: str):
    source = _fake_source()
    first_call = int(source["diagnostics"]["call_index"][0])
    adapters = (_adapters(source, wall_over_call=first_call) if cap == "wall"
                else _adapters(source, rss_over_call=first_call))
    result = _run(adapters, tmp_path)
    assert result["status"] == "INCOMPLETE"
    assert result["decoder_calls"] == 1
    assert len(result["call_records"]) == 1
    assert result["summary"]["calls_complete"] == 1
    assert result["summary"]["source_pairs"] == 192
    assert result["summary"]["source_calls"] == 492
    assert result["summary"]["stop_reasons"]
    _null_full_totals(result["summary"])
    with np.load(result["artifacts"]["outputs.npz"], allow_pickle=False) as archive:
        assert archive["x_hat"].shape == (1, 128)


def test_artifact_cap_marks_complete_fake_batch_incomplete(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(probe, "ARTIFACT_CAP_BYTES", 1)
    source = _fake_source()
    adapters = _adapters(source)
    result = _run(adapters, tmp_path)
    assert result["status"] == "INCOMPLETE"
    assert result["decoder_calls"] == 984
    assert result["summary"]["paired_call_ids_complete"] == 492
    assert "artifact_cap" in result["summary"]["stop_reasons"]
    _null_full_totals(result["summary"])
    assert result["terminal_artifact_bytes"] > 1


def test_linux_rss_high_water_is_converted_from_kib_to_bytes(
        monkeypatch: pytest.MonkeyPatch):
    import resource

    monkeypatch.setattr(resource, "getrusage",
                        lambda who: SimpleNamespace(ru_maxrss=33072))
    assert probe._rss_bytes() == 33_865_728
