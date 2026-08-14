from __future__ import annotations

import argparse
from pathlib import Path

from ..io.dataset_builder import build_frame_batch, frame_batch_to_table
from ..io.pairs_loader import load_pairs_table
from ..io.table_store import write_table
import pandas as pd


def _sidecar_points(root: Path) -> list[Path]:
    points: list[Path] = []
    for a_path in root.rglob("a_eff.npy"):
        point = a_path.parent
        if (point / "b_eff.npy").exists():
            points.append(point)
    return sorted(points, key=lambda p: str(p).lower())


def _dataset_id_from_sidecar(path: Path, default_prefix: str) -> str:
    parts = path.parts
    token = path.parent.name if path.name.lower().startswith("blk") else path.name
    if path.name.lower().startswith("blk") and len(path.parts) >= 2:
        token = path.parts[-2]
    return f"{default_prefix}_{token}_{path.name}".replace("-", "_")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a normalized comparison frame batch table.")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--dimension", type=int, default=0)
    ap.add_argument("--frame-len-symbols", type=int, required=True)
    ap.add_argument("--dataset-id", default="")
    ap.add_argument("--scan-sidecars", action="store_true", help="Recursively load all sidecar directories containing a_eff.npy and b_eff.npy.")
    args = ap.parse_args()
    in_path = Path(args.input)
    tables = []
    if args.scan_sidecars:
        points = _sidecar_points(in_path)
        if not points:
            raise SystemExit(f"no sidecar a_eff/b_eff pairs found under {in_path}")
        prefix = args.dataset_id or "real_sidecar"
        for point in points:
            df = load_pairs_table(point)
            dim = int(args.dimension or df.get("dimension", pd.Series([0])).iloc[0])
            if dim <= 1:
                raise SystemExit(f"missing dimension for sidecar point {point}")
            batch = build_frame_batch(df, _dataset_id_from_sidecar(point, prefix), dim, args.frame_len_symbols)
            batch.metadata["source_path"] = str(point)
            batch.metadata.setdefault("data_mode", "real_data")
            tables.append(frame_batch_to_table(batch))
    else:
        if int(args.dimension) <= 1:
            raise SystemExit("--dimension is required for non-scan builds")
        df = load_pairs_table(in_path)
        batch = build_frame_batch(df, args.dataset_id or in_path.stem, args.dimension, args.frame_len_symbols)
        batch.metadata["source_path"] = str(in_path)
        tables.append(frame_batch_to_table(batch))
    out_df = pd.concat(tables, ignore_index=True) if len(tables) > 1 else tables[0]
    write_table(out_df, Path(args.output))
    print(f"wrote frame batch: {args.output}")
    print(f"datasets: {out_df['dataset_id'].nunique()} rows: {len(out_df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
