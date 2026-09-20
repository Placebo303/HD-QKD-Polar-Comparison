# R23b RESULT — V72P3R23B-WEAK (DEAD-floor, descriptive)

Terminal: DEAD-floor (descriptive) per main-thread acceptance — NOT a non-scaling assertion. Synthetic-only; no scaling claim asserted.

## Execution evidence (Wb-ev, operator-attested)
- Exit 0; wall ~144 s + RSS ~199 MB (OPERATOR-ATTESTED).
- Budgets: sci 32/32, setup 4 (within caps sci ≤ 64 / setup ≤ 8).
- Per-cell: n1024:r65 0/16 + n128:r65 0/16 (exact-gap E_g 0/0 each).
- Exact 0, undetected 0; all 32 converged_no_syndrome @90.
- Calibration guard n128@0.65: 0/16 ≤ 4 — NOT tripped.
- GATE: literal DEAD (0 ≤ 2, gap +0) recorded AS DEAD-floor descriptive — both widths below edge, expected given ~uniform weak prior (mass ≈ 1/32); NOT a non-scaling assertion (symmetric to R23a ceiling handling).
- Prior ≈ uniform note: Model-F marginal at decoder input only; weak-prior mass ≈ 1/32 explains below-edge outcome.
- Verify: initial FAIL, 4 violations — arm 'S' vs 'W' predicate bug on reused-graph rows (decoder rows clean) → fix (b) applied (predicate accepts R23-builder 'S' on exact frozen seed set; decoder rows strict unchanged) + S-builder regression tests → re-verify checked = 32, violations = 0, PASS. No re-execution.

## Provenance
- Zero replacement / retune; seeds identical (reused 4801/4802 + 4811/4812).
- Prior read-only npz mtime unchanged.
- Decode ORACLE-free 32/32; truth = synthetic (no real data).
- Protected paths clean; no commit / push.

## Scratch root (6 files)
- `workspace/r23b_weak_73ef80ff-332e-4569-870f-cae33c41a89f/` (6-file root; see INDEPENDENT_ACCEPTANCE.md for manifest cross-check).

## Ceiling
- Synthetic-only. DEAD-floor is descriptive of this 0.65 weak-prior probe (0/16 + 0/16, below-both-edges); it asserts no scaling, FER, leakage, SKR, qualification, or real-data claim.

## Acceptance block
- Grant single-consumption: consumed once; no rerun/repair under this grant.
- Pre-EXECUTE Q1–Q6: satisfied (per frozen packet).
- Batch-end reviewer-go: PASS-WITH-REWORK (fix-then-reverify; fix (b) verified, re-verify 0 violations).
- Main-thread: ACCEPTED DEAD-floor (descriptive) + verifier-fix (b).
