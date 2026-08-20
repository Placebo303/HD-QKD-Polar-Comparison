"""V29 frozen retrospective finite-code gate.

The implementation keeps the scientific boundary explicit: only the three
registered parquet sources are selected, the decoder receives Bob/public
inputs only, and the read-only verifier reconstructs truth from parquet
without rerunning a decoder.
"""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
import math
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from ..io.pairs_loader import load_pairs_table, normalize_pair_columns
from . import nonbinary_v28 as v28
from . import nonbinary_v10_fftqspa as qspa
from .nonbinary_field import GF2mField

Q = 32
N = 1024
FRAME_PAIRS = 256
BLOCK_FRAMES = 4
BLOCKS_PER_SOURCE = 100
TAG_BITS = 64
MAX_ITER = 200
STREAK = 20
RESOURCE_LIMIT_SECONDS = 24.0 * 60.0 * 60.0
SOURCE_ORDER = ("1M", "1p5M", "2M")
TERMINAL_PASS = "retrospective_ready_for_fresh_change"
TERMINAL_FAIL = "v29_finite_gate_fail"
TERMINAL_IMPL = "implementation_blocked"
TERMINAL_RESOURCE = "resource_blocked"
EVIDENCE_FILES = (
    "RUN_MANIFEST.json", "frame_selection.json", "block_manifest.json",
    "channel_model_binding.json", "matrix_binding.json",
    "per_block_results.jsonl", "source_summary.json", "gate.json",
    "readonly_verify.json",
)
PRE_VERIFY_FILES = EVIDENCE_FILES[:-1]
SOURCE_IDS = dict(v28.SOURCE_IDS)
SOURCE_DELAY_PS = dict(v28.SOURCE_DELAY_PS)
SOURCE_N_PAIRS = dict(v28.SOURCE_N_PAIRS)
SOURCE_M2 = dict(v28.SOURCE_M2)
SOURCE_H_TOTAL = {"1M": 0.801037825, "1p5M": 0.825566052, "2M": 0.832562722}
SOURCE_FRAMES = {"1M": (1600, 1999), "1p5M": (2213, 2612), "2M": (2916, 3315)}
SOURCE_PARQUETS = {
    label: "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
    "v13r3fresh_pairs_20260816/" + source_id + "/pairs.parquet"
    for label, source_id in SOURCE_IDS.items()
}

__all__ = [
    "Q", "N", "FRAME_PAIRS", "BLOCK_FRAMES", "BLOCKS_PER_SOURCE",
    "SOURCE_ORDER", "SOURCE_FRAMES", "SOURCE_H_TOTAL", "frozen_v29_config",
    "select_frames", "load_blocks", "leakage_bits", "tag64", "run_v29",
    "verify_v29", "finalize_stopped_prefix",
]


def _frozen_source(label: str) -> dict[str, Any]:
    start, end = SOURCE_FRAMES[label]
    m2 = SOURCE_M2[label]
    leak = (v28.M1 + m2) * 5 + TAG_BITS
    h_total = SOURCE_H_TOTAL[label]
    return {
        "source_id": SOURCE_IDS[label], "delay_used_ps": SOURCE_DELAY_PS[label],
        "n_pairs": SOURCE_N_PAIRS[label], "pairs_parquet": SOURCE_PARQUETS[label],
        "frame_start": start, "frame_end": end, "frame_count": end - start + 1,
        "pair_count_per_frame": FRAME_PAIRS, "block_count": BLOCKS_PER_SOURCE,
        "m1": v28.M1, "m2": m2, "m_total": v28.M1 + m2, "leak_bits": leak,
        "h_total": h_total, "f": leak / (N * h_total),
    }


def frozen_v29_config() -> dict[str, Any]:
    """Return the V29 I01 frozen configuration.

    H values are current V28R frozen constants and are not re-estimated by the
    selector or the later execution gate.
    """
    return {
        "schema": "nbldpc_v29_frozen_config_v1", "q": Q, "n": N,
        "factorization": "F03_natural_MSB_to_LSB_GF32_plus_GF32",
        "frame_pairs": FRAME_PAIRS, "block_frames": BLOCK_FRAMES,
        "max_iter": MAX_ITER, "streak": STREAK,
        "resource_limit_seconds": RESOURCE_LIMIT_SECONDS,
        "source_order": list(SOURCE_ORDER),
        "sources": {label: _frozen_source(label) for label in SOURCE_ORDER},
        "tag_bits": TAG_BITS, "tag_method": "sha256(bytes(x1)||bytes(x2))[:8]",
        "h_total_binding": "V28R_frozen_config_no_execution_reestimation",
        "scientific_input_policy": "only_three_registered_V25_pairs_parquet_files",
        "gate": {"min_tag_verified_per_source": 95,
                 "min_offline_exact_per_source": 95,
                 "false_accept_count": 0, "all_blocks_required": True},
        "terminal_precedence": "implementation;complete_300_before_resource;resource;scientific_pass_fail",
        "evidence_files": list(EVIDENCE_FILES),
    }


def _config(config: Mapping[str, Any] | None) -> dict[str, Any]:
    base = frozen_v29_config()
    if config is None:
        return base
    out = copy.deepcopy(base)
    for key, value in config.items():
        if key == "sources" and isinstance(value, Mapping):
            for label, info in value.items():
                if label not in out["sources"]:
                    raise ValueError(f"unknown V29 source: {label}")
                out["sources"][label].update(copy.deepcopy(info))
        elif key == "gate" and isinstance(value, Mapping):
            out["gate"].update(copy.deepcopy(value))
        else:
            out[key] = copy.deepcopy(value)
    out["source_order"] = list(config.get("source_order", out["source_order"]))
    for label, override in (config.get("sources", {}) or {}).items():
        if "frame_start" in override or "frame_end" in override:
            start = int(out["sources"][label]["frame_start"])
            end = int(out["sources"][label]["frame_end"])
            out["sources"][label]["frame_count"] = end - start + 1
            out["sources"][label].setdefault("block_count", (end - start + 1) // BLOCK_FRAMES)
    return out


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _inventory_paths() -> dict[str, str]:
    path = _repo_root() / "workspace" / "nbldpc_v25_p0" / "data_inventory.json"
    if not path.exists():
        return dict(SOURCE_PARQUETS)
    doc = json.loads(path.read_text(encoding="utf-8"))
    found: dict[str, str] = {}
    for item in doc.get("primary_joint_data_sources", []):
        for label in SOURCE_ORDER:
            if item.get("source_id") == SOURCE_IDS[label]:
                found[label] = str(item["pairs_parquet"])
    return {label: found.get(label, SOURCE_PARQUETS[label]) for label in SOURCE_ORDER}


def _resolve_input_paths(input_paths: Any, config: Mapping[str, Any],
                         input_root: str | Path | None = None) -> dict[str, Path]:
    if input_paths is None:
        raw = _inventory_paths()
    elif isinstance(input_paths, Mapping):
        raw = dict(input_paths)
    elif isinstance(input_paths, (str, Path)):
        candidate = Path(input_paths)
        if candidate.suffix.lower() == ".json":
            doc = json.loads(candidate.read_text(encoding="utf-8"))
            raw = {}
            for label in config["source_order"]:
                item = next((x for x in doc.get("primary_joint_data_sources", [])
                             if x.get("source_id") == config["sources"][label]["source_id"]), None)
                if item is None:
                    raise ValueError(f"inventory has no source {label}")
                raw[label] = item["pairs_parquet"]
            input_root = candidate.parent
        elif candidate.is_file():
            raise ValueError("V29 requires one parquet path per source")
        else:
            raw = {}
            for label in config["source_order"]:
                info = config["sources"][label]
                choices = [candidate / label / "pairs.parquet",
                           candidate / str(info["source_id"]) / "pairs.parquet"]
                raw[label] = next((p for p in choices if p.exists()), choices[0])
    else:
        values = list(input_paths)
        if len(values) != len(config["source_order"]):
            raise ValueError("input_paths must contain one parquet path per source")
        raw = dict(zip(config["source_order"], values))
    root = Path(input_root) if input_root is not None else _repo_root()
    paths: dict[str, Path] = {}
    for label in config["source_order"]:
        if label not in raw:
            raise ValueError(f"missing input path for source {label}")
        path = Path(raw[label])
        if not path.is_absolute():
            path = root / path
        if path.suffix.lower() not in {".parquet", ".pq"}:
            raise ValueError(f"V29 scientific input must be parquet: {path}")
        paths[label] = path
    return paths


def _select_frames_with_paths(input_paths: Any, config: Mapping[str, Any],
                              input_root: str | Path | None = None) -> tuple[dict[str, pd.DataFrame], dict[str, Path]]:
    paths = _resolve_input_paths(input_paths, config, input_root)
    selected: dict[str, pd.DataFrame] = {}
    for label in config["source_order"]:
        table = normalize_pair_columns(load_pairs_table(paths[label]))
        start = int(config["sources"][label]["frame_start"])
        end = int(config["sources"][label]["frame_end"])
        part = table[(table["frame_id"] >= start) & (table["frame_id"] <= end)].copy()
        expected_frames = list(range(start, end + 1))
        if sorted(part["frame_id"].unique().tolist()) != expected_frames:
            raise ValueError(f"{label}: frame range {start}..{end} is incomplete")
        for frame_id in expected_frames:
            frame = part[part["frame_id"] == frame_id].sort_values("pair_idx")
            if len(frame) != FRAME_PAIRS or frame["pair_idx"].tolist() != list(range(FRAME_PAIRS)):
                raise ValueError(f"{label}: frame {frame_id} must contain pair_idx 0..255 exactly")
            for column in ("alice_symbol", "bob_symbol"):
                values = frame[column].to_numpy(dtype=np.int64)
                if np.any(values < 0) or np.any(values >= 1024):
                    raise ValueError(f"{label}: {column} outside 10-bit symbol domain")
        part = part.sort_values(["frame_id", "pair_idx"]).reset_index(drop=True)
        part.attrs["source_path"] = str(paths[label])
        selected[label] = part
    return selected, paths


def select_frames(input_paths: Any = None, config: Mapping[str, Any] | None = None,
                  input_root: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Read and validate the registered V29 frame ranges."""
    selected, _ = _select_frames_with_paths(input_paths, _config(config), input_root)
    return selected


def load_blocks(input_paths: Any = None, config: Mapping[str, Any] | None = None,
                input_root: str | Path | None = None) -> list[dict[str, Any]]:
    """Group selected rows in frozen source/frame order into 1024 symbols."""
    cfg = _config(config)
    selected, paths = _select_frames_with_paths(input_paths, cfg, input_root)
    blocks: list[dict[str, Any]] = []
    global_index = 0
    for label in cfg["source_order"]:
        info = cfg["sources"][label]
        frame_ids = list(range(int(info["frame_start"]), int(info["frame_end"]) + 1))
        if len(frame_ids) % BLOCK_FRAMES:
            raise ValueError(f"{label}: selected frame count must be divisible by four")
        for block_index in range(len(frame_ids) // BLOCK_FRAMES):
            group_ids = frame_ids[block_index * BLOCK_FRAMES:(block_index + 1) * BLOCK_FRAMES]
            groups = [selected[label][selected[label]["frame_id"] == frame_id].sort_values("pair_idx")
                      for frame_id in group_ids]
            alice = np.concatenate([group["alice_symbol"].to_numpy(dtype=np.int64) for group in groups])
            bob = np.concatenate([group["bob_symbol"].to_numpy(dtype=np.int64) for group in groups])
            if len(alice) != N or len(bob) != N:
                raise ValueError(f"{label} block {block_index}: expected 1024 symbols")
            blocks.append({
                "source": label, "source_id": info["source_id"],
                "delay_used_ps": info["delay_used_ps"], "source_path": str(paths[label]),
                "block_index": block_index, "global_block_index": global_index,
                "frame_ids": group_ids,
                "pair_idx_ranges": [[0, FRAME_PAIRS - 1] for _ in group_ids],
                "alice_symbols": alice, "bob_symbols": bob,
            })
            global_index += 1
    expected = sum(int(cfg["sources"][label]["block_count"]) for label in cfg["source_order"])
    if len(blocks) != expected:
        raise ValueError(f"expected {expected} blocks, got {len(blocks)}")
    return blocks


def leakage_bits(m_total: int, q: int = Q, tag_bits: int = TAG_BITS) -> int:
    """Return `(m_total * log2(q)) + 64` for frozen GF(32) accounting."""
    return int(m_total) * int(round(math.log2(q))) + int(tag_bits)


def factor_layers(symbols: Sequence[int]) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(symbols, dtype=np.int64)
    if values.ndim != 1 or np.any(values < 0) or np.any(values >= 1024):
        raise ValueError("F03 symbols must be a one-dimensional 10-bit array")
    return ((values >> 5) & 31).astype(np.int64), (values & 31).astype(np.int64)


def tag64(x1: Sequence[int] | None, x2: Sequence[int] | None) -> str | None:
    if x1 is None or x2 is None:
        return None
    payload = bytes(int(v) & 0xFF for v in x1) + bytes(int(v) & 0xFF for v in x2)
    return hashlib.sha256(payload).digest()[:8].hex()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")


def _frame_selection_doc(blocks: Sequence[Mapping[str, Any]], cfg: Mapping[str, Any]) -> dict[str, Any]:
    sources: dict[str, Any] = {}
    for label in cfg["source_order"]:
        info = cfg["sources"][label]
        rows = [block for block in blocks if block["source"] == label]
        frame_ids = [fid for block in rows for fid in block["frame_ids"]]
        sources[label] = {
            "source_id": info["source_id"], "delay_used_ps": info["delay_used_ps"],
            "pairs_parquet": str(rows[0].get("source_path", "<in-memory>")) if rows else "<none>",
            "frame_start": int(info["frame_start"]), "frame_end": int(info["frame_end"]),
            "frame_ids": frame_ids, "pair_count_per_frame": FRAME_PAIRS,
            "pair_idx_range": [0, FRAME_PAIRS - 1],
        }
    return {"schema": "nbldpc_v29_frame_selection_v1", "sources": sources}


def _block_manifest_doc(blocks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    keys = ("global_block_index", "source", "source_id", "delay_used_ps",
            "block_index", "frame_ids", "pair_idx_ranges")
    return {"schema": "nbldpc_v29_block_manifest_v1", "block_count": len(blocks),
            "blocks": [{key: block[key] for key in keys} for block in blocks]}


def _matrix_binding(cfg: Mapping[str, Any]) -> dict[str, Any]:
    vcfg = v28.frozen_v28_config()
    return {
        "schema": "nbldpc_v29_v28r_matrix_binding_v1", "v28r_schema": vcfg["schema"],
        "q": Q, "n": N, "m1": v28.M1,
        "m2": {label: int(cfg["sources"][label]["m2"]) for label in cfg["source_order"]},
        "seed_l1": vcfg["seed_l1"], "seed_l2": vcfg["seed_l2"],
        "topology": vcfg["topology"], "coefficient_call": vcfg["coefficient_call"],
        "factorization": vcfg["factorization"],
        "matrix_summary": v28._matrix_summary(vcfg),
    }


def _channel_binding(cfg: Mapping[str, Any], test_mode: bool) -> dict[str, Any]:
    return {
        "schema": "nbldpc_v29_channel_model_binding_v1",
        "model": "injected_test_adapter" if test_mode else "V26_train_only_source_delay_conditioned",
        "fit_source": "test_only_injected" if test_mode else "V26_train_split_only",
        "holdout_fit": False, "source_order": list(cfg["source_order"]),
        "sources": {label: {"source_id": cfg["sources"][label]["source_id"],
                             "delay_used_ps": cfg["sources"][label]["delay_used_ps"]}
                    for label in cfg["source_order"]},
    }


def _default_adapters() -> dict[str, Any]:
    """Load the frozen V26 train adapters; never synthesize a canonical fallback."""
    from .nonbinary_v26_channel import build_adapter, load_channel_counts
    counts = load_channel_counts()
    return {label: build_adapter(counts, fact_id="F03", source=SOURCE_IDS[label])
            for label in SOURCE_ORDER}


def _default_decoder(block: Mapping[str, Any], public: Mapping[str, Any], adapter: Any,
                     matrices: Mapping[str, Any], cfg: Mapping[str, Any]) -> dict[str, Any]:
    """Thin Bob-only V28R/V26 empirical sequential decoder.

    ``block`` is sanitized and contains Bob observations only.  Alice values
    are never passed to the adapter or either QSPA call.
    """
    started = time.monotonic()
    field = GF2mField.create(Q)
    bob = np.asarray(public["bob_symbols"], dtype=np.int64)
    y1, y2 = factor_layers(bob)
    rows1 = adapter.posterior_rows("L1", bob)
    r1 = v28.decode_error_domain_posterior(
        field, y1.tolist(), matrices["L1"], public["s1"],
        v28._center_rows(field, rows1, y1), int(cfg["max_iter"]), streak=int(cfg["streak"]),
    )
    if r1.get("status") != qspa.STATUS_SUCCESS or not r1.get("reconstruction_ok"):
        return {"L1": r1, "L2": {"status": "not_run", "x_hat": None,
                                  "syndrome_ok": False, "reconstruction_ok": False},
                "x1_hat": r1.get("x_hat"), "x2_hat": None,
                "l2_conditioning": "not_run", "decoder_calls": 1,
                "runtime_s": time.monotonic() - started}
    x1_hat = r1.get("x_hat")
    rows2 = adapter.posterior_rows("L2", bob, x1_hat)
    r2 = v28.decode_error_domain_posterior(
        field, y2.tolist(), matrices["L2"], public["s2"],
        v28._center_rows(field, rows2, y2), int(cfg["max_iter"]), streak=int(cfg["streak"]),
    )
    return {"L1": r1, "L2": r2, "x1_hat": x1_hat, "x2_hat": r2.get("x_hat"),
            "l2_conditioning": "returned_L1_x1_hat", "decoder_calls": 2,
            "runtime_s": time.monotonic() - started}


def _layer_success(layer: Mapping[str, Any]) -> bool:
    return layer.get("status") == qspa.STATUS_SUCCESS and bool(layer.get("reconstruction_ok", True))


def _config_contract_problems(cfg: Mapping[str, Any]) -> list[str]:
    """Return violations of the V29 frozen scientific/configuration contract."""
    problems: list[str] = []
    scalar_expected = {
        "q": Q,
        "n": N,
        "factorization": "F03_natural_MSB_to_LSB_GF32_plus_GF32",
        "max_iter": MAX_ITER,
        "streak": STREAK,
        "tag_bits": TAG_BITS,
        "tag_method": "sha256(bytes(x1)||bytes(x2))[:8]",
    }
    for key, expected in scalar_expected.items():
        if cfg.get(key) != expected:
            problems.append(f"config mismatch: {key}")
    if list(cfg.get("source_order", [])) != list(SOURCE_ORDER):
        problems.append("config mismatch: source_order")
    expected_gate = {"min_tag_verified_per_source": 95,
                     "min_offline_exact_per_source": 95,
                     "false_accept_count": 0, "all_blocks_required": True}
    if cfg.get("gate") != expected_gate:
        problems.append("config mismatch: gate")
    if set(cfg.get("sources", {})) != set(SOURCE_ORDER):
        problems.append("config mismatch: source labels")
    for label in SOURCE_ORDER:
        info = cfg.get("sources", {}).get(label, {})
        frozen = _frozen_source(label)
        # These fields are scientific identity/accounting bindings.  They are
        # deliberately exact, rather than recomputed from a modified config.
        for key in ("source_id", "delay_used_ps", "n_pairs", "frame_start", "frame_end",
                    "frame_count", "pair_count_per_frame", "block_count", "m1", "m2",
                    "m_total", "leak_bits", "h_total"):
            if info.get(key) != frozen[key]:
                problems.append(f"{label}: config mismatch: {key}")
        expected_leak = leakage_bits(frozen["m_total"], Q, TAG_BITS)
        if info.get("leak_bits") != expected_leak:
            problems.append(f"{label}: leakage binding mismatch")
        expected_f = expected_leak / (N * float(frozen["h_total"]))
        try:
            if float(info.get("f")) != expected_f:
                problems.append(f"{label}: f binding mismatch")
        except (TypeError, ValueError):
            problems.append(f"{label}: f binding is not numeric")
        if float(frozen["h_total"]) <= 0 or expected_f >= 1.3:
            problems.append(f"{label}: frozen f is not below 1.3")
    return problems


def _validate_bindings(cfg: Mapping[str, Any], blocks: Sequence[Mapping[str, Any]]) -> list[str]:
    """Validate the exact 300-block identity/order contract before decoding."""
    problems = _config_contract_problems(cfg)
    expected_count = len(SOURCE_ORDER) * BLOCKS_PER_SOURCE
    if len(blocks) != expected_count:
        problems.append(f"blocks: expected exactly {expected_count}, got {len(blocks)}")
    for global_index, block in enumerate(blocks):
        if global_index >= expected_count:
            problems.append(f"blocks: unexpected block at index {global_index}")
            break
        source_slot = global_index // BLOCKS_PER_SOURCE
        expected_source = SOURCE_ORDER[source_slot]
        expected_block_index = global_index % BLOCKS_PER_SOURCE
        info = cfg.get("sources", {}).get(expected_source, {})
        expected_start = int(SOURCE_FRAMES[expected_source][0]) + 4 * expected_block_index
        expected_frames = list(range(expected_start, expected_start + BLOCK_FRAMES))
        if block.get("global_block_index") != global_index:
            problems.append(f"block {global_index}: global_block_index mismatch")
        if block.get("source") != expected_source:
            problems.append(f"block {global_index}: source/order mismatch")
        if block.get("block_index") != expected_block_index:
            problems.append(f"block {global_index}: block_index mismatch")
        if block.get("source_id") != info.get("source_id"):
            problems.append(f"block {global_index}: source_id mismatch")
        if block.get("delay_used_ps") != info.get("delay_used_ps"):
            problems.append(f"block {global_index}: delay binding mismatch")
        try:
            if list(map(int, block.get("frame_ids", []))) != expected_frames:
                problems.append(f"block {global_index}: frame_ids mismatch")
            if block.get("pair_idx_ranges") != [[0, FRAME_PAIRS - 1]] * BLOCK_FRAMES:
                problems.append(f"block {global_index}: pair_idx_ranges mismatch")
            for key in ("alice_symbols", "bob_symbols"):
                values = np.asarray(block[key], dtype=np.int64)
                if values.shape != (N,) or np.any(values < 0) or np.any(values >= 1024):
                    problems.append(f"block {global_index}: {key} shape/domain mismatch")
        except (KeyError, TypeError, ValueError):
            problems.append(f"block {global_index}: malformed symbol/frame payload")
    return problems


def _layer_failure(row: Mapping[str, Any], layer: str) -> bool:
    status_key = f"{layer}_status"
    syndrome_key = f"{layer}_syndrome_ok"
    reconstruction_key = f"{layer}_reconstruction_ok"
    return (row.get(status_key) != qspa.STATUS_SUCCESS or
            row.get(reconstruction_key, True) is not True or
            row.get(syndrome_key) is not True)


def _decoder_record(block: Mapping[str, Any], public: Mapping[str, Any], result: Mapping[str, Any],
                    field: GF2mField, matrices: Mapping[str, Any], runtime_s: float,
                    decoder_calls: int) -> dict[str, Any]:
    l1 = dict(result.get("L1") or {})
    l2 = dict(result.get("L2") or {})
    l1_ok = _layer_success(l1)
    if not l1_ok and l2.get("status") not in {None, "not_run"}:
        raise ValueError("L2 must be not_run after L1 failure")
    x1 = l1.get("x_hat", result.get("x1_hat"))
    x2 = None if l2.get("status") == "not_run" or not l1_ok else l2.get("x_hat", result.get("x2_hat"))
    x1 = None if x1 is None else [int(value) for value in x1]
    x2 = None if x2 is None else [int(value) for value in x2]
    if x1 is not None and len(x1) != N or x2 is not None and len(x2) != N:
        raise ValueError("decoder layer estimate must contain 1024 symbols")
    truth1, truth2 = factor_layers(block["alice_symbols"])
    syndrome1_ok = x1 is not None and v28.compute_syndrome(field, matrices["L1"], x1) == public["s1"]
    syndrome2_ok = x2 is not None and v28.compute_syndrome(field, matrices["L2"], x2) == public["s2"]
    true_tag = tag64(truth1, truth2)
    decoded_tag = tag64(x1, x2)
    exact = bool(x1 is not None and x2 is not None and
                 np.array_equal(np.asarray(x1), truth1) and np.array_equal(np.asarray(x2), truth2))
    tag_verified = bool(decoded_tag is not None and decoded_tag == true_tag)
    return {
        "schema": "nbldpc_v29_block_result_v1",
        "global_block_index": int(block["global_block_index"]), "source": block["source"],
        "source_id": block["source_id"], "delay_used_ps": block["delay_used_ps"],
        "source_path": block.get("source_path", "<in-memory>"), "block_index": int(block["block_index"]),
        "frame_ids": list(map(int, block["frame_ids"])), "pair_idx_ranges": block["pair_idx_ranges"],
        "n_symbols": N, "l1_status": l1.get("status"), "l2_status": l2.get("status", "not_run"),
        "l1_reconstruction_ok": bool(l1.get("reconstruction_ok", True)),
        "l2_reconstruction_ok": bool(l2.get("reconstruction_ok", True)),
        "l1_iterations": l1.get("iterations"), "l2_iterations": l2.get("iterations"),
        "l1_syndrome": list(map(int, public["s1"])), "l2_syndrome": list(map(int, public["s2"])),
        "l1_syndrome_ok": bool(syndrome1_ok), "l2_syndrome_ok": bool(syndrome2_ok),
        "x1_hat": x1, "x2_hat": x2, "tag_true": true_tag, "tag_decoded": decoded_tag,
        "tag_verified": tag_verified, "offline_exact": exact,
        "false_accept": bool(tag_verified and not exact),
        "l1_symbol_errors": None if x1 is None else int(np.count_nonzero(np.asarray(x1) != truth1)),
        "l2_symbol_errors": None if x2 is None else int(np.count_nonzero(np.asarray(x2) != truth2)),
        "decoder_calls": int(decoder_calls), "decoder_runtime_s": float(runtime_s),
        "alice_truth_used": False, "truth_persistence": "public_syndrome_tag_and_offline_score_only",
        "l2_conditioning": result.get("l2_conditioning", "not_run" if not l1_ok else "returned_L1_x1_hat"),
    }


def _summary(records: Sequence[Mapping[str, Any]], cfg: Mapping[str, Any]) -> dict[str, Any]:
    sources: dict[str, Any] = {}
    for label in cfg["source_order"]:
        rows = [row for row in records if row["source"] == label]
        completed = len(rows)
        exact = sum(bool(row["offline_exact"]) for row in rows)
        sources[label] = {
            "source": label, "source_id": cfg["sources"][label]["source_id"],
            "delay_used_ps": cfg["sources"][label]["delay_used_ps"],
            "expected_block_count": int(cfg["sources"][label]["block_count"]),
            "completed_block_count": completed,
            "l1_fail_count": sum(_layer_failure(row, "l1") for row in rows),
            "l2_conditional_fail_count": sum(
                not _layer_failure(row, "l1") and _layer_failure(row, "l2")
                for row in rows
            ),
            "tag_verified_count": sum(bool(row["tag_verified"]) for row in rows),
            "offline_exact_count": exact, "false_accept_count": sum(bool(row["false_accept"]) for row in rows),
            # L1 failure/syndrome failure is always a syndrome failure.  If L1
            # verifies but L2 is not_run, that is also a conditional failure.
            "syndrome_fail_count": sum(
                _layer_failure(row, "l1") or
                (not _layer_failure(row, "l1") and _layer_failure(row, "l2"))
                for row in rows
            ),
            "decoder_fail_count": sum(
                _layer_failure(row, "l1") or
                (not _layer_failure(row, "l1") and _layer_failure(row, "l2"))
                for row in rows
            ),
            "fer": None if not rows else 1.0 - exact / completed,
        }
    all_rows = list(records)
    exact = sum(bool(row["offline_exact"]) for row in all_rows)
    return {"schema": "nbldpc_v29_source_summary_v1", "sources": sources,
            "global": {"expected_block_count": sum(item["expected_block_count"] for item in sources.values()),
                        "completed_block_count": len(all_rows), "tag_verified_count": sum(bool(row["tag_verified"]) for row in all_rows),
                        "offline_exact_count": exact, "false_accept_count": sum(bool(row["false_accept"]) for row in all_rows),
                        "fer": None if not all_rows else 1.0 - exact / len(all_rows)},
            "fer_scope": ("full_300_blocks" if len(all_rows) == len(SOURCE_ORDER) * BLOCKS_PER_SOURCE
                          else "observed_prefix_only")}


def _scientific_pass(summary: Mapping[str, Any], cfg: Mapping[str, Any]) -> bool:
    gate = cfg["gate"]
    if _config_contract_problems(cfg):
        return False
    for label in cfg["source_order"]:
        info = cfg["sources"][label]
        expected_leak = leakage_bits(int(info["m_total"]), Q, TAG_BITS)
        f = expected_leak / (N * float(info["h_total"]))
        source = summary["sources"][label]
        if (source["tag_verified_count"] < int(gate["min_tag_verified_per_source"])
                or source["offline_exact_count"] < int(gate["min_offline_exact_per_source"])
                or source["false_accept_count"] != int(gate["false_accept_count"])
                or int(info["leak_bits"]) != expected_leak
                or f >= 1.3):
            return False
    return True


def _early_fail_proof(summary: Mapping[str, Any], cfg: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return a proof that a per-source threshold can no longer be met.

    This is a gate decision only.  It never promotes a prefix FER to a
    full-300-block FER and is evaluated only after the current block record is
    durably written.
    """
    threshold = int(cfg["gate"]["min_offline_exact_per_source"])
    tag_threshold = int(cfg["gate"]["min_tag_verified_per_source"])
    for label in cfg["source_order"]:
        source = summary["sources"][label]
        expected = int(source["expected_block_count"])
        completed = int(source["completed_block_count"])
        remaining = expected - completed
        exact = int(source["offline_exact_count"])
        tags = int(source["tag_verified_count"])
        false_accepts = int(source["false_accept_count"])
        if false_accepts > int(cfg["gate"]["false_accept_count"]):
            return {
                "schema": "nbldpc_v29_early_fail_proof_v1",
                "reason": "false_accept_count_exceeded",
                "source": label, "completed_source_blocks": completed,
                "expected_source_blocks": expected, "remaining_expected": remaining,
                "tag_verified_count": tags, "offline_exact_count": exact,
                "false_accept_count": false_accepts, "threshold": threshold,
                "max_possible_tag_verified": tags + remaining,
                "max_possible_offline_exact": exact + remaining,
                "condition": "false_accept_count > 0",
            }
        if exact + remaining < threshold:
            return {
                "schema": "nbldpc_v29_early_fail_proof_v1",
                "reason": "offline_exact_threshold_irreversible",
                "source": label, "completed_source_blocks": completed,
                "expected_source_blocks": expected, "remaining_expected": remaining,
                "tag_verified_count": tags, "offline_exact_count": exact,
                "false_accept_count": false_accepts, "threshold": threshold,
                "max_possible_tag_verified": tags + remaining,
                "max_possible_offline_exact": exact + remaining,
                "condition": "offline_exact_count + remaining_expected < threshold",
            }
        if tags + remaining < tag_threshold:
            return {
                "schema": "nbldpc_v29_early_fail_proof_v1",
                "reason": "tag_verified_threshold_irreversible",
                "source": label, "completed_source_blocks": completed,
                "expected_source_blocks": expected, "remaining_expected": remaining,
                "tag_verified_count": tags, "offline_exact_count": exact,
                "false_accept_count": false_accepts, "threshold": tag_threshold,
                "max_possible_tag_verified": tags + remaining,
                "max_possible_offline_exact": exact + remaining,
                "condition": "tag_verified_count + remaining_expected < threshold",
            }
    return None


def run_v29(output_root: str | Path, input_paths: Any = None,
            config: Mapping[str, Any] | None = None,
            decoder_fn: Any = None, *, adapters: Mapping[str, Any] | None = None,
            blocks: Sequence[Mapping[str, Any]] | None = None,
            input_root: str | Path | None = None) -> dict[str, Any]:
    """Run the V29 block state machine and write the first eight evidence files.

    The fixed test/extension decoder signature is
    ``decoder_fn(block_without_alice, public_inputs, adapter, matrices, config)``.
    The official holdout path is not used by tests; tests inject ``blocks`` and
    ``decoder_fn``.  ``readonly_verify.json`` is intentionally deferred.
    """
    cfg = _config(config)
    root = Path(output_root)
    if root.exists():
        raise FileExistsError(f"V29 output root must be new: {root}")
    root.mkdir(parents=True, exist_ok=False)
    load_error: str | None = None
    try:
        if blocks is None:
            ordered = load_blocks(input_paths, cfg, input_root)
            paths = _resolve_input_paths(input_paths, cfg, input_root)
        else:
            ordered = [dict(block) for block in blocks]
            if input_paths is None:
                paths = {label: Path("<in-memory>") for label in cfg["source_order"]}
            else:
                paths = _resolve_input_paths(input_paths, cfg, input_root)
                # Test injection may provide block objects with an in-memory
                # provenance marker; the selected parquet paths remain the
                # persisted binding used by the verifier.
                for block in ordered:
                    if block.get("source") in paths:
                        block["source_path"] = str(paths[block["source"]])
    except Exception as exc:
        ordered = []
        try:
            paths = _resolve_input_paths(input_paths, cfg, input_root)
        except Exception:
            paths = {label: Path("<unresolved>") for label in cfg.get("source_order", SOURCE_ORDER)}
        load_error = f"{type(exc).__name__}: {exc}"
    expected_order = list(cfg.get("source_order", SOURCE_ORDER))
    binding_problems = _validate_bindings(cfg, ordered)
    if load_error is not None:
        binding_problems.insert(0, f"input loading failed: {load_error}")
    test_mode = decoder_fn is not None or adapters is not None or blocks is not None
    vcfg = v28.frozen_v28_config()
    h1, h2map = v28.build_matrices(vcfg)
    field = GF2mField.create(Q)
    matrices = {"L1": h1}
    frame_doc = _frame_selection_doc(ordered, cfg)
    block_doc = _block_manifest_doc(ordered)
    channel_doc = _channel_binding(cfg, test_mode)
    matrix_doc = _matrix_binding(cfg)
    _write_json(root / "frame_selection.json", frame_doc)
    _write_json(root / "block_manifest.json", block_doc)
    _write_json(root / "channel_model_binding.json", channel_doc)
    _write_json(root / "matrix_binding.json", matrix_doc)
    records: list[dict[str, Any]] = []
    cumulative = 0.0
    decoder_calls = 0
    terminal: str | None = None
    error_detail: str | None = "; ".join(binding_problems) if binding_problems else None
    early_proof: dict[str, Any] | None = None
    if not binding_problems:
        adapter_map = dict(adapters or {})
        if decoder_fn is None:
            try:
                adapter_map = _default_adapters()
            except Exception as exc:
                terminal = TERMINAL_IMPL
                error_detail = f"{type(exc).__name__}: {exc}"
    with (root / "per_block_results.jsonl").open("w", encoding="utf-8") as stream:
        for block in ordered if not binding_problems and terminal is None else []:
            source = block["source"]
            h2 = v28.layer_matrix(h2map, source, vcfg)
            truth1, truth2 = factor_layers(block["alice_symbols"])
            s1 = v28.compute_syndrome(field, h1, truth1.tolist())
            s2 = v28.compute_syndrome(field, h2, truth2.tolist())
            bob = np.asarray(block["bob_symbols"], dtype=np.int64)
            # The decoder receives only Bob observations and public syndromes.
            # True tags are computed here for the offline record and are never
            # part of the decoder call contract.
            public = {"bob_symbols": bob, "s1": s1, "s2": s2}
            oracle_keys = {"alice_symbols", "truth1", "truth2", "alice_truth",
                           "alice_x1", "alice_x2", "x1", "x2", "tag_true"}
            decoder_block = {key: value for key, value in block.items() if key not in oracle_keys}
            started = time.monotonic()
            try:
                if decoder_fn is None:
                    result = _default_decoder(decoder_block, public, adapter_map[source],
                                              {"L1": h1, "L2": h2}, cfg)
                else:
                    result = decoder_fn(decoder_block, public, adapter_map.get(source),
                                        {"L1": h1, "L2": h2}, cfg)
                if not isinstance(result, Mapping):
                    raise TypeError("decoder_fn must return a mapping")
                runtime = float(result.get("runtime_s", time.monotonic() - started))
                if not math.isfinite(runtime) or runtime < 0:
                    raise ValueError("decoder runtime must be finite and nonnegative")
                calls = int(result.get("decoder_calls", 1 if (result.get("L2") or {}).get("status") == "not_run" else 2))
                record = _decoder_record(block, public, result, field,
                                         {"L1": h1, "L2": h2}, runtime, calls)
            except Exception as exc:
                terminal = TERMINAL_IMPL
                error_detail = f"{type(exc).__name__}: {exc}"
                break
            cumulative += runtime
            decoder_calls += calls
            records.append(record)
            stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            complete = len(records) == len(ordered) == len(SOURCE_ORDER) * BLOCKS_PER_SOURCE
            if complete:
                terminal = TERMINAL_PASS if _scientific_pass(_summary(records, cfg), cfg) else TERMINAL_FAIL
                break
            early_proof = _early_fail_proof(_summary(records, cfg), cfg)
            if early_proof is not None:
                terminal = TERMINAL_FAIL
                break
            if cumulative >= float(cfg["resource_limit_seconds"]):
                terminal = TERMINAL_RESOURCE
                break
    if terminal is None:
        terminal = TERMINAL_RESOURCE if cumulative >= float(cfg["resource_limit_seconds"]) else TERMINAL_IMPL
    summary = _summary(records, cfg)
    expected_block_count = len(SOURCE_ORDER) * BLOCKS_PER_SOURCE
    gate = {"schema": "nbldpc_v29_gate_v1", "status": terminal,
            "completed_block_count": len(records), "expected_block_count": expected_block_count,
            "decoder_call_count": decoder_calls, "decoder_wallclock_seconds": cumulative,
            "resource_limit_seconds": cfg["resource_limit_seconds"],
            "scientific_gate_evaluated": len(records) == expected_block_count,
            "stop_before_next_block": True, "error_detail": error_detail,
            "early_fail_proof": early_proof,
            "user_authorized_stop": False,
            "evidence_files_written": list(PRE_VERIFY_FILES),
            "readonly_verify_pending": True}
    _write_json(root / "source_summary.json", summary)
    _write_json(root / "gate.json", gate)
    manifest = {"schema": "nbldpc_v29_run_manifest_v1",
                "run_role": "v29_retrospective_finite_code_gate",
                "frozen_config": cfg, "source_order": expected_order,
                "input_paths": {label: str(paths[label]) for label in expected_order},
                "evidence_files": list(PRE_VERIFY_FILES), "readonly_verify_pending": True,
                "channel_model_binding": channel_doc, "matrix_binding_schema": matrix_doc["schema"],
                "terminal_state": terminal, "completed_block_count": len(records),
                "decoder_call_count": decoder_calls, "decoder_wallclock_seconds": cumulative}
    _write_json(root / "RUN_MANIFEST.json", manifest)
    return {"status": terminal, "evidence_root": str(root), "gate": gate,
            "source_summary": summary}


def _same_float(left: Any, right: Any, tol: float = 1e-12) -> bool:
    try:
        return abs(float(left) - float(right)) <= tol
    except (TypeError, ValueError):
        return False


def _record_truth_metrics(block: Mapping[str, Any], row: Mapping[str, Any], field: GF2mField,
                          matrices: Mapping[str, Any], public_s1: Sequence[int],
                          public_s2: Sequence[int]) -> dict[str, Any]:
    truth1, truth2 = factor_layers(block["alice_symbols"])
    x1 = row.get("x1_hat")
    x2 = row.get("x2_hat")
    x1_values = None if x1 is None else [int(v) for v in x1]
    x2_values = None if x2 is None else [int(v) for v in x2]
    syndrome1_ok = x1_values is not None and v28.compute_syndrome(
        field, matrices["L1"], x1_values) == list(public_s1)
    syndrome2_ok = x2_values is not None and v28.compute_syndrome(
        field, matrices["L2"], x2_values) == list(public_s2)
    true_tag = tag64(truth1, truth2)
    decoded_tag = tag64(x1_values, x2_values)
    exact = bool(x1_values is not None and x2_values is not None and
                 np.array_equal(np.asarray(x1_values), truth1) and
                 np.array_equal(np.asarray(x2_values), truth2))
    return {
        "l1_syndrome": list(map(int, public_s1)), "l2_syndrome": list(map(int, public_s2)),
        "l1_syndrome_ok": bool(syndrome1_ok), "l2_syndrome_ok": bool(syndrome2_ok),
        "tag_true": true_tag, "tag_decoded": decoded_tag,
        "tag_verified": bool(decoded_tag is not None and decoded_tag == true_tag),
        "offline_exact": exact,
        "false_accept": bool(decoded_tag is not None and decoded_tag == true_tag and not exact),
        "l1_symbol_errors": None if x1_values is None else int(np.count_nonzero(np.asarray(x1_values) != truth1)),
        "l2_symbol_errors": None if x2_values is None else int(np.count_nonzero(np.asarray(x2_values) != truth2)),
    }


def _manifest_blocks(frame_doc: Mapping[str, Any], block_doc: Mapping[str, Any],
                     cfg: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Build identity-only blocks from persisted manifests.

    This path is used only for an authorized irreversible early-fail prefix;
    it intentionally contains no Alice/Bob symbols and therefore does not
    trigger a parquet read.
    """
    sources = frame_doc.get("sources", {})
    blocks = []
    for item in block_doc.get("blocks", []):
        source = item.get("source")
        source_info = sources.get(source, {}) if isinstance(sources, Mapping) else {}
        blocks.append({
            "global_block_index": item.get("global_block_index"),
            "source": source, "source_id": item.get("source_id"),
            "delay_used_ps": item.get("delay_used_ps"),
            "source_path": source_info.get("pairs_parquet", "<unknown>"),
            "block_index": item.get("block_index"), "frame_ids": item.get("frame_ids"),
            "pair_idx_ranges": item.get("pair_idx_ranges"),
        })
    return blocks


def _validate_manifest_prefix(frame_doc: Mapping[str, Any], block_doc: Mapping[str, Any],
                              records: Sequence[Mapping[str, Any]],
                              cfg: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate manifest/frame identity without loading scientific parquet."""
    problems: list[str] = []
    blocks = _manifest_blocks(frame_doc, block_doc, cfg)
    expected_count = len(SOURCE_ORDER) * BLOCKS_PER_SOURCE
    if block_doc.get("schema") != "nbldpc_v29_block_manifest_v1":
        problems.append("block manifest schema mismatch")
    if block_doc.get("block_count") != expected_count or len(blocks) != expected_count:
        problems.append("block manifest is not the frozen 300-block manifest")
    if frame_doc.get("schema") != "nbldpc_v29_frame_selection_v1":
        problems.append("frame selection schema mismatch")
    expected_sources: dict[str, Any] = {}
    for label in SOURCE_ORDER:
        info = cfg["sources"][label]
        start, end = int(info["frame_start"]), int(info["frame_end"])
        entry = frame_doc.get("sources", {}).get(label, {})
        expected_sources[label] = {
            "source_id": info["source_id"], "delay_used_ps": info["delay_used_ps"],
            "pairs_parquet": entry.get("pairs_parquet"),
            "frame_start": start, "frame_end": end,
            "frame_ids": list(range(start, end + 1)),
            "pair_count_per_frame": FRAME_PAIRS, "pair_idx_range": [0, FRAME_PAIRS - 1],
        }
        for key, expected in expected_sources[label].items():
            if entry.get(key) != expected:
                problems.append(f"{label}: frame manifest {key} mismatch")
    for index, block in enumerate(blocks):
        if index >= expected_count:
            break
        label = SOURCE_ORDER[index // BLOCKS_PER_SOURCE]
        source_info = cfg["sources"][label]
        expected_first = int(source_info["frame_start"]) + 4 * (index % BLOCKS_PER_SOURCE)
        expected = {
            "global_block_index": index, "source": label,
            "source_id": source_info["source_id"],
            "delay_used_ps": source_info["delay_used_ps"],
            "block_index": index % BLOCKS_PER_SOURCE,
            "frame_ids": list(range(expected_first, expected_first + BLOCK_FRAMES)),
            "pair_idx_ranges": [[0, FRAME_PAIRS - 1]] * BLOCK_FRAMES,
        }
        for key, value in expected.items():
            if block.get(key) != value:
                problems.append(f"block manifest {index}: {key} mismatch")
    if len(records) > expected_count:
        problems.append("record prefix exceeds 300 blocks")
    for index, row in enumerate(records):
        if index >= len(blocks):
            break
        block = blocks[index]
        for key in ("global_block_index", "source", "source_id", "delay_used_ps",
                    "block_index", "frame_ids", "pair_idx_ranges"):
            if row.get(key) != block.get(key):
                problems.append(f"record {index}: {key} does not match manifest")
        if row.get("source_path") != block.get("source_path"):
            problems.append(f"record {index}: source_path does not match frame manifest")
    return blocks, problems


def _validate_prefix_record_shape(row: Mapping[str, Any], index: int) -> list[str]:
    """Check internal record consistency when truth parquet is intentionally not read."""
    problems: list[str] = []
    forbidden = {"alice_symbols", "truth1", "truth2", "alice_truth", "alice_x1", "alice_x2"}
    if forbidden.intersection(row):
        problems.append(f"record {index}: persisted Alice truth is forbidden")
    if row.get("l1_status") != qspa.STATUS_SUCCESS and row.get("l2_status") != "not_run":
        problems.append(f"record {index}: L2 ran after L1 failure")
    tag_true, tag_decoded = row.get("tag_true"), row.get("tag_decoded")
    if row.get("tag_verified") is not (tag_true is not None and tag_decoded == tag_true):
        problems.append(f"record {index}: tag_verified is internally inconsistent")
    if row.get("false_accept") is not bool(row.get("tag_verified") and not row.get("offline_exact")):
        problems.append(f"record {index}: false_accept is internally inconsistent")
    if row.get("l2_conditioning") != (
            "not_run" if row.get("l1_status") != qspa.STATUS_SUCCESS
            else "returned_L1_x1_hat"):
        problems.append(f"record {index}: L2 conditioning marker mismatch")
    return problems


def finalize_stopped_prefix(run_root: str | Path, input_paths: Any = None,
                            user_stop_reason: str = "") -> dict[str, Any]:
    """Close an authorized irreversible-fail prefix without reading parquet.

    The function only reads the five already-persisted identity/evidence files
    plus `per_block_results.jsonl`.  It writes the three missing closeout files
    and delegates the final consistency check to the proof-aware verifier.
    The finalizer itself does not read parquet; the verifier then reloads the
    registered parquet rows and recomputes the completed-prefix truth metrics.
    """
    del input_paths
    root = Path(run_root)
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(root)
    if not isinstance(user_stop_reason, str) or not user_stop_reason.strip():
        raise ValueError("user_stop_reason is required for an authorized prefix stop")
    base_files = {"frame_selection.json", "block_manifest.json",
                  "channel_model_binding.json", "matrix_binding.json",
                  "per_block_results.jsonl"}
    actual_files = {path.name for path in root.iterdir() if path.is_file()}
    if actual_files != base_files:
        raise ValueError("prefix finalizer requires exactly the existing five V29 files")

    def read_json(name: str) -> Any:
        return json.loads((root / name).read_text(encoding="utf-8"))

    frame_doc = read_json("frame_selection.json")
    block_doc = read_json("block_manifest.json")
    channel_doc = read_json("channel_model_binding.json")
    matrix_doc = read_json("matrix_binding.json")
    rows = [json.loads(line) for line in (root / "per_block_results.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()]
    cfg = frozen_v29_config()
    blocks, problems = _validate_manifest_prefix(frame_doc, block_doc, rows, cfg)
    for index, row in enumerate(rows):
        problems.extend(_validate_prefix_record_shape(row, index))
    if len(rows) >= len(SOURCE_ORDER) * BLOCKS_PER_SOURCE:
        problems.append("prefix finalizer requires an incomplete run")
    if channel_doc.get("model") not in {"V26_train_only_source_delay_conditioned", "injected_test_adapter"}:
        problems.append("unknown channel model binding")
    if matrix_doc != _matrix_binding(cfg):
        problems.append("matrix binding does not match frozen V28R config")
    if problems:
        raise ValueError("cannot finalize prefix: " + "; ".join(problems))

    summary = _summary(rows, cfg)
    proof = _early_fail_proof(summary, cfg)
    if proof is None:
        raise ValueError("prefix has no mathematically irreversible threshold failure")
    runtime = sum(float(row.get("decoder_runtime_s", 0.0)) for row in rows)
    calls = sum(int(row.get("decoder_calls", 0)) for row in rows)
    terminal = TERMINAL_FAIL
    gate = {
        "schema": "nbldpc_v29_gate_v1", "status": terminal,
        "completed_block_count": len(rows),
        "expected_block_count": len(SOURCE_ORDER) * BLOCKS_PER_SOURCE,
        "decoder_call_count": calls, "decoder_wallclock_seconds": runtime,
        "resource_limit_seconds": cfg["resource_limit_seconds"],
        "scientific_gate_evaluated": False, "stop_before_next_block": True,
        "error_detail": user_stop_reason,
        "early_fail_proof": proof, "user_authorized_stop": True,
        "user_stop_reason": user_stop_reason,
        "evidence_files_written": list(PRE_VERIFY_FILES),
        "readonly_verify_pending": True,
    }
    _write_json(root / "source_summary.json", summary)
    _write_json(root / "gate.json", gate)
    input_manifest = {
        label: frame_doc["sources"][label]["pairs_parquet"] for label in SOURCE_ORDER
    }
    manifest = {
        "schema": "nbldpc_v29_run_manifest_v1",
        "run_role": "v29_retrospective_finite_code_gate",
        "frozen_config": cfg, "source_order": list(SOURCE_ORDER),
        "input_paths": input_manifest, "evidence_files": list(PRE_VERIFY_FILES),
        "readonly_verify_pending": True,
        "channel_model_binding": channel_doc,
        "matrix_binding_schema": matrix_doc.get("schema"),
        "terminal_state": terminal, "completed_block_count": len(rows),
        "decoder_call_count": calls, "decoder_wallclock_seconds": runtime,
        "early_fail_proof": proof, "user_authorized_stop": True,
        "user_stop_reason": user_stop_reason,
    }
    _write_json(root / "RUN_MANIFEST.json", manifest)
    verification = verify_v29(root)
    return {"status": terminal, "evidence_root": str(root), "gate": gate,
            "source_summary": summary, "readonly_verify": verification,
            "completed_block_count": len(rows), "early_fail_proof": proof}


def verify_v29(run_root: str | Path, input_paths: Any = None,
               *, input_root: str | Path | None = None) -> dict[str, Any]:
    """Rebuild V29 evidence without invoking a decoder.

    The verifier reads the selected parquet truth rows, reconstructs the
    frozen V28R matrices and public syndromes/tags, then checks the persisted
    block prefix, summaries, accounting, and terminal precedence.  It never
    loads a posterior adapter and never calls a decoder.
    """
    root = Path(run_root)
    problems: list[str] = []
    if not root.exists() or not root.is_dir():
        return {"schema": "nbldpc_v29_readonly_verify_v1", "ok": False,
                "problems": [f"missing evidence root: {root}"],
                "recomputed_terminal": TERMINAL_IMPL, "persisted_terminal": None,
                "decoder_rerun": False}

    actual_files = {path.name for path in root.iterdir() if path.is_file()}
    allowed_sets = (set(PRE_VERIFY_FILES), set(EVIDENCE_FILES))
    if actual_files != allowed_sets[0] and actual_files != allowed_sets[1]:
        problems.append("evidence file set must be exactly the first eight files or all nine files")
    missing = [name for name in PRE_VERIFY_FILES if name not in actual_files]
    if missing:
        problems.append("missing evidence files: " + ", ".join(missing))

    docs: dict[str, Any] = {}
    for name in PRE_VERIFY_FILES:
        path = root / name
        if not path.exists():
            continue
        try:
            if name.endswith(".jsonl"):
                docs[name] = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            else:
                docs[name] = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"cannot read {name}: {type(exc).__name__}: {exc}")

    manifest = docs.get("RUN_MANIFEST.json", {})
    gate = docs.get("gate.json", {})
    cfg_doc = manifest.get("frozen_config")
    if not isinstance(cfg_doc, Mapping):
        cfg_doc = frozen_v29_config()
        problems.append("manifest has no frozen_config")
    cfg = _config(cfg_doc)
    channel_doc = docs.get("channel_model_binding.json", {})
    test_mode = channel_doc.get("model") == "injected_test_adapter"

    early_mode = isinstance(gate.get("early_fail_proof"), Mapping)
    # The persisted path map is part of the input binding.  Every verifier
    # mode, including an authorized early-fail prefix, reloads parquet so that
    # syndrome, tag, exactness, and the irreversible-fail proof are independent
    # of the persisted block records.
    manifest_paths = manifest.get("input_paths", {})
    paths = None
    blocks: list[dict[str, Any]] = []
    try:
        path_source = input_paths if input_paths is not None else manifest_paths
        paths = _resolve_input_paths(path_source, cfg, input_root)
        if not isinstance(manifest_paths, Mapping):
            problems.append("manifest input_paths is not a mapping")
        for label in SOURCE_ORDER:
            persisted = str(manifest_paths.get(label, ""))
            if persisted != str(paths[label]):
                problems.append(f"{label}: manifest input path mismatch")
        if not test_mode:
            canonical_paths = _resolve_input_paths(None, cfg)
            for label in SOURCE_ORDER:
                if str(paths[label].resolve()) != str(canonical_paths[label].resolve()):
                    problems.append(f"{label}: canonical input path is not the registered V25 path")
    except Exception as exc:
        paths = None
        problems.append(f"input binding cannot be resolved: {type(exc).__name__}: {exc}")
    if paths is not None:
        try:
            blocks = load_blocks(paths, cfg)
        except Exception as exc:
            problems.append(f"cannot reconstruct parquet blocks: {type(exc).__name__}: {exc}")
    problems.extend(_validate_bindings(cfg, blocks))

    expected_frame_doc = _frame_selection_doc(blocks, cfg)
    expected_block_doc = _block_manifest_doc(blocks)
    if docs.get("frame_selection.json") != expected_frame_doc:
        problems.append("frame_selection.json does not match reconstructed parquet selection")
    if docs.get("block_manifest.json") != expected_block_doc:
        problems.append("block_manifest.json does not match reconstructed block order")
    expected_channel = _channel_binding(cfg, test_mode)
    if channel_doc != expected_channel:
        problems.append("channel_model_binding.json does not match the frozen channel contract")
    expected_matrix = _matrix_binding(cfg)
    matrix_doc = docs.get("matrix_binding.json")
    if matrix_doc != expected_matrix:
        problems.append("matrix_binding.json does not match the frozen V28R contract")

    # Rebuild the V28R matrices and check dimensions/rank/degree summary.  No
    # decoder or posterior is involved in this operation.
    vcfg = v28.frozen_v28_config()
    h1, h2map = v28.build_matrices(vcfg)
    field = GF2mField.create(Q)
    try:
        if v28.cb.gf_rank(h1, field) != v28.M1:
            problems.append("rebuilt L1 rank mismatch")
        if len(h1) != v28.M1 or any(len(row) != N for row in h1):
            problems.append("rebuilt L1 row count mismatch")
        for label in SOURCE_ORDER:
            h2 = v28.layer_matrix(h2map, label, vcfg)
            if v28.cb.gf_rank(h2, field) != int(vcfg["sources"][label]["m2"]):
                problems.append(f"rebuilt {label} L2 rank mismatch")
        if expected_matrix.get("matrix_summary") != v28._matrix_summary(vcfg):
            problems.append("rebuilt V28R matrix summary mismatch")
    except Exception as exc:
        problems.append(f"V28R matrix rebuild failed: {type(exc).__name__}: {exc}")

    rows = docs.get("per_block_results.jsonl", [])
    if not isinstance(rows, list) or len(rows) > len(SOURCE_ORDER) * BLOCKS_PER_SOURCE:
        problems.append("per_block_results.jsonl is not a valid completed prefix")
        rows = rows if isinstance(rows, list) else []
    matrices_for_source = {"L1": h1}
    records: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            problems.append(f"record {index}: not an object")
            continue
        forbidden = {"alice_symbols", "truth1", "truth2", "alice_truth", "alice_x1", "alice_x2"}
        if forbidden.intersection(row):
            problems.append(f"record {index}: persisted Alice truth is forbidden")
        if index >= len(blocks):
            problems.append(f"record {index}: no matching reconstructed block")
            continue
        block = blocks[index]
        identity = ("global_block_index", "source", "source_id", "delay_used_ps",
                    "block_index", "frame_ids", "pair_idx_ranges")
        for key in identity:
            if row.get(key) != block.get(key):
                problems.append(f"record {index}: {key} mismatch")
        h2 = v28.layer_matrix(h2map, block["source"], vcfg)
        matrices_for_source["L2"] = h2
        truth1, truth2 = factor_layers(block["alice_symbols"])
        s1 = v28.compute_syndrome(field, h1, truth1.tolist())
        s2 = v28.compute_syndrome(field, h2, truth2.tolist())
        metrics = _record_truth_metrics(block, row, field, matrices_for_source, s1, s2)
        for key, expected in metrics.items():
            actual = row.get(key)
            if actual != expected:
                problems.append(f"record {index}: {key} mismatch")
        expected_conditioning = (
            "not_run" if row.get("l1_status") != qspa.STATUS_SUCCESS
            else "returned_L1_x1_hat"
        )
        if row.get("l2_conditioning") != expected_conditioning:
            problems.append(f"record {index}: L2 conditioning marker mismatch")
        if row.get("l1_status") != qspa.STATUS_SUCCESS and row.get("l2_status") != "not_run":
            problems.append(f"record {index}: L2 ran after L1 failure")
        records.append(dict(row))

    summary = _summary(records, cfg)
    if docs.get("source_summary.json") != summary:
        problems.append("source_summary.json does not match recomputed records")

    expected_count = len(SOURCE_ORDER) * BLOCKS_PER_SOURCE
    completed = len(records)
    try:
        runtime = float(gate.get("decoder_wallclock_seconds"))
        calls = int(gate.get("decoder_call_count"))
    except (TypeError, ValueError):
        runtime, calls = float("nan"), -1
        problems.append("gate runtime/call count is malformed")
    row_runtime = sum(float(row.get("decoder_runtime_s", 0.0)) for row in records)
    row_calls = sum(int(row.get("decoder_calls", 0)) for row in records)
    if not _same_float(runtime, row_runtime):
        problems.append("gate decoder wall-clock does not match block records")
    if calls != row_calls:
        problems.append("gate decoder call count does not match block records")
    if gate.get("completed_block_count") != completed:
        problems.append("gate completed_block_count mismatch")
    if gate.get("expected_block_count") != expected_count:
        problems.append("gate expected_block_count mismatch")
    if gate.get("scientific_gate_evaluated") is not (completed == expected_count):
        problems.append("gate scientific_gate_evaluated mismatch")

    persisted_proof = gate.get("early_fail_proof")
    recomputed_proof = _early_fail_proof(summary, cfg)
    if early_mode:
        if persisted_proof != recomputed_proof or recomputed_proof is None:
            problems.append("early_fail_proof does not match recomputed prefix counters")
        if summary.get("fer_scope") != "observed_prefix_only":
            problems.append("early-fail summary must be scoped to observed prefix")
        if gate.get("scientific_gate_evaluated") is not False:
            problems.append("early-fail gate cannot claim full scientific evaluation")
        if gate.get("user_authorized_stop") is True and not str(gate.get("user_stop_reason", "")).strip():
            problems.append("authorized early stop has no user_stop_reason")
        recomputed_terminal = TERMINAL_FAIL if recomputed_proof is not None else TERMINAL_IMPL
    elif _config_contract_problems(cfg):
        recomputed_terminal = TERMINAL_IMPL
    elif completed == expected_count:
        recomputed_terminal = TERMINAL_PASS if _scientific_pass(summary, cfg) else TERMINAL_FAIL
    elif completed < expected_count and gate.get("status") == TERMINAL_RESOURCE:
        recomputed_terminal = TERMINAL_RESOURCE
        if not math.isfinite(runtime) or runtime < float(cfg.get("resource_limit_seconds", RESOURCE_LIMIT_SECONDS)):
            problems.append("resource_blocked terminal is below the resource limit")
    else:
        recomputed_terminal = TERMINAL_IMPL
    if gate.get("status") != recomputed_terminal:
        problems.append("gate status does not match recomputed terminal precedence")
    if manifest.get("terminal_state") != gate.get("status"):
        problems.append("manifest/gate terminal mismatch")
    if manifest.get("completed_block_count") != completed:
        problems.append("manifest completed_block_count mismatch")
    if manifest.get("decoder_call_count") != calls or not _same_float(manifest.get("decoder_wallclock_seconds"), runtime):
        problems.append("manifest decoder counters mismatch")
    if manifest.get("source_order") != list(SOURCE_ORDER):
        problems.append("manifest source order mismatch")
    if manifest.get("channel_model_binding") != channel_doc:
        problems.append("manifest/channel binding mismatch")
    if manifest.get("matrix_binding_schema") != matrix_doc.get("schema"):
        problems.append("manifest/matrix binding mismatch")
    if manifest.get("early_fail_proof") != gate.get("early_fail_proof"):
        problems.append("manifest/gate early_fail_proof mismatch")
    if manifest.get("evidence_files") != list(PRE_VERIFY_FILES):
        problems.append("manifest evidence file declaration mismatch")

    result = {
        "schema": "nbldpc_v29_readonly_verify_v1", "ok": not problems,
        "problems": problems, "recomputed_terminal": recomputed_terminal,
        "persisted_terminal": gate.get("status"), "decoder_rerun": False,
    }
    _write_json(root / "readonly_verify.json", result)
    return result
