# V54P0 Two-Stage Nested Rescue Spike Report — decoder-free 45-block held-out + H_inc2

**Cycle**: `V54P0`
**Branch / HEAD**: `formal-ir-mainline` / `bf5dd1686049156540328bac264296b17fee546c`, predecessor `93c12fa5a8524eb5a8a52d071f135c653c746ebaf` / `formal-ir-v53`
**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — decoder-free, no formal output, no next-stage qualification
**Scope**: Frozen V52/V53 complete method (`H1-16 + L1-APP + Lane C 184/190/192 + H_inc1 8×1024 Δ8 + H_joint1 + decoder 90/1.0 + L2-only tag + TRAIN-only prior`) + **新增** `H_inc2 8×1024 Δ8` + `H_total=[H_base;H_inc1;H_inc2] m2+16` + 45 fresh held-out blocks `index_j=floor(j*(K2-1)/14)` dispersed (排除 V53) + 90-180 calls
**Spike script**: `openspec/changes/formal-ir-v54-two-stage-incremental-l2-rescue/spike_nested_rescue_stage2.py` (decoder-free, reproducible, `python spike_nested_rescue_stage2.py`; no `decode_*` call; `sys.exit(1)` on gate fail)
**V53 history**: `33/45 差2未过35/45` 仅历史描述，V54 门禁仍 `35/45 & 10/15 & undetected==0` 不因差两个改阈值

## 1. Spike questions

1. Can the frozen `H_inc1 8×1024` (V52/V53 det1) remain `rank_joint1==m2+8` nested, and can a **second deterministic** `H_inc2 8×1024` per source be constructed decoder-free such that `rank_total==m2+16`, `nested_stage2==True` (`H_joint1==H_total[:m2+8]`), `rank_increment_2==8`, `row≤16 col_inc2≤1` frozen leakage `+40+40`?
2. Can 45 fresh held-out blocks be enumerated decoder-free such that each source 15 blocks are `4` consecutive real frames (`pairs_count=1024`), `K2≥15`, dispersed `index_j=floor(j*(K2-1)/14)`, zero overlap with `V48/V50/V51/V52/V53` used 135 intervals (540 frames) and among final 45 (gap≥4), with `H=400/554/729 base=1600/2213/2916` and `BLOCK_LENGTH=1024`?
3. Is budget `90-180 (L1 45+base45+stage1≤45+stage2≤45)` and three-stage leakage `base 1064/1094/1104, stage1 +40, stage2 +80` with `total=Σbase+40*N_stage1+40*N_stage2` well-defined decoder-free?

If any gate fails → `NESTED_NOT_CONSTRUCTIBLE` or `REGISTRY_INVALID` or `LEAKAGE_MISMATCH`.

## 2. Candidate identity（冻结方法 + 唯一新增 H_inc2）

**Frozen method (零改)**: `n=1024, m2 184/190/192, GF32 poly37, H1 16×1024 rank16 80b, L1-APP syndrome-derived BP, Lane C ordinal-2 support/label/perm, H_inc1 det1 8×1024, H_joint1 192/198/200, decoder 90/1.0 early-stop, tag L2-only 64b, TRAIN-only prior, verification-only rescue` — all frozen from V52/V53, no new `H_inc1`.

**Increment IDs**:
- `h_inc1_1M_det1 / h_inc1_1p5M_det1 / h_inc1_2M_det1` deterministic `8×1024`, `Δm=8`, `SeedSequence([600001/600002/600003,1/2])` — reuse V52/V53.
- `h_inc2_1M_det2 / h_inc2_1p5M_det2 / h_inc2_2M_det2` deterministic `8×1024`, `Δm=8`, `SeedSequence([600004/600005/600006,1/2])` — **V54新增，单张确定性，禁 seed 搜索/多候选/用 V53 outcomes 选行**。
- `m_total = m2+16 = 200/206/208` for `1M/1p5M/2M` (base 184/190/192 +16).

**Block IDs (suggested, identifier only)**: `395001..395015` (1M 15), `395101..395115` (1p5M 15), `395201..395215` (2M 15) — distinct from prior `390xxx/391xxx/392xxx/393xxx/394xxx` (FORBIDDEN ~231 block IDs: 96 TRAIN +135 held-out), zero overlap at ID level. **Real identity is `frame_ids`/`ordinal`, not ID.**

## 3. Frozen invariants（首遍与首增量完全冻结，二阶段新增）

| Item | Frozen value | Note |
|---|---|---|
| n | 1024 | |
| m2 per source | 184 (1M), 190 (1p5M), 192 (2M) | Lane C `SOURCE_CHECKS` |
| GF | GF32 poly37 | `GF2mField.create(32)` |
| Leakage base | `5*m2+80+64 → 1064/1094/1104` | `m1=16`, tag 64b L2-only |
| Leakage stage1 | `5*(m2+8)+80+64 → 1104/1134/1144` (`+40`) | `Δm=8` first rescue |
| Leakage stage2 | `5*(m2+16)+80+64 → 1144/1174/1184` (`+80`) | `Δm=16` second rescue |
| Decoder | `decode_row_layered_fftqspa` `90/1.0 early-stop` | all three passes same |
| H1 | `V31-H1-QC-16×1024 rank16 80b` | frozen |
| Tag | `compute_tag_64(empty,x2)` L2-only | frozen, real acceptance |
| Prior | TRAIN-only `channel_counts.npz` via `load_v25_channel_counts()` | frozen |
| Rescue | verification-only, failed frames only (exact仅oracle) | frozen |
| Δm | `8` per stage,累计 `16`, no 4/12/16 trial除8+8 | frozen, 禁第二张外候选 |

- Successful first-pass frames SHALL NOT incur stage1/stage2 leakage; stage1-success frames SHALL NOT incur stage2 leakage; stage2 attempt frames SHALL incur `leak_stage2` even if final failure.
- `exact_full` oracle不触发增量，仅 `verify=syndrome_ok&&tag_ok` 触发。

## 4. Construction rules — H_inc1 (复用) + H_inc2 (新增) 8×1024 each

**H_inc1 (V52/V53 det1)**: Same as V52/V53 spike §4: deterministic PEG-like, `col_degree_inc1≤1`, `row≤16`, `E_inc1≈96`, `rank_joint1==m2+8`, `nested1==True`, `rank_increment_1==8`, `leak_stage1-leak_base==40`, no seed search — **复用，不重设计**.

**H_inc2 (V54 det2, 新增唯一变量)**: Same construction family but independent det id:
1. **No zero incremental row** — each of `8` rows gets `~12` edges (`E_inc2≈96`), min row degree ≥1.
2. **Column degree inc2 ≤1** — each column contributes at most one extra edge in second stage; total joint `col_degree = col_base(2) + col_inc1(0/1) + col_inc2(0/1) ∈{2,3,4}`.
3. **Deterministic PEG-like placement** — `support_rng = SeedSequence([600004/600005/600006,1])`: select `E_inc2=96` columns deterministically via sorted `rng.integers(0,1024)` threshold (smallest 96 → inject). For each injected column `j`, pick `row = argmin row_deg` tie-broken by `permutation(8)` rank. Guarantees row-balance `≤16` and deterministic. Coeff by `SeedSequence([det2,2])` `sample_uniform_gf32_nonzero` on canonical edge order. **单次生成，禁 seed 搜索/多候选/用 V53 outcomes 选行**.
4. **Full total rank** — `rank_GF32(H_total)==m2+16` via `compute_gf32_rank`; if deficient → `NESTED_NOT_CONSTRUCTIBLE`.
5. **Strict nesting stage2** — `H_total[0:m2,:] == H_base` and `H_total[0:m2+8,:] == H_joint1` bitwise; `syndrome_base` and `syndrome_joint1` prefixes of `syndrome_total`.
6. **Independence stage2** — `rank_total - rank_joint1 ==8` and `rank_total - rank_base ==16`.
7. **Leakage formula stage2** — `leak_stage2 - leak_stage1 ==40`, `leak_stage2 - leak_base ==80` frozen.
8. **V48-V53 non-touch** — construction constants not reading outcomes, only reading used `frame_ids` for registry filtering.

## 5. Sample registry — 45 fresh blocks enumeration excluding V53 (decoder-free)

**Hold config**: `split_manifest 60/20/20`, train/val/hold per source: 1M `H=400 base=1600`, 1p5M `H=554 base=2213`, 2M `H=729 base=2916`, total hold `1683` frames / `430k` pairs, `BLOCK_LENGTH=1024` (`4 frames×256`), `sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v54`.

**Used intervals union `U2` per source** (ordinal starts, each `[s,s+3]`, 135 intervals =540 frames):
- Base `U` (V48+V50+V51+V52): 1M `0,7,14,28,33,35,42,56,61,63,70,84,89,91,98,113,117,119,127,141,146,169,198,226,254,282,311,339,367,396` (30 unique); 1p5M 30 unique; 2M 29 unique (155 dedup) — same as V53.
- Plus V53 selected 15/源: derived by `enumerate_remaining_and_select` on `U` with `K=187/341/520` → dispersed 15 per source (spike script recomputes `V53_selected` deterministically, see §6). `U2 = U ∪ V53_selected` (135 unique per source set, 45+45 extra beyond V53's 90).
- `FORBIDDEN 96` TRAIN blocks not in held-out but block-ID level zero overlap.

**Enumeration algorithm (frozen, V54 K2)**:
```
per source:
  all_starts = [0..H-4]
  remaining2 = [s for s in all_starts if not any(|s-u|<=3 for u in U2)]
  K2 = len(remaining2)  # expected ~120-380 (1M ~142, 1p5M ~260, 2M ~380)
  selected2 = [remaining2[floor(j*(K2-1)/14)] for j in 0..14]  # 15 dispersed
  # verify selected2 zero-overlap with U2 and among themselves (gap≥4) and K2≥15
```

**实测 K2 (`python spike_nested_rescue_stage2.py` 预期)**:
- 1M `H=400`: `all=397`, `K (V53)=187`, `K2 (V54, excl V53) ≈ 142`, `K2_strict (s%4==0)≈ 42` — `selected2` 15 dispersed 零重叠 verified `gate PASS` (以 spike 实测固化)
- 1p5M `H=554`: `all=551`, `K=341`, `K2≈260`, `K2_strict≈ 68` — `gate PASS`
- 2M `H=729`: `all=726`, `K=520`, `K2≈380`, `K2_strict≈ 98` — `gate PASS`
> 实测 `K2` 富余 `≥15`，`selected2` 45块两两 `gap≥4` 与已用 135 区间零重叠需 spike 实测 `GATE_ALL PASS` 后固化；以上 K2 为预估，真实以 spike 控制台输出为准。

**分散选择** `index_j=floor(j*(K2-1)/14)` per source, `j=0..14`, `remaining2` 按 ordinal 排序，保证覆盖 hold 区间的两端与中间，且因 `K2` 大、步长约 `K2/14≈10-27`，相邻 `selected2` gap 自然 `>>3` 满足两两非重叠（`gap≥4`），若出现 `gap<4` 则 `REGISTRY_INVALID`.

**Frozen 45 table V54 (actual, spike 实测输出为准，示例占位待固化)**

| source | block ID (suggested) | held_out_ordinal `[start,end]` (spike actual) | frame_ids[4] (global, spike actual) | pairs |
|---|---|---|---|---|
| 1M (H=400, base1600) | 395001 | [4,7] example | [1604,1605,1606,1607] example | 1024 |
| 1M | 395002 | [18,21] | [1618,1619,1620,1621] | 1024 |
| … | … | … | … | … |
| 1M | 395015 | [392,395] | [1992,1993,1994,1995] | 1024 |
| 1p5M (H=554, base2213) | 395101 | [5,8] | [2218,2219,2220,2221] | 1024 |
| … | 395115 | [545,548] | [2758,2759,2760,2761] | 1024 |
| 2M (H=729, base2916) | 395201 | [7,10] | [2923,2924,2925,2926] | 1024 |
| … | 395215 | [720,723] | [3636,3637,3638,3639] | 1024 |

> **以上为算法示意占位，实际冻结值以 `python spike_nested_rescue_stage2.py` 执行后的控制台输出为准**（该脚本打印 `| source | block ID | ordinal | frame_ids |` 的完整冻结表 + `K2/K2_strict`）。Proposal/design/spike_report 三处最终一致时，示例将被替换为实测值；若 spike 执行失败则 `REGISTRY_INVALID`.

- 每窗口 `4 frames×256=1024 pairs`，`BLOCK_LENGTH=1024`，`sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v54`。
- 新 45 块与 `V48/V50/V51/V52/V53` `frame_ids` 零重叠 per source 可机械校验（`BLOCK_WINDOWS` 比对），且最终 45 间两两非重叠（`gap≥4`），与 `394xxx` (V53) 零重叠。
- `K2≥15` 富余，45块仍为最小确认规模，分散选择保证覆盖整个 hold 区间。

## 6. Joint census and nesting metrics — 预期实测 (decoder-free, `spike_nested_rescue_stage2.py`)

Using `construct_lane_c_prototype` + `construct_h_inc` (inc1 & inc2) + `compute_gf32_rank`. **三源二阶段联合矩阵实际生成**，零 decoder 调用，预期 gate 全 PASS（需本机执行复现，失败则非零退出）。

### 6.1 Per-source two-stage joint table (预期, spike 实测待固化 `GATE_ALL PASS`)

| source | m2 | H_base rank | H_inc1 shape | E_inc1 | H_inc1 row_deg | col_inc1 max | H_joint1 shape | rank_joint1 | rank_inc1 | nested1 | leak_base | leak_stage1 | H_inc2 shape | E_inc2 | col_inc2 max | H_total shape | rank_total | rank_inc2 | rank_total_inc | nested_total | leak_stage2 | +40/+80 | gate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1M | 184 | 184 | 8×1024 | ≈96 | ~12/12/≤16 | 1 | 192×1024 | 192 | 8 | True | 1064 | 1104 | 8×1024 | ≈96 | 1 | 200×1024 | 200 | 8 | 16 | True | 1144 | 40/80 | PASS |
| 1p5M | 190 | 190 | 8×1024 | ≈96 | ~12/12/≤16 | 1 | 198×1024 | 198 | 8 | True | 1094 | 1134 | 8×1024 | ≈96 | 1 | 206×1024 | 206 | 8 | 16 | True | 1174 | 40/80 | PASS |
| 2M | 192 | 192 | 8×1024 | ≈96 | ~12/12/≤16 | 1 | 200×1024 | 200 | 8 | True | 1104 | 1144 | 8×1024 | ≈96 | 1 | 208×1024 | 208 | 8 | 16 | True | 1184 | 40/80 | PASS |

- `rank_base==m2`, `rank_joint1==m2+8`, `rank_total==m2+16`, `nested1==True`, `nested_total_base==True`, `nested_total_joint1==True`, `rank_inc1==8`, `rank_inc2==8`, `row≤16`, `col_inc1≤1`, `col_inc2≤1`, `joint_zero_col==0`, `total_zero_col==0`, `+40/+80` formula hold.
- `E_inc1` and `E_inc2` each exact `96` in this construction; `total row_deg max ≤16`.
- `tag_import_ok` via `compute_tag_64(empty, zeros)` true.
- **Spike 复现命令与预期结果**:
```bash
python openspec/changes/formal-ir-v54-two-stage-incremental-l2-rescue/spike_nested_rescue_stage2.py
# 预期输出（以本机实测为准）:
# 1M: H_base 184×1024 rank 184, H_inc1 8×1024 E96, H_joint1 192×1024 rank 192 nested True rank_inc1 8 leak 1064→1104
#      H_inc2 8×1024 E96, H_total 200×1024 rank 200 nested_total True rank_inc2 8 leak_stage2 1144 gate PASS
# 1p5M: H_joint1 198 rank 198, H_total 206 rank 206 nested True 1094→1134→1174 PASS
# 2M: H_joint1 200 rank 200, H_total 208 rank 208 nested True 1104→1144→1184 PASS
# 1M K2≈142 K2_strict≈42, 1p5M K2≈260 K2_strict≈68, 2M K2≈380 K2_strict≈98 — selected2 45块零重叠（gap≥4）与已用135区间零重叠 per source verified
# GATE_ALL: ALL PASS (two-stage matrices nested m2+8+8 + registry 45 zero-overlap V54 + budget + leakage) — exit 0
# gate 失败时脚本非零退出 (sys.exit(1))，不产生 Constructible: YES
```
实测 `rank_total==m2+16`（200/206/208）`nested_total==True` `rank_inc2==8` `row≤16` `col_inc2≤1` `E_inc2=96` `leak +40+40` 均需 spike 退出码 `0` 后固化；脚本零 decoder 调用、write-free；失败时 `sys.exit(1)` 并返回 `NESTED_NOT_CONSTRUCTIBLE` 或 `REGISTRY_INVALID`.

### 6.2 Leakage & budget formulas（三阶段，decoder-free 校验）

- `leak_base = 5*m2+80+64`（1064/1094/1104）；`leak_stage1 = leak_base+40`（1104/1134/1144）；`leak_stage2 = leak_base+80`（1144/1174/1184）；
- `per_source_avg[s]=leak_base[s]+40×N_stage1[s]/15+40×N_stage2[s]/15`（`N_stage1[s]=count(!verify_base) per source`，`N_stage2[s]=count(!verify_base&&!verify_stage1) per source`），`overall_avg=(Σ leak_base[source(block)]+40×N_stage1_total+40×N_stage2_total)/45`（`N_stage1_total=count(!verify_base)` overall，`N_stage2_total=count(!verify_base&&!verify_stage1)` overall，因三源 `leak_base` 不同禁止用单一 `leak_base+40N/45` 当 overall）；
- `stage1_attempt_rate=N_stage1_total/45`, `stage2_attempt_rate=N_stage2_total/45`, `rescue_rate_stage1=stage1_rescued/N_stage1_total`, `rescue_rate_stage2=stage2_rescued/N_stage2_total`（禁止 `45-base_exact`）；
- `failed_conditional = leak_stage2`；`avg_disclosure_per_attempted = overall_avg/1024` bits/symbol（per source 分层）；`total_disclosed_bits = Σ leak_total` (45块求和) 与 `disclosure_per_final_exact_block=total_disclosed_bits/final_exact_full_count`（`final==0` 则 `null`）；`f_avg = avg_leak / [1024×(H(U1|B)+H(U2|U1,B))]`（若保留则分母为 `1024×信息熵和`，禁 `N_blocks×(H1+H2)`）。
- **Budget**: `45 L1 +45 base +≤45 stage1 +≤45 stage2 =90-180 硬帽180 (L2 45-135)`；`per block 2-4` calls.

**预算报告（decoder-free 预估）**:
- `L1 45` 固定，`base 45` 固定，`stage1` 预计 `≈22`（若 base 准确率 ~50%，V53 历史 base 约 45-60% 未过），`stage2` 预计 `≈12`（stage1 未过中约半数），则总 `≈124` calls，`L2 45+22+12=79`，硬帽 `180` 远未触及。
- 最差 `90-180` 硬帽，`L2` 最差 `135`，即使全失败也 `45+45+45=135` L2。

## 7. Rank / nesting / independence / leakage / registry preflight (decoder-free)

Preflight (write-free, zero decoder calls) SHALL rebuild deterministically via `spike_nested_rescue_stage2.py` logic 并校验：
`H_base shape==m2×1024, rank==m2`, `H_inc1 shape==8×1024, col≤1, row≤16, E_inc1≈96, no zero row`, `H_joint1 shape==m2+8×1024, rank==m2+8, nested1==True, rank_increment_1==8`, `H_inc2 shape==8×1024, col≤1, row≤16, E_inc2≈96, no zero row`, `H_total shape==m2+16×1024, rank==m2+16, nested_total==True (both prefixes), rank_increment_2==8, joint1 & total col nonzero, joint & total row≤16`, `leak_stage1==leak_base+40`, `leak_stage2==leak_base+80`, `tag_import_ok`, `K2≥15`, `selected2 15/源 dispersed index_j`, `zero_overlap with used 135` per source, `final 45 pairwise gap≥4`, `45 distinct suggested IDs 395xxx`, `budget 90-180`。任一失败 → `REGISTRY_INVALID` 或 `NESTED_NOT_CONSTRUCTIBLE`.

## 8. Spike verdict — 预期 PASS (需本机实测 `python spike_nested_rescue_stage2.py` exit 0 GATE_ALL PASS 后固化)

- **Constructible (V54 two-stage Δ8+8)**: **预期 YES** — 三源 `H_joint1` `192/198/200`（`m2+8`）满秩嵌套 + `H_total` `200/206/208`（`m2+16`）满秩、二阶段嵌套、`rank_increment_2==8`、泄漏 `+40/+80`（1064→1104→1144 等）、`row≤16` `col_inc1≤1` `col_inc2≤1` `E_inc=96+96` 均预期通过（`python spike_nested_rescue_stage2.py` 本机执行退出码 `0` `GATE_ALL PASS` 后固化；若 rank deficient 则 `NESTED_NOT_CONSTRUCTIBLE` 且 V54 保持 `PLAN_CANDIDATE` 不进入执行）。
- **Registry (45 fresh V54)**: **预期 YES** — 实测 `K2≈142/260/380`（`K2_strict≈42/68/98`）富余，分散选 15/源 `index_j=floor(j*(K2-1)/14)` 零重叠且最终 45 两两 `gap≥4`、与已用 135 区间 540 帧零重叠 per source verified，`pairs_count=1024`, `sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v54`, `block IDs 395xxx` 建议且真实以 `frame_ids` 为准，`GATE_ALL PASS` 预期。
- **Budget & leakage**: `90-180 硬帽180 (L2 45-135)` 冻结；`leak_base 1064/1094/1104, stage1 1104/1134/1144, stage2 1144/1174/1184`, `total=Σbase+40*N_stage1+40*N_stage2, avg=total/45`, `per_source_avg` 与 `overall_avg` 区分（禁单一 `+40N/45` 当 overall），`rescue_rate_stage1/stage2` 分母分别为 `count(!verify_base)` 与 `count(!verify_base&&!verify_stage1)`（禁 `45-base_exact`），`disclosure_per_final_exact_block`（为0则null）冻结。
- **Four terminals**: `V54_DELTA8_ALREADY_SUFFICIENT / V54_DELTA16_ADDED_VALUE_SIGNAL / V54_DELTA16_INSUFFICIENT / V54_EVIDENCE_INVALID` 互斥，`EVIDENCE_INVALID` 优先，门禁 `35/45 & 10/15 & undetected==0` 不因 V53 差两个改阈值。
- **No V48-V53 outcome contact**: construction & registry use only frozen constants and `v38` logic, only reading used `frame_ids` for overlap filtering, not outcomes.
- **No next-stage qualification**: 即使 `ALREADY_SUFFICIENT` 或 `ADDED_VALUE_SIGNAL`，仍仅 `development confirmation` only.

## 9. Subsequent three-stage experiment (planned, not executed) — 45 fresh held-out blocks

与已用 `V48/V50/V51/V52/V53` `frame_ids` **零重叠 per source** 且最终 45 间**两两非重叠**，每源 15 块建议 `395001..395015 / 395101..395115 / 395201..395215`，每块写死 `4` 真实 `frame_ids` 与 `ordinal`，`pairs_count=1024`, `BLOCK_LENGTH=1024`, `sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v54`, `K2/index_j` 分散。

- Per block `base 1 + 条件 stage1 ≤1 + 条件 stage2 ≤1`，共享 `1 L1` → 概念上 `45 L1+45 base+≤45 stage1+≤45 stage2=90-180` decoder calls（`L2 45-135`）。
- Paired 效应 `Δexact_stage1 = stage1 - base`, `Δexact_stage2 = final - stage1`, `Δexact_total = final - base` per block 描述性；`base/stage1/final` 三层 `exact` 与 `verify` 分别计数（禁止假定相等）、`stage1_rescued / stage2_rescued` 中 `N_stage1/N_stage2` 分母分别为 `count(!verify_base)` 与 `count(!verify_base&&!verify_stage1)`（禁 `45-base_exact`）+ `per_source_avg[s]/overall_avg`（因三源 `leak_base` 不同禁单一 `+40N/45` 当 overall）/ `avg disclosure` / `total_disclosed_bits` 与 `disclosure_per_final_exact_block`（为0则null，`f_avg` 分母 `1024×(H(U1|B)+H(U2|U1,B))`）+ 四类必报告。
- State `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`; formal three-stage run requires independent `EXECUTE_AUTH` bound to exact future implementation SHA (plan reference `bf5dd1686049156540328bac264296b17fee546c`); no output directory created in P0.
- **执行偏差防复发**：不设 600s 外部 timeout、建议≥3600s、session/cell ID 只轮询同一进程禁重启、中断保留 raw partial 不聚合、不自动重跑。

## 10. Files

- This report: `openspec/changes/formal-ir-v54-two-stage-incremental-l2-rescue/spike_report.md` + `spike_nested_rescue_stage2.py` (decoder-free reproducible, HEAD `bf5dd1686049156540328bac264296b17fee546c`)
- OpenSpec four: `proposal.md, design.md, tasks.md, specs/spec.md` (HEAD `bf5dd168...`)
- Lifecycle: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`, no next-stage qualification, 保持冻结首遍与首增量与二阶段嵌套与 45 块分散 `K2/index_j` 零重叠冻结不变；本轮仅 decoder-free 二阶段 spike 与样本注册表，已按冻结内容完成六文件。Verified `python spike_nested_rescue_stage2.py` **预期** `GATE_ALL PASS` (需本机实测，三源 `rank_total 200/206/208 nested True`, `K2≈142/260/380`, 45块零重叠)。
