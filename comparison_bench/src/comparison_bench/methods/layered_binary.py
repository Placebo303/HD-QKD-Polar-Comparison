"""Layered-binary LDPC honest baseline (M2; implementation-only, fake-tested).

Replaces the V19 conservative-row (f=4.169) strawman with per-Gray-plane entropy
allocation + blind reconciliation (M2-LAYEREDBIN-SYNTH PACKET F2/F3/F5;
``openspec/changes/m2-honest-baselines/design.md`` §§4-5):

  T5 allocation table: per-plane rows {m_j}, Σm_j = m (this-arm m basis), H input
     frozen (1M 0.801038 / 1.5M 0.825566 / 2M 0.832563), never refit;
  T6 per-plane construction: n=64 family semantics preserved; production path reuses
     the existing PEG (``formal_ir.nonbinary_v10_peg.peg_construct``) read-only
     (imported, never modified); tiny fake frames pass explicit ``allow_non64=True``;
  T7 blind reconciliation: multi-stage small steps (m_init + {Δm_k}); every stage
     disclosure joins the leak_EC decomposition; binary SPA max_iter–streak frozen
     (b2f MAX_ITER machine-checked, streak frozen, tuning refused; override refused);
     success requires per-plane syndrome consistency + Toeplitz verification (t=64).

Accounting mirrors the HD-Cascade arm (four counts, f triple this-arm m basis,
λ_total decomposition, 1.50x prior report-only, LDPC 3.14 message aperture with the
Cascade 446 aperture as non-comparable annotation, undetected isolation, no SKR).

Tests MUST inject explicit fake ``construct_fn``/``decode_fn``; the production PEG +
binary-SPA path is never entered by fake tests (guarded there by monkeypatch).
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from .layered_ldpc_lite import split_symbol_bitplanes
from ..metrics.leakage import compute_beta_eff_empirical
from ..types import FrameBatch, IRRunConfig, IRRunResult
from ..utils.bitops import bit_error_rate, bits_per_symbol, flatten_bits, frame_symbol_error_rate

# ---------------------------------------------------------------- frozen literals
# (carried, not invented: M2-LAYEREDBIN-SYNTH PACKET F2/F4/F5 + b2f/v28 pins).

#: Frozen per-source H sums used ONLY as allocation input (PACKET F2; no refit).
FROZEN_H: dict[str, float] = {"1M": 0.801038, "1p5M": 0.825566, "2M": 0.832563}

#: Frozen f_eff slope (PACKET F5; x1_arm_runner.F_EFF_SLOPE).
F_EFF_SLOPE_FROZEN = 4.785675

#: Frozen verification tag width (Toeplitz t=64, design §5).
TAG_BITS_FROZEN = 64

#: Frozen prior opportunity-cost scale: report-only, never into λ_total/f numerators.
PRIOR_SCALE_REPORTONLY = 1.50

#: Frozen binary-SPA pins (b2f MAX_ITER=300 / v28 streak default 3; cross-checked
#: read-only at run time; any override is refused).
SPA_MAX_ITER_FROZEN = 300
SPA_STREAK_FROZEN = 3

#: n=64 family semantic for per-plane construction (T6; PACKET F1 N-grid analogue).
N_FAMILY_FROZEN = 64

#: LDPC-level per-frame message aperture (T7/F5; independent column).
LDPC_MSG_PER_FRAME_REF = 3.14

#: Cascade aperture carried as a non-comparable annotation only (never mixed).
CASCADE_MSG_PER_FRAME_REF = 446

#: Claim-ceiling fixed sentence (M2 packets §5; carried verbatim on synthetic numbers).
CLAIM_CEILING = ("合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；"
                 "D1 条件化分支下不得用本批合成数论证真实优劣。")


# ------------------------------------------------------------- frozen param slots

@dataclass(frozen=True)
class PlaneAllocation:
    """T5: per-plane row allocation {plane j=0..9: rows m_j} with Σm_j = m (G-D gate)."""

    source_key: str
    h_basis: float
    m_basis: int
    plane_rows: Mapping[int, int]

    def validated(self, plane_bits: int) -> "PlaneAllocation":
        if self.source_key not in FROZEN_H:
            raise ValueError(f"unknown source_key {self.source_key!r} (frozen: 1M|1p5M|2M)")
        if abs(float(self.h_basis) - FROZEN_H[self.source_key]) > 1e-6:
            raise ValueError(f"h_basis {self.h_basis!r} != frozen H for {self.source_key} "
                             f"({FROZEN_H[self.source_key]}; allocation input only, no refit)")
        rows = {int(k): int(v) for k, v in dict(self.plane_rows).items()}
        if sorted(rows) != list(range(int(plane_bits))):
            raise ValueError(f"plane_rows must cover planes 0..{int(plane_bits) - 1} exactly")
        if any(v < 0 for v in rows.values()):
            raise ValueError("plane_rows must be non-negative ints")
        for j in sorted(rows):  # single-plane fail-closed gate, alongside the sum gate
            if rows[j] > N_FAMILY_FROZEN:
                raise ValueError(f"plane {j}: m_j={rows[j]} > n_plane={N_FAMILY_FROZEN} "
                                 f"(fail closed; single-plane rows cannot exceed plane length)")
        if sum(rows.values()) != int(self.m_basis):
            raise ValueError(f"Σm_j={sum(rows.values())} != m_basis={self.m_basis} "
                             f"(V19-style row substitution refused; recompute per-plane)")
        return self


@dataclass(frozen=True)
class BlindStageTable:
    """T7/F3: frozen blind schedule m_init + {Δm_1..Δm_k} (multi-stage small steps)."""

    m_init: int
    delta_steps: Sequence[int]

    def validated(self) -> "BlindStageTable":
        if not isinstance(self.m_init, int) or isinstance(self.m_init, bool) or self.m_init < 1:
            raise ValueError("m_init must be a positive int")
        steps = [int(x) for x in self.delta_steps]
        if not steps or any(s <= 0 for s in steps):
            raise ValueError("delta_steps must be a non-empty list of positive ints "
                             "(grant-time frozen; no mid-run extension)")
        return self


@dataclass(frozen=True)
class LayeredParams:
    """Arm-frozen scalar slots (grant-time filled; SPA pins checked, never tuned)."""

    source_key: str
    tag_bits: int = TAG_BITS_FROZEN
    max_iter: int = SPA_MAX_ITER_FROZEN
    streak: int = SPA_STREAK_FROZEN
    allow_non64: bool = False

    def validated(self) -> "LayeredParams":
        if self.source_key not in FROZEN_H:
            raise ValueError(f"unknown source_key {self.source_key!r}")
        if int(self.tag_bits) != TAG_BITS_FROZEN:
            raise ValueError(f"tag_bits frozen at {TAG_BITS_FROZEN}")
        if int(self.max_iter) != SPA_MAX_ITER_FROZEN or int(self.streak) != SPA_STREAK_FROZEN:
            raise ValueError(f"binary SPA max_iter/streak frozen at "
                             f"{SPA_MAX_ITER_FROZEN}/{SPA_STREAK_FROZEN} (no tuning)")
        _crosscheck_spa_freeze()
        return self


def _crosscheck_spa_freeze() -> None:
    """Read-only cross-check of the SPA pins against the frozen b2f config."""
    from ..formal_ir.v80_b2f_campaign import MAX_ITER as _b2f_max_iter
    if int(_b2f_max_iter) != SPA_MAX_ITER_FROZEN:
        raise ValueError("SPA max_iter freeze mismatch vs frozen b2f config (STOP)")


# ----------------------------------------------- packet-literal f/λ/N_req helpers

def f_super_packet_literal(m: int, h_basis: float) -> float:
    """Frozen F5 literal: f_super = (5m+64)/(1024·H_src), this-arm m basis."""
    return (5.0 * int(m) + 64.0) / (1024.0 * float(h_basis))


def f_notag_packet_literal(m: int, h_basis: float) -> float:
    """Frozen F5 literal: f_notag = 5m/(1024·H_src), this-arm m basis."""
    return (5.0 * int(m)) / (1024.0 * float(h_basis))


def f_eff_from(f_super: float, fer: float) -> float:
    """Frozen F5 literal: f_eff = f_super + 4.785675·FER (never f_super-as-f_eff)."""
    return float(f_super) + F_EFF_SLOPE_FROZEN * float(fer)


def lambda_total(leak_ec: float, tag_bits: float = TAG_BITS_FROZEN,
                 rescue_bits: float = 0.0, control_bits: float = 0.0) -> float:
    """Verification-aware λ_total = leak_EC + 64(tag) + rescue + control (each single column)."""
    return float(leak_ec) + float(tag_bits) + float(rescue_bits) + float(control_bits)


def n_required_reportonly(f_super: float) -> float:
    """Frozen G-C rule, report-only: N ≥ ceil(3·4.785675/(1.3−f_super)); inf if f≥1.3."""
    denom = 1.3 - float(f_super)
    if denom <= 0.0:
        return math.inf
    return float(math.ceil(3.0 * F_EFF_SLOPE_FROZEN / denom))


# ------------------------------------------------- production path (granted runs
# only; fake tests always inject construct_fn/decode_fn and monkeypatch these).

def _construct_plane_production(n_plane: int, m_rows: int, seed: int) -> dict[str, Any]:
    """Per-plane construction via the existing PEG, read-only (T6)."""
    from ..formal_ir.nonbinary_v10_peg import peg_construct
    from ..formal_ir.nonbinary_v26_mcde import make_rho
    from ..formal_ir import v80_s2_peg as _s2
    from ..formal_ir.nonbinary_field import GF2mField
    field = GF2mField.create(_s2.Q)
    lam = {2: 1.0}
    rho = make_rho(1.0 - int(m_rows) / int(n_plane), lam)
    return peg_construct(int(n_plane), int(m_rows), lam, rho, int(seed), max_trials=20, field=field)


def _spa_decode_production(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Binary-SPA production decode placeholder (frozen pins; granted runs only)."""
    raise NotImplementedError("production binary-SPA decode is grant-gated (no fake/test call)")


# ---------------------------------------------------------------- main entrypoint

#: Required fake/production outcome keys (missing key fails closed; never defaulted).
_OUTCOME_KEYS = ("exact_match", "accepted", "syndrome_consistent", "toeplitz_verified",
                 "leak_ec_bits", "blind_stage_bits", "rescue_bits", "control_bits",
                 "messages_actual", "prior_entropy_bits", "construction")


def run_layered_binary(batch: FrameBatch, cfg: IRRunConfig, *,
                       allocation: PlaneAllocation, stages: BlindStageTable,
                       params: LayeredParams,
                       construct_fn: Callable[..., Mapping[str, Any]] | None = None,
                       decode_fn: Callable[..., Mapping[str, Any]] | None = None) -> IRRunResult:
    """Run the layered-binary arm over a FrameBatch (fake tests MUST pass fakes)."""
    start = time.perf_counter()
    params.validated()
    if params.source_key != allocation.source_key:
        raise ValueError("source_key mismatch between params and allocation (no cross-source use)")
    plane_bits = bits_per_symbol(int(batch.dimension))
    allocation.validated(plane_bits)
    stages.validated()
    n_frames = int(batch.alice_symbols.shape[0])
    frame_symbols = int(batch.frame_len_symbols)
    if int(frame_symbols) != N_FAMILY_FROZEN and not params.allow_non64:
        raise ValueError(f"n=64 family semantic: frame_len {frame_symbols} != 64 "
                         f"(tiny fake frames require explicit allow_non64=True)")

    successes = failed_decode = failed_verify = 0
    accepted_wrong = 0
    sum_leak = sum_rescue = sum_control = sum_prior = 0.0
    sum_messages = 0.0
    sum_blind_stages: list[float] = [0.0 for _ in stages.delta_steps]
    raw_sers: list[float] = []
    frame_rows: list[dict[str, Any]] = []

    for frame_idx in range(n_frames):
        a_sym = np.asarray(batch.alice_symbols[frame_idx], dtype=np.int64)
        b_sym = np.asarray(batch.bob_symbols[frame_idx], dtype=np.int64)
        raw_ser = frame_symbol_error_rate(a_sym, b_sym)
        raw_sers.append(float(raw_ser))
        a_planes = [np.asarray(p, dtype=np.uint8).reshape(-1)
                    for p in split_symbol_bitplanes(a_sym, int(batch.dimension), "gray")]
        b_planes = [np.asarray(p, dtype=np.uint8).reshape(-1)
                    for p in split_symbol_bitplanes(b_sym, int(batch.dimension), "gray")]
        # Seed 2026092001 retained, consistent with M2-LAYEREDBIN F4 (not a new value).
        if construct_fn is not None:
            constructions = [dict(construct_fn(len(a_planes[p]), int(allocation.plane_rows[p]),
                                               2026092001, frame_idx, p))
                             for p in range(plane_bits)]
        else:
            constructions = [dict(_construct_plane_production(len(a_planes[p]),
                                                              int(allocation.plane_rows[p]),
                                                              2026092001 + frame_idx))
                             for p in range(plane_bits)]
        if decode_fn is not None:
            outcome = dict(decode_fn(a_planes, b_planes, constructions, stages, frame_idx,
                                     int(params.max_iter), int(params.streak)))
        else:
            outcome = dict(_spa_decode_production(a_planes, b_planes, constructions, stages))
        for key in _OUTCOME_KEYS:
            if key not in outcome:
                raise ValueError(f"layered-binary outcome missing {key!r} (fail closed, no defaults)")
        exact = bool(outcome["exact_match"])
        accepted = bool(outcome["accepted"])
        # Success needs BOTH per-plane syndrome consistency AND Toeplitz t=64 (design §5).
        gate_ok = bool(outcome["syndrome_consistent"]) and bool(outcome["toeplitz_verified"])
        success = bool(exact and gate_ok and accepted)
        und = bool(accepted and not success)
        if success:
            successes += 1
        elif not accepted:
            failed_decode += 1
        else:
            failed_verify += 1
        accepted_wrong += int(und)
        stage_bits = [float(x) for x in outcome["blind_stage_bits"]]
        if len(stage_bits) != len(sum_blind_stages):
            raise ValueError("blind_stage_bits length != frozen stage count (no mid-run extension)")
        leak = float(outcome["leak_ec_bits"])
        rescue = float(outcome["rescue_bits"])
        control = float(outcome["control_bits"])
        prior = float(outcome["prior_entropy_bits"])
        messages = float(outcome["messages_actual"])
        sum_leak += leak + sum(stage_bits)
        for i, s in enumerate(stage_bits):
            sum_blind_stages[i] += s
        sum_rescue += rescue
        sum_control += control
        sum_prior += prior
        sum_messages += messages
        frame_rows.append({
            "dataset_id": batch.dataset_id, "method": "layered_binary", "frame_idx": frame_idx,
            "decode_success": success, "verify_success": gate_ok and exact,
            "accepted": accepted, "accepted_wrong": und,
            "syndrome_consistent": bool(outcome["syndrome_consistent"]),
            "toeplitz_verified": bool(outcome["toeplitz_verified"]),
            "raw_frame_ser": float(raw_ser),
            "leak_EC_bits": leak + sum(stage_bits), "blind_stage_bits": stage_bits,
            "tag_bits": TAG_BITS_FROZEN, "rescue_bits": rescue, "control_bits": control,
            "lambda_total": lambda_total(leak + sum(stage_bits), TAG_BITS_FROZEN, rescue, control),
            "messages_actual": messages,
            "messages_ldpc_ref": LDPC_MSG_PER_FRAME_REF,
            "prior_entropy_bits_reportonly": prior,
            "prior_1p50_reportonly": PRIOR_SCALE_REPORTONLY * prior,
        })

    attempted = n_frames
    fails = attempted - successes
    fer = (fails / attempted) if attempted else float("nan")
    f_super = f_super_packet_literal(int(allocation.m_basis), float(allocation.h_basis))
    f_notag = f_notag_packet_literal(int(allocation.m_basis), float(allocation.h_basis))
    f_eff = f_eff_from(f_super, fer if math.isfinite(fer) else 0.0)
    lam = lambda_total(sum_leak, TAG_BITS_FROZEN * attempted, sum_rescue, sum_control)
    n_bits = int(batch.alice_symbols.size) * plane_bits
    raw_ber_all = bit_error_rate(flatten_bits(batch.alice_symbols, int(batch.dimension)),
                                 flatten_bits(batch.bob_symbols, int(batch.dimension)))
    beta = compute_beta_eff_empirical(sum_leak + TAG_BITS_FROZEN * attempted, n_bits, raw_ber_all)
    raw_ser = float(np.mean(raw_sers)) if raw_sers else float("nan")
    if successes == attempted and attempted > 0:
        method_status = "ok"
    elif successes > 0:
        method_status = "ok"
    elif failed_verify > 0:
        method_status = "no_verified_success"
    elif attempted > 0:
        method_status = "decode_failed"
    else:
        method_status = "unavailable"
    runtime = time.perf_counter() - start
    notes = (
        f"layered_binary per-plane entropy allocation Σm_j={allocation.m_basis} "
        f"H[{allocation.source_key}]={allocation.h_basis} (assumed input, no refit); "
        f"blind m_init={stages.m_init}+{len(stages.delta_steps)} small steps; "
        f"SPA max_iter/streak {params.max_iter}/{params.streak} frozen; "
        f"success = syndrome-consistent + Toeplitz-t64 + exact; undetected isolated; "
        f"V19 f=4.169 strawman replaced, never cited; {CLAIM_CEILING}"
    )
    return IRRunResult(
        dataset_id=batch.dataset_id, method="layered_binary", method_variant=cfg.method_variant,
        frame_len_symbols=frame_symbols, frame_len_bits=frame_symbols * plane_bits,
        n_frames_total=n_frames, n_frames_attempted=attempted,
        n_frames_success=successes, n_frames_failed_decode=failed_decode,
        n_frames_failed_verify=failed_verify,
        raw_ser=raw_ser, raw_ber=raw_ber_all, post_ir_ser=raw_ser, post_ir_ber=raw_ber_all,  # raw-only placeholder; granted runs must recompute or declare
        leak_EC_actual_bits=float(sum_leak),
        leak_EC_per_frame=(float(sum_leak) / n_frames) if n_frames else float("nan"),
        leak_EC_per_input_bit=(float(sum_leak) / n_bits) if n_bits else float("nan"),
        beta_eff_empirical=beta, runtime_s=runtime,
        throughput_input_bits_per_s=(n_bits / runtime) if runtime > 0 else 0.0,
        throughput_output_bits_per_s=0.0,  # placeholder; granted runs must recompute or declare
        metadata={
            "method_status": method_status,
            "backend_status": "layered_binary_fake" if decode_fn else "layered_binary",
            "notes": notes,
            "frame_results": frame_rows,
            "attempted": attempted, "exact_match": successes, "accepted": successes + failed_verify,
            "accepted_wrong": accepted_wrong, "undetected": accepted_wrong,
            "fer": fer,
            "f_super": f_super, "f_notag": f_notag, "f_eff": f_eff,
            "f_basis": {"m": int(allocation.m_basis), "H": float(allocation.h_basis),
                        "source": allocation.source_key, "H_column": "assumed"},
            "lambda_total": lam,
            "lambda_parts": {"leak_EC": float(sum_leak), "tag": float(TAG_BITS_FROZEN * attempted),
                             "rescue": float(sum_rescue), "control": float(sum_control),
                             "blind_stages": [float(x) for x in sum_blind_stages]},  # blind_stages subset of leak_EC, breakdown only, never added (anti-double-count)
            "prior_1p50_reportonly": PRIOR_SCALE_REPORTONLY * float(sum_prior),
            "prior_column": "report-only (never into lambda_total/f numerators)",
            "messages_per_frame_actual": (float(sum_messages) / n_frames) if n_frames else float("nan"),
            "messages_ldpc_ref": LDPC_MSG_PER_FRAME_REF,
            "messages_cascade_ref_noncomparable": CASCADE_MSG_PER_FRAME_REF,
            "n_req_reportonly": n_required_reportonly(f_super),
            "key_eligible_contrast": (200, 276, 364),
            "d_dim": int(batch.dimension), "q_alphabet": "2x10 layers",
            "n_ir_bits": int(frame_symbols * plane_bits),
            "allocation_rows": {int(k): int(v) for k, v in dict(allocation.plane_rows).items()},
            "blind_schedule": {"m_init": int(stages.m_init),
                               "delta_steps": [int(x) for x in stages.delta_steps]},
            "spa_pins": {"max_iter": int(params.max_iter), "streak": int(params.streak)},
            "claim_ceiling": CLAIM_CEILING,
            "claim_column": "measured(fake-synthetic-tiny); H assumed; projected empty",
        },
    )


__all__ = [
    "FROZEN_H", "F_EFF_SLOPE_FROZEN", "TAG_BITS_FROZEN", "PRIOR_SCALE_REPORTONLY",
    "SPA_MAX_ITER_FROZEN", "SPA_STREAK_FROZEN", "N_FAMILY_FROZEN",
    "LDPC_MSG_PER_FRAME_REF", "CASCADE_MSG_PER_FRAME_REF", "CLAIM_CEILING",
    "PlaneAllocation", "BlindStageTable", "LayeredParams",
    "f_super_packet_literal", "f_notag_packet_literal", "f_eff_from",
    "lambda_total", "n_required_reportonly", "run_layered_binary",
]
