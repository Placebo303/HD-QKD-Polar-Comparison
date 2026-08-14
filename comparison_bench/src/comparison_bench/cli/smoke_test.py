from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import load_config
from ..pipeline.run_ir_benchmark import benchmark_from_yaml
from ..metrics.summary import summarize_methods
from ..utils.paths import repo_root


def _write_synth_pairs(path: Path, dimension: int, frame_len_symbols: int, n_frames: int, ser: float, seed: int = 1234) -> None:
    rng = np.random.default_rng(seed)
    n = int(frame_len_symbols) * int(n_frames)
    alice = rng.integers(0, int(dimension), size=n, dtype=np.int64)
    bob = alice.copy()
    flip = rng.random(n) < float(ser)
    offsets = rng.integers(1, int(dimension), size=int(np.count_nonzero(flip)), dtype=np.int64)
    bob[flip] = (bob[flip] + offsets) % int(dimension)
    df = pd.DataFrame({
        "frame_id": np.repeat(np.arange(n_frames), frame_len_symbols),
        "pair_idx": np.tile(np.arange(frame_len_symbols), n_frames),
        "alice_symbol": alice,
        "bob_symbol": bob,
        "dimension": int(dimension),
        "n_eff_pairs": int(n),
        "processing_rule_version": "synthetic_qary_symmetric_v1",
        "pairing_path_tag": "synthetic",
    })
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run synthetic comparison smoke test.")
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    cfg_path = Path(args.config)
    cfg = load_config(cfg_path)
    dataset = cfg["datasets"][0]
    path = Path(dataset["path"])
    if not path.is_absolute():
        path = repo_root() / path
    _write_synth_pairs(
        path,
        int(dataset.get("dimension", 8)),
        int(dataset.get("frame_len_symbols", 64)),
        int(dataset.get("n_frames", 8)),
        float(dataset.get("ser", 0.05)),
    )
    results, frames = benchmark_from_yaml(cfg_path)
    out_dir = Path(cfg.get("global", {}).get("output_dir", "comparison_bench/outputs_comparison"))
    if not out_dir.is_absolute():
        out_dir = repo_root() / out_dir
    summary = summarize_methods(results)
    summary.to_csv(out_dir / "ir_method_summary.csv", index=False)
    required = {"polar_existing", "cascade_lite", "layered_ldpc_lite", "qldpc_reference"}
    got = set(results["method"].astype(str))
    if not required.issubset(got):
        raise SystemExit(f"missing methods in smoke output: {sorted(required - got)}")
    if frames.empty:
        raise SystemExit("smoke frame output is empty")
    print(f"smoke ok: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
