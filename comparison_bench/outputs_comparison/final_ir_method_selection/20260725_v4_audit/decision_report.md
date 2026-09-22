# Phase 4 audit decision

Decision: **no_decision** (exact two-sided paired p=1; alpha=0.05).

Cascade has 60/60 and Layered LDPC 59/60 independently verified successes, but the single discordant pair is not significant under the pre-registered exact McNemar/binomial test.

Leakage is preserved as method-specific disclosure accounting and is not cross-method ranked.

Route A documented-field compatibility gate: **fail**; no numerical Route A rerun was performed.

## Supported domain

{
  "data_mode": "real_data",
  "dataset_raw_ser_stratum": {
    "lower_inclusive": 0.2,
    "upper_exclusive": 0.3
  },
  "dimension": 1024,
  "frame_len_symbols": 64
}

## Non-claims

- No claim outside real d=1024, 64-symbol frames, dataset raw-SER [0.20, 0.30).
- No Polar or qLDPC winner comparison; they were not frame-identical executable candidates.
- No cross-method leakage ranking and no Route A numerical/proof claim.
