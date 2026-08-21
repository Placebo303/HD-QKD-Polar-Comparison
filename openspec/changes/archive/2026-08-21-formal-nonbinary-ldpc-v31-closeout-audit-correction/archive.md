# Archive: formal-nonbinary-ldpc-v31-closeout-audit-correction — 2026-08-21

**Change:** `formal-nonbinary-ldpc-v31-closeout-audit-correction` (Change A)
**Archived to:** `openspec/changes/archive/2026-08-21-formal-nonbinary-ldpc-v31-closeout-audit-correction/`
**Date:** 2026-08-21
**Schema:** closeout-audit-correction (A1-A12)

## Verdict: ARCHIVABLE — ARCHIVED

All A1-A11 [x], A12 now [x] after this archive decision. C01-C18 all ACCEPT (C01-C16 ACCEPT, C17 ACCEPT after A10, C18 ACCEPT after A11).

## Terminal

- **Change A terminal:** `closeout_corrected`
- **Scientific lifecycle:** `V31 ARCHIVED_PARTIAL`
- **Definition:** n=1024 full-window finite_graph_fail (300/300, 0 exact/tag, syndrome 0.00, L2 converged_no_syndrome) valid as bounded negative; n=2048 bounded 14-block diagnostic prefix on 1M only; original complete execution incomplete; global PASS impossible under original both-n requirement; bounded-prefix contingency post hoc (not pre-registered).

n=2048:
- 1M: 14/50
- 1.5M: 0/50
- 2M: 0/50
- total: 14/150
- remaining: 136/150

## Decoded-Block Accounting (corrected)

QC decoded: 0/314 exact/tag/syndrome (n=1024: 300/300; n=2048: 14/14)
PEG candidates were rejected during M2 construction/rank audit.
They did not enter block decoding and therefore do not have a decoder FER.

## Authoritative Evidence

- **Authoritative:** `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_closeout_audit_v2/run_02/` — closeout_verify.json (terminal closeout_corrected, C01-C18 PASS, contingency_post_hoc true, evidence_limitations with PEG replay limitation), closeout_recount.json, closeout_gate.json (ARCHIVED_PARTIAL, post hoc), closeout_run_manifest.json
- **Superseded (preserved):** `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_closeout_audit_v2/run_01/` — empty evidence_limitations, superseded because it omitted PEG replay limitation; retained byte-identical for history
- **Canonical (preserved byte-identical):** `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/` — 16 files byte-identical, no overwrite

## PEG Replay Limitation (persisted in run_02)

> "The canonical V31 manifest does not retain independently reconstructable rejected PEG packets. matrix_audits.json records two PEG rejection summaries, but the rejected constructions and rank decisions cannot be fully replayed from the persisted closeout inputs. This limitation does not alter the accepted QC packet recount or the n=1024 finite_graph_fail result."

Manifest does not retain independently reconstructable rejected PEG packets; matrix_audits.json records two PEG rejection summaries but rank decisions cannot be fully replayed. QC packet recount and n=1024 finite_graph_fail unaffected. C09 remains PASS with limitation persisted.

## Preserved Invariants

- No DE/decoder rerun (no_de_rerun true, no_decoder_rerun true; verifier static grep clean)
- No n=2048 completion (14/1M only, not 150 full window)
- No qualification/promotion (Change A success != V31 qualification, global PASS impossible)
- No forbidden diff (canonical 16, archive V31, old reports, src/experiments/tools byte-identical)
- No push (local commit ea319511 atop c8d2acab only)
- No V32 start (V32 finite-DE bridge is separate future change, not started)

## Git

- **Before:** HEAD c8d2acabccaae9d55a344e8f0c8ac1bb21ff9d1e (P1 freeze baseline)
- **A11 commit:** ea319511b2de74b96e33cf0f423306f57bd58242 — closeout-audit-correction: V31 ARCHIVED_PARTIAL (run_02 authoritative, run_01 superseded, PEG limitation, closeout_corrected) — local only, no push
- **Log:** `c8d2acab -> ea319511` (verified via .git/logs/HEAD line 470-471)
- **Status after:** This archive adds `openspec/changes/archive/2026-08-21-formal-nonbinary-ldpc-v31-closeout-audit-correction/archive.md` plus moved proposal/design/tasks/specs (preserved). No canonical/archive-old edits. The 7 excluded untracked remain excluded (workspace/, outputs_comparison/, etc. — not committed)
- **Diff --stat:** Only Change A additive files + addendum/decision-log/memory + this archive move; no canonical overwrite
- **Push:** NOT performed (local only)

## Delta Spec Sync

- Delta spec at `specs/formal-nonbinary-ldpc-v31-closeout-audit-correction/spec.md` — SHALL statements for closeout audit (audit-only, not a reusable method spec).
- Decision: NOT merged into `openspec/specs/` — Change A is terminal audit correction; V31 remains ARCHIVED_PARTIAL in archive, not promoted to canonical method spec. Note preserved here; no spec sync.

## Sources of Truth Consistent

- Addendum `docs/nbldpc-v31-closeout-audit-addendum-20260821.md` — references run_02 authoritative, run_01 superseded, ARCHIVED_PARTIAL, post hoc
- Decision-log `docs/decision-log.md` 2026-08-21 entry — same run_02 authoritative, PEG limitation, ARCHIVED_PARTIAL, post hoc
- Memory `AGENT_PROJECT_MEMORY.md` § V31 closeout correction — same authoritative run_02, lifecycle, limitation
- All three mutually consistent, all reference run_02

## Reviewer

- reviewer-go independent read-only T0/T1/T2 PASS (A8), no edits, frozen-directory diffs empty, no unauthorized production output

## Archivable Conditions Met

- [x] A1-A11 all [x]
- [x] C01-C18 all ACCEPT (C17 after A10, C18 after A11)
- [x] verifier authoritative run_02 with PEG limitation, run_01 superseded
- [x] addendum/decision-log/memory consistent (all run_02, ARCHIVED_PARTIAL, post hoc)
- [x] no forbidden diff, no promotion, reviewer PASS
- [x] git log ea319511 atop c8d2acab, no push

**Action:** Change archived; V31 closed as ARCHIVED_PARTIAL via run_02; no further V31 execution/push/V32.
