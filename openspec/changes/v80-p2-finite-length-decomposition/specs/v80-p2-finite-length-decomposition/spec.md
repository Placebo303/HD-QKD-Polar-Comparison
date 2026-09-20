## ADDED Requirements

### Requirement: Reproducible joint-rate DE threshold
Arm (i) SHALL report one MC-DE threshold efficiency f_DE at rate 0.796875 (m = 416/n = 2048) on seeds {2026094951, 2026094952} using the unchanged V26 kernel with a joint (u1,u2) sampler; the point is reproducible only if the seeds agree within 0.05.

#### Scenario: Seeds disagree
- **WHEN** |f_DE(seed1) − f_DE(seed2)| > 0.05
- **THEN** the point is NON-REPRODUCIBLE and no decomposition is computed.

### Requirement: Non-overlapping curve partition with P1 ownership
Arm (ii) SHALL measure only m ∈ {196, 204, 192} (@instance 2026092001); m = 200 SHALL be refused in this batch (P1-owned, consumed by reference); m ∈ {202, 208} SHALL be taken by citation without re-run.

#### Scenario: m = 200 measurement proposed in P2
- **WHEN** an m = 200 decode is proposed under this change
- **THEN** it is refused as owned by P1 (double-count prevention).

### Requirement: Diagnostic-only assembly
The decomposition SHALL be computed as finite-length = m_min − m_DE and structured = m_DE − 170.5 with m_DE ≡ f_DE × 852.544/5, reported as diagnostic and never extrapolated to other channels.

#### Scenario: Extrapolation proposed
- **WHEN** applying the split to another channel, noise, or alphabet is proposed
- **THEN** it is refused as beyond the claim ceiling.

### Requirement: Gated execution with explicit grant
No P2 execution SHALL occur without Pre-EXECUTE Q0–Q6 plus a fresh explicit user grant per arm; this change alone authorizes nothing.

#### Scenario: Execution requested citing freeze alone
- **WHEN** execution is requested citing this frozen change without a fresh grant
- **THEN** it is refused pending the grant and Pre-EXECUTE.
