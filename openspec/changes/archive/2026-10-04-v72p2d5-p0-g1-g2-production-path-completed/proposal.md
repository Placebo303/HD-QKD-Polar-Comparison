# V72P2D5 P0/G1/G2 production path (implementation candidate only)

- Change: `v72p2d5-p0-g1-g2-production-path`
- Predecessor: `formal-ir-v72p2d5-gf32-rate-mother-plan` (R2_DV3, PLAN accepted; STRUCTURE accepted; G0 recovery accepted)
- Cycle: `V72P2D5-GF32-RATE-MOTHER`
- Lifecycle: `IMPLEMENTATION_CANDIDATE_ONLY` (no execution, no authorization)
- Branch: `formal-ir-v72p1-addendum-clean` (per task packet)
- Prerequisite: G0 recovery accepted; `cycle_state.next_gate=P0_PACKET_REVIEW`

## Goal

Make P0, G1, G2 production-reachable through existing CLI phases using the
accepted GF32 decoder and dv3 nested mother, with the rate-scan prefix defect
fixed. Produce an implementation candidate only.

## Why

Current `_run_rate_scan` computes per-`f` row counts but decodes every `f`
with the same full `h1/h2` matrices. A reported rate point without its
corresponding matrix prefix `H1_f=H1_mother[:m1(f)]`,
`H2_f=H2_mother[:m2(f)]` is invalid. P0/G1/G2 are therefore not
production-reachable today despite frozen plans, seeds, budgets, and call
counts.

## Defect statement (frozen)

`_run_rate_scan(decode_fn, h1, h2, ...)` loops `f in f_list`, records
`per_f` entries per `f`, but calls `_run_layered_block(decode_fn, h1, h2, ...)`
with identical `h1/h2` for every `f`. `run_g1_phase`/`run_g2_phase` compute a
`frozen_rows` dict but never slice. `run_p0_cost_phase` loops `f` but never
uses `f` for slicing either. Fix: each `f` MUST decode with
`H1_f = H1_mother[:m1(f)]` and `H2_f = H2_mother[:m2(f)]`, where `m1(f)/m2(f)`
are the frozen tables below. Same-mother prefix reuse across `f` is required;
per-`f` reconstruction is forbidden.

## Frozen order

`STRUCTURE accepted -> G0 accepted -> P0 -> G1 -> G2`. This change does not
reorder, skip, or merge gates. No single authorization across P0/G1/G2.

## Scope

- Fix prefix slicing in the rate path (P0/G1/G2).
- Add production-reachable synthetic stage builders for P0/G1 (width 64) and
  G2 (width 256) reusing `build_dv3_nested_mother` (one max mother per
  layer/width, prefix reuse, fixed graph seeds).
- Connect historical GF32 decoder (`max_iter=90`, `damping_alpha=1.0`, cold
  start) on the authorized path; keep fake injection for tests.
- Add one explicit frozen model-F preparation function reusing `build_f_model`
  and accepted axis semantics, with a BLOCKED path (no VAL, no G0 toy reuse,
  no invented distribution).
- Wire existing CLI phases `p0-cost`, `g1`, `g2` to the builders.
- Add one explicit four-file writer per stage root with no-overwrite.
- Focused tests only proving items 1-8 of the frozen packet.

## Non-Goals

- No P0/G1/G2 execution or authorization in this change. No
  `p0_cost/g1/g2_execution_authorized=true`, no decoder run, no `run_01`,
  no formal output creation.
- No CAL/VAL/raw/real-data read during implementation or tests
  (`cal_rows_read=0`, `val_rows_read=0`).
- No generic parameter-sweep framework; no `IRRunResult` adapter; no
  concurrency/resume/retry; no hashes/manifests/versioning; no arbitrary YAML
  grid; no alternate graph families; no `max_iter`/damping/seed tuning.
- No change to frozen experiments, thresholds, seeds, budgets, call counts,
  G2 four-state grading, or `exact_failure_fraction` naming.
- No change to accepted STRUCTURE/G0/G0-recovery code paths beyond strict
  regression preservation.
- No new defensive/audit/checksum/hash/tag machinery.

## Impact Scope

- Code (candidate only, no execution):
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`,
  `scripts/v72p2d5_gf32_rate_mother.py`
- Tests (focused only):
  `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`
  (additive cases; existing G0/recovery/structure cases unchanged)
- Docs (this change only):
  `openspec/changes/v72p2d5-p0-g1-g2-production-path/`
- Explicitly untouched: `src/`, `experiments/`, `tools/`, `results/`,
  frozen D5 plan files, `cycle_state.yaml` authorizations, formal
  `workspace/v72p2d5_*` output roots.

## Acceptance Criteria

- [ ] Each `f` decodes with its own `H1[:m1(f)]` / `H2[:m2(f)]` prefix from the
  same mother; different `f` use different row counts per frozen tables.
- [ ] One max mother per layer/width; prefixes reused across `f`; fixed graph
  seeds; no seed search, no per-`f` rebuild.
- [ ] Historical decoder connected with `max_iter=90`, `damping_alpha=1.0`,
  `warm_beliefs=None` on the authorized path only.
- [ ] Single model-F prep function reusing `build_f_model`; no G0 toy reuse
  for P0/G1/G2; no VAL read; BLOCKED verdict with single missing artifact if
  accepted input needs CAL.
- [ ] `python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost|g1|g2`
  reach the stage builders (still refuse while unauthorized).
- [ ] Four-file writers refuse overwrite at the three frozen roots.
- [ ] Frozen experiments, call counts, seeds, budgets, oracle-diagnostic-only
  semantics, `exact_failure_fraction` naming, and G2 grading preserved.
- [ ] Focused tests prove item 8 of the packet; G0/recovery/structure tests
  still pass; `py_compile` clean; no CAL/VAL read; no formal output created.
