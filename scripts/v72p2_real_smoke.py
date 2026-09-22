#!/usr/bin/env python3
"""Bounded V72P2 real-VAL descriptive smoke runner.

The default invocation is deliberately inert.  The real path is entered only
with ``--execute-real`` and reads the one registered 1M parquet file.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


Q = 1024
N = 1024
NBIT = 10240
M = 9036
FRAME_PAIRS = 256
CAL_START = 702
CAL_STOP = 1726
SMOKE_START = 1726
SMOKE_STOP = 1762
CHECKPOINT_ROWS = tuple(list(range(160, 8993, 128)) + [9032, 9036])
MAX_ITER_PER_CHECKPOINT = 10
MAX_TOTAL_ITERATIONS = 720
LLR_CLIP = 20.0
CONVERGENCE_TOL = 1e-6
PROBABILITY_FLOOR = 1e-300
BLOCK_DEADLINE_S = 600.0
INVOCATION_DEADLINE_S = 7200.0
SEED = 20260902
PAIR_COLUMNS = ["frame_id", "pair_idx", "alice_symbol", "bob_symbol"]


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REPO_ROOT = Path(__file__).resolve().parents[1]
_ADAPTER = _load_module(
    REPO_ROOT
    / "comparison_bench"
    / "src"
    / "comparison_bench"
    / "formal_ir"
    / "v72p1_soft_joint_adapter.py",
    "v72p1_soft_joint_adapter_for_v72p2",
)
_V70 = _load_module(
    REPO_ROOT / "scripts" / "v70_binary_soft_joint_feasibility.py",
    "v70_binary_soft_joint_for_v72p2",
)


class DataValidationError(ValueError):
    """A selected CAL/VAL frame cannot satisfy the fixed input contract."""


class DecoderNumericError(ValueError):
    """The decoder returned a non-finite or out-of-contract numeric value."""


def _repo_path(path: str | Path, repo_root: Path = REPO_ROOT) -> Path:
    value = Path(path)
    return value if value.is_absolute() else repo_root / value


def load_registry(path: str | Path) -> tuple[dict, Path]:
    registry_path = _repo_path(path)
    return json.loads(registry_path.read_text(encoding="utf-8")), registry_path


def select_1m_session(registry: dict) -> dict:
    sessions = [
        session
        for session in registry.get("sessions", [])
        if session.get("session_id") == "20260123_1M_600k_0dB"
        and session.get("source_label") == "1M"
    ]
    if len(sessions) != 1:
        raise DataValidationError("registry must contain exactly one target 1M session")
    return sessions[0]


def assigned_frame_groups(session: dict) -> tuple[list[int], list[list[int]]]:
    cal_ids = [int(x) for x in session.get("stage2_CAL_frame_ids", [])]
    val_ids = [int(x) for x in session.get("stage2_VAL_frame_ids", [])]
    expected_cal = list(range(CAL_START, CAL_STOP))
    expected_smoke = list(range(SMOKE_START, SMOKE_STOP))
    if cal_ids != expected_cal:
        raise DataValidationError("CAL assignment is not the frozen 702..1725 sequence")
    if val_ids[: len(expected_smoke)] != expected_smoke:
        raise DataValidationError("VAL assignment does not start with frozen 1726..1761")
    groups = [
        val_ids[offset : offset + 4]
        for offset in range(0, len(expected_smoke), 4)
    ]
    if len(groups) != 9 or any(len(group) != 4 for group in groups):
        raise DataValidationError("smoke assignment must contain nine four-frame groups")
    if any(group != list(range(group[0], group[0] + 4)) for group in groups):
        raise DataValidationError("each smoke group must contain consecutive frame IDs")
    return cal_ids, groups


def read_selected_pairs(
    pairs_path: str | Path,
    frame_ids: list[int],
    reader=None,
) -> tuple[pd.DataFrame, str]:
    """Read only the selected columns and frame IDs from the registered file."""
    if reader is None:
        reader = pd.read_parquet
    path = Path(pairs_path)
    filters = [("frame_id", "in", [int(fid) for fid in frame_ids])]
    frame = reader(path, columns=PAIR_COLUMNS, filters=filters)
    return frame, "predicate_pushdown"


def _integer_column(frame: pd.DataFrame, name: str) -> np.ndarray:
    values = pd.to_numeric(frame[name], errors="coerce").to_numpy(dtype=np.float64)
    if (
        values.size == 0
        or not np.all(np.isfinite(values))
        or not np.all(values == np.floor(values))
    ):
        raise DataValidationError(f"{name} contains missing or non-integral values")
    return values.astype(np.int32)


def validate_frame(frame: pd.DataFrame, frame_id: int) -> dict[str, np.ndarray]:
    missing = [column for column in PAIR_COLUMNS if column not in frame.columns]
    if missing:
        raise DataValidationError(f"missing columns: {missing}")
    selected = frame.loc[frame["frame_id"] == int(frame_id), PAIR_COLUMNS].copy()
    if len(selected) != FRAME_PAIRS:
        raise DataValidationError(
            f"frame {frame_id} has {len(selected)} rows, expected {FRAME_PAIRS}"
        )
    pair_idx = _integer_column(selected, "pair_idx")
    if len(np.unique(pair_idx)) != FRAME_PAIRS:
        raise DataValidationError(f"frame {frame_id} pair_idx values are not distinct")
    order = np.argsort(pair_idx, kind="stable")
    alice = _integer_column(selected, "alice_symbol")[order]
    bob = _integer_column(selected, "bob_symbol")[order]
    if (
        np.any(alice < 0)
        or np.any(alice >= Q)
        or np.any(bob < 0)
        or np.any(bob >= Q)
    ):
        raise DataValidationError(f"frame {frame_id} contains a symbol outside 0..1023")
    return {"alice_symbols": alice, "bob_symbols": bob}


def validate_selected_frames(
    frame: pd.DataFrame, frame_ids: list[int]
) -> tuple[dict[int, dict[str, np.ndarray]], dict[int, str]]:
    valid: dict[int, dict[str, np.ndarray]] = {}
    errors: dict[int, str] = {}
    for frame_id in frame_ids:
        try:
            valid[int(frame_id)] = validate_frame(frame, int(frame_id))
        except DataValidationError as exc:
            errors[int(frame_id)] = str(exc)
    return valid, errors


def assemble_frame_group(
    frames: dict[int, dict[str, np.ndarray]], frame_ids: list[int]
) -> tuple[np.ndarray, np.ndarray]:
    if any(int(frame_id) not in frames for frame_id in frame_ids):
        raise DataValidationError("cannot assemble a group with an invalid frame")
    alice = np.concatenate([frames[int(fid)]["alice_symbols"] for fid in frame_ids])
    bob = np.concatenate([frames[int(fid)]["bob_symbols"] for fid in frame_ids])
    if alice.shape != (N,) or bob.shape != (N,):
        raise DataValidationError("a four-frame group must contain 1024 symbols")
    return alice.astype(np.int32), bob.astype(np.int32)


def symbols_to_bits(symbols: np.ndarray) -> np.ndarray:
    values = np.asarray(symbols, dtype=np.int32)
    if values.shape != (N,) or np.any(values < 0) or np.any(values >= Q):
        raise ValueError("symbols must have shape (1024,) and lie in 0..1023")
    return ((values[:, None] >> np.arange(10, dtype=np.int32)) & 1).astype(np.uint8).reshape(
        NBIT
    )


def fit_full_cal_model(a_cal: np.ndarray, b_cal: np.ndarray) -> dict:
    """Select lambda on CAL folds and refit the hierarchical model on all CAL."""
    a = np.asarray(a_cal, dtype=np.int32)
    b = np.asarray(b_cal, dtype=np.int32)
    if a.shape != b.shape or a.ndim != 1 or len(a) == 0:
        raise DataValidationError("CAL arrays must be non-empty one-dimensional pairs")
    if np.any(a < 0) or np.any(a >= Q) or np.any(b < 0) or np.any(b >= Q):
        raise DataValidationError("CAL symbols must lie in 0..1023")
    lam_star, cv_scores, ce_ref, boundary = _V70.select_lambda(a, b)
    counts = np.zeros((Q, Q), dtype=np.int32)
    np.add.at(counts, (b, a), 1)
    n_b = counts.sum(axis=1).astype(np.float64)
    p_global = counts.sum(axis=0).astype(np.float64) / float(len(a))
    probabilities = np.asarray(
        _V70.hierarchical_P(counts, p_global, n_b, lam_star), dtype=np.float64
    )
    probabilities = np.maximum(probabilities, PROBABILITY_FLOOR)
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    if not np.all(np.isfinite(probabilities)):
        raise DataValidationError("CAL model produced non-finite probabilities")
    return {
        "selected_lambda": float(lam_star),
        "lambda_cv_scores": {str(float(k)): float(v) for k, v in cv_scores.items()},
        "ce_ref_log2": float(ce_ref),
        "ce_ref_definition": (
            "selected CAL-CV cross-entropy in log2; selection-conditioned model "
            "reference, not Shannon entropy or independent validation"
        ),
        "lambda_at_boundary": bool(boundary),
        "probability_floor": PROBABILITY_FLOOR,
        "Ps_full": probabilities,
    }


def build_prior_logp(bob_symbols: np.ndarray, probabilities: np.ndarray) -> np.ndarray:
    """Build the natural-log BP prior from Bob symbols only."""
    bob = np.asarray(bob_symbols, dtype=np.int32)
    p = np.asarray(probabilities, dtype=np.float64)
    if bob.shape != (N,) or p.shape != (Q, Q):
        raise ValueError("Bob symbols/prior model have an unexpected shape")
    if np.any(bob < 0) or np.any(bob >= Q):
        raise ValueError("Bob symbols must lie in 0..1023")
    rows = np.maximum(p[bob], PROBABILITY_FLOOR)
    rows /= rows.sum(axis=1, keepdims=True)
    return np.log(rows).astype(np.float64)


def smoke_cross_entropy(
    alice_symbols: np.ndarray, bob_symbols: np.ndarray, probabilities: np.ndarray
) -> float:
    alice = np.asarray(alice_symbols, dtype=np.int32)
    bob = np.asarray(bob_symbols, dtype=np.int32)
    p = np.asarray(probabilities, dtype=np.float64)
    if alice.shape != (N,) or bob.shape != (N,) or p.shape != (Q, Q):
        raise ValueError("smoke CE inputs have an unexpected shape")
    likelihood = np.maximum(p[bob, alice], PROBABILITY_FLOOR)
    return float(-np.log2(likelihood).mean())


def get_mother_csr() -> tuple[np.ndarray, np.ndarray, int]:
    return _ADAPTER.get_mother_csr()


def derive_public(
    alice_bits: np.ndarray, indptr: np.ndarray, indices: np.ndarray
) -> tuple[np.ndarray, bytes]:
    bits = np.asarray(alice_bits, dtype=np.uint8)
    indptr = np.asarray(indptr, dtype=np.int32)
    indices = np.asarray(indices, dtype=np.int32)
    if bits.shape != (NBIT,):
        raise ValueError("Alice bits must have shape (10240,)")
    syndrome = np.zeros(len(indptr) - 1, dtype=np.uint8)
    for check in range(len(syndrome)):
        start, end = int(indptr[check]), int(indptr[check + 1])
        parity = 0
        for variable in indices[start:end]:
            parity ^= int(bits[int(variable)])
        syndrome[check] = np.uint8(parity)
    reference_tag = hashlib.sha256(bits.tobytes()).digest()[:8]
    return syndrome, reference_tag


def candidate_tag(hard_bits: np.ndarray) -> bytes:
    bits = np.asarray(hard_bits, dtype=np.uint8)
    if bits.shape != (NBIT,):
        raise ValueError("candidate hard_bits must have shape (10240,)")
    return hashlib.sha256(bits.tobytes()).digest()[:8]


def available_iterations(
    total_used: int,
    max_iter_per_checkpoint: int = MAX_ITER_PER_CHECKPOINT,
    max_total_iterations: int = MAX_TOTAL_ITERATIONS,
) -> int:
    return max(0, min(int(max_iter_per_checkpoint), int(max_total_iterations) - int(total_used)))


def _empty_block(block_id: int, frame_ids: list[int], status: str = "NOT_ATTEMPTED") -> dict:
    return {
        "block_id": int(block_id),
        "frame_ids": [int(x) for x in frame_ids],
        "status": status,
        "attempted": False,
        "disclosed_rows": 0,
        "syndrome_bits_published": 0,
        "tag_bits_published": 0,
        "control_bits_sent": 0,
        "leak_IR_bits": 0,
        "total_public_bits": 0,
        "iterations_used": 0,
        "protocol_accepted": False,
        "verified_exact_success": False,
        "undetected": False,
        "oracle_exact": None,
        "raw_bit_errors": None,
        "raw_symbol_errors": None,
        "bit_errors": None,
        "symbol_errors": None,
        "frame_row_count": 0,
        "valid_frame_count": 0,
        "frame_row_counts": {},
        "smoke_ce_log2": None,
        "elapsed_s": 0.0,
        "deadline_overrun": False,
        "f_model_relative": None,
        "f_public_model_relative": None,
        "per_checkpoint": [],
        "error": None,
    }


def _finish_block(block: dict, ce_ref: float | None) -> dict:
    block["leak_IR_bits"] = int(
        block["syndrome_bits_published"] + block["tag_bits_published"]
    )
    block["total_public_bits"] = int(block["leak_IR_bits"] + block["control_bits_sent"])
    if block["attempted"] and ce_ref is not None and np.isfinite(ce_ref) and ce_ref > 0:
        denominator = float(N * ce_ref)
        block["f_model_relative"] = block["leak_IR_bits"] / denominator
        block["f_public_model_relative"] = block["total_public_bits"] / denominator
    return block


def run_block(
    block_id: int,
    frame_ids: list[int],
    alice_bits: np.ndarray,
    prior_logp: np.ndarray,
    syndrome_full: np.ndarray,
    reference_tag: bytes,
    indptr: np.ndarray,
    indices: np.ndarray,
    *,
    decoder,
    bob_symbols: np.ndarray | None = None,
    checkpoint_rows: tuple[int, ...] = CHECKPOINT_ROWS,
    max_iter_per_checkpoint: int = MAX_ITER_PER_CHECKPOINT,
    max_total_iterations: int = MAX_TOTAL_ITERATIONS,
    deadline_s: float = BLOCK_DEADLINE_S,
    clock=None,
    ce_ref: float | None = None,
) -> dict:
    """Run one assigned block with an injectable decoder for fake tests."""
    bits = np.asarray(alice_bits, dtype=np.uint8)
    bob = None if bob_symbols is None else np.asarray(bob_symbols, dtype=np.int32)
    prior = np.asarray(prior_logp, dtype=np.float64)
    target = np.asarray(syndrome_full, dtype=np.uint8)
    indptr = np.asarray(indptr, dtype=np.int32)
    indices = np.asarray(indices, dtype=np.int32)
    if bits.shape != (NBIT,) or prior.shape != (N, Q):
        raise ValueError("block input shapes do not match the frozen contract")
    if bob is not None:
        if bob.shape != (N,) or np.any(bob < 0) or np.any(bob >= Q):
            raise ValueError("Bob symbols must have shape (1024,) and lie in 0..1023")
    if len(target) < max(checkpoint_rows):
        raise ValueError("syndrome target is shorter than checkpoint ladder")
    if clock is None:
        clock = time.monotonic
    block = _empty_block(block_id, frame_ids)
    started = float(clock())
    c2v = np.zeros(0, dtype=np.float64)
    previous_nnz = 0
    disclosed_rows = 0
    iterations_used = 0
    last_hard_bits = None
    deadline_overrun = False

    for checkpoint_index, checkpoint in enumerate(checkpoint_rows):
        checkpoint = int(checkpoint)
        remaining = available_iterations(
            iterations_used, max_iter_per_checkpoint, max_total_iterations
        )
        elapsed_before = float(clock()) - started
        if remaining <= 0:
            block["status"] = "BUDGET_EXHAUSTED"
            break
        if elapsed_before >= float(deadline_s):
            block["status"] = "TIMEOUT"
            block["error"] = "block deadline before checkpoint publication"
            break
        if checkpoint <= disclosed_rows or checkpoint > M:
            raise ValueError("checkpoint ladder is not strictly increasing and bounded")

        if checkpoint_index:
            block["control_bits_sent"] += 1
        new_rows = checkpoint - disclosed_rows
        disclosed_rows = checkpoint
        block["disclosed_rows"] = disclosed_rows
        block["syndrome_bits_published"] = disclosed_rows
        if block["tag_bits_published"] == 0:
            block["tag_bits_published"] = 64
        block["attempted"] = True

        active_nnz = int(indptr[checkpoint])
        if active_nnz < previous_nnz or active_nnz > len(indices):
            raise ValueError("CSR active edge prefix is invalid")
        warm = np.zeros(active_nnz, dtype=np.float64)
        if previous_nnz:
            warm[:previous_nnz] = c2v[:previous_nnz]
        max_iter = available_iterations(
            iterations_used, max_iter_per_checkpoint, max_total_iterations
        )
        residuals = []
        completed_iterations = None
        try:
            returned = decoder(
                prior,
                target[:checkpoint],
                indptr=indptr[: checkpoint + 1],
                indices=indices[:active_nnz],
                max_iter=max_iter,
                warm_start_c2v=warm,
            )
            residuals = [float(x) for x in returned["residuals"]]
            if not residuals:
                raise ValueError("decoder returned an invalid residual trajectory")
            completed_iterations = len(residuals)
            iterations_used += completed_iterations
            if completed_iterations > max_iter:
                raise ValueError("decoder returned too many iterations")
            if any(not np.isfinite(value) or value < 0 for value in residuals):
                raise DecoderNumericError("decoder residual trajectory is non-finite")
            candidate_c2v = np.asarray(returned["check_to_variable"], dtype=np.float64)
            if candidate_c2v.shape != (active_nnz,):
                raise ValueError("decoder returned an invalid active c2v shape")
            if not np.all(np.isfinite(candidate_c2v)):
                raise DecoderNumericError("decoder c2v is non-finite")
            hard = np.asarray(returned["hard_bits"], dtype=np.uint8)
            if hard.shape != (NBIT,):
                raise ValueError("decoder returned invalid hard_bits")
            observed = np.asarray(returned["syndrome_observed"], dtype=np.uint8)
            syndrome_ok = observed.shape == (checkpoint,) and np.array_equal(
                observed, target[:checkpoint]
            )
            max_llr = float(returned.get("max_llr", float("nan")))
            if not np.isfinite(max_llr) or max_llr > LLR_CLIP + 1e-12:
                raise DecoderNumericError("decoder max_llr is non-finite or exceeds clip")
            if "app_llr" in returned:
                app = np.asarray(returned["app_llr"], dtype=np.float64)
                if app.shape != (NBIT,) or not np.all(np.isfinite(app)):
                    raise DecoderNumericError("decoder app_llr is non-finite")
                if float(np.max(np.abs(app))) > LLR_CLIP + 1e-12:
                    raise DecoderNumericError("decoder app_llr exceeds clip")
            finite = bool(returned["finite"])
            tag_is_checked = True
            tag_ok = candidate_tag(hard) == reference_tag
            protocol_accepted = bool(finite and syndrome_ok and tag_ok)
            elapsed_after = float(clock()) - started
            deadline_overrun = bool(elapsed_after > float(deadline_s))
            if deadline_overrun:
                block["deadline_overrun"] = True
            c2v = candidate_c2v.copy()
            previous_nnz = active_nnz
            last_hard_bits = hard.copy()
            residual = residuals[-1]
            checkpoint_log = {
                "checkpoint_rows": checkpoint,
                "new_rows": int(new_rows),
                "disclosed_rows": int(disclosed_rows),
                "syndrome_bits_published": int(block["syndrome_bits_published"]),
                "tag_bits_published": int(block["tag_bits_published"]),
                "control_bits_sent": int(block["control_bits_sent"]),
                "iterations": len(residuals),
                "total_iterations": int(iterations_used),
                "residuals": residuals,
                "residual": residual,
                "converged": bool(residual < CONVERGENCE_TOL),
                "finite": finite,
                "max_llr": max_llr,
                "syndrome_ok": bool(syndrome_ok),
                "tag_checked": tag_is_checked,
                "tag_ok": bool(tag_ok),
                "protocol_accepted": protocol_accepted,
                "elapsed_s": elapsed_after,
                "deadline_overrun": deadline_overrun,
            }
            block["per_checkpoint"].append(checkpoint_log)
            if protocol_accepted:
                block["status"] = (
                    "VERIFIED_DEADLINE_OVERRUN" if deadline_overrun else "VERIFIED"
                )
                block["protocol_accepted"] = True
                break
            if not finite:
                block["status"] = "NUMERIC_FAILURE"
                block["error"] = "decoder returned finite=false"
                break
            if elapsed_after > float(deadline_s):
                block["status"] = "TIMEOUT"
                block["error"] = "block deadline after checkpoint"
                break
            if iterations_used >= int(max_total_iterations):
                block["status"] = (
                    "LADDER_EXHAUSTED"
                    if checkpoint == int(checkpoint_rows[-1])
                    else "BUDGET_EXHAUSTED"
                )
                break
        except Exception as exc:
            elapsed_after = float(clock()) - started
            if isinstance(exc, DecoderNumericError):
                block["status"] = "NUMERIC_FAILURE"
            else:
                block["status"] = "DECODER_ERROR"
            if elapsed_after > float(deadline_s):
                block["deadline_overrun"] = True
            block["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
            block["per_checkpoint"].append(
                {
                    "checkpoint_rows": checkpoint,
                    "new_rows": int(new_rows),
                    "disclosed_rows": int(disclosed_rows),
                    "syndrome_bits_published": int(block["syndrome_bits_published"]),
                    "tag_bits_published": int(block["tag_bits_published"]),
                    "control_bits_sent": int(block["control_bits_sent"]),
                    "iterations": completed_iterations,
                    "iterations_known": completed_iterations is not None,
                    "total_iterations": int(iterations_used),
                    "residuals": residuals,
                    "residual": residuals[-1] if residuals else None,
                    "converged": False,
                    "finite": False,
                    "max_llr": None,
                    "syndrome_ok": False,
                    "tag_checked": False,
                    "tag_ok": False,
                    "protocol_accepted": False,
                    "elapsed_s": elapsed_after,
                    "deadline_overrun": bool(elapsed_after > float(deadline_s)),
                }
            )
            break
    else:
        block["status"] = "LADDER_EXHAUSTED"

    block["iterations_used"] = int(iterations_used)
    block["elapsed_s"] = float(clock()) - started
    block["deadline_overrun"] = bool(block["deadline_overrun"] or deadline_overrun)
    if bob is not None:
        bob_bits = symbols_to_bits(bob)
        block["raw_bit_errors"] = int(np.count_nonzero(bob_bits != bits))
        block["raw_symbol_errors"] = int(
            np.count_nonzero(bob != bits.reshape(N, 10).dot(1 << np.arange(10)) )
        )
    if last_hard_bits is not None:
        alice = bits
        block["oracle_exact"] = bool(np.array_equal(last_hard_bits, alice))
        block["bit_errors"] = int(np.count_nonzero(last_hard_bits != alice))
        block["symbol_errors"] = int(
            np.count_nonzero(
                last_hard_bits.reshape(N, 10).dot(1 << np.arange(10))
                != alice.reshape(N, 10).dot(1 << np.arange(10))
            )
        )
        block["verified_exact_success"] = bool(
            block["protocol_accepted"] and block["oracle_exact"]
        )
        block["undetected"] = bool(
            block["protocol_accepted"] and not block["oracle_exact"]
        )
    return _finish_block(block, ce_ref)


def _cycle_state(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def _git_head() -> str:
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("cannot bind runtime to git HEAD") from exc
    if len(head) != 40:
        raise RuntimeError("git HEAD is not a 40-character commit SHA")
    return head


def _json_default(value):
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(type(value).__name__)


def _results_payload(
    rows: list[dict],
    fatal_error: str | None = None,
    ce_ref: float | None = None,
    invocation_elapsed_s: float | None = None,
) -> dict:
    attempted = [row for row in rows if row["attempted"]]
    accepted = [row for row in rows if row["verified_exact_success"]]
    denominator_all = len(attempted) * N * ce_ref if ce_ref and ce_ref > 0 else None
    denominator_success = len(accepted) * N * ce_ref if ce_ref and ce_ref > 0 else None
    sum_leak_all = sum(row["leak_IR_bits"] for row in attempted)
    sum_public_all = sum(row["total_public_bits"] for row in attempted)
    sum_leak_success = sum(row["leak_IR_bits"] for row in accepted)
    sum_public_success = sum(row["total_public_bits"] for row in accepted)
    smoke_ce_values = [row["smoke_ce_log2"] for row in rows if row["smoke_ce_log2"] is not None]
    ratio = lambda numerator, denominator: numerator / denominator if denominator else None
    return {
        "schema": "v72p2_val_descriptive_smoke_v1",
        "lifecycle": "DEVELOPMENT_EXECUTION / DESCRIPTIVE_ONLY",
        "overall": "COMPLETED" if not fatal_error and all(row["status"] != "NOT_ATTEMPTED" for row in rows) else "INCOMPLETE",
        "fatal_error": fatal_error,
        "invocation_elapsed_s": invocation_elapsed_s,
        "assigned_blocks": rows,
        "assigned_count": len(rows),
        "attempted_count": len(attempted),
        "verified_count": sum(row["protocol_accepted"] for row in rows),
        "verified_exact_success_count": sum(row["verified_exact_success"] for row in rows),
        "undetected_count": sum(row["undetected"] for row in rows),
        "invalid_input_count": sum(row["status"] == "INVALID_INPUT" for row in rows),
        "not_attempted_count": sum(row["status"] == "NOT_ATTEMPTED" for row in rows),
        "aggregate": {
            "all_attempts": {
                "blocks": len(attempted),
                "leak_IR_bits_sum": sum_leak_all,
                "total_public_bits_sum": sum_public_all,
                "f_model_relative": ratio(sum_leak_all, denominator_all),
                "f_public_model_relative": ratio(sum_public_all, denominator_all),
            },
            "success_conditional": {
                "blocks": len(accepted),
                "leak_IR_bits_sum": sum_leak_success,
                "total_public_bits_sum": sum_public_success,
                "f_model_relative": ratio(sum_leak_success, denominator_success),
                "f_public_model_relative": ratio(sum_public_success, denominator_success),
            },
            "smoke_ce_log2_mean": float(np.mean(smoke_ce_values)) if smoke_ce_values else None,
            "ce_ref_log2": ce_ref,
        },
    }


def _manifest(
    registry: dict | None,
    registry_path: Path,
    session: dict | None,
    cal_ids: list[int] | None,
    groups: list[list[int]] | None,
    model: dict | None,
    read_mode: str | None,
    fatal_error: str | None,
    git_head: str | None,
    command: str,
) -> dict:
    state = _cycle_state(REPO_ROOT / "docs" / "research_cycles" / "V72P2-VAL" / "cycle_state.yaml")
    return {
        "schema": "v72p2_val_descriptive_smoke_manifest_v1",
        "cycle_id": "V72P2-VAL",
        "git_head": git_head,
        "git_binding": "VERIFIED" if git_head else "FAILED",
        "accepted_plan_sha": state.get("accepted_plan_sha"),
        "implementation_sha": state.get("implementation_sha"),
        "registry_path": str(registry_path.relative_to(REPO_ROOT)) if registry_path.is_relative_to(REPO_ROOT) else str(registry_path),
        "registry_schema": registry.get("schema") if registry else None,
        "data_sha": registry.get("data_sha") if registry else None,
        "session_id": session.get("session_id") if session else None,
        "source_label": session.get("source_label") if session else None,
        "provenance": session.get("provenance") if session else None,
        "cal_frame_ids": cal_ids,
        "smoke_frame_groups": groups,
        "data_roles": {"CAL": "fit_and_select", "SMOKE": "non_fresh_descriptive_VAL"},
        "read_mode": read_mode,
        "model": {
            key: value for key, value in (model or {}).items() if key != "Ps_full"
        },
        "decoder": {
            "checkpoint_rows": list(CHECKPOINT_ROWS),
            "max_iter_per_checkpoint": MAX_ITER_PER_CHECKPOINT,
            "max_total_iterations": MAX_TOTAL_ITERATIONS,
            "llr_clip": LLR_CLIP,
            "convergence_tol": CONVERGENCE_TOL,
            "warm_start": True,
            "mother_rows": M,
            "mother_columns": NBIT,
            "mother_nnz": 49620,
        },
        "seed": SEED,
        "command": command,
        "communication": {
            "first_syndrome_rows": 160,
            "tag_bits": 64,
            "continue_bits": "one before each later checkpoint",
            "excluded_bits": ["ACK", "header", "authentication", "transport"],
        },
        "budgets": {
            "block_seconds": BLOCK_DEADLINE_S,
            "invocation_seconds": INVOCATION_DEADLINE_S,
        },
        "non_fresh": True,
        "no_run_01": True,
        "fatal_error": fatal_error,
    }


def _write_outputs(out_dir: Path, manifest: dict, results: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )
    (out_dir / "results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )
    fields = [
        "block_id",
        "frame_ids",
        "status",
        "attempted",
        "disclosed_rows",
        "syndrome_bits_published",
        "tag_bits_published",
        "control_bits_sent",
        "leak_IR_bits",
        "total_public_bits",
        "iterations_used",
        "elapsed_s",
        "frame_row_count",
        "valid_frame_count",
        "smoke_ce_log2",
        "protocol_accepted",
        "verified_exact_success",
        "undetected",
        "oracle_exact",
        "raw_bit_errors",
        "raw_symbol_errors",
        "bit_errors",
        "symbol_errors",
        "f_model_relative",
        "f_public_model_relative",
        "error",
    ]
    with (out_dir / "table.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in results["assigned_blocks"]:
            record = {key: row.get(key) for key in fields}
            record["frame_ids"] = ";".join(str(x) for x in row["frame_ids"])
            writer.writerow(record)
    lines = [
        "# V72P2 real VAL-reuse descriptive smoke",
        "",
        "This is a bounded, non-fresh descriptive smoke; it is not confirmation, FER, SKR, qualification, or promotion.",
        "",
        f"- overall: `{results['overall']}`",
        f"- assigned blocks: {results['assigned_count']}; attempted: {results['attempted_count']}",
        f"- protocol-accepted blocks: {results['verified_count']}",
        f"- exact accepted blocks: {results['verified_exact_success_count']}",
        f"- accepted-wrong (undetected) blocks: {results['undetected_count']}",
        f"- invalid assigned blocks: {results['invalid_input_count']}",
        f"- not attempted: {results['not_attempted_count']}",
        f"- invocation wall time including CAL: `{results['invocation_elapsed_s']}` s",
        "- `leak_IR_bits` and `total_public_bits` are kept separate; model-relative ratios use the selected CAL-CV CE.",
    ]
    aggregate = results["aggregate"]
    lines.extend(
        [
            f"- all-attempt model-relative ratio: `{aggregate['all_attempts']['f_model_relative']}`",
            f"- success-conditional model-relative ratio: `{aggregate['success_conditional']['f_model_relative']}`",
            f"- posthoc smoke CE (log2) mean: `{aggregate['smoke_ce_log2_mean']}`",
        ]
    )
    if results.get("fatal_error"):
        lines.extend(["", f"- retained stop reason: `{results['fatal_error']}`"])
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def execute_real(
    registry_path: str | Path,
    out_dir: str | Path,
    *,
    block_deadline_s: float = BLOCK_DEADLINE_S,
    invocation_deadline_s: float = INVOCATION_DEADLINE_S,
) -> int:
    output_path = _repo_path(out_dir)
    if output_path.exists():
        raise FileExistsError(f"output directory already exists: {output_path}")
    output_path.mkdir(parents=True)
    invocation_started = time.monotonic()
    registry_file = _repo_path(registry_path)
    command = " ".join(["python", "scripts/v72p2_real_smoke.py", *sys.argv[1:]])
    registry: dict | None = None
    session: dict | None = None
    cal_ids: list[int] | None = None
    groups: list[list[int]] | None = None
    model: dict | None = None
    read_mode: str | None = None
    rows: list[dict] = []
    fatal_error: str | None = None

    # Bind the run to the current source before reading data or calling a
    # decoder.  The cached value is reused for every retained artifact.
    try:
        git_head = _git_head()
    except Exception as exc:
        fatal_error = f"GIT_BINDING_FAILURE: {type(exc).__name__}: {str(exc)[:200]}"
        _write_outputs(
            output_path,
            _manifest(
                registry,
                registry_file,
                session,
                cal_ids,
                groups,
                model,
                read_mode,
                fatal_error,
                None,
                command,
            ),
            _results_payload(rows, fatal_error, invocation_elapsed_s=time.monotonic() - invocation_started),
        )
        return 1

    try:
        registry, registry_file = load_registry(registry_path)
        session = select_1m_session(registry)
        cal_ids, groups = assigned_frame_groups(session)
        rows = [_empty_block(index, frame_ids) for index, frame_ids in enumerate(groups)]
        selected_ids = cal_ids + [frame_id for group in groups for frame_id in group]
        pairs_path = _repo_path(session["provenance"])
        frame, read_mode = read_selected_pairs(pairs_path, selected_ids)
        cal_frames, cal_errors = validate_selected_frames(frame, cal_ids)
        if cal_errors:
            raise DataValidationError(f"invalid CAL frame: {next(iter(cal_errors.values()))}")
        smoke_ids = [frame_id for group in groups for frame_id in group]
        smoke_frames, _ = validate_selected_frames(frame, smoke_ids)
        a_cal = np.concatenate([cal_frames[fid]["alice_symbols"] for fid in cal_ids])
        b_cal = np.concatenate([cal_frames[fid]["bob_symbols"] for fid in cal_ids])
        model = fit_full_cal_model(a_cal, b_cal)
        indptr, indices, nnz = get_mother_csr()
        if int(nnz) != 49620 or len(indptr) != M + 1:
            raise DataValidationError("mother CSR does not match the frozen 9036x10240 graph")
        for block_id, frame_ids in enumerate(groups):
            row = rows[block_id]
            row["frame_row_counts"] = {
                str(fid): int(frame.loc[frame["frame_id"] == fid].shape[0])
                for fid in frame_ids
            }
            row["frame_row_count"] = int(sum(row["frame_row_counts"].values()))
            row["valid_frame_count"] = int(sum(fid in smoke_frames for fid in frame_ids))
            if time.monotonic() - invocation_started >= float(invocation_deadline_s):
                fatal_error = "INVOCATION_TIMEOUT"
                break
            invalid = [fid for fid in frame_ids if fid not in smoke_frames]
            if invalid:
                row["status"] = "INVALID_INPUT"
                row["error"] = f"assigned frame {invalid[0]} is invalid"
                rows[block_id] = _finish_block(row, model["ce_ref_log2"])
                _write_outputs(
                    output_path,
                    _manifest(registry, registry_file, session, cal_ids, groups, model, read_mode, fatal_error, git_head, command),
                    _results_payload(rows, fatal_error, model["ce_ref_log2"], time.monotonic() - invocation_started),
                )
                continue
            alice_symbols, bob_symbols = assemble_frame_group(smoke_frames, frame_ids)
            alice_bits = symbols_to_bits(alice_symbols)
            syndrome, reference = derive_public(alice_bits, indptr, indices)
            prior = build_prior_logp(bob_symbols, model["Ps_full"])
            remaining_invocation = float(invocation_deadline_s) - (
                time.monotonic() - invocation_started
            )
            if remaining_invocation <= 0:
                fatal_error = "INVOCATION_TIMEOUT"
                break
            rows[block_id] = run_block(
                block_id,
                frame_ids,
                alice_bits,
                prior,
                syndrome,
                reference,
                indptr,
                indices,
                decoder=_ADAPTER.run_decoder,
                bob_symbols=bob_symbols,
                deadline_s=min(float(block_deadline_s), remaining_invocation),
                ce_ref=model["ce_ref_log2"],
            )
            rows[block_id]["frame_row_count"] = N
            rows[block_id]["valid_frame_count"] = len(frame_ids)
            rows[block_id]["frame_row_counts"] = {str(fid): FRAME_PAIRS for fid in frame_ids}
            rows[block_id]["smoke_ce_log2"] = smoke_cross_entropy(
                alice_symbols, bob_symbols, model["Ps_full"]
            )
            print(f"[V72P2] block {block_id + 1}/9: {rows[block_id]['status']}", flush=True)
            _write_outputs(
                output_path,
                _manifest(registry, registry_file, session, cal_ids, groups, model, read_mode, fatal_error, git_head, command),
                _results_payload(rows, fatal_error, model["ce_ref_log2"], time.monotonic() - invocation_started),
            )
            if rows[block_id]["status"] in {
                "NUMERIC_FAILURE",
                "DECODER_ERROR",
                "TIMEOUT",
                "BUDGET_EXHAUSTED",
                "VERIFIED_DEADLINE_OVERRUN",
            }:
                fatal_error = rows[block_id]["status"]
                break
            if rows[block_id]["deadline_overrun"]:
                fatal_error = "DEADLINE_OVERRUN"
                break
            if time.monotonic() - invocation_started >= float(invocation_deadline_s):
                fatal_error = "INVOCATION_TIMEOUT"
                break
        if fatal_error:
            for index in range(9):
                if rows[index]["status"] == "NOT_ATTEMPTED":
                    rows[index]["error"] = fatal_error
    except Exception as exc:
        fatal_error = f"{type(exc).__name__}: {str(exc)[:300]}"
    finally:
        _write_outputs(
            output_path,
            _manifest(registry, registry_file, session, cal_ids, groups, model, read_mode, fatal_error, git_head, command),
            _results_payload(rows, fatal_error, model["ce_ref_log2"] if model else None, time.monotonic() - invocation_started),
        )
    return 1 if fatal_error else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default="v71_data_registry.json")
    parser.add_argument(
        "--out-dir",
        default="comparison_bench/outputs_comparison/v72p2_val_descriptive_smoke_20260903",
    )
    parser.add_argument("--execute-real", action="store_true")
    args = parser.parse_args(argv)
    if not args.execute_real:
        print("V72P2 real execution is disabled; pass --execute-real after Pre-EXECUTE.")
        return 0
    try:
        return execute_real(args.registry, args.out_dir)
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
