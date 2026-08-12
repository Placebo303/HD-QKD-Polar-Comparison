# Final IR Method-Selection Runbook

This is the bounded, additive three-stage workflow for selecting between the
two executable comparison candidates only: `cascade_lite` and
`layered_ldpc_lite`. It does not replace the frozen Polar pipeline.

## Authoritative Evidence

- Phase 2 lock: `comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1/`.
- Phase 3 run: `comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v2/`.
- Phase 4 audit: `comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v4_audit/`.

The original Phase-3 files in `20260725_v1/` are invalid for decisions; see
`invalid_run_notice.json`. The v3 audit is superseded; see its additive
`superseded_notice.json`. Do not overwrite either directory.

## 1. Lock Before Tuning

Create a new additive directory only after choosing an immutable source table:

```powershell
python -m comparison_bench.src.comparison_bench.cli.lock_final_ir_data --source INPUT.parquet --output-dir comparison_bench/outputs_comparison/final_ir_method_selection/NEW_V1
```

The lock freezes source/split hashes, group-disjoint tuning and confirmation
keys, shared mapping and verification, the candidate scope, and the stopping
rule. Verify it without writing:

```powershell
python -m comparison_bench.src.comparison_bench.cli.lock_final_ir_data --verify --manifest comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1/data_lock_manifest.json
```

## 2. Bounded Tuning and Confirmation

Use a new output directory and explicitly pass the immutable lock. The runner
writes `pre_run_plan.json` before tuning, then preserves all attempted tuning
and confirmation outcomes, including failures.

```powershell
python -m comparison_bench.src.comparison_bench.cli.run_final_ir_method_selection --lock-manifest comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1/data_lock_manifest.json --output-dir comparison_bench/outputs_comparison/final_ir_method_selection/NEW_V2 --time-limit-s 600
```

Only one global frozen configuration per candidate may reach confirmation.
Do not extend the confirmation set or choose configurations from confirmation
outcomes. `qldpc_reference` remains reference-only and `polar_existing`
remains non-frame-identical historical context.

## 3. Read-Only Audit and Decision

For a new run, write its audit into a fresh additive directory. The audit
checks hashes, identical confirmation keys, complete paired outcomes, frozen
grid membership, status denominators, and the bounded decision rule.

```powershell
python -m comparison_bench.src.comparison_bench.cli.audit_final_ir_method_selection --v1-dir comparison_bench/outputs_comparison/final_ir_method_selection/NEW_V1 --v2-dir comparison_bench/outputs_comparison/final_ir_method_selection/NEW_V2 --output-dir comparison_bench/outputs_comparison/final_ir_method_selection/NEW_V4_AUDIT
```

Revalidate the authoritative 20260725 evidence without creating or replacing
files:

```powershell
python -m comparison_bench.src.comparison_bench.cli.audit_final_ir_method_selection --verify --v1-dir comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1 --v2-dir comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v2 --output-dir comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v4_audit
```

The current authoritative audit yields `no_decision`: 60/60 Cascade and 59/60
LDPC independently verified successes have one Cascade-only discordance, which
is not significant under the pre-registered exact paired test. This claim is
limited to real d=1024, 64-symbol frames in dataset raw-SER [0.20, 0.30).
It does not rank method-specific leakage across methods, select Polar/qLDPC,
or establish a production winner.

## Route A Gate

The audit's Route A compatibility gate is intentionally a document/schema
check. It fails for the current comparison outcome schema because the required
universal-hash verification, leakage, and correctness-budget fields are not
present. A failed gate is not a Route A rerun and supports no numerical or
formal-proof claim.

## Output Policy

All paths above are additive under
`comparison_bench/outputs_comparison/final_ir_method_selection/`. Never reuse
an existing run directory, modify `results/`, or change frozen `src/`,
`experiments/`, or `tools/` code.
