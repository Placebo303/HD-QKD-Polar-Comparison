"""Immutable Cascade-only real-data qualification lock and runner.

This is deliberately separate from the historical final-IR selection lock: it
locks atomic rows and formal Toeplitz seeds for the formal method only.
"""
from __future__ import annotations

import csv
import importlib.metadata
import hashlib
import json
import os
import platform
import secrets
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from .cascade import run_cascade_formal
from .shared import FORMAL_ARTIFACTS, FORMAL_STATUSES, canonical_event, locked_seed_bits, materialize_seed_record, transcript_summary, verification_union_bound

RUN_ID = "20260725_v2_real_cascade"
Q, N, SEED_BITS = 1024, 64, 703
METHOD = "cascade_formal_v1"
REAL_BASE_SEED = 2026072522
CAPS = {"frame_s": 5, "total_s": 1200, "cascade": {"events": 100000, "corrections": 4096, "queue_pops": 10000}}
SYNTHETIC_REPORT_SHA256 = "d005ef4d7a7143c22e7dfd23e3c0c6def99f4761397e4158ff89cfc9c1ce97f5"
SOURCE_SHA256 = "967f569c3b3977cc9846025fc9af9b2faf3aa7d89b4e52e0d0ca804f5ab972cc"
FINAL_IR_MANIFEST_SHA256 = "28efc5d1654bfc241681a3a9e320aeded213f96f94e23273e33e4f4ea68acd95"
FINAL_IR_SPLIT_SHA256 = "915eb3212b801e7a3539d28b1b8de77dff8c2bcb7629fc6e9a08cd4e0fea20cb"
SOURCE_COLUMNS = ("dataset_id", "frame_id", "pair_idx", "alice_symbol", "bob_symbol", "dimension", "frame_len_symbols", "rows_input", "rows_used", "rows_dropped_tail", "source_path", "loss_db", "bin_width_ps", "n_eff_pairs", "threshold_ps", "processing_rule_version", "pairing_path_tag", "data_mode")
# Frozen provenance string (AGENTS.md section 5.4 exception): this exact value
# is bound by equality into existing lock artifacts (see _old_keys/make_lock/
# verify_lock below), so the constant itself must not change. Portable
# filesystem access goes through _resolve_split_path, which honors
# FINAL_IR_SPLIT_OVERRIDE; when that variable is unset (or set to the old
# value) behavior is unchanged.
FINAL_IR_SPLIT_PATH = r"D:\Code\HD-QKD_Polar_Comparison\comparison_bench\outputs_comparison\final_ir_method_selection\20260725_v1\locked_frame_split.csv"
SELECTION = {"calibration_dataset": "real_typeii_20db_d1024_bw100_blk0", "confirmation_dataset": "real_typeii_20db_d1024_bw120_blk0", "calibration_seed": 2026072541, "confirmation_seed": 2026072542, "ser": [0.2, 0.3]}
SYNTHETIC_GATES = {"cascade_formal_v1|0.01": {"promoted": True, "requested": 32, "verified_success": 32, "unclassified_internal_provenance_accounting_failures": 0}, "cascade_formal_v1|0.02": {"promoted": True, "requested": 32, "verified_success": 32, "unclassified_internal_provenance_accounting_failures": 0}, "ldpc_formal_v1|0.01": {"promoted": False, "requested": 32, "verified_success": 29, "unclassified_internal_provenance_accounting_failures": 0}, "ldpc_formal_v1|0.02": {"promoted": False, "requested": 32, "verified_success": 14, "unclassified_internal_provenance_accounting_failures": 0}}
GATE_STATUSES = {"verified_success", "verify_failed", "decode_failed", "syndrome_inconsistent", "aborted_resource_limit"}
LOCK_FILES = {"real_data_lock.json", "pre_run_plan.json"}
RUN_FILES = LOCK_FILES | {"formal_frame_outcomes.csv", "formal_transcript.jsonl", "formal_codebook_manifest.json", "formal_run_manifest.json", "formal_qualification_report.json"}
ELIGIBILITY_HASHES = {
    "bw100": {"sorted": "adc790769d7c59118fa92c7b1514cd5b27408c8d1ca49d1db4c4c5121d5def52", "permuted": "7e5c92bab7f25ba922a4c510d7359b8d21fe0343cbdc72bf4c2fe6e521ded140", "selected": "3430d890e95d0af30b81b8f1c25429ee7175911ba8187510054f557954b91865"},
    "bw120": {"sorted": "6b4b8fcaed9264aeaa3c90acc027ed8c0e7ba88591672e675f9304bed2a903ec", "permuted": "bee68cb8cb6b182b4d60b68b190c203ac1fb354b77ba38a8b7731c576357d62b", "selected": "eb336295544f2f38ebecc24ec9006dc976b23b0d6cdc8342074ce076070df1b9"},
}

def _sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def _compact(x: Any) -> bytes: return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
def _now() -> str: return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
def _write_x(path: Path, data: bytes) -> None:
    with path.open("xb") as f: f.write(data)
def _json_x(path: Path, item: Any) -> None: _write_x(path, json.dumps(item, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False).encode("utf-8") + b"\n")
def _file_sha(path: Path) -> str: return _sha(path.read_bytes())

def _eligible(source: pd.DataFrame, dataset: str) -> pd.DataFrame:
    x = source[(source.dataset_id == dataset) & (source.dimension == Q) & (source.frame_len_symbols == N)].copy()
    groups = x.groupby(["dataset_id", "frame_id"], sort=True)
    rows = []
    for (did, fid), frame in groups:
        frame = frame.sort_values("pair_idx")
        if frame.pair_idx.tolist() != list(range(N)) or len(frame) != N: continue
        ser = float((frame.alice_symbol.to_numpy() != frame.bob_symbol.to_numpy()).mean())
        if .20 <= ser < .30:
            rows.append({"dataset_id": did, "frame_id": int(fid), "frame_key": f"{did}:{fid}", "frame_ser": ser})
    return pd.DataFrame(rows).sort_values(["dataset_id", "frame_id"]).reset_index(drop=True)

def _selection(items: pd.DataFrame, seed: int) -> pd.DataFrame:
    if len(items) < 60: raise ValueError("insufficient eligible frames")
    order = np.random.Generator(np.random.PCG64(seed)).permutation(len(items))
    return items.iloc[order[:60]].reset_index(drop=True)

def _eligibility_record(items: pd.DataFrame, seed: int, name: str) -> tuple[dict[str, Any], pd.DataFrame]:
    """Hash the contract's frame-key lists, never dataframe records or indices."""
    sorted_keys = items.frame_key.astype(str).tolist()
    order = np.random.Generator(np.random.PCG64(seed)).permutation(len(items))
    permuted = [sorted_keys[int(i)] for i in order]
    selected = permuted[:60]
    got = {"count": len(sorted_keys), "sorted_sha256": _sha(_compact(sorted_keys)),
           "permuted_sha256": _sha(_compact(permuted)), "selected_sha256": _sha(_compact(selected))}
    fixed = ELIGIBILITY_HASHES[name]
    if got != {"count": 295 if name == "bw100" else 322, "sorted_sha256": fixed["sorted"], "permuted_sha256": fixed["permuted"], "selected_sha256": fixed["selected"]}:
        raise ValueError("fixed eligible-list preimage/hash mismatch")
    return got, items.iloc[order[:60]].reset_index(drop=True)

def _resolve_split_path(stored_path: str) -> Path:
    """Resolve the locked split CSV for reading.

    The stored provenance string stays frozen; only the live read may be
    redirected via FINAL_IR_SPLIT_OVERRIDE for POSIX/fresh-clone use.
    Raises a clear error when the file is absent.
    """
    override = os.environ.get("FINAL_IR_SPLIT_OVERRIDE")
    path = Path(override) if override else Path(stored_path)
    if not path.exists():
        raise FileNotFoundError(
            f"final-IR split CSV absent: {path} "
            "(set FINAL_IR_SPLIT_OVERRIDE to its POSIX location)")
    return path

def _old_keys(path: Path) -> set[str]:
    old = json.loads(path.read_text(encoding="utf-8"))
    locked = old.get("locked_split", {})
    if locked != {"path": FINAL_IR_SPLIT_PATH, "sha256": FINAL_IR_SPLIT_SHA256}: raise ValueError("final-IR split path/manifest mismatch")
    split_path = _resolve_split_path(str(locked["path"]))
    if _file_sha(split_path) != FINAL_IR_SPLIT_SHA256: raise ValueError("final-IR split hash mismatch")
    split = pd.read_csv(split_path)
    return set(split["locked_frame_key"].astype(str))

def make_lock(source_path: Path, output: Path, final_ir_manifest: Path, synthetic_report: Path) -> None:
    """Create exactly real_data_lock.json and its binding pre_run_plan.json."""
    if output.exists(): raise FileExistsError("fresh output required")
    if _file_sha(source_path) != SOURCE_SHA256: raise ValueError("source hash is not the canonical real source")
    if _file_sha(final_ir_manifest) != FINAL_IR_MANIFEST_SHA256: raise ValueError("final-IR manifest hash mismatch")
    if _file_sha(synthetic_report) != SYNTHETIC_REPORT_SHA256: raise ValueError("synthetic report hash is not the approved Cascade evidence")
    report = json.loads(synthetic_report.read_text(encoding="utf-8"))
    if report.get("run_id") != "20260725_v3_synthetic" or report.get("run_status") != "completed" or report.get("promotion_gates") != SYNTHETIC_GATES: raise ValueError("synthetic-v3 gate contract mismatch")
    src_bytes = source_path.read_bytes(); source = pd.read_parquet(source_path)
    if tuple(source.columns) != SOURCE_COLUMNS: raise ValueError("source columns are not the canonical 18-column schema")
    eligible100 = _eligible(source, SELECTION["calibration_dataset"])
    eligible120 = _eligible(source, SELECTION["confirmation_dataset"])
    if (len(eligible100), len(eligible120)) != (295, 322): raise ValueError("canonical eligibility counts changed")
    elig100, tuning = _eligibility_record(eligible100, 2026072541, "bw100")
    elig120, confirm = _eligibility_record(eligible120, 2026072542, "bw120")
    old = _old_keys(final_ir_manifest)
    if set(tuning.frame_key) & set(confirm.frame_key) or (set(tuning.frame_key) | set(confirm.frame_key)) & old: raise ValueError("group/final-IR overlap")
    output.mkdir(parents=True)
    selected = pd.concat([tuning.assign(split="calibration"), confirm.assign(split="confirmation")], ignore_index=True)
    selected["selection_index"] = np.arange(len(selected))
    atomic = source.merge(selected[["dataset_id", "frame_id", "split", "selection_index"]], on=["dataset_id", "frame_id"], how="inner", validate="many_to_one").sort_values(["selection_index", "pair_idx"])
    if len(atomic) != 120 * N: raise ValueError("atomic row reconstruction failed")
    atomic_rows = atomic[list(SOURCE_COLUMNS)].to_dict("records")
    seeds = {r.frame_key: materialize_seed_record(SEED_BITS) for r in confirm.itertuples()}
    selected_records = selected.to_dict("records")
    for record in selected_records:
        frame = atomic[(atomic.dataset_id == record["dataset_id"]) & (atomic.frame_id == record["frame_id"])].sort_values("pair_idx")
        record["pair_idx_sequence_sha256"] = _sha(_compact(frame.pair_idx.astype(int).tolist()))
    core = {"run_id": RUN_ID, "method": METHOD, "dimension": Q, "frame_len_symbols": N, "mapping": "gray", "source": {"path": str(source_path), "sha256": _sha(src_bytes), "columns": list(SOURCE_COLUMNS)}, "eligibility": {"bw100": elig100, "bw120": elig120}, "selection": SELECTION, "selected_frames": selected_records, "selected_frames_sha256": _sha(_compact(selected_records)), "atomic_rows": atomic_rows, "atomic_rows_sha256": _sha(_compact(atomic_rows)), "confirmation_seeds": seeds, "final_ir_v1": {"manifest_path": str(final_ir_manifest), "manifest_sha256": _file_sha(final_ir_manifest), "split_path": FINAL_IR_SPLIT_PATH, "split_sha256": FINAL_IR_SPLIT_SHA256, "overlap_count": 0}, "synthetic_v3": {"report_path": str(synthetic_report), "report_sha256": SYNTHETIC_REPORT_SHA256, "promotion_gates": SYNTHETIC_GATES, "method": METHOD, "ldpc_excluded": True}}
    lock = {**core, "lock_content_sha256": _sha(_compact(core))}
    _json_x(output / "real_data_lock.json", lock)
    plan = {"run_id": RUN_ID, "method": METHOD, "dimension": Q, "frame_len_symbols": N, "mapping": "gray", "schedule": [16,32,64,128], "declared_argv": ["-m", "comparison_bench.src.comparison_bench.cli.run_formal_real_qualification", "--output-dir", str(output)], "caps": CAPS, "base_seed": REAL_BASE_SEED, "failure_finalizer": "exclusive_preserve_partial_six_artifacts", "real_data_lock_sha256": _file_sha(output / "real_data_lock.json"), "confirmation_order": confirm.frame_key.tolist()}
    _json_x(output / "pre_run_plan.json", plan)

def verify_lock(output: Path, expected_state: str = "lock") -> dict[str, Any]:
    lock_path, plan_path = output / "real_data_lock.json", output / "pre_run_plan.json"
    actual = {p.name for p in output.iterdir()}
    if expected_state not in {"lock", "run"}: raise ValueError("invalid expected state")
    if actual != (LOCK_FILES if expected_state == "lock" else RUN_FILES): raise ValueError("unexpected real qualification artifact set")
    lock, plan = json.loads(lock_path.read_text()), json.loads(plan_path.read_text())
    core = {k: v for k, v in lock.items() if k != "lock_content_sha256"}
    if lock.get("lock_content_sha256") != _sha(_compact(core)): raise ValueError("lock content mismatch")
    if plan.get("real_data_lock_sha256") != _file_sha(lock_path) or lock.get("method") != METHOD: raise ValueError("plan binding/method mismatch")
    source_path = Path(lock["source"]["path"])
    if _file_sha(source_path) != SOURCE_SHA256 or lock["source"] != {"path": str(source_path), "sha256": SOURCE_SHA256, "columns": list(SOURCE_COLUMNS)}: raise ValueError("source hash/schema mismatch")
    report = json.loads(Path(lock["synthetic_v3"]["report_path"]).read_text(encoding="utf-8"))
    if _file_sha(Path(lock["synthetic_v3"]["report_path"])) != SYNTHETIC_REPORT_SHA256 or lock["synthetic_v3"] != {"report_path": str(Path(lock["synthetic_v3"]["report_path"])), "report_sha256": SYNTHETIC_REPORT_SHA256, "promotion_gates": SYNTHETIC_GATES, "method": METHOD, "ldpc_excluded": True} or report.get("promotion_gates") != SYNTHETIC_GATES: raise ValueError("synthetic report mismatch")
    old_manifest = Path(lock["final_ir_v1"]["manifest_path"])
    expected_old = {"manifest_path": str(old_manifest), "manifest_sha256": FINAL_IR_MANIFEST_SHA256, "split_path": FINAL_IR_SPLIT_PATH, "split_sha256": FINAL_IR_SPLIT_SHA256, "overlap_count": 0}
    if lock.get("final_ir_v1") != expected_old or _file_sha(old_manifest) != FINAL_IR_MANIFEST_SHA256: raise ValueError("old manifest mismatch")
    src = pd.read_parquet(source_path); sel = pd.DataFrame(lock["selected_frames"])
    if tuple(src.columns) != SOURCE_COLUMNS or lock.get("selection") != SELECTION or len(sel) != 120 or sel.split.value_counts().to_dict() != {"calibration": 60, "confirmation": 60} or sel.selection_index.tolist() != list(range(120)) or lock.get("selected_frames_sha256") != _sha(_compact(lock["selected_frames"])): raise ValueError("selection counts")
    e100, e120 = _eligible(src, lock["selection"]["calibration_dataset"]), _eligible(src, lock["selection"]["confirmation_dataset"])
    if (len(e100), len(e120)) != (295, 322): raise ValueError("eligibility count mismatch")
    expect100, s100 = _eligibility_record(e100, 2026072541, "bw100")
    expect120, s120 = _eligibility_record(e120, 2026072542, "bw120")
    if lock.get("eligibility") != {"bw100": expect100, "bw120": expect120}: raise ValueError("eligibility hash mismatch")
    expected = pd.concat([s100.assign(split="calibration"), s120.assign(split="confirmation")], ignore_index=True)
    expected["selection_index"] = np.arange(120)
    expected_records = expected.to_dict("records")
    for record in expected_records:
        frame = src[(src.dataset_id == record["dataset_id"]) & (src.frame_id == record["frame_id"])].sort_values("pair_idx")
        record["pair_idx_sequence_sha256"] = _sha(_compact(frame.pair_idx.astype(int).tolist()))
    if lock["selected_frames"] != expected_records: raise ValueError("PCG selected full-record mismatch")
    if lock.get("final_ir_v1", {}).get("overlap_count") != 0 or set(sel.frame_key) & _old_keys(old_manifest): raise ValueError("final IR overlap")
    for record in lock["selected_frames"]:
        frame = src[(src.dataset_id == record["dataset_id"]) & (src.frame_id == record["frame_id"])].sort_values("pair_idx")
        if record.get("pair_idx_sequence_sha256") != _sha(_compact(frame.pair_idx.astype(int).tolist())): raise ValueError("pair-index sequence mismatch")
    rows = src.merge(sel[["dataset_id", "frame_id", "selection_index"]], on=["dataset_id", "frame_id"], how="inner").sort_values(["selection_index", "pair_idx"])[list(SOURCE_COLUMNS)].to_dict("records")
    if rows != lock["atomic_rows"] or lock.get("atomic_rows_sha256") != _sha(_compact(rows)): raise ValueError("atomic rows mismatch")
    seeds = lock.get("confirmation_seeds", {})
    if set(seeds) != set(sel.loc[sel.split == "confirmation", "frame_key"]) or len({v["seed_id"] for v in seeds.values()}) != 60: raise ValueError("seed set mismatch")
    for item in seeds.values(): locked_seed_bits(item, SEED_BITS)
    expected_plan = {"run_id": RUN_ID, "method": METHOD, "dimension": Q, "frame_len_symbols": N, "mapping": "gray", "schedule": [16,32,64,128], "declared_argv": ["-m", "comparison_bench.src.comparison_bench.cli.run_formal_real_qualification", "--output-dir", str(output)], "caps": CAPS, "base_seed": REAL_BASE_SEED, "failure_finalizer": "exclusive_preserve_partial_six_artifacts", "real_data_lock_sha256": _file_sha(lock_path), "confirmation_order": expected.loc[expected.split == "confirmation", "frame_key"].tolist()}
    if plan != expected_plan: raise ValueError("pre-run plan contract mismatch")
    return lock

def _csv_x(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({k for row in rows for k in row}) or ["method", "status"]
    with path.open("x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

def _dag(output: Path) -> dict[str, str]:
    names = ("real_data_lock.json", "pre_run_plan.json", "formal_frame_outcomes.csv", "formal_transcript.jsonl", "formal_codebook_manifest.json")
    return {name: _file_sha(output / name) for name in names if (output / name).is_file()}

def _git_evidence() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[4]
    commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    raw = subprocess.run(["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"], capture_output=True, check=True).stdout
    return {"commit": commit, "porcelain_bytes_hex": raw.hex(), "porcelain_sha256": _sha(raw), "dirty": bool(raw)}

def _module_hashes() -> dict[str, str]:
    cli = Path(__file__).resolve().parents[1] / "cli"
    paths = {"real_qualification": Path(__file__), "cascade": Path(__file__).with_name("cascade.py"), "shared": Path(__file__).with_name("shared.py"), "ldpc": Path(__file__).with_name("ldpc.py"), "lock_cli": cli / "lock_formal_real_qualification.py", "run_cli": cli / "run_formal_real_qualification.py"}
    return {key: _file_sha(path) for key, path in paths.items()}

def _environment() -> dict[str, str]:
    return {"python": platform.python_version(), "platform": platform.platform(), "numpy": np.__version__, "pandas": pd.__version__, "ldpc": importlib.metadata.version("ldpc")}

def _semantic_argv(argv: list[str], declared: list[str]) -> bool:
    if len(declared) != 4 or declared[:3] != ["-m", "comparison_bench.src.comparison_bench.cli.run_formal_real_qualification", "--output-dir"]: return False
    return len(argv) == 3 and Path(argv[0]).name == "run_formal_real_qualification.py" and argv[1:] == ["--output-dir", declared[3]]

def _writable_external_root(candidate: Path, repo: Path) -> Path | None:
    probe: Path | None = None
    created = False
    try:
        root = candidate.resolve()
        if root == repo or repo in root.parents: return None
        root.mkdir(parents=True, exist_ok=True)
        probe = root / f".formal-ir-write-probe-{secrets.token_hex(16)}"
        with probe.open("xb"):
            created = True
        return root
    except OSError:
        return None
    finally:
        if created and probe is not None:
            probe.unlink(missing_ok=True)

def _system_temp_root() -> Path:
    return Path(tempfile.gettempdir())

def _external_preflight_paths() -> tuple[Path, Path]:
    repo = Path(__file__).resolve().parents[4]
    configured = os.environ.get("FORMAL_IR_TEST_TMP")
    test_root = _writable_external_root(Path(configured), repo) if configured else None
    if test_root is None:
        system_root = _writable_external_root(_system_temp_root(), repo)
        if system_root is None: raise RuntimeError("no writable external system temp root")
        test_root = (system_root / f"formal-real-tests-{secrets.token_hex(16)}").resolve()
        test_root.mkdir(exist_ok=False)
        if test_root == repo or repo in test_root.parents: raise RuntimeError("fresh FORMAL_IR_TEST_TMP is not external")
    basetemp = (test_root / f"formal-real-pytest-{secrets.token_hex(16)}").resolve()
    basetemp.mkdir(exist_ok=False)
    if basetemp == repo or repo in basetemp.parents: raise RuntimeError("fresh pytest basetemp is not external")
    return test_root, basetemp

def _deterministic_preflight() -> dict[str, Any]:
    test_root, base = _external_preflight_paths()
    command = [sys.executable, "-m", "pytest", "comparison_bench/tests/test_formal_verification.py", "comparison_bench/tests/test_cascade_formal.py", "comparison_bench/tests/test_ldpc_formal.py", "comparison_bench/tests/test_formal_real_qualification.py", "-q", "-p", "no:cacheprovider", "--basetemp", str(base)]
    result = subprocess.run(command, cwd=Path.cwd(), env={**os.environ, "FORMAL_IR_TEST_TMP": str(test_root), "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True)
    evidence = result.stdout + b"\n---STDERR---\n" + result.stderr
    import re
    match = re.search(r"(\d+) passed", result.stdout.decode("utf-8", "replace"))
    return {"command": command, "exit_code": result.returncode, "passed_count": int(match.group(1)) if match else None, "output_sha256": _sha(evidence), "passed": result.returncode == 0 and match is not None}

def run_locked(output: Path) -> None:
    """Public real execution path; it deliberately has no testing seams."""
    _run_locked_for_test(output, runner=run_cascade_formal)

def _run_locked_for_test(output: Path, *, runner: Callable[..., dict[str, Any]] = run_cascade_formal, _argv: list[str] | None = None, _preflight: dict[str, Any] | None = None, _git: dict[str, Any] | None = None) -> None:
    lock = verify_lock(output, "lock")
    plan = json.loads((output / "pre_run_plan.json").read_text())
    # The lock phase has already written the binding pre-run plan; all other
    # common evidence files must still be absent before execution.
    reserved = [x for x in FORMAL_ARTIFACTS if x != "pre_run_plan.json" and (output / x).exists()]
    if reserved: raise FileExistsError(f"formal evidence already exists: {reserved}")
    start = time.monotonic(); utc_started = _now(); rows: list[dict[str, Any]] = []; events: list[dict[str, Any]] = []
    preflight: dict[str, Any] | None = None; git: dict[str, Any] | None = None
    try:
        preflight = _preflight if _preflight is not None else _deterministic_preflight()
        if not preflight["passed"]: raise RuntimeError("deterministic_preflight_failed")
        git = _git if _git is not None else _git_evidence()  # raw porcelain bytes are captured before method calls.
        atomic = pd.DataFrame(lock["atomic_rows"]); selected = pd.DataFrame(lock["selected_frames"])
        for key in plan["confirmation_order"]:
            if time.monotonic() - start >= CAPS["total_s"]: raise TimeoutError("total cap")
            frame = atomic[(atomic.dataset_id + ":" + atomic.frame_id.astype(str)) == key].sort_values("pair_idx")
            result = runner(frame.alice_symbol.to_numpy(), frame.bob_symbol.to_numpy(), dimension=Q, dataset_id=str(frame.dataset_id.iloc[0]), frame_id=str(frame.frame_id.iloc[0]), mapping="gray", base_seed=plan["base_seed"], locked_seed=lock["confirmation_seeds"][key], caps={**CAPS["cascade"], "wall_s": CAPS["frame_s"]})
            group = b"".join(canonical_event(e) for e in result["events"])
            if result["outcome"].get("transcript_sha256") != _sha(group): raise ValueError("original transcript mismatch")
            row = dict(result["outcome"]); row.update({"qualification_role": "confirmation", "plan_frame_key": key, "transcript_bytes_sha256": _sha(group), "transcript_bytes_len": len(group)})
            rows.append(row); events.extend(result["events"])
        _write_x(output / "formal_transcript.jsonl", b"".join(canonical_event(e) for e in events)); _csv_x(output / "formal_frame_outcomes.csv", rows)
        _json_x(output / "formal_codebook_manifest.json", {"generator_id": "not_applicable_cascade", "entries": []})
        invoked = sum(bool(x["verification_invoked"]) for x in rows)
        manifest = {"run_id": RUN_ID, "run_status": "completed", "argv": list(sys.argv) if _argv is None else _argv, "declared_argv": plan["declared_argv"], "utc_started": utc_started, "utc_finished": _now(), "stop_reason": "completed", "preflight": preflight, "git": git, "environment": _environment(), "module_hashes": _module_hashes(), "lock_sha256": _file_sha(output / "real_data_lock.json"), "plan_sha256": _file_sha(output / "pre_run_plan.json"), "configuration_sha256": _sha(_compact({"q":Q,"n":N,"method":METHOD,"mapping":"gray","caps":CAPS})), "artifacts": _dag(output), "outcome_count": len(rows), "verification_invoked_count": invoked, "verification_union_bound": verification_union_bound(invoked), "runner_internal_failure_count": 0}
        _json_x(output / "formal_run_manifest.json", manifest)
        good = sum(x["status"] == "verified_success" for x in rows); bad = sum(x["status"] not in GATE_STATUSES for x in rows)
        _json_x(output / "formal_qualification_report.json", {"run_id": RUN_ID, "run_status": "completed", "promotion_gate": {"requested": 60, "verified_success": good, "unclassified_internal_provenance_accounting_failures": bad, "promoted": good == 60 and bad == 0}, "formal_run_manifest_sha256": _file_sha(output / "formal_run_manifest.json")})
    except BaseException as exc:
        # immutable best-effort six-artifact failure package
        if not (output / "formal_frame_outcomes.csv").exists(): _csv_x(output / "formal_frame_outcomes.csv", rows)
        if not (output / "formal_transcript.jsonl").exists(): _write_x(output / "formal_transcript.jsonl", b"".join(canonical_event(e) for e in events))
        if not (output / "formal_codebook_manifest.json").exists(): _json_x(output / "formal_codebook_manifest.json", {"generator_id": "not_applicable_cascade", "entries": []})
        if not (output / "formal_run_manifest.json").exists(): _json_x(output / "formal_run_manifest.json", {"run_id": RUN_ID, "run_status": "non_promoted", "argv": list(sys.argv) if _argv is None else _argv, "declared_argv": plan.get("declared_argv"), "utc_started": utc_started, "utc_finished": _now(), "stop_reason": "exception", "exception": {"class": type(exc).__name__, "message": str(exc)}, "preflight": preflight, "git": git, "environment": _environment(), "module_hashes": _module_hashes(), "lock_sha256": _file_sha(output / "real_data_lock.json"), "plan_sha256": _file_sha(output / "pre_run_plan.json"), "configuration_sha256": _sha(_compact({"q":Q,"n":N,"method":METHOD,"mapping":"gray","caps":CAPS})), "artifacts": _dag(output), "outcome_count": len(rows), "verification_invoked_count": sum(bool(x.get("verification_invoked")) for x in rows), "verification_union_bound": verification_union_bound(sum(bool(x.get("verification_invoked")) for x in rows)), "runner_internal_failure_count": 1})
        if not (output / "formal_qualification_report.json").exists(): _json_x(output / "formal_qualification_report.json", {"run_id": RUN_ID, "run_status": "non_promoted", "stop_reason": "exception", "exception": {"class": type(exc).__name__, "message": str(exc)}, "promotion_gate": {"requested": 60, "attempted": len(rows), "verified_success": sum(x.get("status") == "verified_success" for x in rows), "unclassified_internal_provenance_accounting_failures": sum(x.get("status") not in GATE_STATUSES for x in rows) + 1, "promoted": False}, "formal_run_manifest_sha256": _file_sha(output / "formal_run_manifest.json")})
        raise

def verify_run(output: Path) -> None:
    lock = verify_lock(output, "run"); report = json.loads((output / "formal_qualification_report.json").read_text()); manifest = json.loads((output / "formal_run_manifest.json").read_text())
    if (output / "formal_qualification_report.json").read_bytes() != json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False).encode("utf-8") + b"\n": raise ValueError("report canonical bytes")
    if report.get("formal_run_manifest_sha256") != _file_sha(output / "formal_run_manifest.json"): raise ValueError("report binding")
    rows = list(csv.DictReader((output / "formal_frame_outcomes.csv").open(encoding="utf-8")))
    keys = json.loads((output / "pre_run_plan.json").read_text())["confirmation_order"]
    if manifest.get("run_id") != RUN_ID or report.get("run_id") != RUN_ID or manifest.get("declared_argv") != json.loads((output / "pre_run_plan.json").read_text())["declared_argv"] or not _semantic_argv(manifest.get("argv", []), manifest["declared_argv"]): raise ValueError("run id/argv mismatch")
    if manifest.get("lock_sha256") != _file_sha(output / "real_data_lock.json") or manifest.get("plan_sha256") != _file_sha(output / "pre_run_plan.json"): raise ValueError("manifest lock/plan binding")
    if manifest.get("environment") != _environment() or manifest.get("module_hashes") != _module_hashes() or manifest.get("configuration_sha256") != _sha(_compact({"q":Q,"n":N,"method":METHOD,"mapping":"gray","caps":CAPS})): raise ValueError("manifest common evidence mismatch")
    try:
        started, finished = (datetime.fromisoformat(manifest[key].replace("Z", "+00:00")) for key in ("utc_started", "utc_finished"))
    except (AttributeError, ValueError, KeyError) as exc: raise ValueError("manifest UTC evidence mismatch") from exc
    if not manifest["utc_started"].endswith("Z") or not manifest["utc_finished"].endswith("Z") or finished < started: raise ValueError("manifest UTC order mismatch")
    completed = manifest.get("run_status") == "completed"
    if (completed and (manifest.get("stop_reason") != "completed" or report.get("run_status") != "completed")) or (not completed and (manifest.get("run_status") != "non_promoted" or manifest.get("stop_reason") != "exception" or report.get("run_status") != "non_promoted" or report.get("stop_reason") != "exception")): raise ValueError("run/report status mismatch")
    if json.loads((output / "formal_codebook_manifest.json").read_text(encoding="utf-8")) != {"generator_id": "not_applicable_cascade", "entries": []}: raise ValueError("Cascade codebook manifest mismatch")
    preflight = manifest.get("preflight")
    prefix = [sys.executable, "-m", "pytest", "comparison_bench/tests/test_formal_verification.py", "comparison_bench/tests/test_cascade_formal.py", "comparison_bench/tests/test_ldpc_formal.py", "comparison_bench/tests/test_formal_real_qualification.py", "-q", "-p", "no:cacheprovider", "--basetemp"]
    if completed and (not isinstance(preflight, dict) or not preflight.get("passed") or preflight.get("exit_code") != 0 or not isinstance(preflight.get("passed_count"), int) or not isinstance(preflight.get("output_sha256"), str) or len(preflight["output_sha256"]) != 64 or not isinstance(preflight.get("command"), list) or preflight["command"][:-1] != prefix or not isinstance(preflight["command"][-1], str) or not preflight["command"][-1]): raise ValueError("preflight evidence mismatch")
    if not completed and preflight is not None and (not isinstance(preflight, dict) or not isinstance(preflight.get("command"), list) or not isinstance(preflight.get("output_sha256"), str) or len(preflight["output_sha256"]) != 64): raise ValueError("failure preflight evidence mismatch")
    git = manifest.get("git")
    if completed and (not isinstance(git, dict) or not isinstance(git.get("commit"), str) or not git["commit"]): raise ValueError("git evidence missing")
    if git is not None:
        try: raw = bytes.fromhex(str(git.get("porcelain_bytes_hex", "")))
        except ValueError as exc: raise ValueError("git evidence encoding mismatch") from exc
        if _sha(raw) != git.get("porcelain_sha256") or bool(raw) != git.get("dirty"): raise ValueError("git evidence mismatch")
    if manifest.get("artifacts") != _dag(output): raise ValueError("artifact DAG mismatch")
    if (completed and (len(rows) != 60 or [x["plan_frame_key"] for x in rows] != keys)) or (not completed and ([x["plan_frame_key"] for x in rows] != keys[:len(rows)] or len(rows) > 60)): raise ValueError("outcome order/count")
    data = (output / "formal_transcript.jsonl").read_bytes(); events = [json.loads(x) for x in data.splitlines()]
    if b"".join(canonical_event(event) for event in events) != data: raise ValueError("transcript canonical bytes mismatch")
    cursor = 0
    for row in rows:
        if row.get("method") != METHOD or f"{row.get('dataset_id')}:{row.get('frame_id')}" != row.get("plan_frame_key"): raise ValueError("row method/frame-key mismatch")
        part = []
        while cursor < len(events):
            e = events[cursor]
            if part and e["frame_key"] != part[0]["frame_key"]: break
            if e.get("method") != METHOD or e.get("frame_key") != row["plan_frame_key"]: raise ValueError("event method/frame-key mismatch")
            part.append(e); cursor += 1
        group = b"".join(canonical_event(e) for e in part)
        if row["transcript_sha256"] != _sha(group) or row.get("transcript_bytes_sha256") != _sha(group) or int(row.get("transcript_bytes_len", -1)) != len(group): raise ValueError("original transcript hash")
        if row["status"] not in FORMAL_STATUSES or row.get("attempted", "").lower() not in {"true", "1"} or row.get("denominator_included", "").lower() not in {"true", "1"}: raise ValueError("row status/denominator")
        summary = transcript_summary(part)
        if str(summary["key_dependent_disclosure_bits_total"]) != row.get("key_dependent_disclosure_bits_total") or str(summary["public_control_bits_total"]) != row.get("public_control_bits_total"): raise ValueError("row disclosure totals mismatch")
        invoked = row.get("verification_invoked", "").lower() in {"1", "true"}
        if invoked:
            if row.get("verification_seed_id") != lock["confirmation_seeds"][row["plan_frame_key"]]["seed_id"]: raise ValueError("seed binding")
        elif row.get("verification_seed_id"): raise ValueError("uninvoked seed disclosed")
    if cursor != len(events): raise ValueError("transcript cursor not exhausted")
    invoked_count = sum(r.get("verification_invoked", "").lower() in {"1", "true"} for r in rows)
    good = sum(r["status"] == "verified_success" for r in rows)
    bad = sum(r["status"] not in GATE_STATUSES for r in rows)
    gate = report.get("promotion_gate", {})
    if manifest.get("outcome_count") != len(rows) or manifest.get("verification_invoked_count") != invoked_count or manifest.get("verification_union_bound") != verification_union_bound(invoked_count): raise ValueError("manifest accounting")
    expected_gate = {"requested": 60, "attempted": len(rows), "verified_success": good, "unclassified_internal_provenance_accounting_failures": bad + 1, "promoted": False} if not completed else {"requested": 60, "verified_success": good, "unclassified_internal_provenance_accounting_failures": bad, "promoted": good == 60 and bad == 0}
    if gate != expected_gate or (completed and (len(rows) != 60 or manifest.get("runner_internal_failure_count") != 0)) or (not completed and (report.get("run_status") != "non_promoted" or manifest.get("runner_internal_failure_count") != 1 or not manifest.get("exception") or not report.get("exception"))): raise ValueError("gate/failure mismatch")
