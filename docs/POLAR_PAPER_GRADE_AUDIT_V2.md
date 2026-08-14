# Polar Paper-Grade Audit V2

Date: 2026-08-11 (Asia/Shanghai)

## Conclusion boundary

V2 qualifies binary Polar reconciliation and its correctness-verification accounting. The downstream visibility and finite-size table remains a calibrated, model-dependent, non-composable shadow because the repository does not contain the protocol-specific phase-error and parameter-estimation observables needed for a composable HD-QKD proof.

Historical results under `results/authoritative/` are unchanged. All V2 runtime evidence is written under `results/paper_grade_v2/`.

## Correctness defects found in V1

1. Actual SCL replay used CRC-aided final-path selection even though experimental information bits were not CRC-precoded. In a read-only audit, all 202 sampled real information vectors were CRC-invalid; the historical SCL lane therefore did not implement the declared arbitrary-key reconciliation problem.
2. Verification matrices were derived deterministically from public point/layer/block identifiers. That fixed public map cannot support the claimed random-universal-hash collision bound; a nonzero null-space collision was constructed during the audit.
3. SC Monte Carlo did not receive the declared seed, so repeated runs could change FER decisions.
4. `best_hard_PIE` selected one global decoder total while exported layer metadata selected per-layer maxima. The two disagreed on 147 of 484 historical points, by as much as 0.057617 bit/pair.
5. Effective-pair aggregation multiplied by block success after `total_kept_info_bits` had already included block success.
6. A source update could silently reuse an older decoder DLL because the wrapper only checked whether the library existed.
7. Archived sidecars had been moved under `results/authoritative/`, while frozen CSV metadata retained the earlier absolute paths.

## V2 corrections

- Ordinary frozen-aware SCL (list size 4) now selects the minimum path metric. Legacy CA-SCL remains an explicit comparison API only.
- Verification uses one recorded uniformly random Toeplitz seed per predeclared fixed batch. The paper-grade API requires the seed explicitly; identifier-derived helpers are legacy-labelled and disconnected from the main API.
- Monte Carlo seeds are deterministically keyed by the declared base seed and scientific candidate `(dimension, bin width, layer, k, decoder)`.
- FER acceptance uses a reported one-sided 95% Wilson upper bound and requires that upper bound to be below 0.05.
- `best_hard_PIE` is the sum of the same per-layer candidates exported in `polar_layer_metrics.csv`.
- Effective pairs apply block success conditionally and do not apply it twice when layer fraction came from actual kept bits.
- The decoder wrapper rebuilds when `main.cpp` is newer than the runtime library.
- Only the concrete historical `results/` to `results/authoritative/` move is resolved as a fallback.

## Literature definition check

- Tal and Vardy define ordinary SCL output as the most likely path in the final list; CRC is an optional genie/precoding aid, not a valid selector for arbitrary unprecoded information bits: <https://doi.org/10.1109/TIT.2015.2410251>.
- QKD reconciliation literature treats verification as a separate epsilon-universal-hash step after error correction: <https://arxiv.org/abs/1705.06664>.
- Finite-key QKD protocols use a random two-universal hash for error verification and account for approximately `ceil(log2(1/epsilon_cor))` revealed bits: <https://doi.org/10.1103/PhysRevA.92.032305>.
- Finite-key security requires protocol observables and a proof-specific entropy bound, not only a reconciliation FER and an assumed visibility: <https://arxiv.org/abs/1103.4130>.
- The retained PW ordering is a low-complexity, channel-independent approximation and is therefore frozen as an engineering construction choice rather than promoted to an optimized proof-specific construction: <https://arxiv.org/abs/1805.02813>.

## Q0-Q2 evidence

- Focused and smoke tests: 14 passed. Pytest could not write its optional cache in the repository, which did not affect test execution.
- A first metric test collection failed because a same-directory report module was not on the test import path; the loader was corrected without changing the algorithm.
- A first metric canary produced `missing_sidecar` because of frozen old paths. It is preserved at `results/paper_grade_v2/canary_20dB/metrics_missing_sidecar_attempt/`.
- A second metric attempt failed before output because the stale `ca_scl.dll` lacked the new ordinary-SCL export. The runtime-library freshness rule was then corrected.
- With seed `20260228`, frames `100`, and point `(loss=20 dB, d=4, bw=20 ps)`, two independent metric executions returned identical `sc_hard_PIE`, `cpp_scl_hard_PIE`, and `best_hard_PIE`.
- The corrected selected layer is ordinary SCL with `k=634`, rate `0.15478515625`, CRC bits `0`, FER `1/100`, and one-sided 95% upper bound `0.04358177353405607`. The historical CRC-aided selection was `k=739` with 16 CRC bits.
- Fresh actual replay audited 6 blocks: 6 decoded matches, 0 decoder failures, 6 verification passes, 0 verification failures, and 0 empirical undetected errors.
- The 32-bit canary bounds were `1.3969838619232178e-09` (6 blocks), `3.4924596548080444e-09` (15 blocks), and `1.257285475730896e-08` (54 blocks). All exceed the declared `eps_cor=1e-10`; 32 bits therefore failed the analytical correctness-budget precheck even though decoder and transcript tests passed.
- The tag length was amended to 64 bits before any full-grid replay. At 205,425 invoked blocks, the conservative union bound would be approximately `1.11e-14`, below `1e-10`.
- The tag-32 full-grid metric jobs were stopped before Stage 1 and preserved at `results/paper_grade_v2/four_loss_parts_tag32_budget_failed/`; they are not result evidence.
- Tag-64 Q2 passed at all four representative points `(d=4, bw=20 ps)`: 20 dB used ordinary SCL `k=634`; 16 dB used SC `k=616`; 10 and 6 dB used SC `k=562`. The selected-code FER estimates were respectively `0.01`, `0`, `0.01`, and `0.01`; every one-sided 95% Wilson upper bound was below `0.05`.
- The four tag-64 replays audited 6, 15, 54, and 54 blocks. Every block decoded correctly and passed verification; the union bounds were `3.2526065174565133e-19`, `8.131516293641283e-19`, and `2.927345865710862e-18` for the latter two losses. All four Stage-C validators passed with `epsilon_EC_bound <= 1e-10`.

## Full-run command

The full Q3 runner recomputes layer metrics before replay and writes to a new root:

```powershell
python pipelines/current/routeA_run_formal_cross_loss.py --losses 20,16,10,6 --output-dir results/paper_grade_v2/four_loss_full --shards 16 --workers 2 --metric-jobs 4 --frames 100 --seed 20260228 --verification-tag-bits 64
```

The tag-64 Q3 jobs were restarted under `results/paper_grade_v2/four_loss_parts_tag64/`. They must remain isolated until every loss-specific validator finishes with no errors and confirms `epsilon_EC_bound <= 1e-10`.
