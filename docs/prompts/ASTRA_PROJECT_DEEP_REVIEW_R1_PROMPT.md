# Directly usable GPT-6 Astra prompt — Project Deep Review R1

I am uploading a task packet and three project evidence files from an
HD-QKD information-reconciliation research repository.

Your role is **principal scientific reviewer and experimental-design
adjudicator**. Use your strongest mathematical and causal reasoning. This is a
read-only review: do not write code, do not ask me to run an experiment, and do
not infer execution authorization.

Read the task packet first. Then inspect every uploaded evidence file and work
only on Q1–Q3:

1. adjudicate the D19 frozen-seed × accepted-constructor conflict;
2. design the smallest defensible DE-to-finite validation;
3. define the finite graph population and admission-conditioning contract.

Important constraints:

- The current D19 state is STOP with zero scientific calls.
- Seed `2026094408` fails deterministically for n256 DV3 under the accepted
  constructor; socket arithmetic is valid and 23/24 planned graph cells admit.
- Do not casually replace the seed. First state the estimand and the bias
  created by conditioning or replacement.
- Preserve paired comparison where scientifically justified.
- Treat the D18 L020 winner as a deterministic representative among a DE
  near-tie, not as a proven optimum.
- Distinguish construction failure, decoder failure, exact recovery, syndrome
  satisfaction, and undetected acceptance.
- Prefer the simplest design that can falsify the scientific hypothesis.
- Do not propose real-data, APP/D7-H, FER, leakage, SKR, qualification,
  promotion, or publication claims.
- If files conflict, quote the filenames and conflicting propositions, then
  stop that branch of analysis instead of guessing.

Use this exact response structure:

```text
EVIDENCE_READ
CONFLICTS_OR_MISSING_INPUTS
Q1_RECOMMENDATION
Q2_ANALYSIS_DESIGN
Q3_POPULATION_CONTRACT
REJECTED_ALTERNATIVES
CLAIM_CEILING
NEXT_PACKET_DELTA
STOP
```

Within Q1, compare at least these four options: deterministic paired seed
replacement; preregistered admitted-graph sampling; retaining construction
failure in the endpoint; accepting D19 as BLOCKED and redesigning the
constructor. Recommend exactly one and give one fallback.

Within Q2, give the primary paired estimand, uncertainty method, replication
unit, minimum replication logic, positive/negative/ambiguous rule, and explicit
falsifier. Do not hide graph-level dependence by treating block outcomes as
independent Bernoulli trials.

Within Q3, provide a table mapping claim -> target population -> denominator ->
handling of construction failures. Include a rule for when admission bias is
large enough to force constructor redesign.

Tag every substantive statement as `OBSERVED`, `DERIVED`, `PROPOSED`, or
`UNKNOWN`. Show short calculations where useful. End by naming exactly one
decision I must make next. Confirm that nothing in your answer is execution
authorization.
