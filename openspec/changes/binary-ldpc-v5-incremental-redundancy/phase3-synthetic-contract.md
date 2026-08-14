# Frozen Phase 3 Synthetic Qualification Contract

## 1. Identity, path, and lifecycle

The sole package is:

```text
comparison_bench/outputs_comparison/formal_ir_methods/
  20260801_v1_binary_ldpc_v5_synthetic/
```

Constants:

- `run_id="binary_ldpc_v5_synthetic_qualification_v1"`
- `method_id="ldpc_formal_v5"`
- `role="synthetic_confirmation"`
- candidate `V5-C2` (the verified Phase 2 selected candidate)
- channel strata `adjacent_nominal`, `adjacent_stress_125`
- `frame_count_per_stratum=128`
- data-stratum placeholder `bw120` (frozen v5 CSV/run schema requires a
  bw value; `v5_plane_error_channel` hardcodes `adjacent_nominal` and treats
  every bw value identically, so the placeholder is semantics-neutral)
- stratum order `adjacent_nominal,adjacent_stress_125`
- rank order `0..127` as `f000..f127`
- execution order is stratum, then frame rank (fixed, not randomized)
- expected outcomes `256`

Prepare, main-thread review, execute, and read-only verify are separate.
Prepare and execute each occur at most once. The directory is fresh,
no-overwrite, non-resumable, and immutable after execution. A failure package
is retained and never repaired, tuned, or rerun. No real confirmation output
is created by this phase; the report's `ready_for_real_qualification` must be
exactly `true` before Phase 4 may start.

## 2. Exact artifacts

The package contains exactly these ten files:

```text
pre_run_plan.json
formal_codebook_manifest.json
formal_selection_manifest.json
formal_channel_model.json
v5_h2_manifest.json
v5_policy_manifest.json
synthetic_frame_outcomes.csv
synthetic_transcript.jsonl
synthetic_run_manifest.json
synthetic_qualification_report.json
```

Prepare writes only `pre_run_plan.json`. Execute finalizes the remaining nine
files even on retained partial failure when possible. Every JSON object has an
exact schema and a `*_sha256` self-hash; every cross-artifact edge also
records the target file SHA256. Canonical JSON is compact sorted-key ASCII
with `allow_nan=False`. JSONL is concatenated `canonical_event_v5` bytes. CSV
uses the frozen `encode_outcome_csv_v5` encoder with
`role="confirmation"`, `stratum="bw120"`, and
`plan_frame_id="<channel_stratum>|f<rank:03d>"`.

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
development_binding
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

- `schema="binary_ldpc_v5_synthetic_plan_v1"`
- `domain` contains exactly dimension 1024, frame length 256, mapping "gray",
  candidate "V5-C2", channel strata, `frame_count_per_stratum=128`, and
  `data_stratum="bw120"`
- `execution` contains exact order string `"stratum_rank"`, the 256 ordered
  attempt IDs `"<stratum>|f<rank:03d>"`, and their SHA256
- `development_binding` contains the exact verified Phase 2 package path,
  per-artifact SHA256 (codebook/selection/channel/h2/policy manifests,
  development selection/report/run manifest), the selection's
  `selected_candidate_id="V5-C2"`, `ready_for_synthetic_prepare=true`, and
  the development `run_status="completed"`
- `generator` is exactly section 5
- `seed_schedule` is exactly section 4
- `gates` is 126 successes of 128 denominators in every stratum and zero
  forbidden failures
- `caps` is complete-run 1,800 seconds plus the exact policy per-frame caps
- `failure_policy` is
  `immutable_partial_finalization_no_resume_no_rerun_no_tuning`
- `environment` contains Python, NumPy, ldpc=2.4.1, platform, and
  `test_only=false`

`scoped_source_sha256` binds each Phase-3 runner/verifier/core source file
and every Phase-1/v4/Phase-2 source file it invokes. Whole-worktree status is
diagnostic only and is never a verifier gate.

## 4. Roots and seeds

Prepare creates exactly 8 independent 256-bit CSPRNG roots:

- `bob` and `delta` roots per channel stratum (4) for frame generation;
- `toeplitz` roots per channel stratum and verification round 0/1 (4) for
  the 2623-bit Toeplitz seeds.

Each root record contains exactly:

```text
stratum
kind
verification_round (toeplitz only, else absent)
root_hex
root_id
```

`root_hex` is 64 lowercase hex from `secrets.token_bytes(32)`.
`root_id = SHA256(bytes.fromhex(root_hex))`. For channel stratum `s`,
verification round `r`, and rank `i` derive:

```python
label = (
  f"binary_ldpc_v5_synthetic_qualification_v1|{s}|"
  f"round={r}|rank={i}"
).encode("ascii")
raw = hashlib.shake_256(bytes.fromhex(root_hex) + b"\0" + label).digest(328)
bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8), bitorder="big")[:2623]
```

Then use the frozen `seed_record(bits)`. All 512 seed IDs and all 8 roots are
unique. Prepare scans the four bound predecessor packages (same frozen
whitelist and extraction as Phase 2) plus the Phase 2 development package's
18 roots and 9,216 seed IDs, and rejects overlap with any prior root or seed
ID. The plan stores the root records, overall seed count, sorted seed-ID
digest, prior root/seed digests and counts, and an isolation boolean. Seed
bytes/bit arrays are not stored.

No Phase 4 roots are created in Phase 3.

## 5. Generator

Frame generation for channel stratum `s` uses the frozen v4 channel model's
`probabilities[s]` table:

```python
bob = PCG64(bob_root).integers(0, 1024, size=(128, 256), dtype=np.uint16)
u = PCG64(delta_root).random((128, 256))
delta = np.where(u < p_minus, -1,
                 np.where(u < p_minus + p_plus, 1, 0)).astype(np.int16)
alice = ((bob.astype(np.int16) + delta) % 1024).astype(np.uint16)
```

with fixed delta order `minus_one,plus_one,zero` and PCG64 seeds derived
from the domain-separated root digests (same derivation style as the v4
synthetic package, with the v5 run-id domain). `bob` is uniform over the
dimension; errors are adjacent-bin +/-1 exactly as the error-channel prior
models. The nominal stratum's injected distribution therefore exactly matches
the frozen `adjacent_nominal` prior; the stress stratum injects the
`adjacent_stress_125` table (1.25x) against the same nominal prior and is the
deliberate stress arm.

## 6. Prepare and execute APIs

New CLIs:

```text
python -m comparison_bench.src.comparison_bench.cli.run_ldpc_v5_synthetic_qualification
python -m comparison_bench.src.comparison_bench.cli.verify_ldpc_v5_synthetic_qualification
```

Runner modes:

```text
--mode prepare --output-dir <exact-dir> --development-dir <verified phase2 dir>
--mode execute --output-dir <exact-dir>
```

Production entry points expose no test switch. Private test helpers require an
explicit fake method runner and test-owned output root; tests can never fall
through to the real decoder or official output.

Prepare requires the verified Phase 2 development directory
(`verify_ldpc_v5_development` returns `run_status="completed"` and
`ready_for_synthetic_prepare=true`), rebuilds/validates the deterministic
method bundle (codebook/selection/channel/h2/policy), creates and validates
the root/seed schedule with predecessor+development isolation, binds
source/environment, and writes only the plan.

Execute requires the directory contain only the exact plan, validates every
plan field and current scoped hash, generates the frozen synthetic frames,
then processes every attempt. It invokes the production-default
`run_ldpc_formal_v5` with the V5-C2 candidate policy, the two derived locked
seeds, `dataset_id="synthetic_<channel_stratum>"`, `frame_id=plan_frame_id`,
and data-stratum placeholder `bw120`. Every attempt enters the CSV
denominator. Transcript slices and hashes are recorded exactly.

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
unless its exact reason is a classified backend failure. Frame generation or
identity failure creates a retained nonattempted row and makes the package
non-ready. Unexpected exceptions trigger partial finalization, retain the
exact observed prefix, and make promotion false. Missing denominators are
never imputed. No outcome, event, status, disclosure, runtime, or failure is
dropped from the report.

## 8. Read-only verifier

The verifier:

- requires the exact ten-file set and canonical bytes;
- rebuilds the development prerequisite, generator, manifests, policies,
  source hashes, environment, seed schedule, execution order, and full
  artifact DAG;
- reconstructs the exact synthetic frames from the frozen generator;
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
`ready_for_real_qualification` is exactly `true` only when both strata pass
their 126/128 gates with zero forbidden failures and the run completed.

## 9. Tests

- T0: compile/import/constants/generator determinism/tiny seed derivation.
- T1: plan/root/seed uniqueness and predecessor+development isolation; exact
  binding; no-overwrite; partial finalization; every raw and locally
  re-signed plan/generator/binding/outcome/transcript/CSV/accounting/gate/
  report/run-manifest tamper.
- T2: complete 256-attempt fake package plus strict read-only replay, with
  success, retained failure, cap, exception, and non-promotion.

T2 replays run only against fake-runner packages in test-owned roots; the
production package is never touched by tests.
