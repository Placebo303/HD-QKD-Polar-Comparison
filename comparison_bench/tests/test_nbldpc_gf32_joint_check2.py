"""Focused fake-only tests for the GF(32) jointcheck2 selector profile."""
from __future__ import annotations

import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_mechanism_pair as probe
from test_nbldpc_gf32_mechanism_pair import (
    FakeBatch as AcceptedFakeBatch,
    _decode_result,
    rescue,
)


class JointCheck2Fake(AcceptedFakeBatch):
    """Reuse the accepted saved-source fixture; all sampling/decoding is fake."""

    def __init__(self, *, failures=(0,), success_by_pair=None,
                 truth_by_pair=None):
        super().__init__(
            "jointcheck2", failures=tuple(failures),
            truth_by_pair=truth_by_pair,
        )
        self.success_by_pair = {} if success_by_pair is None else dict(success_by_pair)

    def soft_prior(self, h, prior, syndrome, **kwargs):
        self._record("soft_prior", h, prior, syndrome, kwargs)
        call_number = self.branch_calls[self.current_pair]
        self.branch_calls[self.current_pair] = call_number + 1

        if call_number < 6:
            # The shared rank-1 rescue fails, triggering the two joint policies.
            branch_index = call_number
            stage = "rank1"
            method = "rank1"
            outcome = "zero"
        else:
            local = call_number - 6
            set_index, branch_index = divmod(local, 4)
            order = ("control", "candidate") if self.current_pair % 2 == 0 else (
                "candidate", "control")
            method = order[set_index]
            stage = "joint"
            success_kind = self.success_by_pair.get(self.current_pair)
            succeeds = success_kind == "both" or success_kind == method
            outcome = ("truth" if succeeds and branch_index == 0 else "zero")

        self.decoder_inputs[-1]["stage"] = stage
        self.decoder_inputs[-1]["method"] = method
        if stage == "joint":
            joint_outcomes = getattr(self, "joint_outcomes", {})
            custom = joint_outcomes.get((self.current_pair, success_kind, branch_index))
            if custom is not None:
                outcome = custom
        return probe_fake_decode(self, h, prior, syndrome, outcome, branch_index)


def probe_fake_decode(fake, h, prior, syndrome, outcome, branch_index):
    x_hat = fake._outcome(outcome)
    return _decode_result(h, x_hat, syndrome, iterations=4 + branch_index)


def _entropy_vector(size=6):
    return np.zeros(size, dtype=np.float64)


def test_selector_uses_full_integer_count_then_entropy_and_excludes_zero_count():
    # Counts are 3, 2, 1, 0. Entropy deliberately favors the lower-count columns.
    h = np.asarray([
        [1, 1, 1, 0],
        [1, 1, 0, 0],
        [1, 0, 0, 0],
    ], dtype=np.int64)
    metadata = {
        "active_variable_columns": [0, 1, 2, 3],
        "violated_check_ids": [0, 1, 2],
        "entropy_bits": [0.0, 9.0, 10.0, 100.0],
    }

    primary, secondary, counts = probe.select_jointcheck2_variables(h, metadata)

    assert counts == {0: 3, 1: 2, 2: 1, 3: 0}
    assert all(type(value) is int for value in counts.values())
    assert (primary, secondary) == (0, 1)


def test_selector_tie_uses_eps_and_lowest_column_then_recomputes_after_exclusion():
    h = np.asarray([
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 1, 0, 0],
    ], dtype=np.int64)
    entropy = _entropy_vector(5)
    entropy[0] = 0.4
    entropy[4] = 0.4 + 5e-13
    entropy[1] = entropy[2] = 0.8
    entropy[3] = 5.0
    metadata = {
        "active_variable_columns": [0, 1, 2, 3, 4],
        "violated_check_ids": [0, 1, 2],
        "entropy_bits": entropy,
    }

    primary, secondary, counts = probe.select_jointcheck2_variables(h, metadata)

    assert counts == {0: 2, 1: 1, 2: 1, 3: 0, 4: 2}
    assert (primary, secondary) == (0, 4)


def test_joint_guess_plan_is_primary_outer_and_requires_two_supported_guesses():
    assert probe.build_joint_branch_plan((7, 3, 1), (15, 1, 0)) == [
        (0, 7, 15), (1, 7, 1), (2, 3, 15), (3, 3, 1),
    ]
    with pytest.raises(ValueError, match="exactly two"):
        probe.build_joint_branch_plan((7,), (15, 1))


def _control_pair(metadata):
    first = int(metadata["selected_column"])
    second = probe.select_rank2_variable(metadata, first)
    return first, second


def _force_joint_variables(mode):
    real_selector = probe.select_jointcheck2_variables

    def select(h, metadata):
        _, _, counts = real_selector(h, metadata)
        first, second = _control_pair(metadata)
        if first is None or second is None:
            return None, None, counts
        if mode == "same":
            return first, second, counts
        if mode == "swapped":
            return second, first, counts
        raise AssertionError(mode)

    return select


def _joint_rows(result, pair_index):
    return [row for row in result["calls"]
            if row["pair_index"] == pair_index and row["role"].startswith("jointcheck2_")]


def _assert_joint_prior_inputs(fake, rows):
    original = np.tile(rescue.pmf(), (128, 1))
    for call in rows:
        recorded = fake.decoder_inputs[int(call["call_index"])]
        prior = recorded["prior"]
        changed = [column for column in range(128)
                   if not np.array_equal(prior[column], original[column])]
        expected = sorted((int(call["selected_variable"]),
                           int(call["secondary_variable"])))
        assert sorted(changed) == expected
        for column in changed:
            row = prior[column]
            assert np.count_nonzero(row) == 1
            assert float(np.sum(row)) == pytest.approx(1.0)
            assert int(np.argmax(row)) in probe.GUESSES
        unchanged = [column for column in range(128) if column not in changed]
        np.testing.assert_array_equal(prior[unchanged], original[unchanged])
        assert recorded["kwargs"] == {
            "max_iter": 90, "damping_alpha": 1.0,
            "warm_beliefs": None, "field": None,
        }


def test_distinct_pairs_run_eight_calls_in_parity_order_and_candidate_cannot_borrow(
        tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "select_jointcheck2_variables", _force_joint_variables("swapped"))
    fake = JointCheck2Fake(
        failures=(0, 1), success_by_pair={0: "control", 1: "control"})
    result = fake.execute(tmp_path)

    assert result["status"] == "COMPLETE"
    assert result["attempted_physical_calls"] == 192 + 6 * 2 + 8 * 2
    assert result["jointcheck2_accounting"] == {
        "F_baseline_failures": 2, "G_triggered_frames": 2,
        "D_distinct_ordered_pairs": 2,
        "expected_physical_calls": 220,
        "expected_logical_calls_per_method": 212,
        "max_physical_calls": probe.JOINTCHECK2_MAX_PHYSICAL_CALLS,
        "max_iterations": probe.JOINTCHECK2_MAX_PHYSICAL_CALLS * 90,
    }
    assert result["logical_control_calls"] == result["logical_candidate_calls"] == 212
    assert result["attempted_physical_calls"] <= probe.JOINTCHECK2_MAX_PHYSICAL_CALLS

    even, odd = result["pairs"][0], result["pairs"][1]
    assert even["joint_pair_shared"] is False
    assert even["joint_pair_order"] == "control_then_candidate"
    assert odd["joint_pair_shared"] is False
    assert odd["joint_pair_order"] == "candidate_then_control"
    for pair in (even, odd):
        assert pair["control_exact"] is True
        assert pair["candidate_exact"] is False
        assert pair["candidate_selected_call_index"] == pair["baseline_call_index"]
        roles = [row["role"] for row in _joint_rows(result, pair["pair_index"])]
        expected = ((["jointcheck2_control"] * 4 + ["jointcheck2_candidate"] * 4)
                    if pair["frame_index"] % 2 == 0 else
                    (["jointcheck2_candidate"] * 4 + ["jointcheck2_control"] * 4))
        assert roles == expected
        for role in ("jointcheck2_control", "jointcheck2_candidate"):
            branch_rows = sorted(
                (row for row in _joint_rows(result, pair["pair_index"])
                 if row["role"] == role), key=lambda row: row["branch_index"])
            assert [row["branch_index"] for row in branch_rows] == [0, 1, 2, 3]
            first = int(branch_rows[0]["selected_variable"])
            second = int(branch_rows[0]["secondary_variable"])
            beliefs = pair["baseline_beliefs"]
            first_guesses, _ = probe.cost_profile.rank_allowed_guesses(beliefs, first)
            second_guesses, _ = probe.cost_profile.rank_allowed_guesses(beliefs, second)
            expected_plan = probe.build_joint_branch_plan(first_guesses, second_guesses)
            assert [(row["branch_index"], row["guess_symbol"],
                     row["secondary_guess_symbol"]) for row in branch_rows] == expected_plan
            _assert_joint_prior_inputs(fake, branch_rows)

    # Control has a valid joint result on both frames; candidate must fall back
    # to its own shared baseline/rank-1 choice when its own four branches fail.
    assert all(row["role"] == "baseline" or "truth" not in row
               for row in fake.decoder_inputs)
    assert result["control_exact"] >= 2
    assert result["candidate_exact"] <= result["control_exact"]


def test_shared_pair_reuses_four_calls_and_joint_score_is_truth_blind(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "select_jointcheck2_variables", _force_joint_variables("same"))
    truth = np.zeros(128, dtype=np.uint8)
    truth[:3] = 1
    truth[127] = 1
    fake = JointCheck2Fake(
        failures=(0,), success_by_pair={0: "both"}, truth_by_pair={0: truth})
    fake.joint_outcomes = {
        # The one-error alternative has a higher original-prior score than the
        # sampled three-error truth, so blind scoring selects a valid-wrong row.
        (0, "both", 0): "wrong",
        (0, "both", 1): "truth",
    }
    result = fake.execute(tmp_path)

    assert result["status"] == "COMPLETE"
    assert result["attempted_physical_calls"] == 192 + 6 + 4
    assert result["logical_control_calls"] == result["logical_candidate_calls"] == 202
    pair = result["pairs"][0]
    assert pair["joint_pair_shared"] is True
    assert pair["joint_pair_order"] == "shared_single_set"
    joint = _joint_rows(result, 0)
    assert len(joint) == 4
    assert {row["role"] for row in joint} == {"jointcheck2_shared"}
    scores = {int(row["branch_index"]): row["score_original_prior"] for row in joint}
    assert scores[0] > scores[1]
    assert scores[2] is None and scores[3] is None
    assert pair["control_selected_call_index"] == pair["candidate_selected_call_index"]
    selected = result["calls"][pair["control_selected_call_index"]]
    assert selected["role"] == "jointcheck2_shared"
    assert selected["branch_index"] == 0
    assert selected["syndrome_valid"] is True
    assert selected["exact"] is False
    assert result["calls"][joint[1]["call_index"]]["exact"] is True
    assert pair["control_valid_wrong"] is True
    assert pair["candidate_valid_wrong"] is True
    assert result["raw_valid_wrong_by_role"]["jointcheck2_shared"] == 1
    _assert_joint_prior_inputs(fake, joint)


def test_full_192_classifier_uses_baseline_exact_and_counts_shared_cost(tmp_path, monkeypatch):
    failures = tuple(range(50))
    monkeypatch.setattr(probe, "select_jointcheck2_variables", _force_joint_variables("same"))
    fake = JointCheck2Fake(
        failures=failures, success_by_pair={pair: "both" for pair in failures})
    result = fake.execute(tmp_path)

    assert result["status"] == "COMPLETE"
    assert result["planned_pairs"] == result["sampled_pairs"] == result["completed_pairs"] == 192
    assert result["baseline_exact"] == 142
    assert result["control_exact"] == result["candidate_exact"] == 192
    assert result["classification"] == "INCREMENT_NOT_ESTABLISHED"
    assert result["attempted_physical_calls"] == 192 + 6 * 50 + 4 * 50 == 692
    assert result["logical_control_calls"] == result["logical_candidate_calls"] == 692
    assert result["jointcheck2_accounting"]["expected_physical_calls"] == 692
    assert result["jointcheck2_accounting"]["expected_logical_calls_per_method"] == 692
    assert result["jointcheck2_shared_pair_frames"] == 50
    assert result["jointcheck2_distinct_pair_frames"] == 0
    assert result["disclosure_bits_physical_batch"] == 192 * probe.SYNDROME_BITS


def test_dry_run_is_read_free_and_output_cap_leaves_comparison_null(tmp_path, monkeypatch):
    dry_root = tmp_path / probe.PROFILES["jointcheck2"]["out_root"]
    dry = probe.dry_run("jointcheck2", out_root=dry_root, repo_root=tmp_path)
    assert dry["status"] == "DRY_RUN"
    assert dry["source_reads"] == dry["sampler_calls"] == dry["decoder_calls"] == dry["writes"] == 0
    assert not dry_root.exists()

    monkeypatch.setattr(probe, "ARTIFACT_CAP_BYTES", 1)
    fake = JointCheck2Fake(failures=())
    result = fake.execute(tmp_path / "capped")
    assert result["status"] == "INCOMPLETE"
    assert any("output_cap" in reason for reason in result["stop_reasons"])
    assert result["resource_violations"] > 0
    assert result["baseline_exact"] is None
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    assert result["delta_exact"] is None
    assert result["classification"] == "INCOMPLETE"

