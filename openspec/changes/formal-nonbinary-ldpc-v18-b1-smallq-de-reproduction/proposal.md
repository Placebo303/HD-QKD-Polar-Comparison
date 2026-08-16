# Proposal: formal-nonbinary-ldpc-v18-b1-smallq-de-reproduction

> Status: PLANNING — Route B M0, gate-first engineering. No finite code, no q=1024 run.

## What
Reproduce Müller 2024 small-q NB-LDPC density-evolution (DE) pipeline using the
repo's existing frozen DE/MC-DE assets. This change only builds a gate harness;
it does not construct a production code.

## Why
Route B efficiency work must first prove that our MC-DE + DE search pipeline
can reproduce published small-q thresholds before optimizing q=1024 structured
channels.

## Scope
- New thin orchestrator importing existing `nonbinary_v10_de.run_de_search` and
  `nonbinary_v8_mcde` read-only.
- Smoke mode with tiny budget; production execute later under freeze review.
- No modifications to frozen V8/V9/V10/V14/V17 sources.

## Out of scope
- q=1024 DE search
- finite code construction
- rerunning/tuning V14/V17 gates
