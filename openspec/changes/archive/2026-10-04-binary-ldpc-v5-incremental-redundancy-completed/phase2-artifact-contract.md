# Frozen Phase 2 Artifact Schemas and DAG

## 1. Existing-schema artifacts

These files retain their existing canonical bytes and schemas; no wrapper,
extra key, or re-signing is allowed:

- `partition_lock.json`: byte-identical copy of the approved production lock.
- `formal_codebook_manifest.json`, `formal_selection_manifest.json`, and
  `formal_channel_model.json`: byte-identical copies from the bound promoted
  v4 synthetic package.
- `v5_h2_manifest.json`: exact `binary_ldpc_v5_h2_manifest_v1` rebuilt from
  the copied selection.
- `v5_policy_manifest.json`: exact
  `binary_ldpc_v5_policy_manifest_v1` rebuilt from the preceding four
  method-binding objects.

Their content self-hashes and exact file SHA256 values are validated before
the first frame.

## 2. Plan filesystem binding

Add `output_binding` to the exact plan field set in the Phase-2 contract. It
contains exactly:

```text
output_directory
artifact_names
prepare_file_set
```

Values are the repository-relative sole package directory, the twelve
artifact names in contract order, and `["pre_run_plan.json"]`. Prepare
requires the requested resolved path equal the sole path. Execute requires the
directory initially contain exactly the prepare file. Neither symlinks nor
path aliases are accepted.

`seed_schedule` contains exactly:

```text
schema
derivation
roots
seed_count
seed_ids_sha256
prior_root_count
prior_roots_sha256
prior_seed_id_count
prior_seed_ids_sha256
isolated
seed_schedule_sha256
```

with schema `binary_ldpc_v5_development_seed_schedule_v1`, the exact
derivation expression from the Phase-2 contract, 18 ordered root records,
9,216 seeds, sorted-list digests, and `isolated=true`.
`seed_schedule_sha256` excludes only itself.

`method_bindings` contains exactly:

```text
h1_codebook_manifest_sha256
h1_selection_sha256
channel_model_sha256
h2_manifest_sha256
policy_manifest_sha256
```

These are content self-hashes, not file hashes.

`scoped_source_sha256` is an object keyed by repository-relative POSIX source
path, sorted lexicographically. `environment` contains exactly
`python_version,numpy_version,ldpc_version,platform,test_only`.

## 3. Outcome and transcript artifacts

`development_frame_outcomes.csv` uses the exact Phase-1 v5 package CSV fields
and canonical encoding. Rows are in execution order. The seven prefix fields
come from the locked development row and exact transcript slice.

`development_transcript.jsonl` is the concatenation, in outcome order, of
every attempt's canonical event bytes. Each CSV row's
`transcript_bytes_len` consumes the next exact slice and its SHA256 must equal
`transcript_bytes_sha256` and the formal outcome transcript hash.

Formal-method nonattempted outcomes containing a non-finite `raw_ser` cannot
enter canonical CSV. The runner replaces such a result with a package failure
outcome containing the same formal identity/provenance, zero events,
`raw_ser=0.0`, `attempted=false`, `denominator_included=false`,
`status="invalid_input"`, and
`failure_reason="package_<class>:<normalized_reason>"`. This is counted as a
forbidden package failure and missing denominator, never as a decode result.

If an unexpected exception occurs after execution begins, finalize the exact
completed prefix plus one such package-failure row for the current attempt.
If plan validation fails before execution begins, write nothing and leave the
prepare-only directory as `invalid_pre_execute`.

## 4. Development selection

`development_selection.json` contains exactly:

```text
schema
run_id
method_id
plan_sha256
partition_sha256
policy_manifest_sha256
outcomes_file_sha256
transcript_file_sha256
selection_status
candidate_summaries
eligible_candidate_ids
ranking_rule
ranked_candidates
selected_candidate_id
selected_policy_sha256
ready_for_synthetic_prepare
selection_sha256
```

Constants:

- schema `binary_ldpc_v5_development_selection_v1`
- selection status `selected`, `non_promoted_development`, or
  `invalid_execution`
- ranking rule is the exact ordered five-item rule from the Phase-2 contract

Each candidate summary contains exactly:

```text
candidate_id
strata
denominator_total
verified_success_total
forbidden_failure_count_total
key_dependent_disclosure_bits_total
mean_disclosure_numerator
mean_disclosure_denominator
runtime_s_total
minimum_stratum_verified_success
selectable
```

`strata` is an ordered three-element list. Each entry contains exactly the
seven fields in Phase-2 contract §7 plus `stratum`. Mean numerator is total
disclosure and denominator is 1,536 only for a full-denominator candidate,
otherwise the actual denominator. No rounded mean float is stored.

Each ranked-candidate entry contains exactly:

```text
candidate_id
rank_key
```

`rank_key` is
`[mean_numerator,mean_denominator,-min_success,-total_success,
runtime_s_total,candidate_id]`; comparison uses exact rational
cross-multiplication for the first pair, then the remaining fields. Only
selectable candidates are ranked.

`selected_policy_sha256` is null when no candidate is selected.
`selection_sha256` excludes only itself.

## 5. Run manifest

`development_run_manifest.json` contains exactly:

```text
schema
run_id
method_id
run_status
plan_sha256
plan_file_sha256
execution_order_sha256
seed_schedule_sha256
expected_outcomes
observed_outcomes
artifact_file_sha256
failure
wall_runtime_s
run_manifest_sha256
```

Schema is `binary_ldpc_v5_development_run_manifest_v1`.
`artifact_file_sha256` contains exact file hashes for artifacts 2--10 in
contract order (partition through selection), excluding the run manifest and
report to avoid cycles.

`failure` is null on a full run, otherwise exactly
`{"class":<frozen class>,"reason":<normalized string>,
"attempt_id":<string or null>}`. Wall runtime is finite, nonnegative,
diagnostic, and never enters ranking. The self-hash excludes only itself.

Run status is:

- `completed` for a full 4,608-row run with a selected candidate;
- `non_promoted_development` for a full valid run with no selection;
- `invalid_execution` for partial/package-invalid execution.

## 6. Report

`development_report.json` contains exactly:

```text
schema
run_id
method_id
run_status
scientific_scope
plan_sha256
run_manifest_sha256
run_manifest_file_sha256
selection_sha256
selection_file_sha256
outcomes_file_sha256
transcript_file_sha256
expected_outcomes
observed_outcomes
candidate_summaries
gate
package_failure_counts
selected_candidate_id
ready_for_synthetic_prepare
next_action
report_sha256
```

Schema is `binary_ldpc_v5_development_report_v1`.
`scientific_scope="sacrificed_10db_development_not_confirmation"`.
`gate` contains exactly the frozen denominator/success/zero-forbidden
requirements and per-candidate booleans. `package_failure_counts` contains all
eight frozen classes, including zeros.

`next_action` is exactly:

- `freeze_phase3_synthetic_plan` if ready;
- `stop_no_synthetic_output_no_tuning_no_rerun` if full non-promoted;
- `stop_invalid_execution_retain_partial_no_resume` if invalid.

The report self-hash excludes only itself.

## 7. DAG and verifier order

The verifier checks in this order:

1. exact file set and canonical encodings;
2. every local self-hash;
3. plan output/partition/predecessor/source/environment binding;
4. byte-identical copied artifacts and rebuilt H2/policy;
5. seed schedule and execution order;
6. CSV/transcript slices and public-payload replay;
7. selection aggregation/ranking;
8. run-manifest artifact map;
9. report duplication and gate;
10. before/after file hashes unchanged.

Locally re-signing a downstream object never excuses a changed upstream edge.

## 8. Exact predecessor root and seed extraction

Extraction uses only the five exact directories and files bound by
`predecessor-contract.md`; no regex or generic 64-hex scan is permitted.
Normalize every root to a 64-character lowercase hex integer, left-padding
historical 128-bit hex and integer roots with zeros. Seed IDs are exact
64-character lowercase hex.

Whitelist:

- promoted v4 synthetic plan:
  - roots from every
    `development_root_binding.roots[*].root_hex`;
  - roots from every `generator.roots[*][*].root_hex`;
  - roots from every value of `v3_seed_binding.root_seeds`;
  - seed IDs from `v3_seed_binding.toeplitz_seed_ids[*]`;
- 16 dB, invalid 10 dB v1, and completed 10 dB v2 plans:
  - roots from `roots[*].root_hex`;
  - seed IDs from `roots[*].seeds[*].seed_id`;
- every bound `*transcript*.jsonl`:
  - seed IDs only from events whose exact type is `VERIFICATION_SEED`, at
    `payload.seed_id`.

The development plan contributes no root/seed record. Sets are deduplicated
after normalization and hashed as compact canonical JSON of the
lexicographically sorted unique string list.

Frozen expected result:

```text
prior_root_count = 26
prior_roots_sha256 =
  afe519e096df61a39093c9ea4952f9c2ff7bade8c0aaa9a29c21d1525609766b
prior_seed_id_count = 1472
prior_seed_ids_sha256 =
  7be045ed771b15f17f0e41dd9163471c1bfe7cde5332c75faf42b73bdc8c8386
```

The verifier independently repeats this whitelist extraction from the bound
bytes. Unknown/missing fields, wrong types, invalid hex, changed expected
counts/digests, or overlap fail closed.

## 9. Private test-package delta

Tests use only these private APIs:

```python
_prepare_test_package(output_dir, *, deterministic_roots) -> dict
_execute_test_package(output_dir, *, method_runner, array_loader, clock) -> dict
_verify_test_package(output_dir) -> dict
```

All dependencies are mandatory keyword arguments; no default may enter the
production decoder or real array loader.

The test output directory must be a fresh, non-symlink descendant of the
repository `workspace/` directory. It is recorded repository-relative in
`output_binding.output_directory`. The approved production partition is read
and copied but `array_loader` is always the explicit fake.

Exact test identity deltas:

```text
plan schema: binary_ldpc_v5_development_plan_test_v1
run_id: binary_ldpc_v5_development_test_v1
selection schema: binary_ldpc_v5_development_selection_test_v1
run-manifest schema: binary_ldpc_v5_development_run_manifest_test_v1
report schema: binary_ldpc_v5_development_report_test_v1
environment.test_only: true
report.scientific_scope: test_only_not_qualification_evidence
report.next_action: test_only_none
```

The supplied 18 deterministic roots follow the production root-record order,
remain unique and predecessor-isolated, and derive all 9,216 seeds using the
same production algorithm. Counts, order, gates, artifacts, failure retention,
hashes, DAG, and 4,608 attempts are otherwise identical.

Production prepare/verifier reject every test identity/path. Private test APIs
reject the official output path and any non-workspace path. Tests must prove
that omitting `method_runner` or `array_loader` fails before package creation
and that neither production decoder nor real arrays are touched.
