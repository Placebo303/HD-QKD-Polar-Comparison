"""Fresh, fail-closed synthetic-v3 qualification evidence package."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from ..formal_ir.cascade import run_cascade_formal
from ..formal_ir.ldpc import calibrate_rates, materialize_codebooks, run_ldpc_formal, verify_codebook_manifest
from ..formal_ir.shared import FORMAL_ARTIFACTS, FORMAL_STATUSES, canonical_event, locked_seed_bits, materialize_seed_record, transcript_summary, verification_union_bound

RUN_ID = "20260725_v3_synthetic"
Q, N, SEED_BITS = 1024, 64, 703
ROOT = Path("comparison_bench/outputs_comparison/formal_ir_methods") / RUN_ID
METHODS = ("cascade_formal_v1", "ldpc_formal_v1")
TOP_LEVEL = set(FORMAL_ARTIFACTS) | {"codebooks"}


def _sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def _now() -> str: return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
def _compact(value: Any) -> bytes: return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
def _write_x(path: Path, data: bytes) -> None:
    with path.open("xb") as handle: handle.write(data)
def _json_x(path: Path, value: Any) -> None: _write_x(path, json.dumps(value, indent=2, sort_keys=True).encode("utf-8") + b"\n")


def _flip(alice: np.ndarray, noise_seed: int, p: float) -> np.ndarray:
    rng = np.random.Generator(np.random.PCG64(noise_seed))
    flips = rng.random((*alice.shape, 10)) < p
    masks = (flips.astype(np.int64) * (1 << np.arange(9, -1, -1))).sum(axis=2)
    return np.asarray(alice, dtype=np.int64) ^ masks


def _batches() -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """The only Alice RNG: four canonical sequential calls, never reused elsewhere."""
    alice_rng = np.random.Generator(np.random.PCG64(2026072501))
    alice = [alice_rng.integers(0, Q, size=(32, N), dtype=np.int64) for _ in range(4)]
    return {
        "p01_calibration": (alice[0], _flip(alice[0], 2026072513, .01)),
        "p01_qualification": (alice[1], _flip(alice[1], 2026072511, .01)),
        "p02_calibration": (alice[2], _flip(alice[2], 2026072514, .02)),
        "p02_qualification": (alice[3], _flip(alice[3], 2026072512, .02)),
    }


def _ids() -> list[str]:
    return ([f"synthetic_q1024_p001_qualification_f{i:03d}" for i in range(32)] +
            [f"synthetic_q1024_p002_qualification_f{i:03d}" for i in range(32)])


def _plan() -> dict[str, Any]:
    batches = _batches(); ids = _ids()
    order = np.random.Generator(np.random.PCG64(2026072531)).permutation(64)
    ordered = [ids[int(index)] for index in order]
    frames = [{"frame_id": frame_id, "verification_seed": materialize_seed_record(SEED_BITS)} for frame_id in ordered]
    return {
        "run_id": RUN_ID, "synthetic_only": True, "dimension": Q, "frame_len_symbols": N,
        "methods": list(METHODS), "mapping": "gray",
        "seeds": {"alice_symbols": 2026072501, "noise_p01_calibration": 2026072513,
                  "noise_p01_qualification": 2026072511, "noise_p02_calibration": 2026072514,
                  "noise_p02_qualification": 2026072512, "cascade_base": 2026072521,
                  "frame_order": 2026072531},
        "caps": {"frame_s": 5, "total_s": 600, "ldpc_max_iter": 50,
                 "cascade": {"events": 100000, "corrections": 4096, "queue_pops": 10000}},
        "synthetic_generation": {name: _sha(a.tobytes() + b.tobytes()) for name, (a, b) in batches.items()},
        "canonical_qualification_ids": ids, "qualification_execution_order": ordered,
        "qualification_execution_order_sha256": _sha(_compact(ordered)), "frames": frames,
    }


def _git_provenance() -> dict[str, Any]:
    def capture(*args: str) -> bytes: return subprocess.run(["git", *args], cwd=Path.cwd(), check=True, capture_output=True).stdout
    status = capture("status", "--porcelain=v1", "--untracked-files=all")
    return {"commit": capture("rev-parse", "HEAD").decode("ascii").strip(), "status_porcelain_v1_hex": status.hex(), "status_porcelain_v1_sha256": _sha(status), "dirty": bool(status)}


def _deterministic_preflight() -> dict[str, Any]:
    base = Path(tempfile.mkdtemp(prefix="formal-ir-v3-preflight-"))
    command = [sys.executable, "-m", "pytest", "comparison_bench/tests/test_formal_verification.py", "comparison_bench/tests/test_cascade_formal.py", "comparison_bench/tests/test_ldpc_formal.py", "-q", "-p", "no:cacheprovider", "--basetemp", str(base)]
    result = subprocess.run(command, cwd=Path.cwd(), env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True)
    evidence = result.stdout + b"\n---STDERR---\n" + result.stderr
    import re
    match = re.search(r"(\d+) passed", result.stdout.decode("utf-8", "replace"))
    return {"command": command, "exit_code": result.returncode, "passed_count": int(match.group(1)) if match else None,
            "output_sha256": _sha(evidence), "passed": result.returncode == 0 and match is not None}


def _write_csv_x(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["method", "status", "attempted", "denominator_included", "failure_reason"]
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for row in rows: writer.writerow({key: json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else value for key, value in row.items()})


def _artifact_hashes(output: Path) -> dict[str, str]:
    # Report binds this manifest, so including it here would make the DAG circular.
    names = ("pre_run_plan.json", "formal_frame_outcomes.csv", "formal_transcript.jsonl", "formal_codebook_manifest.json")
    return {name: _sha((output / name).read_bytes()) for name in names if (output / name).is_file()}


def _finalize_failure(output: Path, *, exc: BaseException, provenance: dict[str, Any] | None, preflight: dict[str, Any] | None, utc_started: str) -> None:
    """Only fills absent evidence files; it never repairs or overwrites prior bytes."""
    reason = f"{type(exc).__name__}: {exc}"
    if not (output / "pre_run_plan.json").exists(): _json_x(output / "pre_run_plan.json", {"run_id": RUN_ID, "plan_status": "incomplete", "stop_reason": reason})
    if not (output / "formal_frame_outcomes.csv").exists(): _write_csv_x(output / "formal_frame_outcomes.csv", [])
    if not (output / "formal_transcript.jsonl").exists(): _write_x(output / "formal_transcript.jsonl", b"")
    if not (output / "formal_codebook_manifest.json").exists(): _json_x(output / "formal_codebook_manifest.json", {"generator_id": "unavailable", "entries": []})
    if not (output / "formal_run_manifest.json").exists():
        _json_x(output / "formal_run_manifest.json", {"run_id": RUN_ID, "run_status": "non_promoted", "stop_reason": reason,
            "exception": {"class": type(exc).__name__, "message": str(exc)}, "git": provenance, "deterministic_preflight": preflight,
            "utc_started": utc_started, "utc_finished": _now(), "artifacts": _artifact_hashes(output), "indexed_codebooks": {}})
    if not (output / "formal_qualification_report.json").exists():
        _json_x(output / "formal_qualification_report.json", {"run_id": RUN_ID, "run_status": "non_promoted", "stop_reason": reason,
            "exception": {"class": type(exc).__name__, "message": str(exc)}, "promotion_gates": {},
            "deterministic_preflight": preflight, "formal_run_manifest_sha256": _sha((output / "formal_run_manifest.json").read_bytes())})


def _gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    good = sum(row["status"] == "verified_success" for row in rows)
    allowed = {"verified_success", "verify_failed", "decode_failed", "syndrome_inconsistent", "aborted_resource_limit"}
    bad = sum(row["status"] not in allowed for row in rows)
    return {"requested": 32, "verified_success": good, "unclassified_internal_provenance_accounting_failures": bad, "promoted": good >= 31 and bad == 0}


def run(output: Path) -> None:
    if output.exists(): raise FileExistsError("fresh output required")
    provenance = _git_provenance()  # required before the output directory exists
    output.mkdir(parents=True)
    utc_started = _now()
    preflight: dict[str, Any] | None = None
    try:
        # The plan itself is evidence: if its generation or exclusive write fails,
        # finalization must retain that partial state and fill the other five files.
        plan = _plan(); _json_x(output / "pre_run_plan.json", plan)
        preflight = _deterministic_preflight()
        if not preflight["passed"]: raise RuntimeError("deterministic_preflight_failed")
        codebook = materialize_codebooks(output, allow_plan_only=True)
        entries = {(entry["rate_id"], entry["plane_id"]): entry for entry in codebook["entries"]}
        raw = {identity: (output / "codebooks" / entry["filename"]).read_bytes() for identity, entry in entries.items()}
        batches = _batches(); calibrations: dict[str, Any] = {}
        for label, p in (("p01", .01), ("p02", .02)):
            alice, bob = batches[f"{label}_calibration"]
            calibrations[label] = calibrate_rates({f"synthetic_p{p:.2f}": (alice, bob)},
                sacrificed_frame_keys={f"synthetic_p{p:.2f}": [f"{label}_calibration_{i:02d}" for i in range(32)]},
                calibration_role="sacrificed_tuning_only", mapping="gray", source_bytes=alice.tobytes() + bob.tobytes(), dimension=Q)
        rows: list[dict[str, Any]] = []; emitted: list[dict[str, Any]] = []; started = time.monotonic()
        for locked in plan["frames"]:
            if time.monotonic() - started >= 600: raise TimeoutError("total_s")
            frame = locked["frame_id"]; label, p = ("p01", .01) if "p001" in frame else ("p02", .02)
            index = int(frame[-3:]); alice, bob = batches[f"{label}_qualification"]
            dataset = f"synthetic_p{p:.2f}"
            for method in METHODS:
                result = (run_cascade_formal(alice[index], bob[index], dimension=Q, dataset_id=dataset, frame_id=frame, mapping="gray", base_seed=2026072521, locked_seed=locked["verification_seed"], caps={**plan["caps"]["cascade"], "wall_s": plan["caps"]["frame_s"]})
                    if method == METHODS[0] else run_ldpc_formal(alice[index], bob[index], dimension=Q, dataset_id=dataset, frame_id=frame, mapping="gray", locked_seed=locked["verification_seed"], frozen_calibration=calibrations[label], codebook_entries=entries, codebook_bytes=raw))
                group = b"".join(canonical_event(event) for event in result["events"])
                if result["outcome"].get("transcript_sha256") != _sha(group): raise ValueError("formal method original transcript hash mismatch")
                row = dict(result["outcome"]); row.update({"stratum_p": p, "qualification_role": "qualification", "plan_frame_id": frame,
                    "transcript_bytes_len": len(group), "transcript_bytes_sha256": _sha(group)})
                rows.append(row); emitted.extend(result["events"])
        transcript = b"".join(canonical_event(event) for event in emitted)
        _write_x(output / "formal_transcript.jsonl", transcript); _write_csv_x(output / "formal_frame_outcomes.csv", rows)
        groups: dict[str, list[dict[str, Any]]] = {}
        for row in rows: groups.setdefault(f"{row['method']}|{row['stratum_p']:.2f}", []).append(row)
        report = {"run_id": RUN_ID, "run_status": "completed", "deterministic_preflight": preflight,
                  "promotion_gates": {key: _gate(value) for key, value in groups.items()}}
        runner = Path(__file__); modules = {"runner": runner, "shared": runner.parent.parent / "formal_ir" / "shared.py", "cascade": runner.parent.parent / "formal_ir" / "cascade.py", "ldpc": runner.parent.parent / "formal_ir" / "ldpc.py"}
        manifest = {"run_id": RUN_ID, "run_status": "completed", "argv": list(sys.argv), "git": provenance,
            "utc_started": utc_started, "utc_finished": _now(), "stop_reason": "completed", "deterministic_preflight": preflight,
            "environment": {"python": platform.python_version(), "platform": platform.platform(), "numpy": np.__version__, "pandas": importlib.metadata.version("pandas"), "ldpc": importlib.metadata.version("ldpc")},
            "source_hashes": {f"{name}_sha256": _sha(path.read_bytes()) for name, path in modules.items()},
            "configuration_sha256": _sha(_compact({"run_id": RUN_ID, "q": Q, "n": N, "methods": METHODS})), "plan_sha256": _sha((output / "pre_run_plan.json").read_bytes()),
            "artifacts": _artifact_hashes(output), "indexed_codebooks": {entry["filename"]: entry["sha256"] for entry in codebook["entries"]},
            "verification_invoked_count": sum(bool(row["verification_invoked"]) for row in rows), "verification_union_bound": verification_union_bound(sum(bool(row["verification_invoked"]) for row in rows)), "outcome_count": len(rows)}
        _json_x(output / "formal_run_manifest.json", manifest)
        report["formal_run_manifest_sha256"] = _sha((output / "formal_run_manifest.json").read_bytes())
        _json_x(output / "formal_qualification_report.json", report)
    except BaseException as exc:
        _finalize_failure(output, exc=exc, provenance=provenance, preflight=preflight, utc_started=utc_started)
        raise


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle: return list(csv.DictReader(handle))
def _truth(value: str) -> bool: return value.lower() in {"true", "1"}


def verify(output: Path) -> None:
    actual = {item.name for item in output.iterdir()}
    if not actual.issubset(TOP_LEVEL) or not set(FORMAL_ARTIFACTS).issubset(actual): raise ValueError("unexpected top-level artifact set")
    plan = json.loads((output / "pre_run_plan.json").read_text()); manifest = json.loads((output / "formal_run_manifest.json").read_text()); report = json.loads((output / "formal_qualification_report.json").read_text())
    if (output / "formal_qualification_report.json").read_bytes() != json.dumps(report, indent=2, sort_keys=True).encode("utf-8") + b"\n": raise ValueError("report canonical bytes mismatch")
    if plan.get("run_id") != RUN_ID or manifest.get("run_id") != RUN_ID or report.get("run_id") != RUN_ID: raise ValueError("run id mismatch")
    if report.get("formal_run_manifest_sha256") != _sha((output / "formal_run_manifest.json").read_bytes()): raise ValueError("report manifest binding mismatch")
    if manifest.get("artifacts") != _artifact_hashes(output): raise ValueError("artifact hash DAG mismatch")
    git = manifest.get("git", {})
    if not isinstance(git.get("commit"), str) or _sha(bytes.fromhex(str(git.get("status_porcelain_v1_hex", "")))) != git.get("status_porcelain_v1_sha256") or bool(bytes.fromhex(str(git.get("status_porcelain_v1_hex", "")))) != git.get("dirty"): raise ValueError("git provenance mismatch")
    if manifest.get("run_status") == "non_promoted":
        if actual not in (set(FORMAL_ARTIFACTS), TOP_LEVEL) or report.get("run_status") != "non_promoted" or not manifest.get("exception") or ("codebooks" not in actual and manifest.get("indexed_codebooks") != {}): raise ValueError("failure finalizer evidence mismatch")
        print(json.dumps({"verified": True, "run_id": RUN_ID, "run_status": "non_promoted"}, sort_keys=True)); return
    expected_seeds = {"alice_symbols": 2026072501, "noise_p01_calibration": 2026072513, "noise_p01_qualification": 2026072511, "noise_p02_calibration": 2026072514, "noise_p02_qualification": 2026072512, "cascade_base": 2026072521, "frame_order": 2026072531}
    expected_caps = {"frame_s": 5, "total_s": 600, "ldpc_max_iter": 50, "cascade": {"events": 100000, "corrections": 4096, "queue_pops": 10000}}
    if plan.get("synthetic_only") is not True or plan.get("dimension") != Q or plan.get("frame_len_symbols") != N or plan.get("methods") != list(METHODS) or plan.get("mapping") != "gray" or plan.get("seeds") != expected_seeds or plan.get("caps") != expected_caps: raise ValueError("plan contract mismatch")
    if manifest.get("run_status") != "completed" or manifest.get("stop_reason") != "completed" or report.get("run_status") != "completed": raise ValueError("success run status mismatch")
    if actual != TOP_LEVEL: raise ValueError("successful run requires indexed codebooks")
    if manifest.get("plan_sha256") != _sha((output / "pre_run_plan.json").read_bytes()): raise ValueError("plan hash mismatch")
    if manifest.get("configuration_sha256") != _sha(_compact({"run_id": RUN_ID, "q": Q, "n": N, "methods": METHODS})): raise ValueError("configuration hash mismatch")
    expected_env = {"python": platform.python_version(), "platform": platform.platform(), "numpy": np.__version__, "pandas": importlib.metadata.version("pandas"), "ldpc": importlib.metadata.version("ldpc")}
    if manifest.get("environment") != expected_env: raise ValueError("environment provenance mismatch")
    for name in ("runner", "shared", "cascade", "ldpc"):
        path = Path(__file__) if name == "runner" else Path(__file__).parent.parent / "formal_ir" / f"{name}.py"
        if manifest.get("source_hashes", {}).get(f"{name}_sha256") != _sha(path.read_bytes()): raise ValueError("source hash mismatch")
    batches = _batches()
    if plan.get("synthetic_generation") != {name: _sha(a.tobytes() + b.tobytes()) for name, (a, b) in batches.items()}: raise ValueError("Alice/noise generation mismatch")
    ids = _ids(); order = [ids[int(index)] for index in np.random.Generator(np.random.PCG64(2026072531)).permutation(64)]
    if plan.get("canonical_qualification_ids") != ids or plan.get("qualification_execution_order") != order or plan.get("qualification_execution_order_sha256") != _sha(_compact(order)): raise ValueError("frame-order binding mismatch")
    frames = plan.get("frames", [])
    if [item.get("frame_id") for item in frames] != order: raise ValueError("plan frame lock mismatch")
    seed_by_frame: dict[str, str] = {}
    for item in frames:
        locked_seed_bits(item.get("verification_seed", {}), SEED_BITS); seed_by_frame[item["frame_id"]] = item["verification_seed"]["seed_id"]
    if len(set(seed_by_frame.values())) != 64: raise ValueError("verification seeds are not independent")
    codebook = json.loads((output / "formal_codebook_manifest.json").read_text()); verify_codebook_manifest(output, codebook)
    indexed = {entry["filename"]: entry["sha256"] for entry in codebook["entries"]}
    if manifest.get("indexed_codebooks") != indexed or {item.name for item in (output / "codebooks").iterdir()} != set(indexed): raise ValueError("codebook index mismatch")
    rows = _read_rows(output / "formal_frame_outcomes.csv")
    if len(rows) != 128 or manifest.get("outcome_count") != 128: raise ValueError("outcome count mismatch")
    data = (output / "formal_transcript.jsonl").read_bytes(); events = [json.loads(line) for line in data.splitlines()]
    cursor = 0; grouped: dict[str, list[dict[str, str]]] = {}
    expected_keys = [(method, frame) for frame in order for method in METHODS]
    if [(row["method"], row["frame_id"]) for row in rows] != expected_keys: raise ValueError("outcome execution order mismatch")
    for row in rows:
        if row["status"] not in FORMAL_STATUSES or not _truth(row["attempted"]) or not _truth(row["denominator_included"]): raise ValueError("status/denominator mismatch")
        if _truth(row["verification_invoked"]):
            if row["verification_seed_id"] != seed_by_frame[row["frame_id"]]: raise ValueError("verification seed binding mismatch")
        elif row["verification_seed_id"] != "": raise ValueError("noninvoked verification seed must be empty")
        key = f"{row['dataset_id']}:{row['frame_id']}"; begin = cursor
        while cursor < len(events) and events[cursor]["method"] == row["method"] and events[cursor]["frame_key"] == key: cursor += 1
        group = events[begin:cursor]; blob = b"".join(canonical_event(event) for event in group); summary = transcript_summary(group)
        if _sha(blob) != row["transcript_sha256"] or _sha(blob) != row["transcript_bytes_sha256"] or str(len(blob)) != row["transcript_bytes_len"]: raise ValueError("original transcript group hash mismatch")
        if str(summary["key_dependent_disclosure_bits_total"]) != row["key_dependent_disclosure_bits_total"] or str(summary["public_control_bits_total"]) != row["public_control_bits_total"]: raise ValueError("disclosure mismatch")
        grouped.setdefault(f"{row['method']}|{float(row['stratum_p']):.2f}", []).append(row)
    if cursor != len(events) or b"".join(canonical_event(event) for event in events) != data: raise ValueError("transcript bytes mismatch")
    invoked = sum(_truth(row["verification_invoked"]) for row in rows)
    if manifest.get("verification_invoked_count") != invoked or manifest.get("verification_union_bound") != verification_union_bound(invoked): raise ValueError("union-bound mismatch")
    evidence = report.get("deterministic_preflight", {})
    if evidence != manifest.get("deterministic_preflight") or not evidence.get("passed") or evidence.get("exit_code") != 0 or not isinstance(evidence.get("passed_count"), int): raise ValueError("preflight evidence mismatch")
    expected_preflight = [sys.executable, "-m", "pytest", "comparison_bench/tests/test_formal_verification.py", "comparison_bench/tests/test_cascade_formal.py", "comparison_bench/tests/test_ldpc_formal.py", "-q", "-p", "no:cacheprovider", "--basetemp"]
    command = evidence.get("command")
    if not isinstance(command, list) or command[:-1] != expected_preflight or not isinstance(command[-1], str) or not command[-1]: raise ValueError("preflight command mismatch")
    if set(grouped) != {f"{method}|{p:.2f}" for method in METHODS for p in (.01, .02)}: raise ValueError("qualification group mismatch")
    for key, group in grouped.items():
        if len(group) != 32 or report.get("promotion_gates", {}).get(key) != _gate(group): raise ValueError("promotion gate mismatch")
    print(json.dumps({"verified": True, "outcomes": 128, "run_id": RUN_ID}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, default=ROOT); parser.add_argument("--verify", action="store_true"); args = parser.parse_args()
    verify(args.output_dir) if args.verify else run(args.output_dir)
if __name__ == "__main__": main()
