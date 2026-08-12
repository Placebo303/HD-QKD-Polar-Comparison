# Tasks: final-ir-method-selection

## Phase 2: Data Lock

- [x] Read the active change, project memory, Route A required-field contract, and existing comparison contracts.
- [x] Declare the supported dimension, raw-SER, and frame-length domain, required strata, sample-size/confidence rule, and bounded stopping rules.
- [x] Select exact common frames and freeze disjoint tuning/confirmation frame IDs before tuning.
- [x] Create a data-lock manifest with source hashes, preprocessing/config hashes, seeds, commit, dependencies, and environment metadata.
- [x] Confirm both candidates use the same preprocessing, mapping, success classifier, and independent verification.
- [x] Reserve an additive output directory; do not overwrite prior outputs.

## Phase 3: Bounded Run

- [x] Tune `cascade_lite` and `layered_ldpc_lite` only on the locked tuning split.
- [x] Freeze one global configuration per candidate; prohibit per-point oracle selection.
- [x] Run both fixed configurations on every locked confirmation frame within declared compute/frame/time bounds.
- [x] Persist every attempted frame and its decode/verification status; retain failures in all denominators.
- [x] Preserve `qldpc_reference` as `reference_only` and Polar rows as historical context only.
- [x] Write additive manifests, configuration snapshots, frame records, and aggregate summaries.

## Phase 4: Audit and Decision

- [x] Audit frame identity, source/preprocessing equality, frozen configurations, status preservation, and manifest hashes.
- [x] Separate incompatible leakage decompositions and exclude them from ranking.
- [x] Apply the pre-registered attempted-frame and confidence rule without extending runs adaptively.
- [x] Produce a bounded decision: winner, `no_decision`, or `insufficient_evidence`; state the supported domain and non-claims.
- [x] Perform the Route A required-field compatibility gate without a numerical rerun and record missing fields or outcome.

## Phase 5: Hardening and Handoff

- [x] Review that no `src/`, `experiments/`, `tools/`, or schema/interface files changed.
- [x] Review no existing result or comparison output was overwritten.
- [x] Add or update focused tests only for any new comparison-layer behavior, using disposable output locations.
- [x] Update the decision log, handoff, and OpenSpec task state with evidence paths and remaining limitations.
- [x] Complete memory triage; persist only verified durable findings.
