"""V13 R3 legacy drift audit — ``formal-nonbinary-ldpc-v13-r3-legacy-drift-audit``.

User-authorized execution on the three ``2026-01-21`` Type2 legacy sources that
D0 rejected as fresh-confirmation input and D5 flagged as ``drift_exceeded``.

Frozen claim boundary (design.md section 1): this lane can only emit
``legacy_drift_audit``.  ``fresh_confirmed`` / ``promotion`` / ``qualification``
are never states here.  The frozen R3 candidate is unchanged: codebook
``nbldpc_v13_r3_code_v1``, QSC p=.20, flooding FFT-QSPA, max_iter=100.

The module imports the candidate lazily (only inside the production decode
path) so the read-only verifier and test-only lanes never import a decoder.
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import pandas as pd

# ------------------------------------------------------------------ frozen constants

METHOD = "nbldpc_v13_r3_legacy_drift_audit"
RUN_ID = "v13r3_legacy_drift_audit_20260816"
TEST_RUN_ID = "nbldpc_v13r3_legacy_drift_audit_test_v1"

Q, N, M = 1024, 256, 170
P = 0.20
MAX_ITER = 100
FRAMES_PER_SOURCE = 64

CLAIM_BOUNDARY = "legacy_drift_audit"
DATA_INTAKE_STATE = "data_intake_rejected_for_fresh_confirmation"
DRIFT_PRECHECK_STATE = "drift_exceeded"

SCHEMA_REPORT = "nbldpc_v13r3_legacy_drift_audit_report_v1"
SCHEMA_REPORT_TEST = "nbldpc_v13r3_legacy_drift_audit_report_test_v1"
SCHEMA_MANIFEST = "nbldpc_v13r3_legacy_drift_audit_manifest_v1"
SCHEMA_MANIFEST_TEST = "nbldpc_v13r3_legacy_drift_audit_manifest_test_v1"
SCHEMA_TELEMETRY = "nbldpc_v13r3_legacy_drift_audit_telemetry_v1"
SCHEMA_TELEMETRY_TEST = "nbldpc_v13r3_legacy_drift_audit_telemetry_test_v1"

OUTCOME_COLUMNS = ("source_tag", "frame_id", "raw_ser", "status", "reason",
                   "iterations", "exact_correct")
ARTIFACTS = ("audit_outcomes.csv", "decoder_telemetry.jsonl",
             "audit_report.json", "audit_run_manifest.json")

SELECTION_RULE = ("first 64 complete frames per source in ascending frame_id "
                  "(0..63); no randomisation, no replacement")

# ------------------------------------------------------------------ helpers


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha(value: Any) -> str:
    return _sha_bytes(_compact(value))


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _put_exclusive(path: Path, data: bytes) -> None:
    path.open("xb").write(data)


def _json_read(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    doc = json.loads(raw)
    if not isinstance(doc, dict) or _compact(doc) != raw:
        raise ValueError(f"noncanonical json: {path}")
    return doc


def _test_schema(doc: Mapping[str, Any]) -> bool:
    return bool(str(doc.get("schema", "")).endswith("_test_v1"))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _git_head(path: Path) -> str | None:
    try:
        return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True,
                              timeout=20).stdout.strip()
    except Exception:
        return None


# ------------------------------------------------------------------ pairs validation


def _read_pairs(parquet: Path) -> pd.DataFrame:
    try:
        df = pd.read_parquet(parquet)
    except Exception as exc:
        raise ValueError(f"parquet unreadable: {type(exc).__name__}: {exc}") from exc
    required = {"frame_id", "pair_idx", "alice_symbol", "bob_symbol"}
    if set(df.columns) != required:
        raise ValueError(f"pairs columns must be exactly {sorted(required)}; "
                         f"got {sorted(df.columns)}")
    if not all(pd.api.types.is_integer_dtype(df[col]) for col in required):
        raise ValueError("pairs columns must be integer dtypes")
    if int(df.isna().sum().sum()) != 0:
        raise ValueError("pairs table contains nulls")
    for col in ("alice_symbol", "bob_symbol"):
        if int(df[col].min()) < 0 or int(df[col].max()) >= Q:
            raise ValueError(f"{col} symbols outside [0, {Q})")
    return df


def validate_pairs_table(parquet: Any) -> dict[str, Any]:
    """Read-only structural validation of one D4 legacy pairs table.

    Every frame must be complete (exactly 256 rows, pair_idx 0..255 unique).
    Returns the sorted complete frame ids and aggregate diagnostics.
    """
    df = _read_pairs(Path(parquet))
    sizes = df.groupby("frame_id", sort=True).size()
    bad_size = int((sizes != N).sum())
    nunique = df.groupby("frame_id", sort=True)["pair_idx"].nunique()
    bad_idx = int((nunique != N).sum())
    if bad_size or bad_idx:
        raise ValueError(f"incomplete frames found: bad_size={bad_size}, bad_idx={bad_idx}")
    ids = sorted(int(v) for v in sizes.index)
    if ids != list(range(len(ids))):
        raise ValueError("frame_id is not a contiguous 0..n-1 sequence")
    return {"parquet": str(Path(parquet)), "complete_frames": len(ids),
            "frame_ids": ids,
            "sha256": _sha_bytes(Path(parquet).read_bytes())}


def selected_frame_ids(source: Mapping[str, Any], count: int | None = FRAMES_PER_SOURCE) -> list[int]:
    """Frozen selection: first ``count`` complete frames by ascending frame_id.

    ``count=None`` selects **all** complete frames (full-data extension).
    """
    ids = list(source.get("frame_ids", []))
    if count is None:
        return ids
    if len(ids) < count:
        raise ValueError(f"insufficient legacy frames: {len(ids)} < {count}")
    return ids[:count]


def _frames_for_ids(df: pd.DataFrame, ids: Sequence[int]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for fid in ids:
        sub = df[df["frame_id"] == fid].sort_values("pair_idx")
        if len(sub) != N:
            raise ValueError(f"frame {fid} has {len(sub)} rows, expected {N}")
        alice = sub["alice_symbol"].to_numpy(dtype=np.int64)
        bob = sub["bob_symbol"].to_numpy(dtype=np.int64)
        if len(alice) != N or len(bob) != N:
            raise ValueError(f"frame {fid} array length mismatch")
        frames.append({"frame_id": int(fid),
                       "alice": alice, "bob": bob,
                       "raw_ser": float((alice != bob).mean())})
    return frames


# ------------------------------------------------------------------ decode


def _decode_frame(frame: Mapping[str, Any], manifest: Mapping[str, Any],
                  matrix: Any) -> dict[str, Any]:
    """Lazy import boundary: production R3 decoder, unchanged public entrypoint."""
    from . import nonbinary_v13_r3_candidate as r3
    from .nonbinary_field import GF2mField
    from .nonbinary_qspa import nonbinary_syndrome
    field = GF2mField.create(Q)
    syndrome = nonbinary_syndrome(matrix, frame["alice"], field)
    return r3.decode_r3_frame(frame["bob"], syndrome, manifest, matrix, hook=True)


def _decode_frame_prebuilt(frame: Mapping[str, Any], manifest: Mapping[str, Any],
                           matrix: Any, *, max_iter: int = MAX_ITER) -> dict[str, Any]:
    """Production decode using the already-built/verified R3 matrix.

    This mirrors ``nonbinary_v13_r3_candidate.decode_r3_frame`` exactly but
    skips the per-frame ``build_r3_codebook()`` reconstruction.  The codebook
    is verified once by the caller; the decoding math is the same frozen
    flooding FFT-QSPA mirror (``_hooked_decode_flooding``).
    """
    from .nonbinary_field import GF2mField
    from .nonbinary_qspa import (_declared_dense_bytes, _symbols,
                                 nonbinary_syndrome, qsc_symbol_priors)
    from .nonbinary_v13_diagnostics import (_hooked_decode_flooding, _matrix_edges,
                                            _telemetry_summary)
    field = GF2mField.create(Q)
    syndrome = nonbinary_syndrome(matrix, frame["alice"], field)
    bob = _symbols(frame["bob"], Q, expected=N)
    disclosed = _symbols(syndrome, Q, expected=M)
    priors = qsc_symbol_priors(bob, Q, P)
    checks, variables = _matrix_edges(matrix)
    edge_count = sum(map(len, checks))
    declared = _declared_dense_bytes(N, edge_count, Q)
    codebook_id = str(manifest["canonical_sha256"])
    result, records, decoded_words = _hooked_decode_flooding(
        bob, disclosed, matrix, checks, variables, priors, field,
        M, codebook_id, declared, max_iter=int(max_iter))
    return {"result": result,
            "telemetry": _telemetry_summary(records, result, decoded_words)}


def _outcome_row(source_tag: str, frame: Mapping[str, Any], result: Mapping[str, Any]) -> dict[str, Any]:
    status = str(result.get("status", "unclassified"))
    reason: str
    exact = False
    if status == "syndrome_consistent":
        decoded = tuple(int(v) for v in result.get("decoded_symbols", ()))
        alice = tuple(int(v) for v in frame["alice"])
        reason = "exact_correct" if decoded == alice else "exact_mismatch"
        exact = reason == "exact_correct"
    else:
        reason = str(result.get("reason", "no_decoded_word"))
    return {"source_tag": source_tag, "frame_id": int(frame["frame_id"]),
            "raw_ser": float(frame["raw_ser"]), "status": status,
            "reason": reason, "iterations": int(result.get("iterations", 0)),
            "exact_correct": bool(exact)}


def _report_doc(run_id: str, sources: Sequence[Mapping[str, Any]],
                test_only: bool, command: str, manifest_sha256: str,
                manifest_id: str, frames_per_source: int | None,
                chunk_index: int = 0, chunk_count: int = 1) -> dict[str, Any]:
    rows = [row for src in sources for row in src["outcome_rows"]]
    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[str(row["status"])] = status_counts.get(str(row["status"]), 0) + 1
    source_records = []
    for src in sources:
        srows = src["outcome_rows"]
        counts: dict[str, int] = {}
        for row in srows:
            counts[str(row["status"])] = counts.get(str(row["status"]), 0) + 1
        exact = int(sum(1 for r in srows if r["exact_correct"]))
        ser = [float(r["raw_ser"]) for r in srows]
        source_records.append({
            "source_tag": str(src["source_tag"]),
            "parquet": str(src["parquet"]),
            "parquet_sha256": str(src["source"]["sha256"]),
            "frames_available": int(src["source"]["complete_frames"]),
            "frames_attempted": len(srows),
            "exact_correct": exact,
            "exact_mismatch": int(sum(1 for r in srows
                                      if r["reason"] == "exact_mismatch")),
            "status_counts": counts,
            "raw_ser_mean": float(np.mean(ser)) if ser else None,
            "raw_ser_min": float(np.min(ser)) if ser else None,
            "raw_ser_max": float(np.max(ser)) if ser else None,
        })
    exact_total = int(sum(1 for r in rows if r["exact_correct"]))
    chunk_note = "" if chunk_count <= 1 else f"; chunk {chunk_index + 1}/{chunk_count}"
    return {
        "schema": SCHEMA_REPORT_TEST if test_only else SCHEMA_REPORT,
        "run_id": run_id,
        "created_at_utc": _now(),
        "claim_boundary": CLAIM_BOUNDARY,
        "fresh_confirmed": False,
        "promotion": False,
        "qualification": False,
        "observed_fresh_correction": False,
        "data_intake_state": DATA_INTAKE_STATE,
        "drift_precheck_state": DRIFT_PRECHECK_STATE,
        "method": METHOD,
        "decoder_binding": {
            "codebook": "nbldpc_v13_r3_code_v1",
            "manifest_id": manifest_id,
            "q": Q, "n": N, "m": M, "p": P, "max_iter": MAX_ITER,
        },
        "selection_rule": SELECTION_RULE + ("" if frames_per_source is not None
                                         else "; full-data extension: all complete frames") + chunk_note,
        "frames_per_source": frames_per_source,
        "attempted_frames": len(rows),
        "exact_correct_frames": exact_total,
        "status_counts": status_counts,
        "sources": source_records,
        "verdict": "legacy_drift_audit_completed"
                   if len(rows) == sum(len(src["frames"]) for src in sources)
                   else "invalid_audit_execution",
        "command": command,
        "audit_run_manifest_sha256": manifest_sha256,
    }


def _manifest_doc(run_id: str, sources: Sequence[Mapping[str, Any]],
                  test_only: bool, command: str, artifact_index: Mapping[str, Any],
                  release_head: str | None, manifest_id: str,
                  frames_per_source: int | None,
                  chunk_index: int = 0, chunk_count: int = 1) -> dict[str, Any]:
    comparison_head = _git_head(_repo_root())
    chunk_note = "" if chunk_count <= 1 else f"; chunk {chunk_index + 1}/{chunk_count}"
    return {
        "schema": SCHEMA_MANIFEST_TEST if test_only else SCHEMA_MANIFEST,
        "run_id": run_id,
        "created_at_utc": _now(),
        "command": command,
        "claim_boundary": CLAIM_BOUNDARY,
        "selection_rule": SELECTION_RULE + ("" if frames_per_source is not None
                                         else "; full-data extension: all complete frames") + chunk_note,
        "frames_per_source": frames_per_source,
        "sources": [{
            "source_tag": str(src["source_tag"]),
            "parquet": str(src["parquet"]),
            "parquet_sha256": str(src["source"]["sha256"]),
            "frames_available": int(src["source"]["complete_frames"]),
            "selected_frame_ids": [int(f["frame_id"]) for f in src["frames"]],
        } for src in sources],
        "git": {"comparison_head": comparison_head,
                "release_head": release_head},
        "platform": {"system": platform.system(), "python": platform.python_version()},
        "decoder_binding": {
            "codebook": "nbldpc_v13_r3_code_v1",
            "manifest_id": manifest_id,
            "q": Q, "n": N, "m": M, "p": P, "max_iter": MAX_ITER,
        },
        "artifact_index": dict(artifact_index),
    }


def run_audit(output_dir: Any, *, parquet_paths: Sequence[Any],
              run_id: str = RUN_ID, command: str = "",
              _test_only: bool = False, production_authorized: bool = False,
              all_frames: bool = False,
              progress_every: int = 0,
              chunk_index: int = 0,
              chunk_count: int = 1,
              decode_fn: Callable[[Mapping[str, Any], Mapping[str, Any], Any],
                                  dict[str, Any]] | None = None) -> dict[str, Any]:
    """Execute the legacy drift audit once and write the additive package.

    ``decode_fn`` exists only for the test lane; production always uses the
    real frozen R3 candidate via :func:`_decode_frame`.
    """
    if not _test_only and not production_authorized:
        raise ValueError("legacy drift audit production execution requires "
                         "--authorized --production (main-thread authorization)")
    out = Path(output_dir).resolve()
    if out.exists():
        raise FileExistsError("fresh additive output root required")
    if not parquet_paths:
        raise ValueError("at least one parquet path is required")
    out.mkdir(parents=True)
    written: list[Path] = []
    try:
        sources: list[dict[str, Any]] = []
        for path in parquet_paths:
            parquet = Path(path).resolve()
            source = validate_pairs_table(parquet)
            tag = parquet.parent.name
            ids = selected_frame_ids(source, None if all_frames else FRAMES_PER_SOURCE)
            if chunk_count > 1:
                if chunk_index < 0 or chunk_index >= chunk_count:
                    raise ValueError("chunk_index out of range")
                chunk_size = (len(ids) + chunk_count - 1) // chunk_count
                ids = ids[chunk_index * chunk_size:(chunk_index + 1) * chunk_size]
            df = _read_pairs(parquet)
            frames = _frames_for_ids(df, ids)
            sources.append({"source_tag": tag, "parquet": parquet,
                            "source": source, "frames": frames,
                            "outcome_rows": [], "telemetry_rows": []})
        if len(sources) != 3:
            raise ValueError(f"exactly three legacy sources required; got {len(sources)}")

        # Frozen decoder binding: production builds and verifies the R3
        # codebook once before any decode; the test lane uses a stub binding
        # and never imports a decoder.
        if decode_fn is None:
            from . import nonbinary_v13_r3_candidate as r3
            manifest, matrix = r3.build_r3_codebook()
            verified = r3.verify_r3_codebook(manifest, matrix)
            if verified.get("status") != "ok":
                raise ValueError("R3 codebook binding mismatch")
            manifest_id = str(manifest["canonical_sha256"])
        else:
            manifest, matrix = {
                "canonical_sha256": "0" * 64,
                "method": "test_stub_codebook_v1",
            }, None
            manifest_id = str(manifest["canonical_sha256"])

        decoded_total = 0
        for src in sources:
            for frame in src["frames"]:
                try:
                    hook = (decode_fn or _decode_frame_prebuilt)(frame, manifest, matrix)
                    result = hook.get("result", hook) if isinstance(hook, dict) else hook
                    if not isinstance(result, dict):
                        raise TypeError("decode callback must return a result dict")
                    row = _outcome_row(str(src["source_tag"]), frame, result)
                    telemetry = hook.get("telemetry") if isinstance(hook, dict) else None
                except Exception as exc:
                    row = {"source_tag": str(src["source_tag"]),
                           "frame_id": int(frame["frame_id"]),
                           "raw_ser": float(frame["raw_ser"]),
                           "status": "decoder_exception",
                           "reason": f"{type(exc).__name__}: {exc}",
                           "iterations": 0, "exact_correct": False}
                    telemetry = None
                src["outcome_rows"].append(row)
                src["telemetry_rows"].append({
                    "schema": SCHEMA_TELEMETRY_TEST if _test_only else SCHEMA_TELEMETRY,
                    "run_id": run_id,
                    "source_tag": str(src["source_tag"]),
                    "frame_id": int(frame["frame_id"]),
                    "status": row["status"],
                    "iterations": row["iterations"],
                    "telemetry": telemetry,
                })
                decoded_total += 1
                if progress_every and decoded_total % progress_every == 0:
                    print(json.dumps({"progress": decoded_total,
                                      "source_tag": str(src["source_tag"]),
                                      "frame_id": int(frame["frame_id"])},
                                     sort_keys=True), flush=True)

        # Write outcomes CSV and telemetry JSONL, then bind them in the manifest.
        outcomes_path = out / ARTIFACTS[0]
        with outcomes_path.open("x", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(OUTCOME_COLUMNS), lineterminator="\n")
            writer.writeheader()
            for src in sources:
                for row in src["outcome_rows"]:
                    writer.writerow(row)
        written.append(outcomes_path)
        telemetry_path = out / ARTIFACTS[1]
        with telemetry_path.open("x", encoding="utf-8") as fh:
            for src in sources:
                for row in src["telemetry_rows"]:
                    fh.write(_compact(row).decode("ascii") + "\n")
        written.append(telemetry_path)

        artifact_index = {
            ARTIFACTS[0]: {"sha256": _sha_bytes(outcomes_path.read_bytes()),
                           "bytes": outcomes_path.stat().st_size},
            ARTIFACTS[1]: {"sha256": _sha_bytes(telemetry_path.read_bytes()),
                           "bytes": telemetry_path.stat().st_size},
        }
        release_root = Path("D:/Code/HD-QKD_Polar_Release")
        release_head = _git_head(release_root) if release_root.exists() else None
        frames_per_source = None if all_frames else FRAMES_PER_SOURCE
        manifest_doc = _manifest_doc(run_id, sources, _test_only, command,
                                     artifact_index, release_head, manifest_id,
                                     frames_per_source, chunk_index, chunk_count)
        manifest_path = out / ARTIFACTS[3]
        _put_exclusive(manifest_path, _compact(manifest_doc))
        written.append(manifest_path)
        report_doc = _report_doc(run_id, sources, _test_only, command,
                                 _sha_bytes(manifest_path.read_bytes()),
                                 manifest_id, frames_per_source,
                                 chunk_index, chunk_count)
        report_path = out / ARTIFACTS[2]
        _put_exclusive(report_path, _compact(report_doc))
        written.append(report_path)
        return {"output_directory": str(out), "run_id": run_id,
                "attempted_frames": len([r for s in sources for r in s["outcome_rows"]]),
                "verdict": report_doc["verdict"],
                "claim_boundary": report_doc["claim_boundary"]}
    except Exception:
        for path in written:
            if path.exists():
                path.unlink()
        if out.exists() and not any(out.iterdir()):
            out.rmdir()
        raise


# ------------------------------------------------------------------ verify


def _verify_outcomes(path: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    expected = sum(len(src["selected_frame_ids"]) for src in manifest["sources"])
    rows = list(csv.DictReader(path.open("r", encoding="utf-8", newline="")))
    selected = {str(src["source_tag"]): [int(i) for i in src["selected_frame_ids"]]
                for src in manifest["sources"]}
    got: dict[str, list[int]] = {}
    for row in rows:
        got.setdefault(row["source_tag"], []).append(int(row["frame_id"]))
    problems = []
    if len(rows) != expected:
        problems.append(f"outcome rows {len(rows)} != {expected}")
    for src in manifest["sources"]:
        tag = str(src["source_tag"])
        if got.get(tag) != selected[tag]:
            problems.append(f"source {tag} frame ids do not match pre-registration")
    return {"ok": not problems, "rows": len(rows), "problems": problems}


def verify_package(output_dir: Any) -> dict[str, Any]:
    """Read-only verification: hashes, row counts, selection, claim boundary."""
    out = Path(output_dir)
    manifest = _json_read(out / ARTIFACTS[3])
    test_only = _test_schema(manifest)
    report = _json_read(out / ARTIFACTS[2])
    problems: list[str] = []
    checks: list[dict[str, Any]] = []

    if manifest["claim_boundary"] != CLAIM_BOUNDARY:
        problems.append("manifest claim_boundary != legacy_drift_audit")
    if report["claim_boundary"] != CLAIM_BOUNDARY:
        problems.append("report claim_boundary != legacy_drift_audit")
    for key in ("fresh_confirmed", "promotion", "qualification"):
        if report.get(key) is not False:
            problems.append(f"report {key} is not false")
    if report.get("verdict") != "legacy_drift_audit_completed":
        problems.append(f"report verdict unexpected: {report.get('verdict')}")
    if manifest["decoder_binding"]["manifest_id"] != report["decoder_binding"]["manifest_id"]:
        problems.append("decoder binding manifest_id mismatch between report and manifest")
    manifest_path = out / ARTIFACTS[3]
    if report.get("audit_run_manifest_sha256") != _sha_bytes(manifest_path.read_bytes()):
        problems.append("report does not bind the current manifest bytes")

    for name, meta in manifest["artifact_index"].items():
        path = out / name
        if not path.exists():
            checks.append({"artifact": name, "ok": False, "reason": "missing"})
            problems.append(f"{name} missing")
            continue
        data = path.read_bytes()
        ok = _sha_bytes(data) == meta["sha256"] and path.stat().st_size == meta["bytes"]
        checks.append({"artifact": name, "ok": ok,
                       "sha256_ok": _sha_bytes(data) == meta["sha256"],
                       "bytes_ok": path.stat().st_size == meta["bytes"]})
        if not ok:
            problems.append(f"{name} hash/size mismatch")

    outcome_check = _verify_outcomes(out / ARTIFACTS[0], manifest)
    checks.append({"artifact": ARTIFACTS[0], **outcome_check})
    if not outcome_check["ok"]:
        problems.extend(outcome_check["problems"])

    for src in manifest["sources"]:
        path = Path(src["parquet"])
        if not path.exists():
            problems.append(f"parquet missing: {src['parquet']}")
        elif _sha_bytes(path.read_bytes()) != src["parquet_sha256"]:
            problems.append(f"parquet sha256 mismatch: {src['source_tag']}")

    result = {
        "schema": "nbldpc_v13r3_legacy_drift_audit_verify_v1",
        "output_directory": str(out),
        "run_id": manifest["run_id"],
        "test_only": test_only,
        "claim_boundary": manifest["claim_boundary"],
        "ok": not problems,
        "problems": problems,
        "checks": checks,
    }
    return result
