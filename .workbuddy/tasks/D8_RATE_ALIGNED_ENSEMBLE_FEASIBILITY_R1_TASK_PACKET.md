# D8 rate-aligned GF32 ensemble feasibility — heavy R1

## 1. Accepted predecessor and purpose

- Repository: `D:\Code\HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`; do not switch.
- Track: `EXPLORE_HEAVY` readiness/implementation only.
- Accepted predecessor lifecycle: `D6_R1D_EXPLORE_RESULT_ACCEPTED_GRAPH_REDIRECT_CLOSED`.
- Accepted predecessor evidence: under frozen B0/B1/T1 DV3 synthetic conditions, L1 exact/syndrome 0/40, L2-APP 5/40, L2-oracle 35/40, end-to-end APP exact 0/120, and PEG-DV3 silent at n64/n128/n256.

Objective: establish the smallest scientifically defensible rate-aligned GF32 density-evolution/ensemble-design contract that can select a new degree-distribution candidate before another finite-length decoder batch.

This packet does not authorize the DE candidate sweep or a production decoder run. It authorizes audit, OpenSpec, minimal implementation, tiny/fake checks, bounded performance profiling and one independent readiness review.

## 2. Scientific ruling

The D6 result closes only the eligible-only DV3 topology substitution. The next variable must be ensemble/degree distribution, not another DV3 topology, more BP iterations, schedule replacement or cross-layer alternation.

Why D7-H remains excluded:

- X4: both base layers had zero syndrome-valid recovery over 600 n256 blocks.
- X3: 360 iterations rescued 1/156 and flooding-90 rescued 0/156.
- D6: PEG-DV3 changed graph topology but left L1 at 0/40 across n64/n128/n256.

D7-H therefore changes message circulation while retaining an unresolved base-code bottleneck. It may be reconsidered only after a new ensemble shows reproducible marginal L1 syndrome-valid recovery.

## 3. Required sources and reuse-first rule

Read before editing:

- `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`, and `docs/research-cycle-sop.md`;
- D6 R1d readiness, exploration log, batch-end review and cycle state;
- D5 Model-F input acceptance and X4 G2 artifacts;
- historical GF32/nonbinary DE implementations and accepted evidence, especially V11/V17/V19/V25/V27/V32 references discovered by `rg`;
- current nonbinary decoder/graph constructors needed only to define compatible degree conventions.

Reuse the nearest accepted DE/channel representation. Do not build a second DE framework if an existing one can be adapted with a small, explicit delta. Historical thresholds/results from another channel/domain may be used only as implementation validation, never copied as current evidence.

## 4. Questions the readiness package must answer

1. Which existing DE implementation is nearest to GF32, polynomial 37, the current probability-domain/check-update convention and current Model-F priors?
2. Does it represent the channel needed for L1 marginal decoding without silently reducing the accepted 32-ary distribution to a scalar surrogate?
3. What is the exact rate/check-row mapping between edge/node degree distributions and the D5 disclosure points at n64/n256?
4. What minimal candidate family changes degree distribution while keeping Model-F, GF32 arithmetic, disclosed rows and decoder semantics fixed?
5. What DE observable and threshold would justify a finite-length candidate, and what result would close the candidate family without claiming an information-theoretic impossibility?
6. Can the selected DE reproduce at least one known accepted historical limit or tiny exact/tree case before current-domain use?

If the current Model-F channel cannot be represented faithfully without a new mathematical assumption, return `BLOCKED_CHANNEL_REPRESENTATION_DECISION` with the exact missing contract. Do not substitute BSC/AWGN/q-SC heuristics silently.

## 5. Required implementation scope

Create OpenSpec change:

`openspec/changes/v72p2d8-rate-aligned-gf32-ensemble-feasibility/`

The change must freeze:

- the reused DE engine and exact delta;
- GF32/channel message representation and normalization;
- L1-first bottleneck scope; L2 may be a read-only comparator, not a joint optimization target;
- rate equation and mapping to current row budgets;
- a deterministic, bounded candidate enumeration rule and explicit maximum candidate count;
- baseline regular-DV3 inclusion;
- candidate degree support and coefficient/graph compatibility constraints;
- iteration/population/seed/budget limits for the future DE sweep;
- advancement rule to exactly one finite-length ensemble candidate, with deterministic tie-breaking;
- failure/unknown states and claim ceiling;
- one fresh future result root and exact command, left absent.

Implement only what is necessary to make that frozen sweep executable and verifiable. Prefer a thin adapter around accepted DE code plus one runner and one focused test file. No generalized optimizer, workflow engine, cache, checkpoint system, integrity manifest or new dependency.

## 6. Allowed files

- new OpenSpec change in §5;
- the nearest existing DE module, only if a small compatibility delta is required;
- one new thin D8 adapter/module if necessary;
- one D8 runner under `scripts/`;
- focused D8 tests plus directly affected existing DE tests;
- `docs/research_cycles/V72P2D8-RATE-ALIGNED-ENSEMBLE/**` using one compact readiness record, one future append-only exploration log and one independent review;
- `docs/decision-log.md` for one concise entry;
- `AGENT_PROJECT_MEMORY.md` only at accepted memory triage;
- this packet/prompt pair.

STOP before editing outside this list. Preserve frozen baseline directories, Model-F/D5/D6/D7 roots and unrelated dirty files.

## 7. Work items

- **E01** — Re-read and record the accepted D6 claim ceiling and route close without rerunning D6.
- **E02** — Inventory historical DE implementations/evidence; rank reuse candidates by mathematical compatibility, not age or convenience.
- **E03** — Trace current Model-F L1 marginal channel representation into the selected DE input and identify every transformation.
- **E04** — Derive the rate/degree/check-row equations and validate them on regular-DV3 plus at least one tiny hand-checkable ensemble.
- **E05** — Freeze a bounded deterministic candidate enumeration/selection rule; no adaptive post-result tuning.
- **E06** — Create the complete OpenSpec change before behavior edits.
- **E07** — Implement the minimum adapter/runner/verifier required for the frozen future sweep.
- **E08** — Add tiny exact/normalization/rate tests, baseline reproduction, deterministic enumeration, invalid-distribution refusal, fresh-root/no-overwrite and fake-runner isolation.
- **E09** — Run T0/T1 focused tests and a bounded no-production-decoder performance smoke. Historical accepted reviewer results may be trusted; do not broadly rerun unrelated suites.
- **E10** — Freeze the exact future command, fresh root, maximum candidates, random seeds, DE iterations/population, wall/RSS budget and stop rules.
- **E11** — Obtain one independent reviewer-go implementation + readiness review with `EVIDENCE_ACCESS` and explicit mathematical/claim-boundary findings.
- **E12** — Apply at most one scoped non-scientific correction, re-review only the affected scope, and stop at `D8_RATE_ALIGNED_ENSEMBLE_READY_AWAITING_EXPLICIT_AUTHORIZATION`.

## 8. Claim and route boundaries

Readiness may establish only that the proposed DE experiment is mathematically specified, implementation-tested, rate-aligned and executable. It establishes no decoder improvement or ensemble superiority.

The future DE sweep may advance one candidate only if it meets the frozen convergence/margin rule across the registered L1 conditions. Advancement would authorize neither finite-length execution nor D7-H; it would generate the next finite-length task packet.

A silent bounded search closes only its frozen candidate support/grid. It must route to either a broader degree/ensemble proposal or an explicit channel/decoder mismatch analysis, not “NB-LDPC impossible.”

## 9. STOP conditions

- D6 acceptance marker or reviewed root is inconsistent.
- No historical DE engine can represent the current channel without an unresolved new assumption.
- Rate mapping cannot be reconciled with D5/X4 row budgets.
- The proposal varies channel/prior, ensemble and decoder simultaneously.
- Candidate generation becomes adaptive to observed sweep outcomes.
- Production decoder, CAL/VAL/raw/real data, D7-H or a DE scientific sweep is reached.
- Independent review has a blocking mathematical or evidence finding.

Return the raw conflict and one main-thread decision. Do not silently choose a surrogate model.

## 10. Return contract

Return exactly `COMPLETE` or `BLOCKED`.

`COMPLETE` reports E01–E12, selected historical reuse path and rejected alternatives, channel/rate equations, frozen candidate rule and cap, changed files, tests/profile, production decoder/DE scientific-call count zero, exact future root/command/budget, independent verdict/findings, authorization flags false, no commit/no push, and terminal `D8_RATE_ALIGNED_ENSEMBLE_READY_AWAITING_EXPLICIT_AUTHORIZATION`.
