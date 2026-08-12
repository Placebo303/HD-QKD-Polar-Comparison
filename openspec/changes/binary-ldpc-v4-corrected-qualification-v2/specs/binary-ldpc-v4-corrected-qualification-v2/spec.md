# Binary LDPC v4 Corrected Qualification v2

## ADDED Requirements

### Requirement: Corrected development prerequisite

Synthetic qualification SHALL accept only a strictly verified, completed,
ready `binary_ldpc_v4_development_v2` package and SHALL bind its exact
artifacts and scoped sources.

#### Scenario: Failed-v1 substitution

- **WHEN** the failed v1 development package is supplied
- **THEN** prepare fails before creating an output directory.

#### Scenario: Corrected-v2 prerequisite

- **WHEN** the exact corrected package verifies ready
- **THEN** prepare freezes its hashes and unchanged scientific bindings.

### Requirement: Independent synthetic qualification

The v2 synthetic package SHALL contain 128 nominal and 128 stress
denominators, use fresh isolated roots/seeds, and promote only with at least
126 verified successes in each stratum and zero forbidden failures.

### Requirement: Real capacity before lock

Real prepare SHALL fail before output creation unless at least 128 complete,
non-reserved, non-calibration, unique frames exist in each registered real
stratum.

#### Scenario: Copied or reprocessed acquisition

- **WHEN** an added source has the same main/chunk `.ttbin` SHA256 pair as the
  base source or another addition
- **THEN** source-extension construction fails and supplies zero new capacity.

#### Scenario: Traceable source extension

- **WHEN** genuinely distinct same-domain `.ttbin` files and exact bw120,
  bw180, and bw200 sidecars are supplied
- **THEN** a no-overwrite self-hashed extension manifest binds all raw,
  sidecar, metadata, processing, framing, and acquisition identities.

#### Scenario: Duplicate frame payload

- **WHEN** the same Alice/Bob 256-symbol payload occurs more than once across
  the base and added candidate pool
- **THEN** the duplicated candidates are rejected rather than counted twice.

#### Scenario: Insufficient validated extension

- **WHEN** any stratum remains below 128 candidates after validation,
  duplicate rejection, calibration exclusion, and v3-reserved exclusion
- **THEN** real prepare fails before creating its output directory.

### Requirement: Conditional real qualification

After strict synthetic promotion and sufficient locked data, real
qualification SHALL execute exactly 128 frames in each of bw120, bw180, and
bw200 and promote only when all three strata achieve at least 126 verified
successes with zero forbidden failures.

The real lock and read-only verifier SHALL bind and reconstruct the exact
source-extension manifest and SHALL report no decoder reexecution.
