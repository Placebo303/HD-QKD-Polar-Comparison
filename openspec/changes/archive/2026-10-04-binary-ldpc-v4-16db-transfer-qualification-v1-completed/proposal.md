# Proposal: Binary LDPC v4 16 dB Transfer Qualification v1

## Why

The corrected binary LDPC v4 package is synthetic-promoted, while its original
20 dB real qualification remains capacity-blocked at 85 eligible frames per
stratum. A read-only audit of all `QKD_Loss` data found no second independent
20 dB acquisition.

The existing Type-II 16 dB acquisition is the highest-loss available domain
that has a q=1024, bw120/bw180/bw200 sidecar triplet with at least 128 complete
256-symbol frames per stratum:

| Stratum | Symbols | Complete frames |
|---|---:|---:|
| bw120 | 74,176 | 289 |
| bw180 | 74,388 | 290 |
| bw200 | 74,466 | 290 |

Type-II 25/30 dB acquisitions have no matching sidecar triplet. Choosing
16 dB is therefore a pre-registered capacity-and-loss rule, not a choice based
on LDPC outcomes.

## What Changes

- Add a separate 16 dB transfer-qualification source lock and runner/verifier.
- Bind the already frozen 20 dB-designed, synthetic-promoted binary LDPC v4
  matrices, channel, selection, decoder, caps, accounting, and 126/128 gate.
- Add an explicit relocation record for the historical
  `D:\Data\QKD_Loss` to current `D:\Data\Raw Data\QKD_Loss` path move without
  modifying any raw file, sidecar, or metadata.
- Select 128 frames independently in each of bw120/bw180/bw200 by frozen
  SHA256 rank, execute once, and verify once.

## Claim Boundary

Passing establishes only a 16 dB cross-domain transfer qualification for the
already frozen binary LDPC v4 method. It does not promote the blocked 20 dB
route, prove other losses, or authorize a Cascade/LDPC/Polar winner claim.

No 16 dB frame outcome, BER, or decoder result may be inspected before the
source lock and plan are frozen. Existing aggregate Polar/physics reports are
provenance context only and must not alter the LDPC method or gate.

