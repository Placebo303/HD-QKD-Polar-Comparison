# FER-RESOLUTION-ANALYTIC — PREREG_AND_AUTH (Frozen 0/300-resolution analytic packet; zero decode, zero sweep)

- **Status**: FROZEN — analytic resolution packet for audit open question #2 (0/300 statistical resolution). Authorizes only EXPLORE analytic work T-1…T-4 in one fresh additive root and nothing else (§§6/14). Operator records the Pre-EXECUTE checklist (§9.1) before T-1. **This file is planning text only; no script or test is executed by freezing it.**
- **Succession (no supersession)**: this packet does **not** supersede `N2048-BUDGET-RECALC/PREREG_AND_AUTH_v2.md`, `N2048-GAIN-SWEEP/PREREG_AND_AUTH.md`, `CROSS-BATCH-AUDIT-20260929/AUDIT.md`, `POLAR-SCALING-BOUND/PREREG_AND_AUTH.md`, or `PSB-CEILING-EXTENSION/PREREG_AND_AUTH.md` (CEILING-ROBUST, batch-end review pass with comments). All five stay current for their scopes. This packet **inherits** only: (a) the `g_req` interval + threshold provenance (§2, verbatim values, no change), (b) the §11 claim-ceiling blocks (a)+(b)+(c) verbatim (§11), (c) the B-track step-2 grid record as comparison anchor only (never a bound input), (d) the citation discipline (§12). It answers only how far the 0/300 empirical first-pass is from a true-FER≤1e-3 proof, and it **does not** draft, authorize, or pre-approve any deep-frame / fine-grid / SCL / DE / DECIDE packet.
- **Track**: **EXPLORE** (pure binomial arithmetic; zero decode, zero sweep, zero data contact — see §0.1).
- **Branch**: `formal-ir-v72p1-addendum-clean`. No commit, no push by the operator.

---

## §0 Goal / Non-Goals / Impact Scope / Classification

### Goal

With **pure analytic binomial confidence bounds only (Clopper-Pearson / Wilson / rule-of-three; zero decode, zero sweep, zero real data, WALL-seconds)**, quantify how far the 0/300 empirical first-pass (FER\*≤1e-3 mechanical rule) is from a true FER≤1e-3 proof, and whether deep sampling at 3000/30000 frames within the same WALL could change the B-track second-step word. Output exactly one mechanical word (§5.4): `FER-ROBUST` vs `FER-FRAGILE` vs `FER-INDETERMINATE` (or `CONTEXT-ONLY` on the downgrade path). **This packet claims no real-frame FER fact and no N=2048 feasibility conclusion of either sign** (§11).

### Non-Goals

- No decoder run of any kind; no sweep; no contact with real frames / `.ttbin` / `rows.json` / bundles / `(a,b)` arrays / raw data of any kind (§2/§8).
- No FER / efficiency / leakage / f / SKR / key / method figure or claim about real data; no N=2048 feasible/infeasible assertion; no publication number (§11).
- No void-baseline reference in any form (void never a baseline), no ranking, no joint table (forbidden-token gate §9).
- No reopening of: Stage-0 KILL / JOINT MARGINAL / superframe KILL / C-track kill / U1 / M3C / M3D / M2 / SCALING-BOUND-EXCLUDES / CEILING-ROBUST (§12).
- No re-run of B-track v1 / v2 / GAIN / SCALING-BOUND / CEILING-EXTENSION any execution; no threshold change to the inherited `g_req` interval; no redefinition of `g_req`; no μ-interval work (μ out of scope here).
- No reading of the resolution result as a real-channel conclusion of any sign (§8/§11 — prohibited sentence).
- No drafting, authorizing, or pre-approving any deep-frame / fine-grid / SCL / DE / DECIDE experiment packet; deep-frame numbers here are analytic projections, never execution clearance.
- No modification of any frozen packet, any existing `workspace/` root, `results/`, `comparison_bench/outputs_comparison/`, `docs/NOW.md`, `docs/decision-log.md`, `docs/troubleshooting.md`, `openspec/`, `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`.
- No commit, no push.

### Impact Scope

- **Written by this stage**: this packet (already written by the planner); at Pre-EXECUTE, one frozen scoped manifest (§10); on execution, all outputs inside one fresh additive root `workspace/ferres_<new-uuid8>` (§6). Nothing else.
- **Read-only inputs**: none for content beyond transcribed closed-packet constants (§2 — `g_synth` identity, `g_req` lower edge, B-track step-2 grid record as comparison anchor only, audit deep-frame accounting as context, FER\* gate; files govern nothing here because no file is opened for content).
- **Untouched**: `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/outputs_comparison/`, every existing `workspace/` root (including `workspace/n2048b_4e28c8cb/`, `workspace/n2048g_2e921d8e/`, every `workspace/psb_*` and `workspace/psbce_*` root — retained, never overwritten, never reused), all frozen packets, `docs/NOW.md`, `docs/decision-log.md`, `docs/troubleshooting.md`, `openspec/`, `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`.

### §0.1 Track classification: EXPLORE — confirmed against `AGENTS.md` §1.2 (all five)

1. **Synthetic / already-approved non-sensitive input**: arithmetic only over transcribed closed-packet constants (§2: `g_synth` identity, `g_req` lower edge, grid record, audit accounting, FER\* gate); no new channel statistic, no sensitive input.
2. **Fresh additive root or no-write probe**: execution (when granted) writes only to one fresh additive root `workspace/ferres_<new-uuid8>`; the derivation itself is a no-write probe until then. No existing root is touched.
3. **Bounded and reversible**: one process, hard wall **WALL=300 s**, ≤1 GiB, no RNG (closed-form binomial arithmetic only; deterministic row order needs no seed); deleting the fresh root fully reverses the stage.
4. **No claim**: output is a binomial-bound derivation + one mechanical word under the §11 ceiling; no FER/SKR/qualification/promotion/publication figure about real data (§11).
5. **No destructive overwrite or new user-facing external action**: no overwrite path, no network, no commit/push.

**Escalation trigger**: the moment real frames, a real decoder/construction call on real or synthetic frames, a sweep-frame draw, a deep-frame execution, a route-closing threshold, a publication number, or a destructive output is needed → **STOP** and return to the main thread for DECIDE escalation. Evaluating frozen binomial closed forms on transcribed literals inside the fresh root does not trigger escalation; opening any real-data file does; invoking any decoder does; drawing any sweep/deep frame does (§8).

---

## §1 Frozen question (answerable in one shot)

With the B-track step-2 grid record carried as a **comparison anchor only (never a bound input)** (§2/§3), the `g_req` lower edge carried as the **unchanged numeric bar** (§2), and **binomial tail/confidence closed forms only**, does the 0/300 zero-count upper bound sit above, at/below, or across the FER\*=1e-3 gate (K-F1); do the zero-count projected bounds at 3000/30000 still leave a gap>0 to the gate (K-F2); and does threatening the B-track gate require ≥2 steps of same-direction asymmetric misclassification (K-F3) — mechanically yielding one closed-vocabulary word (§5.4) under the §11 ceiling, via the K-F1→K-F2→K-F3 chain (§5)?

---

## §2 Frozen input list (no file opened for content)

No file is opened for content at any step. Mismatch against the cited text = STOP (§8).

| # | Constant | Value | Provenance (text reference, not a file open) |
|---|---|---|---|
| G-SYN | B-track step-2 record (anchor only, **never a bound input**) | **`g_synth(H-1)=0.041667=1−1.15/1.2`** from grid-quantized empirical first-pass `f*_1024=1.20` [0/300@1.20; 4/300@1.15] / `f*_2048=1.15` [0/300], 6-point f-grid step 0.05, 300 synth frames/point, empirical FER\*≤1e-3 first-pass, BSC(p_s)+Bhattacharyya DESIGN_P 0.25+LLR-SC; H-5 `g=0.0` context only | `N2048-GAIN-SWEEP/PREREG_AND_AUTH.md` + BATCH_END_REVIEW citable form + N1/N3/N4 limiters carried |
| F-ANC | sweep anchors (comparison targets only) | `f*_1024=1.20` [0/300@1.20; 4/300@1.15] / `f*_2048=1.15` [0/300], always labeled empirical-first-pass grid-quantized, never true-FER proof | GAIN citable form (B-track step-2) |
| G-INT | **gain-gate lower edge (UNCHANGED, no edit)** | **0.133333** (H-1 loosest; upper H-5 edge as context) | v2 §5/K-B3; formula tag-free LEAK **derived arithmetic, non-measurement** |
| GAP | bar-minus-synth gap (derived identity, not a measurement) | **0.091667≈2.2 steps** (0.133333−0.041667) | arithmetic over G-SYN/G-INT literals frozen here |
| NC2 | asymmetric-correction limiter (carried, corrected form) | **N-C2 correction >2 steps (explicitly not >3 steps)** | cross-batch audit correction; carried as the K-F3 bar |
| FER* | analytic gate | **FER\*≤1e-3** (same numeric gate as the sweep first-pass rule, applied here to bound expressions, not to decoder counts) | frozen in SCALING-BOUND, carried unchanged for comparability |
| R03 | 0/300 resolution literals (frozen here) | 95% rule-of-three UB **~0.01** (=3/300); **P(0\|true 1e-3,n=300)≈0.74** (=(1−1e-3)^300) | frozen here (§3 — recomputation targets, not measurements) |
| DEEP | audit deep-frame accounting (context, **not execution clearance**) | **3000≈178 s / 30000≈696 s same-WALL feasible**; identity `T_pred=G_pts×F_per×t_frame_upper+120`, `t_frame_upper=0.0008` | cross-batch audit accounting; carried as K-F2 context only |
| WALL | this packet's execution wall | **300 s single process**, pure analytic (**zero decode, zero sweep**) | frozen here (§4/§6) |

**Lower-vs-upper meaning (frozen, inherited shape)**: the **lower edge (13.33%, H-1)** is the only gate edge in this packet; the H-5 upper edge is context. **This packet gates FER-ROBUST/FRAGILE on the lower edge only.** Threshold values unchanged.

---

## §3 Method selection, two-sided bounds, and non-circularity (frozen; T-1 enacts, K-F1/K-F2 adjudicate)

- **Upper-bound side (resolution) U**: for zero-count rows, one-sided 95% Clopper-Pearson `UB_CP(0,n)=1−0.05^{1/n}` + Wilson k=0 form (explicit citable constants carried) + rule-of-three `3/n` cross-check. Frozen projections: n=300→~0.01; n=3000→~0.001; n=30000→~0.0001 (§7 table recomputes all three). If `UB > FER*` then n frames at zero count cannot prove true FER≤FER\*.
- **Tail-probability side (distance) L**: `P(0|p=FER*,n)=(1−FER*)^n≈exp(−n·FER*)`: n=300→≈0.74; n=3000→≈0.0498; n=30000→≈9e-14. A high value means a true-at-gate channel routinely yields the observed zero — the empirical first-pass is expected, not probative.
- **Asymmetric-flip projector S**: translate the G-SYN→bar gap (0.091667) into grid steps of 0.05 and count same-direction single-point misclassifications needed to flip the B-track order word; needs **≥2 steps** (N-C2 bar) to threaten ⇒ ROBUST (§5 K-F3). μ / constructor analysis is explicitly out of scope here (no μ input, no construction call).
- **Non-circularity**: bounds depend only on (n, k=0, FER\*, 95% level) plus transcribed §2 literals for comparison. **No sweep `f*`/`g_synth`/seed/DESIGN_P value and no sweep outcome enters any bound expression**; the T-1 manifest records a `no_sweep_input_attestation`; the T-3 entry refuses start on any freeze mismatch. The sweep grid record enters **only** the K-F3 step-count comparison, never the bound computation.
- **Deep-frame discipline**: K-F2 evaluates the n=3000/30000 UB projections analytically (zero-count assumption stated as projection, not data). **K-F2 licenses no deep-frame execution**; any execution needs a new DECIDE packet.

---

## §4 Cost pre-arithmetic gate design (frozen; T-2 enacts, K-F0 adjudicates — 先算后测)

- **WALL restated**: single-process **300 s**, pure analytic (**zero decode, zero sweep**). Per-arm stall limit **60 s without落盘 → STOP**.
- **Pre-arithmetic formula (pure arithmetic, before any bound table is built)**: `T_pred = N_eval × t_eval_upper + T_overhead`, where `N_eval` = frozen count of closed-form evaluations (bound rows × methods (CP/Wilson/R03/tail) × n-points {300,3000,30000}, frozen in T-1), `t_eval_upper` = frozen per-evaluation analytic upper bound from the T-1 no-write arithmetic micro-probe (≤64 closed-form evals in RAM, median taken, ×2 safety factor — never from 51.0 s), `T_overhead` = frozen 60 s harness margin. All three inputs frozen in T-1; T-2 substitutes numbers only. The audit deep-frame identity (§2 DEEP) is carried alongside as context and never as this packet's cost prediction.
- **Gate**: `T_pred ≤ 300 s` ⟺ proceed to T-3; `T_pred > 300 s` ⟺ mechanical **STOP** with no verdict word, evidence retained (§5/§8). No bound-table evaluation beyond the ≤64-eval micro-probe may run before this inequality is evaluated and recorded. **先算后测 is structural: T-3 is unreachable on a failing prediction.**
- **Auditable 先算后测**: the executor records **monotonic `perf_counter_ns` (or equivalent nanosecond) stamps** for PRED-write, first TABLE-row write, and VERDICT-write; the required order is `t_PRED < t_TABLE_first < t_VERDICT`, and the T-3 entrypoint refuses start without a passing PRED record (code-order + stamp-order + file-order triple gate). Second-granularity mtime alone does not satisfy this packet.
- **Fence**: any plan predicting ≥1800 s, any arm silent for its stall limit, any attempt to price with 51.0 s as throughput = STOP (§8).

---

## §5 Kill conditions (mechanical; K-F1→K-F2→K-F3 in order; any downgrade short-circuits)

- **K-F0 — cost-validity gate (first)**: T-2 evaluates §4 `T_pred ≤ 300 s` on frozen T-1 inputs. Provenance: WALL=300 s frozen here. **Fail ⇒ mechanical STOP (no verdict word).** K-F0 never emits a FER word.
- **K-F1 — resolution gate (the distance statement)**: compare the 0/300 zero-count 95% UB (~0.01, §3 U at n=300) against FER\*=1e-3. `UB > 10×FER*` ⇒ the empirical first-pass is an order of magnitude short of a true-FER proof (record the factor); `UB ≤ FER*` ⇒ resolution sufficient (not pre-expected); straddle ⇒ record exact numbers. K-F1 alone never emits the final word — it fixes the distance premise for K-F3. Provenance: §2 R03/FER\*.
- **K-F2 — deep-frame gate (projection only)**: compare the zero-count projected UBs at n=3000 (~0.001, at-gate borderline) and n=30000 (~0.0001, below-gate) against FER\*. If **both** leave `UB > FER*` (gap>0 remains) ⇒ deep sampling within the audit WALL cannot change the word ⇒ carry ROBUST-leaning premise; if 30000 projects below-gate while 3000 does not ⇒ record the split (INDETERMINATE-leaning premise); if both project below-gate with margin ⇒ record resolvability premise. **All three branches are analytic projections under an explicit zero-count assumption — none authorizes execution.** Provenance: §2 DEEP + §3 U.
- **K-F3 — asymmetric-flip gate (the only FER-word-eligible gate)**: count same-direction single-point misclassifications (grid step 0.05) needed to move the B-track order word across the bar given the GAP 0.091667. `need ≥ 2 steps` (N-C2 bar) ⇒ `FER-ROBUST` (a single asymmetric error cannot threaten the gate); `need < 2 steps` ⇒ `FER-FRAGILE` (a single flip could threaten — licenses only a future measurement packet, claims nothing now); K-F2 split with K-F1 shortfall and flip-count exactly at bar ⇒ `FER-INDETERMINATE`. Provenance: §2 GAP/NC2.
- **Wall-stop rule + failure retention**: any arm exceeding WALL, any 60 s silence without落盘, any predicted-over-wall overrun attempt = STOP; failed attempt retained in the same fresh root with the failing command, exact error/traceback or stall nanosecond stamp, and the single decision needed; at most one preregistered engineering repair+rerun with unchanged scientific inputs/seeds/thresholds/data roles/hypothesis (§10); failed attempt never deleted.

### §5.4 Verdict vocabulary (closed; exactly one word published)

`FER-ROBUST` (K-F0 pass; K-F1 distance recorded; K-F2 gap premise carried; K-F3 need≥2 steps) · `FER-FRAGILE` (K-F0 pass; K-F3 need<2 steps — a single flip could threaten, licenses only a future measurement packet, claims nothing now) · `FER-INDETERMINATE` (K-F0 pass; deep-frame split straddles the gate with flip-count at bar) · `CONTEXT-ONLY` (method breach, citation failure, or single-side-only instantiation — evidence is context, no resolution word beyond that). No other word. No word claims real FER, real feasibility of either sign, or method standing (§11).

---

## §6 Execution root and budget (for the granted run only)

Fresh additive root `workspace/ferres_<new-uuid8>` only — distinct from every existing root including `workspace/n2048b_4e28c8cb/`, `workspace/n2048g_2e921d8e/`, every `workspace/psb_*` and `workspace/psbce_*` root, which are retained, never overwritten, never reused. One process, **≤300 s**, ≤1 GiB, no RNG (deterministic closed-form row order). No overwrite of anything outside the fresh root. Pre-EXECUTE verifies target-root absence (§9.1). This packet's freezing itself wrote only this file.

---

## §7 Machine artifacts and recomputable columns (for the granted run)

`FERRES_TABLE.csv` columns (exact): `n,k_obs,fer_gate,cl_level,ub_cp,ub_wilson,ub_r03,p_zero_at_gate,gap_literal,steps_needed,deep_proj_flag,t_eval_ns`. Rows frozen: n∈{300,3000,30000} × methods {CP,Wilson,R03,tail} (zero-count assumption labeled projection for n>300). Plus `FERRES_PRED.json`: `{N_eval,t_eval_upper,T_overhead,T_pred,wall_pass,deep_identity_carried,t_pred_ns}` (K-F0 cost record with nanosecond stamp). Plus `FERRES_PROV.json`: `{fer_gate,cl_level,cp_formula_citation,wilson_formula_citation,gap_identity,step_quantum,nc2_bar,no_sweep_input_attestation,t_prov_ns}` (K-F1/K-F3 record). Plus `FERRES_VERDICT.json`: `{ub_300,ub_3000,ub_30000,p0_300,p0_3000,p0_30000,steps_needed,kf1_branch,kf2_branch,kf3_branch,verdict_word,t_verdict_ns}`. Reviewer hand-recomputes ≥1 R03 row + ≥1 CP row + ≥1 tail probability + the `T_pred` inequality + the K-F1/K-F2/K-F3 branch chain (§9).

---

## §8 Stop rules (mechanical)

STOP (no verdict) on: transcribed-constant mismatch vs §2 text (including any `g_req`/`g_synth`/GAP/NC2/R03/DEEP digit change or N-C2 >3-step restatement); `T_pred` unevaluated before first bound-table evaluation beyond the micro-probe; any bound-table evaluation before K-F0 cost-pass record; any sweep `f*`/`g_synth`/seed/DESIGN_P value entering a bound expression (redirects to `CONTEXT-ONLY` per §3/§5, further FER words STOPped); any decoder call; any sweep-frame or deep-frame draw; any real-data file open; any wall exceedance or 60 s落盘 silence; any use of 51.0 s as throughput or 0.098260 as measurement; any use of the audit DEEP numbers as execution clearance; any forbidden token in outputs (§9); any sentence reading the resolution as real-channel FER / real-channel gain / N=2048 feasible-or-infeasible / method standing; any cross-claim sentence outside the §11 ceiling block. STOP retains the failed attempt per §5.

---

## §9 Acceptance criteria (numbered; machine-recheckable)

- **AC-F01** Threshold fidelity: `g_synth(H-1)=0.041667=1−1.15/1.2` with grid record `f*_1024=1.20` [0/300@1.20; 4/300@1.15] / `f*_2048=1.15` [0/300], step 0.05, 300 frames/point, labeled empirical-first-pass grid-quantized (never true-FER proof); `g_req` lower edge 0.133333 labeled derived/tag-free/non-measurement; GAP 0.091667≈2.2 steps; N-C2 bar >2 steps (not >3); R03 UB ~0.01 + P(0|1e-3,300)≈0.74; DEEP 3000≈178 s/30000≈696 s with identity `T_pred=G_pts×F_per×t_frame_upper+120`, `t_frame_upper=0.0008`; any digit drift ⇒ STOP. Provenance §2.
- **AC-F02** Cost pre-gate: `FERRES_PRED.json` exists with all frozen inputs + `T_pred ≤ 300` evaluated before any bound-table evaluation (nanosecond-stamp + file-order + code-refusal triple-audited). Fail ⇒ STOP. Provenance §4.
- **AC-F03** Method validity: `FERRES_PROV.json` shows CP + Wilson + R03 + tail closed forms with citation slots filled and no sweep input (`no_sweep_input_attestation` true); single-method-only instantiation ⇒ `CONTEXT-ONLY` cap, no FER word. Provenance §3.
- **AC-F04** Non-circularity: manifest diff shows no sweep `f*`/`g_synth`/seed/DESIGN_P value in any bound expression; grid record used only in the K-F3 step comparison; ≥1 hand row recomputes from (n, k=0, FER\*, level) alone. Breach ⇒ `CONTEXT-ONLY` cap. Provenance §3.
- **AC-F05** Resolution-gate evaluation: K-F1 UB-vs-1e-3 comparison recomputed on the n=300 row with the order-of-magnitude factor recorded. Provenance §2 R03/FER\* / §5.
- **AC-F06** Deep-frame evaluation: K-F2 UB projections at n=3000/30000 recomputed with zero-count-assumption labels; gap>0-or-not recorded per n; no execution sentence present. Provenance §2 DEEP / §5.
- **AC-F07** Flip-gate evaluation: K-F3 step count recomputed from GAP 0.091667 over step 0.05 against the N-C2 ≥2-step bar; branch (ROBUST / FRAGILE / INDETERMINATE) recomputed. Provenance §2 GAP/NC2 / §5.
- **AC-F08** Single mechanical word from §5.4 only; no feasibility/FER-existence/method sentence outside the §11 ceiling block; in particular no real-channel reading of either sign; no claim that N=2048 is feasible or infeasible; no deep-frame execution licensed.
- **AC-F09** §11 claim-ceiling block present with (a) v2-inherited paragraph character-identical + (b) GAIN extension carried + (c) scaling-bound extension carried + (d) resolution-extension paragraph; batch evidence never promoted above it.
- **AC-F10** Forbidden-token machine sweep passes on all outputs (quoted list here is the pattern source, not usage): `0.098260`, `f_eff`, `f_super`, `HDC`, `Layered-Binary`, `void`, `ranking`, `合表`, `10/240`, `35/35`, `thin-surplus`, `CALIBRE-OK`, `GAIN-TESTABLE`, `GAIN-UNTESTABLE`, `SCALING-BOUND-EXCLUDES`, `SCALING-BOUND-REQUIRES`, `SCALING-BOUND-INDETERMINATE`, `CEILING-ROBUST`, `CEILING-FRAGILE`, `CEILING-INDETERMINATE`, `FER-TESTABLE`, `direct`, `double`, `51.0`, `24.6`, `real-frame`, `真实信道`, `无增益`, `.ttbin`, `rows.json`. Quoted pattern lines in the packet/result-config are exempt by exact-line allowlist; any other occurrence FAILs. (Prior-cycle words banned here as outputs to prevent word reuse; provenance discussion by packet-name reference only.)
- **AC-F11** Pre-EXECUTE checklist recorded (§9.1) with explicit grant; FAIL blocks execution.
- **AC-F12** Independent batch-end review (T-4) passes with no blocking comment before any promotion; FAIL blocks promotion; review grants zero threshold/method/claim elevation. Plus wall discipline: no arm exceeds 300 s; no 60 s落盘 silence; stamp order `t_PRED < t_TABLE_first < t_VERDICT` holds; failed attempts retained; at most one preregistered repair+rerun with unchanged inputs/thresholds. Violation ⇒ STOP.

### §9.1 Pre-EXECUTE checklist (FAIL blocks)

Intended branch `formal-ir-v72p1-addendum-clean`; scoped manifest frozen (§10); scientific contract above unchanged since freezing; explicit user authorization citing §14 lineage; target root `workspace/ferres_<new-uuid8>` absent (all existing roots retained untouched); T-1 vectors frozen (binomial formula slots + §2 literals + `T_pred` formula) and loadable with zero real-data contact; forbidden-token pattern loaded; WALL timer armed (300 s kill + 60 s落盘 watchdog + `perf_counter_ns` stamping). T-1 green is produced by execution, not required before it (historical/smoke reference green + frozen vectors loadable suffice).

---

## §10 Scoped manifest (frozen at Pre-EXECUTE, not rewritten here)

At most: one `ferres.py` helper (binomial evaluators CP/Wilson/R03/tail + gap/step projector + `T_pred` calculator; allowed-input gate: no real-data open, no decoder import, no sweep sampler — §2 literals only, T-3 entry refuses without passing PRED) + one fake test (R03/CP/Wilson/tail hand vectors for n∈{300,3000,30000} + gap/step vectors + `T_pred` inequality vectors + K-F1/K-F2/K-F3 branch vectors; **no real frames, no decoder vectors, no sweep vectors**) + wall-timer harness (300 s kill + 60 s落盘 watchdog + `perf_counter_ns` stamping). No decoder entrypoint, no sweep sampler, no deep-frame runner, no I/O reader, no bundle path. Single preregistered engineering repair (harness/stamp-probe fix only, unchanged scientific inputs/seeds/thresholds) permitted once per §5.

---

## §11 Claim ceiling (result record must carry it; (a)+(b)+(c) verbatim-inherited, (d) resolution-extension)

### (a) Inherited v2 block — verbatim, marked as inherited (every word identical to v2 §11 and GAIN §11(a) and SCALING-BOUND §11(a) and CEILING-EXTENSION §11(a)):

> N2048-BUDGET-RECALC reports pure arithmetic under a no-polarization-gain baseline only: per-branch headroom structure at N=2048 and the derived f-gain interval needed to cure the +20% overrun. It claims no polarization gain, no construction, no decoding, no FER, no efficiency, no leakage measurement, no f measurement, no feasibility or infeasibility of N=2048, no method comparison, and no publication number. Numbers labeled derived arithmetic are recomputation targets, not measurements. Any use beyond setting the later sweep packet's gain-gate threshold requires a new DECIDE packet and explicit authorization.

### (b) Carried GAIN extension — carried as inherited context (every word identical to GAIN §11(b) and SCALING-BOUND §11(b) and CEILING-EXTENSION §11(b)):

> N2048-GAIN-SWEEP reports synthetic testability inside a 1200 s cost class only: whether a non-circular synthetic sweep reaches the inherited 13.33% lower edge (H-5 upper edge as context). It claims no real-frame gain existence, no real decoding, no real FER/efficiency/leakage/f measurement, no N=2048 feasibility or infeasibility, no method comparison, and no publication number. Synthetic `g_synth` values are decoder-count derivations on synthetic frames, not measurements of real data. Any use beyond licensing a future DECIDE real-data packet requires a new DECIDE packet and explicit authorization.

### (c) Carried scaling-bound extension — carried as inherited context (every word identical to SCALING-BOUND §11(c) and CEILING-EXTENSION §11(c)):

> POLAR-SCALING-BOUND reports an analytic / semi-analytic polarization-bound interval inside a 300 s zero-decode zero-sweep class only: whether a non-circular two-sided bound interval for the N=1024→2048 `f`-ratio gain lies below, above, or across the inherited 13.33% lower edge (H-5 upper edge as context). It claims no decoder measurement, no sweep measurement, no real-frame gain fact, no real FER/efficiency/leakage/f measurement, no N=2048 feasibility or infeasibility, no statement that the real channel has no gain, no method comparison, and no publication number. Bound `g_bound` values are closed-form derivations from frozen priors (`p_s`, N, μ interval, FER*), not measurements of any channel. Any use beyond excluding-or-not the scaling-law possibility space requires a new DECIDE packet and explicit authorization.

### (d) Resolution-extension (adds scope, weakens nothing above):

> FER-RESOLUTION-ANALYTIC reports a binomial-resolution derivation inside a 300 s zero-decode zero-sweep class only: how far the 0/300 empirical first-pass is from a true-FER≤1e-3 proof, and what the zero-count projected bounds at 3000/30000 imply for the B-track second-step word under the ≥2-step asymmetric-flip bar. It claims no decoder measurement, no sweep measurement, no real-frame FER fact, no real FER/efficiency/leakage/f measurement, no N=2048 feasibility or infeasibility, no statement about the real channel of either sign, no method comparison, and no publication number. Bound values are closed-form binomial derivations from (n, k=0, FER\*, level) plus transcribed comparison literals, not measurements of any channel. Any use beyond answering the 0/300-resolution question requires a new DECIDE packet and explicit authorization.

---

## §12 Non-reopening list + citation discipline (carried; not decided here)

- Stage-0 KILL — scope only: frozen ten per-plane-independent allocations on that f grid + budget only; never cited beyond that range.
- JOINT-PRICING-R2 MARGINAL §5.3(a) — terminal; **both numbers always co-cited: nominal 1100 surplus 4 and +20% 1319 excess 215**; no solo-nominal citation.
- Superframe KILL — M0-2M eval-region sequences only; `S_a`/`S_spread` are context, never clearance.
- C-track kill — same 6×40/240 partition + dual caps 1800/10800 + descriptive unit-price 51.0 s/block at α=0 only; **never cited as proxy-infeasible or channel-stationary**; `FLAG=False` is non-detection under α=0 only, never honesty proof; 51.0 never throughput.
- U1 ceiling as context — q is dispersion-equivalent, non-measured; ~24.6 bit/superframe is context, never clearance.
- M3C / M3D / M2 untouched by this packet.
- Void baselines (including HDC / Layered-Binary void forms) never baselines.
- `0.098260` never a measurement; `51.0 s` never throughput (descriptive unit-price only).
- v2 calibre word means calibre self-consistency + nominal sign-consistent non-negative + interval delivered **only** — not N=2048 feasible, not B-track passed, not gain obtained; never emitted as this packet's output (AC-F10).
- GAIN word means this cost class / synthetic conditions only — not N=2048 infeasible, not B-track terminated, not gain-nonexistent; never emitted as this packet's output (AC-F10).
- SCALING word means this cost class / analytic-bound conditions only — not a real-channel verdict; never emitted as this packet's output (AC-F10).
- CEILING word means grid-top non-flip only under its packet's conditions — not a resolution verdict; never emitted as this packet's output (AC-F10).
- RESIDUAL means nominal structure only; never a clearance claim.
- `g_synth` never a real gain; H-5 zero never a zero-gain proof; TABLE `f_star`/`g_synth` two columns permanently unreadable (recompute from `f_scan`/`fer_emp` only); v1 hand vector permanently banned; 1.20/1.15 always labeled empirical-first-pass grid-quantized, never true-FER proof.

---

## §13 Provenance + fences + design decisions (carried as constraints)

TOTAL含tag + budget 1104 + leak-budget 1040 (single 64-bit tag, N=1024) from `m0_realframe_runner.py:101-106` + STAGE0 §16; v2 calibre anchors from `workspace/n2048b_4e28c8cb/` (R-A@N=1024 `B_T=1104`∧`B_L=1040`; JOINT dual anchors; 10-pair `delta_pure`∈{−1,0}; paired budgets R-A `B_L=2080` / T1 `B_T=2144` / T2 `B_T=2208`; `D_nom` +8恒等×3 arms; `g_req` interval §2 G-INT). **Fences (must inherit)**: v2 calibre fence (§12); GAIN BATCH_END_REVIEW citable form + N1 (TABLE columns unreadable) + N3 (grid-quantization limiter) + N4 (empirical 0/300 first-pass, never true-FER proof) limiters; SCALING-BOUND verdict literal `g_hi=0.10236220` + information-set erratum (successors apply first, no reinterpretation); CEILING-ROBUST verdict literal `g_hi_ext=0.10236<0.133333` carried as context (never this packet's output); `+8` shall never be cited as a thin-surplus conclusion; `g_req` shall never be cited as a measurement or achieved gain; the v1 ≈+8-bit hand vector shall never be cited for any purpose. **Design decisions**: (i) three-method bound side (CP+Wilson+R03) TAKEN for cross-check redundancy — single-method ⇒ CONTEXT-ONLY cap; (ii) deep-frame n=3000/30000 as analytic zero-count projections TAKEN, execution reading explicitly REJECTED; (iii) μ / constructor analysis EXCLUDED (no μ input, no construction call — differs from SCALING/CEILING packets by omission, not by redefinition); (iv) K-F1 records distance but never emits the final word alone (prevents resolution-shortfall misread as fragility); (v) no deviation from frozen §2 threshold digits — any future deviation must be listed here explicitly, none present.

---

## §14 Authorization (main-thread explanation + budget-cap restatement suffice — thin form)

Per the user 2026-09-29 continuous-advance grant ("continue at least ten rounds without step-by-step approval") and the cross-batch audit open question #2 (0/300 statistical resolution — the cheapest frozen sub-question of the three remaining: resolution vs constructor-generality vs R2 unit-price paraphrase), the next frozen step is this analytic resolution packet. Budget caps restated: N=1024 B_T=1104 / B_L=1040 (single 64-bit tag); N=2048 candidate caps authoritative only for v2 K-B1 surviving pairs; gain bar lower edge 0.133333 (derived, tag-free LEAK); synth record `g_synth(H-1)=0.041667`; execution wall WALL=300 s single process, pure analytic, zero decode, zero sweep. **This packet authorizes no real-data contact, no real decode/construction call, no sweep, no DECIDE packet, no deep-frame / fine-grid / SCL / DE experiment, no commit, and no push.**

---

## §15 Tasks (ordered; coder-operator contracts)

- **T-1 — Binomial-bound definition + fake tests (zero decode, zero sweep)**: freeze §10 helper interface; freeze CP/Wilson/R03/tail closed forms with citation slots, FER\*=1e-3, level 95%, n-points {300,3000,30000}, gap identity 0.091667, step quantum 0.05, N-C2 bar ≥2 steps, `T_pred` inputs (`N_eval`, `t_eval_upper` micro-probe design ≤64 closed-form evals, `T_overhead=60 s`); fake tests green on R03/CP/Wilson/tail vectors + gap/step vectors + `T_pred` inequality vectors + K-F1/K-F2/K-F3 branch vectors. Done when AC-F01/AC-F03/AC-F04 vectors recomputed by hand on ≥1 row each and `FERRES_PROV.json` skeleton frozen.
- **T-2 — Cost pre-arithmetic gate (先算后测, no bound table)**: substitute frozen T-1 numbers into §4 `T_pred`, evaluate `≤300 s` with `perf_counter_ns` stamps, emit `FERRES_PRED.json`. Done when AC-F02 stamp/file-order/code-refusal triple audit shows prediction before any bound-table evaluation beyond the micro-probe; fail ⇒ STOP with retained record, T-3 unreachable.
- **T-3 — Bounds + flip-count + mechanical word**: evaluate frozen binomial closed forms only after K-F0 cost-pass; build `FERRES_TABLE.csv` + `FERRES_VERDICT.json` via K-F1→K-F2→K-F3 chain with short-circuit honored (method breach ⇒ `CONTEXT-ONLY`; else K-F3 lower-edge comparison). Done when AC-F05/AC-F06/AC-F07 recomputed on ≥1 row each and §5.4 single word emitted under §11.
- **T-4 — Independent batch-end review**: independent thread re-checks §3 identities, §2 digit fidelity, §5 chain, AC-F01…AC-F12, §11 (a)+(b)+(c)+(d) blocks, forbidden-token sweep (AC-F10), output-root discipline. Pass with no blocking comment required before any promotion; FAIL blocks promotion (rework only; no rerun beyond the one preregistered engineering repair with unchanged inputs/thresholds); review grants zero elevation.
