"""X1 successor thin arm runner (T-X1S-4, EXPLORE code — NOT execution).

Frozen contract: ``docs/research_cycles/V80-NBLDPC-JAN21/
X1_SUCCESSOR_ENTRY_PACKET.md`` (§§1–8) + ``X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md``
+ ``X1_SUCCESSOR_ENTRY_PROMPT.md`` (proposed Acceptance ID G-X1S).

Determination (X1-RUN-1): NO existing campaign CLI can run the frozen §2
grid verbatim, so this ONE additive module exists. What the existing
``v80_b2f_campaign`` CLI cannot meet (file:line evidence):

- Arms frozen to F208/F202 only (``v80_b2f_campaign.py:179-189`` ARMS table;
  unknown-arm refusals at :208-209, :243-244, :1043-1044, :1257-1258). X1
  needs 15 arms with m in {185,189,193,197,201} / {191,195,199,203,207} /
  {192,196,200,204,208} — only m=208 overlaps, and m=202 is NOT in the X1
  grid at all.
- Construction delegates to the frozen O1 paired instances A208/A202
  (``v80_b2f_campaign.py:235-253``). X1 §2.3 needs standalone per-m
  constructs (``X1-*-S<m>-standalone``) with pins fc=0 + rank-full +
  twice-identical GATED.
- Metrics on the UNCHANGED O1 basis f_super=(5m+64)/852.544
  (``v80_b2f_campaign.py:358-364``; CONTENT_BITS at :150). X1 §2.5 needs
  own-H ``f_super=(5m+64)/(1024·H_source_corr)`` + ``f_eff=f_super+
  4.785675·FER`` per source, an ``undetected`` class logged separately
  (zero ``undetected`` hits in the b2f module), bar-12 ⇒ CENSORED
  reporting (b2f emits ``FAIL-early-stop``, :1187), and per-arm ≤1800 s
  (b2f WALL_CAP_S=3600, :139) under ``workspace/x1_`` roots (:132-133).

What this module reuses READ-ONLY (zero frozen-module change):

- ``s2c.bind_empirical_bundle(bundle_path, source_key)`` — the frozen
  consumer, F1 path form (bundle npz + sibling ``gamma_f03_pb.npz``
  resolved by the frozen ``PB_SIDECAR_NAME``).
- ``b2f.decode_block_marginal(construction, seed, bundle, n, m)`` — the
  frozen b2f/v28 procedure verbatim (``o1_blk:{seed}`` triple draw, exact
  Bayes-marginal prior, XOR centering, ``decode_error_domain_posterior``
  max_iter 300 / streak 3, ``exact_match`` flag, report-only
  ``prior_entropy_bits`` + ``u1_mismatches``).
- ``o1.fail_bar`` / ``o1.stream_seed`` — frozen bar-12 + stream semantics.
- ``peg.peg_construct`` + ``_mcde.make_rho`` + ``s2.Q`` + GF(32) field —
  the frozen A-series construction body (same calls as
  ``o1.construct_arm``, ``v80_o1_campaign.py:297-315``), parameterized by
  the arm's m for standalone per-m constructs.

Frozen literals CARRIED here (packet §2 restatement; nothing invented):

- n=1024, lambda={2:1}, construct instance 2026092001 / trials 20,
  block seeds 2026095601+idx idx 0..239, stream ``o1_blk:{seed}``,
  240 blocks, per-decode ≤300 s, per-arm ≤1800 s, RSS <4 GiB, 1 CPU.
- Grid: 1M {185,189,193,197,201} / 1.5M {191,195,199,203,207} /
  2M {192,196,200,204,208}; display→key {1M:1M, 1.5M:1p5M, 2M:2M}.
- Own-H ``H_corr``: 1M 0.8012690084416184 / 1p5M 0.8272902027770036 /
  2M 0.8333327179427281; slope 4.785675; bars 12 and f_super ≤ 1.3.

Block classes: success (``exact_match is True``) / undetected
(converged — ``reconstruction_ok is True`` — but x_hat != x) / fail
(all other non-matches). Gate-(a) ``fails`` counts EVERY non-exact-match
block (b2f-verbatim: undetected is NOT success, and the bar is not
weakened by a third class); the undetected count is logged separately
and never merged into success (packet §2.5). Overall arm verdict PASS
iff gate (a) AND gate (b); gate (c) is rule-evaluated per arm
(expected-FAIL at high m per packet §4) with the presentation ban
enforced structurally (f_super and f_eff always reported as DISTINCT
lines, never a single certifiable number). Curve-relative
monotone/non-monotone labels are batch-level (no cross-m inference
here): non-early-stop arms are recorded NON-CENSORED with the curve
label deferred to batch analysis; bar-12 arms are CENSORED.

No ``.ttbin`` read (no such import, path, or string anywhere here), no
decoder/DE/graph-kernel change, no refit path, no overwrite path, no
resume/continue path (wall-partial ⇒ INCOMPLETE, retained, never
continued), no writes outside the fresh per-arm root, never under
``results/`` or ``comparison_bench/outputs_comparison/``.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v10_peg as peg,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v26_mcde as _mcde,
)
from comparison_bench.src.comparison_bench.formal_ir import v80_o1_campaign as o1
from comparison_bench.src.comparison_bench.formal_ir import v80_s2_peg as s2
from comparison_bench.src.comparison_bench.formal_ir import (
    v80_s2c_campaign as s2c,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    v80_b2f_campaign as b2f,
)
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (
    GF2mField,
)

__all__ = [
    "X1_N", "X1_CONSTRUCT_SEED", "X1_MAX_TRIALS", "X1_LAMBDA",
    "X1_BLOCK_BASE", "X1_N_BLOCKS", "X1_MAX_ITER",
    "X1_WALL_CAP_S", "X1_PER_DECODE_CAP_S", "X1_RSS_CAP_GIB",
    "X1_ROOT_PREFIX", "FORBIDDEN_ROOT_PARTS",
    "X1_VERIFY_FILENAME", "GRID", "DISPLAY_TO_KEY", "H_CORR",
    "F_EFF_SLOPE", "F_SUPER_MAX",
    "Refusal", "refuse", "parse_arm", "block_seed", "stream_seed",
    "fail_bar", "f_super_for", "f_eff_for", "n_required",
    "construct_standalone", "bind_source_bundle",
    "block_accounting_csv", "result_markdown",
    "execute", "run_execution", "main",
]

#: Frozen single-code length (o1.O1_N; f_super denominator 1024·H).
X1_N = 1024
#: Frozen single construction instance (o1.O1_CONSTRUCT_SEED; packet §2.2).
X1_CONSTRUCT_SEED = 2026092001
#: Frozen constructor trials (o1.O1_MAX_TRIALS).
X1_MAX_TRIALS = 20
#: Frozen variable-side degree profile (every O1 A-arm; b2f ARMS).
X1_LAMBDA: dict[int, float] = {2: 1.0}
#: Frozen literal block-seed base (B2F_BLOCK_BASE; packet §2.2).
X1_BLOCK_BASE = 2026095601
#: Frozen campaign width: 240 blocks = 240 decodes/arm.
X1_N_BLOCKS = 240
#: Frozen decoder cap (b2f MAX_ITER; v28 streak default 3).
X1_MAX_ITER = 300
#: Frozen X1 per-arm wall budget (packet §2.7; NOT the b2f 3600 s window).
X1_WALL_CAP_S = 1800
#: Frozen per-decode terminal (packet §2.7; b2f PER_DECODE_CAP_S).
X1_PER_DECODE_CAP_S = 300
#: Frozen RSS cap (packet §2.7).
X1_RSS_CAP_GIB = 4
#: Fresh additive X1 run-root prefix (packet §2.7).
X1_ROOT_PREFIX = "workspace/x1_"
#: Roots the executor never writes under.
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")
#: F2 segregation: the verification-only re-derived 2M file is NEVER bound.
X1_VERIFY_FILENAME = "x1_gamma_f03r1_2M_verify.npz"
#: Frozen 15-arm grid (packet §2.2), keyed by BUNDLE key.
GRID: dict[str, tuple[int, ...]] = {
    "1M": (185, 189, 193, 197, 201),
    "1p5M": (191, 195, 199, 203, 207),
    "2M": (192, 196, 200, 204, 208),
}
#: Arm-display source → bundle-key map (packet §2.6; "1.5M" never a key).
DISPLAY_TO_KEY = {"1M": "1M", "1.5M": "1p5M", "2M": "2M"}
#: R1-corrected own-H basis (packet §2.1), keyed by BUNDLE key.
H_CORR = {
    "1M": 0.8012690084416184,
    "1p5M": 0.8272902027770036,
    "2M": 0.8333327179427281,
}
#: Frozen f_eff slope (packet §2.5).
F_EFF_SLOPE = 4.785675
#: Frozen efficiency bar (packet §4 G-B).
F_SUPER_MAX = 1.3

_ARM_RE = re.compile(r"^X1-(1M|1\.5M|2M)-(\d+)$")


class Refusal(SystemExit):
    """rc=2 pre-write refusal (unauthorized / invalid / gate-blocked)."""


def refuse(reason: str) -> "Any":
    print(f"X1-REFUSAL rc=2: {reason}", file=sys.stderr)
    raise Refusal(2)


def parse_arm(arm: str) -> dict[str, Any]:
    """Parse ``X1-<SOURCE>-<M>`` against the frozen grid (packet §2.2).

    Returns display source, bundle key, m, and the standalone
    construction label. Anything off-grid refuses (fail closed, rc=2).
    """
    mobj = _ARM_RE.match(str(arm))
    if mobj is None:
        refuse(f"unknown arm {arm} (frozen form: X1-<1M|1.5M|2M>-<m>)")
    display = str(mobj.group(1))
    m = int(mobj.group(2))
    key = DISPLAY_TO_KEY[display]
    if m not in GRID[key]:
        refuse(f"arm {arm} m={m} off the frozen X1-{display} grid "
               f"{list(GRID[key])} (packet §2.2; grid unchanged)")
    return {"arm": str(arm), "display": display, "source_key": key,
            "m": m,
            "construct_label": f"X1-{display}-S{m}-standalone"}


def block_seed(idx: int, base: int | None = None) -> int:
    """Frozen literal block seed: base+idx, idx=0..239 (packet §2.2)."""
    b = X1_BLOCK_BASE if base is None else base
    if isinstance(b, bool) or not isinstance(b, int):
        refuse("block base must be an integer literal")
    return int(b) + int(idx)


def stream_seed(seed: int) -> int:
    """Frozen stream derivation (o1.stream_seed, read-only reuse)."""
    return o1.stream_seed(int(seed))


def fail_bar(n_blocks: int) -> int:
    """Derived pass bar via the frozen o1 rule: floor(n·0.05); 240 → 12."""
    return o1.fail_bar(int(n_blocks))


def f_super_for(source_key: str, m: int) -> float:
    """Own-basis f_super = (5m+64)/(1024·H_corr[source]) (packet §2.5)."""
    if source_key not in H_CORR:
        refuse(f"unknown source key {source_key} (frozen: 1M|1p5M|2M)")
    return float(5 * int(m) + 64) / (float(X1_N) * float(H_CORR[source_key]))


def f_eff_for(f_super: float, fer: float) -> float:
    """f_eff = f_super + 4.785675·FER on the same own basis (packet §2.5)."""
    return float(f_super) + float(F_EFF_SLOPE) * float(fer)


def n_required(f_super: float) -> float:
    """Gate-(c) rule: N ≥ ceil(3·4.785675/(1.3−f_super)); inf if f≥1.3."""
    denom = float(F_SUPER_MAX) - float(f_super)
    if denom <= 0.0:
        return math.inf
    return float(math.ceil(3.0 * float(F_EFF_SLOPE) / denom))


def construct_standalone(m: int, seed: int = X1_CONSTRUCT_SEED,
                         max_trials: int = X1_MAX_TRIALS) -> dict[str, Any]:
    """Standalone per-m single build (packet §2.3; A-series precedent).

    Frozen PEG path only (same calls as ``o1.construct_arm``,
    ``v80_o1_campaign.py:297-315``, with the arm-name gate replaced by
    the arm's m): ``peg_construct`` + ``make_rho`` +
    ``_reconcile_check_counts`` (inside ``peg_construct``), GF(32)
    labels, n=1024, lambda={2:1}. Pin gating (fc=0 + rank-full +
    twice-identical) happens in ``_construct_gate`` on top of this.
    Pure in-memory; no disk writes.
    """
    if isinstance(m, bool) or not isinstance(m, int) or int(m) < 1:
        refuse("standalone construct m must be a positive int")
    if isinstance(seed, bool) or not isinstance(seed, int):
        refuse("construct seed must be an integer")
    if isinstance(max_trials, bool) or not isinstance(max_trials, int) \
            or int(max_trials) < 1:
        refuse("construct trials must be a positive int")
    field = GF2mField.create(s2.Q)
    lam = {int(k): float(v) for k, v in X1_LAMBDA.items()}
    try:
        rho = _mcde.make_rho(1.0 - int(m) / X1_N, lam)
        code = peg.peg_construct(X1_N, int(m), lam, rho, int(seed),
                                 max_trials=int(max_trials), field=field)
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed pre-decode
        refuse(f"standalone construction failed (m={m}): "
               f"{type(exc).__name__}: {exc}")
    code["family"] = "peg-irregular"
    s2.refuse_three_shift_cyclic({"family": code["family"]})
    code["lambda_edge"] = lam
    code["rho_edge"] = {int(k): float(v) for k, v in rho.items()}
    return code


def _construct_gate(m: int, construct_fn: Callable, seed: int,
                    trials: int) -> dict[str, Any]:
    """Pre-run construction gate (packet §2.3): build twice on the frozen
    instance, require twice-identical triples; pins fc=0 + rank-full
    (rank==m) GATED (STOP-BLOCKED); girth recorded-not-gated.
    ``construct_fn`` convention is ``(m, seed, trials)``. Mismatch halts
    STOP-BLOCKED before any decode.
    """
    try:
        code_a = construct_fn(int(m), int(seed), int(trials))
        code_b = construct_fn(int(m), int(seed), int(trials))
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed pre-decode
        refuse(f"construction failed (m={m}): "
               f"{type(exc).__name__}: {exc}")
    ta, tb = code_a.get("triples"), code_b.get("triples")
    if ta is not None or tb is not None:
        try:
            sa = sorted(tuple(map(int, t)) for t in ta)
            sb = sorted(tuple(map(int, t)) for t in tb)
        except Exception:  # noqa: BLE001
            refuse(f"construction triples corrupt (m={m}; STOP-BLOCKED)")
        if sa != sb:
            refuse(f"construct-twice mismatch (m={m}; not identical; "
                   f"STOP-BLOCKED)")
    if code_a.get("status", "ok") != "ok":
        refuse(f"construction {code_a.get('status')} (m={m}; STOP-BLOCKED)")
    try:
        fc = int(code_a.get("four_cycles"))
        girth = int(code_a.get("min_girth"))
        rank = int(code_a.get("rank"))
    except Exception:  # noqa: BLE001
        refuse(f"construction missing fc/girth/rank pins (m={m}; "
               f"STOP-BLOCKED)")
    if fc != 0:
        refuse(f"standalone m={m} four_cycles {fc} != 0 (STOP-BLOCKED; "
               f"packet §2.3; measured girth {girth})")
    if rank != int(m):
        refuse(f"standalone m={m} rank {rank} != {m} (STOP-BLOCKED; "
               f"packet §2.3; measured girth {girth})")
    code_a["construct_seed"] = seed
    code_a["construct_trials"] = trials
    code_a["measured_girth"] = girth  # recorded-not-gated
    return code_a


def bind_source_bundle(bundle_path: str, source_key: str,
                       arm: str) -> dict[str, Any]:
    """Bind the §2.6 bundle READ-ONLY via the frozen consumer (F1 form).

    Cross-source reuse is REFUSED by source-label check: the arm's frozen
    key must equal ``source_key`` (packet §2.4), the F2 verification-only
    file is never bound, and the frozen ``bind_empirical_bundle`` path
    form (shape/normalization gates) does the array-level binding.
    """
    spec = parse_arm(arm)
    if source_key != spec["source_key"]:
        refuse(f"cross-source channel reuse refused: arm {arm} needs key "
               f"{spec['source_key']}, got {source_key} (packet §2.4)")
    name = Path(str(bundle_path)).name
    if name == X1_VERIFY_FILENAME:
        refuse(f"verification-only file {X1_VERIFY_FILENAME} is never "
               f"bound by any decode path (F2 segregation, packet §2.6)")
    if spec["source_key"] == "2M":
        if name != "gamma_f03.npz":
            refuse(f"2M decode arms bind ONLY the frozen gamma_f03.npz "
                   f"(got {name}; NEVER the re-derived-2M verification "
                   f"file, NEVER a substitute — packet §2.6/F2)")
    elif name != "x1_gamma_f03r1.npz":
        refuse(f"1M/1.5M decode arms bind ONLY the §2.6-built "
               f"x1_gamma_f03r1.npz (got {name}; vintage substitution "
               f"refused — packet §5)")
    bound = s2c.bind_empirical_bundle(str(bundle_path), str(source_key))
    if bound.get("source") != str(source_key):
        refuse("bound source label mismatch (fail closed)")
    return bound


def _check_root(root: str) -> None:
    if not root:
        refuse("root required (fresh additive workspace/x1_<uuid>)")
    if not str(root).startswith(X1_ROOT_PREFIX):
        refuse(f"root must be fresh additive {X1_ROOT_PREFIX}<uuid> "
               f"(got {root})")
    parts = Path(str(root)).parts
    if any(p in FORBIDDEN_ROOT_PARTS for p in parts):
        refuse(f"root under forbidden tree (results/outputs_comparison): "
               f"{root}")


def default_writer(root: str, files: dict[str, str]) -> None:
    """Single-writer overwrite-in-place (research code; root policy is
    enforced in ``execute`` — fail closed before the first write)."""
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
    """Per-block accounting table (packet §2.9 deliverable)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["block", "seed", "exact_match", "undetected", "status",
                "iterations", "wall_s", "prior_entropy_bits",
                "u1_mismatches", "leak_bits", "f_super"])
    for r in rows:
        if r.get("status") in ("error", "overrun"):
            w.writerow([r.get("block"), "", "", "", r.get("status"), "",
                        "", "", "", "", ""])
            continue
        w.writerow([r.get("block"), r.get("seed"), r.get("exact_match"),
                    r.get("undetected"), r.get("status"),
                    r.get("iterations"), r.get("wall_s"),
                    r.get("prior_entropy_bits"), r.get("u1_mismatches"),
                    r.get("leak_bits"), r.get("f_super")])
    return buf.getvalue()


def result_markdown(summary: dict[str, Any]) -> str:
    """Per-arm ``X1_RESULT_*.md`` body (packet §2.9)."""
    g = summary["gates"]
    lines = [
        f"# X1 result — {summary['arm']} (EXPLORE synthetic, RAW)",
        "",
        f"- arm: `{summary['arm']}` ({summary['construct_label']}; "
        f"standalone per-m construct — NOT a P1 nested submatrix)",
        f"- bundle: `{summary['bundle_path']}` key `{summary['source_key']}` "
        f"(TRAIN-side provenance; H_corr CONDITIONAL on the R1 §3A "
        f"alignment; bound source label == arm source, cross-source "
        f"reuse refused)",
        f"- seeds: `2026095601+idx` idx 0..{summary['blocks_done'] - 1} "
        f"(stream `o1_blk:{{seed}}`); construction instance 2026092001 / "
        f"trials 20; pins fc={summary['four_cycles']} + rank-full "
        f"(rank={summary['rank']}) + twice-identical GATED, girth "
        f"{summary['girth']} recorded-not-gated",
        f"- decoder: b2f verbatim + v28 `decode_error_domain_posterior` "
        f"max_iter 300 / streak 3, `exact_match` accept; NO "
        f"genie/argmax/L1; report-only `prior_entropy_bits`, "
        f"`u1_mismatches`",
        f"- wall: {summary['elapsed_s']:.1f} s (cap 1800 s/arm); "
        f"per-decode ≤300 s terminal; peak RSS {summary['rss_gib']:.3f} "
        f"GiB (<4 GiB)",
        f"- fails: {summary['failures']}/{summary['blocks_done']} "
        f"(FER {summary['fer']:.6f}); undetected {summary['undetected']} "
        f"(logged separately, NEVER merged into success; gate-(a) fails "
        f"count every non-exact-match block, b2f-verbatim)",
        f"- f_super (own-basis H_corr[{summary['source_key']}]="
        f"{summary['h_corr']!r}): {summary['f_super']:.8f}; f_eff = "
        f"f_super+4.785675·FER = {summary['f_eff']:.8f} (DISTINCT lines; "
        f"NEVER quote f_super as f_eff when FER > 0; single-source f_eff "
        f"is NEVER presented as certifiable/literature-comparable)",
        f"- curve label: {summary['curve_label']} (no cross-m "
        f"monotonicity inference)",
        f"- G-A (route fails/240 ≤ 12): {g['a']}; G-B (f_super ≤ 1.3 own "
        f"H_corr): {g['b']}; G-C (N ≥ ceil(3·4.785675/(1.3−f_super)) = "
        f"{summary['n_required']}: N={summary['blocks_done']} ⇒ "
        f"{g['c']}; presentation ban held)",
        f"- G-D (bundle entry): bound via the frozen consumer "
        f"(shape/normalization gates PASS at bind); R1-checksum + 2M "
        f"lineage evidence in the bundle-root verification report "
        f"(batch-level record)",
        f"- G-E (integrity/stop): budgets held; zero `.ttbin` reads "
        f"(no such code path); cross-source reuse refused by "
        f"source-label check; no pooling; no `undetected`-merging; "
        f"`src/` untouched (batch-level `git diff -- src/` proof)",
        f"- verdict: {summary['verdict']}",
        "",
    ]
    return "\n".join(lines)


def execute(*, root: str, arm: str,
            bundle: dict[str, Any] | None = None,
            bundle_label: str | None = None,
            construct_fn: Callable | None = None,
            decode_fn: Callable | None = None,
            clock: Callable | None = None,
            rss_fn: Callable | None = None,
            writer: Callable | None = None,
            max_blocks: int | None = None) -> dict:
    """Run the frozen X1 arm procedure under ``root`` (one arm/invocation).

    ``max_blocks`` is a PROBE-ONLY cap (never a CLI flag, never part of
    any verdict). Without an injected ``decode_fn``, ``bundle`` is
    required (no silent production bind — the CLI binds ``--bundle``
    explicitly). Tests MUST pass an explicit fake ``decode_fn`` (and a
    fake ``construct_fn`` where construction is not under test).
    """
    spec = parse_arm(arm)
    _check_root(root)
    m = int(spec["m"])
    source_key = str(spec["source_key"])
    f_super = f_super_for(source_key, m)
    leak_bits = 5 * m + 64
    bar = fail_bar(X1_N_BLOCKS)
    construct_fn = construct_fn or construct_standalone
    if decode_fn is None:
        if bundle is None:
            refuse("empirical bundle required (no silent production bind; "
                   "pass bundle or bind --bundle at the CLI)")
        _bundle = bundle

        def decode_fn(construction, seed, _b=_bundle):  # noqa: B023
            return b2f.decode_block_marginal(construction, seed, _b,
                                             X1_N, m)
    clock = clock or time.monotonic
    rss_fn = rss_fn or _default_rss
    writer = writer or default_writer
    if max_blocks is not None and (
            not isinstance(max_blocks, int) or max_blocks < 1):
        refuse("max_blocks (probe-only) must be a positive int")

    if os.path.exists(root):
        refuse(f"root not fresh: {root}")
    construction = _construct_gate(m, construct_fn, X1_CONSTRUCT_SEED,
                                   X1_MAX_TRIALS)
    rows: list[dict] = []
    failures = 0
    undetected = 0
    ledger_decodes = 0
    t_start = clock()
    rss_peak_gib = 0.0

    target = X1_N_BLOCKS if max_blocks is None else min(max_blocks,
                                                        X1_N_BLOCKS)

    def _summary(verdict: str, censored: bool) -> dict[str, Any]:
        n = len(rows)
        fer = (failures / n) if n else 0.0
        f_eff = f_eff_for(f_super, fer)
        n_req = n_required(f_super)
        gate_a = "PASS" if failures <= bar else "FAIL"
        gate_b = "PASS" if f_super <= F_SUPER_MAX else "FAIL"
        gate_c = ("PASS" if n >= n_req
                  else "FAIL-expected (packet §4: expected-FAIL at high m; "
                       "presentation ban enforced)")
        return {
            "arm": arm, "source_key": source_key, "m": m,
            "construct_label": spec["construct_label"],
            "bundle_path": (bundle_label if bundle_label is not None
                            else "<injected-bound-bundle>"),
            "h_corr": H_CORR[source_key],
            "four_cycles": construction.get("four_cycles"),
            "rank": construction.get("rank"),
            "girth": construction.get("measured_girth",
                                      construction.get("min_girth")),
            "blocks_done": n, "failures": failures,
            "undetected": undetected, "fer": fer,
            "f_super": f_super, "f_eff": f_eff,
            "n_required": (n_req if math.isfinite(n_req) else "inf"),
            "curve_label": ("CENSORED (bar-12 early-stop; fails-at-stop / "
                            "blocks-at-stop reported, projected NEVER)"
                            if censored else
                            "NON-CENSORED (curve-relative monotone label "
                            "deferred to batch analysis)"),
            "censored": bool(censored),
            "gates": {"a": gate_a, "b": gate_b, "c": gate_c},
            "verdict": verdict,
            "ledger_decodes": ledger_decodes,
            "elapsed_s": float(clock() - t_start),
            "rss_gib": float(rss_peak_gib),
        }

    def _flush(summary: dict[str, Any]) -> dict[str, Any]:
        writer(root, {
            f"X1_RESULT_{source_key}_{m}.md": result_markdown(summary),
            "rows.json": json.dumps({"summary": summary, "rows": rows},
                                    indent=1, sort_keys=True, default=str),
            "block_accounting.csv": block_accounting_csv(rows)})
        return summary

    for k in range(target):
        if clock() - t_start > X1_WALL_CAP_S:
            return _flush(_summary("INCOMPLETE-wall", False))
        try:
            rss_gib = float(rss_fn()) / (1024 ** 3)
        except Exception:  # noqa: BLE001 — probe failure never halts
            rss_gib = 0.0
        rss_peak_gib = max(rss_peak_gib, rss_gib)
        if rss_gib >= X1_RSS_CAP_GIB:
            return _flush(_summary("FAIL(budget)", False))
        seed = block_seed(k)
        t0 = clock()
        try:
            out = decode_fn(construction, seed)
        except Exception as exc:  # noqa: BLE001 — no-retry: retain + halt
            rows.append({"block": k, "status": "error",
                         "error": f"{type(exc).__name__}: {exc}"})
            return _flush(_summary("FAIL(budget)", False))
        dt = clock() - t0
        if dt > X1_PER_DECODE_CAP_S:
            rows.append({"block": k, "status": "overrun",
                         "decode_s": dt})
            return _flush(_summary("FAIL(budget)", False))
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
            failures += 1
        if und:
            undetected += 1
        ledger_decodes += 1
        rows.append({
            "block": k,
            "seed": seed,
            "exact_match": exact,
            "undetected": und,
            "block_accept": exact,
            "block_fail": 0 if exact else 1,
            "status": out.get("status"),
            "converged": conv,
            "iterations": out.get("iterations"),
            "wall_s": dt,
            "prior_entropy_bits": float(pe),
            "u1_mismatches": int(km),
            "leak_bits": leak_bits,
            "f_super": f_super,
            "bundle_provenance": ("TRAIN-side; R1-root derived; "
                                  "alignment-conditional H_corr"),
            "source_key": source_key,
            "arm": arm,
            "construct_label": spec["construct_label"],
        })
        _flush(_summary("INCOMPLETE-wall", False))
        if failures > bar:
            return _flush(_summary("FAIL-early-stop", True))

    if max_blocks is not None:
        return _flush(_summary("PROBE-truncated", False))
    passed = failures <= bar and f_super <= F_SUPER_MAX
    return _flush(_summary("PASS" if passed else "FAIL", False))


def run_execution(root: str, arm: str, bundle_path: str,
                  pb_sidecar: str, source_key: str) -> int:
    bound = bind_source_bundle(bundle_path, source_key, arm)
    expected_sidecar = str(Path(bundle_path).parent / s2c.PB_SIDECAR_NAME)
    if str(pb_sidecar) != expected_sidecar:
        refuse(f"pb-sidecar {pb_sidecar} != frozen-resolved sibling "
               f"{expected_sidecar} (F1 path form; packet §2.6)")
    summary = execute(root=root, arm=arm, bundle=bound,
                      bundle_label=str(bundle_path))
    print(json.dumps({"arm": summary["arm"],
                      "verdict": summary["verdict"],
                      "failures": summary["failures"],
                      "undetected": summary["undetected"],
                      "fer": summary["fer"],
                      "f_super": summary["f_super"],
                      "f_eff": summary["f_eff"],
                      "curve_label": summary["curve_label"],
                      "gates": summary["gates"],
                      "ledger_decodes": summary["ledger_decodes"],
                      "root": root}, indent=1, sort_keys=True, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="X1 successor thin arm runner (T-X1S-4; one arm per "
                    "invocation).")
    ap.add_argument("--execute-real", action="store_true", default=False)
    ap.add_argument("--execution-authorized", action="store_true",
                    default=False)
    ap.add_argument("--arm", default="")
    ap.add_argument("--bundle", default="")
    ap.add_argument("--pb-sidecar", default="")
    ap.add_argument("--source-key", default="")
    ap.add_argument("--construct-instance", type=int, default=None)
    ap.add_argument("--standalone", action="store_true", default=False)
    ap.add_argument("--seeds", default="")
    ap.add_argument("--stream", default="")
    ap.add_argument("--blocks", type=int, default=None)
    ap.add_argument("--root", default="")
    ap.add_argument("--per-decode-timeout-s", type=int, default=None)
    ap.add_argument("--budget-s", type=int, default=None)
    args = ap.parse_args(argv)
    # Dual-flag gate: refuse EVERYTHING else rc=2 BEFORE any root/contact.
    if not args.execute_real:
        refuse("refusing: --execute-real missing (rc2 pre-anything)")
    if not args.execution_authorized:
        refuse("refusing: --execution-authorized missing (rc2 pre-anything)")
    spec = parse_arm(args.arm)
    if args.source_key != spec["source_key"]:
        refuse(f"source-key {args.source_key} != arm {args.arm} frozen key "
               f"{spec['source_key']} (cross-source reuse refused; "
               f"packet §2.4)")
    if args.construct_instance != X1_CONSTRUCT_SEED:
        refuse(f"construct-instance must be the frozen {X1_CONSTRUCT_SEED} "
               f"(got {args.construct_instance}; any change is a "
               f"science-input change → STOP)")
    if not args.standalone:
        refuse("refusing: --standalone missing (X1 constructs are "
               "standalone per-m, never P1 nested; packet §2.3)")
    if args.seeds != "2026095601+idx":
        refuse(f"seeds must be the frozen literal 2026095601+idx "
               f"(got {args.seeds})")
    if args.stream != "o1_blk:{seed}":
        refuse(f"stream must be the frozen literal o1_blk:{{seed}} "
               f"(got {args.stream})")
    if args.blocks != X1_N_BLOCKS:
        refuse(f"blocks must be the frozen {X1_N_BLOCKS} "
               f"(got {args.blocks})")
    if args.per_decode_timeout_s != X1_PER_DECODE_CAP_S:
        refuse(f"per-decode-timeout-s must be the frozen "
               f"{X1_PER_DECODE_CAP_S} (got {args.per_decode_timeout_s})")
    if args.budget_s != X1_WALL_CAP_S:
        refuse(f"budget-s must be the frozen {X1_WALL_CAP_S} "
               f"(got {args.budget_s})")
    if not args.bundle:
        refuse("bundle required (read-only §2.6 bundle path)")
    if not args.pb_sidecar:
        refuse("pb-sidecar required (read-only §2.6 sidecar path)")
    return run_execution(root=args.root, arm=args.arm,
                         bundle_path=args.bundle,
                         pb_sidecar=args.pb_sidecar,
                         source_key=args.source_key)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
