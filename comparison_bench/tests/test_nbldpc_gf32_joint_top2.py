"""Fake-only checks for the frozen GF(32) joint-top2 EXPLORE profile."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_mechanism_pair as probe
from comparison_bench.cli import nbldpc_gf32_softprior_cost_profile as cost_profile
from comparison_bench.cli import nbldpc_gf32_softprior_rescue as rescue
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from test_nbldpc_gf32_mechanism_pair import (
    GRAPH_IDS, GUESSES, _fake_source as _accepted_fake_source, _truth as _accepted_truth,
)


def _fake_source() -> dict[str, np.ndarray]:
    return _accepted_fake_source()


def _truth() -> np.ndarray:
    return _accepted_truth()


def _truth_with_null_triangle() -> np.ndarray:
    vector = _truth()
    vector[:3] = 1
    return vector


def _decode_result(h: np.ndarray, x_hat: np.ndarray, syndrome: np.ndarray,
                   *, beliefs: np.ndarray | None = None,
                   iterations: int = 7) -> SimpleNamespace:
    own_valid = np.array_equal(
        np.asarray(layout.gf32_syndrome(h, x_hat), dtype=np.int64).ravel(),
        np.asarray(syndrome, dtype=np.int64).ravel())
    return SimpleNamespace(
        x_hat=np.asarray(x_hat, dtype=np.uint8).copy(), iterations=iterations,
        runtime_s=0.001, status="fake", syndrome_ok=own_valid,
        final_beliefs=(np.zeros((128, 32), dtype=np.float64) if beliefs is None else beliefs),
        belief_provenance="CHECK_UPDATED",
    )


class FakeJointBatch:
    """Injected source, sampler and decoder callbacks; never opens source NPZ/BP."""

    def __init__(self, *, failures: tuple[int, ...] | range = (0, 1, 2),
                 outcomes: dict[tuple[int, str, int], str] | None = None,
                 truths: dict[int, np.ndarray] | None = None,
                 iterations: int = 7):
        self.plan = probe.build_seed_plan("jointtop2")
        self.pair_by_seed = {int(row[3]): index for index, row in enumerate(self.plan)}
        self.failures = set(failures)
        self.outcomes = {} if outcomes is None else outcomes
        self.truths = {} if truths is None else truths
        self.iterations = iterations
        self.current_pair = -1
        self.current_truth = _truth()
        self.zero = np.zeros(128, dtype=np.uint8)
        self.original_prior = np.tile(rescue.pmf(), (128, 1))
        self.source_reads = 0
        self.sampled_seeds: list[int] = []
        self.soft_branch_count: dict[int, int] = {}
        self.baseline_inputs: list[dict] = []
        self.soft_inputs: list[dict] = []

    def source_reader(self):
        self.source_reads += 1
        return _fake_source()

    def sampler(self, seed, pmf, *, width):
        self.current_pair = self.pair_by_seed[int(seed)]
        self.current_truth = np.asarray(
            self.truths.get(self.current_pair, _truth()), dtype=np.uint8).copy()
        self.sampled_seeds.append(int(seed))
        self.soft_branch_count[self.current_pair] = 0
        assert width == 128
        np.testing.assert_allclose(pmf, rescue.pmf(), rtol=0.0, atol=1e-15)
        return self.current_truth.copy()

    def baseline(self, h, prior, syndrome, **kwargs):
        self.baseline_inputs.append({
            "pair": self.current_pair, "prior": np.asarray(prior).copy(),
            "syndrome": np.asarray(syndrome).copy(), "kwargs": dict(kwargs),
        })
        x_hat = self.zero if self.current_pair in self.failures else self.current_truth
        return _decode_result(
            h, x_hat, syndrome, beliefs=np.zeros((128, 32), dtype=np.float64),
            iterations=(90 if self.current_pair in self.failures else self.iterations))

    def soft_prior(self, h, prior, syndrome, **kwargs):
        call_number = self.soft_branch_count[self.current_pair]
        self.soft_branch_count[self.current_pair] = call_number + 1
        phase, branch_index = (("rank1", call_number) if call_number < 6
                               else ("joint", call_number - 6))
        self.soft_inputs.append({
            "pair": self.current_pair, "phase": phase, "branch_index": branch_index,
            "prior": np.asarray(prior).copy(), "syndrome": np.asarray(syndrome).copy(),
            "kwargs": dict(kwargs),
        })
        outcome = self.outcomes.get((self.current_pair, phase, branch_index), "zero")
        if outcome == "truth":
            x_hat = self.current_truth
        elif outcome == "alternate":
            x_hat = _truth()
        else:
            x_hat = self.zero
        return _decode_result(h, x_hat, syndrome, iterations=self.iterations)

    def execute(self, repo_root: Path, *, now=None, rss_fn=None):
        return probe.execute_batch(
            mechanism="jointtop2", source_reader=self.source_reader,
            sampler=self.sampler,
            decode_fns={"baseline": self.baseline, "soft_prior": self.soft_prior},
            out_root=probe.JOINTTOP2_OUT_ROOT_RELATIVE, repo_root=repo_root,
            now=(lambda: 10.0) if now is None else now,
            rss_fn=(lambda: 100_000) if rss_fn is None else rss_fn,
            command="fake-only jointtop2",
        )


def test_t0_and_dry_run_are_read_free_and_write_free(tmp_path):
    t0 = probe.verify_t0("jointtop2")
    dry = probe.dry_run("jointtop2", repo_root=tmp_path)

    assert t0["status"] == "PASS"
    assert t0["holdout_pairs"] == 192
    assert t0["prior_exclusion_plan_count"] == 17
    assert t0["prior_exclusion_rows"] == 3600
    assert all(t0[key] == 0 for key in ("source_reads", "sampler_calls", "decoder_calls", "writes"))
    assert dry["status"] == "DRY_RUN"
    assert all(dry[key] == 0 for key in ("source_reads", "sampler_calls", "decoder_calls", "writes"))
    assert dry["t0"]["status"] == "PASS"
    assert not Path(dry["out_root"]).exists()


def test_supported_top_two_probability_ties_are_stable_at_one_e_minus_12():
    beliefs = np.zeros((128, 32), dtype=np.float64)
    beliefs[7, 1] = 1e-12
    ranking, probabilities = cost_profile.rank_allowed_guesses(beliefs, 7)

    assert 0.0 < probabilities[1] - probabilities[0] <= 1e-12
    assert ranking[:2] == [0, 1]


@pytest.mark.parametrize(
    "baseline,control,candidate,graph_deltas,expected",
    (
        (144, 161, 153, (-1, -1, -1, -2, -1, -2), "INCREMENT_NOT_ESTABLISHED"),
        (154, 144, 150, (2, 2, 1, 1, 0, 0), "CONTROL_RANGE_UNINFORMATIVE"),
    ),
)
def test_jointtop2_classifier_gates_on_baseline_exact(
        baseline, control, candidate, graph_deltas, expected):
    summary = {
        "baseline_exact": baseline, "control_exact": control,
        "candidate_exact": candidate, "delta_exact": candidate - control,
        "per_graph": {
            str(graph_id): {"delta_exact": delta}
            for graph_id, delta in zip(GRAPH_IDS, graph_deltas)
        },
        "syndrome_valid_wrong_control": 0,
        "syndrome_valid_wrong_candidate": 0,
    }

    assert probe._classification("jointtop2", summary) == expected


def test_complete_fake_checks_trigger_order_priors_blind_choice_and_costs(tmp_path):
    truths = {0: _truth_with_null_triangle(), 1: _truth_with_null_triangle()}
    outcomes = {
        (0, "rank1", 0): "truth", (0, "rank1", 1): "alternate",
        (1, "joint", 0): "truth", (1, "joint", 1): "alternate",
    }
    fake = FakeJointBatch(failures=(0, 1, 2), outcomes=outcomes, truths=truths)
    result = fake.execute(tmp_path)

    assert result["status"] == "COMPLETE"
    assert result["planned_pairs"] == result["sampled_pairs"] == result["completed_pairs"] == 192
    assert fake.source_reads == 1
    assert fake.sampled_seeds == [row[3] for row in fake.plan]
    baseline_calls = [row for row in result["calls"] if row["role"] == "baseline"]
    assert len(baseline_calls) == result["baseline_calls"] == 192
    assert result["baseline_exact"] == sum(bool(row["exact"]) for row in baseline_calls) == 189

    # F=3 baseline failures, G=2 all-rank1-fail frames with a second variable.
    assert result["attempted_physical_calls"] == 192 + 6 * 3 + 4 * 2 == 218
    assert result["branch_calls"] == 26
    assert result["logical_control_calls"] == 192 + 6 * 3 == 210
    assert result["logical_candidate_calls"] == 210 + 4 * 2 == 218
    assert result["attempted_physical_calls"] <= probe.JOINTTOP2_MAX_PHYSICAL_CALLS == 2112
    assert result["physical_decoder_iterations"] <= 190_080
    assert result["disclosure_bits_physical_batch"] == 192 * 260 == 49_920
    assert result["syndrome_bits_per_method_frame"] == 260
    assert result["internal_branch_disclosure_bits"] == result["tag_bits"] == 0
    assert result["verification"] == "NOT_IMPLEMENTED"
    assert result["undetected"] == "NOT_MEASURED"

    pair0, pair1, pair2, pair3 = result["pairs"][:4]
    assert pair0["candidate_selected_call_index"] == pair0["control_selected_call_index"]
    assert pair0["candidate_exact"] is False
    assert pair0["candidate_valid_wrong"] is True
    assert pair1["control_selected_call_index"] == pair1["baseline_call_index"]
    assert pair1["candidate_incremental_branch_calls"] == 4
    assert pair1["candidate_exact"] is False
    assert pair1["candidate_valid_wrong"] is True
    assert pair2["rank2_reason"] == "all_jointtop2_branches_syndrome_invalid_baseline_fallback"
    assert pair2["candidate_selected_call_index"] == pair2["baseline_call_index"]
    assert pair2["candidate_syndrome_failed"] is True
    assert pair3["candidate_selected_call_index"] == pair3["baseline_call_index"]
    assert pair3["control_selected_call_index"] == pair3["baseline_call_index"]

    pair1_joint = [row for row in result["calls"]
                   if row["pair_index"] == 1 and row["role"] == "jointtop2_candidate"]
    assert len(pair1_joint) == 4
    assert [row["branch_index"] for row in pair1_joint] == [0, 1, 2, 3]
    assert [(row["guess_symbol"], row["secondary_guess_symbol"]) for row in pair1_joint] == [
        (0, 0), (0, 1), (1, 0), (1, 1),
    ]
    active = pair1["selector_metadata"]["active_variable_columns"]
    entropy = pair1["selector_metadata"]["entropy_bits"]
    assert pair1["rank1_variable"] == min(active)
    assert pair1["rank2_variable"] == min(column for column in active
                                           if column != pair1["rank1_variable"])
    assert pair1["rank1_variable"] != pair1["rank2_variable"]
    assert max(entropy[column] for column in active) - min(entropy[column] for column in active) <= 1e-12
    assert pair1["arm_order"] == "rank1_then_conditional_jointtop2"

    # The original-prior score prefers the wrong one-symbol vector over a valid
    # exact four-symbol vector. Truth is therefore not the joint selector.
    joint_truth, joint_wrong = pair1_joint[:2]
    assert joint_truth["exact"] is True and joint_wrong["exact"] is False
    assert joint_wrong["score_original_prior"] > joint_truth["score_original_prior"]
    assert pair1["candidate_selected_call_index"] == joint_wrong["call_index"]
    assert result["calls"][pair0["candidate_selected_call_index"]]["role"] == "rank1_onehot"
    assert result["classification"] == "CONTROL_RANGE_UNINFORMATIVE"

    # Each joint call changes exactly two distinct raw-prior rows to one-hot;
    # rank1 calls change one row. All remaining rows preserve the original PMF.
    original = fake.original_prior
    p0_calls = [row for row in result["calls"]
                if row["pair_index"] == 0 and row["role"] == "rank1_onehot"]
    p0_inputs = [row for row in fake.soft_inputs if row["pair"] == 0 and row["phase"] == "rank1"]
    assert len(p0_calls) == len(p0_inputs) == 6
    for call, decoder_input in zip(p0_calls, p0_inputs):
        variable = int(call["selected_variable"])
        expected = original.copy()
        expected[variable] = 0.0
        expected[variable, int(call["guess_symbol"])] = 1.0
        np.testing.assert_array_equal(decoder_input["prior"], expected)
        assert np.count_nonzero(np.any(decoder_input["prior"] != original, axis=1)) == 1

    joint_inputs = [row for row in fake.soft_inputs if row["pair"] == 1 and row["phase"] == "joint"]
    assert len(joint_inputs) == 4
    for call, decoder_input in zip(pair1_joint, joint_inputs):
        expected = original.copy()
        expected[pair1["rank1_variable"]] = 0.0
        expected[pair1["rank1_variable"], int(call["guess_symbol"])] = 1.0
        expected[pair1["rank2_variable"]] = 0.0
        expected[pair1["rank2_variable"], int(call["secondary_guess_symbol"])] = 1.0
        np.testing.assert_array_equal(decoder_input["prior"], expected)
        assert np.count_nonzero(np.any(decoder_input["prior"] != original, axis=1)) == 2
    for row in fake.baseline_inputs:
        np.testing.assert_array_equal(row["prior"], original)
        assert row["kwargs"] == {
            "max_iter": 90, "damping_alpha": 1.0, "warm_beliefs": None, "field": None,
        }


def test_all_six_rank1_failures_without_second_variable_skip_joint_calls(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "select_rank2_variable", lambda _metadata, _rank1: None)
    result = FakeJointBatch(failures=(0,)).execute(tmp_path)

    pair = result["pairs"][0]
    assert result["status"] == "COMPLETE"
    assert pair["rank2_attempted"] is True
    assert pair["rank2_variable"] == -1
    assert pair["rank2_reason"] == "triggered_no_second_active_variable"
    assert pair["candidate_selected_call_index"] == pair["baseline_call_index"]
    assert not any(row["role"] == "jointtop2_candidate" for row in result["calls"])
    assert result["attempted_physical_calls"] == 192 + 6 == 198


def test_jointtop2_worst_case_matches_frozen_2112_call_and_iteration_budget(tmp_path):
    result = FakeJointBatch(failures=range(192), iterations=90).execute(tmp_path)

    assert result["status"] == "COMPLETE"
    assert result["baseline_calls"] == 192
    assert result["branch_calls"] == 192 * 10
    assert result["attempted_physical_calls"] == 192 + 192 * 6 + 192 * 4 == 2112
    assert result["attempted_physical_calls"] == probe.JOINTTOP2_MAX_PHYSICAL_CALLS
    assert result["logical_control_calls"] == 192 + 192 * 6 == 1344
    assert result["logical_candidate_calls"] == 192 + 192 * 6 + 192 * 4 == 2112
    assert result["physical_decoder_iterations"] == 2112 * 90 == 190_080


@pytest.mark.parametrize("cap", ("wall", "rss"))
def test_wall_and_rss_partial_batches_keep_full_totals_null(cap, tmp_path, monkeypatch):
    fake = FakeJointBatch(failures=())
    clock = {"ticks": 0}
    rss_calls = {"count": 0}

    def step_clock():
        clock["ticks"] += 1
        return 0.1 * clock["ticks"]

    def rss_fn():
        rss_calls["count"] += 1
        if cap == "rss" and rss_calls["count"] >= 4:
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
    assert result["delta_exact"] is None
    assert result["per_graph"] is None
    assert result["classification"] == "INCOMPLETE"


def test_output_cap_keeps_partial_artifacts_and_null_totals(tmp_path, monkeypatch):
    def write_small_archive(path, arrays):
        np.savez_compressed(path, **arrays)
        return path.stat().st_size

    monkeypatch.setattr(probe, "ARTIFACT_CAP_BYTES", 1)
    monkeypatch.setattr(rescue, "_write_diagnostics", write_small_archive)
    result = FakeJointBatch(failures=()).execute(tmp_path)

    assert result["status"] == "INCOMPLETE"
    assert result["completed_pairs"] == 192
    assert result["baseline_exact"] is None
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    assert result["delta_exact"] is None
    assert result["classification"] == "INCOMPLETE"
    assert Path(result["artifacts"]["diagnostics"]).exists()
    assert Path(result["artifacts"]["calls"]).exists()
    assert Path(result["artifacts"]["frames"]).exists()
