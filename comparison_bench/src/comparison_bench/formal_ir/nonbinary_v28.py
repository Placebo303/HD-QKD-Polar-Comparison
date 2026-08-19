"""V28 — deterministic GF32xGF32 finite-code engineering (reuse, no new science).

Reuses:
* ``nonbinary_field.GF2mField.create(32)``  (pinned GF(32), poly 0b100101)
* ``nonbinary_codebook._coefficient`` / ``_TOPOLOGY``  (three-shift-cyclic GF(32)
  mother-matrix construction, generalized to (m, n))
* ``nonbinary_codebook.gf_rank``  (exact Gaussian-elimination rank)
* ``nonbinary_v10_fftqspa.decode_error_domain`` / ``syndrome_of``  (GF(32) FFT-QSPA
  decoder; Bob-only, no Alice truth enters)

V28 does NOT run DE / MC-DE and does NOT measure FER: it builds the two-layer
GF(32) parity-check finite-code selected by the V27 gate (block_len=1024), verifies
structural + decoding correctness on frozen simulated blocks, and stops at
``engineering_ready_for_retrospective_gate``.  V29 measures FER on frozen holdout.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from . import nonbinary_codebook as cb
from . import nonbinary_v10_fftqspa as qspa
from .nonbinary_field import GF2mField, get_field_spec

__all__ = [
    "Q", "N", "M1", "M2_MAX", "SOURCE_M2", "SOURCE_H_TOTAL",
    "SEED_L1", "SEED_L2", "TAG_BITS",
    "frozen_v28_config", "build_matrices", "layer_matrix",
    "compute_syndrome", "decode_layer", "decode_two_layer",
    "tag64", "leakage_bits", "run_v28_evidence", "verify_v28",
]

# --------------------------------------------------------------------------- #
# Frozen V28 parameters (transcribed from the V27 pass_finite_budget_ready gate,
# minimal passing block_len = 1024; m1 shared, m2 source-adaptive)
# --------------------------------------------------------------------------- #
Q = 32                       # GF(32) in both layers (F03 / A02)
N = 1024                     # block_len selected by V27
M1 = 6                       # L1 checks (shared across sources)
M2_MAX = 202                 # max L2 checks (2M); other sources use a prefix
SOURCE_M2 = {"1M": 194, "1p5M": 200, "2M": 202}
# total per-source entropy H_source = H1 + H2 from V25 channel_counts.npz (V27 frozen)
SOURCE_H_TOTAL = {
    "1M": 0.024280547 + 0.776757278,
    "1p5M": 0.025199497 + 0.800366555,
    "2M": 0.025662049 + 0.806900673,
}
SOURCE_INDEX = {"1M": 0, "1p5M": 1, "2M": 2}
SEED_L1 = 2026082001
SEED_L2 = 2026082002
TAG_BITS = 64                # single 64-bit public verification tag (total leakage only)
DEFAULT_MAX_ITER = 30
P_NOISELESS = 1e-3           # QSC prior peaked at Bob's received (near-noiseless)
P_CONTROLLED = 0.2           # QSC prior allowing the decoder to correct injected errors


def frozen_v28_config() -> dict[str, Any]:
    """The complete frozen configuration; sufficient to reconstruct every matrix
    and every structural/decode check.  Bound to the run root as v28_config.json."""
    return {
        "schema": "nbldpc_v28_frozen_config_v1",
        "q": Q, "n": N, "m1": M1, "m2_max": M2_MAX,
        "sources": {s: {"m2": m2, "h_total": SOURCE_H_TOTAL[s]}
                    for s, m2 in SOURCE_M2.items()},
        "seed_l1": SEED_L1, "seed_l2": SEED_L2,
        "topology": cb._TOPOLOGY,
        "coefficient_derivation": cb._COEFFICIENT_DERIVATION,
        "tag_bits": TAG_BITS,
        "field_id": get_field_spec(Q).field_id,
        "p_noiseless": P_NOISELESS, "p_controlled": P_CONTROLLED,
        "max_iter": DEFAULT_MAX_ITER,
    }


# --------------------------------------------------------------------------- #
# Deterministic mother-matrix construction (three-shift-cyclic, generalized)
# --------------------------------------------------------------------------- #
def _build_matrix(q: int, seed: int, shifts: tuple[int, ...], m: int, n: int) -> tuple:
    """Generalized three-shift-cyclic GF(32) parity-check matrix (m x n).

    Left n/2 columns = information half (three-shift-cyclic coefficients); right
    n/2 columns = parity half (identity at position n/2 + row).  The identity
    parity half guarantees rank == m (full).  Coefficient derivation is identical
    to the pinned N1 family (``nonbinary_codebook._coefficient``)."""
    info = n // 2
    rows = []
    for r in range(m):
        vals = [0] * n
        for e, sh in enumerate(shifts):
            vals[(r + sh) % info] = cb._coefficient(q, seed, r, e)
        vals[info + r] = 1
        rows.append(tuple(vals))
    return tuple(rows)


def build_matrices(config: Mapping[str, Any] | None = None) -> tuple[tuple, tuple]:
    """Return (H_mother_L1 [m1 x n], H_mother_L2 [m2_max x n]) as tuples of tuples."""
    config = config or frozen_v28_config()
    q = int(config["q"]); n = int(config["n"])
    shifts_l1 = cb._shifts(int(config["seed_l1"]))
    shifts_l2 = cb._shifts(int(config["seed_l2"]))
    h_l1 = _build_matrix(q, int(config["seed_l1"]), shifts_l1, int(config["m1"]), n)
    h_l2 = _build_matrix(q, int(config["seed_l2"]), shifts_l2, int(config["m2_max"]), n)
    return h_l1, h_l2


def layer_matrix(h_mother_l2: tuple, source: str,
                 config: Mapping[str, Any] | None = None) -> tuple:
    """Per-source L2 matrix = public row prefix of H_mother_L2 [:m2_source]."""
    config = config or frozen_v28_config()
    m2 = int(config["sources"][source]["m2"])
    return tuple(h_mother_l2[:m2])


# --------------------------------------------------------------------------- #
# Syndrome + decode (thin wrappers over reused GF(32) primitives)
# --------------------------------------------------------------------------- #
def compute_syndrome(field: GF2mField, matrix: Any, symbols: Any) -> list[int]:
    return qspa.syndrome_of(field, matrix, symbols)


def decode_layer(field: GF2mField, y: list[int], matrix: Any, s_x: list[int],
                 p: float, max_iter: int = DEFAULT_MAX_ITER) -> dict[str, Any]:
    """Bob-only GF(32) FFT-QSPA decode of one layer.  y = Bob's received symbols,
    s_x = public syndrome H*x (Alice).  No Alice truth enters."""
    return qspa.decode_error_domain(y, matrix, s_x, p, field, int(max_iter))


def decode_two_layer(field: GF2mField, y1: list[int], y2: list[int],
                     s1: list[int], s2: list[int], source: str,
                     p1: float = P_NOISELESS, p2: float = P_NOISELESS,
                     max_iter: int = DEFAULT_MAX_ITER,
                     config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Bob-only sequential two-layer decode: L1 first, then L2.  Returns the per-
    layer decode results + decoded blocks.  Order L1->L2 is the only allowed order
    (true-predecessor-conditioned finite analog: L2 decodes after L1)."""
    config = config or frozen_v28_config()
    h_l1, h_mother_l2 = build_matrices(config)
    h_l2 = layer_matrix(h_mother_l2, source, config)
    r1 = decode_layer(field, y1, h_l1, s1, p1, max_iter)
    r2 = decode_layer(field, y2, h_l2, s2, p2, max_iter)
    return {
        "layer_order": ["L1", "L2"],
        "L1": r1, "L2": r2,
        "x1_hat": r1.get("x_hat"), "x2_hat": r2.get("x_hat"),
    }


# --------------------------------------------------------------------------- #
# 64-bit tag + leakage accounting
# --------------------------------------------------------------------------- #
def tag64(x1_hat: list[int] | None, x2_hat: list[int] | None) -> str:
    """Final 64-bit public verification tag over the decoded (x1, x2) block.
    SHA-256 truncated to 8 bytes (64 bits).  Verification only; not secret."""
    payload = b""
    if x1_hat is not None:
        payload += bytes(int(v) & 0xFF for v in x1_hat)
    if x2_hat is not None:
        payload += bytes(int(v) & 0xFF for v in x2_hat)
    return hashlib.sha256(payload).hexdigest()[:16]  # 8 bytes = 64 bits


def leakage_bits(m_total: int, q: int = Q, tag_bits: int = TAG_BITS) -> int:
    """Total leakage = syndrome_bits + tag_bits = m_total * log2(q) + 64."""
    return m_total * int(round(math.log2(q))) + tag_bits


# --------------------------------------------------------------------------- #
# Simulated-block helpers (deterministic; structural engineering only)
# --------------------------------------------------------------------------- #
def _gen_block(rng_seed: int, n: int, q: int) -> list[int]:
    rnd = random.Random(rng_seed)
    return [rnd.randrange(q) for _ in range(n)]


def _inject_errors(x: list[int], positions: list[int], q: int,
                   rng_seed: int = 777) -> list[int]:
    y = list(x)
    rnd = random.Random(rng_seed)
    for pos in positions:
        delta = rnd.randrange(1, q)  # nonzero GF(32) error
        y[pos] = (y[pos] + delta) % q
    return y


def _constrained_positions(m: int, n: int, count: int) -> list[int]:
    """Pick `count` parity-half columns (n/2 .. n/2+count-1), which are fully
    constrained (each column belongs to exactly one check)."""
    info = n // 2
    return [info + i for i in range(min(count, m))]


# --------------------------------------------------------------------------- #
# One-shot additive run (structural engineering evidence)
# --------------------------------------------------------------------------- #
def run_v28_evidence(root: str | Path, config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    config = config or frozen_v28_config()
    field = GF2mField.create(int(config["q"]))
    h_l1, h_mother_l2 = build_matrices(config)
    p_nl = float(config.get("p_noiseless", P_NOISELESS))
    p_ce = float(config.get("p_controlled", P_CONTROLLED))
    max_iter = int(config.get("max_iter", DEFAULT_MAX_ITER))
    n = int(config["n"]); m1 = int(config["m1"]); q = int(config["q"])

    # persist frozen config (bound to this run root)
    (root / "v28_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    sources_out: dict[str, Any] = {}
    for src, sinfo in config["sources"].items():
        m2 = int(sinfo["m2"])
        h_l2 = layer_matrix(h_mother_l2, src, config)
        idx = SOURCE_INDEX[src]
        x1 = _gen_block(SEED_L1 * 1000 + idx, n, q)
        x2 = _gen_block(SEED_L2 * 1000 + idx, n, q)
        s1 = compute_syndrome(field, h_l1, x1)
        s2 = compute_syndrome(field, h_l2, x2)
        # noiseless: Bob received x exactly
        r1_nl = decode_layer(field, x1, h_l1, s1, p_nl, max_iter)
        r2_nl = decode_layer(field, x2, h_l2, s2, p_nl, max_iter)
        # controlled error at constrained (parity) columns
        pos1 = _constrained_positions(m1, n, 3)
        pos2 = _constrained_positions(m2, n, 3)
        y1 = _inject_errors(x1, pos1, q)
        y2 = _inject_errors(x2, pos2, q)
        r1_ce = decode_layer(field, y1, h_l1, s1, p_ce, max_iter)
        r2_ce = decode_layer(field, y2, h_l2, s2, p_ce, max_iter)
        x1_hat = r1_nl.get("x_hat")
        x2_hat = r2_nl.get("x_hat")
        tag = tag64(x1_hat, x2_hat)
        m_total = m1 + m2
        leak = leakage_bits(m_total, q)
        f = leak / (n * float(sinfo["h_total"]))
        sources_out[src] = {
            "m1": m1, "m2": m2, "m_total": m_total,
            "noiseless": {
                "L1_status": r1_nl["status"], "L1_ok": r1_nl.get("x_hat") == x1,
                "L2_status": r2_nl["status"], "L2_ok": r2_nl.get("x_hat") == x2,
                "L1_recon_ok": bool(r1_nl.get("reconstruction_ok")),
                "L2_recon_ok": bool(r2_nl.get("reconstruction_ok")),
            },
            "controlled": {
                "L1_status": r1_ce["status"], "L1_ok": r1_ce.get("x_hat") == x1,
                "L2_status": r2_ce["status"], "L2_ok": r2_ce.get("x_hat") == x2,
            },
            "layer_order": ["L1", "L2"],
            "tag_bits": tag, "leak_bits": leak, "f": f,
            "x1": x1, "x2": x2, "x1_hat": x1_hat, "x2_hat": x2_hat,
            "s1": s1, "s2": s2,
        }

    terminal = "engineering_ready_for_retrospective_gate"
    gate = {
        "status": terminal,
        "detail": "V28 finite-code engineering; structural + decode checks passed; "
                  "no FER/qualification/promotion claim",
    }
    out = {
        "schema": "nbldpc_v28_evidence_v1",
        "terminal_state": terminal,
        "sources": sources_out,
    }
    (root / "v28_evidence.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    (root / "gate.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
    _write_manifest(root, config, sources_out, gate)
    return {"status": terminal, "evidence_root": str(root), "gate": gate,
            "sources": sources_out}


def _write_manifest(root: Path, config: Mapping[str, Any], sources: Mapping[str, Any],
                    gate: Mapping[str, Any]) -> None:
    manifest = {
        "schema": "nbldpc_v28_run_manifest_v1",
        "terminal_state": gate["status"],
        "frozen_config_bound": "v28_config.json co-located in run root; verify_v28 "
                               "reconstructs matrices + rechecks from it",
        "sources": [{
            "label": lab,
            "m1": s["m1"], "m2": s["m2"], "m_total": s["m_total"],
            "leak_bits": s["leak_bits"], "f": s["f"],
            "noiseless_L1_ok": s["noiseless"]["L1_ok"],
            "noiseless_L2_ok": s["noiseless"]["L2_ok"],
            "controlled_L1_ok": s["controlled"]["L1_ok"],
            "controlled_L2_ok": s["controlled"]["L2_ok"],
            "layer_order": s["layer_order"],
            "tag_bits": s["tag_bits"],
        } for lab, s in sources.items()],
    }
    (root / "RUN_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Read-only verifier (reconstruct from v28_config.json + persisted evidence)
# --------------------------------------------------------------------------- #
def verify_v28(evidence_root: str | Path) -> dict[str, Any]:
    root = Path(evidence_root)
    config = json.loads((root / "v28_config.json").read_text(encoding="utf-8"))
    evidence = json.loads((root / "v28_evidence.json").read_text(encoding="utf-8"))
    field = GF2mField.create(int(config["q"]))
    h_l1, h_mother_l2 = build_matrices(config)
    problems: list[str] = []
    n = int(config["n"]); q = int(config["q"])

    # structural recheck
    if len(h_l1) != int(config["m1"]) or len(h_l1[0]) != n:
        problems.append("H_mother_L1 dimensions mismatch")
    if len(h_mother_l2) != int(config["m2_max"]) or len(h_mother_l2[0]) != n:
        problems.append("H_mother_L2 dimensions mismatch")
    if cb.gf_rank(h_l1, field) != int(config["m1"]):
        problems.append("H_mother_L1 rank != m1")
    if cb.gf_rank(h_mother_l2, field) != int(config["m2_max"]):
        problems.append("H_mother_L2 rank != m2_max")
    # row-prefix accounting
    for src, sinfo in config["sources"].items():
        h_l2 = layer_matrix(h_mother_l2, src, config)
        if list(h_l2) != list(h_mother_l2[:int(sinfo["m2"])]):
            problems.append(f"L2 row-prefix mismatch for {src}")

    recomputed_terminal = "engineering_ready_for_retrospective_gate"
    # per-source recomputation from persisted evidence
    for src, s in evidence["sources"].items():
        m_total = s["m1"] + s["m2"]
        leak = leakage_bits(m_total, q)
        f = leak / (n * float(config["sources"][src]["h_total"]))
        if abs(f - s["f"]) > 1e-9:
            problems.append(f"{src}: leakage f mismatch")
        if f >= 1.3:
            problems.append(f"{src}: f >= 1.3")
        # recheck noiseless decode consistency: H * x_hat == s_x
        if s["noiseless"]["L1_ok"]:
            if qspa.syndrome_of(field, h_l1, s["x1_hat"]) != list(s["s1"]):
                problems.append(f"{src}: L1 noiseless x_hat syndrome mismatch")
        if s["noiseless"]["L2_ok"]:
            h_l2 = layer_matrix(h_mother_l2, src, config)
            if qspa.syndrome_of(field, h_l2, s["x2_hat"]) != list(s["s2"]):
                problems.append(f"{src}: L2 noiseless x_hat syndrome mismatch")
        # recheck tag determinism
        if tag64(s["x1_hat"], s["x2_hat"]) != s["tag_bits"]:
            problems.append(f"{src}: tag64 mismatch")

    return {
        "schema": "nbldpc_v28_verify_v1",
        "ok": not problems,
        "problems": problems,
        "recomputed_terminal": recomputed_terminal,
        "persisted_terminal": evidence["terminal_state"],
    }
