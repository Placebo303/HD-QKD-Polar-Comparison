# V80-P2 Finite-Length Decomposition — Tasks

Planning-only change: no code/test edits in this task. T3–T5 need explicit grants before execution.

- [x] P2-T1 packet freeze — acceptance: `docs/research_cycles/V80-NBLDPC-JAN21/P2_PACKET.md` written (§§1–7: diagnostic hypothesis, DE point, curve partition + P1 precedence, assembly rule, budgets, forbidden list, explicit user gate), every number traces to a frozen source or is marked [TO BE MEASURED]/[TO BE COMPUTED].
- [x] P2-T2 operator prompt — acceptance: `docs/research_cycles/V80-NBLDPC-JAN21/P2_PROMPT.md` written, copy-paste ready, authorizes nothing.
- [ ] P2-T3 Pre-EXECUTE + grant (needs fresh explicit user grant per arm) — acceptance: Q0–Q6 recorded per arm (branch, scope cleanliness, frozen contract, output-absence + rg proofs, focused tests incl. dry joint-sampler check and dry-construct pins for new m points).
- [ ] P2-T4 gated execution (needs grant from T3) — acceptance: arm (i) f_DE per seed + agreement gate within DE budget; arm (ii) per-point FER/censor states within ≤3600 s, m = 200 never measured here, no forbidden action.
- [ ] P2-T5 batch-end review + assembly — acceptance: one independent review over the append-only EXPLORATION_LOG.md; assembly note computes m_min − m_DE / m_DE − 170.5 (or records non-reproducibility/unresolved with no inference); diagnostic ceiling held; nothing published beyond the batch.
