# PROXY-RECAL-R2 — A-continuation Segmented-Checkpoint Packet (Draft, DRAFT-FROZEN)

- **Status**: DRAFT-FROZEN — drafting authorized 2026-09-28 (user 「都授权」 covers drafting this packet). **Execution is NOT authorized**: no Pre-EXECUTE, no run, no segment may start until a new explicit grant fills §14 with verbatim text. This packet authorizes nothing by itself.
- **Track**: **EXPLORE, annotated EXPLORE_HEAVY for cost** — justification against `AGENTS.md` §1.2 in §0.1. The route-closing interpretation of any result is DECIDE and stays outside this batch.
- **Continuation of**: `docs/research_cycles/PROXY-RECALIBRATION/PREREG_AND_AUTH.md` (Packet A, FROZEN) + `workspace/proxy_recal_3481c8d2/PROXY_LOG.md` (terminal INCOMPLETE, attempt 2: wall > 3600 s, 240 Stage-1 unfinished, D-1/D-2 never written, in-memory rows lost with the kill).
- **What changed vs Packet A**: exactly one infra-only delta — **segmented checkpointing** (§3.6): the same 240 frame identities are executed as 6 sequential segments × 40 frames, each segment flushing its rows to its own SEG file after every block, so a wall breach in segment k retains segments 0..k−1 (and the completed blocks of k). **Zero science change**: same nine inputs (§2), same sampler S-1…S-5 + §3.5 gate (§3), same §4 comparators, same §5 rule, same decoder pins, same seeds. Any science change is a new packet, not a repair.
- **Branch**: `formal-ir-v72p1-addendum-clean`. No commit, no push by any operator under this packet.
- **Order note**: this packet exists only because Packet A attempt 2 proved the single-shot 3600 s close is unwinnable on the harder channel (M3B-R1 250 decodes in 1767.651 s on the easy synthetic vs recalibrated 240 decodes > 3600 s unfinished — §8 basis; mechanism recorded as hypothesis only: frequent `max_iter=300` saturation on rate-hardened frames). The fix is durability (partial rows survive), not speed (no tuning, no setting change).

---

## §0 Goal / Non-Goals / Impact Scope / Classification

### Goal

Answer Packet A's frozen question with a durable execution: take the M3B-R1 construction and its 240 paired synthetic frames for one fixed graph instance, regenerate the same frame identities through the same slip-first sampler calibrated to the measured CQ-J21c values, run Stage-1 m=200 cold with identical graph/decoder/settings, and apply the frozen §5 word — but executed in **6 checkpointed segments** so that a wall breach no longer discards all rows. On full completion (all 6 segments), assemble the identical D-1/D-2 content Packet A would have produced and apply the identical §5 rule.

### Non-Goals

- No `.ttbin` open, no channel-bundle open (`gamma_f03.npz`, `gamma_f03_pb.npz`, any `x1_*.npz` — named here only to forbid them), no raw-data contact of any kind (§2.3).
- No Stage-2 rescue, no second graph instance (M3B-R2 out of scope), no new PEG construction, no decoder-setting change (no `max_iter`, streak, prior, centering, or acceptance change — the saturation hypothesis is recorded, never acted on here).
- No FER, efficiency, leakage, `f`, SKR, or key figure for any method; no method comparison or ranking; no claim that any code improves (§11).
- No route closure, qualification, publication number, or acceptance of any method.
- No modification of Packet A (`docs/research_cycles/PROXY-RECALIBRATION/PREREG_AND_AUTH.md`), the attempt-2 root (`workspace/proxy_recal_3481c8d2/`), any runner/construction/decoder/config, any existing workspace root, `docs/NOW.md`, `docs/decision-log.md`, `openspec/`, or `AGENTS.md`.
- No commit, no push.
- No re-interpretation of Packet A's INCOMPLETE as evidence for any §5 word; partial segments are durability, not a decision.

### Impact Scope

- **Written by this stage**: exactly two new repo files — `comparison_bench/src/comparison_bench/cli/proxy_recal_sampler_seg.py` (additive segmented driver reusing Packet A's frozen sampler/validation/decision helpers by import, T-R2-01) and `comparison_bench/tests/test_proxy_recal_seg_fake.py` (fake-only test, T-R2-02) — plus this packet (already written by the planner), plus all execution outputs inside one fresh additive root `workspace/proxy_recal_r2_<uuid8>` (§6).
- **Read-only inputs**: the §2 frozen list only (same nine files as Packet A). Nothing else is opened for content.
- **Untouched**: `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/outputs_comparison/`, every existing `workspace/` root (including `workspace/proxy_recal_3481c8d2/`), `docs/NOW.md`, `docs/decision-log.md`, `openspec/`, `AGENTS.md`, and the two Packet-A repo files (`proxy_recal_sampler.py`, `test_proxy_recal_fake.py` — reused by import, never edited).

### §0.1 Track classification: EXPLORE (EXPLORE_HEAVY cost annotation) — justification against `AGENTS.md` §1.2

Packet R2 is **EXPLORE**, confirmed against the §1.2 applicability matrix row "Synthetic route gate (diagnostic/construction arms) → EXPLORE (`EXPLORE_HEAVY` if costly)":

1. **Input character**: the only channel inputs are the same already-persisted, non-sensitive channel *statistics* (float vectors and scalars in the §2 JSONs) plus the persisted M3B-R1 synthetic outcomes. The stage opens no `.ttbin`, no channel bundle, no `(a,b)` array, no raw data of any kind (§2.3). Regenerated frames are synthetic draws from the frozen sampler, not real data.
2. **Bounded and reversible**: one graph instance, 240 Stage-1 decodes in 6 sequential segments, one CPU at a time, per-segment wall ≤ 1800 s and total wall ≤ 10800 s, RSS ≤ 2 GiB (§8); one fresh additive root, append-only (§6).
3. **No claim**: the §11 ceiling forbids every claim-bearing figure and every method statement. The only output on full completion is the same proxy-fidelity word (PASS/MARGINAL/KILL, §5) about a *generator*, plus the paired transition table. On partial completion the only output is INCOMPLETE with retained segments — no word.
4. **Cost annotation**: the six-segment decode cost (~1.5–3 CPU-hours on the attempt-2 observed floor of > 3600 s per 240, §8) trips the `EXPLORE_HEAVY` annotation, which is a cost note, not a third lifecycle. The route-closing interpretation of any word is DECIDE and stays outside this batch.
5. **Uncertainty default**: no concrete risk named here defaults this to DECIDE. The foreseeable failure modes (input drift, unrealizable rates, evidence-label error, checkpoint mismatch) are met by the size/mtime gate (PR2-01), the validation-gate refusal (§3.5), the segment-manifest gate (§3.6), the fake-only test (§10 P-3), and the batch-end review (PR2-07) — not by escalation.

---

## §1 The frozen question (unchanged from Packet A — proxy fidelity, not code improvement)

Take the M3B-R1 construction and its 240 paired synthetic frames for one fixed graph instance (`workspace/m3a_nested_200p8_20260926/arm1.json`, construction seed label 2026092001), and regenerate the same frame identities (seeds `2026096401+idx`, idx 0..239, stream `o1_blk:{seed}`) through a sampler whose symbol error rate and ±1 asymmetry are set to the **measured** CQ-J21c values rather than to the frozen bundle's. Run Stage-1 m=200 cold with the identical graph, decoder, and settings.

**Does the real frame-error shortfall close, partially close, or not close at all?** The shortfall's *direction* is verified (M0 D1: real worse than X1-synthetic in 5 of 6 arms, consistent in 1, better in 0 — `M0-REALFRAME/RESULT.md` §3); its *factor* is **main's own derivation, not recorded anywhere, and is never quoted as a number in this stage** (not in the packet, not in any deliverable, not in review).

The question is answered by the §5 rule, stated in terms of whether the regenerated channel's frame-error rate matches the real one — never in terms of whether any code improves. **R2 answers the identical question; only the execution durability changes (§3.6). A partial (fewer than 240-frame) result answers nothing and yields no word.**

---

## §2 Frozen input list (read-only — identical to Packet A §2)

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
| I-9 | `workspace/m3b_nested_paired_20260926/P1S1-R1_73d2f40a/M3B_RESULT_M3B-R1.md` | 1344 | 2026-09-26 07:12:05 UTC | M3B-R1 arm summary (k0, wall 1767.651 s — part of the §8 budget basis) |

*Tasking shorthand note (§13.4): the drafting task's "same six inputs" is read as the six JSON channel/graph/baseline inputs I-1…I-6 + I-7 + I-8 with I-9 as the frozen echo (i.e. all nine above, identical to Packet A). No input is dropped, added, or substituted; any deviation is a STOP (§9).*

### §2.1 Active sampler numbers (transcribed from I-5/I-6; the files govern — identical to Packet A)

Corresponding-capture decision (frozen): M3B's frozen channel is "source 2M" (`M3B-NESTED-PAIRED/PACKET.md`); CQ-J21c is the Jan-21 2M source measured over the M0 VAL+HOLD eval region (`CHAN-QUALITY-SURVEY/RESULT.md` §1). **CQ-J21c is therefore the corresponding capture; its numbers drive the sampler.** The other four captures are context/provenance (transcription discipline), never sampler inputs.

- `ser` = **0.25375836** (sampler error probability).
- ±1 masses: `m_0` = 0.74624164, `m_+1` = 0.00143807, `m_-1` = 0.25232029 (−1-dominant; sign follows the per-source offset sign +50 — `RESULT.md` §3). Conditional slip direction: `q_-1` = 0.25232029/0.25375836 ≈ **0.99433**, `q_+1` ≈ 0.00567.
- Per-plane rates `p_k`, LSB-first index 0 = LSB plane: `[0.12711631, 0.06325473, 0.03222911, 0.01576779, 0.00784055, 0.00382211, 0.00202707, 0.00097146, 0.00050485, 0.00022438]`.
- H values: `H(U1|B)` = 0.02491156, `H(U2|U1B)` = 0.80076697, `H(A|B)` = 0.82567853 (context; no disclosure arithmetic is performed in this stage).
- Plane count is **ten** (`comparison_bench/src/comparison_bench/formal_ir/nonbinary_v25_gate.py:28` `BITS = 10`). A future 9-plane treatment must freeze which plane is excluded and why.
- Five-capture `ser` range: **0.23856707–0.25433839** (≈ 0.24–0.25).

### §2.2 Input-transcription discipline

The script reads the JSON values, never this transcription. Any mismatch between this transcription and the files is a STOP under §9 — the files govern. I-5 and I-6 must agree on the CQ-J21c `p_k` vector and `H(A|B)` bitwise; disagreement is a STOP (input drift), never an averaging license.

### §2.3 Zero-real-data / no-bundle statement

The channel bundle (`docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz`, `gamma_f03_pb.npz`) is **not an input and must not be opened** — not for reading, not for comparison, not for "checking" the sampler against it. Likewise no `.ttbin`, no `x1_*.npz`, no `pairs.parquet`, no `(a,b)` array, no raw data of any kind. The script's allowed-input gate (T-R2-01) refuses any path outside the nine frozen above and any path ending in `.ttbin`, `.npz`, `.parquet`. The M3B-R2 arm, the P1 comparator roots, and all M0 roots except via the frozen M0-2M numbers in §4 are not inputs and stay untouched. The attempt-2 root `workspace/proxy_recal_3481c8d2/` is provenance only (its `PROXY_LOG.md` is cited, never executed from, never written to).

### §2.4 Standing citation discipline

Where the channel structure is invoked, use verbatim the standing fenced forms from `CHAN-QUALITY-SURVEY/INDEPENDENT_ACCEPTANCE.md` Part B:

- Channel premise: "**zero observed cross-plane co-error; single-plane-flip structure**" — triple evidence (off-diagonals exactly 0.0, Gray popcount only on {0,1}, `expected_planes_flipped_per_error` = 1.0 both routes), with the detection-floor caveat (~10⁶ pairs exclude only multi-plane rates above ~10⁻⁶) whenever the word "independent" is used.
- Negative: "**no measured easier point among the five captures; the unmeasured groups supply no evidence of one on recorded grounds**" — the short本体 form ("no easier data exists") is never cited alone.
- Legacy `0.098260`: an expectation under a different pipeline and pairing rule, never a result; in frozen-chain terms: "unfreezes under frozen chain; recorded differences are pairing rule + pipeline; further cause unestablished" (N-9 form). It is never cited as a measurement and never enters any comparison.

---

## §3 The sampler (frozen decisions, not code — identical to Packet A, plus infra-only §3.6)

Slip-first Gray-consistent sampler S-1…S-5, unchanged. Rationale in one line: every measured error is a ±1 bin slip (`other` mass ≈ 0), and a ±1 slip of a Gray-labelled symbol flips exactly one plane — so drawing slips reproduces the single-plane structure by construction, while the per-plane ladder emerges and is validated, not hand-imposed.

- **S-1 Source symbols**: Alice symbols i.i.d. uniform over the 1024 bins `{0,…,1023}`. Stated assumption with basis: under uniform source the emergent plane law is `p_k ≈ ser·2^{-(k+1)}`, which matches the measured CQ-J21c ladder within ~4% on planes 0–8. Source-marginal mismatch beyond this is a recorded limitation (§12.2), not a silent approximation.
- **S-2 Slip draw**: per symbol, draw `s ∈ {0,+1,−1}` with the measured CQ-J21c masses (`m_0` = 0.74624164, `m_+1` = 0.00143807, `m_-1` = 0.25232029). `Bob_bin = Alice_bin + s`, Gray-encode both sides with the frozen mapping reused verbatim (the same Gray function the survey used; no reimplementation, no alternative Gray variant — any ambiguity about which function is a STOP).
- **S-3 Edge rule**: saturate (`Bob_bin = clamp(Alice_bin + s, 0, 1023)`). Stated micro-choice with bound: affects at most `2/1024` of draws at one-sided edges; the §3.5 validation gate would catch any material distortion.
- **S-4 Cross-plane / cross-symbol structure**: draws are i.i.d. **across symbols**; within a symbol at most one plane ever flips (Gray adjacency), so cross-plane co-error is zero by construction — consistent with the fenced triple, stronger than observation. The word "independent" is not used for planes except with the §2.4 detection-floor caveat. Rejected alternative, recorded: literal independent-per-plane Bernoulli(`p_k`) would emit ≈ 2.0% multi-plane flips — ~20,000 events per 10⁶ pairs against exactly zero observed. It is refuted by the frozen evidence and is explicitly forbidden (§13.2 of Packet A, carried).
- **S-5 Frame construction**: 240 frames × 1024 symbols, frame `idx` uses seed `2026096401+idx` and stream label `o1_blk:{seed}` — the identical identities as M3B-R1. One fixed graph instance (I-7), Stage-1 m=200 cold only, decoder settings frozen identical to M3B-R1 (`max_iter=300`, streak 3, exact-match success, no warm start, no genie/argmax u1). No Stage-2 rescue under this packet.
- **§3.5 Validation gate (machine gate before any decode in every segment)**: on a frozen `N_valid = 10⁶`-symbol draw (validation seed frozen at Pre-EXECUTE, same value as Packet A's rerun unless Pre-EXECUTE refreezes with reason), require per plane `|emergent_k − p_k| ≤ max(5%·p_k, 5·SE_k)` with `SE_k = sqrt(p_k(1−p_k)/N_valid)` from the measured `p_k`, AND `|emergent_ser − 0.25375836| ≤ 0.003`. Breach ⇒ **REFUSE: no decode in that segment, no silent approximation**, retain evidence, return to main. Pass ⇒ proceed to that segment's Stage-1 blocks. The gate re-runs identically in each segment (numpy-only, seconds) so every segment is self-validating; no cross-segment validation caching.
- **Loader passthrough (carried repair)**: the I-7 graph-loader dict carries `four_cycles`, `rank` (gated) and `min_girth` (recorded) by direct artifact index alongside n/m/triples/status, through the UNMODIFIED frozen F6 pin gate (`p1.construct_and_pin`). No defaults, no fallbacks, no synthesised pins: an absent pin is a REFUSE, never a fill-in. This is Packet A's authorised §8 repair, carried as the frozen baseline here — not a new repair.

### §3.6 Segmentation (the sole R2 delta — infra-only, zero science change)

- **Partition**: the 240 frame identities split into **6 sequential segments of 40**: segment `g ∈ {0,…,5}` owns `idx ∈ [40g, 40g+39]`, seeds `2026096401+idx`, same stream labels, same graph, same settings. Order is fixed ascending; segments run strictly sequentially (one process at a time, §8). No segment is skipped, reordered, retried, or resumed under this packet.
- **Checkpoint files**: segment `g` writes `SEG_g.json` (`SEG_0.json`…`SEG_5.json`) in the fresh root, **rewritten after every completed block** (rows appended in-memory then full-file rewrite + flush, simplest correct per `AGENTS.md` §5.7 — no atomic rename, no locking, no checksums). Each `SEG_g.json` holds: segment index, idx range, validation-gate margins for that segment, per-block rows completed so far, block count, per-segment wall/RSS. A killed process therefore retains every fully written block of every started segment.
- **Manifest**: `SEG_MANIFEST.json` (written at start, updated at each segment close) records uuid8, validation seed, segment count (6), per-segment idx ranges, and close status. Any manifest/SEG mismatch at assembly (missing segment, overlapping idx, seed mismatch, count ≠ 40 per segment) is a STOP (§9), never a patch license.
- **Assembly rule**: D-1/D-2 are assembled **only when all 6 SEG files are closed with 40 rows each (240 total)**. Assembly concatenates rows in idx order, recomputes `k'`, `W'`, the 2×2 paired table and the §5 word with the UNMODIFIED helpers imported from the Packet-A module. Fewer than 240 rows ⇒ INCOMPLETE with retained segments, no word, no assembly, no partial-word extrapolation.
- **Validation-seed reuse**: the same validation seed as Packet A's rerun (`2026097301`) is the default freeze at Pre-EXECUTE (same draw, same gate). Pre-EXECUTE may refreeze only with a recorded zero-collision reason; the frozen value goes in §10 P-6 and the manifest.
- **What segmentation is not**: not a parameter change, not a seed change, not a graph/setting change, not a budget relaxation for any single decode, not a resume of Packet A's killed process (that process is terminal INCOMPLETE; R2 starts fresh in a fresh root).

---

## §4 Comparison metric (frozen — identical to Packet A)

- **Exact comparator (paired, same frame identities)**: M3B-R1 baseline `k0 = 10/240` Stage-1 nonexact (I-8/I-9). Deliverable includes the 2×2 paired transition table old→new over the 240 matched seeds (same shape as M3B's paired table: old_success_new_success, old_success_new_failure, old_failure_new_success, old_failure_new_failure), plus stage-specific `undetected` (counts as failure, separately reported).
- **Real comparator (directional, stage-mismatched — stated openly)**: M0-2M m=208 arm: 16/383 fails, Wilson 95% CI **R = [0.025875, 0.066776]** (`workspace/m0_b1a9142d_2M/rows.json` summary, as recorded in `M0-REALFRAME/RESULT.md` §2.3). M0-2M m=204 (22/383, CI [0.038236, 0.085436]) is recorded context only. Caveat, frozen: synthetic Stage-1 m=200 nonexact and real final m=208 FER are different stages at different `m`; the M0 comparator is directional (did the regenerated rate move toward the real scale?), while the paired M3B-R1 comparator is exact. `undetected` is never merged into success on either side.
- Let `k'` = regenerated Stage-1 nonexact count over the same 240 seeds, `W'` its Wilson 95% score interval (same `z = 1.96` definition as the M0 rows). The script evaluates overlap mechanically; the §5 rule governs. **On partial completion `k'`/`W'` are reported per retained segment as durability evidence only (e.g. `k'_retained/n_retained`); the §5 rule is not applied.**

---

## §5 Frozen decision rule (PASS / MARGINAL / KILL — identical to Packet A, full-completion only)

Applied mechanically to `k'`/`W'` with the §4 comparators and **only when all 240 rows are present**. The `k'` table is frozen before comparison with the real band (outcome-independent).

> **§5.1 PASS (gap closes).** Iff `k' > k0` (= 10) **and** `W'` overlaps R: the word is **PASS**. Consequence: the rate/asymmetry mismatch explains the shortfall at Stage-1 scale; licenses **only** the drafting of a rescreen packet (T-N6 class: M3B re-run on the recalibrated synthetic). Licenses no method claim, no FER/efficiency/leakage/`f`/SKR/key figure, no statement that the regenerated channel equals the real channel, and no execution.
>
> **§5.2 MARGINAL (partially closes).** Iff `k' > k0` but `W'` lies entirely **above** R (recalibrated proxy overshoots — now pessimistic): the word is **MARGINAL**. Consequence: rates explain part of the shortfall but fidelity is not restored; the operator returns to main with the frozen paired table; any continuation requires a **new packet + new grant** — never a relaxed re-reading. MARGINAL is terminal for this packet, exactly as KILL is.
>
> **§5.3 KILL (not close at all).** Iff `k' ≤ k0` (paired movement absent — the measured rates alone explain nothing): the word is **KILL**. Consequence: abandon rate-recalibration; escalate to per-superframe conditioning research (`PROPOSAL.md` §2 row A); synthetic stays untrusted as a development proxy. The frozen paired table is the killing evidence.
>
> **§5.4 What PASS does and does not license.** A PASS licenses only the drafting of the rescreen packet. It licenses no decoder run, no construction run, no performance claim of any kind, no method comparison, and no execution.
>
> **§5.5 Partial completion yields no word.** Fewer than 240 rows ⇒ INCOMPLETE (retained segments + per-segment counts), never PASS/MARGINAL/KILL, never an extrapolated word, never a "trend" sentence.

Planner's integer expectation (the script's Wilson evaluation governs, not this note — carried from Packet A): KILL at `k' ≤ 10`; PASS expected for `11 ≤ k' ≤ 23`; MARGINAL expected at `k' ≥ 24`.

---

## §6 Deliverables and where each goes

One fresh additive root, fixed at Pre-EXECUTE: `workspace/proxy_recal_r2_<uuid8>/` (uuid8 recorded in §14 P-6; the `r2_` infix guarantees no collision with the Packet-A root pattern). **No existing root may be written.**

| # | File | Content |
|---|---|---|
| S-0..S-5 | `workspace/proxy_recal_r2_<uuid8>/SEG_g.json` (g = 0..5) | Per-segment checkpoint: segment index, idx range, validation-gate margins for that segment, per-block rows (flushed after every block), block count, per-segment wall/RSS. Written during execution; retained on INCOMPLETE |
| M | `workspace/proxy_recal_r2_<uuid8>/SEG_MANIFEST.json` | Manifest: uuid8, validation seed, 6 × idx ranges, per-segment close status. Mismatch at assembly ⇒ STOP |
| D-1 | `workspace/proxy_recal_r2_<uuid8>/PROXY_RESULT.json` | Assembled ONLY on full completion (240 rows): same schema as Packet A D-1 — `inputs` (9 paths + byte sizes + UTC mtimes), `sampler` (S-1…S-5 parameters as executed + validation-draw seed + segmentation record), `validation` (per-segment gate margins, PASS/REFUSE), `stage1` (per-seed outcome rows + `k'` + `W'`), `paired` (2×2 old→new transition table + undetected), `decision` (PASS/MARGINAL/KILL + fired §5 clause + evidence pointers), `resources` (per-segment + total wall_s, peak RSS, CPU, commands, thread-pin env) |
| D-2 | `workspace/proxy_recal_r2_<uuid8>/PROXY_SUMMARY.md` | Assembled ONLY on full completion: same content as Packet A D-2 (validation table, `k'` vs `k0` vs M0-2M band, 2×2 paired table, decision word, §11 ceiling verbatim). No ranking sentence; no method sentence |
| D-3 | `workspace/proxy_recal_r2_<uuid8>/PROXY_LOG.md` | Single append-only log (EXPLORE contract): Pre-EXECUTE record, per-segment attempts, machine-gate results (validation gate first in each segment), the preregistered repair if used (§8), retained failures, final evidence pointer, review pointer |
| D-4 | `workspace/proxy_recal_r2_<uuid8>/BATCH_END_REVIEW.md` | Independent batch-end review against PR2-01…PR2-08 (§7). FAIL blocks promotion of every number in this batch; rework + re-review, never publish-then-patch. On INCOMPLETE the review covers durability (segments retained, no word emitted, no extrapolation) |

---

## §7 Acceptance items (stable IDs)

| ID | Item | Verify against |
|---|---|---|
| PR2-01 | Input fidelity: exactly the nine §2 paths opened, byte sizes + UTC mtimes match the table, I-5 vs I-6 agree bitwise on the J21c `p_k`/`H(A\|B)`; no `.ttbin`/`.npz`/`.parquet`/raw path opened; attempt-2 root untouched (no writes) | `PROXY_RESULT.json` `inputs` (or SEG files on INCOMPLETE) + `PROXY_LOG.md` + script source + `git status` scoping |
| PR2-02 | Sampler fidelity: S-1…S-5 as executed (uniform source, measured slip masses, saturate edges, frozen Gray reuse, 240 frozen seeds/streams, I-7 graph with carried pin passthrough, Stage-1 m=200 cold, identical decoder settings `max_iter=300`); no Stage-2 rescue; no independent-Bernoulli plane draw; segmentation is ordering/checkpointing only (same per-idx draws — spot-check: segment draws equal single-shot draws for same seed) | fake test (§10 P-3) + reviewer check of seed/graph/setting pins + SEG idx ranges |
| PR2-03 | Validation gate: `N_valid`, tolerance formula, and PASS/REFUSE recorded with per-plane margins **in every segment**; on REFUSE in segment g, zero decodes ran in g and no later segment started | SEG files `validation` + log |
| PR2-04 | Decision mechanics (full completion only): exactly one of PASS/MARGINAL/KILL with the fired §5 clause cited; `k'`/`W'` computed on the same 240 seeds; 2×2 paired table complete; `undetected` isolated. On partial completion: INCOMPLETE with retained-segment counts, no word, no extrapolation | `PROXY_RESULT.json` `decision` + `paired` + `PROXY_SUMMARY.md`, or INCOMPLETE record |
| PR2-05 | Budget: per-segment wall ≤ 1800 s, total wall ≤ 10800 s, peak RSS ≤ 2 GiB, 1 CPU at a time, threads pinned (`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1`), sequential segments; breach in segment g ⇒ INCOMPLETE at g, prior segments retained, never continued | log + resource lines in SEG files / `PROXY_RESULT.json` |
| PR2-06 | No-overwrite: fresh `workspace/proxy_recal_r2_<uuid8>` only; `results/`, `comparison_bench/outputs_comparison/`, all pre-existing `workspace/` roots untouched; `git diff --stat -- src/ experiments/ tools/` empty; new repo files = exactly the §10 scoped manifest; Packet-A files unmodified | filesystem + git state |
| PR2-07 | Deliverables + review: on full completion D-1…D-4 + 6 SEG + manifest complete in the fresh root; on INCOMPLETE the retained SEG + manifest + log complete with no D-1/D-2 assembly; §11 ceiling respected verbatim; independent batch-end review PASS (FAIL ⇒ no promotion, rework, re-review) | review document |
| PR2-08 | Claim-ceiling machine check: the strings `0.098260`/`0.09826` return **zero hits** outside the quoted §11 ceiling, the symbol `f_eff` returns **zero hits** outside it, and no numeric FER/efficiency/leakage/`f`/SKR/key claim and no method-ranking or method-improvement sentence anywhere in SEG/D-1…D-4; the shortfall factor is never quoted as a number; no partial-result trend/word sentence | `rg` over `workspace/proxy_recal_r2_<uuid8>` + reviewer read |

---

## §8 Budget (frozen segmented ceiling)

Sequential segments, one process at a time, one CPU, threads pinned (`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1`), **no retry, no resume, no reorder, no skip** except the single preregistered infra repair below. Per-segment wall **≤ 1800 s**, total wall **≤ 10800 s**, peak RSS **≤ 2 GiB** (per segment and overall). Breach in segment g ⇒ INCOMPLETE at g, segments 0..g−1 retained with all flushed blocks, never continued. Per-block cap carried: any single block wall > 300 s ⇒ that block marked `overrun`/failed with `undetected` 0 and the segment stops INCOMPLETE (same semantics as Packet A's per-block gate).

Basis (stated): M3B-R1 executed 250 decodes in 1767.651 s single-CPU on the easy synthetic (I-9; ≈ 7 s/decode); Packet A attempt 2 exceeded 3600 s for 240 decodes on the recalibrated harder channel without finishing (observed floor > 15 s/decode average, mechanism as hypothesis only: frequent `max_iter=300` saturation on rate-hardened frames — no per-block timing exists, nothing is concluded). A 40-frame segment at the observed floor costs > 600 s; the 1800 s per-segment ceiling is ≈ 2–3× that floor, and the 10800 s total is 6 × per-segment (3× Packet A's single-shot ceiling). The ceiling buys durability headroom, never a result: exceeding it is INCOMPLETE, not slowness evidence.

**Preregistered repair (single, infra-only)**: at most one repair+rerun of the affected segment(s), only for infrastructure failure (process crash, OOM-kill, tool-side timeout, lost transcript, checkpoint-write I/O error) with **unchanged** scientific inputs, sampler parameters, seeds, graph, decoder settings, thresholds, partition, and decision rule; the failed attempt is retained in `PROXY_LOG.md` in the same root. A validation REFUSE, a budget breach attributed to decode cost (saturation), or any change to a scientific input, parameter, partition, or the §5 rule is not a repair — it is a new packet.

---

## §9 Stop rules (any one ⇒ stop, retain evidence, return to main)

1. Any of the nine §2 files absent, unreadable, size/mtime drifted from the table, or I-5 vs I-6 bitwise disagreement on the J21c vector.
2. Validation-gate breach (§3.5) in any segment — REFUSE that segment before any of its decodes (not a repair trigger); no later segment starts.
3. A sampler formula ambiguous as written here (do not interpolate — stop).
4. Any attempt, successful or attempted, to open a bundle/`.npz`, a `.ttbin`, a `pairs.parquet`, or any raw data — or any write into the attempt-2 root.
5. Any invented rate (a number not read from the §2 files), any cross-source averaging, any independent-Bernoulli plane draw.
6. Graph/seed/setting/partition drift: I-7 bytes/mtime drift, construction seed label ≠ 2026092001, frame seeds/streams ≠ §3 S-5, decoder settings ≠ M3B-R1 pins, segment partition ≠ 6 × 40 in ascending idx order, validation seed ≠ the §10 P-6 frozen value, or any Stage-2 decode attempted.
7. Budget breach (§8) — per-segment, total, RSS, or per-block overrun.
8. Output collision (`workspace/proxy_recal_r2_<uuid8>` already exists, or any `SEG_g.json`/`PROXY_RESULT.json`/`PROXY_SUMMARY.md` already exists at segment start) or any write inside an existing root, `results/`, or `comparison_bench/outputs_comparison/`.
9. Any evidence-label error (a number cited with the wrong source/file, a status relabelled, a fenced §2.4 sentence altered, the shortfall factor quoted as a number, a partial count presented as a §5 word or trend).
10. Checkpoint mismatch at assembly: missing/extra SEG file, per-segment row count ≠ 40, overlapping or non-contiguous idx ranges, seed-set mismatch vs the frozen 240, or manifest disagreement.

On stop: retain all evidence in place (including all flushed SEG blocks), **do not adjust inputs to fit**, return to the main thread with the failing check, the exact command, and the exact error. No rerun except the §8 preregistered infra repair.

---

## §10 Pre-EXECUTE checklist (main measures in one session before any execution)

| # | Check | How |
|---|---|---|
| P-1 | Branch / HEAD re-measured | `git branch --show-current`, `git rev-parse HEAD` recorded |
| P-2 | Scoped cleanliness | `git diff --stat -- src/ experiments/ tools/` empty; Packet-A files (`proxy_recal_sampler.py`, `test_proxy_recal_fake.py`) unmodified vs their accepted state; new repo files = exactly two: `comparison_bench/src/comparison_bench/cli/proxy_recal_sampler_seg.py` + `comparison_bench/tests/test_proxy_recal_seg_fake.py` (scoped manifest). This packet file itself is the planner's already-written deliverable |
| P-3 | Focused test — **new fake-only test REQUIRED** | **Exact command**: `.venv/bin/python -m pytest comparison_bench/tests/test_proxy_recal_seg_fake.py -p no:cacheprovider` — must be **all-pass** on fresh additive `workspace/proxy_recal_r2__pytest_<uuid8>` roots. **Why new code needs a new test**: T-R2-01 adds a segmented driver (partition, per-block checkpoint rewrite, manifest, assembly gate) covered by no existing test. **What the fake asserts** (hand-computable constants, zero data contact — reads no CQ/M3B JSON, no bundle, nothing): partition covers the frozen idx set exactly once (6 × 40, ascending, no overlap/gap); per-block checkpoint rewrite retains completed blocks after a simulated kill (fake rows survive); assembly REFUSES a planted short set (< 240) and a planted overlapping set; the §5 word helper returns the same word as Packet A's helper on three hand-fixed (`k'`, interval, band) cases; the input path-gate refuses planted `.npz`/`.ttbin` paths before any read |
| P-4 | Input size/mtime check | `stat` the nine §2 paths: byte sizes + UTC mtimes match the table exactly; I-5 vs I-6 bitwise agreement re-verified (values only) |
| P-5 | Output absence | `workspace/proxy_recal_r2_<uuid8>` does not exist; `results/` and `comparison_bench/outputs_comparison/` state recorded (no writes there); attempt-2 root present and unmodified |
| P-6 | Exact commands frozen | Per-segment: `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONPATH=<repo-root> .venv/bin/python -m comparison_bench.src.comparison_bench.cli.proxy_recal_sampler_seg --graph <I-7> --baseline-rows <I-8> --root workspace/proxy_recal_r2_<uuid8> --segment-index <g> --num-segments 6 --validation-seed <seed> --execute-synthetic --execution-authorized` for g = 0..5 in ascending order (refuse without both flags; refuse unless `--num-segments 6`). Root uuid8 + validation seed (default `2026097301`, Packet-A rerun value) fixed here at Pre-EXECUTE; assembly command frozen likewise (assemble only, no decode) |
| P-7 | Budgets + stops read back | §8 ceilings (per-segment 1800 s / total 10800 s / RSS 2 GiB / per-block 300 s) and §9 stop rules read back verbatim |
| P-8 | Protected roots + forbidden reads | Prove the nine input files' parent roots and the attempt-2 root are otherwise untouched (no writes); `rg` the T-R2-01 script for `decode\|ldpc\|construct\|bundle\|gamma` read-shaped tokens returns only the refusal-gate lines and the frozen Stage-1 call reuse (zero bundle/raw read paths) |

---

## §11 Claim ceiling (verbatim — binds the execution, the review, and any citation; quoted verbatim in every artifact)

> This stage produces a proxy-fidelity result about a generator, nothing more. It establishes NO FER, NO efficiency, NO leakage, NO f, NO SKR and NO key figure for any method; NO method comparison or ranking; NO claim that any code improves; and NO claim that the regenerated channel equals the real channel. The value 0.098260 is never cited as a measurement. The void HDC and void Layered-Binary figures are never used as a baseline in any form. The real-frame shortfall factor is main's own derivation, not a recorded number, and is never quoted as one. A PASS licenses only the drafting of a rescreen packet; it licenses no performance claim, no decoder claim, and no execution.

---

## §12 What this stage cannot decide

1. **That any method corrects well.** No code is compared, improved, or qualified here; `k'` is a channel-fidelity observable, not a method result. Cheapest test that would: the rescreen packet a PASS licenses (T-N6 class) — and even that is synthetic-only.
2. **That the real channel is fully characterised.** Five captures, one 200 ps bin width, with the survey's stated limits (`RESULT.md` §§2–4; §2.4 fences). The sampler inherits exactly those limits.
3. **That synthetic becomes trustworthy for any purpose beyond the stated one.** A PASS restores the proxy for Stage-1 screening comparability only — not for qualification, publication numbers, or real-frame claims, each of which needs its own DECIDE packet.
4. **Anything from a partial result.** Retained segments measure durability only; they support no rate claim, no trend claim, and no rescreen decision. The rescreen packet is licensed by a full-completion PASS and nothing else.

---

## §13 Carried corrections and R2 deltas (binding on this packet)

- **§13.1 Ten Gray planes, not nine** (carried from Packet A §13.1). `BITS = 10` verified at freezing.
- **§13.2 Slip-first sampler, Bernoulli forbidden** (carried from Packet A §13.2). A literal independent-per-plane Bernoulli(`p_k`) draw is refuted by the frozen evidence and is forbidden. S-1…S-5 are unchanged.
- **§13.3 Decode scope** (carried from Packet A §13.3). Stage-1 m=200 cold on the 240 regenerated frames; Stage-2 rescue excluded to bound cost.
- **§13.4 Tasking-shorthand resolution (planner's, vs "same six inputs / §4 grid").** The drafting task's "同一六输入" is satisfied by the full frozen nine (I-1…I-9 identical to Packet A — the six JSON channel/baseline inputs plus graph plus rows plus the frozen echo summary); "§4 grid / §5 rule" is satisfied by carrying §4 (k0 = 10/240, R band, Wilson z = 1.96) and §5 (PASS/MARGINAL/KILL + §5.5) verbatim. No input dropped, no comparator changed, no clause relaxed. Any conflict between this reading and the tasking is a STOP, not a patch license.
- **§13.5 Segmentation is infra-only (planner's R2 delta).** The 6 × 40 partition, per-block SEG rewrite, manifest, and assembly gate change durability only. Per-idx draws, seeds, streams, graph, settings, validation formula, comparators, and decision rule are byte-identical in intent to Packet A. The saturation timing note (§8 basis) is a hypothesis, never a tuning license: `max_iter` stays 300.
- **§13.6 Attempt-2 provenance (read-only).** `workspace/proxy_recal_3481c8d2/PROXY_LOG.md` attempt-2 INCOMPLETE is the sole motivation evidence (wall > 3600 s, 240 unfinished, zero rows retained). That root is never written, never resumed, never reassembled from.

---

## §14 Grant block

- Drafting grant verbatim: 「都授权」 — date / granter: 2026-09-28, user. Scope: **covers drafting this packet only** (planner output, no repo-code change, no execution).
- Execution grant: **PENDING — no verbatim text, no execution.** Pre-EXECUTE (T-R2-03), all six segment commands, the assembly, and the review (T-R2-04/05) are blocked until the user issues a new explicit grant naming this packet (`PROXY-RECAL-R2`) with its §8 ceilings; the new verbatim text will be pasted here with date/granter before any P-1 measurement.

---

## §15 Tasks (ordered, for coder agents; implementation-only = no track gate)

1. **T-R2-01** — Implement `comparison_bench/src/comparison_bench/cli/proxy_recal_sampler_seg.py` (new file only): stdlib + numpy; import (never copy-edit) the frozen sampler/validation/decision helpers from `proxy_recal_sampler.py` (`draw_frame`, `gray_plane_rates`, `validation_gate`, `build_exact_prior_table`, `stage1_block_outcome`, `wilson`, `intervals_overlap`, `decide_word`, `paired_table`, path-gate constants); argv takes exactly the §2 paths + `--root workspace/proxy_recal_r2_<uuid8>` + `--segment-index g` + `--num-segments 6` (refuse unless 6) + validation-seed + dual `--execute-synthetic --execution-authorized` flags (refuse without both); startup path-gate refuses any input outside the frozen nine and any `.ttbin`/`.npz`/`.parquet` path; root gate accepts only `workspace/proxy_recal_r2_[0-9a-f]{8}` and refuses `results/`/`outputs_comparison`/existing-root collisions; I-5 vs I-6 bitwise cross-check + transcription check identical to Packet A; §3.5 validation gate per segment (REFUSE = exit nonzero, zero decodes in that segment); then that segment's 40-frame Stage-1 m=200 cold run with the carried pin passthrough, rewriting `SEG_g.json` after every block; per-segment wall ≤ 1800 s / RSS ≤ 2 GiB / per-block 300 s gates; prints segment close line last; `main() -> int` + `if __name__ == "__main__"` house style. Plus a `--assemble` mode that reads the 6 SEG + manifest, enforces the §3.6 assembly gate, and writes D-1 + D-2 only on 240/240 (no decode in assemble mode). No `src/` touch, no Packet-A file edit. Per `AGENTS.md` §5.7: simplest implementation that is scientifically correct — no checksums, no atomic writes, no locking, no retry framework, no caching.
2. **T-R2-02** — Implement `comparison_bench/tests/test_proxy_recal_seg_fake.py` per §10 P-3 (fake-only; `-p no:cacheprovider`; fresh `workspace/proxy_recal_r2__pytest_<uuid8>` roots; zero scientific/real-data contact — hand constants only, reads no input file).
3. **T-R2-03** — Pre-EXECUTE measurement (§10 P-1…P-8) by main; fill the execution root uuid8 and validation seed only on PASS and only under the §14 execution grant (currently pending — this task is BLOCKED until the grant lands).
4. **T-R2-04** — Execute the six frozen §10 P-6 segment commands ascending (g = 0..5), then the frozen assemble command; operator writes SEG files + manifest + D-1…D-3. Any STOP (§9) retains evidence and returns to main; the only permitted rerun is the §8 preregistered infra repair. BLOCKED until grant.
5. **T-R2-05** — Independent batch-end review → D-4 (`BATCH_END_REVIEW.md`) against PR2-01…PR2-08; FAIL ⇒ rework + re-review, never publish-then-patch. BLOCKED until execution completes.

**Size note for orchestrator**: small enough to implement directly — one additive segmented driver (~150 lines: partition, per-block SEG rewrite, manifest, assemble gate; all math imported from the frozen Packet-A module) plus one fake-only test with hand-computable constants. No full pipeline needed. No `/opsx-explore` needed: every primitive (rates, masses, seeds, graph, settings, formulas, comparators, rule, budget chain) is frozen above; the sole delta (§3.6) is specified to the file level.
