"""Read-only correction verifier for the NB-LDPC V32 operating-point audit (v2).

OpenSpec change: formal-nonbinary-ldpc-v32-operating-point-audit-correction.

This CLI independently recomputes D0/D1/D2 from raw persisted records with the
corrected semantics of design §3 (C1–C6), rewrites D3 as the definition of an
exact-V31-rate empirical-P ensemble DE question (defined only, never executed),
and mechanically selects a candidate terminal state (design §9 priority over a
C01–C13 checklist).

STRICTLY READ-ONLY over its inputs: no DE run, no decoder invocation, no graph
builder, no finite-control, no raw-data pipeline.  The five old evidence roots,
the archive and the frozen baseline are never modified; every write is confined
to exactly one additive run root (``…_v2/run_01``).  A pre-existing run root is
a collision STOP (no overwrite, no automatic ``run_02``).

Subcommands:

- ``d0``   full failure-signature recomputation from V32 ``per_block.jsonl``
- ``d1``   Q_B1 vs V25 empirical-P support mismatch (analytic + frozen MC)
- ``d2``   dual-law feasibility: empirical_P_budget vs original_Q_B1_budget
- ``d3``   the single next question (definition only)
- ``all``  manifest freeze -> d0 -> d1 -> d2 -> d3 -> corrected_branch_decision

``--runner MODULE:ATTR`` injects an alternative binding provider (test fakes);
the provider object must expose ``binding_paths() -> dict[str, Path]``.

Exit codes: 0 ok; 2 output-root collision; 3 blocked (binding drift / stage-0);
4 evidence inconsistent; 5 manifest missing/drifted/tampered; 6 unsafe write.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------- #
# Frozen constants (identical to the four OpenSpec docs; do not restate elsewh.)
# --------------------------------------------------------------------------- #

REPO_ROOT = Path(__file__).resolve().parents[4]
DIAG = "comparison_bench/outputs_comparison/nonbinary_diagnostics"
V32_DIR = f"{DIAG}/nbldpc_v32_finite_de_bridge/run_01"
OLD_AUDIT_DIR = f"{DIAG}/nbldpc_v32_operating_point_audit/run_01"
V25_DIR = f"{DIAG}/nbldpc_v25_20260818/run_04"
V26_DIR = f"{DIAG}/nbldpc_v26_20260818/run_02"
V31_DIR = f"{DIAG}/nbldpc_v31_20260820/run_01"
DEFAULT_RUN_ROOT = (
    REPO_ROOT / DIAG / "nbldpc_v32_operating_point_audit_v2/run_01"
)

SOURCE_IDS = {
    "1M": "type2_1M_20260121_184040",
    "1p5M": "type2_1p5M_20260121_183806",
    "2M": "type2_2M_20260121_183657",
}
FROZEN_RAW_SER = {
    "1M": 0.239779296875,
    "1p5M": 0.2544695292735815,
    "2M": 0.2557409550754458,
}
N_SYMBOLS = 1024
Q_SYMBOLS = 1024
BITS_PER_GF32 = 5.0  # log2(32) bits per GF(32) syndrome symbol

EXPECTED_COUNTS = {"B5": 1, "B0": 6, "B1": 60, "B2": 60, "B3": 60, "B4": 60}
PER_BLOCK_SCHEMA = "nbldpc_v32_bridge_block_result_v1"

# Thresholds preregistered BEFORE any computation (design §2 manifest freeze).
THRESHOLDS = {
    "expected_nll_ratio_K": 3.0,
    "expected_nll_ratio_derivation": (
        "Anchored to log2(1024)=10 bits/symbol uniform-symmetry bound. The "
        "self-NLL baseline is the V31 reference conditional entropy sum "
        "H.L1+H.L2 <= 0.833 bits/symbol; K=3 places the catastrophic-mismatch "
        "line at ~2.50 bits/symbol, far above plug-in estimation noise "
        "(< 0.05 bits) and far below the 10 bits/symbol uniform bound."
    ),
    "support_miss_fraction_max": 0.01,
    "support_miss_fraction_derivation": (
        "With n=1024 symbols per frame, a per-symbol support-miss probability "
        "of 1% gives P(at least one miss per frame) = 1-(1-0.01)^1024 ~= 1.0: "
        "every long frame would hit a P-zero posterior cell. Anchored to the "
        "frozen n=1024 frame length."
    ),
}

MC_PLAN = {
    "seed": 20260822,
    "n_samples": 100000,
    "quantiles": [0.05, 0.5, 0.95],
    "zero_hit_policy": (
        "samples whose true-symbol posterior cell has probability zero are "
        "counted separately; finite statistics are computed over non-hit "
        "samples only"
    ),
}

# Histogram bin edges frozen BEFORE execution; identical to the old v1 audit
# run_01 audit_manifest.frozen.histogram_bins (error-delta integer edges and
# log2 bits/symbol edges). Declared here once; never tuned afterwards.
DELTA_BIN_EDGES = list(range(-1024, 1025, 64))
LOG2_EDGES_BITS_PER_SYMBOL = [float(2 ** e) for e in range(-20, 7)]

MARGIN_METHOD = (
    "simple gap reporting at n=1024 only: gap_bits = leakage_bits - "
    "required_bits per layer and total, plus leakage/required ratio; no "
    "normal approximation and no other statistics"
)
H_CROSS_CHECK_TOL_BITS = 1e-6

LIFECYCLE_NOTE = [
    "post_hoc_exploratory_only",
    "not_formal_pre_registered_gate",
    "numerical_outputs_retained",
    "scientific_terminal_superseded_pending_correction",
]

TERMINAL_CORRECTED = "audit_corrected_rate_aligned_de_required"
TERMINAL_INCONSISTENT = "audit_evidence_inconsistent"
TERMINAL_BLOCKED = "audit_verifier_blocked"
TERMINAL_PRIORITY = [TERMINAL_INCONSISTENT, TERMINAL_BLOCKED, TERMINAL_CORRECTED]

FORBIDDEN_CONCLUSION_STRINGS = [
    "finite_graph_decoder_mismatch",
    "QC graph confirmed failure",
    "decoder confirmed failure",
    "NB-Polar preferred",
    "qualification-ready",
    "promotion-ready",
    "deployment-ready",
]
SCAN_SCOPE_FILES = [  # forbidden-string scan scope: v2 analysis outputs only
    "d0_failure_signature.json", "d1_support_mismatch.json",
    "d2_dual_law_feasibility.json", "d3_next_question.json",
    "corrected_branch_decision.json",
]  # audit_manifest.json excluded: lifecycle context may cite the distrusted old terminal

OUTPUT_FILES_EIGHT = [
    "audit_manifest.json", "d0_failure_signature.json", "d1_support_mismatch.json",
    "d2_dual_law_feasibility.json", "d3_next_question.json",
    "corrected_branch_decision.json", "readonly_review.json", "operator_handoff.md",
]

D3_QUESTION = (
    "在 V25 empirical joint P(A,B)、F03/A02 分配和 V31 实际层率下，对应 ensemble DE "
    "是否在三源、两层全部收敛？"
)
LAYER_RATE_TABLE_FROZEN = {
    "L1": {"1M": 0.984375, "1p5M": 0.984375, "2M": 0.984375},
    "L2": {"1M": 0.8203125, "1p5M": 0.814453125, "2M": 0.8125},
}
ALLOCATION_ID = "m1_16_n1024"  # registry entries MUST be filtered by allocation
PACKET_ID = "m1_16_n1024_n1024|QC-cyclic-projective"

# Old v1 audit numbers retained read-only as comparison columns only; never a
# trusted source, never rewritten, never silently aligned (design §5).
OLD_AUDIT_REFERENCE = {
    "q_mass_on_p_zero_cells": {"1M": 0.239468, "1p5M": 0.254127, "2M": 0.255348},
    "mc_conditional_mean_bits_per_symbol_approx_range": [0.397, 0.431],
    "truncated_common_support_cross_entropy_bits_approx_range": [7.77, 7.91],
}

NAMING_RULES = {
    "rule": "three distinct quantities with non-interchangeable names (C4)",
    "full_expected_nll": (
        'complete E_Q[-log2 P]; the string "infinity" iff q_mass_on_p_zero_cells '
        '> 0 (positive Q mass sits on cells with log2(P) = -infinity); '
        'otherwise the JSON-safe finite analytic value'
    ),
    "conditional_finite_support_mean": (
        "seeded MC mean over non-hit samples only (posterior cell nonzero); "
        "never call it full NLL"
    ),
    "truncated_common_support_cross_entropy": (
        "cross entropy summed over common-support cells only (P>0); never "
        "call it full cross entropy"
    ),
}

FULL_EXPECTED_NLL_DERIVATION = (
    "E_Q[-log2 P] = infinity because positive Q mass (q_mass_on_p_zero_cells "
    "> 0) sits on cells where log2(P) = log2(0) = -infinity, so the sum "
    "contains mass * (-infinity) summed negatively to -infinity."
)
ZERO_MASS_FULL_NLL_DERIVATION = (
    "q_mass_on_p_zero_cells == 0: Q places no mass on P-zero cells, so "
    "E_Q[-log2 P] is finite and equals its analytic value over the common "
    "support (reported as a JSON-safe number; minimal representation chosen "
    "in the verifier-fix handoff because the frozen schema specifies no "
    "zero-mass literal)"
)
Q_B1_INFEASIBLE_CONCLUSION = (
    "information-theoretically infeasible at current allocation"
)
CONCLUSION_SCOPE_NOMINAL = (
    "nominal information budget feasible only — no finite-length/DE/"
    "fixed-graph/decoder feasibility claim"
)
Q_B1_DE_NOTE = (
    "不需要也不应该对 Q_B1 运行 DE：信息论不可行时 DE 无意义。"
)

EXIT_OK = 0
EXIT_COLLISION = 2
EXIT_BLOCKED = 3
EXIT_EVIDENCE = 4
EXIT_MANIFEST = 5
EXIT_WRITE = 6


class AuditStop(Exception):
    """Frozen-scope stop with a distinct process exit code."""

    def __init__(self, code: int, reason: str):
        super().__init__(reason)
        self.code = int(code)
        self.reason = str(reason)


# --------------------------------------------------------------------------- #
# Safe writes + digests
# --------------------------------------------------------------------------- #

def _safe_path(run_root: Path, name: str) -> Path:
    root = Path(run_root).resolve()
    p = (root / name).resolve()
    if p.parent != root or "/" in name or "\\" in name:
        raise AuditStop(EXIT_WRITE, f"write outside run root rejected: {name!r}")
    return p


def _write_json(run_root: Path, name: str, obj) -> None:
    p = _safe_path(run_root, name)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_canonical(obj) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def git_head() -> str:
    """Current Git HEAD of the repository hosting this CLI."""
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT),
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise AuditStop(EXIT_BLOCKED, f"cannot resolve git HEAD: {proc.stderr.strip()}")
    return proc.stdout.strip()


# --------------------------------------------------------------------------- #
# Runner contract + default repo bindings
# --------------------------------------------------------------------------- #

class RepoBindings:
    """Default binding provider: resolves frozen repository paths read-only."""

    def binding_paths(self) -> dict[str, Path]:
        paths = {}
        # R1: V32 bridge run_01
        paths["v32_per_block"] = REPO_ROOT / V32_DIR / "per_block.jsonl"
        paths["v32_run_manifest"] = REPO_ROOT / V32_DIR / "RUN_MANIFEST.json"
        for b in range(6):
            paths[f"v32_summary_B{b}"] = REPO_ROOT / V32_DIR / f"summary_B{b}.json"
        paths["v32_candidate_terminal"] = REPO_ROOT / V32_DIR / "candidate_terminal.json"
        # R2: old audit run_01 ten files (existence + hash identity ONLY;
        # their numeric content is never a trusted source).
        for n in ("audit_manifest", "d0_signature", "d1_consistency", "d2_feasibility",
                  "d3_v26_evidence"):
            paths[f"oldaudit_{n}_json"] = REPO_ROOT / OLD_AUDIT_DIR / f"{n}.json"
        for n in ("d0_signature", "d1_consistency", "d2_feasibility", "d3_v26_evidence"):
            paths[f"oldaudit_{n}_md"] = REPO_ROOT / OLD_AUDIT_DIR / f"{n}.md"
        paths["oldaudit_final_branch_decision"] = (
            REPO_ROOT / OLD_AUDIT_DIR / "final_branch_decision.json")
        # R3/R4: V25 counts + summary + split
        paths["v25_channel_counts"] = REPO_ROOT / V25_DIR / "channel_counts.npz"
        paths["v25_channel_summary"] = REPO_ROOT / V25_DIR / "channel_summary.json"
        paths["v25_split_manifest"] = REPO_ROOT / V25_DIR / "split_manifest.json"
        # R5: V26 DE history (read-only historical comparison only)
        for n in ("gate", "RUN_MANIFEST", "screen_results", "confirmation_results"):
            paths[f"v26_{n}"] = REPO_ROOT / V26_DIR / f"{n}.json"
        # R6/R7: V31 manifest + matrix audits + m1 registry
        for n in ("RUN_MANIFEST", "matrix_audits", "m1_registry"):
            paths[f"v31_{n}"] = REPO_ROOT / V31_DIR / f"{n}.json"
        return paths


def load_runner(spec: str | None):
    if not spec:
        return RepoBindings()
    module_name, attr = spec.split(":", 1)
    obj = importlib.import_module(module_name)
    for part in attr.split("."):
        obj = getattr(obj, part)
    return obj() if callable(obj) else obj  # class or zero-arg factory


# --------------------------------------------------------------------------- #
# Loaders
# --------------------------------------------------------------------------- #

def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    recs = []
    text = Path(path).read_text(encoding="utf-8")
    for i, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise AuditStop(EXIT_EVIDENCE,
                            f"truncated/malformed JSONL at {path} line {i}: {exc}")
    return recs


def load_counts_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path) as z:
        return {k: np.asarray(z[k], dtype=np.float64) for k in z.files}


# --------------------------------------------------------------------------- #
# Stage 0 — seven-binding verification (existence + SHA256 + literal values)
# --------------------------------------------------------------------------- #

def stage0_bindings(paths: dict[str, Path]) -> tuple[list[dict], dict]:
    rows = []
    for name in sorted(paths):
        p = Path(paths[name])
        if not p.is_file():
            raise AuditStop(EXIT_BLOCKED, f"binding missing: {name}: {p}")
        rows.append({
            "binding": name,
            "path": str(p),
            "size_bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        })

    # R1: per_block.jsonl has exactly 247 records.
    n_lines = sum(1 for ln in Path(paths["v32_per_block"]).read_text(
        encoding="utf-8").splitlines() if ln.strip())
    if n_lines != 247:
        raise AuditStop(EXIT_BLOCKED, f"R1 per_block.jsonl record count drift: {n_lines} != 247")

    # Persisted terminal read as DISTRUSTED: recorded only to state that its
    # attribution is not accepted; its value never enters the v2 reasoning chain.
    term = load_json(paths["v32_candidate_terminal"])
    distrust_record = {
        "file": str(paths["v32_candidate_terminal"]),
        "recorded_value": term.get("terminal"),
        "status": "read_as_distrusted_not_accepted",
        "note": ("persisted terminal of the superseded v1 chain; never used as a v2 "
                 "conclusion and never emitted as one"),
    }

    # R3: verbatim npz keys (duplicated suffix is part of the on-disk name).
    counts = load_counts_npz(paths["v25_channel_counts"])
    expected_keys = {f"{sid}_N_ab_train_N_ab_train" for sid in SOURCE_IDS.values()}
    if set(counts.keys()) != expected_keys:
        raise AuditStop(EXIT_BLOCKED, f"npz keys drift: got {sorted(counts.keys())}")
    for k in expected_keys:
        if counts[k].shape != (Q_SYMBOLS, Q_SYMBOLS) or counts[k].sum() <= 0:
            raise AuditStop(EXIT_BLOCKED, f"npz array shape/mass drift for key {k}")

    # R4: frozen raw_ser values quoted verbatim from channel_summary.json.
    summary = load_json(paths["v25_channel_summary"])
    for label, sid in SOURCE_IDS.items():
        row = summary.get("per_source", {}).get(sid, {})
        if row.get("ser") != FROZEN_RAW_SER[label]:  # exact match on frozen value
            raise AuditStop(EXIT_BLOCKED, f"frozen raw_ser drift for {label}: {row.get('ser')!r}")
        if "pm1_mass" not in row:
            raise AuditStop(EXIT_BLOCKED, f"pm1_mass field missing for {label}")

    # R5: V26 gate identity (historical comparison only).
    gate = load_json(paths["v26_gate"])
    if gate.get("status") != "pass_target_f13":
        raise AuditStop(EXIT_BLOCKED, f"V26 gate status drift: {gate.get('status')!r}")
    bpf = gate.get("best_passing_f") or {}
    if bpf.get("A01") != 1.6 or bpf.get("A02") != 1.3:
        raise AuditStop(EXIT_BLOCKED, f"V26 best_passing_f drift: {bpf!r}")
    if "design_constants" not in load_json(paths["v26_RUN_MANIFEST"]):
        raise AuditStop(EXIT_BLOCKED, "V26 RUN_MANIFEST.design_constants missing")

    # R6: V31 allocation/leakage identities per source label.
    v31 = load_json(paths["v31_RUN_MANIFEST"])
    cfg = v31.get("configs", {}).get("1024", {})
    m2_expect = {"1M": 184, "1p5M": 190, "2M": 192}
    leak_expect = {"1M": 1064, "1p5M": 1094, "2M": 1104}
    for label, row in cfg.get("sources", {}).items():
        if row.get("m1") != 16:
            raise AuditStop(EXIT_BLOCKED, f"V31 m1 drift for {label}: {row.get('m1')!r}")
        if row.get("m2") != m2_expect[label]:
            raise AuditStop(EXIT_BLOCKED, f"V31 m2 drift for {label}: {row.get('m2')!r}")
        if row.get("m_total") != m2_expect[label] + 16:
            raise AuditStop(EXIT_BLOCKED, f"V31 m_total drift for {label}: {row.get('m_total')!r}")
        if row.get("leak_total_bits") != leak_expect[label]:
            raise AuditStop(EXIT_BLOCKED,
                            f"V31 leak_total_bits drift for {label}: {row.get('leak_total_bits')!r}")
        h = row.get("H") or {}
        if not (isinstance(h.get("L1"), (int, float)) and isinstance(h.get("L2"), (int, float))
                and h["L1"] > 0 and h["L2"] > 0 and row.get("f_total") is not None):
            raise AuditStop(EXIT_BLOCKED, f"V31 H/f_total fields missing for {label}")

    # R7: packet identity + layer rates, filtered by allocation id.
    audits = load_json(paths["v31_matrix_audits"])
    packets = [p for p in audits.get("packets", []) if p.get("packet_id") == PACKET_ID]
    if not packets:
        raise AuditStop(EXIT_BLOCKED, f"V31 matrix_audits packet_id drift: {PACKET_ID!r} absent")
    pkt = packets[0]
    if pkt.get("audits", {}).get("L1", {}).get("shape") != [16, Q_SYMBOLS]:
        raise AuditStop(EXIT_BLOCKED, "V31 matrix_audits packet L1 shape drift")

    registry_calls = load_json(paths["v31_m1_registry"]).get("registered_calls", [])
    # Filter by allocation first: the same file also contains other allocations
    # (e.g. n2048); a full-table scan comparison is FORBIDDEN (design §2 R7).
    alloc_calls = [c for c in registry_calls if c.get("allocation_id") == ALLOCATION_ID]
    if not alloc_calls:
        raise AuditStop(EXIT_BLOCKED, f"no m1_registry entries for allocation {ALLOCATION_ID}")
    combos = {(c.get("layer"), c.get("source")) for c in alloc_calls}
    need = {(layer, src) for layer in LAYER_RATE_TABLE_FROZEN for src in SOURCE_IDS}
    if not need.issubset(combos):
        raise AuditStop(EXIT_BLOCKED, f"registry allocation entries incomplete: {sorted(combos)}")
    for c in alloc_calls:
        expect = LAYER_RATE_TABLE_FROZEN[c["layer"]][c["source"]]
        if c.get("rate") != expect:
            raise AuditStop(EXIT_BLOCKED,
                            f"registry rate drift for {c['layer']}/{c['source']}: "
                            f"{c.get('rate')!r} != {expect!r}")

    return rows, {"persisted_terminal_distrust": distrust_record}


# --------------------------------------------------------------------------- #
# Manifest freeze / verify (frozen BEFORE any computation)
# --------------------------------------------------------------------------- #

MANIFEST_NAME = "audit_manifest.json"
MANIFEST_SCHEMA = "nbldpc_v32_operating_point_audit_correction_manifest_v1"
CLI_PATH = Path(__file__).resolve()


def _expected_frozen() -> dict:
    """The frozen block, rebuilt from module constants (fix task D): lets
    verify_manifest catch a frozen-field tamper even when the tamperer also
    recomputes freeze_digest."""
    return {
        "thresholds": THRESHOLDS,
        "mc_plan": MC_PLAN,
        "histogram_bins": {
            "error_delta_bin_edges": DELTA_BIN_EDGES,
            "log2_edges_bits_per_symbol": LOG2_EDGES_BITS_PER_SYMBOL,
        },
        "margin_method": MARGIN_METHOD,
        "h_cross_check_tol_bits": H_CROSS_CHECK_TOL_BITS,
    }


def freeze_manifest(run_root: Path, binding_rows: list[dict], extras: dict) -> dict:
    frozen = _expected_frozen()
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "execution_order": ["manifest_freeze", "d0", "d1", "d2", "d3",
                            "corrected_branch_decision"],
        "bindings": binding_rows,
        "lifecycle_note": list(LIFECYCLE_NOTE),
        "no_de_run": True,
        "no_decoder_run": True,
        "old_roots_read_only": True,
        "git_head": git_head(),
        "implementation_identity": {"path": str(CLI_PATH), "sha256": sha256_file(CLI_PATH)},
        "output_files_expected_eight": OUTPUT_FILES_EIGHT,
        **extras,
        "frozen": frozen,
        "freeze_digest": None,
    }
    manifest["freeze_digest"] = sha256_canonical(frozen)
    _write_json(run_root, MANIFEST_NAME, manifest)
    return manifest


def verify_manifest(run_root: Path, runner) -> dict:
    mpath = Path(run_root) / MANIFEST_NAME
    if not mpath.is_file():
        raise AuditStop(EXIT_MANIFEST, f"frozen manifest missing: {mpath} (run `all` first)")
    manifest = load_json(mpath)

    # Fix task D: field-level guards on the frozen acceptance semantics.
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise AuditStop(EXIT_MANIFEST,
                        f"manifest schema drift: {manifest.get('schema')!r}")
    if manifest.get("lifecycle_note") != list(LIFECYCLE_NOTE):
        raise AuditStop(EXIT_MANIFEST, "manifest lifecycle_note tampered")
    for flag in ("no_de_run", "no_decoder_run", "old_roots_read_only"):
        if manifest.get(flag) is not True:
            raise AuditStop(EXIT_MANIFEST, f"manifest flag tampered: {flag} is not true")
    ident = manifest.get("implementation_identity")
    if not (isinstance(ident, dict)
            and isinstance(ident.get("path"), str) and ident["path"]
            and isinstance(ident.get("sha256"), str)
            and len(ident["sha256"]) == 64):
        raise AuditStop(EXIT_MANIFEST,
                        "manifest implementation_identity missing/malformed")
    # Time binding: implementation_identity/git_head bind the EXECUTION-time
    # commit and CLI file.  They are recorded verbatim above but are NEVER
    # compared against the CURRENT HEAD or the current CLI file, both of which
    # legitimately move on afterwards (fix task D).
    gh = manifest.get("git_head")
    if not (isinstance(gh, str) and len(gh) == 40):
        raise AuditStop(EXIT_MANIFEST, "manifest git_head missing/malformed")
    if manifest.get("output_files_expected_eight") != OUTPUT_FILES_EIGHT:
        raise AuditStop(EXIT_MANIFEST, "manifest expected-output file list tampered")

    frozen = manifest.get("frozen")
    if frozen != _expected_frozen():
        raise AuditStop(EXIT_MANIFEST,
                        "manifest frozen-block content drift vs module constants")
    if manifest.get("freeze_digest") != sha256_canonical(frozen):
        raise AuditStop(EXIT_MANIFEST,
                        "manifest freeze digest mismatch: thresholds/MC plan/bins/"
                        "margin method drifted")
    current = runner.binding_paths()
    for row in manifest.get("bindings", []):
        name = row["binding"]
        p = current.get(name)
        if p is None or not Path(p).is_file():
            raise AuditStop(EXIT_BLOCKED, f"input drift: binding {name} missing ({p})")
        if sha256_file(Path(p)) != row["sha256"]:
            raise AuditStop(EXIT_BLOCKED, f"input drift detected on {name}: {p}")
    return manifest


# --------------------------------------------------------------------------- #
# F03/A02 layer maps + entropies + Q_B1 law (inline; no production imports)
# --------------------------------------------------------------------------- #

def split_f03(a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """F03_natural_MSB_to_LSB_GF32_plus_GF32: U1 = top 5 bits, U2 = low 5 bits."""
    v = np.asarray(a, dtype=np.int64) & 0x3FF
    return v >> 5, v & 31


def joint_entropy_bits(counts: np.ndarray) -> float:
    tot = float(np.sum(counts))
    if tot <= 0:
        return 0.0
    p = counts.ravel().astype(np.float64)
    p = p[p > 0] / tot
    return float(-np.sum(p * np.log2(p)))


def _vec_entropy(p: np.ndarray) -> float:
    q = p.astype(np.float64)
    q = q[q > 0]
    s = q.sum()
    if s <= 0:
        return 0.0
    q = q / s
    return float(-np.sum(q * np.log2(q)))


def _cond_entropy_rows(N: np.ndarray, col: np.ndarray) -> float:
    tot = float(N.sum())
    if tot <= 0:
        return 0.0
    h = 0.0
    for b in range(Q_SYMBOLS):
        cb = float(col[b])
        if cb <= 0:
            continue
        p_col = cb / tot
        p_row = N[:, b] / cb
        nz = p_row[p_row > 0]
        h += p_col * float(-np.sum(nz * np.log2(nz)))
    return h


def layer_entropies(N: np.ndarray) -> dict:
    """H(U1|B), H(U2|B,U1), H(A|B) in bits via the F03/A02 maps.

    Chain rule on joint counts: H(U_i | B, U_<i) = H(B, U_<i, U_i) - H(B, U_<i).
    """
    N3 = N.reshape(32, 32, Q_SYMBOLS)  # [u1, u2, b] because a = 32*u1 + u2
    h_b = _vec_entropy(N.sum(axis=0))
    h_u1_b = joint_entropy_bits(N3.sum(axis=1))       # H(B,U1)
    h_b_u1_u2 = joint_entropy_bits(N3)                # H(B,U1,U2)
    h_l1 = h_u1_b - h_b
    h_l2 = h_b_u1_u2 - h_u1_b
    col = N.sum(axis=0)
    h_ab = _cond_entropy_rows(N, col)
    return {"H_U1_given_B_bits": float(h_l1), "H_U2_given_B_U1_bits": float(h_l2),
            "H_A_given_B_bits": float(h_ab), "chain_rule_total_bits": float(h_l1 + h_l2)}


def build_q_joint(ser: float) -> np.ndarray:
    """Q_B1(b|a) = (1-ser)*delta_{b=a} + ser*Uniform{b != a mod 1024}, joint form."""
    q = np.full((Q_SYMBOLS, Q_SYMBOLS), ser / ((Q_SYMBOLS - 1) * Q_SYMBOLS),
                dtype=np.float64)
    np.fill_diagonal(q, (1.0 - ser) / Q_SYMBOLS)
    return q


def _layer_posteriors(pab: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """From P(a|b): P(U1|B) [32,1024] and P(U2|B,U1) [32,32,1024]."""
    p3 = pab.reshape(32, 32, Q_SYMBOLS)          # [u1, u2, b]
    p_u1_b = p3.sum(axis=1)                       # P(U1=u1|B)
    with np.errstate(divide="ignore", invalid="ignore"):
        p_u2_b_u1 = np.divide(p3, p_u1_b[:, None, :],
                              out=np.zeros_like(p3), where=p_u1_b[:, None, :] > 0)
    return p_u1_b, p_u2_b_u1


def _nll_maps(pab: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-(a,b) NLL (bits/symbol) of the true layer symbols under P posteriors."""
    p_u1_b, p_u2_b_u1 = _layer_posteriors(pab)
    u1 = (np.arange(Q_SYMBOLS) >> 5)[:, None]
    u2 = (np.arange(Q_SYMBOLS) & 31)[:, None]
    cols = np.arange(Q_SYMBOLS)[None, :]
    with np.errstate(divide="ignore"):
        nll1 = -np.log2(p_u1_b[u1, cols])   # [a,b]
        nll2 = -np.log2(p_u2_b_u1[u1, u2, cols])
    return nll1, nll2


def h2(x: float) -> float:
    return float(-x * math.log2(x) - (1.0 - x) * math.log2(1.0 - x))


# --------------------------------------------------------------------------- #
# D0 — full failure signature (corrected semantics)
# --------------------------------------------------------------------------- #

D0_EXTRACT_FIELDS = [
    "l1_errors_initial", "l1_errors_final", "l2_errors_initial", "l2_errors_final",
    "terminal_decoder_status", "l1_decoder_status_verbatim", "iterations",
    "unsatisfied_checks", "posterior_nll", "posterior_entropy", "truth_symbol_rank",
    "calibration_bucket", "posterior_anomaly_block", "syndrome", "exact", "tag",
    "false_accept", "success",
]


def _agg(values: list[float]) -> dict:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return {"n": 0}
    return {
        "n": int(arr.size),
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "min": float(arr.min()),
        "max": float(arr.max()),
    }


def _hist(values: list[float], edges: list[float]) -> dict:
    counts, _ = np.histogram(np.asarray(values, dtype=np.float64), bins=np.asarray(edges))
    return {"bin_edges": edges, "counts": [int(c) for c in counts]}


def check_d0_predicates(records_by_arm: dict[str, list[dict]]) -> dict:
    violations = {"P_i": [], "P_ii": [], "P_iii": []}
    for r in records_by_arm.get("B1", []):
        if not (r["l2_errors_final"] > r["l2_errors_initial"] and r["posterior_anomaly_block"]):
            violations["P_i"].append(r["block_uid"])
    for r in records_by_arm.get("B2", []):
        if not (r["l2_errors_final"] == 1024 and r["terminal_decoder_status"] == "not_run"):
            violations["P_ii"].append(r["block_uid"])
    for arm in ("B3", "B4"):
        for r in records_by_arm.get(arm, []):
            if not (r["l2_errors_final"] < r["l2_errors_initial"]
                    and r["syndrome"] is False and r["exact"] is False):
                violations["P_iii"].append(r["block_uid"])
    predicates = {
        "P-i_B1_active_divergence_observation": {
            "passed": not violations["P_i"],
            "violating_block_uids": violations["P_i"],
            "attribution_note": (
                "observation stands (if passed) but attribution to the fixed QC graph "
                "or decoder is BARRED by C1: B1 samples follow generator law Q_B1 while "
                "the posterior follows the V25 empirical joint P(A,B)"
            ),
        },
        "P-ii_B2_sentinel_not_run": {
            "passed": not violations["P_ii"],
            "violating_block_uids": violations["P_ii"],
            "attribution_note": (
                "l2_errors_final==1024 with terminal_decoder_status=='not_run' is the "
                "not-run sentinel (L1 failed -> L2 never ran, x2_hat does not exist); "
                "it is NOT divergence evidence (C2)"
            ),
        },
        "P-iii_B3B4_improve_but_no_syndrome": {
            "passed": not violations["P_iii"],
            "violating_block_uids": violations["P_iii"],
            "attribution_note": (
                "improve-but-no-syndrome semantics per C3; the word 'divergent' is "
                "never applied to B3/B4"
            ),
        },
    }
    return {"predicates": predicates,
            "signature_mismatch": any(v["violating_block_uids"] for v in predicates.values())}


def run_d0(run_root: Path, paths: dict[str, Path], frozen: dict) -> dict:
    records = load_jsonl(paths["v32_per_block"])

    seen: set[str] = set()
    dupes = []
    for r in records:
        uid = r.get("block_uid")
        if uid in seen:
            dupes.append(uid)
        seen.add(uid)
    if dupes:
        raise AuditStop(EXIT_EVIDENCE,
                        f"duplicate block_uid (evidence inconsistency): {dupes[:5]}")

    by_arm: dict[str, list[dict]] = {}
    schema_bad = [r.get("schema") for r in records if r.get("schema") != PER_BLOCK_SCHEMA]
    if schema_bad:
        raise AuditStop(EXIT_EVIDENCE, f"per_block schema drift: {schema_bad[:3]}")
    for r in records:
        by_arm.setdefault(r.get("arm"), []).append(r)  # parse strictly by arm field

    counts = {arm: len(by_arm.get(arm, [])) for arm in EXPECTED_COUNTS}
    if counts != EXPECTED_COUNTS:
        raise AuditStop(EXIT_EVIDENCE, f"arm record-count mismatch: {counts} vs {EXPECTED_COUNTS}")

    b5 = by_arm["B5"][0]
    b5_report = {
        "block_uid": b5.get("block_uid"), "kind": b5.get("kind"),
        "imported_records": b5.get("imported_records"),
        "integrity_ok": b5.get("integrity_ok"),
        "per_source_counts": b5.get("per_source_counts"),
    }

    extracted: dict[str, list[dict]] = {}
    for arm in ("B0", "B1", "B2", "B3", "B4"):
        rows = []
        for r in by_arm[arm]:
            missing = [f for f in D0_EXTRACT_FIELDS if f not in r]
            rs = r.get("residual_syndrome_stats") or {}
            if missing or "l1_residual_checks" not in rs or "l2_residual_checks" not in rs:
                raise AuditStop(EXIT_EVIDENCE,
                                f"decode record {r.get('block_uid')} missing fields "
                                f"{missing or ['residual_syndrome_stats.*']}")
            row = {f: r[f] for f in D0_EXTRACT_FIELDS}
            row.update({"block_uid": r.get("block_uid"), "source": r.get("source"),
                        "l1_residual_checks": rs.get("l1_residual_checks"),
                        "l2_residual_checks": rs.get("l2_residual_checks")})
            rows.append(row)
        extracted[arm] = rows

    delta_edges = frozen["histogram_bins"]["error_delta_bin_edges"]
    log_edges = frozen["histogram_bins"]["log2_edges_bits_per_symbol"]
    numeric_fields = [
        "l1_errors_initial", "l1_errors_final", "l2_errors_initial", "l2_errors_final",
        "iterations", "unsatisfied_checks", "posterior_nll", "posterior_entropy",
        "truth_symbol_rank",
    ]

    # B2 is EXCLUDED from trajectory/divergence statistics entirely (C2): it is
    # reported only as sentinel counts + status fields, in its own section.
    aggregation = {}
    for arm in ("B0", "B1", "B3", "B4"):
        for src in ("1M", "1p5M", "2M"):
            rows = [r for r in extracted[arm] if r["source"] == src]
            if not rows:
                continue
            entry = {"n_records": len(rows)}
            for f in numeric_fields:
                vals = [r[f] for r in rows]
                entry[f] = _agg(vals)
                if f in ("posterior_nll", "posterior_entropy"):  # units rule: both forms
                    entry[f + "_bits_per_symbol"] = _agg([v / N_SYMBOLS for v in vals])
            entry["l1_error_delta_histogram"] = _hist(
                [r["l1_errors_final"] - r["l1_errors_initial"] for r in rows], delta_edges)
            entry["l2_error_delta_histogram"] = _hist(
                [r["l2_errors_final"] - r["l2_errors_initial"] for r in rows], delta_edges)
            entry["posterior_nll_bits_per_symbol_histogram"] = _hist(
                [r["posterior_nll"] / N_SYMBOLS for r in rows], log_edges)
            entry["posterior_entropy_bits_per_symbol_histogram"] = _hist(
                [r["posterior_entropy"] / N_SYMBOLS for r in rows], log_edges)
            aggregation[f"{arm}|{src}"] = entry

    b2_rows = extracted["B2"]

    def _is_sentinel(r: dict) -> bool:
        return r["l2_errors_final"] == 1024 and r["terminal_decoder_status"] == "not_run"

    b2_sentinel = {
        "excluded_from_trajectory_and_divergence_stats": True,
        "sentinel_definition": (
            "l2_errors_final==1024 AND terminal_decoder_status=='not_run': L1 failed "
            "so L2 never ran and x2_hat does not exist (C2)"
        ),
        "per_source": {
            src: {
                "n_records": sum(1 for r in b2_rows if r["source"] == src),
                "sentinel_count": sum(1 for r in b2_rows
                                      if r["source"] == src and _is_sentinel(r)),
            } for src in ("1M", "1p5M", "2M")
        },
        "total_sentinel_count": sum(1 for r in b2_rows if _is_sentinel(r)),
        "distinct_terminal_decoder_status": sorted({r["terminal_decoder_status"]
                                                    for r in b2_rows}),
        "distinct_l1_decoder_status_verbatim": sorted({str(r["l1_decoder_status_verbatim"])
                                                       for r in b2_rows}),
    }

    predicates = check_d0_predicates(extracted)

    result = {
        "schema": "nbldpc_v32_operating_point_audit_correction_d0_v1",
        "records_total": len(records),
        "parsing_rule": "records grouped strictly by the per-record 'arm' field; no line-number addressing",
        "arm_record_counts": counts,
        "duplicate_block_uids": [],
        "b5_import_control": b5_report,
        "extracted_fields_per_decode_record": D0_EXTRACT_FIELDS + [
            "residual_syndrome_stats.l1_residual_checks",
            "residual_syndrome_stats.l2_residual_checks"],
        "units_rule": ("posterior_nll/posterior_entropy reported raw (per block of "
                       "n=1024) and as bits/symbol; comparisons against reference "
                       "entropies use bits/symbol only"),
        "aggregation_arm_x_source": aggregation,
        "b2_sentinel": b2_sentinel,
        "semantic_labels": {
            "B1": "active divergence observation; attribution barred by C1 (generator/posterior law mismatch)",
            "B2": "not-run sentinel only (C2); excluded from trajectory/divergence statistics",
            "B3": "improve-but-no-syndrome (C3); trapping-like/finite-redundancy wording only",
            "B4": "improve-but-no-syndrome (C3); trapping-like/finite-redundancy wording only",
        },
        "full_population_rule": ("every conclusion rests on full-population counts/"
                                 "distributions above; single-sample anecdotes are "
                                 "forbidden as evidence"),
        **predicates,
    }
    _write_json(run_root, "d0_failure_signature.json", result)
    return result


# --------------------------------------------------------------------------- #
# D1 — Q_B1 vs V25 empirical-P support mismatch (corrected naming)
# --------------------------------------------------------------------------- #

def run_d1(run_root: Path, paths: dict[str, Path], frozen: dict) -> dict:
    counts = load_counts_npz(paths["v25_channel_counts"])
    mc = frozen["mc_plan"]

    rng = np.random.default_rng(mc["seed"])  # single stream, fixed source order
    per_source = {}
    for label, sid in SOURCE_IDS.items():    # fixed order: 1M, 1p5M, 2M
        N = counts[f"{sid}_N_ab_train_N_ab_train"]
        total = float(N.sum())
        P = N / total
        ser = FROZEN_RAW_SER[label]          # stage-0 verified == channel_summary value
        Q_joint = build_q_joint(ser)

        mass = float(Q_joint.sum())
        if abs(mass - 1.0) > 1e-12:
            raise AuditStop(EXIT_EVIDENCE, f"Q_B1 mass conservation violated for {label}: {mass}")

        mask_p = P > 0
        q_on_p_zero = float(Q_joint[~mask_p].sum())   # analytic sum, NOT MC
        p_on_q_zero = float(P[Q_joint <= 0].sum())

        # Truncated common-support cross entropy (C4-named quantity).
        h_qp_truncated = float(-(Q_joint[mask_p] * np.log2(P[mask_p])).sum())

        # Fix B (blocking): "infinity" is legal ONLY when positive Q mass sits
        # on P-zero cells; otherwise E_Q[-log2 P] is finite and equals the
        # analytic expectation over the common support exactly (no Q mass
        # outside mask_p), reported as the JSON-safe number.
        if q_on_p_zero > 0:
            full_nll_value = "infinity"
            nll_derivation = FULL_EXPECTED_NLL_DERIVATION
        else:
            full_nll_value = h_qp_truncated
            nll_derivation = ZERO_MASS_FULL_NLL_DERIVATION

        # Layer NLL under the empirical-P posteriors (bits/symbol per symbol pair).
        colP = P.sum(axis=0)
        pab_P = np.divide(P, colP, out=np.zeros_like(P), where=colP > 0)
        nll1, nll2 = _nll_maps(pab_P)

        # Declared seeded MC: E_Q[NLL] samples; zero-hit samples counted apart.
        flat = Q_joint.ravel()
        idx = rng.choice(flat.size, size=mc["n_samples"], p=flat)
        sa, sb = idx // Q_SYMBOLS, idx % Q_SYMBOLS
        stot = nll1[sa, sb] + nll2[sa, sb]
        zero_hit_count = int(np.isinf(stot).sum())
        finite = stot[np.isfinite(stot)]              # non-hit samples only
        quantiles = ({str(q): float(np.quantile(finite, q)) for q in mc["quantiles"]}
                     if finite.size else {})

        # ponytail: conditional mean covers non-hit samples only — ceiling is that
        # it is NOT the full expectation (which is infinite); upgrade path is an
        # explicit denominator model over zero-mass cells, explicitly out of scope.
        per_source[label] = {
            "source_id": sid,
            "raw_ser_quoted_from": f"channel_summary.json per_source[{sid}].ser",
            "raw_ser": ser,
            "q_definition": (
                "Q_B1(b|a) = (1-raw_ser)*delta_{b=a} + raw_ser*Uniform{b != a mod 1024}; "
                "Q(a)=Uniform"
            ),
            "q_total_mass": mass,
            "support_miss": {
                "q_mass_on_p_zero_cells_analytic": q_on_p_zero,
                "p_mass_on_q_zero_cells": p_on_q_zero,
                "zero_hit_count_mc": zero_hit_count,
                "zero_hit_frequency_mc": zero_hit_count / mc["n_samples"],
            },
            "full_expected_nll": full_nll_value,
            "full_expected_nll_derivation": nll_derivation,
            "conditional_finite_support_mean": {
                "mean_bits_per_symbol": float(finite.mean()) if finite.size else None,
                "quantiles_bits_per_symbol": quantiles,
                "n_samples_non_hit": int(finite.size),
                "mc_seed": mc["seed"],
                "definition_note": NAMING_RULES["conditional_finite_support_mean"],
            },
            "truncated_common_support_cross_entropy": {
                "value_bits": h_qp_truncated,
                "common_support_cell_count": int(mask_p.sum()),
                "definition_note": NAMING_RULES["truncated_common_support_cross_entropy"],
            },
            "old_audit_reference_readonly": {
                "note": ("v1 audit numbers retained as cross-reference only; never a "
                         "trusted source; deltas reported honestly, no silent alignment, "
                         "old files never rewritten"),
                "q_mass_on_p_zero_cells_v1_reference": OLD_AUDIT_REFERENCE[
                    "q_mass_on_p_zero_cells"][label],
                "delta_q_mass_v2_minus_v1": q_on_p_zero - OLD_AUDIT_REFERENCE[
                    "q_mass_on_p_zero_cells"][label],
                "mc_conditional_mean_v1_approx_range_bits_per_symbol": OLD_AUDIT_REFERENCE[
                    "mc_conditional_mean_bits_per_symbol_approx_range"],
                "truncated_cross_entropy_v1_approx_range_bits": OLD_AUDIT_REFERENCE[
                    "truncated_common_support_cross_entropy_bits_approx_range"],
            },
        }

    result = {
        "schema": "nbldpc_v32_operating_point_audit_correction_d1_v1",
        "p_definition": ("P = N_ab / total from channel_counts.npz key "
                         "{sid}_N_ab_train_N_ab_train (verbatim on-disk key with "
                         "duplicated suffix)"),
        "naming_rules": NAMING_RULES,   # schema description field enforcing C4
        "mc_plan_frozen_in_manifest": mc,
        "per_source": per_source,
        "signature_mismatch": any(
            (v["support_miss"]["q_mass_on_p_zero_cells_analytic"] > 0)
            != (v["full_expected_nll"] == "infinity")
            for v in per_source.values()),
    }
    _write_json(run_root, "d1_support_mismatch.json", result)
    return result


# --------------------------------------------------------------------------- #
# D2 — dual-law feasibility (two flat sibling objects; never merged)
# --------------------------------------------------------------------------- #

def run_d2(run_root: Path, paths: dict[str, Path], frozen: dict) -> dict:
    counts = load_counts_npz(paths["v25_channel_counts"])
    v31 = load_json(paths["v31_RUN_MANIFEST"])
    audits = load_json(paths["v31_matrix_audits"])
    registry = load_json(paths["v31_m1_registry"])["registered_calls"]
    tol = frozen["h_cross_check_tol_bits"]

    pkt = next(p for p in audits["packets"] if p.get("packet_id") == PACKET_ID)
    reg_by_layer_src = {(c["layer"], c["source"]): c for c in registry
                        if c.get("allocation_id") == ALLOCATION_ID}

    law_a_sources, law_b_sources = {}, {}
    for label, sid in SOURCE_IDS.items():
        N = counts[f"{sid}_N_ab_train_N_ab_train"]
        comp = layer_entropies(N)
        row31 = v31["configs"]["1024"]["sources"][label]
        drift_l1 = abs(comp["H_U1_given_B_bits"] - row31["H"]["L1"])
        drift_l2 = abs(comp["H_U2_given_B_U1_bits"] - row31["H"]["L2"])
        if max(drift_l1, drift_l2) > tol:
            raise AuditStop(EXIT_BLOCKED,
                            f"binding drift STOP: recomputed H differs from V31 manifest "
                            f"beyond {tol} bits for {label} "
                            f"(L1 diff {drift_l1:.3e}, L2 diff {drift_l2:.3e})")

        m1, m2 = int(row31["m1"]), int(row31["m2"])
        leak_verbatim = row31["leak_total_bits"]
        req_l1 = comp["H_U1_given_B_bits"] * N_SYMBOLS
        req_l2 = comp["H_U2_given_B_U1_bits"] * N_SYMBOLS
        req_total = comp["H_A_given_B_bits"] * N_SYMBOLS
        leak_l1 = m1 * BITS_PER_GF32
        leak_l2 = m2 * BITS_PER_GF32
        pure_total = (m1 + m2) * BITS_PER_GF32

        law_a_sources[label] = {
            "source_id": sid,
            "recomputed_chain_entropies_bits_per_symbol": {
                "H_U1_given_B": comp["H_U1_given_B_bits"],
                "H_U2_given_B_U1": comp["H_U2_given_B_U1_bits"],
                "H_A_given_B": comp["H_A_given_B_bits"],
                "chain_rule_identity_H_U1_plus_H_U2": comp["chain_rule_total_bits"],
            },
            "v31_cross_check_abs_diff_bits": {"L1": drift_l1, "L2": drift_l2,
                                              "tolerance": tol},
            "v31_manifest_quoted": {"field_citation":
                                    "nbldpc_v31_20260820/run_01/RUN_MANIFEST.json "
                                    "configs[\"1024\"].sources[%s]" % label,
                                    "H": row31["H"], "m1": m1, "m2": m2,
                                    "m_total": row31.get("m_total"),
                                    "leak_total_bits": leak_verbatim,
                                    "f_total": row31.get("f_total")},
            "registry_rates_quoted": {
                "allocation_id_filter": ALLOCATION_ID,
                "L1_rate": reg_by_layer_src.get(("L1", label), {}).get("rate"),
                "L2_rate": reg_by_layer_src.get(("L2", label), {}).get("rate"),
                "packet_id": pkt.get("packet_id"),
            },
            "required_bits_n1024": {"L1": req_l1, "L2": req_l2,
                                    "total_H_A_given_B": req_total},
            "leakage_bits_two_definitions_explicitly_separate": {
                "L1_syndrome_bits_m1x5": leak_l1,
                "L2_syndrome_bits_m2x5": leak_l2,
                "total_pure_recomputed_m1m2x5": pure_total,
                "total_verbatim_leak_total_bits": leak_verbatim,
                "definitions_note": ("verbatim manifest leak_total_bits includes budget "
                                     "overhead beyond the pure syndrome value; the two "
                                     "definitions stay separate and are never merged"),
            },
            "gap_bits_leakage_minus_required": {
                "L1": leak_l1 - req_l1,
                "L2": leak_l2 - req_l2,
                "total_pure_syndrome": pure_total - req_total,
                "total_verbatim": leak_verbatim - req_total,
            },
            "ratio_leakage_over_required": {
                "L1": leak_l1 / req_l1 if req_l1 > 0 else None,
                "L2": leak_l2 / req_l2 if req_l2 > 0 else None,
                "total_pure_syndrome": pure_total / req_total if req_total > 0 else None,
                "total_verbatim": leak_verbatim / req_total if req_total > 0 else None,
            },
        }

        ser = FROZEN_RAW_SER[label]
        h_q = h2(ser) + ser * math.log2(Q_SYMBOLS - 1)
        required_q = N_SYMBOLS * h_q
        law_b_sources[label] = {
            "source_id": sid,
            "raw_ser": ser,
            "h_q_b_given_a_bits_per_symbol_formula": "h2(raw_ser) + raw_ser*log2(1023)",
            "h_q_b_given_a_bits_per_symbol": h_q,
            "required_bits_n1024": required_q,
            "pure_syndrome_total_bits_m1m2x5": pure_total,
            "gap_bits_pure_syndrome_minus_required": pure_total - required_q,
        }

    empirical_P_budget = {
        "law": "A",
        "description": ("empirical joint P(A,B) from V25 train counts + F03/A02 "
                        "multilevel allocation at n=1024"),
        "per_source": law_a_sources,
        "conclusion_scope": CONCLUSION_SCOPE_NOMINAL,
    }
    original_Q_B1_budget = {
        "law": "B",
        "description": ("original B1 generator law Q_B1: Alice uniform + Bernoulli(raw_ser) "
                        "substitution with uniform nonzero delta mod 1024"),
        "per_source": law_b_sources,
        "conclusion": Q_B1_INFEASIBLE_CONCLUSION,
        "de_note": Q_B1_DE_NOTE,
    }

    result = {
        "schema": "nbldpc_v32_operating_point_audit_correction_d2_v1",
        "margin_method_frozen_in_manifest": frozen["margin_method"],
        "h_cross_check_tol_bits": tol,
        "empirical_P_budget": empirical_P_budget,
        "original_Q_B1_budget": original_Q_B1_budget,
        "red_line_note": ("the two laws remain two flat sibling objects and are never "
                          "merged into one boolean; Law A feasible does not rescue Law B; "
                          "Law B infeasible does not negate Law A's nominal statement"),
    }
    _write_json(run_root, "d2_dual_law_feasibility.json", result)
    return result


# --------------------------------------------------------------------------- #
# D3 — the single next question (definition only, nothing executed)
# --------------------------------------------------------------------------- #

def run_d3(run_root: Path, paths: dict[str, Path], frozen: dict) -> dict:
    del frozen  # d3 uses no tunable constants
    gate = load_json(paths["v26_gate"])

    result = {
        "schema": "nbldpc_v32_operating_point_audit_correction_d3_v1",
        "question": D3_QUESTION,
        "question_scope_qualification": (
            "DE is ensemble/channel analysis, NOT fixed-QC-graph analysis; this is a "
            "definition of the next question, not an execution"
        ),
        "not_fixed_packet_de": True,
        "layer_rate_table_verbatim_from_v31_registry": {
            "allocation_id_filter": ALLOCATION_ID,
            "rates": LAYER_RATE_TABLE_FROZEN,
            "source_order": ["1M", "1p5M", "2M"],
        },
        "v26_historical_reference_readonly": {
            "gate_status": gate.get("status"),
            "best_passing_f": gate.get("best_passing_f"),
            "non_extrapolation_note": (
                "V26 best_passing_f A02=1.3 (gate pass_target_f13) was a pass at the "
                "V26 operating point only; V31 layer rates differ, so this is NOT the "
                "same ensemble problem and must not be extrapolated to V31 rates"
            ),
        },
        "stop_condition": (
            "any source/layer failing to converge => do not start finite-control"
        ),
        "advance_condition": (
            "all three sources and both layers converge => only the ensemble/channel "
            "level may proceed; fixed-packet (QC graph) conclusions must wait for a "
            "separate finite-control change, which this change does not issue"
        ),
        "no_DE_executed_in_this_change": True,
    }
    _write_json(run_root, "d3_next_question.json", result)
    return result


# --------------------------------------------------------------------------- #
# Corrected branch decision — mechanical priority + C01–C13 checklist
# --------------------------------------------------------------------------- #

def _scan_forbidden_strings(run_root: Path, payload: dict) -> list[str]:
    hits = []
    texts = [json.dumps(payload, ensure_ascii=False)]
    for name in SCAN_SCOPE_FILES[:-1]:  # already-written v2 analysis outputs
        p = run_root / name
        if p.is_file():
            texts.append(p.read_text(encoding="utf-8"))
    blob = "\n".join(texts)
    for s in FORBIDDEN_CONCLUSION_STRINGS:
        if s in blob:
            hits.append(s)
    return hits


def write_corrected_branch_decision(run_root: Path, runner, d0r: dict, d1r: dict,
                                    d2r: dict, d3r: dict) -> dict:
    # Runtime immutability re-check of every bound input (during-run part of C12;
    # full before/during/after root hashing remains with the operator logs).
    c12_basis = "inputs unchanged since manifest freeze (SHA256 recomputed at decision time)"
    try:
        verify_manifest(run_root, runner)
        c12_value = True
    except AuditStop as exc:
        c12_value = False
        c12_basis = str(exc.reason)

    preds = d0r.get("predicates", {})
    b34_blob = json.dumps({k: v for k, v in d0r["aggregation_arm_x_source"].items()
                           if k.startswith(("B3|", "B4|"))}, ensure_ascii=False).lower()

    checklist = {
        "C01_d0_full_recompute_and_predicates_recorded": bool(preds),
        "C02_b2_sentinel_semantics": bool(d0r["b2_sentinel"]["sentinel_definition"]
                                          == "l2_errors_final==1024 AND terminal_decoder_status=='not_run': "
                                             "L1 failed so L2 never ran and x2_hat does not exist (C2)")
        and bool(d0r["b2_sentinel"]["excluded_from_trajectory_and_divergence_stats"])
        and bool(preds.get("P-ii_B2_sentinel_not_run", {}).get("passed")),
        "C03_b3b4_improve_but_no_syndrome_wording": "divergent" not in b34_blob,
        "C04_d1_analytic_q_mass_three_sources": (
            len(d1r["per_source"]) == 3
            and all(isinstance(v["support_miss"]["q_mass_on_p_zero_cells_analytic"], float)
                    and v["support_miss"]["q_mass_on_p_zero_cells_analytic"] >= 0
                    for v in d1r["per_source"].values())),
        "C05_full_nll_marked_infinity_with_derivation": all(
            bool(v["full_expected_nll_derivation"])
            and ((v["support_miss"]["q_mass_on_p_zero_cells_analytic"] > 0)
                 == (v["full_expected_nll"] == "infinity"))
            for v in d1r["per_source"].values()),
        "C06_conditional_truncated_naming": (
            d1r["naming_rules"] == NAMING_RULES
            and all("conditional_finite_support_mean" in v
                    and "truncated_common_support_cross_entropy" in v
                    and "full_expected_nll" in v for v in d1r["per_source"].values())),
        "C07_d2_dual_laws_both_present_unmerged": (
            "empirical_P_budget" in d2r and "original_Q_B1_budget" in d2r),
        "C08_empirical_P_nominal_conclusion_scope": (
            d2r["empirical_P_budget"]["conclusion_scope"] == CONCLUSION_SCOPE_NOMINAL),
        "C09_q_b1_infeasible_conclusion": (
            d2r["original_Q_B1_budget"]["conclusion"] == Q_B1_INFEASIBLE_CONCLUSION),
        "C10_d3_exact_rate_empirical_P_de_question": (
            d3r["question"] == D3_QUESTION
            and d3r["layer_rate_table_verbatim_from_v31_registry"]["rates"]
            == LAYER_RATE_TABLE_FROZEN
            and d3r["not_fixed_packet_de"] is True),
        "C11_no_de_or_decoder_invoked": True,  # runtime flags below; static scan external
        "C12_old_roots_byte_identical_runtime_window": c12_value,
        "C13_reviewer_artifact_blocking_false": False,  # set honestly at decision time
    }
    review_path = run_root / "readonly_review.json"
    if review_path.is_file():
        try:
            checklist["C13_reviewer_artifact_blocking_false"] = (
                load_json(review_path).get("blocking") is False)
        except json.JSONDecodeError:
            pass

    failed = [k for k, ok in checklist.items() if not ok]

    def _failed_class(names: list[str]) -> bool:
        return any(any(n.startswith(p) for p in names) for n in failed)

    reasons = []
    if _failed_class(["C04_", "C10_"]):  # D-verdict failures route to inconsistent
        selected = TERMINAL_INCONSISTENT
        reasons.append(f"D-verdict failure(s): {failed}")
    elif _failed_class(["C05_", "C06_", "C08_", "C09_", "C07_"]):
        # semantic-naming/law-conclusion drift inside our own schema cannot occur
        # without implementation error; classify conservatively as blocked.
        selected = TERMINAL_BLOCKED
        reasons.append(f"verifier self-consistency failure(s): {failed}")
    elif failed:  # remaining pending items (C13 review artifact, C12 window)
        selected = TERMINAL_BLOCKED
        reasons.append(f"pending/unmet condition(s): {failed}")
    else:
        selected = TERMINAL_CORRECTED
        reasons.append("all C01-C13 conditions satisfied at decision time")

    payload = {
        "schema": "nbldpc_v32_operating_point_audit_correction_branch_decision_v1",
        "selected_branch": selected,
        "selection_priority_frozen": TERMINAL_PRIORITY,
        "conditions_checklist_c01_c13": checklist,
        "failed_conditions": failed,
        "selection_reasons": reasons,
        "branch_inputs": {
            "d0_signature_mismatch": d0r.get("signature_mismatch"),
            "d1_signature_mismatch": d1r.get("signature_mismatch"),
            "d1_full_expected_nll_all_sources": {lbl: v["full_expected_nll"]
                                                 for lbl, v in d1r["per_source"].items()},
            "d2_law_a_conclusion_scope": d2r["empirical_P_budget"]["conclusion_scope"],
            "d2_law_b_conclusion": d2r["original_Q_B1_budget"]["conclusion"],
            "d3_question_defined_not_executed": True,
        },
        "candidate_only": True,
        "main_acceptance_pending": True,
        "review_note": (
            "C13 is evaluated against readonly_review.json at decision time; the "
            "independent reviewer appends that file after this sequence, and the main "
            "adjudication (A9) owns the final candidate determination"
        ),
        "generated_by_execution_order": ["manifest_freeze", "d0", "d1", "d2", "d3",
                                         "corrected_branch_decision"],
    }

    forbidden_hits = _scan_forbidden_strings(run_root, payload)
    if forbidden_hits:
        raise AuditStop(EXIT_EVIDENCE,
                        f"forbidden conclusion string(s) present in v2 outputs: {forbidden_hits}")

    _write_json(run_root, "corrected_branch_decision.json", payload)
    return payload


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

STAGE_OUTPUT_NAMES = {
    "d0": "d0_failure_signature.json",
    "d1": "d1_support_mismatch.json",
    "d2": "d2_dual_law_feasibility.json",
    "d3": "d3_next_question.json",
}


# --------------------------------------------------------------------------- #
# Run-root guardrail (fix task C): minimal explicit allow/deny path checks.
# No general security framework — a fixed deny list plus one allow rule.
# --------------------------------------------------------------------------- #

_PROTECTED_ROOTS_REL = [
    V32_DIR,   # nbldpc_v32_finite_de_bridge/run_01
    OLD_AUDIT_DIR,
    V25_DIR,
    V26_DIR,
    V31_DIR,
    f"{DIAG}/nbldpc_v31_closeout_audit_v2/run_01",
    f"{DIAG}/nbldpc_v31_closeout_audit_v2/run_02",
    "openspec/changes/archive",
]
_BROAD_ROOTS_REL = ["results", "comparison_bench/outputs_comparison", DIAG]


def _norm(p: Path) -> str:
    return os.path.normcase(str(Path(p).resolve()))


def validate_run_root(run_root: Path, fake_runner: bool) -> None:
    """Allow exactly: the frozen additive v2 run_01 root, or -- only with an
    explicit fake runner -- a directory under workspace/.  Reject the repo
    root, results root, diagnostics root and other too-broad paths, and every
    protected old root itself or any subpath inside it."""
    rr = _norm(run_root)
    if rr == _norm(DEFAULT_RUN_ROOT):
        return
    ws = _norm(REPO_ROOT / "workspace")
    if fake_runner and rr.startswith(ws + os.sep):
        return

    repo = _norm(REPO_ROOT)
    if rr == repo:
        raise AuditStop(EXIT_WRITE, "run root rejected: repository root itself")
    for broad in _BROAD_ROOTS_REL:
        br = _norm(REPO_ROOT / broad)
        if rr == br:
            raise AuditStop(EXIT_WRITE, f"run root rejected: too-broad root {broad}")
    for prot in _PROTECTED_ROOTS_REL:
        pr = _norm(REPO_ROOT / prot)
        if rr == pr:
            raise AuditStop(EXIT_WRITE, f"run root rejected: protected old root {prot}")
        if rr.startswith(pr + os.sep):
            raise AuditStop(EXIT_WRITE,
                            f"run root rejected: subpath inside protected root {prot}")
    raise AuditStop(
        EXIT_WRITE,
        "run root rejected: only the frozen additive v2 run_01 root, or a "
        "workspace test root with an explicit fake runner, may be used")


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_nonbinary_v32_operating_point_audit_correction.py",
        description="Read-only correction verifier for the NB-LDPC V32 operating-point "
                    "audit (v2). No DE rerun, no decoder invocation, no raw capture access.")
    parser.add_argument("subcommand", choices=["d0", "d1", "d2", "d3", "all"])
    parser.add_argument("--runner", default=None, metavar="MODULE:ATTR",
                        help="binding provider injection for tests (default: real repo bindings)")
    parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT),
                        help="correction run root (default: frozen v2 run_01 path)")
    args = parser.parse_args(argv)

    run_root = Path(args.run_root)
    try:
        validate_run_root(run_root, fake_runner=args.runner is not None)
        if args.subcommand == "all":
            if run_root.exists():  # STOP: collision — no overwrite, no automatic run_02
                raise AuditStop(EXIT_COLLISION,
                                f"run root already exists -> STOP collision: {run_root} "
                                f"(no overwrite, no automatic run_02)")
            runner = load_runner(args.runner)
            paths = runner.binding_paths()
            binding_rows, extras = stage0_bindings(paths)
            run_root.mkdir(parents=True)
            manifest = freeze_manifest(run_root, binding_rows, extras)
            frozen = manifest["frozen"]
            d0r = run_d0(run_root, paths, frozen)
            d1r = run_d1(run_root, paths, frozen)
            d2r = run_d2(run_root, paths, frozen)
            d3r = run_d3(run_root, paths, frozen)
            write_corrected_branch_decision(run_root, runner, d0r, d1r, d2r, d3r)
        else:
            runner = load_runner(args.runner)
            manifest = verify_manifest(run_root, runner)  # refuse on missing/drift
            frozen = manifest["frozen"]
            paths = runner.binding_paths()
            name = STAGE_OUTPUT_NAMES[args.subcommand]
            if (Path(run_root) / name).exists():
                raise AuditStop(EXIT_COLLISION,
                                f"output collision: {name} already exists in {run_root}")
            if args.subcommand == "d0":
                run_d0(run_root, paths, frozen)
            elif args.subcommand == "d1":
                run_d1(run_root, paths, frozen)
            elif args.subcommand == "d2":
                run_d2(run_root, paths, frozen)
            elif args.subcommand == "d3":
                run_d3(run_root, paths, frozen)
    except AuditStop as stop:
        print(f"STOP[{stop.code}]: {stop.reason}", file=sys.stderr)
        return stop.code
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(cli_main())
