# EXPLORE — accepted fixed-call kernel hotspot diagnosis

Main accepts independent H5 PASS for UUID `443938ee-da09-4795-a9b2-25bc95047283`, root `workspace/gf32_hotspots_443938ee/`. One frozen command, operator census_scope session31917/chunkc1eb83, exit0; no rerun/repair/resume or post-execution code changes. Classification **KERNEL_HOTSPOT_PROFILE_COMPLETE** is diagnostic only.

Single parent UUIDcbe151fe-25f7-4990-8895-858091467e2b / workspace/gf32_softprior_replica_cbe151fe, original classification unchanged. Fixed18 source-call convenience cases: each of six graphs' first syndrome-valid baseline, first failed baseline and selected valid rescue of first eligible failed pair. Selection uses saved syndrome flags/pointers, not truth. No new frames, labels, prior, decoder settings or candidate-selection policy.

| Round | Mode | Calls | Iterations | Sum of decoder-call outer wall (s) |
| --- | --- | ---: | ---: | ---: |
| 1 | unprofiled | 18 | 657 | 4.0216 |
| 2 | unprofiled | 18 | 657 | 4.0352 |
| 3 | cProfile around decoder only | 18 | 657 | 5.7778 |

Per-round iterations: baseline-failed540, baseline-valid52, selected-rescue65; maximum90 per call. Total54 calls/1971 iterations. All54 recorded vector/iteration/status/syndrome round-trip checks passed; failed baseline CHECK_UPDATED beliefs checked with atol1e-12/rtol0. There are12 unique exact calls,0 valid-wrong,6 baseline failures; the summary36 exact is12 repeated three times, not36 independent samples or an efficacy result. Exact requires both truth equality and independently computed own syndrome.

Independent reviewer recomputed source-case selection, pointer joins, source-vector syndrome/truth outcomes, iteration/status/report flags, CSV counters and resource/profile interpretation. Returned vectors and final beliefs are not duplicated in the artifacts; the CLI performed actual array comparisons and recorded their match results. Reviewer did not directly inspect the replay-returned arrays, and did not rerun BP. This is the evidence boundary.

| Profile function | Self time (s) | Cumulative time (s) |
| --- | ---: | ---: |
| _check_update_log_batch | 1.874 | 5.464 |
| fwht_batched | 1.644 | 2.508 |
| decode_row_layered_fftqspa | 0.228 | 5.777 |

FWHT is nested inside check-update; do not add cumulative times. cProfile attributes NumPy native work to Python callers and perturbs frequent small calls. The two ordinary rounds, first-use GF-table/cache effects and profile overhead remain separate; neither a speedup nor steady-state/pipeline throughput is measured. Hotspot concentration supports trying a local fused check-update/FWHT implementation before broad refactoring, parallel restarts or branch pruning. Any such prototype must have its own frozen packet, numerical gates and additive root.

Checkpoint wall13.9033s through first-pass artifacts, not full-process wall; high-water RSS104,083,456B (Linux ru_maxrss KiB converted to bytes). Source reads1; sampler/search/graph-build0; no resource events. First-pass output16,041B; execution-terminal five-file total independently measured16,164B before review/closeout log append, below5MiB. Final writes and later append are outside the checkpoint's recursive scope. New public disclosure0 (local replay only), tag0; verification NOT_IMPLEMENTED/undetected NOT_MEASURED. No FER/f_eff/SKR, fresh holdout, qualification/promotion/publication/security, real-data,n256/N2048, route or cross-batch comparison claim.

Focused11 explicit-fake tests passed in3.31s, only existing pytest.ini cache_dir warning. Compile/T0/dry and immediate branch/scoped-file/output-absence checks passed. Baseline-pointer pass-through/fallback, exact truth-AND-syndrome and CLI dry-run invocation fixes occurred before the one-shot execution. No commit/push/merge/add/archive. Main accepts the diagnostic, with project-memory triage and independent milestone documentation review.
