"""Tests for ldpc_v5_confirmation_arrays (Phase 4 confirmation array access)."""
from __future__ import annotations
import sys
import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Fake lock / fake source adapter
# ---------------------------------------------------------------------------

N = 256
Q = 1024

# Fake arrays: deterministic per (stratum, frame_id)
_FAKE_A = np.arange(N, dtype=np.int64) % Q          # 0..255
_FAKE_B = (np.arange(N, dtype=np.int64) + 128) % Q  # 128..383 mod 1024


def _fake_arrays_for_frame(lock, frame):
    """Return deterministic fake arrays for any stratum/frame_id."""
    return _FAKE_A.copy(), _FAKE_B.copy()


def _make_row(role, stratum, frame_id, rank, source_start=0, source_end=N):
    return {
        "role": role,
        "stratum": stratum,
        "frame_id": frame_id,
        "partition_rank": rank,
        "role_rank": rank if role == "confirmation" else rank - 128,
        "frame_identity": f"fid_{role}_{stratum}_{frame_id}",
        "payload_identity": f"pid_{role}_{stratum}_{frame_id}",
        "ranking_sha256": f"sha_{role}_{stratum}_{frame_id}",
        "source_record_sha256": f"src_{stratum}",
        "source_pair_start": source_start,
        "source_pair_end": source_end,
    }


def _make_lock():
    rows = []
    for st in ("d1024_bw120", "d1024_bw180", "d1024_bw200"):
        # 128 confirmation rows per stratum (ranks 0..127)
        for i in range(128):
            rows.append(_make_row("confirmation", st, i, i,
                                  source_start=i * N, source_end=(i + 1) * N))
        # 512 development rows per stratum (ranks 128..639)
        for i in range(512):
            rows.append(_make_row("development", st, i + 128, 128 + i,
                                  source_start=(128 + i) * N,
                                  source_end=(129 + i) * N))
    return {
        "role_rows": rows,
        "access_contract": {
            "confirmation_api": "ldpc_v5_confirmation_arrays",
            "confirmation_decoding_authorized": False,
            "development_api": "development_arrays_for_frame_v1",
            "role_enforcement": "exact_locked_row_membership_before_array_load",
        },
        "partition_policy": {
            "confirmation_partition_ranks": [0, 127],
            "development_partition_ranks": [128, 639],
            "dimension": Q,
            "frame_len_symbols": N,
            "mapping": "gray",
        },
    }


# ---------------------------------------------------------------------------
# Monkeypatch: replace build_source_lock so tests never touch real data
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_source(monkeypatch):
    """Patch source.build_source_lock to return a fake lock."""
    import comparison_bench.src.comparison_bench.formal_ir.ldpc_v4_10db_source as src_mod
    import comparison_bench.src.comparison_bench.formal_ir.ldpc_v5_confirmation_arrays as conf_mod

    # Reset cache
    conf_mod._SOURCE_LOCK_CACHE = None

    monkeypatch.setattr(src_mod, "build_source_lock", lambda: {"fake": True})
    monkeypatch.setattr(src_mod, "arrays_for_frame", _fake_arrays_for_frame)
    yield
    conf_mod._SOURCE_LOCK_CACHE = None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_confirmation_rows_order_and_detached():
    lock = _make_lock()
    rows = __import__(
        "comparison_bench.src.comparison_bench.formal_ir.ldpc_v5_confirmation_arrays",
        fromlist=["confirmation_rows"],
    ).confirmation_rows(lock)
    # 128 per stratum * 3 strata = 384
    assert len(rows) == 384
    # all are dicts, all have role "confirmation"
    for r in rows:
        assert isinstance(r, dict)
        assert r["role"] == "confirmation"
    # order matches lock confirmation rows
    expected = [x for x in lock["role_rows"] if x["role"] == "confirmation"]
    for got, exp in zip(rows, expected):
        assert got == exp
    # detached: modifying returned row does not affect lock
    rows[0]["mutated"] = True
    assert "mutated" not in lock["role_rows"][0]


def test_confirmation_arrays_normal_load():
    lock = _make_lock()
    mod = __import__(
        "comparison_bench.src.comparison_bench.formal_ir.ldpc_v5_confirmation_arrays",
        fromlist=["confirmation_rows", "confirmation_arrays_for_frame"],
    )
    rows = mod.confirmation_rows(lock)
    row = rows[0]
    a, b = mod.confirmation_arrays_for_frame(lock, row)
    assert a.shape == (N,)
    assert b.shape == (N,)
    assert np.issubdtype(a.dtype, np.integer)
    assert np.issubdtype(b.dtype, np.integer)
    assert np.all(a >= 0) and np.all(a < Q)
    assert np.all(b >= 0) and np.all(b < Q)
    # detached: modifying returned array does not affect lock
    a[0] = 999
    a2, b2 = mod.confirmation_arrays_for_frame(lock, row)
    assert a2[0] != 999


def test_development_row_raises_before_load():
    """Loader must reject development rows and never invoke the source adapter."""
    load_count = {"n": 0}
    original = _fake_arrays_for_frame

    def counting_fake(lock, frame):
        load_count["n"] += 1
        return original(lock, frame)

    import comparison_bench.src.comparison_bench.formal_ir.ldpc_v4_10db_source as src_mod
    src_mod.arrays_for_frame = counting_fake

    lock = _make_lock()
    mod = __import__(
        "comparison_bench.src.comparison_bench.formal_ir.ldpc_v5_confirmation_arrays",
        fromlist=["confirmation_arrays_for_frame"],
    )
    dev_rows = [x for x in lock["role_rows"] if x["role"] == "development"]
    with pytest.raises(ValueError, match="membership"):
        mod.confirmation_arrays_for_frame(lock, dev_rows[0])
    assert load_count["n"] == 0, "source adapter must not be called for wrong role"


def test_changed_row_raises_before_load():
    """A row with modified fields is not an exact locked row."""
    lock = _make_lock()
    mod = __import__(
        "comparison_bench.src.comparison_bench.formal_ir.ldpc_v5_confirmation_arrays",
        fromlist=["confirmation_rows", "confirmation_arrays_for_frame"],
    )
    rows = mod.confirmation_rows(lock)
    fake_row = dict(rows[0])
    fake_row["frame_id"] = 99999  # not in lock
    with pytest.raises(ValueError, match="membership"):
        mod.confirmation_arrays_for_frame(lock, fake_row)


def test_unknown_row_raises_before_load():
    lock = _make_lock()
    mod = __import__(
        "comparison_bench.src.comparison_bench.formal_ir.ldpc_v5_confirmation_arrays",
        fromlist=["confirmation_arrays_for_frame"],
    )
    unknown = _make_row("confirmation", "d1024_bw120", 0, 0,
                        source_start=0, source_end=N)
    unknown["frame_identity"] = "totally_unknown"
    with pytest.raises(ValueError, match="membership"):
        mod.confirmation_arrays_for_frame(lock, unknown)


def test_wrong_role_raises_before_load():
    lock = _make_lock()
    mod = __import__(
        "comparison_bench.src.comparison_bench.formal_ir.ldpc_v5_confirmation_arrays",
        fromlist=["confirmation_arrays_for_frame"],
    )
    wrong_role = _make_row("something_else", "d1024_bw120", 0, 0,
                           source_start=0, source_end=N)
    with pytest.raises(ValueError, match="membership"):
        mod.confirmation_arrays_for_frame(lock, wrong_role)


def test_out_of_range_slice_raises():
    """Changing source fields breaks exact membership → caught before load."""
    lock = _make_lock()
    mod = __import__(
        "comparison_bench.src.comparison_bench.formal_ir.ldpc_v5_confirmation_arrays",
        fromlist=["confirmation_rows", "confirmation_arrays_for_frame"],
    )
    rows = mod.confirmation_rows(lock)
    bad_row = dict(rows[0])
    bad_row["source_pair_start"] = 0
    bad_row["source_pair_end"] = N + 1  # wrong size
    # Modifying source fields breaks exact membership check (role enforcement first)
    with pytest.raises(ValueError, match="membership"):
        mod.confirmation_arrays_for_frame(lock, bad_row)


def test_module_does_not_import_decoder():
    """Phase 4 confirmation loader must never import or call a decoder."""
    import comparison_bench.src.comparison_bench.formal_ir.ldpc_v5_confirmation_arrays as mod
    src = open(mod.__file__).read()
    # no import of ldpc_v5 (the decoder module)
    assert "from .ldpc_v5" not in src
    assert "import ldpc_v5" not in src
    # no call to run_ldpc_formal_v5
    assert "run_ldpc_formal_v5" not in src
