import math
from statistics import NormalDist

import pytest

from comparison_bench.src.comparison_bench.formal_ir.msd_error_allocation import (
    allocate_normal_error_budget,
    normal_stage_budgets,
)


def test_allocation_satisfies_epsilon_constraint_and_kkt_stationarity():
    variances = (0.2, 1.0, 3.0, 0.0)
    allocation = allocate_normal_error_budget(variances, 0.01)

    assert sum(allocation.epsilons) <= 0.01
    assert 0.01 - sum(allocation.epsilons) <= 1e-14
    assert allocation.epsilons[3] == 0.0
    assert allocation.z_values[3] is None
    assert allocation.backoff_bits_per_sqrt_symbol[3] == 0.0

    normal = NormalDist()
    stationary_values = []
    for variance, epsilon, z in zip(
        variances, allocation.epsilons, allocation.z_values
    ):
        if variance == 0.0:
            continue
        assert z is not None
        assert math.isclose(epsilon, 1.0 - normal.cdf(z), rel_tol=0.0, abs_tol=2e-16)
        stationary_values.append(math.sqrt(variance) / normal.pdf(z))
    assert max(stationary_values) - min(stationary_values) < 2e-10

    uniform_z = normal.inv_cdf(1.0 - 0.01 / len(variances))
    uniform_objective = math.fsum(
        math.sqrt(variance) * uniform_z for variance in variances if variance > 0.0
    )
    assert allocation.continuous_objective_bits_per_sqrt_symbol <= uniform_objective


def test_allocation_is_permutation_equivariant_and_scale_invariant():
    variances = (0.1, 0.7, 2.5)
    original = allocate_normal_error_budget(variances, 0.01)
    permutation = (2, 0, 1)
    permuted = allocate_normal_error_budget(
        tuple(variances[index] for index in permutation), 0.01
    )
    assert permuted.epsilons == pytest.approx(
        tuple(original.epsilons[index] for index in permutation), abs=2e-15
    )
    assert permuted.z_values == pytest.approx(
        tuple(original.z_values[index] for index in permutation), abs=2e-14
    )

    scaled = allocate_normal_error_budget(tuple(9.0 * v for v in variances), 0.01)
    assert scaled.epsilons == pytest.approx(original.epsilons, abs=2e-15)
    assert scaled.continuous_objective_bits_per_sqrt_symbol == pytest.approx(
        3.0 * original.continuous_objective_bits_per_sqrt_symbol, rel=2e-14
    )


def test_single_positive_and_all_zero_variance_conventions():
    single = allocate_normal_error_budget((0.0, 2.0, 0.0), 0.01)
    assert single.epsilons == (0.0, 0.01, 0.0)
    assert single.z_values[0] is None and single.z_values[2] is None
    assert single.z_values[1] == pytest.approx(NormalDist().inv_cdf(0.99))

    all_zero = allocate_normal_error_budget((0.0, 0.0, 0.0), 0.01)
    assert all_zero.epsilons == pytest.approx((0.01 / 3.0,) * 3)
    assert all_zero.z_values == (None, None, None)
    assert all_zero.backoff_bits_per_sqrt_symbol == (0.0, 0.0, 0.0)
    assert all_zero.continuous_objective_bits_per_sqrt_symbol == 0.0


@pytest.mark.parametrize("epsilon", (1e-20, math.nextafter(0.5, 0.0)))
def test_tail_quantiles_round_trip_without_complement_cancellation(epsilon):
    complement = 1.0 - epsilon
    assert complement == (1.0 if epsilon == 1e-20 else 0.5)

    allocation = allocate_normal_error_budget((1.0,), epsilon)
    stage = normal_stage_budgets((0.25,), (0.4,), 128, (epsilon,))
    quantiles = (allocation.z_values[0], stage.z_values[0])
    for z in quantiles:
        assert z is not None and math.isfinite(z) and z > 0.0
        round_trip_epsilon = 0.5 * math.erfc(z / math.sqrt(2.0))
        assert math.isclose(round_trip_epsilon, epsilon, rel_tol=1e-12, abs_tol=0.0)
    assert math.isfinite(stage.continuous_bits_per_stage[0])


def test_ceil_and_clip_are_separate_and_integer_cost_can_worsen():
    N = 100_000
    variances = (1.0, 1.01)
    entropies = (1.2512536980237883e-05, 8.886412325185802e-06)
    optimized_allocation = allocate_normal_error_budget(variances, 0.01)
    uniform = normal_stage_budgets(entropies, variances, N, (0.005, 0.005))
    optimized = normal_stage_budgets(
        entropies, variances, N, optimized_allocation.epsilons
    )

    assert math.fsum(optimized.continuous_bits_per_stage) < math.fsum(
        uniform.continuous_bits_per_stage
    )
    assert sum(optimized.clipped_bits_per_stage) > sum(uniform.clipped_bits_per_stage)
    assert uniform.raw_ceil_bits_per_stage == (816, 820)
    assert optimized.raw_ceil_bits_per_stage == (817, 820)


def test_zero_variance_does_not_zero_nonzero_entropy_or_disclosure():
    result = normal_stage_budgets((1.0,), (0.0,), 64, (0.0,))
    assert result.z_values == (None,)
    assert result.continuous_bits_per_stage == (64.0,)
    assert result.raw_ceil_bits_per_stage == (64,)
    assert result.clipped_bits_per_stage == (64,)


@pytest.mark.parametrize(
    "variances,total_epsilon",
    [
        ((), 0.01),
        ((-1.0,), 0.01),
        ((math.inf,), 0.01),
        ((math.nan,), 0.01),
        ((1.0,), 0.0),
        ((1.0,), 0.5),
        ((1.0,), math.inf),
        (((1.0, 2.0),), 0.01),
    ],
)
def test_allocator_rejects_invalid_inputs(variances, total_epsilon):
    with pytest.raises(ValueError):
        allocate_normal_error_budget(variances, total_epsilon)


@pytest.mark.parametrize(
    "entropies,variances,N,epsilons",
    [
        ((0.1,), (0.2, 0.3), 10, (0.01,)),
        ((-0.1,), (0.2,), 10, (0.01,)),
        ((1.1,), (0.2,), 10, (0.01,)),
        ((0.1,), (-0.2,), 10, (0.01,)),
        ((0.1,), (0.2,), 0, (0.01,)),
        ((0.1,), (0.2,), True, (0.01,)),
        ((0.1,), (0.2,), 10, (0.0,)),
        ((0.1,), (0.0,), 10, (0.5,)),
    ],
)
def test_stage_budget_rejects_invalid_inputs(entropies, variances, N, epsilons):
    with pytest.raises(ValueError):
        normal_stage_budgets(entropies, variances, N, epsilons)
