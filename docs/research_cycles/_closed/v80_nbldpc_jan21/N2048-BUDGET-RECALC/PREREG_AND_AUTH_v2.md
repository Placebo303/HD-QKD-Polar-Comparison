# N2048-BUDGET-RECALC — PREREG_AND_AUTH_v2 (Frozen successor packet; Scheme-C enactment; pure arithmetic, no gain claim)

- **Status**: FROZEN — successor execution packet for the B-track budget-calibre gate. This packet authorizes only EXPLORE arithmetic T-1…T-4 in one fresh additive root and nothing else (§§6/14). Operator records the Pre-EXECUTE checklist (§9.1) before T-1.
- **Supersession (disposition record)**: this file **supersedes** `PREREG_AND_AUTH.md` (v1, 205 lines, FROZEN) as the sole B-track execution authority. `PREREG_AND_AUTH.md` (v1) and `AMENDMENT-01.md` (406 lines, PROPOSAL) both transfer to **record status** with disposition **`superseded-before-execution`** — retained unmodified as records, never deleted, never rewritten, **not citable as current authority**. The successor authority is this v2 file alone.
- **Track**: **EXPLORE** (pure arithmetic; zero data contact — see §0.1).
- **Branch**: `formal-ir-v72p1-addendum-clean`. No commit, no push by the operator.
- **Revision motives (cited per item)**:
  - **B-1 (packet defect)**: v1 §3.4 (L95–L97) asserted `|direct − double| ≤ 1` per cell with no branch qualifier. T1 branch fails structurally on every cell (independent raw-`math.ceil` 20-cell recount: T1 ten cells delta ∈ {+63,+64}, 10/10 violate; T2 ten cells ∈ {−1,0}, 10/10 pass). Structural proof: with `x = f·1024·H`, `direct(t) − double = (ceil(2x) − 2·ceil(x)) + (128 − t)` and `ceil(2x) − 2·ceil(x) ∈ {−1,0}` always, so T1 is always {+63,+64} and T2 always {−1,0}, independent of H/f values — no second path via a different H/f set exists.
  - **B-2 (internal contradiction)**: v1 §3.2/§3.5/L7 already priced tag-dilution ≈ +60 bit (`B_T(T1) = 2144` vs `B_T(T2) = 2208`, exactly 64 apart; §3.5's own `2·1036+64 = 2136` vs `2208` surplus 72), yet §3.4 imposed a pure-ceil ≤1-bit assertion on the T1 comparison that contains the 64-bit dilution gap. Implementation (`budget2048.py` L33–L50) and hand vectors (2199/2135/2072/+63; T2 2071/−1) match the v1 literal — **no engineering defect**.
  - **B-3 (promotion double-lock)**: v1 §8 (L147) tripped STOP; v1 AC-10 requires zero blocking comments for promotion, so nothing under v1 is promotable.
- **Repair quota note**: the EXPLORE single engineering repair quota was unspent under v1 but **inapplicable** to this defect (v1 Non-Goals bars threshold/formula changes; v1 §10 limits the helper to §3 identities; v1 §15 T-4 allows only the preregistered correction under unchanged inputs/thresholds). The only compliant path is packet revision + fresh authorization — this v2 file. The unused engineering quota transfers to this v2 packet's own T-1 execution; it was not spent by the v1 STOP.
- **Frozen antecedents (read, never re-verified here)**: `m0_realframe_runner.py:101-106` + STAGE0_PACKET §16 (I-TOTAL / I-LEAK / I-BUDGET / I-GATE / I-SHAPE, C-1/C-2/C-3 machine checks in `accounting_identities.py`); JOINT-PRICING-R2 §5.3(a) MARGINAL (N=1024 nominal 1100 fits by 4; +20% 1319 excess 215); Stage-0 per-plane independent KILL; superframe KILL (M0-2M eval-region only); C-track `STRUCTURALLY_INCOMPLETE_KILL` (§5.2 K-C2, R2 + 6×40/240 partition + dual caps 1800/10800 + descriptive unit-price U_mean 51.0 s/block at α=0); five-source M0 / five-capture ser / plane-structure fence context (§13).
- **Derived-arithmetic anchors (NON-MEASUREMENT — recomputation targets only, never verdict inputs)**: N doubling → slope 84–85 ⇒ 168–170 bit/0.1f; tag dilution nominal-side ≈ +60 bit (illustration `2·1036+64 = 2136` vs linear-extrapolation budget 2208, surplus 72, **as the R-B+T1 paired number — see §3.5**); `1.2·2136 = 2563` vs 2208 excess **355** (same pairing caveat); cure-+20% f-gain **≥ ~14%** (interval recomputed in §5/K-B3).

---

## §0 Goal / Non-Goals / Impact Scope / Classification

### Goal

Establish a **self-consistent budget calibre for N=2048** and pass a pure-arithmetic feasibility gate answering exactly one question: **under N=2048, how does the leakage-budget structure scale with N and tag dilution, and — with zero polarization-gain evidence — how far are the nominal and +20%-fallback points from budget, per tag branch?** This packet contains **no polarization-gain claim**; the gain gate belongs to a later independent synthesis-sweep packet.

### Non-Goals

- No code/decoder run of any kind; no contact with real frames / `.ttbin` / `rows.json` / bundles / `(a,b)` arrays / raw data of any kind (§2).
- No FER / efficiency / leakage / f / SKR / key / method figure or claim; no statement that N=2048 is feasible or infeasible beyond the no-gain-baseline margin structure (§11).
- No void-baseline reference, no ranking, no joint table (forbidden-token gate §9).
- No reopening of: Stage-0 KILL / JOINT MARGINAL / superframe KILL / C-track KILL / U1 / M3C / M3D / M2 (§12).
- No new `f` grid, no backoff redefinition, no threshold change, no data-role change. In particular: **no relaxation of any gate threshold to 64** (§3.4/§3.7 — forbidden because it would swallow the dilution signal).
- No modification of any frozen packet, any existing `workspace/` root, `results/`, `comparison_bench/outputs_comparison/`, `docs/NOW.md`, `docs/decision-log.md`, `docs/troubleshooting.md`, `openspec/`, `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`.
- No commit, no push.

### Impact Scope

- **Written by this stage**: this packet (already written by the planner); at Pre-EXECUTE, one frozen scoped manifest (§10: one small budget-recalc helper + its fake test, reusing `accounting_identities.py` by reference); on execution, all outputs inside one fresh additive root `workspace/n2048b_<new-uuid8>` (§6). Nothing else.
- **Read-only inputs**: none for content (§2 — pure arithmetic from transcribed closed-packet constants; files govern nothing here because no file is opened).
- **Untouched**: `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/outputs_comparison/`, every existing `workspace/` root (any v1 partial root, if created, is retained, never overwritten), all frozen packets, `docs/NOW.md`, `docs/decision-log.md`, `docs/troubleshooting.md`, `openspec/`, `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`.

### §0.1 Track classification: EXPLORE — confirmed against `AGENTS.md` §1.2 (all five)

1. **Synthetic / already-approved non-sensitive input**: arithmetic only over transcribed closed-packet constants (§2: five H values carried from JOINT-PRICING-R2 §2.1 text, f anchors f₀=1.3 / f₁=1.56); no new channel statistic, no sensitive input.
2. **Fresh additive root or no-write probe**: execution (when granted) writes only to one fresh additive root `workspace/n2048b_<new-uuid8>`; the derivation itself is a no-write probe until then. No existing root is touched.
3. **Bounded and reversible**: one process, ≤300 s, ≤1 GiB, deterministic seeds (no RNG needed; ceil arithmetic only); deleting the fresh root fully reverses the stage.
4. **No claim**: output is a budget-calibre derivation + paired headroom table + one mechanical decision word under the §11 ceiling; no FER/SKR/qualification/promotion/publication figure (§11).
5. **No destructive overwrite or new user-facing external action**: no overwrite path, no network, no commit/push.

**Escalation trigger**: the moment real data, a real decoder/construction call, a route-closing threshold, a publication number, or a destructive output is needed → **STOP** and escalate to DECIDE. Calling the frozen `accounting_identities.py` shape as a fake-test reference does not trigger escalation; opening any data file does.

---

## §1 Frozen question (answerable in one shot)

With the N=1024 authoritative accounting (`TOTAL = ceil(f·1024·H)` tag-inclusive; budget 1104; leak-budget 1040; single 64-bit tag) carried as the consistency anchor, derive the N=2048 budget calibre per explicit tag branch, recompute nominal (f₀=1.3) and +20%-fallback (f₁=1.56, backoff-inside-ceil) headrooms **paired within each branch**, and close with one mechanical decision word (§5): `CALIBRE-OK`, `AMBIGUOUS`, or `KILL`.

Scheme-C lineage note: verdict TOTALs flow from the decomposition identity alone (§3.1 `double` lineage); ceil-order is a once-global tag-free lemma pre-check (§3.4), never a per-cell verdict input.

---

## §2 Frozen input list (no file opened for content)

No file is opened for content at any step. The arithmetic placeholders are transcribed from closed-packet text (mismatch against the cited text = STOP, §8):

| # | Constant | Value | Provenance (text reference, not a file open) |
|---|---|---|---|
| H-1 | H(A\|B) CQ-20a | 0.79089947 | JOINT-PRICING-R2 §2.1 |
| H-2 | H(A\|B) CQ-20b | 0.81957888 | JOINT-PRICING-R2 §2.1 |
| H-3 | H(A\|B) CQ-J21a | 0.79837921 | JOINT-PRICING-R2 §2.1 |
| H-4 | H(A\|B) CQ-J21b | 0.82351165 | JOINT-PRICING-R2 §2.1 |
| H-5 | H(A\|B) CQ-J21c (M0 baseline; drives §5) | 0.82567853 | JOINT-PRICING-R2 §2.1 |
| F-0 | nominal efficiency anchor | f₀ = 1.3 | JOINT-PRICING-R2 §3 item 9 |
| F-1 | +20% fallback anchor (backoff-inside-ceil) | f₁ = 1.2·f₀ = 1.56 | JOINT-PRICING-R2 §4 semantics |
| B-0 | N=1024 total budget | 1104 | STAGE0 §16 I-BUDGET |
| B-1 | N=1024 leak budget | 1040 (= 1104−64) | STAGE0 §16 I-BUDGET |
| T-0 | tag size | 64 bit | STAGE0 §16 I-LEAK/I-GATE |

Scope: Scope-A `H(A|B)` primary only (ten-plane basis commensurate with Stage-0/JOINT). No Scope-B pricing here; no scope choice is made for any construction.

---

## §3 Frozen formulas (Scheme-C revision of v1 §3; Q1–Q4 as machine-recomputable identities)

### §3.0 What changed vs v1 (revision map; the operative text is §§3.1–3.7 below)

- v1 §3.4 computed a per-cell mixed quantity `direct(t) − double` (one tag deduction on the left, two on the right) and gated `≤ 1` on every branch — the B-1/B-2 defect. This v2 **retires that per-cell gate entirely**.
- Three quantities are now defined separately with disjoint roles: (i) verdict lineage = decomposition identity (§3.1); (ii) ceil-order = once-global tag-free lemma (§3.4); (iii) tag-dilution gap = standalone non-gating column (§3.4/`gap_tag`). The old mixed difference **SHALL NOT gate and SHALL NOT appear in any verdict column** (§3.7).
- K-B1/K-B2/K-B3 criteria, thresholds and provenance are **unchanged**; only the execution path is re-routed through (i)+(ii) (§5).

### §3.1 Q1 — N=2048 tag-inclusive TOTAL definition (per branch; the sole verdict lineage)

Let `L₁₀₂₄(f,H) = M₁₀₂₄(f,H) − 64` be the N=1024 leak, with `M₁₀₂₄(f,H) = ceil(f·1024·H)` the tag-inclusive total (I-TOTAL). Syndrome scales linearly with N; tag is added per branch:

- `L₂₀₄₈(f,H) = 2 · L₁₀₂₄(f,H)` (exact integer doubling; this `double` lineage is the verdict input).
- `TOTAL₂₀₄₈(f,H;t) = L₂₀₄₈(f,H) + t`, where `t` is the branch tag-bit count (§3.3).
- Leak form: `LEAK₂₀₄₈(f,H) = TOTAL₂₀₄₈ − t = L₂₀₄₈` (I-LEAK shape at N=2048; C-1/C-2/C-3 shape anchor).

Verdict TOTALs use this decomposition identity **by definition**. No per-cell `direct − double` difference gates any verdict cell.

### §3.2 Q2 — budget_2048 definition rules (candidates; K-B1 adjudicates; unchanged from v1)

- **R-A (structured / tag-explicit)**: `B_L(N) = (N/1024)·1040`; `B_T(N;t) = B_L(N) + t`. At N=1024, t=64 ⇒ B_L=1040, B_T=1104 (reproduces both numbers). At N=2048: B_L=2080; T1 (t=64) ⇒ B_T=2144; T2 (t=128) ⇒ B_T=2208.
- **R-B (naive total-scaling)**: `B_T(N) = (N/1024)·1104`. At N=1024 ⇒ 1104 (total only; leak decomposition unchecked). At N=2048 ⇒ B_T=2208 for any t. Decomposition `B_T − t` gives 2144 (t=64, ≠2080, 64-bit inconsistency) or 2080 (t=128, consistent — collapses to R-A-T2).

The §3.5 mixed-pair illustration (`2136` vs `2208`, surplus 72) is the **R-B+T1 paired number**, carried only as an arithmetic cross-check, never as a verdict input. Verdicts use strictly paired comparisons (§3.6).

### §3.3 Q4 — tag branches including parametric T3 (no silent assumption)

- **T1 — single 64-bit tag per N=2048 block** (full tag dilution): t=64. `B_T=2080+64=2144` (under R-A). `TOTAL = L₂₀₄₈+64`.
- **T2 — two 64-bit tags** (one per 1024 chunk / per wire-frame): t=128. `B_T=2080+128=2208` (under R-A; identical to R-B total). `TOTAL = L₂₀₄₈+128`.
- **T3 — parametric**: t=64·k for integer k≥1 (cable/frame-structure-dependent; k chosen only by wiring evidence, never assumed). `B_T(k)=2080+64k`, `TOTAL(k)=L₂₀₄₈+64k`. Headroom is k-invariant under R-A pairing (`D_T(k) = 2080 − L₂₀₄₈ = D_L` for every k); T3 needs no numeric pick in this packet. T3 inherits the same pairing discipline as T1/T2 (§3.6/§3.7): its total may only be compared against its own same-k budget.

### §3.4 Ceil-order as a once-global tag-free lemma (demoted; replaces v1 §3.4 gate)

Define the tag-free pure-ceil quantity (no `t` anywhere):

- `delta_pure(f,H) = ceil(f·2048·H) − 2·ceil(f·1024·H)`.
- **Lemma**: `delta_pure(f,H) ∈ {−1, 0}` for all real f·H (pure ceil-doubling; proof: write `x = f·1024·H = n + θ`; `θ = 0` ⇒ 0; `θ ∈ (0,0.5]` ⇒ −1; `θ ∈ (0.5,1)` ⇒ 0).
- **Global check (once, not per verdict cell)**: computed over the 10 (source × f-point) syndrome pairs (H-1…H-5 × f₀/f₁); assert `|delta_pure| ≤ 1` on all 10; violation = STOP (§8). This gate applies **only** to the same-tag-count / tag-free comparison. It never sees `t` and never judges dilution.
- **Tag-dilution gap (standalone, non-gating)**: `gap_tag(t) = 128 − t` (equivalently `64·(2−k)` for t=64k): +64 for T1, 0 for T2, `128−64k` for T3. Carried in its own table column as an informative record of the branch tag offset. **No threshold is applied to it; it does not gate.**
- The retired v1 quantity `direct(t) − double = delta_pure + gap_tag(t)` fuses the two effects above. Fusing them and then judging `≤ 1` is **forbidden**: the fused difference SHALL NOT gate, SHALL NOT appear in any verdict column, and SHALL NOT be reintroduced under a renamed column.
- **Threshold-relaxation ban**: revising any gate to `≤ 64` (or any dilution-sized threshold) is **forbidden**. A 64-bit gate would swallow exactly the dilution signal this packet prices separately, letting K-B2/K-B3 false-pass under a wrong pairing. Violation = packet violation = STOP (§8).

### §3.5 Derived-arithmetic cross-checks (labeled NON-MEASUREMENT; unchanged from v1)

Recomputed (not assumed): slope per 0.1f at N=1024 ≈ 0.1·1024·H ≈ 84–85 bit (H≈0.82–0.83); at N=2048 ≈ 168–170 bit (tolerance ±2 for ceil). Mixed-pair illustration: with `L₁₀₂₄≈1036`, `2·1036+64=2136` vs `2208` surplus 72; `1.2·2136=2563` vs `2208` excess 355. These reproduce the closed derived anchors and validate the arithmetic path only.

### §3.6 Q3 — paired gates (verdict-bearing; cross-branch pairing FORBIDDEN; unchanged rule, Scheme-C lineage)

Per branch, with total and budget from the **same** t (T3: same k):

- Total gate: fit ⟺ `TOTAL₂₀₄₈(f,H;t) ≤ B_T(t)`; headroom `D_T(t) = B_T(t) − TOTAL₂₀₄₈(t)`; excess `E_T(t) = −D_T(t)`.
- Leak gate: fit ⟺ `L₂₀₄₈ ≤ 2080`; headroom `D_L = 2080 − L₂₀₄₈` (t-invariant; equal across T1/T2/T3(k) by construction — the script asserts equality, mirroring I-GATE).
- Invariance: `D_T(T1) = D_T(T2) = D_L` whenever R-A pairs are used (cost and budget shift by the same 64 bits); likewise `D_T(k) = D_L` for every T3 k. Comparing a T1 total against a T2 budget, a T3(k) total against any other k′ budget, or an R-B total against an R-A-T1 budget is a category error and SHALL NOT appear in any verdict column.

### §3.7 Allowed vs forbidden comparisons (normative inventory)

- **Allowed to gate verdicts**: `TOTAL_double(t)` vs `B_T(t)` same-t (K-B2); `L₂₀₄₈` vs `2080` (K-B2 leak form); `B_T(t) − t = 2080` decomposition (K-B1); `g_req` on LEAK only (K-B3); global `|delta_pure| ≤ 1` tag-free pre-check (§3.4 STOP only, not a verdict input).
- **Allowed as non-gating records**: `gap_tag(t)` column; slope cross-checks (§3.5); the R-B+T1 mixed-pair illustration labeled as such.
- **Forbidden everywhere in verdict columns**: any cross-t / cross-k total-vs-budget cell; any cell computed from the fused `direct(t) − double` difference; any gate with a dilution-sized threshold (≤64 or equivalent). Presence of any forbidden cell = STOP (§8).

---

## §4 Frozen evaluation grid (no sweep)

Per H-1…H-5 × per surviving branch (T1/T2 numeric; T3 symbolic at parametric k) × two points (f₀ nominal, f₁ +20% backoff-inside-ceil): 20 numeric cells + T3 symbolic invariance + global lemma record + slope cross-checks. No other f, no other H, no ranking, no joint table.

---

## §5 Kill conditions (mechanical; criteria, thresholds and provenance unchanged from v1; execution path re-routed per Scheme C)

Single overall decision word (§5.4) fed by K-B1 → K-B2 → K-B3 in order; any KILL short-circuits to `KILL`. Execution-path note: K-B1/K-B2/K-B3 consume only decomposition-lineage numbers (§3.1) plus the §3.4 global lemma as a STOP pre-check; no per-cell `direct − double` value enters any gate.

- **K-B1 — calibre self-consistency gate (MAIN GATE)**: each candidate rule+branch pair must satisfy (a) N=1024 back-substitution `B_T=1104 ∧ B_L=1040` at t=64 (provenance: STAGE0 §16 I-BUDGET; `m0_realframe_runner.py:101-106`), and (b) N=2048 decomposition `B_T(t) − t = 2080` (provenance: linear leak scaling §3.2). R-B+T1 fails (b) (2144≠2080) ⇒ that pair is dead. **If no pair survives (a)∧(b) ⇒ packet verdict `KILL` (calibre not self-consistent; all downstream comparison invalid).**
- **K-B2 — tag-dilution gate (nominal headroom sign across surviving branches)**: let `D_nom(t) = B_T(t) − TOTAL₂₀₄₈(f₀,H-5;t)` (M0-baseline source drives; all five reported). If surviving branches give inconsistent signs (one surplus, one overspend) ⇒ verdict `AMBIGUOUS`, manual adjudication required, no machine word beyond that. If all surviving branches strictly negative ⇒ verdict `KILL`. (Expected derived anchor, non-binding: R-A-T1/T2 both ≈ +8-bit thin surplus — sign-consistent; the packet recomputes exactly.)
- **K-B3 — gain-gap quantification gate**: compute per surviving branch the f-gain needed to cure the +20% overrun, `g_req(t) = 1 − 2080 / L₂₀₄₈(f₁,H)` (exact via ceil recomputation; total-form equivalent by §3.6). Output the interval across H-1…H-5 × surviving branches **explicitly labeled derived arithmetic (non-measurement)** for the later sweep packet's gain-gate threshold. Expected anchor (non-binding): ≈14–17% (closed ≥~14% anchor sits inside). K-B3 never KILLs by itself; it sets the numeric bar the later sweep must clear. `g_req` is computed on tag-free LEAK and needs no tag-branch correction under Scheme C.

### §5.4 Verdict vocabulary (closed; exactly one word published; unchanged)

`CALIBRE-OK` (≥1 pair passes K-B1; K-B2 sign-consistent non-negative nominal; K-B3 interval delivered) · `AMBIGUOUS` (K-B2 sign split) · `KILL` (K-B1 total failure or K-B2 all-negative nominal). No other word. `CALIBRE-OK` licenses only the later sweep packet's threshold-setting; it claims no feasibility, no gain, no method.

---

## §6 Execution root and budget (for the granted run only)

Fresh additive root `workspace/n2048b_<new-uuid8>` only — distinct from any v1 partial root, which (if created) is retained, never overwritten, never reused. One process, ≤300 s, ≤1 GiB, no RNG. No overwrite of anything outside the fresh root. Pre-EXECUTE verifies target-root absence (§9.1). This packet's freezing itself wrote only this file.

---

## §7 Machine artifacts and recomputable columns (for the granted run; Scheme-C column set)

`BUDGET2048_TABLE.csv` columns (exact): `source,H,f_point,branch,t,B_T,B_L,TOTAL,LEAK,D_T,D_L,gap_tag,slope_check`. No `ceil_order_delta` column and no fused `direct − double` column exist in this table. `gap_tag` is the §3.4 informative record (no gate). Plus `BUDGET2048_LEMMA.json`: the 10 tag-free `delta_pure` values with the global `|·| ≤ 1` assertion record. Plus `BUDGET2048_VERDICT.json`: `{rule_branch_survival, D_nom_per_branch, g_req_interval, verdict_word}`. T3 appears as symbolic rows (formula + k-invariance assertion, no numeric pick). Reviewer hand-recomputes ≥1 row per branch (JR-02 analogue, §9).

---

## §8 Stop rules (mechanical; Scheme-C trigger set)

STOP (no verdict) on: transcribed-constant mismatch vs §2 text; global lemma violation (`|delta_pure| > 1` on any of the 10 pairs); leak-gate/total-gate disagreement within a pair; any cross-branch (cross-t / cross-k) cell in a verdict column; any fused-difference column smuggled into verdict inputs; any dilution-sized gate threshold (≤64 or equivalent); any file open outside §2 (there is none — any open is a violation); any forbidden token in outputs (§9); any attempt to contact real data/decoder.

---

## §9 Acceptance criteria (numbered; machine-recheckable)

- **AC-01** Back-substitution: R-A at N=1024 reproduces B_T=1104 ∧ B_L=1040 (exact integers). Fail ⇒ K-B1 KILL.
- **AC-02** Decomposition: every surviving N=2048 pair satisfies B_T(t)−t=2080 (exact). R-B+T1 demonstrably fails and is excluded.
- **AC-03** Paired-only verdicts: every headroom/excess verdict cell pairs total and budget from the same t (T3: same k); no cross-branch cell exists in verdict columns; no fused-difference column exists in verdict inputs (grep-audited against the §7 column set).
- **AC-04** Invariance: D_T(T1)=D_T(T2)=D_L per (source,f) under surviving R-A pairs, plus D_T(k)=D_L for T3 symbolic (exact integers/formula). **Must be re-emitted and re-asserted inside the v2 T-2 full table; v1 partial vectors do not count.**
- **AC-05** Slope cross-checks: ΔTOTAL per 0.1f within 84–85±2 (N=1024 lineage) and 168–170±2 (N=2048 recomputed), labeled derived, recorded against the single stated `double` lineage. **Must be re-emitted inside the v2 run; v1 partial vectors do not count.**
- **AC-06** Single mechanical word from §5.4 only; no feasibility/gain/method sentence outside the §11 ceiling block.
- **AC-07** §11 claim-ceiling block present verbatim in the result record; batch evidence never promoted above it.
- **AC-08** Forbidden-token machine sweep passes on all outputs (quoted list here is the pattern source, not usage): `0.098260`, `f_eff`, `f_super`, `HDC`, `Layered-Binary`, `ranking`, `合表`, `10/240`, `35/35`. Quoted pattern lines in the packet/result-config are exempt by exact-line allowlist; any other occurrence FAILs.
- **AC-09** Pre-EXECUTE checklist recorded (§9.1) with explicit grant; FAIL blocks execution.
- **AC-10** Independent batch-end review (T-4/D-4) passes with no blocking comment before any promotion; FAIL blocks promotion.

### §9.1 Pre-EXECUTE checklist (FAIL blocks; NB-1 loop clarified)

Intended branch `formal-ir-v72p1-addendum-clean`; scoped manifest frozen (§10); scientific contract above unchanged except the enacted §3.4/§7/§8 Scheme-C diff explicitly listed; explicit user authorization citing §14 lineage; target root `workspace/n2048b_<new-uuid8>` absent (old v1 root, if any, retained untouched); focused fake-test vectors frozen with zero data contact; forbidden-token pattern loaded.

NB-1 clarification (test-green loop): T-1 **is** the packet's own test execution — Pre-EXECUTE "tests green" does **not** require T-1 to have already run. It requires (a) historical/smoke reference tests already green in the environment (zero data contact) and (b) the v2 T-1 vectors frozen and loadable. T-1 green is produced by execution, then checked at T-4.

### §9.2 Reusable vs must-recompute (AC inventory)

- **Reusable without recomputation (re-verify transcription per §8; re-assert same values on rerun)**: AC-01 back-substitution integers (1104/1040); H-1…H-5 + f₀/f₁ transcription values; JOINT anchors (1100 surplus 4 / 1319 excess 215); §3.5 slope-illustration arithmetic narrative; §11 ceiling verbatim; AC-06/AC-07/AC-08 machinery.
- **Must recompute under v2 (first emission; v1 partials never count as PASS)**: global lemma record (10 `delta_pure` values); full §7 table (20 numeric cells + T3 symbolic + `gap_tag`); AC-03 grep audit against the new column set; AC-04 invariance; AC-05 slopes; T-3 `g_req` interval + §5.4 word; AC-09 fresh Pre-EXECUTE record; AC-10 fresh batch-end review (the v1 independent review does not transfer).

### §9.3 STOP-batch citation warning (normative)

The v1 batch STOP-tripped at T-1 with only single-hand vectors emitted (including an ≈ +8-bit thin-surplus-shaped hand vector). **That partial vector is not a headroom conclusion, not thin-surplus evidence, and SHALL NOT be cited as any branch's `D_nom`, surplus, or feasibility signal.** Only the v2 T-2 full-table `D_nom(t)` per surviving branch counts. Any citation of the v1 single-hand D vector as a result = packet violation.

---

## §10 Scoped manifest (frozen at Pre-EXECUTE, not rewritten here)

At most: one `budget2048.py` helper (revised §3 identities only — decomposition lineage + global tag-free lemma + `gap_tag` record; allowed-input gate: no file open — constants passed as literals from §2) + one fake test (back-substitution vectors AC-01/AC-02 + global lemma 10-pair vectors + slope vectors; **no per-cell fused-difference vectors**) + reuse of `accounting_identities.py` C-1/C-2/C-3 shape by reference (read-only). No decoder, no I/O, no bundle reader.

---

## §11 Claim ceiling (verbatim block; result record must carry it word-for-word)

> N2048-BUDGET-RECALC reports pure arithmetic under a no-polarization-gain baseline only: per-branch headroom structure at N=2048 and the derived f-gain interval needed to cure the +20% overrun. It claims no polarization gain, no construction, no decoding, no FER, no efficiency, no leakage measurement, no f measurement, no feasibility or infeasibility of N=2048, no method comparison, and no publication number. Numbers labeled derived arithmetic are recomputation targets, not measurements. Any use beyond setting the later sweep packet's gain-gate threshold requires a new DECIDE packet and explicit authorization.

---

## §12 Non-reopening list (carried; not decided here)

Stage-0 per-plane KILL (scope: frozen ten per-plane-independent allocations on that f grid + budget only); JOINT-PRICING-R2 MARGINAL §5.3(a) (terminal; both numbers always co-cited — nominal 1100 surplus 4 and +20% 1319 excess 215 — no solo-nominal citation); superframe KILL (M0-2M eval-region sequences only; `S_a`/`S_spread` are context, never clearance); C-track STRUCTURALLY_INCOMPLETE_KILL (R2 same 6×40/240 partition + dual caps 1800/10800 + descriptive unit-price U_mean 51.0 s/block at α=0 only — never cited as proxy-infeasible or channel-stationary); `FLAG=False` (non-detection under α=0 only, never honesty proof); five-source M0 / ser 0.2386–0.2543 / plane-structure fence (zero co-error + popcount{0,1}+1.0, detection limit ~1e-6, mandatory qualifier); U1 ceiling as context (q is dispersion-equivalent, non-measured; ~24.6 bit/superframe is context, never clearance); M3C / M3D / M2 untouched; void baselines (including HDC / Layered-Binary void forms) never baselines; `0.098260` never a measurement; 51.0 s never throughput. This packet asserts neither N=2048 feasibility nor infeasibility.

---

## §13 Provenance (closed facts carried as constraints)

TOTAL含tag + budget 1104 + leak-budget 1040 (single 64-bit tag, N=1024) from `m0_realframe_runner.py:101-106` + STAGE0 §16; C-1/C-2/C-3 present in `accounting_identities.py`; JOINT nominal 1100 surplus 4 / +20% 1319 excess 215; derived N=2048 anchors (§3.5) as non-measurement.

---

## §14 Authorization (main-thread explanation + budget-cap restatement suffice)

Per main-thread direction under the user 2026-09-29 continuous-advance grant, the C-track `STRUCTURALLY_INCOMPLETE_KILL` verdict routes the program to the B-synthesis rail automatically, whose first frozen step is this budget-calibre re-derivation gate. Budget caps restated: N=1024 B_T=1104 / B_L=1040 (single 64-bit tag); N=2048 caps are derived candidates under §3.2, authoritative only for pairs surviving K-B1. The main thread decided on 2026-09-29 to enact Scheme C (this v2 packet); the user continuous-advance authorization plus the decision-tree cutover constitutes the execution authorization for this EXPLORE packet's T-1…T-4 arithmetic run (subject to the §9.1 Pre-EXECUTE record). **This packet authorizes no real-frame contact, no real decode/construction call, no DECIDE packet, no commit, and no push.**

---

## §15 Tasks (ordered; coder-operator contracts)

- **T-1 — Global lemma + N=1024 back-substitution + fake tests (zero data contact)**: freeze §10 helper; back-substitution AC-01/AC-02 vectors; global lemma 10-pair `delta_pure` vectors (§3.4); slope §3.5 vectors. Done when fake tests green and AC-01/AC-02/lemma cells recomputed by hand on ≥1 vector each.
- **T-2 — Per-branch arithmetic (T1/T2 numeric; T3 symbolic)**: emit §7 table (20 cells + T3 symbolic + invariants + `gap_tag`); paired gates only (AC-03/AC-04); cross-branch and fused-difference cells forbidden. Done when all D_nom(t)/D_L recomputed and invariance holds exactly.
- **T-3 — Gain-gap quantification + mechanical word**: emit `g_req` interval (AC-cross H-1…H-5 × surviving branches, labeled derived) + §5.4 single word. Done when K-B1→K-B2→K-B3 chain executes in order with short-circuit honored.
- **T-4 — Independent batch-end review (D-4)**: independent thread re-checks §3 identities, §5 chain, AC-01…AC-10, §11 verbatim block, forbidden-token sweep (AC-08), output-root discipline. Pass with no blocking comment required before any promotion; FAIL blocks promotion (rework, no rerun beyond the preregistered arithmetic correction with unchanged inputs/thresholds).
