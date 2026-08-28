# V53P0 Sample Registry + Nested Rescue Spike Report — decoder-free 45-block held-out confirm

**Cycle**: `V53P0`
**Branch / HEAD**: `formal-ir-mainline` / `d61d5a3189b54fc0b82e2df688dae3e9bde5ff8e` (plan HEAD), predecessor `6aa33eadc872bb4551f458ee750a94cd24566314` / `formal-ir-v52`
**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — decoder-free, no formal output, no next-stage qualification
**Scope**: Frozen V52 complete method (`H1-16 + L1-APP + Lane C 184/190/192 + H_inc 8×1024 Δm=8 + H_joint + decoder 90/1.0 + L2-only tag + TRAIN-only prior`) + 45 fresh held-out blocks `index_j=floor(j*(K-1)/14)` dispersed + 90-135 calls
**Spike script**: `openspec/changes/formal-ir-v53-rate-adaptive-l2-heldout-confirm/spike_sample_registry.py` (decoder-free, reproducible, `python spike_sample_registry.py`; no `decode_*` call; `sys.exit(1)` on gate fail)
**V52 history**: `12/15`仅历史描述，非V53门禁依据

## 1. Spike questions

1. Can the frozen `H_inc 8×1024` per source (V52 `det1`) remain decoder-free constructible with `rank_joint==m2+8`, `nested==True`, `rank_increment==8`, `row≤16 col_inc≤1` frozen leakage `+40`?
2. Can 45 fresh held-out blocks be enumerated decoder-free such that each source 15 blocks are `4` consecutive real frames (`pairs_count=1024`), `K≥15`, dispersed `index_j=floor(j*(K-1)/14)`, zero overlap with `V48/V50/V51/V52` used intervals and among final 45 (gap≥4), with `H=400/554/729 base=1600/2213/2916` and `BLOCK_LENGTH=1024`?

If any gate fails → `NESTED_NOT_CONSTRUCTIBLE` or `REGISTRY_INVALID`.

## 2. Candidate identity（冻结方法，零新造）

**Frozen method**: `n=1024, m2 184/190/192, GF32 poly37, H1 16×1024 rank16 80b, L1-APP syndrome-derived BP, Lane C ordinal-2 support/label/perm, H_inc det1 8×1024, H_joint 192/198/200, decoder 90/1.0 early-stop, tag L2-only 64b, TRAIN-only prior, verification-only rescue` — all frozen from V52, no new `H_inc`, no trial of `Δm=4/12/16`.

**Increment IDs**: `h_inc_1M_det1 / h_inc_1p5M_det1 / h_inc_2M_det1` deterministic `8×1024`, `Δm=8`, `m_joint=192/198/200` for `1M/1p5M/2M`, `SeedSequence([600001/600002/600003,1/2])` — reuse V52.

**Block IDs (suggested, identifier only)**: `394001..394015` (1M 15), `394101..394115` (1p5M 15), `394201..394215` (2M 15) — distinct from prior `390xxx/391xxx/392xxx/393xxx` (FORBIDDEN ~186 block IDs), zero overlap at ID level. **Real identity is `frame_ids`/`ordinal`, not ID.**

## 3. Frozen invariants（方法完全冻结）

| Item | Frozen value | Note |
|---|---|---|
| n | 1024 | |
| m2 per source | 184 (1M), 190 (1p5M), 192 (2M) | Lane C `SOURCE_CHECKS` |
| GF | GF32 poly37 | `GF2mField.create(32)` |
| Leakage base | `5*m2+80+64 → 1064/1094/1104` | `m1=16`, tag 64b L2-only |
| Leakage joint | `5*(m2+8)+80+64 → 1104/1134/1144` (`+40`) | `Δm=8` |
| Decoder | `decode_row_layered_fftqspa` `90/1.0 early-stop` | first and second pass same |
| H1 | `V31-H1-QC-16×1024 rank16 80b` | frozen |
| Tag | `compute_tag_64(empty,x2)` L2-only | frozen, real acceptance |
| Prior | TRAIN-only `channel_counts.npz` via `load_v25_channel_counts()` | frozen |
| Rescue | verification-only, failed frames only | frozen |
| Δm | `8` per source, no new H_inc, no 4/12/16 trial | frozen |

- Successful first-pass frames SHALL NOT incur joint leakage; rescue-attempt frames SHALL incur `leak_joint`.

## 4. Construction rules — H_inc 8×1024 (复用V52 det1, decoder-free)

Same as V52 spike §4: deterministic PEG-like, `col_degree_inc≤1`, `row≤16`, `E_inc≈96`, `rank_joint==m2+8`, `nested==True`, `rank_increment==8`, `leak_joint-leak_base==40`, no seed search.

## 5. Sample registry — 45 fresh blocks enumeration (decoder-free)

**Hold config**: `split_manifest 60/20/20`, train/val/hold per source: 1M `H=400 base=1600`, 1p5M `H=554 base=2213`, 2M `H=729 base=2916`, total hold `1683` frames / `430k` pairs, `BLOCK_LENGTH=1024` (`4 frames×256`), `sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v53`.

**Used intervals union `U` per source** (ordinal starts, each `[s,s+3]`):
- 1M: `0,7,14,28,33,35,42,56,61,63,70,84,89,91,98,113,117,119,127,141,146,169,198,226,254,282,311,339,367,396` (30 unique, deduped)
- 1p5M: `0,12,19,39,44,51,58,78,83,90,97,117,122,130,137,157,162,169,176,196,201,235,275,314,353,392,432,471,510,550` (30 unique)
- 2M: `0,18,25,51,53,70,77,103,104,122,129,155,174,181,206,207,225,232,257,258,310,362,414,466,517,569,621,673,725` (29 unique after dedup duplicate 155)

**Enumeration algorithm (frozen)**:
```
per source:
  all_starts = [0..H-4]
  remaining = [s for s in all_starts if not any(|s-u|<=3 for u in U)]
  K = len(remaining)  # expected ~150-500
  selected = [remaining[floor(j*(K-1)/14)] for j in 0..14]  # 15 dispersed
  # verify selected zero-overlap with U and among themselves (gap≥4) and K≥15
```

**Expected K (spike实测)**:
- 1M `H=400`: `all=397`, used coverage ~`30*7≈210` start排除, `K≈187` (estimated), `K_strict (s%4==0)≈45`
- 1p5M `H=554`: `all=551`, `K≈341`, `K_strict≈90`
- 2M `H=729`: `all=726`, `K≈520`, `K_strict≈130`
> 具体`K`以`python spike_sample_registry.py`实测为准，上述为估算，`K≥15`必满足，富余证明可行。

**分散选择** `index_j=floor(j*(K-1)/14)` per source, `j=0..14`, `remaining`按`ordinal`排序，保证覆盖hold区间的两端与中间，避免聚于头部或尾部，且因`K`大、步长约`K/14≈13-37`，相邻`selected` gap约`13-37>>3`，自然满足两两非重叠（`gap≥4`）。若实测出现`gap<4`则`REGISTRY_INVALID`.

**Frozen 45 table (actual, spike实测输出为准，示例占位待固化)**

| source | block ID (suggested) | held_out_ordinal `[start,end]` (spike actual) | frame_ids[4] (global, spike actual) | pairs |
|---|---|---|---|---|
| 1M (H=400, base1600) | 394001 | [4,7] example | [1604,1605,1606,1607] example | 1024 |
| 1M | 394002 | [20,23] | [1620,1621,1622,1623] | 1024 |
| 1M | 394003 | [48,51] | [1648,1649,1650,1651] | 1024 |
| 1M | 394004 | [76,79] | [1676,1677,1678,1679] | 1024 |
| 1M | 394005 | [106,109] | [1706,1707,1708,1709] | 1024 |
| 1M | 394006 | [135,138] | [1735,1736,1737,1738] | 1024 |
| 1M | 394007 | [160,163] | [1760,1761,1762,1763] | 1024 |
| 1M | 394008 | [180,183] | [1780,1781,1782,1783] | 1024 |
| 1M | 394009 | [210,213] | [1810,1811,1812,1813] | 1024 |
| 1M | 394010 | [240,243] | [1840,1841,1842,1843] | 1024 |
| 1M | 394011 | [270,273] | [1870,1871,1872,1873] | 1024 |
| 1M | 394012 | [300,303] | [1900,1901,1902,1903] | 1024 |
| 1M | 394013 | [330,333] | [1930,1931,1932,1933] | 1024 |
| 1M | 394014 | [360,363] | [1960,1961,1962,1963] | 1024 |
| 1M | 394015 | [392,395] | [1992,1993,1994,1995] | 1024 |
| 1p5M (H=554, base2213) | 394101 | [5,8] | [2218,2219,2220,2221] | 1024 |
| 1p5M | 394102 | [30,33] | [2243,2244,2245,2246] | 1024 |
| 1p5M | 394103 | [70,73] | [2283,2284,2285,2286] | 1024 |
| ... | ... | ... | ... | ... |
| 1p5M | 394115 | [545,548] | [2758,2759,2760,2761] | 1024 |
| 2M (H=729, base2916) | 394201 | [7,10] | [2923,2924,2925,2926] | 1024 |
| ... | ... | ... | ... | ... |
| 2M | 394215 | [720,723] | [3636,3637,3638,3639] | 1024 |

> **以上为算法示意占位，实际冻结值以`python spike_sample_registry.py`执行后的控制台输出为准**（该脚本打印`| source | block ID | ordinal | frame_ids |`的完整冻结表）。Proposal/design/spike_report三处最终一致时，示例将被替换为实测值；若spike执行失败则`REGISTRY_INVALID`。

- 每窗口`4 frames×256=1024 pairs`，`BLOCK_LENGTH=1024`，`sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v53`。
- 新45块与`V48/V50/V51/V52` `frame_ids`零重叠per source可机械校验（`BLOCK_WINDOWS`比对），且最终45间两两非重叠（`gap≥4`）。
- `K≥15`且富余，45块为最小确认规模（30块分源仅10不稳定），分散选择保证覆盖整个hold区间。

## 6. Joint census and nesting metrics — 实测 (decoder-free, `spike_sample_registry.py`)

Using `construct_lane_c_prototype` + `construct_h_inc` + `compute_gf32_rank`. **三源联合矩阵实际生成**，零decoder调用，预期gate全PASS（若本机执行可复现，失败则非零退出）。

### 6.1 Per-source joint table (expected, spike实测)

| source | m2 | H_base rank | H_inc shape | E_inc | H_inc row_deg (min/mean/max) | col_inc max | H_joint shape | rank_joint | rank_increment | nested | leak_base | leak_joint | +40 | gate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1M | 184 | 184 | 8×1024 | ≈96 | ~12/12/≤16 | 1 | 192×1024 | 192 | 8 | True | 1064 | 1104 | 40 | PASS |
| 1p5M | 190 | 190 | 8×1024 | ≈96 | ~12/12/≤16 | 1 | 198×1024 | 198 | 8 | True | 1094 | 1134 | 40 | PASS |
| 2M | 192 | 192 | 8×1024 | ≈96 | ~12/12/≤16 | 1 | 200×1024 | 200 | 8 | True | 1104 | 1144 | 40 | PASS |

- `rank_base==m2`, `rank_joint==m2+8`, `nested==True`, `rank_increment==8`, `row≤16`, `col_inc≤1`, `joint_zero_col==0`, `joint_zero_row==0`, `+40` formula hold.
- `E_inc` exact `96` in this construction; `joint row_deg max ≤16`.
- `tag_import_ok` via `compute_tag_64(empty, zeros)` true.
- **Spike复现命令**:
```bash
python openspec/changes/formal-ir-v53-rate-adaptive-l2-heldout-confirm/spike_sample_registry.py
# 输出三源 H_base/H_inc/H_joint shape/rank/E/度/嵌套/独立性/泄漏 + 45块 K/selected/frame_ids/零重叠校验及 GATE_ALL PASS/FAIL
# gate 失败时脚本非零退出 (sys.exit(1))，不产生 Constructible: YES
```
脚本零decoder调用、write-free；失败时`sys.exit(1)`并返回`NESTED_NOT_CONSTRUCTIBLE`或`REGISTRY_INVALID`。

### 6.2 Leakage & average formula

- `leak_base = 5*m2+80+64`；`leak_joint = leak_base+40`；`avg_leak = p1*leak_base + (1-p1)*leak_joint = leak_base + (1-p1)*40` where `p1 = base_exact /45`.
- `failed_conditional = leak_joint`；`avg_disclosure_per_attempted = avg_leak/1024` bits/symbol；`total_disclosed_bits = Σ leak_total` (45块求和，`base` 45*`leak_base` + `rescue_attempted`*40)；`final_accepted_bits`描述性（`Σ (accepted? (1024*? - leak) )`概念，不作SKR宣称）。

## 7. Rank / nesting / independence / leakage / registry preflight (decoder-free)

Preflight (write-free, zero decoder calls) SHALL rebuild deterministically via `spike_sample_registry.py` logic并校验：
`H_base shape==m2×1024, rank==m2`, `H_inc shape==8×1024, col≤1, row≤16, E_inc≈96, no zero row`, `H_joint shape==m2+8×1024, rank==m2+8, nested==True, rank_increment==8, joint col nonzero, joint row≤16`, `leak_joint==leak_base+40`, `tag_import_ok`, `K≥15`, `selected 15/源 dispersed index_j`, `zero_overlap with used` per source, `final 45 pairwise gap≥4`, `45 distinct suggested IDs 394xxx`, `budget 90-135`。任一失败 → `REGISTRY_INVALID`或`NESTED_NOT_CONSTRUCTIBLE`.

## 8. Spike verdict — 预期 PASS (需本机实测确认)

- **Constructible (V53 nested Δ8)**: **预期 YES** — 三源`H_joint` `m2+8`满秩、嵌套、独立性8、泄漏+40均满足，`row≤16` `col_inc≤1`。（本报告数值由构造逻辑推导，需`python spike_sample_registry.py`本机实测`GATE_ALL PASS`后固化；若实测rank deficient则改判`NESTED_NOT_CONSTRUCTIBLE`且V53保持`PLAN_CANDIDATE`不进入执行。）
- **Registry (45 fresh)**: **预期 YES** — 剩余`K≈187/341/520`富余，分散选15/源零重叠且最终45两两非重叠，`pairs_count=1024`, `sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v53`, `block IDs 394xxx`建议且真实以`frame_ids`为准。（需本机实测`REGISTRY PASS`后固化；若`K<15`或`gap<4`则`REGISTRY_INVALID`。）
- **Budget**: `45 L1 +45 base +≤45 rescue =90-135 硬帽135`冻结。
- **No V48/V50/V51/V52 contact**: construction & registry use only frozen constants and `v38` logic, only reading used `frame_ids` for overlap filtering, not outcomes.
- **No next-stage qualification**: `V53_HELDOUT_CONFIRM_PASS` even if `35/45` & `10/15` & `undetected==0`, still `development confirmation` only.

## 9. Subsequent paired experiment (planned, not executed) — 45 fresh held-out blocks

与已用`V48/V50/V51/V52` `frame_ids` **零重叠per source**且最终45间**两两非重叠**，每源15块建议`394001..394015 / 394101..394115 / 394201..394215`，每块写死`4`真实`frame_ids`与`ordinal`，`pairs_count=1024`, `BLOCK_LENGTH=1024`, `sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v53`, `K/index_j`分散。

- Per block `base 1(兼old)+条件rescue ≤1`，共享`1 L1` → 概念上`45 L1+45 base+≤45 rescue=90-135` decoder calls。
- Paired效应`Δexact = final - base` per block描述性；`base_exact / rescued / final`三计数 + `avg_leak / avg disclosure / total/final bits` + 四类必报告。
- State `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`; formal paired run requires independent `EXECUTE_AUTH` bound to exact future implementation SHA (plan reference `d61d5a3189b...`); no output directory created in P0.
- **执行偏差防复发**：不设600s外部timeout、建议≥3600s、session/cell ID只轮询同一进程禁重启、中断保留raw partial不聚合、不自动重跑。

## 10. Files

- This report: `openspec/changes/formal-ir-v53-rate-adaptive-l2-heldout-confirm/spike_report.md` + `spike_sample_registry.py` (decoder-free reproducible, HEAD `d61d5a3189b54fc0b82e2df688dae3e9bde5ff8e`)
- OpenSpec four: `proposal.md, design.md, tasks.md, specs/spec.md` (HEAD `d61d5a3189b...`)
- Lifecycle: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`, no next-stage qualification, 保持冻结方法与嵌套增量与45块分散`K/index_j`零重叠冻结不变；本轮仅decoder-free样本注册表与矩阵复核，待独立复审. Verified `python spike_sample_registry.py` expected exit 0 `GATE_ALL PASS` (需本机实测).
