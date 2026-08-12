"""Read-only Phase 6A bridge for TTBIN-derived formal LDPC v3 data."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from ..utils.bitops import symbols_to_bits

N = 256
DIMENSION = 1024
_DATASETS = (("d1024_bw100", 100, "calibration", 64), ("d1024_bw120", 120, "confirmation", 32),
             ("d1024_bw180", 180, "confirmation", 32), ("d1024_bw200", 200, "confirmation", 32))


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _file_record(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError("source is not a file")
    data = resolved.read_bytes()
    return {"path": str(resolved), "bytes": len(data), "sha256": _sha_bytes(data)}


def _valid_hex(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def _source_record_sha(record: Mapping[str, Any]) -> str:
    return _sha_bytes(_compact(dict(record)))


def _load_dataset(entry: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    sidecar = Path(entry["sidecar_dir"])
    a_path, b_path, meta_path = sidecar / "a_eff.npy", sidecar / "b_eff.npy", sidecar / "sidecar_meta.json"
    try:
        a, b = np.load(a_path, allow_pickle=False), np.load(b_path, allow_pickle=False)
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("unreadable sidecar") from exc
    if not isinstance(meta, dict):
        raise ValueError("sidecar metadata")
    if (a.ndim != 1 or b.ndim != 1 or a.shape != b.shape or not np.issubdtype(a.dtype, np.integer)
            or not np.issubdtype(b.dtype, np.integer) or np.any(a < 0) or np.any(a >= DIMENSION)
            or np.any(b < 0) or np.any(b >= DIMENSION)):
        raise ValueError("sidecar arrays")
    used = meta.get("materialize_params", {}).get("used_params", {})
    if not isinstance(used, dict):
        raise ValueError("sidecar used parameters")
    required = {"joint_source_mode": "from_ttbin", "joint_origin": "from_ttbin",
                "materialize_origin": "materialized_from_ttbin", "sequence_source_mode": "strict"}
    if any(meta.get(key) != value for key, value in required.items()) or meta.get("sequence_is_sampled") not in (0, False):
        raise ValueError("sidecar provenance")
    dimension = used.get("dimension", meta.get("point", {}).get("d", meta.get("d_eff", meta.get("q"))))
    bin_width = used.get("bin_width_ps", meta.get("point", {}).get("bw"))
    if dimension != DIMENSION or bin_width != entry["bin_width_ps"]:
        raise ValueError("sidecar domain")
    supplied = Path(entry["main_ttbin"]).resolve(strict=True)
    source_paths = used.get("source_ttbin_paths", meta.get("source_ttbin_paths"))
    candidates = source_paths if isinstance(source_paths, list) else [source_paths]
    try:
        resolved = {str(Path(str(item)).resolve(strict=True)) for item in candidates if item is not None}
    except Exception as exc:
        raise ValueError("sidecar source path") from exc
    if resolved != {str(supplied)} or a.size < int(entry["required_frames"]) * N:
        raise ValueError("sidecar completeness")
    if used.get("pairing_mode") != "nearest":
        raise ValueError("sidecar pairing mode")
    loss = meta.get("loss", meta.get("acquisition_loss"))
    if loss is None:
        import re
        found = re.search(r"(?:^|[^0-9])20dB(?:[^0-9]|$)", str(supplied), flags=re.IGNORECASE)
        loss = 20 if found else None
    if loss != 20:
        raise ValueError("acquisition loss")
    return a, b, meta


def build_source_manifest(main_ttbin: str | Path, chunk_ttbin: str | Path, sidecar_dirs: Mapping[str, str | Path]) -> dict:
    """Bind the exact files and validate four prescribed sidecar datasets."""
    main, chunk = Path(main_ttbin).resolve(strict=True), Path(chunk_ttbin).resolve(strict=True)
    expected_chunk = f"{main.stem}.1.ttbin"
    matching_chunks = sorted(main.parent.glob(f"{main.stem}.*.ttbin"))
    if chunk.name != expected_chunk or matching_chunks != [chunk]:
        raise ValueError("exactly one .1.ttbin chunk required")
    if set(sidecar_dirs) != {name for name, *_ in _DATASETS}:
        raise ValueError("exact sidecar datasets required")
    datasets: list[dict[str, Any]] = []
    for dataset_id, bw, role, count in _DATASETS:
        sidecar = Path(sidecar_dirs[dataset_id]).resolve(strict=True)
        entry = {"dataset_id": dataset_id, "bin_width_ps": bw, "role": role, "required_frames": count,
                 "sidecar_dir": str(sidecar), "main_ttbin": str(main), "pairing_mode": "nearest",
                 "processing_rule": "sidecar_a_eff_b_eff_v1", "dimension": DIMENSION}
        a, b, meta = _load_dataset(entry)
        entry["acquisition_loss"] = 20
        entry["files"] = {"a_eff.npy": _file_record(sidecar / "a_eff.npy"), "b_eff.npy": _file_record(sidecar / "b_eff.npy"),
                          "sidecar_meta.json": _file_record(sidecar / "sidecar_meta.json")}
        entry["source_metadata_sha256"] = entry["files"]["sidecar_meta.json"]["sha256"]
        entry["source_record_sha256"] = _source_record_sha({k: entry[k] for k in entry if k not in {"files", "source_record_sha256"}} | {"files": entry["files"]})
        datasets.append(entry)
    result = {"schema": "binary_ldpc_v3_phase6_source_manifest_v1", "main_ttbin": _file_record(main),
              "chunk_ttbin": _file_record(chunk), "datasets": datasets}
    result["manifest_sha256"] = _sha_bytes(_compact(result))
    return result


def verify_source_manifest(manifest: Mapping[str, Any]) -> None:
    if not isinstance(manifest, Mapping) or set(manifest) != {"schema", "main_ttbin", "chunk_ttbin", "datasets", "manifest_sha256"}:
        raise ValueError("manifest schema")
    base = dict(manifest); digest = base.pop("manifest_sha256")
    if manifest["schema"] != "binary_ldpc_v3_phase6_source_manifest_v1" or not _valid_hex(digest) or _sha_bytes(_compact(base)) != digest:
        raise ValueError("manifest hash")
    main = manifest["main_ttbin"]
    chunk = manifest["chunk_ttbin"]
    if not isinstance(main, Mapping) or not isinstance(chunk, Mapping) or Path(str(chunk.get("path", ""))).name != Path(str(main.get("path", ""))).stem + ".1.ttbin":
        raise ValueError("manifest ttbin")
    expected = [x[0] for x in _DATASETS]
    if not isinstance(manifest["datasets"], list) or [d.get("dataset_id") for d in manifest["datasets"] if isinstance(d, Mapping)] != expected:
        raise ValueError("manifest datasets")
    for record in (main, chunk):
        current = _file_record(Path(str(record.get("path", ""))))
        if dict(record) != current: raise ValueError("source file changed")
    for d, spec in zip(manifest["datasets"], _DATASETS):
        if not isinstance(d, Mapping): raise ValueError("dataset schema")
        _, bw, role, required = spec
        check = dict(d); check.pop("source_record_sha256", None)
        if (d.get("bin_width_ps"), d.get("role"), d.get("required_frames"), d.get("dimension"), d.get("pairing_mode"), d.get("processing_rule"), d.get("acquisition_loss")) != (bw, role, required, DIMENSION, "nearest", "sidecar_a_eff_b_eff_v1", 20) or d.get("main_ttbin") != main["path"] or _source_record_sha(check) != d.get("source_record_sha256"):
            raise ValueError("dataset binding")
        for record in d.get("files", {}).values():
            if not isinstance(record, Mapping) or dict(record) != _file_record(Path(str(record.get("path", "")))): raise ValueError("sidecar file changed")
        _load_dataset(d)


def _identity(entry: Mapping[str, Any], frame_id: int, a: np.ndarray, b: np.ndarray) -> str:
    start, end = frame_id * N, (frame_id + 1) * N
    payload = {"source_record_sha256": entry["source_record_sha256"], "dataset_id": entry["dataset_id"], "frame_id": frame_id,
               "source_pair_start": start, "source_pair_end": end,
               "alice_sha256": _sha_bytes(np.asarray(a[start:end], dtype="<i8").tobytes()),
               "bob_sha256": _sha_bytes(np.asarray(b[start:end], dtype="<i8").tobytes())}
    return _sha_bytes(_compact(payload))


def _selected(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for entry in manifest["datasets"]:
        a, b, _ = _load_dataset(entry)
        candidates = []
        for frame_id in range(a.size // N):
            identity = _identity(entry, frame_id, a, b)
            rank = _sha_bytes(f"binary_ldpc_v3_phase6_selection_v1|{entry['role']}|{entry['dataset_id']}|{identity}".encode("ascii"))
            candidates.append((rank, frame_id, identity))
        for rank, frame_id, identity in sorted(candidates)[:entry["required_frames"]]:
            rows.append({"role": entry["role"], "dataset_id": entry["dataset_id"], "bin_width_ps": entry["bin_width_ps"], "frame_id": frame_id,
                         "selection_rank": rank, "frame_identity": identity, "source_pair_start": frame_id * N, "source_pair_end": (frame_id + 1) * N})
    rows.sort(key=lambda r: (r["role"], r["bin_width_ps"], r["selection_rank"]))
    return rows


def _calibration(manifest: Mapping[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    entry = manifest["datasets"][0]; a, b, _ = _load_dataset(entry)
    selected = [r for r in rows if r["role"] == "calibration"]
    if len(selected) != 64: raise ValueError("calibration selection")
    ai = np.concatenate([a[r["source_pair_start"]:r["source_pair_end"]] for r in selected])
    bi = np.concatenate([b[r["source_pair_start"]:r["source_pair_end"]] for r in selected])
    ab, bb = symbols_to_bits(ai.astype(np.int64), DIMENSION, "gray"), symbols_to_bits(bi.astype(np.int64), DIMENSION, "gray")
    planes = [{"plane_id": i, "errors": int(np.count_nonzero(ab[:, i] != bb[:, i])), "total_bits": 64 * N,
               "p_hat": int(np.count_nonzero(ab[:, i] != bb[:, i])) / (64 * N)} for i in range(10)]
    source = _sha_bytes(_compact([{k: r[k] for k in ("dataset_id", "frame_id", "frame_identity", "selection_rank")} for r in selected]))
    result = {"calibration_role": "sacrificed_tuning_only", "dimension": DIMENSION, "mapping": "gray", "frame_len_symbols": N,
              "source_sha256": source, "planes": planes}
    result["calibration_sha256"] = _sha_bytes(_compact(result))
    return result


def build_locked_data(manifest: Mapping[str, Any]) -> dict:
    verify_source_manifest(manifest)
    selected = _selected(manifest)
    lock = {"schema": "binary_ldpc_v3_phase6_locked_data_v1", "source_manifest": dict(manifest),
            "source_manifest_sha256": manifest["manifest_sha256"], "selected_frames": selected,
            "calibration": _calibration(manifest, selected)}
    lock["lock_sha256"] = _sha_bytes(_compact(lock))
    return lock


def verify_locked_data(lock: Mapping[str, Any]) -> None:
    if not isinstance(lock, Mapping) or set(lock) != {"schema", "source_manifest", "source_manifest_sha256", "selected_frames", "calibration", "lock_sha256"}:
        raise ValueError("lock schema")
    base = dict(lock); digest = base.pop("lock_sha256")
    if lock["schema"] != "binary_ldpc_v3_phase6_locked_data_v1" or not _valid_hex(digest) or _sha_bytes(_compact(base)) != digest:
        raise ValueError("lock hash")
    verify_source_manifest(lock["source_manifest"])
    if lock["source_manifest_sha256"] != lock["source_manifest"]["manifest_sha256"] or lock["selected_frames"] != _selected(lock["source_manifest"]):
        raise ValueError("selection reconstruction")
    if lock["calibration"] != _calibration(lock["source_manifest"], lock["selected_frames"]): raise ValueError("calibration reconstruction")
    keys = {(r["dataset_id"], r["frame_id"]) for r in lock["selected_frames"]}
    if len(keys) != 160 or len([r for r in lock["selected_frames"] if r["role"] == "calibration"]) != 64: raise ValueError("selection disjointness")


def frame_arrays(lock: Mapping[str, Any], role: str, dataset_id: str, frame_id: int) -> tuple[np.ndarray, np.ndarray]:
    """Return copies of one verified selected frame; never writes source files."""
    verify_locked_data(lock)
    matches = [r for r in lock["selected_frames"] if (r["role"], r["dataset_id"], r["frame_id"]) == (role, dataset_id, frame_id)]
    if len(matches) != 1: raise ValueError("selected frame not found")
    entry = next(d for d in lock["source_manifest"]["datasets"] if d["dataset_id"] == dataset_id)
    a, b, _ = _load_dataset(entry); row = matches[0]
    start, end = row["source_pair_start"], row["source_pair_end"]
    if _identity(entry, frame_id, a, b) != row["frame_identity"]: raise ValueError("frame identity")
    return a[start:end].copy(), b[start:end].copy()
