"""Fake-only focused tests for the frozen GF(32) top-three runtime profile."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from comparison_bench.cli.probes_closed import nbldpc_gf32_mechanism_pair as probe
from comparison_bench.cli.probes_closed import nbldpc_gf32_softprior_cost_profile as cost_profile
from comparison_bench.cli.probes_closed import nbldpc_gf32_softprior_rescue as rescue
from .test_nbldpc_gf32_mechanism_pair import (
    FakeBatch as AcceptedFakeBatch,
    _decode_result,
)


GUESSES = (0, 1, 3, 7, 15, 31)


def _ranked_beliefs(order=(1, 0, 3)):
    """Give every variable identical entropy while controlling allowed-symbol rank."""
    beliefs = np.zeros((128, 32), dtype=np.float64)
    logits = {symbol: float(10 - rank) for rank, symbol in enumerate(order)}
    for symbol, value in logits.items():
        beliefs[:, symbol] = value
    return beliefs


class Top3RuntimeFake(AcceptedFakeBatch):
    """Reuse the accepted graph/source fake; never reads NPZ or runs BP."""

    def __init__(self, *, failures=(0,), beliefs_by_pair=None, outcomes=None,
                 truth_by_pair=None):
        super().__init__("top3runtime", failures=tuple(failures),
                         truth_by_pair=truth_by_pair)
        self.beliefs_by_pair = {} if beliefs_by_pair is None else dict(beliefs_by_pair)
        self.top3_outcomes = {} if outcomes is None else dict(outcomes)
        self.test_clock = None

    def baseline(self, h, prior, syndrome, **kwargs):
        result = super().baseline(h, prior, syndrome, **kwargs)
        if self.current_pair in self.beliefs_by_pair:
            result.final_beliefs = self.beliefs_by_pair[self.current_pair].copy()
        if self.test_clock is not None:
            self.test_clock.advance(0.002)
        return result

    def soft_prior(self, h, prior, syndrome, **kwargs):
        self._record("soft_prior", h, prior, syndrome, kwargs)
        pair = self.current_pair
        call_number = self.branch_calls[pair]
        self.branch_calls[pair] = call_number + 1

        beliefs = self.beliefs_by_pair.get(
            pair, np.zeros((128, 32), dtype=np.float64))
        ranked, _ = cost_profile.rank_allowed_guesses(
            beliefs, int(np.flatnonzero(np.any(
                np.asarray(prior) != self.original_prior, axis=1))[0]))
        if pair % 2 == 0:
            method = "control" if call_number < 6 else "candidate"
            local_index = call_number if method == "control" else call_number - 6
        else:
            method = "candidate" if call_number < 3 else "control"
            local_index = call_number if method == "candidate" else call_number - 3
        guess = (GUESSES[local_index] if method == "control"
                 else int(ranked[local_index]))
        branch_index = GUESSES.index(guess)
        self.decoder_inputs[-1]["method"] = method
        self.decoder_inputs[-1]["branch_index"] = branch_index
        self.decoder_inputs[-1]["guess_symbol"] = guess

        outcome = self.top3_outcomes.get((pair, method, branch_index), "zero")
        result = _decode_result(
            h, self._outcome(outcome), syndrome, iterations=4 + branch_index)
        if self.test_clock is not None:
            self.test_clock.advance(0.001)
        return result


def test_top3_plan_keeps_posterior_rank_separate_from_canonical_branch_index():
    beliefs = _ranked_beliefs((31, 7, 15))

    assert probe.build_top3_branch_plan(beliefs, 0) == [
        (0, 5, 31), (1, 3, 7), (2, 4, 15),
    ]

    # Equal posterior mass uses the frozen EPS/tie rule and then the lowest symbol.
    tied = np.zeros((128, 32), dtype=np.float64)
    tied[:, 31] = 1e-13
    tied[:, 7] = 0.0
    tied[:, 15] = 0.0
    assert probe.build_top3_branch_plan(tied, 0) == [
        (0, 0, 0), (1, 1, 1), (2, 2, 3),
    ]


def _screen_summary(*, baseline=100, control=104, candidate=103,
                    control_path=10.0, candidate_path=7.0,
                    candidate_wrong=0, control_wrong=0):
    return {
        "baseline_exact": baseline,
        "control_exact": control,
        "candidate_exact": candidate,
        "syndrome_valid_wrong_control": control_wrong,
        "syndrome_valid_wrong_candidate": candidate_wrong,
        "timing": {
            "control_method_path_s": control_path,
            "candidate_method_path_s": candidate_path,
        },
    }


def test_tradeoff_classifier_includes_exact_retention_and_method_path_boundaries():
    exact_boundary = _screen_summary()
    assert probe._classification("top3runtime", exact_boundary) == "TRADEOFF_SCREEN_MET"
    assert exact_boundary["gain_retention"] == 0.75
    assert exact_boundary["accounted_method_path_ratio"] == 0.70

    below_retention = _screen_summary(candidate=102)
    assert probe._classification("top3runtime", below_retention) == "TRADEOFF_SCREEN_NOT_MET"
    assert below_retention["gain_retention"] == 0.5

    above_time_boundary = _screen_summary(candidate_path=7.01)
    assert probe._classification("top3runtime", above_time_boundary) == "TRADEOFF_SCREEN_NOT_MET"
    assert above_time_boundary["accounted_method_path_ratio"] == pytest.approx(0.701)

    worse_wrong_count = _screen_summary(candidate_wrong=1, control_wrong=0)
    assert probe._classification("top3runtime", worse_wrong_count) == "TRADEOFF_SCREEN_NOT_MET"


@pytest.mark.parametrize("baseline", (38, 154))
def test_tradeoff_screen_is_uninformative_outside_frozen_baseline_range(baseline):
    summary = _screen_summary(baseline=baseline, control=baseline + 2,
                              candidate=baseline + 2)

    assert probe._classification("top3runtime", summary) == "TRADEOFF_SCREEN_UNINFORMATIVE"
    assert summary["gain_retention"] == 1.0


@pytest.mark.parametrize("control", (99, 100))
def test_nonpositive_full_six_gain_is_uninformative_and_retention_is_null(control):
    summary = _screen_summary(baseline=100, control=control, candidate=100)

    assert probe._classification("top3runtime", summary) == "TRADEOFF_SCREEN_UNINFORMATIVE"
    assert summary["full6_gain"] <= 0
    assert summary["gain_retention"] is None


def test_fake_192_flow_uses_cold_one_row_calls_independent_ids_parity_and_no_borrow(
        tmp_path):
    truth = np.zeros(128, dtype=np.uint8)
    truth[:3] = 1
    truth[127] = 1
    fake = Top3RuntimeFake(
        failures=(0, 1),
        beliefs_by_pair={0: _ranked_beliefs((1, 0, 3))},
        # On pair 0, the candidate has both a valid wrong row and the truth;
        # the original-prior score must choose the more likely wrong row.
        # On pair 1, control recovers truth while candidate has no valid row.
        outcomes={
            (0, "control", 0): "truth",
            (0, "candidate", 0): "wrong",
            (0, "candidate", 1): "truth",
            (1, "control", 0): "truth",
        },
        truth_by_pair={0: truth},
    )
    result = fake.execute(tmp_path)

    assert result["status"] == "COMPLETE"
    assert result["planned_pairs"] == result["sampled_pairs"] == result["completed_pairs"] == 192
    assert result["attempted_physical_calls"] == 192 + 9 * 2
    assert result["logical_control_calls"] == 192 + 6 * 2
    assert result["logical_candidate_calls"] == 192 + 3 * 2
    assert len({row["call_index"] for row in result["calls"]}) == 192 + 18
    accounting = result["top3runtime_accounting"]
    assert accounting["F_baseline_failures"] == accounting["F_branched"] == 2
    assert accounting["expected_physical_calls"] == 210
    assert accounting["expected_logical_control_calls"] == 204
    assert accounting["expected_logical_candidate_calls"] == 198
    assert result["physical_decoder_iterations"] == sum(
        int(row["iterations"]) for row in result["calls"])
    assert result["disclosure_bits_physical_batch"] == 192 * probe.SYNDROME_BITS
    assert result["disclosure_bits_logical_control"] == 192 * probe.SYNDROME_BITS
    assert result["disclosure_bits_logical_candidate"] == 192 * probe.SYNDROME_BITS
    assert result["internal_branch_disclosure_bits"] == result["tag_bits"] == 0

    for pair_index, expected_roles in (
        (0, ["top3_control"] * 6 + ["top3_candidate"] * 3),
        (1, ["top3_candidate"] * 3 + ["top3_control"] * 6),
    ):
        pair = result["pairs"][pair_index]
        branch_rows = [row for row in result["calls"]
                       if row["pair_index"] == pair_index and row["role"] != "baseline"]
        assert [row["role"] for row in branch_rows] == expected_roles
        control = [row for row in branch_rows if row["role"] == "top3_control"]
        candidate = [row for row in branch_rows if row["role"] == "top3_candidate"]
        assert [row["branch_index"] for row in control] == list(range(6))
        assert len(candidate) == 3
        assert [row["posterior_rank"] for row in candidate] == [0, 1, 2]
        assert all(row["branch_index"] == GUESSES.index(row["guess_symbol"])
                   for row in candidate)
        assert all(row["selected_variable"] == pair["rank1_variable"]
                   for row in branch_rows)

        calls_by_id = {int(row["call_index"]): row for row in result["calls"]}
        assert pair["control_selected_call_index"] != pair["candidate_selected_call_index"] or (
            pair["control_selected_call_index"] == pair["baseline_call_index"]
            and pair["candidate_selected_call_index"] == pair["baseline_call_index"])
        assert all(calls_by_id[int(row["call_index"])]["role"] == row["role"]
                   for row in branch_rows)

        for row in branch_rows:
            recorded = fake.decoder_inputs[int(row["call_index"])]
            prior = recorded["prior"]
            changed = [column for column in range(128)
                       if not np.array_equal(prior[column], fake.original_prior[column])]
            assert changed == [int(row["selected_variable"])]
            assert np.count_nonzero(prior[changed[0]]) == 1
            assert int(np.argmax(prior[changed[0]])) == int(row["guess_symbol"])
            unchanged = np.arange(128) != changed[0]
            np.testing.assert_array_equal(prior[unchanged], fake.original_prior[unchanged])
            assert recorded["kwargs"] == {
                "max_iter": 90, "damping_alpha": 1.0,
                "warm_beliefs": None, "field": None,
            }

    first, second = result["pairs"][:2]
    first_candidate_selected = result["calls"][first["candidate_selected_call_index"]]
    assert first_candidate_selected["role"] == "top3_candidate"
    assert first_candidate_selected["syndrome_valid"] is True
    assert first_candidate_selected["exact"] is False
    assert first["candidate_valid_wrong"] is True
    assert first["candidate_exact"] is False
    first_candidate_calls = [row for row in result["calls"]
                             if row["pair_index"] == 0
                             and row["role"] == "top3_candidate"]
    candidate_truth = next(row for row in first_candidate_calls if row["exact"] is True)
    assert first_candidate_selected["score_original_prior"] > candidate_truth["score_original_prior"]
    assert first_candidate_selected["call_index"] != first["control_selected_call_index"]

    # Pair 1 control succeeds, but candidate has no valid rescue and retains its
    # own failed baseline instead of borrowing the control's truth call.
    assert second["control_exact"] is True
    assert second["candidate_exact"] is False
    assert second["candidate_selected_call_index"] == second["baseline_call_index"]
    assert second["control_selected_call_index"] != second["candidate_selected_call_index"]
    assert result["total_wall_s"] is not None


def test_partial_physical_cap_keeps_comparison_totals_null(tmp_path, monkeypatch):
    monkeypatch.setitem(probe.PROFILES["top3runtime"], "physical_call_cap", 193)
    fake = Top3RuntimeFake(failures=(0,))

    result = fake.execute(tmp_path)

    assert result["status"] == "INCOMPLETE"
    assert "physical_call_cap" in " ".join(result["stop_reasons"])
    assert result["baseline_exact"] is None
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    assert result["paired"] is None


def test_fake_clock_proves_arm_timer_includes_ranking_choice_and_excludes_common_selector(
        tmp_path, monkeypatch):
    class FakeClock:
        value = 0.0

        def __call__(self):
            return self.value

        def advance(self, seconds):
            self.value += float(seconds)

    clock = FakeClock()
    fake = Top3RuntimeFake(failures=(0,))
    fake.test_clock = clock

    build_plan = probe.build_top3_branch_plan

    def timed_build_plan(beliefs, variable):
        clock.advance(0.05)
        return build_plan(beliefs, variable)

    select = rescue.select_uncertain_variable

    def timed_selector(*args, **kwargs):
        clock.advance(0.07)
        return select(*args, **kwargs)

    choose = rescue.select_soft_prior_branch

    def timed_choice(*args, **kwargs):
        clock.advance(0.02)
        return choose(*args, **kwargs)

    monkeypatch.setattr(probe, "build_top3_branch_plan", timed_build_plan)
    monkeypatch.setattr(rescue, "select_uncertain_variable", timed_selector)
    monkeypatch.setattr(rescue, "select_soft_prior_branch", timed_choice)

    result = fake.execute(tmp_path, now=clock)

    timing = result["timing"]
    assert result["status"] == "COMPLETE"
    assert timing["baseline_call_s"] == pytest.approx(192 * 0.002)
    assert timing["common_selector_s"] == pytest.approx(0.07)
    assert timing["control_arm_loop_s"] + 1e-12 >= 6 * 0.001 + 0.02
    assert timing["candidate_arm_loop_s"] + 1e-12 >= 0.05 + 3 * 0.001 + 0.02
    assert timing["candidate_arm_loop_s"] > timing["control_arm_loop_s"]
    assert timing["control_method_path_s"] == pytest.approx(
        timing["baseline_call_s"] + timing["control_arm_loop_s"])
    assert timing["candidate_method_path_s"] == pytest.approx(
        timing["baseline_call_s"] + timing["candidate_arm_loop_s"])
    assert timing["branch_loop_ratio"] == pytest.approx(
        timing["candidate_arm_loop_s"] / timing["control_arm_loop_s"])
    assert timing["method_path_ratio"] == pytest.approx(
        timing["candidate_method_path_s"] / timing["control_method_path_s"])
    assert timing["candidate_method_path_s"] != pytest.approx(
        timing["baseline_call_s"] + timing["common_selector_s"]
        + timing["candidate_arm_loop_s"])


def test_no_active_selector_falls_back_to_shared_baseline_without_rescue_calls(
        tmp_path, monkeypatch):
    def no_active(*_args, **_kwargs):
        raise ValueError("baseline failure has no variables adjacent to violated checks")

    monkeypatch.setattr(rescue, "select_uncertain_variable", no_active)
    fake = Top3RuntimeFake(failures=(0,))

    result = fake.execute(tmp_path)

    pair = result["pairs"][0]
    assert result["status"] == "COMPLETE"
    assert result["attempted_physical_calls"] == 192
    assert result["top3runtime_accounting"]["no_active_frames"] == 1
    assert pair["top3_selector_status"] == "no_active"
    assert pair["control_branch_calls"] == pair["candidate_incremental_branch_calls"] == 0
    assert pair["control_selected_call_index"] == pair["candidate_selected_call_index"]
    assert pair["control_selected_call_index"] == pair["baseline_call_index"]


def test_top3_t0_and_dry_run_are_read_free(tmp_path, monkeypatch):
    def forbidden_binding():
        raise AssertionError("T0/dry-run must not bind source, sampler, or production BP")

    monkeypatch.setattr(probe, "_bind_production", forbidden_binding)
    t0 = probe.verify_t0("top3runtime")
    dry = probe.dry_run("top3runtime", repo_root=tmp_path)

    assert t0["status"] == "PASS"
    assert t0["holdout_pairs"] == 192
    assert (t0["prior_exclusion_plan_count"], t0["prior_exclusion_rows"]) == (19, 3984)
    assert all(t0[key] == 0 for key in ("source_reads", "sampler_calls", "decoder_calls", "writes"))
    assert dry["status"] == "DRY_RUN"
    assert all(dry[key] == 0 for key in ("source_reads", "sampler_calls", "decoder_calls", "writes"))
    assert not (tmp_path / probe.PROFILES["top3runtime"]["out_root"]).exists()
