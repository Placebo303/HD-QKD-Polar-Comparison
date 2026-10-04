"""Research-only natural and residual-ranked GF(32) row-layered loops."""
from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable

import numpy as np

from comparison_bench.formal_ir import v35_algorithm_development as v35


@dataclass(frozen=True)
class ResidualSweepResult:
    """Decoder output plus the work and row-order trace for this research loop."""

    x_hat: np.ndarray
    syndrome_ok: bool
    iterations: int
    runtime_s: float
    status: str
    final_beliefs: np.ndarray
    belief_provenance: str
    extrinsic_log_beliefs: np.ndarray
    extrinsic_provenance: str
    row_orders: tuple[tuple[int, ...], ...]
    first_sweep_residuals: tuple[float, ...]
    score_check_updates: int
    applied_check_updates: int
    score_edge_updates: int
    applied_edge_updates: int


def _checked_inputs(h_matrix: Any, priors: Any, syndrome: Any) -> tuple[
        np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[np.ndarray],
        list[list[int]]]:
    raw_h = np.asarray(h_matrix)
    raw_syndrome = np.asarray(syndrome).ravel()
    if raw_h.ndim != 2 or raw_h.shape[0] < 1 or raw_h.shape[1] < 1:
        raise ValueError("H must be a nonempty two-dimensional matrix")
    if raw_syndrome.shape != (raw_h.shape[0],):
        raise ValueError("syndrome shape must match H rows")
    if (not np.issubdtype(raw_h.dtype, np.integer)
            or not np.issubdtype(raw_syndrome.dtype, np.integer)
            or np.any(raw_h < 0) or np.any(raw_h >= v35.FIELD_Q)
            or np.any(raw_syndrome < 0) or np.any(raw_syndrome >= v35.FIELD_Q)):
        raise ValueError("H and syndrome must contain GF(32) symbols")
    matrix = raw_h.astype(np.uint8, copy=True)
    target = raw_syndrome.astype(np.uint8, copy=True)

    # Match v35 exactly: floor once, then normalize each row once. Keep the
    # caller's raw prior untouched so a separate v35 reference receives it raw.
    clean = np.maximum(np.asarray(priors, dtype=np.float64), 1e-15)
    if clean.shape != (matrix.shape[1], v35.FIELD_Q) or not np.all(np.isfinite(clean)):
        raise ValueError(
            f"priors must be finite shape ({matrix.shape[1]},{v35.FIELD_Q})")
    clean = clean / np.sum(clean, axis=1, keepdims=True)
    if not np.all(np.isfinite(clean)):
        raise ValueError("cleaned prior must be finite")
    log_prior = np.log(clean)

    columns = [np.flatnonzero(matrix[row] != 0) for row in range(matrix.shape[0])]
    coefficients = [matrix[row, cols].astype(np.uint8).tolist()
                    for row, cols in enumerate(columns)]
    return matrix, target, clean, log_prior, columns, coefficients


def _softmax_log(message: Any) -> np.ndarray:
    values = np.asarray(message, dtype=np.float64)
    if values.shape != (v35.FIELD_Q,) or not np.all(np.isfinite(values)):
        raise ValueError("C2V message must be a finite GF(32) log vector")
    shifted = values - np.max(values)
    probabilities = np.exp(shifted)
    total = float(np.sum(probabilities))
    if not np.isfinite(total) or total <= 0.0:
        raise ValueError("C2V message softmax has invalid normalization")
    return probabilities / total


def _check_outputs(out_messages: Any, degree: int, row: int) -> list[np.ndarray]:
    values = list(out_messages)
    if len(values) != degree:
        raise ValueError(f"check update returned wrong message count at row {row}")
    result = []
    for message in values:
        array = np.asarray(message, dtype=np.float64)
        if array.shape != (v35.FIELD_Q,) or not np.all(np.isfinite(array)):
            raise ValueError(f"check update returned invalid C2V at row {row}")
        result.append(array.copy())
    return result


def decode_row_layered_residual_sweep(
        h_matrix: Any, priors: Any, syndrome: Any, *, max_iter: int = 90,
        schedule: str = "residual", damping_alpha: float = 1.0,
        field: Any = None,
        check_update_fn: Callable[..., Any] | None = None) -> ResidualSweepResult:
    """Decode cold with natural order or one residual-ranked order per sweep.

    Residual mode scores every check from an immutable sweep-start snapshot,
    sorts by descending raw probability L-infinity residual (ties by row),
    then recomputes and immediately applies each row against the live state.
    The scoring messages are never reused as committed updates.
    """
    if schedule not in ("natural", "residual"):
        raise ValueError("schedule must be exactly 'natural' or 'residual'")
    if float(damping_alpha) != 1.0:
        raise ValueError("the residual research loop is frozen to damping_alpha=1.0")
    if int(max_iter) < 0:
        raise ValueError("max_iter must be non-negative")

    started = time.perf_counter()
    matrix, target, _clean_prior, log_prior, columns, coefficients = _checked_inputs(
        h_matrix, priors, syndrome)
    if field is None:
        field = v35.GF2mField.create(v35.FIELD_Q)
    tables = v35._get_gf32_tables(field)
    update = v35._check_update_log_batch if check_update_fn is None else check_update_fn

    beliefs = log_prior.copy()
    check_to_var = [
        [np.zeros(v35.FIELD_Q, dtype=np.float64) for _ in row_columns]
        for row_columns in columns
    ]
    score_check_updates = 0
    applied_check_updates = 0
    score_edge_updates = 0
    applied_edge_updates = 0
    row_orders: list[tuple[int, ...]] = []
    first_sweep_residuals: tuple[float, ...] = ()

    def result(iterations: int, status: str, *, prior_only: bool) -> ResidualSweepResult:
        x_hat = np.argmax(beliefs, axis=1).astype(np.uint8)
        own_syndrome = v35.syndrome_of_gf32(matrix, x_hat, field)
        syndrome_ok = bool(np.array_equal(own_syndrome, target))
        if prior_only:
            extrinsic = np.zeros_like(beliefs)
            belief_provenance = v35.BELIEF_PROVENANCE_PRIOR_ONLY
            extrinsic_provenance = v35.EXTRINSIC_NO_CHECK_EVIDENCE
        else:
            extrinsic = v35._build_check_extrinsic_log_beliefs(beliefs, log_prior)
            belief_provenance = v35.BELIEF_PROVENANCE_CHECK_UPDATED
            extrinsic_provenance = v35.EXTRINSIC_CHECK_EXTRINSIC
        return ResidualSweepResult(
            x_hat=x_hat, syndrome_ok=syndrome_ok, iterations=int(iterations),
            runtime_s=time.perf_counter() - started, status=status,
            final_beliefs=beliefs.copy(), belief_provenance=belief_provenance,
            extrinsic_log_beliefs=extrinsic,
            extrinsic_provenance=extrinsic_provenance,
            row_orders=tuple(row_orders), first_sweep_residuals=first_sweep_residuals,
            score_check_updates=score_check_updates,
            applied_check_updates=applied_check_updates,
            score_edge_updates=score_edge_updates,
            applied_edge_updates=applied_edge_updates)

    initial_x = np.argmax(beliefs, axis=1).astype(np.uint8)
    if np.array_equal(v35.syndrome_of_gf32(matrix, initial_x, field), target):
        return result(0, "converged_exact", prior_only=True)

    completed = 0
    for _ in range(int(max_iter)):
        if schedule == "natural":
            order = tuple(range(matrix.shape[0]))
        else:
            # Freeze both beliefs and C2V for all scores in this sweep.
            score_beliefs = beliefs.copy()
            score_c2v = [[message.copy() for message in row] for row in check_to_var]
            residuals = [0.0] * matrix.shape[0]
            for row, row_columns in enumerate(columns):
                in_messages = [
                    score_beliefs[int(column)] - score_c2v[row][pos]
                    for pos, column in enumerate(row_columns)
                ]
                scored = _check_outputs(
                    update(in_messages, coefficients[row], int(target[row]), field, tables),
                    len(row_columns), row)
                score_check_updates += 1
                score_edge_updates += len(row_columns)
                edge_residuals = [
                    float(np.max(np.abs(_softmax_log(scored[pos])
                                        - _softmax_log(score_c2v[row][pos]))))
                    for pos in range(len(row_columns))
                ]
                residuals[row] = max(edge_residuals, default=0.0)
                if not np.isfinite(residuals[row]):
                    raise ValueError(f"nonfinite residual score at row {row}")
            if completed == 0:
                first_sweep_residuals = tuple(residuals)
            # Exact float ties only; row index is the deterministic tie break.
            order = tuple(sorted(range(matrix.shape[0]),
                                 key=lambda row: (-residuals[row], row)))

        for row in order:
            row_columns = columns[row]
            in_messages = [
                beliefs[int(column)] - check_to_var[row][pos]
                for pos, column in enumerate(row_columns)
            ]
            outgoing = _check_outputs(
                update(in_messages, coefficients[row], int(target[row]), field, tables),
                len(row_columns), row)
            applied_check_updates += 1
            applied_edge_updates += len(row_columns)
            for pos, column in enumerate(row_columns):
                old = check_to_var[row][pos]
                message = outgoing[pos]
                # Preserve v35's arithmetic order exactly for the natural canary.
                beliefs[int(column)] = beliefs[int(column)] - old + message
                check_to_var[row][pos] = message
        row_orders.append(order)
        completed += 1

        best_x = np.argmax(beliefs, axis=1).astype(np.uint8)
        if np.array_equal(v35.syndrome_of_gf32(matrix, best_x, field), target):
            return result(completed, "converged_exact", prior_only=False)

    return result(completed, "converged_no_syndrome", prior_only=(completed == 0))
