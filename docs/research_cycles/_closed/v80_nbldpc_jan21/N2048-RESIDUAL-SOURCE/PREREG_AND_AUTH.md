# N2048-RESIDUAL-SOURCE — PREREG_AND_AUTH (Frozen residual-structure packet; freeze-only, no execution)

- **Status**: FROZEN — residual-source headroom packet for the B-track N=2048 nominal structure. This freezing writes only this file; T-1…T-4 execution requires a separate Pre-EXECUTE record (§9.1) plus explicit grant and is **not** authorized here (§§6/14).
- **Succession (no supersession)**: this packet does **not** supersede `N2048-BUDGET-RECALC/PREREG_AND_AUTH_v2.md` (245 lines, sole B-track step-1 authority), `N2048-GAIN-SWEEP/PREREG_AND_AUTH.md` (sole B-track step-2 authority), `POLAR-SCALING-BOUND/PREREG_AND_AUTH.md` (208 lines, analytic-exclusion authority), or `CROSS-BATCH-AUDIT-20260929/AUDIT.md` (pass with comments / Blocking None). All four stay current for their scopes. This packet **inherits as read-only对照 only** (never as判定 inputs): (a) the v2 budget calibre (budgets, pairing, `D_nom` +8 triple-arm identity, `g_req` interval), (b) the scaling-bound对照 interval (`g_hi=0.1024 < 0.133333`, margin 0.031, three conservative biases), (c) the §11 ceiling blocks (a)+(b)+(c) verbatim (§11), (d) the full citation discipline (§12).
- **Track**: **EXPLORE** (pure arithmetic; zero decode, zero sweep, zero data contact — see §0.1).
- **Branch**: `formal-ir-v72p1-addendum-clean`. No commit, no push by anyone under this packet.

---

## §0 Goal / Non-Goals / Impact Scope / Classification

### Goal

Give the **complete nominal headroom structure at N=2048, per source** (including negative values), and answer exactly three mechanical questions: (Q1) does the N=2048 failure point sit at nominal or at fallback; (Q2) does the thin-margin (single-tag 64-bit) discipline bite harder or lighter at N=2048; (Q3) if the failure point is confirmed at nominal, is the gain-gate question demoted to secondary (recorded explicitly as **范围收窄, not overturn**, of the prior batch conclusion).

### Non-Goals

- No decoder run of any kind; no sweep; no contact with real frames / `.ttbin` / `rows.json` / bundles / `(a,b)` arrays / raw data of any kind (§2/§8).
- No FER / efficiency / leakage / f / SKR / key / method figure or claim; no statement that N=2048 is feasible or infeasible; no publication number (§11).
- No void-baseline reference in any form, no ranking, no joint table (forbidden-token gate §9).
- No reopening of any closed item: Stage-0 KILL / JOINT MARGINAL / superframe KILL / C-track KILL / U1 / M3C / M3D / M2 (§12).
- No overturn of any closed verdict word; this packet only narrows scope or supplements structure (§5 K-R4).
- No drafting, authorizing, or pre-approving any deep-frame / fine-grid / SCL / DE / DECIDE packet.
- No change of any判据: `D_nom` definition, same-t pairing, budgets, H transcription, f anchors, tag size — all copied verbatim from v2 (§2/§3).
- No modification of any frozen packet, any existing `workspace/` root, `results/`, `comparison_bench/outputs_comparison/`, `docs/decision-log.md`, `docs/NOW.md`, `docs/troubleshooting.md`, `AGENT_PROJECT_MEMORY.md`, `AGENTS.md`, `openspec/`.
- No commit, no push.

### Impact Scope

- **Written by this stage**: this packet file only (`docs/research_cycles/N2048-RESIDUAL-SOURCE/PREREG_AND_AUTH.md`).
- **Read-only inputs for the granted run**: transcribed closed-packet constants (§2) plus read-only transcription of `workspace/n2048b_4e28c8cb/BUDGET2048_TABLE.csv` (columns `LEAK,D_T,D_L,TOTAL,B_T,B_L` only) and `BUDGET2048_VERDICT.json` (fields `D_nom_per_branch,g_req_interval` only); the scaling对照 numbers from `workspace/psb_cb0669c0/SCALE218_VERDICT.json` (fields `g_bound_interval,g_req_lower` only). GAIN TABLE `f_star`/`g_synth` two columns are permanently unreadable and shall never be opened (§8/§12).
- **Untouched**: everything listed in Non-Goals; on execution, all outputs inside one fresh additive root `workspace/n2048r_<new-uuid8>` (§6).

### §0.1 Track classification: EXPLORE — confirmed against `AGENTS.md` §1.2 (all five)

1. **Synthetic / already-approved non-sensitive input**: arithmetic only over transcribed closed-packet constants (§2: five H values, f anchors f₀=1.3 / f₁=1.56, budgets, tag=64) plus read-only transcription of already-closed machine artifacts; no new channel statistic, no sensitive input.
2. **Fresh additive root or no-write probe**: this freezing is a no-write probe except this file; execution (when granted) writes only to one fresh additive root `workspace/n2048r_<new-uuid8>`. No existing root is touched.
3. **Bounded and reversible**: one process, ≤300 s, ≤1 GiB, no RNG (ceil arithmetic only); deleting the fresh root fully reverses the stage.
4. **No claim**: output is a per-source headroom table + thin-margin predicate table + dimension-separated Δf/`g_equiv` anchors + one mechanical word under the §11 ceiling; no FER/SKR/qualification/promotion/publication figure (§11).
5. **No destructive overwrite or new user-facing external action**: no overwrite path, no network, no commit/push.

**Escalation trigger**: the moment real data, a real decoder/construction call, a route-closing threshold, a publication number, a change of scientific inputs/hypothesis/thresholds, or a destructive output is needed → **STOP** and escalate to DECIDE. Recomputing frozen ceil expressions on transcribed literals inside the fresh root does not trigger escalation; opening any data file does.

---

## §1 Frozen question (answerable in one shot)

With `D_nom(t) = B_T(t) − TOTAL_double(t)` computed per source × per side (nominal f₀=1.3, fallback f₁=1.56) × per tag branch (T1/T2 numeric, T3 symbolic) under strict same-t pairing, (Q1) is every nominal cell non-negative while every fallback cell negative (failure at fallback, gain gate stays primary) or does any nominal cell go negative (K-R4 fires, gain gate demoted to secondary as范围收窄); (Q2) what is the exact per-cell pattern of the thin-margin predicate `D ≥ 64 bit` across the four (side × branch) cells; (Q3) what absolute-Δf moves (and their ratio-form equivalents) separate each source from the +8 floor and the 64-bit line — with dimensions never mixed (K-R2).

---

## §2 Frozen input list (transcribed; mismatch = STOP)

### §2a Closed-packet constants (copied from v2 §2; no file opened for content)

| # | Constant | Value | Provenance (text reference, not a file open) |
|---|---|---|---|
| H-1 | H(A\|B) CQ-20a | 0.79089947 | JOINT-PRICING-R2 §2.1 |
| H-2 | H(A\|B) CQ-20b | 0.81957888 | JOINT-PRICING-R2 §2.1 |
| H-3 | H(A\|B) CQ-J21a | 0.79837921 | JOINT-PRICING-R2 §2.1 |
| H-4 | H(A\|B) CQ-J21b | 0.82351165 | JOINT-PRICING-R2 §2.1 |
| H-5 | H(A\|B) CQ-J21c (M0 baseline) | 0.82567853 | JOINT-PRICING-R2 §2.1 |
| F-0 | nominal efficiency anchor | f₀ = 1.3 | JOINT-PRICING-R2 §3 item 9 |
| F-1 | +20% fallback anchor (backoff-inside-ceil) | f₁ = 1.2·f₀ = 1.56 | JOINT-PRICING-R2 §4 semantics |
| B-L | N=2048 leak budget (R-A surviving) | 2080 | v2 §3.2 K-B1 survivor |
| B-T1 | N=2048 total budget, single tag t=64 | 2144 (= 2080+64) | v2 §3.2/§3.3 T1 |
| B-T2 | N=2048 total budget, two tags t=128 | 2208 (= 2080+128) | v2 §3.2/§3.3 T2 |
| T-0 | tag size | 64 bit | STAGE0 §16 I-LEAK/I-GATE |

Scope: Scope-A `H(A|B)` primary only (ten-plane basis commensurate with Stage-0/JOINT). No Scope-B pricing here.

### §2b Read-only TABLE transcription (values read from the closed root, recomputed by the executor; transcription mismatch vs the cited fields = STOP)

Read from `workspace/n2048b_4e28c8cb/BUDGET2048_TABLE.csv` columns `LEAK,D_T,D_L,TOTAL,B_T,B_L` and `BUDGET2048_VERDICT.json` fields `D_nom_per_branch,g_req_interval`:

| source | H | f₀ LEAK | f₀ D (T1=T2=L) | f₁ LEAK | f₁ D (T1=T2=L) |
|---|---|---|---|---|---|
| H-1 | 0.79089947 | 1978 | +102 | 2400 | −320 |
| H-2 | 0.81957888 | 2056 | +24 | 2492 | −412 |
| H-3 | 0.79837921 | 1998 | +82 | 2424 | −344 |
| H-4 | 0.82351165 | 2066 | +14 | 2504 | −424 |
| H-5 | 0.82567853 | 2072 | +8 | 2510 | −430 |

Invariance transcribed (executor re-asserts exactly): `D_T(T1) = D_T(T2) = D_L` in every row; T3 symbolic `D_T(k) = D_L` for every k. Verdict-field transcription: `D_nom_per_branch = {T1: 8, T2: 8, leak: 8}` (minimum over sources, H-5) and `g_req_interval = [0.133333, 0.171314]` with per-source anchors H-1 0.133333 / H-2 0.165329 / H-3 0.141914 / H-4 0.169329 / H-5 0.171314 (derived arithmetic, tag-free LEAK, non-measurement).

### §2c Scaling对照 numbers (comparison only, never判定 inputs; from `SCALE218_VERDICT.json` fields `g_bound_interval,g_req_lower`)

Union `g_bound = [−0.0769, 0.1024]` with `g_hi = 0.10236220 < 0.133333` (margin 0.031), reviewed as standing under three conservative biases (U-side extremely loose with saturated union bound / grid quantization overestimates `g_hi` / L-side remainder covered ~3–6× by the margin) — carried here as对照 context for the dimension-separated comparison in §3.5. Note: the §3.1 `I(f)` literal erratum of the scaling packet is recorded in §12/§13; execution there used the information-set reading (complement of the disclosed anchor, size N−L); any future reuse of that bound must first勘误 its §3.1, and no self-justification on the ground of a small literal difference is permitted.

---

## §3 Frozen formulas (copied lineage; Q-definitions as machine-recomputable identities)

### §3.1 Q1 — `D_nom` lineage (the sole headroom definition; v2 §3.1 decomposition lineage, unchanged)

Let `M₁₀₂₄(f,H) = ceil(f·1024·H)` (tag-inclusive total, I-TOTAL shape), `L₁₀₂₄ = M₁₀₂₄ − 64`, `L₂₀₄₈(f,H) = 2·L₁₀₂₄` (exact integer doubling; this `double` lineage is the headroom input — the word `double` here names only the v2 §3.1 decomposition lineage, never a fused per-cell difference value, see §3.7). `TOTAL_double(t) = L₂₀₄₈ + t`. Headroom: `D_nom(t) = B_T(t) − TOTAL_double(t)`; leak form `D_L = 2080 − L₂₀₄₈`; excess `E = −D`. The retired v1 fused quantity (per-cell mixed difference coupling ceil-order with the 64-bit dilution gap) SHALL NOT be recomputed as a verdict column here; only the §3.1 lineage totals enter headrooms.

### §3.2 Q2 — paired branches (T1/T2 numeric; T3 symbolic; cross-t pairing FORBIDDEN)

- **T1** (t=64): `B_T=2144`, `TOTAL=L₂₀₄₈+64`. **T2** (t=128): `B_T=2208`, `TOTAL=L₂₀₄₈+128`. Every headroom cell pairs total and budget from the **same** t.
- **T3** (parametric t=64k, k≥1 integer): `B_T(k)=2080+64k`, `TOTAL(k)=L₂₀₄₈+64k`, headroom k-invariant `D_T(k)=D_L` for every k (symbolic row, no numeric pick; k chosen only by wiring evidence, never assumed).
- Comparing a T1 total against a T2 budget (or any cross-k cell) is a category error and SHALL NOT appear in any headroom column.

### §3.3 Q3 — thin-margin predicate (mechanical, per cell)

`THIN(t, side, source) ⟺ D(side, source, t) ≥ 64` (single-tag bar). The packet emits the full 5 × 2 × 2 predicate table (source × {nominal, fallback} × {T1, T2}) plus the T3 symbolic predicate (`D_L ≥ 64`, same value for every k). No threshold relaxation (e.g. redefining the bar to absorb dilution) is permitted.

### §3.4 Reverse-direction and target-distance formulas (first-order slope anchors; executor recomputes exactly via ceil)

- Slope (tag-free LEAK): `dL₂₀₄₈/df ≈ 2048·H` (≈1619–1691 per unit f; ≈162–169 per 0.1f, matching the transcribed `slope_check` column 162/166/164/168/168). All Δf anchors below are first-order (`Δf ≈ ΔL/(2048·H)`), labeled derived, non-binding; the executor's exact ceil recomputation governs.
- Zero-headroom edge (ceil-aware): `D_L = 0 ⟺ ceil(f·1024·H) = 1104 ⟺ f ∈ (1103/(1024·H), 1104/(1024·H)]`. If the nominal-negative set is empty, T-2 records the formula plus a mechanical vacuous-set N/A (no invented target rows).
- +8-floor distance: `ΔL₈ = L₂₀₄₈(f₀,H) − 2072` (negative ⇒ f may rise; positive ⇒ f must fall). 64-bit-line distance: `ΔL₆₄ = L₂₀₄₈(f₀,H) − 2016` (same sign convention).
- Expected (non-binding) anchors: Δf to +8 floor ≈ +0.0580 (H-1) / +0.0095 (H-2) / +0.0453 (H-3) / +0.0036 (H-4) / 0 (H-5); Δf to 64-bit line ≈ +0.0235 (H-1) / −0.0238 (H-2) / +0.0110 (H-3) / −0.0296 (H-4) / −0.0331 (H-5); zero-edge upper f ≈ 1.3632 / 1.3155 / 1.3504 / 1.3092 / 1.3058 (H-1…H-5).

### §3.5 Dimension separation (normative; K-R2 enforces)

- `g_req` / `g_bound` / `g_hi` are **dimensionless ratios** (`1 − f₂/f₁` form on matched quantities; v2 `g_req = 1 − 2080/L₂₀₄₈(f₁,H)` is tag-free LEAK ratio form).
- Δf moves from §3.4 are **absolute f-unit quantities**. Direct comparison of any absolute Δf against any ratio gain is a dimension error and SHALL NOT appear anywhere (K-R2 STOP).
- The only comparable form is the ratio equivalent `g_equiv = 1 − f_target/f_ref` (dimensionless; `f_ref` stated, default f₀=1.3) or inversely `Δf_abs = g·f_ref`. Expected (non-binding) ratio anchors: H-5 8→64 needs `g_equiv ≈ 0.0255` (f_target ≈ 1.2669); H-4 →64 needs `≈ 0.0228`; H-2 →64 needs `≈ 0.0183` — each contrasted with the对照 `g_hi = 0.1024` **only** in this ratio form, labeled derived, never as a gain measurement or feasibility signal.

### §3.6 Hand-vector anchor for T-1 fake tests (zero data contact)

H-1 f₀: `1.3·1024·0.79089947 = 1052.845… → ceil 1053 → L₁₀₂₄=989 → L₂₀₄₈=1978 → TOTAL(T1)=2042 → D=2144−2042=+102`. H-5 f₀: `1.3·1024·0.82567853 = 1099.143… → ceil 1100 → L₁₀₂₄=1036 → L₂₀₄₈=2072 → TOTAL(T1)=2136 → D=2144−2136=+8`. Executor hand-recomputes ≥1 vector per branch plus the §3.4 zero-edge interval on ≥1 source.

### §3.7 Allowed vs forbidden computations (normative inventory)

- **Allowed as headroom inputs**: `TOTAL_double(t)` vs `B_T(t)` same-t (K-R1/K-R3/K-R4); `L₂₀₄₈` vs `2080` leak form; `B_T(t) − t = 2080` decomposition check; `THIN` predicate; §3.4/§3.5 distance formulas with explicit units.
- **Allowed as non-gating records**: `gap_tag`-style tag-offset column (informative, no gate); slope cross-checks (§3.4); the scaling对照 numbers (§2c) labeled对照.
- **Forbidden everywhere in headroom columns**: any cross-t / cross-k total-vs-budget cell; any fused `direct(t) − double`-difference value column or gate (the v1 defect; the bare lineage name `TOTAL_double(t)`/`double` lineage in §3.1 is the only permitted use of that token); any dilution-sized gate threshold; any absolute-Δf vs ratio-g comparison (K-R2). Presence of any forbidden cell or comparison = STOP (§8).

---

## §4 Frozen evaluation grid (no sweep)

5 sources (H-1…H-5) × 2 sides (f₀ nominal, f₁ fallback) × 2 numeric branches (T1/T2) = 20 numeric headroom cells, plus T3 symbolic invariance row, plus the 20-cell THIN predicate table, plus §3.4/§3.5 distance anchors per source. No other f, no other H, no ranking, no joint table.

---

## §5 Kill conditions (mechanical; K-R1→K-R2→K-R3→K-R4 in order)

- **K-R1 — dual-side completeness gate**: nominal AND fallback headrooms must be listed for **every** source (any source missing on either side → STOP, no word). Provenance: this packet §1/§4 grid (anti-cherry-picking).
- **K-R2 — dimension gate**: if anywhere in the batch an absolute Δf is directly compared with a ratio-form gain (`g_req`, `g_bound`, `g_hi`, `g_synth`) without the §3.5 conversion — or units are unstated on any Δf/`g_equiv` row → STOP, no word. Provenance: this packet §3.5 (dimensional homogeneity).
- **K-R3 — thin-margin gate**: the mechanical predicate `D ≥ 64 bit` is evaluated on nominal and fallback sides, per source, for T1/T2 (four cells per source) plus T3 symbolic; any missing predicate cell → STOP. The predicate table itself never collapses into the single verdict word (structure preserved). Provenance: this packet §3.3 (single-tag bar from STAGE0 §16 I-LEAK/I-GATE tag=64).
- **K-R4 — direction gate**: if ∃ source with nominal `D < 0` (in either numeric branch), the gain-gate question is demoted to secondary — recorded explicitly as **范围收窄 of the prior batch conclusion, never an overturn of any closed word**. If no nominal cell is negative, K-R4 does not fire and the gain gate stays primary; the failure point is then mechanically at fallback. Provenance: this packet §1 Q1/Q3 (direction discipline). Transcribed shape (non-binding expectation): nominal all-positive (+102/+24/+82/+14/+8), fallback all-negative (−320/−412/−344/−424/−430) ⇒ K-R4 expected not to fire; the executor recomputes and adjudicates.

### §5.4 Verdict vocabulary (closed; exactly one word published; reason recorded)

`RESIDUAL-NOMINAL-SUFFICIENT` (all nominal D ≥ 0 AND all nominal D ≥ 64 — sufficient and non-thin) · `RESIDUAL-THINNER` (all nominal D ≥ 0 BUT ∃ nominal 0 ≤ D < 64 — sufficient yet thin; the THIN table in §3.3 carries the per-source structure that one word cannot) · `RESIDUAL-NOMINAL-FAILS` (∃ nominal D < 0 — K-R4 fires; the mandatory downgrade sentence of §5 records the范围收窄) · `CONTEXT-ONLY` (downgrade path: e.g. transcription-vs-recomputation disagreement beyond ceil tolerance with pairing intact — evidence is context, no structural word). Evaluation order is FAILS → THINNER → SUFFICIENT (first match wins); K-R1/K-R2/K-R3 breaches yield STOP (no word), never CONTEXT-ONLY. No other word. Reason for adopting the suggested four-word set with ordered priority: a single word must encode the K-R4 direction outcome (Q1/Q3), while the thin-margin structure (Q2, a 20-cell predicate pattern such as nominal 2/5 pass vs fallback 0/5) is preserved in its own table and must not be lossily collapsed into that word. Expected (non-binding): `RESIDUAL-THINNER` on the transcribed shape. No word claims feasibility/infeasibility, gain existence, or method standing (§11).

---

## §6 Execution root and budget (for the granted run only)

Fresh additive root `workspace/n2048r_<new-uuid8>` only — distinct from every existing root including `workspace/n2048b_4e28c8cb/`, `workspace/n2048g_2e921d8e/`, `workspace/psb_cb0669c0/`, which are retained, never overwritten, never reused. One process, ≤300 s, ≤1 GiB, no RNG (ceil arithmetic only). No overwrite of anything outside the fresh root. Pre-EXECUTE verifies target-root absence (§9.1). This packet's freezing itself wrote only this file.

---

## §7 Machine artifacts and recomputable columns (for the granted run)

`RESIDUAL2048_TABLE.csv` columns (exact): `source,H,f_point,branch,t,B_T,B_L,TOTAL_double,LEAK,D_nom,D_L,THIN_ge64,slope_check`. (`TOTAL_double` is the §3.1 lineage name; no fused-difference column exists.) Plus T3 symbolic rows (`formula + D_T(k)=D_L invariance + THIN symbolic`). Plus `RESIDUAL2048_DISTANCES.csv` columns (exact): `source,H,L_f0,deltaL_to_plus8,deltaL_to_64,delta_f_to_plus8,delta_f_to_64,f_units,g_equiv_to_64,f_ref,g_units` (units explicit per K-R2; `g_equiv` rows present only where the §3.5 conversion is stated; vacuous-set N/A recorded for the reverse-direction zero-edge where applicable). Plus `RESIDUAL2048_VERDICT.json`: `{D_nominal_per_source,D_fallback_per_source,thin_table_summary,k_r1,k_r2,k_r3,k_r4_fired,verdict_word}`. Plus `EXPLORATION_LOG.md` (append-only; attempts, preregistered correction if used, final evidence, batch-end review). Reviewer hand-recomputes ≥1 headroom row per branch + ≥1 THIN row + ≥1 distance row + the K-R2 unit audit + the K-R4 existential check (§9).

---

## §8 Stop rules (mechanical)

STOP (no verdict) on: transcribed-constant mismatch vs §2a text (H/f/B/tag any digit); transcription mismatch vs the cited TABLE/VERDICT fields beyond exact-integer equality; any missing nominal/fallback cell (K-R1); any cross-t/cross-k cell in a headroom column; any fused-difference value column or gate; any absolute-Δf vs ratio-g comparison or unitless distance row (K-R2); any missing THIN predicate cell (K-R3); any threshold relaxation (dilution-sized bar); GAIN TABLE `f_star`/`g_synth` columns opened for any purpose; any real-data file open; any decoder call; any sweep-frame draw; any forbidden token outside its §9 allowlist line; any feasibility/infeasibility/gain-existence/method sentence outside the §11 ceiling block; any sentence overturning a closed word. STOP retains the failed attempt with command/error record; at most one preregistered engineering repair+rerun with unchanged scientific inputs/thresholds/data roles/hypothesis.

---

## §9 Acceptance criteria (numbered; machine-recheckable)

- **AC-R01** Transcription fidelity: H-1…H-5 + f₀/f₁ + B_L/B_T1/B_T2 + tag=64 exact vs §2a; budgets satisfy `B_T(t) − t = 2080` and N=1024 back-substitution shape (1104/1040 single-tag) referenced. Fail ⇒ STOP. Provenance §2a / v2 §3.2 / STAGE0 §16.
- **AC-R02** Dual-side full grid: 20 numeric cells (5 × 2 × T1/T2) + T3 symbolic present with recomputed integers; any absence ⇒ K-R1 STOP. Provenance §4/§5.
- **AC-R03** Pairing + invariance: same-t pairing only (grep-audited against the §7 column set); `D_T(T1)=D_T(T2)=D_L` exact per (source,f) plus `D_T(k)=D_L` symbolic; no fused-difference column. Fail ⇒ STOP. Provenance §3.1/§3.2/§3.7.
- **AC-R04** Thin table: 20-cell `THIN_ge64` predicate + T3 symbolic present; nominal 2/5-pass shape (H-1 +102 / H-3 +82 pass; H-2/H-4/H-5 below bar) recomputed, not assumed. Missing cell ⇒ K-R3 STOP. Provenance §3.3.
- **AC-R05** Dimension separation: every distance row carries explicit units; no absolute-Δf vs ratio-g comparison exists (unit grep audit); `g_equiv` rows state `f_ref` (default 1.3). Breach ⇒ K-R2 STOP. Provenance §3.5.
- **AC-R06** Reverse direction: zero-edge formula `(1103/(1024·H), 1104/(1024·H)]` recorded; if the nominal-negative set is empty, a mechanical vacuous-set N/A is recorded (no invented rows); expected `f_zero` anchors (1.3632/1.3155/1.3504/1.3092/1.3058) labeled derived non-binding. Provenance §3.4.
- **AC-R07** Single mechanical word from §5.4 only; K-R4 existential adjudicated; if the word is `RESIDUAL-NOMINAL-FAILS`, the mandatory范围收窄-not-overturn sentence is present. No other word. Provenance §5.
- **AC-R08** §11 ceiling blocks (a)+(b)+(c) present verbatim plus (d) extension; batch evidence never promoted above it. Provenance §11.
- **AC-R09** Forbidden-token machine sweep passes on all outputs with exact-line allowlist (quoted pattern lines in the packet/result-config carrying their limiter on the same line are exempt; any other occurrence FAILs). Quoted pattern source (not usage): `0.098260`, `f_eff`, `f_super`, `HDC`, `Layered-Binary`, `ranking`, `合表`, `10/240`, `35/35`, `CALIBRE-OK`, `GAIN-TESTABLE`, `GAIN-UNTESTABLE`, `51.0`, `24.6`, `real-frame`, `.ttbin`, `rows.json`. Prior words (`CALIBRE-OK` / `GAIN-UNTESTABLE-IN-CLASS` / `SCALING-BOUND-EXCLUDES`) may appear only on lines also carrying a scope limiter (对照/继承/仅作本 scopes); `51.0` only with 描述性单价非吞吐 limiter; `24.6` only with context非clearance limiter; `real-frame`/`.ttbin`/`rows.json` only with 不接触/零接触 limiter; the fused-difference token pair only as the §3.7 banned-pattern definition. Provenance §12.
- **AC-R10** Pre-EXECUTE checklist recorded (§9.1) with explicit grant; FAIL blocks execution. Provenance §9.1.
- **AC-R11** Independent batch-end review (T-4) passes with no blocking comment before any promotion; FAIL blocks promotion. Provenance §9/T-4.

### §9.1 Pre-EXECUTE checklist (FAIL blocks)

Intended branch `formal-ir-v72p1-addendum-clean`; scoped manifest frozen (§10); scientific contract above unchanged since freezing; explicit user authorization citing §14 lineage; target root `workspace/n2048r_<new-uuid8>` absent (all existing roots retained untouched); T-1 vectors frozen (§3.6 + slope + zero-edge vectors) and loadable with zero real-data contact; forbidden-token pattern + allowlist loaded; TABLE-column readlist loaded (`LEAK,D_T,D_L,TOTAL,B_T,B_L,D_nom_per_branch,g_req_interval,g_bound_interval,g_req_lower` — GAIN `f_star`/`g_synth` columns never opened). T-1 green is produced by execution, not required before it (historical/smoke reference green + frozen vectors loadable suffice).

### §9.2 Reusable vs must-recompute (AC inventory)

- **Reusable without recomputation (re-verify transcription per §8)**: §2a constants; JOINT dual anchors (see §12); v2 `CALIBRE-OK` scope fence (see §12); GAIN citable limiters (see §12); scaling对照 interval + three biases (see §2c); §11 blocks (a)+(b)+(c) verbatim; AC-R08/AC-R09 machinery.
- **Must recompute under this packet (first emission; transcriptions never count as PASS)**: full §7 headroom table (20 cells + T3 symbolic); AC-R03 invariance; AC-R04 THIN table; AC-R05 distance rows with units + K-R2 audit; AC-R06 zero-edge adjudication; K-R1→K-R4 chain + §5.4 word; AC-R10 fresh Pre-EXECUTE record; AC-R11 fresh batch-end review (no prior review transfers).

### §9.3 Prior partial-vector citation warning (normative)

No prior hand vector (v1 ≈+8-bit vector, v2 T-1 vectors, scaling T-1 vectors) counts as any branch's `D_nom`, distance, or predicate input here. Only this packet's T-2 full-table values count. Any citation of a prior hand vector as a result = packet violation.

---

## §10 Scoped manifest (frozen at Pre-EXECUTE, not rewritten here)

At most: one `residual2048.py` helper (§3 identities only — decomposition lineage + same-t pairing + THIN predicate + §3.4/§3.5 distance calculators with unit tags; allowed-input gate: no file open for content beyond the §9.1 column readlist — constants passed as literals from §2) + one fake test (transcription vectors §2a/§2b + hand vectors §3.6 + slope vectors + zero-edge vectors + THIN branch vectors + K-R2 unit-mixing trip vectors + K-R4 existential vectors; **no real frames, no decoder vectors, no sweep vectors**) + reuse of `accounting_identities.py` C-1/C-2/C-3 shape by reference (read-only). No decoder, no sweep sampler, no I/O reader, no bundle path. Single preregistered engineering repair (harness/unit-tag fix only, unchanged scientific inputs/thresholds) permitted once per §8.

---

## §11 Claim ceiling (result record must carry it; (a)(b)(c) verbatim-inherited, (d) residual extension)

### (a) Inherited v2 block — verbatim, marked as inherited (every word identical to v2 §11 and scaling §11(a)):

> N2048-BUDGET-RECALC reports pure arithmetic under a no-polarization-gain baseline only: per-branch headroom structure at N=2048 and the derived f-gain interval needed to cure the +20% overrun. It claims no polarization gain, no construction, no decoding, no FER, no efficiency, no leakage measurement, no f measurement, no feasibility or infeasibility of N=2048, no method comparison, and no publication number. Numbers labeled derived arithmetic are recomputation targets, not measurements. Any use beyond setting the later sweep packet's gain-gate threshold requires a new DECIDE packet and explicit authorization.

### (b) Carried GAIN extension — carried as inherited context (every word identical to GAIN §11(b) / scaling §11(b)):

> N2048-GAIN-SWEEP reports synthetic testability inside a 1200 s cost class only: whether a non-circular synthetic sweep reaches the inherited 13.33% lower edge (H-5 upper edge as context). It claims no real-frame gain existence, no real decoding, no real FER/efficiency/leakage/f measurement, no N=2048 feasibility or infeasibility, no method comparison, and no publication number. Synthetic `g_synth` values are decoder-count derivations on synthetic frames, not measurements of real data. Any use beyond licensing a future DECIDE real-data packet requires a new DECIDE packet and explicit authorization.

### (c) Scaling-bound extension — carried as inherited context (every word identical to scaling §11(c)):

> POLAR-SCALING-BOUND reports an analytic / semi-analytic polarization-bound interval inside a 300 s zero-decode zero-sweep class only: whether a non-circular two-sided bound interval for the N=1024→2048 `f`-ratio gain lies below, above, or across the inherited 13.33% lower edge (H-5 upper edge as context). It claims no decoder measurement, no sweep measurement, no real-frame gain fact, no real FER/efficiency/leakage/f measurement, no N=2048 feasibility or infeasibility, no statement that the real channel has no gain, no method comparison, and no publication number. Bound `g_bound` values are closed-form derivations from frozen priors (`p_s`, N, μ interval, FER*), not measurements of any channel. Any use beyond excluding-or-not the scaling-law possibility space requires a new DECIDE packet and explicit authorization.

### (d) Residual-source extension (adds scope, weakens nothing above):

> N2048-RESIDUAL-SOURCE reports per-source nominal-vs-fallback headroom structure at N=2048 inside a 300 s zero-decode zero-sweep EXPLORE class only: the recomputed `D_nom`/`D_fallback` integers per source per tag branch, the per-cell thin-margin (`≥64 bit`) predicates, and the unit-tagged distance anchors (absolute Δf and ratio-form `g_equiv` never intercompared). It claims no decoder measurement, no sweep measurement, no real-frame gain fact, no real FER/efficiency/leakage/f measurement, no N=2048 feasibility or infeasibility, no statement about the real channel, no method comparison, and no publication number. Distance anchors are derived-arithmetic recomputation targets (first-order slope form, exact ceil recomputation governs), not measurements of any channel. Any use beyond structural context for future packets requires a new DECIDE packet and explicit authorization.

---

## §12 Non-reopening list + citation discipline (carried; not decided here)

- JOINT-PRICING-R2 MARGINAL §5.3(a) — terminal; **both numbers always co-cited: nominal 1100 surplus 4 and +20% 1319 excess 215**; no solo-nominal citation. (Attribution note, fixed here to block conflation: the `+8` thin number belongs to the N=2048 H-5 `D_nom` triple-arm identity per v2 §13 fence, while N=1024 nominal is surplus 4 per MARGINAL; the task shorthand "N=1024 +8 level" is read as the thin-margin level and both numbers above govern.)
- Stage-0 per-plane KILL — scope only: frozen ten per-plane-independent allocations on that f grid + budget only; never cited beyond that range.
- Superframe KILL — M0-2M eval-region sequences only; `S_a`/`S_spread` are context, never clearance.
- C-track `STRUCTURALLY_INCOMPLETE_KILL` — R2 same 6×40/240 partition + dual caps 1800/10800 + descriptive unit-price 51.0 s/block at α=0 only, 描述性单价非吞吐; never cited as proxy-infeasible or channel-stationary; `FLAG=False` is non-detection under α=0 only, never honesty proof.
- U1 ceiling as context — q is dispersion-equivalent, non-measured; ~24.6 bit/superframe is context非clearance, never clearance.
- M3C / M3D / M2 untouched by this packet.
- Void baselines (including void forms of named methods) never baselines.
- `0.098260` never a measurement (pattern-source line, exempt).
- v2 `CALIBRE-OK` means calibre self-consistency + nominal sign-consistent non-negative + interval delivered **only** — not N=2048 feasible, not B-track passed, not gain obtained;仅作本 scopes对照引用, never emitted as this packet's output (AC-R09).
- GAIN `GAIN-UNTESTABLE-IN-CLASS` means this cost class / synthetic conditions only — not N=2048 infeasible, not B-track terminated, not gain-nonexistent;仅作本 scopes对照引用, never emitted as this packet's output (AC-R09).
- Scaling `SCALING-BOUND-EXCLUDES` means the scaling-law possibility space fails the inherited lower edge inside that 300 s zero-decode zero-sweep class **only** — not real-channel no-gain, not N=2048 infeasible, not B-track terminated, not gain-nonexistent, not scaling-law falsified;仅作本 scopes对照引用, never emitted as this packet's output (AC-R09).
- `g_synth` (e.g. H-1 0.041667) never a real gain, 非真实增益对照引用 only; H-5 zero never a zero-gain proof, 禁作零增益证明; GAIN TABLE `f_star`/`g_synth` two columns permanently unreadable, 永久禁读.
- `1.20/1.15` anchors always carry 经验首过网格量化、非真FER证明 limiter, never cited bare.
- Scaling N1 note: that packet's §3.1 `I(f)` wording deviates from its executed information-set reading (complement of the disclosed anchor, size N−L; the literal reading would void the bound to single-sided); this packet performs no bound computation and no repair — any future bound reuse must first勘误 that §3.1, and no self-justification on the ground of a small literal difference is permitted.
- v1 hand vector permanently banned (see §9.3).

---

## §13 Provenance + fences (carried as constraints)

TOTAL含tag + budget 1104 + leak-budget 1040 (single 64-bit tag, N=1024) from `m0_realframe_runner.py:101-106` + STAGE0 §16; v2 calibre anchors from `workspace/n2048b_4e28c8cb/` (R-A@N=1024 `B_T=1104`∧`B_L=1040`; JOINT dual anchors; 10-pair tag-free lemma; paired budgets R-A `B_L=2080` / T1 `B_T=2144` / T2 `B_T=2208`; `D_nom` +8恒等×3 arms; `g_req` interval §2b). **Fences (must inherit)**: v2 `CALIBRE-OK` fence (§12); GAIN BATCH_END_REVIEW citable form + grid-quantization + empirical-first-pass limiters (§12); scaling对照 interval + three conservative biases + N1–N6 review notes (§2c/§12); `D_nom` +8 shall never be cited as a thin-surplus conclusion; `g_req` shall never be cited as a measurement or achieved gain; the v1 ≈+8-bit hand vector shall never be cited for any purpose.

---

## §14 Authorization (main-thread explanation + budget-cap restatement suffice — thin form)

Per the user 2026-09-29 continuous-advance grant and the post-`SCALING-BOUND-EXCLUDES` residual-structure review need (the scale bound closed the four audit-listed paths inside its cost class; the remaining open structure is the per-source nominal headroom at N=2048), the frozen step is this residual-source packet. Budget caps restated: N=1024 B_T=1104 / B_L=1040 (single 64-bit tag); N=2048 R-A survivor caps B_L=2080 / T1 B_T=2144 / T2 B_T=2208; gain bar `g_req`∈[0.133333,0.171314] (derived, tag-free LEAK); execution wall 300 s single process, pure arithmetic, zero decode, zero sweep. **This freezing authorizes the packet text only; T-1…T-4 execution needs a separate Pre-EXECUTE record plus explicit grant. This packet authorizes no real-data contact, no real decode/construction call, no sweep, no DECIDE packet, no deep-frame / fine-grid / SCL / DE experiment, no commit, and no push.**

---

## §15 Tasks (ordered; coder-operator contracts for the granted run)

- **T-1 — Input transcription fidelity + fake tests (zero data contact)**: freeze §10 helper interface; transcribe §2a/§2b/§2c literals with mismatch-STOP; hand vectors §3.6 (≥1 per branch) + slope vectors + zero-edge vectors + THIN branch vectors + K-R2 unit-mixing trip vectors + K-R4 existential vectors; fake tests green. Done when AC-R01 vectors recomputed by hand on ≥1 row each and the §9.1 column readlist is loaded.
- **T-2 — Dual-side full-grid recomputation (T1/T2 numeric; T3 symbolic)**: emit §7 `RESIDUAL2048_TABLE.csv` (20 cells + T3 symbolic + invariants + THIN predicates) and `RESIDUAL2048_DISTANCES.csv` (unit-tagged §3.4/§3.5 rows; vacuous-set N/A where applicable); paired cells only (AC-R02/AC-R03/AC-R04/AC-R05/AC-R06); cross-t cells, fused-difference cells, and unitless comparisons forbidden. Done when all `D_nom`/`D_fallback`/THIN/distance rows recomputed and invariance holds exactly.
- **T-3 — Kill-chain adjudication + mechanical word**: run K-R1→K-R2→K-R3→K-R4 in order with short-circuit honored; emit `RESIDUAL2048_VERDICT.json` with the §5.4 single word (+ mandatory范围收窄 sentence iff `RESIDUAL-NOMINAL-FAILS`). Done when AC-R07 adjudicated with the existential check recomputed.
- **T-4 — Independent batch-end review**: independent thread re-checks §3 identities, §5 chain, AC-R01…AC-R11, §11 (a)+(b)+(c) verbatim + (d), forbidden-token sweep with allowlist (AC-R09), output-root discipline. Pass with no blocking comment required before any promotion; FAIL blocks promotion (rework only; no rerun beyond the one preregistered engineering repair with unchanged inputs/thresholds).
