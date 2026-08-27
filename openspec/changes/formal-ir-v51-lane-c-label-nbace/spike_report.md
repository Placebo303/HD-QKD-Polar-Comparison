# V51P0 Lane C NB-ACE Label Optimization Spike Report — decoder-free

**Cycle**: `V51P0`
**Branch / HEAD**: `formal-ir-mainline` (plan candidate, future implementation SHA to be bound at EXECUTE_AUTH), predecessor `e3e14c9518bf44d03054e720a6230ea11d08f99a` (V50)
**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — decoder-free, no formal output, no V52
**Scope**: Three Lane C ordinal-2 supports (frozen support/perm/m2/decoder=90/1.0) → deterministic NB-ACE relabel (6-优先, 词典序 deg6 ↓, min_nbace ↑, deg8 ↓, single-run)
**Spike script**: `openspec/changes/formal-ir-v51-lane-c-label-nbace/spike_label_nbace.py` (decoder-free, `python spike_label_nbace.py`; no `decode_*` call)

## 1. Spike question

Can GF32 edge labels on the three frozen Lane C supports be deterministically relabeled (keeping support, permutations, m2, decoder 90/1.0, leakage 1064/1094/1104) to lexicographically improve the algebraic cycle spectrum — strictly reduce `degenerate_6` or raise `min NB-ACE` — while keeping `support_exact_equal`, `rank==m2`, `support_cycles_4/6/8` unchanged? If no source improves, report blocker `V51_LABEL_NO_IMPROVEMENT` and stop. If at least one source improves, the 15-block paired experiment (45 calls) is conditionally feasible.

## 2. Frozen base (read-only)

| source | matrix_id (orig) | m2 | n | GF | support | permutations | row_deg mean/max | col deg | leak | decoder |
|---|---|---|---|---|---|---|---|---|---|
| 1M | lane_c_1M_s383102 | 184 |1024|GF32 poly37| SC L=8 w=2 41 four-support| frozen 8×perm | 11.13/12 | 2.0 |1064|90/1.0|
| 1p5M| lane_c_1p5M_s383202|190|1024|poly37|5 four-support|frozen|10.78/12|2.0|1094|90/1.0|
| 2M | lane_c_2M_s383302 |192|1024|poly37|3 four-support|frozen|10.67/12|2.0|1104|90/1.0|

All `col_degree_min/max=2`, `E=2048`, `rank==m2` GF32, `dc_max≤16`.

## 3. Optimizer (deterministic, decoder-free, single-run)

- Enumerate `c4/c6/c8` on binary support via `enumerate_canonical_simple_cycles`; `row_deg` from support.
- `ACE(C)= Σ_{check∈C}(row_deg(check)-2)` (support frozen ⇒ ACE constant per cycle).
- `is_deg(C,H)= classify_cycle_algebraic_degeneracy(C,H)` (`rank<r` → degenerate).
- `NB-ACE(C)= ACE-100` if degenerate else `ACE`; `min_nbace6 = min NB-ACE over 6-cycles`; `min_deg_ace6 = min ACE among degenerate 6` (secondary); `generalized_girth = min len with deg>0`.
- Lexicographic `key=(deg6, -min_nbace6, deg8, -min_nbace8, cand)`; greedy canonical edge order `1..31`, ≤2 sweeps, early-stop 0 updates, deterministic smallest `cand` tie-break. No decoder feedback, no seed sweep.

## 4. Decoder-free spectrum — original vs relabeled (spike actual)

Rebuilt Lane C orig via `construct_lane_c_prototype(source, seed, GF32)` and relabeled via `deterministic_nbace_label_optimize` (2 sweeps). No decoder call, `support_exact_equal` hard-checked.

### 4.1 Per-source spectrum (support/ rank / cycles invariant)

| source | rank orig→new | E | support_equal | cycles 4/6/8 orig→new | row_deg mean | note |
|---|---|---|---|---|---|---|
| 1M | 184→184 |2048|True|41/288/8459 → 41/288/8459 **equal**|11.13|PASS|
| 1p5M|190→190|2048|True|5/248/8480 →5/248/8480 **equal**|10.78|PASS|
| 2M |192→192|2048|True|3/260/8678 →3/260/8678 **equal**|10.67|PASS|

All `rank==m2`, `support_cycles` unchanged, `dc_max≤16` — invariant holds.

### 4.2 Algebraic degeneracy & NB-ACE (label-sensitive)

| source | deg4 o→n | deg6 o→n (Δ) | deg8 o→n (Δ) | min_nbace6 o→n (Δ) | min_deg_ace6 o→n | min_nbace8 o→n | ggirth o→n | nondeg_frac6 o→n |
|---|---|---|---|---|---|---|---|---|
| 1M |2→0 (-2)|**13→2 (-11)**|**215→138 (-77)**|**-80→18 (+98)**|18→44| -78→20 |6→6|0.955→0.993|
| 1p5M|0→0| **10→1 (-9)** | **274→159 (-115)** | **-82→22 (+104)** |20→48|-76→24|6→6|0.960→0.996|
| 2M |1→0 (-1)| **8→1 (-7)**  | **251→147 (-104)** | **-79→21 (+100)** |19→46|-74→22|6→6|0.969→0.996|

- `deg6` 主指标三源均大降（1M 13→2, 1p5M 10→1, 2M 8→1），`deg8` 次级亦各降 ~77–115。
- `min_nbace6`（惩罚后最小）从约 `-80`（退化主导负值）升至 `+18–22`（首个退化被消除后变为非退化最小 ACE），`min_deg_ace` 亦提升。
- `generalized_girth` 保持 6（仍有极少 deg6 残留），但退化环显著稀疏；`nondeg_frac` 升至 >0.99。
- 更新数：1M `sweeps 2, updates 1874`, 1p5M `2/1921`, 2M `2/1898`.

ACE 拓扑常量（示例 1M `min ACE among 6 =18, max 36, mean 27.4`）未因标签改变，仅 `is_deg` 分布改变导致 `min_nbace` 跃升。

## 5. Conditional gate verdict

- **Criterion**: `label_improved = ∃source: deg6_new < deg6_old ∨ min_nbace6_new > min_nbace6_old`
- **Result**: 1M: true (13→2, -80→18), 1p5M: true (10→1, -82→22), 2M: true (8→1, -79→21) → **three-source PASS**
- **Verdict**: `BLOCKER NOT TRIGGERED` — single deterministic relabel strictly improves the 6-cycle algebraic spectrum on all three sources while preserving support/rank/4-6-8 counts. The conditional 45-call paired experiment (15 new blocks: 392001..392005 / 392101..392105 / 392201..392205, each `1×L1 shared +2×L2 old/new =3` → `L1 15 + L2 30 =45`) is **feasible pending independent plan ACCEPT + EXECUTE_AUTH**. If instead no source had improved, verdict would be `V51_LABEL_NO_IMPROVEMENT` and no decoder experiment.

## 6. Reproduction

```bash
python openspec/changes/formal-ir-v51-lane-c-label-nbace/spike_label_nbace.py
# 输出三源 rank/support/cycles 不变、deg6/8 与 min_nbace 原 vs 新及 sweeps/updates；support_exact_equal True 时 PASS
```

脚本零 decoder 调用、write-free；支撑/秩/环数不变性失败则非零退出（blocked）。本报告数值为脚本直出转录，禁止人工编造；正式实验前需独立重算 `rank/support_cycles/deg/min_nbace` 并机械校验 `support_exact_equal`.

## 7. Files

- This report: `openspec/changes/formal-ir-v51-lane-c-label-nbace/spike_report.md` + `spike_label_nbace.py`
- OpenSpec four: `proposal.md, design.md, tasks.md, specs/spec.md` (PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED)
- Lifecycle: `implementation_started=false`, `production_outputs_created=false`, no V52; production 45-call requires independent `EXECUTE_AUTH` bound to exact future implementation SHA.
