# X1 Successor 15-Arm Batch — Main-Thread Acceptance (Acceptance ID G-X1S)

- Date (UTC): 2026-09-22. Track: **EXPLORE** (EXPLORE_HEAVY). Gate: **main-thread acceptance** (AGENTS.md §1.2 EXPLORE contract: batch-end independent review + main-thread acceptance).
- Acceptance delegation: the main thread delegated this acceptance to the orchestrator (conversation-grant mode, this cycle; the G-X1S grant and the paperwork deviation are recorded in the prereg amendment notes; administrative ratification follows this acceptance per the P3-A1-REVIEW F-3 precedent).
- Chain of record: `X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md` (grant) → `X1_SUCCESSOR_ENTRY_PREEXEC.md` (Q0–Q6) → bundle build + G-D verification (`workspace/x1_bundles_7c1d4a2b/`) → runner pre-execution review → batch execution (`X1_EXPLORATION_LOG.md` + 15 `workspace/x1_<uuid8>/` arm roots) → `X1_BATCH_END_REVIEW.md` (PASS_WITH_FINDINGS; F-b ruled within the measurement-terminal pattern) → this acceptance.

## Accepted scope (ONLY)

The 15-arm synthetic per-source FER cliff curves (fails/240 or fails-at-stop for CENSORED arms; own-corrected-H `f_super`/`f_eff`; `undetected` isolated; girths; walls) plus the materialized bundle inputs. NO operating point is selected; NO P1/P2 execution is authorized; NO FER/SKR/route/qualification/publication claim.

## Accepted results (summary; authoritative record = `X1_EXPLORATION_LOG.md` + `X1_BATCH_END_REVIEW.md`)

- 15/15 arms terminal: 6 COMPLETE (2M-204 2/240, 2M-208 0/240, 1.5M-203 2/240, 1.5M-207 1/240, 1M-197 3/240, 1M-201 0/240 with G-B EXPECTED-OUT), 9 CENSORED-bar12, 0 INCOMPLETE-wall, 0 budget-FAIL. `undetected` = 1 (X1-1M-193; isolated, counted b2f-verbatim inside fails, never merged). Wall 15915.7 s ≤ 27000 s; RSS ≤ 0.68 GiB; zero `.ttbin` reads; no repair path used.
- Route-gate (G-A, ≤ 12/240) `m_min` on the frozen grid: 2M **204** · 1.5M **203** · 1M **197**. Efficiency-gate (G-B, `f_super` ≤ 1.3 own `H_corr`) `m_min`: 2M 192 · 1.5M 191 · 1M 185 (only 1M-201 fails G-B: `f_super` 1.30286 > 1.3, zero-failure EXPECTED-OUT characterization).
- Certifiability arithmetic (G-C vs key-eligible 200/276/364): NO grid point is simultaneously route-passing and count-certifiable — `N_req` at the six G-A-passing points is 484 / 2298 / 546 / 5315 / 668 / inf, all exceeding eligibility. The corrected structural-uncertifiability finding (baseline §3, R1-corrected basis) stands, now with measured cliffs.
- Cross-batch consistency (never pooled): 2M-208 0/240 agrees with the frozen b2f F208 citation; 2M-204 2/240 vs F202 6/240 is a distinct-instance comparison, not a verification.

## Closed / not authorized

- CLOSED: per-source `m_min` measurement at grid resolution (between-grid positions remain unmapped); the X1 successor batch execution; the long-open "m_min never measured" item.
- NOT authorized by this acceptance: operating-point selection (a later DECIDE consuming these curves + P1 rescue results); P1/P2 execution; any FER/SKR/route/qualification/publication claim; a standing conversation-grant mode.
- Censored arms' stop-point FER/`f_eff` are never 240-basis numbers (R1 read rule, applied throughout).

**Verdict: G-X1S batch ACCEPTED (main thread), scope-limited as above.**
