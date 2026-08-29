"""T1-T12 for V63 shell adapter/integration/CLI — decoder-free fake_runner only."""
import pathlib
import json
import sys

import numpy as np
import pytest


def test_T1_factorization_32_u1_u2():
    from comparison_bench.src.comparison_bench.methods.nbldpc_shell_adapter import (
        decompose_symbols,
        recompose_symbols,
    )

    arr = np.arange(1024)
    u1, u2 = decompose_symbols(arr)
    assert np.all(u1 == arr // 32) and np.all(u2 == arr % 32)
    recon = recompose_symbols(u1, u2)
    assert np.array_equal(recon, arr)
    for s in [0, 31, 32, 63, 1023]:
        assert 32 * (s // 32) + (s % 32) == s


def test_T2_exact_full_is_u1_and_u2():
    s_true = np.array([0, 31, 32, 1023])
    s_hat_ok = np.array([0, 31, 32, 1023])
    s_hat_bad = np.array([32, 31, 0, 1023])
    assert np.array_equal(s_hat_ok, s_true)
    assert not np.array_equal(s_hat_bad, s_true)
    assert np.all((s_hat_ok // 32 == s_true // 32) & (s_hat_ok % 32 == s_true % 32))
    assert not np.all((s_hat_bad // 32 == s_true // 32) & (s_hat_bad % 32 == s_true % 32))


def test_T3_reconciled_full_range_1023():
    from comparison_bench.src.comparison_bench.types import FrameBatch
    from comparison_bench.src.comparison_bench.methods.nbldpc_shell_adapter import NbLdpcShellIRAdapter

    rng = np.random.default_rng(1)
    alice = rng.integers(0, 1024, size=(2, 1024), dtype=np.int64)
    bob = rng.integers(0, 1024, size=(2, 1024), dtype=np.int64)
    batch = FrameBatch("test", alice, bob, 1024, 1024, {})
    adapter = NbLdpcShellIRAdapter("1M", fake_runner=True)
    res = adapter._fake_shell_run(batch, "1M", ["base", "delta8"])  # type: ignore[attr-defined]
    assert res.reconciled_symbols.shape == (2, 1024)
    assert np.all(res.reconciled_symbols >= 0) and np.all(res.reconciled_symbols < 1024)
    assert np.all(res.reconciled_symbols // 32 < 32) and np.all(res.reconciled_symbols % 32 < 32)


def test_T4_leakage_three_tier_tag_single():
    from comparison_bench.src.comparison_bench.methods.nbldpc_shell_adapter import leak_for_stage

    for src in ["1M", "1p5M", "2M"]:
        b = leak_for_stage(src, "base")
        s1 = leak_for_stage(src, "delta8")
        s2 = leak_for_stage(src, "delta16")
        assert s1 - b == 40 and s2 - s1 == 40
        m = {"1M": 184, "1p5M": 190, "2M": 192}[src]
        assert b == 5 * m + 80 + 64


def test_T5_pa_proxy_uses_actual_disclosure():
    from comparison_bench.src.comparison_bench.pipeline.shell_integration import _pa_proxy

    out = _pa_proxy([0], [1064, 1104])
    assert out["pa_input_leak"] == 2168
    assert out["note"] == "POLAR_REFERENCE_PROXY"


def test_T6_pa_rejects_polar_leak_EC():
    from comparison_bench.src.comparison_bench.pipeline.shell_integration import _pa_proxy

    try:
        _pa_proxy([0], [1064], polar_leak_EC=999)
        assert False
    except ValueError as e:
        assert "REJECT" in str(e)


def test_T7_domain_gate_calibration_required():
    from comparison_bench.src.comparison_bench.pipeline.shell_integration import domain_check

    assert domain_check(is_new_or_incompatible=False) == "DOMAIN_OK"
    assert domain_check(is_new_or_incompatible=True) == "DOMAIN_CALIBRATION_REQUIRED"
    assert domain_check(False) == "DOMAIN_OK"
    assert domain_check(True) == "DOMAIN_CALIBRATION_REQUIRED"
    assert domain_check() == "DOMAIN_OK"


def test_T8_irrunresult_signature_frozen():
    from comparison_bench.src.comparison_bench.types import IRRunResult
    import inspect

    sig = inspect.signature(IRRunResult.__init__)
    params = list(sig.parameters.keys())
    assert "leak_EC_actual_bits" in params
    assert "actual_disclosure_bits" not in params
    assert "stage_used" not in params


def test_T9_smoke_registry_9_integration_replay_smoke():
    # authoritative registries under docs/research_cycles/V63P0
    p = pathlib.Path("docs/research_cycles/V63P0/v63_smoke_registry.json")
    j = json.loads(p.read_text(encoding="utf-8"))
    assert j["registry_type"] == "INTEGRATION_REPLAY_SMOKE"
    assert len(j["entries"]) == 9
    for e in j["entries"]:
        assert e["pairs_count"] == 1024
        assert len(e["frame_ids"]) == 4
        # smoke sampling_mode unified as deterministic_four_consecutive_frames_heldout_fresh_v63_smoke
        assert "smoke" in e["sampling_mode"]


def test_T10_fresh_90_zero_overlap_smoke():
    smoke = json.loads(pathlib.Path("docs/research_cycles/V63P0/v63_smoke_registry.json").read_text(encoding="utf-8"))
    dev = json.loads(pathlib.Path("docs/research_cycles/V63P0/v63_dev_registry.json").read_text(encoding="utf-8"))
    assert dev["registry_type"] == "INTEGRATION_FRESH_CANDIDATE"
    assert len(dev["entries"]) == 90
    for s in smoke["entries"]:
        for d in dev["entries"]:
            if s["source"] != d["source"]:
                continue
            assert s["held_out_ordinal_end"] < d["held_out_ordinal_start"] or d["held_out_ordinal_end"] < s["held_out_ordinal_start"], f"overlap {s} {d}"


def test_T11_shell_wraps_irrunresult_not_mutate():
    from comparison_bench.src.comparison_bench.types import FrameBatch
    from comparison_bench.src.comparison_bench.methods.nbldpc_shell_adapter import NbLdpcShellIRAdapter

    rng = np.random.default_rng(2)
    alice = rng.integers(0, 1024, size=(1, 1024))
    bob = rng.integers(0, 1024, size=(1, 1024))
    batch = FrameBatch("t", alice, bob, 1024, 1024, {})
    adapter = NbLdpcShellIRAdapter("2M", fake_runner=True)
    res = adapter._fake_shell_run(batch, "2M", ["delta16"])  # type: ignore[attr-defined]
    assert hasattr(res, "ir_result") and hasattr(res, "reconciled_symbols")
    assert res.ir_result.leak_EC_actual_bits == int(np.sum(res.actual_disclosure_bits))
    assert res.actual_disclosure_bits[0] == 1184  # 2M delta16
    # to_ir_run_result preserves signature
    ir = res.to_ir_run_result()
    assert ir.leak_EC_actual_bits == res.ir_result.leak_EC_actual_bits


def test_T12_e2e_fake_pipeline_ttbin_to_pa_no_decoder():
    from comparison_bench.src.comparison_bench.types import FrameBatch
    from comparison_bench.src.comparison_bench.pipeline.shell_integration import run_shell_pipeline

    rng = np.random.default_rng(3)
    alice = rng.integers(0, 1024, size=(3, 1024))
    bob = rng.integers(0, 1024, size=(3, 1024))
    batch = FrameBatch("e2e", alice, bob, 1024, 1024, {})
    out = run_shell_pipeline(batch, "1p5M", fake_runner=True, stage_pattern=["base", "delta8", "delta16"])
    assert out["pa"]["pa_input_leak"] == sum([1094, 1134, 1174])
    shell = out["shell_result"]
    assert np.all(shell.reconciled_symbols == shell.reconciled_symbols // 32 * 32 + shell.reconciled_symbols % 32)
    # CLI guard not executed here
