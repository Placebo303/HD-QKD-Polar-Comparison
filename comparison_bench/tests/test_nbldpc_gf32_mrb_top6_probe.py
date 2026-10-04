from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path

import pytest
import numpy as np

from comparison_bench.cli import nbldpc_gf32_mrb_top6_probe as probe
from comparison_bench.formal_ir import nonbinary_field
from comparison_bench.formal_ir import nonbinary_v19_osd


@dataclass(frozen=True)
class _DecodeResult:
    x_hat: np.ndarray
    syndrome_ok: bool
    iterations: int
    runtime_s: float
    status: str
    final_beliefs: np.ndarray


def _decode_result(vector, syndrome_ok, status):
    return _DecodeResult(
        np.asarray(vector, dtype=np.uint8), bool(syndrome_ok), 4, 0.01,
        status, np.zeros((probe.N, 32), dtype=np.float64))


def _syndrome(field, matrix, vector):
    out = []
    for row in matrix:
        total = 0
        for coefficient, symbol in zip(row, vector):
            total = field.add(total, field.mul(int(coefficient), int(symbol)))
        out.append(total)
    return np.asarray(out, dtype=np.int64)


def _free_variable_case(hard_symbol: int, scores: np.ndarray):
    field = nonbinary_field.GF2mField.create(32)
    matrix = np.asarray([[1, 1]], dtype=np.int64)
    hard = np.asarray([hard_symbol, hard_symbol], dtype=np.int64)
    beliefs = np.tile(np.asarray(scores, dtype=np.float64), (2, 1))
    syndrome = _syndrome(field, matrix, hard)
    candidates = nonbinary_v19_osd.osd_decode_candidates_mrb(
        field=field, matrix=matrix, syndrome=syndrome, beliefs=beliefs,
        e_hat=hard, order=1, top_info=None, top_symbols=6,
        max_candidates=probe.MAX_CANDIDATES)
    return field, matrix, syndrome, hard, beliefs, candidates


def test_actual_top6_helper_keeps_hard_and_adds_five_when_hard_is_in_top6():
    scores = np.arange(32, dtype=np.float64)[::-1]
    field, matrix, syndrome, hard, beliefs, candidates = _free_variable_case(0, scores)
    top = set(np.argsort(beliefs[1])[::-1][:6].tolist())
    expected = sorted(top | {int(hard[1])})

    assert 0 in top
    assert len(expected) == 6  # hard is not an extra alternative
    assert {int(row[1]) for row in candidates} == set(expected)
    assert len(candidates) == 6
    assert len({tuple(row) for row in candidates}) == 6
    assert all(np.array_equal(_syndrome(field, matrix, row), syndrome)
               for row in candidates)


def test_actual_top6_helper_adds_hard_and_keeps_six_alternatives_when_outside():
    scores = np.arange(32, dtype=np.float64)[::-1]
    field, matrix, syndrome, hard, beliefs, candidates = _free_variable_case(31, scores)
    top = set(np.argsort(beliefs[1])[::-1][:6].tolist())
    expected = sorted(top | {int(hard[1])})

    assert 31 not in top
    assert len(expected) == 7  # base/hard plus six belief-ranked alternatives
    assert {int(row[1]) for row in candidates} == set(expected)
    assert len(candidates) == 7
    assert all(np.array_equal(_syndrome(field, matrix, row), syndrome)
               for row in candidates)


def test_top6_tied_membership_matches_the_actual_helper_without_stable_tie_claim():
    scores = np.ones(32, dtype=np.float64)
    field, matrix, syndrome, hard, beliefs, candidates = _free_variable_case(0, scores)
    top_as_implemented = set(np.argsort(beliefs[1])[::-1][:6].tolist())
    expected = top_as_implemented | {int(hard[1])}

    assert {int(row[1]) for row in candidates} == expected
    assert all(np.array_equal(_syndrome(field, matrix, row), syndrome)
               for row in candidates)


def test_mrb_arm_adapters_change_only_top_symbols_keyword():
    field = nonbinary_field.GF2mField.create(32)
    matrix = np.asarray([[1]], dtype=np.int64)
    syndrome = np.asarray([1], dtype=np.int64)
    beliefs = np.zeros((1, 32), dtype=np.float64)
    hard = np.asarray([0], dtype=np.int64)
    calls = []

    def spy(**kwargs):
        calls.append({key: value.copy() if isinstance(value, np.ndarray) else value
                      for key, value in kwargs.items()})
        return [np.asarray([1], dtype=np.int64)]

    common = {
        "field": field, "matrix": matrix, "syndrome": syndrome,
        "beliefs": beliefs, "e_hat": hard, "order": 1,
        "top_info": None, "top_symbols": None, "max_candidates": 256,
    }
    control = probe.mrb_adapter_for_arm("control", spy)
    candidate = probe.mrb_adapter_for_arm("candidate", spy)
    control(**common)
    candidate(**common)

    assert calls[0]["top_symbols"] is None
    assert calls[1]["top_symbols"] == 6
    assert set(calls[0]) == set(calls[1])
    differing = []
    for key in set(common) - {"top_symbols"}:
        left, right = calls[0][key], calls[1][key]
        same = np.array_equal(left, right) if isinstance(left, np.ndarray) else left == right
        if not same:
            differing.append(key)
    assert differing == []


def test_explicit_arm_callbacks_and_batch_context_are_distinct_without_global_mutation():
    calls = []

    def spy(**kwargs):
        calls.append(dict(kwargs))
        return []

    by_arm = probe.mrb_fns_by_arm(spy)
    common = {
        "field": object(), "matrix": np.asarray([[1]], dtype=np.int64),
        "syndrome": np.asarray([0], dtype=np.int64),
        "beliefs": np.zeros((1, 32)), "e_hat": np.asarray([0]),
        "order": 1, "top_info": None, "top_symbols": None,
        "max_candidates": 256,
    }
    by_arm["control"](**common)
    by_arm["candidate"](**common)

    assert calls[0]["top_symbols"] is None
    assert calls[1]["top_symbols"] == 6
    assert set(calls[0]) == set(calls[1])
    for key in set(calls[0]) - {"top_symbols"}:
        left, right = calls[0][key], calls[1][key]
        assert np.array_equal(left, right) if isinstance(left, np.ndarray) else left is right or left == right

    context = probe.BATCH_CONTEXT
    assert context["batch_uuid"] == "df44e589-370d-4818-b652-2e2cc67de758"
    assert context["contract"] == probe.CONTRACT
    assert context["out_root_relative"] == "workspace/gf32_mrb_top6_df44e589"
    assert context["seed_namespace"] == probe.SEED_PREFIX
    assert context["source_batch_uuid"] == probe.SOURCE_BATCH_UUID
    assert context["reaggregation_uuid"] == probe.REAGGREGATION_UUID
    assert context["arm_metadata"] == {
        "control": {"top_symbols": None},
        "candidate": {"top_symbols": 6},
    }


def test_top6_t0_uses_fresh_disjoint_seed_namespace_and_frozen_root(tmp_path, monkeypatch):
    forbidden = AssertionError("dry-run called an execution helper")
    monkeypatch.setattr(probe.mrb, "_candidate_vectors", lambda *a, **k: (_ for _ in ()).throw(forbidden))
    monkeypatch.setattr(probe.mrb.search_runner, "build_profile_graph", lambda *a, **k: (_ for _ in ()).throw(forbidden))
    rows = probe._validate_seed_plan()
    seeds = [row[3] for row in rows]

    assert len(rows) == probe.HOLDOUT_PAIRS == 192
    assert len(set(seeds)) == len(seeds)
    assert rows == probe.seed_plan()
    assert not any(set(seeds) & old for old in probe.mrb._prior_seed_sets())
    assert probe.holdout_seed(*rows[0][:3]) != probe.mrb.holdout_seed(*rows[0][:3])

    root = tmp_path / probe.OUT_ROOT_RELATIVE
    result = probe.dry_run(probe.OUT_ROOT_RELATIVE, repo_root=tmp_path)
    assert result["status"] == "DRY_RUN"
    assert result["batch_uuid"] == probe.BATCH_UUID
    assert result["seed_namespace"] == probe.SEED_PREFIX
    assert result["writes"] == result["empirical_input_reads"] == result["artifact_reads"] == 0
    assert result["graph_construction_calls"] == result["decoder_calls"] == result["mrb_calls"] == 0
    assert result["holdout_pair_count"] == 192 and result["holdout_call_count"] == 384
    assert not root.exists()

    with pytest.raises(ValueError, match="frozen fresh root"):
        probe.validate_out_root("workspace/some-other-root", repo_root=tmp_path)
    root.mkdir(parents=True)
    with pytest.raises(FileExistsError, match="refusing existing output root"):
        probe.validate_out_root(probe.OUT_ROOT_RELATIVE, repo_root=tmp_path)


def test_real_top6_summary_keeps_partial_unknowns_and_counts_both_arm_rescues():
    rows = [
        {
            "phase": "holdout", "arm": "control", "graph_seed": probe.GRAPH_SEEDS[0],
            "exact": False, "syndrome_accept": True,
            "syndrome_consistent_wrong": True, "status": "mrb_rescued",
            "iterations": 2, "wall_s": 0.8, "rescue_attempted": True,
            "rescue_status": "rescued", "candidate_count": 5,
            "selected_prior_score": -3.0, "rescue_wall_s": 0.4,
            "mrb_helper_wall_s": 0.2,
        },
        {
            "phase": "holdout", "arm": "candidate", "graph_seed": probe.GRAPH_SEEDS[0],
            "exact": True, "syndrome_accept": True,
            "syndrome_consistent_wrong": False, "status": "mrb_rescued",
            "iterations": 3, "wall_s": 0.9, "rescue_attempted": True,
            "rescue_status": "rescued", "candidate_count": 7,
            "selected_prior_score": -2.0, "rescue_wall_s": 0.5,
            "mrb_helper_wall_s": 0.25,
        },
    ]

    # This is the actual summary callback used by the new runner, not a test
    # stub for identity production. No full performance denominator exists.
    summary = probe.summarize_top6(rows, [], "fake_partial")

    assert summary["batch_uuid"] == probe.BATCH_UUID
    assert "top_symbols argument (None versus 6)" in summary["claim_ceiling"]
    assert "versus raw BP" not in summary["claim_ceiling"]
    assert summary["contract"] == probe.CONTRACT
    assert summary["seed_namespace"] == probe.SEED_PREFIX
    assert summary["out_root_relative"] == str(probe.OUT_ROOT_RELATIVE)
    assert summary["source_batch_uuid"] == probe.SOURCE_BATCH_UUID
    assert summary["reaggregation_uuid"] == probe.REAGGREGATION_UUID
    assert summary["top_symbols_by_arm"] == {"control": None, "candidate": 6}
    assert summary["holdout_complete"] is False
    assert summary["control_exact"] is None
    assert summary["candidate_exact"] is None
    assert summary["delta"] is None
    assert summary["paired_states"] is None
    assert summary["rescue_metrics_by_arm"]["control"] == {
        "rescue_attempts": 1, "rescues_selected": 1,
        "candidate_vectors_examined": 5, "empty_candidate_lists": 0,
        "selected_prior_score_count": 1, "selected_prior_score_min": -3.0,
        "selected_prior_score_max": -3.0, "selected_prior_scores": [-3.0],
        "mrb_helper_wall_s_total": 0.2, "rescue_wall_s_total": 0.4,
    }
    assert summary["rescue_metrics_by_arm"]["candidate"]["rescue_attempts"] == 1
    assert summary["rescue_metrics_by_arm"]["candidate"]["candidate_vectors_examined"] == 7


def test_top6_execute_fake_batch_reuses_pairing_and_persists_identity_and_arm_costs(
        tmp_path, monkeypatch):
    (tmp_path / "workspace").mkdir()
    h = np.zeros((probe.M, probe.N), dtype=np.int64)
    h[0, 0] = 1
    truth = np.zeros(probe.N, dtype=np.int64)
    graph_calls = []
    candidate_calls = []
    bp_calls = []
    mrb_calls = []

    def graph_builder(seed):
        graph_calls.append(seed)
        return {"dense": h.copy()}

    def graph_preflight(graph, seed):
        return True, {"graph_seed": int(seed), "admitted": True}

    def candidate_builder(dense, pmf, seed):
        candidate_calls.append(int(seed))
        return dense.copy(), dense.copy(), {
            "candidate_admitted": True, "deep_candidate_admitted": True,
            "construction_stop": False,
        }

    def sample_error(seed, pmf, width=probe.N):
        assert width == probe.N
        return truth.copy()

    def fake_decode(matrix, prior, syndrome):
        bp_calls.append((matrix.copy(), prior.copy(), syndrome.copy()))
        wrong = truth.copy()
        wrong[0] = 1  # fails original H*x=s, so both arms enter their MRB callback
        return _decode_result(wrong, False, "fake_bp_syndrome_fail")

    def fake_mrb(**kwargs):
        mrb_calls.append({
            key: value.copy() if isinstance(value, np.ndarray) else value
            for key, value in kwargs.items()})
        assert "truth" not in kwargs and "exact" not in kwargs
        return [truth.copy()]

    monkeypatch.setattr(probe.mrb.search_runner, "graph_preflight", graph_preflight)
    monkeypatch.setattr(probe.mrb.prior_runner.prior_runner, "sample_error", sample_error)
    tick = [0.0]

    def now():
        tick[0] += 0.001
        return tick[0]

    summary = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE, decode_fn=fake_decode,
        graph_builder=graph_builder, candidate_builder=candidate_builder,
        mrb_fn=fake_mrb, command="fake-top6-only", repo_root=tmp_path,
        now=now, rss_fn=lambda: 100)
    root = tmp_path / probe.OUT_ROOT_RELATIVE

    assert len(graph_calls) == len(candidate_calls) == 6
    assert len(bp_calls) == 384
    assert len(mrb_calls) == 384  # both arms, bounded at 192 each
    assert summary["holdout_pairs_completed"] == 192
    assert summary["attempted_decoder_calls"] == 384
    assert summary["classification"] == "CONTROL_RANGE_UNINFORMATIVE"
    assert summary["control_exact"] == summary["candidate_exact"] == 192
    assert summary["delta"] == 0
    assert summary["actual_syndrome_disclosure_bits"] == 99840
    assert summary["resource_measurement"]["max_call_wall_s"] is not None
    assert summary["rescue_attempts"] == summary["rescues_selected"] == 384
    assert summary["candidate_vectors_examined"] == 384
    assert summary["rescue_metrics_by_arm"]["control"]["rescue_attempts"] == 192
    assert summary["rescue_metrics_by_arm"]["candidate"]["rescue_attempts"] == 192
    assert summary["rescue_wall_s_total"] >= summary["mrb_helper_wall_s_total"]
    assert set(p.name for p in root.iterdir()) == {
        "manifest.json", "frame_records.csv", "summary.json", "EXPLORATION_LOG.md"}

    with (root / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    with (root / "summary.json").open(encoding="utf-8") as stream:
        persisted = json.load(stream)
    with (root / "frame_records.csv").open(encoding="utf-8", newline="") as stream:
        records = list(csv.DictReader(stream))
    log = (root / "EXPLORATION_LOG.md").read_text(encoding="utf-8")

    for artifact in (summary, persisted, manifest):
        assert artifact["batch_uuid"] == probe.BATCH_UUID
        assert artifact["contract"] == probe.CONTRACT
        assert artifact["seed_namespace"] == probe.SEED_PREFIX
    assert persisted["rescue_metrics_by_arm"] == summary["rescue_metrics_by_arm"]
    assert manifest["rescue_metrics_by_arm"] == summary["rescue_metrics_by_arm"]
    assert manifest["source_batch_uuid"] == probe.SOURCE_BATCH_UUID
    assert manifest["reaggregation_uuid"] == probe.REAGGREGATION_UUID
    assert manifest["budgets"]["max_mrb_invocations"] == 384
    assert manifest["top_symbols_by_arm"] == {"control": None, "candidate": 6}
    assert len(records) == 384 and "top_symbols" in records[0]
    assert records[0]["top_symbols"] in ("", "6")
    assert log.count("top_symbols=None") >= 1
    assert log.count("top_symbols=6") >= 1
    assert probe.BATCH_UUID in log and probe.CONTRACT in log
    assert probe.SEED_PREFIX in log and probe.REAGGREGATION_UUID in log
    for index in range(0, 384, 2):
        first, second = records[index:index + 2]
        assert first["graph_seed"] == second["graph_seed"]
        assert first["stream"] == second["stream"]
        assert first["frame"] == second["frame"]
        assert first["seed"] == second["seed"]
        assert (first["arm"], second["arm"]) == (
            ("control", "candidate") if int(first["frame"]) % 2 == 0
            else ("candidate", "control"))
        assert first["top_symbols"] != second["top_symbols"]
        left, right = bp_calls[index:index + 2]
        assert np.array_equal(left[0], right[0])
        assert np.array_equal(left[1], right[1])
        assert np.array_equal(left[2], right[2])
        assert np.array_equal(mrb_calls[index]["matrix"], mrb_calls[index + 1]["matrix"])
        assert np.array_equal(mrb_calls[index]["syndrome"], mrb_calls[index + 1]["syndrome"])
        assert mrb_calls[index]["top_symbols"] in (None, 6)
        assert mrb_calls[index + 1]["top_symbols"] in (None, 6)
        assert mrb_calls[index]["top_symbols"] != mrb_calls[index + 1]["top_symbols"]


def test_top6_rescue_wall_includes_candidate_scoring_and_selection(monkeypatch):
    field = nonbinary_field.GF2mField.create(32)
    h = np.zeros((1, probe.N), dtype=np.int64)
    h[0, 0] = 1
    syndrome = np.asarray([3], dtype=np.int64)
    prior = np.tile(np.asarray(probe.mrb.shape_pmf_grid()[0]["pmf"]),
                    (probe.N, 1))
    raw = _decode_result(np.zeros(probe.N), False, "fake_bp_failed")
    candidate = np.zeros(probe.N, dtype=np.int64)
    candidate[0] = 3
    clock = {"now": 0.0}
    seen = []
    real_fsum = math.fsum

    def slow_fsum(values):
        clock["now"] += 3.0
        return real_fsum(values)

    def fake_mrb(**kwargs):
        seen.append(kwargs)
        clock["now"] += 1.0
        return [candidate.copy()]

    monkeypatch.setattr(probe.mrb.math, "fsum", slow_fsum)
    selected, metadata, issue = probe.mrb._candidate_vectors(
        raw, h, prior, syndrome, now=lambda: clock["now"], rss_fn=lambda: 100,
        started=0.0, arm_started=0.0,
        mrb_fn=probe.mrb_adapter_for_arm("candidate", fake_mrb), field=field)

    assert issue == ""
    assert np.array_equal(selected.x_hat, candidate)
    assert selected is not raw
    assert seen[0]["top_symbols"] == 6
    assert seen[0]["order"] == 1 and seen[0]["top_info"] is None
    assert np.array_equal(seen[0]["syndrome"], syndrome)
    assert metadata["mrb_helper_wall_s"] == 1.0
    assert metadata["rescue_wall_s"] == 4.0
    assert metadata["rescue_wall_s"] > metadata["mrb_helper_wall_s"]


def test_top6_partial_orphan_keeps_raw_valid_wrong_and_nulls_performance(
        tmp_path, monkeypatch):
    (tmp_path / "workspace").mkdir()
    h = np.zeros((probe.M, probe.N), dtype=np.int64)
    h[0, 0] = 1
    monkeypatch.setattr(
        probe.mrb.search_runner, "graph_preflight",
        lambda _graph, seed: (True, {"graph_seed": int(seed), "admitted": True}))
    monkeypatch.setattr(
        probe.mrb.prior_runner.prior_runner, "sample_error",
        lambda _seed, _pmf, width=probe.N: np.zeros(width, dtype=np.int64))
    candidate_builder = lambda dense, _pmf, _seed: (
        dense.copy(), dense.copy(), {"candidate_admitted": True,
                                    "deep_candidate_admitted": True,
                                    "construction_stop": False})
    decode_calls = []
    mrb_calls = []

    def decode(_matrix, _prior, _syndrome):
        decode_calls.append(1)
        if len(decode_calls) == 3:
            raise RuntimeError("fake orphan stop")
        wrong = np.zeros(probe.N, dtype=np.uint8)
        wrong[1] = 1  # H*x remains zero, but the sample truth is all-zero
        return _decode_result(wrong, True, "fake_valid_wrong")

    def should_not_mrb(**kwargs):
        mrb_calls.append(kwargs)
        raise AssertionError("syndrome-valid wrong raw BP must pass through")

    tick = [0.0]

    def now():
        tick[0] += 0.001
        return tick[0]

    summary = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE, decode_fn=decode,
        graph_builder=lambda seed: {"dense": h.copy()},
        candidate_builder=candidate_builder, mrb_fn=should_not_mrb,
        command="fake-orphan", repo_root=tmp_path, now=now, rss_fn=lambda: 100)
    root = tmp_path / probe.OUT_ROOT_RELATIVE

    assert len(decode_calls) == 3 and mrb_calls == []
    assert summary["terminal_status"] == "INTEGRITY_STOP"
    assert summary["holdout_pairs_completed"] == 1
    assert summary["holdout_complete"] is False
    assert summary["control_exact"] is summary["candidate_exact"] is None
    assert summary["delta"] is None and summary["paired_states"] is None
    assert summary["syndrome_consistent_wrong_rows"] == 2
    assert summary["rescue_metrics_by_arm"]["control"]["rescue_attempts"] == 0
    assert summary["rescue_metrics_by_arm"]["candidate"]["rescue_attempts"] == 0
    per_graph = summary["delta_by_graph"][str(probe.GRAPH_SEEDS[0])]
    assert per_graph["control_exact"] is None and per_graph["delta_g"] is None
    with (root / "frame_records.csv").open(encoding="utf-8", newline="") as stream:
        records = list(csv.DictReader(stream))
    assert len(records) == 3
    assert records[0]["syndrome_consistent_wrong"] == "True"
    assert records[0]["exact"] == "False" and records[0]["syndrome_accept"] == "True"
    assert records[2]["status"].startswith("decoder_exception:RuntimeError")


@pytest.mark.parametrize("cap", ["call", "total", "rss"])
def test_top6_mrb_exception_after_each_resource_cap_retains_row_and_stops(
        tmp_path, monkeypatch, cap):
    (tmp_path / "workspace").mkdir()
    h = np.zeros((probe.M, probe.N), dtype=np.int64)
    h[0, 0] = 1
    monkeypatch.setattr(
        probe.mrb.search_runner, "graph_preflight",
        lambda _graph, seed: (True, {"graph_seed": int(seed), "admitted": True}))
    monkeypatch.setattr(
        probe.mrb.prior_runner.prior_runner, "sample_error",
        lambda _seed, _pmf, width=probe.N: np.zeros(width, dtype=np.int64))
    clock = {"now": 0.0}
    rss = {"bytes": 100}

    def candidate_builder(dense, _pmf, seed):
        if cap == "total" and int(seed) == int(probe.GRAPH_SEEDS[-1]):
            clock["now"] = probe.WALL_CAP_S - 10.0
        return dense.copy(), dense.copy(), {
            "candidate_admitted": True, "deep_candidate_admitted": True,
            "construction_stop": False,
        }

    decode_calls = []
    mrb_calls = []

    def decode(_matrix, _prior, _syndrome):
        decode_calls.append(1)
        raw = np.zeros(probe.N, dtype=np.uint8)
        raw[0] = 1  # fails the original syndrome and triggers MRB on frame 0 control
        return _decode_result(raw, False, "fake_bp_failed")

    def broken_mrb(**kwargs):
        mrb_calls.append(kwargs)
        if cap == "call":
            clock["now"] += probe.CALL_CAP_S + 1.0
        elif cap == "total":
            clock["now"] += 20.0  # <120 s per arm, while total becomes >1800 s
        else:
            rss["bytes"] = probe.RSS_CAP_BYTES + 1
        raise RuntimeError("fake MRB exception at resource cap")

    result = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE, decode_fn=decode,
        graph_builder=lambda seed: {"dense": h.copy()},
        candidate_builder=candidate_builder, mrb_fn=broken_mrb,
        command="fake-resource-stop", repo_root=tmp_path,
        now=lambda: clock["now"], rss_fn=lambda: rss["bytes"])
    root = tmp_path / probe.OUT_ROOT_RELATIVE

    assert len(decode_calls) == len(mrb_calls) == 1
    assert mrb_calls[0]["top_symbols"] is None  # frame 0 starts with control
    assert result["terminal_status"] == "RESOURCE_STOP"
    assert result["resource_violations"] == 1
    assert result["holdout_pairs_completed"] == 0
    assert result["holdout_complete"] is False
    assert result["control_exact"] is result["candidate_exact"] is None
    assert result["delta"] is None and result["paired_states"] is None
    with (root / "frame_records.csv").open(encoding="utf-8", newline="") as stream:
        records = list(csv.DictReader(stream))
    assert len(records) == 1
    row = records[0]
    assert "integrity_error:mrb_exception:RuntimeError" in row["status"]
    assert "resource_abort:" in row["status"]
    assert "resource_abort:" in result["stop_reason"]
    assert result["resource_measurement"]["max_call_wall_s"] is not None
    if cap == "call":
        assert "decoder_call_wall_cap_after_return" in result["stop_reason"]
        assert result["resource_measurement"]["max_call_wall_s"] >= probe.CALL_CAP_S
    elif cap == "total":
        assert "total_wall_cap_after_call" in result["stop_reason"]
        assert result["resource_measurement"]["max_call_wall_s"] < probe.CALL_CAP_S
        assert result["resource_measurement"]["batch_wall_s"] >= probe.WALL_CAP_S
    else:
        assert "rss_cap_after_call" in result["stop_reason"]
