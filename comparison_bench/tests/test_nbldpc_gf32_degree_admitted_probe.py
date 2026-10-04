"""Fake-only tests for reusing the accepted degree-construction canary."""
from __future__ import annotations

import csv
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_degree_admitted_probe as probe
from comparison_bench.cli import nbldpc_gf32_degree_probe as degree_probe
from comparison_bench.formal_ir import nbldpc_gf32_label_alignment as alignment
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from comparison_bench.formal_ir import v72p2d10_mixed_degree_l1 as d10


def _fake_h(matrix_index: int) -> np.ndarray:
    """A shaped lineage marker, not a profile-valid research matrix."""
    h = np.zeros((52, 128), dtype=np.uint8)
    for row in range(52):
        h[row, row] = 1 + ((row + matrix_index) % 31)
    return h


def _fake_source_doc() -> dict:
    """Build a canary-shaped document with the frozen 3905 j=1 matrix join."""
    matrices: list[dict] = []
    attempts: list[dict] = []
    groups: list[dict] = []
    next_matrix_index = 0

    def admitted_attempt(graph_id: int, profile_id: str, attempt_j: int,
                         construction_seed: int) -> int:
        nonlocal next_matrix_index
        matrix_index = next_matrix_index
        next_matrix_index += 1
        profile = degree_probe.PROFILES[profile_id]
        edge_count = int(profile["edge_count"])
        constructor_record = {
            "profile_id": profile_id,
            "graph_seed": construction_seed,
            "n": 128,
            "m": 52,
            "E": edge_count,
            "edges": [[0, 0]] * edge_count,
            "coefficients": [1] * edge_count,
            "status": "ok",
            "admitted": True,
        }
        preflight = {
            "profile_id": profile_id,
            "graph_seed": construction_seed,
            "checks": {"fake_admitted": True},
        }
        matrices.append({
            "matrix_index": matrix_index,
            "graph_id": graph_id,
            "profile_id": profile_id,
            "attempt_j": attempt_j,
            "construction_seed": construction_seed,
            "H": _fake_h(matrix_index),
            "structure": {"fake_matrix_index": matrix_index},
        })
        attempts.append({
            "matrix_index": matrix_index,
            "graph_id": graph_id,
            "profile_id": profile_id,
            "attempt_j": attempt_j,
            "construction_seed": construction_seed,
            "status": "admitted",
            "admitted": True,
            "constructor_record": constructor_record,
            "preflight": preflight,
        })
        return matrix_index

    def failed_attempt(graph_id: int, profile_id: str, attempt_j: int,
                       construction_seed: int) -> None:
        attempts.append({
            "matrix_index": None,
            "graph_id": graph_id,
            "profile_id": profile_id,
            "attempt_j": attempt_j,
            "construction_seed": construction_seed,
            "status": "construction_failed",
            "admitted": False,
        })

    for graph_id in degree_probe.GRAPH_SEEDS:
        if graph_id != 2026093905:
            selected = {
                profile_id: admitted_attempt(
                    graph_id, profile_id, 0, graph_id)
                for profile_id in degree_probe.PROFILE_ORDER
            }
            selected_j, selected_seed = 0, graph_id
        else:
            # Index 8 is an unselected j=0 control. The candidate's j=0
            # construction fails; the selected common pair is j=1 at 9/10.
            admitted_attempt(graph_id, "control", 0, graph_id)
            failed_attempt(graph_id, "candidate", 0, graph_id)
            selected = {
                profile_id: admitted_attempt(
                    graph_id, profile_id, 1, 2560859716)
                for profile_id in degree_probe.PROFILE_ORDER
            }
            selected_j, selected_seed = 1, 2560859716
        groups.append({
            "graph_id": graph_id,
            "status": "SELECTED",
            "selected_matrix_indices": selected,
            "selected_attempt_j": selected_j,
            "selected_seed": selected_seed,
        })

    return {
        "batch_uuid": probe.SOURCE_UUID,
        "contract": probe.SOURCE_CONTRACT,
        "seed_namespace": probe.SOURCE_NAMESPACE,
        "terminal_status": "COMPLETE",
        "classification": "CONSTRUCTION_FEASIBLE",
        "complete_all_groups": True,
        "stop_reason": None,
        "matrix_count": len(matrices),
        "matrices": matrices,
        "attempts": attempts,
        "groups": groups,
    }


def test_selected_graphs_joins_matrix_index_and_keeps_logical_and_source_seeds():
    doc = _fake_source_doc()

    selected = probe.selected_graphs(doc)

    assert set(selected) == {
        (graph_id, profile_id)
        for graph_id in degree_probe.GRAPH_SEEDS
        for profile_id in degree_probe.PROFILE_ORDER
    }
    control = selected[(2026093905, "control")]
    candidate = selected[(2026093905, "candidate")]
    assert control["source_matrix_index"] == 9
    assert candidate["source_matrix_index"] == 10
    assert control["source_attempt_j"] == candidate["source_attempt_j"] == 1
    assert control["source_construction_seed"] == 2560859716
    assert candidate["source_construction_seed"] == 2560859716
    assert control["source_graph_id"] == candidate["source_graph_id"] == 2026093905
    assert control["graph_seed"] == candidate["graph_seed"] == 2026093905
    assert control["H"][0, 0] == _fake_h(9)[0, 0]
    assert candidate["H"][0, 0] == _fake_h(10)[0, 0]
    assert not np.array_equal(control["H"], candidate["H"])
    # Matrix 8 is the unselected control j=0 record, not graph 3905's input.
    assert control["source_matrix_index"] != 8
    assert control["H"][0, 0] != _fake_h(8)[0, 0]
    assert control["source_uuid"] == probe.SOURCE_UUID
    assert control["source_path"] == probe.SOURCE_JSON_RELATIVE.as_posix()


def test_selected_graphs_rejects_a_broken_matrix_attempt_join():
    doc = _fake_source_doc()
    selected_control_attempt = next(
        row for row in doc["attempts"] if row["matrix_index"] == 9)
    selected_control_attempt["construction_seed"] += 1

    with pytest.raises(ValueError, match="provenance mismatch"):
        probe.selected_graphs(doc)


def test_dry_run_does_not_read_source_bind_production_or_create_root(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = tmp_path / "repo"
    (repo / "workspace").mkdir(parents=True)
    expected_root = repo / probe.OUT_ROOT_RELATIVE

    def forbidden(*args, **kwargs):
        raise AssertionError("dry-run touched a production/source binding")

    monkeypatch.setattr(probe, "_bind_production", forbidden)
    monkeypatch.setattr(probe, "_default_source_reader", forbidden)

    wrong_root = repo / "workspace" / "wrong-degree-admitted-root"
    with pytest.raises(ValueError, match="out-root must equal frozen fresh root"):
        probe.dry_run(wrong_root, repo_root=repo)
    assert not wrong_root.exists()

    result = probe.dry_run(expected_root, repo_root=repo)

    assert result["status"] == "DRY_RUN"
    assert result["graph_input_kind"] == "admitted_source"
    assert result["source_reads"] == 0
    assert result["writes"] == 0
    assert result["artifact_reads"] == 0
    assert result["graph_build_calls"] == 0
    assert result["label_calls"] == 0
    assert result["decoder_calls"] == 0
    assert result["t0"] and all(result["t0"].values())
    assert not expected_root.exists()


def _fake_entry_callbacks(doc: dict, monkeypatch: pytest.MonkeyPatch):
    """Explicit source/profile/label/decode fakes for the real entry loop."""
    selected = probe.selected_graphs(doc)
    sampler_calls: list[tuple[int, np.ndarray]] = []
    decoder_calls: list[dict] = []
    preflight_calls: list[tuple[str, int]] = []
    candidate_calls: list[tuple[str, int, np.ndarray]] = []
    real_sampler = degree_probe.prior_runner.sample_error

    def sampler_spy(seed: int, pmf: np.ndarray, width: int = 128):
        truth = real_sampler(seed, pmf, width=width)
        sampler_calls.append((int(seed), np.asarray(truth).copy()))
        return truth

    monkeypatch.setattr(degree_probe.prior_runner, "sample_error", sampler_spy)

    def profile_preflight(profile: dict, graph: dict, graph_seed: int):
        profile_id = str(profile["profile_id"])
        assert graph["profile_id"] == profile_id
        assert graph["graph_seed"] == int(graph_seed)
        assert any(
            graph_seed == key[0] and profile_id == key[1]
            and np.array_equal(graph["H"], record["H"])
            for key, record in selected.items())
        preflight_calls.append((profile_id, int(graph_seed)))
        # Synthetic H arrays exercise identity and data flow only. This fake
        # callback is not evidence of profile/rank admission.
        return True, {"fake_profile": profile_id, "fake_graph_seed": int(graph_seed)}

    def candidate_builder(h: np.ndarray, pmf: np.ndarray, graph_seed: int):
        h = np.asarray(h, dtype=np.int64)
        matches = [
            (key, record) for key, record in selected.items()
            if key[0] == int(graph_seed) and np.array_equal(record["H"], h)
        ]
        assert len(matches) == 1
        (logical_seed, profile_id), _ = matches[0]
        candidate_calls.append((profile_id, logical_seed, h.copy()))
        onepass_labels = np.ones(128, dtype=np.int64)
        onepass_labels[0] = 2
        deep_labels = np.ones(128, dtype=np.int64)
        deep_labels[1] = 3
        onepass = alignment.scale_columns(h, onepass_labels)
        deep = alignment.scale_columns(h, deep_labels)
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
        assert np.array_equal(np.asarray(pmf),
                              degree_probe.search_runner.shape_pmf_grid()[0]["pmf"])
        return onepass, deep, diagnostics

    def truth_blind_decoder(arm: str):
        def decode(h: np.ndarray, prior: np.ndarray, syndrome: np.ndarray):
            h = np.asarray(h, dtype=np.int64)
            prior = np.asarray(prior, dtype=np.float64)
            syndrome = np.asarray(syndrome, dtype=np.int64)
            decoder_calls.append({
                "arm": arm, "H": h.copy(), "prior": prior.copy(),
                "syndrome": syndrome.copy(),
            })
            # The fake H is diagonal in its first 52 columns. Solve only those
            # coordinates; the 76 unobserved symbols are not given to decoder.
            raw = np.zeros(128, dtype=np.int64)
            for row in range(52):
                coefficient = int(h[row, row])
                inverse = next(
                    value for value in range(1, 32)
                    if layout.gf32_mul(coefficient, value) == 1)
                raw[row] = layout.gf32_mul(int(syndrome[row]), inverse)
            return SimpleNamespace(
                x_hat=raw,
                syndrome_ok=bool(layout.syndrome_ok(h, raw, syndrome)),
                iterations=4,
                status="fake_valid_partial_word",
            )
        return decode

    return {
        "decode_fns": {
            "control": truth_blind_decoder("control"),
            "candidate": truth_blind_decoder("candidate"),
        },
        "candidate_builder": candidate_builder,
        "profile_preflight_fn": profile_preflight,
        "sampler_calls": sampler_calls,
        "decoder_calls": decoder_calls,
        "preflight_calls": preflight_calls,
        "candidate_calls": candidate_calls,
        "selected": selected,
    }


def _diagnostic_arrays(root: Path) -> dict[str, np.ndarray]:
    with np.load(root / "diagnostics.npz", allow_pickle=False) as loaded:
        return {name: loaded[name].copy() for name in loaded.files}


def test_fake_entry_runs_all_pairs_through_selected_source_and_rechecks_maps(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = tmp_path / "repo"
    (repo / "workspace").mkdir(parents=True)
    root_relative = probe.OUT_ROOT_RELATIVE
    source_doc = _fake_source_doc()
    calls = _fake_entry_callbacks(source_doc, monkeypatch)
    read_count = 0

    def source_reader():
        nonlocal read_count
        read_count += 1
        return source_doc

    summary = probe.execute_batch(
        out_root=root_relative,
        repo_root=repo,
        source_reader=source_reader,
        decode_fns=calls["decode_fns"],
        candidate_builder=calls["candidate_builder"],
        profile_preflight_fn=calls["profile_preflight_fn"],
        rss_fn=lambda: 0,
        command="fake admitted-source entry",
    )

    root = repo / root_relative
    assert summary["complete"] is True
    assert summary["terminal_status"] == "COMPLETE"
    assert summary["batch_uuid"] == probe.BATCH_UUID
    assert summary["contract"] == probe.CONTRACT
    assert summary["seed_namespace"] == probe.SEED_PREFIX
    assert summary["graph_input_kind"] == "admitted_source"
    assert read_count == 1
    assert len(calls["sampler_calls"]) == 192
    assert len({seed for seed, _ in calls["sampler_calls"]}) == 192
    assert len(calls["preflight_calls"]) == 12
    assert len(calls["candidate_calls"]) == 12
    assert len(calls["decoder_calls"]) == 384
    assert summary["attempted_decoder_calls"] == 384
    assert summary["attempted_frame_rows"] == 384
    assert summary["disclosed_syndrome_bits"] == 384 * degree_probe.SYNDROME_BITS
    assert summary["edge_update_proxy_is_measured_operations"] is False
    assert summary["profile_costs"]["control"]["graphs_loaded"] == 6
    assert summary["profile_costs"]["candidate"]["graphs_loaded"] == 6
    for profile_id in degree_probe.PROFILE_ORDER:
        costs = summary["profile_costs"][profile_id]
        assert costs["graphs_built"] == 0
        assert costs["graph_build_wall_s"] == 0
        assert costs["graph_load_wall_s"] >= 0
    expected_proxy = {
        profile_id: degree_probe.PROFILES[profile_id]["edge_count"]
        * summary["per_arm_outcomes"][profile_id]["iterations_sum"]
        for profile_id in degree_probe.PROFILE_ORDER
    }
    assert summary["edge_update_proxy"] == expected_proxy
    assert expected_proxy == {"control": 196608, "candidate": 294912}

    with (root / "frame_records.csv").open(
            newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    arrays = _diagnostic_arrays(root)
    assert len(rows) == 384
    assert arrays["pair_truth"].shape == (192, 128)
    assert arrays["pair_syndrome"].shape == (192, 2, 52)
    assert arrays["H_constructor"].shape == (12, 52, 128)
    assert arrays["H_deep"].shape == (12, 52, 128)
    assert arrays["raw_x_hat"].shape == (384, 128)
    assert arrays["call_vector_index"].tolist() == list(range(384))
    assert arrays["vector_call_index"].tolist() == list(range(384))
    assert arrays["batch_uuid"].tolist() == [probe.BATCH_UUID]
    assert arrays["contract"].tolist() == [probe.CONTRACT]
    assert arrays["seed_namespace"].tolist() == [probe.SEED_PREFIX]
    assert arrays["graph_input_kind"].tolist() == ["admitted_source"]
    assert arrays["constructor_source_uuid"].tolist() == [probe.SOURCE_UUID] * 12
    assert arrays["constructor_source_path"].tolist() == [
        probe.SOURCE_JSON_RELATIVE.as_posix()] * 12

    expected_source_indices = [
        calls["selected"][(graph_id, profile_id)]["source_matrix_index"]
        for profile_id in degree_probe.PROFILE_ORDER
        for graph_id in degree_probe.GRAPH_SEEDS
    ]
    assert arrays["constructor_source_matrix_index"].tolist() == expected_source_indices
    assert arrays["constructor_source_attempt_j"].tolist() == [
        calls["selected"][(graph_id, profile_id)]["source_attempt_j"]
        for profile_id in degree_probe.PROFILE_ORDER
        for graph_id in degree_probe.GRAPH_SEEDS
    ]
    assert arrays["constructor_source_seed"].tolist() == [
        calls["selected"][(graph_id, profile_id)]["source_construction_seed"]
        for profile_id in degree_probe.PROFILE_ORDER
        for graph_id in degree_probe.GRAPH_SEEDS
    ]
    assert arrays["constructor_source_graph_id"].tolist() == [
        graph_id for _profile_id in degree_probe.PROFILE_ORDER
        for graph_id in degree_probe.GRAPH_SEEDS
    ]
    for matrix_i, (profile_id, graph_id) in enumerate(
            (profile_id, graph_id)
            for profile_id in degree_probe.PROFILE_ORDER
            for graph_id in degree_probe.GRAPH_SEEDS):
        source_h = calls["selected"][(graph_id, profile_id)]["H"]
        assert np.array_equal(arrays["H_constructor"][matrix_i], source_h)
        assert not np.array_equal(arrays["H_constructor"][matrix_i],
                                  arrays["H_deep"][matrix_i])

    seed_plan = degree_probe.seed_plan(seed_prefix=probe.SEED_PREFIX)
    assert len(seed_plan) == 192
    assert len({seed for _, _, _, seed in seed_plan}) == 192
    assert [int(row["seed"]) for row in rows[::2]] == [
        int(row["seed"]) for row in rows[1::2]]
    wrong_by_profile = {profile_id: 0 for profile_id in degree_probe.PROFILE_ORDER}
    for pair_i, (graph_id, stream, frame, seed) in enumerate(seed_plan):
        truth = arrays["pair_truth"][pair_i]
        graph_index = int(arrays["pair_graph_index"][pair_i])
        assert int(arrays["pair_graph_seed"][pair_i]) == graph_id
        assert int(arrays["graph_seed"][graph_index]) == graph_id
        assert int(arrays["pair_stream"][pair_i]) == stream
        assert int(arrays["pair_frame"][pair_i]) == frame
        assert int(arrays["pair_seed"][pair_i]) == seed
        assert calls["sampler_calls"][pair_i][0] == seed
        assert np.array_equal(truth, calls["sampler_calls"][pair_i][1])
        pair_rows = rows[2 * pair_i:2 * pair_i + 2]
        expected_order = ("control", "candidate") if frame % 2 == 0 else (
            "candidate", "control")
        assert tuple(row["arm"] for row in pair_rows) == expected_order
        for arm_i, profile_id in enumerate(degree_probe.PROFILE_ORDER):
            deep_i = np.flatnonzero(
                (arrays["deep_profile_index"] == arm_i)
                & (arrays["deep_graph_index"] == graph_index))[0]
            deep_h = arrays["H_deep"][deep_i]
            expected_syndrome = np.asarray(
                layout.gf32_syndrome(deep_h, truth), dtype=np.uint8)
            assert np.array_equal(arrays["pair_syndrome"][pair_i, arm_i],
                                  expected_syndrome)
            call_i = 2 * pair_i + expected_order.index(profile_id)
            call = calls["decoder_calls"][call_i]
            row = rows[call_i]
            assert call["arm"] == profile_id
            assert np.array_equal(call["H"], deep_h)
            assert np.array_equal(call["syndrome"], expected_syndrome)
            assert "truth" not in call
            assert np.array_equal(
                call["prior"],
                np.tile(degree_probe.search_runner.shape_pmf_grid()[0]["pmf"],
                        (128, 1)))
            assert row["batch_uuid"] == probe.BATCH_UUID
            assert row["contract"] == probe.CONTRACT
            assert row["seed_namespace"] == probe.SEED_PREFIX
            assert row["source_uuid"] == probe.SOURCE_UUID
            assert row["source_path"] == probe.SOURCE_JSON_RELATIVE.as_posix()
            assert row["graph_input_kind"] == "admitted_source"
            expected_source = calls["selected"][(graph_id, profile_id)]
            assert int(row["source_matrix_index"]) == expected_source[
                "source_matrix_index"]
            assert int(row["source_attempt_j"]) == expected_source[
                "source_attempt_j"]
            assert int(row["source_construction_seed"]) == expected_source[
                "source_construction_seed"]
            assert int(row["source_graph_id"]) == graph_id
            assert int(arrays["call_index"][call_i]) == call_i
            assert int(arrays["call_pair_index"][call_i]) == pair_i
            assert int(arrays["call_profile_index"][call_i]) == arm_i
            assert int(arrays["call_graph_index"][call_i]) == graph_index
            vector_i = int(arrays["call_vector_index"][call_i])
            assert vector_i == call_i
            assert int(arrays["vector_call_index"][vector_i]) == call_i
            assert int(arrays["vector_pair_index"][vector_i]) == pair_i
            assert int(arrays["vector_profile_index"][vector_i]) == arm_i
            assert int(arrays["vector_graph_index"][vector_i]) == graph_index
            assert int(arrays["vector_stream"][vector_i]) == stream
            assert int(arrays["vector_frame"][vector_i]) == frame
            assert int(arrays["vector_seed"][vector_i]) == seed
            raw = arrays["raw_x_hat"][vector_i]
            raw_equal = bool(np.array_equal(raw, truth))
            syndrome_ok = bool(layout.syndrome_ok(deep_h, raw, expected_syndrome))
            assert (row["raw_symbols_equal"] == "True") is raw_equal
            assert (row["syndrome_accept"] == "True") is syndrome_ok
            assert (row["exact"] == "True") is (raw_equal and syndrome_ok)
            is_wrong = syndrome_ok and not raw_equal
            assert (row["syndrome_consistent_wrong"] == "True") is is_wrong
            wrong_by_profile[profile_id] += int(is_wrong)
    assert all(value > 0 for value in wrong_by_profile.values())
    for profile_id, expected_wrong in wrong_by_profile.items():
        outcome = summary["per_arm_outcomes"][profile_id]
        assert outcome["syndrome_valid_wrong"] == expected_wrong
        assert outcome["exact_and_syndrome"] + outcome["syndrome_valid_wrong"] \
            <= degree_probe.HOLDOUT_PAIRS

    with (root / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    assert manifest["batch_uuid"] == probe.BATCH_UUID
    assert manifest["contract"] == probe.CONTRACT
    assert manifest["seed_namespace"] == probe.SEED_PREFIX
    assert manifest["graph_input_kind"] == "admitted_source"
    assert len(manifest["source_provenance"]) == 12
    assert len(manifest["graph_diagnostics"]) == 12
    assert all(record["source_preflight"]["checks"]["fake_admitted"]
               for record in manifest["graph_diagnostics"])
    provenance_3905_control = next(
        record for record in manifest["source_provenance"]
        if record["graph_seed"] == 2026093905
        and record["profile_id"] == "control")
    assert provenance_3905_control["source_matrix_index"] == 9
    assert provenance_3905_control["source_attempt_j"] == 1
    assert provenance_3905_control["source_construction_seed"] == 2560859716
    log = (root / "EXPLORATION_LOG.md").read_text(encoding="utf-8")
    assert probe.BATCH_UUID in log
    assert probe.CONTRACT in log
    assert probe.SEED_PREFIX in log
    assert {"manifest.json", "frame_records.csv", "summary.json",
            "diagnostics.npz", "EXPLORATION_LOG.md"} == {
                path.name for path in root.iterdir()}


def test_invalid_source_stops_before_preflight_labels_and_decoders(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = tmp_path / "repo"
    (repo / "workspace").mkdir(parents=True)
    doc = _fake_source_doc()
    doc["batch_uuid"] = "wrong-source-uuid"
    calls = _fake_entry_callbacks(_fake_source_doc(), monkeypatch)
    source_reads = 0

    def source_reader():
        nonlocal source_reads
        source_reads += 1
        return doc

    summary = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE, repo_root=repo,
        source_reader=source_reader,
        decode_fns=calls["decode_fns"],
        candidate_builder=calls["candidate_builder"],
        profile_preflight_fn=calls["profile_preflight_fn"],
        rss_fn=lambda: 0,
        command="fake invalid source",
    )

    root = repo / probe.OUT_ROOT_RELATIVE
    assert source_reads == 1
    assert summary["terminal_status"] == "STOP"
    assert summary["complete"] is False
    assert summary["control_exact"] is None
    assert summary["candidate_exact"] is None
    assert summary["per_arm_outcomes"] is None
    assert calls["preflight_calls"] == []
    assert calls["candidate_calls"] == []
    assert calls["decoder_calls"] == []
    assert summary["attempted_decoder_calls"] == 0
    arrays = _diagnostic_arrays(root)
    assert arrays["H_constructor"].shape == (0, 52, 128)
    assert arrays["H_deep"].shape == (0, 52, 128)
    assert arrays["raw_x_hat"].shape == (0, 128)
    with (root / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    assert manifest["graph_input_kind"] == "admitted_source"
    assert any("source construction canary identity/status" in
               record.get("failure_reason", "")
               for record in manifest["graph_diagnostics"])
    assert {"manifest.json", "frame_records.csv", "summary.json",
            "diagnostics.npz", "EXPLORATION_LOG.md"} == {
                path.name for path in root.iterdir()}


def test_label_admission_stop_retains_sources_without_onepass_fallback(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = tmp_path / "repo"
    (repo / "workspace").mkdir(parents=True)
    doc = _fake_source_doc()
    calls = _fake_entry_callbacks(doc, monkeypatch)
    original_candidate_builder = calls["candidate_builder"]
    onepass_rows: list[np.ndarray] = []
    source_reads = 0

    def source_reader():
        nonlocal source_reads
        source_reads += 1
        return doc

    def reject_first_deep(h: np.ndarray, pmf: np.ndarray, graph_seed: int):
        onepass, _deep, diagnostics = original_candidate_builder(
            h, pmf, graph_seed)
        onepass_rows.append(onepass.copy())
        rejected = dict(diagnostics)
        rejected["deep_candidate_admitted"] = False
        return onepass, None, rejected

    summary = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE, repo_root=repo,
        source_reader=source_reader,
        decode_fns=calls["decode_fns"],
        candidate_builder=reject_first_deep,
        profile_preflight_fn=calls["profile_preflight_fn"],
        rss_fn=lambda: 0,
        command="fake deep-label admission stop",
    )

    root = repo / probe.OUT_ROOT_RELATIVE
    assert source_reads == 1
    assert summary["terminal_status"] == "STOP"
    assert summary["complete"] is False
    assert summary["control_exact"] is None
    assert summary["candidate_exact"] is None
    assert summary["per_arm_outcomes"] is None
    assert len(calls["preflight_calls"]) == 12
    assert len(calls["candidate_calls"]) == 1
    assert len(onepass_rows) == 1
    assert calls["decoder_calls"] == []
    assert summary["attempted_decoder_calls"] == 0
    arrays = _diagnostic_arrays(root)
    assert arrays["H_constructor"].shape == (12, 52, 128)
    assert arrays["H_deep"].shape == (0, 52, 128)
    assert arrays["pair_truth"].shape == (0, 128)
    assert arrays["raw_x_hat"].shape == (0, 128)
    with (root / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    assert len(manifest["source_provenance"]) == 12
    assert manifest["candidate_diagnostics"][0]["admitted"] is False
    assert manifest["candidate_diagnostics"][0]["checks"][
        "deep_present_and_shaped"] is False
    assert {"manifest.json", "frame_records.csv", "summary.json",
            "diagnostics.npz", "EXPLORATION_LOG.md"} == {
                path.name for path in root.iterdir()}


def test_source_mode_rss_stop_retains_first_returned_vector_and_provenance(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = tmp_path / "repo"
    (repo / "workspace").mkdir(parents=True)
    doc = _fake_source_doc()
    calls = _fake_entry_callbacks(doc, monkeypatch)
    control_decoder = calls["decode_fns"]["control"]
    decoder_returned = False
    monitor_error_sent = False
    source_reads = 0

    def source_reader():
        nonlocal source_reads
        source_reads += 1
        return doc

    def first_arm_then_monitor_fails(h: np.ndarray, prior: np.ndarray,
                                    syndrome: np.ndarray):
        nonlocal decoder_returned
        result = control_decoder(h, prior, syndrome)
        decoder_returned = True
        return result

    def stateful_rss():
        nonlocal monitor_error_sent
        if decoder_returned and not monitor_error_sent:
            monitor_error_sent = True
            raise OSError("injected source-mode RSS failure")
        return 0

    summary = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE,
        repo_root=repo,
        source_reader=source_reader,
        decode_fns={"control": first_arm_then_monitor_fails,
                    "candidate": calls["decode_fns"]["candidate"]},
        candidate_builder=calls["candidate_builder"],
        profile_preflight_fn=calls["profile_preflight_fn"],
        rss_fn=stateful_rss,
        command="fake source-mode RSS STOP",
    )

    root = repo / probe.OUT_ROOT_RELATIVE
    assert source_reads == 1
    assert summary["terminal_status"] == "STOP"
    assert summary["complete"] is False
    assert summary["control_exact"] is None
    assert summary["candidate_exact"] is None
    assert summary["per_arm_outcomes"] is None
    assert summary["attempted_decoder_calls"] == 1
    assert len(calls["decoder_calls"]) == 1
    assert summary["resource_stop_markers"] == [
        "rss_monitor_exception:OSError:injected source-mode RSS failure"]
    arrays = _diagnostic_arrays(root)
    assert arrays["H_constructor"].shape == (12, 52, 128)
    assert arrays["constructor_source_matrix_index"].shape == (12,)
    assert arrays["constructor_source_uuid"].tolist() == [probe.SOURCE_UUID] * 12
    assert arrays["call_vector_index"].tolist() == [0]
    assert arrays["vector_call_index"].tolist() == [0]
    assert arrays["vector_pair_index"].tolist() == [0]
    assert arrays["raw_x_hat"].shape == (1, 128)
    with (root / "frame_records.csv").open(
            newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert rows[0]["raw_vector_saved"] == "True"
    assert rows[0]["status"] == "resource_abort"
    assert rows[0]["source_uuid"] == probe.SOURCE_UUID
    assert "rss_monitor_exception" in rows[0]["failure_reason"]
    with (root / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    assert len(manifest["source_provenance"]) == 12
    assert {"manifest.json", "frame_records.csv", "summary.json",
            "diagnostics.npz", "EXPLORATION_LOG.md"} == {
                path.name for path in root.iterdir()}
