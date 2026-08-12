"""Read-only confirmation array access for the v5 partition lock.

Introduces the first confirmation array API (Phase 4).  The partition
module stays frozen and does not expose confirmation arrays.
"""
from __future__ import annotations
import numpy as np
from typing import Any, Mapping, Tuple

from . import ldpc_v4_10db_source as source

N = 256
Q = 1024

_SOURCE_LOCK_CACHE: dict[str, Any] | None = None


def _get_source_lock() -> dict[str, Any]:
    global _SOURCE_LOCK_CACHE
    if _SOURCE_LOCK_CACHE is None:
        _SOURCE_LOCK_CACHE = source.build_source_lock()
    return _SOURCE_LOCK_CACHE


def confirmation_rows(lock: Mapping) -> list[dict]:
    """Return detached dictionaries in exact confirmation role-row order."""
    return [dict(row) for row in lock["role_rows"] if row["role"] == "confirmation"]


def confirmation_arrays_for_frame(lock: Mapping, row: Mapping) -> Tuple[np.ndarray, np.ndarray]:
    """Load arrays for an exact confirmation row.

    Role enforcement (development/changed/unknown/wrong role) happens
    before any array load.  Out-of-range source slices also raise
    ``ValueError`` before loading.
    """
    # --- role enforcement before load ---
    matches = [x for x in lock["role_rows"]
               if x["role"] == "confirmation" and dict(x) == dict(row)]
    if len(matches) != 1:
        raise ValueError("confirmation locked-row membership")

    # out-of-range source slice check (before load)
    start = int(row["source_pair_start"])
    end = int(row["source_pair_end"])
    if end - start != N or start < 0:
        raise ValueError("confirmation source slice range")

    # --- array load (same source adapter as development) ---
    frame = {"stratum": row["stratum"], "frame_id": int(row["frame_id"])}
    src = _get_source_lock()
    a, b = source.arrays_for_frame(src, frame)

    # shape/range guard
    if (a.shape != (N,) or b.shape != (N,)
            or np.any(a < 0) or np.any(a >= Q)
            or np.any(b < 0) or np.any(b >= Q)):
        raise ValueError("confirmation arrays")

    return a.copy(), b.copy()
