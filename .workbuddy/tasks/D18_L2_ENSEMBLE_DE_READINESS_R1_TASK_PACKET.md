# D18 Current-Channel L2 Ensemble DE — Readiness R1 Task Packet

## 1. Main-thread route decision

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Change: `v72p2d18-current-channel-l2-ensemble-de`
- Future batch track: `EXPLORE_HEAVY`; this packet is implementation/readiness
  only and authorizes zero scientific DE/decoder calls.
- Accepted predecessor:
  `D16_HOLDOUT_VALIDATION_COMPLETE_REVIEWED_AWAITING_ROUTE_DECISION`.
- Route: pause further L1 construction/decoder investment. Optimize the L2
  variable-degree ensemble under the exact current true-U1-conditioned channel,
  then validate a selected ensemble on finite L2 graphs in a later packet.
- D7-H, APP, joint decoding, real data, FER/leakage/SKR/qualification, and
  route closure remain out of scope.

## 2. Scientific adjudication to record first

- Preserve D17's preregistered result: L055 is `FALSIFIED` under the frozen
  rule comparing observed `27/32=0.84375` to the parameter-probability band
  `[0.8899387155669418,0.9955050869733582]`. Never relabel it after observing
  D16.
- Also record the interpretation ceiling: this is a mild model-calibration
  miss, not an L1-construction failure. L055 achieved 27/32 with per-graph
  `[7,7,6,7]`; L045 25/32 survived; L2-ORACLE achieved only 9/32 and survived
  its own prediction `[0,0.5]`.
- For future held-outs, distinguish a confidence band for latent `p_success`
  from a predictive interval for an observed binomial count. Add this as a
  forward methodology amendment only; do not recompute D16's registered
  verdict. Report the D16 binomial predictive/tail calculation descriptively.
- The legacy `D16_L2_DEGREE_SIGNAL` agrees directionally but remains secondary;
  the new route is a main-thread decision based on the complete evidence, not
  automatic inheritance of that terminal.

## 3. Reuse and channel identity

- Reuse the corrected D17 R2 production channel builder and explicit
  `L2_DV3_ORACLE` sampler dispatch. It must remain true-U1 conditioned,
  XOR-centered on U2, current Model-F candidate, GF32/poly37.
- Reuse the V26 MC-DE kernel, D9 degree/rho mathematics, D17 rate/delta axis,
  convergence rule, trajectory schema, budgets, and verifier patterns.
- Do not copy a DE kernel, Model-F loader, GF32 primitive, channel sampler, or
  candidate enumerator when an accepted helper can be imported.
- Prove callable identity/signature and current-channel entropy. D8/D9 L1
  outcomes and V26 historical numeric thresholds do not transfer.

## 4. Frozen candidate family

- Variable-node edge-perspective family only:
  `lambda={2:x,3:1-x}` for `x=0.00,0.05,...,1.00`, exactly 21 candidates.
- Candidate IDs use the accepted D8/D9 form
  `lam_d2_<x:.2f>_d3_<1-x:.2f>`; `x=0` is mandatory DV3 control.
- For each `(candidate,m)`, derive `rho` from exact `R=1-m/128` using the D9
  rule. No hand-set check distribution and no CE/f label.
- Current L2 row grid exactly `{89,94,99,104,109}` with
  `delta=5m/128-H_L2`; D17 DV3 `delta_DE=0.5468113653656221` is the baseline
  comparator, not a refittable value.
- Reject a candidate/cell before DE if socket realization is invalid, minimum
  check degree <2, maximum check degree >8, or rho is not normalized. Record
  refusals; do not replace candidates.

## 5. Frozen two-stage non-searching DE plan

### Stage S — bounded screen

- All 21 candidates × m `{94,104}` × seeds `2026094301..4304` × population
  4000: at most 168 calls.
- V26 `max_iter=60`, entropy tolerance `1e-4`, streak20.
- Rank all non-refused candidates deterministically by:
  `(S_m94 descending, S_m104 descending, worst_H60_m94 ascending,
  worst_H60_m104 ascending, candidate_id ascending)`.
- Select exactly the top three non-DV3 candidates plus DV3. If fewer than three
  non-DV3 candidates are executable, return engineering-blocked; do not widen
  the family.

### Stage C — confirmation

- For the selected four candidates only, complete the full five-m grid,
  seeds `2026094301..4308`, populations `{4000,16000}`.
- Reuse the 32 already-computed Stage-S identities for the selected candidates;
  never rerun them. Maximum new confirmation calls 288; total ceiling 456.
- The selected set is determined only by the frozen Stage-S rank. No manual
  substitution, outcome-driven extension, binary search, or extra seed.

### Candidate decision

- Recompute each selected candidate's pop16000 bracket using D17's exact
  `DE_BRACKET/DE_SOFT_BRACKET/DE_ONE_SIDED/POP_UNSTABLE` rules.
- Eligible only if it has a clean stable `DE_BRACKET`, no refusal, and
  `delta_DE <= 0.5077488653656221` (at least one n128 row step below the
  reviewed DV3 threshold).
- Rank eligible non-DV3 candidates by
  `(delta_DE ascending, worst_H60_at_hi ascending, max_check_degree ascending,
  candidate_id ascending)`.
- One winner only. The result selects a candidate for a later finite L2 packet;
  it does not authorize finite construction or claim optimality.

## 6. Terminals

- `D18_L2_DE_SELECT_ONE_ENSEMBLE`: at least one eligible; deterministic winner.
- `D18_L2_DE_NO_IMPROVING_ENSEMBLE`: completed plan, no eligible candidate.
- `D18_L2_DE_BASELINE_DRIFT`: recomputed DV3 result conflicts with the accepted
  D17 baseline beyond the frozen grid/stability rule.
- `D18_L2_DE_ENGINEERING_BLOCKED`: contract, resource, channel, refusal-count,
  or incomplete-plan failure.

All are synthetic DE evidence only.

## 7. Implementation/readiness tasks

- **E01** OpenSpec first: proposal/design/tasks/delta spec with §§1–6 verbatim
  in scientific effect.
- **E02** Add a thin D18 module importing corrected D17/D9/V26 helpers; document
  reuse and rejected duplication.
- **E03** Build the deterministic 21-candidate feasibility table, Stage-S plan,
  selection rule, conditional Stage-C plan, de-duplication, and terminals.
- **E04** Add a runner with `--profile-only`, `--de-sweep`, default-false
  `--execution-authorized`, fresh-root refusal, and read-only `--verify`.
- **E05** Freeze fresh DE seeds/root/command and budgets; prove all D16/D17 and
  predecessor seeds disjoint.
- **E06** Focused tests: exact candidate grid/IDs; rho/socket feasibility;
  stage counts/order; selection ties; overlap de-duplication; all terminal
  edges; corrected L2 sampler dispatch; APP/L1 exclusion; fake complete run;
  refusal/no-overwrite/tamper checks proportionate to scientific risk.
- **E07** PROFILE_ONLY: plan/candidate arithmetic only, zero DE/decoder calls,
  future root absent.
- **E08** Independent review with actual artifact access: channel identity,
  reuse, feasibility, frozen plans, rank/eligibility, budgets, no-production,
  D16 interpretation ceiling, and tests.
- **E09** Memory triage and one decision-log entry. No commit/push unless the
  task session's explicit scope safely permits a D18-only local commit.

## 8. Future execution boundary

- Freeze a fresh root under `workspace/d18_l2_ensemble_de_<uuid>` and one exact
  repo-venv command during readiness; root must remain absent.
- Maximum 456 scientific DE calls plus ≤16 setup units; wall ≤1800s;
  per-call ≤300s; RSS <2GiB; one CPU process; no retry/resume/seed-search/
  adaptive grid extension.
- One later explicit user grant may cover Stage S and the mechanically selected
  Stage C. This readiness packet grants none.

## 9. STOP conditions

STOP without scientific execution if the current true-conditioned L2 sampler
cannot be proven identical to corrected D17; D16's verdict would be rewritten;
the candidate/grid/selection is outcome-adaptive beyond §5; Stage-S overlap is
rerun; exact/syndrome/undetected are merged; APP/joint/L1 enters; seeds collide;
future root exists; or independent review has a blocker.

## 10. Return contract

Return only:

`D18_L2_ENSEMBLE_DE_READY_AWAITING_EXPLICIT_AUTHORIZATION`

with route adjudication; forward-only predictive-interval correction; reuse
map; exact candidates/feasibility; Stage-S/Stage-C plan and maximum calls;
eligibility/rank/terminals; command/root/budgets; tests/profile/fake/refusal/
verifier; independent verdict; zero scientific calls; root absence;
commit/no-push and memory state.

Do not run D18 DE, finite L2 graphs, D7-H, APP, real data, or make FER/leakage/
SKR/qualification/optimality/publication claims.
