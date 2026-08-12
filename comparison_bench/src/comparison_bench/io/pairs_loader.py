from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ["frame_id", "pair_idx", "alice_symbol", "bob_symbol"]
META_COLUMNS = [
    "source_path",
    "loss_db",
    "dimension",
    "bin_width_ps",
    "n_eff_pairs",
    "threshold_ps",
    "effective_pairing_window_ps",
    "processing_rule_version",
    "pairing_path_tag",
    "data_mode",
]

_ALIAS_MAP = {
    "frame": "frame_id",
    "frameid": "frame_id",
    "frame_idx": "frame_id",
    "frame_index": "frame_id",
    "pair": "pair_idx",
    "pair_id": "pair_idx",
    "pair_index": "pair_idx",
    "idx": "pair_idx",
    "alice": "alice_symbol",
    "alice_sym": "alice_symbol",
    "alice_symbols": "alice_symbol",
    "a_symbol": "alice_symbol",
    "a_eff": "alice_symbol",
    "bob": "bob_symbol",
    "bob_sym": "bob_symbol",
    "bob_symbols": "bob_symbol",
    "b_symbol": "bob_symbol",
    "b_eff": "bob_symbol",
}


def _canon(name: Any) -> str:
    return str(name).strip().lower().replace(" ", "_").replace("-", "_")


def _loss_from_path(path: Path) -> float:
    m = re.search(r"(\d+(?:\.\d+)?)dB", str(path), re.IGNORECASE)
    return float(m.group(1)) if m else float("nan")


def _sidecar_metadata(path: Path) -> dict[str, Any]:
    meta_path = path / "sidecar_meta.json"
    meta: dict[str, Any] = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    used = (((meta.get("materialize_params") or {}).get("used_params") or {}) if isinstance(meta, dict) else {})
    point = meta.get("point") or {}
    diagnostics = meta.get("diagnostics") or {}
    occupancy = used.get("occupancy_filter") or {}
    return {
        "source_path": str(path),
        "loss_db": _loss_from_path(path),
        "dimension": used.get("dimension") or point.get("d") or meta.get("d_eff") or meta.get("q"),
        "bin_width_ps": used.get("bin_width_ps") or point.get("bw"),
        "n_eff_pairs": used.get("n_pairs_actual") or diagnostics.get("n_pairs_actual") or meta.get("n_symbols"),
        "threshold_ps": occupancy.get("threshold_ps") or used.get("nearest_threshold_ps"),
        "effective_pairing_window_ps": used.get("coincidence_window_ps") or used.get("coinc_window_override_ps"),
        "processing_rule_version": "sidecar_a_eff_b_eff_v1",
        "pairing_path_tag": used.get("pairing_mode") or meta.get("sequence_source_mode"),
        "data_mode": "real_data",
    }


def _load_sidecar_pair_dir(path: Path) -> pd.DataFrame:
    a_path = path / "a_eff.npy"
    b_path = path / "b_eff.npy"
    if not a_path.exists() or not b_path.exists():
        raise FileNotFoundError(f"sidecar directory must contain a_eff.npy and b_eff.npy: {path}")
    alice = np.asarray(np.load(a_path), dtype=np.int64).reshape(-1)
    bob = np.asarray(np.load(b_path), dtype=np.int64).reshape(-1)
    n = int(min(alice.size, bob.size))
    if n <= 0:
        raise ValueError(f"empty sidecar symbol arrays: {path}")
    meta = _sidecar_metadata(path)
    df = pd.DataFrame({
        "frame_id": np.zeros(n, dtype=np.int64),
        "pair_idx": np.arange(n, dtype=np.int64),
        "alice_symbol": alice[:n],
        "bob_symbol": bob[:n],
    })
    for key, value in meta.items():
        df[key] = value
    return df


def load_pairs_table(path: Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    if p.is_dir():
        return _load_sidecar_pair_dir(p)
    if p.suffix.lower() == ".csv":
        return pd.read_csv(p)
    if p.suffix.lower() in (".parquet", ".pq"):
        try:
            return pd.read_parquet(p)
        except Exception:
            return pd.read_pickle(p)
    raise ValueError(f"Unsupported pairs table format: {p.suffix}")


def normalize_pair_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename: dict[Any, str] = {}
    used: set[str] = set()
    for col in df.columns:
        c = _canon(col)
        target = _ALIAS_MAP.get(c, c)
        if target in REQUIRED_COLUMNS or target in META_COLUMNS:
            if target not in used:
                rename[col] = target
                used.add(target)
    out = df.rename(columns=rename).copy()
    missing = [c for c in REQUIRED_COLUMNS if c not in out.columns]
    if missing:
        raise ValueError(f"Missing required pair columns after normalization: {missing}")
    for col in REQUIRED_COLUMNS:
        out[col] = pd.to_numeric(out[col], errors="raise").astype("int64")
    return out
