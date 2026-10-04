# N2048-GAIN-SWEEP — PREREG_AND_AUTH (Frozen B-track step-2 packet; synthetic only, no gain-existence claim)

- **Status**: FROZEN — B-track second-step execution packet. Authorizes only EXPLORE synthetic work T-1…T-4 in one fresh additive root and nothing else (§§6/14). Operator records the Pre-EXECUTE checklist (§9.1) before T-1. **This file is planning text only; no script or test is executed by freezing it.**
- **Succession (no supersession)**: this packet does **not** supersede `N2048-BUDGET-RECALC/PREREG_AND_AUTH_v2.md` (245 lines, sole B-track step-1 authority). v2 stays current for its scope. This packet **inherits** from v2 only: (a) the `g_req` interval + threshold provenance (§2/§5, verbatim values, no change), (b) the §11 claim-ceiling block verbatim (§11a), (c) the `CALIBRE-OK` fence (§13), (d) the citation discipline (§12). v1 (`PREREG_AND_AUTH.md`) and `AMENDMENT-01.md` remain `superseded-before-execution` records; the v1 ≈+8-bit hand vector stays permanently banned (§13).
- **Track**: **EXPLORE** with **`EXPLORE_HEAVY` cost annotation priced at T-2** (lifecycle is EXPLORE; annotation applies because a synthetic sweep may approach wall — see §0.1/§4).
- **Branch**: `formal-ir-v72p1-addendum-clean`. No commit, no push by the operator.

---

## §0 Goal / Non-Goals / Impact Scope / Classification

### Goal

Under **synthetic conditions only**, test whether the N=2048 polarization-gain gate set by v2 (`g_req` interval lower edge **13.33%**) can be reached inside a wall-bounded cost class, in order to determine **testability of the K-B3 gain gate within that cost class**. The packet outputs exactly one mechanical word (§5.4): testability inside the cost class vs untestability inside the cost class (or `CONTEXT-ONLY` on the non-circularity downgrade path). **This packet claims no real-frame gain existence and no N=2048 feasibility conclusion of any kind** (§11).

### Non-Goals

- No contact with real frames / `.ttbin` / `rows.json` / bundles / `(a,b)` arrays / raw data of any kind (§2/§8).
- No real decode/construction call on real data; no FER / efficiency / leakage / f / SKR / key / method figure or claim about real data (§11).
- No void-baseline reference (HDC / Layered-Binary in any form), no ranking, no joint table (forbidden-token gate §9).
- No reopening of: Stage-0 KILL / JOINT MARGINAL / superframe KILL / C-track `STRUCTURALLY_INCOMPLETE_KILL` / U1 / M3C / M3D / M2 (§12).
- No assertion that N=2048 is feasible or infeasible; no assertion that any measured gain exists on real data; no publication number.
- No threshold change to the inherited `g_req` interval; no redefinition of `g_req`; no backoff redefinition.
- No modification of any frozen packet, any existing `workspace/` root, `results/`, `comparison_bench/outputs_comparison/`, `docs/NOW.md`, `docs/decision-log.md`, `docs/troubleshooting.md`, `openspec/`, `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`.
- No commit, no push.

### Impact Scope

- **Written by this stage**: this packet (already written by the planner); at Pre-EXECUTE, one frozen scoped manifest (§10); on execution, all outputs inside one fresh additive root `workspace/n2048g_<new-uuid8>` (§6). Nothing else.
- **Read-only inputs**: none for content beyond transcribed closed-packet constants (§2 — five H values, f anchors, `g_req` interval, three wall-death facts; files govern nothing here because no file is opened for content).
- **Untouched**: `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/outputs_comparison/`, every existing `workspace/` root (including `workspace/n2048b_4e28c8cb/` — retained, never overwritten, never reused), all frozen packets, `docs/NOW.md`, `docs/decision-log.md`, `docs/troubleshooting.md`, `openspec/`, `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`.

### §0.1 Track classification: EXPLORE (EXPLORE_HEAVY priced) — confirmed against `AGENTS.md` §1.2 (all five)

1. **Synthetic / already-approved non-sensitive input**: generator is a synthetic binary-symmetric source with crossover solved from transcribed H targets (§2/§3); no real/private/raw input; thresholds are inherited transcribed numbers, not new channel statistics.
2. **Fresh additive root or no-write probe**: execution (when granted) writes only to one fresh additive root `workspace/n2048g_<new-uuid8>`; T-1 derivation + fake tests are runnable as a no-write probe until then. No existing root is touched.
3. **Bounded and reversible**: one process, hard wall **WALL=1200 s**, ≤2 GiB, deterministic seeds (frozen in §6); deleting the fresh root fully reverses the stage. `EXPLORE_HEAVY` annotation applies because the sweep grid (§3/§4) is priced against wall rather than assumed cheap — annotation only, lifecycle stays EXPLORE.
4. **No claim**: output is a synthetic testability derivation + one mechanical word under the §11 ceiling; no FER/SKR/qualification/promotion/publication figure about real data (§11).
5. **No destructive overwrite or new user-facing external action**: no overwrite path, no network, no commit/push.

**Escalation trigger**: the moment real frames, a real decoder/construction call on real data, a real-N=2048 verification, a route-closing threshold, a publication number, or a destructive output is needed → **STOP** and escalate to DECIDE. Calling a frozen synthetic decoder on synthetic frames inside the fresh root does not trigger escalation; opening any real-data file does (§8).

---

## §1 Frozen question (answerable in one shot)

With the v2 `g_req` interval carried as the **unchanged numeric bar** (§2), and with wall deaths carried as the **unchanged cost fence** (§2/§4), can a **non-circular synthetic sweep** reach the interval lower edge (13.33%) inside the WALL=1200 s cost class — and if so, is the K-B3 gain gate testable in principle within that class? Answer with one mechanical word (§5.4) under the §11 ceiling, via the K-G1→K-G2→K-G3 chain (§5).

---

## §2 Frozen input list (no file opened for content)

No file is opened for content at any step. Mismatch against the cited text = STOP (§8).

| # | Constant | Value | Provenance (text reference, not a file open) |
|---|---|---|---|
| H-1…H-5 | H(A\|B) five sources | 0.79089947 / 0.81957888 / 0.79837921 / 0.82351165 / 0.82567853 | JOINT-PRICING-R2 §2.1 (transcribed; generator targets only via §3 BSC inversion) |
| F-0/F-1 | efficiency anchors | f₀=1.3 / f₁=1.56 (=1.2·f₀, backoff-inside-ceil) | JOINT-PRICING-R2 §3 item 9 / §4 semantics |
| G-INT | **gain-gate interval (UNCHANGED from v2, no edit)** | **[0.133333, 0.171314]**, i.e. **[13.33%, 17.13%]**; lower H-1 loosest, upper H-5 tightest | v2 §5/K-B3 + v2 T-3 fresh root `workspace/n2048b_4e28c8cb/` `BUDGET2048_VERDICT.json`; formula `g_req = 1 − 2080/L₂₀₄₈(f₁,H)` **derived arithmetic, non-measurement, tag-free LEAK**; per-source anchors H-1 0.133333 / H-2 0.165329 / H-3 0.141914 / H-4 0.169329 / H-5 0.171314 |
| W-1 | M3C wall death | **5280 s** | closed-cycle record (cost fence; §4) |
| W-2 | A attempt-2 wall death | **3600 s, zero落盘** | closed-cycle record (cost fence; §4) |
| W-3 | Proxy R2 seg-0 wall death | **1800 s, 35/40 blocks only**; mean **51.0 s/block descriptive only** | closed-cycle record + C-track dual-cap context (§12); 51.0 s never throughput |
| WALL | this packet's execution wall | **1200 s single process** (strictly below the smallest observed death 1800 s, with margin) | frozen here (§4/§6); Pre-EXECUTE re-asserts |

**Lower-vs-upper meaning (frozen)**: reaching the **lower edge (13.33%, H-1)** means even the loosest source's cure-bar is met — the K-B3 gate is non-vacuous in principle within this cost class. Reaching the **upper edge (17.13%, H-5)** means even the tightest source's cure-bar is met — full five-source coverage. **This packet gates PASS on the lower edge and carries the upper edge as context**, because (i) v2 K-B3's closed ≥~14% anchor sits inside the interval and the lower edge is its minimal non-vacuous bar, (ii) demanding the tightest source as PASS would conflate hardest-source coverage with gate testability, (iii) thresholds are inherited and must not be tightened by this packet. Reason recorded; threshold values unchanged.

---

## §3 Gain-metric definition and non-circularity argument (frozen; T-1 enacts, K-G2 adjudicates)

### §3.1 Non-circular gain definition (the only PASS-eligible metric)

- **Generator (assumption side)**: synthetic binary-symmetric source BSC(p_s) with crossover `p_s` solved numerically from `h2(p_s) = H_target` for exactly two targets: **H-1 (PASS point)** and **H-5 (context point)**. Seeds frozen in T-1 before any sweep frame is drawn. Generator emits i.i.d. synthetic pairs at the transcribed H only; it assumes **no N-scaling and no gain**.
- **Constructor (frozen before measurement)**: one frozen polar reliability order family + one frozen frozen-set rule at design-p (e.g. Bhattacharyya/proxy order — exact choice frozen in T-1 manifest, identical rule for N=1024 and N=2048). No tuning on sweep outcomes.
- **Measurer (independent side)**: synthetic-only SC decoder inside the fresh root; for each N∈{1024,2048} find the minimal efficiency multiplier `f*_N` achieving the frozen FER target (**FER*≤1e-3** on synthetic frames, frozen here) by monotone scan over disclosed-bit counts. Gain is then **`g_synth = 1 − f*_2048 / f*_1024`**, computed from decoder success counts only.
- **Independence argument**: generator parameters (p_s, seeds) are frozen before T-3 and never conditioned on decoder outcomes; constructor rule is frozen before T-3 and identical across N; `g_synth` is a function of decoder counts alone — no number is both assumed in generation and read back as verification of the same assumption. T-1 fake tests (§10) pin the `h2` inversion and the `g_synth` formula on hand tables before any sweep frame exists.

### §3.2 Downgrade path (normative)

If K-G2 finds generator↔measurer same-sourcing (any of: p_s retuned on T-3 outcomes; constructor re-picked on T-3 outcomes; `g_synth` computed from generator parameters rather than decoder counts; FER target moved post hoc), the sweep **loses PASS eligibility**: verdict vocabulary collapses to **`CONTEXT-ONLY`** (or `KILL`/STOP per §5), no `GAIN-TESTABLE` word may be emitted, and the packet's evidence is carried as context for a future re-registered packet only. The downgrade is mechanical, not discretionary.

---

## §4 Cost pre-arithmetic gate design (frozen; T-2 enacts, K-G1 adjudicates — 先算后测)

- **WALL restated**: single-process **1200 s** (§2 WALL), per-arm stall limit **600 s without落盘 → STOP** (inherits the A attempt-2 zero落盘 death shape: silence is failure, not patience).
- **Pre-arithmetic formula (pure arithmetic, before any sweep frame)**: `T_pred = G_pts × F_per × t_frame_upper + T_overhead`, where `G_pts` = frozen sweep grid size (H-points × f-scan steps, frozen in T-1), `F_per` = synthetic frames per grid point (frozen), `t_frame_upper` = frozen per-frame synthetic-decode upper bound from the T-1 no-write timing probe (synthetic N=2048 SC decode, ≤64 frames, median taken, ×2 safety factor — never from 51.0 s), `T_overhead` = frozen 120 s harness margin. All four inputs frozen in T-1; T-2 substitutes numbers only.
- **Gate**: `T_pred ≤ 1200 s` ⟺ proceed to T-3; `T_pred > 1200 s` ⟺ mechanical **STOP** with no verdict word, evidence retained (§5/§8). No sweep frame may be drawn before this inequality is evaluated and recorded. **先算后测 is structural: T-3 is unreachable on a failing prediction.**
- **Three-deaths fence**: this packet refuses the dead classes outright — any plan requiring ≥1800 s predicted, any arm silent for 600 s, any attempt to price with 51.0 s as throughput = STOP (§8).

---

## §5 Kill conditions (mechanical; K-G1→K-G2→K-G3 in order; any KILL short-circuits)

- **K-G1 — cost pre-gate (pure arithmetic first)**: T-2 evaluates §4 `T_pred ≤ 1200 s` on frozen T-1 inputs. Provenance: WALL=1200 s frozen here against W-1/W-2/W-3 (§2). **Fail ⇒ mechanical STOP (no verdict word)**; partial prediction record retained in the fresh root; no sweep frame drawn. K-G1 never emits a PASS word.
- **K-G2 — gain non-circularity gate**: T-1 independence record (frozen p_s/seeds/constructor/FER* + fake-test green) re-checked against actual T-3 provenance. Provenance: §3.1 definition. **Fail (same-sourcing detected) ⇒ vocabulary collapses to `CONTEXT-ONLY`**; no `GAIN-TESTABLE` word may be emitted even if numbers reach 13.33%. K-G2 never emits a PASS word by itself.
- **K-G3 — gain achievement gate (synthetic only)**: on the surviving non-circular sweep, `g_synth(H-1) ≥ 0.133333` (v2 lower edge, tag-free LEAK provenance §2 G-INT). Provenance of threshold: v2 T-3 `BUDGET2048_VERDICT.json` (derived arithmetic, non-measurement). **Pass ⇒ `GAIN-TESTABLE`; fail ⇒ `GAIN-UNTESTABLE-IN-CLASS`.** The H-5 upper-edge value (0.171314) is recorded as context alongside, never as a second gate.
- **Wall-stop rule + failure retention**: any arm exceeding WALL, any 600 s silence without落盘, any predicted-over-wall overrun attempt = STOP; failed attempt retained in the same fresh root with the failing command, exact error/traceback or stall timestamp, and the single decision needed; at most one preregistered engineering repair+rerun with unchanged scientific inputs/seeds/thresholds/data roles/hypothesis (§10); failed attempt never deleted.

### §5.4 Verdict vocabulary (closed; exactly one word published)

`GAIN-TESTABLE` (K-G1 pass; K-G2 pass; K-G3 lower-edge reached synthetically) · `GAIN-UNTESTABLE-IN-CLASS` (K-G1 pass; K-G2 pass; K-G3 lower-edge not reached, or cost-class exhaustion without circularity breach) · `CONTEXT-ONLY` (K-G2 breach — evidence is context, no testability word beyond that) · `KILL` (grid/constructor incoherence proven before any gain read — e.g. FER* unreachable at both N on synthetic calibration). No other word. No word claims real gain, real feasibility, or method standing (§11).

---

## §6 Execution root and budget (for the granted run only)

Fresh additive root `workspace/n2048g_<new-uuid8>` only — distinct from every existing root including `workspace/n2048b_4e28c8cb/`, which is retained, never overwritten, never reused. One process, **≤1200 s**, ≤2 GiB, deterministic seeds (frozen `rng_seed` list in the T-1 manifest; no unseeded RNG). No overwrite of anything outside the fresh root. Pre-EXECUTE verifies target-root absence (§9.1). This packet's freezing itself wrote only this file.

---

## §7 Machine artifacts and recomputable columns (for the granted run)

`GAIN218_TABLE.csv` columns (exact): `H_target,p_s,N,f_scan,frames,fer_emp,f_star,g_synth,wall_s_pred,wall_s_used`. Plus `GAIN218_PRED.json`: `{G_pts,F_per,t_frame_upper,T_overhead,T_pred,wall_pass}` (K-G1 record). Plus `GAIN218_PROV.json`: `{p_s,seeds,constructor_rule,fer_target,frozen_hash_note,no_retune_attestation}` (K-G2 record). Plus `GAIN218_VERDICT.json`: `{g_synth_H1,g_req_lower,g_req_upper_context,verdict_word}`. Reviewer hand-recomputes ≥1 `h2` inversion + ≥1 `g_synth` row + the `T_pred` inequality (§9).

---

## §8 Stop rules (mechanical)

STOP (no verdict) on: transcribed-constant mismatch vs §2 text (including any `g_req` digit change); `T_pred` unevaluated before first sweep frame; any sweep frame before K-G1 pass record; generator/constructor retune after T-3 start (redirects to `CONTEXT-ONLY` per §5, further PASS words STOPped); any real-data file open; any real decode/construction call on real data; any wall exceedance or 600 s落盘 silence; any use of 51.0 s as throughput or 0.098260 as measurement; any forbidden token in outputs (§9); any cross-claim sentence outside the §11 ceiling block. STOP retains the failed attempt per §5.

---

## §9 Acceptance criteria (numbered; machine-recheckable)

- **AC-G01** Threshold fidelity: `g_req` interval transcribed as [0.133333, 0.171314] with formula `1 − 2080/L₂₀₄₈(f₁,H)` labeled derived/tag-free/non-measurement; any digit drift ⇒ STOP. Provenance §2 G-INT.
- **AC-G02** Cost pre-gate: `GAIN218_PRED.json` exists with all four frozen inputs + `T_pred ≤ 1200` evaluated before any sweep frame (timestamp/file-order audited). Fail ⇒ STOP. Provenance §4.
- **AC-G03** Non-circularity: `GAIN218_PROV.json` shows p_s/seeds/constructor/FER* frozen at T-1 with no post-start retune (manifest diff empty); `g_synth` recomputes from decoder counts on ≥1 hand row. Breach ⇒ `CONTEXT-ONLY` cap. Provenance §3.
- **AC-G04** Gain achievement: `g_synth(H-1) ≥ 0.133333` evaluated on synthetic decoder counts with H-5 value as context-only column; cell pairs total-vs-budget discipline inherited (same-t/same-k only — no fused `direct−double` column anywhere). Provenance §2 G-INT / v2 §3.7.
- **AC-G05** Single mechanical word from §5.4 only; no feasibility/gain-existence/method sentence outside the §11 ceiling block.
- **AC-G06** §11 claim-ceiling block present with (a) v2-inherited paragraph verbatim + (b) sweep extension; batch evidence never promoted above it.
- **AC-G07** Forbidden-token machine sweep passes on all outputs (quoted list here is the pattern source, not usage): `0.098260`, `f_eff`, `f_super`, `HDC`, `Layered-Binary`, `ranking`, `合表`, `10/240`, `35/35`, `thin-surplus`, `CALIBRE-OK`, `direct`, `double`, `51.0`, `24.6`, `real-frame`, `.ttbin`, `rows.json`. Quoted pattern lines in the packet/result-config are exempt by exact-line allowlist; any other occurrence FAILs. (`CALIBRE-OK` banned here as output to prevent step-1 word reuse; v2 provenance discussion by packet-name reference only.)
- **AC-G08** Pre-EXECUTE checklist recorded (§9.1) with explicit grant; FAIL blocks execution.
- **AC-G09** Independent batch-end review (T-4) passes with no blocking comment before any promotion; FAIL blocks promotion.
- **AC-G10** Wall discipline: no arm exceeds 1200 s; no 600 s落盘 silence; failed attempts retained with command/error/stall record; at most one preregistered repair+rerun with unchanged inputs/seeds/thresholds. Violation ⇒ STOP.

### §9.1 Pre-EXECUTE checklist (FAIL blocks)

Intended branch `formal-ir-v72p1-addendum-clean`; scoped manifest frozen (§10); scientific contract above unchanged since freezing; explicit user authorization citing §14 lineage; target root `workspace/n2048g_<new-uuid8>` absent (all existing roots retained untouched); T-1 vectors frozen (h2 inversion + g_synth formula + T_pred formula) and loadable with zero real-data contact; forbidden-token pattern loaded; WALL timer armed. T-1 green is produced by execution, not required before it (historical/smoke reference green + frozen vectors loadable suffice).

---

## §10 Scoped manifest (frozen at Pre-EXECUTE, not rewritten here)

At most: one `gain218.py` helper (BSC generator + h2 inversion + frozen constructor rule + synthetic SC-decode sweep + `g_synth` + `T_pred` calculators; allowed-input gate: no real-data open — H targets passed as literals from §2) + one fake test (h2 inversion vectors for H-1/H-5 + `g_synth` hand-table vectors + `T_pred` inequality vectors; **no real frames, no fused-difference vectors**) + wall-timer harness (1200 s kill + 600 s落盘 watchdog). No real decoder entrypoint, no I/O reader, no bundle path. Single preregistered engineering repair (harness/timing-probe fix only, unchanged scientific inputs/seeds/thresholds) permitted once per §5.

---

## §11 Claim ceiling (result record must carry it; (a) verbatim-inherited, (b) sweep extension)

### (a) Inherited v2 block — verbatim, marked as inherited (every word identical to v2 §11):

> N2048-BUDGET-RECALC reports pure arithmetic under a no-polarization-gain baseline only: per-branch headroom structure at N=2048 and the derived f-gain interval needed to cure the +20% overrun. It claims no polarization gain, no construction, no decoding, no FER, no efficiency, no leakage measurement, no f measurement, no feasibility or infeasibility of N=2048, no method comparison, and no publication number. Numbers labeled derived arithmetic are recomputation targets, not measurements. Any use beyond setting the later sweep packet's gain-gate threshold requires a new DECIDE packet and explicit authorization.

### (b) Sweep extension (adds scope, weakens nothing above):

> N2048-GAIN-SWEEP reports synthetic testability inside a 1200 s cost class only: whether a non-circular synthetic sweep reaches the inherited 13.33% lower edge (H-5 upper edge as context). It claims no real-frame gain existence, no real decoding, no real FER/efficiency/leakage/f measurement, no N=2048 feasibility or infeasibility, no method comparison, and no publication number. Synthetic `g_synth` values are decoder-count derivations on synthetic frames, not measurements of real data. Any use beyond licensing a future DECIDE real-data packet requires a new DECIDE packet and explicit authorization.

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

---

## §13 Provenance + CALIBRE-OK fence (carried as constraints)

TOTAL含tag + budget 1104 + leak-budget 1040 (single 64-bit tag, N=1024) from `m0_realframe_runner.py:101-106` + STAGE0 §16; v2 calibre anchors from `workspace/n2048b_4e28c8cb/` (R-A@N=1024 `B_T=1104`∧`B_L=1040`; JOINT dual anchors; 10-pair `delta_pure`∈{−1,0}; paired budgets R-A `B_L=2080` / T1 `B_T=2144` / T2 `B_T=2208`; `D_nom` +8恒等×3 arms; `g_req` interval §2 G-INT). **Fence (must inherit)**: v2 `CALIBRE-OK` means calibre self-consistency + nominal sign-consistent non-negative + interval delivered **only** — not N=2048 feasible, not B-track passed, not gain obtained — licensing only this sweep packet's threshold-setting. `+8` shall never be cited as a thin-surplus conclusion; `g_req` shall never be cited as a measurement or achieved gain; the v1 ≈+8-bit hand vector shall never be cited for any purpose.

---

## §14 Authorization (main-thread explanation + budget-cap restatement suffice)

Per the user 2026-09-29 continuous-advance grant, the decision-tree B-track second step is this synthetic gain-sweep testability gate, following the closed v2 calibre gate. Budget caps restated: N=1024 B_T=1104 / B_L=1040 (single 64-bit tag); N=2048 candidate caps authoritative only for v2 K-B1 surviving pairs; gain bar `g_req`∈[0.133333,0.171314] (derived, tag-free LEAK); execution wall WALL=1200 s single process. **This packet authorizes no real-data contact, no real decode/construction call, no DECIDE packet, no commit, and no push.**

---

## §15 Tasks (ordered; coder-operator contracts)

- **T-1 — Gain-metric definition + independence record + fake tests (zero real-data contact)**: freeze §10 helper interface; solve+record BSC `p_s` for H-1/H-5 via `h2` inversion with hand vectors; freeze constructor rule, FER*=1e-3, seeds, grid size `G_pts`, `F_per`, `t_frame_upper` probe design, `T_overhead=120 s`; fake tests green on h2/g_synth/T_pred vectors. Done when AC-G01/AC-G03 vectors recomputed by hand on ≥1 row each and `GAIN218_PROV.json` skeleton frozen.
- **T-2 — Cost pre-arithmetic gate (先算后测, no sweep frame)**: substitute frozen T-1 numbers into §4 `T_pred`, evaluate `≤1200 s`, emit `GAIN218_PRED.json`. Done when AC-G02 timestamp/file-order audit shows prediction before any sweep frame; fail ⇒ STOP with retained record, T-3 unreachable.
- **T-3 — Synthetic sweep + mechanical word**: draw synthetic frames only after K-G1 pass; run frozen constructor + synthetic SC decode at N=1024/2048 over the frozen grid; emit `GAIN218_TABLE.csv` + `GAIN218_VERDICT.json` via K-G1→K-G2→K-G3 chain with short-circuit honored. Done when AC-G04 recomputed on ≥1 row and §5.4 single word emitted under §11.
- **T-4 — Independent batch-end review**: independent thread re-checks §3 identities, §5 chain, AC-G01…AC-G10, §11 (a)+(b) blocks, forbidden-token sweep (AC-G07), output-root discipline. Pass with no blocking comment required before any promotion; FAIL blocks promotion (rework only; no rerun beyond the one preregistered engineering repair with unchanged inputs/seeds/thresholds).
