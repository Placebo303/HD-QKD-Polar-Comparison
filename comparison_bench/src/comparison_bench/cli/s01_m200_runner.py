"""S0.1 soft-marginal m=200 FER-probe thin runner (EXPLORE code — NOT execution).

Frozen contract: ``docs/research_cycles/V80-NBLDPC-JAN21/S0_1_M200_PACKET.md``
(§§1–11; Acceptance ID ``G-S01M200``) + ``S0_1_M200_PROMPT.md``. This module
is the packet §10(b) execution surface; implementing it carries NO track gate
(AGENTS §1.2 matrix — implementation-only). The track gate hangs on the FIRST
SYNTHETIC EXECUTION, which requires the packet §10 authorization block signed
FIRST. This prompt/module authorizes any execution = 0.

Safety shape (why this ONE additive module exists):

- **NO default production decoding.** ``execute()`` REFUSES to run unless an
  explicit ``construct_fn``, ``decode_fn`` AND ``rank_fn`` are injected —
  there is no silent production wiring anywhere in the execution core. The
  CLI reaches a production decode ONLY behind BOTH flags
  ``--execute-real`` AND ``--execution-authorized`` plus every frozen
  literal matching (F1–F3); a bare invocation refuses rc=2 BEFORE any bind,
  construct, root or write. ``--dry`` is the only pre-grant path and builds
  no decode function at all (zero decode by construction).
- **No real-data path anywhere** (F4): the ONLY channel is the frozen
  synthetic ``gamma_f03.npz`` + ``gamma_f03_pb.npz`` sibling under
  ``docs/research_cycles/V80-NBLDPC-JAN21/``, bound READ-ONLY through the
  frozen consumer ``s2c.bind_empirical_bundle`` (shape/normalization gates;
  never refit). No ``.ttbin`` read path exists (no such import, path, or
  read anywhere here).
- **Frozen procedure F1–F10**: exactly two arms — ``S01-R1`` construct
  instance 2026092001 / ``S01-R2`` construct instance 2026092011 — reported
  SEPARATELY; cross-instance pooling FORBIDDEN (incl. any 6+4 sum). m=200
  single point = nested leading-200 ``rows[0,200)`` of the SAME-instance
  frozen A208 matrix (never an A200 construct; rescue rows ``rows[200,208)``
  never disclosed; no Stage-2 exists here). 240 paired blocks, seeds
  ``2026095601+idx`` idx 0..239, stream ``o1_blk:{seed}`` (paired-frame
  comparison with O1R/P0/L1B/b2e/b2f/b2g/X1 — NO independence claim).
  Decoder/accept is the b2f lineage VERBATIM via the frozen
  ``b2f.decode_block_marginal`` (soft-marginal prior + v28
  ``decode_error_domain_posterior`` max_iter 300 / streak 3,
  ``exact_match`` accept; NO genie u1, NO argmax û1, NO L1 code, NO refit).
- **F9 no early stop**: ALL 240 blocks always run; bar-12 NEVER stops a
  run — it is a report-only route-context line and adjudicates nothing.
- **F10 class separation**: ``exact_match is True`` = success; anything
  else counts into k (fail); a syndrome-valid-but-mismatched block is
  counted SEPARATELY as ``undetected`` and is NEVER merged into success.
- **F7 accounting**: ``f_super = (5*200+64)/852.544 = 1064/852.544``
  (frozen V80 anchor basis, content = 852.544 b, = 1.24803);
  ``f_eff = f_super + 4.785675*FER`` on this arm's OWN k. f_super is NEVER
  quoted as f_eff (FER>0); no second basis is ever computed; ``N_req=277``
  is report-only.
- **Budget (§5)**: wall ≤ 3600 s/arm; batch ceiling ≤ 7200 s (batch-level,
  tallied in the exploration log, not here); per-decode ≤ 300 s (overrun =
  TERMINAL, the block counts fail, no continuation); RSS < 2 GiB; 1 CPU.
  NO retry / resume / adaptive: wall-partial ⇒ ``INCOMPLETE-wall`` retained
  forever; the root must be fresh (existing root refuses), so resume is
  structurally impossible.
- **Roots**: fresh additive ``workspace/S0_1/<arm>_<uuid8>/`` ONLY;
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
    "S01_N", "S01_M", "S01_A208_M", "S01_N_BLOCKS", "S01_BLOCK_BASE",
    "S01_STREAM", "S01_MAX_TRIALS", "S01_MAX_ITER", "S01_STREAK",
    "ARMS", "S01_WALL_CAP_S", "S01_BATCH_CEILING_S", "S01_PER_DECODE_CAP_S",
    "S01_RSS_CAP_GIB", "S01_CPUS", "S01_ROOT_PREFIX", "FORBIDDEN_ROOT_PARTS",
    "CHANNEL_NPZ", "CHANNEL_SOURCE", "CONTENT_BITS", "LEAK_BITS",
    "F_SUPER", "F_SUPER_LITERAL", "F_EFF_SLOPE", "F_SUPER_MAX", "N_REQ",
    "BAR12", "CSV_COLUMNS", "CLAIM_CEILING",
    "Refusal", "refuse", "parse_arm", "block_seed", "stream_seed",
    "fail_bar", "f_super_for", "f_eff_for", "n_required_frozen",
    "production_rank_fn", "construct_and_pin", "_check_root",
    "default_writer", "block_accounting_csv", "result_markdown",
    "execute", "run_execution", "dry_pins", "main",
]

#: Frozen single-code length (o1.O1_N; content-basis denominator 1024·H).
S01_N = 1024
#: Frozen m point — the ONLY one (packet F2).
S01_M = 200
#: Frozen parent parity-check rows of the same-instance A208 matrix (F2/F6).
S01_A208_M = 208
#: Frozen campaign width: 240 paired blocks per arm, both arms always full
#: unless a terminal budget event fires (F3/F9).
S01_N_BLOCKS = 240
#: Frozen literal block-seed base (packet F3).
S01_BLOCK_BASE = 2026095601
#: Frozen literal stream template (packet F3; b2f/O1R/P0/L1B/X1 pairing).
S01_STREAM = "o1_blk:{seed}"
#: Frozen constructor trials (b2f/o1 ARMS construction pins).
S01_MAX_TRIALS = 20
#: Frozen decoder cap (packet F5; v28 streak default 3).
S01_MAX_ITER = 300
#: Frozen decoder streak (packet F5; recorded — the frozen kernel default).
S01_STREAK = 3
#: Frozen arms → construct instance (packet F1; separate report, NO pooling).
ARMS: dict[str, int] = {"S01-R1": 2026092001, "S01-R2": 2026092011}
#: Frozen per-arm wall budget (packet §5; = P1 §7 per-arm cap).
S01_WALL_CAP_S = 3600
#: Frozen batch total ceiling (packet §5; tallied batch-level in the log).
S01_BATCH_CEILING_S = 7200
#: Frozen per-decode terminal cap (packet §5: overrun = terminal, block
#: counts fail, no continuation).
S01_PER_DECODE_CAP_S = 300
#: Frozen RSS cap (packet §5).
S01_RSS_CAP_GIB = 2
#: Frozen CPU budget (packet §5).
S01_CPUS = 1
#: Fresh additive machine-root family (packet §5).
S01_ROOT_PREFIX = "workspace/S0_1/"
#: Roots this executor never writes under (packet §5/§8).
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")
#: Frozen 2M synthetic channel, READ-ONLY, never refit (packet F4).
CHANNEL_NPZ = "docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz"
#: Frozen channel source label (frozen 2M bundle; s2c.SOURCE_DEFAULT).
CHANNEL_SOURCE = "2M"
#: Frozen content basis (V80_BASELINE §2 anchor: 1024·0.83256272 b).
CONTENT_BITS = 852.544
#: Frozen leak at m=200 incl. 64-bit tag (packet F7).
LEAK_BITS = 5 * S01_M + 64  # = 1064
#: Frozen f_super (packet F7): 1064/852.544 = 1.24803…
F_SUPER = LEAK_BITS / CONTENT_BITS
#: Frozen 5-decimal restatement used for the N_req arithmetic (packet F7/F8).
F_SUPER_LITERAL = "1.24803"
#: Frozen f_eff slope (packet F7; V80_BASELINE §2).
F_EFF_SLOPE = 4.785675
#: Frozen efficiency bar (packet F7 gate (b); by construction at frozen m).
F_SUPER_MAX = 1.3
#: Frozen report-only zero-failure rule N_req (packet F8).
N_REQ = 277
#: Frozen bar-12 value via the frozen o1 rule (floor(240·0.05) = 12) —
#: REPORT-ONLY route context; NEVER a stop, NEVER an adjudication (F9).
BAR12 = o1.fail_bar(S01_N_BLOCKS)
#: Frozen per-block accounting columns (packet §3).
CSV_COLUMNS = ["block_idx", "seed", "iters", "wall_s", "decoded", "failed",
               "undetected", "prior_entropy_bits", "u1_mismatches"]
#: Frozen claim ceiling (packet §9).
CLAIM_CEILING = (
    "synthetic paired-frame m=200 soft-marginal efficiency probe ONLY "
    "(per-instance k/240 + frozen-basis f_super/f_eff + iters/wall + "
    "undetected single count) as the P1 Stage-1 measured anchor; NOT SKR, "
    "NOT qualification, NOT route adjudication, NOT operating-point "
    "selection, NOT real-data FER, NOT a certifiable/literature-comparable "
    "f_eff<=1.3 sentence, NOT publication material; key-eligible "
    "200/276/364 cited-not-consumed; any later citation MUST list both "
    "instances separately (pooling incl. 6+4 FORBIDDEN)"
)


class Refusal(SystemExit):
    """rc=2 pre-write refusal (unauthorized / invalid / gate-blocked)."""


def refuse(reason: str) -> "Any":
    print(f"S01-REFUSAL rc=2: {reason}", file=sys.stderr)
    raise Refusal(2)


def parse_arm(arm: str) -> dict[str, Any]:
    """Parse ``S01-R1``/``S01-R2`` against the frozen two-arm table (F1)."""
    if arm not in ARMS:
        refuse(f"unknown arm {arm!r} (frozen exactly: S01-R1 | S01-R2; "
               f"packet F1 — two arms, separate report, NO pooling)")
    return {"arm": str(arm), "instance": int(ARMS[arm])}


def block_seed(idx: int) -> int:
    """Frozen literal block seed: 2026095601+idx, idx=0..239 (F3)."""
    if isinstance(idx, bool) or not isinstance(idx, int) \
            or not 0 <= int(idx) < S01_N_BLOCKS:
        refuse(f"block idx must be in 0..{S01_N_BLOCKS - 1} (got {idx!r})")
    return S01_BLOCK_BASE + int(idx)


def stream_seed(seed: int) -> int:
    """Frozen stream derivation (o1.stream_seed, read-only reuse): F3."""
    return o1.stream_seed(int(seed))


def fail_bar(n_blocks: int) -> int:
    """Derived bar via the frozen o1 rule — REPORT-ONLY here (F9)."""
    return o1.fail_bar(int(n_blocks))


def f_super_for(m: int = S01_M) -> float:
    """f_super = (5m+64)/852.544 on the frozen anchor basis (F7)."""
    return float(5 * int(m) + 64) / CONTENT_BITS


def f_eff_for(fer: float) -> float:
    """f_eff = f_super + 4.785675·FER, this arm's OWN FER (F7)."""
    return F_SUPER + F_EFF_SLOPE * float(fer)


def n_required_frozen() -> int:
    """Frozen report-only N_req arithmetic pin (packet F8): must be 277."""
    value = math.ceil(3.0 * F_EFF_SLOPE
                      / (F_SUPER_MAX - float(F_SUPER_LITERAL)))
    if int(value) != N_REQ:
        refuse(f"frozen N_req arithmetic drifted: computed {value} != "
               f"{N_REQ} (packet F8)")
    return int(value)


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
    ``rank == 200`` REQUIRED else STOP-BLOCKED. Returns the base-code dict
    (m=200; rescue rows ``rows[200,208)`` EXCLUDED — never disclosed).
    ``construct_fn`` convention: ``(instance, trials) -> code dict``.
    ``rank_fn`` convention: ``(dense rows) -> int`` (explicit injection).
    """
    spec = parse_arm(arm)
    instance = spec["instance"]
    try:
        code_a = construct_fn(instance, S01_MAX_TRIALS)
        code_b = construct_fn(instance, S01_MAX_TRIALS)
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
    if int(code_a.get("n", -1)) != S01_N or int(code_a.get("m", -1)) \
            != S01_A208_M:
        refuse(f"construction (n, m) != ({S01_N}, {S01_A208_M}) ({arm}; "
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
    if a208_rank != S01_A208_M:
        refuse(f"{arm} A208 rank {a208_rank} != {S01_A208_M} "
               f"(STOP-BLOCKED; F6)")
    field = GF2mField.create(s2.Q)
    dense = peg.sparse_to_dense(sa, S01_N, S01_A208_M, field)
    try:
        base_rank = int(rank_fn(dense[:S01_M]))
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed pre-decode
        refuse(f"base-rank evaluation failed ({arm}; STOP-BLOCKED; F6): "
               f"{type(exc).__name__}: {exc}")
    if base_rank != S01_M:
        refuse(f"{arm} base rank(rows[0,200)) = {base_rank} != {S01_M} "
               f"(STOP-BLOCKED; packet F6 — rank==200 REQUIRED)")
    base_triples = [(int(r), int(c), int(v)) for r, c, v in sa
                    if int(r) < S01_M]  # rescue rows rows[200,208) EXCLUDED
    return {
        "n": S01_N,
        "m": S01_M,
        "triples": base_triples,
        "status": "ok",
        "family": code_a.get("family"),
        "lambda_edge": code_a.get("lambda_edge"),
        "rho_edge": code_a.get("rho_edge"),
        "source_arm": "A208",
        "construct_instance": instance,
        "nested_base": ("rows[0,200) of the same-instance frozen A208 "
                        "matrix (nested leading-200; NOT an A200 construct; "
                        "rescue rows[200,208) never disclosed; no warm "
                        "start / no Stage-2 in this probe)"),
        "a208_pins": {"four_cycles": fc, "rank": a208_rank,
                      "girth": girth, "twice_identical": True},
        "base_rank": base_rank,
        "measured_girth": girth,
    }


def _check_root(root: str, arm: str) -> None:
    if not root:
        refuse(f"root required (fresh additive {S01_ROOT_PREFIX}"
               f"<arm>_<uuid8>)")
    if not str(root).startswith(S01_ROOT_PREFIX):
        refuse(f"root must be fresh additive {S01_ROOT_PREFIX}"
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
    """Per-arm ``S01_RESULT_<arm>_m200.md`` body (packet §3)."""
    pins = summary["pins"]
    lines = [
        f"# S0.1 m=200 result — {summary['arm']} (EXPLORE synthetic, RAW)",
        "",
        f"- arm: `{summary['arm']}`; construct instance "
        f"{summary['construct_instance']} (recorded girth "
        f"{pins['girth']}); base code = nested leading-200 rows[0,200) of "
        f"THAT instance's A208 (NOT an A200 construct; rescue rows "
        f"rows[200,208) never disclosed; no Stage-2/warm-start here)",
        f"- pins (F6): A208 fc={pins['four_cycles']} + rank {pins['rank']} "
        f"+ twice-identical GATED; base rank(rows[0,200))="
        f"{summary['base_rank']} REQUIRED==200; girth {pins['girth']} "
        f"recorded-not-gated",
        f"- channel: `{summary['channel_path']}` + sibling "
        f"`gamma_f03_pb.npz` (READ-ONLY, never refit; pure synthetic — zero "
        f"`.ttbin` reads, no such code path; no real data)",
        f"- seeds: `2026095601+idx` idx 0..239, stream `o1_blk:{{seed}}` "
        f"(paired-frame comparison with O1R/P0/L1B/b2e/b2f/b2g/X1; NO "
        f"independence claim); construction instance "
        f"{summary['construct_instance']} / trials {S01_MAX_TRIALS}",
        f"- decoder (F5, b2f verbatim): soft-marginal prior + v28 "
        f"`decode_error_domain_posterior` max_iter={S01_MAX_ITER} / streak "
        f"{S01_STREAK}, accept = `exact_match`; NO genie u1 / NO argmax "
        f"û1 / NO L1 code / NO refit",
        f"- blocks (F9): {summary['blocks_done']}/{S01_N_BLOCKS} run "
        f"(all 240 always run; bar-12 NEVER stops a run — report-only)",
        f"- k = {summary['failures']}/{S01_N_BLOCKS}; FER = "
        f"{summary['fer']:.6f} (THIS ARM's own k; two instances reported "
        f"SEPARATELY — cross-instance pooling incl. 6+4 FORBIDDEN)",
        f"- undetected: {summary['undetected']} (SEPARATE class: "
        f"syndrome-valid but x̂!=x; counts into k as fail; NEVER merged "
        f"into success)",
        f"- iters: min {summary['iters_min']} / max {summary['iters_max']}",
        f"- f_super (F7) = (5·200+64)/852.544 = 1064/852.544 = "
        f"{summary['f_super']:.6f} (frozen V80 TRAIN/anchor basis, "
        f"content=852.544 b; DISTINCT line — NEVER quoted as f_eff)",
        f"- f_eff (F7) = f_super + 4.785675·FER = "
        f"{summary['f_eff']:.6f} (this arm's FER; single frozen basis — "
        f"no second basis computed)",
        f"- N_req = {N_REQ} report-only (packet F8; zero-failure rule "
        f"relevant only if k=0; no certifiability claim here)",
        f"- wall: {summary['elapsed_s']:.1f} s / cap "
        f"{S01_WALL_CAP_S} s per arm (batch ceiling "
        f"{S01_BATCH_CEILING_S} s, tallied in the exploration log); "
        f"per-block mean {summary['wall_mean_s']:.2f} s; per-decode cap "
        f"{S01_PER_DECODE_CAP_S} s terminal; peak RSS "
        f"{summary['rss_gib']:.3f} GiB (cap {S01_RSS_CAP_GIB} GiB); "
        f"{S01_CPUS} CPU; unspent budget != authorization",
        f"- bar-12 context (REPORT-ONLY, F9): {summary['route_ctx']}; "
        f"never stops a run, never adjudicates a route",
        f"- S0.1-gate: {summary['gate_contribution']}",
        f"- claim ceiling (packet §9): {CLAIM_CEILING}",
        f"- verdict: {summary['verdict']}",
        "",
    ]
    return "\n".join(lines)


def execute(*, root: str, arm: str, construct_fn: Callable | None,
            decode_fn: Callable | None, rank_fn: Callable | None,
            clock: Callable | None = None, rss_fn: Callable | None = None,
            writer: Callable | None = None) -> dict:
    """Run the frozen S0.1 arm procedure under ``root`` (one arm/invocation).

    ALL THREE of ``construct_fn`` / ``decode_fn`` / ``rank_fn`` are REQUIRED
    (explicit injection; ``None`` refuses rc=2 BEFORE any construction,
    root, or write) — there is NO default production decoding path in this
    core; only ``run_execution`` (dual-flag CLI-gated) wires one, explicitly.
    Tests MUST pass explicit fakes. Zero decode happens before the F6
    construction gate passes. No resume/retry/adaptive: the root must not
    exist; terminal states flush and return.
    """
    spec = parse_arm(arm)
    _check_root(root, arm)
    for name, fn in (("construct_fn", construct_fn),
                     ("decode_fn", decode_fn), ("rank_fn", rank_fn)):
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

    rows: list[dict] = []
    failures = 0
    undetected = 0
    t_start = clock()
    rss_peak_gib = 0.0

    def _summary(verdict: str) -> dict[str, Any]:
        n = len(rows)
        fer = (failures / n) if n else 0.0
        elapsed = float(clock() - t_start)
        complete = verdict == "COMPLETE"
        iters_seen = [int(r["iters"]) for r in rows
                      if isinstance(r.get("iters"), (int, np.integer))
                      and not isinstance(r.get("iters"), bool)]
        route_ctx = (
            (f"route-ctx PASS (k<= {BAR12})" if failures <= BAR12
             else f"route-ctx FAIL (k> {BAR12})") + "; report-only"
            if complete else
            "route-ctx n/a (arm incomplete — no bar-12 reading)")
        gate = (f"PASS-component: {n}/{S01_N_BLOCKS} complete, "
                f"non-wall-partial (both arms must reach this for "
                f"S0.1-gate PASS)" if complete else
                f"NOT satisfied: {n}/{S01_N_BLOCKS} (gate needs 240/240 "
                f"complete; 10/240 extrapolation stays FORBIDDEN until "
                f"S0.1-gate PASS)")
        return {
            "arm": arm,
            "construct_instance": spec["instance"],
            "m": S01_M,
            "blocks_target": S01_N_BLOCKS,
            "blocks_done": n,
            "failures": failures,
            "k_over_240": f"{failures}/{S01_N_BLOCKS}",
            "fer": fer,
            "undetected": undetected,
            "iters_min": (min(iters_seen) if iters_seen else None),
            "iters_max": (max(iters_seen) if iters_seen else None),
            "f_super": F_SUPER,
            "f_eff": f_eff_for(fer),
            "n_req_report_only": N_REQ,
            "pins": construction["a208_pins"],
            "base_rank": construction["base_rank"],
            "seeds": f"2026095601+idx idx 0..{S01_N_BLOCKS - 1}",
            "stream": S01_STREAM,
            "channel_path": CHANNEL_NPZ,
            "decoder": (f"b2f verbatim + v28 decode_error_domain_posterior "
                        f"max_iter={S01_MAX_ITER}/streak {S01_STREAK}, "
                        f"exact_match accept; NO genie/argmax/L1"),
            "budgets": {"wall_cap_s": S01_WALL_CAP_S,
                        "batch_ceiling_s": S01_BATCH_CEILING_S,
                        "per_decode_cap_s": S01_PER_DECODE_CAP_S,
                        "rss_cap_gib": S01_RSS_CAP_GIB,
                        "cpus": S01_CPUS},
            "elapsed_s": elapsed,
            "wall_mean_s": (elapsed / n) if n else 0.0,
            "rss_gib": float(rss_peak_gib),
            "route_ctx": route_ctx,
            "gate_contribution": gate,
            "claim_ceiling": CLAIM_CEILING,
            "bar12_report_only": BAR12,
            "verdict": verdict,
        }

    def _flush(summary: dict[str, Any]) -> dict[str, Any]:
        writer(root, {
            f"S01_RESULT_{arm}_m200.md": result_markdown(summary),
            "rows.json": json.dumps({"summary": summary, "rows": rows},
                                    indent=1, sort_keys=True, default=str),
            "block_accounting.csv": block_accounting_csv(rows)})
        return summary

    for k in range(S01_N_BLOCKS):
        if clock() - t_start > S01_WALL_CAP_S:
            return _flush(_summary("INCOMPLETE-wall"))
        try:
            rss_gib = float(rss_fn()) / (1024 ** 3)
        except Exception:  # noqa: BLE001 — probe failure never halts
            rss_gib = 0.0
        rss_peak_gib = max(rss_peak_gib, rss_gib)
        if rss_gib >= S01_RSS_CAP_GIB:
            return _flush(_summary("INCOMPLETE-budget"))
        seed = block_seed(k)
        t0 = clock()
        try:
            out = decode_fn(construction, seed)
        except Exception as exc:  # noqa: BLE001 — no-retry: retain + halt
            rows.append({"block_idx": k, "seed": seed, "iters": None,
                         "wall_s": float(clock() - t0), "decoded": 0,
                         "failed": 1, "undetected": 0,
                         "prior_entropy_bits": None, "u1_mismatches": None,
                         "status": "error",
                         "error": f"{type(exc).__name__}: {exc}"})
            return _flush(_summary("INCOMPLETE-error"))
        dt = float(clock() - t0)
        if dt > S01_PER_DECODE_CAP_S:
            rows.append({"block_idx": k, "seed": seed,
                         "iters": out.get("iterations"), "wall_s": dt,
                         "decoded": 0, "failed": 1, "undetected": 0,
                         "prior_entropy_bits": out.get(
                             "prior_entropy_bits"),
                         "u1_mismatches": out.get("u1_mismatches"),
                         "status": "overrun"})
            return _flush(_summary("INCOMPLETE-decode-cap"))
        pe = out.get("prior_entropy_bits")
        km = out.get("u1_mismatches")
        if isinstance(pe, bool) or not isinstance(pe, (int, float,
                                                       np.floating)):
            refuse(f"decode output missing numeric prior_entropy_bits "
                   f"(block {k}; fail closed)")
        if isinstance(km, bool) or not isinstance(km, (int, np.integer)):
            refuse(f"decode output missing integer u1_mismatches "
                   f"(block {k}; fail closed)")
        exact = bool(out.get("exact_match") is True)
        conv = bool(out.get("reconstruction_ok", False))
        und = bool(not exact and conv)
        if not exact:
            failures += 1  # F10: EVERY non-exact block counts into k
        if und:
            undetected += 1  # F10: SEPARATE count — never merged
        rows.append({
            "block_idx": k,
            "seed": seed,
            "iters": out.get("iterations"),
            "wall_s": dt,
            "decoded": 1,
            "failed": 0 if exact else 1,
            "undetected": 1 if und else 0,
            "prior_entropy_bits": float(pe),
            "u1_mismatches": int(km),
            "status": out.get("status"),
            "arm": arm,
            "construct_instance": spec["instance"],
        })
        # Retained partial evidence every block (F9: no early stop here —
        # the loop ALWAYS continues to 240 unless a terminal event fired).
        _flush(_summary("INCOMPLETE-wall"))

    return _flush(_summary("COMPLETE"))


def _construct_r1(instance: int, trials: int) -> dict[str, Any]:
    """Production R1 constructor: frozen b2f F208 → o1 A208 @ 2026092001."""
    if int(instance) != ARMS["S01-R1"]:
        refuse(f"R1 instance {instance} != {ARMS['S01-R1']} (F1)")
    return b2f.construct_arm("F208", int(instance), int(trials))


def _construct_r2(instance: int, trials: int) -> dict[str, Any]:
    """Production R2 constructor: frozen b2g F208 → o1 A208 @ 2026092011."""
    if int(instance) != ARMS["S01-R2"]:
        refuse(f"R2 instance {instance} != {ARMS['S01-R2']} (F1)")
    return b2g.construct_arm("F208", int(instance), int(trials))


#: Frozen production constructors, keyed by arm (wired ONLY behind the
#: dual-flag CLI gate; never a default inside ``execute``).
PRODUCTION_CONSTRUCT: dict[str, Callable] = {
    "S01-R1": _construct_r1,
    "S01-R2": _construct_r2,
}


def run_execution(root: str, arm: str) -> int:
    """Production arm run — reached ONLY via the dual-flag CLI gate.

    Explicit wiring, one place: channel bound READ-ONLY through the frozen
    consumer; construction via the frozen same-instance A208 constructors;
    decode via the frozen b2f soft-marginal procedure on the m=200 base
    code; rank via the frozen PEG RREF. One arm per invocation; R1→R2
    order and the single authorization live in the packet/prompt, not here.
    """
    spec = parse_arm(arm)
    bound = s2c.bind_empirical_bundle(CHANNEL_NPZ, CHANNEL_SOURCE)
    if bound.get("source") != CHANNEL_SOURCE:
        refuse("bound channel source label mismatch (fail closed)")

    def decode_fn(construction, seed, _b=bound):  # noqa: B023
        return b2f.decode_block_marginal(construction, seed, _b,
                                         S01_N, S01_M)

    summary = execute(root=root, arm=arm,
                      construct_fn=PRODUCTION_CONSTRUCT[spec["arm"]],
                      decode_fn=decode_fn, rank_fn=production_rank_fn)
    print(json.dumps({"arm": summary["arm"],
                      "construct_instance": summary["construct_instance"],
                      "verdict": summary["verdict"],
                      "blocks_done": summary["blocks_done"],
                      "k_over_240": summary["k_over_240"],
                      "fer": summary["fer"],
                      "undetected": summary["undetected"],
                      "f_super": summary["f_super"],
                      "f_eff": summary["f_eff"],
                      "elapsed_s": summary["elapsed_s"],
                      "route_ctx": summary["route_ctx"],
                      "gate": summary["gate_contribution"],
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
    last = block_seed(S01_N_BLOCKS - 1)
    stream_ok = (stream_seed(first)
                 == common.v10_seed(f"o1_blk:{first}"))
    pin("seeds", S01_BLOCK_BASE == 2026095601 and S01_N_BLOCKS == 240
        and first == 2026095601 and last == 2026095840 and stream_ok
        and S01_STREAM == "o1_blk:{seed}",
        {"block_base": S01_BLOCK_BASE, "blocks": S01_N_BLOCKS,
         "first": first, "last": last, "stream": S01_STREAM,
         "stream_first_matches_frozen": bool(stream_ok)})

    pin("budget", S01_WALL_CAP_S == 3600 and S01_BATCH_CEILING_S == 7200
        and S01_PER_DECODE_CAP_S == 300 and S01_RSS_CAP_GIB == 2
        and S01_CPUS == 1 and BAR12 == 12
        and n_required_frozen() == N_REQ,
        {"wall_cap_s_per_arm": S01_WALL_CAP_S,
         "batch_ceiling_s": S01_BATCH_CEILING_S,
         "per_decode_cap_s": S01_PER_DECODE_CAP_S,
         "rss_cap_gib": S01_RSS_CAP_GIB, "cpus": S01_CPUS,
         "bar12_report_only": BAR12, "n_req_report_only": N_REQ})

    pin("arms", ARMS == {"S01-R1": 2026092001, "S01-R2": 2026092011}
        and S01_M == 200,
        {"arms": dict(ARMS), "m": S01_M,
         "reporting": "separate per instance; pooling incl. 6+4 FORBIDDEN"})

    out["roots"] = {"family": S01_ROOT_PREFIX,
                    "family_exists": os.path.exists(S01_ROOT_PREFIX)}

    out["frozen_accounting"] = {
        "f_super": F_SUPER, "f_super_literal": F_SUPER_LITERAL,
        "content_bits": CONTENT_BITS, "leak_bits": LEAK_BITS,
        "f_eff_slope": F_EFF_SLOPE, "n_req_report_only": N_REQ,
        "f_super_formula": "(5*200+64)/852.544 = 1064/852.544"}

    if with_construct_pins:
        measured: dict[str, Any] = {}
        for arm_name in ("S01-R1", "S01-R2"):
            base = construct_and_pin(arm_name,
                                     PRODUCTION_CONSTRUCT[arm_name],
                                     production_rank_fn)
            measured[arm_name] = {
                "instance": base["construct_instance"],
                "a208_pins": base["a208_pins"],
                "base_rows": "rows[0,200)",
                "base_rank": base["base_rank"],
                "base_rank_required": S01_M,
                "girth": "recorded-not-gated"}
        out["construction_pins"] = {
            "status": "MEASURED-DRY (zero decode)",
            "measured": measured}
        out["verdict"] = "DRY-PASS (zero decode; literal + construction pins)"
    else:
        out["construction_pins"] = {
            "status": "PENDING (rank==200 dry placeholder — NOT run in "
                      "this pass; zero decode either way)",
            "gates": {"a208_four_cycles": 0, "a208_rank": S01_A208_M,
                      "a208_twice_identical": True,
                      "base_rows": "rows[0,200)",
                      "base_rank_required": S01_M,
                      "girth": "recorded-not-gated"},
            "command": ("PYTHONPATH=<repo> .venv/bin/python -m "
                        "comparison_bench.src.comparison_bench.cli."
                        "s01_m200_runner --dry --construct-pins")}
        out["verdict"] = ("DRY-PASS (zero decode; literal pins; F6 "
                          "construction pins PENDING)")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="S0.1 m=200 thin runner (one arm per invocation; "
                    "--dry is the zero-decode pre-grant path; production "
                    "decoding requires BOTH execution flags + every "
                    "frozen literal).")
    ap.add_argument("--dry", action="store_true", default=False)
    ap.add_argument("--construct-pins", action="store_true", default=False)
    ap.add_argument("--execute-real", action="store_true", default=False)
    ap.add_argument("--execution-authorized", action="store_true",
                    default=False)
    ap.add_argument("--arm", default="")
    ap.add_argument("--m", type=int, default=None)
    ap.add_argument("--instance", type=int, default=None)
    ap.add_argument("--blocks", type=int, default=None)
    ap.add_argument("--seed-base", type=int, default=None)
    ap.add_argument("--root", default="")
    args = ap.parse_args(argv)

    if args.dry:
        if args.execute_real or args.execution_authorized:
            refuse("--dry cannot be combined with execution flags "
                   "(rc=2 pre-anything)")
        if args.arm or args.root or args.m is not None:
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
    if args.m != S01_M:
        refuse(f"--m must be the frozen {S01_M} (got {args.m}; packet F2 — "
               f"single point, no operating-point selection)")
    if args.instance != spec["instance"]:
        refuse(f"--instance must be {spec['instance']} for {args.arm} "
               f"(got {args.instance}; packet F1)")
    if args.blocks != S01_N_BLOCKS:
        refuse(f"--blocks must be the frozen {S01_N_BLOCKS} "
               f"(got {args.blocks}; packet F3/F9 — no early stop)")
    if args.seed_base != S01_BLOCK_BASE:
        refuse(f"--seed-base must be the frozen literal {S01_BLOCK_BASE} "
               f"(got {args.seed_base}; packet F3)")
    if not args.root:
        refuse(f"root required: fresh additive {S01_ROOT_PREFIX}"
               f"{args.arm}_<uuid8> (packet §5)")
    _check_root(args.root, args.arm)  # rc=2 BEFORE any bind/construct
    return run_execution(root=args.root, arm=args.arm)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
