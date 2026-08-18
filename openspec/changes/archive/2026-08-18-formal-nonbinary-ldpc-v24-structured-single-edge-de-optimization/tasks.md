# Tasks: formal-nonbinary-ldpc-v24-structured-single-edge-de-optimization

Status: **COMPLETE — V24 M0-M2 gate result FAIL (single_edge_bounded_optimization_failed); M3 closeout done; archived 2026-08-18**

## P — freeze and review

- [x] **P01** Freeze scope: q=1024 V17 structured channel, single-edge
  `lambda/rho`, target `R>=0.9375`, `f_total<=1.3`, degree cap 512.
- [x] **P02** Freeze M0 read-only accepted V8 corrected-trace path and exact
  lambda/rho/strict-entropy-streak/seed/scan fields; freeze channel,
  rate/leakage, 1–8-degree-support validity, and decision states. No V8 rerun.
- [x] **P03** Freeze M1 search representation, 512-candidate/8192-attempt
  ceilings, exact lambda-first/rho-second RNG calls, profile-valid versus DE-
  result semantics, development seeds, budgets, ranking, and selection.
- [x] **P04** Freeze M2 holdout seeds/budget and all-five-seeds PASS rule.
- [x] **P05** Freeze additive artifact set, T0–T3 evidence matrix, completed-DE-
  call `time.perf_counter` 24 h resource stop, no-overwrite/no-rerun rules, and
  claim boundary. No RSS hard gate.
- [x] **P06** Independent read-only freeze review: ACCEPT after three review
  passes; all execution-contract blockers were closed. Confirmed P01–P05 are
  internally complete and V23 is aggregate single-edge, not true MET/
  protograph DE.
- [x] **P07** User authorization granted by the current objective (2026-08-18) to
  formally archive V21->V22->V23, complete I01-I11, and run the frozen M0-M2 gate.

Stop rule: no implementation before P06 ACCEPT; no scientific execution
before P07. Any material amendment returns to P06 and P07.

## I — engineering (engineering pass only)

- [x] **I01** Add the minimal V24 profile representation and deterministic
  NumPy proposal generator; reuse V22b without modifying predecessor modules.
- [x] **I02** Implement validity checks and recomputation for normalization,
  degree bounds, design rate, leakage, `f_total`, sparse-support bounds, and
  duplicate identity. Do not include DE entropy/result in profile validity.
- [x] **I03** Implement M0 read-only accepted-trace validator and fail-closed
  transition to `mechanism_unverified`; do not bind or call a V8 runner.
- [x] **I04** Implement M1 screening/refinement orchestration with the exact
  frozen budgets, seeds, ranking, selection, complete proposal ledger, and
  additive output root.
- [x] **I05** Implement pre-holdout finalist persistence and M2 orchestration;
  enforce disjoint seeds and forbid replacement/tuning after holdout starts.
- [x] **I06** Implement machine-readable decision and a separate read-only
  semantic verifier that reconstructs validity, ranking, finalist selection,
  convergence, and gate state from records.
- [x] **I07** T0 checks: compile/import, known rate/accounting values,
  normalization, deterministic proposals, degree cap.
- [x] **I08** T1 checks: invalid/duplicate profiles, deterministic tie-break,
  seed disjointness, threshold boundary, attempt ceiling, and no overwrite.
- [x] **I09** T2 fake lifecycle with an explicitly injected fake runner,
  covering pass, fail, mechanism-unverified, resource-blocked, partial
  evidence retention, and verifier rejection of semantic tampering.
- [x] **I10** T3 optional read-only validation of the recorded V22b
  iter30/n200 artifact; keep it outside M1 ranking and execute no V8/V22b DE.
- [x] **I11** Independent candidate-delivery review: task-file manifest,
  focused diffs, frozen-directory check, test results, and confirmation that no
  production output or finite-code path was entered.

Engineering acceptance: I01–I11 pass. This state is not DE PASS and does not
authorize finite construction, FER, qualification, or promotion claims.

## M0 — authorized mechanism/accounting gate

- [x] **M001** Create a fresh additive V24 run root and persist the frozen
  manifest before scientific evaluation.
- [x] **M002** Read-only validate the accepted corrected V8 trace at
  `openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/evidence/v8_reproduction_trace_corrected.json`,
  including published lambda, corrected rho, strict `<0.01`/streak-20 rule,
  seed 2026080418, p scan, budgets, threshold, delta, and PASS. Do not execute.
- [x] **M003** Read-only verify the V8 rate identity, exact V17 channel values,
  entropy/accounting constants, and all V24 seed lists.

Stop rule: any M0 failure sets `mechanism_unverified`; M1/M2 do not execute.

## M1 — bounded development optimization

- [x] **M101** For each attempt `k=0..8191`, use independent
  `default_rng(SeedSequence([24000,k]))` and the exact order: lambda first with
  `np.arange(2,65,dtype=np.int64)`, then rho with
  `np.arange(2,513,dtype=np.int64)`; for each side call
  `s=int(rng.integers(1,9))`, then sorted
  `degrees=np.sort(rng.choice(frozen_degree_array,size=s,replace=False))`, then
  `np.full(s,1.0/s,dtype=np.float64)`, then
  `rng.multinomial(64-s,probabilities)+1`. No alternative API/order or extra
  RNG call. Canonicalize ascending `degree:count`, use first attempt k as ID,
  and retain first 512 unique profile-valid candidates plus the full ledger.
- [x] **M102** Screen every valid candidate at `n_samples=200`, `max_iter=50`,
  seeds 24001/24002; retain every result.
- [x] **M103** Rank by `(converged_count desc, worst_final_entropy asc,
  mean_final_entropy asc, candidate_id asc)`, treating error/non-finite as
  non-converged with `+inf`; errors still consume valid-evaluation slots.
  Persist `min(8,N_valid)` before refinement; N_valid is fixed by pre-DE
  profile validity and is never changed by DE outcomes.
- [x] **M104** Refine the selected set at `n_samples=1000`, `max_iter=150`,
  seeds 24003/24004/24005; retain every result.
- [x] **M105** Apply the same ranking to refinement and persist
  `min(4,N_refined)` finalist distributions before holdout. `N_valid=0` sets
  `mechanism_unverified` and forbids M2.
- [x] **M106** Read-only verify candidate count, attempt ceiling, complete seed
  coverage, rate/accounting validity, deterministic rankings, and that no
  holdout seed influenced M1.

Stop rule: no budget/seed/search expansion and no post-result amendment.
Within the single authorized M0–M2 invocation, append each completed DE call
and its `time.perf_counter` duration immediately. Then first test whether all
frozen evaluations are complete: if yes, compute PASS/FAIL even when time is
>=24 h; only if required evaluations remain and time is >=24 h, record
`resource_blocked` and do not start another call. An in-flight call may finish
and must be recorded before this check. Do not shrink or rerun the budget.

## M2 — independent holdout gate

- [x] **M201** Evaluate each pre-persisted finalist at `n_samples=2000`,
  `max_iter=200`, seeds 24101–24105, without profile replacement or mutation.
- [x] **M202** Mark a finalist PASS only if it remains valid and final base-q
  entropy is `<=0.01` on all five holdout seeds.
- [x] **M203** Set V24 `pass` iff at least one finalist passes M202; otherwise,
  after complete frozen execution, set `fail`.
- [x] **M204** Independent read-only acceptance: reconstruct every candidate
  gate and the final state; verify complete evidence, development/holdout seed
  separation, output additivity, and absence of finite-code/FER claims.

Stop rule: a failed holdout is retained and is never rerun, averaged away, or
replaced by a “closest” candidate.

## M3 — closeout

- [x] **M301** Record the exact terminal state and evidence index in
  `docs/decision-log.md`; correct any surviving statement that V23 tested true
  MET.
- [x] **M302** Update CURRENT_TASK, AGENT_HANDOFF, and AGENT_PROJECT_MEMORY with
  commands, artifacts, failures, warnings, and the authorization boundary.
- [x] **M303** Mark every task accurately: blocked/cancelled work is not
  completed; retain partial and invalid evidence with reasons.
- [x] **M304** Run required memory triage and final dirty-worktree/frozen-root
  review.
- [x] **M305** Archive V24 only after formal completion and user choice.

Terminal successor rule:

- PASS -> a separate finite-code proposal may be requested; nothing starts
  automatically.
- FAIL -> bounded single-edge optimization closes. True MET is only a new
  change candidate after explicit user authorization.
- `mechanism_unverified`/`resource_blocked` -> report the blocker; do not call
  it scientific FAIL and do not rerun without an authorized amendment.
