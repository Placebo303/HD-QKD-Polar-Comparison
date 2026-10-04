# Design: Binary LDPC v4 16 dB Transfer Qualification v1

## 1. Frozen Method Prerequisite

The transfer lane accepts only the exact strictly verified promoted package:

`comparison_bench/outputs_comparison/formal_ir_methods/20260728_v2_binary_ldpc_v4_synthetic/`.

It reuses, byte-for-byte:

- `ldpc_formal_v4`;
- the selected candidate per Gray bit plane;
- the formal codebooks and channel model;
- decoder/backend policy and `ldpc==2.4.1`;
- 256-symbol frames and 2623-bit Toeplitz verification;
- complete/per-frame resource caps;
- transcript, leakage, failure, denominator, and promotion accounting.

No 16 dB calibration, development, matrix selection, rate adaptation, or
synthetic retuning is permitted.

## 2. Exact 16 dB Source

Bind the unique Type-II 16 dB raw acquisition:

- main:
  `D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_16dB_2026-01-30_224900\Type2_5s_16dB_2026-01-30_224900.ttbin`;
- main SHA256:
  `f7ff84d769d0a4f0e0831c006a8c654649a30beb3cf51769e4ceea7e54840e79`;
- `.1.ttbin` chunk SHA256:
  `c97175e98124f83d8627d6d5a192647cbe58d3c06df6afeac38691903013895e`;
- sidecar root:
  `e2e_new_ttbin_fullgrid\sidecars`;
- datasets: exactly `d1024_bw120`, `d1024_bw180`, and `d1024_bw200`,
  each at `blk0`.

For each dataset bind `a_eff.npy`, `b_eff.npy`, and `sidecar_meta.json` by
absolute path, bytes, and SHA256. Require one-dimensional equal-length integer
arrays in `[0,1023]`, strict unsampled `from_ttbin`,
`materialized_from_ttbin`, nearest pairing, q/dimension 1024, exact bin width,
and at least 128 complete contiguous frames. Natural incomplete tails are
ignored, never padded.

Processing semantics SHALL be read from their recorded locations rather than
invented by the adapter: require `materialize_params.used_params.mapping` to
be `gray`, and require `symbolization_snapshot` to contain the exact
dimension 1024, dataset bin width, `block_symbols=256`, `mapping=gray`,
`bit_order=lsb0`, and `wrap_rule=floor_div`. Its `ttbin_file` must reconstruct
to the locked raw main through the same relocation rule. Missing fields fail;
the adapter must not synthesize defaults.

The pre-registered sidecar SHA256 values are:

| Dataset | `a_eff.npy` | `b_eff.npy` | `sidecar_meta.json` |
|---|---|---|---|
| `d1024_bw120` | `f902479141d5c40a634e29b6c74b06be43033a206735b41da73d2363f3d84205` | `383cec398462f8a28d38f78c1d1f1c5bd49600641b07a0eacd4c8403341054dc` | `d838f023783bdf16b2aea6acde3f96d5fbb492f9ce4ad3b81ecefafc07e3dd0b` |
| `d1024_bw180` | `e6b3cdfe3dc74b51699a0443b1fa9e1518845651c0add94ca7c6526d24daea1c` | `b3d41c38d8952168332f67d81caad4f9195d248ff3be8e006621895775f69716` | `dea51fead31c8fa8729fe99c9bcde2463a62e54e4780b8c9352385dd236f4e83` |
| `d1024_bw200` | `656f808bec1920ff097cc01ecf546b73c52efc8f531c23a6e58eacfdf39f6f42` | `e2fa8d2a686f176626f1759dd0523a5235f097f6d805df98d1e7509a36683968` | `62971bdacc4bc457443d40c380ee362b0ab002ec75408e0586bc3bd2ec55e8c9` |

The materializer semantics are source-bin indices: the frozen baseline
`src/workflow/export_joint_sequence_sidecar.py` computes modulo-d bin
coordinates and writes them directly to `a_eff.npy`/`b_eff.npy`; Gray
conversion remains in the formal LDPC bridge. Bind the exact baseline source
SHA256
`c05f52f960cf292a4cc5c7a1c0591902a48a1e4fc0d270adc08f9b97b6867d16`
and reject any attempt to pre-transform arrays in the transfer adapter.

## 3. Relocation Provenance

Historical metadata records the now-absent prefix
`D:\Data\QKD_Loss`; the capture and its complete output tree now live under
`D:\Data\Raw Data\QKD_Loss`.

The source lock SHALL contain a canonical
`binary_ldpc_v4_source_relocation_v1` record with:

- recorded and actual roots;
- proof that the recorded source path does not resolve;
- exact case-insensitive relative suffix equality from
  `TypeII_776.1nm_3s` onward;
- the actual raw main/chunk file records;
- file records for `run_config.json`, `results/ttbin_parsing/ttbin_source.txt`,
  `ttbin_config.json`, `ttbin_metrics.json`, `results/inputs_snapshot.json`,
  `resolved_config.json`, and `run_config.source.txt`;
- reconstruction of every embedded raw/output path through the same single
  prefix substitution;
- the three sidecar records and metadata hashes.

The pre-registered provenance SHA256 values are:

| Relative path | SHA256 |
|---|---|
| `run_config.json` | `78a67343198e97be075ebe90fa45f9ff3dcd05ab583467e0b5efa286b9f97490` |
| `results/ttbin_parsing/ttbin_source.txt` | `6bd6db3267a8e15d54942defcd306cd0a423fccbdc93f8165eb47e345f60f87c` |
| `results/ttbin_parsing/ttbin_config.json` | `b2a0025e9f93090300d53d285123c5d43c17ffe16af5f6ec31d8e252e0f1c24b` |
| `results/ttbin_parsing/ttbin_metrics.json` | `18859063834e843c4b9cdf2d8b4f8f20f3212650e97e16a591f2960a140f6ed4` |
| `results/inputs_snapshot.json` | `7f782ce337f6cd379e378d99b1bef8c458a5520014475d1166feff38f3c5f1ab` |
| `results/resolved_config.json` | `d9669aabf24ac2eaba6fdcddc530672c974e7524343a7bbd763fa91368099cd5` |
| `results/run_config.source.txt` | `9df6ab9c81675d2ff4fbfe8ec364619cc8eb3c55faca6922f83aa1130d02fad3` |

The adapter must not rewrite metadata or create symlinks/copies. Any suffix
mismatch, resolvable competing recorded source, second substitution rule,
hash drift, missing provenance snapshot, or raw acquisition ambiguity fails
before an output directory exists. Reports must expose
`source_relocation=true`.

## 4. Selection and Isolation

Construct source-aware and payload identities from the exact 256-symbol Alice
and Bob bytes. Reject duplicate payload identities within or across strata.

Rank candidates by:

`SHA256("binary_ldpc_v4_16db_transfer_selection_v1|<stratum>|<frame_identity>")`.

Select the first 128 per stratum. Freeze order before decoding. Use three new
16-byte CSPRNG roots, one per stratum, and derive exactly 128 Toeplitz seeds
per root. Prove roots/seeds are disjoint from v3, development, synthetic, and
any existing real plan.

## 5. Qualification Gate and Lifecycle

Package identity:

- run ID `binary_ldpc_v4_16db_transfer_qualification_v1`;
- plan, source lock, run manifest, and report schemas ending `_v1`;
- output root chosen only after main-thread plan review.

Lifecycle is strictly:

1. source `lock/prepare` once;
2. main-thread review;
3. execute once;
4. read-only verify once.

Each of bw120/bw180/bw200 retains all 128 denominators and must achieve at
least 126 `verified_success` with zero backend/source/internal/accounting/
unclassified failures. Failure is immutable `non_promoted_transfer`; do not
tune or rerun from 16 dB outcomes.

The verifier reconstructs prerequisite artifacts, scoped source hashes,
relocation, raw/sidecar/provenance files, candidate pool, selection, roots,
Toeplitz seeds, outcome/transcript/public payloads, leakage, denominators, and
gates. It reports `decoder_reexecution=false`.
