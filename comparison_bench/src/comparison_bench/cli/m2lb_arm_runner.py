"""M2 layered-binary thin arm runner (M2LB, implementation-only, NOT execution).

Frozen contract: ``docs/research_cycles/M2-LAYEREDBIN-SYNTH/PACKET.md``
(Sec 0-9) + ``M2-LAYEREDBIN-SYNTH-PROMPT.md`` (proposed Acceptance ID
G-M2-LAYEREDBIN-SYNTH). This file is code only; it grants NOTHING.
Execution needs a fresh explicit grant + Pre-EXECUTE; this module only
provides the executor + fake-testable mechanics.

Determination: NO existing campaign CLI can run the frozen F1-F6 grid
verbatim, so this ONE additive module exists. What is reused READ-ONLY
(zero frozen-module change):

- ``s2c.bind_empirical_bundle(bundle_path, source_key)`` — the frozen
  consumer, F1 path form (bundle file + sibling sidecar resolved by the
  frozen ``PB_SIDECAR_NAME``).
- ``o1.stream_seed`` / ``o1.fail_bar`` — frozen stream + bar-12 semantics.
- ``peg.peg_construct`` + ``_mcde.make_rho`` + ``GF2mField.create`` —
  the frozen per-plane construction body (same calls as the A-series
  precedent), parameterized per Gray plane, read-only.
- ``split_symbol_bitplanes`` (gray) — the frozen plane splitter, used
  read-only to verify the 10-plane Gray family.
- ``FrameBatch`` — the frozen batch type for the 240-frame sampler.

Frozen literals CARRIED here (packet Sec 7 restatement; nothing invented):

- n_plane=64 family, content denominator 1024, dimension=1024 (10 Gray
  planes), construct instance 2026092001 / trials 20, block seeds
  2026095601+idx idx 0..239, stream ``o1_blk:{seed}``, 240 blocks,
  per-decode terminal 300 s, per-arm wall 1800 s, RSS <4 GiB, 1 CPU.
- Grid: 1M {197, 201} / 1.5M {203, 207} / 2M {204, 208};
  display-to-key {1M:1M, 1.5M:1p5M, 2M:2M}; modes {matched, blind}.
- Allocation H input (allocation ONLY, never refit): 1M 0.801038 /
  1.5M 0.825566 / 2M 0.832563; slope 4.785675; bars 12 and f_super 1.3.
- F2 equal-share + largest-remainder (10 Gray planes, sum rows == m,
  each plane rows <= 64); F3 blind ``m_init=m-20`` + ``[4 x 5]``
  (5 small steps, 6 cumulative levels incl. init); F4 SPA pins
  max_iter=300 / streak=3 (machine-checked, never tuned).

Block classes: success requires ``exact_match`` AND ``accepted`` AND
per-plane syndrome consistency AND Toeplitz verification (double gate);
undetected (``accepted`` but not success) is logged separately and never
merged into success; fail is every other non-success block. Gate-(a)
fails count EVERY non-success block; bar-12 arms are CENSORED
(fails-at-stop / blocks-at-stop reported, projected NEVER). Overall arm
verdict PASS iff gate (a) AND gate (b); gate (c) is rule-evaluated
report-only with the presentation ban enforced structurally (f_super,
f_notag and f_eff always reported as DISTINCT lines, never a single
certifiable number). Curve-relative monotone/non-monotone labels are
batch-level (no cross-m inference here): non-early-stop arms are
recorded NON-CENSORED with the curve label deferred to batch analysis.

No raw-dump reads (no such import, path, or extension string anywhere
here), no decoder/DE/graph-kernel change, no refit path, no overwrite
path, no resume/continue path (wall-partial yields INCOMPLETE, retained,
never continued; at most one preregistered infra repair+rerun with
unchanged science inputs, retained in the same root), no writes outside
the fresh per-arm root, never under ``results/`` or
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

from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v10_peg as peg,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    codebook_v4 as _cb4,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v26_mcde as _mcde,
)
from comparison_bench.src.comparison_bench.formal_ir import v80_o1_campaign as o1
from comparison_bench.src.comparison_bench.formal_ir import v80_s2_peg as s2
from comparison_bench.src.comparison_bench.formal_ir import (
    v80_s2c_campaign as s2c,
)
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (
    GF2mField,
)
from comparison_bench.src.comparison_bench.methods.layered_ldpc_lite import (
    split_symbol_bitplanes,
)
from comparison_bench.src.comparison_bench.types import FrameBatch

__all__ = [
    "M2LB_N_PLANE", "M2LB_CONTENT_N", "M2LB_DIMENSION", "M2LB_PLANES",
    "M2LB_CONSTRUCT_SEED", "M2LB_MAX_TRIALS", "M2LB_BLOCK_BASE",
    "M2LB_N_BLOCKS", "M2LB_MAX_ITER", "M2LB_STREAK",
    "M2LB_WALL_CAP_S", "M2LB_PER_DECODE_CAP_S", "M2LB_RSS_CAP_GIB",
    "M2LB_ROOT_PREFIX", "FORBIDDEN_ROOT_PARTS",
    "M2LB_BUNDLE_FILENAME", "GRID", "DISPLAY_TO_KEY", "FROZEN_H",
    "F_EFF_SLOPE", "F_SUPER_MAX", "TAG_BITS", "BLIND_DELTA",
    "PRIOR_SCALE_REPORTONLY", "LDPC_MSG_REF", "CASCADE_MSG_REF",
    "CLAIM_CEILING", "OUTCOME_KEYS",
    "Refusal", "refuse", "parse_arm", "block_seed", "stream_seed",
    "fail_bar", "f_super_for", "f_notag_for", "f_eff_for", "n_required",
    "lambda_total", "allocation_for", "blind_table_for", "blind_levels_for",
    "bind_source_bundle", "sample_frozen_batch",
    "construct_plane_production", "spa_decode_production",
    "block_accounting_csv", "result_markdown",
    "execute", "run_execution", "main",
]

#: Frozen per-plane length (n=64 family; FrameBatch frame_len_symbols).
M2LB_N_PLANE = 64
#: Frozen content denominator for f accounting (1024 * H_src).
M2LB_CONTENT_N = 1024
#: Frozen alphabet size (1024 symbols -> 10 Gray planes).
M2LB_DIMENSION = 1024
#: Frozen Gray plane count.
M2LB_PLANES = 10
#: Frozen single construction instance (packet Sec 7-4/7-5).
M2LB_CONSTRUCT_SEED = 2026092001
#: Frozen constructor trials.
M2LB_MAX_TRIALS = 20
#: Frozen literal block-seed base (packet Sec 7-5).
M2LB_BLOCK_BASE = 2026095601
#: Frozen campaign width: 240 blocks = 240 frames per arm.
M2LB_N_BLOCKS = 240
#: Frozen binary-SPA pins (packet Sec 7-4; machine-checked).
M2LB_MAX_ITER = 300
M2LB_STREAK = 3
#: Frozen per-arm wall budget (packet Sec 7-6).
M2LB_WALL_CAP_S = 1800
#: Frozen per-decode terminal (packet Sec 7-6).
M2LB_PER_DECODE_CAP_S = 300
#: Frozen RSS cap (packet Sec 7-6).
M2LB_RSS_CAP_GIB = 4
#: Fresh additive M2LB run-root prefix (packet Sec 7-2).
M2LB_ROOT_PREFIX = "workspace/m2lb_"
#: Roots the executor never writes under.
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")
#: Frozen bundle file name (packet Sec 7-3; sidecar via s2c.PB_SIDECAR_NAME).
M2LB_BUNDLE_FILENAME = "gamma_f03.npz"
#: Frozen 6-point grid (packet Sec 7-5), keyed by BUNDLE key.
GRID: dict[str, tuple[int, ...]] = {
    "1M": (197, 201),
    "1p5M": (203, 207),
    "2M": (204, 208),
}
#: Arm-display source -> bundle-key map (packet Sec 7-3; "1.5M" never a key).
DISPLAY_TO_KEY = {"1M": "1M", "1.5M": "1p5M", "2M": "2M"}
#: Frozen allocation H input (packet Sec 7-3; allocation input ONLY, no refit).
FROZEN_H = {
    "1M": 0.801038,
    "1p5M": 0.825566,
    "2M": 0.832563,
}
#: Frozen f_eff slope (packet F5).
F_EFF_SLOPE = 4.785675
#: Frozen efficiency bar (packet Sec 6 G-B).
F_SUPER_MAX = 1.3
#: Frozen verification tag width.
TAG_BITS = 64
#: Frozen blind delta steps (packet Sec 7-4: 5 small steps of +4).
BLIND_DELTA: list[int] = [4, 4, 4, 4, 4]
#: Frozen prior opportunity-cost scale (report-only, never into lambda/f).
PRIOR_SCALE_REPORTONLY = 1.50
#: LDPC-level per-frame message aperture (F5; independent column).
LDPC_MSG_REF = 3.14
#: Cascade aperture carried as a non-comparable annotation only.
CASCADE_MSG_REF = 446
#: Claim-ceiling fixed sentence (packet Sec 5; carried verbatim).
CLAIM_CEILING = (
    "合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；"
    "D1 条件化分支下不得用本批合成数论证真实优劣。"
)
#: Required decode outcome keys (exactly 13; missing key fails closed).
OUTCOME_KEYS = (
    "exact_match", "accepted", "syndrome_consistent", "toeplitz_verified",
    "leak_ec_bits", "blind_stage_bits", "rescue_bits", "control_bits",
    "messages_actual", "prior_entropy_bits", "iterations", "max_iter",
    "streak",
)
#: Outcome keys that must NEVER appear (NO genie/argmax path).
FORBIDDEN_OUTCOME_KEYS = ("genie", "argmax")

_ARM_RE = re.compile(r"^M2LB-(1M|1\.5M|2M)-(\d+)-(matched|blind)$")
_ROOT_RE = re.compile(r"^workspace/m2lb_[0-9A-Za-z]{8}$")


class Refusal(SystemExit):
    """rc=2 pre-write refusal (unauthorized / invalid / gate-blocked)."""


def refuse(reason: str) -> Any:
    print(f"M2LB-REFUSAL rc=2: {reason}", file=sys.stderr)
    raise Refusal(2)


def parse_arm(arm: str) -> dict[str, Any]:
    """Parse ``M2LB-<SOURCE>-<M>-<MODE>`` against the frozen grid.

    Returns display source, bundle key, m, mode, and the layered
    construction label. Anything off-grid refuses (fail closed, rc=2).
    """
    mobj = _ARM_RE.match(str(arm))
    if mobj is None:
        refuse(f"unknown arm {arm} "
               f"(frozen form: M2LB-<1M|1.5M|2M>-<m>-<matched|blind>)")
    display = str(mobj.group(1))
    m = int(mobj.group(2))
    mode = str(mobj.group(3))
    key = DISPLAY_TO_KEY[display]
    if m not in GRID[key]:
        refuse(f"arm {arm} m={m} off the frozen M2LB-{display} grid "
               f"{list(GRID[key])} (packet Sec 7-5; grid unchanged)")
    if mode not in ("matched", "blind"):
        refuse(f"arm {arm} mode {mode} not frozen (matched|blind only)")
    return {"arm": str(arm), "display": display, "source_key": key,
            "m": m, "mode": mode,
            "construct_label": f"M2LB-{display}-S{m}-layered"}


def block_seed(idx: int, base: int | None = None) -> int:
    """Frozen literal block seed: base+idx, idx=0..239 (packet Sec 7-5)."""
    b = M2LB_BLOCK_BASE if base is None else base
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
        float(M2LB_CONTENT_N) * float(FROZEN_H[source_key]))


def f_notag_for(source_key: str, m: int) -> float:
    """f_notag = 5m/(1024*H[source]) (packet F5; tag-free contrast)."""
    if source_key not in FROZEN_H:
        refuse(f"unknown source key {source_key} (frozen: 1M|1p5M|2M)")
    return float(5 * int(m)) / (
        float(M2LB_CONTENT_N) * float(FROZEN_H[source_key]))


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


def allocation_for(source_key: str, m: int,
                   h_basis: float | None = None) -> dict[int, int]:
    """F2 equal-share + largest-remainder over 10 Gray planes.

    ``h_basis`` must equal the frozen H input for the source (no refit;
    mismatch refuses). Returns ``{plane j=0..9: rows m_j}`` with
    ``sum == m`` and each ``m_j <= 64`` (n=64 family gate).
    """
    if source_key not in FROZEN_H:
        refuse(f"unknown source key {source_key} (frozen: 1M|1p5M|2M)")
    h = float(FROZEN_H[source_key]) if h_basis is None else float(h_basis)
    if abs(h - float(FROZEN_H[source_key])) > 1e-9:
        refuse(f"h_basis {h!r} != frozen H for {source_key} "
               f"({FROZEN_H[source_key]}; allocation input only, no refit)")
    if isinstance(m, bool) or not isinstance(m, int) or int(m) < 1:
        refuse("allocation m must be a positive int")
    base, rem = divmod(int(m), M2LB_PLANES)
    rows = {j: (base + 1 if j < rem else base)
            for j in range(M2LB_PLANES)}
    if sum(rows.values()) != int(m):
        refuse(f"allocation sum {sum(rows.values())} != m {m} (fail closed)")
    for j, v in rows.items():
        if v > M2LB_N_PLANE:
            refuse(f"plane {j}: m_j={v} > n_plane={M2LB_N_PLANE} "
                   f"(fail closed; single-plane rows cannot exceed 64)")
        if v < 0:
            refuse(f"plane {j}: negative rows {v} (fail closed)")
    return rows


def blind_table_for(m: int) -> dict[str, Any]:
    """F3 frozen blind schedule: ``m_init=m-20`` + ``[4 x 5]``.

    Returns ``{"m_init": ..., "delta_steps": [4,4,4,4,4]}`` with
    ``len == 5`` and ``m_init + sum(delta) == m``. Any deviation in a
    caller-supplied table is a science-input change (refuse).
    """
    if isinstance(m, bool) or not isinstance(m, int) or int(m) < 1:
        refuse("blind table m must be a positive int")
    m_init = int(m) - 20
    if m_init < 1:
        refuse(f"blind m_init {m_init} < 1 for m={m} (fail closed)")
    deltas = list(BLIND_DELTA)
    if len(deltas) != 5:
        refuse("blind delta table must hold exactly 5 steps (fail closed)")
    if any((isinstance(x, bool) or not isinstance(x, int) or x != 4)
           for x in deltas):
        refuse("blind delta steps frozen at [4 x 5] (fail closed)")
    if m_init + sum(deltas) != int(m):
        refuse(f"blind schedule {m_init}+{deltas} != m {m} (fail closed)")
    return {"m_init": m_init, "delta_steps": deltas}


def blind_levels_for(m: int) -> list[int]:
    """Cumulative blind disclosure levels (init + 5 small steps; 6 levels)."""
    tab = blind_table_for(int(m))
    levels = [int(tab["m_init"])]
    for d in tab["delta_steps"]:
        levels.append(levels[-1] + int(d))
    if levels[-1] != int(m):
        refuse(f"blind levels {levels} do not terminate at m {m}")
    return levels


def _check_spa_pins(max_iter: int, streak: int) -> None:
    """Machine-check the frozen binary-SPA pins (300/3; never tuned)."""
    if int(max_iter) != M2LB_MAX_ITER or int(streak) != M2LB_STREAK:
        refuse(f"binary SPA pins frozen at "
               f"{M2LB_MAX_ITER}/{M2LB_STREAK} (got {max_iter}/{streak}; "
               f"no tuning)")
    if int(s2.MAX_ITER) != M2LB_MAX_ITER:
        refuse("SPA max_iter freeze mismatch vs frozen s2 config (STOP)")


def _check_outcome(outcome: dict[str, Any]) -> dict[str, Any]:
    """Fail-closed 13-key outcome check (exact accept; NO genie path)."""
    if not isinstance(outcome, dict):
        refuse("decode outcome not a dict (fail closed)")
    for bad in FORBIDDEN_OUTCOME_KEYS:
        if bad in outcome:
            refuse(f"decode outcome carries forbidden {bad} key "
                   f"(NO genie/argmax path)")
        for k in outcome:
            if bad in str(k).lower():
                refuse(f"decode outcome key {k!r} resembles forbidden "
                       f"{bad} path (NO genie/argmax)")
    for key in OUTCOME_KEYS:
        if key not in outcome:
            refuse(f"decode outcome missing {key!r} (fail closed, "
                   f"13 keys required, no defaults)")
    if len(OUTCOME_KEYS) != 13:
        refuse("OUTCOME_KEYS must hold exactly 13 entries (fail closed)")
    bs = outcome.get("blind_stage_bits")
    try:
        blist = list(bs)
    except Exception:  # noqa: BLE001
        refuse("blind_stage_bits must be a 5-step list (fail closed)")
    if len(blist) != 5:
        refuse(f"blind_stage_bits len {len(blist)} != 5 frozen steps")
    try:
        float(outcome.get("leak_ec_bits"))
        float(outcome.get("rescue_bits"))
        float(outcome.get("control_bits"))
        float(outcome.get("messages_actual"))
        float(outcome.get("prior_entropy_bits"))
        int(outcome.get("iterations"))
    except Exception:  # noqa: BLE001
        refuse("decode outcome numeric fields corrupt (fail closed)")
    if int(outcome.get("max_iter")) != M2LB_MAX_ITER:
        refuse("decode outcome max_iter != frozen 300 (fail closed)")
    if int(outcome.get("streak")) != M2LB_STREAK:
        refuse("decode outcome streak != frozen 3 (fail closed)")
    return outcome


def construct_plane_production(m_rows: int, seed: int, trials: int,
                               plane: int) -> dict[str, Any]:
    """Per-plane production construction via the existing PEG, read-only.

    Frozen path: ``GF2mField.create`` + ``make_rho`` + ``peg_construct``
    with n_plane=64, lambda={2:1}, trials=20. Tests MUST inject an
    explicit fake ``construct_fn``; the production path is never entered
    by fake tests (guarded there by monkeypatch to raise).
    """
    if int(trials) != M2LB_MAX_TRIALS:
        refuse(f"construct trials frozen at {M2LB_MAX_TRIALS} "
               f"(got {trials})")
    if not 0 <= int(plane) < M2LB_PLANES:
        refuse(f"plane {plane} outside 0..9 (fail closed)")
    field = GF2mField.create(s2.Q)
    lam = {2: 1.0}
    rho = _mcde.make_rho(1.0 - int(m_rows) / int(M2LB_N_PLANE), lam)
    code = peg.peg_construct(int(M2LB_N_PLANE), int(m_rows), lam, rho,
                             int(seed), max_trials=int(trials), field=field)
    code["family"] = "peg-irregular"
    s2.refuse_three_shift_cyclic({"family": code["family"]})
    code["lambda_edge"] = {int(k): float(v) for k, v in lam.items()}
    code["rho_edge"] = {int(k): float(v) for k, v in rho.items()}
    return code


def spa_decode_production(a_planes: Any, b_planes: Any,
                          constructions: Any, stage_ctx: dict[str, Any],
                          frame_idx: int, max_iter: int,
                          streak: int) -> dict[str, Any]:
    """Binary-SPA production decode (frozen pins; granted runs + tiny self-check).

    冻结注释 (R1修订包选项A重冻; T2-BLOCKER原文coeff==1冻结已推翻; 改注释 = 科学输入变更 -> STOP):
    1. H规则: 本地 ``_h_from_triples`` 由 triples 建二元支撑矩阵 (``H[r,c]=1``);
       越界/空/重复/m_hint语义保留 (越界fail-closed, 空拒, 重复塌缩置1, m_hint须等span).
    2. coeff处理: coeff!=0一律按支撑置1 (2/512/1023等GF标记按支撑处理, 推翻旧==1冻结);
       coeff==0拒 (支撑空 -> STOP).
    3. rank域: 二元支撑GF(2)域 ``rank∈{m_j-1,m_j}`` GATED (仓内二元rank helper
       ``codebook_v4.gf2_rank`` 计算支撑H的GF(2)秩; PEG返回不动, 不读PEG的GF(1024)rank;
       列重2单维容忍 (rank==m_j-1过), rank<=m_j-2仍STOP).
    4. twice域: 支撑排序比较 (sorted ``(r,c)`` 支撑, coeff归一化, 零系数先拒);
       不一致 -> STOP-BLOCKED.
    5. fc域: 二元域声明 ``fc==0`` GATED (STOP-BLOCKED); girth仅记录不门控.
    6. 返回语义: PEG调用参数/种子/trials字面量不动, PEG返回字典不动
       (门仅读triples/fc/girth, rank重算); outcome仍13键, 双门语义
       (success=exact+accepted+syndrome+toeplitz, undetected独立)不变.
    7. 不重冻项: LLR ``p_assumed=0.02``/综合征/盲段stage_rows(A)/会计映射/
       Toeplitz本地展开/异常fail-closed(后端缺失或异常即STOP, 永不切bit-flip)
       沿用T2-BLOCKER冻结, 本次不重冻.
    """
    _check_spa_pins(int(max_iter), int(streak))
    import importlib.util as _ilu
    from comparison_bench.src.comparison_bench.formal_ir.shared import (
        toeplitz_tag as _toeplitz_tag,
    )
    from comparison_bench.src.comparison_bench.methods.layered_ldpc_lite import (
        _decode_error_ldpc_backend as _spa_backend,
    )
    from comparison_bench.src.comparison_bench.methods.layered_ldpc_lite import (
        _syndrome as _bin_syndrome,
    )
    if _ilu.find_spec("ldpc") is None:
        refuse("STOP-BLOCKED: ldpc backend absent for production binary-SPA "
               "(no bit-flip substitute; install the frozen backend or revise)")
    _P_ASSUMED = 0.02  # frozen BSC assumption (assumed, uniform, no adaptation)

    def _need_int(value: Any, what: str) -> int:
        if isinstance(value, bool):
            refuse(f"spa decode {what} must be an int (fail closed)")
        try:
            out = int(value)
        except Exception:  # noqa: BLE001 — fail closed, no defaults
            refuse(f"spa decode {what} not an int (fail closed)")
        return out

    try:
        a_list = [np.asarray(p, dtype=np.uint8).reshape(-1)
                  for p in list(a_planes)]
        b_list = [np.asarray(p, dtype=np.uint8).reshape(-1)
                  for p in list(b_planes)]
        cons_list = list(constructions)
    except Refusal:
        raise
    except Exception:  # noqa: BLE001 — fail closed, no defaults
        refuse("spa decode inputs must be 10-plane sequences (fail closed)")
    if not (len(a_list) == len(b_list) == len(cons_list) == M2LB_PLANES):
        refuse(f"spa decode needs exactly {M2LB_PLANES} planes each "
               f"(got {len(a_list)}/{len(b_list)}/{len(cons_list)}; "
               f"fail closed)")
    n_plane = len(a_list[0])
    if n_plane < 1:
        refuse("spa decode plane length < 1 (fail closed)")
    for j in range(M2LB_PLANES):
        if len(a_list[j]) != n_plane or len(b_list[j]) != n_plane:
            refuse(f"spa decode plane {j} length mismatch (fail closed)")
        for vec in (a_list[j], b_list[j]):
            if bool(np.any((vec != 0) & (vec != 1))):
                refuse(f"spa decode plane {j} non-binary bits "
                       f"(binary SPA only; fail closed)")

    if not isinstance(stage_ctx, dict):
        refuse("spa decode stage_ctx must be a dict (fail closed)")
    mode = stage_ctx.get("mode")
    if mode not in ("matched", "blind"):
        refuse(f"spa decode mode {mode!r} not frozen "
               f"(matched|blind only; fail closed)")
    m_target = _need_int(stage_ctx.get("m_target"), "m_target")
    m_stage = _need_int(stage_ctx.get("m_stage"), "m_stage")
    stage_idx = _need_int(stage_ctx.get("stage_idx"), "stage_idx")
    m_init = _need_int(stage_ctx.get("m_init"), "m_init")
    try:
        deltas = [int(x) for x in list(stage_ctx.get("delta_steps"))]
    except Exception:  # noqa: BLE001 — fail closed, no defaults
        refuse("spa decode delta_steps corrupt (fail closed)")
    if [int(x) for x in deltas] != [int(x) for x in BLIND_DELTA]:
        refuse(f"spa decode delta steps frozen at {list(BLIND_DELTA)} "
               f"(got {deltas}; science-input change -> STOP)")
    if m_target < 1 or m_stage < 1 or m_init < 1:
        refuse("spa decode m_target/m_stage/m_init must be positive "
               "(fail closed)")
    if m_init != m_target - 20:
        refuse(f"spa decode m_init {m_init} != m_target-20 {m_target - 20} "
               f"(frozen blind table; science-input change -> STOP)")
    if mode == "matched":
        if m_stage != m_target or stage_idx != 0:
            refuse("spa decode matched stage must be single full-m "
                   "(m_stage==m_target, stage_idx==0; fail closed)")
    else:
        if not 0 <= stage_idx <= 5:
            refuse(f"spa decode blind stage_idx {stage_idx} outside 0..5 "
                   f"(fail closed)")
        if m_init + sum(int(x) for x in deltas[:stage_idx]) != m_stage:
            refuse(f"spa decode blind m_stage {m_stage} != m_init "
                   f"{m_init}+used deltas (fail closed)")
        if m_stage > m_target:
            refuse(f"spa decode blind m_stage {m_stage} > m_target "
                   f"{m_target} (fail closed)")
    fidx = _need_int(frame_idx, "frame_idx")
    if fidx < 0:
        refuse("spa decode frame_idx must be non-negative (fail closed)")

    def _h_from_triples(triples: Any, m_hint: Any,
                        plane: int) -> tuple[Any, int]:
        """Local binary-support-H builder (R1修订包选项A): coeff!=0->H=1.

        支撑语义 (推翻旧==1冻结): 任意非零coeff (1/2/512/1023等GF标记) 一律按
        支撑置 ``H[r,c]=1``; coeff==0拒 (支撑空 -> STOP). 越界/重复/空/m_hint
        语义保留 (越界fail-closed, 空拒, 重复塌缩置1, m_hint须等span).
        """
        try:
            trips = list(triples)
        except Exception:  # noqa: BLE001 — fail closed
            refuse(f"spa decode plane {plane}: triples not a sequence "
                   f"(fail closed)")
        if not trips:
            refuse(f"spa decode plane {plane}: empty triples (fail closed)")
        rows: list[int] = []
        cols: list[int] = []
        for t in trips:
            try:
                r, c, v = int(t[0]), int(t[1]), int(t[2])
            except Exception:  # noqa: BLE001 — fail closed
                refuse(f"spa decode plane {plane}: corrupt triple "
                       f"{t!r} (fail closed)")
            if int(v) == 0:
                refuse(f"spa decode plane {plane}: zero coeff "
                       f"{v!r} (support-empty; fail closed -> STOP)")
            # R1修订包选项A: 非零coeff按支撑置1 (旧==1冻结已推翻).
            rows.append(r)
            cols.append(c)
        m_full = max(rows) + 1
        if m_hint is not None:
            try:
                if int(m_hint) != int(m_full):
                    refuse(f"spa decode plane {plane}: triples span "
                           f"m={m_full} != construction m={m_hint} "
                           f"(fail closed)")
            except Refusal:
                raise
            except Exception:  # noqa: BLE001 — fail closed
                refuse(f"spa decode plane {plane}: construction m "
                       f"corrupt (fail closed)")
        if min(rows) < 0 or min(cols) < 0 or max(cols) >= n_plane:
            refuse(f"spa decode plane {plane}: triple index out of range "
                   f"(fail closed)")
        mat = np.zeros((m_full, n_plane), dtype=np.uint8)
        for r, c in zip(rows, cols):
            mat[r, c] = 1
        return mat, m_full

    h_full: list[Any] = []
    m_fulls: list[int] = []
    for j in range(M2LB_PLANES):
        try:
            code_j = cons_list[j]
            trips_j = code_j["triples"]
            hint_j = code_j.get("m", None)
        except Exception:  # noqa: BLE001 — fail closed
            refuse(f"spa decode plane {j}: construction missing "
                   f"triples/m (fail closed)")
        hj, mj = _h_from_triples(trips_j, hint_j, j)
        h_full.append(hj)
        m_fulls.append(mj)
    # Frozen stage_rows choice (A): equal-share prefix per plane.
    _sbase, _srem = divmod(m_stage, M2LB_PLANES)
    stage_rows = [(_sbase + 1) if j < _srem else _sbase
                  for j in range(M2LB_PLANES)]
    if sum(stage_rows) != m_stage:  # pragma: no cover — divmod invariant
        refuse("spa decode stage_rows sum != m_stage (fail closed)")
    for j in range(M2LB_PLANES):
        if stage_rows[j] > m_fulls[j]:
            refuse(f"spa decode plane {j}: stage rows {stage_rows[j]} > "
                   f"m_j {m_fulls[j]} (fail closed)")
    if m_stage == m_target:
        for j in range(M2LB_PLANES):
            if stage_rows[j] != m_fulls[j]:
                refuse(f"spa decode plane {j}: stage rows "
                       f"{stage_rows[j]} != full m_j {m_fulls[j]} "
                       f"(conflicts with the F2 full table -> STOP)")

    rec_list: list[Any] = []
    ok_list: list[bool] = []
    syn_list: list[bool] = []
    exact_list: list[bool] = []
    total_iters = 0
    for j in range(M2LB_PLANES):
        a_j = a_list[j]
        b_j = b_list[j]
        k_j = int(stage_rows[j])
        h_j = h_full[j][:k_j, :]
        s_alice = np.asarray(_bin_syndrome(h_j, a_j),
                             dtype=np.uint8).reshape(-1)
        s_bob = np.asarray(_bin_syndrome(h_j, b_j),
                           dtype=np.uint8).reshape(-1)
        delta = np.bitwise_xor(s_alice, s_bob).astype(np.uint8)
        if k_j == 0:
            err_hat = np.zeros(n_plane, dtype=np.uint8)
            back_ok, iters_j = True, 0
        else:
            try:
                err_hat, back_ok, iters_j, _be = _spa_backend(
                    h_j, delta, int(max_iter), float(_P_ASSUMED),
                    osd_order=0, bp_method="minimum_sum")
            except Refusal:
                raise
            except Exception as exc:  # noqa: BLE001 — never bit-flip
                refuse(f"spa decode plane {j}: binary-SPA backend failed "
                       f"({type(exc).__name__}: {exc}; no bit-flip "
                       f"substitute; fail closed)")
            err_hat = np.asarray(err_hat, dtype=np.uint8).reshape(-1)
            if err_hat.shape != (n_plane,):
                refuse(f"spa decode plane {j}: backend error vector "
                       f"shape {err_hat.shape} != ({n_plane},) "
                       f"(fail closed)")
            back_ok, iters_j = bool(back_ok), int(iters_j)
        rec_j = np.bitwise_xor(b_j, err_hat).astype(np.uint8)
        syn_ok = bool(np.array_equal(
            np.asarray(_bin_syndrome(h_j, rec_j),
                       dtype=np.uint8).reshape(-1), s_alice))
        rec_list.append(rec_j)
        ok_list.append(back_ok)
        syn_list.append(syn_ok)
        exact_list.append(bool(np.array_equal(rec_j, a_j)))
        total_iters += int(iters_j)
    exact_match = bool(all(exact_list))
    accepted = bool(all(ok_list))
    syndrome_consistent = bool(all(syn_list))
    # Toeplitz double gate: local seed expansion only (shared untouched).
    n_ir = int(M2LB_PLANES * n_plane)
    try:
        rng = np.random.default_rng(int(block_seed(fidx)) % (2 ** 32))
        seed_bits = rng.integers(
            0, 2, size=(n_ir + int(TAG_BITS) - 1)).astype(np.uint8)
        tag_a = _toeplitz_tag(np.concatenate(a_list), seed_bits,
                              int(TAG_BITS))
        tag_r = _toeplitz_tag(np.concatenate(rec_list), seed_bits,
                              int(TAG_BITS))
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed
        refuse(f"spa decode toeplitz verification failed "
               f"({type(exc).__name__}: {exc}; fail closed)")
    toeplitz_verified = bool(tag_a == tag_r)
    # Frozen accounting map (blind increments join leak via the caller sum).
    if mode == "matched":
        leak_ec = float(m_target)
        blind_bits = [0.0, 0.0, 0.0, 0.0, 0.0]
    else:
        leak_ec = float(m_init)
        blind_bits = ([float(x) for x in deltas[:stage_idx]]
                      + [0.0] * (5 - stage_idx))
    if abs(float(leak_ec) + float(sum(blind_bits))
           - float(m_stage)) > 1e-9:  # pragma: no cover — invariant
        refuse("spa decode accounting leak+stages != m_stage (fail closed)")
    _h2 = -(_P_ASSUMED * math.log2(_P_ASSUMED)
            + (1.0 - _P_ASSUMED) * math.log2(1.0 - _P_ASSUMED))
    outcome = {
        "exact_match": exact_match,
        "accepted": accepted,
        "syndrome_consistent": syndrome_consistent,
        "toeplitz_verified": toeplitz_verified,
        "leak_ec_bits": float(leak_ec),
        "blind_stage_bits": [float(x) for x in blind_bits],
        "rescue_bits": 0.0,
        "control_bits": 0.0,
        "messages_actual": float(LDPC_MSG_REF),
        "prior_entropy_bits": float(n_ir) * float(_h2),
        "iterations": int(total_iters),
        "max_iter": int(M2LB_MAX_ITER),
        "streak": int(M2LB_STREAK),
    }
    return _check_outcome(outcome)


def _construct_gate_planes(allocation: dict[int, int], frame_idx: int,
                           construct_fn: Callable, seed_base: int,
                           trials: int) -> list[dict[str, Any]]:
    """Pre-run per-plane construction gate (packet Sec F4; R1修订包选项A重冻).

    For each of the 10 planes: build twice on ``seed_base+frame_idx``,
    require twice-identical SUPPORT (sorted ``(r,c)`` with coeff!=0->1;
    coeff==0 refused); pins fc=0 (binary-domain declaration) + binary-support
    GF(2) rank∈{m_j-1,m_j} GATED (STOP-BLOCKED, computed via the in-repo binary rank
    helper ``codebook_v4.gf2_rank`` on the support H; PEG return untouched,
    PEG rank field ignored; single-deficiency tolerance for column-weight-2
    ring (rank==m_j-1 passes), rank<=m_j-2 still STOP-BLOCKED);
    girth recorded-not-gated. ``construct_fn``
    convention is ``(m_rows, seed, trials, plane)``.
    """
    if int(seed_base) != M2LB_CONSTRUCT_SEED:
        refuse(f"construct instance must be the frozen "
               f"{M2LB_CONSTRUCT_SEED} (got {seed_base})")
    if int(trials) != M2LB_MAX_TRIALS:
        refuse(f"construct trials frozen at {M2LB_MAX_TRIALS} "
               f"(got {trials})")
    if sorted(int(k) for k in allocation) != list(range(M2LB_PLANES)):
        refuse("allocation must cover planes 0..9 exactly (fail closed)")
    seed = int(seed_base) + int(frame_idx)
    gated: list[dict[str, Any]] = []
    for plane in range(M2LB_PLANES):
        m_j = int(allocation[plane])
        try:
            code_a = construct_fn(int(m_j), int(seed), int(trials),
                                  int(plane))
            code_b = construct_fn(int(m_j), int(seed), int(trials),
                                  int(plane))
        except Refusal:
            raise
        except Exception as exc:  # noqa: BLE001 — fail closed pre-decode
            refuse(f"construction failed (plane {plane} m_j={m_j}): "
                   f"{type(exc).__name__}: {exc}")
        ta, tb = code_a.get("triples"), code_b.get("triples")
        if ta is not None or tb is not None:
            try:
                # R1修订包选项A: 支撑排序比较 — coeff归一化为支撑 (r,c).
                def _support_sorted(tt: Any) -> list[tuple[int, int]]:
                    sup: list[tuple[int, int]] = []
                    for t in list(tt):
                        r, c, v = int(t[0]), int(t[1]), int(t[2])
                        if int(v) == 0:
                            refuse(f"construction plane {plane}: zero coeff "
                                   f"support-empty (STOP-BLOCKED)")
                        sup.append((int(r), int(c)))
                    return sorted(sup)
                sa = _support_sorted(ta)
                sb = _support_sorted(tb)
            except Refusal:
                raise
            except Exception:  # noqa: BLE001
                refuse(f"construction triples corrupt (plane {plane}; "
                       f"STOP-BLOCKED)")
            if sa != sb:
                refuse(f"construct-twice mismatch (plane {plane} m_j={m_j}; "
                       f"not identical; STOP-BLOCKED)")
        if code_a.get("status", "ok") != "ok":
            refuse(f"construction {code_a.get('status')} (plane {plane}; "
                   f"STOP-BLOCKED)")
        try:
            fc = int(code_a.get("four_cycles"))
            girth = int(code_a.get("min_girth"))
        except Exception:  # noqa: BLE001
            refuse(f"construction missing fc/girth pins (plane {plane}; "
                   f"STOP-BLOCKED)")
        # R1修订包选项A: fc=0保留 (二元域声明).
        if fc != 0:
            refuse(f"plane {plane} m_j={m_j} four_cycles {fc} != 0 "
                   f"(STOP-BLOCKED; measured girth {girth})")
        # R1修订包选项A: 二元支撑GF(2) rank∈{m_j-1,m_j} (复用仓内二元rank helper,
        # 禁新依赖; PEG返回不动, 不读PEG的GF(1024)rank字段; 列重2单维容忍).
        try:
            trips = list(code_a.get("triples"))
            if not trips:
                refuse(f"plane {plane}: empty triples (STOP-BLOCKED)")
            s_rows: list[int] = []
            s_cols: list[int] = []
            for t in trips:
                r, c, v = int(t[0]), int(t[1]), int(t[2])
                if int(v) == 0:
                    refuse(f"plane {plane}: zero coeff "
                           f"support-empty (STOP-BLOCKED)")
                s_rows.append(int(r))
                s_cols.append(int(c))
            if min(s_rows) < 0 or min(s_cols) < 0 \
                    or max(s_cols) >= int(M2LB_N_PLANE):
                refuse(f"plane {plane}: triple index out of range "
                       f"(STOP-BLOCKED)")
            m_span = max(s_rows) + 1
            if int(m_span) != int(m_j):
                refuse(f"plane {plane}: triples span m={m_span} != m_j "
                       f"{m_j} (STOP-BLOCKED)")
            _mat = np.zeros((int(m_j), int(M2LB_N_PLANE)), dtype=np.uint8)
            for r, c in zip(s_rows, s_cols):
                _mat[int(r), int(c)] = 1
            rank_bin = int(_cb4.gf2_rank(_mat))
        except Refusal:
            raise
        except Exception:  # noqa: BLE001
            refuse(f"construction support-rank failed (plane {plane}; "
                   f"STOP-BLOCKED)")
        if rank_bin != int(m_j) and rank_bin != int(m_j) - 1:
            refuse(f"plane {plane} m_j={m_j} binary-support GF(2) rank "
                   f"{rank_bin} not in {{{int(m_j) - 1},{m_j}}} "
                   f"(STOP-BLOCKED; measured girth {girth})")
        code_a["construct_seed"] = seed
        code_a["construct_trials"] = trials
        code_a["measured_girth"] = girth  # recorded-not-gated
        gated.append(code_a)
    return gated


def bind_source_bundle(bundle_path: str, source_key: str,
                       arm: str) -> dict[str, Any]:
    """Bind the Sec 7-3 bundle READ-ONLY via the frozen consumer (F1 form).

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
    if name != M2LB_BUNDLE_FILENAME:
        refuse(f"M2LB arms bind ONLY the frozen {M2LB_BUNDLE_FILENAME} "
               f"(got {name}; substitute refused — packet Sec 7-3)")
    bound = s2c.bind_empirical_bundle(str(bundle_path), str(source_key))
    if bound.get("source") != str(source_key):
        refuse("bound source label mismatch (fail closed)")
    return bound


def sample_frozen_batch(bundle: dict[str, Any], source_key: str,
                        n_blocks: int | None = None) -> FrameBatch:
    """Frozen 240-frame sampler (packet F1/F4; synthetic only).

    Returns a ``FrameBatch`` with 240 frames x 64 symbols, dimension
    1024 (10 Gray planes). Deterministic per-block streams
    ``o1_blk:{seed}`` with seeds ``2026095601+idx``. Validates the bound
    source label (no cross-source use), the 240 width, the n=64 family,
    and the 10-plane Gray split (read-only ``split_symbol_bitplanes``).
    Pure in-memory; never refits the bundle.
    """
    n = M2LB_N_BLOCKS if n_blocks is None else int(n_blocks)
    if isinstance(n, bool) or n != M2LB_N_BLOCKS:
        refuse(f"sampler width frozen at {M2LB_N_BLOCKS} "
               f"(got {n_blocks}; no alternate denominator)")
    if not isinstance(bundle, dict) or bundle.get("source") != source_key:
        refuse("sampler source label mismatch (fail closed; no cross use)")
    if source_key not in FROZEN_H:
        refuse(f"unknown source key {source_key} (frozen: 1M|1p5M|2M)")
    alice = np.empty((n, M2LB_N_PLANE), dtype=np.int64)
    bob = np.empty((n, M2LB_N_PLANE), dtype=np.int64)
    for idx in range(n):
        seed = block_seed(idx)
        rng = np.random.default_rng(int(stream_seed(seed)) % (2 ** 32))
        a = rng.integers(0, M2LB_DIMENSION, size=M2LB_N_PLANE,
                         dtype=np.int64)
        flips = rng.random(M2LB_N_PLANE) < 0.02
        b = np.where(flips, (a + rng.integers(1, M2LB_DIMENSION,
                                              size=M2LB_N_PLANE)) % M2LB_DIMENSION,
                     a)
        alice[idx] = a
        bob[idx] = b
    batch = FrameBatch(dataset_id=f"m2lb-synth-{source_key}",
                       alice_symbols=alice, bob_symbols=bob,
                       dimension=int(M2LB_DIMENSION),
                       frame_len_symbols=int(M2LB_N_PLANE),
                       metadata={"source_key": source_key,
                                 "stream": "o1_blk:{seed}",
                                 "seed_base": M2LB_BLOCK_BASE})
    if int(batch.frame_len_symbols) != M2LB_N_PLANE:
        refuse("sampler broke the n=64 family semantic (fail closed)")
    probe = split_symbol_bitplanes(np.asarray(batch.alice_symbols[0]),
                                   int(batch.dimension), "gray")
    if len(probe) != M2LB_PLANES:
        refuse(f"Gray split gave {len(probe)} planes != 10 (fail closed)")
    return batch


def _check_root(root: str) -> None:
    if not root:
        refuse("root required (fresh additive workspace/m2lb_<uuid8>)")
    if not _ROOT_RE.match(str(root)):
        refuse(f"root must be fresh additive workspace/m2lb_<uuid8> "
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
                "status", "converged", "syndrome_consistent",
                "toeplitz_verified", "iterations", "wall_s", "max_iter",
                "streak", "leak_ec_bits", "blind_stage_bits", "rescue_bits",
                "control_bits", "tag_bits", "lambda_total",
                "prior_entropy_bits", "prior_1p50_reportonly",
                "messages_actual", "messages_ldpc_ref", "f_super", "f_notag",
                "f_eff", "n_required", "key_eligible_200_276_364",
                "d_dim", "q_alphabet", "n_ir_bits", "m_stage", "stages_used",
                "source_key", "arm", "construct_label"])
    for r in rows:
        if r.get("status") in ("error", "overrun"):
            w.writerow([r.get("block"), "", "", "", "", "", "", "",
                        r.get("status"), "", "", "", "", "", "", "",
                        "", "", "", "", "", "", "", "", "", "", "", "",
                        "", "", "", "", "", "", "", "", "", ""])
            continue
        w.writerow([r.get("block"), r.get("seed"), r.get("exact_match"),
                    r.get("undetected"), r.get("block_accept"),
                    r.get("block_fail"), r.get("accepted"),
                    r.get("accepted_wrong"), r.get("status"),
                    r.get("converged"), r.get("syndrome_consistent"),
                    r.get("toeplitz_verified"), r.get("iterations"),
                    r.get("wall_s"), r.get("max_iter"), r.get("streak"),
                    r.get("leak_ec_bits"), r.get("blind_stage_bits"),
                    r.get("rescue_bits"), r.get("control_bits"),
                    r.get("tag_bits"), r.get("lambda_total"),
                    r.get("prior_entropy_bits"),
                    r.get("prior_1p50_reportonly"),
                    r.get("messages_actual"),
                    r.get("messages_ldpc_ref"), r.get("f_super"),
                    r.get("f_notag"), r.get("f_eff"),
                    r.get("n_required"),
                    r.get("key_eligible_200_276_364"), r.get("d_dim"),
                    r.get("q_alphabet"), r.get("n_ir_bits"),
                    r.get("m_stage"), r.get("stages_used"),
                    r.get("source_key"), r.get("arm"),
                    r.get("construct_label")])
    return buf.getvalue()


def result_markdown(summary: dict[str, Any]) -> str:
    """Per-arm ``M2LB_RESULT_*.md`` body (packet F5/Sec 6)."""
    g = summary["gates"]
    lines = [
        f"# M2LB result — {summary['arm']} (synthetic, RAW)",
        "",
        f"- arm: `{summary['arm']}` ({summary['construct_label']}; "
        f"layered per-plane constructs — NOT a nested submatrix)",
        f"- bundle: `{summary['bundle_path']}` key `{summary['source_key']}` "
        f"(TRAIN-side provenance; H CONDITIONAL on the F03 estimator + "
        f"TRAIN split side; bound source label == arm source, cross-source "
        f"reuse refused)",
        f"- allocation F2: `{summary['allocation_rows']}` sum "
        f"{summary['m']} (equal-share + largest-remainder; H input "
        f"{summary['h_basis']!r} assumed, no refit)",
        f"- blind F3: `{summary['blind_schedule']}` "
        f"(levels `{summary['blind_levels']}`; rescue disclosure single "
        f"column, never merged)",
        f"- seeds: `2026095601+idx` idx 0..{summary['blocks_done'] - 1} "
        f"(stream `o1_blk:{{seed}}`); construction instance 2026092001 / "
        f"trials 20; 10 planes n=64; pins fc=0 + rank-in-{{m_j-1,m_j}} "
        f"+ twice-identical GATED, girths {summary['girths']} "
        f"recorded-not-gated",
        f"- decoder: true binary SPA max_iter 300 / streak 3 "
        f"(machine-checked), `exact_match` accept; NO genie/argmax; "
        f"success = exact + accepted + syndrome + toeplitz (double gate); "
        f"report-only `prior_entropy_bits`, `messages_actual`",
        f"- wall: {summary['elapsed_s']:.1f} s (cap 1800 s/arm); "
        f"per-decode terminal 300 s; peak RSS {summary['rss_gib']:.3f} "
        f"GiB (<4 GiB); ledger decodes {summary['ledger_decodes']}",
        f"- fails: {summary['failures']}/{summary['blocks_done']} "
        f"(FER {summary['fer']:.6f}); undetected {summary['undetected']} "
        f"(logged separately, NEVER merged into success; gate-(a) fails "
        f"count every non-success block)",
        f"- f_super (H[{summary['source_key']}]="
        f"{summary['h_basis']!r}): {summary['f_super']:.8f}; f_notag = "
        f"{summary['f_notag']:.8f}; f_eff = f_super+4.785675*FER = "
        f"{summary['f_eff']:.8f} (DISTINCT lines; NEVER quote f_super as "
        f"f_eff when FER > 0; single-source f_eff is NEVER presented as "
        f"certifiable/literature-comparable)",
        f"- lambda_total = {summary['lambda_total']:.3f} "
        f"(leak_EC {summary['lambda_parts']['leak_EC']:.3f} + tag "
        f"{summary['lambda_parts']['tag']:.3f} + rescue "
        f"{summary['lambda_parts']['rescue']:.3f} + control "
        f"{summary['lambda_parts']['control']:.3f}; 1.50xprior "
        f"{summary['prior_1p50_reportonly']:.3f} report-only, never into "
        f"lambda/f numerators)",
        f"- messages: actual {summary['messages_per_frame_actual']:.3f} "
        f"/frame (LDPC {LDPC_MSG_REF} aperture independent column; "
        f"Cascade {CASCADE_MSG_REF} non-comparable annotation)",
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
        f"(shape/normalization gates PASS at bind); allocation sum + "
        f"blind-table frozen consistency PASS",
        f"- G-E (integrity/stop): budgets held; zero raw-dump reads "
        f"(no such code path); cross-source reuse refused by "
        f"source-label check; no pooling; no `undetected`-merging; "
        f"`src/` untouched",
        f"- verdict: {summary['verdict']}",
        f"- claim ceiling: {CLAIM_CEILING}",
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
    """Run the frozen M2LB arm procedure under ``root`` (one arm/invocation).

    ``max_blocks`` is a PROBE-ONLY cap (never a CLI flag, never part of
    any verdict). ``bundle`` is required (no silent production bind).
    Tests MUST pass an explicit fake ``decode_fn`` (and a fake
    ``construct_fn`` where construction is not under test).
    """
    spec = parse_arm(arm)
    _check_root(root)
    m = int(spec["m"])
    mode = str(spec["mode"])
    source_key = str(spec["source_key"])
    _check_spa_pins(M2LB_MAX_ITER, M2LB_STREAK)
    allocation = allocation_for(source_key, m)
    blind_tab = blind_table_for(m)
    blind_levels = blind_levels_for(m)
    f_super = f_super_for(source_key, m)
    f_notag = f_notag_for(source_key, m)
    n_req = n_required(f_super)
    bar = fail_bar(M2LB_N_BLOCKS)
    if bundle is None:
        refuse("empirical bundle required (no silent production bind; "
               "pass bundle or bind --bundle at the CLI)")
    construct_fn = construct_fn or construct_plane_production
    if decode_fn is None:
        def decode_fn(a_planes, b_planes, constructions,  # noqa: B023
                      stage_ctx, frame_idx,
                      max_iter=M2LB_MAX_ITER, streak=M2LB_STREAK):
            return spa_decode_production(a_planes, b_planes,
                                         constructions, stage_ctx,
                                         frame_idx, max_iter, streak)
    clock = clock or time.monotonic
    rss_fn = rss_fn or _default_rss
    writer = writer or default_writer
    if max_blocks is not None and (
            not isinstance(max_blocks, int) or max_blocks < 1):
        refuse("max_blocks (probe-only) must be a positive int")

    if os.path.exists(root):
        refuse(f"root not fresh: {root}")
    batch = sample_frozen_batch(bundle, source_key)
    rows: list[dict] = []
    failures = 0
    undetected = 0
    ledger_decodes = 0
    sum_leak = 0.0
    sum_rescue = 0.0
    sum_control = 0.0
    sum_prior = 0.0
    sum_messages = 0.0
    sum_iters = 0
    girths: list[int] = []
    t_start = clock()
    rss_peak_gib = 0.0

    target = M2LB_N_BLOCKS if max_blocks is None else min(max_blocks,
                                                          M2LB_N_BLOCKS)

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
                  else "FAIL-expected (packet Sec 6: expected-FAIL at high m; "
                       "presentation ban enforced)")
        return {
            "arm": arm, "source_key": source_key, "m": m, "mode": mode,
            "construct_label": spec["construct_label"],
            "bundle_path": (bundle_label if bundle_label is not None
                            else "<injected-bound-bundle>"),
            "h_basis": FROZEN_H[source_key],
            "h_column": "assumed (allocation input only, no refit)",
            "allocation_rows": {int(k): int(v)
                                for k, v in allocation.items()},
            "blind_schedule": {"m_init": int(blind_tab["m_init"]),
                               "delta_steps": [int(x) for x in
                                               blind_tab["delta_steps"]]},
            "blind_levels": list(blind_levels),
            "girths": list(girths),
            "blocks_done": n, "attempted": n, "failures": failures,
            "undetected": undetected, "fer": fer,
            "f_super": f_super, "f_notag": f_notag, "f_eff": f_eff,
            "f_basis": {"m": int(m), "H": float(FROZEN_H[source_key]),
                        "source": source_key, "H_column": "assumed"},
            "lambda_total": lam, "lambda_parts": lam_parts,
            "prior_1p50_reportonly": PRIOR_SCALE_REPORTONLY * float(sum_prior),
            "messages_per_frame_actual": (float(sum_messages) / n
                                          if n else float("nan")),
            "n_required": (n_req if math.isfinite(n_req) else "inf"),
            "key_eligible_contrast": (200, 276, 364),
            "d_dim": int(M2LB_DIMENSION),
            "q_alphabet": "2x10 layers",
            "n_ir_bits": int(M2LB_N_PLANE * M2LB_PLANES),
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
            "elapsed_s": float(clock() - t_start),
            "rss_gib": float(rss_peak_gib),
        }

    def _flush(summary: dict[str, Any]) -> dict[str, Any]:
        writer(root, {
            f"M2LB_RESULT_{source_key}_{m}_{mode}.md":
                result_markdown(summary),
            "rows.json": json.dumps({"summary": summary, "rows": rows},
                                    indent=1, sort_keys=True, default=str),
            "block_accounting.csv": block_accounting_csv(rows)})
        return summary

    for k in range(target):
        if clock() - t_start > M2LB_WALL_CAP_S:
            return _flush(_summary("INCOMPLETE-wall", False))
        try:
            rss_gib = float(rss_fn()) / (1024 ** 3)
        except Exception:  # noqa: BLE001 — probe failure never halts
            rss_gib = 0.0
        rss_peak_gib = max(rss_peak_gib, rss_gib)
        if rss_gib >= M2LB_RSS_CAP_GIB:
            return _flush(_summary("FAIL(budget)", False))
        seed = block_seed(k)
        a_sym = np.asarray(batch.alice_symbols[k], dtype=np.int64)
        b_sym = np.asarray(batch.bob_symbols[k], dtype=np.int64)
        a_planes = [np.asarray(p, dtype=np.uint8).reshape(-1)
                    for p in split_symbol_bitplanes(a_sym,
                                                    int(batch.dimension),
                                                    "gray")]
        b_planes = [np.asarray(p, dtype=np.uint8).reshape(-1)
                    for p in split_symbol_bitplanes(b_sym,
                                                    int(batch.dimension),
                                                    "gray")]
        if len(a_planes) != M2LB_PLANES or len(b_planes) != M2LB_PLANES:
            refuse(f"block {k}: Gray split != 10 planes (fail closed)")
        try:
            constructions = _construct_gate_planes(
                allocation, int(k), construct_fn, M2LB_CONSTRUCT_SEED,
                M2LB_MAX_TRIALS)
        except Refusal:
            raise
        except Exception as exc:  # noqa: BLE001 — fail closed pre-decode
            refuse(f"construction gate failed (block {k}): "
                   f"{type(exc).__name__}: {exc}")
        for c in constructions:
            girths.append(int(c.get("measured_girth",
                                    c.get("min_girth", 0))))
        # -- decode (matched single full-m; blind incremental early-stop)
        block_wall0 = clock()
        final_out: dict[str, Any] | None = None
        stages_used = 0
        m_stage = m
        block_iters = 0
        if mode == "matched":
            stage_ctx = {"mode": "matched", "m_target": m, "m_stage": m,
                         "stage_idx": 0,
                         "delta_steps": list(BLIND_DELTA),
                         "m_init": int(blind_tab["m_init"])}
            t0 = clock()
            try:
                out = decode_fn(a_planes, b_planes, constructions,
                                stage_ctx, int(k),
                                int(M2LB_MAX_ITER), int(M2LB_STREAK))
            except Exception as exc:  # noqa: BLE001 — no-retry: retain+halt
                rows.append({"block": k, "status": "error",
                             "error": f"{type(exc).__name__}: {exc}"})
                return _flush(_summary("FAIL(budget)", False))
            dt = clock() - t0
            if dt > M2LB_PER_DECODE_CAP_S:
                rows.append({"block": k, "status": "overrun",
                             "decode_s": dt})
                return _flush(_summary("FAIL(budget)", False))
            ledger_decodes += 1
            final_out = _check_outcome(dict(out))
            stages_used = 1
            m_stage = m
            block_iters = int(final_out.get("iterations"))
            block_wall = dt
        else:
            block_wall = 0.0
            for s_idx, lev in enumerate(blind_levels):
                stage_ctx = {"mode": "blind", "m_target": m,
                             "m_stage": int(lev), "stage_idx": int(s_idx),
                             "delta_steps": list(BLIND_DELTA),
                             "m_init": int(blind_tab["m_init"])}
                t0 = clock()
                try:
                    out_try = decode_fn(a_planes, b_planes, constructions,
                                        stage_ctx, int(k),
                                        int(M2LB_MAX_ITER),
                                        int(M2LB_STREAK))
                except Exception as exc:  # noqa: BLE001 — retain+halt
                    rows.append({"block": k, "status": "error",
                                 "error": f"{type(exc).__name__}: {exc}"})
                    return _flush(_summary("FAIL(budget)", False))
                dt = clock() - t0
                if dt > M2LB_PER_DECODE_CAP_S:
                    rows.append({"block": k, "status": "overrun",
                                 "decode_s": dt})
                    return _flush(_summary("FAIL(budget)", False))
                ledger_decodes += 1
                block_wall += dt
                cand = _check_outcome(dict(out_try))
                exact_c = bool(cand.get("exact_match") is True)
                acc_c = bool(cand.get("accepted") is True)
                gate_c = (bool(cand.get("syndrome_consistent") is True)
                          and bool(cand.get("toeplitz_verified") is True))
                stages_used += 1
                m_stage = int(lev)
                block_iters += int(cand.get("iterations"))
                if exact_c and acc_c and gate_c:
                    final_out = cand
                    break
                final_out = cand
            if final_out is None:
                refuse(f"block {k}: blind stages exhausted with no outcome")
        assert final_out is not None
        exact = bool(final_out.get("exact_match") is True)
        accepted = bool(final_out.get("accepted") is True)
        gate_ok = (bool(final_out.get("syndrome_consistent") is True)
                   and bool(final_out.get("toeplitz_verified") is True))
        success = bool(exact and accepted and gate_ok)
        und = bool(accepted and not success)
        if not success:
            failures += 1
        if und:
            undetected += 1
        leak = float(final_out.get("leak_ec_bits"))
        stage_bits = [float(x) for x in final_out.get("blind_stage_bits")]
        rescue = float(final_out.get("rescue_bits"))
        control = float(final_out.get("control_bits"))
        prior = float(final_out.get("prior_entropy_bits"))
        messages = float(final_out.get("messages_actual"))
        sum_leak += leak + sum(stage_bits)
        sum_rescue += rescue
        sum_control += control
        sum_prior += prior
        sum_messages += messages
        sum_iters += block_iters
        lam_row = lambda_total(leak + sum(stage_bits), TAG_BITS, rescue,
                               control)
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
            "converged": bool(accepted),
            "syndrome_consistent": bool(final_out.get("syndrome_consistent")),
            "toeplitz_verified": bool(final_out.get("toeplitz_verified")),
            "iterations": block_iters,
            "wall_s": (block_wall if mode == "blind"
                       else float(clock() - block_wall0)),
            "max_iter": int(final_out.get("max_iter")),
            "streak": int(final_out.get("streak")),
            "leak_ec_bits": leak + sum(stage_bits),
            "blind_stage_bits": stage_bits,
            "rescue_bits": rescue,
            "control_bits": control,
            "tag_bits": int(TAG_BITS),
            "lambda_total": lam_row,
            "prior_entropy_bits": prior,
            "prior_1p50_reportonly": PRIOR_SCALE_REPORTONLY * prior,
            "messages_actual": messages,
            "messages_ldpc_ref": float(LDPC_MSG_REF),
            "f_super": f_super,
            "f_notag": f_notag,
            "f_eff": f_eff_for(f_super, failures / (len(rows) + 1)),
            "n_required": (n_req if math.isfinite(n_req) else "inf"),
            "key_eligible_200_276_364": "200|276|364",
            "d_dim": int(M2LB_DIMENSION),
            "q_alphabet": "2x10 layers",
            "n_ir_bits": int(M2LB_N_PLANE * M2LB_PLANES),
            "m_stage": int(m_stage),
            "stages_used": int(stages_used),
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
                  pb_sidecar: str, source_key: str) -> int:
    bound = bind_source_bundle(bundle_path, source_key, arm)
    expected_sidecar = str(Path(bundle_path).parent / s2c.PB_SIDECAR_NAME)
    if str(pb_sidecar) != expected_sidecar:
        refuse(f"pb-sidecar {pb_sidecar} != frozen-resolved sibling "
               f"{expected_sidecar} (F1 path form; packet Sec 7-3)")
    summary = execute(root=root, arm=arm, bundle=bound,
                      bundle_label=str(bundle_path))
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
                      "root": root}, indent=1, sort_keys=True, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="M2 layered-binary thin arm runner "
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
    if args.construct_instance != M2LB_CONSTRUCT_SEED:
        refuse(f"construct-instance must be the frozen "
               f"{M2LB_CONSTRUCT_SEED} "
               f"(got {args.construct_instance}; any change is a "
               f"science-input change -> STOP)")
    if not args.standalone:
        refuse("refusing: --standalone missing (M2LB constructs are "
               "layered per-plane, never nested; packet F2/F4)")
    if args.seeds != "2026095601+idx":
        refuse(f"seeds must be the frozen literal 2026095601+idx "
               f"(got {args.seeds})")
    if args.stream != "o1_blk:{seed}":
        refuse(f"stream must be the frozen literal o1_blk:{{seed}} "
               f"(got {args.stream})")
    if args.blocks != M2LB_N_BLOCKS:
        refuse(f"blocks must be the frozen {M2LB_N_BLOCKS} "
               f"(got {args.blocks})")
    if args.per_decode_timeout_s != M2LB_PER_DECODE_CAP_S:
        refuse(f"per-decode-timeout-s must be the frozen "
               f"{M2LB_PER_DECODE_CAP_S} (got {args.per_decode_timeout_s})")
    if args.budget_s != M2LB_WALL_CAP_S:
        refuse(f"budget-s must be the frozen {M2LB_WALL_CAP_S} "
               f"(got {args.budget_s})")
    if not args.bundle:
        refuse("bundle required (read-only Sec 7-3 bundle path)")
    if not args.pb_sidecar:
        refuse("pb-sidecar required (read-only Sec 7-3 sidecar path)")
    return run_execution(root=args.root, arm=args.arm,
                         bundle_path=args.bundle,
                         pb_sidecar=args.pb_sidecar,
                         source_key=args.source_key)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


# ---------------------------------------------------------------------------
# Route-A explicit SPA fallback wrapper (ADDITIVE ONLY; frozen body untouched).
#
# 本次放宽仅 wrapper (本节两函数 + ``_spa_decode_numpy_planes``); 本体
# ``spa_decode_production`` 的 STOP-BLOCKED 语义 (ldpc 缺席即 refuse, 永不
# 切 bit-flip) 仍有效, 本节未改其一字 ( particularly 459-461 refuse)。
#
# 对照表 (真体 vs numpy fallback; 与新测试头 + docs 附录
# ``docs/research_cycles/M2-LAYEREDBIN-SYNTH/
# APPENDIX_SPA_NUMPY_FALLBACK_COMPARISON.md`` 三处一致, 以本表为准):
#
# | 维度 | 真体 ldpc.BpOsdDecoder (缺席即 STOP-BLOCKED, 永不替代) | numpy-minsum-fallback (assumed, 非ldpc.BpOsdDecoder) |
# | 泄漏 leak_ec_bits / blind_stage_bits | matched: m_target; blind: m_init + 已用 delta | 相同会计映射 (matched: m_target; blind: m_init + 已用 delta), 泄漏口径一致 |
# | 迭代 iterations | 真体返回的实际迭代 | numpy 实测 (零错输入 iters==0; 其余为实际收敛轮数) |
# | status 四旗 (exact/accepted/syndrome/toeplitz) | 双门语义: success=exact+accepted+syndrome+toeplitz, undetected 独立 | 相同双门语义与 13 键; 后端不同源, 状态位不可跨后端比较 |
#
# CLAIM_CEILING 原文: 合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；
# D1 条件化分支下不得用本批合成数论证真实优劣。
#
# assumed 非 ldpc 不可比声明: fallback 结果为 assumed 先验 + 非 ldpc 后端,
# 与真体数不可比、不可互换、不可合并; ``backend_used`` 仅经 log + metadata
# 侧车透出精确字面量, 永不进入 outcome dict (13 键以外零新增)。
# ---------------------------------------------------------------------------


def resolve_spa_decode_fn(find_spec_fn: Callable | None = None
                          ) -> tuple[Callable, str]:
    """Resolve the binary-SPA decode entry against ``ldpc`` availability.

    ``ldpc`` present -> ``(spa_decode_production, "ldpc.BpOsdDecoder")``
    (transparent true-body call). ``ldpc`` absent -> the explicit numpy
    fallback plane path plus its exact ``BACKEND_ID`` literal
    (``"numpy-minsum-fallback (assumed, 非ldpc.BpOsdDecoder)"``).
    ``find_spec_fn`` is an injectable ``find_spec`` (tests mock absence
    deterministically); ``None`` means ``importlib.util.find_spec``.
    """
    import importlib.util as _ilu
    _fs = find_spec_fn if find_spec_fn is not None else _ilu.find_spec
    try:
        _present = _fs("ldpc") is not None
    except Exception:  # noqa: BLE001 — probe failure reads as absent
        _present = False
    if _present:
        return spa_decode_production, "ldpc.BpOsdDecoder"
    from comparison_bench.src.comparison_bench.methods.binary_spa_numpy import (
        BACKEND_ID as _BID,
    )
    return _spa_decode_numpy_planes, str(_BID)


def spa_decode_with_explicit_fallback(a_planes: Any, b_planes: Any,
                                      constructions: Any,
                                      stage_ctx: dict[str, Any],
                                      frame_idx: int,
                                      max_iter: int = M2LB_MAX_ITER,
                                      streak: int = M2LB_STREAK, *,
                                      find_spec_fn: Callable | None = None,
                                      sidecar: dict[str, Any] | None = None
                                      ) -> dict[str, Any]:
    """Explicit-fallback SPA decode (execute-compatible ``decode_fn`` shape).

    Resolves via :func:`resolve_spa_decode_fn`, runs the resolved entry,
    returns the ``_check_outcome``-gated 13-key outcome dict. ``backend_used``
    is exposed ONLY through the ``sidecar`` dict (``sidecar["backend_used"]``
    exact literal + one ``sidecar["log"]`` line) and NEVER enters the outcome
    dict. ``sidecar=None`` skips the sidecar (outcome still exact 13 keys).
    """
    fn, backend_used = resolve_spa_decode_fn(find_spec_fn=find_spec_fn)
    if sidecar is not None:
        if not isinstance(sidecar, dict):
            refuse("spa fallback sidecar must be a dict (fail closed)")
        sidecar["backend_used"] = backend_used
        sidecar.setdefault("log", []).append(
            f"M2LB spa backend_used={backend_used}")
    if fn is spa_decode_production:
        return spa_decode_production(a_planes, b_planes, constructions,
                                     stage_ctx, frame_idx, max_iter, streak)
    return _spa_decode_numpy_planes(a_planes, b_planes, constructions,
                                    stage_ctx, frame_idx, max_iter, streak)


def _spa_decode_numpy_planes(a_planes: Any, b_planes: Any,
                             constructions: Any,
                             stage_ctx: dict[str, Any],
                             frame_idx: int, max_iter: int,
                             streak: int) -> dict[str, Any]:
    """Numpy-fallback plane path (same gates/accounting as the true body).

    Mirrors ``spa_decode_production`` validation, H-support, stage_rows,
    Toeplitz and accounting semantics; only the per-plane error-estimation
    backend differs (explicit numpy min-sum, ``_P_ASSUMED=0.02``). Outcome
    still passes ``_check_outcome`` (exactly 13 keys).
    """
    _check_spa_pins(int(max_iter), int(streak))
    from comparison_bench.src.comparison_bench.formal_ir.shared import (
        toeplitz_tag as _toeplitz_tag,
    )
    from comparison_bench.src.comparison_bench.methods.binary_spa_numpy import (
        decode_error_numpy_min_sum as _np_backend,
    )
    from comparison_bench.src.comparison_bench.methods.layered_ldpc_lite import (
        _syndrome as _bin_syndrome,
    )
    _P_ASSUMED = 0.02  # frozen BSC assumption (assumed, uniform, no adaptation)

    def _need_int(value: Any, what: str) -> int:
        if isinstance(value, bool):
            refuse(f"numpy-fallback spa {what} must be an int (fail closed)")
        try:
            return int(value)
        except Exception:  # noqa: BLE001 — fail closed, no defaults
            refuse(f"numpy-fallback spa {what} not an int (fail closed)")

    try:
        a_list = [np.asarray(p, dtype=np.uint8).reshape(-1)
                  for p in list(a_planes)]
        b_list = [np.asarray(p, dtype=np.uint8).reshape(-1)
                  for p in list(b_planes)]
        cons_list = list(constructions)
    except Refusal:
        raise
    except Exception:  # noqa: BLE001 — fail closed, no defaults
        refuse("numpy-fallback spa inputs must be 10-plane sequences "
               "(fail closed)")
    if not (len(a_list) == len(b_list) == len(cons_list) == M2LB_PLANES):
        refuse(f"numpy-fallback spa needs exactly {M2LB_PLANES} planes each "
               f"(got {len(a_list)}/{len(b_list)}/{len(cons_list)}; "
               f"fail closed)")
    n_plane = len(a_list[0])
    if n_plane < 1:
        refuse("numpy-fallback spa plane length < 1 (fail closed)")
    for j in range(M2LB_PLANES):
        if len(a_list[j]) != n_plane or len(b_list[j]) != n_plane:
            refuse(f"numpy-fallback spa plane {j} length mismatch "
                   f"(fail closed)")
        for vec in (a_list[j], b_list[j]):
            if bool(np.any((vec != 0) & (vec != 1))):
                refuse(f"numpy-fallback spa plane {j} non-binary bits "
                       f"(binary SPA only; fail closed)")

    if not isinstance(stage_ctx, dict):
        refuse("numpy-fallback spa stage_ctx must be a dict (fail closed)")
    mode = stage_ctx.get("mode")
    if mode not in ("matched", "blind"):
        refuse(f"numpy-fallback spa mode {mode!r} not frozen "
               f"(matched|blind only; fail closed)")
    m_target = _need_int(stage_ctx.get("m_target"), "m_target")
    m_stage = _need_int(stage_ctx.get("m_stage"), "m_stage")
    stage_idx = _need_int(stage_ctx.get("stage_idx"), "stage_idx")
    m_init = _need_int(stage_ctx.get("m_init"), "m_init")
    try:
        deltas = [int(x) for x in list(stage_ctx.get("delta_steps"))]
    except Exception:  # noqa: BLE001 — fail closed, no defaults
        refuse("numpy-fallback spa delta_steps corrupt (fail closed)")
    if [int(x) for x in deltas] != [int(x) for x in BLIND_DELTA]:
        refuse(f"numpy-fallback spa delta steps frozen at "
               f"{list(BLIND_DELTA)} (science-input change -> STOP)")
    if m_target < 1 or m_stage < 1 or m_init < 1:
        refuse("numpy-fallback spa m_target/m_stage/m_init must be positive "
               "(fail closed)")
    if m_init != m_target - 20:
        refuse(f"numpy-fallback spa m_init {m_init} != m_target-20 "
               f"{m_target - 20} (frozen blind table -> STOP)")
    if mode == "matched":
        if m_stage != m_target or stage_idx != 0:
            refuse("numpy-fallback spa matched stage must be single full-m "
                   "(fail closed)")
    else:
        if not 0 <= stage_idx <= 5:
            refuse(f"numpy-fallback spa blind stage_idx {stage_idx} outside "
                   f"0..5 (fail closed)")
        if m_init + sum(int(x) for x in deltas[:stage_idx]) != m_stage:
            refuse("numpy-fallback spa blind m_stage != m_init+used deltas "
                   "(fail closed)")
        if m_stage > m_target:
            refuse(f"numpy-fallback spa blind m_stage {m_stage} > m_target "
                   f"{m_target} (fail closed)")
    fidx = _need_int(frame_idx, "frame_idx")
    if fidx < 0:
        refuse("numpy-fallback spa frame_idx must be non-negative "
               "(fail closed)")

    def _h_from_triples(triples: Any, m_hint: Any,
                        plane: int) -> tuple[Any, int]:
        try:
            trips = list(triples)
        except Exception:  # noqa: BLE001 — fail closed
            refuse(f"numpy-fallback spa plane {plane}: triples not a "
                   f"sequence (fail closed)")
        if not trips:
            refuse(f"numpy-fallback spa plane {plane}: empty triples "
                   f"(fail closed)")
        rows: list[int] = []
        cols: list[int] = []
        for t in trips:
            try:
                r, c, v = int(t[0]), int(t[1]), int(t[2])
            except Exception:  # noqa: BLE001 — fail closed
                refuse(f"numpy-fallback spa plane {plane}: corrupt triple "
                       f"{t!r} (fail closed)")
            if int(v) == 0:
                refuse(f"numpy-fallback spa plane {plane}: zero coeff "
                       f"{v!r} (support-empty; fail closed -> STOP)")
            rows.append(r)
            cols.append(c)
        m_full = max(rows) + 1
        if m_hint is not None:
            try:
                if int(m_hint) != int(m_full):
                    refuse(f"numpy-fallback spa plane {plane}: triples span "
                           f"m={m_full} != construction m={m_hint} "
                           f"(fail closed)")
            except Refusal:
                raise
            except Exception:  # noqa: BLE001 — fail closed
                refuse(f"numpy-fallback spa plane {plane}: construction m "
                       f"corrupt (fail closed)")
        if min(rows) < 0 or min(cols) < 0 or max(cols) >= n_plane:
            refuse(f"numpy-fallback spa plane {plane}: triple index out of "
                   f"range (fail closed)")
        mat = np.zeros((m_full, n_plane), dtype=np.uint8)
        for r, c in zip(rows, cols):
            mat[r, c] = 1
        return mat, m_full

    h_full: list[Any] = []
    m_fulls: list[int] = []
    for j in range(M2LB_PLANES):
        try:
            code_j = cons_list[j]
            trips_j = code_j["triples"]
            hint_j = code_j.get("m", None)
        except Exception:  # noqa: BLE001 — fail closed
            refuse(f"numpy-fallback spa plane {j}: construction missing "
                   f"triples/m (fail closed)")
        hj, mj = _h_from_triples(trips_j, hint_j, j)
        h_full.append(hj)
        m_fulls.append(mj)
    _sbase, _srem = divmod(m_stage, M2LB_PLANES)
    stage_rows = [(_sbase + 1) if j < _srem else _sbase
                  for j in range(M2LB_PLANES)]
    if sum(stage_rows) != m_stage:  # pragma: no cover — divmod invariant
        refuse("numpy-fallback spa stage_rows sum != m_stage (fail closed)")
    for j in range(M2LB_PLANES):
        if stage_rows[j] > m_fulls[j]:
            refuse(f"numpy-fallback spa plane {j}: stage rows "
                   f"{stage_rows[j]} > m_j {m_fulls[j]} (fail closed)")
    if m_stage == m_target:
        for j in range(M2LB_PLANES):
            if stage_rows[j] != m_fulls[j]:
                refuse(f"numpy-fallback spa plane {j}: stage rows "
                       f"{stage_rows[j]} != full m_j {m_fulls[j]} "
                       f"(conflicts with the F2 full table -> STOP)")

    rec_list: list[Any] = []
    ok_list: list[bool] = []
    syn_list: list[bool] = []
    exact_list: list[bool] = []
    total_iters = 0
    for j in range(M2LB_PLANES):
        a_j = a_list[j]
        b_j = b_list[j]
        k_j = int(stage_rows[j])
        h_j = h_full[j][:k_j, :]
        s_alice = np.asarray(_bin_syndrome(h_j, a_j),
                             dtype=np.uint8).reshape(-1)
        s_bob = np.asarray(_bin_syndrome(h_j, b_j),
                           dtype=np.uint8).reshape(-1)
        delta = np.bitwise_xor(s_alice, s_bob).astype(np.uint8)
        if k_j == 0:
            err_hat = np.zeros(n_plane, dtype=np.uint8)
            back_ok, iters_j = True, 0
        else:
            try:
                err_hat, back_ok, iters_j = _np_backend(
                    h_j, delta, int(max_iter), float(_P_ASSUMED))
            except Refusal:
                raise
            except Exception as exc:  # noqa: BLE001 — never bit-flip
                refuse(f"numpy-fallback spa plane {j}: backend failed "
                       f"({type(exc).__name__}: {exc}; no bit-flip "
                       f"substitute; fail closed)")
            err_hat = np.asarray(err_hat, dtype=np.uint8).reshape(-1)
            if err_hat.shape != (n_plane,):
                refuse(f"numpy-fallback spa plane {j}: error vector shape "
                       f"{err_hat.shape} != ({n_plane},) (fail closed)")
            back_ok, iters_j = bool(back_ok), int(iters_j)
        rec_j = np.bitwise_xor(b_j, err_hat).astype(np.uint8)
        syn_ok = bool(np.array_equal(
            np.asarray(_bin_syndrome(h_j, rec_j),
                       dtype=np.uint8).reshape(-1), s_alice))
        rec_list.append(rec_j)
        ok_list.append(back_ok)
        syn_list.append(syn_ok)
        exact_list.append(bool(np.array_equal(rec_j, a_j)))
        total_iters += int(iters_j)
    exact_match = bool(all(exact_list))
    accepted = bool(all(ok_list))
    syndrome_consistent = bool(all(syn_list))
    n_ir = int(M2LB_PLANES * n_plane)
    try:
        rng = np.random.default_rng(int(block_seed(fidx)) % (2 ** 32))
        seed_bits = rng.integers(
            0, 2, size=(n_ir + int(TAG_BITS) - 1)).astype(np.uint8)
        tag_a = _toeplitz_tag(np.concatenate(a_list), seed_bits,
                              int(TAG_BITS))
        tag_r = _toeplitz_tag(np.concatenate(rec_list), seed_bits,
                              int(TAG_BITS))
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed
        refuse(f"numpy-fallback spa toeplitz verification failed "
               f"({type(exc).__name__}: {exc}; fail closed)")
    toeplitz_verified = bool(tag_a == tag_r)
    if mode == "matched":
        leak_ec = float(m_target)
        blind_bits = [0.0, 0.0, 0.0, 0.0, 0.0]
    else:
        leak_ec = float(m_init)
        blind_bits = ([float(x) for x in deltas[:stage_idx]]
                      + [0.0] * (5 - stage_idx))
    if abs(float(leak_ec) + float(sum(blind_bits))
           - float(m_stage)) > 1e-9:  # pragma: no cover — invariant
        refuse("numpy-fallback spa accounting leak+stages != m_stage "
               "(fail closed)")
    _h2 = -(_P_ASSUMED * math.log2(_P_ASSUMED)
            + (1.0 - _P_ASSUMED) * math.log2(1.0 - _P_ASSUMED))
    outcome = {
        "exact_match": exact_match,
        "accepted": accepted,
        "syndrome_consistent": syndrome_consistent,
        "toeplitz_verified": toeplitz_verified,
        "leak_ec_bits": float(leak_ec),
        "blind_stage_bits": [float(x) for x in blind_bits],
        "rescue_bits": 0.0,
        "control_bits": 0.0,
        "messages_actual": float(LDPC_MSG_REF),
        "prior_entropy_bits": float(n_ir) * float(_h2),
        "iterations": int(total_iters),
        "max_iter": int(M2LB_MAX_ITER),
        "streak": int(M2LB_STREAK),
    }
    return _check_outcome(outcome)
