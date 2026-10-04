# Frozen v5 Predecessor Contract

P1-01 binds every file listed below by exact path, filename set, bytes, and
SHA256. Extra, missing, renamed, or changed files fail before a v5 output
exists.

Base root:

`comparison_bench/outputs_comparison/formal_ir_methods`

## 1. Corrected v4 development

Directory: `20260727_v2_binary_ldpc_v4_development`

| File | SHA256 |
|---|---|
| `development_plane_outcomes.csv` | `c48d00ba68fe37e2104794348734d6c22a5f295d3e90826362f9e094124d3018` |
| `development_report.json` | `31f51cec0625fe7be0f36a4b746de37e1a512a7bc63c182501baaedbe5b6bfa5` |
| `development_run_manifest.json` | `7ff6cb96ef25be36c92d54c10e74a75e757a07a11227c0444b4193ff5dd5b713` |
| `development_selection.json` | `5d3757f7e36e117877e9c2d75fa1e90496d83cc080171cfaa4f3299c44b6b4dd` |
| `pre_run_plan.json` | `0b690fe2e4ac56cf1d742368877b07f72ad3cc84dc0c7de894caf1c3a9919255` |
| `v4_candidate_manifest.json` | `786b48287f0b453a668c1ae1bdab2126aa7d13aeb94439860b80899a34687500` |
| `v4_channel_model.json` | `83a80a2db8d7b7cacc63e5e7531ecc7d4bd4e93605af53aa2fa987257d15cf6c` |

Call
`verify_ldpc_v4_development_v2.verify_output(path)` under the accepted bounded
replay context. Require exactly:

- `status=verified`
- `run_status=completed`
- `ready_for_synthetic_prepare=true`
- `decoder_reexecution=false`
- `scope=predecessor_source_model_codebook_development_selection_accounting`

## 2. Promoted v4 synthetic

Directory: `20260728_v2_binary_ldpc_v4_synthetic`

| File | SHA256 |
|---|---|
| `formal_channel_model.json` | `83a80a2db8d7b7cacc63e5e7531ecc7d4bd4e93605af53aa2fa987257d15cf6c` |
| `formal_codebook_manifest.json` | `786b48287f0b453a668c1ae1bdab2126aa7d13aeb94439860b80899a34687500` |
| `formal_frame_outcomes.csv` | `3dd169aa692aba94232abf5018bbaee819645ac210a79c466b1702e0500d6c93` |
| `formal_qualification_report.json` | `57268f73d4fa7dcbce01c2e63066af6d177502b415aa076312dd3a9c7a3f804a` |
| `formal_run_manifest.json` | `3a142ff8d6d37c665ac8e0a1a8541fe9b36133ea10e75e3b55cbdc044eb49fa6` |
| `formal_selection_manifest.json` | `5d3757f7e36e117877e9c2d75fa1e90496d83cc080171cfaa4f3299c44b6b4dd` |
| `formal_transcript.jsonl` | `c2518fd89ad9a9ca3f884e74419e5801b42c956d3f027d90d9044167b7782b0f` |
| `pre_run_plan.json` | `6a8c8c11afe7e13061c876a8955592f78911fc12883558fa9ccb3546391874cc` |

Call `verify_ldpc_v4_synthetic_qualification.verify_output(path)` under the
same bounded replay context. Require `status=verified`,
`run_status=completed`, `promoted=true`, `outcomes=256`, and
`decoder_reexecution=false`.

## 3. Non-promoted v4 16 dB

Directory: `20260729_v1_binary_ldpc_v4_16db_transfer`

| File | SHA256 |
|---|---|
| `formal_channel_model.json` | `83a80a2db8d7b7cacc63e5e7531ecc7d4bd4e93605af53aa2fa987257d15cf6c` |
| `formal_codebook_manifest.json` | `786b48287f0b453a668c1ae1bdab2126aa7d13aeb94439860b80899a34687500` |
| `formal_frame_outcomes.csv` | `08a99fddb910afce675c05d9a7388165f772c98db2c60e396853600e341dcb73` |
| `formal_qualification_report.json` | `c9986ca024c23d3111793890688e352062107686db1a634653a6e4e430359e97` |
| `formal_run_manifest.json` | `64a92178f17e5e669370585a3a72c88ccae986835ed06a53b68de0488bda7550` |
| `formal_selection_manifest.json` | `5d3757f7e36e117877e9c2d75fa1e90496d83cc080171cfaa4f3299c44b6b4dd` |
| `formal_transcript.jsonl` | `b3dd574ae9f9bade050a71bdf3c4fa22b70498aa6e4b421ecb98dbb749607f75` |
| `pre_run_plan.json` | `ce7a582c34b5a99846e5da6631b836bbc8d950d08f760721aa9a7a2435512eee` |
| `real_data_lock.json` | `9852dad0d57a226913a2391650ab1829b3d155f8cc42908d6196543799ae1bc2` |

Call `verify_ldpc_v4_16db_transfer_qualification.verify_output(path)`.
Require `status=verified`, `run_status=completed`, `promoted=false`,
`outcomes=384`, `decoder_reexecution=false`, and `source_relocation=true`.
Also reconstruct exact successes 125/128, 128/128, 128/128 and zero forbidden.

## 4. Invalid-pre-execute v4 10 dB v1

Directory: `20260729_v1_binary_ldpc_v4_10db_transfer`

| File | SHA256 |
|---|---|
| `pre_run_plan.json` | `dae9d27a068bf9b15f25ae684bd3cf290623524b0e92af8989869579b0ac523c` |
| `real_data_lock.json` | `6596316074b0e473de26ba44a87556016f23b082dc36239e06a65fa4e7d11baf` |

There is intentionally no execute verifier call. Require exactly two
canonical JSON files, valid local self-hashes, production `_test_only=false`,
v1 run/schema identity, source lock relation, 384 selected frames, and no
outcome/transcript/run/report files. Record status only as
`invalid_pre_execute_self_collision`; never call its execute function.

## 5. Non-promoted v4 10 dB v2

Directory: `20260729_v2_binary_ldpc_v4_10db_transfer`

| File | SHA256 |
|---|---|
| `formal_channel_model.json` | `83a80a2db8d7b7cacc63e5e7531ecc7d4bd4e93605af53aa2fa987257d15cf6c` |
| `formal_codebook_manifest.json` | `786b48287f0b453a668c1ae1bdab2126aa7d13aeb94439860b80899a34687500` |
| `formal_frame_outcomes.csv` | `7e906a5749b5f8c9d126798f2975ba5caec3cbd4592aef13ff50e7a39eb54d41` |
| `formal_qualification_report.json` | `960e59f6f5b8acee191d6572421cc8d928707c771b99267dcf80a1a31d02a343` |
| `formal_run_manifest.json` | `3a75b74227a84a9e8f6aea80e10af2477656ad89cbfe310fbbea5b96ddf1d67c` |
| `formal_selection_manifest.json` | `5d3757f7e36e117877e9c2d75fa1e90496d83cc080171cfaa4f3299c44b6b4dd` |
| `formal_transcript.jsonl` | `f1decb49c9209a4a546eade3b158776853f997422dd9e56d7967022b0508aedf` |
| `pre_run_plan.json` | `ff7d5f987a3eec19d30a92c5781d77ba612b7305530f38744b6bd9a9872c63ed` |
| `real_data_lock.json` | `6596316074b0e473de26ba44a87556016f23b082dc36239e06a65fa4e7d11baf` |

Call `verify_ldpc_v4_10db_transfer_qualification_v2.verify_output(path)`.
Require `status=verified`, `run_status=completed`, `promoted=false`,
`outcomes=384`, `decoder_reexecution=false`, and `source_relocation=true`.
Also reconstruct exact successes 125/128, 127/128, 128/128 and zero forbidden.

## 6. Replay implementation rule

The v5 binder may reuse the already accepted bounded matrix/candidate/CSV
replay context in new v5 code. It must not modify historical verifier source.
All temporary patches restore in `finally`; cached results are keyed by exact
path plus the complete expected artifact-hash tuple. The verifier APIs remain
read-only and no decoder is reexecuted.

## 7. Canonical predecessor-binding record and API

The new v5 predecessor module exports exactly:

```python
build_predecessor_binding(base_root: pathlib.Path) -> dict
validate_predecessor_binding(
    record: Mapping[str, object],
    base_root: pathlib.Path,
) -> None
```

Both functions fail closed. `build_predecessor_binding` performs every file
and replay check in sections 1--6 before returning. `validate` first validates
the supplied schema/self-hash, then independently rebuilds the record from
`base_root` and requires exact object equality. Neither function writes a
file, invokes a decoder, accepts `_test_only`, or resolves a default
production root.

The returned record contains exactly:

```text
schema
contract_id
base_root_policy
packages
binding_sha256
```

Constants:

- `schema="binary_ldpc_v5_predecessor_binding_v1"`
- `contract_id="binary_ldpc_v5_five_predecessors_20260729"`
- `base_root_policy="caller_supplied_unhashed_location"`

`binding_sha256` is SHA256 of compact sorted-key ASCII JSON of the complete
record excluding only `binding_sha256`, with `allow_nan=False`.

`packages` contains exactly five records in section order. Each record has
exactly:

```text
package_id
directory_name
verification_mode
verifier
files
verified_result
```

The fixed `package_id` values in order are:

```text
v4_corrected_development
v4_promoted_synthetic
v4_16db_non_promoted
v4_10db_v1_invalid_pre_execute
v4_10db_v2_non_promoted
```

`directory_name` is the exact basename named in the corresponding section.
No absolute path, drive, resolved location, mtime, inode, or directory
separator enters the record or any hash.

For sections 1, 2, 3, and 5:

- `verification_mode="read_only_verifier"`
- `verifier` is the exact dotted module plus `.verify_output`
- `verified_result` contains exactly the required result keys and values
  listed in that section, with the three per-stratum success counts and zero
  forbidden count additionally represented for sections 3 and 5 as:

```text
successes_by_stratum
forbidden_failure_count
```

`successes_by_stratum` is an object in fixed semantic form with keys
`bw120`, `bw180`, `bw200`; JSON key sorting supplies canonical byte order.
The binder may receive additional diagnostic keys from a historical verifier
but must neither record them nor use them as a substitute for any required
key.

The exact verifier strings in package order (with section 4 omitted) are:

```text
comparison_bench.src.comparison_bench.cli.verify_ldpc_v4_development_v2.verify_output
comparison_bench.src.comparison_bench.cli.verify_ldpc_v4_synthetic_qualification.verify_output
comparison_bench.src.comparison_bench.cli.verify_ldpc_v4_16db_transfer_qualification.verify_output
comparison_bench.src.comparison_bench.cli.verify_ldpc_v4_10db_transfer_qualification_v2.verify_output
```

The section-3 success object is
`{"bw120":125,"bw180":128,"bw200":128}` and the section-5 object is
`{"bw120":125,"bw180":127,"bw200":128}`; both have
`forbidden_failure_count=0`.

For section 4:

- `verification_mode="canonical_semantic_only"`
- `verifier=null`
- `verified_result` contains exactly:

```text
status
canonical_json_files
production_test_only
selected_frames
forbidden_output_files_present
```

with values
`"invalid_pre_execute_self_collision"`,
`["pre_run_plan.json","real_data_lock.json"]`, `false`, `384`, and `[]`.
The semantic checks listed in section 4 must all pass before this normalized
result is emitted.

`files` contains one record per exact file in the corresponding table,
lexicographically ordered by filename. Each file record contains exactly:

```text
name
size_bytes
sha256
```

`size_bytes` is read from the bound bytes and `sha256` must equal the frozen
table value. Extra or missing filenames fail before replay. Location is never
stored.

Tests cover record and package ordering, every field, extra/missing file,
byte/size/hash drift, locally re-signed outer hashes, normalized replay-result
drift, verifier identity drift, absolute-path injection, relocation to a
different caller-supplied root, detached copies, and zero writes/decoder
reexecution.

## 8. Accepted bounded replay adapter

Directly invoking the four historical verifiers serially is rejected: on the
accepted Windows environment it exceeded both 600-second and 1,800-second
caller limits without returning. This is a replay-orchestration defect, not a
historical evidence failure.

`build_predecessor_binding` must enter exactly one outer
`run_ldpc_v4_16db_transfer_qualification._replay_matrix_cache()` context
before the package loop and keep it active across all five package checks in
section order. Historical verifier functions remain unmodified and are still
called exactly once each. Their own nested replay contexts are permitted.

Before entering the context, bind and verify:

- all five exact filename sets and file hashes;
- the shared v4 selection hash
  `5d3757f7e36e117877e9c2d75fa1e90496d83cc080171cfaa4f3299c44b6b4dd`;
- the shared v4 codebook hash
  `786b48287f0b453a668c1ae1bdab2126aa7d13aeb94439860b80899a34687500`;
- the shared channel hash
  `83a80a2db8d7b7cacc63e5e7531ecc7d4bd4e93605af53aa2fa987257d15cf6c`.

The outer context may cache only the 40 exact `(plane_id,candidate_id)`
matrices and 40 exact candidate records already bounded by that accepted
context. It may use the canonical linear CSV reader from that context. It
must not cache verifier return values, source payloads, transcript results, or
gate conclusions. Every matrix/candidate accessor returns a detached copy.
All patched references restore in `finally`, including verifier exceptions.

The T3 acceptance invocation runs the builder in one task-owned process with
a 900-second outer timeout. Completion within that envelope with all four
normalized verifier results is required. Timeout, cache overflow, restoration
failure, or any verifier mismatch fails P1-01; no prefilled replay result,
skip flag, or historical-result trust path is allowed.

Tests prove one call per historical verifier, cache maxima, mutation
isolation, exception restoration, exact normalized results, no decoder
reexecution, no file changes, and the 900-second acceptance command.
