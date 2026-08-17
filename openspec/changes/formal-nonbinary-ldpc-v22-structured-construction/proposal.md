# Proposal: formal-nonbinary-ldpc-v22-structured-construction

> Status: DRAFT — triggered by V21 stop gate.

## What
Move from short-block OSD/top-K candidate selection to paper-faithful structured
constructions (MET/protograph or SC-LDPC) for q=1024 nonbinary LDPC, with a DE
gate before finite-length coding.

## Why
V21 Bob-only validation on 64 fresh frames:
- S0 BP-only FER=0.625
- S1 bounded4-only FER=0.5625
- S2 BP-first-fallback-bounded4 FER=0.5625
All >= 0.45, so the short-block OSD/top-K branch is frozen as
`scientific_not_ready`. Further gains require a different code family.

## Scope
- Add V22 modules under `comparison_bench/` only.
- First reproduce/implement structured DE gate on the V17 structured channel.
- Only after DE passes, construct finite codes n>=512/1024.
- All blind/retry/public verification bits must be counted in f_total.

## Out of scope
- Modifying frozen `src/`, `experiments/`, `tools/`, `results/`.
- Fresh/promotion/qualification claims.
- Reopening short-block OSD/top-K tuning.

## Claim boundary
`diagnostic_only` until a Bob-only structured-code success is independently verified.
