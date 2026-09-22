# Proposal: Comparison-owned end-to-end NB-LDPC roadmap

## Why

The accepted long-term route needs an explicit repository boundary. The
algorithm, real-input bridge, scans, reporting, and research evidence belong
in `HD-QKD_Polar_Comparison`. The sibling Polar Release checkout is a frozen
reference implementation and must not become the development location for the
NB-LDPC research line.

## Change

- Publish a deliverable-organized roadmap from the current V72P2D5 gate to a
  fixed-`d` `tau` scan, then `d` x `tau` generalization and qualified secure
  point selection.
- Make Comparison the owner of all new implementation and evidence.
- Limit Release use to read-only study and, only after a stable Comparison
  output contract exists, a separately authorized thin consumer adapter.
- Preserve the current phase order and authorization boundaries.

## Non-goals

- No decoder execution, CAL/VAL/raw read, result creation, or promotion.
- No changes in `../HD-QKD_Polar_Release`.
- No duplicate NB-LDPC implementation in Release.
- No implementation authorization for P0, G1, G2, real data, or scans.

