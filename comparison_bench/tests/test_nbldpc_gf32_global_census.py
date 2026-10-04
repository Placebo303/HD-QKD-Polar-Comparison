"""Focused fake-only tests for the fixed GF32 global support census."""
from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_global_census as census


GRAPH_IDS = tuple(range(2026093901, 2026093907))
SOURCE_BATCH_UUID = "a9352bc1-ae56-443b-ae93-9dcfa85d4229"
SOURCE_CONTRACT = (
    "NBLDPC-GF32-DEGREE-ADMITTED-20261001/PREREG_AND_AUTH.md")
SOURCE_SEED_NAMESPACE = "gf32-degree-admitted-v1"
CONSTRUCTION_UUID = "a9a18abe-3547-4d16-aa50-1f7150182f31"
CONSTRUCTION_PATH = "workspace/gf32_construct_a9a18abe/constructions.json"
CONTROL_MATRIX_INDICES = (0, 2, 4, 6, 9, 11)
ATTEMPT_J = (0, 0, 0, 0, 1, 0)
CONSTRUCTION_SEEDS = (*GRAPH_IDS[:4], 2560859716, GRAPH_IDS[5])


def _edge_matrix(edges: list[tuple[int, int]], *, shift: int = 0,
                 label_shift: int = 0) -> np.ndarray:
    """Turn an edge list into an integer GF(32) parity-check matrix."""
    h = np.zeros((52, len(edges)), dtype=np.int64)
    for edge_id, (left, right) in enumerate(edges):
        left = (left + shift) % 52
        right = (right + shift) % 52
        coefficient = ((edge_id * 7 + shift * 3 + label_shift) % 31) + 1
        h[left, edge_id] = coefficient
        h[right, edge_id] = coefficient
    return h


def _control_matrix(graph_index: int) -> np.ndarray:
    """Build one explicit fake 52x128 control support with the frozen degrees."""
    edges = []
    # A connected 4-regular circulant on 52 checks contributes 104 edges.
    for check in range(52):
        edges.append((check, (check + 1) % 52))
        edges.append((check, (check + 2) % 52))
    # Raise checks 4..51 to degree five with 24 disjoint non-circulant edges.
    edges.extend((check, check + 24) for check in range(4, 28))
    h = _edge_matrix(edges, shift=graph_index)
    assert h.shape == (52, 128)
    assert np.all(np.count_nonzero(h, axis=0) == 2)
    assert sorted(np.count_nonzero(h, axis=1).tolist()) == [4] * 4 + [5] * 48
    return h


def _candidate_matrix(graph_index: int) -> np.ndarray:
    """Make an unused-by-design degree-three row to catch wrong profile joins."""
    h = np.zeros((52, 128), dtype=np.int64)
    for column in range(128):
        start = (column + graph_index) % 52
        for offset in range(3):
            check = (start + offset) % 52
            h[check, column] = ((column * 5 + check + 1) % 31) + 1
    assert np.all(np.count_nonzero(h, axis=0) == 3)
    return h


def _fake_source_arrays() -> dict[str, np.ndarray]:
    """Return NPZ-shaped fake arrays with deliberately shuffled matrix rows."""
    # These are the accepted source writer's explicit maps.  Physical row
    # order is intentionally reversed so it cannot stand in for profile/graph
    # identity.  No source NPZ is opened by this fixture.
    maps = [(profile_i, graph_i)
            for profile_i in range(2) for graph_i in range(len(GRAPH_IDS))]
    maps.reverse()
    matrices = []
    source_matrix_index = []
    source_attempt_j = []
    source_seed = []
    source_graph_id = []
    for profile_i, graph_i in maps:
        if profile_i == 0:
            matrices.append(_control_matrix(graph_i))
            source_matrix_index.append(CONTROL_MATRIX_INDICES[graph_i])
        else:
            matrices.append(_candidate_matrix(graph_i))
            source_matrix_index.append((1, 3, 5, 7, 10, 12)[graph_i])
        source_attempt_j.append(ATTEMPT_J[graph_i])
        source_seed.append(CONSTRUCTION_SEEDS[graph_i])
        source_graph_id.append(GRAPH_IDS[graph_i])

    return {
        "batch_uuid": np.asarray([SOURCE_BATCH_UUID]),
        "contract": np.asarray([SOURCE_CONTRACT]),
        "seed_namespace": np.asarray([SOURCE_SEED_NAMESPACE]),
        "graph_input_kind": np.asarray(["admitted_source"]),
        "profile_order": np.asarray(["control", "candidate"]),
        "graph_seed": np.asarray(GRAPH_IDS, dtype=np.int64),
        "constructor_profile_index": np.asarray(
            [profile_i for profile_i, _ in maps], dtype=np.int64),
        "constructor_graph_index": np.asarray(
            [graph_i for _, graph_i in maps], dtype=np.int64),
        "H_constructor": np.stack(matrices),
        "constructor_source_uuid": np.asarray(
            [CONSTRUCTION_UUID] * len(maps)),
        "constructor_source_path": np.asarray(
            [CONSTRUCTION_PATH] * len(maps)),
        "constructor_source_matrix_index": np.asarray(
            source_matrix_index, dtype=np.int64),
        "constructor_source_attempt_j": np.asarray(
            source_attempt_j, dtype=np.int64),
        "constructor_source_seed": np.asarray(source_seed, dtype=np.int64),
        "constructor_source_graph_id": np.asarray(
            source_graph_id, dtype=np.int64),
    }


def _path_matrix() -> np.ndarray:
    h = np.zeros((4, 3), dtype=np.int64)
    for edge_id, (left, right) in enumerate(((0, 1), (1, 2), (2, 3))):
        h[left, edge_id] = 1
        h[right, edge_id] = 1
    return h


def _triangle_matrix() -> np.ndarray:
    h = np.zeros((3, 3), dtype=np.int64)
    for edge_id, (left, right) in enumerate(((0, 1), (1, 2), (0, 2))):
        h[left, edge_id] = 1
        h[right, edge_id] = 1
    return h


def test_rss_bytes_converts_linux_getrusage_kib_to_bytes(
        monkeypatch: pytest.MonkeyPatch):
    calls = []
    fake_resource = SimpleNamespace(
        RUSAGE_SELF="self",
        getrusage=lambda who: calls.append(who)
        or SimpleNamespace(ru_maxrss=33072),
    )
    monkeypatch.setitem(sys.modules, "resource", fake_resource)

    assert census._rss_bytes() == 33_865_728
    assert calls == ["self"]


def test_triangle_known_spectrum_sweep_residual_and_degeneracy():
    result = census.compute_graph_metrics(_triangle_matrix())

    assert np.allclose(result["eigenvalues"], [0.0, 1.5, 1.5],
                       rtol=0.0, atol=1e-10)
    assert result["lambda2"] == pytest.approx(1.5, abs=1e-10)
    assert result["lambda3_minus_lambda2"] == pytest.approx(0.0, abs=1e-10)
    assert result["eigensystem_residual_max_abs"] <= 1e-10
    assert result["tolerance"] == 1e-10
    assert "FIEDLER_DEGENERATE" in result["flags"]
    assert len(result["sweep"]) == 2
    assert all(row["phi"] == pytest.approx(1.0, abs=1e-10)
               for row in result["sweep"])
    assert result["phi_sweep"] == pytest.approx(1.0, abs=1e-10)
    assert result["best_prefix_k"] == 1


def test_path4_known_spectrum_conductance_and_determinism():
    h = _path_matrix()
    first = census.compute_graph_metrics(h)
    second = census.compute_graph_metrics(h.copy())

    assert np.allclose(first["eigenvalues"], [0.0, 0.5, 1.5, 2.0],
                       rtol=0.0, atol=1e-10)
    assert first["lambda2"] == pytest.approx(0.5, abs=1e-10)
    assert first["lambda3_minus_lambda2"] == pytest.approx(1.0, abs=1e-10)
    assert first["phi_sweep"] == pytest.approx(1.0 / 3.0, abs=1e-10)
    assert first["best_prefix_k"] == 2
    assert first["fiedler_order"] == second["fiedler_order"]
    assert first["fiedler_sign_flip"] == second["fiedler_sign_flip"]
    assert first["sweep"] == second["sweep"]


def test_parallel_edges_preserve_each_column_and_multiplicity():
    h = np.zeros((3, 3), dtype=np.int64)
    for edge_id, (left, right) in enumerate(((0, 1), (0, 1), (1, 2))):
        h[left, edge_id] = 1
        h[right, edge_id] = 1

    result = census.compute_graph_metrics(h)

    assert result["edge_endpoints_by_column"] == [[0, 1], [0, 1], [1, 2]]
    assert np.array_equal(result["adjacency"],
                          [[0, 2, 0], [2, 0, 1], [0, 1, 0]])
    assert np.array_equal(result["degree"], [2, 3, 1])
    assert result["eigenvalues"] == pytest.approx([0.0, 1.0, 2.0], abs=1e-10)
    assert result["phi_sweep"] == pytest.approx(1.0, abs=1e-10)


def test_fake_source_rows_are_joined_by_explicit_profile_and_graph_maps(
        tmp_path: Path):
    source = _fake_source_arrays()
    assert len(source["H_constructor"]) == 12
    assert not np.array_equal(
        source["constructor_profile_index"], np.repeat([0, 1], 6))

    reads = []

    def source_reader():
        reads.append("read")
        return source

    (tmp_path / "workspace").mkdir()
    out_root = tmp_path / "workspace" / "gf32_global_f4a0ff0d"
    result = census.execute_batch(
        source_reader=source_reader,
        out_root=out_root,
        repo_root=tmp_path,
        now=lambda: 0.0,
        rss_fn=lambda: 0,
        command="fake-only C2 source-map check",
    )

    assert reads == ["read"]
    assert result["completed_graphs"] == 6
    assert result["status"] == "COMPLETE"
    graph_by_id = {graph["graph_id"]: graph for graph in result["graphs"]}
    assert tuple(graph_by_id) == GRAPH_IDS
    for graph_index, graph_id in enumerate(GRAPH_IDS):
        graph = graph_by_id[graph_id]
        lineage = graph["source_lineage"]
        assert lineage["source_graph_id"] == graph_id
        assert lineage["source_matrix_index"] == CONTROL_MATRIX_INDICES[graph_index]
        assert lineage["source_attempt_j"] == ATTEMPT_J[graph_index]
        assert lineage["source_construction_seed"] == CONSTRUCTION_SEEDS[graph_index]
        expected_edges = _control_matrix(graph_index)
        expected = [np.flatnonzero(expected_edges[:, edge_id]).tolist()
                    for edge_id in range(expected_edges.shape[1])]
        assert graph["edge_ids_by_column"] == list(range(128))
        assert graph["edge_endpoints_by_column"] == expected
    source_map_by_id = {row["graph_id"]: row for row in result["source_maps"]}
    for graph_index, graph_id in enumerate(GRAPH_IDS):
        mapped = source_map_by_id[graph_id]
        expected_row = int(np.flatnonzero(
            (source["constructor_profile_index"] == 0)
            & (source["constructor_graph_index"] == graph_index))[0])
        assert mapped["constructor_row_index"] == expected_row
        assert mapped["constructor_profile_index"] == 0
        assert mapped["constructor_graph_index"] == graph_index
        assert mapped["graph_seed"] == graph_id
        assert mapped["source_matrix_index"] == CONTROL_MATRIX_INDICES[graph_index]


def test_source_free_t0_dry_run_and_root_refusal(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        census, "_default_source_reader",
        lambda *args, **kwargs: pytest.fail("production source reader entered"))

    t0 = census.verify_t0()
    assert t0["status"] == "PASS"
    assert t0["source_reads"] == 0
    assert t0["decoder_calls"] == 0
    assert t0["graph_build_calls"] == 0
    assert t0["writes"] == 0

    dry_repo = tmp_path / "dry-repo"
    (dry_repo / "workspace").mkdir(parents=True)
    dry = census.dry_run(repo_root=dry_repo)
    assert dry["status"] == "DRY_RUN"
    assert dry["source_reads"] == 0
    assert dry["decoder_calls"] == 0
    assert dry["graph_build_calls"] == 0
    assert dry["writes"] == 0

    reader_calls: list[int] = []
    reader = lambda: reader_calls.append(1) or _fake_source_arrays()

    wrong_root = dry_repo / "workspace" / "wrong-root"
    with pytest.raises(ValueError, match="out-root"):
        census.execute_batch(
            source_reader=reader, out_root=wrong_root, repo_root=dry_repo,
            now=lambda: 0.0, rss_fn=lambda: 0)
    assert reader_calls == []

    existing_repo = tmp_path / "existing-repo"
    existing_root = existing_repo / census.OUT_ROOT_RELATIVE
    existing_root.mkdir(parents=True)
    marker = existing_root / "keep.txt"
    marker.write_text("preserve", encoding="utf-8")
    with pytest.raises(FileExistsError):
        census.execute_batch(
            source_reader=reader, out_root=census.OUT_ROOT_RELATIVE,
            repo_root=existing_repo, now=lambda: 0.0, rss_fn=lambda: 0)
    assert reader_calls == []
    assert marker.read_text(encoding="utf-8") == "preserve"


def test_invalid_source_stops_without_replacement_and_retains_prior_graphs(
        tmp_path: Path):
    source = _fake_source_arrays()
    source["H_constructor"] = source["H_constructor"].copy()
    selected_row = int(np.flatnonzero(
        (source["constructor_profile_index"] == 0)
        & (source["constructor_graph_index"] == 5))[0])
    bad_check = int(np.flatnonzero(source["H_constructor"][selected_row, :, 0])[0])
    source["H_constructor"][selected_row, bad_check, 0] = 0

    repo = tmp_path / "invalid-source-repo"
    (repo / "workspace").mkdir(parents=True)
    reader_calls: list[int] = []
    result = census.execute_batch(
        source_reader=lambda: reader_calls.append(1) or source,
        out_root=census.OUT_ROOT_RELATIVE,
        repo_root=repo,
        now=lambda: 0.0,
        rss_fn=lambda: 0,
        command="fake invalid-source STOP",
    )

    assert reader_calls == [1]
    assert result["source_reads"] == 1
    assert result["status"] == "INCOMPLETE"
    assert result["completed_graphs"] == 5
    assert [graph["graph_id"] for graph in result["graphs"]] == list(GRAPH_IDS[:5])
    assert [row["graph_id"] for row in result["source_maps"]] == list(GRAPH_IDS)
    assert "source_or_graph_stop:ValueError:" in result["stop_reason"]
    assert "2026093906" in result["stop_reason"]

    root = repo / census.OUT_ROOT_RELATIVE
    assert set(path.name for path in root.iterdir()) == set(census.ARTIFACT_NAMES)
    log = (root / "EXPLORATION_LOG.md").read_text(encoding="utf-8")
    assert log.rstrip().splitlines()[-1].startswith("FINAL_STATUS=INCOMPLETE")


def test_terminal_artifact_write_wall_overcap_keeps_all_fake_metrics(
        tmp_path: Path):
    source = _fake_source_arrays()
    repo = tmp_path / "terminal-overcap-repo"
    (repo / "workspace").mkdir(parents=True)
    root = repo / census.OUT_ROOT_RELATIVE
    artifacts = tuple(root / name for name in census.ARTIFACT_NAMES)
    terminal_artifacts_seen = False

    def fake_now() -> float:
        nonlocal terminal_artifacts_seen
        if all(path.is_file() for path in artifacts):
            terminal_artifacts_seen = True
            return census.WALL_CAP_S + 1.0
        return 0.0

    result = census.execute_batch(
        source_reader=lambda: source,
        out_root=census.OUT_ROOT_RELATIVE,
        repo_root=repo,
        now=fake_now,
        rss_fn=lambda: 0,
        command="fake terminal-write wall overcap",
    )

    assert terminal_artifacts_seen is True
    assert result["status"] == "INCOMPLETE"
    assert result["stop_reason"] == "final_total_wall_cap"
    assert result["completed_graphs"] == 6
    assert [graph["graph_id"] for graph in result["graphs"]] == list(GRAPH_IDS)
    assert result["resources"]["final_wall_s"] > census.WALL_CAP_S
    log = (root / "EXPLORATION_LOG.md").read_text(encoding="utf-8")
    assert log.rstrip().splitlines()[-1].startswith("FINAL_STATUS=INCOMPLETE")

