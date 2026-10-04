# PROXY-NONSTATIONARY-FAITHFULNESS — C-split EXPLORE synthetic double-gate (FROZEN)

- **Status**: FROZEN — planning-frozen by planner on branch `formal-ir-v72p1-addendum-clean`. **Execution is NOT authorized by freezing**: Pre-EXECUTE, any synthetic draw, and the batch-end review are all BLOCKED until a new explicit user grant fills §14. This packet authorizes nothing by itself.
- **Track**: **EXPLORE** (no `EXPLORE_HEAVY` annotation — numpy-only seconds, zero decoder calls, §8). Justification against `AGENTS.md` §1.2 in §0.1. Any route-closing interpretation, any real-data contact, and any recal execution are DECIDE and stay outside this batch.
- **Continuation of**: three-direction comparison conclusion (main thread, 2026-09-29): **preferred C-split EXPLORE part first** (synthetic proxy faithfulness + structural cost double-gate, no real recal); if C is KILLed auto-switch to B synthetic track; if B also KILLed stop-all and return to user. **A (easier-channel) not recommended, not done.** This packet freezes **only the C-EXPLORE synthetic proxy gate**; it drafts **no DECIDE recal packet**.
- **Branch**: `formal-ir-v72p1-addendum-clean`. No commit, no push by any operator under this packet.
- **Single-append**: one fresh additive root + one append-only `EXPLORATION_LOG.md` (EXPLORE contract, §6). No per-arm paperwork.

---

## §0 Goal / Non-Goals / Impact Scope / Classification

### Goal

On one synthetic "nonstationary" proxy, test two things together with one mechanical verdict word each, without touching real data and without running any decoder:

1. **(i) Proxy faithfulness**: whether the proxy can reproduce the M0-2M measured three-family statistics (drift `z`, lag-1 autocorrelation `r_1`, dispersion `D`) and their frozen null bands (§4); and
2. **(ii) Structural cost**: whether per-block decode cost under the same R2 partition could possibly fall inside the R2 segment cap / total cap (§3.5, pure arithmetic, no decode run).

Output is either a permanent fence — "the nonstationary excuse is not completable under this partition / unfaithful" (one of three KILL words, §5) — or "proxy faithful and cost feasible → eligible to **apply for** a DECIDE recal packet" (`FAITHFUL_AND_COST_FEASIBLE`, §5.4). Eligibility licenses no execution (§11, §14).

### Non-Goals

- No contact with any real frame, `.ttbin`, `rows.json`, channel bundle (`gamma_f03.npz`, `gamma_f03_pb.npz`, any `x1_*.npz` — named here only to forbid them), `pairs.parquet`, or any `(a,b)` array (§2.3).
- No real recal, no recal execution, no `assemble` of any real-data result, no write into any production output root (`results/`, `comparison_bench/outputs_comparison/`).
- No void-baseline reference in any form (void HDC / void Layered-Binary figures — named here only to forbid them).
- No FER / efficiency / leakage / `f` / SKR / key figure for any method; no method statement, comparison, or ranking; no combined-table (`合表`) sentence.
- No reopening of any closed item: Stage-0 KILL, JOINT MARGINAL, M3C / M3D / M2 / U1, or any other frozen close.
- No comparison against the `10/240` baseline; no `35/35` trend sentence.
- No citation of the legacy `0.098260` as a measurement (fenced form only, §13).
- No modification of any existing frozen packet, any existing `workspace/` root, `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`, `docs/NOW.md`, `docs/decision-log.md`, `docs/troubleshooting.md`, or `openspec/`.
- No commit, no push.
- No `51.0 s` throughput/performance citation (descriptive per-block wall only, §3.5).

### Impact Scope

- **Written by this stage**: exactly two new repo files (T-1/T-2, §15) — `comparison_bench/src/comparison_bench/cli/proxy_nonstat_sampler.py` (additive numpy-only driver, no decoder import) and `comparison_bench/tests/test_proxy_nonstat_faithfulness_fake.py` (fake-only test, hand constants, zero data contact) — plus this packet (already written by the planner), plus all execution outputs inside one fresh additive root `workspace/proxy_nonstat_<uuid8>/` (§6).
- **Read-only references** (planning-frozen numbers carried from docs, never opened for content by execution except the two doc-transcription checks in T-1/P-4 which read **docs only**, no raw data): `docs/decision-log.md:5227` (M0-2M triple + bands), `docs/research_cycles/PROXY-RECAL-R2/PREREG_AND_AUTH.md` §8 (segment/total caps), the R2 descriptive unit prices as转述 in §3.5. The execution opens **zero** data files (no JSON bundle, no rows, no `.ttbin`/`.npz`/`.parquet`).
- **Untouched**: `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/outputs_comparison/`, every existing `workspace/` root, `docs/NOW.md`, `docs/decision-log.md`, `docs/troubleshooting.md`, `openspec/`, `AGENTS.md`.

### §0.1 Track classification: EXPLORE — justification against `AGENTS.md` §1.2 (all five required)

1. **Synthetic or already-approved non-sensitive input**: all numeric inputs are planning-transcribed frozen statistics (M0-2M triple/bands, R2 caps, R2 descriptive walls) plus synthetic binomial draws generated inside the fresh root from frozen seeds. No real frame, no `.ttbin`, no `rows.json`, no bundle is opened (§2.3, §9).
2. **Fresh additive root or no-write probe**: T-1 arithmetic + fake test use a no-write probe plus fresh `workspace/proxy_nonstat__pytest_<uuid8>/` throwaway roots; T-2 draws write only one fresh additive `workspace/proxy_nonstat_<uuid8>/`, append-only (§6). No existing root is written.
3. **Bounded and reversible**: numpy-only, ≤ 500 × 383 binomial draws × 2 arms + validation draws, wall ≤ 300 s total, RSS ≤ 2 GiB, 1 CPU (§8); zero decoder calls; delete-the-root reverses everything; no retry except the single preregistered infra repair (§8).
4. **No claim**: the §11 ceiling forbids every claim-bearing figure (FER/efficiency/leakage/`f`/SKR/key/method/ranking/combined-table) and every performance reading of `51.0 s`. The only outputs are the frozen triple/cost tables and the single mechanical verdict word (§5), plus the batch-end review. The route-closing reading of any word is DECIDE and stays outside.
5. **No destructive overwrite or new user-facing external action**: fresh-root-only writes; `results/`, `outputs_comparison/`, all pre-existing roots untouched; no commit/push; no external call.

**Upgrade trigger (binding)**: the moment any step needs a real frame, a real recal, a `.ttbin`/`rows.json`/bundle open, a decoder call, a budget above §8, a destructive output, or a publication/qualification/promotion claim, this packet **STOPS immediately** (STOP, retain evidence, return to main) and any continuation requires a new DECIDE packet + new explicit user grant. Uncertainty defaults to DECIDE only when the concrete risk is named; calling a decoder alone does not force DECIDE — but this packet contains zero decoder calls by construction, so any decoder call is a STOP violation (§9).

---

## §1 The frozen question (synthetic proxy double-gate, no recal)

Take a synthetic nonstationary proxy (§3: 383-position count sequence, binomial sampling around the carried ser scale with a frozen linear drift injection) and ask, without any decoder run and without any real-data contact:

**(Q1, faithfulness)** Does the proxy reproduce the M0-2M quiet triple and its frozen null bands when stationary, and does its injected drift exceed the detection floor when nonstationary (§4, K-C1)? **(Q2, structural cost)** Does the arithmetic per-block cost upper bound forced by the R2 partition already exclude the measured descriptive unit price, before any timing run (§3.5, K-C2)? **(Q3, honesty)** Does the proxy simultaneously beautify error scale and cost assumption (optimistic-proxy flag, §5.3, K-C3)?

The three kill conditions (§5) answer Q1–Q3 mechanically. Full PASS on all three yields only `FAITHFUL_AND_COST_FEASIBLE` — eligibility to **apply for** a DECIDE recal packet, never a recal authorization.

---

## §2 Frozen inputs and thresholds (read-only transcription — zero data contact)

Exactly the frozen numbers below. The execution opens **no data file for content**; T-1/P-4 verify transcription against the cited **docs only** (byte/line pointers, no `.ttbin`/`.npz`/`.parquet`/`rows.json`/bundle open — any such open is a STOP, §9). Files govern over this transcription; any mismatch is a STOP, never an averaging license.

| # | Frozen quantity | Value | Provenance (threshold source, citable) |
|---|---|---|---|
| F-1 | M0-2M eval-region length | `n = 383` | `docs/decision-log.md:5227` (`2M eval-region sequence n=383`); band denominators 383/382 corroborate |
| F-2 | M0-2M drift statistic | `z = -1.74066440` (rounded `-1.7407`), null band `\|z\| ≤ 3` → quiet | Value + `\|z\|≤3 静` from `docs/decision-log.md:5227` |
| F-3 | M0-2M lag-1 autocorrelation | `r_1 = 0.12224678` (rounded `0.1222`), null band `\|r_1\| ≤ 0.15329284` (`= 3/√383`, frozen gate) → quiet | Value + band + formula from `docs/decision-log.md:5227` (`对带 0.15329284（=3/√383，冻结门）静`) |
| F-4 | M0-2M dispersion | `D = 0.80642234` (rounded `0.8064`), upper band `D ≤ 1.21707238` (`= 1+3√(2/382)`, frozen gate) → quiet | Value + band + formula from `docs/decision-log.md:5227` (`对带 1.21707238（=1+3√(2/382)，冻结门）静`) |
| F-5 | Detection floor | `~1e-6` (five-acquisition fence; multi-plane rates above ~10⁻⁶ excluded per 10⁶-pair floor) | Five-capture fence + `CHAN-QUALITY-SURVEY/INDEPENDENT_ACCEPTANCE.md` Part B detection-floor caveat (standing); user-frozen kill source for K-C1 |
| F-6 | R2 segment cap / total cap | `segCap = 1800 s`, `totalCap = 10800 s`; partition `6 × 40`, `N_cost = 240` | `docs/research_cycles/PROXY-RECAL-R2/PREREG_AND_AUTH.md` §8 (per-segment ≤ 1800 s, total ≤ 10800 s, 6 sequential segments of 40) |
| F-7 | R2 descriptive unit prices | `mean 51.0 s/block`, `max 80.8 s/block` — **descriptive only, non-performance口径** (see §3.5 labels) | Main-thread转述 R2 execution record (user statement 2026-09-29); this packet does **not** re-measure them and never cites them as throughput/performance |
| F-8 | M0-2M count scale (context) | `mean 259.8486, min 202, max 299` on the 383-sequence | `docs/decision-log.md:5227` (context column, never a gate target) |

### §2.3 Zero-real-data / no-bundle statement

The channel bundle, any `.ttbin`, any `x1_*.npz`, any `rows.json`, any `pairs.parquet`, any `(a,b)` array, and every M0/CQ workspace root are **not inputs and must not be opened** — not for reading, not for comparison, not for "checking" the proxy against them. The driver path-gate (T-2) refuses any path outside the fresh root and any path ending in `.ttbin`/`.npz`/`.parquet`/containing `rows.json` before any read. T-1/P-4 read **only** the two doc paths cited above (frozen numbers/bands/caps) plus this packet itself.

---

## §3 The proxy (frozen decisions S-N1…S-N6, not code)

**Rationale in one line**: the M0-2M 383-sequence mean (≈ 259.85) equals `1024 × 0.25375836` (CQ-J21c ser scale) to 0.01, with min/max consistent with binomial spread — so a binomial count proxy at that scale with a frozen linear drift injection tests exactly whether a "nonstationary" story can reproduce the quiet triple (control) and exceed the detection floor when drift is present (drift arm), with zero real-data contact. **[DD-1: planner's scale identification; assumption with stated basis, not a measurement claim.]**

- **S-N1 Length and replicates [DD-2]**: fidelity length `N = 383` (F-1); replicates `R = 500` per arm (numpy-trivial, multi-seed default per §1.2). Seeds `2026099001 + r`, `r = 0..499`, stream label `nonstat:{arm}:{r}`. Same seeds both arms (paired draws).
- **S-N2 Sampling law [DD-3]**: per position `i = 0..382`, draw `X_i ~ Binomial(n_sym = 1024, p_i)` with `p_i = clip(p_base + Δ_arm·(i/(N-1) − 0.5), 0, 1)`. `p_base = 0.25375836` (CQ-J21c ser scale, carried context from PROXY-RECAL-R2 §2.1 — **not** re-measured here). Control arm `Δ_ctrl = 0` (stationary); drift arm `Δ_drift = 0.02` absolute peak-to-peak (assumption, frozen; `0.02 ≫ 1e-6` floor so the sensitivity sub-gate is meaningful; keeps `p_i ∈ [0.2438, 0.2638]` valid). Any other `Δ` is a new packet.
- **S-N3 Statistics (frozen formulas [DD-4])**: per replicate sequence `X_0..382`, compute exactly:
  - `z = (m2 − m1) / sqrt(s1²/n1 + s2²/n2)` with first half `n1 = 191` (`X_0..190`, mean `m1`, var `s1²`) vs second half `n2 = 192` (`X_191..382`, mean `m2`, var `s2²`) — two-half mean-difference drift statistic. Gate `|z| ≤ 3` (F-2 band).
  - `r_1` = lag-1 Pearson autocorrelation of the 383 sequence (mean-centered, denominator `Σ(X_i−m)²`, `i = 0..382`). Gate `|r_1| ≤ 0.15329284` (F-3 band).
  - `D = s² / m` with `m` = mean, `s²` = sample variance (`ddof=1`) of the 383 counts. Gate `D ≤ 1.21707238` (**upper-only**, F-4 band literally; no lower bound is imposed — see DD-5).
  - Gate aggregation: **median across the R = 500 replicates** per arm (`z_med`, `r_med`, `D_med`). Medians are the single gate statistics (robust, one number each). **[DD-4: formula + median-aggregation choices are the planner's; T-1 verifies transcription of bands only (docs), never recomputes M0-2M from raw data; any formula ambiguity at implementation is a STOP, §9.]**
- **S-N4 No-lower-bound on D [DD-5]**: the user froze only the upper expression `1+3√(2/382) = 1.21707238`; this packet imposes **no** lower bound (`1−3√…` is recorded as an arithmetic derivation `0.7829…` for context only, never a gate). A lower-bound reading is a new packet.
- **S-N5 Zero-decoder construction**: numpy-only (`numpy.random.default_rng` with the frozen seeds). No LDPC/decode import, no graph, no `max_iter`, no Stage-1/Stage-2, no timing measurement of any decode. Any decoder call is a STOP (§9).
- **S-N6 What the proxy is not**: not a channel fit, not a recalibration, not a real-frame model, not a method, not evidence that the real channel is (non)stationary. It is a synthetic sensitivity + reproduction probe only (§11, §12).

### §3.5 Front-loaded cost arithmetic gate (pure derivation — no decode run)

Required per-block upper forced by the R2 partition (F-6):

> `C_req = min(segCap/40, totalCap/240) = min(1800/40, 10800/240) = min(45, 45) = 45 s/block.`
> `E_req = 240 × C_req = 10800 s` (whole-partition extrapolation ceiling).

Unit-price labels (frozen; **which are assumptions vs existing measured labels**):

- **Existing measured labels (descriptive, NOT performance; never throughput)**: `U_mean = 51.0 s/block`, `U_max = 80.8 s/block` (F-7). Provenance: main-thread转述 R2 segment descriptive measurement (user 2026-09-29). This packet does not re-measure, does not verify by timing, and **never** cites `51.0 s` as throughput or decoder performance.
- **Assumptions (planner's, frozen)**: proxy overhead factor `α ≥ 0` with `U_assume(α) = U_mean × (1+α)` — nonstationary handling under identical decoder/pins cannot be cheaper than the stationary descriptive floor. Gating uses the most lenient frozen value **`α = 0 → U_assume = 51.0 s`**; the `α = 0.1 → 56.1 s` sensitivity line is recorded as descriptive context only, never a second gate. **[DD-6: α-form is the planner's honesty device; the lenient α = 0 choice favors the proxy and is therefore the correct kill-gate baseline.]**

K-C2 arithmetic verdict (computed in T-3 **before** any T-2 draw; §5.2): `51.0 > 45` **and** `240 × 51.0 = 12240 > 10800` → the bound is already exceeded at the lenient assumption. `80.8 > 45` is recorded as corroborating descriptive context (max exceeds the bound by `35.8 s`), not an independent gate. **No 1800 s burn, no timing run, no post-hoc statistic is permitted before this verdict** — any decode or timing measurement before the recorded arithmetic verdict is a STOP (§9).

---

## §4 Comparison metric (frozen — control vs drift, medians vs F-2…F-4 bands)

| Arm | Input | Gate statistic | Pass condition (all three required for the arm's word) |
|---|---|---|---|
| Control (stationary, `Δ = 0`) | 500 draws, seeds `2026099001+r` | `z_med_ctrl`, `r_med_ctrl`, `D_med_ctrl` | `\|z_med_ctrl\| ≤ 3` **and** `\|r_med_ctrl\| ≤ 0.15329284` **and** `D_med_ctrl ≤ 1.21707238` → reproduces the M0-2M quiet triple |
| Drift (`Δ = 0.02`) | same 500 seeds (paired) | `z_med_drift`, `r_med_drift`, `D_med_drift`; emergent ser `p_emerg = mean(X)/1024` per replicate, median `p_med_drift` | sensitivity: **NOT** all-quiet (at least one of the three bands exceeded) **and** `Δ_drift = 0.02 ≥ 1e-6` floor **and** `p_med_drift` within `p_base ± 0.003` (non-beautified; else see K-C3) |

`undetected` has no meaning here (no decoder) and is never merged into anything. No `10/240` comparator is used anywhere. No `35/35` sentence is written anywhere.

---

## §5 Frozen decision rule (exactly one word — priority C1 > C2 > C3) **[DD-7: priority order is the planner's]**

Applied mechanically to the §4 medians + §3.5 arithmetic + §5.3 flag. The verdict is **exactly one** of the four words below; if several clauses fire, the highest-priority word is emitted alone with its clause cited.

> **§5.1 K-C1 Faithfulness gate (KILL as `UNFAITHFUL_PROXY_KILL`).** Fires iff **any** of: (a) control reproduction fails — `|z_med_ctrl| > 3` **or** `|r_med_ctrl| > 0.15329284` **or** `D_med_ctrl > 1.21707238`; **or** (b) injected drift below the detection floor — `Δ_drift < 1e-6` as frozen (here `0.02`, so this sub-arm passes by freeze; any implementation with `Δ < 1e-6` fires it); **or** (c) drift insensitive — drift arm stays all-quiet (`|z_med_drift| ≤ 3` **and** `|r_med_drift| ≤ 0.15329284` **and** `D_med_drift ≤ 1.21707238`). Threshold sources: F-2/F-3/F-4 bands + F-5 floor (see §7 kill-mapping). Consequence: permanent fence "proxy unfaithful — the nonstationary story in this form reproduces nothing / detects nothing"; auto-route to the B synthetic track per the main-thread comparison conclusion (a new packet + new grant, never an edit here).
>
> **§5.2 K-C2 Structural cost gate (KILL as `STRUCTURALLY_INCOMPLETE_KILL`).** Fires iff `U_assume(0) = 51.0 > C_req = 45` **or** `240 × 51.0 = 12240 > 10800`. Pure §3.5 arithmetic (assumption + measured labels, zero timing). A timing burn before this verdict (any decoder call, any 1800 s segment run, any per-block stopwatch used as gate evidence) is forbidden — the gate is front-loaded by construction. Consequence: permanent fence "nonstationary excuse structurally incompletable under the 6×40 / 240 partition"; same B-track routing as §5.1.
>
> **§5.3 K-C3 Gain-honesty gate (KILL as `OPTIMISTIC_PROXY_KILL`).** Optimistic-proxy flag (frozen **before** any draw — measured after): `FLAG = O_err AND O_cost` with `O_err := (p_med_drift < p_base − 0.003)` (drift arm makes the channel look **easier** than its own design target beyond the carried R2 §3.5 `0.003` tolerance — descriptive count mean only, **NOT** FER/efficiency/leakage/`f`/SKR) and `O_cost := (U_used_in_T3 < U_mean = 51.0)` (T-3 assumes the proxy **cheaper** than the descriptive floor without evidence). `FLAG = true` → KILL. By freeze `U_used = 51.0` so `O_cost = false` and the flag cannot fire unless the operator invents a cheaper assumption (forbidden, STOP if done silently). **[DD-8: the `0.003` tolerance carry + AND-form are the planner's; they reuse the only frozen ser-tolerance on record without inventing a new one.]**
>
> **§5.4 PASS (`FAITHFUL_AND_COST_FEASIBLE`).** Iff **none** of K-C1/K-C2/K-C3 fires. Consequence: **only** this is licensed — "proxy faithful and cost feasible → eligible to **apply for** a DECIDE recal packet" (new packet + new explicit grant + Pre-EXECUTE + Pre-RESULT, real-data/expensive/formal rules apply there). Licenses no real-frame contact, no recal execution, no performance/method/ranking/combined-table claim, and no execution of any kind here.

Planner's arithmetic expectation (the frozen rules govern, not this note): K-C1 control medians expected near `z ≈ 0`, `r_1 ≈ 0`, `D ≈ 0.75` (upper-only PASS); drift arm with `Δ = 0.02` expected to break at least the `z` band (sensitivity PASS); K-C2 fires on `51.0 > 45` regardless — so the packet's expected terminal is `STRUCTURALLY_INCOMPLETE_KILL` unless the batch-end review finds a frozen-number transcription error. This expectation is descriptive planning context, never gate evidence.

---

## §6 Deliverables and where each goes

One fresh additive root, fixed at Pre-EXECUTE: `workspace/proxy_nonstat_<uuid8>/` (uuid8 recorded in §14 P-6; the `nonstat_` infix guarantees no collision). **No existing root may be written. Zero decoder calls in any deliverable.**

| # | File | Content |
|---|---|---|
| D-1 | `workspace/proxy_nonstat_<uuid8>/PROXY_NONSTAT_RESULT.json` | `inputs` (frozen numbers F-1…F-8 as transcribed + doc pointers), `proxy` (S-N1…S-N6 as executed + seeds), `fidelity` (per-arm medians `z/r/D` + band margins + PASS/FAIL per sub-arm, `p_med` per arm), `cost` (`C_req` derivation + `U_mean`/`U_max` labels + `U_assume` + fired/not arithmetic), `honesty` (`O_err`/`O_cost`/`FLAG` with numbers), `decision` (exactly one §5 word + fired clause + evidence pointers), `resources` (numpy wall_s, peak RSS, CPU, commands, thread-pin env — decode counts identically `0`) |
| D-2 | `workspace/proxy_nonstat_<uuid8>/PROXY_NONSTAT_SUMMARY.md` | Human-readable twin of D-1 (triple table, cost table, honesty table, single verdict word, §11 ceiling **quoted verbatim**). No ranking sentence; no method sentence; no `10/240` comparison; no `35/35` sentence |
| D-3 | `workspace/proxy_nonstat_<uuid8>/EXPLORATION_LOG.md` | Single append-only log (EXPLORE contract): Pre-EXECUTE record, T-1/T-3a arithmetic record, per-arm draw attempts, machine-gate results, the preregistered repair if used (§8), retained failures, final evidence pointer, review pointer |
| D-4 | `workspace/proxy_nonstat_<uuid8>/BATCH_END_REVIEW.md` | Independent batch-end review against PC-01…PC-08 (§7). FAIL blocks promotion of every number in this batch; rework + re-review, never publish-then-patch |

---

## §7 Acceptance items (stable IDs — each verifiable by machine column + threshold source)

| ID | Item (gate + threshold source) | Verify against |
|---|---|---|
| PC-01 | Input/threshold fidelity: F-1…F-8 transcribed exactly (`383`; `-1.74066440 / ±3`; `0.12224678 / 0.15329284 = 3/√383`; `0.80642234 / 1.21707238 = 1+3√(2/382)` upper-only; `~1e-6` floor; `1800 / 10800 / 6×40 / 240`; `51.0 / 80.8` descriptive labels; `259.8486 / 202 / 299` context); zero data-file opens | D-1 `inputs` + D-3 Pre-EXECUTE record + reviewer `stat`/`rg` of doc pointers; `rg` for `\.ttbin\|\.npz\|\.parquet\|rows\.json` in driver returns only refusal-gate lines |
| PC-02 | Proxy-fidelity mechanics: S-N1…S-N6 as executed (`N = 383`, `R = 500`, seeds `2026099001+r`, `n_sym = 1024`, `p_base = 0.25375836`, `Δ_ctrl = 0` / `Δ_drift = 0.02`, frozen `z`/`r_1`/`D` formulas, median aggregation); per-arm medians with band margins recorded | D-1 `fidelity` + fake test (P-3) + reviewer recomputation on hand-fixed sequences |
| PC-03 | Cost arithmetic (front gate): `C_req = min(1800/40, 10800/240) = 45` derivation present; `U_mean = 51.0` / `U_max = 80.8` labeled existing-measured-descriptive (NOT performance/throughput); `U_assume(0) = 51.0` labeled assumption (`α = 0`); verdict `51.0 > 45`, `12240 > 10800` computed with **zero** timing/decoding before it | D-1 `cost` + D-3 T-3a record (timestamp before any draw) + `rg` for `decode\|ldpc\|construct\|max_iter` in driver returns zero non-comment hits |
| PC-04 | Honesty flag: `O_err` (`p_med_drift < p_base − 0.003`) and `O_cost` (`U_used < 51.0`) frozen, computed, `FLAG = AND` recorded; no FER/efficiency/leakage/`f`/SKR column anywhere | D-1 `honesty` + reviewer check that no `FER\|efficien\|leak\|SKR` claim column exists outside the §11 quotation |
| PC-05 | Single verdict word: exactly one of `UNFAITHFUL_PROXY_KILL` / `STRUCTURALLY_INCOMPLETE_KILL` / `OPTIMISTIC_PROXY_KILL` / `FAITHFUL_AND_COST_FEASIBLE` with the fired §5 clause cited and priority C1 > C2 > C3 honored; no second word, no trend sentence | D-1 `decision` + D-2 word line + reviewer priority re-evaluation |
| PC-06 | No-overwrite + zero-decoder: fresh `workspace/proxy_nonstat_<uuid8>` only; `results/`, `comparison_bench/outputs_comparison/`, all pre-existing `workspace/` roots untouched; `git diff --stat -- src/ experiments/ tools/` empty; new repo files = exactly the §10 scoped manifest; decoder-call count identically `0` | filesystem + git state + D-1 `resources` |
| PC-07 | Deliverables + review: D-1…D-4 complete in the fresh root; D-2 quotes the §11 ceiling **verbatim**; independent batch-end review PASS (FAIL ⇒ no promotion, rework, re-review); **zero promotion before review PASS** | review document + `diff` of D-2 ceiling block vs §11 |
| PC-08 | Claim-ceiling machine check: in the fresh root, tokens ``0.098260`` (and `0.09826`), `f_eff`, `f_super`, `HDC`, `Layered-Binary`, `ranking`, `合表`, `10/240`, `35/35` return **zero hits** outside the quoted §11 ceiling block (planner extension: `10/240` + `35/35` added to the user-frozen four groups — see DD-9); no numeric FER/efficiency/leakage/`f`/SKR/key claim and no method-improvement sentence anywhere | `rg` over `workspace/proxy_nonstat_<uuid8>` + reviewer read |

**Kill-condition → threshold-source mapping (machine-checkable)**: K-C1a → F-2/F-3/F-4 bands (`decision-log.md:5227`); K-C1b-floor → F-5 (`~1e-6` fence + frozen `Δ = 0.02`); K-C1c-sensitivity → F-2/F-3/F-4 bands (NOT-all-quiet); K-C2 → F-6 caps (`PROXY-RECAL-R2 §8`) + F-7 labels (`51.0/80.8` descriptive) via the §3.5 derivation; K-C3 → carried `0.003` tolerance (`PROXY-RECAL-R2 §3.5`) + F-7 `51.0` floor.

---

## §8 Budget (frozen ceiling — numpy-only, zero decodes)

Numpy-only draws + arithmetic, one CPU, threads pinned (`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1`), total wall **≤ 300 s**, peak RSS **≤ 2 GiB**, decoder calls **identically 0**. Breach ⇒ STOP, retain evidence, return to main (not a repair trigger). **No 1800 s segment, no per-block timing, no decode stopwatch exists in this packet.**

**Preregistered repair (single, infra-only)**: at most one repair+rerun of the affected draw set, only for infrastructure failure (process crash, OOM-kill, tool-side timeout, lost transcript, checkpoint-write I/O error) with **unchanged** scientific inputs, proxy parameters, seeds, thresholds, formulas, partition, and decision rule; the failed attempt is retained in `EXPLORATION_LOG.md` in the same root. A fidelity REFUSE, an arithmetic KILL, an honesty FLAG, or any change to a scientific input/parameter/threshold/formula/rule is not a repair — it is a new packet.

---

## §9 Stop rules (any one ⇒ stop, retain evidence, return to main)

1. Any frozen number/band/cap/price in §2 challenged by a doc mismatch (transcription ≠ cited doc line) — files govern, never average.
2. Any attempt to open a bundle/`.npz`, a `.ttbin`, a `pairs.parquet`, a `rows.json`, or any raw-data/workspace data root — or any write into an existing root.
3. Any decoder call, any LDPC/graph/`max_iter` code path entered, any per-block decode timing measured or cited as gate evidence.
4. Any timing burn before the T-3a arithmetic verdict is recorded (front-gate violation).
5. A proxy formula ambiguous as written here (do not interpolate — stop).
6. Any invented rate/price (a number not in §2 or not derived by a §3.5/§5.3 frozen formula), any cross-source averaging, any lower-bound D gate, any `Δ` ≠ `{0, 0.02}`.
7. Seed/count/partition drift: seeds ≠ `2026099001+r`, `N` ≠ 383, `R` ≠ 500, `n_sym` ≠ 1024, cost partition ≠ `6 × 40 / 240`, caps ≠ `1800/10800`.
8. Budget breach (§8) — wall, RSS, or any decoder-count ≠ 0.
9. Output collision (`workspace/proxy_nonstat_<uuid8>` already exists, or any D-1/D-2 already exists at start) or any write inside an existing root, `results/`, or `comparison_bench/outputs_comparison/`.
10. Any evidence-label error (a number cited with the wrong source, a status relabelled, a fenced §13 sentence altered, `51.0 s` cited as throughput/performance, a `10/240` comparison or `35/35` trend written, a second verdict word emitted).

On stop: retain all evidence in place, **do not adjust inputs to fit**, return to the main thread with the failing check, the exact command, and the exact error. No rerun except the §8 preregistered infra repair.

---

## §10 Pre-EXECUTE checklist (main measures in one session before any draw)

| # | Check | How |
|---|---|---|
| P-1 | Branch / HEAD re-measured | `git branch --show-current`, `git rev-parse HEAD` recorded |
| P-2 | Scoped cleanliness | `git diff --stat -- src/ experiments/ tools/` empty; new repo files = exactly two: `comparison_bench/src/comparison_bench/cli/proxy_nonstat_sampler.py` + `comparison_bench/tests/test_proxy_nonstat_faithfulness_fake.py` (scoped manifest). This packet file itself is the planner's already-written deliverable |
| P-3 | Focused test — **new fake-only test REQUIRED** | **Exact command**: `.venv/bin/python -m pytest comparison_bench/tests/test_proxy_nonstat_faithfulness_fake.py -p no:cacheprovider` — must be **all-pass** on fresh additive `workspace/proxy_nonstat__pytest_<uuid8>` roots. **Why new code needs a new test**: T-2 adds a new sampler/statistics/verdict path covered by no existing test. **What the fake asserts** (hand-computable constants, zero data contact — reads no data/doc JSON, no bundle, nothing): `z`/`r_1`/`D` helpers return hand-fixed values on three hand-fixed 12-length sequences; `C_req` helper returns `45` from `(1800, 40, 10800, 240)`; verdict helper returns each of the four §5 words on four hand-fixed (medians, prices, flag) cases with priority C1 > C2 > C3; the input path-gate refuses planted `.npz`/`.ttbin`/`.parquet`/`rows.json` paths before any read; median aggregation matches a hand median |
| P-4 | Input/threshold transcription check (docs only) | `stat`/read the two cited doc lines (`decision-log.md:5227`, `PROXY-RECAL-R2 §8`) + user-frozen `51.0/80.8` labels: F-1…F-8 match §2 exactly; no data file opened |
| P-5 | Output absence | `workspace/proxy_nonstat_<uuid8>` does not exist; `results/` and `comparison_bench/outputs_comparison/` state recorded (no writes there) |
| P-6 | Exact commands frozen | T-3a arithmetic command + T-2 draw command frozen with form `OMP_NUM_THREADS=1 … PYTHONPATH=<repo-root> .venv/bin/python -m comparison_bench.src.comparison_bench.cli.proxy_nonstat_sampler --root workspace/proxy_nonstat_<uuid8> --execute-synthetic --execution-authorized` (refuse without both flags; refuse any decoder/timing flag). Root uuid8 fixed here |
| P-7 | Budgets + stops read back | §8 ceilings (300 s / 2 GiB / 0 decodes) and §9 stop rules read back verbatim |
| P-8 | Protected roots + forbidden reads | Prove all pre-existing `workspace/` roots untouched (no writes); `rg` the T-2 driver for `decode\|ldpc\|construct\|bundle\|gamma\|ttbin` returns only refusal-gate lines and zero read-shaped paths |

---

## §11 Claim ceiling (verbatim — binds the execution, the review, and any citation; quoted verbatim in D-2)

> This stage produces a synthetic proxy-faithfulness + arithmetic-cost result about a generator, nothing more. It establishes NO FER, NO efficiency, NO leakage, NO f, NO SKR and NO key figure for any method; NO method comparison, NO ranking and NO combined table; NO claim that any code improves; NO claim that the proxy equals the real channel; and NO real-recal license of any kind. The value 0.098260 is never cited as a measurement. The void HDC and void Layered-Binary figures are never used as a baseline in any form. The number 51.0 s is a descriptive per-block wall label, never a throughput or performance figure. No 10/240 comparison is made and no 35/35 trend sentence is written. A FAITHFUL_AND_COST_FEASIBLE word licenses only an application for a DECIDE recal packet; it licenses no performance claim, no decoder claim, and no execution.

---

## §12 What this stage cannot decide

1. **That any method corrects well.** No code is compared, improved, or qualified here; medians are channel-proxy observables, not method results. Cheapest test that would: the DECIDE recal packet a PASS licenses — and even that is real-data-gated.
2. **That the real channel is (non)stationary.** The proxy inherits exactly the limits of its frozen transcribed statistics plus the planner's binomial + linear-drift assumptions (DD-1…DD-4); it characterizes no real frame.
3. **That synthetic becomes trustworthy beyond the stated eligibility.** A PASS restores nothing except the right to apply for a DECIDE recal packet; qualification, publication numbers, and real-frame claims each need their own DECIDE packet.
4. **Anything from a partial or repaired run beyond the frozen rule.** Retained draws measure execution only; they support no rate claim, no trend claim, and no recal decision. Only the single §5 word on full completion counts.

---

## §13 Standing citation disciplines (binding on this packet and every deliverable)

- **MARGINAL dual-number rule**: any reference to the JOINT MARGINAL band cites **both** `nominal 1100 vs 1104 (fits by 4)` **and** `+20% backoff 1319 vs 1104 (excess 215)` together (`docs/decision-log.md:5205`); a lone `fits by 4` / single-nominal citation is forbidden.
- **Superframe-KILL scope**: the landed superframe KILL covers **only** the landed M0-2M eval-region sequence already on disk — it does **not** close the conditioning route as a whole; a route-wide closure claim is forbidden.
- **`S_a` / `S_spread`**: `S_a = 18.851175` / `S_spread = 391.5144` are **context columns only** (`decision-log.md:5227` counterfactual), never a pass/fail override — bounds never move a verdict word (§5).
- **`u1`**: `u1 ≈ 24.6 bit/superframe` header bound is **context**, and its `q` is a dispersion-equivalent (non-measured) quantity — neither is cited as a measurement nor enters any gate.
- **Legacy / void / ranking fences**: `0.098260` never a measurement; void HDC / void Layered-Binary never a baseline; no `ranking` / `合表` sentence; no `10/240` comparison; no `35/35` trend — enforced by PC-08 machine check.

---

## §14 Grant block

- Drafting + continuous-push authorization verbatim: user 2026-09-29 「往下持续推进，不要逐项问」 + main-thread three-direction comparison decision (**preferred C-split EXPLORE first**, C-KILL → auto B-synthetic, B-KILL → stop-all return to user, A not recommended / not done). Date / granter: 2026-09-29, user + main thread. Scope: **covers freezing this EXPLORE packet only** (planner output, no repo-code change, no execution).
- Execution grant: **PENDING — no verbatim text, no execution.** Pre-EXECUTE (T-3), all draw commands (T-2), and the review (T-4) are blocked until the user issues a new explicit grant naming this packet (`PROXY-NONSTATIONARY-FAITHFULNESS`) with its §8 ceilings; the new verbatim text will be pasted here with date/granter before any P-1 measurement.
- **This packet does NOT authorize any real recal execution.** No real frame, no `.ttbin`/`rows.json`/bundle contact, no decoder run, no `assemble`, and no DECIDE recal run is authorized here or by any review PASS under this packet. A DECIDE recal needs its own packet + its own explicit grant.

---

## §15 Tasks (ordered, for coder agents)

1. **T-1** — Inputs, thresholds, arithmetic helper + fake test (zero data contact): implement `comparison_bench/tests/test_proxy_nonstat_faithfulness_fake.py` per §10 P-3 (fake-only; `-p no:cacheprovider`; fresh `workspace/proxy_nonstat__pytest_<uuid8>` roots; hand constants only, reads no data/doc file); implement the frozen `C_req`/`z`/`r_1`/`D`/median/`FLAG`/verdict helpers it asserts (helpers live in the T-2 driver module and are imported, never duplicated). No `src/` touch. Per `AGENTS.md` §5.7: simplest implementation that is scientifically correct — no checksums, no atomic writes, no locking, no retry framework, no caching.
2. **T-2** — Proxy driver `comparison_bench/src/comparison_bench/cli/proxy_nonstat_sampler.py` (new file only): stdlib + numpy; frozen S-N1…S-N6 + §4 formulas + §5 rule as the only logic; argv takes exactly `--root workspace/proxy_nonstat_<uuid8>` + dual `--execute-synthetic --execution-authorized` flags (refuse without both; refuse any decoder/timing flag); startup path-gate refuses any input path outside the fresh root and any `.ttbin`/`.npz`/`.parquet`/`rows.json` path; root gate accepts only `workspace/proxy_nonstat_[0-9a-f]{8}` and refuses `results/`/`outputs_comparison`/existing-root collisions; runs control + drift arms (`R = 500` each, paired seeds), writes D-1 + D-2 + D-3 records; decoder-call count hardcoded `0` with an assertion. No `src/` touch.
3. **T-3** — Front cost-arithmetic gate (compute before any draw): evaluate the §3.5 derivation (`C_req = 45`, `U_assume(0) = 51.0`, `51.0 > 45`, `12240 > 10800`) from the frozen numbers with zero timing, record it in `EXPLORATION_LOG.md` **before** the first T-2 draw, then append the honesty `O_err`/`O_cost`/`FLAG` computation after the draws. Any draw before the recorded arithmetic verdict is a STOP. BLOCKED until grant.
4. **T-4** — Single mechanical verdict + independent batch-end review → D-4 (`BATCH_END_REVIEW.md`) against PC-01…PC-08 with the §11 ceiling quoted verbatim; FAIL ⇒ rework + re-review, never publish-then-patch; **zero promotion before PASS**. BLOCKED until T-1…T-3 complete.

**Size note for orchestrator**: small enough to implement directly — one additive numpy-only driver (~120 lines: binomial draws, three frozen statistics, median aggregation, arithmetic + flag + verdict) plus one fake-only test with hand-computable constants. No full pipeline needed. No `/opsx-explore` needed: every primitive (lengths, seeds, laws, formulas, bands, caps, prices, flag, rule, budget chain) is frozen above; the nine DD-items are the only planner interpolation and each is marked. **[DD-9: PC-08 machine-check extends the user-frozen four token groups with `10/240` + `35/35` (Non-Goals enforcement); strictly stronger than requested, still compliant.]**
