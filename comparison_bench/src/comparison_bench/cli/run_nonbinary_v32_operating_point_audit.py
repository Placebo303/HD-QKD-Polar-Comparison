"""Read-only operating-point consistency audit for NB-LDPC V32 (audit-only).

OpenSpec change: formal-nonbinary-ldpc-v32-operating-point-consistency-audit.

This CLI is STRICTLY READ-ONLY over its inputs.  It performs no DE rerun, no
new DE sampling, no decoder invocation and never touches raw device-capture
data of any kind.
Subcommands:

- ``d0``   full failure-signature extraction from V32 run_01 ``per_block.jsonl``
- ``d1``   B1 generator/posterior consistency (analytic Q_B1 vs P_V25)
- ``d2``   information-theoretic feasibility vs actual code rates + branch map
- ``d3``   read-only inspection of existing V26 DE evidence
- ``all``  manifest freeze -> d0 -> d1 -> d2 -> d3 -> final_branch_decision

``--runner MODULE:ATTR`` injects an alternative binding provider (test fakes);
the provider object must expose ``binding_paths() -> dict[str, Path]``.

Exit codes: 0 ok; 2 output-root collision; 3 binding drift/missing;
4 evidence inconsistency; 5 manifest missing/drifted/tampered; 6 unsafe write.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------- #
# Frozen constants (identical to the four OpenSpec docs; do not restate elsewh.)
# --------------------------------------------------------------------------- #

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RUN_ROOT = (
    REPO_ROOT / "comparison_bench/outputs_comparison/nonbinary_diagnostics"
    / "nbldpc_v32_operating_point_audit/run_01"
)

V32_DIR = "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_finite_de_bridge/run_01"
V25_DIR = "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04"
V26_DIR = "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v26_20260818/run_02"
V31_DIR = "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01"
HARNESS_REL = "comparison_bench/src/comparison_bench/cli/run_nonbinary_v32_finite_de_bridge.py"
SAMPLER_REL = "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_channel.py"

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
BITS_PER_GF32 = 5.0  # log2(32)

EXPECTED_COUNTS = {"B5": 1, "B0": 6, "B1": 60, "B2": 60, "B3": 60, "B4": 60}
PER_BLOCK_SCHEMA = "nbldpc_v32_bridge_block_result_v1"

# Preregistered BEFORE any D1 computation (SHALL-D1c). Derivation bases stated.
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
DELTA_BIN_EDGES = list(range(-1024, 1025, 64))
LOG2_EDGES_BITS_PER_SYMBOL = [float(2 ** e) for e in range(-20, 7)]
MARGIN_METHOD = (
    "simple gap reporting at n=1024 only: gap_bits = leakage_bits - "
    "required_bits per layer and total, plus leakage/required ratio; no "
    "normal approximation and no other statistics"
)
H_CROSS_CHECK_TOL_BITS = 1e-6

BRANCH_TABLE = [
    {
        "branch": "A",
        "condition": "total infeasible",
        "consequence": "LDPC 与 Polar 同速率方案均暂停，先重审泄漏预算/运行点",
    },
    {
        "branch": "B",
        "condition": "total feasible 且 L2 allocation infeasible",
        "consequence": "当前 multilevel allocation 失败，joint/重新分配的 NB-Polar feasibility 价值上升，不值得先换 QC 图",
    },
    {
        "branch": "C",
        "condition": "layer 与 total 均可行",
        "consequence": "finite graph/decoder 值得一次 corrected matched control（后续单独变更，不在本审计内执行）",
    },
]

EXIT_OK = 0
EXIT_COLLISION = 2
EXIT_BINDING = 3
EXIT_EVIDENCE = 4
EXIT_MANIFEST = 5
EXIT_WRITE = 6

DE_QUESTIONS = [
    "What is the DE threshold f for the QC-cyclic-projective packet per source under the corrected matched generator law Q_B1 (uniform alice, Bernoulli(raw_ser) substitution with uniform nonzero delta mod 1024) at n=1024 for the A02 L1/L2 layers?",
    "Does the empirical-channel pass point (gate.json best_passing_f A01=1.6, A02=1.3) remain a pass when the channel sampler draws from Q_B1 instead of the V25 train joint?",
]


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


def _write_json(run_root: Path, name: str, obj) -> Path:
    p = _safe_path(run_root, name)
    if p.exists():
        raise AuditStop(
            EXIT_COLLISION, f"refusing to overwrite existing output {name} (additive-only)"
        )
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def _write_text(run_root: Path, name: str, text: str) -> Path:
    p = _safe_path(run_root, name)
    if p.exists():
        raise AuditStop(
            EXIT_COLLISION, f"refusing to overwrite existing output {name} (additive-only)"
        )
    p.write_text(text, encoding="utf-8")
    return p


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_canonical(obj) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _md_table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Runner contract + default repo bindings
# --------------------------------------------------------------------------- #

class RepoBindings:
    """Default binding provider: resolves frozen repository paths read-only."""

    def binding_paths(self) -> dict[str, Path]:
        paths = {}
        paths["v32_per_block"] = REPO_ROOT / f"{V32_DIR}/per_block.jsonl"
        paths["v32_run_manifest"] = REPO_ROOT / f"{V32_DIR}/RUN_MANIFEST.json"
        for b in range(6):
            paths[f"v32_summary_B{b}"] = REPO_ROOT / f"{V32_DIR}/summary_B{b}.json"
        paths["v32_candidate_terminal"] = REPO_ROOT / f"{V32_DIR}/candidate_terminal.json"
        paths["v32_terminal_reconstruction"] = REPO_ROOT / f"{V32_DIR}/terminal_reconstruction.json"
        paths["v25_channel_counts"] = REPO_ROOT / f"{V25_DIR}/channel_counts.npz"
        paths["v25_channel_summary"] = REPO_ROOT / f"{V25_DIR}/channel_summary.json"
        paths["v25_split_manifest"] = REPO_ROOT / f"{V25_DIR}/split_manifest.json"
        for n in ("run_manifest", "gate", "m0_report", "m1_report", "screen_results",
                  "confirmation_results"):
            paths[f"v26_{n}"] = REPO_ROOT / f"{V26_DIR}/{n}.json"
        for n in ("run_manifest", "matrix_audits", "m1_registry"):
            paths[f"v31_{n}"] = REPO_ROOT / f"{V31_DIR}/{n}.json"
        paths["code_fact_harness"] = REPO_ROOT / HARNESS_REL
        paths["code_fact_sampler"] = REPO_ROOT / SAMPLER_REL
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
            raise AuditStop(EXIT_EVIDENCE, f"truncated/malformed JSONL at {path} line {i}: {exc}")
    return recs


def load_counts_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path) as z:
        return {k: np.asarray(z[k], dtype=np.float64) for k in z.files}


# --------------------------------------------------------------------------- #
# Stage 0 — binding verification (recorded into audit_manifest.json)
# --------------------------------------------------------------------------- #

CODE_FACT_HARNESS_MARKERS = ("def synth_channel_sample", "rng.integers(1, 1024", "(alice + deltas) % 1024")
CODE_FACT_SAMPLER_MARKERS = ("P(A,B)", "N_ab")


def stage0_bindings(paths: dict[str, Path]) -> tuple[list[dict], dict]:
    rows = []
    for name in sorted(paths):
        p = Path(paths[name])
        if not p.is_file():
            raise AuditStop(EXIT_BINDING, f"binding missing: {name}: {p}")
        rows.append({
            "binding": name,
            "path": str(p),
            "size_bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        })

    # Binding 5: harness synth_channel_sample L555-564 (code fact, cited verbatim).
    harness_lines = Path(paths["code_fact_harness"]).read_text(encoding="utf-8").splitlines()
    harness_block = harness_lines[554:564]
    for marker in CODE_FACT_HARNESS_MARKERS:
        if not any(marker in ln for ln in harness_block):
            raise AuditStop(EXIT_BINDING, f"harness code-fact drift at L555-564: marker {marker!r} absent")
    # Binding 6: V26 sampler semantics L10-13.
    sampler_lines = Path(paths["code_fact_sampler"]).read_text(encoding="utf-8").splitlines()
    sampler_block = sampler_lines[9:13]
    for marker in CODE_FACT_SAMPLER_MARKERS:
        if not any(marker in ln for ln in sampler_block):
            raise AuditStop(EXIT_BINDING, f"sampler code-fact drift at L10-13: marker {marker!r} absent")

    code_facts = {
        "harness_synth_channel_sample_L555_L564": {
            "file": str(paths["code_fact_harness"]),
            "lines": "555-564",
            "excerpt": "\n".join(harness_block),
        },
        "nonbinary_v26_channel_semantics_L10_L13": {
            "file": str(paths["code_fact_sampler"]),
            "lines": "10-13",
            "excerpt": "\n".join(sampler_block),
        },
    }

    # Binding 2: verbatim npz keys + frozen raw_ser values.
    counts = load_counts_npz(paths["v25_channel_counts"])
    expected_keys = {f"{sid}_N_ab_train_N_ab_train" for sid in SOURCE_IDS.values()}
    if set(counts.keys()) != expected_keys:
        raise AuditStop(EXIT_BINDING, f"npz keys drift: got {sorted(counts.keys())}")
    summary = load_json(paths["v25_channel_summary"])
    for label, sid in SOURCE_IDS.items():
        got = summary.get("per_source", {}).get(sid, {}).get("ser")
        if got != FROZEN_RAW_SER[label]:  # exact match on the frozen value
            raise AuditStop(EXIT_BINDING, f"frozen raw_ser drift for {label}: {got!r}")

    # Binding 3: V26 gate identity.
    gate = load_json(paths["v26_gate"])
    if gate.get("status") != "pass_target_f13":
        raise AuditStop(EXIT_BINDING, f"V26 gate status drift: {gate.get('status')!r}")
    bpf = gate.get("best_passing_f") or {}
    if bpf.get("A01") != 1.6 or bpf.get("A02") != 1.3:
        raise AuditStop(EXIT_BINDING, f"V26 best_passing_f drift: {bpf!r}")

    # Binding 4: V31 allocation/leakage identities.
    v31 = load_json(paths["v31_run_manifest"])
    cfg = v31.get("configs", {}).get("1024", {})
    m2_set, leak_set = set(), set()
    for label, row in cfg.get("sources", {}).items():
        if row.get("m1") != 16:
            raise AuditStop(EXIT_BINDING, f"V31 m1 drift for {label}: {row.get('m1')!r}")
        m2_set.add(row.get("m2"))
        leak_set.add(row.get("leak_total_bits"))
        if "source_id" not in row or "H" not in row or "L1" not in row["H"] or "L2" not in row["H"]:
            raise AuditStop(EXIT_BINDING, f"V31 source fields missing for {label}")
    if m2_set != {184, 190, 192}:
        raise AuditStop(EXIT_BINDING, f"V31 m2 values drift: {sorted(map(str, m2_set))}")
    if leak_set != {1064.0, 1094.0, 1104.0}:
        raise AuditStop(EXIT_BINDING, f"V31 leak_total_bits drift: {sorted(map(str, leak_set))}")
    audits = load_json(paths["v31_matrix_audits"])
    packets = audits.get("packets", [])
    if not packets or packets[0].get("audits", {}).get("L1", {}).get("shape") != [16, 1024]:
        raise AuditStop(EXIT_BINDING, "V31 matrix_audits packet L1 shape drift")
    registry = load_json(paths["v31_m1_registry"]).get("registered_calls", [])
    required_reg = {"layer", "rate", "H_bits_per_symbol", "m1", "m2"}
    if not registry or any(not required_reg.issubset(call) for call in registry):
        raise AuditStop(EXIT_BINDING, "V31 m1_registry registered_calls field drift")

    return rows, code_facts


# --------------------------------------------------------------------------- #
# Manifest freeze / verify (SHALL-MF1)
# --------------------------------------------------------------------------- #

MANIFEST_NAME = "audit_manifest.json"


def freeze_manifest(run_root: Path, binding_rows: list[dict], code_facts: dict) -> dict:
    frozen = {
        "thresholds": THRESHOLDS,
        "mc_plan": MC_PLAN,
        "histogram_bins": {
            "error_delta_bin_edges": DELTA_BIN_EDGES,
            "log2_edges_bits_per_symbol": LOG2_EDGES_BITS_PER_SYMBOL,
        },
        "margin_method": MARGIN_METHOD,
        "h_cross_check_tol_bits": H_CROSS_CHECK_TOL_BITS,
        "branch_table": BRANCH_TABLE,
    }
    manifest = {
        "schema": "nbldpc_v32_operating_point_audit_manifest_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "execution_order": ["manifest_freeze", "d0", "d1", "d2", "d3", "final_branch_decision"],
        "bindings": binding_rows,
        "code_facts": code_facts,
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
    frozen = manifest.get("frozen")
    if not isinstance(frozen, dict) or manifest.get("freeze_digest") != sha256_canonical(frozen):
        raise AuditStop(
            EXIT_MANIFEST,
            "manifest freeze digest mismatch: thresholds/MC plan/bins/margin method drifted",
        )
    current = runner.binding_paths()
    for row in manifest.get("bindings", []):
        p = Path(current[row["binding"]])
        if not p.is_file():
            raise AuditStop(EXIT_BINDING, f"input drift: binding {row['binding']} missing ({p})")
        if sha256_file(p) != row["sha256"]:
            raise AuditStop(EXIT_BINDING, f"input drift detected on {row['binding']}: {p}")
    return manifest


# --------------------------------------------------------------------------- #
# F03/A02 layer maps + entropies (inline; no production imports)
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


def layer_entropies(N: np.ndarray) -> dict:
    """H(U1|B), H(U2|B,U1), H(A|B) in bits via the F03/A02 maps.

    Chain rule on joint counts: H(U_i | B, U_<i) = H(B, U_<i, U_i) - H(B, U_<i).
    """
    N3 = N.reshape(32, 32, Q_SYMBOLS)  # [u1, u2, b] because a = 32*u1 + u2
    h_b = _vec_entropy(N.sum(axis=0))
    # H(U1,B) == H(B,U1) (symmetric); H(B,U1,U2) from the full 3-way joint.
    h_u1_b = joint_entropy_bits(N3.sum(axis=1))
    h_b_u1_u2 = joint_entropy_bits(N3)
    h_l1 = h_u1_b - h_b
    h_l2 = h_b_u1_u2 - h_u1_b
    col = N.sum(axis=0)
    h_ab = _cond_entropy_rows(N, col)
    return {"H_U1_given_B_bits": float(h_l1), "H_U2_given_B_U1_bits": float(h_l2),
            "H_A_given_B_bits": float(h_ab),
            "chain_rule_total_bits": float(h_l1 + h_l2)}


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


# --------------------------------------------------------------------------- #
# D0 — full failure signature
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

    return {
        "predicates": {
            "P-i_B1_active_divergence": {"passed": not violations["P_i"],
                                         "violating_block_uids": violations["P_i"]},
            "P-ii_B2_sentinel_not_run": {"passed": not violations["P_ii"],
                                         "violating_block_uids": violations["P_ii"]},
            "P-iii_B3B4_improve_no_syndrome": {"passed": not violations["P_iii"],
                                               "violating_block_uids": violations["P_iii"]},
        },
        "signature_mismatch": any(violations.values()),
    }


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
        raise AuditStop(EXIT_EVIDENCE, f"duplicate block_uid (evidence inconsistency): {dupes[:5]}")

    by_arm: dict[str, list[dict]] = {}
    schema_bad = [r.get("schema") for r in records if r.get("schema") != PER_BLOCK_SCHEMA]
    if schema_bad:
        raise AuditStop(EXIT_EVIDENCE, f"per_block schema drift: {schema_bad[:3]}")
    for r in records:
        by_arm.setdefault(r.get("arm"), []).append(r)

    counts = {arm: len(by_arm.get(arm, [])) for arm in EXPECTED_COUNTS}
    if counts != EXPECTED_COUNTS:
        raise AuditStop(EXIT_EVIDENCE, f"arm record-count mismatch: {counts} vs {EXPECTED_COUNTS}")

    # B5 import control reported separately.
    b5 = by_arm["B5"][0]
    b5_report = {
        "block_uid": b5.get("block_uid"),
        "kind": b5.get("kind"),
        "imported_records": b5.get("imported_records"),
        "integrity_ok": b5.get("integrity_ok"),
        "per_source_counts": b5.get("per_source_counts"),
    }

    # Decode records B0..B4: extract design §3 field list.
    extracted: dict[str, list[dict]] = {}
    for arm in ("B0", "B1", "B2", "B3", "B4"):
        rows = []
        for r in by_arm[arm]:
            missing = [f for f in D0_EXTRACT_FIELDS if f not in r]
            if missing:
                raise AuditStop(
                    EXIT_EVIDENCE, f"decode record {r.get('block_uid')} missing fields {missing}"
                )
            rs = r.get("residual_syndrome_stats") or {}
            if "l1_residual_checks" not in rs or "l2_residual_checks" not in rs:
                raise AuditStop(
                    EXIT_EVIDENCE, f"decode record {r.get('block_uid')} missing residual_syndrome_stats"
                )
            row = {f: r[f] for f in D0_EXTRACT_FIELDS}
            row.update({
                "block_uid": r.get("block_uid"),
                "source": r.get("source"),
                "l1_residual_checks": rs.get("l1_residual_checks"),
                "l2_residual_checks": rs.get("l2_residual_checks"),
            })
            rows.append(row)
        extracted[arm] = rows

    delta_edges = frozen["histogram_bins"]["error_delta_bin_edges"]
    log_edges = frozen["histogram_bins"]["log2_edges_bits_per_symbol"]
    numeric_fields = [
        "l1_errors_initial", "l1_errors_final", "l2_errors_initial", "l2_errors_final",
        "iterations", "unsatisfied_checks", "posterior_nll", "posterior_entropy",
        "truth_symbol_rank",
    ]

    aggregation = {}
    for arm in ("B0", "B1", "B2", "B3", "B4"):
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
            if arm != "B2":  # sentinel excluded from error-trajectory analysis
                entry["l1_error_delta_histogram"] = _hist(
                    [r["l1_errors_final"] - r["l1_errors_initial"] for r in rows], delta_edges)
                entry["l2_error_delta_histogram"] = _hist(
                    [r["l2_errors_final"] - r["l2_errors_initial"] for r in rows], delta_edges)
            entry["posterior_nll_bits_per_symbol_histogram"] = _hist(
                [r["posterior_nll"] / N_SYMBOLS for r in rows], log_edges)
            entry["posterior_entropy_bits_per_symbol_histogram"] = _hist(
                [r["posterior_entropy"] / N_SYMBOLS for r in rows], log_edges)
            aggregation[f"{arm}|{src}"] = entry

    predicates = check_d0_predicates({arm: extracted[arm] for arm in extracted})

    result = {
        "schema": "nbldpc_v32_operating_point_audit_d0_v1",
        "records_total": len(records),
        "arm_record_counts": counts,
        "duplicate_block_uids": [],
        "b5_import_control": b5_report,
        "extracted_fields_per_decode_record": D0_EXTRACT_FIELDS,
        "aggregation_arm_x_source": aggregation,
        "b2_sentinel_excluded_from_trajectory": True,
        "units_rule": "posterior_nll/posterior_entropy reported raw (per block of n=1024) and as bits/symbol; comparisons against reference entropies use bits/symbol only",
        **predicates,
    }
    _write_json(run_root, "d0_signature.json", result)

    md = ["# D0 — Full failure signature (read-only)", ""]
    md.append(f"- records_total: {len(records)}; arm counts: {counts}")
    md.append(f"- B5 import control: imported={b5_report['imported_records']}, integrity_ok={b5_report['integrity_ok']}")
    md.append(f"- signature_mismatch: {predicates['signature_mismatch']}")
    for k, v in predicates["predicates"].items():
        md.append(f"- {k}: passed={v['passed']} violations={len(v['violating_block_uids'])}")
    md.append("")
    rows = []
    for key, e in sorted(aggregation.items()):
        rows.append([key, e["n_records"], round(e["l2_errors_initial"]["mean"], 2),
                     round(e["l2_errors_final"]["mean"], 2),
                     round(e.get("posterior_nll_bits_per_symbol", {}).get("mean", float("nan")), 6)])
    md += ["## arm×source means (L2 initial→final, NLL bits/symbol)", "",
           _md_table(["arm|source", "n", "l2_init_mean", "l2_final_mean", "nll_bpsym_mean"], rows)]
    _write_text(run_root, "d0_signature.md", "\n".join(md) + "\n")
    return result


# --------------------------------------------------------------------------- #
# D1 — B1 generator/posterior consistency
# --------------------------------------------------------------------------- #

def build_q_joint(ser: float) -> np.ndarray:
    """Q_B1(b|a) = (1-ser)*delta_{b=a} + ser*Uniform{b != a mod 1024}, joint form."""
    q = np.full((Q_SYMBOLS, Q_SYMBOLS), ser / ((Q_SYMBOLS - 1) * Q_SYMBOLS), dtype=np.float64)
    np.fill_diagonal(q, (1.0 - ser) / Q_SYMBOLS)
    return q


def _delta_distribution(joint: np.ndarray) -> np.ndarray:
    # P(delta=d) = sum_a joint[a, (a+d) mod 1024]; bob = (a+delta) mod 1024.
    out = np.zeros(Q_SYMBOLS)
    idx_a = np.arange(Q_SYMBOLS)
    for d in range(Q_SYMBOLS):
        out[d] = joint[idx_a, (idx_a + d) % Q_SYMBOLS].sum()
    return out


def _layer_posteriors(pab: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """From P(a|b): P(U1|B) [32,1024] and P(U2|B,U1) [32,32,1024]."""
    p3 = pab.reshape(32, 32, Q_SYMBOLS)          # [u1, u2, b]
    p_u1_b = p3.sum(axis=1)                       # P(U1=u1|B)
    with np.errstate(divide="ignore", invalid="ignore"):
        p_u2_b_u1 = np.divide(p3, p_u1_b[:, None, :],
                              out=np.zeros_like(p3), where=p_u1_b[:, None, :] > 0)
    return p_u1_b, p_u2_b_u1


def _nll_maps(pab: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-(a,b) NLL of the true layer symbols under the V25 posteriors (bits)."""
    p_u1_b, p_u2_b_u1 = _layer_posteriors(pab)  # p_u2_b_u1 is [u1, u2, b]
    u1 = (np.arange(Q_SYMBOLS) >> 5)[:, None]
    u2 = (np.arange(Q_SYMBOLS) & 31)[:, None]
    cols = np.arange(Q_SYMBOLS)[None, :]
    with np.errstate(divide="ignore"):
        nll1 = -np.log2(p_u1_b[u1, cols])   # [a,b]
        nll2 = -np.log2(p_u2_b_u1[u1, u2, cols])
    return nll1, nll2


def run_d1(run_root: Path, paths: dict[str, Path], frozen: dict) -> dict:
    counts = load_counts_npz(paths["v25_channel_counts"])
    summary = load_json(paths["v25_channel_summary"])
    thresholds = frozen["thresholds"]
    mc = frozen["mc_plan"]

    rng = np.random.default_rng(mc["seed"])
    per_source = {}
    worst_ratio = 0.0
    for label, sid in SOURCE_IDS.items():
        N = counts[f"{sid}_N_ab_train_N_ab_train"]
        total = float(N.sum())
        P = N / total
        ser = summary["per_source"][sid]["ser"]
        Q_joint = build_q_joint(ser)

        mass = float(Q_joint.sum())
        offdiag_support_ok = bool(np.all(np.diag(np.ones_like(Q_joint)) >= 0)) and \
            float(Q_joint[~np.eye(Q_SYMBOLS, dtype=bool)].min()) > 0.0
        if abs(mass - 1.0) > 1e-12:
            raise AuditStop(EXIT_EVIDENCE, f"Q_B1 mass conservation violated for {label}: {mass}")

        # Cross-entropy H(Q,P) restricted to cells where P is defined (>0).
        mask_p = P > 0
        h_qp = float(-(Q_joint[mask_p] * np.log2(P[mask_p])).sum())
        q_on_p_zero = float(Q_joint[~mask_p].sum())           # Q mass on P-zero cells
        p_on_q_zero = float(P[Q_joint <= 0].sum())            # P mass on Q-zero cells

        # Delta distributions incl +-1 direction mass (pm1_mass contrast).
        p_delta = _delta_distribution(P)
        q_delta = np.concatenate([[1.0 - ser], np.full(Q_SYMBOLS - 1, ser / (Q_SYMBOLS - 1))])
        pm1 = summary["per_source"][sid].get("pm1_mass", {})

        # Posteriors under both laws + conditional TV distances.
        colP = P.sum(axis=0)
        pab_P = np.divide(P, colP, out=np.zeros_like(P), where=colP > 0)
        qcol = Q_joint.sum(axis=0)
        pab_Q = Q_joint / qcol  # doubly stochastic: qcol == 1/1024 everywhere
        pu1_P, pu2_P = _layer_posteriors(pab_P)
        pu1_Q, pu2_Q = _layer_posteriors(pab_Q)
        tv1 = 0.5 * np.abs(pu1_Q - pu1_P).sum(axis=0)         # per conditioning b
        valid_b = colP > 0
        p3P = pab_P.reshape(32, 32, Q_SYMBOLS)
        p3Q = pab_Q.reshape(32, 32, Q_SYMBOLS)
        denom = p3P.sum(axis=1)                                # P(u1|b)
        cond_valid = denom > 0
        tv2 = 0.5 * np.abs(p3Q - p3P).sum(axis=1)              # [u1, b]
        tv2_vals = tv2[cond_valid]

        # Dual expected NLL.
        nll1, nll2 = _nll_maps(pab_P)
        mask_p = P > 0  # NLL is finite exactly where the joint has mass
        self_nll1 = float((P[mask_p] * nll1[mask_p]).sum())    # E_V25[NLL|own posterior] L1
        self_nll2 = float((P[mask_p] * nll2[mask_p]).sum())
        q_terms = (Q_joint * nll1) + (Q_joint * nll2)
        analytic_inf = bool(np.isinf(q_terms).any() and Q_joint[np.isinf(q_terms)].sum() > 0)
        eq_analytic = None if analytic_inf else float(q_terms.sum())

        # Declared seeded MC: Q-sampled empirical NLL distribution (bits/symbol).
        flat = Q_joint.ravel()
        idx = rng.choice(flat.size, size=mc["n_samples"], p=flat)
        sa, sb = idx // Q_SYMBOLS, idx % Q_SYMBOLS
        s1 = nll1[sa, sb]
        s2 = nll2[sa, sb]
        stot = s1 + s2
        zero_hits = int(np.isinf(stot).sum())
        finite = stot[np.isfinite(stot)]  # already per-symbol bits
        quantiles = {str(q): float(np.quantile(finite, q))
                     for q in mc["quantiles"]} if finite.size else {}

        # nll maps are per-symbol quantities: expectations are bits/symbol as-is.
        ref_bpsym = self_nll1 + self_nll2  # ~= V31 (H.L1+H.L2) magnitude
        eq_bpsym = (float(q_terms.sum()) if not analytic_inf else
                    (float(finite.mean()) if finite.size else float("inf")))
        ratio = eq_bpsym / ref_bpsym if ref_bpsym > 0 else float("inf")
        worst_ratio = max(worst_ratio, ratio if np.isfinite(ratio) else float("inf"))
        catastrophic = (ratio >= thresholds["expected_nll_ratio_K"]) or \
            (q_on_p_zero >= thresholds["support_miss_fraction_max"])

        per_source[label] = {
            "source_id": sid,
            "raw_ser_quoted_from": f"channel_summary.json per_source[{sid}].ser",
            "raw_ser": ser,
            "q_mass_conservation": {"total_mass": mass, "off_diagonal_support_positive": offdiag_support_ok},
            "cross_entropy_H_QP_bits_over_common_support": h_qp,
            "common_support_cell_count": int(mask_p.sum()),
            "support_miss": {
                "q_mass_on_p_zero_cells": q_on_p_zero,
                "p_mass_on_q_zero_cells": p_on_q_zero,
                "mc_zero_hit_count": zero_hits,
                "mc_zero_hit_frequency": zero_hits / mc["n_samples"],
            },
            "delta_distribution": {
                "q_delta_mass_at_zero": float(q_delta[0]),
                "q_delta_pm1_mass": {"plus1": float(q_delta[1]), "minus1": float(q_delta[Q_SYMBOLS - 1])},
                "p_delta_pm1_mass_quoted_from_pm1_mass_field": {
                    "plus1": pm1.get("+1"), "minus1": pm1.get("-1"), "zero": pm1.get("0")},
                "structure_note": "Q's uniform nonzero delta destroys the V25 +/-1 direction structure (1M dominated by +1; 1p5M/2M by -1)",
                "tv_distance_q_vs_p_delta": float(0.5 * np.abs(q_delta - p_delta).sum()),
            },
            "conditional_tv_distances": {
                "measure": "total variation per conditioning value, aggregated mean/max",
                "U1_given_B_mean": float(tv1[valid_b].mean()), "U1_given_B_max": float(tv1.max()),
                "U2_given_B_U1_mean": float(tv2_vals.mean()), "U2_given_B_U1_max": float(tv2_vals.max()),
            },
            "dual_expected_nll": {
                "E_V25_nll_under_own_posterior_bits_per_symbol": {"L1": self_nll1,
                                                                  "L2": self_nll2},
                "E_Q_nll_under_V25_posterior_bits_per_symbol": {
                    "analytic": None if eq_analytic is None else eq_analytic,
                    "analytic_is_infinite_due_to_support_miss": analytic_inf,
                    "mc_mean": float(finite.mean()) if finite.size else None,
                    "mc_quantiles_bits_per_symbol": quantiles,
                    "mc_sample_size": mc["n_samples"],
                    "mc_seed": mc["seed"],
                },
                "self_reference_magnitude_check": "E_V25[NLL|own posterior] ~= V31 H.L1+H.L2 magnitudes (cross-checked in d2_feasibility.json)",
                "ratio_E_Q_over_self": None if not np.isfinite(ratio) else float(ratio),
            },
            "catastrophic_mismatch": bool(catastrophic),
            "thresholds_applied": thresholds,
        }

    result = {
        "schema": "nbldpc_v32_operating_point_audit_d1_v1",
        "q_definition": "Q_B1(b|a) = (1-raw_ser)*delta_{b=a} + raw_ser*Uniform{b != a mod 1024}; raw_ser quoted verbatim from V25 channel_summary.json per_source[sid].ser",
        "p_definition": "P = N_ab / total from channel_counts.npz key {sid}_N_ab_train_N_ab_train (verbatim on-disk key with duplicated suffix)",
        "mc_plan_frozen_in_manifest": mc,
        "per_source": per_source,
        "worst_expected_nll_ratio": None if not np.isfinite(worst_ratio) else float(worst_ratio),
        "signature_mismatch": any(v["catastrophic_mismatch"] for v in per_source.values()),
    }
    _write_json(run_root, "d1_consistency.json", result)

    md = ["# D1 — B1 generator/posterior consistency (read-only)", ""]
    rows = []
    for label, v in per_source.items():
        enll = v["dual_expected_nll"]["E_Q_nll_under_V25_posterior_bits_per_symbol"]["mc_mean"]
        rows.append([label, v["raw_ser"],
                     round(v["cross_entropy_H_QP_bits_over_common_support"], 4),
                     f"{v['support_miss']['q_mass_on_p_zero_cells']:.3e}",
                     round(enll, 4) if enll is not None else None,
                     round(v["conditional_tv_distances"]["U1_given_B_mean"], 4),
                     v["catastrophic_mismatch"]])
    md += ["", _md_table(["source", "ser", "H(Q,P)", "Q->Pzero mass", "E_Q NLL mc (bpsym)",
                          "TV U1|B mean", "catastrophic"], rows),
           "", "- Thresholds preregistered in audit_manifest.json before computation.",
           "- ±1 direction mass: Q uniform delta destroys the V25 structure (see per_source deltas)."]
    _write_text(run_root, "d1_consistency.md", "\n".join(md) + "\n")
    return result


# --------------------------------------------------------------------------- #
# D2 — feasibility vs actual rates
# --------------------------------------------------------------------------- #

def map_branch(l1_all_ok: bool, l2_all_ok: bool, total_verbatim_ok: bool,
               total_pure_ok: bool) -> dict:
    """Mechanical mapping onto exactly A/B/C/inconclusive (no fourth branch)."""
    reasons = []
    if not total_verbatim_ok and not total_pure_ok:
        branch = "A"
        reasons.append("total infeasible under both leakage definitions")
    elif total_verbatim_ok and total_pure_ok and l1_all_ok and l2_all_ok:
        branch = "C"
        reasons.append("layer-specific (L1,L2) and total feasibility hold for every source")
    elif total_verbatim_ok and total_pure_ok and not l2_all_ok:
        branch = "B"
        reasons.append("total feasible but L2 allocation infeasible for at least one source")
    else:
        branch = "inconclusive"
        if total_verbatim_ok != total_pure_ok:
            reasons.append("ambiguous: verbatim leak_total_bits and recomputed pure-syndrome totals disagree on feasibility")
        if not l1_all_ok and l2_all_ok:
            reasons.append("uncovered combination: L1-only infeasibility")
    return {"branch": branch, "reasons": reasons}


def run_d2(run_root: Path, paths: dict[str, Path], frozen: dict) -> dict:
    counts = load_counts_npz(paths["v25_channel_counts"])
    v31 = load_json(paths["v31_run_manifest"])
    audits = load_json(paths["v31_matrix_audits"])
    registry = load_json(paths["v31_m1_registry"])["registered_calls"]
    tol = frozen["h_cross_check_tol_bits"]

    packet = audits["packets"][0]
    m2_by_source_quote = packet.get("m2_by_source")

    reg_by_layer_src = {}
    for call in registry:
        reg_by_layer_src.setdefault((call["layer"], call["source"]), call)

    per_source, gaps = {}, {}
    for label, sid in SOURCE_IDS.items():
        N = counts[f"{sid}_N_ab_train_N_ab_train"]
        comp = layer_entropies(N)
        row31 = v31["configs"]["1024"]["sources"][label]
        drift = max(abs(comp["H_U1_given_B_bits"] - row31["H"]["L1"]),
                    abs(comp["H_U2_given_B_U1_bits"] - row31["H"]["L2"]))
        if drift > tol:
            raise AuditStop(
                EXIT_BINDING,
                f"binding drift STOP: recomputed H differs from V31 manifest beyond {tol} bits "
                f"for {label} (max diff {drift:.3e})",
            )

        m1, m2 = row31["m1"], row31["m2"]
        leak_verbatim = row31["leak_total_bits"]
        req_l1 = comp["H_U1_given_B_bits"] * N_SYMBOLS
        req_l2 = comp["H_U2_given_B_U1_bits"] * N_SYMBOLS
        req_total = comp["H_A_given_B_bits"] * N_SYMBOLS
        leak_l1_bits = m1 * BITS_PER_GF32
        leak_l2_bits = m2 * BITS_PER_GF32
        pure_syndrome_total_bits = (m1 + m2) * BITS_PER_GF32
        gaps[label] = {
            "gap_L1_bits": leak_l1_bits - req_l1,
            "gap_L2_bits": leak_l2_bits - req_l2,
            "gap_total_pure_syndrome_bits": pure_syndrome_total_bits - req_total,
            "gap_total_verbatim_leak_total_bits_bits": leak_verbatim - req_total,
        }
        per_source[label] = {
            "source_id": sid,
            "computed": comp,
            "v31_manifest_quoted": {
                "field_citation": f"nbldpc_v31_20260820/run_01/RUN_MANIFEST.json configs[\"1024\"].sources[{label}]",
                "H": row31["H"], "m1": m1, "m2": m2, "m_total": row31.get("m_total"),
                "leak_total_bits": leak_verbatim, "f_total": row31.get("f_total"),
            },
            "matrix_audits_quoted": {
                "packet_id": packet.get("packet_id"), "m2_by_source": m2_by_source_quote,
                "L1_shape": packet.get("audits", {}).get("L1", {}).get("shape"),
            },
            "m1_registry_quoted": {
                "L1": {k: reg_by_layer_src.get(("L1", label), {}).get(k) for k in
                       ("rate", "H_bits_per_symbol", "m1", "m2")},
                "L2": {k: reg_by_layer_src.get(("L2", label), {}).get(k) for k in
                       ("rate", "H_bits_per_symbol", "m1", "m2")},
            },
            "required_bits_n1024": {"L1": req_l1, "L2": req_l2, "total_chain_rule": req_total},
            "leakage_bits": {
                "L1_syndrome": leak_l1_bits,
                "L2_syndrome": leak_l2_bits,
                "total_pure_syndrome_recomputed": pure_syndrome_total_bits,
                "total_verbatim_leak_total_bits": leak_verbatim,
                "definitions_note": "verbatim manifest leak_total_bits includes budget overhead beyond the pure syndrome value; the two definitions are kept explicitly separate and never merged",
            },
            "margin_simple_gap_n1024": {
                **gaps[label],
                "ratio_L1_leakage_over_required": leak_l1_bits / req_l1 if req_l1 > 0 else None,
                "ratio_L2_leakage_over_required": leak_l2_bits / req_l2 if req_l2 > 0 else None,
                "ratio_total_pure": pure_syndrome_total_bits / req_total if req_total > 0 else None,
                "ratio_total_verbatim": leak_verbatim / req_total if req_total > 0 else None,
            },
            "feasible": {
                "L1": gaps[label]["gap_L1_bits"] >= 0,
                "L2": gaps[label]["gap_L2_bits"] >= 0,
                "total_pure_syndrome": gaps[label]["gap_total_pure_syndrome_bits"] >= 0,
                "total_verbatim": gaps[label]["gap_total_verbatim_leak_total_bits_bits"] >= 0,
            },
        }

    l1_ok = all(v["feasible"]["L1"] for v in per_source.values())
    l2_ok = all(v["feasible"]["L2"] for v in per_source.values())
    tot_v = all(v["feasible"]["total_verbatim"] for v in per_source.values())
    tot_p = all(v["feasible"]["total_pure_syndrome"] for v in per_source.values())

    margin_method = frozen["margin_method"]
    result = {
        "schema": "nbldpc_v32_operating_point_audit_d2_v1",
        "margin_method_frozen_in_manifest": margin_method,
        "h_cross_check_tol_bits": tol,
        "per_source": per_source,
        "layer_and_total_conclusions": {
            "L1_feasible_all_sources": l1_ok,
            "L2_allocation_feasible_all_sources": l2_ok,
            "total_feasible_verbatim_budget_all_sources": tot_v,
            "total_feasible_pure_syndrome_all_sources": tot_p,
            "conclusion_levels": "both mandatory levels reported: layer-specific (L1, L2) AND total",
        },
    }
    _write_json(run_root, "d2_feasibility.json", result)

    md = ["# D2 — Information-theoretic feasibility vs actual rates (read-only)", "",
          f"- margin method: {margin_method}", ""]
    rows = [[label,
             round(v["computed"]["H_U1_given_B_bits"], 6), round(v["computed"]["H_U2_given_B_U1_bits"], 6),
             round(v["computed"]["H_A_given_B_bits"], 6),
             v["v31_manifest_quoted"]["leak_total_bits"],
             round(gaps[label]["gap_L1_bits"], 2), round(gaps[label]["gap_L2_bits"], 2),
             round(gaps[label]["gap_total_verbatim_leak_total_bits_bits"], 2),
             all(v["feasible"].values())]
            for label, v in per_source.items()]
    md += [_md_table(["source", "H.U1|B", "H.U2|B,U1", "H.A|B", "leak_total(verbatim)",
                      "gap L1", "gap L2", "gap total(verb)", "feasible"], rows)]
    _write_text(run_root, "d2_feasibility.md", "\n".join(md) + "\n")

    result["_branch_inputs"] = {"l1_all_ok": l1_ok, "l2_all_ok": l2_ok,
                                "total_verbatim_ok": tot_v, "total_pure_ok": tot_p}
    return result


# --------------------------------------------------------------------------- #
# D3 — existing DE evidence, read-only
# --------------------------------------------------------------------------- #

def run_d3(run_root: Path, paths: dict[str, Path], frozen: dict) -> dict:
    del frozen  # d3 uses no tunable constants
    gate = load_json(paths["v26_gate"])
    man = load_json(paths["v26_run_manifest"])
    screen = load_json(paths["v26_screen_results"])
    confirm = load_json(paths["v26_confirmation_results"])
    m0 = load_json(paths["v26_m0_report"])
    m1rep = load_json(paths["v26_m1_report"])
    audits = load_json(paths["v31_matrix_audits"])
    registry = load_json(paths["v31_m1_registry"])["registered_calls"]
    v31 = load_json(paths["v31_run_manifest"])

    code_facts = {
        "de_sampler_draws_AB_from_P_AB": {
            "citation": "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_channel.py L10-13",
            "fact": "(A,B) sampled directly from the train joint P(A,B)=N_ab/total; sources independent; ±1 directions preserved",
        },
        "b1_generator_did_not_replicate_that_channel": {
            "citation": "comparison_bench/src/comparison_bench/cli/run_nonbinary_v32_finite_de_bridge.py L555-564 (synth_channel_sample)",
            "fact": "uniform alice + Bernoulli(raw_ser) substitution with uniform nonzero delta mod 1024 — not the empirical-joint sampler used by the V26 DE",
        },
    }

    def _headline(doc: dict) -> dict:
        keep = {}
        for k in ("status", "terminal_state", "target_f", "best_passing_f", "passed",
                  "screen_state", "confirm_state", "schema", "role"):
            if isinstance(doc, dict) and k in doc:
                keep[k] = doc[k]
        return keep

    comparison = {
        "v26_de_design_constants_quoted_from_RUN_MANIFEST.design_constants": man.get("design_constants"),
        "v32_qc_packet_identity_quoted": {
            "packet_id": audits["packets"][0].get("packet_id"),
            "m1": audits["packets"][0].get("m1"),
            "m2_by_source": audits["packets"][0].get("m2_by_source"),
            "registry_rates_H_per_layer_source": [
                {"layer": c["layer"], "source": c["source"], "rate": c["rate"],
                 "H_bits_per_symbol": c["H_bits_per_symbol"]} for c in registry
            ],
        },
        "numeric_side_by_side": {
            "note": "V26 DE was evaluated on the empirical-joint sampler; the V32 QC packet numbers below are the rate/entropy parameters that a corrected operating-point DE would have to reproduce",
            "gate_best_passing_f": gate.get("best_passing_f"),
            "v31_configs_1024_sources_H": {lbl: v31["configs"]["1024"]["sources"][lbl]["H"]
                                           for lbl in SOURCE_IDS},
        },
    }

    missing_fields = [k for k, v in {
        "screen_operating_point": _headline(screen).get("passed"),
        "confirmation_operating_point": _headline(confirm).get("passed"),
    }.items() if v in (None, [], {})]

    new_de_required = True  # generator != DE sampler semantics confirmed at stage 0
    result = {
        "schema": "nbldpc_v32_operating_point_audit_d3_v1",
        "code_facts_cited_verbatim": code_facts,
        "v26_pass_location": {
            "gate_status": gate.get("status"),
            "best_passing_f": gate.get("best_passing_f"),
            "run_manifest_terminal_state": man.get("terminal_state"),
            "m0_report_headline": _headline(m0),
            "m1_report_headline": _headline(m1rep),
            "screen_results_headline": _headline(screen),
            "confirmation_results_headline": _headline(confirm),
        },
        "v26_vs_v32_comparison": comparison,
        "operating_point_gaps_detected": missing_fields,
        "new_DE_change_required": new_de_required,
        "new_DE_change_required_reason": (
            "existing V26 DE evidence covers the empirical-joint sampler operating point only; "
            "it cannot answer whether the QC graph passes at the corrected matched-control "
            "generator law Q_B1 (the B1 generator did not replicate the DE channel)"
        ),
        "minimal_DE_question_list": DE_QUESTIONS,
        "no_DE_executed_inside_this_change": True,
    }
    _write_json(run_root, "d3_v26_evidence.json", result)

    md = ["# D3 — Existing DE evidence (read-only inspection)", ""]
    md += [f"- gate status: `{gate.get('status')}` best_passing_f: `{gate.get('best_passing_f')}`",
            f"- new_DE_change_required: **{new_de_required}**",
            "", "## Code facts", "",
            f"```python\n{code_facts['de_sampler_draws_AB_from_P_AB']['citation']}\n"
            f"{paths['code_fact_sampler'].read_text(encoding='utf-8').splitlines()[9]}...\n```",
            "", "## Minimal DE questions", ""]
    md += [f"{i}. {q}" for i, q in enumerate(DE_QUESTIONS, 1)]
    _write_text(run_root, "d3_v26_evidence.md", "\n".join(md) + "\n")
    return result


# --------------------------------------------------------------------------- #
# Final branch decision
# --------------------------------------------------------------------------- #

def write_final_branch_decision(run_root: Path, d0_result: dict, d2_result: dict) -> dict:
    bi = d2_result["_branch_inputs"]
    decision = map_branch(bi["l1_all_ok"], bi["l2_all_ok"],
                          bi["total_verbatim_ok"], bi["total_pure_ok"])
    payload = {
        "schema": "nbldpc_v32_operating_point_audit_branch_decision_v1",
        "branch_table_frozen": BRANCH_TABLE,
        "selected_branch": decision["branch"],
        "selection_reasons": decision["reasons"],
        "branch_inputs": bi,
        "d0_signature_mismatch": d0_result.get("signature_mismatch"),
        "generated_by_execution_order": ["manifest_freeze", "d0", "d1", "d2", "d3",
                                         "final_branch_decision"],
    }
    _write_json(run_root, "final_branch_decision.json", payload)
    return payload


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _require_outputs_absent(run_root: Path, names: list[str]) -> None:
    for n in names:
        if (Path(run_root) / n).exists():
            raise AuditStop(EXIT_COLLISION, f"output collision: {n} already exists in {run_root}")


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_nonbinary_v32_operating_point_audit.py",
        description="Read-only operating-point consistency audit (NB-LDPC V32). "
                    "No DE rerun, no decoder invocation, no raw capture access.")
    parser.add_argument("subcommand", choices=["d0", "d1", "d2", "d3", "all"])
    parser.add_argument("--runner", default=None, metavar="MODULE:ATTR",
                        help="binding provider injection for tests (default: real repo bindings)")
    parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT),
                        help="audit run root (default: frozen run_01 path)")
    args = parser.parse_args(argv)

    run_root = Path(args.run_root)
    stage_files = ["d0_signature.json", "d1_consistency.json", "d2_feasibility.json",
                   "d3_v26_evidence.json", "final_branch_decision.json"]

    try:
        if args.subcommand == "all":
            if run_root.exists():  # STOP: implementation/output collision
                raise AuditStop(EXIT_COLLISION,
                                f"run root already exists -> STOP implementation/output "
                                f"collision: {run_root} (no overwrite, no automatic run_02)")
            run_root.mkdir(parents=True)
            runner = load_runner(args.runner)
            binding_rows, code_facts = stage0_bindings(runner.binding_paths())
            manifest = freeze_manifest(run_root, binding_rows, code_facts)
            frozen = manifest["frozen"]
            paths = runner.binding_paths()
            d0r = run_d0(run_root, paths, frozen)
            d1r = run_d1(run_root, paths, frozen)
            d2r = run_d2(run_root, paths, frozen)
            run_d3(run_root, paths, frozen)
            write_final_branch_decision(run_root, d0r, d2r)
        else:
            runner = load_runner(args.runner)
            manifest = verify_manifest(run_root, runner)
            frozen = manifest["frozen"]
            paths = runner.binding_paths()
            if args.subcommand == "d0":
                _require_outputs_absent(run_root, ["d0_signature.json", "d0_signature.md"])
                run_d0(run_root, paths, frozen)
            elif args.subcommand == "d1":
                _require_outputs_absent(run_root, ["d1_consistency.json", "d1_consistency.md"])
                run_d1(run_root, paths, frozen)
            elif args.subcommand == "d2":
                _require_outputs_absent(run_root, ["d2_feasibility.json", "d2_feasibility.md"])
                run_d2(run_root, paths, frozen)
            elif args.subcommand == "d3":
                _require_outputs_absent(run_root, ["d3_v26_evidence.json", "d3_v26_evidence.md"])
                run_d3(run_root, paths, frozen)
    except AuditStop as stop:
        print(f"STOP[{stop.code}]: {stop.reason}", file=sys.stderr)
        return stop.code
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(cli_main())
