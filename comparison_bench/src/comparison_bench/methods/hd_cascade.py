"""HD-Cascade honest baseline (M2; implementation-only, fake-tested).

Mueller-2024 three changes (naming per ``docs/RESEARCH_DIRECTION_REPORT_20260924.md``
M2 + ``openspec/changes/m2-honest-baselines/design.md`` S2), incremental ONLY on top of
``methods/cascade_lite.py`` + ``methods/cascade/single_kernel.py`` (read-only reuse;
those modules are never modified here):

  T1/改① binary mapping 10bit -> Gray bit-plane grouping (Alice reference, Bob local);
  T2/改② per-plane block-size schedule (plane x pass -> initial/growth/cap);
  T3/改③ cascade propagation (reuse cascade_lite; cross-plane lookback new bounded sweep of this arm,
         parallel-first);
  T4      per-frame message accounting (Mueller 446 aperture, separate column).

待澄清表 rule (design §2): the block-length table carries NO guessed numbers. Every
plane x pass entry must be explicitly supplied via :class:`HdCascadeBlockTable` before
any grant; a missing entry fails closed (``ValueError`` naming the plane), never a
silent default.

Accounting (M2-HDCASCADE-SYNTH PACKET F5; A-CMPE-1..7):
  four counts attempted / exact_match(=success) / accepted / accepted_wrong(=undetected,
  isolated, never success/FER-merged); f_super/f_notag/f_eff on the THIS-arm m basis
  with frozen synthetic-F03 H (1M 0.801038 / 1.5M 0.825566 / 2M 0.832563; own source
  only, cross-source H refused); verification-aware
  λ_total = leak_EC + 64(tag) + rescue single column + control rounds; 1.50x prior
  opportunity cost is report-only and never enters λ_total or any f numerator;
  wall + per-frame messages (Cascade 446 aperture; LDPC 3.14 carried as a
  non-comparable annotation, never mixed); N_req report-only; d/q/n_IR separated;
  no SKR; V19 f=4.169 strawman never cited as comparison.

Tests MUST inject an explicit fake ``decode_fn``; the production per-plane cascade
path is never entered by fake tests (guarded in the fake test files by monkeypatch).
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from . import cascade_lite as _cascade_lite
from ..metrics.leakage import compute_beta_eff_empirical
from ..types import FrameBatch, IRRunConfig, IRRunResult
from ..utils.bitops import bit_error_rate, bits_per_symbol, flatten_bits, frame_symbol_error_rate, symbols_to_bits

# ---------------------------------------------------------------- frozen literals
# (carried, not invented: M2-HDCASCADE-SYNTH PACKET F5 + x1_arm_runner F_EFF_SLOPE).

#: Frozen synthetic-F03 H basis per source (6-decimal display; precise lineage in
#: formal_ir.nonbinary_v29.SOURCE_H_TOTAL; TRAIN-side assumed input, never refit).
FROZEN_H: dict[str, float] = {"1M": 0.801038, "1p5M": 0.825566, "2M": 0.832563}

#: Frozen f_eff slope (packet F5; x1_arm_runner.F_EFF_SLOPE).
F_EFF_SLOPE_FROZEN = 4.785675

#: Frozen verification tag width (Toeplitz t=64).
TAG_BITS_FROZEN = 64

#: Frozen prior opportunity-cost scale: report-only, never into λ_total/f numerators.
PRIOR_SCALE_REPORTONLY = 1.50

#: Mueller per-frame message aperture for Cascade (T4; independent column).
CASCADE_MSG_PER_FRAME_REF = 446

#: LDPC-level aperture carried as a non-comparable annotation only (never mixed).
LDPC_MSG_PER_FRAME_REF = 3.14

#: Claim-ceiling fixed sentence (M2 packets §5; carried verbatim on synthetic numbers).
CLAIM_CEILING = ("合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；"
                 "D1 条件化分支下不得用本批合成数论证真实优劣。")


# ------------------------------------------------------------- frozen param slots

@dataclass(frozen=True)
class HdCascadeBlockTable:
    """Per-plane x pass block schedule (T2; structure frozen, values granted).

    ``schedules`` maps plane_idx (0..plane_bits-1) -> per-pass block sizes
    (pass 0..k-1). ``max_cross_plane_sweeps`` bounds the T3 cross-plane lookback.
    Anything missing fails closed: no guessed numbers (待澄清表 rule).
    """

    schedules: Mapping[int, Sequence[int]]
    max_cross_plane_sweeps: int = 1

    def planes(self, plane_bits: int) -> list[int]:
        missing = [p for p in range(int(plane_bits)) if p not in dict(self.schedules)]
        if missing:
            raise ValueError(f"hd-cascade block table missing planes {missing} "
                             f"(待澄清表 unfilled; fill before grant, never guess)")
        if not isinstance(self.max_cross_plane_sweeps, int) or self.max_cross_plane_sweeps < 0:
            raise ValueError("max_cross_plane_sweeps must be a non-negative int")
        out: list[int] = []
        for p in range(int(plane_bits)):
            sizes = [int(x) for x in self.schedules[p]]
            if not sizes or any(s <= 0 for s in sizes):
                raise ValueError(f"hd-cascade block table plane {p}: need non-empty positive sizes")
            out.append(p)
        return out

    def schedule_for(self, plane_idx: int) -> list[int]:
        try:
            sizes = [int(x) for x in self.schedules[int(plane_idx)]]
        except KeyError:
            raise ValueError(f"hd-cascade block table missing plane {plane_idx} (待澄清表 unfilled)")
        if not sizes or any(s <= 0 for s in sizes):
            raise ValueError(f"hd-cascade block table plane {plane_idx}: need positive sizes")
        return sizes


@dataclass(frozen=True)
class HdCascadeParams:
    """Arm-frozen scalar slots (this-arm m basis; grant-time filled)."""

    source_key: str
    h_basis: float
    m_basis: int
    plane_bits: int = 10
    tag_bits: int = TAG_BITS_FROZEN
    seed: int = 20260415  # PLACEHOLDER seed: grant-time override; never cite as frozen value
    max_passes: int = 4
    permutation_mode: str = "seeded_random"

    def validated(self, dimension: int) -> "HdCascadeParams":
        if self.source_key not in FROZEN_H:
            raise ValueError(f"unknown source_key {self.source_key!r} (frozen: 1M|1p5M|2M)")
        if abs(float(self.h_basis) - FROZEN_H[self.source_key]) > 1e-6:
            raise ValueError(f"h_basis {self.h_basis!r} != frozen H for {self.source_key} "
                             f"({FROZEN_H[self.source_key]}; own-source H only, never cross-source, no refit)")
        if not isinstance(self.m_basis, int) or isinstance(self.m_basis, bool) or self.m_basis < 1:
            raise ValueError("m_basis must be a positive int (this-arm m)")
        if int(self.tag_bits) != TAG_BITS_FROZEN:
            raise ValueError(f"tag_bits frozen at {TAG_BITS_FROZEN}")
        if 2 ** int(self.plane_bits) != int(dimension):
            raise ValueError(f"plane_bits {self.plane_bits} inconsistent with dimension {dimension}")
        if int(self.max_passes) < 1:
            raise ValueError("max_passes must be positive")
        return self


# ------------------------------------------------------- T1: Gray plane grouping

def symbols_to_gray_planes(symbols: np.ndarray, dimension: int) -> list[np.ndarray]:
    """改①: 10-bit symbols -> Gray code -> per-plane bit vectors (read-only reuse).

    Returns ``plane_bits`` vectors of length n_symbols (plane 0 = MSB).
    """
    bps = bits_per_symbol(int(dimension))
    bits = symbols_to_bits(np.asarray(symbols, dtype=np.int64), int(dimension), "gray")
    if bits.ndim == 1:
        bits = bits.reshape(1, -1)
    return [np.asarray(bits[:, i], dtype=np.uint8).reshape(-1) for i in range(bps)]


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


# ------------------------------------------------- T3: production cascade (granted
# runs only; fake tests always inject decode_fn and monkeypatch this to raise).

def _run_planes_production(alice_planes: list[np.ndarray], bob_planes: list[np.ndarray],
                           table: HdCascadeBlockTable, seed: int, max_passes: int,
                           permutation_mode: str) -> dict[str, Any]:
    """Per-plane cascade_lite kernel + bounded cross-plane lookback sweep (T3)."""
    n_planes = len(alice_planes)
    decoded = [np.asarray(b, dtype=np.uint8).copy() for b in bob_planes]
    leak_parts: list[int] = []
    messages = 0
    for p in range(n_planes):
        sched = table.schedule_for(p)
        out, stats = _cascade_lite._run_frame_cascade(
            np.asarray(alice_planes[p], dtype=np.uint8), decoded[p],
            sched, int(seed) + 104729 * p, int(max_passes), str(permutation_mode))
        decoded[p] = out
        leak_parts.append(int(stats["parity_disclosures_bits"] + stats["bisection_disclosures_bits"]))
        # PLACEHOLDER pending PACKET F3 pin; message-aperture claim forbidden.
        messages += int(stats["total_blocks_checked"]) * 2 + int(stats["iterations_used"])
    for _ in range(int(table.max_cross_plane_sweeps)):
        still = [p for p in range(n_planes)
                 if _cascade_lite._mismatched_block(
                     np.asarray(alice_planes[p], dtype=np.uint8), decoded[p],
                     np.arange(decoded[p].size, dtype=np.int64))]
        if not still:
            break
        for p in still:  # cross-plane lookback: one bounded re-pass per open plane
            sched = table.schedule_for(p)
            out, stats = _cascade_lite._run_frame_cascade(
                np.asarray(alice_planes[p], dtype=np.uint8), decoded[p],
                sched[:1], int(seed) + 99991 * p, 1, str(permutation_mode))
            decoded[p] = out
            leak_parts.append(int(stats["parity_disclosures_bits"] + stats["bisection_disclosures_bits"]))
            # PLACEHOLDER pending PACKET F3 pin; message-aperture claim forbidden.
            messages += int(stats["total_blocks_checked"]) * 2 + int(stats["iterations_used"])
    return {"decoded_planes": decoded, "leak_ec_bits": int(sum(leak_parts)),
            "leak_ec_parts": leak_parts, "messages_actual": int(messages),
            "rescue_bits": 0.0, "control_bits": 0, "prior_entropy_bits": 0.0,
            "exact_match": all(bool(np.array_equal(np.asarray(alice_planes[p], dtype=np.uint8), decoded[p]))
                               for p in range(n_planes)),
            "accepted": True, "toeplitz_verified": False}


# ---------------------------------------------------------------- main entrypoint

#: Required fake/production outcome keys (missing key fails closed; never defaulted).
_OUTCOME_KEYS = ("exact_match", "accepted", "toeplitz_verified", "leak_ec_bits",
                 "rescue_bits", "control_bits", "messages_actual", "prior_entropy_bits")


def run_hd_cascade(batch: FrameBatch, cfg: IRRunConfig, *, params: HdCascadeParams,
                   block_table: HdCascadeBlockTable,
                   decode_fn: Callable[..., Mapping[str, Any]] | None = None) -> IRRunResult:
    """Run the HD-Cascade arm over a FrameBatch (fake tests MUST pass ``decode_fn``)."""
    start = time.perf_counter()
    params.validated(int(batch.dimension))
    plane_bits = int(params.plane_bits)
    block_table.planes(plane_bits)
    bps = bits_per_symbol(int(batch.dimension))
    n_frames = int(batch.alice_symbols.shape[0])
    frame_symbols = int(batch.frame_len_symbols)

    successes = failed_decode = failed_verify = 0
    accepted_wrong = 0
    sum_leak = sum_rescue = sum_control = sum_prior = 0.0
    sum_messages = 0.0
    raw_sers: list[float] = []
    frame_rows: list[dict[str, Any]] = []

    for frame_idx in range(n_frames):
        a_sym = np.asarray(batch.alice_symbols[frame_idx], dtype=np.int64)
        b_sym = np.asarray(batch.bob_symbols[frame_idx], dtype=np.int64)
        raw_ser = frame_symbol_error_rate(a_sym, b_sym)
        raw_sers.append(float(raw_ser))
        a_planes = symbols_to_gray_planes(a_sym, int(batch.dimension))
        b_planes = symbols_to_gray_planes(b_sym, int(batch.dimension))
        schedules = [block_table.schedule_for(p) for p in range(plane_bits)]
        if decode_fn is not None:
            outcome = dict(decode_fn(a_planes, b_planes, schedules, frame_idx, int(params.seed)))
        else:
            prod = _run_planes_production(a_planes, b_planes, block_table,
                                          int(params.seed) + frame_idx * 104729,
                                          int(params.max_passes), str(params.permutation_mode))
            outcome = dict(prod)
        for key in _OUTCOME_KEYS:
            if key not in outcome:
                raise ValueError(f"hd-cascade outcome missing {key!r} (fail closed, no defaults)")
        exact = bool(outcome["exact_match"])
        accepted = bool(outcome["accepted"])
        verified = bool(outcome["toeplitz_verified"])
        # Unified gate (layered style): exact and gate_ok and accepted.
        success = bool(exact and verified and accepted)  # undetected can never satisfy this
        und = bool(accepted and not success)
        if success:
            successes += 1
        elif not accepted:
            failed_decode += 1
        else:
            failed_verify += 1
        accepted_wrong += int(und)
        leak = float(outcome["leak_ec_bits"])
        rescue = float(outcome["rescue_bits"])
        control = float(outcome["control_bits"])
        prior = float(outcome["prior_entropy_bits"])
        messages = float(outcome["messages_actual"])
        sum_leak += leak
        sum_rescue += rescue
        sum_control += control
        sum_prior += prior
        sum_messages += messages
        frame_rows.append({
            "dataset_id": batch.dataset_id, "method": "hd_cascade", "frame_idx": frame_idx,
            "decode_success": success, "verify_success": verified,
            "accepted": accepted, "accepted_wrong": und,
            "raw_frame_ser": float(raw_ser),
            "leak_EC_bits": leak, "tag_bits": TAG_BITS_FROZEN,
            "rescue_bits": rescue, "control_bits": control,
            "lambda_total": lambda_total(leak, TAG_BITS_FROZEN, rescue, control),
            "messages_actual": messages,
            "messages_cascade_ref": CASCADE_MSG_PER_FRAME_REF,
            "prior_entropy_bits_reportonly": prior,
            "prior_1p50_reportonly": PRIOR_SCALE_REPORTONLY * prior,
        })

    attempted = n_frames
    fails = attempted - successes
    fer = (fails / attempted) if attempted else float("nan")
    f_super = f_super_packet_literal(int(params.m_basis), float(params.h_basis))
    f_notag = f_notag_packet_literal(int(params.m_basis), float(params.h_basis))
    f_eff = f_eff_from(f_super, fer if math.isfinite(fer) else 0.0)
    lam = lambda_total(sum_leak, TAG_BITS_FROZEN * attempted, sum_rescue, sum_control)
    n_bits = int(batch.alice_symbols.size) * bps
    raw_ber_all = bit_error_rate(flatten_bits(batch.alice_symbols, int(batch.dimension)),
                                 flatten_bits(batch.bob_symbols, int(batch.dimension)))
    beta = compute_beta_eff_empirical(sum_leak + TAG_BITS_FROZEN * attempted, n_bits, raw_ber_all)
    raw_ser = float(np.mean(raw_sers)) if raw_sers else float("nan")
    # Full and partial success share "ok" (undetected isolated separately, never merged).
    if successes > 0:
        method_status = "ok"
    elif failed_verify > 0:
        method_status = "no_verified_success"
    elif attempted > 0:
        method_status = "decode_failed"
    else:
        method_status = "unavailable"
    runtime = time.perf_counter() - start
    notes = (
        f"hd_cascade Mueller三改 (mapping=gray-planes-{plane_bits}, per-plane-schedule, "
        f"cross-plane-lookback parallel-first); this-arm m_basis={params.m_basis} "
        f"H[{params.source_key}]={params.h_basis} (assumed, own-source, no refit); "
        f"f_super/f_notag/f_eff this-arm basis; undetected isolated (never success); "
        f"V19 f=4.169 strawman replaced, never cited; {CLAIM_CEILING}"
    )
    return IRRunResult(
        dataset_id=batch.dataset_id, method="hd_cascade", method_variant=cfg.method_variant,
        frame_len_symbols=frame_symbols, frame_len_bits=frame_symbols * bps,
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
            "method_status": method_status, "backend_status": "hd_cascade_fake" if decode_fn else "hd_cascade",
            "notes": notes,
            "frame_results": frame_rows,
            "attempted": attempted, "exact_match": successes, "accepted": successes + failed_verify,
            "accepted_wrong": accepted_wrong, "undetected": accepted_wrong,
            "fer": fer,
            "f_super": f_super, "f_notag": f_notag, "f_eff": f_eff,
            "f_basis": {"m": int(params.m_basis), "H": float(params.h_basis),
                        "source": params.source_key, "H_column": "assumed"},
            "lambda_total": lam,
            "lambda_parts": {"leak_EC": float(sum_leak), "tag": float(TAG_BITS_FROZEN * attempted),
                             "rescue": float(sum_rescue), "control": float(sum_control)},
            "prior_1p50_reportonly": PRIOR_SCALE_REPORTONLY * float(sum_prior),
            "prior_column": "report-only (never into lambda_total/f numerators)",
            # PLACEHOLDER pending PACKET F3 pin; provisional column, no aperture claim.
            "messages_per_frame_actual": (float(sum_messages) / n_frames) if n_frames else float("nan"),
            "messages_per_frame_actual_status": "provisional (PLACEHOLDER pending PACKET F3 pin)",
            "messages_cascade_ref": CASCADE_MSG_PER_FRAME_REF,
            "messages_ldpc_ref_noncomparable": LDPC_MSG_PER_FRAME_REF,
            "n_req_reportonly": n_required_reportonly(f_super),
            "key_eligible_contrast": (200, 276, 364),
            "d_dim": int(batch.dimension), "q_alphabet": int(batch.dimension),
            "n_ir_bits": int(frame_symbols * bps),
            "claim_ceiling": CLAIM_CEILING,
            "claim_column": "measured(fake-synthetic-tiny); H assumed; projected empty",
        },
    )


__all__ = [
    "FROZEN_H", "F_EFF_SLOPE_FROZEN", "TAG_BITS_FROZEN", "PRIOR_SCALE_REPORTONLY",
    "CASCADE_MSG_PER_FRAME_REF", "LDPC_MSG_PER_FRAME_REF", "CLAIM_CEILING",
    "HdCascadeBlockTable", "HdCascadeParams", "symbols_to_gray_planes",
    "f_super_packet_literal", "f_notag_packet_literal", "f_eff_from",
    "lambda_total", "n_required_reportonly", "run_hd_cascade",
]
