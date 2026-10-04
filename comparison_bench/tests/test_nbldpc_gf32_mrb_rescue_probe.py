from __future__ import annotations

import csv
from dataclasses import dataclass
import json
import math
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_mrb_rescue_probe as probe
from comparison_bench.formal_ir import nonbinary_field
from comparison_bench.formal_ir import nonbinary_v19_osd


@dataclass
class FakeResult:
    x_hat: np.ndarray
    syndrome_ok: bool
    iterations: int
    runtime_s: float
    status: str
    final_beliefs: np.ndarray
    belief_provenance: str = "CHECK_UPDATED"
    extrinsic_log_beliefs: np.ndarray | None = None
    extrinsic_provenance: str | None = "CHECK_EXTRINSIC"


def _syndrome(field, matrix, vector):
    out = []
    for row in matrix:
        total = 0
        for coefficient, symbol in zip(row, vector):
            total = field.add(total, field.mul(int(coefficient), int(symbol)))
        out.append(total)
    return np.asarray(out, dtype=np.int64)


def _raw(*, x=None, syndrome_ok=False, beliefs=None, status="bp_failed"):
    if x is None:
        x = np.zeros(probe.N, dtype=np.uint8)
    if beliefs is None:
        beliefs = np.zeros((probe.N, 32), dtype=np.float64)
    return FakeResult(np.asarray(x, dtype=np.uint8), syndrome_ok, 3, 0.02,
                      status, np.asarray(beliefs, dtype=np.float64))


def test_t0_and_dry_run_are_no_write_no_graph_decoder_or_osd(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "OUT_ROOT_RELATIVE", Path("workspace/mrb-t0"))
    monkeypatch.setattr(
        probe.nonbinary_v19_osd, "osd_decode_candidates_mrb",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("OSD in T0")))
    monkeypatch.setattr(
        probe.search_runner, "build_profile_graph",
        lambda seed: (_ for _ in ()).throw(AssertionError("graph in T0")))
    monkeypatch.setattr(
        probe, "_bind_production_decoder",
        lambda: (_ for _ in ()).throw(AssertionError("decoder bind in T0")))

    result = probe.dry_run("workspace/mrb-t0", repo_root=tmp_path)
    root = tmp_path / "workspace/mrb-t0"
    assert result["status"] == "DRY_RUN"
    assert result["writes"] == result["decoder_calls"] == result["mrb_calls"] == 0
    assert result["graph_construction_calls"] == result["artifact_reads"] == 0
    assert result["holdout_pair_count"] == 192
    assert result["holdout_call_count"] == 384
    assert result["max_candidates_per_rescue"] == 256
    assert not root.exists()


def test_tiny_gf32_mrb_order0_order1_and_original_column_coordinates():
    field = nonbinary_field.GF2mField.create(32)
    matrix = np.asarray([[1, 2, 0], [0, 1, 1]], dtype=np.int64)
    truth = np.asarray([4, 7, 3], dtype=np.int64)
    syndrome = _syndrome(field, matrix, truth)
    hard = np.zeros(3, dtype=np.int64)
    beliefs = np.zeros((3, 32), dtype=np.float64)
    beliefs[0, 1] = 5.0
    beliefs[1, 2] = 1.0
    beliefs[2, 3] = 3.0

    base = nonbinary_v19_osd.osd_decode_candidates_mrb(
        field=field, matrix=matrix, syndrome=syndrome,
        beliefs=beliefs, e_hat=hard, order=0, top_info=None,
        top_symbols=None, max_candidates=256)
    candidates = nonbinary_v19_osd.osd_decode_candidates_mrb(
        field=field, matrix=matrix, syndrome=syndrome,
        beliefs=beliefs, e_hat=hard, order=1, top_info=None,
        top_symbols=None, max_candidates=256)

    assert len(base) == 1
    assert len(candidates) == 32  # one free coordinate, base plus 31 symbols
    assert len({tuple(row) for row in candidates}) == len(candidates)
    assert tuple(truth.tolist()) in {tuple(row) for row in candidates}
    assert all(np.array_equal(_syndrome(field, matrix, row), syndrome)
               for row in base + candidates)
    assert all(len(row) == 3 for row in candidates)  # original column order


def test_tiny_gf32_mrb_candidate_cap_includes_base_and_order1_is_unique():
    field = nonbinary_field.GF2mField.create(32)
    matrix = np.zeros((1, 10), dtype=np.int64)
    beliefs = np.zeros((10, 32), dtype=np.float64)
    candidates = nonbinary_v19_osd.osd_decode_candidates_mrb(
        field=field, matrix=matrix, syndrome=[0], beliefs=beliefs,
        e_hat=np.zeros(10, dtype=np.int64), order=1, top_info=None,
        top_symbols=None, max_candidates=256)
    assert len(candidates) == 256
    assert len({tuple(row) for row in candidates}) == 256
    assert all(np.array_equal(_syndrome(field, matrix, row), [0])
               for row in candidates)


def test_rescue_uses_original_syndrome_scores_every_candidate_and_does_not_mutate_raw():
    field = nonbinary_field.GF2mField.create(32)
    matrix = np.zeros((1, probe.N), dtype=np.int64)
    matrix[0, :2] = 1
    syndrome = np.asarray([3], dtype=np.int64)
    pmf = np.asarray(probe.shape_pmf_grid()[0]["pmf"], dtype=np.float64)
    prior = np.tile(pmf, (probe.N, 1))
    raw = _raw()
    less_likely = np.zeros(probe.N, dtype=np.int64)
    less_likely[0:2] = [1, 2]  # symbol 2 is floored by the frozen prior rule
    best = np.zeros(probe.N, dtype=np.int64)
    best[0] = 3
    seen = {}

    def fake_mrb(**kwargs):
        seen.update(kwargs)
        return [less_likely.copy(), best.copy()]

    selected, metadata, issue = probe._candidate_vectors(
        raw, matrix, prior, syndrome, now=lambda: 10.0, rss_fn=lambda: 100,
        started=0.0, arm_started=0.0, mrb_fn=fake_mrb, field=field)

    assert issue == ""
    assert seen["matrix"] is matrix or np.array_equal(seen["matrix"], matrix)
    assert np.array_equal(seen["syndrome"], syndrome)  # original H*x=s target
    assert seen["order"] == 1 and seen["top_info"] is None
    assert seen["top_symbols"] is None and seen["max_candidates"] == 256
    assert np.array_equal(seen["e_hat"], raw.x_hat)
    assert metadata["raw_syndrome_accept"] is False
    assert metadata["rescue_attempted"] is True
    assert metadata["candidate_count"] == 2
    assert metadata["rescue_status"] == "rescued"
    assert np.array_equal(selected.x_hat, best)
    assert selected is not raw
    assert selected.syndrome_ok is True
    assert selected.status == "mrb_rescued_order1"
    assert np.array_equal(raw.x_hat, np.zeros(probe.N, dtype=np.uint8))
    assert raw.status == "bp_failed" and raw.syndrome_ok is False
    assert metadata["selected_prior_score"] == pytest.approx(
        float(probe._effective_log_prior(prior)[0, 3]
              + probe._effective_log_prior(prior)[1:, 0].sum()))


def test_rescue_wall_includes_candidate_scoring(monkeypatch):
    field = nonbinary_field.GF2mField.create(32)
    matrix = np.zeros((1, probe.N), dtype=np.int64)
    matrix[0, 0] = 1
    syndrome = np.asarray([3], dtype=np.int64)
    prior = np.tile(np.asarray(probe.shape_pmf_grid()[0]["pmf"]),
                    (probe.N, 1))
    raw = _raw()
    candidate = np.zeros(probe.N, dtype=np.int64)
    candidate[0] = 3
    clock = {"now": 0.0}
    real_fsum = math.fsum

    def slow_fsum(values):
        clock["now"] += 3.0
        return real_fsum(values)

    def fake_mrb(**_kwargs):
        clock["now"] += 1.0
        return [candidate.copy()]

    monkeypatch.setattr(probe.math, "fsum", slow_fsum)
    selected, metadata, issue = probe._candidate_vectors(
        raw, matrix, prior, syndrome, now=lambda: clock["now"],
        rss_fn=lambda: 100, started=0.0, arm_started=0.0,
        mrb_fn=fake_mrb, field=field)

    assert issue == ""
    assert np.array_equal(selected.x_hat, candidate)
    assert metadata["mrb_helper_wall_s"] == pytest.approx(1.0)
    assert metadata["rescue_wall_s"] == pytest.approx(4.0)
    assert metadata["rescue_wall_s"] > metadata["mrb_helper_wall_s"]


def test_rescue_tie_uses_lexicographically_smallest_and_empty_retains_raw():
    field = nonbinary_field.GF2mField.create(32)
    matrix = np.zeros((1, probe.N), dtype=np.int64)
    matrix[0, :2] = 1
    syndrome = np.asarray([3], dtype=np.int64)
    pmf = np.asarray(probe.shape_pmf_grid()[0]["pmf"], dtype=np.float64)
    prior = np.tile(pmf, (probe.N, 1))
    raw = _raw()
    left = np.zeros(probe.N, dtype=np.int64)
    left[0] = 3
    right = np.zeros(probe.N, dtype=np.int64)
    right[1] = 3
    now = lambda: 1.0
    rss = lambda: 1

    selected, metadata, issue = probe._candidate_vectors(
        raw, matrix, prior, syndrome, now=now, rss_fn=rss, started=0.0,
        arm_started=0.0, mrb_fn=lambda **kwargs: [left, right], field=field)
    assert issue == ""
    assert np.array_equal(selected.x_hat, right)
    assert metadata["candidate_count"] == 2

    empty_selected, empty_meta, empty_issue = probe._candidate_vectors(
        raw, matrix, prior, syndrome, now=now, rss_fn=rss, started=0.0,
        arm_started=0.0, mrb_fn=lambda **kwargs: [], field=field)
    assert empty_issue == ""
    assert empty_selected is raw
    assert empty_meta["rescue_status"] == "empty_candidate_list_raw_retained"
    assert empty_meta["candidate_count"] == 0


def test_syndrome_consistent_wrong_does_not_invoke_rescue():
    field = nonbinary_field.GF2mField.create(32)
    matrix = np.zeros((1, probe.N), dtype=np.int64)
    vector = np.zeros(probe.N, dtype=np.int64)
    syndrome = np.asarray([0], dtype=np.int64)
    prior = np.tile(np.asarray(probe.shape_pmf_grid()[0]["pmf"]),
                    (probe.N, 1))
    raw = _raw(x=vector, syndrome_ok=True, status="converged_exact")
    called = []

    result, metadata, issue = probe._candidate_vectors(
        raw, matrix, prior, syndrome, now=lambda: 1.0, rss_fn=lambda: 1,
        started=0.0, arm_started=0.0,
        mrb_fn=lambda **kwargs: called.append(kwargs), field=field)
    assert issue == ""
    assert result is raw
    assert metadata["raw_syndrome_accept"] is True
    assert metadata["rescue_attempted"] is False
    assert called == []


def test_invalid_or_oversized_mrb_output_stops_and_preserves_raw():
    field = nonbinary_field.GF2mField.create(32)
    matrix = np.zeros((1, probe.N), dtype=np.int64)
    matrix[0, 0] = 1
    syndrome = np.asarray([3], dtype=np.int64)
    prior = np.tile(np.asarray(probe.shape_pmf_grid()[0]["pmf"]),
                    (probe.N, 1))
    raw = _raw()

    invalid = np.zeros(probe.N, dtype=np.int64)  # fails original H*x=s
    result, metadata, issue = probe._candidate_vectors(
        raw, matrix, prior, syndrome, now=lambda: 1.0, rss_fn=lambda: 1,
        started=0.0, arm_started=0.0,
        mrb_fn=lambda **kwargs: [invalid], field=field)
    assert result is raw
    assert issue.startswith("integrity_error:invalid_candidate")
    assert metadata["rescue_status"] == "integrity_error:invalid_candidate"

    many = [np.zeros(probe.N, dtype=np.int64)] * 257
    result, metadata, issue = probe._candidate_vectors(
        raw, matrix, prior, syndrome, now=lambda: 1.0, rss_fn=lambda: 1,
        started=0.0, arm_started=0.0,
        mrb_fn=lambda **kwargs: many, field=field)
    assert result is raw
    assert issue == "integrity_error:candidate_cap_exceeded"
    assert metadata["candidate_count"] == 257


def test_resource_guard_stops_before_mrb_and_samples_after_helper_exception():
    field = nonbinary_field.GF2mField.create(32)
    matrix = np.zeros((1, probe.N), dtype=np.int64)
    matrix[0, 0] = 1
    syndrome = np.asarray([3], dtype=np.int64)
    prior = np.tile(np.asarray(probe.shape_pmf_grid()[0]["pmf"]),
                    (probe.N, 1))
    raw = _raw()
    calls = []
    too_late = probe.CALL_CAP_S + 1.0
    result, metadata, issue = probe._candidate_vectors(
        raw, matrix, prior, syndrome, now=lambda: too_late,
        rss_fn=lambda: 1, started=0.0, arm_started=0.0,
        mrb_fn=lambda **kwargs: calls.append(kwargs), field=field)
    assert result is raw
    assert calls == []
    assert issue.startswith("resource_abort:")
    assert metadata["rescue_status"] == "resource_stop_before_mrb"

    tick = [0.0]
    rss_count = [0]

    def now():
        tick[0] += 0.01
        return tick[0]

    def rss():
        rss_count[0] += 1
        return (probe.RSS_CAP_BYTES + 1) if rss_count[0] >= 3 else 1

    def raise_mrb(**kwargs):
        raise RuntimeError("fake MRB error")

    result, metadata, issue = probe._candidate_vectors(
        raw, matrix, prior, syndrome, now=now, rss_fn=rss,
        started=0.0, arm_started=0.0, mrb_fn=raise_mrb, field=field)
    assert result is raw
    assert "integrity_error:mrb_exception:RuntimeError" in issue
    assert "resource_abort:rss_cap_after_call" in issue
    assert metadata["rescue_status"].startswith("integrity_error:mrb_exception")
    assert rss_count[0] >= 3  # pre-rescue, pre-helper, and post-helper exception


def test_fake_full_batch_is_paired_alternating_and_has_only_four_artifacts(
        tmp_path, monkeypatch):
    relative_root = Path("workspace/mrb-fake")
    monkeypatch.setattr(probe, "OUT_ROOT_RELATIVE", relative_root)
    (tmp_path / "workspace").mkdir()
    h = np.zeros((probe.M, probe.N), dtype=np.int64)
    graph_calls = []
    candidate_calls = []
    decoder_calls = []

    def graph_builder(seed):
        graph_calls.append(seed)
        return {"dense": h.copy()}

    def graph_admit(graph, seed):
        return True, {"graph_seed": int(seed), "admitted": True}

    def candidate_builder(dense, pmf, seed):
        candidate_calls.append(seed)
        return dense.copy(), dense.copy(), {
            "candidate_admitted": True, "deep_candidate_admitted": True,
            "construction_stop": False,
        }

    def fake_decode(matrix, prior, syndrome):
        decoder_calls.append((matrix.copy(), prior.copy(), syndrome.copy()))
        return _raw(x=np.zeros(probe.N, dtype=np.uint8), syndrome_ok=True,
                    status="converged_exact")

    monkeypatch.setattr(probe.search_runner, "graph_preflight", graph_admit)
    monkeypatch.setattr(
        probe.nonbinary_v19_osd, "osd_decode_candidates_mrb",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("raw-syn-pass rescue")))
    tick = [0.0]

    def now():
        tick[0] += 0.001
        return tick[0]

    summary = probe.execute_batch(
        out_root=relative_root, decode_fn=fake_decode,
        graph_builder=graph_builder, candidate_builder=candidate_builder,
        command="fake-only", repo_root=tmp_path, now=now,
        rss_fn=lambda: 100)
    root = tmp_path / relative_root
    assert len(graph_calls) == 6
    assert len(candidate_calls) == 6
    assert len(decoder_calls) == 384
    assert summary["holdout_pairs_completed"] == 192
    assert summary["attempted_decoder_calls"] == 384
    assert summary["batch_uuid"] == probe.BATCH_UUID
    assert summary["contract"] == probe.CONTRACT
    assert summary["seed_namespace"] == probe.SEED_PREFIX
    assert summary["actual_syndrome_disclosure_bits"] == 99840
    assert summary["rescue_attempts"] == summary["rescues_selected"] == 0
    assert summary["classification"] == "CONTROL_RANGE_UNINFORMATIVE"
    assert set(p.name for p in root.iterdir()) == {
        "manifest.json", "frame_records.csv", "summary.json", "EXPLORATION_LOG.md"}
    with (root / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    with (root / "summary.json").open(encoding="utf-8") as stream:
        persisted_summary = json.load(stream)
    for artifact in (summary, persisted_summary, manifest):
        assert artifact["batch_uuid"] == probe.BATCH_UUID
        assert artifact["contract"] == probe.CONTRACT
        assert artifact["seed_namespace"] == probe.SEED_PREFIX
    assert manifest["budgets"]["max_mrb_invocations"] == probe.HOLDOUT_PAIRS
    with (root / "frame_records.csv").open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        assert "top_symbols" not in reader.fieldnames
        rows = list(reader)
    assert len(rows) == 384
    assert [(rows[i]["arm"], rows[i + 1]["arm"]) for i in range(0, 384, 2)] == [
        ("control", "candidate") if int(rows[i]["frame"]) % 2 == 0
        else ("candidate", "control") for i in range(0, 384, 2)]
    assert all(row["rescue_status"] == "not_needed_raw_syndrome_pass"
               for row in rows if row["arm"] == "candidate")
    assert all(row["candidate_count"] == "0" for row in rows
               if row["arm"] == "candidate")
    assert rows[0]["seed"] == str(probe.holdout_seed(
        int(rows[0]["graph_seed"]), int(rows[0]["stream"]), int(rows[0]["frame"])))


def test_fake_exception_is_retained_and_stops_before_next_decoder_call(
        tmp_path, monkeypatch):
    relative_root = Path("workspace/mrb-exception")
    monkeypatch.setattr(probe, "OUT_ROOT_RELATIVE", relative_root)
    (tmp_path / "workspace").mkdir()
    h = np.zeros((probe.M, probe.N), dtype=np.int64)
    monkeypatch.setattr(
        probe.search_runner, "graph_preflight",
        lambda graph, seed: (True, {"graph_seed": int(seed), "admitted": True}))
    graph_builder = lambda seed: {"dense": h.copy()}
    candidate_builder = lambda dense, pmf, seed: (
        dense.copy(), dense.copy(), {"candidate_admitted": True,
                                    "deep_candidate_admitted": True,
                                    "construction_stop": False})
    calls = []

    def broken_decode(*args):
        calls.append(1)
        raise RuntimeError("fake decoder failure")

    tick = [0.0]

    def now():
        tick[0] += 0.001
        return tick[0]

    result = probe.execute_batch(
        out_root=relative_root, decode_fn=broken_decode,
        graph_builder=graph_builder, candidate_builder=candidate_builder,
        command="fake-exception", repo_root=tmp_path, now=now,
        rss_fn=lambda: 100)
    assert len(calls) == 1
    assert result["terminal_status"] == "INTEGRITY_STOP"
    assert result["holdout_complete"] is False
    assert result["control_exact"] is None and result["delta"] is None
    with (tmp_path / relative_root / "frame_records.csv").open(
            encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert rows[0]["status"].startswith("decoder_exception:RuntimeError")
    assert rows[0]["exact"] == "False"


def test_mrb_exception_after_rss_cap_stops_before_next_decoder_call(
        tmp_path, monkeypatch):
    relative_root = Path("workspace/mrb-rss-exception")
    monkeypatch.setattr(probe, "OUT_ROOT_RELATIVE", relative_root)
    (tmp_path / "workspace").mkdir()
    h = np.zeros((probe.M, probe.N), dtype=np.int64)
    h[0, 0] = 1
    monkeypatch.setattr(
        probe.search_runner, "graph_preflight",
        lambda graph, seed: (True, {"graph_seed": int(seed), "admitted": True}))
    monkeypatch.setattr(
        probe.search_runner.d10, "gf32_row_rank", lambda _matrix: probe.M)
    graph_builder = lambda seed: {"dense": h.copy()}
    candidate_builder = lambda dense, pmf, seed: (
        dense.copy(), dense.copy(), {"candidate_admitted": True,
                                    "deep_candidate_admitted": True,
                                    "construction_stop": False})
    monkeypatch.setattr(
        probe.prior_runner.prior_runner, "sample_error",
        lambda _seed, _pmf, width=probe.N: np.zeros(width, dtype=np.int64))
    decoder_calls = []
    mrb_calls = []
    rss = {"bytes": 100}

    def decoder(_matrix, _prior, _syndrome):
        decoder_calls.append(len(decoder_calls) + 1)
        candidate = np.zeros(probe.N, dtype=np.uint8)
        candidate[0] = 1  # raw BP fails on both arms
        return _raw(x=candidate, syndrome_ok=False, status="bp_failed")

    def broken_mrb(**_kwargs):
        mrb_calls.append(1)
        rss["bytes"] = probe.RSS_CAP_BYTES + 1
        raise RuntimeError("fake MRB failure above RSS cap")

    result = probe.execute_batch(
        out_root=relative_root, decode_fn=decoder,
        graph_builder=graph_builder, candidate_builder=candidate_builder,
        mrb_fn=broken_mrb, command="fake-rss-exception", repo_root=tmp_path,
        now=lambda: 0.0, rss_fn=lambda: rss["bytes"])

    assert decoder_calls == [1, 2]
    assert mrb_calls == [1]
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert result["resource_violations"] == 1
    assert result["holdout_pairs_completed"] == 0
    assert result["control_exact"] is result["candidate_exact"] is None
    assert "rss_cap_after_call" in result["stop_reason"]
    with (tmp_path / relative_root / "frame_records.csv").open(
            encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2
    assert rows[0]["arm"] == "control"
    assert rows[0]["rescue_status"] == "not_candidate_arm"
    candidate_row = rows[1]
    assert candidate_row["arm"] == "candidate"
    assert "integrity_error:mrb_exception:RuntimeError" in candidate_row["status"]
    assert "resource_abort:rss_cap_after_call" in candidate_row["status"]

