# V80 NB-LDPC Jan-21 Restart — Proposal

- Charter: `docs/research_cycles/V80-NBLDPC-JAN21/PROGRAM_PLAN.md` (141 lines).
- S0 record: `docs/research_cycles/V80-NBLDPC-JAN21/S0_RESULT.md` (GO, all sources named).
- Q-prior: `docs/research_cycles/V80-NBLDPC-JAN21/LITERATURE_QPRIOR.md` (Mitra extraction).
- Freeze refs: `docs/decision-log.md:4435-4436` (S0 acceptance + q-prior).
- Track: program-level planning record. This change itself authorizes no execution
  and consumes no budget; S1 execution needs an explicit grant + Pre-EXECUTE,
  S3 needs a DECIDE prereg + Pre-RESULT.

## Why (what changed)

- Unsealing condition met (user-confirmed): per `V72P3G8-PRIOR-EFFICIENCY/DECISION_BRIEF.md`
  §10.4, Jan-21-class data is the primary data class and the goal is a truly
  feasible NB-LDPC.
- INFORMATION-CLOSURE applies to 20260123_* pools only; Jan-21-class
  (H_full ≈ 0.55–0.80 bits/symbol) is unconstrained.
- R3-efficiency premise: R3 already proves correctability on this class
  (8284/8412 exact, 0 mismatch) at f≈12.1 (2486 bits/frame); this program is a
  pure efficiency play — same correctability, leakage 2486 → ~267 bits/frame (~9×).
- Müller/V26 credibility: Müller et al. QIP 2024 Table 1 reproduced in-repo (V8);
  V26 MC-DE kernel verified against it; its rate 0.50–0.90 design points cover
  our 0.89–0.91 target zone.

## Scope (phases with gates)

- S0 DONE → S0→S1 GO (all three sources: 1M / 1p5M / 2M; G1 H_full ≤ 1.0,
  G2 design frozen, G3 ban carried).
- S1: DE ensemble optimization (EXPLORE, V26 kernel); gate f_ens ≤ 1.15/arm.
- S2: PEG construction + synthetic FER gate (EXPLORE); gate FER ≤ 5%, efficiency ≤ 1.3;
  three-shift-cyclic GF(32) mothers banned.
- S3: Jan-21 real-data development/confirmation (DECIDE, separate prereg after S2);
  acceptance f measured, FER, net/frame (≈+1200 bits/frame target) vs binary/R3.

## Non-goals

- No SKR/qualification/promotion claim in this change.
- No Jan-23-pool work (closure stands; V70R1 pools out-of-scope).
- No TERTIARY (a=3–4 refinements) work — deferred.

## Affected specs

- None yet. No behavior change is made by this change (planning record only),
  so there is no `specs/` subdir. Delta specs arrive at S2/S3 if construction
  or real-data behavior is frozen then.
