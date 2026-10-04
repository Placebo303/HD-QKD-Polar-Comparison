# NEXT-STEP-OPTIONS — ranked options map (planner record, authorizes nothing)

- **Track**: documentation-only (`AGENTS.md` §1.2 matrix: no track gate). This document **authorizes nothing, schedules nothing, closes no route**, promotes no evidence, and grants no execution.
- **Branch / date**: `formal-ir-v72p1-addendum-clean`, 2026-09-27. No commit, no push by the author.
- **Method**: read-only verification against the cited records. No decoder, construction, or scientific command was run; no `.ttbin` or channel bundle was opened (the `workspace/s0_1bbe38ac/` Stage-0 arithmetic JSONs are neither — they were read read-only to verify the Stage-0 figures cited below; nothing under `workspace/` was written).
- **First principle served** (`AGENTS.md` §1.1): every option below is judged by correction success/FER, leakage/efficiency, throughput/runtime, memory cost, and accepted-frame net key yield — in that order — with the shortest scientifically valid path preferred.

## §0 Goal / Non-Goals / Impact Scope / Acceptance Criteria / Tasks

### Goal

Give main a complete, ranked map of what the project can do next — each candidate with its motivating evidence, relative cost, what it would settle, and its cheapest discriminating test — plus falsification/decision rules, dependency ordering, cost perspective, publishability risk, a labelled recommendation, and the decisions that belong to the user.

### Non-Goals

- No authorization, execution, decoder/construction call, `.ttbin`/bundle open, commit, or push.
- No route closure, qualification, publication number, method ranking, or acceptance of any method.
- No modification of any runner, construction, decoder, config, existing workspace root, `docs/NOW.md`, `docs/decision-log.md`, `openspec/`, or `AGENTS.md`.
- No use of the void HDC / void Layered-Binary figures as baselines; no `f_eff` for those families; no single-point `f_eff ≤ 1.3` certification language.

### Impact Scope

- **Written**: exactly one file, `docs/research_cycles/NEXT-STEP-OPTIONS/PROPOSAL.md` (this file; parent directory is new and additive).
- **Read-only inputs cited**: `docs/research_cycles/CHAN-QUALITY-SURVEY/RESULT.md` + `INDEPENDENT_ACCEPTANCE.md`; `docs/research_cycles/PERPLANE-BINARY-LDPC/STAGE0_PACKET.md` + `workspace/s0_1bbe38ac/S0_SUMMARY.md` + `STAGE0_LOG.md`; `docs/research_cycles/M0-REALFRAME/RESULT.md` + `INDEPENDENT_ACCEPTANCE.md`; `docs/research_cycles/M2-REALCOMP/CORRECTION_RESULT.md` + `CORRECTION_INDEPENDENT_ACCEPTANCE.md` + `BACKEND_TRACE_REPORT.md`; `docs/research_cycles/M2-HDCASCADE-SYNTH/BATCH_END_REVIEW.md`; `docs/research_cycles/M3B-NESTED-PAIRED/PACKET.md`; `docs/research_cycles/M3C-REAL-U2-2M/STOP_RECORD.md` + `PREREG_AND_AUTH.md` + `PRE_EXECUTE.md`; `docs/research_cycles/M3D-ITER250-SYNTH/BATCH_END_REVIEW.md` + `PACKET.md`; `docs/research_cycles/M1-FINITE-LENGTH/RECOMPUTE_VERDICT.md`; `docs/research_cycles/V80-NBLDPC-JAN21/LITERATURE_DIRECTION_MEMO_20260921.md`; `docs/research_cycles/PERPLANE-BINARY-LDPC/PROPOSAL.md`; `openspec/changes/m2real-accounting-correction/proposal.md`; `docs/NOW.md`; `docs/decision-log.md` (tail entries 2026-09-24…27).
- **Untouched**: everything else.

### Acceptance Criteria (for this document)

- AC-1: every settled fact carries provenance (file + section/line where available); every unverifiable item is labelled as such (§8).
- AC-2: all six required candidates appear with what/evidence/cost/settles/cheapest-test; no required candidate silently dropped (§1).
- AC-3: each option has a falsification test and a decision rule, with sequencing dependencies stated (§§1–2).
- AC-4: the Stage-0 KILL scope statement is precise about what was priced and what remains open (§3).
- AC-5: dependency/ordering analysis declares EXPLORE vs DECIDE per `AGENTS.md` §1.2 for each option (§4).
- AC-6: cost perspective in CPU-hours and calendar terms with the M3C reference scale and the cheap-channel-work observation (§5).
- AC-7: honest publishability risk + fallback, including what void baselines do to the G0=(B) deliverable (§6).
- AC-8: labelled recommendation + rejected-recommendation alternatives (§7); user-owned decisions listed (§9).

### Tasks (candidate work-packet sketches — each needs its own frozen packet + grant; nothing here is delegated)

- T-N1 (EXPLORE): synthetic-proxy recalibration packet (measured-rate ±1-asymmetric sampler; gap-closure test vs M0 real).
- T-N2 (EXPLORE analytic, seconds): joint-but-structured budget pricing (joint-entropy ledger vs 1104-bit budget).
- T-N3 (EXPLORE, zero-decode): u1-path probe (argmax-u1 accuracy on real eval frames; full10-mismatch accounting).
- T-N4 (EXPLORE/EXPLORE_HEAVY): throughput ledger + vectorization sizing (iteration-count-gated, repeated wall measurements).
- T-N5 (DECIDE, conditional): M3C-successor real-frame canary (single-graph Stage-1-only; gated on T-N4 sizing).
- T-N6 (EXPLORE_HEAVY, conditional): M3B re-run on the recalibrated synthetic (only if T-N1 closes the gap).
- T-N7 (DECIDE, conditional): longer-frame (n=2048) study (only after T-N1 + T-N4; science-input change).

---

## §1 Ranked options map

Ranking logic: (a) first-principle leverage per unit cost — what most reduces uncertainty about real-frame correction at ≤ budget; (b) dependency position — unblockers rank above the work they unblock; (c) reversibility and cost — seconds-scale analytic/EXPLORE probes rank above hours-scale DECIDE executions. Rank is a planning order, not a decision; main may reorder.

### Option A — Recalibrate the synthetic channel to the measured per-plane ladder (rank 1, unblocker)

- **What it is**: replace the frozen-bundle synthetic sampler (known-optimistic proxy) with a sampler drawn from the five measured captures' per-plane rates `p_k` (§2.1 of `STAGE0_PACKET.md`) plus the measured ±1 sign asymmetry per source (offset-sign rule, `CHAN-QUALITY-SURVEY/RESULT.md` §3), explicitly labelled proxy; re-freeze all downstream synthetic work on it.
- **Motivating evidence**: M0's frozen-route mechanical conclusion — real frame error worse than X1-synthetic in 5 of 6 arms, 0 better (`M0-REALFRAME/RESULT.md` §§3–3.1); the M0 D1 verdict that the synthetic channel shall not serve as a development proxy until conditioning is done. Every synthetic result to date (M3B, M3D, P1) sits on the optimistic proxy.
- **Relative cost**: cheapest class — sampler construction + validation arithmetic, EXPLORE, single-CPU minutes; no decoder needed for the calibration comparison itself (reuse frozen M0/M3B rows read-only).
- **What it would settle**: whether the real-vs-synthetic gap is explained by the rate/asymmetry mismatch (recalibrated synthetic Stage-1 nonexact distribution ≈ M0 real) or by deeper structure (gap persists → conditioning question is harder than rates alone).
- **Cheapest discriminating test** (before committing to the route): build the measured-rate asymmetric sampler; draw the M3B 240-frame seed set through Stage-1 m=200 cold and compare the nonexact-count histogram against M0-2M real rows. Gap closes substantially → proxy restored, invest (Options C, E depend on this). Gap unmoved → abandon recalibration-as-rates; escalate to per-superframe conditioning research.

### Option B — Complete the real-frame test of the M3 code family, M3C successor (rank 2, most decision-relevant unknown)

- **What it is**: a successor to the stopped M3C two-arm diagnostic (`M3C-REAL-U2-2M/STOP_RECORD.md`): nested 200+8 graphs on the same 2M VAL+HOLD eval frames, redesigned so it can finish inside the wall budget (fewer arms, staged gates, or reduced Stage-2 scope — exact design belongs to its own packet).
- **Motivating evidence**: M3C-R1 completed (383/383; 372 final u2 successes, 11 failures) but R2 walled with 24 frames unknown and no 383-frame FER (`STOP_RECORD.md`); M3B's synthetic nested-graph gain (Stage-1 non-exact 84/240→10/240, 138/240→15/240, batch-end PASS, synthetic-only ceiling) has no real-frame counterpart. Whether the nested construction survives real frames is the single largest open question about the GF(32) line.
- **Relative cost**: most expensive class — M3C spent 4813 s (R1) + 5280 s (R2, incomplete) ≈ 2.8 CPU-hours for one 2M two-arm attempt with zero accepted conclusion; any successor is DECIDE with full gate contract (prereg + Pre-EXECUTE + execution + independent Pre-RESULT + acceptance), i.e. days of calendar including reviews.
- **What it would settle**: the real-frame u2 FER of the nested family on 2M (confirm/rescue-rate/falsify), which gates all further GF(32) code-design investment.
- **Cheapest discriminating test** (before committing to the full route): single-graph **Stage-1-only** real-frame canary on 2M — no Stage-2 rescue, one arm, ≈ half an M3C arm (~40 min single-CPU). If Stage-1 nonexact ≈ 39/383 (M3C-R1 scale), the rescue question survives and the full successor is worth pricing; if Stage-1 nonexact is far worse (e.g. >100/383), the nested family is in trouble on real frames and the full successor should not be funded. **Blocked on Option D sizing** (no successor packet before the wall budget is credibly sized).

### Option C — Further GF(32) code design, M3 line continuation (rank 5, synthetic-only until proxy fixed)

- **What it is**: continue the M3 nested-construction program (PEG degree/extension-length search, paired synthetic screening) that produced M3B's 84/240→10/240 gain.
- **Motivating evidence**: M3B batch-end PASS with two separately-reported instances, final failures 0/240 on synthetic (`M3B-NESTED-PAIRED/PACKET.md`); the Stage-0 KILL leaves GF(32) joint coding untouched (it priced only independent per-plane coding — §3).
- **Relative cost**: medium — synthetic construction + 240-frame screens per candidate, EXPLORE_HEAVY (M3B-scale: ~1–2 CPU-hours per two-arm batch); cheap per candidate relative to real-frame work, but unbounded if run as open-ended search.
- **What it would settle**: whether the nested-family synthetic advantage replicates across more graph instances and operating points — **not** whether it works on real frames (synthetic ceiling stands until Option A restores the proxy).
- **Cheapest discriminating test**: re-run the exact M3B paired comparison on the **recalibrated** synthetic (Option A output). Advantage persists → continue design; advantage evaporates → the M3B gain was proxy artifact, stop the line. **Value depends on Option A succeeding first** — running more frozen-bundle synthetic design without recalibration is discouraged.

### Option D — Throughput engineering (rank 3, load-bearing for all real-frame work)

- **What it is**: measure and attack the decode wall that stopped M3C (R2 `INCOMPLETE-wall` at 5280 s internal / 5400 s external; Stage-2 frame 160 interrupted after 3.79 s by the remaining-wall alarm) and the ~480–900× gap between single-threaded reconciliation (~366 symbols/s, derived from the b2f 2.80 s/block figure at `decision-log.md:4745` — itself flagged "derived, pending independent arithmetic review") and the source pair rate (~1.75–3.27×10⁵ pairs/s from M0 pair counts ÷ ~3 s acquisitions; gap arithmetic is the author's derivation, §8).
- **Motivating evidence**: M3C wall overrun proves throughput is not optional for any further real-frame work; M3D's timing probe failed to resolve whether a 250-iteration cap helps and its hypothesis-level negative was retracted (noise-scale margin: 11.0 s shortfall vs 7.3 s demonstrated same-batch offset, `M3D-ITER250-SYNTH/BATCH_END_REVIEW.md` §§2–4, escalation retraction at `decision-log.md:5078`); the literature memo's two throughput bases (Müller 6.7 kbit/s **raw acquisition**, never SKR/IR throughput — `LITERATURE_DIRECTION_MEMO_20260921.md` §§1–2; b2f ~1.83 kb/s single-thread decode at `decision-log.md:4745`) are non-interchangeable.
- **Relative cost**: low-to-medium — measurement and vectorization sizing are EXPLORE (hours); a backend change (`BpOsdDecoder` install/C++ build, env fingerprint) or parallelization is dearer and belongs behind measured headroom.
- **What it would settle**: the per-call wall distribution by stage (M3D measured Stage-1 synthetic; the M3C overrun was **Stage-2** — a scope mismatch the M3D review explicitly calls out), and whether a ≥3× speedup is available without changing scientific inputs.
- **Cheapest discriminating test** (before committing): iteration-count-gated, **repeated** wall ledger on frozen synthetic Stage-1 **and** Stage-2-shaped calls (M3D's design flaws repaired: repeat ≥3×, gate on deterministic iteration counts, same-day baseline). If a vectorization/prior-caching change shows ≥3× on the ledger, fund implementation; if the wall is dominated by irreducible per-iteration FFT-QSPA cost with no headroom, real-frame ambitions must shrink (fewer arms, canary-only) rather than grow. **Gates Option B.**

### Option E — Joint-but-structured layered design (rank 4, the route Stage-0 did not price)

- **What it is**: a decoder that treats the ten Gray planes jointly but with the measured structure baked in — single-plane-flip constraint (zero observed co-error), per-plane rates `p_k`, ±1 direction asymmetry — e.g. joint-syndrome Slepian-Wolf coding, conditional plane-by-plane decoding (quiet planes condition the LSB plane), or a GF(32) code with a single-plane-error prior. This is **not** the killed independent-per-plane scheme and **not** the structure-blind GF(32) mainline.
- **Motivating evidence**: the Stage-0 arithmetic priced **only** independent per-plane coding (§3); the channel finding (single-plane flips, LSB ≈ 50%, rates spanning 370–674×) is exactly the structure a joint-but-structured code would exploit; the per-plane `PROPOSAL.md` §§2.4/6 already isolates the `_P_ASSUMED = 0.02` uniform-prior defect as the likely cause of the LB 0.13% failure — a joint-structured decoder fixes priors **and** shares information across planes.
- **Relative cost**: analytic pricing is seconds (EXPLORE); design + synthetic screening is M3B-scale (EXPLORE_HEAVY); real-frame validation is M3C-scale (DECIDE). Staged accordingly.
- **What it would settle**: whether the ~0.5 bit/symbol "non-additivity tax" (Stage-0 coherence column) is recoverable by joint coding at ≤ 1104-bit budget.
- **Cheapest discriminating test** (analytic, run before any design): the joint-budget computation — at `f = 1.3`, joint requirement ≈ `1.3 × H(A|B) × 1024` ≈ `1.3 × 0.8257 × 1024 ≈ 1099 bits` on 2M vs the 1104-bit budget: it **fits** (marginally), where independent allocation needs 1875 bits. If this arithmetic holds under the packet's frozen formulas, the design direction is alive and worth a Stage-1-style packet; if backoff/finite-length analysis kills even the joint budget, abandon. This test costs nothing and should precede all other design spending.

### Option F — Attack the required entropy itself via the u1 path (rank 6, cheap probe)

- **What it is**: reduce `H(A|B) ≈ 0.826` bits/symbol from the u1 side, given `H(U1|B) ≈ 0.024` — the u1 layer carries little entropy but the current chain recovers it by unverified global argmax (M0 is a u2-only chain with u1 "via argmax, u1 正确率未验证"; M3C-R1 reports 168 full10 mismatches among 372 final-u2-success frames — the u1 recovery is observably lossy).
- **Motivating evidence**: `H(U1|B)` 0.02402–0.02491 across all five captures (`CHAN-QUALITY-SURVEY/RESULT.md` §§2–3); M3C `STOP_RECORD.md` full10 fields (168/372 R1, 150/352-known R2) show full-symbol reconciliation currently loses on u1 even when u2 succeeds.
- **Relative cost**: cheapest class — the accuracy probe below is zero-decode channel-level work (minutes, EXPLORE); acting on it (coding u1, better estimators) is design work comparable to Option E.
- **What it would settle**: how much of the 0.826 bits/symbol is u1-estimation loss vs irreducible channel entropy — i.e. whether a better u1 path buys meaningful budget headroom.
- **Cheapest discriminating test** (before committing): measure argmax-u1 error rate directly on the real eval frames (compare argmax `a>>5` estimate vs true Alice upper bits; no decoder, reconstructible `(a,b)` arrays). If argmax-u1 error is already ≪ 1%, the u1 path is nearly optimal and attacking it buys nothing → abandon. If it is several %, a coded/estimated-u1 direction earns a design packet.

### Option G — Longer frames, n = 2048 study (rank 7, added with justification)

- **What it is**: move the operating point to 2048-symbol superframes (plane blocks 2048 bits), motivated by M1-R4 (≈0.056 total saving at n=2048: 0.0188 finite-length + 0.0375 tag, `M1-FINITE-LENGTH/RECOMPUTE_VERDICT.md` §R4) and the literature direction memo's lengthening discussion (`LITERATURE_DIRECTION_MEMO_20260921.md` §5, first bullet).
- **Motivating evidence**: M1 recompute PASS_WITH_FINDINGS with the `f* ≈ 1.064` decomposition (code gap ~0.13, finite length ~0.06, tag ~0.075); Zhou scaling cited in the memo (longer is better down to 1.046 at 2³⁰).
- **Relative cost**: high — doubles decode work per frame, changes frame/tag accounting (science-input change ⇒ DECIDE for any real-frame leg), and the projected saving (~0.056) does not by itself close the 1875-vs-1104 independent-coding gap.
- **What it would settle**: whether finite-length + tag amortization recover enough budget to matter at our noise (no paper reports `f` at our noise/alphabet — memo §3 — so this must be measured, not extrapolated).
- **Cheapest discriminating test**: single synthetic n=2048 arm on the **recalibrated** channel (EXPLORE_HEAVY, one construction, 240 frames) before any real-frame or accounting change. No gain at matched disclosure → abandon lengthening. **Depends on Options A (proxy) and D (throughput, since frames cost ~2×).**

### Explicitly deprioritized (per §1.1 first principle — recorded so nothing is silently dropped)

- **D-1 headline resolution** (which tag total is the headline column): accounting hygiene, not correction performance; stays DEFERRED, non-blocking.
- **Verifier/audit hardening** (real Toeplitz verifier for HDC, sidecar/key-discipline retrofits except as frozen into future packets): the HDC path needs a *converging cascade*, not just a verifier (D-4(ii) rejected — `decision-log.md:5094`); backend-trace requirements are already recorded (`BACKEND_TRACE_REPORT.md` §13) and bind future packets without new spending now.
- **More frozen-bundle synthetic GF(32) search** without recalibration: spends the medium-cost class on a known-optimistic proxy.

---

## §2 Falsification tests and decision rules (per option)

| Option | Abandon if | Invest if | Depends on |
|---|---|---|---|
| A — proxy recalibration | recalibrated synthetic still misses real Stage-1 behavior (gap unmoved) | gap closes substantially on frozen seed sets | nothing; unblocks C, G |
| B — M3C successor | Stage-1-only canary shows nonexact far above M3C-R1 scale, or D sizing shows no feasible wall | canary ≈ M3C-R1 scale **and** wall budget credibly fits | D (wall sizing) |
| C — GF(32) design | M3B advantage evaporates on recalibrated synthetic | advantage persists across instances on recalibrated synthetic | A must succeed first |
| D — throughput | wall dominated by irreducible per-iteration cost, no ≥3× headroom found | ≥3× demonstrated on repeated iteration-gated ledger | nothing; gates B |
| E — joint-structured | even joint budget fails under frozen formulas + backoff | joint arithmetic fits (≈1099 vs 1104) and survives backoff sensitivity | nothing for analytic; synthetic screening needs A |
| F — u1 path | argmax-u1 error ≪ 1% (nothing to buy) | argmax-u1 error several % (headroom exists) | nothing (independent cheap probe) |
| G — longer frames | no gain on recalibrated synthetic n=2048 arm | clear gain worth the ~2× decode cost + accounting change | A (proxy), D (throughput) |

Cross-dependency summary: A → C, G (and sharpens E-screening); D → B (and G cost); E-analytic, F-probe, A are mutually independent and all cheap — they form the natural parallel front. B is terminal-expensive and last.

---

## §3 What the Stage-0 KILL does and does not rule out (precise)

**What was priced** (`STAGE0_PACKET.md` §§3–5; evidence `workspace/s0_1bbe38ac/S0_SUMMARY.md`, `STAGE0_LOG.md`): **independent** per-plane coding only — ten separate binary LDPC codes, per-plane parity `m_k(f) = ceil(1024·f·h2(p_k))` at the frozen `f` grid, disclosure total `Σ_k m_k + 64` against the 1104-bit budget, decided on CQ-J21c at `f = 1.3` nominal under §5.2. Result: every plane feasible individually, but the total is **1875 > 1104 (excess 771 bits)** — KILL without reaching any backoff column; all five sources fail nominal by ~690–772 bits. The coherence mechanism is visible: `Σ_k h2(p_k)` exceeds measured `H(A|B)` by **+0.498…+0.533 bits/symbol** on all five captures (10-plane sums 1.296–1.357 vs `H(A|B)` 0.791–0.826). Status caveat, stated plainly: the independent batch-end review (S0-01…S0-08) is **pending** (`STAGE0_LOG.md` close-out) — treat the KILL as **provisional** until it lands.

**What the KILL rules out**: H1's arithmetic precondition as framed — independent per-plane rate-adaptive binary LDPC at `f = 1.3` nominal on this channel and budget. No Stage-1/2/3 work under that packet follows (KILL is terminal for the packet, exactly as MARGINAL would be).

**What remains open** (each needs its own pricing before design spending):

1. **Joint/conditional coding across planes** — the KILL arithmetic sums marginal entropies; it says nothing about the Slepian-Wolf region near `H(A|B)`. Pricing needed: joint-budget computation (§1, Option E test) plus finite-length backoff for the chosen joint family.
2. **Longer blocks** — `n_plane = 1024` was frozen into every `m_k`; changing block length changes finite-length margin and tag amortization (new accounting, DECIDE for real frames). Pricing needed: n=2048 construction-gate + backoff model, not extrapolation from literature at other noises.
3. **Non-uniform / staged disclosure** (blind stages, rescue-triggered syndromes, per-block adaptation) — priced differently from one-shot `Σ m_k`; note the Scarinzi closure (per-block spread ≈ 3 bits/block, no usable headroom at n=1024) already constrains the adaptation variant.
4. **Attacking `H(A|B)` itself** — better u1 estimation/coding (Option F); the KILL takes measured `p_k` and `H(A|B)` as inputs and cannot rule out changing them.
5. **Different binning / framing** — all `p_k` are measured at the imposed 200 ps / 1024-bin convention; re-binning is a science-input change (own DECIDE packet with alignment re-derivation), explicitly out of Stage-0 scope (`STAGE0_PACKET.md` §12.4).

**Standing citation discipline** (from the survey acceptance): the channel premise may be cited only as "**zero observed cross-plane co-error; single-plane-flip structure**" (triple: off-diagonals exactly 0.0, popcount only on {0,1}, `expected_planes_flipped_per_error` = 1.0 both routes), with the detection-floor caveat (~10⁶ pairs exclude only multi-plane rates above ~10⁻⁶) whenever the word "independent" is used; the negative only as "**no measured easier point among the five captures; the unmeasured groups supply no evidence of one on recorded grounds**" (`CHAN-QUALITY-SURVEY/INDEPENDENT_ACCEPTANCE.md` §§5–8, Part B).

---

## §4 Dependency and ordering analysis (with EXPLORE/DECIDE per `AGENTS.md` §1.2)

- **Independent cheap front (run in any order, all EXPLORE)**: A-recalibration build, E-analytic joint pricing (seconds, zero data contact beyond frozen JSONs — EXPLORE analytic), F-probe (zero-decode channel-level work on already-persisted `(a,b)`-derived statistics — EXPLORE; any *new* raw-data contact beyond frozen eval frames would escalate to DECIDE, so the probe packet must fence its inputs).
- **Sequential**: A → C-screening and A → G-synthetic (synthetic work is gated on the restored proxy; the route-closing decision on any synthetic gate is itself DECIDE per the matrix). D-sizing → B-successor (no real-frame packet before the wall is credibly sized). B-canary → B-full (canary result is the funding gate).
- **Blocked on something**: B-full on D and on explicit user DECIDE grant + Pre-EXECUTE/Pre-RESULT contract; G-real on A, D, and a science-input accounting change (DECIDE); any publication/report number on its own DECIDE claim packet.
- **Requires a DECIDE gate** (touches real data / is claim-bearing / expensive / formal): B in all forms (real-data development/validation — full contract: accepted prereg → Pre-EXECUTE with exact command/budget/output-absence/explicit grant → one execution + result record → independent Pre-RESULT → main acceptance); G-real (science-input change + real frames); any formal qualification or paper-number extraction.
- **EXPLORE**: A, E-analytic, F-probe, D-measurement (packet+prompt, machine root, one append-only log, one batch-end review; `EXPLORE_HEAVY` annotation for C/G synthetic batches exceeding ~3× the Stage-0 ceiling). The route-closing interpretation of any EXPLORE batch is DECIDE and is not taken inside the batch.

---

## §5 Cost perspective (rough CPU-hours and calendar; real-frame work is the expensive class)

Reference scales (measured, single-CPU, threads pinned):

- **M3C real-frame attempt** (the reference unit): R1 4813 s + R2 5280 s (incomplete) ≈ **2.8 CPU-hours** for one 2M two-arm attempt yielding no accepted conclusion; calendar ≈ 1 day including Pre-EXECUTE/terminal-audit. Any successor budgets in units of M3C.
- **M0 three-source real-frame loop**: per-source walls 3409/3696/4672 s, 1750 decodes, batch wall ~4676 s parallel ⇒ **~3.3 CPU-hours** total; calendar several days with re-review (`M0-REALFRAME/RESULT.md` §§2–3).
- **Channel-level work is cheap even though decoding is not**: Arm-B survey 77–200 s/source, peak RSS ≤ 0.62 GiB, zero decoders (`CHAN-QUALITY-SURVEY/RESULT.md` §3); Stage-0 0.39 s outer / 0.015 s internal (`STAGE0_LOG.md`). The five captures' `(a,b)` arrays are reconstructible without any decoder, so Options A-build, E-analytic, and F-probe live in the **seconds-to-minutes** class.
- **Synthetic design work is the middle class**: M3B-scale two-arm batch ~1–2 CPU-hours (EXPLORE_HEAVY); M3D 16-call diagnostic ~513 s single-arm. Per-candidate cost is bounded; the risk is open-ended candidate count, not unit cost.
- **Calendar rule of thumb**: EXPLORE probes (A/E/F/D-measurement) ≈ days including batch-end review; DECIDE real-frame executions (B/G-real) ≈ 1–2 weeks each including both independent reviews and acceptance. Reviews, not computation, dominate the calendar — another reason to front-load the cheap discriminating tests.

---

## §6 Publishability risk and fallback (honest)

**Current position**: paper positioning is "measured efficiency curve plus same-data binary comparison" per the G0=(B) decision (`docs/NOW.md` §2, decision 2026-09-22). Both binary baselines are now void — HD-Cascade 0/28,000 (`void-stub-artifact` + `void-no-correction`) and Layered-Binary 36/28,000 (`void-no-correction`), with LB backend UNKNOWN and NOT RECOVERABLE — so **no comparison column may be filled for either baseline** (`decision-log.md:5102`, `CORRECTION_INDEPENDENT_ACCEPTANCE.md` Part B). The same-data comparison half of the headline currently has no publishable content.

**What that does to the deliverable**: as things stand the citable package is (i) the M0 measured GF(32) real-frame efficiency/FER curve (u2-only, argmax-u1-unverified — F9(i) annotation mandatory), (ii) two documented negative implementation results, (iii) the accepted channel-structure finding (single-plane-flip, no easier measured point), (iv) the provisional Stage-0 KILL arithmetic, and (v) the finite-length decomposition. That is a **measurement + negative-results paper**, not the promised "measured curve plus same-data binary comparison." It is publishable in a weaker venue/form only if main explicitly re-scopes; it does not satisfy G0=(B) as written.

**What would restore the deliverable**, in ascending cost order: (a) any binary decoder (corrected-prior per-plane, joint-structured, or improved-LB with full key discipline) correcting real eval frames at measured FER with ledgered disclosure — even without beating GF(32), a *working* same-data binary column restores a comparison; (b) an M3C-successor real-frame positive (nested GF(32) FER confirmed with rescue accounting) strengthening the mainline half while (a) is pursued; (c) a joint-structured design win (Option E) delivering both halves at once.

**Risk that none of this produces a publishable result**: stated plainly — the channel sits at SER ≈ 0.24–0.25 with no easier measured point; independent per-plane coding is arithmetically dead by ~770 bits; joint coding fits only marginally (~1099 vs 1104 before backoff); real-frame decoding runs at ~10² symbols/s against a ~10⁵ pairs/s source; and every positive signal to date (M3B, b2f 0/240) is synthetic on a known-optimistic proxy. It is genuinely possible that no binary scheme corrects these frames at ≤ budget within attainable effort. **Fallback position** if that materializes: publish the measurement record as-is (real-frame GF(32) curve + channel structure + KILL arithmetic + two void baselines with the architectural explanations now in hand — the `_P_ASSUMED` prior mismatch for LB, the hardcoded gate for HDC) as a well-documented negative result constraining the field, and redirect the program to easier channels or longer frames as a new proposal, not as an extension of this one.

---

## §7 Recommendation (main's to accept or reject — not a decision)

**Recommended**: fund the cheap parallel front first — **A (proxy recalibration) + E-analytic (joint-budget pricing) + F-probe (u1 accuracy)**, all EXPLORE, no decoder, completable in days — and **hold B (M3C successor) until D (throughput sizing) reports**. Reasoning: A determines whether all synthetic evidence to date means anything; E-analytic costs seconds and decides whether any binary direction survives Stage-0 at all; F-probe costs minutes and bounds the u1 headroom; D is load-bearing for B, and B is the most expensive item on the map — sequencing B after D avoids a second M3C-scale wall stop. Total front cost ≈ CPU-minutes + three batch-end reviews.

**If the recommendation is rejected, run these two-to-three instead**:

1. **D-sizing + B-canary directly** (skip the proxy work): accept that synthetic is untrusted, bet the program on real frames only — Stage-1-only 2M canary after wall sizing. Fastest path to a real-frame answer; risks another expensive stop if the wall estimate is wrong.
2. **E full design track immediately** (skip A): bet that joint-structured coding is the answer regardless of proxy fidelity, proceeding straight to a Stage-1-style construction/screening packet on measured-rate synthetic. Justified only if main judges the joint arithmetic (≈1099 vs 1104) compelling enough to fund design before proxy repair.
3. **G-synthetic single arm** (skip A and E): bet on longer frames as the dominant lever (M1-R4 + literature), testing n=2048 on the current synthetic. Cheapest if main believes finite length, not structure, is binding — but note no paper reports `f` at our noise, so this is the weakest-evidenced bet.

---

## §8 Verification appendix (what was checked; discrepancies; §8 of the return contract)

- **Verified from cited records**: facts 1 (survey RESULT §§2–4 + acceptance Part A/B, fenced forms, detection-floor caveat at acceptance §6), 2 (same, plus §5 recomputation rows), 3 (S0_SUMMARY tables + STAGE0_LOG: 1875 vs 1104/excess 771 on CQ-J21c §5.2; coherence gaps +0.4978…+0.5334; KILL provisional — review pending), 4 (M0 RESULT §§2–3: 16/383 2M-m208, Wilson [0.025875, 0.066776]; min measured `f_eff` 1.464047 on the 1p5M-m207 arm; 5-worse/1-consistent table §3 + acceptance re-review PASS), 6 (HDC 0/28,000 + gate cites via CORRECTION_RESULT §5 + HDC batch-end FAIL B1/H1–H2; LB 36/28,000 = 12+7+5+6+3+3 with block FER 0.9963–0.9995 via correction acceptance Part B; MAC-10/D-4/D-5 void statuses via proposal + decision-log 5094–5116; LB architectural explanation as *change in explanation, not status* via acceptance §6–7 + survey acceptance §7 fenced), 7 (M3B synthetic 84/240→10/240, 138/240→15/240, batch-end PASS, synthetic-only ceiling via M3B PACKET; M3C STOP_RECORD R1 372/383-final-u2-success, R2 24-unknown/no-FER; M3D batch-end + escalation retraction at BATCH_END_REVIEW §§2/4/6 and decision-log 5078–5084), 9 (M1 RECOMPUTE_VERDICT R1–R4: f*≈1.064 rows, decomposition code-gap ~0.13/finite ~0.06/tag ~0.075, PASS_WITH_FINDINGS + H-basis caveat at R3-Finding and NOW.md §3), 10 (D-1…D-5 via decision-log 5094–5116 + NOW.md §5; `f_eff ≤ 1.3` ban via NOW.md §7.1 `N_req`-vs-key-eligible line; no-ranking rule via correction acceptance §§5–6 + NOW.md §7.4).
- **Could NOT be verified as stated (briefing-supplied, carried with caveats in §§1/5)**:
  - Fact 5's "**roughly 2–4×**" proxy-optimism factor: *direction* verified (M0 5-worse/1-consistent/0-better); no 2–4× error-rate factor found in the cited records (bundle never opened per constraint; synthetic SER unknown in-repo). Treat as briefing-supplied magnitude, not a measured ratio.
  - Fact 3's "**about 1.6× restricted to the five planes**": verified nearby values — 10-plane `Σh2/H(A|B)` = 1.642 on CQ-J21c (1.3559/0.8257) and planes-0–4 subset ≈ 1.55 (1.2782/0.8257, author's subset arithmetic from the frozen S0 table) — but the exact "five planes the alphabet codes" subset definition was not found verbatim; approximately consistent, subset unspecified.
  - Fact 8's "**≈366 symbols/s** vs **1.75–3.27×10⁵ pairs/s**, gap **480–900×**": derived, not directly quoted — 366 = 1024/2.80 from the b2f figure at `decision-log.md:4745` (itself flagged "derived, pending independent arithmetic review"); pair rates = M0 pair counts ÷ ~3 s acquisitions; gap = ratio of the two derivations. The memo citation verifies the two *bases* (6.7 kbit/s raw acquisition vs single-thread decode) and their non-interchangeability, not these exact numbers.
- **Discrepancies found (file + line)**:
  - `decision-log.md:5122` ("legacy value **is an artifact of** the old pairing rule and pipeline") vs `CHAN-QUALITY-SURVEY/INDEPENDENT_ACCEPTANCE.md` N-9 (cause **beyond the recorded differences is not established**; RESULT.md §2.3 as amended: "unfreezes under frozen chain; recorded differences are pairing rule + pipeline; further cause unestablished"). The acceptance's weaker wording controls; cite the N-9 form.
  - `STAGE0_PACKET.md` §5.3 named MARGINAL "the most likely outcome"; execution returned KILL (all sources fail nominal by ~690–772 bits). Recorded as surprise in `STAGE0_LOG.md` close-out, not a defect — the table was frozen before comparison per §5.
- **Blocker**: none — no command was run (no failing command to report).

---

## §9 Decisions that belong to the user (not to this planner)

1. **Which options to fund and in what order** — including whether to accept the §7 recommendation or one of its alternatives.
2. **Whether the provisional Stage-0 KILL binds planning now**, or waits for the pending independent batch-end review (S0-01…S0-08).
3. **Whether to authorize any DECIDE real-frame work** (B-canary/B-full, G-real): exact wall budget, arm scope, and grant wording — per-execution authorization stays with the user under `AGENTS.md` §§3/10.3.
4. **Throughput investment level**: sizing-only vs implementation (vectorization/caching) vs backend change (`BpOsdDecoder` install) vs parallelism — and its budget.
5. **G0=(B) stance under void baselines**: hold the "curve + comparison" headline and fund restoration (options A/B/E), or re-scope to a measurement + negative-results deliverable (fallback in §6).
6. **Whether longer frames (n=2048) enter scope** as a science-input/accounting change, and under which packet.
7. **Any ranking, qualification, or publication claim**: none follows from this document; each needs its own DECIDE claim packet and explicit grant.

---

## Correction 2026-09-28 — joint-budget figures (append-only; §§0–9 above preserved)

- §1 Option E line 92 ("`≈1099 bits` … it **fits** (marginally)"): the `≈1099` is the un-ceiled ideal `1.3 × 0.8257 × 1024`. The correct ceiled total is `ceil(1099.143…) = 1100`, which fits the 1104-bit budget by **about 4 bits, not 5**. One-bit proposal-framing difference; no decision rests on it.
- §2 decision table line 126 ("joint arithmetic fits (`≈1099 vs 1104`) **and survives backoff sensitivity**"): the backoff-survival half was never computed and is not supported — corrected: the joint total fits nominally by about 4 bits (`1100 vs 1104`) and **fails the `+20%` backoff column by about 215 bits** (`1319 vs 1104`). Corrected figures per `JOINT-PRICING/PREREG_AND_AUTH.md` §17.2; the joint stage is executed-but-miscounted, and formal re-evaluation needs a new packet and grant, not an edit.
- Line 182 ("joint coding fits only marginally (`~1099 vs 1104` before backoff)"): carries no backoff-survival claim (it is already qualified "before backoff"), so only the number is corrected here — ceiled total `1100`, margin about 4 bits. §6 fallback and §7 recommendation wording is otherwise unchanged.
