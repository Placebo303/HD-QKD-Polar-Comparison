# Design: Binary LDPC v4 10 dB Transfer Qualification v1

## 1. Frozen prerequisites and scientific boundary

The method prerequisite is exactly:

`comparison_bench/outputs_comparison/formal_ir_methods/20260728_v2_binary_ldpc_v4_synthetic/`

The predecessor real package is exactly:

`comparison_bench/outputs_comparison/formal_ir_methods/20260729_v1_binary_ldpc_v4_16db_transfer/`

The runner and verifier bind every file of both packages by SHA256 and
strictly replay both. The synthetic package must remain promoted. The 16 dB
package must reconstruct as completed, verified, non-promoted, with exact
counts 125/128, 128/128, and 128/128 and zero forbidden failures.

No 10 dB development, calibration, tuning, or parameter selection is allowed.
The scientific claim, if promoted, is only unchanged-method transfer at the
registered 10 dB acquisition.

## 2. Exact 10 dB source

Canonical capture root:

`D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_10dB_2026-01-30_224808`

Raw files:

| File | Bytes | SHA256 |
|---|---:|---|
| `Type2_5s_10dB_2026-01-30_224808.ttbin` | 21328 | `83f85f54a2e0a8573afe2e252fdb9184006f14b2c074998ca8569785b12b1205` |
| `Type2_5s_10dB_2026-01-30_224808.1.ttbin` | 36374336 | `714e7e7171f254b023b352ba024e75f27eca629c40f8fd5df4f73c93045f3877` |

Sidecars are under `e2e_new_ttbin_fullgrid\sidecars\<stratum>\blk0`:

| Stratum | Complete frames | `a_eff.npy` | `b_eff.npy` | `sidecar_meta.json` |
|---|---:|---|---|---|
| `d1024_bw120` | 1108 | `6568dbfa553e19c8f185a3676f95fb247ce7f4e83d637b8a54551419750a19eb` | `12b616448679e55a22dab02ac2c656aeff9fdfa02401b1d81f039365c448c281` | `43c3b94bc7934c8545cdc379730e8f166c7e6177b22dbf31f4bd4af72fb1025d` |
| `d1024_bw180` | 1111 | `4534d286b1cbe1493ec75b5be8ac5d2c24caa21974511eae56e595c9bab062f4` | `eef858931ead1e1868a55f9ce8c1c58952addcd7f446ee646d0dec4a01c0af65` | `75b6695f5597af9dcad425d698026c7399d7a6af92a118ecd397d6c54ef191bb` |
| `d1024_bw200` | 1112 | `f0a9e75ca9626291f8c7222f069be28ac215a31781b79dcfdb8ba8ce99c6f5ab` | `b6146037b4aa91530c795308b6f32054ae40be434914f8fac9a02a6f14d5cc76` | `c6846c77c45ffe2a9b8bf3a7a17b313a881d4c95bc367d4cfad74027fff6df6d` |

Require one-dimensional, equal-length integer arrays in `[0,1023]`;
256-symbol contiguous frames; natural tail rejection without padding;
`from_ttbin`, `materialized_from_ttbin`, strict unsampled nearest pairing;
q=1024; exact bin width; Gray mapping; `lsb0`; and `floor_div`.

Historical metadata uses the absent prefix `D:\Data\QKD_Loss`. Permit exactly
one case-insensitive prefix relocation to
`D:\Data\Raw Data\QKD_Loss`, require suffix equality, and reject a competing
resolving recorded source. Bind these provenance files:

| Relative file | SHA256 |
|---|---|
| `run_config.json` | `e3e290cc6dfb9354524ca54f3ed2c492e7a5062f690506422f0bd21ae04bb475` |
| `results/ttbin_parsing/ttbin_source.txt` | `32aa328ca0ea3f917eca54969d8570733db066609a1139c4f8158a99b456402e` |
| `results/ttbin_parsing/ttbin_config.json` | `b2a0025e9f93090300d53d285123c5d43c17ffe16af5f6ec31d8e252e0f1c24b` |
| `results/ttbin_parsing/ttbin_metrics.json` | `4c9ff5c523f26de1e0f795842b45e4eb55433443fff4cced3895d9ea4afa6bc7` |
| `results/inputs_snapshot.json` | `d24a61c0fba4715513c22cd5edcbf7445d60c4e5eead6a9de0fc702ea63b6375` |
| `results/resolved_config.json` | `3b320c67220eb8f8afda71d7e646b0d5664e437547460d6296023d1817f74dfe` |
| `results/run_config.source.txt` | `3323d20f7137b105b175d876a95f5ce3282e30a62838edd0ea37993cfe8ae9e6` |

The duplicate `TypeII_776.1nm_3s - 副本` tree is not a second acquisition and
must never add denominators.

## 3. Selection, isolation, and lifecycle

Build source-aware frame and payload identities from exact little-endian
Alice/Bob bytes. Reject duplicate payloads. Rank all complete frames by:

`SHA256("binary_ldpc_v4_10db_transfer_selection_v1|<stratum>|<frame_identity>")`

Select the first 128 per stratum and freeze their order before decoding.
Generate three fresh 16-byte CSPRNG roots and 128 deterministic 2623-bit
Toeplitz seeds per stratum. Prove root/seed isolation from v3, development,
synthetic, 16 dB, and every prior real plan.

Lifecycle:

1. prepare exactly once into a fresh additive directory;
2. main-thread plan/source-lock review;
3. execute exactly once;
4. read-only verify exactly once.

Retain all 384 denominators. Each stratum requires at least 126
`verified_success` and zero forbidden failures. A miss is immutable
`non_promoted_transfer`; it is never tuned or rerun.

The verifier reconstructs source selection, prerequisite packages, source
hash DAG, roots/seeds, outcomes, transcripts, public payloads, leakage,
accounting, and gates, and reports `decoder_reexecution=false`.

