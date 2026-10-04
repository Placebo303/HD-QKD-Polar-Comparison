"""Focused fake-only tests for the fresh GF(32) soft-prior replica."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from comparison_bench.cli.probes_closed import nbldpc_gf32_softprior_replica as replica
from comparison_bench.cli.probes_closed import nbldpc_gf32_softprior_rescue as rescue
from comparison_bench.formal_ir import nonbinary_v10_common as common
from .test_nbldpc_gf32_softprior_rescue import _fake_batch_adapters


def _assert_no_operations(result: dict) -> None:
    assert result["source_reads"] == 0
    assert result["sampler_calls"] == 0
    assert result["decoder_calls"] == 0
    assert result["writes"] == 0


def test_replica_seed_identity_exclusions_and_source_free_dry_run(tmp_path: Path):
    # The predecessor defaults must remain exactly on their original identity.
    old_plan = rescue.build_seed_plan()
    old_t0 = rescue.verify_t0()
    old_dry = rescue.dry_run(rescue.OUT_ROOT_RELATIVE, repo_root=tmp_path)
    assert rescue.BATCH_UUID == "31dca97b-808c-4205-ac01-7c5ab7b9e9b5"
    assert rescue.CONTRACT == "NBLDPC-GF32-SOFT-PRIOR-RESCUE-20261001/PREREG_AND_AUTH.md"
    assert rescue.SEED_NAMESPACE == "gf32-softprior-v1"
    assert old_t0["prior_exclusion_plan_count"] == 13
    assert old_t0["prior_exclusion_rows"] == 2832
    assert old_dry["status"] == "DRY_RUN"
    _assert_no_operations(old_t0)
    _assert_no_operations(old_dry)

    expected_new_plan = [
        (graph_id, stream, frame, int(common.v10_seed(
            f"{replica.SEED_NAMESPACE}:holdout:{graph_id}:{stream}:{frame}")))
        for graph_id in rescue.GRAPH_IDS
        for stream in rescue.HOLDOUT_STREAMS
        for frame in range(rescue.HOLDOUT_FRAMES_PER_STREAM)
    ]
    new_plan, records = replica.validate_seed_plan()
    new_seeds = {row[3] for row in new_plan}
    assert replica.BATCH_UUID == "cbe151fe-25f7-4990-8895-858091467e2b"
    assert replica.CONTRACT == "NBLDPC-GF32-SOFT-PRIOR-REPLICA-20261001/PREREG_AND_AUTH.md"
    assert replica.SEED_NAMESPACE == "gf32-softprior-replica-v1"
    assert replica.OUT_ROOT_RELATIVE == Path("workspace/gf32_softprior_replica_cbe151fe")
    assert new_plan == expected_new_plan
    assert len(new_plan) == len(new_seeds) == 192
    assert new_seeds.isdisjoint({row[3] for row in old_plan})
    assert len(records) == 14
    assert sum(row["rows"] for row in records) == 3024
    assert records[-1] == {
        "generator": replica.PREDECESSOR_PLAN_NAME,
        "rows": 192,
        "unique_seeds": 192,
    }

    excluded_plans = rescue._prior_seed_plans()
    excluded_plans.extend(
        (name, rows, 192) for name, rows in replica.additional_excluded_plans())
    excluded_union = set()
    for name, plan, expected_rows in excluded_plans:
        seeds = rescue._seeds_from_plan(plan)
        assert len(seeds) == len(set(seeds)) == expected_rows, name
        assert new_seeds.isdisjoint(seeds), name
        excluded_union.update(seeds)
    assert len(excluded_union) == 3024

    t0 = replica.verify_t0(repo_root=tmp_path)
    dry = replica.dry_run(repo_root=tmp_path)
    expected_root = tmp_path / replica.OUT_ROOT_RELATIVE
    assert t0["status"] == "PASS"
    assert t0["batch_uuid"] == replica.BATCH_UUID
    assert t0["contract"] == replica.CONTRACT
    assert t0["seed_namespace"] == replica.SEED_NAMESPACE
    assert t0["holdout_pairs"] == 192
    assert t0["prior_exclusion_plan_count"] == 14
    assert t0["prior_exclusion_rows"] == 3024
    assert t0["out_root"] == str(expected_root)
    _assert_no_operations(t0)
    assert dry["status"] == "DRY_RUN"
    assert dry["batch_uuid"] == replica.BATCH_UUID
    assert dry["contract"] == replica.CONTRACT
    assert dry["out_root"] == str(expected_root)
    _assert_no_operations(dry)
    assert not expected_root.exists()


def test_replica_full192_fake_batch_identity_maps_cost_and_disclosure(tmp_path: Path):
    adapters = _fake_batch_adapters(tmp_path)
    state = adapters.pop("state")
    result = replica.execute_batch(
        out_root=replica.OUT_ROOT_RELATIVE, **adapters)
    root = tmp_path / replica.OUT_ROOT_RELATIVE
    expected_plan = replica.build_seed_plan()
    expected_seeds = [row[3] for row in expected_plan]

    assert state["source_reads"] == 1
    assert state["sampler_seeds"] == expected_seeds
    assert len(state["decoder_inputs"]) == 210
    assert result["status"] == "COMPLETE"
    assert result["batch_uuid"] == replica.BATCH_UUID
    assert result["contract"] == replica.CONTRACT
    assert result["seed_namespace"] == replica.SEED_NAMESPACE
    assert result["completed_pairs"] == 192
    assert result["attempted_physical_calls"] == 210
    assert result["baseline_calls"] == 192
    assert result["branch_calls"] == 18
    assert result["logical_control_calls"] == 192
    assert result["logical_candidate_calls"] == 210
    assert result["control_exact"] == 188
    assert result["candidate_exact"] == 189
    assert result["delta_exact"] == 1
    assert result["disclosure_bits"] == 99_840
    assert result["syndrome_bits_per_method_frame"] == 260
    assert result["internal_branch_disclosure_bits"] == 0
    assert result["tag_bits"] == 0
    assert result["verification"] == "NOT_IMPLEMENTED"
    assert result["undetected"] == "NOT_MEASURED"
    assert result["resource_violations"] == 0
    assert result["integrity_violations"] == 0

    pairs = result["pairs"]
    calls = result["calls"]
    assert len(pairs) == 192
    assert len(calls) == 210
    assert [row["seed"] for row in pairs] == expected_seeds
    assert [row["call_index"] for row in calls] == list(range(210))
    assert all(row["seed"] == expected_seeds[row["pair_index"]] for row in calls)
    assert [row["candidate_selected_call_index"] for row in pairs[2:5]] == [6, 10, 16]
    assert all(row["candidate_selected_call_index"] == row["baseline_call_index"]
               for i, row in enumerate(pairs) if i not in (2, 3, 4))

    source_maps = result["source_maps"]
    assert [row["graph_id"] for row in source_maps] == list(rescue.GRAPH_IDS)
    assert source_maps[4]["source_lineage"]["source_matrix_index"] == 9
    assert source_maps[4]["source_lineage"]["source_attempt_j"] == 1
    assert source_maps[4]["source_lineage"]["source_construction_seed"] == 2560859716
    assert {path.name for path in root.iterdir()} == {
        "manifest.json", "summary.json", "frame_records.csv",
        "diagnostics.npz", "EXPLORATION_LOG.md",
    }
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    assert manifest["batch_uuid"] == summary["batch_uuid"] == replica.BATCH_UUID
    assert manifest["contract"] == summary["contract"] == replica.CONTRACT
    assert manifest["seed_namespace"] == summary["seed_namespace"] == replica.SEED_NAMESPACE
    assert [(row["graph_id"], row["stream"], row["frame"], row["seed"])
            for row in manifest["seed_plan"]] == expected_plan
    assert manifest["source_identity"] == {
        "batch_uuid": rescue.SOURCE_BATCH_UUID,
        "contract": rescue.SOURCE_CONTRACT,
        "seed_namespace": rescue.SOURCE_NAMESPACE,
        "graph_input_kind": rescue.SOURCE_KIND,
    }
    assert manifest["source_expected"] == manifest["source_identity"]
    assert len(manifest["seed_exclusion_generators"]) == 14
    assert sum(row["rows"] for row in manifest["seed_exclusion_generators"]) == 3024

    with np.load(root / "diagnostics.npz", allow_pickle=False) as archive:
        assert archive["pair_seed"].tolist() == expected_seeds
        assert archive["call_seed"].tolist() == [row["seed"] for row in calls]
        assert archive["raw_vector_call_index"].tolist() == [
            row["call_index"] for row in calls if row["raw_vector_index"] is not None]
        assert archive["raw_x_hat"].shape == (210, 128)
        assert archive["pair_candidate_selected_call_index"][2:5].tolist() == [6, 10, 16]


def test_replica_partial_resource_stop_keeps_fake_calls_and_nulls_totals(
        tmp_path: Path):
    adapters = _fake_batch_adapters(
        tmp_path, failure_pairs=(0,), branch_resource_pair=0)
    state = adapters.pop("state")
    result = replica.execute_batch(
        out_root=replica.OUT_ROOT_RELATIVE, **adapters)

    assert result["status"] == "INCOMPLETE"
    assert result["batch_uuid"] == replica.BATCH_UUID
    assert result["attempted_physical_calls"] == 2
    assert result["baseline_calls"] == 1
    assert result["branch_calls"] == 1
    assert result["resource_violations"] >= 1
    assert result["control_exact"] is result["candidate_exact"] is None
    assert result["delta_exact"] is result["paired"] is result["per_graph"] is None
    assert [row["role"] for row in result["calls"]] == ["baseline", "soft_prior"]
    assert result["calls"][1]["raw_vector_index"] == 1
    assert state["source_reads"] == 1
    assert len(state["sampler_seeds"]) == 1
    assert len(state["decoder_inputs"]) == 2
    assert state["next_branch"] == 1

