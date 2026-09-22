# Astra Project Deep Review R1 — Task Packet

## 0. Purpose and authority

This is a **read-only scientific reasoning packet** for a GPT-6 Astra chat.
It organizes the hardest open questions in `HD-QKD_Polar_Comparison` without
authorizing code edits, decoder/DE execution, real-data access, route closure,
or publication claims.

- Repository: `HD-QKD_Polar_Comparison`
- Project identity: formal-IR / NB-LDPC research mainline
- Lifecycle: documentation-only analysis; neither `EXPLORE` nor `DECIDE`
- Output wanted: mathematical and experimental-design advice, not patches
- Governing rules: `AGENTS.md`, especially §§0–3, 5, and 10
- Current evidence cutoff: 2026-09-16, through D19 readiness STOP

If an uploaded file conflicts with this packet, report the conflict and stop
that line of reasoning. Do not silently reconcile incompatible lifecycle
states.

## 1. Executive map of the project

The project asks whether high-dimensional QKD information reconciliation can
be made practically useful with source-aware nonbinary codes. The scientific
chain is:

```text
measured/calibrated channel
  -> source model and conditional entropy
  -> asymptotic ensemble feasibility (DE)
  -> finite graph + decoder behavior
  -> accepted-frame leakage and undetected-error accounting
  -> real-data net yield and, only later, secure-key qualification
```

The frozen binary Polar implementation is a comparison baseline. The active
algorithmic route is NB-LDPC; NB-Polar is isolated in a sibling checkout and is
not part of this review.

Current accepted route state, condensed:

1. D5/D6 showed that several tested rate-mother and graph/mother constructions
   do not provide usable evidence in their tested scopes. They did **not**
   disprove NB-LDPC.
2. D7 established decoder correctness in an easy regime and bounded
   cross-layer dependence. Directional transfer exists, but reverse-order
   joint recovery failed; posterior-only alternation risks double-counting.
3. D14–D17 repaired the channel/rate accounting and separated asymptotic DE
   behavior from finite-length behavior. A held-out finite test partially
   falsified the scaling model.
4. D18 found an L2 irregular ensemble family with a better DE threshold than
   DV3. Three nearby candidates tied at the available grid resolution; the
   selected `lambda_2=0.20, lambda_3=0.80` candidate won by a frozen
   deterministic tie-break, not by a demonstrated optimum.
5. D19 attempted a paired finite validation at `n=128` and conditional
   `n=256`. Readiness STOPped before scientific execution because one frozen
   n256 DV3 seed deterministically fails the accepted PEG constructor. The
   current seed set cannot be authorized as frozen.

## 2. Priority order

| ID | Question | Why it matters now | Desired Astra contribution |
|---|---|---|---|
| Q1 | D19 seed–constructor conflict | Immediate blocker | Decide the scientifically clean amendment, or justify accepting BLOCKED |
| Q2 | Asymptotic DE to finite-length inference | Core scientific uncertainty | Build a falsifiable bridge that does not overclaim from DE |
| Q3 | Finite graph ensemble representativeness | Determines whether D19 tests a code family or constructor luck | Define admissible sampling/conditioning and bias diagnostics |
| Q4 | Cross-layer extrinsic/cavity contract | Highest upside after a usable L2 regime | Derive a no-double-counting message contract and negative controls |
| Q5 | Synthetic-to-real decision bridge | Converts algorithm progress into project value | Specify the minimum DECIDE experiment and accounting table |

Work in this order. Q1–Q3 form one connected decision. Q4 remains paused until
finite L2 evidence is credible. Q5 is design-only and must not authorize real
data.

## 3. Hard questions

### Q1 — What is the scientifically clean response to D19's frozen-seed failure?

Observed facts:

- Candidate: L020, node counts at n256 `2^70 + 3^186`, check counts
  `3^54 + 4^134`.
- Control: DV3, variable counts `3^256`, check counts `4^172 + 5^16`.
- Frozen DV3 graph seed `2026094408` fails deterministically at
  `variable 255 socket 2`: no eligible check placement.
- Socket arithmetic is valid; five sibling seeds with the identical degree
  multiset admit.
- Accepted constructor is unchanged; 23/24 planned graph cells admit.
- The frozen packet forbids replacement/search, so the correct current state
  is `D19_L2_FINITE_ENGINEERING_BLOCKED`, with zero scientific calls.

Decision candidates for Astra to compare:

1. Replace only seed 4408 using a preregistered, non-adaptive next-seed rule,
   re-prove disjointness, re-profile all 24 graphs, and re-review.
2. Amend the design to sample a fixed number of **admitted** graphs from a
   preregistered seed stream, report admission probability, and condition the
   finite comparison explicitly on constructor admission.
3. Treat constructor failure as part of the code-ensemble outcome, preserve
   it as a failure rather than replacing it, and alter the statistical target.
4. Accept D19 as BLOCKED and redesign the constructor before testing decoder
   performance.

Astra must distinguish:

- harmless random-seed replacement;
- seed shopping that selects favorable graphs;
- conditioning on constructor success, which changes the estimand;
- a constructor robustness failure that is itself relevant engineering
  evidence.

Required Q1 output:

- one recommended option and one fallback;
- explicit estimand for each;
- bias introduced by admission conditioning;
- exact preregistration language;
- STOP conditions;
- why the choice preserves pairing between DV3 and L020.

Toy example for reasoning:

```text
Six preregistered seeds are paired across two arms.
Arm A admits all six; Arm B admits five and deterministically rejects seed 2.
Replacing seed 2 only in B breaks pairing.
Replacing seed 2 in both arms preserves pairing but conditions the sample on
an event discovered after freeze.
Keeping the rejected pair estimates a combined constructor+decoder pipeline,
not decoder performance conditional on an admitted graph.
```

Explain which estimand is scientifically most useful for this project and why.

### Q2 — How should DE predictions be connected to finite-length outcomes?

Known evidence:

- Current-channel L2 DV3 DE bracket: m94/m99 at n128-equivalent accounting,
  `delta_DE = 0.5468113653656221`.
- L020/nearby irregular candidates bracket at m89/m94,
  `delta_DE = 0.35149886536562214`.
- D18 therefore identifies a threshold improvement of `5/128` in disclosed
  symbols at this grid resolution.
- The three L2 irregular candidates 0.15/0.20/0.25 are indistinguishable on
  the observed DE grid; L020 is a deterministic representative, not a proven
  optimum.
- Earlier D17 scaling predictions were partially falsified by a held-out
  finite run, so a smooth finite-scaling law is not yet reliable.

Astra should propose the smallest model that can answer:

> Does L020 improve finite-length exact-recovery probability over DV3 at a
> matched channel and disclosure, and does that advantage persist from n128
> to n256?

Required Q2 output:

- primary paired estimand and uncertainty interval;
- minimum graph/block replication justified by the hierarchical variance
  sources (graph, block, decoder randomness if any);
- a decision rule that separates `positive`, `negative`, and `ambiguous`;
- what evidence would falsify the DE-to-finite hypothesis;
- what must remain descriptive rather than inferential;
- whether n256 should be conditional on a positive n128 result.

Avoid fitting a many-parameter waterfall model to a few points. A simpler
paired hierarchical/binomial analysis is preferred if it answers the decision.

### Q3 — What finite graph population are we actually testing?

The accepted PEG constructor may reject some degree-sequence/seed pairs.
Consequently, “draw a seed and construct a graph” defines at least two
populations:

1. all requested degree-sequence/seed pairs, including construction failure;
2. graphs conditional on successful construction;
3. a practical deployed pipeline with a bounded retry rule.

Astra should determine which population matches each project claim:

- ensemble potential;
- accepted-constructor decoder comparison;
- deployable algorithm reliability and runtime;
- end-to-end reconciliation yield.

Required Q3 output:

- a population/estimand table;
- an admission-rate measurement plan;
- diagnostics for topology bias after conditioning on admission;
- a fair pairing rule across DV3 and L020 when their admission mechanisms
  differ;
- a concrete rule for when constructor redesign is required rather than seed
  replacement.

Minimum topology diagnostics may include connectedness, rank, short cycles,
component sizes, check/variable degree realization, and any constructor-specific
failure position. Do not add generic graph metrics without explaining which
scientific error they can reveal.

### Q4 — What is a valid cross-layer extrinsic message contract?

Accepted D7 evidence shows that knowledge from the other layer can help, but
posterior reuse can count the same channel or syndrome evidence more than once.
The candidate contract is conceptually:

```text
L_code_ext(x) = L_post(x) - log p_in(x) + constant
```

where subtraction is in the log domain and the result must be normalized.
This identity alone is not sufficient: implementation schedules and factor
ownership determine whether evidence is truly extrinsic.

Required Q4 output:

- a factor-graph definition naming every factor and message owner;
- exact equations for one L1 -> L2 -> L1 round;
- normalization and zero-probability handling;
- an invariant showing which evidence appears exactly once;
- a tree-factor positive control;
- a loopy recurrence diagnostic;
- a posterior-double-counting negative control;
- STOP criteria before any multi-round D7-H experiment.

Example negative control:

```text
Use a tiny tree where the exact marginal is enumerable. Feed a decoder's full
posterior back as if it were extrinsic. The second-round belief becomes more
confident despite no new independent factor. A correct cavity message must
match the one-pass exact marginal and must not create this confidence gain.
```

No claim about FER, leakage, or implementable joint decoding may follow from
the algebra or toy test alone.

### Q5 — What is the minimum synthetic-to-real DECIDE experiment?

This is a design exercise only. The eventual project value comes from accepted
real frames after disclosure and verification costs, not from DE convergence
or syndrome satisfaction alone.

The minimum real-data result must keep separate:

- attempted frames;
- exact correct frames;
- protocol-accepted frames;
- accepted-wrong / undetected frames;
- syndrome, verification, control, and interaction disclosure;
- retained symbols;
- wall time and memory;
- per-source/session results;
- `beta_eff_empirical`, derived from leakage and entropy inputs;
- reconciled-net yield;
- secure-key quantities only when their independent security inputs exist.

Required Q5 output:

- one frozen operating point and why it is sufficient for a first DECIDE
  result;
- CAL/selection/confirmation split with no population leakage;
- exact accounting equations and denominator definitions;
- a compact per-frame and aggregate schema;
- go/no-go thresholds that cannot relabel undetected failures as success;
- what additional measurements are required before any SKR claim.

## 4. Upload manifest

### Minimal first chat (recommended)

Upload only:

1. this task packet;
2. `docs/research_cycles/V72P2D19-L2FINITE/READINESS_R1.md`;
3. `openspec/changes/v72p2d19-l2-finite-ensemble-validation/design.md`;
4. `docs/research_cycles/V72P2D18-L2ENSEMBLE/EXPLORATION_LOG.md`.

Ask Astra to answer Q1–Q3 only. This is the best use of one high-reasoning
conversation because those questions share the same evidence and decision.

### Second chat, only after Q1–Q3 adjudication

Upload this packet plus the D7-G extrinsic-contract proposal/design and the
accepted D7-E/D7-F result records. Ask for Q4 only.

### Third chat, later

Upload this packet, the accepted finite-L2 result, the real-data contract, and
the security-accounting specification. Ask for Q5 only.

Do **not** upload raw/private ttbin data, credentials, the whole dirty checkout,
or thousands of historical files. More context would reduce signal rather than
increase it.

## 5. Required return contract

Astra's response must use this structure:

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

For each recommendation, label statements as one of:

- `OBSERVED` — directly present in uploaded evidence;
- `DERIVED` — recomputed from observed values;
- `PROPOSED` — new design choice;
- `UNKNOWN` — requires missing evidence.

The final `STOP` section must confirm:

- no code or repository edits requested;
- no run or authorization inferred;
- no route/FER/leakage/SKR/publication claim made;
- exactly one next decision is named.

## 6. Acceptance criteria for the Astra review

- A1: distinguishes constructor admission, decoder success, and deployed
  pipeline reliability.
- A2: states the estimand before recommending seed replacement or conditioning.
- A3: preserves pairing or explicitly explains why pairing is abandoned.
- A4: treats the D18 winner as a representative tie-break selection, not an
  optimal ensemble.
- A5: provides a falsifiable finite-length design with uncertainty.
- A6: does not infer authorization or scientific claims from readiness docs.
- A7: identifies one next decision, not a sprawling roadmap.

Failure of A1–A6 means the answer is advisory only and must not be converted
into a task packet.
