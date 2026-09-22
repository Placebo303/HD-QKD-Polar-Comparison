#!/usr/bin/env python3
"""V72P2D2 CLI boundary and synthetic layered-kernel cost preflight.

The default command is deliberately limited to the accepted synthetic
preflight.  The future real L/I/P invocation has a separate, explicit CLI
mode and a fail-closed cycle-state gate.  No input-data or production-output
path is touched by the default path.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "comparison_bench"
    / "src"
    / "comparison_bench"
    / "formal_ir"
    / "v72p2d2_orthogonal_triage.py"
)
CYCLE_ID = "V72P2D2-TRIAGE"
ACCEPTED_PLAN_GIT_REVISION = "4592bdad357a02f8f08a880ca0036beaed3ee900"
SEED = 20260902
CYCLE_STATE_PATH = REPO_ROOT / "docs" / "research_cycles" / CYCLE_ID / "cycle_state.yaml"
WORKSPACE_ROOT = (REPO_ROOT / "workspace").resolve()
PRODUCTION_OUTPUT_ROOT = (
    REPO_ROOT / "comparison_bench" / "outputs_comparison"
).resolve()
DEFAULT_OUTPUT = WORKSPACE_ROOT / "v72p2d2_orthogonal_preflight" / "cost_preflight.json"
REAL_OUTPUT_ROOT = (
    PRODUCTION_OUTPUT_ROOT / "v72p2d2_orthogonal_oneblock_20260904"
).resolve()
R1_OUTPUT_ROOT = (
    PRODUCTION_OUTPUT_ROOT / "v72p2d2r1_orthogonal_oneblock_20260904"
).resolve()
D1_RESULTS_PATH = (
    PRODUCTION_OUTPUT_ROOT / "v72p2d1_parity_layout_ab" / "results.json"
).resolve()
BASE_GIT_REVISION = "e094f7e548380db4bfcbc1fe73472e670c32379a"
TARGET_SESSION = "20260123_1M_600k_0dB"
TARGET_BLOCK_FRAMES = (1726, 1727, 1728, 1729)
ARM_ORDER = ("A", "L", "I", "P")
NEW_ARM_ORDER = ("L", "I", "P")
ARM_DEADLINE_S = 600.0
INVOCATION_DEADLINE_S = 2400.0
RSS_LIMIT_BYTES = 2 * 1024**3
NOT_RECORDED_REASON = "D1 baseline did not record this metric; A was not rerun"
PAIR_COLUMNS = ["frame_id", "pair_idx", "alice_symbol", "bob_symbol"]
FRAME_PAIRS = 256
CAL_FRAME_IDS = tuple(range(702, 1726))
VAL_FRAME_IDS = tuple(range(1726, 1762))
PROBABILITY_FLOOR = 1e-300
LAMBDA_GRID = tuple(10.0 ** value for value in np.linspace(-2.0, 4.0, 30))
# ponytail: runner mirrors the core's authoritative block constants; test asserts equality.
Q = 1024
N = 1024
NBIT = 10240
M = 9036
NNZ = 49620
CHECKPOINT_ROWS = tuple(list(range(160, 8993, 128)) + [9032, 9036])


def load_triage_module():
    """Load the core module without importing any data or output runner."""
    spec = importlib.util.spec_from_file_location(
        "v72p2d2_orthogonal_triage", str(MODULE_PATH)
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json_value(value: Any) -> Any:
    """Convert NumPy-like scalar/array values for the small JSON report."""
    if hasattr(value, "item"):
        return value.item()
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _resolve_workspace_output(path: str | Path) -> Path:
    """Resolve a synthetic report path and keep it inside ``workspace``."""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    output = candidate.resolve()
    try:
        output.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:
        raise ValueError("synthetic preflight output must stay under workspace/") from exc
    if output == PRODUCTION_OUTPUT_ROOT or PRODUCTION_OUTPUT_ROOT in output.parents:
        raise ValueError("synthetic preflight output must stay outside production outputs")
    if output.name != "cost_preflight.json":
        raise ValueError("preflight output must be named cost_preflight.json")
    return output


def _parse_yaml_scalar(value: str) -> Any:
    """Parse the small scalar subset used by the cycle-state file."""
    text = value.strip()
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    if text.lower() in {"null", "~"}:
        return None
    if (text.startswith("\"") and text.endswith("\"")) or (
        text.startswith("'") and text.endswith("'")
    ):
        return text[1:-1]
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


def read_cycle_state(path: str | Path = CYCLE_STATE_PATH) -> dict[str, Any]:
    """Read only the flat authorization fields from a cycle-state YAML file.

    The repository cycle state is intentionally tiny and flat.  Avoiding a
    YAML dependency keeps this gate import-safe for the synthetic path.
    """
    state_path = Path(path)
    if not state_path.is_absolute():
        state_path = REPO_ROOT / state_path
    state_path = state_path.resolve()
    if not state_path.is_file():
        raise FileNotFoundError(f"cycle-state file not found: {state_path}")
    values: dict[str, Any] = {}
    for raw_line in state_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = _parse_yaml_scalar(value)
    values["_path"] = str(state_path)
    return values


def require_real_authorization(
    *,
    execute_real: bool,
    cycle_state_path: str | Path = CYCLE_STATE_PATH,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Require the one explicit real-diagnostic gate before reading data."""
    if not execute_real:
        raise PermissionError("real L/I/P execution requires --execute-real")
    state = read_cycle_state(cycle_state_path)
    if state.get("cycle_id") != CYCLE_ID:
        raise PermissionError("cycle-state cycle_id does not match V72P2D2-TRIAGE")
    if state.get("accepted_plan_git_revision") != ACCEPTED_PLAN_GIT_REVISION:
        raise PermissionError("cycle-state accepted plan revision is not the accepted V72P2D2 plan")
    # ponytail: R1 new root reads r1 counts/flags (1/0 or true/false); old root keeps old counts.
    is_r1_output = output_path is not None and Path(output_path).resolve() == R1_OUTPUT_ROOT
    if is_r1_output:
        if state.get("r1_real_execution_authorized") != 1:
            raise PermissionError("cycle-state r1_real_execution_authorized is not true")
        if state.get("r1_formal_execution_authorized") != 0:
            raise PermissionError("r1_formal_execution_authorized must remain false")
        completed = int(state.get("r1_execution_count_completed", 0))
        authorized = int(state.get("r1_execution_count_authorized", 0))
        if authorized != 1 or completed != 0:
            raise PermissionError("the single authorized R1 diagnostic invocation is already consumed")
    else:
        if state.get("real_execution_authorized") is not True:
            raise PermissionError("cycle-state real_execution_authorized is not true")
        if state.get("formal_execution_authorized") is not False:
            raise PermissionError("formal_execution_authorized must remain false")
        completed = int(state.get("execution_count_completed", 0))
        authorized = int(state.get("execution_count_authorized", 0))
        if authorized != 1 or completed != 0:
            raise PermissionError("the single authorized diagnostic invocation is already consumed")
    if output_path is not None and Path(output_path).resolve().exists():
        raise FileExistsError(f"output directory already exists: {Path(output_path).resolve()}")
    return state


def _preflight_status(report: Mapping[str, Any]) -> tuple[str, int]:
    """Apply the frozen synthetic cost gate without changing its threshold.

    The core's frozen arithmetic and 600-second threshold are retained.  The
    synthetic preflight reports ``PLAN_REVISE_REQUIRED`` when the projection
    exceeds that threshold.  ``RESOURCE_BLOCKED`` is reserved for a future
    real L timeout and is not a synthetic preflight result.
    """
    projected = float(report["projected_L_wall_s"])
    if projected > 600.0:
        return "PLAN_REVISE_REQUIRED", 2
    return "PASS", 0


def run_synthetic_preflight(
    *, output: str | Path = DEFAULT_OUTPUT, seed: int = SEED
) -> int:
    """Run only the five-point synthetic layered cost preflight."""
    if int(seed) != SEED:
        raise ValueError(f"synthetic preflight seed is frozen at {SEED}")
    output_path = _resolve_workspace_output(output)
    module = load_triage_module()
    indptr, indices, nnz = module.get_mother_csr()
    if (
        int(nnz) != module.NNZ
        or indptr.shape != (module.M + 1,)
        or indices.shape != (module.NNZ,)
    ):
        raise ValueError("mother dimensions do not match the frozen contract")

    report = dict(module.cost_preflight(indptr, indices, seed=SEED))
    status, exit_code = _preflight_status(report)
    report["cli_mode"] = "synthetic-preflight"
    report["cycle_id"] = CYCLE_ID
    report["hard_wall_limit_s"] = 600.0
    report["core_preflight_status"] = report.get("status")
    report["status"] = status
    report["exit_code"] = exit_code
    report["real_decoder_executed"] = False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(_json_value(report), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    summary = {
        "output": str(output_path),
        "status": status,
        "projected_L_wall_s": float(report["projected_L_wall_s"]),
        "peak_rss_bytes": int(report["peak_rss_bytes"]),
        "exit_code": exit_code,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return exit_code


def _derive_syndrome(bits: np.ndarray, indptr: np.ndarray, indices: np.ndarray) -> np.ndarray:
    """Derive the public binary syndrome without creating a tag."""
    values = np.asarray(bits, dtype=np.uint8)
    offsets = np.asarray(indptr, dtype=np.int32)
    columns = np.asarray(indices, dtype=np.int32)
    if values.shape != (NBIT,) or offsets.ndim != 1 or columns.ndim != 1:
        raise ValueError("syndrome inputs have unexpected shapes")
    if offsets.size != M + 1 or int(offsets[0]) != 0 or int(offsets[-1]) != columns.size:
        raise ValueError("syndrome CSR does not match the frozen mother")
    syndrome = np.zeros(offsets.size - 1, dtype=np.uint8)
    for row in range(syndrome.size):
        start, end = int(offsets[row]), int(offsets[row + 1])
        syndrome[row] = np.uint8(int(np.sum(values[columns[start:end]])) & 1)
    return syndrome


def _pack_symbols(bits: np.ndarray) -> np.ndarray:
    values = np.asarray(bits, dtype=np.uint8)
    if values.shape != (NBIT,):
        raise ValueError("bit array must have shape (10240,)")
    return np.asarray(
        [sum(int(values[10 * symbol + bit]) << bit for bit in range(10)) for symbol in range(N)],
        dtype=np.uint16,
    )


def _physicalize_bits(bits: np.ndarray, old_to_phys: np.ndarray) -> np.ndarray:
    values = np.asarray(bits, dtype=np.uint8)
    mapping = np.asarray(old_to_phys, dtype=np.int32)
    if values.shape != (NBIT,) or mapping.shape != (NBIT,):
        raise ValueError("physical bit mapping inputs have unexpected shapes")
    physical = np.zeros_like(values)
    physical[mapping] = values
    return physical


def _load_registry(path: str | Path) -> tuple[dict[str, Any], Path]:
    registry_path = Path(path)
    if not registry_path.is_absolute():
        registry_path = REPO_ROOT / registry_path
    registry_path = registry_path.resolve()
    return json.loads(registry_path.read_text(encoding="utf-8")), registry_path


def _select_target_session(registry: Mapping[str, Any]) -> Mapping[str, Any]:
    sessions = [
        session for session in registry.get("sessions", [])
        if session.get("session_id") == TARGET_SESSION and session.get("source_label") == "1M"
    ]
    if len(sessions) != 1:
        raise ValueError("registry must contain exactly one target 1M session")
    return sessions[0]


def _assigned_frame_groups(session: Mapping[str, Any]) -> tuple[list[int], list[list[int]]]:
    cal_ids = [int(value) for value in session.get("stage2_CAL_frame_ids", [])]
    val_ids = [int(value) for value in session.get("stage2_VAL_frame_ids", [])]
    if cal_ids != list(CAL_FRAME_IDS):
        raise ValueError("CAL assignment is not the frozen 702..1725 sequence")
    if val_ids[: len(VAL_FRAME_IDS)] != list(VAL_FRAME_IDS):
        raise ValueError("VAL assignment does not start with frozen 1726..1761")
    groups = [
        val_ids[offset : offset + 4]
        for offset in range(0, len(VAL_FRAME_IDS), 4)
    ]
    if len(groups) != 9 or any(len(group) != 4 for group in groups):
        raise ValueError("VAL assignment must contain nine four-frame groups")
    if any(group != list(range(group[0], group[0] + 4)) for group in groups):
        raise ValueError("each VAL group must contain consecutive frame IDs")
    return cal_ids, groups


def _read_selected_pairs(path: str | Path, frame_ids: list[int]) -> tuple[Any, str]:
    """Read only the fixed no-tag columns and frame IDs from the registry file."""
    import pandas as pd

    pairs_path = Path(path)
    frame = pd.read_parquet(
        pairs_path,
        columns=PAIR_COLUMNS,
        filters=[("frame_id", "in", [int(value) for value in frame_ids])],
    )
    return frame, "predicate_pushdown"


def _integer_column(frame: Any, name: str) -> np.ndarray:
    values = frame[name].to_numpy(dtype=np.float64)
    if values.size == 0 or not np.all(np.isfinite(values)) or not np.all(values == np.floor(values)):
        raise ValueError(f"{name} contains missing or non-integral values")
    return values.astype(np.int32)


def _validate_selected_frame(frame: Any, frame_id: int) -> dict[str, np.ndarray]:
    missing = [column for column in PAIR_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")
    selected = frame.loc[frame["frame_id"] == int(frame_id), PAIR_COLUMNS].copy()
    if len(selected) != FRAME_PAIRS:
        raise ValueError(f"frame {frame_id} has {len(selected)} rows, expected {FRAME_PAIRS}")
    pair_idx = _integer_column(selected, "pair_idx")
    if len(np.unique(pair_idx)) != FRAME_PAIRS:
        raise ValueError(f"frame {frame_id} pair_idx values are not distinct")
    order = np.argsort(pair_idx, kind="stable")
    alice = _integer_column(selected, "alice_symbol")[order]
    bob = _integer_column(selected, "bob_symbol")[order]
    if np.any(alice < 0) or np.any(alice >= Q) or np.any(bob < 0) or np.any(bob >= Q):
        raise ValueError(f"frame {frame_id} contains a symbol outside 0..1023")
    return {"alice_symbols": alice, "bob_symbols": bob}


def _validate_selected_frames(frame: Any, frame_ids: list[int]) -> dict[int, dict[str, np.ndarray]]:
    return {int(frame_id): _validate_selected_frame(frame, int(frame_id)) for frame_id in frame_ids}


def _assemble_frame_group(
    frames: Mapping[int, Mapping[str, np.ndarray]], frame_ids: list[int]
) -> tuple[np.ndarray, np.ndarray]:
    if any(int(frame_id) not in frames for frame_id in frame_ids):
        raise ValueError("cannot assemble a group with an invalid frame")
    alice = np.concatenate([frames[int(fid)]["alice_symbols"] for fid in frame_ids])
    bob = np.concatenate([frames[int(fid)]["bob_symbols"] for fid in frame_ids])
    if alice.shape != (N,) or bob.shape != (N,):
        raise ValueError("a four-frame group must contain 1024 symbols")
    return alice.astype(np.int32), bob.astype(np.int32)


def _symbols_to_bits(symbols: np.ndarray) -> np.ndarray:
    values = np.asarray(symbols, dtype=np.int32)
    if values.shape != (N,) or np.any(values < 0) or np.any(values >= Q):
        raise ValueError("symbols must have shape (1024,) and lie in 0..1023")
    return ((values[:, None] >> np.arange(10, dtype=np.int32)) & 1).astype(np.uint8).reshape(NBIT)


def _hierarchical_p(counts: np.ndarray, p_global: np.ndarray, n_b: np.ndarray, lam: float) -> np.ndarray:
    probabilities = (counts.astype(np.float64) + float(lam) * p_global[None, :]) / (n_b[:, None] + float(lam))
    zero = n_b == 0
    if np.any(zero):
        probabilities[zero] = p_global
    return probabilities


def _select_lambda(a_cal: np.ndarray, b_cal: np.ndarray) -> tuple[float, dict[float, float], float, bool]:
    n = len(a_cal)
    fold = n // 4
    best_lam: float | None = None
    best_ce = float("inf")
    per: dict[float, float] = {}
    for lam in LAMBDA_GRID:
        ces = []
        for k in range(4):
            lo = k * fold
            hi = (k + 1) * fold if k < 3 else n
            mask = np.ones(n, dtype=bool)
            mask[lo:hi] = False
            a_train, b_train = a_cal[mask], b_cal[mask]
            a_test, b_test = a_cal[lo:hi], b_cal[lo:hi]
            counts = np.zeros((Q, Q), dtype=np.int32)
            np.add.at(counts, (b_train, a_train), 1)
            n_b = counts.sum(axis=1).astype(np.float64)
            p_global = counts.sum(axis=0).astype(np.float64) / float(len(a_train))
            probabilities = _hierarchical_p(counts, p_global, n_b, lam)
            likelihood = np.maximum(probabilities[b_test, a_test], PROBABILITY_FLOOR)
            ces.append(float(-np.log2(likelihood).mean()))
        average = float(np.mean(ces))
        per[float(lam)] = average
        if average < best_ce:
            best_ce = average
            best_lam = float(lam)
    if best_lam is None:  # pragma: no cover - nonempty CAL is validated by caller
        raise ValueError("CAL lambda selection produced no candidate")
    boundary = bool(best_lam <= 1e-2 + 1e-12 or best_lam >= 1e4 - 1e-9)
    return best_lam, per, best_ce, boundary


def _fit_cal_model(a_cal: np.ndarray, b_cal: np.ndarray) -> dict[str, Any]:
    """Fit the frozen CAL-only M0 model without importing the tag runner."""
    a = np.asarray(a_cal, dtype=np.int32)
    b = np.asarray(b_cal, dtype=np.int32)
    if a.shape != b.shape or a.ndim != 1 or len(a) == 0:
        raise ValueError("CAL arrays must be non-empty one-dimensional pairs")
    if np.any(a < 0) or np.any(a >= Q) or np.any(b < 0) or np.any(b >= Q):
        raise ValueError("CAL symbols must lie in 0..1023")
    lam_star, cv_scores, ce_ref, boundary = _select_lambda(a, b)
    counts = np.zeros((Q, Q), dtype=np.int32)
    np.add.at(counts, (b, a), 1)
    n_b = counts.sum(axis=1).astype(np.float64)
    p_global = counts.sum(axis=0).astype(np.float64) / float(len(a))
    probabilities = np.asarray(_hierarchical_p(counts, p_global, n_b, lam_star), dtype=np.float64)
    probabilities = np.maximum(probabilities, PROBABILITY_FLOOR)
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    if not np.all(np.isfinite(probabilities)):
        raise ValueError("CAL model produced non-finite probabilities")
    return {
        "selected_lambda": float(lam_star),
        "lambda_cv_scores": {str(float(key)): float(value) for key, value in cv_scores.items()},
        "ce_ref_log2": float(ce_ref),
        "ce_ref_definition": "selected CAL-CV cross-entropy in log2; selection-conditioned model",
        "lambda_at_boundary": bool(boundary),
        "probability_floor": PROBABILITY_FLOOR,
        "Ps_full": probabilities,
    }


def _build_m0_prior(bob_symbols: np.ndarray, probabilities: np.ndarray) -> np.ndarray:
    bob = np.asarray(bob_symbols, dtype=np.int32)
    probabilities = np.asarray(probabilities, dtype=np.float64)
    if bob.shape != (N,) or probabilities.shape != (Q, Q):
        raise ValueError("Bob symbols/prior model have an unexpected shape")
    rows = np.maximum(probabilities[bob], PROBABILITY_FLOOR)
    rows /= rows.sum(axis=1, keepdims=True)
    return np.log(rows).astype(np.float64)


def _load_a_baseline(path: str | Path) -> dict[str, Any]:
    """Read only the accepted D1 Arm A scalar record; never rerun D1."""
    baseline_path = Path(path)
    if not baseline_path.is_absolute():
        baseline_path = REPO_ROOT / baseline_path
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    arms = payload.get("arms", [])
    if isinstance(arms, Mapping):
        arms = list(arms.values())
    arm = next((item for item in arms if item.get("arm") == "A"), None)
    if not isinstance(arm, Mapping):
        raise ValueError("accepted D1 results do not contain Arm A")
    d = arm.get("D", {}) if isinstance(arm.get("D", {}), Mapping) else {}
    reason = NOT_RECORDED_REASON
    o1_value = arm.get("O1_violation")
    common = {
        "outcome": arm.get("status"),
        "iterations": arm.get("iterations_used"),
        "candidate_vs_bob": {
            "bits": arm.get("D8_alice_vs_bob_bit", d.get("D8_alice_vs_bob_bit")),
            "symbols": arm.get("D8_alice_vs_bob_sym", d.get("D8_alice_vs_bob_sym")),
        },
        "D1_APP": {
            "finite": d.get("D4_finite"),
            "max_abs": d.get("D4_max_abs"),
            "mean": d.get("D4_mean"),
        },
        "D1_single_edge_c2v": {
            "finite": d.get("D5_finite"),
            "max_abs": d.get("D5_max_abs"),
            "residual": d.get("D5_residual"),
            "iterations": d.get("D5_iters"),
        },
        "O1_violation": {
            "value": o1_value,
            "label": "POSTHOC_RECONSTRUCTED" if o1_value is not None else None,
            "not_recorded_reason": None if o1_value is not None else reason,
        },
    }
    new_metric_names = (
        "L0",
        "F",
        "S",
        "A_raw",
        "delta_app",
        "sign_transitions",
        "clip_counts",
        "syndrome_satisfied",
    )
    null_metrics = {
        name: {"value": None, "not_recorded_reason": reason}
        for name in new_metric_names
    }
    return {
        "arm_id": "A",
        "status": str(arm.get("status", "UNKNOWN")),
        "graph_id": "original_D1_reused",
        "prior_id": "D1_M0_reused",
        "schedule_id": "D1_flooding_reused",
        "attempted": False,
        "attempted_checkpoints": int(len(arm.get("per_checkpoint", []))),
        "stop_reason": "D1_REUSED",
        "first_syndrome_satisfied_ckpt": None,
        "final_checkpoint_rows": None,
        "final_syndrome_satisfied": None,
        "final_oracle_exact": None,
        "diagnostic_exact": None,
        "syndrome_collision_wrong": None,
        "sweeps_used": None,
        "edge_updates": None,
        "local_factor_target_updates": None,
        "state_evaluations": None,
        "diagnostic_L0_target_updates": None,
        "diagnostic_checkpoint_rebuild_target_updates": None,
        "diagnostic_final_readout_target_updates": None,
        "diagnostic_factor_target_updates": None,
        "diagnostic_state_evaluations": None,
        "diagnostic_readout_evaluations": None,
        "total_target_updates": None,
        "total_state_evaluations": None,
        "peak_rss_bytes": None,
        "rss_samples": [],
        "accounting": {
            "syndrome_rows_published": None,
            "syndrome_bits_published": None,
            "tag_bits_published": None,
            "control_bits_sent": None,
            "disclosed_rows": None,
            "public_disclosure_bits": None,
            "not_recorded_reason": reason,
        },
        "checkpoint_metrics": [],
        "common_metrics": common,
        "new_metrics": null_metrics,
        "new_metric_fields": list(new_metric_names),
        "posthoc_oracle": {
            "runs_after_arm_end": False,
            "final_oracle_exact": None,
            "not_recorded_reason": reason,
        },
        "tag_bits": 0,
        "tag_ok": "NOT_APPLICABLE",
        "baseline_source": str(baseline_path),
    }


def _mapping_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    """Keep interleaver evidence to public scalar/short-summary fields."""
    keys = (
        "bijection",
        "shape_preserved",
        "row_degree_multiset_preserved",
        "column_degree_multiset_preserved",
        "all_symbols_have_ten_slots",
        "high_distribution_valid",
        "rank_old",
        "rank_new",
        "rank_preserved",
        "prefix_nesting_preserved",
        "old_pure_h_four_cycles",
        "new_pure_h_four_cycles",
        "old_pure_h_collision_pairs",
        "new_pure_h_collision_pairs",
        "pure_h_four_cycles",
        "pure_h_collision_pairs",
        "symbol_sigma_c2",
        "symbol_collision_rows",
    )
    summary = {key: _json_value(report.get(key)) for key in keys}
    old_symbol = report.get("old_symbol_stats", {})
    new_symbol = report.get("new_symbol_stats", {})
    for label, item in (("old", old_symbol), ("new", new_symbol)):
        if isinstance(item, Mapping):
            summary[f"{label}_symbol_edges"] = {
                key: _json_value(item.get(key))
                for key in ("symbol_edges_min", "symbol_edges_median", "symbol_edges_max")
            }
    return summary


def _prepare_real_inputs(
    registry_path: str | Path,
    d1_results_path: str | Path,
    core: Any,
) -> dict[str, Any]:
    """Load the fixed block and CAL model after the real gate has passed."""
    registry, registry_file = _load_registry(registry_path)
    session = _select_target_session(registry)
    cal_ids, groups = _assigned_frame_groups(session)
    if not groups or tuple(groups[0]) != TARGET_BLOCK_FRAMES:
        raise ValueError("the registered VAL sequence does not begin with the fixed D1 block")
    block_frame_ids = list(TARGET_BLOCK_FRAMES)
    selected_ids = list(cal_ids) + block_frame_ids
    pairs_path = Path(session["provenance"])
    if not pairs_path.is_absolute():
        pairs_path = REPO_ROOT / pairs_path
    frame, read_mode = _read_selected_pairs(pairs_path, selected_ids)
    try:
        cal_frames = _validate_selected_frames(frame, list(cal_ids))
        block_frames = _validate_selected_frames(frame, block_frame_ids)
    except ValueError as exc:
        raise ValueError(f"invalid selected frame: {exc}") from exc
    alice_symbols, bob_symbols = _assemble_frame_group(block_frames, block_frame_ids)
    a_cal = np.concatenate([cal_frames[fid]["alice_symbols"] for fid in cal_ids])
    b_cal = np.concatenate([cal_frames[fid]["bob_symbols"] for fid in cal_ids])
    model = _fit_cal_model(a_cal, b_cal)
    indptr, indices, nnz = core.get_mother_csr()
    if int(nnz) != core.NNZ or indptr.shape != (core.M + 1,) or indices.shape != (core.NNZ,):
        raise ValueError("mother CSR does not match the frozen 9036x10240 graph")
    core._validate_mother_contract(indptr, indices)
    mapping = core.build_degree_balanced_interleaver(indptr, indices)
    mapping_report = core.verify_interleaver(indptr, indices, mapping)
    old_to_phys = np.asarray(mapping["old_to_phys"], dtype=np.int32)
    indices_i = core.remap_csr(indices, old_to_phys)
    alice_bits = _symbols_to_bits(alice_symbols)
    bob_bits = _symbols_to_bits(bob_symbols)
    alice_bits_i = _physicalize_bits(alice_bits, old_to_phys)
    bob_bits_i = _physicalize_bits(bob_bits, old_to_phys)
    syndrome = _derive_syndrome(alice_bits, indptr, indices)
    syndrome_i = _derive_syndrome(alice_bits_i, indptr, indices_i)
    if not np.array_equal(syndrome, syndrome_i):
        raise ValueError("interleaved syndrome algebra does not match the original graph")
    bob_symbols_i = _pack_symbols(bob_bits_i)
    prior_m0 = _build_m0_prior(bob_symbols, model["Ps_full"])
    prior_m0_i = core.build_m0_prior_logp(bob_symbols_i, model["Ps_full"])
    prior_m2 = core.build_m2_prior_logp(bob_symbols)
    return {
        "registry": registry,
        "registry_file": registry_file,
        "session": session,
        "cal_frame_ids": list(map(int, cal_ids)),
        "block_frame_ids": block_frame_ids,
        "read_mode": read_mode,
        "model": model,
        "indptr": np.asarray(indptr, dtype=np.int32),
        "indices": np.asarray(indices, dtype=np.int32),
        "indices_i": np.asarray(indices_i, dtype=np.int32),
        "mapping": mapping,
        "mapping_summary": _mapping_summary(mapping_report),
        "alice_symbols": np.asarray(alice_symbols, dtype=np.int32),
        "bob_symbols": np.asarray(bob_symbols, dtype=np.int32),
        "alice_bits": np.asarray(alice_bits, dtype=np.uint8),
        "bob_bits": np.asarray(bob_bits, dtype=np.uint8),
        "alice_bits_i": np.asarray(alice_bits_i, dtype=np.uint8),
        "bob_bits_i": np.asarray(bob_bits_i, dtype=np.uint8),
        "syndrome": np.asarray(syndrome, dtype=np.uint8),
        "syndrome_i": np.asarray(syndrome_i, dtype=np.uint8),
        "prior_m0": np.asarray(prior_m0, dtype=np.float64),
        "prior_m0_i": np.asarray(prior_m0_i, dtype=np.float64),
        "prior_m2": np.asarray(prior_m2, dtype=np.float64),
        "a_baseline": _load_a_baseline(d1_results_path),
    }


def _not_attempted_arm(arm_id: str, error: str) -> dict[str, Any]:
    return {
        "arm_id": arm_id,
        "status": "NOT_ATTEMPTED",
        "graph_id": None,
        "prior_id": None,
        "schedule_id": None,
        "attempted": False,
        "attempted_checkpoints": 0,
        "stop_reason": error,
        "first_syndrome_satisfied_ckpt": None,
        "final_checkpoint_rows": None,
        "final_syndrome_satisfied": None,
        "final_oracle_exact": None,
        "diagnostic_exact": None,
        "syndrome_collision_wrong": None,
        "sweeps_used": 0,
        "edge_updates": 0,
        "local_factor_target_updates": 0,
        "state_evaluations": 0,
        "diagnostic_L0_target_updates": 0,
        "diagnostic_checkpoint_rebuild_target_updates": 0,
        "diagnostic_final_readout_target_updates": 0,
        "diagnostic_factor_target_updates": 0,
        "diagnostic_state_evaluations": 0,
        "diagnostic_readout_evaluations": 0,
        "total_target_updates": 0,
        "total_state_evaluations": 0,
        "peak_rss_bytes": None,
        "rss_samples": [],
        "accounting": {
            "syndrome_rows_published": 0,
            "syndrome_bits_published": 0,
            "tag_bits_published": 0,
            "control_bits_sent": 0,
            "disclosed_rows": 0,
            "public_disclosure_bits": 0,
        },
        "checkpoint_metrics": [],
        "common_metrics": {},
        "new_metric_fields": [],
        "posthoc_oracle": {"runs_after_arm_end": False, "final_oracle_exact": None},
        "tag_bits": 0,
        "tag_ok": "NOT_APPLICABLE",
        "error": error,
    }


def _run_real_arm(
    arm_id: str,
    prepared: Mapping[str, Any],
    core: Any,
    *,
    flooding_decoder: Any,
    clock: Any = time.monotonic,
    rss_reader: Any | None = None,
) -> dict[str, Any]:
    if arm_id == "L":
        graph_id, prior_id, schedule = "original_H", "M0_CAL", "layered"
        indices = prepared["indices"]
        prior = prepared["prior_m0"]
        alice = prepared["alice_bits"]
        bob = prepared["bob_bits"]
        syndrome = prepared["syndrome"]
        decoder = core.run_layered_decoder
    elif arm_id == "I":
        graph_id, prior_id, schedule = "H_I_degree_balanced", "M0_CAL", "flooding"
        indices = prepared["indices_i"]
        prior = prepared["prior_m0_i"]
        alice = prepared["alice_bits_i"]
        bob = prepared["bob_bits_i"]
        syndrome = prepared["syndrome_i"]
        decoder = flooding_decoder
    elif arm_id == "P":
        graph_id, prior_id, schedule = "original_H", "M2_V70R1", "flooding"
        indices = prepared["indices"]
        prior = prepared["prior_m2"]
        alice = prepared["alice_bits"]
        bob = prepared["bob_bits"]
        syndrome = prepared["syndrome"]
        decoder = flooding_decoder
    else:
        raise ValueError(f"unknown new arm {arm_id}")
    result = core.run_arm_synthetic(
        arm_id,
        prior,
        syndrome,
        alice,
        bob,
        prepared["indptr"],
        indices,
        decoder,
        schedule,
        checkpoint_rows=core.CHECKPOINT_ROWS,
        max_per_checkpoint=core.MAX_SWEEPS_PER_CHECKPOINT,
        max_total=core.MAX_TOTAL_SWEEPS,
        deadline_s=ARM_DEADLINE_S,
        rss_limit_bytes=RSS_LIMIT_BYTES,
        clock=clock,
        rss_reader=rss_reader,
    )
    result["graph_id"] = graph_id
    result["prior_id"] = prior_id
    result["schedule_id"] = schedule
    result["attempted"] = True
    return result


def run_real_invocation(
    prepared: Mapping[str, Any],
    core: Any,
    *,
    arm_runner: Any | None = None,
    flooding_decoder: Any | None = None,
    clock: Any = time.monotonic,
    rss_reader: Any | None = None,
) -> tuple[dict[str, dict[str, Any]], str, str | None]:
    """Run A(read-only), then L/I/P once each with fail-closed ordering.

    ``arm_runner`` is used only by focused fake tests.  Production calls use
    ``_run_real_arm`` and the existing V72P1 flooding decoder.
    """
    arms: dict[str, dict[str, Any]] = {"A": prepared["a_baseline"]}
    if rss_reader is None:
        rss_reader = core.current_rss_bytes
    started = float(clock())
    for index, arm_id in enumerate(NEW_ARM_ORDER):
        if float(clock()) - started >= INVOCATION_DEADLINE_S:
            error = "invocation_timeout"
            for later in NEW_ARM_ORDER[index:]:
                arms[later] = _not_attempted_arm(later, error)
            return arms, "RESOURCE_BLOCKED", error
        try:
            if arm_runner is not None:
                result = arm_runner(arm_id, prepared)
            else:
                if flooding_decoder is None:
                    flooding_decoder = core.get_flooding_decoder()
                result = _run_real_arm(
                    arm_id,
                    prepared,
                    core,
                    flooding_decoder=flooding_decoder,
                    clock=clock,
                    rss_reader=rss_reader,
                )
            if not isinstance(result, Mapping):
                raise ValueError("arm runner did not return a mapping")
            result = dict(result)
        except TimeoutError as exc:
            result = _not_attempted_arm(arm_id, f"timeout: {exc}")
            result["status"] = "RESOURCE_BLOCKED"
            result["stop_reason"] = "timeout"
        except Exception as exc:
            result = _not_attempted_arm(arm_id, f"exception: {type(exc).__name__}: {exc}")
            result["status"] = "RESOURCE_BLOCKED"
            result["stop_reason"] = "exception"
        arms[arm_id] = result
        if result.get("status") not in {"LADDER_EXHAUSTED", "BUDGET_EXHAUSTED"}:
            error = str(result.get("stop_reason", result.get("status", "arm_blocked")))
            for later in NEW_ARM_ORDER[index + 1 :]:
                arms[later] = _not_attempted_arm(later, error)
            # ponytail: resource stops are RESOURCE_BLOCKED, never an algorithm verdict.
            invocation = "RESOURCE_BLOCKED" if result.get("status") == "RESOURCE_BLOCKED" else "BLOCKED"
            return arms, invocation, error
    return arms, "COMPLETED", None


def _preflight_for_manifest(path: str | Path | None, state: Mapping[str, Any]) -> dict[str, Any]:
    """Load and validate the explicitly supplied synthetic preflight report.

    This gate is deliberately independent of ``cycle_state``: a PASS flag in
    cycle state is not a substitute for the specified JSON artifact.  No data
    loader is called until this function returns.
    """
    del state
    if path is None:
        raise FileNotFoundError("a synthetic cost-preflight JSON is required before real execution")
    preflight_path = Path(path)
    if not preflight_path.is_absolute():
        preflight_path = REPO_ROOT / preflight_path
    preflight_path = preflight_path.resolve()
    if not preflight_path.is_file():
        raise FileNotFoundError(f"synthetic cost-preflight JSON not found: {preflight_path}")
    try:
        report = json.loads(preflight_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"synthetic cost-preflight JSON is invalid: {preflight_path}") from exc
    if not isinstance(report, Mapping):
        raise ValueError("synthetic cost-preflight report must be a JSON object")
    if report.get("cycle_id") != CYCLE_ID:
        raise PermissionError("synthetic cost-preflight report is stale or belongs to another cycle")
    if report.get("synthetic_only") is not True or report.get("real_decoder_executed") is not False:
        raise PermissionError("synthetic cost-preflight report is not a synthetic-only PASS artifact")
    if report.get("status") != "PASS":
        raise PermissionError("synthetic cost-preflight status is not PASS")
    try:
        projected = float(report["projected_L_wall_s"])
    except (KeyError, TypeError, ValueError) as exc:
        raise PermissionError("synthetic cost-preflight projected_L_wall_s is missing or invalid") from exc
    if not np.isfinite(projected) or projected > ARM_DEADLINE_S:
        raise PermissionError("synthetic cost-preflight exceeds the 600-second L wall gate")
    try:
        peak = int(report["peak_rss_bytes"])
    except (KeyError, TypeError, ValueError) as exc:
        raise PermissionError("synthetic cost-preflight peak_rss_bytes is missing or invalid") from exc
    if peak <= 0 or peak >= RSS_LIMIT_BYTES:
        raise PermissionError("synthetic cost-preflight peak RSS exceeds the 2GiB gate")
    return dict(report)


def _real_manifest(
    prepared: Mapping[str, Any] | None,
    state: Mapping[str, Any],
    arms: Mapping[str, Any],
    invocation_status: str,
    prep_status: str,
    command: str,
    cost_preflight: Mapping[str, Any],
) -> dict[str, Any]:
    model = prepared.get("model", {}) if prepared else {}
    registry = prepared.get("registry", {}) if prepared else {}
    registry_file = prepared.get("registry_file") if prepared else None
    if isinstance(registry_file, Path):
        try:
            registry_path = str(registry_file.resolve().relative_to(REPO_ROOT))
        except ValueError:
            registry_path = str(registry_file)
    else:
        registry_path = str(registry_file) if registry_file else None
    projected = cost_preflight.get("projected_L_wall_s") if isinstance(cost_preflight, Mapping) else None
    return {
        "schema": "v72p2d2_orthogonal_oneblock_manifest_v1",
        "cycle": CYCLE_ID,
        "cycle_id": CYCLE_ID,
        "base_sha": BASE_GIT_REVISION,
        "accepted_plan_sha": state.get("accepted_plan_git_revision"),
        "implementation_sha": state.get("implementation_revision"),
        "source_registry": registry_path,
        "registry_schema": registry.get("schema") if isinstance(registry, Mapping) else None,
        "session_id": prepared.get("session", {}).get("session_id") if prepared else TARGET_SESSION,
        "block_frame_ids": list(prepared.get("block_frame_ids", TARGET_BLOCK_FRAMES)) if prepared else list(TARGET_BLOCK_FRAMES),
        "non_fresh": True,
        "mother_shape": [M, NBIT],
        "mother_nnz": NNZ,
        "checkpoint_rows": list(CHECKPOINT_ROWS),
        "max_sweeps_per_checkpoint": 10,
        "max_total_sweeps": 720,
        "llr_clip": 20.0,
        "convergence_tol": 1e-6,
        "dtype": "float64",
        "arm_order": list(ARM_ORDER),
        "invocation_status": invocation_status,
        "prep_status": prep_status,
        "cost_preflight": _json_value(cost_preflight),
        "projected_L_wall_s": _json_value(projected),
        "rss_sampling": {
            "source": "psutil.Process(os.getpid()).memory_info().rss",
            "points": ["prep", "after_each_checkpoint", "arm_end"],
            "peak_limit_bytes": RSS_LIMIT_BYTES,
        },
        "model": {
            "family": "hierarchical_M0_and_V70R1_M2",
            "selected_lambda": model.get("selected_lambda"),
            "ce_ref_log2": model.get("ce_ref_log2"),
            "m2_parameters": {
                "family": "laplace",
                "mu": 0.0,
                "scale": 0.2714417616594907,
                "eps": 0.562251256281407,
                "Q": Q,
            },
            "prior_log_base": "natural_log",
            "ce_log_base": "log2",
        },
        "interleaver": prepared.get("mapping_summary") if prepared else None,
        "arms": dict(arms),
        "tag_semantics": {"tag_bits": 0, "tag_ok": "NOT_APPLICABLE", "diagnostic": "syndrome_only"},
        "claim_boundary": (
            "One non-fresh VAL block descriptive diagnostic only; no protocol acceptance, "
            "FER, SKR, information-limit, causal graph, or promotion claim."
        ),
        "command": command,
        "no_run_01": True,
    }


def _real_results(manifest: Mapping[str, Any]) -> dict[str, Any]:
    arms = manifest.get("arms", {})
    return {
        **dict(manifest),
        "schema": "v72p2d2_orthogonal_oneblock_results_v1",
        "result_scope": "descriptive_one_block_L_I_P_diagnostic",
        "normal_new_arm_count": sum(
            arms.get(arm, {}).get("status") in {"LADDER_EXHAUSTED", "BUDGET_EXHAUSTED"}
            for arm in NEW_ARM_ORDER
        ) if isinstance(arms, Mapping) else 0,
    }


def _write_real_outputs(out_dir: str | Path, manifest: Mapping[str, Any], results: Mapping[str, Any]) -> None:
    """Write exactly the four additive diagnostic artifacts."""
    path = Path(out_dir).resolve()
    if path.exists():
        raise FileExistsError(f"output directory already exists: {path}")
    path.mkdir(parents=True, exist_ok=False)
    (path / "manifest.json").write_text(
        json.dumps(_json_value(manifest), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (path / "results.json").write_text(
        json.dumps(_json_value(results), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    fields = [
        "arm_id", "status", "graph_id", "prior_id", "schedule_id", "attempted",
        "attempted_checkpoints", "stop_reason", "first_syndrome_satisfied_ckpt",
        "final_checkpoint_rows", "final_syndrome_satisfied", "final_oracle_exact",
        "diagnostic_exact", "syndrome_collision_wrong", "sweeps_used", "edge_updates",
        "local_factor_target_updates", "state_evaluations", "diagnostic_factor_target_updates",
        "diagnostic_state_evaluations", "peak_rss_bytes", "syndrome_rows_published",
        "syndrome_bits_published", "tag_bits_published", "control_bits_sent",
        "disclosed_rows", "public_disclosure_bits",
    ]
    with (path / "table.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        arms = results.get("arms", {})
        for arm_id in ARM_ORDER:
            arm = arms.get(arm_id, {}) if isinstance(arms, Mapping) else {}
            accounting = arm.get("accounting", {}) if isinstance(arm, Mapping) else {}
            row = {key: arm.get(key) for key in fields}
            for key in (
                "syndrome_rows_published", "syndrome_bits_published", "tag_bits_published",
                "control_bits_sent", "disclosed_rows", "public_disclosure_bits",
            ):
                row[key] = accounting.get(key)
            writer.writerow({"arm_id": arm_id, **{key: row.get(key) for key in fields if key != "arm_id"}})
    lines = [
        "# V72P2D2 orthogonal one-block diagnostic",
        "",
        "This output is one non-fresh VAL block, syndrome-only, descriptive evidence.",
        "It is not protocol acceptance, FER, SKR, information-limit evidence, or promotion.",
        "",
        f"- invocation_status: `{results.get('invocation_status')}`",
        f"- prep_status: `{results.get('prep_status')}`",
        f"- new arms completed normally: `{results.get('normal_new_arm_count')}` / 3",
        "- Arm A is a read-only reuse of the accepted D1 scalar record; it was not rerun.",
        "- tag_bits=0 and tag_ok=NOT_APPLICABLE for this diagnostic.",
    ]
    for arm_id in ARM_ORDER:
        arm = results.get("arms", {}).get(arm_id, {})
        lines.append(
            f"- {arm_id}: status=`{arm.get('status')}`, stop=`{arm.get('stop_reason')}`, "
            f"final_rows=`{arm.get('final_checkpoint_rows')}`"
        )
    (path / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if {item.name for item in path.iterdir()} != {"manifest.json", "results.json", "table.csv", "report.md"}:
        raise RuntimeError("real diagnostic output root does not contain exactly four files")


def run_real_orchestration(
    *,
    registry_path: str | Path = "v71_data_registry.json",
    out_dir: str | Path = REAL_OUTPUT_ROOT,
    d1_results_path: str | Path = D1_RESULTS_PATH,
    cycle_state_path: str | Path = CYCLE_STATE_PATH,
    preflight_path: str | Path | None = DEFAULT_OUTPUT,
) -> int:
    """Execute the single authorized fixed-block L/I/P diagnostic."""
    output_path = Path(out_dir).resolve()
    # ponytail: R1 additive root only; default stays the D2 root, anything else is rejected.
    if output_path not in (REAL_OUTPUT_ROOT, R1_OUTPUT_ROOT):
        raise ValueError(f"real output root must be {REAL_OUTPUT_ROOT} or {R1_OUTPUT_ROOT}")
    state = require_real_authorization(
        execute_real=True,
        cycle_state_path=cycle_state_path,
        output_path=output_path,
    )
    # ponytail: preflight gate before any registry/parquet read, output creation, or count use.
    cost_preflight = _preflight_for_manifest(preflight_path, state)
    command = " ".join(["python", "scripts/v72p2d2_orthogonal_triage.py", *sys.argv[1:]])
    core = load_triage_module()
    # ponytail: invocation wall covers registry/CAL/block/L/I/P/report; RSS at phase boundaries.
    invocation_start = time.monotonic()
    outer_rss: list[int] = []

    def _sample_outer() -> int | None:
        try:
            value = int(core.current_rss_bytes())
        except Exception:
            return None
        outer_rss.append(value)
        return value

    _sample_outer()
    prep_start = time.monotonic()
    prepared: dict[str, Any] | None = None
    prep_elapsed: float | None = None
    try:
        prepared = _prepare_real_inputs(registry_path, d1_results_path, core)
        prep_elapsed = time.monotonic() - prep_start
        _sample_outer()
        if prep_elapsed > 600.0:
            raise TimeoutError(f"prep wall {prep_elapsed:.3f}s exceeds 600s")
        arms, invocation_status, fatal_error = run_real_invocation(prepared, core)
        prep_status = "PASS"
    except Exception as exc:
        if prep_elapsed is None:
            prep_elapsed = time.monotonic() - prep_start
        _sample_outer()
        fatal_error = f"{type(exc).__name__}: {str(exc)[:300]}"
        baseline: dict[str, Any]
        if isinstance(prepared, Mapping) and isinstance(prepared.get("a_baseline"), Mapping):
            baseline = dict(prepared["a_baseline"])
        else:
            try:
                baseline = _load_a_baseline(d1_results_path)
            except Exception:
                baseline = _not_attempted_arm("A", fatal_error)
        arms = {"A": baseline}
        for _arm in NEW_ARM_ORDER:
            arms[_arm] = _not_attempted_arm(_arm, fatal_error)
        invocation_status = "PREP_FAILED"
        prep_status = "FAILED"
    _sample_outer()
    invocation_before_report = time.monotonic() - invocation_start
    peaks = [int(v) for v in outer_rss if v is not None]
    for _arm in ARM_ORDER:
        _peak = (arms.get(_arm, {}) or {}).get("peak_rss_bytes")
        if isinstance(_peak, int) and _peak > 0:
            peaks.append(int(_peak))
    invocation_peak = max(peaks) if peaks else None
    if invocation_peak is not None and invocation_peak >= RSS_LIMIT_BYTES and invocation_status == "COMPLETED":
        invocation_status = "RESOURCE_BLOCKED"
        fatal_error = ((fatal_error + "; ") if fatal_error else "") + "peak_rss_exceeded"
    if invocation_before_report > INVOCATION_DEADLINE_S and invocation_status == "COMPLETED":
        invocation_status = "RESOURCE_BLOCKED"
        fatal_error = ((fatal_error + "; ") if fatal_error else "") + "invocation_timeout"
    manifest = _real_manifest(
        prepared,
        state,
        arms,
        invocation_status,
        prep_status,
        command,
        cost_preflight,
    )
    manifest["prep_wall_s"] = float(prep_elapsed) if prep_elapsed is not None else None
    manifest["invocation_wall_s_before_report"] = float(invocation_before_report)
    manifest["peak_rss_bytes"] = invocation_peak
    manifest["budget_gates"] = {
        "prep_limit_s": 600.0,
        "arm_limit_s": ARM_DEADLINE_S,
        "invocation_limit_s": INVOCATION_DEADLINE_S,
        "peak_limit_bytes": RSS_LIMIT_BYTES,
    }
    if fatal_error:
        manifest["fatal_error"] = fatal_error
    results = _real_results(manifest)
    _write_real_outputs(output_path, manifest, results)
    _sample_outer()
    print(json.dumps({"status": invocation_status, "output": str(output_path)}, indent=2))
    return 0 if invocation_status == "COMPLETED" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        choices=("synthetic-preflight", "real"),
        default="synthetic-preflight",
        help="synthetic preflight is the only phase enabled by default; real requires authorization",
    )
    parser.add_argument(
        "--execute-real",
        action="store_true",
        help="explicitly request the future real L/I/P path; cycle-state authorization is also required",
    )
    parser.add_argument(
        "--cycle-state",
        type=Path,
        default=CYCLE_STATE_PATH,
        help="cycle_state.yaml used only by the explicit real-execution gate",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=REPO_ROOT / "v71_data_registry.json",
        help="registry consumed only by the explicitly authorized real path",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=REAL_OUTPUT_ROOT,
        help="fixed additive real diagnostic output directory",
    )
    parser.add_argument(
        "--d1-results",
        type=Path,
        default=D1_RESULTS_PATH,
        help="accepted D1 results used for read-only Arm A reuse",
    )
    parser.add_argument(
        "--preflight",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="synthetic cost-preflight JSON recorded in the real manifest",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=SEED)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.phase == "real" and not args.execute_real:
        print("--phase real requires --execute-real; no real run was started", file=sys.stderr)
        return 2
    if args.phase != "real" and args.execute_real:
        print("--execute-real requires --phase real; no synthetic run was started", file=sys.stderr)
        return 2
    if args.phase == "real":
        try:
            return run_real_orchestration(
                registry_path=args.registry,
                out_dir=args.out_dir,
                d1_results_path=args.d1_results,
                cycle_state_path=args.cycle_state,
                preflight_path=args.preflight,
            )
        except (FileNotFoundError, FileExistsError, PermissionError, RuntimeError, ValueError) as exc:
            print(f"REAL_EXECUTION_BLOCKED: {exc}", file=sys.stderr)
            return 2
    try:
        return run_synthetic_preflight(output=args.out, seed=args.seed)
    except (FileNotFoundError, ImportError, ValueError, RuntimeError) as exc:
        print(f"SYNTHETIC_PREFLIGHT_FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
