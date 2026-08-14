from __future__ import annotations

import numpy as np

from comparison_bench.src.comparison_bench.methods.qldpc_reference import run_qldpc_reference
from comparison_bench.src.comparison_bench.types import FrameBatch, IRRunConfig


def test_qldpc_reference_is_executable_reference():
    batch = FrameBatch("ds", np.zeros((1, 8), dtype=int), np.ones((1, 8), dtype=int), 2, 8, {"qldpc_seed": 5})
    cfg = IRRunConfig("qldpc_reference", "offline_reference", 2, 8, 10)
    result = run_qldpc_reference(batch, cfg)
    assert result.metadata["method_status"] == "reference"
    assert "qary_ldpc_reference_qary_hard_syndrome_bf" in result.metadata["backend_status"]
    assert "not a full industrial qLDPC implementation" in result.metadata["notes"]
    assert result.n_frames_attempted == 1
    assert len(result.metadata["frame_results"]) == 1
    assert result.leak_EC_actual_bits > 0
