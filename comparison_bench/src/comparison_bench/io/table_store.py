from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_table(df: pd.DataFrame, path: Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix.lower() in (".parquet", ".pq"):
        try:
            df.to_parquet(p, index=False)
        except Exception:
            df.to_pickle(p)
        return
    if p.suffix.lower() == ".json":
        df.to_json(p, orient="records", indent=2)
        return
    df.to_csv(p, index=False)


def read_table(path: Path) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() in (".parquet", ".pq"):
        try:
            return pd.read_parquet(p)
        except Exception:
            return pd.read_pickle(p)
    if p.suffix.lower() == ".json":
        return pd.read_json(p)
    return pd.read_csv(p)
