# G-M3D-ITER250-SYNTH — selected Stage-1 call-cost diagnostic

**Status: IMPLEMENTED AND FAKE-TESTED, NOT GRANTED FOR SCIENTIFIC EXECUTION.** Track `EXPLORE`. This new packet does not resume or rerun the stopped M3C real-data diagnostic. The M3C eval rows suggested this hypothesis; reuse of those real frames later would be development reuse, not independent qualification.

## Frozen question and inputs

Does `max_iter=250` preserve exact-match outcomes and reduce Stage-1 decoder-call wall on selected M3-b synthetic blocks that were previously exact or nonexact at `max_iter=300`? Use the two saved M3-a graph instances, M3-b's synthetic 2M source and read-only `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` / `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03_pb.npz`, n=1024 GF(32), cold m=200 Stage 1, b2f soft-marginal prior, default streak 3, and stream `o1_blk:{seed}` with `seed=2026096401+block_idx`. No Stage 2 is run. The sole scientific change is the iteration cap.

| arm | graph | exact baseline indices | nonexact baseline indices | fresh arm root | read-only comparator |
|---|---|---|---|---|---|
| M3D-R1 | `workspace/m3a_nested_200p8_20260926/arm1.json` | 0,1,2,3,4,5,6,7 | 127,158,186,192,193,204,210,217 | `workspace/m3d_iter250_synth_20260927/R1_17b6c2e9` | `workspace/m3b_nested_paired_20260926/P1S1-R1_73d2f40a/rows.json` |
| M3D-R2 | `workspace/m3a_nested_200p8_20260926/arm2.json` | 0,1,3,4,5,6,7,8 | 2,23,30,94,95,129,130,137 | `workspace/m3d_iter250_synth_20260927/R2_45ad8f31` | `workspace/m3b_nested_paired_20260926/P1S1-R2_89ae671c/rows.json` |

The selected mix deliberately balances known successes and failures. It is a targeted 32-call diagnostic, not a 240-frame sample. Run R1 first; run R2 only if R1 completes and individually passes the identity, accuracy, resource and runtime gates. No graph construction, seed search, channel refit, real input, warm start, alternate trigger or decoder schedule change.

## Measures and decision gate

Each arm retains 16 paired rows with block index, seed, baseline status/exact/undetected/iterations/wall, new status/exact/undetected/iterations/wall, actual `max_iter=250` and selection stratum. Retain arm wall and peak RSS. Compare per-row identity with the read-only M3-b artifacts. Baseline selected failure-stratum summed decoder-call wall is **516.273374667042 s for R1** and **573.172282627085 s for R2**; selected exact-stratum sums are 29.0487699548248 s and 24.642091246089 s. The baseline has eight exact and eight nonexact Stage-1 rows per arm.

An arm passes only if all 16 calls complete, each selected exact row stays exact, each selected nonexact row stays nonexact, all new undetected flags are zero, and its selected nonexact-stratum summed decoder-call wall is at most **90%** of the corresponding baseline sum (R1 ≤464.646037200338 s; R2 ≤515.855054364377 s). Report exact-stratum wall and all iterations descriptively, without a separate threshold. A call timeout, missing row, resource breach or identity drift fails the arm. Both arms must pass for a **selected synthetic call-cost signal**. Any failure retains evidence and stops. No pooling, significance language, FER, overall throughput, real-data advantage, leakage/f or SKR claim follows from PASS.

## Cost, files and STOP

One CPU with `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=NUMBA_NUM_THREADS=1`; ≤1200 s per arm, ≤2400 s sequential batch, ≤90 s per decoder call, peak RSS <2 GiB. Both fresh arm roots and family log must be absent before first execution; R2's root must still be absent at its Pre-EXECUTE check. New per-arm JSON/brief Markdown and **one append-only `EXPLORATION_LOG.md`** under the family root retain attempts, gates, evidence and one independent batch-end review. Stop on input/graph/seed drift, output collision, budget breach, evidence-label error or code/review FAIL. No overwrite or ad hoc retry/resume; at most one preregistered engineering repair plus rerun with unchanged science, indices, seeds, thresholds, roles and hypothesis, retaining the failed attempt. Protected `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/outputs_comparison/` and all M3-a/M3-b/M3C roots stay read-only.

## Authorization and return boundary

Implementation-only changes and fake-only tests under `openspec/changes/m3d-iter250-synth/` are allowed. Before any synthetic decoder execution, main records the exact command, branch/scoped diff, focused tests, fresh-root and input checks, cost/STOP gates, and an **explicit grant for this new batch**. Prior M3-b/M3C grants were consumed. One grant covers both frozen arms conditionally; no per-arm permission loop. One independent batch-end review precedes main acceptance. The implementation operator returns only after M3D-01/02 finish or on a concrete blocker.
