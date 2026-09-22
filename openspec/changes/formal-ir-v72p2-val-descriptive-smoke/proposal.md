# V72P2 real VAL-reuse descriptive smoke

Status: PLAN_REVISED_FOR_MAIN_ACCEPTANCE. Cycle: V72P2-VAL.
Base: cd0b0e77c5cedbf3ac74d271cff3d6649f7043fc, branch formal-ir-v72p1-addendum-clean.
V72P1 accepted synthetic evidence and its historical implementation remain intact.

## Goal and authority

Measure one fixed 1M session, nine 1024-symbol blocks, with the existing hierarchical CAL-only prior and soft-joint mother. Report recovery, actual disclosure, model-relative efficiency, iterations and runtime even if all nine fail. Historical VAL is non-fresh; this is descriptive smoke, not independent confirmation, information-limit evidence, qualification or SKR.

The user explicitly requested the main conversation to plan/review and luna_worker to implement/execute V72. This cycle bounds that authority to these nine blocks; real execution remains gated on main-reviewer Pre-EXECUTE of the exact committed implementation. No other sources, retries, tuning, new worktrees, branch switches or promotion.

## Minimal delta

1. One runner and focused tests, reusing V70 hierarchical_P/select_lambda and V72P1 run_decoder.
2. Two narrow run_decoder corrections: warm-start residual measures change from incoming c2v on the first iteration too; returned hard decision uses factor/APP recomputed from the final c2v. No BP schedule, mother, numerical-parameter or API change. A historical test's initialization-only assertion is updated to the documented final-snapshot contract.
3. Preserve old artifacts. No artifact hashes, new registry framework, generator, damping, layered schedule or extra dependencies. The existing 64-bit reconciliation tag remains a protocol check, not an artifact integrity system.

Authoritative details and test IDs are in design.md, specs/spec.md and the cycle EXECUTION_PACKET.md.

Pre-execution amendment: retain the measured historical P1C one-iteration timing failure as non-blocking for this correctness-focused successor; all numerical checks remain mandatory. The design records exact evidence and replaces the blanket all-historical-timings-pass gate without changing any historical threshold, decoder kernel or real-run budget.
