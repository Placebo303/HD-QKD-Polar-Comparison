# Proposal — D18 Current-Channel L2 Ensemble DE (Readiness R1)

- Authority: `.workbuddy/tasks/D18_L2_ENSEMBLE_DE_READINESS_R1_TASK_PACKET.md`
  (§§1, 2, 3, 4, 5, 6, 8, 9 sole authority; §7 tasks; §10 return contract).
  Packet §§2/4/5 take precedence on any conflict; STOP rules are fail-closed.
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch
  `formal-ir-v72p1-addendum-clean` (verified this call via `.git/HEAD`;
  do not switch; no commit/push in this call).
- Track: `EXPLORE` readiness planning (OpenSpec-only, this call). Future
  scientific DE batch track: `EXPLORE_HEAVY`. This packet grants zero
  scientific DE/decoder calls.
- This call (E01, planner, no production code): OpenSpec freeze only
  (`proposal.md`, `design.md`, `tasks.md`, `specs/l2-ensemble-de/spec.md`).
  Zero DE/decoder calls, no roots created, no commits, no push.
- Predecessor: `D16_HOLDOUT_VALIDATION_COMPLETE_REVIEWED_AWAITING_ROUTE_DECISION`
  — verdict PRESENT (exact-string search, 9 hits; see Return section).
  Trusted read-only context: D16 B1 evidence, D17 A2 DE brackets, D17 R2
  corrected dispatch, V26 kernel + D9 rho rule, D17 rate/delta/convergence/
  trajectory/budget/verifier patterns.

## 0. Adjudication (packet §2 — recorded FIRST, verbatim in scientific effect)

1. Preserve D17's preregistered result: L055 is `FALSIFIED` under the frozen
   rule comparing observed `27/32=0.84375` to the parameter-probability band
   `[0.8899387155669418,0.9955050869733582]`. Never relabel it after observing
   D16.
2. Also record the interpretation ceiling: this is a mild model-calibration
   miss, not an L1-construction failure. L055 achieved 27/32 with per-graph
   `[7,7,6,7]`; L045 25/32 (`[7,6,7,5]`) survived; L2-ORACLE achieved only
   9/32 (`[3,1,2,3]`) and survived its own prediction `[0,0.5]`.
3. For future held-outs, distinguish a confidence band for latent `p_success`
   from a predictive interval for an observed binomial count. Add this as a
   forward methodology amendment only; do not recompute D16's registered
   verdict. Report the D16 binomial predictive/tail calculation descriptively
   (exact formula + inputs specified in `design.md` §2; numeric evaluation is
   E02/E06 implementation business as a descriptive test value — planner
   specifies formula only, no numeric value is computed in E01).
4. The legacy `D16_L2_DEGREE_SIGNAL` agrees directionally but remains
   secondary; the new route is a main-thread decision based on the complete
   evidence, not automatic inheritance of that terminal.
5. Route (packet §1, main-thread decision, not automatic inheritance): pause
   further L1 construction/decoder investment. Optimize the L2
   variable-degree ensemble under the exact current true-U1-conditioned
   channel, then validate a selected ensemble on finite L2 graphs in a later
   packet. D7-H, APP, joint decoding, real data, FER/leakage/SKR/
   qualification, and route closure remain out of scope.

## Goal

Freeze, before any new execution, the complete readiness contract for a
bounded non-searching two-stage current-channel L2 variable-degree ensemble
DE screen: adjudication-first record, reuse map, frozen 21-candidate family
with socket feasibility gate, frozen Stage-S/Stage-C plans with rank-only
selection and de-duplication, eligibility/winner decision rule, four
terminals, future execution boundary, and STOP conditions. The result selects
at most one candidate ensemble for a later finite-L2 packet; it authorizes no
finite construction and claims no optimality.

## Non-Goals

No DE/decoder execution or authorization; no new DE kernel (reuse V26 + D9 +
D17 adapters); no threshold refit from finite data (D17 DV3 `delta_DE` is a
baseline comparator, not refittable); no D16 rerun/refit/relabel; no finite
L2 construction; no APP/joint/L1 work; no D7-H revival; no FER/leakage/SKR/
qualification/publication/optimality/route-closure claim; no change to any
predecessor root, frozen baseline (`src/`, `experiments/`, `tools/`),
`AGENTS.md`, or decision log; no commit/push in this call.

## Impact Scope

- Added only: `openspec/changes/v72p2d18-current-channel-l2-ensemble-de/`
  (`proposal.md`, `design.md`, `tasks.md`, `specs/l2-ensemble-de/spec.md`).
- Read-only inputs (never modified): D16 B1 evidence, D17 A2 DE brackets and
  R2 corrected dispatch, V26 kernel, D9 rho mathematics, D17 rate/delta axis,
  convergence rule, trajectory schema, budgets, verifier patterns, D8/D9 L1
  outcome records (non-transfer reference only).
- Forbidden this call: code/scripts/tests/roots/`AGENTS.md`/decision-log
  edits, commits, pushes, branch switch, any DE/decoder call.

## Acceptance Criteria

1. §2 adjudication recorded FIRST and verbatim in scientific effect
   (FALSIFIED preserved, ceiling, forward-only amendment, descriptive tail
   formula without recompute, secondary-signal status, main-thread route).
2. §3 reuse map frozen (corrected D17 R2 builder + explicit L2-oracle
   dispatch; V26 kernel; D9 rho; D17 rate/delta/convergence/trajectory/
   budgets/verifier; callable identity + entropy proof required; D8/D9 L1
   outcomes + V26 thresholds non-transfer; rejected duplication listed).
3. §4 family frozen (21 lambdas, exact IDs, DV3 control, D9 rho from exact
   rate, no hand-set checks, no CE/f labels, 5-m L2 grid + delta axis, DV3
   baseline non-refittable, socket gate with refuse+record/no-replace).
4. §5 two-stage plan frozen (Stage-S ≤168 with rank + top-3+DV3 rule +
   engineering-blocked edge; Stage-C selected-4-only with 32-identity reuse,
   ≤288 new, ≤456 total, rank-only selection; decision recompute +
   eligibility threshold `0.5077488653656221` + winner rank + candidate-only
   effect).
5. §6 four terminals frozen with exact conditions (incl. BASELINE_DRIFT grid/
   stability rule).
6. §8 boundary frozen (fresh-root pattern, exact command deferred to E05,
   root absent, ≤456 DE + ≤16 setup, 1800s/300s/2GiB/1-proc, no retry/resume/
   search/adaptive, one later grant may cover S + mechanical C, this packet
   grants none).
7. `tasks.md`: E01 `[x]`, E02–E09 packet-exact `[ ]`.
8. Zero scientific calls; DE/decoder counters 0; no commit/push.

## Frozen plan summary (§§3–6, 8–9 in scientific effect; full freeze in `design.md` + delta spec)

- Reuse (§3): corrected D17 R2 production channel builder + explicit
  `L2_DV3_ORACLE` sampler dispatch (true-U1 conditioned, XOR-centered on U2,
  current Model-F candidate, GF32/poly37); V26 MC-DE kernel; D9 degree/rho
  mathematics; D17 rate/delta axis, convergence rule, trajectory schema,
  budgets, verifier patterns. Prove callable identity/signature and
  current-channel entropy. D8/D9 L1 outcomes and V26 historical numeric
  thresholds do not transfer. No copied kernel/loader/primitive/sampler/
  enumerator when an accepted helper can be imported.
- Family (§4): variable-node edge-perspective `lambda={2:x,3:1-x}`,
  `x=0.00..1.00` step `0.05`, exactly 21 candidates, IDs
  `lam_d2_<x:.2f>_d3_<1-x:.2f>`; `x=0` DV3 control mandatory. Per
  (candidate, m): `rho` from exact `R=1-m/128` via D9 rule; no hand-set check
  distribution, no CE/f label. L2 row grid `{89,94,99,104,109}`,
  `delta=5m/128-H_L2`; D17 DV3 `delta_DE=0.5468113653656221` baseline
  comparator, not refittable. Socket gate: invalid / min-dc<2 / max-dc>8 /
  rho-unnormalized → refuse+record, no replacement.
- Stage S (§5): 21 × m`{94,104}` × seeds `2026094301..4304` × pop4000 ≤168
  calls; V26 `max_iter=60`, `tol=1e-4`, streak20; rank
  `(S_m94↓,S_m104↓,worst_H60_m94↑,worst_H60_m104↑,id↑)`; top-3 non-DV3 + DV3;
  <3 executable non-DV3 → engineering-blocked.
- Stage C (§5): selected 4 only; full 5-m grid; seeds `2026094301..4308`;
  pops `{4000,16000}`; reuse 32 Stage-S identities, never rerun; max new 288,
  total ceiling 456; rank-only selection (no substitution/extension/search/
  extra seed).
- Decision (§5): recompute pop16000 brackets with D17 exact
  `DE_BRACKET/DE_SOFT_BRACKET/DE_ONE_SIDED/POP_UNSTABLE` rules; eligible iff
  clean stable `DE_BRACKET` + no refusal + `delta_DE <= 0.5077488653656221`
  (≥ one n128 row step below reviewed DV3; arithmetic verified in Return);
  rank eligible non-DV3 by `(delta_DE↑, worst_H60_at_hi↑, max_dc↑, id↑)`; one
  winner only; selects candidate for a later finite-L2 packet (no
  construction/optimality).
- Terminals (§6): `D18_L2_DE_SELECT_ONE_ENSEMBLE` / `D18_L2_DE_NO_IMPROVING_ENSEMBLE`
  / `D18_L2_DE_BASELINE_DRIFT` / `D18_L2_DE_ENGINEERING_BLOCKED` (exact
  conditions in `design.md` §6). All synthetic DE evidence only.
- Boundary (§8): fresh root `workspace/d18_l2_ensemble_de_<uuid>` + one exact
  repo-venv command frozen during E05/readiness; root absent; ≤456 DE + ≤16
  setup; wall ≤1800s, per-call ≤300s, RSS <2GiB, 1 proc; no retry/resume/
  seed-search/adaptive grid extension; one later explicit user grant may cover
  Stage S + mechanically selected Stage C; this packet grants none. UUID
  selection is E05 implementation business — planner reserves the naming
  pattern only.
- STOP (§9): no scientific execution if L2 sampler unprovable identical to
  corrected D17; D16 verdict rewritten; candidate/grid/selection
  outcome-adaptive beyond §5; Stage-S overlap rerun; exact/syndrome/
  undetected merged; APP/joint/L1 enters; seeds collide; future root exists;
  or independent review has a blocker.

## Claim ceiling

Synthetic DE evidence only. No FER/leakage/SKR/qualification/promotion/
publication/optimality/route-closure claim. The winner is a candidate for a
later finite-L2 packet, not a validated code.

## Return

`E01 DONE` (details in the final message). Execution false; DE/decoder calls
`0`; no commit/push. Next: E02–E09 per `tasks.md` (each needs its own
authorization; future DE batch additionally needs one explicit user grant +
Pre-EXECUTE).

(End of file)
