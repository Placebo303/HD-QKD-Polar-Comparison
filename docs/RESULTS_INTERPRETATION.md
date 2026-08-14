# Results Interpretation Guide

## Overview

This guide explains how to interpret the results from the HD-QKD Polar pipeline, including PIE, SKR, and other metrics.

## Key Metrics

### Photon Information Efficiency (PIE)

PIE measures the amount of secure key information per detected photon coincidence.

**Interpretation**:
| PIE (bits/coincidence) | Quality | Notes |
|------------------------|---------|-------|
| < 1.0 | Low | Limited information capacity |
| 1.0 - 3.0 | Medium | Typical for binary encoding |
| 3.0 - 6.0 | High | Good for high-dimensional encoding |
| > 6.0 | Excellent | Near theoretical limit |

**Example**: A PIE of 7.53 bits/coincidence means each detected photon pair carries ~7.5 bits of secure key information.

### Secure Key Rate (SKR)

SKR is the rate of secure key generation in bits per second.

**Interpretation**:
| SKR (bits/s) | Quality | Notes |
|--------------|---------|-------|
| < 100 | Low | Limited practical use |
| 100 - 1000 | Medium | Suitable for some applications |
| 1000 - 10000 | High | Good for practical QKD |
| > 10000 | Excellent | High-speed QKD |

### Error Rate (QBER)

Quantum Bit Error Rate measures the fraction of incorrect bits.

**Interpretation**:
| QBER | Quality | Notes |
|------|---------|-------|
| < 1% | Excellent | Very low noise |
| 1% - 5% | Good | Typical for practical systems |
| 5% - 11% | Marginal | Security may be compromised |
| > 11% | Poor | No secure key possible |

## Understanding Output Files

### Main Results File

The main results are in `results/authoritative/`:

```
PIE_main: 7.53
SKR_main_bps: 3600
QBER: 0.02
```

### Diagnostic Results

Diagnostic results (not for security claims):

```
PIE_practical: 8.2
SKR_measured_bps: 4200
```

## Comparison with Theoretical Limits

### Time-bin Encoding

For $d$-dimensional time-bin encoding:

$$\text{PIE}_{\text{max}} = \log_2(d)$$

Example: For $d = 256$, $\text{PIE}_{\text{max}} = 8$ bits/coincidence.

### Practical Limits

Practical PIE is reduced by:
1. **Noise**: Background counts, detector dark counts
2. **Losses**: Channel loss, detector efficiency
3. **Finite-key effects**: Statistical fluctuations
4. **Error correction overhead**: Information leakage

## Reading Results Tables

### Example Output

```
=== Security Results ===
PIE_secure_actual_ir: 6.97 bits/coincidence
SKR_secure_actual_ir_bps: 3580 bits/s
QBER_actual_ir: 0.018
epsilon_EC_bound: 1e-10
finite_key_correction: 0.12 bits
```

### Interpretation

- **PIE_secure_actual_ir**: Legacy calibrated shadow — BLOCKED for scientific reporting (`scientifically_blocked_dimensional_inconsistency`, `diagnostic_only`; see `docs/decision-log.md` 2026-08-14). It is not a secure PIE.
- **SKR_secure_actual_ir_bps**: Legacy calibrated shadow — BLOCKED, diagnostic only. It is not a secure key rate. The current main metric is `PIE_main` / `SKR_main_bps` = `PIE_reconciled_net` / `SKR_reconciled_net_bps` (public-EC-only net shared bits, `claim_boundary=public_ec_only_not_secure`).
- **QBER_actual_ir**: Actual quantum bit error rate
- **epsilon_EC_bound**: Error correction security parameter
- **finite_key_correction**: Reduction due to finite-key effects

## Troubleshooting

### No Secure Key

If secure key is zero:
1. Check QBER (should be < 11%)
2. Check finite-key correction (may be too large)
3. Check error correction leakage

### Low PIE

If PIE is lower than expected:
1. Increase dimensions (`--dims`)
2. Reduce bin width (`--bws`)
3. Increase acquisition time (`--acq-time`)
4. Check noise levels

### Low SKR

If SKR is lower than expected:
1. Increase acquisition time
2. Reduce error correction overhead
3. Check system losses

## References

1. Zhong, T., et al. (2015). Photon-efficient quantum key distribution using time-energy entanglement with high-dimensional encoding. *New Journal of Physics*, 17(2), 022002.

2. Xu, F., et al. (2020). Secure quantum key distribution with realistic devices. *Reviews of Modern Physics*, 92(2), 025002.
