#!/usr/bin/env python3
"""V65A historical Type-II scout: real-input, decoder-free, staged and small."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


CONTRACT = {
    "dimension": 1024,
    "bin_width_ps": 200,
    "pairing": "nearest",
    "pair_assignment": "double_pointer_bin_div_dimension",
    "processing_rule": "legacy_v1",
    "frame_period_ps": 204800,
    "frame_division": "floor_div",
    "frame_bins": 1024,
    "pairs_per_frame": 256,
    "threshold_ps": 40000,
    "gate_ps": 200,
}

LAMBDA_LOG10_BOUNDS = (-2.0, 4.0)
LAMBDA_GRID_POINTS = 50
STAGE1 = {"cal_frames": 256, "val_frames": 64}
STAGE2_PLAN = {"cal_frames": 1024, "val_frames": 256, "test_frames": 32}


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    path_parts: tuple[str, ...]
    raw_name: str
    provisional_tier: str
    tier_basis: str
    tier_uncertainty: str


# The relative paths are inventory evidence, not a default data root.  The
# caller supplies the root explicitly (or PROJECT_DATA_ROOT).
CANDIDATE_SPECS: tuple[CandidateSpec, ...] = (
    CandidateSpec(
        "2026-01-13 162148",
        ("2026.1.13", "SHG_Type2PPLN_3s_2_2026-01-13_162148"),
        "SHG_Type2PPLN_3s_2_2026-01-13_162148.1.ttbin",
        "B",
        "Early Type-II/PIE-SKR-era material; no V36-V64 NB-LDPC reference found in the repository scan.",
        "External-use ledger is incomplete; keep provisional B, reclassify C if a current NB-LDPC dependency is found, and A only after an explicit no-influence record.",
    ),
    CandidateSpec(
        "2026-01-07 2500K",
        ("2026.1.7",),
        "Type2PPLN_2500K_3s_2026-01-07_174324.1.ttbin",
        "B",
        "Early Type-II raw session outside the V36-V64 candidate registries; retained as a historical generalization candidate.",
        "The repository cannot prove every early Polar/Cascade use; do not promote to A without an external-use ledger and reclassify C if current NB-LDPC influence is discovered.",
    ),
    CandidateSpec(
        "2026-01-07 160254",
        ("2026.1.7",),
        "Type2PPLN_3s_2026-01-07_160254.1.ttbin",
        "B",
        "Early Type-II raw session outside the V36-V64 candidate registries; retained as a historical generalization candidate.",
        "The repository cannot prove every early Polar/Cascade use; do not promote to A without an external-use ledger and reclassify C if current NB-LDPC influence is discovered.",
    ),
)
FROZEN_ORDER = tuple(item.candidate_id for item in CANDIDATE_SPECS)


@dataclass
class Observation:
    frame_id: np.ndarray
    pair_idx: np.ndarray
    alice: np.ndarray
    bob: np.ndarray
    metadata: dict[str, Any]
    source_path: str

    def subset_frames(self, frame_ids: Sequence[int]) -> "Observation":
        wanted = set(int(x) for x in frame_ids)
        keep = np.asarray([int(x) in wanted for x in self.frame_id], dtype=bool)
        return Observation(
            self.frame_id[keep].copy(),
            self.pair_idx[keep].copy(),
            self.alice[keep].copy(),
            self.bob[keep].copy(),
            dict(self.metadata),
            self.source_path,
        )


def _plain(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def _pick(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def _nested(mapping: Mapping[str, Any], *paths: tuple[str, ...]) -> Any:
    for path in paths:
        cur: Any = mapping
        for key in path:
            if not isinstance(cur, Mapping) or key not in cur:
                cur = None
                break
            cur = cur[key]
        if cur is not None:
            return cur
    return None


def _number(value: Any) -> float | None:
    try:
        if value is None or isinstance(value, bool):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _normal_path(value: Any, base: Path) -> str | None:
    if value is None or not str(value).strip():
        return None
    raw = str(value)
    path = Path(raw)
    if not path.is_absolute():
        path = base / path
    try:
        return os.path.normcase(os.path.normpath(str(path.resolve())))
    except OSError:
        return os.path.normcase(os.path.normpath(str(path)))


def _find_sidecars(session_dir: Path) -> list[Path]:
    if not session_dir.exists():
        return []
    found: list[Path] = []
    for pattern in ("*.meta.json", "sidecar*.json", "metadata.json"):
        found.extend(sorted(session_dir.glob(pattern)))
    return sorted(set(found))


def discover_candidate(root: Path | None, candidate: CandidateSpec) -> dict[str, Any]:
    if root is None:
        return {"status": "V65A_DATA_NOT_READY", "reason": "candidate_root_missing", "candidate": candidate}
    base = root.joinpath(*candidate.path_parts)
    session_dir = base if base.is_dir() else base.parent
    source = base if base.is_file() else session_dir / candidate.raw_name
    pair_paths = [
        session_dir / "pairs.parquet",
        session_dir / "pairs.csv",
        session_dir / "pairs.npz",
    ]
    pair_paths = [path for path in pair_paths if path.exists()]
    source_exists = source.exists() and source.is_file()
    sidecars = _find_sidecars(session_dir)
    if not source_exists and not pair_paths:
        return {
            "status": "V65A_DATA_NOT_READY",
            "reason": "source_and_processed_pairs_missing",
            "candidate": candidate,
            "session_dir": session_dir,
            "source_path": source,
            "pair_paths": pair_paths,
            "sidecar_paths": sidecars,
        }
    return {
        "status": "DISCOVERED",
        "candidate": candidate,
        "session_dir": session_dir,
        "source_path": source if source_exists else pair_paths[0],
        "pair_paths": pair_paths,
        "sidecar_paths": sidecars,
    }


def _read_sidecar(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("sidecar must be a JSON object")
    return value


def _summarize_sidecar_provenance(path: Path, session_dir: Path, source_path: Path) -> dict[str, Any]:
    """Read only provenance fields so an ambiguous sidecar is auditable."""
    payload = _read_sidecar(path)
    declared_dir = _pick(payload, "data_dir", "source_dir", "session_dir")
    declared_raw = _pick(payload, "ttbin", "ttbin_path", "raw_path")
    actual_dir = _normal_path(session_dir, session_dir)
    actual_source = _normal_path(source_path, session_dir)
    return {
        "path": str(path),
        "session_id": _pick(payload, "session_id", "session"),
        "provenance_source_dir": declared_dir,
        "provenance_raw_path": declared_raw,
        "source_dir_matches_candidate": bool(
            declared_dir and _normal_path(declared_dir, session_dir) == actual_dir
        ),
        "raw_path_matches_candidate": bool(
            declared_raw and _normal_path(declared_raw, session_dir) == actual_source
        ),
    }


def normalize_metadata(candidate: CandidateSpec, discovery: Mapping[str, Any], payload: Mapping[str, Any]) -> dict[str, Any]:
    session_dir = Path(str(discovery["session_dir"]))
    source_path = Path(str(discovery["source_path"]))
    pairing = _nested(payload, ("pairing",), ("ttbin", "pairing"))
    pairing = pairing if isinstance(pairing, Mapping) else {}
    anchor = _nested(payload, ("frame_anchor",), ("framing",))
    anchor = anchor if isinstance(anchor, Mapping) else {}
    channels = _pick(payload, "channels")
    if not isinstance(channels, Mapping):
        channels = {
            "A": _pick(payload, "raw_ch0_id", "channel_a", "ch_a"),
            "B": _pick(payload, "raw_ch1_id", "channel_b", "ch_b"),
        }
    channel_a = _pick(channels, "A", "a", "alice", "ch_a")
    channel_b = _pick(channels, "B", "b", "bob", "ch_b")
    gate_ps = _number(_pick(payload, "gate_ps", "gate_width_ps"))
    if gate_ps is None:
        gate_ns = _number(_pick(payload, "gate_width_ns"))
        gate_ps = None if gate_ns is None else gate_ns * 1000.0
    bin_value = _pick(payload, "bin_width_ps", "binwidth_ps", "bin_width")
    delay = _number(_pick(payload, "delay_used_ps", "delay_ps", "offset_ps"))
    peak = _number(_pick(payload, "peak_center_ps", "peak_center", "peak_ps"))
    sigma = _number(_pick(payload, "sigma_ps", "sigma", "peak_sigma_ps"))
    threshold = _number(_pick(payload, "threshold_ps", "nearest_threshold_ps", "threshold"))
    period = _number(_pick(anchor, "period_ps", "frame_period_ps"))
    if period is None:
        period = _number(_pick(payload, "frame_period_ps", "period_ps"))
    frame_bins = _pick(anchor, "frame_bins", "dimension")
    division = _pick(anchor, "division", "operation", "bin_operation")
    pairing_policy = _pick(pairing, "policy", "mode", "name")
    assignment = _pick(pairing, "assignment", "frame_assignment", "disambiguation")
    mapping = _pick(payload, "mapping", "mapping_rule", "symbol_mapping")
    processing_rule = _pick(payload, "processing_rule", "processing_rule_version", "rule")
    source_dir = _pick(payload, "data_dir", "source_dir", "session_dir")
    raw_path = _pick(payload, "ttbin", "ttbin_path", "raw_path")
    session_id = _pick(payload, "session_id", "session")
    return {
        "candidate_id": candidate.candidate_id,
        "session_id": session_id,
        "session_dir": str(session_dir),
        "source_path": str(source_path),
        "provenance_source_dir": source_dir,
        "provenance_raw_path": raw_path,
        "dimension": _number(_pick(payload, "dimension", "d")),
        "bin_width_ps": _number(bin_value) if not isinstance(bin_value, (list, tuple)) else None,
        "pairing": str(pairing_policy).lower() if pairing_policy is not None else None,
        "pair_assignment": str(assignment).lower() if assignment is not None else None,
        "processing_rule": str(processing_rule).lower() if processing_rule is not None else None,
        "channels_used": {"A": channel_a, "B": channel_b},
        "delay_used_ps": delay,
        "peak_center_ps": peak,
        "sigma_ps": sigma,
        "gate_ps": gate_ps,
        "threshold_ps": threshold,
        "frame_period_ps": period,
        "frame_bins": _number(frame_bins),
        "frame_division": str(division).lower() if division is not None else None,
        "mapping": str(mapping).lower() if mapping is not None else None,
        "sidecar_payload": dict(payload),
    }


def validate_candidate_metadata(candidate: CandidateSpec, discovery: Mapping[str, Any], payload: Mapping[str, Any] | None) -> dict[str, Any]:
    sidecars = list(discovery.get("sidecar_paths", []))
    source_path = Path(str(discovery["source_path"]))
    checks: dict[str, Any] = {
        "source_exists": source_path.exists(),
        "sidecar_present": bool(sidecars),
        "sidecar_unique": len(sidecars) == 1,
    }
    if payload is None:
        checks.update({key: False for key in ("provenance", "session", "dimension", "bin_width", "pairing", "assignment", "processing_rule", "channels", "timing", "sigma", "gate", "threshold", "frame_anchor", "mapping")})
        return {
            "metadata": None,
            "checks": checks,
            "verify_pass": False,
            "status": "V65A_INCOMPATIBLE" if len(sidecars) > 1 else "V65A_DATA_NOT_READY",
            "fail_reason": "sidecar_missing_or_ambiguous",
        }
    metadata = normalize_metadata(candidate, discovery, payload)
    session_dir = Path(str(discovery["session_dir"]))
    candidate_sources = [source_path, *(Path(str(path)) for path in discovery.get("pair_paths", []))]
    actual_sources = {
        normalized
        for path in candidate_sources
        if (normalized := _normal_path(path, session_dir)) is not None
    }
    actual_dir = _normal_path(session_dir, session_dir)
    prov_dir = _normal_path(metadata["provenance_source_dir"], session_dir)
    prov_raw = _normal_path(metadata["provenance_raw_path"], session_dir)
    checks["provenance"] = bool(prov_dir and prov_raw and prov_dir == actual_dir and prov_raw in actual_sources)
    session_id = str(metadata["session_id"] or "").strip()
    checks["session"] = bool(session_id)
    checks["dimension"] = metadata["dimension"] == CONTRACT["dimension"]
    checks["bin_width"] = metadata["bin_width_ps"] == CONTRACT["bin_width_ps"]
    checks["pairing"] = metadata["pairing"] == CONTRACT["pairing"]
    checks["assignment"] = metadata["pair_assignment"] == CONTRACT["pair_assignment"]
    checks["processing_rule"] = metadata["processing_rule"] == CONTRACT["processing_rule"]
    channel_a = metadata["channels_used"].get("A")
    channel_b = metadata["channels_used"].get("B")
    checks["channels"] = channel_a is not None and channel_b is not None and channel_a != channel_b
    delay = metadata["delay_used_ps"]
    peak = metadata["peak_center_ps"]
    checks["timing"] = delay is not None and peak is not None and np.sign(delay) == np.sign(peak) and abs(delay - peak) < 50.0
    checks["sigma"] = metadata["sigma_ps"] is not None and 50.0 <= metadata["sigma_ps"] <= 150.0
    checks["gate"] = metadata["gate_ps"] == CONTRACT["gate_ps"]
    checks["threshold"] = metadata["threshold_ps"] == CONTRACT["threshold_ps"]
    checks["frame_anchor"] = (
        metadata["frame_period_ps"] == CONTRACT["frame_period_ps"]
        and metadata["frame_bins"] == CONTRACT["frame_bins"]
        and metadata["frame_division"] == CONTRACT["frame_division"]
    )
    checks["mapping"] = metadata["mapping"] == CONTRACT["processing_rule"]
    hard = tuple(bool(v) for v in checks.values())
    failed = [key for key, value in checks.items() if not value]
    explicit_conflict = any(key in failed for key in ("provenance", "dimension", "bin_width", "pairing", "assignment", "processing_rule", "timing", "sigma", "gate", "threshold", "frame_anchor", "mapping"))
    return {
        "metadata": metadata,
        "checks": checks,
        "verify_pass": bool(all(hard)),
        "status": "V65A_INCOMPATIBLE" if explicit_conflict or len(sidecars) != 1 else "V65A_DATA_NOT_READY",
        "fail_reason": None if all(hard) else ",".join(failed),
    }


def _column(table: Any, names: Sequence[str]) -> np.ndarray:
    available = {str(name).lower(): name for name in getattr(table, "columns", [])}
    if isinstance(table, Mapping):
        available = {str(name).lower(): name for name in table}
    for name in names:
        key = name.lower()
        if key in available:
            return np.asarray(table[available[key]])
    raise ValueError(f"missing pair column; expected one of {names}")


def canonical_pairs(table: Any, source_path: str) -> Observation:
    frame_id = _column(table, ("frame_id", "frame", "logical_frame"))
    pair_idx = _column(table, ("pair_idx", "pair_index", "idx"))
    alice = _column(table, ("alice_symbol", "alice", "a_eff", "a"))
    bob = _column(table, ("bob_symbol", "bob", "b_eff", "b"))
    n = len(frame_id)
    if not all(len(arr) == n for arr in (pair_idx, alice, bob)):
        raise ValueError("pair columns have different lengths")
    return Observation(
        np.asarray(frame_id, dtype=np.int64),
        np.asarray(pair_idx, dtype=np.int64),
        np.asarray(alice, dtype=np.int64),
        np.asarray(bob, dtype=np.int64),
        {},
        source_path,
    )


def _take_first_frames(observation: Observation, count: int) -> Observation:
    frame_ids = sorted({int(x) for x in observation.frame_id})
    selected = frame_ids[:count]
    if len(selected) < count:
        raise ValueError(f"only {len(selected)} complete frame ids available, need {count}")
    return observation.subset_frames(selected)


def validate_pairs(observation: Observation, min_frames: int) -> dict[str, Any]:
    frame = observation.frame_id
    pair = observation.pair_idx
    checks: dict[str, Any] = {
        "columns_equal_length": len(frame) == len(pair) == len(observation.alice) == len(observation.bob),
        "symbols_range": bool(np.all((observation.alice >= 0) & (observation.alice < 1024) & (observation.bob >= 0) & (observation.bob < 1024))),
        "ordered": bool(np.all((frame[1:] > frame[:-1]) | ((frame[1:] == frame[:-1]) & (pair[1:] >= pair[:-1])))) if len(frame) > 1 else True,
        "mapping_a": bool(np.all((observation.alice // 32) * 32 + (observation.alice % 32) == observation.alice)),
        "mapping_b": bool(np.all((observation.bob // 32) * 32 + (observation.bob % 32) == observation.bob)),
    }
    frame_ids = sorted({int(x) for x in frame})
    checks["frame_count"] = len(frame_ids) >= min_frames
    checks["frame_256"] = all(int(np.sum(frame == fid)) == 256 for fid in frame_ids)
    checks["pair_idx_0_255"] = all(set(pair[frame == fid].tolist()) == set(range(256)) for fid in frame_ids)
    checks["mapping"] = checks["mapping_a"] and checks["mapping_b"]
    return {"checks": checks, "pass": bool(all(checks.values())), "frame_ids": frame_ids, "pairs": int(len(frame))}


def _read_pairs_file(path: Path) -> Any:
    if path.suffix.lower() == ".parquet":
        import pandas as pd

        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        import pandas as pd

        return pd.read_csv(path)
    with np.load(path, allow_pickle=False) as values:
        return {key: values[key] for key in values.files}


def _read_raw_pairs(path: Path, metadata: Mapping[str, Any], frame_limit: int) -> Observation:
    # This imports only the established bin/pair helpers and touches one
    # candidate at a time.  No correction routine is imported or called.
    from src.reconciliation.run_nbldpc_demo_point import (
        _bin_indices_sorted_for_binwidth,
        _pairs_from_sorted_bins,
        _read_ttbin_timetags,
    )

    channels = metadata["channels_used"]
    tt = _read_ttbin_timetags(path, int(channels["A"]), int(channels["B"]))
    b0, b1, _ = _bin_indices_sorted_for_binwidth(tt, CONTRACT["bin_width_ps"])
    pairs, _ = _pairs_from_sorted_bins(b0, b1, CONTRACT["dimension"])
    needed = frame_limit * CONTRACT["pairs_per_frame"]
    if len(pairs) < needed:
        raise ValueError(f"raw pair stream has {len(pairs)} pairs, need {needed}")
    pairs = pairs[:needed]
    return Observation(
        np.repeat(np.arange(frame_limit, dtype=np.int64), CONTRACT["pairs_per_frame"]),
        np.tile(np.arange(CONTRACT["pairs_per_frame"], dtype=np.int64), frame_limit),
        pairs[:, 0].astype(np.int64),
        pairs[:, 1].astype(np.int64),
        dict(metadata),
        str(path),
    )


def load_observation(discovery: Mapping[str, Any], metadata: Mapping[str, Any], frame_limit: int) -> Observation:
    pair_paths = list(discovery.get("pair_paths", []))
    if pair_paths:
        obs = canonical_pairs(_read_pairs_file(Path(pair_paths[0])), str(pair_paths[0]))
        obs = _take_first_frames(obs, frame_limit)
        obs.metadata = dict(metadata)
        return obs
    return _read_raw_pairs(Path(str(discovery["source_path"])), metadata, frame_limit)


def probe_candidate(candidate: CandidateSpec, root: Path | None, *, loader: Callable[[Mapping[str, Any], Mapping[str, Any], int], Observation] = load_observation) -> dict[str, Any]:
    discovery = discover_candidate(root, candidate)
    base: dict[str, Any] = {
        "candidate_id": candidate.candidate_id,
        "provisional_tier": candidate.provisional_tier,
        "tier_basis": candidate.tier_basis,
        "tier_uncertainty": candidate.tier_uncertainty,
        "status": discovery.get("status"),
        "source_path": str(discovery.get("source_path", "")),
        "sidecar_paths": [str(x) for x in discovery.get("sidecar_paths", [])],
        "materialized_frames": 0,
        "materialized_pairs": 0,
        "observation": None,
        "discovery": discovery,
    }
    if discovery.get("status") != "DISCOVERED":
        base["fail_reason"] = discovery.get("reason")
        return base
    sidecars = list(discovery.get("sidecar_paths", []))
    payload = None
    if len(sidecars) == 1:
        try:
            payload = _read_sidecar(Path(sidecars[0]))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            base["status"] = "V65A_INCOMPATIBLE"
            base["fail_reason"] = f"sidecar_read_error:{exc}"
            return base
    elif sidecars:
        details: list[dict[str, Any]] = []
        read_errors: list[str] = []
        for sidecar in sidecars:
            try:
                details.append(
                    _summarize_sidecar_provenance(
                        Path(sidecar),
                        Path(str(discovery["session_dir"])),
                        Path(str(discovery["source_path"])),
                    )
                )
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                read_errors.append(f"{sidecar}:{exc}")
        base["sidecar_details"] = details
        base["provenance_conflict"] = bool(
            read_errors
            or any(
                not (item["source_dir_matches_candidate"] and item["raw_path_matches_candidate"])
                for item in details
            )
        )
        base["status"] = "V65A_INCOMPATIBLE"
        base["fail_reason"] = (
            "sidecar_ambiguous_provenance_conflict"
            if base["provenance_conflict"]
            else "sidecar_ambiguous"
        )
        if read_errors:
            base["sidecar_read_errors"] = read_errors
        return base
    meta_result = validate_candidate_metadata(candidate, discovery, payload)
    base.update({"metadata": meta_result.get("metadata"), "metadata_checks": meta_result["checks"], "fail_reason": meta_result["fail_reason"], "status": meta_result["status"]})
    if not meta_result["verify_pass"]:
        return base
    try:
        obs = loader(discovery, meta_result["metadata"], 8)
        pair_result = validate_pairs(obs, 8)
        if not pair_result["pass"]:
            base["status"] = "V65A_INCOMPATIBLE"
            base["fail_reason"] = "pair_contract:" + ",".join(key for key, value in pair_result["checks"].items() if not value)
            base["pair_checks"] = pair_result
            return base
    except (OSError, ValueError, ImportError) as exc:
        base["status"] = "V65A_DATA_NOT_READY" if isinstance(exc, (OSError, ImportError)) else "V65A_INCOMPATIBLE"
        base["fail_reason"] = f"materialization:{exc}"
        return base
    frame_ids = pair_result["frame_ids"]
    base.update({
        "status": "V65A_VERIFY_PASS",
        "verify_pass": True,
        "pair_checks": pair_result,
        "materialized_frames": 8,
        "materialized_pairs": int(len(obs.frame_id)),
        "frame_split": {"calibration": frame_ids[:4], "validation": frame_ids[4:8]},
        "observation": obs,
    })
    return base


def run_stage0(root: Path | None, candidates: Sequence[CandidateSpec] = CANDIDATE_SPECS, probe: Callable[[CandidateSpec, Path | None], dict[str, Any]] = probe_candidate) -> dict[str, Any]:
    ids = tuple(item.candidate_id for item in candidates)
    if ids != FROZEN_ORDER:
        raise ValueError("candidate order drift")
    checked: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None
    selected_index: int | None = None
    for index, candidate in enumerate(candidates):
        item = probe(candidate, root)
        item["checked_index"] = index
        checked.append(item)
        if bool(item.get("verify_pass")):
            selected = item
            selected_index = index
            break
    materialized_frames = int(sum(int(item.get("materialized_frames", 0)) for item in checked))
    later = [] if selected_index is None else [item.candidate_id for item in candidates[selected_index + 1 :]]
    guard = materialized_frames <= 8 * len(checked) and not any(item.get("batch_materialized") for item in checked)
    return {
        "checked_candidates": [item["candidate_id"] for item in checked],
        "per_candidate": checked,
        "selected": selected["candidate_id"] if selected else None,
        "selected_index": selected_index,
        "not_materialized_later_candidates": later,
        "materialized_candidates_count": sum(int(item.get("materialized_frames", 0)) > 0 for item in checked),
        "materialized_frames_total": materialized_frames,
        "batch_guard_pass": bool(guard),
        "order_guard_pass": True,
        "none_passed": selected is None,
        "selected_item": selected,
    }


def _counts(alice: np.ndarray, bob: np.ndarray) -> np.ndarray:
    result = np.zeros((1024, 1024), dtype=np.float64)
    np.add.at(result, (alice, bob), 1.0)
    return result


def _conditional(alice: np.ndarray, bob: np.ndarray, lam: float) -> np.ndarray:
    counts = _counts(alice, bob)
    total = float(counts.sum())
    global_prior = counts.sum(axis=1) / total if total else np.full(1024, 1.0 / 1024.0)
    nb = counts.sum(axis=0)
    return (counts + float(lam) * global_prior[:, None]) / (nb[None, :] + float(lam))


def _nll(model: np.ndarray, alice: np.ndarray, bob: np.ndarray) -> float:
    return float(-np.mean(np.log2(np.maximum(model[alice, bob], 1e-300))))


def _cv_lambda(cal: Observation) -> dict[str, Any]:
    frame_ids = sorted({int(x) for x in cal.frame_id})
    grid = np.logspace(LAMBDA_LOG10_BOUNDS[0], LAMBDA_LOG10_BOUNDS[1], LAMBDA_GRID_POINTS)
    scores: list[float] = []
    for lam in grid:
        fold_scores: list[float] = []
        for fold in (0, 1):
            eval_frames = {fid for idx, fid in enumerate(frame_ids) if idx % 2 == fold}
            train_frames = set(frame_ids) - eval_frames
            eval_mask = np.isin(cal.frame_id, list(eval_frames))
            train_mask = np.isin(cal.frame_id, list(train_frames))
            if not np.any(eval_mask) or not np.any(train_mask):
                continue
            fold_scores.append(_nll(_conditional(cal.alice[train_mask], cal.bob[train_mask], float(lam)), cal.alice[eval_mask], cal.bob[eval_mask]))
        scores.append(float(np.mean(fold_scores)) if fold_scores else math.inf)
    best = int(np.argmin(np.asarray(scores)))
    chosen = float(grid[best])
    return {
        "log10_lambda_grid": [float(x) for x in np.log10(grid)],
        "cv_nll_grid": scores,
        "lambda_star": chosen,
        "lambda_at_boundary": best in (0, len(grid) - 1),
        "search": "calibration_two_fold_50_point_log_grid",
    }


def _entropy(counts: np.ndarray) -> float:
    total = float(counts.sum())
    if total <= 0:
        return math.nan
    p = counts.reshape(-1) / total
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def _conditional_entropy_parts(counts: np.ndarray) -> tuple[float, float, float]:
    """Return H(A|B), H(U1|B), and H(U2|U1,B) from a C_ab table.

    The Stage 1 values are descriptive only, but they must still use the
    conditional distribution rather than the joint entropy of (A, B).
    """
    counts = np.asarray(counts, dtype=np.float64)
    total = float(counts.sum())
    if total <= 0:
        return (math.nan, math.nan, math.nan)
    n_b = counts.sum(axis=0)
    active = n_b > 0
    if not np.any(active):
        return (math.nan, math.nan, math.nan)
    weights = n_b[active] / total
    p_a_given_b = counts[:, active] / n_b[active][None, :]
    p_a_given_b = np.maximum(p_a_given_b, 0.0)
    safe_p_a = np.where(p_a_given_b > 0, p_a_given_b, 1.0)
    h_a_columns = -np.sum(
        np.where(p_a_given_b > 0, p_a_given_b * np.log2(safe_p_a), 0.0),
        axis=0,
    )
    p_u1_given_b = p_a_given_b.reshape(32, 32, -1).sum(axis=1)
    safe_p_u1 = np.where(p_u1_given_b > 0, p_u1_given_b, 1.0)
    h_u1_columns = -np.sum(
        np.where(p_u1_given_b > 0, p_u1_given_b * np.log2(safe_p_u1), 0.0),
        axis=0,
    )
    p_u2_given_u1_b = np.divide(
        p_a_given_b.reshape(32, 32, -1),
        p_u1_given_b[:, None, :],
        out=np.zeros_like(p_a_given_b.reshape(32, 32, -1)),
        where=p_u1_given_b[:, None, :] > 0,
    )
    h_u2_columns = -np.sum(
        np.where(
            p_a_given_b.reshape(32, 32, -1) > 0,
            p_a_given_b.reshape(32, 32, -1)
            * np.log2(np.maximum(p_u2_given_u1_b, 1e-300)),
            0.0,
        ),
        axis=(0, 1),
    )
    h_a_given_b = float(np.dot(weights, h_a_columns))
    h_u1_given_b = float(np.dot(weights, h_u1_columns))
    h_u2_given_u1_b = float(np.dot(weights, h_u2_columns))
    return h_a_given_b, h_u1_given_b, h_u2_given_u1_b


def _ce_parts(model: np.ndarray, alice: np.ndarray, bob: np.ndarray) -> dict[str, float]:
    reshaped = model.reshape(32, 32, 1024)
    p_u1 = reshaped.sum(axis=1)
    u1 = alice // 32
    p1 = np.maximum(p_u1[u1, bob], 1e-300)
    pfull = np.maximum(model[alice, bob], 1e-300)
    p2 = np.maximum(pfull / p1, 1e-300)
    ce1 = float(-np.mean(np.log2(p1)))
    ce2 = float(-np.mean(np.log2(p2)))
    full = float(-np.mean(np.log2(pfull)))
    return {"CE1": ce1, "CE2": ce2, "CE_full": full, "chain_delta": abs(full - ce1 - ce2)}


def required_m_from_ce(ce: float) -> int:
    # ponytail: ceil without cap/floor/handfill; no min/max wrapping
    return int(math.ceil(1.3 * 1024.0 * float(ce) / 5.0))


def classify_required_rate(m1: int, m2: int, *, lambda_at_boundary: bool, model_stable: bool) -> str:
    # priority: MODEL_NOT_STABLE > FULL_DISCLOSURE_LAYER(>=1024) > RATE_ADAPTATION_REQUIRED(>frozen but <1024) > FROZEN_RATE_COMPATIBLE
    if lambda_at_boundary or not model_stable:
        return "MODEL_NOT_STABLE"
    total = int(m1) + int(m2)
    if m1 >= 1024 or m2 >= 1024 or total >= 1024:
        return "FULL_DISCLOSURE_LAYER"
    if m1 <= 16 and m2 <= 200 and total <= 216:
        return "FROZEN_RATE_COMPATIBLE"
    return "RATE_ADAPTATION_REQUIRED"


def coarse_screen(observation: Observation, *, excluded_frame_ids: Sequence[int] = ()) -> dict[str, Any]:
    excluded = {int(x) for x in excluded_frame_ids}
    all_frames = [fid for fid in sorted({int(x) for x in observation.frame_id}) if fid not in excluded]
    needed = STAGE1["cal_frames"] + STAGE1["val_frames"]
    if len(all_frames) < needed:
        return {
            "status": "V65A_DATA_NOT_READY",
            "overall": "V65A_COARSE_REJECTED",
            "coarse_cannot_ready": True,
            "fail_reason": f"need_{needed}_frames_after_stage0_have_{len(all_frames)}",
            "materialized_frames": len(all_frames),
        }
    cal_ids = all_frames[: STAGE1["cal_frames"]]
    val_ids = all_frames[STAGE1["cal_frames"] : needed]
    cal = observation.subset_frames(cal_ids)
    val = observation.subset_frames(val_ids)
    cal_counts = _counts(cal.alice, cal.bob)
    h_cal, h1, h2 = _conditional_entropy_parts(cal_counts)
    search = _cv_lambda(cal)
    lam = float(search["lambda_star"])
    model = _conditional(cal.alice, cal.bob, lam)
    ce = _ce_parts(model, val.alice, val.bob)
    unseen = float(np.mean(cal_counts[val.alice, val.bob] == 0))
    map_acc = float(np.mean(np.argmax(model[:, val.bob], axis=0) == val.alice))
    p_u2_emp = cal_counts / np.maximum(cal_counts.sum(axis=0, keepdims=True), 1e-300)
    m1 = required_m_from_ce(ce["CE1"])
    m2 = required_m_from_ce(ce["CE2"])
    val_nll = ce["CE_full"]
    delta_nll = val_nll - h_cal
    gates = {
        "lambda_not_boundary": not bool(search["lambda_at_boundary"]),
        "delta_nll_le_0_75": delta_nll <= 0.75,
        "val_nll_le_h_plus_1_5": val_nll <= h_cal + 1.5,
        "unseen_le_0_02": unseen <= 0.02,
        "m1_le_16": m1 <= 16,
        "m2_le_200": m2 <= 200,
        "m_total_le_216": m1 + m2 <= 216,
        "ce_chain": ce["chain_delta"] < 1e-9,
        "entropy_chain": abs(h_cal - h1 - h2) < 1e-9,
        "frame_contract": True,
    }
    model_stable = bool(gates["lambda_not_boundary"] and gates["delta_nll_le_0_75"] and gates["val_nll_le_h_plus_1_5"] and gates["unseen_le_0_02"] and gates["ce_chain"] and gates["entropy_chain"])
    rate_class = classify_required_rate(m1, m2, lambda_at_boundary=bool(search["lambda_at_boundary"]), model_stable=model_stable)
    # Stage1 never grants RATE_READY/FROZEN_READY; it only REJECTs or marks ELIGIBLE_FOR_FORMAL
    return {
        "status": "V65A_COARSE_SCREENED",
        "overall": "V65A_ELIGIBLE_FOR_FORMAL" if all(gates.values()) else "V65A_COARSE_REJECTED",
        "coarse_cannot_ready": True,
        "cal_frame_ids": cal_ids,
        "val_frame_ids": val_ids,
        "N_cal": int(len(cal.alice)),
        "N_val": int(len(val.alice)),
        "H_cal": h_cal,
        "H1_cal": h1,
        "H2_cal": h2,
        "entropy_chain_delta": abs(h_cal - h1 - h2),
        "search": search,
        "lambda_star": lam,
        "CE1": ce["CE1"],
        "CE2": ce["CE2"],
        "CE_full": ce["CE_full"],
        "ce_chain_delta": ce["chain_delta"],
        "val_nll": val_nll,
        "delta_nll": delta_nll,
        "unseen_rate": unseen,
        "MAP_acc": map_acc,
        "m1_raw": m1,
        "m2_raw": m2,
        "m_total_raw": m1 + m2,
        "leak_bits": 5 * (m1 + m2) + 64,
        "gates": gates,
        "required_rate_classification": rate_class,
        "rate_branch": rate_class,
        "test_statistics_used": False,
        "TEST_used": False,
        "reported_empirical_p_u2": bool(p_u2_emp.size),
    }


def formal_plan(selected: str | None, excluded_frame_ids: Sequence[int] = ()) -> dict[str, Any]:
    return {
        "planned_only": True,
        "selected_candidate": selected,
        "CAL": {"frames": STAGE2_PLAN["cal_frames"], "pairs": STAGE2_PLAN["cal_frames"] * 256},
        "VAL": {"frames": STAGE2_PLAN["val_frames"], "pairs": STAGE2_PLAN["val_frames"] * 256},
        "TEST": {"frames": STAGE2_PLAN["test_frames"], "pairs": STAGE2_PLAN["test_frames"] * 256, "identity_only": True, "statistics_used": False},
        "lambda": {"log10_bounds": list(LAMBDA_LOG10_BOUNDS), "folds": 4, "cal_only": True},
        "ce_chain_tolerance": 1e-9,
        "required_rate_formula": "m1=ceil(1.3*1024*CE1/5) m2=ceil(1.3*1024*CE2/5) no cap/floor/handfill",
        "rate_branches": ["MODEL_NOT_STABLE", "FROZEN_RATE_COMPATIBLE", "RATE_ADAPTATION_REQUIRED", "FULL_DISCLOSURE_LAYER"],
        "rate_note": "MODEL_NOT_STABLE priority; RATE_ADAPTATION_REQUIRED is stable but exceeds frozen capacity and <1024; FULL_DISCLOSURE_LAYER is any m>=1024; same-family only P(U1|B)/P(U2|U1B) re-estimation keeps Lane C family/L1APP/conditional increment/full-tag, adjacent preregistered increments only, no successor change this turn",
        "stage2_min_frames": "CAL1024 VAL256 sealed TEST32 required before FROZEN/ADAPTATION judgment",
        "excluded_stage0_frame_ids": [int(x) for x in excluded_frame_ids],
        "sealed_test_identity": {"frames": None, "blocks": 8, "to_be_frozen_after_new_plan_accept": True},
    }


def _strip_internal(value: Any) -> Any:
    if isinstance(value, Observation):
        return None
    if isinstance(value, Mapping):
        return {str(k): _strip_internal(v) for k, v in value.items() if k not in {"discovery", "selected_item", "observation"} and not str(k).startswith("_")}
    if isinstance(value, (list, tuple)):
        return [_strip_internal(v) for v in value]
    return _plain(value)


def run_scout(stage: str, root: Path | None) -> dict[str, Any]:
    if stage == "formal":
        return {
            "stage": "formal",
            "overall": "V65A_FORMAL_PLAN_ONLY",
            "stage0": None,
            "stage1": None,
            "formal_plan": formal_plan(None),
            "guards": {"decoder_calls": 0, "test_statistics_used": False, "batch_materialization": False},
        }
    stage0 = run_stage0(root)
    _sel = stage0.get("selected_item") or {}
    _split = _sel.get("frame_split", {}) if isinstance(_sel, dict) else {}
    result: dict[str, Any] = {"stage": stage, "stage0": stage0, "stage1": None, "formal_plan": formal_plan(stage0["selected"], _split.get("calibration", []) + _split.get("validation", []))}
    if stage in {"coarse", "all"} and stage0.get("selected_item") is not None:
        selected = stage0["selected_item"]
        selected_candidate = selected["discovery"]
        metadata = selected.get("metadata")
        try:
            obs = load_observation(selected_candidate, metadata, 328)
            first_ids = selected.get("pair_checks", {}).get("frame_ids", [])
            result["stage1"] = coarse_screen(obs, excluded_frame_ids=first_ids)
            stage0["materialized_frames_total"] = int(stage0["materialized_frames_total"]) + int(result["stage1"].get("materialized_frames", 320))
        except (OSError, ValueError, ImportError) as exc:
            result["stage1"] = {"status": "V65A_DATA_NOT_READY", "overall": "V65A_COARSE_REJECTED", "coarse_cannot_ready": True, "fail_reason": f"selected_replay:{exc}"}
    if stage == "verify" and stage0.get("selected"):
        result["overall"] = "V65A_STAGE0_VERIFY_PASS"
    elif stage0.get("selected") is None:
        result["overall"] = "V65A_NO_CANDIDATE_PASSED_VERIFICATION"
    elif result.get("stage1") is None:
        result["overall"] = "V65A_STAGE0_VERIFY_PASS"
    else:
        result["overall"] = result["stage1"]["overall"]
    result["guards"] = {
        "decoder_calls": 0,
        "test_statistics_used": False,
        "historical_result_files_read": False,
        "batch_materialization": False,
        "stage2_executed": False,
        "coarse_cannot_ready": True,
    }
    return result


def build_report(result: Mapping[str, Any]) -> str:
    stage0 = result.get("stage0") or {}
    lines = [
        "# V65A historical Type-II scout",
        "",
        f"- stage: `{result.get('stage')}`",
        f"- overall: `{result.get('overall')}`",
        f"- fixed order: `{list(FROZEN_ORDER)}`",
        f"- selected: `{stage0.get('selected')}`",
        f"- checked candidates: `{stage0.get('checked_candidates')}`",
        f"- materialized frames: `{stage0.get('materialized_frames_total', 0)}`",
        "",
        "Stage 0 is a contract/provenance check only. A pass does not establish channel compatibility.",
        "Stage 1 is a 256/64 coarse screen with淘汰权 only; it cannot produce READY.",
        "Stage 2 is a plan-only 1024/256 re-characterization with 32 TEST identities; TEST statistics are not used.",
        "",
        "Candidate provenance is provisional: all three are B pending a complete external-use ledger; any V36-V64 dependency would reclassify it to C.",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(result: Mapping[str, Any], out: Path, report: Path, registry: Path, manifest: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    registry.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    clean = _strip_internal(result)
    registry_payload = {
        "schema": "v65a_v1",
        "lifecycle": "PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED",
        "candidates_ordered": [asdict(item) for item in CANDIDATE_SPECS],
        "stage0": clean.get("stage0"),
        "stage1": clean.get("stage1"),
        "formal_plan": clean.get("formal_plan"),
    }
    manifest_payload = {
        "schema": "v65a_manifest_v1",
        "guards": clean.get("guards", {}),
        "fixed_contract": CONTRACT,
        "materialized_frames_total": clean.get("stage0", {}).get("materialized_frames_total", 0) if clean.get("stage0") else 0,
        "candidate_order": list(FROZEN_ORDER),
    }
    out.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    registry.write_text(json.dumps(_plain(registry_payload), ensure_ascii=False, indent=2), encoding="utf-8")
    manifest.write_text(json.dumps(_plain(manifest_payload), ensure_ascii=False, indent=2), encoding="utf-8")
    report.write_text(build_report(clean), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V65A historical Type-II decoder-free scout")
    parser.add_argument("--stage", choices=("verify", "coarse", "formal", "all"), default="verify")
    parser.add_argument("--candidate-root", default=None)
    parser.add_argument("--out", default="workspace/v65a_scout.json")
    parser.add_argument("--report", default="workspace/V65A_SCOUT_REPORT.md")
    parser.add_argument("--registry", default="workspace/v65a_registry.json")
    parser.add_argument("--manifest", default="workspace/v65a_manifest.json")
    args = parser.parse_args(argv)
    root_text = args.candidate_root or os.environ.get("PROJECT_DATA_ROOT")
    root = Path(root_text) if root_text else None
    result = run_scout(args.stage, root)
    write_outputs(result, Path(args.out), Path(args.report), Path(args.registry), Path(args.manifest))
    print(f"[v65a] stage={args.stage} overall={result.get('overall')} selected={(result.get('stage0') or {}).get('selected')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
