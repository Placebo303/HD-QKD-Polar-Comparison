# Spec — v28_gf32_finite_code

Deterministic two-layer GF(32) parity-check finite-code engineering selected by the V27 gate.

## Requirement: deterministic GF(32) mother matrices
The implementer must construct two-layer GF(32) parity-check mother matrices from a frozen
config using `GF2mField.create(32)` and the three-shift-cyclic deterministic construction.
The implementer must not introduce new field arithmetic or new decoder science.

#### Scenario: matrix dimensions and full rank
- **Given** the frozen `v28_config.json` (block_len=1024, m1=6, m2 ∈ {194,200,202}).
- **When** the mother matrices are built.
- **Then** `H_mother_L1` is 6×1024, `H_mother_L2` is 202×1024, all entries ∈ GF(32), and
  `gf_rank(H_mother_L1)==6`, `gf_rank(H_mother_L2)==202`.

#### Scenario: source-specific public row prefix
- **Given** the three sources with m2 ∈ {194,200,202}.
- **When** the per-source L2 matrix is taken.
- **Then** it equals `H_mother_L2[:m2_source, :]` and the prefix is public + leak-accounted.

## Requirement: two-layer Bob-only sequential decode
The implementer must decode L1 from its syndrome using the L1 posterior, then L2 conditioned
on the decoded L1, with no Alice oracle and no top-K truth selection.

#### Scenario: noiseless recovery
- **Given** a known symbol block `x`.
- **When** syndromes `s1=H_L1·x1`, `s2=H_L2·x2` are decoded sequentially.
- **Then** both layers recover `x` exactly for all three sources.

#### Scenario: failure is surfaced, not replaced
- **Given** a decode that cannot recover.
- **When** the decoder returns.
- **Then** the failure is reported; no substitute frame is injected.

## Requirement: 64-bit tag and leakage accounting
The implementer must derive a 64-bit public verification tag over the decoded block and report
total leakage `m_total·5 + 64` bits.

#### Scenario: leakage under 1.3
- **Given** the three sources' m_total.
- **When** leakage is computed.
- **Then** f = leakage / (n·H_source) < 1.3 for all three sources.

## Requirement: terminal state
The implementer must emit only `engineering_ready_for_retrospective_gate`.

#### Scenario: engineering ready
- **Given** all structural + decode checks pass and the read-only verifier returns ok.
- **When** V28 completes.
- **Then** terminal state is `engineering_ready_for_retrospective_gate`.
