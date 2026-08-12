"""Immutable v1 fresh real qualification package for binary LDPC v5.

Implements the frozen Phase 4 contract (prepare once, main-thread review,
execute once, read-only verify once; no-overwrite, non-resumable, immutable
failure retention; 126/128 per stratum with zero forbidden failures).
Production entry points expose no test switch; private test helpers require
explicit fakes and a test-owned workspace root.

The package uses the verified Phase 3 synthetic package and the locked
partition as frozen prerequisites. Frames come from the locked real
partition; no generator exists.
"""
from __future__ import annotations
import functools, hashlib, importlib.metadata, json, logging, os, platform, secrets, time
from pathlib import Path
from typing import Any, Callable, Mapping
import numpy as np

logger = logging.getLogger("comparison_bench.ldpc_v5_real_qualification")
from . import ldpc_v5_development as dev
from .codebook_v5_h2 import verify_h2_manifest
from .ldpc_v5 import (METHOD, run_ldpc_formal_v5, build_v5_policy_manifest,
                      verify_v5_policy_manifest, _selected_candidates,
                      validate_outcome_v5, verify_public_payload_v5,
                      encode_outcome_csv_v5, canonical_event_v5, OUTCOME_FIELDS)
from .ldpc_v5_partition import validate_partition_lock
from .ldpc_v5_confirmation_arrays import confirmation_rows, confirmation_arrays_for_frame
from .shared import seed_record

RUN_ID = "binary_ldpc_v5_real_qualification_v1"
TEST_RUN_ID = "binary_ldpc_v5_real_qualification_test_v1"
ROLE = "real_confirmation"
N = 256
Q = 1024
MAPPING = "gray"
CANDIDATE = "V5-C2"
REAL_STRATA = ("bw120", "bw180", "bw200")
# Explicit mapping from partition-lock internal stratum names to public names.
LOCK_TO_PUBLIC: dict[str, str] = {"d1024_bw120": "bw120", "d1024_bw180": "bw180", "d1024_bw200": "bw200"}
PUBLIC_TO_LOCK: dict[str, str] = {v: k for k, v in LOCK_TO_PUBLIC.items()}
FRAMES_PER_STRATUM = 128
SEED_BIT_LENGTH = 2623
PLAN_SCHEMA = "binary_ldpc_v5_real_plan_v1"
TEST_PLAN_SCHEMA = "binary_ldpc_v5_real_plan_test_v1"
RUN_MANIFEST_SCHEMA = "binary_ldpc_v5_real_run_manifest_v1"
TEST_RUN_MANIFEST_SCHEMA = "binary_ldpc_v5_real_run_manifest_test_v1"
REPORT_SCHEMA = "binary_ldpc_v5_real_report_v1"
TEST_REPORT_SCHEMA = "binary_ldpc_v5_real_report_test_v1"
SEED_SCHEDULE_SCHEMA = "binary_ldpc_v5_real_seed_schedule_v1"
FAILURE_POLICY = "immutable_partial_finalization_no_resume_no_rerun_no_tuning"
COMPLETE_RUN_CAP_S = 1800.0
GATE_SUCCESSES = 126

ARTIFACTS = ("pre_run_plan.json", "formal_codebook_manifest.json",
             "formal_selection_manifest.json", "formal_channel_model.json",
             "v5_h2_manifest.json", "v5_policy_manifest.json",
             "real_frame_outcomes.csv", "real_transcript.jsonl",
             "real_run_manifest.json", "real_qualification_report.json")

FORBIDDEN_CLASSES = ("backend", "source", "internal", "accounting", "resource",
                     "syndrome", "unclassified", "provenance")
FORBIDDEN_STATUSES = {"invalid_input", "unsupported_domain", "backend_unavailable",
                       "aborted_resource_limit", "syndrome_inconsistent", "decoder_error"}

_REPO = Path(__file__).resolve().parents[4]
_ROOT = _REPO / "comparison_bench" / "outputs_comparison" / "formal_ir_methods"
OFFICIAL_OUTPUT = _ROOT / "20260801_v2_binary_ldpc_v5_real"
DEVELOPMENT_PKG = _ROOT / "20260731_v1_binary_ldpc_v5_development"
SYNTHETIC_PKG = _ROOT / "20260801_v1_binary_ldpc_v5_synthetic"
PARTITION_LOCK = _ROOT / "20260731_v1_binary_ldpc_v5_partition" / "partition_lock.json"

_SCOPED = ("cli/run_ldpc_v5_real_qualification.py",
           "cli/verify_ldpc_v5_real_qualification.py",
           "formal_ir/ldpc_v5_real_qualification.py",
           "formal_ir/ldpc_v5_confirmation_arrays.py",
           "formal_ir/ldpc_v5.py", "formal_ir/ldpc_v5_development.py",
           "formal_ir/ldpc_v5_partition.py", "formal_ir/ldpc_v5_predecessors.py",
           "formal_ir/codebook_v5_h2.py", "formal_ir/codebook_v4.py",
           "formal_ir/ldpc_v4_channel.py", "formal_ir/ldpc_v4_10db_source.py",
           "formal_ir/shared.py", "utils/bitops.py",
           "cli/run_ldpc_v5_development.py", "cli/verify_ldpc_v5_development.py")


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _self(value: dict[str, Any], key: str) -> dict[str, Any]:
    return {**value, key: _sha(_compact(value))}


def _json(path: Path, value: Any) -> None:
    path.open("xb").write(_compact(value))


def _write(path: Path, value: bytes) -> None:
    path.open("xb").write(value)


def _json_read(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    doc = json.loads(raw)
    if not isinstance(doc, dict) or _compact(doc) != raw:
        raise ValueError("noncanonical json")
    return doc


def _hashes() -> dict[str, str]:
    src = _REPO / "comparison_bench" / "src" / "comparison_bench"
    return {f"comparison_bench/src/comparison_bench/{rel}": _sha((src / rel).read_bytes()) for rel in sorted(_SCOPED)}


def _environment(test_only: bool) -> dict[str, Any]:
    try:
        ldpc_version = importlib.metadata.version("ldpc")
    except Exception:
        ldpc_version = None
    return {"python_version": platform.python_version(), "numpy_version": np.__version__,
            "ldpc_version": ldpc_version, "platform": platform.platform(), "test_only": bool(test_only)}


def _root_id(value: str) -> str:
    return _sha(bytes.fromhex(value))


def _new_root_hex() -> str:
    return secrets.token_bytes(32).hex()


# --- development prerequisite ----------------------------------------------

def _quick_verify_development(dir_path: Path) -> None:
    """Fast test-mode prerequisite check: static plan/artifact consistency."""
    if not dir_path.is_dir() or {x.name for x in dir_path.iterdir()} != set(dev.ARTIFACTS):
        raise ValueError("development 12 artifact contract")
    plan = _json_read(dir_path / "pre_run_plan.json")
    dev._validate_plan(plan, test_only=False, output_dir=dir_path)
    manifest = _json_read(dir_path / "development_run_manifest.json")
    index = {name: {"sha256": _sha((dir_path / name).read_bytes()), "bytes": (dir_path / name).stat().st_size}
             for name in dev.ARTIFACTS[1:10]}
    if manifest.get("run_manifest_sha256") != _sha(_compact({k: v for k, v in manifest.items() if k != "run_manifest_sha256"})) or \
       manifest.get("artifact_file_sha256") != index or manifest.get("run_status") != "completed":
        raise ValueError("development manifest drift")
    selection = _json_read(dir_path / "development_selection.json")
    report = _json_read(dir_path / "development_report.json")
    if selection.get("selected_candidate_id") != CANDIDATE or \
       selection.get("ready_for_synthetic_prepare") is not True or \
       report.get("run_status") != "completed":
        raise ValueError("development package not ready")


@functools.lru_cache(maxsize=4)
def _load_development_cached(dir_path: str, private: bool) -> dict[str, Any]:
    return _load_development_uncached(Path(dir_path), private=private)


def _load_development_uncached(dir_path: Path, *, private: bool) -> dict[str, Any]:
    if private:
        _quick_verify_development(dir_path)
        result = {"status": "verified", "run_status": "completed", "outcomes": 4608,
                  "selected_candidate_id": CANDIDATE, "ready_for_synthetic_prepare": True,
                  "decoder_reexecution": False}
    else:
        from ..cli import verify_ldpc_v5_development as dev_verify
        result = dev_verify.verify_output(dir_path, _private_test_only=False)
        if result.get("run_status") != "completed" or result.get("ready_for_synthetic_prepare") is not True:
            raise ValueError("development package not verified ready")
    docs = {name: _json_read(dir_path / name) for name in ("pre_run_plan.json", "formal_codebook_manifest.json",
                                                           "formal_selection_manifest.json", "formal_channel_model.json",
                                                           "v5_h2_manifest.json", "v5_policy_manifest.json",
                                                           "development_selection.json", "development_run_manifest.json",
                                                           "development_report.json")}
    selection = docs["formal_selection_manifest.json"]
    selected = [x["candidate_id"] for x in selection["plane_selections"]]
    policy = docs["v5_policy_manifest.json"]
    candidates = {c["candidate_id"]: c for c in policy["candidates"]}
    if CANDIDATE not in candidates:
        raise ValueError("v5-C2 policy missing")
    hashes = {name: _sha((dir_path / name).read_bytes()) for name in (
        "formal_codebook_manifest.json", "formal_selection_manifest.json",
        "formal_channel_model.json", "v5_h2_manifest.json", "v5_policy_manifest.json",
        "development_selection.json", "development_run_manifest.json", "development_report.json")}
    return {"path": str(dir_path.resolve()), "verification": result, "hashes": hashes,
            "docs": docs, "selected": selected, "candidate_policy": candidates[CANDIDATE]}


def load_development(dir_path: Path, *, private: bool) -> dict[str, Any]:
    return _load_development_cached(str(Path(dir_path).resolve()), bool(private))


def _development_root_digest(dev_dir: Path) -> dict[str, Any]:
    plan = _json_read(dev_dir / "pre_run_plan.json")
    roots = sorted(x["root_hex"] for x in plan["seed_schedule"]["roots"])
    return {"count": len(roots), "roots_sha256": _sha(_compact(roots)), "roots": roots}


def _development_seed_digest(dev_dir: Path) -> dict[str, Any]:
    plan = _json_read(dev_dir / "pre_run_plan.json")
    records = plan["seed_schedule"]["roots"]
    seed_ids: list[str] = []
    for record in records:
        root_hex = record["root_hex"]
        for rank in range(dev.FRAMES_PER_STRATUM):
            seed_ids.append(dev.derive_seed(root_hex, record["candidate_id"],
                                            record["stratum"], record["verification_round"], rank)["seed_id"])
    if len(seed_ids) != 18 * dev.FRAMES_PER_STRATUM:
        raise ValueError("development seed derivation")
    return {"count": len(seed_ids), "seed_ids_sha256": _sha(_compact(sorted(set(seed_ids)))),
            "seed_ids": sorted(set(seed_ids))}


# --- synthetic prerequisite ------------------------------------------------

def _load_synthetic(dir_path: Path, *, private: bool) -> dict[str, Any]:
    """Validate the Phase 3 synthetic package and return its verification result."""
    from . import ldpc_v5_synthetic_qualification as syn
    if private:
        # fast static check
        report = _json_read(dir_path / "synthetic_qualification_report.json")
        if report.get("run_status") != "completed" or report.get("ready_for_real_qualification") is not True:
            raise ValueError("synthetic package not ready")
        result = report
    else:
        from ..cli import verify_ldpc_v5_synthetic_qualification as syn_verify
        result = syn_verify.verify_output(dir_path, _private_test_only=False)
        if result.get("run_status") != "completed" or result.get("ready_for_real_qualification") is not True:
            raise ValueError("synthetic package not verified ready")
    hashes = {name: _sha((dir_path / name).read_bytes()) for name in (
        "synthetic_qualification_report.json",)}
    return {"path": str(dir_path.resolve()), "verification": result, "hashes": hashes}


# --- roots and seeds --------------------------------------------------------

def derive_seed(root_hex: str, stratum: str, round_: int, frame_id: int) -> dict[str, Any]:
    label = f"{RUN_ID}|{stratum}|round={round_}|frame={frame_id}".encode("ascii")
    raw = hashlib.shake_256(bytes.fromhex(root_hex) + b"\0" + label).digest(328)
    bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8), bitorder="big")[:SEED_BIT_LENGTH]
    return seed_record(bits)


def _new_roots() -> dict[str, dict[str, dict[str, str]]]:
    """Create 6 independent roots: 3 strata × 2 verification rounds."""
    out: dict[str, dict[str, dict[str, str]]] = {}
    for s in REAL_STRATA:
        out[s] = {}
        for r in (0, 1):
            raw = _new_root_hex()
            out[s][f"toeplitz_r{r}"] = {"root_hex": raw, "root_id": _root_id(raw),
                                        "verification_round": r}
    return out


def _lock_stratum_to_public(lock_stratum: str) -> str:
    """Map a lock-internal stratum name to the public stratum name."""
    pub = LOCK_TO_PUBLIC.get(lock_stratum)
    if pub is None:
        raise ValueError(f"unknown lock stratum: {lock_stratum!r}")
    return pub


def _attempt_ids(lock: Mapping[str, Any]) -> list[str]:
    """Return ordered attempt IDs from the confirmation rows, using public stratum names."""
    rows = confirmation_rows(lock)
    if len(rows) != FRAMES_PER_STRATUM * len(REAL_STRATA):
        raise ValueError("confirmation row count mismatch")
    attempt_ids = []
    for row in rows:
        pub = _lock_stratum_to_public(row["stratum"])
        frame_id = row["frame_id"]
        attempt_ids.append(f"{pub}|{frame_id}")
    return attempt_ids


def _seed_schedule(roots: Mapping[str, Mapping[str, dict[str, Any]]], lock: Mapping[str, Any],
                   *, private: bool, development_dir: Path | None = None,
                   synthetic_dir: Path | None = None) -> dict[str, Any]:
    run_id = TEST_RUN_ID if private else RUN_ID
    rows = confirmation_rows(lock)
    records = []
    all_ids: list[str] = []
    for pub_s in REAL_STRATA:
        lock_s = PUBLIC_TO_LOCK[pub_s]
        for r in (0, 1):
            root = roots[pub_s][f"toeplitz_r{r}"]
            # derive seeds for each frame id in this stratum (filter by lock stratum)
            stratum_rows = [row for row in rows if row["stratum"] == lock_s]
            ids = []
            for row in stratum_rows:
                frame_id = row["frame_id"]
                seed = derive_seed(root["root_hex"], pub_s, r, frame_id)
                ids.append(seed["seed_id"])
            records.append({"stratum": pub_s, "verification_round": r, "root_hex": root["root_hex"],
                            "root_id": _root_id(root["root_hex"]),
                            "seed_count": len(ids), "seed_ids_sha256": _sha(_compact(ids))})
            all_ids.extend(ids)
    if len(set(all_ids)) != len(REAL_STRATA) * FRAMES_PER_STRATUM * 2:
        raise ValueError("seed schedule uniqueness")
    # scan prior packages
    prior_roots, prior_seeds = dev._extract_prior()
    dev_digest = _development_root_digest(Path(development_dir) if development_dir is not None else DEVELOPMENT_PKG)
    dev_seeds = _development_seed_digest(Path(development_dir) if development_dir is not None else DEVELOPMENT_PKG)
    # synthetic package
    syn_digest = _load_synthetic(Path(synthetic_dir) if synthetic_dir is not None else SYNTHETIC_PKG, private=private)
    # synthetic seeds: need to extract from synthetic package (8 roots, 512 seeds)
    # For now, we rely on the synthetic package's seed schedule (we can compute later)
    # The contract says: scan synthetic package (8 roots, 512 seed IDs)
    # We'll compute synthetic seeds from the synthetic package's plan roots
    # (but we don't need to import the whole module, just read the plan)
    syn_plan = _json_read((Path(synthetic_dir) if synthetic_dir is not None else SYNTHETIC_PKG) / "pre_run_plan.json")
    syn_roots = syn_plan["generator"]["roots"]
    synthetic_seed_ids: list[str] = []
    for s_syn, kinds in syn_roots.items():
        for kind, record in kinds.items():
            if "toeplitz" in kind:
                root_hex = record["root_hex"]
                for rank in range(128):  # synthetic frames per stratum
                    label = f"binary_ldpc_v5_synthetic_qualification_v1|{s_syn}|round={record['verification_round']}|rank={rank}".encode("ascii")
                    raw = hashlib.shake_256(bytes.fromhex(root_hex) + b"\0" + label).digest(328)
                    bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8), bitorder="big")[:SEED_BIT_LENGTH]
                    synthetic_seed_ids.append(seed_record(bits)["seed_id"])
    if len(set(synthetic_seed_ids)) != 4 * 128:
        raise ValueError("synthetic seed derivation")
    # check collisions
    if set(all_ids) & set(dev_seeds["seed_ids"]):
        raise ValueError("development seed id collision")
    if set(all_ids) & set(synthetic_seed_ids):
        raise ValueError("synthetic seed id collision")
    base = {"schema": SEED_SCHEDULE_SCHEMA,
            "derivation": f"shake_256(root + b'\\x00' + '{run_id}|{{stratum}}|round={{round}}|frame={{frame_id}}').digest(328); unpackbits[:2623]; seed_record",
            "roots": records, "seed_count": len(REAL_STRATA) * FRAMES_PER_STRATUM * 2,
            "seed_ids_sha256": _sha(_compact(sorted(set(all_ids)))),
            "prior_root_count": len(prior_roots), "prior_roots_sha256": _sha(_compact(prior_roots)),
            "prior_seed_id_count": len(prior_seeds), "prior_seed_ids_sha256": _sha(_compact(prior_seeds)),
            "development_root_count": dev_digest["count"],
            "development_roots_sha256": dev_digest["roots_sha256"],
            "development_seed_id_count": dev_seeds["count"],
            "development_seed_ids_sha256": dev_seeds["seed_ids_sha256"],
            "synthetic_root_count": len(synthetic_seed_ids) // 128,
            "synthetic_seed_id_count": len(synthetic_seed_ids),
            "synthetic_seed_ids_sha256": _sha(_compact(sorted(set(synthetic_seed_ids)))),
            "isolated": True}
    return _self(base, "seed_schedule_sha256")


def _validate_roots(plan: Mapping[str, Any]) -> set[int]:
    """Validate root uniqueness, prior/development/synthetic isolation."""
    roots = plan.get("generator")
    if roots != {}:
        raise ValueError("generator must be empty")
    # roots are stored in seed_schedule.roots
    schedule = plan["seed_schedule"]
    root_ints: set[int] = set()
    for record in schedule["roots"]:
        raw = record.get("root_hex")
        if not isinstance(raw, str) or len(raw) != 64 or raw.lower() != raw or \
           any(c not in "0123456789abcdef" for c in raw) or record.get("root_id") != _root_id(raw):
            raise ValueError("root record")
        root_ints.add(int(raw, 16))
    if len(root_ints) != len(REAL_STRATA) * 2:
        raise ValueError("root uniqueness")
    prior_roots, prior_seeds = dev._extract_prior()
    if root_ints & {int(x, 16) for x in prior_roots}:
        raise ValueError("predecessor root collision")
    # development roots
    dev_digest = _development_root_digest(Path(plan["development_binding"]["path"]))
    if root_ints & {int(x, 16) for x in dev_digest["roots"]}:
        raise ValueError("development root collision")
    # synthetic roots: compute from synthetic plan (4 toeplitz roots)
    syn_plan = _json_read(Path(plan["synthetic_binding"]["path"]) / "pre_run_plan.json")
    syn_root_ints: set[int] = set()
    for s_syn, kinds in syn_plan["generator"]["roots"].items():
        for kind, record in kinds.items():
            if "toeplitz" in kind:
                syn_root_ints.add(int(record["root_hex"], 16))
    if root_ints & syn_root_ints:
        raise ValueError("synthetic root collision")
    # verify prior/development/synthetic digests match
    if schedule.get("prior_root_count") != len(prior_roots) or \
       schedule.get("prior_roots_sha256") != _sha(_compact(prior_roots)) or \
       schedule.get("prior_seed_id_count") != len(prior_seeds) or \
       schedule.get("prior_seed_ids_sha256") != _sha(_compact(prior_seeds)):
        raise ValueError("prior digest drift")
    if schedule.get("development_root_count") != dev_digest["count"] or \
       schedule.get("development_roots_sha256") != dev_digest["roots_sha256"]:
        raise ValueError("development digest drift")
    dev_seeds = _development_seed_digest(Path(plan["development_binding"]["path"]))
    if schedule.get("development_seed_id_count") != dev_seeds["count"] or \
       schedule.get("development_seed_ids_sha256") != dev_seeds["seed_ids_sha256"]:
        raise ValueError("development seed digest drift")
    return root_ints


# --- plan -------------------------------------------------------------------

def _load_partition_lock(lock_path: Path) -> dict[str, Any]:
    """Load and validate the partition lock."""
    lock = _json_read(lock_path)
    # basic validation
    if "partition_sha256" not in lock:
        raise ValueError("partition lock missing sha256")
    rows = confirmation_rows(lock)
    if len(rows) != FRAMES_PER_STRATUM * len(REAL_STRATA):
        raise ValueError("partition lock confirmation row count")
    return lock


def _plan(dev_bundle: Mapping[str, Any], syn_bundle: Mapping[str, Any],
          lock: Mapping[str, Any], roots: Mapping[str, Mapping[str, dict[str, Any]]],
          *, test_only: bool, output_dir: Path) -> dict[str, Any]:
    schedule = _seed_schedule(roots, lock, private=test_only,
                              development_dir=Path(dev_bundle["path"]),
                              synthetic_dir=Path(syn_bundle["path"]))
    attempt_ids = _attempt_ids(lock)
    binding = dev_bundle["docs"]
    base = {"schema": TEST_PLAN_SCHEMA if test_only else PLAN_SCHEMA,
            "run_id": TEST_RUN_ID if test_only else RUN_ID, "method_id": METHOD, "role": ROLE,
            "domain": {"dimension": Q, "frame_len_symbols": N, "mapping": MAPPING,
                       "candidate": CANDIDATE, "strata": list(REAL_STRATA),
                       "frame_count_per_stratum": FRAMES_PER_STRATUM},
            "execution": {"order": "stratum_frame", "attempt_ids": attempt_ids,
                          "attempt_ids_sha256": _sha(_compact(attempt_ids))},
            "output_binding": {"output_directory": output_dir.resolve().relative_to(_REPO).as_posix(),
                               "artifact_names": list(ARTIFACTS), "prepare_file_set": [ARTIFACTS[0]]},
            "development_binding": {"path": dev_bundle["path"], "artifact_hashes": dev_bundle["hashes"],
                                    "selected_candidate_id": CANDIDATE,
                                    "ready_for_synthetic_prepare": True,
                                    "development_run_status": "completed",
                                    "codebook_manifest_sha256": dev_bundle["hashes"]["formal_codebook_manifest.json"],
                                    "selection_manifest_sha256": dev_bundle["hashes"]["formal_selection_manifest.json"],
                                    "channel_model_sha256": dev_bundle["hashes"]["formal_channel_model.json"],
                                    "h2_manifest_sha256": dev_bundle["hashes"]["v5_h2_manifest.json"],
                                    "policy_manifest_sha256": dev_bundle["hashes"]["v5_policy_manifest.json"],
                                    "codebook": binding["formal_codebook_manifest.json"],
                                    "selection": binding["formal_selection_manifest.json"],
                                    "channel_model": binding["formal_channel_model.json"],
                                    "h2_manifest": binding["v5_h2_manifest.json"],
                                    "policy_manifest": binding["v5_policy_manifest.json"]},
            "partition_binding": {"lock_path": str(Path(PARTITION_LOCK).resolve()),
                                  "partition_sha256": lock["partition_sha256"],
                                  "confirmation_row_digest": _sha(_compact(confirmation_rows(lock))),
                                  "confirmation_count_per_stratum": FRAMES_PER_STRATUM,
                                  "confirmation_access_api": "confirmation_arrays_for_frame"},
            "synthetic_binding": {"path": syn_bundle["path"],
                                  "report_sha256": syn_bundle["hashes"]["synthetic_qualification_report.json"],
                                  "ready_for_real_qualification": True},
            "generator": {},
            "seed_schedule": schedule,
            "gates": {"denominator_per_stratum": FRAMES_PER_STRATUM,
                      "successes_per_stratum": GATE_SUCCESSES,
                      "forbidden_failure_count_limit": 0, "strata": list(REAL_STRATA)},
            "caps": {"complete_run_s": COMPLETE_RUN_CAP_S, "per_frame_wall_s": 10.0,
                     "per_frame_decoder_calls": 20, "per_frame_events": 32},
            "failure_policy": FAILURE_POLICY, "scoped_source_sha256": _hashes(),
            "environment": _environment(test_only)}
    provisional = _self(base, "plan_sha256")
    _validate_plan(provisional, test_only=test_only, output_dir=output_dir)
    return provisional


def prepare_plan(output_dir: Path, partition_lock: Path) -> dict[str, Any]:
    """Production prepare: exact official paths, fresh directory, plan only."""
    output_dir = Path(output_dir)
    partition_lock = Path(partition_lock)
    if output_dir.resolve() != OFFICIAL_OUTPUT.resolve():
        raise ValueError("official output path required")
    if partition_lock.resolve() != PARTITION_LOCK.resolve():
        raise ValueError("partition lock path required")
    if output_dir.exists():
        raise FileExistsError("fresh output directory required")
    dev_bundle = load_development(DEVELOPMENT_PKG, private=False)
    syn_bundle = _load_synthetic(SYNTHETIC_PKG, private=False)
    lock = _load_partition_lock(partition_lock)
    roots = _new_roots()
    plan = _plan(dev_bundle, syn_bundle, lock, roots, test_only=False, output_dir=output_dir)
    output_dir.mkdir(parents=True)
    _json(output_dir / ARTIFACTS[0], plan)
    return plan


def _prepare_test_plan(output_dir: Path, partition_lock: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError("fresh output directory required")
    dev_bundle = load_development(DEVELOPMENT_PKG, private=True)
    syn_bundle = _load_synthetic(SYNTHETIC_PKG, private=True)
    lock = _load_partition_lock(partition_lock)
    roots = _new_roots()
    plan = _plan(dev_bundle, syn_bundle, lock, roots, test_only=True, output_dir=output_dir)
    output_dir.mkdir(parents=True)
    _json(output_dir / ARTIFACTS[0], plan)
    return plan


def _validate_plan(plan: Mapping[str, Any], *, test_only: bool, output_dir: Path) -> dict[str, Any]:
    if not isinstance(plan, Mapping):
        raise ValueError("plan type")
    supplied = dict(plan)
    digest = supplied.pop("plan_sha256", None)
    if not isinstance(digest, str) or _sha(_compact(supplied)) != digest:
        raise ValueError("plan self hash")
    if plan.get("schema") != (TEST_PLAN_SCHEMA if test_only else PLAN_SCHEMA) or \
       plan.get("run_id") != (TEST_RUN_ID if test_only else RUN_ID) or \
       plan.get("method_id") != METHOD or plan.get("role") != ROLE:
        raise ValueError("plan identity")
    domain = plan.get("domain")
    if domain != {"dimension": Q, "frame_len_symbols": N, "mapping": MAPPING, "candidate": CANDIDATE,
                  "strata": list(REAL_STRATA), "frame_count_per_stratum": FRAMES_PER_STRATUM}:
        raise ValueError("plan domain")
    # execution: need to compare attempt_ids
    lock = _load_partition_lock(Path(plan["partition_binding"]["lock_path"]))
    expected_attempt_ids = _attempt_ids(lock)
    if plan.get("execution") != {"order": "stratum_frame", "attempt_ids": expected_attempt_ids,
                                 "attempt_ids_sha256": _sha(_compact(expected_attempt_ids))}:
        raise ValueError("plan execution")
    expected_out = {"output_directory": output_dir.resolve().relative_to(_REPO).as_posix(),
                    "artifact_names": list(ARTIFACTS), "prepare_file_set": [ARTIFACTS[0]]}
    if plan.get("output_binding") != expected_out:
        raise ValueError("plan output binding")
    dev_bundle = load_development(Path(plan["development_binding"]["path"]), private=test_only)
    binding = plan.get("development_binding")
    if binding is None or binding.get("artifact_hashes") != dev_bundle["hashes"] or \
       binding.get("selected_candidate_id") != CANDIDATE or \
       binding.get("ready_for_synthetic_prepare") is not True or \
       binding.get("development_run_status") != "completed":
        raise ValueError("development binding")
    expected = {"codebook_manifest_sha256": dev_bundle["hashes"]["formal_codebook_manifest.json"],
                "selection_manifest_sha256": dev_bundle["hashes"]["formal_selection_manifest.json"],
                "channel_model_sha256": dev_bundle["hashes"]["formal_channel_model.json"],
                "h2_manifest_sha256": dev_bundle["hashes"]["v5_h2_manifest.json"],
                "policy_manifest_sha256": dev_bundle["hashes"]["v5_policy_manifest.json"],
                "codebook": dev_bundle["docs"]["formal_codebook_manifest.json"],
                "selection": dev_bundle["docs"]["formal_selection_manifest.json"],
                "channel_model": dev_bundle["docs"]["formal_channel_model.json"],
                "h2_manifest": dev_bundle["docs"]["v5_h2_manifest.json"],
                "policy_manifest": dev_bundle["docs"]["v5_policy_manifest.json"]}
    for key in expected:
        if binding.get(key) != expected[key]:
            raise ValueError(f"development binding {key}")
    # partition binding
    pb = plan.get("partition_binding")
    if pb is None or pb.get("lock_path") != str(Path(PARTITION_LOCK).resolve()) or \
       pb.get("partition_sha256") != lock["partition_sha256"] or \
       pb.get("confirmation_row_digest") != _sha(_compact(confirmation_rows(lock))) or \
       pb.get("confirmation_count_per_stratum") != FRAMES_PER_STRATUM or \
       pb.get("confirmation_access_api") != "confirmation_arrays_for_frame":
        raise ValueError("partition binding")
    # synthetic binding
    sb = plan.get("synthetic_binding")
    syn_bundle = _load_synthetic(Path(sb["path"]), private=test_only)
    if sb is None or sb.get("path") != syn_bundle["path"] or \
       sb.get("report_sha256") != syn_bundle["hashes"]["synthetic_qualification_report.json"] or \
       sb.get("ready_for_real_qualification") is not True:
        raise ValueError("synthetic binding")
    # generator must be empty
    if plan.get("generator") != {}:
        raise ValueError("generator must be empty")
    # gates
    expected_gates = {"denominator_per_stratum": FRAMES_PER_STRATUM, "successes_per_stratum": GATE_SUCCESSES,
                      "forbidden_failure_count_limit": 0, "strata": list(REAL_STRATA)}
    if plan.get("gates") != expected_gates:
        raise ValueError("plan gates")
    if plan.get("caps") != {"complete_run_s": COMPLETE_RUN_CAP_S, "per_frame_wall_s": 10.0,
                            "per_frame_decoder_calls": 20, "per_frame_events": 32}:
        raise ValueError("plan caps")
    if plan.get("failure_policy") != FAILURE_POLICY:
        raise ValueError("plan failure policy")
    # reconstruct roots dict from seed schedule records for validation
    roots_recon: dict[str, dict[str, dict[str, Any]]] = {}
    for rec in plan["seed_schedule"]["roots"]:
        s = rec["stratum"]
        r = rec["verification_round"]
        if s not in roots_recon:
            roots_recon[s] = {}
        roots_recon[s][f"toeplitz_r{r}"] = {"root_hex": rec["root_hex"],
                                            "root_id": _root_id(rec["root_hex"]),
                                            "verification_round": r}
    if plan.get("seed_schedule") != _seed_schedule(roots_recon, lock,
                                                    private=test_only,
                                                    development_dir=Path(plan["development_binding"]["path"]),
                                                    synthetic_dir=Path(plan["synthetic_binding"]["path"])):
        raise ValueError("seed schedule reconstruction")
    _validate_roots(plan)
    if not test_only and (plan.get("scoped_source_sha256") != _hashes() or
                          importlib.metadata.version("ldpc") != "2.4.1"):
        raise ValueError("production source/backend drift")
    return dict(plan)


# --- execution --------------------------------------------------------------

def _gate(rows: list[Mapping[str, Any]], stratum: str, denominator: int, floor: int) -> dict[str, Any]:
    rows_s = [r for r in rows if str(r.get("plan_frame_id", "")).split("|")[0] == stratum]
    success = sum(r.get("status") == "verified_success" for r in rows_s)
    forbidden = sum(r.get("status") in FORBIDDEN_STATUSES for r in rows_s)
    return {"denominator": len(rows_s), "verified_success": success,
            "forbidden_failure_count": forbidden,
            "passed": len(rows_s) == denominator and success >= floor and forbidden == 0}


def _finalize(out: Path, plan: Mapping[str, Any], rows: list[dict[str, Any]],
              events: list[Mapping[str, Any]], status: str, reason: str, *, test_only: bool) -> None:
    binding = plan["development_binding"]
    for name, obj in ((ARTIFACTS[1], binding["codebook"]), (ARTIFACTS[2], binding["selection"]),
                      (ARTIFACTS[3], binding["channel_model"]), (ARTIFACTS[4], binding["h2_manifest"]),
                      (ARTIFACTS[5], binding["policy_manifest"])):
        if not (out / name).exists():
            _json(out / name, obj)
    if not (out / ARTIFACTS[6]).exists():
        _write(out / ARTIFACTS[6], encode_outcome_csv_v5(rows) if rows else b"")
    if not (out / ARTIFACTS[7]).exists():
        _write(out / ARTIFACTS[7], b"".join(canonical_event_v5(e) for e in events))
    index = {name: {"sha256": _sha((out / name).read_bytes()), "bytes": (out / name).stat().st_size}
             for name in ARTIFACTS[1:8]}
    denominator = int(plan["gates"]["denominator_per_stratum"])
    floor = int(plan["gates"]["successes_per_stratum"])
    gates = {s: _gate(rows, s, denominator, floor) for s in REAL_STRATA}
    promoted = status == "completed" and all(g["passed"] for g in gates.values())
    run_status = ("completed" if promoted else "non_promoted") if status == "completed" else "invalid_execution"
    manifest = _self({"schema": TEST_RUN_MANIFEST_SCHEMA if test_only else RUN_MANIFEST_SCHEMA,
                      "run_id": TEST_RUN_ID if test_only else RUN_ID, "run_status": run_status,
                      "stop_reason": reason, "plan_sha256": plan["plan_sha256"],
                      "outcome_count": len(rows), "artifact_file_sha256": index,
                      "decoder_reexecution": False}, "run_manifest_sha256")
    if not (out / ARTIFACTS[8]).exists():
        _json(out / ARTIFACTS[8], manifest)
    report = _self({"schema": TEST_REPORT_SCHEMA if test_only else REPORT_SCHEMA,
                    "run_id": TEST_RUN_ID if test_only else RUN_ID, "run_status": run_status,
                    "stop_reason": reason, "plan_sha256": plan["plan_sha256"],
                    "run_manifest_sha256": manifest["run_manifest_sha256"],
                    "promotion_gates": gates, "promoted": promoted,
                    "ready_for_real_qualification": promoted,
                    "decoder_reexecution": False}, "report_sha256")
    if not (out / ARTIFACTS[9]).exists():
        _json(out / ARTIFACTS[9], report)


def _csv_row(attempt_id: str, outcome: Mapping[str, Any], alice: np.ndarray, bob: np.ndarray,
             transcript: bytes) -> dict[str, Any]:
    stratum, frame_id = attempt_id.split("|")
    return {"role": "real", "stratum": stratum, "plan_frame_id": attempt_id,
            "alice_sha256": _sha(np.asarray(alice, dtype="<u2").tobytes()),
            "bob_sha256": _sha(np.asarray(bob, dtype="<u2").tobytes()),
            "transcript_bytes_len": len(transcript), "transcript_bytes_sha256": _sha(transcript),
            **dict(outcome)}


def _package_failure_outcome(attempt_id: str, cls: str, reason: str) -> dict[str, Any]:
    stratum, frame_id = attempt_id.split("|")
    base = {"dataset_id": f"real_10db_{stratum}", "frame_id": attempt_id, "n_pairs": N,
            "pair_idx_sequence_sha256": _sha(_compact([])), "method": METHOD,
            "candidate_id": CANDIDATE, "attempted": False, "denominator_included": False,
            "status": "invalid_input", "failure_reason": f"package_{cls}:{reason}",
            "dimension": Q, "frame_len_symbols": N, "raw_ser": 0.0,
            "fallback_invoked": False, "rounds_attempted": 1, "verification_invoked": False,
            "verification_seed_id_round0": "", "verification_seed_id_round1": "",
            "verification_tag_bits": 0, "epsilon_ec": 0.0,
            "key_dependent_disclosure_bits_total": 0, "public_control_bits_total": 0,
            "transcript_first_event_id": None, "transcript_last_event_id": None,
            "transcript_sha256": _sha(b""), "runtime_s": 0.0,
            "decoder_call_count": 0, "verification_check_count": 0, "ldpc_syndrome_bits": 0,
            "h1_syndrome_bits": 0, "h2_syndrome_bits": 0, "verification_tag_bits_component": 0,
            "feedback_control_bits": 0, "selection_sha256": "", "channel_model_sha256": "",
            "h1_codebook_manifest_sha256": "", "h2_manifest_sha256": "", "policy_sha256": "",
            "mapping": MAPPING, "leakage_comparison_policy": "method_specific_not_cross_ranked",
            "backend_name": "", "backend_version": ""}
    return base


def _execute(out: Path, runner: Callable[..., dict[str, Any]], *, test_only: bool) -> None:
    if not out.is_dir() or {x.name for x in out.iterdir()} != {ARTIFACTS[0]}:
        raise ValueError("execute requires only reviewed plan")
    plan = _validate_plan(_json_read(out / ARTIFACTS[0]), test_only=test_only, output_dir=out)
    lock = _load_partition_lock(Path(plan["partition_binding"]["lock_path"]))
    rows_confirmation = confirmation_rows(lock)
    # build a mapping from attempt_id to (row, alice, bob)
    frame_data: dict[str, tuple[dict[str, Any], np.ndarray, np.ndarray]] = {}
    for row in rows_confirmation:
        pub = _lock_stratum_to_public(row["stratum"])
        attempt_id = f"{pub}|{row['frame_id']}"
        alice, bob = confirmation_arrays_for_frame(lock, row)
        frame_data[attempt_id] = (row, alice, bob)
    schedule = {(r["stratum"], r["verification_round"]): r["root_hex"]
                for r in plan["seed_schedule"]["roots"]}
    policy = plan["development_binding"]["policy_manifest"]
    candidate_policy = next(c for c in policy["candidates"] if c["candidate_id"] == CANDIDATE)
    rows: list[dict[str, Any]] = []
    events: list[Mapping[str, Any]] = []
    started = time.monotonic()
    current: str | None = None
    appended_current = False
    attempt_ids = plan["execution"]["attempt_ids"]
    total = len(attempt_ids)
    try:
        for attempt_idx, attempt_id in enumerate(attempt_ids):
            if attempt_idx and attempt_idx % 64 == 0:
                elapsed = time.monotonic() - started
                rate = attempt_idx / elapsed if elapsed > 0 else 0.0
                eta = (total - attempt_idx) / rate if rate > 0 else float("nan")
                logger.info("real execute progress: %d/%d attempts (%.0f%%) after %.1fs, %.0f/s, eta %.0fs",
                            attempt_idx, total, 100.0 * attempt_idx / total, elapsed, rate, eta)
            if time.monotonic() - started >= float(plan["caps"]["complete_run_s"]):
                raise TimeoutError("complete_run_cap")
            stratum, frame_id_str = attempt_id.split("|")
            frame_id = int(frame_id_str)
            row, alice, bob = frame_data[attempt_id]
            current = attempt_id
            appended_current = False
            seeds = [derive_seed(schedule[(stratum, r)], stratum, r, frame_id) for r in (0, 1)]
            result = runner(alice, bob, pair_idx_sequence=np.arange(N, dtype=np.int64),
                            dataset_id=f"real_10db_{stratum}", frame_id=frame_id_str,
                            stratum=stratum, candidate_policy=candidate_policy,
                            policy_manifest=plan["development_binding"]["policy_manifest"],
                            selection_manifest=plan["development_binding"]["selection"],
                            channel_model=plan["development_binding"]["channel_model"],
                            h2_manifest=plan["development_binding"]["h2_manifest"],
                            locked_seeds=seeds)
            outcome = dict(result["outcome"])
            es = list(result["events"])
            validate_outcome_v5(outcome, es)
            if not bool(outcome["attempted"]) and not np.isfinite(float(outcome["raw_ser"])):
                outcome = _package_failure_outcome(attempt_id, "unclassified",
                                                    str(outcome["failure_reason"]) or str(outcome["status"]))
                es = []
                transcript = b""
            elif bool(outcome["attempted"]):
                verify_public_payload_v5(outcome, es, alice_symbols=alice,
                                         pair_idx_sequence=np.arange(N, dtype=np.int64),
                                         stratum=stratum, candidate_policy=candidate_policy,
                                         policy_manifest=plan["development_binding"]["policy_manifest"],
                                         selection_manifest=plan["development_binding"]["selection"],
                                         channel_model=plan["development_binding"]["channel_model"],
                                         h2_manifest=plan["development_binding"]["h2_manifest"],
                                         locked_seeds=seeds)
                transcript = b"".join(canonical_event_v5(e) for e in es)
            else:
                transcript = b""
            row_csv = _csv_row(attempt_id, outcome, alice, bob, transcript)
            rows.append(row_csv)
            events.extend(es)
            appended_current = True
        if len(rows) != total:
            raise RuntimeError("outcome accounting")
        _finalize(out, plan, rows, events, "completed", "", test_only=test_only)
    except Exception as exc:
        if current is not None and not appended_current:
            stratum_c, frame_id_c = current.split("|")
            row_c, alice_c, bob_c = frame_data[current]
            rows.append(_csv_row(current, _package_failure_outcome(current, "internal", f"{type(exc).__name__}:{exc}"),
                                 alice_c, bob_c, b""))
        if not rows:
            first = attempt_ids[0]
            stratum_f, frame_id_f = first.split("|")
            row_f, alice_f, bob_f = frame_data[first]
            rows.append(_csv_row(first, _package_failure_outcome(first, "internal", f"{type(exc).__name__}:{exc}"),
                                 alice_f, bob_f, b""))
        _finalize(out, plan, rows, events, "invalid_execution", f"{type(exc).__name__}:{exc}", test_only=test_only)
        if not test_only:
            raise


def execute_plan(output_dir: Path) -> None:
    _execute(output_dir, run_ldpc_formal_v5, test_only=False)


def _execute_test_plan(output_dir: Path, runner: Callable[..., dict[str, Any]]) -> None:
    _execute(output_dir, runner, test_only=True)