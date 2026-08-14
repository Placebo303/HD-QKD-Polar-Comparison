from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from comparison_bench.src.comparison_bench.io.polar_existing_bridge import run_polar_existing
from comparison_bench.src.comparison_bench.types import FrameBatch, IRRunConfig


def test_polar_existing_bridge_read_mode():
    out_dir = Path("comparison_bench/outputs_comparison/test_fixtures")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "real_polar_max_pie_grid.csv"
    pd.DataFrame([{
        "dataset_id": "ds",
        "dimension": 8,
        "raw_ser": 0.05,
        "raw_ber": 0.02,
        "total_leak_ec_bits": 100,
        "block_success_rate": 0.5,
    }]).to_csv(out, index=False)
    batch = FrameBatch("ds", np.zeros((2, 4), dtype=int), np.zeros((2, 4), dtype=int), 8, 4, {"polar_existing_output": str(out)})
    cfg = IRRunConfig("polar_existing", "read_existing", 8, 4, 0)
    result = run_polar_existing(batch, cfg)
    assert result.metadata["method_status"] == "ok"
    assert result.n_frames_success == 1
    assert result.leak_EC_actual_bits == 100
