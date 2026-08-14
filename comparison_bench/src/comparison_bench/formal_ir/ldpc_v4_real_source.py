"""Read-only v4 real-source extension intake and candidate reconstruction."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from . import ldpc_v3_ttbin_data as base

N = 256
DIMENSION = 1024
STRATA = ("d1024_bw120", "d1024_bw180", "d1024_bw200")
_BINS = {"d1024_bw120": 120, "d1024_bw180": 180, "d1024_bw200": 200}


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _file(path: str | Path) -> dict[str, Any]:
    p = Path(path).resolve(strict=True)
    if not p.is_file():
        raise ValueError("source is not a file")
    raw = p.read_bytes()
    return {"path": str(p), "bytes": len(raw), "sha256": _sha(raw)}


def _self(doc: dict[str, Any], key: str) -> dict[str, Any]:
    return {**doc, key: _sha(_compact(doc))}


def _check_ttbin(main: Path, chunk: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    main, chunk = main.resolve(strict=True), chunk.resolve(strict=True)
    expected = f"{main.stem}.1.ttbin"
    matching = sorted(main.parent.glob(f"{main.stem}.*.ttbin"))
    if chunk.name != expected or matching != [chunk]:
        raise ValueError("exactly one .1.ttbin chunk required")
    return _file(main), _file(chunk)


def _sidecar(entry: Mapping[str, Any], dataset_id: str) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    if dataset_id not in STRATA:
        raise ValueError("stratum")
    sidecar = Path(str(entry["sidecar_dirs"][dataset_id])).resolve(strict=True)
    paths = {name: sidecar / name for name in ("a_eff.npy", "b_eff.npy", "sidecar_meta.json")}
    if any(not p.is_file() for p in paths.values()):
        raise ValueError("sidecar files")
    try:
        a = np.load(paths["a_eff.npy"], allow_pickle=False)
        b = np.load(paths["b_eff.npy"], allow_pickle=False)
        meta = json.loads(paths["sidecar_meta.json"].read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("unreadable sidecar") from exc
    if (not isinstance(meta, dict) or a.ndim != 1 or b.ndim != 1 or a.shape != b.shape
            or not np.issubdtype(a.dtype, np.integer) or not np.issubdtype(b.dtype, np.integer)
            or np.any(a < 0) or np.any(a >= DIMENSION) or np.any(b < 0) or np.any(b >= DIMENSION)
            or a.size < N):
        raise ValueError("sidecar arrays")
    used = meta.get("materialize_params", {}).get("used_params", {})
    required = {"joint_source_mode": "from_ttbin", "joint_origin": "from_ttbin",
                "materialize_origin": "materialized_from_ttbin", "sequence_source_mode": "strict"}
    if not isinstance(used, dict) or any(meta.get(k) != v for k, v in required.items()) or meta.get("sequence_is_sampled") not in (0, False):
        raise ValueError("sidecar provenance")
    dim = used.get("dimension", meta.get("point", {}).get("d", meta.get("d_eff", meta.get("q"))))
    if dim != DIMENSION or used.get("bin_width_ps", meta.get("point", {}).get("bw")) != _BINS[dataset_id] or used.get("pairing_mode") != "nearest":
        raise ValueError("sidecar domain")
    source_paths = used.get("source_ttbin_paths", meta.get("source_ttbin_paths"))
    values = source_paths if isinstance(source_paths, list) else [source_paths]
    try:
        resolved = {str(Path(str(x)).resolve(strict=True)) for x in values if x is not None}
    except Exception as exc:
        raise ValueError("sidecar source path") from exc
    main = str(Path(str(entry["main_ttbin"]["path"])).resolve(strict=True))
    loss = meta.get("loss", meta.get("acquisition_loss"))
    if loss is None:
        import re
        loss = 20 if re.search(r"(?:^|[^0-9])20dB(?:[^0-9]|$)", main, flags=re.IGNORECASE) else None
    declared = used.get("n_pairs_actual", meta.get("n_symbols", meta.get("n_pairs_actual")))
    if (resolved != {main} or loss != 20 or (declared is not None and declared != int(a.size))
            or any(bool(meta.get(k, False)) for k in ("tail_padding", "padding", "padded"))):
        raise ValueError("sidecar source/loss")
    files = {name: _file(path) for name, path in paths.items()}
    record = {"dataset_id": dataset_id, "bin_width_ps": _BINS[dataset_id], "sidecar_dir": str(sidecar),
              "files": files, "array_dtype": {"a_eff.npy": a.dtype.str, "b_eff.npy": b.dtype.str},
              "array_length": int(a.size), "complete_frames": int(a.size // N),
              "source_metadata_sha256": files["sidecar_meta.json"]["sha256"], "dimension": DIMENSION,
              "pairing_mode": "nearest", "processing_rule": "sidecar_a_eff_b_eff_v1", "acquisition_loss": 20}
    record["source_record_sha256"] = _sha(_compact(record))
    return record, a, b


def _acquisition(spec: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, Mapping) or set(spec) != {"main_ttbin", "chunk_ttbin", "sidecar_dirs"} or not isinstance(spec["sidecar_dirs"], Mapping) or set(spec["sidecar_dirs"]) != set(STRATA):
        raise ValueError("acquisition specification")
    main, chunk = _check_ttbin(Path(str(spec["main_ttbin"])), Path(str(spec["chunk_ttbin"])))
    interim = {"main_ttbin": main, "chunk_ttbin": chunk, "sidecar_dirs": dict(spec["sidecar_dirs"])}
    datasets = []
    for dataset_id in STRATA:
        record, _, _ = _sidecar(interim, dataset_id)
        datasets.append(record)
    acquisition_id = _sha(_compact({"main_sha256": main["sha256"], "chunk_sha256": chunk["sha256"]}))
    return {"acquisition_id": acquisition_id, "main_ttbin": main, "chunk_ttbin": chunk, "datasets": datasets}


def build_extension(base_manifest: Mapping[str, Any], acquisitions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    base.verify_source_manifest(base_manifest)
    if not isinstance(acquisitions, Sequence) or isinstance(acquisitions, (str, bytes)) or not acquisitions:
        raise ValueError("added acquisitions")
    base_pair = (base_manifest["main_ttbin"]["sha256"], base_manifest["chunk_ttbin"]["sha256"])
    records = [_acquisition(spec) for spec in acquisitions]
    pairs = [(x["main_ttbin"]["sha256"], x["chunk_ttbin"]["sha256"]) for x in records]
    if base_pair in pairs or len(set(pairs)) != len(pairs) or len({x["acquisition_id"] for x in records}) != len(records):
        raise ValueError("duplicate raw acquisition")
    doc = {"schema": "binary_ldpc_v4_real_source_extension_v1", "base_source_manifest": dict(base_manifest),
           "base_source_manifest_sha256": base_manifest["manifest_sha256"], "added_acquisitions": records}
    result = _self(doc, "extension_sha256")
    candidate_pool(result)
    return result


def write_extension(output: Path, base_manifest: Mapping[str, Any], acquisitions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("fresh extension manifest required")
    doc = build_extension(base_manifest, acquisitions)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.open("xb").write(_compact(doc))
    return doc


def _read_extension(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = path.resolve(strict=True).read_bytes()
    doc = json.loads(raw)
    if _compact(doc) != raw:
        raise ValueError("noncanonical extension")
    verify_extension(doc)
    return doc, _file(path)


def verify_extension(doc: Mapping[str, Any]) -> None:
    keys = {"schema", "base_source_manifest", "base_source_manifest_sha256", "added_acquisitions", "extension_sha256"}
    if not isinstance(doc, Mapping) or set(doc) != keys or doc.get("schema") != "binary_ldpc_v4_real_source_extension_v1":
        raise ValueError("extension schema")
    base_doc = dict(doc); digest = base_doc.pop("extension_sha256")
    if not isinstance(digest, str) or _sha(_compact(base_doc)) != digest:
        raise ValueError("extension hash")
    base.verify_source_manifest(doc["base_source_manifest"])
    if doc["base_source_manifest_sha256"] != doc["base_source_manifest"]["manifest_sha256"]:
        raise ValueError("base binding")
    rebuilt = build_extension(doc["base_source_manifest"], [{"main_ttbin": x["main_ttbin"]["path"], "chunk_ttbin": x["chunk_ttbin"]["path"],
                                                               "sidecar_dirs": {d["dataset_id"]: d["sidecar_dir"] for d in x["datasets"]}} for x in doc["added_acquisitions"]])
    if dict(doc) != rebuilt:
        raise ValueError("extension reconstruction")
    candidate_pool(doc)  # also checks global payload duplicates.


def _payload(a: np.ndarray, b: np.ndarray, frame_id: int) -> str:
    start, end = frame_id * N, (frame_id + 1) * N
    return _sha(np.asarray(a[start:end], dtype="<u2").tobytes() + np.asarray(b[start:end], dtype="<u2").tobytes())


def _row(source_record_sha256: str, acquisition_id: str, dataset_id: str, frame_id: int, a: np.ndarray, b: np.ndarray, *, base_row: bool = False) -> dict[str, Any]:
    start, end = frame_id * N, (frame_id + 1) * N
    payload_identity = _payload(a, b, frame_id)
    source_aware_identity = _sha(_compact({"source_record_sha256": source_record_sha256, "acquisition_id": acquisition_id,
                                           "dataset_id": dataset_id, "frame_id": frame_id, "source_pair_start": start,
                                           "source_pair_end": end, "payload_identity": payload_identity}))
    return {"dataset_id": dataset_id, "frame_id": frame_id, "source_pair_start": start, "source_pair_end": end,
            "frame_identity": source_aware_identity, "payload_identity": payload_identity,
            "source_record_sha256": source_record_sha256, "acquisition_id": acquisition_id, "base_row": base_row}


def candidate_pool(doc: Mapping[str, Any]) -> list[dict[str, Any]]:
    base.verify_source_manifest(doc["base_source_manifest"])
    rows: list[dict[str, Any]] = []
    base_acquisition = _sha(_compact({"main_sha256": doc["base_source_manifest"]["main_ttbin"]["sha256"], "chunk_sha256": doc["base_source_manifest"]["chunk_ttbin"]["sha256"]}))
    for entry in doc["base_source_manifest"]["datasets"]:
        if entry["dataset_id"] not in STRATA:
            continue
        a, b, _ = base._load_dataset(entry)
        for i in range(a.size // N):
            row = _row(entry["source_record_sha256"], base_acquisition, entry["dataset_id"], i, a, b, base_row=True)
            # Preserve v3 identity solely for the registered-base exclusion set.
            row["frame_identity"] = base._identity(entry, i, a, b)
            rows.append(row)
    for acquisition in doc["added_acquisitions"]:
        interim = {"main_ttbin": acquisition["main_ttbin"], "chunk_ttbin": acquisition["chunk_ttbin"],
                   "sidecar_dirs": {d["dataset_id"]: d["sidecar_dir"] for d in acquisition["datasets"]}}
        for expected in acquisition["datasets"]:
            actual, a, b = _sidecar(interim, expected["dataset_id"])
            if actual != expected:
                raise ValueError("added sidecar changed")
            rows.extend(_row(expected["source_record_sha256"], acquisition["acquisition_id"], expected["dataset_id"], i, a, b) for i in range(a.size // N))
    payloads = [row["payload_identity"] for row in rows]
    if len(set(payloads)) != len(payloads):
        raise ValueError("duplicate frame payload")
    return rows


def selection_pool(extension_path: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    doc, record = _read_extension(extension_path)
    return doc, record, candidate_pool(doc)


def arrays_for_row(doc: Mapping[str, Any], row: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    """Reconstruct one selected frame from the verified extension pool."""
    wanted = next((x for x in candidate_pool(doc) if x["frame_identity"] == row.get("frame_identity")), None)
    if wanted is None or any(wanted[k] != row.get(k) for k in ("dataset_id", "frame_id", "payload_identity", "acquisition_id")):
        raise ValueError("selected source row")
    if wanted["base_row"]:
        entry = next(x for x in doc["base_source_manifest"]["datasets"] if x["dataset_id"] == wanted["dataset_id"])
        a, b, _ = base._load_dataset(entry)
    else:
        acquisition = next(x for x in doc["added_acquisitions"] if x["acquisition_id"] == wanted["acquisition_id"])
        interim = {"main_ttbin": acquisition["main_ttbin"], "chunk_ttbin": acquisition["chunk_ttbin"],
                   "sidecar_dirs": {d["dataset_id"]: d["sidecar_dir"] for d in acquisition["datasets"]}}
        _, a, b = _sidecar(interim, wanted["dataset_id"])
    return a[wanted["source_pair_start"]:wanted["source_pair_end"]].copy(), b[wanted["source_pair_start"]:wanted["source_pair_end"]].copy()
