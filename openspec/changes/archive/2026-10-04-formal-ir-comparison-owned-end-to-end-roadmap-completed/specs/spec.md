# Spec delta: Comparison-owned end-to-end roadmap

## Repository ownership

- The project SHALL implement new NB-LDPC algorithms, model-input preparation,
  real-data bridges, scans, result contracts, and research evidence in
  `HD-QKD_Polar_Comparison`.
- The project SHALL treat `HD-QKD_Polar_Release` as read-only reference during
  these milestones and SHALL NOT advance Polar-mainline work from Comparison.
- A Release-side adapter SHALL require a separate authorized change after a
  stable Comparison output contract and accepted real single-point evidence.
  It SHALL remain a thin consumer and SHALL NOT duplicate NB-LDPC or scanning.

## Milestone order

- Candidate acceptance and Model-F input SHALL precede P0.
- P0, G1, and G2 SHALL remain separately reviewed and authorized.
- Target-block and real single-point evidence SHALL precede a fixed-`d` `tau`
  scan; fixed-`d` confirmation SHALL precede `d x tau` generalization.
- Reconciled-net selection SHALL remain distinct from qualified secure-key-rate
  selection.

## Current lifecycle

This roadmap change SHALL NOT authorize or execute any decoder, CAL/VAL/raw
read, output creation, scan, real-data run, qualification, or promotion.

