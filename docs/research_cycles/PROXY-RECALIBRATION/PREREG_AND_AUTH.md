# PROXY-RECALIBRATION — Frozen Executable Packet (Packet A)

- **Status**: FROZEN — awaits Pre-EXECUTE measurement + execution under the grant below (§14). This packet authorizes nothing by itself.
- **Track**: **EXPLORE, annotated EXPLORE_HEAVY for cost** — justification against `AGENTS.md` §1.2 in §0.1. The route-closing interpretation of the result is DECIDE and is not taken inside this batch.
- **Proposal authority**: `docs/research_cycles/NEXT-STEP-OPTIONS/PROPOSAL.md` §§1 (Option A), 2 (row A), 4, 5, 8. This packet freezes what that document sketched; it redesigns nothing. Any conflict between this packet and the proposal is a STOP (§9), not a patch license — with one recorded planner correction in §13.2 (sampler structure) and one resolved ambiguity in §13.3 (decode vs no-decode).
- **Branch**: `formal-ir-v72p1-addendum-clean`. No commit, no push by the operator.
- **Order note (main's judgement, recorded per tasking)**: **Packet A runs first because it repairs a root cause** — every synthetic result to date sits on the known-optimistic proxy, so no downstream synthetic work means anything until proxy fidelity is tested.

---

## §0 Goal / Non-Goals / Impact Scope / Classification

### Goal

Test whether a synthetic generator calibrated to the **measured** per-plane ladder reproduces the real frame-error shortfall, and therefore whether synthetic can become a trustworthy development proxy again. Concretely: take the M3B-R1 construction and its 240 paired synthetic frames for one fixed graph instance, regenerate the same frames through a sampler whose symbol error rate and ±1 asymmetry are the **measured** CQ-J21c values rather than the frozen bundle's, run Stage-1 m=200 cold with the identical graph/decoder/settings, and compare the regenerated Stage-1 nonexact count against the M3B-R1 baseline (same frame identities) and against the M0-2M real result.

### Non-Goals

- No `.ttbin` open, no channel-bundle open (`gamma_f03.npz`, `gamma_f03_pb.npz`, any `x1_*.npz` — named here only to forbid them), no raw-data contact of any kind (§2.3).
- No Stage-2 rescue, no second graph instance (M3B-R2 explicitly out of scope), no new PEG construction, no decoder-setting change.
- No FER, efficiency, leakage, `f`, SKR, or key figure for any method; no method comparison or ranking; no claim that any code improves (§11).
- No route closure, qualification, publication number, or acceptance of any method.
- No modification of any runner, construction, decoder, config, existing workspace root, `docs/NOW.md`, `docs/decision-log.md`, `openspec/`, or `AGENTS.md`.
- No commit, no push.

### Impact Scope

- **Written by this stage**: exactly two new repo files — `comparison_bench/src/comparison_bench/cli/proxy_recal_sampler.py` (additive sampler + Stage-1 driver, T-PA01) and `comparison_bench/tests/test_proxy_recal_fake.py` (fake-only test, T-PA02) — plus this packet (already written by the planner), plus all execution outputs inside one fresh additive root `workspace/proxy_recal_<uuid8>` (§6).
- **Read-only inputs**: the §2 frozen list only. Nothing else is opened for content.
- **Untouched**: `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/outputs_comparison/`, every existing `workspace/` root, `docs/NOW.md`, `docs/decision-log.md`, `openspec/`, `AGENTS.md`.

### §0.1 Track classification: EXPLORE (EXPLORE_HEAVY cost annotation) — justification against `AGENTS.md` §1.2

Packet A is **EXPLORE**, confirmed against the §1.2 applicability matrix row "Synthetic route gate (diagnostic/construction arms) → EXPLORE (`EXPLORE_HEAVY` if costly)":

1. **Input character**: the only channel inputs are already-persisted, non-sensitive channel *statistics* (float vectors and scalars in the §2 JSONs) plus the persisted M3B-R1 synthetic outcomes. The stage opens no `.ttbin`, no channel bundle, no `(a,b)` array, no raw data of any kind (§2.3). Regenerated frames are synthetic draws from the frozen sampler, not real data.
2. **Bounded and reversible**: one graph instance, 240 Stage-1 decodes, one CPU, wall ≤ 3600 s, RSS ≤ 2 GiB (§8); one fresh additive root, append-only (§6).
3. **No claim**: the §11 ceiling forbids every claim-bearing figure and every method statement. The only output is a proxy-fidelity word (PASS/MARGINAL/KILL, §5) about a *generator*, plus the paired transition table.
4. **Cost annotation**: the single-arm decode cost (~0.5–1 CPU-hour on the M3B-R1 measured basis, §8) trips the `EXPLORE_HEAVY` annotation, which is a cost note, not a third lifecycle. The route-closing interpretation of the word is DECIDE and stays outside this batch.
5. **Uncertainty default**: no concrete risk named here defaults this to DECIDE. The foreseeable failure modes (input drift, unrealizable rates, evidence-label error) are met by the size/mtime gate (PA-01), the validation-gate refusal (§3.5), the fake-only test (§10 P-3), and the batch-end review (PA-07) — not by escalation.

---

## §1 The frozen question (answerable YES or NO — proxy fidelity, not code improvement)

Take the M3B-R1 construction and its 240 paired synthetic frames for one fixed graph instance (`workspace/m3a_nested_200p8_20260926/arm1.json`, construction seed label 2026092001), and regenerate the same frame identities (seeds `2026096401+idx`, idx 0..239, stream `o1_blk:{seed}`) through a sampler whose symbol error rate and ±1 asymmetry are set to the **measured** CQ-J21c values rather than to the frozen bundle's. Run Stage-1 m=200 cold with the identical graph, decoder, and settings.

**Does the real frame-error shortfall close, partially close, or not close at all?** The shortfall's *direction* is verified (M0 D1: real worse than X1-synthetic in 5 of 6 arms, consistent in 1, better in 0 — `M0-REALFRAME/RESULT.md` §3); its *factor* is **main's own derivation, not recorded anywhere, and is never quoted as a number in this stage** (not in the packet, not in any deliverable, not in review).

The question is answered by the §5 rule, stated in terms of whether the regenerated channel's frame-error rate matches the real one — never in terms of whether any code improves.

---

## §2 Frozen input list (read-only)

Exactly these nine files. No other file is opened for content by the execution (code, docs, and configs cited elsewhere in this packet are frozen references carried from planning, not execution inputs).

| # | Path | Bytes | UTC mtime (measured) | Role |
|---|---|---|---|---|
| I-1 | `workspace/cq_15d6f160/CQ-20a.json` | 8632 | 2026-09-27 09:48:32 UTC | Context: 500K per-plane vector + H values (transcription discipline §2.2) |
| I-2 | `workspace/cq_15d6f160/CQ-20b.json` | 8628 | 2026-09-27 09:50:34 UTC | Context: 1M per-plane vector + H values |
| I-3 | `workspace/cq_4af91a87/ArmB/CQ-J21a/CQ-J21a.json` | 4221 | 2026-09-27 09:21:12 UTC | Context: Jan-21 1M vector + H values |
| I-4 | `workspace/cq_4af91a87/ArmB/CQ-J21b/CQ-J21b.json` | 4235 | 2026-09-27 09:24:52 UTC | Context: Jan-21 1p5M vector + H values |
| I-5 | `workspace/cq_4af91a87/ArmB/CQ-J21c/CQ-J21c.json` | 4211 | 2026-09-27 09:28:26 UTC | **Active sampler source**: the 2M corresponding capture (§2.1) |
| I-6 | `workspace/s0_1bbe38ac/S0_RESULT.json` | 19701 | 2026-09-27 11:59:00 UTC | Machine-readable per-source `p_k` vectors + `H(A\|B)` (same numbers, script cross-checks I-5 against I-6) |
| I-7 | `workspace/m3a_nested_200p8_20260926/arm1.json` | 64621 | 2026-09-25 17:44:07 UTC | The one fixed graph instance (M3B-R1; seed label 2026092001; ranks 200/208; four-cycles 0/0) |
| I-8 | `workspace/m3b_nested_paired_20260926/P1S1-R1_73d2f40a/rows.json` | 97545 | 2026-09-26 07:12:05 UTC | M3B-R1 per-frame baseline outcomes (per-seed Stage-1 success/fail; baseline k0 = 10/240) |
| I-9 | `workspace/m3b_nested_paired_20260926/P1S1-R1_73d2f40a/M3B_RESULT_M3B-R1.md` | 1344 | 2026-09-26 07:12:05 UTC | M3B-R1 arm summary (k0, wall 1767.651 s — the §8 budget basis) |

### §2.1 Active sampler numbers (transcribed from I-5/I-6; the files govern)

Corresponding-capture decision (frozen): M3B's frozen channel is "source 2M" (`M3B-NESTED-PAIRED/PACKET.md`); CQ-J21c is the Jan-21 2M source measured over the M0 VAL+HOLD eval region (`CHAN-QUALITY-SURVEY/RESULT.md` §1). **CQ-J21c is therefore the corresponding capture; its numbers drive the sampler.** The other four captures are context/provenance (transcription discipline), never sampler inputs.

- `ser` = **0.25375836** (sampler error probability).
- ±1 masses: `m_0` = 0.74624164, `m_+1` = 0.00143807, `m_-1` = 0.25232029 (−1-dominant; sign follows the per-source offset sign +50 — `RESULT.md` §3). Conditional slip direction: `q_-1` = 0.25232029/0.25375836 ≈ **0.99433**, `q_+1` ≈ 0.00567.
- Per-plane rates `p_k`, LSB-first index 0 = LSB plane: `[0.12711631, 0.06325473, 0.03222911, 0.01576779, 0.00784055, 0.00382211, 0.00202707, 0.00097146, 0.00050485, 0.00022438]`.
- H values: `H(U1|B)` = 0.02491156, `H(U2|U1B)` = 0.80076697, `H(A|B)` = 0.82567853 (context; no disclosure arithmetic is performed in this stage).
- Plane count is **ten** (`comparison_bench/src/comparison_bench/formal_ir/nonbinary_v25_gate.py:28` `BITS = 10`), correcting the earlier "nine" error. A future 9-plane treatment must freeze which plane is excluded and why.
- Five-capture `ser` range: **0.23856707–0.25433839** (≈ 0.24–0.25).

### §2.2 Input-transcription discipline (from `STAGE0_PACKET.md` §3 pattern)

The script reads the JSON values, never this transcription. Any mismatch between this transcription and the files is a STOP under §9 — the files govern. I-5 and I-6 must agree on the CQ-J21c `p_k` vector and `H(A|B)` bitwise; disagreement is a STOP (input drift), never an averaging license.

### §2.3 Zero-real-data / no-bundle statement

The channel bundle (`docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz`, `gamma_f03_pb.npz`) is **not an input and must not be opened** — not for reading, not for comparison, not for "checking" the sampler against it. Likewise no `.ttbin`, no `x1_*.npz`, no `pairs.parquet`, no `(a,b)` array, no raw data of any kind. The script's allowed-input gate (T-PA01) refuses any path outside the nine frozen above and any path ending in `.ttbin`, `.npz`, `.parquet`. The M3B-R2 arm, the P1 comparator roots, and all M0 roots except via the frozen M0-2M numbers in §4 are not inputs and stay untouched.

### §2.4 Standing citation discipline

Where the channel structure is invoked, use verbatim the standing fenced forms from `CHAN-QUALITY-SURVEY/INDEPENDENT_ACCEPTANCE.md` Part B:

- Channel premise: "**zero observed cross-plane co-error; single-plane-flip structure**" — triple evidence (off-diagonals exactly 0.0, Gray popcount only on {0,1}, `expected_planes_flipped_per_error` = 1.0 both routes), with the detection-floor caveat (~10⁶ pairs exclude only multi-plane rates above ~10⁻⁶) whenever the word "independent" is used.
- Negative: "**no measured easier point among the five captures; the unmeasured groups supply no evidence of one on recorded grounds**" — the short本体 form ("no easier data exists") is never cited alone.
- Legacy `0.098260`: an expectation under a different pipeline and pairing rule, never a result; in frozen-chain terms: "unfreezes under frozen chain; recorded differences are pairing rule + pipeline; further cause unestablished" (N-9 form). It is never cited as a measurement and never enters any comparison.

---

## §3 The sampler (frozen decisions, not code)

Slip-first Gray-consistent sampler S-1…S-5. Rationale in one line: every measured error is a ±1 bin slip (`other` mass ≈ 0), and a ±1 slip of a Gray-labelled symbol flips exactly one plane — so drawing slips reproduces the single-plane structure by construction, while the per-plane ladder emerges and is validated, not hand-imposed.

- **S-1 Source symbols**: Alice symbols i.i.d. uniform over the 1024 bins `{0,…,1023}`. Stated assumption with basis: under uniform source the emergent plane law is `p_k ≈ ser·2^{-(k+1)}`, which matches the measured CQ-J21c ladder within ~4% on planes 0–8 (planner's arithmetic on frozen numbers, e.g. `ser/2` = 0.126879 vs measured 0.127116). Source-marginal mismatch beyond this is a recorded limitation (§12.2), not a silent approximation.
- **S-2 Slip draw**: per symbol, draw `s ∈ {0,+1,−1}` with the measured CQ-J21c masses (`m_0` = 0.74624164, `m_+1` = 0.00143807, `m_-1` = 0.25232029). `Bob_bin = Alice_bin + s`, Gray-encode both sides with the frozen mapping reused verbatim (the same Gray function the survey used; no reimplementation, no alternative Gray variant — any ambiguity about which function is a STOP).
- **S-3 Edge rule**: saturate (`Bob_bin = clamp(Alice_bin + s, 0, 1023)`). Stated micro-choice with bound: affects at most `2/1024` of draws at one-sided edges; the §3.5 validation gate would catch any material distortion.
- **S-4 Cross-plane / cross-symbol structure**: draws are i.i.d. **across symbols**; within a symbol at most one plane ever flips (Gray adjacency), so cross-plane co-error is zero by construction — consistent with the fenced triple, stronger than observation. The word "independent" is not used for planes except with the §2.4 detection-floor caveat. Rejected alternative, recorded: literal independent-per-plane Bernoulli(`p_k`) would emit ≈ 2.0% multi-plane flips (`1 − Π(1−p_k) − Π(1−p_k)·Σ p_k/(1−p_k)` on the J21c vector) — ~20,000 events per 10⁶ pairs against exactly zero observed. It is refuted by the frozen evidence and is explicitly forbidden (§13.2).
- **S-5 Frame construction**: 240 frames × 1024 symbols, frame `idx` uses seed `2026096401+idx` and stream label `o1_blk:{seed}` — the identical identities as M3B-R1. One fixed graph instance (I-7), Stage-1 m=200 cold only, decoder settings frozen identical to M3B-R1 (`max_iter=300`, streak 3, exact-match success, no warm start, no genie/argmax u1). No Stage-2 rescue under this packet.
- **§3.5 Validation gate (machine gate before any decode)**: on a frozen `N_valid = 10⁶`-symbol draw (validation seed frozen at Pre-EXECUTE), require per plane `|emergent_k − p_k| ≤ max(5%·p_k, 5·SE_k)` with `SE_k = sqrt(p_k(1−p_k)/N_valid)` from the measured `p_k`, AND `|emergent_ser − 0.25375836| ≤ 0.003`. The `5·SE` arm exists because plane 9's known law-vs-measured residual (−9.5% relative, 2.3e-5 absolute) would spuriously trip a pure-relative gate. Breach ⇒ **REFUSE: no decode, no silent approximation**, retain evidence, return to main. Pass ⇒ proceed to the 240-frame Stage-1 run.

---

## §4 Comparison metric (frozen)

- **Exact comparator (paired, same frame identities)**: M3B-R1 baseline `k0 = 10/240` Stage-1 nonexact (I-8/I-9). Deliverable includes the 2×2 paired transition table old→new over the 240 matched seeds (same shape as M3B's paired table: old_success_new_success, old_success_new_failure, old_failure_new_success, old_failure_new_failure), plus stage-specific `undetected` (counts as failure, separately reported).
- **Real comparator (directional, stage-mismatched — stated openly)**: M0-2M m=208 arm: 16/383 fails, Wilson 95% CI **R = [0.025875, 0.066776]** (`workspace/m0_b1a9142d_2M/rows.json` summary, as recorded in `M0-REALFRAME/RESULT.md` §2.3). M0-2M m=204 (22/383, CI [0.038236, 0.085436]) is recorded context only. Caveat, frozen: synthetic Stage-1 m=200 nonexact and real final m=208 FER are different stages at different `m`; the M0 comparator is directional (did the regenerated rate move toward the real scale?), while the paired M3B-R1 comparator is exact. `undetected` is never merged into success on either side.
- Let `k'` = regenerated Stage-1 nonexact count over the same 240 seeds, `W'` its Wilson 95% score interval (same `z = 1.96` definition as the M0 rows). The script evaluates overlap mechanically; the §5 rule governs.

---

## §5 Frozen decision rule (PASS / MARGINAL / KILL — proxy fidelity only)

Applied mechanically to `k'`/`W'` with the §4 comparators. The `k'` table is frozen before comparison with the real band (outcome-independent).

> **§5.1 PASS (gap closes).** Iff `k' > k0` (= 10) **and** `W'` overlaps R: the word is **PASS**. Consequence: the rate/asymmetry mismatch explains the shortfall at Stage-1 scale; licenses **only** the drafting of a rescreen packet (T-N6 class: M3B re-run on the recalibrated synthetic). Licenses no method claim, no FER/efficiency/leakage/`f`/SKR/key figure, no statement that the regenerated channel equals the real channel, and no execution.
>
> **§5.2 MARGINAL (partially closes).** Iff `k' > k0` but `W'` lies entirely **above** R (recalibrated proxy overshoots — now pessimistic): the word is **MARGINAL**. Consequence: rates explain part of the shortfall but fidelity is not restored; the operator returns to main with the frozen paired table; any continuation requires a **new packet + new grant** — never a relaxed re-reading. MARGINAL is terminal for this packet, exactly as KILL is.
>
> **§5.3 KILL (not close at all).** Iff `k' ≤ k0` (paired movement absent — the measured rates alone explain nothing): the word is **KILL**. Consequence: abandon rate-recalibration; escalate to per-superframe conditioning research (`PROPOSAL.md` §2 row A); synthetic stays untrusted as a development proxy. The frozen paired table is the killing evidence.
>
> **§5.4 What PASS does and does not license.** A PASS licenses only the drafting of the rescreen packet. It licenses no decoder run, no construction run, no performance claim of any kind, no method comparison, and no execution.

Planner's integer expectation (the script's Wilson evaluation governs, not this note): KILL at `k' ≤ 10`; PASS expected for `11 ≤ k' ≤ 23`; MARGINAL expected at `k' ≥ 24`.

---

## §6 Deliverables and where each goes

One fresh additive root, fixed at Pre-EXECUTE: `workspace/proxy_recal_<uuid8>/` (uuid8 recorded in §14 P-6). **No existing root may be written.**

| # | File | Content |
|---|---|---|
| D-1 | `workspace/proxy_recal_<uuid8>/PROXY_RESULT.json` | One JSON: `inputs` (9 paths + byte sizes + UTC mtimes), `sampler` (S-1…S-5 parameters as executed + validation-draw seed), `validation` (emergent plane rates vs measured `p_k`, per-plane gate margins, PASS/REFUSE), `stage1` (per-seed outcome rows + `k'` + `W'`), `paired` (2×2 old→new transition table + undetected), `decision` (PASS/MARGINAL/KILL + fired §5 clause + evidence pointers), `resources` (wall_s, peak RSS, CPU, command, thread-pin env) |
| D-2 | `workspace/proxy_recal_<uuid8>/PROXY_SUMMARY.md` | Short Markdown: the validation table, `k'` vs `k0` vs M0-2M band, the 2×2 paired table, the decision word, the §11 ceiling restated verbatim. No ranking sentence; no method sentence |
| D-3 | `workspace/proxy_recal_<uuid8>/PROXY_LOG.md` | Single append-only log (EXPLORE contract): attempts, machine-gate results (validation gate first), the preregistered repair if used (§8), retained failures, final evidence pointer, review pointer |
| D-4 | `workspace/proxy_recal_<uuid8>/BATCH_END_REVIEW.md` | Independent batch-end review against PA-01…PA-08 (§7). FAIL blocks promotion of every number in this batch; rework + re-review, never publish-then-patch |

---

## §7 Acceptance items (stable IDs)

| ID | Item | Verify against |
|---|---|---|
| PA-01 | Input fidelity: exactly the nine §2 paths opened, byte sizes + UTC mtimes match the table, I-5 vs I-6 agree bitwise on the J21c `p_k`/`H(A\|B)`; no `.ttbin`/`.npz`/`.parquet`/raw path opened (script path-gate + log) | `PROXY_RESULT.json` `inputs` + `PROXY_LOG.md` + script source |
| PA-02 | Sampler fidelity: S-1…S-5 as executed (uniform source, measured slip masses, saturate edges, frozen Gray reuse, 240 frozen seeds/streams, I-7 graph, Stage-1 m=200 cold, identical decoder settings); no Stage-2 rescue; no independent-Bernoulli plane draw | fake test (§10 P-3) + reviewer check of seed/graph/setting pins |
| PA-03 | Validation gate: `N_valid`, tolerance formula, and PASS/REFUSE recorded with per-plane margins; on REFUSE, zero decodes ran | `PROXY_RESULT.json` `validation` + log |
| PA-04 | Decision mechanics: exactly one of PASS/MARGINAL/KILL with the fired §5 clause cited; `k'`/`W'` computed on the same 240 seeds; 2×2 paired table complete; `undetected` isolated | `PROXY_RESULT.json` `decision` + `paired` + `PROXY_SUMMARY.md` |
| PA-05 | Budget: wall ≤ 3600 s, peak RSS ≤ 2 GiB, 1 CPU, threads pinned (`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1`), one process, sequential; breach ⇒ INCOMPLETE, retained, never continued | log + resource lines in `PROXY_RESULT.json` |
| PA-06 | No-overwrite: fresh `workspace/proxy_recal_<uuid8>` only; `results/`, `comparison_bench/outputs_comparison/`, all pre-existing `workspace/` roots untouched; `git diff --stat -- src/ experiments/ tools/` empty; new repo files = exactly the §10 scoped manifest | filesystem + git state |
| PA-07 | Deliverables + review: D-1…D-4 complete in the fresh root; §11 ceiling respected verbatim; independent batch-end review PASS (FAIL ⇒ no promotion, rework, re-review) | review document |
| PA-08 | Claim-ceiling machine check: the strings `0.098260`/`0.09826` return **zero hits** outside the quoted §11 ceiling, the symbol `f_eff` returns **zero hits** outside it, and no numeric FER/efficiency/leakage/`f`/SKR/key claim and no method-ranking or method-improvement sentence anywhere in D-1…D-4; the shortfall factor is never quoted as a number | `rg` over `workspace/proxy_recal_<uuid8>` + reviewer read |

---

## §8 Budget (frozen ceiling)

One process, one CPU, threads pinned (`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1`), sequential, **no retry, no resume** except the single preregistered infra repair below. Wall **≤ 3600 s**, peak RSS **≤ 2 GiB**. Breach ⇒ INCOMPLETE, retained, never continued.

Basis (stated): M3B-R1 executed 240 Stage-1 + 10 rescue decodes in 1767.651 s single-CPU (I-9); 240 Stage-1-only decodes on the same graph/settings therefore cost ≈ 1700 s, plus seconds for the 10⁶-symbol validation draw (numpy-only; Stage-0-class arithmetic measured 0.39 s outer). The 3600 s ceiling is ≈ 2× measured — generous headroom that is never the thing under test.

**Preregistered repair (single, infra-only)**: at most one repair+rerun, only for infrastructure failure (process crash, OOM-kill, tool-side timeout, lost transcript) with **unchanged** scientific inputs, sampler parameters, seeds, graph, decoder settings, thresholds, and decision rule; the failed attempt is retained in `PROXY_LOG.md` in the same root. Any change to a scientific input, parameter, or the §5 rule is not a repair — it is a new packet.

---

## §9 Stop rules (any one ⇒ stop, retain evidence, return to main)

1. Any of the nine §2 files absent, unreadable, size/mtime drifted from the table, or I-5 vs I-6 bitwise disagreement on the J21c vector.
2. Validation-gate breach (§3.5) — REFUSE before any decode (not a repair trigger).
3. A sampler formula ambiguous as written here (do not interpolate — stop).
4. Any attempt, successful or attempted, to open a bundle/`.npz`, a `.ttbin`, a `pairs.parquet`, or any raw data.
5. Any invented rate (a number not read from the §2 files), any cross-source averaging, any independent-Bernoulli plane draw.
6. Graph/seed/setting drift: I-7 bytes/mtime drift, construction seed label ≠ 2026092001, frame seeds/streams ≠ §3 S-5, decoder settings ≠ M3B-R1 pins, or any Stage-2 decode attempted.
7. Budget breach (§8).
8. Output collision (`workspace/proxy_recal_<uuid8>` already exists) or any write inside an existing root, `results/`, or `comparison_bench/outputs_comparison/`.
9. Any evidence-label error (a number cited with the wrong source/file, a status relabelled, a fenced §2.4 sentence altered, the shortfall factor quoted as a number).

On stop: retain all evidence in place, **do not adjust inputs to fit**, return to the main thread with the failing check, the exact command, and the exact error. No rerun except the §8 preregistered infra repair.

---

## §10 Pre-EXECUTE checklist (main measures in one session before execution)

| # | Check | How |
|---|---|---|
| P-1 | Branch / HEAD re-measured | `git branch --show-current`, `git rev-parse HEAD` recorded |
| P-2 | Scoped cleanliness | `git diff --stat -- src/ experiments/ tools/` empty; new repo files = exactly two: `comparison_bench/src/comparison_bench/cli/proxy_recal_sampler.py` + `comparison_bench/tests/test_proxy_recal_fake.py` (scoped manifest). This packet file itself is the planner's already-written deliverable |
| P-3 | Focused test — **new fake-only test REQUIRED** | **Exact command**: `.venv/bin/python -m pytest comparison_bench/tests/test_proxy_recal_fake.py -p no:cacheprovider` — must be **all-pass** on a fresh additive `workspace/proxy_recal__pytest_<uuid8>` root. **Why new code needs a new test**: T-PA01 adds a new sampler (slip-mass draw, Gray-consistency, validation gate, path refusal) covered by no existing test. **What the fake asserts** (hand-computable constants, zero data contact — reads no CQ/M3B JSON, no bundle, nothing): a toy 2-bit Gray sampler with masses (`m_0` = 0.75, `m_+1` = 0.0, `m_-1` = 0.25) yields emergent plane rates exactly `p_0` = 0.125, `p_1` = 0.0625 under uniform source (hand derivation in the test docstring); the validation gate passes those and REFUSES a planted 10%-shifted vector; the overlap predicate returns PASS/MARGINAL/KILL on three hand-fixed (`k'`, interval, band) cases; and the input path-gate refuses planted `.npz`/`.ttbin` paths before any read |
| P-4 | Input size/mtime check | `stat` the nine §2 paths: byte sizes + UTC mtimes match the table exactly; I-5 vs I-6 bitwise agreement re-verified (values only — the planner's read already proved content; this is a drift check) |
| P-5 | Output absence | `workspace/proxy_recal_<uuid8>` does not exist; `results/` and `comparison_bench/outputs_comparison/` state recorded (no writes there) |
| P-6 | Exact command frozen | `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONPATH=<repo-root> .venv/bin/python -m comparison_bench.src.comparison_bench.cli.proxy_recal_sampler --graph <I-7> --baseline-rows <I-8> --root workspace/proxy_recal_<uuid8> --execute-synthetic --execution-authorized` (refuse without both flags). Root uuid8 + validation seed fixed here at Pre-EXECUTE |
| P-7 | Budgets + stops read back | §8 ceilings and §9 stop rules read back verbatim |
| P-8 | Protected roots + forbidden reads | Prove the nine input files' parent roots are otherwise untouched (no writes); `rg` the T-PA01 script for `decode|ldpc|construct|bundle|gamma` read-shaped tokens returns only the refusal-gate lines and the frozen Stage-1 call (zero bundle/raw read paths) |

---

## §11 Claim ceiling (verbatim — binds the execution, the review, and any citation; quoted verbatim in every artifact)

> This stage produces a proxy-fidelity result about a generator, nothing more. It establishes NO FER, NO efficiency, NO leakage, NO f, NO SKR and NO key figure for any method; NO method comparison or ranking; NO claim that any code improves; and NO claim that the regenerated channel equals the real channel. The value 0.098260 is never cited as a measurement. The void HDC and void Layered-Binary figures are never used as a baseline in any form. The real-frame shortfall factor is main's own derivation, not a recorded number, and is never quoted as one. A PASS licenses only the drafting of a rescreen packet; it licenses no performance claim, no decoder claim, and no execution.

---

## §12 What this stage cannot decide

1. **That any method corrects well.** No code is compared, improved, or qualified here; `k'` is a channel-fidelity observable, not a method result. Cheapest test that would: the rescreen packet a PASS licenses (T-N6 class) — and even that is synthetic-only.
2. **That the real channel is fully characterised.** Five captures, one 200 ps bin width, with the survey's stated limits (`RESULT.md` §§2–4; §2.4 fences). The sampler inherits exactly those limits.
3. **That synthetic becomes trustworthy for any purpose beyond the stated one.** A PASS restores the proxy for Stage-1 screening comparability only — not for qualification, publication numbers, or real-frame claims, each of which needs its own DECIDE packet.

---

## §13 Carried corrections (binding on this packet)

- **§13.1 Ten Gray planes, not nine** (as `STAGE0_PACKET.md` §13.1). `BITS = 10` verified at freezing.
- **§13.2 Sampler-structure correction (planner's, vs the tasking's loose "independent across planes" phrasing).** A literal independent-per-plane Bernoulli(`p_k`) draw is refuted by the frozen evidence (≈ 2.0% multi-plane flips predicted vs exactly zero observed in ~10⁶ pairs) and is forbidden. The frozen S-1…S-5 slip-first sampler reproduces the fenced triple by construction; draws are i.i.d. across symbols. This correction is process-faithful: it keeps the tasking's intent (realise measured rates, zero co-error per the standing citation) while refusing a construction the evidence rules out.
- **§13.3 Decode-scope resolution (options-document ambiguity).** `PROPOSAL.md` §1 Option A says "no decoder needed" in its cost line but its own cheapest discriminating test draws the seed set "through Stage-1 m=200 cold". The tasking resolves it: "regenerated-frame outcome" compared "against the M3B baseline for the same frame identities" requires decode outcomes, so this packet freezes Stage-1 m=200 cold on the 240 regenerated frames — and explicitly excludes Stage-2 rescue to bound cost. Channel-level histogram comparison alone could not be compared against the M3B decode baseline.

---

## §14 Grant block

- Grant verbatim: 「可以冻结，然后直接开始按你觉得比较好的顺序来」
- Date / granter: 2026-09-28, user.
- Scope: this grant covers **freezing this packet and executing it within the §8 ceilings only** — main's recorded judgement is that **this packet (A) runs first because it repairs a root cause**. Nothing else is authorized: the remaining options in `NEXT-STEP-OPTIONS/PROPOSAL.md` (B, C, D, E, G) and any DECIDE real-frame, qualification, or publication-claim work remain unauthorised and each needs its own packet + grant.

---

## §15 Tasks (ordered, for coder agents; implementation-only = no track gate)

1. **T-PA01** — Implement `comparison_bench/src/comparison_bench/cli/proxy_recal_sampler.py` (new file only): stdlib + numpy; argv takes exactly the §2 paths + `--root workspace/proxy_recal_<uuid8>` + validation-seed + dual `--execute-synthetic --execution-authorized` flags (refuse without both); startup path-gate refuses any input outside the frozen nine and any `.ttbin`/`.npz`/`.parquet` path; I-5 vs I-6 bitwise cross-check; S-1…S-5 sampler; §3.5 validation gate (REFUSE = exit nonzero, zero decodes); then 240-frame Stage-1 m=200 cold run on I-7 with M3B-R1-identical settings; writes D-1 + D-2 + appends D-3 log lines into the fresh root only; prints the §5 decision word last; `main() -> int` + `if __name__ == "__main__"` house style. No `src/` touch. Per `AGENTS.md` §5.7: simplest implementation that is scientifically correct — no checksums, no atomic writes, no locking, no retry framework, no caching.
2. **T-PA02** — Implement `comparison_bench/tests/test_proxy_recal_fake.py` per §10 P-3 (fake-only; `-p no:cacheprovider`; fresh `workspace/proxy_recal__pytest_<uuid8>` roots; zero scientific/real-data contact — hand constants only, reads no input file).
3. **T-PA03** — Pre-EXECUTE measurement (§10 P-1…P-8) by main; fill the execution root uuid8 and validation seed only on PASS.
4. **T-PA04** — Execute the single frozen §10 P-6 command; operator writes D-1…D-3. Any STOP (§9) retains evidence and returns to main; the only permitted rerun is the §8 preregistered infra repair.
5. **T-PA05** — Independent batch-end review → D-4 (`BATCH_END_REVIEW.md`) against PA-01…PA-08; FAIL ⇒ rework + re-review, never publish-then-patch.

**Size note for orchestrator**: small enough to implement directly — one additive sampler+driver script (~200 lines: slip draw, Gray-consistency, validation gate, frozen-path gate, Stage-1 call reuse) plus one fake-only test with hand-computable constants. No full pipeline needed. No `/opsx-explore` needed: every primitive (rates, masses, seeds, graph, settings, formulas, budget chain) is frozen above.
