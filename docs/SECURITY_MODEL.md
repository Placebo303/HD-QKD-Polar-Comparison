# Security Model: Finite-Key Security Accounting

## Overview

This document describes the finite-key security accounting methodology used in the HD-QKD Polar pipeline. The security model is based on the layered secure PIE (Photon Information Efficiency) framework.

## Key Concepts

### Photon Information Efficiency (PIE)

PIE measures the amount of secure key information extracted per detected photon coincidence:

$$\text{PIE} = \frac{\text{Secure Key Bits}}{\text{Total Coincidences}}$$

### Secure Key Rate (SKR)

SKR is the rate of secure key generation:

$$\text{SKR} = \frac{\text{Secure Key Bits}}{\text{Acquisition Time (seconds)}}$$

### Layered Secure PIE

The total secure PIE is composed of multiple layers:

$$\text{PIE}_{\text{total}} = \text{PIE}_{\text{time-bin}} + \text{PIE}_{\text{polarization}}$$

where:
- **Time-bin layer**: High-dimensional arrival-time encoding
- **Polarization layer**: Additional binary key register (BBM92-type)

## Security Framework

### Finite-Key Regime

In practical QKD systems, the key length is finite. The finite-key security framework accounts for:

1. **Statistical fluctuations**: Due to finite sample size
2. **Privacy amplification**: Reducing Eve's information
3. **Error correction**: Information leakage during reconciliation

### Security Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| $\epsilon_{\text{sec}}$ | Security parameter | $10^{-10}$ |
| $\epsilon_{\text{corr}}$ | Correctness parameter | $10^{-10}$ |
| $\epsilon_{\text{EC}}$ | Error correction bound | $10^{-10}$ |

### Zhong-like Security Aggregation

The pipeline implements a Zhong-like security aggregation:

1. **Frame synchronization**: Align time-bin frames
2. **Polar encoding**: Encode key bits using Polar codes
3. **Information reconciliation**: Correct errors between Alice and Bob
4. **Privacy amplification**: Remove Eve's information

## PIE Calculation

### Time-bin PIE

For time-bin encoding with $d$ dimensions:

$$\text{PIE}_{\text{time-bin}} = \log_2(d) - H_{\text{leakage}} - \Delta_{\text{finite-key}}$$

where:
- $\log_2(d)$: Raw information per coincidence
- $H_{\text{leakage}}$: Information leakage during error correction
- $\Delta_{\text{finite-key}}$: Finite-key correction term

### Polarization PIE

For polarization encoding (binary):

$$\text{PIE}_{\text{polarization}} = 1 - H(e) - \Delta_{\text{finite-key}}$$

where:
- $H(e)$: Binary entropy of error rate $e$
- $\Delta_{\text{finite-key}}$: Finite-key correction term

## Security Accounting Modes

### Primary Reporting Mode

The primary reporting mode is `actual_ir_finite_key`:

```
PRIMARY_REPORTING_MODE = actual_ir_finite_key
default main result columns: PIE_main, SKR_main_bps
default main result source: PIE_secure_actual_ir, SKR_secure_actual_ir_bps
```

### Diagnostic Mode

Diagnostic performance proxies:
- `PIE_practical`: Practical PIE without finite-key corrections
- `SKR_measured_bps`: Measured SKR without security guarantees

## Scope Note (2026-09-21): Frozen Polar Baseline vs Active V80 NB-LDPC / IR Work

> Additive scope note. Existing content above (including the
> time-bin/polarization layers and the "polarization layer (BBM92-type)"
> text) is frozen-Polar-pipeline legacy and is PRESERVED unchanged; this
> section only delimits its scope relative to the active IR line.

- The polarization / BBM92-type layer described above belongs to the
  **frozen Polar baseline pipeline** and is NOT in scope for the active
  V80 NB-LDPC / IR work.
- The active IR work operates on the **high-dimensional time-of-arrival
  (ToA) layer only**: CW pumped SPDC, **time-energy entanglement**, ToA
  time-bin encoding with d up to 1024 (10-bit alphabet), working alphabet
  GF(32)^2 / superframe n=1024.
- **It is not BBM92.** The IR stage consumes only H(X|Y) and the empirical
  channel P(y|x); it is independent of the downstream security protocol and
  of whether a polarization register is used.
- Consequence: PM-vs-EB resolution is **not blocking** for IR work. The
  upstream acquisition configuration for source
  `type2_2M_20260121_183657` remains unavailable; it is needed only for the
  security/protocol write-up, where the protocol assumption must be stated
  explicitly.
- Composable finite-size security is out of scope for this IR line
  (companion-paper scope). Only bridge retained: Kanitschar & Huber —
  `leak_IR = leak_EC + log2(2/eps_EV)`, so our 64-bit verification tag
  corresponds to `eps_EV ≈ 2^-63`. See
  `docs/research_cycles/V80-NBLDPC-JAN21/KANITSCHAR_RELEVANCE_ADJUDICATION_20260921.md`.
- IR-layer contribution to security remains downgraded: IR does not alter
  quantum-side security, it only consumes H(X|Y).

## References

1. Zhong, T., et al. (2015). Photon-efficient quantum key distribution using time-energy entanglement with high-dimensional encoding. *New Journal of Physics*, 17(2), 022002.

2. Niu, M. Y., et al. (2018). Quantum key distribution with high-dimensional encoding. *Physical Review A*, 98(3), 032314.

3. Xu, F., et al. (2020). Secure quantum key distribution with realistic devices. *Reviews of Modern Physics*, 92(2), 025002.
