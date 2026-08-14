# Polar Reconciled Result V3

Date: 2026-08-12 (Asia/Shanghai)

## Result boundary

The V3 main result is a measured, actual-replay reconciliation result:

```text
PIE_reconciled_net = max(0, (total_kept_info_bits - total_leak_ec_bits) / n_pairs_actual)
SKR_reconciled_net_bps = PIE_reconciled_net * coincidence_rate_hz
```

Despite the historical `SKR` column name, this is a public-EC-only net shared-bit rate. It is not a secret-key rate. It does not subtract Eve information, instantiate a phase-error or parameter-estimation bound, perform privacy amplification, or claim composable HD-QKD security.

The previous calibrated `PIE_secure_actual_ir` formula mixed an accepted-frame fraction with bits-per-pair terms and also applied acceptance in the rate. It is retained only for compatibility and is blocked from scientific reporting.

## Evidence

- Final root: `results/paper_grade_v3/reconciled_stage2_20260812_final_v3/`
- Master table: `cross_loss_reconciled_master_table.csv`
- Rows: 484 total, 484 reportable reconciliation rows.
- Rate provenance: 484 rows use `authoritative_candidate_grid_table_preserved_measured_rate`.
- Correctness: 206,402 invoked verification blocks, 2,530 detected verification failures, maximum pointwise union bound `1.0863705768304752e-16`, below `eps_cor=1e-10`.
- All four loss-specific formal validators passed 121/121 point rows and now also check the main PIE/SKR identities, claim labels, rate provenance, and blocked legacy status.

## Main maxima

| Loss | Positive rows | Max PIE | Max reconciled rate (bit/s) | Best point |
|---:|---:|---:|---:|---:|
| 6 dB | 83 | 6.848487 | 1,570,570.66 | d=4096, 200 ps |
| 10 dB | 82 | 6.792930 | 644,880.14 | d=4096, 200 ps |
| 16 dB | 84 | 7.060273 | 1,335,766.95 | d=2048, 200 ps |
| 20 dB | 88 | 7.297932 | 73,388.02 | d=4096, 200 ps |

These maxima are reconciliation-throughput results and must not be labelled secure PIE or secret-key rate.

## Rebuild and validation

```powershell
python pipelines\current\routeA_rebuild_stage2_from_q3.py `
  --source-root results\paper_grade_v2\four_loss_parts_tag64 `
  --output-root results\paper_grade_v3\reconciled_stage2_YYYYMMDD
```

The rebuild reads the frozen Q3 Stage 1 replay, copies fresh Stage 0 algorithm outputs, restores measured rate and occupancy provenance from the immutable authoritative candidate sidecars, and writes a new Stage 2 tree. It does not rerun the decoder and does not overwrite historical results.

## Remaining boundary

A paper may report the reconciliation algorithm, leakage, FER/correctness verification, and the reconciled net shared-bit rate. A secure/composable QKD key-rate result remains blocked until protocol-specific Eve/phase-error and parameter-estimation observables plus privacy-amplification accounting are supplied.
