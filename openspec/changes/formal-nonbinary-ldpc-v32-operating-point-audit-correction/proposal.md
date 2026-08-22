# Proposal: formal-nonbinary-ldpc-v32-operating-point-audit-correction

- **Status**: candidate_only — pending Codex master ACCEPT/REJECT. Nothing in this
  change is a formal gate until the master records ACCEPT.
- **Author / orchestrator**: Ox Alpha (long-range research orchestration agent).
- **Date frozen**: 2026-08-22 (this session; git HEAD at freeze recorded below).
- **Repository state at freeze**: branch `main`, HEAD `dda3503ea54dba41f863dd6b3ce88a268bb61a18`,
  dirty scope = `AGENTS.md` (user modification, preserved, never staged).

## Goal

Correct the lifecycle and scientific semantics of the V32 operating-point
consistency audit (`formal-nonbinary-ldpc-v32-operating-point-consistency-audit`)
and produce an additive v2 evidence root that:

1. Retains the original audit `run_01` byte-identical as **post-hoc exploratory
   evidence** and retracts its scientific terminal attribution — without
   rewriting history.
2. Independently recomputes D0/D1/D2 from raw persisted records with corrected
   semantics, and redefines D3 as the exact-V31-rate empirical-P ensemble DE
   question.
3. Emits a candidate terminal using the priority
   `audit_evidence_inconsistent` > `audit_verifier_blocked` >
   `audit_corrected_rate_aligned_de_required`.

This correction runs **no DE, no decoder, no graph builder, no finite-control,
no raw-data pipeline, no longrun/minrerun/routeA, and never touches the sibling
Polar checkout**. It is read-only over all old evidence roots and additive at
exactly one new output root.

## Why: lifecycle defects of the existing audit change

The existing change
`formal-nonbinary-ldpc-v32-operating-point-consistency-audit` has the following
verified defects (evidence citations in `design.md §1`):

- L1. Implementation commit `60117174` precedes the complete OpenSpec commit
  `dda3503e`; the audit execution also precedes it.
- L2. The proposal/design/spec commit `dda3503e` was submitted after the run.
  The change therefore cannot serve as a pre-registered formal gate.
- L3. `tasks.md` P3–P5 checkboxes are unchecked, while
  `workspace/nbldpc_v32_operating_point_audit/OPERATOR_HANDOFF.md` claims
  "P5.2 R2 ACCEPT_CANDIDATE_EVIDENCE … 不存在 pending 状态".
- L4. No independent, verifiable R1/R2 reviewer artifact exists on disk;
  handoff prose cannot substitute for an independent acceptance record.

Handling principle: the old audit is neither deleted nor "repaired". It is
referenced and annotated in this correction only as:

```
post_hoc_exploratory_only
not_formal_pre_registered_gate
numerical_outputs_retained
scientific_terminal_superseded_pending_correction
```

## Why: scientific defects to correct (semantics, not numbers)

The old audit's numeric outputs are retained; its naming and attribution are not:

- S1. Persisted terminal `finite_graph_decoder_mismatch`
  (`nbldpc_v32_finite_de_bridge/run_01/candidate_terminal.json`) is not supported:
  arm B1 is not a matched empirical-joint control. B1 samples come from the
  generator law Q_B1 (Alice uniform + Bernoulli(raw_ser) + uniform nonzero delta)
  while the posterior comes from the V25 empirical joint P(A,B). A generator/posterior
  law mismatch cannot attribute divergence to the fixed QC graph or the decoder.
- S2. B2 `l2_errors_final=1024` is a **not_run sentinel**, not evidence of L2
  divergence.
- S3. B3/B4 improve-but-no-syndrome (~250→~179 mean L2 errors): substantive
  correction capability without syndrome convergence; they must not be called
  "divergent".
- S4. D1 full E_Q[-log P] is infinite (positive Q mass on P-zero cells);
  only conditional-over-finite-support means and common-support truncated cross
  entropies are finite, and they must be named as such.
- S5. D2 must report two separate laws: empirical P (nominal information budget
  feasible — nothing more) and original Q_B1 (information-theoretically infeasible
  at the current allocation); feasibility of nominal budgets does not prove
  finite-length/DE/fixed-graph/decoder feasibility.

## What: deliverables of this change

1. New OpenSpec (this directory), frozen before any implementation.
2. Correction verifier CLI (read-only recomputation):
   `comparison_bench/src/comparison_bench/cli/run_nonbinary_v32_operating_point_audit_correction.py`
3. Test suite T0–T3:
   `comparison_bench/tests/test_nonbinary_v32_operating_point_audit_correction.py`
4. One additive evidence root:
   `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_operating_point_audit_v2/run_01/`
   containing exactly: `audit_manifest.json`, `d0_failure_signature.json`,
   `d1_support_mismatch.json`, `d2_dual_law_feasibility.json`,
   `d3_next_question.json`, `corrected_branch_decision.json`,
   `readonly_review.json`, `operator_handoff.md`.
5. Workspace scratch under
   `workspace/nbldpc_v32_operating_point_audit_correction/<fresh-id>/`.
6. Draft-only successor materials (no execution, no registered change):
   a V33 rate-aligned empirical-channel ensemble DE OpenSpec draft and an
   NB-Polar feasibility concept note, both under `workspace/`.

## Affected specs

- Marks the delta spec
  `openspec/changes/formal-nonbinary-ldpc-v32-operating-point-consistency-audit/spec.md`
  as superseded-in-lifecycle by
  `specs/formal-nonbinary-ldpc-v32-operating-point-audit-correction/spec.md`
  (the old file itself is never edited).
- No merged spec in `openspec/specs/` is modified by this round.

## Success criteria (summary; normative text in spec.md)

All acceptance groups AC-D0, AC-D1, AC-D2, AC-D3, AC-L, AC-N, AC-R, AC-T pass;
candidate terminal is selected strictly by the AC-T priority; the final report
states `candidate_only`, awaiting Codex master ACCEPT/REJECT.
