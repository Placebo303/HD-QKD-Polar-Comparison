"""Research-only row-layered GF(32) loop with explicit C2V state."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

from comparison_bench.formal_ir import v35_algorithm_development as v35


@dataclass
class EdgeState:
    h_matrix: np.ndarray
    syndrome: np.ndarray
    beliefs: np.ndarray
    log_prior: np.ndarray
    check_to_var: list[list[np.ndarray]]
    completed_sweeps: int = 0
    stopped_exact: bool = False


@dataclass
class EdgeLoopResult:
    x_hat: np.ndarray
    syndrome_ok: bool
    iterations: int
    iterations_this_call: int
    status: str
    final_beliefs: np.ndarray
    state: EdgeState
    belief_provenance: str
    extrinsic_log_beliefs: np.ndarray
    extrinsic_provenance: str


def clean_prior(priors: Any, n: int, q: int = v35.FIELD_Q) -> np.ndarray:
    """Apply the exact v35 floor-and-row-normalize rule."""
    values = np.asarray(priors, dtype=np.float64)
    if values.shape != (int(n), int(q)) or not np.all(np.isfinite(values)):
        raise ValueError(f"priors must be finite shape ({int(n)}, {int(q)})")
    values = np.maximum(values, 1e-15)
    return values / np.sum(values, axis=1, keepdims=True)


def _matrix_rows(h_matrix: Any, syndrome: Any) -> tuple[
        np.ndarray, np.ndarray, list[np.ndarray], list[np.ndarray]]:
    raw_matrix = np.asarray(h_matrix)
    raw_target = np.asarray(syndrome).ravel()
    if raw_matrix.ndim != 2 or raw_matrix.shape[0] < 1 or raw_matrix.shape[1] < 1:
        raise ValueError("H must be a nonempty two-dimensional matrix")
    if raw_target.shape != (raw_matrix.shape[0],):
        raise ValueError("syndrome shape must match H rows")
    if (not np.issubdtype(raw_matrix.dtype, np.integer)
            or not np.issubdtype(raw_target.dtype, np.integer)
            or np.any(raw_matrix < 0) or np.any(raw_matrix >= v35.FIELD_Q)
            or np.any(raw_target < 0) or np.any(raw_target >= v35.FIELD_Q)):
        raise ValueError("H and syndrome must contain GF(32) symbols")
    matrix = raw_matrix.astype(np.uint8, copy=True)
    target = raw_target.astype(np.uint8, copy=True)
    columns = [np.flatnonzero(matrix[row] != 0) for row in range(matrix.shape[0])]
    coefficients = [matrix[row, cols].astype(np.uint8, copy=True)
                    for row, cols in enumerate(columns)]
    return matrix, target, columns, coefficients


def sum_check_to_var(state: EdgeState) -> np.ndarray:
    """Sum the current edge messages at each variable in row order."""
    n, q = state.beliefs.shape
    result = np.zeros((n, q), dtype=np.float64)
    for row in range(state.h_matrix.shape[0]):
        cols = np.flatnonzero(state.h_matrix[row] != 0)
        for pos, column in enumerate(cols):
            result[int(column)] += state.check_to_var[row][pos]
    return result


def initial_v2c_message(state: EdgeState, check: int, variable: int) -> np.ndarray:
    """Return the state-consistent V2C message for one Tanner-graph edge."""
    row = int(check)
    column = int(variable)
    if row < 0 or row >= state.h_matrix.shape[0] or column < 0 or column >= state.h_matrix.shape[1]:
        raise IndexError("check or variable index is outside the state matrix")
    cols = np.flatnonzero(state.h_matrix[row] != 0)
    positions = np.flatnonzero(cols == column)
    if positions.size != 1:
        raise ValueError("requested check/variable pair is not an edge")
    return (state.beliefs[column] - state.check_to_var[row][int(positions[0])]).copy()


def _validate_state(state: EdgeState, matrix: np.ndarray, target: np.ndarray,
                    log_prior: np.ndarray, columns: list[np.ndarray]) -> EdgeState:
    if not np.array_equal(state.h_matrix, matrix) or not np.array_equal(state.syndrome, target):
        raise ValueError("edge state belongs to a different H or syndrome")
    if not np.array_equal(state.log_prior, log_prior):
        raise ValueError("prior changed; call rebase_edge_state before decoding")
    if state.beliefs.shape != log_prior.shape or not np.all(np.isfinite(state.beliefs)):
        raise ValueError("edge-state beliefs have invalid shape or values")
    if len(state.check_to_var) != matrix.shape[0]:
        raise ValueError("edge-state check-row count differs from H")
    copied: list[list[np.ndarray]] = []
    for row, cols in enumerate(columns):
        if len(state.check_to_var[row]) != len(cols):
            raise ValueError(f"edge-state degree differs at check row {row}")
        messages = []
        for message in state.check_to_var[row]:
            value = np.asarray(message, dtype=np.float64)
            if value.shape != (log_prior.shape[1],) or not np.all(np.isfinite(value)):
                raise ValueError(f"invalid C2V message at check row {row}")
            messages.append(value.copy())
        copied.append(messages)
    if int(state.completed_sweeps) < 0:
        raise ValueError("completed_sweeps must be non-negative")
    return EdgeState(
        h_matrix=matrix.copy(), syndrome=target.copy(), beliefs=state.beliefs.copy(),
        log_prior=log_prior.copy(), check_to_var=copied,
        completed_sweeps=int(state.completed_sweeps),
        stopped_exact=bool(state.stopped_exact),
    )


def rebase_edge_state(state: EdgeState, new_priors: Any) -> EdgeState:
    """Keep C2V messages and rebuild beliefs from a newly cleaned prior."""
    matrix, target, columns, _ = _matrix_rows(state.h_matrix, state.syndrome)
    old_state = _validate_state(state, matrix, target, state.log_prior, columns)
    prior = clean_prior(new_priors, matrix.shape[1], state.beliefs.shape[1])
    check_sum = sum_check_to_var(old_state)
    return EdgeState(
        h_matrix=matrix.copy(), syndrome=target.copy(),
        beliefs=np.log(prior) + check_sum, log_prior=np.log(prior),
        check_to_var=[[message.copy() for message in row]
                      for row in old_state.check_to_var],
        completed_sweeps=0, stopped_exact=False,
    )


def _result(state: EdgeState, *, iterations_this_call: int,
            status: str) -> EdgeLoopResult:
    x_hat = np.argmax(state.beliefs, axis=1).astype(np.uint8)
    syndrome_ok = bool(np.array_equal(
        v35.syndrome_of_gf32(state.h_matrix, x_hat), state.syndrome))
    has_edge_messages = any(
        np.any(message != 0.0)
        for row in state.check_to_var for message in row)
    rebased_without_sweep = (
        state.completed_sweeps == 0 and iterations_this_call == 0 and has_edge_messages)
    if state.completed_sweeps > 0 or has_edge_messages:
        extrinsic = v35._build_check_extrinsic_log_beliefs(
            state.beliefs, state.log_prior)
        ext_provenance = (
            v35.EXTRINSIC_WARM_START_UNSPECIFIED if rebased_without_sweep
            else v35.EXTRINSIC_CHECK_EXTRINSIC)
        belief_provenance = (
            v35.BELIEF_PROVENANCE_WARM_START_UNSPECIFIED if rebased_without_sweep
            else v35.BELIEF_PROVENANCE_CHECK_UPDATED)
    else:
        extrinsic = np.zeros_like(state.beliefs)
        ext_provenance = v35.EXTRINSIC_NO_CHECK_EVIDENCE
        belief_provenance = v35.BELIEF_PROVENANCE_PRIOR_ONLY
    return EdgeLoopResult(
        x_hat=x_hat, syndrome_ok=syndrome_ok,
        iterations=int(state.completed_sweeps),
        iterations_this_call=int(iterations_this_call), status=status,
        final_beliefs=state.beliefs.copy(), state=state,
        belief_provenance=belief_provenance,
        extrinsic_log_beliefs=extrinsic,
        extrinsic_provenance=ext_provenance,
    )


def decode_row_layered_edge_state(
        h_matrix: Any, priors: Any, syndrome: Any, *, max_iter: int = 90,
        damping_alpha: float = 1.0, state: EdgeState | None = None,
        field: Any = None) -> EdgeLoopResult:
    """Run the frozen alpha-one row schedule with explicit C2V state.

    ``max_iter`` is the maximum number of additional complete sweeps in this
    call. ``result.iterations`` is cumulative along the supplied state path;
    ``iterations_this_call`` is the number charged to this decoder call.
    """
    if float(damping_alpha) != 1.0:
        raise ValueError("the edge-state research loop is frozen to alpha=1.0")
    if int(max_iter) < 0:
        raise ValueError("max_iter must be non-negative")
    matrix, target, columns, coefficients = _matrix_rows(h_matrix, syndrome)
    prior = clean_prior(priors, matrix.shape[1])
    log_prior = np.log(prior)
    if field is None:
        field = v35.GF2mField.create(v35.FIELD_Q)
    tables = v35._get_gf32_tables(field)

    if state is None:
        current = EdgeState(
            h_matrix=matrix.copy(), syndrome=target.copy(),
            beliefs=log_prior.copy(), log_prior=log_prior.copy(),
            check_to_var=[[np.zeros(v35.FIELD_Q, dtype=np.float64)
                           for _ in columns[row]]
                          for row in range(matrix.shape[0])],
        )
    else:
        current = _validate_state(state, matrix, target, log_prior, columns)

    start_sweeps = current.completed_sweeps
    best_x = np.argmax(current.beliefs, axis=1).astype(np.uint8)
    syndrome_ok = np.array_equal(v35.syndrome_of_gf32(matrix, best_x, field), target)
    if current.stopped_exact and not syndrome_ok:
        raise ValueError("edge state is marked exact but its current decision fails syndrome")
    if syndrome_ok:
        current.stopped_exact = True
        return _result(current, iterations_this_call=0, status="converged_exact")

    for _ in range(int(max_iter)):
        for row, cols in enumerate(columns):
            in_messages = [
                current.beliefs[int(column)] - current.check_to_var[row][pos]
                for pos, column in enumerate(cols)
            ]
            out_messages = v35._check_update_log_batch(
                in_messages, coefficients[row].tolist(), int(target[row]), field, tables)
            if len(out_messages) != len(cols):
                raise ValueError(f"check update returned wrong message count at row {row}")
            for pos, column in enumerate(cols):
                message = np.asarray(out_messages[pos], dtype=np.float64)
                if message.shape != (v35.FIELD_Q,) or not np.all(np.isfinite(message)):
                    raise ValueError(f"check update returned invalid C2V at row {row}")
                old = current.check_to_var[row][pos]
                current.beliefs[int(column)] = (
                    current.beliefs[int(column)] - old + message)
                current.check_to_var[row][pos] = message.copy()
        current.completed_sweeps += 1
        best_x = np.argmax(current.beliefs, axis=1).astype(np.uint8)
        syndrome_ok = np.array_equal(v35.syndrome_of_gf32(matrix, best_x, field), target)
        if syndrome_ok:
            current.stopped_exact = True
            return _result(
                current, iterations_this_call=current.completed_sweeps - start_sweeps,
                status="converged_exact")

    current.stopped_exact = False
    return _result(
        current, iterations_this_call=current.completed_sweeps - start_sweeps,
        status="converged_no_syndrome")


def capture_reference_state(
        h_matrix: Any, priors: Any, syndrome: Any, *, max_iter: int = 90,
        damping_alpha: float = 1.0, decode_fn: Callable[..., Any] | None = None,
        check_update_impl: Callable[..., Any] | None = None) -> tuple[Any, EdgeState]:
    """Capture C2V while delegating the original prior to the v35 decoder."""
    if float(damping_alpha) != 1.0:
        raise ValueError("C2V capture is frozen to alpha=1.0")
    matrix, target, columns, coefficients = _matrix_rows(h_matrix, syndrome)
    prior = clean_prior(priors, matrix.shape[1])
    log_prior = np.log(prior)
    decode = v35.decode_row_layered_fftqspa if decode_fn is None else decode_fn
    check_update = v35._check_update_log_batch if check_update_impl is None else check_update_impl
    row_calls = 0
    partial_sweep: list[list[np.ndarray] | None] = [None] * matrix.shape[0]
    last_complete: list[list[np.ndarray]] | None = None

    def capture_update(in_messages, actual_coefficients, actual_syndrome,
                       field_value, tables_value):
        nonlocal row_calls, last_complete
        row = row_calls % matrix.shape[0]
        expected_coefficients = coefficients[row]
        if (not np.array_equal(np.asarray(actual_coefficients, dtype=np.uint8),
                               expected_coefficients)
                or int(actual_syndrome) != int(target[row])
                or len(in_messages) != len(columns[row])):
            raise ValueError(f"v35 C2V callback phase/order mismatch at row {row}")
        outgoing = check_update(
            in_messages, actual_coefficients, actual_syndrome, field_value, tables_value)
        if len(outgoing) != len(columns[row]):
            raise ValueError(f"v35 check helper returned wrong degree at row {row}")
        captured = []
        for message in outgoing:
            value = np.asarray(message, dtype=np.float64)
            if value.shape != (v35.FIELD_Q,) or not np.all(np.isfinite(value)):
                raise ValueError(f"v35 check helper returned invalid C2V at row {row}")
            captured.append(value.copy())
        partial_sweep[row] = captured
        row_calls += 1
        if row_calls % matrix.shape[0] == 0:
            if any(messages is None for messages in partial_sweep):
                raise ValueError("v35 C2V callback ended a sweep with a missing row")
            last_complete = [
                [message.copy() for message in messages]
                for messages in partial_sweep if messages is not None
            ]
        return outgoing

    raw = decode(
        matrix, priors, target, max_iter=int(max_iter),
        damping_alpha=1.0, warm_beliefs=None, field=None,
        check_update_fn=capture_update)
    iterations = int(raw.iterations)
    expected_calls = iterations * matrix.shape[0]
    if row_calls != expected_calls:
        raise ValueError(
            f"v35 callback count {row_calls} != iterations*rows {expected_calls}")
    if iterations == 0:
        c2v = [[np.zeros(v35.FIELD_Q, dtype=np.float64) for _ in columns[row]]
               for row in range(matrix.shape[0])]
    else:
        if last_complete is None or len(last_complete) != matrix.shape[0]:
            raise ValueError("v35 C2V callback did not capture a complete final sweep")
        c2v = last_complete
    beliefs = np.asarray(raw.final_beliefs, dtype=np.float64)
    if beliefs.shape != log_prior.shape or not np.all(np.isfinite(beliefs)):
        raise ValueError("v35 reference returned invalid final_beliefs")
    state = EdgeState(
        h_matrix=matrix.copy(), syndrome=target.copy(), beliefs=beliefs.copy(),
        log_prior=np.log(prior), check_to_var=c2v,
        completed_sweeps=iterations,
        stopped_exact=(str(raw.status) == "converged_exact"),
    )
    return raw, state
