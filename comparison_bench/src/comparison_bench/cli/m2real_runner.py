"""M2 real-frame runner for the two new-method arms (M2REAL, implementation-only).

Frozen contract: ``docs/research_cycles/M2-REALCOMP/PREREG_AND_AUTH.md``
(Acceptance ID ``G-M2-REALCOMP``) + ``M2-REALCOMP-PROMPT.md``. This file
is code only; it grants NOTHING. Execution needs a fresh explicit grant
+ Pre-EXECUTE + independent Pre-RESULT. NOT GRANTED at implementation
time (PREREG section 6 BLANK).

One invocation = one Jan-21 source, all four new-method arms on the M0
eval superframes: HD-Cascade x {m1, m2} + layered-binary x {m1, m2}
(single full-m decode per block). The NB column is an M0 artifact
reference (never re-run here).

What is reused READ-ONLY (zero frozen-module change):

- ``m0_realframe_runner.load_real_series`` / ``load_bundle`` /
  ``superframes`` / ``SOURCES`` / ``H_CORR`` — the frozen A1/R1 read,
  alignment, pairing, framing and eval-region chain (base X member only)
  plus the R1-corrected H basis for f accounting. The production
  defaults read real data; tests MUST inject fake series/bundle fns.
- ``m2hdc_arm_runner.provisional_block_table`` + ``M2HDC_ARM_SEED`` —
  the assumed-v1 block schedule ([8, 4] per plane, one cross sweep) and
  the 5701-series per-arm seed bases. Any deviation from assumed-v1 in
  the reused table refuses (Mueller true-value fill = STOP).
- ``m2lb_arm_runner.allocation_for`` / ``blind_table_for`` /
  ``blind_levels_for`` / ``M2LB_BLOCK_BASE`` — the verbatim F2/F3
  allocation ([equal-share + largest-remainder], sum == m, rows <= 64)
  and blind schedule (m_init = m-20 + [4 x 5]) plus the 5601 seed base.
- ``hd_cascade.run_hd_cascade`` + ``HdCascadeParams`` — the frozen
  HD-Cascade method body, called read-only with an explicitly injected
  ``hdc_decode_fn`` (fake tests MUST inject; production per-plane
  cascade never entered by fake tests).
- ``layered_binary.run_layered_binary`` + ``PlaneAllocation`` /
  ``BlindStageTable`` / ``LayeredParams`` — the frozen layered-binary
  method body, called read-only with explicitly injected
  ``lb_construct_fn`` / ``lb_decode_fn``.

Frozen real slicing (M2-REALCOMP section 1 F3, M0-measured): eval
superframes 205 / 287 / 383 per source (remainder 407 / 405 / 529
symbols dropped and reported); every 1024-symbol superframe is cut into
16 consecutive 64-symbol blocks (the 1024 -> 16x64 mapping is the single
assumed frame map; anything else refuses). A superframe counts success
iff all 16 blocks are exact; its leak is the 16-block sum. FER uses the
64-block denominator (3280 / 4592 / 6128); superframe counts are a
separate column, never the FER denominator.

Seeds: per-block seed = ARM base + global 64-block index ``g``
(``o1_blk:{seed}`` stream label; the stream derivation itself is the
frozen ``o1.stream_seed`` reuse). HDC uses the 5701-series per-arm bases
(same (source, m) -> base map as the synthetic HDC family); LB uses the
5601 base. The two method families are thereby on distinct series; real
global indices run far past the synthetic 0..239 range. Seeds drive
verification/permutation only: real arms contain zero synthetic
sampling. Any seed outside these rules refuses (STOP).

Accounting (M2-REALCOMP section 1, A-CMPE-1..7, machine columns):
attempted / exact_match (= success) / accepted / accepted_wrong
(= undetected, isolated, never success/FER); f_super / f_notag / f_eff
on the H_corr basis (M0 section 3; this-arm m); leak_EC + 64-bit tag
=> lambda_total (+ rescue / control / blind-stage single columns, never
merged); 1.50x prior opportunity-cost report-only (never into f);
wall (total/per-block) + peak RSS + per-block messages (Cascade 446 vs
LDPC 3.14 apertures kept independent, never compared); N_req
report-only vs key-eligible (200/276/364) contrast column; d / q /
n_IR separated; measured / assumed / projected / qualified labels (no
security observable => no SKR). D2 inputs are recorded with the frozen
rule restated; evaluation stays DEFERRED (needs M0 NB refs plus
independent Pre-RESULT). Every artifact carries the F9(i) annotation
and the section 8 claim ceiling.

No raw-dump reads outside the frozen m0 chain (no such import, path, or
extension literal anywhere here), no decoder/DE/graph-kernel change, no
refit path, no overwrite path, no resume/continue path (wall-partial
yields INCOMPLETE, retained, never continued), no writes outside the
fresh per-source root, never under ``results/`` or
``comparison_bench/outputs_comparison/``.
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

from comparison_bench.src.comparison_bench.cli import m0_realframe_runner as m0
from comparison_bench.src.comparison_bench.cli import m2hdc_arm_runner as m2hdc
from comparison_bench.src.comparison_bench.cli import m2lb_arm_runner as m2lb
from comparison_bench.src.comparison_bench.methods import hd_cascade as hc
from comparison_bench.src.comparison_bench.methods import layered_binary as lay
from comparison_bench.src.comparison_bench.types import FrameBatch, IRRunConfig

__all__ = [
    "SOURCES", "GRID", "DIMENSION", "SUPER_LEN", "BLOCK_LEN",
    "BLOCKS_PER_SUPERFRAME", "FROZEN_SLICE", "F_EFF_SLOPE", "TAG_BITS",
    "WALL_CAP_S", "PER_DECODE_CAP_S", "RSS_CAP_GIB", "ROOT_PREFIX",
    "FORBIDDEN_ROOT_PARTS", "HDC_SCHEDULE_ASSUMED_V1",
    "HDC_CROSS_SWEEPS_ASSUMED_V1", "HDC_FLOOR_ASSUMED_V1",
    "HDC_MAX_PASSES_ASSUMED_V1", "F9_NOTE", "REAL_CLAIM_CEILING",
    "D2_RULE", "KEY_ELIGIBLE_CONTRAST",
    "Refusal", "refuse", "hdc_base_for", "hdc_block_seed",
    "lb_block_seed", "stream_label", "f_super_for", "f_notag_for",
    "f_eff_for", "n_required", "lambda_total",
    "slice_real_blocks", "require_assumed_block_table",
    "block_accounting_csv", "result_markdown", "execute", "main",
]

#: Frozen sources (bundle keys double as CLI source keys).
SOURCES: tuple[str, ...] = ("1M", "1p5M", "2M")
#: Frozen m grid per source, read-only from the M0 contract (never copied).
GRID: dict[str, tuple[int, ...]] = {
    s: tuple(int(v) for v in m0.SOURCES[s]["arms"]) for s in SOURCES
}
#: Frozen symbol alphabet size (Gray-plane family; anything else = STOP).
DIMENSION = 1024
#: Frozen M0 superframe length in symbols.
SUPER_LEN = 1024
#: Frozen real-block length in symbols (n=64 family).
BLOCK_LEN = 64
#: Assumed frame map: one superframe = 16 consecutive 64-blocks, no remainder.
BLOCKS_PER_SUPERFRAME = SUPER_LEN // BLOCK_LEN
#: M0-measured slicing per source: superframes / dropped remainder / blocks.
FROZEN_SLICE: dict[str, dict[str, int]] = {
    "1M": {"superframes": 205, "remainder": 407, "blocks": 3280},
    "1p5M": {"superframes": 287, "remainder": 405, "blocks": 4592},
    "2M": {"superframes": 383, "remainder": 529, "blocks": 6128},
}
#: Frozen f_eff slope (read-only reuse of the frozen method literal).
F_EFF_SLOPE = hc.F_EFF_SLOPE_FROZEN
#: Frozen verification tag width.
TAG_BITS = hc.TAG_BITS_FROZEN
#: Frozen per-source wall budget in seconds (M2-REALCOMP section 2).
WALL_CAP_S = 5400
#: Frozen per-decode terminal in seconds (overrun = block fail, continue).
PER_DECODE_CAP_S = 300
#: Frozen RSS cap in GiB (overrun stops the source).
RSS_CAP_GIB = 4
#: Fresh additive M2REAL run-root prefix (PREREG section 3).
ROOT_PREFIX = "workspace/m2real_"
#: Roots the executor never writes under.
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")
#: Assumed-v1 Mueller pins (assumed until grant-freeze; any drift = STOP).
HDC_SCHEDULE_ASSUMED_V1: dict[int, list[int]] = {p: [8, 4] for p in range(10)}
HDC_CROSS_SWEEPS_ASSUMED_V1 = 1
HDC_FLOOR_ASSUMED_V1 = 1
HDC_MAX_PASSES_ASSUMED_V1 = 4
#: F9(i) annotation obligation (decision-log 2026-09-24; PREREG section 1).
F9_NOTE = "u2-only, u1 via argmax, u1 正确率未验证"
#: Claim ceiling (M2-REALCOMP section 8, verbatim).
REAL_CLAIM_CEILING = (
    "无安全观测量，只能写“实测纠错收益 / 公开开销收益”；"
    "禁止 SKR、secure-key、资格化、composable 安全、发表主张。"
    "单一构造实例（NB 实例 2026092001；新方法 pin 实例见快照）、"
    "单次采集、Jan-21 三源上的开发测量。"
    "对外数字只能来自真实帧实测本身。"
)
#: D2 rule (decision-log 2026-09-24 D2裁定; PREREG section 4, verbatim).
D2_RULE = (
    "(1) HD-Cascade 去 tag f 比 NB 低 > 0.05 ⇒ 如实报告，NB 改定位为"
    "“单向 1 条消息低时延”，给定信道时延下密钥吞吐对比；"
    "(2) 分层二元 ≥ NB（f 更优或持平）⇒ “高维必须用非二元码”叙事不成立，"
    "主线转向分层二元 + 信道建模；"
    "(3) 否则 ⇒ NB 主线进 M3（码设计）。D2 只决定后继主线方向，不是 P3 "
    "verdict，不放行任何 P3 门控动作，不产生 SKR/发表主张。"
)
#: Key-eligible certification contrast (report-only, never FER denominator).
KEY_ELIGIBLE_CONTRAST = (200, 276, 364)

_ROOT_RE = re.compile(r"^workspace/m2real_[0-9A-Za-z]{8}$")


class Refusal(SystemExit):
    """rc=2 pre-write refusal (unauthorized / invalid / gate-blocked)."""


def refuse(reason: str) -> Any:
    print(f"M2REAL-REFUSAL rc=2: {reason}", file=sys.stderr)
    raise Refusal(2)


# ---------------------------------------------------------------- seeds

def _hdc_bases() -> dict[tuple[str, int], int]:
    """(source_key, m) -> 5701-series base, read-only from the synthetic map."""
    out: dict[tuple[str, int], int] = {}
    for arm_label, base in m2hdc.M2HDC_ARM_SEED.items():
        spec = m2hdc.parse_arm(str(arm_label))
        out[(str(spec["source_key"]), int(spec["m"]))] = int(base)
    return out


def hdc_base_for(source_key: str, m: int) -> int:
    """Frozen HDC ARM base for (source, m); anything off-map refuses (STOP)."""
    bases = _hdc_bases()
    try:
        base = bases[(str(source_key), int(m))]
    except KeyError:
        refuse(f"no frozen HDC seed base for ({source_key}, m={m}) "
               f"(seed-outside-rule -> STOP)")
    if not 2026095701 <= int(base) <= 2026095706:
        refuse(f"HDC seed base {base} outside the frozen 5701 series "
               f"(seed-outside-rule -> STOP)")
    return int(base)


def hdc_block_seed(source_key: str, m: int, g: int) -> int:
    """HDC per-block seed: ARM base + global 64-block index g (递增)."""
    if isinstance(g, bool) or int(g) < 0:
        refuse("global block index must be a non-negative int")
    return int(hdc_base_for(source_key, m)) + int(g)


def lb_block_seed(g: int) -> int:
    """LB per-block seed: frozen 5601 base + global 64-block index g (递增)."""
    if int(m2lb.M2LB_BLOCK_BASE) != 2026095601:
        refuse("LB seed base drifted from frozen 2026095601 "
               "(seed-outside-rule -> STOP)")
    if isinstance(g, bool) or int(g) < 0:
        refuse("global block index must be a non-negative int")
    return int(m2lb.M2LB_BLOCK_BASE) + int(g)


def stream_label(seed: int) -> str:
    """Frozen stream label for a block seed (derivation is o1 reuse)."""
    return f"o1_blk:{int(seed)}"


# ---------------------------------------------------------------- accounting

def _h_corr(source_key: str) -> float:
    """R1-corrected H basis for f accounting (M0 section 3, read-only)."""
    try:
        return float(m0.H_CORR[str(source_key)])
    except KeyError:
        refuse(f"unknown source {source_key} (frozen: 1M|1p5M|2M)")


def f_super_for(source_key: str, m: int) -> float:
    """f_super = (5m+64)/(1024*H_corr[source]), this-arm m basis."""
    return float(5 * int(m) + 64) / (1024.0 * _h_corr(source_key))


def f_notag_for(source_key: str, m: int) -> float:
    """f_notag = 5m/(1024*H_corr[source]), this-arm m basis (D2 去tag口径)."""
    return float(5 * int(m)) / (1024.0 * _h_corr(source_key))


def f_eff_for(f_super: float, fer: float) -> float:
    """f_eff = f_super + 4.785675*FER on the same basis."""
    return float(f_super) + float(F_EFF_SLOPE) * float(fer)


def n_required(f_super: float) -> float:
    """Gate rule, report-only: N >= ceil(3*4.785675/(1.3-f_super))."""
    denom = 1.3 - float(f_super)
    if denom <= 0.0:
        return math.inf
    return float(math.ceil(3.0 * float(F_EFF_SLOPE) / denom))


def lambda_total(leak_ec: float, tag_bits: float = TAG_BITS,
                 rescue_bits: float = 0.0,
                 control_bits: float = 0.0) -> float:
    """Frozen decomposition: leak_EC + tag + rescue + control."""
    return (float(leak_ec) + float(tag_bits)
            + float(rescue_bits) + float(control_bits))


# ---------------------------------------------------------------- slicing

def slice_real_blocks(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    """Cut eval symbol arrays into superframes and 16x64 consecutive blocks.

    Returns superframe count, dropped remainder, and the ordered block
    list (global index g = sf*16+j, views into the input arrays).
    Anything outside the 1024 -> 16x64 map refuses (STOP).
    """
    a = np.asarray(a, dtype=np.int64).reshape(-1)
    b = np.asarray(b, dtype=np.int64).reshape(-1)
    if a.size == 0 or a.size != b.size:
        refuse("real series empty or Alice/Bob length mismatch (fail closed)")
    if int(a.min()) < 0 or int(a.max()) >= DIMENSION \
            or int(b.min()) < 0 or int(b.max()) >= DIMENSION:
        refuse("real symbols outside 0..1023 "
               "(new mapping beyond 1024 -> STOP)")
    if BLOCKS_PER_SUPERFRAME * BLOCK_LEN != SUPER_LEN:
        refuse("16x64 frame map broken (science-input change -> STOP)")
    sfs = m0.superframes(a, b, SUPER_LEN)
    blocks: list[dict[str, Any]] = []
    for s, (sa, sb) in enumerate(sfs):
        if sa.size != SUPER_LEN:
            refuse(f"superframe {s} length {sa.size} != 1024 (fail closed)")
        for j in range(BLOCKS_PER_SUPERFRAME):
            sl = slice(j * BLOCK_LEN, (j + 1) * BLOCK_LEN)
            blocks.append({"g": len(blocks), "superframe": s,
                           "block_in_sf": j, "a": sa[sl], "b": sb[sl]})
    return {"n_superframes": len(sfs),
            "remainder_symbols": int(a.size) - SUPER_LEN * len(sfs),
            "n_blocks": len(blocks), "blocks": blocks}


def require_assumed_block_table(table: Any) -> Any:
    """Fail closed unless the table is exactly assumed-v1 (Mueller guard).

    A filled Mueller true-value table no longer equals assumed-v1, so it
    refuses here (STOP) instead of being silently adopted.
    """
    try:
        planes = table.planes(10)
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed, never defaulted
        refuse(f"hd-cascade block table unusable (fail closed): "
               f"{type(exc).__name__}: {exc}")
    if list(planes) != list(range(10)):
        refuse("hd-cascade block table must cover planes 0..9 exactly")
    for p in range(10):
        try:
            sizes = [int(x) for x in table.schedule_for(int(p))]
        except Refusal:
            raise
        except Exception as exc:  # noqa: BLE001
            refuse(f"hd-cascade block table plane {p} unreadable "
                   f"(fail closed): {type(exc).__name__}: {exc}")
        if sizes != [int(x) for x in HDC_SCHEDULE_ASSUMED_V1[p]]:
            refuse(f"hd-cascade block table plane {p} {sizes} != assumed-v1 "
                   f"{HDC_SCHEDULE_ASSUMED_V1[p]} "
                   f"(Mueller true-value fill -> STOP, needs re-freeze)")
    if int(table.max_cross_plane_sweeps) != HDC_CROSS_SWEEPS_ASSUMED_V1:
        refuse("hd-cascade cross-sweep bound != assumed-v1 1 (-> STOP)")
    if int(HDC_MAX_PASSES_ASSUMED_V1) != 4 \
            or int(HDC_FLOOR_ASSUMED_V1) != 1:
        refuse("assumed-v1 pass/floor pin drifted (-> STOP)")
    return table


# ---------------------------------------------------------------- outputs

_CSV_COLS = ["source", "family", "m", "mode", "block", "superframe",
             "block_in_sf", "seed", "stream", "exact_match", "undetected",
             "block_accept", "block_fail", "accepted", "accepted_wrong",
             "status", "wall_s", "leak_ec_bits", "blind_stage_bits",
             "rescue_bits", "control_bits", "tag_bits", "lambda_total",
             "prior_entropy_bits", "prior_1p50_reportonly",
             "messages_actual", "f_super", "f_notag", "f_eff",
             "n_required", "H_basis", "H_column", "d_dim", "q_alphabet",
             "n_ir_bits", "construct_label", "bundle_path"]


def block_accounting_csv(rows: list[dict]) -> str:
    """Per-64-block accounting table (A-CMPE-1..7 machine columns)."""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=_CSV_COLS, extrasaction="ignore",
                       lineterminator="\n")
    w.writeheader()
    for r in rows:
        out = dict(r)
        if out.get("status") in ("error", "overrun"):
            w.writerow({"block": out.get("block"),
                        "superframe": out.get("superframe"),
                        "status": out.get("status")})
            continue
        w.writerow(out)
    return buf.getvalue()


def result_markdown(summary: dict[str, Any]) -> str:
    """Per-source ``M2REAL_RESULT_*.md`` body (PREREG sections 1/4/8)."""
    exp, act = summary["slice_expected"], summary["slice_actual"]
    lines = [
        f"# M2REAL result — {summary['source']} ({summary['verdict']})",
        "",
        f"- member: `{summary['provenance'].get('member')}`; "
        f"offset {summary['provenance'].get('offset_ps')} ps; "
        f"dataset `{summary['provenance'].get('dataset')}`",
        f"- eval pairs {summary['provenance'].get('n_pairs_eval')} -> "
        f"superframes {act['superframes']} (expected {exp['superframes']}; "
        f"match {summary['slice_match']}; remainder {act['remainder']} "
        f"symbols dropped, expected {exp['remainder']})",
        f"- 64-blocks {act['blocks']} (expected {exp['blocks']}; "
        f"FER denominator = blocks; superframe counts separate, "
        f"never FER denominator)",
        f"- bundle: `{summary['bundle_path']}` (prior provenance only; "
        f"real arms decode prior-free; never refit)",
        f"- H basis for f: H_corr[{summary['source']}] = "
        f"{summary['H_corr']} (M0 section 3, measured R1-corrected; "
        f"synthetic F03 H used ONLY inside verbatim allocation/params "
        f"validators, labeled assumed, never into f)",
        "",
        "| family | m | mode | blocks | fails | undetected | FER(block) | "
        "sf_success/sf_total | f_super | f_notag | f_eff | lambda_total |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in summary["arms"]:
        lines.append(
            f"| {s['family']} | {s['m']} | {s['mode']} | {s['blocks_done']} | "
            f"{s['fails']} | {s['undetected']} | {s['fer_blocks']:.6f} | "
            f"{s['sf_success']}/{s['sf_total']} | {s['f_super']:.8f} | "
            f"{s['f_notag']:.8f} | {s['f_eff']:.8f} | "
            f"{s['lambda_total']:.3f} |")
    lines += [
        "",
        f"- f_super / f_notag / f_eff are DISTINCT lines (never quote "
        f"f_super as f_eff when FER > 0; single-source f_eff NEVER "
        f"certifiable/literature-comparable).",
        f"- D2 worksheet ({summary['d2']['status']}): rule: {D2_RULE}",
    ]
    for arm_d2 in summary["d2"]["arm_inputs"]:
        lines.append(
            f"  - {arm_d2['family']}-m{arm_d2['m']}: f_notag = "
            f"{arm_d2['f_notag']:.8f} (D2 去tag口径 input).")
    lines += [
        f"- D2 needs M0 NB refs (pointer only, no copied numbers: "
        f"`docs/research_cycles/M0-REALFRAME/RESULT.md`) + independent "
        f"Pre-RESULT; no D2 branch evaluated here.",
        f"- F9(i) annotation (mandatory on every M0-number reference): "
        f"{F9_NOTE}.",
        f"- claim ceiling: {REAL_CLAIM_CEILING}",
        f"- measures: blocks measured; H_corr measured (M0/R1); "
        f"Mueller pins assumed-v1; finite-limit projected (empty); "
        f"qualified (empty, no SKR).",
        f"- wall {summary['wall_s']:.1f} s (cap {WALL_CAP_S} s/source); "
        f"per-decode terminal {PER_DECODE_CAP_S} s; peak RSS "
        f"{summary['rss_gib']:.3f} GiB (<{RSS_CAP_GIB} GiB); "
        f"decodes {summary['decodes']}; 1 CPU.",
        "",
    ]
    return "\n".join(lines)


def _check_root(root: str) -> None:
    if not root or not _ROOT_RE.match(str(root)):
        refuse(f"root must be fresh additive workspace/m2real_<uuid8> "
               f"(8-char suffix; got {root})")
    if any(p in Path(str(root)).parts for p in FORBIDDEN_ROOT_PARTS):
        refuse(f"root under forbidden tree (results/outputs_comparison): "
               f"{root}")


def default_writer(root: str, files: dict[str, str]) -> None:
    """Single-writer overwrite-in-place (root freshness checked pre-write)."""
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


# ---------------------------------------------------------------- execution

def _one_frame_batch(source_key: str, a64: np.ndarray, b64: np.ndarray,
                     seed: int, g: int, sf: int) -> FrameBatch:
    return FrameBatch(
        dataset_id=f"m2real-{source_key}",
        alice_symbols=np.asarray(a64, dtype=np.int64).reshape(1, -1),
        bob_symbols=np.asarray(b64, dtype=np.int64).reshape(1, -1),
        dimension=int(DIMENSION), frame_len_symbols=int(BLOCK_LEN),
        metadata={"source_key": source_key, "stream": stream_label(seed),
                  "seed": int(seed), "block": int(g),
                  "superframe": int(sf)})


def _hdc_block(source_key: str, m: int, a64: np.ndarray, b64: np.ndarray,
               g: int, sf: int, table: Any,
               decode_fn: Callable) -> tuple[dict[str, Any], float]:
    """One real 64-block through the frozen HD-Cascade body (read-only)."""
    seed = hdc_block_seed(source_key, m, g)
    batch = _one_frame_batch(source_key, a64, b64, seed, g, sf)
    params = hc.HdCascadeParams(
        source_key=source_key, h_basis=float(hc.FROZEN_H[source_key]),
        m_basis=int(m), seed=int(seed),
        max_passes=int(HDC_MAX_PASSES_ASSUMED_V1))
    cfg = IRRunConfig("hd_cascade", "m2real-assumed-v1", int(DIMENSION),
                      int(BLOCK_LEN), 300)
    res = hc.run_hd_cascade(batch, cfg, params=params, block_table=table,
                            decode_fn=decode_fn)
    md = res.metadata
    frame = md["frame_results"][0]
    return {"exact_match": bool(md.get("exact_match", 0) == 1),
            "accepted": bool(md.get("accepted", 0) == 1),
            "undetected": bool(md.get("undetected", 0) == 1),
            "success": bool(res.n_frames_success == 1),
            "leak_ec_bits": float(res.leak_EC_actual_bits),
            "rescue_bits": float(frame.get("rescue_bits", 0.0)),
            "control_bits": float(frame.get("control_bits", 0.0)),
            "prior_entropy_bits": float(
                frame.get("prior_entropy_bits_reportonly", 0.0)),
            "messages_actual": float(frame.get("messages_actual", 0.0))}, \
        float(seed)


def _lb_block(source_key: str, m: int, a64: np.ndarray, b64: np.ndarray,
              g: int, sf: int, allocation: dict[int, int],
              blind_tab: dict[str, Any], construct_fn: Callable,
              decode_fn: Callable) -> dict[str, Any]:
    """One real 64-block through the frozen layered-binary body (read-only).

    Single full-m decode per block (matched semantics); the verbatim
    blind schedule validates the frozen rescue-disclosure frame and is
    recorded report-only (no incremental rescue run on real blocks).
    """
    seed = lb_block_seed(g)
    batch = _one_frame_batch(source_key, a64, b64, seed, g, sf)
    alloc = lay.PlaneAllocation(
        source_key=source_key, h_basis=float(lay.FROZEN_H[source_key]),
        m_basis=int(m),
        plane_rows={int(k): int(v) for k, v in allocation.items()})
    alloc.validated(10)
    stages = lay.BlindStageTable(
        m_init=int(blind_tab["m_init"]),
        delta_steps=[int(x) for x in blind_tab["delta_steps"]]).validated()
    params = lay.LayeredParams(source_key=source_key, tag_bits=int(TAG_BITS),
                               max_iter=int(m2lb.M2LB_MAX_ITER),
                               streak=int(m2lb.M2LB_STREAK)).validated()
    cfg = IRRunConfig("layered_binary", "m2real-matched", int(DIMENSION),
                      int(BLOCK_LEN), 300)
    res = lay.run_layered_binary(batch, cfg, allocation=alloc, stages=stages,
                                 params=params, construct_fn=construct_fn,
                                 decode_fn=decode_fn)
    md = res.metadata
    frame = md["frame_results"][0]
    return {"exact_match": bool(md.get("exact_match", 0) == 1),
            "accepted": bool(md.get("accepted", 0) == 1),
            "undetected": bool(md.get("undetected", 0) == 1),
            "success": bool(res.n_frames_success == 1),
            "leak_ec_bits": float(frame.get("leak_EC_bits", 0.0)),
            "blind_stage_bits": [float(x) for x in
                                 frame.get("blind_stage_bits", [])],
            "rescue_bits": float(frame.get("rescue_bits", 0.0)),
            "control_bits": float(frame.get("control_bits", 0.0)),
            "prior_entropy_bits": float(
                frame.get("prior_entropy_bits_reportonly", 0.0)),
            "messages_actual": float(frame.get("messages_actual", 0.0))}


def execute(*, source: str, root: str,
            series_fn: Callable[[str], dict[str, Any]] | None = None,
            bundle_fn: Callable[[str], dict[str, Any]] | None = None,
            hdc_decode_fn: Callable | None = None,
            lb_construct_fn: Callable | None = None,
            lb_decode_fn: Callable | None = None,
            clock: Callable[[], float] | None = None,
            rss_fn: Callable[[], int] | None = None,
            writer: Callable | None = None,
            max_blocks: int | None = None) -> dict[str, Any]:
    """Run all four new-method arms of one source over the real eval blocks.

    Tests MUST inject fake ``series_fn`` / ``bundle_fn`` /
    ``hdc_decode_fn`` / ``lb_construct_fn`` / ``lb_decode_fn``; the
    production defaults read real data (grant-gated). ``max_blocks`` is
    a PROBE-ONLY per-arm cap (never a CLI flag, never part of any
    verdict beyond the PROBE-truncated label).
    """
    if source not in SOURCES:
        refuse(f"unknown source {source} (frozen: 1M|1p5M|2M)")
    _check_root(root)
    if hdc_decode_fn is None or lb_decode_fn is None \
            or lb_construct_fn is None:
        refuse("explicit hdc_decode_fn + lb_construct_fn + lb_decode_fn "
               "required (no silent production decode; grant-gated)")
    if max_blocks is not None and (
            not isinstance(max_blocks, int) or isinstance(max_blocks, bool)
            or max_blocks < 1):
        refuse("max_blocks (probe-only) must be a positive int")
    series_fn = series_fn or m0.load_real_series
    bundle_fn = bundle_fn or m0.load_bundle
    clock = clock or time.monotonic
    rss_fn = rss_fn or _default_rss
    writer = writer or default_writer
    if os.path.exists(root):
        refuse(f"root not fresh: {root}")

    table = require_assumed_block_table(m2hdc.provisional_block_table())
    h_corr = _h_corr(source)
    exp = FROZEN_SLICE[source]

    t_start = clock()
    series = series_fn(source)
    try:
        a_all, b_all = series["a"], series["b"]
        prov = {k: v for k, v in series.items() if k not in ("a", "b")}
    except (KeyError, TypeError, AttributeError) as exc:
        refuse(f"real series contract broken (fail closed): "
               f"{type(exc).__name__}: {exc}")
    sliced = slice_real_blocks(a_all, b_all)
    bundle = bundle_fn(source)
    if not isinstance(bundle, dict):
        refuse("empirical bundle contract broken (fail closed)")
    bundle_path = str(bundle.get("path", "<injected>"))
    blocks = sliced["blocks"]
    actual = {"superframes": sliced["n_superframes"],
              "remainder": sliced["remainder_symbols"],
              "blocks": sliced["n_blocks"]}
    slice_match = (actual["superframes"] == exp["superframes"]
                   and actual["remainder"] == exp["remainder"]
                   and actual["blocks"] == exp["blocks"])

    rows: list[dict] = []
    arms_out: list[dict] = []
    verdict = "COMPLETE"
    rss_peak = 0.0

    def summary() -> dict[str, Any]:
        return {
            "source": source, "verdict": verdict,
            "provenance": {"dataset": prov.get("dataset"),
                           "member": prov.get("ttbin"),
                           "offset_ps": prov.get("offset_ps"),
                           "n_pairs_total": prov.get("n_pairs_total"),
                           "n_pairs_eval": prov.get("n_pairs_eval"),
                           "eval_first_frame": prov.get("eval_first_frame"),
                           "read_wall_s": prov.get("read_wall_s")},
            "bundle_path": bundle_path, "H_corr": h_corr,
            "H_column": "measured (M0 section 3, R1-corrected)",
            "slice_expected": dict(exp), "slice_actual": dict(actual),
            "slice_match": bool(slice_match),
            "arms": list(arms_out),
            "d2": {"status": "DEFERRED (needs M0 NB refs + Pre-RESULT)",
                   "rule": D2_RULE,
                   "arm_inputs": [
                       {"family": s["family"], "m": s["m"],
                        "f_notag": s["f_notag"], "f_super": s["f_super"]}
                       for s in arms_out]},
            "f9_note": F9_NOTE, "claim_ceiling": REAL_CLAIM_CEILING,
            "budgets": {"wall_cap_s": WALL_CAP_S,
                        "per_decode_cap_s": PER_DECODE_CAP_S,
                        "rss_cap_gib": RSS_CAP_GIB, "cpus": 1},
            "wall_s": clock() - t_start, "rss_gib": rss_peak,
            "decodes": len(rows)}

    def flush() -> None:
        s = summary()
        _check_root_fresh_or_exists(root)
        writer(root, {f"M2REAL_RESULT_{source}.md": result_markdown(s),
                      "rows.json": json.dumps(
                          {"summary": s, "rows": rows}, indent=1,
                          default=str),
                      "block_accounting.csv": block_accounting_csv(rows)})

    arm_specs: list[tuple[str, int]] = (
        [("hdc", m) for m in GRID[source]]
        + [("lb", m) for m in GRID[source]])
    for family, m in arm_specs:
        f_super = f_super_for(source, m)
        f_notag = f_notag_for(source, m)
        n_req = n_required(f_super)
        if family == "lb":
            allocation = m2lb.allocation_for(source, m)
            blind_tab = m2lb.blind_table_for(m)
            m2lb.blind_levels_for(m)
            construct_label = f"M2REAL-{source}-S{m}-layered"
            mode = "matched"
        else:
            allocation, blind_tab = {}, {}
            construct_label = f"M2REAL-{source}-S{m}-hdcascade"
            mode = "cascade"
        fails = und = 0
        sum_leak = sum_rescue = sum_control = sum_prior = sum_msg = 0.0
        arm_wall = 0.0
        sf_success = 0
        sf_total = 0
        sf_open_ok = True
        arm_rows_start = len(rows)
        target = sliced["n_blocks"] if max_blocks is None else min(
            max_blocks, sliced["n_blocks"])
        arm_verdict = "COMPLETE"
        for blk in blocks[:target]:
            if clock() - t_start > WALL_CAP_S:
                verdict = arm_verdict = "INCOMPLETE-wall"
                break
            try:
                rss_gib = float(rss_fn()) / (1024 ** 3)
            except Exception:  # noqa: BLE001 — probe failure never halts
                rss_gib = 0.0
            rss_peak = max(rss_peak, rss_gib)
            if rss_gib >= RSS_CAP_GIB:
                verdict = arm_verdict = "FAIL(budget-rss)"
                break
            g, sf = int(blk["g"]), int(blk["superframe"])
            t0 = clock()
            try:
                if family == "hdc":
                    out = _hdc_block(source, m, blk["a"], blk["b"], g, sf,
                                     table, hdc_decode_fn)[0]
                    seed = hdc_block_seed(source, m, g)
                    blind_bits: list[float] = []
                else:
                    out = _lb_block(source, m, blk["a"], blk["b"], g, sf,
                                    allocation, blind_tab, lb_construct_fn,
                                    lb_decode_fn)
                    seed = lb_block_seed(g)
                    blind_bits = [float(x)
                                  for x in out["blind_stage_bits"]]
            except Refusal:
                raise
            except Exception as exc:  # noqa: BLE001 — no-retry: retain + halt
                rows.append({"block": g, "superframe": sf,
                             "status": "error",
                             "error": f"{type(exc).__name__}: {exc}"})
                verdict = arm_verdict = "FAIL(budget)"
                break
            dt = clock() - t0
            arm_wall += dt
            overrun = dt > PER_DECODE_CAP_S  # terminal: fail, never re-run
            success = bool(out["success"]) and not overrun
            if not success:
                fails += 1
            if bool(out["undetected"]) and not overrun:
                und += 1
            leak = float(out["leak_ec_bits"])
            rescue = float(out["rescue_bits"])
            control = float(out["control_bits"])
            prior = float(out["prior_entropy_bits"])
            messages = float(out["messages_actual"])
            sum_leak += leak
            sum_rescue += rescue
            sum_control += control
            sum_prior += prior
            sum_msg += messages
            fer_now = fails / (len(rows) - arm_rows_start + 1)
            rows.append({
                "source": source, "family": family, "m": m, "mode": mode,
                "block": g, "superframe": sf,
                "block_in_sf": int(blk["block_in_sf"]), "seed": seed,
                "stream": stream_label(seed),
                "exact_match": bool(out["exact_match"]) and not overrun,
                "undetected": bool(out["undetected"]) and not overrun,
                "block_accept": success, "block_fail": 0 if success else 1,
                "accepted": bool(out["accepted"]) and not overrun,
                "accepted_wrong": bool(out["undetected"]) and not overrun,
                "status": "overrun" if overrun
                else ("success" if success else "fail"),
                "wall_s": dt, "leak_ec_bits": leak,
                "blind_stage_bits": "|".join(f"{x:.6f}"
                                             for x in blind_bits),
                "rescue_bits": rescue, "control_bits": control,
                "tag_bits": int(TAG_BITS),
                "lambda_total": lambda_total(leak, TAG_BITS, rescue,
                                            control),
                "prior_entropy_bits": prior,
                "prior_1p50_reportonly": 1.50 * prior,
                "messages_actual": messages,
                "f_super": f_super, "f_notag": f_notag,
                "f_eff": f_eff_for(f_super, fer_now),
                "n_required": (n_req if math.isfinite(n_req) else "inf"),
                "H_basis": h_corr,
                "H_column": "measured (M0 section 3, R1-corrected)",
                "d_dim": int(DIMENSION),
                "q_alphabet": (int(DIMENSION) if family == "hdc"
                               else "2x10 layers"),
                "n_ir_bits": int(BLOCK_LEN * 10),
                "construct_label": construct_label,
                "bundle_path": bundle_path})
            if int(blk["block_in_sf"]) == 0:
                sf_open_ok = True
                sf_total += 1
            sf_open_ok = sf_open_ok and success
            if int(blk["block_in_sf"]) == BLOCKS_PER_SUPERFRAME - 1:
                sf_success += int(sf_open_ok)
            if int(blk["block_in_sf"]) == BLOCKS_PER_SUPERFRAME - 1:
                flush()
        n_done = len(rows) - arm_rows_start
        fer = (fails / n_done) if n_done else 0.0
        if arm_verdict == "COMPLETE" and max_blocks is not None:
            arm_verdict = "PROBE-truncated"
            if verdict == "COMPLETE":
                verdict = "PROBE-truncated"
        elif verdict != "COMPLETE":
            arm_verdict = verdict
        lam_parts = {"leak_EC": float(sum_leak),
                     "tag": float(TAG_BITS * n_done),
                     "rescue": float(sum_rescue),
                     "control": float(sum_control)}
        arms_out.append({
            "family": family, "m": m, "mode": mode,
            "construct_label": construct_label,
            "blocks_done": n_done, "superframes_done": sf_total,
            "fails": fails, "undetected": und, "fer_blocks": fer,
            "sf_success": sf_success, "sf_total": sf_total,
            "f_super": f_super, "f_notag": f_notag,
            "f_eff": f_eff_for(f_super, fer),
            "f_basis": {"m": int(m), "H": h_corr, "source": source,
                        "H_column": "measured (M0 section 3)"},
            "lambda_total": lambda_total(sum_leak, TAG_BITS * n_done,
                                        sum_rescue, sum_control),
            "lambda_parts": lam_parts,
            "prior_1p50_reportonly": 1.50 * float(sum_prior),
            "messages_per_frame_actual": (float(sum_msg) / n_done
                                          if n_done else float("nan")),
            "messages_cascade_ref": 446,
            "messages_ldpc_ref_noncomparable": 3.14,
            "n_required": (n_req if math.isfinite(n_req) else "inf"),
            "key_eligible_contrast": list(KEY_ELIGIBLE_CONTRAST),
            "d_dim": int(DIMENSION),
            "q_alphabet": (int(DIMENSION) if family == "hdc"
                           else "2x10 layers"),
            "n_ir_bits": int(BLOCK_LEN * 10),
            "seed_base": (hdc_base_for(source, m) if family == "hdc"
                          else int(m2lb.M2LB_BLOCK_BASE)),
            "stream": "o1_blk:{seed}",
            "block_table": ("assumed-v1 [8,4]/cross1/floor1/max_passes4"
                            if family == "hdc" else None),
            "block_table_status": ("provisional (assumed-v1; Mueller "
                                   "待澄清表待核对)" if family == "hdc"
                                   else None),
            "allocation_status": ("verbatim F2 (equal-share + "
                                  "largest-remainder)" if family == "lb"
                                  else None),
            "blind_status": ("verbatim F3 (m_init=m-20 + [4 x 5]; "
                             "single full-m decode, rescue recorded "
                             "report-only)" if family == "lb" else None),
            "verdict": arm_verdict, "wall_s": arm_wall})
        flush()
        if verdict in ("INCOMPLETE-wall", "FAIL(budget-rss)",
                       "FAIL(budget)"):
            break
    flush()
    return summary()


def _check_root_fresh_or_exists(root: str) -> None:
    _check_root(root.replace("\\", "/"))


def _production_lb_construct_fn(n_len: int, m_rows: int, seed_const: int,
                                frame_idx: int, plane: int) -> dict[str, Any]:
    """Production LB construct adapter (grant-gated CLI only; read-only).

    Thin lay-convention -> ``m2lb.construct_plane_production`` delegate:
    seed is the frozen ``M2LB_CONSTRUCT_SEED`` instance (``seed_const``;
    the per-batch ``frame_idx`` is always 0 in the m2real single-frame
    blocks, so the frozen instance is reused per block by construction).
    ``n_len`` is the frozen 64 (validated by the method body). Never
    entered by fake tests (they inject an explicit fake).
    """
    return m2lb.construct_plane_production(int(m_rows), int(seed_const),
                                           int(m2lb.M2LB_MAX_TRIALS),
                                           int(plane))


def _production_lb_decode_fn(a_planes: Any, b_planes: Any,
                             constructions: Any, stages: Any,
                             frame_idx: int, max_iter: int,
                             streak: int) -> dict[str, Any]:
    """Production LB decode adapter (grant-gated CLI only; read-only).

    Thin lay-convention -> ``m2lb`` explicit-fallback delegate: rebuilds
    the matched single-full-m ``stage_ctx`` from the verbatim blind table
    (``m_target = m_init + 20``) and calls
    ``m2lb.spa_decode_with_explicit_fallback`` read-only (ldpc present ->
    ``spa_decode_production`` transparent true body; ldpc absent -> the
    assumed numpy-minsum fallback branch, retained). Adds the lay
    ``"construction"`` key (report-only ``{}``; m2lb outcomes carry the
    13-key set without it). Never entered by fake tests.
    """
    m_init = int(stages.m_init)
    m_target = m_init + 20
    stage_ctx = {"mode": "matched", "m_target": m_target,
                 "m_stage": m_target, "stage_idx": 0,
                 "delta_steps": [int(x) for x in stages.delta_steps],
                 "m_init": m_init}
    out = dict(m2lb.spa_decode_with_explicit_fallback(
        a_planes, b_planes, constructions, stage_ctx, int(frame_idx),
        int(max_iter), int(streak)))
    out.setdefault("construction", {})
    return out


def main(argv: list[str] | None = None, *,
         series_fn: Callable[[str], dict[str, Any]] | None = None,
         bundle_fn: Callable[[str], dict[str, Any]] | None = None,
         hdc_decode_fn: Callable | None = None,
         lb_construct_fn: Callable | None = None,
         lb_decode_fn: Callable | None = None,
         clock: Callable[[], float] | None = None,
         rss_fn: Callable[[], int] | None = None,
         writer: Callable | None = None,
         max_blocks: int | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--source", default=None,
                   choices=list(SOURCES) + [None])
    p.add_argument("--root", default="",
                   help="fresh workspace/m2real_<uuid8> root")
    p.add_argument("--execute-real", action="store_true")
    p.add_argument("--execution-authorized", action="store_true")
    p.add_argument("--with-production-fns", action="store_true",
                   help="explicitly wire the frozen production HDC/LB "
                        "construct+decode fns (grant-gated; absent refuses)")
    args = p.parse_args(argv)
    if not args.execute_real:
        refuse("real-data execution needs --execute-real "
               "(grant in PREREG section 6)")
    if not args.execution_authorized:
        refuse("real-data execution needs --execution-authorized "
               "(grant in PREREG section 6)")
    if not args.with_production_fns:
        refuse("real-data execution needs --with-production-fns "
               "(explicit production-fn wiring; default refuses)")
    hdc_fn = (hdc_decode_fn if hdc_decode_fn is not None
              else m2hdc._m2hdc_production_decode_fn)
    lb_c_fn = (lb_construct_fn if lb_construct_fn is not None
               else _production_lb_construct_fn)
    lb_d_fn = (lb_decode_fn if lb_decode_fn is not None
               else _production_lb_decode_fn)
    if hdc_fn is None or lb_c_fn is None or lb_d_fn is None:
        refuse("explicit hdc_decode_fn + lb_construct_fn + lb_decode_fn "
               "required (no silent production decode; grant-gated)")
    s = execute(source=args.source, root=args.root,
                series_fn=series_fn, bundle_fn=bundle_fn,
                hdc_decode_fn=hdc_fn,
                lb_construct_fn=lb_c_fn, lb_decode_fn=lb_d_fn,
                clock=clock, rss_fn=rss_fn, writer=writer,
                max_blocks=max_blocks)
    print(json.dumps({"source": s["source"], "verdict": s["verdict"],
                      "root": args.root,
                      "arms": [{k: a[k] for k in (
                          "family", "m", "mode", "blocks_done", "fails",
                          "undetected", "fer_blocks", "sf_success",
                          "sf_total", "f_super", "f_notag", "f_eff")}
                          for a in s["arms"]]}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
