# Tasks: Formal Nonbinary LDPC V8 Reference Reproduction

## Phase V8-00 — Freeze and Audit

- [x] **V8-00.1** Record starting HEAD, dirty-worktree scope, allowed file
  manifest, forbidden directories, and absence of a V8 official output root.
- [x] **V8-00.2** Create an additive V7 scientific-interpretation audit. Keep
  V7 immutable; distinguish T0-T3 engineering PASS from canary failures.
- [x] **V8-00.3** Record R1B as an out-of-contract extra-observation diagnostic
  and R2 as an unvalidated scalar-DE implementation result.

## Phase V8-10 — Error-Domain Contract

- [x] **V8-10.1** Implement pure helpers for syndrome transformation and Alice
  reconstruction without importing a production decoder.
- [x] **V8-10.2** Add exhaustive/bounded q=4 and q=8 equivalence tests,
  coefficient-order tests, invalid-input tests, and fail-closed tests.

## Phase V8-20 — Independent Oracle

- [x] **V8-20.1** Implement direct probability-domain GF check convolution and
  variable update for small fields.
- [x] **V8-20.2** Implement brute-force tiny-code posterior/MAP enumeration.
- [x] **V8-20.3** Compare oracle and production check updates for deterministic
  q=4/q=8 cases and one-check GF(1024) sparse/dense vectors.
- [x] **V8-20.4** Enforce by import inspection/test that the oracle does not call
  V1-V7 FFT/FWHT/check-update/decoder functions.

## Phase V8-30 — Full-Vector QSC MC-DE

- [x] **V8-30.1** Implement QSC channel messages, full-q populations, direct
  check updates, variable updates, normalization, and base-q entropy.
- [x] **V8-30.2** Implement and test node-to-edge distribution conversion;
  reject ambiguous or unnormalized degree specifications.
- [x] **V8-30.3** Sample exact variable/check degrees and include a fresh
  channel term in each variable update.
- [x] **V8-30.4** Add deterministic regression tests that expose the old R2
  missing-channel and fixed-`dv_max` behavior.

## Phase V8-40 — Published Reproduction

- [x] **V8-40.1** Extract one exact q-ary QSC reference configuration with
  citation coordinates, conventions, perspective, target, tolerance, and
  local-extract SHA256. If unavailable, STOP `implementation_blocked`.
- [x] **V8-40.2** Freeze seed, population, iteration budget, convergence rule,
  and tolerance before running the reproduction.
- [x] **V8-40.3** Run the bounded reproduction once and record the complete
  trace/result. Do not tune against the target after the run.
- [x] **V8-40.4** Only on PASS, write a V9 recommendation that maps the
  reproduced construction to this project's single-side-information syndrome
  contract. Do not implement or execute V9.

## Phase V8-50 — Acceptance

- [x] **V8-50.1 T0** Compile/import/structure/tiny algebra tests pass.
- [x] **V8-50.2 T1** Focused oracle, MC-DE, invalid-input, numerical, and
  independence tests pass.
- [x] **V8-50.3 T2** Deterministic reference-reproduction tests and read-only
  evidence verification pass; no production runner is callable.
- [x] **V8-50.4 T3** Frozen nonbinary V1-V7 regression subset passes without
  modifying frozen files or artifacts.
- [x] **V8-50.5** Write source hashes, command results, parameter provenance,
  and acceptance matrix V8-A01..V8-A12 under `evidence/`.
- [x] **V8-50.6** Independently review the complete candidate. The implementer
  SHALL NOT self-accept.
- [x] **V8-50.7** Update decision log, handoff, current task, and durable memory
  only with verified facts.

## Frozen Acceptance Matrix

| ID | Acceptance condition |
|---|---|
| V8-A01 | Additive scope; frozen baseline and V1-V7 files unchanged |
| V8-A02 | V7/R1B/R2 interpretation audit recorded without evidence rewrite |
| V8-A03 | Error-domain syndrome and reconstruction equivalence passes |
| V8-A04 | q=4/q=8 brute-force MAP oracle passes |
| V8-A05 | Independent check oracle agrees at q=4/q=8 and bounded q=1024 |
| V8-A06 | Full-vector QSC MC-DE is deterministic and numerically fail-closed |
| V8-A07 | Edge-perspective distributions and exact sampled degrees verified |
| V8-A08 | Missing-channel/fixed-degree regressions detect old R2 behavior |
| V8-A09 | Precisely cited published q-ary reproduction passes, or concrete blocker returned |
| V8-A10 | Frozen V1-V7 regression subset passes |
| V8-A11 | No V8 scientific/lifecycle output created |
| V8-A12 | Evidence/source hashes and independent review are complete |

## Stop Rules

- Stop on ambiguity in the paper's degree perspective, channel convention, or
  target value; do not guess.
- Stop if oracle independence would require copying or vendoring external code.
- Stop on any V1-V7 or frozen-baseline modification.
- Stop on any request to run canary/development/confirmation/real/N4 work.
- Stop after one frozen published-reproduction run; do not tune and rerun.

## Operator Return Conditions

Return only when either:

1. V8-A01..V8-A12 are complete and independently reviewable; or
2. a concrete blocker is documented with the exact command, error/evidence,
   attempted safe remedies, files changed, and one decision required.

---

## Phase V8-60 — Audit Correction Close-out (2026-08-04)

Independent audit finding: the mean-matched concentrated check weights
approximate the edge-perspective rate condition (`w_lo = dc_hi - dc_mean` does
not make `sum_j rho_j/j = (1-R)*sum_i lambda_i/i` exact); the citation first
author was wrong; the tolerance arithmetic `0.005+0.003+0.0025=0.015` was
invalid. V8-60 corrects the formula (not a tuning), re-runs the reproduction
once with frozen corrected parameters, and closes the acceptance without
rewriting the original evidence.

- [x] **V8-60.1** Append the V8-60 correction addendum to proposal.md,
  design.md and this tasks.md (done by the main thread).
- [x] **V8-60.2** Fix `concentrated_check_distribution` to solve
  `sum_j rho_j/j = (1-rate) * sum_i lambda_i/i` exactly for adjacent check
  degrees `{floor(dc), ceil(dc)}` with `w_lo = (target - 1/d_hi) /
  (1/d_lo - 1/d_hi)`, `w_hi = 1 - w_lo`, `target = (1-rate)*integral_lambda`,
  `dc = 1/target`; integer `dc` degenerates to the regular degree. Add a
  `reconstructed_rate(lambda_edge, rho_edge)` helper.
- [x] **V8-60.3** Add tests asserting `|reconstructed_rate - target_rate|
  <= 1e-12` for the reproduction config and additional rate/lambda configs;
  re-record the frozen golden traces once under the corrected formula (same
  configs/seeds; recording, not tuning); keep the missing-channel /
  fixed-degree old-R2 regressions meaningful.
- [x] **V8-60.4** Fix `REPRODUCTION_CITATION` authors to Ronny Müller et al.
  exactly as listed on arXiv:2307.02225v2.
- [x] **V8-60.5** Preserve `evidence/v8_reproduction_trace.json`
  byte-identical; record its SHA256; write sidecar annotation
  `v8_reproduction_trace_precorrection_annotation.json` marking it as the
  pre-correction approximate trace; add a read-only test asserting the
  on-disk bytes still match the recorded hash.
- [x] **V8-60.6** Freeze corrected parameters BEFORE the run (n_samples
  100000, max_iter 150 per the paper; seed 2026080418; p_lo 0.01, p_hi 0.12,
  p_tol 0.0025; entropy_tol 0.01, streak 20; tolerance 0.012); execute the
  corrective reference run exactly once; write
  `evidence/v8_reproduction_trace_corrected.json`. No rerun, no tuning.
- [x] **V8-60.7** Record the auditable tolerance arithmetic in the trace and
  correction evidence: 0.0005 (3-decimal published rounding) + 0.00125
  (p_tol/2) + 0.005 (our MC error at 100000 nodes) + 0.005 (paper MC error at
  100000 nodes) = 0.01175 <= 0.012. Do not reuse the invalid 0.015 claim.
- [x] **V8-60.8** Run compile + V8 focused T0/T1/T2 (including the affected
  rate/reproduction tests); do NOT rerun T3; write
  `evidence/v8_60_correction_evidence.json` (commands, exit codes, counts,
  old->new constants and file hashes, manifest regeneration delta).
- [x] **V8-60.9** Independent read-only reviewer re-reviews the corrected
  candidate and writes `evidence/v8_independent_review_acceptance.json`
  (review scope, re-run commands/results, source hashes, V8-A01..A12
  conclusions). The implementer must not self-accept. [reviewer-go]
- [x] **V8-60.10** Main thread writes the additive
  `evidence/v8_acceptance_closeout_addendum.json` explicitly resolving the
  original `A12 = blocked` status (referencing the V8-60 review); the
  original `v8_engineering_acceptance.json` is not rewritten. [main thread]
- [x] **V8-60.11** Update tasks.md, docs/decision-log.md, CURRENT_TASK.md,
  AGENT_HANDOFF.md and AGENT_PROJECT_MEMORY.md noting that this was a
  non-tuning formula correction discovered by an independent audit.
  [docs/memory agents]
