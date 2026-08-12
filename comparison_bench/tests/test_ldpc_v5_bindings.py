"""Focused v5 binding and role-isolation tamper tests (no production runner)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import ldpc_v5_partition as partition
from comparison_bench.src.comparison_bench.formal_ir.ldpc_v5_predecessors import build_predecessor_binding, validate_predecessor_binding


ROOT=Path("comparison_bench/outputs_comparison/formal_ir_methods")


def _rehash(record, field):
    data=dict(record); data.pop(field)
    return {**data, field:hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")).hexdigest()}


def test_predecessor_binding_is_self_hashed_and_rebuilds_read_only():
    record=build_predecessor_binding(ROOT)
    validate_predecessor_binding(record, ROOT)
    changed=json.loads(json.dumps(record)); changed["packages"][0]["verified_result"]["status"]="not_verified"
    changed=_rehash(changed,"binding_sha256")
    with pytest.raises(ValueError):
        validate_predecessor_binding(changed,ROOT)


def _fast_predecessor(_):
    # P1-03 only: P1-01 real verifier path is exercised by the preceding test.
    return {"schema":"test_predecessor_binding","binding_sha256":"0" * 64}


def test_partition_confirmation_row_never_loads_arrays(monkeypatch):
    monkeypatch.setattr(partition,"build_predecessor_binding",_fast_predecessor)
    lock=partition.build_partition_lock()
    partition.validate_partition_lock(lock)
    confirmation=next(row for row in lock["role_rows"] if row["role"]=="confirmation")
    called=[]
    monkeypatch.setattr(partition.source,"arrays_for_frame",lambda *_: called.append(True))
    with pytest.raises(ValueError):
        partition.development_arrays_for_frame(lock,confirmation)
    assert called == []


def test_partition_changed_development_row_never_loads_arrays(monkeypatch):
    monkeypatch.setattr(partition,"build_predecessor_binding",_fast_predecessor)
    lock=partition.build_partition_lock()
    changed=partition.development_rows(lock)[0]
    changed["frame_id"] += 1
    called=[]
    monkeypatch.setattr(partition.source,"arrays_for_frame",lambda *_: called.append(True))
    with pytest.raises(ValueError):
        partition.development_arrays_for_frame(lock,changed)
    assert called == []
