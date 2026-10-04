from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from comparison_bench.cli import nbldpc_gf32_mrb_reaggregate as reagg
from comparison_bench.cli import nbldpc_gf32_mrb_rescue_probe as mrb


def _fixture_source(tmp_path: Path, *, omit_last: bool = False) -> Path:
    source = tmp_path / "retained-mrb"
    source.mkdir()
    seeds = [int(seed) for seed in mrb.GRAPH_SEEDS]
    manifest = {
        "track": "EXPLORE", "status": "NO_SUFFICIENT_SIGNAL",
        "batch_uuid": mrb.BATCH_UUID, "contract": mrb.CONTRACT,
        "seed_namespace": mrb.SEED_PREFIX,
        "pilot": "NOT_RUN_FIXED_PMF", "fixed_p0": 0.55,
        "graph_profile": {"n": 128, "m": 52, "E": 256,
                          "field": "GF(32)/polynomial-37",
                          "graph_seeds": seeds},
        "decoder": {"implementation": "v35.decode_row_layered_fftqspa",
                    "max_iter": 90, "damping_alpha": 1.0,
                    "same_bp_decoder_both_arms": True,
                    "candidate_postprocessor": "MRB order1 cap256"},
        "rescue_contract": {"candidate_cap": 256},
        "graph_diagnostics": [
            {"graph_seed": seed, "admitted": True} for seed in seeds],
        "candidate_diagnostics": [
            {"graph_seed": seed, "candidate_admitted": True,
             "deep_candidate_admitted": True, "construction_stop": False}
            for seed in seeds],
        "attempted_decoder_calls": 384,
        "attempted_frame_rows": 384,
        "resource_measurement": {
            "batch_wall_s": 40.0, "max_call_wall_s": 0.1,
            "max_rss_bytes": 1000, "rss_sample_count": 500,
            "rss_scope": "fake process RSS samples",
        },
    }
    (source / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    # The historical summary's identity is deliberately bad. The reducer must
    # derive from manifest + CSV and retain this file without trusting it.
    (source / "summary.json").write_text(json.dumps({
        "batch_uuid": "a3444f81-f091-4ffd-9c16-393c6062f6e3",
        "contract": "NBLDPC-GF32-DAMPING-20261001/PREREG_AND_AUTH.md",
        "seed_namespace": "gf32-damping-v1",
    }), encoding="utf-8")
    (source / "EXPLORATION_LOG.md").write_text("retained fake source\n", encoding="utf-8")

    rows = []
    for graph_seed, stream, frame, seed in mrb.seed_plan():
        for arm in mrb.arm_order(frame):
            success = frame % 2 == 0
            wrong = False
            syn = success
            raw_syn = success
            rescue = False
            rescue_status = "not_candidate_arm" if arm == "control" else "not_needed_raw_syndrome_pass"
            candidate_count = 0
            rescue_wall = 0.0
            selected_score = None
            if arm == "control" and (graph_seed, stream, frame) == (
                    seeds[0], 0, 1):
                syn, raw_syn, wrong = True, True, True
            if arm == "candidate" and frame % 2 == 1:
                raw_syn = False
                rescue = True
                rescue_status = "empty_candidate_list_raw_retained"
                rescue_wall = 0.02
                if (graph_seed, stream, frame) == (seeds[0], 0, 1):
                    syn, wrong = True, True
                    rescue_status = "rescued"
                    candidate_count = 2
                    selected_score = -3.25
            rows.append({
                "call_index": len(rows) + 1, "phase": "holdout",
                "graph_seed": graph_seed, "stream": stream, "frame": frame,
                "seed": seed, "arm": arm,
                "exact": success, "syndrome_accept": syn,
                "syndrome_consistent_wrong": wrong,
                "status": "mrb_rescued_order1" if rescue_status == "rescued" else "converged",
                "iterations": 4, "wall_s": 0.1, "rss_b": 200,
                "raw_syndrome_accept": raw_syn,
                "rescue_attempted": rescue,
                "rescue_status": rescue_status,
                "candidate_count": candidate_count,
                "selected_prior_score": selected_score,
                "rescue_wall_s": rescue_wall,
                "bp_runtime_s": 0.08,
                "damping_alpha": 1.0, "max_iter": 90,
            })
    if omit_last:
        rows.pop()
    with (source / "frame_records.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=mrb.FRAME_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return source


def _run(tmp_path: Path, monkeypatch, source: Path):
    relative_root = Path("workspace") / "reaggregate-fake"
    monkeypatch.setattr(reagg, "OUT_ROOT_RELATIVE", relative_root)
    (tmp_path / "workspace").mkdir(exist_ok=True)
    ticks = [0.0]

    def now():
        ticks[0] += 0.01
        return ticks[0]

    return reagg.execute_reaggregation(
        out_root=relative_root, source_root=source, repo_root=tmp_path,
        now=now, rss_fn=lambda: 100)


def test_fake_reaggregation_recomputes_wrong_and_pair_totals_without_using_bad_summary(
        tmp_path, monkeypatch):
    source = _fixture_source(tmp_path)
    before = {path.name: path.read_bytes() for path in source.iterdir()}
    summary = _run(tmp_path, monkeypatch, source)
    root = tmp_path / "workspace" / "reaggregate-fake"

    assert set(path.name for path in root.iterdir()) == set(reagg.OUTPUT_FILES)
    assert summary["batch_uuid"] == mrb.BATCH_UUID
    assert summary["contract"] == mrb.CONTRACT
    assert summary["seed_namespace"] == mrb.SEED_PREFIX
    assert summary["reaggregation_uuid"] == reagg.REAGGREGATION_UUID
    assert summary["terminal_status"] == "REAGGREGATION_COMPLETE"
    assert summary["holdout_pairs_completed"] == 192
    assert summary["attempted_decoder_calls"] == 384
    assert summary["control_exact"] == summary["candidate_exact"] == 96
    assert summary["delta"] == 0
    assert summary["paired_states"] == {
        "control_only": 0, "candidate_only": 0, "both": 96, "neither": 96}
    assert summary["syndrome_consistent_wrong_by_arm"] == {
        "control": 1, "candidate": 1}
    assert summary["syndrome_consistent_wrong_rows"] == 2
    assert summary["rescue_attempts"] == 96
    assert summary["rescues_selected"] == 1
    assert summary["candidate_vectors_examined"] == 2
    assert summary["actual_syndrome_disclosure_bits"] == 99840
    assert summary["classification"] == "NO_SUFFICIENT_SIGNAL"
    assert summary["source_artifact_provenance"]["source_summary_used_for_aggregate"] is False
    assert summary["source_science_cost_inherited"]["batch_wall_s"] == 40.0
    with (root / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    with (root / "summary.json").open(encoding="utf-8") as stream:
        disk_summary = json.load(stream)
    assert manifest["source_batch_uuid"] == mrb.BATCH_UUID
    assert manifest["reaggregation_uuid"] == reagg.REAGGREGATION_UUID
    assert manifest["scientific_calls"] == manifest["decoder_calls"] == 0
    assert disk_summary == summary
    assert {path.name: path.read_bytes() for path in source.iterdir()} == before


def test_incomplete_source_keeps_performance_totals_unknown(tmp_path, monkeypatch):
    source = _fixture_source(tmp_path, omit_last=True)
    summary = _run(tmp_path, monkeypatch, source)

    assert summary["terminal_status"] == "SOURCE_INCOMPLETE"
    assert summary["holdout_complete"] is False
    assert summary["attempted_frame_rows"] == 383
    assert summary["holdout_pairs_completed"] == 191
    assert summary["control_exact"] is None
    assert summary["candidate_exact"] is None
    assert summary["delta"] is None
    assert summary["paired_states"] is None
    assert summary["syndrome_consistent_wrong_rows"] is None


def test_bad_source_identity_stops_and_missing_source_is_retained(tmp_path, monkeypatch):
    source = _fixture_source(tmp_path)
    manifest_path = source / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["batch_uuid"] = "wrong-source"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    summary = _run(tmp_path, monkeypatch, source)
    assert summary["terminal_status"] == "SOURCE_STOP"
    assert summary["control_exact"] is None
    assert "source manifest MRB identity" in summary["stop_reason"]


def test_batch_wall_below_retained_call_wall_sum_stops(tmp_path, monkeypatch):
    source = _fixture_source(tmp_path)
    manifest_path = source / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["resource_measurement"]["batch_wall_s"] = 20.0
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    summary = _run(tmp_path, monkeypatch, source)
    assert summary["terminal_status"] == "SOURCE_STOP"
    assert summary["control_exact"] is None
    assert summary["delta"] is None
    assert "batch wall cost is below summed retained call wall" in summary["stop_reason"]


def test_missing_source_writes_only_a_stop_record_with_unknown_totals(tmp_path, monkeypatch):
    source = tmp_path / "missing-source"
    summary = _run(tmp_path, monkeypatch, source)
    root = tmp_path / "workspace" / "reaggregate-fake"
    assert summary["terminal_status"] == "SOURCE_STOP"
    assert summary["control_exact"] is None
    assert summary["candidate_exact"] is None
    assert summary["delta"] is None
    assert set(path.name for path in root.iterdir()) == set(reagg.OUTPUT_FILES)
    assert "missing_source_artifacts" in summary["stop_reason"]


def test_resource_cap_after_source_read_stops_with_unknown_totals(tmp_path, monkeypatch):
    source = _fixture_source(tmp_path)
    relative_root = Path("workspace") / "reaggregate-rss-fake"
    monkeypatch.setattr(reagg, "OUT_ROOT_RELATIVE", relative_root)
    (tmp_path / "workspace").mkdir(exist_ok=True)
    rss_calls = [0]

    def rss():
        rss_calls[0] += 1
        return 100 if rss_calls[0] == 1 else reagg.MAX_RSS_BYTES

    summary = reagg.execute_reaggregation(
        out_root=relative_root, source_root=source, repo_root=tmp_path,
        now=lambda: 1.0, rss_fn=rss)
    assert summary["terminal_status"] == "RESOURCE_STOP"
    assert summary["control_exact"] is None
    assert summary["delta"] is None
    assert "reader_rss_cap" in summary["stop_reason"]


def test_existing_reaggregation_root_is_refused(tmp_path, monkeypatch):
    relative_root = Path("workspace") / "existing-reaggregate"
    monkeypatch.setattr(reagg, "OUT_ROOT_RELATIVE", relative_root)
    root = tmp_path / relative_root
    root.mkdir(parents=True)
    marker = root / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError):
        reagg.execute_reaggregation(out_root=relative_root, repo_root=tmp_path,
                                    source_root=tmp_path / "missing")
    assert marker.read_text(encoding="utf-8") == "keep"
