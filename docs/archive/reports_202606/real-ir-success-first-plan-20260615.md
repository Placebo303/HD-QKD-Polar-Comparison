# Real IR Success First Plan - 2026-06-15

## 1. First-Principles Objective

The project should prioritize a real information reconciliation (IR) process for high-dimensional time-bin / arrival-time QKD data.

The near-term goal is not to fit or report a polished reconciliation efficiency number. The goal is to make non-Polar methods actually complete the same kind of verified reconciliation task that the existing Polar line has already demonstrated.

In practical terms, a candidate method must take real paired Alice/Bob symbols, use only protocol-allowed public information, correct Bob's frame toward Alice's frame, pass independent verification, and record actual leakage. Only after that should the project compare efficiency, runtime, or final method choice.

## 2. Why The Plan Changes

The previous planning emphasis was "select the best IR method." That is still the final destination, but it is premature while most non-Polar methods have not yet produced stable real-data verification success.

The next phase should therefore be:

1. define what counts as real IR success;
2. select a small set of real QKD frames and operating regimes;
3. make at least one non-Polar method succeed on real frames;
4. diagnose why LDPC/qLDPC fail or only partially succeed;
5. only then compare leakage, beta, runtime, and method choice.

## 3. Real IR Success Criteria

A run should count as real IR success only if all criteria below hold.

### 3.1 Real Data Criteria

- Input is a real paired-symbol frame from the high-dimensional arrival-time data path, not only a synthetic channel sample.
- Alice and Bob symbols are represented through the shared `FrameBatch` contract.
- Dataset metadata preserves at least dimension, bin width, frame length, and source/provenance tag when available.

### 3.2 Protocol Discipline Criteria

- The decoder must not directly copy or inspect Alice's full frame as a correction oracle.
- Any information derived from Alice and disclosed to Bob must be counted as public leakage.
- The method may use Alice-side syndromes, parity checks, verification hashes, or allowed transcript messages, but those disclosures must be accounted for.
- Verification must be independent of the decoder's internal success flag.

### 3.3 Success / Failure Criteria

- `verify_success=True` is required for success.
- A decode that improves BER/SER but fails verification is still a failure for method-selection purposes.
- `method_status` must preserve failures such as `decode_failed`, `no_verified_success`, `experimental_failed`, `reference`, `stub`, or `unavailable`.
- No pipeline layer may convert failed, reference, unavailable, or unverified results into `ok`.

### 3.4 Leakage / Efficiency Criteria

- `leak_EC_actual_bits` must be derived from protocol transcript or explicit accounting.
- `beta_eff_empirical` must be derived from leakage and error inputs, never hand-filled.
- Approximate leakage is allowed only when clearly labeled in `notes` or diagnostics.
- Leakage comparisons across methods are valid only when the decomposition semantics are documented.

## 4. Method Roles For The Next Phase

### 4.1 Polar Existing

Role: frozen reference baseline.

- Use it to understand what the already-working Polar line achieved.
- Do not treat imported `polar_existing` rows as evidence that the comparison layer reran Polar.
- Do not modify original Polar source or workflows.

### 4.2 Cascade Lite

Role: first non-Polar real-data success candidate.

Rationale:

- It is currently the most stable executable non-Polar route on observed real-data representative sweeps.
- It is less dependent on a precise parametric channel model than LDPC.
- It can provide the first concrete non-Polar answer to: can we reconcile real high-dimensional arrival-time frames at all?

Important caveat:

- It remains an internal simplified Cascade-like baseline, not full industrial Cascade.

### 4.3 Layered LDPC Lite

Role: executable LDPC baseline and failure-diagnosis target.

Rationale:

- It is now a real executable baseline rather than a placeholder.
- Current failures may reveal whether bit-plane independence, LLR modeling, parity budget, or frame size is the bottleneck.

Next work should emphasize diagnostics over cosmetic parameter sweeps.

### 4.4 qLDPC Reference

Role: medium-term q-ary direction and reference feasibility probe.

Rationale:

- High-dimensional time-bin data is naturally q-ary.
- q-ary methods may preserve symbol structure better than independent binary bit planes.

Important caveat:

- Current qLDPC is reference-grade and must not be described as production qLDPC.

## 5. Recommended Work Packages

### WP0 - OpenSpec And Coordination

Goal: make the new objective durable before implementation.

Tasks:

1. Use `openspec/changes/real-ir-success-first/` as the active change.
2. Keep code changes limited to `comparison_bench/` unless a later approved OpenSpec change explicitly says otherwise.
3. Keep all new outputs additive.
4. Record any requirement ambiguity before coding rather than guessing.

Deliverables:

- `openspec/changes/real-ir-success-first/proposal.md`
- `openspec/changes/real-ir-success-first/design.md`
- `openspec/changes/real-ir-success-first/tasks.md`
- `openspec/changes/real-ir-success-first/specs/real-ir-success/spec.md`

### WP1 - Real IR Success Contract

Goal: create one explicit, machine-checkable definition of real IR success.

Implementation target:

- Add comparison-layer helpers or validators, not baseline modifications.

Expected behavior:

- A method result is classified as real success only when verification succeeds.
- Improved post-IR error rate without verification remains failure.
- `method_status` and `backend_status` remain transparent.
- Leakage and beta fields are validated for consistency.

Suggested outputs:

- an audit table or summary column that distinguishes:
  - `real_ir_success`
  - `decode_improved_but_unverified`
  - `verified_failure`
  - `method_unavailable`
  - `reference_only`

Acceptance criteria:

- Existing successful rows remain interpretable.
- Existing failed/reference rows are not reclassified as success.
- Tests cover at least one verified success, one decode failure, one verification failure, and one reference/unavailable status.

### WP2 - Representative Real-Frame Set

Goal: choose a small real-data set for iteration before any full sweep.

Selection guidance:

- Include low, medium, and high raw SER regimes.
- Include at least two dimensions if available.
- Include at least one previously successful/tractable point such as `d=8`, `bin_width_ps=180` if still available in current artifacts.
- Prefer existing `real_sidecars_frame_batch.parquet` or known sidecar-derived frame batches before rebuilding from raw data.

Output policy:

- Do not overwrite existing `real_sidecars_frame_batch.parquet`.
- If a new representative subset is needed, write to a new additive path under `comparison_bench/outputs_comparison/`, for example `real_ir_success_first/`.

Acceptance criteria:

- The chosen frames and their raw SER/BER are documented.
- The subset can be reconstructed from config and manifest.
- The subset is small enough for fast iteration by other agents.

### WP3 - Cascade Lite Real Success Baseline

Goal: establish the first non-Polar real-data IR success path.

Tasks:

1. Run or adapt Cascade-lite only on the representative real-frame set.
2. Preserve transcript/leakage decomposition.
3. Record verification success and failure by frame.
4. Identify the smallest configuration family that produces stable verified success.
5. Do not overclaim beyond simplified Cascade.

Acceptance criteria:

- At least one real-data frame group has verified non-Polar success.
- Leakage accounting is present and labeled.
- Failed frames remain failed.
- Outputs are written additively.

### WP4 - Layered LDPC Failure Diagnosis

Goal: explain current LDPC failures rather than only sweeping parameters.

Diagnostics to produce:

- raw SER/BER bucket;
- frame length bucket;
- dimension bucket;
- bit-plane BER;
- parity fraction;
- LLR mode;
- bitplane rate mode;
- verification failure versus decoder failure;
- whether failure is concentrated in specific bit planes.

Questions to answer:

- Is LDPC failing because the real channel model is not well represented by current LLRs?
- Is independent bit-plane decoding losing important q-ary structure?
- Is the parity budget too low, or is the decoder unable to converge even with more parity?
- Does longer frame length help or hurt?

Acceptance criteria:

- A failed LDPC run is diagnosable by cause bucket.
- No failed run is marked `ok`.
- The result states whether LDPC should continue as a serious candidate, remain diagnostic, or be deferred.

### WP5 - qLDPC Reference Feasibility Probe

Goal: determine whether the q-ary reference path can verify on easy real frames.

Tasks:

1. Start with low-noise / low raw SER representative frames.
2. Use the current internal GF(2^m) fallback unless dependency work is explicitly assigned.
3. Keep `reference` labeling unless the decoder is genuinely upgraded.
4. Record syndrome weight, correction attempts, verification status, and leakage.

Acceptance criteria:

- qLDPC reference either verifies on an easy real frame or produces a clear blocker.
- Any status upgrade beyond `reference` is backed by implementation evidence and tests.
- The result distinguishes q-ary feasibility from production qLDPC readiness.

### WP6 - Final Selection Only After Real Success

Goal: compare methods only after at least one non-Polar path has verified real-data success.

Method selection should use:

- verified success rate;
- post-IR SER/BER only after verification semantics are clear;
- leakage per input bit;
- `beta_eff_empirical`;
- runtime and throughput;
- implementation complexity;
- scientific defensibility.

Acceptance criteria:

- The selected method and fallback are explicit.
- If Cascade-lite is selected, the selection says "simplified Cascade baseline" unless a full Cascade implementation exists.
- If LDPC/qLDPC are not selected, the failure reason is documented rather than hidden.

## 6. Suggested Agent Handoff

For coding agents:

1. Read `AGENTS.md`.
2. Read `AGENT_PROJECT_MEMORY.md`.
3. Read `docs/ir-method-comparison-state-20260615.md`.
4. Read this plan.
5. Implement only tasks from `openspec/changes/real-ir-success-first/tasks.md`.
6. Keep changes in `comparison_bench/` unless the task explicitly updates docs/configs.
7. Use additive output paths and preserve statuses.

For reviewer agents:

1. Verify no original Polar logic changed.
2. Verify no output overwrite occurred.
3. Verify real IR success requires independent verification.
4. Verify leakage/beta are not fabricated.
5. Verify failed/reference/unavailable statuses remain visible.

## 7. Stop Conditions

Stop and return to planning if:

- the task requires changing original Polar semantics;
- a method needs to use Alice's full sequence as an unaccounted correction oracle;
- success cannot be verified independently;
- leakage cannot be accounted for or clearly labeled;
- a required real-data source is missing;
- schema changes are needed but not covered by OpenSpec.

