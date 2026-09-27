# M2 real accounting correction — Proposal

- Change: `m2real-accounting-correction`
- Track: **DECIDE (real-data artifact review)**. Per `AGENTS.md` §1.2 the
  applicability matrix requires the full DECIDE gate contract for
  real-data development/validation and for security/leakage calculations
  supporting claims. This change recomputes disclosure arithmetic from
  already-persisted real-result artifacts; it runs no decoder, opens no
  `.ttbin`, and modifies no existing root.
- Authority: `docs/research_cycles/M2-REALCOMP/MAIN_ADJUDICATION_20260926.md`
  (authoritative problem statement; 5 blocking findings; scientific
  acceptance WITHHELD; D2 branch (3) SUSPENDED). Predecessors, read-only:
  `docs/research_cycles/M2-REALCOMP/RESULT.md`,
  `INDEPENDENT_ACCEPTANCE.md`, `ACCOUNTING_REPLAY_RESULT.md`,
  `ACCOUNTING_REPLAY_PREREG_AND_AUTH.md`,
  `ACCOUNTING_REPLAY_INDEPENDENT_ACCEPTANCE.md`,
  `docs/research_cycles/M2-REALCOMP/PREREG_AND_AUTH.md` (G-M2-REALCOMP),
  decision-log 2026-09-24 (D2 frozen rule) and 2026-09-26 (WITHHELD /
  suspension entries), `docs/V80_BASELINE_20260921.md` §2 (frozen
  `(5m+64)` nominal basis), `docs/ROADMAP-20260921.md` §1.1 (64-bit tag
  per 1024-symbol superframe).
- Relation to `same-data-comparison-metrics` (docs-only draft): that
  draft freezes the A-CMPE-1..7 report contract for NB-LDPC same-data
  arms. This change is consistent with it (A-CMPE-1 outcome separation
  and `undetected` isolation, A-CMPE-5 source/arm separation, A-CMPE-7
  claim ceiling and measured/assumed/projected/qualified columns) and
  does not duplicate it: it scopes *which* A-CMPE-2/3 formulas may be
  applied to the M2 64-block HDC/LB arms, where the draft's single-tag
  `λ_total = leak_EC + 64` and `f_eff` slope were written against the NB
  1024-symbol superframe protocol. No existing spec text is modified.

## Goal

Close the M2 accounting gap as explicit written definitions, without
redecoding: freeze the tag-verification unit, the actual-disclosure f
as primary, the counterfactual labelling of the one-tag column, the FER
unit separation (with `f_eff` for HDC/LB dropped per decided D-2,
2026-09-27), the UNKNOWN backend provenance (with exact future persistence
requirements), the HDC method-identity scope limit, the RETIRED-for-M2 D2
state (decided D-3, 2026-09-27; rejected options recorded, no new rule set here), and the
status-column discipline. Then recompute corrected columns from
persisted artifacts only, retain original columns beside them with
clear status, and obtain an independent Pre-RESULT review plus
main-thread acceptance before any comparison number is citable.

## Non-Goals

- No redecoding, no `.ttbin` or bundle read, no decoder or construction
  call, no new execution of any method arm.
- No modification of `m2real_runner.py` (frozen executed evidence; its
  formulas are the subject of the findings and stay intact for
  provenance), of the three M2 T3 roots
  (`workspace/m2real_d4e5f6a7`, `workspace/m2real_b8c9d0e1`,
  `workspace/m2real_f2a3b4c5`), of `RESULT.md`, of the first
  independent review, or of any M0 artifact.
- No new D2 rule is set by this change; no D2 branch is evaluated; no
  method-family ranking, no `f_eff_actual`, no SKR, no qualification,
  no publication claim.
- No backend inference: the real LB backend is recorded as UNKNOWN and
  stays UNKNOWN; what is installed now proves nothing about the run.
- No new 1024-symbol `f_eff` slope is fitted onto 64-block FER; no
  HDC/LB number is promoted toward real-data FER/efficiency/leakage
  conclusions beyond the recorded-implementation arithmetic.
- No commit/push beyond the ordinary non-force named-branch policy;
  never into a branch carrying the Polar/sibling line.

## Impact Scope

- New: `openspec/changes/m2real-accounting-correction/` (proposal,
  design, tasks, one delta spec).
- New (gated): one corrected-accounting record document under
  `docs/research_cycles/M2-REALCOMP/` plus its independent Pre-RESULT
  review and main-thread acceptance entry; one fresh additive
  `workspace/` root only if the recomputation needs machine files
  (otherwise the record is a doc-only table verified by read-only
  recomputation — decided at preregistration).
- Read-only inputs: the three T3 `rows.json` summaries and the reviewed
  `workspace/m2_accounting_replay_20260926/diagnostic.json`
  (G-M2-ACCT-REPLAY, independent Pre-RESULT PASS for stored disclosure
  arithmetic only).
- Untouched: `src/`, `experiments/`, `tools/`, `results/`,
  `comparison_bench/outputs_comparison/`, all existing workspace roots,
  all M2/M0 cycle records.

## Acceptance Criteria

- AC-1: Every definition (a)–(h) from the tasking is frozen in
  `design.md` and traceable to a SHALL in
  `specs/m2-corrected-accounting/spec.md`, together with the
  HDC verification-path void extension of (f), the zero-correction
  void (design §11, `void-no-correction`, spec MAC-2/MAC-6/MAC-9 as
  revised 2026-09-27) and the HDC
  exclusion rule (design §6/§7/§9 choice 6/§10, spec MAC-6/MAC-9), the LB disclosure void (design §14/§10.2, spec MAC-10, decided D-5, 2026-09-27),
  per the M2-HDCASCADE-SYNTH batch-end review (FAIL, B1).
- AC-2: The corrected record carries, per source/family/m arm, both the
  original nominal columns (labelled historical/frozen-nominal) and the
  corrected actual-disclosure columns (labelled primary), the recorded-tag
  inclusive column, the one-tag column labelled COUNTERFACTUAL, separate
  block-level and superframe-level denominators, explicit per-column
  status, UNKNOWN backend, and assumed-v1 HDC scope — with `undetected`
  never merged into success and no status silently converted to `ok`.
- AC-3: At least one arm per source is independently recomputed from the
  persisted `rows.json` summaries; all 12 identities match; the
  discrepancy mechanism (nominal `1.20048829` vs actual `10.15137` /
  `3.84156` at 1M/m197) is reproduced, not merely asserted.
- AC-4: An independent Pre-RESULT review (separate thread) covering
  accounting, backend provenance, FER units, D2 applicability, status
  discipline, and claim ceiling records PASS or FAIL; FAIL blocks
  solidification. Main-thread acceptance stays BLANK until signed.
- AC-5: D2 branch evaluation is RETIRED for M2 (D-3, decided by the
  user 2026-09-27); "NB mainline enters M3" is carried, if at all, via
  the independent M0/P1 measured gap, not via a D2 verdict. No new D2
  rule text appears anywhere in the record except the rejected options
  (i)/(ii) recorded as considered-and-rejected.
