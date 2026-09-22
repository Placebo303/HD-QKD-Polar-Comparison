# D9 GF32 DE-decoder calibration and threshold — heavy R1

## 1. Purpose and authority

- Repository: `D:\Code\HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`; do not switch.
- Track: implementation/readiness, followed by a separately authorized
  `EXPLORE_HEAVY` calibration batch.
- Accepted predecessor: `D8_DE_SWEEP_RESULT_ACCEPTED_ROUTE_TO_D9_CALIBRATION`.

Objective: determine whether D8's primary-only convergence window is a genuine
ensemble threshold signal, a Monte-Carlo stability artifact, or a mismatch
between V26 DE semantics and the finite row-layered v35 decoder; then freeze
one scientifically justified next experiment.

This packet authorizes audit, OpenSpec, minimal calibration code, tiny exact or
fake tests, bounded profile-only calls and one independent readiness review. It
does not authorize a scientific DE calibration sweep or finite-length decoder
batch.

## 2. Accepted D8 facts and interpretation ceiling

- 126/126 frozen DE calls completed and independently recomputed.
- Regular-DV3 converged 0/3 at f1.2 and 0/3 at f1.0.
- No candidate met the frozen both-condition advancement rule; D8 winner is
  none and remains none.
- Lambda2 0.45 and 0.50 converged 3/3 at primary f1.2; every candidate was 0/3
  at f1.0. These are descriptive inputs to D9 design, not promoted winners.

D9 may revise the role of f1.0 only prospectively with a mathematical
justification and a new preregistration. It must not reinterpret D8's terminal.

## 3. Four hypotheses to discriminate

- **C1 genuine threshold window**: V26 DE is semantically aligned and the
  degree-2 mixtures improve the f1.2 asymptotic trajectory, while f1.0 is at or
  beyond the tested ensemble threshold.
- **C2 DE/decoder semantic mismatch**: centering, coefficient action, variable
  update, posterior/belief metric, schedule or stopping semantics make D8 an
  unreliable screen for v35.
- **C3 Monte-Carlo instability**: 4000 samples ×3 seeds is insufficient near
  the transition and the 3/3 pattern is not stable.
- **C4 gate-role mismatch**: demanding f1.0 convergence as a hard prerequisite
  for an f1.2 finite-length candidate is scientifically unjustified; f1.0 may
  instead be a registered boundary/negative diagnostic.

## 4. Required audit and mathematical work

Read the D8 OpenSpec/readiness/log/review/root, V26 kernel, V35 row-layered
decoder, D7-A decoder certification and the current Model-F prior path.

Create OpenSpec change:

`openspec/changes/v72p2d9-gf32-de-decoder-calibration/`

Before behavior edits, freeze:

1. exact message-coordinate convention at channel, variable-to-check,
   check-to-variable and posterior stages;
2. coefficient permutation direction and syndrome/coset centering;
3. flooding DE iteration versus row-layered decoder sweep correspondence and
   the limit of any equivalence claim;
4. entropy/convergence observable versus finite decoder exact/syndrome stop;
5. deterministic finite-graph node-degree realization from edge-perspective
   lambda for n64/n128/n256, including socket balance, integrality, degree-2
   cycles/components and check-degree limits;
6. a bounded future calibration matrix containing only regular-DV3 and the
   smallest D8-informed neighborhood needed to test stability. Candidate 0.45
   and 0.50 must be included; any additional point requires a stated control
   role, not a broader search;
7. prospective f1.0 role (`HARD_GATE` or `BOUNDARY_DIAGNOSTIC`) with an
   information/rate argument independent of the observed D8 outcome;
8. exact advancement, ambiguity and stop rules; no post-result tuning.

If C2 cannot be resolved without changing the decoder or adopting a new
channel model, STOP with the exact mismatch. Do not tune the decoder inside D9.

## 5. Minimal implementation

Implement the shortest calibration harness that can:

- compare V26 and v35 primitive variable/check/belief updates on identical
  full-vector messages and coefficients;
- certify exact equality/tolerance on trees and clearly label loopy/schedule
  comparisons as non-equivalence diagnostics;
- reconstruct finite node/check degree counts for the frozen lambda candidates
  at n64/n128/n256 and fail clearly on unrealizable socket counts;
- run future MC stability replications without invoking the production decoder;
- write one fresh additive calibration root and support read-only verification.

Reuse D7-A/V26/V35 helpers where possible. Do not create a generic DE framework,
optimizer, graph library, checkpoint system, cache or new dependency.

## 6. Allowed files

- new D9 OpenSpec change from §4;
- one thin D9 calibration module and one runner under existing formal_ir/scripts
  locations;
- one focused D9 test file and directly affected existing tests only;
- `docs/research_cycles/V72P2D9-DE-DECODER-CALIBRATION/**` with one compact
  readiness record, one append-only exploration log and one independent review;
- `docs/decision-log.md` for one concise route entry;
- `AGENT_PROJECT_MEMORY.md` only at accepted memory triage;
- this packet/prompt pair.

Existing V26, v35, D7-A and D8 result files are read-only unless an exact
implementation defect creates a blocker; report that blocker rather than
patching outside scope. Preserve unrelated dirty files.

## 7. Work items

- **C01** — Verify and record the accepted D8 counts/claim ceiling from raw
  artifacts; no DE rerun.
- **C02** — Produce a stage-by-stage V26↔v35 semantic map with exact code
  pointers and identify match, approximation and mismatch boundaries.
- **C03** — Derive the prospective scientific role of f1.0 from rate/entropy
  margin and experiment purpose, not from whether D8 passed.
- **C04** — Derive edge-to-node degree realization and socket-balance rules;
  enumerate feasibility for baseline, 0.45 and 0.50 at all three widths.
- **C05** — Freeze the minimal stability/control matrix, seeds, population,
  iterations, budgets and decision rules for a future calibration run.
- **C06** — Create the complete OpenSpec change before behavior edits.
- **C07** — Implement primitive same-input certification, graph-realization
  audit, future calibration runner and verifier.
- **C08** — Test channel/centering, coefficient direction, variable/check/
  belief updates, tree equality, loopy claim ceiling, degree integrality,
  deterministic planning, failure retention and no production-decoder entry.
- **C09** — Run focused tests and bounded PROFILE_ONLY calibration calls; no
  D8 evidence reuse as a new result and no scientific calibration root.
- **C10** — Freeze one exact future command/root and strict call/wall/RSS
  budget; leave the root absent and all authorization false.
- **C11** — Obtain one independent reviewer-go review that separately judges
  semantic equivalence, f1.0 role, graph realizability and execution boundary.
- **C12** — Apply at most one scoped non-scientific correction and stop at
  `D9_DE_DECODER_CALIBRATION_READY_AWAITING_EXPLICIT_AUTHORIZATION`.

## 8. Required future-decision shape

The readiness packet must make the later result mechanically routeable:

- semantic certification fails → block DE-to-finite inference and diagnose
  the exact interface; no candidate promotion;
- semantics pass but MC stability fails → no finite candidate; revise only
  population/uncertainty design under a new preregistration;
- semantics and stability pass, graph realization valid → select at most one
  prospectively ranked ensemble for a later finite-length synthetic packet;
- degree realization invalid → redesign the ensemble representation before any
  decoder call;
- no outcome revives D7-H automatically.

## 9. STOP conditions

- D8 root/review does not support §2.
- f1.0 role is chosen from outcome convenience rather than a prior scientific
  argument.
- same-input semantics require modifying v35/V26 or changing the channel.
- the future matrix becomes an adaptive degree search.
- a production decoder, scientific DE calibration sweep, CAL/VAL/raw/real data,
  D7-H or finite-length execution is reached.
- independent review finds a blocking mathematical/semantic issue.

Return `BLOCKED` with raw evidence and the single decision needed.

## 10. Return contract

Return exactly `COMPLETE` or `BLOCKED`. `COMPLETE` reports C01–C12, the
semantic map and equivalence ceiling, f1.0 role and derivation, degree/socket
feasibility table, frozen future calibration matrix/command/root/budgets,
changed files, focused tests/profile, scientific DE and production-decoder calls
zero, independent verdict/findings, authorization flags false, no commit/no
push, and terminal
`D9_DE_DECODER_CALIBRATION_READY_AWAITING_EXPLICIT_AUTHORIZATION`.
