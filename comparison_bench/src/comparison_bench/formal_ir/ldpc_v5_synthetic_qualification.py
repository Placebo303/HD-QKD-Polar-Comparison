"""Immutable v1 fresh synthetic qualification package for binary LDPC v5.

Implements the frozen Phase 3 contract (prepare once, main review, execute
once, read-only verify once; no-overwrite, non-resumable, immutable failure
retention; 126/128 per stratum with zero forbidden failures before Phase 4).
Production entry points expose no test switch; private test helpers require
explicit fakes and a test-owned workspace root.

The package uses the verified Phase 2 development package as its frozen
prerequisite: it binds the exact V5-C2 policy/h2/channel/codebook contents and
re-uses the development seed derivation domain only for frame generation with
new domain-separated roots. Synthetic frames are generated from the frozen v4
channel model (adjacent +/-1 errors); the CSV uses role="confirmation" and
data-stratum placeholder "bw120" because the frozen v5 CSV/run schema requires
a bw value while v5_plane_error_channel treats every bw value identically.
"""
from __future__ import annotations
import functools, hashlib, importlib.metadata, json, logging, os, platform, secrets, time
from pathlib import Path
from typing import Any, Callable, Mapping
import numpy as np

logger = logging.getLogger("comparison_bench.ldpc_v5_synthetic_qualification")
from . import ldpc_v5_development as dev
from .codebook_v5_h2 import verify_h2_manifest
from .ldpc_v5 import (METHOD, run_ldpc_formal_v5, build_v5_policy_manifest,
                      verify_v5_policy_manifest, _selected_candidates,
                      validate_outcome_v5, verify_public_payload_v5,
                      encode_outcome_csv_v5, canonical_event_v5, OUTCOME_FIELDS)
from .ldpc_v5_partition import validate_partition_lock
from .shared import seed_record

RUN_ID = "binary_ldpc_v5_synthetic_qualification_v1"
TEST_RUN_ID = "binary_ldpc_v5_synthetic_qualification_test_v1"
ROLE = "synthetic_confirmation"
N = 256
Q = 1024
MAPPING = "gray"
CANDIDATE = "V5-C2"
CHANNEL_STRATA = ("adjacent_nominal", "adjacent_stress_125")
FRAMES_PER_STRATUM = 128
DATA_STRATUM = "bw120"
SEED_BIT_LENGTH = 2623
PLAN_SCHEMA = "binary_ldpc_v5_synthetic_plan_v1"
TEST_PLAN_SCHEMA = "binary_ldpc_v5_synthetic_plan_test_v1"
RUN_MANIFEST_SCHEMA = "binary_ldpc_v5_synthetic_run_manifest_v1"
TEST_RUN_MANIFEST_SCHEMA = "binary_ldpc_v5_synthetic_run_manifest_test_v1"
REPORT_SCHEMA = "binary_ldpc_v5_synthetic_report_v1"
TEST_REPORT_SCHEMA = "binary_ldpc_v5_synthetic_report_test_v1"
SEED_SCHEDULE_SCHEMA = "binary_ldpc_v5_synthetic_seed_schedule_v1"
GENERATOR_SCHEMA = "binary_ldpc_v5_synthetic_rng_v1"
FAILURE_POLICY = "immutable_partial_finalization_no_resume_no_rerun_no_tuning"
COMPLETE_RUN_CAP_S = 1800.0
GATE_SUCCESSES = 126

ARTIFACTS = ("pre_run_plan.json", "formal_codebook_manifest.json",
             "formal_selection_manifest.json", "formal_channel_model.json",
             "v5_h2_manifest.json", "v5_policy_manifest.json",
             "synthetic_frame_outcomes.csv", "synthetic_transcript.jsonl",
             "synthetic_run_manifest.json", "synthetic_qualification_report.json")

FORBIDDEN_CLASSES = ("backend", "source", "internal", "accounting", "resource",
                     "syndrome", "unclassified", "provenance")
FORBIDDEN_STATUSES = {"invalid_input", "unsupported_domain", "backend_unavailable",
                      "aborted_resource_limit", "syndrome_inconsistent", "decoder_error"}

_REPO = Path(__file__).resolve().parents[4]
_ROOT = _REPO / "comparison_bench" / "outputs_comparison" / "formal_ir_methods"
OFFICIAL_OUTPUT = _ROOT / "20260801_v1_binary_ldpc_v5_synthetic"
DEVELOPMENT_PKG = _ROOT / "20260731_v1_binary_ldpc_v5_development"

_SCOPED = ("cli/run_ldpc_v5_synthetic_qualification.py",
           "cli/verify_ldpc_v5_synthetic_qualification.py",
           "formal_ir/ldpc_v5_synthetic_qualification.py",
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

def _quick_verify(dir_path: Path) -> None:
    """Fast test-mode prerequisite check: static plan/artifact consistency.

    The full read-only verifier rebuilds the partition lock and source lock
    (minutes); test packages bind the already-verified official development
    package, so this path validates the plan DAG, manifest/artifact index, and
    readiness fields without the slow rebuilds.
    """
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
    """Validate the Phase 2 package and return its bound method bundle.

    Production (private=False) runs the full strict read-only verifier; test
    mode (private=True) runs the fast static prerequisite check against the
    official development package (test packages cannot fabricate a
    verified-ready development package because the v5 execute path verifies
    every attempted frame's public payload).
    """
    if private:
        _quick_verify(dir_path)
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
    """Derive the Phase 2 package's 9,216 locked seed IDs from its plan roots.

    The development schedule records per candidate/stratum/round roots; seed
    IDs derive through the frozen development derivation domain (18 roots x
    512 ranks). Overlap with any of them is forbidden for synthetic seeds.
    """
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


# --- roots and seeds --------------------------------------------------------

def derive_seed(root_hex: str, stratum: str, round_: int, rank: int) -> dict[str, Any]:
    label = f"{RUN_ID}|{stratum}|round={round_}|rank={rank}".encode("ascii")
    raw = hashlib.shake_256(bytes.fromhex(root_hex) + b"\0" + label).digest(328)
    bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8), bitorder="big")[:SEED_BIT_LENGTH]
    return seed_record(bits)


def _generator_root_derive(root_hex: str, stratum: str, kind: str) -> np.random.Generator:
    digest = _sha(_compact({"schema": GENERATOR_SCHEMA, "run_id": RUN_ID,
                            "root_hex": root_hex, "stratum": stratum, "kind": kind}))
    return np.random.Generator(np.random.PCG64(int.from_bytes(bytes.fromhex(digest[:32]), "big")))


def _new_roots() -> dict[str, dict[str, dict[str, str]]]:
    out: dict[str, dict[str, dict[str, str]]] = {}
    for s in CHANNEL_STRATA:
        out[s] = {}
        for kind in ("bob", "delta"):
            raw = _new_root_hex()
            out[s][kind] = {"root_hex": raw, "root_id": _root_id(raw)}
        for r in (0, 1):
            raw = _new_root_hex()
            out[s][f"toeplitz_r{r}"] = {"root_hex": raw, "root_id": _root_id(raw),
                                        "verification_round": r}
    return out


def _generate(plan: Mapping[str, Any], stratum: str) -> tuple[np.ndarray, np.ndarray]:
    if stratum not in CHANNEL_STRATA:
        raise ValueError("channel stratum")
    roots = plan["generator"]["roots"][stratum]
    model = plan["development_binding"]["channel_model"]
    n = int(plan["domain"]["frame_count_per_stratum"])
    bob = _generator_root_derive(roots["bob"]["root_hex"], stratum, "bob").integers(
        0, Q, size=(n, N), dtype=np.uint16)
    u = _generator_root_derive(roots["delta"]["root_hex"], stratum, "delta").random((n, N))
    probs = model["probabilities"][stratum]
    p_minus, p_plus = float(probs["minus_one"]), float(probs["plus_one"])
    delta = np.where(u < p_minus, -1,
                     np.where(u < p_minus + p_plus, 1, 0)).astype(np.int16)
    alice = ((bob.astype(np.int16) + delta) % Q).astype(np.uint16)
    return alice, bob


def _attempt_ids() -> list[str]:
    return [f"{s}|f{i:03d}" for s in CHANNEL_STRATA for i in range(FRAMES_PER_STRATUM)]


def _seed_schedule(roots: Mapping[str, Mapping[str, dict[str, Any]]], *, private: bool,
                   development_dir: Path | None = None) -> dict[str, Any]:
    run_id = TEST_RUN_ID if private else RUN_ID
    records = []
    all_ids: list[str] = []
    for s in CHANNEL_STRATA:
        for r in (0, 1):
            root = roots[s][f"toeplitz_r{r}"]
            ids = sorted(derive_seed(root["root_hex"], s, r, i)["seed_id"] for i in range(FRAMES_PER_STRATUM))
            records.append({"stratum": s, "verification_round": r, "root_hex": root["root_hex"],
                            "seed_count": FRAMES_PER_STRATUM, "seed_ids_sha256": _sha(_compact(ids))})
            all_ids.extend(ids)
    if len(set(all_ids)) != 4 * FRAMES_PER_STRATUM:
        raise ValueError("seed schedule uniqueness")
    prior_roots, prior_seeds = dev._extract_prior()
    dev_digest = _development_root_digest(Path(development_dir) if development_dir is not None else DEVELOPMENT_PKG)
    dev_seeds = _development_seed_digest(Path(development_dir) if development_dir is not None else DEVELOPMENT_PKG)
    if set(all_ids) & set(dev_seeds["seed_ids"]):
        raise ValueError("development seed id collision")
    base = {"schema": SEED_SCHEDULE_SCHEMA,
            "derivation": f"shake_256(root + b'\\x00' + '{run_id}|{{stratum}}|round={{round}}|rank={{rank}}').digest(328); unpackbits[:2623]; seed_record",
            "roots": records, "seed_count": 4 * FRAMES_PER_STRATUM,
            "seed_ids_sha256": _sha(_compact(sorted(set(all_ids)))),
            "prior_root_count": len(prior_roots), "prior_roots_sha256": _sha(_compact(prior_roots)),
            "prior_seed_id_count": len(prior_seeds), "prior_seed_ids_sha256": _sha(_compact(prior_seeds)),
            "development_root_count": dev_digest["count"],
            "development_roots_sha256": dev_digest["roots_sha256"],
            "development_seed_id_count": dev_seeds["count"],
            "development_seed_ids_sha256": dev_seeds["seed_ids_sha256"], "isolated": True}
    return _self(base, "seed_schedule_sha256")


def _validate_roots(plan: Mapping[str, Any]) -> set[int]:
    roots = plan["generator"]
    if set(roots) != {"schema", "algorithm", "roots", "delta_order"} or \
       roots["schema"] != GENERATOR_SCHEMA or roots["algorithm"] != "PCG64" or \
       roots["delta_order"] != "minus_one,plus_one,zero" or set(roots["roots"]) != set(CHANNEL_STRATA):
        raise ValueError("generator contract")
    root_ints: set[int] = set()
    for s in CHANNEL_STRATA:
        kinds = roots["roots"][s]
        if set(kinds) != {"bob", "delta", "toeplitz_r0", "toeplitz_r1"}:
            raise ValueError("generator kinds")
        for record in kinds.values():
            raw = record.get("root_hex") if isinstance(record, dict) else None
            if not isinstance(raw, str) or len(raw) != 64 or raw.lower() != raw or \
               any(c not in "0123456789abcdef" for c in raw) or record.get("root_id") != _root_id(raw):
                raise ValueError("root record")
            root_ints.add(int(raw, 16))
    if len(root_ints) != 8:
        raise ValueError("root uniqueness")
    prior_roots, prior_seeds = dev._extract_prior()
    if root_ints & {int(x, 16) for x in prior_roots}:
        raise ValueError("predecessor root collision")
    schedule = plan["seed_schedule"]
    if schedule.get("prior_root_count") != len(prior_roots) or \
       schedule.get("prior_roots_sha256") != _sha(_compact(prior_roots)) or \
       schedule.get("prior_seed_id_count") != len(prior_seeds) or \
       schedule.get("prior_seed_ids_sha256") != _sha(_compact(prior_seeds)):
        raise ValueError("prior digest drift")
    dev_digest = _development_root_digest(Path(plan["development_binding"]["path"]))
    if schedule.get("development_root_count") != dev_digest["count"] or \
       schedule.get("development_roots_sha256") != dev_digest["roots_sha256"]:
        raise ValueError("development digest drift")
    if root_ints & {int(x, 16) for x in dev_digest["roots"]}:
        raise ValueError("development root collision")
    dev_seeds = _development_seed_digest(Path(plan["development_binding"]["path"]))
    if schedule.get("development_seed_id_count") != dev_seeds["count"] or \
       schedule.get("development_seed_ids_sha256") != dev_seeds["seed_ids_sha256"]:
        raise ValueError("development seed digest drift")
    my_ids = set()
    for s in CHANNEL_STRATA:
        for r in (0, 1):
            for i in range(FRAMES_PER_STRATUM):
                my_ids.add(derive_seed(plan["generator"]["roots"][s][f"toeplitz_r{r}"]["root_hex"], s, r, i)["seed_id"])
    if len(my_ids) != 4 * FRAMES_PER_STRATUM:
        raise ValueError("seed schedule uniqueness")
    if my_ids & set(dev_seeds["seed_ids"]):
        raise ValueError("development seed id collision")
    return root_ints


# --- plan -------------------------------------------------------------------

def _plan(dev: Mapping[str, Any], roots: Mapping[str, Mapping[str, dict[str, Any]]],
          *, test_only: bool, output_dir: Path) -> dict[str, Any]:
    schedule = _seed_schedule(roots, private=test_only, development_dir=Path(dev["path"]))
    attempt_ids = _attempt_ids()
    binding = dev["docs"]
    base = {"schema": TEST_PLAN_SCHEMA if test_only else PLAN_SCHEMA,
            "run_id": TEST_RUN_ID if test_only else RUN_ID, "method_id": METHOD, "role": ROLE,
            "domain": {"dimension": Q, "frame_len_symbols": N, "mapping": MAPPING,
                       "candidate": CANDIDATE, "strata": list(CHANNEL_STRATA),
                       "frame_count_per_stratum": FRAMES_PER_STRATUM, "data_stratum": DATA_STRATUM},
            "execution": {"order": "stratum_rank", "attempt_ids": attempt_ids,
                          "attempt_ids_sha256": _sha(_compact(attempt_ids))},
            "output_binding": {"output_directory": output_dir.resolve().relative_to(_REPO).as_posix(),
                               "artifact_names": list(ARTIFACTS), "prepare_file_set": [ARTIFACTS[0]]},
            "development_binding": {"path": dev["path"], "artifact_hashes": dev["hashes"],
                                    "selected_candidate_id": CANDIDATE,
                                    "ready_for_synthetic_prepare": True,
                                    "development_run_status": "completed",
                                    "codebook_manifest_sha256": dev["hashes"]["formal_codebook_manifest.json"],
                                    "selection_manifest_sha256": dev["hashes"]["formal_selection_manifest.json"],
                                    "channel_model_sha256": dev["hashes"]["formal_channel_model.json"],
                                    "h2_manifest_sha256": dev["hashes"]["v5_h2_manifest.json"],
                                    "policy_manifest_sha256": dev["hashes"]["v5_policy_manifest.json"],
                                    "codebook": binding["formal_codebook_manifest.json"],
                                    "selection": binding["formal_selection_manifest.json"],
                                    "channel_model": binding["formal_channel_model.json"],
                                    "h2_manifest": binding["v5_h2_manifest.json"],
                                    "policy_manifest": binding["v5_policy_manifest.json"]},
            "generator": {"schema": GENERATOR_SCHEMA, "algorithm": "PCG64",
                          "roots": roots, "delta_order": "minus_one,plus_one,zero"},
            "seed_schedule": schedule,
            "gates": {"denominator_per_stratum": FRAMES_PER_STRATUM,
                      "successes_per_stratum": GATE_SUCCESSES,
                      "forbidden_failure_count_limit": 0, "strata": list(CHANNEL_STRATA)},
            "caps": {"complete_run_s": COMPLETE_RUN_CAP_S, "per_frame_wall_s": 10.0,
                     "per_frame_decoder_calls": 20, "per_frame_events": 32},
            "failure_policy": FAILURE_POLICY, "scoped_source_sha256": _hashes(),
            "environment": _environment(test_only)}
    provisional = _self(base, "plan_sha256")
    _validate_plan(provisional, test_only=test_only, output_dir=output_dir)
    return provisional


def prepare_plan(output_dir: Path, development_dir: Path) -> dict[str, Any]:
    """Production prepare: exact official paths, fresh directory, plan only."""
    output_dir = Path(output_dir)
    development_dir = Path(development_dir)
    if output_dir.resolve() != OFFICIAL_OUTPUT.resolve():
        raise ValueError("official output path required")
    if development_dir.resolve() != DEVELOPMENT_PKG.resolve():
        raise ValueError("development prerequisite path required")
    if output_dir.exists():
        raise FileExistsError("fresh output directory required")
    dev_bundle = load_development(development_dir, private=False)
    roots = _new_roots()
    plan = _plan(dev_bundle, roots, test_only=False, output_dir=output_dir)
    output_dir.mkdir(parents=True)
    _json(output_dir / ARTIFACTS[0], plan)
    return plan


def _prepare_test_plan(output_dir: Path, development_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError("fresh output directory required")
    dev_bundle = load_development(development_dir, private=True)
    roots = _new_roots()
    plan = _plan(dev_bundle, roots, test_only=True, output_dir=output_dir)
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
                  "strata": list(CHANNEL_STRATA), "frame_count_per_stratum": FRAMES_PER_STRATUM,
                  "data_stratum": DATA_STRATUM}:
        raise ValueError("plan domain")
    if plan.get("execution") != {"order": "stratum_rank", "attempt_ids": _attempt_ids(),
                                 "attempt_ids_sha256": _sha(_compact(_attempt_ids()))}:
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
    expected_gates = {"denominator_per_stratum": FRAMES_PER_STRATUM, "successes_per_stratum": GATE_SUCCESSES,
                      "forbidden_failure_count_limit": 0, "strata": list(CHANNEL_STRATA)}
    if plan.get("gates") != expected_gates:
        raise ValueError("plan gates")
    if plan.get("caps") != {"complete_run_s": COMPLETE_RUN_CAP_S, "per_frame_wall_s": 10.0,
                            "per_frame_decoder_calls": 20, "per_frame_events": 32}:
        raise ValueError("plan caps")
    if plan.get("failure_policy") != FAILURE_POLICY:
        raise ValueError("plan failure policy")
    if plan.get("seed_schedule") != _seed_schedule(plan["generator"]["roots"], private=test_only,
                                                   development_dir=Path(plan["development_binding"]["path"])):
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
    gates = {s: _gate(rows, s, denominator, floor) for s in CHANNEL_STRATA}
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
    stratum, frame = attempt_id.split("|")
    return {"role": "confirmation", "stratum": DATA_STRATUM, "plan_frame_id": attempt_id,
            "alice_sha256": _sha(np.asarray(alice, dtype="<u2").tobytes()),
            "bob_sha256": _sha(np.asarray(bob, dtype="<u2").tobytes()),
            "transcript_bytes_len": len(transcript), "transcript_bytes_sha256": _sha(transcript),
            **dict(outcome)}


def _package_failure_outcome(attempt_id: str, cls: str, reason: str) -> dict[str, Any]:
    stratum, frame = attempt_id.split("|")
    base = {"dataset_id": f"synthetic_{stratum}", "frame_id": attempt_id, "n_pairs": N,
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
    frames = {s: _generate(plan, s) for s in CHANNEL_STRATA}
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
                logger.info("synthetic execute progress: %d/%d attempts (%.0f%%) after %.1fs, %.0f/s, eta %.0fs",
                            attempt_idx, total, 100.0 * attempt_idx / total, elapsed, rate, eta)
            if time.monotonic() - started >= float(plan["caps"]["complete_run_s"]):
                raise TimeoutError("complete_run_cap")
            stratum, frame = attempt_id.split("|")
            i = int(frame[1:])
            alice, bob = frames[stratum]
            current = attempt_id
            appended_current = False
            seeds = [derive_seed(schedule[(stratum, r)], stratum, r, i) for r in (0, 1)]
            result = runner(alice[i], bob[i], pair_idx_sequence=np.arange(N, dtype=np.int64),
                            dataset_id=f"synthetic_{stratum}", frame_id=attempt_id, stratum=DATA_STRATUM,
                            candidate_policy=candidate_policy,
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
                verify_public_payload_v5(outcome, es, alice_symbols=alice[i],
                                         pair_idx_sequence=np.arange(N, dtype=np.int64),
                                         stratum=DATA_STRATUM, candidate_policy=candidate_policy,
                                         policy_manifest=plan["development_binding"]["policy_manifest"],
                                         selection_manifest=plan["development_binding"]["selection"],
                                         channel_model=plan["development_binding"]["channel_model"],
                                         h2_manifest=plan["development_binding"]["h2_manifest"],
                                         locked_seeds=seeds)
                transcript = b"".join(canonical_event_v5(e) for e in es)
            else:
                transcript = b""
            row = _csv_row(attempt_id, outcome, alice[i], bob[i], transcript)
            rows.append(row)
            events.extend(es)
            appended_current = True
        if len(rows) != total:
            raise RuntimeError("outcome accounting")
        _finalize(out, plan, rows, events, "completed", "", test_only=test_only)
    except Exception as exc:
        if current is not None and not appended_current:
            s, f = current.split("|")
            i = int(f[1:])
            rows.append(_csv_row(current, _package_failure_outcome(current, "internal", f"{type(exc).__name__}:{exc}"),
                                 frames[s][0][i], frames[s][1][i], b""))
        if not rows:
            first = attempt_ids[0]
            s, f = first.split("|")
            i = int(f[1:])
            rows.append(_csv_row(first, _package_failure_outcome(first, "internal", f"{type(exc).__name__}:{exc}"),
                                 frames[s][0][i], frames[s][1][i], b""))
        _finalize(out, plan, rows, events, "invalid_execution", f"{type(exc).__name__}:{exc}", test_only=test_only)
        if not test_only:
            raise


def execute_plan(output_dir: Path) -> None:
    _execute(output_dir, run_ldpc_formal_v5, test_only=False)


def _execute_test_plan(output_dir: Path, runner: Callable[..., dict[str, Any]]) -> None:
    _execute(output_dir, runner, test_only=True)
