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
