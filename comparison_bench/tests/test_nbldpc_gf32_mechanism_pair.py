"""Fake-only tests for the frozen rank2 and mixed05 GF(32) probes."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_mechanism_pair as probe
from comparison_bench.cli import nbldpc_gf32_softprior_rescue as rescue
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout


GRAPH_IDS = tuple(range(2026093901, 2026093907))
SOURCE_MATRIX_INDICES = (0, 2, 4, 6, 9, 11)
ATTEMPT_J = (0, 0, 0, 0, 1, 0)
CONSTRUCTION_SEEDS = (*GRAPH_IDS[:4], 2560859716, GRAPH_IDS[5])
CONSTRUCTION_UUID = "a9a18abe-3547-4d16-aa50-1f7150182f31"
CONSTRUCTION_PATH = "workspace/gf32_construct_a9a18abe/constructions.json"
GUESSES = (0, 1, 3, 7, 15, 31)


def _fake_control_matrix(graph_index: int) -> np.ndarray:
    """Build the accepted source's connected, degree-2-variable 52x128 shape."""
    edges = []
    for check in range(52):
        edges.extend(((check, (check + 1) % 52), (check, (check + 2) % 52)))
    edges.extend((check, check + 24) for check in range(4, 28))
    h = np.zeros((52, 128), dtype=np.int64)
    for column, (left, right) in enumerate(edges):
        h[(left + graph_index) % 52, column] = 1
        h[(right + graph_index) % 52, column] = 1
    assert np.all(np.count_nonzero(h, axis=0) == 2)
    assert sorted(np.count_nonzero(h, axis=1).tolist()) == [4] * 4 + [5] * 48
    return h


def _fake_source() -> dict[str, np.ndarray]:
    # Same accepted full source map, including deliberately shuffled physical rows.
    rows = [(profile, graph) for profile in range(2) for graph in range(6)]
    rows.reverse()
    graph_index = np.asarray([graph for _, graph in rows], dtype=np.int64)
    profile_index = np.asarray([profile for profile, _ in rows], dtype=np.int64)
    graph_ids = np.asarray([GRAPH_IDS[g] for g in graph_index], dtype=np.int64)
    source_matrix = [SOURCE_MATRIX_INDICES[g] if p == 0 else (1, 3, 5, 7, 10, 12)[g]
                     for p, g in rows]
    h_deep = np.stack([_fake_control_matrix(g) for _, g in rows])
    return {
        "batch_uuid": np.asarray([rescue.SOURCE_BATCH_UUID]),
        "contract": np.asarray([rescue.SOURCE_CONTRACT]),
        "seed_namespace": np.asarray([rescue.SOURCE_NAMESPACE]),
        "graph_input_kind": np.asarray([rescue.SOURCE_KIND]),
        "profile_order": np.asarray(["control", "candidate"]),
        "graph_seed": np.asarray(GRAPH_IDS, dtype=np.int64),
        "deep_profile_index": profile_index.copy(),
        "deep_graph_index": graph_index.copy(),
        "H_deep": h_deep,
        "constructor_profile_index": profile_index.copy(),
        "constructor_graph_index": graph_index.copy(),
        "constructor_source_uuid": np.asarray([CONSTRUCTION_UUID] * len(rows)),
        "constructor_source_path": np.asarray([CONSTRUCTION_PATH] * len(rows)),
        "constructor_source_matrix_index": np.asarray(source_matrix, dtype=np.int64),
        "constructor_source_attempt_j": np.asarray([ATTEMPT_J[g] for _, g in rows], dtype=np.int64),
        "constructor_source_seed": np.asarray([CONSTRUCTION_SEEDS[g] for _, g in rows], dtype=np.int64),
        "constructor_source_graph_id": graph_ids,
    }


def _truth() -> np.ndarray:
    vector = np.zeros(128, dtype=np.uint8)
    vector[127] = 1
    return vector


def _decode_result(h: np.ndarray, x_hat: np.ndarray, syndrome: np.ndarray,
                   *, beliefs: np.ndarray | None = None,
                   syndrome_ok: bool | None = None,
                   iterations: int = 7) -> SimpleNamespace:
    own_valid = np.array_equal(
        np.asarray(layout.gf32_syndrome(h, x_hat), dtype=np.int64).ravel(),
        np.asarray(syndrome, dtype=np.int64).ravel())
    return SimpleNamespace(
        x_hat=np.asarray(x_hat, dtype=np.uint8), iterations=iterations,
        runtime_s=0.001, status="fake", syndrome_ok=own_valid if syndrome_ok is None else syndrome_ok,
        final_beliefs=(np.zeros((128, 32), dtype=np.float64) if beliefs is None else beliefs),
        belief_provenance="CHECK_UPDATED",
    )


class FakeBatch:
    """Injected source, sampler, and v35-shaped fake decoders; never reads NPZ/BP."""

    def __init__(self, mechanism: str, *, failures: tuple[int, ...] = (0,),
                 branch_policy: str = "truth_first", valid_wrong: tuple[int, ...] = (),
                 mismatch_pair: int | None = None,
                 branch_outcomes: dict[tuple, object] | None = None,
                 truth_by_pair: dict[int, np.ndarray] | None = None,
                 bad_source: bool = False):
        self.mechanism = mechanism
        self.plan = probe.build_seed_plan(mechanism)
        self.pair_by_seed = {int(row[3]): index for index, row in enumerate(self.plan)}
        self.failures = set(failures)
        self.valid_wrong = set(valid_wrong)
        self.branch_policy = branch_policy
        self.mismatch_pair = mismatch_pair
        self.branch_outcomes = {} if branch_outcomes is None else branch_outcomes
        self.truth_by_pair = {} if truth_by_pair is None else truth_by_pair
        self.bad_source = bad_source
        self.source_reads = 0
        self.sampled_seeds: list[int] = []
        self.decoder_inputs: list[dict] = []
        self.branch_calls: dict[int, int] = {}
        self.current_pair = -1
        self.zero = np.zeros(128, dtype=np.uint8)
        self.truth = _truth()
        self.current_truth = self.truth.copy()
        self.original_prior = np.tile(rescue.pmf(), (128, 1))

    def source_reader(self):
        self.source_reads += 1
        source = _fake_source()
        if self.bad_source:
            source["batch_uuid"] = np.asarray(["wrong-source-uuid"])
        return source

    def sampler(self, seed, pmf, *, width):
        self.current_pair = self.pair_by_seed[int(seed)]
        self.current_truth = np.asarray(
            self.truth_by_pair.get(self.current_pair, self.truth), dtype=np.uint8).copy()
        self.sampled_seeds.append(int(seed))
        self.branch_calls[self.current_pair] = 0
        assert width == 128
        np.testing.assert_allclose(pmf, rescue.pmf(), rtol=0.0, atol=1e-15)
        return self.current_truth.copy()

    def _record(self, role, h, prior, syndrome, kwargs):
        self.decoder_inputs.append({
            "pair": self.current_pair, "role": role,
            "H": np.asarray(h).copy(), "prior": np.asarray(prior).copy(),
            "syndrome": np.asarray(syndrome).copy(), "kwargs": dict(kwargs),
        })

    def baseline(self, h, prior, syndrome, **kwargs):
        self._record("baseline", h, prior, syndrome, kwargs)
        if self.current_pair in self.failures:
            x_hat = self.zero
            iterations = 90
        elif self.current_pair in self.valid_wrong:
            x_hat = self._wrong_vector()
            iterations = 7
        else:
            x_hat = self.current_truth
            iterations = 7
        reported = None
        if self.current_pair == self.mismatch_pair:
            own = np.array_equal(layout.gf32_syndrome(h, x_hat), syndrome)
            reported = not bool(own)
        return _decode_result(h, x_hat, syndrome, iterations=iterations, syndrome_ok=reported)

    def _wrong_vector(self):
        wrong = self.current_truth.copy()
        # The first three columns form a GF(32) triangle null vector.
        wrong[:3] ^= np.uint8(1)
        return wrong

    def _outcome(self, value):
        if isinstance(value, np.ndarray):
            return np.asarray(value, dtype=np.uint8).copy()
        if value == "truth":
            return self.current_truth.copy()
        if value == "wrong":
            return self._wrong_vector()
        if value == "zero":
            return self.zero
        raise AssertionError(f"unknown fake branch outcome {value!r}")

    def soft_prior(self, h, prior, syndrome, **kwargs):
        self._record("soft_prior", h, prior, syndrome, kwargs)
        call_number = self.branch_calls[self.current_pair]
        self.branch_calls[self.current_pair] = call_number + 1
        if self.mechanism == "rank2":
            branch_index = call_number % 6
            phase = call_number // 6
            outcome = self.branch_outcomes.get((self.current_pair, phase, branch_index))
            if outcome is not None:
                x_hat = self._outcome(outcome)
            elif self.branch_policy == "rank2_success" and phase == 1 and branch_index == 0:
                x_hat = self.current_truth
            elif self.branch_policy == "rank1_valid" and phase == 0 and branch_index == 0:
                x_hat = self.current_truth
            else:
                x_hat = self.zero
        else:
            branch_index = call_number // 2
            is_candidate = (call_number % 2 == (1 if self.current_pair % 2 == 0 else 0))
            method = "candidate" if is_candidate else "control"
            outcome = self.branch_outcomes.get((self.current_pair, method, branch_index))
            if outcome is not None:
                x_hat = self._outcome(outcome)
            elif branch_index == 0:
                x_hat = self.current_truth
            else:
                x_hat = self.zero
            self.decoder_inputs[-1]["method"] = (
                "mixed05_candidate" if is_candidate else "onehot_control")
        return _decode_result(h, x_hat, syndrome, iterations=4 + branch_index)

    def decode_fns(self):
        return {"baseline": self.baseline, "soft_prior": self.soft_prior}

    def execute(self, out_root: Path, *, now=None, rss_fn=None):
        return probe.execute_batch(
            mechanism=self.mechanism, source_reader=self.source_reader,
            sampler=self.sampler, decode_fns=self.decode_fns(), out_root=probe.PROFILES[self.mechanism]["out_root"],
            repo_root=out_root, now=(lambda: 10.0) if now is None else now,
            rss_fn=(lambda: 100_000) if rss_fn is None else rss_fn,
            command=f"fake-only {self.mechanism}",
        )


@pytest.mark.parametrize("mechanism", ("rank2", "mixed05"))
def test_complete_192_fake_batch_and_shared_baseline(mechanism, tmp_path):
    failures = (0, 1) if mechanism == "mixed05" else (0,)
    fake = FakeBatch(mechanism, failures=failures, branch_policy="rank1_valid")
    result = fake.execute(tmp_path)

    assert result["status"] == "COMPLETE"
    assert result["planned_pairs"] == result["sampled_pairs"] == result["completed_pairs"] == 192
    assert result["baseline_calls"] == 192
    assert fake.source_reads == 1
    assert fake.sampled_seeds == [row[3] for row in fake.plan]
    assert result["attempted_physical_calls"] == (216 if mechanism == "mixed05" else 198)
    assert result["logical_control_calls"] == (204 if mechanism == "mixed05" else 198)
    assert result["logical_candidate_calls"] == (204 if mechanism == "mixed05" else 198)
    assert result["control_exact"] == result["candidate_exact"] == 192
    assert result["delta_exact"] == 0
    assert result["paired"] == {"both_exact": 192, "candidate_only": 0, "control_only": 0, "neither": 0}
    baseline_calls = [call for call in result["calls"] if call["role"] == "baseline"]
    assert len(baseline_calls) == 192
    assert result["baseline_exact"] == sum(bool(call["exact"]) for call in baseline_calls)
    assert result["baseline_exact"] == (190 if mechanism == "mixed05" else 191)
    assert len(fake.decoder_inputs) == result["attempted_physical_calls"]

    for call in fake.decoder_inputs:
        assert call["kwargs"] == {
            "max_iter": 90, "damping_alpha": 1.0, "warm_beliefs": None, "field": None,
        }
    # Baseline is shared once, then the two arms use retained call pointers.
    assert result["pairs"][2]["control_selected_call_index"] == result["pairs"][2]["baseline_call_index"]
    assert result["pairs"][2]["candidate_selected_call_index"] == result["pairs"][2]["baseline_call_index"]
    assert result["pairs"][0]["completed"] is True
    if mechanism == "rank2":
        assert result["pairs"][0]["rank2_attempted"] is False
        assert result["pairs"][0]["rank2_reason"] == "not_triggered_rank1_has_valid_branch"
        assert result["pairs"][0]["rank1_variable"] == min(
            result["pairs"][0]["selector_metadata"]["active_variable_columns"])
    else:
        frame_zero_roles = [call["role"] for call in result["calls"]
                            if call["pair_index"] == 0 and call["role"] != "baseline"]
        frame_one_roles = [call["role"] for call in result["calls"]
                           if call["pair_index"] == 1 and call["role"] != "baseline"]
        assert frame_zero_roles == [role for _ in GUESSES for role in ("onehot_control", "mixed05_candidate")]
        assert frame_one_roles == [role for _ in GUESSES for role in ("mixed05_candidate", "onehot_control")]
        assert [call["guess_symbol"] for call in result["calls"]
                if call["pair_index"] == 0 and call["role"] != "baseline"] == [
            guess for guess in GUESSES for _ in range(2)]
        assert [call["guess_symbol"] for call in result["calls"]
                if call["pair_index"] == 1 and call["role"] != "baseline"] == [
            guess for guess in GUESSES for _ in range(2)]
        candidate_inputs = [row for row in fake.decoder_inputs if row.get("method") == "mixed05_candidate"]
        assert len(candidate_inputs) == 12
        for row in candidate_inputs:
            selected = int(np.flatnonzero(np.any(row["prior"] != fake.original_prior, axis=1))[0])
            guess = int(row["prior"][selected].argmax())
            expected = 0.5 * fake.original_prior[selected]
            expected = expected.copy()
            expected[guess] += 0.5
            np.testing.assert_allclose(row["prior"][selected], expected, rtol=0.0, atol=1e-15)
            unchanged = np.arange(128) != selected
            np.testing.assert_array_equal(row["prior"][unchanged], fake.original_prior[unchanged])


@pytest.mark.parametrize(
    "mechanism,baseline,control,candidate,graph_deltas,expected",
    (
        (
            "mixed05", 144, 161, 153, (-1, -1, -1, -2, -1, -2),
            "INCREMENT_NOT_ESTABLISHED",
        ),
        (
            "mixed05", 150, 160, 166, (1, 1, 1, 1, 1, 1),
            "EXPLORATORY_INCREMENT_SIGNAL",
        ),
        (
            "rank2", 154, 165, 167, (1, 1, 0, 0, 0, 0),
            "CONTROL_RANGE_UNINFORMATIVE",
        ),
    ),
)
def test_classifier_uses_frozen_baseline_count_rule(
        mechanism, baseline, control, candidate, graph_deltas, expected):
    summary = {
        "baseline_exact": baseline,
        "control_exact": control,
        "candidate_exact": candidate,
        "delta_exact": candidate - control,
        "per_graph": {
            str(graph_id): {"delta_exact": delta}
            for graph_id, delta in zip(GRAPH_IDS, graph_deltas)
        },
        "syndrome_valid_wrong_control": 0,
        "syndrome_valid_wrong_candidate": 0,
    }

    assert probe._classification(mechanism, summary) == expected


@pytest.mark.parametrize("mechanism", ("rank2", "mixed05"))
def test_t0_seed_separation_and_dry_run_are_read_free(mechanism, tmp_path, monkeypatch):
    def forbidden_binding():
        raise AssertionError("T0/dry-run must not bind the production source or decoder")

    monkeypatch.setattr(probe, "_bind_production", forbidden_binding)
    t0 = probe.verify_t0(mechanism)
    dry = probe.dry_run(mechanism, repo_root=tmp_path)

    assert t0["status"] == "PASS"
    assert t0["holdout_pairs"] == 192
    assert t0["prior_exclusion_plan_count"] == 16
    assert t0["prior_exclusion_rows"] == 3408
    assert all(t0[key] == 0 for key in ("source_reads", "sampler_calls", "decoder_calls", "writes"))
    assert dry["status"] == "DRY_RUN"
    assert all(dry[key] == 0 for key in ("source_reads", "sampler_calls", "decoder_calls", "writes"))
    assert not (tmp_path / probe.PROFILES[mechanism]["out_root"]).exists()


def test_frozen_seed_plans_are_unique_historical_and_sister_disjoint():
    plans = {}
    for mechanism in ("rank2", "mixed05"):
        rows, exclusions = probe.validate_seed_plan(mechanism)
        seeds = [row[3] for row in rows]
        assert len(rows) == len(set((row[0], row[1], row[2]) for row in rows)) == 192
        assert len(seeds) == len(set(seeds)) == 192
        assert len(exclusions) == 16
        assert sum(int(row["rows"]) for row in exclusions) == 3408
        plans[mechanism] = set(seeds)
    assert plans["rank2"].isdisjoint(plans["mixed05"])


def test_rank2_trigger_selection_fallback_and_wrong_are_separate(tmp_path):
    # Pair 0: rank1 valid, so rank2 is forbidden. Pair 1: rank1 all fail,
    # rank2 branch 0 succeeds. Pair 3: all rank2 fail and baseline is retained.
    outcomes = {(0, 0, 0): "truth", (1, 1, 0): "truth"}
    fake = FakeBatch(
        "rank2", failures=(0, 1, 3), valid_wrong=(4,), branch_outcomes=outcomes)
    result = fake.execute(tmp_path)

    assert result["status"] == "COMPLETE"
    assert result["attempted_physical_calls"] == 222
    assert result["attempted_physical_calls"] <= probe.MAX_PHYSICAL_CALLS == 2496
    assert result["baseline_calls"] == 192
    assert result["logical_control_calls"] == 210
    assert result["logical_candidate_calls"] == 222
    assert (result["control_exact"], result["candidate_exact"], result["delta_exact"]) == (189, 190, 1)
    assert result["paired"] == {"both_exact": 189, "candidate_only": 1, "control_only": 0, "neither": 2}
    assert result["syndrome_valid_wrong_control"] == 1
    assert result["syndrome_valid_wrong_candidate"] == 1
    assert result["syndrome_failed_control"] == 2
    assert result["syndrome_failed_candidate"] == 1

    rank1_pass = result["pairs"][0]
    rank2_pass = result["pairs"][1]
    rank2_fail = result["pairs"][3]
    baseline_wrong = result["pairs"][4]
    assert rank1_pass["rank2_attempted"] is False
    assert rank1_pass["rank2_reason"] == "not_triggered_rank1_has_valid_branch"
    assert rank2_pass["rank2_attempted"] is True
    assert rank2_pass["rank2_reason"] == "rank2_valid_branch_selected"
    assert rank2_pass["rank2_variable"] == min(
        column for column in rank2_pass["selector_metadata"]["active_variable_columns"]
        if column != rank2_pass["rank1_variable"])
    assert rank2_pass["control_exact"] is False
    assert rank2_pass["candidate_exact"] is True
    selected_rank2 = result["calls"][rank2_pass["candidate_selected_call_index"]]
    assert selected_rank2["role"] == "rank2_onehot"
    assert rank2_fail["rank2_attempted"] is True
    assert rank2_fail["rank2_reason"] == "all_rank2_branches_syndrome_invalid_baseline_fallback"
    assert rank2_fail["control_selected_call_index"] == rank2_fail["baseline_call_index"]
    assert rank2_fail["candidate_selected_call_index"] == rank2_fail["baseline_call_index"]
    assert baseline_wrong["control_valid_wrong"] is True
    assert baseline_wrong["candidate_valid_wrong"] is True
    assert baseline_wrong["control_exact"] is False
    assert baseline_wrong["candidate_exact"] is False
    assert result["raw_valid_wrong_by_role"]["baseline"] == 1
    assert result["raw_valid_wrong_by_role"]["rank2_onehot"] == 0
    assert sum(row["n"] for row in result["per_graph"].values()) == 192
    assert sum(row["delta_exact"] for row in result["per_graph"].values()) == result["delta_exact"]


def test_rank2_no_second_active_variable_makes_no_rank2_calls(tmp_path, monkeypatch):
    metadata = {"active_variable_columns": [9], "entropy_bits": [0.0] * 128}
    assert probe.select_rank2_variable(metadata, 9) is None
    monkeypatch.setattr(probe, "select_rank2_variable", lambda _metadata, _rank1: None)
    fake = FakeBatch("rank2", failures=(0,))
    result = fake.execute(tmp_path)

    pair = result["pairs"][0]
    assert result["status"] == "COMPLETE"
    assert pair["rank2_attempted"] is True
    assert pair["rank2_variable"] == -1
    assert pair["rank2_reason"] == "triggered_no_second_active_variable"
    assert not any(call["role"] == "rank2_onehot" for call in result["calls"])
    assert result["attempted_physical_calls"] == 198


def test_original_prior_tie_is_lowest_branch_and_truth_blind(tmp_path):
    truth = _truth()
    base = truth.copy()
    alternate = truth.copy()
    base[:3] = 1
    alternate[6:9] = 1
    h = _fake_control_matrix(0)
    syndrome = layout.gf32_syndrome(h, truth)
    np.testing.assert_array_equal(layout.gf32_syndrome(h, base), syndrome)
    np.testing.assert_array_equal(layout.gf32_syndrome(h, alternate), syndrome)
    prior = np.tile(rescue.pmf(), (128, 1))
    selected, scores = rescue.select_soft_prior_branch(
        [
            {"call_index": 10, "branch_index": 0, "x_hat": base, "syndrome_valid": True},
            {"call_index": 11, "branch_index": 1, "x_hat": alternate, "syndrome_valid": True},
        ], prior)
    assert scores[0]["score"] == scores[1]["score"]
    assert selected == 10
    sampled_truth = alternate
    assert np.array_equal(alternate, sampled_truth)
    assert not np.array_equal(base, sampled_truth)

    fake = FakeBatch(
        "rank2", failures=(0,), branch_outcomes={(0, 0, 0): base, (0, 0, 1): alternate},
        truth_by_pair={0: alternate})
    result = fake.execute(tmp_path)
    pair = result["pairs"][0]
    assert pair["completed"] is True
    assert pair["control_selected_call_index"] == result["calls"][pair["control_selected_call_index"]]["call_index"]
    assert result["calls"][pair["control_selected_call_index"]]["branch_index"] == 0
    assert result["calls"][pair["control_selected_call_index"]]["score_original_prior"] == \
        result["calls"][pair["control_selected_call_index"] + 1]["score_original_prior"]
    assert result["calls"][pair["control_selected_call_index"] + 1]["exact"] is True
    assert pair["control_exact"] is False
    assert pair["candidate_exact"] is False
    assert all("truth" not in row for row in fake.decoder_inputs)


def test_mixed05_raw_prior_only_changes_selected_row_and_can_lose_exact(tmp_path):
    fake = FakeBatch(
        "mixed05", failures=(0,), valid_wrong=(1,),
        branch_outcomes={(0, "control", 0): "truth", (0, "candidate", 0): "wrong"})
    result = fake.execute(tmp_path)

    assert result["status"] == "COMPLETE"
    assert result["attempted_physical_calls"] == 204
    assert result["logical_control_calls"] == result["logical_candidate_calls"] == 198
    assert result["control_exact"] == 191
    assert result["candidate_exact"] == 190
    assert result["delta_exact"] == -1
    assert result["paired"] == {"both_exact": 190, "candidate_only": 0, "control_only": 1, "neither": 1}
    assert result["syndrome_valid_wrong_control"] == 1
    assert result["syndrome_valid_wrong_candidate"] == 2
    assert result["raw_valid_wrong_by_role"]["baseline"] == 1
    assert result["raw_valid_wrong_by_role"]["mixed05_candidate"] == 1
    assert int(bool(result["pairs"][0]["candidate_exact"])
               - bool(result["pairs"][0]["control_exact"])) == -1
    assert result["pairs"][1]["control_selected_call_index"] == result["pairs"][1]["baseline_call_index"]
    assert result["pairs"][1]["candidate_selected_call_index"] == result["pairs"][1]["baseline_call_index"]
    assert result["pairs"][1]["control_valid_wrong"] is True
    assert result["pairs"][1]["candidate_valid_wrong"] is True
    assert sum(row["candidate_exact"] for row in result["per_graph"].values()) == result["candidate_exact"]
    selected = result["calls"][result["pairs"][0]["candidate_selected_call_index"]]
    assert selected["role"] == "mixed05_candidate"
    assert selected["syndrome_valid_wrong"] is True
    with np.load(result["artifacts"]["diagnostics"]) as diagnostics:
        assert diagnostics["raw_x_hat"].shape == (204, 128)
        assert int(diagnostics["call_index"][result["pairs"][0]["candidate_selected_call_index"]]) == \
            result["pairs"][0]["candidate_selected_call_index"]


def test_source_and_reported_syndrome_mismatch_stop_with_null_totals(tmp_path):
    bad_source = FakeBatch("rank2", bad_source=True)
    source_result = bad_source.execute(tmp_path / "bad_source")
    assert source_result["status"] == "STOP"
    assert bad_source.source_reads == 1
    assert bad_source.sampled_seeds == []
    assert bad_source.decoder_inputs == []
    assert source_result["completed_pairs"] == 0
    assert source_result["baseline_exact"] is None
    assert source_result["control_exact"] is None
    assert source_result["candidate_exact"] is None

    mismatch = FakeBatch("rank2", failures=(), mismatch_pair=0)
    mismatch_result = mismatch.execute(tmp_path / "mismatch")
    assert mismatch_result["status"] == "STOP"
    assert mismatch_result["completed_pairs"] == 0
    assert mismatch_result["attempted_physical_calls"] == 1
    assert mismatch_result["baseline_exact"] is None
    assert mismatch_result["control_exact"] is None
    assert mismatch_result["candidate_exact"] is None
    assert "decoder_syndrome_flag_mismatch" in mismatch_result["stop_reasons"]
    assert mismatch_result["calls"][0]["status"] == "STOP"
    assert mismatch_result["calls"][0]["syndrome_valid"] is True
    assert mismatch_result["calls"][0]["syndrome_ok_reported"] is False


def test_existing_frozen_root_is_refused_before_any_fake_binding(tmp_path):
    fake = FakeBatch("rank2")
    root = tmp_path / probe.PROFILES["rank2"]["out_root"]
    root.mkdir(parents=True)
    with pytest.raises(FileExistsError):
        fake.execute(tmp_path)
    assert fake.source_reads == 0
    assert fake.sampled_seeds == []
    assert fake.decoder_inputs == []


@pytest.mark.parametrize("cap", ("wall", "rss"))
def test_wall_and_rss_caps_retain_returned_call_and_null_full_totals(cap, tmp_path, monkeypatch):
    fake = FakeBatch("rank2", failures=())
    clock = {"value": 0}
    rss_calls = {"value": 0}

    def step_clock():
        clock["value"] += 1
        return clock["value"] * 0.1

    def rss_fn():
        rss_calls["value"] += 1
        if cap == "rss" and rss_calls["value"] >= 4:
            return probe.RSS_CAP_BYTES + 1
        return 100_000

    if cap == "wall":
        monkeypatch.setattr(probe, "WALL_CAP_S", 0.4)
    result = fake.execute(tmp_path, now=step_clock, rss_fn=rss_fn)

    assert result["status"] == "INCOMPLETE"
    assert result["completed_pairs"] == 0
    assert result["sampled_pairs"] == 1
    assert result["attempted_physical_calls"] == 1
    assert result["baseline_exact"] is None
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    assert len(result["calls"]) == 1
    assert result["calls"][0]["x_hat"].shape == (128,)
    assert result["calls"][0]["status"] == "RESOURCE_STOP_AFTER_RETURN"
    assert any(reason in ";".join(result["stop_reasons"]) for reason in
               (("total_wall_cap",) if cap == "wall" else ("peak_rss_cap",)))
    assert Path(result["artifacts"]["diagnostics"]).exists()


def test_output_cap_keeps_first_pass_artifacts_but_nulls_full_totals(tmp_path, monkeypatch):
    def write_small_archive(path, arrays):
        np.savez_compressed(path, **arrays)
        return path.stat().st_size

    # Isolate the runner's post-write output-cap handling from the accepted
    # diagnostics writer's own payload-size guard.
    monkeypatch.setattr(probe, "ARTIFACT_CAP_BYTES", 1)
    monkeypatch.setattr(rescue, "_write_diagnostics", write_small_archive)
    result = FakeBatch("mixed05", failures=()).execute(tmp_path)
    assert result["output_bytes"] > probe.ARTIFACT_CAP_BYTES, (
        result["output_bytes"], probe.ARTIFACT_CAP_BYTES, result.get("resource_events"))
    assert result["status"] == "INCOMPLETE", (
        result["resource_violations"], result["stop_reasons"], result["completed_pairs"])
    assert result["completed_pairs"] == 192
    assert result["output_bytes"] > 1
    assert result["baseline_exact"] is None
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    assert result["delta_exact"] is None
    assert result["classification"] == "INCOMPLETE"
    assert Path(result["artifacts"]["diagnostics"]).exists()
    assert Path(result["artifacts"]["calls"]).exists()
    assert Path(result["artifacts"]["frames"]).exists()

