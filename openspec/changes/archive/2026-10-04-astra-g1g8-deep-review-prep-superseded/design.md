# Design — Astra G1–G8 Deep-Review Prep (docs-only)

Operator transcription of planner P-design. No behavior change, no specs delta.

## D2.1 Estimand before design

- Every Q1 option must name its estimand first (packet acceptance A2):
  decoder performance conditional on admitted graphs vs. combined
  constructor+decoder pipeline yield vs. deployed reliability with bounded
  retry. Conditioning on admission changes the estimand; replacement redefines
  the population.

## D2.2 Pairing toy (from packet §3 Q1)

- Six preregistered seeds paired across two arms; arm A admits six, arm B
  admits five (seed 2 deterministically rejected).
- Drop/replace-g* in one arm only: destroys pairing, estimand becomes
  E[FER | admissible] on non-identical graph sets.
- Replace in both arms: preserves pairing mechanically but conditions the
  sample on a post-freeze event.
- Only paired identical graph lists with the inadmissible cell retained as a
  pipeline failure preserve the comparison; pipeline yield = admission ×
  decode, inadmissible scored as zero-yield (never silently dropped).

## D2.3 D18-winner tie-break role

- L020 is a deterministic representative of three DE-indistinguishable
  candidates at grid resolution (packet §3 Q2; READINESS §1). All downstream
  inference is conditional on that representative status; no optimality claim
  may enter the amendment.

## D2.4 Why Q1–Q3-first chat must precede any seed set

- Q1 (amendment form), Q2 (DE→finite bridge), Q3 (population contract) share
  one evidence base and jointly determine the frozen seed list, admission rule,
  and statistic. Freezing a new seed set before Astra's Q1–Q3 return risks
  baking in the wrong estimand. Hence: manual Astra first-chat (Q1–Q3 only)
  → verbatim return → independent A1–A7 check → only then open a v72p2d19
  amendment change with a new packet.

## D2.5 Exact 4-file upload manifest (first chat, Q1–Q3 only)

1. `docs/astra/ASTRA_PROJECT_DEEP_REVIEW_R1_TASK_PACKET.md`
2. `docs/research_cycles/V72P2D19-L2FINITE/READINESS_R1.md`
3. `openspec/changes/v72p2d19-l2-finite-ensemble-validation/design.md`
4. `docs/research_cycles/V72P2D18-L2ENSEMBLE/EXPLORATION_LOG.md`

No raw/private data, no whole-checkout dump. Q4 and Q5 chats come only after
Q1–Q3 adjudication, with their own inputs (packet §4).

## D2.6 Astra return contract + labels + A1–A7

- Required sections: `EVIDENCE_READ / CONFLICTS_OR_MISSING_INPUTS /
  Q1_RECOMMENDATION / Q2_ANALYSIS_DESIGN / Q3_POPULATION_CONTRACT /
  REJECTED_ALTERNATIVES / CLAIM_CEILING / NEXT_PACKET_DELTA / STOP`
  (packet §5).
- Statement labels: `OBSERVED / DERIVED / PROPOSED / UNKNOWN` (packet §5).
- Final `STOP` must confirm: no code edits requested; no run/authorization
  inferred; no route/FER/leakage/SKR/publication claim; exactly one next
  decision named.
- Acceptance A1–A7 (packet §6): admission/decoder/pipeline separation; estimand
  first; pairing preserved or abandonment justified; D18 winner as
  representative; falsifiable finite design with uncertainty; no inferred
  authorization/claims; one next decision. A1–A6 failure → advisory only, must
  not become a task packet.

## D2.7 Q1-Option-3 preregistration skeleton (recommended default)

- Population: TBD after Q1 adjudication; frozen 4408 retained as inadmissible,
  never silently replaced.
- Constructor: frozen D10-R2, no per-graph exception, no redesign inside the
  validation.
- Graph list: identical paired lists across DV3/L020 arms, including the
  D18-winner arm; shared block seeds per width as frozen.
- Statistic: pipeline yield = admission × decode; inadmissible cells scored as
  zero-yield failures; conditional-on-admitted decoder rate reported secondary
  only with explicit conditioning label.
- STOP conditions: constructor exception outside the preregistered rule;
  budget overrun; any seed change; real-data touch; any claim-bearing readout
  beyond the preregistered confidence interval.
