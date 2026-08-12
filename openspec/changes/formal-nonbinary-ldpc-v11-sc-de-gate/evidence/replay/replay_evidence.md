# V11-40.3 Strict-Replay Evidence — Byte Comparison

- **Schema**: `v11_replay_evidence_v1`
- **Change**: `formal-nonbinary-ldpc-v11-sc-de-gate` (task V11-40.3)
- **Compared at (UTC)**: 2026-08-11T21:49:55+00:00
- **Plan ref**: evidence/formal_plan.json (schema v11_formal_plan_v1, plan_version 1.0.0, frozen 2026-08-06)

## Roots

| Role | Root |
|---|---|
| Execute | `D:\Code\HD-QKD_Polar_Comparison\workspace\nbldpc_v11_execute_002d51de` |
| Replay  | `D:\Code\HD-QKD_Polar_Comparison\workspace\nbldpc_v11_replay_8e63bf62` |

## Method

V10-precedent direct byte comparison (no hashes). Level 1: threshold_search.json compared byte-for-byte for each of 60 runs. Level 2: run_measurement.json scientific fields compared by JSON value with explicit exclusion of non-deterministic timing/resource fields (wall_seconds, per_iteration_seconds, per_sample_per_iteration_seconds, peak_rss_bytes, cap_exceeded) and the per-root output_dir path. Level 3: formal_matrix_results.json scientific result fields (conservative, paired_gains, gate, rate_contract, seeds_ok, runs science fields keyed by run_id) compared, excluding bookkeeping (session wall, heartbeat/progress paths), executed_at, execution_root, runs[*].wall_seconds, runs[*].peak_rss_bytes.

## Verdict

- threshold_search.json byte-identical: **60/60**
- run_measurement.json science fields identical: **60/60**
- formal_matrix_results.json science fields match: **yes**
- **replay_ok: `True`**

## Excluded (non-deterministic / bookkeeping) fields

| File | Excluded fields |
|---|---|
| threshold_search.json | *(none — full byte comparison)* |
| run_measurement.json | `cap_exceeded`, `output_dir`, `peak_rss_bytes`, `per_iteration_seconds`, `per_sample_per_iteration_seconds`, `wall_seconds` |
| formal_matrix_results.json | `bookkeeping.heartbeat_file`, `bookkeeping.progress_file`, `bookkeeping.session_batch_wall_seconds`, `executed_at`, `execution_root`, `resource.batch_wall_seconds`, `resource.peak_rss_bytes`, `runs[*].peak_rss_bytes`, `runs[*].wall_seconds` |

Excluded fields differ between roots by design (replay wall time / RSS differ under CPU contention; per-root absolute paths and timestamps differ).

## Integrity checks

- Replay threshold_search.json all present and `status=valid`: **True** (60/60)
- progress.json done: execute 60/60, replay 60/60
- Run-id sets identical: **True** (60/60 dirs)
- matrix runs list order identical: **True**
- gate.state execute/replay: `failed_reference` / `failed_reference` — match: **True**

## Per-run results

| run_id | threshold byte match | measurement science match | measurement mismatches |
|---|---|---|---|
| S1_G1_seed1222026398_coupled | True | True | — |
| S1_G1_seed197472535_control | True | True | — |
| S1_G1_seed2005000629_control | True | True | — |
| S1_G1_seed2660679541_control | True | True | — |
| S1_G1_seed2959007440_control | True | True | — |
| S1_G1_seed3301261827_coupled | True | True | — |
| S1_G1_seed3441440341_control | True | True | — |
| S1_G1_seed4222513407_coupled | True | True | — |
| S1_G1_seed4272195966_coupled | True | True | — |
| S1_G1_seed762539858_coupled | True | True | — |
| S1_G2_seed1105888531_coupled | True | True | — |
| S1_G2_seed1451501760_coupled | True | True | — |
| S1_G2_seed1522090265_control | True | True | — |
| S1_G2_seed1582603594_control | True | True | — |
| S1_G2_seed302933967_control | True | True | — |
| S1_G2_seed3663636734_coupled | True | True | — |
| S1_G2_seed3774424946_control | True | True | — |
| S1_G2_seed4001332335_coupled | True | True | — |
| S1_G2_seed4138641662_coupled | True | True | — |
| S1_G2_seed949613946_control | True | True | — |
| S1_G3_seed1028646838_coupled | True | True | — |
| S1_G3_seed1299160519_coupled | True | True | — |
| S1_G3_seed1506741124_control | True | True | — |
| S1_G3_seed1976747491_coupled | True | True | — |
| S1_G3_seed2109324390_coupled | True | True | — |
| S1_G3_seed2307418581_control | True | True | — |
| S1_G3_seed2765619946_control | True | True | — |
| S1_G3_seed3992260457_coupled | True | True | — |
| S1_G3_seed4036769515_control | True | True | — |
| S1_G3_seed693545339_control | True | True | — |
| S3_G1_seed148926513_control | True | True | — |
| S3_G1_seed2586418385_control | True | True | — |
| S3_G1_seed3101754375_coupled | True | True | — |
| S3_G1_seed3294282856_coupled | True | True | — |
| S3_G1_seed3696755679_coupled | True | True | — |
| S3_G1_seed4266052623_control | True | True | — |
| S3_G1_seed600249577_control | True | True | — |
| S3_G1_seed732969838_coupled | True | True | — |
| S3_G1_seed75123851_coupled | True | True | — |
| S3_G1_seed90306507_control | True | True | — |
| S3_G2_seed1003283467_control | True | True | — |
| S3_G2_seed1371758077_control | True | True | — |
| S3_G2_seed1456786342_coupled | True | True | — |
| S3_G2_seed2265290548_coupled | True | True | — |
| S3_G2_seed2716543585_control | True | True | — |
| S3_G2_seed2819376759_control | True | True | — |
| S3_G2_seed329195505_coupled | True | True | — |
| S3_G2_seed3831670887_control | True | True | — |
| S3_G2_seed4161882935_coupled | True | True | — |
| S3_G2_seed795614139_coupled | True | True | — |
| S3_G3_seed1237583460_coupled | True | True | — |
| S3_G3_seed1449336257_coupled | True | True | — |
| S3_G3_seed1558752836_control | True | True | — |
| S3_G3_seed2588231339_control | True | True | — |
| S3_G3_seed2819034846_coupled | True | True | — |
| S3_G3_seed3198668028_coupled | True | True | — |
| S3_G3_seed335849802_coupled | True | True | — |
| S3_G3_seed575023286_control | True | True | — |
| S3_G3_seed660002917_control | True | True | — |
| S3_G3_seed894708125_control | True | True | — |

## Mismatch detail

None — all 60 threshold_search.json byte-identical and all scientific fields identical between execute and replay.

Machine-readable: `evidence/replay/replay_evidence.json`.
