"""V33 rate-aligned empirical-channel ensemble DE diagnostic (single-file CLI).

OpenSpec change: formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic
(FROZEN_ACCEPTED, baseline 0a050066).  Binding Registry R1-R7 and all SHALL
clauses live in that change's spec.md -- this file references, never redefines.

Method identity (read-only provenance): the DE engine below is a SELF-CONTAINED
numpy re-implementation of the V26 posterior-population full-vector MC-DE:

- channel construction copied from
  ``comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_channel.py``
  (ChannelAdapter / make_channel_sampler semantics, F03 natural MSB->LSB:
  U1 = A>>5, U2 = A & 31, P(U1|B) for L1, true-predecessor-conditioned
  P(U2|B,U1) for L2, GF-XOR re-centering so the true symbol sits at index 0);
- iteration kernel copied from
  ``comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_mcde.py``
  (variable product update, check-node update with random nonzero GF edge
  coefficient permutation via XOR-order WHT, 1e-300 floor, fail-closed
  normalization, mean bits/symbol entropy observable, streak convergence).
  Pure-numpy replacements for the numba kernels preserve the exact operation
  order; RNG draw order (PCG64, seeded per call) is preserved call-for-call.

NO project module is imported (zero in-project imports beyond this file); no
parameter value is inherited from V26/V31/V25 code.  All V33 parameters come
from the frozen OpenSpec constants below.

Subcommands (design section 4 lifecycle):
- ``prepare``        stage-0 seven-binding validation (R1-R7) -> binding report
                     JSON on stdout / --report-out.  Never touches DE.
- ``verify``         read-only: independently recompute call/cell/overall
                     terminals from persisted evidence in a run root; validate
                     call completeness/uniqueness/order, bindings, rates, rho,
                     H_t traces, streak, reason codes and claim flags.  No DE,
                     no decoder.
- ``test-selfcheck`` tiny synthetic self-check (fake data only, no real inputs,
                     no filesystem writes).
- ``execute``        production path.  Mechanical authorization gate: requires
                     ``--execute-auth-file <path>`` containing JSON with
                     ``{"granted": true, ...}``; missing/refused => exit 7 with
                     zero side effects.  After the gate: path guard -> collision
                     check (entry, once) -> mkdir run_01 -> pre-execution
                     manifest -> fixed-order 30 calls (each persisted before
                     the next) -> cell/overall aggregation -> final_state.json.
- ``--runner MODULE:ATTR`` injects a fake binding provider + fake DE runner
                     (test-only).  When injected the execute authorization gate
                     is skipped, but the path guard still forces fresh
                     workspace-child roots only.  Provider contract:

                         provider.binding_context(repo_root) ->
                             {"mode": "fake",
                              "bindings": <stage-0 report dict, ok=True>,
                              "counts": {source_id: N_ab ndarray}}
                         provider.run_call(request: dict) ->
                             {"terminal", "reason_codes", "iterations",
                              "entropy_trace_bits", "final_entropy_bits"}

Exit codes: 0 ok; 1 self-check failed; 2 output-root collision;
3 blocked (stage-0 binding failure); 4 evidence inconsistent;
5 manifest missing/drifted/tampered; 6 unsafe write target;
7 unauthorized.

Lazy-DE guarantee: importing this module performs no DE computation (module
level holds only constants and function definitions); the real DE engine only
runs inside ``execute`` behind the authorization gate.
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
# Frozen constants (OpenSpec four-piece docs; do not restate elsewhere)
# --------------------------------------------------------------------------- #

CHANGE_NAME = "formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic"
REPO_ROOT = Path(__file__).resolve().parents[4]
DIAGNOSTICS_REL = "comparison_bench/outputs_comparison/nonbinary_diagnostics"
OFFICIAL_RUN_REL = (
    f"{DIAGNOSTICS_REL}/nbldpc_v33_rate_aligned_empirical_de/run_01"
)
OFFICIAL_RUN_ROOT = REPO_ROOT / OFFICIAL_RUN_REL
WORKSPACE_ROOT = REPO_ROOT / "workspace"
RESULTS_ROOT = REPO_ROOT / "results"
ARCHIVE_ROOT = REPO_ROOT / "openspec/changes/archive"
SIBLING_CHECKOUT = REPO_ROOT.parent / "HD-QKD_Polar_Release"

# Binding Registry R1-R7 (spec.md canonical table; paths verbatim).
BINDING_PATHS = {
    "R1": f"{DIAGNOSTICS_REL}/nbldpc_v25_20260818/run_04/channel_counts.npz",
    "R2": f"{DIAGNOSTICS_REL}/nbldpc_v25_20260818/run_04/channel_summary.json",
    "R3": f"{DIAGNOSTICS_REL}/nbldpc_v25_20260818/run_04/split_manifest.json",
    "R4": f"{DIAGNOSTICS_REL}/nbldpc_v31_20260820/run_01/RUN_MANIFEST.json",
    "R5": f"{DIAGNOSTICS_REL}/nbldpc_v31_20260820/run_01/matrix_audits.json",
    "R6": f"{DIAGNOSTICS_REL}/nbldpc_v31_20260820/run_01/m1_registry.json",
    "R7": f"{DIAGNOSTICS_REL}/nbldpc_v26_20260818/run_02/gate.json",
}
V26_CHANNEL_SRC = REPO_ROOT / "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_channel.py"
V26_MCDE_SRC = REPO_ROOT / "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_mcde.py"

# Source ID <-> NPZ key <-> m2 (verbatim on-disk literals; spec Source ID table).
SOURCE_ORDER = ["1M", "1p5M", "2M"]
SOURCE_TABLE = {
    "1M": {
        "source_id": "type2_1M_20260121_184040",
        "npz_key": "type2_1M_20260121_184040_N_ab_train_N_ab_train",
        "m2": 184,
        "leak_total_bits": 1064.0,
    },
    "1p5M": {
        "source_id": "type2_1p5M_20260121_183806",
        "npz_key": "type2_1p5M_20260121_183806_N_ab_train_N_ab_train",
        "m2": 190,
        "leak_total_bits": 1094.0,
    },
    "2M": {
        "source_id": "type2_2M_20260121_183657",
        "npz_key": "type2_2M_20260121_183657_N_ab_train_N_ab_train",
        "m2": 192,
        "leak_total_bits": 1104.0,
    },
}
FROZEN_RAW_SER = {
    "type2_1M_20260121_184040": 0.239779296875,
    "type2_1p5M_20260121_183806": 0.2544695292735815,
    "type2_2M_20260121_183657": 0.2557409550754458,
}

# Factorization / field identity (SHALL-FAC1 / SHALL-FIELD1).
FACT_ID = "F03_natural_MSB_to_LSB_GF32_plus_GF32"
Q = 32
WIDTH_BITS = 5
N_BLOCKS = 1024
M1 = 16
LAYER_ORDER = ["L1", "L2"]
FROZEN_FIELD_ID = "c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf"
PRIMITIVE_POLYNOMIAL = 37  # 0b100101
FIELD_PAYLOAD = {
    "method": "nbldpc_formal_v1",
    "backend_id": "internal_polynomial_basis_gf2m",
    "backend_version": "1",
    "q": Q,
    "m": Q.bit_length() - 1,
    "primitive_polynomial": PRIMITIVE_POLYNOMIAL,
    "basis": "polynomial",
    "symbol_encoding": "unsigned_coefficient_integer_lsb_x_to_the_i",
}

# Candidate Call Matrix, promoted to frozen values at ACCEPT_FREEZE (SHALL-MC1).
SEEDS = [33101, 33102, 33103, 33104, 33105]
N_SAMPLES = 2000
MAX_ITER = 200
ENTROPY_TOL_BITS = 0.01
STREAK = 20
RNG_NAME = "PCG64"
LAMBDA_EDGE = {2: 1.0}
TOTAL_CALLS = len(SOURCE_ORDER) * len(LAYER_ORDER) * len(SEEDS)

STAGE0_REASONS = (
    "missing_input",
    "binding_drift",
    "field_mismatch",
    "allocation_mismatch",
    "malformed_input",
)
OVERALL_PASS_LABEL = "pass_rate_aligned_empirical_de"
OVERALL_FAIL_LABEL = "rate_allocation_or_ensemble_fail"
OVERALL_INCONCLUSIVE_LABEL = "de_diagnostic_inconclusive"
CLAIM_BOUNDARY = (
    "exact-rate empirical-P ensemble DE diagnostic only; not_fixed_packet_de;"
    " no finite code, decoder, FER, QC matrix, qualification or promotion claim"
)
CONVERGENCE_DEFINITION = (
    "H_t = mean_bits_entropy(c2v_t, q) = (1/M) * sum_j H(p_{t,j}) bits/symbol,"
    " M = c2v_t.shape[0] = n_samples = 2000 MC population rows (NOT n=1024);"
    " call PASS iff probabilities valid throughout and streak=20 consecutive"
    " iterations satisfy H_t < 0.01; running to max_iter=200 without the streak"
    " (including finite oscillation) => FAIL; NaN/Inf/negative probability/"
    " normalization failure/exception => INCONCLUSIVE; illegal conditional"
    " denominator => INCONCLUSIVE(reason=inconclusive_input_binding),"
    " one-hot fallback forbidden"
)

MANIFEST_SCHEMA = "nbldpc_v33_rate_aligned_empirical_de_manifest_v1"
CALL_MATRIX_SCHEMA = "nbldpc_v33_rate_aligned_empirical_de_calls_v1"
CELL_MATRIX_SCHEMA = "nbldpc_v33_rate_aligned_empirical_de_cells_v1"
FINAL_STATE_SCHEMA = "nbldpc_v33_rate_aligned_empirical_de_final_state_v1"

# Five protected old roots (SHALL-PATH1).
PROTECTED_OLD_ROOTS = [
    ("v31_run_01", f"{DIAGNOSTICS_REL}/nbldpc_v31_20260820/run_01"),
    ("closeout_v2_run_01", f"{DIAGNOSTICS_REL}/nbldpc_v31_closeout_audit_v2/run_01"),
    ("closeout_v2_run_02", f"{DIAGNOSTICS_REL}/nbldpc_v31_closeout_audit_v2/run_02"),
    ("v32_bridge_run_01", f"{DIAGNOSTICS_REL}/nbldpc_v32_finite_de_bridge/run_01"),
    ("opaudit_v1_run_01", f"{DIAGNOSTICS_REL}/nbldpc_v32_operating_point_audit/run_01"),
]

EXIT_OK = 0
EXIT_SELFCHECK_FAILED = 1
EXIT_COLLISION = 2
EXIT_BLOCKED_BINDING = 3
EXIT_EVIDENCE_INCONSISTENT = 4
EXIT_MANIFEST = 5
EXIT_WRITE_GUARD = 6
EXIT_UNAUTHORIZED = 7

_FLOOR = 1e-300          # V14/V9 positivity floor convention
_NORM_TOL = 1e-9         # normalized-message fraction tolerance
POSTE_RTOL = 1e-6        # V26 posterior row-normalization tolerance


class ZeroDenominatorError(RuntimeError):
    """A positive-probability sample hit an illegal conditional denominator."""


class NumericError(RuntimeError):
    """NaN/Inf/negative probability/normalization failure inside the engine."""


class WriteGuardError(RuntimeError):
    """Target path rejected by the SHALL-PATH1 guard."""


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def git_head() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=30, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return "unavailable"


def this_file_sha256() -> str:
    return sha256_file(Path(__file__).resolve())


def load_runner(spec: str):
    """Resolve ``--runner MODULE:ATTR`` lazily (test-only injection)."""
    module_name, _, attr = spec.partition(":")
    if not module_name or not attr:
        raise ValueError("--runner expects MODULE:ATTR")
    module = importlib.import_module(module_name)
    return getattr(module, attr)


# --------------------------------------------------------------------------- #
# GF(32) field identity (self-contained copy of nonbinary_field.GF2mField,
# polynomial basis, primitive polynomial 37; attribution see module docstring)
# --------------------------------------------------------------------------- #

_FIELD_CACHE: dict = {}


def get_field():
    """Build (memoized) exp/log tables for GF(2^5), poly 37, polynomial basis."""
    if "field" in _FIELD_CACHE:
        return _FIELD_CACHE["field"]
    q = Q
    poly = PRIMITIVE_POLYNOMIAL
    exp: list[int] = []
    log = [-1] * q
    value = 1
    for _ in range(q - 1):
        if value <= 0 or value >= q or log[value] != -1:
            raise ValueError("primitive polynomial does not generate a complete cycle")
        exp.append(value)
        log[value] = len(exp) - 1
        value <<= 1
        if value & q:
            value ^= poly
        value &= q - 1
    if value != 1 or any(v < 0 for v in log[1:]):
        raise ValueError("primitive polynomial does not generate a complete cycle")
    field = {
        "exp": tuple(exp),
        "log": tuple(log),
        "nonzero_cycle": tuple(exp),
        "field_id": sha256_bytes(canonical_json(FIELD_PAYLOAD).encode("ascii")),
    }
    _FIELD_CACHE["field"] = field
    return field


def gf_mul(a: int, b: int) -> int:
    f = get_field()
    if not a or not b:
        return 0
    return f["exp"][(f["log"][a] + f["log"][b]) % (Q - 1)]


def gf_inverse(a: int) -> int:
    f = get_field()
    if not a:
        raise ValueError("zero has no multiplicative inverse")
    return f["exp"][(-f["log"][a]) % (Q - 1)]


def build_gf_perm_table():
    """``perm[h, y] = inverse(h) * y`` for nonzero h (V26 build_gf_perm_table)."""
    f = get_field()
    perm = np.zeros((Q, Q), dtype=np.int64)
    for h in f["nonzero_cycle"]:
        inv = gf_inverse(int(h))
        perm[int(h)] = [gf_mul(inv, y) for y in range(Q)]
    nonzero = np.asarray(f["nonzero_cycle"], dtype=np.int64)
    return perm, nonzero


def check_field_identity() -> dict:
    """Strict GF(32) identity check (SHALL-FIELD1); mismatch => field_mismatch."""
    f = get_field()
    ok_cycle = len(f["nonzero_cycle"]) == Q - 1 and len(set(f["nonzero_cycle"])) == Q - 1
    ok_inv = all(gf_mul(x, gf_inverse(x)) == 1 for x in range(1, Q))
    match = f["field_id"] == FROZEN_FIELD_ID
    return {
        "primitive_polynomial": PRIMITIVE_POLYNOMIAL,
        "basis": FIELD_PAYLOAD["basis"],
        "symbol_encoding": FIELD_PAYLOAD["symbol_encoding"],
        "constructor": "GF2mField.create(32)",
        "computed_field_id": f["field_id"],
        "frozen_field_id": FROZEN_FIELD_ID,
        "cycle_ok": bool(ok_cycle),
        "inverse_ok": bool(ok_inv),
        "match": bool(match and ok_cycle and ok_inv),
    }


# --------------------------------------------------------------------------- #
# Degree distribution helpers (V9/V26 semantics, self-contained)
# --------------------------------------------------------------------------- #

def parse_degree_hist(hist: dict, name: str):
    """Validate ``{degree: weight}`` -> ``(degrees, probs)`` (normalized)."""
    degrees, weights = [], []
    for key, value in hist.items():
        degree = int(key)
        weight = float(value)
        if not math.isfinite(weight) or weight <= 0.0:
            raise NumericError(f"{name} requires positive finite weights")
        if not 1 <= degree <= 2048:
            raise NumericError(f"{name} degree outside 1..2048")
        degrees.append(degree)
        weights.append(weight)
    if not degrees:
        raise NumericError(f"{name} is empty")
    order = np.argsort(degrees)
    degree_arr = np.asarray(degrees, dtype=np.int64)[order]
    weight_arr = np.asarray(weights, dtype=np.float64)[order]
    total = float(weight_arr.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise NumericError(f"{name} weights have invalid total")
    return degree_arr, weight_arr / total


def make_rho(rate: float, lambda_edge: dict | None = None) -> dict:
    """Harmonic-exact concentrated check distribution ``{degree: weight}``.

    Self-contained copy of the V8-60 two-point concentration formula used by
    ``nonbinary_v9_common.concentrated_check_distribution`` +
    ``concentrated_rho_to_hist`` (attribution: V26 make_rho semantics).
    """
    lambda_edge = LAMBDA_EDGE if lambda_edge is None else lambda_edge
    if not math.isfinite(float(rate)):
        raise NumericError("rate must be finite")
    rate = float(rate)
    if (1.0 - rate) <= 0.0:
        raise NumericError("(1 - rate) must be positive")
    integral_lambda = sum(float(w) / int(d) for d, w in lambda_edge.items())
    if not math.isfinite(integral_lambda) or integral_lambda <= 0.0:
        raise NumericError("lambda_edge has invalid integral")
    target = (1.0 - rate) * integral_lambda
    if not math.isfinite(target) or target <= 0.0:
        raise NumericError("target (1-rate)*integral_lambda must be positive and finite")
    dc = 1.0 / target
    if not math.isfinite(dc) or dc < 2.0:
        raise NumericError("implied mean check degree must be >= 2")
    d_lo = int(math.floor(dc))
    if d_lo < 2:
        raise NumericError("implied mean check degree must be >= 2")
    d_hi = d_lo + 1
    if abs(dc - d_lo) < 1e-12:
        return {d_lo: 1.0}
    w_lo = (target - 1.0 / d_hi) / (1.0 / d_lo - 1.0 / d_hi)
    w_hi = 1.0 - w_lo
    if w_lo < 0.0 or w_hi < 0.0:
        raise NumericError("concentrated distribution weights must be non-negative")
    return {d_lo: w_lo, d_hi: w_hi}


def layer_rates() -> dict:
    """Frozen actual rates: R_i = 1 - m_i/1024 with make_rho(R_i) per
    (source, layer); identical structure to the stage-0 ``rates`` section."""
    out = {}
    for label in SOURCE_ORDER:
        m2 = SOURCE_TABLE[label]["m2"]
        out[label] = {}
        for layer in LAYER_ORDER:
            m_i = M1 if layer == "L1" else m2
            r_i = 1.0 - m_i / N_BLOCKS
            out[label][layer] = {"m_i": int(m_i), "R_i": r_i, "rho": make_rho(r_i)}
    return out


# --------------------------------------------------------------------------- #
# Channel construction (self-contained copy of V26 nonbinary_v26_channel
# ChannelAdapter semantics restricted to A02/F03; attribution above)
# --------------------------------------------------------------------------- #

def build_q_joint(counts: np.ndarray) -> dict:
    """Posterior-population channel tables from one source's train N_ab.

    Semantics (V26 ChannelAdapter._build_layer_tables / make_channel_sampler):
    P(A,B) = N_ab/total; P(A|B) column-normalized; U1 = A>>5 (F03 natural
    MSB-to-LSB L1), U2 = A & 31 (L2); P(U1|B) accumulated over A; joint
    P(U1,U2|B) accumulated over A for the true-predecessor-conditioned L2.
    """
    n_ab = np.asarray(counts, dtype=np.float64)
    if n_ab.shape != (N_BLOCKS, N_BLOCKS):
        raise NumericError(f"N_ab must have shape ({N_BLOCKS}, {N_BLOCKS})")
    if not np.all(np.isfinite(n_ab)) or np.any(n_ab < 0.0):
        raise NumericError("N_ab must be finite and non-negative")
    total = float(n_ab.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise NumericError("N_ab must have positive total mass")
    p_ab = (n_ab / total).ravel()
    col = n_ab.sum(axis=0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        p_a_gb = np.divide(n_ab, col, out=np.zeros_like(n_ab), where=col > 0)
    a_idx = np.arange(N_BLOCKS, dtype=np.int64)
    u1 = a_idx >> WIDTH_BITS          # F03 natural MSB-to-LSB: L1 = A >> 5
    u2 = a_idx & (Q - 1)              #                                L2 = A & 31
    p_u1_gb = np.zeros((Q, N_BLOCKS), dtype=np.float64)
    np.add.at(p_u1_gb, u1, p_a_gb)
    p_joint = np.zeros((Q, Q, N_BLOCKS), dtype=np.float64)
    np.add.at(p_joint, (u1, u2), p_a_gb)
    return {"P_ab": p_ab, "p_u1_gb": p_u1_gb, "p_joint": p_joint, "u1": u1, "u2": u2}


def _center_rows(rows: np.ndarray, true_sym: np.ndarray) -> np.ndarray:
    """GF-XOR centering: out[i, j] = rows[i, j XOR tv_i] (truth at index 0)."""
    q_cols = rows.shape[1]
    idx = np.arange(q_cols, dtype=np.int64)[None, :] ^ \
        np.asarray(true_sym, dtype=np.int64)[:, None]
    return np.take_along_axis(rows, idx, axis=1)


def _l1_rows(qdata: dict, b: np.ndarray) -> np.ndarray:
    """P(U1|B=b) rows, (n, 32) (V26: p_u1_gb.T[b])."""
    return qdata["p_u1_gb"].T[b]


def _l2_rows(qdata: dict, b: np.ndarray, u1_true: np.ndarray) -> np.ndarray:
    """True-predecessor-conditioned P(U2|B,U1) rows, (n, 32).

    Zero conditional denominator => ZeroDenominatorError; one-hot fallback is
    FORBIDDEN (SHALL-ZD1).  (V26 silently substituted a one-hot row there; V33
    must terminate the call instead.)
    """
    norms = qdata["p_u1_gb"][u1_true, b]
    bad = (~np.isfinite(norms)) | (norms <= 0.0)
    if np.any(bad):
        raise ZeroDenominatorError(
            "illegal L2 conditional denominator "
            f"P(U1|B) column mass zero at {int(np.flatnonzero(bad)[0])} sampled indices"
        )
    rows = qdata["p_joint"][u1_true, :, b] / norms[:, None]
    return rows


def sample_centered_rows(qdata: dict, layer: str, n: int, rng: np.random.Generator) -> np.ndarray:
    """Draw n (A,B) pairs from flattened P_s(A,B) and return true-symbol-centered
    posterior rows (n, 32).  PCG64 draw order frozen (V26 make_channel_sampler).
    Three sources stay independent; populations are never merged."""
    pick = rng.choice(qdata["P_ab"].size, size=n, p=qdata["P_ab"])
    a = (pick // N_BLOCKS).astype(np.int64)     # flat index -> label A
    b = (pick % N_BLOCKS).astype(np.int64)      # flat index -> Bob symbol B
    if layer == "L1":
        rows = _l1_rows(qdata, b)
        true_val = qdata["u1"][a]
    elif layer == "L2":
        u1_true = qdata["u1"][a]
        rows = _l2_rows(qdata, b, u1_true)
        true_val = qdata["u2"][a]
    else:
        raise NumericError(f"unknown layer {layer}")
    return _center_rows(rows, true_val)


def _channel_from_centered(centered: np.ndarray) -> np.ndarray:
    """Validate + row-normalize centered posterior rows (V26
    _channel_rows_from_centered; violations raise => INCONCLUSIVE(numeric))."""
    centered = np.asarray(centered, dtype=np.float64)
    if centered.ndim != 2:
        raise NumericError("posterior population must be 2-D (n, q)")
    if not np.all(np.isfinite(centered)):
        raise NumericError("posterior population must be finite")
    if np.any(centered < 0.0):
        raise NumericError("posterior population must be non-negative")
    totals = centered.sum(axis=1)
    if not np.all(np.isfinite(totals)) or np.any(totals <= 0.0):
        raise NumericError("posterior population rows must have positive total mass")
    out = centered / totals[:, None]
    if not np.all(np.abs(out.sum(axis=1) - 1.0) < POSTE_RTOL):
        raise NumericError("posterior population not normalized")
    return out


# --------------------------------------------------------------------------- #
# MC-DE kernels (pure-numpy copies of V14/V26 njit math; attribution above)
# --------------------------------------------------------------------------- #

def _wht_rows(block: np.ndarray) -> np.ndarray:
    """Unnormalized XOR-order Walsh-Hadamard transform along axis 1."""
    out = block.copy()
    n, q = out.shape
    width = 1
    while width < q:
        out = out.reshape(n, -1, 2, width)
        left = out[:, :, 0, :].copy()
        right = out[:, :, 1, :]
        out[:, :, 0, :] = left + right
        out[:, :, 1, :] = left - right
        out = out.reshape(n, q)
        width *= 2
    return out


def _floor_normalize(pop: np.ndarray, name: str) -> np.ndarray:
    """Fail-closed floor(1e-300) + row normalization (V14 kernel epilogue)."""
    if not np.all(np.isfinite(pop)):
        raise NumericError(f"{name}: non-finite mass")
    if np.any(pop < -1e-12):
        raise NumericError(f"{name}: negative mass")
    floored = np.maximum(pop, _FLOOR)
    sums = floored.sum(axis=1, keepdims=True)
    if not np.all(np.isfinite(sums)) or np.any(sums <= 0.0):
        raise NumericError(f"{name}: zero or non-finite total mass")
    return floored / sums


def _variable_update(c2v: np.ndarray, channel: np.ndarray,
                     rng: np.random.Generator) -> np.ndarray:
    """Variable product update, dv={2:1} (V26 variable_update_mcde draw order:
    one degree choice, then per-slot integers draws, then the product)."""
    n = channel.shape[0]
    dv_degrees, dv_probs = parse_degree_hist(LAMBDA_EDGE, "lambda_edge")
    degrees = rng.choice(dv_degrees, size=n, p=dv_probs)
    draws = degrees - 1
    max_draws = int(draws.max())
    idx = np.empty((max_draws, n), dtype=np.int64)
    for d in range(max_draws):
        idx[d] = rng.integers(0, n, size=n)
    product = channel.copy()
    for d in range(max_draws):
        active = draws > d
        if not active.any():
            continue
        product[active] *= c2v[idx[d][active]]
    return _floor_normalize(product, "variable update")


def _check_update(v2c: np.ndarray, rng: np.random.Generator,
                  dc_degrees: np.ndarray, dc_probs: np.ndarray,
                  perm: np.ndarray, nonzero: np.ndarray) -> np.ndarray:
    """Check update with random nonzero GF edge coefficients (V26
    check_update_mcde_posterior draw order: degree choice, per-slot integers,
    per-slot coefficient choices, then permute->WHT->accumulate->iWHT/q)."""
    n = v2c.shape[0]
    q_cols = v2c.shape[1]
    degrees = rng.choice(dc_degrees, size=n, p=dc_probs)
    draws = degrees - 1
    max_draws = int(draws.max())
    idx = np.empty((max_draws, n), dtype=np.int64)
    for d in range(max_draws):
        idx[d] = rng.integers(0, n, size=n)
    coeff = np.empty((max_draws, n), dtype=np.int64)
    for d in range(max_draws):
        coeff[d] = rng.choice(nonzero, size=n)
    acc = np.ones((n, q_cols))
    for d in range(max_draws):
        active = draws > d
        if not active.any():
            continue
        rows = v2c[idx[d][active]]
        permuted = np.take_along_axis(rows, perm[coeff[d][active]], axis=1)
        acc[active] *= _wht_rows(permuted)
    acc = _wht_rows(acc) / q_cols
    return _floor_normalize(acc, "check update")


def mean_bits_entropy(pop: np.ndarray) -> float:
    """Mean categorical entropy of a (M, 32) population in bits/symbol.

    H_t = (1/M) * sum_j H(p_{t,j}) with **M = pop.shape[0] = MC-DE population
    rows (n_samples)** -- never a block-length n=1024 normalization
    (SHALL-CONV1).  Same quantity as V26 mean_bits_entropy(c2v, q).
    """
    arr = np.asarray(pop, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != Q:
        raise NumericError(f"population must be (M, {Q})")
    if not np.all(np.isfinite(arr)):
        raise NumericError("population must be finite")
    if np.any(arr < 0.0):
        raise NumericError("population must be non-negative")
    totals = arr.sum(axis=1)
    if not np.all(np.isfinite(totals)) or np.any(totals <= 0.0):
        raise NumericError("population rows must have positive total mass")
    terms = np.zeros_like(arr)
    nz = arr > 0.0
    terms[nz] = -arr[nz] * np.log2(arr[nz])
    return float(np.mean(terms.sum(axis=1)))


def mcde_iterate(qdata: dict, layer: str, seed: int, *, rate: float,
                 n_samples: int = N_SAMPLES, max_iter: int = MAX_ITER,
                 entropy_tol_bits: float = ENTROPY_TOL_BITS,
                 streak_target: int = STREAK) -> dict:
    """One V26-family posterior-population full-vector MC-DE call.

    Convergence is mechanical (SHALL-CONV1): PASS iff probabilities stay valid
    throughout and H_t < entropy_tol_bits for ``streak_target`` consecutive
    iterations; exhausting max_iter without the streak (finite oscillation
    included) => FAIL; any numeric anomaly => INCONCLUSIVE('numeric'); an
    illegal L2 conditional denominator => INCONCLUSIVE('inconclusive_input_binding').
    One-hot fallback is never applied.
    """
    rng = np.random.default_rng(seed)  # PCG64, seeded per call
    rho = make_rho(rate)
    dc_degrees, dc_probs = parse_degree_hist(rho, "rho_edge")
    perm, nonzero = build_gf_perm_table()
    c2v = np.full((n_samples, Q), 1.0 / Q, dtype=np.float64)
    trace: list[float] = []
    streak = 0
    converged = False
    iterations = 0
    terminal = None
    reason_codes: list[str] = []
    try:
        for iteration in range(1, max_iter + 1):
            centered = sample_centered_rows(qdata, layer, n_samples, rng)
            channel = _channel_from_centered(centered)
            v2c = _variable_update(c2v, channel, rng)
            c2v = _check_update(v2c, rng, dc_degrees, dc_probs, perm, nonzero)
            h_t = mean_bits_entropy(c2v)
            trace.append(h_t)
            iterations = iteration
            if h_t < entropy_tol_bits:
                streak += 1
            else:
                streak = 0
            if streak >= streak_target:
                converged = True
                break
    except ZeroDenominatorError as exc:
        terminal = "INCONCLUSIVE"
        reason_codes = ["inconclusive_input_binding"]
        return _call_core(terminal, reason_codes, trace, iterations, detail=str(exc))
    except NumericError as exc:
        terminal = "INCONCLUSIVE"
        reason_codes = ["numeric"]
        return _call_core(terminal, reason_codes, trace, iterations, detail=str(exc))
    except Exception as exc:  # noqa: BLE001 - anomaly => INCONCLUSIVE, never crash
        terminal = "INCONCLUSIVE"
        reason_codes = ["numeric"]
        return _call_core(terminal, reason_codes, trace, iterations,
                          detail=f"{type(exc).__name__}: {exc}")
    if converged:
        terminal = "PASS"
    else:
        terminal = "FAIL"
        reason_codes = ["max_iter_exhausted_without_streak"]
    return _call_core(terminal, reason_codes, trace, iterations)


def _call_core(terminal: str, reason_codes: list[str], trace: list[float],
               iterations: int, detail: str | None = None) -> dict:
    core = {
        "terminal": terminal,
        "reason_codes": list(reason_codes),
        "iterations": int(iterations),
        "entropy_trace_bits": [float(h) for h in trace],
        "final_entropy_bits": float(trace[-1]) if trace else None,
        "rng": RNG_NAME,
        "not_fixed_packet_de": True,
    }
    if detail:
        core["detail"] = detail
    return core


# --------------------------------------------------------------------------- #
# Stage-0 binding validation (Registry R1-R7, SHALL-BIND1)
# --------------------------------------------------------------------------- #

def _binding_entry(rid: str, role: str, rel_or_abs, exists: bool,
                   sha: str | None, checks: list, failure_reason: str | None) -> dict:
    return {
        "id": rid,
        "role": role,
        "path": str(rel_or_abs),
        "exists": bool(exists),
        "sha256": sha,
        "checks": checks,
        "failure_reason": failure_reason,
    }


def _check(name: str, ok: bool, detail: str = "") -> dict:
    return {"name": name, "ok": bool(ok), "detail": detail}


def stage0_validate(repo_root: Path, provider=None) -> tuple[dict, dict]:
    """Validate bindings R1-R7 (existence + SHA256 + literal values).

    Returns ``(report, counts_by_source_id)``.  ``report['ok']`` False means
    blocked: zero DE calls, no aggregation, no fabricated call records.
    Reason mapping (fixed enum): missing_input / binding_drift /
    field_mismatch / allocation_mismatch / malformed_input.
    """
    if provider is not None:
        ctx = provider.binding_context(Path(repo_root))
        report = dict(ctx["bindings"])
        report.setdefault("ok", True)
        report.setdefault("reasons", [])
        # counts are keyed by source_id (canonical), labels only index SOURCE_TABLE
        return report, {SOURCE_TABLE[label]["source_id"]:
                        np.asarray(ctx["counts"][SOURCE_TABLE[label]["source_id"]],
                                   dtype=np.float64)
                        for label in SOURCE_ORDER}

    reasons: list[str] = []
    bindings: dict = {}
    counts: dict = {}

    def fail(reason: str) -> None:
        if reason not in reasons:
            reasons.append(reason)

    # ---- R1: V25 train counts npz ----------------------------------------- #
    p1 = repo_root / BINDING_PATHS["R1"]
    checks, sha1, fr = [], None, None
    if not p1.exists():
        fr = "missing_input"
        checks.append(_check("file_exists", False, str(p1)))
    else:
        sha1 = sha256_file(p1)
        try:
            data = np.load(p1)
            keys = list(data.files)
            for label in SOURCE_ORDER:
                tab = SOURCE_TABLE[label]
                chk = _check(f"key[{tab['npz_key']}]", tab["npz_key"] in keys)
                checks.append(chk)
                if not chk["ok"]:
                    fr = fr or "missing_input"
                    continue
                arr = np.asarray(data[tab["npz_key"]], dtype=np.float64)
                ok_shape = arr.shape == (N_BLOCKS, N_BLOCKS)
                ok_vals = bool(np.all(np.isfinite(arr)) and np.all(arr >= 0.0)
                               and arr.sum() > 0.0)
                checks.append(_check(f"shape[{label}]", ok_shape, str(arr.shape)))
                checks.append(_check(f"values[{label}]", ok_vals))
                if not ok_shape or not ok_vals:
                    fr = fr or "malformed_input"
                else:
                    counts[tab["source_id"]] = arr
        except Exception as exc:  # noqa: BLE001
            fr = "malformed_input"
            checks.append(_check("npz_readable", False, f"{type(exc).__name__}: {exc}"))
    if fr:
        fail(fr)
    bindings["R1"] = _binding_entry("R1", "V25 train counts (DE channel sole source)",
                                    BINDING_PATHS["R1"], p1.exists(), sha1, checks, fr)

    # ---- R2: V25 summary raw_ser / pm1_mass ------------------------------- #
    p2 = repo_root / BINDING_PATHS["R2"]
    checks, sha2, fr = [], None, None
    if not p2.exists():
        fr = "missing_input"
        checks.append(_check("file_exists", False, str(p2)))
    else:
        sha2 = sha256_file(p2)
        try:
            summary = json.loads(p2.read_text(encoding="utf-8"))
            per_source = summary.get("per_source")
            if not isinstance(per_source, dict):
                fr = "malformed_input"
                checks.append(_check("per_source_dict", False))
            else:
                for label in SOURCE_ORDER:
                    sid = SOURCE_TABLE[label]["source_id"]
                    entry = per_source.get(sid)
                    if not isinstance(entry, dict):
                        checks.append(_check(f"summary[{sid}]", False, "absent"))
                        fr = fr or "missing_input"
                        continue
                    ser = entry.get("ser")
                    ok_type = isinstance(ser, (int, float)) and math.isfinite(float(ser))
                    checks.append(_check(f"ser_type[{sid}]", ok_type))
                    if not ok_type:
                        fr = fr or "malformed_input"
                        continue
                    ok_val = float(ser) == FROZEN_RAW_SER[sid]
                    checks.append(_check(f"ser_literal[{sid}]", ok_val,
                                         f"{ser!r} vs {FROZEN_RAW_SER[sid]!r}"))
                    if not ok_val:
                        fr = fr or "binding_drift"
                    checks.append(_check(f"pm1_mass_present[{sid}]",
                                         isinstance(entry.get("pm1_mass"), dict)))
                    if not isinstance(entry.get("pm1_mass"), dict):
                        fr = fr or "missing_input"
        except Exception as exc:  # noqa: BLE001
            fr = "malformed_input"
            checks.append(_check("json_readable", False, f"{type(exc).__name__}: {exc}"))
    if fr:
        fail(fr)
    bindings["R2"] = _binding_entry("R2", "V25 summary raw_ser/pm1_mass",
                                    BINDING_PATHS["R2"], p2.exists(), sha2, checks, fr)

    # ---- R3: V25 split manifest (train boundary declaration) -------------- #
    p3 = repo_root / BINDING_PATHS["R3"]
    checks, sha3, fr = [], None, None
    if not p3.exists():
        fr = "missing_input"
        checks.append(_check("file_exists", False, str(p3)))
    else:
        sha3 = sha256_file(p3)
        try:
            split = json.loads(p3.read_text(encoding="utf-8"))
            checks.append(_check("schema", split.get("schema") == "nbldpc_v25_split_manifest_v1",
                                 str(split.get("schema"))))
            if split.get("schema") != "nbldpc_v25_split_manifest_v1":
                fr = "binding_drift"
            per_source = split.get("per_source")
            if not isinstance(per_source, dict):
                fr = fr or "malformed_input"
                checks.append(_check("per_source_dict", False))
            else:
                for label in SOURCE_ORDER:
                    sid = SOURCE_TABLE[label]["source_id"]
                    entry = per_source.get(sid, {})
                    pairs = entry.get("pairs", {}) if isinstance(entry, dict) else {}
                    train_pairs = pairs.get("train", 0) if isinstance(pairs, dict) else 0
                    ok = isinstance(train_pairs, int) and train_pairs > 0
                    checks.append(_check(f"train_boundary[{sid}]", ok, str(train_pairs)))
                    if not ok:
                        fr = fr or "malformed_input"
        except Exception as exc:  # noqa: BLE001
            fr = "malformed_input"
            checks.append(_check("json_readable", False, f"{type(exc).__name__}: {exc}"))
    if fr:
        fail(fr)
    bindings["R3"] = _binding_entry("R3", "V25 split manifest (train/holdout boundary)",
                                    BINDING_PATHS["R3"], p3.exists(), sha3, checks, fr)

    # ---- R4: V31 RUN_MANIFEST (layer rates + allocation + field identity) - #
    p4 = repo_root / BINDING_PATHS["R4"]
    checks, sha4, fr = [], None, None
    manifest_sources = {}
    if not p4.exists():
        fr = "missing_input"
        checks.append(_check("file_exists", False, str(p4)))
    else:
        sha4 = sha256_file(p4)
        try:
            rm = json.loads(p4.read_text(encoding="utf-8"))
            cfg = rm.get("configs", {}).get("1024")
            if not isinstance(cfg, dict):
                fr = "allocation_mismatch"
                checks.append(_check("configs[1024]", False))
            else:
                sources = cfg.get("sources")
                if not isinstance(sources, dict):
                    fr = "malformed_input"
                    checks.append(_check("sources_dict", False))
                else:
                    for label in SOURCE_ORDER:
                        tab = SOURCE_TABLE[label]
                        entry = sources.get(label)
                        if not isinstance(entry, dict):
                            checks.append(_check(f"source[{label}]", False, "absent"))
                            fr = fr or "missing_input"
                            continue
                        manifest_sources[label] = entry
                        checks.append(_check(f"source_id[{label}]",
                                             entry.get("source_id") == tab["source_id"],
                                             str(entry.get("source_id"))))
                        if entry.get("source_id") != tab["source_id"]:
                            fr = fr or "binding_drift"
                        checks.append(_check(f"m1[{label}]", entry.get("m1") == M1,
                                             str(entry.get("m1"))))
                        if entry.get("m1") != M1:
                            fr = fr or "binding_drift"
                        checks.append(_check(f"m2[{label}]",
                                             entry.get("m2") == tab["m2"],
                                             str(entry.get("m2"))))
                        if entry.get("m2") != tab["m2"]:
                            fr = fr or "binding_drift"
                        leak = entry.get("leak_total_bits")
                        ok_leak = isinstance(leak, (int, float)) and \
                            float(leak) == tab["leak_total_bits"]
                        checks.append(_check(f"leak_total_bits[{label}]", ok_leak,
                                             str(leak)))
                        if not ok_leak:
                            fr = fr or "binding_drift"
                        f_tot = entry.get("f_total")
                        if not isinstance(f_tot, (int, float)) or \
                                not math.isfinite(float(f_tot)) or float(f_tot) <= 0:
                            checks.append(_check(f"f_total[{label}]", False, str(f_tot)))
                            fr = fr or "malformed_input"
                        else:
                            checks.append(_check(f"f_total[{label}]", True))
                            # f=1.3 is historical reference only; never used for rates
                        hid = entry.get("H")
                        ok_h = isinstance(hid, dict) and \
                            isinstance(hid.get("L1"), (int, float)) and \
                            isinstance(hid.get("L2"), (int, float))
                        checks.append(_check(f"H_identity[{label}]", ok_h))
                        if not ok_h:
                            fr = fr or "missing_input"
                fld = cfg.get("field")
                if not isinstance(fld, dict):
                    fr = fr or "malformed_input"
                    checks.append(_check("field_block", False))
                else:
                    ident = check_field_identity()
                    lit_ok = (fld.get("q") == Q and fld.get("primitive_polynomial") ==
                              PRIMITIVE_POLYNOMIAL and fld.get("basis") == "polynomial")
                    id_ok = fld.get("field_id") == FROZEN_FIELD_ID and ident["match"]
                    checks.append(_check("field_literals", lit_ok, canonical_json(
                        {k: fld.get(k) for k in ("q", "primitive_polynomial", "basis")})))
                    checks.append(_check("field_id", id_ok, str(fld.get("field_id"))))
                    if not lit_ok or not id_ok:
                        fr = fr or "field_mismatch"
        except Exception as exc:  # noqa: BLE001
            fr = "malformed_input"
            checks.append(_check("json_readable", False, f"{type(exc).__name__}: {exc}"))
    if fr:
        fail(fr)
    bindings["R4"] = _binding_entry("R4", "V31 manifest (layer rates/allocation/H identity)",
                                    BINDING_PATHS["R4"], p4.exists(), sha4, checks, fr)

    # ---- R5: V31 matrix audits (packet identity only; NEVER a DE input) --- #
    p5 = repo_root / BINDING_PATHS["R5"]
    checks, sha5, fr = [], None, None
    if not p5.exists():
        fr = "missing_input"
        checks.append(_check("file_exists", False, str(p5)))
    else:
        sha5 = sha256_file(p5)
        try:
            ma = json.loads(p5.read_text(encoding="utf-8"))
            packets = ma.get("packets")
            if not isinstance(packets, list):
                fr = "malformed_input"
                checks.append(_check("packets_list", False))
            else:
                alloc = [pk for pk in packets if isinstance(pk, dict) and
                         pk.get("allocation_id") == "m1_16_n1024"]
                checks.append(_check("allocation_filter", len(alloc) >= 1,
                                     f"{len(alloc)} packets"))
                if not alloc:
                    fr = "allocation_mismatch"
                else:
                    target = [pk for pk in alloc if
                              pk.get("packet_id") == "m1_16_n1024_n1024|QC-cyclic-projective"]
                    checks.append(_check("packet_id", len(target) >= 1))
                    if not target:
                        fr = "binding_drift"
                    else:
                        l1_shape = (target[0].get("audits", {}) or {}).get("L1", {}).get("shape")
                        ok_shape = l1_shape == [M1, N_BLOCKS]
                        checks.append(_check("L1_shape", ok_shape, str(l1_shape)))
                        if not ok_shape:
                            fr = "binding_drift"
        except Exception as exc:  # noqa: BLE001
            fr = "malformed_input"
            checks.append(_check("json_readable", False, f"{type(exc).__name__}: {exc}"))
    if fr:
        fail(fr)
    bindings["R5"] = _binding_entry(
        "R5", "V31 matrix audits (allocation/packet identity only; not a DE input)",
        BINDING_PATHS["R5"], p5.exists(), sha5, checks, fr)

    # ---- R6: V31 m1_registry (filtered allocation; limited field reads) --- #
    p6 = repo_root / BINDING_PATHS["R6"]
    checks, sha6, fr = [], None, None
    if not p6.exists():
        fr = "missing_input"
        checks.append(_check("file_exists", False, str(p6)))
    else:
        sha6 = sha256_file(p6)
        try:
            reg = json.loads(p6.read_text(encoding="utf-8"))
            calls = reg.get("registered_calls")
            if not isinstance(calls, list):
                fr = "malformed_input"
                checks.append(_check("registered_calls_list", False))
            else:
                filt = [c for c in calls if isinstance(c, dict) and
                        c.get("allocation_id") == "m1_16_n1024"]
                checks.append(_check("allocation_filter", len(filt) >= 1, f"{len(filt)} calls"))
                if not filt:
                    fr = "allocation_mismatch"
                else:
                    rates_allowed = {"L1": 1.0 - M1 / N_BLOCKS}
                    for label in SOURCE_ORDER:
                        tab = SOURCE_TABLE[label]
                        rates_allowed["L2"] = 1.0 - tab["m2"] / N_BLOCKS
                        mine = [c for c in filt if c.get("source_id") == tab["source_id"]]
                        checks.append(_check(f"registry_entries[{label}]", len(mine) >= 1,
                                             f"{len(mine)} calls"))
                        if not mine:
                            fr = fr or "allocation_mismatch"
                            continue
                        m1_ok = all(c.get("m1") == M1 for c in mine)
                        m2_ok = all(c.get("m2") == tab["m2"] for c in mine)
                        rate_ok = all(
                            isinstance(c.get("rate"), (int, float)) and
                            min(abs(float(c["rate"]) - r) for r in rates_allowed.values()) < 1e-9
                            for c in mine)
                        checks.append(_check(f"m1[{label}]", m1_ok))
                        checks.append(_check(f"m2[{label}]", m2_ok))
                        checks.append(_check(f"rate[{label}]", rate_ok))
                        if not m1_ok or not m2_ok or not rate_ok:
                            fr = fr or "binding_drift"
        except Exception as exc:  # noqa: BLE001
            fr = "malformed_input"
            checks.append(_check("json_readable", False, f"{type(exc).__name__}: {exc}"))
    if fr:
        fail(fr)
    bindings["R6"] = _binding_entry(
        "R6", "V31 registry (source/allocation/m1/m2/rate/H reads only;"
              " V31 DE params never inherited)",
        BINDING_PATHS["R6"], p6.exists(), sha6, checks, fr)

    # ---- R7: V26 method identity reference (read-only) -------------------- #
    p7 = repo_root / BINDING_PATHS["R7"]
    checks, sha7, fr = [], None, None
    if not p7.exists():
        fr = "missing_input"
        checks.append(_check("file_exists", False, str(p7)))
    else:
        sha7 = sha256_file(p7)
        try:
            gate = json.loads(p7.read_text(encoding="utf-8"))
            status_ok = gate.get("status") == "pass_target_f13"
            best = gate.get("best_passing_f")
            best_ok = isinstance(best, dict) and best.get("A01") == 1.6 and \
                best.get("A02") == 1.3
            checks.append(_check("gate_status", status_ok, str(gate.get("status"))))
            checks.append(_check("best_passing_f", best_ok, canonical_json(best)
                                 if isinstance(best, dict) else str(best)))
            if not status_ok or not best_ok:
                fr = "binding_drift"
        except Exception as exc:  # noqa: BLE001
            fr = "malformed_input"
            checks.append(_check("json_readable", False, f"{type(exc).__name__}: {exc}"))
    if fr:
        fail(fr)
    entry7 = _binding_entry("R7", "V26 DE kernel/method identity + historical gate"
                            " (read-only reference; never extrapolated)",
                            BINDING_PATHS["R7"], p7.exists(), sha7, checks, fr)
    # Sampler/kernel code identity: recorded only (no frozen literal exists).
    code_ids = {}
    for tag, src in (("v26_channel_py", V26_CHANNEL_SRC), ("v26_mcde_py", V26_MCDE_SRC)):
        rec = {"path": str(src.relative_to(REPO_ROOT)) if src.exists() else str(src),
               "exists": src.exists(),
               "sha256": sha256_file(src) if src.exists() else None}
        code_ids[tag] = rec
        if not src.exists():
            fr7 = "missing_input"
            entry7["checks"].append(_check(f"code_identity[{tag}]", False, rec["path"]))
            fail(fr7)
            entry7["failure_reason"] = entry7["failure_reason"] or fr7
    entry7["code_identity"] = code_ids
    entry7["code_identity_enforcement"] = "recorded_only"
    bindings["R7"] = entry7

    # ---- field identity (own implementation vs frozen constant) ----------- #
    ident = check_field_identity()
    if not ident["match"]:
        fail("field_mismatch")

    rates = {}
    for label in SOURCE_ORDER:
        rates[label] = {}
        for layer in LAYER_ORDER:
            m_i = M1 if layer == "L1" else SOURCE_TABLE[label]["m2"]
            r_i = 1.0 - m_i / N_BLOCKS
            rates[label][layer] = {"m_i": int(m_i), "R_i": r_i,
                                   "rho": make_rho(r_i)}
    report = {
        "schema": "nbldpc_v33_rate_aligned_empirical_de_stage0_v1",
        "change": CHANGE_NAME,
        "generated_utc": utc_now(),
        "repo_root": str(repo_root),
        "git_head": git_head(),
        "factorization": FACT_ID,
        "field_identity": ident,
        "bindings": bindings,
        "rates": rates,
        "reason_enum": list(STAGE0_REASONS),
        "reasons": reasons,
        "ok": not reasons,
    }
    return report, counts


# --------------------------------------------------------------------------- #
# Call matrix enumeration / aggregation
# --------------------------------------------------------------------------- #

def enumerate_calls() -> list[dict]:
    """Fixed exact-once order: source(1M->1p5M->2M) x layer(L1->L2) x seed asc."""
    calls = []
    ordinal = 0
    for label in SOURCE_ORDER:
        for layer in LAYER_ORDER:
            for seed in SEEDS:
                ordinal += 1
                calls.append({
                    "ordinal": ordinal,
                    "source_label": label,
                    "source_id": SOURCE_TABLE[label]["source_id"],
                    "layer": layer,
                    "seed": seed,
                })
    return calls


def aggregate(records: list[dict], rates: dict) -> tuple[dict, dict]:
    """Cells (source,layer over seeds) then overall; priority
    INCONCLUSIVE > FAIL > PASS; uncovered combos => inconclusive."""
    cells: dict = {}
    for label in SOURCE_ORDER:
        for layer in LAYER_ORDER:
            subset = [r for r in records
                      if r.get("source_label") == label and r.get("layer") == layer]
            subset.sort(key=lambda r: r.get("seed", 0))
            terms = [r.get("terminal") for r in subset]
            reasons = sorted({rc for r in subset for rc in (r.get("reason_codes") or [])})
            if len(subset) != len(SEEDS):
                terminal, label_reasons = "INCONCLUSIVE", ["uncovered_combination"]
            elif "INCONCLUSIVE" in terms:
                terminal = "INCONCLUSIVE"
            elif all(t == "PASS" for t in terms):
                terminal, label_reasons = "PASS", []
            else:
                terminal = "FAIL"
            cells[f"{label}|{layer}"] = {
                "source_label": label, "layer": layer,
                "seeds": [r.get("seed") for r in subset],
                "terminals": terms,
                "terminal": terminal,
                "reason_codes": reasons if terminal != "INCONCLUSIVE" else
                (sorted(set(reasons) | {"uncovered_combination"})
                 if len(subset) != len(SEEDS) else reasons),
                "rate": rates[label][layer]["R_i"],
            }
    all_terms = [c["terminal"] for c in cells.values()]
    # Overall INCONCLUSIVE reports only the terminal-driving (INCONCLUSIVE)
    # cell reasons; FAIL-cell reasons stay visible per cell in the matrix.
    cell_reasons = sorted({rc for c in cells.values()
                           if c["terminal"] == "INCONCLUSIVE"
                           for rc in c["reason_codes"]})
    if "INCONCLUSIVE" in all_terms:
        overall = {"terminal": "INCONCLUSIVE", "label": OVERALL_INCONCLUSIVE_LABEL,
                   "reason_codes": cell_reasons}
    elif all(t == "PASS" for t in all_terms) and cells:
        overall = {"terminal": "PASS", "label": OVERALL_PASS_LABEL, "reason_codes": []}
    else:
        overall = {"terminal": "FAIL", "label": OVERALL_FAIL_LABEL, "reason_codes": []}
    return cells, overall


# --------------------------------------------------------------------------- #
# Path guard (SHALL-PATH1) and manifest freeze
# --------------------------------------------------------------------------- #

def guard_run_root(run_root: Path, fake: bool) -> Path:
    """Whitelist guard: production execute only at the complete official
    run_01; fake/test-only only at a fresh workspace child root.  Everything
    else (repo root, results root, diagnostics root, archive, five protected
    old roots and subpaths, workspace root itself, sibling checkout) is
    rejected with EXIT_WRITE_GUARD."""
    rp = Path(os.path.abspath(str(run_root))).resolve()

    if SIBLING_CHECKOUT.exists():
        sib = SIBLING_CHECKOUT.resolve()
        if rp == sib or sib in rp.parents:
            raise WriteGuardError(f"sibling checkout is forbidden: {rp}")

    protected = [(tag, (REPO_ROOT / rel).resolve()) for tag, rel in PROTECTED_OLD_ROOTS]
    for tag, prot in protected:
        if rp == prot or prot in rp.parents:
            raise WriteGuardError(f"protected old root '{tag}' (or subpath) forbidden: {rp}")
    for tag, root in [("results_root", RESULTS_ROOT), ("archive_root", ARCHIVE_ROOT)]:
        r = root.resolve()
        if rp == r or r in rp.parents:
            raise WriteGuardError(f"'{tag}' (or subpath) forbidden: {rp}")

    official = OFFICIAL_RUN_ROOT.resolve()
    if not fake:
        if rp != official:
            raise WriteGuardError(
                "production execute writes only the complete official run_01: "
                f"{OFFICIAL_RUN_REL} (got {rp})")
        return rp

    ws = WORKSPACE_ROOT.resolve()
    if rp == ws or ws not in rp.parents:
        raise WriteGuardError(
            f"fake/test writes only at a fresh child root under {ws}/ (got {rp})")
    if rp == official or official in rp.parents or rp in official.parents:
        raise WriteGuardError(f"official run root forbidden in fake mode: {rp}")
    return rp


def check_collision(run_root: Path) -> bool:
    return run_root.exists()


def deny_protected_write(target: Path) -> None:
    """Reject operator-directed report paths inside protected roots
    (SHALL-PATH1 spirit; everything outside the listed roots is allowed)."""
    rp = Path(os.path.abspath(str(target))).resolve()
    if SIBLING_CHECKOUT.exists():
        sib = SIBLING_CHECKOUT.resolve()
        if rp == sib or sib in rp.parents:
            raise WriteGuardError(f"sibling checkout is forbidden: {rp}")
    for tag, rel in PROTECTED_OLD_ROOTS:
        prot = (REPO_ROOT / rel).resolve()
        if rp == prot or prot in rp.parents:
            raise WriteGuardError(f"protected old root '{tag}' forbidden: {rp}")
    for tag, root in [("results_root", RESULTS_ROOT),
                      ("archive_root", ARCHIVE_ROOT),
                      ("diagnostics_root", REPO_ROOT / DIAGNOSTICS_REL)]:
        r = root.resolve()
        if rp == r or r in rp.parents:
            raise WriteGuardError(f"'{tag}' (or subpath) forbidden: {rp}")


def freeze_manifest(report: dict, run_root: Path, auth_info: dict,
                    output_inventory: list) -> dict:
    """Pre-execution manifest: written BEFORE any DE computation."""
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "change": CHANGE_NAME,
        "generated_utc": utc_now(),
        "git_head": git_head(),
        "lifecycle": {
            "state_machine": "EXECUTE_AUTH granted via mechanical auth gate"
            if auth_info["mechanism"] == "auth_file" else
            "fake runner injection (authorization gate skipped; workspace-only)",
            "execute_auth": auth_info,
            "collision_checked_at_entry": True,
            "not_fixed_packet_de": True,
        },
        "frozen_call_matrix": {
            "sources_order": list(SOURCE_ORDER),
            "layers_order": list(LAYER_ORDER),
            "seeds": list(SEEDS),
            "n_samples": N_SAMPLES,
            "max_iter": MAX_ITER,
            "entropy_tol_bits": ENTROPY_TOL_BITS,
            "streak": STREAK,
            "rng": RNG_NAME,
            "lambda_edge": {str(k): v for k, v in LAMBDA_EDGE.items()},
            "n_blocks": N_BLOCKS,
            "m1": M1,
            "total_calls": TOTAL_CALLS,
        },
        "convergence_definition": CONVERGENCE_DEFINITION,
        "factorization": FACT_ID,
        "field_identity": report["field_identity"],
        "bindings": report["bindings"],
        "rates": report["rates"],
        "implementation_identity": {
            "cli": Path(__file__).name,
            "cli_sha256": this_file_sha256(),
        },
        "run_root": str(run_root),
        "output_inventory": output_inventory,
    }
    manifest["freeze_digest"] = sha256_bytes(
        canonical_json({k: v for k, v in manifest.items() if k != "freeze_digest"})
        .encode("utf-8"))
    return manifest


def verify_freeze_digest(manifest: dict) -> bool:
    digest = manifest.get("freeze_digest")
    if not isinstance(digest, str):
        return False
    body = {k: v for k, v in manifest.items() if k != "freeze_digest"}
    return sha256_bytes(canonical_json(body).encode("utf-8")) == digest


# --------------------------------------------------------------------------- #
# Subcommands
# --------------------------------------------------------------------------- #

def cmd_prepare(args) -> int:
    provider = load_runner(args.runner) if args.runner else None
    report, _ = stage0_validate(REPO_ROOT, provider)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.report_out:
        out = Path(args.report_out)
        try:
            deny_protected_write(out)
        except WriteGuardError as exc:
            print(json.dumps({"blocked": "write_guard", "detail": str(exc)}))
            return EXIT_WRITE_GUARD
        out.write_text(text + "\n", encoding="utf-8")
    return EXIT_OK if report["ok"] else EXIT_BLOCKED_BINDING


def _request_for(call_spec: dict, rates: dict) -> dict:
    label, layer = call_spec["source_label"], call_spec["layer"]
    rate_entry = rates[label][layer]
    return {
        "ordinal": call_spec["ordinal"],
        "source_label": label,
        "source_id": call_spec["source_id"],
        "layer": layer,
        "seed": call_spec["seed"],
        "rate": rate_entry["R_i"],
        "rho": rate_entry["rho"],
        "params": {
            "n_samples": N_SAMPLES, "max_iter": MAX_ITER,
            "entropy_tol_bits": ENTROPY_TOL_BITS, "streak": STREAK,
            "rng": RNG_NAME, "q": Q,
        },
        "not_fixed_packet_de": True,
    }


def _finalize_record(core: dict, request: dict) -> dict:
    rec = dict(request)
    rec.update(core)
    rec["claim_boundary"] = CLAIM_BOUNDARY
    return rec


def cmd_execute(args) -> int:
    fake = bool(args.runner)
    provider = load_runner(args.runner) if fake else None
    run_root = Path(args.run_root) if args.run_root else OFFICIAL_RUN_ROOT

    # 1. mechanical authorization gate -- first checkpoint, zero side effects
    if fake:
        auth_info = {"mechanism": "fake_runner", "runner": args.runner,
                     "granted": True, "note": "authorization gate skipped (test-only)"}
    else:
        auth_path = getattr(args, "execute_auth_file", None)
        if not auth_path:
            print(json.dumps({"blocked": "unauthorized",
                              "detail": "--execute-auth-file required for execute"}))
            return EXIT_UNAUTHORIZED
        ap = Path(auth_path)
        if not ap.exists():
            print(json.dumps({"blocked": "unauthorized",
                              "detail": f"auth file missing: {ap}"}))
            return EXIT_UNAUTHORIZED
        try:
            auth = json.loads(ap.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(json.dumps({"blocked": "unauthorized",
                              "detail": f"auth file unparsable: {exc}"}))
            return EXIT_UNAUTHORIZED
        if auth.get("granted") is not True:
            print(json.dumps({"blocked": "unauthorized",
                              "detail": "auth file does not grant execution"}))
            return EXIT_UNAUTHORIZED
        auth_info = {"mechanism": "auth_file", "file": str(ap),
                     "sha256": sha256_file(ap), "granted": True}

    # 2. path guard (SHALL-PATH1) -- before anything else touches disk
    try:
        run_root = guard_run_root(run_root, fake)
    except WriteGuardError as exc:
        print(json.dumps({"blocked": "write_guard", "detail": str(exc)}))
        return EXIT_WRITE_GUARD

    # 3. collision check at the execute entry, exactly once
    if check_collision(run_root):
        print(json.dumps({"blocked": "collision", "run_root": str(run_root),
                          "detail": "run root already exists; run_02/resume forbidden"}))
        return EXIT_COLLISION

    # 4. stage-0 binding validation -- failure => zero DE calls, no directory
    report, counts = stage0_validate(REPO_ROOT, provider)
    if not report["ok"]:
        print(json.dumps({"blocked": "stage0_binding_failure",
                          "reasons": report["reasons"],
                          "report": report}, default=str))
        return EXIT_BLOCKED_BINDING

    # 5. lifecycle: mkdir -> pre-execution manifest -> 30 calls -> aggregate
    run_root.mkdir(parents=True)
    output_inventory = [
        "audit_manifest.json", "de_call_matrix.json", "de_cell_matrix.json",
        "de_cell_matrix.md", "final_state.json", "v26_reference_readonly.json",
    ]
    manifest = freeze_manifest(report, run_root, auth_info, output_inventory)
    (run_root / "audit_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # R7 read-only reference snapshot
    ref = {
        "schema": "nbldpc_v33_v26_reference_readonly_v1",
        "note": "read-only method-identity reference; never a V33 parameter source",
        "gate": json.loads((REPO_ROOT / BINDING_PATHS["R7"]).read_text(encoding="utf-8")),
        "code_identity": report["bindings"]["R7"].get("code_identity", {}),
    }
    (run_root / "v26_reference_readonly.json").write_text(
        json.dumps(ref, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    calls_path = run_root / "de_call_matrix.json"
    records: list[dict] = []

    for call_spec in enumerate_calls():
        request = _request_for(call_spec, report["rates"])
        if fake:
            core = provider.run_call(request)
        else:
            qdata = build_q_joint(counts[call_spec["source_id"]])
            core = mcde_iterate(
                qdata, call_spec["layer"], call_spec["seed"],
                rate=request["rate"])
        records.append(_finalize_record(core, request))
        # persist THIS call before entering the next one (exact-once, design §2)
        calls_path.write_text(
            json.dumps({"schema": CALL_MATRIX_SCHEMA, "records": records},
                       indent=2, sort_keys=True) + "\n", encoding="utf-8")

    cells, overall = aggregate(records, report["rates"])
    cell_doc = {
        "schema": CELL_MATRIX_SCHEMA,
        "aggregation_priority": "INCONCLUSIVE > FAIL > PASS",
        "cells": cells,
    }
    (run_root / "de_cell_matrix.json").write_text(
        json.dumps(cell_doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_lines = ["# V33 rate-aligned empirical DE cell matrix", "",
                "| cell | terminal | seeds | reasons | rate |", "|---|---|---|---|---|"]
    for key, cell in cells.items():
        md_lines.append(f"| {key} | {cell['terminal']} | "
                        f"{','.join(str(s) for s in cell['seeds'])} | "
                        f"{';'.join(cell['reason_codes']) or '-'} | {cell['rate']} |")
    (run_root / "de_cell_matrix.md").write_text("\n".join(md_lines) + "\n",
                                                encoding="utf-8")

    final_state = {
        "schema": FINAL_STATE_SCHEMA,
        "change": CHANGE_NAME,
        "generated_utc": utc_now(),
        "overall_terminal": overall["terminal"],
        "overall_label": overall["label"],
        "reason_codes": overall["reason_codes"],
        "aggregation_priority": "INCONCLUSIVE > FAIL > PASS",
        "calls_total": len(records),
        "not_fixed_packet_de": True,
        "claim_boundary": CLAIM_BOUNDARY,
        "candidate_only": True,
        "main_acceptance_pending": True,
        "qualification": False,
        "promotion": False,
        "freeze_digest_ref": manifest["freeze_digest"],
    }
    (run_root / "final_state.json").write_text(
        json.dumps(final_state, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({"ok": True, "run_root": str(run_root),
                      "overall_terminal": overall["terminal"],
                      "overall_label": overall["label"]}))
    return EXIT_OK


def _replay_terminal(record: dict) -> tuple[str, list, int | None]:
    """Independently recompute a call terminal from its persisted H_t trace.

    Returns ``(terminal, reason_codes, replayed_iterations)``; the iteration
    count is the streak-completion index for PASS runs (None otherwise)."""
    trace = record.get("entropy_trace_bits") or []
    reasons = list(record.get("reason_codes") or [])
    if "INCONCLUSIVE" in (record.get("terminal"),):
        return "INCONCLUSIVE", reasons, None
    if not trace:
        return "INCONCLUSIVE", sorted(set(reasons) | {"empty_trace"}), None
    if any((not math.isfinite(h)) or h < 0.0 for h in trace):
        return "INCONCLUSIVE", sorted(set(reasons) | {"invalid_entropy_values"}), None
    streak = 0
    for iteration, h in enumerate(trace, start=1):
        streak = streak + 1 if h < ENTROPY_TOL_BITS else 0
        if streak >= STREAK:
            return "PASS", [], iteration
    if len(trace) >= MAX_ITER:
        return "FAIL", ["max_iter_exhausted_without_streak"], None
    return "INCONCLUSIVE", sorted(set(reasons) | {"truncated_trace"}), None


def cmd_verify(args) -> int:
    provider = load_runner(args.runner) if args.runner else None
    run_root = Path(args.run_root)
    problems: list[str] = []

    manifest_path = run_root / "audit_manifest.json"
    if not manifest_path.exists():
        print(json.dumps({"verdict": "manifest_missing", "problems":
                          [f"{manifest_path} not found"], "exit": EXIT_MANIFEST}))
        return EXIT_MANIFEST
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"verdict": "manifest_unparsable",
                          "problems": [str(exc)], "exit": EXIT_MANIFEST}))
        return EXIT_MANIFEST
    if not verify_freeze_digest(manifest):
        print(json.dumps({"verdict": "freeze_digest_drift",
                          "problems": ["freeze_digest does not match manifest body"],
                          "exit": EXIT_MANIFEST}))
        return EXIT_MANIFEST

    # bindings: re-validate now and compare against manifest-recorded hashes
    report, _ = stage0_validate(REPO_ROOT, provider)
    if not report["ok"]:
        problems.append(f"stage0_now_blocked:{','.join(report['reasons'])}")
    else:
        for rid, now_entry in report["bindings"].items():
            frozen = (manifest.get("bindings") or {}).get(rid) or {}
            if now_entry.get("sha256") != frozen.get("sha256"):
                problems.append(f"binding_sha_drift:{rid}")

    # frozen matrix consistency between manifest and code constants
    fcm = manifest.get("frozen_call_matrix") or {}
    expected_matrix = {
        "seeds": list(SEEDS), "n_samples": N_SAMPLES, "max_iter": MAX_ITER,
        "entropy_tol_bits": ENTROPY_TOL_BITS, "streak": STREAK, "rng": RNG_NAME,
        "total_calls": TOTAL_CALLS, "m1": M1, "n_blocks": N_BLOCKS,
        "layers_order": list(LAYER_ORDER), "sources_order": list(SOURCE_ORDER),
    }
    for key, want in expected_matrix.items():
        got = fcm.get(key)
        if isinstance(want, float):
            ok = isinstance(got, (int, float)) and float(got) == want
        else:
            ok = got == want
        if not ok:
            problems.append(f"matrix_param_drift:{key}:{got!r}!={want!r}")

    # call evidence
    calls_path = run_root / "de_call_matrix.json"
    if not calls_path.exists():
        problems.append("de_call_matrix.json missing")
        records = []
    else:
        try:
            records = json.loads(calls_path.read_text(encoding="utf-8"))["records"]
        except Exception as exc:  # noqa: BLE001
            problems.append(f"de_call_matrix unparsable: {exc}")
            records = []

    expected = enumerate_calls()
    if len(records) != len(expected):
        problems.append(f"call_count:{len(records)}!={len(expected)}")
    seen = set()
    for i, rec in enumerate(records):
        exp = expected[i] if i < len(expected) else None
        if exp is None:
            problems.append(f"extra_call_at_index:{i}")
            continue
        key = (rec.get("source_label"), rec.get("layer"), rec.get("seed"))
        if key in seen:
            problems.append(f"duplicate_call:{key}")
        seen.add(key)
        if key != (exp["source_label"], exp["layer"], exp["seed"]) or \
                rec.get("ordinal") != exp["ordinal"]:
            problems.append(f"out_of_order_at_index:{i}:{key}")
        # frozen params + rate/rho per record
        params = rec.get("params") or {}
        for pk, pv in (("n_samples", N_SAMPLES), ("max_iter", MAX_ITER),
                       ("entropy_tol_bits", ENTROPY_TOL_BITS), ("streak", STREAK),
                       ("rng", RNG_NAME)):
            if params.get(pk) != pv:
                problems.append(f"param_drift:{i}:{pk}:{params.get(pk)!r}!={pv!r}")
        label = rec.get("source_label")
        layer = rec.get("layer")
        if label in report["rates"] and layer in report["rates"][label]:
            want_rate = report["rates"][label][layer]["R_i"]
            if not (isinstance(rec.get("rate"), (int, float)) and
                    abs(float(rec["rate"]) - want_rate) < 1e-12):
                problems.append(f"rate_drift:{i}")
            want_rho = {str(k): v for k, v in
                        report["rates"][label][layer]["rho"].items()}
            got_rho = {str(k): v for k, v in (rec.get("rho") or {}).items()}
            if got_rho != want_rho:
                problems.append(f"rho_drift:{i}")
        if rec.get("not_fixed_packet_de") is not True:
            problems.append(f"not_fixed_packet_de_flag_missing:{i}")
        term, replay_reasons, replay_iters = _replay_terminal(rec)
        if term != rec.get("terminal"):
            problems.append(f"terminal_replay_mismatch:{i}:"
                            f"{rec.get('terminal')}!={term}")
        if term != "PASS" and not replay_reasons and not rec.get("reason_codes"):
            problems.append(f"missing_reason_codes:{i}")
        if term == "PASS" and rec.get("reason_codes"):
            problems.append(f"pass_with_reasons:{i}")
        if term == "PASS":
            need = rec.get("iterations")
            if need is None or need < STREAK or need > MAX_ITER:
                problems.append(f"pass_iterations_out_of_range:{i}:{need}")
            elif need != replay_iters:
                problems.append(f"pass_iterations_replay_mismatch:{i}:"
                                f"{need}!={replay_iters}")

    # duplicate/missing coverage independent of ordering
    wanted = {(c["source_label"], c["layer"], c["seed"]) for c in expected}
    missing = wanted - seen
    if missing:
        problems.append(f"missing_calls:{sorted(missing)}")

    # cell + overall recomputation
    if records:
        cells, overall = aggregate(records, report["rates"])
        cell_path = run_root / "de_cell_matrix.json"
        if not cell_path.exists():
            problems.append("de_cell_matrix.json missing")
        else:
            stored_cells = json.loads(cell_path.read_text(encoding="utf-8")).get("cells") or {}
            if {k: v.get("terminal") for k, v in stored_cells.items()} != \
                    {k: v["terminal"] for k, v in cells.items()}:
                problems.append("cell_terminals_recompute_mismatch")
        final_path = run_root / "final_state.json"
        if not final_path.exists():
            problems.append("final_state.json missing")
        else:
            final_state = json.loads(final_path.read_text(encoding="utf-8"))
            if final_state.get("overall_terminal") != overall["terminal"]:
                problems.append("overall_terminal_recompute_mismatch:"
                                f"{final_state.get('overall_terminal')}!={overall['terminal']}")
            if final_state.get("overall_label") != overall["label"]:
                problems.append("overall_label_recompute_mismatch")
            if final_state.get("not_fixed_packet_de") is not True:
                problems.append("final_state_not_fixed_packet_de_flag")
            if final_state.get("qualification") is not False or \
                    final_state.get("promotion") is not False:
                problems.append("claim_flags_invalid")

    verdict = {
        "verdict": "consistent" if not problems else "evidence_inconsistent",
        "run_root": str(run_root),
        "problems": problems,
        "records_checked": len(records),
    }
    print(json.dumps(verdict, indent=2))
    return EXIT_OK if not problems else EXIT_EVIDENCE_INCONSISTENT


# --------------------------------------------------------------------------- #
# Built-in tiny synthetic self-check (fake data only; no real inputs, no writes)
# --------------------------------------------------------------------------- #

def selfcheck() -> int:
    checks: list[dict] = []

    def expect(name: str, cond: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(cond), "detail": detail})

    ident = check_field_identity()
    expect("gf32_field_identity", ident["match"], ident["computed_field_id"])

    rho_l1 = make_rho(1.0 - M1 / N_BLOCKS)
    expect("rho_L1_concentrated_dc128", rho_l1 == {128: 1.0}, canonical_json(rho_l1))
    rho_l2 = make_rho(1.0 - 184 / N_BLOCKS)
    integ = sum(w / d for d, w in rho_l2.items())
    expect("rho_L2_harmonic_exact",
           abs(integ - (1.0 - (1.0 - 184 / N_BLOCKS)) * 0.5) < 1e-12,
           f"{integ!r} vs {(184 / N_BLOCKS) * 0.5!r}")
    expect("rho_L2_two_point_adjacent",
           sorted(rho_l2) in ([11, 12], [12]), canonical_json(rho_l2))

    # H_t means over population rows M (=shape[0]), NOT n=1024 (SHALL-CONV1)
    pop = np.zeros((7, Q))
    entropies = []
    for i in range(7):
        pop[i, i] = 1.0 - (i + 1) * 0.05
        rest = 1.0 - pop[i, i]
        for j in range(1, Q):
            pop[i, j] = rest / (Q - 1)
        p = pop[i]
        ent = -(p[p > 0] * np.log2(p[p > 0])).sum()
        entropies.append(ent)
    expect("mean_bits_entropy_M_not_n",
           abs(mean_bits_entropy(pop) - float(np.mean(entropies))) < 1e-12,
           f"M=7 rows, got {mean_bits_entropy(pop)!r}")

    # centering puts the true symbol at index 0
    rows = np.zeros((2, Q)); rows[0, 5] = 1.0; rows[1, 9] = 0.5; rows[1, 3] = 0.5
    centered = _center_rows(rows, np.array([5, 3]))
    expect("gf_xor_centering_truth_at_zero",
           abs(centered[0, 0] - 1.0) < 1e-15 and abs(centered[1, 0] - 0.5) < 1e-15
           and abs(centered[1, 10] - 0.5) < 1e-15)

    # zero-denominator => inconclusive_input_binding, no one-hot fallback
    degenerate_counts = np.zeros((N_BLOCKS, N_BLOCKS))
    degenerate_counts[0, 0] = 10.0
    qd = build_q_joint(degenerate_counts)
    expect("build_q_joint_delta", qd["p_u1_gb"][0, 0] == 1.0)
    raised = False
    try:
        _l2_rows(qd, np.array([7]), np.array([3]))  # P(U1=3|B=7) undefined
    except ZeroDenominatorError:
        raised = True
    expect("zero_denominator_raises", raised)

    # separable toy channel (single (A,B) pair) => PASS via full pipeline
    toy = np.zeros((N_BLOCKS, N_BLOCKS)); toy[5, 3] = 1000.0
    rec_pass = mcde_iterate(build_q_joint(toy), "L2", 12345, rate=0.984375,
                            n_samples=64, max_iter=40, entropy_tol_bits=1e-6,
                            streak_target=5)
    expect("toy_separable_channel_PASS", rec_pass["terminal"] == "PASS",
           canonical_json({k: rec_pass[k] for k in ("terminal", "iterations")}))
    # uniform toy channel => H_t stuck at 5 bits => FAIL at max_iter (no crash)
    uni = np.full((N_BLOCKS, N_BLOCKS), 1.0)
    rec_fail = mcde_iterate(build_q_joint(uni), "L1", 999, rate=0.984375,
                            n_samples=64, max_iter=8)
    expect("toy_uniform_channel_FAIL_max_iter",
           rec_fail["terminal"] == "FAIL" and rec_fail["iterations"] == 8 and
           len(rec_fail["entropy_trace_bits"]) == 8,
           canonical_json({k: rec_fail[k] for k in ("terminal", "iterations")}))

    ok = all(c["ok"] for c in checks)
    print(json.dumps({"selfcheck_ok": ok, "checks": checks}, indent=2))
    return EXIT_OK if ok else EXIT_SELFCHECK_FAILED


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_nonbinary_v33_rate_aligned_empirical_de",
        description="V33 rate-aligned empirical-channel ensemble DE diagnostic "
                    "(ensemble/channel layer only; not_fixed_packet_de=true).")
    sub = parser.add_subparsers(dest="command", required=True)

    p_prep = sub.add_parser("prepare", help="stage-0 R1-R7 binding validation report")
    p_prep.add_argument("--report-out", default=None,
                        help="optional path to also write the binding report JSON")
    p_prep.add_argument("--runner", default=None, help="MODULE:ATTR fake provider (tests)")
    p_prep.set_defaults(func=cmd_prepare)

    p_ver = sub.add_parser("verify", help="read-only evidence recompute in a run root")
    p_ver.add_argument("--run-root", required=True)
    p_ver.add_argument("--runner", default=None, help="MODULE:ATTR fake provider (tests)")
    p_ver.set_defaults(func=cmd_verify)

    p_chk = sub.add_parser("test-selfcheck", help="tiny synthetic self-check (no real inputs)")
    p_chk.set_defaults(func=lambda _args: selfcheck())

    p_exe = sub.add_parser("execute", help="production DE execution (authorized, exact-once)")
    p_exe.add_argument("--run-root", default=str(OFFICIAL_RUN_ROOT))
    p_exe.add_argument("--execute-auth-file", default=None,
                       help='JSON file with {"granted": true, ...}')
    p_exe.add_argument("--runner", default=None, help="MODULE:ATTR fake provider (tests)")
    p_exe.set_defaults(func=cmd_execute)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
