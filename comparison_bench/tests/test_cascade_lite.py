from __future__ import annotations

import numpy as np

from comparison_bench.src.comparison_bench.methods.cascade_lite import symbols_to_bits_gray, symbols_to_bits_natural


def test_gray_and_natural_mapping():
    symbols = np.asarray([0, 1, 2, 3])
    assert symbols_to_bits_natural(symbols, 4).reshape(4, 2).tolist() == [[0, 0], [0, 1], [1, 0], [1, 1]]
    assert symbols_to_bits_gray(symbols, 4).reshape(4, 2).tolist() == [[0, 0], [0, 1], [1, 1], [1, 0]]



def test_cascade_lite_internal_runs_and_reports_status():
    from comparison_bench.src.comparison_bench.methods.cascade_lite import run_cascade_lite
    from comparison_bench.src.comparison_bench.types import FrameBatch, IRRunConfig

    alice = np.tile(np.arange(8), 16).reshape(2, 64) % 8
    bob = alice.copy()
    bob[0, 0] = (bob[0, 0] + 1) % 8
    bob[1, 7] = (bob[1, 7] + 2) % 8
    batch = FrameBatch("ds", alice, bob, 8, 64, {"mapping": "gray", "cascade_passes": 4, "cascade_seed": 7})
    cfg = IRRunConfig("cascade_lite", "gray", 8, 64, 20)
    result = run_cascade_lite(batch, cfg)
    assert result.n_frames_attempted == 2
    assert result.metadata["method_status"] != "unavailable"
    assert result.metadata["backend_status"] == "internal_cascade_lite"
    assert len(result.metadata["frame_results"]) == 2
    assert result.leak_EC_actual_bits > 0
    if result.metadata["method_status"] == "ok":
        assert result.n_frames_success > 0
        assert result.post_ir_ser <= result.raw_ser
