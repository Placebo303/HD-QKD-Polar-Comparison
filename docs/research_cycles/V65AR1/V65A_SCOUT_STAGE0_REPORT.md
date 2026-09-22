# V65A historical Type-II scout

- stage: `verify`
- overall: `V65A_NO_CANDIDATE_PASSED_VERIFICATION`
- fixed order: `['2026-01-13 162148', '2026-01-07 2500K', '2026-01-07 160254']`
- selected: `None`
- checked candidates: `['2026-01-13 162148', '2026-01-07 2500K', '2026-01-07 160254']`
- materialized frames: `0`

Stage 0 is a contract/provenance check only. A pass does not establish channel compatibility.
Stage 1 is a 256/64 coarse screen with淘汰权 only; it cannot produce READY.
Stage 2 is a plan-only 1024/256 re-characterization with 32 TEST identities; TEST statistics are not used.

Candidate provenance is provisional: all three are B pending a complete external-use ledger; any V36-V64 dependency would reclassify it to C.
