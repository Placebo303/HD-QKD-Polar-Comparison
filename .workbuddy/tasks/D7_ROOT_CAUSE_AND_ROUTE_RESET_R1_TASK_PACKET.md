# D7 Root-Cause and Route-Reset Master Packet R1

## 1. Identity and authority

- Repository: `D:\Code\HD-QKD_Polar_Comparison`
- Intended branch: the branch active when this packet is accepted; record it, do not switch branches.
- Change name: `formal-ir-d7-root-cause-and-route-reset`
- Packet type: `PLAN + IMPLEMENT + REVIEW-READINESS + CONDITIONAL EXECUTE + RESULT-READINESS`
- Lifecycle at issue: D7-H is implemented but no D7-H scientific execution is authorized by this packet.
- This is the single master packet for the remediation. Later authorization may resume a named phase of this same packet; do not create successor micro-packets unless a requirement changes.

This packet authorizes scoped documentation, OpenSpec, implementation, and test-only work. It does **not** authorize a production decoder run, G1 rerun, multi-graph diagnostic, G2 run, D7-H run, real-data run, result solidification, push, or scientific promotion.

## 2. Objective

Remove the unresolved experimental-design and evidence problems that currently make further D7-H execution premature:

1. establish whether the historical G1 and current D7 transfer paths are mathematically equivalent when given the same graph, block, priors, and decoder outputs;
2. make provenance and per-layer outcomes observable instead of inferring them from joint counters;
3. measure graph-seed sensitivity with a small pre-registered multi-graph diagnostic;
4. restore G2 as the frozen n=256 length discriminator, or explicitly supersede it only through an accepted scientific decision;
5. add a bounded strong-reference/feasibility diagnostic without calling it an information-theoretic proof;
6. supersede over-strong single-graph terminal wording without altering historical artifacts;
7. implement the existing lightweight exploratory workflow instead of adding another ceremony framework.

## 3. Claim ceiling

Allowed claims after implementation/tests only:

- implementation candidate;
- same-input transfer-path equivalence or a concrete localized mismatch;
- runner/test readiness;
- frozen exploratory and G2 commands awaiting authorization.

Forbidden without separately authorized execution and independent result review:

- G1 is valid or invalid scientific evidence;
- a particular graph, four-cycle, decoder, transfer direction, block length, or information margin causes failure;
- D7-F proves reverse-order regression;
- G2 passes/fails;
- FER, leakage, efficiency, SKR, qualification, route death, or promotion.

## 4. Authoritative corrections to carry forward

- Do not encode the unsupported hypothesis that historical G1 used `None` beliefs or silently fell back to a uniform L2 prior. The old wrapper converted `result.final_beliefs` to an array, and the old row-layered decoder updated beliefs during its 90 iterations.
- In current code, provenance is checked before the `bel1 is None` branch; missing provenance fails closed rather than silently using a uniform transfer.
- G1 and D7 used different block seeds and do not expose identical metrics. Their numerical difference is an unresolved consistency question, not a logical contradiction.
- D7-C/D/E/F used one graph pair. Their terminal labels are pre-registered classifications for that graph, not general mechanism facts.
- For D7-F f=1.2 the paired table is candidate-only 2, reference-only 0, both 0, neither 14. Record the exact paired test and its weak evidential status; do not treat the terminal name as statistical confirmation.
> Correction note (2026-09-13, main-thread authorized): this line is inverted; the immutable D7-F `stratum_summary.csv` stores `candidate_only=0, reference_only=2`, and the terminal `D7_F_REVERSE_ORDER_REGRESSION` requires `reference_only >= 2 and candidate_only == 0`. The rest of this packet is unaffected.
- G2 remains the accepted-plan n=256 length discriminator until an explicit accepted plan supersedes it. P0's 485-second projection is not a reliable G2 runtime estimate.

## 5. Allowed files

The operator may create or modify only:

- `openspec/changes/formal-ir-d7-root-cause-and-route-reset/**`
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
- one new narrowly named D7 consistency/multi-graph module under `comparison_bench/src/comparison_bench/formal_ir/`
- one new narrowly named CLI script under `scripts/`
- focused `comparison_bench/tests/test_v72p2d5_*.py` and `test_v72p2d7_*.py`
- `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/**`
- a narrow corrigendum or decision entry in `docs/decision-log.md`
- `docs/research-cycle-sop.md` only if a concrete ambiguity prevents the already-written lightweight exploratory rule from being used; prefer no SOP edit
- `AGENT_PROJECT_MEMORY.md` only during final memory triage, for accepted durable facts
- this packet's operator-return section, if the workflow requires an in-place return record

Before modifying a listed existing file, read it. If another file is required, STOP with the exact path and reason.

## 6. Forbidden scope

- No edits to frozen `src/`, `experiments/`, historical `tools/`, existing result roots, or sibling repositories.
- Do not modify historical G1/D7 manifests, summaries, tables, reports, or authorization records.
- Do not delete, rename, clean, stash, reset, normalize, or commit unrelated dirty-worktree content.
- No new framework, plugin, dependency, database, checksum system, retry layer, or generic experiment engine.
- No raw-data/VAL/CAL decoding; Model-F artifacts are read-only inputs.
- No D7-H execution.
- No push or force operation.

## 7. Frozen work plan and acceptance IDs

### Phase A — OpenSpec and evidence correction

Create the minimal OpenSpec proposal/design/tasks/delta spec before behavioral code edits.

- **A01**: Record the seven objectives and claim ceiling in Section 2–3.
- **A02**: Record that historical evidence is retained byte-identical; corrections are additive/superseding.
- **A03**: Add a cycle state whose initial terminal is `IMPLEMENTATION_IN_PROGRESS / EXECUTION_NOT_AUTHORIZED`.
- **A04**: Add a D7-F corrigendum: `D7_F_REVERSE_ORDER_REGRESSION` remains a historical machine label but is not an immutable general mechanism fact. The accepted interpretation is single-graph, n=16 paired evidence with exact discordant counts and exact-test p-value.
- **A05**: Record G2 as pending, not failed, skipped, or superseded.

### Phase B — same-input G1/D7 equivalence and observability

- **B01**: Factor or expose the smallest shared helper necessary so G1 and D7 form `q_L1` and `P(U2|B)` through one canonical implementation. Do not rewrite the decoder.
- **B02**: Add a deterministic test fixture using the same in-memory graph, block, priors, and injected decoder results. Assert equality of L1 input prior, L1 posterior-to-probability conversion, L2 transfer prior, target syndrome, decoded target, and per-layer counters between legacy-G1-compatible and D7 paths.
- **B03**: Cover exact `CHECK_UPDATED`, missing/`None`, `PRIOR_ONLY`, unknown, and a valid zero-iteration prior-only return. Non-`CHECK_UPDATED` cross-layer consumption must fail closed.
- **B04**: If same-input equality fails, localize the first unequal tensor/value and STOP. Do not compensate or tune.
- **B05**: Extend future G1 evidence schema additively with per-layer exact, syndrome-valid, iterations, provenance, and transfer-invoked/blocked counts. Preserve existing keys and filenames.
- **B06**: Add a no-write probe mode or pure callable that resolves the real historical decoder and reports whether its result carries accepted provenance, without starting a phase run or creating an output root.

### Phase C — frozen multi-graph exploratory design

Implement one small runner reusing existing builders and decoder bindings.

- **C01 graph pairs**: baseline `(2026090501,2026090502)` plus `(2026091401,2026091402)` and `(2026091501,2026091502)`. No graph search or replacement after observation.
- **C02 blocks**: `2026091300..2026091315` for every graph pair.
- **C03 operating points**: n=64; f=1.2 primary with rows L1=59/L2=52; f=1.0 negative-margin sanity with rows 49/43.
- **C04 arms**: marginal L1, L1-to-L2 transfer, marginal L2, L2-to-L1 transfer, and forward/reverse joint outcomes. Use the existing Model-F input and `max_iter=90`, `damping_alpha=1.0`.
- **C05 output**: one fresh user-specified `workspace/` root; manifest, per-call records, per-block paired table, per-graph summary, across-graph summary, report, command log. Never overwrite.
- **C06 statistics**: report raw paired discordant counts by graph; exact two-sided McNemar/binomial p-values and confidence intervals as descriptive diagnostics. No pass/fail based only on p-values and no pooled claim that hides graph heterogeneity.
- **C07 terminal vocabulary**: only `GRAPH_SENSITIVITY_OBSERVED`, `NO_GRAPH_SENSITIVITY_OBSERVED_IN_BOUNDED_SAMPLE`, `INCONCLUSIVE`, or an engineering/resource blocker. All carry `EXPLORATORY_SYNTHETIC_SINGLE_IMPLEMENTATION`.

### Phase D — bounded feasibility/strong-reference design

- **D01**: Do not promise exhaustive ML decoding for n=64 GF32.
- **D02**: Implement the smallest available reference ladder: current decoder at 90 iterations; same decoder at a frozen higher ceiling of 360; and one existing materially different decoder/schedule only if it already exists and accepts the same syndrome/prior contract. Do not create a new decoder family for this packet.
- **D03**: For each arm record exact, syndrome-valid, posterior score of truth and returned candidate under the input prior/check factors where computable, residual syndrome weight, and whether the higher/reference arm changes the outcome.
- **D04**: Include tiny exact-enumeration tests demonstrating score/ranking correctness. Label n=64 results `STRONG_REFERENCE_DIAGNOSTIC`, never ML proof or information-theoretic feasibility.
- **D05**: Apply the reference ladder only to the frozen multi-graph blocks that fail at f=1.2; no adaptive seed replacement.

### Phase E — restore G2 readiness

- **E01**: Reconcile the current G2 implementation with the accepted D5 plan: n=256, f=`[1.0,1.1,1.2]`, rows L1=`[196,215,235]`, rows L2=`[172,189,206]`, block seeds `2026091000..2026091199`, graph seeds L1=`2026090501`, L2=`2026090502`, APP 200 and oracle 40 per f, existing resource ceilings.
- **E02**: Preserve the later four-state interpretation from accepted project memory/specification; do not revive an obsolete unconditional `ROUTE_DEAD` claim if current accepted OpenSpec superseded it.
- **E03**: Add injected/fake-runner tests for exact matrix, budget accounting, additive output, per-layer metrics, and no accidental decoder call.
- **E04**: Produce an evidence-based runtime estimate only from measured/scaled probes explicitly authorized later. Until then state `G2_RUNTIME_UNVERIFIED`.

### Phase F — tests and review readiness

- **F01 T0**: focused import/compile and tiny mathematical tests.
- **F02 T1**: all focused provenance, equivalence, schema, multi-graph aggregation, exact-statistic, reference-ladder, no-overwrite, and G2 fake-runner tests.
- **F03**: Test-only calls must inject fake decoders and fresh `workspace/<task>/<uuid>` roots. Production decoder call count must remain zero.
- **F04**: Record exact commands, exit codes, and concise outputs.
- **F05**: Prepare a review entrypoint and scoped changed-file manifest. Do not self-accept. Stop at `IMPLEMENTATION_CANDIDATE_AWAITING_INDEPENDENT_REVIEW`.

## 8. Conditional execution phases — dormant until explicit authorization

The same packet may be resumed for these phases only after the main thread records the exact command, fresh output root, budget, and explicit user authorization.

1. **X1 consistency probe**: no phase output, zero decoder phase calls; may run after implementation review if it is genuinely read-only.
2. **X2 multi-graph exploratory batch**: production decoder execution; requires Pre-EXECUTE review and explicit authorization.
3. **X3 failed-block reference ladder**: production decoder execution; authorize separately or explicitly together with X2 after its maximum call count is known.
4. **X4 G2**: sole n=256 length discriminator; separate explicit authorization required. Do not bundle implicitly with X2/X3.
5. **D7-H**: remains outside execution scope until X2–X4 evidence is reviewed and the main thread makes a new route decision.

No execution phase may review or accept its own results. Pre-RESULT independent review remains mandatory before result solidification.

## 9. STOP conditions

Immediately return `BLOCKED` with raw evidence if any of these occurs:

- requirement ambiguity changes seeds, thresholds, arms, evidence meaning, or accepted G2 semantics;
- first unequal tensor/value in B04 cannot be explained without changing the frozen contract;
- a required edit falls outside Section 5;
- a production decoder, CAL/VAL loader, formal root, or existing output is touched during A–F;
- an applicable test fails after one scoped root-cause fix attempt;
- an execution authorization, fresh root, or independent review is missing;
- unrelated dirty files prevent a scoped review.

Do not retry, tune, replace seeds, delete outputs, weaken tests, or continue to a later phase after STOP.

## 10. Return contract

Return exactly one of:

### COMPLETE

- completed acceptance IDs;
- changed-file manifest;
- exact tests/commands and results;
- production decoder/CAL/VAL call counts, expected to be zero for A–F;
- first-principles equivalence finding;
- remaining dormant phases and their exact authorization needs;
- commit IDs if created, and confirmation that nothing was pushed;
- lifecycle terminal `IMPLEMENTATION_CANDIDATE_AWAITING_INDEPENDENT_REVIEW`.

### BLOCKED

- completed acceptance IDs;
- exact failing command/check and raw error or first mismatch;
- remedies attempted, at most one scoped attempt;
- the single decision needed from the main thread;
- confirmation that no later phase ran and no protected output changed.

