"""V17 Stage 1 — frozen multibit channel model
(``formal-nonbinary-ldpc-v17-multibit-structured-de-gate``, additive layer).

The V17 multibit channel model maps the V13 D01 characterization observation
into a frozen per-bit-plane channel prior.  It is built **read-only** from the
V13 characterization package (``comparison_bench/outputs_comparison/
nonbinary_diagnostics/v13_d01_20260814/channel_diagnostics.json``): no frame
arrays are re-loaded, no decoder is executed, and no new measurement is
performed — the per-bit-plane error probabilities are read from the published
D01 aggregate and re-declared as the frozen model.

Frozen contents (design section 3):

- **per-bit-plane error probability vector** ``{p_1 .. p_10}`` (MSB-first,
  monotonically increasing), read from
  ``aggregates.bit_plane_mismatch.mismatch_rate`` (V13 D01, gray mapping,
  128 characterization frames / 32768 symbols);
- **joint-structure declaration**: ``independent_bit_plane_conservative`` — the
  model declares the planes approximately independent (the D01 package does not
  persist a per-plane joint error distribution, only the aggregate per-plane
  mismatch rates), which is the conservative frozen assumption; the declaration
  is explicit and never silently promoted to a fitted joint model.

Persistence schema ``nbldpc_v17_multibit_channel_model_v1`` (``diagnostic_only``).
The production loader is lazy and requires ``production_authorized=True``; the
test lane builds from synthetic frames or from an explicit in-memory aggregate.

Only numpy and the standard library are imported.  This module never executes a
decoder and never reads the real source sidecars at import time.
"""
from __future__ import annotations

import json
import math
import os
from numbers import Integral
from typing import Any, Mapping

import numpy as np

# --------------------------------------------------------------------------- #
# frozen schema / constants
# --------------------------------------------------------------------------- #

#: Schema of the V17 multibit channel model doc.
CHANNEL_MODEL_SCHEMA = "nbldpc_v17_multibit_channel_model_v1"

#: Frozen joint-structure declaration values.
JOINT_INDEPENDENT = "independent_bit_plane_conservative"

#: Frozen domain (V13 D01): q=1024, 10 bit planes, gray mapping.
Q = 1024
BIT_PLANES = 10
MAPPING = "gray"

#: The V13 D01 characterization package directory (read-only source).
#: Resolved relative to the repo root at call time (never at import).
DEFAULT_D01_ROOT = os.path.join(
    "comparison_bench", "outputs_comparison", "nonbinary_diagnostics",
    "v13_d01_20260814")


# --------------------------------------------------------------------------- #
# validation / construction helpers
# --------------------------------------------------------------------------- #

def _validate_mismatch_rates(rates: Any) -> np.ndarray:
    vector = np.asarray(rates, dtype=np.float64)
    if vector.shape != (BIT_PLANES,):
        raise ValueError(f"per-bit-plane rates must have length {BIT_PLANES} "
                         f"(got {vector.shape})")
    if not np.all(np.isfinite(vector)) or np.any(vector < 0.0) or np.any(vector > 1.0):
        raise ValueError("per-bit-plane rates must be finite in [0, 1]")
    # Strictly positive: a zero plane would remove a bit (not a multibit model).
    if np.any(vector == 0.0):
        raise ValueError("per-bit-plane rates must be strictly positive")
    # MSB-first monotone non-decreasing (the V13 D01 frozen observation).
    if np.any(np.diff(vector) < -1e-15):
        raise ValueError("per-bit-plane rates must be MSB-first monotone non-decreasing")
    return vector


def binary_entropy_bits(p: float) -> float:
    """``h2(p)`` in bits; 0 at the endpoints."""
    if isinstance(p, bool) or not isinstance(p, (int, float)) \
            or not math.isfinite(float(p)) or not 0.0 <= float(p) <= 1.0:
        raise ValueError("p must be finite in [0, 1]")
    p = float(p)
    if p == 0.0 or p == 1.0:
        return 0.0
    return float(-p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p))


def total_leakage_bits(mismatch_rates: Any) -> float:
    """Total bit-plane leakage ``sum_i h2(p_i)`` (bits/symbol) under the
    conservative independent-plane declaration (the V17 ``f`` denominator)."""
    rates = _validate_mismatch_rates(mismatch_rates)
    return float(sum(binary_entropy_bits(float(p)) for p in rates))


def build_channel_model_doc(mismatch_rates: Any, *, run_id: str = "v17_multibit",
                            source_path: str | None = None,
                            source_fields: Mapping[str, Any] | None = None,
                            joint_structure: str = JOINT_INDEPENDENT,
                            q: int = Q, bit_planes: int = BIT_PLANES,
                            mapping: str = MAPPING,
                            frames_used: int | None = None,
                            symbols_used: int | None = None) -> dict[str, Any]:
    """Build the ``nbldpc_v17_multibit_channel_model_v1`` doc.

    ``mismatch_rates`` is the MSB-first per-bit-plane error probability vector
    (read from V13 D01 ``aggregates.bit_plane_mismatch.mismatch_rate`` in the
    production lane; synthetic in the test lane).  The joint structure is
    declared (default: conservative independent planes); the total leakage
    ``entropy_bits`` is ``sum_i h2(p_i)``.
    """
    if q != Q or bit_planes != BIT_PLANES:
        raise ValueError("V17 channel model is frozen to q=1024, 10 bit planes")
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or int(q) & (int(q) - 1):
        raise ValueError("q must be a power of two >= 2")
    if mapping != MAPPING:
        raise ValueError("V17 channel model is frozen to gray mapping")
    rates = _validate_mismatch_rates(mismatch_rates)
    if joint_structure not in (JOINT_INDEPENDENT,):
        raise ValueError(f"unknown joint-structure declaration: {joint_structure}")
    plane_entropies = [float(binary_entropy_bits(float(p))) for p in rates]
    return {
        "schema": CHANNEL_MODEL_SCHEMA,
        "run_id": str(run_id),
        "q": int(q),
        "bit_planes": int(bit_planes),
        "mapping": mapping,
        "per_bit_plane_error_probability_msb_first": [float(x) for x in rates],
        "joint_structure": joint_structure,
        "joint_structure_form": "product_of_per_plane_marginals",
        "joint_structure_note": (
            "per-plane error probabilities are the V13 D01 aggregate MSB-first "
            "bit-plane mismatch rates; joint bit-plane error statistics are NOT "
            "persisted anywhere in the D01 package (aggregate-only, per-position "
            "data not persisted), so per frozen design section 3 the model "
            "DECLARES the conservative independent approximation: the joint "
            "symbol-difference distribution is the product of the per-plane "
            "marginals. This is an explicit declared modeling assumption, never "
            "a fitted joint model and never fabricated from absent data."),
        "per_bit_plane_entropy_bits": plane_entropies,
        "entropy_bits": float(sum(plane_entropies)),
        "frames_used": frames_used,
        "symbols_used": symbols_used,
        "source_path": source_path,
        "source_fields": dict(source_fields or {}),
        "fit_source": "v13 d01 characterization aggregate (read-only)",
        "diagnostic_only": True,
        "retrospective_reuse": True,
    }


# --------------------------------------------------------------------------- #
# lazy production loader (execute-only)
# --------------------------------------------------------------------------- #

def load_production_mismatch_rates(*, production_authorized: bool = False,
                                   d01_root: str | None = None) -> tuple[dict, list[float]]:
    """Read the frozen per-bit-plane mismatch rates from the V13 D01
    ``channel_diagnostics.json`` (read-only aggregate; no frame loader, no
    decoder).  Requires ``production_authorized=True`` (hard stop otherwise).

    Returns ``(channel_diagnostics_doc, mismatch_rates)``.  The source fields
    consumed are ``aggregates.bit_plane_mismatch.mismatch_rate`` (the MSB-first
    10-vector) and the ``aggregates.domain`` block (frames/symbols/mapping).
    """
    root = _repo_root()
    d01_path = root / (d01_root or DEFAULT_D01_ROOT) / "channel_diagnostics.json"
    if not production_authorized:
        raise ValueError("load_production_mismatch_rates requires production_authorized=True")
    if not d01_path.is_file():
        raise FileNotFoundError(f"V13 D01 channel_diagnostics.json missing: {d01_path}")
    doc = json.loads(d01_path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or doc.get("schema") != "nbldpc_v13_channel_diagnostics_v1":
        raise ValueError(f"unexpected V13 D01 schema at {d01_path}")
    bit_plane = (doc.get("aggregates") or {}).get("bit_plane_mismatch") or {}
    rates = bit_plane.get("mismatch_rate")
    if not isinstance(rates, list) or len(rates) != BIT_PLANES:
        raise ValueError("V13 D01 bit_plane_mismatch.mismatch_rate missing or wrong length")
    return doc, [float(x) for x in rates]


def build_production_channel_model(*, production_authorized: bool = False,
                                   d01_root: str | None = None,
                                   run_id: str = "v17_multibit") -> dict:
    """Production lane: build the model doc read-only from the V13 D01 package.

    The per-plane rates come from ``aggregates.bit_plane_mismatch.mismatch_rate``;
    ``frames_used`` / ``symbols_used`` from ``aggregates.domain``; the source
    field provenance is recorded verbatim in ``source_fields``.
    """
    doc, rates = load_production_mismatch_rates(
        production_authorized=production_authorized, d01_root=d01_root)
    agg = (doc.get("aggregates") or {})
    domain = agg.get("domain") or {}
    frames = domain.get("frames")
    symbols = domain.get("symbols")
    cond = agg.get("conditional_entropy") or {}
    qsc = agg.get("qsc_p20") or {}
    src = {
        "schema": doc.get("schema"),
        "run_id": doc.get("run_id"),
        "field_mismatch_rate": "aggregates.bit_plane_mismatch.mismatch_rate",
        "field_domain": "aggregates.domain",
        "empirical_conditional_entropy_bits_per_symbol_src":
            "aggregates.conditional_entropy.empirical_conditional_entropy_bits_per_symbol",
        "empirical_conditional_entropy_bits_per_symbol":
            cond.get("empirical_conditional_entropy_bits_per_symbol"),
        "empirical_ser_src": "aggregates.qsc_p20.empirical_ser",
        "empirical_ser": qsc.get("empirical_ser"),
        "joint_statistics_persisted": False,
    }
    return build_channel_model_doc(
        rates, run_id=run_id,
        source_path=str((_repo_root() / (d01_root or DEFAULT_D01_ROOT)
                         / "channel_diagnostics.json")),
        source_fields=src, frames_used=frames, symbols_used=symbols)


# --------------------------------------------------------------------------- #
# test-lane builders (synthetic, never production)
# --------------------------------------------------------------------------- #

def synthetic_mismatch_rates(*, seed: int = 2026090301,
                             bit_planes: int = BIT_PLANES) -> list[float]:
    """Deterministic monotone MSB-first per-plane rates for the test lane only
    (a monotonically increasing profile, clearly labelled synthetic)."""
    if isinstance(bit_planes, bool) or not isinstance(bit_planes, Integral) \
            or int(bit_planes) < 1:
        raise ValueError("bit_planes must be a positive integer")
    rng = np.random.default_rng(int(seed))
    raw = np.sort(rng.uniform(1e-5, 5e-2, size=int(bit_planes)))
    raw = np.clip(raw, 1e-6, 0.49)
    return [float(x) for x in raw]


def _repo_root():
    from pathlib import Path
    return Path(__file__).resolve().parents[4]
