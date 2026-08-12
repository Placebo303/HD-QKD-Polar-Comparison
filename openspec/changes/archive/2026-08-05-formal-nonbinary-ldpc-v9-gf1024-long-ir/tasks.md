# Tasks: Formal Nonbinary LDPC V9 GF(1024) Long-Block IR

## V9-00 — Freeze and Audit

- [x] **V9-00.1** Record HEAD, dirty-worktree scope, allowed file manifest,
  frozen V1-V8 hashes, existing output identities, and absence of V9 official
  output.
- [x] **V9-00.2** Freeze V9 roots/seed derivation and constituent identities;
  prove disjointness from prior evidence and across stages; freeze resource
  measurement, rank policy, leakage formulas, and stop rules.
- [x] **V9-00.3** Write an evidence note that V8 q=4 validates the method only,
  not GF(1024) threshold or FER.

## V9-10 — V9A GF(1024) Kernel

- [x] **V9-10.1** Implement full-vector q=1024 QSC message operations and
  coefficient-correct WHT check convolution with fail-closed normalization.
- [x] **V9-10.2** Cross-check q=4/8/32 and bounded sparse/dense q=1024 against
  the V8 direct oracle; add coefficient-order and numerical tamper tests.
- [x] **V9-10.3** Implement deterministic multi-seed MC-DE with exact sampled
  edge-view degrees, fresh channel terms, entropy convergence, and bounded
  resource accounting.

## V9-20 — V9A Ensemble Optimization and Gate

- [x] **V9-20.1** Compute H_q and m by formula for p=.20/.30 and f=1.15/1.08;
  create one plan-only package freezing all four searches, objectives, budgets,
  seeds, robust targets (.22/.32), target targets (.215/.32), degree bounds,
  and ties.
- [x] **V9-20.2** Optimize four separate irregular lambda candidates and build
  harmonic-exact rho distributions; prove reconstructed rates <=1e-12 error.
- [x] **V9-20.3** Independently read-only review the plan; execute exactly once
  deterministically for all four searches plus at least three disjoint fixed
  validation seeds; strict-replay exactly once; record conservative thresholds.
- [x] **V9-20.4** If robust thresholds are below .22/.32, freeze and STOP
  before codebooks. Apply .215/.32 target gates; target failure records
  `efficiency_target_not_met` and permits robust-only continuation. No rerun.

## V9-30 — V9B n=4096 Engineering

- [ ] **V9-30.1** Build deterministic irregular PEG/ACE-or-equivalent
  codebooks from accepted V9A ensembles with rank/cycle diagnostics, zero
  parallel edges, seeded nonzero GF(1024) labels, and `rank(H)=m`; reconstruct
  before plan or stop. Bind 4 ordered disjoint constituents per superframe.
- [ ] **V9-30.2** Implement error-domain layered log-FFT-SPA, frozen 100-150
  iterations, workers=1, full syndrome checks, resource caps, no truth/fallback.
- [ ] **V9-30.3 T0** Compile/import/structure/tiny-math tests pass.
- [ ] **V9-30.4 T1** Focused oracle, graph, decoder, invalid-input, numerical,
  identity, and disclosure tests pass.
- [ ] **V9-30.5 T2** Complete fake lifecycle plus strict replay and layered
  tamper matrix pass; tests cannot invoke production by default.
- [ ] **V9-30.6 T3** Frozen V8 and selected V5-V7 regression suite passes;
  frozen source/evidence hashes and no-output boundary pass.
- [ ] **V9-30.7** Independent engineering review accepts V9B before a canary
  plan is prepared.

## V9-40 — V9B Sacrificed Canary

- [ ] **V9-40.1** Prepare one fresh 4+4 p=.20/.30 n=4096 canary plan and bind
  code/graph/source hashes, identities, disclosure, gates, and resource caps.
- [ ] **V9-40.2** Independent read-only review returns ready; otherwise STOP.
- [ ] **V9-40.3** Execute exactly once with workers=1 and strict-replay exactly
  once; preserve outputs even on failure.
- [ ] **V9-40.4** Advance only at >=3/4 verified per stratum, zero forbidden,
  exact disclosure, median <=2h/superframe, peak RSS <=3GiB. Else freeze STOP.

## V9-50 — V9C n=16384 Bridge

- [ ] **V9-50.1** Build/test n=16384 from the accepted ensemble and write
  engineering evidence plus independent acceptance; require `rank(H)=m` and
  bind 16 ordered disjoint constituents per superframe with no cross-stage reuse.
- [ ] **V9-50.2** Prepare and independently review one fresh 4+4 canary plan.
- [ ] **V9-50.3** Execute exactly once with workers=1 and strict-replay exactly
  once.
- [ ] **V9-50.4** Advance only at >=3/4 verified per stratum, zero forbidden,
  exact disclosure, median <=8h/superframe, peak RSS <=3GiB. Else freeze STOP.

## V9-60 — V9C n=32768 Candidate

- [ ] **V9-60.1** Build n=32768 with exactly 32 ordered, disjoint 1024-symbol
  constituents per superframe and complete constituent provenance; require
  `rank(H)=m` before plan preparation.
- [ ] **V9-60.2** Freeze one fixed rate per stratum: target f=1.08 only where
  its .215/.32 gate passed, otherwise robust f=1.15 with
  `efficiency_target_not_met`; compute `m=ceil(f*H_q(p)*n)`, enforce syndrome
  `L_recon=10*m`, separate 64-bit tag, `L_total=10*m+64`, and these exact hard
  caps. Reject puncturing, shortening, adaptive stages, informative indices/
  control, or any additional reconciliation payload; defer blind work to V10.
- [ ] **V9-60.3** Complete T0-T3 milestone and independent engineering review.
- [ ] **V9-60.4** Prepare/review one fresh 4+4 canary; execute once and strict-
  replay once.
- [ ] **V9-60.5** Canary passes only at >=3/4 verified per stratum, zero
  forbidden, exact disclosure, median runtime <=16h, hard timeout 24h per
  superframe, and <=3GiB RSS. Else freeze STOP.

## V9-70 — V9C Development and Close-out

- [ ] **V9-70.1** Only after V9-60 PASS, prepare one fresh disjoint 16+16
  development plan; independently review it.
- [ ] **V9-70.2** Execute development exactly once with workers=1 and strict-
  replay exactly once.
- [ ] **V9-70.3** Record development-ready only at >=15/16 verified per
  stratum, zero forbidden, exact replay/disclosure, median <=24h/superframe,
  and peak RSS <=3GiB.
- [ ] **V9-70.4** Independent final review evaluates V9-A01..V9-A16; update
  decision log, handoff, current task, and durable memory with verified facts.
- [ ] **V9-70.5** Stop. Do not create qualification/confirmation/real/N4 or
  formal-comparison plans or outputs.

## Frozen Acceptance Matrix

| ID | Acceptance condition |
|---|---|
| V9-A01 | Additive scope; frozen baseline and V1-V8 unchanged |
| V9-A02 | V8 q=4 method-only boundary explicitly enforced |
| V9-A03 | GF(1024) WHT kernel agrees with independent direct oracle |
| V9-A04 | Full-vector MC-DE semantics, determinism, and fail-closed behavior pass |
| V9-A05 | H_q sizing and harmonic ensemble rate reconstruct exactly |
| V9-A06 | One reviewed/once-executed/replayed V9A package; robust gates reach .22/.32 |
| V9-A07 | Target gates use .215/.32; downstream fixed tier matches their result |
| V9-A08 | Finite graphs have rank(H)=m and meet parallel-edge/PEG-ACE/label/constituent contract |
| V9-A09 | Error-domain decoder matches oracle/tiny-cycle-free goldens and has no fallback |
| V9-A10 | Fake lifecycle, strict replay, deep tamper, no-overwrite, and production guard pass |
| V9-A11 | V9B canary lifecycle and gate are mechanically reconstructed |
| V9-A12 | V9C n=16384 lifecycle and gate are mechanically reconstructed |
| V9-A13 | Fixed-rate syndrome/tag leakage equals 10*m and 10*m+64; no other payload |
| V9-A14 | n=32768 32-frame provenance and canary gate pass |
| V9-A15 | n=32768 development gate and resource caps are reconstructed |
| V9-A16 | Evidence hashes/independent review complete; no unauthorized output/action |

## V9A Close-out (2026-08-04)

- [x] **V9A-C1** Strict replay: 9/11 files byte-identical; 2 provenance-only diffs. See `evidence/v9a_independent_review_acceptance.json`.
- [x] **V9A-C2** Independent reviewer-go ACCEPT: all checklist items pass; no blocking issues.
- [x] **V9A-C3** All execute/replay SHA256 hashes computed and recorded in acceptance JSON.
- [x] **V9A-C4** Replay overwrite incident documented: lifecycle defect, no scientific impact, restored from v2_execute copy.
- [x] **V9A-C5** Interrupted trials (pid 17948, pid 23652) frozen as non-decisional; excluded from gate decisions.
- [x] **V9A-C6** No V9B/V9C artifacts exist. V9-30 through V9-70 unchecked.
- [x] **V9A-C7** Docs updated: CURRENT_TASK.md, AGENT_HANDOFF.md, decision-log.md, memory.
- [x] **V9A-C8** Acceptance matrix: V9-A01..A05 covered; V9-A06/A07 FAIL; V9-A16 reached. V9-A08..A15 not reached.

**Result**: V9A frozen STOP. The frozen 8-candidate bounded enumeration failed its preregistered gates. This change is archive-ready pending archive action.

## Operator Return Conditions

Return only after either all reachable tasks complete through the first frozen
STOP gate (including immutable evidence and close-out), or a concrete blocker
is documented with exact command, error, remedies, changed files, preserved
artifacts, and the single decision needed. Do not return merely "in progress."
