"""Decoder-free mapping of the frozen V25 GF(32) train counts.

The command first checks the four named provenance records and NPZ/NPY
headers. It does not materialize a count array until every metadata gate has
passed. See the paired preregistration for the scientific contract.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

try:
    import resource
except ImportError:  # pragma: no cover - production execution is under WSL
    resource = None  # type: ignore[assignment]


BATCH_UUID = "6f821d0b-71e3-46c1-ae84-2da374edbcc2"
EXACT_COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.nbldpc_gf32_source_map --execute --out-root "
    "workspace/gf32_source_map_6f821d0b"
)
COUNTS_REL = Path(
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
    "nbldpc_v25_20260818/run_04/channel_counts.npz"
)
PROVENANCE_REL = {
    "run_inventory": Path(
        "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
        "nbldpc_v25_20260818/run_04/data_inventory.json"
    ),
    "split_manifest": Path(
        "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
        "nbldpc_v25_20260818/run_04/split_manifest.json"
    ),
    "evidence_inventory": Path(
        "openspec/changes/formal-nonbinary-ldpc-v25-empirical-timestamp-"
        "channel-and-multilevel-factorization-gate/evidence/data_inventory.json"
    ),
    "build_manifest": Path(
        "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
        "v13r3fresh_pairs_20260816/build_manifest.json"
    ),
}
V13_PAIRS_PREFIX = (
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
    "v13r3fresh_pairs_20260816"
)
EXPECTED_ROLES = {
    "data_role": (
        "characterization/empirical-joint (NOT qualification; may be split "
        "train/validation/holdout)"
    ),
    "allowed_uses": (
        "characterization; channel-model comparison; factorization gate; "
        "source-drift analysis; train/validation/holdout split by time"
    ),
    "forbidden_uses": "fresh qualification; promotion; final FER claim",
}
SOURCE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "source_id": "type2_1M_20260121_184040",
        "label": "1M",
        "train_pairs": 307200,
    },
    {
        "source_id": "type2_1p5M_20260121_183806",
        "label": "1p5M",
        "train_pairs": 424960,
    },
    {
        "source_id": "type2_2M_20260121_183657",
        "label": "2M",
        "train_pairs": 559872,
    },
)
EXPECTED_TRAIN_TOTAL = sum(int(s["train_pairs"]) for s in SOURCE_SPECS)
ARRAY_SHAPE = (1024, 1024)
N_SYMBOLS = 32
MAX_SECONDS = 60.0
MAX_RSS_BYTES = 1024**3
ENTROPY_TOL = 1e-10


class SourceGateError(ValueError):
    """The documented input/source/split metadata do not match the freeze."""


class CountValueError(ValueError):
    """An admitted train count array violates the frozen value contract."""


def expected_npz_key(source_id: str) -> str:
    """Return the exact double-suffix logical key emitted by the V25 writer."""
    return f"{source_id}_N_ab_train_N_ab_train"


def _norm_slashes(path_value: Any) -> str:
    value = str(path_value).replace("\\", "/")
    while "//" in value:
        value = value.replace("//", "/")
    return value.rstrip("/")


def _expected_pairs_path(source_id: str) -> str:
    return f"{V13_PAIRS_PREFIX}/{source_id}/pairs.parquet"


def _source_records(records: Any, where: str) -> dict[str, Mapping[str, Any]]:
    if not isinstance(records, list):
        raise SourceGateError(f"{where}.primary_joint_data_sources must be a list")
    by_id: dict[str, Mapping[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("source_id"), str):
            raise SourceGateError(f"{where} has a source record without source_id")
        source_id = record["source_id"]
        if source_id in by_id:
            raise SourceGateError(f"{where} repeats source_id {source_id}")
        by_id[source_id] = record
    expected = {str(s["source_id"]) for s in SOURCE_SPECS}
    if set(by_id) != expected:
        raise SourceGateError(f"{where} source IDs differ from the frozen three-source set")
    return by_id


def validate_provenance(provenance: Mapping[str, Any]) -> dict[str, Any]:
    """Validate only the four explicitly admitted JSON provenance records.

    Contained paths are compared as strings. This function never opens or
    follows a parquet, sidecar, TTBin, or raw-data path.
    """
    required = set(PROVENANCE_REL)
    if set(provenance) != required:
        raise SourceGateError("provenance input set differs from the four frozen JSONs")

    inventories: list[tuple[str, dict[str, Mapping[str, Any]]]] = []
    for name in ("run_inventory", "evidence_inventory"):
        document = provenance[name]
        if not isinstance(document, dict):
            raise SourceGateError(f"{name} must be a JSON object")
        records = _source_records(document.get("primary_joint_data_sources"), name)
        inventories.append((name, records))

    source_paths: dict[str, str] = {}
    expected_ids = [str(s["source_id"]) for s in SOURCE_SPECS]
    for name, records in inventories:
        for spec in SOURCE_SPECS:
            source_id = str(spec["source_id"])
            record = records[source_id]
            for field, expected_value in EXPECTED_ROLES.items():
                if record.get(field) != expected_value:
                    raise SourceGateError(
                        f"{name} role field {field} differs for {source_id}"
                    )
            path_value = record.get("pairs_parquet")
            normalized = _norm_slashes(path_value)
            expected_path = _expected_pairs_path(source_id)
            if normalized != expected_path:
                raise SourceGateError(
                    f"{name} pairs_parquet path differs for {source_id}"
                )
            if name == "run_inventory":
                source_paths[source_id] = normalized

    split = provenance["split_manifest"]
    if not isinstance(split, dict):
        raise SourceGateError("split_manifest must be a JSON object")
    ratios = split.get("split_ratios")
    if (
        not isinstance(ratios, list)
        or len(ratios) != 3
        or any(not isinstance(v, (int, float)) or isinstance(v, bool) for v in ratios)
        or any(not math.isclose(float(got), want, rel_tol=0.0, abs_tol=1e-12)
               for got, want in zip(ratios, (0.60, 0.20, 0.20)))
    ):
        raise SourceGateError("split ratios differ from frozen 0.60/0.20/0.20")
    per_source = split.get("per_source")
    if not isinstance(per_source, dict) or set(per_source) != set(expected_ids):
        raise SourceGateError("split manifest source IDs differ from the frozen set")
    for spec in SOURCE_SPECS:
        source_id = str(spec["source_id"])
        record = per_source[source_id]
        if not isinstance(record, dict) or not isinstance(record.get("pairs"), dict):
            raise SourceGateError(f"split record is malformed for {source_id}")
        train = record["pairs"].get("train")
        if isinstance(train, bool) or not isinstance(train, int):
            raise SourceGateError(f"train pair count is not an integer for {source_id}")
        if train != int(spec["train_pairs"]):
            raise SourceGateError(f"train pair total differs for {source_id}")

    upstream = provenance["build_manifest"]
    if not isinstance(upstream, dict) or not isinstance(upstream.get("sources"), list):
        raise SourceGateError("build_manifest.sources must be a list")
    upstream_by_id: dict[str, Mapping[str, Any]] = {}
    for record in upstream["sources"]:
        if not isinstance(record, dict):
            raise SourceGateError("build manifest source record is malformed")
        source_tag = record.get("source_tag")
        if not isinstance(source_tag, str) or source_tag in upstream_by_id:
            raise SourceGateError("build manifest has missing or duplicate source_tag")
        upstream_by_id[source_tag] = record
    if set(upstream_by_id) != set(expected_ids):
        raise SourceGateError("build manifest source IDs differ from the frozen set")
    for source_id in expected_ids:
        record = upstream_by_id[source_id]
        pairs = record.get("pairs_parquet")
        if not isinstance(pairs, dict):
            raise SourceGateError(f"build manifest pairs_parquet is malformed for {source_id}")
        upstream_path = _norm_slashes(pairs.get("path"))
        if not upstream_path.endswith("/" + _expected_pairs_path(source_id)):
            raise SourceGateError(
                f"build manifest repository suffix differs for {source_id}"
            )

    return {
        "status": "PASS",
        "provenance_level": "DOCUMENTED_TRAIN_ROLE_CONSISTENT",
        "source_ids": expected_ids,
        "source_paths": source_paths,
        "split_ratios": [0.60, 0.20, 0.20],
        "train_pairs_by_source": {
            str(s["source_id"]): int(s["train_pairs"]) for s in SOURCE_SPECS
        },
        "total_train_pairs": EXPECTED_TRAIN_TOTAL,
        "role_fields_checked": list(EXPECTED_ROLES),
        "upstream_source_tags_equal_source_ids": True,
        "path_records_followed": False,
        "limitation": (
            "Documented train-role consistency only; frame boundaries and an "
            "artifact-to-historical-writer binding are not reconstructed."
        ),
    }


def _read_npy_header(stream: Any) -> tuple[tuple[int, ...], bool, np.dtype, tuple[int, int]]:
    version = np.lib.format.read_magic(stream)
    if version == (1, 0):
        shape, fortran_order, dtype = np.lib.format.read_array_header_1_0(stream)
    elif version == (2, 0):
        shape, fortran_order, dtype = np.lib.format.read_array_header_2_0(stream)
    elif version == (3, 0):
        # Version 3 has the same framing as v2 but UTF-8 header strings.
        shape, fortran_order, dtype = np.lib.format._read_array_header(
            stream, version=version
        )
    else:
        raise SourceGateError(f"unsupported NPY version {version}")
    return tuple(shape), bool(fortran_order), np.dtype(dtype), version


def inspect_npz_headers(path: str | Path) -> dict[str, dict[str, Any]]:
    """Read ZIP directory entries and NPY headers, never array payloads."""
    expected_keys = [expected_npz_key(str(s["source_id"])) for s in SOURCE_SPECS]
    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = archive.infolist()
            if len(infos) != len(expected_keys):
                raise SourceGateError("NPZ physical member count is not exactly three")
            logical_infos: dict[str, zipfile.ZipInfo] = {}
            for info in infos:
                filename = info.filename
                if info.is_dir() or not filename.endswith(".npy"):
                    raise SourceGateError("NPZ contains a non-NPY physical member")
                logical_key = filename[:-4]
                if logical_key in logical_infos:
                    raise SourceGateError(f"NPZ repeats logical key {logical_key}")
                logical_infos[logical_key] = info
            if set(logical_infos) != set(expected_keys):
                raise SourceGateError("NPZ logical keys differ from exact frozen source keys")

            headers: dict[str, dict[str, Any]] = {}
            for key in expected_keys:
                with archive.open(logical_infos[key], "r") as member:
                    shape, fortran_order, dtype, version = _read_npy_header(member)
                if shape != ARRAY_SHAPE:
                    raise SourceGateError(f"NPY shape differs for {key}")
                if dtype.hasobject or dtype.kind != "f" or dtype.itemsize != 8:
                    raise SourceGateError(f"NPY dtype is not non-object float64 for {key}")
                if fortran_order:
                    raise SourceGateError(f"NPY order is not C-order for {key}")
                headers[key] = {
                    "shape": list(shape),
                    "dtype": dtype.str,
                    "fortran_order": fortran_order,
                    "npy_version": list(version),
                }
            return headers
    except SourceGateError:
        raise
    except (OSError, EOFError, zipfile.BadZipFile, ValueError, KeyError) as exc:
        raise SourceGateError(f"NPZ header inspection failed: {exc}") from exc


def validate_count_values(values: Any, expected_total: int) -> np.ndarray:
    """Validate one float64 count matrix, then convert it for exact sums."""
    array = np.asarray(values)
    if array.shape != ARRAY_SHAPE:
        raise CountValueError("count shape differs from (1024,1024)")
    if array.dtype.hasobject or array.dtype.kind != "f" or array.dtype.itemsize != 8:
        raise CountValueError("count values are not float64")
    if not np.all(np.isfinite(array)):
        raise CountValueError("count array contains non-finite values")
    if np.any(array < 0):
        raise CountValueError("count array contains negative values")
    if np.any(array != np.floor(array)):
        raise CountValueError("count array contains fractional values")
    if np.any(array > int(expected_total)):
        raise CountValueError("a cell exceeds the frozen source train total")
    exact = array.astype(np.int64)
    total = int(exact.sum(dtype=np.int64))
    if total != int(expected_total):
        raise CountValueError(
            f"count sum {total} differs from frozen train total {expected_total}"
        )
    return exact


def _entropy_from_counts(counts: np.ndarray) -> float:
    total = int(np.asarray(counts, dtype=np.int64).sum(dtype=np.int64))
    if total <= 0:
        return 0.0
    probabilities = np.asarray(counts, dtype=np.float64) / total
    probabilities = probabilities[probabilities > 0]
    entropy = float(-np.sum(probabilities * np.log2(probabilities)))
    return 0.0 if entropy == 0.0 else entropy


def summarize_source_counts(
    counts_ab: np.ndarray, source_id: str, label: str, expected_total: int
) -> dict[str, Any]:
    """Map one N_ab[a,b] matrix to E1 counts and Bob-conditioned diagnostics."""
    counts = validate_count_values(counts_ab, expected_total)

    # N_ab is C-order with A on axis 0 and B on axis 1. Reshape A as
    # (U1_A, U2_A, B), then sum away the low five A bits.
    counts_u1a_b = counts.reshape(32, 32, 1024).sum(axis=1, dtype=np.int64)
    u1a = np.arange(32, dtype=np.int64)[:, None]
    u1b = (np.arange(1024, dtype=np.int64)[None, :] >> 5) & 31
    error_symbol = u1a ^ u1b
    b_index = np.broadcast_to(np.arange(1024, dtype=np.int64), counts_u1a_b.shape)
    conditional_counts = np.zeros((32, 1024), dtype=np.int64)
    conditional_counts[error_symbol, b_index] = counts_u1a_b

    h = conditional_counts.sum(axis=1, dtype=np.int64)
    input_total = int(counts.sum(dtype=np.int64))
    marginal_total = int(h.sum(dtype=np.int64))
    conditional_total = int(conditional_counts.sum(dtype=np.int64))
    if not (input_total == marginal_total == conditional_total == int(expected_total)):
        raise CountValueError("mapped counts do not conserve the input total")

    pmf = h.astype(np.float64) / input_total
    pmf_sum = float(pmf.sum())
    if not math.isclose(pmf_sum, 1.0, rel_tol=0.0, abs_tol=ENTROPY_TOL):
        raise CountValueError("error PMF does not normalize")
    entropy = _entropy_from_counts(h)
    bob_counts = conditional_counts.sum(axis=0, dtype=np.int64)
    conditional_entropy = 0.0
    for b, n_b in enumerate(bob_counts):
        if n_b:
            conditional_entropy += (int(n_b) / input_total) * _entropy_from_counts(
                conditional_counts[:, b]
            )
    mutual_information = entropy - conditional_entropy
    if (
        entropy < -ENTROPY_TOL
        or entropy > 5.0 + ENTROPY_TOL
        or conditional_entropy < -ENTROPY_TOL
        or conditional_entropy > entropy + ENTROPY_TOL
    ):
        raise CountValueError("entropy bounds failed")
    if mutual_information < -ENTROPY_TOL:
        raise CountValueError("I(E1;B) is negative beyond numeric tolerance")
    if mutual_information <= 0:
        mutual_information = 0.0

    n_zero = int(h[0])
    n_nonzero = input_total - n_zero
    nonzero_tv: float | None = None
    conditional_tv_weighted: float | None = None
    error_per_b = conditional_counts[1:, :].sum(axis=0, dtype=np.int64)
    if n_nonzero > 0:
        uniform31 = np.full(31, 1.0 / 31.0, dtype=np.float64)
        nonzero_tv = 0.5 * float(
            np.abs(h[1:].astype(np.float64) / n_nonzero - uniform31).sum()
        )
        conditional_tv_weighted = 0.0
        for b, n_error_b in enumerate(error_per_b):
            if n_error_b:
                local_pmf = conditional_counts[1:, b].astype(np.float64) / int(n_error_b)
                local_tv = 0.5 * float(np.abs(local_pmf - uniform31).sum())
                conditional_tv_weighted += (int(n_error_b) / n_nonzero) * local_tv

    error_bearing = error_per_b[error_per_b > 0]
    return {
        "source_id": source_id,
        "label": label,
        "npz_key": expected_npz_key(source_id),
        "N": input_total,
        "E1_counts": [int(v) for v in h],
        "E1_pmf": [float(v) for v in pmf],
        "n_zero": n_zero,
        "n_nonzero": n_nonzero,
        "p_zero": n_zero / input_total,
        "H_E1_bits": entropy,
        "H_E1_given_B_bits": conditional_entropy,
        "I_E1_B_bits": mutual_information,
        "nonzero_tv": nonzero_tv,
        "conditional_nonzero_tv_weighted": conditional_tv_weighted,
        "observed_B_columns": int(np.count_nonzero(bob_counts)),
        "error_bearing_B_columns": int(error_bearing.size),
        "error_bearing_B_columns_lt5": int(np.count_nonzero(error_bearing < 5)),
        "error_bearing_B_columns_lt20": int(np.count_nonzero(error_bearing < 20)),
    }


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise SourceGateError(f"provenance JSON is not an object: {path}")
    return value


def _rss_bytes() -> int | None:
    if resource is None:
        return None
    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # Linux reports KiB; macOS reports bytes. Frozen execution is Linux/WSL.
    return peak if sys.platform == "darwin" else peak * 1024


def _budget_stop(snapshot: Mapping[str, Any]) -> str | None:
    rss = snapshot.get("peak_rss_bytes")
    if rss is None:
        return "RSS_MONITOR_UNAVAILABLE"
    if float(snapshot["elapsed_s"]) > MAX_SECONDS:
        return "WALL_BUDGET_EXCEEDED"
    if int(rss) > MAX_RSS_BYTES:
        return "RSS_BUDGET_EXCEEDED"
    return None


def _json_dump(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _append_log(path: Path, line: str) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(line.rstrip() + "\n")


def _load_one_npz_member(path: Path, key: str) -> np.ndarray:
    with np.load(path, allow_pickle=False) as archive:
        return archive[key]


def run_batch(
    *,
    counts_path: str | Path,
    provenance_paths: Mapping[str, str | Path],
    out_root: str | Path,
    source_specs: Sequence[Mapping[str, Any]] = SOURCE_SPECS,
    dirty_tree_uuid: str = BATCH_UUID,
    exact_command: str = EXACT_COMMAND,
    clock: Any = time.monotonic,
    load_member: Any = _load_one_npz_member,
    rss_bytes: Any = _rss_bytes,
) -> dict[str, Any]:
    """Execute the frozen mapping against injected paths (tests use only fakes)."""
    root = Path(out_root)
    if root.exists():
        raise FileExistsError(f"refusing existing output root: {root}")
    root.mkdir(parents=True, exist_ok=False)
    manifest_path = root / "manifest.json"
    summary_path = root / "source_summary.json"
    log_path = root / "RESULT_LOG.md"
    started = clock()
    manifest: dict[str, Any] = {
        "schema": "gf32_source_map_manifest_v1",
        "batch_uuid": BATCH_UUID,
        "dirty_tree_uuid": dirty_tree_uuid,
        "dirty_tree_uuid_note": "scope reference only; not state/hash binding",
        "track": "DECIDE",
        "status": "IN_PROGRESS",
        "exact_command": exact_command,
        "counts_input": str(counts_path),
        "provenance_json_inputs": {k: str(v) for k, v in provenance_paths.items()},
        "provenance_level": "DOCUMENTED_TRAIN_ROLE_CONSISTENT",
        "expected_source_profile": [
            {
                "source_id": str(spec["source_id"]),
                "label": str(spec["label"]),
                "train_pairs": int(spec["train_pairs"]),
                "npz_key": expected_npz_key(str(spec["source_id"])),
            }
            for spec in source_specs
        ],
        "provenance_gate": {"status": "PENDING"},
        "npz_header_gate": {"status": "PENDING", "headers": []},
        "admitted_sources": [],
        "attempted_sources": [],
        "resource_checks": [],
        "runtime": {"max_seconds": MAX_SECONDS, "max_rss_bytes": MAX_RSS_BYTES},
        "mapping_convention": {
            "axis0": "A",
            "axis1": "B",
            "F03_encoding": "natural",
            "U1": "(s >> 5) & 31",
            "U2": "s & 31",
            "E1": "U1(A) XOR U1(B)",
            "GF32_addition": "XOR",
            "polynomial": 37,
            "multiplication_used": False,
            "source_pooling": False,
        },
        "claim_ceiling": (
            "Descriptive historical documented-train statistics only; no "
            "calibration, Model-F transfer, FER/SKR, qualification, or route decision."
        ),
    }
    summary: dict[str, Any] = {
        "schema": "gf32_source_map_summary_v1",
        "status": "IN_PROGRESS",
        "per_source": [],
    }
    _json_dump(manifest_path, manifest)
    _json_dump(summary_path, summary)
    log_path.write_text(
        "# GF32 source mapping execution log\n\n"
        "DECIDE; decoder-free; per-source only. Subsequent review and main "
        "acceptance are append-only entries.\n",
        encoding="utf-8",
    )
    _append_log(log_path, "- Execution started; no count values read yet.")

    def current_snapshot() -> dict[str, Any]:
        return {
            "elapsed_s": max(0.0, clock() - started),
            "peak_rss_bytes": rss_bytes(),
        }

    def persist(status: str) -> None:
        manifest["status"] = status
        summary["status"] = status
        manifest["runtime"]["last_snapshot"] = current_snapshot()
        _json_dump(manifest_path, manifest)
        _json_dump(summary_path, summary)

    try:
        expected_provenance = set(PROVENANCE_REL)
        if set(provenance_paths) != expected_provenance:
            raise SourceGateError("provenance paths differ from the four frozen JSONs")
        provenance = {
            name: _read_json(Path(provenance_paths[name])) for name in PROVENANCE_REL
        }
        provenance_result = validate_provenance(provenance)
        manifest["provenance_gate"] = provenance_result
        headers = inspect_npz_headers(counts_path)
        manifest["npz_header_gate"] = {
            "status": "PASS",
            "member_count": len(headers),
            "headers": headers,
            "value_payloads_materialized": False,
        }
        manifest["admitted_sources"] = [str(spec["source_id"]) for spec in source_specs]
        _append_log(log_path, "- F1 provenance and NPZ header gates PASS; no count payload was loaded before this point.")
        _json_dump(manifest_path, manifest)
    except (OSError, ValueError, KeyError, EOFError, zipfile.BadZipFile) as exc:
        manifest["provenance_gate"] = manifest.get("provenance_gate", {"status": "PENDING"})
        if manifest["provenance_gate"].get("status") != "PASS":
            manifest["provenance_gate"] = {"status": "FAIL", "reason": str(exc)}
        else:
            manifest["npz_header_gate"] = {"status": "FAIL", "reason": str(exc), "headers": []}
        manifest["stop_code"] = "SOURCE_OR_SPLIT_UNRESOLVED"
        _append_log(log_path, f"- STOP SOURCE_OR_SPLIT_UNRESOLVED before count values: {exc}")
        persist("SOURCE_OR_SPLIT_UNRESOLVED")
        return manifest

    # Include the metadata phase in the same one-shot wall/RSS budget.
    for spec in source_specs:
        before = current_snapshot()
        check = {"source_id": str(spec["source_id"]), "phase": "before", **before}
        manifest["resource_checks"].append(check)
        stop_reason = _budget_stop(before)
        if stop_reason:
            manifest["stop_code"] = stop_reason
            _append_log(log_path, f"- STOP {stop_reason} before {spec['source_id']}; no count values read for this source.")
            persist("INCOMPLETE_RESOURCE_STOP")
            return manifest

        source_id = str(spec["source_id"])
        manifest["attempted_sources"].append(source_id)
        key = expected_npz_key(source_id)
        try:
            raw = load_member(Path(counts_path), key)
            source_summary = summarize_source_counts(
                raw, source_id, str(spec["label"]), int(spec["train_pairs"])
            )
            summary["per_source"].append(source_summary)
            del raw
        except (OSError, ValueError, KeyError, EOFError, zipfile.BadZipFile) as exc:
            after_failure = current_snapshot()
            manifest["resource_checks"].append(
                {"source_id": source_id, "phase": "after_failed", **after_failure}
            )
            manifest["stop_code"] = "COUNT_VALUE_MISMATCH"
            manifest["source_failure"] = {"source_id": source_id, "reason": str(exc)}
            _append_log(log_path, f"- STOP COUNT_VALUE_MISMATCH for {source_id}: {exc}")
            persist("INCOMPLETE_COUNT_VALUE_MISMATCH")
            return manifest
        except MemoryError as exc:
            after_failure = current_snapshot()
            manifest["resource_checks"].append(
                {"source_id": source_id, "phase": "after_failed", **after_failure}
            )
            manifest["stop_code"] = _budget_stop(after_failure) or "MEMORY_ERROR"
            manifest["source_failure"] = {"source_id": source_id, "reason": str(exc)}
            _append_log(log_path, f"- STOP {manifest['stop_code']} while mapping {source_id}.")
            persist("INCOMPLETE_RESOURCE_STOP")
            return manifest

        after = current_snapshot()
        manifest["resource_checks"].append(
            {"source_id": source_id, "phase": "after", **after}
        )
        _json_dump(summary_path, summary)
        stop_reason = _budget_stop(after)
        if stop_reason:
            manifest["stop_code"] = stop_reason
            _append_log(log_path, f"- STOP {stop_reason} after {source_id}; completed source retained.")
            persist("INCOMPLETE_RESOURCE_STOP")
            return manifest
        _append_log(log_path, f"- Source {source_id} mapped; count payload released.")
        _json_dump(manifest_path, manifest)

    _append_log(log_path, "- All three documented train sources mapped independently.")
    persist("DESCRIPTIVE_MAPPING_COMPLETE")
    return manifest


def _default_paths(repo_root: Path) -> tuple[Path, dict[str, Path]]:
    return (
        repo_root / COUNTS_REL,
        {name: repo_root / rel for name, rel in PROVENANCE_REL.items()},
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="run the frozen mapping")
    parser.add_argument(
        "--out-root", default="workspace/gf32_source_map_6f821d0b",
        help="fresh output root from the frozen packet",
    )
    args = parser.parse_args(argv)
    if not args.execute:
        print("DRY_RUN: no provenance or NPZ reads; no files written.")
        print(f"Frozen command: {EXACT_COMMAND}")
        return 0

    repo_root = Path(__file__).resolve().parents[4]
    if _norm_slashes(args.out_root) != "workspace/gf32_source_map_6f821d0b":
        print("STOP: --out-root must match the frozen root.", file=sys.stderr)
        return 2
    counts_path, provenance_paths = _default_paths(repo_root)
    out_root = repo_root / args.out_root
    try:
        manifest = run_batch(
            counts_path=counts_path,
            provenance_paths=provenance_paths,
            out_root=out_root,
        )
    except FileExistsError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if manifest.get("status") == "DESCRIPTIVE_MAPPING_COMPLETE" else 1


if __name__ == "__main__":  # pragma: no cover - exercised by CLI smoke test
    raise SystemExit(main())
