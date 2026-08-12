# Design: implement-formal-cascade-and-ldpc

## Boundary and Roles

This is a paper-grade, offline reconciliation model under an already
authenticated public-channel assumption. Alice's frame is the reference;
Bob receives reconciliation messages and corrects locally. Authentication
transport cost, hardware timing, finite-key/Route-A numerical claims, Polar
adaptation, and three-method comparison remain outside this change.

`cascade_lite` and `layered_ldpc_lite` remain unchanged historical baselines.
Their existing outputs MUST NOT be relabeled as formal evidence.

## Additive Result Contract

The implementation MUST preserve current public result schemas. Formal runs
use method identities `cascade_formal_v1` and `ldpc_formal_v1`, and add
metadata/additive frame tables rather than silently changing legacy columns.
Each frame records input/provenance identity, attempted status, failure reason,
method transcript reference/hash, verification seed/seed-id/tag length, and:

- `key_dependent_disclosure_bits_total`;
- method-specific components (Cascade parity/bisection/look-back; LDPC
  syndrome by bit-plane);
- `verification_tag_bits`;
- `public_control_bits_total` (seeds, matrix IDs, rate IDs, abort/control);
- a labeled statement that cross-method leakage ranking is disallowed until
  decomposition compatibility is separately established.

All outputs are additive under
`comparison_bench/outputs_comparison/formal_ir_methods/<run_id>/`.

Each run directory has these required named top-level contract artifacts:

- `pre_run_plan.json`;
- `formal_frame_outcomes.csv`;
- `formal_transcript.jsonl`;
- `formal_run_manifest.json`;
- `formal_codebook_manifest.json` (present for LDPC; an explicit empty/not-used
  manifest for a Cascade-only run);
- `formal_qualification_report.json`.

LDPC codebook binaries additionally live under `codebooks/` and are indexed by
the top-level codebook manifest. `pre_run_plan.json` is the immutable run lock:
it embeds ordered frame selections and seed records and references the
read-only source table by path/hash.

Required frame fields are `dataset_id`, `frame_id`, `n_pairs`,
`pair_idx_sequence_sha256`, `method`,
`attempted`, `denominator_included`, `status`, `failure_reason`, `dimension`,
`frame_len_symbols`, `raw_ser`, `verification_invoked`, `verification_seed_id`,
`verification_tag_bits`, `epsilon_ec`, `key_dependent_disclosure_bits_total`,
`public_control_bits_total`, `transcript_first_event_id`,
`transcript_last_event_id`, `transcript_sha256`, `runtime_s`, and the relevant
method-specific disclosure/config/codebook fields.

Status precedence is first-match in this order:
`preflight_unavailable`, `invalid_input`, `unsupported_domain`,
`backend_unavailable`, `aborted_resource_limit`, `decoder_error`,
`syndrome_inconsistent`, `decode_failed`, `verify_failed`,
`verified_success`. The first four have `attempted=false` and are excluded from
the statistical denominator, but still appear as requested-frame records and
fail any gate requiring all frames attempted. From `aborted_resource_limit`
onward, `attempted=true`, `denominator_included=true`, and failures remain in
the denominator. `preflight_unavailable` is also the required run result for a
pinned dependency mismatch.

## Locked Frame Provenance

Formal locks MUST ingest a table whose atomic symbol-pair key is
`dataset_id:frame_id:pair_idx`. A generic reshape or frame re-numbering that
loses source `frame_id` or ordered `pair_idx` is forbidden. Lock verification
checks unique atomic keys, exactly 64 symbols and ordered `pair_idx=0..63` per
frame, source-file hash, mapping, and ordered selected frame keys before
execution. Frame outcomes use `dataset_id:frame_id` plus
`pair_idx_sequence_sha256`; the lock retains every atomic pair row.

## Shared Formal Verification

Formal success means both reconciliation-specific consistency and an
independent universal2 Toeplitz hash verification pass. CRC may remain a debug
diagnostic but MUST NOT determine formal success.

Verification input is the frame's symbols transformed by the locked mapping,
then MSB-first flattened into `x` of length `n`. The Toeplitz matrix is
`T in {0,1}^{t x n}`, with `t=64`, and consumes exactly `n+t-1` seed bits:
`T[i,j] = seed[j-i+t-1]` for zero-based `i,j`. Matrix-vector multiplication is
over GF(2). A fixed synthetic test vector and expected tag SHALL be committed
before qualification.

Before a qualification run, its lock uses the system CSPRNG to materialize one
independent public seed bitstring per locked frame. It stores the exact seed as
hex plus `seed_id = sha256(seed_bytes)` and the bit length. Execution reads
these locked values only and MUST NOT generate or replace a seed. Domain/frame
association is covered by the lock manifest and seed ID.

Bitstrings are packed MSB-first (`numpy.packbits(..., bitorder="big")`); unused
low bits in the final byte are zero. Seed hex is lowercase packed-byte hex, and
`seed_id` hashes those exact packed bytes. The golden vector is `n=t=64`,
input `0123456789abcdef` interpreted MSB-first, 127 seed bits packed as
`192a7c4d8615633fcd4ff3fdaafa622e`, seed ID
`46b785fc4ffa59c18eb9bafa71f7399fe48870ded7d3d5a6b7fdaecda8638b84`,
and expected tag `6e0cf65a8a33be65`.

After reconciliation consistency succeeds, Alice sends the 64-bit tag to Bob.
Only when `verification_invoked=true` do the tag's 64 bits count as
key-dependent disclosure and the `n+63` seed bits count as public control.
Decode, input, backend, or resource failure before verification records zero
tag and seed communication. Equal tags produce `verified_success` with
per-frame `epsilon_ec=2^-64`; unequal tags produce `verify_failed`. The
run-level union bound is `min(1, verification_invoked_count * 2^-64)`.

Each transcript event is canonical JSON encoded as UTF-8 with
`sort_keys=True`, `separators=(',', ':')`, and `ensure_ascii=True`, followed by
one newline. `transcript_sha256` hashes the exact concatenated JSONL bytes.
Every event contains `event_id`, `frame_key`, `method`, `event_type`,
`direction`, `parent_event_id`, `pass_id`, `block_id` or `plane_id`,
`key_dependent_bits`, `public_control_bits`, and `payload`. Payloads may contain
only public parity/syndrome/tag values and public protocol-control identifiers,
including block/subblock ranges and message-path references. Explicit corrected
raw bit indices, raw or corrected key bits, and other secret values are
forbidden in `formal_transcript.jsonl`.

## Cascade Formal Protocol

Each frame uses deterministic, domain-separated pass/permutation seeds and a
predeclared ordered pass/block schedule. For every primary block, Alice emits
one `BLOCK_PARITY` bit and Bob compares it with his local parity. On mismatch,
each bisection layer makes Alice emit one `BISECTION_LEFT_PARITY` bit for the
left half; Bob chooses the mismatched half and corrects the final bit locally.
Alice parity values are cached by block/subblock identity.

After every correction, enqueue all blocks in every already-completed pass
that contain the corrected bit, except the correction's source block. Entries
are ordered by `(pass_id, block_id)` in a FIFO. A pending set deduplicates only
currently queued items; after dequeue, a later correction may enqueue the same
block again. Drain the entire queue after each primary correction before
continuing the current pass. `LOOKBACK_RECHECK` reveals zero key-dependent
bits and uses the cached Alice block parity. If it mismatches, its bisection
events disclose fresh one-bit left parities and may recursively enqueue work.

Events record direction (`alice_to_bob`, `bob_local`, or `control`), parent
event, source block/subblock and public message path, monotonically increasing
event ID, and disclosure counts. A `CORRECTION`/Bob-local event records only
its source event/block/path in the public artifact; the corrected raw bit index
exists solely in in-memory test diagnostics and MUST NOT be serialized.

Formal v1 qualification fixes four passes with bit block sizes
`[16,32,64,128]`; the last short block is retained. Pass 0 uses identity
ordering. For pass `p>0`, the public permutation seed is the big-endian integer
in the first 16 bytes of
`SHA256(UTF8("cascade_formal_v1|frame=<dataset_id:frame_id>|base=<base_seed>|pass=<p>"))`,
used by `numpy.random.Generator(PCG64(seed)).permutation(n_bits)`. Synthetic
uses public base seed `2026072521`; real qualification uses `2026072522`.

Hard caps are 5 seconds wall time per frame, 100000 events, 4096 corrections,
and 10000 queue pops. Reaching any cap emits an abort control event and status
`aborted_resource_limit`; there is no silent partial success.

## LDPC Formal Protocol

Symbols are mapped MSB-first into bit planes. Alice sends each selected
bit-plane syndrome; Bob calculates the local syndrome delta and decodes an
error estimate. Parameter/rate selection MUST be fixed before a frame is
processed and MUST NOT inspect that frame's Alice truth. Version 1 uses a
pre-registered fixed rate family only: no shortening or puncturing.

Version 1 supports exactly 64 symbols and `q=2^m`, `m in [1,10]`; every
bit-plane code has `n=64`. Its rate family is fixed:

| rate_id | m_checks = rank | design rate | syndrome fraction |
|---|---:|---:|---:|
| `r050` | 32 | 0.500 | 0.500 |
| `r0375` | 40 | 0.375 | 0.625 |
| `r025` | 48 | 0.250 | 0.750 |
| `r0125` | 56 | 0.125 | 0.875 |

`generator_id=gf2_sparse_accumulator_v1`. For each
`(n,rate_id,plane_id)`, construct `H=[A|B]`. `B` is the `m_checks x m_checks`
unit lower-bidiagonal binary matrix (ones on the diagonal and immediately
below it), so it is full rank. For each column of `A`, derive a PCG64 seed as
the big-endian integer represented by the first 16 bytes of
`SHA256(UTF8("gf2_sparse_accumulator_v1|n=64|rate=<rate_id>|plane=<plane_id>|column=<column_id>"))`;
use `numpy.random.Generator(PCG64(seed))` to choose `min(3,m_checks)` distinct
row indices without replacement. GF(2) rank MUST equal `m_checks`.

Canonical matrix bytes are ASCII `HGF2V1`, followed by little-endian uint32
`(m_checks,n)`, followed by C-order uint8 `H` bytes; SHA256 covers these exact
bytes. Matrix files are named
`formal_codebook_n64_<rate_id>_plane<plane_id:02d>.hgf2v1`; the index is exactly
`formal_codebook_manifest.json`. It records filename, hash, dimensions, rank,
design rate, generator ID, and construction-domain string. Codebooks are
materialized and verified before the first frame.

Rate selection is calibrated only from independent sacrificed tuning frames,
which never enter qualification denominators. For each dataset/plane, the lock
records error/total bit counts, `p_hat`, selected input hash, and mapping.
Let `p=clip(p_hat,1e-4,0.49)`,
`h2(p)=-p*log2(p)-(1-p)*log2(1-p)`, and
`d_req=min(0.875, 1.20*h2(p))`. Select the smallest syndrome fraction in
`{0.5,0.625,0.75,0.875}` at least `d_req`; if none exists, record
`unsupported_domain`. The resulting dataset/plane rate IDs and `p_hat` values
are frozen before confirmation. Confirmation MUST NOT read the current Alice
truth to estimate a channel value, select a rate, or update calibration.

The formal dependency lock is
`comparison_bench/requirements-formal-ir.txt` and pins `ldpc==2.4.1`; a
mismatch is fail-closed.
`BpOsdDecoder` parameters are exactly `error_rate=p`, `max_iter=50`,
`bp_method="minimum_sum"`, `ms_scaling_factor=1.0`, `schedule="serial"`,
`omp_thread_count=1`, `serial_schedule_order=[0,1,...,63]`,
`osd_method="OSD_0"`, and `osd_order=0`.
The run manifest records all values. No decoder or internal bit-flip fallback
is allowed. Formal success requires Bob's corrected bits to satisfy Alice's
syndrome for every plane and then pass shared Toeplitz verification.

The installed 2.4.1 class docstring advertises `random_serial_schedule`, but
the actual constructor rejects that keyword with
`ValueError: Unknown parameter 'random_serial_schedule'`. It is therefore not
a required or passed kwarg. Determinism instead requires all three of
`schedule="serial"`, the explicit full order `[0..63]`, and
`omp_thread_count=1`; omitting the explicit order is forbidden.

Preflight MUST test constructor behavior, not scan the docstring. It constructs
`H_probe` as a 1-by-64 uint8 matrix with only `H_probe[0,0]=1`, then constructs
`BpOsdDecoder(H_probe, ...)` with the exact frozen kwargs above and
`error_rate=0.01`. It MUST NOT call `decode`. Any version mismatch, rejected
keyword/value, missing deterministic order, or constructor exception yields
`preflight_unavailable` before real/synthetic frame attempts.

## Qualification and Promotion Gate

Each method qualifies independently before any Polar adapter or fair
three-method comparison may begin. All deterministic vectors—noiseless,
single-error, hand-built Cascade look-back, LDPC syndrome, and Toeplitz—must
pass 100%.

Synthetic qualification is fixed at `q=1024`, 64 symbols, 32 qualification
frames with independent bit flips at `p=0.01`, and 32 at `p=0.02`. Each
method/stratum requires at least 31/32 `verified_success` and zero unclassified,
internal, provenance, or accounting failures.

### Synthetic v3 Generation and Order

Alice generation uses exactly one
`numpy.random.Generator(PCG64(2026072501))`. In this canonical order, four and
only four calls generate `integers(0,1024,size=(32,64),dtype=np.int64)`:

1. `p=.01` calibration;
2. `p=.01` qualification;
3. `p=.02` calibration;
4. `p=.02` qualification.

No additional Alice seed or generator is allowed. For each batch, natural
symbol integers are converted to MSB-first 10-bit natural words. Independent
XOR bit flips use PCG64 seeds `2026072513` (`.01` calibration),
`2026072511` (`.01` qualification), `2026072514` (`.02` calibration), and
`2026072512` (`.02` qualification), respectively. The flipped 10-bit words are
converted back to natural symbol integers; both sides then enter the formal
methods with the locked `gray` mapping. Calibration remains in canonical order,
is used only for `p_hat`, and never enters attempted/qualification denominators.

Canonical qualification identities are
`synthetic_q1024_p001_qualification_f000..f031` followed by
`synthetic_q1024_p002_qualification_f000..f031`. A single
`Generator(PCG64(2026072531)).permutation(64)` permutes that canonical list and
has no other purpose. `pre_run_plan.json` stores the ordered 64 IDs and
`qualification_execution_order_sha256`, defined as SHA256 of UTF-8
`json.dumps(ordered_ids,ensure_ascii=True,separators=(',',':'))`. The verifier
reconstructs both list and hash.

The lock materializes system-CSPRNG Toeplitz seeds for exactly those 64
qualification frame identities, not for calibration. The same locked frame
seed/seed ID is supplied to both formal methods.

### Synthetic v3 Transcript and Preflight

`formal_transcript.jsonl` stores the exact canonical event bytes emitted by a
formal method. It MUST NOT wrap, rewrite, reserialize, or append fields to an
event. Groups are contiguous in qualification execution order and, within a
frame, method order `cascade_formal_v1`, then `ldpc_formal_v1`, keyed by the
event's existing `(method,frame_key)`. Each outcome's `transcript_sha256` is
exactly the SHA256 of its group's stored JSONL bytes, including every newline.
No alternate/reconstructed transcript hash may mask a mismatch.

Before any frame call, the runner executes exactly:

`python -m pytest comparison_bench/tests/test_formal_verification.py comparison_bench/tests/test_cascade_formal.py comparison_bench/tests/test_ldpc_formal.py -q -p no:cacheprovider --basetemp <fresh_external_temp_dir>`

with `PYTHONDONTWRITEBYTECODE=1`. The resolved command, exit code, parsed passed
count, and output hash are recorded in the run manifest and qualification
report. Output-hash bytes are exactly
`stdout_bytes + b"\n---STDERR---\n" + stderr_bytes`; SHA256 covers that sequence.
Any nonzero exit, unparseable count, or deterministic-vector failure invokes
the six-artifact non-promotion finalizer and prohibits all formal frame calls.

### Synthetic v3 Provenance, Finalization, and Verification

Before creating the output directory, the runner captures git commit and exact
UTF-8 bytes/hash of
`git status --porcelain=v1 --untracked-files=all`, plus a dirty flag. The
manifest records SHA256 for the runner, `formal_ir/shared.py`,
`formal_ir/cascade.py`, and `formal_ir/ldpc.py`; Python, NumPy, pandas, and
ldpc versions; exact invocation argv; UTC start/end; stop reason; and hashes
of configuration and `pre_run_plan.json`.

The artifact hash DAG is non-circular: `formal_run_manifest.json` stores hashes
for the plan, outcomes, transcript, codebook manifest, and every indexed
codebook; `formal_qualification_report.json` stores the manifest SHA256 and
promotion gates. The verifier requires the exact six named top-level artifacts
plus only indexed `codebooks/` files—no missing, extra, or unindexed artifact.

The entire run body is guarded by a six-artifact finalizer. On any exception it
preserves existing plan and partial artifact bytes without overwrite, creates
only missing required artifacts using exclusive writes, records the exception
class/message and stop reason, and produces a non-promotion report. Existing
bytes are evidence and MUST NOT be rewritten to make hashes pass.

The v3 read-only verifier reconstructs generation/order hashes and checks the
exact artifact set/hash DAG, source/version/worktree/config provenance,
outcome seed IDs against the plan, each original transcript group hash,
disclosure totals, `verification_invoked` count and union bound, denominators,
statuses, and every report gate.

Synthetic v1 partial evidence and v2 contract-violating diagnostics are not
promotable. v2 MUST receive an additive `invalid_run_notice.json` recording its
unused declared Alice/frame-order seeds, extra undeclared Alice seeds,
non-authoritative transcript handling if present, and a pointer to fresh v3.
Neither v1 nor v2 may be reused or overwritten.

### Real Lock Eligibility and v1 Invalidation

Real qualification is a per-method continuation of synthetic promotion, not a
second opportunity to tune a synthetic non-promotion. The verified synthetic
v3 report promotes `cascade_formal_v1` in both strata and does not promote
`ldpc_formal_v1` (29/32 at `.01`, 14/32 at `.02`). Therefore this change may
lock and run only `cascade_formal_v1` on real data. It MUST NOT run
`ldpc_formal_v1`, and MUST NOT substitute either lite method. A future LDPC
improvement change must earn a new synthetic promotion before it can receive a
fresh real lock.

The existing
`comparison_bench/outputs_comparison/formal_ir_methods/20260725_v1_real_cascade/`
lock is invalid and SHALL never be executed: its `pre_run_plan.json` binds
synthetic Cascade base seed `2026072521`, while R3 requires real base seed
`2026072522`. Its existing bytes are immutable, unexecuted evidence. Add only
`invalid_lock_notice.json`, recording the exact plan hash
`3fd15043dc6e43c0eb4365e5ebaf57990dfc917eff908ef26d3804cbcaea07ab`, lock hash
`aec7ffa3cdcb471748e6c41920cfa82b9df1dc4745d85c4ce66456f9fce904c9`, the base
seed mismatch, zero formal method calls, absence of run artifacts, and only the
fresh v2 successor path. Do not overwrite or reuse either v1 file or any v1
verification seed.

The only runnable Cascade real root is the fresh additive
`comparison_bench/outputs_comparison/formal_ir_methods/20260725_v2_real_cascade/`,
with `run_id=20260725_v2_real_cascade` and Cascade base seed exactly
`2026072522`.
Before execution, its exclusive `real_data_lock.json` SHALL contain: schema and
run IDs; source path and SHA256; domain and mapping; method eligibility;
selection seeds and canonical ordered frame-key lists/hashes; 60 calibration
and 60 confirmation frame records; every atomic source row in each selected
frame (including `dataset_id`, `frame_id`, `pair_idx`, Alice/Bob symbols, and
source provenance); per-frame `pair_idx=0..63` sequence hash; final-IR-v1
manifest/split hashes and an empty-overlap assertion; 60 confirmation-only
system-CSPRNG Toeplitz seed records; and `lock_content_sha256`. Its SHA256
preimage is UTF-8 `json.dumps(lock_object_without_lock_content_sha256,
ensure_ascii=True,sort_keys=True,separators=(',',':'))`; the field is omitted,
not null, from the hashed object. The verifier recomputes that exact rule. The
accompanying `pre_run_plan.json` binds this lock SHA256, method, frozen Cascade
schedule and base seed, `declared_argv` (the intended semantic run arguments),
caps, and the six-artifact failure-finalizer policy. Only
`formal_run_manifest.json` records actual invocation argv; the verifier checks
its semantic arguments against `declared_argv`, allowing only the resolved
interpreter/program path to differ.
`real_data_lock.json` is an additional required top-level artifact for a real
run; the real verifier allows exactly the six common artifacts plus that lock
and indexed `codebooks/` files only.

The audited source is
`real_sidecars_frame_batch.parquet` SHA256
`967f569c3b3977cc9846025fc9af9b2faf3aa7d89b4e52e0d0ca804f5ab972cc`.
Eligible complete frames are the single `bw100` source group (295) and the
single group-disjoint `bw120` source group (322). Sort each eligible group by
`(dataset_id, frame_id)`, then use `PCG64(2026072541)` for `bw100` and
`PCG64(2026072542)` for `bw120`; take the first 60 indices of each permutation
as the calibration and confirmation execution orders, respectively. The lock
stores three distinct compact-JSON SHA256 values per group: the sorted eligible
list, the full PCG-permuted eligible list, and the first-60 selected execution
list. For `bw100` those values are respectively
`adc790769d7c59118fa92c7b1514cd5b27408c8d1ca49d1db4c4c5121d5def52`,
`7e5c92bab7f25ba922a4c510d7359b8d21fe0343cbdc72bf4c2fe6e521ded140`, and
`3430d890e95d0af30b81b8f1c25429ee7175911ba8187510054f557954b91865`.
For `bw120` they are respectively
`6b4b8fcaed9264aeaa3c90acc027ed8c0e7ba88591672e675f9304bed2a903ec`,
`bee68cb8cb6b182b4d60b68b190c203ac1fb354b77ba38a8b7731c576357d62b`, and
`eb336295544f2f38ebecc24ec9006dc976b23b0d6cdc8342074ce076070df1b9`.

The 60 `bw100` frames are sacrificed: they may establish the LDPC
dataset/plane `p_hat` and rates only in a later eligible LDPC run, but they do
not enter a confirmation denominator and they have no Toeplitz seeds. For this
Cascade-only run they are retained solely as the declared split evidence and
are not executed. The 60 `bw120` confirmation frames receive one CSPRNG seed
each before execution. A lock intended for more than one eligible formal method
would supply that exact frame seed to each; this run supplies it only to the
eligible Cascade method.

Before any v2 formal method call, the real runner executes exactly:

`python -m pytest comparison_bench/tests/test_formal_verification.py comparison_bench/tests/test_cascade_formal.py comparison_bench/tests/test_ldpc_formal.py comparison_bench/tests/test_formal_real_qualification.py -q -p no:cacheprovider --basetemp <fresh_external_temp_dir>`

with `PYTHONDONTWRITEBYTECODE=1`. `FORMAL_IR_TEST_TMP` is inherited only when it
resolves to a writable external temp root; otherwise the runner sets it to a
fresh external directory. The immutable run manifest records the resolved
command, exit code, parsed passed count, and SHA256 over exact bytes
`stdout_bytes + b"\n---STDERR---\n" + stderr_bytes`. A nonzero exit,
unparseable count, or test failure invokes the v2 failure finalizer before any
method call.

The v2 lock uses the same fixed deterministic selected frame identities and
list hashes above, but materializes 60 fresh confirmation CSPRNG seeds. It SHALL
not reuse v1 seed bytes or IDs. Independent lock review is required before the
unique v2 execution; v1 has no execution path.

V2 lock review precedes its unique execution. Promotion requires 60/60 requested
confirmation frames attempted, zero unclassified/internal/provenance/accounting
failures, and 60/60 `verified_success`; this is the predeclared evidence rule
for the claim that the locked domain has at least 95% verified success. Any
lesser result is retained as non-promotion evidence without changing
configuration.

Caps are 5 seconds per frame; Cascade caps defined above; LDPC `max_iter=50`;
10 minutes for the complete synthetic qualification and 20 minutes per method
for real qualification. A stop is evidence, not a reason to tune confirmation.
The change may archive with either method non-promoted. A later formal Polar
comparison may include only promoted formal methods; lite substitution is
forbidden, and improvement of a non-promoted method requires a new change.
