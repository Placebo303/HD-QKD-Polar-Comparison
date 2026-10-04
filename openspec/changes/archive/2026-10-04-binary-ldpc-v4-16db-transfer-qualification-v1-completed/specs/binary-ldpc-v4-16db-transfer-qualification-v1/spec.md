# Binary LDPC v4 16 dB Transfer Qualification v1

## ADDED Requirements

### Requirement: Highest-loss capacity-qualified transfer domain

The lane SHALL use the Type-II 16 dB acquisition because it is the
highest-loss existing domain with an exact q=1024 bw120/bw180/bw200 sidecar
triplet and at least 128 complete frames per stratum.

#### Scenario: Claim interpretation

- **WHEN** the transfer package promotes
- **THEN** it establishes only 16 dB transfer qualification and leaves 20 dB
  real qualification blocked.

### Requirement: Relocated source provenance

The lock SHALL reconstruct exactly one historical-to-current root
substitution, bind all raw/provenance/sidecar files, and reject ambiguity or
drift without editing source data.

#### Scenario: Copied tree

- **WHEN** a byte-identical duplicate tree is presented as a second
  acquisition
- **THEN** it supplies no additional frame identity or denominator.

#### Scenario: Relocation mismatch

- **WHEN** any embedded suffix, provenance snapshot, raw hash, or sidecar hash
  cannot be reconstructed through the single frozen substitution
- **THEN** prepare fails before creating its output directory.

### Requirement: Frozen cross-domain method

The transfer lane SHALL use the exact 20 dB-designed synthetic-promoted v4
method without 16 dB calibration, tuning, matrix/rate selection, or outcome
inspection before plan freeze.

### Requirement: Transfer qualification

The package SHALL contain exactly 128 denominators in each of bw120, bw180,
and bw200, and SHALL promote only if every stratum has at least 126 verified
successes and zero forbidden failures.

The read-only verifier SHALL reconstruct the full source/artifact/transcript/
gate DAG without decoder reexecution and SHALL explicitly report source
relocation.

