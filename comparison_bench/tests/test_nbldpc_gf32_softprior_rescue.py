"""Focused fake-only tests for the frozen GF(32) soft-prior rescue cycle."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_softprior_rescue as probe
from comparison_bench.formal_ir import nonbinary_v10_common as common


GRAPH_IDS = tuple(range(2026093901, 2026093907))
SOURCE_BATCH_UUID = "a9352bc1-ae56-443b-ae93-9dcfa85d4229"
SOURCE_CONTRACT = (
    "NBLDPC-GF32-DEGREE-ADMITTED-20261001/PREREG_AND_AUTH.md")
SOURCE_SEED_NAMESPACE = "gf32-degree-admitted-v1"
CONSTRUCTION_UUID = "a9a18abe-3547-4d16-aa50-1f7150182f31"
CONSTRUCTION_PATH = "workspace/gf32_construct_a9a18abe/constructions.json"
SOURCE_MATRIX_INDICES = (0, 2, 4, 6, 9, 11)
ATTEMPT_J = (0, 0, 0, 0, 1, 0)
CONSTRUCTION_SEEDS = (*GRAPH_IDS[:4], 2560859716, GRAPH_IDS[5])
SUPPORT = (0, 1, 3, 7, 15, 31)
COUNTS = {1: 2295, 3: 1126, 7: 557, 15: 304, 31: 146}


def _fake_control_matrix(graph_index: int) -> np.ndarray:
    """Make a connected, source-shaped 52x128 multigraph matrix."""
    edges = []
    for check in range(52):
        edges.append((check, (check + 1) % 52))
        edges.append((check, (check + 2) % 52))
    edges.extend((check, check + 24) for check in range(4, 28))
    h = np.zeros((52, 128), dtype=np.int64)
    for edge_id, (left, right) in enumerate(edges):
        left = (left + graph_index) % 52
        right = (right + graph_index) % 52
        h[left, edge_id] = 1
        h[right, edge_id] = 1
    assert h.shape == (52, 128)
    assert np.all(np.count_nonzero(h, axis=0) == 2)
    assert sorted(np.count_nonzero(h, axis=1).tolist()) == [4] * 4 + [5] * 48
    return h


def _fake_source_arrays() -> dict[str, np.ndarray]:
    """NPZ-shaped fake source with shuffled physical rows and explicit maps."""
    pairs = [(profile_i, graph_i)
             for profile_i in range(2) for graph_i in range(len(GRAPH_IDS))]
    pairs.reverse()
    matrices = []
    matrix_indices = []
    attempts = []
    seeds = []
    graph_ids = []
    for profile_i, graph_i in pairs:
        matrices.append(_fake_control_matrix(graph_i))
        if profile_i == 0:
            matrix_indices.append(SOURCE_MATRIX_INDICES[graph_i])
            attempts.append(ATTEMPT_J[graph_i])
            seeds.append(CONSTRUCTION_SEEDS[graph_i])
        else:
            matrix_indices.append((1, 3, 5, 7, 10, 12)[graph_i])
            attempts.append(ATTEMPT_J[graph_i])
            seeds.append(CONSTRUCTION_SEEDS[graph_i])
        graph_ids.append(GRAPH_IDS[graph_i])

    profile_index = np.asarray([p for p, _ in pairs], dtype=np.int64)
    graph_index = np.asarray([g for _, g in pairs], dtype=np.int64)
    return {
        "batch_uuid": np.asarray([SOURCE_BATCH_UUID]),
        "contract": np.asarray([SOURCE_CONTRACT]),
        "seed_namespace": np.asarray([SOURCE_SEED_NAMESPACE]),
        "graph_input_kind": np.asarray(["admitted_source"]),
        "profile_order": np.asarray(["control", "candidate"]),
        "graph_seed": np.asarray(GRAPH_IDS, dtype=np.int64),
        "deep_profile_index": profile_index.copy(),
        "deep_graph_index": graph_index.copy(),
        "H_deep": np.stack(matrices),
        "constructor_profile_index": profile_index,
        "constructor_graph_index": graph_index,
        "constructor_source_uuid": np.asarray([CONSTRUCTION_UUID] * len(pairs)),
        "constructor_source_path": np.asarray([CONSTRUCTION_PATH] * len(pairs)),
        "constructor_source_matrix_index": np.asarray(matrix_indices, dtype=np.int64),
        "constructor_source_attempt_j": np.asarray(attempts, dtype=np.int64),
        "constructor_source_seed": np.asarray(seeds, dtype=np.int64),
        "constructor_source_graph_id": np.asarray(graph_ids, dtype=np.int64),
    }


def _original_prior() -> np.ndarray:
    pmf = np.zeros(32, dtype=np.float64)
    pmf[0] = 0.550
    for symbol, count in COUNTS.items():
        pmf[symbol] = 0.450 * count / 4428
    pmf /= pmf.sum()
    return np.tile(pmf, (128, 1))


def _truth() -> np.ndarray:
    # Fixed fake sample. Decoders receive only H, prior and its syndrome.
    truth = np.zeros(128, dtype=np.uint8)
    truth[127] = 1
    return truth


def _wrong_valid_vector(truth: np.ndarray) -> np.ndarray:
    # The first three source columns form a check-triangle null vector.
    wrong = truth.copy()
    wrong[:3] ^= np.uint8(1)
    return wrong


def _decode_result(x_hat: np.ndarray, *, iterations: int = 7,
                   beliefs: np.ndarray | None = None,
                   belief_provenance: str = "CHECK_UPDATED",
                   status: str = "fake_complete",
                   syndrome_ok: bool | None = None) -> SimpleNamespace:
    if beliefs is None:
        beliefs = np.zeros((128, 32), dtype=np.float64)
    return SimpleNamespace(
        x_hat=np.asarray(x_hat, dtype=np.uint8),
        iterations=iterations,
        final_beliefs=np.asarray(beliefs, dtype=np.float64),
        belief_provenance=belief_provenance,
        status=status,
        runtime_s=0.001,
        syndrome_ok=syndrome_ok,
    )


def _branch_records(vectors: list[np.ndarray], *, call_base: int = 100,
                    valid: list[bool] | None = None) -> list[dict]:
    if valid is None:
        valid = [True] * len(vectors)
    return [
        {
            "call_index": call_base + i,
            "branch_index": i,
            "guess_symbol": SUPPORT[i],
            "x_hat": np.asarray(vector, dtype=np.uint8),
            "syndrome_valid": valid[i],
        }
        for i, vector in enumerate(vectors)
    ]


def _fake_batch_adapters(
        repo_root: Path, *, failure_pairs: tuple[int, ...] = (2, 3, 4),
        branch_resource_pair: int | None = None,
        bad_beliefs_pair: int | None = None,
        bad_source: bool = False,
        terminal_overrun: bool = False,
        syndrome_mismatch_overrun_pair: int | None = None,
        ) -> dict:
    """Build deterministic source/sampler/decoder fakes for 192 pairs."""
    state = {
        "source_reads": 0, "sampler_seeds": [], "decoder_inputs": [],
        "current_pair": -1, "next_branch": 0, "rss_over": False,
        "clock": 0.0, "terminal_triggered": False,
    }
    truth = _truth()
    wrong = _wrong_valid_vector(truth)
    zero = np.zeros(128, dtype=np.uint8)
    original = _original_prior()
    source = _fake_source_arrays()
    if bad_source:
        source["batch_uuid"] = np.asarray(["wrong-source-uuid"])

    def source_reader():
        state["source_reads"] += 1
        return source

    def sampler(seed, pmf, width=128):
        state["current_pair"] = len(state["sampler_seeds"])
        state["next_branch"] = 0
        state["sampler_seeds"].append(int(seed))
        assert width == 128
        np.testing.assert_allclose(pmf, probe.pmf(), rtol=0.0, atol=1e-15)
        return truth.copy()

    def record_input(role, H, prior, syndrome, kwargs):
        state["decoder_inputs"].append({
            "role": role, "H": np.asarray(H).copy(),
            "prior": np.asarray(prior).copy(),
            "syndrome": np.asarray(syndrome).copy(), "kwargs": dict(kwargs),
        })

    def reported_syndrome(H, x_hat, syndrome):
        actual = np.asarray(probe.layout.gf32_syndrome(H, x_hat), dtype=np.int64).ravel()
        return bool(np.array_equal(actual, np.asarray(syndrome, dtype=np.int64)))

    def baseline(H, prior, syndrome, **kwargs):
        pair_index = state["current_pair"]
        record_input("baseline", H, prior, syndrome, kwargs)
        if pair_index in failure_pairs:
            x_hat = zero
            iterations = 90
            status = "fake_baseline_failed"
            beliefs = (np.zeros((127, 32), dtype=np.float64)
                       if pair_index == bad_beliefs_pair else
                       np.zeros((128, 32), dtype=np.float64))
        elif pair_index == 1:
            x_hat = wrong
            iterations = 7
            status = "fake_baseline_valid_wrong"
            beliefs = np.zeros((128, 32), dtype=np.float64)
        else:
            x_hat = truth
            iterations = 7
            status = "fake_baseline_exact"
            beliefs = np.zeros((128, 32), dtype=np.float64)
        syndrome_ok = reported_syndrome(H, x_hat, syndrome)
        if pair_index == syndrome_mismatch_overrun_pair:
            # Simulate a decoder return after the per-call wall cap, while
            # independently reporting the opposite syndrome flag.
            state["clock"] += probe.CALL_CAP_S + 1.0
            syndrome_ok = not syndrome_ok
        return _decode_result(
            x_hat, iterations=iterations, beliefs=beliefs, status=status,
            syndrome_ok=syndrome_ok)

    def soft_prior(H, prior, syndrome, **kwargs):
        pair_index = state["current_pair"]
        branch_index = state["next_branch"]
        state["next_branch"] += 1
        record_input("soft_prior", H, prior, syndrome, kwargs)
        if pair_index == 2 and branch_index < 3:
            x_hat = wrong
        elif pair_index == 2 and branch_index == 3:
            x_hat = truth
        elif pair_index == 2:
            x_hat = zero
        elif pair_index in (3, branch_resource_pair):
            x_hat = wrong if pair_index == 3 or branch_index == 0 else zero
        else:
            x_hat = zero
        valid = reported_syndrome(H, x_hat, syndrome)
        if branch_resource_pair == pair_index and branch_index == 0:
            # The returned branch is retained; the resource guard must stop
            # before another branch call.
            state["rss_over"] = True
        return _decode_result(
            x_hat, iterations=(4 + branch_index if valid else 90),
            status="fake_branch_valid" if valid else "fake_branch_failed",
            syndrome_ok=valid)

    def now():
        root = repo_root / probe.OUT_ROOT_RELATIVE
        expected_artifacts = {
            "manifest.json", "summary.json", "frame_records.csv",
            "diagnostics.npz", "EXPLORATION_LOG.md",
        }
        if terminal_overrun and not state["terminal_triggered"] and root.exists():
            if expected_artifacts.issubset({path.name for path in root.iterdir()}):
                state["terminal_triggered"] = True
                state["clock"] = probe.WALL_CAP_S + 2.0
                return state["clock"]
        state["clock"] += 0.001
        return state["clock"]

    def rss_fn():
        return probe.RSS_CAP_BYTES + 1 if state["rss_over"] else 100_000

    return {
        "source_reader": source_reader,
        "sampler": sampler,
        "decode_fns": {"baseline": baseline, "soft_prior": soft_prior},
        "repo_root": repo_root,
        "now": now,
        "rss_fn": rss_fn,
        "command": "fake-only S2",
        "state": state,
    }


def test_seed_plan_and_t0_dry_run_are_source_free(tmp_path: Path):
    plan = probe.build_seed_plan()
    assert len(plan) == 192
    assert len({row[3] for row in plan}) == 192
    assert plan == [
        (graph_id, stream, frame,
         common.v10_seed(
             f"gf32-softprior-v1:holdout:{graph_id}:{stream}:{frame}"))
        for graph_id in GRAPH_IDS for stream in (0, 1) for frame in range(16)
    ]

    t0 = probe.verify_t0()
    dry = probe.dry_run(out_root=probe.OUT_ROOT_RELATIVE, repo_root=tmp_path)
    assert t0["status"] == "PASS"
    assert t0["prior_exclusion_plan_count"] == 13
    assert t0["prior_exclusion_rows"] == 2832
    assert dry["status"] == "DRY_RUN"
    assert dry["source_reads"] == dry["writes"] == 0
    assert not (tmp_path / probe.OUT_ROOT_RELATIVE).exists()


def test_fake_source_selects_explicit_control_map_and_3905_j1_lineage():
    identity, selected = probe.select_sources(_fake_source_arrays())

    assert identity["batch_uuid"] == SOURCE_BATCH_UUID
    assert [row["graph_id"] for row in selected] == list(GRAPH_IDS)
    assert selected[4]["deep_row_index"] != 4  # physical matrix order is shuffled
    lineage = selected[4]["source_lineage"]
    assert lineage == {
        "source_uuid": CONSTRUCTION_UUID,
        "source_path": CONSTRUCTION_PATH,
        "source_matrix_index": 9,
        "source_attempt_j": 1,
        "source_construction_seed": 2560859716,
        "source_graph_id": 2026093905,
    }
    np.testing.assert_array_equal(selected[4]["H"], _fake_control_matrix(4))


def test_bad_fake_source_maps_stop_at_source_selection():
    source = _fake_source_arrays()
    source["deep_graph_index"] = source["deep_graph_index"].copy()
    source["deep_graph_index"][0] = source["deep_graph_index"][1]
    with pytest.raises(ValueError, match="deep-H/profile/graph maps"):
        probe.select_sources(source)


def test_selector_uses_syndrome_relative_active_checks_stable_entropy_and_ties():
    h = _fake_control_matrix(0)
    x_hat = np.zeros(128, dtype=np.uint8)
    x_hat[0] = 1
    # H*x is nonzero at checks 0,1. The nonzero public syndrome agrees there
    # and differs only at check 10, so activity must come from H*x != syndrome.
    syndrome = np.zeros(52, dtype=np.int64)
    syndrome[0:2] = 1
    syndrome[10] = 1
    log_beliefs = np.full((128, 32), 1000.0, dtype=np.float64)

    selected, metadata = probe.select_uncertain_variable(
        H=h, x_hat=x_hat, syndrome=syndrome, final_beliefs=log_beliefs,
        belief_provenance="CHECK_UPDATED")

    expected_active = np.flatnonzero(h[10] != 0).tolist()
    assert selected == min(expected_active)  # uniform entropy; lowest column wins
    assert selected > 0  # H*x != 0 alone would incorrectly include columns 0,1
    assert metadata["violated_check_ids"] == [10]
    assert metadata["active_variable_columns"] == expected_active
    assert metadata["selected_column"] == selected
    np.testing.assert_allclose(metadata["entropy_bits"], np.full(128, 5.0),
                               rtol=0.0, atol=1e-12)


@pytest.mark.parametrize("bad_beliefs,provenance", [
    (np.zeros((4, 32)), "CHECK_UPDATED"),
    (np.full((5, 32), np.nan), "CHECK_UPDATED"),
    (np.zeros((5, 32)), "INITIAL_PRIOR"),
])
def test_selector_stops_on_bad_beliefs_or_provenance(bad_beliefs, provenance):
    h = _fake_control_matrix(0)
    x_hat = np.zeros(128, dtype=np.uint8)
    x_hat[0] = 1
    with pytest.raises((ValueError, RuntimeError)):
        probe.select_uncertain_variable(
            H=h, x_hat=x_hat, syndrome=np.zeros(52, dtype=np.int64),
            final_beliefs=bad_beliefs, belief_provenance=provenance)


def test_selector_stops_when_no_check_is_violated():
    h = _fake_control_matrix(0)
    x_hat = np.zeros(128, dtype=np.uint8)
    with pytest.raises(ValueError, match="no variables adjacent"):
        probe.select_uncertain_variable(
            H=h, x_hat=x_hat, syndrome=np.zeros(52, dtype=np.int64),
            final_beliefs=np.zeros((128, 32)),
            belief_provenance="CHECK_UPDATED")


def test_original_prior_branch_scoring_all_six_ties_and_no_valid_branch():
    prior = _original_prior()
    vectors = []
    for symbol in SUPPORT:
        x = np.zeros(128, dtype=np.uint8)
        x[0] = symbol
        vectors.append(x)
    records = _branch_records(vectors, call_base=20)

    selected_call, score_rows = probe.select_soft_prior_branch(records, prior)
    assert selected_call == 20  # original P favors zero at variable 0
    assert [row["branch_index"] for row in score_rows] == list(range(6))
    assert score_rows[0]["score"] > score_rows[1]["score"]

    # Equal original-prior scores resolve to the lowest branch index, not call order.
    tied = _branch_records([vectors[1], vectors[1]], call_base=90)
    tied[0]["branch_index"], tied[1]["branch_index"] = 5, 2
    tied_call, _ = probe.select_soft_prior_branch(tied, prior)
    assert tied_call == 91

    no_valid = _branch_records(vectors, valid=[False] * 6)
    none_call, none_scores = probe.select_soft_prior_branch(no_valid, prior)
    assert none_call is None
    assert all(row["score"] is None for row in none_scores)


def test_linux_rss_high_water_kib_is_converted_to_bytes(monkeypatch: pytest.MonkeyPatch):
    calls = []
    fake_resource = SimpleNamespace(
        RUSAGE_SELF="self",
        getrusage=lambda who: calls.append(who)
        or SimpleNamespace(ru_maxrss=33072),
    )
    monkeypatch.setitem(sys.modules, "resource", fake_resource)

    assert probe._rss_bytes() == 33_865_728
    assert calls == ["self"]


def test_out_root_refusal_precedes_source_sampler_and_decoder(tmp_path: Path):
    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append(1)
        raise AssertionError("preflight must refuse before adapters")

    adapters = {
        "source_reader": forbidden,
        "sampler": forbidden,
        "decode_fns": {"baseline": forbidden, "soft_prior": forbidden},
        "repo_root": tmp_path,
        "now": lambda: 0.0,
        "rss_fn": lambda: 0,
    }
    with pytest.raises(ValueError):
        probe.execute_batch(out_root="workspace/wrong-root", **adapters)
    assert calls == []

    exact_root = tmp_path / probe.OUT_ROOT_RELATIVE
    exact_root.mkdir(parents=True)
    with pytest.raises(FileExistsError):
        probe.execute_batch(out_root=probe.OUT_ROOT_RELATIVE, **adapters)
    assert calls == []


def test_fake_full192_keeps_physical_logical_costs_vectors_and_wrong_isolation(
        tmp_path: Path):
    (tmp_path / "workspace").mkdir()
    adapters = _fake_batch_adapters(tmp_path)
    state = adapters.pop("state")
    result = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE, **adapters)
    root = tmp_path / probe.OUT_ROOT_RELATIVE

    assert state["source_reads"] == 1
    assert len(state["sampler_seeds"]) == 192
    assert state["sampler_seeds"] == [row[3] for row in probe.build_seed_plan()]
    assert result["status"] == "COMPLETE"
    assert result["completed_pairs"] == 192
    assert result["attempted_physical_calls"] == 210  # 192 + 6*3 failures
    assert result["baseline_calls"] == 192
    assert result["branch_calls"] == 18
    assert result["logical_control_calls"] == 192
    assert result["logical_candidate_calls"] == 210
    assert result["control_exact"] == 188
    assert result["candidate_exact"] == 189
    assert result["delta_exact"] == 1
    assert result["syndrome_valid_wrong_control"] == 1
    assert result["syndrome_valid_wrong_candidate"] == 2
    assert result["syndrome_failed_control"] == 3
    assert result["syndrome_failed_candidate"] == 1
    assert result["paired"] == {
        "both_exact": 188, "candidate_only": 1,
        "control_only": 0, "neither": 3,
    }
    assert result["disclosure_bits"] == 99_840
    assert result["syndrome_bits_per_method_frame"] == 260
    assert result["internal_branch_disclosure_bits"] == 0
    calls = result["calls"]
    assert len(calls) == 210
    assert result["physical_decoder_iterations"] == sum(
        int(row["iterations"]) for row in calls)
    assert result["nominal_edge_iteration_proxy"] == 256 * sum(
        int(row["iterations"]) for row in calls)
    assert all(0 <= int(row["iterations"]) <= 90 for row in calls)

    # Each baseline/branch call has only H, probability prior and public syndrome;
    # candidate restarts are cold and differ from original P in one row only.
    assert len(state["decoder_inputs"]) == 210
    original = _original_prior()
    for input_index, call_input in enumerate(state["decoder_inputs"]):
        assert set(call_input["kwargs"]) == {
            "max_iter", "damping_alpha", "warm_beliefs", "field"}
        assert call_input["kwargs"] == {
            "max_iter": 90, "damping_alpha": 1.0,
            "warm_beliefs": None, "field": None,
        }
        assert call_input["H"].shape == (52, 128)
        assert call_input["syndrome"].shape == (52,)
        if call_input["role"] == "baseline":
            np.testing.assert_allclose(
                call_input["prior"], original, rtol=0.0, atol=1e-15)
        else:
            prior = call_input["prior"]
            same_as_original = np.all(
                np.isclose(prior, original, rtol=0.0, atol=1e-15), axis=1)
            changed = np.flatnonzero(~same_as_original)
            assert len(changed) == 1
            assert changed[0] == result["calls"][input_index]["selected_variable"]
            unchanged = np.setdiff1d(np.arange(128), changed)
            np.testing.assert_allclose(
                prior[unchanged], original[unchanged], rtol=0.0, atol=1e-15)
            assert prior[changed[0]].sum() == 1.0
            assert np.count_nonzero(prior[changed[0]]) == 1
            assert prior[
                changed[0], result["calls"][input_index]["guess_symbol"]] == 1.0

    branches = [row for row in calls if row["role"] == "soft_prior"]
    assert len(branches) == 18
    for pair_index in (2, 3, 4):
        pair_branches = [row for row in branches if row["pair_index"] == pair_index]
        assert [row["branch_index"] for row in pair_branches] == list(range(6))
        assert [row["guess_symbol"] for row in pair_branches] == list(SUPPORT)
    pair2_selected = next(row for row in result["pairs"]
                          if row["pair_index"] == 2)
    pair3_selected = next(row for row in result["pairs"]
                          if row["pair_index"] == 3)
    pair4_selected = next(row for row in result["pairs"]
                          if row["pair_index"] == 4)
    assert pair2_selected["candidate_selected_call_index"] == 6
    assert pair3_selected["candidate_selected_call_index"] == 10
    assert pair4_selected["candidate_selected_call_index"] == 16
    selected_pair2_branch = next(row for row in branches if row["call_index"] == 6)
    assert selected_pair2_branch["guess_symbol"] == 7
    assert selected_pair2_branch["returned_selected_symbol"] != 7
    assert all(pair["candidate_selected_call_index"] == pair["baseline_call_index"]
               for pair in result["pairs"] if pair["pair_index"] in (0, 1, 5))
    assert result["source_maps"][4]["graph_id"] == 2026093905
    assert result["source_maps"][4]["source_lineage"]["source_matrix_index"] == 9

    with np.load(root / "diagnostics.npz", allow_pickle=False) as archive:
        vector_call_ids = archive["raw_vector_call_index"]
        vectors = archive["raw_x_hat"]
        assert len(vector_call_ids) == len(vectors) == 210
        vectors_by_call = {
            int(call_id): vector for call_id, vector in zip(vector_call_ids, vectors)
        }
        assert np.array_equal(vectors_by_call[1], _wrong_valid_vector(_truth()))
        assert np.array_equal(vectors_by_call[6], _truth())
        assert np.array_equal(vectors_by_call[10], _wrong_valid_vector(_truth()))
        failure_call_ids = [row["call_index"] for row in calls
                            if row["role"] == "baseline"
                            and row["pair_index"] in (2, 3, 4)]
        assert archive["belief_call_index"].tolist() == failure_call_ids
        assert archive["baseline_failure_belief_provenance"].tolist() == [
            "CHECK_UPDATED"] * 3
        assert archive["baseline_failure_beliefs"].shape == (3, 128, 32)
        assert archive["selector_call_index"].tolist() == failure_call_ids
        assert archive["selector_entropy_bits"].shape == (3, 128)
        assert archive["selector_active_mask"].shape == (3, 128)
        assert archive["source_graph_id"].tolist() == list(GRAPH_IDS)
        assert archive["source_constructor_matrix_index"][4] == 9
        assert archive["original_prior"].shape == (128, 32)
        assert archive["pair_truth"].shape == (192, 128)
        assert archive["pair_syndrome"].shape == (192, 52)
        assert archive["pair_candidate_selected_call_index"][2] == 6
        assert archive["pair_candidate_selected_call_index"][3] == 10
        assert archive["pair_candidate_selected_call_index"][4] == 16

    with (root / "frame_records.csv").open(
            encoding="utf-8", newline="") as stream:
        frame_rows = list(csv.DictReader(stream))
    assert len(frame_rows) == 210
    assert all("x_hat" not in row for row in frame_rows)
    persisted = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    assert persisted["status"] == "COMPLETE"
    assert persisted["disclosure_bits"] == 99_840


def test_fake_bad_source_stops_before_sampling_or_decode(tmp_path: Path):
    (tmp_path / "workspace").mkdir()
    adapters = _fake_batch_adapters(tmp_path, bad_source=True)
    state = adapters.pop("state")
    result = probe.execute_batch(out_root=probe.OUT_ROOT_RELATIVE, **adapters)

    assert result["status"] == "STOP"
    assert result["completed_pairs"] == 0
    assert result["attempted_physical_calls"] == 0
    assert result["control_exact"] is result["candidate_exact"] is None
    assert result["delta_exact"] is result["per_graph"] is result["paired"] is None
    assert state["source_reads"] == 1
    assert state["sampler_seeds"] == []
    assert state["decoder_inputs"] == []


def test_fake_bad_baseline_beliefs_stop_before_any_restart(tmp_path: Path):
    (tmp_path / "workspace").mkdir()
    adapters = _fake_batch_adapters(
        tmp_path, failure_pairs=(0,), bad_beliefs_pair=0)
    state = adapters.pop("state")
    result = probe.execute_batch(out_root=probe.OUT_ROOT_RELATIVE, **adapters)

    assert result["status"] == "STOP"
    assert result["attempted_physical_calls"] == result["baseline_calls"] == 1
    assert result["branch_calls"] == 0
    assert result["control_exact"] is result["candidate_exact"] is None
    assert state["sampler_seeds"] == [probe.build_seed_plan()[0][3]]
    assert [row["role"] for row in result["calls"]] == ["baseline"]
    assert result["calls"][0]["raw_vector_index"] == 0
    assert result["calls"][0]["x_hat"].shape == (128,)
    with np.load(Path(result["artifacts"]["diagnostics"]), allow_pickle=False) as archive:
        assert archive["raw_vector_call_index"].tolist() == [0]
        assert archive["belief_call_index"].size == 0


def test_fake_syndrome_mismatch_does_not_bypass_postreturn_call_cap(
        tmp_path: Path):
    (tmp_path / "workspace").mkdir()
    adapters = _fake_batch_adapters(
        tmp_path, failure_pairs=(), syndrome_mismatch_overrun_pair=0)
    state = adapters.pop("state")
    result = probe.execute_batch(out_root=probe.OUT_ROOT_RELATIVE, **adapters)
    manifest = json.loads(Path(result["artifacts"]["manifest"]).read_text(
        encoding="utf-8"))

    assert state["source_reads"] == 1
    assert len(state["sampler_seeds"]) == 1
    assert len(state["decoder_inputs"]) == 1
    assert result["status"] == "INCOMPLETE"
    assert result["attempted_physical_calls"] == 1
    assert result["resource_violations"] >= 1
    assert result["control_exact"] is result["candidate_exact"] is None
    assert result["delta_exact"] is result["paired"] is result["per_graph"] is None
    call = result["calls"][0]
    assert call["syndrome_valid"] is True
    assert call["syndrome_ok_reported"] is False
    assert call["wall_s"] > probe.CALL_CAP_S
    assert "decoder_syndrome_flag_mismatch" in result["stop_reasons"]
    assert "after_decoder_call:decoder_call_wall_cap_after_return" in manifest["resource_events"]
    assert manifest["summary"]["status"] == "INCOMPLETE"


def test_fake_branch_resource_stop_retains_partial_actual_calls_and_nulls_totals(
        tmp_path: Path):
    (tmp_path / "workspace").mkdir()
    adapters = _fake_batch_adapters(
        tmp_path, failure_pairs=(0,), branch_resource_pair=0)
    state = adapters.pop("state")
    result = probe.execute_batch(out_root=probe.OUT_ROOT_RELATIVE, **adapters)

    assert result["status"] == "INCOMPLETE"
    assert result["attempted_physical_calls"] == 2
    assert result["baseline_calls"] == result["branch_calls"] == 1
    assert result["resource_violations"] >= 1
    assert result["control_exact"] is result["candidate_exact"] is None
    assert result["delta_exact"] is result["paired"] is result["per_graph"] is None
    assert [row["role"] for row in result["calls"]] == ["baseline", "soft_prior"]
    assert result["calls"][1]["raw_vector_index"] == 1
    assert state["next_branch"] == 1  # stop before branch 1 is called
    with np.load(Path(result["artifacts"]["diagnostics"]), allow_pickle=False) as archive:
        assert archive["raw_vector_call_index"].tolist() == [0, 1]
        assert archive["belief_call_index"].tolist() == [0]
        assert archive["branch_score_call_index"].size == 0


def test_fake_terminal_write_overcap_nulls_full_comparison_and_logs_final_status(
        tmp_path: Path):
    (tmp_path / "workspace").mkdir()
    adapters = _fake_batch_adapters(
        tmp_path, failure_pairs=(), terminal_overrun=True)
    state = adapters.pop("state")
    result = probe.execute_batch(out_root=probe.OUT_ROOT_RELATIVE, **adapters)
    root = tmp_path / probe.OUT_ROOT_RELATIVE

    assert state["terminal_triggered"] is True
    assert result["status"] == "INCOMPLETE"
    assert result["completed_pairs"] == 192
    assert result["total_wall_s"] > probe.WALL_CAP_S
    assert result["control_exact"] is result["candidate_exact"] is None
    assert result["delta_exact"] is result["paired"] is result["per_graph"] is None
    assert result["classification"] == "INCOMPLETE"
    assert {path.name for path in root.iterdir()} == {
        "manifest.json", "summary.json", "frame_records.csv",
        "diagnostics.npz", "EXPLORATION_LOG.md",
    }
    log = (root / "EXPLORATION_LOG.md").read_text(encoding="utf-8")
    assert f"FINAL_STATUS=INCOMPLETE" in log
    persisted = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    assert persisted["status"] == "INCOMPLETE"
    assert persisted["delta_exact"] is None
