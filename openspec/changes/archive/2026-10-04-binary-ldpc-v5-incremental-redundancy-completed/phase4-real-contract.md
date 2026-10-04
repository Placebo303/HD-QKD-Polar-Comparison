# Frozen Phase 4 Real Qualification Contract

## 1. Identity, path, and lifecycle

The sole package is:

```text
comparison_bench/outputs_comparison/formal_ir_methods/
  20260801_v2_binary_ldpc_v5_real/
```

Constants:

- `run_id="binary_ldpc_v5_real_qualification_v1"`
- `method_id="ldpc_formal_v5"`
- `role="real_confirmation"`
- candidate `V5-C2` (the Phase 3 promoted candidate)
- real strata `bw120`, `bw180`, `bw200`
- `frame_count_per_stratum=128` (the partition lock confirmation partition
  size, ranks 0--127, never decoded before)
- stratum order `bw120,bw180,bw200`
- frame order is the exact confirmation role-row order of the partition lock
- expected outcomes `384`

Prepare, main-thread review, execute, and read-only verify are separate.
Prepare and execute each occur at most once. The directory is fresh,
no-overwrite, non-resumable, and immutable after execution. A failure package
is retained and never repaired, tuned, or rerun. No Phase 5 output is created
by this phase.

Phase 4 may start only after the Phase 3 package exists and its read-only
verifier returns `ready_for_real_qualification=true` exactly, and the
partition lock
`20260731_v1_binary_ldpc_v5_partition/partition_lock.json` validates.

## 2. Exact artifacts

The package contains exactly these ten files:

```text
pre_run_plan.json
formal_codebook_manifest.json
formal_selection_manifest.json
formal_channel_model.json
v5_h2_manifest.json
v5_policy_manifest.json
real_frame_outcomes.csv
real_transcript.jsonl
real_run_manifest.json
real_qualification_report.json
```

Prepare writes only `pre_run_plan.json`. Execute finalizes the remaining nine
files even on retained partial failure when possible. Every JSON object has an
exact schema and a `*_sha256` self-hash; every cross-artifact edge also
records the target file SHA256. Canonical JSON is compact sorted-key ASCII
with `allow_nan=False`. JSONL is concatenated `canonical_event_v5` bytes. CSV
uses the frozen `encode_outcome_csv_v5` encoder with
`role="real_confirmation"`, the real stratum name, and
`plan_frame_id="<stratum>|<frame_id>"` where `frame_id` is the exact locked
frame id.

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
synthetic_binding
generator
seed_schedule
gates
caps
failure_policy
scoped_source_sha256
environment
plan_sha256
```

Constants:

- `schema="binary_ldpc_v5_real_plan_v1"`
- `domain` contains exactly dimension 1024, frame length 256, mapping "gray",
  candidate "V5-C2", real strata, `frame_count_per_stratum=128`
- `execution` contains exact order string `"stratum_frame"`, the 384 ordered
  attempt IDs `"<stratum>|<frame_id>"`, and their SHA256
- `partition_binding` contains the exact lock path, its `partition_sha256`,
  the confirmation role-row digest, counts 128 per stratum, and the
  confirmation access API name
- `synthetic_binding` contains the Phase 3 package path, its report SHA256,
  and the verified `ready_for_real_qualification=true`
- `generator` is empty (no synthetic frame generation; frames come from the
  locked real partition)
- `seed_schedule` is exactly section 4
- `gates` is 126 successes of 128 denominators in every stratum and zero
  forbidden failures
- `caps` is complete-run 1,800 seconds plus the exact policy per-frame caps
- `failure_policy` is
  `immutable_partial_finalization_no_resume_no_rerun_no_tuning`
- `environment` contains Python, NumPy, ldpc=2.4.1, platform, and
  `test_only=false`

`scoped_source_sha256` binds each Phase-4 runner/verifier/core source file,
the confirmation-array loader, and every Phase-1/v4/Phase-2/Phase-3 source
file it invokes. Whole-worktree status is diagnostic only and is never a
verifier gate.

## 4. Roots and seeds

Prepare creates exactly 6 independent 256-bit CSPRNG roots, one Toeplitz
verification root per real stratum and verification round 0/1:

```text
bw120 round0, bw120 round1, bw180 round0, bw180 round1,
bw200 round0, bw200 round1
```

Each root record contains exactly:

```text
stratum
kind
verification_round
root_hex
root_id
```

`root_hex` is 64 lowercase hex from `secrets.token_bytes(32)`.
`root_id = SHA256(bytes.fromhex(root_hex))`. For stratum `s`, round `r`, and
locked frame id `fid` derive:

```python
label = (
  f"binary_ldpc_v5_real_qualification_v1|{s}|"
  f"round={r}|frame={fid}"
).encode("ascii")
raw = hashlib.shake_256(bytes.fromhex(root_hex) + b"\0" + label).digest(328)
bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8), bitorder="big")[:2623]
```

Then use the frozen `seed_record(bits)`. All 768 seed IDs and all 6 roots are
unique. Prepare scans the four bound predecessor packages plus the Phase 2
development package (18 roots, 9,216 seed IDs) plus the Phase 3 synthetic
package (8 roots, 512 seed IDs), and rejects overlap with any prior root or
seed ID. The plan stores the root records, overall seed count, sorted seed-ID
digest, prior root/seed digests and counts, and an isolation boolean. Seed
bytes/bit arrays are not stored.

No Phase 5 roots are created in Phase 4.

## 5. Confirmation frame arrays

Phase 1 deliberately provided no confirmation array API. Phase 4 introduces
the first read-only confirmation access in a new module (the Phase-1
partition module stays frozen):

```python
confirmation_rows(lock: Mapping) -> list[dict]
confirmation_arrays_for_frame(lock: Mapping, row: Mapping) -> tuple[np.ndarray, np.ndarray]
```

`confirmation_rows` returns detached dictionaries in exact confirmation
role-row order. `confirmation_arrays_for_frame` accepts only an exact row
present in the lock's confirmation role; a development row, changed row,
unknown row, wrong role, or out-of-range source slice raises `ValueError`
before loading arrays. Returned arrays are detached, writable, shape
`(256,)`, integer, in `[0,1023]`, and reconstructed from the same source
adapter and source locks the partition lock binds. The loader never imports
or calls a decoder.

## 6. Prepare and execute APIs

New CLIs:

```text
python -m comparison_bench.src.comparison_bench.cli.run_ldpc_v5_real_qualification
python -m comparison_bench.src.comparison_bench.cli.verify_ldpc_v5_real_qualification
```

Runner modes:

```text
--mode prepare --output-dir <exact-dir> --partition-lock <exact lock file>
--mode execute --output-dir <exact-dir>
```

Production entry points expose no test switch. Private test helpers require an
explicit fake method runner and test-owned output root; tests can never fall
through to the real decoder or official output.

Prepare requires a validated partition lock, validates the Phase 3 synthetic
package readiness, rebuilds/validates the deterministic method bundle
(codebook/selection/channel/h2/policy), creates and validates the root/seed
schedule with predecessor+development+synthetic isolation, binds
source/environment, and writes only the plan.

Execute requires the directory contain only the exact plan, validates every
plan field and current scoped hash, loads the locked confirmation frames,
then processes every attempt. It invokes the production-default
`run_ldpc_formal_v5` with the V5-C2 candidate policy, the two derived locked
seeds, `dataset_id="real_10db_<stratum>"`, and `frame_id` equal to the exact
locked frame id. Every attempt enters the CSV denominator. Transcript slices
and hashes are recorded exactly.

## 7. Failure and accounting

Formal statuses and event accounting remain the Phase-1/v5 contract. Package
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
unless its exact reason is a classified backend failure. Array load or
identity failure creates a retained nonattempted row and makes the package
non-ready. Unexpected exceptions trigger partial finalization, retain the
exact observed prefix, and make promotion false. Missing denominators are
never imputed. No outcome, event, status, disclosure, runtime, or failure is
dropped from the report.

## 8. Read-only verifier

The verifier:

- requires the exact ten-file set and canonical bytes;
- rebuilds the partition prerequisite, confirmation rows, generator absence,
  manifests, policies, source hashes, environment, seed schedule, execution
  order, and full artifact DAG;
- reconstructs the exact confirmation frame arrays from the locked source;
- validates CSV typing, transcript slices, every public Alice
  syndrome/tag/seed, outcome/accounting/status/failure mapping, denominators,
  per-stratum gates, and promotion;
- hashes files before and after and changes none;
- never imports/calls a decoder and returns
  `decoder_reexecution=false`.

Successful return contains exactly:

```text
status
run_status
outcomes
selected_candidate_id
ready_for_real_qualification
decoder_reexecution
```

`status="verified"` proves artifact integrity, not promotion. `run_status` is
`completed`, `non_promoted`, or `invalid_execution`.
`ready_for_real_qualification` is exactly `true` only when all three strata
pass their 126/128 gates with zero forbidden failures and the run completed.

## 9. Tests

- T0: compile/import/constants/lock binding/tiny seed derivation.
- T1: plan/root/seed uniqueness and predecessor+development+synthetic
  isolation; exact partition binding; confirmation-array role enforcement
  (loader never invoked for development/changed/unknown rows); no-overwrite;
  partial finalization; every raw and locally re-signed
  plan/partition/generator/binding/outcome/transcript/CSV/accounting/gate/
  report/run-manifest tamper.
- T2: complete 384-attempt fake package plus strict read-only replay, with
  success, retained failure, cap, exception, and non-promotion.

T2 replays run only against fake-runner packages in test-owned roots; the
production package and partition lock are never touched by tests.
