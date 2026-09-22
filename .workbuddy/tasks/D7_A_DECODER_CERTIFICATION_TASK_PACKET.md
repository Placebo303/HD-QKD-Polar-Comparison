# D7-A — GF32 decoder ground-truth certification

## 0. Main-thread ruling and authority

NB-LDPC remains the research mainline. The previously frozen D6 R1d Option C
experiment is **paused**, not cancelled and not authorized:

`R1D_PAUSED_PENDING_DECODER_CERTIFICATION`

This packet authorizes one autonomous planning, implementation, test, review,
and documentation cycle for D7-A. It does not authorize any claim-bearing or
formal decoder run, D7-B/C/D execution, R1d, G1, G2, VAL, real/raw data, or a
push.

The operator may run the historical decoder function only on new, tiny,
fully synthetic in-memory fixtures created by D7-A tests. Such calls are
correctness-unit calls, not scientific decoder calls. They must not use the
Model-F artifact, frozen CAL blocks, formal mothers, formal roots, or any
existing development evidence root.

## 1. Baseline and first gate

- Repository: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Expected starting HEAD: `dfab1ed8`
- R1d state: frozen and Pre-EXECUTE reviewed, but unexecuted
- All execution authorization keys must remain false
- G2 must remain absent
- Existing formal/development/VOID roots are read-only and out of scope
- Known unrelated dirty files and CRLF churn must be preserved

The roadmap file
`docs/hd-qkd-ir-performance-roadmap-20260824.md` contains the main-thread D7
route as an uncommitted real-content change. Read it fully and verify that its
§12 says, in substance:

- stop local graph/mother patching;
- pause R1d pending decoder certification;
- the historical decoder is already row-layered FFT-QSPA;
- current L1→L2 already passes soft APP;
- D7-A→B→C→D is the active sequence;
- NB-LDPC remains mainline and Cascade is not part of this cycle.

If that scoped roadmap content is absent or materially different, STOP. Do not
reconstruct it from this packet. If it matches, it is an explicitly allowed
input and must be landed without semantic rewriting in the first docs commit.

Use scoped `git diff --numstat` and explicit manifests. Do not use a broad
porcelain-clean requirement. Do not clean, normalize EOLs, reset, checkout,
stash, rebase, amend, or broad-stage.

## 2. Objective and decision boundary

Determine whether the historical GF32 row-layered FFT-QSPA implementation
faithfully implements its intended finite-iteration sum-product algorithm and
field/syndrome conventions.

D7-A must answer these questions independently:

1. Are the GF32 arithmetic tables and symbol labels internally correct?
2. Does the FFT check-node update equal an independent direct sum-product
   enumeration for tiny checks, coefficients, syndromes, and nonuniform
   messages?
3. On a tree Tanner graph, do decoder marginals equal exact enumeration?
4. On a small loopy graph, do per-iteration messages/states equal an
   independently written recurrence for the same schedule?
5. Are coefficient permutations and nonzero-syndrome offsets applied in the
   correct direction?
6. Are normalization, probability/log-domain conversion, damping=1.0, cold
   start, stopping, and returned beliefs semantically consistent?
7. Does the existing L1→soft-APP→L2 bridge preserve the intended probability
   meaning without a shape/axis/softmax mistake?

This packet does **not** ask whether the actual CAL channel is recoverable,
whether flooding is better, whether bidirectional decoding works, or whether
R1d should run. Those belong to D7-B/C/D and later route decisions.

## 3. Scientific contract

### 3.1 System under test

The primary implementation under certification is the historical decoder in:

`comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`

including its GF32 tables, syndrome calculation, FFT-QSPA check update,
`decode_row_layered_fftqspa`, and returned `final_beliefs` semantics. The D5
adapter and layer bridge in
`comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
are also in scope for interface certification.

Do not change either production module in the first certification pass.

### 3.2 Independent reference rule

Create a small D7-owned reference module. It must be readable, direct, and
slow-by-design. It may use Python and NumPy, but it must not call or copy the
suspect implementation's:

- multiplication/inverse/permutation lookup arrays;
- FFT/Walsh convolution helper;
- check-update helper;
- syndrome-offset indexing helper;
- row-layered message-update code.

Implement field multiplication independently from the declared GF(2^5)
primitive polynomial using bitwise polynomial reduction. Construct reference
tables from that implementation. Implement direct check-node SP by explicit
enumeration of assignments for degree 2 and degree 3 checks. Tiny exact
posteriors must enumerate all assignments satisfying `H x = s`.

It is acceptable to import constants that identify the field polynomial or
alphabet size after independently checking their declared values. It is not
acceptable to import a derived table and call that an independent oracle.

### 3.3 Tree versus loopy acceptance

- Tree fixtures: compare normalized posterior vectors to exact enumeration.
  Required max-absolute tolerance: `1e-10`; MAP equality is secondary evidence,
  never a substitute for posterior equality.
- Loopy fixtures: do **not** compare finite-iteration BP with exact MAP. Compare
  the production algorithm's messages/beliefs after each complete iteration or
  row sweep with an independent implementation of the same row-layered
  recurrence. Freeze a precise iteration-count convention before writing the
  comparison.
- If production internals do not expose enough state, add a D7-only trace hook
  with default `None` whose disabled behavior and public return are unchanged.
  This is the only production-code change permitted in the initial pass, and
  it requires OpenSpec coverage and tests proving zero behavior change when
  disabled. Prefer no hook if beliefs after `max_iter=1,2,3` are sufficient.

### 3.4 Fixtures

Use deterministic, strictly positive, normalized synthetic priors. At minimum:

- every field element and every nonzero multiplier;
- zero and nonzero syndromes;
- degree-2 and degree-3 single checks;
- coefficients including `1` and at least three nontrivial nonzero elements;
- at least one two-check tree;
- at least one small cycle with nontrivial labels;
- cold start, `damping_alpha=1.0`, and `max_iter` in `{1,2,3}`;
- one already-satisfied case and one non-satisfied initial MAP case;
- probability vectors spanning ordinary and strongly skewed values without
  relying on exact delta priors.

Use fixed seeds only where generated vectors are clearer than literal fixtures.
Record every seed in the test or preregistration.

### 3.5 L1→L2 interface audit

Independently establish what `final_beliefs` represents in the historical
decoder: normalized probabilities, log-probabilities, log-likelihoods, or
another score. Then verify the conversion in `_run_layered_block` and
`app_fed_l2_prior` against an explicit probability calculation on tiny arrays.

In particular, test whether applying row-wise softmax is correct or whether it
double-exponentiates/alters an already normalized posterior. Check axis order
`(block position, GF32 symbol)`, Bob indexing, U1 conditioning, positivity,
normalization, and the fallback when beliefs are absent.

Any mismatch here is a decoder/interface correctness finding, even if the
standalone check kernel passes.

## 4. Required artifacts and allowed files

Create a new OpenSpec change:

`openspec/changes/v72p2d7-gf32-decoder-certification/`

with `proposal.md`, `design.md`, `tasks.md`, and the minimal spec delta needed.

Preferred implementation files:

- new
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_decoder_certification.py`
- new
  `comparison_bench/tests/test_v72p2d7_gf32_decoder_certification.py`
- optional narrowly scoped edits to
  `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`
  only for a disabled-by-default trace hook
- optional narrowly scoped tests in an existing v35/D5 test file only if a
  behavior-preservation assertion cannot cleanly live in the new test file

Create cycle documents under:

`docs/research_cycles/V72P2D7-GF32-DECODER-CERTIFICATION/`

Required:

- `D7_A_PREREG_R1.md`
- `D7_A_CERTIFICATION_REPORT_R1.md`
- `D7_A_CORRECTNESS_REVIEW_R1.md`

Allowed durable append-only updates at closeout:

- `docs/decision-log.md`
- `AGENT_PROJECT_MEMORY.md`
- `docs/hd-qkd-ir-performance-roadmap-20260824.md` (land the already written
  §12 content; no unrelated rewrite)

No `workspace/` result root is required. Pytest may use one fresh, named,
task-owned basetemp and remove only that directory after resolving and checking
its path. Do not write under any formal or previous development root.

## 5. Ordered execution plan

### T0 — Baseline and scope inventory

Read `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`, the roadmap §12, relevant D5/D6
acceptance/review documents, the two production modules, and existing related
tests. Record exact starting HEAD and explicit scoped status. Confirm R1d and
G2 target roots are absent and all authorization keys are false using metadata
only. Do not open VOID evidence contents.

### T1 — Freeze OpenSpec and preregistration

Before observing new numerical comparison results, write the OpenSpec and
`D7_A_PREREG_R1.md`. Freeze:

- reference independence rules;
- fixtures/seeds;
- tolerances;
- iteration/sweep convention;
- exact comparison fields;
- pass/fail classification;
- no-production-run boundary;
- allowed files and commands.

Commit planning/docs locally with an explicit path allowlist. This commit may
also land the roadmap §12 change. Do not push.

### T2 — Implement the independent oracle

Implement independent GF32 arithmetic, direct syndrome, direct check-SP, exact
tiny-graph posterior, and independent row-layered recurrence. Favor clear
loops over clever vectorization. Add self-tests that would fail under at least
one deliberately wrong coefficient direction and one deliberately wrong
syndrome shift.

### T3 — Certify arithmetic and check update

Compare production and independent results over the frozen exhaustive/sampled
matrix. Report maximum absolute error by family, normalization error, finite
status, and exact failing tuple if any.

### T4 — Certify tree and loopy dynamics

Run only tiny synthetic in-memory tests. For trees, compare full posterior. For
cycles, compare matched per-sweep beliefs/messages under the same row-layered
schedule. Record the first divergent iteration, node/edge/symbol, reference
value, production value, and max error.

### T5 — Certify adapter and L1→L2 soft APP

Audit and test `final_beliefs` semantics, `_decode_block`,
`_run_layered_block`, and `app_fed_l2_prior`. Explicitly detect unnecessary or
incorrect softmax. Do not repair a discovered mismatch in this task.

### T6 — Tests

Run in tiers:

1. `py_compile` for new/changed modules;
2. focused D7-A tests;
3. related v35/D5/D6 fake/unit tests needed to show no regression;
4. the established non-perf formal-IR suite only once at milestone closeout.

Never run perf-v38, any CLI `--phase`, R1d, formal G1/G2, preparation scripts,
or real/raw/CAL/VAL reads. Tests must not bind Model-F or production evidence.

### T7 — Independent correctness review

After implementation and tests, use a reviewer context that did not author the
reference logic. The reviewer must inspect source and recompute a representative
subset independently; merely trusting green tests is insufficient. Review:

- independence of the oracle;
- field polynomial and label convention;
- coefficient and syndrome directions;
- direct-SP enumeration completeness;
- tree posterior equality;
- loopy schedule equivalence and iteration convention;
- final-belief and L1→L2 APP semantics;
- scope, roots, authorization, and overclaim boundaries.

Allowed verdicts:

- `D7_A_DECODER_CERTIFICATION_PASS`
- `D7_A_DECODER_CERTIFICATION_FAIL_ARITHMETIC`
- `D7_A_DECODER_CERTIFICATION_FAIL_CHECK_UPDATE`
- `D7_A_DECODER_CERTIFICATION_FAIL_TREE_POSTERIOR`
- `D7_A_DECODER_CERTIFICATION_FAIL_LAYERED_DYNAMICS`
- `D7_A_DECODER_CERTIFICATION_FAIL_LAYER_INTERFACE`
- `D7_A_DECODER_CERTIFICATION_BLOCKED`

If multiple failures exist, report all and choose the earliest causal class as
the terminal verdict.

### T8 — Closeout

Create the report and review files, update OpenSpec task state, append only the
durable result to decision log and project memory, and make scoped local
commits. Do not push.

If PASS, set the documented next route to `D7_B_EASY_REGIME_PACKET_FREEZE`.
This is readiness to design D7-B, not authorization to execute it.

If FAIL, set the documented next route to
`D7_A_SCOPED_CORRECTNESS_REWORK_PROPOSAL`. Preserve the minimal counterexample;
do not fix the historical decoder in this packet and do not run R1d.

If BLOCKED, name one exact missing capability/evidence item and stop.

## 6. Acceptance matrix

- A01 baseline, branch, roadmap delta, authorization and roots checked
- A02 OpenSpec and prereg committed before new comparison results
- A03 independent GF32 oracle does not reuse derived production machinery
- A04 all field/table/label identities pass or have a minimal counterexample
- A05 direct-SP equals FFT check update within `1e-10`, or failure localized
- A06 nonzero syndrome and coefficient directions explicitly discriminated
- A07 tree full posteriors equal exact enumeration within `1e-10`
- A08 loopy comparison uses matched recurrence, never finite-BP-vs-MAP
- A09 iteration/sweep and damping/cold-start semantics are explicit
- A10 `final_beliefs` representation is established from code and tests
- A11 L1→L2 APP conversion is independently verified or precisely falsified
- A12 existing public behavior is unchanged unless a trace hook was required
- A13 no production/formal decoder, Model-F, CAL/VAL, real/raw, R1d/G1/G2 use
- A14 focused and milestone regression tests reported literally
- A15 independent correctness review completed with one allowed verdict
- A16 formal/development/VOID roots unchanged; G2 absent; auth keys false
- A17 only allowlisted files/commits; no push and unrelated dirty tree preserved
- A18 memory triage completed with only durable scientific/engineering facts

## 7. Hard stop rules

STOP immediately, without repair or continuation, if:

- branch differs or the expected baseline commits are not present;
- roadmap §12 materially conflicts with this packet;
- a target test would read Model-F, CAL, VAL, raw, formal or VOID evidence;
- a command would invoke `--phase`, R1d, G1 or G2;
- independent reference construction cannot avoid suspect derived machinery;
- a correctness mismatch is found: finish only the smallest counterexample,
  report, review and FAIL closeout; do not patch production in the same task;
- an unlisted production file would need modification;
- any authorization key changes or a protected root changes;
- scope cannot be isolated from unrelated dirty files.

Do not interpret a FAIL as proof that NB-LDPC is invalid. It means downstream
performance attribution is paused until a separate scoped correction is
reviewed.

## 8. Return format

Report deltas only:

1. starting/final HEAD and scoped commit list;
2. files changed and why;
3. A01–A18 table;
4. GF32 arithmetic/table findings;
5. direct-SP versus FFT maximum errors and worst tuples;
6. tree posterior and loopy per-sweep comparison results;
7. `final_beliefs` and L1→L2 APP conclusion;
8. literal compile/pytest summaries and failing IDs;
9. independent review verdict and blocking/non-blocking findings;
10. protected-root/auth/G2/no-push checklist;
11. next route, explicitly without execution authorization.

End exactly with one of:

`D7-A decoder certification 已通过；下一步仅可冻结 D7-B easy-regime 包，R1d、D7-B、G1、G2 均未授权。`

or

`D7-A decoder certification 发现 correctness 缺陷；下游性能归因暂停，等待独立修复任务，R1d、G1、G2 均未授权。`

or

`D7-A decoder certification 被具体 blocker 阻断；未形成通过结论，R1d、G1、G2 均未授权。`
