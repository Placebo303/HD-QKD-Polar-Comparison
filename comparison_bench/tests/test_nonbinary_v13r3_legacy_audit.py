"""V13 R3 legacy drift audit acceptance tests
(``formal-nonbinary-ldpc-v13-r3-legacy-drift-audit``).

All execution uses fake parquet sources and a stub decoder.  No production
decoder is imported and no production output root is entered.  Temp roots are
owned by ``workspace/`` (pytest's system temp root is inaccessible in this
environment).
"""
from __future__ import annotations

import ast
import json
import shutil
import uuid
from pathlib import Path

import pandas as pd
import pytest

from comparison_bench.src.comparison_bench.formal_ir import \
    nonbinary_v13r3_legacy_audit as core


# ---------------------------------------------------------------- helpers


def _temp_root(name: str) -> Path:
    root = Path("workspace") / f"nbldpc_v13r3_legacy_{name}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_fake_parquet(path: Path, n_frames: int = 70, *,
                        bad_symbol: bool = False,
                        incomplete: bool = False) -> Path:
    rows = []
    for frame_id in range(n_frames):
        for pair_idx in range(256):
            if incomplete and frame_id == n_frames - 1 and pair_idx == 255:
                continue
            alice = 1024 if (bad_symbol and frame_id == 0 and pair_idx == 0) else 0
            rows.append({"frame_id": frame_id, "pair_idx": pair_idx,
                         "alice_symbol": alice, "bob_symbol": 0})
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def _stub_decode(frame, manifest, matrix):
    decoded = tuple(int(v) for v in frame["alice"])
    result = {"status": "syndrome_consistent", "iterations": 1,
              "decoded_symbols": decoded, "reason": ""}
    return {"result": result, "telemetry": {"final_status": "syndrome_consistent"}}


def _three_sources(root: Path, frames: int = 70) -> list[Path]:
    return [_write_fake_parquet(root / f"type2_{i}/pairs.parquet", frames)
            for i in (1, 2, 3)]


# ---------------------------------------------------------------- T0


def _parse_ok(path: str) -> ast.Module:
    with open(path, encoding="utf-8") as fh:
        return ast.parse(fh.read(), filename=path)


def test_t0_sources_parse():
    for rel in ("comparison_bench/src/comparison_bench/formal_ir/nonbinary_v13r3_legacy_audit.py",
                "comparison_bench/src/comparison_bench/cli/run_v13r3_legacy_drift_audit.py",
                "comparison_bench/tests/test_nonbinary_v13r3_legacy_audit.py"):
        _parse_ok(rel)


def test_t0_constants():
    assert core.METHOD == "nbldpc_v13_r3_legacy_drift_audit"
    assert core.CLAIM_BOUNDARY == "legacy_drift_audit"
    assert core.DATA_INTAKE_STATE == "data_intake_rejected_for_fresh_confirmation"
    assert core.DRIFT_PRECHECK_STATE == "drift_exceeded"
    assert core.FRAMES_PER_SOURCE == 64
    assert (core.Q, core.N, core.M, core.P, core.MAX_ITER) == (1024, 256, 170, 0.20, 100)


# ---------------------------------------------------------------- T1


def test_validate_pairs_table_and_selection():
    root = _temp_root("validate")
    try:
        path = _write_fake_parquet(root / "type2_1/pairs.parquet", 70)
        source = core.validate_pairs_table(path)
        assert source["complete_frames"] == 70
        assert core.selected_frame_ids(source) == list(range(64))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_validate_pairs_rejects_bad_symbol():
    root = _temp_root("bad_symbol")
    try:
        path = _write_fake_parquet(root / "type2_1/pairs.parquet", 70, bad_symbol=True)
        with pytest.raises(ValueError):
            core.validate_pairs_table(path)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_validate_pairs_rejects_incomplete_frame():
    root = _temp_root("incomplete")
    try:
        path = _write_fake_parquet(root / "type2_1/pairs.parquet", 70, incomplete=True)
        with pytest.raises(ValueError):
            core.validate_pairs_table(path)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_insufficient_frames_stops():
    root = _temp_root("insufficient")
    try:
        path = _write_fake_parquet(root / "type2_1/pairs.parquet", 63)
        source = core.validate_pairs_table(path)
        with pytest.raises(ValueError):
            core.selected_frame_ids(source)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_production_authorization_required():
    root = _temp_root("auth")
    try:
        paths = _three_sources(root, 65)
        out = root / "prod_pkg"
        with pytest.raises(ValueError):
            core.run_audit(out, parquet_paths=paths, production_authorized=False,
                           decode_fn=_stub_decode)
        assert not out.exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ---------------------------------------------------------------- T2 fake lifecycle


def test_fake_lifecycle_and_verify():
    root = _temp_root("lifecycle")
    try:
        paths = _three_sources(root, 70)
        out = root / "audit_pkg"
        result = core.run_audit(out, parquet_paths=paths,
                                run_id="nbldpc_v13r3_legacy_drift_audit_test_v1",
                                _test_only=True, decode_fn=_stub_decode)
        assert result["attempted_frames"] == 192
        assert result["verdict"] == "legacy_drift_audit_completed"
        assert result["claim_boundary"] == "legacy_drift_audit"

        report = json.loads((out / "audit_report.json").read_text(encoding="utf-8"))
        assert report["fresh_confirmed"] is False
        assert report["promotion"] is False
        assert report["qualification"] is False
        assert report["exact_correct_frames"] == 192

        verify = core.verify_package(out)
        assert verify["ok"], verify["problems"]

        # Tampering must be detected read-only.
        data = (out / "audit_outcomes.csv").read_bytes()
        (out / "audit_outcomes.csv").write_bytes(data + b"\n")
        verify_bad = core.verify_package(out)
        assert verify_bad["ok"] is False
        (out / "audit_outcomes.csv").write_bytes(data)
        assert core.verify_package(out)["ok"]
    finally:
        shutil.rmtree(root, ignore_errors=True)
