"""V32 finite-de bridge diagnostic harness.

Single-purpose attribution harness for the frozen V31 n=1024 finite-graph
failure.  Executes six pre-registered arms (B5 import + B0..B4 decode arms)
against read-only canonical bindings, persists per-block evidence, enforces a
12h cumulative wall-clock budget with exact resume, and maps the observed
pattern onto exactly one of nine frozen terminals via the design.md §5 truth
table.  This is a diagnostic bridge only: no qualification, promotion, new
reconciler, or V31-completion semantics exist here.

Frozen scope: openspec/changes/formal-nonbinary-ldpc-v32-finite-de-bridge-diagnostic/
All canonical roots are opened strictly read-only; every write resolves under
the single unique run root.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import time
import traceback
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

# ---------------------------------------------------------------------------
# Frozen constants (identical across proposal/design/tasks/spec — do not edit)
# ---------------------------------------------------------------------------

FIELD_ID = "c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf"
FIELD_POLY = 0b100101
M1_FROZEN = 16
N_FROZEN = 1024

SOURCE_ORDER = ("1M", "1p5M", "2M")
SOURCE_IDS = {
    "1M": "type2_1M_20260121_184040",
    "1p5M": "type2_1p5M_20260121_183806",
    "2M": "type2_2M_20260121_183657",
}
PACKET_ID_FROZEN = "m1_16_n1024_n1024|QC-cyclic-projective"

# B1/B2 frozen seeds (proposal SHALL-A2).
SEEDS_B1_B2 = {
    "1M": tuple(range(320101, 320121)),
    "1p5M": tuple(range(320201, 320221)),
    "2M": tuple(range(320301, 320321)),
}
# B3/B4 real block set: EXACTLY blocks 0..19 per source (P1.4 ruling f).
REAL_BLOCK_IDS = tuple(range(20))
B0_BLOCKS_PER_SOURCE = 2
SYNTH_BLOCKS_PER_SOURCE = 20
PERM_SEED_FROZEN = 20260822  # B3 permutation base seed (pre-frozen)

BUDGET_SECONDS = 12 * 3600

REPO_REL_V31 = "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01"
REPO_REL_V25 = "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04"
REPO_REL_V26 = "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v26_20260818/run_02"
REPO_REL_RUN_ROOT = (
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
    "nbldpc_v32_finite_de_bridge/run_01"
)

TERMINALS = (
    "bridge_binding_fail",
    "finite_graph_decoder_mismatch",
    "l1_sequential_propagation_limit",
    "real_error_structure_mismatch",
    "empirical_channel_model_mismatch",
    "bridge_pass_ready_for_successor",
    "bridge_inconclusive",
    "resource_blocked",
    "implementation_blocked",
)
# Scientific terminals are final; resume is allowed only from operational stops.
SCIENTIFIC_FINAL = frozenset({
    "finite_graph_decoder_mismatch", "l1_sequential_propagation_limit",
    "real_error_structure_mismatch", "empirical_channel_model_mismatch",
    "bridge_pass_ready_for_successor", "bridge_inconclusive",
    "bridge_binding_fail",
})
RESUMABLE_TERMINALS = frozenset({"resource_blocked", "implementation_blocked"})

# Early-stop whitelist (exhaustive, design §4.5) — exactly seven items.
WHITELIST_BINDING_FAILURE = "binding_failure"
WHITELIST_B0_FAILURE = "b0_failure"
WHITELIST_IMPLEMENTATION_EXCEPTION = "implementation_exception"
WHITELIST_OUTPUT_COLLISION = "output_collision"
WHITELIST_BUDGET_EXHAUSTED = "cumulative_12h_exhausted"
WHITELIST_CANONICAL_DRIFT = "canonical_input_drift"
WHITELIST_TRUTH_USE_VIOLATION = "truth_use_violation"
EARLY_STOP_WHITELIST = (
    WHITELIST_BINDING_FAILURE, WHITELIST_B0_FAILURE,
    WHITELIST_IMPLEMENTATION_EXCEPTION, WHITELIST_OUTPUT_COLLISION,
    WHITELIST_BUDGET_EXHAUSTED, WHITELIST_CANONICAL_DRIFT,
    WHITELIST_TRUTH_USE_VIOLATION,
)

EXECUTION_ORDER = (
    "binding_verification", "B5", "B0", "B1", "B2", "B3", "B4",
    "terminal_reconstruction",
)

ARMS_DECODED = ("B0", "B1", "B2", "B3", "B4")
TRUTH_MARKERS_ORACLE = {"truth_used": True, "truth_role": "oracle_l1",
                        "operational": False, "qualification": False}

# Pre-registered posterior-anomaly constants (recorded into RUN_MANIFEST
# before any arm executes; never tuned after results).
ANOM_P_TRUE_MIN = 0.05      # block anomalous if mean true-symbol prior prob below this
ANOM_FRACTION = 0.25        # arm-level anomaly if anomalous fraction of B3+B4 above this
DEFAULT_MAX_ITER = 30
DEFAULT_STREAK = 20         # V30/V31 production streak binding

BLOCK_SCHEMA = "nbldpc_v32_bridge_block_result_v1"
MANIFEST_SCHEMA = "nbldpc_v32_run_manifest_v1"


class BridgeStop(Exception):
    """Whitelisted stop condition (design §4.5)."""

    def __init__(self, kind: str, detail: str = ""):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail


class ResumeRefused(Exception):
    """Exact-resume precondition violated (design §4.3)."""


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _repo_root_default() -> Path:
    # .../comparison_bench/src/comparison_bench/cli/<this file> → repo root
    return Path(__file__).resolve().parents[4]


def _load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:  # read-only canonical access
        return json.load(fh)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise BridgeStop(
                    "evidence_inconsistent",
                    f"malformed JSONL at {path.name}:{lineno}: {exc}") from exc
    return out


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _factor_layers(symbols_1024: Sequence[int]) -> tuple[list[int], list[int]]:
    """F03 natural MSB->LSB split of GF(1024) symbols into two GF(32) layers."""
    vals = np.asarray(symbols_1024, dtype=np.int64)
    if vals.ndim != 1 or vals.shape[0] != N_FROZEN:
        raise ValueError(f"F03 input must have length {N_FROZEN}")
    if np.any(vals < 0) or np.any(vals >= 1024):
        raise ValueError("F03 symbols outside 10-bit domain")
    return ((vals >> 5) & 31).tolist(), (vals & 31).tolist()


def tag64(x1: Sequence[int] | None, x2: Sequence[int] | None) -> str:
    payload = bytes(int(v) & 0xFF for v in x1) if x1 is not None else b""
    payload += bytes(int(v) & 0xFF for v in x2) if x2 is not None else b""
    return hashlib.sha256(payload).digest()[:8].hex()


def b0_seed(source: str, index: int) -> int:
    """Deterministic B0 seed constant, recorded in RUN_MANIFEST pre-execution."""
    payload = f"nbldpc-v32-B0:{SOURCE_IDS[source]}:{index}".encode("ascii")
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


# ---------------------------------------------------------------------------
# Stage 0 — nine frozen binding verifications (strictly read-only)
# ---------------------------------------------------------------------------

def verify_bindings(repo_root: Path) -> dict[str, Any]:
    """Verify all nine frozen input bindings read-only; return their identities.

    Raises BridgeStop(WHITELIST_BINDING_FAILURE) on any mismatch.
    """
    problems: list[str] = []
    ident: dict[str, Any] = {}

    def need(cond: bool, msg: str) -> None:
        if not cond:
            problems.append(msg)

    v31 = repo_root / REPO_REL_V31
    v25 = repo_root / REPO_REL_V25
    v26 = repo_root / REPO_REL_V26

    # (1) canonical V31 n=1024 QC packet
    aud_path, pay_path = v31 / "matrix_audits.json", v31 / "matrix_payloads.json"
    packet_rec = None
    try:
        need(aud_path.is_file() and pay_path.is_file(), "binding1: QC packet files missing")
        if aud_path.is_file():
            audits = _load_json(aud_path)
            pkts = [p for p in audits.get("packets", [])
                    if p.get("packet_id") == PACKET_ID_FROZEN]
            need(len(pkts) == 1, f"binding1: accepted packet {PACKET_ID_FROZEN} not unique")
            packet_rec = pkts[0] if pkts else None
            if packet_rec is not None:
                need(packet_rec.get("family") == "QC-cyclic-projective",
                     "binding1: family mismatch")
                need(int(packet_rec.get("n", -1)) == N_FROZEN, "binding1: n != 1024")
                need(int(packet_rec.get("m1", -1)) == M1_FROZEN, "binding1: m1 != 16")
                need(pay_path.stat().st_size > 0, "binding1: empty matrix_payloads.json")
                ident["v31_packet_sha256"] = _sha256_file(pay_path)
                ident["graph_packet_identity"] = ident["v31_packet_sha256"][:16]
                ident["packet_id"] = PACKET_ID_FROZEN
    except BridgeStop:
        raise
    except Exception as exc:  # malformed canonical file
        problems.append(f"binding1 unreadable: {exc}")

    # (2) V31 n=1024 validation blocks/frames
    try:
        vb_path, vf_path = v31 / "validation_blocks_n1024.json", v31 / "validation_frames_n1024.json"
        need(vb_path.is_file() and vf_path.is_file(), "binding2: validation files missing")
        blocks_doc = _load_json(vb_path)
        need(blocks_doc.get("schema") == "nbldpc_v31_validation_blocks_v1024",
             "binding2: validation blocks schema mismatch")
        need(int(blocks_doc.get("n", -1)) == N_FROZEN, "binding2: n != 1024")
        blocks = blocks_doc.get("blocks", [])
        need(len(blocks) == 300, f"binding2: expected 300 blocks, got {len(blocks)}")
        seen_src: dict[str, int] = {}
        for blk in blocks:
            lbl = blk.get("source")
            seen_src[lbl] = seen_src.get(lbl, 0) + 1
            need(blk.get("source_id") == SOURCE_IDS.get(lbl),
                 f"binding2: source_id mismatch for {lbl}")
        for lbl in SOURCE_ORDER:
            need(seen_src.get(lbl) == 100, f"binding2: {lbl} block count != 100")
        # deep length check only on the consumed B3/B4 subset (blocks 0..19/source)
        for lbl in SOURCE_ORDER:
            own = sorted((b for b in blocks if b.get("source") == lbl),
                         key=lambda b: int(b.get("block_index", -1)))[:20]
            for blk in own:
                for key in ("alice_symbols", "bob_symbols"):
                    arr = blk.get(key)
                    need(isinstance(arr, list) and len(arr) == N_FROZEN,
                         f"binding2: {lbl} block {blk.get('block_index')} {key} length")
        frames = _load_json(vf_path)
        need(frames.get("schema") == "nbldpc_v31_frame_manifest_v1",
             "binding2: frame manifest schema mismatch")
        ident["validation_blocks_sha256"] = _sha256_file(vb_path)
    except BridgeStop:
        raise
    except Exception as exc:
        problems.append(f"binding2 unreadable: {exc}")

    # (3) V31 n=1024 per-block baseline (300 lines)
    try:
        pb_path = v31 / "per_block_n1024.jsonl"
        need(pb_path.is_file(), "binding3: per_block_n1024.jsonl missing")
        baseline = _read_jsonl(pb_path)
        need(len(baseline) == 300, f"binding3: expected 300 baseline records, got {len(baseline)}")
        cnt: dict[str, int] = {}
        for rec in baseline:
            cnt[rec.get("source")] = cnt.get(rec.get("source"), 0) + 1
            need(rec.get("packet_id") == PACKET_ID_FROZEN,
                 "binding3: baseline packet_id mismatch")
        for lbl in SOURCE_ORDER:
            need(cnt.get(lbl) == 100, f"binding3: {lbl} baseline count != 100")
        ident["baseline_records"] = len(baseline)
        ident["baseline_sha256"] = _sha256_file(pb_path)
    except BridgeStop:
        raise
    except Exception as exc:
        problems.append(f"binding3 unreadable: {exc}")

    # (4) V25 run_04 empirical channel
    try:
        cc, di, sm = v25 / "channel_counts.npz", v25 / "data_inventory.json", v25 / "split_manifest.json"
        need(cc.is_file() and di.is_file() and sm.is_file(),
             "binding4: V25 run_04 channel files missing")
        inv = _load_json(di)
        per_src = inv.get("primary_joint_data_sources") or inv.get("per_source") or {}
        ids_found = set()
        if isinstance(per_src, list):
            ids_found = {row.get("source_id") for row in per_src}
        elif isinstance(per_src, dict):
            ids_found = set(per_src.keys())
        for sid in SOURCE_IDS.values():
            need(sid in ids_found, f"binding4: V25 inventory missing {sid}")
        ident["channel_counts_sha256"] = _sha256_file(cc)
        ident["posterior_identity"] = ident["channel_counts_sha256"][:16]
    except BridgeStop:
        raise
    except Exception as exc:
        problems.append(f"binding4 unreadable: {exc}")

    # (5) V26 run_02 F03/A02 allocation
    try:
        man = _load_json(v26 / "RUN_MANIFEST.json")
        need(man.get("schema") == "nbldpc_v26_run_manifest_v1",
             "binding5: V26 manifest schema mismatch")
        meta = man.get("source_metadata", {})
        for sid in SOURCE_IDS.values():
            need(sid in meta, f"binding5: V26 metadata missing {sid}")
        ident["v26_terminal_state"] = man.get("terminal_state")
    except BridgeStop:
        raise
    except Exception as exc:
        problems.append(f"binding5 unreadable: {exc}")

    # (6) V28R decoder interface (import authority only — never invoked here)
    try:
        from ..formal_ir import nonbinary_v28 as v28  # noqa: F401  (interface check)
        need(callable(getattr(v28, "decode_error_domain_posterior", None)),
             "binding6: V28R decode_error_domain_posterior not callable")
        cfg_field = getattr(v28.frozen_v28_config(), "get", lambda *_: None)("field_id")
        need(cfg_field == FIELD_ID, "binding6: V28R config field_id mismatch")
    except BridgeStop:
        raise
    except Exception as exc:
        problems.append(f"binding6: V28R interface unavailable: {exc}")

    # (7) GF(32) field identity
    try:
        from ..formal_ir.nonbinary_field import GF2mField
        spec = GF2mField.create(32).spec
        need(spec.field_id == FIELD_ID, "binding7: field_id mismatch")
        need(spec.primitive_polynomial == FIELD_POLY, "binding7: primitive polynomial mismatch")
        ident["field_id"] = spec.field_id
        ident["field_polynomial"] = bin(spec.primitive_polynomial)
    except BridgeStop:
        raise
    except Exception as exc:
        problems.append(f"binding7: field backend unavailable: {exc}")

    # (8) allocation scalar m1=16 in the V31 frozen config
    try:
        rm = _load_json(v31 / "RUN_MANIFEST.json")
        cfg = (rm.get("configs") or {}).get("1024") or {}
        need(int(cfg.get("m1", -1)) == M1_FROZEN, "binding8: V31 config m1 != 16")
    except BridgeStop:
        raise
    except Exception as exc:
        problems.append(f"binding8 unreadable: {exc}")

    # (9) three frozen source IDs — already cross-checked inside bindings
    # 2/4/5 against canonical files; assert the frozen map itself has not
    # drifted from the spec table.
    need(SOURCE_IDS == {
        "1M": "type2_1M_20260121_184040",
        "1p5M": "type2_1p5M_20260121_183806",
        "2M": "type2_2M_20260121_183657",
    }, "binding9: frozen source ID table drifted")

    if problems:
        raise BridgeStop(WHITELIST_BINDING_FAILURE, "; ".join(problems))
    ident["verified_utc"] = _utcnow()
    return ident


# ---------------------------------------------------------------------------
# Posterior provider (bound V25/V26 empirical posterior; injectable for tests)
# ---------------------------------------------------------------------------

def ident_sha(path: Path) -> str:
    return _sha256_file(path)[:16]


def production_posterior_factory(repo_root: Path):
    """Build the bound V26 empirical posterior provider bundle."""
    from ..formal_ir.nonbinary_v26_channel import build_adapter, load_channel_counts
    counts_path = repo_root / REPO_REL_V25 / "channel_counts.npz"
    counts = load_channel_counts(counts_path)
    adapters = {lbl: build_adapter(counts, fact_id="F03", source=sid)
                for lbl, sid in SOURCE_IDS.items()}
    ent = {}
    from ..formal_ir.nonbinary_v26_channel import adapter_entropy_bits
    for lbl, ad in adapters.items():
        ent[lbl] = float(sum(adapter_entropy_bits(ad).values()))

    def rows_for(label: str) -> Callable[[str, Sequence[int], Sequence[int] | None], np.ndarray]:
        ad = adapters[label]

        def rows(lid: str, bob: Sequence[int], u1: Sequence[int] | None = None) -> np.ndarray:
            b = np.asarray(bob, dtype=np.int64)
            u = None if u1 is None else np.asarray(u1, dtype=np.int64)
            return ad.posterior_rows(lid, b, u)
        return rows

    return {
        "identity": f"v26_a02_f03:{ident_sha(counts_path)}",
        "rows_for": rows_for,
        "entropy_bits": ent,
    }


# ---------------------------------------------------------------------------
# Production block runner (binds the frozen V28R decode interface)
# ---------------------------------------------------------------------------

FORBIDDEN_REQUEST_SUBSTRINGS = ("alice", "truth", "_symbols")


def audit_decoder_input(request: Mapping[str, Any]) -> None:
    """Truth-use boundary: no undeclared truth ever enters a runner request.

    B2 must additionally carry no prebuilt L2 prior (pure Bob-only sequential);
    B3's declared oracle conditioning arrives solely as ``prior_l2`` rows built
    by the harness from the marked oracle mechanism (P1.4 ruling a/c).
    """
    for key in request:
        low = key.lower()
        if any(tok in low for tok in FORBIDDEN_REQUEST_SUBSTRINGS):
            raise BridgeStop(
                WHITELIST_TRUTH_USE_VIOLATION,
                f"forbidden key '{key}' in decoder input for {request.get('arm')}")
    if request.get("arm") == "B2":
        if request.get("prior_l2") is not None or request.get("l1_mode") != "sequential":
            raise BridgeStop(WHITELIST_TRUTH_USE_VIOLATION,
                             "B2 received oracle-conditioned L2 prior")


class ProductionRunner:
    """Bob-only GF(32) FFT-QSPA decode via the frozen V28R interface.

    Oracle arms (B1/B3/B4) receive ``prior_l2`` prebuilt by the harness from
    the declared oracle-L1 conditioning; the runner itself never sees Alice
    truth arrays.  Sequential arms (B0/B2) call ``posterior_provider`` for L2
    conditioned on the RETURNED x1_hat (never Alice data).
    """

    def __init__(self, repo_root: Path, packet_identity: str):
        from ..formal_ir import nonbinary_v28 as v28
        from ..formal_ir.nonbinary_field import GF2mField
        self._v28 = v28
        self.field = GF2mField.create(32)
        self.matrices = load_packet_matrices(repo_root, packet_identity)

    def run_block(self, request: Mapping[str, Any]) -> dict[str, Any]:
        v28 = self._v28
        field = self.field
        label = request["source"]
        h1 = self.matrices["L1"]
        h2 = self.matrices["L2"][label]
        y1, y2 = request["y1"], request["y2"]
        s1, s2 = request["s1"], request["s2"]
        max_iter = int(request.get("max_iter", DEFAULT_MAX_ITER))
        streak = int(request.get("streak", DEFAULT_STREAK))

        if request.get("l1_mode") == "oracle":
            # prior_l2 arrives as value-domain P(U2|B,U1) rows from the bound
            # posterior; decode_error_domain_posterior contracts P(E_i), so
            # center on the observation exactly like the sequential path.
            prior2 = v28._center_rows(field, np.asarray(request["prior_l2"], dtype=np.float64),
                                      np.asarray(y2, dtype=np.int64))
            r2 = v28.decode_error_domain_posterior(
                field, y2, h2, s2, np.asarray(prior2, dtype=np.float64),
                max_iter, streak=streak)
            l2_ok = bool(r2.get("reconstruction_ok")) and bool(r2.get("syndrome_ok"))
            resid2 = _unsat_count(field, h2, r2.get("x_hat"), s2)
            return {
                "l1_status": "oracle_not_decoded", "l2_status": str(r2.get("status")),
                "l1_iterations": 0, "l2_iterations": int(r2.get("iterations", 0)),
                "l1_syndrome_ok": None, "l2_syndrome_ok": bool(r2.get("syndrome_ok")),
                "x1_hat": None,          # harness substitutes oracle x1 for evaluation
                "x2_hat": r2.get("x_hat"),
                "unsatisfied_checks": resid2,
            }

        # sequential Bob-only plumbing (B0/B2)
        provider = request["posterior_provider"]
        prior1 = v28._center_rows(field, provider("L1", None), np.asarray(y1, dtype=np.int64))
        r1 = v28.decode_error_domain_posterior(
            field, y1, h1, s1, prior1, max_iter, streak=streak)
        resid1 = _unsat_count(field, h1, r1.get("x_hat"), s1)
        l1_ok = bool(r1.get("reconstruction_ok")) and bool(r1.get("syndrome_ok"))
        if not l1_ok:
            return {
                "l1_status": str(r1.get("status")), "l2_status": "not_run",
                "l1_iterations": int(r1.get("iterations", 0)), "l2_iterations": 0,
                "l1_syndrome_ok": bool(r1.get("syndrome_ok")), "l2_syndrome_ok": False,
                "x1_hat": r1.get("x_hat"), "x2_hat": None,
                "unsatisfied_checks": resid1,
            }
        x1_hat = r1.get("x_hat")
        rows2 = provider("L2", x1_hat)  # returned decoder output, never Alice data
        prior2 = v28._center_rows(field, rows2, np.asarray(y2, dtype=np.int64))
        r2 = v28.decode_error_domain_posterior(
            field, y2, h2, s2, prior2, max_iter, streak=streak)
        resid2 = _unsat_count(field, h2, r2.get("x_hat"), s2)
        return {
            "l1_status": str(r1.get("status")), "l2_status": str(r2.get("status")),
            "l1_iterations": int(r1.get("iterations", 0)),
            "l2_iterations": int(r2.get("iterations", 0)),
            "l1_syndrome_ok": bool(r1.get("syndrome_ok")),
            "l2_syndrome_ok": bool(r2.get("syndrome_ok")),
            "x1_hat": x1_hat, "x2_hat": r2.get("x_hat"),
            "unsatisfied_checks": resid1 + resid2,
        }


def _unsat_count(field, matrix, x_hat: Sequence[int] | None, s_target: Sequence[int]) -> int:
    if x_hat is None:
        return len(s_target)
    got = field_mul_syndrome(matrix, list(x_hat), field)
    return sum(1 for a, b in zip(got, s_target) if int(a) != int(b))


def field_mul_syndrome(matrix, symbols, field) -> list[int]:
    from ..formal_ir.nonbinary_qspa import nonbinary_syndrome
    return [int(v) for v in nonbinary_syndrome(matrix, symbols, field)]


def load_packet_matrices(repo_root: Path, packet_identity: str) -> dict[str, Any]:
    """Read-only import of the bound V31 n=1024 QC packet matrices."""
    doc = _load_json(repo_root / REPO_REL_V31 / "matrix_payloads.json")
    pkt = next((p for p in doc.get("packets", []) if p.get("packet_id") == PACKET_ID_FROZEN), None)
    if pkt is None:
        raise BridgeStop(WHITELIST_CANONICAL_DRIFT, "bound QC packet missing from payloads")
    mats = pkt.get("matrices") or {}
    if ident_sha(repo_root / REPO_REL_V31 / "matrix_payloads.json") != packet_identity:
        raise BridgeStop(WHITELIST_CANONICAL_DRIFT, "matrix payload hash drifted vs manifest")
    return mats


# ---------------------------------------------------------------------------
# Public fixture builders (harness-owned; truth never leaves the harness)
# ---------------------------------------------------------------------------

def synth_channel_sample(seed: int, p_ser: float) -> tuple[list[int], list[int]]:
    """Matched iid synthetic channel: uniform GF(1024) words, iid substitution
    with probability ``p_ser`` (frozen V25 raw_ser), replacement delta uniform
    in [1,1023] added modulo 1024."""
    rng = np.random.default_rng(seed)
    alice = rng.integers(0, 1024, size=N_FROZEN, dtype=np.int64)
    mask = rng.random(N_FROZEN) < float(p_ser)
    deltas = rng.integers(1, 1024, size=N_FROZEN, dtype=np.int64)
    bob = np.where(mask, (alice + deltas) % 1024, alice)
    return alice.tolist(), bob.tolist()


def real_error_vector(alice: Sequence[int], bob: Sequence[int]) -> np.ndarray:
    a = np.asarray(alice, dtype=np.int64)
    b = np.asarray(bob, dtype=np.int64)
    return (b - a) % 1024


def permute_error_vector(errors: np.ndarray, global_block_key: str) -> np.ndarray:
    """Pre-frozen B3 permutation rule: position permutation seeded by
    PERM_SEED_FROZEN + stable block key; preserves per-block error count and
    value marginals exactly (positions only)."""
    digest = int.from_bytes(
        hashlib.sha256(f"{PERM_SEED_FROZEN}:{global_block_key}".encode()).digest()[:4], "big")
    rng = np.random.default_rng(digest)
    perm = rng.permutation(len(errors))
    return np.asarray(errors, dtype=np.int64)[perm]


def load_real_validation_block(repo_root: Path, label: str, block_index: int) -> dict[str, Any]:
    doc = _load_json(repo_root / REPO_REL_V31 / "validation_blocks_n1024.json")
    for blk in doc.get("blocks", []):
        if blk.get("source") == label and int(blk.get("block_index", -1)) == block_index:
            return blk
    raise BridgeStop(WHITELIST_CANONICAL_DRIFT,
                     f"validation block {label}/{block_index} missing")


def v25_raw_ser(repo_root: Path) -> dict[str, float]:
    inv = _load_json(repo_root / REPO_REL_V25 / "data_inventory.json")
    rows = inv.get("primary_joint_data_sources") or []
    out = {}
    for row in rows:
        sid = row.get("source_id")
        for lbl, sid_frozen in SOURCE_IDS.items():
            if sid == sid_frozen:
                out[lbl] = float(row.get("raw_ser"))
    missing = [lbl for lbl in SOURCE_ORDER if lbl not in out]
    if missing:
        raise BridgeStop(WHITELIST_BINDING_FAILURE, f"raw_ser missing for {missing}")
    return out


# ---------------------------------------------------------------------------
# Schedules (fixed, shared by B1/B2 so block sets are provably identical)
# ---------------------------------------------------------------------------

def b1_b2_schedule() -> list[dict[str, Any]]:
    sched = []
    for label in SOURCE_ORDER:
        for seed in SEEDS_B1_B2[label]:
            sched.append({"source": label, "seed": int(seed)})
    return sched


def b3_b4_schedule() -> list[dict[str, Any]]:
    sched = []
    for label in SOURCE_ORDER:
        for block_index in REAL_BLOCK_IDS:
            sched.append({"source": label, "block_index": int(block_index)})
    return sched


def b0_schedule() -> list[dict[str, Any]]:
    sched = []
    for label in SOURCE_ORDER:
        for index in range(B0_BLOCKS_PER_SOURCE):
            sched.append({"source": label, "index": index, "seed": b0_seed(label, index)})
    return sched


# ---------------------------------------------------------------------------
# Run state: ledger / progress / per-block JSONL (single-run-root writes only)
# ---------------------------------------------------------------------------

class RunState:
    def __init__(self, run_root: Path, budget_seconds: float):
        self.root = run_root
        self.budget_seconds = float(budget_seconds)
        self._t_last = time.monotonic()
        now = _utcnow()
        ledger_path = self.root / "resource_ledger.json"
        if ledger_path.exists():
            self.ledger = _load_json(ledger_path)
        else:
            self.ledger = {
                "schema": "nbldpc_v32_resource_ledger_v1",
                "budget_seconds": self.budget_seconds,
                "cumulative_seconds": 0.0,
                "created_utc": now,
                "resume_events": [],
            }
        self.progress_path = self.root / "progress.json"
        if self.progress_path.exists():
            self.progress = _load_json(self.progress_path)
        else:
            self.progress = {
                "schema": "nbldpc_v32_progress_v1",
                "arms_completed": [], "blocks_completed": 0,
                "block_uids": [], "gate_event": None, "gate_detail": None,
                "meter_snapshot_seconds": 0.0, "final_terminal": None,
                "updated_utc": now,
            }
        self.per_block_path = self.root / "per_block.jsonl"

    # ---- metering ---------------------------------------------------------
    def sweep_elapsed(self) -> None:
        now = time.monotonic()
        self.ledger["cumulative_seconds"] += max(0.0, now - self._t_last)
        self._t_last = now

    def flush(self) -> None:
        self.sweep_elapsed()
        self.ledger["updated_utc"] = _utcnow()
        (self.root / "resource_ledger.json").write_text(
            json.dumps(self.ledger, indent=2), encoding="utf-8")

    def check_budget(self) -> None:
        self.sweep_elapsed()
        if self.ledger["cumulative_seconds"] >= self.ledger["budget_seconds"]:
            raise BridgeStop(WHITELIST_BUDGET_EXHAUSTED,
                             f"cumulative {self.ledger['cumulative_seconds']:.1f}s >= "
                             f"{self.ledger['budget_seconds']:.0f}s")

    # ---- per-block persistence -------------------------------------------
    def existing_block_uids(self) -> list[str]:
        if not self.per_block_path.exists():
            return []
        uids = []
        for rec in _read_jsonl(self.per_block_path):
            uids.append(rec.get("block_uid"))
        dupes = {u for u in uids if uids.count(u) > 1}
        if dupes:
            raise BridgeStop("evidence_inconsistent",
                             f"duplicated block uid in per_block.jsonl: {sorted(dupes)}")
        return uids

    def append_block_record(self, record: Mapping[str, Any]) -> None:
        known = set(self.progress.get("block_uids", []))
        uid = record.get("block_uid")
        if uid in known:
            raise BridgeStop("evidence_inconsistent", f"duplicate block completion: {uid}")
        with open(self.per_block_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
        self.progress["block_uids"].append(uid)
        self.progress["blocks_completed"] = len(self.progress["block_uids"])
        self.flush()
        self.persist_progress()

    def mark_arm_done(self, arm: str) -> None:
        if arm not in self.progress["arms_completed"]:
            self.progress["arms_completed"].append(arm)
        self.persist_progress()

    def set_gate(self, kind: str, detail: str) -> None:
        self.progress["gate_event"] = kind
        self.progress["gate_detail"] = detail[:2000]
        self.persist_progress()

    def persist_progress(self) -> None:
        self.sweep_elapsed()
        self.progress["meter_snapshot_seconds"] = self.ledger["cumulative_seconds"]
        self.progress["updated_utc"] = _utcnow()
        self.progress_path.write_text(json.dumps(self.progress, indent=2),
                                      encoding="utf-8")

    def record_resume(self, reason: str) -> None:
        self.ledger["resume_events"].append({
            "reason": str(reason), "utc": _utcnow(),
            "cumulative_at_resume": self.ledger["cumulative_seconds"],
        })
        self.flush()


# ---------------------------------------------------------------------------
# RUN_MANIFEST (pre-registration: bindings, B0 seeds, B3 permutation rule,
# posterior anomaly criteria — all frozen before any arm executes)
# ---------------------------------------------------------------------------

def posterior_anomaly_criteria(ref_entropy_bits: Mapping[str, float]) -> dict[str, Any]:
    return {
        "registered_before": "any_arm_execution",
        "bucket_definition":
            "calibration_bucket = 9 - min(9, floor(mean_true_symbol_prior_prob * 10)); "
            "0=best calibrated, 9=worst",
        "block_anomaly_rule":
            f"mean_true_symbol_prior_prob < {ANOM_P_TRUE_MIN} OR "
            f"posterior_nll_bits_per_symbol > source_ref_entropy_bits[source]",
        "arm_anomaly_rule":
            f"anomalous_fraction_over_B3_and_B4_blocks >= {ANOM_FRACTION}",
        "reference_semantics":
            "per-source total posterior entropy (bits/symbol) of the bound V25/V26 "
            "empirical posterior population (adapter_entropy_bits on frozen counts)",
        "source_ref_entropy_bits": {k: float(v) for k, v in ref_entropy_bits.items()},
    }


def b3_permutation_spec() -> dict[str, Any]:
    return {
        "rule": "position permutation of the real per-block error vector "
                "(delta = (bob-alice) mod 1024); surrogate bob = (alice + permuted_delta) "
                "mod 1024; per-block error count and value marginals preserved exactly",
        "object": "EXACTLY the B4 block set: blocks 0..19 per source (P1.4 ruling f)",
        "base_seed": PERM_SEED_FROZEN,
        "seed_derivation": "sha256('<base_seed>:<source>/<block_index>')[:4] big-endian",
        "selected_by_results": False,
    }


def build_run_manifest(repo_root: Path, identity: Mapping[str, Any],
                       ref_entropy_bits: Mapping[str, float]) -> dict[str, Any]:
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "created_utc": _utcnow(),
        "role": "diagnostic_bridge_only_not_qualification",
        "bindings": dict(identity),
        "allocation_scalar_m1": M1_FROZEN,
        "field_id": FIELD_ID,
        "sources": dict(SOURCE_IDS),
        "arms": {
            "B0": {"blocks_per_source": B0_BLOCKS_PER_SOURCE,
                   "seeds": {lbl: [b0_seed(lbl, i) for i in range(B0_BLOCKS_PER_SOURCE)]
                             for lbl in SOURCE_ORDER}},
            "B1": {"blocks_per_source": SYNTH_BLOCKS_PER_SOURCE,
                   "seeds": {lbl: list(SEEDS_B1_B2[lbl]) for lbl in SOURCE_ORDER},
                   "channel": "matched iid synthetic (uniform substitution at frozen "
                              "V25 raw_ser), bound V25/V26 posterior, oracle L1"},
            "B2": {"identical_blocks_as": "B1",
                   "only_change": "oracle L1 -> Bob-only sequential L1"},
            "B3": {"blocks_per_source": SYNTH_BLOCKS_PER_SOURCE,
                   "permutation": b3_permutation_spec()},
            "B4": {"block_ids": list(REAL_BLOCK_IDS),
                   "errors": "real V31 n=1024 validation errors, oracle L1"},
            "B5": {"mode": "read_only_import", "expected_records": 300},
        },
        "discriminator": {
            "block_success": "exact && tag && syndrome && !false_accept",
            "arm_pass": "every source >= 19/20 block successes (B0: 6/6)",
            "b2_significantly_below_b1": "B2 FAIL while B1 PASS under the same discriminator",
            "development_only": True,
        },
        "posterior_anomaly_criteria": posterior_anomaly_criteria(ref_entropy_bits),
        "terminals": list(TERMINALS),
        "early_stop_whitelist": list(EARLY_STOP_WHITELIST),
        "execution_order": list(EXECUTION_ORDER),
        "budget_seconds": BUDGET_SECONDS,
        "harness_code_sha256": _sha256_file(Path(__file__).resolve())[:16],
    }
    # Fingerprint payload excludes volatile fields (created_utc and the
    # per-verification verified_utc timestamp) so that exact-resume comparison
    # is deterministic across wall-clock time; everything frozen stays in.
    fp_payload = {k: v for k, v in manifest.items() if k != "created_utc"}
    fp_payload["bindings"] = {k: v for k, v in fp_payload.get("bindings", {}).items()
                              if k != "verified_utc"}
    manifest["config_fingerprint"] = hashlib.sha256(json.dumps(
        fp_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return manifest


# ---------------------------------------------------------------------------
# Block execution + per-block record assembly (§3 fields)
# ---------------------------------------------------------------------------

def _prior_metrics(centered: np.ndarray, e_true: Sequence[int]) -> dict[str, float]:
    """True-symbol statistics of the centered error-domain prior rows."""
    idx = np.arange(centered.shape[0])
    p_true = centered[idx, np.asarray(e_true, dtype=np.int64)]
    with np.errstate(divide="ignore"):
        nll = -np.log2(np.maximum(p_true, 1e-300))
    ent = -np.sum(np.where(centered > 0, centered * np.log2(np.maximum(centered, 1e-300)), 0.0),
                  axis=1)
    ranks = (centered > p_true[:, None]).sum(axis=1)
    return {
        "posterior_nll": float(nll.mean()),
        "posterior_entropy": float(ent.mean()),
        "truth_symbol_rank": float(ranks.mean()),
        "p_true_mean": float(p_true.mean()),
    }


def build_block_record(*, arm: str, label: str, seed_or_block_id: Any, block_uid: str,
                       identity: Mapping[str, Any], truth_layers: tuple[list[int], list[int]],
                       observed_layers: tuple[list[int], list[int]],
                       result: Mapping[str, Any], runtime_s: float,
                       l1_mode: str, ref_entropy: Mapping[str, float],
                       syndrome_fn: Callable[[str, str, Sequence[int]], list[int]]) -> dict[str, Any]:
    x1_t, x2_t = truth_layers
    y1, y2 = observed_layers
    e1 = [int(a ^ b) for a, b in zip(x1_t, y1)]
    e2 = [int(a ^ b) for a, b in zip(x2_t, y2)]

    sentinel1, sentinel2 = result.get("x1_hat"), result.get("x2_hat")
    x1_hat = list(y1) if sentinel1 == "ECHO_Y1" else sentinel1
    x2_hat = list(y2) if sentinel2 == "ECHO_Y2" else sentinel2

    oracle = (l1_mode == "oracle")
    l1_errors_initial = sum(1 for v in e1 if v != 0)
    l2_errors_initial = sum(1 for v in e2 if v != 0)
    if oracle:
        l1_errors_final = 0                      # 0 by construction (oracle L1)
        x1_effective = x1_t
        exact = bool(x2_hat is not None and list(x2_hat) == x2_t)
    else:
        l1_errors_final = (sum(1 for a, b in zip(x1_hat, x1_t) for v in [int(a) ^ int(b)] if v != 0)
                           if x1_hat is not None else N_FROZEN)
        x1_effective = list(x1_hat) if x1_hat is not None else None
        exact = bool(x1_hat is not None and list(x1_hat) == x1_t
                     and x2_hat is not None and list(x2_hat) == x2_t)
    l2_errors_final = (sum(1 for a, b in zip(x2_hat, x2_t) for v in [int(a) ^ int(b)] if v != 0)
                       if x2_hat is not None else N_FROZEN)

    true_tag = tag64(x1_t, x2_t)
    dec_tag = tag64(x1_effective if not oracle else None, x2_hat) if not oracle \
        else tag64(None, x2_hat)
    # oracle L1 fixes x1 to truth by construction; tag covers the L2 recovery
    if oracle:
        dec_tag = tag64(x1_t, x2_hat)
    tag = bool(x2_hat is not None and dec_tag == true_tag)
    false_accept = bool(tag and not exact)
    l1_syn_ok = result.get("l1_syndrome_ok")
    l2_syn_ok = result.get("l2_syndrome_ok")
    syndrome_flag = bool(l2_syn_ok) and (bool(l1_syn_ok) if l1_syn_ok is not None else True)

    # prior-based diagnostics: rebuild centered priors is runner-side; the harness
    # receives p-metrics via the request-time computation instead (see execute path)
    pmetrics = result.get("_prior_metrics", {})
    p_mean = float(pmetrics.get("p_true_mean", 0.0))
    nll = float(pmetrics.get("posterior_nll", float("inf"))) if pmetrics else float("inf")
    anomalous = (p_mean < ANOM_P_TRUE_MIN) or (not math.isfinite(nll)) or \
                (nll > float(ref_entropy.get(label, math.inf)))

    record = {
        "schema": BLOCK_SCHEMA,
        "arm": arm,
        "source": label,
        "source_id": SOURCE_IDS[label],
        "seed_or_block_id": seed_or_block_id,
        "block_uid": block_uid,
        "graph_packet_identity": identity.get("graph_packet_identity"),
        "posterior_identity": identity.get("posterior_identity"),
        "truth_used": TRUTH_MARKERS_ORACLE["truth_used"] if arm in ("B1", "B2", "B3", "B4")
                      else False,
        "truth_role": "oracle_l1" if arm in ("B1", "B3", "B4")
                      else ("sequential_no_truth" if arm == "B2" else "none"),
        "operational": False,
        "qualification": False,
        "l1_mode": l1_mode,
        "l1_errors_initial": int(l1_errors_initial),
        "l1_errors_final": int(l1_errors_final),
        "l2_errors_initial": int(l2_errors_initial),
        "l2_errors_final": int(l2_errors_final),
        "exact": exact,
        "tag": tag,
        "false_accept": false_accept,
        "syndrome": syndrome_flag,
        "unsatisfied_checks": int(result.get("unsatisfied_checks", 0)),
        "iterations": int(result.get("l1_iterations", 0)) + int(result.get("l2_iterations", 0)),
        "terminal_decoder_status": str(result.get("l2_status", "unknown")),
        "l1_decoder_status_verbatim": str(result.get("l1_status", "unknown")),
        "runtime_s": float(runtime_s),
        "posterior_nll": nll,
        "posterior_entropy": float(pmetrics.get("posterior_entropy", 0.0)) if pmetrics else 0.0,
        "truth_symbol_rank": float(pmetrics.get("truth_symbol_rank", 0.0)) if pmetrics else 0.0,
        "calibration_bucket": 9 - min(9, int(p_mean * 10)) if pmetrics else 9,
        "posterior_anomaly_block": bool(anomalous),
        "residual_syndrome_stats": {
            "l1_residual_checks": None if l1_syn_ok is None
            else (0 if l1_syn_ok else N_FROZEN),
            "l2_residual_checks": int(result.get("unsatisfied_checks", 0))
            if not l2_syn_ok else 0,
        },
        "success": bool(exact and tag and syndrome_flag and not false_accept),
    }
    return record


def _center_rows_xor(rows: np.ndarray, observed: Sequence[int]) -> np.ndarray:
    """Value-domain P(U|·) rows -> error-domain P(E) rows via GF(2^5) rotation:
    out[i, e] = rows[i, observed[i] XOR e]; the true-error probability then
    sits at index (true_symbol XOR observed)."""
    arr = np.asarray(rows, dtype=np.float64)
    obs = np.asarray(observed, dtype=np.int64)
    idx = np.arange(arr.shape[1])[None, :] ^ obs[:, None]
    return np.take_along_axis(arr, idx, axis=1)


def _compute_prior_metrics_for_record(prior_l1_rows, prior_l2_rows, y1, y2,
                                      e1, e2) -> dict[str, float]:
    """Harness-side true-symbol prior statistics (truth stays private).

    Rows are received in the posterior's value domain and centered on the
    observation first, so NLL/entropy/rank/bucket are computed at the true
    ERROR index — consistent with the pre-registered anomaly criteria."""
    import numpy as _np
    metrics = {}
    for rows, obs, e in ((prior_l1_rows, y1, e1), (prior_l2_rows, y2, e2)):
        if rows is None:
            continue
        m = _prior_metrics(_center_rows_xor(_np.asarray(rows, dtype=np.float64), obs), e)
        for k, v in m.items():
            metrics.setdefault(k, []).append(v)
    return {k: float(_np.mean(v)) for k, v in metrics.items()}


# ---------------------------------------------------------------------------
# Arms
# ---------------------------------------------------------------------------

def run_b5_import(state: RunState, identity: Mapping[str, Any], repo_root: Path) -> dict[str, Any]:
    """Read-only import of the canonical V31 n=1024 300-block baseline.

    Import integrity only: this arm performs no decoding and regenerates
    nothing; it never invokes any decoder entry point.
    """
    baseline = _read_jsonl(repo_root / REPO_REL_V31 / "per_block_n1024.jsonl")
    problems = []
    if len(baseline) != 300:
        problems.append(f"record count {len(baseline)} != 300")
    per_source = {lbl: 0 for lbl in SOURCE_ORDER}
    for rec in baseline:
        if rec.get("packet_id") != PACKET_ID_FROZEN:
            problems.append("identity mismatch vs canonical packet")
            break
        lbl = rec.get("source")
        if lbl in per_source:
            per_source[lbl] += 1
    for lbl in SOURCE_ORDER:
        if per_source[lbl] != 100:
            problems.append(f"{lbl} count {per_source[lbl]} != 100")
    ok = not problems
    if not ok:
        state.set_gate("b5_integrity", "; ".join(problems[:5]))
        raise BridgeStop("b5_integrity", "; ".join(problems[:5]))
    record = {
        "schema": BLOCK_SCHEMA, "kind": "baseline_import", "arm": "B5",
        "source": "all", "source_id": None, "seed_or_block_id": None,
        "block_uid": "B5|import|v31_n1024_baseline",
        "graph_packet_identity": identity.get("graph_packet_identity"),
        "posterior_identity": identity.get("posterior_identity"),
        "truth_used": False, "truth_role": "imported_baseline",
        "operational": False, "qualification": False,
        "imported_records": len(baseline), "per_source_counts": per_source,
        "integrity_ok": True,
        "terminal_decoder_status": "not_applicable",
        "runtime_s": 0.0, "success": True,
    }
    state.append_block_record(record)
    summary = {
        "arm": "B5", "stratum": "imported_operational_baseline",
        "records": len(baseline), "per_source_counts": per_source,
        "integrity_ok": True, "decoder_invoked": False,
    }
    (state.root / "summary_B5.json").write_text(json.dumps(summary, indent=2),
                                                encoding="utf-8")
    state.mark_arm_done("B5")
    return summary


def _finish_decode_arm(state: RunState, arm: str, stratum: str) -> dict[str, Any]:
    """Arm summary evaluated over ALL persisted records of this arm (not just
    the blocks newly executed in this segment), so a resumed partial arm is
    summarized against its complete block set."""
    all_arm = [r for r in _read_jsonl(state.per_block_path)
               if r.get("arm") == arm and r.get("kind") != "baseline_import"]
    per_source = {}
    for lbl in SOURCE_ORDER:
        own = [r for r in all_arm if r["source"] == lbl]
        succ = sum(1 for r in own if r.get("success"))
        expected = B0_BLOCKS_PER_SOURCE if arm == "B0" else SYNTH_BLOCKS_PER_SOURCE
        per_source[lbl] = {
            "n": len(own), "successes": succ, "threshold": len(own) if arm == "B0" else 19,
            "pass": (succ == len(own) == expected) if arm == "B0" else (succ >= 19 and len(own) == expected),
        }
    arm_pass = bool(all(v["pass"] for v in per_source.values()))
    fa_total = sum(1 for r in all_arm if r.get("false_accept"))
    if arm == "B0":
        arm_pass = arm_pass and fa_total == 0
    summary = {
        "arm": arm, "stratum": stratum, "arm_pass": arm_pass,
        "per_source": per_source, "false_accept_total": fa_total,
        "development_discriminator_only": True,
    }
    (state.root / f"summary_{arm}.json").write_text(json.dumps(summary, indent=2),
                                                    encoding="utf-8")
    state.mark_arm_done(arm)
    return summary


def _execute_decode_blocks(state: RunState, arm: str, identity: Mapping[str, Any],
                           runner: Callable[[Mapping[str, Any]], Mapping[str, Any]],
                           posterior, syndrome_fn, ref_entropy: Mapping[str, float],
                           repo_root: Path, raw_ser: Mapping[str, float],
                           skip_uids: set[str], stop_counter: dict[str, int] | None
                           ) -> tuple[list[dict[str, Any]], bool]:
    """Shared fixed-order executor for B0..B4 (schedule depends on arm).

    Returns ``(records_newly_executed, interrupted)``; ``interrupted`` marks a
    test-only segment pause — the caller must then NOT finalize the arm.
    """
    records: list[dict[str, Any]] = []
    if arm == "B0":
        entries = [{"source": e["source"], "id": f"B0-{e['index']}", "seed": e["seed"]}
                   for e in b0_schedule()]
    elif arm in ("B1", "B2"):
        entries = [{"source": e["source"], "id": str(e["seed"]), "seed": e["seed"]}
                   for e in b1_b2_schedule()]
    else:  # B3/B4 share the exact real block set
        entries = [{"source": e["source"], "id": str(e["block_index"]),
                    "block_index": e["block_index"]} for e in b3_b4_schedule()]

    for entry in entries:
        label = entry["source"]
        block_uid = f"{arm}|{label}|{entry['id']}"
        if block_uid in skip_uids:
            continue
        state.check_budget()

        # ---- build public fixture + private truth --------------------------
        if arm == "B0":
            alice, bob = synth_channel_sample(entry["seed"], 0.0)   # noiseless
        elif arm in ("B1", "B2"):
            alice, bob = synth_channel_sample(entry["seed"], raw_ser[label])
        elif arm == "B4":
            blk = load_real_validation_block(repo_root, label, entry["block_index"])
            alice, bob = list(blk["alice_symbols"]), list(blk["bob_symbols"])
        else:  # B3: deterministic permutation of EXACTLY this B4 block's errors
            blk = load_real_validation_block(repo_root, label, entry["block_index"])
            alice = list(blk["alice_symbols"])
            errs = permute_error_vector(real_error_vector(blk["alice_symbols"],
                                                          blk["bob_symbols"]),
                                        f"{label}/{entry['block_index']}")
            bob = ((np.asarray(alice, dtype=np.int64) + errs) % 1024).tolist()

        x1_t, x2_t = _factor_layers(alice)
        y1, y2 = _factor_layers(bob)
        s1 = syndrome_fn("L1", label, x1_t)
        s2 = syndrome_fn("L2", label, x2_t)

        l1_mode = "sequential" if arm in ("B0", "B2") else "oracle"
        rows1 = posterior["rows_for"](label)("L1", bob, None)
        prior_l1_rows = rows1
        prior_l2_rows = None
        if l1_mode == "oracle":
            prior_l2_rows = posterior["rows_for"](label)("L2", bob, x1_t)  # declared oracle

        request = {
            "arm": arm, "source": label, "source_id": SOURCE_IDS[label],
            "seed_or_block_id": entry["id"], "block_uid": block_uid,
            "l1_mode": l1_mode,
            "y1": y1, "y2": y2, "s1": s1, "s2": s2,
            "prior_l1": prior_l1_rows, "prior_l2": prior_l2_rows,
            "posterior_provider": None if l1_mode == "oracle"
            else (lambda lid, u1, _label=label, _bob=bob:
                  posterior["rows_for"](_label)(lid, _bob, u1)),
            "max_iter": DEFAULT_MAX_ITER, "streak": DEFAULT_STREAK,
        }
        audit_decoder_input(request)

        started = time.monotonic()
        result = dict(runner(request))
        runtime_s = time.monotonic() - started

        # harness-private prior metrics (truth never entered the request)
        e1 = [int(a ^ b) for a, b in zip(x1_t, y1)]
        e2 = [int(a ^ b) for a, b in zip(x2_t, y2)]
        pm = _compute_prior_metrics_for_record(
            request["prior_l1"], request["prior_l2"], y1, y2, e1, e2)
        result["_prior_metrics"] = pm

        record = build_block_record(
            arm=arm, label=label, seed_or_block_id=entry["id"], block_uid=block_uid,
            identity=identity, truth_layers=(x1_t, x2_t), observed_layers=(y1, y2),
            result=result, runtime_s=runtime_s, l1_mode=l1_mode,
            ref_entropy=ref_entropy, syndrome_fn=syndrome_fn)
        state.append_block_record(record)
        records.append(record)
        if stop_counter is not None:
            stop_counter["done"] += 1
            if stop_counter["done"] >= stop_counter["limit"]:
                return records, True
    return records, False


def run_decode_arm(state: RunState, arm: str, identity: Mapping[str, Any], runner,
                   posterior, syndrome_fn, ref_entropy, repo_root: Path, raw_ser,
                   skip_uids: set[str], stop_counter: dict[str, int] | None) -> dict[str, Any]:
    strata = {
        "B0": "noiseless_plumbing_control",
        "B1": "synthetic_iid_oracle_l1",
        "B2": "synthetic_iid_bob_only_sequential",
        "B3": "permuted_real_surrogate_oracle_l1",
        "B4": "real_retrospective_oracle_l1",
    }
    if arm == "B0":
        records, interrupted = _execute_decode_blocks(
            state, arm, identity, runner, posterior, syndrome_fn, ref_entropy,
            repo_root, raw_ser, skip_uids, stop_counter)
        if interrupted:
            # Segment pause mid-arm: never finalize (no summary, no arm-done
            # mark) so the resume reruns the remaining blocks of this arm.
            return {"arm": arm, "interrupted": True}
        summary = _finish_decode_arm(state, arm, strata[arm])
        if not summary["arm_pass"]:
            state.set_gate(WHITELIST_B0_FAILURE, "B0 failed its 6/6 requirement")
            raise BridgeStop(WHITELIST_B0_FAILURE, json.dumps(summary["per_source"]))
        return summary
    records, interrupted = _execute_decode_blocks(state, arm, identity, runner,
                                                  posterior, syndrome_fn, ref_entropy,
                                                  repo_root, raw_ser, skip_uids,
                                                  stop_counter)
    if interrupted:
        return {"arm": arm, "interrupted": True}
    return _finish_decode_arm(state, arm, strata[arm])


# ---------------------------------------------------------------------------
# Terminal reconstruction — design §5 (gate layer first-match-wins + R01–R16)
# ---------------------------------------------------------------------------

GATE_TERMINAL = {
    WHITELIST_BINDING_FAILURE: "bridge_binding_fail",
    "b5_integrity": "bridge_binding_fail",
    WHITELIST_B0_FAILURE: "bridge_binding_fail",
    WHITELIST_CANONICAL_DRIFT: "bridge_binding_fail",
    WHITELIST_IMPLEMENTATION_EXCEPTION: "implementation_blocked",
    "exception": "implementation_blocked",
    "evidence_inconsistent": "implementation_blocked",
    WHITELIST_TRUTH_USE_VIOLATION: "implementation_blocked",
    WHITELIST_BUDGET_EXHAUSTED: "resource_blocked",
}


def arm_pass_from_records(records: Sequence[Mapping[str, Any]], arm: str) -> bool:
    per_src = {}
    for lbl in SOURCE_ORDER:
        own = [r for r in records if r.get("arm") == arm and r.get("source") == lbl]
        succ = sum(1 for r in own if r.get("success"))
        if arm == "B0":
            per_src[lbl] = (succ == B0_BLOCKS_PER_SOURCE)
        else:
            per_src[lbl] = succ >= 19
    fa = sum(1 for r in records if r.get("arm") == arm and r.get("false_accept"))
    return all(per_src.values()) and (fa == 0 if arm == "B0" else True)


def anomaly_present_from_records(records: Sequence[Mapping[str, Any]]) -> bool:
    flagged = [r for r in records
               if r.get("arm") in ("B3", "B4") and r.get("posterior_anomaly_block")]
    total = sum(1 for r in records if r.get("arm") in ("B3", "B4"))
    return bool(total) and (len(flagged) / total) >= ANOM_FRACTION


def classify_terminal(*, gate_event: str | None, arms_pass: Mapping[str, bool],
                      anomaly_present: bool, complete_execution: bool) -> str:
    """Frozen decision procedure: gate layer first-match-wins, then R01–R16."""
    if gate_event is not None:
        if gate_event == WHITELIST_OUTPUT_COLLISION:
            return "implementation_stop_pre_execution"  # never persisted as terminal
        return GATE_TERMINAL[gate_event]
    if not complete_execution:
        return "bridge_inconclusive"
    b1 = arms_pass.get("B1", False)
    b2 = arms_pass.get("B2", False)
    b3 = arms_pass.get("B3", False)
    b4 = arms_pass.get("B4", False)
    if not b1:
        return "finite_graph_decoder_mismatch"           # R09–R16 (frozen rule dominates)
    if b2 and b3 and b4:
        return "bridge_pass_ready_for_successor"          # R01
    if b2 and b3 and not b4:
        return "real_error_structure_mismatch"            # R02
    if b2 and not b3 and b4:
        return "bridge_inconclusive"                      # R03
    if b2 and not b3 and not b4:
        return ("empirical_channel_model_mismatch" if anomaly_present
                else "bridge_inconclusive")               # R04a / R04b
    if not b2 and b3 and b4:
        return "l1_sequential_propagation_limit"          # R05
    if not b2 and b3 and not b4:
        return "bridge_inconclusive"                      # R06
    return "bridge_inconclusive"                          # R07/R08/uncovered combos


def reconstruct_terminal(records: Sequence[Mapping[str, Any]], *,
                         gate_event: str | None, complete_execution: bool) -> dict[str, Any]:
    arms_pass = {arm: arm_pass_from_records(records, arm) for arm in ARMS_DECODED}
    b5_ok = any(r.get("arm") == "B5" and r.get("integrity_ok") for r in records)
    anomaly = anomaly_present_from_records(records)
    gate = gate_event
    if gate is None and not b5_ok:
        gate = "b5_integrity"
    terminal = classify_terminal(gate_event=gate, arms_pass=arms_pass,
                                 anomaly_present=anomaly,
                                 complete_execution=complete_execution)
    return {
        "schema": "nbldpc_v32_terminal_reconstruction_v1",
        "terminal": terminal,
        "gate_event": gate,
        "arms_pass": arms_pass,
        "b5_import_ok": b5_ok,
        "posterior_anomaly_present": anomaly,
        "complete_execution": complete_execution,
        "decision_procedure": "design.md section 5: gate layer first-match-wins, "
                              "then scientific table R01-R16; uncovered -> bridge_inconclusive",
        "candidate_only": True,
        "main_acceptance_pending": True,
        "qualification": False,
        "promotion": False,
    }


# ---------------------------------------------------------------------------
# Full run driver
# ---------------------------------------------------------------------------

def _resolve_runner(runner_spec: str | None, repo_root: Path, identity: Mapping[str, Any]):
    """Resolve the block runner.  Explicit injection only; 'production' lazily
    constructs the bound V28R runner.  Never implicit."""
    if runner_spec is None or runner_spec == "production":
        prod = ProductionRunner(repo_root, identity["graph_packet_identity"])

        def run(request: Mapping[str, Any]) -> Mapping[str, Any]:
            return prod.run_block(request)
        return run
    module_name, attr = runner_spec.split(":", 1)
    obj = getattr(importlib.import_module(module_name), attr)
    return obj.run_block if hasattr(obj, "run_block") else obj


def _default_syndrome_fn_factory(repo_root: Path, identity: Mapping[str, Any]):
    """Lazy production syndrome computer over the bound QC packet matrices."""
    cache: dict[str, Any] = {}

    def syndrome_fn(layer: str, label: str, symbols: Sequence[int]) -> list[int]:
        from ..formal_ir.nonbinary_field import GF2mField
        field = GF2mField.create(32)
        if "matrices" not in cache:
            cache["matrices"] = load_packet_matrices(repo_root, identity["graph_packet_identity"])
        mats = cache["matrices"]
        matrix = mats["L1"] if layer == "L1" else mats["L2"][label]
        from ..formal_ir.nonbinary_qspa import nonbinary_syndrome
        return [int(v) for v in nonbinary_syndrome(matrix, list(symbols), field)]
    return syndrome_fn


def _zero_syndrome_fn(layer: str, label: str, symbols: Sequence[int]) -> list[int]:
    return [0] * (M1_FROZEN if layer == "L1" else len(symbols) // 57)


def execute_run(repo_root: Path, run_root: Path, *, runner=None,
                posterior=None, syndrome_fn=None, resume_reason: str | None = None,
                budget_seconds: float = BUDGET_SECONDS,
                stop_after_blocks: int | None = None) -> dict[str, Any]:
    """Execute (or resume) the V32 bridge run inside ``run_root``.

    ``runner``/``posterior``/``syndrome_fn`` are explicit injections for tests;
    ``None`` selects the production bindings lazily.  ``stop_after_blocks`` is a
    test-only segment interrupt simulating a crash between blocks.
    """
    repo_root = Path(repo_root)
    run_root = Path(run_root)

    # G-coll: collision STOP before anything else; no overwrite, no auto run_02.
    resuming = run_root.exists()
    if resuming and not resume_reason:
        raise BridgeStop(WHITELIST_OUTPUT_COLLISION,
                         f"run root already exists: {run_root}")
    if not resuming:
        run_root.mkdir(parents=True)

    # Stage 0: binding verification (also serves as the drift check on resume).
    identity = verify_bindings(repo_root)

    posterior = posterior or production_posterior_factory(repo_root)
    ref_entropy = posterior["entropy_bits"]

    state = RunState(run_root, budget_seconds)
    manifest_path = run_root / "RUN_MANIFEST.json"
    if resuming:
        # ---- exact-resume preconditions (design §4.3) ----------------------
        if not manifest_path.exists():
            raise ResumeRefused("RUN_MANIFEST missing: not a V32 run root")
        old = _load_json(manifest_path)
        current = build_run_manifest(repo_root, identity, ref_entropy)
        if old.get("config_fingerprint") != current["config_fingerprint"]:
            raise ResumeRefused("config/seed/input drift vs interrupted run")
        snap = float(state.progress.get("meter_snapshot_seconds", 0.0))
        if float(state.ledger["cumulative_seconds"]) < snap - 1e-9:
            raise ResumeRefused("resource meter went backwards: ledger tampered")
        final_terminal = state.progress.get("final_terminal")
        if final_terminal is not None and final_terminal not in RESUMABLE_TERMINALS:
            raise ResumeRefused(
                f"resume from final terminal '{final_terminal}' is forbidden")
        state.record_resume(str(resume_reason))
        # The persisted gate was consumed by this authorized resume; clear it
        # so post-resume terminal reconstruction reflects new evidence only
        # (a gate that fires again will be re-recorded during this segment).
        state.progress["gate_event"] = None
        state.progress["gate_detail"] = None
    else:
        manifest = build_run_manifest(repo_root, identity, ref_entropy)
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    completed = set(state.existing_block_uids())
    runner_fn = runner if runner is not None else None   # resolve lazily below
    syn_fn = syndrome_fn
    raw_ser = v25_raw_ser(repo_root)
    stop_counter = ({"done": 0, "limit": int(stop_after_blocks)}
                    if stop_after_blocks else None)
    gate_event: str | None = state.progress.get("gate_event")
    gate_detail: str | None = state.progress.get("gate_detail")

    def make_exec():
        nonlocal runner_fn, syn_fn
        if runner_fn is None:
            runner_fn = _resolve_runner(None, repo_root, identity)
        if syn_fn is None:
            syn_fn = _default_syndrome_fn_factory(repo_root, identity)
        return runner_fn, syn_fn

    arm_summaries: dict[str, Any] = {}
    complete_execution = True
    try:
        for stage in EXECUTION_ORDER[1:-1]:  # after binding_verification, before reconstruction
            if stage in state.progress["arms_completed"]:
                continue
            if stage == "B5":
                if "B5|import|v31_n1024_baseline" in completed:
                    state.mark_arm_done("B5")
                    continue
                run_b5_import(state, identity, repo_root)
                continue
            rf, sf = make_exec()
            summary = run_decode_arm(state, stage, identity, rf, posterior, sf,
                                     ref_entropy, repo_root, raw_ser, completed,
                                     stop_counter)
            arm_summaries[stage] = summary
            if stop_counter is not None and stop_counter["done"] >= stop_counter["limit"]:
                complete_execution = False
                return {"status": "paused_segment", "blocks_done": stop_counter["done"],
                        "run_root": str(run_root)}
    except BridgeStop as stop:
        gate_event, gate_detail = stop.kind, stop.detail
        state.set_gate(gate_event, gate_detail)
        complete_execution = False
    except Exception as exc:  # G-exc: unhandled implementation exception
        gate_event = "exception"
        gate_detail = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[-1500:]}"
        state.set_gate(gate_event, gate_detail)
        complete_execution = False
    finally:
        state.flush()

    # Terminal reconstruction (design §5) from persisted evidence.
    records = _read_jsonl(state.per_block_path) if state.per_block_path.exists() else []
    recon = reconstruct_terminal(records, gate_event=gate_event,
                                 complete_execution=complete_execution)
    (state.root / "terminal_reconstruction.json").write_text(
        json.dumps(recon, indent=2), encoding="utf-8")
    state.progress["final_terminal"] = recon["terminal"]
    state.persist_progress()
    return {"status": "complete", "terminal": recon["terminal"],
            "run_root": str(run_root), "reconstruction": recon}


# ---------------------------------------------------------------------------
# Static self-checks (T0 helpers)
# ---------------------------------------------------------------------------

def b5_code_path_clean(path: Path | None = None) -> bool:
    """Static guarantee: the B5 arm body references no decode-entry symbols.

    AST-based so that documentation prose and evidence-record field names
    cannot trip the scan; only real identifiers and call targets count."""
    import ast
    tree = ast.parse((path or Path(__file__)).read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
              and n.name == "run_b5_import")
    names: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Name):
            names.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            names.add(node.attr.lower())
            f = node.value
            if isinstance(f, ast.Name):
                names.add(f.id.lower())
    forbidden = ("decode", "qspa", "fftqspa", "v28", "run_v28", "productionrunner")
    return not any(tok in n for n in names for tok in forbidden)


def no_ttbin_references(path: Path | None = None) -> bool:
    src = (path or Path(__file__)).read_text(encoding="utf-8")
    # token assembled dynamically so this V32 source file itself stays free
    # of any raw raw-tape path reference
    return ("." + "ttbin") not in src


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_nonbinary_v32_finite_de_bridge")
    parser.add_argument("run_root", nargs="?", default=REPO_REL_RUN_ROOT,
                        help="unique V32 run root (default: frozen run_01 path)")
    parser.add_argument("--repo-root", default=None,
                        help="repository root (default: derived from this file)")
    parser.add_argument("--resume-reason", default=None,
                        help="resume the SAME run_01; reason recorded in the ledger")
    parser.add_argument("--runner", default=None, metavar="MODULE:ATTR",
                        help="explicit block-runner injection (tests/fakes only)")
    parser.add_argument("--bindings-only", action="store_true",
                        help="run stage-0 binding verification and exit")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _repo_root_default()
    if args.bindings_only:
        identity = verify_bindings(repo_root)
        print(json.dumps({"ok": True, "field_id": identity.get("field_id"),
                          "packet_id": identity.get("packet_id")}))
        return 0

    run_root = Path(args.run_root)
    if not run_root.is_absolute():
        run_root = repo_root / run_root
    runner = None
    if args.runner:
        runner = _resolve_runner(args.runner, repo_root, {"graph_packet_identity": ""})

    try:
        result = execute_run(repo_root, run_root, runner=runner,
                             resume_reason=args.resume_reason)
    except BridgeStop as stop:
        print(json.dumps({"status": "STOP", "whitelist_reason": stop.kind,
                          "detail": stop.detail}))
        return 2 if stop.kind == WHITELIST_OUTPUT_COLLISION else 1
    except ResumeRefused as refused:
        print(json.dumps({"status": "RESUME_REFUSED", "reason": str(refused)}))
        return 3
    print(json.dumps({"status": result["status"], "terminal": result.get("terminal"),
                      "run_root": result["run_root"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
