# Proposal: Binary LDPC v4 Corrected Qualification v2

## Why

The immutable corrected development package
`20260727_v2_binary_ldpc_v4_development` strictly verified and passed its
frozen screen at 510/512 nominal and 511/512 stress. Existing conditional
synthetic/real tooling still requires the failed v1 development package and
therefore correctly rejects the corrected prerequisite.

No production v4 synthetic or real package exists, so the shortest auditable
route is to version the uninstantiated conditional tooling in place rather
than duplicate its full runner/verifier implementation.

## What Changes

- Bind synthetic qualification to the corrected v2 development runner,
  verifier, schemas, source hashes, and exact immutable package.
- Version synthetic and real package identities to v2.
- Preserve the existing fresh-root generator, 128 frames per stratum,
  126/128 promotion floors, failure accounting, transcript reconstruction, and
  no-overwrite lifecycle.
- Preserve real frame exclusion of all 96 v3-reserved identities.
- Add an explicit real-data capacity gate before real prepare.
- Add a no-overwrite, read-only source-extension manifest that combines the
  frozen base capture with one or more genuinely distinct 20 dB `.ttbin`
  acquisitions without changing calibration.

## Current Data Constraint

The bound sidecars contain 117 complete frames in each of bw120, bw180, and
bw200. Excluding the 32 v3-reserved frames per stratum leaves 85 eligible
frames, 43 fewer than the frozen 128. No real plan may be created until each
stratum has at least 128 eligible complete frames.

## Evidence Boundary

Synthetic execution occurs once with fresh roots. Failure is immutable and
cannot be tuned or rerun. Real lock/prepare is permitted only after strict
synthetic promotion and sufficient new source data. Passing real qualification
would apply only to the exact locked 20 dB, q=1024, Gray, 256-symbol,
bin-width, matrix, decoder, and source domain.

The similarly named directory under `TypeII_776.1nm_3s - 副本` is not new
capacity: both its main and `.1.ttbin` SHA256 values equal the registered
capture. Reprocessing or copying one acquisition SHALL NOT create additional
denominators.
