# Design: consolidate-real-ir-evidence-package

## Overview

A single-file CLI that reads existing sweep results from `real_ir_success_first/` and produces a consolidated evidence package under `expanded_real_ir_20260615/`. The CLI is idempotent, read-only with respect to source data, and produces deterministic outputs.

## Goals

1. **Reproducibility**: Same inputs → same outputs (deterministic ordering, stable hashes)
2. **Read-only**: No modification to source CSVs or manifest
3. **Graceful degradation**: Missing source files produce warnings, not errors
4. **Traceability**: Manifest records source hashes and config snapshots

## Constraints

- No new sweeps may be triggered
- Source outputs under `real_ir_success_first/` must not be modified
- All outputs go under `expanded_real_ir_20260615/`
- qLDPC rows must preserve `success_classification` from source
- Cascade/LDPC selection must filter `real_ir_success=True` before finding minimum

## Technical Approach

### Module Structure

```
comparison_bench/src/comparison_bench/cli/make_expanded_evidence_package.py
```

Single-file CLI with:
- `main()` entry point (argparse)
- Helper functions for each output type
- No external dependencies beyond pandas, hashlib, subprocess

### Data Flow

```
Input CSVs → Filter/Group → Aggregate → Write Output CSVs
                                           ↓
ir_v3_run_manifest.json ──────────────→ expanded_evidence_manifest.json
```

### Selection Logic

1. **Cascade optimized**: `df[df['real_ir_success'] == True].groupby('dataset_id').apply(lambda g: g.loc[g['leak_EC_actual_bits'].idxmin()])`
2. **LDPC optimized**: Same pattern as Cascade
3. **qLDPC reference**: `df.groupby(['dataset_id', 'q', 'frame_len_symbols']).apply(lambda g: g.loc[g['n_frames_success'].idxmax()])`
4. **Scalability**: Concat real + synthetic, deduplicate by `dataset_id`
5. **Method comparison**: Group by `frame_len_symbols`, count successes, average metrics
6. **Failure analysis**: Filter `real_ir_success=False`, group by method/dimension/bin_width, count

### Manifest Structure

```json
{
  "timestamp": "2026-06-15T07:30:00Z",
  "git_commit": "<short-hash>",
  "source_files": {
    "cascade_sweep": {
      "path": "real_ir_success_first/cascade_param_sweep_results.csv",
      "sha256": "<hash>"
    }
  },
  "source_manifest": {
    "path": "real_ir_success_first/ir_v3_run_manifest.json",
    "config_snapshots": { ... }
  },
  "output_files": [ "cascade_optimized_summary.csv", ... ]
}
```

### Idempotency

- Output directory is created if missing, otherwise reused
- Generated files are overwritten on each run
- SHA-256 hashes are computed from file content, not timestamps

## Alternatives Considered

### Alt 1: Multiple CLI scripts
- **Pros**: Modularity
- **Cons**: Harder to maintain consistency, more entry points
- **Decision**: Single CLI for atomicity

### Alt 2: Write to temp dir then move
- **Pros**: Atomicity
- **Cons**: Adds complexity, temp dir cleanup
- **Decision**: Direct write (non-critical outputs)

### Alt 3: Cache hashes in manifest
- **Pros**: Faster re-runs
- **Cons**: Stale cache, complexity
- **Decision**: Always recompute (small files)

## Impacted Files / Modules

| File | Action | Description |
|------|--------|-------------|
| `cli/make_expanded_evidence_package.py` | Create | Main CLI script |
| `tests/test_evidence_package.py` | Create | pytest coverage |
| `cli/__init__.py` | Modify | Add entry point (if needed) |

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Source CSV format changes | Low | Medium | Validate columns on read, fail gracefully |
| Large CSVs cause OOM | Low | Low | Sweep results are small (<1000 rows) |
| Git not available for manifest | Medium | Low | Fall back to "unknown" commit hash |
| Output dir permission denied | Low | Medium | Check writability before starting |
