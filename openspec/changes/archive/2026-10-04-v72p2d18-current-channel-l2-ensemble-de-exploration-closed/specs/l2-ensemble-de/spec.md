# Spec — Current-channel L2 ensemble DE (delta requirement set)

Scope: D18 readiness freeze (planner, no code). Normative language
(`SHALL`/`SHALL NOT`) binds E02–E09 implementation and E08 review. Packet
§§2/4/5 take precedence on any conflict; STOP rules are fail-closed.

## Adjudication (packet §2 — first, verbatim in effect)

- REQ-D18-ADJ-01: The L055 `FALSIFIED` verdict under the frozen rule
  (observed `27/32 = 0.84375` vs parameter-probability band
  `[0.8899387155669418, 0.9955050869733582]`) SHALL be preserved and SHALL
  NOT be relabelled after observing D16.
- REQ-D18-ADJ-02: The interpretation ceiling SHALL be recorded: mild
  model-calibration miss, NOT L1-construction failure (27/32 per-graph
  `[7,7,6,7]`; L045 25/32 survived; L2-ORACLE 9/32 survived `[0,0.5]`). No
  construction/optimality/route claim SHALL follow from it.
- REQ-D18-ADJ-03: The forward methodology amendment SHALL distinguish the
  latent-`p_success` confidence band (`[p_lo,p_hi]`, `design.md` §2.3(a))
  from the observed-count predictive interval/tail (`Binomial(n,p)` PMF,
  tail sum, quantiles, union over the band, `design.md` §2.3(b)), with each
  applied only to its question. It SHALL apply to future held-outs only;
  the D16 verdict SHALL NOT be recomputed.
- REQ-D18-ADJ-04: The descriptive D16 tail SHALL be exactly
  `T(p) = P(X <= 27 | n=32, p) = sum_{k=0}^{27} C(32,k) p^k (1-p)^(32-k)`
  evaluated descriptively at `p_lo = 0.8899387155669418` and
  `p_hi = 0.9955050869733582`. E01 SHALL compute no numeric value; E02/E06
  SHALL evaluate it as a descriptive test value that SHALL NOT revise any
  verdict.
- REQ-D18-ADJ-05: Legacy `D16_L2_DEGREE_SIGNAL` SHALL remain directional-
  secondary. The L2-ensemble route SHALL be recorded as a main-thread
  decision (pause L1, optimize L2 ensemble, later finite L2 validation),
  NOT automatic inheritance.

## Reuse and channel identity (packet §3)

- REQ-D18-REUSE-01: The implementation SHALL reuse the corrected D17 R2
  production channel builder and the explicit `L2_DV3_ORACLE` sampler
  dispatch, remaining true-U1 conditioned, XOR-centered on U2, current
  Model-F candidate, GF32/poly37.
- REQ-D18-REUSE-02: The implementation SHALL reuse the V26 MC-DE kernel
  (`max_iter=60`, `tol=1e-4`, streak 20), D9 degree/rho mathematics, D17
  rate/delta axis, convergence rule, trajectory schema, budgets, and
  verifier patterns.
- REQ-D18-REUSE-03: The implementation SHALL NOT copy a DE kernel, Model-F
  loader, GF32 primitive, channel sampler, or candidate enumerator when an
  accepted helper can be imported; E02 SHALL document the import map and
  each rejected copy.
- REQ-D18-REUSE-04: E02/E05 SHALL prove callable identity/signature of both
  production samplers and current-channel entropy. D8/D9 L1 outcomes and V26
  historical numeric thresholds SHALL NOT transfer as evidence or
  thresholds.

## Candidate family (packet §4)

- REQ-D18-FAM-01: The family SHALL be exactly `lambda={2:x,3:1-x}` for
  `x = 0.00, 0.05, ..., 1.00` (21 candidates) with IDs
  `lam_d2_<x:.2f>_d3_<1-x:.2f>`; `x=0` DV3 control SHALL be present.
- REQ-D18-FAM-02: Per (candidate, m), `rho` SHALL be derived from exact
  `R = 1 - m/128` via the frozen D9 rule. Hand-set check distributions and
  CE/f labels SHALL NOT appear.
- REQ-D18-FAM-03: The L2 row grid SHALL be exactly `{89,94,99,104,109}`
  with `delta = 5m/128 - H_L2`. D17 DV3 `delta_DE = 0.5468113653656221`
  SHALL be the baseline comparator and SHALL NOT be refit.
- REQ-D18-FAM-04: The socket gate SHALL refuse (record, no replacement) any
  candidate/cell with invalid realization, min check degree < 2, max check
  degree > 8, or unnormalized rho, before any DE call on it.

## Two-stage plan (packet §5)

- REQ-D18-STAGE-01 (Stage S): The screen SHALL be exactly 21 candidates × m
  `{94,104}` × seeds `2026094301..4304` × pop4000 — at most 168 calls — with
  the V26 `60/1e-4/20` rule. Ranking SHALL be exactly
  `(S_m94 DESC, S_m104 DESC, worst_H60_m94 ASC, worst_H60_m104 ASC,
  candidate_id ASC)`. Selection SHALL be exactly the top three non-DV3 plus
  DV3; fewer than three executable non-DV3 SHALL return
  engineering-blocked with NO family widening.
- REQ-D18-STAGE-02 (Stage C): Confirmation SHALL cover ONLY the selected
  four, on the full five-m grid with seeds `2026094301..4308` and pops
  `{4000,16000}`. The 32 Stage-S identities of the selected candidates
  SHALL be reused and SHALL NEVER be rerun. New calls SHALL NOT exceed 288;
  total SHALL NOT exceed 456. Selection SHALL be rank-only: no manual
  substitution, outcome-driven extension, binary search, or extra seed.
- REQ-D18-STAGE-03 (decision): Brackets SHALL be recomputed at pop16000
  with D17's exact `DE_BRACKET/DE_SOFT_BRACKET/DE_ONE_SIDED/POP_UNSTABLE`
  rules. A candidate SHALL be eligible ONLY IF it holds a clean stable
  `DE_BRACKET` AND has no refusal AND satisfies
  `delta_DE <= 0.5077488653656221`. Eligible non-DV3 SHALL be ranked by
  `(delta_DE ASC, worst_H60_at_hi ASC, max_check_degree ASC, candidate_id
  ASC)`. Exactly one winner SHALL be returned. The result SHALL select a
  candidate for a later finite-L2 packet and SHALL NOT authorize finite
  construction or claim optimality.

## Terminals (packet §6)

- REQ-D18-TERM-01: Terminals SHALL be exactly the four frozen labels with
  `design.md` §6 conditions: `D18_L2_DE_SELECT_ONE_ENSEMBLE` (≥1 eligible +
  deterministic single winner); `D18_L2_DE_NO_IMPROVING_ENSEMBLE`
  (completed plan, no eligible non-DV3);
  `D18_L2_DE_BASELINE_DRIFT` (recomputed DV3 conflicts with the D17 baseline
  beyond the frozen grid/stability rule); `D18_L2_DE_ENGINEERING_BLOCKED`
  (contract/resource/channel/refusal-count/incomplete-plan failure). All
  SHALL be labeled synthetic DE evidence only.

## Boundary, runner, tests, review (packets §7–8)

- REQ-D18-BOUND-01: The future root SHALL match
  `workspace/d18_l2_ensemble_de_<uuid>` (UUID picked at E05) with one exact
  repo-venv command frozen at E05; the root SHALL be absent throughout
  readiness. Ceilings SHALL be ≤456 DE + ≤16 setup, wall ≤1800s, per-call
  ≤300s (between/after-call check only), RSS <2GiB, one CPU process, no
  retry/resume/seed-search/adaptive extension. This packet SHALL grant zero
  calls; one later explicit user grant may cover S + mechanical C.
- REQ-D18-BOUND-02: The runner SHALL expose `--profile-only`, `--de-sweep`,
  default-false `--execution-authorized` (refuse before output/input reads
  when unauthorized, never overwrite), fresh-root refusal, and read-only
  `--verify`.
- REQ-D18-BOUND-03: E06 tests SHALL cover exact grid/IDs, rho/socket
  feasibility, stage counts/order, selection ties, overlap de-duplication,
  all terminal edges, corrected L2 dispatch, APP/L1 exclusion, a fake
  complete run, and proportionate refusal/no-overwrite/tamper checks —
  including the descriptive §2.4 tail as a test value only.
- REQ-D18-BOUND-04: E07 SHALL be plan/candidate arithmetic only with zero
  DE/decoder calls and proven root absence. E08 SHALL independently verify,
  with actual artifact access, channel identity, reuse, feasibility, frozen
  plans, rank/eligibility, budgets, no-production, the D16 ceiling, and
  tests; any blocker SHALL STOP promotion.

## STOP (packet §9)

- REQ-D18-STOP-01: Execution SHALL STOP with no scientific call if the L2
  sampler is unprovable identical to corrected D17; the D16 verdict would be
  rewritten; candidate/grid/selection is outcome-adaptive beyond §5;
  Stage-S overlap is rerun; exact/syndrome/undetected are merged;
  APP/joint/L1 enters; seeds collide; the future root exists; or
  independent review has a blocker.

(End of file)
