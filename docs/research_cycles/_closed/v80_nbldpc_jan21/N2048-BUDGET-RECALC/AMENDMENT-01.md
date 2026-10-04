# N2048-BUDGET-RECALC — AMENDMENT-01 (PROPOSAL ONLY, NOT EFFECTIVE)

- **Status**: `PROPOSAL` — this file changes nothing. The frozen packet
  `PREREG_AND_AUTH.md` (205 lines, FROZEN) is untouched and remains the sole
  authority until/unless the main thread enacts a revision.
- **Effectiveness conditions (all three required)**: (1) independent batch-end
  review conclusion recorded; (2) explicit user authorization citing this
  amendment; (3) main-thread decision enacting it as a revised packet
  (or rejecting it). Until then, T-1 STOP stands and T-2/T-3 remain unentered.
- **Scope of this file**: doc-only proposal. No code, no test, no workspace
  root, no commit, no push. Track gate: none (doc-only, no execution).
- **Trigger**: T-1 STOP on the §3.4 ceil-order gate
  (fake 7 passed / 1 failed; T-2/T-3 not entered). Operator structural
  explanation recorded below and verified here as packet-internal.

---

## 1. 缺陷陈述 (defect statement)

### 1.1 逐字引用与行号

**§3.4 (lines 95–97)** — the defective clause:

> L95: `### §3.4 Ceil-order sub-branch (machine-checked, ≤1-bit)`
> L97: `` `L₂₀₄₈-direct(f,H) = ceil(f·2048·H) − t` vs `L₂₀₄₈-double = 2·(ceil(f·1024·H) − 64)`. Both computed; `|direct − double| ≤ 1` asserted per cell (ceil-doubling lemma); violation = STOP (§8). Verdict column uses `double` (lineage to the N=1024 anchor); `direct` is the cross-check. ``

Supporting machinery:

- L78 (`§3.1`): `L₂₀₄₈(f,H) = 2 · L₁₀₂₄(f,H)` with `L₁₀₂₄ = ceil(f·1024·H) − 64`.
- L141 (`§7`): `BUDGET2048_TABLE.csv` carries a per-cell `ceil_order_delta` column.
- L147 (`§8`): `STOP (no verdict) on: …; ceil-order delta >1 bit; …`.
- L202 (`§15` T-1): T-1 freezes `§3.4 vectors` as fake-test items, so the
  defective assertion is directly gating.

**§3.5 (lines 99–101)** — the packet's own tag-dilution admission:

> L101: `Mixed-pair illustration: with `L₁₀₂₄≈1036`, `2·1036+64=2136` vs `2208` surplus 72; …`

plus L7 (frozen antecedents):

> L7: `… tag dilution nominal-side ≈ +60 bit (illustration `2·1036+64 = 2136` vs linear-extrapolation budget 2208, surplus 72, **as the R-B+T1 paired number — see §3.5**) …`

plus L87 (`§3.2`):

> L87: `The §3.5 mixed-pair illustration (`2136` vs `2208`, surplus 72) is the **R-B+T1 paired number**, carried only as an arithmetic cross-check, never as a verdict input.`

### 1.2 定性:包内自相矛盾 (internal contradiction, NOT 外部证据推翻)

No external measurement, no new data, and no operator arithmetic error is
involved. The packet contradicts itself:

- §3.5 + L7 state, in the packet's own numbers, that a single-tag (t=64)
  N=2048 total sits ~60–72 bits away from the double-tag-implied scale
  (2136 vs 2208, surplus 72).
- §3.4 L97 simultaneously asserts that `direct(t) − double` — a quantity
  containing exactly that single-vs-double tag difference — is `≤ 1` bit
  **per cell, on every branch including T1 (t=64)**.
- §3.6 L109 independently forbids cross-branch (cross-t) pairing in verdict
  columns ("Comparing a T1 total against a T2 budget … SHALL NOT appear in
  any verdict column"). The §3.4 T1 comparison **is** such a cross-tag
  pairing wearing a ceil-lemma costume: `direct` carries one tag deduction
  (−t, t=64) while `double` carries two (−2×64=−128). The packet's §3.4
  therefore violates the packet's own §3.6 pairing rule.

### 1.3 结构性证明 (structural proof; no execution needed)

Let `x = f·1024·H` (so `f·2048·H = 2x`). Then:

```
direct(t) − double
  = [ceil(2x) − t] − 2·[ceil(x) − 64]
  = (ceil(2x) − 2·ceil(x)) + (128 − t).          … (★)
```

**Lemma** (pure ceil bit): `ceil(2x) − 2·ceil(x) ∈ {−1, 0}` for all real x.
*Proof.* Write `x = n + θ`, integer `n ≥ 0`, `θ ∈ [0,1)`.
`ceil(x) = n + (θ > 0 ? 1 : 0)`; `ceil(2x) = 2n + ceil(2θ)`.
- `θ = 0`: both terms `2n` ⇒ delta `0`.
- `θ ∈ (0, 0.5]`: `ceil(2θ) = 1`, `2·ceil(x) = 2n+2` ⇒ delta `−1`.
- `θ ∈ (0.5, 1)`: `ceil(2θ) = 2`, `2·ceil(x) = 2n+2` ⇒ delta `0`. ∎

Consequences via (★):

- **T1 (t=64)**: `direct − double = pure_term + 64 ∈ {+63, +64}` on **every**
  cell, deterministically. The `|·| ≤ 1` assertion (L97) fails on all ten
  T1 cells by construction — the observed T-1 STOP was predetermined by the
  packet text, not by any helper arithmetic error.
- **T2 (t=128)**: `direct − double = pure_term + 0 ∈ {−1, 0}` on every cell,
  deterministically. The assertion passes on all ten T2 cells with zero
  discriminating power over tag semantics (it checks only the pure lemma).
- **T3 (t=64k)**: `direct − double = pure_term + 128 − 64k`; `≤1` holds only
  for k=2 and fails for every other k by `64·|2−k| − 1 ≥ 63` bits.

In short, §3.4 conflates two quantities differing by exactly the tag gap
the packet elsewhere quantifies as ≈ +60–72 bits, then gates execution on
their near-equality. The STOP was the packet working as written against a
self-inconsistent clause — a correct trip of a miscalibrated gate.

---

## 2. 候选修订方案 (candidates A / B / C)

Common ground for all three: the verdict lineage (`double`, L78/L97
second half-sentence) and every headroom number computed through it are
**untouched**; only the `direct` cross-check definition and/or the `≤1`
assertion scope change. None of A/B/C alters any closed fact (§7 of this
proposal lists them).

### 方案 A — `ceil_order_delta` 重定义为纯 ceil 位,tag-dilution gap 单列

- **改动条款**: §3.4 L97 formula + §7 L141 column semantics + §8 L147 STOP
  trigger wording. §§3.1/3.2/3.3/3.6, §§5/11/12 untouched.
- **改动后的公式/断言原文 (proposed verbatim)**:
  > `delta_pure(f,H) = ceil(f·2048·H) − 2·ceil(f·1024·H) ∈ {−1,0} (pure ceil-doubling lemma; tag-free). Asserted per cell: |delta_pure| ≤ 1; violation = STOP. Tag-dilution gap carried in a separate non-gating column gap_tag(t) = 128 − t (+64 for T1, 0 for T2, 128−64k for T3); the old mixed quantity direct(t)−double = delta_pure + gap_tag(t) SHALL NOT gate.`
- **需重跑 AC 与 fake**:
  - Rewrite + rerun: T-1 `§3.4 vectors` (all ceil-order fake vectors under
    the new tag-free definition); §7 `ceil_order_delta` column re-emitted
    as `delta_pure` + new `gap_tag` column.
  - Re-assert on rerun (numerics unchanged, must re-emit): AC-03 (grep audit
    over renamed columns), AC-04, AC-05.
  - AC-01/AC-02 vectors reusable as-is (see §6).
- **风险**:
  1. The revised `|delta_pure| ≤ 1` gate becomes **tautologically true**
     (lemma-proven); it retains value only as a code-path checksum (catches
     implementation slips), not as a scientific check. Reviewers may fairly
     ask why a proven identity gates execution at all.
  2. Column rename touches the frozen §7 artifact spec — the largest
     mechanical diff of the three options (table header + STOP wording +
     fake vectors all change together; partial application would leave
     column/STOP/vector三者不一致).
  3. Slight didactic risk: a future reader seeing a perpetually-zero-ish
     `delta_pure` column may mistake "gate always passes" for "N=2048
     calibre confirmed" — mitigated only by the §11 ceiling block, which
     is unchanged.
- **科学结论可能方向**: none. `delta_pure` never enters K-B1/K-B2/K-B3 or
  any headroom cell; verdict-word reachability (CALIBRE-OK / AMBIGUOUS /
  KILL) is identical before/after. Touches no closed fact.

### 方案 B — 保留 `direct − double` 双 tag 语义,断言限到同 tag 数比较

- **改动条款**: §3.4 L97 assertion scope only (formula text unchanged) +
  §8 L147 STOP trigger gains a branch qualifier. §§7/3.6 need only a
  clarifying footnote, no column rename.
- **改动后的公式/断言原文 (proposed verbatim)**:
  > `` `L₂₀₄₈-direct(f,H) = ceil(f·2048·H) − t` vs `L₂₀₄₈-double = 2·(ceil(f·1024·H) − 64)`. The `|direct − double| ≤ 1` assertion applies ONLY where both sides deduct the same tag count, i.e. T2 (t=128) cells; T1/T3(k≠2) cells carry `direct − double` as a NON-GATING informative column (expected structurally at +63/+64 for T1). Cross-tag near-equality SHALL NOT gate, per §3.6. Violation = STOP applies to same-tag cells only. ``
- **需重跑 AC 与 fake**:
  - Rewrite + rerun: T-1 `§3.4 vectors` split into gating (T2) vs
    informative (T1/T3) sets; STOP-logic fake for the branch qualifier.
  - Re-assert: AC-03 (verdict columns already paired; audit now also covers
    the informative-column exclusion), AC-04, AC-05.
  - AC-01/AC-02 reusable (see §6).
- **风险**:
  1. The table permanently carries a column that reads `+63/+64` on half
     its rows — every future reader must be taught "that column is
     supposed to look broken on T1". High confusion-per-bit; invites a
     repeat of this exact incident at the next review.
  2. Branch-conditional STOP logic is the most error-prone of the three
     (a wrong qualifier re-introduces either the original false-STOP on T1
     or a silent skip of the T2 check). The qualifying fake test must be
     exact.
  3. Preserves a quantity the packet's own §3.6 calls a category error as
     a first-class emitted column, merely labeled non-gating — philosophically
     the weakest fix.
- **科学结论可能方向**: none. Same-tag restriction changes which cells can
  STOP, but T2 cells pass deterministically either way and T1 cells move
  from "false-STOP" to "informative" — no headroom, sign, or interval
  number moves. Touches no closed fact.
- **附带优点**: makes §3.4 consistent with §3.6 with the smallest textual
  diff (one scoping sentence); aligns the packet with its own pairing rule.

### 方案 C (更稳,推荐) — T1/T3  verdict 路径只用分解恒等式,ceil 差值退为全局引理单检

- **改动条款**: §3.4 L97 (replace per-cell gating delta with a single global
  lemma check) + §7 L141 (drop or demote `ceil_order_delta` to appendix) +
  §8 L147 (STOP trigger rewritten) + §15 T-1 vector list (L202).
- **改动后的公式/断言原文 (proposed verbatim)**:
  > `Verdict TOTALs use the decomposition identity TOTAL₂₀₄₈(f,H;t) = 2·(ceil(f·1024·H) − 64) + t (double lineage) by definition; no per-cell direct−double difference gates. Ceil-order is covered once globally by the tag-free lemma check delta_pure(f,H) = ceil(f·2048·H) − 2·ceil(f·1024·H) ∈ {−1,0} over the 10 (source × f-point) syndrome pairs; violation = STOP. A tag-consistent direct form direct*(f,H;t) = ceil(f·2048·H) − (t − 64)… (equivalently: direct compared only against the matching-tag double) MAY appear as a non-gating appendix diagnostic, never as a verdict input.`
  >
  > *(Drafter's note for the main thread: the exact `direct*` parenthetical
  > needs one careful editorial pass at enactment time — the load-bearing
  > sentence is the first one: verdicts flow from the decomposition
  > identity alone. If the `direct*` form risks fresh confusion, drop the
  > appendix entirely; nothing is lost.)*
- **需重跑 AC 与 fake**:
  - Rewrite + rerun: T-1 `§3.4 vectors` replaced by the 10-pair global lemma
    vectors (tag-free); STOP-logic fake updated to the global check.
  - Re-emit + re-assert: full §7 table (column dropped/demoted ⇒ AC-03 audit
    re-run mandatory), AC-04, AC-05.
  - AC-01/AC-02 reusable (see §6).
- **风险**:
  1. Largest edit surface of the three (§3.4 + §7 + §8 + T-1 list) — more
     lines for the independent reviewer to verify, and the §7 column change
     invalidates any already-written (but never-executed — T-2 never ran,
     so nothing is actually invalidated) table emitter draft.
  2. Removes a per-cell cross-check entirely; a future implementation slip
     in per-cell TOTAL emission would no longer be caught by a per-cell
     delta — mitigated by AC-04 invariance (exact per-cell equality, which
     IS a per-cell check on the numbers that matter) and the AC-01/AC-02
     back-substitution anchors.
  3. The `direct*` appendix option, if kept, needs precise wording to avoid
     minting a third formula variant; recommendation is to drop it.
- **科学结论可能方向**: none — and most robustly none: by construction C
  cannot move any headroom/sign/interval number because it deletes the only
  path through which tag semantics could leak into the gate. Verdict-word
  reachability unchanged. Touches no closed fact.
- **三方案比较**: A keeps a per-cell gate but renders it tautological; B
  keeps the misleading column alive with a label; C removes the misleading
  comparison from the gate while preserving the only check with content
  (the tag-free lemma) plus the per-cell AC-04 equality that actually guards
  the verdict numbers. **C is the most stable; A is the minimal-diff runner-up;
  B is the smallest diff but the highest future-confusion cost.**

---

## 3. 对判定词与杀死条件的影响 (K-B1 / K-B2 / K-B3, `g_req`)

- **K-B1 (calibre self-consistency, L123)**: unaffected under all of A/B/C.
  K-B1 consumes only `B_T/B_L` budget rules (R-A vs R-B adjudication via
  N=1024 back-substitution `1104/1040` and `B_T(t)−t=2080`); neither side of
  either check involves `direct`, `double`, or any ceil-order delta. Still
  fully mechanical: exact-integer equalities, R-B+T1 demonstrably dead in
  all schemes.
- **K-B2 (tag-dilution sign gate, L124)**: unaffected under all of A/B/C.
  `D_nom(t) = B_T(t) − TOTAL_double(t) = 2080 − L_double` — the tag `t`
  cancels exactly, so all surviving R-A branches share one sign by
  construction; the sign value itself is recomputed from `double`-lineage
  numbers no scheme modifies. Mechanical decidability (sign-consistency →
  CALIBRE-OK-path / split → AMBIGUOUS / all-negative → KILL) preserved
  verbatim. Note: K-B2's "expected anchor ≈ +8-bit thin surplus" (L124,
  non-binding) is re-derivable on rerun; no scheme edits it.
- **K-B3 (gain-gap quantification, L125)**: unaffected under all of A/B/C.
  `g_req(t) = 1 − 2080 / L₂₀₄₈(f₁,H)` is computed on LEAK (`L₂₀₄₈`, tag-free
  by L80 `LEAK₂₀₄₈ = TOTAL − t = L₂₀₄₈`); tag never enters. **The `g_req`
  definition needs NO revision under any candidate scheme** — state this
  explicitly at enactment so no editor "fixes" what is not broken.
- **Verdict vocabulary (§5.4 L129)**: unchanged; no new word, no removed
  word, no threshold touched by any scheme.

---

## 4. repair 额度状态 (preregistered repair quota)

Packet repair clause (L205, `§15` T-4 parenthetical):

> L205: `… Pass with no blocking comment required before any promotion; FAIL blocks promotion (rework, no rerun beyond the preregistered arithmetic correction with unchanged inputs/thresholds).`

Repository EXPLORE contract (`AGENTS.md` §1.2): at most one preregistered
repair+rerun **with unchanged scientific inputs, seeds, thresholds, data
roles and tested hypothesis**; failed attempt retained in the same log.

- **情形一 — repair 未消耗 (actual state)**: T-1 STOP froze the batch before
  any correction+rerun executed; T-2/T-3 never entered; no repair rerun has
  run. Consequence: the single engineering-repair quota is technically still
  available — **but it cannot legalize this fix**, because any of A/B/C edits
  a frozen packet clause (§3.4 + consequential §7/§8 wording), i.e. changes
  the scientific contract's gate definition, which by definition exceeds
  "unchanged inputs/thresholds/hypothesis" repair scope. The quota covers an
  operator/helper slip (wrong ceil call, typo'd constant); it does not cover
  rewriting the packet's own assertion. Using it here would be a scope
  violation even though the quota is unspent.
- **情形二 — repair 视为已消耗 (counterfactual)**: if the T-1 fake attempt
  itself (or any ad-hoc correction already applied to the helper) is counted
  as the one repair, then consequence: **zero** reruns remain; any
  re-execution under a revised clause set needs a fresh authorization and a
  revised (or successor) packet regardless.
- **本提案判断**: 情形一成立 (repair 未消耗),但两种情形收敛到同一后果 —
  **structural packet defects are outside the repair boundary either way**;
  proceeding requires independent-review conclusion + new user authorization
  + main-thread enacted revision (see §8 of this proposal), not expenditure
  of the leftover engineering quota. The unused quota, if the revised packet
  retains an equivalent clause, transfers to the revised packet's own T-1
  execution — it must not be treated as already spent by this never-rerun
  STOP.依据: L205 "with unchanged inputs/thresholds" 限定 + `AGENTS.md`
  §1.2 repair 条款 ("unchanged scientific inputs, seeds, thresholds, data
  roles and tested hypothesis"); §3.4 改写恰恰改变 gate 定义,不满足该限定。

---

## 5. AC-04 / AC-05 修订前是否本就无意义 (judgment)

**判断:否 — AC-04 与 AC-05 修订前仍有意义,未被 tag 项污染.**
污染只存在于 §3.4 `ceil_order_delta` 一列,不在 AC-04/AC-05:

- **AC-04 (invariance, L156: `D_T(T1)=D_T(T2)=D_L`)**: tag-free by
  algebra. Under surviving R-A pairs,
  `D_T(t) = B_T(t) − TOTAL_double(t) = (2080+t) − (L_double+t) = 2080 − L_double = D_L`.
  Both `+t` terms cancel exactly per cell; the T1/T2 equality holds (or
  fails, diagnostically) independent of any tag-dilution magnitude. The
  check guards the verdict numbers that matter and is orthogonal to the
  §3.4 defect. Verdict: AC-04 有意义且在修订后原样保留,无需改写。
- **AC-05 (slope, L157: 84–85±2 lineage / 168–170±2 recomputed)**: tag-free
  by differencing. Slope = ΔTOTAL per 0.1f; the additive `+t` cancels in
  every difference, so tag dilution cannot pollute it under either lineage.
  (Caveat for the rerun, not for meaningfulness: slope vectors must be
  recorded against ONE stated lineage — `double` — so a mixed-lineage slope
  cannot sneak in; that is bookkeeping, not a formula fix.) Verdict: AC-05
  有意义且在修订后原样保留。
- 真正无意义的 (must be revised, not retained): §3.4 L97 的 T1/T3(k≠2)
  cells 上的 `|direct−double| ≤ 1` 断言,以及 §7 `ceil_order_delta` 在该定义下
  的 T1 列值 (+63/+64) — 它们是结构性常数,不是检验。

---

## 6. 重跑范围 (rerun scope after enactment)

### 6.1 可复用 (reusable without recomputation; re-verify transcription per §8)

- **AC-01 vectors** (L153: R-A N=1024 back-substitution `1104/1040`): the
  N=1024 anchor involves no doubling and no §3.4 quantity. Reusable as
  frozen evidence; rerun re-asserts the same integers.
- **JOINT anchor constants** (H-1…H-5, f₀=1.3, f₁=1.56, L55–L66
  transcription): reusable as transcribed inputs; the rerun's §8
  transcription-vs-text check re-verifies them but does not recompute them.
- **§3.5 slope-illustration arithmetic** (`2·1036+64=2136` etc., L101):
  reusable as the arithmetic-path cross-check narrative; tag-free slope
  content (see §5) unaffected.
- **AC-08 forbidden-token pattern + AC-07 ceiling block + AC-06 vocabulary
  machinery**: reusable verbatim (no scheme touches §§5.4/9/11).

### 6.2 必须重算/重写 (must recompute under the enacted scheme)

- **T-1 `§3.4 vectors`** (all ceil-order fake vectors): rewrite to the
  enacted definition (A: `delta_pure` + `gap_tag`; B: gating/informative
  split; C: 10-pair global lemma) and rerun green. This is the core rerun.
- **§7 `BUDGET2048_TABLE.csv` `ceil_order_delta` column** (all cells):
  re-emit under the new definition (A renames/extends; B annotates scope;
  C drops/demotes). No T-2 table was ever emitted (T-2 unentered), so this
  is first-emission-under-revision, not invalidation of prior evidence.
- **AC-03 audit** (L155, paired-only + no cross-branch cells): re-run the
  grep audit against the revised column set — mandatory under all schemes
  because the audited column inventory changes.
- **AC-04 + AC-05**: numerics expected identical (tag-cancelled, §5 of this
  proposal) but MUST be re-emitted and re-asserted inside the new table;
  prior T-1 partial evidence does not substitute for the revised-table
  assertion.
- **T-2 full run** (20 cells + invariants, L203) and **T-3 full run**
  (`g_req` interval + §5.4 word, L204): never executed → full first
  execution under revision, in K-B1→K-B2→K-B3 order with short-circuit.
- **AC-09 Pre-EXECUTE checklist** (L161/§9.1) and **AC-10 independent
  batch-end review** (L162): re-recorded fresh against the revised packet;
  the pending independent review of the ORIGINAL packet does not transfer
  as a pass for revised execution.

---

## 7. 本提案不改变的东西 (explicit non-changes; closed items stay closed)

Enactment of any of A/B/C SHALL NOT, by side effect or reinterpretation:

1. **Stage-0 KILL**: per-plane independent KILL on its frozen f grid +
   budget only — untouched, not re-argued.
2. **JOINT MARGINAL §5.3(a)**: `1100 余 4 / 1319 超 215` — 双数字同引
   (surplus 4 nominal-side, excess 215 at +20%); no solo-nominal citation
   smuggled in via this amendment.
3. **超帧 KILL 范围限定**: M0-2M eval-region sequences only — untouched.
4. **C 轨 `STRUCTURALLY_INCOMPLETE_KILL`**: 仅限 R2 同 6×40/240 分区与描述性
   单价 `51.0 s/block` — never cited as proxy-infeasible or
   channel-stationary; this amendment draws no C-track inference.
5. **U1 天花板为 context** (never clearance); `S_a`/`S_spread` context-only;
   `FLAG=False` non-detection under α=0 only.
6. **void 基线永不作基线**: no void reference, no ranking, no joint table
   introduced.
7. **`0.098260` 永禁当测量** (AC-08 forbidden-token list intact; pattern
   lines in packet/result-config exempt by exact-line allowlist only).
8. **`51.0 s` 禁作吞吐**: descriptive unit-price only, never a throughput
   figure.
9. 本提案**不断言 N=2048 可行或不可行** — it repairs a gate definition; the
   feasibility word belongs to the later sweep packet under its own DECIDE
   gate, and to this packet's §5.4 word only after clean re-execution.
   No closed item is advanced, narrowed, or reopened by this amendment.

---

## 8. Track 与授权 (track + effectiveness + re-authorization needs)

- **本提案 Track**: none — doc-only, zero execution, zero data contact, zero
  workspace write. No EXPLORE/DECIDE gate is consumed by writing or reading
  this file.
- **生效条件 (conjunction)**: (i) 独立批末审查结论 recorded (the parallel
  reviewer-go review is NOT prejudged by this proposal — it may agree,
  disagree, or find further defects; its conclusion governs); (ii) 用户显式
  授权 citing this amendment and the review conclusion; (iii) 主线程决定
  (enact one of A/B/C as a revised packet version, or reject with reasons).
  Absent any one of the three, the frozen packet + T-1 STOP remain the state
  of record.
- **生效后 T-1…T-3 的新授权需求**: revision is a changed scientific contract,
  so the original §14 lineage grant does not carry over. Required before any
  re-execution: fresh **Pre-EXECUTE record** (§9.1 items re-verified against
  the REVISED text: branch, scoped §10 manifest re-frozen to the new vectors,
  unchanged-except-§3.4 contract diff explicitly listed, explicit user grant
  citing the revised section, FRESH target root `workspace/n2048b_<new-uuid8>`
  absence — the old root, if any partial root was created, is retained, never
  overwritten) + explicit user authorization for T-1…T-3 + focused fake tests
  green under the new definitions. T-4 independent review re-runs against the
  revised packet (AC-01…AC-10 + §11 verbatim + AC-08 sweep).

---

## Blocker (current)

- **Enactment blocked pending**: (1) independent batch-end review conclusion
  (parallel reviewer-go thread — do not prejudge); (2) user explicit
  authorization; (3) main-thread decision on scheme choice (A/B/C) and
  revised-packet issuance. This file requests all three and authorizes none.
- No code/test/execution blocker is asserted — nothing is asked to run until
  a revised packet with fresh Pre-EXECUTE exists.
