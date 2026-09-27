"""P4 n=2048 construction-feasibility thin runner (EXPLORE code — NOT execution).

Frozen contract: ``docs/research_cycles/V80-NBLDPC-JAN21/P4_FEAS_PACKET.md``
(FROZEN, NOT GRANTED; the §10(d) authorization block is BLANK = unauthorized)
+ ``P4_FEAS_PROMPT.md``. This module IS the packet §10(b) execution surface;
implementing it carries NO track gate (AGENTS §1.2 implementation-only
matrix). The track gate hangs on the FIRST SYNTHETIC EXECUTION. This module
authorizing any execution = 0.

Frozen F1–F6 scope implemented here (packet §2):

- **F1 two arms, frozen ORDER**: ``P4F-R1`` construct lineage 2026092001,
  then ``P4F-R2`` 2026092011 (``ARM_ORDER``); reported SEPARATELY —
  cross-instance pooling of pins/counts FORBIDDEN. Lineage integers are the
  n=2048 construction RNG seeds (no new-seed invention path exists here:
  any seed other than the two lineage integers refuses ⇒ STOP).
- **F2 ONE matrix per arm**: PEG irregular, n=2048 GF(32) symbols,
  m=416, λ={2:1} edge perspective, ρ=``make_rho(1-416/2048)=
  make_rho(0.796875)`` (read-only ``nonbinary_v26_mcde.make_rho`` reuse),
  trials=20, ``family="peg-irregular"`` stamped +
  ``refuse_three_shift_cyclic`` guard (v80_s2_peg frozen semantics).
  NO second matrix family, NO non-PEG family. Nested base capability:
  leading ``rows[0,400)`` MUST be rank-400 REQUIRED (F2/F6). Matrix
  degree basis: dv=2 ⇒ 4096 edges / 416 ⇒ mean check degree ≈9.85
  (the m≈208 "19.7" figure is SUPERSEDED — never a design number here).
- **F3 fresh object**: same lineage integers ≠ same matrix as n=1024
  (different dimensions); no paired blocks, no block seeds, no
  ``o1_blk:`` stream, zero blocks. F4 channel: NONE — construction is
  channel-ignorant; there is NO channel-bundle read path in this file
  (no such import, path, or quoted literal anywhere here).
- **F5 zero decode**: no decoder entrypoint is imported or reachable;
  ``decode_calls == 0`` is asserted and recorded on every output; the
  module defines no callable whose name starts with ``decode``.
- **F6 pins (gated)**: ``fc=0`` AND full ``rank==416`` AND
  twice-identical triples AND base ``rank(rows[0,400))==400`` REQUIRED,
  any miss ⇒ STOP-BLOCKED (rc=2); girth is RECORDED-not-gated per
  instance; sockets/parity are recorded (not gates).
- **F7/F8/F9/F10**: accounting is an ARITHMETIC IDENTITY ROW only
  (H_anchor=0.83256272, content_2048=1705.088, leak=5·416+64=2144,
  f_super=1.25741, headroom=2216.61−2144=72.61 b, N_req=338 report-only)
  — NEVER quoted as f_eff (zero decode ⇒ no FER ⇒ no f_eff); one
  construction + one twice-identical reconstruction per arm (2
  ``peg_construct`` calls/arm); ``undetected`` is N/A (no syndrome, no
  such column); budgets wall ≤1800 s/arm, single construct ≤600 s
  (overrun = terminal construction FAIL, no continuation), RSS < 2 GiB,
  1 CPU; wall-partial ⇒ ``INCOMPLETE-wall`` retained, never continued.

Outputs ONLY under fresh additive per-arm roots
``workspace/P4_FEAS/<arm>_<uuid8>/`` (uuid8 frozen Pre-EXECUTE, passed
explicitly — no generation path here) + one APPEND-ONLY exploration log.
Both write destinations are guarded by exact path-segment checks: the
root must equal ``workspace/P4_FEAS`` exactly, and BOTH the root and the
log path (``--log``) refuse any segment in ``FORBIDDEN_ROOT_PARTS``
(``results``, ``outputs_comparison``) rc=2 BEFORE any write. This is a
guard on these two destinations only (segment-exact match), NOT a
general no-write guarantee for every path in the repository; existing
evidence roots are simply never opened.

CLI: production construction runs ONLY behind BOTH flags ``--execute-real``
AND ``--execution-authorized`` plus every frozen literal echo (n, m,
trials, λ, ρ rate, seed line) and both uuid8 roots; a bare or partial
invocation refuses rc=2 BEFORE any root, log, or write. ``execute()``
itself requires explicit ``construct_fn``/``rank_fn`` injection (no default
production wiring in the core — AGENTS §10.1 clause 8).

Printed rows use 6 decimal places with the legend
``success := ¬failed; decoded := returned`` (P1 Stage-1 batch-end review
F3 finding, carried forward).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from typing import Any, Callable

from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v10_peg as peg,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v26_mcde as _mcde,
)
from comparison_bench.src.comparison_bench.formal_ir import v80_s2_peg as s2
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (
    GF2mField,
)

__all__ = [
    "P4_N", "P4_M", "P4_M_BASE", "P4_LAMBDA", "P4_RHO_RATE",
    "P4_MAX_TRIALS", "ARMS", "ARM_ORDER",
    "P4_WALL_CAP_S", "P4_CONSTRUCT_CAP_S", "P4_RSS_CAP_GIB", "P4_CPUS",
    "P4_ROOT", "P4_ROOT_PREFIX", "FORBIDDEN_ROOT_PARTS", "DEFAULT_LOG_PATH",
    "H_ANCHOR", "CONTENT_2048", "LEAK_BITS", "LEAK_CAP_BITS",
    "F_SUPER_416", "F_SUPER_416_LITERAL", "HEADROOM_CTX", "F_EFF_SLOPE",
    "F_SUPER_MAX", "N_REQ_CTX", "N_REQ_CTX_LITERAL",
    "RESULT_FIELDS", "CLAIM_CEILING", "IDENTITY_ROW_MARK", "LEGEND",
    "DECODE_CALLS",
    "Refusal", "refuse", "parse_arm", "identity_row", "claim_ceiling_row",
    "construct_and_pin", "production_construct", "production_rank_fn",
    "_check_base_root", "_check_uuid8", "_check_log_path", "arm_root",
    "default_writer",
    "append_log", "build_record", "result_markdown",
    "execute", "run_execution", "main",
]

#: Frozen F1: exactly two arms, frozen R1 -> R2 order, separate report.
P4_N = 2048
P4_M = 416
#: Frozen F2/F6 nested base capability: leading rows[0,400) rank-400.
P4_M_BASE = 400
#: Frozen F2 variable-side degree profile (edge perspective): λ={2:1}.
P4_LAMBDA: dict[int, float] = {2: 1.0}
#: Frozen F2 concentrated check distribution rate: make_rho(0.796875).
P4_RHO_RATE = 0.796875  # = 1 - 416/2048 (binary-exact literal)
#: Frozen F2 constructor trials (O1-family same value).
P4_MAX_TRIALS = 20
#: Frozen F1 lineage integers (n=2048 construction RNG seeds) in order.
ARMS: dict[str, int] = {"P4F-R1": 2026092001, "P4F-R2": 2026092011}
ARM_ORDER = tuple(ARMS)  # frozen batch order: P4F-R1 -> P4F-R2
#: Frozen §5 budgets: wall per arm, single peg_construct call, RSS, CPU.
#: §5 budget rank count — ACTUAL per arm (successful construction): 3 rank
#: evaluations = 2 full-rank (416) RREFs inside the two peg_construct calls
#: + 1 base-rank rows[0,400) via rank_fn in construct_and_pin. The packet §5
#: "两次 rank" note counts only the two constructor-internal full-rank
#: RREFs; the former constructor-side base-rank pre-computation was dead
#: (construct_and_pin recomputes gate["rank_base_400"]) and is deleted.
P4_WALL_CAP_S = 1800
P4_CONSTRUCT_CAP_S = 600
P4_RSS_CAP_GIB = 2
P4_CPUS = 1
#: Fresh additive machine-root family (packet §5) + forbidden trees.
P4_ROOT = "workspace/P4_FEAS"
P4_ROOT_PREFIX = "workspace/P4_FEAS/"
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")
#: Pre-EXECUTE-frozen uuid8 form (packet §5 placeholder: [TO BE FROZEN]).
UUID8_RE = re.compile(r"^[0-9a-f]{8}$")
#: Append-only batch log (packet §6.2; created at execution, never here).
DEFAULT_LOG_PATH = (
    "docs/research_cycles/V80-NBLDPC-JAN21/P4_FEAS_EXPLORATION_LOG.md"
)

# --- Frozen §2 F7 / §2.1 accounting: an IDENTITY ROW, never f_eff ----------
#: Frozen whole-frame-with-tag content anchor (bits/symbol).
H_ANCHOR = 0.83256272
#: Frozen content literal: 2048 x H_anchor (§2.1 linear extension).
CONTENT_2048 = 1705.088
#: Frozen leak at m=416: 5m+64; tag 64 bits/superframe, NOT doubled.
LEAK_BITS = 5 * P4_M + 64  # = 2144
#: Frozen cap literal: 1.3 x 1705.088 = 2216.61 b.
LEAK_CAP_BITS = 2216.61
#: Frozen f_super line (frozen restatement "1.25741"; computed ≈1.257413).
F_SUPER_416 = LEAK_BITS / CONTENT_2048
F_SUPER_416_LITERAL = "1.25741"
#: Frozen headroom context literal: 2216.61 - 2144 = 72.61 b.
HEADROOM_CTX = 72.61
#: Frozen f_eff slope (m/n constant ⇒ scale-invariant; ROADMAP §8).
F_EFF_SLOPE = 4.785675
#: Frozen efficiency bar (identity check (b) arithmetic, not a science gate).
F_SUPER_MAX = 1.3
#: Report-only N rule on this arm's identity row: ceil(3·4.785675/(1.3-f)).
N_REQ_CTX = math.ceil(3.0 * F_EFF_SLOPE / (F_SUPER_MAX - F_SUPER_416))
N_REQ_CTX_LITERAL = 338

#: Frozen §3 per-arm record fields (construction.json + pins report).
RESULT_FIELDS = [
    "arm", "construct_seed", "n", "m", "lambda_edge", "rho_edge", "trials",
    "family", "four_cycles", "rank_full", "rank_base_400",
    "twice_identical", "girth", "sockets", "parity", "wall_s", "rss_peak",
    "H_anchor", "content_2048", "f_super_416", "headroom_ctx", "N_req_ctx",
    "claim_ceiling",
]
#: Frozen §9 claim ceiling (carried on every record).
CLAIM_CEILING = (
    "n=2048 PEG construction feasibility ONLY (per-instance pins + nested "
    "base capability + frozen arithmetic identity row) as route-1 entry "
    "evidence; NOT mechanism performance (no FER/conversion/leakage "
    "measured), NOT SKR, NOT qualification, NOT route adjudication (P4 "
    "elevation to S3 is NOT decided here), NOT operating-point selection, "
    "NOT real-data FER, NOT a certifiable/literature-comparable f_eff<=1.3 "
    "sentence, NOT publication material; key-eligible 200/276/364 cited-"
    "not-consumed and N_req 338 report-only; any later citation MUST list "
    "the two instances separately (single-instance-as-conclusion FORBIDDEN; "
    "cross-instance pooling FORBIDDEN)"
)
#: Identity-row marker (§3: identity row, NEVER f_eff).
IDENTITY_ROW_MARK = (
    "identity row (frozen §2 F7 arithmetic restated; NEVER f_eff — zero "
    "decode ⇒ no FER ⇒ no f_eff, no measured headroom)"
)
#: Printed-row legend (P1 Stage-1 batch-end review F3, carried forward).
LEGEND = "success := ¬failed (= NOT failed); decoded := returned"

#: Decode ledger — structurally frozen at zero (F5: no decode path exists).
DECODE_CALLS = 0


class Refusal(SystemExit):
    """rc=2 pre-write refusal (unauthorized / invalid / gate-blocked)."""


def refuse(reason: str) -> "Any":
    print(f"P4F-REFUSAL rc=2: {reason}", file=sys.stderr)
    raise Refusal(2)


def parse_arm(arm: object) -> dict[str, Any]:
    """Parse an arm name against the frozen F1 two-arm lineage table."""
    if arm not in ARMS:
        refuse(
            f"unknown arm {arm!r} (frozen exactly: P4F-R1 | P4F-R2; "
            f"packet F1 — two arms, frozen order R1→R2, separate report, "
            f"NO pooling)"
        )
    return {"arm": str(arm), "instance": int(ARMS[arm])}  # type: ignore[index]


def identity_row() -> dict[str, Any]:
    """Frozen §2 F7/§2.1 accounting identity row (report-only, NOT f_eff)."""
    return {
        "row": IDENTITY_ROW_MARK,
        "H_anchor": H_ANCHOR,
        "content_2048": CONTENT_2048,
        "leak_bits": LEAK_BITS,
        "f_super_416": F_SUPER_416,
        "f_super_416_literal": F_SUPER_416_LITERAL,
        "headroom_ctx": HEADROOM_CTX,
        "N_req_ctx": N_REQ_CTX,
        "f_eff_slope": F_EFF_SLOPE,
        "f_super_max": F_SUPER_MAX,
        "tag_bits": 64,
        "lambda_total": "leak_EC+64 (form unchanged, ≡ε_EV≈2⁻⁶³)",
        "formula": (
            "f_super=(5·m+64)/(2048·H_anchor); tag 64 bits per superframe "
            "NOT doubled; N_req=ceil(3·4.785675/(1.3−f_super)) report-only"
        ),
        "second_basis": "NONE (single anchor basis; per-source H_MM not in this packet)",
    }


def claim_ceiling_row() -> dict[str, Any]:
    """Frozen §9 claim-ceiling row (carried on every record)."""
    return {
        "row": "claim-ceiling (packet §9)",
        "claim_ceiling": CLAIM_CEILING,
        "pooling": (
            "two instances reported separately; cross-instance pooling of "
            "pins/counts FORBIDDEN; single-instance-as-conclusion FORBIDDEN"
        ),
        "cited_not_consumed": (
            "key-eligible 200/276/364 referenced, never consumed (zero "
            "blocks); N_req 338 report-only (relevant only to a future "
            "zero-failure decode arm)"
        ),
    }


def production_construct(instance: object, trials: object) -> dict[str, Any]:
    """Production constructor: frozen F2 path, ZERO decode.

    ``peg_construct(2048, 416, λ={2:1}, ρ=make_rho(0.796875), seed,
    trials=20, GF(32) field)`` verbatim + ``family="peg-irregular"`` stamp
    + ``refuse_three_shift_cyclic`` guard. The nested-base rank of
    ``rows[0,400)`` is NOT computed here (no constructor-side
    pre-computation); ``construct_and_pin`` computes it once per arm via
    the injected ``rank_fn`` (production wiring: ``production_rank_fn``,
    the frozen PEG RREF — never a decode). Pure in-memory; no disk
    writes. Reached ONLY behind the dual-flag CLI gate
    (``run_execution``); ``execute()`` never defaults to this.
    """
    if isinstance(instance, bool) or not isinstance(instance, int) \
            or int(instance) not in set(ARMS.values()):
        refuse(
            f"construct instance {instance!r} != frozen lineage integers "
            f"{sorted(set(ARMS.values()))} (packet F1 — integer lineage "
            f"literals only; no seed coercion, no seed invention; new "
            f"seeds ⇒ STOP back to the main thread)"
        )
    if isinstance(trials, bool) or not isinstance(trials, int) \
            or int(trials) != P4_MAX_TRIALS:
        refuse(
            f"construct trials {trials!r} != frozen {P4_MAX_TRIALS} "
            f"(packet F2 — trials is a frozen science input; integer "
            f"literal only, no coercion)"
        )
    field = GF2mField.create(s2.Q)
    lam = {int(k): float(v) for k, v in P4_LAMBDA.items()}
    rho = _mcde.make_rho(P4_RHO_RATE, lam)  # ρ=make_rho(0.796875) (F2)
    try:
        code = peg.peg_construct(P4_N, P4_M, lam, rho, int(instance),
                                 max_trials=int(trials), field=field)
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed, zero decode
        refuse(
            f"construction failed (instance {instance}): "
            f"{type(exc).__name__}: {exc}"
        )
    code["family"] = "peg-irregular"
    s2.refuse_three_shift_cyclic({"family": code["family"]})
    code["lambda_edge"] = lam
    code["rho_edge"] = {int(k): float(v) for k, v in rho.items()}
    # No rank pre-computation here (dead: construct_and_pin never reads a
    # code-dict "rank_base_400"; it recomputes the base rank itself via the
    # injected rank_fn and returns gate["rank_base_400"]).
    return code


def production_rank_fn(base_dense: Any) -> int:
    """Production GF(32) rank of ``rows[0,400)`` (F6 gate core).

    The frozen PEG RREF (``peg.rank_GF1024``) — deterministic. This is the
    ONLY other production routine wired by name; it computes a rank and can
    never decode.
    """
    return int(peg.rank_GF1024(GF2mField.create(s2.Q), base_dense))


def construct_and_pin(arm: str, construct_fn: Callable, rank_fn: Callable,
                      clock: Callable | None = None) -> dict[str, Any]:
    """F6 construction gate — ZERO decode, one arm (2 construct calls).

    The lineage instance is constructed TWICE (twice-identical GATED);
    ``four_cycles == 0`` GATED; full ``rank == 416`` GATED; frozen family
    stamp + three-shift-cyclic refusal; base ``rows[0,400)`` rank == 400
    REQUIRED else STOP-BLOCKED; girth RECORDED-not-gated; sockets/parity
    recorded (not gates). Each single construct call is capped at
    ``P4_CONSTRUCT_CAP_S`` — overrun = TERMINAL construction FAIL (rc=2,
    no continuation, packet §5). ``construct_fn`` convention:
    ``(instance, trials) -> code dict``; ``rank_fn`` convention:
    ``(dense rows[0,400)) -> int`` (explicit injection). Both are REQUIRED
    — no default production wiring (AGENTS §10.1 clause 8).
    """
    spec = parse_arm(arm)
    instance = spec["instance"]
    if construct_fn is None:
        refuse("construct_fn required — no default production wiring "
               "(explicit injection only; packet §10(b))")
    if rank_fn is None:
        refuse("rank_fn required — no default production wiring "
               "(explicit injection only; packet §10(b))")
    clock = clock or time.monotonic

    def _build() -> dict[str, Any]:
        t0 = clock()
        code = construct_fn(instance, P4_MAX_TRIALS)
        dt = clock() - t0
        if dt > P4_CONSTRUCT_CAP_S:
            refuse(
                f"single construct call {dt:.1f}s > {P4_CONSTRUCT_CAP_S}s "
                f"cap ({arm} @ {instance}; TERMINAL construction FAIL, "
                f"no continuation; packet §5)"
            )
        return code

    try:
        code_a = _build()
        code_b = _build()
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed, zero decode
        refuse(f"construction failed ({arm} @ {instance}): "
               f"{type(exc).__name__}: {exc}")

    ta, tb = code_a.get("triples"), code_b.get("triples")
    if ta is None or tb is None:
        refuse(f"construction missing triples ({arm}; STOP-BLOCKED; F6)")
    try:
        sa = sorted((int(r), int(c), int(v)) for r, c, v in ta)
        sb = sorted((int(r), int(c), int(v)) for r, c, v in tb)
    except Exception as exc:  # noqa: BLE001
        refuse(f"construction triples corrupt ({arm}; STOP-BLOCKED; F6): "
               f"{type(exc).__name__}: {exc}")
    twice = sa == sb
    if not twice:
        refuse(f"construct-twice mismatch ({arm} @ {instance}; not "
               f"identical; STOP-BLOCKED; F6 twice-identical GATED)")
    if code_a.get("status", "ok") != "ok":
        refuse(f"construction status {code_a.get('status')!r} ({arm}; "
               f"STOP-BLOCKED; F6)")
    if int(code_a.get("n", -1)) != P4_N or int(code_a.get("m", -1)) != P4_M:
        refuse(f"construction (n, m) != ({P4_N}, {P4_M}) ({arm}; got "
               f"({code_a.get('n')}, {code_a.get('m')}); STOP-BLOCKED; F2)")
    try:
        fc = int(code_a.get("four_cycles"))
        rank_full = int(code_a.get("rank"))
    except Exception:  # noqa: BLE001
        refuse(f"construction missing fc/rank pins ({arm}; STOP-BLOCKED)")
    girth = code_a.get("min_girth")  # RECORDED-not-gated (F6)
    if fc != 0:
        refuse(f"{arm} four_cycles {fc} != 0 (STOP-BLOCKED; F6 fc=0 GATED; "
               f"recorded girth {girth})")
    if rank_full != P4_M:
        refuse(f"{arm} rank {rank_full} != {P4_M} (STOP-BLOCKED; F6 "
               f"rank==416 GATED; recorded girth {girth})")
    family = code_a.get("family")
    try:
        s2.refuse_three_shift_cyclic({"family": family})
    except ValueError as exc:
        refuse(f"{arm} banned family provenance (STOP-BLOCKED; F2): {exc}")
    if family != "peg-irregular":
        refuse(f"{arm} family {family!r} != 'peg-irregular' (STOP-BLOCKED; "
               f"F2 NO non-PEG family, NO second matrix family)")
    field = GF2mField.create(s2.Q)
    try:
        dense = peg.sparse_to_dense(sa, P4_N, P4_M, field)
        base_rank = int(rank_fn(dense[:P4_M_BASE]))
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed, zero decode
        refuse(f"base-rank evaluation failed ({arm}; STOP-BLOCKED; F6): "
               f"{type(exc).__name__}: {exc}")
    if base_rank != P4_M_BASE:
        refuse(f"{arm} base rank(rows[0,400)) = {base_rank} != "
               f"{P4_M_BASE} (STOP-BLOCKED; F6 rank_base_400 REQUIRED)")
    return {
        "arm": arm,
        "construct_seed": instance,
        "family": family,
        "four_cycles": fc,
        "rank_full": rank_full,
        "rank_base_400": base_rank,
        "twice_identical": True,
        "girth": girth,  # recorded-not-gated (per instance)
        "sockets": code_a.get("total_sockets"),
        "parity": code_a.get("parallel_edges"),
        "trials_used": code_a.get("trials_used"),
    }


def _check_base_root(root: object) -> str:
    """Fail-closed base-root gate: exactly the ``workspace/P4_FEAS`` family."""
    if not root or not isinstance(root, str):
        refuse(f"root required (fresh additive {P4_ROOT}/<arm>_<uuid8>)")
    parts = root.rstrip("/").split("/")
    if any(p in FORBIDDEN_ROOT_PARTS for p in parts):
        refuse(f"root under forbidden tree (results/outputs_comparison): "
               f"{root}")
    if root.rstrip("/") != P4_ROOT:
        refuse(f"root must be exactly the {P4_ROOT} machine-root family "
               f"(got {root!r}; packet §5 — per-arm roots "
               f"{P4_ROOT_PREFIX}<arm>_<uuid8> only)")
    return root.rstrip("/")


def _check_log_path(log_path: object) -> str:
    """Fail-closed log-path gate: same ``FORBIDDEN_ROOT_PARTS`` guard as
    ``_check_base_root`` now applies to the ``--log`` destination (rc=2
    BEFORE any write); emptiness still refused separately by callers."""
    if not log_path or not isinstance(log_path, str):
        refuse("append-only exploration log path required (packet §6.2)")
    parts = log_path.rstrip("/").split("/")
    if any(p in FORBIDDEN_ROOT_PARTS for p in parts):
        refuse(f"log path under forbidden tree (results/outputs_comparison): "
               f"{log_path}")
    return log_path


def _check_uuid8(uuid8: object) -> dict[str, str]:
    """Validate the Pre-EXECUTE-frozen uuid8 pair (explicit, never generated)."""
    if not isinstance(uuid8, dict):
        refuse("uuid8 mapping required (Pre-EXECUTE-frozen per arm; "
               "packet §5 — no generation path in this module)")
    if set(uuid8) != set(ARM_ORDER):
        refuse(f"uuid8 must carry EXACTLY the frozen arms {list(ARM_ORDER)} "
               f"(got {sorted(map(str, uuid8))}; packet F1)")
    out: dict[str, str] = {}
    for arm in ARM_ORDER:
        value = uuid8.get(arm)
        if not isinstance(value, str) or not UUID8_RE.match(value):
            refuse(f"uuid8 for {arm} must be 8 lowercase hex chars, "
                   f"Pre-EXECUTE-frozen (got {value!r}; packet §5 "
                   f"[TO BE FROZEN] placeholder)")
        out[arm] = value
    return out


def arm_root(base: str, arm: str, uuid8: str) -> str:
    """Per-arm fresh additive root: ``workspace/P4_FEAS/<arm>_<uuid8>``."""
    return f"{P4_ROOT_PREFIX.rstrip('/')}/{arm}_{uuid8}" \
        if base == P4_ROOT else f"{base}/{arm}_{uuid8}"


def default_writer(root: str, files: dict[str, str]) -> None:
    """Single-writer overwrite-in-place inside the FRESH per-arm root only
    (research code; freshness enforced in ``execute`` before first write)."""
    os.makedirs(root, exist_ok=True)
    for name, blob in files.items():
        with open(os.path.join(root, name), "w") as fh:
            fh.write(blob)


def append_log(log_path: str, lines: list[str]) -> None:
    """APPEND-ONLY batch-log write (mode "a"; never truncates, never rewrites)."""
    if not log_path:
        refuse("append-only exploration log path required (packet §6.2)")
    parent = os.path.dirname(log_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(log_path, "a") as fh:
        for line in lines:
            fh.write(line.rstrip("\n") + "\n")


def _default_rss() -> int:
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except Exception:  # noqa: BLE001 — RSS probe is best-effort only
        return 0


def build_record(arm: str, gate: dict[str, Any], wall_s: float,
                 rss_gib: float, verdict: str) -> dict[str, Any]:
    """Build the frozen §3 per-arm record: §3 fields + identity row +
    claim-ceiling row + gate verdicts + ``decode_calls=0``."""
    rho = _mcde.make_rho(P4_RHO_RATE, dict(P4_LAMBDA))
    failed = verdict != "PASS"
    identity = identity_row()
    rec: dict[str, Any] = {
        "arm": arm,
        "construct_seed": gate["construct_seed"],
        "n": P4_N,
        "m": P4_M,
        "lambda_edge": {int(k): float(v) for k, v in P4_LAMBDA.items()},
        "rho_edge": {int(k): float(v) for k, v in rho.items()},
        "trials": P4_MAX_TRIALS,
        "family": gate["family"],
        "four_cycles": gate["four_cycles"],
        "rank_full": gate["rank_full"],
        "rank_base_400": gate["rank_base_400"],
        "twice_identical": gate["twice_identical"],
        "girth": gate["girth"],  # recorded-not-gated, per instance
        "sockets": gate["sockets"],
        "parity": gate["parity"],
        "wall_s": float(wall_s),
        "rss_peak": float(rss_gib),
        "H_anchor": H_ANCHOR,
        "content_2048": CONTENT_2048,
        "f_super_416": F_SUPER_416,
        "headroom_ctx": HEADROOM_CTX,
        "N_req_ctx": N_REQ_CTX,
        "claim_ceiling": CLAIM_CEILING,
        "identity_row": identity,
        "claim_ceiling_row": claim_ceiling_row(),
        "gates": {
            "a_pins": "PASS",  # construct_and_pin returned ⇒ fc/rank/twins/base passed
            "b_f_super_identity": (
                "PASS (arithmetic identity: f_super=1.25741 ≤ 1.3 by the "
                "frozen formula; NOT a science gate — no measured f exists)"
            ),
            "c_nested_base": (
                f"PASS (rank(rows[0,400))=={gate['rank_base_400']}==400 "
                f"recorded; N_req 338 report-only, key-eligible not consumed)"
            ),
            "girth": (
                f"recorded-not-gated: {gate['girth']} (per instance; F6 "
                f"girth sets no gate)"
            ),
        },
        "decode_calls": 0,
        "undetected": ("N/A (zero decode ⇒ no syndrome ⇒ no undetected "
                       "column; any decode-shaped output = STOP-BLOCKED)"),
        "failed": bool(failed),
        "success": bool(not failed),
        "legend": LEGEND,
        "budgets": {
            "wall_cap_s": P4_WALL_CAP_S,
            "construct_cap_s": P4_CONSTRUCT_CAP_S,
            "rss_cap_gib": P4_RSS_CAP_GIB,
            "cpus": P4_CPUS,
            "note": "unspent budget != authorization",
        },
        "reporting": (
            "per instance only; cross-instance pooling of pins/counts "
            "FORBIDDEN; no cross-n transfer inference (n=1024 pins are "
            "never presumed here)"
        ),
        "verdict": verdict,
    }
    missing = [k for k in RESULT_FIELDS if k not in rec]
    if missing:  # frozen §3 field contract — fail closed
        refuse(f"record missing frozen §3 fields {missing} ({arm})")
    return rec


def result_markdown(rec: dict[str, Any]) -> str:
    """Per-arm ``P4FEAS_RESULT_<arm>.md`` body (packet §6.1/§3/§9)."""
    g = rec["gates"]
    lines = [
        f"# P4 n=2048 construction feasibility — {rec['arm']} "
        f"(EXPLORE zero-decode, RAW)",
        "",
        f"- arm/lineage: `{rec['arm']}` construct instance "
        f"{rec['construct_seed']} / trials {rec['trials']} "
        f"(frozen order {'→'.join(ARM_ORDER)}; two instances reported "
        f"SEPARATELY — cross-instance pooling FORBIDDEN)",
        f"- matrix (F2): ONE PEG irregular n={rec['n']} GF(32), "
        f"m={rec['m']}, λ={rec['lambda_edge']} edge perspective, "
        f"ρ=make_rho({P4_RHO_RATE}), family `{rec['family']}` + "
        f"three-shift-cyclic refusal; NO second matrix family, NO "
        f"non-PEG family; mean check degree ≈9.85 (4096 edges/416; the "
        f"m≈208 '19.7' figure is SUPERSEDED)",
        f"- pins (F6, GATED): fc={rec['four_cycles']}==0 AND "
        f"rank_full={rec['rank_full']}==416 AND twice-identical="
        f"{rec['twice_identical']} AND rank(rows[0,400))="
        f"{rec['rank_base_400']}==400 REQUIRED ⇒ {g['a_pins']}; girth "
        f"{rec['girth']} RECORDED-not-gated; sockets={rec['sockets']} / "
        f"parity={rec['parity']} recorded (not gates)",
        f"- gate (b) identity: content_2048={rec['content_2048']:.6f} b, "
        f"leak=2144 b (tag 64 bits/superframe, not doubled), "
        f"f_super={rec['f_super_416']:.6f} (frozen line "
        f"{F_SUPER_416_LITERAL}) ≤ 1.3 — arithmetic identity, "
        f"NEVER quoted as f_eff (zero decode ⇒ no FER ⇒ no f_eff)",
        f"- gate (c) nested base: rank(rows[0,400))==400 ⇒ "
        f"{g['c_nested_base']}; headroom_ctx="
        f"{rec['headroom_ctx']:.6f} b vs gate bar — MEASURED headroom is "
        f"UNDECIDABLE at zero decode (deferred to a future decode packet)",
        f"- identity row (F7): {IDENTITY_ROW_MARK}",
        f"- wall/RSS (per instance): {rec['wall_s']:.6f} s / cap "
        f"{P4_WALL_CAP_S} s (single construct ≤{P4_CONSTRUCT_CAP_S} s "
        f"terminal); peak RSS {rec['rss_peak']:.6f} GiB / cap "
        f"{P4_RSS_CAP_GIB} GiB; {P4_CPUS} CPU; budget total is tallied in "
        f"the exploration log",
        f"- decode: `decode_calls={rec['decode_calls']}` (REQUIRED and "
        f"asserted; no channel read, no block loop, no `undetected` "
        f"column — {rec['undetected']})",
        f"- legend: `{rec['legend']}`",
        f"- claim ceiling (§9): {rec['claim_ceiling']}",
        f"- verdict: {rec['verdict']} (failed={rec['failed']}, "
        f"success={rec['success']}; success := ¬failed)",
        "",
    ]
    return "\n".join(lines)


def _print_arm_line(rec: dict[str, Any]) -> None:
    """6-decimal printed row + success=¬failed legend semantics."""
    print(
        f"P4FEAS {rec['arm']} verdict={rec['verdict']} "
        f"success={rec['success']} failed={rec['failed']} "
        f"fc={rec['four_cycles']} rank_full={rec['rank_full']} "
        f"rank_base_400={rec['rank_base_400']} "
        f"twice_identical={rec['twice_identical']} girth={rec['girth']} "
        f"sockets={rec['sockets']} parity={rec['parity']} "
        f"wall_s={rec['wall_s']:.6f} rss_peak={rec['rss_peak']:.6f} "
        f"content_2048={rec['content_2048']:.6f} "
        f"f_super_416={rec['f_super_416']:.6f} "
        f"headroom_ctx={rec['headroom_ctx']:.6f} "
        f"N_req_ctx={rec['N_req_ctx']} decode_calls=0"
    )
    print(f"P4FEAS legend: {LEGEND} (6dp printed rows)")


def execute(*, root: str, uuid8: dict[str, str],
            construct_fn: Callable | None,
            rank_fn: Callable | None,
            clock: Callable | None = None,
            rss_fn: Callable | None = None,
            writer: Callable | None = None,
            log_path: str = DEFAULT_LOG_PATH) -> dict[str, Any]:
    """Run the frozen P4 construction-feasibility batch (both arms, F1 order).

    Arms run SEQUENTIALLY in the frozen order ``P4F-R1 → P4F-R2``; the next
    arm runs only while the preceding machine gate permits (its verdict is
    PASS), otherwise it is recorded ``NOT-RUN`` (packet §7 one-authorization
    arm sequence). ``construct_fn``/``rank_fn`` are REQUIRED (explicit
    injection; any ``None`` refuses rc=2 BEFORE any root, log, or write) —
    there is NO default production construction path in this core; only
    ``run_execution`` (dual-flag CLI-gated) wires one, explicitly. Zero
    decode happens structurally (no decode callable exists here).
    ``decode_calls == 0`` is asserted before returning. All writes stay
    under the fresh per-arm roots + the append-only log; roots must not
    exist (fresh additive ⇒ resume/continue is structurally impossible).
    """
    base = _check_base_root(root)
    uuids = _check_uuid8(uuid8)
    if construct_fn is None:
        refuse("construct_fn required — no default production wiring "
               "(explicit injection only; packet §10(b); AGENTS §10.1 c8)")
    if rank_fn is None:
        refuse("rank_fn required — no default production wiring "
               "(explicit injection only; packet §10(b); AGENTS §10.1 c8)")
    _check_log_path(log_path)  # FORBIDDEN_ROOT_PARTS guard (same as --root)
    for arm in ARM_ORDER:
        d = arm_root(base, arm, uuids[arm])
        if os.path.exists(d):
            refuse(f"arm root not fresh: {d} (fresh additive per-arm root "
                   f"mandatory; NO resume/continue; packet §5)")
    clock = clock or time.monotonic
    rss_fn = rss_fn or _default_rss
    writer = writer or default_writer

    print(f"P4FEAS legend: {LEGEND} (6dp printed rows)")
    append_log(log_path, [
        f"- [batch] start arms={'→'.join(ARM_ORDER)} root={base} "
        f"decode_calls=0"
    ])
    arm_results: dict[str, dict[str, Any]] = {}
    gate_permits = True
    for arm in ARM_ORDER:
        if not gate_permits:
            arm_results[arm] = {
                "arm": arm,
                "verdict": "NOT-RUN",
                "reason": ("machine gate: previous arm did not PASS "
                           "(frozen order R1→R2; packet §7)"),
                "decode_calls": 0,
            }
            append_log(log_path, [
                f"- [{arm}] uuid8={uuids[arm]} verdict=NOT-RUN (previous "
                f"arm machine gate did not permit continuation) "
                f"decode_calls=0"
            ])
            continue
        arm_dir = arm_root(base, arm, uuids[arm])
        t0 = clock()
        try:
            gate = construct_and_pin(arm, construct_fn, rank_fn, clock=clock)
        except Refusal:
            append_log(log_path, [
                f"- [{arm}] uuid8={uuids[arm]} verdict=FAIL-pins "
                f"STOP-BLOCKED (exact refusal text on stderr; pins gate "
                f"miss or terminal construction failure; inputs unchanged; "
                f"no repair path used) decode_calls=0"
            ])
            raise
        wall_s = float(clock() - t0)
        try:
            rss_gib = float(rss_fn()) / (1024 ** 3)
        except Exception:  # noqa: BLE001 — probe failure never halts
            rss_gib = 0.0
        if wall_s > P4_WALL_CAP_S:
            verdict = "INCOMPLETE-wall"  # retained, NEVER continued (§5)
        elif rss_gib >= P4_RSS_CAP_GIB:
            verdict = "INCOMPLETE-budget"  # retained, never continued
        else:
            verdict = "PASS"
        rec = build_record(arm, gate, wall_s, rss_gib, verdict)
        writer(arm_dir, {
            f"P4FEAS_RESULT_{arm}.md": result_markdown(rec),
            "construction.json": json.dumps(rec, indent=1, sort_keys=True,
                                            default=str),
            "pins_report.json": json.dumps(
                {**{k: rec[k] for k in RESULT_FIELDS},
                 "gates": rec["gates"], "decode_calls": 0,
                 "failed": rec["failed"], "success": rec["success"],
                 "legend": rec["legend"], "verdict": verdict},
                indent=1, sort_keys=True, default=str),
        })
        _print_arm_line(rec)
        append_log(log_path, [
            f"- [{arm}] uuid8={uuids[arm]} verdict={verdict} "
            f"fc={rec['four_cycles']} rank_full={rec['rank_full']} "
            f"rank_base_400={rec['rank_base_400']} "
            f"twice_identical={rec['twice_identical']} "
            f"girth={rec['girth']} (recorded-not-gated) "
            f"wall_s={rec['wall_s']:.6f} rss_gib={rec['rss_peak']:.6f} "
            f"decode_calls=0 success={'NOT-failed' if rec['success'] else 'failed'}"
        ])
        arm_results[arm] = rec
        gate_permits = verdict == "PASS"

    tally = {arm: arm_results.get(arm, {}).get("verdict", "MISSING")
             for arm in ARM_ORDER}
    batch = {
        "mode": "p4-feas-construct zero-decode",
        "arm_order": list(ARM_ORDER),
        "root": base,
        "uuid8": uuids,
        "arms": arm_results,
        "tally": tally,
        "decode_calls": 0,
        "repair": "no repair path used",
        "claim_ceiling": CLAIM_CEILING,
        "identity_row": identity_row(),
        "legend": LEGEND,
    }
    append_log(log_path, [
        f"- [batch] tally={json.dumps(tally, sort_keys=True)} "
        f"decode_calls=0 repair=no repair path used claim_ceiling=row-per-arm"
    ])
    assert DECODE_CALLS == 0, "decode_calls must remain 0 (packet F5)"
    return batch


def run_execution(root: str, uuid8: dict[str, str],
                  log_path: str = DEFAULT_LOG_PATH) -> int:
    """Production batch run — reached ONLY via the dual-flag CLI gate.

    Explicit wiring, one place: production construction + production rank
    (both zero-decode routines), fresh per-arm roots under
    ``workspace/P4_FEAS/``, append-only exploration log. The R1→R2 order,
    the single authorization, and the uuid8 freeze live in the
    packet/Pre-EXECUTE record — mirrored here only as literals.
    """
    batch = execute(root=root, uuid8=uuid8,
                    construct_fn=production_construct,
                    rank_fn=production_rank_fn, log_path=log_path)
    print(json.dumps({
        "mode": batch["mode"],
        "arm_order": batch["arm_order"],
        "root": batch["root"],
        "tally": batch["tally"],
        "decode_calls": batch["decode_calls"],
        "repair": batch["repair"],
        "log": log_path,
    }, indent=1, sort_keys=True, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="P4 n=2048 construction-feasibility thin runner "
                    "(zero decode; both arms in frozen order R1→R2; "
                    "production construction requires BOTH execution flags "
                    "+ every frozen literal echo + both Pre-EXECUTE-frozen "
                    "uuid8 roots).")
    ap.add_argument("--execute-real", action="store_true", default=False)
    ap.add_argument("--execution-authorized", action="store_true",
                    default=False)
    ap.add_argument("--root", default="")
    ap.add_argument("--r1-uuid8", default="")
    ap.add_argument("--r2-uuid8", default="")
    ap.add_argument("--log", default=DEFAULT_LOG_PATH)
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--m", type=int, default=None)
    ap.add_argument("--trials", type=int, default=None)
    ap.add_argument("--seeds", default="")
    ap.add_argument("--lambda-edge", dest="lambda_edge", default="")
    ap.add_argument("--rho-rate", dest="rho_rate", type=float, default=None)
    args = ap.parse_args(argv)

    # Dual-flag gate FIRST: refuse rc=2 BEFORE any root/log/write.
    if not args.execute_real:
        refuse("refusing: --execute-real missing (rc=2 pre-anything; "
               "packet §10: unfilled grant = unauthorized)")
    if not args.execution_authorized:
        refuse("refusing: --execution-authorized missing (rc=2 "
               "pre-anything; packet §10: unfilled grant = unauthorized)")
    if args.n != P4_N:
        refuse(f"--n must be the frozen {P4_N} (got {args.n}; packet F2)")
    if args.m != P4_M:
        refuse(f"--m must be the frozen {P4_M} (got {args.m}; packet F2)")
    if args.trials != P4_MAX_TRIALS:
        refuse(f"--trials must be the frozen {P4_MAX_TRIALS} "
               f"(got {args.trials}; packet F2)")
    if args.seeds != "2026092001,2026092011":
        refuse(f"--seeds must be the frozen lineage literal "
               f"2026092001,2026092011 (got {args.seeds!r}; packet F1 — "
               f"no seed invention)")
    if args.lambda_edge != "{2:1}":
        refuse(f"--lambda-edge must be the frozen {{2:1}} literal "
               f"(got {args.lambda_edge!r}; packet F2 edge perspective)")
    if args.rho_rate != P4_RHO_RATE:
        refuse(f"--rho-rate must be the frozen {P4_RHO_RATE} "
               f"(got {args.rho_rate}; packet F2 ρ=make_rho(0.796875))")
    if not args.root:
        refuse(f"root required: fresh additive {P4_ROOT}/<arm>_<uuid8> "
               f"(packet §5)")
    _check_base_root(args.root)  # rc=2 BEFORE any construct/write
    uuid8 = {"P4F-R1": args.r1_uuid8, "P4F-R2": args.r2_uuid8}
    _check_uuid8(uuid8)  # rc=2 BEFORE any construct/write
    _check_log_path(args.log)  # rc=2 BEFORE any construct/write (same guard)
    return run_execution(args.root, uuid8, args.log)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
