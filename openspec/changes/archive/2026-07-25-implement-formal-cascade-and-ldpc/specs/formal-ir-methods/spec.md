# Spec: Formal Offline IR Methods

## Requirements

### R1: Method Identity and Boundary

The system SHALL add `cascade_formal_v1` and `ldpc_formal_v1` without changing
or relabeling `cascade_lite` or `layered_ldpc_lite`. The formal methods SHALL
model offline reconciliation on an already authenticated public channel, with
Alice as reference and Bob correcting locally. They SHALL retain every attempt
and failure. They SHALL NOT claim network transport, authentication cost,
hardware real-time behavior, finite-key/Route-A proof, Polar adaptation, or a
three-method winner.

### R2: Formal Verification and Transcript

Formal success SHALL require a universal2 Toeplitz tag and method consistency.
The input SHALL be the locked-mapping symbols flattened MSB-first to `n` bits.
With `t=64`, `T` SHALL be `t x n`, its seed SHALL have exactly `n+t-1` bits,
and zero-based entries SHALL be `T[i,j]=seed[j-i+t-1]`, over GF(2). A fixed
synthetic vector SHALL define an expected tag.

Bit packing SHALL be MSB-first with unused low bits in the last byte zero.
Lowercase seed hex and `seed_id` SHALL cover those exact packed bytes. The
golden vector SHALL use `n=t=64`, input hex `0123456789abcdef`, 127-bit seed
hex `192a7c4d8615633fcd4ff3fdaafa622e`, seed ID
`46b785fc4ffa59c18eb9bafa71f7399fe48870ded7d3d5a6b7fdaecda8638b84`,
and expected tag hex `6e0cf65a8a33be65`.

The qualification lock SHALL use the system CSPRNG to materialize independent
public seed bits for every frame before execution, storing exact seed hex,
bit length, and `seed_id=SHA256(seed_bytes)`. Execution SHALL read only these
locked seeds. After consistency succeeds, Alice SHALL send the 64-bit tag.
Only then SHALL 64 tag bits count as key-dependent disclosure and `n+63` seed
bits as public control; any earlier failure SHALL count both as zero. Equal
tags SHALL produce `verified_success` with `epsilon_ec=2^-64`; unequal tags
SHALL produce `verify_failed`. The run bound SHALL be
`min(1, verification_invoked_count*2^-64)`. CRC MAY be diagnostic only.

Transcript events SHALL be UTF-8 canonical JSON using `sort_keys=True`,
`separators=(',',':')`, `ensure_ascii=True`, one event per newline, with SHA256
over the exact JSONL bytes. Events SHALL have stable event/parent IDs,
direction, method/frame identity, event type, pass/block or plane identity,
disclosure counts, and payload. Payload SHALL contain only public parity,
syndrome, tag, or public protocol-control values, including block/subblock
ranges and message paths. Explicit corrected raw bit indices, raw/corrected key
bits, and other secret values are forbidden.

The output SHALL distinguish total key-dependent disclosure from public
control bits. Parity, syndrome, and invoked tag disclosure SHALL be summed
from ordered events. Seeds, matrix/rate IDs, and control/abort signals SHALL be
reported separately. Incompatible method-specific decompositions SHALL NOT be
silently cross-ranked.

### R3: Formal Cascade

`cascade_formal_v1` SHALL use deterministic pass/block/permutation schedules
with a domain-separated frame seed. Alice SHALL emit one `BLOCK_PARITY` bit per
primary block. On mismatch, each bisection level SHALL emit one Alice
`BISECTION_LEFT_PARITY` bit; Bob SHALL choose the mismatched half and correct
the last bit locally. Alice parity values SHALL be cached.

`LOOKBACK_RECHECK` SHALL disclose zero new key-dependent bits and use cached
parity. After each correction, all containing blocks in already completed
passes other than the source SHALL be enqueued by `(pass_id,block_id)` FIFO
order and drained before primary processing resumes. Only currently pending
entries may be deduplicated; a dequeued block may be re-enqueued after a later
correction. Events SHALL record direction, parent, source, and monotonic ID,
without serializing corrected positions in public payload. A
`CORRECTION`/Bob-local event SHALL identify only its source event/block/path;
the raw corrected bit index MAY be asserted in in-memory tests but SHALL NOT
appear in any public artifact.

Caps SHALL be 5 seconds/frame, 100000 events, 4096 corrections, and 10000 queue
pops. A cap hit SHALL produce `aborted_resource_limit` and remain a failed
attempt.

Formal qualification SHALL use four passes with bit block sizes
`[16,32,64,128]`, retaining a final short block. Pass 0 SHALL be identity. Each
later public permutation SHALL use PCG64 seeded by the big-endian integer in
the first 16 SHA256 bytes of
`cascade_formal_v1|frame=<dataset_id:frame_id>|base=<base_seed>|pass=<p>`.
Synthetic base seed SHALL be `2026072521`; real base seed `2026072522`.

### R4: Formal LDPC

`ldpc_formal_v1` SHALL use MSB-first bit planes. Alice SHALL send syndromes and
Bob SHALL form local syndrome deltas. Version 1 SHALL support exactly 64
symbols and `q=2^m` for `1<=m<=10`; every bit-plane code SHALL have `n=64`.
The fixed family SHALL be `r050=(32 checks/rank, rate .5)`,
`r0375=(40,.375)`, `r025=(48,.25)`, and `r0125=(56,.125)`. A plane's selected
rate SHALL be frozen by dataset/plane before confirmation. Shortening and
puncturing are forbidden.

The generator SHALL be `gf2_sparse_accumulator_v1`, with `H=[A|B]`; `B` SHALL
be a unit lower-bidiagonal `m_checks x m_checks` matrix. Each A-column SHALL
choose `min(3,m_checks)` distinct rows with PCG64 seeded by the big-endian
integer in the first 16 bytes of SHA256 over
`gf2_sparse_accumulator_v1|n=64|rate=<rate_id>|plane=<plane_id>|column=<column_id>`.
GF(2) rank SHALL equal `m_checks`. Canonical bytes SHALL be ASCII `HGF2V1`,
little-endian uint32 `(m_checks,n)`, then C-order uint8 matrix bytes. Files
SHALL be named `formal_codebook_n64_<rate_id>_plane<plane_id:02d>.hgf2v1` and
indexed by `formal_codebook_manifest.json` with hash/rank/rate/generator data.

Per-plane `p_hat` SHALL come only from sacrificed tuning/calibration frames,
excluded from qualification denominators. The lock SHALL record error/total
counts, `p_hat`, selected input hash, and mapping. With
`p=clip(p_hat,1e-4,.49)` and
`h2(p)=-p*log2(p)-(1-p)*log2(1-p)`, the selector SHALL compute
`d_req=min(.875,1.20*h2(p))` and choose the smallest syndrome fraction in
`{.5,.625,.75,.875}` meeting it, otherwise `unsupported_domain`.
Confirmation SHALL NOT inspect current Alice truth or update calibration.

`comparison_bench/requirements-formal-ir.txt` SHALL pin `ldpc==2.4.1`, failing
closed on mismatch.
`BpOsdDecoder` SHALL use `error_rate=p`, `max_iter=50`,
`bp_method=minimum_sum`, `ms_scaling_factor=1.0`, `schedule=serial`,
`omp_thread_count=1`, explicit deterministic `serial_schedule_order=[0..63]`,
`osd_method=OSD_0`, and `osd_order=0`. It SHALL NOT pass
`random_serial_schedule`: the pinned 2.4.1 docstring advertises the keyword but
the actual constructor rejects it. Explicit order SHALL NOT be omitted. No
fallback is permitted.
Formal success SHALL require every plane's syndrome consistency followed by
Toeplitz verification.

Preflight SHALL construct, without decoding, a 1-by-64 uint8 parity matrix
having only `H[0,0]=1`, and instantiate `BpOsdDecoder` with the exact frozen
kwargs and `error_rate=.01`. It SHALL inspect actual constructor acceptance,
not infer support from a docstring. Version mismatch, constructor rejection,
missing explicit order, or any probe exception SHALL produce
`preflight_unavailable` before frame attempts.

### R5: Artifacts, Provenance, and Status

The required named top-level artifacts SHALL be `pre_run_plan.json`,
`formal_frame_outcomes.csv`, `formal_transcript.jsonl`,
`formal_run_manifest.json`, `formal_codebook_manifest.json`, and
`formal_qualification_report.json`, under a fresh additive run directory.
The lock SHALL preserve every atomic `dataset_id:frame_id:pair_idx` source row,
source hash, mapping, and exactly 64 ordered `pair_idx=0..63` values per frame.
Generic reshaping that loses this provenance is forbidden. Frame outcomes SHALL
use `dataset_id:frame_id`, `n_pairs`, and `pair_idx_sequence_sha256`. LDPC
matrix binaries SHALL live under `codebooks/` and be indexed by the required
top-level manifest.

Required frame fields SHALL include the key fields, method, attempted and
denominator flags, status/failure, domain and raw SER, verification invocation,
seed ID/tag/epsilon, total and method-specific key-dependent disclosure, public
control bits, transcript event range/hash, runtime, and codebook/config IDs.

Status precedence SHALL be `preflight_unavailable`, `invalid_input`,
`unsupported_domain`, `backend_unavailable`, `aborted_resource_limit`,
`decoder_error`, `syndrome_inconsistent`, `decode_failed`, `verify_failed`,
`verified_success`. The first four SHALL have `attempted=false` and remain
visible but outside the statistical denominator; every later status SHALL
have `attempted=true` and remain in it. Any requested non-attempt SHALL fail an
all-frames-attempted promotion gate.

### R6: Qualification and Promotion

Deterministic noiseless, single-error, Cascade look-back, LDPC syndrome, and
Toeplitz vectors SHALL pass 100%. Synthetic qualification SHALL use fixed
`q=1024`, 64-symbol frames, 32 independent-bit-flip frames at `p=.01` and 32
at `p=.02`, with all seeds predeclared. Per method/stratum promotion SHALL
require at least 31/32 verified successes and zero unclassified, internal,
provenance, or accounting failures.

Synthetic v3 SHALL use exactly one
`numpy.random.Generator(PCG64(2026072501))` for Alice. In order, exactly four
calls SHALL generate 32-by-64 int64 symbol batches for `.01` calibration,
`.01` qualification, `.02` calibration, and `.02` qualification. No additional
Alice seed or generator is permitted.

Each natural symbol SHALL become an MSB-first 10-bit natural word before exact
independent XOR flips. Noise generators SHALL be PCG64 `2026072513` for `.01`
calibration, `2026072511` for `.01` qualification, `2026072514` for `.02`
calibration, and `2026072512` for `.02` qualification. Flipped words SHALL be
converted back to natural symbols and supplied with locked `gray` mapping.
Calibration SHALL remain canonical and excluded from denominators.

Canonical qualification IDs SHALL be
`synthetic_q1024_p001_qualification_f000..f031`, then
`synthetic_q1024_p002_qualification_f000..f031`. PCG64 `2026072531` SHALL be
used exactly once to permute those 64 IDs and for no other purpose. The plan
SHALL store the ordered IDs and SHA256 of canonical compact UTF-8 JSON for the
list; the verifier SHALL reconstruct them. System-CSPRNG Toeplitz seeds SHALL
be materialized for exactly the 64 qualification frames, never calibration,
and the same frame seed SHALL be supplied to both methods.

Stored transcript events SHALL be the formal method's exact canonical bytes,
without wrapper, rewrite, reserialization, or appended field. Contiguous groups
SHALL be keyed by existing `(method,frame_key)` in execution order and method
order Cascade then LDPC. Outcome `transcript_sha256` SHALL directly hash the
stored group bytes including newlines; no substitute hash field is permitted.

Before frame calls, runner preflight SHALL execute the exact three focused
formal test files with pytest `-q -p no:cacheprovider`, a fresh external
`--basetemp`, and `PYTHONDONTWRITEBYTECODE=1`. Manifest/report SHALL record
resolved command, exit code, parsed passed count, and output SHA256 over exact
bytes `stdout + b"\n---STDERR---\n" + stderr`. Any failure SHALL finalize six
non-promotion artifacts and SHALL NOT call either formal method.

The run manifest SHALL record hashes of the runner, shared, Cascade, and LDPC
modules; git commit, pre-output-directory porcelain-v1 worktree bytes/hash and
dirty flag; Python/NumPy/pandas/ldpc versions; configuration and plan hashes;
exact argv; UTC start/end; and stop reason. It SHALL hash the plan, outcomes,
transcript, codebook manifest, and indexed codebooks. The report SHALL bind the
manifest hash and promotion gates.

Any run-body exception SHALL invoke a six-artifact finalizer. It SHALL preserve
existing plan/partial bytes without overwrite, exclusively create only missing
required artifacts, record exception/stop reason, and force non-promotion. The
read-only verifier SHALL require the exact artifact set and hash DAG, rebuild
generation/order, bind outcome verification seed IDs to the plan, verify
original transcript group hashes, union bound, denominators, statuses, source
provenance, and report gates.

Synthetic v1 partial and v2 contract-violating diagnostics SHALL NOT support
promotion. v2 SHALL receive an additive `invalid_run_notice.json` naming its
unused declared Alice/frame-order seeds, undeclared Alice seeds, any transcript
contract breach, and fresh v3 successor. Existing v1/v2 bytes SHALL remain
unchanged.

Real qualification SHALL be per-method gated on synthetic promotion. The
verified v3 report promotes `cascade_formal_v1` in both synthetic strata, but
does not promote `ldpc_formal_v1` (29/32 at `.01`, 14/32 at `.02`). This change
SHALL NOT run real LDPC or replace it with a lite method. Any later LDPC real
run requires a new improvement change and new synthetic promotion.

The existing v1 Cascade lock at
`comparison_bench/outputs_comparison/formal_ir_methods/20260725_v1_real_cascade/`
SHALL never execute because its plan binds synthetic base seed `2026072521`,
not real base seed `2026072522`. Existing plan SHA256
`3fd15043dc6e43c0eb4365e5ebaf57990dfc917eff908ef26d3804cbcaea07ab` and lock
SHA256 `aec7ffa3cdcb471748e6c41920cfa82b9df1dc4745d85c4ce66456f9fce904c9`
SHALL remain unchanged. An additive `invalid_lock_notice.json` SHALL record
those hashes, the mismatch, zero method calls, absence of run artifacts, and
only the v2 successor. No v1 seed, file, or output SHALL be reused.

The only runnable Cascade real root SHALL be
`comparison_bench/outputs_comparison/formal_ir_methods/20260725_v2_real_cascade/`,
with matching `run_id=20260725_v2_real_cascade` and real Cascade base seed
exactly `2026072522`.
Its immutable `real_data_lock.json` SHALL retain source/path hashes, domain and
mapping, method eligibility, selection seeds and ordered-list hashes, all 120
selected frame records and atomic source rows, `pair_idx=0..63` sequence hashes,
final-IR-v1 manifest/split hashes with an empty-overlap assertion, 60
confirmation-only CSPRNG Toeplitz seeds, and `lock_content_sha256`. That hash
SHALL be SHA256 of UTF-8
`json.dumps(lock_object_without_lock_content_sha256,ensure_ascii=True,sort_keys=True,separators=(',',':'))`;
the field is omitted from its own preimage, and the verifier SHALL recompute
that exact rule. `pre_run_plan.json` SHALL store only `declared_argv` for the
intended semantic invocation. `formal_run_manifest.json` SHALL store actual
argv; its semantic arguments SHALL match `declared_argv`, apart from the
resolved interpreter/program path. It is a
seventh required top-level real-run artifact in addition to the six R5
artifacts; a real-run verifier SHALL reject any other top-level artifact except
indexed codebooks.

The source SHALL be
`real_sidecars_frame_batch.parquet` SHA256
`967f569c3b3977cc9846025fc9af9b2faf3aa7d89b4e52e0d0ca804f5ab972cc`.
After sorting each eligible group by `(dataset_id,frame_id)`, PCG64 seed
`2026072541` SHALL select the first 60 permuted eligible `bw100` frames for
sacrificed calibration, and PCG64 seed `2026072542` SHALL select the first 60
permuted eligible `bw120` frames for confirmation. Both groups SHALL be
restricted to `d=1024`, 64 symbols, complete ordered `pair_idx=0..63`, and
frame SER `[.20,.30)`; they SHALL share no frame key with final-IR v1. The
lock/verifier SHALL record and rebuild distinct sorted-eligible,
PCG-permuted-eligible, and first-60-selected hashes. They SHALL be, for bw100,
`adc790769d7c59118fa92c7b1514cd5b27408c8d1ca49d1db4c4c5121d5def52`,
`7e5c92bab7f25ba922a4c510d7359b8d21fe0343cbdc72bf4c2fe6e521ded140`, and
`3430d890e95d0af30b81b8f1c25429ee7175911ba8187510054f557954b91865`; and,
for bw120, `6b4b8fcaed9264aeaa3c90acc027ed8c0e7ba88591672e675f9304bed2a903ec`,
`bee68cb8cb6b182b4d60b68b190c203ac1fb354b77ba38a8b7731c576357d62b`, and
`eb336295544f2f38ebecc24ec9006dc976b23b0d6cdc8342074ce076070df1b9`.
The verifier SHALL stop before execution on any count, source, uniqueness,
domain, disjointness, seed, codebook, calibration, or frozen-plan failure.

`bw100` frames are excluded from confirmation denominators and have no
verification seed. For a later eligible LDPC run, only those sacrificed frames
could provide frozen per-plane calibration; confirmation truth SHALL remain
unread. The `bw120` lock SHALL materialize one CSPRNG Toeplitz seed per frame
before execution. Those seeds are common across methods only when multiple
methods are eligible to run the same lock. V2 SHALL use the same fixed selected
frame identities and list hashes, but 60 fresh CSPRNG confirmation seeds; no v1
seed bytes or IDs may recur.

Before any v2 method call, the real runner SHALL execute exactly
`python -m pytest comparison_bench/tests/test_formal_verification.py comparison_bench/tests/test_cascade_formal.py comparison_bench/tests/test_ldpc_formal.py comparison_bench/tests/test_formal_real_qualification.py -q -p no:cacheprovider --basetemp <fresh_external_temp_dir>`
with `PYTHONDONTWRITEBYTECODE=1`. `FORMAL_IR_TEST_TMP` SHALL be inherited only if
it is a writable external temp root, otherwise set to a fresh external
directory. The immutable run manifest SHALL record resolved command, exit code,
parsed passed count, and SHA256 over
`stdout_bytes + b"\n---STDERR---\n" + stderr_bytes`. Failure or an unparseable
count SHALL finalize without a method call. Independent review of the v2 lock
is mandatory before its single execution; v1 SHALL have no execution path.

Cascade promotion SHALL require 60/60 requested confirmation frames attempted,
zero unclassified/internal/provenance/accounting failures, and 60/60 verified
successes. Lesser results SHALL be retained as non-promotion evidence without
reconfiguration.

Caps SHALL be 5 seconds/frame, the Cascade limits in R3, LDPC 50 iterations,
10 minutes total synthetic, and 20 minutes real per method. Configuration
changes after confirmation begins SHALL stop work for planner review.

The change MAY archive with either formal method non-promoted. A later formal
Polar comparison SHALL include only promoted formal methods. A non-promoted
formal method SHALL require a new improvement change and SHALL NOT be replaced
by its lite predecessor.

## Constraints

- Frozen baseline directories and existing outputs remain untouched.
- Existing public schemas/interfaces must not silently change; additive
  metadata/artifacts are preferred.
- A future frame-identical Polar comparison requires a separate OpenSpec
  change after formal candidate promotion.
