"""Focused V29 I01--I04/T0 tests using synthetic temporary parquet files only."""
from __future__ import annotations

import json
import shutil
import tempfile
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v29 as v29


@pytest.fixture()
def synthetic_inputs():
    # Use a fresh additive workspace root; several historical scratch roots
    # are ACL-locked on Windows.
    root = Path("workspace") / f"nbldpc_v29_t0_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    paths = {}
    try:
        for label in v29.SOURCE_ORDER:
            start, end = v29.SOURCE_FRAMES[label]
            frame_ids = np.repeat(np.arange(start, end + 1, dtype=np.int64), v29.FRAME_PAIRS)
            pair_idx = np.tile(np.arange(v29.FRAME_PAIRS, dtype=np.int64), end - start + 1)
            alice = (frame_ids * v29.FRAME_PAIRS + pair_idx) % 1024
            bob = (alice + 1) % 1024
            path = root / f"{label}.parquet"
            pd.DataFrame({"frame_id": frame_ids, "pair_idx": pair_idx,
                          "alice_symbol": alice, "bob_symbol": bob}).to_parquet(path, index=False)
            paths[label] = path
        yield paths
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_frozen_config_and_leakage_accounting():
    cfg = v29.frozen_v29_config()
    assert cfg["factorization"] == "F03_natural_MSB_to_LSB_GF32_plus_GF32"
    assert [cfg["sources"][label]["leak_bits"] for label in v29.SOURCE_ORDER] == [1064, 1094, 1104]
    assert [v29.leakage_bits(cfg["sources"][label]["m_total"]) for label in v29.SOURCE_ORDER] == [1064, 1094, 1104]
    assert all(cfg["sources"][label]["f"] < 1.3 for label in v29.SOURCE_ORDER)
    assert cfg["sources"]["1M"]["frame_start"] == 1600
    assert cfg["sources"]["1M"]["frame_end"] == 1999
    assert cfg["sources"]["1p5M"]["frame_start"] == 2213
    assert cfg["sources"]["2M"]["frame_end"] == 3315


def test_three_source_selection_order_and_100_blocks(synthetic_inputs):
    selected = v29.select_frames(synthetic_inputs)
    assert list(selected) == list(v29.SOURCE_ORDER)
    for label, table in selected.items():
        start, end = v29.SOURCE_FRAMES[label]
        assert len(table) == (end - start + 1) * v29.FRAME_PAIRS
        assert table["frame_id"].tolist()[:v29.FRAME_PAIRS] == [start] * v29.FRAME_PAIRS
        assert table["pair_idx"].tolist()[:v29.FRAME_PAIRS] == list(range(v29.FRAME_PAIRS))
        assert table["pair_idx"].tolist()[-v29.FRAME_PAIRS:] == list(range(v29.FRAME_PAIRS))

    blocks = v29.load_blocks(synthetic_inputs)
    assert len(blocks) == 300
    assert [b["source"] for b in blocks[:100]] == ["1M"] * 100
    assert [b["source"] for b in blocks[100:200]] == ["1p5M"] * 100
    assert [b["source"] for b in blocks[200:]] == ["2M"] * 100
    assert blocks[0]["frame_ids"] == [1600, 1601, 1602, 1603]
    assert blocks[99]["frame_ids"] == [1996, 1997, 1998, 1999]
    assert blocks[100]["frame_ids"] == [2213, 2214, 2215, 2216]
    assert blocks[-1]["frame_ids"] == [3312, 3313, 3314, 3315]
    assert all(len(block["alice_symbols"]) == v29.N and len(block["bob_symbols"]) == v29.N
               for block in blocks)
    assert all(block["pair_idx_ranges"] == [[0, 255]] * 4 for block in blocks)


def test_selector_ignores_legal_frames_outside_frozen_range(synthetic_inputs):
    for label, path in synthetic_inputs.items():
        start, end = v29.SOURCE_FRAMES[label]
        extra_frames = [start - 2, start - 1, end + 1, end + 2]
        extras = []
        for frame_id in extra_frames:
            pair_idx = np.arange(v29.FRAME_PAIRS, dtype=np.int64)
            alice = (frame_id * v29.FRAME_PAIRS + pair_idx) % 1024
            extras.append(pd.DataFrame({
                "frame_id": frame_id, "pair_idx": pair_idx,
                "alice_symbol": alice, "bob_symbol": (alice + 1) % 1024,
            }))
        table = pd.concat([pd.read_parquet(path), *extras], ignore_index=True)
        table.to_parquet(path, index=False)

    selected = v29.select_frames(synthetic_inputs)
    for label, table in selected.items():
        start, end = v29.SOURCE_FRAMES[label]
        assert table["frame_id"].min() == start
        assert table["frame_id"].max() == end
        assert sorted(table["frame_id"].unique().tolist()) == list(range(start, end + 1))
        assert len(table) == (end - start + 1) * v29.FRAME_PAIRS


def test_missing_pair_index_is_rejected(synthetic_inputs):
    path = synthetic_inputs["1M"]
    table = pd.read_parquet(path)
    bad = table[~((table["frame_id"] == 1600) & (table["pair_idx"] == 255))]
    bad.to_parquet(path, index=False)
    with pytest.raises(ValueError, match="pair_idx"):
        v29.select_frames(synthetic_inputs)


def test_missing_frame_is_rejected(synthetic_inputs):
    path = synthetic_inputs["2M"]
    table = pd.read_parquet(path)
    bad = table[table["frame_id"] != 3315]
    bad.to_parquet(path, index=False)
    with pytest.raises(ValueError, match="frame range"):
        v29.select_frames(synthetic_inputs)


def _synthetic_blocks(nonzero: bool = False):
    blocks = []
    index = 0
    for source in v29.SOURCE_ORDER:
        info = v29.frozen_v29_config()["sources"][source]
        for block_index in range(100):
            value = (index + 1) % 1024 if nonzero else 0
            symbols = np.full(v29.N, value, dtype=np.int64)
            first = info["frame_start"] + 4 * block_index
            blocks.append({
                "source": source, "source_id": info["source_id"],
                "delay_used_ps": info["delay_used_ps"], "source_path": "<in-memory>",
                "block_index": block_index, "global_block_index": index,
                "frame_ids": [first, first + 1, first + 2, first + 3],
                "pair_idx_ranges": [[0, 255]] * 4,
                "alice_symbols": symbols.copy(), "bob_symbols": symbols.copy(),
            })
            index += 1
    return blocks


class _SpyAdapter:
    def __init__(self):
        self.calls = []

    def posterior_rows(self, layer, bob, x1_hat=None):
        self.calls.append((layer, None if x1_hat is None else list(x1_hat)))
        return None


def _run_root(name):
    root = Path("workspace") / f"nbldpc_v29_{name}_{uuid.uuid4().hex}"
    assert not root.exists()
    return root


def _exact_fake(block, public, adapter, matrices, config):
    assert not {"alice_symbols", "truth1", "truth2", "alice_truth", "tag_true"}.intersection(block)
    assert "tag_true" not in public
    assert "alice_symbols" not in public
    assert set(public) == {"bob_symbols", "s1", "s2"}
    bob_x1, bob_x2 = v29.factor_layers(public["bob_symbols"])
    if adapter is not None:
        adapter.posterior_rows("L1", public["bob_symbols"])
        adapter.posterior_rows("L2", public["bob_symbols"], bob_x1)
    return {
        "L1": {"status": "success", "iterations": 1, "x_hat": bob_x1.tolist(),
                "reconstruction_ok": True},
        "L2": {"status": "success", "iterations": 1, "x_hat": bob_x2.tolist(),
                "reconstruction_ok": True},
        "runtime_s": 0.0, "decoder_calls": 2,
    }


def test_fake_pass_300_and_bob_only_order(monkeypatch):
    monkeypatch.setattr(v29.v28, "compute_syndrome", lambda field, matrix, symbols: [0] * len(matrix))
    blocks = _synthetic_blocks()
    adapters = {source: _SpyAdapter() for source in v29.SOURCE_ORDER}
    root = _run_root("pass")
    try:
        result = v29.run_v29(root, decoder_fn=_exact_fake, adapters=adapters, blocks=blocks)
        assert result["status"] == v29.TERMINAL_PASS
        assert result["gate"]["completed_block_count"] == 300
        assert set(p.name for p in root.iterdir()) == set(v29.PRE_VERIFY_FILES)
        observed = [call[0] for adapter in adapters.values() for call in adapter.calls]
        assert observed == ["L1", "L2"] * 300
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_fake_94_per_source_is_scientific_fail(monkeypatch):
    monkeypatch.setattr(v29.v28, "compute_syndrome", lambda field, matrix, symbols: [0] * len(matrix))
    blocks = _synthetic_blocks(nonzero=True)

    def fake(block, public, adapter, matrices, config):
        exact = int(block["block_index"]) < 94
        bob_x1, bob_x2 = v29.factor_layers(public["bob_symbols"])
        x1 = bob_x1.tolist() if exact else [0] * v29.N
        x2 = bob_x2.tolist() if exact else [0] * v29.N
        return {"L1": {"status": "success", "x_hat": x1, "reconstruction_ok": True},
                "L2": {"status": "success", "x_hat": x2, "reconstruction_ok": True},
                "runtime_s": 0.0, "decoder_calls": 2}

    root = _run_root("94fail")
    try:
        result = v29.run_v29(root, decoder_fn=fake, blocks=blocks)
        assert result["status"] == v29.TERMINAL_FAIL
        assert result["gate"]["completed_block_count"] == 100
        assert result["source_summary"]["sources"]["1M"]["offline_exact_count"] == 94
        assert result["source_summary"]["sources"]["1p5M"]["completed_block_count"] == 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_false_accept_is_scientific_fail(monkeypatch):
    monkeypatch.setattr(v29.v28, "compute_syndrome", lambda field, matrix, symbols: [0] * len(matrix))
    monkeypatch.setattr(v29, "tag64", lambda x1, x2: "00" * 8)
    blocks = _synthetic_blocks(nonzero=True)

    def wrong(block, public, adapter, matrices, config):
        return {"L1": {"status": "success", "x_hat": [0] * v29.N, "reconstruction_ok": True},
                "L2": {"status": "success", "x_hat": [0] * v29.N, "reconstruction_ok": True},
                "runtime_s": 0.0, "decoder_calls": 2}

    root = _run_root("falseaccept")
    try:
        result = v29.run_v29(root, decoder_fn=wrong, blocks=blocks)
        assert result["status"] == v29.TERMINAL_FAIL
        assert result["gate"]["completed_block_count"] == 1
        assert result["source_summary"]["global"]["false_accept_count"] == 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_l1_failure_skips_l2_and_resource_prefix_never_starts_301(monkeypatch):
    monkeypatch.setattr(v29.v28, "compute_syndrome", lambda field, matrix, symbols: [0] * len(matrix))
    blocks = _synthetic_blocks()
    calls = []

    def l1_fail(block, public, adapter, matrices, config):
        calls.append(block["global_block_index"])
        return {"L1": {"status": "decode_failed", "iterations": 200, "x_hat": None,
                        "reconstruction_ok": False},
                "L2": {"status": "not_run", "x_hat": None, "reconstruction_ok": False},
                "runtime_s": 1.0, "decoder_calls": 1}

    root = _run_root("resource")
    try:
        result = v29.run_v29(root, config={"resource_limit_seconds": 0.5},
                             decoder_fn=l1_fail, blocks=blocks)
        assert result["status"] == v29.TERMINAL_RESOURCE
        assert result["gate"]["completed_block_count"] == 1
        assert calls == [0]
        row = (root / "per_block_results.jsonl").read_text(encoding="utf-8").strip()
        assert '"l2_status": "not_run"' in row
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_irreversible_threshold_fail_stops_before_next_block(monkeypatch):
    monkeypatch.setattr(v29.v28, "compute_syndrome", lambda field, matrix, symbols: [0] * len(matrix))
    blocks = _synthetic_blocks()
    calls = []

    def l1_fail(block, public, adapter, matrices, config):
        calls.append(block["global_block_index"])
        return {"L1": {"status": "decode_failed", "iterations": 20, "x_hat": None,
                        "reconstruction_ok": False},
                "L2": {"status": "not_run", "x_hat": None, "reconstruction_ok": False},
                "runtime_s": 0.0, "decoder_calls": 1}

    root = _run_root("earlyfail")
    try:
        result = v29.run_v29(root, decoder_fn=l1_fail, blocks=blocks)
        assert result["status"] == v29.TERMINAL_FAIL
        assert result["gate"]["completed_block_count"] == 6
        assert calls == list(range(6))
        proof = result["gate"]["early_fail_proof"]
        assert proof["source"] == "1M"
        assert proof["completed_source_blocks"] == 6
        assert proof["remaining_expected"] == 94
        assert proof["max_possible_offline_exact"] == 94
        assert result["gate"]["user_authorized_stop"] is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _bob_minus_one_fake(block, public, adapter, matrices, config):
    """Bob-only fake that reverses the fixture's deterministic +1 offset."""
    if adapter is not None:
        adapter.posterior_rows("L1", public["bob_symbols"])
    alice = (np.asarray(public["bob_symbols"], dtype=np.int64) - 1) % 1024
    x1, x2 = v29.factor_layers(alice)
    if adapter is not None:
        adapter.posterior_rows("L2", public["bob_symbols"], x1)
    return {
        "L1": {"status": "success", "iterations": 1, "x_hat": x1.tolist(),
                "reconstruction_ok": True},
        "L2": {"status": "success", "iterations": 1, "x_hat": x2.tolist(),
                "reconstruction_ok": True},
        "runtime_s": 0.0, "decoder_calls": 2,
    }


def _clean_parquet_run(monkeypatch, synthetic_inputs):
    monkeypatch.setattr(v29.v28, "compute_syndrome", lambda field, matrix, symbols: [0] * len(matrix))
    blocks = v29.load_blocks(synthetic_inputs)
    adapters = {source: _SpyAdapter() for source in v29.SOURCE_ORDER}
    root = _run_root("verify")
    result = v29.run_v29(root, input_paths=synthetic_inputs, decoder_fn=_bob_minus_one_fake,
                         adapters=adapters, blocks=blocks)
    assert result["status"] == v29.TERMINAL_PASS
    return root


def test_oracle_sealed_and_readonly_verifier_clean(monkeypatch, synthetic_inputs):
    root = _clean_parquet_run(monkeypatch, synthetic_inputs)
    try:
        verified = v29.verify_v29(root, input_paths=synthetic_inputs)
        assert verified["ok"] is True, verified
        assert verified["recomputed_terminal"] == v29.TERMINAL_PASS
        assert verified["decoder_rerun"] is False
        assert set(path.name for path in root.iterdir()) == set(v29.EVIDENCE_FILES)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_readonly_verifier_rejects_semantic_tamper_and_file_set(monkeypatch, synthetic_inputs):
    root = _clean_parquet_run(monkeypatch, synthetic_inputs)
    try:
        assert v29.verify_v29(root, input_paths=synthetic_inputs)["ok"]

        cases = [
            ("per_block_results.jsonl", lambda doc: doc[0]["x1_hat"].__setitem__(0, 1)),
            ("per_block_results.jsonl", lambda doc: doc[0].__setitem__("tag_true", "00" * 8)),
            ("frame_selection.json", lambda doc: doc["sources"]["1M"]["frame_ids"].__setitem__(0, 1601)),
            ("matrix_binding.json", lambda doc: doc.__setitem__("n", 999)),
            ("source_summary.json", lambda doc: doc["global"].__setitem__("offline_exact_count", 0)),
        ]
        for filename, mutate in cases:
            path = root / filename
            original = path.read_text(encoding="utf-8")
            if filename.endswith(".jsonl"):
                value = [json.loads(line) for line in original.splitlines() if line.strip()]
                mutate(value)
                path.write_text("\n".join(json.dumps(item, sort_keys=True) for item in value) + "\n", encoding="utf-8")
            else:
                value = json.loads(original)
                mutate(value)
                path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
            try:
                assert v29.verify_v29(root, input_paths=synthetic_inputs)["ok"] is False
            finally:
                path.write_text(original, encoding="utf-8")

        gate_path = root / "gate.json"
        gate_original = gate_path.read_text(encoding="utf-8")
        gate_path.unlink()
        try:
            assert v29.verify_v29(root, input_paths=synthetic_inputs)["ok"] is False
        finally:
            gate_path.write_text(gate_original, encoding="utf-8")

        extra = root / "unexpected.txt"
        extra.write_text("x", encoding="utf-8")
        try:
            assert v29.verify_v29(root, input_paths=synthetic_inputs)["ok"] is False
        finally:
            extra.unlink()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_binding_tamper_is_implementation_blocked(monkeypatch):
    blocks = _synthetic_blocks()
    calls = []

    def should_not_run(*args):
        calls.append(args)
        return _exact_fake(*args)

    root = _run_root("binding_block")
    try:
        result = v29.run_v29(root, config={"sources": {"1M": {"h_total": 999.0}}},
                             decoder_fn=should_not_run, blocks=blocks)
        assert result["status"] == v29.TERMINAL_IMPL
        assert calls == []
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_finalize_stopped_prefix_is_readonly_and_rejects_proof_tamper(monkeypatch, synthetic_inputs):
    monkeypatch.setattr(v29.v28, "compute_syndrome", lambda field, matrix, symbols: [0] * len(matrix))
    blocks = v29.load_blocks(synthetic_inputs)
    root = _run_root("finalize")

    def l1_fail(block, public, adapter, matrices, config):
        return {"L1": {"status": "decode_failed", "iterations": 20, "x_hat": None,
                        "reconstruction_ok": False},
                "L2": {"status": "not_run", "x_hat": None, "reconstruction_ok": False},
                "runtime_s": 0.0, "decoder_calls": 1}

    try:
        v29.run_v29(root, input_paths=synthetic_inputs, decoder_fn=l1_fail, blocks=blocks)
        for name in ("source_summary.json", "gate.json", "RUN_MANIFEST.json"):
            (root / name).unlink()

        result = v29.finalize_stopped_prefix(
            root, input_paths=synthetic_inputs,
            user_stop_reason="user-authorized irreversible threshold stop",
        )
        assert result["status"] == v29.TERMINAL_FAIL
        assert result["readonly_verify"]["ok"] is True
        assert result["source_summary"]["fer_scope"] == "observed_prefix_only"
        proof_path = root / "gate.json"
        original = proof_path.read_text(encoding="utf-8")
        gate = json.loads(original)
        gate["early_fail_proof"]["max_possible_offline_exact"] = 99
        proof_path.write_text(json.dumps(gate, indent=2, sort_keys=True), encoding="utf-8")
        try:
            tampered = v29.verify_v29(root)
            assert tampered["ok"] is False
        finally:
            proof_path.write_text(original, encoding="utf-8")
        assert v29.verify_v29(root)["ok"] is True
    finally:
        shutil.rmtree(root, ignore_errors=True)
