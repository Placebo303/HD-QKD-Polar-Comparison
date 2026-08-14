from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ..types import FrameBatch
from .pairs_loader import META_COLUMNS, normalize_pair_columns


def build_frame_batch(
    df: pd.DataFrame,
    dataset_id: str,
    dimension: int,
    frame_len_symbols: int,
    alice_col: str = "alice_symbol",
    bob_col: str = "bob_symbol",
    frame_col: str = "frame_id",
    pair_col: str = "pair_idx",
) -> FrameBatch:
    explicit = {alice_col: "alice_symbol", bob_col: "bob_symbol", frame_col: "frame_id", pair_col: "pair_idx"}
    explicit = {k: v for k, v in explicit.items() if k in df.columns and k != v}
    pre = df.rename(columns=explicit).copy() if explicit else df.copy()
    work = normalize_pair_columns(pre)
    work = work.sort_values(["frame_id", "pair_idx"]).reset_index(drop=True)
    q = int(dimension)
    frame_len = int(frame_len_symbols)
    if q <= 1 or frame_len <= 0:
        raise ValueError("dimension and frame_len_symbols must be positive")
    alice = pd.to_numeric(work["alice_symbol"], errors="raise").to_numpy(dtype=np.int64)
    bob = pd.to_numeric(work["bob_symbol"], errors="raise").to_numpy(dtype=np.int64)
    if np.any(alice < 0) or np.any(alice >= q) or np.any(bob < 0) or np.any(bob >= q):
        raise ValueError("alice/bob symbols are outside [0, dimension)")
    n_complete = int(min(alice.size, bob.size) // frame_len)
    if n_complete <= 0:
        raise ValueError("not enough rows for one complete frame")
    n_keep = n_complete * frame_len
    alice_frames = alice[:n_keep].reshape(n_complete, frame_len)
    bob_frames = bob[:n_keep].reshape(n_complete, frame_len)
    metadata: dict[str, Any] = {
        "rows_input": int(len(work)),
        "rows_used": int(n_keep),
        "rows_dropped_tail": int(len(work) - n_keep),
    }
    for col in META_COLUMNS:
        if col in work.columns:
            vals = work[col].dropna().unique()
            if len(vals) == 1:
                v = vals[0]
                metadata[col] = v.item() if hasattr(v, "item") else v
            elif len(vals) > 1:
                metadata[col] = [v.item() if hasattr(v, "item") else v for v in vals[:20]]
    return FrameBatch(
        dataset_id=str(dataset_id),
        alice_symbols=alice_frames,
        bob_symbols=bob_frames,
        dimension=q,
        frame_len_symbols=frame_len,
        metadata=metadata,
    )


def frame_batch_to_table(batch: FrameBatch) -> pd.DataFrame:
    rows = []
    scalar_meta: dict[str, Any] = {}
    for key, value in batch.metadata.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            scalar_meta[key] = value
        elif hasattr(value, "item"):
            try:
                scalar_meta[key] = value.item()
            except Exception:
                pass
    for frame_idx in range(int(batch.alice_symbols.shape[0])):
        for pair_idx in range(int(batch.frame_len_symbols)):
            row = {
                "dataset_id": batch.dataset_id,
                "frame_id": frame_idx,
                "pair_idx": pair_idx,
                "alice_symbol": int(batch.alice_symbols[frame_idx, pair_idx]),
                "bob_symbol": int(batch.bob_symbols[frame_idx, pair_idx]),
                "dimension": int(batch.dimension),
                "frame_len_symbols": int(batch.frame_len_symbols),
            }
            row.update({k: v for k, v in scalar_meta.items() if k not in row})
            rows.append(row)
    return pd.DataFrame(rows)


def table_to_frame_batch(df: pd.DataFrame, dataset_id: str | None = None) -> FrameBatch:
    work = normalize_pair_columns(df)
    if "dimension" not in work.columns or "frame_len_symbols" not in work.columns:
        raise ValueError("frame batch table must include dimension and frame_len_symbols")
    dim = int(pd.to_numeric(work["dimension"], errors="raise").iloc[0])
    flen = int(pd.to_numeric(work["frame_len_symbols"], errors="raise").iloc[0])
    ds = dataset_id or str(work.get("dataset_id", pd.Series(["dataset"])).iloc[0])
    return build_frame_batch(work, ds, dim, flen)



def table_to_frame_batches(df: pd.DataFrame, dataset_id: str | None = None) -> list[FrameBatch]:
    if dataset_id:
        return [table_to_frame_batch(df, dataset_id)]
    work = df.copy()
    if "dataset_id" not in work.columns:
        return [table_to_frame_batch(work, None)]
    batches: list[FrameBatch] = []
    for ds, group in work.groupby("dataset_id", sort=True, dropna=False):
        batches.append(table_to_frame_batch(group.reset_index(drop=True), str(ds)))
    return batches
