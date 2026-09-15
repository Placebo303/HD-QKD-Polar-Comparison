# Tasks — D17 Current-Channel Asymptotic-to-Finite Scaling

Legend: `[x]` done this call (D01, planner, no production code, zero
scientific calls); `[ ]` packet-exact future work (each needs its own
packet/authorization; `DE` batch + any claim-bearing run additionally needs an
explicit user grant with Pre-`EXECUTE`/Pre-`RESULT`).

## Readiness audit + spec (this call)

- [x] **A01 channel identity** — exact Model-F candidate prior/generator,
  axes, floor/renormalization, L1/L2 marginal/conditional channels for `D8–D16`
  proven from the rate-mother chain + `R`-audit entropy record + `D8–D16`
  cycle docs. Evidence: `proposal.md` §A01 (verdict EXACT; four recorded
  distinctions; no STOP). Spot files: `entropy.json`, N-prereg §1, `D16`
  design §5, `D15` log pre-dispatch.
- [x] **A02 DE inventory** — `V25/V26/V27` + `D8/D9` mapped by channel, layer,
  profile, rate definition, population, iterations, convergence metric; exact
  transfer/no-transfer table for V26 f1.3 conclusions. Evidence: `proposal.md`
  §A02 + `design.md` §4 (kernel/adapter/method transfer; no numeric transfer).
- [x] **A03 finite inventory** — table `F1–F19` from `D10–D15` roots with `n`,
  layer, profile, rows, recomputed `delta` (3-spot hand recompute ✓),
  graphs/blocks, exact/syndrome/undetected, decoder settings; clusters + root
  identity preserved. Evidence: `design.md` §3 (`D12/D14N/D15` summaries
  re-read this call; `R3/D11` rows provisional → `D02` confirm).
- [x] **A04 compatibility classes** — FIT / validation-only / descriptive-only
  per observation; `APP`/joint excluded from single-layer fit; `L2 ORACLE`
  only in the true-conditioned `L2` model. Evidence: `design.md` §3 classes +
  join rule (cluster+root retention; `D02` join-key check).
- [x] **A05 D16 holdout lock** — cells/seeds/command/root/budgets recorded;
  official root proven absent (`File not found` this call); banned seeds
  `2026094001..4012` + `2026094101..4108` listed; fake-identity scratch
  (`workspace/d16_align_20260915_a/`) locked out with fake-proof; seed grep
  clean outside `D16` plan/test/spec files. Evidence: `proposal.md` §A05 +
  `design.md` §7 gate.
- [x] **D01 OpenSpec freeze** — this change (`proposal.md`, `design.md`,
  `tasks.md`, `specs/de-scaling/spec.md`): L1–L4 hierarchy + probit law with
  `delta_DE/alpha/beta`, binomial likelihood + cluster-bootstrap/`LOO`,
  logistic sensitivity (descriptive), `epsilon 0.10/0.01` + integer row-backoff
  inversion at `n=64/128/256`, units, eligibility, frozen 15-point `DE` grid
  (points/seeds/rule/command/root/budgets), identifiability logic (two-param →
  `beta=0` → `MODEL_NOT_IDENTIFIABLE`), uncertainty, holdout schema + blank
  fields + fail-if-exists, residual separation, post-prediction
  rank/cycle/schedule measurement, claim ceiling. B-grid bounded and
  non-adaptive (no extension/binary search).

## Future asymptotic DE readiness (packet §4 — [ ])

- [x] **B01** Reuse accepted V26 `MC-DE` kernel + `D9` semantic adapter with no
  new kernel; three profiles (L1 L045, L1 L055, L2 DV3 true-conditioned) on the
  exact current candidate channel (`D15/D16` channel).
- [x] **B02** Parameterize rate by `delta`; derive ensemble `rho` from the
  exact rate (frozen `D9` rule); never use legacy `CE` labels.
- [x] **B03** Execute the §4 frozen bounded coarse-plus-confirmation grid
  (only after explicit authorization): bracket each transition with fixed
  points/seeds; no outcome-driven extension or binary search; population
  stability (`4000` vs `16000`) at the bracket.
- [x] **B04** Emit full trajectory summaries for the convergence definition;
  no `DE`↔row-layered trajectory claim beyond `D9` certified primitives.
- [x] **B05** Future `DE` batch command/root/budget with default-false
  authorization, `PROFILE_ONLY`, read-only verifier; root absent + unauthorized
  until the separately authorized run.

## Future finite-length scaling model (packet §5 — [ ])

- [x] **C01** Implement the predeclared probit law; fit separately per profile;
  `delta_DE` fixed from the reviewed `DE` result (never refit to finite data).
- [x] **C02** Fit `alpha>0`, `beta` by binomial likelihood with
  graph-cluster bootstrap / leave-one-graph-out uncertainty.
- [x] **C03** Apply the identifiability ladder (two-param → `beta=0` →
  `MODEL_NOT_IDENTIFIABLE`); never report unstable coefficients.
- [x] **C04** Logistic-link sensitivity fit, descriptive-only; NumPy/stdlib
  only, no new dependency.
- [x] **C05** Report implied integer row backoff at `n=64/128/256` with
  uncertainty for `epsilon=0.10` (primary) / `0.01` (sensitivity) —
  modeling targets, not `FER` qualification.
- [x] **C06** Persist all three `D16`-arm predictions (interval, expected graph
  dispersion, falsification criteria) before any `D16` execution; never revise
  after observing `D16`.
- [x] **C07** Separate residual diagnostics (rank/admission, four-cycles/girth,
  iterations, residual syndrome, graph random effects); not folded into the
  backoff without a new preregistration.

## Future implementation + review (packet §6 — [ ])

- [x] **D02** Audit artifact: compact `CSV`/`JSON` inventory (`F1–F19` +
  join keys) + report; read-only predecessor roots; confirm `R3/D11` rows;
  leave-one-root-out sensitivity.
- [x] **D03** `DE` adapter/runner: current-channel three-profile plan,
  fake-injected tests, authorization refusal, fresh root + verifier; zero
  scientific calls until authorized.
- [x] **D04** Scaling module: graph-aggregated exact binomial counts,
  deterministic fit/uncertainty, synthetic recovery tests (known parameters +
  non-identifiable fixtures), fail-closed banned-seed gate.
- [x] **D05** Holdout record: immutable `D16` prediction schema + blank outcome
  fields; fail if `D16` root exists before prediction freeze.
- [x] **D06** Focused validation: compile, math/channel equivalence, plan/grid,
  fake `DE`, fit recovery, eligibility isolation, root absence, no-production.
- [x] **D07** Independent review with actual artifact access: channel/`DE`
  identity, finite-data eligibility, equations/units, grid/budgets,
  identifiability logic, target-row inversion, `D16` holdout isolation, zero
  scientific calls. Any blocking finding → STOP.
