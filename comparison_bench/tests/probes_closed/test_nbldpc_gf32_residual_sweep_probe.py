"""Explicit-fake E3-E5 gates for the GF(32) residual-sweep probe."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.cli.probes_closed import nbldpc_gf32_residual_sweep_probe as probe
from comparison_bench.cli.probes_closed import nbldpc_gf32_softprior_rescue as rescue
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from .test_nbldpc_gf32_mechanism_pair import _decode_result, _fake_source, _truth


def _kernel_word() -> np.ndarray:
    value = np.zeros(rescue.N, dtype=np.uint8)
    value[:3] = 1
    return value


class FakeClock:
    def __init__(self, value: float = 10.0):
        self.value = float(value)

    def __call__(self) -> float:
        return self.value


class FakeResidualBatch:
    """Explicit source/sampler/decoder seams; no NPZ reader or production BP."""

    def __init__(self, *, iterations: int = 90,
                 wrong_candidate_pairs: tuple[int, ...] = (),
                 control_failed_pairs: tuple[int, ...] = (),
                 control_wrong_pairs: tuple[int, ...] = (),
                 candidate_success_pairs: tuple[int, ...] = (),
                 canary_belief_mismatch: bool = False,
                 canary_timeout: bool = False):
        self.plan = rescue.build_seed_plan(probe.SEED_NAMESPACE)
        self.pair_for_seed = {int(row[3]): index for index, row in enumerate(self.plan)}
        self.iterations = int(iterations)
        self.wrong_candidate_pairs = set(wrong_candidate_pairs)
        self.control_failed_pairs = set(control_failed_pairs)
        self.control_wrong_pairs = set(control_wrong_pairs)
        self.candidate_success_pairs = set(candidate_success_pairs)
        self.canary_belief_mismatch = canary_belief_mismatch
        self.canary_timeout = canary_timeout
        self.clock = FakeClock()
        self.current_pair = -1
        self.truth = _truth().copy()
        self.source_reads = 0
        self.sampler_calls = 0
        self.sampled_seeds: list[int] = []
        self.decoder_inputs: list[dict] = []

    def source_reader(self):
        self.source_reads += 1
        return _fake_source()

    def sampler(self, seed, pmf, *, width):
        self.sampler_calls += 1
        self.current_pair = self.pair_for_seed[int(seed)]
        self.sampled_seeds.append(int(seed))
        assert width == rescue.N
        np.testing.assert_allclose(pmf, rescue.pmf(), rtol=0.0, atol=1e-15)
        return self.truth.copy()

    def _record(self, role, h, prior, syndrome, kwargs):
        row = {
            "role": role, "pair": self.current_pair,
            "H": np.asarray(h).copy(), "prior": np.asarray(prior).copy(),
            "syndrome": np.asarray(syndrome).copy(), "kwargs": dict(kwargs),
        }
        self.decoder_inputs.append(row)
        return row

    def _raw(self, h, *, vector, syndrome, beliefs=None):
        return _decode_result(
            h, vector, syndrome,
            beliefs=(np.zeros((rescue.N, rescue.Q), dtype=np.float64)
                     if beliefs is None else beliefs),
            iterations=self.iterations)

    def _control_vector(self, pair: int) -> np.ndarray:
        vector = self.truth.copy()
        if pair in self.control_wrong_pairs:
            vector ^= _kernel_word()
        elif pair in self.control_failed_pairs:
            vector[127] ^= 1
        return vector

    def reference(self, h, prior, syndrome, **kwargs):
        self._record("reference", h, prior, syndrome, kwargs)
        result = self._raw(
            h, vector=self._control_vector(self.current_pair), syndrome=syndrome)
        if self.canary_timeout and self.current_pair == 0:
            # The canary measures the reference plus auxiliary natural call.
            self.clock.value += probe.CANARY_CAP_S + 1.0
        return result

    def _helper_result(self, h, *, vector, syndrome, natural: bool,
                       beliefs=None):
        raw = self._raw(h, vector=vector, syndrome=syndrome, beliefs=beliefs)
        edge_count = int(np.count_nonzero(h))
        rows = tuple(range(rescue.M))
        if natural:
            row_orders = tuple(rows for _ in range(self.iterations))
            first_scores = ()
            score_checks = score_edges = 0
        else:
            reverse = tuple(reversed(rows))
            row_orders = tuple(reverse for _ in range(self.iterations))
            first_scores = tuple(float(x) for x in range(rescue.M))
            score_checks = self.iterations * rescue.M
            score_edges = self.iterations * edge_count
        return SimpleNamespace(
            **vars(raw), row_orders=row_orders,
            first_sweep_residuals=first_scores,
            score_check_updates=score_checks,
            applied_check_updates=self.iterations * rescue.M,
            score_edge_updates=score_edges,
            applied_edge_updates=self.iterations * edge_count,
        )

    def natural(self, h, prior, syndrome, **kwargs):
        self._record("natural", h, prior, syndrome, kwargs)
        beliefs = np.zeros((rescue.N, rescue.Q), dtype=np.float64)
        if self.canary_belief_mismatch and self.current_pair == 0:
            beliefs[0, 0] = 1e-4
        return self._helper_result(
            h, vector=self._control_vector(self.current_pair), syndrome=syndrome,
            natural=True, beliefs=beliefs)

    def residual(self, h, prior, syndrome, **kwargs):
        self._record("residual", h, prior, syndrome, kwargs)
        vector = self._control_vector(self.current_pair)
        if self.current_pair in self.wrong_candidate_pairs:
            vector = self.truth.copy() ^ _kernel_word()
        elif self.current_pair in self.candidate_success_pairs:
            vector = self.truth.copy()
        assert (np.array_equal(layout.gf32_syndrome(h, vector), syndrome)
                == (self.current_pair not in self.control_failed_pairs
                    or self.current_pair in self.candidate_success_pairs
                    or self.current_pair in self.wrong_candidate_pairs
                    or self.current_pair in self.control_wrong_pairs))
        if self.current_pair in self.wrong_candidate_pairs:
            assert np.array_equal(layout.gf32_syndrome(h, vector), syndrome)
        return self._helper_result(
            h, vector=vector, syndrome=syndrome, natural=False)

    def decode_fns(self):
        return {
            "reference": self.reference,
            "natural": self.natural,
            "residual": self.residual,
        }

    def execute(self, repo_root: Path, *, out_root=None, rss_fn=None):
        return probe.execute_batch(
            source_reader=self.source_reader, sampler=self.sampler,
            decode_fns=self.decode_fns(),
            out_root=probe.OUT_ROOT_RELATIVE if out_root is None else out_root,
            repo_root=repo_root, now=self.clock,
            rss_fn=(lambda: 100_000) if rss_fn is None else rss_fn,
            command="explicit-fake residual sweep")


def _assert_partial_null(result):
    assert result["run_status"] == "INCOMPLETE"
    assert result["classification"] is None
    for key in (
            "control_exact", "candidate_exact", "delta", "paired_both",
            "paired_control_only", "paired_candidate_only", "paired_neither",
            "control_syndrome_valid_wrong", "candidate_syndrome_valid_wrong",
            "positive_graph_deltas", "per_graph"):
        assert result[key] is None, key
    for name in ("summary", "calls", "frames", "diagnostics", "exploration_log"):
        assert Path(result["artifacts"][name]).exists(), name


def test_e5_t0_dry_source_free_seed_exclusions_and_root_refusal(tmp_path):
    t0 = probe.verify_t0()
    rows, records = probe.validate_seed_plan()
    dry = probe.dry_run(repo_root=tmp_path)

    assert t0["status"] == "PASS"
    assert t0["batch_uuid"] == probe.BATCH_UUID
    assert t0["contract"] == probe.CONTRACT
    assert t0["seed_namespace"] == probe.SEED_NAMESPACE
    assert t0["holdout_pairs"] == 192
    assert t0["prior_exclusion_plan_count"] == 23
    assert t0["prior_exclusion_rows"] == 4752
    assert all(t0[key] == 0 for key in (
        "source_reads", "sampler_calls", "decoder_calls", "writes"))
    assert len(rows) == len({row[3] for row in rows}) == 192
    assert len(records) == 23
    assert sum(int(row["rows"]) for row in records) == 4752
    assert dry["status"] == "DRY_RUN"
    assert all(dry[key] == 0 for key in (
        "source_reads", "sampler_calls", "decoder_calls", "writes"))
    assert not (tmp_path / probe.OUT_ROOT_RELATIVE).exists()

    fake = FakeResidualBatch(iterations=1)
    with pytest.raises(ValueError, match="out-root must equal frozen fresh root"):
        fake.execute(tmp_path, out_root=Path("workspace") / "wrong-residual-root")
    assert fake.source_reads == fake.sampler_calls == 0
    assert fake.decoder_inputs == []

    existing = tmp_path / probe.OUT_ROOT_RELATIVE
    existing.mkdir(parents=True)
    with pytest.raises(FileExistsError):
        fake.execute(tmp_path)
    assert fake.source_reads == fake.sampler_calls == 0
    assert fake.decoder_inputs == []


def test_e3_complete_192_fake_pairs_reuse_canary_prefix_and_separate_truth_wrong(tmp_path):
    failed = (1, 33, 65, 97, 129, 161, 2, 34, 66, 98, 130)
    gains = (1, 33, 65, 97, 129, 161, 3)
    fake = FakeResidualBatch(
        iterations=90, control_failed_pairs=failed,
        control_wrong_pairs=(3,), candidate_success_pairs=gains,
        wrong_candidate_pairs=(20,))
    result = fake.execute(tmp_path)

    assert result["run_status"] == "COMPLETE"
    # Fake outcomes intentionally cross the frozen positive screen; this only
    # exercises classifier routing, not scientific acceptance.
    assert result["classification"] == "EXPLORATORY_INCREMENT_SIGNAL"
    assert result["planned_pairs"] == result["sampled_pairs"] == 192
    assert result["completed_pairs"] == 192
    assert fake.source_reads == 1
    assert fake.sampler_calls == 192
    assert fake.sampled_seeds == [row[3] for row in fake.plan]
    assert len(set(fake.sampled_seeds)) == 192
    assert len(result["calls"]) == 385
    assert result["physical_calls"] == result["attempted_physical_calls"] == 385
    assert result["control_calls"] == result["candidate_calls"] == 192
    assert result["auxiliary_calls"] == 1
    assert len(fake.decoder_inputs) == 385
    assert [row["role"] for row in fake.decoder_inputs[:3]] == [
        "reference", "natural", "residual"]
    assert sum(row["role"] == "natural" for row in fake.decoder_inputs) == 1
    assert sum(row["role"] == "reference" for row in fake.decoder_inputs) == 192
    assert sum(row["role"] == "residual" for row in fake.decoder_inputs) == 192

    canary = result["canary"]
    assert canary["passed"] is True
    assert canary["reference_call_index"] == 0
    assert canary["aux_call_index"] == 1
    assert canary["max_abs_belief_diff"] == 0.0
    assert result["calls"][0]["role"] == "control_reference"
    assert result["calls"][1]["role"] == "canary_aux_natural"
    assert result["calls"][2]["role"] == "residual_candidate"
    assert result["frames"][0]["control_call_index"] == 0
    assert result["frames"][0]["candidate_call_index"] == 2

    expected_kwargs = {
        "max_iter": 90, "damping_alpha": 1.0,
        "warm_beliefs": None, "field": None,
    }
    expected_prior = np.tile(rescue.pmf(), (rescue.N, 1))
    for row in fake.decoder_inputs:
        assert row["kwargs"] == expected_kwargs
        np.testing.assert_array_equal(row["prior"], expected_prior)
        assert row["H"].shape == (rescue.M, rescue.N)
        assert row["syndrome"].shape == (rescue.M,)
        # The decoder seam receives no truth argument; truth is used only by
        # the runner after return to classify exact vs syndrome-valid-wrong.
        assert "truth" not in row["kwargs"]

    assert result["control_exact"] == 180
    assert result["candidate_exact"] == 186
    assert result["delta"] == 6
    assert result["positive_graph_deltas"] == 6
    assert result["candidate_syndrome_valid_wrong"] == 1
    assert result["control_syndrome_valid_wrong"] == 1
    first = result["frames"][0]
    assert first["candidate_exact"] is True
    assert first["candidate_syndrome_valid_wrong"] is False
    wrong_frame = result["frames"][20]
    assert wrong_frame["control_exact"] is True
    assert wrong_frame["candidate_exact"] is False
    assert wrong_frame["candidate_syndrome_valid_wrong"] is True
    candidate_rows = [row for row in result["calls"]
                      if row["role"] == "residual_candidate"]
    assert len(candidate_rows) == 192
    assert all(row["score_check_updates"] == 90 * rescue.M for row in candidate_rows)
    assert all(row["applied_check_updates"] == 90 * rescue.M for row in candidate_rows)
    assert all(row["score_edge_updates"] == 90 * 256 for row in candidate_rows)
    assert all(row["applied_edge_updates"] == 90 * 256 for row in candidate_rows)

    # The full fake run reaches the frozen worst-case schedule accounting.
    assert result["physical_sweeps"] == probe.MAX_PHYSICAL_SWEEPS == 34_650
    assert result["score_check_updates"] == probe.MAX_CANDIDATE_SCORE_KERNELS == 898_560
    assert result["applied_check_updates"] == (
        probe.MAX_REFERENCE_APPLIED_KERNELS + probe.MAX_CANDIDATE_APPLIED_KERNELS)
    assert result["applied_check_updates"] == 1_801_800
    assert result["kernel_evaluations"] == probe.MAX_KERNEL_EVALUATIONS == 2_700_360
    assert result["score_edge_updates"] == probe.MAX_SCORE_EDGE_UPDATES == 4_423_680
    assert result["applied_edge_updates"] == probe.MAX_APPLIED_EDGE_UPDATES == 8_870_400
    assert result["edge_updates"] == probe.MAX_EDGE_UPDATES == 13_294_080
    assert result["caps"]["canary_wall_s"] == 30.0
    assert result["caps"]["total_wall_s"] == 1200.0
    assert result["caps"]["rss_bytes"] == 1024 ** 3
    assert result["caps"]["artifact_bytes"] == 20 * 1024 * 1024

    with np.load(result["artifacts"]["diagnostics"], allow_pickle=False) as arrays:
        assert len(arrays["first_sweep_score_call_index"]) == 192
        assert arrays["first_sweep_residuals"].shape == (192, rescue.M)
        # The diagnostics retain the auxiliary natural canary's sweep trace
        # before all 192 residual candidate traces.
        assert len(arrays["row_order_call_index"]) == 193 * 90
        assert len(arrays["row_order_values"]) == 193 * 90 * rescue.M
        np.testing.assert_array_equal(
            arrays["first_sweep_score_call_index"],
            [row["call_index"] for row in candidate_rows])
        np.testing.assert_array_equal(
            arrays["row_order_values"][:rescue.M],
            np.arange(rescue.M, dtype=np.uint8))
        np.testing.assert_array_equal(
            arrays["row_order_call_index"][:90], np.full(90, 1))
        np.testing.assert_array_equal(
            arrays["row_order_call_index"][90:180], np.full(90, 2))
        candidate_first_sweep = 90 * rescue.M
        np.testing.assert_array_equal(
            arrays["row_order_values"][candidate_first_sweep:
                                       candidate_first_sweep + rescue.M],
            np.arange(rescue.M - 1, -1, -1, dtype=np.uint8))


@pytest.mark.parametrize("failure", ["belief", "time"])
def test_e3_canary_failure_retains_prefix_and_never_calls_candidate(tmp_path, failure):
    fake = FakeResidualBatch(
        iterations=2,
        canary_belief_mismatch=(failure == "belief"),
        canary_timeout=(failure == "time"))
    result = fake.execute(tmp_path)

    if failure == "time":
        # The >30s canary resource cap is incomplete with null full totals;
        # numerical canary mismatches are STOPs.
        _assert_partial_null(result)
    else:
        assert result["run_status"] == "STOP"
        assert result["classification"] is None
    assert result["physical_calls"] == 2
    assert result["completed_pairs"] == 0
    assert result["candidate_calls"] == 0
    assert [row["role"] for row in result["calls"]] == [
        "control_reference", "canary_aux_natural"]
    assert result["canary"]["passed"] is False
    if failure == "time":
        assert result["canary"]["total_wall_s"] > probe.CANARY_CAP_S
        assert result["canary"]["checks"]["within_30s"] is False
    else:
        assert result["canary"]["checks"]["final_beliefs_atol_1e12_rtol_0"] is False
    for name in ("summary", "calls", "frames", "diagnostics", "exploration_log"):
        assert Path(result["artifacts"][name]).exists()
    saved = json.loads(Path(result["artifacts"]["summary"]).read_text())
    assert saved["run_status"] == result["run_status"]
    assert saved["classification"] is None


def test_e4_call_and_kernel_caps_retain_partial_null_totals(tmp_path, monkeypatch):
    fake = FakeResidualBatch(iterations=1, wrong_candidate_pairs=())
    monkeypatch.setattr(probe, "MAX_PHYSICAL_CALLS", 2)
    result = fake.execute(tmp_path / "call-cap")

    assert result["run_status"] == "INCOMPLETE"
    assert result["physical_calls"] == probe.MAX_PHYSICAL_CALLS == 2
    assert result["completed_pairs"] == 0
    assert [row["role"] for row in result["calls"]] == [
        "control_reference", "canary_aux_natural"]
    _assert_partial_null(result)

    # A complete returned reference call may cross a work cap; it is retained,
    # counted, and marks the entire comparison incomplete without full totals.
    fake = FakeResidualBatch(iterations=1, wrong_candidate_pairs=())
    monkeypatch.setattr(probe, "MAX_PHYSICAL_CALLS", 385)
    monkeypatch.setattr(probe, "MAX_KERNEL_EVALUATIONS", 1)
    work_limited = fake.execute(tmp_path / "kernel-cap")

    assert work_limited["run_status"] == "INCOMPLETE"
    assert work_limited["physical_calls"] == 1
    assert work_limited["calls"][0]["status"] == "RESOURCE_STOP_AFTER_RETURN"
    assert work_limited["kernel_evaluations"] > probe.MAX_KERNEL_EVALUATIONS
    _assert_partial_null(work_limited)


@pytest.mark.parametrize("limit_name,limit_value,reason", [
    ("MAX_PHYSICAL_SWEEPS", 0, "physical_sweep_cap"),
    ("MAX_EDGE_UPDATES", 0, "edge_update_cap"),
])
def test_e4_sweep_and_edge_caps_stop_after_complete_call(tmp_path, monkeypatch,
                                                          limit_name, limit_value, reason):
    monkeypatch.setattr(probe, limit_name, limit_value)
    result = FakeResidualBatch(iterations=1, wrong_candidate_pairs=()).execute(
        tmp_path / "work-cap")

    assert result["run_status"] == "INCOMPLETE"
    assert result["physical_calls"] == 1
    assert reason in result["stop_reasons"]
    assert result["calls"][0]["status"] == "RESOURCE_STOP_AFTER_RETURN"
    _assert_partial_null(result)


def test_e4_wall_rss_and_artifact_caps_are_bounded_and_incomplete(tmp_path, monkeypatch):
    fake = FakeResidualBatch(iterations=1, wrong_candidate_pairs=())
    ticks = iter((0.0, probe.WALL_CAP_S + 1.0))
    fake.clock = lambda: next(ticks, probe.WALL_CAP_S + 1.0)
    wall_limited = fake.execute(tmp_path / "wall-cap")
    assert wall_limited["run_status"] == "INCOMPLETE"
    assert wall_limited["physical_calls"] == 0
    _assert_partial_null(wall_limited)

    fake = FakeResidualBatch(iterations=1, wrong_candidate_pairs=())
    rss_limited = fake.execute(
        tmp_path / "rss-cap",
        rss_fn=lambda: probe.RSS_CAP_BYTES + 1)
    assert rss_limited["run_status"] == "INCOMPLETE"
    assert rss_limited["physical_calls"] == 0
    assert "rss_cap" in rss_limited["stop_reasons"]
    _assert_partial_null(rss_limited)

    monkeypatch.setattr(probe, "ARTIFACT_CAP_BYTES", 0)
    artifact_limited = FakeResidualBatch(
        iterations=1, wrong_candidate_pairs=()).execute(
            tmp_path / "artifact-cap")
    assert artifact_limited["run_status"] == "INCOMPLETE"
    assert artifact_limited["physical_calls"] == 385
    assert artifact_limited["classification"] is None
    assert artifact_limited["control_exact"] is None
    assert artifact_limited["candidate_exact"] is None
    assert "artifact_bytes_cap" in artifact_limited["stop_reasons"]
    assert Path(artifact_limited["artifacts"]["summary"]).exists()


@pytest.mark.parametrize("late_limit", ["wall", "rss"])
def test_e4_after_write_wall_and_rss_caps_null_complete_totals(
        tmp_path, monkeypatch, late_limit):
    fake = FakeResidualBatch(iterations=1)
    original_write_csv = probe._write_csv
    rss_state = {"bytes": 100_000}

    def write_csv_then_cross_limit(path, rows, fields):
        original_write_csv(path, rows, fields)
        if Path(path).name == "frames.csv":
            # Cross the resource cap only after CSV and NPZ evidence has been
            # written, so pre-call and post-decoder checks cannot detect it.
            if late_limit == "wall":
                fake.clock.value += probe.WALL_CAP_S + 1.0
            else:
                rss_state["bytes"] = probe.RSS_CAP_BYTES + 1

    monkeypatch.setattr(probe, "_write_csv", write_csv_then_cross_limit)
    result = fake.execute(
        tmp_path / f"after-write-{late_limit}",
        rss_fn=lambda: rss_state["bytes"])

    assert result["run_status"] == "INCOMPLETE"
    assert result["classification"] is None
    assert result["physical_calls"] == 385
    assert result["completed_pairs"] == 192
    reason = "total_wall_cap" if late_limit == "wall" else "rss_cap"
    assert reason in result["stop_reasons"]
    _assert_partial_null(result)

    for name in ("manifest", "summary", "calls", "frames", "diagnostics",
                 "exploration_log"):
        assert Path(result["artifacts"][name]).exists(), name
    saved = json.loads(Path(result["artifacts"]["summary"]).read_text())
    manifest = json.loads(Path(result["artifacts"]["manifest"]).read_text())
    assert saved["run_status"] == manifest["run_status"] == "INCOMPLETE"
    assert saved["classification"] is None
    assert saved["stop_reasons"] == result["stop_reasons"]
