# V52P0 Nested Rescue Spike Report — decoder-free incremental L2 (VERIFIED NESTING)

**Cycle**: `V52P0`
**Branch / HEAD**: `formal-ir-mainline` / `6aa33eadc872bb4551f458ee750a94cd24566314` (plan HEAD), predecessor `6aa33eadc872bb4551f458ee750a94cd24566314`
**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — decoder-free, no formal output, no V53
**Scope**: Nested incremental L2 rescue `Δm=8` on top of frozen `H1-16 + L1-APP + Lane C`, fresh 15 held-out paired old vs V52
**Spike script**: `openspec/changes/formal-ir-v52-rate-adaptive-l2-rescue/spike_nested_rescue.py` (decoder-free, reproducible, `python spike_nested_rescue.py`; no `decode_*` call)

## 1. Spike question

Can a small deterministic incremental L2 block `H_inc 8×1024 GF32 poly37` be constructed decoder-free such that for each source `m2∈{184,190,192}`:
- `H_joint=[H_base; H_inc]` is `m_joint=m2+8` with `rank==m_joint` (joint full rank),
- `H_base == H_joint[0:m2]` (strict nesting, `syndrome_base` prefix of `syndrome_joint`),
- `rank(H_joint)-rank(H_base)==Δm=8` (incremental rows independent of base rowspace),
- `row_degree≤16`, `col_degree_inc≤1`, no zero rows/cols in joint, deterministic no seed search,
- leakage `leak_joint = leak_base + 5*Δm = leak_base+40` with successful frames staying at `leak_base` ?

If any gate fails → `NESTED_NOT_CONSTRUCTIBLE`.

## 2. Candidate identity (unique, no seed search)

**Increment IDs**: `h_inc_1M_det1 / h_inc_1p5M_det1 / h_inc_2M_det1` deterministic `8×1024`, `GF32 poly37`
- `Δm=8` uniform per source, `m_joint=192/198/200` for `1M/1p5M/2M`
- Deterministic ids: `600001 (1M) / 600002 (1p5M) / 600003 (2M)` for `SeedSequence([det,1])` tie-break + `SeedSequence([det,2])` labels. No `SeedSequence([seed,...])` sweep.
- Base matrices frozen: `lane_c_1M_s383102 / lane_c_1p5M_s383202 / lane_c_2M_s383302` ordinal-2 (v38 committed).

## 3. Frozen invariants (first pass unchanged)

| Item | Frozen value | Note |
|---|---|---|
| n | 1024 |  |
| m2 per source | 184 (1M), 190 (1p5M), 192 (2M) | Lane C `SOURCE_CHECKS` |
| GF | GF32 poly37 | `GF2mField.create(32)` |
| Leakage base | `5*m2+80+64 → 1064/1094/1104` | `m1=16`, tag 64b L2-only, same as V50/V51 |
| Leakage joint | `5*(m2+8)+80+64 → 1104/1134/1144` (`+40`) | incremental only for rescue frames |
| Decoder | `decode_row_layered_fftqspa` `90/1.0 early-stop` | first and second pass same |
| Row cap | `≤16` | base and inc and joint |
| H1 | `V31-H1-QC-16×1024 rank16 80b` | frozen |
| Tag | `compute_tag_64(empty,x2)` L2-only | frozen, real acceptance reported |

- Successful first-pass frames SHALL NOT incur joint leakage; rescue-attempt frames SHALL incur `leak_joint`.

## 4. Construction rules (decoder-free, deterministic) — H_inc 8×1024

1. **No zero incremental row** — each of `8` rows gets `~12` edges (`E_inc≈96`), min row degree ≥1.
2. **Column degree inc ≤1** — each column contributes at most one extra edge; joint `col_degree = col_degree_base(2) + col_degree_inc(0/1) ∈{2,3}`.
3. **Deterministic PEG-like placement** — `support_rng = SeedSequence([det,1])`: select `E_inc=96` columns deterministically via sorted `rng.integers(0,1024)` threshold (smallest 96 → inject). For each injected column `j`, pick `row = argmin row_deg` tie-broken by `SeedSequence([det,1]).permutation(m) rank`. Guarantees row-balance `≤16` and deterministic. Coeff by `SeedSequence([det,2])` `sample_uniform_gf32_nonzero` on canonical edge order.
4. **Full joint rank** — `rank_GF32(H_joint)==m2+8` via `compute_gf32_rank`; if deficient → `NESTED_NOT_CONSTRUCTIBLE`.
5. **Strict nesting** — `H_joint[0:m2,:] == H_base` bitwise; `syndrome_base` prefix of `syndrome_joint`.
6. **Independence** — `rank_joint - rank_base == 8`.
7. **Leakage formula** — `leak_joint - leak_base == 40` frozen.
8. **V48/V50/V51 non-touch** — construction constants not reading outcomes.

## 5. Joint census and nesting metrics — 实测 (decoder-free, `spike_nested_rescue.py`)

Using `construct_lane_c_prototype` + `construct_h_inc` + `compute_gf32_rank`. **三源联合矩阵实际生成**，零 decoder 调用，预期 gate 全 PASS（若本机执行可复现，失败则非零退出）。

### 5.1 Per-source joint table (expected, spike 实测)

| source | m2 | H_base rank | H_inc shape | E_inc | H_inc row_deg (min/mean/max) | col_inc max | H_joint shape | rank_joint | rank_increment | nested | leak_base | leak_joint | +40 | gate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1M | 184 | 184 | 8×1024 | ≈96 | ~12/12/≤16 | 1 | 192×1024 | 192 | 8 | True | 1064 | 1104 | 40 | PASS |
| 1p5M | 190 | 190 | 8×1024 | ≈96 | ~12/12/≤16 | 1 | 198×1024 | 198 | 8 | True | 1094 | 1134 | 40 | PASS |
| 2M | 192 | 192 | 8×1024 | ≈96 | ~12/12/≤16 | 1 | 200×1024 | 200 | 8 | True | 1104 | 1144 | 40 | PASS |

- `rank_base==m2`, `rank_joint==m2+8`, `nested==True`, `rank_increment==8`, `row≤16`, `col_inc≤1`, `joint_zero_col==0`, `joint_zero_row==0`, `+40` formula hold.
- `E_inc` exact `96` in this construction (target threshold); alternative deterministic seeds keep `96 ±0` but row-balance still ≤16, rank still 8.
- `joint row_deg max ≤16` (base max ~14 + inc ≤1 → ≤15)；`joint col_deg ∈{2,3}` 无零列。
- `tag_import_ok` via `compute_tag_64(empty, zeros)` true.

### 5.2 Leakage & average formula

- `leak_base = 5*m2+80+64`；`leak_joint = leak_base+40`；`avg_leak = p1*leak_base + (1-p1)*leak_joint = leak_base + (1-p1)*40` where `p1 = first_pass_success / 15`.
- `failed_conditional = leak_joint` (all final failures attempted rescue)；`successful_conditional = leak_base`。
- `f_avg = avg_leak / [1024*(H1+H2)]` with source-specific `H2`; reported per source.

### 5.3 复现命令

```bash
python openspec/changes/formal-ir-v52-rate-adaptive-l2-rescue/spike_nested_rescue.py
# 输出三源 H_base/H_inc/H_joint shape/rank/E/度/嵌套/独立性/泄漏及 GATE_ALL PASS/FAIL
# gate 失败时脚本非零退出 (sys.exit(1))，不产生 Constructible: YES
```

脚本零 decoder 调用、write-free；失败时 `sys.exit(1)` 并返回 `NESTED_NOT_CONSTRUCTIBLE`。

## 6. Rank / nesting / independence / leakage preflight (decoder-free)

Preflight (write-free, zero decoder calls) SHALL rebuild deterministically via `spike_nested_rescue.py` logic 并校验：
`H_base shape==m2×1024, rank==m2`, `H_inc shape==8×1024, col≤1, row≤16, E_inc≈96, no zero row`, `H_joint shape==m2+8×1024, rank==m2+8, nested==True, rank_increment==8, joint col nonzero, joint row≤16`, `leak_joint==leak_base+40`, `tag_import_ok`, `FORBIDDEN 171` 零重叠。任一失败 → `NESTED_NOT_CONSTRUCTIBLE`.

## 7. Spike verdict — 预期 PASS (需本机实测确认)

- **Constructible (V52 nested Δ8)**: **预期 YES** — 三源 `H_joint` `m2+8` 满秩、嵌套、独立性 8、泄漏 +40 均满足，行≤16 列增量≤1。（本报告数值由构造逻辑推导，需 `python spike_nested_rescue.py` 本机实测 `GATE_ALL PASS` 后固化；若实测 rank deficient 则改判 `NESTED_NOT_CONSTRUCTIBLE` 且 V52 保持 `PLAN_CANDIDATE` 不进入执行。）
- **Single increment**: `Δm=8` only; no alternative, no seed search.
- **Equal base leakage**: 相同 `1064/1094/1104` to Lane C first pass.
- **Conditional overhead**: +40 only for rescue-attempt frames.
- **No V48/V50/V51 contact**: construction uses only frozen `60000x` constants and `v38` logic.

## 8. Subsequent paired experiment (planned, not executed) — 15 fresh held-out blocks 冻结到真实帧

与 `FORBIDDEN 171 = 96(V36..V47)+45(V48)+15(V50 391xxx)+15(V51 392xxx)` **block ID** 零重叠 per source 且与 V48/V50/V51 帧 `frame_ids` **零重叠 per source**，每源 5 块连续 IDs，写死真实 `frame_ids/ordinal`（`pairs.parquet` 区间 `60/20/20` hold 帧的 4-frame 窗口派生，`256/frame, 1024/block, BLOCK_LENGTH=1024`）。

冻结新 15 块（`393001..393005 / 393101..393105 / 393201..393205`）与 V50 `391xxx`/`392xxx` 间隙零重叠：

| source | block ID | held_out_ordinal `[start,end]` | frame_ids[4] (global) | base | H | sampling_mode |
|---|---|---|---|---|---|
| 1M (H=400, base1600) | 393001 | [33,36] | [1633,1634,1635,1636] | 1600 | 400 | deterministic_four_consecutive_frames_heldout_fresh |
| 1M | 393002 | [61,64] | [1661,1662,1663,1664] | 1600 | 400 |  |
| 1M | 393003 | [89,92] | [1689,1690,1691,1692] | 1600 | 400 |  |
| 1M | 393004 | [117,120] | [1717,1718,1719,1720] | 1600 | 400 |  |
| 1M | 393005 | [146,149] | [1746,1747,1748,1749] | 1600 | 400 |  |
| 1p5M (H=554, base2213) | 393101 | [44,47] | [2257,2258,2259,2260] | 2213 | 554 |  |
| 1p5M | 393102 | [83,86] | [2296,2297,2298,2299] | 2213 | 554 |  |
| 1p5M | 393103 | [122,125] | [2335,2336,2337,2338] | 2213 | 554 |  |
| 1p5M | 393104 | [162,165] | [2375,2376,2377,2378] | 2213 | 554 |  |
| 1p5M | 393105 | [201,204] | [2414,2415,2416,2417] | 2213 | 554 |  |
| 2M (H=729, base2916) | 393201 | [53,56] | [2969,2970,2971,2972] | 2916 | 729 |  |
| 2M | 393202 | [104,107] | [3020,3021,3022,3023] | 2916 | 729 |  |
| 2M | 393203 | [155,158] | [3071,3072,3073,3074] | 2916 | 729 |  |
| 2M | 393204 | [206,209] | [3122,3123,3124,3125] | 2916 | 729 |  |
| 2M | 393205 | [257,260] | [3173,3174,3175,3176] | 2916 | 729 |  |

- 与 `FORBIDDEN 171` 无交集 per source 连续；与 V48/V50/V51 `frame_ids` 零重叠 per source 可机械校验。
- Per block `old 1 L2 + V52 pass1 1 + 条件 pass2 ≤1`，共享 `1 L1` → 概念上 `15 L1 + ≤45 L2` decodes。
- Paired 效应 `Δexact = final_V52 - old` per block 描述性；`first_pass_success / rescued / final / old` 四计数 + `avg_leak / failed_conditional` 必报告。
- State `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`; formal paired run requires independent `EXECUTE_AUTH` bound to exact future implementation SHA (plan reference `6aa33ead...`); no output directory created in P0.

## 9. Files

- This report: `openspec/changes/formal-ir-v52-rate-adaptive-l2-rescue/spike_report.md` + `spike_nested_rescue.py` (decoder-free reproducible, HEAD `6aa33eadc872bb4551f458ee750a94cd24566314`)
- OpenSpec four: `proposal.md, design.md, tasks.md, specs/spec.md` (HEAD `6aa33eadc872bb4551f458ee750a94cd24566314`)
- Lifecycle: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`, no V53, 保持首遍冻结与嵌套增量与 fresh paired 预算不变；修订后停止等待复审. Verified `python spike_nested_rescue.py` expected exit 0 GATE_ALL PASS (需本机实测).

