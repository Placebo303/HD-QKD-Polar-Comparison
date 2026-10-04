# Change Proposal: real-ir-success-first

## Summary

Reframe the next phase of `HD-QKD_Polar_Comparison` around verified real information reconciliation (IR) success on high-dimensional arrival-time QKD data before final method selection.

The project should first prove that non-Polar methods can perform a real, protocol-disciplined reconciliation process on real paired-symbol frames. Efficiency comparison and final method selection come after verified success, leakage accounting, and failure diagnostics are reliable.

## Motivation

The current comparison layer has working infrastructure and several method paths, but most non-Polar methods have not yet demonstrated stable verified success on real data. Comparing efficiency metrics before this point risks optimizing artifacts rather than solving the actual QKD reconciliation problem.

The first-principles objective is:

- take real Alice/Bob high-dimensional arrival-time frames;
- reconcile Bob to Alice using only protocol-allowed public information;
- pass independent verification;
- account for public leakage;
- preserve failure statuses honestly.

## Scope

In scope:

- define real IR success criteria;
- add comparison-layer validation/reporting for real IR success;
- select a small representative real-frame set for iteration;
- establish Cascade-lite as the first non-Polar real-data success baseline if evidence supports it;
- diagnose Layered LDPC failures;
- probe qLDPC reference feasibility on easy real frames;
- write additive outputs and documentation.

Out of scope:

- modifying original Polar logic under `src/`, `experiments/`, or `tools/`;
- rerunning raw-data front-half workflows by default;
- full real-data benchmark sweeps before the representative path is validated;
- claiming production qLDPC or full industrial Cascade without implementation evidence;
- changing public schemas, CLI names, or config keys silently.

## Affected Areas

- `comparison_bench/` implementation and tests;
- `comparison_bench/configs/` for bounded representative configs if needed;
- `comparison_bench/docs/` or top-level `docs/` for success criteria and audit notes;
- `comparison_bench/outputs_comparison/` only through additive output paths;
- no original Polar baseline code.

## Success Criteria

- A documented real IR success contract exists.
- At least one bounded real-frame validation path can classify success/failure honestly.
- Cascade-lite is either shown to verify on representative real frames or its blockers are documented.
- Layered LDPC failures are bucketed by likely cause.
- qLDPC reference feasibility is tested on easy real frames without overclaiming status.
- All outputs are additive and traceable to configs/manifests.

## Risks

- Existing real frame artifacts may be insufficient or unavailable in a fresh environment.
- Some methods may require more channel modeling before they can verify on real frames.
- Leakage decomposition differs across methods and must not be compared casually.
- Historical error logs may contain stale failures and need careful interpretation.

