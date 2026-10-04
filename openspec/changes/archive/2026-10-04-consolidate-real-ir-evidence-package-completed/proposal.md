---
slug: "consolidate-real-ir-evidence-package"
createdAt: "2026-06-15T07:24:26.018Z"
---

# Proposal: consolidate-real-ir-evidence-package

## What

Implement a CLI that consolidates existing real_ir_success_first outputs into a single evidence package under `comparison_bench/outputs_comparison/expanded_real_ir_20260615/`.

## Why

The expanded-real-ir-evidence report currently lives as a standalone markdown document with manually curated data. We need a reproducible, automated pipeline that:

1. Reads existing sweep results (no new sweeps)
2. Extracts best configurations per method
3. Consolidates scalability data
4. Generates comparison summaries
5. Produces a manifest with source hashes and config snapshots

## Scope

### In Scope
- CLI script: `comparison_bench/src/comparison_bench/cli/make_expanded_evidence_package.py`
- Input files: cascade/ldpc/qldpc sweep CSVs, scalability CSVs, ir_v3_run_manifest.json
- Output files: 7 CSV/JSON files + 1 markdown report
- pytest coverage for selection correctness and manifest generation

### Out of Scope
- Running new sweeps
- Modifying source outputs
- Changing existing CLI entry points
- Modifying frozen baseline code

## Affected Specs

- New spec: `specs/evidence-package-cli.md`
