"""Frozen GF(32) soft-prior mechanism probes (EXPLORE)."""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from comparison_bench.cli.probes_closed import nbldpc_gf32_softprior_rescue as rescue
from comparison_bench.cli.probes_closed import nbldpc_gf32_softprior_cost_profile as cost_profile
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout


N, M, Q = rescue.N, rescue.M, rescue.Q
GRAPH_IDS = rescue.GRAPH_IDS
HOLDOUT_STREAMS = rescue.HOLDOUT_STREAMS
HOLDOUT_FRAMES_PER_STREAM = rescue.HOLDOUT_FRAMES_PER_STREAM
HOLDOUT_PAIRS = rescue.HOLDOUT_PAIRS
GUESSES = rescue.GUESSES
MAX_ITER = rescue.MAX_ITER
DAMPING_ALPHA = rescue.DAMPING_ALPHA
SYNDROME_BITS = rescue.SYNDROME_BITS
WALL_CAP_S = 1200.0
RSS_CAP_BYTES = 1 * 1024 ** 3
ARTIFACT_CAP_BYTES = 20 * 1024 * 1024
MAX_PHYSICAL_CALLS = 2496
JOINTTOP2_MAX_PHYSICAL_CALLS = 2112
JOINTCHECK2_MAX_PHYSICAL_CALLS = 2880
TOP3RUNTIME_MAX_PHYSICAL_CALLS = HOLDOUT_PAIRS * (1 + 6 + 3)
JOINTTOP3_MAX_PHYSICAL_CALLS = 2688
JOINTTOP3_MAX_PHYSICAL_ITERATIONS = 241920
JOINTTOP3_J2_SUBSET = (0, 1, 3, 4)
LAMBDA_MIXED = 0.5

PROFILES: dict[str, dict[str, Any]] = {
    "rank2": {
        "batch_uuid": "4cd4756b-989e-47fa-b751-5f9b45d02fee",
        "contract": "NBLDPC-GF32-RANK2-FALLBACK-20261002/PREREG_AND_AUTH.md",
        "seed_namespace": "gf32-softprior-rank2-fallback-v1",
        "out_root": Path("workspace") / "gf32_rank2_4cd4756b",
        "sister_namespace": "gf32-softprior-mixed05-v1",
        "sister_plan_name": "mechanism-sister/gf32-softprior-mixed05-v1",
    },
    "mixed05": {
        "batch_uuid": "20297614-3e4e-4d14-a70b-d74237e5ddd4",
        "contract": "NBLDPC-GF32-MIXED05-20261002/PREREG_AND_AUTH.md",
        "seed_namespace": "gf32-softprior-mixed05-v1",
        "out_root": Path("workspace") / "gf32_mixed05_20297614",
        "sister_namespace": "gf32-softprior-rank2-fallback-v1",
        "sister_plan_name": "mechanism-sister/gf32-softprior-rank2-fallback-v1",
    },
    "jointtop2": {
        "batch_uuid": "d112d5ce-9b97-431a-81ff-9a7abdd9eff5",
        "contract": "NBLDPC-GF32-JOINT-TOP2-20261002/PREREG_AND_AUTH.md",
        "seed_namespace": "gf32-softprior-jointtop2-v1",
        "out_root": Path("workspace") / "gf32_joint_top2_d112d5ce",
        "physical_call_cap": JOINTTOP2_MAX_PHYSICAL_CALLS,
    },
    "jointcheck2": {
        "batch_uuid": "c608cfb6-3593-4364-b4be-a6f65878b372",
        "contract": "NBLDPC-GF32-JOINT-CHECK2-20261002/PREREG_AND_AUTH.md",
        "seed_namespace": "gf32-softprior-jointcheck2-v1",
        "out_root": Path("workspace") / "gf32_joint_check2_c608cfb6",
        "physical_call_cap": JOINTCHECK2_MAX_PHYSICAL_CALLS,
    },
    "top3runtime": {
        "batch_uuid": "65d7a521-09fe-4d02-819c-922fc14157a4",
        "contract": "NBLDPC-GF32-TOP3-RUNTIME-20261003/PREREG_AND_AUTH.md",
        "seed_namespace": "gf32-softprior-top3-runtime-v1",
        "out_root": Path("workspace") / "gf32_top3_runtime_65d7a521",
        "physical_call_cap": TOP3RUNTIME_MAX_PHYSICAL_CALLS,
    },
    "jointtop3": {
        "batch_uuid": "e75d9191-e250-4aec-bf63-00fea8faacbe",
        "contract": "NBLDPC-GF32-JOINT-TOP3-20261004/PREREG_AND_AUTH.md",
        "seed_namespace": "gf32-softprior-jointtop3-v1",
        "out_root": Path("workspace") / "gf32_joint_top3_e75d9191",
        "physical_call_cap": JOINTTOP3_MAX_PHYSICAL_CALLS,
    },
}
RANK2_OUT_ROOT_RELATIVE = PROFILES["rank2"]["out_root"]
MIXED05_OUT_ROOT_RELATIVE = PROFILES["mixed05"]["out_root"]
JOINTTOP2_OUT_ROOT_RELATIVE = PROFILES["jointtop2"]["out_root"]
JOINTCHECK2_OUT_ROOT_RELATIVE = PROFILES["jointcheck2"]["out_root"]

CALL_FIELDS = (
    "call_index", "pair_index", "frame_index", "graph_id", "graph_seed", "stream", "frame", "seed",
    "role", "method", "branch_index", "guess_symbol", "selected_variable",
    "prior_profile", "prior_lambda", "prior_override_symbols_json",
    "returned_selected_symbol", "status", "decoder_status", "iterations",
    "decoder_runtime_s", "wall_s", "rss_bytes", "syndrome_valid",
    "syndrome_ok_reported", "exact", "syndrome_valid_wrong", "syndrome_failed",
    "raw_vector_index", "score_original_prior", "belief_provenance",
    "selected_for_control", "selected_for_candidate",
    "selector_active_variable_columns_json", "selector_violated_check_ids_json",
    "selector_entropy_bits_json", "failure_reason",
)
JOINTTOP2_CALL_FIELDS = ("secondary_variable", "secondary_guess_symbol")
JOINTCHECK2_CALL_FIELDS = JOINTTOP2_CALL_FIELDS + ("selector_violated_neighbor_counts_json",)
TOP3RUNTIME_CALL_FIELDS = ("posterior_rank",)
JOINTTOP3_CALL_FIELDS = JOINTTOP2_CALL_FIELDS + ("selected_for_derived_j2",)

FRAME_FIELDS = (
    "pair_index", "frame_index", "arm_order", "graph_id", "graph_seed", "stream", "frame", "seed", "completed",
    "baseline_call_index", "control_selected_call_index", "candidate_selected_call_index",
    "rank1_variable", "rank2_variable", "rank2_attempted", "rank2_reason",
    "selector_active_variable_columns_json", "selector_violated_check_ids_json",
    "selector_entropy_bits_json", "control_exact", "candidate_exact", "delta_exact",
    "control_syndrome_valid_wrong", "candidate_syndrome_valid_wrong",
    "control_syndrome_failed", "candidate_syndrome_failed", "control_branch_calls",
    "candidate_incremental_branch_calls",
)
JOINTCHECK2_FRAME_FIELDS = FRAME_FIELDS + (
    "control_primary_variable", "control_secondary_variable",
    "candidate_primary_variable", "candidate_secondary_variable",
    "joint_pair_shared", "joint_pair_order",
    "control_joint_branch_calls", "candidate_joint_branch_calls",
    "selector_violated_neighbor_counts_json",
    "control_joint_call_indices_json", "candidate_joint_call_indices_json",
)
TOP3RUNTIME_FRAME_FIELDS = FRAME_FIELDS + (
    "top3_attempted", "top3_selector_status", "posterior_ranked_guesses_json",
    "candidate_top3_guesses_json", "control_branch_call_indices_json",
    "candidate_branch_call_indices_json", "baseline_wall_s",
    "common_selector_wall_s", "control_arm_wall_s", "candidate_arm_wall_s",
)
JOINTTOP3_FRAME_FIELDS = FRAME_FIELDS + (
    "jointtop3_attempted", "jointtop3_primary_guesses_json",
    "jointtop3_secondary_guesses_json", "jointtop3_call_indices_json",
    "derived_j2_call_indices_json", "derived_j2_selected_call_index",
    "derived_j2_selected_branch_index", "derived_j2_exact",
    "delta_j3_vs_derived_j2", "derived_j2_syndrome_valid_wrong",
    "derived_j2_syndrome_failed", "j3_selected_branch_index",
)


def _profile(mechanism: str) -> dict[str, Any]:
    try:
        return PROFILES[mechanism]
    except KeyError as exc:
        raise ValueError(
            "mechanism must be exactly 'rank2', 'mixed05', 'jointtop2', 'jointcheck2', 'top3runtime', or 'jointtop3'") from exc


def build_seed_plan(mechanism: str) -> list[tuple[int, int, int, int]]:
    profile = _profile(mechanism)
    return rescue.build_seed_plan(profile["seed_namespace"])


def _additional_excluded_plans(mechanism: str) -> tuple[tuple[str, list[tuple[int, int, int, int]]], ...]:
    profile = _profile(mechanism)
    common = (
        ("softprior-rescue/gf32-softprior-v1",
         rescue.build_seed_plan("gf32-softprior-v1")),
        ("softprior-replica/gf32-softprior-replica-v1",
         rescue.build_seed_plan("gf32-softprior-replica-v1")),
    )
    if mechanism in ("jointtop2", "jointcheck2", "top3runtime", "jointtop3"):
        plans = common + (
            ("mechanism-predecessor/gf32-softprior-rank2-fallback-v1",
             rescue.build_seed_plan("gf32-softprior-rank2-fallback-v1")),
            ("mechanism-predecessor/gf32-softprior-mixed05-v1",
             rescue.build_seed_plan("gf32-softprior-mixed05-v1")),
        )
        if mechanism in ("jointcheck2", "top3runtime", "jointtop3"):
            plans += (("mechanism-predecessor/gf32-softprior-jointtop2-v1",
                       rescue.build_seed_plan("gf32-softprior-jointtop2-v1")),)
        if mechanism in ("top3runtime", "jointtop3"):
            plans += (("mechanism-predecessor/gf32-softprior-jointcheck2-v1",
                       rescue.build_seed_plan("gf32-softprior-jointcheck2-v1")),)
        if mechanism == "jointtop3":
            plans += (
                ("mechanism-predecessor/gf32-softprior-top3-runtime-v1",
                 rescue.build_seed_plan("gf32-softprior-top3-runtime-v1")),
                ("mechanism-predecessor/gf32-softprior-edge-state-v1",
                 rescue.build_seed_plan("gf32-softprior-edge-state-v1")),
                ("mechanism-predecessor/gf32-softprior-edge-state-r2-v1",
                 rescue.build_seed_plan("gf32-softprior-edge-state-r2-v1")),
            )
        return plans
    return common + ((profile["sister_plan_name"],
                      rescue.build_seed_plan(profile["sister_namespace"])),)


def validate_seed_plan(
        mechanism: str, plan: Sequence[Sequence[int]] | None = None,
        ) -> tuple[list[tuple[int, int, int, int]], list[dict[str, Any]]]:
    profile = _profile(mechanism)
    return rescue.validate_seed_plan(
        plan, seed_namespace=profile["seed_namespace"],
        additional_excluded_plans=_additional_excluded_plans(mechanism))


def verify_t0(mechanism: str) -> dict[str, Any]:
    profile = _profile(mechanism)
    rows, exclusions = validate_seed_plan(mechanism)
    if (len(rows) != HOLDOUT_PAIRS
            or len({row[3] for row in rows}) != HOLDOUT_PAIRS
            or not np.isclose(rescue.pmf().sum(), 1.0, atol=1e-15)):
        raise AssertionError("frozen mechanism seed plan or PMF is invalid")
    expected_exclusions = ((22, 4560) if mechanism == "jointtop3" else
                           (19, 3984) if mechanism == "top3runtime" else
                           (18, 3792) if mechanism == "jointcheck2" else
                           (17, 3600) if mechanism == "jointtop2" else (16, 3408))
    if (len(exclusions), sum(int(row["rows"]) for row in exclusions)) != expected_exclusions:
        raise AssertionError("the frozen seed-exclusion plans changed")
    return {
        "status": "PASS", "mechanism": mechanism,
        "batch_uuid": profile["batch_uuid"], "contract": profile["contract"],
        "seed_namespace": profile["seed_namespace"], "holdout_pairs": HOLDOUT_PAIRS,
        "prior_exclusion_plan_count": len(exclusions),
        "prior_exclusion_rows": sum(int(row["rows"]) for row in exclusions),
        "source_reads": 0, "sampler_calls": 0, "decoder_calls": 0, "writes": 0,
    }


def dry_run(mechanism: str, out_root: str | Path | None = None,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    profile = _profile(mechanism)
    requested = profile["out_root"] if out_root is None else out_root
    root = rescue.validate_out_root(
        requested, repo_root=repo_root, official_root=profile["out_root"])
    return {
        "status": "DRY_RUN", "mechanism": mechanism,
        "batch_uuid": profile["batch_uuid"], "contract": profile["contract"],
        "out_root": str(root), "source_reads": 0, "sampler_calls": 0,
        "decoder_calls": 0, "writes": 0, "t0": verify_t0(mechanism),
    }


def select_rank2_variable(selector_metadata: Mapping[str, Any], rank1_variable: int
                          ) -> int | None:
    """Choose the next entropy-ranked active column from the same baseline beliefs."""
    active = [int(column) for column in selector_metadata["active_variable_columns"]
              if int(column) != int(rank1_variable)]
    if not active:
        return None
    entropy = selector_metadata["entropy_bits"]
    maximum = max(float(entropy[column]) for column in active)
    return min(column for column in active
               if maximum - float(entropy[column]) <= 1e-12)


def select_jointcheck2_variables(
        H: Any, selector_metadata: Mapping[str, Any]
        ) -> tuple[int | None, int | None, dict[int, int]]:
    """Select two active columns by violated-check degree, then baseline entropy."""
    matrix = np.asarray(H)
    active = [int(column) for column in selector_metadata["active_variable_columns"]]
    violated = np.asarray(selector_metadata["violated_check_ids"], dtype=np.int64).ravel()
    entropy = np.asarray(selector_metadata["entropy_bits"], dtype=np.float64).ravel()
    if (matrix.ndim != 2 or entropy.shape != (matrix.shape[1],)
            or np.any(violated < 0) or np.any(violated >= matrix.shape[0])
            or any(column < 0 or column >= matrix.shape[1] for column in active)
            or not np.all(np.isfinite(entropy))):
        raise ValueError("jointcheck2 selector inputs have invalid shapes or indices")
    counts = {
        column: int(np.count_nonzero(matrix[violated, column] != 0))
        for column in active
    }

    def choose(columns: Sequence[int]) -> int | None:
        eligible = [int(column) for column in columns if counts[int(column)] > 0]
        if not eligible:
            return None
        max_count = max(counts[column] for column in eligible)
        by_count = [column for column in eligible if counts[column] == max_count]
        max_entropy = max(float(entropy[column]) for column in by_count)
        tied = [column for column in by_count
                if max_entropy - float(entropy[column]) <= 1e-12]
        return min(tied)

    primary = choose(active)
    secondary = (None if primary is None else
                 choose([column for column in active if column != primary]))
    return primary, secondary, counts


def build_joint_branch_plan(
        primary_guesses: Sequence[int], secondary_guesses: Sequence[int]
        ) -> list[tuple[int, int, int]]:
    """Return four primary-outer/secondary-inner ordered joint guesses."""
    first = [int(value) for value in primary_guesses[:2]]
    second = [int(value) for value in secondary_guesses[:2]]
    if len(first) != 2 or len(second) != 2:
        raise ValueError("jointcheck2 requires exactly two ranked guesses per variable")
    if any(value not in GUESSES for value in first + second):
        raise ValueError("jointcheck2 guesses must use the frozen six-symbol support")
    return [(index, guess1, guess2)
            for index, (guess1, guess2) in enumerate(
                (g1, g2) for g1 in first for g2 in second)]


def build_jointtop3_branch_plan(
        primary_guesses: Sequence[int], secondary_guesses: Sequence[int]
        ) -> list[tuple[int, int, int]]:
    """Return nine primary-outer/secondary-inner ordered joint guesses."""
    first = [int(value) for value in primary_guesses[:3]]
    second = [int(value) for value in secondary_guesses[:3]]
    if len(first) != 3 or len(second) != 3:
        raise ValueError("jointtop3 requires exactly three ranked guesses per variable")
    if any(value not in GUESSES for value in first + second):
        raise ValueError("jointtop3 guesses must use the frozen six-symbol support")
    return [(3 * i + j, guess1, guess2)
            for i, guess1 in enumerate(first)
            for j, guess2 in enumerate(second)]


def build_top3_branch_plan(
        baseline_beliefs: Any, selected_variable: int
        ) -> list[tuple[int, int, int]]:
    """Rank top-three guesses; retain canonical branch index separately from rank."""
    ranked, _ = cost_profile.rank_allowed_guesses(baseline_beliefs, selected_variable)
    if len(ranked) < 3:
        raise ValueError("top3runtime requires three ranked guesses")
    return [(rank, GUESSES.index(int(symbol)), int(symbol))
            for rank, symbol in enumerate(ranked[:3])]


def _run_status_for_pairs(summary: dict[str, Any], completed: int) -> str:
    return "COMPLETE" if completed == HOLDOUT_PAIRS else "INCOMPLETE"


def _classification(mechanism: str, summary: Mapping[str, Any]) -> str:
    if mechanism == "top3runtime":
        baseline = int(summary["baseline_exact"])
        control = int(summary["control_exact"])
        candidate = int(summary["candidate_exact"])
        full6_gain = control - baseline
        top3_gain = candidate - baseline
        timing = summary["timing"]
        control_path = timing["control_method_path_s"]
        candidate_path = timing["candidate_method_path_s"]
        method_path_ratio = (
            None if control_path is None or candidate_path is None or control_path <= 0.0
            else float(candidate_path) / float(control_path))
        retention = (None if full6_gain <= 0 else float(top3_gain) / float(full6_gain))
        summary["full6_gain"] = int(full6_gain)
        summary["top3_gain"] = int(top3_gain)
        summary["gain_retention"] = retention
        summary["accounted_method_path_ratio"] = method_path_ratio
        if not 39 <= baseline <= 153 or full6_gain <= 0:
            return "TRADEOFF_SCREEN_UNINFORMATIVE"
        if (retention is not None and retention >= 0.75
                and method_path_ratio is not None and method_path_ratio <= 0.70
                and int(summary["syndrome_valid_wrong_candidate"])
                <= int(summary["syndrome_valid_wrong_control"])):
            return "TRADEOFF_SCREEN_MET"
        return "TRADEOFF_SCREEN_NOT_MET"
    baseline = int(summary["baseline_exact"])
    delta = int(summary["delta_exact"])
    graph_deltas = [int(row["delta_exact"]) for row in summary["per_graph"].values()]
    if not 39 <= baseline <= 153:
        return "CONTROL_RANGE_UNINFORMATIVE"
    if delta >= 6 and sum(value > 0 for value in graph_deltas) >= 4:
        if (int(summary["syndrome_valid_wrong_candidate"])
                <= int(summary["syndrome_valid_wrong_control"])):
            return "EXPLORATORY_INCREMENT_SIGNAL"
    return "INCREMENT_NOT_ESTABLISHED"


def _null_totals(summary: dict[str, Any], mechanism: str | None = None) -> None:
    for key in (
        "baseline_exact", "control_exact", "candidate_exact", "delta_exact",
        "syndrome_valid_wrong_control", "syndrome_valid_wrong_candidate",
        "syndrome_failed_control", "syndrome_failed_candidate", "paired", "per_graph",
    ):
        summary[key] = None
    for key in ("full6_gain", "top3_gain", "gain_retention",
                "accounted_method_path_ratio"):
        if key in summary:
            summary[key] = None
    if mechanism == "jointtop3":
        for key in (
            "derived_j2_exact", "delta_j3_vs_derived_j2",
            "syndrome_valid_wrong_derived_j2", "syndrome_failed_derived_j2",
            "raw_valid_wrong_control", "raw_valid_wrong_j3",
            "raw_valid_wrong_derived_j2", "j3_added_five_wins", "j3_added_five_losses",
            "paired_j3_vs_derived_j2", "per_graph_j3_vs_derived_j2",
        ):
            summary[key] = None
    summary["classification"] = (
        None if mechanism == "jointtop3" and summary["status"] == "INCOMPLETE" else
        "STOP" if summary["status"] == "STOP" else "INCOMPLETE")


def _full_totals(
        summary: dict[str, Any],
        pairs: Sequence[Mapping[str, Any]],
        calls: Sequence[Mapping[str, Any]],
        ) -> None:
    complete = [row for row in pairs if row.get("completed")]
    baseline_exact = sum(
        bool(row["exact"]) for row in calls if row.get("role") == "baseline")
    control_exact = sum(bool(row["control_exact"]) for row in complete)
    candidate_exact = sum(bool(row["candidate_exact"]) for row in complete)
    wrong_control = sum(bool(row["control_valid_wrong"]) for row in complete)
    wrong_candidate = sum(bool(row["candidate_valid_wrong"]) for row in complete)
    failed_control = sum(bool(row["control_syndrome_failed"]) for row in complete)
    failed_candidate = sum(bool(row["candidate_syndrome_failed"]) for row in complete)
    per_graph: dict[str, dict[str, int]] = {}
    for graph_id in GRAPH_IDS:
        rows = [row for row in complete if int(row["graph_id"]) == graph_id]
        control = sum(bool(row["control_exact"]) for row in rows)
        candidate = sum(bool(row["candidate_exact"]) for row in rows)
        per_graph[str(graph_id)] = {
            "n": len(rows), "control_exact": int(control),
            "candidate_exact": int(candidate), "delta_exact": int(candidate - control),
            "control_valid_wrong": int(sum(bool(x["control_valid_wrong"]) for x in rows)),
            "candidate_valid_wrong": int(sum(bool(x["candidate_valid_wrong"]) for x in rows)),
            "control_syndrome_failed": int(sum(bool(x["control_syndrome_failed"]) for x in rows)),
            "candidate_syndrome_failed": int(sum(bool(x["candidate_syndrome_failed"]) for x in rows)),
        }
    both = sum(bool(row["control_exact"] and row["candidate_exact"]) for row in complete)
    control_only = sum(bool(row["control_exact"] and not row["candidate_exact"]) for row in complete)
    candidate_only = sum(bool(row["candidate_exact"] and not row["control_exact"]) for row in complete)
    summary.update({
        "baseline_exact": int(baseline_exact),
        "control_exact": int(control_exact), "candidate_exact": int(candidate_exact),
        "delta_exact": int(candidate_exact - control_exact),
        "syndrome_valid_wrong_control": int(wrong_control),
        "syndrome_valid_wrong_candidate": int(wrong_candidate),
        "syndrome_failed_control": int(failed_control),
        "syndrome_failed_candidate": int(failed_candidate),
        "paired": {"both_exact": int(both), "candidate_only": int(candidate_only),
                   "control_only": int(control_only),
                   "neither": int(len(complete) - both - control_only - candidate_only)},
        "per_graph": per_graph,
    })


def _jointtop3_full_totals(
        summary: dict[str, Any], pairs: Sequence[Mapping[str, Any]],
        calls: Sequence[Mapping[str, Any]],
        ) -> None:
    """Summarize derived J2 from already executed jointtop3 outputs."""
    complete = [row for row in pairs if row.get("completed")]
    both = sum(bool(row["candidate_exact"] and row["derived_j2_exact"])
               for row in complete)
    j3_only = sum(bool(row["candidate_exact"] and not row["derived_j2_exact"])
                  for row in complete)
    j2_only = sum(bool(row["derived_j2_exact"] and not row["candidate_exact"])
                  for row in complete)
    j2_exact = sum(bool(row["derived_j2_exact"]) for row in complete)
    j2_wrong = sum(bool(row["derived_j2_valid_wrong"]) for row in complete)
    j2_failed = sum(bool(row["derived_j2_syndrome_failed"]) for row in complete)
    control_roles = ("baseline", "rank1_onehot")
    j2_roles = (*control_roles, "jointtop3_candidate")
    raw_wrong_control = sum(
        row.get("role") in control_roles
        and row.get("syndrome_valid") is True and row.get("exact") is False
        for row in calls)
    raw_wrong_j3 = sum(
        row.get("role") in j2_roles
        and row.get("syndrome_valid") is True and row.get("exact") is False
        for row in calls)
    j2_raw_wrong = sum(
        (row.get("role") in ("baseline", "rank1_onehot")
         or (row.get("role") == "jointtop3_candidate"
             and int(row.get("branch_index", -1)) in JOINTTOP3_J2_SUBSET))
        and row.get("syndrome_valid") is True and row.get("exact") is False
        for row in calls)
    added_five_wins = sum(
        bool(row["candidate_exact"] and not row["derived_j2_exact"])
        and int(row.get("j3_selected_branch_index", -1)) >= 0
        and int(row["j3_selected_branch_index"]) not in JOINTTOP3_J2_SUBSET
        for row in complete)
    added_five_losses = sum(
        bool(row["derived_j2_exact"] and not row["candidate_exact"])
        and int(row.get("j3_selected_branch_index", -1)) >= 0
        and int(row["j3_selected_branch_index"]) not in JOINTTOP3_J2_SUBSET
        for row in complete)
    per_graph: dict[str, dict[str, int]] = {}
    for graph_id in GRAPH_IDS:
        rows = [row for row in complete if int(row["graph_id"]) == graph_id]
        g_both = sum(bool(row["candidate_exact"] and row["derived_j2_exact"])
                     for row in rows)
        g_j3_only = sum(bool(row["candidate_exact"] and not row["derived_j2_exact"])
                        for row in rows)
        g_j2_only = sum(bool(row["derived_j2_exact"] and not row["candidate_exact"])
                        for row in rows)
        g_added_five_wins = sum(
            bool(row["candidate_exact"] and not row["derived_j2_exact"])
            and int(row.get("j3_selected_branch_index", -1)) >= 0
            and int(row["j3_selected_branch_index"]) not in JOINTTOP3_J2_SUBSET
            for row in rows)
        g_added_five_losses = sum(
            bool(row["derived_j2_exact"] and not row["candidate_exact"])
            and int(row.get("j3_selected_branch_index", -1)) >= 0
            and int(row["j3_selected_branch_index"]) not in JOINTTOP3_J2_SUBSET
            for row in rows)
        pair_ids = {int(row["pair_index"]) for row in rows}
        graph_calls = [call for call in calls if int(call["pair_index"]) in pair_ids]
        graph_raw_wrong_control = sum(
            call.get("role") in control_roles
            and call.get("syndrome_valid") is True and call.get("exact") is False
            for call in graph_calls)
        graph_raw_wrong_j3 = sum(
            call.get("role") in j2_roles
            and call.get("syndrome_valid") is True and call.get("exact") is False
            for call in graph_calls)
        graph_raw_wrong_j2 = sum(
            (call.get("role") in control_roles
             or (call.get("role") == "jointtop3_candidate"
                 and int(call.get("branch_index", -1)) in JOINTTOP3_J2_SUBSET))
            and call.get("syndrome_valid") is True and call.get("exact") is False
            for call in graph_calls)
        per_graph[str(graph_id)] = {
            "n": len(rows),
            "j3_exact": int(sum(bool(row["candidate_exact"]) for row in rows)),
            "derived_j2_exact": int(sum(bool(row["derived_j2_exact"]) for row in rows)),
            "delta_exact": int(sum(bool(row["candidate_exact"]) for row in rows)
                                - sum(bool(row["derived_j2_exact"]) for row in rows)),
            "both_exact": int(g_both), "j3_only": int(g_j3_only),
            "derived_j2_only": int(g_j2_only),
            "j3_added_five_wins": int(g_added_five_wins),
            "j3_added_five_losses": int(g_added_five_losses),
            "derived_j2_selected_valid_wrong": int(sum(
                bool(row["derived_j2_valid_wrong"]) for row in rows)),
            "derived_j2_syndrome_failed": int(sum(
                bool(row["derived_j2_syndrome_failed"]) for row in rows)),
            "raw_valid_wrong_control": int(graph_raw_wrong_control),
            "raw_valid_wrong_j3": int(graph_raw_wrong_j3),
            "raw_valid_wrong_derived_j2": int(graph_raw_wrong_j2),
        }
    summary.update({
        "derived_j2_exact": int(j2_exact),
        "delta_j3_vs_derived_j2": int(summary["candidate_exact"] - j2_exact),
        "syndrome_valid_wrong_derived_j2": int(j2_wrong),
        "syndrome_failed_derived_j2": int(j2_failed),
        "raw_valid_wrong_control": int(raw_wrong_control),
        "raw_valid_wrong_j3": int(raw_wrong_j3),
        "raw_valid_wrong_derived_j2": int(j2_raw_wrong),
        "j3_added_five_wins": int(added_five_wins),
        "j3_added_five_losses": int(added_five_losses),
        "paired_j3_vs_derived_j2": {
            "both_exact": int(both), "j3_only": int(j3_only),
            "derived_j2_only": int(j2_only),
            "neither": int(len(complete) - both - j3_only - j2_only),
        },
        "per_graph_j3_vs_derived_j2": per_graph,
    })


def _source_map(row: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "H"}


def _diagnostic_arrays(
        selected_sources: Sequence[Mapping[str, Any]],
        source_identity: Mapping[str, str] | None,
        original_prior: np.ndarray,
        pairs: Sequence[Mapping[str, Any]],
        calls: Sequence[Mapping[str, Any]],
        raw_vectors: Sequence[np.ndarray],
        ) -> dict[str, np.ndarray]:
    sampled = [row for row in pairs if row.get("truth") is not None]
    beliefs = [{"call_index": row["baseline_call_index"],
                "provenance": "CHECK_UPDATED", "beliefs": row["baseline_beliefs"]}
               for row in sampled if row.get("baseline_beliefs") is not None]
    selectors = []
    for row in sampled:
        metadata = row.get("selector_metadata")
        if metadata is None:
            continue
        if row.get("top3_selector_status") == "no_active":
            continue
        active = np.zeros(N, dtype=np.bool_)
        active[metadata["active_variable_columns"]] = True
        violated = np.zeros(M, dtype=np.bool_)
        violated[metadata["violated_check_ids"]] = True
        selectors.append({"call_index": row["baseline_call_index"], "metadata": metadata,
                          "active_mask": active, "violated_mask": violated})
    scores = [{"call_index": row["call_index"], "branch_index": row["branch_index"],
               "guess_symbol": row["guess_symbol"], "score": row["score_original_prior"],
               "syndrome_valid": bool(row.get("syndrome_valid"))}
              for row in calls if row.get("branch_index", -1) >= 0]
    arrays = rescue._diagnostic_arrays(
        selected_sources, source_identity, original_prior, sampled, calls,
        raw_vectors, beliefs, selectors, scores)
    if sampled and "top3_attempted" in sampled[0]:
        arrays["call_role"] = np.asarray([row["role"] for row in calls], dtype="<U24")
        arrays["call_posterior_rank"] = np.asarray(
            [row.get("posterior_rank", -1) for row in calls], dtype=np.int64)
        arrays["pair_top3_attempted"] = np.asarray(
            [row.get("top3_attempted", False) for row in sampled], dtype=np.bool_)
        arrays["pair_baseline_wall_s"] = np.asarray(
            [np.nan if row.get("baseline_wall_s") is None else row["baseline_wall_s"]
             for row in sampled], dtype=np.float64)
        arrays["pair_common_selector_wall_s"] = np.asarray(
            [row.get("common_selector_wall_s", 0.0) for row in sampled], dtype=np.float64)
        arrays["pair_control_arm_wall_s"] = np.asarray(
            [row.get("control_arm_wall_s", 0.0) for row in sampled], dtype=np.float64)
        arrays["pair_candidate_arm_wall_s"] = np.asarray(
            [row.get("candidate_arm_wall_s", 0.0) for row in sampled], dtype=np.float64)
        arrays["pair_posterior_ranked_guesses"] = np.asarray([
            (list(row.get("posterior_ranked_guesses", [])) + [-1] * 3)[:3]
            for row in sampled], dtype=np.int64).reshape((-1, 3))
    arrays.update({
        "pair_frame_index": np.asarray([row["frame_index"] for row in sampled], dtype=np.int64),
        "pair_arm_order": np.asarray([row.get("arm_order", "") for row in sampled], dtype="<U40"),
        "pair_control_selected_call_index": np.asarray(
            [row.get("control_selected_call_index", -1) for row in sampled], dtype=np.int64),
        "pair_rank1_variable": np.asarray([row.get("rank1_variable", -1) for row in sampled], dtype=np.int64),
        "pair_rank2_variable": np.asarray([row.get("rank2_variable", -1) for row in sampled], dtype=np.int64),
        "pair_rank2_attempted": np.asarray([row.get("rank2_attempted", False) for row in sampled], dtype=np.bool_),
        "pair_rank2_reason": np.asarray([row.get("rank2_reason", "") for row in sampled], dtype="<U96"),
        "call_frame_index": np.asarray([row["frame_index"] for row in calls], dtype=np.int64),
        "call_method": np.asarray([row.get("method", "") for row in calls], dtype="<U12"),
        "call_role": np.asarray([row.get("role", "") for row in calls], dtype="<U24"),
        "call_prior_profile": np.asarray([row.get("prior_profile", "") for row in calls], dtype="<U32"),
        "call_prior_lambda": np.asarray([row.get("prior_lambda", np.nan) for row in calls], dtype=np.float64),
        "call_prior_override": np.asarray([
            np.full(Q, np.nan) if row.get("prior_override") is None else row["prior_override"]
            for row in calls], dtype=np.float64).reshape((-1, Q)),
    })
    if sampled and "control_primary_variable" in sampled[0]:
        arrays.update({
            "pair_control_primary_variable": np.asarray(
                [row.get("control_primary_variable", -1) for row in sampled], dtype=np.int64),
            "pair_control_secondary_variable": np.asarray(
                [row.get("control_secondary_variable", -1) for row in sampled], dtype=np.int64),
            "pair_candidate_primary_variable": np.asarray(
                [row.get("candidate_primary_variable", -1) for row in sampled], dtype=np.int64),
            "pair_candidate_secondary_variable": np.asarray(
                [row.get("candidate_secondary_variable", -1) for row in sampled], dtype=np.int64),
            "pair_joint_pair_shared": np.asarray(
                [row.get("joint_pair_shared", False) for row in sampled], dtype=np.bool_),
            "pair_joint_pair_order": np.asarray(
                [row.get("joint_pair_order", "") for row in sampled], dtype="<U32"),
            "selector_violated_neighbor_counts": np.asarray([
                [int((row.get("selector_violated_neighbor_counts") or {}).get(column, 0))
                 for column in range(N)] for row in sampled], dtype=np.int16),
            "call_secondary_variable": np.asarray(
                [row.get("secondary_variable", -1) for row in calls], dtype=np.int64),
            "call_secondary_guess_symbol": np.asarray(
                [row.get("secondary_guess_symbol", -1) for row in calls], dtype=np.int64),
        })
    if sampled and "jointtop3_attempted" in sampled[0]:
        arrays.update({
            "pair_jointtop3_attempted": np.asarray(
                [row.get("jointtop3_attempted", False) for row in sampled], dtype=np.bool_),
            "pair_jointtop3_primary_guesses": np.asarray([
                (list(row.get("jointtop3_primary_guesses", [])) + [-1] * 3)[:3]
                for row in sampled], dtype=np.int64).reshape((-1, 3)),
            "pair_jointtop3_secondary_guesses": np.asarray([
                (list(row.get("jointtop3_secondary_guesses", [])) + [-1] * 3)[:3]
                for row in sampled], dtype=np.int64).reshape((-1, 3)),
            "pair_jointtop3_call_indices": np.asarray([
                (list(row.get("jointtop3_call_indices", [])) + [-1] * 9)[:9]
                for row in sampled], dtype=np.int64).reshape((-1, 9)),
            "pair_derived_j2_call_indices": np.asarray([
                (list(row.get("derived_j2_call_indices", [])) + [-1] * 4)[:4]
                for row in sampled], dtype=np.int64).reshape((-1, 4)),
            "pair_derived_j2_selected_call_index": np.asarray(
                [row.get("derived_j2_selected_call_index", -1) for row in sampled], dtype=np.int64),
            "pair_j3_selected_branch_index": np.asarray(
                [row.get("j3_selected_branch_index", -1) for row in sampled], dtype=np.int64),
            "pair_derived_j2_selected_branch_index": np.asarray(
                [row.get("derived_j2_selected_branch_index", -1) for row in sampled], dtype=np.int64),
            "call_selected_for_derived_j2": np.asarray(
                [row.get("selected_for_derived_j2", False) for row in calls], dtype=np.bool_),
            "call_secondary_variable": np.asarray(
                [row.get("secondary_variable", -1) for row in calls], dtype=np.int64),
            "call_secondary_guess_symbol": np.asarray(
                [row.get("secondary_guess_symbol", -1) for row in calls], dtype=np.int64),
        })
    if any(row.get("truth") is None for row in pairs):
        arrays["attempted_pair_index"] = np.asarray([row["pair_index"] for row in pairs], dtype=np.int64)
        arrays["attempted_pair_seed"] = np.asarray([row["seed"] for row in pairs], dtype=np.int64)
        arrays["attempted_pair_truth_present"] = np.asarray(
            [row.get("truth") is not None for row in pairs], dtype=np.bool_)
    return arrays


def _write_csv(path: Path, fields: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: (json.dumps(value, separators=(",", ":"))
                      if isinstance(value, (list, dict, tuple)) else value)
                for key, value in row.items()
            })


def execute_batch(
        *, mechanism: str,
        source_reader: Callable[[], Mapping[str, Any]],
        sampler: Callable[..., Any],
        decode_fns: Mapping[str, Callable[..., Any]],
        out_root: str | Path | None = None,
        repo_root: str | Path | None = None,
        now: Callable[[], float] = time.perf_counter,
        rss_fn: Callable[[], int | None] | None = None,
        command: str | None = None,
        ) -> dict[str, Any]:
    profile = _profile(mechanism)
    physical_call_cap = int(profile.get("physical_call_cap", MAX_PHYSICAL_CALLS))
    requested_root = profile["out_root"] if out_root is None else out_root
    root = rescue.validate_out_root(
        requested_root, repo_root=repo_root, official_root=profile["out_root"])
    if not callable(source_reader) or not callable(sampler):
        raise ValueError("explicit source_reader and sampler callbacks are required")
    if (not isinstance(decode_fns, Mapping)
            or set(decode_fns) != {"baseline", "soft_prior"}
            or any(not callable(decode_fns[key]) for key in decode_fns)):
        raise ValueError("decode_fns must explicitly provide baseline and soft_prior callbacks")
    rss_fn = rescue._rss_bytes if rss_fn is None else rss_fn
    started = float(now())
    root.mkdir(parents=True, exist_ok=False)
    log_path = root / "EXPLORATION_LOG.md"
    rescue._append_log(log_path, (
        f"EXPLORE {mechanism} batch {profile['batch_uuid']} started; "
        "source, profile, and seed plans are frozen."))

    summary: dict[str, Any] = {
        "track": "EXPLORE", "mechanism": mechanism,
        "batch_uuid": profile["batch_uuid"], "contract": profile["contract"],
        "claim_ceiling": "Synthetic finite-length mechanism diagnostic only; no FER, f_eff, leakage, SKR, real-data, route-closure, qualification, or publication claim.",
        "seed_namespace": profile["seed_namespace"], "status": "RUNNING",
        "classification": None, "planned_pairs": HOLDOUT_PAIRS, "sampled_pairs": 0,
        "completed_pairs": 0, "attempted_physical_calls": 0,
        "baseline_calls": 0, "branch_calls": 0,
        "logical_control_calls": 0, "logical_candidate_calls": 0,
        "physical_decoder_iterations": 0, "logical_control_iterations": 0,
        "logical_candidate_iterations": 0, "nominal_edge_iteration_proxy": 0,
        "disclosure_bits_physical_batch": 0,
        "syndrome_bits_per_method_frame": SYNDROME_BITS,
        "internal_branch_disclosure_bits": 0, "tag_bits": 0,
        "verification": "NOT_IMPLEMENTED", "undetected": "NOT_MEASURED",
        "baseline_exact": None, "control_exact": None,
        "candidate_exact": None, "delta_exact": None,
        "syndrome_valid_wrong_control": None, "syndrome_valid_wrong_candidate": None,
        "syndrome_failed_control": None, "syndrome_failed_candidate": None,
        "paired": None, "per_graph": None, "raw_valid_wrong_by_role": {},
        "resource_violations": 0, "integrity_violations": 0,
        "data_violations": 0, "authorization_violations": 0,
        "peak_rss_bytes": None, "total_wall_s": None,
        "prior_exclusion_plan_count": 0, "prior_exclusion_rows": 0,
        "stop_reasons": [],
    }
    if mechanism == "top3runtime":
        summary.update({
            "baseline_failures": 0, "baseline_failures_branched": 0,
            "no_active_frames": 0, "full6_gain": None, "top3_gain": None,
            "gain_retention": None, "accounted_method_path_ratio": None,
            "timing": None, "top3runtime_accounting": None,
        })
    if mechanism == "jointtop3":
        summary.update({
            "logical_derived_j2_calls": 0,
            "logical_derived_j2_iterations": 0,
            "derived_j2_exact": None, "delta_j3_vs_derived_j2": None,
            "syndrome_valid_wrong_derived_j2": None,
            "syndrome_failed_derived_j2": None,
            "raw_valid_wrong_derived_j2": None,
            "j3_added_five_wins": None, "j3_added_five_losses": None,
            "paired_j3_vs_derived_j2": None,
            "per_graph_j3_vs_derived_j2": None,
            "jointtop3_accounting": None,
        })
    plan: list[tuple[int, int, int, int]] = []
    exclusions: list[dict[str, Any]] = []
    source_identity: dict[str, str] | None = None
    selected_sources: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    raw_vectors: list[np.ndarray] = []
    resources: list[str] = []
    stop_reasons: list[str] = []
    peak_rss: int | None = None
    run_status = "RUNNING"
    physical_iterations = 0
    original_pmf = rescue.pmf()
    original_prior = np.tile(original_pmf, (N, 1))
    prior_eff = rescue.effective_prior(original_prior)

    def stop(status: str, reason: str, kind: str) -> None:
        nonlocal run_status
        if run_status in ("RUNNING", "COMPLETE") or (run_status == "INCOMPLETE" and status == "STOP"):
            run_status = status
        if reason not in stop_reasons:
            stop_reasons.append(reason)
        counter = {"resource": "resource_violations", "integrity": "integrity_violations",
                   "data": "data_violations", "authorization": "authorization_violations"}[kind]
        summary[counter] = int(summary[counter]) + 1

    def check_resources(phase: str, *, after_call: bool = False,
                        at_time: float | None = None) -> list[str]:
        nonlocal peak_rss
        elapsed = max((float(now()) if at_time is None else at_time) - started, 0.0)
        current_rss = rss_fn()
        if current_rss is not None:
            current_rss = int(current_rss)
            peak_rss = current_rss if peak_rss is None else max(peak_rss, current_rss)
        reasons: list[str] = []
        if elapsed > WALL_CAP_S:
            reasons.append("total_wall_cap")
        if current_rss is not None and current_rss > RSS_CAP_BYTES:
            reasons.append("peak_rss_cap")
        if reasons:
            resources.extend(f"{phase}:{reason}" for reason in reasons)
        return reasons

    def make_call(pair: dict[str, Any], *, role: str, method: str,
                  prior: np.ndarray, branch_index: int = -1,
                  guess_symbol: int = -1, selected_variable: int = -1,
                  posterior_rank: int = -1,
                  secondary_variable: int = -1, secondary_guess_symbol: int = -1,
                  prior_profile: str = "original", prior_lambda: float = math.nan,
                  prior_override: np.ndarray | None = None,
                  selector_metadata: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
        nonlocal peak_rss, physical_iterations
        if len(calls) >= physical_call_cap:
            stop("INCOMPLETE", "physical_call_cap", "resource")
            return None
        if (mechanism == "jointtop3"
                and physical_iterations >= JOINTTOP3_MAX_PHYSICAL_ITERATIONS):
            resources.append("before_decoder_call:physical_iteration_cap")
            stop("INCOMPLETE", "physical_iteration_cap", "resource")
            return None
        before = check_resources("before_decoder_call")
        if before:
            stop("INCOMPLETE", ";".join(before), "resource")
            return None
        row: dict[str, Any] = {
            **{key: pair[key] for key in ("pair_index", "frame_index", "graph_id", "graph_seed", "stream", "frame", "seed")},
            "call_index": len(calls), "role": role, "method": method,
            "branch_index": int(branch_index), "guess_symbol": int(guess_symbol),
            "selected_variable": int(selected_variable),
            "prior_profile": prior_profile,
            "prior_lambda": prior_lambda, "prior_override": None if prior_override is None else np.asarray(prior_override, dtype=np.float64).copy(),
            "returned_selected_symbol": -1, "status": "RUNNING", "decoder_status": None,
            "iterations": None, "decoder_runtime_s": None, "wall_s": None, "rss_bytes": None,
            "syndrome_valid": None, "syndrome_ok_reported": None, "exact": None,
            "syndrome_valid_wrong": None, "syndrome_failed": None,
            "raw_vector_index": None, "score_original_prior": None,
            "belief_provenance": "", "selected_for_control": False,
            "selected_for_candidate": False, "failure_reason": "", "x_hat": None,
        }
        if mechanism in ("jointtop2", "jointcheck2", "jointtop3"):
            row["secondary_variable"] = int(secondary_variable)
            row["secondary_guess_symbol"] = int(secondary_guess_symbol)
        if mechanism == "jointtop3":
            row["selected_for_derived_j2"] = False
        if mechanism == "top3runtime":
            row["posterior_rank"] = int(posterior_rank)
        if mechanism == "jointcheck2":
            row["selector_violated_neighbor_counts_json"] = (
                "" if selector_metadata is None else json.dumps(
                    selector_metadata.get("violated_neighbor_counts", {}),
                    separators=(",", ":")))
        if selector_metadata is not None:
            row["selector_active_variable_columns_json"] = json.dumps(
                selector_metadata["active_variable_columns"])
            row["selector_violated_check_ids_json"] = json.dumps(
                selector_metadata["violated_check_ids"])
            row["selector_entropy_bits_json"] = json.dumps(selector_metadata["entropy_bits"])
        calls.append(row)
        call_started = float(now())
        try:
            decoder = decode_fns["baseline" if role == "baseline" else "soft_prior"]
            raw = decoder(pair["H"], np.asarray(prior, dtype=np.float64).copy(),
                          pair["syndrome"], max_iter=MAX_ITER,
                          damping_alpha=DAMPING_ALPHA, warm_beliefs=None, field=None)
            x_hat = np.asarray(raw.x_hat)
            if (x_hat.shape != (N,) or not np.issubdtype(x_hat.dtype, np.integer)
                    or np.any(x_hat < 0) or np.any(x_hat >= Q)):
                raise ValueError("decoder x_hat must be an integer GF(32) vector of length 128")
            x_hat = x_hat.astype(np.uint8, copy=True)
            iterations = int(raw.iterations)
            runtime_s = float(raw.runtime_s)
            if not 0 <= iterations <= MAX_ITER or not math.isfinite(runtime_s) or runtime_s < 0.0:
                raise ValueError("decoder iterations/runtime are outside the frozen range")
            syndrome_valid = bool(np.array_equal(
                np.asarray(layout.gf32_syndrome(pair["H"], x_hat), dtype=np.int64).ravel(),
                np.asarray(pair["syndrome"], dtype=np.int64)))
            reported = getattr(raw, "syndrome_ok", None)
            raw_vectors.append(x_hat)
            physical_iterations += iterations
            exact = bool(syndrome_valid and np.array_equal(x_hat, pair["truth"]))
            row.update({
                "status": "COMPLETE", "decoder_status": str(raw.status),
                "iterations": iterations, "decoder_runtime_s": runtime_s,
                "syndrome_valid": syndrome_valid,
                "syndrome_ok_reported": None if reported is None else bool(reported),
                "exact": exact,
                "syndrome_valid_wrong": bool(syndrome_valid and not exact),
                "syndrome_failed": not syndrome_valid,
                "raw_vector_index": len(raw_vectors) - 1, "belief_provenance": str(
                    getattr(raw, "belief_provenance", "") or ""),
                "x_hat": x_hat, "_raw_result": raw,
            })
            if selected_variable >= 0:
                row["returned_selected_symbol"] = int(x_hat[selected_variable])
            row["wall_s"] = max(float(now()) - call_started, 0.0)
            current_rss = rss_fn()
            row["rss_bytes"] = None if current_rss is None else int(current_rss)
            if row["rss_bytes"] is not None:
                peak_rss = row["rss_bytes"] if peak_rss is None else max(peak_rss, row["rss_bytes"])
            mismatch = reported is not None and bool(reported) != syndrome_valid
            if mismatch:
                row["status"] = "STOP"
                row["failure_reason"] = "decoder_syndrome_flag_mismatch"
                stop("STOP", "decoder_syndrome_flag_mismatch", "integrity")
            if (mechanism == "jointtop3"
                    and physical_iterations > JOINTTOP3_MAX_PHYSICAL_ITERATIONS):
                reason = (f"physical_iteration_cap_overshoot:{physical_iterations}-"
                          f"{JOINTTOP3_MAX_PHYSICAL_ITERATIONS}")
                resources.append(f"after_decoder_call:{reason}")
                stop("INCOMPLETE", reason, "resource")
            after = check_resources("after_decoder_call", after_call=True)
            if after:
                if not mismatch:
                    row["status"] = "RESOURCE_STOP_AFTER_RETURN"
                    row["failure_reason"] = ";".join(after)
                stop("INCOMPLETE", ";".join(after), "resource")
            return row
        except Exception as exc:
            row["status"] = "CALL_EXCEPTION"
            row["failure_reason"] = f"{type(exc).__name__}:{exc}"
            row["wall_s"] = max(float(now()) - call_started, 0.0)
            current_rss = rss_fn()
            row["rss_bytes"] = None if current_rss is None else int(current_rss)
            if row["rss_bytes"] is not None:
                peak_rss = row["rss_bytes"] if peak_rss is None else max(peak_rss, row["rss_bytes"])
            stop("STOP", "decoder_call_failed", "integrity")
            over = check_resources("after_failed_decoder_call", after_call=True)
            if over:
                stop("INCOMPLETE", ";".join(over), "resource")
            return row

    def branch_prior(selected_variable: int, guess: int, kind: str) -> tuple[np.ndarray, np.ndarray]:
        prior = original_prior.copy()
        if kind == "one_hot":
            override = np.zeros(Q, dtype=np.float64)
            override[int(guess)] = 1.0
        elif kind == "mixed05":
            override = (1.0 - LAMBDA_MIXED) * original_prior[int(selected_variable)]
            override = override.copy()
            override[int(guess)] += LAMBDA_MIXED
        else:
            raise ValueError(f"unknown branch prior kind {kind}")
        prior[int(selected_variable)] = override
        return prior, override.copy()

    def jointtop2_prior(
            selected_variable: int, guess: int,
            secondary_variable: int, secondary_guess: int,
            ) -> tuple[np.ndarray, np.ndarray]:
        if int(selected_variable) == int(secondary_variable):
            raise ValueError("jointtop2 requires distinct selected variables")
        prior = original_prior.copy()
        primary_override = np.zeros(Q, dtype=np.float64)
        primary_override[int(guess)] = 1.0
        secondary_override = np.zeros(Q, dtype=np.float64)
        secondary_override[int(secondary_guess)] = 1.0
        prior[int(selected_variable)] = primary_override
        prior[int(secondary_variable)] = secondary_override
        return prior, primary_override.copy()

    def score_branches(pair: dict[str, Any], output: list[dict[str, Any]],
                       method: str) -> int | None:
        selected_call, score_rows = rescue.select_soft_prior_branch(output, original_prior)
        by_index = {int(row["branch_index"]): row for row in output}
        for score in score_rows:
            by_index[int(score["branch_index"])]["score_original_prior"] = score["score"]
        if selected_call is not None:
            by_call = {int(row["call_index"]): row for row in output}
            pair[f"{method}_branch_selected_call_index"] = int(selected_call)
            pair[f"{method}_branch_selected_call"] = by_call[int(selected_call)]
        return selected_call

    def run_branches(pair: dict[str, Any], *, role: str, method: str,
                     selected_variable: int, metadata: Mapping[str, Any],
                     prior_kind: str) -> tuple[list[dict[str, Any]], bool]:
        output: list[dict[str, Any]] = []
        order = list(enumerate(GUESSES))
        for branch_index, guess in order:
            if run_status != "RUNNING":
                return output, False
            prior, override = branch_prior(selected_variable, guess, prior_kind)
            prior_profile = "one_hot" if prior_kind == "one_hot" else "raw_prior_mix_lambda_0.5"
            result = make_call(
                pair, role=role, method=method, prior=prior,
                branch_index=branch_index, guess_symbol=guess,
                selected_variable=selected_variable, prior_profile=prior_profile,
                prior_lambda=(0.5 if prior_kind == "mixed05" else math.nan),
                prior_override=override, selector_metadata=metadata)
            if result is None or run_status != "RUNNING" or result["status"] != "COMPLETE":
                return output, False
            output.append(result)
        score_branches(pair, output, method)
        return output, True

    def run_top3_arm(
            pair: dict[str, Any], *, method: str,
            selected_variable: int, beliefs: np.ndarray,
            metadata: Mapping[str, Any],
            ) -> tuple[list[dict[str, Any]], bool]:
        """Run one independent arm; candidate ranking through blind choice is timed."""
        arm_started = float(now())
        output: list[dict[str, Any]] = []
        call_indices: list[int] = []
        try:
            if method == "control":
                branch_plan = [(-1, GUESSES.index(guess), int(guess))
                               for guess in GUESSES]
                role, call_method = "top3_control", "top3ctrl"
            else:
                branch_plan = build_top3_branch_plan(beliefs, selected_variable)
                role, call_method = "top3_candidate", "top3cand"
                pair["posterior_ranked_guesses"] = [
                    int(symbol) for _, _, symbol in branch_plan]
                pair["candidate_top3_guesses"] = [
                    int(symbol) for _, _, symbol in branch_plan]
            for posterior_rank, canonical_index, guess in branch_plan:
                if run_status != "RUNNING":
                    return output, False
                prior, override = branch_prior(selected_variable, guess, "one_hot")
                row = make_call(
                    pair, role=role, method=call_method, prior=prior,
                    branch_index=canonical_index, guess_symbol=guess,
                    selected_variable=selected_variable,
                    posterior_rank=posterior_rank,
                    prior_profile="one_hot", prior_override=override,
                    selector_metadata=metadata)
                if row is not None:
                    call_indices.append(int(row["call_index"]))
                    output.append(row)
                    pair[f"{method}_branch_call_indices"] = list(call_indices)
                    if not bool(pair.get("top3_attempted")):
                        pair["top3_attempted"] = True
                        summary["baseline_failures_branched"] += 1
                if (row is None or run_status != "RUNNING"
                        or row["status"] != "COMPLETE"):
                    return output, False
            selected_call = score_branches(pair, output, method)
            pair[f"{method}_selected_call_index"] = (
                int(pair["baseline_call_index"]) if selected_call is None
                else int(selected_call))
            pair[f"{method}_branch_calls"] = len(output)
            return output, True
        finally:
            pair[f"{method}_arm_wall_s"] = max(float(now()) - arm_started, 0.0)

    def run_mixed_pair(pair: dict[str, Any], *, selected_variable: int,
                       metadata: Mapping[str, Any]
                       ) -> tuple[dict[str, list[dict[str, Any]]], bool]:
        branch_sets: dict[str, list[dict[str, Any]]] = {"control": [], "candidate": []}
        order = (("control", "candidate") if int(pair["frame_index"]) % 2 == 0
                 else ("candidate", "control"))
        pair["arm_order"] = ("onehot_then_mixed05_per_guess" if order[0] == "control"
                              else "mixed05_then_onehot_per_guess")
        for branch_index, guess in enumerate(GUESSES):
            for method in order:
                role = "onehot_control" if method == "control" else "mixed05_candidate"
                prior_kind = "one_hot" if method == "control" else "mixed05"
                prior, override = branch_prior(selected_variable, guess, prior_kind)
                row = make_call(
                    pair, role=role, method=method, prior=prior,
                    branch_index=branch_index, guess_symbol=guess,
                    selected_variable=selected_variable,
                    prior_profile=("one_hot" if prior_kind == "one_hot"
                                   else "raw_prior_mix_lambda_0.5"),
                    prior_lambda=(math.nan if prior_kind == "one_hot" else LAMBDA_MIXED),
                    prior_override=override, selector_metadata=metadata)
                if row is None or run_status != "RUNNING" or row["status"] != "COMPLETE":
                    return branch_sets, False
                branch_sets[method].append(row)
        score_branches(pair, branch_sets["control"], "control")
        score_branches(pair, branch_sets["candidate"], "candidate")
        return branch_sets, True

    def run_jointtop2(
            pair: dict[str, Any], *, selected_variable: int,
            secondary_variable: int, beliefs: np.ndarray,
            metadata: Mapping[str, Any],
            ) -> tuple[list[dict[str, Any]], bool]:
        primary_guesses, _ = cost_profile.rank_allowed_guesses(
            beliefs, selected_variable)
        secondary_guesses, _ = cost_profile.rank_allowed_guesses(
            beliefs, secondary_variable)
        primary_top2 = primary_guesses[:2]
        secondary_top2 = secondary_guesses[:2]
        output: list[dict[str, Any]] = []
        branch_index = 0
        for primary_guess in primary_top2:
            for secondary_guess in secondary_top2:
                if run_status != "RUNNING":
                    return output, False
                prior, primary_override = jointtop2_prior(
                    selected_variable, primary_guess,
                    secondary_variable, secondary_guess)
                result = make_call(
                    pair, role="jointtop2_candidate", method="jointtop2",
                    prior=prior, branch_index=branch_index,
                    guess_symbol=primary_guess, selected_variable=selected_variable,
                    secondary_variable=secondary_variable,
                    secondary_guess_symbol=secondary_guess,
                    prior_profile="joint_two_variable_one_hot",
                    prior_override=primary_override, selector_metadata=metadata)
                if (result is None or run_status != "RUNNING"
                        or result["status"] != "COMPLETE"):
                    return output, False
                output.append(result)
                branch_index += 1
        score_branches(pair, output, "candidate")
        return output, True

    def run_jointtop3(
            pair: dict[str, Any], *, selected_variable: int,
            secondary_variable: int, beliefs: np.ndarray,
            metadata: Mapping[str, Any],
            ) -> tuple[list[dict[str, Any]], bool]:
        primary_guesses, _ = cost_profile.rank_allowed_guesses(
            beliefs, selected_variable)
        secondary_guesses, _ = cost_profile.rank_allowed_guesses(
            beliefs, secondary_variable)
        primary_top3 = [int(value) for value in primary_guesses[:3]]
        secondary_top3 = [int(value) for value in secondary_guesses[:3]]
        pair["jointtop3_primary_guesses"] = list(primary_top3)
        pair["jointtop3_secondary_guesses"] = list(secondary_top3)
        pair["jointtop3_attempted"] = True
        output: list[dict[str, Any]] = []
        for branch_index, primary_guess, secondary_guess in build_jointtop3_branch_plan(
                primary_top3, secondary_top3):
            if run_status != "RUNNING":
                return output, False
            prior, primary_override = jointtop2_prior(
                selected_variable, primary_guess,
                secondary_variable, secondary_guess)
            result = make_call(
                pair, role="jointtop3_candidate", method="jointtop3",
                prior=prior, branch_index=branch_index,
                guess_symbol=primary_guess, selected_variable=selected_variable,
                secondary_variable=secondary_variable,
                secondary_guess_symbol=secondary_guess,
                prior_profile="joint_two_variable_one_hot",
                prior_override=primary_override, selector_metadata=metadata)
            if result is None:
                return output, False
            output.append(result)
            pair["jointtop3_call_indices"].append(int(result["call_index"]))
            if branch_index in JOINTTOP3_J2_SUBSET:
                pair["derived_j2_call_indices"].append(int(result["call_index"]))
            if run_status != "RUNNING" or result["status"] != "COMPLETE":
                return output, False
        score_branches(pair, output, "candidate")
        j2_output = [row for row in output
                     if int(row["branch_index"]) in JOINTTOP3_J2_SUBSET]
        score_branches(pair, j2_output, "derived_j2")
        return output, True

    def run_jointcheck2_set(
            pair: dict[str, Any], *, role: str, score_method: str,
            primary_variable: int, secondary_variable: int,
            beliefs: np.ndarray, metadata: Mapping[str, Any],
            ) -> tuple[list[dict[str, Any]], bool]:
        primary_guesses, _ = cost_profile.rank_allowed_guesses(
            beliefs, primary_variable)
        secondary_guesses, _ = cost_profile.rank_allowed_guesses(
            beliefs, secondary_variable)
        output: list[dict[str, Any]] = []
        for branch_index, primary_guess, secondary_guess in build_joint_branch_plan(
                primary_guesses, secondary_guesses):
            if run_status != "RUNNING":
                return output, False
            prior, primary_override = jointtop2_prior(
                primary_variable, primary_guess,
                secondary_variable, secondary_guess)
            result = make_call(
                pair, role=role, method="jointcheck2", prior=prior,
                branch_index=branch_index, guess_symbol=primary_guess,
                selected_variable=primary_variable,
                secondary_variable=secondary_variable,
                secondary_guess_symbol=secondary_guess,
                prior_profile="joint_two_variable_one_hot",
                prior_override=primary_override, selector_metadata=metadata)
            if (result is None or run_status != "RUNNING"
                    or result["status"] != "COMPLETE"):
                return output, False
            output.append(result)
        score_branches(pair, output, score_method)
        pair[f"{score_method}_joint_call_indices"] = [
            int(row["call_index"]) for row in output]
        return output, True

    def run_jointcheck2(
            pair: dict[str, Any], *, control_variables: tuple[int, int],
            candidate_variables: tuple[int, int], beliefs: np.ndarray,
            metadata: Mapping[str, Any],
            ) -> bool:
        control_calls: list[dict[str, Any]] = []
        candidate_calls: list[dict[str, Any]] = []
        if control_variables == candidate_variables:
            pair["joint_pair_shared"] = True
            pair["joint_pair_order"] = "shared_single_set"
            shared_calls, complete = run_jointcheck2_set(
                pair, role="jointcheck2_shared", score_method="control",
                primary_variable=control_variables[0],
                secondary_variable=control_variables[1],
                beliefs=beliefs, metadata=metadata)
            if not complete:
                return False
            selected = score_branches(pair, shared_calls, "candidate")
            pair["candidate_joint_call_indices"] = [
                int(row["call_index"]) for row in shared_calls]
            if selected is not None:
                pair["candidate_branch_selected_call_index"] = int(selected)
                by_call = {int(row["call_index"]): row for row in shared_calls}
                pair["candidate_branch_selected_call"] = by_call[int(selected)]
            control_calls = shared_calls
            candidate_calls = shared_calls
        else:
            pair["joint_pair_shared"] = False
            order = (("control", "candidate") if int(pair["frame_index"]) % 2 == 0
                     else ("candidate", "control"))
            pair["joint_pair_order"] = f"{order[0]}_then_{order[1]}"
            variables = {"control": control_variables,
                         "candidate": candidate_variables}
            results: dict[str, list[dict[str, Any]]] = {}
            for method in order:
                role = ("jointcheck2_control" if method == "control"
                        else "jointcheck2_candidate")
                branch_calls, complete = run_jointcheck2_set(
                    pair, role=role, score_method=method,
                    primary_variable=variables[method][0],
                    secondary_variable=variables[method][1],
                    beliefs=beliefs, metadata=metadata)
                if not complete:
                    return False
                results[method] = branch_calls
            control_calls = results["control"]
            candidate_calls = results["candidate"]
        pair["control_joint_branch_calls"] = len(control_calls)
        pair["candidate_joint_branch_calls"] = len(candidate_calls)
        return True

    try:
        plan, exclusions = validate_seed_plan(mechanism)
        summary["prior_exclusion_plan_count"] = len(exclusions)
        summary["prior_exclusion_rows"] = sum(int(row["rows"]) for row in exclusions)
    except Exception as exc:
        stop("STOP", f"seed_plan:{type(exc).__name__}:{exc}", "authorization")

    if run_status == "RUNNING":
        try:
            source_identity, selected_sources = rescue.select_sources(source_reader())
        except Exception as exc:
            stop("STOP", f"source:{type(exc).__name__}:{exc}", "data")
    if run_status == "RUNNING":
        over = check_resources("after_source_load")
        if over:
            stop("INCOMPLETE", ";".join(over), "resource")

    source_by_graph = {int(row["graph_id"]): row for row in selected_sources}
    seed_by_key = {(g, s, f): seed for g, s, f, seed in plan}
    for graph_id in GRAPH_IDS:
        for stream in HOLDOUT_STREAMS:
            for frame in range(HOLDOUT_FRAMES_PER_STREAM):
                if run_status != "RUNNING":
                    break
                if (mechanism == "jointtop3"
                        and physical_iterations >= JOINTTOP3_MAX_PHYSICAL_ITERATIONS):
                    resources.append("before_sample:physical_iteration_cap")
                    stop("INCOMPLETE", "physical_iteration_cap", "resource")
                    break
                before_sample = check_resources("before_sample")
                if before_sample:
                    stop("INCOMPLETE", ";".join(before_sample), "resource")
                    break
                graph = source_by_graph[graph_id]
                pair: dict[str, Any] = {
                    "pair_index": len(pairs), "frame_index": len(pairs), "graph_id": graph_id,
                    "graph_seed": graph_id, "stream": stream, "frame": frame,
                    "seed": int(seed_by_key[(graph_id, stream, frame)]),
                    "truth": None, "syndrome": None, "H": graph["H"],
                    "completed": False, "baseline_call_index": -1,
                    "control_selected_call_index": -1,
                    "candidate_selected_call_index": -1,
                    "rank1_variable": -1, "rank2_variable": -1,
                    "rank2_attempted": False, "rank2_reason": "not_applicable",
                    "arm_order": (
                        "rank1_then_conditional_rank2" if mechanism == "rank2" else
                        "rank1_then_conditional_jointtop2" if mechanism == "jointtop2" else
                        "rank1_then_conditional_jointcheck2" if mechanism == "jointcheck2" else ""),
                    "selector_metadata": None, "baseline_beliefs": None,
                }
                if mechanism == "jointtop3":
                    pair.update({
                        "arm_order": "shared_baseline_then_rank1_then_conditional_jointtop3",
                        "jointtop3_attempted": False,
                        "jointtop3_primary_guesses": [],
                        "jointtop3_secondary_guesses": [],
                        "jointtop3_call_indices": [],
                        "derived_j2_call_indices": [],
                        "derived_j2_selected_call_index": -1,
                        "derived_j2_selected_branch_index": -1,
                        "j3_selected_branch_index": -1,
                    })
                if mechanism == "top3runtime":
                    pair.update({
                        "top3_attempted": False,
                        "top3_selector_status": "pending",
                        "posterior_ranked_guesses": [],
                        "candidate_top3_guesses": [],
                        "control_branch_call_indices": [],
                        "candidate_branch_call_indices": [],
                        "baseline_wall_s": None,
                        "common_selector_wall_s": 0.0,
                        "control_arm_wall_s": 0.0,
                        "candidate_arm_wall_s": 0.0,
                    })
                if mechanism == "jointcheck2":
                    pair.update({
                        "control_primary_variable": -1,
                        "control_secondary_variable": -1,
                        "candidate_primary_variable": -1,
                        "candidate_secondary_variable": -1,
                        "joint_pair_shared": False,
                        "joint_pair_order": "not_triggered",
                        "control_joint_call_indices": [],
                        "candidate_joint_call_indices": [],
                        "control_joint_branch_calls": 0,
                        "candidate_joint_branch_calls": 0,
                        "jointcheck2_attempted": False,
                        "selector_violated_neighbor_counts": {},
                    })
                pairs.append(pair)
                try:
                    truth = np.asarray(sampler(pair["seed"], original_pmf.copy(), width=N))
                    if (truth.shape != (N,) or not np.issubdtype(truth.dtype, np.integer)
                            or np.any(truth < 0) or np.any(truth >= Q)):
                        raise ValueError("sampler must return an integer GF(32) vector of length 128")
                    truth = truth.astype(np.uint8, copy=True)
                    syndrome = np.asarray(layout.gf32_syndrome(graph["H"], truth), dtype=np.uint8).ravel()
                    if syndrome.shape != (M,):
                        raise ValueError("sampled truth produced an invalid 52-check syndrome")
                    pair["truth"], pair["syndrome"] = truth, syndrome
                except Exception as exc:
                    stop("STOP", f"sampler:{type(exc).__name__}:{exc}", "data")
                    break
                baseline = make_call(pair, role="baseline", method="shared",
                                     prior=original_prior)
                if baseline is None or run_status != "RUNNING" or baseline["status"] != "COMPLETE":
                    break
                pair["baseline_call_index"] = baseline["call_index"]
                if mechanism == "top3runtime":
                    pair["baseline_wall_s"] = float(baseline["wall_s"] or 0.0)
                    summary["baseline_failures"] += int(not baseline["syndrome_valid"])
                baseline_exact = bool(baseline["syndrome_valid"] and np.array_equal(baseline["x_hat"], truth))
                baseline.update({
                    "exact": baseline_exact,
                    "syndrome_valid_wrong": bool(baseline["syndrome_valid"] and not baseline_exact),
                    "syndrome_failed": not bool(baseline["syndrome_valid"]),
                })
                if baseline["syndrome_valid"]:
                    if mechanism == "top3runtime":
                        pair["top3_selector_status"] = "not_needed_baseline_valid"
                    pair.update({
                        "control_selected_call_index": baseline["call_index"],
                        "candidate_selected_call_index": baseline["call_index"],
                        "control_exact": baseline_exact, "candidate_exact": baseline_exact,
                        "control_valid_wrong": not baseline_exact,
                        "candidate_valid_wrong": not baseline_exact,
                        "control_syndrome_failed": False,
                        "candidate_syndrome_failed": False,
                        "control_branch_calls": 0, "candidate_incremental_branch_calls": 0,
                        "completed": True,
                    })
                    if mechanism == "jointtop3":
                        pair.update({
                            "derived_j2_selected_call_index": int(baseline["call_index"]),
                            "derived_j2_selected_branch_index": -1,
                            "derived_j2_exact": baseline_exact,
                            "derived_j2_valid_wrong": not baseline_exact,
                            "derived_j2_syndrome_failed": False,
                        })
                    baseline["selected_for_control"] = True
                    baseline["selected_for_candidate"] = True
                    if mechanism == "jointtop3":
                        baseline["selected_for_derived_j2"] = True
                    summary["completed_pairs"] += 1
                    continue

                raw = baseline.get("_raw_result")
                selector_started = float(now()) if mechanism == "top3runtime" else None
                try:
                    beliefs = np.asarray(getattr(raw, "final_beliefs", None), dtype=np.float64)
                    provenance = getattr(raw, "belief_provenance", None)
                    rank1, metadata = rescue.select_uncertain_variable(
                        pair["H"], baseline["x_hat"], beliefs, syndrome,
                        belief_provenance=provenance)
                    rank2 = (select_rank2_variable(metadata, rank1)
                             if mechanism in ("rank2", "jointtop3") else None)
                    if mechanism == "jointcheck2":
                        control_secondary = select_rank2_variable(metadata, rank1)
                        candidate_primary, candidate_secondary, counts = (
                            select_jointcheck2_variables(pair["H"], metadata))
                        metadata = dict(metadata)
                        metadata["violated_neighbor_counts"] = counts
                        pair.update({
                            "control_primary_variable": int(rank1),
                            "control_secondary_variable": (
                                -1 if control_secondary is None else int(control_secondary)),
                            "candidate_primary_variable": (
                                -1 if candidate_primary is None else int(candidate_primary)),
                            "candidate_secondary_variable": (
                                -1 if candidate_secondary is None else int(candidate_secondary)),
                            "selector_violated_neighbor_counts": counts,
                        })
                    pair["rank1_variable"] = rank1
                    pair["rank2_variable"] = -1 if rank2 is None else rank2
                    pair["selected_variable"] = rank1
                    pair["selector_metadata"] = metadata
                    pair["baseline_beliefs"] = beliefs.copy()
                    baseline["selector_active_variable_columns_json"] = json.dumps(
                        metadata["active_variable_columns"])
                    baseline["selector_violated_check_ids_json"] = json.dumps(
                        metadata["violated_check_ids"])
                    baseline["selector_entropy_bits_json"] = json.dumps(metadata["entropy_bits"])
                    if mechanism == "jointcheck2":
                        baseline["selector_violated_neighbor_counts_json"] = json.dumps(
                            metadata["violated_neighbor_counts"], separators=(",", ":"))
                    if mechanism == "top3runtime":
                        pair["top3_selector_status"] = "active"
                        pair["common_selector_wall_s"] = max(
                            float(now()) - float(selector_started), 0.0)
                except Exception as exc:
                    if (mechanism == "top3runtime"
                            and isinstance(exc, ValueError)
                            and str(exc) == "baseline failure has no variables adjacent to violated checks"):
                        observed = np.asarray(layout.gf32_syndrome(
                            pair["H"], baseline["x_hat"]), dtype=np.int64).ravel()
                        violated = np.flatnonzero(observed != np.asarray(syndrome, dtype=np.int64))
                        pair.update({
                            "top3_selector_status": "no_active",
                            "common_selector_wall_s": max(
                                float(now()) - float(selector_started), 0.0),
                            "baseline_beliefs": beliefs.copy(),
                            "selector_metadata": {
                                "active_variable_columns": [],
                                "violated_check_ids": [int(x) for x in violated],
                                "entropy_bits": [],
                            },
                            "control_selected_call_index": int(baseline["call_index"]),
                            "candidate_selected_call_index": int(baseline["call_index"]),
                            "control_branch_calls": 0,
                            "candidate_incremental_branch_calls": 0,
                            "control_exact": False, "candidate_exact": False,
                            "control_valid_wrong": False, "candidate_valid_wrong": False,
                            "control_syndrome_failed": True,
                            "candidate_syndrome_failed": True,
                            "completed": True,
                        })
                        summary["no_active_frames"] += 1
                        baseline["selected_for_control"] = True
                        baseline["selected_for_candidate"] = True
                        summary["completed_pairs"] += 1
                        continue
                    stop("STOP", f"baseline_beliefs:{type(exc).__name__}:{exc}", "integrity")
                    break

                if mechanism == "top3runtime":
                    order = (("control", "candidate")
                             if int(pair["frame_index"]) % 2 == 0
                             else ("candidate", "control"))
                    pair["arm_order"] = f"{order[0]}_then_{order[1]}"
                    pair["top3_selector_status"] = "active"
                    arm_complete = True
                    for method in order:
                        _, arm_complete = run_top3_arm(
                            pair, method=method, selected_variable=rank1,
                            beliefs=beliefs, metadata=metadata)
                        if not arm_complete:
                            break
                    if not arm_complete:
                        break
                    pair["control_selected_call_index"] = int(
                        pair["control_selected_call_index"])
                    pair["candidate_selected_call_index"] = int(
                        pair["candidate_selected_call_index"])
                    pair["control_branch_calls"] = int(pair.get("control_branch_calls", 0))
                    pair["candidate_incremental_branch_calls"] = int(
                        pair.get("candidate_branch_calls", 0))
                elif mechanism == "rank2":
                    pair["rank2_reason"] = "not_triggered_rank1_has_valid_branch"
                    rank1_calls, rank1_complete = run_branches(
                        pair, role="rank1_onehot", method="rank1",
                        selected_variable=rank1, metadata=metadata, prior_kind="one_hot")
                    if not rank1_complete:
                        break
                    rank1_selected = pair.get("rank1_branch_selected_call_index")
                    control_choice = baseline["call_index"] if rank1_selected is None else rank1_selected
                    candidate_choice = control_choice
                    pair["control_branch_calls"] = len(rank1_calls)
                    pair["candidate_incremental_branch_calls"] = 0
                    if rank1_selected is None:
                        pair["rank2_attempted"] = True
                        if rank2 is None:
                            pair["rank2_reason"] = "triggered_no_second_active_variable"
                        else:
                            pair["rank2_reason"] = "triggered_all_rank1_branches_syndrome_invalid"
                            rank2_calls, rank2_complete = run_branches(
                                pair, role="rank2_onehot", method="rank2",
                                selected_variable=rank2, metadata=metadata, prior_kind="one_hot")
                            if not rank2_complete:
                                break
                            pair["candidate_incremental_branch_calls"] = len(rank2_calls)
                            rank2_selected = pair.get("rank2_branch_selected_call_index")
                            if rank2_selected is not None:
                                candidate_choice = rank2_selected
                                pair["rank2_reason"] = "rank2_valid_branch_selected"
                            else:
                                pair["rank2_reason"] = "all_rank2_branches_syndrome_invalid_baseline_fallback"
                    pair["control_selected_call_index"] = control_choice
                    pair["candidate_selected_call_index"] = candidate_choice
                elif mechanism == "jointtop2":
                    pair["rank2_reason"] = "not_triggered_rank1_has_valid_branch"
                    rank1_calls, rank1_complete = run_branches(
                        pair, role="rank1_onehot", method="rank1",
                        selected_variable=rank1, metadata=metadata, prior_kind="one_hot")
                    if not rank1_complete:
                        break
                    rank1_selected = pair.get("rank1_branch_selected_call_index")
                    control_choice = baseline["call_index"] if rank1_selected is None else rank1_selected
                    candidate_choice = control_choice
                    pair["control_branch_calls"] = len(rank1_calls)
                    pair["candidate_incremental_branch_calls"] = 0
                    if rank1_selected is None:
                        pair["rank2_attempted"] = True
                        rank2 = select_rank2_variable(metadata, rank1)
                        pair["rank2_variable"] = -1 if rank2 is None else rank2
                        if rank2 is None:
                            pair["rank2_reason"] = "triggered_no_second_active_variable"
                        else:
                            pair["rank2_reason"] = "triggered_jointtop2_branches"
                            joint_calls, joint_complete = run_jointtop2(
                                pair, selected_variable=rank1,
                                secondary_variable=rank2, beliefs=beliefs,
                                metadata=metadata)
                            if not joint_complete:
                                break
                            pair["candidate_incremental_branch_calls"] = len(joint_calls)
                            joint_selected = pair.get("candidate_branch_selected_call_index")
                            if joint_selected is not None:
                                candidate_choice = joint_selected
                                pair["rank2_reason"] = "jointtop2_valid_branch_selected"
                            else:
                                pair["rank2_reason"] = "all_jointtop2_branches_syndrome_invalid_baseline_fallback"
                    pair["control_selected_call_index"] = control_choice
                    pair["candidate_selected_call_index"] = candidate_choice
                elif mechanism == "jointtop3":
                    pair["rank2_reason"] = "not_triggered_rank1_has_valid_branch"
                    rank1_calls, rank1_complete = run_branches(
                        pair, role="rank1_onehot", method="rank1",
                        selected_variable=rank1, metadata=metadata, prior_kind="one_hot")
                    if not rank1_complete:
                        break
                    rank1_selected = pair.get("rank1_branch_selected_call_index")
                    control_choice = (baseline["call_index"] if rank1_selected is None
                                      else int(rank1_selected))
                    j3_choice = control_choice
                    j2_choice = control_choice
                    pair["control_branch_calls"] = len(rank1_calls)
                    pair["candidate_incremental_branch_calls"] = 0
                    if rank1_selected is None:
                        pair["rank2_attempted"] = True
                        if rank2 is None:
                            pair["rank2_reason"] = "triggered_no_second_active_variable"
                        else:
                            pair["rank2_reason"] = "triggered_all_rank1_branches_syndrome_invalid"
                            joint_calls, joint_complete = run_jointtop3(
                                pair, selected_variable=rank1,
                                secondary_variable=rank2, beliefs=beliefs,
                                metadata=metadata)
                            if not joint_complete:
                                break
                            pair["candidate_incremental_branch_calls"] = len(joint_calls)
                            j3_selected = pair.get("candidate_branch_selected_call_index")
                            j2_selected = pair.get("derived_j2_branch_selected_call_index")
                            j3_choice = (baseline["call_index"] if j3_selected is None
                                         else int(j3_selected))
                            j2_choice = (baseline["call_index"] if j2_selected is None
                                         else int(j2_selected))
                            if j3_selected is not None:
                                pair["j3_selected_branch_index"] = int(
                                    calls[int(j3_selected)]["branch_index"])
                            if j2_selected is not None:
                                pair["derived_j2_selected_branch_index"] = int(
                                    calls[int(j2_selected)]["branch_index"])
                            pair["rank2_reason"] = (
                                "jointtop3_valid_branch_selected" if j3_selected is not None else
                                "all_jointtop3_branches_syndrome_invalid_baseline_fallback")
                    pair["control_selected_call_index"] = int(control_choice)
                    pair["candidate_selected_call_index"] = int(j3_choice)
                    pair["derived_j2_selected_call_index"] = int(j2_choice)
                elif mechanism == "jointcheck2":
                    pair["rank2_reason"] = "not_triggered_rank1_has_valid_branch"
                    rank1_calls, rank1_complete = run_branches(
                        pair, role="rank1_onehot", method="rank1",
                        selected_variable=rank1, metadata=metadata, prior_kind="one_hot")
                    if not rank1_complete:
                        break
                    rank1_selected = pair.get("rank1_branch_selected_call_index")
                    pair["control_branch_calls"] = len(rank1_calls)
                    pair["candidate_incremental_branch_calls"] = 0
                    if rank1_selected is None:
                        pair["rank2_attempted"] = True
                        control_secondary = int(pair["control_secondary_variable"])
                        candidate_primary = int(pair["candidate_primary_variable"])
                        candidate_secondary = int(pair["candidate_secondary_variable"])
                        if (control_secondary < 0 or candidate_primary < 0
                                or candidate_secondary < 0):
                            pair["rank2_reason"] = "triggered_no_second_active_variable"
                            control_choice = baseline["call_index"]
                            candidate_choice = baseline["call_index"]
                        else:
                            pair["rank2_reason"] = "triggered_jointcheck2_branches"
                            pair["jointcheck2_attempted"] = True
                            complete = run_jointcheck2(
                                pair,
                                control_variables=(int(rank1), control_secondary),
                                candidate_variables=(candidate_primary, candidate_secondary),
                                beliefs=beliefs, metadata=metadata)
                            if not complete:
                                break
                            control_joint_selected = pair.get(
                                "control_branch_selected_call_index")
                            candidate_joint_selected = pair.get(
                                "candidate_branch_selected_call_index")
                            control_choice = (baseline["call_index"]
                                              if control_joint_selected is None
                                              else int(control_joint_selected))
                            candidate_choice = (baseline["call_index"]
                                                if candidate_joint_selected is None
                                                else int(candidate_joint_selected))
                            pair["candidate_incremental_branch_calls"] = 4
                            pair["rank2_reason"] = (
                                "jointcheck2_valid_branch_selected"
                                if candidate_joint_selected is not None else
                                "all_jointcheck2_candidate_branches_syndrome_invalid_baseline_fallback")
                    else:
                        control_choice = int(rank1_selected)
                        candidate_choice = int(rank1_selected)
                    pair["control_selected_call_index"] = int(control_choice)
                    pair["candidate_selected_call_index"] = int(candidate_choice)
                else:
                    pair["rank2_reason"] = "not_applicable_mixed05"
                    branch_sets, all_complete = run_mixed_pair(
                        pair, selected_variable=rank1, metadata=metadata)
                    if not all_complete:
                        break
                    control_selected = pair.get("control_branch_selected_call_index")
                    candidate_selected = pair.get("candidate_branch_selected_call_index")
                    pair["control_selected_call_index"] = baseline["call_index"] if control_selected is None else control_selected
                    pair["candidate_selected_call_index"] = baseline["call_index"] if candidate_selected is None else candidate_selected
                    pair["control_branch_calls"] = len(branch_sets["control"])
                    pair["candidate_incremental_branch_calls"] = len(branch_sets["candidate"])

                control_call = calls[int(pair["control_selected_call_index"])]
                candidate_call = calls[int(pair["candidate_selected_call_index"])]
                control_exact = bool(control_call["syndrome_valid"] and np.array_equal(control_call["x_hat"], truth))
                candidate_exact = bool(candidate_call["syndrome_valid"] and np.array_equal(candidate_call["x_hat"], truth))
                pair.update({
                    "control_exact": control_exact, "candidate_exact": candidate_exact,
                    "control_valid_wrong": bool(control_call["syndrome_valid"] and not control_exact),
                    "candidate_valid_wrong": bool(candidate_call["syndrome_valid"] and not candidate_exact),
                    "control_syndrome_failed": not bool(control_call["syndrome_valid"]),
                    "candidate_syndrome_failed": not bool(candidate_call["syndrome_valid"]),
                    "completed": True,
                })
                control_call["exact"] = control_exact
                control_call["syndrome_valid_wrong"] = pair["control_valid_wrong"]
                control_call["syndrome_failed"] = pair["control_syndrome_failed"]
                candidate_call["exact"] = candidate_exact
                candidate_call["syndrome_valid_wrong"] = pair["candidate_valid_wrong"]
                candidate_call["syndrome_failed"] = pair["candidate_syndrome_failed"]
                control_call["selected_for_control"] = True
                candidate_call["selected_for_candidate"] = True
                if mechanism == "jointtop3":
                    derived_j2_call = calls[int(pair["derived_j2_selected_call_index"])]
                    derived_j2_exact = bool(
                        derived_j2_call["syndrome_valid"]
                        and np.array_equal(derived_j2_call["x_hat"], truth))
                    pair.update({
                        "derived_j2_exact": derived_j2_exact,
                        "derived_j2_valid_wrong": bool(
                            derived_j2_call["syndrome_valid"] and not derived_j2_exact),
                        "derived_j2_syndrome_failed": not bool(
                            derived_j2_call["syndrome_valid"]),
                    })
                    derived_j2_call["selected_for_derived_j2"] = True
                    derived_j2_call["exact"] = derived_j2_exact
                    derived_j2_call["syndrome_valid_wrong"] = pair["derived_j2_valid_wrong"]
                    derived_j2_call["syndrome_failed"] = pair["derived_j2_syndrome_failed"]
                if baseline_exact and (not control_exact or not candidate_exact):
                    stop("STOP", "baseline_valid_passthrough_lost_exact_frame", "integrity")
                    break
                summary["completed_pairs"] += 1
            if run_status != "RUNNING":
                break

    summary["sampled_pairs"] = sum(row.get("truth") is not None for row in pairs)
    summary["attempted_physical_calls"] = len(calls)
    summary["baseline_calls"] = sum(row["role"] == "baseline" for row in calls)
    summary["branch_calls"] = len(calls) - summary["baseline_calls"]
    if mechanism == "rank2":
        summary["logical_control_calls"] = summary["baseline_calls"] + sum(
            row["role"] == "rank1_onehot" for row in calls)
        summary["logical_candidate_calls"] = summary["logical_control_calls"] + sum(
            row["role"] == "rank2_onehot" for row in calls)
    elif mechanism == "jointtop2":
        summary["logical_control_calls"] = summary["baseline_calls"] + sum(
            row["role"] == "rank1_onehot" for row in calls)
        summary["logical_candidate_calls"] = summary["logical_control_calls"] + sum(
            row["role"] == "jointtop2_candidate" for row in calls)
    elif mechanism == "jointtop3":
        shared_prefix_calls = summary["baseline_calls"] + sum(
            row["role"] == "rank1_onehot" for row in calls)
        joint_calls = [row for row in calls if row["role"] == "jointtop3_candidate"]
        summary["logical_control_calls"] = shared_prefix_calls
        summary["logical_candidate_calls"] = shared_prefix_calls + len(joint_calls)
        summary["logical_derived_j2_calls"] = shared_prefix_calls + sum(
            int(row["branch_index"]) in JOINTTOP3_J2_SUBSET for row in joint_calls)
    elif mechanism == "jointcheck2":
        rank1_calls = sum(row["role"] == "rank1_onehot" for row in calls)
        shared_calls = sum(row["role"] == "jointcheck2_shared" for row in calls)
        control_joint_calls = sum(row["role"] == "jointcheck2_control" for row in calls)
        candidate_joint_calls = sum(row["role"] == "jointcheck2_candidate" for row in calls)
        summary["logical_control_calls"] = (
            summary["baseline_calls"] + rank1_calls + shared_calls + control_joint_calls)
        summary["logical_candidate_calls"] = (
            summary["baseline_calls"] + rank1_calls + shared_calls + candidate_joint_calls)
        triggered = [row for row in pairs if bool(row.get("jointcheck2_attempted"))]
        divergent = [row for row in triggered if not bool(row.get("joint_pair_shared"))]
        summary.update({
            "baseline_fail_frames": int(sum(
                calls[int(row["baseline_call_index"])]["syndrome_valid"] is False
                for row in pairs if row.get("truth") is not None
                and int(row.get("baseline_call_index", -1)) >= 0)),
            "jointcheck2_triggered_frames": len(triggered),
            "jointcheck2_distinct_pair_frames": len(divergent),
            "jointcheck2_shared_pair_frames": len(triggered) - len(divergent),
        })
    elif mechanism == "top3runtime":
        control_branch_calls = sum(row["role"] == "top3_control" for row in calls)
        candidate_branch_calls = sum(row["role"] == "top3_candidate" for row in calls)
        summary["logical_control_calls"] = summary["baseline_calls"] + control_branch_calls
        summary["logical_candidate_calls"] = summary["baseline_calls"] + candidate_branch_calls
    else:
        summary["logical_control_calls"] = summary["baseline_calls"] + sum(
            row["role"] == "onehot_control" for row in calls)
        summary["logical_candidate_calls"] = summary["baseline_calls"] + sum(
            row["role"] == "mixed05_candidate" for row in calls)
    summary["physical_decoder_iterations"] = int(sum(row.get("iterations") or 0 for row in calls))
    summary["logical_control_iterations"] = int(sum(
        int(row.get("iterations") or 0) for row in calls
        if row["role"] == "baseline" or row["role"] in ("rank1_onehot", "onehot_control")))
    if mechanism in ("rank2", "jointtop2"):
        summary["logical_candidate_iterations"] = int(sum(
            int(row.get("iterations") or 0) for row in calls
            if row["role"] in (
                "baseline", "rank1_onehot",
                "rank2_onehot" if mechanism == "rank2" else "jointtop2_candidate")))
    elif mechanism == "jointtop3":
        shared_prefix_iterations = sum(
            int(row.get("iterations") or 0) for row in calls
            if row["role"] in ("baseline", "rank1_onehot"))
        joint_calls = [row for row in calls if row["role"] == "jointtop3_candidate"]
        summary["logical_control_iterations"] = int(shared_prefix_iterations)
        summary["logical_candidate_iterations"] = int(
            shared_prefix_iterations + sum(int(row.get("iterations") or 0)
                                           for row in joint_calls))
        summary["logical_derived_j2_iterations"] = int(
            shared_prefix_iterations + sum(
                int(row.get("iterations") or 0) for row in joint_calls
                if int(row["branch_index"]) in JOINTTOP3_J2_SUBSET))
    elif mechanism == "jointcheck2":
        summary["logical_control_iterations"] = int(sum(
            int(row.get("iterations") or 0) for row in calls
            if row["role"] in (
                "baseline", "rank1_onehot", "jointcheck2_control", "jointcheck2_shared")))
        summary["logical_candidate_iterations"] = int(sum(
            int(row.get("iterations") or 0) for row in calls
            if row["role"] in (
                "baseline", "rank1_onehot", "jointcheck2_candidate", "jointcheck2_shared")))
    elif mechanism == "top3runtime":
        summary["logical_control_iterations"] = int(sum(
            int(row.get("iterations") or 0) for row in calls
            if row["role"] in ("baseline", "top3_control")))
        summary["logical_candidate_iterations"] = int(sum(
            int(row.get("iterations") or 0) for row in calls
            if row["role"] in ("baseline", "top3_candidate")))
    else:
        summary["logical_candidate_iterations"] = int(sum(
            int(row.get("iterations") or 0) for row in calls
            if row["role"] in ("baseline", "mixed05_candidate")))
    summary["nominal_edge_iteration_proxy"] = 256 * summary["physical_decoder_iterations"]
    summary["disclosure_bits_physical_batch"] = summary["sampled_pairs"] * SYNDROME_BITS
    if mechanism == "jointtop3":
        logical_disclosure = summary["sampled_pairs"] * SYNDROME_BITS
        summary["disclosure_bits_logical_control"] = logical_disclosure
        summary["disclosure_bits_logical_j3"] = logical_disclosure
        summary["disclosure_bits_logical_derived_j2"] = logical_disclosure
    if mechanism == "top3runtime":
        summary["disclosure_bits_logical_control"] = summary["sampled_pairs"] * SYNDROME_BITS
        summary["disclosure_bits_logical_candidate"] = summary["sampled_pairs"] * SYNDROME_BITS
        summary["internal_branch_disclosure_bits"] = 0
        summary["tag_bits"] = 0
    raw_roles = (
        "baseline", "rank1_onehot", "rank2_onehot", "onehot_control", "mixed05_candidate")
    if mechanism == "jointtop2":
        raw_roles += ("jointtop2_candidate",)
    elif mechanism == "jointcheck2":
        raw_roles += ("jointcheck2_control", "jointcheck2_candidate", "jointcheck2_shared")
    elif mechanism == "top3runtime":
        raw_roles += ("top3_control", "top3_candidate")
    elif mechanism == "jointtop3":
        raw_roles += ("jointtop3_candidate",)
    summary["raw_valid_wrong_by_role"] = {
        role: int(sum(row.get("syndrome_valid") is True and row.get("exact") is False
                      for row in calls if row["role"] == role))
        for role in raw_roles
    }
    if mechanism == "jointcheck2":
        baseline_failures = int(sum(
            row["role"] == "baseline" and row.get("syndrome_valid") is False
            for row in calls))
        triggered_pairs = [row for row in pairs
                           if bool(row.get("jointcheck2_attempted"))]
        distinct_pairs = int(sum(not bool(row.get("joint_pair_shared"))
                                 for row in triggered_pairs))
        expected_physical = (HOLDOUT_PAIRS + 6 * baseline_failures
                             + 4 * len(triggered_pairs) + 4 * distinct_pairs)
        expected_logical = HOLDOUT_PAIRS + 6 * baseline_failures + 4 * len(triggered_pairs)
        summary["jointcheck2_accounting"] = {
            "F_baseline_failures": baseline_failures,
            "G_triggered_frames": len(triggered_pairs),
            "D_distinct_ordered_pairs": distinct_pairs,
            "expected_physical_calls": expected_physical,
            "expected_logical_calls_per_method": expected_logical,
            "max_physical_calls": JOINTCHECK2_MAX_PHYSICAL_CALLS,
            "max_iterations": JOINTCHECK2_MAX_PHYSICAL_CALLS * MAX_ITER,
        }
        if run_status == "RUNNING" and (
                distinct_pairs > len(triggered_pairs)
                or len(triggered_pairs) > baseline_failures
                or len(calls) != expected_physical
                or summary["logical_control_calls"] != expected_logical
                or summary["logical_candidate_calls"] != expected_logical):
            stop("STOP", "jointcheck2_call_identity_mismatch", "integrity")
    elif mechanism == "top3runtime":
        branched = [row for row in pairs if bool(row.get("top3_attempted"))]
        f_branched = len(branched)
        expected_physical = int(summary["sampled_pairs"]) + 9 * f_branched
        expected_logical_control = int(summary["sampled_pairs"]) + 6 * f_branched
        expected_logical_candidate = int(summary["sampled_pairs"]) + 3 * f_branched
        baseline_wall = float(sum(float(row.get("baseline_wall_s") or 0.0) for row in pairs))
        selector_wall = float(sum(float(row.get("common_selector_wall_s") or 0.0)
                                  for row in pairs))
        control_arm_wall = float(sum(float(row.get("control_arm_wall_s") or 0.0)
                                     for row in pairs))
        candidate_arm_wall = float(sum(float(row.get("candidate_arm_wall_s") or 0.0)
                                       for row in pairs))
        control_path = baseline_wall + control_arm_wall
        candidate_path = baseline_wall + candidate_arm_wall
        branch_ratio = (None if control_arm_wall <= 0.0
                        else candidate_arm_wall / control_arm_wall)
        method_path_ratio = (None if control_path <= 0.0
                             else candidate_path / control_path)
        summary["timing"] = {
            "baseline_call_s": baseline_wall,
            "common_selector_s": selector_wall,
            "control_arm_loop_s": control_arm_wall,
            "candidate_arm_loop_s": candidate_arm_wall,
            "branch_loop_ratio": branch_ratio,
            "control_method_path_s": control_path,
            "candidate_method_path_s": candidate_path,
            "method_path_ratio": method_path_ratio,
            "arm_timing_scope": (
                "candidate ranking, one-hot prior construction, actual branch calls, "
                "original-prior blind choice, and in-memory arm record updates; no disk writes"),
            "excluded_common_timing_s": selector_wall,
        }
        summary["top3runtime_accounting"] = {
            "F_baseline_failures": int(summary["baseline_failures"]),
            "F_branched": f_branched,
            "no_active_frames": int(summary["no_active_frames"]),
            "expected_physical_calls": expected_physical,
            "expected_logical_control_calls": expected_logical_control,
            "expected_logical_candidate_calls": expected_logical_candidate,
            "max_physical_calls": TOP3RUNTIME_MAX_PHYSICAL_CALLS,
            "max_iterations": TOP3RUNTIME_MAX_PHYSICAL_CALLS * MAX_ITER,
        }
        if run_status == "RUNNING" and (
                len(calls) != expected_physical
                or summary["logical_control_calls"] != expected_logical_control
                or summary["logical_candidate_calls"] != expected_logical_candidate
                or any(int(row.get("control_branch_calls", 0)) != 6
                       or int(row.get("candidate_branch_calls", 0)) != 3
                       for row in branched)):
            stop("STOP", "top3runtime_call_identity_mismatch", "integrity")
    elif mechanism == "jointtop3":
        baseline_failures = int(sum(
            row["role"] == "baseline" and row.get("syndrome_valid") is False
            for row in calls))
        triggered = [row for row in pairs if bool(row.get("jointtop3_attempted"))]
        expected_physical = (HOLDOUT_PAIRS + 6 * baseline_failures
                             + 9 * len(triggered))
        expected_logical_control = HOLDOUT_PAIRS + 6 * baseline_failures
        expected_logical_j3 = expected_logical_control + 9 * len(triggered)
        expected_logical_j2 = expected_logical_control + 4 * len(triggered)
        summary["jointtop3_accounting"] = {
            "F_baseline_failures": baseline_failures,
            "G_jointtop3_frames": len(triggered),
            "expected_physical_calls": expected_physical,
            "expected_logical_control_calls": expected_logical_control,
            "expected_logical_j3_calls": expected_logical_j3,
            "expected_logical_derived_j2_calls": expected_logical_j2,
            "max_physical_calls": JOINTTOP3_MAX_PHYSICAL_CALLS,
            "max_physical_iterations": JOINTTOP3_MAX_PHYSICAL_ITERATIONS,
            "derived_j2_joint_branch_indices": list(JOINTTOP3_J2_SUBSET),
        }
        jointtop3_identity_ok = True
        for pair in triggered:
            branch_rows = [row for row in calls
                           if int(row["pair_index"]) == int(pair["pair_index"])
                           and row["role"] == "jointtop3_candidate"]
            primary_guesses = [int(value) for value in pair.get("jointtop3_primary_guesses", [])]
            secondary_guesses = [int(value) for value in pair.get("jointtop3_secondary_guesses", [])]
            expected_plan = ([(3 * i + j, primary, secondary)
                              for i, primary in enumerate(primary_guesses)
                              for j, secondary in enumerate(secondary_guesses)]
                             if len(primary_guesses) == 3 and len(secondary_guesses) == 3
                             else [])
            actual_plan = [(int(row["branch_index"]), int(row["guess_symbol"]),
                            int(row["secondary_guess_symbol"])) for row in branch_rows]
            expected_joint_ids = [int(row["call_index"]) for row in branch_rows]
            expected_j2_ids = [int(row["call_index"]) for row in branch_rows
                               if int(row["branch_index"]) in JOINTTOP3_J2_SUBSET]
            if (actual_plan != expected_plan
                    or expected_joint_ids != pair.get("jointtop3_call_indices")
                    or expected_j2_ids != pair.get("derived_j2_call_indices")
                    or any(int(row["selected_variable"]) != int(pair["rank1_variable"])
                           or int(row["secondary_variable"]) != int(pair["rank2_variable"])
                           for row in branch_rows)):
                jointtop3_identity_ok = False
        if run_status == "RUNNING" and (
                len(triggered) > baseline_failures
                or len(calls) != expected_physical
                or summary["logical_control_calls"] != expected_logical_control
                or summary["logical_candidate_calls"] != expected_logical_j3
                or summary["logical_derived_j2_calls"] != expected_logical_j2
                or not jointtop3_identity_ok
                or any(len(row.get("jointtop3_call_indices", [])) != 9
                       or len(row.get("derived_j2_call_indices", [])) != 4
                       for row in triggered)):
            stop("STOP", "jointtop3_call_identity_mismatch", "integrity")
    if run_status == "RUNNING":
        run_status = _run_status_for_pairs(summary, int(summary["completed_pairs"]))
    summary["status"] = run_status
    if run_status == "COMPLETE":
        _full_totals(summary, pairs, calls)
        if mechanism == "jointtop3":
            _jointtop3_full_totals(summary, pairs, calls)
        summary["classification"] = _classification(mechanism, summary)
    else:
        _null_totals(summary, mechanism)
    summary["peak_rss_bytes"] = peak_rss
    summary["stop_reasons"] = stop_reasons

    command_value = command or (
        "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
        "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
        f"comparison_bench.cli.probes_closed.nbldpc_gf32_mechanism_pair --mechanism {mechanism} "
        f"--execute --out-root {profile['out_root'].as_posix()}")
    manifest: dict[str, Any] = {
        "track": "EXPLORE", "mechanism": mechanism,
        "batch_uuid": profile["batch_uuid"], "contract": profile["contract"],
        "claim_ceiling": "Synthetic finite-length mechanism diagnostic only; no FER, f_eff, leakage, SKR, real-data, route-closure, qualification, or publication claim.",
        "seed_namespace": profile["seed_namespace"], "status": summary["status"],
        "classification": summary["classification"], "exact_command": command_value,
        "source_expected": {
            "batch_uuid": rescue.SOURCE_BATCH_UUID,
            "contract": rescue.SOURCE_CONTRACT,
            "seed_namespace": rescue.SOURCE_NAMESPACE,
            "graph_input_kind": rescue.SOURCE_KIND,
        },
        "source_identity": source_identity,
        "source_maps": [_source_map(row) for row in selected_sources],
        "seed_plan": [{"graph_id": g, "stream": s, "frame": f, "seed": seed}
                      for g, s, f, seed in plan],
        "seed_exclusion_generators": exclusions,
        "pmf": original_pmf.tolist(),
        "decoder": {"implementation": "v35.decode_row_layered_fftqspa",
                     "max_iter": MAX_ITER, "damping_alpha": DAMPING_ALPHA,
                     "warm_beliefs": None, "field": None},
        "algorithm": {
            "baseline_validity": "independent GF32 H*x_hat == sampled syndrome",
            "selector": "accepted stable-softmax CHECK_UPDATED entropy on baseline violated-check active variables; 1e-12 ties to lowest column",
            "guesses": list(GUESSES),
            "candidate_score": "sum log(P_eff[i,x_hat_i]) using original effective prior; 1e-12 ties to lowest original branch index",
            "rank2": "only after all six rank1 one-hot outputs fail own syndrome; rank2 is the next active variable by same baseline entropy with rank1 excluded; six independent cold one-hot calls from original prior",
            "mixed05": "same rank1 variable and six guesses; q_g=0.5*raw_original_prior+0.5*one_hot before decoder floor/normalization; no rank2",
            "mixed05_call_order": "frame_index is the global 0..191 pair-plan index; for each ordered guess [0,1,3,7,15,31], even frames call one-hot then mixed, odd frames mixed then one-hot",
            "truth_blind_choice": True,
            "branch_prior_rows_retained": "changed 32-symbol row per call in diagnostics; all other rows equal original_prior",
        },
        "accounting": {
            "physical_calls": summary["attempted_physical_calls"],
            "logical_control_calls": summary["logical_control_calls"],
            "logical_candidate_calls": summary["logical_candidate_calls"],
            "syndrome_bits_per_method_frame": SYNDROME_BITS,
            "disclosure_bits_physical_batch": summary["disclosure_bits_physical_batch"],
            "internal_branch_disclosure_bits": 0, "tag_bits": 0,
            "verification": "NOT_IMPLEMENTED", "undetected": "NOT_MEASURED",
        },
        "budgets": {"wall_s": WALL_CAP_S, "rss_bytes": RSS_CAP_BYTES,
                    "output_bytes": ARTIFACT_CAP_BYTES,
                    "physical_calls": physical_call_cap},
        "resource_events": resources, "stop_reasons": stop_reasons,
        "summary": summary,
    }
    if mechanism == "top3runtime":
        manifest["accounting"].update({
            "disclosure_bits_logical_control": HOLDOUT_PAIRS * SYNDROME_BITS,
            "disclosure_bits_logical_candidate": HOLDOUT_PAIRS * SYNDROME_BITS,
            "internal_branch_disclosure_bits": 0,
            "tag_bits": 0,
            "timed_method_path": (
                "shared baseline call wall plus that method's measured arm loop; common entropy "
                "selector, sampler, physical-batch scheduling and artifact I/O excluded"),
            "end_to_end_fps_claim": False,
        })
    if mechanism == "jointtop3":
        manifest["accounting"].update({
            "logical_j3_calls": summary["logical_candidate_calls"],
            "logical_derived_j2_calls": summary["logical_derived_j2_calls"],
            "logical_derived_j2_iterations": summary["logical_derived_j2_iterations"],
            "disclosure_bits_logical_control": summary["sampled_pairs"] * SYNDROME_BITS,
            "disclosure_bits_logical_j3": summary["sampled_pairs"] * SYNDROME_BITS,
            "disclosure_bits_logical_derived_j2": summary["sampled_pairs"] * SYNDROME_BITS,
            "derived_j2_joint_branch_indices": list(JOINTTOP3_J2_SUBSET),
            "derived_j2_is_independent_execution": False,
        })
        manifest["budgets"]["physical_iterations"] = JOINTTOP3_MAX_PHYSICAL_ITERATIONS
    if mechanism in ("jointtop2", "jointcheck2", "top3runtime", "jointtop3"):
        for key in ("rank2", "mixed05", "mixed05_call_order"):
            manifest["algorithm"].pop(key)
    if mechanism == "jointtop2":
        manifest["algorithm"]["jointtop2"] = (
            "after all six rank1 branches fail, choose the next active baseline-entropy "
            "variable excluding rank1; rank both variables within the fixed six-symbol "
            "support, form four pairs in primary-outer/secondary-inner order, cold "
            "one-hot on both rows of the original prior, then blind-select valid outputs "
            "by original-prior score")
        manifest["algorithm"]["branch_prior_rows_retained"] = (
            "jointtop2 calls change only the two selected 32-symbol rows; all other rows "
            "equal original_prior")
    elif mechanism == "jointcheck2":
        manifest["algorithm"]["selector"] = (
            "control uses accepted baseline-entropy selector; candidate selects the maximum "
            "full integer count of adjacent violated checks, then baseline entropy with "
            "1e-12 ties to lowest column; second choice recomputes after excluding first")
        manifest["algorithm"]["jointcheck2"] = (
            "after all six shared rank1 branches fail, independently form four primary-outer "
            "joint guesses for control and candidate; share exactly one four-call set only "
            "when the ordered variable pairs match, otherwise run both sets in the frozen "
            "global-frame parity order; each branch is cold one-hot on two rows of the "
            "original prior and is selected by original-prior score")
        manifest["algorithm"]["branch_prior_rows_retained"] = (
            "jointcheck2 calls change only the two selected 32-symbol rows; all other rows "
            "equal original_prior")
    elif mechanism == "top3runtime":
        manifest["algorithm"]["top3runtime"] = (
            "one shared baseline; valid baseline passes through both methods; on failure use "
            "the same baseline CHECK_UPDATED entropy-selected variable; control runs all six "
            "canonical guesses and candidate independently runs posterior-ranked top three "
            "from the original beliefs; both use independent cold one-hot calls from the "
            "original prior, execute all branches without early stop, and blind-select valid "
            "outputs by original-prior score with canonical-index tie break")
        manifest["algorithm"]["top3_order"] = (
            "global frame index even: control six then candidate three; odd: candidate three "
            "then control six; actual call IDs are always distinct")
        manifest["algorithm"]["posterior_rank_storage"] = (
            "posterior execution rank is stored separately; branch_index remains the canonical "
            "index in GUESSES=(0,1,3,7,15,31)")
        manifest["algorithm"]["tradeoff_targets"] = {
            "minimum_gain_retention": 0.75,
            "maximum_accounted_method_path_ratio": 0.70,
            "candidate_selected_valid_wrong_must_not_exceed_control": True,
            "finite_synthetic_screen_only": True,
        }
    elif mechanism == "jointtop3":
        manifest["algorithm"]["jointtop3"] = (
            "C is the shared baseline plus the full six canonical one-variable cold one-hot "
            "branches after baseline failure, selected by original-prior score; J3 and derived "
            "J2 pass through the same baseline/rank1 choice unless all six rank1 branches are "
            "own-syndrome-invalid. Then select primary and secondary distinct variables from "
            "the original baseline CHECK_UPDATED entropy ranking, rank the fixed six-symbol "
            "support independently for each row, and execute all nine primary-outer/secondary-"
            "inner cold two-row one-hot calls in canonical index 3*i+j order. J3 blind-selects "
            "among all nine own-valid outputs by original effective-prior score with 1e-12 "
            "score ties to the lowest canonical index. Derived J2 reselects from those same "
            "outputs at indices 0,1,3,4; it performs no extra decoder calls or timing pass.")
        manifest["algorithm"]["branch_prior_rows_retained"] = (
            "jointtop3 calls change only the selected primary and secondary 32-symbol rows to "
            "one-hot priors; all other rows equal original_prior")
        manifest["algorithm"]["jointtop3_branch_order"] = (
            "primary top-three outer loop, secondary top-three inner loop; canonical branch "
            "index is 3*i+j for i,j in 0..2")
        manifest["algorithm"]["derived_j2_subset"] = list(JOINTTOP3_J2_SUBSET)
    arrays = _diagnostic_arrays(selected_sources, source_identity, original_prior,
                                pairs, calls, raw_vectors)
    files = {
        "diagnostics": root / "diagnostics.npz",
        "calls": root / "call_records.csv",
        "frames": root / "frame_records.csv",
        "summary": root / "summary.json",
        "manifest": root / "manifest.json",
    }
    artifact_paths = {key: str(value) for key, value in files.items()}
    artifact_paths["exploration_log"] = str(log_path)
    summary["artifacts"] = artifact_paths
    manifest["artifacts"] = artifact_paths

    def after_write(phase: str) -> None:
        reasons = check_resources(phase)
        if reasons:
            stop("INCOMPLETE", ";".join(reasons), "resource")
        total = sum(path.stat().st_size for path in root.iterdir() if path.is_file())
        if total > ARTIFACT_CAP_BYTES:
            resources.append(f"{phase}:output_cap")
            stop("INCOMPLETE", "output_cap", "resource")

    try:
        size = rescue._write_diagnostics(files["diagnostics"], arrays)
        manifest["diagnostics_npz_bytes"] = size
        after_write("after_diagnostics_write")
    except Exception as exc:
        stop("STOP", f"diagnostics_write:{type(exc).__name__}:{exc}", "integrity")
        summary["status"] = run_status
        _null_totals(summary, mechanism)
        manifest["status"] = summary["status"]
        manifest["classification"] = summary["classification"]
        manifest["summary"] = summary
    public_calls = []
    for row in calls:
        public = {key: value for key, value in row.items() if not key.startswith("_")}
        override = row.get("prior_override")
        public["prior_override_symbols_json"] = (
            "" if override is None else json.dumps(np.asarray(override).tolist(), separators=(",", ":")))
        public_calls.append(public)
    call_fields = (CALL_FIELDS + JOINTTOP3_CALL_FIELDS if mechanism == "jointtop3" else
                   CALL_FIELDS + TOP3RUNTIME_CALL_FIELDS if mechanism == "top3runtime" else
                   CALL_FIELDS + JOINTCHECK2_CALL_FIELDS if mechanism == "jointcheck2" else
                   CALL_FIELDS + JOINTTOP2_CALL_FIELDS if mechanism == "jointtop2" else
                   CALL_FIELDS)
    _write_csv(files["calls"], call_fields, public_calls)
    after_write("after_call_records_write")
    frame_rows: list[dict[str, Any]] = []
    for pair in pairs:
        metadata = pair.get("selector_metadata") or {}
        frame_row = {
            **{key: pair.get(key) for key in FRAME_FIELDS},
            "selector_active_variable_columns_json": json.dumps(metadata.get("active_variable_columns", [])),
            "selector_violated_check_ids_json": json.dumps(metadata.get("violated_check_ids", [])),
            "selector_entropy_bits_json": json.dumps(metadata.get("entropy_bits", [])),
            "delta_exact": (None if not pair.get("completed") else
                            int(bool(pair["candidate_exact"]) - bool(pair["control_exact"]))),
        }
        if mechanism == "jointcheck2":
            frame_row.update({
                key: pair.get(key) for key in JOINTCHECK2_FRAME_FIELDS
                if key not in FRAME_FIELDS and key != "selector_violated_neighbor_counts_json"
            })
            frame_row.update({
                "selector_violated_neighbor_counts_json": json.dumps(
                    metadata.get("violated_neighbor_counts", {}), separators=(",", ":")),
                "control_joint_call_indices_json": json.dumps(
                    pair.get("control_joint_call_indices", []), separators=(",", ":")),
                "candidate_joint_call_indices_json": json.dumps(
                    pair.get("candidate_joint_call_indices", []), separators=(",", ":")),
            })
        elif mechanism == "top3runtime":
            frame_row.update({
                "top3_attempted": bool(pair.get("top3_attempted", False)),
                "top3_selector_status": pair.get("top3_selector_status", ""),
                "posterior_ranked_guesses_json": json.dumps(
                    pair.get("posterior_ranked_guesses", []), separators=(",", ":")),
                "candidate_top3_guesses_json": json.dumps(
                    pair.get("candidate_top3_guesses", []), separators=(",", ":")),
                "control_branch_call_indices_json": json.dumps(
                    pair.get("control_branch_call_indices", []), separators=(",", ":")),
                "candidate_branch_call_indices_json": json.dumps(
                    pair.get("candidate_branch_call_indices", []), separators=(",", ":")),
                "baseline_wall_s": pair.get("baseline_wall_s"),
                "common_selector_wall_s": pair.get("common_selector_wall_s", 0.0),
                "control_arm_wall_s": pair.get("control_arm_wall_s", 0.0),
                "candidate_arm_wall_s": pair.get("candidate_arm_wall_s", 0.0),
            })
        elif mechanism == "jointtop3":
            frame_row.update({
                "jointtop3_attempted": bool(pair.get("jointtop3_attempted", False)),
                "jointtop3_primary_guesses_json": json.dumps(
                    pair.get("jointtop3_primary_guesses", []), separators=(",", ":")),
                "jointtop3_secondary_guesses_json": json.dumps(
                    pair.get("jointtop3_secondary_guesses", []), separators=(",", ":")),
                "jointtop3_call_indices_json": json.dumps(
                    pair.get("jointtop3_call_indices", []), separators=(",", ":")),
                "derived_j2_call_indices_json": json.dumps(
                    pair.get("derived_j2_call_indices", []), separators=(",", ":")),
                "derived_j2_selected_call_index": pair.get("derived_j2_selected_call_index"),
                "derived_j2_selected_branch_index": pair.get("derived_j2_selected_branch_index", -1),
                "derived_j2_exact": pair.get("derived_j2_exact"),
                "delta_j3_vs_derived_j2": (
                    None if not pair.get("completed") else
                    int(bool(pair["candidate_exact"]) - bool(pair["derived_j2_exact"]))),
                "derived_j2_syndrome_valid_wrong": pair.get("derived_j2_valid_wrong"),
                "derived_j2_syndrome_failed": pair.get("derived_j2_syndrome_failed"),
                "j3_selected_branch_index": pair.get("j3_selected_branch_index", -1),
            })
        frame_rows.append(frame_row)
    frame_fields = (JOINTTOP3_FRAME_FIELDS if mechanism == "jointtop3" else
                    TOP3RUNTIME_FRAME_FIELDS if mechanism == "top3runtime" else
                    JOINTCHECK2_FRAME_FIELDS if mechanism == "jointcheck2" else FRAME_FIELDS)
    _write_csv(files["frames"], frame_fields, frame_rows)
    after_write("after_frame_records_write")
    rescue._write_json(files["summary"], summary)
    after_write("after_summary_write")
    rescue._write_json(files["manifest"], manifest)
    after_write("after_manifest_write")

    output_bytes = sum(path.stat().st_size for path in root.iterdir() if path.is_file())
    checkpoint_wall = max(float(now()) - started, 0.0)
    after_artifacts = check_resources("after_first_pass_artifacts", at_time=started + checkpoint_wall)
    summary["resource_checkpoint_wall_s"] = checkpoint_wall
    summary["total_wall_s"] = checkpoint_wall
    summary["peak_rss_bytes"] = peak_rss
    summary["output_bytes"] = output_bytes
    if output_bytes > ARTIFACT_CAP_BYTES:
        resources.append("after_first_pass_artifacts:output_cap")
        stop("INCOMPLETE", "output_cap", "resource")
        after_artifacts.append("output_cap")
    if after_artifacts:
        stop("INCOMPLETE", ";".join(after_artifacts), "resource")
    if run_status != "COMPLETE":
        summary["status"] = run_status
        _null_totals(summary, mechanism)
    manifest["status"] = summary["status"]
    manifest["classification"] = summary["classification"]
    manifest["resource_events"] = resources
    manifest["stop_reasons"] = stop_reasons
    manifest["summary"] = summary
    rescue._write_json(files["summary"], summary)
    rescue._write_json(files["manifest"], manifest)
    attempt_detail = (
        f"jointtop2_calls={sum(row['role'] == 'jointtop2_candidate' for row in calls)}"
        if mechanism == "jointtop2" else
        f"jointcheck2_control={sum(row['role'] in ('jointcheck2_control', 'jointcheck2_shared') for row in calls)}; "
        f"jointcheck2_candidate={sum(row['role'] in ('jointcheck2_candidate', 'jointcheck2_shared') for row in calls)}; "
        f"distinct_pairs={summary.get('jointcheck2_distinct_pair_frames', 0)}"
        if mechanism == "jointcheck2" else
        f"jointtop3_calls={sum(row['role'] == 'jointtop3_candidate' for row in calls)}; "
        f"G={sum(bool(row.get('jointtop3_attempted')) for row in pairs)}"
        if mechanism == "jointtop3" else
        f"rank2_attempts={sum(bool(row.get('rank2_attempted')) for row in pairs)}")
    rescue._append_log(log_path, (
        f"FINAL_STATUS={summary['status']}; classification={summary['classification']}; "
        f"completed_pairs={summary['completed_pairs']}; "
        f"physical_calls={summary['attempted_physical_calls']}; {attempt_detail}; "
        f"resource_checkpoint_wall_s={checkpoint_wall:.9f}; peak_rss_bytes={peak_rss}; "
        f"output_bytes={output_bytes}; stop_reasons={stop_reasons}"))
    final_output_bytes = sum(path.stat().st_size for path in root.iterdir() if path.is_file())
    if final_output_bytes > ARTIFACT_CAP_BYTES and run_status == "COMPLETE":
        resources.append("after_terminal_log_write:output_cap")
        stop("INCOMPLETE", "output_cap", "resource")
        summary["status"] = run_status
        _null_totals(summary, mechanism)
        summary["output_bytes"] = final_output_bytes
        manifest["status"] = summary["status"]
        manifest["classification"] = summary["classification"]
        manifest["resource_events"] = resources
        manifest["summary"] = summary
        rescue._write_json(files["summary"], summary)
        rescue._write_json(files["manifest"], manifest)
    summary["output_bytes"] = final_output_bytes
    summary["artifacts"] = {key: str(value) for key, value in files.items()}
    summary["artifacts"]["exploration_log"] = str(log_path)
    result = dict(summary)
    result.update({
        "summary": summary, "calls": public_calls,
        "pairs": pairs, "source_maps": [_source_map(row) for row in selected_sources],
        "artifacts": summary["artifacts"],
    })
    return result


def _bind_production() -> dict[str, Any]:
    """Bind source, sampler, and decoder only in the explicit --execute branch."""
    from comparison_bench.cli.probes_closed import nbldpc_gf32_label_probe as sampler_module
    from comparison_bench.formal_ir import v35_algorithm_development as v35

    def decode(h, prior, syndrome, *, max_iter, damping_alpha,
               warm_beliefs, field):
        return v35.decode_row_layered_fftqspa(
            h, prior, syndrome, max_iter=max_iter,
            damping_alpha=damping_alpha, warm_beliefs=warm_beliefs, field=field)

    return {
        "source_reader": rescue._default_source_reader(),
        "sampler": sampler_module.sample_error,
        "decode_fns": {"baseline": decode, "soft_prior": decode},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Frozen GF(32) soft-prior mechanism EXPLORE probes")
    parser.add_argument("--mechanism", choices=tuple(PROFILES), required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--t0", action="store_true", help="source-free seed and contract checks")
    mode.add_argument("--dry-run", action="store_true", help="frozen-root check without source reads/writes")
    mode.add_argument("--execute", action="store_true", help="run exactly one frozen synthetic mechanism batch")
    parser.add_argument("--out-root", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.t0:
        result = verify_t0(args.mechanism)
    elif args.dry_run:
        result = dry_run(args.mechanism, args.out_root)
    else:
        profile = _profile(args.mechanism)
        rescue.validate_out_root(
            profile["out_root"] if args.out_root is None else args.out_root,
            official_root=profile["out_root"])
        result = execute_batch(
            mechanism=args.mechanism, **_bind_production(),
            out_root=args.out_root)
    printable = result.get("summary", result)
    print(json.dumps(printable, indent=2, sort_keys=True, default=rescue._json_value))
    return 0 if result.get("status") in ("PASS", "DRY_RUN", "COMPLETE") else 2


if __name__ == "__main__":
    raise SystemExit(main())
