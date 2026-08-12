# Proposal: Binary LDPC v5 Incremental Redundancy

## Why

The unchanged v4 method completed two independent real transfer packages but
missed the frozen gate in one layer each:

- 16 dB: 125/128, 128/128, 128/128;
- 10 dB: 125/128, 127/128, 128/128.

All seven failures were retained `verify_failed` after valid syndrome
decoding and final Toeplitz mismatch; forbidden failures were zero. Moving to
progressively easier losses until one passes would be selective reporting.
The next method version therefore improves decoding robustness under a
pre-registered development/confirmation split.

## Scope

- Freeze disjoint unused 10 dB `.ttbin` frames before development:
  512 development and 128 sealed real confirmation frames per stratum.
- Evaluate three pre-registered policies: v4 control, stronger local OSD, and
  one two-round incremental-redundancy fallback.
- Select only on sacrificed development data under frozen success, leakage,
  runtime, and failure rules.
- Require a fresh independent synthetic confirmation before any real
  confirmation.
- Execute the sealed real confirmation exactly once if synthetic promotes.

## Claim boundary

A promoted package proves only binary LDPC v5 on the registered 10 dB
Type-II acquisition, q=1024, Gray mapping, 256-symbol frames, and
bw120/bw180/bw200. It does not repair or promote v4, 16 dB, 20 dB, other
captures, nonbinary LDPC, Polar, Cascade, or a final comparison.

