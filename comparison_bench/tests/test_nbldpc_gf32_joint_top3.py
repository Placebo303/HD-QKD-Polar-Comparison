"""Fake-only readiness checks for the frozen GF(32) jointtop3 profile."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_mechanism_pair as probe
from comparison_bench.cli import nbldpc_gf32_softprior_cost_profile as cost_profile
from comparison_bench.cli import nbldpc_gf32_softprior_rescue as rescue
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from test_nbldpc_gf32_mechanism_pair import _decode_result, _fake_source, _truth


J2_BRANCHES = (0, 1, 3, 4)
ADDED_FIVE = (2, 5, 6, 7, 8)


def _codeword_truth() -> np.ndarray:
    """Use the accepted fake source's three-edge cycle as a tiny codeword."""
    truth = np.zeros(128, dtype=np.uint8)
    truth[:3] = 1
    return truth


def _invalid_vector(h: np.ndarray, truth: np.ndarray, syndrome: np.ndarray) -> np.ndarray:
    for column in range(truth.size):
        candidate = truth.copy()
        candidate[column] = (int(candidate[column]) + 1) % 32
        if not np.array_equal(
                np.asarray(layout.gf32_syndrome(h, candidate), dtype=np.int64).ravel(),
                np.asarray(syndrome, dtype=np.int64).ravel()):
            return candidate
    raise AssertionError("the fake graph must admit a one-symbol syndrome-invalid vector")


class FakeJointTop3Batch:
    """Explicit source, sampler and decoder seams; never opens source NPZ or runs BP."""

    def __init__(self, *, failures: tuple[int, ...] | range = (),
                 outcomes: dict[tuple[int, str, int], str] | None = None,
                 truths: dict[int, np.ndarray] | None = None,
                 iterations_override: int | None = None,
                 reported_mismatch: tuple[int, str, int] | None = None):
        self.plan = probe.build_seed_plan("jointtop3")
        self.pair_by_seed = {int(row[3]): index for index, row in enumerate(self.plan)}
        self.failures = set(failures)
        self.outcomes = {} if outcomes is None else outcomes
        self.truths = {} if truths is None else truths
        self.iterations_override = iterations_override
        self.reported_mismatch = reported_mismatch
        self.current_pair = -1
        self.current_truth = _truth().copy()
        self.zero = np.zeros(128, dtype=np.uint8)
        self.original_prior = np.tile(rescue.pmf(), (128, 1))
        self.source_reads = 0
        self.sampler_calls = 0
        self.decoder_calls = 0
        self.sampled_seeds: list[int] = []
        self.soft_branch_count: dict[int, int] = {}
        self.baseline_inputs: list[dict] = []
        self.soft_inputs: list[dict] = []

    def source_reader(self):
        self.source_reads += 1
        return _fake_source()

    def sampler(self, seed, pmf, *, width):
        self.sampler_calls += 1
        self.current_pair = self.pair_by_seed[int(seed)]
        self.current_truth = np.asarray(
            self.truths.get(self.current_pair, _truth()), dtype=np.uint8).copy()
        self.sampled_seeds.append(int(seed))
        self.soft_branch_count[self.current_pair] = 0
        assert width == 128
        np.testing.assert_allclose(pmf, rescue.pmf(), rtol=0.0, atol=1e-15)
        return self.current_truth.copy()

    def baseline(self, h, prior, syndrome, **kwargs):
        self.decoder_calls += 1
        self.baseline_inputs.append({
            "pair": self.current_pair, "H": np.asarray(h).copy(),
            "prior": np.asarray(prior).copy(),
            "syndrome": np.asarray(syndrome).copy(), "kwargs": dict(kwargs),
        })
        x_hat = (_invalid_vector(h, self.current_truth, syndrome)
                 if self.current_pair in self.failures else self.current_truth.copy())
        iterations = (self.iterations_override if self.iterations_override is not None
                      else (90 if self.current_pair in self.failures else 2))
        beliefs = np.zeros((128, 32), dtype=np.float64)
        return _decode_result(h, x_hat, syndrome, beliefs=beliefs, iterations=iterations)

    def soft_prior(self, h, prior, syndrome, **kwargs):
        self.decoder_calls += 1
        call_number = self.soft_branch_count[self.current_pair]
        self.soft_branch_count[self.current_pair] = call_number + 1
        phase, branch_index = ("rank1", call_number) if call_number < 6 else (
            "jointtop3", call_number - 6)
        input_row = {
            "pair": self.current_pair, "phase": phase,
            "branch_index": branch_index, "H": np.asarray(h).copy(),
            "prior": np.asarray(prior).copy(),
            "syndrome": np.asarray(syndrome).copy(), "kwargs": dict(kwargs),
        }
        self.soft_inputs.append(input_row)

        outcome = self.outcomes.get((self.current_pair, phase, branch_index), "invalid")
        if outcome == "truth":
            x_hat = self.current_truth.copy()
        elif outcome == "wrong_zero":
            x_hat = self.zero.copy()
        elif outcome == "alternate":
            alternate = self.current_truth.copy()
            alternate[:3] = 1 - alternate[:3]
            x_hat = alternate
        elif outcome == "invalid":
            x_hat = _invalid_vector(h, self.current_truth, syndrome)
        else:
            raise AssertionError(f"unknown fake outcome: {outcome}")

        own_valid = np.array_equal(
            np.asarray(layout.gf32_syndrome(h, x_hat), dtype=np.int64).ravel(),
            np.asarray(syndrome, dtype=np.int64).ravel())
        mismatch_key = (self.current_pair, phase, branch_index)
        reported = (not own_valid if mismatch_key == self.reported_mismatch else None)
        iterations = (self.iterations_override if self.iterations_override is not None
                      else (branch_index + 1 if phase == "rank1" else 10 + branch_index))
        return _decode_result(
            h, x_hat, syndrome, iterations=iterations,
            syndrome_ok=reported,
        )

    def execute(self, repo_root: Path, *, out_root=None, now=None, rss_fn=None):
        return probe.execute_batch(
            mechanism="jointtop3", source_reader=self.source_reader,
            sampler=self.sampler,
            decode_fns={"baseline": self.baseline, "soft_prior": self.soft_prior},
            out_root=(probe.PROFILES["jointtop3"]["out_root"]
                      if out_root is None else out_root),
            repo_root=repo_root,
            now=(lambda: 10.0) if now is None else now,
            rss_fn=(lambda: 100_000) if rss_fn is None else rss_fn,
            command="fake-only jointtop3",
        )


def _joint_calls(result, pair_index: int):
    return [row for row in result["calls"]
            if row["pair_index"] == pair_index and row["role"] == "jointtop3_candidate"]


def test_a6_t0_dry_run_and_seed_exclusions_are_read_free(tmp_path):
    t0 = probe.verify_t0("jointtop3")
    dry = probe.dry_run("jointtop3", repo_root=tmp_path)
    rows, records = probe.validate_seed_plan("jointtop3")

    assert t0["status"] == "PASS"
    assert t0["holdout_pairs"] == 192
    assert t0["prior_exclusion_plan_count"] == 22
    assert t0["prior_exclusion_rows"] == 4560
    assert all(t0[key] == 0 for key in ("source_reads", "sampler_calls", "decoder_calls", "writes"))
    assert dry["status"] == "DRY_RUN"
    assert dry["t0"]["status"] == "PASS"
    assert all(dry[key] == 0 for key in ("source_reads", "sampler_calls", "decoder_calls", "writes"))
    assert not Path(dry["out_root"]).exists()
    assert len(rows) == len({row[3] for row in rows}) == 192
    assert len(records) == 22
    assert sum(int(row["rows"]) for row in records) == 4560

    names = {str(row["generator"]) for row in records}
    for fragment in (
            "jointtop2-v1", "jointcheck2-v1", "top3-runtime-v1",
            "edge-state-v1", "edge-state-r2-v1", "rank2-fallback-v1", "mixed05-v1"):
        assert any(fragment in name for name in names)

    fresh_seeds = {int(row[3]) for row in rows}
    excluded_seeds: set[int] = set()
    for _name, plan, expected_count in rescue._prior_seed_plans():
        seeds = set(rescue._seeds_from_plan(plan))
        assert len(seeds) == expected_count
        assert not (fresh_seeds & seeds)
        excluded_seeds.update(seeds)
    for _name, plan in probe._additional_excluded_plans("jointtop3"):
        seeds = {int(row[3]) for row in plan}
        assert len(seeds) == 192
        assert not (fresh_seeds & seeds)
        excluded_seeds.update(seeds)
    assert len(excluded_seeds) == 4560
    assert not (fresh_seeds & excluded_seeds)


def test_a1_complete_192_fake_baseline_and_rank1_pass_through(tmp_path):
    fake = FakeJointTop3Batch(failures=(1,), outcomes={(1, "rank1", 0): "truth"})
    result = fake.execute(tmp_path)

    assert result["status"] == "COMPLETE"
    assert result["planned_pairs"] == result["sampled_pairs"] == result["completed_pairs"] == 192
    assert fake.source_reads == 1 and fake.sampler_calls == 192
    assert len(fake.sampled_seeds) == len(set(fake.sampled_seeds)) == 192
    assert fake.sampled_seeds == [row[3] for row in fake.plan]
    assert result["attempted_physical_calls"] == 192 + 6 == 198
    assert result["baseline_calls"] == 192
    assert result["logical_control_calls"] == result["logical_candidate_calls"] == 198
    assert result["logical_derived_j2_calls"] == 198
    assert not any(row["role"] == "jointtop3_candidate" for row in result["calls"])

    pair0, pair1 = result["pairs"][:2]
    assert pair0["baseline_call_index"] == pair0["control_selected_call_index"]
    assert pair0["candidate_selected_call_index"] == pair0["baseline_call_index"]
    assert pair0["derived_j2_selected_call_index"] == pair0["baseline_call_index"]
    assert pair1["control_selected_call_index"] != pair1["baseline_call_index"]
    assert pair1["candidate_selected_call_index"] == pair1["control_selected_call_index"]
    assert pair1["derived_j2_selected_call_index"] == pair1["control_selected_call_index"]
    assert pair1["rank2_reason"] == "not_triggered_rank1_has_valid_branch"


def test_a1_all_six_invalid_without_second_variable_skips_jointtop3(
        tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "select_rank2_variable", lambda _metadata, _rank1: None)
    fake = FakeJointTop3Batch(failures=(0,))
    result = fake.execute(tmp_path)

    pair0 = result["pairs"][0]
    assert result["status"] == "COMPLETE"
    assert pair0["rank2_attempted"] is True
    assert pair0["rank2_variable"] == -1
    assert pair0["rank2_reason"] == "triggered_no_second_active_variable"
    assert pair0["candidate_selected_call_index"] == pair0["baseline_call_index"]
    assert pair0["derived_j2_selected_call_index"] == pair0["baseline_call_index"]
    assert result["attempted_physical_calls"] == 192 + 6
    assert not any(row["role"] == "jointtop3_candidate" for row in result["calls"])


def test_a2_a3_a4_nine_branches_derived_j2_blind_selection_and_accounting(tmp_path):
    codeword = _codeword_truth()
    outcomes = {
        # The first frame's only valid output is new branch 2: J3 gains over J2.
        (0, "jointtop3", 2): "truth",
        # The second frame's J2 exact branch loses J3's original-prior score
        # contest to a higher-probability valid-wrong vector on new branch 2.
        (1, "jointtop3", 0): "truth",
        (1, "jointtop3", 2): "wrong_zero",
    }
    fake = FakeJointTop3Batch(
        failures=(0, 1), outcomes=outcomes,
        truths={0: codeword, 1: codeword},
    )
    result = fake.execute(tmp_path)

    assert result["status"] == "COMPLETE"
    assert result["planned_pairs"] == result["sampled_pairs"] == result["completed_pairs"] == 192
    assert fake.source_reads == 1 and fake.sampler_calls == 192
    assert result["attempted_physical_calls"] == 192 + 6 * 2 + 9 * 2 == 222
    assert result["logical_control_calls"] == 192 + 6 * 2 == 204
    assert result["logical_candidate_calls"] == 204 + 9 * 2 == 222
    assert result["logical_derived_j2_calls"] == 204 + 4 * 2 == 212

    # Every conditional candidate runs the complete fixed 3 x 3 product.
    pair0_joint = _joint_calls(result, 0)
    pair1_joint = _joint_calls(result, 1)
    expected_pairs = [(a, b) for a in (0, 1, 3) for b in (0, 1, 3)]
    assert len(pair0_joint) == len(pair1_joint) == 9
    for pair, joint in zip(result["pairs"][:2], (pair0_joint, pair1_joint)):
        assert [row["branch_index"] for row in joint] == list(range(9))
        assert [(row["guess_symbol"], row["secondary_guess_symbol"]) for row in joint] == expected_pairs
        assert len({(row["selected_variable"], row["secondary_variable"]) for row in joint}) == 1
        primary, secondary = joint[0]["selected_variable"], joint[0]["secondary_variable"]
        assert primary != secondary
        assert pair["rank1_variable"] == primary
        assert pair["rank2_variable"] == secondary
        metadata = pair["selector_metadata"]
        active = metadata["active_variable_columns"]
        entropy = metadata["entropy_bits"]
        assert primary == min(c for c in active if max(entropy[x] for x in active) - entropy[c] <= 1e-12)
        remaining = [c for c in active if c != primary]
        assert secondary == min(c for c in remaining
                               if max(entropy[x] for x in remaining) - entropy[c] <= 1e-12)

    # Uniform fake baseline beliefs tie the supported softmax probabilities;
    # lower symbols win each 1e-12 tie, and canonical index is 3*i+j.
    tied_beliefs = np.zeros((128, 32), dtype=np.float64)
    tied_beliefs[7, 1] = 1e-12
    ranking, probabilities = cost_profile.rank_allowed_guesses(tied_beliefs, 7)
    assert 0.0 < probabilities[1] - probabilities[0] <= cost_profile.TIE_TOL
    assert ranking[:3] == [0, 1, 3]
    assert probe.build_jointtop3_branch_plan(ranking, ranking) == [
        (3 * i + j, a, b) for i, a in enumerate((0, 1, 3))
        for j, b in enumerate((0, 1, 3))
    ]

    # Each two-row branch is a cold one-hot edit of the same raw prior.
    for pair_index, joint in ((0, pair0_joint), (1, pair1_joint)):
        inputs = [row for row in fake.soft_inputs
                  if row["pair"] == pair_index and row["phase"] == "jointtop3"]
        assert len(inputs) == 9
        pair = result["pairs"][pair_index]
        for call, decoder_input in zip(joint, inputs):
            expected_prior = fake.original_prior.copy()
            expected_prior[call["selected_variable"]] = 0.0
            expected_prior[call["selected_variable"], call["guess_symbol"]] = 1.0
            expected_prior[call["secondary_variable"]] = 0.0
            expected_prior[call["secondary_variable"], call["secondary_guess_symbol"]] = 1.0
            np.testing.assert_array_equal(decoder_input["prior"], expected_prior)
            assert np.count_nonzero(np.any(decoder_input["prior"] != fake.original_prior, axis=1)) == 2
            assert decoder_input["kwargs"] == {
                "max_iter": 90, "damping_alpha": 1.0,
                "warm_beliefs": None, "field": None,
            }
            assert call["status"] == "COMPLETE"

    assert all(row["kwargs"] == {
        "max_iter": 90, "damping_alpha": 1.0,
        "warm_beliefs": None, "field": None,
    } for row in fake.baseline_inputs)

    # J2 is selected independently from physically shared calls at {0,1,3,4}.
    for pair_index, joint in ((0, pair0_joint), (1, pair1_joint)):
        pair = result["pairs"][pair_index]
        j2_calls = [row for row in joint if row["branch_index"] in J2_BRANCHES]
        assert pair["jointtop3_call_indices"] == [row["call_index"] for row in joint]
        assert pair["derived_j2_call_indices"] == [row["call_index"] for row in j2_calls]
        assert len(pair["derived_j2_call_indices"]) == 4
        selected_id = pair["derived_j2_selected_call_index"]
        selected_call = result["calls"][selected_id]
        assert pair["derived_j2_selected_branch_index"] == selected_call["branch_index"]
        assert (selected_id in pair["derived_j2_call_indices"]
                or selected_id == pair["baseline_call_index"])
        assert selected_call["call_index"] == selected_id
        assert selected_call["selected_for_derived_j2"] is True

    p0 = result["pairs"][0]
    assert p0["candidate_selected_call_index"] == pair0_joint[2]["call_index"]
    assert p0["j3_selected_branch_index"] == 2
    assert p0["candidate_exact"] is True
    assert p0["derived_j2_selected_call_index"] == p0["baseline_call_index"]
    assert p0["derived_j2_syndrome_failed"] is True
    np.testing.assert_array_equal(
        result["calls"][p0["candidate_selected_call_index"]]["x_hat"], codeword)

    p1 = result["pairs"][1]
    assert p1["derived_j2_selected_branch_index"] == 0
    assert p1["derived_j2_exact"] is True
    assert p1["candidate_selected_call_index"] == pair1_joint[2]["call_index"]
    assert p1["j3_selected_branch_index"] == 2
    assert p1["candidate_exact"] is False
    assert p1["candidate_valid_wrong"] is True
    assert result["calls"][pair1_joint[2]["call_index"]]["score_original_prior"] > pair1_joint[0]["score_original_prior"]
    np.testing.assert_array_equal(
        result["calls"][p1["derived_j2_selected_call_index"]]["x_hat"], codeword)
    np.testing.assert_array_equal(
        result["calls"][p1["candidate_selected_call_index"]]["x_hat"], np.zeros(128, dtype=np.uint8))
    assert result["j3_added_five_wins"] == 1
    assert result["j3_added_five_losses"] == 1
    assert result["raw_valid_wrong_control"] == 0
    assert result["raw_valid_wrong_j3"] == 1
    assert result["raw_valid_wrong_derived_j2"] == 0
    assert result["paired_j3_vs_derived_j2"] == {
        "both_exact": 190, "j3_only": 1, "derived_j2_only": 1, "neither": 0,
    }

    # Shared prefixes count once physically and in both logical views; each view
    # then accrues only its own branch set, including actual returned iterations.
    calls = result["calls"]
    physical_iterations = sum(int(row["iterations"]) for row in calls)
    prefix = [row for row in calls if row["role"] in ("baseline", "rank1_onehot")]
    j3_joint = [row for row in calls if row["role"] == "jointtop3_candidate"]
    j2_joint = [row for row in j3_joint if row["branch_index"] in J2_BRANCHES]
    assert result["physical_decoder_iterations"] == physical_iterations
    assert result["logical_control_iterations"] == sum(
        int(row["iterations"]) for row in prefix)
    assert result["logical_candidate_iterations"] == sum(
        int(row["iterations"]) for row in prefix + j3_joint)
    assert result["logical_derived_j2_iterations"] == sum(
        int(row["iterations"]) for row in prefix + j2_joint)
    assert result["logical_derived_j2_calls"] == 192 + 6 * 2 + 4 * 2
    assert result["logical_control_calls"] == 192 + 6 * 2
    assert result["logical_candidate_calls"] == 192 + 6 * 2 + 9 * 2
    assert result["syndrome_valid_wrong_candidate"] == 1
    assert result["syndrome_valid_wrong_derived_j2"] == 0

    # Persisted frame/call IDs retain the same subset and selected vectors.
    with np.load(result["artifacts"]["diagnostics"], allow_pickle=False) as diagnostics:
        for pair_index, joint in ((0, pair0_joint), (1, pair1_joint)):
            expected_j3_ids = [row["call_index"] for row in joint]
            expected_j2_ids = [row["call_index"] for row in joint
                                if row["branch_index"] in J2_BRANCHES]
            np.testing.assert_array_equal(
                diagnostics["pair_jointtop3_call_indices"][pair_index], expected_j3_ids)
            np.testing.assert_array_equal(
                diagnostics["pair_derived_j2_call_indices"][pair_index], expected_j2_ids)
        raw_by_call = {
            int(call_id): vector for call_id, vector in zip(
                diagnostics["raw_vector_call_index"], diagnostics["raw_x_hat"])
        }
        for pair in (p0, p1):
            for selected_key in ("candidate_selected_call_index",
                                 "derived_j2_selected_call_index"):
                call_id = int(pair[selected_key])
                np.testing.assert_array_equal(
                    raw_by_call[call_id], result["calls"][call_id]["x_hat"])
        selected_flags = diagnostics["call_selected_for_derived_j2"]
        for pair in (p0, p1):
            selected_id = int(pair["derived_j2_selected_call_index"])
            assert bool(selected_flags[selected_id])

    with Path(result["artifacts"]["frames"]).open(
            newline="", encoding="utf-8") as stream:
        frame_rows = list(csv.DictReader(stream))
    for pair_index, joint in ((0, pair0_joint), (1, pair1_joint)):
        frame = frame_rows[pair_index]
        assert json.loads(frame["jointtop3_call_indices_json"]) == [
            row["call_index"] for row in joint]
        assert json.loads(frame["derived_j2_call_indices_json"]) == [
            row["call_index"] for row in joint if row["branch_index"] in J2_BRANCHES]


@pytest.mark.parametrize(
    "probability_gap,expected_call",
    ((0.5e-12, 10), (2.0e-12, 11)),
)
def test_a3_original_prior_score_uses_epsilon_then_canonical_branch_tie(
        probability_gap, expected_call):
    prior = np.ones((128, 32), dtype=np.float64)
    prior[0, 1] = np.exp(probability_gap)
    lower_score = np.zeros(128, dtype=np.uint8)
    higher_score = lower_score.copy()
    higher_score[0] = 1
    selected, scores = rescue.select_soft_prior_branch(
        [
            {"call_index": 10, "branch_index": 0, "syndrome_valid": True,
             "x_hat": lower_score},
            {"call_index": 11, "branch_index": 1, "syndrome_valid": True,
             "x_hat": higher_score},
        ], prior)
    assert selected == expected_call
    assert scores[1]["score"] > scores[0]["score"]
    if probability_gap < 1e-12:
        assert scores[1]["score"] - scores[0]["score"] <= 1e-12
    else:
        assert scores[1]["score"] - scores[0]["score"] > 1e-12


def test_a3_own_syndrome_report_mismatch_stops_before_selection(tmp_path):
    fake = FakeJointTop3Batch(
        failures=(0,), reported_mismatch=(0, "rank1", 0))
    result = fake.execute(tmp_path)

    row = next(row for row in result["calls"]
               if row["pair_index"] == 0 and row["role"] == "rank1_onehot")
    assert row["status"] == "STOP"
    assert row["syndrome_valid"] is False
    assert row["syndrome_ok_reported"] is True
    assert row["syndrome_valid_wrong"] is False
    assert row["failure_reason"] == "decoder_syndrome_flag_mismatch"
    assert result["status"] == "STOP"
    assert result["candidate_exact"] is None
    assert result["derived_j2_exact"] is None
    assert not any(row["role"] == "jointtop3_candidate" for row in result["calls"])


def test_a5_call_and_iteration_caps_keep_partial_artifacts_and_null_totals(tmp_path):
    fake = FakeJointTop3Batch(failures=range(192), iterations_override=90)
    result = fake.execute(tmp_path)

    assert result["status"] == "INCOMPLETE"
    assert result["attempted_physical_calls"] == probe.JOINTTOP3_MAX_PHYSICAL_CALLS == 2688
    assert result["physical_decoder_iterations"] == probe.JOINTTOP3_MAX_PHYSICAL_ITERATIONS == 241_920
    assert result["completed_pairs"] < result["planned_pairs"] == 192
    assert len(result["calls"]) == 2688
    assert result["baseline_exact"] is None
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    assert result["derived_j2_exact"] is None
    assert result["delta_exact"] is None
    assert result["delta_j3_vs_derived_j2"] is None
    assert result["per_graph"] is None
    assert result["per_graph_j3_vs_derived_j2"] is None
    assert result["classification"] is None
    assert Path(result["artifacts"]["calls"]).exists()
    assert Path(result["artifacts"]["frames"]).exists()
    assert Path(result["artifacts"]["diagnostics"]).exists()


def test_a5_root_refusal_and_dry_run_do_not_call_fake_seams(tmp_path):
    fake = FakeJointTop3Batch()
    with pytest.raises(ValueError, match="out-root must equal frozen fresh root"):
        fake.execute(tmp_path, out_root=Path("workspace/not-the-jointtop3-root"))
    assert fake.source_reads == fake.sampler_calls == fake.decoder_calls == 0
    assert not (tmp_path / "workspace").exists()

    dry = probe.dry_run("jointtop3", repo_root=tmp_path)
    assert dry["status"] == "DRY_RUN"
    assert all(dry[key] == 0 for key in ("source_reads", "sampler_calls", "decoder_calls", "writes"))
    assert not Path(dry["out_root"]).exists()

