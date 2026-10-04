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

**实测 K2 (`python spike_nested_rescue_stage2.py` 实测 GATE_ALL PASS 2026-08-28 HEAD 8b29dee, 裸运行 `python openspec/changes/formal-ir-v54-two-stage-incremental-l2-rescue/spike_nested_rescue_stage2.py` exit 0)**:
- 1M `H=400`: `all=397`, `K (V53)=224`, `K2 (V54, excl V53) = 135`, `K2_strict (s%4==0)= 34` — `selected2=[22,52,109,155,179,202,230,240,263,287,303,324,347,371,388]` 15 dispersed 零重叠 verified `GATE PASS`
- 1p5M `H=554`: `all=551`, `K=357`, `K2=260`, `K2_strict= 65` — `selected2=[8,73,151,214,247,279,305,337,370,388,419,451,484,516,542]` `GATE PASS`
- 2M `H=729`: `all=726`, `K=552`, `K2=461`, `K2_strict=111` — `selected2=[8,81,136,197,264,304,351,396,442,489,536,583,630,677,717]` `GATE PASS`
> 实测 `K2` 富余 `≥15` (135/260/461)，`selected2` 45块两两 `gap≥4` 与已用 135 区间零重叠已实测 `GATE_ALL PASS` 固化。

**分散选择** `index_j=floor(j*(K2-1)/14)` per source, `j=0..14`, `remaining2` 按 ordinal 排序，保证覆盖 hold 区间的两端与中间，且因 `K2` 大、步长约 `K2/14≈10-27`，相邻 `selected2` gap 自然 `>>3` 满足两两非重叠（`gap≥4`），若出现 `gap<4` 则 `REGISTRY_INVALID`.

**Frozen 45 table V54 (actual, spike 实测 GATE_ALL PASS 固化 2026-08-28)**

| source | block ID (suggested) | held_out_ordinal `[start,end]` (spike actual) | frame_ids[4] (global, spike actual) | pairs |
|---|---|---|---|---|
| 1M (H=400, base1600) | 395001 | [22,25] | [1622,1623,1624,1625] | 1024 |
| 1M | 395002 | [52,55] | [1652,1653,1654,1655] | 1024 |
| 1M | 395003 | [109,112] | [1709,1710,1711,1712] | 1024 |
| 1M | 395004 | [155,158] | [1755,1756,1757,1758] | 1024 |
| 1M | 395005 | [179,182] | [1779,1780,1781,1782] | 1024 |
| 1M | 395006 | [202,205] | [1802,1803,1804,1805] | 1024 |
| 1M | 395007 | [230,233] | [1830,1831,1832,1833] | 1024 |
| 1M | 395008 | [240,243] | [1840,1841,1842,1843] | 1024 |
| 1M | 395009 | [263,266] | [1863,1864,1865,1866] | 1024 |
| 1M | 395010 | [287,290] | [1887,1888,1889,1890] | 1024 |
| 1M | 395011 | [303,306] | [1903,1904,1905,1906] | 1024 |
| 1M | 395012 | [324,327] | [1924,1925,1926,1927] | 1024 |
| 1M | 395013 | [347,350] | [1947,1948,1949,1950] | 1024 |
| 1M | 395014 | [371,374] | [1971,1972,1973,1974] | 1024 |
| 1M | 395015 | [388,391] | [1988,1989,1990,1991] | 1024 |
| 1p5M (H=554, base2213) | 395101 | [8,11] | [2221,2222,2223,2224] | 1024 |
| 1p5M | 395102 | [73,76] | [2286,2287,2288,2289] | 1024 |
| 1p5M | 395103 | [151,154] | [2364,2365,2366,2367] | 1024 |
| 1p5M | 395104 | [214,217] | [2427,2428,2429,2430] | 1024 |
| 1p5M | 395105 | [247,250] | [2460,2461,2462,2463] | 1024 |
| 1p5M | 395106 | [279,282] | [2492,2493,2494,2495] | 1024 |
| 1p5M | 395107 | [305,308] | [2518,2519,2520,2521] | 1024 |
| 1p5M | 395108 | [337,340] | [2550,2551,2552,2553] | 1024 |
| 1p5M | 395109 | [370,373] | [2583,2584,2585,2586] | 1024 |
| 1p5M | 395110 | [388,391] | [2601,2602,2603,2604] | 1024 |
| 1p5M | 395111 | [419,422] | [2632,2633,2634,2635] | 1024 |
| 1p5M | 395112 | [451,454] | [2664,2665,2666,2667] | 1024 |
| 1p5M | 395113 | [484,487] | [2697,2698,2699,2700] | 1024 |
| 1p5M | 395114 | [516,519] | [2729,2730,2731,2732] | 1024 |
| 1p5M | 395115 | [542,545] | [2755,2756,2757,2758] | 1024 |
| 2M (H=729, base2916) | 395201 | [8,11] | [2924,2925,2926,2927] | 1024 |
| 2M | 395202 | [81,84] | [2997,2998,2999,3000] | 1024 |
| 2M | 395203 | [136,139] | [3052,3053,3054,3055] | 1024 |
| 2M | 395204 | [197,200] | [3113,3114,3115,3116] | 1024 |
| 2M | 395205 | [264,267] | [3180,3181,3182,3183] | 1024 |
| 2M | 395206 | [304,307] | [3220,3221,3222,3223] | 1024 |
| 2M | 395207 | [351,354] | [3267,3268,3269,3270] | 1024 |
| 2M | 395208 | [396,399] | [3312,3313,3314,3315] | 1024 |
| 2M | 395209 | [442,445] | [3358,3359,3360,3361] | 1024 |
| 2M | 395210 | [489,492] | [3405,3406,3407,3408] | 1024 |
| 2M | 395211 | [536,539] | [3452,3453,3454,3455] | 1024 |
| 2M | 395212 | [583,586] | [3499,3500,3501,3502] | 1024 |
| 2M | 395213 | [630,633] | [3546,3547,3548,3549] | 1024 |
| 2M | 395214 | [677,680] | [3593,3594,3595,3596] | 1024 |
| 2M | 395215 | [717,720] | [3633,3634,3635,3636] | 1024 |

> **以上为 `python openspec/changes/formal-ir-v54-two-stage-incremental-l2-rescue/spike_nested_rescue_stage2.py` 裸运行 (parents[3]) 实测 `GATE_ALL PASS` 固化值 (K2 135/260/461, K2_strict 34/65/111)，与设计冻结表一致。**

- 每窗口 `4 frames×256=1024 pairs`，`BLOCK_LENGTH=1024`，`sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v54`。
- 新 45 块与 `V48/V50/V51/V52/V53` `frame_ids` 零重叠 per source 可机械校验（`BLOCK_WINDOWS` 比对），且最终 45 间两两非重叠（`gap≥4`），与 `394xxx` (V53) 零重叠。
- `K2≥15` 富余，45块仍为最小确认规模，分散选择保证覆盖整个 hold 区间。

## 6. Joint census and nesting metrics — 实测固化 GATE_ALL PASS (decoder-free, `spike_nested_rescue_stage2.py` 裸运行 parents[3] exit 0)

Using `construct_lane_c_prototype` + `construct_h_inc` (inc1 & inc2) + `compute_gf32_rank`. **三源二阶段联合矩阵实际生成**，零 decoder 调用，预期 gate 全 PASS（需本机执行复现，失败则非零退出）。

### 6.1 Per-source two-stage joint table (实测固化 GATE_ALL PASS 2026-08-28, parents[3] 裸运行 exit 0)

| source | m2 | H_base rank | H_inc1 shape | E_inc1 | H_inc1 row_deg | col_inc1 max | H_joint1 shape | rank_joint1 | rank_inc1 | nested1 | leak_base | leak_stage1 | H_inc2 shape | E_inc2 | col_inc2 max | H_total shape | rank_total | rank_inc2 | rank_total_inc | nested_total | leak_stage2 | +40/+80 | gate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1M | 184 | 184 | 8×1024 | 96 | 12/12/≤16 | 1 | 192×1024 | 192 | 8 | True | 1064 | 1104 | 8×1024 | 96 | 1 | 200×1024 | 200 | 8 | 16 | True | 1144 | 40/80 | PASS |
| 1p5M | 190 | 190 | 8×1024 | 96 | 12/12/≤16 | 1 | 198×1024 | 198 | 8 | True | 1094 | 1134 | 8×1024 | 96 | 1 | 206×1024 | 206 | 8 | 16 | True | 1174 | 40/80 | PASS |
| 2M | 192 | 192 | 8×1024 | 96 | 12/12/≤16 | 1 | 200×1024 | 200 | 8 | True | 1104 | 1144 | 8×1024 | 96 | 1 | 208×1024 | 208 | 8 | 16 | True | 1184 | 40/80 | PASS |

- `rank_base==m2`, `rank_joint1==m2+8`, `rank_total==m2+16`, `nested1==True`, `nested_total_base==True`, `nested_total_joint1==True`, `rank_inc1==8`, `rank_inc2==8`, `row≤16`, `col_inc1≤1`, `col_inc2≤1`, `joint_zero_col==0`, `total_zero_col==0`, `+40/+80` formula hold.
- `E_inc1` and `E_inc2` each exact `96` in this construction; `total row_deg max 12` (min 10-12, mean 10.77-11.20), `col_deg_total max 4 mean 2.19 zero_col 0`.
- `tag_import_ok` via `compute_tag_64(empty, zeros)` true, example `f5a5fd42d16a2030`.
- **Spike 复现命令与实测结果 (parents[3] 裸运行, HEAD 8b29dee, exit 0 GATE_ALL PASS)**:
```bash
python openspec/changes/formal-ir-v54-two-stage-incremental-l2-rescue/spike_nested_rescue_stage2.py  # 裸运行，无需 PYTHONPATH, parents[3] 固化
# 实测输出 (已固化):
# 1M: H_base 184×1024 rank 184, H_inc1 8×1024 E96 row_deg [12]*8, H_joint1 192×1024 rank 192 nested True rank_inc1 8 leak 1064→1104
#      H_inc2 8×1024 E96 row_deg [12]*8, H_total 200×1024 rank 200 nested_total True rank_inc2 8 rank_total_inc 16 leak_stage2 1144 gate PASS total row max 12 col max 4 zero 0
# 1p5M: H_base 190 rank 190, H_joint1 198 rank 198, H_total 206 rank 206 nested True 1094→1134→1174 PASS total row max 12
# 2M: H_base 192 rank 192, H_joint1 200 rank 200, H_total 208 rank 208 nested True 1104→1144→1184 PASS total row max 12
# 1M K2=135 K2_strict=34, 1p5M K2=260 K2_strict=65, 2M K2=461 K2_strict=111 — selected2 45块零重叠（gap≥4）与已用135区间零重叠 per source verified (V53 K 224/357/552)
# GATE_ALL: ALL PASS (two-stage matrices nested m2+8+8 + registry 45 zero-overlap V54 + budget + leakage) — exit 0
# gate 失败时脚本非零退出 (sys.exit(1))，不产生 Constructible: YES
```
实测 `rank_total==m2+16`（200/206/208）`nested_total==True` `rank_inc2==8` `row≤16` `col_inc2≤1` `E_inc2=96` `leak +40+40` 已 spike 退出码 `0` 固化；脚本零 decoder 调用、write-free；失败时 `sys.exit(1)` 并返回 `NESTED_NOT_CONSTRUCTIBLE` 或 `REGISTRY_INVALID`。裸运行已验证 `parents[3]` 路径，无需临时 PYTHONPATH。

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

## 8. Spike verdict — 实测 PASS (`python spike_nested_rescue_stage2.py` 裸运行 parents[3] exit 0 GATE_ALL PASS 已固化 2026-08-28)

- **Constructible (V54 two-stage Δ8+8)**: **实测 YES (GATE_ALL PASS)** — 三源 `H_joint1` `192/198/200`（`m2+8`）满秩嵌套 + `H_total` `200/206/208`（`m2+16`）满秩、二阶段嵌套、`rank_increment_2==8`、泄漏 `+40/+80`（1064→1104→1144 等）、`row≤16` `col_inc1≤1` `col_inc2≤1` `E_inc=96+96` 已实测 `GATE PASS` (1M rank 192→200, 1p5M 198→206, 2M 200→208, E_inc1=96 E_inc2=96 row max 12 tag f5a5fd42d16a2030)。
- **Registry (45 fresh V54)**: **实测 YES (GATE_ALL PASS)** — 实测 `K2=135/260/461`（`K2_strict=34/65/111`）富余，分散选 15/源 `index_j=floor(j*(K2-1)/14)` 零重叠且最终 45 两两 `gap≥4`、与已用 135 区间零重叠 per source verified (V53 K 224/357/552, V54 K2 135/260/461)，`pairs_count=1024`, `sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v54`, `block IDs 395xxx` 建议且真实以 `frame_ids` 为准，`GATE_ALL PASS` 已固化。
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
- Lifecycle: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`, no next-stage qualification, 保持冻结首遍与首增量与二阶段嵌套与 45 块分散 `K2/index_j` 零重叠冻结不变；本轮仅 decoder-free 二阶段 spike 与样本注册表，已按冻结内容完成六文件。Verified `python spike_nested_rescue_stage2.py` **实测** `GATE_ALL PASS` (裸运行 parents[3] exit 0, 三源 `rank_total 200/206/208 nested True rank_inc2 8 E_inc2 96`, `K2 135/260/461 K2_strict 34/65/111`, 45块零重叠 frame windows 见 §5 冻结表)。
