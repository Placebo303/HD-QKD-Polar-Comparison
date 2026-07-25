from __future__ import annotations

import numpy as np

from comparison_bench.src.comparison_bench.methods.layered_ldpc_lite import _classify_status, split_symbol_bitplanes


def test_split_symbol_bitplanes_gray():
    planes = split_symbol_bitplanes(np.asarray([0, 1, 2, 3]), 4, mapping="gray")
    assert len(planes) == 2
    assert planes[0].tolist() == [0, 0, 1, 1]
    assert planes[1].tolist() == [0, 1, 1, 0]


def test_layered_ldpc_lite_status_rules():
    assert _classify_status(8, 0, 0, 0.05, 0.20, True) == "experimental_failed"
    assert _classify_status(8, 0, 8, 0.05, 0.05, True) == "decode_failed"
    assert _classify_status(8, 0, 0, 0.05, 0.04, True) == "no_verified_success"
    assert _classify_status(8, 1, 0, 0.05, 0.04, True) == "ok"
    assert _classify_status(8, 1, 0, 0.05, 0.04, False) == "unavailable"


def test_layered_ldpc_lite_runs_and_does_not_mislabel_failure():
    from comparison_bench.src.comparison_bench.methods.layered_ldpc_lite import run_layered_ldpc_lite
    from comparison_bench.src.comparison_bench.types import FrameBatch, IRRunConfig
    alice = np.tile(np.arange(8), 8).reshape(1, 64) % 8
    bob = alice.copy()
    bob[0, 0] = (bob[0, 0] + 1) % 8
    batch = FrameBatch("ds", alice, bob, 8, 64, {"mapping": "gray", "parity_fraction": 0.75, "column_weight": 3})
    cfg = IRRunConfig("layered_ldpc_lite", "gray_hard_ldpc", 8, 64, 20)
    result = run_layered_ldpc_lite(batch, cfg)
    status = result.metadata["method_status"]
    assert status in {"ok", "experimental_failed", "decode_failed", "no_verified_success", "unavailable"}
    if status == "ok":
        assert result.n_frames_success > 0
        assert result.post_ir_ser <= result.raw_ser
    else:
        assert not (result.n_frames_success == 0 and result.post_ir_ser > result.raw_ser and status == "ok")
    assert result.n_frames_attempted == 1
    assert len(result.metadata["frame_results"]) == 1
    assert result.leak_EC_actual_bits > 0
