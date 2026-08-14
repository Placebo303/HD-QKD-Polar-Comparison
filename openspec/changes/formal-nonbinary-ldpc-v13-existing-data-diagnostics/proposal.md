# Proposal: V13 Existing-Data Nonbinary LDPC Diagnostics

## Status

**PLAN DRAFTED / EXECUTION NOT AUTHORIZED** (2026-08-14).

This change is a planning packet only. Planning items V13-P01--P07 are
drafted; V13-P08 (independent read-only freeze review) is pending. No
implementation, telemetry hook, decoder execution, real-data decode, or
qualification is authorized by this proposal.

## Why

V12 ended honestly at `source_partition_blocked`: all 768 existing 10 dB
bw200 rows were covered by historical V4/V5 frame or payload identities, so
there were no collision-free rows for V12's fresh-canary contract. This is a
freshness failure, not evidence that the local data set is too small or that a
decoder has already been tested on it.

The existing 10 dB Type-II, q=1024, Gray, 256-symbol data are nevertheless
large enough for a **retrospective diagnostic/development** study. V13 asks
which interface, channel-prior, numerical/convergence, or finite-graph/rate
mechanism most plausibly explains the nonbinary LDPC failures. It deliberately
uses existing identities as diagnostic evidence and therefore cannot call the
data fresh, confirmatory, qualifying, or promotional evidence.

## Scope

- Bind the observed V7 R1A fact ("V7 R1A failed its synthetic p=.20/.30
  canaries; no real-data evidence"), V10 `failed_ensemble`, V11
  `failed_coupling`, V12 `source_partition_blocked`, and binary V5 10 dB
  control facts without rewriting them.
- Reconstruct a complete role ledger for existing 10 dB bw120/bw180/bw200
  frames. Use bw200 as the primary stratum; inspect bw120/bw180 only after a
  bw200 root-cause conclusion.
- Partition mutually exclusive `characterization`, `development`, and
  `retrospective_audit` roles when historical role records permit an
  unambiguous reconstruction; otherwise stop at `blocked_role_ledger`.
- Plan channel characterization, a tiny engineering oracle, optional decoder
  telemetry equivalence, and one unchanged V7 R1A baseline probe. Alice truth
  is permitted only for offline diagnosis and post-hoc exact-correction
  checking.
- Produce a diagnostic-only root-cause report and, only after that report and
  a new amendment review, select at most one one-factor candidate route.

## Out of Scope

- Reopening V7 R1A, V10, V11, or V12; rerunning their rejected routes; or
  relabeling any prior result.
- Calling an existing frame `fresh canary`, `confirmation`, `qualification`,
  `promotion`, or `observed_fresh_correction`.
- New acquisition as a prerequisite for this diagnostic study. A later fresh
  acquisition or formal qualification requires a separate OpenSpec change.
- Simultaneously changing prior, matrix/graph/rate, and decoder; route sweeps;
  result-dependent tuning; or reusing audit truth in decoder control.
- Changes to frozen `src/`, `experiments/`, `tools/`, or `results/`.

## Affected Areas

- Future implementation, if separately authorized: `comparison_bench/` only.
- Diagnostic outputs: additive
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/<run_id>/`.
- The six-file plan includes `diagnostic_outcomes.csv` (baseline, candidate
  development, and retrospective-audit rows with `phase` and `method`), not a
  qualification-results file.
- Tests: fresh `workspace/nbldpc_v13_<uuid>/` roots only.
- Planning and handoff documents listed in this change; no official
  `formal_ir_methods` qualification root is used.

## Decision Requested

Approve only **V13-P08 independent read-only freeze review** of this packet.
The review may accept, reject, or return the plan for correction. It does not
authorize a decoder, a real-data baseline probe, or any D/R/I/E/A/C task.
