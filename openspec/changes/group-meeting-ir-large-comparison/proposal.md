---
slug: "group-meeting-ir-large-comparison"
createdAt: "2026-06-15T08:30:00.018Z"
---

# Proposal: group-meeting-ir-large-comparison

## What

Generate a large-scale real-data IR method comparison package suitable for group meeting presentation. This extends the existing `real-ir-success-first` and `optimize-real-ir-methods-after-success` results by running sweeps on an expanded real-data dataset (more dimensions, more noise regimes, more frames, longer frame lengths) and producing 9 detailed comparison CSVs, a traceability manifest, and a comprehensive analysis report.

## Why

Current results cover only 6 representative points at d=8,d=16 with 4 frames each. For a credible group meeting presentation, we need:
- Broader coverage: d=32, more noise regimes, more frames per point
- Multi-frame-length analysis: 64, 128, 256 symbols
- Method-specific diagnostics: Cascade parity thresholds, LDPC check budgets, qLDPC feasibility bounds
- Honest comparisons with Polar imported baseline
- Actionable method recommendation with caveats

## Scope

### In Scope
- Build an expanded representative subset from the existing 121-dataset real sidecar batch
- Build longer-frame variants (128, 256 symbols)
- Run Cascade-lite sweeps with optimized configs on expanded set
- Run Layered LDPC sweeps with parity threshold scan on expanded set
- Run qLDPC reference on low-noise subset
- Read existing Polar historical baseline data via polar_existing bridge
- Generate 9 analysis CSVs + manifest + group meeting report
- All outputs under `comparison_bench/outputs_comparison/group_meeting_ir_20260615/`

### Out of Scope
- Modifying src/, experiments/, tools/ frozen baseline code
- Running original Polar pipeline
- Modifying or overwriting existing sweep outputs
- Full 121-dataset exhaustive sweep (compute-bound; we select a representative subset)
- Real qLDPC hard-decode beyond current GF(2^m) reference path

## Affected Specs
- New spec: `specs/large-ir-comparison/spec.md`
