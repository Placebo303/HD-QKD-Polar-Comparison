# Nonbinary LDPC V1-V7 Audit and V8 Plan

Date: 2026-08-04

## Current conclusion

The project has not shown that nonbinary LDPC is intrinsically unusable. It has
shown that the implemented V1-V7 candidates did not satisfy the project's
frozen promotion/readiness gates. V5 came closest at 255/256 aggregate frames,
but its final syndrome disclosure was 8.75 bits per input symbol, so that result
is not yet a practically efficient reconciliation design.

V7 engineering did not fail: its T0-T3 suites passed. Its four scientific
canaries failed their pre-registered gates.

| Route | Frozen observed result | Valid conclusion |
|---|---:|---|
| V7 R1A | p=.20 0/4; p=.30 0/4 | Implemented short (2,3) mother candidate failed canary |
| V7 R1B | p=.20 3/4; p=.30 0/4 | Extra-observation diagnostic failed; not formal single-observation IR evidence |
| V7 R2 | p=.20 0/4; p=.30 0/4 | Implemented scalar-DE surrogate failed; full-vector paper route remains untested |
| V7 R3 | p=.20 0/4; p=.30 0/4 | Implemented GF(32)xGF(32) EMS candidate failed at layer 0 |

## Why V8 changes direction

R1B creates a second independently corrupted observation from Alice and
combines it with Bob's real synthetic observation. The current reconciliation
contract provides Bob one paired-symbol observation plus public disclosure;
therefore R1B cannot support a formal IR success claim even where it decoded.

R2 compresses nonbinary messages into a scalar two-level ratio. The literature
construction instead evolves full q-ary messages, uses edge-perspective degree
distributions, samples actual node degrees, includes channel evidence in
variable updates, and judges convergence using message entropy. Consequently,
R2's 0/8 does not close the literature route.

## Ranked next routes

1. **V8: reference reproduction and math audit — execute now.** Establish an
   independent probability-domain oracle, error-domain syndrome equivalence,
   and full-vector q-ary MC-DE; reproduce a published reference before project
   adaptation. No canary data.
2. **V9: paper-faithful GF(1024) syndrome reconciliation — conditional on V8.**
   Use a reproduced ensemble and blind puncturing/shortening or another
   explicitly justified rate-adaptation mechanism. Use fresh development and
   confirmation roots.
3. **Finite-length ensemble redesign — conditional alternative.** If the
   published ensemble cannot meet the project's disclosure/runtime contract,
   optimize a protograph/degree distribution with the validated V8 tool and
   then freeze it before new data.
4. **GF(32)xGF(32) revisit — low priority.** Only after a validated per-layer
   ensemble predicts that layer 0 is below threshold. Do not tune the frozen R3
   evidence.
5. **Multiplicative repetition — diagnostic/future only.** It is admissible
   only if repeated likelihoods arise from a proved public protocol or actual
   independent observations. Do not synthesize free side information.

Decoder list/ADMM/post-processing permutations are not prioritized: V5C/V5D
already indicate that changing the decoder around the same high-disclosure
construction does not address the central model/ensemble question.

## V8 pass condition

V8 passes only if all algebra/oracle/MC-DE gates pass and at least one exactly
sourced q-ary QSC reference is reproduced with a pre-frozen numerical tolerance.
If the source lacks exact degree vectors or conventions, V8 stops as a concrete
blocker rather than inventing parameters.

## Scientific boundary

V8 produces engineering evidence, not FER evidence. It must not create or run
canary, development, confirmation, real-data, N4, or formal comparison plans.
Successful V8 completion only authorizes drafting a separate V9 OpenSpec
change.

## Literature anchors

- Muller et al., *Non-binary LDPC codes for quantum key distribution*,
  https://arxiv.org/abs/2307.02225
- Kasai et al., *Non-binary LDPC codes with multiplicative repetition*,
  https://arxiv.org/abs/1004.5367
