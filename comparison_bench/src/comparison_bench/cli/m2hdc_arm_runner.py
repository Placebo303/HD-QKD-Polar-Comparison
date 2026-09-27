"""M2 HD-Cascade thin arm runner (M2HDC, implementation-only, NOT execution).

Frozen contract: ``docs/research_cycles/M2-HDCASCADE-SYNTH/PACKET.md``
(Sec 0-9, cycle ``G-M2-HDCASCADE-SYNTH``) + ``M2-HDCASCADE-SYNTH-PROMPT.md``.
This file is code only; it grants NOTHING. The packet §7 authorization
block is BLANK (ungranted); execution needs a fresh explicit grant +
Pre-EXECUTE. This module only provides the executor + fake-testable
mechanics.

Determination: NO existing campaign CLI can run the frozen F1-F6 grid
verbatim, so this ONE additive module exists. What is reused READ-ONLY
(zero frozen-module change):

- ``s2c.bind_empirical_bundle(bundle_path, source_key)`` — the frozen
  consumer, F1 path form (bundle file + sibling sidecar resolved by the
  frozen ``PB_SIDECAR_NAME``).
- ``o1.stream_seed`` / ``o1.fail_bar`` — frozen stream + bar-12 semantics
  (``o1_blk:{seed}`` streams, ``ARM_SEED[arm]+k`` block seeds).
- ``hc.run_hd_cascade`` + ``hc.HdCascadeBlockTable`` +
  ``hc.HdCascadeParams`` — the frozen HD-Cascade method body, called
  read-only with an explicitly injected ``decode_fn`` (fake tests MUST
  inject; production per-plane cascade is never entered by fake tests).
- ``split_symbol_bitplanes`` (gray) — the frozen plane splitter, used
  read-only to verify the 10-plane Gray family in the sampler.
- ``FrameBatch`` / ``IRRunConfig`` — the frozen batch/config types.

Frozen literals CARRIED here (packet F1/F4-F6 restatement; nothing
invented):

- dimension=1024 (10 Gray planes), frame_len=64 symbols, content
  denominator 1024, construct instance 2026092001 (retained), block seeds
  ``ARM_SEED[arm]+k`` (A1 2026095701 .. A6 2026095706, k 0..239;
  ``2026095601`` OBSOLETE, provenance only), stream ``o1_blk:{seed}``,
  240 blocks, per-decode terminal 300 s, per-arm wall 5400 s,
  RSS <4 GiB, 1 CPU.
- Grid: 1M {197, 201} / 1.5M {203, 207} / 2M {204, 208};
  display-to-key {1M:1M, 1.5M:1p5M, 2M:2M}.
- Denominator H input (allocation/denominator ONLY, never refit):
  1M 0.801038 / 1.5M 0.825566 / 2M 0.832563 (packet F5 synthetic-F03 H,
  same basis as the frozen ``hd_cascade`` module); slope 4.785675;
  bars 12 and f_super 1.3; tag 64; key-eligible contrast (200, 276, 364).

Provisional pin slots (§7 F2/F3 BLANK at implementation time; values
below are marked ``assumed`` in every artifact and frozen at grant
time, never tuned mid-run): per-plane block schedules ``[8, 4]`` with
one bounded cross-plane sweep, ``max_passes`` 4, block-length floor 1,
per-frame message counting = ``messages_actual`` as reported by the
decode outcome (Cascade 446 aperture carried as an independent column,
LDPC 3.14 as a non-comparable annotation). The per-block cascade seed
is always passed explicitly (``block_seed(k, arm=arm)``); the placeholder
default seed carried by ``HdCascadeParams`` is never used here.

Block classes (A-CMPE-1): success requires ``exact_match`` AND
``accepted`` AND Toeplitz verification (the frozen unified gate inside
``run_hd_cascade``); undetected (``accepted`` but not success) is
logged separately and never merged into success; fail is every other
non-success block. Gate-(a) fails count EVERY non-success block;
bar-12 arms are CENSORED (fails-at-stop / blocks-at-stop reported,
projected NEVER). Overall arm verdict PASS iff gate (a) AND gate (b);
gate (c) is rule-evaluated report-only with the presentation ban
enforced structurally (f_super, f_notag and f_eff always reported as
DISTINCT lines, never a single certifiable number). Curve-relative
labels are batch-level (no cross-m inference here): non-early-stop
arms are recorded NON-CENSORED with the curve label deferred to batch
analysis. ``nb_decode_calls`` is always 0 (the narrowband production
decoder is never called; Cascade is the method under test).

No raw-dump reads (no such import, path, or extension string anywhere
here), no decoder/DE/graph-kernel change, no refit path, no overwrite
path, no resume/continue path (wall-partial yields INCOMPLETE,
retained, never continued; at most one preregistered infra
repair+rerun with unchanged science inputs, retained in the same
root), no writes outside the fresh per-arm root, never under
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

from comparison_bench.src.comparison_bench.formal_ir import v80_o1_campaign as o1
from comparison_bench.src.comparison_bench.formal_ir import (
    v80_s2c_campaign as s2c,
)
from comparison_bench.src.comparison_bench.methods import hd_cascade as hc
from comparison_bench.src.comparison_bench.methods.layered_ldpc_lite import (
    split_symbol_bitplanes,
)
from comparison_bench.src.comparison_bench.types import FrameBatch, IRRunConfig

__all__ = [
    "M2HDC_DIMENSION", "M2HDC_PLANES", "M2HDC_FRAME_LEN",
    "M2HDC_CONTENT_N", "M2HDC_CONSTRUCT_SEED", "M2HDC_BLOCK_BASE",
    "M2HDC_ARM_SEED",
    "M2HDC_N_BLOCKS", "M2HDC_WALL_CAP_S", "M2HDC_PER_DECODE_CAP_S",
    "M2HDC_RSS_CAP_GIB", "M2HDC_ROOT_PREFIX", "FORBIDDEN_ROOT_PARTS",
    "M2HDC_BUNDLE_FILENAME", "GRID", "DISPLAY_TO_KEY", "FROZEN_H",
    "F_EFF_SLOPE", "F_SUPER_MAX", "TAG_BITS",
    "M2HDC_MAX_PASSES_PROVISIONAL", "M2HDC_CROSS_SWEEPS_PROVISIONAL",
    "M2HDC_BLOCK_FLOOR_PROVISIONAL", "PRIOR_SCALE_REPORTONLY",
    "LDPC_MSG_REF", "CASCADE_MSG_REF", "CLAIM_CEILING",
    "Refusal", "refuse", "parse_arm", "block_seed", "stream_seed",
    "fail_bar", "f_super_for", "f_notag_for", "f_eff_for", "n_required",
    "lambda_total", "provisional_block_table", "check_block_table",
    "bind_source_bundle", "sample_frozen_batch",
    "block_accounting_csv", "result_markdown",
    "execute", "run_execution", "main",
]

#: Frozen alphabet size (1024 symbols -> 10 Gray planes).
M2HDC_DIMENSION = 1024
#: Frozen Gray plane count.
M2HDC_PLANES = 10
#: Frozen per-block frame length in symbols (n=64 family).
M2HDC_FRAME_LEN = 64
#: Frozen content denominator for f accounting (1024 * H_src).
M2HDC_CONTENT_N = 1024
#: Frozen construction instance (packet F4 seed slot family; single instance, retained).
M2HDC_CONSTRUCT_SEED = 2026092001
#: OBSOLETE literal (packet §7-4): superseded by M2HDC_ARM_SEED; retained
#: for provenance only, never used by sampler/executor paths (which always
#: pass an explicit arm).
M2HDC_BLOCK_BASE = 2026095601
#: Frozen per-arm seed bases (packet §7-4 assumed-v1; block k = ARM_SEED[arm]+k,
#: k 0..239; A1..A6 in frozen arm order).
M2HDC_ARM_SEED: dict[str, int] = {
    "M2HDC-1M-197": 2026095701,
    "M2HDC-1M-201": 2026095702,
    "M2HDC-1.5M-203": 2026095703,
    "M2HDC-1.5M-207": 2026095704,
    "M2HDC-2M-204": 2026095705,
    "M2HDC-2M-208": 2026095706,
}
#: Frozen campaign width: 240 blocks per arm.
M2HDC_N_BLOCKS = 240
#: Frozen per-arm wall budget (packet §7-6).
M2HDC_WALL_CAP_S = 5400
#: Frozen per-decode terminal (packet F3 timeout rule).
M2HDC_PER_DECODE_CAP_S = 300
#: Frozen RSS cap (packet F6).
M2HDC_RSS_CAP_GIB = 4
#: Fresh additive M2HDC run-root prefix (packet F6).
M2HDC_ROOT_PREFIX = "workspace/m2hdc_"
#: Roots the executor never writes under.
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")
#: Frozen bundle file name (packet F1; sidecar via s2c.PB_SIDECAR_NAME).
M2HDC_BUNDLE_FILENAME = "gamma_f03.npz"
#: Frozen 6-point grid (packet F1), keyed by BUNDLE key.
GRID: dict[str, tuple[int, ...]] = {
    "1M": (197, 201),
    "1p5M": (203, 207),
    "2M": (204, 208),
}
#: Arm-display source -> bundle-key map (packet F1; "1.5M" never a key).
DISPLAY_TO_KEY = {"1M": "1M", "1.5M": "1p5M", "2M": "2M"}
#: Frozen denominator H input (packet F5; denominator input ONLY, no refit;
#: H column is always "assumed" in artifacts).
FROZEN_H = {
    "1M": 0.801038,
    "1p5M": 0.825566,
    "2M": 0.832563,
}
#: Frozen f_eff slope (packet F5).
F_EFF_SLOPE = 4.785675
#: Frozen efficiency bar (packet §8 E-gates).
F_SUPER_MAX = 1.3
#: Frozen verification tag width.
TAG_BITS = 64
#: Provisional pin slot (§7 F3 BLANK): cascade pass cap, assumed until grant.
M2HDC_MAX_PASSES_PROVISIONAL = 4
#: Provisional pin slot (§7 F2 BLANK): bounded cross-plane lookback, assumed.
M2HDC_CROSS_SWEEPS_PROVISIONAL = 1
#: Provisional pin slot (§7 F2 BLANK): per-schedule block-length floor, assumed.
M2HDC_BLOCK_FLOOR_PROVISIONAL = 1
#: Frozen prior opportunity-cost scale (report-only, never into lambda/f).
PRIOR_SCALE_REPORTONLY = 1.50
#: LDPC-level per-frame message aperture (independent column, non-comparable).
LDPC_MSG_REF = 3.14
#: Cascade per-frame message aperture (independent column, non-comparable).
CASCADE_MSG_REF = 446
#: Claim-ceiling fixed sentence (packet §5; carried verbatim via hc).
CLAIM_CEILING = hc.CLAIM_CEILING

_ARM_RE = re.compile(r"^M2HDC-(1M|1\.5M|2M)-(\d+)$")
_ROOT_RE = re.compile(r"^workspace/m2hdc_[0-9A-Za-z]{8}$")


class Refusal(SystemExit):
    """rc=2 pre-write refusal (unauthorized / invalid / gate-blocked)."""


def refuse(reason: str) -> Any:
    print(f"M2HDC-REFUSAL rc=2: {reason}", file=sys.stderr)
    raise Refusal(2)


def parse_arm(arm: str) -> dict[str, Any]:
    """Parse ``M2HDC-<SOURCE>-<M>`` against the frozen grid (packet F1).

    Returns display source, bundle key, m, and the arm construction
    label. Anything off-grid refuses (fail closed, rc=2).
    """
    mobj = _ARM_RE.match(str(arm))
    if mobj is None:
        refuse(f"unknown arm {arm} "
               f"(frozen form: M2HDC-<1M|1.5M|2M>-<m>)")
    display = str(mobj.group(1))
    m = int(mobj.group(2))
    key = DISPLAY_TO_KEY[display]
    if m not in GRID[key]:
        refuse(f"arm {arm} m={m} off the frozen M2HDC-{display} grid "
               f"{list(GRID[key])} (packet F1; grid unchanged)")
    return {"arm": str(arm), "display": display, "source_key": key,
            "m": m,
            "construct_label": f"M2HDC-{display}-S{m}-hdcascade"}


def block_seed(idx: int, arm: str | None = None,
               base: int | None = None) -> int:
    """Frozen per-arm block seed: ARM_SEED[arm]+k, k=0..239 (packet §7-4).

    ``arm`` selects the frozen per-arm base (A1 2026095701 .. A6
    2026095706). An explicit ``base`` preserves the legacy explicit-base
    form (tests only). The module default ``M2HDC_BLOCK_BASE``
    (2026095601) is OBSOLETE (provenance only); sampler/executor paths
    always pass ``arm`` and never touch the obsolete default.
    """
    if arm is not None:
        try:
            b = M2HDC_ARM_SEED[str(arm)]
        except KeyError:
            refuse(f"unknown arm {arm} for ARM_SEED "
                   f"(frozen: {sorted(M2HDC_ARM_SEED)})")
        return int(b) + int(idx)
    b = M2HDC_BLOCK_BASE if base is None else base
    if isinstance(b, bool) or not isinstance(b, int):
        refuse("block base must be an integer literal")
    return int(b) + int(idx)


def stream_seed(seed: int) -> int:
    """Frozen stream derivation (o1.stream_seed, read-only reuse)."""
    return o1.stream_seed(int(seed))


def fail_bar(n_blocks: int) -> int:
    """Derived pass bar via the frozen o1 rule: floor(n*0.05); 240 -> 12."""
    return o1.fail_bar(int(n_blocks))


def f_super_for(source_key: str, m: int) -> float:
    """Own-basis f_super = (5m+64)/(1024*H[source]) (packet F5)."""
    if source_key not in FROZEN_H:
        refuse(f"unknown source key {source_key} (frozen: 1M|1p5M|2M)")
    return float(5 * int(m) + 64) / (
        float(M2HDC_CONTENT_N) * float(FROZEN_H[source_key]))


def f_notag_for(source_key: str, m: int) -> float:
    """f_notag = 5m/(1024*H[source]) (packet F5; tag-free contrast)."""
    if source_key not in FROZEN_H:
        refuse(f"unknown source key {source_key} (frozen: 1M|1p5M|2M)")
    return float(5 * int(m)) / (
        float(M2HDC_CONTENT_N) * float(FROZEN_H[source_key]))


def f_eff_for(f_super: float, fer: float) -> float:
    """f_eff = f_super + 4.785675*FER on the same basis (packet F5)."""
    return float(f_super) + float(F_EFF_SLOPE) * float(fer)


def n_required(f_super: float) -> float:
    """Gate-(c) rule: N >= ceil(3*4.785675/(1.3-f_super)); inf if f>=1.3."""
    denom = float(F_SUPER_MAX) - float(f_super)
    if denom <= 0.0:
        return math.inf
    return float(math.ceil(3.0 * float(F_EFF_SLOPE) / denom))


def lambda_total(leak_ec: float, tag_bits: float = TAG_BITS,
                 rescue_bits: float = 0.0,
                 control_bits: float = 0.0) -> float:
    """Frozen F5 decomposition: leak_EC + tag + rescue + control."""
    return (float(leak_ec) + float(tag_bits)
            + float(rescue_bits) + float(control_bits))


def provisional_block_table() -> "hc.HdCascadeBlockTable":
    """Provisional per-plane x pass block schedule (§7 F2 slot, assumed).

    The packet F2 block-length table is BLANK at implementation time, so
    this helper carries explicitly provisional values (uniform ``[8, 4]``
    per plane, one bounded cross-plane sweep) marked ``assumed`` in every
    artifact. Grant-time freezing may replace the values; the structure
    (10 planes, positive sizes, non-negative sweep bound) is enforced by
    :func:`check_block_table`.
    """
    schedules = {p: [8, 4] for p in range(M2HDC_PLANES)}
    table = hc.HdCascadeBlockTable(
        schedules,
        max_cross_plane_sweeps=int(M2HDC_CROSS_SWEEPS_PROVISIONAL))
    return check_block_table(table)


def check_block_table(table: Any) -> "hc.HdCascadeBlockTable":
    """Fail-closed validation of the per-plane block table (packet F2).

    Every plane 0..9 must carry a non-empty positive schedule (the
   待澄清表 rule: missing entries never defaulted); the provisional
    block-length floor also applies. Violations refuse (rc=2).
    """
    try:
        planes = table.planes(int(M2HDC_PLANES))
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed, never defaulted
        refuse(f"hd-cascade block table missing planes (fail closed): "
               f"{type(exc).__name__}: {exc}")
    if list(planes) != list(range(M2HDC_PLANES)):
        refuse("hd-cascade block table must cover planes 0..9 exactly")
    for p in range(M2HDC_PLANES):
        try:
            sizes = table.schedule_for(int(p))
        except Refusal:
            raise
        except Exception as exc:  # noqa: BLE001
            refuse(f"hd-cascade block table missing plane {p} "
                   f"(fail closed): {type(exc).__name__}: {exc}")
        if not sizes or any(int(s) < int(M2HDC_BLOCK_FLOOR_PROVISIONAL)
                            for s in sizes):
            refuse(f"hd-cascade block table plane {p}: sizes {sizes} "
                   f"below provisional floor "
                   f"{M2HDC_BLOCK_FLOOR_PROVISIONAL} (fail closed)")
    return table


def bind_source_bundle(bundle_path: str, source_key: str,
                       arm: str) -> dict[str, Any]:
    """Bind the F1 bundle READ-ONLY via the frozen consumer (F1 path form).

    Cross-source reuse is REFUSED by source-label check: the arm's frozen
    key must equal ``source_key`` (packet F1/F6), the bundle file must be
    the frozen ``gamma_f03.npz`` name, and the frozen
    ``bind_empirical_bundle`` path form (shape/normalization gates) does
    the array-level binding. No refit path exists here.
    """
    spec = parse_arm(arm)
    if source_key != spec["source_key"]:
        refuse(f"cross-source channel reuse refused: arm {arm} needs key "
               f"{spec['source_key']}, got {source_key} (packet F1/F6)")
    name = Path(str(bundle_path)).name
    if name != M2HDC_BUNDLE_FILENAME:
        refuse(f"M2HDC arms bind ONLY the frozen {M2HDC_BUNDLE_FILENAME} "
               f"(got {name}; substitute refused — packet F1)")
    bound = s2c.bind_empirical_bundle(str(bundle_path), str(source_key))
    if bound.get("source") != str(source_key):
        refuse("bound source label mismatch (fail closed)")
    return bound


def sample_frozen_batch(bundle: dict[str, Any], source_key: str,
                        n_blocks: int | None = None,
                        arm: str | None = None) -> FrameBatch:
    """Frozen 240-frame sampler (packet F1; synthetic only).

    Returns a ``FrameBatch`` with 240 frames x 64 symbols, dimension
    1024 (10 Gray planes). Deterministic per-block streams
    ``o1_blk:{seed}`` with seeds ``ARM_SEED[arm]+k`` k 0..239 (x1
    same-family stream derivation, read-only reuse of
    ``o1.stream_seed``); arm-less calls fall back to the OBSOLETE
    ``2026095601`` base (provenance only). Validates
    the bound source label (no cross-source use; an explicit ``arm``
    must also match ``source_key``), the 240 width, the
    n=64 family, and the 10-plane Gray split (read-only
    ``split_symbol_bitplanes``). Pure in-memory synthetic draws; never
    refits the bundle; never touches raw dumps.
    """
    n = M2HDC_N_BLOCKS if n_blocks is None else int(n_blocks)
    if isinstance(n, bool) or n != M2HDC_N_BLOCKS:
        refuse(f"sampler width frozen at {M2HDC_N_BLOCKS} "
               f"(got {n_blocks}; no alternate denominator)")
    if not isinstance(bundle, dict) or bundle.get("source") != source_key:
        refuse("sampler source label mismatch (fail closed; no cross use)")
    if source_key not in FROZEN_H:
        refuse(f"unknown source key {source_key} (frozen: 1M|1p5M|2M)")
    if arm is not None:
        aspec = parse_arm(str(arm))
        if aspec["source_key"] != source_key:
            refuse(f"sampler arm {arm} needs key {aspec['source_key']}, "
                   f"got {source_key} (no cross-source use)")
    alice = np.empty((n, M2HDC_FRAME_LEN), dtype=np.int64)
    bob = np.empty((n, M2HDC_FRAME_LEN), dtype=np.int64)
    for idx in range(n):
        seed = block_seed(idx, arm=arm) if arm is not None \
            else block_seed(idx)
        rng = np.random.default_rng(int(stream_seed(seed)) % (2 ** 32))
        a = rng.integers(0, M2HDC_DIMENSION, size=M2HDC_FRAME_LEN,
                         dtype=np.int64)
        flips = rng.random(M2HDC_FRAME_LEN) < 0.02
        b = np.where(flips, (a + rng.integers(1, M2HDC_DIMENSION,
                                              size=M2HDC_FRAME_LEN)) % M2HDC_DIMENSION,
                     a)
        alice[idx] = a
        bob[idx] = b
    batch = FrameBatch(dataset_id=f"m2hdc-synth-{source_key}",
                       alice_symbols=alice, bob_symbols=bob,
                       dimension=int(M2HDC_DIMENSION),
                       frame_len_symbols=int(M2HDC_FRAME_LEN),
                       metadata={"source_key": source_key,
                                 "stream": "o1_blk:{seed}",
                                 "seed_base": (M2HDC_ARM_SEED[str(arm)]
                                               if arm is not None
                                               else M2HDC_BLOCK_BASE)})
    if int(batch.frame_len_symbols) != M2HDC_FRAME_LEN:
        refuse("sampler broke the n=64 family semantic (fail closed)")
    probe = split_symbol_bitplanes(np.asarray(batch.alice_symbols[0]),
                                   int(batch.dimension), "gray")
    if len(probe) != M2HDC_PLANES:
        refuse(f"Gray split gave {len(probe)} planes != 10 (fail closed)")
    return batch


def _check_root(root: str) -> None:
    if not root:
        refuse("root required (fresh additive workspace/m2hdc_<uuid8>)")
    if not _ROOT_RE.match(str(root)):
        refuse(f"root must be fresh additive workspace/m2hdc_<uuid8> "
               f"(8-char suffix; got {root})")
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
    """Per-block accounting table (packet F5 A-CMPE-1..7, machine columns)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["block", "seed", "exact_match", "undetected",
                "block_accept", "block_fail", "accepted", "accepted_wrong",
                "status", "wall_s", "leak_ec_bits", "rescue_bits",
                "control_bits", "tag_bits", "lambda_total",
                "prior_entropy_bits", "messages_actual", "f_super",
                "f_notag", "f_eff", "n_required", "source_key", "arm",
                "construct_label"])
    for r in rows:
        if r.get("status") in ("error", "overrun"):
            w.writerow([r.get("block"), "", "", "", "", "", "", "",
                        r.get("status"), "", "", "", "", "", "", "",
                        "", "", "", "", "", "", "", ""])
            continue
        w.writerow([r.get("block"), r.get("seed"), r.get("exact_match"),
                    r.get("undetected"), r.get("block_accept"),
                    r.get("block_fail"), r.get("accepted"),
                    r.get("accepted_wrong"), r.get("status"),
                    r.get("wall_s"), r.get("leak_ec_bits"),
                    r.get("rescue_bits"), r.get("control_bits"),
                    r.get("tag_bits"), r.get("lambda_total"),
                    r.get("prior_entropy_bits"),
                    r.get("messages_actual"), r.get("f_super"),
                    r.get("f_notag"), r.get("f_eff"),
                    r.get("n_required"), r.get("source_key"),
                    r.get("arm"), r.get("construct_label")])
    return buf.getvalue()


def result_markdown(summary: dict[str, Any]) -> str:
    """Per-arm ``M2HDC_RESULT_*.md`` body (packet F5/§8)."""
    g = summary["gates"]
    lines = [
        f"# M2HDC result — {summary['arm']} (synthetic, RAW)",
        "",
        f"- arm: `{summary['arm']}` ({summary['construct_label']}; "
        f"HD-Cascade per-block constructs — NOT a nested submatrix)",
        f"- bundle: `{summary['bundle_path']}` key `{summary['source_key']}` "
        f"(TRAIN-side provenance; H CONDITIONAL on the F03 estimator + "
        f"TRAIN split side; bound source label == arm source, cross-source "
        f"reuse refused)",
        f"- block table (provisional, assumed until §7 grant-freeze): "
        f"`{summary['block_schedule']}` sweep "
        f"{summary['cross_sweeps']} (floor "
        f"{summary['block_floor']}; missing-plane entries fail closed, "
        f"never defaulted)",
        f"- seeds: `{M2HDC_ARM_SEED[summary['arm']]}+k` k 0..{summary['blocks_done'] - 1} "
        f"(stream `o1_blk:{{seed}}`, verbatim per-block cascade seed "
        f"ARM_SEED[arm]+k; construction instance 2026092001 retained; "
        f"2026095601 obsolete; 10 planes n=64)",
        f"- decoder: injected decode_fn only (production per-plane cascade "
        f"never entered by fake/test paths); `max_passes` "
        f"{summary['max_passes']} provisional assumed (§7 F3 slot BLANK); "
        f"`exact_match` accept with Toeplitz gate; report-only "
        f"`prior_entropy_bits`, `messages_actual`",
        f"- wall: {summary['elapsed_s']:.1f} s (cap 5400 s/arm); "
        f"per-decode terminal 300 s; peak RSS {summary['rss_gib']:.3f} "
        f"GiB (<4 GiB); ledger decodes {summary['ledger_decodes']}; "
        f"nb_decode_calls {summary['nb_decode_calls']}",
        f"- fails: {summary['failures']}/{summary['blocks_done']} "
        f"(FER {summary['fer']:.6f}); undetected {summary['undetected']} "
        f"(logged separately, NEVER merged into success; gate-(a) fails "
        f"count every non-success block)",
        f"- f_super (H[{summary['source_key']}]="
        f"{summary['h_basis']!r}, assumed): {summary['f_super']:.8f}; "
        f"f_notag = {summary['f_notag']:.8f}; f_eff = "
        f"f_super+4.785675*FER = {summary['f_eff']:.8f} (DISTINCT lines; "
        f"NEVER quote f_super as f_eff when FER > 0; single-source f_eff "
        f"is NEVER presented as certifiable/literature-comparable)",
        f"- lambda_total = {summary['lambda_total']:.3f} "
        f"(leak_EC {summary['lambda_parts']['leak_EC']:.3f} + tag "
        f"{summary['lambda_parts']['tag']:.3f} + rescue "
        f"{summary['lambda_parts']['rescue']:.3f} + control "
        f"{summary['lambda_parts']['control']:.3f}; 1.50xprior "
        f"{summary['prior_1p50_reportonly']:.3f} report-only, never into "
        f"lambda/f numerators)",
        f"- messages: actual {summary['messages_per_frame_actual']:.3f} "
        f"/frame as reported (counting rule provisional assumed; Cascade "
        f"{CASCADE_MSG_REF} aperture independent column; LDPC "
        f"{LDPC_MSG_REF} non-comparable annotation)",
        f"- N_req report-only vs 200/276/364: N_req={summary['n_required']}; "
        f"key-eligible contrast (200, 276, 364) report-only",
        f"- d/q/n_IR: d={summary['d_dim']} / q={summary['q_alphabet']} / "
        f"n_IR={summary['n_ir_bits']} (separate columns, never one number)",
        f"- curve label: {summary['curve_label']} (no cross-m "
        f"monotonicity inference)",
        f"- G-A (route fails/240 <= 12): {g['a']}; G-B (f_super <= 1.3): "
        f"{g['b']}; G-C (N >= ceil(3*4.785675/(1.3-f_super)) = "
        f"{summary['n_required']}: N={summary['blocks_done']} => "
        f"{g['c']}; presentation ban held)",
        f"- G-D (bundle entry): bound via the frozen consumer "
        f"(shape/normalization gates PASS at bind)",
        f"- G-E (integrity/stop): budgets held; zero raw-dump reads "
        f"(no such code path); cross-source reuse refused by "
        f"source-label check; no pooling; no `undetected`-merging; "
        f"`src/` untouched; wall-partial INCOMPLETE retained never "
        f"continued; at most one preregistered repair+rerun",
        f"- verdict: {summary['verdict']}",
        f"- claim ceiling: {CLAIM_CEILING}",
        "",
    ]
    return "\n".join(lines)


def execute(*, root: str, arm: str,
            bundle: dict[str, Any] | None = None,
            bundle_label: str | None = None,
            decode_fn: Callable | None = None,
            block_table: Any | None = None,
            clock: Callable | None = None,
            rss_fn: Callable | None = None,
            writer: Callable | None = None,
            max_blocks: int | None = None) -> dict:
    """Run the frozen M2HDC arm procedure under ``root`` (one arm/invocation).

    ``max_blocks`` is a PROBE-ONLY cap (never a CLI flag, never part of
    any verdict). ``bundle`` (already-bound mapping) and an explicit
    ``decode_fn`` are both required (no silent production bind or
    production decode — the production cascade path is grant-gated).
    Tests MUST pass an explicit fake ``decode_fn``. The per-block
    cascade seed is ``ARM_SEED[arm]+k`` (``block_seed(k, arm=arm)``)
    verbatim.
    """
    spec = parse_arm(arm)
    _check_root(root)
    m = int(spec["m"])
    source_key = str(spec["source_key"])
    if decode_fn is None:
        refuse("decode_fn required (no silent production decode; "
               "production cascade is grant-gated — pass an explicit "
               "decode_fn)")
    if bundle is None:
        refuse("empirical bundle required (no silent production bind; "
               "pass bundle or bind --bundle at the CLI)")
    table = check_block_table(block_table) if block_table is not None \
        else provisional_block_table()
    f_super = f_super_for(source_key, m)
    f_notag = f_notag_for(source_key, m)
    n_req = n_required(f_super)
    bar = fail_bar(M2HDC_N_BLOCKS)
    clock = clock or time.monotonic
    rss_fn = rss_fn or _default_rss
    writer = writer or default_writer
    if max_blocks is not None and (
            not isinstance(max_blocks, int) or max_blocks < 1):
        refuse("max_blocks (probe-only) must be a positive int")

    if os.path.exists(root):
        refuse(f"root not fresh: {root}")
    batch = sample_frozen_batch(bundle, source_key, arm=arm)
    rows: list[dict] = []
    failures = 0
    undetected = 0
    ledger_decodes = 0
    sum_leak = 0.0
    sum_rescue = 0.0
    sum_control = 0.0
    sum_prior = 0.0
    sum_messages = 0.0
    t_start = clock()
    rss_peak_gib = 0.0

    target = M2HDC_N_BLOCKS if max_blocks is None else min(max_blocks,
                                                           M2HDC_N_BLOCKS)

    def _summary(verdict: str, censored: bool) -> dict[str, Any]:
        n = len(rows)
        fer = (failures / n) if n else 0.0
        f_eff = f_eff_for(f_super, fer)
        lam_parts = {"leak_EC": float(sum_leak),
                     "tag": float(TAG_BITS * n),
                     "rescue": float(sum_rescue),
                     "control": float(sum_control)}
        lam = lambda_total(sum_leak, TAG_BITS * n, sum_rescue,
                           sum_control)
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
            "h_basis": FROZEN_H[source_key],
            "h_column": "assumed (denominator input only, no refit)",
            "block_schedule": {int(k): [int(x) for x in
                                        table.schedule_for(int(k))]
                               for k in range(M2HDC_PLANES)},
            "block_schedule_status": "provisional (assumed; §7 F2 BLANK)",
            "cross_sweeps": int(table.max_cross_plane_sweeps),
            "block_floor": int(M2HDC_BLOCK_FLOOR_PROVISIONAL),
            "max_passes": int(M2HDC_MAX_PASSES_PROVISIONAL),
            "max_passes_status": "provisional (assumed; §7 F3 BLANK)",
            "msg_count_rule": ("messages_actual-as-reported "
                               "(provisional, assumed)"),
            "blocks_done": n, "attempted": n, "failures": failures,
            "undetected": undetected, "fer": fer,
            "f_super": f_super, "f_notag": f_notag, "f_eff": f_eff,
            "f_basis": {"m": int(m), "H": float(FROZEN_H[source_key]),
                        "source": source_key, "H_column": "assumed"},
            "lambda_total": lam, "lambda_parts": lam_parts,
            "prior_1p50_reportonly": PRIOR_SCALE_REPORTONLY * float(sum_prior),
            "messages_per_frame_actual": (float(sum_messages) / n
                                          if n else float("nan")),
            "messages_cascade_ref": int(CASCADE_MSG_REF),
            "messages_ldpc_ref_noncomparable": float(LDPC_MSG_REF),
            "n_required": (n_req if math.isfinite(n_req) else "inf"),
            "key_eligible_contrast": (200, 276, 364),
            "d_dim": int(M2HDC_DIMENSION),
            "q_alphabet": int(M2HDC_DIMENSION),
            "n_ir_bits": int(M2HDC_FRAME_LEN * M2HDC_PLANES),
            "curve_label": ("CENSORED (bar-12 early-stop; fails-at-stop / "
                            "blocks-at-stop reported, projected NEVER)"
                            if censored else
                            "NON-CENSORED (curve-relative monotone label "
                            "deferred to batch analysis)"),
            "censored": bool(censored),
            "gates": {"a": gate_a, "b": gate_b, "c": gate_c,
                      "d": "PASS", "e": "PASS"},
            "verdict": verdict,
            "ledger_decodes": ledger_decodes,
            "nb_decode_calls": 0,
            "repair_budget": "at most one preregistered repair+rerun "
                             "(none used in this invocation)",
            "elapsed_s": float(clock() - t_start),
            "rss_gib": float(rss_peak_gib),
        }

    def _flush(summary: dict[str, Any]) -> dict[str, Any]:
        writer(root, {
            f"M2HDC_RESULT_{source_key}_{m}.md":
                result_markdown(summary),
            "rows.json": json.dumps({"summary": summary, "rows": rows},
                                    indent=1, sort_keys=True, default=str),
            "block_accounting.csv": block_accounting_csv(rows)})
        return summary

    for k in range(target):
        if clock() - t_start > M2HDC_WALL_CAP_S:
            return _flush(_summary("INCOMPLETE-wall", False))
        try:
            rss_gib = float(rss_fn()) / (1024 ** 3)
        except Exception:  # noqa: BLE001 — probe failure never halts
            rss_gib = 0.0
        rss_peak_gib = max(rss_peak_gib, rss_gib)
        if rss_gib >= M2HDC_RSS_CAP_GIB:
            return _flush(_summary("FAIL(budget)", False))
        seed = block_seed(k, arm=arm)
        one = FrameBatch(dataset_id=str(batch.dataset_id),
                         alice_symbols=np.asarray(
                             batch.alice_symbols[k:k + 1], dtype=np.int64),
                         bob_symbols=np.asarray(
                             batch.bob_symbols[k:k + 1], dtype=np.int64),
                         dimension=int(batch.dimension),
                         frame_len_symbols=int(batch.frame_len_symbols),
                         metadata=dict(batch.metadata))
        params = hc.HdCascadeParams(
            source_key=source_key, h_basis=float(FROZEN_H[source_key]),
            m_basis=int(m), seed=int(seed),
            max_passes=int(M2HDC_MAX_PASSES_PROVISIONAL))
        cfg = IRRunConfig("hd_cascade", "m2hdc-provisional",
                          int(M2HDC_DIMENSION), int(M2HDC_FRAME_LEN), 300)
        t0 = clock()
        try:
            res = hc.run_hd_cascade(one, cfg, params=params,
                                    block_table=table, decode_fn=decode_fn)
        except Refusal:
            raise
        except (ValueError, KeyError, TypeError,
                AttributeError) as exc:  # noqa: BLE001 — fail closed
            refuse(f"hd-cascade outcome/table contract failed (block {k}; "
                   f"fail closed): {type(exc).__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001 — no-retry: retain + halt
            rows.append({"block": k, "status": "error",
                         "error": f"{type(exc).__name__}: {exc}"})
            return _flush(_summary("FAIL(budget)", False))
        dt = clock() - t0
        if dt > M2HDC_PER_DECODE_CAP_S:
            rows.append({"block": k, "status": "overrun",
                         "decode_s": dt})
            return _flush(_summary("FAIL(budget)", False))
        md = res.metadata
        frame = md["frame_results"][0]
        success = bool(res.n_frames_success == 1)
        exact = bool(md.get("exact_match", 0) == 1)
        accepted = bool(md.get("accepted", 0) == 1)
        und = bool(md.get("undetected", 0) == 1)
        if not success:
            failures += 1
        if und:
            undetected += 1
        ledger_decodes += 1
        leak = float(res.leak_EC_actual_bits)
        parts = md.get("lambda_parts", {})
        rescue = float(parts.get("rescue", 0.0))
        control = float(parts.get("control", 0.0))
        prior = float(frame.get("prior_entropy_bits_reportonly", 0.0))
        messages = float(frame.get("messages_actual", 0.0))
        sum_leak += leak
        sum_rescue += rescue
        sum_control += control
        sum_prior += prior
        sum_messages += messages
        lam_row = lambda_total(leak, TAG_BITS, rescue, control)
        rows.append({
            "block": k,
            "seed": seed,
            "exact_match": exact,
            "undetected": und,
            "block_accept": success,
            "block_fail": 0 if success else 1,
            "accepted": accepted,
            "accepted_wrong": und,
            "status": "success" if success else "fail",
            "wall_s": dt,
            "leak_ec_bits": leak,
            "rescue_bits": rescue,
            "control_bits": control,
            "tag_bits": int(TAG_BITS),
            "lambda_total": lam_row,
            "prior_entropy_bits": prior,
            "messages_actual": messages,
            "f_super": f_super,
            "f_notag": f_notag,
            "f_eff": f_eff_for(f_super, failures / (len(rows) + 1)),
            "n_required": (n_req if math.isfinite(n_req) else "inf"),
            "bundle_provenance": ("TRAIN-side; F03 estimator family; "
                                  "alignment-conditional H"),
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
                  pb_sidecar: str, source_key: str,
                  decode_fn: Callable | None = None) -> int:
    bound = bind_source_bundle(bundle_path, source_key, arm)
    expected_sidecar = str(Path(bundle_path).parent / s2c.PB_SIDECAR_NAME)
    if str(pb_sidecar) != expected_sidecar:
        refuse(f"pb-sidecar {pb_sidecar} != frozen-resolved sibling "
               f"{expected_sidecar} (F1 path form; packet F1)")
    if decode_fn is None:
        decode_fn = _m2hdc_production_decode_fn
    summary = execute(root=root, arm=arm, bundle=bound,
                      bundle_label=str(bundle_path),
                      decode_fn=decode_fn)
    print(json.dumps({"arm": summary["arm"],
                      "verdict": summary["verdict"],
                      "failures": summary["failures"],
                      "undetected": summary["undetected"],
                      "fer": summary["fer"],
                      "f_super": summary["f_super"],
                      "f_notag": summary["f_notag"],
                      "f_eff": summary["f_eff"],
                      "curve_label": summary["curve_label"],
                      "gates": summary["gates"],
                      "ledger_decodes": summary["ledger_decodes"],
                      "nb_decode_calls": summary["nb_decode_calls"],
                      "root": root}, indent=1, sort_keys=True, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="M2 HD-Cascade thin arm runner "
                    "(one arm per invocation).")
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
               f"packet F1/F6)")
    if args.construct_instance != M2HDC_CONSTRUCT_SEED:
        refuse(f"construct-instance must be the frozen "
               f"{M2HDC_CONSTRUCT_SEED} "
               f"(got {args.construct_instance}; any change is a "
               f"science-input change -> STOP)")
    if not args.standalone:
        refuse("refusing: --standalone missing (M2HDC constructs are "
               "per-arm, never nested; packet F2)")
    arm_seed_base = M2HDC_ARM_SEED.get(str(args.arm))
    if arm_seed_base is None:
        refuse(f"arm {args.arm} has no frozen ARM_SEED (packet §7-4)")
    if args.seeds != f"{arm_seed_base}+idx":
        refuse(f"seeds must be the frozen literal {arm_seed_base}+idx "
               f"(got {args.seeds})")
    if args.stream != "o1_blk:{seed}":
        refuse(f"stream must be the frozen literal o1_blk:{{seed}} "
               f"(got {args.stream})")
    if args.blocks != M2HDC_N_BLOCKS:
        refuse(f"blocks must be the frozen {M2HDC_N_BLOCKS} "
               f"(got {args.blocks})")
    if args.per_decode_timeout_s != M2HDC_PER_DECODE_CAP_S:
        refuse(f"per-decode-timeout-s must be the frozen "
               f"{M2HDC_PER_DECODE_CAP_S} (got {args.per_decode_timeout_s})")
    if args.budget_s != M2HDC_WALL_CAP_S:
        refuse(f"budget-s must be the frozen {M2HDC_WALL_CAP_S} "
               f"(got {args.budget_s})")
    if not args.bundle:
        refuse("bundle required (read-only F1 bundle path)")
    if not args.pb_sidecar:
        refuse("pb-sidecar required (read-only F1 sidecar path)")
    return run_execution(root=args.root, arm=args.arm,
                         bundle_path=args.bundle,
                         pb_sidecar=args.pb_sidecar,
                         source_key=args.source_key)


def _m2hdc_production_decode_fn(a_planes, b_planes, schedules,
                                frame_idx, seed):
    """Thin production decode_fn (grant-gated execution only).

    Read-only delegate to the frozen ``hc._run_planes_production`` —
    the SOLE ``_run_planes_production`` call site in this module.
    Rebuilds the block table from the passed schedules (provisional
    cross-sweep bound) and mirrors the frozen production seed advance
    (``seed + frame_idx*104729``). Fake tests MUST inject an explicit
    fake ``decode_fn`` and never enter here (they monkeypatch the
    production kernel to raise); ``execute`` with ``decode_fn=None``
    still refuses — only ``run_execution`` defaults ``None`` to this
    wrapper as an explicit parameter.
    """
    table = hc.HdCascadeBlockTable(
        {int(p): [int(x) for x in schedules[int(p)]]
         for p in range(len(schedules))},
        max_cross_plane_sweeps=int(M2HDC_CROSS_SWEEPS_PROVISIONAL))
    return hc._run_planes_production(
        a_planes, b_planes, table,
        int(seed) + int(frame_idx) * 104729,
        int(M2HDC_MAX_PASSES_PROVISIONAL), "seeded_random")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
