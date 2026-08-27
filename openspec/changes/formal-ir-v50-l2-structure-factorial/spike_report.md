# V50P0 Structure Spike Report — decoder-free single protograph/MET L2 candidate (VERIFIED CONSTRUCTION)

**Cycle**: `V50P0`
**Branch / HEAD**: `formal-ir-mainline` / `d95d46ac559ac9e5860ebcc793abc0500ba9b09b` (plan SHA; future implementation SHA to be bound at EXECUTE_AUTH), predecessor result `28228b9d4bf158361d247aac89c1864e1b5ca9b0` (V48 result) — prior `f58955f3...` deprecated
**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — decoder-free, no formal output, no V51
**Scope**: One equal-leakage **true MET** L2 candidate vs Lane C, orthogonal TRAIN vs TRAIN+VAL prior, 15 held-out blocks 2×2 factorial (90 calls)
**Spike script**: `openspec/changes/formal-ir-v50-l2-structure-factorial/spike_construct.py` (decoder-free, reproducible, `python spike_construct.py`; no `decode_*` call)

## 1. Spike question

Can a single deterministic **true MET** L2 matrix be constructed decoder-free with `n=1024, m2∈{184,190,192}, GF32 poly37, no-zero-column, full-row-rank, bounded degree-2 chains/rings, deterministic lifting/label, no seed search`, at exactly the same `m2`/leakage as Lane C (`1064/1094/1104`, `leak=5*m2+80+64` 与 `E` 无关), same decoder `90/1.0`, zero 4-cycles, reported 6/8-cycles, frozen `dc_max=16`, and rules that do not touch V48 outcomes? 1024 全 `dv=2` 非 MET — 本 spike 构造真 MET `{dv2:512,dv3:512}` (`E=2560, dv_mean=2.5`); 若坚持全 `dv2` 则改名 `PEG-dv2, E=2048` 并修正定义。

## 2. Candidate identity (unique, no seed search)

**Candidate ID**: `P0-MET-1 — single deterministic PEG-MET {dv2:512,dv3:512}, E=2560` (`PEG-dv2` 为备选名)
- One candidate only. No seed sweep, no tuning, no fallback, no V48 outcome ingestion.
- Per-source deterministic matrices: `p0_met_1M_det1 / p0_met_1p5M_det1 / p0_met_2M_det1`, each `m2×1024`, GF32 `poly=37` (`GF2mField.create(32)`), `m2=184/190/192`.
- Degree distribution: `col_degree` exactly `512×dv2 + 512×dv3`, `E=2560` (与泄漏无关；泄漏仅由 `m2` 决定).
- Naming: `p0_met_{source}_det1` (suffix `det1` = deterministic single construction, not a seed).
- Deterministic ids: `500001 (1M) / 500002 (1p5M) / 500003 (2M)` for `SeedSequence([det,1])` (support tie-break) and `SeedSequence([det,2])` (labels). No `SeedSequence([seed,...])` sweep.
- Fallback note: `PEG-dv2` (`E=2048, 1024×dv2`) 同样可构造（本报告附表对比），但非 MET，需改名与修正环定义；V50 主选为真 MET。

## 3. Frozen invariants (equal leakage, same decoder)

| Item | Frozen value | Note |
|---|---|---|
| n | 1024 |  |
| m2 per source | 184 (1M), 190 (1p5M), 192 (2M) | identical to Lane C `SOURCE_CHECKS` |
| GF | GF32 poly37 | `DIMENSION=32, POLYNOMIAL=37` |
| Leakage | `5*m2+5*m1+64` with `m1=16` → `1064 / 1094 / 1104` (920/950/960 +80+64) | exactly Lane C, no change; **与 `E` 无关** |
| Decoder | `decode_row_layered_fftqspa` row-layered FFT-QSPA, `max_iter=90, damping_alpha=1.0, early-stop frozen` | same as Lane C §5 |
| Row degree cap | `dc_max = 16` (MAX_CHECK_DEGREE_LIMIT) | frozen |
| Edge budget | **真 MET `E=2560`** (`512*2+512*3`, `dv_mean 2.5`); `PEG-dv2` 备选 `E=2048` | **同 `m2` 等泄漏，不以 `E` 冻结泄漏** |
| H1 | `V31-H1-QC-16×1024 rank16 80b` | frozen |
| Tag | `compute_tag_64(empty,x2)` L2-only | frozen |

## 4. Construction rules (decoder-free, deterministic) — 真 MET

1. **No zero column / no zero row** — `col_degree ∈{2,3}` (512 each), `row_degree ≥1`; hard gate.
2. **Full row rank GF32** — `rank_GF32 == m2` via `compute_gf32_rank`; hard gate. If rank-deficient → `CANDIDATE_NOT_CONSTRUCTIBLE` (not retried with another seed).
3. **Deterministic support placement — PEG-MET with strict 4-cycle avoidance across degree levels** — Order `j=0..1023` deterministic; `dv_list = [2]*512+[3]*512` (`j<512→2 else 3`). For each column's `d` checks: iteratively, group eligible checks by `check_degrees` ascending, and within each degree level select only candidates where all pairs `(pc,c)` are fresh in global `check_pairs_connected`; pick lowest `rank_in_perm` among the first degree level that offers such a candidate. If no level offers a fresh candidate, fallback to minimal-degree pick (signals `CANDIDATE_NOT_CONSTRUCTIBLE`; with these parameters this branch is not taken → `support_cycles_4==0` guaranteed). Coeff by `SeedSequence([det,2])` `sample_uniform_gf32_nonzero` on canonical edge order `get_canonical_support_edges`. No search. *Fixed 2026-08-28: previous version only searched within minimal-degree set, allowing forced duplicates → 32/53/33 4-cycles.*
4. **Degree-2 chain/ring limits — 唯一权威定义 (fixes double-count)**:
   - Define induced subgraph `G2` = subgraph induced by `dv==2` vars only (512 nodes) plus incident checks, edges only to `dv==2` vars. A **degree-2 chain** is a maximal path `v0-c0-v1-c1-...-vk` in `G2` where every internal check has `deg==2` **within `G2`** (`check_to_vars_G2 ==2`). `max_degree2_chain = max vars in such path`; hard gate `≤4` vars (authoritative graph metric).
   - **Degree-2 pure ring (authoritative)**: `pure_ring_via_graph` as defined by the graph method above (cycles where every internal check has `deg==2` within `G2` and `2*|vars|≤12`). **Enumerated `pure_4/6/8` (all-vars-dv2 cycles from `enumerate_canonical_simple_cycles` filtered by `col_deg==2`) are reporting only, NOT the gate**; they count any cycle whose variables are all `dv==2` even if checks branch (`deg>2` in `G2`). The double-count is removed: gate uses `pure_ring_via_graph==0` only. Single `dv=3` on cycle breaks both but graph metric is stricter.
5. **Deterministic lifting & label**: `Q=1` direct finite matrix; two variable types (`dv2`/`dv3`)即 MET type partition; shift/label均由上述两个确定性子流派生；无随机 seed 轮询；label `∈1..31`.
6. **Prohibit seed search** — single `det` per source; no ordinal registry, no winner selection.
7. **4-cycle elimination priority** — hard `support_cycles_4 == 0` via rule 3. `6/8-cycles` reported (`enumerate_canonical_simple_cycles` + `classify_cycle_algebraic_degeneracy`), `pure_*` 单独报告.
8. **Row degree frozen** — `row_degree_max ≤16`; `E` frozen per construction (`2560` MET / `2048` PEG) 但不冻结泄漏.
9. **V48 non-touch** — construction constants, counts, block samples, thresholds do not read `v48_summary.json`/`v48_records.json`.

## 5. Cycle census and degree-2 metrics — 实测 (decoder-free, `spike_construct.py`)

Using `enumerate_canonical_simple_cycles` on binary support + `compute_structural_metrics` + `degree2_chain_and_pure_ring` (G2 精确). **三矩阵实际生成**，零 decoder 调用。

### 5.1 真 MET `{dv2:512,dv3:512} E=2560` — V50 主选 (spike 实测, regenerated 2026-08-28)

| source | m2 | det | shape | rank | E | col_deg dist | row_deg min/mean/max | dc_max≤16 | 4-cycles | 6-cycles | 8-cycles | deg 4/6/8 | pure 4/6/8 (report) | max_chain | pure_ring(graph) | gate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1M | 184 | 500001 | 184×1024 | 184 | 2560 | {2:512,3:512} 2/3/2.5 | 13/13.91/14 | YES | **0** | 8528 | 101870 | 0/284/3261 | 0/576/1766 (2342) | **1** | **0** | PASS |
| 1p5M | 190 | 500002 | 190×1024 | 190 | 2560 | {2:512,3:512} | 13/13.47/14 | YES | **0** | 8175 | 92601 | 0/282/2994 | 0/454/941 (1395) | **1** | **0** | PASS |
| 2M | 192 | 500003 | 192×1024 | 192 | 2560 | {2:512,3:512} | 13/13.33/14 | YES | **0** | 8016 | 90244 | 0/259/2830 | 0/512/1520 (2032) | **1** | **0** | PASS |

- `rank==m2` 满行秩, `zero_col==0, zero_row==0`, `support_cycles_4==0` 硬门通过, `max_degree2_chain≤4` (实测 1), `pure_ring_via_graph==0` authoritative. Enumerated `pure_*` (all-vars-dv2) for reporting only; `pure_ring(graph)==0` does not imply `pure_*==0`.
- `6/8-cycles` 实测 `~8k / ~90-101k` (script直出), `degenerate_*` 随 `GF32` label 变化但拓扑 `support_cycles_*` 确定. Prior table `387/412/398` and `2714/2839/2791` were stale transcription — now fixed to script.
- `row_degree_max==14` (not 16) 仍 ≤16；`mean ≈ E/m` 符合预期. Script now exits non-zero on any gate FAIL.

### 5.2 PEG-dv2 `E=2048 (1024×dv2)` 对比 (非 MET, 需改名) — regenerated

| source | m2 | det | E | col {2:1024} | row mean/max | 4-cyc | 6-cyc | 8-cyc | deg 4/6/8 | pure (report) | max_chain | pure_ring(graph) | gate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1M | 184 | 500001 | 2048 | 2/2/2.0 | 11.13/12 | 0 | 1704 | 10368 | 0/50/339 | 0/1704/10368 | 1 | 0 | PASS |
| 1p5M | 190 | 500002 | 2048 | 2/2/2.0 | 10.78/11 | 0 | 2294 | 12902 | 0/71/431 | 0/2294/12902 | 1 | 0 | PASS |
| 2M | 192 | 500003 | 2048 | 2/2/2.0 | 10.67/11 | 0 | 2304 | 15536 | 0/61/527 | 0/2304/15536 | 1 | 0 | PASS |

- 全 `dv=2` 可构造且通过同门，但**非 MET** (单一度)，若保留需文档改名 `PEG-dv2` 并使用本节 `G2` 精确环定义；V50 主选仍为 §5.1 真 MET.

### 5.3 复现命令

```bash
python openspec/changes/formal-ir-v50-l2-structure-factorial/spike_construct.py
# 输出三矩阵 shape/rank/E/度分布/4,6,8-cycle/degenerate/pure_chain_ring 及 GATE_ALL PASS/FAIL
# gate 失败时脚本非零退出 (sys.exit(1))，可作证明
```

脚本零 decoder 调用、write-free；失败时 `sys.exit(1)` 并返回 `CANDIDATE_NOT_CONSTRUCTIBLE`，不产生 `Constructible: YES`；本报告数值由脚本直出后转录，禁止人工编造.

## 6. Rank / zero-column / chain-ring preflight (decoder-free)

Preflight (write-free, zero decoder calls) SHALL rebuild `H_p0_met_{source}` deterministically via `spike_construct.py` 逻辑并校验：
`shape==m2×1024`, `rank_GF32==m2`, `col_degree` 分布 `{2:512,3:512}` (MET) / `{2:1024}` (PEG), `row_degree_max≤16`, `support_edge_count==2560` (MET) / `2048` (PEG), `support_cycles_4==0`, `max_degree2_chain≤4`, `pure_ring(len≤12)==0` (G2 精确), `6/8-cycles` 报告. 任一失败 → `CANDIDATE_NOT_CONSTRUCTIBLE`.

## 7. Spike verdict — 已实证

- **Constructible (V50 主选 真 MET)**: **YES — 实测 PASS** (三矩阵 `184/190/192×1024`, `E=2560`, `rank==m2`, `zero_col/row==0`, `dc_max≤16`, `4-cycles==0`, `max_chain 2-3 ≤4`, `pure_ring==0`). 详见 §5.1.
- **PEG-dv2 fallback**: 同样 PASS (§5.2) 但非 MET；若 V50 保留全 `dv2` 则 lifecycle 文档改名 `PEG-dv2`.
- **Single candidate**: `P0-MET-1 {dv2:512,dv3:512}` only; no alternative, no seed search.
- **Equal leakage**: 相同 `1064/1094/1104` to Lane C (仅 `m2` 决定, 与 `E` 无关).
- **Decoder unchanged**: `90/1.0` row-layered FFT-QSPA.
- **No V48 contact**: construction uses only frozen `det` constants and `v38` tie-break logic, not `v48` outcomes.
- **Blocked path handling**: 若任一 gate 失败则标记 `CANDIDATE_NOT_CONSTRUCTIBLE`，V50 保持 `PLAN_CANDIDATE` 且不进入 decoder 执行，需换规划.

## 8. Subsequent 2×2 experiment (planned, not executed) — 15 未使用 held-out blocks 冻结到真实帧

与 `FORBIDDEN 141 = 96(V36..V47)+45(V48)` **block ID** 零重叠且与 V48 180 帧 `frame_ids` **零重叠 per source**（不仅种子查重），每源 5 块连续 IDs，写死真实 `frame_ids/ordinal`（`pairs.parquet` 区间 `60/20/20` hold 帧的 4-frame 窗口派生，`256/frame, 1024/block, BLOCK_LENGTH=1024, pair_idx 0..255`）.

旧 `391xxx` 仅标签 — 现冻结为真实帧（与 V48 `HELDOUT_STARTS` 分散窗口零重叠，验证 `BLOCK_WINDOWS`）：

| source | block ID | held_out_ordinal `[start,end]` | frame_ids[4] (global) | base | H | sampling_mode |
|---|---|---|---|---|---|---|
| 1M (H=400) | 391001 | [14,17] | [1614,1615,1616,1617] | 1600 | 400 | deterministic_four_consecutive_frames_heldout_unused |
| 1M | 391002 | [42,45] | [1642,1643,1644,1645] | 1600 | 400 |  |
| 1M | 391003 | [70,73] | [1670,1671,1672,1673] | 1600 | 400 |  |
| 1M | 391004 | [98,101] | [1698,1699,1700,1701] | 1600 | 400 |  |
| 1M | 391005 | [127,130] | [1727,1728,1729,1730] | 1600 | 400 |  |
| 1p5M (H=554) | 391101 | [19,22] | [2232,2233,2234,2235] | 2213 | 554 |  |
| 1p5M | 391102 | [58,61] | [2271,2272,2273,2274] | 2213 | 554 |  |
| 1p5M | 391103 | [97,100] | [2310,2311,2312,2313] | 2213 | 554 |  |
| 1p5M | 391104 | [137,140] | [2350,2351,2352,2353] | 2213 | 554 |  |
| 1p5M | 391105 | [176,179] | [2389,2390,2391,2392] | 2213 | 554 |  |
| 2M (H=729) | 391201 | [25,28] | [2941,2942,2943,2944] | 2916 | 729 |  |
| 2M | 391202 | [77,80] | [2993,2994,2995,2996] | 2916 | 729 |  |
| 2M | 391203 | [129,132] | [3045,3046,3047,3048] | 2916 | 729 |  |
| 2M | 391204 | [181,184] | [3097,3098,3099,3100] | 2916 | 729 |  |
| 2M | 391205 | [232,235] | [3148,3149,3150,3151] | 2916 | 729 |  |

- V48 `HELDOUT_STARTS` (15 per source) e.g. 1M `[0,28,56,84,113,141,169,198,226,254,282,311,339,367,396]` 等与本表新窗口逐区间无交集 per source；与 FORBIDDEN 141 block IDs 无交集 per source 连续；与 V38–V48 帧 `frame_ids` 零重叠 per source 可机械校验 (`BLOCK_WINDOWS[block_id].frame_ids` 比对).
- Per block `2×L1 (TRAIN vs TRAIN+VAL) +4×L2 (A=TRAIN×LaneC, B=TRAIN+VAL×LaneC, C=TRAIN×P0, D=TRAIN+VAL×P0) =6` → Total `90` (`L1 30 + L2 60`).
- 因子效应冻结: `E_structure=(C+D-A-B)/2`, `E_prior=(B+D-A-C)/2`, `E_interaction=(D-C)-(B-A)`，并保留四个 simple effects `C-A(TRAIN下结构)/D-B(TRAIN+VAL下结构)/B-A(LaneC下先验)/D-C(P0下先验)`；`C-A` 为 simple effect 非主效应.
- Gates descriptive, no promotion; `exact_full=exact_u1&&exact_l2` oracle, `exact = array_equal(x_hat, ut)`.
- State `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`; formal 90-call run requires independent `EXECUTE_AUTH` bound to exact future implementation SHA (plan reference `d95d46ac...`, not `f58955f...`); no output directory created in P0.

## 9. Files

- This report: `openspec/changes/formal-ir-v50-l2-structure-factorial/spike_report.md` + `spike_construct.py` (decoder-free reproducible, HEAD `d95d46ac...`)
- OpenSpec four: `proposal.md, design.md, tasks.md, specs/formal-ir-v50-l2-structure-factorial/spec.md` (HEAD `d95d46ac559ac9e5860ebcc793abc0500ba9b09b`)
- Lifecycle: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`, no V51, 保持同 `m2`、四臂 `90-call` 预算、15 held-out 块与零 decoder 规划轮边界不变；旧 `f58955f...` 绑定已清理；修订后停止等待复审. Verified `python spike_construct.py` exit 0 GATE_ALL PASS, 4-cycles 0.
