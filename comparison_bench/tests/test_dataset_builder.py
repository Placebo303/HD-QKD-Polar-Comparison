from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd

from comparison_bench.src.comparison_bench.io.dataset_builder import build_frame_batch, frame_batch_to_table, table_to_frame_batch
from comparison_bench.src.comparison_bench.io.pairs_loader import load_pairs_table, normalize_pair_columns
from comparison_bench.src.comparison_bench.metrics.summary import summarize_methods


def test_normalize_pair_columns_aliases():
    df = pd.DataFrame({"frame": [0], "pair_id": [0], "alice": [1], "bob": [2]})
    out = normalize_pair_columns(df)
    assert ["frame_id", "pair_idx", "alice_symbol", "bob_symbol"] == list(out.columns)


def test_build_frame_batch_sorts_and_truncates_metadata():
    df = pd.DataFrame({
        "frame_id": [0, 0, 1, 1, 2],
        "pair_idx": [1, 0, 1, 0, 0],
        "alice_symbol": [1, 0, 3, 2, 1],
        "bob_symbol": [1, 0, 2, 2, 1],
        "loss_db": [20, 20, 20, 20, 20],
    })
    batch = build_frame_batch(df, "ds", 4, 2)
    assert batch.alice_symbols.shape == (2, 2)
    assert batch.alice_symbols[0].tolist() == [0, 1]
    assert batch.metadata["rows_dropped_tail"] == 1
    assert batch.metadata["loss_db"] == 20



def test_sidecar_directory_loader_and_metadata_roundtrip():
    sidecar = Path("comparison_bench/outputs_comparison/test_fixtures/Type2_5s_20dB/sidecars/d8_bw180/blk0")
    sidecar.mkdir(parents=True, exist_ok=True)
    np.save(sidecar / "a_eff.npy", np.arange(8, dtype=np.int64))
    np.save(sidecar / "b_eff.npy", np.arange(8, dtype=np.int64))
    (sidecar / "sidecar_meta.json").write_text(json.dumps({
        "point": {"d": 8, "bw": 180},
        "n_symbols": 8,
        "materialize_params": {"used_params": {"dimension": 8, "bin_width_ps": 180, "n_pairs_actual": 8, "nearest_threshold_ps": 40000, "pairing_mode": "nearest"}},
    }), encoding="utf-8")
    df = load_pairs_table(sidecar)
    assert {"frame_id", "pair_idx", "alice_symbol", "bob_symbol", "data_mode"}.issubset(df.columns)
    batch = build_frame_batch(df, "real", 8, 4)
    assert batch.alice_symbols.shape == (2, 4)
    assert batch.metadata["bin_width_ps"] == 180
    assert batch.metadata["data_mode"] == "real_data"
    table = frame_batch_to_table(batch)
    assert "bin_width_ps" in table.columns
    restored = table_to_frame_batch(table, "real")
    assert restored.metadata["bin_width_ps"] == 180
    assert restored.metadata["data_mode"] == "real_data"


def test_summary_groups_by_data_mode():
    df = pd.DataFrame({
        "dataset_id": ["ds", "ds"],
        "data_mode": ["synthetic", "real_data"],
        "method": ["cascade_lite", "cascade_lite"],
        "method_variant": ["gray", "gray"],
        "method_status": ["ok", "ok"],
        "accepted_frame_fraction": [1.0, 0.5],
    })
    out = summarize_methods(df)
    assert sorted(out["data_mode"].tolist()) == ["real_data", "synthetic"]
