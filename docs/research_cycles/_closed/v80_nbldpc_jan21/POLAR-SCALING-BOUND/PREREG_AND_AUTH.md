# POLAR-SCALING-BOUND — PREREG_AND_AUTH (Frozen analytic-exclusion packet; zero decode, zero sweep)

- **Status**: FROZEN — analytic-exclusion packet for the B-track gain question. Authorizes only EXPLORE analytic work T-1…T-4 in one fresh additive root and nothing else (§§6/14). Operator records the Pre-EXECUTE checklist (§9.1) before T-1. **This file is planning text only; no script or test is executed by freezing it.**
- **Succession (no supersession)**: this packet does **not** supersede `N2048-BUDGET-RECALC/PREREG_AND_AUTH_v2.md` (245 lines, sole B-track step-1 authority), `N2048-GAIN-SWEEP/PREREG_AND_AUTH.md` (191 lines, sole B-track step-2 authority), or `CROSS-BATCH-AUDIT-20260929/AUDIT.md` (115 lines, pass with comments / Blocking None). All three stay current for their scopes. This packet **inherits** only: (a) the `g_req` interval + threshold provenance (§2, verbatim values, no change), (b) the §11 claim-ceiling block (a) verbatim (§11a), (c) the B-track step-2 measurement record as frozen transcribed constants (§2, read-only, never an input to the bound), (d) the citation discipline (§12). It enacts the audit core conclusion that the analytic bound is the only seconds-scale path that may be frozen first, and it **does not** draft, authorize, or pre-approve any deep-frame / fine-grid / SCL / DE packet (audit: those are new scientific hypotheses and shall not be auto-initiated by an agent).
- **Track**: **EXPLORE** (pure analytic; zero decode, zero sweep, zero data contact — see §0.1).
- **Branch**: `formal-ir-v72p1-addendum-clean`. No commit, no push by the operator.

---

## §0 Goal / Non-Goals / Impact Scope / Classification

### Goal

With **analytic / semi-analytic polarization finite-length bounds only (no decoder run, no sweep)**, decide within a seconds-scale wall whether the `f`-ratio gain `g_req` lower edge **0.133333** set by v2 can be physically possible under the polarization scaling law when N doubles 1024→2048 at fixed target FER. Output exactly one mechanical word (§5.4): `SCALING-BOUND-EXCLUDES` vs `SCALING-BOUND-REQUIRES` vs `SCALING-BOUND-INDETERMINATE` (or `CONTEXT-ONLY` on the downgrade paths). **This packet claims no real-frame gain fact and no N=2048 feasibility conclusion of either sign** (§11).

### Non-Goals

- No decoder run of any kind; no sweep; no contact with real frames / `.ttbin` / `rows.json` / bundles / `(a,b)` arrays / raw data of any kind (§2/§8).
- No FER / efficiency / leakage / f / SKR / key / method figure or claim about real data; no N=2048 feasible/infeasible assertion; no publication number (§11).
- No void-baseline reference (HDC / Layered-Binary in any form), no ranking, no joint table (forbidden-token gate §9).
- No reopening of: Stage-0 KILL / JOINT MARGINAL / superframe KILL / C-track `STRUCTURALLY_INCOMPLETE_KILL` / U1 / M3C / M3D / M2 (§12).
- No re-run of B-track v1 / v2 / GAIN any execution; no threshold change to the inherited `g_req` interval; no redefinition of `g_req`; no backoff redefinition.
- No reading of the analytic result as "no gain on the real channel" (§8/§11 — prohibited sentence).
- No drafting, authorizing, or pre-approving any deep-frame / fine-grid / SCL / DE experiment packet.
- No modification of any frozen packet, any existing `workspace/` root, `results/`, `comparison_bench/outputs_comparison/`, `docs/NOW.md`, `docs/decision-log.md`, `docs/troubleshooting.md`, `openspec/`, `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`.
- No commit, no push.

### Impact Scope

- **Written by this stage**: this packet (already written by the planner); at Pre-EXECUTE, one frozen scoped manifest (§10); on execution, all outputs inside one fresh additive root `workspace/psb_<new-uuid8>` (§6). Nothing else.
- **Read-only inputs**: none for content beyond transcribed closed-packet constants (§2 — `g_req` interval, five H values, B-track step-2 `f*`/`g_synth` anchors, audit scaling expectation, wall-death fence; files govern nothing here because no file is opened for content).
- **Untouched**: `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/outputs_comparison/`, every existing `workspace/` root (including `workspace/n2048b_4e28c8cb/` and `workspace/n2048g_2e921d8e/` — retained, never overwritten, never reused), all frozen packets, `docs/NOW.md`, `docs/decision-log.md`, `docs/troubleshooting.md`, `openspec/`, `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`.

### §0.1 Track classification: EXPLORE — confirmed against `AGENTS.md` §1.2 (all five)

1. **Synthetic / already-approved non-sensitive input**: arithmetic only over transcribed closed-packet constants (§2: five H values, f anchors, `g_req` interval, B-track step-2 `f*` anchors as comparison targets only, audit scaling expectation as a to-be-tested expectation, frozen `μ` interval from literature-slot); no new channel statistic, no sensitive input.
2. **Fresh additive root or no-write probe**: execution (when granted) writes only to one fresh additive root `workspace/psb_<new-uuid8>`; the derivation itself is a no-write probe until then. No existing root is touched.
3. **Bounded and reversible**: one process, hard wall **WALL=300 s**, ≤1 GiB, no RNG (closed-form arithmetic only; any deterministic evaluation index needs no seed); deleting the fresh root fully reverses the stage.
4. **No claim**: output is an analytic `g_bound` interval derivation + one mechanical word under the §11 ceiling; no FER/SKR/qualification/promotion/publication figure about real data (§11).
5. **No destructive overwrite or new user-facing external action**: no overwrite path, no network, no commit/push.

**Escalation trigger**: the moment real frames, a real decoder/construction call on real data, a real-N=2048 verification, a literature check that fails and would require an external dependency as a claim input, a route-closing threshold, a publication number, or a destructive output is needed → **STOP** and return to the main thread. Evaluating frozen closed-form bound expressions on transcribed literals inside the fresh root does not trigger escalation; opening any real-data file does; contacting any external source beyond recording a citable reference slot does (§8).

---

## §1 Frozen question (answerable in one shot)

With the v2 `g_req` interval carried as the **unchanged numeric bar** (§2) and the B-track step-2 synthetic result carried as a **comparison target only (never a bound input)** (§3), can a **non-circular analytic / semi-analytic polarization finite-length bound** evaluated at N∈{1024,2048} over the frozen `μ` interval produce a two-sided `f`-ratio-gain interval `g_bound` whose position relative to the lower edge 0.133333 mechanically yields one closed-vocabulary word (§5.4) under the §11 ceiling, via the K-S1→K-S2→K-S3 chain (§5)?

---

## §2 Frozen input list (no file opened for content)

No file is opened for content at any step. Mismatch against the cited text = STOP (§8).

| # | Constant | Value | Provenance (text reference, not a file open) |
|---|---|---|---|
| H-1…H-5 | H(A\|B) five sources | 0.79089947 / 0.81957888 / 0.79837921 / 0.82351165 / 0.82567853 | JOINT-PRICING-R2 §2.1 (transcribed; H-1 is the PASS source, H-5 is context) |
| P-S | BSC crossovers solved from `h2(p_s)=H_target` | H-1 p_s≈0.23752459 / H-5 p_s≈0.25929359 (recomputed by executor from H literals; mismatch beyond 1e-6 = STOP) | N2048-GAIN-SWEEP T-4 review recheck-3/recheck-5 (transcribed cross-check, not a sweep input) |
| F-0/F-1 | efficiency anchors (pricing context only) | f₀=1.3 / f₁=1.56 (=1.2·f₀, backoff-inside-ceil) | JOINT-PRICING-R2 §3 item 9 / §4 semantics |
| G-INT | **gain-gate interval (UNCHANGED from v2, no edit)** | **[0.133333, 0.171314]**, i.e. **[13.33%, 17.13%]**; lower H-1 loosest, upper H-5 tightest | v2 §5/K-B3 + v2 T-3 fresh root `workspace/n2048b_4e28c8cb/` `BUDGET2048_VERDICT.json`; formula `g_req = 1 − 2080/L₂₀₄₈(f₁,H)` **derived arithmetic, non-measurement, tag-free LEAK**; per-source anchors H-1 0.133333 / H-2 0.165329 / H-3 0.141914 / H-4 0.169329 / H-5 0.171314 |
| G-SYN | B-track step-2 measured record (comparison target only, **never a bound input**) | `g_synth(H-1)=0.041667` from grid-quantized `f*_1024=1.20` [0/300@1.20; 4/300@1.15] / `f*_2048=1.15` [0/300], 6-point f-grid step 0.05, 300 synth frames/point, empirical FER*≤1e-3 first-pass, BSC(p_s)+Bhattacharyya DESIGN_P 0.25+LLR-SC; H-5 `g=0.0` context only; word `GAIN-UNTESTABLE-IN-CLASS` (this cost class / synthetic conditions only) | `N2048-GAIN-SWEEP/PREREG_AND_AUTH.md` + `workspace/n2048g_2e921d8e/BATCH_END_REVIEW.md` (citable form + N1/N3/N4 limiters carried) |
| MU-EXP | audit magnitude reference (**to-be-tested expectation, non-measurement, non-theorem**) | polarization scaling μ≈3.6–4 at doubling ⇒ gap shrink ~16% ⇒ `g≈0.027` | `CROSS-BATCH-AUDIT-20260929/AUDIT.md` core-conclusion § (derived expectation, not a measurement, not a literature theorem); **this packet writes it as the expectation under test, never as a known conclusion**; its relation to the literature must be discharged by the executor with a verifiable citation or demoted to context (§3/§5) |
| MU | frozen scaling-exponent input interval | **μ∈[3.6, 4.0]** (interval, not a point; frozen here; no T-3 adjustment) | frozen here (§3.3 — literature slot; executor supplies the citable closed-form reference or K-S1 demotes) |
| FER* | analytic target | **FER*≤1e-3** (same numeric gate as the sweep first-pass rule, applied here to bound expressions, not to decoder counts) | frozen here, inherited numeric value from GAIN §3.1 for comparability |
| WALL | this packet's execution wall | **300 s single process**, pure analytic (**zero decode, zero sweep**) | frozen here (§4/§6); Pre-EXECUTE re-asserts; inherits the three-wall-deaths lesson (M3C 5280 / A-attempt-2 3600 zero-落盘 / proxy-R2-seg-0 1800) as cost discipline, not as recomputed inputs |
| TOL | consistency tolerance (frozen here) | **Δ_f=0.10** absolute in f units, applied at H-1 at both N (§5 K-S3) | frozen here (§3.2/§5 — reason: exceeds one grid quantum 0.05 yet stays below the 0.16 f-distance from 1.20 to the 0.133333 bar, so the check is non-vacuous and discriminating) |

**Lower-vs-upper meaning (frozen, inherited shape)**: reaching the **lower edge (13.33%, H-1)** means even the loosest source's cure-bar is met in the bound; the **upper edge (17.13%, H-5)** is carried as context. **This packet gates EXCLUDES/REQUIRES on the lower edge only**, because v2 K-B3's closed ≥~14% anchor sits inside the interval and the lower edge is its minimal non-vacuous bar. Reason recorded; threshold values unchanged.

---

## §3 Bound selection, two-sided analysis, and non-circularity (frozen; T-1 enacts, K-S1/K-S3 adjudicate)

### §3.1 Selected bound pair (the only EXCLUDES-eligible construction)

- **Upper side (achievability) U**: Bhattacharyya union bound for polar SC, `P_ub(N,f) = Σ_{i∈I(f)} Z_i`, with `Z_i` from the frozen Bhattacharyya recursion at the channel crossover `p_s` (transcribed §2 P-S literals; design-p = channel-matched `p_s`, explicitly **not** GAIN's DESIGN_P 0.25 — no sweep constructor imported). `I(f)` is the analytic disclosed set of size `L(N,f)=2·(ceil(f·1024·H)−64)`-lineage at N=2048 / `ceil(f·1024·H)−64`-lineage at N=1024 (same decomposition shape as v2 §3.1, evaluated as integers, no decoder). If `P_ub(N,f) ≤ FER*` then the true `f*` lies at or below `f` ⇒ **upper bound on `f*_N`**.
- **Lower side (converse) L**: BSC meta-converse (Polyanskiy-Poor-Verdú form) evaluated at blocklength N with code size from the same `L(N,f)` (rate `R(f)=1−L(N,f)/N`-lineage). If `P_lb(N,f) > FER*` then the true `f*` lies strictly above `f` ⇒ **lower bound on `f*_N`**. The executor instantiates one citable closed form (meta-converse or sphere-packing form with explicit constants); the citation slot is frozen in the T-1 manifest.
- **Scaling interpolator S**: finite-length scaling projection `g_scale(μ) = (1 − 2^{−1/μ}) · (f_hi(1024) − 1) / f_hi(1024)` evaluated over the frozen μ interval corners {3.6, 4.0}, where `f_hi(1024)` is the **bound's own** U-side `f*` upper at N=1024 (never the sweep 1.20). S is an expectation cross-check under test (carries MU-EXP), not a second rigorous side.
- **Combination (frozen)**: per N, the bound yields `f*_N ∈ [f_lo(N), f_hi(N)]` from L/U inversion over an analytic f-scan (closed-form evaluations only). The gain interval is `g_bound = [1 − f_hi(2048)/f_lo(1024), 1 − f_lo(2048)/f_hi(1024)]` (min/max over L/U corners), widened by union with the S-corners `{g_scale(3.6), g_scale(4.0)}`: final interval = convex hull of both. K-S2 adjudicates on the **union** (most permissive to the bound, hardest to exclude — conservative against false exclusion).

### §3.2 Methodology answers (the packet's core difficulty — explicit design)

1. **What the bound bounds, and can it give a two-sided `f`-ratio interval?** The bound bounds `f*_N` at each N from both sides (U from above, L from below); the `f`-ratio gain `g` inherits a two-sided interval only when **both** sides are instantiated with explicit citable constants. **Exact conclusion: the U+L pair is two-sided-capable by construction; either side alone is single-sided and insufficient.** If the executor instantiates only one side (e.g. union bound alone, or scaling approximation alone), K-S1 fires mechanically ⇒ vocabulary collapses to `CONTEXT-ONLY`; **no `SCALING-BOUND-EXCLUDES` word may be emitted from a single-sided instantiation** (§5).
2. **Consistency check with the sweep**: the bound's own `f*` midpoints `f_mid(N)=(f_lo(N)+f_hi(N))/2` at H-1 must fall in the same order as the B-track step-2 synthetic `f*` (1.20 @1024 / 1.15 @2048) within the frozen tolerance: `|f_mid(1024)−1.20| ≤ 0.10 ∧ |f_mid(2048)−1.15| ≤ 0.10` (TOL provenance §2). If either fails, the bound and the sweep disagree on the operating order ⇒ K-S3 fires ⇒ vocabulary collapses to `CONTEXT-ONLY` (§5). The sweep numbers enter **only** this comparison, never the bound computation.
3. **Non-circularity**: the bound depends only on prior quantities — `p_s` literals (§2 P-S), N∈{1024,2048}, the frozen μ interval [3.6,4.0], FER*=1e-3, and frozen U/L closed-form constants. **The sweep `f*`/`g_synth` values, the sweep seeds, and the sweep constructor (DESIGN_P 0.25) are never inputs to any bound expression**; the T-1 manifest records a `no_sweep_input_attestation` and the T-3 entry refuses start on any freeze mismatch. Using the sweep 1.20 as the S-scale denominator is explicitly forbidden (S uses the bound's own `f_hi(1024)` instead).
4. **`μ` frozen source (three-way choice, exactly one taken)**: **(i) literature-slot interval [3.6, 4.0] — TAKEN.** Reason: preserves non-circularity (no sweep feedback) and two-sidedness (interval endpoints generate the S-corners; a point value would collapse INDETERMINATE). The executor must fill the citation slot with a verifiable reference for the BSC polar scaling exponent; if no verifiable citation is produced, the S-corners demote to context and S cannot carry an EXCLUDES word (K-S1 path). **(ii) M0-measured calibration — REJECTED**: would require real data ⇒ DECIDE escalation, not available in this EXPLORE packet. **(iii) synthetic-sweep calibration — REJECTED**: would inject sweep feedback into the bound ⇒ K-G2-style downgrade would apply (same-sourcing collapse to `CONTEXT-ONLY`); explicitly not taken. `μ` is an explicit numeric input frozen here and **shall not be adjusted at T-3** (any adjustment = STOP, §8).

---

## §4 Cost pre-arithmetic gate design (frozen; T-2 enacts, K-S1 adjudicates — 先算后测)

- **WALL restated**: single-process **300 s**, pure analytic (**zero decode, zero sweep**). Per-arm stall limit **60 s without落盘 → STOP** (same silence-is-failure shape as the inherited wall deaths, scaled to seconds-scale analytic work).
- **Pre-arithmetic formula (pure arithmetic, before any bound table is built)**: `T_pred = N_eval × t_eval_upper + T_overhead`, where `N_eval` = frozen count of closed-form bound evaluations (f-scan steps × N-points × μ-corners × U/L sides, frozen in T-1), `t_eval_upper` = frozen per-evaluation analytic upper bound from the T-1 no-write arithmetic micro-probe (≤64 closed-form evaluations in RAM, median taken, ×2 safety factor — never from 51.0 s), `T_overhead` = frozen 60 s harness margin. All three inputs frozen in T-1; T-2 substitutes numbers only.
- **Gate**: `T_pred ≤ 300 s` ⟺ proceed to T-3; `T_pred > 300 s` ⟺ mechanical **STOP** with no verdict word, evidence retained (§5/§8). No bound-table evaluation beyond the ≤64-frame micro-probe may run before this inequality is evaluated and recorded. **先算后测 is structural: T-3 is unreachable on a failing prediction.** If the pre-arithmetic already judges the evaluation plan unfinishable inside 300 s ⇒ mechanical STOP.
- **Auditable 先算后测 (audit N-C7 requirement written in)**: the executor records **monotonic `perf_counter_ns` (or equivalent nanosecond) stamps** for PRED-write, first TABLE-row write, and VERDICT-write (not wall-clock/mtime-second granularity); the required order is `t_PRED < t_TABLE_first < t_VERDICT`, and the T-3 entrypoint refuses start without a passing PRED record (code-order + stamp-order double gate). Second-granularity mtime alone does not satisfy this packet.
- **Three-deaths fence (carried as discipline)**: any plan predicting ≥1800 s, any arm silent for its stall limit, any attempt to price with 51.0 s as throughput = STOP (§8).

---

## §5 Kill conditions (mechanical; K-S1→K-S2→K-S3 in order; any downgrade short-circuits)

- **K-S1 — bound-validity gate (double-sided + cost first)**: T-2 evaluates §4 `T_pred ≤ 300 s` on frozen T-1 inputs AND T-1/T-3 shows both U and L sides instantiated with explicit citable closed-form constants plus the frozen μ interval carried unchanged. Provenance: WALL=300 s frozen here; two-sided requirement §3.1/§3.2(1). **Fail on either leg ⇒ mechanical STOP (cost leg, no verdict word) or vocabulary collapse to `CONTEXT-ONLY` (single-side leg — no EXCLUDES/REQUIRES word may be emitted).** K-S1 never emits an EXCLUDES word.
- **K-S2 — scaling-expectation gate (the only EXCLUDES-eligible gate)**: on the surviving two-sided interval, compare the final union `g_bound=[g_lo,g_hi]` against the v2 lower edge 0.133333 (tag-free LEAK provenance §2 G-INT). `g_hi < 0.133333` ⇒ `SCALING-BOUND-EXCLUDES`; `g_lo ≥ 0.133333` ⇒ `SCALING-BOUND-REQUIRES` (needs later measurement, claims nothing now); interval straddling 0.133333 ⇒ `SCALING-BOUND-INDETERMINATE`. The audit `g≈0.027` expectation is carried as the to-be-tested expectation inside the interval, never as the gate itself.
- **K-S3 — consistency gate (bound vs sweep order)**: `|f_mid(1024)−1.20| ≤ 0.10 ∧ |f_mid(2048)−1.15| ≤ 0.10` with `f_mid` from the bound alone and 1.20/1.15 the transcribed B-track step-2 anchors (empirical first-pass, grid-quantized, never true-FER proof). Provenance: BATCH_END_REVIEW citable form + TOL reason §2. **Fail ⇒ vocabulary collapses to `CONTEXT-ONLY`**; no EXCLUDES/REQUIRES word may be emitted even if K-S2 numbers reach the bar. K-S3 never emits an EXCLUDES word by itself.
- **Wall-stop rule + failure retention**: any arm exceeding WALL, any 60 s silence without落盘, any predicted-over-wall overrun attempt = STOP; failed attempt retained in the same fresh root with the failing command, exact error/traceback or stall nanosecond stamp, and the single decision needed; at most one preregistered engineering repair+rerun with unchanged scientific inputs/seeds/thresholds/data roles/hypothesis (§10); failed attempt never deleted.

### §5.4 Verdict vocabulary (closed; exactly one word published)

`SCALING-BOUND-EXCLUDES` (K-S1 pass two-sided; K-S3 pass; K-S2 `g_hi < 0.133333`) · `SCALING-BOUND-REQUIRES` (K-S1 pass; K-S3 pass; K-S2 `g_lo ≥ 0.133333` — licenses only a future measurement packet, claims nothing now) · `SCALING-BOUND-INDETERMINATE` (K-S1 pass; K-S3 pass; interval straddles 0.133333) · `CONTEXT-ONLY` (K-S1 single-side breach or citation failure, or K-S3 order breach — evidence is context, no exclusion word beyond that). No other word. No word claims real gain, real feasibility of either sign, or method standing (§11).

---

## §6 Execution root and budget (for the granted run only)

Fresh additive root `workspace/psb_<new-uuid8>` only — distinct from every existing root including `workspace/n2048b_4e28c8cb/` and `workspace/n2048g_2e921d8e/`, which are retained, never overwritten, never reused. One process, **≤300 s**, ≤1 GiB, no RNG (deterministic closed-form evaluation order). No overwrite of anything outside the fresh root. Pre-EXECUTE verifies target-root absence (§9.1). This packet's freezing itself wrote only this file.

---

## §7 Machine artifacts and recomputable columns (for the granted run)

`SCALE218_TABLE.csv` columns (exact): `H_target,p_s,N,f_scan,P_ub,P_lb,fer_target,mu_lo,mu_hi,f_star_lo,f_star_hi,g_bound_lo,g_bound_hi,t_eval_ns`. Plus `SCALE218_PRED.json`: `{N_eval,t_eval_upper,T_overhead,T_pred,wall_pass,t_pred_ns}` (K-S1 cost record with nanosecond stamp). Plus `SCALE218_PROV.json`: `{p_s,mu_interval,design_p_channel_matched,fer_target,U_formula_citation,L_formula_citation,no_sweep_input_attestation,t_prov_ns}` (K-S1/K-S3 record). Plus `SCALE218_VERDICT.json`: `{g_bound_interval,g_req_lower,g_req_upper_context,f_mid_1024,f_mid_2048,tol_check,verdict_word,t_verdict_ns}`. Reviewer hand-recomputes ≥1 `h2` inversion + ≥1 U/L row + the `T_pred` inequality + the K-S2 comparison + the K-S3 tolerance check (§9).

---

## §8 Stop rules (mechanical)

STOP (no verdict) on: transcribed-constant mismatch vs §2 text (including any `g_req` digit change or any `μ`-interval change at T-3); `T_pred` unevaluated before first bound-table evaluation beyond the micro-probe; any bound-table evaluation before K-S1 cost-pass record; `μ` adjustment at T-3; any sweep `f*`/`g_synth`/seed/DESIGN_P value entering a bound expression (redirects to `CONTEXT-ONLY` per §3/§5, further EXCLUDES words STOPped); any decoder call; any sweep-frame draw; any real-data file open; any real decode/construction call on real data; any wall exceedance or 60 s落盘 silence; any use of 51.0 s as throughput or 0.098260 as measurement; any forbidden token in outputs (§9); any sentence reading the bound as real-channel no-gain / N=2048 feasible-or-infeasible / method standing; any cross-claim sentence outside the §11 ceiling block. STOP retains the failed attempt per §5.

---

## §9 Acceptance criteria (numbered; machine-recheckable)

- **AC-S01** Threshold fidelity: `g_req` interval transcribed as [0.133333, 0.171314] with formula `1 − 2080/L₂₀₄₈(f₁,H)` labeled derived/tag-free/non-measurement; per-source five anchors exact; any digit drift ⇒ STOP. Provenance §2 G-INT.
- **AC-S02** Cost pre-gate: `SCALE218_PRED.json` exists with all three frozen inputs + `T_pred ≤ 300` evaluated before any bound-table evaluation (nanosecond-stamp + file-order + code-refusal triple-audited). Fail ⇒ STOP. Provenance §4.
- **AC-S03** Two-sided validity: `SCALE218_PROV.json` shows U + L closed forms with citation slots filled and μ interval [3.6,4.0] unchanged since freezing; single-side-only instantiation ⇒ `CONTEXT-ONLY` cap, no EXCLUDES word. Provenance §3.
- **AC-S04** Non-circularity: manifest diff shows no sweep `f*`/`g_synth`/seed/DESIGN_P value in any bound expression; S-scale uses the bound's own `f_hi(1024)`, never 1.20; `g_bound` recomputes from bound rows on ≥1 hand row. Breach ⇒ `CONTEXT-ONLY` cap. Provenance §3.
- **AC-S05** Gain-gate evaluation: union `g_bound=[g_lo,g_hi]` compared against 0.133333 only (H-5 upper edge as context-only field); K-S2 branch (EXCLUDES / REQUIRES / INDETERMINATE) recomputed on ≥1 corner. Provenance §2 G-INT / §5.
- **AC-S06** Consistency: K-S3 `|f_mid−f_sweep| ≤ 0.10` evaluated at H-1 at both N with 1.20/1.15 labeled empirical-first-pass grid-quantized (never true-FER proof); breach ⇒ `CONTEXT-ONLY` cap. Provenance §2 TOL / BATCH_END_REVIEW.
- **AC-S07** Single mechanical word from §5.4 only; no feasibility/gain-existence/method sentence outside the §11 ceiling block; in particular no "real channel has no gain" reading.
- **AC-S08** §11 claim-ceiling block present with (a) v2-inherited paragraph character-identical + (b) GAIN extension carried + (c) scaling-bound extension; batch evidence never promoted above it.
- **AC-S09** Forbidden-token machine sweep passes on all outputs (quoted list here is the pattern source, not usage): `0.098260`, `f_eff`, `f_super`, `HDC`, `Layered-Binary`, `ranking`, `合表`, `10/240`, `35/35`, `thin-surplus`, `CALIBRE-OK`, `GAIN-TESTABLE`, `GAIN-UNTESTABLE`, `direct`, `double`, `51.0`, `24.6`, `real-frame`, `真实信道`, `无增益`, `.ttbin`, `rows.json`. Quoted pattern lines in the packet/result-config are exempt by exact-line allowlist; any other occurrence FAILs. (`CALIBRE-OK` / `GAIN-TESTABLE` / `GAIN-UNTESTABLE` banned here as outputs to prevent prior-word reuse; v2/GAIN provenance discussion by packet-name reference only.)
- **AC-S10** Pre-EXECUTE checklist recorded (§9.1) with explicit grant; FAIL blocks execution.
- **AC-S11** Independent batch-end review (T-4) passes with no blocking comment before any promotion; FAIL blocks promotion.
- **AC-S12** Wall discipline: no arm exceeds 300 s; no 60 s落盘 silence; nanosecond-stamp order `t_PRED < t_TABLE_first < t_VERDICT` holds; failed attempts retained with command/error/stall record; at most one preregistered repair+rerun with unchanged inputs/thresholds. Violation ⇒ STOP.

### §9.1 Pre-EXECUTE checklist (FAIL blocks)

Intended branch `formal-ir-v72p1-addendum-clean`; scoped manifest frozen (§10); scientific contract above unchanged since freezing; explicit user authorization citing §14 lineage; target root `workspace/psb_<new-uuid8>` absent (all existing roots retained untouched); T-1 vectors frozen (h2 inversion + U/L formula slots + μ interval + T_pred formula) and loadable with zero real-data contact; forbidden-token pattern loaded; WALL timer armed (300 s kill + 60 s落盘 watchdog + `perf_counter_ns` stamping). T-1 green is produced by execution, not required before it (historical/smoke reference green + frozen vectors loadable suffice).

---

## §10 Scoped manifest (frozen at Pre-EXECUTE, not rewritten here)

At most: one `scale218.py` helper (Bhattacharyya recursion + U/L closed-form evaluators + μ-interval S projector + `g_bound` + `T_pred` calculators; allowed-input gate: no real-data open, no decoder import, no sweep sampler — H/p_s/μ literals from §2 only, T-3 entry refuses without passing PRED) + one fake test (h2 inversion vectors for H-1/H-5 + U/L hand-table vectors + S-corner vectors + `T_pred` inequality vectors + K-S2/K-S3 branch vectors; **no real frames, no decoder vectors, no sweep vectors**) + wall-timer harness (300 s kill + 60 s落盘 watchdog + `perf_counter_ns` stamping). No decoder entrypoint, no sweep sampler, no I/O reader, no bundle path. Single preregistered engineering repair (harness/stamp-probe fix only, unchanged scientific inputs/seeds/thresholds) permitted once per §5.

---

## §11 Claim ceiling (result record must carry it; (a) verbatim-inherited, (b) carried, (c) scaling-bound extension)

### (a) Inherited v2 block — verbatim, marked as inherited (every word identical to v2 §11 and GAIN §11(a)):

> N2048-BUDGET-RECALC reports pure arithmetic under a no-polarization-gain baseline only: per-branch headroom structure at N=2048 and the derived f-gain interval needed to cure the +20% overrun. It claims no polarization gain, no construction, no decoding, no FER, no efficiency, no leakage measurement, no f measurement, no feasibility or infeasibility of N=2048, no method comparison, and no publication number. Numbers labeled derived arithmetic are recomputation targets, not measurements. Any use beyond setting the later sweep packet's gain-gate threshold requires a new DECIDE packet and explicit authorization.

### (b) Carried GAIN extension — carried as inherited context (every word identical to GAIN §11(b)):

> N2048-GAIN-SWEEP reports synthetic testability inside a 1200 s cost class only: whether a non-circular synthetic sweep reaches the inherited 13.33% lower edge (H-5 upper edge as context). It claims no real-frame gain existence, no real decoding, no real FER/efficiency/leakage/f measurement, no N=2048 feasibility or infeasibility, no method comparison, and no publication number. Synthetic `g_synth` values are decoder-count derivations on synthetic frames, not measurements of real data. Any use beyond licensing a future DECIDE real-data packet requires a new DECIDE packet and explicit authorization.

### (c) Scaling-bound extension (adds scope, weakens nothing above):

> POLAR-SCALING-BOUND reports an analytic / semi-analytic polarization-bound interval inside a 300 s zero-decode zero-sweep class only: whether a non-circular two-sided bound interval for the N=1024→2048 `f`-ratio gain lies below, above, or across the inherited 13.33% lower edge (H-5 upper edge as context). It claims no decoder measurement, no sweep measurement, no real-frame gain fact, no real FER/efficiency/leakage/f measurement, no N=2048 feasibility or infeasibility, no statement that the real channel has no gain, no method comparison, and no publication number. Bound `g_bound` values are closed-form derivations from frozen priors (`p_s`, N, μ interval, FER*), not measurements of any channel. Any use beyond excluding-or-not the scaling-law possibility space requires a new DECIDE packet and explicit authorization.

---

## §12 Non-reopening list + citation discipline (carried; not decided here)

- Stage-0 KILL — scope only: frozen ten per-plane-independent allocations on that f grid + budget only; never cited beyond that range.
- JOINT-PRICING-R2 MARGINAL §5.3(a) — terminal; **both numbers always co-cited: nominal 1100 surplus 4 and +20% 1319 excess 215**; no solo-nominal citation.
- Superframe KILL — M0-2M eval-region sequences only; `S_a`/`S_spread` are context, never clearance.
- C-track `STRUCTURALLY_INCOMPLETE_KILL` — R2 same 6×40/240 partition + dual caps 1800/10800 + descriptive unit-price U_mean 51.0 s/block at α=0 only; **never cited as proxy-infeasible or channel-stationary**; `FLAG=False` is non-detection under α=0 only, never honesty proof.
- U1 ceiling as context — q is dispersion-equivalent, non-measured; ~24.6 bit/superframe is context, never clearance.
- M3C / M3D / M2 untouched by this packet.
- Void baselines (including HDC / Layered-Binary void forms) never baselines.
- `0.098260` never a measurement; `51.0 s` never throughput (descriptive unit-price only).
- v2 `CALIBRE-OK` means calibre self-consistency + nominal sign-consistent non-negative + interval delivered **only** — not N=2048 feasible, not B-track passed, not gain obtained; never emitted as this packet's output (AC-S09).
- GAIN `GAIN-UNTESTABLE-IN-CLASS` means this cost class / synthetic conditions only — not N=2048 infeasible, not B-track terminated, not gain-nonexistent; never emitted as this packet's output (AC-S09).
- `g_synth` never a real gain; H-5 zero never a zero-gain proof; TABLE `f_star`/`g_synth` two columns permanently unreadable (recompute from `f_scan`/`fer_emp` only); v1 hand vector permanently banned; audit μ≈3.6–4 expectation is a to-be-tested expectation, never a known conclusion or literature theorem until the executor discharges the citation slot.

---

## §13 Provenance + fences (carried as constraints)

TOTAL含tag + budget 1104 + leak-budget 1040 (single 64-bit tag, N=1024) from `m0_realframe_runner.py:101-106` + STAGE0 §16; v2 calibre anchors from `workspace/n2048b_4e28c8cb/` (R-A@N=1024 `B_T=1104`∧`B_L=1040`; JOINT dual anchors; 10-pair `delta_pure`∈{−1,0}; paired budgets R-A `B_L=2080` / T1 `B_T=2144` / T2 `B_T=2208`; `D_nom` +8恒等×3 arms; `g_req` interval §2 G-INT). **Fences (must inherit)**: v2 `CALIBRE-OK` fence (§12); GAIN BATCH_END_REVIEW citable form + N1 (TABLE columns unreadable) + N3 (grid-quantization limiter) + N4 (empirical 0/300 first-pass, never true-FER proof) limiters; `+8` shall never be cited as a thin-surplus conclusion; `g_req` shall never be cited as a measurement or achieved gain; the v1 ≈+8-bit hand vector shall never be cited for any purpose.

---

## §14 Authorization (main-thread explanation + budget-cap restatement suffice — thin form)

Per the user 2026-09-29 continuous-advance grant and the cross-batch audit core conclusion (B-track step-2 died by frozen assumptions, not by budget; the analytic bound is the only seconds-scale path that may be frozen first for exclusion), the next frozen step is this analytic scaling-bound exclusion packet. Budget caps restated: N=1024 B_T=1104 / B_L=1040 (single 64-bit tag); N=2048 candidate caps authoritative only for v2 K-B1 surviving pairs; gain bar `g_req`∈[0.133333,0.171314] (derived, tag-free LEAK); execution wall WALL=300 s single process, pure analytic, zero decode, zero sweep. **This packet authorizes no real-data contact, no real decode/construction call, no DECIDE packet, no deep-frame / fine-grid / SCL / DE experiment, no commit, and no push.**

---

## §15 Tasks (ordered; coder-operator contracts)

- **T-1 — Bound selection + μ freeze + non-circularity record + fake tests (zero decode, zero sweep)**: freeze §10 helper interface; solve+record BSC `p_s` for H-1/H-5 via `h2` inversion with hand vectors; freeze U/L closed forms with citation slots, channel-matched design-p, FER*=1e-3, μ interval [3.6,4.0] with literature-slot provenance, analytic f-scan size `N_eval`, `t_eval_upper` micro-probe design (≤64 closed-form evals), `T_overhead=60 s`; fake tests green on h2/U-L/S-corner/`T_pred`/K-S2/K-S3 branch vectors. Done when AC-S01/AC-S03/AC-S04 vectors recomputed by hand on ≥1 row each and `SCALE218_PROV.json` skeleton frozen.
- **T-2 — Cost pre-arithmetic gate (先算后测, no bound table)**: substitute frozen T-1 numbers into §4 `T_pred`, evaluate `≤300 s` with `perf_counter_ns` stamps, emit `SCALE218_PRED.json`. Done when AC-S02 stamp/file-order/code-refusal triple audit shows prediction before any bound-table evaluation beyond the micro-probe; fail ⇒ STOP with retained record, T-3 unreachable.
- **T-3 — Two-sided bound + mechanical word**: evaluate frozen U/L closed forms only after K-S1 cost-pass; build `SCALE218_TABLE.csv` + `SCALE218_VERDICT.json` via K-S1→K-S2→K-S3 chain with short-circuit honored (single-side ⇒ `CONTEXT-ONLY`; order breach ⇒ `CONTEXT-ONLY`; else K-S2 lower-edge comparison). Done when AC-S05/AC-S06 recomputed on ≥1 corner/row and §5.4 single word emitted under §11.
- **T-4 — Independent batch-end review**: independent thread re-checks §3 identities, μ-interval immutability, §5 chain, AC-S01…AC-S12, §11 (a)+(b)+(c) blocks, forbidden-token sweep (AC-S09), output-root discipline. Pass with no blocking comment required before any promotion; FAIL blocks promotion (rework only; no rerun beyond the one preregistered engineering repair with unchanged inputs/thresholds).
