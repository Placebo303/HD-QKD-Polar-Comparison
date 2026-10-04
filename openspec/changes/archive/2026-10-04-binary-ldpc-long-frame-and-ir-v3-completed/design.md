# Design: Binary LDPC Long-Frame Foundation

## Identity and Isolation

The first work package adds
`comparison_bench.formal_ir.codebook_long_v3`. It is an offline construction
component, not a runnable formal method. `ldpc_formal_v2`, its codebooks,
confirmation evidence, and output schema remain unchanged.

## Frozen Domain

- Block lengths: 256, 512, 1024 bits per bit plane.
- Prefix check fractions: 1/2, 5/8, 3/4, 7/8.
- Plane IDs: 0 through 9.
- Candidate IDs: 0 through 3.
- Construction identity:
  `binary_ldpc_protograph_accumulator_candidate_v3`, version `1`.

The family is explicitly `candidate_only_not_qualified`. It is
protograph/accumulator-inspired and SHALL NOT be described as a selected
production QC-LDPC family.

## Deterministic Nested Construction

Each candidate is one `(7n/8) x n` binary master matrix. Every advertised rate
is an exact leading-row prefix of that master. Let `m0=n/2`, `t=n/8`, and
`mmax=7n/8`. Construction SHALL use the following exact algorithm:

1. Create an all-zero `mmax x n` uint8 matrix and set `H[i,i]=1` for every
   `0<=i<mmax`.
2. Create one PCG64 generator from the first 16 big-endian SHA256 bytes of
   compact JSON containing construction identity, version, n, plane, and
   candidate.
3. Draw one permutation `p` of `0..m0-1`. For each `0<=j<m0`, column `m0+j`
   receives early supports at the unordered pair
   `{p[j],p[(j+1) mod m0]}`. Because `m0+j` spans the full half-open interval
   `[m0,n)`, this step covers both `[m0,mmax)` and the tail `[mmax,n)` inside
   the n/2 prefix. The cycle edges are unique because `m0>=3`.
4. Draw three independent integer shifts with `rng.integers(0,t)`, retaining
   their exact draw order. For layer `0<=l<3` and `0<=j<t`, row
   `m0+l*t+j` receives one additional support at column
   `mmax+((j+shift[l]) mod t)`. These are additional third-through-fifth
   supports for tail columns; they are not the tail columns' first supports.

The systematic pivots prove full row rank for every prefix. The cycle covers
every early row twice and gives every non-systematic column a distinct
two-support signature at the n/2 prefix. The three shifted late layers are
balanced over the tail columns.

Every prefix SHALL fail closed unless:

- rank equals its row count;
- zero columns and duplicate columns are both zero;
- row weights are within `[2,3]`;
- column weights are within `[1,5]`.

Four-cycle and ACE-style values are diagnostics, not validity gates.

This work package does not select a candidate using FER. Structural scores are
diagnostic only.

## Canonical Encoding

Canonical bytes SHALL be:

1. ASCII `HGF2V3`;
2. little-endian uint32 `(m_checks, n)`;
3. C-order uint8 matrix bytes.

The parser SHALL reject the wrong magic, wrong length, non-binary values,
unsupported n, unsupported prefix rows, or trailing bytes.

## Manifest

`candidate_manifest()` SHALL describe all 3 lengths x 10 planes x 4
candidates. It SHALL contain construction identity/version, domain, per-prefix
shape/rank/hash and structural diagnostics, and a canonical compact-JSON
manifest hash. Verification SHALL reconstruct the entire deterministic
manifest and reject any mutation.

The manifest is in-memory in this work package. No production result directory
or qualification artifact is created.

## Structural Diagnostics

Each prefix SHALL report at least rank, zero/duplicate columns, row/column
weight bounds, exact 4-cycle count, and an ACE-style cycle-support diagnostic
clearly labeled as a proxy. No metric is decoded FER or promotion evidence.

For exact 4-cycle count, let `o(i,j)` be the number of common check rows for
columns `i<j`; report `sum(comb(o(i,j),2))`.

Define the frozen ACE-style proxy only over column pairs with `o(i,j)>=2`.
For each such pair, its proxy value is
`max(weight(i)-2,0)+max(weight(j)-2,0)`. Report:

- `ace_4cycle_proxy_min`: the minimum pair value, or `null` when no pair forms
  a 4-cycle;
- `ace_4cycle_proxy_sum`: the sum of the pair value multiplied by
  `comb(o(i,j),2)`;
- `ace_4cycle_proxy_definition`: the exact stable string
  `column_pair_extrinsic_degree_v1`.

These fields are explicitly proxies and SHALL NOT be called ACE spectrum,
minimum distance, trapping-set evidence, FER, or decoding evidence.

## Resource Boundary

Manifest construction and its focused test SHALL complete under 120 seconds on
the project host. Verification must test actual matrix rank for representative
candidates at all three lengths.

## Phase 2: Sacrificed-Development FER Kernel

Phase 2 adds
`comparison_bench.formal_ir.long_v3_development`. It is an in-memory
development evaluator, not a qualification runner. It SHALL import the Phase 1
candidate matrices and SHALL NOT modify either v2 module.

### Frozen Policy and Backend

`canonical_development_policy(n)` SHALL return exactly:

- `dependency_version="2.4.1"`;
- `max_iter=50`;
- `bp_method="minimum_sum"`;
- `ms_scaling_factor=1.0`;
- `schedule="serial"`;
- `omp_thread_count=1`;
- `serial_schedule_order=[0,...,n-1]`;
- `osd_method="OSD_0"`;
- `osd_order=0`;
- `prefix_ids=["p050","p0625","p075","p0875"]`.

The compact-JSON SHA256 of the policy without its hash SHALL be returned as
`policy_id`. No decoder fallback, OSD tuning, runtime-based selection, or
silent parameter change is permitted.

Only `max_iter`, `bp_method`, `ms_scaling_factor`, `schedule`,
`omp_thread_count`, `serial_schedule_order`, `osd_method`, `osd_order`, plus
the separately supplied clipped `error_rate`, SHALL be passed to the decoder
constructor. Identity/version/prefix/hash fields are metadata, not kwargs.

### Sacrificed Synthetic Development Data

`generate_sacrificed_development(n, plane_id, p, frame_count=16)` SHALL:

- accept only the frozen n/plane domain, `p` exactly `.01` or `.02`, and
  `frame_count=16`;
- derive two independent PCG64 seeds from the first 16 big-endian SHA256 bytes
  of compact JSON containing construction ID/version, role
  `sacrificed_development_only`, kind `alice` or `noise`, n, plane, p encoded
  as `p001` or `p002`, and frame count;
- generate Alice with one
  `rng.integers(0,2,size=(16,n),dtype=np.uint8)` call;
- generate noise with one
  `(rng.random(size=(16,n)) < p).astype(np.uint8)` call;
- return Alice, Bob=`Alice XOR noise`, exact seeds/IDs, ordered frame IDs,
  source hash over canonical Alice/Bob bytes, error count, total bits, and
  `p_hat=error_count/total_bits`.

Frame IDs SHALL be
`dev_n{n}_plane{plane_id:02d}_{p_id}_f{index:02d}` in index order. Each
128-bit seed SHALL be stored as 32 lowercase hex characters and its seed ID
SHALL be SHA256 of the exact 16 big-endian seed bytes. The source hash preimage
SHALL be:

`compact_json(metadata_without_arrays_or_source_hash) + b"\nALICE\n" +
alice.tobytes(order="C") + b"\nBOB\n" + bob.tobytes(order="C")`.

The returned mapping SHALL use keys `role`, `n`, `plane_id`, `p`, `p_id`,
`frame_count`, `frame_ids`, `alice_seed_hex`, `alice_seed_id`,
`noise_seed_hex`, `noise_seed_id`, `error_count`, `total_bits`, `p_hat`,
`source_sha256`, `alice_frames`, and `bob_frames`.

The data role and every returned record SHALL say
`sacrificed_development_only`. These frames MAY be inspected for exact
development FER and SHALL never be reused as confirmation.

### Incremental Candidate Evaluation

`evaluate_candidate(alice_frames, bob_frames, *, n, plane_id, candidate_id,
p_hat, stratum_id, frame_ids, decoder_factory=None)` SHALL require matching
16-by-n uint8 binary arrays, exact ordered frame IDs, a finite
`0<=p_hat<.5`, and stratum `p001` or `p002`.

For each frame it SHALL use one fixed candidate master and process prefix IDs
in frozen order. At each round:

1. Alice's disclosure becomes the current prefix row count, not the sum of all
   prefixes, because later syndromes extend the earlier row prefix.
2. Form `delta=H*Alice XOR H*Bob` over GF(2).
3. Instantiate the pinned decoder with the exact policy and `error_rate` equal
   to `clip(p_hat,1e-4,.49)`.
4. Decode an n-bit error vector; reject wrong length/nonbinary output.
5. Require `H*error==delta`; otherwise record
   `development_syndrome_inconsistent` and stop the frame.
6. Correct Bob locally. Exact equality to Alice produces
   `development_exact_success` and stops at that prefix. A syndrome-consistent
   but inexact correction continues to the next prefix.

If all four rounds are consistent but inexact, status is
`development_decode_failed`. Constructor/decode exceptions produce
`development_decoder_error`. Invalid function arguments SHALL raise
`ValueError` before any outcome is returned. A missing/mismatched backend with
otherwise valid arguments SHALL return exactly 16 retained
`development_backend_unavailable` rows with `attempted=false`, empty terminal
prefix, zero rounds, zero disclosure, and exact-match false. Every other frame
row SHALL have `attempted=true` and retain exactly these keys:
`n`, `plane_id`, `candidate_id`, `stratum_id`, `frame_id`, `attempted`,
`status`, `terminal_prefix_id`, `rounds_attempted`,
`syndrome_bits_disclosed`, `exact_match`, `policy_id`, `p_hat`,
`backend_identity`, and `runtime_s`. Runtime SHALL NOT affect selection.

When `decoder_factory` is omitted, the function SHALL require installed
`ldpc==2.4.1` and use `ldpc.BpOsdDecoder`; mismatch fails closed before frame
attempts. A supplied factory is test-only and SHALL be recorded as
`test_injected`.

### Candidate Selection

`select_candidate(candidate_outcomes)` takes one flat sequence of outcome
rows. It SHALL require exactly the four frozen candidate IDs, both strata,
exactly 16 unique frame rows per candidate/stratum, identical ordered frame
IDs across candidates within each stratum, one n, one plane, one policy ID,
identical p_hat per stratum, and only the statuses
`development_exact_success`, `development_decode_failed`,
`development_syndrome_inconsistent`, `development_decoder_error`, and
`development_backend_unavailable`. Duplicate or missing identities and any
`attempted`/status inconsistency SHALL raise `ValueError`.

For each candidate compute successes in `p001` and `p002`, total syndrome bits,
and status counts. Select once per n/plane using the exact lexicographic tuple:

`[-min(p001_successes,p002_successes), -(p001_successes+p002_successes),
total_syndrome_bits, candidate_id]`.

The result SHALL contain all aggregates, the selected candidate, the tuple,
and a compact-JSON selection hash. The hash preimage is the result without its
`selection_sha256` key. Aggregates SHALL be keyed by decimal candidate ID and
contain `successes_by_stratum`, `total_successes`,
`total_syndrome_bits_disclosed`, and `status_counts`. Runtime and structural
proxies SHALL NOT enter this tuple. This is development selection only, not
qualification.

### Phase 2 Resource Boundary

The focused unit test SHALL use injected deterministic test decoders and
complete under 30 seconds. Phase 2 SHALL NOT execute the full pinned-backend
3-length x 10-plane development sweep or write a result artifact.

## Phase 3A: Bounded Pinned-Backend Pilot

Before designing or running the full development sweep, execute exactly one
in-memory feasibility pilot using the accepted Phase 2 API:

- n=256;
- plane_id=0;
- candidate_id=0;
- p=.01 / stratum `p001`;
- the exact 16 sacrificed frames from
  `generate_sacrificed_development(256,0,.01)`;
- `decoder_factory=None`, therefore requiring installed `ldpc==2.4.1`;
- external wall timeout 120 seconds for the complete Python process.

The pilot SHALL print one compact sorted JSON object containing only:
`role="backend_feasibility_pilot_not_selection"`, n, plane/candidate/stratum,
source SHA256, policy ID, backend identities, status counts, terminal-prefix
counts, exact-success count, total syndrome bits, summed diagnostic runtime,
and process elapsed time.

It SHALL NOT write files, select a candidate, compare lengths, inspect
confirmation/real data, or support a FER/promotion claim. Timeout, exception,
backend unavailable, or any noncanonical outcome is retained as pilot failure
and must return to the planner before a full sweep is specified.

## Phase 3B: Full Development Sweep Runner and Read-Only Verifier

Phase 3B implements tooling only. It SHALL NOT execute the production sweep.

### Files and Entry Points

Add exactly:

- `comparison_bench/src/comparison_bench/cli/run_ldpc_long_v3_development.py`;
- `comparison_bench/src/comparison_bench/cli/verify_ldpc_long_v3_development.py`;
- `comparison_bench/tests/test_ldpc_long_v3_sweep.py`.

The runner CLI SHALL be:

`python -m comparison_bench.src.comparison_bench.cli.run_ldpc_long_v3_development
--output-dir <fresh-path> --mode prepare|execute`

The verifier CLI SHALL be:

`python -m comparison_bench.src.comparison_bench.cli.verify_ldpc_long_v3_development
--output-dir <path>`.

### Frozen Production Grid

The production plan SHALL contain exactly:

- run ID `20260726_v1_binary_ldpc_long_v3_development`;
- role `sacrificed_development_only`;
- n in `[256,512,1024]`, then plane `0..9`, then candidate `0..3`, then
  stratum `[p001,p002]`, in that execution order;
- 16 canonical frames per candidate/stratum;
- 3840 expected outcome rows and 30 expected selections;
- the accepted Phase 2 canonical policies and selection tuple;
- pinned `ldpc==2.4.1`;
- internal total elapsed cap 600 seconds, checked before and after every
  candidate/stratum slice;
- required external process timeout 660 seconds;
- exact SHA256 of the Phase 1 and Phase 2 modules, runner, verifier, and the
  complete deterministic candidate manifest;
- `test_only=false`.

The plan SHALL be compact sorted JSON with `plan_sha256` equal to SHA256 of the
same mapping without that field.

The plan SHALL have exactly these keys:
`schema_version="binary_ldpc_long_v3_development_plan_v1"`, `run_id`, `role`,
`test_only`, `grid`, `policies`, `candidate_manifest_sha256`,
`backend_requirement`, `internal_elapsed_cap_s`,
`required_external_timeout_s`, `expected_outcome_count`,
`expected_selection_count`, `code_sha256`, and `plan_sha256`.

`grid` SHALL have exactly `block_lengths`, `plane_ids`, `candidate_ids`,
`stratum_ids`, `frames_per_stratum`, and `execution_order`, with
`execution_order="n,plane_id,candidate_id,stratum_id,frame_index"`.
`policies` is keyed by decimal n and equals
`canonical_development_policy(n)`. `code_sha256` SHALL have exact keys
`codebook_long_v3.py`, `long_v3_development.py`,
`run_ldpc_long_v3_development.py`, and
`verify_ldpc_long_v3_development.py`.

The private test plan SHALL use the same schema with run ID
`test_only_binary_ldpc_long_v3_development`, n `[256]`, plane `[0]`, the same
four candidates/two strata/16 frames, expected counts 128/1,
`backend_requirement="test_injected"`, internal cap 30, external timeout 60,
and `test_only=true`.

### Two-Step No-Overwrite Execution

`--mode prepare` SHALL require that the output directory does not exist,
create it exclusively, and write only `pre_run_plan.json`. It SHALL perform no
decode.

`--mode execute` SHALL require that the directory contains exactly the one
plan, validate its self-hash, exact production grid, code hashes, candidate
manifest hash, backend version, and `test_only=false`, then exclusively create
the remaining artifacts. Any mismatch stops before decoding and does not
modify the plan.

Existing directories/artifacts SHALL never be overwritten. Repeating prepare
or execute SHALL fail.

### Exact Artifact Set and DAG

A completed or exception-finalized execution SHALL contain exactly:

1. `pre_run_plan.json`;
2. `long_v3_candidate_manifest.json`;
3. `development_outcomes.csv`;
4. `development_selections.json`;
5. `development_run_manifest.json`;
6. `development_report.json`.

Candidate manifest bytes SHALL be compact sorted JSON from
`candidate_manifest()`.

All JSON artifacts SHALL be UTF-8 compact sorted JSON with no trailing newline.
File SHA256 values cover exact bytes. A `*_content_sha256` or self-hash field
covers compact JSON of that mapping with its own hash field omitted.

Outcome CSV SHALL have exactly the Phase 2 outcome keys in this order:
`n,plane_id,candidate_id,stratum_id,frame_id,attempted,status,
terminal_prefix_id,rounds_attempted,syndrome_bits_disclosed,exact_match,
policy_id,p_hat,backend_identity,runtime_s`, followed by
`role,source_sha256`. Boolean values SHALL be lowercase `true|false`;
floats SHALL use Python `repr(float(value))`; rows SHALL follow the production
execution order. CSV SHALL use UTF-8, comma delimiter, minimal quoting, one
header, and `\n` line terminators.

Selections JSON SHALL contain `role`, `selection_count`, an ordered
`selections` list by n then plane, and `selections_sha256`. The hash SHALL cover
compact JSON of the mapping without its hash.

Its exact keys SHALL be
`schema_version="binary_ldpc_long_v3_development_selections_v1"`, `run_id`,
`role`, `test_only`, `plan_sha256`, `outcomes_sha256`, `selection_count`,
`selections`, and `selections_sha256`. Each list entry is the exact mapping
returned by accepted `select_candidate`.

The run manifest SHALL contain run/role/status/stop reason, UTC start/end,
actual argv, backend/Python/NumPy versions, process elapsed, expected/observed
counts, code hashes, and SHA256/byte lengths of the plan, candidate manifest,
outcomes, and selections. `manifest_content_sha256` SHALL hash compact JSON
without itself.

Its exact keys SHALL be
`schema_version="binary_ldpc_long_v3_development_manifest_v1"`, `run_id`,
`role`, `test_only`, `status`, `stop_reason`, `utc_start`, `utc_end`,
`actual_argv`, `backend_identity`, `python_version`, `numpy_version`,
`dependency_version`, `process_elapsed_s`, `expected_outcome_count`,
`observed_outcome_count`, `expected_selection_count`,
`observed_selection_count`, `code_sha256`, `artifact_index`, and
`manifest_content_sha256`.

UTC SHALL use `YYYY-MM-DDTHH:MM:SS.ffffffZ`. Production `actual_argv` is the
actual process argv; private tests use exactly `["<test-helper>"]`.
Production SHALL record `backend_identity="ldpc==2.4.1"` and
`dependency_version="2.4.1"`; private tests SHALL record both as
`test_injected`. Python and NumPy versions SHALL be
`platform.python_version()` and `numpy.__version__`.
`artifact_index` SHALL have exactly `pre_run_plan.json`,
`long_v3_candidate_manifest.json`, `development_outcomes.csv`, and
`development_selections.json`, each mapped to exactly `sha256` and `bytes`.

The report SHALL contain run/role/status, observed outcome/selection counts,
per-length and per-stratum status/terminal/disclosure aggregates, the ordered
selected candidate IDs, explicit
`development_only_not_qualification_or_promotion=true`, the run-manifest
SHA256, and `report_content_sha256` over itself without that field.

Its exact keys SHALL be
`schema_version="binary_ldpc_long_v3_development_report_v1"`, `run_id`,
`role`, `test_only`, `status`, `stop_reason`, `observed_outcome_count`,
`observed_selection_count`, `aggregates`, `selected_candidates`,
`development_only_not_qualification_or_promotion`, `plan_sha256`,
`run_manifest_sha256`, and `report_content_sha256`.

`aggregates` SHALL have exactly `by_length`, `by_stratum`, and
`terminal_prefix_counts`. Each decimal length or stratum entry has exactly
`status_counts`, `exact_success_count`, and
`total_syndrome_bits_disclosed`. `selected_candidates` contains ordered
objects with exactly `n`, `plane_id`, `candidate_id`, and `selection_sha256`.

The frozen DAG is: plan self-hash and plan to candidate/code hashes; candidate
manifest internal self-hash; selections self-hash and selections to
plan/outcomes; run-manifest self-hash and manifest to
plan/candidate/outcomes/selections; report self-hash and report to
plan/run-manifest.

### Runner Semantics

For each n/plane/stratum, generate the sacrificed data once and reuse its exact
arrays across all four candidates. Append `role` and `source_sha256` to every
Phase 2 outcome. After all 128 rows for one n/plane exist, call the accepted
`select_candidate`; never implement a second selection rule.

The production run succeeds only with 3840 rows, 30 selections, pinned backend
on every row, no backend-unavailable/internal schema failure, and within the
600-second cap. Decode failures and syndrome inconsistencies remain valid
development outcomes and do not by themselves fail artifact completion.

Any Python exception or internal-cap failure after execution starts SHALL
preserve the plan, exclusively create any still-missing required artifacts,
retain all completed outcome rows, force empty or completed-only selections,
set status `development_run_failed`, and record the exception/cap stop reason.
It SHALL never claim selection completeness.

A completed-only selection is permitted only for an exact contiguous
128-row n/plane group that passes `select_candidate`; an incomplete group
produces no selection. Failure reports aggregate only persisted rows and list
only completed selections.

Success SHALL use `status="development_run_completed"` and
`stop_reason="completed"`. Failure SHALL use
`status="development_run_failed"` with either
`stop_reason="internal_cap_exceeded"` or
`stop_reason="exception:<ExceptionClass>:<message>"`.

An external hard kill may leave a plan/partial directory. Such a directory is
invalid and SHALL NOT be repaired, resumed, or used as evidence; a new
additively named successor requires planner review.

### Read-Only Verification

The verifier SHALL open files read-only and reject:

- any missing or extra top-level artifact;
- any self-hash, byte-length, DAG, code/backend/version, plan, count, order,
  schema, boolean, float, role, source, status, accounting, or selection
  mismatch;
- noncanonical frame IDs or p_hat/source hashes reconstructed from the exact
  sacrificed generator;
- a success manifest/report unless all production completion conditions hold.

For every n/plane it SHALL feed the parsed 128 rows back through the accepted
`select_candidate` and require byte-equivalent selection content. It SHALL not
rerun LDPC decoding and SHALL state that limitation in its success JSON.

Verifier stdout SHALL be one compact sorted JSON object with `status`,
`run_status`, counts, manifest/report hashes, and
`decoder_reexecution=false`. Exit 0 means artifact integrity only, not
qualification or promotion.

The exact stdout keys SHALL be `status="verified"`, `run_status`,
`outcome_count`, `selection_count`, `manifest_sha256`, `report_sha256`,
`decoder_reexecution=false`, and
`scope="artifact_integrity_and_selection_reconstruction_only"`.

### Test-Only Reduced Domain

Private test helpers MAY create a clearly marked `test_only=true` plan for
exactly n=256/plane0, four candidates, two strata, and 16 frames, using an
injected decoder. Production CLI paths SHALL reject `test_only=true`.
Test artifacts SHALL use a fresh writable temp root outside production outputs.
The verifier MAY verify this reduced package only through a private test
function that explicitly permits test mode; its CLI SHALL reject it.

Tests SHALL cover success, no-overwrite, plan/code/hash tampering, malformed
CSV/accounting/selection, extra files, exception finalization, read-only
verification, and production rejection of test plans.

The runner module SHALL expose `prepare_plan(output_dir: Path) -> dict`,
`execute_plan(output_dir: Path) -> dict`,
`_prepare_test_plan(output_dir: Path) -> dict`, and
`_execute_test_plan(output_dir: Path, decoder_factory, *,
clock=time.perf_counter) -> dict`.

The verifier module SHALL expose `verify_output(output_dir: Path) -> dict` and
`_verify_test_output(output_dir: Path) -> dict`.

Production functions and both CLIs SHALL reject test-only plans. Private test
functions SHALL reject production plans. File tests SHALL use a
caller-created fresh writable temp root outside
`comparison_bench/outputs_comparison/`.

## Phase 4: Ten-Plane Frame-Level Development Aggregation

Phase 4 adds a pure in-memory module
`comparison_bench.formal_ir.long_v3_frame_development`. It consumes only the
already verified 3840 typed outcome rows and exact 30 selection mappings. It
does not decode, read confirmation/real data, or write artifacts.

### Formalizable Global Stopping Model

The q=1024 frame has exactly ten MSB-first bit planes. For each n, stratum, and
frame index, use the selected candidate for each plane and combine the ten
corresponding development outcomes.

Alice is modeled as disclosing one 64-bit frame-wide Toeplitz tag before the
first LDPC round. The fixed decoder candidates SHALL NOT use tag bits to alter
decoding; Bob uses the tag only to stop after a global round. The same tag is
checked at most four times. Development exact equality determines which check
would match, but SHALL be labeled
`development_oracle_equivalent_terminal_not_tag_execution`.

All planes advance through the same global prefix order. A plane that was
already exactly corrected remains fixed while other planes receive the next
nested syndrome extension. The slowest selected-plane terminal determines the
frame terminal.

For a successful frame at prefix row count m:

- input bits = `10*n`;
- syndrome disclosure = `10*m`;
- verification-tag disclosure = 64 bits, once;
- total key-dependent disclosure = `10*m+64`;
- public Toeplitz seed control = `10*n+63` bits;
- `epsilon_ec_union_bound=global_rounds*2^-64`.

If any selected plane is not `development_exact_success`, frame status is
`development_frame_failed`; global rounds/disclosure use the maximum attempted
plane round, capped at four, and the failure remains in the denominator.
For any frame with at least one attempted global round, tag disclosure is 64
and public seed control is `10*n+63`, even on failure. If global rounds are
zero, syndrome/tag/seed disclosure and epsilon are all zero. For rounds
1..4, syndrome disclosure uses ten times that round's prefix row count and
the union bound uses that round count.

### Exact Aggregator API

`aggregate_frame_development(outcome_rows, selections) -> dict` SHALL require:

- exactly 3840 rows and 30 selections;
- the exact n/plane/candidate/stratum/frame grid, canonical policies,
  development role, finite nonnegative runtime, and Phase 2 status/accounting;
- one exact selection per n/plane whose selection hash and selected candidate
  reconstruct through `select_candidate`;
- identical frame indices across all ten planes.

It SHALL return exactly:

- `role="sacrificed_frame_development_only"`;
- `stopping_model`;
- `plane_count=10`;
- `verification_tag_bits=64`;
- `tag_reuse_max_checks=4`;
- `frame_outcome_count=96`;
- ordered `frame_outcomes`;
- `length_aggregates`, keyed by decimal n;
- `selected_length`;
- `length_selection_tuple`;
- `aggregation_sha256`, hashing compact JSON without itself.

Each frame outcome SHALL have exactly `n`, `stratum_id`, `frame_index`,
`selected_candidate_ids` (plane order 0..9), `plane_terminal_prefix_ids`,
`plane_rounds_attempted`, `status`, `global_terminal_prefix_id`,
`global_rounds_attempted`, `input_bits`, `syndrome_bits_disclosed`,
`verification_tag_bits`, `key_dependent_disclosure_bits_total`,
`public_toeplitz_seed_bits`, `epsilon_ec_union_bound`, and
`key_disclosure_per_input_bit`.

Each length aggregate SHALL have exactly `successes_by_stratum`,
`terminal_prefix_counts_by_stratum`,
`mean_key_disclosure_per_input_bit_by_stratum`,
`worst_stratum_mean_key_disclosure_per_input_bit`, and
`overall_mean_key_disclosure_per_input_bit`.

### Frozen Length Selection

Select one development length using:

`[-min(p001_successes,p002_successes),
  -(p001_successes+p002_successes),
  worst_stratum_mean_key_disclosure_per_input_bit,
  overall_mean_key_disclosure_per_input_bit,
  n]`.

Runtime and per-plane structural metrics do not enter. The result is a
development design choice only. It SHALL NOT imply qualification or promotion.

### Phase 4 Tests

Tests SHALL independently construct valid synthetic 3840-row grids and prove:
exact ten-plane alignment; slowest-plane global stopping; one-tag and nested
syndrome accounting; union bound; retained frame failure; strict malformed
row/selection rejection; exact length tuple priority; deterministic hash; and
no file writes.

## Phase 5: Executable Formal Binary LDPC v3

Phase 5 adds one additive module
`comparison_bench.formal_ir.ldpc_v3`. It SHALL NOT modify or call a mutable
variant of `shared.validate_outcome`, because that validator is frozen to
64-pair v1/v2 frames. The new module owns a strict v3 validator while reusing
only general pure helpers from `shared`.

This phase implements the formal method and focused tests only. It does not
create a runner, result package, qualification evidence, or promotion claim.

### Frozen Method Identity and Domain

- method: `ldpc_formal_v3`;
- dimension: exactly 1024;
- mapping: exactly `gray`;
- frame length: exactly 256 paired symbols;
- bit order: the existing `symbols_to_bits` MSB-first order, planes 0..9;
- selected candidate IDs by plane:
  `[1,0,1,2,0,0,1,3,2,3]`;
- development selection binding:
  `1319938ff6c989642950d4e3f3dba7ae9d0cbea14eb0c1e3a90d826e4fbc3227`;
- prefix order: `p050`, `p0625`, `p075`, `p0875`, with row counts
  128, 160, 192, and 224;
- backend: exactly `ldpc==2.4.1`, `BpOsdDecoder`, minimum-sum BP, serial
  schedule, 50 iterations, scale 1.0, one thread, OSD-0/order 0;
- default caps: 10 seconds, 40 decoder calls, and 100 transcript events.

Candidate matrices SHALL be reconstructed from `codebook_long_v3` and never
accepted as caller-provided matrix bytes. For each plane the master candidate
and every prefix SHALL be reconstructed and validated through its canonical
HGF2V3 round trip. Matrix selectors are pre-shared protocol identifiers and
therefore record zero disclosure bits.

### Frozen Calibration Contract

The method accepts exactly one mapping with keys:
`calibration_role`, `dimension`, `mapping`, `frame_len_symbols`,
`source_sha256`, `planes`, and `calibration_sha256`.

The first four values SHALL be respectively
`sacrificed_tuning_only`, 1024, `gray`, and 256. `source_sha256` SHALL be a
lowercase 64-hex digest. `planes` SHALL be an ordered list of exactly ten
mappings, each having exactly `plane_id`, `errors`, `total_bits`, and `p_hat`.
Plane IDs SHALL be 0..9 in order; integer fields SHALL reject booleans;
`0 <= errors <= total_bits`, `total_bits > 0`, and
`p_hat == errors/total_bits` within absolute tolerance 1e-15 with no relative
tolerance. Every p_hat SHALL be finite and in `[0,.5)`.

`calibration_sha256` is SHA256 of compact sorted ASCII JSON after removing
that field. Any mismatch is `unsupported_domain` and occurs before transcript,
tag disclosure, or decoder construction. Decoder error rate is
`min(max(p_hat,1e-4),.49)`.

### Preflight and Input Precedence

Validation order is:

1. exact dimension/mapping/frame shapes, integer symbols in `[0,1023]`,
   locked seed record of exactly 2623 bits, and scalar metadata;
2. exact calibration and frozen selection binding;
3. exact codebook reconstruction and canonical round trips;
4. pinned-backend constructor probe using the plane-0 p050 matrix and the
   exact Phase 5 decoder kwargs;
5. execution.

Steps 1 failures are `invalid_input`, steps 2-3 are `unsupported_domain`, and
step 4 is `preflight_unavailable`. All are non-attempted and denominator
excluded, with an empty transcript and zero disclosure.

The public test entry point MAY inject `_decoder_factory`, `_preflight`, caps,
and a monotonic clock. Production default preflight SHALL inspect the installed
version and constructor. An injected successful preflight must have exactly
`status="ok"` and `dependency_version="2.4.1"`; tests SHALL label injected
construction through the returned backend fields.

### Exact Global-Round Protocol

Alice computes one 64-bit Toeplitz tag over her 2560 MSB-first Gray bits using
the locked 2623-bit seed. Before round 1, record:

1. one `VERIFICATION_SEED` control event, plane -1, key bits 0, public bits
   2623, payload `seed_id` and `seed_bit_length`;
2. one `VERIFICATION_TAG` Alice-to-Bob event, plane -1, key bits 64, public
   bits 0, payload `tag`.

The tag is disclosed exactly once. The decoder never receives tag or tag-match
information and cannot select a candidate, policy, or error vector from it.

At global round r, for every plane 0..9:

- use that plane's frozen selected candidate and the current leading prefix;
- disclose only the new syndrome rows since the prior prefix;
- record one `SYNDROME` Alice-to-Bob event whose key bits equal the extension
  row count and whose payload contains only the packed extension syndrome;
- decode the cumulative syndrome difference with the current full prefix;
- require a binary error vector of length 256 and verify
  `H @ error mod 2 == syndrome_difference`; otherwise stop as
  `decoder_error` or `syndrome_inconsistent`;
- update that plane's Bob bits with the returned error vector.

All ten planes are decoded in every attempted global round, including planes
that previously matched. This keeps decoder behavior independent of Alice
truth and of the tag. After all ten planes finish, assemble Bob's 2560 bits
and perform exactly one local comparison with Alice's already disclosed tag.
Record one `FRAME_TAG_CHECK` Bob-local event with zero disclosure and payload
`value="match"` or `value="mismatch"`.

On match, stop as `verified_success`. On mismatch, advance all ten planes to
the next prefix. A mismatch after p0875 is `verify_failed`. Exact Alice/Bob
equality SHALL NOT be inspected to stop or choose a decoder path.

The terminal cumulative syndrome disclosure is `10*m`, where m is the terminal
prefix row count; total key-dependent disclosure is `10*m+64`; public control
is 2623. `verification_check_count` is the number of completed global tag
checks, `global_rounds_attempted` is the number of started rounds, and
`epsilon_ec` is `verification_check_count*2^-64`.

### Transcript and Resource Semantics

Every event uses canonical `shared.canonical_event`, method
`ldpc_formal_v3`, the atomic frame key, monotonically increasing integer IDs,
`parent_event_id=None`, global zero-based `pass_id`, and `plane_id`.
Besides the two initial events and per-round syndrome/tag-check events, no
selector event is required because candidates and prefix order are frozen
method configuration.

After successful validation and preflight, the seed and tag events form one
atomic protocol-start disclosure; injected event caps below two are invalid
input. Check wall and decoder-call caps before every decoder construction/call,
and check the event cap before every subsequent event. Reaching a cap is
`aborted_resource_limit`; record one `ABORT` control event only when it fits
the event cap. A backend exception is `decoder_error`. The atomic seed/tag
disclosure remains accounted on every attempted terminal status.
`verification_invoked` means the tag was disclosed, not that a check
completed.

### Exact Return Contract

`run_ldpc_formal_v3(...) -> {"outcome": outcome, "events": events,
"decoded_bits": decoded_or_none}` is the only public execution function.
The returned outcome SHALL contain the standard formal fields plus exactly
these v3 fields:

`global_rounds_attempted`, `verification_check_count`,
`terminal_prefix_id`, `ldpc_syndrome_bits`,
`verification_tag_bits_component`, `selection_binding_sha256`,
`candidate_ids`, `calibration_sha256`, `mapping`,
`leakage_comparison_policy`, `backend_name`, and `backend_version`.

Standard identity fields SHALL use `n_pairs=256`,
`frame_len_symbols=256`, and pair-index SHA256 over exact ASCII
`0,1,...,255`. `attempted` and `denominator_included` follow
`shared.status_flags`. `leakage_comparison_policy` is exactly
`method_specific_not_cross_ranked`.

The v3 validator SHALL require exact outcome keys, exact types (booleans are
not integers), finite nonnegative runtime/raw SER, status/flag precedence,
event-ID boundaries, transcript hash and accounting reconstruction, the
terminal prefix/round/disclosure relationship, candidate/calibration binding,
and zero transcript/disclosure for non-attempted statuses.

### Phase 5 Tests

Add only `comparison_bench/tests/test_ldpc_formal_v3.py`. Tests SHALL cover:

- clean round-1 verified success and exact 1280+64/2623 accounting;
- deterministic continuation to a later round without an Alice-truth oracle;
- a full-master nullspace error producing four syndrome-consistent rounds and
  terminal `verify_failed`;
- ten-plane call order, cumulative-prefix decode, extension-only syndrome
  events, one tag, four-check union bound, and exact transcript hash;
- malformed input, seed, calibration/self-hash, selection, codebook,
  preflight, decoder exception, wrong length/nonbinary error,
  syndrome inconsistency, and all three caps;
- proof that decoder inputs never contain tag or tag-match information;
- exact v3 outcome validation and no file writes.

## Phase 6: TTBIN-Derived Data Bridge and Qualification

Phase 6 is additive. It SHALL NOT modify `src/`, `experiments/`, `tools/`,
historical outputs, or Phase 1-5 modules. Production outputs are no-overwrite
and use fresh additive directories.

### Phase 6A: Read-Only Real-Data Bridge

Add `comparison_bench.formal_ir.ldpc_v3_ttbin_data`. It accepts three exact
sidecar directories `d1024_bw100/blk0`, `d1024_bw120/blk0`, and
`d1024_bw180/blk0`, plus `d1024_bw200/blk0`, and the exact main/chunk TTBIN
paths. Each sidecar must contain `a_eff.npy`, `b_eff.npy`, and
`sidecar_meta.json`.

Validation SHALL require q/dimension 1024, the requested bin width, equal
one-dimensional integer arrays, symbols in `[0,1023]`, at least the required
complete frames, `joint_source_mode="from_ttbin"`,
`joint_origin="from_ttbin"`,
`materialize_origin="materialized_from_ttbin"`, strict unsampled sequences,
and metadata whose `source_ttbin_paths` resolves to the supplied main file.
The main file and exactly one `.1.ttbin` chunk must exist. No tail padding,
symbol repair, dtype coercion from non-integral values, or fallback source is
allowed.

Every source record binds resolved path, byte length, and SHA256 for main
TTBIN, chunk TTBIN, both arrays, and metadata. It also binds the processing
rule `sidecar_a_eff_b_eff_v1`, pairing mode, bin width, q, acquisition loss,
and source metadata SHA256.

Frames are exact contiguous slices of 256 source pairs. Frame ID is the
zero-based slice index. Frame identity is SHA256 of compact JSON containing
source-record SHA256, dataset ID, frame ID, source pair start/end, and SHA256
of canonical little-endian int64 Alice/Bob bytes.

Selection rank is SHA256 of ASCII
`binary_ldpc_v3_phase6_selection_v1|<role>|<dataset_id>|<frame_identity>`.
Select the 64 lowest ranks from bw100 as sacrificed calibration. Select the
32 lowest ranks independently from each of bw120, bw180, and bw200 as real
confirmation. Sort selected frames by `(role, bin_width_ps, selection_rank)`.
Calibration and confirmation dataset/frame identities must be disjoint.

Calibration converts natural symbols to existing MSB-first Gray planes and
counts errors over exactly `64*256` bits per plane. It emits the exact Phase 5
calibration schema and compact-JSON self-hash. Confirmation values cannot
affect it.

Public APIs:

- `build_source_manifest(main_ttbin, chunk_ttbin, sidecar_dirs) -> dict`;
- `verify_source_manifest(manifest) -> None`;
- `build_locked_data(manifest) -> dict`;
- `verify_locked_data(lock) -> None`;
- `frame_arrays(lock, role, dataset_id, frame_id) -> (alice, bob)`.

All functions are read-only and write no artifact.

### Phase 6B: Synthetic Qualification

Add a two-step no-overwrite CLI module
`run_ldpc_v3_synthetic_qualification` and read-only verifier
`verify_ldpc_v3_synthetic_qualification`.

The production output directory contains exactly the six formal artifacts:
`pre_run_plan.json`, `formal_frame_outcomes.csv`,
`formal_transcript.jsonl`, `formal_run_manifest.json`,
`formal_codebook_manifest.json`, and
`formal_qualification_report.json`.

Prepare validates Phase 6A data and embeds the source-manifest hash, frozen
calibration, selected-candidate binding, exact Phase 6 source-file hashes,
caps, generator contract, execution order, and fresh CSPRNG Toeplitz seed
records. It performs zero decoder calls.

Synthetic confirmation has exactly 64 q=1024/n=256 frames:

- `calibrated`: 32 frames using the ten calibration p_hat values;
- `stress_125`: 32 frames using `min(.49,1.25*p_hat)` per plane.

For each stratum Alice natural symbols come from a domain-separated PCG64
stream. Convert to Gray planes, draw independent per-plane error masks in
plane order 0..9, XOR, and convert Gray words back to natural symbols. Frozen
integer root seeds and exact NumPy call order are recorded in the plan.
Confirmation generation and Toeplitz seeds are disjoint from development and
real data.

Run `ldpc_formal_v3` in frozen order. All statuses are retained and every
attempted frame remains in the denominator. Per stratum promotion requires
at least 31/32 `verified_success`, exactly 32 denominator rows, and zero
unclassified/internal/provenance/accounting failures. Global promotion
requires both strata.

Default caps are Phase 5 per-frame caps and 1800 seconds complete-run wall.
Exceptions/caps finalize all six missing artifacts exclusively with completed
rows and explicit non-promotion. External-kill partial directories are invalid,
non-resumable, and never repaired.

The verifier opens files read-only, reconstructs source/calibration,
generator frames, selection, schemas, transcript grouping/accounting,
artifact byte hashes/DAG, gates, code hashes, and exact execution order.
It does not rerun decoding and returns
`decoder_reexecution=false`. No live whole-worktree status hash is a gate;
only explicitly listed Phase 6 source-file byte hashes are bound.

### Phase 6C: Real Qualification

Real lock/prepare is forbidden unless the exact Phase 6B report is completed,
strictly verified, and globally promoted. Failure SHALL leave the requested
real output path nonexistent.

Add two-step no-overwrite
`run_ldpc_v3_real_qualification` and read-only
`verify_ldpc_v3_real_qualification`. The output contains the six formal
artifacts plus `real_data_lock.json`.

The real lock binds the verified synthetic report/manifest hashes, complete
Phase 6A source manifest and lock, frozen calibration, exactly 96 confirmation
frames, per-frame canonical arrays/provenance, 96 fresh 2623-bit CSPRNG
Toeplitz seeds, and a self-hash. Execution order is bw120 then bw180 then
bw200, each in selection-rank order.

Each bin-width stratum requires at least 31/32 verified successes, exactly 32
denominator rows, and zero unclassified/internal/provenance/accounting
failures. Global promotion requires all three strata. Failure is retained as
`non_promoted`; no retry, adaptive extension, policy change, or real
confirmation tuning is allowed.

The real verifier reconstructs the source files, lock, frame selection,
calibration, transcript/outcome accounting, artifact DAG, synthetic gate
binding, and real gates without decoder reexecution. The claim is limited to
the current 20 dB acquisition, q=1024, Gray mapping, n=256, and the three
registered bin widths.

### Phase 6 Execution Boundary

Implementation and injected-decoder tests do not authorize production
execution. Production order is exactly synthetic prepare, main-thread plan
audit, synthetic execute once, verifier once, then and only on verified
promotion real lock/prepare, main-thread audit, real execute once, and verifier
once. Every failed or partial package is retained.
