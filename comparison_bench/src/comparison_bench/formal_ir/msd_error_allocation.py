"""Continuous normal-tail allocation and separate integer stage budgets.

This module models only the normal approximation.  It does not predict an
achievable code rate, decoder FER, or out-of-sample performance.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import NormalDist
from typing import Iterable


@dataclass(frozen=True)
class NormalErrorBudgetAllocation:
    """A continuous upper-tail allocation in the caller's original order."""

    epsilons: tuple[float, ...]
    z_values: tuple[float | None, ...]
    backoff_bits_per_sqrt_symbol: tuple[float, ...]
    continuous_objective_bits_per_sqrt_symbol: float
    total_epsilon: float


@dataclass(frozen=True)
class NormalStageBudgets:
    """Continuous and separately rounded/clipped normal stage costs."""

    entropies_bits_per_symbol: tuple[float, ...]
    variances_bits_squared_per_symbol: tuple[float, ...]
    epsilons: tuple[float, ...]
    z_values: tuple[float | None, ...]
    continuous_bits_per_stage: tuple[float, ...]
    raw_ceil_bits_per_stage: tuple[int, ...]
    clipped_bits_per_stage: tuple[int, ...]
    N_symbols: int


def _finite_vector(values: Iterable[float], name: str) -> tuple[float, ...]:
    if getattr(values, "ndim", 1) != 1:
        raise ValueError(f"{name} must be one-dimensional")
    try:
        raw = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be a nonempty one-dimensional sequence") from exc
    if not raw:
        raise ValueError(f"{name} must be nonempty")

    converted: list[float] = []
    for value in raw:
        if isinstance(value, (str, bytes, bool)):
            raise ValueError(f"{name} values must be finite real numbers")
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{name} values must be finite real numbers") from exc
        if not math.isfinite(number):
            raise ValueError(f"{name} values must be finite")
        converted.append(number)
    return tuple(converted)


def _epsilon_scalar(value: float, name: str = "total_epsilon") -> float:
    if isinstance(value, (str, bytes, bool)):
        raise ValueError(f"{name} must be a finite real number")
    try:
        epsilon = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite real number") from exc
    if not math.isfinite(epsilon) or not 0.0 < epsilon < 0.5:
        raise ValueError(f"{name} must be finite and satisfy 0 < {name} < 0.5")
    return epsilon


def _upper_tail(z: float) -> float:
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def allocate_normal_error_budget(
    variances: Iterable[float], total_epsilon: float
) -> NormalErrorBudgetAllocation:
    """Minimize ``sum(sqrt(V_k) * z_k)`` for a fixed total tail probability.

    The result is a continuous normal-approximation allocation.  Exact
    zero-variance stages receive no epsilon when positive-variance stages
    exist; if all variances are zero, epsilon is split uniformly by convention.
    """

    variance_values = _finite_vector(variances, "variances")
    if any(value < 0.0 for value in variance_values):
        raise ValueError("variances must be nonnegative")
    epsilon_target = _epsilon_scalar(total_epsilon)
    positive_indices = [i for i, value in enumerate(variance_values) if value > 0.0]
    count = len(variance_values)

    epsilon_values = [0.0] * count
    z_values: list[float | None] = [None] * count
    backoff_values = [0.0] * count

    if not positive_indices:
        uniform = epsilon_target / count
        epsilon_values = [uniform] * count
        return NormalErrorBudgetAllocation(
            epsilons=tuple(epsilon_values),
            z_values=tuple(z_values),
            backoff_bits_per_sqrt_symbol=tuple(backoff_values),
            continuous_objective_bits_per_sqrt_symbol=0.0,
            total_epsilon=epsilon_target,
        )

    if len(positive_indices) == 1:
        index = positive_indices[0]
        epsilon_values[index] = epsilon_target
        z = -NormalDist().inv_cdf(epsilon_target)
        z_values[index] = z
        backoff_values[index] = math.sqrt(variance_values[index]) * z
        objective = math.fsum(backoff_values)
        if not math.isfinite(objective):
            raise ValueError("normal allocation objective is not finite")
        return NormalErrorBudgetAllocation(
            epsilons=tuple(epsilon_values),
            z_values=tuple(z_values),
            backoff_bits_per_sqrt_symbol=tuple(backoff_values),
            continuous_objective_bits_per_sqrt_symbol=objective,
            total_epsilon=epsilon_target,
        )

    log_sqrt_variances = {
        index: 0.5 * math.log(variance_values[index]) for index in positive_indices
    }
    lower = max(
        log_sqrt_variances[index] + 0.5 * math.log(2.0 * math.pi)
        for index in positive_indices
    )

    def allocation_at(log_lambda: float) -> tuple[float, dict[int, float]]:
        epsilons: dict[int, float] = {}
        for index in positive_indices:
            radicand = 2.0 * (
                log_lambda
                - log_sqrt_variances[index]
                - 0.5 * math.log(2.0 * math.pi)
            )
            z = math.sqrt(max(0.0, radicand))
            epsilons[index] = _upper_tail(z)
        return math.fsum(epsilons.values()), epsilons

    low = lower
    step = 1.0
    high = lower + step
    high_sum, _ = allocation_at(high)
    while high_sum > epsilon_target:
        step *= 2.0
        high = lower + step
        if not math.isfinite(high):
            raise ValueError("could not bracket the requested epsilon allocation")
        high_sum, _ = allocation_at(high)

    # The function is monotone decreasing in log(lambda).  Keep high on the
    # feasible side so the returned epsilon sum cannot exceed the target.
    for _ in range(256):
        middle = low + (high - low) / 2.0
        if middle == low or middle == high:
            break
        middle_sum, _ = allocation_at(middle)
        if middle_sum > epsilon_target:
            low = middle
        else:
            high = middle

    allocated_sum, solved = allocation_at(high)
    if allocated_sum > epsilon_target:
        raise ArithmeticError("normal allocation exceeded the requested epsilon")
    for index, epsilon in solved.items():
        z = math.sqrt(
            max(
                0.0,
                2.0
                * (
                    high
                    - log_sqrt_variances[index]
                    - 0.5 * math.log(2.0 * math.pi)
                ),
            )
        )
        epsilon_values[index] = epsilon
        z_values[index] = z
        backoff_values[index] = math.sqrt(variance_values[index]) * z

    objective = math.fsum(backoff_values)
    if not math.isfinite(objective) or any(
        not math.isfinite(value) for value in (*epsilon_values, *backoff_values)
    ):
        raise ValueError("normal allocation produced a non-finite result")
    if epsilon_target == 0.01 and epsilon_target - allocated_sum > 1e-14:
        raise ArithmeticError("epsilon allocation did not meet the 1e-14 target tolerance")

    return NormalErrorBudgetAllocation(
        epsilons=tuple(epsilon_values),
        z_values=tuple(z_values),
        backoff_bits_per_sqrt_symbol=tuple(backoff_values),
        continuous_objective_bits_per_sqrt_symbol=objective,
        total_epsilon=epsilon_target,
    )


def normal_stage_budgets(
    entropies: Iterable[float],
    variances: Iterable[float],
    N: int,
    epsilons: Iterable[float],
) -> NormalStageBudgets:
    """Compute normal stage budgets, then ceil and clip as separate steps.

    ``H`` is in bits/symbol, ``V`` in bits squared/symbol, ``N`` in symbols,
    and all costs are bits/stage.  Zero variance has zero normal backoff but
    does not imply zero entropy or zero disclosure.
    """

    if isinstance(N, bool) or not isinstance(N, int) or N <= 0:
        raise ValueError("N must be a positive integer number of symbols")
    entropy_values = _finite_vector(entropies, "entropies")
    variance_values = _finite_vector(variances, "variances")
    epsilon_values = _finite_vector(epsilons, "epsilons")
    if not (len(entropy_values) == len(variance_values) == len(epsilon_values)):
        raise ValueError("entropies, variances and epsilons must have matching lengths")
    if any(value < 0.0 or value > 1.0 for value in entropy_values):
        raise ValueError("entropies must be in [0,1] bits/symbol")
    if any(value < 0.0 for value in variance_values):
        raise ValueError("variances must be nonnegative bits squared/symbol")
    for variance, epsilon in zip(variance_values, epsilon_values):
        if variance > 0.0:
            if not 0.0 < epsilon < 0.5:
                raise ValueError("positive-variance stages require 0 < epsilon < 0.5")
        elif not 0.0 <= epsilon < 0.5:
            raise ValueError("zero-variance stages require 0 <= epsilon < 0.5")

    normal = NormalDist()
    z_values: list[float | None] = []
    continuous: list[float] = []
    raw_ceil: list[int] = []
    clipped: list[int] = []
    for entropy, variance, epsilon in zip(
        entropy_values, variance_values, epsilon_values
    ):
        if variance == 0.0:
            z: float | None = None
            backoff = 0.0
        else:
            z = -normal.inv_cdf(epsilon)
            backoff = math.sqrt(N * variance) * z
        value = N * entropy + backoff
        if not math.isfinite(value):
            raise ValueError("continuous stage budget is not finite")
        ceil_value = math.ceil(value)
        clip_value = min(N, max(0, ceil_value))
        z_values.append(z)
        continuous.append(value)
        raw_ceil.append(ceil_value)
        clipped.append(clip_value)

    return NormalStageBudgets(
        entropies_bits_per_symbol=entropy_values,
        variances_bits_squared_per_symbol=variance_values,
        epsilons=epsilon_values,
        z_values=tuple(z_values),
        continuous_bits_per_stage=tuple(continuous),
        raw_ceil_bits_per_stage=tuple(raw_ceil),
        clipped_bits_per_stage=tuple(clipped),
        N_symbols=N,
    )
