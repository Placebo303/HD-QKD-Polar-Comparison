# V72P2D5-GF32-RATE-MOTHER — Structure Implementation Addendum (R2 runner delta)

- cycle_id: V72P2D5-GF32-RATE-MOTHER
- scope: STRUCTURE_RUNNER_IMPLEMENTATION_ONLY
- plan_revision: R2_DV3 (unchanged; no plan file edited)
- packet: STRUCTURE_EXECUTION_PACKET.md (frozen; implementation follows it)
- accepted_r2_implementation: d39b5caec5560d96991b8747bfc12f473e2fe776
- structure_runner_implementation: UNCOMMITTED_CANDIDATE
  (backfill with the candidate commit SHA after the reviewer-PASS commit;
  this file and cycle_state.yaml record the binding, no content digests)

Accepted R2_DV3 math, support, coefficient, and audit behavior is intact.
This round adds only the executable orchestration the structure packet
requires. No full 1000x1024 mother was built, no decoder was called, no
CAL/VAL row was read, and the formal output root was not created.

## 1. Orchestrator call graph

New single entry `run_structure_sequence` (core module):

```text
run_structure_sequence(authorized, ...)
  -> auth check FIRST (refuse before any preflight/builder/writer/dir work)
  -> preflight_fn (default run_structure_preflight; counts no attempt)
  -> attempts 0->1 immediately before the first full L1 builder call
  -> build L1 exactly once -> audit L1 prefixes
  -> L1 hard fail => STOP, L2 build count 0, completed=1, STRUCTURE_BLOCKED
  -> build L2 exactly once -> audit L2 prefixes
  -> combine: four_cycles total 0 => STRUCTURE_PASS
              four_cycles > 0 (rest pass) => STRUCTURE_PASS_WITH_CYCLE_RISK
  -> optional write_structure_evidence(out_dir, result) for every terminal
     outcome (PASS / CYCLE_RISK / BLOCKED / projection-blocked / exception)
```

L1->L2 order proof lines (core): `events` records
`auth_ok, preflight_done, attempt=1, L1_build, L1_audit, [L1_pass,]
L2_build, L2_audit, [L2_pass,] done`; T2_09 asserts the ordering and that
`attempt=1` precedes `L1_build`. DI `build_fn(n, m_max, k_min, seed)` /
`audit_fn(h, prefixes)` / `preflight_fn(*, authorized)` / `writer_fn`
let tests use fakes; production defaults wire the real dv3 builders and
audits. Failures leave seeds, order, family, and coefficients unchanged:
straight-line code, at most one build call per layer, no second-attempt
path of any kind.

## 2. Hard-gate fix (B2)

`audit_prefix` PASS now requires ALL eleven (was nine; base/triple
duplicate gates added, one line):

- rank == k
- zero_rows == 0
- zero_columns == 0
- isolated_variables == 0
- connected_components == 1
- largest_component_fraction == 1.0
- duplicate_projective_columns == 0
- coefficients_nonzero == true
- variable_degree_min >= 2
- base_pair_duplicates == 0 (NEW)
- support_triple_duplicates == 0 (NEW)

Any fail => `passed False`, status STRUCTURE_BLOCKED.
Only `four_cycles > 0` with the eleven passing =>
STRUCTURE_PASS_WITH_CYCLE_RISK (unchanged rule).
`run_structure_phase` and `audit_frozen_prefixes` inherit the fix via
`audit_prefix`; their signatures and return shapes are unchanged.

## 3. Per-prefix schema freeze (B3, 24 fields)

`audit_prefix()` returns exactly these 24 fields (alphabetical, frozen;
T2_16 asserts this list and count):

1. base_pair_duplicates
2. coefficients_nonzero
3. column_degree_full
4. connected_components
5. degree1_variables
6. degree2_variables
7. degree3_variables
8. duplicate_projective_columns
9. four_cycle_variable_incidence_max
10. four_cycles
11. isolated_variables
12. largest_component_fraction
13. passed
14. prefix_rows
15. rank
16. row_degree_histogram
17. status
18. support_triple_duplicates
19. total_edges
20. variable_degree_max
21. variable_degree_median
22. variable_degree_min
23. zero_columns
24. zero_rows

Reconciliation: the packet's "21 fields" are items 1-12, 15-24 minus the
three envelope items (13 passed, 14 prefix_rows, 17 status) — i.e. 21
measurement fields + 3 envelope = 24 total. Nothing was deleted to force
21; `column_degree_full` (the field T1_11 does not enumerate) is retained
and now frozen explicitly. Tests, implementation, and the 4-file outputs
all carry the same 24 per prefix.

## 4. Cost preflight (B4)

`run_structure_preflight` builds only the frozen small fixture
(n=12, m_max=10, k_min=7, prefixes 7/8/9/10) and one proxy with
n=64 <= 256 (m_max=64, k_min=48, prefixes 48/54/59/64), per layer with
the frozen layer seeds. Records per-layer proxy build walls, per-prefix
proxy audit (rank-dominated) walls, fixture walls, and peak RSS.
`extrapolate_structure_cost` applies the frozen recomputable formula
(identical text in its docstring):

```text
edge_scale = 1024 / proxy_n
rank_scale = (1000 / proxy_m)^2 * (1024 / proxy_n)
build_full_L1 = t_build_proxy_L1 * edge_scale
build_full_L2 = t_build_proxy_L2 * edge_scale
rank_full_per_prefix = mean_proxy_rank_wall * rank_scale
single = max(build_full_L1, build_full_L2) + 4 * rank_full_per_prefix
total  = build_full_L1 + build_full_L2 + 8 * rank_full_per_prefix
rss_full = rss_probe * edge_scale (None when RSS is unavailable)
blocked = single > 900 s OR total > 1800 s OR rss_full >= 2 GiB
```

Projection-blocked => sequence returns
STRUCTURE_RESOURCE_PROJECTION_BLOCKED with attempts=0, completed=0 and
zero full-builder calls (T2_07). T2_15 recomputes the formula by hand
(1.0/2.0/0.5 s example => single 7844.5 s, total 15673.0 s, blocked)
and asserts every preflight probe requests n <= 256.

## 5. Attempt semantics (B5)

- Preflight invocations never count (attempts stays 0 through preflight,
  including projection-blocked and preflight-error outcomes).
- attempts 0->1 immediately before the first full L1 builder call
  (events order asserted in T2_09); maximum one invocation, one build
  per layer at most.
- completed=1 only after all attempted prefix audits finish: L1+L2
  audited (any hard outcome, T2_01/T2_11), or L1-blocked with L2
  skipped by rule (T2_02). BLOCKED may therefore be completed=1.
- Mid-exception (builder/auditor raise) => completed=0 with the error
  message retained (T2_10).
- This round verified with fake builders only; repo `cycle_state.yaml`
  attempts/completed counters were not incremented (see section 8).

## 6. Writer (B6)

`write_structure_evidence(out_dir, result)` requires an explicit out_dir
(no default; orchestrator default None writes nothing; CLI passes none).
Refuses when out_dir already exists (no overwrite, no merge; T2_13).
Formal root is fixed as the relative path
`workspace/v72p2d5_structure/20260905_r2` (recorded in every result as
`formal_root`; absolute paths never written). Writes exactly 4 files:

- results.json (scalars + per-prefix 24-field audits + preflight
  projection + attempts/completed/decision; decoder 0, CAL/VAL 0)
- table.csv (one row per prefix: 15 scalar columns)
- report.md (decision, attempts/completed, per-layer seed/status lines,
  per-prefix k/rank/four-cycle lines)
- execution_summary.json (decision, attempts/completed, counts, file list)

Scalars plus the small row-degree histograms only. No mother, support,
coefficient, raw, generator, syndrome, or decoder-message arrays; no
digest fields; no absolute paths (T2_12 walks the payload and asserts
small lists, clean keys, clean strings, 8 table rows + header, sizes
< 64 KiB). BLOCKED and exception results yield the same 4-file set
(T2_07, T2_10). The formal root was NOT created this round.

## 7. CLI (B7)

`scripts/v72p2d5_gf32_rate_mother.py --phase structure` now enters the
single `run_structure_sequence` orchestrator (was the single-layer
`run_structure_phase`, which remains for unit use). The authorization
check runs before any preflight/builder/dir work; other phases are
unchanged; no all/real/retry/seed/family/k_min/m_max/degree params were
added (T1_17/T1_18 still green, T2_14 proves the wiring with a spy).

## 8. cycle_state binding (B8)

Only version-binding fields added; every execution authorization stays
false; no execution granted:

- accepted_r2_implementation:
  d39b5caec5560d96991b8747bfc12f473e2fe776
- structure_runner_implementation: UNCOMMITTED_CANDIDATE

## 9. Test scoping notes (original 60 preserved)

76/76 pass (60 original functions + 16 new T2_01..T2_16). Four original
tests were minimally scoped for this frozen delta, all other 56
byte-identical:

- T0_33: fixture carried a base-pair duplicate, which B2 now hard-gates;
  replaced with a verified 4x4 carrying four_cycles=2 with zero
  base/triple duplicates (same PASS_WITH_CYCLE_RISK intent).
- T0_38/T1_12/T1_14: absolute no-file-write bans now confine the 4
  `open(` writes + `mkdir` to `write_structure_evidence` (proven by
  comparing counts against that function's own source); all data-read
  bans unchanged.

## 10. No-execution confirmation

- FULL_MOTHER_BUILT: false (no 1000x1024 construction; probes <= 64)
- DECODER_CALLS: 0 (no decoder import/call path added or entered)
- CAL_ROWS_READ: 0, VAL_ROWS_READ: 0
- FORMAL_OUTPUT_EXISTS: false
  (`workspace/v72p2d5_structure/20260905_r2/` absent, T2_13)
- STRUCTURE_AUTHORIZED: false (all authorizations false; T1_19 green)
- NEXT_GATE: independent STRUCTURE_IMPLEMENTATION_REVIEW
  (reviewer writes the verdict; A5 is a placeholder, not PASS)

## 11. CLI out_dir close-out (final, implementation-only)

Small fix only; core orchestrator/preflight/writer/mother untouched:

- Call line (CLI): `_RUNNERS["structure"](authorized=True,
  out_dir=STRUCTURE_OUT_DIR)` with `STRUCTURE_OUT_DIR = ROOT /
  "workspace" / "v72p2d5_structure" / "20260905_r2"`, ROOT resolved
  from the CLI file location (`_HERE.parents[1]`). No absolute paths,
  no new CLI params.
- Auth-before-create preserved: the `is_phase_authorized` gate still
  runs first; the orchestrator call happens only after it passes.
- Existing-dir refuse kept: the writer's `FileExistsError` propagates
  through the CLI's refuse path (nonzero exit, no swallow).
- Other phases unaffected: `g0 | p0-cost | g1 | g2` still call with
  `authorized=True` only (T2_18 asserts `g0` receives no `out_dir`).
- No preflight/writer/mother change; no science claim.
- Binding: `structure_runner_implementation` set to
  `737f731702106bacff3c509a3f877a8b037f1434` in `cycle_state.yaml`
  (`accepted_r2_implementation` stays
  `d39b5caec5560d96991b8747bfc12f473e2fe776`).
- `next_gate` set to `STRUCTURE_PRE_EXECUTE_REVIEW`; it takes effect
  only on independent review PASS. All execution authorizations stay
  false; no execution granted.
- Tests: 78/78 pass (76 prior + T2_17 unauthorized no-formal-dir +
  T2_18 frozen-out_dir fake-files). The real CLI authorized path was
  NOT run; the formal root was NOT created.
