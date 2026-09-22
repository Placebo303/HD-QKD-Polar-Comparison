# S2 Constructor Defect Review — 2026-09-20 evening (external read-only review)

Status: external read-only review — user/auditor; no code changes made by that review.
Scope: EXPLORE docs-only record; preserves V1/V2 raw failures; pauses causal attribution + S3.

## Finding 1 — PEG edge selection defect (`nonbinary_v10_peg.py:368`)
- Unreachable candidates ignored when any reachable candidate exists → may actively create short cycles.
- Violates stated "maximize local girth" objective.

## Finding 2 — V2 did not execute "best of 100 candidates" (`nonbinary_v10_peg.py:424`)
- `max_trials` = retry-on-failure; first success breaks; selection seed not varied per trial.
- Packet's "more PEG trials; constructor-kept minimum" mismatches implementation.
- 1158→1140 not attributable to more search (construct seed also changed) — confounded.

## Finding 3 — PLUMBING-SANE scope too broad
- `min_girth=0` has a concrete cause: BFS unreachable −1 then +1 (not a reporting quirk).
- `converged_no_syndrome` = hard-decision streak stability, NOT soft-message convergence (premature-stop not excluded).
- p=0.02 miscorrection shows wrong same-syndrome solutions but without differential
  codeword weight it is NOT "low-weight codeword evidence".

## Finding 4 — Channel/prior mismatch
- Proxy is GF(32) QSC symbol p=0.05 with H = h2(0.05)+0.05·log2(31) = 0.534107.
- Per-frame content = 256·H = 136.7 bits; L2 leak = 235 bits.
- Efficiency in the proxy's own terms ≈ 235/136.7 = 1.719 (not ≤1.3).
- `f_super=1.2246` is a TARGET-channel budget mapping, not a measured efficiency
  of the current proxy experiment; L1 not constructed.
- Consequence: V1/V2 failures mean "current construction+decoder fails on this QSC
  proxy experiment", NOT "S1→S2 gap ≈ dv=2".

## Verdict
- 构造实现与实验解释需要返工，不是 dv=2 路线已失败.

## Mandated order
1. Keep V1/V2 raw failures; pause causal attribution + S3.
2. Fix constructor (unreachable-priority; correct girth; trials semantics aligned with packet).
3. Deterministic tests + independent review, then re-freeze a new experiment.
4. New experiment keeps λ unchanged; channel and prior must explicitly match;
   only afterwards evaluate dv distribution and stopping rules separately.
