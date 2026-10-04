# PSB-CEILING-EXTENSION — PREREG_AND_AUTH (Frozen analytic ceiling-extension packet; zero decode, zero sweep)

- **Status**: FROZEN — analytic ceiling-extension packet for the audit open question #1 (B-track H-1 grid ceiling at 1.20). Authorizes only EXPLORE analytic work T-1…T-4 in one fresh additive root and nothing else (§§6/14). Operator records the Pre-EXECUTE checklist (§9.1) before T-1. **This file is planning text only; no script or test is executed by freezing it.**
- **Succession (no supersession)**: this packet does **not** supersede `N2048-BUDGET-RECALC/PREREG_AND_AUTH_v2.md`, `N2048-GAIN-SWEEP/PREREG_AND_AUTH.md`, `CROSS-BATCH-AUDIT-20260929/AUDIT.md`, or `POLAR-SCALING-BOUND/PREREG_AND_AUTH.md` (SCALING-BOUND-EXCLUDES, batch-end review pass with comments). All four stay current for their scopes. This packet **inherits** only: (a) the `g_req` interval + threshold provenance (§2, verbatim values, no change), (b) the §11 claim-ceiling blocks (a)+(b)+(c) verbatim (§11), (c) the frozen U/L/S closed forms + μ interval + TOL + cost-gate shape from SCALING-BOUND (§§3–4, read-only formulas, never sweep-fed), (d) the citation discipline (§12). It answers only whether grid-ceiling truncation could flip the exclusion, and it **does not** draft, authorize, or pre-approve any deep-frame / fine-grid / SCL / DE / DECIDE packet.
- **Track**: **EXPLORE** (pure arithmetic; zero decode, zero sweep, zero data contact — see §0.1).
- **Branch**: `formal-ir-v72p1-addendum-clean`. No commit, no push by the operator.

---

## §0 Goal / Non-Goals / Impact Scope / Classification

### Goal

With **closed-form analytic extension only (no decoder run, no sweep, zero real data)**, extend the H-1 bound-side `f*_1024` beyond the sweep grid top 1.20 out to `f=1.40` on an analytic grid ≤0.01, recompute the two-sided `f`-ratio-gain interval `g_bound_ext`, and decide mechanically whether — even if the true optimum sat above the grid top — `g` could reach the `g_req` lower edge **0.133333**. Output exactly one mechanical word (§5.4): `CEILING-ROBUST` vs `CEILING-FRAGILE` vs `CEILING-INDETERMINATE` (or `CONTEXT-ONLY` on the downgrade path). **This packet claims no real-frame gain fact and no N=2048 feasibility conclusion of either sign** (§11).

### Non-Goals

- No decoder run of any kind; no sweep; no contact with real frames / `.ttbin` / `rows.json` / bundles / `(a,b)` arrays / raw data of any kind (§2/§8).
- No FER / efficiency / leakage / f / SKR / key / method figure or claim about real data; no N=2048 feasible/infeasible assertion; no publication number (§11).
- No void-baseline reference in any form, no ranking, no joint table (forbidden-token gate §9).
- No reopening of: Stage-0 KILL / JOINT MARGINAL / superframe KILL / C-track kill / U1 / M3C / M3D / M2 / SCALING-BOUND-EXCLUDES (§12).
- No re-run of B-track v1 / v2 / GAIN / SCALING-BOUND any execution; no threshold change to the inherited `g_req` interval; no redefinition of `g_req`; no μ-interval change at T-3.
- No reading of the extension result as "no gain on the real channel" or as a real-channel conclusion of any sign (§8/§11 — prohibited sentence).
- No drafting, authorizing, or pre-approving any deep-frame / fine-grid / SCL / DE / DECIDE experiment packet.
- No modification of any frozen packet, any existing `workspace/` root, `results/`, `comparison_bench/outputs_comparison/`, `docs/NOW.md`, `docs/decision-log.md`, `docs/troubleshooting.md`, `openspec/`, `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`.
- No commit, no push.

### Impact Scope

- **Written by this stage**: this packet (already written by the planner); at Pre-EXECUTE, one frozen scoped manifest (§10); on execution, all outputs inside one fresh additive root `workspace/psbce_<new-uuid8>` (§6). Nothing else.
- **Read-only inputs**: none for content beyond transcribed closed-packet constants (§2 — `g_req` interval, five H values, `g_hi` verdict literal, `g_synth` record, B-track step-2 `f*` anchors as comparison targets only, audit arithmetic context, wall-death fence; files govern nothing here because no file is opened for content).
- **Untouched**: `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/outputs_comparison/`, every existing `workspace/` root (including `workspace/n2048b_4e28c8cb/`, `workspace/n2048g_2e921d8e/`, and every `workspace/psb_*` root — retained, never overwritten, never reused), all frozen packets, `docs/NOW.md`, `docs/decision-log.md`, `docs/troubleshooting.md`, `openspec/`, `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`.

### §0.1 Track classification: EXPLORE — confirmed against `AGENTS.md` §1.2 (all five)

1. **Synthetic / already-approved non-sensitive input**: arithmetic only over transcribed closed-packet constants (§2: five H values, `g_req` interval, `g_hi` verdict literal, `f*` anchors as comparison targets only, audit arithmetic as context, frozen `μ` interval from literature-slot); no new channel statistic, no sensitive input.
2. **Fresh additive root or no-write probe**: execution (when granted) writes only to one fresh additive root `workspace/psbce_<new-uuid8>`; the derivation itself is a no-write probe until then. No existing root is touched.
3. **Bounded and reversible**: one process, hard wall **WALL=300 s**, ≤1 GiB, no RNG (closed-form arithmetic only; any deterministic evaluation index needs no seed); deleting the fresh root fully reverses the stage.
4. **No claim**: output is an extended analytic `g_bound_ext` interval derivation + one mechanical word under the §11 ceiling; no FER/SKR/qualification/promotion/publication figure about real data (§11).
5. **No destructive overwrite or new user-facing external action**: no overwrite path, no network, no commit/push.

**Escalation trigger**: the moment real frames, a real decoder/construction call on real or synthetic frames, a sweep-frame draw, a real-N verification, a route-closing threshold, a publication number, or a destructive output is needed → **STOP** and return to the main thread for DECIDE escalation. Evaluating frozen closed-form bound expressions on transcribed literals inside the fresh root does not trigger escalation; opening any real-data file does; invoking any decoder does (§8).

---

## §1 Frozen question (answerable in one shot)

With the v2 `g_req` interval carried as the **unchanged numeric bar** (§2), the SCALING-BOUND `g_hi=0.10236220` carried as the **pre-extension bound literal** (§2), and the B-track step-2 H-1 grid top `f*_1024=1.20` carried as a **comparison anchor only (never a bound input)** (§3), can a **non-circular closed-form extension** of the frozen U/L/S bound pair over the analytic grid (step ≤0.01, out to `f=1.40`) produce an extended two-sided gain interval `g_bound_ext` whose position relative to the lower edge 0.133333 mechanically yields one closed-vocabulary word (§5.4) under the §11 ceiling, via the K-E0→K-E1→K-E2 chain (§5)?

---

## §2 Frozen input list (no file opened for content)

No file is opened for content at any step. Mismatch against the cited text = STOP (§8).

| # | Constant | Value | Provenance (text reference, not a file open) |
|---|---|---|---|
| H-1…H-5 | H(A\|B) five sources | 0.79089947 / 0.81957888 / 0.79837921 / 0.82351165 / 0.82567853 | JOINT-PRICING-R2 §2.1 (transcribed; H-1 is the PASS source, H-5 is context) |
| P-S | BSC crossovers solved from `h2(p_s)=H_target` | H-1 p_s≈0.23752459 / H-5 p_s≈0.25929359 (recomputed by executor from H literals; mismatch beyond 1e-6 = STOP) | N2048-GAIN-SWEEP T-4 recheck-3/recheck-5 (transcribed cross-check, not a sweep input) |
| F-0/F-1 | efficiency anchors (pricing context only) | f₀=1.3 / f₁=1.56 (=1.2·f₀, backoff-inside-ceil) | JOINT-PRICING-R2 §3 item 9 / §4 semantics |
| G-INT | **gain-gate interval (UNCHANGED from v2, no edit)** | **[0.133333, 0.171314]**, i.e. **[13.33%, 17.13%]**; lower H-1 loosest, upper H-5 tightest | v2 §5/K-B3 + `workspace/n2048b_4e28c8cb/` verdict; formula `g_req = 1 − 2080/L₂₀₄₈(f₁,H)` **derived arithmetic, non-measurement, tag-free LEAK**; per-source anchors H-1 0.133333 / H-2 0.165329 / H-3 0.141914 / H-4 0.169329 / H-5 0.171314 |
| G-HI | **pre-extension bound literal (UNCHANGED, no edit)** | **g_hi=0.10236220** (H-1 union top; margin 0.133333−0.10236220≈0.031) | `SCALE218_VERDICT.json` in the SCALING-BOUND fresh root (transcribed verdict literal; triple-conservative bias carried as context) |
| G-SYN | B-track step-2 measured record (comparison target only, **never a bound input**) | `g_synth(H-1)=0.041667` from grid-quantized empirical first-pass `f*_1024=1.20` [0/300@1.20; 4/300@1.15] / `f*_2048=1.15` [0/300], 6-point f-grid step 0.05, 300 synth frames/point, empirical FER*≤1e-3 first-pass, BSC(p_s)+Bhattacharyya DESIGN_P 0.25+LLR-SC; H-5 `g=0.0` context only | `N2048-GAIN-SWEEP/PREREG_AND_AUTH.md` + BATCH_END_REVIEW citable form + N1/N3/N4 limiters carried |
| F-ANC | H-1/H-5 sweep anchors (comparison targets only) | `f*_1024=1.20` [0/300@1.20; 4/300@1.15] / `f*_2048=1.15` [0/300], always labeled empirical-first-pass grid-quantized, never true-FER proof | GAIN citable form (B-track step-2; grid ceiling at 1.20 is the question under test, not an input) |
| MU | frozen scaling-exponent input interval | **μ∈[3.6, 4.0]** (interval, not a point; frozen here; S-corner interior; no T-3 adjustment) | frozen in SCALING-BOUND §2/§3.3, carried unchanged (literature slot; pre-expected test, non-theorem) |
| FER* | analytic target | **FER*≤1e-3** (same numeric gate as the sweep first-pass rule, applied here to bound expressions, not to decoder counts) | frozen in SCALING-BOUND, carried unchanged for comparability |
| EXT | analytic extension grid (frozen here) | **step ≤0.01, range (1.20, 1.40]**, evaluated at H-1 (H-5 as context); f=1.40 cap covers the audit +2.5-step need (1.327) with margin | frozen here (§3 — covers f*_1024≥1.327 audit arithmetic with 0.073 headroom) |
| TOL | consistency tolerance (carried) | **Δ_f=0.10** absolute in f units, applied at H-1 at both N (§5 K-E2) | carried from SCALING-BOUND §2 (exceeds one grid quantum 0.05 yet stays below the 0.16 f-distance from 1.20 to the bar) |
| WALL | this packet's execution wall | **300 s single process**, pure analytic (**zero decode, zero sweep**) | frozen here (§4/§6); inherits the three-wall-deaths lesson as cost discipline |

**Lower-vs-upper meaning (frozen, inherited shape)**: reaching the **lower edge (13.33%, H-1)** means even the loosest source's cure-bar is met in the extension; the **upper edge (17.13%, H-5)** is carried as context. **This packet gates CEILING-ROBUST/FRAGILE on the lower edge only.** Reason recorded; threshold values unchanged.
**Audit arithmetic carried as context (not inputs)**: at fixed `f_2048=1.15` the bar needs `f*_1024≥1.15/(1−0.133333)≈1.327` (+2.5 sweep steps of 0.05 above 1.20); the continuous-bound max `g≈0.083<0.1333` means fine-grid resolution alone does not bridge the bar. Both are expectations under test, never gate values.

---

## §3 Extension selection, two-sided analysis, and non-circularity (frozen; T-1 enacts, K-E0/K-E2 adjudicate)

### §3.1 Selected extension (the only CEILING-word-eligible construction)

- **Upper side (achievability) U**: Bhattacharyya union bound for polar SC, `P_ub(N,f) = Σ_{i∈I(f)} Z_i`, with `Z_i` from the frozen Bhattacharyya recursion at the channel crossover `p_s` (transcribed §2 P-S literals; design-p = channel-matched `p_s`, explicitly **not** GAIN's DESIGN_P 0.25 — no sweep constructor imported). `I(f)` takes the **information-set reading** (package-literal erratum as fixed in SCALING-BOUND succession; successors apply the erratum first and shall not reinterpret). If `P_ub(N,f) ≤ FER*` then the true `f*` lies at or below `f` ⇒ **upper bound on `f*_N`**.
- **Lower side (converse) L**: BSC meta-converse (same citable closed form as SCALING-BOUND, explicit constants carried) evaluated at blocklength N with code size from the same `L(N,f)` (rate `R(f)=1−L(N,f)/N`-lineage). If `P_lb(N,f) > FER*` then the true `f*` lies strictly above `f` ⇒ **lower bound on `f*_N`**.
- **Scaling interpolator S**: finite-length scaling projection `g_scale(μ) = (1 − 2^{−1/μ}) · (f_hi(1024) − 1) / f_hi(1024)` evaluated over the frozen μ interval corners {3.6, 4.0}, where `f_hi(1024)` is the **bound's own** U-side `f*` upper at N=1024 (extended value when the extension moves it; never the sweep 1.20). S is an expectation cross-check under test (carries MU-EXP), not a second rigorous side.
- **Extension (frozen)**: per N, re-invert `f*_N ∈ [f_lo_ext(N), f_hi_ext(N)]` from L/U over the analytic f-scan (step ≤0.01, cap f=1.40, closed-form evaluations only; the (1.20,1.40] tail is the only new evaluation range). The extended gain interval is `g_bound_ext = [1 − f_hi_ext(2048)/f_lo_ext(1024), 1 − f_lo_ext(2048)/f_hi_ext(1024)]` (min/max over L/U corners), widened by union with the S-corners `{g_scale(3.6), g_scale(4.0)}`: final interval = convex hull of both. K-E1 adjudicates on the **union** (most permissive to the extension, hardest to call ROBUST — conservative against false robustness).

### §3.2 Methodology answers (explicit design)

1. **What the extension bounds, and can it move the ceiling?** The extension re-bounds `f*_N` at each N from both sides over the tail (1.20,1.40]; the `f`-ratio gain inherits a two-sided extended interval only when **both** sides are instantiated with explicit citable constants. **Exact conclusion: the U+L pair is two-sided-capable by construction; either side alone is single-sided and insufficient.** Single-side instantiation ⇒ K-E0 fires mechanically ⇒ vocabulary collapses to `CONTEXT-ONLY`; **no `CEILING-ROBUST`/`CEILING-FRAGILE` word may be emitted from a single-sided extension** (§5).
2. **Consistency check with the sweep**: the extended bound's own `f*` midpoints `f_mid_ext(N)=(f_lo_ext(N)+f_hi_ext(N))/2` at H-1 must stay in the same order as the B-track step-2 synthetic anchors (1.20 @1024 / 1.15 @2048, empirical-first-pass grid-quantized, never true-FER proof) within the frozen tolerance: `|f_mid_ext(1024)−1.20| ≤ 0.10 ∧ |f_mid_ext(2048)−1.15| ≤ 0.10` (TOL provenance §2). If either fails, the extension and the sweep disagree on the operating order ⇒ K-E2 fires ⇒ vocabulary collapses to `CONTEXT-ONLY` (§5). The sweep numbers enter **only** this comparison, never the bound computation.
3. **Non-circularity**: the extension depends only on prior quantities — `p_s` literals (§2 P-S), N∈{1024,2048}, the frozen μ interval [3.6,4.0], FER*=1e-3, frozen U/L closed-form constants, and the frozen EXT grid. **The sweep `f*`/`g_synth` values, the sweep seeds, and the sweep constructor (DESIGN_P 0.25) are never inputs to any bound expression**; the T-1 manifest records a `no_sweep_input_attestation` and the T-3 entry refuses start on any freeze mismatch. Using the sweep 1.20 as the S-scale denominator is explicitly forbidden (S uses the bound's own `f_hi_ext(1024)` instead).
4. **`μ` frozen source (three-way choice, exactly one taken)**: **(i) literature-slot interval [3.6, 4.0] — TAKEN (carried).** Reason: preserves non-circularity and two-sidedness (interval endpoints generate the S-corners). **(ii) M0-measured calibration — REJECTED**: would require real data ⇒ DECIDE escalation. **(iii) synthetic-sweep calibration — REJECTED**: would inject sweep feedback ⇒ same-sourcing collapse to `CONTEXT-ONLY`. `μ` is an explicit numeric input carried unchanged and **shall not be adjusted at T-3** (any adjustment = STOP, §8).

---

## §4 Cost pre-arithmetic gate design (frozen; T-2 enacts, K-E0 adjudicates — 先算后测)

- **WALL restated**: single-process **300 s**, pure analytic (**zero decode, zero sweep**). Per-arm stall limit **60 s without落盘 → STOP** (same silence-is-failure shape as the inherited wall deaths, scaled to seconds-scale analytic work).
- **Pre-arithmetic formula (pure arithmetic, before any extension table is built)**: `T_pred = N_eval × t_eval_upper + T_overhead`, where `N_eval` = frozen count of closed-form evaluations (extension f-steps × N-points × μ-corners × U/L sides, frozen in T-1), `t_eval_upper` = frozen per-evaluation analytic upper bound from the T-1 no-write arithmetic micro-probe (≤64 closed-form evaluations in RAM, median taken, ×2 safety factor — never from 51.0 s), `T_overhead` = frozen 60 s harness margin. All three inputs frozen in T-1; T-2 substitutes numbers only.
- **Gate**: `T_pred ≤ 300 s` ⟺ proceed to T-3; `T_pred > 300 s` ⟺ mechanical **STOP** with no verdict word, evidence retained (§5/§8). No extension-table evaluation beyond the ≤64-frame micro-probe may run before this inequality is evaluated and recorded. **先算后测 is structural: T-3 is unreachable on a failing prediction.**
- **Auditable 先算后测 (audit N-C7 requirement written in)**: the executor records **monotonic `perf_counter_ns` (or equivalent nanosecond) stamps** for PRED-write, first TABLE-row write, and VERDICT-write; the required order is `t_PRED < t_TABLE_first < t_VERDICT`, and the T-3 entrypoint refuses start without a passing PRED record (code-order + stamp-order + file-order triple gate; the entry code path rejects bound-table construction when no passing PRED exists). Second-granularity mtime alone does not satisfy this packet.
- **Three-deaths fence (carried as discipline)**: any plan predicting ≥1800 s, any arm silent for its stall limit, any attempt to price with 51.0 s as throughput = STOP (§8).

---

## §5 Kill conditions (mechanical; K-E0→K-E1→K-E2 in order; any downgrade short-circuits)

- **K-E0 — extension-validity gate (double-sided + cost first)**: T-2 evaluates §4 `T_pred ≤ 300 s` on frozen T-1 inputs AND T-1/T-3 shows both U and L sides instantiated with explicit citable closed-form constants plus the frozen μ interval carried unchanged plus the EXT grid (step ≤0.01, cap 1.40) honored. Provenance: WALL=300 s frozen here; two-sided requirement §3.1/§3.2(1). **Fail on either leg ⇒ mechanical STOP (cost leg, no verdict word) or vocabulary collapse to `CONTEXT-ONLY` (single-side leg — no CEILING word may be emitted).** K-E0 never emits a CEILING word.
- **K-E1 — ceiling gate (the only CEILING-word-eligible gate)**: on the surviving two-sided extended union `g_bound_ext=[g_lo_ext,g_hi_ext]`, compare against the v2 lower edge 0.133333 (tag-free LEAK provenance §2 G-INT). `g_hi_ext < 0.133333` ⇒ `CEILING-ROBUST` (even the extended top stays below the bar — truncation could not flip the exclusion); `g_lo_ext ≥ 0.133333` ⇒ `CEILING-FRAGILE` (the extended interval sits at/above the bar — truncation could flip); `g_lo_ext < 0.133333 ≤ g_hi_ext` ⇒ `CEILING-INDETERMINATE` (the extended interval straddles the bar). The audit `g≈0.027` expectation and the `g≈0.083` continuous max are carried as context inside the interval, never as the gate itself.
- **K-E2 — consistency gate (extension vs sweep order)**: `|f_mid_ext(1024)−1.20| ≤ 0.10 ∧ |f_mid_ext(2048)−1.15| ≤ 0.10` with `f_mid_ext` from the extension alone and 1.20/1.15 the transcribed B-track step-2 anchors (empirical first-pass, grid-quantized, never true-FER proof). Provenance: BATCH_END_REVIEW citable form + TOL reason §2. **Fail ⇒ vocabulary collapses to `CONTEXT-ONLY`**; no CEILING word may be emitted even if K-E1 numbers reach the bar. K-E2 never emits a CEILING word by itself.
- **Wall-stop rule + failure retention**: any arm exceeding WALL, any 60 s silence without落盘, any predicted-over-wall overrun attempt = STOP; failed attempt retained in the same fresh root with the failing command, exact error/traceback or stall nanosecond stamp, and the single decision needed; at most one preregistered engineering repair+rerun with unchanged scientific inputs/seeds/thresholds/data roles/hypothesis (§10); failed attempt never deleted.

### §5.4 Verdict vocabulary (closed; exactly one word published)

`CEILING-ROBUST` (K-E0 pass two-sided; K-E2 pass; K-E1 `g_hi_ext < 0.133333`) · `CEILING-FRAGILE` (K-E0 pass; K-E2 pass; K-E1 `g_lo_ext ≥ 0.133333` — truncation could flip, licenses only a future measurement packet, claims nothing now) · `CEILING-INDETERMINATE` (K-E0 pass; K-E2 pass; interval straddles 0.133333) · `CONTEXT-ONLY` (K-E0 single-side breach or citation failure, or K-E2 order breach — evidence is context, no ceiling word beyond that). No other word. No word claims real gain, real feasibility of either sign, or method standing (§11).

---

## §6 Execution root and budget (for the granted run only)

Fresh additive root `workspace/psbce_<new-uuid8>` only — distinct from every existing root including `workspace/n2048b_4e28c8cb/`, `workspace/n2048g_2e921d8e/`, and every `workspace/psb_*` root, which are retained, never overwritten, never reused. One process, **≤300 s**, ≤1 GiB, no RNG (deterministic closed-form evaluation order). No overwrite of anything outside the fresh root. Pre-EXECUTE verifies target-root absence (§9.1). This packet's freezing itself wrote only this file.

---

## §7 Machine artifacts and recomputable columns (for the granted run)

`CEIL140_TABLE.csv` columns (exact): `H_target,p_s,N,f_scan,P_ub,P_lb,fer_target,mu_lo,mu_hi,f_star_lo_ext,f_star_hi_ext,g_bound_lo_ext,g_bound_hi_ext,t_eval_ns`. Plus `CEIL140_PRED.json`: `{N_eval,t_eval_upper,T_overhead,T_pred,wall_pass,ext_grid_step,ext_f_cap,t_pred_ns}` (K-E0 cost record with nanosecond stamp). Plus `CEIL140_PROV.json`: `{p_s,mu_interval,design_p_channel_matched,fer_target,U_formula_citation,L_formula_citation,info_set_erratum_applied,no_sweep_input_attestation,t_prov_ns}` (K-E0/K-E2 record). Plus `CEIL140_VERDICT.json`: `{g_bound_ext_interval,g_req_lower,g_req_upper_context,g_hi_pre,g_synth_context,f_mid_ext_1024,f_mid_ext_2048,tol_check,verdict_word,t_verdict_ns}`. Reviewer hand-recomputes ≥1 `h2` inversion + ≥1 U/L extension row + the `T_pred` inequality + the K-E1 comparison + the K-E2 tolerance check (§9).

---

## §8 Stop rules (mechanical)

STOP (no verdict) on: transcribed-constant mismatch vs §2 text (including any `g_req` digit change, any `g_hi` digit change, any `μ`-interval change or EXT-grid change at T-3); `T_pred` unevaluated before first extension-table evaluation beyond the micro-probe; any extension-table evaluation before K-E0 cost-pass record; `μ` adjustment at T-3; any sweep `f*`/`g_synth`/seed/DESIGN_P value entering a bound expression (redirects to `CONTEXT-ONLY` per §3/§5, further CEILING words STOPped); any decoder call; any sweep-frame draw; any real-data file open; any wall exceedance or 60 s落盘 silence; any use of 51.0 s as throughput or 0.098260 as measurement; any forbidden token in outputs (§9); any sentence reading the extension as real-channel no-gain / real-channel gain / N=2048 feasible-or-infeasible / method standing; any cross-claim sentence outside the §11 ceiling block. STOP retains the failed attempt per §5.

---

## §9 Acceptance criteria (numbered; machine-recheckable)

- **AC-E01** Threshold fidelity: `g_req` interval transcribed as [0.133333, 0.171314] with formula `1 − 2080/L₂₀₄₈(f₁,H)` labeled derived/tag-free/non-measurement; per-source five anchors exact; `g_hi=0.10236220` literal exact with margin ≈0.031; any digit drift ⇒ STOP. Provenance §2 G-INT/G-HI.
- **AC-E02** Cost pre-gate: `CEIL140_PRED.json` exists with all frozen inputs + EXT grid (step ≤0.01, cap 1.40) + `T_pred ≤ 300` evaluated before any extension-table evaluation (nanosecond-stamp + file-order + code-refusal triple-audited). Fail ⇒ STOP. Provenance §4.
- **AC-E03** Two-sided validity: `CEIL140_PROV.json` shows U + L closed forms with citation slots filled, information-set erratum applied, and μ interval [3.6,4.0] unchanged since freezing; single-side-only instantiation ⇒ `CONTEXT-ONLY` cap, no CEILING word. Provenance §3.
- **AC-E04** Non-circularity: manifest diff shows no sweep `f*`/`g_synth`/seed/DESIGN_P value in any bound expression; S-scale uses the bound's own `f_hi_ext(1024)`, never 1.20; `g_bound_ext` recomputes from extension rows on ≥1 hand row. Breach ⇒ `CONTEXT-ONLY` cap. Provenance §3.
- **AC-E05** Ceiling-gate evaluation: extended union `g_bound_ext=[g_lo_ext,g_hi_ext]` compared against 0.133333 only (H-5 upper edge as context-only field); K-E1 branch (ROBUST / FRAGILE / INDETERMINATE) recomputed on ≥1 extension corner. Provenance §2 G-INT / §5.
- **AC-E06** Consistency: K-E2 `|f_mid_ext−f_sweep| ≤ 0.10` evaluated at H-1 at both N with 1.20/1.15 labeled empirical-first-pass grid-quantized (never true-FER proof); breach ⇒ `CONTEXT-ONLY` cap. Provenance §2 TOL / BATCH_END_REVIEW.
- **AC-E07** Single mechanical word from §5.4 only; no feasibility/gain-existence/method sentence outside the §11 ceiling block; in particular no real-channel reading of either sign.
- **AC-E08** §11 claim-ceiling block present with (a) v2-inherited paragraph character-identical + (b) GAIN extension carried + (c) scaling-bound extension carried + (d) ceiling-extension paragraph; batch evidence never promoted above it.
- **AC-E09** Forbidden-token machine sweep passes on all outputs (quoted list here is the pattern source, not usage): `0.098260`, `f_eff`, `f_super`, `HDC`, `Layered-Binary`, `ranking`, `合表`, `10/240`, `35/35`, `thin-surplus`, `CALIBRE-OK`, `GAIN-TESTABLE`, `GAIN-UNTESTABLE`, `SCALING-BOUND-EXCLUDES`, `SCALING-BOUND-REQUIRES`, `SCALING-BOUND-INDETERMINATE`, `direct`, `double`, `51.0`, `24.6`, `real-frame`, `真实信道`, `无增益`, `.ttbin`, `rows.json`. Quoted pattern lines in the packet/result-config are exempt by exact-line allowlist; any other occurrence FAILs. (`CALIBRE-OK` / `GAIN-*` / `SCALING-BOUND-*` banned here as outputs to prevent prior-word reuse; v2/GAIN/SCALING provenance discussion by packet-name reference only.)
- **AC-E10** Pre-EXECUTE checklist recorded (§9.1) with explicit grant; FAIL blocks execution.
- **AC-E11** Independent batch-end review (T-4) passes with no blocking comment before any promotion; FAIL blocks promotion; review grants zero threshold/method/claim elevation.
- **AC-E12** Wall discipline: no arm exceeds 300 s; no 60 s落盘 silence; nanosecond-stamp order `t_PRED < t_TABLE_first < t_VERDICT` holds; failed attempts retained with command/error/stall record; at most one preregistered repair+rerun with unchanged inputs/thresholds. Violation ⇒ STOP.

### §9.1 Pre-EXECUTE checklist (FAIL blocks)

Intended branch `formal-ir-v72p1-addendum-clean`; scoped manifest frozen (§10); scientific contract above unchanged since freezing; explicit user authorization citing §14 lineage; target root `workspace/psbce_<new-uuid8>` absent (all existing roots retained untouched); T-1 vectors frozen (h2 inversion + U/L formula slots + μ interval + EXT grid + `T_pred` formula) and loadable with zero real-data contact; forbidden-token pattern loaded; WALL timer armed (300 s kill + 60 s落盘 watchdog + `perf_counter_ns` stamping). T-1 green is produced by execution, not required before it (historical/smoke reference green + frozen vectors loadable suffice).

---

## §10 Scoped manifest (frozen at Pre-EXECUTE, not rewritten here)

At most: one `ceil140.py` helper (Bhattacharyya recursion + U/L closed-form evaluators + μ-interval S projector + extension `g_bound_ext` + `T_pred` calculators; allowed-input gate: no real-data open, no decoder import, no sweep sampler — H/p_s/μ/EXT literals from §2 only, T-3 entry refuses without passing PRED) + one fake test (h2 inversion vectors for H-1/H-5 + U/L hand-table vectors + S-corner vectors + extension-corner vectors + `T_pred` inequality vectors + K-E1/K-E2 branch vectors; **no real frames, no decoder vectors, no sweep vectors**) + wall-timer harness (300 s kill + 60 s落盘 watchdog + `perf_counter_ns` stamping). No decoder entrypoint, no sweep sampler, no I/O reader, no bundle path. Single preregistered engineering repair (harness/stamp-probe fix only, unchanged scientific inputs/seeds/thresholds) permitted once per §5.

---

## §11 Claim ceiling (result record must carry it; (a)+(b)+(c) verbatim-inherited, (d) ceiling-extension)

### (a) Inherited v2 block — verbatim, marked as inherited (every word identical to v2 §11 and GAIN §11(a) and SCALING-BOUND §11(a)):

> N2048-BUDGET-RECALC reports pure arithmetic under a no-polarization-gain baseline only: per-branch headroom structure at N=2048 and the derived f-gain interval needed to cure the +20% overrun. It claims no polarization gain, no construction, no decoding, no FER, no efficiency, no leakage measurement, no f measurement, no feasibility or infeasibility of N=2048, no method comparison, and no publication number. Numbers labeled derived arithmetic are recomputation targets, not measurements. Any use beyond setting the later sweep packet's gain-gate threshold requires a new DECIDE packet and explicit authorization.

### (b) Carried GAIN extension — carried as inherited context (every word identical to GAIN §11(b) and SCALING-BOUND §11(b)):

> N2048-GAIN-SWEEP reports synthetic testability inside a 1200 s cost class only: whether a non-circular synthetic sweep reaches the inherited 13.33% lower edge (H-5 upper edge as context). It claims no real-frame gain existence, no real decoding, no real FER/efficiency/leakage/f measurement, no N=2048 feasibility or infeasibility, no method comparison, and no publication number. Synthetic `g_synth` values are decoder-count derivations on synthetic frames, not measurements of real data. Any use beyond licensing a future DECIDE real-data packet requires a new DECIDE packet and explicit authorization.

### (c) Carried scaling-bound extension — carried as inherited context (every word identical to SCALING-BOUND §11(c)):

> POLAR-SCALING-BOUND reports an analytic / semi-analytic polarization-bound interval inside a 300 s zero-decode zero-sweep class only: whether a non-circular two-sided bound interval for the N=1024→2048 `f`-ratio gain lies below, above, or across the inherited 13.33% lower edge (H-5 upper edge as context). It claims no decoder measurement, no sweep measurement, no real-frame gain fact, no real FER/efficiency/leakage/f measurement, no N=2048 feasibility or infeasibility, no statement that the real channel has no gain, no method comparison, and no publication number. Bound `g_bound` values are closed-form derivations from frozen priors (`p_s`, N, μ interval, FER*), not measurements of any channel. Any use beyond excluding-or-not the scaling-law possibility space requires a new DECIDE packet and explicit authorization.

### (d) Ceiling-extension (adds scope, weakens nothing above):

> PSB-CEILING-EXTENSION reports an analytic tail extension inside a 300 s zero-decode zero-sweep class only: whether extending the frozen bound's H-1 `f*_1024` past the 1.20 grid top out to f=1.40 (step ≤0.01) moves the two-sided gain interval to below, at/above, or across the inherited 13.33% lower edge. It claims no decoder measurement, no sweep measurement, no real-frame gain fact, no real FER/efficiency/leakage/f measurement, no N=2048 feasibility or infeasibility, no statement about the real channel of either sign, no method comparison, and no publication number. Extended `g_bound_ext` values are closed-form derivations from frozen priors plus the frozen EXT grid, not measurements of any channel. Any use beyond answering the grid-ceiling robustness question requires a new DECIDE packet and explicit authorization.

---

## §12 Non-reopening list + citation discipline (carried; not decided here)

- Stage-0 KILL — scope only: frozen ten per-plane-independent allocations on that f grid + budget only; never cited beyond that range.
- JOINT-PRICING-R2 MARGINAL §5.3(a) — terminal; **both numbers always co-cited: nominal 1100 surplus 4 and +20% 1319 excess 215**; no solo-nominal citation.
- Superframe KILL — M0-2M eval-region sequences only; `S_a`/`S_spread` are context, never clearance.
- C-track kill — same 6×40/240 partition + dual caps 1800/10800 + descriptive unit-price 51.0 s/block at α=0 only; **never cited as proxy-infeasible or channel-stationary**; `FLAG=False` is non-detection under α=0 only, never honesty proof.
- U1 ceiling as context — q is dispersion-equivalent, non-measured; ~24.6 bit/superframe is context, never clearance.
- M3C / M3D / M2 untouched by this packet.
- Void baselines (including HDC / Layered-Binary void forms) never baselines.
- `0.098260` never a measurement; `51.0 s` never throughput (descriptive unit-price only).
- v2 calibre word means calibre self-consistency + nominal sign-consistent non-negative + interval delivered **only** — not N=2048 feasible, not B-track passed, not gain obtained; never emitted as this packet's output (AC-E09).
- GAIN word means this cost class / synthetic conditions only — not N=2048 infeasible, not B-track terminated, not gain-nonexistent; never emitted as this packet's output (AC-E09).
- SCALING word means this cost class / analytic-bound conditions only — not a real-channel verdict; never emitted as this packet's output (AC-E09).
- RESIDUAL means nominal structure only; never a clearance claim.
- `g_synth` never a real gain; H-5 zero never a zero-gain proof; TABLE `f_star`/`g_synth` two columns permanently unreadable (recompute from `f_scan`/`fer_emp` only); v1 hand vector permanently banned; 1.20/1.15 always labeled empirical-first-pass grid-quantized, never true-FER proof; audit μ≈3.6–4 expectation is a to-be-tested expectation, never a known conclusion or literature theorem until the citation slot is discharged.

---

## §13 Provenance + fences (carried as constraints)

TOTAL含tag + budget 1104 + leak-budget 1040 (single 64-bit tag, N=1024) from `m0_realframe_runner.py:101-106` + STAGE0 §16; v2 calibre anchors from `workspace/n2048b_4e28c8cb/` (R-A@N=1024 `B_T=1104`∧`B_L=1040`; JOINT dual anchors; 10-pair `delta_pure`∈{−1,0}; paired budgets R-A `B_L=2080` / T1 `B_T=2144` / T2 `B_T=2208`; `D_nom` +8恒等×3 arms; `g_req` interval §2 G-INT). **Fences (must inherit)**: v2 calibre fence (§12); GAIN BATCH_END_REVIEW citable form + N1 (TABLE columns unreadable) + N3 (grid-quantization limiter) + N4 (empirical 0/300 first-pass, never true-FER proof) limiters; SCALING-BOUND verdict literal `g_hi=0.10236220` + information-set erratum (successors apply first, no reinterpretation); `+8` shall never be cited as a thin-surplus conclusion; `g_req` shall never be cited as a measurement or achieved gain; the v1 ≈+8-bit hand vector shall never be cited for any purpose.

---

## §14 Authorization (main-thread explanation + budget-cap restatement suffice — thin form)

Per the user 2026-09-29 continuous-advance grant ("continue at least ten rounds without step-by-step approval") and the cross-batch audit open question #1 (H-1 second-step `f*_1024=1.20` sits exactly on the sweep grid top, so the true optimum may lie above it and the exclusion needs a seconds-scale analytic ceiling check), the next frozen step is this analytic ceiling-extension packet. Budget caps restated: N=1024 B_T=1104 / B_L=1040 (single 64-bit tag); N=2048 candidate caps authoritative only for v2 K-B1 surviving pairs; gain bar `g_req`∈[0.133333,0.171314] (derived, tag-free LEAK); pre-extension bound literal `g_hi=0.10236220`; execution wall WALL=300 s single process, pure analytic, zero decode, zero sweep. **This packet authorizes no real-data contact, no real decode/construction call, no sweep, no DECIDE packet, no deep-frame / fine-grid / SCL / DE experiment, no commit, and no push.**

---

## §15 Tasks (ordered; coder-operator contracts)

- **T-1 — Extension definition + μ freeze + non-circularity record + fake tests (zero decode, zero sweep)**: freeze §10 helper interface; solve+record BSC `p_s` for H-1/H-5 via `h2` inversion with hand vectors; freeze U/L closed forms with citation slots, information-set erratum applied, channel-matched design-p, FER*=1e-3, μ interval [3.6,4.0] with literature-slot provenance, EXT grid (step ≤0.01, cap 1.40), analytic f-scan size `N_eval`, `t_eval_upper` micro-probe design (≤64 closed-form evals), `T_overhead=60 s`; fake tests green on h2/U-L/S-corner/extension-corner/`T_pred`/K-E1/K-E2 branch vectors. Done when AC-E01/AC-E03/AC-E04 vectors recomputed by hand on ≥1 row each and `CEIL140_PROV.json` skeleton frozen.
- **T-2 — Cost pre-arithmetic gate (先算后测, no extension table)**: substitute frozen T-1 numbers into §4 `T_pred`, evaluate `≤300 s` with `perf_counter_ns` stamps, emit `CEIL140_PRED.json`. Done when AC-E02 stamp/file-order/code-refusal triple audit shows prediction before any extension-table evaluation beyond the micro-probe; fail ⇒ STOP with retained record, T-3 unreachable.
- **T-3 — Two-sided extension + mechanical word**: evaluate frozen U/L closed forms only after K-E0 cost-pass; build `CEIL140_TABLE.csv` + `CEIL140_VERDICT.json` via K-E0→K-E1→K-E2 chain with short-circuit honored (single-side ⇒ `CONTEXT-ONLY`; order breach ⇒ `CONTEXT-ONLY`; else K-E1 lower-edge comparison). Done when AC-E05/AC-E06 recomputed on ≥1 extension corner/row and §5.4 single word emitted under §11.
- **T-4 — Independent batch-end review**: independent thread re-checks §3 identities, μ-interval and EXT-grid immutability, §5 chain, AC-E01…AC-E12, §11 (a)+(b)+(c)+(d) blocks, forbidden-token sweep (AC-E09), output-root discipline. Pass with no blocking comment required before any promotion; FAIL blocks promotion (rework only; no rerun beyond the one preregistered engineering repair with unchanged inputs/thresholds); review grants zero elevation.
