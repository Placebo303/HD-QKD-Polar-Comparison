"""Explicit-fake gates for the bounded GF(32) edge-state probe."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli.probes_closed import nbldpc_gf32_edge_state_probe as probe
from comparison_bench.cli.probes_closed import nbldpc_gf32_softprior_rescue as rescue
from comparison_bench.formal_ir import nbldpc_gf32_edge_state as edge_state
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from .test_nbldpc_gf32_mechanism_pair import _fake_source


GUESSES = (0, 1, 3, 7, 15, 31)
ZERO = np.zeros(rescue.N, dtype=np.uint8)


def _kernel_triangle() -> np.ndarray:
    value = np.zeros(rescue.N, dtype=np.uint8)
    value[:3] = 1
    return value


def _fake_result(h, vector, syndrome, beliefs, *, iterations, state=None,
                 iterations_this_call=None):
    vector = np.asarray(vector, dtype=np.uint8).copy()
    own_valid = bool(np.array_equal(layout.gf32_syndrome(h, vector), syndrome))
    status = "converged_exact" if own_valid else "converged_no_syndrome"
    common = dict(
        x_hat=vector, syndrome_ok=own_valid, iterations=int(iterations),
        status=status, final_beliefs=np.asarray(beliefs, dtype=np.float64).copy(),
        belief_provenance="CHECK_UPDATED", extrinsic_provenance="CHECK_EXTRINSIC",
    )
    if state is None:
        return SimpleNamespace(**common, runtime_s=0.001)
    return edge_state.EdgeLoopResult(
        **common, iterations_this_call=int(
            iterations if iterations_this_call is None else iterations_this_call),
        state=state,
        extrinsic_log_beliefs=np.zeros((rescue.N, rescue.Q), dtype=np.float64),
    )


class EdgeStateFake:
    """192-frame source/sampler/decoder seam; no production binding is reachable."""

    def __init__(self, *, failures=(0, 1), branch_outcomes=True,
                 mismatch_aux_pair=None):
        self.plan = rescue.build_seed_plan(probe.SEED_NAMESPACE)
        self.pair_for_seed = {int(row[3]): i for i, row in enumerate(self.plan)}
        self.failures = set(failures)
        self.branch_outcomes = bool(branch_outcomes)
        self.mismatch_aux_pair = mismatch_aux_pair
        self.current_pair = -1
        self.source_reads = 0
        self.sampled_seeds = []
        self.reference_states = {}
        self.candidate_states = {}
        self.control_inputs = []
        self.candidate_inputs = []
        self.control_branch_counts = {}
        self.candidate_branch_counts = {}
        self.decoder_calls = []
        self.original_prior = np.tile(rescue.pmf(), (rescue.N, 1))

    def source_reader(self):
        self.source_reads += 1
        return _fake_source()

    def sampler(self, seed, pmf, *, width):
        pair = self.pair_for_seed[int(seed)]
        self.current_pair = pair
        self.sampled_seeds.append(int(seed))
        assert width == rescue.N
        np.testing.assert_allclose(pmf, rescue.pmf(), rtol=0.0, atol=1e-15)
        truth = np.zeros(rescue.N, dtype=np.uint8)
        if pair == 0:
            truth[127] = 1
            truth ^= _kernel_triangle()
        elif pair == 1:
            truth[127] = 1
        return truth

    def _baseline_vector(self, pair, truth):
        return ZERO.copy() if pair in self.failures else np.asarray(truth).copy()

    def _beliefs(self):
        # Flat beliefs exercise canonical lowest-column entropy ties. The edge
        # messages are chosen so L = log(P) + sum(C2V) exactly.
        return np.zeros((rescue.N, rescue.Q), dtype=np.float64)

    def _state(self, h, syndrome, beliefs, prior, *, completed_sweeps, stopped_exact):
        clean = edge_state.clean_prior(prior, rescue.N, rescue.Q)
        degree = np.count_nonzero(np.asarray(h) != 0, axis=0)
        check_to_var = []
        for row in range(rescue.M):
            columns = np.flatnonzero(np.asarray(h)[row] != 0)
            check_to_var.append([
                (beliefs[int(column)] - np.log(clean[int(column)]))
                / float(degree[int(column)])
                for column in columns
            ])
        return edge_state.EdgeState(
            h_matrix=np.asarray(h, dtype=np.uint8).copy(),
            syndrome=np.asarray(syndrome, dtype=np.uint8).copy(),
            beliefs=np.asarray(beliefs, dtype=np.float64).copy(),
            log_prior=np.log(clean), check_to_var=check_to_var,
            completed_sweeps=int(completed_sweeps), stopped_exact=bool(stopped_exact),
        )

    def _record(self, role, h, prior, syndrome, kwargs):
        self.decoder_calls.append((role, self.current_pair))
        record = {
            "pair": self.current_pair, "H": np.asarray(h).copy(),
            "prior": np.asarray(prior).copy(), "syndrome": np.asarray(syndrome).copy(),
            "kwargs": dict(kwargs),
        }
        return record

    def reference(self, h, prior, syndrome, **kwargs):
        record = self._record("reference", h, prior, syndrome, kwargs)
        pair = self.current_pair
        truth = self._truth_for_pair(pair)
        vector = self._baseline_vector(pair, truth)
        beliefs = self._beliefs()
        valid = bool(np.array_equal(layout.gf32_syndrome(h, vector), syndrome))
        raw = _fake_result(h, vector, syndrome, beliefs, iterations=2)
        state = self._state(
            h, syndrome, beliefs, prior, completed_sweeps=2, stopped_exact=valid)
        self.reference_states[pair] = state
        return raw, state

    def control(self, h, prior, syndrome, **kwargs):
        record = self._record("control", h, prior, syndrome, kwargs)
        pair = self.current_pair
        branch_index = self.control_branch_counts.get(pair, 0)
        self.control_branch_counts[pair] = branch_index + 1
        record["branch_index"] = branch_index
        self.control_inputs.append(record)
        vector = self._branch_vector(pair, branch_index)
        return _fake_result(
            h, vector, syndrome, self._beliefs(), iterations=branch_index + 1)

    def edge_loop(self, h, prior, syndrome, *, state, **kwargs):
        record = self._record(
            "edge_state", h, prior, syndrome, {**kwargs, "state": state})
        pair = self.current_pair
        beliefs = self._beliefs()
        if state is None:
            vector = self._baseline_vector(pair, self._truth_for_pair(pair))
            if pair == self.mismatch_aux_pair:
                vector = vector.copy()
                vector[127] ^= 1
            valid = bool(np.array_equal(layout.gf32_syndrome(h, vector), syndrome))
            raw = _fake_result(h, vector, syndrome, beliefs, iterations=2)
            self.aux_calls = getattr(self, "aux_calls", [])
            self.aux_calls.append(record)
            return _fake_result(
                h, vector, syndrome, beliefs, iterations=2,
                iterations_this_call=2,
                state=self._state(
                    h, syndrome, beliefs, prior, completed_sweeps=0,
                    stopped_exact=valid),
            )

        branch_index = self.candidate_branch_counts.get(pair, 0)
        self.candidate_branch_counts[pair] = branch_index + 1
        record["branch_index"] = branch_index
        record["state"] = state
        self.candidate_inputs.append(record)
        vector = self._branch_vector(pair, branch_index)
        branch_sweeps = branch_index + 1
        output_state = edge_state.EdgeState(
            h_matrix=state.h_matrix.copy(), syndrome=state.syndrome.copy(),
            beliefs=state.beliefs.copy(), log_prior=state.log_prior.copy(),
            check_to_var=[[message.copy() for message in row]
                          for row in state.check_to_var],
            completed_sweeps=branch_sweeps, stopped_exact=bool(
                np.array_equal(layout.gf32_syndrome(h, vector), syndrome)),
        )
        return _fake_result(
            h, vector, syndrome, output_state.beliefs, iterations=branch_sweeps,
            iterations_this_call=branch_sweeps, state=output_state)

    def _truth_for_pair(self, pair):
        truth = np.zeros(rescue.N, dtype=np.uint8)
        if pair == 0:
            truth[127] = 1
            truth ^= _kernel_triangle()
        elif pair == 1:
            truth[127] = 1
        return truth

    def _branch_vector(self, pair, branch_index):
        if not self.branch_outcomes or pair not in (0, 1):
            return ZERO.copy()
        truth = self._truth_for_pair(pair)
        wrong = truth ^ _kernel_triangle()
        if pair == 0:
            if branch_index in (0, 2):
                return wrong
            if branch_index == 1:
                return truth
            return ZERO.copy()
        if branch_index == 0:
            return wrong
        if branch_index == 1:
            return truth
        return ZERO.copy()

    def decode_fns(self):
        return {"reference": self.reference, "control": self.control,
                "edge_state": self.edge_loop}

    def execute(self, tmp_path, name, *, now=None, rss_fn=None):
        relative_root = Path("workspace") / name
        return probe.execute_batch(
            source_reader=self.source_reader, sampler=self.sampler,
            decode_fns=self.decode_fns(), out_root=relative_root,
            repo_root=tmp_path, official_root=relative_root,
            now=(lambda: 10.0) if now is None else now,
            rss_fn=(lambda: 100_000) if rss_fn is None else rss_fn,
            command="explicit fake test only",
        )


def _call_map(result):
    return {row["call_index"]: row for row in result["calls"]}


def test_full_192_fake_batch_accounting_parity_state_and_blind_original_prior_choice(
        tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "_bind_production", lambda: pytest.fail(
        "fake execute path must never bind production"))
    fake = EdgeStateFake()
    result = fake.execute(tmp_path, "full-fake")

    assert result["status"] == "COMPLETE"
    assert result["planned_pairs"] == result["sampled_pairs"] == result["completed_pairs"] == 192
    assert fake.source_reads == 1
    assert fake.sampled_seeds == [row[3] for row in fake.plan]
    assert len(set(fake.sampled_seeds)) == 192
    expected_identity, expected_sources = rescue.select_sources(_fake_source())
    assert result["source_identity"] == expected_identity
    assert [row["graph_id"] for row in result["source_maps"]] == list(rescue.GRAPH_IDS)
    assert [row["source_lineage"]["source_uuid"] for row in result["source_maps"]] == [
        rescue.SOURCE_UUID
    ] * 6
    assert result["branched_baseline_failures"] == 2
    assert result["baseline_calls"] == result["zero_state_calls"] == 192
    assert result["zero_state_equivalence_passes"] == 192
    assert result["branch_calls"] == 24
    assert result["control_branch_calls"] == result["candidate_branch_calls"] == 12
    assert result["attempted_physical_calls"] == 408  # 384 + 12*F, F=2
    assert result["logical_control_calls"] == result["logical_candidate_calls"] == 204
    assert result["physical_decoder_iterations"] == 852
    assert result["auxiliary_decoder_iterations"] == 384
    assert result["logical_control_iterations"] == result["logical_candidate_iterations"] == 426
    assert result["physical_disclosure_bits_shared"] == 49_920
    assert result["logical_control_disclosure_bits"] == 49_920
    assert result["logical_candidate_disclosure_bits"] == 49_920
    assert result["internal_branch_disclosure_bits"] == result["tag_bits"] == 0
    assert result["verification_status"] == "NOT_IMPLEMENTED"
    assert result["undetected_status"] == "NOT_MEASURED"

    calls = result["calls"]
    call_ids = [row["call_index"] for row in calls]
    assert call_ids == list(range(408))
    by_pair = {}
    for call in calls:
        by_pair.setdefault(call["pair_index"], []).append(call)
    for pair_index, rows in by_pair.items():
        assert rows[0]["role"] == "baseline_reference"
        assert rows[1]["role"] == "baseline_zero_state"
        assert rows[0]["call_index"] != rows[1]["call_index"]
        assert rows[1]["call_index"] != rows[0]["call_index"]
        assert all(row["role"] != "baseline_zero_state"
                   for row in rows if row["call_index"] not in
                   (rows[0]["call_index"], rows[1]["call_index"]))
        if pair_index in (0, 1):
            expected_roles = (("onehot_control", "edge_state_candidate")
                              if pair_index % 2 == 0 else
                              ("edge_state_candidate", "onehot_control"))
            branch_rows = rows[2:]
            assert len(branch_rows) == 12
            assert tuple(row["role"] for row in branch_rows[::2]) == (expected_roles[0],) * 6
            assert tuple(row["role"] for row in branch_rows[1::2]) == (expected_roles[1],) * 6
            for role in ("onehot_control", "edge_state_candidate"):
                selected_rows = [row for row in branch_rows if row["role"] == role]
                assert [row["branch_index"] for row in selected_rows] == list(range(6))
                assert [row["guess_symbol"] for row in selected_rows] == list(GUESSES)
                assert len({row["call_index"] for row in selected_rows}) == 6

    pairs = {row["pair_index"]: row for row in result["pairs"]}
    for pair_index in range(192):
        pair = pairs[pair_index]
        assert pair["candidate_selected_call_index"] != pair["zero_state_call_index"]
        assert pair["candidate_selected_call_index"] == pair["reference_call_index"] or pair_index in (0, 1)
        assert pair["control_selected_call_index"] == pair["reference_call_index"] or pair_index in (0, 1)
    for pair_index, selected_branch in ((0, 0), (1, 1)):
        pair = pairs[pair_index]
        branch_calls = [row for row in by_pair[pair_index]
                        if row["role"] == "edge_state_candidate"]
        selected_call = next(row["call_index"] for row in branch_calls
                             if row["branch_index"] == selected_branch)
        assert pair["candidate_selected_call_index"] == selected_call
        active = np.flatnonzero(np.any(
            fake.reference_states[pair_index].h_matrix[
                fake.reference_states[pair_index].syndrome != 0] != 0,
            axis=0,
        ))
        assert pair["selected_variable"] == int(active.min())
        assert pair["selector_metadata"]["selected_column"] == int(active.min())
        assert all(row["selected_variable"] == int(active.min())
                   for row in branch_calls)
    assert pairs[0]["candidate_exact"] is False
    assert pairs[0]["candidate_syndrome_valid_wrong"] is True
    assert pairs[1]["candidate_exact"] is True
    assert result["candidate_exact"] == result["control_exact"] == 191
    assert result["syndrome_valid_wrong_candidate"] == result["syndrome_valid_wrong_control"] == 1
    assert result["raw_branch_valid_wrong_candidate"] == 3
    assert result["raw_branch_valid_wrong_control"] == 3
    assert result["raw_branch_valid_wrong_candidate"] > result["syndrome_valid_wrong_candidate"]
    with np.load(result["artifacts"]["diagnostics"]) as arrays:
        np.testing.assert_array_equal(
            arrays["source_H"], np.stack([row["H"] for row in expected_sources]))
        np.testing.assert_array_equal(
            arrays["pair_seed"], np.asarray([row[3] for row in fake.plan]))
        np.testing.assert_array_equal(arrays["original_prior"], fake.original_prior)
    calls_by_id = _call_map(result)
    pair0_candidates = [calls_by_id[row["call_index"]] for row in by_pair[0]
                        if row["role"] == "edge_state_candidate"]
    pair1_candidates = [calls_by_id[row["call_index"]] for row in by_pair[1]
                        if row["role"] == "edge_state_candidate"]
    assert pair0_candidates[0]["score_original_prior"] > pair0_candidates[1]["score_original_prior"]
    assert pair1_candidates[1]["score_original_prior"] > pair1_candidates[0]["score_original_prior"]
    for pair_index in (0, 1):
        ref_id = pairs[pair_index]["reference_call_index"]
        aux_id = pairs[pair_index]["zero_state_call_index"]
        assert calls_by_id[ref_id]["role"] == "baseline_reference"
        assert calls_by_id[aux_id]["role"] == "baseline_zero_state"
        assert calls_by_id[aux_id]["state_initialization"] == "ZERO_STATE"
        for row in by_pair[pair_index]:
            if row["role"] == "edge_state_candidate":
                assert row["state_source_call_index"] == ref_id
                assert row["state_source_iterations"] == 2
                assert row["state_initialization"] == "EDGE_STATE_SEEDED_PRIOR_SWAP"

    # Both branch arms receive the same six one-row priors; candidate state is
    # independently rebased from that frame's original captured reference.
    for row in fake.control_inputs:
        branch_index = row["branch_index"]
        original = fake.original_prior
        changed = np.flatnonzero(np.any(row["prior"] != original, axis=1))
        assert changed.shape == (1,)
        selected = int(changed[0])
        assert row["prior"][selected, GUESSES[branch_index]] == 1.0
        assert np.count_nonzero(row["prior"][selected]) == 1
        unchanged = np.ones(rescue.N, dtype=bool)
        unchanged[selected] = False
        np.testing.assert_array_equal(row["prior"][unchanged], original[unchanged])
    for row in fake.candidate_inputs:
        branch_index = row["branch_index"]
        changed = np.flatnonzero(np.any(row["prior"] != fake.original_prior, axis=1))
        assert changed.shape == (1,)
        selected = int(changed[0])
        assert row["prior"][selected, GUESSES[branch_index]] == 1.0
        assert np.count_nonzero(row["prior"][selected]) == 1
        seeded = row["state"]
        reference_state = fake.reference_states[row["pair"]]
        assert row["kwargs"]["state"] is seeded
        assert not np.shares_memory(seeded.beliefs, reference_state.beliefs)
        assert seeded.completed_sweeps == 0 and seeded.stopped_exact is False
        clean = edge_state.clean_prior(row["prior"], rescue.N, rescue.Q)
        np.testing.assert_allclose(seeded.log_prior, np.log(clean), atol=1e-12, rtol=0.0)
        expected_beliefs = np.log(clean) + edge_state.sum_check_to_var(seeded)
        np.testing.assert_allclose(seeded.beliefs, expected_beliefs, atol=1e-12, rtol=0.0)
        assert len(seeded.check_to_var) == rescue.M
        assert not np.shares_memory(
            seeded.check_to_var[0][0], reference_state.check_to_var[0][0])
    for pair_index in (0, 1):
        states = [row["state"] for row in fake.candidate_inputs if row["pair"] == pair_index]
        for left in range(len(states)):
            for right in range(left + 1, len(states)):
                assert not np.shares_memory(states[left].beliefs, states[right].beliefs)
                assert not np.shares_memory(
                    states[left].check_to_var[0][0], states[right].check_to_var[0][0])


def test_baseline_valid_and_no_active_fallback_use_reference_not_aux(
        tmp_path, monkeypatch):
    fake = EdgeStateFake(failures=(0,), branch_outcomes=False)
    original_selector = rescue.select_uncertain_variable
    original_syndrome = rescue.layout.gf32_syndrome
    no_active_pending = False
    forced_target = None

    def selector_with_no_active(h, x_hat, final_beliefs, syndrome, *, belief_provenance):
        nonlocal no_active_pending, forced_target
        if np.any(syndrome):
            # Force the documented no-active branch after a valid baseline
            # failure. The admitted source has no zero-degree checks, so this
            # specific state requires fault-injecting the selector diagnostic.
            no_active_pending = True
            forced_target = np.asarray(syndrome).copy()
            raise ValueError("baseline failure has no variables adjacent to violated checks")
        return original_selector(
            h, x_hat, final_beliefs, syndrome, belief_provenance=belief_provenance)

    def syndrome_with_no_active_once(h, x_hat):
        nonlocal no_active_pending, forced_target
        if no_active_pending:
            no_active_pending = False
            return np.asarray(forced_target, dtype=np.uint8).copy()
        return original_syndrome(h, x_hat)

    monkeypatch.setattr(probe.rescue, "select_uncertain_variable", selector_with_no_active)
    monkeypatch.setattr(probe.rescue.layout, "gf32_syndrome", syndrome_with_no_active_once)
    result = fake.execute(tmp_path, "fallback-fake")
    assert result["status"] == "COMPLETE"
    pairs = {row["pair_index"]: row for row in result["pairs"]}
    calls = _call_map(result)
    assert result["no_active_pairs"] == 1

    for pair_index, pair in pairs.items():
        ref_index = pair["reference_call_index"]
        aux_index = pair["zero_state_call_index"]
        assert ref_index != aux_index
        assert pair["candidate_selected_call_index"] != aux_index
        if pair_index != 0:
            assert pair["candidate_selected_call_index"] == ref_index
            assert pair["control_selected_call_index"] == ref_index
        else:
            assert pair["no_active"] is True
            assert pair["candidate_selected_call_index"] == ref_index
            assert pair["control_selected_call_index"] == ref_index
    pair0 = pairs[0]
    assert pair0["candidate_selected_call_index"] == pair0["reference_call_index"]
    assert pair0["candidate_selected_call_index"] != pair0["zero_state_call_index"]
    for pair_index in range(1, 192):
        ref = calls[pairs[pair_index]["reference_call_index"]]
        aux = calls[pairs[pair_index]["zero_state_call_index"]]
        assert ref["role"] == "baseline_reference"
        assert aux["role"] == "baseline_zero_state"


def test_branch_set_without_valid_output_falls_back_to_reference(tmp_path):
    fake = EdgeStateFake(failures=(0,), branch_outcomes=False)
    result = fake.execute(tmp_path, "no-valid-branch-fake")
    pair0 = next(row for row in result["pairs"] if row["pair_index"] == 0)
    assert result["status"] == "COMPLETE"
    assert result["branch_calls"] == 12
    assert pair0["control_fallback"] is True
    assert pair0["candidate_fallback"] is True
    assert pair0["control_selected_call_index"] == pair0["reference_call_index"]
    assert pair0["candidate_selected_call_index"] == pair0["reference_call_index"]
    assert pair0["candidate_selected_call_index"] != pair0["zero_state_call_index"]


def test_auxiliary_mismatch_stops_before_rescue_and_retains_partial_artifacts(tmp_path):
    fake = EdgeStateFake(failures=(0,), mismatch_aux_pair=0)
    result = fake.execute(tmp_path, "aux-mismatch-fake")
    assert result["status"] == "STOP"
    assert result["classification"] == "STOP"
    assert result["attempted_physical_calls"] == 2
    assert result["completed_pairs"] == 0
    assert result["branch_calls"] == 0
    assert result["baseline_exact"] is None
    assert result["candidate_exact"] is None
    assert "zero_state_reference_mismatch" in ";".join(result["stop_reasons"])
    assert result["pairs"][0]["equivalence_pass"] is False
    assert not all(result["pairs"][0]["equivalence"].values())
    assert Path(result["artifacts"]["summary"]).exists()
    assert Path(result["artifacts"]["calls"]).exists()
    assert Path(result["artifacts"]["frames"]).exists()
    assert Path(result["artifacts"]["diagnostics"]).exists()
    assert Path(result["artifacts"]["exploration_log"]).exists()


def test_bad_source_preflight_stop_retains_empty_diagnostics_and_null_comparisons(tmp_path):
    fake = EdgeStateFake()
    def empty_source():
        fake.source_reads += 1
        return {}
    fake.source_reader = empty_source
    result = fake.execute(tmp_path, "empty-source-fake")

    assert result["status"] == "STOP"
    assert result["classification"] == "STOP"
    assert result["attempted_physical_calls"] == 0
    assert result["sampled_pairs"] == result["completed_pairs"] == 0
    assert fake.source_reads == 1
    assert result["baseline_exact"] is result["control_exact"] is result["candidate_exact"] is None
    assert result["per_graph"] is None and result["paired"] is None
    arrays = np.load(result["artifacts"]["diagnostics"])
    assert arrays["source_H"].shape == (0, rescue.M, rescue.N)
    assert arrays["pair_truth"].shape == (0, rescue.N)
    assert Path(result["artifacts"]["summary"]).exists()


def _screen_summary(*, baseline=39, control=40, candidate=46,
                    deltas=(2, 1, 1, 1, 1, 0), selected_wrong_candidate=0,
                    selected_wrong_control=0, raw_wrong_candidate=0, raw_wrong_control=0):
    return {
        "baseline_exact": baseline, "control_exact": control,
        "candidate_exact": candidate,
        "per_graph": {str(i): {"delta_exact": delta}
                      for i, delta in enumerate(deltas)},
        "syndrome_valid_wrong_candidate": selected_wrong_candidate,
        "syndrome_valid_wrong_control": selected_wrong_control,
        "raw_branch_valid_wrong_candidate": raw_wrong_candidate,
        "raw_branch_valid_wrong_control": raw_wrong_control,
    }


def test_exact_classifier_integer_boundaries():
    assert probe._classification(_screen_summary()) == "INCREMENT_SCREEN_MET"
    assert probe._classification(_screen_summary(baseline=153, control=154, candidate=160)) == "INCREMENT_SCREEN_MET"
    assert probe._classification(_screen_summary(baseline=38)) == "INCREMENT_SCREEN_UNINFORMATIVE"
    assert probe._classification(_screen_summary(baseline=154)) == "INCREMENT_SCREEN_UNINFORMATIVE"
    assert probe._classification(_screen_summary(control=39, candidate=45)) == "INCREMENT_SCREEN_UNINFORMATIVE"
    assert probe._classification(_screen_summary(candidate=45)) == "INCREMENT_SCREEN_NOT_MET"
    assert probe._classification(_screen_summary(deltas=(4, 1, 1, 0, 0, 0))) == "INCREMENT_SCREEN_NOT_MET"
    assert probe._classification(_screen_summary(selected_wrong_candidate=1)) == "INCREMENT_SCREEN_NOT_MET"
    assert probe._classification(_screen_summary(raw_wrong_candidate=1)) == "INCREMENT_SCREEN_NOT_MET"


def test_physical_call_cap_retains_incomplete_artifacts_and_null_totals(tmp_path, monkeypatch):
    fake = EdgeStateFake(failures=(0,))
    monkeypatch.setattr(probe, "MAX_PHYSICAL_CALLS", 3)
    result = fake.execute(tmp_path, "call-cap-fake")
    assert result["status"] == "INCOMPLETE"
    assert result["attempted_physical_calls"] == 3
    assert result["completed_pairs"] == 0
    assert result["baseline_exact"] is None
    assert result["control_exact"] is None
    assert result["candidate_exact"] is None
    assert result["delta_exact"] is None
    assert Path(result["artifacts"]["summary"]).exists()
    assert Path(result["artifacts"]["exploration_log"]).exists()
    with np.load(result["artifacts"]["diagnostics"]) as arrays:
        failed_reference = int(result["pairs"][0]["reference_call_index"])
        assert failed_reference in arrays["baseline_failure_call_index"]
        assert failed_reference in arrays["baseline_belief_call_index"]
        assert arrays["baseline_failure_c2v_row"].size > 0
        assert arrays["baseline_failure_c2v_column"].size == arrays["baseline_failure_c2v_row"].size
        assert arrays["baseline_failure_c2v_message"].shape == (
            arrays["baseline_failure_c2v_row"].size, rescue.Q)


def test_post_artifact_rss_cap_keeps_full_work_as_incomplete_with_null_totals(tmp_path):
    fake = EdgeStateFake(failures=())
    rss_calls = 0

    def rss_after_first_pass():
        nonlocal rss_calls
        rss_calls += 1
        # Each decoder call samples RSS before, immediately after and during
        # its after-call gate: 3*384 values. The next sample is post-artifact.
        return probe.RSS_CAP_BYTES + 1 if rss_calls >= 3 * 384 + 1 else 100_000

    result = fake.execute(tmp_path, "postwrite-rss-fake", rss_fn=rss_after_first_pass)
    assert rss_calls == 3 * 384 + 1
    assert result["status"] == "INCOMPLETE"
    assert result["completed_pairs"] == 192
    assert result["attempted_physical_calls"] == 384
    assert result["resource_violations"] == 1
    assert result["baseline_exact"] is None
    assert result["candidate_exact"] is None
    saved_summary = json.loads(Path(result["artifacts"]["summary"]).read_text())
    assert saved_summary["classification"] == "INCOMPLETE"
    assert saved_summary["candidate_exact"] is None
    assert Path(result["artifacts"]["diagnostics"]).exists()


def test_t0_and_dry_run_are_source_free_and_do_not_create_root(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "_bind_production", lambda: pytest.fail(
        "T0 and dry-run must not bind production"))
    t0 = probe.verify_t0()
    assert probe.SEED_NAMESPACE == "gf32-softprior-edge-state-r2-v1"
    assert probe.OUT_ROOT_RELATIVE == Path("workspace") / "gf32_edge_state_r2_3aaa1d95"
    assert probe.CONTRACT == "NBLDPC-GF32-EDGE-STATE-R2-20261004/PREREG_AND_AUTH.md"
    assert t0["prior_exclusion_plan_count"] == 21
    assert t0["prior_exclusion_rows"] == 4368
    assert t0["additional_seed_plans"] == 8
    assert t0["source_reads"] == t0["sampler_calls"] == t0["decoder_calls"] == t0["writes"] == 0

    root = tmp_path / "workspace" / probe.OUT_ROOT_RELATIVE.name
    dry = probe.dry_run(repo_root=tmp_path)
    assert dry["status"] == "DRY_RUN"
    assert dry["source_reads"] == dry["sampler_calls"] == dry["decoder_calls"] == dry["writes"] == 0
    assert not root.exists()


def test_existing_frozen_root_is_refused_before_any_fake_callback(tmp_path):
    root = tmp_path / "workspace" / "official"
    root.mkdir(parents=True)
    fake = EdgeStateFake()
    with pytest.raises(FileExistsError, match="refusing existing output root"):
        probe.execute_batch(
            source_reader=fake.source_reader, sampler=fake.sampler,
            decode_fns=fake.decode_fns(), out_root=Path("workspace") / "official",
            repo_root=tmp_path, official_root=Path("workspace") / "official",
            now=lambda: 10.0, rss_fn=lambda: 100_000,
        )
    assert fake.source_reads == 0
    assert fake.sampled_seeds == []
    assert fake.decoder_calls == []
