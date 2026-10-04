"""Fake-only tests for the fixed-source GF(32) endpoint ablation."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli.probes_closed import nbldpc_gf32_degree_admitted_probe as admitted
from comparison_bench.cli.probes_closed import nbldpc_gf32_degree_probe as degree
from comparison_bench.cli.probes_closed import nbldpc_gf32_endpoint_ablation_probe as probe
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout


def _profile_matrix(profile: str, graph_index: int, label_shift: int) -> np.ndarray:
    """Make a shaped, profile-correct fake matrix; it is not research evidence."""
    h = np.zeros((52, 128), dtype=np.uint8)
    degree_v = 2 if profile == "control" else 3
    row_target = ([4] * 4 + [5] * 48 if profile == "control"
                  else [7] * 32 + [8] * 20)

    def put(row: int, col: int) -> None:
        h[row, col] = ((row * 7 + col * 11 + graph_index * 3
                        + label_shift) % 31) + 1

    # A row cycle gives connected fake support. Extra cyclic sockets produce
    # the frozen check-degree histograms while every column has degree dv.
    for row in range(52):
        for offset in range(min(degree_v, 3)):
            put((row + offset) % 52, row)
    used_columns = 52
    extra_edges = 128 * degree_v - 52 * min(degree_v, 3)
    socket_rows = [edge % 52 for edge in range(extra_edges)]
    for col in range(used_columns, 128):
        slot = col - used_columns
        for offset in range(degree_v):
            put(socket_rows[slot * degree_v + offset], col)

    assert np.all(np.count_nonzero(h, axis=0) == degree_v)
    assert sorted(np.count_nonzero(h, axis=1).tolist()) == row_target
    return h


def _fake_source_arrays() -> dict[str, np.ndarray]:
    """Return an NPZ-shaped source mapping with intentionally shuffled pairs."""
    graph_seeds = np.asarray(degree.GRAPH_SEEDS, dtype=np.int64)
    graph_index = {int(seed): i for i, seed in enumerate(graph_seeds)}
    profile_order = np.asarray(degree.PROFILE_ORDER, dtype="<U9")

    constructor: list[np.ndarray] = []
    deep: list[np.ndarray] = []
    constructor_profile_index: list[int] = []
    constructor_graph_index: list[int] = []
    deep_profile_index: list[int] = []
    deep_graph_index: list[int] = []
    source_matrix_index: list[int] = []
    source_attempt_j: list[int] = []
    source_seed: list[int] = []
    source_graph_id: list[int] = []
    source_uuid: list[str] = []
    source_path: list[str] = []

    # The real source matrices are stored profile-major, then graph-major.
    # Candidate source indices retain the construction-canary's selected joins.
    selected_index = {
        "control": [0, 2, 4, 6, 9, 11],
        "candidate": [1, 3, 5, 7, 10, 12],
    }
    selected_j = [0, 0, 0, 0, 1, 0]
    construction_seeds = [*degree.GRAPH_SEEDS[:4], 2560859716,
                          degree.GRAPH_SEEDS[5]]
    for profile_i, profile in enumerate(degree.PROFILE_ORDER):
        for graph_i, graph_id in enumerate(degree.GRAPH_SEEDS):
            h0 = _profile_matrix(profile, graph_i, label_shift=0)
            h1 = _profile_matrix(profile, graph_i, label_shift=1)
            constructor.append(h0)
            deep.append(h1)
            constructor_profile_index.append(profile_i)
            constructor_graph_index.append(graph_i)
            deep_profile_index.append(profile_i)
            deep_graph_index.append(graph_i)
            source_matrix_index.append(selected_index[profile][graph_i])
            source_attempt_j.append(selected_j[graph_i])
            source_seed.append(construction_seeds[graph_i])
            source_graph_id.append(graph_id)
            source_uuid.append(admitted.SOURCE_UUID)
            source_path.append(admitted.SOURCE_JSON_RELATIVE.as_posix())

    seed_plan = degree.seed_plan(seed_prefix=admitted.SEED_PREFIX)
    pairs = []
    for pair_index, (graph_id, stream, frame, seed) in enumerate(seed_plan):
        truth = np.random.default_rng(31415 + pair_index).integers(
            0, 32, size=128, dtype=np.uint8)
        graph_i = graph_index[graph_id]
        syndromes = np.stack([
            layout.gf32_syndrome(deep[profile_i * len(graph_seeds) + graph_i], truth)
            for profile_i in range(len(profile_order))
        ]).astype(np.uint8)
        pairs.append((pair_index, graph_id, stream, frame, seed,
                      truth.copy(), graph_i, syndromes))

    # Reverse the pair arrays to prove that source extraction follows pair_index
    # and explicit graph maps rather than relying on incidental NPZ row order.
    pairs.reverse()
    return {
        "batch_uuid": np.asarray([admitted.BATCH_UUID]),
        "contract": np.asarray([admitted.CONTRACT]),
        "seed_namespace": np.asarray([admitted.SEED_PREFIX]),
        "graph_input_kind": np.asarray(["admitted_source"]),
        "profile_order": profile_order,
        "graph_seed": graph_seeds,
        "constructor_profile_index": np.asarray(constructor_profile_index, dtype=np.int64),
        "constructor_graph_index": np.asarray(constructor_graph_index, dtype=np.int64),
        "H_constructor": np.stack(constructor).astype(np.int64),
        "constructor_source_uuid": np.asarray(source_uuid),
        "constructor_source_path": np.asarray(source_path),
        "constructor_source_matrix_index": np.asarray(source_matrix_index, dtype=np.int64),
        "constructor_source_attempt_j": np.asarray(source_attempt_j, dtype=np.int64),
        "constructor_source_seed": np.asarray(source_seed, dtype=np.int64),
        "constructor_source_graph_id": np.asarray(source_graph_id, dtype=np.int64),
        "deep_profile_index": np.asarray(deep_profile_index, dtype=np.int64),
        "deep_graph_index": np.asarray(deep_graph_index, dtype=np.int64),
        "H_deep": np.stack(deep).astype(np.int64),
        "pair_index": np.asarray([row[0] for row in pairs], dtype=np.int64),
        "pair_graph_index": np.asarray([row[6] for row in pairs], dtype=np.int64),
        "pair_graph_seed": np.asarray([row[1] for row in pairs], dtype=np.int64),
        "pair_stream": np.asarray([row[2] for row in pairs], dtype=np.int64),
        "pair_frame": np.asarray([row[3] for row in pairs], dtype=np.int64),
        "pair_seed": np.asarray([row[4] for row in pairs], dtype=np.int64),
        "pair_truth": np.stack([row[5] for row in pairs]).astype(np.uint8),
        "pair_syndrome": np.stack([row[7] for row in pairs]).astype(np.uint8),
    }


def test_extract_source_data_joins_explicit_maps_and_preserves_same_support_labels():
    source = _fake_source_arrays()

    extracted = probe.extract_source_data(source)

    assert extracted["source_uuid"] == admitted.BATCH_UUID
    assert extracted["source_contract"] == admitted.CONTRACT
    assert extracted["source_path"] == probe.SOURCE_NPZ_RELATIVE.as_posix()
    assert list(extracted["graphs"]) == list(probe.GRAPH_SEEDS)
    assert len(extracted["pairs"]) == probe.HOLDOUT_PAIRS == 192

    candidate_profile = degree.PROFILE_ORDER.index("candidate")
    for graph_i, graph_id in enumerate(probe.GRAPH_SEEDS):
        graph = extracted["graphs"][graph_id]
        h_constructor = graph["constructor"]
        h_deep = graph["deep"]
        assert h_constructor.shape == h_deep.shape == (52, 128)
        assert np.array_equal(h_constructor != 0, h_deep != 0)
        assert not np.array_equal(h_constructor, h_deep)
        assert np.all((h_constructor[h_constructor != 0] > 0)
                      & (h_constructor[h_constructor != 0] < 32))
        assert np.all((h_deep[h_deep != 0] > 0)
                      & (h_deep[h_deep != 0] < 32))
        assert graph["source_graph_index"] == graph_i
        assert graph["deep_profile_index"] == candidate_profile
        assert graph["deep_graph_index"] == graph_i
        assert graph["source_constructor_row_index"] == 6 + graph_i
        assert graph["source_deep_row_index"] == 6 + graph_i
        assert graph["constructor_source_graph_id"] == graph_id
    graph_3905 = extracted["graphs"][2026093905]
    assert graph_3905["constructor_source_matrix_index"] == 10
    assert graph_3905["constructor_source_attempt_j"] == 1
    assert graph_3905["constructor_source_seed"] == 2560859716

    expected_plan = degree.seed_plan(seed_prefix=admitted.SEED_PREFIX)
    for pair_i, pair in enumerate(extracted["pairs"]):
        graph_id, stream, frame, seed = expected_plan[pair_i]
        assert pair["pair_index"] == pair_i
        assert (pair["graph_id"], pair["stream"], pair["frame"], pair["seed"]) \
            == (graph_id, stream, frame, seed)
        expected_truth = np.random.default_rng(31415 + pair_i).integers(
            0, 32, size=128, dtype=np.uint8)
        assert np.array_equal(pair["truth"], expected_truth)


def test_extract_source_data_rejects_changed_endpoint_support_before_decode():
    source = _fake_source_arrays()
    candidate_profile = degree.PROFILE_ORDER.index("candidate")
    matrix_i = int(np.flatnonzero(
        (source["constructor_profile_index"] == candidate_profile)
        & (source["constructor_graph_index"] == 0))[0])
    h_deep = source["H_deep"].copy()
    h_deep[matrix_i, 0, 0] = 0
    source["H_deep"] = h_deep

    with pytest.raises(ValueError, match="384|profile|support"):
        probe.extract_source_data(source)


def _fake_decoders(calls: list[dict]) -> dict:
    def make_decoder(arm: str):
        def decode(h: np.ndarray, prior: np.ndarray, syndrome: np.ndarray):
            h = np.asarray(h, dtype=np.int64)
            prior = np.asarray(prior, dtype=np.float64)
            syndrome = np.asarray(syndrome, dtype=np.int64)
            calls.append({"arm": arm, "H": h.copy(), "prior": prior.copy(),
                          "syndrome": syndrome.copy()})
            # Fixed output uses only decoder inputs; no truth/oracle is passed.
            raw = np.zeros(probe.N, dtype=np.uint8)
            return SimpleNamespace(
                x_hat=raw,
                syndrome_ok=bool(layout.syndrome_ok(h, raw, syndrome)),
                iterations=2,
                status="fake_fixed_word",
            )
        return decode

    return {arm: make_decoder(arm) for arm in probe.ARMS}


def _read_diagnostics(root: Path) -> dict[str, np.ndarray]:
    with np.load(root / "diagnostics.npz", allow_pickle=False) as loaded:
        return {name: loaded[name].copy() for name in loaded.files}


def test_source_free_t0_dry_run_and_existing_root_refusal(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    forbidden = lambda *args, **kwargs: pytest.fail("production binding/read entered")
    monkeypatch.setattr(probe, "_bind_production_decoders", forbidden)
    monkeypatch.setattr(probe, "_default_diagnostic_reader", forbidden)

    checks = probe.verify_t0()
    assert checks and all(checks.values())
    repo = tmp_path / "dry-run-repo"
    (repo / "workspace").mkdir(parents=True)
    dry = probe.dry_run(out_root=probe.OUT_ROOT_RELATIVE, repo_root=repo)
    assert dry["status"] == "DRY_RUN"
    assert dry["exists"] is False
    for field in ("diagnostic_reads", "attempted_decoder_calls",
                  "source_extractions", "production_bindings", "writes"):
        assert dry[field] == 0

    refused_repo = tmp_path / "existing-root-repo"
    existing = refused_repo / probe.OUT_ROOT_RELATIVE
    existing.mkdir(parents=True)
    reader_calls: list[int] = []
    decoder_calls: list[dict] = []
    with pytest.raises(FileExistsError):
        probe.execute_batch(
            out_root=probe.OUT_ROOT_RELATIVE,
            repo_root=refused_repo,
            diagnostic_reader=lambda: reader_calls.append(1) or _fake_source_arrays(),
            decode_fns=_fake_decoders(decoder_calls),
            rss_fn=lambda: 0,
            command="fake existing-root refusal",
        )
    assert reader_calls == []
    assert decoder_calls == []


def test_fake_entry_reuses_192_source_pairs_and_maps_endpoint_outputs(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = tmp_path / "fake-entry-repo"
    (repo / "workspace").mkdir(parents=True)
    source = _fake_source_arrays()
    extracted = probe.extract_source_data(source)
    reader_calls: list[int] = []
    decoder_calls: list[dict] = []
    sample_error_calls: list[int] = []
    monkeypatch.setattr(
        probe.prior_runner, "sample_error",
        lambda *args, **kwargs: sample_error_calls.append(1)
        or pytest.fail("same-sample endpoint replay must not resample"))
    monkeypatch.setattr(
        probe, "_bind_production_decoders",
        lambda *args, **kwargs: pytest.fail("production decoder binding entered"))
    summary = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE,
        repo_root=repo,
        diagnostic_reader=lambda: reader_calls.append(1) or source,
        decode_fns=_fake_decoders(decoder_calls),
        rss_fn=lambda: 0,
        command="fake fixed-source endpoint entry",
    )

    root = repo / probe.OUT_ROOT_RELATIVE
    assert summary["complete"] is True
    assert summary["terminal_status"] == "COMPLETE"
    assert summary["classification"] == "COMPLETE_DESCRIPTIVE_ONLY"
    assert summary["attempted_decoder_calls"] == probe.MAX_CALLS == 384
    assert summary["attempted_pairs"] == summary["completed_pairs"] == 192
    assert summary["raw_vectors_saved"] == 384
    assert summary["source_pairs"] == 192
    assert summary["disclosed_syndrome_bits"] == 384 * probe.SYNDROME_BITS
    assert summary["nominal_edge_update_proxy"] == (
        probe.EDGE_COUNT * sum(summary["iterations_sum_by_arm"].values()))
    assert summary["nominal_edge_update_proxy"] <= probe.EDGE_UPDATE_PROXY_CAP
    assert summary["constructor_exact"] is not None
    assert summary["deep_exact"] is not None
    assert reader_calls == [1]
    assert sample_error_calls == []
    assert len(decoder_calls) == probe.MAX_CALLS
    assert all(set(call) == {"arm", "H", "prior", "syndrome"}
               for call in decoder_calls)

    with (root / "frame_records.csv").open(
            newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    arrays = _read_diagnostics(root)
    with (root / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    assert len(rows) == probe.MAX_CALLS
    assert tuple(rows[0].keys()) == probe.FRAME_FIELDS
    assert tuple(arrays["pair_syndrome_arm_order"].tolist()) == probe.ARMS
    assert arrays["H_constructor"].shape == arrays["H_deep"].shape == (6, 52, 128)
    assert arrays["pair_truth"].shape == (192, 128)
    assert arrays["pair_syndrome"].shape == (192, 2, 52)
    assert arrays["raw_x_hat"].shape == (384, 128)
    assert arrays["call_vector_index"].tolist() == list(range(384))
    assert arrays["vector_call_index"].tolist() == list(range(384))
    assert arrays["batch_uuid"].tolist() == [probe.BATCH_UUID]
    assert arrays["contract"].tolist() == [probe.CONTRACT]
    assert arrays["source_batch_uuid"].tolist() == [probe.SOURCE_UUID]
    assert arrays["source_contract"].tolist() == [probe.SOURCE_CONTRACT]
    assert arrays["source_path"].tolist() == [probe.SOURCE_NPZ_RELATIVE.as_posix()]
    assert arrays["constructor_profile_index"].tolist() == [1] * 6
    assert arrays["constructor_graph_index"].tolist() == list(range(6))
    assert arrays["constructor_source_graph_id"].tolist() == list(probe.GRAPH_SEEDS)
    assert arrays["source_constructor_row_index"].tolist() == list(range(6, 12))
    assert arrays["source_deep_row_index"].tolist() == list(range(6, 12))
    assert manifest["batch_uuid"] == probe.BATCH_UUID
    assert manifest["source"]["batch_uuid"] == probe.SOURCE_UUID
    assert (root / "EXPLORATION_LOG.md").is_file()
    assert set(path.name for path in root.iterdir()) == {
        "manifest.json", "summary.json", "frame_records.csv",
        "diagnostics.npz", "EXPLORATION_LOG.md"}

    pair_by_index = {pair["pair_index"]: pair for pair in extracted["pairs"]}
    graph_index = {graph_id: i for i, graph_id in enumerate(probe.GRAPH_SEEDS)}
    for pair_i, pair in pair_by_index.items():
        assert arrays["pair_index"][pair_i] == pair_i
        assert arrays["pair_graph_id"][pair_i] == pair["graph_id"]
        assert arrays["pair_graph_index"][pair_i] == graph_index[pair["graph_id"]]
        assert arrays["pair_stream"][pair_i] == pair["stream"]
        assert arrays["pair_frame"][pair_i] == pair["frame"]
        assert arrays["pair_seed"][pair_i] == pair["seed"]
        truth = pair["truth"]
        assert np.array_equal(arrays["pair_truth"][pair_i], truth)
        graph = extracted["graphs"][pair["graph_id"]]
        expected_syndromes = {
            arm: np.asarray(layout.gf32_syndrome(graph[arm], truth), dtype=np.uint8)
            for arm in probe.ARMS}
        for arm_i, arm in enumerate(probe.ARMS):
            assert np.array_equal(arrays["pair_syndrome"][pair_i, arm_i],
                                  expected_syndromes[arm])

        pair_rows = [row for row in rows if int(row["pair_index"]) == pair_i]
        expected_order = probe.arm_order(pair["frame"])
        assert tuple(row["arm"] for row in pair_rows) == expected_order
        assert len(pair_rows) == 2
        for row in pair_rows:
            call_i = int(row["call_index"])
            arm = row["arm"]
            call = decoder_calls[call_i]
            expected_h = graph[arm]
            expected_syn = expected_syndromes[arm]
            assert call["arm"] == arm
            assert np.array_equal(call["H"], expected_h)
            assert np.array_equal(call["syndrome"], expected_syn)
            assert np.array_equal(call["prior"], probe._prior_matrix())
            assert int(arrays["call_pair_index"][call_i]) == pair_i
            assert arrays["call_arm"][call_i] == arm
            assert int(arrays["call_graph_index"][call_i]) == graph_index[pair["graph_id"]]
            assert int(row["source_graph_index"]) == graph_index[pair["graph_id"]]
            assert int(row["constructor_source_graph_id"]) == pair["graph_id"]
            assert int(row["source_constructor_row_index"]) == 6 + graph_index[pair["graph_id"]]
            assert int(row["source_deep_row_index"]) == 6 + graph_index[pair["graph_id"]]
            vector_i = int(arrays["call_vector_index"][call_i])
            assert vector_i == call_i
            assert int(arrays["vector_call_index"][vector_i]) == call_i
            assert int(arrays["vector_pair_index"][vector_i]) == pair_i
            assert arrays["vector_arm"][vector_i] == arm
            raw = arrays["raw_x_hat"][vector_i].astype(np.int64)
            raw_equal = bool(np.array_equal(raw, truth))
            syndrome_ok = bool(layout.syndrome_ok(expected_h, raw, expected_syn))
            assert (row["raw_symbols_equal"] == "True") is raw_equal
            assert (row["syndrome_accept"] == "True") is syndrome_ok
            assert (row["exact"] == "True") is (raw_equal and syndrome_ok)
            assert (row["syndrome_consistent_wrong"] == "True") is (
                syndrome_ok and not raw_equal)

    for graph_id, graph in extracted["graphs"].items():
        graph_i = graph_index[graph_id]
        assert np.array_equal(arrays["H_constructor"][graph_i], graph["constructor"])
        assert np.array_equal(arrays["H_deep"][graph_i], graph["deep"])
        assert np.array_equal(arrays["H_constructor"][graph_i] != 0,
                              arrays["H_deep"][graph_i] != 0)
    assert arrays["constructor_source_matrix_index"][4] == 10
    assert arrays["constructor_source_matrix_index"][5] == 12
    assert arrays["constructor_source_attempt_j"][4] == 1
    assert arrays["constructor_source_seed"][4] == 2560859716


def test_bad_source_stops_before_any_decoder_and_retains_incomplete_artifacts(
        tmp_path: Path):
    repo = tmp_path / "bad-source-repo"
    (repo / "workspace").mkdir(parents=True)
    source = _fake_source_arrays()
    candidate_profile = degree.PROFILE_ORDER.index("candidate")
    row = int(np.flatnonzero(
        (source["deep_profile_index"] == candidate_profile)
        & (source["deep_graph_index"] == 0))[0])
    source["H_deep"] = source["H_deep"].copy()
    source["H_deep"][row, 0, 0] = 0
    reader_calls: list[int] = []
    decoder_calls: list[dict] = []
    summary = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE,
        repo_root=repo,
        diagnostic_reader=lambda: reader_calls.append(1) or source,
        decode_fns=_fake_decoders(decoder_calls),
        rss_fn=lambda: 0,
        command="fake invalid source stop",
    )

    root = repo / probe.OUT_ROOT_RELATIVE
    assert reader_calls == [1]
    assert decoder_calls == []
    assert summary["complete"] is False
    assert summary["terminal_status"] == "INCOMPLETE"
    assert summary["attempted_decoder_calls"] == 0
    assert summary["constructor_exact"] is None
    assert summary["deep_exact"] is None
    assert summary["nominal_edge_update_proxy"] is None
    assert "384" in summary["stop_reason"] or "profile" in summary["stop_reason"]
    assert set(path.name for path in root.iterdir()) == {
        "manifest.json", "summary.json", "frame_records.csv",
        "diagnostics.npz", "EXPLORATION_LOG.md"}
    arrays = _read_diagnostics(root)
    assert arrays["H_constructor"].shape == (0, 52, 128)
    assert arrays["H_deep"].shape == (0, 52, 128)
    assert arrays["raw_x_hat"].shape == (0, 128)


def test_post_call_rss_stop_retains_first_vector_and_nulls_full_totals(
        tmp_path: Path):
    repo = tmp_path / "resource-stop-repo"
    (repo / "workspace").mkdir(parents=True)
    source = _fake_source_arrays()
    decoder_calls: list[dict] = []
    reader_calls: list[int] = []
    decoders = _fake_decoders(decoder_calls)

    def rss():
        return probe.RSS_CAP_BYTES if decoder_calls else 0

    summary = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE,
        repo_root=repo,
        diagnostic_reader=lambda: reader_calls.append(1) or source,
        decode_fns=decoders,
        rss_fn=rss,
        command="fake post-call RSS stop",
    )

    root = repo / probe.OUT_ROOT_RELATIVE
    assert reader_calls == [1]
    assert len(decoder_calls) == 1
    assert summary["complete"] is False
    assert summary["terminal_status"] == "INCOMPLETE"
    assert "rss_cap" in summary["stop_reason"]
    assert summary["attempted_decoder_calls"] == 1
    assert summary["attempted_pairs"] == 1
    assert summary["completed_pairs"] == 0
    assert summary["raw_vectors_saved"] == 1
    assert summary["constructor_exact"] is None
    assert summary["deep_exact"] is None
    assert summary["nominal_edge_update_proxy"] is None
    with (root / "frame_records.csv").open(
            newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    arrays = _read_diagnostics(root)
    assert len(rows) == 1
    assert rows[0]["arm"] == probe.ARMS[0]
    assert rows[0]["rss_b"] == str(probe.RSS_CAP_BYTES)
    assert arrays["call_index"].tolist() == [0]
    assert arrays["call_vector_index"].tolist() == [0]
    assert arrays["vector_call_index"].tolist() == [0]
    assert arrays["raw_x_hat"].shape == (1, 128)


def test_terminal_artifact_wall_overrun_retains_completed_calls_and_vectors(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = tmp_path / "terminal-write-wall-repo"
    (repo / "workspace").mkdir(parents=True)
    source = _fake_source_arrays()
    decoder_calls: list[dict] = []
    reader_calls: list[int] = []
    elapsed = [0.0]
    clock_jumps: list[float] = []
    write_json = probe._write_json

    def fake_now() -> float:
        return elapsed[0]

    def advance_after_first_terminal_manifest(path, value):
        write_json(path, value)
        if (Path(path).name == "manifest.json"
                and value.get("status") == "COMPLETE"
                and not clock_jumps):
            # This is the last write of the first-pass terminal artifacts. The
            # implementation must measure the checkpoint after this write.
            elapsed[0] = probe.WALL_CAP_S + 1.0
            clock_jumps.append(elapsed[0])

    monkeypatch.setattr(probe, "_write_json", advance_after_first_terminal_manifest)
    summary = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE,
        repo_root=repo,
        diagnostic_reader=lambda: reader_calls.append(1) or source,
        decode_fns=_fake_decoders(decoder_calls),
        now=fake_now,
        rss_fn=lambda: 0,
        command="fake terminal artifact wall overrun",
    )

    root = repo / probe.OUT_ROOT_RELATIVE
    assert clock_jumps == [probe.WALL_CAP_S + 1.0]
    assert reader_calls == [1]
    assert len(decoder_calls) == probe.MAX_CALLS == 384
    assert summary["complete"] is False
    assert summary["terminal_status"] == "INCOMPLETE"
    assert summary["classification"] == "INCOMPLETE"
    assert "wall" in summary["stop_reason"].lower()
    assert summary["resource_violations"] == 1
    assert summary["attempted_decoder_calls"] == probe.MAX_CALLS
    assert summary["attempted_pairs"] == summary["completed_pairs"] == 192
    assert summary["raw_vectors_saved"] == probe.MAX_CALLS
    for field in (
            "constructor_exact", "deep_exact", "delta", "per_arm_outcomes",
            "per_graph", "paired", "transitions", "nominal_edge_update_proxy",
            "nominal_edge_update_proxy_by_arm", "decoder_wall_s_by_arm",
            "iterations_sum_by_arm"):
        assert summary[field] is None
    with (root / "summary.json").open(encoding="utf-8") as handle:
        saved_summary = json.load(handle)
    with (root / "manifest.json").open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    with (root / "frame_records.csv").open(
            newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    arrays = _read_diagnostics(root)
    assert saved_summary == summary
    assert manifest["status"] == "INCOMPLETE"
    assert manifest["classification"] == "INCOMPLETE"
    assert "wall" in manifest["stop_reason"].lower()
    assert len(rows) == probe.MAX_CALLS
    assert [int(row["call_index"]) for row in rows] == list(range(probe.MAX_CALLS))
    assert arrays["call_index"].tolist() == list(range(probe.MAX_CALLS))
    assert arrays["call_vector_index"].tolist() == list(range(probe.MAX_CALLS))
    assert arrays["vector_call_index"].tolist() == list(range(probe.MAX_CALLS))
    assert arrays["raw_x_hat"].shape == (probe.MAX_CALLS, probe.N)
    assert np.array_equal(arrays["raw_x_hat"], np.zeros((probe.MAX_CALLS, probe.N)))
    log = (root / "EXPLORATION_LOG.md").read_text(encoding="utf-8")
    assert "INCOMPLETE" in log
    assert "wall" in log.lower()
