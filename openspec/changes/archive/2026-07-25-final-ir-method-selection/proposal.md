# Change Proposal: final-ir-method-selection

## Summary

Pre-register a bounded, frame-identical confirmation protocol to select the
best **executable comparison candidate** between `cascade_lite` and
`layered_ldpc_lite`. This is a research comparison decision, not a production
replacement for the frozen Polar pipeline.

## Motivation

Existing results support Cascade-lite as the current preferred executable
non-Polar candidate and Layered LDPC-lite as a control candidate, but they do
not provide a final same-frame selection. Historical Polar imports are useful
context only: the bridge currently matches aggregate dimension/bin-width
information, lacks frame-ID and replay binding, has one tracked-row fixture,
and relies on legacy unavailable sources.

## Scope

In scope:

- lock confirmation inputs and compare both executable candidates on identical
  frames, preprocessing, success classification, and verification;
- pre-register a tuning/confirmation split and a bounded decision rule;
- preserve all attempted frames and failures in denominators;
- report compatible leakage decompositions separately from incompatible ones;
- record reproducibility provenance and additive outputs.

Out of scope:

- production replacement or promotion of either candidate;
- ranking `qldpc_reference`, which remains `reference_only`;
- using `polar_existing` as frame-identical evidence;
- numerical Polar reruns or changes to `src/`, `experiments/`, `tools/`, or
  public schemas.

## Success Criteria

- The protocol defines its supported dimension, SER, and frame-length domain.
- A frozen configuration and evidence manifest make confirmation reproducible.
- The final report makes a bounded selection only if pre-registered sample-size
  and confidence criteria are met; otherwise it reports no final winner.
- Route A required-field compatibility is checked without a numerical rerun.

