# V51P0 Lane C Label Optimization Spike Report — decoder-free (deg4-first, incremental)

**Cycle**: `V51P0`
**Branch / HEAD**: `formal-ir-mainline` plan HEAD `c67a071f3b59924e81bd2bbbd452ab45f5a5c0e9`, predecessor `e3e14c9518bf44d03054e720a6230ea11d08f99a` (V50)
**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — decoder-free, no formal output, no V52
**Scope**: Three Lane C ordinal-2 supports (frozen support/perm/m2/decoder=90/1.0) → deterministic label relabel (primary lexicographic `(deg4,deg6,deg8,cand)` deg4-first, custom `check_extrinsic_score` secondary, single-run, incremental `edge_to_cycle_ids`)
**Spike script**: `openspec/changes/formal-ir-v51-lane-c-label-nbace/spike_label_nbace.py` (decoder-free, `python spike_label_nbace.py`; no `decode_*` call)
**Revision**: V51R1 — 修复 deg4 优先、自定义 score 去文献化、准入三源一致性、高效增量

## 1. Spike question

Can GF32 edge labels on the three frozen Lane C supports be deterministically relabeled (keeping support, permutations, m2, decoder 90/1.0, leakage 1064/1094/1104) to lexicographically improve the algebraic cycle spectrum — primary `(deg4,deg6,deg8)` with deg4 first — while keeping `support_exact_equal`, `rank==m2`, `support_cycles_4/6/8` unchanged, with custom `check_extrinsic_score=ACE-100 if degenerate else ACE` only as secondary report (NOT literature NB-ACE)? Gate requires **all three sources not worsen lexicographically and at least one strictly improves**; otherwise report blocker `V51_LABEL_NO_IMPROVEMENT` and stop. If gate passes, the 15-block paired experiment (45 calls) is conditionally feasible.

## 2. Frozen base (read-only)

| source | matrix_id (orig) | m2 | n | GF | support | permutations | row_deg mean/max | col deg | leak | decoder |
|---|---|---|---|---|---|---|---|---|---|
| 1M | lane_c_1M_s383102 | 184 |1024|GF32 poly37| SC L=8 w=2 41 four-support| frozen 8×perm | 11.13/12 | 2.0 |1064|90/1.0|
| 1p5M| lane_c_1p5M_s383202|190|1024|poly37|5 four-support|frozen|10.78/12|2.0|1094|90/1.0|
| 2M | lane_c_2M_s383302 |192|1024|poly37|3 four-support|frozen|10.67/12|2.0|1104|90/1.0|

All `col_degree_min/max=2`, `E=2048`, `rank==m2` GF32, `dc_max≤16`.

## 3. Optimizer (deterministic, decoder-free, single-run, incremental)

- Enumerate `c4/c6/c8` on binary support via `enumerate_canonical_simple_cycles`; reuse `edge_to_cycle_ids` mapping.
- `ACE(C)= Σ_{check∈C}(row_deg(check)-2)` (support frozen ⇒ ACE constant per cycle).
- `is_deg(C,H)= classify_cycle_algebraic_degeneracy(C,H)` (`rank<r` → degenerate); primary verifiable counts `deg4/6/8`.
- Custom `check_extrinsic_score(C)= ACE-100` if degenerate else `ACE` — **custom secondary, NOT literature NB-ACE**; `min_check_extrinsic6 = min score over 6-cycles`; `min_deg_ace6 = min ACE among degenerate 6` (secondary); `generalized_girth = min len with deg>0`, `nondeg_frac`.
- **Primary lexicographic `key=(deg4, deg6, deg8, cand)`** — deg4 first (1M 2→0 must be eliminated first, correcting prior deg6-first error); smallest `cand` tie-break. Custom score does NOT participate in primary key, only secondary reporting.
- Greedy canonical edge order `1..31`, ≤2 sweeps, early-stop 0 updates, deterministic. **Efficient incremental**: maintains global `deg4/6/8` and `is_deg` array; per edge only recomputes `incident_ids = edge_to_cycle_ids[edge]` cycles, computes `cand_d = curr_d - old_inc + cand_inc`; **does not copy full `is_deg` per candidate**.
- No decoder feedback, no seed sweep.

## 4. Decoder-free spectrum — original vs relabeled (spike actual)

Rebuilt Lane C orig via `construct_lane_c_prototype(source, seed, GF32)` and relabeled via `deterministic_label_optimize` (2 sweeps, incremental). No decoder call, `support_exact_equal` hard-checked.

### 4.1 Per-source spectrum (support/ rank / cycles invariant)

| source | rank orig→new | E | support_equal | cycles 4/6/8 orig→new | row_deg mean | note |
|---|---|---|---|---|---|---|
| 1M | 184→184 |2048|True|41/288/8459 → 41/288/8459 **equal**|11.13|PASS|
| 1p5M|190→190|2048|True|5/248/8480 →5/248/8480 **equal**|10.78|PASS|
| 2M |192→192|2048|True|12/284/9059 →12/284/9059 **equal**|10.67|PASS|

All `rank==m2`, `support_cycles` unchanged, `dc_max≤16` — invariant holds.

### 4.2 Algebraic degeneracy (primary) & custom check_extrinsic_score (secondary)

| source | deg4 o→n (Δ) | deg6 o→n (Δ) | deg8 o→n (Δ) | custom min_check_extrinsic6 o→n (Δ, secondary) | min_deg_ace6 o→n | custom min_check_extrinsic8 o→n | ggirth o→n | nondeg_frac6 o→n |
|---|---|---|---|---|---|---|---|---|
| 1M |**2→0 (-2)**|**13→0 (-13)**|**215→0 (-215)**|**-73→27 (+100)**|27→None| -66→34 (secondary)|4→None|0.955→1.000|
| 1p5M|**0→0 (0)**| **10→0 (-10)** | **274→0 (-274)** | **-73→26 (+99)** |27→None|-68→32|6→None|0.960→1.000|
| 2M |**0→0 (0)**| **12→0 (-12)**  | **261→0 (-261)** | **-76→24 (+100)** |24→None|-68→32|6→None|0.958→1.000|

- **Primary lexicographic `(deg4,deg6,deg8)`** three sources all strictly improve and none worsens: 1M `(2,13,215)→(0,0,0)`, 1p5M `(0,10,274)→(0,0,0)`, 2M `(0,12,261)→(0,0,0)` — deg4 eliminated where present, deg6/deg8 fully eliminated.
- **Custom `check_extrinsic_score`** (ACE-100 if degenerate, secondary report NOT NB-ACE) rises from `-73/-76` (degenerate-dominated) to `+24–27` (nondegenerate ACE) as secondary diagnostic; `min_deg_ace` becomes `None` (no degenerate cycles remain).
- `generalized_girth` `4/6 → None` (no degenerate cycles remain) and `nondeg_frac6/8 =1.000` for all three sources.
- Updates: 1M `sweeps 2, updates 2438`, 1p5M `2/2453`, 2M `2/2483` (incremental path, runtime 134.6s descriptive only, no algorithmic change).
- ACE topology constant (1M `min ACE among 6 =18, max 36, mean 27.4`) unchanged by labels; only `is_deg` distribution changes.

## 5. Conditional gate verdict (three-source consistency)

- **Criterion (revised)**: `label_improved = (∀source: (deg4_new,deg6_new,deg8_new) ≤_lex (deg4_old,deg6_old,deg8_old)) ∧ (∃source: (deg4_new,deg6_new,deg8_new) <_lex (deg4_old,deg6_old,deg8_old))` where `≤_lex` is deg4-first lexicographic. Custom `check_extrinsic_score` NOT in gate primary. Prior `∃source: deg6/min_check_extrinsic improves` (allowing other sources to worsen) is revoked.
- **Result**: 1M: `(2,13,215)→(0,0,0)` strictly better; 1p5M: `(0,10,274)→(0,0,0)` strictly better; 2M: `(0,12,261)→(0,0,0)` strictly better; all `not_worse=True`, `any_strict=True` → **three-source PASS**
- **Verdict**: `BLOCKER NOT TRIGGERED` — single deterministic relabel strictly improves the `(deg4,deg6,deg8)` spectrum on all three sources with no worsening while preserving support/rank/4-6-8 counts. The conditional 45-call paired experiment (15 new blocks: 392001..392005 / 392101..392105 / 392201..392205, each `1×L1 shared +2×L2 old/new =3` → `L1 15 + L2 30 =45`) is **feasible pending independent plan ACCEPT + EXECUTE_AUTH**. If instead any source had worsened or no source strictly improved, verdict would be `V51_LABEL_NO_IMPROVEMENT` and no decoder experiment. Custom score remains secondary report and is not named NB-ACE.

## 6. Reproduction

```bash
python openspec/changes/formal-ir-v51-lane-c-label-nbace/spike_label_nbace.py
# 输出三源 rank/support/cycles 不变、deg4/6/8 与 custom check_extrinsic 原 vs 新及 sweeps/updates；support_exact_equal True 时 PASS；高效增量路径
```

脚本零 decoder 调用、write-free；支撑/秩/环数不变性失败则非零退出（blocked）；增量路径与全量重算在抽样 edge 上一致可校验。正式实验前需独立重算 `rank/support_cycles/deg4/6/8` 并机械校验 `support_exact_equal` 与三源一致性门。本报告数值为脚本直出转录，禁止人工编造；自定义量明确非文献 NB-ACE。

## 7. Files

- This report: `openspec/changes/formal-ir-v51-lane-c-label-nbace/spike_report.md` + `spike_label_nbace.py` (incremental, deg4-first, custom score)
- OpenSpec four: `proposal.md, design.md, tasks.md, specs/spec.md` (PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED, V51R1)
- Lifecycle: `implementation_started=false`, `production_outputs_created=false`, no V52; production 45-call requires independent `EXECUTE_AUTH` bound to exact future implementation SHA; Lane C support/15-block/45-call/decoder/m2 design unchanged.
