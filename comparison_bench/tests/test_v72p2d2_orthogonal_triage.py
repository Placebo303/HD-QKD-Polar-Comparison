"""Focused synthetic checks for V72P2D2; no production data or output paths."""
from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import shutil
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "comparison_bench" / "formal_ir" / "v72p2d2_orthogonal_triage.py"
SPEC = importlib.util.spec_from_file_location("v72p2d2_triage_test_module", str(MODULE_PATH))
assert SPEC is not None and SPEC.loader is not None
triage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(triage)

RUNNER_PATH = ROOT.parent / "scripts" / "v72p2d2_orthogonal_triage.py"
RUNNER_SPEC = importlib.util.spec_from_file_location("v72p2d2_runner_test_module", str(RUNNER_PATH))
assert RUNNER_SPEC is not None and RUNNER_SPEC.loader is not None
runner = importlib.util.module_from_spec(RUNNER_SPEC)
RUNNER_SPEC.loader.exec_module(runner)


def tiny_prior(n: int = 2) -> np.ndarray:
    bob = np.arange(n, dtype=np.uint16)
    return triage.build_m2_prior_logp(bob)


def tiny_graph() -> tuple[np.ndarray, np.ndarray]:
    # Two ordered checks share variable 0 and include two bits of symbol 0.
    return np.asarray([0, 3, 6], dtype=np.int32), np.asarray([0, 1, 0, 2, 3, 4], dtype=np.int32)


def serial_reference(
    prior: np.ndarray, syndrome: np.ndarray, indptr: np.ndarray, indices: np.ndarray, warm: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Independent one-sweep row-serial reference for the tiny contract."""
    state = triage.rebuild_factor_state(prior, warm, indptr, indices)
    c2v = warm.copy()
    btf = state["bit_to_factor"].copy()
    f2b = state["factor_to_bit"].copy()
    for row in range(len(indptr) - 1):
        start, end = int(indptr[row]), int(indptr[row + 1])
        old = c2v[start:end].copy()
        variables = indices[start:end]
        v2c = f2b.reshape(-1)[variables] + btf.reshape(-1)[variables] - old
        tanh_values = np.clip(np.tanh(v2c / 2.0), -0.999999999999, 0.999999999999)
        sign = (-1.0) ** (int(syndrome[row]) + ((end - start) % 2))
        updated = np.empty(end - start, dtype=np.float64)
        for edge in range(end - start):
            product = np.prod(np.delete(tanh_values, edge)) if end - start > 1 else 1.0
            updated[edge] = np.clip(
                2.0 * np.arctanh(np.clip(sign * product, -1.0 + 1e-12, 1.0 - 1e-12)),
                -triage.LLR_CLIP,
                triage.LLR_CLIP,
            )
        c2v[start:end] = updated
        flat = btf.reshape(-1)
        for offset, variable in enumerate(variables):
            flat[int(variable)] += float(updated[offset] - old[offset])
        for symbol in np.unique(variables // 10):
            f2b[int(symbol)] = triage.factor_batch(prior, btf)[int(symbol)]
    return c2v, btf, f2b


def stale_flooding_reference(
    prior: np.ndarray, syndrome: np.ndarray, indptr: np.ndarray, indices: np.ndarray, warm: np.ndarray
) -> np.ndarray:
    """One flooding update using only the checkpoint-start factor state."""
    state = triage.rebuild_factor_state(prior, warm, indptr, indices)
    btf = state["bit_to_factor"].reshape(-1)
    f2b = state["factor_to_bit"].reshape(-1)
    v2c = f2b[indices] + btf[indices] - warm
    c2v = warm.copy()
    for row in range(len(indptr) - 1):
        start, end = int(indptr[row]), int(indptr[row + 1])
        vals = v2c[start:end]
        tanh_values = np.clip(np.tanh(vals / 2.0), -0.999999999999, 0.999999999999)
        degree = end - start
        sign = (-1.0) ** (int(syndrome[row]) + (degree % 2))
        for offset in range(degree):
            product = np.prod(np.delete(tanh_values, offset)) if degree > 1 else 1.0
            c2v[start + offset] = np.clip(
                2.0 * np.arctanh(np.clip(sign * product, -1.0 + 1e-12, 1.0 - 1e-12)),
                -triage.LLR_CLIP,
                triage.LLR_CLIP,
            )
    return c2v


def row_value_map(indices: np.ndarray, values: np.ndarray, indptr: np.ndarray) -> dict[tuple[int, int], float]:
    return {
        (row, int(variable)): float(values[edge])
        for row in range(len(indptr) - 1)
        for edge, variable in zip(range(int(indptr[row]), int(indptr[row + 1])), indices[indptr[row] : indptr[row + 1]])
    }


def test_frozen_constants_and_m2_are_finite_normalized():
    assert triage.Q == 1024 and triage.N == 1024 and triage.NBIT == 10240
    assert triage.M == 9036 and triage.NNZ == 49620
    assert len(triage.CHECKPOINT_ROWS) == 72
    assert triage.CHECKPOINT_ROWS[-2:] == (9032, 9036)
    kernel = triage.wrapped_laplace_kernel()
    assert np.all(np.isfinite(kernel)) and np.all(kernel > 0)
    assert np.isclose(kernel.sum(), 1.0)
    prior = tiny_prior()
    probabilities = np.exp(prior)
    assert np.all(np.isfinite(prior))
    assert np.all(probabilities > 0)
    assert np.allclose(probabilities.sum(axis=1), 1.0)
    assert np.allclose(probabilities, np.exp(triage.build_m2_prior_logp(np.arange(2, dtype=np.uint16))))


def test_m2_formula_shift_floor_and_log_base_contract(monkeypatch):
    assert triage.M2_PARAMS == {
        "family": "laplace",
        "mu": 0.0,
        "scale": 0.2714417616594907,
        "eps": 0.562251256281407,
        "Q": 1024,
    }
    d = np.arange(triage.Q, dtype=np.float64)
    signed = ((d + triage.Q // 2) % triage.Q) - triage.Q // 2
    raw_shape = sum(
        np.exp(-np.abs(signed + period * triage.Q - triage.M2_PARAMS["mu"]) / triage.M2_PARAMS["scale"])
        for period in (-1, 0, 1)
    )
    shape = raw_shape / raw_shape.sum()
    expected_kernel = (1.0 - triage.M2_PARAMS["eps"]) * shape + triage.M2_PARAMS["eps"] / triage.Q
    expected_kernel /= expected_kernel.sum()
    kernel = triage.wrapped_laplace_kernel()
    assert np.allclose(kernel, expected_kernel)
    assert np.all(np.isfinite(kernel)) and np.all(kernel > 0) and np.isclose(kernel.sum(), 1.0)

    probabilities = triage.m2_conditional_probabilities(np.asarray([0, 1, 1023], dtype=np.uint16))
    prior = triage.build_m2_prior_logp(np.asarray([0, 1, 1023], dtype=np.uint16))
    assert np.all(np.isfinite(probabilities)) and np.all(probabilities > 0)
    assert np.allclose(probabilities.sum(axis=1), 1.0)
    assert np.allclose(np.exp(prior), probabilities)
    assert np.allclose(probabilities[1], np.roll(probabilities[0], 1))
    assert np.allclose(probabilities[2], np.roll(probabilities[0], -1))
    assert "alice" not in inspect.signature(triage.build_m2_prior_logp).parameters
    # Natural-log BP prior and log2 reporting are separate contracts.
    assert np.allclose(prior, np.log(probabilities))
    ce_log2 = -float(np.sum(probabilities[0] * np.log2(probabilities[0])))
    assert np.isfinite(ce_log2) and ce_log2 > 0

    # A synthetic zero only exercises the log-stage floor; no post-floor
    # renormalization is allowed.
    floored = np.zeros((1, triage.Q), dtype=np.float64)
    floored[0, 1:] = 0.5 / (triage.Q - 1)
    monkeypatch.setattr(triage, "m2_conditional_probabilities", lambda _: floored)
    floor_logp = triage.build_m2_prior_logp(np.asarray([0], dtype=np.uint16))
    assert floor_logp[0, 0] == pytest.approx(np.log(1e-300))
    assert np.exp(floor_logp[0, 0]) == pytest.approx(1e-300)
    assert np.sum(np.exp(floor_logp[0])) == pytest.approx(0.5)


def test_interleaver_is_full_bijection_and_mapping_direction_is_exact():
    indptr = np.asarray([0, 2, 4], dtype=np.int32)
    indices = np.asarray([0, 1, 10, 11], dtype=np.int32)
    mapping = triage.build_degree_balanced_interleaver(indptr, indices, n_vars=20, n_symbols=2, info_end=4)
    old_to_phys = mapping["old_to_phys"]
    inverse = mapping["phys_to_old"]
    assert np.array_equal(inverse[old_to_phys], np.arange(20))
    assert np.array_equal(old_to_phys[inverse], np.arange(20))
    report = triage.verify_interleaver(indptr, indices, mapping, n_vars=20)
    assert report["bijection"]
    assert mapping["seed"] == 20260902
    assert np.array_equal(mapping["high_symbol_counts"], np.asarray([2, 2], dtype=np.int32))
    assert np.array_equal(mapping["info_count"], np.asarray([2, 2], dtype=np.int32))
    assert report["row_degree_multiset_preserved"]
    assert report["column_degree_multiset_preserved"]
    assert report["shape_preserved"] and report["rank_preserved"] and report["prefix_nesting_preserved"]
    assert report["all_symbols_have_ten_slots"] and report["high_distribution_valid"]
    assert report["pure_h_four_cycles"] == 0
    assert report["pure_h_collision_pairs"] == 0
    assert report["symbol_sigma_c2"] == 0
    assert report["symbol_collision_rows"] == 0
    mapped = triage.remap_csr(indices, old_to_phys)
    x_phys = np.arange(20, dtype=np.uint8) & 1
    x_old = x_phys[old_to_phys]
    old_syndrome = np.asarray([x_old[0] ^ x_old[1], x_old[2] ^ x_old[3]], dtype=np.uint8)
    new_syndrome = np.asarray([x_phys[mapped[0]] ^ x_phys[mapped[1]], x_phys[mapped[2]] ^ x_phys[mapped[3]]], dtype=np.uint8)
    assert np.array_equal(old_syndrome, new_syndrome)

    # Build H_I by the frozen column direction and check its syndrome algebra.
    h_old = np.zeros((2, 20), dtype=np.uint8)
    h_old[0, indices[:2]] = 1
    h_old[1, indices[2:]] = 1
    h_interleaved = np.zeros_like(h_old)
    h_interleaved[:, old_to_phys] = h_old
    assert np.array_equal((h_interleaved @ x_phys) & 1, (h_old @ x_old) & 1)
    assert np.array_equal(mapping["old_to_phys"], triage.build_degree_balanced_interleaver(indptr, indices, n_vars=20, n_symbols=2, info_end=4)["old_to_phys"])


def test_interleaver_mixed_symbol_and_pure_h_cycle_stats_are_separate():
    indptr = np.asarray([0, 2, 4], dtype=np.int32)
    indices = np.asarray([0, 1, 2, 3], dtype=np.int32)
    mixed = triage.symbol_factor_stats(indptr, indices, n_vars=20, n_symbols=2)
    pure = triage.pure_h_cycle_stats(indptr, indices)
    assert mixed["symbol_sigma_c2"] == 2
    assert mixed["symbol_collision_rows"] == 2
    assert pure == {"four_cycles": 0, "collision_pairs": 0}
    # One check with two bits of one symbol is the frozen tiny calibration.
    tiny = triage.symbol_factor_stats(
        np.asarray([0, 2], dtype=np.int32), np.asarray([0, 1], dtype=np.int32), n_vars=20, n_symbols=2
    )
    assert tiny["symbol_sigma_c2"] == 1
    assert triage.pure_h_cycle_stats(np.asarray([0, 2], dtype=np.int32), np.asarray([0, 1], dtype=np.int32))["four_cycles"] == 0


def test_layered_returns_real_shapes_and_warm_state_is_checked():
    indptr, indices = tiny_graph()
    prior = tiny_prior()
    syndrome = np.asarray([0, 1], dtype=np.uint8)
    with pytest.raises(ValueError):
        triage.run_layered_decoder(prior, syndrome, indptr, indices, 1, np.zeros(5))
    result = triage.run_layered_decoder(prior, syndrome, indptr, indices, 2, np.zeros(indices.size))
    assert result["check_to_variable"].shape == (indices.size,)
    assert result["variable_to_check"].shape == (indices.size,)
    assert result["bit_to_factor"].shape == (2, 10)
    assert result["factor_to_bit"].shape == (2, 10)
    assert result["hard_bits"].shape == (20,)
    assert result["syndrome_observed"].shape == (2,)
    assert result["finite"]
    assert len(result["residuals"]) <= 2
    assert result["edge_updates"] == indices.size * len(result["residuals"])
    assert result["state_evaluations"] == 1024 * result["local_factor_target_updates"]
    assert result["diagnostic_checkpoint_rebuild_target_updates"] == 20


def test_layered_is_row_serial_latest_message_visible_and_matches_reference():
    # Ordered rows share a bit and each touches two bits of symbol 0.
    indptr = np.asarray([0, 3, 6], dtype=np.int32)
    indices = np.asarray([0, 1, 10, 0, 2, 11], dtype=np.int32)
    prior = triage.build_m2_prior_logp(np.asarray([7, 23], dtype=np.uint16))
    syndrome = np.asarray([0, 1], dtype=np.uint8)
    warm = np.asarray([0.30, -0.20, 0.10, -0.40, 0.25, -0.15], dtype=np.float64)

    result = triage.run_layered_decoder(prior, syndrome, indptr, indices, 1, warm)
    expected_c2v, expected_btf, expected_f2b = serial_reference(prior, syndrome, indptr, indices, warm)
    stale_c2v = stale_flooding_reference(prior, syndrome, indptr, indices, warm)
    assert np.allclose(result["check_to_variable"], expected_c2v, rtol=1e-12, atol=1e-12)
    assert not np.allclose(result["check_to_variable"], stale_c2v, rtol=1e-12, atol=1e-12)
    assert np.allclose(result["bit_to_factor"], expected_btf, rtol=1e-12, atol=1e-12)
    assert np.allclose(result["factor_to_bit"], expected_f2b, rtol=1e-12, atol=1e-12)
    assert np.allclose(result["app_raw"], result["factor_to_bit"].reshape(-1) + result["bit_to_factor"].reshape(-1))
    assert result["local_factor_target_updates"] == 40  # 10*2 symbols for each row
    assert result["state_evaluations"] == 1024 * 40
    assert result["edge_updates"] == indices.size
    assert result["diagnostic_checkpoint_rebuild_target_updates"] == 20
    assert result["diagnostic_L0_target_updates"] == 0
    assert result["diagnostic_final_readout_target_updates"] == 0
    assert result["total_target_updates"] == 60

    # Reversing edge order within each row cannot change the row's simultaneous
    # SPA update; compare by (row, variable), not by CSR edge position.
    reversed_indices = np.asarray([10, 1, 0, 11, 2, 0], dtype=np.int32)
    reversed_warm = np.asarray([warm[2], warm[1], warm[0], warm[5], warm[4], warm[3]])
    reordered = triage.run_layered_decoder(prior, syndrome, indptr, reversed_indices, 1, reversed_warm)
    assert row_value_map(indices, result["check_to_variable"], indptr) == pytest.approx(
        row_value_map(reversed_indices, reordered["check_to_variable"], indptr)
    )

    # Every target bit of each affected symbol is recomputed with self-exclusion.
    expected_factor_batch = triage.factor_batch(prior, result["bit_to_factor"])
    assert np.allclose(result["factor_to_bit"], expected_factor_batch, rtol=1e-12, atol=1e-12)


@pytest.mark.parametrize("degree", [1, 2, 3])
@pytest.mark.parametrize("syndrome", [0, 1])
def test_layered_spa_sign_handles_syndrome_and_degree_parity(degree: int, syndrome: int):
    vals = np.linspace(-0.7, 0.9, degree, dtype=np.float64)
    product_values = np.clip(np.tanh(vals / 2.0), -0.999999999999, 0.999999999999)
    sign = (-1.0) ** (syndrome + degree % 2)
    expected = []
    for edge in range(degree):
        product = np.prod(np.delete(product_values, edge)) if degree > 1 else 1.0
        expected.append(
            np.clip(
                2.0 * np.arctanh(np.clip(sign * product, -1.0 + 1e-12, 1.0 - 1e-12)),
                -triage.LLR_CLIP,
                triage.LLR_CLIP,
            )
        )
    assert np.allclose(triage._spa_row(vals, syndrome), expected)


def test_layered_row_snapshot_and_raw_v2c_contract():
    # The public row update uses the un-clipped APP algebra; this value is the
    # contract check used by the plan, independent of any clipped readout.
    raw_app = 25.0
    old_c2v = 1.0
    assert raw_app - old_c2v == 24.0
    values = np.asarray([-2.0, 0.0, 3.0, 0.0], dtype=np.float64)
    summary = triage.summarize_values(values)
    assert summary["zero_count"] == 2
    transition = triage.sign_transition(values, -values)
    assert sum(map(sum, transition)) == values.size

    # With a large incident state and no sweeps, the returned v2c must retain
    # the raw APP algebra rather than a clipped APP.  This gives APP_raw>20.
    indptr = np.asarray([0, 25], dtype=np.int32)
    indices = np.zeros(25, dtype=np.int32)
    prior = triage.build_m2_prior_logp(np.asarray([0], dtype=np.uint16))
    warm = np.ones(25, dtype=np.float64)
    raw_result = triage.run_layered_decoder(prior, np.zeros(1, dtype=np.uint8), indptr, indices, 0, warm)
    assert raw_result["_pre_state"]["app_raw"][0] - warm[0] > triage.LLR_CLIP
    assert raw_result["variable_to_check"][0] > triage.LLR_CLIP


def test_checkpoint_metrics_recompute_syndrome_and_separate_f_s_a_counts():
    indptr = np.asarray([0, 2], dtype=np.int32)
    indices = np.asarray([0, 1], dtype=np.int32)
    prior = triage.build_m2_prior_logp(np.asarray([0], dtype=np.uint16))
    pre_c2v = np.asarray([1.0, -2.0], dtype=np.float64)
    pre_state = triage.rebuild_factor_state(prior, pre_c2v, indptr, indices)
    post_c2v = np.asarray([20.0, 5.0], dtype=np.float64)
    post_btf = np.zeros((1, 10), dtype=np.float64)
    post_btf[0, :2] = post_c2v
    post_f2b = triage.factor_batch(prior, post_btf)
    post_app_raw = post_f2b.reshape(-1) + post_btf.reshape(-1)
    post = {
        "bit_to_factor": post_btf,
        "factor_to_bit": post_f2b,
        "check_to_variable": post_c2v,
        "app_raw": post_app_raw,
        "hard_bits": np.zeros(10, dtype=np.uint8),
        "hard_symbols": np.zeros(1, dtype=np.uint16),
        # Deliberately inconsistent; metrics must use H_arm @ hard_bits.
        "syndrome_observed": np.ones(1, dtype=np.uint8),
        "residuals": [0.25],
        "edge_updates": 2,
        "converged": False,
        "finite": True,
        "max_llr": float(np.max(np.abs(np.clip(post_app_raw, -20, 20)))),
    }
    l0 = triage.factor_batch(prior, np.zeros((1, 10), dtype=np.float64)).reshape(-1)
    metrics = triage.checkpoint_metrics(
        prior, pre_c2v, post, indptr, indices, np.zeros(1, dtype=np.uint8),
        np.zeros(10, dtype=np.uint8), 12, 10, 10, l0_values=l0, pre_state=pre_state,
    )
    assert metrics["candidate_syndrome_violation"] == 0
    assert metrics["syndrome_satisfied"] is True
    assert metrics["candidate_vs_bob_bit_flips"] == 0
    assert metrics["candidate_vs_bob_symbol_flips"] == 0
    assert metrics["max_abs_c2v"] == 20.0
    assert metrics["max_abs_incident_c2v_sum"] == 20.0
    assert metrics["clip_counts"]["c2v_at_clip"] == 1
    assert metrics["clip_counts"]["app_preclip_exceed"] >= 1
    assert metrics["L0"] == triage.summarize_values(l0)
    expected_post_a = post_f2b.reshape(-1) + np.pad(post_c2v, (0, 8))
    assert metrics["A_raw_post"] == triage.summarize_values(expected_post_a)
    assert sum(map(sum, metrics["sign_L0_to_F_post"])) == 10
    assert sum(map(sum, metrics["sign_F_post_to_A_raw_post"])) == 10
    assert metrics["local_factor_target_updates"] == 12
    assert metrics["state_evaluations"] == 1024 * 12
    assert metrics["diagnostic_factor_target_updates"] == 10
    assert metrics["diagnostic_state_evaluations"] == 1024 * 10
    assert metrics["oracle_exact"] is None
    assert metrics["tag_bits"] == 0 and metrics["tag_ok"] == "NOT_APPLICABLE"


def test_accounting_is_monotone_and_separate():
    accounting = triage.new_accounting()
    triage.publish_checkpoint(accounting, 2, first=True)
    assert accounting["disclosed_rows"] == accounting["syndrome_rows_published"] == accounting["syndrome_bits_published"] == 2
    triage.publish_checkpoint(accounting, 5, first=False)
    assert accounting["disclosed_rows"] == accounting["syndrome_rows_published"] == accounting["syndrome_bits_published"] == 5
    assert accounting["control_bits_sent"] == 1
    assert accounting["tag_bits_published"] == 0
    assert accounting["public_disclosure_bits"] == 6
    with pytest.raises(ValueError):
        triage.publish_checkpoint(accounting, 4, first=False)


def test_layered_warm_start_carries_only_old_prefix_and_is_arm_local():
    indptr = np.asarray([0, 1, 2], dtype=np.int32)
    indices = np.asarray([0, 1], dtype=np.int32)
    prior = triage.build_m2_prior_logp(np.asarray([0], dtype=np.uint16))
    syndrome = np.zeros(2, dtype=np.uint8)
    alice = np.zeros(10, dtype=np.uint8)
    bob = np.zeros(10, dtype=np.uint8)

    def run_with_capture():
        calls: list[tuple[int, np.ndarray]] = []

        def decoder(prior_logp, syndrome_target, indptr, indices, max_sweeps, warm):
            calls.append((len(indices), np.asarray(warm).copy()))
            return triage.run_layered_decoder(prior_logp, syndrome_target, indptr, indices, max_sweeps, warm)

        arm = triage.run_arm_synthetic(
            "L", prior, syndrome, alice, bob, indptr, indices, decoder, "layered",
            checkpoint_rows=(1, 2), max_per_checkpoint=1, max_total=2,
        )
        return arm, calls

    arm, calls = run_with_capture()
    assert calls[0][1].tolist() == [0.0]
    assert calls[1][1].shape == (2,)
    assert calls[1][1][1] == 0.0  # newly activated edge is zero
    assert calls[1][1][0] != 0.0  # old active prefix was carried
    assert arm["diagnostic_L0_target_updates"] == 10
    assert arm["diagnostic_checkpoint_rebuild_target_updates"] == 20
    assert arm["diagnostic_final_readout_target_updates"] == 0
    assert arm["diagnostic_factor_target_updates"] == 30
    assert arm["total_target_updates"] == arm["local_factor_target_updates"] + 30
    assert [m["accounting"]["disclosed_rows"] for m in arm["checkpoint_metrics"]] == [1, 2]
    assert [m["accounting"]["control_bits_sent"] for m in arm["checkpoint_metrics"]] == [0, 1]
    assert arm["accounting"]["public_disclosure_bits"] == 3
    assert all(not isinstance(value, np.ndarray) for value in arm.values())

    # A second arm starts from zero rather than sharing mutable c2v state.
    _, second_calls = run_with_capture()
    assert second_calls[0][1].tolist() == [0.0]


def test_arm_budget_guard_zero_balance_and_strict_result_fields():
    indptr = np.asarray([0, 1], dtype=np.int32)
    indices = np.asarray([0], dtype=np.int32)
    prior = triage.build_m2_prior_logp(np.asarray([0], dtype=np.uint16))
    syndrome = np.zeros(1, dtype=np.uint8)
    bits = np.zeros(10, dtype=np.uint8)
    called: list[bool] = []

    def decoder(*args, **kwargs):
        called.append(True)
        return triage.run_layered_decoder(args[0], args[1], args[2], args[3], 1, args[5])

    zero = triage.run_arm_synthetic(
        "L", prior, syndrome, bits, bits, indptr, indices, decoder, "layered",
        checkpoint_rows=(1,), max_per_checkpoint=1, max_total=0,
    )
    assert called == []
    assert zero["status"] == "BUDGET_EXHAUSTED"
    assert zero["attempted_checkpoints"] == 0
    assert zero["diagnostic_L0_target_updates"] == 0
    assert zero["accounting"]["public_disclosure_bits"] == 0

    def over_budget(*args, **kwargs):
        result = triage.run_layered_decoder(args[0], args[1], args[2], args[3], 1, args[5])
        result["residuals"] = [1.0, 2.0]
        return result

    blocked = triage.run_arm_synthetic(
        "L", prior, syndrome, bits, bits, indptr, indices, over_budget, "layered",
        checkpoint_rows=(1,), max_per_checkpoint=1, max_total=1,
    )
    assert blocked["status"] == "BLOCKED" and blocked["stop_reason"] == "budget_guard_failed"
    assert blocked["attempted_checkpoints"] == 0

    def missing_field(*args, **kwargs):
        result = triage.run_layered_decoder(args[0], args[1], args[2], args[3], 1, args[5])
        del result["_pre_state"]
        return result

    malformed = triage.run_arm_synthetic(
        "L", prior, syndrome, bits, bits, indptr, indices, missing_field, "layered",
        checkpoint_rows=(1,), max_per_checkpoint=1, max_total=1,
    )
    assert malformed["status"] == "BLOCKED"
    assert malformed["stop_reason"] == "decoder_result_missing_required_fields"


def test_flooding_counterfactual_uses_actual_iterations_and_final_readout_stage():
    indptr = np.asarray([0, 2, 4], dtype=np.int32)
    indices = np.asarray([0, 1, 2, 3], dtype=np.int32)
    prior = triage.build_m2_prior_logp(np.asarray([0], dtype=np.uint16))
    syndrome = np.zeros(2, dtype=np.uint8)
    bits = np.zeros(10, dtype=np.uint8)
    calls = 0

    def fake_flooding(prior_logp, syndrome_target, *, indptr, indices, max_iter, warm_start_c2v):
        nonlocal calls
        calls += 1
        result = triage.run_layered_decoder(
            prior_logp, syndrome_target, indptr, indices, 1, warm_start_c2v
        )
        # Mimic the old adapter's actual iteration output; the arm runner
        # derives core=actual_iterations*10240 and final-readout=10240/call.
        result["local_factor_target_updates"] = len(result["residuals"]) * 10240
        result.pop("_pre_state")
        return result

    arm = triage.run_arm_synthetic(
        "P", prior, syndrome, bits, bits, indptr, indices, fake_flooding, "flooding",
        checkpoint_rows=(1, 2), max_per_checkpoint=1, max_total=2,
    )
    assert calls == 2
    assert arm["local_factor_target_updates"] == 2 * 10240
    assert arm["state_evaluations"] == 1024 * arm["local_factor_target_updates"]
    assert arm["diagnostic_L0_target_updates"] == 10240
    # ponytail: metrics pre-state rebuild is counted as rebuild, final readout stays separate.
    assert arm["diagnostic_checkpoint_rebuild_target_updates"] == 2 * 10240
    assert arm["diagnostic_final_readout_target_updates"] == 2 * 10240
    assert arm["diagnostic_factor_target_updates"] == 5 * 10240
    assert arm["diagnostic_state_evaluations"] == 1024 * 5 * 10240
    assert arm["total_target_updates"] == 7 * 10240
    assert all(metric["oracle_exact"] is None for metric in arm["checkpoint_metrics"])


@pytest.mark.parametrize(
    ("exception", "stop_reason"),
    [(RuntimeError("boom"), "exception"), (TimeoutError("slow"), "timeout")],
)
def test_arm_exception_and_timeout_preserve_published_accounting(exception, stop_reason):
    indptr = np.asarray([0, 1], dtype=np.int32)
    indices = np.asarray([0], dtype=np.int32)
    prior = triage.build_m2_prior_logp(np.asarray([0], dtype=np.uint16))
    syndrome = np.zeros(1, dtype=np.uint8)
    bits = np.zeros(10, dtype=np.uint8)

    def failing(*args, **kwargs):
        raise exception

    arm = triage.run_arm_synthetic(
        "L", prior, syndrome, bits, bits, indptr, indices, failing, "layered",
        checkpoint_rows=(1,), max_per_checkpoint=1, max_total=1,
    )
    assert arm["status"] == "RESOURCE_BLOCKED" and arm["stop_reason"] == stop_reason
    assert arm["attempted_checkpoints"] == 0
    assert arm["accounting"]["disclosed_rows"] == 1
    assert arm["accounting"]["syndrome_rows_published"] == 1
    assert arm["accounting"]["public_disclosure_bits"] == 1


def test_nonfinite_decoder_is_blocked_after_checkpoint_metrics():
    indptr = np.asarray([0, 2], dtype=np.int32)
    indices = np.asarray([0, 1], dtype=np.int32)
    prior = triage.build_m2_prior_logp(np.asarray([0], dtype=np.uint16))
    syndrome = np.zeros(1, dtype=np.uint8)
    bits = np.zeros(10, dtype=np.uint8)

    def nonfinite(*args, **kwargs):
        result = triage.run_layered_decoder(args[0], args[1], args[2], args[3], 1, args[5])
        result["finite"] = False
        return result

    arm = triage.run_arm_synthetic(
        "L", prior, syndrome, bits, bits, indptr, indices, nonfinite, "layered",
        checkpoint_rows=(1,), max_per_checkpoint=1, max_total=1,
    )
    assert arm["status"] == "RESOURCE_BLOCKED" and arm["stop_reason"] == "nonfinite"
    assert arm["attempted_checkpoints"] == 1
    assert arm["checkpoint_metrics"][0]["finite"] is False
    assert arm["final_syndrome_satisfied"] is False


def test_fake_arm_continues_after_first_syndrome_and_oracles_final_candidate():
    # Both all-zero and all-one candidates satisfy these degree-two checks;
    # the latter still differs from Alice and must be classified as a wrong
    # syndrome collision only after the final checkpoint.
    indptr = np.asarray([0, 2, 4, 6], dtype=np.int32)
    indices = np.asarray([0, 1, 2, 3, 4, 5], dtype=np.int32)
    prior = triage.build_m2_prior_logp(np.asarray([0], dtype=np.uint16))
    syndrome = np.zeros(3, dtype=np.uint8)
    alice = np.zeros(10, dtype=np.uint8)
    bob = np.zeros(10, dtype=np.uint8)
    calls: list[int] = []

    def fake_decoder(prior_logp, syndrome_target, indptr, indices, max_sweeps, warm):
        calls.append(len(syndrome_target))
        result = triage.run_layered_decoder(prior_logp, syndrome_target, indptr, indices, 1, warm)
        if len(syndrome_target) == 1:
            result["hard_bits"] = np.zeros(10, dtype=np.uint8)
            result["hard_symbols"] = np.zeros(1, dtype=np.uint16)
            result["syndrome_observed"] = np.zeros(1, dtype=np.uint8)
        else:
            result["hard_bits"] = np.ones(10, dtype=np.uint8)
            result["hard_symbols"] = np.asarray([63], dtype=np.uint16)
            result["syndrome_observed"] = np.zeros(len(syndrome_target), dtype=np.uint8)
        return result

    arm = triage.run_arm_synthetic(
        "L", prior, syndrome, alice, bob, indptr, indices, fake_decoder,
        "layered", checkpoint_rows=(1, 2, 3), max_per_checkpoint=1, max_total=3,
    )
    assert calls == [1, 2, 3]
    assert arm["first_syndrome_satisfied_ckpt"] == 1
    assert arm["final_checkpoint_rows"] == 3
    assert arm["final_syndrome_satisfied"] is True
    assert arm["final_oracle_exact"] is False
    assert arm["diagnostic_exact"] is False
    assert arm["syndrome_collision_wrong"] is True
    assert arm["tag_bits"] == 0 and arm["tag_ok"] == "NOT_APPLICABLE"
    assert arm["accounting"]["disclosed_rows"] == 3
    assert arm["accounting"]["control_bits_sent"] == 2


def test_cost_projection_formula_is_not_hidden_by_threshold():
    # Reproduce the frozen arithmetic independently on synthetic counters.
    tau, tau_diag, work, diag, overhead = 1e-9, 2e-9, 100, 10240 * 73, 1e-6
    projected = (tau * work + tau_diag * diag + 72 * overhead) * 1.2
    assert projected > 0
    assert projected == pytest.approx((tau * work + tau_diag * diag + 72 * overhead) * 1.2)


def test_real_invocation_reuses_a_and_calls_new_arms_once_in_order():
    calls: list[str] = []
    prepared = {"a_baseline": runner._not_attempted_arm("A", "D1_REUSED")}

    def fake_arm(arm_id: str, _prepared):
        calls.append(arm_id)
        if arm_id == "I":
            return {"arm_id": arm_id, "status": "RESOURCE_BLOCKED", "stop_reason": "nonfinite"}
        return {"arm_id": arm_id, "status": "LADDER_EXHAUSTED", "stop_reason": "ladder_exhausted"}

    arms, status, error = runner.run_real_invocation(
        prepared, triage, arm_runner=fake_arm, clock=lambda: 0.0,
    )
    assert calls == ["L", "I"]
    assert status == "RESOURCE_BLOCKED" and error == "nonfinite"
    assert arms["A"]["stop_reason"] == "D1_REUSED"
    assert arms["L"]["status"] == "LADDER_EXHAUSTED"
    assert arms["I"]["status"] == "RESOURCE_BLOCKED"
    assert arms["P"]["status"] == "NOT_ATTEMPTED"


def test_real_invocation_exception_and_timeout_fail_closed():
    prepared = {"a_baseline": runner._not_attempted_arm("A", "D1_REUSED")}
    for failure, expected_reason in ((RuntimeError("boom"), "exception"), (TimeoutError("slow"), "timeout")):
        calls: list[str] = []

        def failing_arm(arm_id: str, _prepared, failure=failure):
            calls.append(arm_id)
            raise failure

        arms, status, error = runner.run_real_invocation(
            prepared, triage, arm_runner=failing_arm, clock=lambda: 0.0,
        )
        assert calls == ["L"]
        assert status == "RESOURCE_BLOCKED" and expected_reason in str(error)
        assert arms["L"]["status"] == "RESOURCE_BLOCKED"
        assert arms["L"]["stop_reason"] == expected_reason
        assert arms["I"]["status"] == "NOT_ATTEMPTED"
        assert arms["P"]["status"] == "NOT_ATTEMPTED"


def _fresh_test_root() -> Path:
    # Keep these two filesystem tests in a dedicated workspace child rather
    # than pytest's configured basetemp, which may be ACL-protected on Windows.
    root = ROOT.parent / "workspace" / "v72p2d2_orthogonal_test_runtime"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


def test_real_authorization_requires_explicit_real_only_and_keeps_formal_false():
    state_path = _fresh_test_root() / "cycle_state.yaml"
    state_path.write_text(
        "\n".join(
            (
                f"cycle_id: {runner.CYCLE_ID}",
                f"accepted_plan_git_revision: {runner.ACCEPTED_PLAN_GIT_REVISION}",
                "real_execution_authorized: true",
                "formal_execution_authorized: false",
                "execution_count_authorized: 1",
                "execution_count_completed: 0",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    state = runner.require_real_authorization(execute_real=True, cycle_state_path=state_path)
    assert state["execution_count_authorized"] == 1
    with pytest.raises(PermissionError):
        runner.require_real_authorization(execute_real=False, cycle_state_path=state_path)

    formal_state = state_path.read_text(encoding="utf-8").replace(
        "formal_execution_authorized: false", "formal_execution_authorized: true"
    )
    state_path.write_text(formal_state, encoding="utf-8")
    with pytest.raises(PermissionError):
        runner.require_real_authorization(execute_real=True, cycle_state_path=state_path)


def test_real_output_schema_is_scalar_only_and_refuses_overwrite():
    arms = {arm_id: runner._not_attempted_arm(arm_id, "not_run_in_fake_test") for arm_id in runner.ARM_ORDER}
    manifest = {
        "schema": "test_manifest",
        "cycle": runner.CYCLE_ID,
        "arms": arms,
        "tag_semantics": {"tag_bits": 0, "tag_ok": "NOT_APPLICABLE"},
    }
    results = runner._real_results(manifest)
    output = _fresh_test_root() / "diagnostic"
    runner._write_real_outputs(output, manifest, results)
    assert {item.name for item in output.iterdir()} == {
        "manifest.json", "results.json", "table.csv", "report.md",
    }
    payload_text = (output / "results.json").read_text(encoding="utf-8")
    for forbidden in (
        "prior_logp", "syndrome_bytes", "alice_bits", "bob_bits",
        "check_to_variable", "variable_to_check", "factor_to_bit",
    ):
        assert forbidden not in payload_text
    with pytest.raises(FileExistsError):
        runner._write_real_outputs(output, manifest, results)


@pytest.mark.parametrize("remaining", [1, 2, 3, 4, 5, 6, 7, 8, 9])
def test_remaining_budget_runs_capped_sweeps_and_only_zero_refuses(remaining: int):
    # ponytail: max_iter=min(10,720-used); only remaining==0 refuses.
    indptr = np.asarray([0, 1, 2], dtype=np.int32)
    indices = np.asarray([0, 1], dtype=np.int32)
    prior = triage.build_m2_prior_logp(np.asarray([0], dtype=np.uint16))
    syndrome = np.zeros(2, dtype=np.uint8)
    bits = np.zeros(10, dtype=np.uint8)
    arm = triage.run_arm_synthetic(
        "L", prior, syndrome, bits, bits, indptr, indices,
        triage.run_layered_decoder, "layered",
        checkpoint_rows=(1,), max_per_checkpoint=10, max_total=remaining,
    )
    # With remaining budget the single checkpoint must be attempted with capped sweeps.
    assert arm["attempted_checkpoints"] == 1
    assert arm["sweeps_used"] <= remaining
    zero = triage.run_arm_synthetic(
        "L", prior, syndrome, bits, bits, indptr, indices,
        triage.run_layered_decoder, "layered",
        checkpoint_rows=(1,), max_per_checkpoint=10, max_total=0,
    )
    # Zero remaining never calls the decoder and records no work.
    assert zero["attempted_checkpoints"] == 0
    assert zero["status"] == "BUDGET_EXHAUSTED"


def test_preflight_gate_requires_pass_projected_peak_and_synthetic(tmp_path):
    base = {
        "cycle_id": runner.CYCLE_ID,
        "synthetic_only": True,
        "real_decoder_executed": False,
        "status": "PASS",
        "projected_L_wall_s": 100.0,
        "peak_rss_bytes": 1024,
    }
    good = tmp_path / "good.json"
    good.write_text(__import__("json").dumps(base), encoding="utf-8")
    assert runner._preflight_for_manifest(str(good), {})["status"] == "PASS"
    for key, value in [
        ("status", "PLAN_REVISE_REQUIRED"),
        ("projected_L_wall_s", 601.0),
        ("peak_rss_bytes", 2 * 1024**3),
        ("synthetic_only", False),
        ("real_decoder_executed", True),
    ]:
        bad = dict(base)
        bad[key] = value
        path = tmp_path / f"bad_{key}.json"
        path.write_text(__import__("json").dumps(bad), encoding="utf-8")
        with pytest.raises(PermissionError):
            runner._preflight_for_manifest(str(path), {})


def test_runner_has_no_legacy_smoke_coupling():
    source = RUNNER_PATH.read_text(encoding="utf-8")
    assert "v72p2_real_smoke" not in source
    assert "_load_real_smoke_module" not in source
    assert "_current_git_revision" not in source
    core_source = MODULE_PATH.read_text(encoding="utf-8")
    assert "v72p2_real_smoke" not in core_source


def test_runner_authoritative_block_constants_match_core():
    # R2: runner mirrors the core's authoritative block constants.
    assert runner.Q == triage.Q == 1024
    assert runner.N == triage.N == 1024
    assert runner.NBIT == triage.NBIT == 10240
    assert runner.M == triage.M == 9036
    assert runner.NNZ == triage.NNZ == 49620
    assert tuple(runner.CHECKPOINT_ROWS) == tuple(triage.CHECKPOINT_ROWS)


def test_runner_has_no_scattered_block_literals():
    # R2: no function-internal numeric 1024/10240; module level owns them.
    tree = ast.parse(RUNNER_PATH.read_text(encoding="utf-8"))
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for child in ast.walk(node):
                if isinstance(child, ast.Constant) and child.value in (1024, 10240):
                    offenders.append((node.name, child.value, child.lineno))
    assert offenders == []


def _runner_undefined_names() -> list[str]:
    # ponytail: global-Store collection; sufficient for top-level Q/N/NBIT/M focus,
    # not a full pyflakes scope analysis (comprehension/for-target shadowing is approximate).
    import builtins

    tree = ast.parse(RUNNER_PATH.read_text(encoding="utf-8"))
    defined: set[str] = set(dir(builtins)) | {"__name__", "__file__"}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                defined.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            defined.add(node.id)
        elif isinstance(node, ast.arg):
            defined.add(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            defined.add(node.name)
    undefined: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id not in defined:
            undefined.add(node.id)
    return sorted(undefined)


def test_runner_has_no_undefined_names():
    # R2: mechanical undefined-name gate without adding a production dependency.
    assert _runner_undefined_names() == []
    for name in (
        "Q", "N", "NBIT", "M", "CHECKPOINT_ROWS",
        "_derive_syndrome", "_pack_symbols", "_physicalize_bits",
        "_load_registry", "_select_target_session", "_assigned_frame_groups",
        "_read_selected_pairs", "_validate_selected_frame", "_assemble_frame_group",
        "_symbols_to_bits", "_fit_cal_model", "_build_m0_prior",
        "_prepare_real_inputs", "_run_real_arm", "run_real_invocation",
        "_preflight_for_manifest", "_write_real_outputs",
    ):
        assert hasattr(runner, name), name


def _fake_registry_payload(provenance: str) -> dict:
    return {
        "schema": "fake",
        "sessions": [
            {
                "session_id": runner.TARGET_SESSION,
                "source_label": "1M",
                "stage2_CAL_frame_ids": list(range(702, 1726)),
                "stage2_VAL_frame_ids": list(range(1726, 1762)),
                "provenance": provenance,
            }
        ],
    }


def _fake_pairs_df(mutate=None):
    import pandas as pd

    ids = list(range(702, 1726)) + [1726, 1727, 1728, 1729]
    frame_ids = np.repeat(np.asarray(ids, dtype=np.int32), 256)
    pair_idx = np.tile(np.arange(256, dtype=np.int32), len(ids))
    alice = ((frame_ids.astype(np.int64) + pair_idx.astype(np.int64)) % 1024).astype(np.int32)
    bob = ((frame_ids.astype(np.int64) * 3 + pair_idx.astype(np.int64) * 7) % 1024).astype(np.int32)
    frame = pd.DataFrame(
        {"frame_id": frame_ids, "pair_idx": pair_idx, "alice_symbol": alice, "bob_symbol": bob}
    )
    if mutate is not None:
        frame = mutate(frame)
    return frame


def _write_fake_registry_and_d1(tmp_path: Path, provenance: str):
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(_fake_registry_payload(provenance)), encoding="utf-8")
    d1_path = tmp_path / "d1.json"
    d1_path.write_text(json.dumps({"arms": [{"arm": "A", "status": "OK", "iterations_used": 0}]}), encoding="utf-8")
    return registry_path, d1_path


def test_fake_preparation_end_to_end_stops_at_decoder_sentinel(tmp_path, monkeypatch):
    provenance = str(tmp_path / "nonexistent.parquet")
    registry_path, d1_path = _write_fake_registry_and_d1(tmp_path, provenance)
    assert not Path(provenance).exists()
    frame = _fake_pairs_df()
    assert set(frame.columns) == {"frame_id", "pair_idx", "alice_symbol", "bob_symbol"}
    read_calls: list[list[int]] = []

    def fake_read(path, frame_ids):
        read_calls.append([int(v) for v in frame_ids])
        return frame, "predicate_pushdown"

    monkeypatch.setattr(runner, "_read_selected_pairs", fake_read)
    before = set(runner.REAL_OUTPUT_ROOT.iterdir()) if runner.REAL_OUTPUT_ROOT.exists() else set()
    try:
        prepared = runner._prepare_real_inputs(str(registry_path), str(d1_path), triage)
    except NameError as exc:
        pytest.fail(f"preparation raised NameError: {exc}")
    # Registry/filter/validate path used the fake frame without touching real parquet.
    assert len(read_calls) == 1
    assert 1730 not in read_calls[0]
    assert sorted(read_calls[0]) == sorted(list(range(702, 1726)) + [1726, 1727, 1728, 1729])
    assert prepared["read_mode"] == "predicate_pushdown"
    assert prepared["cal_frame_ids"] == list(range(702, 1726))
    assert prepared["block_frame_ids"] == [1726, 1727, 1728, 1729]
    # CAL concatenation and lambda/Ps path.
    assert prepared["model"]["Ps_full"].shape == (1024, 1024)
    assert float(prepared["model"]["selected_lambda"]) in [float(v) for v in runner.LAMBDA_GRID]
    # VAL 4x256 -> 1024 symbols; M0+M2 priors and bit mappings built.
    assert prepared["alice_symbols"].shape == (1024,) and prepared["bob_symbols"].shape == (1024,)
    assert prepared["alice_bits"].shape == (10240,) and prepared["bob_bits"].shape == (10240,)
    assert prepared["prior_m0"].shape == (1024, 1024)
    assert prepared["prior_m0_i"].shape == (1024, 1024)
    assert prepared["prior_m2"].shape == (1024, 1024)
    assert prepared["syndrome"].shape == (9036,) and prepared["syndrome_i"].shape == (9036,)
    assert prepared["indices"].shape == (49620,) and prepared["indices_i"].shape == (49620,)
    # A is read-only reuse with zero decoder calls.
    assert prepared["a_baseline"]["arm_id"] == "A"
    assert prepared["a_baseline"]["tag_bits"] == 0
    # No tag/hash disclosure artifact is generated by preparation.
    assert "hash" not in json.dumps({k: str(type(v)) for k, v in prepared.items()}).lower()
    assert prepared["a_baseline"]["tag_ok"] == "NOT_APPLICABLE"
    # Alice never enters the prior: both builders are Bob-only by signature.
    assert "alice" not in inspect.signature(triage.build_m0_prior_logp).parameters
    assert "alice" not in inspect.signature(runner._build_m0_prior).parameters
    assert np.array_equal(
        prepared["prior_m0"], runner._build_m0_prior(prepared["bob_symbols"], prepared["model"]["Ps_full"])
    )
    # I-coordinate syndrome algebra is consistent with the original graph.
    assert np.array_equal(prepared["syndrome"], prepared["syndrome_i"])
    assert np.array_equal(
        prepared["syndrome_i"],
        runner._derive_syndrome(prepared["alice_bits_i"], prepared["indptr"], prepared["indices_i"]),
    )

    class _Sentinel(Exception):
        pass

    decoder_calls: list[str] = []

    def sentinel_arm(arm_id: str, _prepared):
        decoder_calls.append(arm_id)
        raise _Sentinel(f"stopped at {arm_id}")

    arms, status, error = runner.run_real_invocation(
        prepared, triage, arm_runner=sentinel_arm, clock=lambda: 0.0
    )
    assert decoder_calls == ["L"]
    assert arms["A"]["stop_reason"] == "D1_REUSED"
    assert "A" not in decoder_calls
    assert status == "RESOURCE_BLOCKED" and "exception" in str(error).lower()
    after = set(runner.REAL_OUTPUT_ROOT.iterdir()) if runner.REAL_OUTPUT_ROOT.exists() else set()
    assert after == before


def _assert_prepare_fails_before_decoder(tmp_path, monkeypatch, frame, registry_mutate=None):
    provenance = str(tmp_path / "nonexistent.parquet")
    payload = _fake_registry_payload(provenance)
    if registry_mutate is not None:
        registry_mutate(payload)
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(payload), encoding="utf-8")
    d1_path = tmp_path / "d1.json"
    d1_path.write_text(json.dumps({"arms": [{"arm": "A", "status": "OK"}]}), encoding="utf-8")
    monkeypatch.setattr(runner, "_read_selected_pairs", lambda path, ids: (frame, "predicate_pushdown"))
    decoder_calls: list[str] = []

    def sentinel_arm(arm_id: str, _prepared):
        decoder_calls.append(arm_id)
        raise AssertionError("decoder must not run after failed preparation")

    with pytest.raises((ValueError, PermissionError, FileNotFoundError)):
        prepared = runner._prepare_real_inputs(str(registry_path), str(d1_path), triage)
        runner.run_real_invocation(prepared, triage, arm_runner=sentinel_arm, clock=lambda: 0.0)
    assert decoder_calls == []


def test_fake_preparation_invalid_frames_fail_before_decoder(tmp_path, monkeypatch):
    base = _fake_pairs_df()
    # Missing column.
    _assert_prepare_fails_before_decoder(
        tmp_path, monkeypatch, base.drop(columns=["alice_symbol"])
    )
    # Fewer than 256 rows for one VAL frame.
    def drop_one(frame):
        return frame.drop(frame[(frame["frame_id"] == 1726)].index[:1])

    _assert_prepare_fails_before_decoder(tmp_path, monkeypatch, _fake_pairs_df(drop_one))
    # Incomplete pair_idx (duplicate 0, missing 255) for one VAL frame.
    def dup_pair(frame):
        mutated = frame.copy()
        idx = mutated[(mutated["frame_id"] == 1727)].index
        mutated.loc[idx[255], "pair_idx"] = 0
        return mutated

    _assert_prepare_fails_before_decoder(tmp_path, monkeypatch, _fake_pairs_df(dup_pair))
    # Out-of-range symbol.
    def out_of_range(frame):
        mutated = frame.copy()
        idx = mutated[(mutated["frame_id"] == 1728)].index[0]
        mutated.loc[idx, "alice_symbol"] = 1024
        return mutated

    _assert_prepare_fails_before_decoder(tmp_path, monkeypatch, _fake_pairs_df(out_of_range))


def test_fake_preparation_registry_overread_and_gates_fail_before_decoder(tmp_path, monkeypatch):
    # Over-read 1730: registered VAL block does not begin with the fixed D1 block.
    def shift_val(payload):
        payload["sessions"][0]["stage2_VAL_frame_ids"] = list(range(1730, 1766))

    _assert_prepare_fails_before_decoder(
        tmp_path, monkeypatch, _fake_pairs_df(), registry_mutate=shift_val
    )
    # Preflight failure stops before any decoder.
    bad = {
        "cycle_id": runner.CYCLE_ID,
        "synthetic_only": True,
        "real_decoder_executed": False,
        "status": "PLAN_REVISE_REQUIRED",
        "projected_L_wall_s": 100.0,
        "peak_rss_bytes": 1024,
    }
    bad_path = tmp_path / "bad_preflight.json"
    bad_path.write_text(json.dumps(bad), encoding="utf-8")
    decoder_calls: list[str] = []
    with pytest.raises(PermissionError):
        runner._preflight_for_manifest(str(bad_path), {})
    assert decoder_calls == []
    # Existing output directory refuses before any decoder.
    out_dir = tmp_path / "diagnostic"
    out_dir.mkdir()
    state_path = tmp_path / "cycle_state.yaml"
    state_path.write_text(
        "\n".join(
            (
                f"cycle_id: {runner.CYCLE_ID}",
                f"accepted_plan_git_revision: {runner.ACCEPTED_PLAN_GIT_REVISION}",
                "real_execution_authorized: true",
                "formal_execution_authorized: false",
                "execution_count_authorized: 1",
                "execution_count_completed: 0",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(FileExistsError):
        runner.require_real_authorization(
            execute_real=True, cycle_state_path=state_path, output_path=out_dir
        )
    assert decoder_calls == []
    arms = {arm_id: runner._not_attempted_arm(arm_id, "x") for arm_id in runner.ARM_ORDER}
    manifest = {"arms": arms, "tag_semantics": {"tag_bits": 0, "tag_ok": "NOT_APPLICABLE"}}
    with pytest.raises(FileExistsError):
        runner._write_real_outputs(out_dir, manifest, runner._real_results(manifest))
    assert decoder_calls == []
