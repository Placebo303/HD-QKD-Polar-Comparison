# Design: Binary LDPC Adjacent-Channel v4

## 1. Identity, Domain, and Isolation

The change adds only under `comparison_bench/`:

- `formal_ir/codebook_v4.py`;
- `formal_ir/ldpc_v4_channel.py`;
- `formal_ir/ldpc_v4_development.py`;
- `formal_ir/ldpc_v4.py`;
- dedicated development, synthetic, and real runner/verifier CLIs;
- focused tests.

The formal identity is `ldpc_formal_v4`. Its frozen domain is:

- q=1024;
- 256 symbols per frame;
- ten MSB-first binary-reflected Gray planes;
- the current 20 dB acquisition;
- sacrificed calibration from `d1024_bw100`;
- real confirmation strata `d1024_bw120`, `d1024_bw180`, and
  `d1024_bw200`.

V1-v3 modules and evidence remain unchanged. V4 SHALL reuse read-only shared
transcript, Toeplitz, and TTBIN bridge helpers only when their existing public
contracts already fit; it SHALL NOT branch behavior inside a historical
method.

## 2. Sacrificed Adjacent-Bin Channel Contract

### 2.1 Calibration Source

`build_adjacent_channel_model(locked_data)` SHALL accept only a strictly
verified Phase 6-style TTBIN source lock and exactly the 64 existing
`d1024_bw100` sacrificed calibration frames. It SHALL reconstruct the arrays
from the bound `a_eff.npy` and `b_eff.npy` bytes and reject any source hash,
frame identity, range, dtype, shape, or metadata mismatch.

For every selected symbol calculate:

`delta = ((Alice - Bob + 512) mod 1024) - 512`.

The v4 calibration is supported only if:

- total symbols are exactly 16,384;
- the only delta values are `-1`, `0`, and `+1`;
- every nonzero delta produces Gray Hamming distance exactly one;
- every symbol is an integer in `[0,1023]`.

The accepted frozen counts are:

- `zero_count=12403`;
- `plus_one_count=3865`;
- `minus_one_count=116`;
- `total_count=16384`.

Any different count returns to OpenSpec; it is not silently recalibrated.

### 2.2 Canonical Model

The compact sorted JSON model has:

- schema `binary_ldpc_v4_adjacent_channel_v1`;
- role `sacrificed_calibration_only`;
- dimension 1024 and mapping `gray_msb_first`;
- frame length 256 and calibration frame count 64;
- the four exact counts above;
- sign convention `signed_modular_alice_minus_bob`;
- nominal probabilities equal to count/16384;
- stress scale exactly 1.25;
- stress plus/minus probabilities equal to their nominal probabilities times
  1.25 and stress zero probability equal to one minus their sum;
- source-lock, source-manifest, selected-frame, and calibration byte hashes;
- `model_sha256`, computed over the model without that key.

Floating values use Python `repr(float(value))` at CSV boundaries and ordinary
JSON numbers in compact JSON. Verifiers recompute counts and probabilities
from the bound sacrificed bytes.

### 2.3 Bob-Conditioned Soft Information

For Bob symbol `b`, plane `i` in MSB-first order, and model probabilities
`p_plus`, `p_minus`, define:

`p_i(b) = p_plus * I(gray((b+1) mod 1024)_i != gray(b)_i)
        + p_minus * I(gray((b-1) mod 1024)_i != gray(b)_i)`.

`plane_error_channel(bob_symbols, plane_id, stratum)` SHALL return exactly 256
float64 probabilities in input order and clip only for the backend to
`[1e-6,.49]`. The unclipped values and model remain the scientific contract.
No Alice symbol, verification tag, confirmation result, or per-frame truth may
affect these probabilities.

## 3. Deterministic V4 Codebook

### 3.1 Frozen Dimensions

The construction identity is `binary_ldpc_anchored_cw3_v4`, version `1`.
Block length is exactly 256. Plane IDs are `0..9`, candidate IDs are `0..3`,
and syndrome row counts by plane are:

`[16,16,16,24,24,32,48,80,136,192]`.

These fixed rates are deliberately reliability-first. Their sum is 584
syndrome bits; with one 64-bit verification tag a successful frame discloses
648 key-dependent bits, or 2.53125 bits/symbol. Rate optimization is not part
of v4.

### 3.2 Exact Anchored Sparse Construction

For `(plane_id,candidate_id)`, define the base integer seed:

`6000 + 100*candidate_id + plane_id`.

For trial `t=0..99`, initialize a fresh `PCG64(base_seed+t)` and:

1. Create an all-zero `m x 256` uint8 matrix.
2. For each column `j=0..255`:
   - when `j<m`, anchor the column at row `j`, draw two distinct other rows
     uniformly without replacement from the ordered array
     `[0,...,j-1,j+1,...,m-1]`, combine them with `j`, and sort the support;
   - when `j>=m`, draw three distinct rows uniformly without replacement from
     `[0,...,m-1]` and sort the support.
3. If that unordered three-row support duplicates an earlier column support,
   repeat the applicable draw, for at most 10,000 draws for that column.
4. Set those three entries to one.
5. Accept the first completed matrix whose exact GF(2) row rank is `m`.

For the anchored draw, the ordered array excluding `j` SHALL be constructed
explicitly before `rng.choice`; drawing from an integer range with later
index-remapping is not equivalent. Exhausting a column or all 100 trials fails
closed. RNG call order and row ordering are part of the construction identity.

Every accepted matrix SHALL have:

- exact shape `(m,256)`;
- exact GF(2) rank `m`;
- every column weight exactly three;
- no duplicate column support;
- no zero row;
- the first `m` columns contain their corresponding row anchors.

Exact 4-cycle counts and exact weight-3/weight-4 codeword witness searches are
reported. For planes 8 and 9, any weight-3 or weight-4 witness invalidates the
candidate. For planes 0-7 these witnesses remain disclosed diagnostics because
their high-rate sparse codes can contain low-weight words; development FER is
the acceptance evidence.

### 3.3 Canonical Bytes and Manifest

Canonical bytes are ASCII `HGF2V4`, little-endian uint32 `(m,n)`, then C-order
uint8 matrix bytes. Parsing rejects wrong magic, size, plane row count,
nonbinary value, unsupported dimension, or trailing bytes.

The complete manifest contains all 40 candidates, exact construction seeds and
accepted trial numbers, shape/rank/weights, 4-cycle and low-weight diagnostics,
canonical-byte SHA256 values, construction identity/version, and a
self-hash. Verification reconstructs all matrices; caller-supplied bytes are
never trusted as identity.

No external repository code or matrix is imported.

## 4. Frozen Decoder Policy

The only v4 decoder policy is:

- dependency `ldpc==2.4.1`;
- `max_iter=50`;
- `bp_method="product_sum"`;
- `schedule="serial"`;
- `omp_thread_count=1`;
- `serial_schedule_order=[0,...,255]`;
- `osd_method="OSD_0"`;
- `osd_order=0`;
- input vector type `syndrome`;
- `error_channel` equal to the 256 Bob-conditioned probabilities.

The policy is compact-JSON self-hashed. Unsupported dependency or constructor
behavior is retained as backend failure; there is no fallback, scalar
`error_rate`, min-sum substitution, OSD tuning, or per-frame policy selection.

## 5. Sacrificed Development and Candidate Selection

### 5.1 Development Generator

Development uses two deterministic strata, `adjacent_nominal` and
`adjacent_stress_125`, each with 512 q=1024 frames.

For each stratum, separately derive Bob and delta PCG64 roots from the first 16
big-endian bytes of SHA256 over compact JSON containing:

- construction identity/version;
- role `sacrificed_development_only`;
- stratum ID;
- kind `bob` or `delta`;
- frame count 512;
- dimension and frame length;
- channel-model SHA256.

Generate Bob by one
`rng.integers(0,1024,size=(512,256),dtype=np.uint16)` call. Generate one
uniform float64 array of the same shape and map it deterministically to delta
`-1,+1,0` using cumulative minus/plus probabilities in that order. Alice is
`(Bob+delta) mod 1024`.

Frame IDs are `v4dev_<stratum>_f000` through `f511`. Both strata, every
candidate, and every plane use identical frame identities within a stratum.
Development roots and frames can never appear in qualification.

### 5.2 Plane Evaluation

For every plane, candidate, stratum, and frame:

1. Gray-map Alice and Bob and form the true binary error vector for
   sacrificed development only.
2. Form syndrome difference `H*Alice_plane XOR H*Bob_plane`.
3. Instantiate the frozen decoder with Bob-conditioned `error_channel`.
4. Decode the error vector and require length 256, binary values, and syndrome
   consistency.
5. Exact sacrificed equality records `development_exact_success`; consistent
   but wrong output records `development_decode_failed`.

Constructor/decode exceptions, backend mismatch, malformed output, timeout,
and syndrome inconsistency have distinct retained statuses. Runtime never
affects selection.

### 5.3 Candidate Selection and Readiness

Each plane selects exactly one of four candidates using:

`[-min(nominal_successes,stress_successes),
  -(nominal_successes+stress_successes),
  candidate_id]`.

After per-plane selection, reconstruct each q=1024 frame from the ten selected
plane outcomes. A frame is successful only if all ten planes are exact.

Development readiness requires:

- exactly 512 denominator frames in each stratum;
- at least 495 frame successes in each stratum;
- zero backend, source, internal, accounting, or unclassified failure;
- every selected plane candidate valid under the codebook contract.

The 495/512 floor is a readiness screen, not qualification or a population
confidence claim. Failure stops before synthetic prepare. No parameter may be
changed using a qualification result.

### 5.4 Frozen Selection Binding

The development selector emits one compact self-hashed JSON object with
exactly these keys:

- `schema="binary_ldpc_v4_selection_v1"`;
- `method_id="ldpc_formal_v4"`;
- `codebook_manifest_sha256`;
- `channel_model_sha256`;
- `plane_selections`, an ordered ten-element list whose element for plane
  `p=0..9` contains exactly `plane_id`, `candidate_id`,
  `canonical_bytes_sha256`, `nominal_successes`, `stress_successes`, and
  `selection_key`;
- `selection_sha256`, computed over compact sorted JSON of all preceding
  fields.

`selection_key` is the exact three-integer list
`[-min(nominal_successes,stress_successes),
  -(nominal_successes+stress_successes),candidate_id]`.
The formal method SHALL validate the self-hash, exact key set, plane order,
candidate range, matrix hashes reconstructed from the bound codebook manifest,
channel-model hash, success-count range `0..512`, and recomputed selection
keys. It consumes no development outcome rows and performs no candidate
selection itself.

## 6. Formal `ldpc_formal_v4`

### 6.1 Decode

The method accepts exactly one 256-symbol Alice/Bob frame, the frozen channel
model, the selected-candidate binding, and one locked Toeplitz seed.

For each plane in order `0..9`:

1. reconstruct its selected canonical matrix;
2. disclose Alice's syndrome of the fixed plane row count;
3. combine it with Bob's local syndrome to obtain the error syndrome;
4. construct Bob-conditioned per-position error probabilities;
5. run the frozen decoder exactly once;
6. require binary length-256 output and syndrome consistency;
7. correct Bob's plane.

After all ten planes, inverse Gray-map Bob's corrected planes. Disclose and
check exactly one 64-bit Toeplitz verification tag over the 2,560 Gray bits.
The Toeplitz seed has exactly 2,623 public-control bits and is not
key-dependent disclosure.

The decoder never receives Alice truth, tag contents, tag match, or a callback.
The tag is not used to select a matrix, retry, or change a correction.

### 6.2 Outcomes and Accounting

Successful key-dependent disclosure is always:

- 584 LDPC syndrome bits;
- 64 verification-tag bits;
- total 648 bits.

Public control is exactly the 2,623-bit Toeplitz seed plus canonically counted
event/control fields already defined by the shared formal contract. The
verification failure bound is `2^-64` because exactly one tag comparison is
performed.

Every attempted frame enters the denominator. Status precedence is:

1. invalid input/source/model/selection;
2. backend unavailable;
3. resource exhausted;
4. decoder error or malformed output;
5. syndrome inconsistent;
6. `verified_success` when the final tag matches;
7. `verify_failed` otherwise.

The method has a five-second frame wall cap, exactly ten allowed decoder calls,
one allowed verification check, and a bounded transcript event count of 32.
All transcript bytes and outcomes are canonically hashed and strictly
validated.

## 7. Development Package

Dedicated CLIs:

`python -m comparison_bench.src.comparison_bench.cli.run_ldpc_v4_development
 --output-dir <fresh> --mode prepare|execute`

`python -m comparison_bench.src.comparison_bench.cli.verify_ldpc_v4_development
 --output-dir <path>`

Prepare creates a fresh directory exclusively and writes only
`pre_run_plan.json`. Execute validates all hashes and creates exactly:

1. `v4_candidate_manifest.json`;
2. `v4_channel_model.json`;
3. `development_plane_outcomes.csv`;
4. `development_selection.json`;
5. `development_run_manifest.json`;
6. `development_report.json`.

Together with the plan the completed package has seven files. It binds scoped
source-file hashes, installed versions, source lock/manifest, generator roots,
execution order, expected counts, candidate and selection hashes, status
accounting, and the readiness gate. JSON is compact sorted UTF-8 without a
trailing newline; CSV is canonical UTF-8 with `\n` terminators.

The production development plan freezes a 1,800-second complete-run wall cap
and a 5-second per-frame decoder wall cap. The latter is passed to the
development evaluator as `per_frame_s`; it SHALL NOT be mislabeled or enforced
as a per-candidate cap. Every plane-outcome CSV row additionally binds the
deterministically reconstructed stratum frame source through `source_sha256`.

The verifier reconstructs the source selection, channel counts/model,
candidate matrices, deterministic development frames, artifact DAG, candidate
selection, frame aggregation, denominators, and readiness gate. It SHALL set
`decoder_reexecution=false`.

Exceptions finalize an immutable failed package when possible. External-kill
partials are invalid, non-resumable, and never overwritten.

## 8. Fresh Synthetic Qualification

### 8.1 Prerequisite and Generator

Synthetic prepare requires an exit-zero verification of one completed,
ready development package and binds its plan, report, model, codebook, and
selection hashes.

It generates exactly:

- 128 `adjacent_nominal` frames;
- 128 `adjacent_stress_125` frames.

Prepare obtains independent 128-bit roots from `secrets.token_bytes(16)` for
Bob symbols, deltas, execution order, and Toeplitz seeds in each stratum.
Roots are stored as lowercase hex with SHA256 IDs. Substreams are derived by
SHA256 domain separation and consumed through PCG64 in a frozen order. All
2,560 per-frame Gray inputs and every 2,623-bit Toeplitz seed are independent
of development and v3 seeds. Collision checks across every stored v4 root/seed
and the bound v3 plan fail closed.

### 8.2 Gate and Package

Each stratum requires:

- exactly 128 denominator outcomes;
- at least 126 `verified_success`;
- zero source, provenance, internal, accounting, or unclassified failure.

All failures remain in denominators. The gate corresponds to a one-sided 95%
Clopper-Pearson lower bound above 0.95; the verifier recomputes the integer
gate and does not rely on a floating library result.

Dedicated prepare/execute and read-only verifier CLIs use a fresh explicit
output directory, no overwrite, no resume, scoped source hashes, canonical
transcript/outcome accounting, and `decoder_reexecution=false`. The exact
completed artifacts are:

1. `pre_run_plan.json`;
2. `formal_frame_outcomes.csv`;
3. `formal_transcript.jsonl`;
4. `formal_codebook_manifest.json`;
5. `formal_selection_manifest.json`;
6. `formal_channel_model.json`;
7. `formal_run_manifest.json`;
8. `formal_qualification_report.json`.

Prepare writes only the plan. Execute once writes/finalizes the other seven.
Synthetic non-promotion forbids real lock preparation and any v4 retry or
tuning.

## 9. Conditional Real Qualification

### 9.1 Fresh Lock

Real lock/prepare is permitted only when the exact bound synthetic package
strictly verifies and reports `promoted`.

Reuse the read-only TTBIN bridge to enumerate complete 256-symbol frames.
Calibration remains the same 64 sacrificed bw100 frames. For each of bw120,
bw180, and bw200:

1. exclude every frame identity reserved by v3 Phase 6;
2. exclude every v4 calibration identity;
3. sort remaining complete frames by the existing canonical SHA256 selection
   rank;
4. select the first 128.

The three sets and calibration are mutually disjoint. The lock binds all main
and chunk TTBIN, sidecar, metadata, processing-rule, selected-range, file-size,
and SHA256 provenance plus the synthetic report/manifest hashes.

Prepare obtains one fresh 128-bit Toeplitz root from
`secrets.token_bytes(16)` for each registered real stratum. For stratum ID
`d1024_bw120`, `d1024_bw180`, or `d1024_bw200`, derive the PCG64 seed from the
first 16 big-endian bytes of SHA256 over compact sorted JSON containing exactly
`schema="binary_ldpc_v4_real_toeplitz_v1"`, the root hex, stratum ID,
`kind="toeplitz"`, frame count 128, and seed length 2,623. Consume one
`rng.integers(0,2,size=2623,dtype=np.uint8)` call per selected frame in
selection-rank order. Store each lowercase root hex/root SHA256 ID and every
canonical seed record in `real_data_lock.json`.

Real prepare SHALL fail closed if any real root integer or seed ID collides
with another real root/seed, any bound synthetic root/seed, any deterministic
development root, or any bound v3 root/seed. The verifier reconstructs these
substreams and all collision sets without reading qualification outcomes.

### 9.2 Gate and Package

Execute exactly 384 frames in order bw120, bw180, bw200, then selection rank.
Each stratum requires exactly 128 denominator outcomes, at least 126
`verified_success`, and zero source/provenance/internal/accounting/unclassified
failure. One failed stratum makes the package `non_promoted`.

The real package uses the same eight synthetic artifact names and additionally
contains `real_data_lock.json`, for nine completed files. Its verifier
reconstructs the data selection and all source hashes, validates the synthetic
gate before accepting the lock, verifies transcript/outcome/leakage/status
accounting, and reports `decoder_reexecution=false`.

Claims remain limited to this 20 dB acquisition, q=1024, Gray mapping,
256-symbol frames, and the three registered bin widths.

## 10. Execution and Responsibility Boundary

The frozen order is:

1. implement and test codebook, channel, development, formal method, and all
   runner/verifier tooling;
2. main thread reviews code and tests;
3. development prepare once;
4. main thread audits the plan;
5. development execute once and verifier once;
6. only if ready, synthetic prepare once;
7. main thread audits the synthetic plan;
8. synthetic execute once and verifier once;
9. only if promoted, real lock/prepare once;
10. main thread audits the real plan and lock;
11. real execute once and verifier once;
12. main thread performs final acceptance and documentation.

Terra low implements only checked, frozen tasks and runs only specified tests.
Terra does not interpret requirements, change thresholds, inspect evidence to
tune parameters, prepare production plans, execute production evidence, or
make acceptance/promotion conclusions.

## 11. Stop Rules

Stop and retain evidence when:

- calibration bytes/counts differ from the frozen contract;
- no valid codebook candidate exists for a plane;
- development is incomplete or below 495/512 in either stratum;
- a scoped source hash or backend version drifts;
- synthetic is below 126/128 in either stratum;
- real is below 126/128 in any stratum;
- any proposed recovery requires confirmation truth, overwrite, rerun, or
  unregistered parameter change.

After a stop, improvement requires a new OpenSpec and fresh confirmation.
