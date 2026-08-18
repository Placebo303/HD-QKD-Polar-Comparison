# Proposal: formal-nonbinary-ldpc-v21-bob-only-selector-validation

> Status: CONCLUDED_STOP_GATE_TRIGGERED_PENDING_ARCHIVE.

## What was evaluated

V21 evaluated Bob-executable q=1024 short-block strategies S0 BP-only, S1
bounded4-only, and S2 BP-first-fallback-bounded4 on 64 new n=64 frames. Alice
was intended to be confined to offline metrics rather than decoder selection.

## Observed result

- S0: 24/64 exact, FER 0.625.
- S1: 28/64 exact, FER 0.5625.
- S2: 28/64 exact, FER 0.5625.

All observed FER values are at least 0.45, so the declared stop condition was
met and the short-block OSD/top-K branch was stopped.

## Evidence limitation

The result is retained as `diagnostic_only`, not qualification or promotion.
P0/P1 were not actually pre-frozen before execution. Tests included a static
AST Alice-reference check, but the planned runtime Alice-injection semantic
verifier and V01 independent semantic verification were not run. An AST test
is not equivalent to a completed runtime semantic verification.

These gaps do not improve the observed FER and do not reopen the stopped
branch; they prevent describing V21 as fully pre-registered or independently
semantically verified.

## Archive boundary

V21 remains active only for formal closeout. Actual archive movement requires
an independent read-only closeout review followed by explicit user
authorization.
