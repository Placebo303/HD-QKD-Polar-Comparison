# Decoder-free GF32 train-source mapping

2026-09-30. Track **DECIDE**. State **CLOSED — DESCRIPTIVE RESULT ACCEPTED**.
UUID `6f821d0b-71e3-46c1-ae84-2da374edbcc2`. No count array read in preparation.
New user grant referring to this successor (verbatim):

> 可以继续下一步

This covered preparation and one bounded execution after independent
Pre-EXECUTE PASS and main dispatch. This batch's one-shot grant is now consumed;
the previous a74e912c grant was also consumed by its own batch.
No other data, prior fitting, decoder, label optimization, publication or
route decision. These are historical V25 20260121 train sources, not the
20260123 Model-F CAL domain; no domain transfer is granted.

## F1 Allowed inputs and metadata gate

Only count input:
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz`.
Four provenance JSONs also allowed, read-only:

- the same run_04 `data_inventory.json` and `split_manifest.json`;
- `openspec/changes/formal-nonbinary-ldpc-v25-empirical-timestamp-channel-and-multilevel-factorization-gate/evidence/data_inventory.json`;
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/build_manifest.json`.

Never follow raw/TTBin/parquet/sidecar paths in these records. No other NPZ,
raw or heldout arrays. Source order / label / expected train pairs:

1. `type2_1M_20260121_184040` / 1M / 307200;
2. `type2_1p5M_20260121_183806` / 1p5M / 424960;
3. `type2_2M_20260121_183657` / 2M / 559872.

Exact key per source: `{source_id}_N_ab_train_N_ab_train` (actual writer double
concatenation). Strip each physical ZIP member's `.npy` suffix, then require
exactly these three logical keys (no missing/extra/duplicate members). Inspect Zip/NPY
headers only before values: shape=(1024,1024), dtype=float64, C-order,
non-object. Provenance JSONs must agree on source IDs and their pairs paths
under `v13r3fresh_pairs_20260816/{source_id}/pairs.parquet`. For upstream
manifest compare source_tag==source_id; normalize backslashes to forward
slashes, then require the exact repository-relative suffix
`comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/{source_id}/pairs.parquet`
in its absolute Windows path or the inventory relative path; do not follow it.
Each source in both inventories must have these exact role fields:

- data_role: `characterization/empirical-joint (NOT qualification; may be split train/validation/holdout)`;
- allowed_uses: `characterization; channel-model comparison; factorization gate; source-drift analysis; train/validation/holdout split by time`;
- forbidden_uses: `fresh qualification; promotion; final FER claim`.

Split manifest
must give 0.60/0.20/0.20, the source set and train totals above (sum 1292032).
STOP `SOURCE_OR_SPLIT_UNRESOLVED` before values on missing/disagreeing roles,
paths, ratios, totals or header profile. Do not infer a role from key alone.

Provenance level is `DOCUMENTED_TRAIN_ROLE_CONSISTENT`. Writer train mask is
ascending unique frame IDs; actual frame boundaries are not saved. Records
do not bind an actual historical command/writer version to NPZ bytes, so this
does not independently reconstruct the raw split. Preserve this limitation;
do not add hashes or demand invented binding evidence.

## F2 Value gate and mapping

After F1 PASS, read one admitted source at a time with allow_pickle=False.
Require finite, nonnegative integer-valued float64 counts and sum equal to
its frozen train total; otherwise STOP `COUNT_VALUE_MISMATCH`. Convert to
int64 for exact accumulation; totals are within exact float64 representation.
Axis0=A, axis1=B follows writer `a*1024+b` reshape and the V25 report.
Natural F03: U1(s)=(s>>5)&31, U2(s)=s&31, E1=U1(A)^U1(B). GF32 addition
is XOR; record polynomial37 convention but perform no multiplication.
Compute internal C[e,b] (32x1024), h[e]=sum_b C[e,b]. Verify N=sum h=sum C
=sum input, PMF normalization and entropy bounds. No pooling or Gray mapping.

## F3 Exact outputs and limits

Per-source fields: source ID/label/key, N, 32-bin counts h and PMF h/N,
n_zero, n_nonzero, p_zero, H(E1) bits, H(E1|B) bits, I(E1;B)=H-Hcond.
For Nb=sum_e C[e,b]>0, Hcond=sum_b Nb/N * H(C[:,b]/Nb); zero columns have
weight0. Require 0<=Hcond<=H<=5 within 1e-10; tiny negative I may be clamped
to0 within this tolerance.
Nonzero TV=0.5*sum_{e=1..31}|h[e]/n_nonzero-1/31|. For each b with
nb_error>0, TV_b uses C[1:,b]/nb_error in that formula; report its mean
weighted by nb_error/n_nonzero. Also report observed B columns, error-bearing
B columns, and numbers of those with <5 and <20 errors. If n_nonzero=0,
both nonzero TV fields are null. These are empirical, potentially sparse
diagnostics, not independent-sample confidence or stationarity claims.
Do not export input/conditional arrays, frame lists, fitted prior or pooled
statistics. `DESCRIPTIVE_MAPPING_COMPLETE` only records these historical
documented-train statistics; no calibration, current Model-F law, FER/SKR,
method success, qualification or route decision.

## F4 Resources, artifacts, command and review

One process; <=60s from metadata admission through mapping; RSS<=1GiB.
Check before each source and after return. Fresh root
`workspace/gf32_source_map_6f821d0b/`; refuse existing root; no retry/repair,
overwrite, commit/push/public upload. On STOP retain partial completed
sources and mark incomplete; never fabricate unread sources/denominators.
Exactly three root files: `manifest.json`, `source_summary.json`,
`RESULT_LOG.md`. Manifest records gates, header/source profile, admitted and
attempted sources, resources, exact command and dirty-tree reference UUID
(the frozen batch UUID, provenance only, not a hash/state binding). Log records
execution and subsequent independent review/main acceptance append-only.

Exact one-shot command after Pre-EXECUTE PASS and main acceptance:
`wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_source_map --execute --out-root workspace/gf32_source_map_6f821d0b`

Dry-run reads no real input and writes nothing. Tests use fake counts/NPZ and
provenance only. Independent Pre-RESULT reviewer may reread only actually
attempted F1-admitted train arrays and allowed provenance to recompute F2/F3 under this same grant;
if F1 fails neither operator nor reviewer may read count values.
SM1 inputs/roles/headers; SM2 values/axes/mapping/totals; SM3 formulas,
per-source/no-array-export/claim limits; SM4 resources/STOP/root; SM5 focused
fake math/gate/zero-read tests; SM6 independent Pre-EXECUTE; SM7 independent
Pre-RESULT; SM8 main acceptance and repo memory triage. Operator cannot
self-accept. OpenSpec `audit-gf32-train-source-mapping` freezes the two
implementation files. Preserve original outputs and unrelated dirty changes.

## Independent Pre-EXECUTE and main dispatch — 2026-09-30

Independent reviewer `/root/source_contract` reported PASS for SM1–SM6:
allowed NPZ and four JSON inputs exist; provenance roles, paths and split
contract match; static review confirms metadata/header admission precedes
payload reads and the formulas, per-source outputs and STOP rules match F1–F4.
The reviewer independently ran fake-only tests: 26 passed in 1.56s, with only
the existing pytest `cache_dir` configuration warning. Dry-run exit0 read no
provenance/NPZ and wrote no files. Branch is
`formal-ir-v72p1-addendum-clean`; target root is absent. No actual NPZ/header
or count value was read in this review. Historical documented-train provenance
limitations and claim ceiling remain binding.

Main thread accepts this scoped Pre-EXECUTE PASS and dispatches exactly the
one-shot F4 command under the quoted user grant. No retry, extra data or decoder
execution is authorized. Actual F1 header admission may STOP the batch; PASS
here does not pre-judge those headers or resulting source statistics.

## Independent Pre-RESULT and main acceptance — 2026-09-30

Independent reviewer `/root/source_contract` reported SM7 PASS. It independently
recomputed each of the three admitted count inputs by source and by `A` row,
including all `C[e,b]` entries, all 32 `E1` bins, totals, entropy, conditional
entropy, mutual information and both nonzero-TV summaries. The independent
results match the operator summaries with maximum absolute difference
`<=1e-12`. The reviewer also reconfirmed the four provenance JSONs, role/path/
split agreement, each `(1024,1024)` float64 C-order input, finite nonnegative
integer-valued counts, and no pooling or exported conditional arrays.

Main thread accepts the batch only as historical `DOCUMENTED_TRAIN_ROLE_CONSISTENT`
descriptive mapping evidence. This is not an independently reconstructed raw
split, fitted prior, mechanism-gain result, current Model-F transfer, or route
decision. The one-shot authorization is consumed. Any successor needs a new
packet and explicit authorization; none is dispatched here.
