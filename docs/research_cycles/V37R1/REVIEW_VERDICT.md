# Review Verdicts: Cycle V37R1

---

## Milestone 2: Implementation Review

**Repository**: `Placebo303/HD-QKD-Polar-pipeline`
**Branch**: `formal-ir-mainline`
**Target SHA**: `3a64d1e9ad11625f3eee1fa6cafb5d75c7eaca39`
**SHA Verification**: VERIFIED
**Review Kind**: IMPLEMENTATION
**Cycle ID**: V37R1
**Advisory Verdict**: ADVISORY_ACCEPT

### Review Conclusion

The frozen V37-P1 implementation is accepted for development execution eligibility.

Accepted scope includes:
- Deterministic 0.05 simplex candidate enumeration.
- Exact population counts:
  - `raw = 1771`
  - `N2 necessary-gate = 547`
  - `final dcmax<=20 set = 259`
- P0 necessary forest-count integration.
- Distinction between necessary finite feasibility and actual Tanner-graph realizability.
- Regular $d_v=2$ matched reference baseline.
- V36 finite-inadmissible positive control.
- Source-specific empirical-P GF(32) DE setup.
- Harmonic-exact concentrated $\rho$ construction.
- $\text{AUT}_{30}$ and $H5/H10/H15/T_{0.10}/T_{0.01}/H60$ metrics.
- Per-source $\ge 5\%$ development effect-size gate.
- Deterministic screening winner selection.
- Fresh disjoint confirmation seeds.
- P1-B execution only when P1-A produces $\ge 1$ passing candidate.
- No fallback to a second candidate after confirmation failure.
- Correct terminal-state orchestration.
- Focused test coverage including actual pipeline-level PASS/FAIL confirmation branches and early-stop padding semantics (27 tests passing).

No scientific DE result has yet been produced.

### Claim Boundary

This acceptance means only: `IMPLEMENTATION_ACCEPTED_FOR_POSSIBLE_DEVELOPMENT_EXECUTION`.

It does NOT mean:
- A candidate has passed DE;
- Irregular NB-LDPC is superior;
- A finite Tanner graph exists;
- FER improves;
- Exact recovery improves;
- Key rate improves;
- V37 is scientifically promoted.

### Execution Authorization Status

- **DEVELOPMENT_EXECUTION_AUTHORIZATION**: `NOT_GRANTED` (`development_execution_authorized: false`)
- **FORMAL_EXECUTION_AUTHORIZATION**: `NOT_GRANTED` (`formal_execution_authorized: false`)
- Explicit user authorization is required before executing any development DE runs.

---

## Milestone 1: Plan Review

**Repository**: `Placebo303/HD-QKD-Polar-pipeline`
**Branch**: `formal-ir-mainline`
**Target SHA**: `661e2878f96f9fb84291bd601ebd3eb6abfcfdd4`
**SHA Verification**: VERIFIED
**Review Kind**: PLAN
**Cycle ID**: V37R1
**Advisory Verdict**: ADVISORY_ACCEPT

### Summary of Plan Acceptance

The plan for V37-P1 finite-feasible empirical-P DE screening (`docs/nbldpc-v37-p1-plan.md` and associated OpenSpec change `formal-ir-v37-finite-feasible-empirical-p-de-screening`) has been accepted by the user/main reviewer for implementation-only work.

Key frozen items:
- P0 necessary forest-count gate: $N_2 \le 183$ (547 candidates on 0.05 simplex grid over degrees $\{2, 3, 4, 5\}$).
- Additional pre-registered design cap: $d_{c,\max} \le 20$ (259 pre-registered candidates).
- Matched baseline: regular $d_v=2$ evaluated under identical settings ($N=4000, I=60$, GF(32), train empirical-P channel).
- Exploratory positive control: V36 $\lambda=\{2: 0.85, 4: 0.15\}$ tagged `finite_inadmissible=True` (reference only; non-promotable).
- Primary trajectory metric: $\text{AUT}_{30} = \sum_{t=0}^{30} H(t)$ measuring cumulative early-iteration entropy.
- Two-stage evaluation: P1-A screening (3 seeds/source) + conditional P1-B confirmation on fresh disjoint seeds (3 seeds/source) if screening passes.
- Advance threshold: $\ge 5\%$ reduction in $\text{AUT}_{30}$ across all three sources independently.

---

## Milestone 3: Development Execution Authorization

**Authorization Source**: Explicit user authorization (“我授权 V37R1 按已经接受的 implementation 运行 P1-A development DE，并且仅在冻结 screening gate 通过时运行 P1-B。”)
**Lifecycle State**: `DEVELOPMENT_EXECUTION_AUTHORIZED`
**Accepted Implementation SHA**: `3a64d1e9ad11625f3eee1fa6cafb5d75c7eaca39`
**Authorized Scope**: V37R1 frozen P1-A development DE (2,349 runs) and conditional P1-B confirmation (18 runs) only.
**P1-B Condition**: Executed if and only if $\ge 1$ finite candidate passes the frozen P1-A screening gate ($\Delta_s \le -0.05$ on all 3 sources independently, all seeds converge).
**Formal Execution Authorization**: `NOT_GRANTED`
**Scientific Promotion**: `NOT_GRANTED`
