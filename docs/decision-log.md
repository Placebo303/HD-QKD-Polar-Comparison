# Decision Log

Durable decisions and rejected alternatives for the HD-QKD_Polar_Comparison project.

---

## Template

```
### YYYY-MM-DD: <Title>

**Decision**: <What was decided>

**Context**: <Why this was needed>

**Alternatives considered**:
- Alternative A: <Why rejected>
- Alternative B: <Why rejected>

**Consequences**: <What this means going forward>
```

---

## Decisions

### 2025-06-01: Non-invasive comparison layer architecture

**Decision**: The comparison benchmark is built as an outer wrapper (`comparison_bench/`) that reads the original Polar pipeline outputs without modifying them. The original `src/`, `experiments/`, and `tools/` directories are frozen baselines.

**Context**: We needed to compare multiple IR methods without risking regressions in the proven Polar pipeline.

**Alternatives considered**:
- Fork the repo and modify in-place: rejected because it would create maintenance burden and risk breaking the original workflow.
- Build a separate, fully independent project: rejected because we need to directly import/read Polar results.

**Consequences**: 
- `comparison_bench/` is the only mutable area for new IR comparison work.
- The `polar_existing` bridge in `comparison_bench/src/comparison_bench/io/polar_existing_bridge.py` is the sole interface for reading original Polar outputs.

---

### 2025-06-15: OpenSpec workflow initialization

**Decision**: Adopt OpenSpec as the change management workflow for all substantial feature work.

**Context**: Multi-agent workflow requires clear proposal → design → tasks → implement → review → archive pipeline.

**Alternatives considered**:
- GitHub Issues only: rejected because no structured design/spec/task linkage.
- Ad-hoc task lists: rejected because no durable record of decisions and spec changes.

**Consequences**:
- All substantial changes must go through `openspec/` workflow.
- `AGENTS.md` is authoritative for agent rules.
- `docs/decision-log.md` (this file) records durable decisions.

---

### 2026-06-15: Real IR success before final method selection

**Decision**: Prioritize verified real information reconciliation success on high-dimensional arrival-time QKD frames before final error-correction method selection or efficiency comparison.

**Context**: The existing Polar line has produced results, while most non-Polar comparison methods still need stable real-data verification success. Comparing `beta_eff_empirical`, leakage, or runtime before methods actually reconcile real frames risks optimizing a metric artifact instead of solving the IR problem.

**Alternatives considered**:
- Immediate final method selection: rejected because non-Polar methods have not yet established enough verified real-data success.
- Continue broad parameter sweeps first: rejected because broad sweeps are less useful until success/failure criteria and representative real-frame validation are explicit.
- Treat synthetic success as sufficient: rejected because the first-principles target is real high-dimensional arrival-time QKD reconciliation.

**Consequences**:
- The next active OpenSpec change is `real-ir-success-first`.
- Cascade-lite is treated as the first non-Polar real-success candidate, with simplified-Cascade caveats.
- Layered LDPC is treated as an executable failure-diagnosis target before being considered a final candidate.
- qLDPC remains a reference-grade q-ary feasibility direction until stronger evidence exists.
- Final method selection is deferred until verified real-data success and leakage accounting are established.

---

### 2026-07-25: Reconciled evidence is not final method-selection proof

**Decision**: Retain Cascade-lite as the preferred executable non-Polar
candidate and Layered LDPC as the control baseline, but defer final selection
until a new, pre-registered frame-identical confirmation change is completed.

**Context**: The Phase 0 reconciliation verified real-success, optimization,
expanded-evidence, and group-meeting artifacts. It also found material limits:
historical Polar is not frame-identical, low-dimensional group-meeting points
usually have only four frames, and historical changes do not all meet their
written acceptance criteria.

**Alternatives considered**:
- Archive historical changes solely because reports and manifests exist:
  rejected because the acceptance gaps are explicit and measurable.
- Declare Cascade-lite the final production method now: rejected because the
  evidence is bounded and accounting/Polar comparability are incomplete.

**Consequences**:
- No historical IR OpenSpec change is archived in this reconciliation pass.
- The next substantive work is a `final-ir-method-selection` OpenSpec change
  with fixed candidates, compatible leakage reporting, separate tuning and
  confirmation frames, and a stated stopping rule.

---

### 2026-07-25: Bounded final-IR confirmation yields no final winner

**Decision**: Record `no_decision` for the locked medium-SER confirmation; do
not promote Cascade-lite to a final winner from this run.

**Context**: The read-only Phase 4 audit at
`comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v4_audit/`
verified the same 60 unique locked confirmation keys for both candidates, all
attempted statuses, summary denominators, corrected-grid frozen configurations,
and recorded lock hashes. Cascade had 60/60 independently verified successes
and Layered LDPC 59/60; the exact pre-registered two-sided McNemar/binomial
p-value for the one discordant pair is 1.0 at alpha 0.05.

The prior v3 audit is superseded by its additive notice because a generic
decision-helper branch did not represent an LDPC winner or insufficient
evidence. That repair does not change this run's p=1.0 `no_decision` outcome.

**Alternatives considered**:
- Declare Cascade the winner on raw success count: rejected because the
  pre-registered paired test is not significant.
- Rank methods by reported leakage: rejected because the disclosure
  decompositions are method-specific and intentionally non-comparable.

**Consequences**:
- The evidence supports only real d=1024, 64-symbol frames with dataset raw
  SER in [0.20, 0.30); it makes no broader, Polar, qLDPC, or Route A proof claim.
- The non-numerical Route A compatibility gate is `fail`: the Phase-3 schema
  lacks the documented universal-hash protocol, leakage, and correctness-bound
  fields. No Route A numerical rerun was performed.

---

### 2026-07-25: Final-selection evidence is revalidated read-only

**Decision**: Keep the locked v1 data split, authoritative v2 run, and v4
audit immutable; use only read-only verification for their revalidation.

**Context**: Phase 5 hardened the comparison-layer workflow without changing
the frozen baseline or existing evidence. The v1 lock verification and v4
audit verification passed; the latter still reports `no_decision` with p=1.0
and a failing non-numerical Route A compatibility gate.

**Consequences**:
- Future Phase-3 runs require an explicit new additive output directory and
  persist `pre_run_plan.json` before tuning.
- The runbook at `comparison_bench/docs/final_ir_method_selection_runbook.md`
  is the operational entry point for lock, bounded run, and audit commands.
- The result remains bounded to its locked domain; no winner, cross-method
  leakage rank, Polar/qLDPC comparison, Route A numerical result, or proof
  completion is implied.
---

### 2026-07-25: Formal Cascade/LDPC Must Precede Three-Method Ranking

## Decision

Create OpenSpec `implement-formal-cascade-and-ldpc` before attempting a
frame-identical Cascade/LDPC/Polar comparison. It introduces additive
`cascade_formal_v1` and `ldpc_formal_v1` under an offline, already-authenticated
public-channel model, with Alice reference/Bob correction, universal2 Toeplitz
verification, explicit disclosure accounting, and independent qualification.

## Rationale

The existing `cascade_lite` and `layered_ldpc_lite` are executable baselines,
not sufficiently protocol-faithful formal competitors. A three-way comparison
before formalizing them would compare Polar to simplified implementations.

## Consequences

- Lite identities and historical evidence remain unchanged.
- No Polar adapter, formal winner, network/authentication cost, finite-key or
  Route-A numerical claim belongs to this change.
- A later OpenSpec may enable frame-identical three-method comparison only
  after separately qualified formal candidates exist.
- The active spec freezes exact Toeplitz seed/index/transcript semantics,
  Cascade FIFO look-back, deterministic HGF2V1 LDPC codebooks, calibration-only
  rate selection, pinned `ldpc==2.4.1`, additive artifact/status provenance,
  and predeclared synthetic and fresh real-frame promotion gates.
- One or both methods may be archived as `non_promoted`. Only promoted formal
  methods may enter a future Polar comparison; a non-promoted method requires
  a new improvement change and cannot be replaced by its lite predecessor.
- Pinned `ldpc==2.4.1` constructor behavior overrides its docstring: although
  the documentation advertises `random_serial_schedule`, the constructor
  rejects it. Formal kwargs omit it and require serial schedule, explicit
  `[0..63]` order, and one OMP thread. Preflight must prove exact kwargs
  acceptance with a no-decode 1-by-64 constructor probe and fail closed
  otherwise.

---

### 2026-07-25: Synthetic v2 is diagnostic and does not promote a method

**Decision**: Exclude synthetic v1 and v2 from promotion and reopen Phase 5 for
a fresh, contract-compliant v3. No formal method is promoted by these runs.

**Context**: v1 made zero frame calls. v2 listed the pre-registered Alice seed
`2026072501` and frame-order seed `2026072531` but did not use them; it
generated batches using undeclared Alice seeds `2026072502..2505`. Therefore
its outcomes and prior verifier pass do not prove pre-registered generation.

**Consequences**: v2 receives an additive invalid notice and remains diagnostic.
Fresh v3 must bind exact RNG calls/order, qualification-only shared verification
seeds, original transcript bytes, deterministic runner preflight, complete
provenance, exception finalization, and strict verification. Phase 6 and Polar
comparison remain unauthorized.

---

### 2026-07-25: Formal synthetic v3 promotes Cascade only

**Decision**: Record the immutable v3 synthetic qualification as promotion for
`cascade_formal_v1` and non-promotion for `ldpc_formal_v1`.

**Context**: The additive v3 package completed once and its strict read-only
verifier accepted all six artifacts and 128 outcomes. Cascade achieved 32/32
`verified_success` in each p=.01 and p=.02 stratum. LDPC achieved 29/32 and
14/32, below the 31/32 promotion threshold; all remaining outcomes were
retained `verify_failed`, with zero unclassified/internal/provenance/accounting
failures.

**Consequences**: Do not retune this LDPC evidence or replace it with a lite
method. Phase 6 locked real qualification remains required; no Polar adapter
or three-method ranking is authorized by the synthetic result.

---

### 2026-07-25: Bounded formal real qualification promotes Cascade only

**Decision**: Promote `cascade_formal_v1` for the locked real confirmation
domain only: `d=1024`, 64 symbols, bw120, frame SER `[0.20,0.30)`. Do not
infer general Cascade performance or a Cascade-versus-Polar winner.

**Context**: The unique real v2 package passed its strict read-only verifier.
All 60 requested confirmation frames were attempted, denominator-included,
verification-invoked, and `verified_success`, with verification union bound
`3.2526065174565133e-18` and zero unclassified/internal/provenance/accounting
failures. Its exact preflight passed 29 tests with exit 0. The invalid real v1
lock remained unexecuted and byte-preserved apart from its additive invalid
notice. Synthetic v3 separately promotes Cascade at 32/32 in both strata but
leaves LDPC non-promoted at 29/32 and 14/32; LDPC was not run on real data.

**Alternatives considered**:
- Generalize the 60-frame result to other dimensions, frame lengths, bandwidth
  groups, or SER regions: rejected because those domains were not qualified.
- Treat this as a Polar comparison or winner claim: rejected because Polar was
  not run frame-identically in this change.
- Substitute `layered_ldpc_lite` or retune formal LDPC on confirmation:
  rejected because the formal LDPC promotion gate failed and confirmation is
  locked evidence, not tuning data.

**Consequences**:
- The active formal-method change is technically ready for archive review, but
  is not archived until memory triage and the actual archive action complete.
- A new LDPC-improvement OpenSpec change must earn fresh synthetic and real
  promotion before any frame-identical Polar/Cascade/LDPC comparison.
- No general performance, Polar winner, cross-domain, or lite-equivalence claim
  follows from this bounded promotion.

---

### 2026-07-26: Formal LDPC v2 remains non-promoted after frozen qualification

**Decision**: Record `ldpc_formal_v2` as `non_promoted`; do not authorize a
real-data lock/run or a frame-identical Cascade/LDPC/Polar comparison.

**Context**: The active `improve-formal-ldpc-v2` change froze nine policies
(rate margins 0/1/2 crossed with `OSD_0/0`, `OSD_CS/1`, `OSD_CS/2`) and a
nested n=64 codebook with selected 32/40/48/56 prefixes. The prior v1
integration root is invalid because its v1 codebook verifier classified all
576 policy outcomes plus 64 associated outcomes as `unsupported_domain`; its
seven artifacts remain immutable with an additive invalid notice. A fresh v2
plan (SHA256 `c0770b5b1c80c277448ca832b01a5dd6d8413df78870fa040c6546d0098ede18`)
had zero old/new CSPRNG overlap and passed strict verification. Development
selected margin 2 with `OSD_0/0` (26/64, 33/64, 56/64 for margins 0, 1, 2,
identical across OSD variants). Confirmation was 28/32 at p=.01 and 29/32 at
p=.02, with seven `verify_failed`, verification invoked on all 64 outcomes,
and zero unclassified/internal/provenance/accounting failures.

**Alternatives considered**:
- Continue tuning against the confirmation outcomes: rejected because the
  confirmation set is frozen evidence, not development data.
- Treat structural codebook screening as qualification: rejected because it is
  only a structural proxy, not verified decoding evidence.
- Proceed to real qualification or three-method comparison: rejected because
  the synthetic promotion gate was not met.

**Consequences**:
- The short- and medium-term engineering tasks are complete with reproducible
  evidence, but LDPC remains below promotion.
- Archive the completed engineering change as explicit non-promotion evidence;
  archiving does not authorize real LDPC qualification or comparison.
- Terra low acted only as the frozen-task implementer/test operator; the main
  thread retained planning and acceptance.

---

### 2026-07-29: Standardize the project-wide agent delivery workflow

**Decision**: Adopt `AGENTS.md` §10.1 as the global default and
`AGENT_HANDOFF.md` as the operator checklist for substantial delegated work.

**Context**: Formal qualification work repeatedly discovered acceptance
requirements late, returned partial subagent status as completion, reran broad
tests after small edits, hit Windows temp ACL failures, and accidentally
entered production decoder paths from tests.

**Consequences**:
- Freeze stable acceptance IDs and feasibility checks before delegation.
- Reuse the nearest accepted predecessor through an explicit delta list.
- Use T0--T3 staged verification and explicit fake runners in test-only paths.
- Use additive Windows workspace roots, process ownership, scoped dirty-tree
  review, and compact delta-only handoffs.
- Preserve all scientific gates, immutable failures, no-rerun/no-tuning rules,
  and main-thread production authorization.

---

### 2026-07-26: Advance binary and nonbinary LDPC as independent parallel lanes

**Decision**: Continue binary LDPC and nonbinary LDPC in parallel, with
separate formal method identities, OpenSpec changes, codebooks, evidence
chains, disclosure accounting, and promotion decisions.

**Context**: `ldpc_formal_v2` is reproducible but non-promoted at 28/32 and
29/32. Its n=64 result points toward longer frames, stronger code families,
incremental redundancy, and bit-plane soft information. The existing
`qldpc_reference` path uses reference-grade matrix construction and hard
syndrome decoding and does not satisfy the formal backend, codebook,
verification, or leakage contracts required of a production-oriented
nonbinary method.

**Alternatives considered**:
- Improve only binary LDPC: rejected because nonbinary symbol-domain coding is
  a scientifically distinct candidate worth evaluating.
- Treat `qldpc_reference` as the formal nonbinary method: rejected because that
  would overstate its implementation and evidence.
- Use one shared qualification pipeline and promotion result: rejected because
  field arithmetic, codebooks, decoder semantics, and leakage decompositions
  differ materially.

**Consequences**:
- Binary and nonbinary work may proceed concurrently through their engineering
  and synthetic-qualification stages.
- The provisional new nonbinary identity is `nbldpc_formal_v1`; the existing
  `qldpc_reference` identity and status remain unchanged.
- Neither lane may reuse existing confirmation evidence for tuning or borrow
  the other lane's promotion.
- A later fair comparison requires independent promotion and frame-identical
  inputs, with disclosure normalized to bits while preserving method-specific
  decomposition.

---

### 2026-07-26: Accept binary long-frame candidate-codebook foundation only

**Decision**: Accept Phase 1 of `binary-ldpc-long-frame-and-ir-v3` as an
offline, candidate-only engineering foundation. Do not select a code family,
wire a decoder, or infer FER or promotion.

**Context**: The additive implementation supports n=256/512/1024, ten planes,
four deterministic candidates, and four nested redundancy prefixes. Canonical
HGF2V3 bytes and a complete 120-candidate manifest bind construction and
structural diagnostics. Main-thread verification passed the focused 4-test
suite, the v2 regression, compilation, and frozen-directory checks.

**Consequences**:
- `ldpc_formal_v2` and its non-promotion evidence remain unchanged.
- Rank, weight, 4-cycle, and `column_pair_extrinsic_degree_v1` values are
  structural proxies, not decoder evidence.
- The next work package must freeze sacrificed-development FER evaluation and
  candidate-selection rules before it reads any development frames.
- Confirmation and real data remain unauthorized.

---

### 2026-07-26: Accept the long-frame development evaluator, not FER evidence

**Decision**: Accept the Phase 2 sacrificed-development evaluator and exact
candidate-selection contract. Do not claim that any candidate or length has
demonstrated FER improvement.

**Context**: The in-memory kernel freezes deterministic p=.01/.02 development
data, pinned BP+OSD-0 parameters, four nested syndrome prefixes, retained
failure statuses, incremental disclosure, and a runtime-independent
lexicographic selection tuple. Main-thread tests independently reconstructed
seed/hash preimages and exercised valid and malformed selection grids.

**Consequences**:
- The evaluator is ready for a separately frozen pinned-backend pilot.
- Injected-decoder tests are contract evidence, not LDPC performance evidence.
- No full development sweep, confirmation, real-data run, candidate
  qualification, or promotion is authorized by Phase 2.

---

### 2026-07-26: Backend pilot clears feasibility, not performance

**Decision**: Use the successful single-slice pinned-backend pilot to proceed
with planning a full sacrificed-development sweep. Do not treat the pilot as
candidate-selection or FER qualification evidence.

**Context**: The one authorized n=256/plane0/candidate0/p=.01 run completed
16/16 exact successes using `ldpc==2.4.1`, mostly at p050, in 0.323 seconds
process time and 1.0 second external wall. It wrote no files.

**Consequences**:
- Backend/API feasibility is no longer the immediate blocker for n=256.
- n=512/1024, other planes/candidates, comparative FER, artifact finalization,
  and verifier cost remain unmeasured.
- A full development sweep requires a new frozen runner/artifact/verifier
  contract before execution.

---

### 2026-07-26: Accept full-development tooling before running the sweep

**Decision**: Accept the Phase 3B runner/verifier implementation and its
test-only evidence. Keep production plan creation and execution as separate
review gates.

**Context**: The tool freezes 3840 ordered outcomes, 30 selections, six
canonical artifacts, a complete hash DAG, failure finalization, no-overwrite,
and strict production/test isolation. Tests cover valid and failed packages
plus semantic tampering after downstream hashes are recomputed.

**Consequences**:
- Tooling is ready to prepare one fresh production plan.
- No candidate FER or selection exists until the production sweep completes
  and the read-only verifier accepts its package.
- Verifier acceptance will still mean artifact integrity and deterministic
  selection reconstruction, not decoder reexecution or promotion.

---

### 2026-07-26: Full per-plane development succeeds but exposes a stopping oracle

**Decision**: Retain the verified 3840-row development package and its
candidate selections, but do not use its per-plane terminal leakage or
100%-success result as formal qualification evidence.

**Context**: Every candidate/length/plane/stratum outcome was an exact
development success. The strict verifier accepted the package and reconstructed
all 30 selections without rerunning decoding. However, the development
evaluator stops each plane by comparing corrected bits directly with Alice.
Bob does not possess that truth oracle in a deployed protocol.

**Consequences**:
- The code-family/backend lane is promising enough to continue.
- Per-plane terminal rounds must be lifted into ten-plane frame-level rounds.
- A formal design should disclose one frame-wide Toeplitz tag and let the
  slowest plane determine each global incremental-redundancy stop.
- Qualification and promotion remain unauthorized until frame-level
  development leakage and stopping semantics are frozen and tested.

---

### 2026-07-26: Select n=256 from frame-level sacrificed development

**Decision**: Freeze n=256 as the next binary LDPC formal-development length.
Do not qualify it until actual frame-wide Toeplitz stopping and formal
transcript/status accounting are implemented.

**Context**: Ten-plane aggregation retained 16/16 successes in both strata for
all three lengths. With one modeled 64-bit tag and slowest-plane global
rounds, n256 had the lowest worst-stratum and overall disclosure fractions:
.68125 and .62265625. The exact selection tuple was
`[-16,-32,.68125,.62265625,256]`.

**Consequences**:
- Candidate IDs selected per n256 plane remain frozen from Phase 3C.
- Formal v3 should use n=256, q=1024, ten planes, and the four global nested
  prefixes.
- Actual Toeplitz tag execution, transcript disclosure, caps and status
  semantics must be implemented before fresh confirmation is planned.
- No promotion follows from sacrificed development.

---

### 2026-07-26: Accept executable binary LDPC v3 before qualification

**Decision**: Accept `ldpc_formal_v3` as the binary lane's formal method
implementation for q=1024/n=256, while withholding qualification and
promotion.

**Context**: The method executes ten frozen Gray bit planes in synchronous
nested-syndrome rounds and uses one locked frame-wide Toeplitz tag only for
global stopping. Tests cover later-round correction and a full-prefix
nullspace error that remains syndrome-consistent through four rounds and ends
`verify_failed`.

**Consequences**:
- Alice truth and verification-tag feedback are not decoder inputs.
- Transcript validation binds round, terminal prefix, incremental syndrome,
  tag, seed, epsilon, backend, calibration and candidate selection.
- Phase 6 must pre-register fresh confirmation, calibration binding, package
  DAG/verifier, gate and stop rules before execution.
- Engineering acceptance does not make the method comparison-eligible.

---

### 2026-07-26: Stop binary LDPC v3 after failed Phase 6 synthetic gate

**Decision**: Retain the strictly verified Phase 6B package as non-promoted
and do not create or execute the real Phase 6C lane.

**Context**: The TTBIN-derived calibration exposed strongly unequal Gray-plane
BER, reaching about .123 on plane 9. Fresh confirmation produced only 3/32
verified successes in the calibrated stratum and 1/32 under 1.25x stress,
against independent 31/32 gates. The remaining 60 frames were classified
`verify_failed`; integrity and accounting failures were zero.

**Consequences**:
- This is an algorithmic/code-channel mismatch, not a packaging/verifier
  failure.
- Real confirmation remains sealed by the synthetic hard gate.
- No confirmation tuning, rerun, real-data execution, or comparison claim is
  allowed.
- A successor requires a new decoder/code-design proposal and fresh synthetic
  confirmation.

---

### 2026-07-26: Pin the nonbinary N0 field contract before decoder selection

**Decision**: Implement the first `nbldpc_formal_v1` slice as a deterministic
internal polynomial-basis GF(2^m) contract for powers-of-two q through 1024,
with canonical field IDs and a read-only fail-closed preflight. Keep
`qldpc_reference` unchanged.

**Context**: The formal nonbinary lane needs an exact field representation and
q=1024 support before a soft-decoder backend or codebook can be evaluated.
The existing reference fallback stops at q=256 and its greedy hard decoder is
not a promotion candidate.

**Alternatives considered**:
- Relabel `qldpc_reference`: rejected because its implementation and evidence
  remain reference-grade.
- Install a large decoder/GF dependency immediately: deferred until a bounded
  N1/N2 contract identifies the smallest backend that satisfies the frozen
  interface.

**Consequences**:
- N0 establishes field-backend feasibility only. It does not establish
  decoder feasibility, qualification, promotion, or performance.
- Unsupported q, non-integral field inputs, field-ID mismatch, and arithmetic
  inconsistency fail closed without backend or lower-q fallback.
- N1 must define deterministic GF(q) codebooks, GF(q) rank, canonical bytes,
  and manifest hashes. N2 must separately freeze soft decoding and formal
  disclosure/Toeplitz accounting before experiments.

---

### 2026-07-26: Freeze the nonbinary N1 structural codebook family

**Decision**: Use a pure in-memory n=64 nonbinary family with one deterministic
32x64 mother matrix and exact 16/24/32 ordered prefixes. Verify rank over the
pinned GF(q), and identify every codebook and ordered family manifest through
canonical `NBLDPC1` bytes and SHA256.

**Context**: The formal lane needs immutable, rate-compatible codebook
identities before any soft decoder can be evaluated. Random reference matrices
and GF(2)/real rank would not provide that evidence.

**Alternatives considered**:
- Random sparse matrices: rejected because their topology and identity would
  not be a stable formal contract.
- PEG search or an external code-design dependency: deferred because the
  deterministic cyclic/protograph-style plus identity construction satisfies
  the bounded N1 structural contract without adding dependency or search
  nondeterminism.

**Consequences**:
- N1 has reproducible GF(q) ranks, prefix relations, canonical bytes, golden
  hashes, and fail-closed tamper verification for q through 1024.
- Structural rank/hash evidence is not decoder feasibility, distance/FER
  performance, qualification, promotion, or comparison evidence.
- N2 must freeze soft decoding and exact public-disclosure/Toeplitz accounting
  before decoder implementation, dependency selection, or experiments.

---

### 2026-07-26: Accept bounded nonbinary FFT-QSPA feasibility only

**Decision**: Use a pure full-message probability-domain FFT-QSPA as the first
bounded `nbldpc_formal_v1` decoder-feasibility implementation. Keep EMS and
min-sum as separately pre-registered alternatives rather than inventing an
unreviewed truncation/tail rule.

**Context**: The q=2^m additive group permits q log(q) Walsh-Hadamard check
convolution, while the pinned N1 matrices require exact nonzero GF(q)
coefficient permutations. The decoder must implement syndrome/coset semantics
without reading Alice truth, and q=1024 must fail closed under explicit
resource bounds.

**Consequences**:
- q=4 coefficient/coset messages agree with brute-force convolution, and a
  bounded q=1024 no-error case executes within the declared memory cap.
- Syndrome consistency remains distinct from locked Toeplitz verification;
  syndrome, tag, and public-control disclosure are separately accounted.
- These are unit-level engineering feasibility results, not general
  correction, FER/performance, calibration, qualification, promotion,
  real-data, production, or comparison evidence.
- N3 may not execute until development/confirmation isolation, claim domain,
  global policy, metrics/gates, resources/stops, artifacts/statuses,
  invalid-run handling, and strict verification are pre-registered.
### 2026-07-26: Nonbinary N3 is non-promoted and strict-verification-unverifiable

**Decision**: Retain the sole `nbldpc_formal_v1` N3 package unchanged as
non-promoted. Do not tune confirmation, rerun, or authorize N4 real-data work.

**Context**: The frozen q=1024 synthetic run selected margin 7, scale 1.0,
max_iter 10 and 32 checks. It achieved 18/32 verified successes at p=.20 and
5/32 at p=.30, below the independent 31/32 gates. The official strict CLI
verifier then failed only because live whole-worktree `git_status_sha256`
drifted post-execution. Source/CLI/contract hashes, commit, Python and NumPy
matched; a diagnostic `_test_only=True` replay checked artifacts/DAG/gates but
does not qualify as official verification.

**Consequences**: The seven artifacts at
`comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_nbldpc_synthetic`
remain immutable. No promotion, N4, real-data claim, performance comparison,
or confirmation retuning follows.

---

### 2026-07-26: Stop nonbinary LDPC v2 before confirmation

**Decision**: Retain the sole strictly verified `nbldpc_formal_v2` package as
`non_promoted_development`; do not generate confirmation or authorize N4.

**Context**: The selected QC48 tempered+damped policy used margin 8,
max_iter 10, and 32/40 checks for p=.20/.30. Fresh sacrificed development
achieved 0/24 and 5/24 verified successes, below the frozen 22/24 floor in
both strata. The sole execution and full deterministic replay both exited
successfully; scoped provenance passed.

**Consequences**:
- This is development non-readiness, not confirmation failure or FER.
- No confirmation rows/events were generated or executed.
- No rerun, tuning, N4 sidecar adapter, `.ttbin` processing, real-data claim,
  or comparison claim is authorized.

---

### 2026-07-27: Stop binary LDPC v4 at the production development gate

**Decision**: Retain the sole strictly verified
`20260727_v1_binary_ldpc_v4_development` package unchanged and stop before
fresh synthetic preparation. Do not create real qualification evidence,
retune, or rerun this package.

**Context**: The frozen plan executed all 40,960 candidate-plane outcomes and
the read-only verifier reconstructed source, channel, codebooks, selection,
accounting, and readiness without decoder reexecution. Nominal and stress each
had 0/512 frame successes and 5,120 forbidden
`development_decoder_error` plane outcomes, so neither met 495/512.

A subsequent no-decode constructor diagnostic identified a backend-boundary
implementation defect: `ldpc==2.4.1` rejects the NumPy `error_channel` passed
by `ldpc_v4_development.py` and requires a Python list. The formal v4 method
already performs that conversion. Consequently this package is not FER
evidence and cannot support a scientific rejection of the code family.

**Consequences**:
- No production v4 synthetic or real directory, data lock, execution, or
  qualification result exists.
- The immutable package and scoped source hashes remain the audit record.
- Fair Cascade/LDPC/Polar comparison remains blocked.
- Any continuation requires a new main-thread OpenSpec implementation
  correction with a production-constructor regression and newly versioned
  evidence. It must not be represented as a retry or parameter tuning of v4.

---

### 2026-07-27: Accept the versioned v4 backend correction at development

**Decision**: Accept
`20260727_v2_binary_ldpc_v4_development` as strictly verified,
development-ready evidence. Preserve both the failed v1 package and corrected
v2 package unchanged. Do not treat development readiness as qualification.

**Context**: The correction changed only the pinned decoder constructor
boundary from a NumPy float64 array to an equivalent Python list. All matrices,
channel probabilities, deterministic frames, decoder parameters, selection,
accounting, and the 495/512 gates were unchanged. The package achieved 510/512
nominal and 511/512 stress with zero forbidden failures. The read-only verifier
reconstructed predecessor, source, model, codebooks, selection, accounting,
and gates without decoder reexecution.

**Consequences**:
- The confirmed constructor defect is resolved for the versioned development
  path.
- Binary v4 is eligible for a separately reviewed fresh synthetic prepare.
- No synthetic promotion, real-data readiness, FER claim, or fair
  Cascade/LDPC/Polar comparison follows from this decision.
- Do not rerun or tune the immutable development package.

---

### 2026-07-28: Promote corrected binary v4 synthetic; wait for real capacity

**Decision**: Accept the strictly verified corrected-v2 synthetic package as
promoted. Do not prepare real qualification until the registered 128-frame
capacity exists independently in all three real strata.

**Context**: The fresh package achieved 127/128 nominal and 126/128 stress
with zero forbidden failures. Its eight CSPRNG roots and 256 Toeplitz seeds
are unique and disjoint from v3 and development. Read-only verification
reconstructed the full prerequisite/source/method/transcript/outcome/gate DAG
without decoder reexecution.

The current source has 117 complete frames in each of bw120, bw180, and bw200.
The frozen exclusion of 32 v3-reserved identities leaves 85 eligible, a
43-frame deficit against 128.

**Consequences**:
- Binary v4 has passed its independent synthetic qualification.
- Do not reuse v3-reserved real frames or lower the 128/126 gate to fit the
  current capture.
- Obtain traceable same-domain data, preferably at least 64 new complete
  frames per stratum, freeze an extended source manifest, and only then create
  one real lock/plan.
- No real `.ttbin` promotion or Cascade/LDPC/Polar comparison claim exists yet.

---

### 2026-07-28: Accept the v4 real-source intake layer

**Decision**: Accept the frozen source-extension builder, candidate pool, real
lock binding, and read-only reconstruction. Continue to block production real
prepare until a genuinely distinct same-domain acquisition is supplied.

**Context**: The only additional local 20 dB directory has byte-identical
main/chunk `.ttbin` hashes and is therefore a copy, not independent capacity.
The new intake rejects duplicate raw pairs and duplicate 256-symbol payloads,
binds all three q=1024 sidecars and their provenance, ignores rather than pads
natural incomplete tails, and deterministically reconstructs selection without
decoding.

Main-thread acceptance passed 3 source, 5 real, 7 bridge/source, and 25
backend/development/formal-real tests. The first broad regression used a
repository-internal temporary root and retained 8 environment failures; the
same suite passed 25/25 using its required external temp root.

**Consequences**:
- New data can be validated and frozen without modifying the historical v3
  bridge or inspecting real qualification outcomes.
- A copied or re-materialized registered capture supplies zero new capacity.
- Real prepare must bind a reviewed source-extension manifest and remains
  forbidden until all strata have at least 128 eligible frames.
- The next external input is a distinct 20 dB `.ttbin` main/chunk pair with
  traceable bw120/bw180/bw200 sidecars; prefer at least 64 complete frames per
  stratum.

---

### 2026-07-29: Retain the non-promoted 16 dB transfer and pre-register 10 dB

**Decision**: Retain the sole verified 16 dB transfer package as immutable
non-promoted evidence. Do not tune or rerun it. Pre-register one
unchanged-method transfer qualification on the independent 10 dB Type-II
capture.

**Context**: The 16 dB package completed all 384 denominators. bw120 achieved
125/128 against the frozen 126/128 floor; bw180 and bw200 achieved 128/128;
all forbidden counts were zero. Strict verification succeeded without decoder
reexecution or file changes. The 10 dB capture has 1108, 1111, and 1112
complete frames in the same q=1024 bw120/bw180/bw200 processing layers.

**Consequences**:
- The 16 dB and original 20 dB domains remain unpromoted.
- No v4 parameter, matrix, channel, decoder, leakage, cap, or gate changes are
  authorized for the 10 dB transfer.
- The 10 dB package must bind both the promoted synthetic prerequisite and the
  exact non-promoted 16 dB predecessor.
- A promoted result would establish only registered 10 dB transfer, not a
  general real-data or multi-loss claim.

---

### 2026-07-29: Reject 10 dB v1 at prepare review

**Decision**: Do not execute the v1 10 dB plan. Preserve its two files as
immutable `invalid_pre_execute` evidence and permit only a versioned v2
self-exclusion correction.

**Context**: v1 prepare completed without decoding, but strict post-write
validation rediscovered the current plan among prior real plans and therefore
collided with its own roots. This was detected at the required main-thread
review gate before execute.

**Consequences**:
- No 10 dB result has been observed and v1 is not qualification evidence.
- v1 must not be overwritten, deleted, or executed.
- v2 may exclude only its exact current plan SHA during validation.
- v2 must bind v1 and forbid all v1 roots and seeds; all scientific semantics
  remain unchanged.

---

### 2026-07-29: Retain 10 dB v2 non-promotion; develop v5 IR

**Decision**: Retain the strictly verified 10 dB v2 package as non-promoted.
Do not rerun v4 on 10 dB or move through easier losses until a pass appears.
Develop binary LDPC v5 using a pre-locked unused-frame development and
confirmation split.

**Context**: v2 achieved 125/128 at bw120, 127/128 at bw180, and 128/128 at
bw200, with zero forbidden failures. The misses were final Toeplitz
mismatches after complete fixed v4 syndrome decoding. The same fixed policy
also missed 16 dB by one frame, so rate/decoder robustness is the repeated
limitation.

**Consequences**:
- Reserve 512 unused development and 128 sealed confirmation frames per 10 dB
  layer before any v5 decoding.
- Screen only the pre-registered control, stronger OSD, and incremental
  syndrome policies.
- Count all added syndrome/tag disclosure and feedback; a pass with excessive
  leakage remains visible rather than being called free improvement.
- Require a fresh synthetic confirmation before the sealed real attempt.

---

### 2026-07-30: Retain nonbinary LDPC v3 synthetic non-promotion

**Decision**: Retain the sole strictly verified v3 covered-layered synthetic
package as immutable non-promotion evidence. Do not rerun, tune confirmation,
or begin N4/sidecar/`.ttbin` work.

**Context**: The selected layered-l075 margin-8 policy passed development
readiness at 23/24 for p=.20 and 24/24 for p=.30. Its sealed confirmation then
achieved 32/32 and 30/32 with zero prohibited failures. The frozen promotion
floor was 31/32 in each stratum, so p=.30 missed by one frame. The sole strict
read-only replay returned `verified=True`, `run_status=completed`, and
`promoted=False`.

**Consequences**:
- The new codebook and decoder route is implemented and qualified as a
  reproducible synthetic experiment, but is not promoted.
- Confirmation failures remain retained; no post-result parameter search or
  rerun is authorized.
- N4 and real `.ttbin` ingestion remain blocked by the synthetic promotion
  gate and require a new approved OpenSpec change even after promotion.

---

### 2026-07-31: Retain nonbinary LDPC v4 IR synthetic non-promotion

**Decision**: Retain the sole strictly verified v4 incremental-redundancy
package as immutable non-promotion evidence. Stop at A3; do not rerun, tune,
or begin N4/sidecar/`.ttbin` work.

**Context**: Development selected the warm 40→48/32→40 IR policy at 64/64 for
p=.20 and 63/64 for p=.30. Sealed confirmation achieved 128/128 at p=.20 and
120/128 at p=.30. All eight misses were `decode_failed`; there were zero
prohibited failures. The pre-registered gate was exactly 128/128 per stratum.
The sole verifier returned `verified=True`, `run_status=completed`, and
`promoted=False`.

**Consequences**:
- Preserve the complete eight-artifact package without overwrite or rerun.
- One extra eight-symbol syndrome prefix materially improved v3 but did not
  eliminate the p=.30 tail under the frozen decoder and codebook.
- A successor may investigate a stronger pre-registered rate-compatible
  family, additional extension stage, or decoder/codebook redesign only on
  fresh synthetic development data.
- Existing v4 confirmation failures are diagnostic evidence, not tuning data.
  Real-data eligibility remains blocked.

---

### 2026-08-01: Retain nonbinary LDPC v5a Route A synthetic non-promotion

**Decision**: Retain the sole completed v5a multistage-IR package at
`comparison_bench/outputs_comparison/formal_ir_methods/20260731_v5a_nbldpc_multistage_synthetic`
as immutable non-promotion evidence. Do not rerun, tune confirmation, or begin
N4/sidecar/`.ttbin` work. Continue to Route B (task 5.1) as pre-registered.

**Context**: The frozen plan (development seeds 202607720000/730000,
confirmation 202607740000/750000, 128 frames per stratum, caps checks<=56 /
row weight<=8 / stage iterations<=12 / workers 1, probe 202607719999) executed
once: all 512 outcomes completed (`run_status=completed`, `outcome_count=512`).
Readiness passed (both strata >= 63/64) and confirmation material was
atomically materialized and executed. Promotion gates: p=.20 stratum 128/128,
p=.30 stratum 127/128 (one `decode_failed` tail miss), so `promoted=false`
against the frozen 128/128 floor in both strata. Zero prohibited failures.

The pre-registered strict read-only replay was attempted once and could not
run: between plan creation (git HEAD `71bda20d`) and the replay attempt, an
external session committed two unrelated changes (HEAD `3a5d96a`, binary LDPC
v1 sacrificed-development package and a Phase-2 verifier conformity fix;
neither touched any v5a source file). The frozen `_validate_plan` provenance
check therefore rejects the current HEAD. Source/CLI/contract hashes all
still match; only the `git_commit` provenance field drifted. This is an
external interference event, not a package defect; per at-most-once semantics
the strict replay is not rerun.

**Alternatives considered**:
- Reset HEAD to the plan-frozen commit and replay: rejected because it would
  discard another session's committed work.
- Re-run the strict verifier in a temporary worktree: rejected because
  untracked v5a sources and the official output path do not exist there; a
  mirrored environment would not verify the real package.
- Treat the blocked replay as package verification: rejected; the package
  remains "completed but replay-blocked" until a future window with matching
  HEAD re-enables the at-most-once strict replay.

**Consequences**:
- The eight-artifact package is immutable; no rerun or confirmation tuning is
  authorized (no-rerun/no-tuning rules intact).
- Route B (`20260731_v5b_nbldpc_mother_synthetic`, roots 202607760000-
  202607790000) is next; Route A evidence does not establish codebook/decoder
  failure, only failure of the 128/128 promotion floor in the p=.30 tail.
- s6* shift-difference intersection deviation (task 1.3 UNSAT contingency:
  `mask_a ∩ mask6` replaced the full 6-element mask condition; recorded in
  codebook docstring and v5a acceptance evidence) is registered here as a
  formal deviation of the frozen design, not a gate or leakage change.
- Any later strict replay must happen only when the repository HEAD matches
  the plan-frozen commit, and remains an at-most-once action.

---

### 2026-08-01: Retain nonbinary LDPC v5b Route B synthetic non-promotion

**Decision**: Retain the sole completed v5b mother-redesign package at
`comparison_bench/outputs_comparison/formal_ir_methods/20260731_v5b_nbldpc_mother_synthetic`
as immutable non-promotion evidence. Do not rerun or tune. Continue to Route C
(task 6.1) as pre-registered.

**Context**: NBLDPC5B (7 frozen 8-row block templates, disjoint-shift-
difference shift enumeration, salt 0, K=8 proxy candidates with w2=w3=0 —
zero weight-2/weight-3 syndrome collisions over the 56-row mother) ran once:
all 512 outcomes completed (`run_status=completed`, `outcome_count=512`).
Readiness passed in both strata; confirmation material was materialized and
executed. Promotion gates: p=.20 128/128, p=.30 127/128 (one tail miss), so
`promoted=false` against the frozen 128/128 floor. Zero prohibited failures.

The pre-registered strict read-only replay was attempted once and could not
run: between plan creation (git HEAD `3a5d96a`) and the replay attempt an
external session committed an unrelated `ldpc_v5_development` speedup (HEAD
`4dd6b7e`); the frozen `_validate_plan` provenance check therefore rejects
the current HEAD. Source/CLI/contract hashes all still match; only the
`git_commit` provenance field drifted — the same external-interference
pattern already recorded for v5a.

**Alternatives considered**:
- Reset HEAD or drop the external commit: rejected — would discard another
  session's committed work.
- Verify in a temporary worktree: rejected — untracked v5b sources and the
  official output path do not exist there.
- Treat the blocked replay as verification: rejected; the package remains
  "completed but replay-blocked" until a matching-HEAD window re-enables the
  at-most-once strict replay.

**Consequences**:
- The eight-artifact package is immutable; no rerun or confirmation tuning is
  authorized.
- Route C (`20260731_v5c_nbldpc_decoder_synthetic`, roots 202607800000-
  202607830000) is next; codebook identity is fixed to NBLDPC5B (Route B ran
  and is non-promoted).
- A zero-short-weight-codeword mother did not close the p=.30 tail either;
  the remaining lever is the decoder family (damping-schedule FFT-QSPA vs
  truncated EMS), not further codebook search.
- Any later strict replay must happen only when the repository HEAD matches
  the plan-frozen commit, and remains an at-most-once action.

---

### 2026-08-01: Phase 2 speedup refactor and single re-execute approval

**Decision**: Accept the performance refactor of the Phase 2 execute/verify
path (commit `4dd6b7e`) with two formal deviations from the frozen
`phase2-task-packet.md` contract, and approve one fresh prepare/execute/verify
cycle to replace the invalidated official package. The new package
(`20260731_v1_binary_ldpc_v5_development`, plan_sha256
`287d17e825f5bc2a230de7e3b27a77fb99587a91c6057780b5d91d7df7f427d3`) is the
single executed package; the first attempt wrote zero artifacts
(`ValueError: plan frozen equality` — plan binds frozen source hashes and the
source changed under it) and the stale directory was deleted.

**Deviations (semantic-preserving, approved by main thread before re-execute)**:
1. Per-frame loader: `_execute` validates the partition lock once and builds
   rows from `lock["role_rows"]`; per-frame symbols now come from
   `_production_arrays_for_frame` (role membership check + cached
   `build_source_lock()`), replacing per-frame `development_arrays_for_frame`.
2. Verifier: source lock is built once per run instead of per frame; the
   full partition-lock rebuild is skipped for test-injected packages.

**Context**: The unmodified contract cost ~100 s per frame (partition-lock
validation inside the per-frame development loader) and ~0.086 s per frame in
the verifier — an estimated ~130 h wall clock for 4608 frames. The refactor
cut the test suite from 484 s to 97 s (29 passed, 1 skipped), and the official
execute completed in ~4.5 min with per-512-frame progress logs.

**Alternatives considered**:
- Keep the frozen contract and wait ~130 h: rejected as operationally
  unacceptable; speedup is behavior-neutral (verified by
  `test_production_array_loader_matches_locked_source` plus 29-test suite).
- Amend the plan in place: rejected; plans are immutable by design, the only
  legal path is one fresh prepare/execute/verify cycle.

**Consequences**:
- Official package verified once: EXIT=0,
  `{"decoder_reexecution":false,"outcomes":4608,"ready_for_synthetic_prepare":true,"run_status":"completed","selected_candidate_id":"V5-C2","status":"verified"}`.
- V5-C0/C1 are intentionally inactive control candidates (`active=False` in
  `ldpc_v5.py`); their 512x3 `backend_unavailable` rows are expected, not a
  defect.
- The speedup pattern (lock validated once, cached source lock, progress
  logs) is now the normal Phase 3/4 execute/verify path.

---

### 2026-08-01: V5-C2 real-data success promoted — success conditions and robustness boundary

**Decision**: Promote `V5-C2` (round-0 OSD_0/50-iter with H1, strong
OSD_CS/OSD-2/100-iter H1+H2 fallback, 64-bit Toeplitz verification) as the
main flow for binary LDPC v5 incremental redundancy, and proceed to Phase 3
(fresh synthetic confirmation). The promotion is based on verified real-data
success plus a pre-registered robustness argument.

**Context**: The official package verified 1536/1536 V5-C2 frames
(512/512 in bw120, bw180, bw200; fallback invoked 0/1536; SER quantiles
[0.0352, 0.0742, 0.0898, 0.1133, 0.1328, 0.1602, 0.2148]; runtime ~0.133 s;
h1 584 bits/frame). Robustness validation (`workspace/ldpc_v5_robustness/`):
- E1 seed/root independence: 768/768 verified with a fresh root set.
- E3 model-consistent boundary: 768/768 verified at the model's nominal SER
  0.2430 (adjacent +/-1 injected at the frozen calibration probabilities
  plus_one 3865/16384, minus_one 116/16384) — the decoder prior
  (`v5_plane_error_channel` hardcodes `adjacent_nominal`) exactly matches the
  injected distribution there.
- E2 out-of-distribution control: 0/1152 with uniform random symbol
  replacement (structure mismatch vs the +/-1 model) — expected and
  diagnostic, proving the error_channel prior is load-bearing.

**Success-condition analysis**: `plane_error_channel` is Bob-conditioned
(per-position error probability from the frozen calibration table only; it
never sees Alice). Correct decoding therefore requires the real noise to be
adjacent-bin +/-1 errors at rates at or below the frozen nominal table
(SER 0.243). Real frames satisfy this (max SER 0.215 < 0.243), so round-0
corrects everything and the strong fallback never fires. Failure is only
possible under out-of-distribution noise.

**Alternatives considered**:
- Keep C0/C1 as live candidates: rejected; they are intentionally inactive
  controls, not competing decoders.
- Require synthetic confirmation before promotion: deferred; the official
  package itself already gates `ready_for_synthetic_prepare=true`, and Phase 3
  remains the next mandatory gate before sealed real qualification.

**Consequences**:
- V5-C2 is the main v5 flow; Phase 3 synthetic package must still meet
  126/128 nominal and stress with zero forbidden failures before Phase 4.
- The robustness harness (`run_robustness.py`) is retained as reusable
  evidence infrastructure; results in
  `workspace/ldpc_v5_robustness/results.json` (E1/E2) and `results_e1e2.json`
  plus E3 in `results.json`.
- Any future SER-beyond-model evidence must be generated model-consistently
  (adjacent +/-1 at known probabilities); uniform-noise injections are
  recorded as OOD controls, not capability boundaries.

---

### 2026-08-01: Retain nonbinary LDPC v5c Route C synthetic non-promotion

**Decision**: Retain the sole completed v5c decoder-family package at
`comparison_bench/outputs_comparison/formal_ir_methods/20260731_v5c_nbldpc_decoder_synthetic`
as immutable non-promotion evidence. Do not rerun or tune confirmation.
Continue to Route D (task 7.1) as pre-registered.

**Context**: The frozen plan (NBLDPC5B codebook identity fixed at plan freeze
because Route B ran and is non-promoted; dual policies `nbldpc_v5c_sched`
damped FFT-QSPA lambda 0.5/0.75/0.9 per 4-iteration quartile and
`nbldpc_v5c_ems` LLR min-sum nm=64 alpha=0.8; roots 202607800000-
202607830000; 128 frames, 640 development Toeplitz seeds) executed once with
`run_status=completed`. Readiness passed (both strata >= 63/64) and
confirmation material was atomically materialized and executed. Promotion
gates: p=.20 stratum 128/128, p=.30 stratum 127/128 (one retained tail
miss), so `promoted=false` against the frozen 128/128 floor in both strata.
Prohibited failures were zero.

The pre-registered strict read-only replay completed once and returned
`{'verified': True, 'run_status': 'completed', 'promoted': False}`; the
repository worktree status was unchanged by the replay.

**Alternatives considered**:
- Promote on 127/128 in the p=.30 tail: rejected; the frozen floor is 128/128
  in both strata and no-rerun/no-tuning rules remain intact.
- Tune the decoder policies against confirmation outcomes: rejected;
  confirmation is frozen evidence, not tuning data.
- Treat the result as codebook or decoder failure: rejected; it is failure of
  the promotion floor in the p=.30 tail only, the same pattern as v5a and v5b.

**Consequences**:
- The eight-artifact package is immutable; no rerun or confirmation tuning is
  authorized (no-rerun/no-tuning rules intact).
- Route D (`20260731_v5d_nbldpc_post_synthetic`, roots 202607840000-
  202607870000) is next; the pre-registered list-stage + ADMM post stage is
  the remaining lever after codebook redesign (v5b) and decoder-family change
  (v5c) both left the p=.30 tail open.
- The replay succeeded in this window; the strict replay remains an
  at-most-once action.

---

### 2026-08-02: Retain nonbinary LDPC v5d Route D synthetic non-promotion; v5 change terminates

**Decision**: Retain the sole completed v5d post-processing package at
`comparison_bench/outputs_comparison/formal_ir_methods/20260731_v5d_nbldpc_post_synthetic`
as immutable non-promotion evidence. Do not rerun or tune. Per the frozen
rule (task 7.4), with all four routes non-promoted the v5 multistage change
terminates with four immutable non-promoted packages; N4, sidecars,
`.ttbin`, real-data, and comparison claims remain locked.

**Context**: The frozen plan (run ID `20260731_v5d_nbldpc_post_synthetic`,
NBLDPC5B codebook via v5c delegation, dual policies
`nbldpc_v5d_sched_post`/`nbldpc_v5d_ems_post`, roots 202607840000-
202607870000, 128 frames, 640 development Toeplitz seeds, caps and gates
unchanged from the shared v5 contract) executed once with
`run_status=completed` and readiness true; confirmation material was
atomically materialized and executed. Promotion gates: p=.20 128/128,
p=.30 127/128 (one retained confirmation-frame `decode_failed`),
prohibited failures zero, so `promoted=false`. The pre-registered strict
read-only replay completed once and returned
`{'verified': True, 'run_status': 'completed', 'promoted': False}` with an
unchanged worktree.

Implementation corrections were approved and recorded during D1/D2
(module docstring + Verification Notes): the frozen x-update prior-term
sign was wrong (`+ prior/RHO`; correct proximal is `x = z - lambda -
prior/rho`) — a q=4 brute-force experiment showed codeword recovery jump
from ~0% to 87-100% after the fix; and the frozen z-update alternating
projection onto `{per-variable simplex AND output-sum = e_s}` is a strict
subset of the GF(q) check polytope and could not recover codewords — it
was replaced by the per-bit parity-relaxation projection (bitwise-XOR
linearization), which reached 100% exact recovery in the same experiment
(clean and noisy beliefs). A procedural deviation was also recorded: the
7.3 plan was created before the D1/D2 acceptance evidence file; it was
closed read-only at the same HEAD with the plan unchanged.

**Alternatives considered**:
- Promote on 127/128 in the p=.30 tail: rejected; the frozen floor is
  128/128 in both strata and no-rerun/no-tuning rules remain intact.
- Continue Route D tuning (larger list, more ADMM iterations): rejected;
  the list and ADMM bounds are frozen and confirmation is sealed evidence.
- Extend the change with a fifth route: rejected; the pre-registered
  stop rule terminates at four non-promoted routes.

**Consequences**:
- The eight-artifact package is immutable; no rerun or confirmation tuning
  is authorized.
- The v5 multistage change terminates: Routes A, B, C, D are all
  non-promoted with the same p=.30 tail pattern (127/128). Neither codebook
  redesign (B), decoder-family change (C), nor list/ADMM post-processing
  (D) closed the p=.30 tail at the 128/128 floor.
- N4, sidecar access, `.ttbin` processing, real-data qualification, and any
  comparison claim remain locked; a successor requires a new OpenSpec
  change with fresh development and confirmation data.
- The strict replay remains an at-most-once action; any later replay
  requires a matching-HEAD window.

---

### 2026-08-02: Nonbinary v7 R1A canary non-promotion → R1B

**Decision**: R1A (GF(1024) n=256 (2,3) mother, m=170, flooding FFT-QSPA
primary, max_iter 100) sacrificed canary achieved 0/4 verified success in
both strata (8/8 decode_failed at 100 iterations, zero forbidden statuses);
the pre-registered ladder gate fires failed_canary; R1A package frozen
immutably at the workspace canary dir; no rerun/tuning; R1B (one
multiplicative repetition, rate 1/6) is the authorized next route;
development-ready definition (>=15/16 per stratum, zero forbidden, strict
replay, disclosure <=8.75 bits/symbol excluding tag, median <=120 s/frame)
unchanged.

---

### 2026-08-02: Nonbinary v7 R1B canary non-promotion → R2

**Decision**: R1B (one multiplicative repetition of the (2,3) R1A mother,
rate 1/6 nominal, identity nbldpc_formal_v7_r1b_mr1) sacrificed canary
achieved p=.20 3/4 and p=.30 0/4 verified success (5 decode_failed at 100
iterations, zero forbidden statuses); multiplicative repetition improved
p=.20 (vs R1A 0/4) but did not close the p=.30 tail; the pre-registered
ladder gate fires failed_canary (any stratum 0/4); R1B package frozen
immutably; no rerun/tuning; R2 (QSC density-evolution ensemble) is the
authorized next route with its scientific identity requirement (DE must be
independently validated or the route stops implementation_blocked).

---

### 2026-08-02: Nonbinary v7 R2 canary non-promotion → R3

**Decision**: R2 (QSC density-evolution ensemble, identity
nbldpc_formal_v7_r2_qsc_de, DE validated against published BSC/BEC vectors,
per-stratum n=1024 codebooks with 321/458 checks) sacrificed canary achieved
0/4 verified success in both strata (8/8 decode_failed at 100 iterations,
zero forbidden statuses, execute ~21.9 min); the pre-registered ladder gate
fires failed_canary; R2 package frozen immutably at the workspace canary
dir; no rerun/tuning; R3 (GF(32)xGF(32) nonbinary multilevel, EMS nm=32
primary) is the final authorized route; if R3 also fails, the ladder closes
with a non-ready report (V7-40..42).

### 2026-08-02: Nonbinary v7 R3 engineering interrupted — resume state frozen

**Decision**: R3 engineering (identity nbldpc_formal_v7_r3_gf32x2,
reversible 10-bit → high/low 5-bit split, two GF(32) n=1024 codes,
layer-0-first, EMS nm=32 primary, max_iter 100) is PARTIAL on disk:
`formal_ir/nonbinary_v7_r3_codebook.py`, `nonbinary_v7_r3_long.py`, R3
CANARY/DEVELOPMENT configs in `nonbinary_v7_development.py`
(CANARY_R3/DEVELOPMENT_R3), and `tests/test_nonbinary_v7_r3_codebook.py`
exist; missing `tests/test_nonbinary_v7_r3_long.py`, additive harness tests,
T0-T3 runs, and `evidence/v7_r3_engineering_acceptance.json`. The Task tool
intermittently returned empty results or cancelled sessions (memory triage,
coder-fast runs, reviewer-go returns); every completed stage was verified on
disk before acceptance and fresh-session retries succeeded for R1A/R1B/R2.
No R3 plan/execution/official output exists; resume from the frozen partial
inventory (handoff: AGENT_HANDOFF.md current-state section; memory:
AGENT_PROJECT_MEMORY.md §35), then run the R3 canary gate and ladder
closeout (V7-40..42).

---

### 2026-08-04: Nonbinary v7 R3 canary non-promotion — ladder exhausted, closeout

**Decision**: R3 (identity nbldpc_formal_v7_r3_gf32x2, GF(32)xGF(32) two-layer
EMS nm=32 exact min-sum, reversible 10-bit split, layer-0-first conditional
layer-1 priors, m0=m1=404/558, disclosure 4040/5580 bits excluding tag,
3.945/5.449 bits/symbol) engineering was accepted (T0 19/T1 105/T2 33/T3 179,
10/10 independent review PASS); its sacrificed 4+4 canary was staged and
reviewed READY-FOR-SINGLE-EXECUTION, a minimal canary-only authorization edit
was applied, and the canary executed exactly once (exit 0, 668.8 s) and
strict-replayed exactly once (exit 0, 663.4 s) with per-stratum verified
success {0.20: 0, 0.30: 0} (8/8 decode_failed at max_iter=100, layer-0 failed
on every frame, zero forbidden statuses, verification never invoked). The
pre-registered canary gate fires -> failed_canary; R3 package frozen
immutably; no rerun/tuning/confirmation/real data; no official root created.
With R1A, R1B, R2, and R3 all `failed_canary`, no route reached
development-ready: **ladder_exhausted** (report
evidence/v7_ladder_report.md, V7-40 complete). No fourth route is invented;
any successor requires a NEW OpenSpec change with fresh development and
confirmation data, new roots, and its code/rate/decoder change frozen before
new development data; current confirmation rows are not tuning data.
Qualification/promotion/comparison claims remain unauthorized (V7-41/42
pending).

---

### 2026-08-04: Nonbinary V8 starts with reference reproduction, not another canary

**Decision**: Open change
`formal-nonbinary-ldpc-v8-reference-reproduction`. Preserve V7 evidence and
its `ladder_exhausted` result, while narrowing its scientific interpretation:
V7 T0-T3 engineering passed; its route canaries failed. R1B is retained only
as an algorithmic diagnostic because it synthesizes an additional independent
Alice-derived observation outside the project's single-Bob-observation IR
contract. R2's 0/8 applies to its scalar two-level DE surrogate, not to the
paper's full-vector q-ary density evolution. V8 shall implement error-domain
syndrome equivalence, an independent probability-domain oracle, full-vector
QSC MC-DE with edge-perspective degrees and channel terms, and one precisely
sourced published q-ary reproduction. V8 is engineering/reference-only: no
canary, development, confirmation, real/N4/comparison execution or official
output. A separate V9 may be proposed only after V8 acceptance.

---

### 2026-08-04: Nonbinary V8 reference reproduction complete and independently accepted

**Decision**: Accept `formal-nonbinary-ldpc-v8-reference-reproduction` as
implemented and INDEPENDENTLY REVIEWED ACCEPTED (reviewer-go, read-only,
2026-08-04, HEAD `a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344`). V8-A01..V8-A11
pass; V8-A12 is satisfied by the independent review (the operator did not
self-accept). V8 is engineering/reference-only: it authorizes no FER,
readiness, qualification, promotion, or comparison claim; only a separate V9
proposal follows.

**Context**:
- Additive files only (3 modules + 3 tests + 7 evidence files under
  `openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/evidence/`):
  `nonbinary_v8_error_domain.py` (error-domain contract d = H*(x+y),
  reconstruction x_hat = y + e_hat, pure field-tables-only helpers);
  `nonbinary_v8_reference.py` (independent direct probability-domain oracle:
  pairwise XOR convolution + sparse support enumeration + brute-force tiny-code
  coset/MAP, imports only GF2mField, import-boundary test enforced);
  `nonbinary_v8_mcde.py` (full-vector QSC Monte-Carlo density evolution:
  length-q messages, edge-perspective degree distributions with tested
  node/edge conversion, exact sampled degrees, fresh channel message at every
  variable update, direct convolution without FWHT, base-q mean entropy
  convergence, seeded deterministic, fail-closed; golden regressions detect
  old R2 missing-channel and fixed-`dv_max` behavior).
- Tiers (`pytest -q -p no:cacheprovider`, fresh
  `workspace/nbldpc_v8_reference_9c3f51e2a74b48d9b6c0a5f8e1d23a4b` root):
  T0 11/0, T1 31/0, T2 3/0 (read-only reproduction-trace + source-manifest +
  no-production-runner verification), T3 179/0 (frozen 16-file
  v5+v6+v7-R1A/R1B/R2 regression subset, exact frozen file list). The reviewer
  re-ran T0/T1/T2: identical.
- Published reproduction (single frozen run, no rerun/tuning): Muller et al.,
  "Efficient Information Reconciliation for High-Dimensional Quantum Key
  Distribution", Quantum Inf Process 23, 195 (2024), arXiv:2307.02225v2,
  Section 3.1 Table 1 row "0.75": q=4, rate 0.75, DET 0.069, EEff 1.053,
  edge-view lambda with coefficients
  `0.107x+0.245x^3+0.192x^6+0.034x^9+0.207x^18+0.161x^25+0.049x^27`
  (paper Eq. 13: exponents are degree-1, so DE degrees {2,4,7,10,19,26,28});
  concentrated two-point check distribution inferred from the fixed rate:
  dc_mean = 1/((1-R)*sum(lambda_d/d)) = 24.3285893 -> {24,25} (documented
  inference; provenance record `evidence/v8_literature_provenance.json`;
  verbatim extract `evidence/v8_muller2024_table1_extract.txt` SHA256
  `d343f0204e87994e64efd32531bc12490fb4e7125cd90b52cfaf2397279b57bd`). Frozen
  params: seed 2026080418, 20000 nodes, max 200 iterations, entropy
  convergence < 0.01 base-q for 20 consecutive iterations, binary search p in
  [0.01, 0.12] step 0.0025, frozen tolerance 0.015. Result:
  threshold_proxy 0.062421875, delta vs 0.069 = 0.006578 <= 0.015 -> PASS;
  full probe trace in `evidence/v8_reproduction_trace.json`.
- Output policy: no V8 directory under
  `comparison_bench/outputs_comparison/formal_ir_methods/`; no
  canary/development/confirmation/real-data/N4/comparison execution; frozen
  `src/`/`experiments/`/`tools/`/`results/` and all V1-V7 files unchanged
  (git status/diff empty); nothing staged.
- Evidence: `evidence/v8_engineering_acceptance.json` (schema
  v8_engineering_v1; source manifest with SHA256 of the 6 additive files;
  pre-test manifest `evidence/v8_source_manifest.json` re-verified read-only;
  one recorded manifest delta for a test-file assertion addition, all tiers
  re-verified); `evidence/v8_v7_interpretation_audit.md` (R1B =
  out-of-contract extra-observation diagnostic; R2 = unvalidated scalar-DE
  surrogate result; V7 T0-T3 engineering PASS distinct from canary failures);
  `evidence/v8_v9_recommendation.md` (V9 lead: paper-faithful syndrome
  reconciliation with a reproduced ensemble and blind puncturing/shortening,
  fresh roots, separate OpenSpec change; NOT implemented).

**Consequences**:
- V8 is closed; nothing remains for V8 except a future separate V9 proposal.
- No FER, readiness, qualification, promotion, or comparison claim is made
  from V8.

---

### 2026-08-04: Nonbinary V8-60 audit-correction close-out

**Decision**: Record V8-60 as a **non-tuning formula correction** discovered by
an independent audit of the accepted V8 candidate: (a) `concentrated_check_distribution`
previously matched the two-point MEAN check degree (`w_lo = dc_hi - dc_mean`),
which only approximates the edge-perspective rate condition
`sum_j rho_j/j = (1-R)*sum_i lambda_i/i` (relative error ~1e-4); corrected to
solve it exactly for adjacent check degrees `{floor(dc), ceil(dc)}` with
`w_lo = (target - 1/d_hi)/(1/d_lo - 1/d_hi)`, `w_hi = 1 - w_lo`,
`target = (1-R)*integral_lambda`, `dc = 1/target` (integer `dc` degenerates to
the regular degree); new public helper
`reconstructed_rate(lambda_edge, rho_edge) = 1 - (sum rho_j/j)/(sum lambda_i/i)`;
tests assert `|reconstructed_rate - rate| <= 1e-12` (5 configs). (b) The
`REPRODUCTION_CITATION` first author was corrected from the wrong given name
"Rasmus T. Müller" to "Ronny Müller" (full arXiv:2307.02225v2 author list).
(c) The frozen tolerance justification `0.005+0.003+0.0025=0.015` was
arithmetically invalid; replaced by `0.0005` (3-decimal published rounding) +
`0.00125` (p_tol/2) + `0.005` (our MC-DE finite-sample error at 100000 nodes)
+ `0.005` (paper MC-DE error at its 100000 nodes) = `0.01175 <= 0.012`; frozen
tolerance 0.012.

**Context**:
- Corrective reference run (exactly once, parameters frozen BEFORE the run):
  q=4, R=0.75, Muller et al. 2024 Table 1 row 0.75 (DET published 0.069),
  concentrated rho `{24: 0.6623423944, 25: 0.3376576056}` (dc_mean 24.3285893
  unchanged), n_samples 100000 and max_iter 150 (the paper's own MC-DE budget),
  seed 2026080418, p in [0.01,0.12] step 0.0025, entropy < 0.01 base-q for 20
  consecutive iterations. Result: threshold_proxy 0.062421875, delta
  0.006578125 <= 0.012 -> PASS; full probe trace in
  `evidence/v8_reproduction_trace_corrected.json`. No rerun, no tuning.
- History preservation: `evidence/v8_reproduction_trace.json` preserved
  byte-identical (SHA256
  `dd5678fd2d77b67dd7f3fc7ee221a49b0d33eab37ab5d226d96e6d243b071de3`) and
  marked as the pre-correction approximate trace via
  `evidence/v8_reproduction_trace_precorrection_annotation.json`;
  `evidence/v8_engineering_acceptance.json` NOT rewritten (its A12=blocked
  status is explicitly resolved by the new
  `evidence/v8_acceptance_closeout_addendum.json`, main-thread V8-60.10);
  `v8_literature_provenance.json`, `v8_muller2024_table1_extract.txt`,
  `v8_v7_interpretation_audit.md`, `v8_v9_recommendation.md` unchanged.
- Golden regressions: q=4 golden re-recorded under the corrected rho
  `{4: 1/6, 5: 5/6}` (same seed/config; recording not tuning);
  omitted-channel and fixed_max tamper modes still differ (old-R2 detection
  preserved); q=8 golden byte-identical (regular `{6:1.0}`).
- Tiers (V8-60.8 scope, no T3): compile exit 0; T0 17 passed / 0 failed;
  T1 32 passed / 0 failed; T2 4 passed / 0 failed (reproduction-trace +
  source-manifest + no-production-runner + precorrection-preservation, all
  read-only). Independent reviewer-go re-ran T1 32/0 and T2 4/0: identical.
- Independent review (V8-60.9): reviewer-go ACCEPTED the corrected candidate;
  `evidence/v8_independent_review_acceptance.json` written (review scope,
  re-run commands/results, source hashes, V8-A01..A12 conclusions; A12
  resolved pass by this review). Blocking findings: none. Non-blocking:
  `v8_v9_recommendation.md` cites pre-correction run numbers (direction
  unaffected; corrected numbers supersede); cosmetic duplicated REPO_ROOT
  line; pre-existing package `__init__` binding (test scopes correctly).
- Evidence inventory (new in V8-60): `v8_reproduction_trace_corrected.json`,
  `v8_reproduction_trace_precorrection_annotation.json`,
  `v8_60_correction_evidence.json` (formula/constants old->new, tolerance
  arithmetic, source-hash old->new; only `nonbinary_v8_mcde.py` and
  `test_nonbinary_v8_mcde.py` changed: new hashes
  `2c84a5ee76d09f4d6cea537289ff82d88ab19abd31d1a41951a7d24acdd66543` /
  `a508a4228ee06114424db2242b4db784bfa1b9cabcbae54f4cd7172ed988a81f`),
  `v8_independent_review_acceptance.json`, `v8_acceptance_closeout_addendum.json`;
  `v8_source_manifest.json` regenerated with a `v8_60_delta` field (old hashes
  remain in the original acceptance).

**Consequences**:
- V8-60.9 and V8-60.10 are complete; V8-60.11 remains open until the memory
  agent writes AGENT_PROJECT_MEMORY.md section 39.
- The corrected formula, citation, and tolerance supersede the pre-correction
  records; the original evidence remains byte-identical.
- V8 remains engineering/reference-only; no V9 implementation, no
  canary/development/confirmation/real-data/N4, no official output, no
  staging/committing/pushing; only a separate future V9 OpenSpec proposal is
  authorized.
- Nothing remains for V8; the pre-correction evidence stays byte-identical and
  the corrected numbers supersede it.

---

### 2026-08-04: Authorize gated V9 GF(1024) ensemble-to-long-block route

**Decision**: Create OpenSpec change
`formal-nonbinary-ldpc-v9-gf1024-long-ir` and authorize its frozen state
machine V9A -> V9B -> V9C. V9A first validates scalable full-vector GF(1024)
MC-DE and separate p=.20/.30 robust f=1.15 and target f=1.08 ensembles. Robust
multi-seed thresholds must reach .22/.32 before a finite codebook exists.
Passing stages may advance autonomously to n=4096, n=16384, and n=32768
synthetic canary/development; any failed gate freezes evidence and stops.

V8 q=4 validates method/audit machinery only, not GF(1024) threshold or FER.
V9C stops after the n=32768 16+16 development decision. Qualification,
confirmation, real/N4, promotion, and formal comparison remain unauthorized.
Full formulas, resource gates, lifecycle rules, and acceptance IDs V9-A01..
V9-A16 are frozen in the new change and `docs/nonbinary-ldpc-v9-plan.md`.

**Specification correction after independent freeze review**: V9A robust
candidates use conservative .22/.32 gates; target uses .215/.32 (.215 remains
below the p=.20 f=1.08 capacity threshold ~.21827). All four searches
plus multi-seed validation form one reviewed, once-executed, once-replayed
package. n=4096/16384/32768 bind 4/16/32 disjoint constituents respectively;
all finite matrices require `rank(H)=m`. n=32768 canary uses hard 24h timeout
and median <=16h. V9C uses fixed rates only: `m=ceil(f*H_q(p)*n)`, syndrome
`L_recon=10*m`, separate 64-bit tag, `L_total=10*m+64`, with no other
reconciliation payload. Blind adaptation is prohibited in V9 and deferred to
V10.

### 2026-08-04: V9A ensemble gate fails — frozen STOP before codebooks

**Decision**: V9A stops at the ensemble gate. No finite codebook, decoder,
canary, development run, qualification, real/N4 data, promotion, or formal
comparison will be produced under `formal-nonbinary-ldpc-v9-gf1024-long-ir`.

**Context**: V9A executed exactly once under the v2 budget protocol (pid 5084,
3968.5 s, peak RSS 428.3 MiB) and was strict-replayed exactly once (pid 29340,
4838.5 s, peak RSS 451.5 MiB). Scientific outputs are deterministic and
byte-identical between execute and replay; only `run_meta.json` differs in
provenance fields. All four searches (S1 robust p=.20 f=1.15 gate .22; S2
target p=.20 f=1.08 gate .215; S3 robust p=.30 f=1.15 gate .32; S4 target
p=.30 f=1.08 gate .32) recorded zero eligible candidates: every one of the
32 candidate screens at the gate p failed to converge in 150 iterations (final
entropy 0.66-0.93, final error 0.08-0.31). The conservative threshold is
undefined for every gate.

Capacity context (informational only): S1 p*=0.2345, S2 p*=0.2183, S3
p*=0.3527, S4 p*=0.3279. The gates sit below capacity, but the frozen
8-candidate population of 3-term lambda mixtures with harmonic-exact
concentrated rho did not approach it.

**Alternatives considered**:
- Tune the candidate population or expand the search budget: rejected because
  the plan was frozen before any result and a failed execute is immutable.
- Lower the robust gate to match the observed proxies (~0.19-0.20 for S1):
  rejected because that would redefine the frozen gate after seeing the result.
- Advance to V9B anyway with the best non-eligible candidate: rejected because
  the plan requires an eligible/searched winner with a conservative threshold
  before any finite codebook exists.

**Consequences**:
- Evidence is frozen under
  `openspec/changes/formal-nonbinary-ldpc-v9-gf1024-long-ir/evidence/`.
- The replay script's missing guard on the shared
  `evidence/v9a_execute_results.json` path caused an overwrite; the original
  execute version was restored from `v2_execute/evidence_v9a_execute_results.json`.
- V9B/V9C are unreachable. A successor nonbinary LDPC lane would require a new
  OpenSpec change with fresh roots, a different ensemble family, and new
  development/confirmation data.

### 2026-08-05: V9A acceptance and archive complete

**Decision**: The V9A package passed independent review and the change
`formal-nonbinary-ldpc-v9-gf1024-long-ir` was archived (STOP at the ensemble
gate).

**Context**: reviewer-go accepted the V9A evidence package read-only (all
checklist items pass, no blocking issues). Independent SHA256 verification
confirmed 9/11 execute/replay files byte-identical; the 2 differing files
(`evidence_v9a_execute_results.json`, `run_meta.json`) differ only in
provenance fields (pid/start/end/elapsed/peak_rss/command). The official
execute evidence hash matches the v2_execute copy
(`540295123a8a19f3f335f727339df14f4c1106fc01cccab46ecb644dd1eedb8c`).
Acceptance record: `evidence/v9a_independent_review_acceptance.json`.

The generic openspec archive CLI rejected the change (its `verifyChange`
requires numeric `- [ ] 1.1` task IDs and all tasks checked; this project uses
custom `- [x] **V9-XX.Y**` task IDs and V9-30..V9-70 are legitimately
unchecked as unreachable after the frozen STOP). The archive was therefore
performed as the CLI's underlying operation — a dated directory move — exactly
as prior project archives were done.

**Alternatives considered**:
- Rewrite tasks.md to the CLI's numeric format and check all boxes: rejected
  because it would falsify the record (V9B/V9C tasks were never done).
- Run the CLI anyway: rejected because `verifyChange` hard-fails on the
  custom task format and on any pending task.

**Consequences**:
- Change moved to
  `openspec/changes/archive/2026-08-05-formal-nonbinary-ldpc-v9-gf1024-long-ir/`
  (all 6 artifacts: proposal, design, tasks, specs, packet, evidence).
- Delta spec NOT synced into `openspec/specs/` (per user choice: the
  unattained V9B/V9C requirements must not become canonical spec).
- No V9B/V9C artifacts exist; no scientific command was executed during
  close-out or archive.
- Successor nonbinary LDPC work requires a new OpenSpec change with fresh
  roots, a different ensemble family, and new development/confirmation data.

---

### 2026-08-06: Nonbinary V10 fails at the ensemble gate — failed_ensemble, V11 successor

**Decision**: Terminate `formal-nonbinary-ldpc-v10-de-peg-fftqspa` with final
state `failed_ensemble` (`evidence/v10_gate_decision.json`, schema
`v10_gate_decision_v1`). V10A GF(1024) four-search density-evolution ensemble
gate failed (hard stop V10-S02); V10-30 (PEG), V10-40 (FFT-QSPA), V10-50
(canary), and V10-60 (development) are all HALTED. There is no "closest to
gate" candidate, no rerun, and no tuning. The successor is a brand-new V11
NB-SC-LDPC OpenSpec change (fresh everything: new change, new roots, new
development/confirmation data).

**Context**:
- V10-0 q=4 reference-recovery gate PASS: conservative threshold 0.06414,
  |δ| = |0.06414 − 0.069| = 0.00486 ≤ 0.012; main-thread accepted
  2026-08-05.
- V10A searches: S1 (p=.20, f=1.15) conservative 0.2153 < 0.22 FAIL; S2
  (p=.20, f=1.08) conservative 0.1984 < 0.215 FAIL; S3 (p=.30, f=1.15)
  conservative 0.3166 < 0.32 FAIL; S4 (p=.30, f=1.08) no eligible candidate
  FAIL. Triggered hard stop V10-S02.
- Execution record: V10A executed once (~10470 s, peak RSS 335 MB < 3 GiB);
  the first replay attempt was interrupted (PID 21032 died after S1 only);
  per precedent, the replay was rerun in `replay_attempt2/` and completed
  (04:36–07:07Z, RSS 339 MB). Direct byte comparison PASS across 129 files:
  scientific files byte-identical; only provenance normalization differs
  (plan_binding digest key and run_complete role/stage).
- 2026-08-06 protocol amendment (main-thread directive): per AGENTS.md §5.7,
  defensive SHA-256/checksum/integrity-manifest mechanisms were removed
  (plan-bound digest, manifest self/source hash, per-file compare sha256,
  etc.); replacements are git baseline checks, direct byte comparison,
  structured field validation, and semantic recomputation. `v10_seed` is
  retained as a deterministic RNG derivation primitive (DE population
  initialization and mutation RNG streams depend on it; completed results
  depend on its byte reproduction). Amendment record:
  `evidence/v10_protocol_amendment_no_hash_v1.json`.
- Evidence files (change `evidence/`): `v10a_execute_results.json`,
  `v10a_replay_evidence.json`, `v10a_gate_decision.json`,
  `v10_gate_decision.json`, `v10_t3_regression.json` (git baseline PASS,
  frozen directories zero change), `v10_protocol_amendment_no_hash_v1.json`.
- Tests: full V10 suite 89 passed (common 23 / de 24 / gate 13 / peg 12 /
  fftqspa 17).
- Frozen baseline: git HEAD
  `a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344`; `src/`, `experiments/`,
  `tools/`, `results/` zero change; no new output under
  `comparison_bench/outputs_comparison/formal_ir_methods/`; the 12 tracked
  modifications are pre-existing dirty-worktree entries of other workflows.
- V10-30.DESIGN task (PEG no-hash design note) remains unchecked and is left
  for future V11 inheritance.

**Alternatives considered**:
- Report a "closest to gate" candidate: rejected — the gates are
  pre-registered absolute thresholds; no candidate reached them, and naming a
  closest value would imply partial success or tunability.
- Rerun or tune (expand search budget, adjust population): rejected — the
  failed execution is immutable and no-rerun/no-tuning rules remain intact.
- Advance to V10-30 with the best non-eligible candidate: rejected — the
  hard stop V10-S02 requires all gates to pass before any finite codebook.

**Consequences**:
- V10 terminates at `failed_ensemble`; no codebook, decoder, canary,
  development, qualification, real-data, promotion, or comparison output was
  produced under this change.
- The successor is a new V11 NB-SC-LDPC OpenSpec change with fresh roots,
  fresh development/confirmation data, and its code/rate/decoder change
  frozen before new data; starting V11 is a user decision.
- `v10_seed` remains a deterministic RNG primitive; the other defensive hash
  mechanisms were removed per the 2026-08-06 amendment and must not be
  re-added to new evidence without a new decision.
- V10-30.DESIGN (PEG no-hash design note) is inherited by V11, unchecked.
- S4 delta correction (2026-08-06): `evidence/v10_s4_delta_correction.json`
  (schema `v10_s4_delta_correction_v1`) records that the S4 `delta` field in
  `evidence/v10a_gate_decision.json` was a boolean false from the
  build_evidence short-circuit bug; correct semantics is null. The evidence
  file was not overwritten; the script expression was fixed for future reuse.
  The S4 FAIL verdict and the `failed_ensemble` conclusion are unaffected.
- Independent final review (2026-08-06): reviewer-go ACCEPT recorded in
  `evidence/v10_independent_review_acceptance.json` (schema
  `v10_independent_review_acceptance_v1`; 89 tests pass, covering the S4
  correction record).

---

### 2026-08-06: Freeze V11 as a spatially coupled DE-only successor

**Decision**: Create `formal-nonbinary-ldpc-v11-sc-de-gate` as a plan-only
OpenSpec change. V11 first reproduces published q=4/q=16 QSC coupled and
uncoupled SMP thresholds, then validates a separate full-vector coupled MC-DE,
and finally tests the frozen V10 robust S1/S3 ensembles under equal effective
rate. The only formal geometries are G1 `(w=1,L=32,W=8)`, G2
`(w=2,L=32,W=16)`, and G3 `(w=2,L=32,W=32)`.

**Rationale**: The direct QSC literature supports a spatial-coupling gain but
uses simplified symbol-message passing; BEC/AWGN threshold-saturation results
do not by themselves validate GF(1024) HD-QKD full-vector behavior. A dual
reference gate prevents those claims from being conflated. Equal-rate
termination compensation and paired uncoupled controls isolate coupling from
extra leakage.

**Consequences**:
- Passing requires conservative S1/S3 thresholds of .22/.32 and at least .002
  paired gain in both strata.
- Reference mismatch, resource excess, or no passing geometry stops as
  `failed_reference`, `resource_blocked`, or `failed_coupling` respectively.
- V11 stops at `ready_for_finite_length`; it cannot construct a finite code,
  run FFT-QSPA/canary/real data, or make qualification/promotion claims.
- V11-P04 independent freeze review is required before implementation or any
  scientific execution.

---

### 2026-08-12: Binary LDPC v5 sealed real qualification promoted on real 10 dB ttbin

**Decision**: Accept the sealed real qualification of binary LDPC v5 on the
independent 10 dB Type-II capture: 384/384 verified successes (bw120, bw180,
and bw200 each 128/128) with zero forbidden failures and `promoted=true`.
This is the first real-data promotion for binary LDPC.

**Context**: The full pre-registered chain completed, each stage exactly once
with read-only verification: 20260731 partition lock → 20260731 v5
development (V5-C2, 1536/1536) → 20260801 v5 synthetic (256/256, promoted) →
20260801_v2 real (384/384, promoted). The official ten-file package is
`comparison_bench/outputs_comparison/formal_ir_methods/20260801_v2_binary_ldpc_v5_real/`
(run_id `binary_ldpc_v5_real_qualification_v1`, plan_sha256
`a79cd16f19b968364a4c46fb4887f933eeb472e45c19d098a938ae5dc58ad01b`, report
sha256 `18b5566ed636a79473ff7290cb55d90d4ab20a170895b53f786ea2455ad953d5`).
Report fields: `promoted=true`, `run_status=completed`,
`decoder_reexecution=false`. Execute took ~5m12s and read-only verify ~4m29s,
run in a detached background process on 2026-08-12.

The CSV role uses the frozen encoder's allowed `real` value: the contract's
literal `real_confirmation` is rejected by the encoder, the same precedent as
Phase 3. During implementation, three latent bugs masked by test mocks were
found and fixed (synthetic_dir directory semantics, generator empty-dict
check, missing root_id); the fixes are semantic-preserving and do not change
the scientific result.

**Alternatives considered**:
- None: the qualification is pre-registered and gated; alternatives would
  apply only on a failed gate, which did not occur.

**Consequences**:
- The promotion is limited to the 10 dB Type-II, q=1024, Gray, 256-symbol,
  bw120/bw180/bw200 domain with the V5-C2 strategy. It does not extend to v4,
  the 16 dB/20 dB captures, other acquisitions, nonbinary LDPC, or any
  Cascade/Polar comparison claim.
- v4's two real transfers (16 dB 125/128 and 10 dB v2 125/128, both below the
  126/128 gate) remain retained non-promoted failure evidence; v5 is the
  first all-green real 10 dB Type-II promotion.
- Comparison eligibility is updated: binary LDPC v5 may participate in
  comparison within the promoted 10 dB domain; all other domains and methods
  keep their prior status. Binary/nonbinary parallel status: binary v5
  promoted; the nonbinary lane is unchanged.
- A rate-adaptive successor requires a separate new OpenSpec change.

---

### 2026-08-11: V11 spatial-coupling hypothesis rejected — `failed_coupling`

**Decision**: Terminate `formal-nonbinary-ldpc-v11-sc-de-gate` with final
state `failed_coupling` (`evidence/decision/final_gate_decision.json`, schema
`v11_final_gate_decision_v1`). The V11 spatial-coupling hypothesis is
rejected: none of G1/G2/G3 reached the frozen dual gates (S1 ≥ .22 and S3 ≥
.32), and every paired conservative gain is negative. V11 ends honestly at
`failed_coupling`; no silent promotion is made.

**Context**: Under the frozen V10 S1/S3 lambda distributions and the frozen
G1 `(w=1,L=32,W=8)`, G2 `(w=2,L=32,W=16)`, G3 `(w=2,L=32,W=32)` geometries,
the coupled conservative thresholds were S1 G1 .2100 / G2 .2025 / G3 .2019
(all < .22) and S3 G1 .3125 / G2 .3000 / G3 .3000 (all < .32); paired gains
were all negative (S1 -0.0075 / -0.0144 / -0.0156 and S3 -0.0137 / -0.0256 /
-0.0206). The scientific matrix executed 60/60 runs once (2026-08-08,
execution root `workspace/nbldpc_v11_execute_002d51de/`); the strict replay
was 60/60 byte-identical on science fields from a fresh workspace
(`workspace/nbldpc_v11_replay_8e63bf62/`). Independent final acceptance
(reviewer-go V11-50.3) recomputed 12 conservative aggregates + 6 paired gains
+ 3 gate verdicts, all consistent (16/16 A01-A16 PASS).

**Alternatives considered**:
- Silent promotion or describing a "closest to gate" geometry: rejected —
  the gates are pre-registered absolute thresholds and no silent promotion of
  failures is allowed (design.md §6, A15).
- Retune parameters/ensembles and rerun: rejected — the failed execution is
  immutable and no-rerun/no-tuning rules remain intact.
- Shrink the matrix (drop a geometry/stratum or relax the gates after seeing
  the result): rejected — it would redefine the frozen plan after the result.

**Consequences**:
- V11 stops at `failed_coupling`; the provisional `failed_reference` in the
  execution-root summary was a checks-pending placeholder and is superseded by
  the final decision file.
- No finite code, decoder, canary, development, qualification, promotion, or
  comparison output was produced under this change.
- Finite-length/lifting, windowed FFT-QSPA, decoder, canary, real-data,
  qualification, and promotion work all require a new OpenSpec change with
  fresh roots and fresh development/confirmation data (design.md §6/§8).
- Resource budget (15.83 h < 24 h, peak RSS 2.82 GiB < 3 GiB) and rate
  contract passed; the failure is purely scientific (no threshold gain from
  spatial coupling under the frozen distributions and geometries).

---

### 2026-08-13: V12 nonbinary LDPC real micro-feasibility: source_partition_blocked

**Decision**: V12 terminated with terminal state `source_partition_blocked`. The
four-frame bw200 micro-feasibility canary cannot be executed because the
reconstructed traceable 10 dB pool (2304 rows, 768 per stratum) is 100%
covered by historical frame/payload identities from the V4 10 dB/16 dB
transfer locks (20260729_v1/v2) and V5 development/partition role locks
(20260731_v1): 2848 excluded frame + 2688 excluded payload identities, zero
eligible bw200 rows. Implementation (V12-I01..I05) and engineering acceptance
(V12-T0..T2, 41/41 tests) completed; prepare lane (RP01-RP03) produced the
official package
`comparison_bench/outputs_comparison/formal_ir_methods/20260813_v2_nonbinary_v12_real_micro/`
(v1 intermediate package deleted by explicit user decision). No successor,
rerun, tuning, replacement, or promotion is automatically authorized.

**Context**: V12 asked whether the frozen finite GF(1024) R1 baseline
(unchanged V7 R1A matrix, p=.20 prior, full 170-row syndrome) can produce an
independently verified exact correction on four fresh compatible real frames;
the partition-freeze step found zero collision-free rows in the existing pool.

**Alternatives considered**:
- Reuse historical frames: rejected — cross-history frame/payload exclusion is
  frozen in V12-P05 and design §4.
- Relax the exclusion inventory: rejected — the identities are genuinely
  shared with prior V4/V5 real packages; relaxing would break freshness.
- Fresh acquisition now: deferred — out of V12 scope; requires new capture and
  a new OpenSpec change.

**Consequences**: V12 stands as a documentation + engineering deliverable with
terminal state `source_partition_blocked`; no finite decoder correction was
established for the existing pool; any future canary requires a fresh
acquisition and a new OpenSpec change. Claim boundary: V12 never establishes
success probability, FER, threshold, qualification, or promotion.

---

### 2026-08-14: 先用现有数据诊断非二元 LDPC，不以重新采集为前置

**Decision**: 用户决定先使用现有 10 dB Type-II、q=1024、Gray、256-symbol
数据做非二元 LDPC 的 retrospective diagnostic/development 规划，不把
重新采集设为 V13 的前置条件。V13 change
`formal-nonbinary-ldpc-v13-existing-data-diagnostics` 仅处于
`PLAN DRAFTED / EXECUTION NOT AUTHORIZED`；本轮只请求独立只读 freeze
review，不请求 decoder 或真实数据执行。

**Context**: V12 的 `source_partition_blocked` 是 freshness/identity
partition 失败：已有 10 dB 池中的 768 个 bw200 行均已被 V4/V5 历史
frame/payload identities 覆盖，而不是数据量为零。现有行可用于 channel
统计、接口/数值诊断和事后 exact-correction 检查，但不能被称为 fresh
canary、confirmation、qualification 或 promotion evidence。

**Frozen boundary**: V7 R1A、V10 `failed_ensemble`、V11
`failed_coupling`、V12 `source_partition_blocked` 的含义不改写；binary
V5 同域 384/384 仅作 frame-difficulty/control 参照，不复制其 leakage、
prior 或模型。Alice truth 仅可进入离线 aggregate 与事后 exact check；
公共 telemetry 不保存 raw arrays 或逐位置 error mask。bw200 是 primary，
bw120/bw180 只能在 bw200 根因结论之后做预注册 cross-stratum check。

**Artifact naming**: future diagnostics use the six-file additive package;
`diagnostic_outcomes.csv` contains baseline, candidate-development, and
retrospective-audit rows with explicit `phase` and `method` fields. The
diagnostic CSV name is frozen to `diagnostic_outcomes.csv`.

**Consequences**: P01--P07 只在文档中 drafted，P08 独立 freeze review
尚未完成；所有 D/R/I/E/A/C 均未授权。即使未来诊断全绿，最高状态也
只是 `ready_for_fresh_confirmation`。fresh acquisition、正式
qualification 或 promotion 必须另开 OpenSpec change 并由用户决定；V12
仍保持 `source_partition_blocked`，不重开 X01/X02。

---

### 2026-08-14: V13-D04 baseline probe — 主线程授权、实现并执行一次

**Decision**: 主线程授权执行 V13-D04（unchanged V7 R1A `p=.20` baseline
probe，32 个预注册 bw200 development frames，恰好一次，禁止重试/替换/调
参）。D04 通道实现于 `comparison_bench/`：`run_d04` core lane（含 D04
限定的 manifest authorization、冻结失败包处理）、CLI `d04` action、
只读 verify 扩展、D04-lane 工程测试（DT3，27/27 全绿）。生产执行一次，
run_id `v13_d04_20260814`，六文件包位于
`comparison_bench/outputs_comparison/nonbinary_diagnostics/v13_d04_20260814/`，
严格只读 verify PASS（32 outcome rows、32 telemetry records、ledger ready）。

**Context**: P08 freeze review 已 ACCEPT；DT0-DT2 21/21 通过。D04 结果：
8/32 `syndrome_consistent` + `exact_correct`（全部在第 1 次迭代收敛）、
24/32 `decode_failed` 到 100 次迭代上限、零 `decoder_error`、零
exact_mismatch、零 non-finite/normalisation/underflow 事件。telemetry
观测（经验诊断，非结论）：decode_failed 帧末态后验高度集中（mean
posterior max 0.986、entropy 0.103 bits）但平均 3.79 个 unsatisfied
checks，11/32 帧有振荡迹象。hook 等价性在全部 32 帧保持
（hook_equivalence=ok），V7 R1A 冻结源码字节未改。

**Alternatives considered**: D04 之前是 CLI 硬停止（exit 2）；实现即唯一
路径。输出根写入在沙箱下被拒一次，以 danger-full-access 重试同一命令
成功（用户批准）。

**Consequences**: D04 包 run_state=`plan_only`、`d05_emitted=false`，不产
生任何 diagnosis_class/run_state 结论。D05（根因报告 + 独立复核）仍未
授权、未实现；R/I/E/A/C 全部锁死。8/32 不得被表述为 promotion、
qualification 或 fresh correction。下一授权点是主线程决定是否授权 D05。

---

### 2026-08-14: V13 D01 run 统计 bug 修正 + D04 数据的信道结构观测

**Decision**: 修正 `nonbinary_v13_diagnostics._frame_channel_stats` 的 run
计数 bug（条件表达式在 run-end 检查前把 `run` 清零，导致 D01 记录
`run_count=8` 的伪影）；D01 六文件包保持不可变证据不重写。修正后的同一
128 个 bw200 characterization 帧聚合值记入本条目作为可信参考。

**Corrected aggregates** (read-only recompute, same frames): 2525 个错误符
号；2340 个 run（每帧均值 18.3）；run 长度直方图 {1: 2169, 2: 157, 3: 14}
（最大长度 3）；185 个相邻错误对（7.3% 的错误有相邻错误）——错误是孤立
的单符号扰动，不是突发。**99.3%（2508/2525）的非零 Alice-Bob 差分落在
[0,128)**，与位面失配的 MSB→LSB 单调结构（3.1e-5 → 3.75e-2）一致，并与
binary V5 同域已知的相邻 ±1 符号扰动结构（troubleshooting 中
`plane_error_channel` 的 adjacent_nominal）互证。这些是 D01 邻近的经验观
测，不构成 D05 结论。

**Context**: 主线程层面的 D04 数据预分析（非 D05）：基线双峰行为（8/32
在第 1 次迭代 exact-correct、24/32 迭代上限 decode_failed）、失败帧高置
信错字（posterior max 0.986、entropy 0.103、均值 3.79 unsatisfied
checks、11/32 振荡）与"QSC p=.20 均匀先验严重失配于小差分集中信道"的假
说一致（校准失配 0.1229；模型熵 2.722 vs 经验条件熵 0.547 bits/symbol；
R1A 泄漏 6.64 bits/symbol ≈ 12× 经验下界）。候选排序与文献对照详见本轮
分析答复；正式 diagnosis_class 只能由 D05 发射。

**Consequences**: run 统计 bug 修正只影响未来运行；修正后的聚合值用于
后续文档引用（替代 CURRENT_TASK 中旧 8-run 表述）。信道结构观测不自动
授权 R1 候选——R 阶段仍需 D05 + OpenSpec amendment + 主线程批准。

---

### 2026-08-14: V13-D05 根因报告 — code / diagnosis_complete（含一次无效发射修正）

**Decision**: 主线程按推荐步骤授权 D05 发射。离线 girth 分析显示冻结 V7
R1A 图**结构性退化**：170 个校验节点分成 85 个互不相连的 2-校验组件
（每个组件 3-4 个全 degree-2 变量），check 图 girth=2、Tanner girth=4、
逐组件最小距离 d_min=3。对 32 个 D04 development 帧的结构天花板分析：
structural_failure_fraction=0.75 == 观测失败率 0.75，且**帧级完美对应**
（24/24 失败帧都含 ≥2 错误组件；8/8 exact-correct 帧都不含）。D05 发射
`diagnosis_class=code`、`run_state=diagnosis_complete`、后继 **R3
code-only**；QSC p=.20 先验失配（校准失配 0.1229、|熵差| 2.17 bits）作为
已记录的 co-factor（其不解释观测失败——结构单独解释 100% 失败）。

**Correction**: 首次发射 `v13_d05_20260814` 因决策机制缺陷被判
inconclusive（ceiling 文档缺 observed 分数→默认 1.0；entropy gap 为负而
阈值用了带符号值），按 V8-60 先例：保留原包不可变 + 同级
`v13_d05_20260814_invalid_execution_notice.json` 记录 + 修正后以新 run id
`v13_d05_20260814_corrected` 加法重发一次（决策函数为纯函数，证据字段原
样保留）。严格只读 verifier PASS。

**Context**: 该结论与 V7 合成 canary 0/4+0/4（SER 0.20 ≈ 51 错误/帧 → 每
组件多错）以及 V6/V7 全线 0/N 历史一致；并解释 D04 双峰行为（iter-1 成
功/100 迭代失败）——4-cycle 消息传递的振荡是症状而非独立类别。

**Consequences**: R 阶段仅解锁 **R3 code-only**（prior 与 decoder 接口不
变，只改一个明确的 finite graph/rate 属性：把退化的 85 组件图换成同
n/m/rate/度数、连通、girth≥8 的图）。R1/R2 锁死。R3 候选需 OpenSpec
amendment + 独立复核后方可冻结；E01 门（≥1/64）与 A01 门（≥120/128）不
变。D05 独立只读复核（reviewer-go）为下一科学门。最高状态仍为
`ready_for_fresh_confirmation`，禁止 promoted/qualified/
observed_fresh_correction。

---

### 2026-08-14: V13-D05 独立复核 ACCEPT + R3 候选冻结（amendment）

**Decision**: reviewer-go 独立只读复核（2026-08-14）对修正版 D05 包
`v13_d05_20260814_corrected` 出具 **ACCEPT，零 blocker**：五任务全过
（六文件包 + verifier PASS；图普查 85 组件/girth4/d_min3 独立重算一致；
结构天花板 0.75==0.75、完美对应 24/24+8/8、对抗性逐帧 0 失配；决策表符
合性判断——`mixed` 不成立，因为帧级完美对应是决定性分离：每个失败帧结
构上不可纠（≥2 错误在 d_min=3 组件），每个结构干净帧在（失配的）先验
下也成功，先验解释 0/32 结果；边界扫描干净；无效发射处理正确）。四个
非阻塞警告记录在案（共存分辨率 operationalization、rationale 措辞、
D05 重算聚合的可复现性依赖、real_decode_authorized 语义）。

**R3 amendment (frozen by this entry)**: 唯一候选 = **一个** finite
graph/rate 属性变更——把冻结 R1A 退化图（85 个不相连 2-校验组件，Tanner
girth 4，组件 d_min 3）替换为**连通简单 check 图**（170 校验节点、256
变量边、变量全 degree 2、校验度 168×3+2×4、无平行边、check 图 girth≥4
即 Tanner girth≥8）。构造：确定性种子化随机配对，冻结种子 = 20260818
（>=20260814 中第一个通过 简单/连通/check-girth≥4 门的种子；原型验证
通过）。**不变**：prior（QSC p=.20）、decoder 接口（flooding FFT-QSPA，
与 D03 证明等价的镜像循环）、校验数 170、n=256、rate、max_iter=100、
syndrome/tag 语义、Alice 边界、六文件包契约。新身份
`nbldpc_v13_r3_code_v1`（canonical manifest 含构造种子与 girth 证书）。

**E01 预注册（冻结）**: 64 个 bw200 development 帧 = 按 (frame_id,
frame_identity) 排序的 development 行，跳过前 32（D04），取接下来 64：
[77,78,88,89,92,98,100,102,104,105,106,108,111,113,115,116,117,118,119,
121,123,124,125,127,128,129,134,138,139,140,142,144,145,148,151,153,159,
160,161,163,165,166,168,170,171,172,173,175,177,179,181,184,187,190,193,
194,196,198,208,212,215,216,217,221]。与 D04 的 32 帧及 128 个 audit 帧
互斥。E01 = baseline（unchanged R1A）与 candidate 各执行一次；门：
candidate ≥1/64 independently exact-corrected + syndrome consistency +
post-decode exact check + 零 forbidden/internal/accounting failures；
0/64 → `failed_existing_data_feasibility` 冻结路线。E01 通过 → E02 冻结
候选（禁止继续调参/替换）。A01（候选在 128 个 frame-identical audit 帧
上各一次；≥120/128、零 forbidden、median ≤120 s/frame、disclosure ≤8.75
bits/symbol——170×10/256=6.64 结构性通过）→ A02（bw120/bw180 预注册只读
跨层检查）→ C01。

**Consequences**: R3 候选实现（`comparison_bench/` 内新模块 + E01 通道 +
IT0-IT3 测试）现在开始；E01 前必须 IT0-IT3 全过。所有失败保留；禁止
重试/调参/替换/同义重跑 V7/V10/V11 路线。

---

### 2026-08-14: V13-E01 门通过（candidate 64/64）+ A01 开始

**Decision**: E01 development screen 生产执行一次（run_id
`v13_e01_20260814`，64 个预注册 bw200 development 帧）：R3 候选
`nbldpc_v13_r3_code_v1`（QSC p=.20、flooding、连通 girth-8 图）**64/64
exact_correct**，unchanged V7 R1A 基线 13/64，零 forbidden/internal/
accounting 失败，全部行 syndrome consistency + post-decode exact equality，
严格只读 verifier PASS。E01 门（≥1/64）**通过**；E02 无操作——候选在 R3
amendment 中已预冻结，无调参/替换。这与此前 D05 `code` 诊断完全一致：
把退化的 85 组件图换成同契约的连通图后，在相同先验/解码器下可解码性
剧变。

**A01 预注册（本条目固化）**: candidate-only（baseline 不在 audit 帧上
运行——预先决定）；128 个 frame-identical V5 confirmation 帧
（partition ranks 0..127，bw200，与 D04/E01 development 帧互斥）；门
≥120/128 exact + 零 forbidden + median ≤120 s/frame + disclosure ≤8.75
bits/symbol（170×10/256=6.640625 结构性满足）。通过 → 仅
`ready_for_fresh_confirmation`；未过 → `retrospective_non_ready`。

**Consequences**: A01 生产运行（`v13_a01_20260814`）已启动；其后是 A02
（bw200 通过后预注册只读 bw120/bw180 跨层检查，不提升状态）与 C01
（独立验收 + 记忆 triage + 用户决定 fresh acquisition）。64/64 与任何
后续结果均不构成 promotion/qualification/fresh correction。

---

### 2026-08-14: V13-A01 通过（128/128）→ ready_for_fresh_confirmation；A02 通过

**Decision**: A01 retrospective audit 生产执行一次（run_id
`v13_a01_20260814`，128 个 frame-identical V5 confirmation 帧，candidate
once）：R3 候选 **128/128 exact_correct**（raw SER 0.039–0.113），零
forbidden，median 0.90 s/frame（门 ≤120），disclosure 6.640625（门
≤8.75）。全部 readiness 门通过 → **run_state=`ready_for_fresh_confirmation`**
（V13 冻结计划允许的最高声明状态）。严格只读 verifier PASS。

A02 cross-stratum check 生产执行一次（run_id `v13_a02_20260814`）：
bw120 128/128、bw180 128/128 exact_correct，readiness gate 均满足；
`no_state_promotion=true`（只读检查，不改变 bw200 状态）；verifier PASS。

**Context**: E01（64/64）+ A01（128/128）+ A02（256/256）在同一冻结候选
（连通 girth-8 图 + QSC p=.20 先验 + flooding FFT-QSPA）上的全绿结果与
D05 `code` 诊断闭环：图的连通性/girth 是此前 24/32 失败的根因，替换后
在相同先验/解码器下全部精确纠错。补充观测：candidate 帧耗时 median
~0.9–1.0 s（远低于 120 s 门）；全部帧 syndrome_consistent + post-decode
exact equality。

**Consequences**: V13 的 existing-data 诊断路线达到终态
`ready_for_fresh_confirmation`。**不构成** promotion/qualification/fresh
correction（身份仍为历史复用）。下一步由用户决定：是否另开 OpenSpec
change 做 fresh acquisition（新帧身份）以把该候选提升为 fresh canary/
confirmation/qualification。C01（独立验收 + 记忆 triage）进行中。

---

### 2026-08-14: V13-C01 独立验收 ACCEPT — V13 规划完成

**Decision**: reviewer-go 独立只读验收（2026-08-14）出具 **ACCEPT，零
blocker**：六项任务全过——(1) 五个生产包（D04/D05_corrected/E01/A01/A02）
只读 verifier 全 PASS 且 run_state 与声明集一致；(2) 冻结门全部满足
（E01 candidate 64/64≥1/64、A01 128/128≥120 + median 0.904s≤120 +
disclosure 6.640625≤8.75 + gate_passed==run_state、A02 两层 128/128 +
no_state_promotion）；(3) 预注册纪律（D04=排序前 32、E01=次 64、A01=128
audit，互斥且与 decision-log 冻结清单精确一致）；(4) 声明边界（无
promoted/qualified/observed_fresh_correction、无 raw 数据持久化、纯加法
提交零删除）；(5) 执行授权（outcome 行数精确匹配授权解码集：32/128/128/
256）；(6) 科学一致性（`ready_for_fresh_confirmation` 为 V13 最高状态、
R3 候选独立重算一致：seed 20260818、连通、Tanner girth 8、rank 170）。
三个非阻塞警告记录在案（首版 D05 包的 run_state 标注、D01 bursts_runs
已知 bug 与 D05 修正聚合、A02 跨层 frame_id 复用——身份以
(stratum, frame_id, frame_identity) 三元组为准）。

**Consequences**: V13 冻结规划**全部完成**：P→D→R→I→E→A→C 每阶段按
纪律执行，终态 `ready_for_fresh_confirmation`，七个生产包 + 无效发射
notice 全部保留并提交。记忆 triage 完成（AGENT_PROJECT_MEMORY §47）。
待用户决定的独立事项：① 是否另开 OpenSpec change 做 fresh acquisition
（新帧身份 + prepare/review/execute/verify 链）以推进
confirmation/qualification/promotion；② V12 change 的 archive 决定
（独立 housekeeping）。两者都不由 V13 自动触发。`

---

### 2026-08-14: V14 效率可行性门——计划冻结（freeze review ACCEPT）+ 实现 + 门执行启动

**Decision**: 按调研路线（docs/nonbinary-ldpc-efficiency-roadmap-survey.md）
立项 V14 效率可行性门：在构造任何高码率码之前，用 DE 判定"结构化信道
（V13 characterization 帧经验差分分布）上是否存在 rate≥0.90、f≤1.3 的
非二元 LDPC 系综"。冻结内容：信道模型（λ=1e-3 光滑化、cross-fit 只用
characterization 帧；H(w')=0.5677 bits/symbol）；候选集 3 个 λ
（{2:.25,3:.30,4:.45}/{2:.20,3:.25,5:.55}/{3:.3,4:.7}）× m∈{15,16,17,18}
共 12 点评估（不做 profile 搜索——V11 教训 66.7h）；Stage 0 QSC 回归
（q=4 R=0.75 发表门限 0.069±0.012）；Stage 1 折叠小 q 结构化验证
（φ_m(d)=d mod 2^m）；Stage 2 q=1024 点评估（n_samples=1e4、max_iter
150、熵≤0.01 连续 20 迭代）；预算 3 GiB RSS / 24 h wall / execute-once
+ 严格字节回放；预注册降级链（Li-Fair-Krzymień GA → Cohen 位面分解 →
resource_blocked）。判定规则先冻结：PASS iff Stage 0 通过且存在收敛点
且 f≤1.3；FAIL → 路线冻结为"仅 fresh 确认 V13 R3 现状"。

**Process**: DE 机制由调研子代理定稿（V9 run_mcde 信道块 ~10 行改动
即支持任意 w；q=1024 单点 ~1.18s/500×30 可行、profile 搜索不可行）；
freeze review 首轮 BLOCKERS（spec 候选集与 design 矛盾、Stage 0 锚点
漂移）修复后复评 ACCEPT（三个非阻塞词汇警告已并入）；实现由
opencode-go/deepseek-v4-flash 子代理落实（nonbinary_v14_channel.py、
nonbinary_v14_mcde.py——numba 本地核拷贝 + QSC 模式与 V9 等价 1e-12、
cli/run_v14_gate.py），独立 verifier ACCEPT；测试 13/13 + v13 回归
49/49 = 62/62（gate 修复后 64/64）；V8/V9/V11/V13 源码零改动。

**Correction**: 首启失败——gate 动作对 evidence 目录整体 fail-closed，
而模型文件（model 动作产物、已提交）先存在；修复为按文件 fail-closed
（模型文件属同一冻结证据集，gate 只读校验之；gate 自身 6 个输出文件
任一存在即拒绝，execute-once 不变）。

**Consequences**: 生产门（Stage 0/1/2）已启动（execute-once）。门结果
决定 V15：PASS → V15 高码率候选立项（合成资格 + fresh 实数据需用户
决定采集）；FAIL → 路线冻结声明。门证据落 change 的 evidence/ 目录
（加法、fail-closed）。

---

### 2026-08-15: V14 效率可行性门——gate_state=FAIL，效率路线冻结声明

**Decision**: V14 门生产执行一次（evidence 提交 1cdc63b6），E02 独立
gate review **ACCEPT**：Stage 0 机制回归 PASS（proxy 0.060 vs 发表
0.069，|δ|=0.009≤0.012）；Stage 1 折叠验证全绿；Stage 2 的 12 个冻结
点（3 λ × m∈{15,16,17,18}，q=1024 结构化信道）**全部非收敛**——150
迭代后平均 base-q 熵停在 0.288–0.357（收敛阈 0.01 的 29–36 倍，非
边际失败）；f 值 1.032–1.239 全部满足 f≤1.3，但收敛是绑定判据 →
**gate_state=fail**。预算：wall 87 min ≤ 24 h、peak RSS 577 MiB ≤
3 GiB；严格回放在途。机制经 T2 等价测试（与 V9 1e-12）与 Stage 0
文献回归双重背书，FAIL 不是机制伪影。

**科学解读（规划层，非新结论）**: 四个码率点（R=0.9414–0.9297）全部
低于该信道容量（C≈0.9432 base-q），故非信息论不可能；而是**普通不
规则系综（含 degree-2 的 λ、dc≈51 集中 ρ）在该极端码率上的 BP 阈值
距容量存在结构性缺口**。这与历史一致：V10/V11 在 QSC 上 .22/.32 门
失败是同类"普通系综的 BP 阈限"现象。V13 R3（f≈12.1）仍是唯一经
验证的正确器；fresh-confirmation-only 路线不受影响。

**Consequences（冻结纪律的终态）**: V15（高码率候选）与 V16（部署
适配）**不立项**——其提案/设计骨架保留为"门未过、不立项"状态。V14
禁"最接近"续行与换候选重跑；效率路线的下一步只能由用户决定另开
新 change，候选方向（均需新 DE 门先行）：① 非二元 SC-LDPC（阈值饱和
文献：Zhang 2016；V11 在 QSC 门失败但本结构化信道上耦合增益未测）；
② Cohen 2019 位面分解（与本数据 MSB→LSB 单调失配同构）；③ 多边/
高维 λ 族。V12 archive 与 fresh acquisition 决定仍待用户。

---

### 2026-08-15: 更新目标 P0 收口完成 + P1（fresh acquisition）/ P2（V17 位面门）立项

**Decision（用户更新目标）**: P0 状态收口（纯 housekeeping、无科学
执行）→ P1（立即优先：V13 R3 fresh acquisition）→ P2（独立效率研究：
位面/边标签 DE 门先行）。

**P0 执行（2026-08-15，提交 fb6e579d）**:
- V12 正式归档 →
  `openspec/changes/archive/2026-08-15-formal-nonbinary-ldpc-v12-real-micro-feasibility/`
  （保留 `source_partition_blocked`、X01/X02 未执行、v2 prepare 包；
  归档≠成功、不重开执行；delta spec 未合并——V9/V10 先例）。
- V15/V16 归档为 aborted drafts（未立项/前置门失败；delta spec 未合并；
  aborted_notice.md 记录重启边界：需新 DE 门 PASS）。
- 陈旧文档修复：CURRENT_TASK.md（V14 段降级为历史）、V14 tasks.md
  （头部状态、测试数字、回放完成）、V13 tasks.md（C01 COMPLETE、
  IT0-IT3 49/49）、AGENT_HANDOFF.md（Current State 重写）、记忆
  §47/§48 修订 + §50 新增。
- V14 测试数字统一（原始记录 = decision-log 2026-08-14）：修复前
  13+49=62/62 → 修复后 15+49=**64/64**。
- 本地领先 `origin/main` 28 个提交（收口后 29）；**push 待用户单独
  授权**。

**P1 立项（提交 240e3a2e）**: 新 change
`formal-nonbinary-ldpc-v13-r3-fresh-acquisition`——冻结：新帧/载荷
身份（排除 V4/V5/V12/V13 全部历史锁）、acquisition/window/stratum
（bw200 主）、三角色隔离、R3 码本/先验/迭代上限不变、漂移与无
eligible frame 停止规则、失败原样保留；流程冻结→prepare→review→
单次 execute→只读 verify→fresh-confirmed/frozen failure。数据事实：
2026-08-15 检查 `D:\Data` 无 fresh 帧数据源（最新 2026-07-28 JSI，
非帧数据）→ prepare 预计产出 zero-eligible（合法冻结结果，V12 先例）；
用户提供新数据后 prepare 可确定性重跑（非失败重跑）。

**P2 立项（提交 240e3a2e）**: 新 change
`formal-nonbinary-ldpc-v17-multibit-structured-de-gate`——纯可行性门：
Stage 0 Cohen/多位机制复现 → Stage 1 MSB→LSB 单调失配映射为冻结
多位信道模型（schema v1）→ Stage 2 预注册 3–5 个边标签/位面候选点
评估（复用/扩展 V14 structured 分支）→ 冻结收敛（熵≤0.01×20 迭代）/
f≤1.3/预算（3 GiB/24h）/execute-once+回放 → 一次执行。PASS → 另开
有限码 candidate change；FAIL → 冻结、不启动 V15/V16、不扩大搜索。
排名冻结：①位面/边标签（直接对应当前数据位面不均匀性）；②SC-LDPC
（QSC 负耦合、结构化未否定）；③多边/高维 λ。

**Process**: P0 由主线程完成并本地提交；P1/P2 规划文档由主线程起草，
两个独立 freeze review（opencode-go/deepseek-v4-flash 子代理，只读）
在途；ACCEPT 前禁止 prepare/实现/执行。V13/V14 源码零改动。

**Consequences**: 两个新 change 的 tasks P07 均为独立 freeze review；
review 结果决定是否进入 PREP/实现阶段。push（30 个本地领先提交）
仍待用户单独授权。

---

### 2026-08-16: V17 多位结构化 DE 门——gate_state=mechanism_unverified（FAIL 类），位面/边标签效率路线冻结

**Decision**: V17 生产 gate 执行一次（wall 7026.6 s，peak RSS 541 MB
≤ 3 GiB/24h 预算），strict replay 5/5 字节一致，E02 独立 gate review
**ACCEPT（零 blockers）**。终态 **`mechanism_unverified`**（FAIL 类）：
- **Stage 0 锚点 A（q=4 退化 p1=p2 内部一致性）失败**：
  bit-plane 分解 DE 阈值 0.0525 vs 符号级 QSC DE 阈值 0.0600，
  Δ=0.0075 > 容差 0.005 → `mechanism_verified=false`。方向性成立：
  位面分解在 p=0.055 起 joint 未收敛（熵跃升 0.95），符号级至
  p=0.060 仍收敛（0.0625 才翻转）——同一系综/seed/n_samples=1e5/
  max_iter=150 下位面分解阈值严格低于符号级阈值，Cohen 式
  位面分解机制未在冻结判据内复现。
- **Stage 0 锚点 B（文献交叉）通过**：computed 0.0600 vs published
  0.069，|δ|=0.009 ≤ 0.012（V14 冻结常量逐字一致）。
- **Stage 1 模型构建成功**：V13 D01 只读聚合 → 10 个 MSB-first
  位面误码率（3.05e-5→3.75e-2），product-of-marginals 联合近似
  （显式声明保守假设），熵 0.549955 bits/symbol。
- **Stage 2 诊断（diagnostic_only）**：3 候选（bitplane/edgelabel/
  planeweight）× m∈{15,16,17,18} 全 12 点 **全部未收敛**，
  f_achieved∈[1.065,1.279] 均 < f_limit 1.3 但收敛为绑定判据；
  无 pass_point、无 closest/rerun/调参痕迹。

**科学解读（规划层，非新结论）**: 门冻结发生在机制层而非系综层——
Cohen 2019 多位位面分解机制未通过内部一致性锚点，故 Stage 2 的
12 个诊断点不构成效率结论（仅记录，不引用为证据）。这与 V14
（普通不规则系综在 rate 0.93–0.94 无 BP 收敛点）共同说明：位面/
边标签路线在该冻结判据下不可验证，不进入有限码。

**Consequences（冻结纪律的终态）**: 位面/边标签效率路线按 V17 纪律
**冻结**；不启动 V15/V16、不扩大搜索、无"最接近"续行、无 rerun/
调参。效率路线的下一步只能由用户决定另开新 change（候选方向：
② SC-LDPC——QSC 下负耦合、结构化信道下未否定，仍排第二；
③ 多边/高维 λ 族，排第三；或用户指定的其他方向）。本门无 FER/
资格/效率实测结论；P1（V13 R3 fresh acquisition）独立推进不受
影响，仍阻塞于 fresh 数据（用户提供后重新 prepare 即可）。
证据：change `evidence/` 6 文件（5 科学 + replay 记账）。


### 2026-08-16: V13-R3 fresh 数据准入——2026-01-21 三源判定为 data_intake_rejected

**Decision**: 用户提供的三个 `2026-01-21` Type2 ttbin 源不能作为 V13 R3
fresh-confirmation 数据源。新增 D0 准入证据包
`comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_intake_20260816/intake_decision.json`，
判定 `data_intake_rejected_for_fresh_confirmation`。不进入 P1 prepare/execute/verify。

**Context**: frozen design §1 要求 fresh 数据晚于 V13 历史且为可核验 10 dB
Type-II 帧数据。三个源时间戳为 2026-01-21、损耗元数据缺失；且 folder1 已有
D2 烟测 `raw_ser=0.254663`，远超 V13 D01 参考 0.0771，已触发漂移门。

**Alternatives considered**:
- 按原“v16”规划继续 prepare/execute：拒绝，因数据不 fresh 且烟测已漂移。
- 降级为 legacy drift audit：可另开新 change，但不得使用 fresh-confirmed/
  promotion/qualification 声明。

**Consequences**: P1 保持 `no_eligible_frames` 阻塞态；D1–D5 仅在诊断标签下
可后续执行；真正 fresh 数据到达后重新进入 D1–D5→P1。push 仍待用户单独授权。

### 2026-08-16: V13-R3 fresh 数据准入——D1–D5 诊断执行完成，D5 drift_exceeded

**Decision**: shell 可用后按修正参数执行 D1–D5 诊断，完成三源 sidecar/pairs/manifest 与全量漂移预检。D5 三源全部 `drift_exceeded`，按冻结停止规则自动停止，不进入 P/E/V。

**Context**: D0 已判定 `2026-01-21` 三源 `data_intake_rejected_for_fresh_confirmation`；D1–D5 作为只读诊断仍按修正参数执行，以固定证据并确认漂移幅度。

**Evidence**:
- D1: `workspace/v13r3fresh_20260816/d1_baseline.json`
- D2/D3 sidecars: `workspace/v13r3fresh_20260816/sidecars/<source_tag>/`（`map_sanity.verdict=FAIL`，raw SER ≈0.240–0.256）
- D4 pairs: `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/<source_tag>/pairs.parquet` + `build_manifest.json`
- D5: `workspace/v13r3fresh_20260816/precheck_report.json`，三源 `precheck_state=drift_exceeded`，fail reason 均为 `raw_ser_mean_deviation_exceeded`

**Consequences**: P1 仍保持 `no_eligible_frames` 冻结终态；P/E/V 不进入。真正 fresh 数据到达后重新进入 D1–D5→P1；若用户坚持使用 2026-01-21 数据，另开 legacy drift audit change。push 仍待用户单独授权。

### 2026-08-16: V13-R3 legacy drift audit——用户决定使用 2026-01-21 三源；192 帧 188 exact_correct / 4 decode_failed

**Decision**: 用户明确表示这些是之前采集的数据、纠错算法对具体数据源要求没那么高，要求使用三份 `2026-01-21` Type2 数据继续。按冻结规则不以 fresh-confirmation 进入 P/E/V，另开 change `formal-nonbinary-ldpc-v13-r3-legacy-drift-audit`，claim boundary 仅限 `legacy_drift_audit`。

**Execution（一次）**: 新增最小 execute/verify 工具（8 测试通过）。三源各取前 64 个完整帧（frame_id 0..63，共 192 帧），不变 R3 候选 `nbldpc_v13_r3_code_v1`（p=.20、flooding FFT-QSPA、max_iter=100）每帧解码一次，失败原样保留。

**Result**: 188/192 `exact_correct`；4 帧 `decode_failed`（`iteration_limit`：type2_1M frame 15/20、type2_2M frame 52/56），raw SER 0.230–0.297。三源 raw SER 均值约 0.243–0.255（V13 D01 参考 0.0771）。只读 verify OK。证据包：
`comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3_legacy_drift_audit_20260816/`。

**Consequences**: 本结果仅证明 R3 候选在已知漂移 legacy 数据上 188/192 精确纠错，不构成 fresh-confirmed / promotion / qualification；P1 `no_eligible_frames` 冻结终态不变；P2 V17 `mechanism_unverified` 不变。push 仍待用户单独授权。

### 2026-08-16: V13-R3 legacy drift audit——全量 8412 帧完成，8284 exact_correct / 128 decode_failed

**Decision**: 用户要求继续使用三份 `2026-01-21` legacy 数据；在 192 帧审计后进一步执行全量 8412 帧审计。采用 8 chunk 并行（`--all-frames --chunks 8`），每个 chunk 独立 additive 包，claim boundary 仍仅 `legacy_drift_audit`。

**Result**: 8/8 chunk verify OK；合并全量结果：
- 总帧数：8412
- exact_correct：**8284**
- decode_failed：**128**（均为 iteration_limit）
- exact_mismatch：0
- 分源：1p5M 2729/2767，1M 1970/2000，2M 3585/3645
- raw SER 均值：0.240–0.256（V13 D01 参考 0.0771）

**Evidence**: 合并包 `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3_legacy_drift_audit_full_20260816/` + 8 个 chunk 包。

**Consequences**: 仍不构成 fresh-confirmed / promotion / qualification；P1 `no_eligible_frames` 与 P2 V17 `mechanism_unverified` 均不变。push 待用户单独授权。

### 2026-08-16: V20 scientific reclassification and V21 Bob-only plan

**Decision**: 接受外部审查结论，V20 的 `31/64`、`40/96` 不得标为可执行 FER：
- `31/64` = oracle-aided best-of cascade upper bound；
- `40/96` = top-4 oracle list coverage；
- standalone bounded4 `30/64` = unverified Bob-only estimate；
- V01 = counting-only verifier。
V20 状态改为 `CONCLUDED_PENDING_SCIENTIFIC_CORRECTION_AND_ARCHIVE`，语义修正后
再归档。新建 V21 plan：`docs/nbldpc-v21-bob-only-plan-20260816.md`，只验证
Bob-only 策略 S0/S1/S2，Alice 仅出现在最终指标阶段；停止门 FER≥0.45 则冻结
短块 OSD/top-K 路线，转 V22 结构化构造。

**Context**: V20 cascade 用 `np.array_equal(x_hat, alice)` 决定是否调用
bounded4 以及从 top-K 中选谁；Bob 无法知道 syndrome-consistent 候选是否是
exact mismatch，因此该策略不可执行。n64 最多只剩 5 bits 公开预算，n80 只剩
7 bits，16/32-bit 验证标签会使 f 升到 1.50–2.05，top-K+public hash 不能直接
立项。

**Alternatives considered**:
- 继续扩样 n80 top-K：拒绝，因 oracle coverage 与可执行 FER 混同；
- 直接进入 fresh qualification：拒绝，必须先完成 Bob-only 重分类与验证；
- 直接归档不修语义：拒绝，因会固化错误 FER 标签。

**Consequences**: V20 保持 active 直到 Phase 0 addendum 完成并真正移动到
archive；下一阶段执行 V21 Bob-only 验证；push 仍待用户单独授权。

### 2026-08-16: V21 Bob-only stop gate triggered

**Decision**: V21 Bob-only validation on 64 fresh n=64 frames:
- S0 BP-only: 24/64, FER=0.625
- S1 bounded4-only: 28/64, FER=0.5625
- S2 BP-first-fallback-bounded4: 28/64, FER=0.5625
All >= 0.45, so stop gate is triggered. Short-block OSD/top-K branch is frozen as
`scientific_not_ready`. V20 moved to archive; V22 structured construction drafted.

**Context**: This confirms the external review: Bob-only executable FER is around
0.56-0.63, not the oracle upper bounds 0.5156/0.5.

**Consequences**: No fresh qualification; next phase is V22 DE-gated MET/protograph
or SC-LDPC construction. push still user-gated.
