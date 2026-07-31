"""Immutable v1 sacrificed-development package for binary LDPC v5.

Implements the frozen Phase 2 development contract (prepare once, main
review, execute once, read-only verify once; no-overwrite, non-resumable,
immutable failure retention).  Production entry points expose no test switch;
private test helpers require explicit fakes and a test-owned workspace root.
"""
from __future__ import annotations
import hashlib, importlib.metadata, json, os, platform, secrets, time
from functools import cmp_to_key
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
import numpy as np
from .codebook_v5_h2 import h2_manifest, verify_h2_manifest
from .ldpc_v5 import (METHOD, run_ldpc_formal_v5, build_v5_policy_manifest,
                      verify_v5_policy_manifest, _selected_candidates,
                      validate_outcome_v5, verify_public_payload_v5,
                      encode_outcome_csv_v5, canonical_event_v5, OUTCOME_FIELDS)
from .ldpc_v5_partition import development_arrays_for_frame, development_rows, validate_partition_lock
from .shared import seed_record

RUN_ID = "binary_ldpc_v5_development_v1"
TEST_RUN_ID = "binary_ldpc_v5_development_test_v1"
METHOD_ID = METHOD
ROLE = "sacrificed_development"
N = 256
Q = 1024
MAPPING = "gray"
CANDIDATES = ("V5-C0", "V5-C1", "V5-C2")
STRATA = ("bw120", "bw180", "bw200")
FRAMES_PER_STRATUM = 512
SEED_BIT_LENGTH = 2623
DERIVATION = ("shake_256(bytes.fromhex(root_hex) + b'\\x00' + label).digest(328); "
              "bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8), bitorder='big')[:2623]; "
              "seed_record(bits); "
              "label = 'binary_ldpc_v5_development_v1|{candidate}|{stratum}|round={round}|rank={rank}'")
PLAN_SCHEMA = "binary_ldpc_v5_development_plan_v1"
TEST_PLAN_SCHEMA = "binary_ldpc_v5_development_plan_test_v1"
SELECTION_SCHEMA = "binary_ldpc_v5_development_selection_v1"
TEST_SELECTION_SCHEMA = "binary_ldpc_v5_development_selection_test_v1"
RUN_MANIFEST_SCHEMA = "binary_ldpc_v5_development_run_manifest_v1"
TEST_RUN_MANIFEST_SCHEMA = "binary_ldpc_v5_development_run_manifest_test_v1"
REPORT_SCHEMA = "binary_ldpc_v5_development_report_v1"
TEST_REPORT_SCHEMA = "binary_ldpc_v5_development_report_test_v1"
SEED_SCHEDULE_SCHEMA = "binary_ldpc_v5_development_seed_schedule_v1"
ARTIFACTS = ("pre_run_plan.json", "partition_lock.json", "formal_codebook_manifest.json",
             "formal_selection_manifest.json", "formal_channel_model.json", "v5_h2_manifest.json",
             "v5_policy_manifest.json", "development_frame_outcomes.csv",
             "development_transcript.jsonl", "development_selection.json",
             "development_run_manifest.json", "development_report.json")
FORBIDDEN_CLASSES = ("backend", "source", "internal", "accounting", "resource",
                     "syndrome", "unclassified", "provenance")
FAILURE_POLICY = "immutable_partial_finalization_no_resume_no_rerun_no_tuning"

_REPO = Path(__file__).resolve().parents[4]
_ROOT = _REPO / "comparison_bench" / "outputs_comparison" / "formal_ir_methods"
OFFICIAL_OUTPUT = _ROOT / "20260731_v1_binary_ldpc_v5_development"
PARTITION_LOCK = _ROOT / "20260731_v1_binary_ldpc_v5_partition" / "partition_lock.json"
SYNTHETIC_PKG = _ROOT / "20260728_v2_binary_ldpc_v4_synthetic"

PARTITION_LOCK_FILE_SHA256 = "17c128830e5e23dca0d1ddfabf1d3853b2d975e6f65a477bdb52eea4baf5b943"
PARTITION_SHA256 = "060fe8e00542a0aa8a87f978018b4d8d956413a3829c6ab5b32a47d3998cd051"
PREDECESSOR_BINDING_SHA256 = "d1c888bd09bdaf1ad186292e4bfe14bbef32897d75061b9836b6ac1c95222e3a"
PRIOR_ROOT_COUNT = 26
PRIOR_ROOTS_SHA256 = "afe519e096df61a39093c9ea4952f9c2ff7bade8c0aaa9a29c21d1525609766b"
PRIOR_SEED_ID_COUNT = 1472
PRIOR_SEED_IDS_SHA256 = "7be045ed771b15f17f0e41dd9163471c1bfe7cde5332c75faf42b73bdc8c8386"
SHARED_SELECTION = "5d3757f7e36e117877e9c2d75fa1e90496d83cc080171cfaa4f3299c44b6b4dd"
SHARED_CODEBOOK = "786b48287f0b453a668c1ae1bdab2126aa7d13aeb94439860b80899a34687500"
SHARED_CHANNEL = "83a80a2db8d7b7cacc63e5e7531ecc7d4bd4e93605af53aa2fa987257d15cf6c"
EMPTY_HASH = hashlib.sha256(b"").hexdigest()
COMPLETE_RUN_CAP_S = 14400

# Only these four predecessor packages carry plan/transcript root and seed
# records per the frozen whitelist; the v4 development package contributes none.
_PRE_PACKAGES = (
    ("20260728_v2_binary_ldpc_v4_synthetic", "pre_run_plan.json", "formal_transcript.jsonl"),
    ("20260729_v1_binary_ldpc_v4_16db_transfer", "pre_run_plan.json", "formal_transcript.jsonl"),
    ("20260729_v1_binary_ldpc_v4_10db_transfer", "pre_run_plan.json", None),
    ("20260729_v2_binary_ldpc_v4_10db_transfer", "pre_run_plan.json", "formal_transcript.jsonl"),
)
_SCOPED = ("cli/run_ldpc_v5_development.py", "cli/verify_ldpc_v5_development.py",
           "formal_ir/ldpc_v5_development.py", "formal_ir/ldpc_v5.py",
           "formal_ir/ldpc_v5_partition.py", "formal_ir/ldpc_v5_predecessors.py",
           "formal_ir/codebook_v5_h2.py", "formal_ir/codebook_v4.py",
           "formal_ir/ldpc_v4_channel.py", "formal_ir/ldpc_v4_10db_source.py",
           "formal_ir/shared.py", "utils/bitops.py",
           "cli/run_ldpc_v4_16db_transfer_qualification.py",
           "cli/verify_ldpc_v4_synthetic_qualification.py",
           "cli/verify_ldpc_v4_16db_transfer_qualification.py",
           "cli/verify_ldpc_v4_10db_transfer_qualification_v2.py",
           "cli/run_ldpc_v4_development_v2.py", "cli/verify_ldpc_v4_development_v2.py",
           "cli/run_ldpc_v4_development.py")


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


def _normalize_root(value: Any) -> str:
    if isinstance(value, int):
        return f"{value:064x}"
    if isinstance(value, str):
        if not value or any(c not in "0123456789abcdefABCDEF" for c in value):
            raise ValueError("predecessor root hex")
        return f"{int(value, 16):064x}"
    raise ValueError("predecessor root type")


def _normalize_seed_id(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower() or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("predecessor seed id")
    return value


def _extract_prior() -> tuple[list[str], list[str]]:
    """Frozen whitelist extraction from the four bound predecessor packages."""
    roots: list[str] = []
    seeds: list[str] = []
    for directory, plan_name, transcript_name in _PRE_PACKAGES:
        package = _ROOT / directory
        plan = json.loads((package / plan_name).read_bytes())
        if directory == "20260728_v2_binary_ldpc_v4_synthetic":
            for record in plan["development_root_binding"]["roots"]:
                roots.append(_normalize_root(record["root_hex"]))
            for stratum in plan["generator"]["roots"].values():
                for record in stratum.values():
                    roots.append(_normalize_root(record["root_hex"]))
            for value in plan["v3_seed_binding"]["root_seeds"].values():
                roots.append(_normalize_root(value))
            seeds.extend(_normalize_seed_id(value) for value in plan["v3_seed_binding"]["toeplitz_seed_ids"])
        else:
            for record in plan["roots"].values():
                roots.append(_normalize_root(record["root_hex"]))
                seeds.extend(_normalize_seed_id(seed["seed_id"]) for seed in record["seeds"])
        if transcript_name is not None:
            for line in (package / transcript_name).read_bytes().splitlines():
                event = json.loads(line)
                if event.get("event_type") == "VERIFICATION_SEED":
                    seeds.append(_normalize_seed_id(event["payload"]["seed_id"]))
    return sorted(set(roots)), sorted(set(seeds))


def _prior_digests() -> tuple[str, str]:
    roots, seeds = _extract_prior()
    if len(roots) != PRIOR_ROOT_COUNT or len(seeds) != PRIOR_SEED_ID_COUNT:
        raise ValueError("predecessor prior set drift")
    roots_sha = _sha(_compact(roots))
    seeds_sha = _sha(_compact(seeds))
    if roots_sha != PRIOR_ROOTS_SHA256 or seeds_sha != PRIOR_SEED_IDS_SHA256:
        raise ValueError("predecessor prior digest drift")
    return roots_sha, seeds_sha


def derive_seed(root_hex: str, candidate: str, stratum: str, round_: int, rank: int) -> dict[str, Any]:
    label = f"binary_ldpc_v5_development_v1|{candidate}|{stratum}|round={round_}|rank={rank}".encode("ascii")
    raw = hashlib.shake_256(bytes.fromhex(root_hex) + b"\0" + label).digest(328)
    bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8), bitorder="big")[:SEED_BIT_LENGTH]
    return seed_record(bits)


def _new_root_hex() -> str:
    return secrets.token_bytes(32).hex()


def _seed_schedule(roots: Sequence[str]) -> dict[str, Any]:
    if len(roots) != 18 or len(set(roots)) != 18:
        raise ValueError("seed schedule roots")
    records = []
    all_ids: list[str] = []
    for candidate in CANDIDATES:
        for stratum in STRATA:
            for round_ in (0, 1):
                root_hex = roots[CANDIDATES.index(candidate) * 6 + STRATA.index(stratum) * 2 + round_]
                ids = sorted(derive_seed(root_hex, candidate, stratum, round_, rank)["seed_id"] for rank in range(FRAMES_PER_STRATUM))
                records.append({"candidate_id": candidate, "stratum": stratum, "verification_round": round_,
                                "root_hex": root_hex, "seed_count": FRAMES_PER_STRATUM,
                                "seed_ids_sha256": _sha(_compact(ids))})
                all_ids.extend(ids)
    if len(set(all_ids)) != 18 * FRAMES_PER_STRATUM:
        raise ValueError("seed schedule uniqueness")
    prior_roots_sha, prior_seeds_sha = _prior_digests()
    base = {"schema": SEED_SCHEDULE_SCHEMA, "derivation": DERIVATION, "roots": records,
            "seed_count": 18 * FRAMES_PER_STRATUM, "seed_ids_sha256": _sha(_compact(sorted(set(all_ids)))),
            "prior_root_count": PRIOR_ROOT_COUNT, "prior_roots_sha256": prior_roots_sha,
            "prior_seed_id_count": PRIOR_SEED_ID_COUNT, "prior_seed_ids_sha256": prior_seeds_sha,
            "isolated": True}
    return _self(base, "seed_schedule_sha256")


def _source_method_bytes() -> tuple[bytes, bytes, bytes]:
    codebook = (SYNTHETIC_PKG / "formal_codebook_manifest.json").read_bytes()
    selection = (SYNTHETIC_PKG / "formal_selection_manifest.json").read_bytes()
    channel = (SYNTHETIC_PKG / "formal_channel_model.json").read_bytes()
    if _sha(codebook) != SHARED_CODEBOOK or _sha(selection) != SHARED_SELECTION or _sha(channel) != SHARED_CHANNEL:
        raise ValueError("method source drift")
    return codebook, selection, channel


def _method_objects() -> dict[str, Any]:
    """Deterministic manifests/policies and their content self-hashes."""
    codebook_bytes, selection_bytes, channel_bytes = _source_method_bytes()
    selection = json.loads(selection_bytes.decode("ascii"))
    _selected_candidates(selection)
    selected = [x["candidate_id"] for x in selection["plane_selections"]]
    h2 = h2_manifest(selected, h1_codebook_manifest_sha256=selection["codebook_manifest_sha256"],
                     h1_selection_sha256=selection["selection_sha256"])
    verify_h2_manifest(h2, selected)
    policy = build_v5_policy_manifest(selected_candidates=selected,
                                      selection_sha256=selection["selection_sha256"],
                                      codebook_manifest_sha256=selection["codebook_manifest_sha256"],
                                      channel_model_sha256=selection["channel_model_sha256"], h2_manifest=h2)
    verify_v5_policy_manifest(policy, selected_candidates=selected,
                              selection_sha256=selection["selection_sha256"],
                              codebook_manifest_sha256=selection["codebook_manifest_sha256"],
                              channel_model_sha256=selection["channel_model_sha256"], h2_manifest=h2)
    bindings = {"h1_codebook_manifest_sha256": _sha(codebook_bytes),
                "h1_selection_sha256": _sha(selection_bytes),
                "channel_model_sha256": _sha(channel_bytes),
                "h2_manifest_sha256": _sha(_compact(h2)),
                "policy_manifest_sha256": _sha(_compact(policy))}
    return {"codebook_bytes": codebook_bytes, "selection_bytes": selection_bytes,
            "channel_bytes": channel_bytes, "selection": selection, "channel": json.loads(channel_bytes.decode("ascii")),
            "h2": h2, "policy": policy, "selected": selected, "bindings": bindings}


def _attempt_ids() -> list[str]:
    return [f"{c}|{s}|{rank}" for c in CANDIDATES for s in STRATA for rank in range(FRAMES_PER_STRATUM)]


def _static_lock_checks(lock: Mapping[str, Any]) -> None:
    supplied = dict(lock)
    digest = supplied.pop("partition_sha256", None)
    if not isinstance(digest, str) or _sha(_compact(supplied)) != digest:
        raise ValueError("partition local self hash")
    if lock["partition_sha256"] != PARTITION_SHA256:
        raise ValueError("partition content hash")
    if int(lock["role_digests"]["development_count"]) != 1536 or int(lock["role_digests"]["confirmation_count"]) != 384:
        raise ValueError("partition counts")
    if lock["predecessor_binding"]["binding_sha256"] != PREDECESSOR_BINDING_SHA256:
        raise ValueError("predecessor binding hash")


def _static_development_rows(lock: Mapping[str, Any]) -> list[dict[str, Any]]:
    _static_lock_checks(lock)
    return [dict(x) for x in lock["role_rows"] if x["role"] == "development"]


def _plan(lock: Mapping[str, Any], partition_bytes: bytes, method: Mapping[str, Any],
          roots: list[str], *, test_only: bool, output_dir: Path) -> dict[str, Any]:
    schedule = _seed_schedule(roots)
    attempt_ids = _attempt_ids()
    base = {"schema": TEST_PLAN_SCHEMA if test_only else PLAN_SCHEMA,
            "run_id": TEST_RUN_ID if test_only else RUN_ID, "method_id": METHOD_ID, "role": ROLE,
            "domain": {"dimension": Q, "frame_len_symbols": N, "mapping": MAPPING,
                       "candidates": list(CANDIDATES), "strata": list(STRATA),
                       "development_frames_per_stratum": FRAMES_PER_STRATUM},
            "execution": {"order": "candidate_stratum_role_rank", "attempt_ids": attempt_ids,
                          "attempt_ids_sha256": _sha(_compact(attempt_ids))},
            "output_binding": {"output_directory": output_dir.resolve().relative_to(_REPO).as_posix(),
                               "artifact_names": list(ARTIFACTS), "prepare_file_set": [ARTIFACTS[0]]},
            "partition_binding": {"path": PARTITION_LOCK.relative_to(_REPO).as_posix(),
                                  "file_sha256": _sha(partition_bytes),
                                  "partition_sha256": lock["partition_sha256"],
                                  "development_rows_sha256": lock["role_digests"]["development_rows_sha256"],
                                  "development_count": int(lock["role_digests"]["development_count"]),
                                  "confirmation_count": int(lock["role_digests"]["confirmation_count"])},
            "predecessor_binding_sha256": lock["predecessor_binding"]["binding_sha256"],
            "method_bindings": method["bindings"], "seed_schedule": schedule,
            "gates": {"denominator_per_stratum": FRAMES_PER_STRATUM, "successes_per_stratum": 510,
                      "forbidden_failure_count_limit": 0, "strata": list(STRATA)},
            "ranking": ["lowest exact total disclosure divided by denominator (rational)",
                        "highest minimum-stratum verified successes", "highest total verified successes",
                        "lowest exact total runtime", "candidate id"],
            "caps": {"complete_run_s": COMPLETE_RUN_CAP_S, "per_frame_wall_s": 10.0,
                     "per_frame_decoder_calls": 20, "per_frame_events": 32},
            "failure_policy": FAILURE_POLICY, "scoped_source_sha256": _hashes(),
            "environment": _environment(test_only)}
    return _self(base, "plan_sha256")


def _validate_plan(plan: Mapping[str, Any], *, test_only: bool, output_dir: Path) -> dict[str, Any]:
    if not isinstance(plan, Mapping):
        raise ValueError("plan type")
    supplied = dict(plan)
    digest = supplied.pop("plan_sha256", None)
    if not isinstance(digest, str) or _sha(_compact(supplied)) != digest:
        raise ValueError("plan self hash")
    expected_schema = TEST_PLAN_SCHEMA if test_only else PLAN_SCHEMA
    expected_run_id = TEST_RUN_ID if test_only else RUN_ID
    partition_bytes = (PARTITION_LOCK).read_bytes()
    if _sha(partition_bytes) != PARTITION_LOCK_FILE_SHA256:
        raise ValueError("partition file hash")
    lock = json.loads(partition_bytes)
    _static_lock_checks(lock)
    method = _method_objects()
    roots = [record["root_hex"] for record in plan["seed_schedule"]["roots"]]
    rebuilt = _plan(lock, partition_bytes, method, roots, test_only=test_only, output_dir=output_dir)
    if dict(plan) != rebuilt:
        raise ValueError("plan frozen equality")
    if not test_only and plan["environment"]["ldpc_version"] != "2.4.1":
        raise ValueError("backend requirement")
    return dict(plan)


def _test_dir_checks(output_dir: Path) -> None:
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError("fresh test output directory required")
    resolved = output_dir.resolve()
    if str(resolved) != os.path.abspath(str(output_dir)):
        raise ValueError("symlinked test output path rejected")
    workspace = (_REPO / "workspace").resolve()
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise ValueError("test output must be a workspace descendant") from exc
    if resolved == OFFICIAL_OUTPUT.resolve():
        raise ValueError("official output path rejected")


def prepare_plan(output_dir: Path, partition_lock_path: Path) -> dict[str, Any]:
    """Production prepare: exact official paths, fresh directory, plan only."""
    output_dir = Path(output_dir)
    if output_dir.resolve() != OFFICIAL_OUTPUT.resolve():
        raise ValueError("official output path required")
    partition_lock_path = Path(partition_lock_path)
    if partition_lock_path.resolve() != PARTITION_LOCK.resolve():
        raise ValueError("approved partition path required")
    if output_dir.exists():
        raise FileExistsError("fresh output directory required")
    partition_bytes = PARTITION_LOCK.read_bytes()
    if _sha(partition_bytes) != PARTITION_LOCK_FILE_SHA256:
        raise ValueError("partition file hash")
    lock = json.loads(partition_bytes)
    validate_partition_lock(lock)
    method = _method_objects()
    roots = [_new_root_hex() for _ in range(18)]
    plan = _plan(lock, partition_bytes, method, roots, test_only=False, output_dir=output_dir)
    if plan["environment"]["ldpc_version"] != "2.4.1":
        raise ValueError("backend requirement")
    output_dir.mkdir()
    _json(output_dir / ARTIFACTS[0], plan)
    _validate_plan(json.loads((output_dir / ARTIFACTS[0]).read_bytes()), test_only=False, output_dir=output_dir)
    return plan


def _prepare_test_package(output_dir: Path, *, deterministic_roots: list[str]) -> dict[str, Any]:
    """Private test prepare; the approved partition is read/copied, never rebuilt."""
    output_dir = Path(output_dir)
    _test_dir_checks(output_dir)
    if len(deterministic_roots) != 18 or any(not isinstance(r, str) or len(r) != 64 or r != r.lower() or any(c not in "0123456789abcdef" for c in r) for r in deterministic_roots):
        raise ValueError("deterministic roots")
    partition_bytes = PARTITION_LOCK.read_bytes()
    if _sha(partition_bytes) != PARTITION_LOCK_FILE_SHA256:
        raise ValueError("partition file hash")
    lock = json.loads(partition_bytes)
    _static_lock_checks(lock)
    method = _method_objects()
    plan = _plan(lock, partition_bytes, method, list(deterministic_roots), test_only=True, output_dir=output_dir)
    output_dir.mkdir()
    _json(output_dir / ARTIFACTS[0], plan)
    _validate_plan(json.loads((output_dir / ARTIFACTS[0]).read_bytes()), test_only=True, output_dir=output_dir)
    return plan


def _classify(status: str, reason: str) -> str | None:
    if status == "backend_unavailable":
        return "backend"
    if status == "aborted_resource_limit":
        return "resource"
    if status == "syndrome_inconsistent":
        return "syndrome"
    if status in {"invalid_input", "unsupported_domain"}:
        return "unclassified"
    if status == "decoder_error":
        return "backend" if "backend" in reason or "unavailable" in reason else "internal"
    return None


def _package_class(reason: str) -> str | None:
    if isinstance(reason, str) and reason.startswith("package_"):
        cls = reason[len("package_"):].split(":", 1)[0]
        return cls if cls in FORBIDDEN_CLASSES else None
    return None


def _normalize_reason(exc: BaseException) -> str:
    return f"{type(exc).__name__}:{str(exc)}".replace("\n", " ").strip()


def _array_hash(value: Any) -> str:
    data = np.asarray(value)
    if data.shape != (N,) or not np.issubdtype(data.dtype, np.integer):
        raise ValueError("frame array")
    return _sha(np.asarray(data, dtype="<u2").tobytes())


def _package_failure_outcome(attempt_id: str, cls: str, reason: str) -> dict[str, Any]:
    candidate, stratum, rank = attempt_id.split("|")
    return {"dataset_id": stratum, "frame_id": rank, "n_pairs": N,
            "pair_idx_sequence_sha256": _sha(_compact([])), "method": METHOD_ID, "candidate_id": candidate,
            "attempted": False, "denominator_included": False, "status": "invalid_input",
            "failure_reason": f"package_{cls}:{reason}", "dimension": Q, "frame_len_symbols": N,
            "raw_ser": 0.0, "fallback_invoked": False, "rounds_attempted": 1, "verification_invoked": False,
            "verification_seed_id_round0": "", "verification_seed_id_round1": "", "verification_tag_bits": 0,
            "epsilon_ec": 0.0, "key_dependent_disclosure_bits_total": 0, "public_control_bits_total": 0,
            "transcript_first_event_id": None, "transcript_last_event_id": None,
            "transcript_sha256": EMPTY_HASH, "runtime_s": 0.0, "decoder_call_count": 0,
            "verification_check_count": 0, "ldpc_syndrome_bits": 0, "h1_syndrome_bits": 0,
            "h2_syndrome_bits": 0, "verification_tag_bits_component": 0, "feedback_control_bits": 0,
            "selection_sha256": "", "channel_model_sha256": "", "h1_codebook_manifest_sha256": "",
            "h2_manifest_sha256": "", "policy_sha256": "", "mapping": MAPPING,
            "leakage_comparison_policy": "method_specific_not_cross_ranked",
            "backend_name": "", "backend_version": ""}


def _csv_row(attempt_id: str, outcome: Mapping[str, Any], alice_sha: str, bob_sha: str, transcript: bytes) -> dict[str, Any]:
    candidate, stratum, rank = attempt_id.split("|")
    # prefix role is the locked development-row role; the package role
    # ("sacrificed_development") lives in the plan, not in the CSV prefix
    return {"role": "development", "stratum": stratum, "plan_frame_id": f"{stratum}-{rank}",
            "alice_sha256": alice_sha, "bob_sha256": bob_sha,
            "transcript_bytes_len": len(transcript), "transcript_bytes_sha256": _sha(transcript),
            **dict(outcome)}


def _stratum_summary(rows: list[Mapping[str, Any]], candidate: str, stratum: str) -> dict[str, Any]:
    part = [r for r in rows if r["candidate_id"] == candidate and r["stratum"] == stratum]
    status_counts: dict[str, int] = {}
    for row in part:
        status_counts[str(row["status"])] = status_counts.get(str(row["status"]), 0) + 1
    forbidden = sum(_package_class(str(r["failure_reason"])) is not None or _classify(str(r["status"]), str(r["failure_reason"])) is not None for r in part)
    return {"stratum": stratum, "denominator": sum(bool(r["denominator_included"]) for r in part),
            "verified_success": sum(r["status"] == "verified_success" for r in part),
            "status_counts": status_counts,
            "forbidden_failure_count": int(forbidden),
            "key_dependent_disclosure_bits_total": sum(int(r["key_dependent_disclosure_bits_total"]) for r in part),
            "runtime_s_total": sum(float(r["runtime_s"]) for r in part)}


def _candidate_summaries(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for candidate in CANDIDATES:
        strata = [_stratum_summary(rows, candidate, stratum) for stratum in STRATA]
        denominator_total = sum(x["denominator"] for x in strata)
        selectable = all(x["denominator"] == FRAMES_PER_STRATUM and x["verified_success"] >= 510 and x["forbidden_failure_count"] == 0 for x in strata)
        summaries.append({"candidate_id": candidate, "strata": strata,
                          "denominator_total": denominator_total,
                          "verified_success_total": sum(x["verified_success"] for x in strata),
                          "forbidden_failure_count_total": sum(x["forbidden_failure_count"] for x in strata),
                          "key_dependent_disclosure_bits_total": sum(x["key_dependent_disclosure_bits_total"] for x in strata),
                          "mean_disclosure_numerator": sum(x["key_dependent_disclosure_bits_total"] for x in strata),
                          "mean_disclosure_denominator": 1536 if denominator_total == 1536 else denominator_total,
                          "runtime_s_total": sum(x["runtime_s_total"] for x in strata),
                          "minimum_stratum_verified_success": min(x["verified_success"] for x in strata),
                          "selectable": bool(selectable)})
    return summaries


def _rank_key(summary: Mapping[str, Any]) -> list[Any]:
    return [int(summary["mean_disclosure_numerator"]), int(summary["mean_disclosure_denominator"]),
            -int(summary["minimum_stratum_verified_success"]), -int(summary["verified_success_total"]),
            float(summary["runtime_s_total"]), str(summary["candidate_id"])]


def _rank_compare(a: list[Any], b: list[Any]) -> int:
    cross = a[0] * b[1] - b[0] * a[1]
    if cross:
        return -1 if cross < 0 else 1
    for x, y in zip(a[2:], b[2:]):
        if x < y:
            return -1
        if x > y:
            return 1
    return 0


def _expected_outcomes(plan: Mapping[str, Any]) -> int:
    return len(plan["execution"]["attempt_ids"])


def _selection(plan: Mapping[str, Any], rows: list[Mapping[str, Any]],
               outcomes_file_sha256: str, transcript_file_sha256: str) -> dict[str, Any]:
    summaries = _candidate_summaries(rows)
    eligible = [summary["candidate_id"] for summary in summaries if summary["selectable"]]
    ranked = sorted([{"candidate_id": summary["candidate_id"], "rank_key": _rank_key(summary)}
                     for summary in summaries if summary["selectable"]],
                    key=cmp_to_key(lambda a, b: _rank_compare(a["rank_key"], b["rank_key"])))
    selected = ranked[0]["candidate_id"] if ranked else None
    selection_status = "selected" if selected else ("non_promoted_development" if len(rows) == _expected_outcomes(plan) and not any(_package_class(str(r["failure_reason"])) for r in rows) else "invalid_execution")
    policy_sha = None
    if selected is not None:
        policy = next(x for x in _method_objects()["policy"]["candidates"] if x["candidate_id"] == selected)
        policy_sha = policy["policy_sha256"]
    base = {"schema": TEST_SELECTION_SCHEMA if plan["schema"] == TEST_PLAN_SCHEMA else SELECTION_SCHEMA,
            "run_id": plan["run_id"], "method_id": METHOD_ID, "plan_sha256": plan["plan_sha256"],
            "partition_sha256": plan["partition_binding"]["partition_sha256"],
            "policy_manifest_sha256": plan["method_bindings"]["policy_manifest_sha256"],
            "outcomes_file_sha256": outcomes_file_sha256, "transcript_file_sha256": transcript_file_sha256,
            "selection_status": selection_status, "candidate_summaries": summaries,
            "eligible_candidate_ids": eligible, "ranking_rule": list(plan["ranking"]),
            "ranked_candidates": ranked, "selected_candidate_id": selected,
            "selected_policy_sha256": policy_sha,
            "ready_for_synthetic_prepare": selected is not None}
    return _self(base, "selection_sha256")


def _invalid_selection(plan: Mapping[str, Any], rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    summaries = _candidate_summaries(rows)
    base = {"schema": TEST_SELECTION_SCHEMA if plan["schema"] == TEST_PLAN_SCHEMA else SELECTION_SCHEMA,
            "run_id": plan["run_id"], "method_id": METHOD_ID, "plan_sha256": plan["plan_sha256"],
            "partition_sha256": plan["partition_binding"]["partition_sha256"],
            "policy_manifest_sha256": plan["method_bindings"]["policy_manifest_sha256"],
            "outcomes_file_sha256": "", "transcript_file_sha256": "",
            "selection_status": "invalid_execution", "candidate_summaries": summaries,
            "eligible_candidate_ids": [], "ranking_rule": list(plan["ranking"]),
            "ranked_candidates": [], "selected_candidate_id": None,
            "selected_policy_sha256": None, "ready_for_synthetic_prepare": False}
    return _self(base, "selection_sha256")


def _package_failure_counts(rows: list[Mapping[str, Any]]) -> dict[str, int]:
    counts = {cls: 0 for cls in FORBIDDEN_CLASSES}
    for row in rows:
        cls = _package_class(str(row["failure_reason"]))
        if cls is None:
            cls = _classify(str(row["status"]), str(row["failure_reason"]))
        if cls is not None:
            counts[cls] += 1
    return counts


def _run_manifest(plan: Mapping[str, Any], plan_file_sha256: str, rows: list[Mapping[str, Any]],
                  run_status: str, failure: Mapping[str, Any] | None, wall_runtime_s: float,
                  artifact_file_sha256: Mapping[str, Any]) -> dict[str, Any]:
    base = {"schema": TEST_RUN_MANIFEST_SCHEMA if plan["schema"] == TEST_PLAN_SCHEMA else RUN_MANIFEST_SCHEMA,
            "run_id": plan["run_id"], "method_id": METHOD_ID, "run_status": run_status,
            "plan_sha256": plan["plan_sha256"], "plan_file_sha256": plan_file_sha256,
            "execution_order_sha256": plan["execution"]["attempt_ids_sha256"],
            "seed_schedule_sha256": plan["seed_schedule"]["seed_schedule_sha256"],
            "expected_outcomes": _expected_outcomes(plan), "observed_outcomes": len(rows),
            "artifact_file_sha256": artifact_file_sha256, "failure": failure,
            "wall_runtime_s": float(wall_runtime_s)}
    return _self(base, "run_manifest_sha256")


def _report(plan: Mapping[str, Any], rows: list[Mapping[str, Any]], selection: Mapping[str, Any],
            run_manifest: Mapping[str, Any], run_status: str) -> dict[str, Any]:
    summaries = selection["candidate_summaries"]
    selectable = {summary["candidate_id"]: bool(summary["selectable"]) for summary in summaries}
    if run_status == "invalid_execution":
        next_action = "stop_invalid_execution_retain_partial_no_resume"
    elif selection["selected_candidate_id"] is not None:
        next_action = "freeze_phase3_synthetic_plan"
    else:
        next_action = "stop_no_synthetic_output_no_tuning_no_rerun"
    if plan["schema"] == TEST_PLAN_SCHEMA:
        next_action = "test_only_none"
    base = {"schema": TEST_REPORT_SCHEMA if plan["schema"] == TEST_PLAN_SCHEMA else REPORT_SCHEMA,
            "run_id": plan["run_id"], "method_id": METHOD_ID, "run_status": run_status,
            "scientific_scope": "test_only_not_qualification_evidence" if plan["schema"] == TEST_PLAN_SCHEMA else "sacrificed_10db_development_not_confirmation",
            "plan_sha256": plan["plan_sha256"],
            "run_manifest_sha256": run_manifest["run_manifest_sha256"],
            "run_manifest_file_sha256": _sha(_compact(run_manifest)),
            "selection_sha256": selection["selection_sha256"],
            "selection_file_sha256": _sha(_compact(selection)),
            "outcomes_file_sha256": selection["outcomes_file_sha256"],
            "transcript_file_sha256": selection["transcript_file_sha256"],
            "expected_outcomes": _expected_outcomes(plan), "observed_outcomes": len(rows),
            "candidate_summaries": summaries,
            "gate": {"denominator_per_stratum": plan["gates"]["denominator_per_stratum"],
                     "successes_per_stratum": plan["gates"]["successes_per_stratum"],
                     "forbidden_failure_count_limit": plan["gates"]["forbidden_failure_count_limit"],
                     "candidates": selectable},
            "package_failure_counts": _package_failure_counts(rows),
            "selected_candidate_id": selection["selected_candidate_id"],
            "ready_for_synthetic_prepare": bool(selection["ready_for_synthetic_prepare"]),
            "next_action": next_action}
    return _self(base, "report_sha256")


class _PackageFailure(Exception):
    def __init__(self, cls: str) -> None:
        super().__init__(cls)
        self.cls = cls


def _exception_class(exc: BaseException) -> str:
    if isinstance(exc, (TimeoutError, MemoryError)):
        return "resource"
    if "syndrome" in str(exc).lower():
        return "syndrome"
    return "internal"


def _finalize(out: Path, plan: Mapping[str, Any], rows: list[Mapping[str, Any]], transcripts: bytes,
              *, partition_bytes: bytes, method: Mapping[str, Any], run_status: str,
              failure: Mapping[str, Any] | None, wall_runtime_s: float) -> dict[str, Any]:
    """Write artifacts 2..12; every write is no-overwrite. Never called twice."""
    _write(out / ARTIFACTS[1], partition_bytes)
    _write(out / ARTIFACTS[2], method["codebook_bytes"])
    _write(out / ARTIFACTS[3], method["selection_bytes"])
    _write(out / ARTIFACTS[4], method["channel_bytes"])
    _json(out / ARTIFACTS[5], method["h2"])
    _json(out / ARTIFACTS[6], method["policy"])
    _write(out / ARTIFACTS[7], encode_outcome_csv_v5(rows))
    _write(out / ARTIFACTS[8], transcripts)
    csv_file_sha = _sha((out / ARTIFACTS[7]).read_bytes())
    transcript_file_sha = _sha((out / ARTIFACTS[8]).read_bytes())
    if run_status == "invalid_execution":
        selection = _invalid_selection(plan, rows)
    else:
        selection = _selection(plan, rows, csv_file_sha, transcript_file_sha)
    _json(out / ARTIFACTS[9], selection)
    plan_file_sha = _sha((out / ARTIFACTS[0]).read_bytes())
    artifact_map = {name: {"sha256": _sha((out / name).read_bytes()), "bytes": (out / name).stat().st_size}
                    for name in ARTIFACTS[1:10]}
    manifest = _run_manifest(plan, plan_file_sha, rows, run_status, failure, wall_runtime_s, artifact_map)
    _json(out / ARTIFACTS[10], manifest)
    report = _report(plan, rows, selection, manifest, run_status)
    _json(out / ARTIFACTS[11], report)
    return {"run_status": run_status, "observed_outcomes": len(rows), "selection": selection,
            "run_manifest": manifest, "report": report}


def _execute(out: Path, *, method_runner: Callable[..., Any], array_loader: Callable[..., Any],
             clock: Callable[[], float], test_only: bool) -> dict[str, Any]:
    if not out.is_dir() or {x.name for x in out.iterdir()} != {ARTIFACTS[0]}:
        raise ValueError("execute requires only reviewed plan")
    plan = _validate_plan(json.loads((out / ARTIFACTS[0]).read_bytes()), test_only=test_only, output_dir=out)
    partition_bytes = PARTITION_LOCK.read_bytes()
    if _sha(partition_bytes) != PARTITION_LOCK_FILE_SHA256:
        raise ValueError("partition file hash")
    lock = json.loads(partition_bytes)
    if test_only:
        rows_by = {(row["stratum"][6:], int(row["role_rank"])): row for row in _static_development_rows(lock)}
    else:
        validate_partition_lock(lock)
        rows_by = {(row["stratum"][6:], int(row["role_rank"])): row for row in development_rows(lock)}
    method = _method_objects()
    if plan["method_bindings"] != method["bindings"]:
        raise ValueError("plan method binding drift")
    schedule_roots = {(record["candidate_id"], record["stratum"], record["verification_round"]): record["root_hex"]
                      for record in plan["seed_schedule"]["roots"]}
    policies = {candidate["candidate_id"]: candidate for candidate in method["policy"]["candidates"]}

    def locked_seeds_for(candidate: str, stratum: str, rank: int) -> list[dict[str, Any]]:
        return [derive_seed(schedule_roots[(candidate, stratum, 0)], candidate, stratum, 0, rank),
                derive_seed(schedule_roots[(candidate, stratum, 1)], candidate, stratum, 1, rank)]

    rows: list[dict[str, Any]] = []
    transcripts = bytearray()
    started = clock()
    current: str | None = None
    appended_current = False
    try:
        for attempt_id in plan["execution"]["attempt_ids"]:
            if clock() - started > float(plan["caps"]["complete_run_s"]):
                raise TimeoutError("complete_run_cap")
            candidate, stratum, rank_str = attempt_id.split("|")
            rank = int(rank_str)
            current = attempt_id
            appended_current = False
            try:
                alice, bob = array_loader(lock, rows_by[(stratum, rank)])
            except Exception as exc:
                rows.append(_csv_row(attempt_id, _package_failure_outcome(attempt_id, "source", _normalize_reason(exc)),
                                     EMPTY_HASH, EMPTY_HASH, b""))
                appended_current = True
                raise _PackageFailure("source") from exc
            try:
                result = method_runner(alice, bob, pair_idx_sequence=np.arange(N, dtype=np.int64),
                                       dataset_id=stratum, frame_id=str(rank), stratum=stratum,
                                       candidate_policy=policies[candidate], policy_manifest=method["policy"],
                                       selection_manifest=method["selection"], channel_model=method["channel"],
                                       h2_manifest=method["h2"], locked_seeds=locked_seeds_for(candidate, stratum, rank))
                outcome = dict(result["outcome"])
                events = list(result["events"])
                validate_outcome_v5(outcome, events)
                # Formal nonattempted outcomes carry an empty pair hash, so the
                # frozen public verifier (which hashes the real indices) applies
                # only to attempted outcomes (contract §3, §7).  Nonattempted
                # outcomes with non-finite raw_ser cannot enter canonical CSV
                # and are replaced by package failures before any verification.
                if not bool(outcome["attempted"]) and not np.isfinite(float(outcome["raw_ser"])):
                    cls = _classify(str(outcome["status"]), str(outcome["failure_reason"])) or "unclassified"
                    outcome = _package_failure_outcome(attempt_id, cls, str(outcome["failure_reason"]) or str(outcome["status"]))
                    events = []
                    transcript = b""
                elif bool(outcome["attempted"]):
                    verify_public_payload_v5(outcome, events, alice_symbols=alice,
                                             pair_idx_sequence=np.arange(N, dtype=np.int64), stratum=stratum,
                                             candidate_policy=policies[candidate], policy_manifest=method["policy"],
                                             selection_manifest=method["selection"], channel_model=method["channel"],
                                             h2_manifest=method["h2"], locked_seeds=locked_seeds_for(candidate, stratum, rank))
                    transcript = b"".join(canonical_event_v5(event) for event in events)
                else:
                    transcript = b""
                row = _csv_row(attempt_id, outcome, _array_hash(alice), _array_hash(bob), transcript)
            except _PackageFailure:
                raise
            except Exception as exc:
                rows.append(_csv_row(attempt_id, _package_failure_outcome(attempt_id, _exception_class(exc), _normalize_reason(exc)),
                                     _array_hash(alice) if 'alice' in dir() else EMPTY_HASH,
                                     _array_hash(bob) if 'bob' in dir() else EMPTY_HASH, b""))
                appended_current = True
                raise
            rows.append(row)
            transcripts.extend(transcript)
            appended_current = True
        if len(rows) != _expected_outcomes(plan):
            raise RuntimeError("outcome accounting")
        run_status = "completed" if _selection(plan, rows, "", "").get("selection_status") == "selected" else "non_promoted_development"
        return _finalize(out, plan, rows, bytes(transcripts), partition_bytes=partition_bytes, method=method,
                         run_status=run_status, failure=None, wall_runtime_s=clock() - started)
    except Exception as exc:
        if current is not None and not appended_current:
            cls = exc.cls if isinstance(exc, _PackageFailure) else _exception_class(exc)
            rows.append(_csv_row(current, _package_failure_outcome(current, cls, _normalize_reason(exc)),
                                 EMPTY_HASH, EMPTY_HASH, b""))
        failure = {"class": exc.cls if isinstance(exc, _PackageFailure) else _exception_class(exc),
                   "reason": _normalize_reason(exc), "attempt_id": current}
        _finalize(out, plan, rows, bytes(transcripts), partition_bytes=partition_bytes, method=method,
                  run_status="invalid_execution", failure=failure, wall_runtime_s=clock() - started)
        if not test_only:
            raise
        return {"run_status": "invalid_execution", "observed_outcomes": len(rows), "failure": failure}


def execute_plan(output_dir: Path) -> dict[str, Any]:
    return _execute(Path(output_dir), method_runner=run_ldpc_formal_v5,
                    array_loader=development_arrays_for_frame, clock=time.monotonic, test_only=False)


def _execute_test_package(output_dir: Path, *, method_runner: Callable[..., Any],
                          array_loader: Callable[..., Any], clock: Callable[[], float]) -> dict[str, Any]:
    """Private test execute; missing explicit fakes fail before package creation."""
    if method_runner is None or array_loader is None or clock is None:
        raise TypeError("test execution requires explicit fake dependencies")
    return _execute(Path(output_dir), method_runner=method_runner, array_loader=array_loader,
                    clock=clock, test_only=True)
