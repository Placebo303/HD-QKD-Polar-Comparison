import json
import os
import uuid
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir.ldpc_v3_ttbin_data import (build_locked_data, build_source_manifest,
                                                                                  frame_arrays, verify_locked_data,
                                                                                  verify_source_manifest)


def _root():
    value = os.environ.get("FORMAL_IR_TEST_TMP")
    if not value:
        raise RuntimeError("FORMAL_IR_TEST_TMP is required for this test module")
    root = Path(value) / f"phase6a-{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def _fixture():
    tmp_path = _root()
    main = tmp_path / "20dB_capture.ttbin"; chunk = tmp_path / "20dB_capture.1.ttbin"
    main.write_bytes(b"main"); chunk.write_bytes(b"chunk")
    dirs = {}
    for name, bw, frames in (("d1024_bw100", 100, 64), ("d1024_bw120", 120, 32), ("d1024_bw180", 180, 32), ("d1024_bw200", 200, 32)):
        d = tmp_path / name / "blk0"; d.mkdir(parents=True); dirs[name] = d
        a = np.arange(frames * 256, dtype=np.int64) % 1024
        np.save(d / "a_eff.npy", a); np.save(d / "b_eff.npy", (a + (np.arange(a.size) % 13 == 0)) % 1024)
        (d / "sidecar_meta.json").write_text(json.dumps({"point": {"d": 1024, "bw": bw}, "joint_source_mode": "from_ttbin", "joint_origin": "from_ttbin", "materialize_origin": "materialized_from_ttbin", "sequence_source_mode": "strict", "sequence_is_sampled": 0, "materialize_params": {"used_params": {"dimension": 1024, "bin_width_ps": bw, "source_ttbin_paths": str(main), "pairing_mode": "nearest"}}}), encoding="utf-8")
    return main, chunk, dirs


def test_build_lock_reconstructs_calibration_without_confirmation_dependency():
    main, chunk, dirs = _fixture()
    manifest = build_source_manifest(main, chunk, dirs); verify_source_manifest(manifest)
    lock = build_locked_data(manifest); verify_locked_data(lock)
    assert len(lock["selected_frames"]) == 160
    assert [p["total_bits"] for p in lock["calibration"]["planes"]] == [16384] * 10
    row = next(r for r in lock["selected_frames"] if r["role"] == "confirmation")
    a, b = frame_arrays(lock, row["role"], row["dataset_id"], row["frame_id"])
    assert a.shape == b.shape == (256,)
    calibration = lock["calibration"]
    np.save(dirs["d1024_bw120"] / "b_eff.npy", np.zeros(32 * 256, dtype=np.int64))
    changed_confirmation = build_locked_data(build_source_manifest(main, chunk, dirs))
    assert changed_confirmation["calibration"] == calibration


def test_rejects_source_and_lock_tampering():
    main, chunk, dirs = _fixture()
    manifest = build_source_manifest(main, chunk, dirs)
    main.write_bytes(b"changed")
    with pytest.raises(ValueError): verify_source_manifest(manifest)
    main.write_bytes(b"main")
    manifest = build_source_manifest(main, chunk, dirs)
    meta = dirs["d1024_bw100"] / "sidecar_meta.json"
    value = json.loads(meta.read_text(encoding="utf-8")); value["sequence_source_mode"] = "altered"
    meta.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError): verify_source_manifest(manifest)
    value["sequence_source_mode"] = "strict"; meta.write_text(json.dumps(value), encoding="utf-8")
    lock = build_locked_data(manifest); lock["selected_frames"][0]["frame_id"] = 99
    with pytest.raises(ValueError): verify_locked_data(lock)


def test_rejects_non_strict_sidecar_and_tail_requirement():
    main, chunk, dirs = _fixture()
    meta = dirs["d1024_bw100"] / "sidecar_meta.json"
    value = json.loads(meta.read_text(encoding="utf-8")); value["sequence_is_sampled"] = 1
    meta.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError): build_source_manifest(main, chunk, dirs)


def test_rejects_chunk_source_metadata_and_array_violations():
    main, chunk, dirs = _fixture()
    (main.parent / "20dB_capture.2.ttbin").write_bytes(b"extra")
    with pytest.raises(ValueError): build_source_manifest(main, chunk, dirs)
    (main.parent / "20dB_capture.2.ttbin").unlink()
    meta = dirs["d1024_bw120"] / "sidecar_meta.json"
    value = json.loads(meta.read_text(encoding="utf-8")); value["materialize_params"]["used_params"]["source_ttbin_paths"] = str(main.parent / "other.ttbin")
    meta.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError): build_source_manifest(main, chunk, dirs)
    value["materialize_params"]["used_params"]["source_ttbin_paths"] = str(main); meta.write_text(json.dumps(value), encoding="utf-8")
    np.save(dirs["d1024_bw120"] / "a_eff.npy", np.linspace(0, 1, 32 * 256))
    with pytest.raises(ValueError): build_source_manifest(main, chunk, dirs)
    np.save(dirs["d1024_bw120"] / "a_eff.npy", np.full(32 * 256, 1024, dtype=np.int64))
    with pytest.raises(ValueError): build_source_manifest(main, chunk, dirs)
