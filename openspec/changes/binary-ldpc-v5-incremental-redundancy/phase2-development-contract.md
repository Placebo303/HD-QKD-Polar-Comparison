# Frozen Phase 2 Development Package Contract

## 1. Identity, path, and lifecycle

The sole package is:

```text
comparison_bench/outputs_comparison/formal_ir_methods/
  20260731_v1_binary_ldpc_v5_development/
```

Constants:

- `run_id="binary_ldpc_v5_development_v1"`
- `method_id="ldpc_formal_v5"`
- `role="sacrificed_development"`
- `dimension=1024`, `frame_len_symbols=256`, `mapping="gray"`
- candidate order `V5-C0,V5-C1,V5-C2`
- stratum order `bw120,bw180,bw200`
- role-rank order `0..511`
- execution order is candidate, stratum, role rank
- expected outcomes `4608`

Prepare, main-thread review, execute, and read-only verify are separate.
Prepare and execute each occur at most once. The directory is fresh,
no-overwrite, non-resumable, and immutable after execution. A failure package
is retained and never repaired, tuned, or rerun. No synthetic or confirmation
output is created by this phase.

## 2. Exact artifacts

The package contains exactly these twelve files:

```text
pre_run_plan.json
partition_lock.json
formal_codebook_manifest.json
formal_selection_manifest.json
formal_channel_model.json
v5_h2_manifest.json
v5_policy_manifest.json
development_frame_outcomes.csv
development_transcript.jsonl
development_selection.json
development_run_manifest.json
development_report.json
```

Prepare writes only `pre_run_plan.json`. Execute finalizes the remaining
eleven files even on retained partial failure when possible. Every JSON object
has an exact schema and a `*_sha256` self-hash; every cross-artifact edge also
records the target file SHA256. Canonical JSON is compact sorted-key ASCII
with `allow_nan=False`. JSONL is concatenated `canonical_event_v5` bytes. CSV
uses the already frozen v5 canonical encoder.

## 3. Plan

The plan contains exactly:

```text
schema
run_id
method_id
role
domain
execution
output_binding
partition_binding
predecessor_binding_sha256
method_bindings
seed_schedule
gates
ranking
caps
failure_policy
scoped_source_sha256
environment
plan_sha256
```

Constants:

- `schema="binary_ldpc_v5_development_plan_v1"`
- `domain` contains exactly dimension, frame length, mapping, candidates,
  strata, and `development_frames_per_stratum=512`
- `execution` contains exact order string, 4,608 ordered attempt IDs, and its
  SHA256
- `partition_binding` contains exact production lock path relative to repo,
  file SHA256
  `17c128830e5e23dca0d1ddfabf1d3853b2d975e6f65a477bdb52eea4baf5b943`,
  partition content SHA256
  `060fe8e00542a0aa8a87f978018b4d8d956413a3829c6ab5b32a47d3998cd051`,
  development-row digest, count 1,536, and confirmation count 384
- `predecessor_binding_sha256` is
  `d1c888bd09bdaf1ad186292e4bfe14bbef32897d75061b9836b6ac1c95222e3a`
- `method_bindings` contains exact H1 codebook, H1 selection, channel, H2
  manifest, and policy-manifest content hashes
- `gates` is 510 successes of 512 denominators in every stratum and zero
  forbidden failures
- `ranking` is exactly section 7
- `caps` is complete-run 14,400 seconds plus the exact policy per-frame caps
- `failure_policy` is
  `immutable_partial_finalization_no_resume_no_rerun_no_tuning`
- `environment` contains Python, NumPy, ldpc=2.4.1, platform, and
  `test_only=false`

`scoped_source_sha256` binds each Phase-2 runner/verifier/development source
file and all Phase-1/v4 source files it invokes. Whole-worktree status is
diagnostic only and is never a verifier gate.

Every remaining artifact schema, partial-failure convention, file-hash edge,
and verifier order is frozen in `phase2-artifact-contract.md`; it is
normative.

## 4. Roots and seeds

Prepare creates exactly 18 independent 256-bit CSPRNG roots: one per
candidate, stratum, and verification round 0/1. Each root record contains
exactly:

```text
candidate_id
stratum
verification_round
root_hex
seed_count
seed_ids_sha256
```

`root_hex` is 64 lowercase hex from `secrets.token_bytes(32)`.
`seed_count=512`. For role rank `i`, derive:

```python
label = (
  f"binary_ldpc_v5_development_v1|{candidate}|{stratum}|"
  f"round={round}|rank={i}"
).encode("ascii")
raw = hashlib.shake_256(bytes.fromhex(root_hex) + b"\0" + label).digest(328)
bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8), bitorder="big")[:2623]
```

Then use the frozen `seed_record(bits)`. All 9,216 seed IDs and all 18 roots
are unique. Prepare scans every bound predecessor plan/transcript and rejects
overlap with any prior root or seed ID. The plan stores the 18 records,
overall seed count, sorted seed-ID digest, prior-root/seed digests and counts,
and an isolation boolean. Seed bytes/bit arrays are not stored.

No Phase 3 or 4 roots are created in Phase 2.

## 5. Prepare and execute APIs

New CLIs:

```text
python -m comparison_bench.src.comparison_bench.cli.run_ldpc_v5_development
python -m comparison_bench.src.comparison_bench.cli.verify_ldpc_v5_development
```

Runner modes:

```text
--mode prepare --output-dir <exact-dir> --partition-lock <exact-lock>
--mode execute --output-dir <exact-dir>
```

Production entry points expose no test switch. Private test helpers require an
explicit fake method runner and test-owned output root; tests can never fall
through to the real decoder or official output.

Prepare requires the exact approved partition file, validates it, builds all
deterministic manifests/policies, creates and validates the seed schedule,
binds source/environment, and writes only the plan.

Execute requires the directory contain only the exact plan, validates every
plan field and current scoped hash, then processes every locked development
row. It calls only `development_arrays_for_frame`, never a confirmation API.
It invokes the production-default `run_ldpc_formal_v5` with the selected
candidate policy and two derived locked seeds. Every attempt enters the CSV
denominator. Transcript slices and hashes are recorded exactly.

## 6. Failure and accounting

Formal statuses and event accounting remain the Phase-1 contract. Package
forbidden classes are:

```text
backend
source
internal
accounting
resource
syndrome
unclassified
provenance
```

Any formal `backend_unavailable`, `aborted_resource_limit`,
`syndrome_inconsistent`, `invalid_input`, or `unsupported_domain` increments
the corresponding forbidden class. `decoder_error` increments `internal`
unless its exact reason is a classified backend failure. Source loading or
identity failure creates a retained nonattempted row and makes the package
non-ready. Unexpected exceptions trigger partial finalization, retain the
exact observed prefix, and make all candidates non-selectable. Missing
denominators are never imputed.

No outcome, event, status, disclosure, runtime, or failure is dropped from
the report.

## 7. Gate and selection

For every candidate/stratum report:

```text
denominator
verified_success
status_counts
forbidden_failure_count
key_dependent_disclosure_bits_total
runtime_s_total
```

A candidate is selectable only if all three strata have denominator 512,
verified success at least 510, and zero forbidden failures.

Rank selectable candidates by:

1. lowest exact total disclosure divided by 1,536;
2. highest minimum-stratum verified successes;
3. highest total verified successes;
4. lowest exact total runtime;
5. candidate ID.

`development_selection.json` records every candidate summary, ordered rank
tuple, eligible list, selected candidate policy/hash or null, and
`ready_for_synthetic_prepare`. No eligible candidate yields immutable
`non_promoted_development`; it is not permission to tune or rerun.

## 8. Read-only verifier

The verifier:

- requires the exact twelve-file set and canonical bytes;
- rebuilds the partition, predecessors, manifests, policies, source hashes,
  environment, seed schedule, execution order, and full artifact DAG;
- reconstructs only locked development arrays;
- validates CSV typing, transcript slices, every public Alice
  syndrome/tag/seed, outcome/accounting/status/failure mapping, denominators,
  candidate summaries, ranking, selection, and readiness gate;
- hashes files before and after and changes none;
- never imports/calls a decoder and returns
  `decoder_reexecution=false`.

Successful return contains exactly:

```text
status
run_status
outcomes
selected_candidate_id
ready_for_synthetic_prepare
decoder_reexecution
```

`status="verified"` proves artifact integrity, not promotion. `run_status` is
`completed`, `non_promoted_development`, or `invalid_execution`.

## 9. Tests

- T0: compile/import/constants/seed derivation/tiny aggregation.
- T1: plan/root/seed uniqueness and predecessor isolation; exact partition;
  all method paths; no-overwrite; partial finalization; every raw and locally
  re-signed plan/source/manifest/policy/outcome/transcript/CSV/accounting/gate/
  selection/report/run-manifest tamper.
- T2: complete 4,608-attempt fake package plus strict read-only replay, with
  success, retained failure, fallback, cap, exception, and non-promotion.
- T3: all v5 Phase-1 tests, predecessor strict replay, v4 development/
  synthetic/16 dB/10 dB-v2 regressions, compile, frozen diff, exact partition
  hash, and absence of official development output before production.
