"""V34 corrected matched empirical-P finite-control diagnostic.

This is intentionally one small research CLI.  It binds the V25 empirical
joint tables, the V31 QC packet, and the V32 oracle-L1 ProductionRunner, then
draws 1024 GF(1024) pairs per block directly from the source table.  The
production decoder is imported only in the authorized ``execute`` path.  The
``--runner`` option is an explicit fake/test seam and is restricted to a fresh
workspace child.

The implementation is a candidate only.  It does not authorize a real run,
does not resume an existing root, and does not alter any historical output.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


# ---------------------------------------------------------------------------
# Frozen identities and matrix
# ---------------------------------------------------------------------------

CHANGE_NAME = "formal-nonbinary-ldpc-v34-corrected-matched-empirical-p-finite-control"
FREEZE_COMMIT = "f5f61eb672afe8e399727fa5d7507ca9f2f9151a"
REPO_ROOT = Path(__file__).resolve().parents[4]
DIAGNOSTICS_REL = "comparison_bench/outputs_comparison/nonbinary_diagnostics"
OFFICIAL_RUN_REL = (
    f"{DIAGNOSTICS_REL}/"
    "nbldpc_v34_corrected_matched_empirical_p_finite_control/run_01"
)
OFFICIAL_RUN_ROOT = REPO_ROOT / OFFICIAL_RUN_REL
WORKSPACE_ROOT = REPO_ROOT / "workspace"
RESULTS_ROOT = REPO_ROOT / "results"
ARCHIVE_ROOT = REPO_ROOT / "openspec" / "changes" / "archive"
SIBLING_CHECKOUT = REPO_ROOT.parent / "HD-QKD_Polar_Release"

V25_REL = f"{DIAGNOSTICS_REL}/nbldpc_v25_20260818/run_04/channel_counts.npz"
V31_PAYLOAD_REL = f"{DIAGNOSTICS_REL}/nbldpc_v31_20260820/run_01/matrix_payloads.json"
V31_MANIFEST_REL = f"{DIAGNOSTICS_REL}/nbldpc_v31_20260820/run_01/RUN_MANIFEST.json"
V32_RUN_REL = f"{DIAGNOSTICS_REL}/nbldpc_v32_finite_de_bridge/run_01/RUN_MANIFEST.json"
V32_CLI_REL = "comparison_bench/src/comparison_bench/cli/run_nonbinary_v32_finite_de_bridge.py"
V28R_CLI_REL = "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v28.py"
V28R_ROOT_REL = f"{DIAGNOSTICS_REL}/nbldpc_v28_gf32_finite_code/run_02_v28r"

V25_COUNTS_SHA256 = "e0360203b8003c821d3ee543bdaf712bd853b0ea712055b936ca37f478ddd5b2"
V31_PACKET_SHA256 = "3d0e8773a436eed59b515f32c1bde9525814f0ecaf0d8af5cd9d2bcd12ce9242"
PACKET_ID = "m1_16_n1024_n1024|QC-cyclic-projective"
FIELD_ID = "c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf"
FIELD_POLY = 37
FACTORIZATION = "F03_natural_MSB_to_LSB_GF32_plus_GF32"
M1 = 16
N = 1024
Q = 32
MAX_ITER = 30
STREAK = 20
RNG_NAME = "PCG64"
NUMPY_REQUIRED = "2.4.0"
SOURCE_ORDER = ("1M", "1p5M", "2M")
SOURCE_IDS = {
    "1M": "type2_1M_20260121_184040",
    "1p5M": "type2_1p5M_20260121_183806",
    "2M": "type2_2M_20260121_183657",
}
NPZ_KEYS = {
    "1M": "type2_1M_20260121_184040_N_ab_train_N_ab_train",
    "1p5M": "type2_1p5M_20260121_183806_N_ab_train_N_ab_train",
    "2M": "type2_2M_20260121_183657_N_ab_train_N_ab_train",
}
M2 = {"1M": 184, "1p5M": 190, "2M": 192}
SEEDS = {
    "1M": tuple(range(340101, 340121)),
    "1p5M": tuple(range(340201, 340221)),
    "2M": tuple(range(340301, 340321)),
}
BLOCKS_PER_SOURCE = 20
TOTAL_CALLS = 60
THRESHOLD = 19

# Compatibility names used by adjacent diagnostic candidates and by the
# acceptance tests.  They are aliases only; there is still one frozen matrix.
N_FROZEN = N
DEFAULT_MAX_ITER = MAX_ITER
DEFAULT_STREAK = STREAK
SOURCE_SEEDS = SEEDS

TERMINAL_PASS = "matched_empirical_finite_control_pass"
TERMINAL_FAIL = "matched_empirical_finite_control_fail"
TERMINAL_INCONCLUSIVE = "matched_empirical_finite_control_inconclusive"
CLAIM_BOUNDARY = (
    "corrected matched empirical-P finite control only; one V31 QC packet; "
    "oracle L1; V32 ProductionRunner max_iter=30; no FER, key rate, "
    "qualification, operational, promotion, or general NB-LDPC claim"
)

MANIFEST_SCHEMA = "nbldpc_v34_corrected_matched_empirical_p_manifest_v1"
RECORD_SCHEMA = "nbldpc_v34_corrected_matched_empirical_p_block_v1"
CALLS_SCHEMA = "nbldpc_v34_corrected_matched_empirical_p_calls_v1"
SUMMARY_SCHEMA = "nbldpc_v34_corrected_matched_empirical_p_source_summary_v1"
FINAL_SCHEMA = "nbldpc_v34_corrected_matched_empirical_p_final_v1"

AUTH_SCHEMA = "nbldpc_v34_execute_auth_v1"
AUTH_EXACT_VALUES = {
    "schema": AUTH_SCHEMA,
    "change": CHANGE_NAME,
    "freeze_commit": FREEZE_COMMIT,
    "official_run_root": OFFICIAL_RUN_REL,
    "decision": "EXECUTE_AUTH",
}
AUTH_KEYS = set(AUTH_EXACT_VALUES) | {
    "implementation_commit", "call_matrix_digest", "granted_by",
    "decision_id", "granted",
}
EXECUTE_AUTH_SCHEMA = AUTH_SCHEMA
EXECUTE_AUTH_EXACT_VALUES = AUTH_EXACT_VALUES
EXECUTE_AUTH_KEYS = AUTH_KEYS
AUTH_FREEZE_COMMIT = FREEZE_COMMIT
BINDING_PATHS = {
    "V25": V25_REL, "V31_PACKET": V31_PAYLOAD_REL,
    "V31_MANIFEST": V31_MANIFEST_REL, "V32_RUN": V32_RUN_REL,
    "V32_CLI": V32_CLI_REL, "V28R_CLI": V28R_CLI_REL,
    "V28R_ROOT": V28R_ROOT_REL,
}
TERMINALS = (TERMINAL_PASS, TERMINAL_FAIL, TERMINAL_INCONCLUSIVE)

PROTECTED_OLD_ROOTS = (
    ("v25", f"{DIAGNOSTICS_REL}/nbldpc_v25_20260818/run_04"),
    ("v26", f"{DIAGNOSTICS_REL}/nbldpc_v26_20260818/run_02"),
    ("v28r", V28R_ROOT_REL),
    ("v31", f"{DIAGNOSTICS_REL}/nbldpc_v31_20260820/run_01"),
    ("v31_closeout_run_01", f"{DIAGNOSTICS_REL}/nbldpc_v31_closeout_audit_v2/run_01"),
    ("v31_closeout_run_02", f"{DIAGNOSTICS_REL}/nbldpc_v31_closeout_audit_v2/run_02"),
    ("v32_finite", f"{DIAGNOSTICS_REL}/nbldpc_v32_finite_de_bridge/run_01"),
    ("v32_audit", f"{DIAGNOSTICS_REL}/nbldpc_v32_operating_point_audit/run_01"),
    ("v32_audit_v2", f"{DIAGNOSTICS_REL}/nbldpc_v32_operating_point_audit_v2/run_01"),
    ("v33", f"{DIAGNOSTICS_REL}/nbldpc_v33_rate_aligned_empirical_de/run_01"),
)

EXIT_OK = 0
EXIT_SELFCHECK_FAILED = 1
EXIT_COLLISION = 2
EXIT_BLOCKED_BINDING = 3
EXIT_EVIDENCE_INCONSISTENT = 4
EXIT_MANIFEST = 5
EXIT_WRITE_GUARD = 6
EXIT_UNAUTHORIZED = 7

REASON_ORDINARY = "ordinary_decode_failure"
FATAL_REASONS = frozenset({
    "binding_failure", "probability_invalid", "probability_support_violation",
    "decoder_interface_exception", "decoder_result_malformed",
    "decoder_result_nonfinite", "decoder_identity_failure", "output_collision",
    "interrupted", "sampler_failure", "evidence_write_failure",
})

REF_N = np.arange(1, 17, dtype=np.float64).reshape((4, 4), order="C")
REF_SEED = 340101
REF_SIZE = 12
REF_IDX = np.array([8, 9, 14, 9, 15, 13, 10, 14, 10, 4, 11, 15], dtype=np.int64)
REF_A = REF_IDX // 4
REF_B = REF_IDX % 4


# ---------------------------------------------------------------------------
# Small pure helpers
# ---------------------------------------------------------------------------

def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def git_head() -> str:
    import subprocess
    try:
        import subprocess as _sp
        return _sp.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                                text=True, stderr=_sp.DEVNULL).strip()
    except Exception:
        return ""


def this_file_sha256() -> str:
    return sha256_file(Path(__file__))


def _lower_hex(value: Any, size: int) -> bool:
    return isinstance(value, str) and len(value) == size and all(
        c in "0123456789abcdef" for c in value)


def _json_load(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _record_write(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True,
                               ensure_ascii=False, allow_nan=False) + "\n",
                    encoding="utf-8")


def enumerate_calls() -> list[dict[str, Any]]:
    calls = []
    ordinal = 1
    for source in SOURCE_ORDER:
        for block, seed in enumerate(SEEDS[source], start=1):
            calls.append({
                "ordinal": ordinal, "source": source,
                "source_id": SOURCE_IDS[source], "block": block,
                "seed": int(seed), "n": N, "m1": M1, "m2": M2[source],
            })
            ordinal += 1
    return calls


def expected_call_matrix_digest() -> str:
    return sha256_bytes(canonical_json({
        "sources_order": list(SOURCE_ORDER),
        "calls": enumerate_calls(),
        "blocks_per_source": BLOCKS_PER_SOURCE,
        "total_calls": TOTAL_CALLS,
        "rng": RNG_NAME,
        "numpy": NUMPY_REQUIRED,
        "max_iter": MAX_ITER,
        "streak": STREAK,
        "threshold": THRESHOLD,
    }).encode())


def _validate_probability_table(counts: np.ndarray) -> tuple[np.ndarray, list[str]]:
    problems: list[str] = []
    arr = np.asarray(counts)
    if arr.shape != (N, N):
        return np.empty(0, dtype=np.float64), [f"shape:{arr.shape!r}"]
    try:
        arr = np.asarray(arr, dtype=np.float64)
    except Exception as exc:
        return np.empty(0, dtype=np.float64), [f"float64:{exc}"]
    if not np.all(np.isfinite(arr)):
        problems.append("nonfinite_counts")
    if np.any(arr < 0):
        problems.append("negative_counts")
    total = float(np.sum(arr, dtype=np.float64))
    if not math.isfinite(total) or total <= 0:
        problems.append("invalid_total")
    if problems:
        return np.empty(0, dtype=np.float64), problems
    p = arr.reshape(-1, order="C") / total
    if not np.all(np.isfinite(p)) or np.any(p < 0):
        problems.append("invalid_probability_vector")
    if not np.isclose(float(p.sum()), 1.0, rtol=1e-12, atol=1e-12):
        problems.append("probability_sum_not_one")
    return np.asarray(p, dtype=np.float64), problems


def sample_empirical_block(counts: np.ndarray, seed: int, size: int = N) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The sole frozen production sampling operation (one PCG64 choice)."""
    p, problems = _validate_probability_table(counts)
    if problems:
        raise ValueError(";".join(problems))
    rng = np.random.Generator(np.random.PCG64(int(seed)))
    idx = rng.choice(N * N, size=int(size), replace=True, p=p)
    idx = np.asarray(idx, dtype=np.int64)
    return idx, idx // N, idx % N


def sampler_reference() -> dict[str, Any]:
    p = REF_N.reshape(-1, order="C") / REF_N.sum()
    rng = np.random.Generator(np.random.PCG64(REF_SEED))
    idx = np.asarray(rng.choice(16, size=REF_SIZE, replace=True, p=p), dtype=np.int64)
    return {"idx": idx.tolist(), "A": (idx // 4).tolist(), "B": (idx % 4).tolist()}


def check_sampler_reference() -> bool:
    got = sampler_reference()
    return got == {"idx": REF_IDX.tolist(), "A": REF_A.tolist(), "B": REF_B.tolist()}


def _counts_context(counts: Mapping[str, Any]) -> dict[str, np.ndarray]:
    out: dict[str, np.ndarray] = {}
    for source in SOURCE_ORDER:
        val = counts.get(source)
        if val is None:
            val = counts.get(SOURCE_IDS[source])
        if val is None:
            raise ValueError(f"missing counts for {source}")
        out[source] = np.asarray(val)
    return out


def _posterior_l2(counts: np.ndarray, bob: np.ndarray, u1: np.ndarray) -> np.ndarray:
    """Build P(U2|B,U1) from the same P(A,B) table; no smoothing."""
    arr = np.asarray(counts, dtype=np.float64)
    b = np.asarray(bob, dtype=np.int64)
    u = np.asarray(u1, dtype=np.int64)
    rows = arr[(u[:, None] * 32 + np.arange(32)[None, :]), b[:, None]]
    denom = rows.sum(axis=1)
    if np.any(~np.isfinite(denom)) or np.any(denom <= 0):
        raise ValueError("zero_or_nonfinite_conditional_denominator")
    rows = rows / denom[:, None]
    if np.any(~np.isfinite(rows)) or np.any(rows < 0):
        raise ValueError("invalid_conditional_probability")
    return rows


def _prior_metrics(prior: np.ndarray, true_u2: np.ndarray) -> dict[str, float]:
    p_true = prior[np.arange(prior.shape[0]), true_u2]
    if np.any(~np.isfinite(p_true)) or np.any(p_true <= 0):
        raise ValueError("sampled_positive_event_has_zero_prior_mass")
    with np.errstate(divide="raise", invalid="raise"):
        nll = -np.log2(p_true)
        entropy = -np.sum(prior * np.log2(np.maximum(prior, 1e-300)), axis=1)
    ranks = np.sum(prior > p_true[:, None], axis=1)
    return {
        "posterior_nll_bits_per_symbol": float(np.mean(nll)),
        "posterior_entropy_bits_per_symbol": float(np.mean(entropy)),
        "truth_symbol_rank_mean": float(np.mean(ranks)),
        "true_prior_probability_mean": float(np.mean(p_true)),
    }


def _histogram(values: np.ndarray, bins: int) -> list[int]:
    return np.bincount(np.asarray(values, dtype=np.int64), minlength=bins).astype(int).tolist()


def _factor(symbols: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(symbols, dtype=np.int64)
    return x >> 5, x & 31


def _tag64(x1: Sequence[int], x2: Sequence[int]) -> str:
    payload = bytes(int(v) & 0xff for v in x1) + bytes(int(v) & 0xff for v in x2)
    return sha256_bytes(payload)[:16]


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        v = int(value)
        return v if v >= 0 else default
    except Exception:
        return default


# ---------------------------------------------------------------------------
# Read-only stage-0 binding validation
# ---------------------------------------------------------------------------

def _real_counts(repo_root: Path) -> dict[str, np.ndarray]:
    path = repo_root / V25_REL
    with np.load(path, allow_pickle=False) as data:
        return {source: np.asarray(data[NPZ_KEYS[source]]) for source in SOURCE_ORDER}


def _packet_info(repo_root: Path) -> dict[str, Any]:
    path = repo_root / V31_PAYLOAD_REL
    doc = _json_load(path)
    packets = [p for p in doc.get("packets", []) if p.get("packet_id") == PACKET_ID]
    if len(packets) != 1:
        raise ValueError("packet_not_unique")
    packet = packets[0]
    mats = packet.get("matrices") or {}
    if len(mats.get("L1", [])) != M1 or int(packet.get("n", -1)) != N:
        raise ValueError("packet_L1_or_n_mismatch")
    m2_by_source = packet.get("m2_by_source") or {}
    if {s: int(m2_by_source.get(s, -1)) for s in SOURCE_ORDER} != M2:
        raise ValueError("packet_m2_mismatch")
    if any(int(m2_by_source.get(s, -1)) in (194, 200, 202) for s in SOURCE_ORDER):
        raise ValueError("forbidden_V28R_m2")
    return {
        "packet_id": PACKET_ID, "sha256": sha256_file(path),
        "graph_packet_identity": sha256_file(path)[:16],
        "m1": M1, "n": N, "m2_by_source": dict(M2),
        "field_id": FIELD_ID,
    }


def _binding_report_from_context(context: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    report = dict(context.get("bindings") or {})
    if report.get("ok") is not True:
        raise ValueError("fake_binding_report_not_ok")
    counts = _counts_context(context.get("counts") or {})
    for source, arr in counts.items():
        _, problems = _validate_probability_table(arr)
        if problems:
            raise ValueError(f"{source}:" + ";".join(problems))
    return report, counts


def stage0_validate(repo_root: Path = REPO_ROOT, provider: Any = None) -> tuple[dict[str, Any], dict[str, np.ndarray] | None]:
    """Read-only binding gate.  It never imports or calls a decoder."""
    # Environment and sampler identity are binding requirements even for a
    # fake provider; otherwise a test fixture could silently bypass REF1.
    if np.__version__ != NUMPY_REQUIRED:
        return {"schema": MANIFEST_SCHEMA, "ok": False,
                "reasons": [f"numpy_version:{np.__version__}!={NUMPY_REQUIRED}"]}, None
    if not check_sampler_reference():
        return {"schema": MANIFEST_SCHEMA, "ok": False,
                "reasons": ["V34-PCG64-REF1_mismatch"]}, None
    if provider is not None and hasattr(provider, "binding_context"):
        try:
            context = provider.binding_context(repo_root)
            report, counts = _binding_report_from_context(context)
            if report.get("numpy_version", np.__version__) != NUMPY_REQUIRED or \
                    report.get("sampler_reference", True) is not True:
                raise ValueError("fake_environment_binding_mismatch")
            report.setdefault("schema", "nbldpc_v34_fake_bindings_v1")
            report.setdefault("numpy_version", np.__version__)
            report.setdefault("call_matrix_digest", expected_call_matrix_digest())
            report.setdefault("sampler_reference", check_sampler_reference())
            return report, counts
        except Exception as exc:
            return {"schema": MANIFEST_SCHEMA, "ok": False,
                    "reasons": [f"fake_binding:{exc}"]}, None

    problems: list[str] = []
    bindings: dict[str, Any] = {}
    counts: dict[str, np.ndarray] | None = None
    if np.__version__ != NUMPY_REQUIRED:
        problems.append(f"numpy_version:{np.__version__}!={NUMPY_REQUIRED}")
    if not check_sampler_reference():
        problems.append("V34-PCG64-REF1_mismatch")

    counts_path = repo_root / V25_REL
    if not counts_path.is_file():
        problems.append("missing_V25_counts")
    else:
        actual_sha = sha256_file(counts_path)
        bindings["v25_counts"] = {"path": V25_REL, "sha256": actual_sha,
                                    "expected_sha256": V25_COUNTS_SHA256,
                                    "keys": dict(NPZ_KEYS)}
        if actual_sha != V25_COUNTS_SHA256:
            problems.append("v25_counts_sha256_mismatch")
        try:
            counts = _real_counts(repo_root)
            for source, arr in counts.items():
                _, p = _validate_probability_table(arr)
                if p:
                    problems.extend(f"{source}:{x}" for x in p)
        except Exception as exc:
            problems.append(f"v25_counts_unreadable:{exc}")

    packet_path = repo_root / V31_PAYLOAD_REL
    if not packet_path.is_file():
        problems.append("missing_V31_packet")
    else:
        actual_sha = sha256_file(packet_path)
        bindings["v31_packet"] = {"path": V31_PAYLOAD_REL, "sha256": actual_sha,
                                   "expected_sha256": V31_PACKET_SHA256,
                                   "packet_id": PACKET_ID, "m1": M1, "m2": dict(M2)}
        if actual_sha != V31_PACKET_SHA256:
            problems.append("v31_packet_sha256_mismatch")
        try:
            _packet_info(repo_root)
        except Exception as exc:
            problems.append(f"v31_packet_invalid:{exc}")

    v32_path = repo_root / V32_CLI_REL
    if not v32_path.is_file():
        problems.append("missing_v32_production_source")
    else:
        source = v32_path.read_text(encoding="utf-8")
        required = ("class ProductionRunner", "def run_block", "decode_error_domain_posterior",
                    "l1_mode")
        if any(token not in source for token in required):
            problems.append("v32_production_identity_mismatch")
        bindings["v32_production_runner"] = {
            "path": V32_CLI_REL, "sha256": sha256_file(v32_path),
            "identity": "run_nonbinary_v32_finite_de_bridge.ProductionRunner",
            "oracle_branch": True, "max_iter": MAX_ITER, "streak": STREAK,
        }
    v28_path = repo_root / V28R_CLI_REL
    if not v28_path.is_file():
        problems.append("missing_v28r_decoder_source")
    else:
        v28_source = v28_path.read_text(encoding="utf-8")
        if "def decode_error_domain_posterior" not in v28_source:
            problems.append("v28r_decoder_function_missing")
        bindings["v28r_decoder"] = {
            "path": V28R_CLI_REL, "sha256": sha256_file(v28_path),
            "identity": "nonbinary_v28.decode_error_domain_posterior",
            "import_only_at_execute": True,
        }
    # Bind the V32 persisted schedule when present; this check is read-only.
    v32_manifest = repo_root / V32_RUN_REL
    if v32_manifest.is_file():
        try:
            vm = _json_load(v32_manifest)
            b1 = ((vm.get("arms") or {}).get("B1") or {})
            if int(b1.get("blocks_per_source", -1)) != BLOCKS_PER_SOURCE:
                problems.append("v32_schedule_block_count_mismatch")
            disc = vm.get("discriminator") or {}
            if disc.get("block_success") != "exact && tag && syndrome && !false_accept":
                problems.append("v32_success_predicate_mismatch")
            bindings["v32_run_manifest"] = {"path": V32_RUN_REL,
                                             "sha256": sha256_file(v32_manifest),
                                             "max_iter": MAX_ITER, "streak": STREAK,
                                             "threshold": THRESHOLD}
        except Exception as exc:
            problems.append(f"v32_manifest_invalid:{exc}")
    else:
        # The persisted bridge is provenance; source identity remains mandatory.
        bindings["v32_run_manifest"] = {"path": V32_RUN_REL, "missing": True}

    report = {
        "schema": MANIFEST_SCHEMA.replace("manifest", "bindings"),
        "ok": not problems,
        "reasons": problems,
        "numpy_version": np.__version__,
        "numpy_required": NUMPY_REQUIRED,
        "sampler_reference_id": "V34-PCG64-REF1",
        "sampler_reference": check_sampler_reference(),
        "field": {"field_id": FIELD_ID, "primitive_polynomial": FIELD_POLY,
                   "factorization": FACTORIZATION},
        "packet": {"packet_id": PACKET_ID, "m1": M1, "m2": dict(M2), "n": N},
        "bindings": bindings,
        "sources": {s: {"source_id": SOURCE_IDS[s], "npz_key": NPZ_KEYS[s],
                         "m2": M2[s]} for s in SOURCE_ORDER},
        "call_matrix_digest": expected_call_matrix_digest(),
        "matrix": enumerate_calls(),
        "verified_utc": utc_now(),
    }
    return report, counts


# ---------------------------------------------------------------------------
# Runner seam and production decoder adapter
# ---------------------------------------------------------------------------

def load_runner(spec: str) -> Any:
    module_name, attr = spec.split(":", 1)
    obj = getattr(importlib.import_module(module_name), attr)
    return obj() if isinstance(obj, type) else obj


def _production_runner(repo_root: Path, packet_sha: str):
    """Lazy V32 ProductionRunner import; call only after production auth."""
    mod = importlib.import_module(
        "comparison_bench.src.comparison_bench.cli.run_nonbinary_v32_finite_de_bridge")
    identity = {"graph_packet_identity": packet_sha[:16]}
    prod = mod.ProductionRunner(repo_root, identity["graph_packet_identity"])
    syndrome_fn = mod._default_syndrome_fn_factory(repo_root, identity)
    return prod, syndrome_fn


def _fake_syndrome(source: str, layer: str) -> list[int]:
    return [0] * (M1 if layer == "L1" else M2[source])


def _make_request(call: Mapping[str, Any], counts: np.ndarray,
                  *, fake: bool, syndrome_fn: Any = None) -> tuple[dict[str, Any], dict[str, Any]]:
    idx, alice, bob = sample_empirical_block(counts, int(call["seed"]), N)
    x1, x2 = _factor(alice)
    y1, y2 = _factor(bob)
    prior2 = _posterior_l2(counts, bob, x1)
    metrics = _prior_metrics(prior2, x2)
    delta = (bob - alice) % (N)
    if fake or syndrome_fn is None:
        s1 = _fake_syndrome(str(call["source"]), "L1")
        s2 = _fake_syndrome(str(call["source"]), "L2")
    else:
        s1 = syndrome_fn("L1", str(call["source"]), x1.tolist())
        s2 = syndrome_fn("L2", str(call["source"]), x2.tolist())
    request = {
        "ordinal": int(call["ordinal"]), "source": call["source"],
        "source_id": call["source_id"], "block": int(call["block"]),
        "seed": int(call["seed"]), "block_uid": f"V34|{call['source']}|{call['block']}",
        "l1_mode": "oracle", "y1": y1.tolist(), "y2": y2.tolist(),
        "s1": list(s1), "s2": list(s2), "prior_l2": prior2,
        "max_iter": MAX_ITER, "streak": STREAK,
        "operational": False, "qualification": False,
    }
    private = {
        "idx": idx, "alice": alice, "bob": bob, "x1": x1, "x2": x2,
        "y1": y1, "y2": y2, "prior2": prior2, "metrics": metrics,
        "delta": delta,
        "sampled_pair_digest": sha256_bytes(np.asarray(idx, dtype=np.int64).tobytes()),
    }
    return request, private


def _normalise_result(result: Mapping[str, Any], private: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(result, Mapping):
        raise ValueError("decoder_result_malformed")
    # Decoder implementations may expose optional numerical diagnostics.  If
    # supplied, non-finite values are evidence failures, never ordinary block
    # failures.  (The mechanical booleans below remain the only success test.)
    for key in ("iterations", "l1_iterations", "l2_iterations", "runtime_s",
                "posterior_nll", "posterior_entropy"):
        if key in result and result[key] is not None:
            try:
                if not math.isfinite(float(result[key])):
                    raise ValueError("decoder_result_nonfinite")
            except (TypeError, ValueError) as exc:
                if str(exc) == "decoder_result_nonfinite":
                    raise
                raise ValueError("decoder_result_malformed") from exc
    # A fake runner can return the four mechanical predicates directly.  When
    # it also supplies x2_hat, keep and validate that candidate for independent
    # L2-error accounting; the mechanical predicates remain the fake seam's
    # explicit success inputs.
    x2_hat = None
    if all(k in result for k in ("exact_l2", "syndrome_ok", "tag_ok", "false_accept")):
        values = {k: result[k] for k in ("exact_l2", "syndrome_ok", "tag_ok", "false_accept")}
        if any(not isinstance(v, (bool, np.bool_)) for v in values.values()):
            raise ValueError("decoder_result_malformed")
        exact, syndrome, tag, false_accept = (bool(values[k]) for k in values)
        raw_xhat = result.get("x2_hat")
        if raw_xhat is not None:
            try:
                x2_hat = np.asarray(raw_xhat, dtype=np.int64)
            except Exception as exc:
                raise ValueError(f"decoder_result_malformed:{exc}") from exc
            if x2_hat.shape != (N,) or np.any(x2_hat < 0) or np.any(x2_hat >= 32):
                raise ValueError("decoder_result_malformed")
    else:
        raw_xhat = result.get("x2_hat")
        # V32 returns a complete legal status object even when the decoder
        # cannot produce a candidate (x2_hat=None).  That is an ordinary
        # decode failure and the frozen matrix must continue to the next block.
        if raw_xhat is None and ("l2_status" in result or "l2_syndrome_ok" in result):
            exact = False
            syndrome = bool(result.get("l2_syndrome_ok", False))
            tag = False
            false_accept = False
        elif raw_xhat is None:
            raise ValueError("decoder_result_malformed")
        else:
            try:
                x2_hat = np.asarray(raw_xhat, dtype=np.int64)
            except Exception as exc:
                raise ValueError(f"decoder_result_malformed:{exc}") from exc
            if x2_hat.shape != (N,) or np.any(x2_hat < 0) or np.any(x2_hat >= 32):
                raise ValueError("decoder_result_malformed")
            exact = bool(np.array_equal(x2_hat, private["x2"]))
            syndrome = bool(result.get("l2_syndrome_ok"))
            tag = bool(_tag64(private["x1"], x2_hat) == _tag64(private["x1"], private["x2"]))
            false_accept = bool(tag and not exact)
    iters = _safe_int(result.get("l2_iterations", result.get("iterations", 0)))
    runtime_s = result.get("runtime_s", 0.0)
    try:
        runtime_s = float(runtime_s)
    except Exception as exc:
        raise ValueError(f"decoder_result_malformed:{exc}") from exc
    if not math.isfinite(runtime_s) or runtime_s < 0:
        raise ValueError("decoder_result_nonfinite")
    if iters > MAX_ITER:
        raise ValueError("decoder_result_malformed")
    success = bool(exact and syndrome and tag and not false_accept)
    if x2_hat is None:
        l2_errors_final = N
        l2_error_accounting = "candidate_unavailable"
    else:
        # The decoder's optional l2_errors_final field is deliberately ignored:
        # this is the authoritative GF(32)-symbol comparison against the
        # sampled Alice layer, and remains independently replayable from the
        # persisted x2_hat plus the frozen sampler.
        l2_errors_final = int(np.count_nonzero(x2_hat != private["x2"]))
        l2_error_accounting = "measured"
    return {
        "exact_l2": exact, "syndrome_ok": syndrome, "tag_ok": tag,
        "false_accept": false_accept, "success": success,
        "l2_status": str(result.get("l2_status", "fake")),
        "l2_iterations": iters, "runtime_s": runtime_s,
        "x2_hat": None if x2_hat is None else x2_hat.tolist(),
        "l2_errors_final": l2_errors_final,
        "l2_error_accounting": l2_error_accounting,
        "decoder_terminal_status": str(result.get("terminal", result.get("l2_status", "complete"))),
    }


def _build_record(call: Mapping[str, Any], private: Mapping[str, Any],
                  result: Mapping[str, Any], report: Mapping[str, Any],
                  fatal: str | None = None, detail: str = "") -> dict[str, Any]:
    source = str(call["source"])
    metrics = private.get("metrics", {})
    if fatal:
        terminal = "INCONCLUSIVE"
        success = False
    else:
        terminal = "PASS" if result.get("success") else "FAIL"
        success = bool(result.get("success"))
    rec = {
        "schema": RECORD_SCHEMA, "ordinal": int(call["ordinal"]),
        "source": source, "source_id": SOURCE_IDS[source],
        "block": int(call["block"]), "seed": int(call["seed"]),
        "block_uid": f"V34|{source}|{call['block']}",
        "packet_id": PACKET_ID, "packet_sha256": V31_PACKET_SHA256,
        "packet_m1": M1, "packet_m2": M2[source], "field_id": FIELD_ID,
        "posterior_identity": V25_COUNTS_SHA256[:16],
        "truth_used": True, "truth_role": "oracle_l1",
        "operational": False, "qualification": False,
        "sample_rng": RNG_NAME, "numpy_version": NUMPY_REQUIRED,
        "sampler_choice_calls": 1,
        "sampled_pair_digest": private.get("sampled_pair_digest"),
        "sampled_ser": float(np.mean(private["alice"] != private["bob"])),
        "delta_histogram": _histogram(private["delta"], N),
        "empirical_support_violations": int(np.sum(
            np.asarray(private.get("support_mask", np.ones(N, dtype=bool)) == False))),
        "posterior_nll_bits_per_symbol": float(metrics.get("posterior_nll_bits_per_symbol", math.nan)),
        "posterior_entropy_bits_per_symbol": float(metrics.get("posterior_entropy_bits_per_symbol", math.nan)),
        "truth_symbol_rank_mean": float(metrics.get("truth_symbol_rank_mean", math.nan)),
        "true_prior_probability_mean": float(metrics.get("true_prior_probability_mean", math.nan)),
        "l2_errors_initial": int(np.sum(private["x2"] != private["y2"])),
        "l2_errors_final": int(result.get("l2_errors_final", N)),
        "x2_hat": result.get("x2_hat"),
        "l2_error_accounting": str(result.get("l2_error_accounting", "candidate_unavailable")),
        "l2_status": str(result.get("l2_status", "not_run")),
        "l2_iterations": int(result.get("l2_iterations", 0)),
        "runtime_s": float(result.get("runtime_s", 0.0)),
        "exact_l2": bool(result.get("exact_l2", False)),
        "syndrome_ok": bool(result.get("syndrome_ok", False)),
        "tag_ok": bool(result.get("tag_ok", False)),
        "false_accept": bool(result.get("false_accept", False)),
        "success": success, "terminal": terminal,
        "decoder_terminal_status": str(result.get("decoder_terminal_status", "not_run")),
        "syndrome_leakage_bits": int(M2[source] * 5),
        "verification_leakage_bits": 64,
        "fatal": fatal is not None, "reason": fatal or ("" if success else REASON_ORDINARY),
        "detail": detail,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    return rec


# ---------------------------------------------------------------------------
# Execution and evidence
# ---------------------------------------------------------------------------

def guard_run_root(run_root: Path, fake: bool = False) -> Path:
    rp = Path(os.path.abspath(str(run_root))).resolve()
    if SIBLING_CHECKOUT.exists():
        sib = SIBLING_CHECKOUT.resolve()
        if rp == sib or sib in rp.parents:
            raise PermissionError("sibling checkout forbidden")
    for _, rel in PROTECTED_OLD_ROOTS:
        prot = (REPO_ROOT / rel).resolve()
        if rp == prot or prot in rp.parents:
            raise PermissionError("protected historical root forbidden")
    for root in (RESULTS_ROOT, ARCHIVE_ROOT, REPO_ROOT / "comparison_bench" / "outputs_comparison"):
        rr = root.resolve()
        if rp == rr or rr in rp.parents:
            # official root is a narrow exception in production mode.
            if not (not fake and rp == OFFICIAL_RUN_ROOT.resolve()):
                raise PermissionError("broad protected root forbidden")
    official = OFFICIAL_RUN_ROOT.resolve()
    if fake:
        ws = WORKSPACE_ROOT.resolve()
        if rp == ws or ws not in rp.parents or rp == official or official in rp.parents:
            raise PermissionError("fake writes require a workspace child")
    elif rp != official:
        raise PermissionError("production writes only official run_01")
    return rp


def validate_execute_auth(auth: Any, expected_commit: str | None = None) -> str | None:
    if not isinstance(auth, dict):
        return "auth_payload_not_object"
    if set(auth) != AUTH_KEYS:
        return f"auth_keys_mismatch:missing={sorted(AUTH_KEYS-set(auth))};extra={sorted(set(auth)-AUTH_KEYS)}"
    for key, want in AUTH_EXACT_VALUES.items():
        if not isinstance(auth.get(key), str) or auth.get(key) != want:
            return f"{key}_mismatch"
    commit = auth.get("implementation_commit")
    current = expected_commit or git_head()
    if not _lower_hex(commit, 40) or commit != current:
        return "implementation_commit_mismatch_current_HEAD"
    if not _lower_hex(auth.get("call_matrix_digest"), 64) or \
            auth["call_matrix_digest"] != expected_call_matrix_digest():
        return "call_matrix_digest_mismatch"
    if not isinstance(auth.get("granted_by"), str) or not auth["granted_by"].strip():
        return "granted_by_invalid"
    if not isinstance(auth.get("decision_id"), str) or not auth["decision_id"].strip():
        return "decision_id_invalid"
    if auth.get("granted") is not True:
        return "granted_not_true"
    return None


def _manifest(report: Mapping[str, Any], run_root: Path, fake: bool,
              auth_info: Mapping[str, Any]) -> dict[str, Any]:
    body = {
        "schema": MANIFEST_SCHEMA, "change": CHANGE_NAME,
        "generated_utc": utc_now(), "run_root": str(run_root),
        "mode": "fake" if fake else "production",
        "auth": dict(auth_info), "freeze_commit": FREEZE_COMMIT,
        "implementation_commit": git_head(),
        "numpy_version": np.__version__, "numpy_required": NUMPY_REQUIRED,
        "sampler_reference_id": "V34-PCG64-REF1",
        "field": {"field_id": FIELD_ID, "primitive_polynomial": FIELD_POLY,
                   "factorization": FACTORIZATION},
        "packet": {"packet_id": PACKET_ID, "sha256": V31_PACKET_SHA256,
                   "m1": M1, "m2": dict(M2), "n": N},
        "decoder": {"identity": "V32.ProductionRunner -> V28R.decode_error_domain_posterior",
                     "max_iter": MAX_ITER, "streak": STREAK,
                     "l1_mode": "oracle", "l1_decoded": False},
        "matrix": {"sources_order": list(SOURCE_ORDER), "calls": enumerate_calls(),
                    "total_calls": TOTAL_CALLS, "digest": expected_call_matrix_digest(),
                    "threshold": THRESHOLD, "blocks_per_source": BLOCKS_PER_SOURCE,
                    "rng": RNG_NAME},
        "bindings": dict(report.get("bindings") or {}),
        "source_bindings": dict(report.get("sources") or {}),
        "claim_boundary": CLAIM_BOUNDARY,
        "no_resume_no_retry": True,
        "output_inventory": ["audit_manifest.json", "block_records.json",
                              "source_summaries.json", "final_state.json",
                              "operator_handoff.md"],
    }
    body["freeze_digest"] = sha256_bytes(canonical_json(body).encode())
    return body


def _verify_manifest_digest(manifest: Mapping[str, Any]) -> bool:
    digest = manifest.get("freeze_digest")
    if not isinstance(digest, str):
        return False
    body = {k: v for k, v in manifest.items() if k != "freeze_digest"}
    try:
        return digest == sha256_bytes(canonical_json(body).encode())
    except Exception:
        return False


def _aggregate(records: Sequence[Mapping[str, Any]]) -> tuple[dict[str, dict[str, Any]], str]:
    summaries: dict[str, dict[str, Any]] = {}
    inconclusive = False
    all_pass = True
    for source in SOURCE_ORDER:
        own = [r for r in records if r.get("source") == source]
        successes = sum(bool(r.get("success")) for r in own)
        fatal = sum(bool(r.get("fatal")) or r.get("terminal") == "INCONCLUSIVE" for r in own)
        missing = max(0, BLOCKS_PER_SOURCE - len(own))
        if fatal or missing:
            terminal = "INCONCLUSIVE"
            inconclusive = True
        elif successes >= THRESHOLD:
            terminal = "PASS"
        else:
            terminal = "FAIL"
            all_pass = False
        if terminal != "PASS":
            all_pass = False
        summaries[source] = {
            "schema": SUMMARY_SCHEMA, "source": source,
            "source_id": SOURCE_IDS[source], "attempted": len(own),
            "completed": len(own) - fatal, "missing": missing,
            "duplicates": len(own) - len({r.get("block_uid") for r in own}),
            "successes": successes, "denominator": BLOCKS_PER_SOURCE,
            "threshold": THRESHOLD, "terminal": terminal,
            "m1": M1, "m2": M2[source], "syndrome_leakage_bits": M2[source] * 5,
            "verification_leakage_bits": 64,
            "false_accepts": sum(bool(r.get("false_accept")) for r in own),
            "decoder_terminal_counts": {
                key: sum(r.get("terminal") == key for r in own)
                for key in ("PASS", "FAIL", "INCONCLUSIVE")
            },
            "iterations": [r.get("l2_iterations") for r in own],
            "runtime_s": [r.get("runtime_s") for r in own],
            "success_components": {
                "exact_l2": sum(bool(r.get("exact_l2")) for r in own),
                "syndrome_ok": sum(bool(r.get("syndrome_ok")) for r in own),
                "tag_ok": sum(bool(r.get("tag_ok")) for r in own),
                "no_false_accept": sum(not bool(r.get("false_accept")) for r in own),
            },
        }
    if inconclusive:
        overall = TERMINAL_INCONCLUSIVE
    elif all_pass:
        overall = TERMINAL_PASS
    else:
        overall = TERMINAL_FAIL
    return summaries, overall


def _write_handoff(run_root: Path, overall: str, records: Sequence[Mapping[str, Any]]) -> None:
    text = ("# V34 operator handoff\n\n"
            f"- overall terminal: `{overall}`\n"
            f"- records persisted: {len(records)}/{TOTAL_CALLS}\n"
            "- oracle L1: true U1 is used only to condition P(U2|B,U1); no L1 decoder call\n"
            "- threshold: each source >=19/20; mechanical discriminator only\n"
            "- claim boundary: bounded corrected matched empirical-P finite control only\n"
            "- successor/rerun/resume: not authorized\n")
    (run_root / "operator_handoff.md").write_text(text, encoding="utf-8")


def execute_run(repo_root: Path, run_root: Path, *, provider: Any = None,
                fake: bool = False, auth_info: Mapping[str, Any] | None = None) -> tuple[int, dict[str, Any] | None]:
    """Execute exactly the frozen matrix; only explicit fake or auth production."""
    try:
        run_root = guard_run_root(run_root, fake=fake)
    except PermissionError as exc:
        print(json.dumps({"blocked": "write_guard", "detail": str(exc)}))
        return EXIT_WRITE_GUARD, None
    if run_root.exists():
        print(json.dumps({"blocked": "output_collision", "run_root": str(run_root)}))
        return EXIT_COLLISION, None

    report, counts = stage0_validate(repo_root, provider if fake else None)
    if not report.get("ok") or counts is None:
        print(json.dumps({"blocked": "binding_failure", "reasons": report.get("reasons", [])}))
        return EXIT_BLOCKED_BINDING, None
    try:
        counts = _counts_context(counts)
    except Exception as exc:
        print(json.dumps({"blocked": "binding_failure", "detail": str(exc)}))
        return EXIT_BLOCKED_BINDING, None

    run_root.mkdir(parents=True)
    auth_info = dict(auth_info or ({"mechanism": "fake_runner"} if fake else {}))
    manifest = _manifest(report, run_root, fake, auth_info)
    _record_write(run_root / "audit_manifest.json", manifest)
    records: list[dict[str, Any]] = []
    calls_path = run_root / "block_records.json"
    prod = syndrome_fn = None
    # The production implementation is imported only after auth and manifest.
    if not fake:
        try:
            prod, syndrome_fn = _production_runner(repo_root, V31_PACKET_SHA256)
        except Exception as exc:
            rec = {"schema": RECORD_SCHEMA, "fatal": True, "terminal": "INCONCLUSIVE",
                   "reason": "decoder_identity_failure", "detail": str(exc),
                   "claim_boundary": CLAIM_BOUNDARY}
            records.append(rec)
            _record_write(calls_path, {"schema": CALLS_SCHEMA, "records": records})
            summaries, overall = _aggregate(records)
            _record_write(run_root / "source_summaries.json", summaries)
            final = {"schema": FINAL_SCHEMA, "change": CHANGE_NAME,
                     "overall_terminal": overall, "terminal": overall,
                     "records": len(records), "calls_total": TOTAL_CALLS,
                     "candidate_only": True, "main_acceptance_pending": True,
                     "qualification": False, "promotion": False,
                     "claim_boundary": CLAIM_BOUNDARY,
                     "freeze_digest_ref": manifest["freeze_digest"],
                     "fatal": True, "no_resume_no_retry": True}
            _record_write(run_root / "final_state.json", final)
            _write_handoff(run_root, overall, records)
            return EXIT_BLOCKED_BINDING, final

    for call in enumerate_calls():
        private: dict[str, Any] = {}
        try:
            request, private = _make_request(call, counts[call["source"]],
                                             fake=fake,
                                             syndrome_fn=syndrome_fn)
            # Keep a local support assertion: every direct empirical draw must
            # have positive mass, and no fallback/resample is legal.
            positive = np.asarray(counts[call["source"]], dtype=np.float64)[
                private["alice"], private["bob"]] > 0
            private["support_mask"] = positive
            if not bool(np.all(positive)):
                raise ValueError("probability_support_violation")
            # The harness measurement is authoritative for runtime_s.  Keep
            # the boundary identical for fake and production calls: sampling,
            # posterior construction, and evidence writes are outside it.
            started = time.monotonic()
            if fake:
                result = provider.run_call(request)
            else:
                result = prod.run_block(request)
            runtime_s = time.monotonic() - started
            if not math.isfinite(runtime_s) or runtime_s < 0:
                raise ValueError("decoder_result_nonfinite")
            norm = _normalise_result(result, private)
            norm["runtime_s"] = float(runtime_s)
            rec = _build_record(call, private, norm, report)
        except KeyboardInterrupt as exc:
            rec = _build_record(call, private or {"alice": np.zeros(N, dtype=np.int64),
                                                   "bob": np.zeros(N, dtype=np.int64),
                                                   "x1": np.zeros(N, dtype=np.int64),
                                                   "x2": np.zeros(N, dtype=np.int64),
                                                   "y2": np.zeros(N, dtype=np.int64),
                                                   "delta": np.zeros(N, dtype=np.int64),
                                                   "metrics": {}}, {}, report,
                                "interrupted", str(exc))
            records.append(rec)
            _record_write(calls_path, {"schema": CALLS_SCHEMA, "records": records})
            break
        except ValueError as exc:
            reason = str(exc).split(":", 1)[0] or "decoder_result_malformed"
            if reason not in FATAL_REASONS:
                reason = "decoder_result_malformed"
            fallback = private or {"alice": np.zeros(N, dtype=np.int64),
                                   "bob": np.zeros(N, dtype=np.int64),
                                   "x1": np.zeros(N, dtype=np.int64),
                                   "x2": np.zeros(N, dtype=np.int64),
                                   "y2": np.zeros(N, dtype=np.int64),
                                   "delta": np.zeros(N, dtype=np.int64), "metrics": {}}
            rec = _build_record(call, fallback, {}, report, reason, str(exc))
            records.append(rec)
            _record_write(calls_path, {"schema": CALLS_SCHEMA, "records": records})
            break
        except Exception as exc:  # interface exceptions are fatal and retained
            fallback = private or {"alice": np.zeros(N, dtype=np.int64),
                                   "bob": np.zeros(N, dtype=np.int64),
                                   "x1": np.zeros(N, dtype=np.int64),
                                   "x2": np.zeros(N, dtype=np.int64),
                                   "y2": np.zeros(N, dtype=np.int64),
                                   "delta": np.zeros(N, dtype=np.int64), "metrics": {}}
            rec = _build_record(call, fallback, {}, report,
                                "decoder_interface_exception", repr(exc))
            records.append(rec)
            _record_write(calls_path, {"schema": CALLS_SCHEMA, "records": records})
            break
        records.append(rec)
        _record_write(calls_path, {"schema": CALLS_SCHEMA, "records": records})

    summaries, overall = _aggregate(records)
    _record_write(run_root / "source_summaries.json", summaries)
    final = {
        "schema": FINAL_SCHEMA, "change": CHANGE_NAME,
        "overall_terminal": overall, "terminal": overall,
        "records": len(records), "calls_total": TOTAL_CALLS,
        "candidate_only": True, "main_acceptance_pending": True,
        "qualification": False, "promotion": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "freeze_digest_ref": manifest["freeze_digest"],
        "fatal": any(bool(r.get("fatal")) for r in records),
        "no_resume_no_retry": True,
    }
    _record_write(run_root / "final_state.json", final)
    _write_handoff(run_root, overall, records)
    print(json.dumps({"ok": overall != TERMINAL_INCONCLUSIVE,
                      "run_root": str(run_root), "overall_terminal": overall,
                      "records": len(records)}))
    return EXIT_OK if overall != TERMINAL_INCONCLUSIVE else EXIT_EVIDENCE_INCONSISTENT, final


# ---------------------------------------------------------------------------
# Strict read-only verify
# ---------------------------------------------------------------------------

def _verify_records(records: list[dict[str, Any]], counts: Mapping[str, np.ndarray],
                    manifest: Mapping[str, Any]) -> list[str]:
    problems: list[str] = []
    expected = enumerate_calls()
    if len(records) != int(manifest.get("matrix", {}).get("total_calls", TOTAL_CALLS)):
        # A retained fatal root is validly partial only when terminal is inconclusive.
        if manifest.get("mode") == "fake" and len(records) < TOTAL_CALLS:
            pass
        else:
            problems.append(f"record_count:{len(records)}")
    seen = set()
    for i, rec in enumerate(records):
        if i >= len(expected):
            problems.append(f"extra_record:{i}")
            continue
        exp = expected[i]
        key = (rec.get("source"), rec.get("block"), rec.get("seed"))
        if key in seen:
            problems.append(f"duplicate_call:{key}")
        seen.add(key)
        if key != (exp["source"], exp["block"], exp["seed"]) or rec.get("ordinal") != exp["ordinal"]:
            problems.append(f"out_of_order:{i}")
        for field, want in (("source_id", SOURCE_IDS[exp["source"]]),
                            ("packet_id", PACKET_ID), ("packet_sha256", V31_PACKET_SHA256),
                            ("packet_m1", M1), ("packet_m2", M2[exp["source"]]),
                            ("field_id", FIELD_ID), ("truth_used", True),
                            ("truth_role", "oracle_l1"), ("operational", False),
                            ("qualification", False), ("sample_rng", RNG_NAME),
                            ("numpy_version", NUMPY_REQUIRED), ("sampler_choice_calls", 1),
                            ("claim_boundary", CLAIM_BOUNDARY)):
            if rec.get(field) != want:
                problems.append(f"field_drift:{i}:{field}")
        try:
            idx, alice, bob = sample_empirical_block(counts[exp["source"]], exp["seed"], N)
            digest = sha256_bytes(np.asarray(idx, dtype=np.int64).tobytes())
            if rec.get("sampled_pair_digest") != digest:
                problems.append(f"sampler_digest_drift:{i}")
            sampled_ser = float(np.mean(alice != bob))
            if not math.isclose(float(rec.get("sampled_ser")), sampled_ser, rel_tol=0, abs_tol=1e-15):
                problems.append(f"sampled_ser_drift:{i}")
            if rec.get("delta_histogram") != _histogram((bob - alice) % N, N):
                problems.append(f"delta_histogram_drift:{i}")
            if int(rec.get("empirical_support_violations", -1)) != 0:
                problems.append(f"support_violation:{i}")
            _, replay_x2 = _factor(alice)
            _, replay_y2 = _factor(bob)
            recomputed_initial = int(np.count_nonzero(replay_x2 != replay_y2))
            if type(rec.get("l2_errors_initial")) is not int or \
                    rec["l2_errors_initial"] != recomputed_initial:
                problems.append(f"l2_initial_error_recompute_mismatch:{i}")
            stored_x2_hat = rec.get("x2_hat")
            accounting = rec.get("l2_error_accounting")
            stored_final = rec.get("l2_errors_final")
            if stored_x2_hat is None:
                if accounting != "candidate_unavailable":
                    problems.append(f"l2_accounting_mode:{i}")
                if type(stored_final) is not int or stored_final != N:
                    problems.append(f"l2_sentinel_mismatch:{i}")
            else:
                if (not isinstance(stored_x2_hat, list) or
                        len(stored_x2_hat) != N or
                        any(type(v) is not int for v in stored_x2_hat)):
                    problems.append(f"l2_x2_hat_invalid:{i}")
                else:
                    replay_x2_hat = np.asarray(stored_x2_hat, dtype=np.int64)
                    if np.any(replay_x2_hat < 0) or np.any(replay_x2_hat >= Q):
                        problems.append(f"l2_x2_hat_range:{i}")
                    recomputed_final = int(np.count_nonzero(replay_x2_hat != replay_x2))
                    if accounting != "measured":
                        problems.append(f"l2_accounting_mode:{i}")
                    if type(stored_final) is not int or stored_final != recomputed_final:
                        problems.append(f"l2_error_recompute_mismatch:{i}")
                    if rec.get("exact_l2") is not (recomputed_final == 0):
                        problems.append(f"l2_exact_recompute_mismatch:{i}")
        except Exception as exc:
            problems.append(f"sampler_replay_error:{i}:{exc}")
        try:
            runtime_s = float(rec.get("runtime_s"))
            if not math.isfinite(runtime_s) or runtime_s < 0:
                problems.append(f"runtime_invalid:{i}")
        except (TypeError, ValueError):
            problems.append(f"runtime_invalid:{i}")
        terminal = rec.get("terminal")
        if terminal not in ("PASS", "FAIL", "INCONCLUSIVE"):
            problems.append(f"terminal_invalid:{i}")
        if terminal == "PASS" and not all(rec.get(k) is True for k in ("exact_l2", "syndrome_ok", "tag_ok")):
            problems.append(f"pass_predicate_mismatch:{i}")
        if terminal == "PASS" and rec.get("false_accept") is not False:
            problems.append(f"pass_false_accept:{i}")
        if terminal == "INCONCLUSIVE" and not rec.get("fatal"):
            problems.append(f"inconclusive_not_fatal:{i}")
        if rec.get("success") != (terminal == "PASS"):
            problems.append(f"success_terminal_mismatch:{i}")
    if len(records) == TOTAL_CALLS:
        wanted = {(x["source"], x["block"], x["seed"]) for x in expected}
        if seen != wanted:
            problems.append("missing_or_extra_calls")
    return problems


def cmd_verify(args) -> int:
    run_root = Path(args.run_root)
    mp = run_root / "audit_manifest.json"
    problems: list[str] = []
    if not mp.is_file():
        print(json.dumps({"verdict": "manifest_missing", "problems": [str(mp)],
                          "records_checked": 0}))
        return EXIT_MANIFEST
    try:
        manifest = _json_load(mp)
    except Exception as exc:
        print(json.dumps({"verdict": "manifest_unparsable", "problems": [str(exc)],
                          "records_checked": 0}))
        return EXIT_MANIFEST
    if not _verify_manifest_digest(manifest):
        problems.append("freeze_digest_mismatch")
    if manifest.get("schema") != MANIFEST_SCHEMA or manifest.get("change") != CHANGE_NAME:
        problems.append("manifest_identity_mismatch")
    if manifest.get("freeze_commit") != FREEZE_COMMIT:
        problems.append("freeze_commit_mismatch")
    if manifest.get("matrix", {}).get("digest") != expected_call_matrix_digest():
        problems.append("matrix_digest_mismatch")
    matrix = manifest.get("matrix") or {}
    if matrix.get("total_calls") != TOTAL_CALLS or matrix.get("threshold") != THRESHOLD or \
            matrix.get("blocks_per_source") != BLOCKS_PER_SOURCE or matrix.get("rng") != RNG_NAME:
        problems.append("matrix_semantics_mismatch")
    decoder = manifest.get("decoder") or {}
    if decoder.get("max_iter") != MAX_ITER or decoder.get("streak") != STREAK or \
            decoder.get("l1_mode") != "oracle" or decoder.get("l1_decoded") is not False:
        problems.append("decoder_semantics_mismatch")
    if manifest.get("numpy_required") != NUMPY_REQUIRED or \
            manifest.get("sampler_reference_id") != "V34-PCG64-REF1":
        problems.append("sampler_semantics_mismatch")
    if manifest.get("claim_boundary") != CLAIM_BOUNDARY or \
            manifest.get("no_resume_no_retry") is not True:
        problems.append("lifecycle_semantics_mismatch")
    if manifest.get("packet", {}).get("m2") != M2:
        problems.append("packet_m2_manifest_mismatch")
    if manifest.get("run_root") != str(run_root):
        problems.append("run_root_mismatch")
    provider = load_runner(args.runner) if args.runner else None
    report, counts = stage0_validate(REPO_ROOT, provider if manifest.get("mode") == "fake" else None)
    if not report.get("ok") or counts is None:
        problems.append("current_binding_failure")
    try:
        records_doc = _json_load(run_root / "block_records.json")
        records = records_doc.get("records") or []
    except Exception as exc:
        records = []
        problems.append(f"records_unparsable:{exc}")
    if counts is not None:
        problems.extend(_verify_records(records, counts, manifest))
    summaries, overall = _aggregate(records)
    try:
        stored_summaries = _json_load(run_root / "source_summaries.json")
        if stored_summaries != summaries:
            # generated summaries are deterministic; reject semantic tampering.
            problems.append("source_summary_recompute_mismatch")
    except Exception as exc:
        problems.append(f"source_summary_unparsable:{exc}")
    try:
        final = _json_load(run_root / "final_state.json")
        if final.get("overall_terminal") != overall or final.get("terminal") != overall:
            problems.append("final_terminal_recompute_mismatch")
        if final.get("freeze_digest_ref") != manifest.get("freeze_digest"):
            problems.append("final_freeze_digest_ref_mismatch")
        if final.get("claim_boundary") != CLAIM_BOUNDARY or final.get("qualification") is not False or final.get("promotion") is not False:
            problems.append("final_claim_boundary_invalid")
    except Exception as exc:
        problems.append(f"final_unparsable:{exc}")
    verdict = "consistent" if not problems else "evidence_inconsistent"
    print(json.dumps({"verdict": verdict, "run_root": str(run_root),
                      "problems": problems, "records_checked": len(records)}, indent=2))
    return EXIT_OK if not problems else EXIT_EVIDENCE_INCONSISTENT


def cmd_prepare(args) -> int:
    """Compatibility wrapper: prepare is stdout-only and never writes."""
    provider = load_runner(args.runner) if getattr(args, "runner", None) else None
    report, _ = stage0_validate(REPO_ROOT, provider)
    print(json.dumps(report, indent=2, sort_keys=True))
    return EXIT_OK if report.get("ok") else EXIT_BLOCKED_BINDING


def cmd_execute(args) -> int:
    """Argument-object wrapper used by focused tests and adjacent tooling."""
    fake = bool(getattr(args, "runner", None))
    if fake:
        provider = load_runner(args.runner)
        return execute_run(REPO_ROOT, Path(args.run_root), provider=provider,
                           fake=True, auth_info={"mechanism": "fake_runner",
                                                 "runner": args.runner})[0]
    auth_path = getattr(args, "execute_auth_file", None)
    if not auth_path:
        return EXIT_UNAUTHORIZED
    auth = _json_load(Path(auth_path))
    rejection = validate_execute_auth(auth)
    if rejection:
        return EXIT_UNAUTHORIZED
    return execute_run(
        REPO_ROOT, Path(getattr(args, "run_root", OFFICIAL_RUN_ROOT)), fake=False,
        auth_info={"mechanism": "auth_file", "path": str(auth_path),
                   "sha256": sha256_file(Path(auth_path)), "payload": auth},
    )[0]


# ---------------------------------------------------------------------------
# Self-check and command line
# ---------------------------------------------------------------------------

def selfcheck() -> int:
    checks = {
        "numpy_version": np.__version__ == NUMPY_REQUIRED,
        "sampler_reference": check_sampler_reference(),
        "matrix_count": len(enumerate_calls()) == TOTAL_CALLS,
        "matrix_unique": len({(x["source"], x["block"], x["seed"]) for x in enumerate_calls()}) == TOTAL_CALLS,
        "source_major": [x["source"] for x in enumerate_calls()] ==
                        [s for s in SOURCE_ORDER for _ in range(BLOCKS_PER_SOURCE)],
        "m2_bound": all(x["m2"] == M2[x["source"]] for x in enumerate_calls()),
        "threshold": THRESHOLD == 19,
        "decoder_schedule": MAX_ITER == 30 and STREAK == 20,
        "no_v28r_m2": all(v not in (194, 200, 202) for v in M2.values()),
        "auth_keys": len(AUTH_KEYS) == 10,
    }
    out = {"ok": all(checks.values()), "checks": checks,
            "call_matrix_digest": expected_call_matrix_digest(),
            "official_run_root_exists": OFFICIAL_RUN_ROOT.exists()}
    print(json.dumps(out, indent=2, sort_keys=True))
    return EXIT_OK if out["ok"] else EXIT_SELFCHECK_FAILED


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=Path(__file__).stem)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--runner")
    v = sub.add_parser("verify")
    v.add_argument("--run-root", required=True)
    v.add_argument("--runner")
    e = sub.add_parser("execute")
    e.add_argument("--run-root", default=str(OFFICIAL_RUN_ROOT))
    e.add_argument("--runner", help="explicit fake runner MODULE:ATTR")
    e.add_argument("--execute-auth-file")
    sub.add_parser("test-selfcheck")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        return cmd_prepare(args)
    if args.command == "test-selfcheck":
        return selfcheck()
    if args.command == "verify":
        return cmd_verify(args)
    try:
        return cmd_execute(args)
    except Exception as exc:
        print(json.dumps({"blocked": "unauthorized", "detail": str(exc)}))
        return EXIT_UNAUTHORIZED


if __name__ == "__main__":
    raise SystemExit(main())
