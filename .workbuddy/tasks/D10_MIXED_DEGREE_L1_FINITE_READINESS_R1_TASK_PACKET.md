# D10 mixed-degree L1 finite-length discriminator — heavy R1 readiness

## 1. Purpose and authority

- Repository: `D:\Code\HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`; do not switch.
- Track: implementation/readiness; future decoder batch is `EXPLORE_HEAVY` and
  requires separate explicit authorization.
- Accepted predecessor:
  `D9_DE_CALIBRATION_RESULT_ACCEPTED_SELECT_DV23_045`.
- Sole selected candidate: `lam_d2_0.45_d3_0.55`.

Objective: implement and freeze the smallest finite-length L1-only experiment
that tests whether the D9-selected mixed degree distribution restores
reproducible syndrome-valid/exact recovery relative to a matched regular-DV3
control at f1.2 and n64/n128/n256.

This packet authorizes OpenSpec, construction implementation, structural
qualification, fake/tiny decoder tests, profile-only graph builds and one
independent readiness review. It does not authorize the scientific decoder
batch.

## 2. Scientific isolation contract

Exactly two arms:

- `PEG_DV3_MATCHED`: regular variable degree 3 control;
- `PEG_DV23_LAM2_045`: D9-selected edge-perspective lambda2=0.45 candidate,
  realized deterministically by the accepted largest-remainder rule.

Both arms must use the same graph-construction algorithm, tie-breaking policy,
graph seed set, Model-F L1 prior, row count, block seed set, decoder, schedule,
iteration cap, damping, field and coefficient-distribution convention. The
candidate may differ only where mathematically forced by its degree/socket
profile.

Primary scope only:

- L1 marginal decoding;
- f1.2 row counts `(n,m) = (64,59), (128,118), (256,236)`;
- q=32, polynomial 37;
- cold row-layered v35 decoder, max_iter=90, damping=1.0;
- exact and syndrome-valid reported separately, with provenance and residual
  syndrome weight.

No L2, APP transfer, oracle-L2, f1.0, square point, alternation or D7-H.

## 3. Graph and coefficient requirements

Create deterministic simple Tanner graphs with the exact node/check degree
counts frozen by D9. Reuse an accepted PEG/configuration builder if it can
honor arbitrary degree sequences; otherwise implement one minimal deterministic
degree-sequence PEG builder.

Required structural checks before any future decoder binding:

- exact variable/check degree histograms and socket balance;
- no duplicate edge and no empty check;
- rank measured and reported, never silently repaired after seeing decoder
  results;
- connected-component and degree-2 subgraph diagnostics;
- four-cycle count/girth or the nearest existing accepted metric;
- construction failures retained and excluded before decoder dispatch;
- at least three predeclared graph seeds per width to avoid single-graph
  conclusions.

Finite coefficients use a deterministic seeded stream of independent uniform
nonzero GF32 values, matching the V26 ensemble distribution but not claiming
edgewise identity with DE. Freeze the seed derivation before execution. Because
the two arms have different edge counts, require the same distribution and
seed rule, not impossible edge-for-edge equality.

## 4. Future experiment design to freeze

The readiness work must preregister:

- exactly three graph seeds per width, fixed before execution;
- exactly eight block seeds per width, separated from graph seeds;
- paired control/candidate decoding on identical sampled L1 blocks;
- conditional width progression starting at n64, with explicit positive,
  negative, ambiguous and engineering-blocked rules;
- maximum planned decoder calls and setup calls;
- wall/per-call/RSS limits and no retry/resume/seed search;
- one fresh output root and exact command;
- one result log and one independent batch-end review.

Use the smallest call matrix that still tests reproducibility across both graph
and block variation. A natural full ceiling is `2 arms × 3 widths × 3 graphs ×
8 blocks = 144` scientific L1 calls; conditional stopping may reduce it but
must be frozen before execution. Do not add L2 calls to consume unused budget.

Advance at most the mixed candidate, and only on a predeclared reproducible
syndrome-valid/exact signal across graph seeds. Do not use a single rescued
block or pooled-only count as sufficient evidence. Freeze exact thresholds in
OpenSpec and justify them against the 3×8 paired design; do not invent them
after observing results.

## 5. OpenSpec and allowed files

Create before behavior edits:

`openspec/changes/v72p2d10-mixed-degree-l1-finite-discriminator/`

Allowed files:

- the new D10 OpenSpec change;
- one minimal mixed-degree graph constructor or thin adapter in `formal_ir`;
- one D10 runner under `scripts/`;
- one focused D10 test file and directly affected graph-constructor tests;
- `docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/**` with one readiness record,
  one append-only exploration log and one independent review;
- `docs/decision-log.md` for one concise route entry;
- `AGENT_PROJECT_MEMORY.md` only at accepted memory triage;
- this packet/prompt pair.

Existing D5–D9 code/results, V26, v35, baseline `src/`, `experiments/`, `tools/`
and unrelated dirty files are read-only. STOP before expanding scope.

## 6. Work items

- **F01** — Verify D9 accepted terminal, unique selected candidate, stability
  counts and claim ceiling from existing artifacts; no DE rerun.
- **F02** — Inventory existing degree-sequence/PEG builders and select the
  smallest compatible reuse path; reject builders unable to preserve the
  two-arm isolation contract.
- **F03** — Freeze exact degree counts, graph seeds, coefficient seed rule,
  block seeds, call order and structural gates.
- **F04** — Freeze paired multi-graph success/negative/ambiguous thresholds and
  conditional width progression with claim ceiling.
- **F05** — Create complete OpenSpec before behavior edits.
- **F06** — Implement the two-arm graph construction, structural records,
  coefficient generation, L1-only runner and read-only verifier.
- **F07** — Guarantee invalid structure fails before decoder binding and tests
  cannot reach the production decoder without explicit injected runner.
- **F08** — Add tiny exact-degree/socket tests, determinism, seed separation,
  multi-graph variation, coefficient distribution/range, rank/4-cycle metrics,
  paired call matrix, transition rules, exact/syndrome separation,
  provenance/residual fields, no-overwrite and fake-runner isolation.
- **F09** — Run focused T0/T1 tests and bounded PROFILE_ONLY graph construction
  at all widths; no scientific decoder call or future root.
- **F10** — Freeze exact future command/root/budgets; verify root absent and all
  authorization false.
- **F11** — Obtain one independent reviewer-go review of graph mathematics,
  isolation, decoder-entry boundary, thresholds and frozen command.
- **F12** — Apply at most one scoped non-scientific correction and stop at
  `D10_MIXED_DEGREE_L1_READY_AWAITING_EXPLICIT_AUTHORIZATION`.

## 7. Required routing after the future run

- reproducible candidate L1 recovery across graph seeds and widths → propose a
  separate L2/APP integration experiment; D7-H still does not auto-revive;
- n64-only recovery that collapses with width → retain as finite-size signal
  and diagnose scaling/degree realization;
- no material candidate advantage → close this `{2,3}` finite realization and
  return to a broader ensemble/protograph proposal, not more alternation;
- structural or implementation invalidity → engineering block, no algorithm
  conclusion.

## 8. STOP conditions

- D9 evidence does not uniquely select lambda2=0.45.
- Control and candidate cannot share one construction/tie-breaking family.
- Degree/socket counts or graph seeds are chosen adaptively.
- Any invalid graph can reach the decoder.
- The design changes Model-F, rows, decoder, schedule or channel with degree
  distribution.
- Production decoder, L2, D7-H, real data or scientific output root is reached.
- Independent review finds a blocking graph/math/isolation issue.

Return `BLOCKED` with raw evidence and one decision needed.

## 9. Return contract

Return exactly `COMPLETE` or `BLOCKED`. `COMPLETE` reports F01–F12, selected
builder/rejected alternatives, exact degree tables and seeds, paired matrix and
thresholds, changed files, structural/profile results, focused tests,
production decoder/scientific calls zero, exact future command/root/budgets,
independent verdict/findings, authorization false, no commit/no push, and
terminal `D10_MIXED_DEGREE_L1_READY_AWAITING_EXPLICIT_AUTHORIZATION`.
