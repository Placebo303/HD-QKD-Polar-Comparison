# V80-P1 Rate-Adaptive Rescue — Tasks

Planning-only change: no code/test edits in this task. T3–T5 need explicit grants before execution.

- [x] P1-T1 packet freeze — acceptance: `docs/research_cycles/V80-NBLDPC-JAN21/P1_PACKET.md` written (§§1–8: nested-cold design, 2 arms, gates (a)/(b)/(c), budgets, forbidden list, explicit user gate), every number traces to a frozen source or is marked [TO BE MEASURED].
- [x] P1-T2 operator prompt — acceptance: `docs/research_cycles/V80-NBLDPC-JAN21/P1_PROMPT.md` written, copy-paste ready, authorizes nothing.
- [ ] P1-T3 Pre-EXECUTE + grant (needs fresh explicit user grant per arm) — acceptance: Q0–Q6 recorded (branch, scope cleanliness, frozen contract, output-absence + rg proofs, focused tests incl. dry submatrix-rank pins + 1-block dry decode per stage).
- [ ] P1-T4 gated execution (needs grant from T3) — acceptance: 2 arms within wall/per-call/RSS caps; Stage-1 k/240, rescue conversions, final F/240, r, E[leak], f_exp, f_eff, headroom recorded; no forbidden action; single-window, no resume.
- [ ] P1-T5 batch-end review — acceptance: one independent review over the append-only EXPLORATION_LOG.md (authorization boundary, machine gates, retained failures, preregistered repair if used, claim ceiling); verdict PASS/FAIL per frozen gates returned to main thread; no route/S3 decision made here.
