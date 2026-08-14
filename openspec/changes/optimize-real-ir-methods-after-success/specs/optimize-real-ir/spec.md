# Spec Delta: Optimize Real IR Methods

## Requirements

### Requirement: Maintain real_ir_success=True
All optimized method configurations MUST maintain independent verification success. Any run that reduces leakage or runtime but fails verification MUST NOT be classified as successful.

### Requirement: Exact leakage accounting for Cascade-lite
`cascade_lite` transcript leakage calculations MUST count actual disclosed bits (parity checks, bisection disclosures, and verification CRC bits) exactly based on protocol execution, rather than generic approximations.

### Requirement: Step-down parity validation for Layered LDPC
`layered_ldpc_lite` runs MUST be evaluated across a descending schedule of `parity_fraction` values `[1.0, 0.9, 0.8, 0.67, 0.50]`. The system MUST preserve failed statuses when the decoder cannot converge or verify under a lower check budget.

### Requirement: Scalability frame size increase
The comparison pipeline MUST support scaling `frame_len_symbols` to `[256, 512, 1024]` symbols. Under these larger frame sizes, empirical efficiency $\beta_{eff\_empirical}$ MUST be derived dynamically from actual leakage and error inputs, verifying if it becomes positive ($>0$).
