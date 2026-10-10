# V80 Prior-Cost Accounting — Proposal

- Charter: `docs/V80_BASELINE_20260921.md` §0.2-D1 (new OpenSpec change vs explicit waiver REQUIRED) + §§2/5/6-1/7-4/7-5 + `docs/PRIOR_COST_ACCOUNTING_DECISION_20260921.md` (Step-1 decision, [DEC]§§A–E) + `AGENTS.md` §3 (OpenSpec change required when behavior/architecture/workflow rules change).
- Packet: none (docs-only consolidation of already-decided accounting contract; no new experiment packet). Provenance: [REV]=`docs/PRIOR_COST_CLAIM_REVIEW_20260921.md`, [AUD]=`docs/PRIOR_COST_ACCOUNTING_AUDIT_20260921.md`, [SIB]=`docs/SIBLING_PRIOR_PARAMETERIZATION_AUDIT_20260921.md`, [A1R]=`docs/research_cycles/V80-NBLDPC-JAN21/P3_A1_REVIEW.md`, estimator verification `docs/A1_ESTIMATOR_AND_SLOPE_VERIFICATION_20260921.md`.
- Track: **— (no track gate: implementation-only/docs-only change, no execution)**. Per `AGENTS.md` §1.2 applicability matrix ("Implementation-only changes (no execution)" → no track gate). This change itself authorizes no execution, opens no `.ttbin`, consumes no budget, and makes no FER/SKR/route/qualification/publication claim. Any future census re-run or real-data use is DECIDE and needs its own prereg + authorization (see `tasks.md`).
- Data authority: no data touched. Number authority is `docs/V80_BASELINE_20260921.md` §§2–3 + [DEC] §§A–C; `docs/A1_ARITHMETIC_RECOMPUTE_20260921.md` was ABSENT at drafting time, so corrected `N_req` values below are baseline-§3 values marked **pending recompute**.

## Why (what changed)

- The independent review of the V80 baseline reset returned REVISE partly because the prior/calibration cost was decided in a document ([DEC]) that was not spec-level. The gap is CONFIRMED: `λ_total = leak_EC + 64` carries no prior term (no `+prior` term in `v80_o1_campaign.py:415-417`, `nonbinary_qspa.py:264-268`, `metrics/leakage.py:29-34`; [AUD] C1), and `docs/SECURITY_MODEL.md` has zero hits for prior terms (baseline §2).
- The consolidation introduced NEW decisions that go beyond documentation: the disclosure route (sacrifice-the-sample DEFAULT, [DEC]§B, baseline §§2/5-ii/7-4) and the corrected data roles / key-eligible block counts 200/276/364 (correcting [P3]:43, [DEC]§C, baseline §§2/5-iii/7-5). Per `AGENTS.md` §3 these behavior/workflow-rule changes REQUIRE an OpenSpec change (or explicit waiver); baseline §0.2-D1 flags exactly this.
- Meanwhile the four existing V80 OpenSpec changes (`v80-p1-rate-adaptive-rescue`, `v80-p2-finite-length-decomposition`, `v80-p3-real-hfull-census`, `v80-x1-cross-source-cliff`) carry SUPERSEDE banners on `proposal.md` ONLY while their `specs/*/spec.md` still contain effective SHALL requirements (baseline §0.2-D1). This change does NOT retire those SHALLs and does NOT touch those directories; it adds the missing accounting contract so future packets cite spec-level rules instead of a docs-only decision.

## Scope (frozen)

- The prior/calibration-cost accounting contract ONLY:
  1. Amortization model (read-only one-time factory calibration; withdrawn 0.12–0.26× sensitivity figure; binding 1.50× per-source forgone/key figure).
  2. Disclosure route (sacrifice-the-sample DEFAULT with SKR-numerator-only cost; disclose-the-statistic PERMITTED-BUT-NOT-DEFAULT with conditional charging model + amortization basis required first).
  3. Corrected data roles (TRAIN/VAL/HOLD) and key-eligible superframe counts 200/276/364 with corrected-count certifiability.
  4. Estimator auditability caveat (joint-MM on conditional plug-in; `K_B` persistence requirement; design points UNVERIFIED pending re-run).
  5. Claim ceiling (no composable-security / SKR / qualification / publication claim on this basis).
- Restatement only: every number traces to `docs/V80_BASELINE_20260921.md` §§2–3 or [DEC] §§A–C, or is marked `[TO BE MEASURED]` / `[BLOCKING]` / `pending recompute`. No new constant is introduced.

## Non-goals

- No change to any frozen scientific input (n, m, tag, H_full, gates, thresholds, seeds, channel, alignment, decoder parameters).
- No decoder work, no DE, no graph construction, no parameterization decision (§5-iv stays OPEN).
- No real-data execution, no `.ttbin` access, no workspace root, no budget consumed.
- No FER, SKR, operating-point, route, certifiability-overturn, qualification, or publication claim; the route decision belongs to the main thread.
- No edit to `docs/`, `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`, `src/`, `workspace/`, `results/`, `comparison_bench/outputs_comparison/`, or any of the four existing OpenSpec change directories.
- No commit, push, PR, or authorization granted by this change.

## Affected specs

- `specs/v80-prior-cost-accounting/spec.md` (delta: prior-cost disclosure in leakage/key accounting; sacrifice-the-sample exclusion + forgone-key reporting; key-eligible counts 200/276/364 with corrected-count certifiability; disclosure-cost charging model + amortization basis; f_super/f_eff invariance; estimator estimand + correction auditability; claim ceiling).
