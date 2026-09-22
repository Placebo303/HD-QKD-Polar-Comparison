"""P1 Stage-1 rate-adaptive rescue thin runner (EXPLORE code — NOT execution).

Frozen contract: ``docs/research_cycles/V80-NBLDPC-JAN21/P1_STAGE1_PACKET.md``
(§§1–11; Acceptance ID ``G-P1S1``) + ``P1_STAGE1_PROMPT.md``. This module
is the packet §10(b) execution surface; implementing it carries NO track gate
(AGENTS §1.2 matrix — implementation-only). The track gate hangs on the FIRST
SYNTHETIC EXECUTION, which requires the packet §10(d) authorization block
signed FIRST. This prompt/module authorizes any execution = 0.

Safety shape (why this ONE additive module exists):

- **NO default production decoding.** ``execute()`` REFUSES to run unless an
  explicit ``construct_fn``, ``decode_fn``, ``rescue_decode_fn`` AND
  ``rank_fn`` are injected — any ``None`` refuses rc=2 BEFORE any
  construction, root, decode, or write. There is no silent production wiring
  anywhere in the execution core. The CLI reaches a production decode ONLY
  behind BOTH flags ``--execute-real`` AND ``--execution-authorized`` plus
  every frozen literal matching (F1–F3); a bare invocation refuses rc=2
  BEFORE any bind, construct, root or write. ``--dry`` is the only pre-grant
  path and builds no decode function at all (zero decode by construction).
- **No real-data path anywhere** (F4): the ONLY channel is the frozen
  synthetic ``gamma_f03.npz`` + ``gamma_f03_pb.npz`` sibling under
  ``docs/research_cycles/V80-NBLDPC-JAN21/``, bound READ-ONLY through the
  frozen consumer ``s2c.bind_empirical_bundle`` (shape/normalization gates;
  never refit). No ``.ttbin`` read path exists (no such import, path, or
  read anywhere here).
- **Frozen procedure F1–F10**: exactly two arms — ``P1S1-R1`` construct
  instance 2026092001 / ``P1S1-R2`` construct instance 2026092011 — reported
  SEPARATELY; cross-instance pooling FORBIDDEN (incl. any 6+4 sum). Base code
  = nested leading-200 ``rows[0,200)`` of the SAME-instance frozen A208
  matrix (never an A200 construct; single segment ONLY — NO two/multi
  segment). 240 paired blocks, seeds ``2026096401+idx`` idx 0..239, stream
  ``o1_blk:{seed}`` (FRESH interval — zero overlap with the S0.1
  2026095601..2026095840 family; NO independence claim). Decoder/accept is
  the b2f lineage VERBATIM via the frozen ``b2f.decode_block_marginal``
  (soft-marginal prior + v28 ``decode_error_domain_posterior`` max_iter 300
  / streak 3, ``exact_match`` accept; NO genie u1, NO argmax û1, NO L1 code,
  NO refit). Stage-1 AND Stage-2 both COLD start (NO warm-start, F2).
  Stage-2 covers EXACTLY the Stage-1 non-``success`` block set (exact_match
  false full set) disclosing ``rows[200,208)`` with a COLD full-matrix
  re-decode (``rows[0,208)``); total rows 208 <= 208 HARD cap (F2).
- **F9 no early stop**: ALL 240 Stage-1 blocks always run; bar-12 NEVER
  stops a run — it is a report-only route-context line and adjudicates
  nothing; the Stage-2 set is NEVER trimmed.
- **F10 class separation**: ``exact_match is True`` = success; anything
  else counts into k (Stage-1) / F (final); a syndrome-valid-but-mismatched
  block is counted SEPARATELY as ``undetected`` and is NEVER merged into
  success (per-column; no pooling).
- **F7 accounting** (frozen V80 anchor basis, content = 852.544 b):
  baseline leak 1064 b ⇒ ``f_super_base = 1064/852.544 = 1.24803``;
  all-triggered worst-case leak 1104 b ⇒ ``f_super_full =
  (5*208+64)/852.544 = 1104/852.544 = 1.294947`` (by construction, NOT a
  science gate); ``E[leak] = 1064 + 40·r`` with ``r = #rescued/240`` (this
  arm's own counts); ``f_exp = E[leak]/852.544`` (this arm's own blended
  basis); ``f_eff = f_exp + 4.785675·(F/240)`` (this arm's own final F);
  ``headroom = 1108.31 − E[leak]``. f_super/f_exp are NEVER quoted as
  f_eff (F>0); no second basis is ever computed; ``N_req`` is report-only
  (relevant only if F=0).
- **Budget (§5)**: wall ≤ 3600 s/arm (BOTH stages combined, one window);
  batch ceiling 7200 s (batch-level, tallied in the exploration log, not
  here); per-decode ≤ 300 s (overrun = TERMINAL, the block counts fail, no
  continuation); RSS < 2 GiB; 1 CPU. NO retry / resume / adaptive:
  wall-partial ⇒ ``INCOMPLETE-wall`` retained forever; the root must be
  fresh (existing root refuses), so resume is structurally impossible.
- **Roots**: fresh additive ``workspace/P1_STAGE1/<arm>_<uuid8>/`` ONLY;
  anything under ``results/`` or ``comparison_bench/outputs_comparison/``
  refuses; existing evidence roots are never touched; nothing is written
  outside the fresh per-arm root.

Construction pins F6 (ZERO decode): the same-instance A208 build is
constructed TWICE (twice-identical GATED), ``four_cycles == 0`` and full
``rank == 208`` GATED, girth RECORDED-not-gated; the base code
``rows[0,200)`` must satisfy ``rank == 200`` REQUIRED else STOP-BLOCKED
before any decode. ``execute()`` re-runs this gate on every invocation.
``--dry`` reports the F6 base-rank check as a rank==200 DRY PLACEHOLDER
(PENDING; no construction, no decode); ``--dry --construct-pins`` performs
the full zero-decode pin run for both instances (pre-grant Q5).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v10_common as common,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v10_peg as peg,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    v80_b2f_campaign as b2f,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    v80_b2g_campaign as b2g,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    v80_o1_campaign as o1,
)
from comparison_bench.src.comparison_bench.formal_ir import v80_s2_peg as s2
from comparison_bench.src.comparison_bench.formal_ir import (
    v80_s2c_campaign as s2c,
)
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (
    GF2mField,
)

__all__ = [
    "P1_N", "P1_M_BASE", "P1_DELTA_M", "P1_M_TOTAL", "P1_N_BLOCKS",
    "P1_BLOCK_BASE", "P1_STREAM", "P1_MAX_TRIALS", "P1_MAX_ITER",
    "P1_STREAK", "ARMS", "P1_WALL_CAP_S", "P1_BATCH_CEILING_S",
    "P1_PER_DECODE_CAP_S", "P1_RSS_CAP_GIB", "P1_CPUS", "P1_ROOT_PREFIX",
    "FORBIDDEN_ROOT_PARTS", "CHANNEL_NPZ", "CHANNEL_SOURCE",
    "CONTENT_BITS", "LEAK_BASE_BITS", "LEAK_FULL_BITS", "F_SUPER_BASE",
    "F_SUPER_BASE_LITERAL", "F_SUPER_FULL", "F_SUPER_FULL_LITERAL",
    "F_EFF_SLOPE", "LEAK_CAP_BITS", "F_SUPER_MAX", "BAR12",
    "CSV_COLUMNS", "CLAIM_CEILING",
    "Refusal", "refuse", "parse_arm", "block_seed", "stream_seed",
    "fail_bar", "f_super_for", "expected_leak_for", "f_exp_for",
    "f_eff_for", "n_required_for", "production_rank_fn",
    "construct_and_pin", "_check_root",
    "default_writer", "block_accounting_csv", "result_markdown",
    "execute", "run_execution", "dry_pins", "main",
]

#: Frozen single-code length (o1.O1_N; content-basis denominator 1024·H).
P1_N = 1024
#: Frozen base rows — nested leading-200 of the same-instance A208 (F2).
P1_M_BASE = 200
#: Frozen single-segment rescue disclosure rows[200,208) = 40 b (F2).
P1_DELTA_M = 8
#: Frozen total rows (base + single rescue segment; F2 HARD cap).
P1_M_TOTAL = 208
assert P1_M_BASE + P1_DELTA_M == P1_M_TOTAL  # frozen single segment
assert P1_M_TOTAL <= 208  # HARD top: m1+m2<=208 (V80_BASELINE §2)
#: Frozen campaign width: 240 paired blocks per arm, both stages always full
#: unless a terminal budget event fires (F3/F9).
P1_N_BLOCKS = 240
#: Frozen literal block-seed base (packet F3; FRESH — outside every prior
#: family: 2026095601..2026095840 paired, 2026095501 O1, S2 families).
P1_BLOCK_BASE = 2026096401
#: Frozen literal stream template (packet F3; b2f/O1R/P0/L1B/X1 pairing).
P1_STREAM = "o1_blk:{seed}"
#: Frozen constructor trials (b2f/o1 ARMS construction pins).
P1_MAX_TRIALS = 20
#: Frozen decoder cap (packet F5; v28 streak default 3).
P1_MAX_ITER = 300
#: Frozen decoder streak (packet F5; recorded — the frozen kernel default).
P1_STREAK = 3
#: Frozen arms → construct instance (packet F1; separate report, NO pooling).
ARMS: dict[str, int] = {"P1S1-R1": 2026092001, "P1S1-R2": 2026092011}
#: Frozen per-arm wall budget, BOTH stages combined, one window (packet §5).
P1_WALL_CAP_S = 3600
#: Frozen batch total ceiling (packet §5; tallied batch-level in the log).
P1_BATCH_CEILING_S = 7200
#: Frozen per-decode terminal cap (packet §5: overrun = terminal, block
#: counts fail, no continuation).
P1_PER_DECODE_CAP_S = 300
#: Frozen RSS cap (packet §5).
P1_RSS_CAP_GIB = 2
#: Frozen CPU budget (packet §5).
P1_CPUS = 1
#: Fresh additive machine-root family (packet §5).
P1_ROOT_PREFIX = "workspace/P1_STAGE1/"
#: Roots this executor never writes under (packet §5/§8).
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")
#: Frozen 2M synthetic channel, READ-ONLY, never refit (packet F4).
CHANNEL_NPZ = "docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz"
#: Frozen channel source label (frozen 2M bundle; s2c.SOURCE_DEFAULT).
CHANNEL_SOURCE = "2M"
#: Frozen content basis (V80_BASELINE §2 anchor: 1024·0.83256272 b).
CONTENT_BITS = 852.544
#: Frozen baseline leak at m=200 incl. 64-bit tag (packet F7).
LEAK_BASE_BITS = 5 * P1_M_BASE + 64  # = 1064
#: Frozen all-triggered worst-case leak at m=208 incl. tag (packet F7).
LEAK_FULL_BITS = 5 * P1_M_TOTAL + 64  # = 1104
#: Frozen f_super baseline (packet F7): 1064/852.544 = 1.24803…
F_SUPER_BASE = LEAK_BASE_BITS / CONTENT_BITS
#: Frozen 5-decimal restatement of the baseline line (packet F7).
F_SUPER_BASE_LITERAL = "1.24803"
#: Frozen f_super worst-case (packet F7): (5*208+64)/852.544 = 1.294947…
F_SUPER_FULL = LEAK_FULL_BITS / CONTENT_BITS
#: Frozen 6-decimal restatement of the worst-case line (packet F7).
F_SUPER_FULL_LITERAL = "1.294947"
#: Frozen f_eff slope (packet F7; V80_BASELINE §2).
F_EFF_SLOPE = 4.785675
#: Frozen leak cap 1.3·852.544 b (packet F7 gate (b)/(c) arithmetic).
LEAK_CAP_BITS = 1108.31
#: Frozen efficiency bar (packet F7 gate (b); worst-case by construction).
F_SUPER_MAX = 1.3
#: Frozen bar-12 value via the frozen o1 rule (floor(240·0.05) = 12) —
#: REPORT-ONLY route context; NEVER a stop, NEVER an adjudication (F9).
BAR12 = o1.fail_bar(P1_N_BLOCKS)
#: Frozen per-block accounting columns: X1/S0.1-isomorphic + Stage marker
#: (packet §3).
CSV_COLUMNS = ["block_idx", "seed", "stage", "iters", "wall_s", "decoded",
               "failed", "undetected", "prior_entropy_bits",
               "u1_mismatches"]
#: Frozen claim ceiling (packet §9).
CLAIM_CEILING = (
    "synthetic paired-frame rate-adaptive rescue efficiency ONLY "
    "(per-instance Stage-1 k/240 + rescued/attempted + final F/240 + "
    "trigger rate r + frozen-basis E[leak]/f_exp/f_eff + iters/wall + "
    "undetected single count) as S-B main-path P1 evidence; NOT SKR, "
    "NOT qualification, NOT route adjudication, NOT operating-point "
    "selection, NOT real-data FER, NOT a certifiable/literature-comparable "
    "f_eff<=1.3 sentence, NOT publication material; key-eligible "
    "200/276/364 cited-not-consumed; any later citation MUST list both "
    "instances separately (pooling incl. 6+4 FORBIDDEN)"
)


class Refusal(SystemExit):
    """rc=2 pre-write refusal (unauthorized / invalid / gate-blocked)."""


def refuse(reason: str) -> "Any":
    print(f"P1S1-REFUSAL rc=2: {reason}", file=sys.stderr)
    raise Refusal(2)


def parse_arm(arm: str) -> dict[str, Any]:
    """Parse ``P1S1-R1``/``P1S1-R2`` against the frozen two-arm table (F1)."""
    if arm not in ARMS:
        refuse(f"unknown arm {arm!r} (frozen exactly: P1S1-R1 | P1S1-R2; "
               f"packet F1 — two arms, separate report, NO pooling)")
    return {"arm": str(arm), "instance": int(ARMS[arm])}


def block_seed(idx: int) -> int:
    """Frozen literal block seed: 2026096401+idx, idx=0..239 (F3)."""
    if isinstance(idx, bool) or not isinstance(idx, int) \
            or not 0 <= int(idx) < P1_N_BLOCKS:
        refuse(f"block idx must be in 0..{P1_N_BLOCKS - 1} (got {idx!r})")
    return P1_BLOCK_BASE + int(idx)


def stream_seed(seed: int) -> int:
    """Frozen stream derivation (o1.stream_seed, read-only reuse): F3."""
    return o1.stream_seed(int(seed))


def fail_bar(n_blocks: int) -> int:
    """Derived bar via the frozen o1 rule — REPORT-ONLY here (F9)."""
    return o1.fail_bar(int(n_blocks))


def f_super_for(m: int = P1_M_TOTAL) -> float:
    """f_super = (5m+64)/852.544 on the frozen anchor basis (F7)."""
    return float(5 * int(m) + 64) / CONTENT_BITS


def expected_leak_for(n_rescued: int) -> float:
    """E[leak] = 1064 + 40·r with r = #rescued/240 (packet F7, this arm)."""
    return float(LEAK_BASE_BITS) + 40.0 * (float(n_rescued) / P1_N_BLOCKS)


def f_exp_for(n_rescued: int) -> float:
    """f_exp = E[leak]/852.544, this arm's OWN blended basis (F7)."""
    return expected_leak_for(n_rescued) / CONTENT_BITS


def f_eff_for(n_rescued: int, final_fails: int) -> float:
    """f_eff = f_exp + 4.785675·(F/240), this arm's OWN final F (F7)."""
    return f_exp_for(n_rescued) + F_EFF_SLOPE * (float(final_fails)
                                                / P1_N_BLOCKS)


def n_required_for(f_exp: float) -> int | None:
    """Report-only N_req rule (packet F8): relevant only if final F=0."""
    if float(f_exp) >= F_SUPER_MAX:
        return None
    return int(math.ceil(3.0 * F_EFF_SLOPE / (F_SUPER_MAX - float(f_exp))))


def production_rank_fn(base_dense: Any) -> int:
    """Production GF(32) rank of the base rows[0,200) (F6 gate core).

    Uses the frozen PEG RREF (``peg.rank_GF1024``) — deterministic. This is
    the ONLY production routine wired by name; it computes a rank and can
    never decode.
    """
    return int(peg.rank_GF1024(GF2mField.create(s2.Q), base_dense))


def construct_and_pin(arm: str, construct_fn: Callable,
                      rank_fn: Callable) -> dict[str, Any]:
    """F6 construction gate — ZERO decode, runs before any decode.

    Same-instance A208 built TWICE (twice-identical GATED);
    ``four_cycles == 0`` GATED; full ``rank == 208`` GATED; girth
    RECORDED-not-gated; base = ``rows[0,200)`` with
    ``rank == 200`` REQUIRED else STOP-BLOCKED. Returns BOTH the base-code
    dict (m=200, rescue rows EXCLUDED — Stage-1 COLD) and the full-code dict
    (m=208 = rows[0,208) — Stage-2 COLD full-matrix re-decode); total rows
    208 <= 208 HARD cap asserted. ``construct_fn`` convention:
    ``(instance, trials) -> code dict``. ``rank_fn`` convention:
    ``(dense rows) -> int`` (explicit injection). NO warm-start state is
    carried between the two dicts (F2); Stage-2 re-decodes COLD from the
    same frozen triples.
    """
    spec = parse_arm(arm)
    instance = spec["instance"]
    try:
        code_a = construct_fn(instance, P1_MAX_TRIALS)
        code_b = construct_fn(instance, P1_MAX_TRIALS)
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed pre-decode
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
    if sa != sb:
        refuse(f"construct-twice mismatch ({arm} @ {instance}; not "
               f"identical; STOP-BLOCKED; F6)")
    if code_a.get("status", "ok") != "ok":
        refuse(f"construction status {code_a.get('status')!r} ({arm}; "
               f"STOP-BLOCKED; F6)")
    if int(code_a.get("n", -1)) != P1_N or int(code_a.get("m", -1)) \
            != P1_M_TOTAL:
        refuse(f"construction (n, m) != ({P1_N}, {P1_M_TOTAL}) ({arm}; "
               f"got ({code_a.get('n')}, {code_a.get('m')}); STOP-BLOCKED)")
    try:
        fc = int(code_a.get("four_cycles"))
        a208_rank = int(code_a.get("rank"))
    except Exception:  # noqa: BLE001
        refuse(f"construction missing fc/rank pins ({arm}; STOP-BLOCKED)")
    girth = code_a.get("min_girth")  # recorded-not-gated (F6)
    if fc != 0:
        refuse(f"{arm} A208 four_cycles {fc} != 0 (STOP-BLOCKED; F6; "
               f"recorded girth {girth})")
    if a208_rank != P1_M_TOTAL:
        refuse(f"{arm} A208 rank {a208_rank} != {P1_M_TOTAL} "
               f"(STOP-BLOCKED; F6)")
    field = GF2mField.create(s2.Q)
    dense = peg.sparse_to_dense(sa, P1_N, P1_M_TOTAL, field)
    try:
        base_rank = int(rank_fn(dense[:P1_M_BASE]))
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed pre-decode
        refuse(f"base-rank evaluation failed ({arm}; STOP-BLOCKED; F6): "
               f"{type(exc).__name__}: {exc}")
    if base_rank != P1_M_BASE:
        refuse(f"{arm} base rank(rows[0,200)) = {base_rank} != {P1_M_BASE} "
               f"(STOP-BLOCKED; packet F6 — rank==200 REQUIRED)")
    base_triples = [(int(r), int(c), int(v)) for r, c, v in sa
                    if int(r) < P1_M_BASE]  # rescue rows rows[200,208)
    # EXCLUDED from the Stage-1 dict; Stage-2 discloses them in one
    # single segment (F2 single-segment ONLY — no multi-segment path).
    if P1_M_BASE + P1_DELTA_M != P1_M_TOTAL or P1_M_TOTAL > 208:
        refuse(f"row budget drifted: {P1_M_BASE}+{P1_DELTA_M} != "
               f"{P1_M_TOTAL}<=208 (STOP-BLOCKED; packet F2 HARD cap)")
    base_code = {
        "n": P1_N,
        "m": P1_M_BASE,
        "triples": base_triples,
        "status": "ok",
        "family": code_a.get("family"),
        "lambda_edge": code_a.get("lambda_edge"),
        "rho_edge": code_a.get("rho_edge"),
        "source_arm": "A208",
        "construct_instance": instance,
        "nested_base": ("rows[0,200) of the same-instance frozen A208 "
                        "matrix (nested leading-200; NOT an A200 construct; "
                        "rescue rows[200,208) undisclosed in Stage-1; "
                        "NO warm start)"),
    }
    full_code = {
        "n": P1_N,
        "m": P1_M_TOTAL,
        "triples": [(int(r), int(c), int(v)) for r, c, v in sa],
        "status": "ok",
        "family": code_a.get("family"),
        "lambda_edge": code_a.get("lambda_edge"),
        "rho_edge": code_a.get("rho_edge"),
        "source_arm": "A208",
        "construct_instance": instance,
        "nested_full": ("rows[0,208) of the same-instance frozen A208 "
                        "matrix (Stage-2 COLD full-matrix re-decode; "
                        "single segment 200→208; NO warm start)"),
    }
    return {
        "base": base_code,
        "full": full_code,
        "a208_pins": {"four_cycles": fc, "rank": a208_rank,
                      "girth": girth, "twice_identical": True},
        "base_rank": base_rank,
        "measured_girth": girth,
    }


def _check_root(root: str, arm: str) -> None:
    if not root:
        refuse(f"root required (fresh additive {P1_ROOT_PREFIX}"
               f"<arm>_<uuid8>)")
    if not str(root).startswith(P1_ROOT_PREFIX):
        refuse(f"root must be fresh additive {P1_ROOT_PREFIX}"
               f"<arm>_<uuid8> (got {root})")
    name = Path(str(root)).name
    if not name.startswith(f"{arm}_"):
        refuse(f"root name must start with {arm}_ (arm/root mismatch: "
               f"{name}; packet §5 per-arm roots)")
    parts = Path(str(root)).parts
    if any(p in FORBIDDEN_ROOT_PARTS for p in parts):
        refuse(f"root under forbidden tree (results/outputs_comparison): "
               f"{root}")


def default_writer(root: str, files: dict[str, str]) -> None:
    """Single-writer overwrite-in-place inside the FRESH per-arm root only
    (research code; freshness enforced in ``execute`` before first write)."""
    os.makedirs(root, exist_ok=True)
    for name, blob in files.items():
        with open(os.path.join(root, name), "w") as fh:
            fh.write(blob)


def _default_rss() -> int:
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except Exception:  # noqa: BLE001 — RSS probe is best-effort only
        return 0


def block_accounting_csv(rows: list[dict]) -> str:
    """Per-block accounting table — EXACTLY the packet §3 columns."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(CSV_COLUMNS)
    for r in rows:
        w.writerow([r.get(c) for c in CSV_COLUMNS])
    return buf.getvalue()


def result_markdown(summary: dict[str, Any]) -> str:
    """Per-arm ``P1S1_RESULT_<arm>.md`` body (packet §3)."""
    pins = summary["pins"]
    lines = [
        f"# P1 Stage-1 rescue result — {summary['arm']} (EXPLORE synthetic, RAW)",
        "",
        f"- arm: `{summary['arm']}`; construct instance "
        f"{summary['construct_instance']} (recorded girth "
        f"{pins['girth']}); base code = nested leading-200 rows[0,200) of "
        f"THAT instance's A208 (NOT an A200 construct; single segment "
        f"200→208; both stages COLD, NO warm start)",
        f"- pins (F6): A208 fc={pins['four_cycles']} + rank {pins['rank']} "
        f"+ twice-identical GATED; base rank(rows[0,200))="
        f"{summary['base_rank']} REQUIRED==200; girth {pins['girth']} "
        f"recorded-not-gated; total rows {P1_M_TOTAL}<=208 HARD cap",
        f"- channel: `{summary['channel_path']}` + sibling "
        f"`gamma_f03_pb.npz` (READ-ONLY, never refit; pure synthetic — zero "
        f"`.ttbin` reads, no such code path; no real data)",
        f"- seeds: `2026096401+idx` idx 0..239, stream `o1_blk:{{seed}}` "
        f"(FRESH interval — zero overlap with the S0.1 2026095601..2026095840 "
        f"family, no paired-block identity with S0.1; NO independence "
        f"claim); construction instance "
        f"{summary['construct_instance']} / trials {P1_MAX_TRIALS}",
        f"- decoder (F5, b2f verbatim): soft-marginal prior + v28 "
        f"`decode_error_domain_posterior` max_iter={P1_MAX_ITER} / streak "
        f"{P1_STREAK}, accept = `exact_match`; NO genie u1 / NO argmax "
        f"û1 / NO L1 code / NO refit; Stage-1 COLD on rows[0,200), Stage-2 "
        f"COLD full-matrix re-decode on rows[0,208)",
        f"- Stage-1 (F9): {summary['blocks_done']}/{P1_N_BLOCKS} run "
        f"(all 240 always run; bar-12 NEVER stops a run — report-only); "
        f"k = {summary['stage1_fails']}/{P1_N_BLOCKS}; FER_Stage1 = "
        f"{summary['fer_stage1']:.6f} (THIS ARM's own k; two instances "
        f"reported SEPARATELY — cross-instance pooling incl. 6+4 FORBIDDEN)",
        f"- Stage-2: rescue set = EXACTLY the Stage-1 non-success set "
        f"(attempted = {summary['attempted']} == k identity); rescued = "
        f"{summary['rescued']}; final F = {summary['final_fails']}/"
        f"{P1_N_BLOCKS} (F/240 = {summary['fer_final']:.6f})",
        f"- undetected: {summary['undetected']} (SEPARATE class: "
        f"syndrome-valid but x̂!=x; counts into k/F as fail; NEVER merged "
        f"into success; per-column, no pooling)",
        f"- iters: Stage-1 min {summary['iters_min_s1']} / max "
        f"{summary['iters_max_s1']}; Stage-2 min {summary['iters_min_s2']} "
        f"/ max {summary['iters_max_s2']}",
        f"- f_super baseline (F7) = (5·200+64)/852.544 = 1064/852.544 = "
        f"{summary['f_super_base']:.6f} (frozen V80 TRAIN/anchor basis, "
        f"content=852.544 b; DISTINCT line — NEVER quoted as f_eff)",
        f"- f_super worst-case (F7) = (5·208+64)/852.544 = 1104/852.544 = "
        f"{summary['f_super_full']:.6f} (by construction ≤1.3, NOT a "
        f"science gate; NEVER quoted as f_eff)",
        f"- E[leak] (F7) = 1064+40·r = {summary['e_leak']:.2f} b "
        f"(r=#rescued/240 = {summary['trigger_rate']:.6f}, this arm)",
        f"- f_exp (F7) = E[leak]/852.544 = {summary['f_exp']:.6f} "
        f"(this arm's blended basis; single frozen basis — no second "
        f"basis computed)",
        f"- f_eff (F7) = f_exp + 4.785675·(F/240) = "
        f"{summary['f_eff']:.6f} (this arm's final F)",
        f"- headroom = 1108.31−E[leak] = {summary['headroom']:.2f} b "
        f"(gate (c) needs ≥21.5 b ⇔ r ≤ 57.0%)",
        f"- N_req = {summary['n_req']} report-only (packet F8; zero-failure "
        f"rule relevant only if F=0; no certifiability claim here)",
        f"- wall: {summary['elapsed_s']:.1f} s / cap "
        f"{P1_WALL_CAP_S} s per arm BOTH stages combined, one window "
        f"(batch ceiling {P1_BATCH_CEILING_S} s, tallied in the "
        f"exploration log); per-block mean {summary['wall_mean_s']:.2f} s; "
        f"per-decode cap {P1_PER_DECODE_CAP_S} s terminal; peak RSS "
        f"{summary['rss_gib']:.3f} GiB (cap {P1_RSS_CAP_GIB} GiB); "
        f"{P1_CPUS} CPU; unspent budget != authorization",
        f"- bar-12 context (REPORT-ONLY, F9): {summary['route_ctx']}; "
        f"never stops a run, never adjudicates a route, never trims "
        f"the Stage-2 set",
        f"- S0.1-anchor reference (mechanism context ONLY, per-instance "
        f"columns, NOT paired identity, NOT prediction): S01-R1 79/240 + "
        f"S01-R2 119/240",
        f"- claim ceiling (packet §9): {CLAIM_CEILING}",
        f"- verdict: {summary['verdict']}",
        "",
    ]
    return "\n".join(lines)


def execute(*, root: str, arm: str, construct_fn: Callable | None,
            decode_fn: Callable | None, rescue_decode_fn: Callable | None,
            rank_fn: Callable | None, clock: Callable | None = None,
            rss_fn: Callable | None = None,
            writer: Callable | None = None) -> dict:
    """Run the frozen P1 Stage-1 rescue arm procedure (one arm/invocation).

    ALL FOUR of ``construct_fn`` / ``decode_fn`` / ``rescue_decode_fn`` /
    ``rank_fn`` are REQUIRED (explicit injection; any ``None`` refuses rc=2
    BEFORE any construction, root, decode, or write) — there is NO default
    production decoding path in this core; only ``run_execution`` (dual-flag
    CLI-gated) wires one, explicitly. Tests MUST pass explicit fakes. Zero
    decode happens before the F6 construction gate passes. Stage-2 covers
    EXACTLY the Stage-1 non-``success`` set (F9/F10); its per-block rows
    carry ``stage`` markers (``stage1`` / ``stage2-rescue``). No
    retry/resume/adaptive: the root must not exist; terminal states flush
    and return.
    """
    spec = parse_arm(arm)
    _check_root(root, arm)
    for name, fn in (("construct_fn", construct_fn),
                     ("decode_fn", decode_fn),
                     ("rescue_decode_fn", rescue_decode_fn),
                     ("rank_fn", rank_fn)):
        if fn is None:
            refuse(f"{name} required — no default production wiring "
                   f"(explicit injection only; packet §10(b))")
    clock = clock or time.monotonic
    rss_fn = rss_fn or _default_rss
    writer = writer or default_writer
    if os.path.exists(root):
        refuse(f"root not fresh: {root} (no resume/continue — fresh "
               f"additive per-arm root mandatory; packet §5)")
    construction = construct_and_pin(arm, construct_fn, rank_fn)
    base, full = construction["base"], construction["full"]

    rows: list[dict] = []
    stage1_fails = 0
    undetected = 0
    rescued = 0
    attempted = 0
    final_fails = 0
    t_start = clock()
    rss_peak_gib = 0.0

    def _summary(verdict: str) -> dict[str, Any]:
        n = len([r for r in rows if r.get("stage") == "stage1"])
        fer_s1 = (stage1_fails / P1_N_BLOCKS) if verdict == "COMPLETE" \
            else (stage1_fails / n if n else 0.0)
        fer_final = (final_fails / P1_N_BLOCKS) if verdict == "COMPLETE" \
            else 0.0
        elapsed = float(clock() - t_start)
        complete = verdict == "COMPLETE"
        it_s1 = [int(r["iters"]) for r in rows
                 if r.get("stage") == "stage1"
                 and isinstance(r.get("iters"), (int, np.integer))
                 and not isinstance(r.get("iters"), bool)]
        it_s2 = [int(r["iters"]) for r in rows
                 if r.get("stage") == "stage2-rescue"
                 and isinstance(r.get("iters"), (int, np.integer))
                 and not isinstance(r.get("iters"), bool)]
        route_ctx = (
            (f"route-ctx PASS (k<= {BAR12})" if stage1_fails <= BAR12
             else f"route-ctx FAIL (k> {BAR12})") + "; report-only"
            if complete else
            "route-ctx n/a (arm incomplete — no bar-12 reading)")
        e_leak = expected_leak_for(rescued)
        f_exp = f_exp_for(rescued)
        return {
            "arm": arm,
            "construct_instance": spec["instance"],
            "m_base": P1_M_BASE,
            "m_total": P1_M_TOTAL,
            "blocks_target": P1_N_BLOCKS,
            "blocks_done": n,
            "stage1_fails": stage1_fails,
            "k_over_240": f"{stage1_fails}/{P1_N_BLOCKS}",
            "fer_stage1": fer_s1,
            "attempted": attempted,
            "rescued": rescued,
            "final_fails": final_fails,
            "f_over_240": f"{final_fails}/{P1_N_BLOCKS}",
            "fer_final": fer_final,
            "trigger_rate": (rescued / P1_N_BLOCKS) if complete else 0.0,
            "undetected": undetected,
            "iters_min_s1": (min(it_s1) if it_s1 else None),
            "iters_max_s1": (max(it_s1) if it_s1 else None),
            "iters_min_s2": (min(it_s2) if it_s2 else None),
            "iters_max_s2": (max(it_s2) if it_s2 else None),
            "f_super_base": F_SUPER_BASE,
            "f_super_full": F_SUPER_FULL,
            "e_leak": e_leak,
            "f_exp": f_exp,
            "f_eff": f_eff_for(rescued, final_fails),
            "headroom": LEAK_CAP_BITS - e_leak,
            "n_req": (n_required_for(f_exp) if complete else None),
            "pins": construction["a208_pins"],
            "base_rank": construction["base_rank"],
            "seeds": f"2026096401+idx idx 0..{P1_N_BLOCKS - 1}",
            "stream": P1_STREAM,
            "channel_path": CHANNEL_NPZ,
            "decoder": (f"b2f verbatim + v28 decode_error_domain_posterior "
                        f"max_iter={P1_MAX_ITER}/streak {P1_STREAK}, "
                        f"exact_match accept; NO genie/argmax/L1; Stage-1 "
                        f"COLD rows[0,200), Stage-2 COLD rows[0,208)"),
            "budgets": {"wall_cap_s": P1_WALL_CAP_S,
                        "batch_ceiling_s": P1_BATCH_CEILING_S,
                        "per_decode_cap_s": P1_PER_DECODE_CAP_S,
                        "rss_cap_gib": P1_RSS_CAP_GIB,
                        "cpus": P1_CPUS},
            "elapsed_s": elapsed,
            "wall_mean_s": (elapsed / n) if n else 0.0,
            "rss_gib": float(rss_peak_gib),
            "route_ctx": route_ctx,
            "claim_ceiling": CLAIM_CEILING,
            "bar12_report_only": BAR12,
            "verdict": verdict,
        }

    def _flush(summary: dict[str, Any]) -> dict[str, Any]:
        writer(root, {
            f"P1S1_RESULT_{arm}.md": result_markdown(summary),
            "rows.json": json.dumps({"summary": summary, "rows": rows},
                                    indent=1, sort_keys=True, default=str),
            "block_accounting.csv": block_accounting_csv(rows)})
        return summary

    def _budgets_ok() -> str | None:
        if clock() - t_start > P1_WALL_CAP_S:
            return "INCOMPLETE-wall"
        try:
            rss_gib = float(rss_fn()) / (1024 ** 3)
        except Exception:  # noqa: BLE001 — probe failure never halts
            rss_gib = 0.0
        nonlocal rss_peak_gib
        rss_peak_gib = max(rss_peak_gib, rss_gib)
        if rss_gib >= P1_RSS_CAP_GIB:
            return "INCOMPLETE-budget"
        return None

    def _check_decode_out(out: Any, k: int, stage: str) -> None:
        pe = out.get("prior_entropy_bits")
        km = out.get("u1_mismatches")
        if isinstance(pe, bool) or not isinstance(pe, (int, float,
                                                       np.floating)):
            refuse(f"decode output missing numeric prior_entropy_bits "
                   f"({stage} block {k}; fail closed)")
        if isinstance(km, bool) or not isinstance(km, (int, np.integer)):
            refuse(f"decode output missing integer u1_mismatches "
                   f"({stage} block {k}; fail closed)")

    # -- Stage-1: COLD decode ALL 240 blocks on rows[0,200) (F9: no stop) --
    stage1_ok: list[bool] = []
    for k in range(P1_N_BLOCKS):
        term = _budgets_ok()
        if term is not None:
            return _flush(_summary(term))
        seed = block_seed(k)
        t0 = clock()
        try:
            out = decode_fn(base, seed)
        except Exception as exc:  # noqa: BLE001 — no-retry: retain + halt
            rows.append({"block_idx": k, "seed": seed, "stage": "stage1",
                         "iters": None, "wall_s": float(clock() - t0),
                         "decoded": 0, "failed": 1, "undetected": 0,
                         "prior_entropy_bits": None, "u1_mismatches": None,
                         "status": "error",
                         "error": f"{type(exc).__name__}: {exc}"})
            return _flush(_summary("INCOMPLETE-error"))
        dt = float(clock() - t0)
        if dt > P1_PER_DECODE_CAP_S:
            rows.append({"block_idx": k, "seed": seed, "stage": "stage1",
                         "iters": out.get("iterations"), "wall_s": dt,
                         "decoded": 0, "failed": 1, "undetected": 0,
                         "prior_entropy_bits": out.get(
                             "prior_entropy_bits"),
                         "u1_mismatches": out.get("u1_mismatches"),
                         "status": "overrun"})
            return _flush(_summary("INCOMPLETE-decode-cap"))
        _check_decode_out(out, k, "stage1")
        exact = bool(out.get("exact_match") is True)
        conv = bool(out.get("reconstruction_ok", False))
        und = bool(not exact and conv)
        if not exact:
            stage1_fails += 1  # F10: EVERY non-exact block counts into k
        if und:
            undetected += 1  # F10: SEPARATE count — never merged
        stage1_ok.append(exact)
        rows.append({
            "block_idx": k,
            "seed": seed,
            "stage": "stage1",
            "iters": out.get("iterations"),
            "wall_s": dt,
            "decoded": 1,
            "failed": 0 if exact else 1,
            "undetected": 1 if und else 0,
            "prior_entropy_bits": float(out.get("prior_entropy_bits")),
            "u1_mismatches": int(out.get("u1_mismatches")),
            "status": out.get("status"),
            "arm": arm,
            "construct_instance": spec["instance"],
        })
        # Retained partial evidence every block (F9: no early stop here —
        # the loop ALWAYS continues to 240 unless a terminal event fired).
        _flush(_summary("INCOMPLETE-wall"))

    # -- Stage-2: EXACTLY the Stage-1 non-success set, COLD full re-decode --
    rescue_idx = [k for k, ok in enumerate(stage1_ok) if not ok]
    attempted = len(rescue_idx)  # attempted == k identity (F9 gate)
    if attempted != stage1_fails:
        refuse(f"rescue-set identity drifted: attempted {attempted} != "
               f"Stage-1 k {stage1_fails} (packet F9)")
    for k in rescue_idx:
        term = _budgets_ok()
        if term is not None:
            return _flush(_summary(term))
        seed = block_seed(k)
        t0 = clock()
        try:
            out = rescue_decode_fn(full, seed)
        except Exception as exc:  # noqa: BLE001 — no-retry: retain + halt
            rows.append({"block_idx": k, "seed": seed,
                         "stage": "stage2-rescue", "iters": None,
                         "wall_s": float(clock() - t0), "decoded": 0,
                         "failed": 1, "undetected": 0,
                         "prior_entropy_bits": None, "u1_mismatches": None,
                         "status": "error",
                         "error": f"{type(exc).__name__}: {exc}"})
            return _flush(_summary("INCOMPLETE-error"))
        dt = float(clock() - t0)
        if dt > P1_PER_DECODE_CAP_S:
            rows.append({"block_idx": k, "seed": seed,
                         "stage": "stage2-rescue",
                         "iters": out.get("iterations"), "wall_s": dt,
                         "decoded": 0, "failed": 1, "undetected": 0,
                         "prior_entropy_bits": out.get(
                             "prior_entropy_bits"),
                         "u1_mismatches": out.get("u1_mismatches"),
                         "status": "overrun"})
            return _flush(_summary("INCOMPLETE-decode-cap"))
        _check_decode_out(out, k, "stage2-rescue")
        exact = bool(out.get("exact_match") is True)
        conv = bool(out.get("reconstruction_ok", False))
        und = bool(not exact and conv)
        if exact:
            rescued += 1
        else:
            final_fails += 1  # F10: unrescued non-exact counts into F
        if und:
            undetected += 1  # F10: SEPARATE count — never merged
        rows.append({
            "block_idx": k,
            "seed": seed,
            "stage": "stage2-rescue",
            "iters": out.get("iterations"),
            "wall_s": dt,
            "decoded": 1,
            "failed": 0 if exact else 1,
            "undetected": 1 if und else 0,
            "prior_entropy_bits": float(out.get("prior_entropy_bits")),
            "u1_mismatches": int(out.get("u1_mismatches")),
            "status": out.get("status"),
            "arm": arm,
            "construct_instance": spec["instance"],
        })
        _flush(_summary("INCOMPLETE-wall"))

    return _flush(_summary("COMPLETE"))


def _construct_r1(instance: int, trials: int) -> dict[str, Any]:
    """Production R1 constructor: frozen b2f F208 → o1 A208 @ 2026092001."""
    if int(instance) != ARMS["P1S1-R1"]:
        refuse(f"R1 instance {instance} != {ARMS['P1S1-R1']} (F1)")
    return b2f.construct_arm("F208", int(instance), int(trials))


def _construct_r2(instance: int, trials: int) -> dict[str, Any]:
    """Production R2 constructor: frozen b2g F208 → o1 A208 @ 2026092011."""
    if int(instance) != ARMS["P1S1-R2"]:
        refuse(f"R2 instance {instance} != {ARMS['P1S1-R2']} (F1)")
    return b2g.construct_arm("F208", int(instance), int(trials))


#: Frozen production constructors, keyed by arm (wired ONLY behind the
#: dual-flag CLI gate; never a default inside ``execute``).
PRODUCTION_CONSTRUCT: dict[str, Callable] = {
    "P1S1-R1": _construct_r1,
    "P1S1-R2": _construct_r2,
}


def run_execution(root: str, arm: str) -> int:
    """Production arm run — reached ONLY via the dual-flag CLI gate.

    Explicit wiring, one place: channel bound READ-ONLY through the frozen
    consumer; construction via the frozen same-instance A208 constructors;
    Stage-1 decode via the frozen b2f soft-marginal procedure on the m=200
    nested base; Stage-2 COLD full-matrix re-decode via the same frozen
    procedure on the m=208 full matrix; rank via the frozen PEG RREF. One
    arm per invocation; R1→R2 order and the single authorization live in
    the packet/prompt, not here.
    """
    spec = parse_arm(arm)
    bound = s2c.bind_empirical_bundle(CHANNEL_NPZ, CHANNEL_SOURCE)
    if bound.get("source") != CHANNEL_SOURCE:
        refuse("bound channel source label mismatch (fail closed)")

    def decode_fn(construction, seed, _b=bound):  # noqa: B023
        return b2f.decode_block_marginal(construction, seed, _b,
                                         P1_N, P1_M_BASE)

    def rescue_decode_fn(construction, seed, _b=bound):  # noqa: B023
        return b2f.decode_block_marginal(construction, seed, _b,
                                         P1_N, P1_M_TOTAL)

    summary = execute(root=root, arm=arm,
                      construct_fn=PRODUCTION_CONSTRUCT[spec["arm"]],
                      decode_fn=decode_fn,
                      rescue_decode_fn=rescue_decode_fn,
                      rank_fn=production_rank_fn)
    print(json.dumps({"arm": summary["arm"],
                      "construct_instance": summary["construct_instance"],
                      "verdict": summary["verdict"],
                      "blocks_done": summary["blocks_done"],
                      "k_over_240": summary["k_over_240"],
                      "rescued": summary["rescued"],
                      "attempted": summary["attempted"],
                      "f_over_240": summary["f_over_240"],
                      "trigger_rate": summary["trigger_rate"],
                      "e_leak": summary["e_leak"],
                      "f_exp": summary["f_exp"],
                      "f_eff": summary["f_eff"],
                      "headroom": summary["headroom"],
                      "undetected": summary["undetected"],
                      "elapsed_s": summary["elapsed_s"],
                      "route_ctx": summary["route_ctx"],
                      "root": root}, indent=1, sort_keys=True,
                     default=str))
    return 0


def dry_pins(*, channel_path: str | None = None,
             with_construct_pins: bool = False) -> dict:
    """Pre-grant DRY pins — ZERO decode by construction (no decode_fn here).

    Pins: frozen channel bound READ-ONLY (F4), seed literals (F3), budget
    literals (§5), root-family absence, arm table (F1), frozen accounting
    (F7/F8). With ``with_construct_pins`` the full zero-decode F6
    construction-pin run executes for BOTH instances (pre-grant Q5);
    otherwise the F6 base-rank check is reported as a rank==200 DRY
    PLACEHOLDER (PENDING) with its exact command.
    """
    channel = CHANNEL_NPZ if channel_path is None else str(channel_path)
    out: dict[str, Any] = {"mode": "dry-zero-decode", "decode_calls": 0,
                           "channel_path": channel}

    def pin(name: str, ok: bool, detail: Any) -> None:
        if not ok:
            refuse(f"dry pin FAILED: {name}: {detail}")
        out[name] = detail

    bound = s2c.bind_empirical_bundle(channel, CHANNEL_SOURCE)
    sidecar = Path(channel).parent / s2c.PB_SIDECAR_NAME
    if not sidecar.exists():
        refuse(f"dry pin FAILED: pb sidecar absent: {sidecar}")
    if bound.get("source") != CHANNEL_SOURCE:
        refuse("dry pin FAILED: bound channel source label mismatch")
    out["channel"] = {
        "source": bound.get("source"),
        "g1_shape": list(np.asarray(bound.get("g1")).shape),
        "g2_shape": list(np.asarray(bound.get("g2")).shape),
        "sidecar": str(sidecar),
        "access": "read-only via frozen bind_empirical_bundle; never "
                  "refit; pure synthetic (packet F4)",
    }

    first = block_seed(0)
    last = block_seed(P1_N_BLOCKS - 1)
    stream_ok = (stream_seed(first)
                 == common.v10_seed(f"o1_blk:{first}"))
    pin("seeds", P1_BLOCK_BASE == 2026096401 and P1_N_BLOCKS == 240
        and first == 2026096401 and last == 2026096640 and stream_ok
        and P1_STREAM == "o1_blk:{seed}",
        {"block_base": P1_BLOCK_BASE, "blocks": P1_N_BLOCKS,
         "first": first, "last": last, "stream": P1_STREAM,
         "stream_first_matches_frozen": bool(stream_ok)})

    pin("budget", P1_WALL_CAP_S == 3600 and P1_BATCH_CEILING_S == 7200
        and P1_PER_DECODE_CAP_S == 300 and P1_RSS_CAP_GIB == 2
        and P1_CPUS == 1 and BAR12 == 12,
        {"wall_cap_s_per_arm": P1_WALL_CAP_S,
         "batch_ceiling_s": P1_BATCH_CEILING_S,
         "per_decode_cap_s": P1_PER_DECODE_CAP_S,
         "rss_cap_gib": P1_RSS_CAP_GIB, "cpus": P1_CPUS,
         "bar12_report_only": BAR12})

    pin("arms", ARMS == {"P1S1-R1": 2026092001, "P1S1-R2": 2026092011}
        and P1_M_BASE == 200 and P1_M_TOTAL == 208
        and P1_M_BASE + P1_DELTA_M == P1_M_TOTAL and P1_M_TOTAL <= 208,
        {"arms": dict(ARMS), "m_base": P1_M_BASE, "delta_m": P1_DELTA_M,
         "m_total": P1_M_TOTAL, "hard_cap": 208,
         "reporting": "separate per instance; pooling incl. 6+4 FORBIDDEN"})

    pin("frozen_accounting",
        abs(F_SUPER_BASE - 1064 / CONTENT_BITS) < 1e-12
        and abs(F_SUPER_FULL - (5 * 208 + 64) / CONTENT_BITS) < 1e-12
        and LEAK_BASE_BITS == 1064 and LEAK_FULL_BITS == 1104,
        {"f_super_base": F_SUPER_BASE,
         "f_super_base_literal": F_SUPER_BASE_LITERAL,
         "f_super_full": F_SUPER_FULL,
         "f_super_full_literal": F_SUPER_FULL_LITERAL,
         "content_bits": CONTENT_BITS, "leak_base_bits": LEAK_BASE_BITS,
         "leak_full_bits": LEAK_FULL_BITS,
         "f_eff_slope": F_EFF_SLOPE, "leak_cap_bits": LEAK_CAP_BITS,
         "f_super_formula": "(5*208+64)/852.544 = 1104/852.544"})

    out["roots"] = {"family": P1_ROOT_PREFIX,
                    "family_exists": os.path.exists(P1_ROOT_PREFIX)}

    if with_construct_pins:
        measured: dict[str, Any] = {}
        for arm_name in ("P1S1-R1", "P1S1-R2"):
            gated = construct_and_pin(arm_name,
                                      PRODUCTION_CONSTRUCT[arm_name],
                                      production_rank_fn)
            measured[arm_name] = {
                "instance": gated["base"]["construct_instance"],
                "a208_pins": gated["a208_pins"],
                "base_rows": "rows[0,200)",
                "base_rank": gated["base_rank"],
                "base_rank_required": P1_M_BASE,
                "full_rows": "rows[0,208)",
                "full_m": gated["full"]["m"],
                "girth": "recorded-not-gated"}
        out["construction_pins"] = {
            "status": "MEASURED-DRY (zero decode)",
            "measured": measured}
        out["verdict"] = "DRY-PASS (zero decode; literal + construction pins)"
    else:
        out["construction_pins"] = {
            "status": "PENDING (rank==200 dry placeholder — NOT run in "
                       "this pass; zero decode either way)",
            "gates": {"a208_four_cycles": 0, "a208_rank": P1_M_TOTAL,
                      "a208_twice_identical": True,
                      "base_rows": "rows[0,200)",
                      "base_rank_required": P1_M_BASE,
                      "full_rows": "rows[0,208)",
                      "girth": "recorded-not-gated"},
            "command": ("PYTHONPATH=<repo> .venv/bin/python -m "
                        "comparison_bench.src.comparison_bench.cli."
                        "p1_stage1_runner --dry --construct-pins")}
        out["verdict"] = ("DRY-PASS (zero decode; literal pins; F6 "
                          "construction pins PENDING)")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="P1 Stage-1 rescue thin runner (one arm per invocation; "
                    "--dry is the zero-decode pre-grant path; production "
                    "decoding requires BOTH execution flags + every "
                    "frozen literal).")
    ap.add_argument("--dry", action="store_true", default=False)
    ap.add_argument("--construct-pins", action="store_true", default=False)
    ap.add_argument("--execute-real", action="store_true", default=False)
    ap.add_argument("--execution-authorized", action="store_true",
                    default=False)
    ap.add_argument("--arm", default="")
    ap.add_argument("--m-base", type=int, default=None)
    ap.add_argument("--m-total", type=int, default=None)
    ap.add_argument("--instance", type=int, default=None)
    ap.add_argument("--blocks", type=int, default=None)
    ap.add_argument("--seed-base", type=int, default=None)
    ap.add_argument("--root", default="")
    args = ap.parse_args(argv)

    if args.dry:
        if args.execute_real or args.execution_authorized:
            refuse("--dry cannot be combined with execution flags "
                   "(rc=2 pre-anything)")
        if args.arm or args.root or args.m_base is not None:
            refuse("--dry takes no arm/root/m arguments (batch-wide "
                   "literal pins; rc=2 pre-anything)")
        result = dry_pins(with_construct_pins=args.construct_pins)
        print(json.dumps(result, indent=1, sort_keys=True, default=str))
        return 0

    # Dual-flag gate FIRST: refuse rc=2 BEFORE any bind/construct/root/write.
    if not args.execute_real:
        refuse("refusing: --execute-real missing (rc=2 pre-anything; "
               "use --dry for the zero-decode Pre-EXECUTE pins)")
    if not args.execution_authorized:
        refuse("refusing: --execution-authorized missing (rc=2 "
               "pre-anything; packet §10: unfilled grant = unauthorized)")
    if args.construct_pins:
        refuse("--construct-pins is a --dry-only mode (rc=2 pre-anything)")
    spec = parse_arm(args.arm)
    if args.m_base != P1_M_BASE:
        refuse(f"--m-base must be the frozen {P1_M_BASE} (got "
               f"{args.m_base}; packet F2 — nested leading-200, no "
               f"operating-point selection)")
    if args.m_total != P1_M_TOTAL or P1_M_TOTAL > 208:
        refuse(f"--m-total must be the frozen {P1_M_TOTAL}<=208 (got "
               f"{args.m_total}; packet F2 HARD cap)")
    if args.instance != spec["instance"]:
        refuse(f"--instance must be {spec['instance']} for {args.arm} "
               f"(got {args.instance}; packet F1)")
    if args.blocks != P1_N_BLOCKS:
        refuse(f"--blocks must be the frozen {P1_N_BLOCKS} "
               f"(got {args.blocks}; packet F3/F9 — no early stop)")
    if args.seed_base != P1_BLOCK_BASE:
        refuse(f"--seed-base must be the frozen literal {P1_BLOCK_BASE} "
               f"(got {args.seed_base}; packet F3)")
    if not args.root:
        refuse(f"root required: fresh additive {P1_ROOT_PREFIX}"
               f"{args.arm}_<uuid8> (packet §5)")
    _check_root(args.root, args.arm)  # rc=2 BEFORE any bind/construct
    return run_execution(root=args.root, arm=args.arm)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
