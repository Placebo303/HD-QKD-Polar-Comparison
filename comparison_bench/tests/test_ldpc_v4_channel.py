import copy
import hashlib
import json

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import ldpc_v4_channel as channel


def _compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _lock(alice, bob):
    rows = []
    for frame_id in range(64):
        rows.append({"role": "calibration", "dataset_id": "d1024_bw100", "bin_width_ps": 100, "frame_id": frame_id,
                     "selection_rank": f"{frame_id:064x}", "frame_identity": hashlib.sha256(f"frame-{frame_id}".encode()).hexdigest(),
                     "source_pair_start": frame_id * 256, "source_pair_end": (frame_id + 1) * 256})
    manifest = {"manifest_sha256": "a" * 64, "main_ttbin": {"sha256": "b" * 64}, "chunk_ttbin": {"sha256": "c" * 64}}
    return {"selected_frames": rows, "source_manifest": manifest, "source_manifest_sha256": "a" * 64,
            "calibration": {"calibration_sha256": "d" * 64}, "lock_sha256": "e" * 64}, alice, bob


def _vectors():
    bob = np.arange(16384, dtype=np.int64) % 1024
    delta = np.zeros(16384, dtype=np.int64); delta[:3865] = 1; delta[3865:3981] = -1
    return (bob + delta) % 1024, bob


def _patched_lock(monkeypatch, alice=None, bob=None):
    alice, bob = _vectors() if alice is None else (alice, bob)
    lock, alice, bob = _lock(alice, bob)
    monkeypatch.setattr(channel._v3_data, "verify_locked_data", lambda value: None)
    calls = []
    def frames(value, role, dataset, frame_id):
        calls.append((role, dataset, frame_id))
        start = frame_id * 256
        return alice[start:start + 256].copy(), bob[start:start + 256].copy()
    monkeypatch.setattr(channel._v3_data, "frame_arrays", frames)
    return lock, calls


def test_exact_model_hash_and_confirmation_never_requested(monkeypatch):
    lock, calls = _patched_lock(monkeypatch)
    model = channel.build_adjacent_channel_model(lock)
    assert model["model_sha256"] == hashlib.sha256(_compact({k: v for k, v in model.items() if k != "model_sha256"})).hexdigest()
    assert (model["zero_count"], model["plus_one_count"], model["minus_one_count"], model["total_count"]) == (12403, 3865, 116, 16384)
    assert len(calls) == 64 and all(item[:2] == ("calibration", "d1024_bw100") for item in calls)
    channel.verify_adjacent_channel_model(model, lock)


def test_rejects_wrong_count_delta_and_gray_property(monkeypatch):
    alice, bob = _vectors(); alice[0] = bob[0]
    lock, _ = _patched_lock(monkeypatch, alice, bob)
    with pytest.raises(ValueError, match="counts"): channel.build_adjacent_channel_model(lock)
    alice, bob = _vectors(); alice[0] = (bob[0] + 2) % 1024
    lock, _ = _patched_lock(monkeypatch, alice, bob)
    with pytest.raises(ValueError, match="delta support"): channel.build_adjacent_channel_model(lock)
    lock, _ = _patched_lock(monkeypatch)
    monkeypatch.setattr(channel, "symbols_to_bits", lambda values, *_: np.zeros((len(values), 10), dtype=np.uint8))
    with pytest.raises(ValueError, match="Gray hamming"): channel.build_adjacent_channel_model(lock)


def test_probability_formula_and_clipping(monkeypatch):
    lock, _ = _patched_lock(monkeypatch); model = channel.build_adjacent_channel_model(lock)
    bob = np.asarray([0, 1, 2, 3] + [0] * 252, dtype=np.int64)
    raw = channel.plane_error_channel(bob, 9, "adjacent_nominal", model, clip_for_backend=False)
    p_plus = 3865 / 16384; p_minus = 116 / 16384
    gray = channel.gray_encode(bob[:4]); plus = channel.gray_encode((bob[:4] + 1) % 1024); minus = channel.gray_encode((bob[:4] - 1) % 1024)
    expected = p_plus * ((plus & 1) != (gray & 1)) + p_minus * ((minus & 1) != (gray & 1))
    assert raw[:4].tolist() == pytest.approx(expected.tolist())
    clipped = channel.plane_error_channel(bob, 0, "adjacent_nominal", model)
    assert clipped.dtype == np.float64 and np.min(clipped) == 1e-6 and np.max(clipped) < .49
    altered = copy.deepcopy(model); altered["probabilities"]["adjacent_nominal"]["plus_one"] = 1.0; altered["model_sha256"] = hashlib.sha256(_compact({k: v for k, v in altered.items() if k != "model_sha256"})).hexdigest()
    with pytest.raises(ValueError, match="probabilities"): channel.plane_error_channel(bob, 9, "adjacent_nominal", altered)
    with pytest.raises(ValueError): channel.plane_error_channel(bob[:-1], 0, "adjacent_nominal", model)
