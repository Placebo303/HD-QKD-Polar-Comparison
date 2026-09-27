# D1 Tag-Verification-Unit Memo (2026-09-27) — V80-NBLDPC-JAN21

- **Track:** documentation-only (AGENTS.md §1.2 — no track gate). This memo is a documentation/analysis product only.
- **Scope:** one analysis memo structuring findings already established by main through direct inspection. It discovers nothing new, runs nothing, and settles nothing.
- **What this memo authorizes:** nothing. No execution, no decoder, no scientific command, no `.ttbin`, no commit, no push. See §10.
- **Change context:** `openspec/changes/m2real-accounting-correction/`, decision **D-1 (tag verification unit)**, status DEFERRED and non-blocking (2026-09-27).

## 0. Deferral baseline (preserved verbatim in meaning)

D-1 was left DEFERRED and non-blocking on 2026-09-27 because it cannot be settled by reading code; it needs a frozen protocol specification.

- Design decision record (`openspec/changes/m2real-accounting-correction/design.md:439-443`): "D-1 (tag verification unit): DEFERRED. The user will not pick a unit by inference from code. It does not block T0: all tag totals are carried distinctly and D-1 decides only the headline column. Settling evidence, when it comes, is a frozen protocol specification, not a code reading."
- Tasks decided-status block (`openspec/changes/m2real-accounting-correction/tasks.md:95-97`): "D-1 (tag verification unit): DEFERRED — the single open item. The user will not pick a unit by inference from code. Scope of deferral: it does NOT block the T0 read-only recompute, because all tag totals are already carried distinctly (recorded 16x64-bit-per-block, one-tag-per-superframe nominal, one-tag column COUNTERFACTUAL); D-1 decides only which column is the headline. Resolving it later changes the headline f column, not any already-published column; the settling evidence is a frozen protocol specification, not a code reading."
- Design §§1–3 carry the same rule in full: the protocol under test is UNDETERMINED on the tag-unit point (`design.md:44-53`); the corrected record carries the recorded 16-tag total and the one-tag counterfactual distinctly and selects neither.
- This memo is consistent with that deferral and does not narrow, reinterpret, or close it.

## 1. The frozen V80 basis is LDPC-shaped and counts one tag per superframe

- Frozen formula (`docs/research_cycles/V80-NBLDPC-JAN21/S2_ACCOUNTING_MAP_20260920.md:16`): `f_super = (4·(5·(m₂+m₁)) + 64)/(1024·H_full)`, `H_full = 0.83256272`.
- The n=1024 whole-frame-with-tag row (`S2_ACCOUNTING_MAP_20260920.md:14`): `(4·245+64)/(1024·H_full) = 1044/852.544 ≈ 1.2246` (`f_super = 1.224570` repro).
- Frozen accounting is per superframe with a whole-frame 64-bit tag (`docs/ROADMAP-20260921.md:22`: "超帧 n=1024 GF(32) 符号、整帧含 64-bit tag").
- The triage records the S2 map line as the frozen resolution with the 64-bit tag explicit in the numerator (`docs/research_cycles/V80-NBLDPC-JAN21/LITERATURE_RECOMMENDATION_TRIAGE_20260921.md:32`: "`S2_ACCOUNTING_MAP_20260920.md:16`: `f_super=(4·(5·m)+64)/(1024·H_full)`，64-bit tag 显式入分子").
- The superframe amortizes the tag over four 256-symbol frames (`S2_ACCOUNTING_MAP_20260920.md:20-24`, including "four frames sharing one 64-bit tag" and "Budget 1.2246 < 1.3 holds BUT depends on … four frames sharing one 64-bit tag, zero extra disclosure").
- Structural reason (analysis, not a repo quote): an LDPC syndrome is global over the superframe, so one verification tag per superframe is correct for NB-LDPC, and `k` is not a free parameter for it. The one-tag convention is therefore structurally determined for the NB-LDPC family — it is not a choice among the M2 columns.

## 2. The tag unit is a property of the method's verification structure, not a free global choice

A cascade must verify each unit of correction to decide whether to advance, so its verification is per cluster. The repository transcribes the governing equations at `LITERATURE_RECOMMENDATION_TRIAGE_20260921.md:242-246`:

- `f = leak_IR/(n·H(X|Y))` (their Eq. 4); FER variant `f_FER = (1−FER)·f + FER/H(p)` (their Eq. 5) (`:240-241`).
- Effective efficiency (their Eq. 11) (`:242-244`): `f_eff = (1 − FER_cluster − P_Collision)·f + (FER_cluster + P_Collision)/H(q) + t/(n·H(q))`, with `FER_cluster = 1 − (1 − FER)^k` (their Eq. 12), where `k` is the number of blocks clustered into one cluster for the EV.
- Equivalent expansion (their Eq. 13, verbatim) (`:245-247`): `n·H(q)·f_eff = (1 − FER_cluster − P_Collision)·leak_IR + n·(FER_cluster + P_Collision) + t`, with the repository gloss "失败帧按'整帧 n bits 全部泄漏'计；EV 的 t bits 每次都泄漏".
- In that protocol `t` is a **per-cluster** tag, so the number of tags scales as (blocks)/k. Larger `k` means fewer tags but a higher cluster failure probability. This is a **trade-off with an interior optimum**, not two estimates of one quantity.

Corroborating entries:

- `docs/research_cycles/V80-NBLDPC-JAN21/LITERATURE_DIRECTION_MEMO_20260921.md:11-13`: their `f_eff` (Eq. 11) adds `t/(n·H(q))` with `t = 50`, plus `(FER_cluster + P_Collision)/H(q)`; the EV tag is NOT in their plain `f` ("EV tag NOT in plain f — their f_eff (Eq. 11) adds t/(nH(q)) with t = 50").
- `docs/research_cycles/V80-NBLDPC-JAN21/F_EFF_ACCOUNTING_NOTE_20260921.md:44` (item 1): "cluster frames for EV to choose optimal k" (Eqs. 11/12, Fig. 9) is "the principled version of our empirical 4-frame superframe tag amortization", and the penalty "is worst at high FER / short block / low QBER — exactly our regime".
- `F_EFF_ACCOUNTING_NOTE_20260921.md:45` (item 2): "one repeat request allowed per cluster" corresponds to the conditional rescue / HARQ.

Attribution caveat (see §6): the repository section carrying `:242-246` is headed as a Müller 2025 IET-Quantum-Communication full-PDF reading (`LITERATURE_RECOMMENDATION_TRIAGE_20260921.md:217-219`), not as the "Müller et al. 2024 (Quantum Inf. Process. 23, 195; arXiv:2307.02225)" label used in the tasking. The equations are cited here by their repository location; the 2024-bibliographic label was not verified in this memo session.

## 3. The two M2 columns are the two endpoints of that trade-off, not two estimates of one number

Frozen real slicing (`comparison_bench/src/comparison_bench/cli/m2real_runner.py:38-45`): eval superframes 205/287/383 per source; "every 1024-symbol superframe is cut into 16 consecutive 64-symbol blocks (the 1024 → 16×64 mapping is the single assumed frame map; anything else refuses)"; "A superframe counts success iff all 16 blocks are exact; its leak is the 16-block sum"; "FER uses the 64-block denominator (3280/4592/6128); superframe counts are a separate column, never the FER denominator."

The runner adds 64 bits per 64-symbol block, i.e. 1024 bits per superframe: per-block `tag_bits = 64` and `lambda_total = leak + tag + rescue + control` (`m2real_runner.py:749-755`); arm accumulation `lambda_parts.tag = TAG_BITS · n_done` with `lambda_total = lambda(sum_leak, TAG_BITS · n_done, …)` (`m2real_runner.py:786-801`) — line ranges per the adjudication, verified by inspection in this session.

Map the two columns onto the `(t, k)` curve:

- `f_with_recorded_tags` (16 tags/superframe) is the **k = 1** endpoint: maximum tag disclosure, and `FER_cluster` equal to the per-block FER (the most optimistic failure term).
- `f_one_tag_CF` (1 tag/superframe) is the **k = 16** endpoint: minimum tag disclosure, but `FER_cluster = 1 − (1−p)^16 ≈ 16p` for small `p`, so the failed-frame term `n·(FER_cluster + P_Collision)` scales up by roughly that factor (the most pessimistic failure term).
- The two endpoints therefore distort in **opposite** directions, and neither is "the" cascade number. The one-tag column is a counterfactual in which a cascade is charged LDPC-shaped verification. It SHALL NOT appear without the COUNTERFACTUAL_ONLY label (M2 design §3; `CORRECTION_RESULT.md` Tables C-1/C-2).

## 4. D-1 is material to the comparison, not a footnote

Persisted diagnostics (`docs/research_cycles/M2-REALCOMP/ACCOUNTING_REPLAY_RESULT.md:7-20`, corroborated at full precision in `docs/research_cycles/M2-REALCOMP/CORRECTION_RESULT.md:91-104` Table C-1):

- Real Layered-Binary arms: `f_ec_actual` 3.841563 / 3.919564 (1M), 3.834054 / 3.909601 (1p5M), 3.825003 / 3.900003 (2M) — i.e. around **3.83–3.92**.
- `f_recorded_tag` (`f_with_recorded_tags`): 5.089583 / 5.167584 (1M), 5.042819 / 5.118367 (1p5M), 5.025004 / 5.100004 (2M) — i.e. around **5.03–5.17**.
- `f_one_tag_CF`: 3.919564 / 3.997565 (1M), 3.909601 / 3.985149 (1p5M), 3.900003 / 3.975003 (2M) — i.e. around **3.90–4.00**.
- So the tag convention alone moves the LB figure by roughly **1.1–1.2 in f** (recorded-16-tag vs one-tag-counterfactual).

Compare against the measured NB-LDPC real-frame efficiency recorded for M0: the minimum measured `f_eff` is about **1.46** — specifically 1.464047 (1p5M, m=207) in `docs/research_cycles/M0-REALFRAME/RESULT.md:42-45` (full M0 table `:27-60`; other arms 1.493675–1.745385). Stated plainly: the tag convention is of the same order as a large part of the LB-versus-NB gap, so it must be settled or explicitly bounded.

No corrected LB-versus-NB verdict is computed here. None may be: the HDC arm is void on two independent grounds — the production verification path cannot return success (`docs/research_cycles/M2-HDCASCADE-SYNTH/BATCH_END_REVIEW.md:23-30` B1, `hd_cascade.py:224-229` with the `:280-281` gate; M2 design §§6/10) and the measured zero-correction count `exact_match = 0` in every one of the 28,000 real HDC blocks (`openspec/changes/m2real-accounting-correction/design.md:372-386` §11; `docs/research_cycles/M2-REALCOMP/CORRECTION_RESULT.md:145-154` §5; synth corroboration 0 of 78) — and the real LB `backend_used` is UNKNOWN (`CORRECTION_RESULT.md:114-127` Table C-2; design §5). This memo therefore sizes the tag effect only and produces no ranking.

## 5. No frozen protocol specification for HDC or LB verification granularity exists in this repository

This is stated as a finding:

- `m2real_runner.py:38-45` documents the 16×64 map as an **assumption** ("the single assumed frame map; anything else refuses") applied uniformly to BOTH method families, not a derivation for either. A cascade's cluster granularity and a layered-binary code's verification granularity are different objects and neither has been determined here — consistent with the M2 design's "the protocol under test is UNDETERMINED on this point" (`design.md:44-53`).
- Open question, flagged and not answered: a layered-binary implementation decodes Gray plane by plane (the M2 LB block entrypoint takes a per-plane row allocation and blind-stage table, `m2real_runner.py:508-549`), which raises the separate question of whether its verification granularity should be per plane rather than per 64-symbol block. This memo answers nothing about it; it records the question so a future frozen specification can settle it.

## 6. What was searched and not found

Recorded honestly, as relayed by main (not re-run in this documentation-only memo session):

- The sciverse corpus did not return the Müller cluster-EV paper: a title search returned unrelated printbook records, and only the arXiv abstract page was retrievable. Eqs. 11/12 were therefore taken from the repository's own verbatim transcriptions at `LITERATURE_RECOMMENDATION_TRIAGE_20260921.md:242-246` rather than from the publisher's typeset article.
- Consequence: the transcriptions should be re-verified against the typeset article before any D-1 resolution.
- Transfer limit (verified in-repo): the cluster parameters Müller reports are for a binary BSC at 2–6% QBER with n = 2^16 (`LITERATURE_DIRECTION_MEMO_20260921.md:11-13`: "binary BSC; EC frame n = 2^16 = 65536 b", "denominator n·H(q), q = true QBER 2–6%"), which is not our channel. That memo records the NOT-COMPARABLE verdict with the channel model as the dominant reason ("NOT COMPARABLE — dominant reason: channel model (binary BSC at 2–6% QBER vs our GF(32) structured channel …); n = 65536 vs 5120 secondary"). Their numbers therefore do not transfer to the GF(32) structured channel.

## 7. Options (presented; none chosen, none authorized)

These replace the "which column is the headline" framing with "report the cost as a function of the protocol parameter". **No option here is selected and none is authorized.**

- **(a) Report the `(t, k)` trade-off for the cascade family instead of choosing `k`.** Honest and more informative; converts the choice into a discussable curve. What it would change: the record would carry a family of values (tag disclosure vs cluster-failure term across `k`, endpoints anchored at the two existing columns) rather than one headline column. Evidence that would settle it: a frozen statement that the curve — not a point — is the reportable object, plus re-verified Eqs. 11/12 transcription (§6) and the per-`k` failure-term convention.
- **(b) Keep 1 tag/superframe for NB-LDPC and label it as structurally determined by the global syndrome, not as a choice.** What it would change: nothing numerically in the V80 basis; only the gloss — the one-tag convention for NB-LDPC would be recorded as following from the global-syndrome verification structure (§1), insulating it from whatever D-1 later decides for the other families. Evidence that would settle it: the existing frozen S2/ROADMAP accounting (§1) already suffices as the basis; no new measurement is needed, only the structural label.
- **(c) Determine Layered-Binary's verification granularity from its own structure (candidate: per Gray plane) rather than inheriting the runner's 16×64 assumption.** What it would change: a new, method-specific tag denominator for LB (possibly neither 16 nor 1 per superframe), with its own disclosure and failure-term accounting. Evidence that would settle it: a frozen determination of the LB verification unit from its decode/verify structure. This is a new scientific determination and would need its own frozen decision; **it is out of scope for the current M2 accounting change** and is recorded here only so it is not silently inherited from the runner assumption.

## 8. Consistency statement

- D-1 remains DEFERRED and non-blocking. The M2 accounting correction continues to carry all tag totals distinctly and to designate no headline; this memo changes no frozen quantity, no gate, no code, and no existing record.
- No conflict with the M2 accounting change or the V80 baseline was introduced by this memo (see the planner return for the line-level check). Where this memo's `(t, k)` framing goes beyond the change's "two columns, no headline" language, it is analysis only and does not amend the change.

## 9. Concrete next steps that would be needed to close D-1 (listed, not designed or scheduled)

1. A frozen protocol specification stating verification granularity per method (cascade cluster size `k` / tag `t`; layered-binary verification unit; NB-LDPC global-syndrome confirmation).
2. Re-verification of the Eqs. 11/12 transcription against the typeset article (§6).
3. A decision on whether the cascade is charged per cluster or per frame in the paper's headline table (i.e. which point — or curve — on the `(t, k)` trade-off is the headline, or whether the headline is the curve itself per option (a)).

None of these is designed, scheduled, or authorized here.

## 10. Authorization statement

This memo authorizes nothing and grants no execution. Any D-1 resolution, any recomputation, any real-data or formal run, and any change to a frozen quantity, gate, record, or code requires its own frozen packet and explicit grant under the applicable track.
