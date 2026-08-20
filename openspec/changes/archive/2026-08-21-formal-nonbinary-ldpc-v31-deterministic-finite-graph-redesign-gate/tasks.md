# V31 Tasks — deterministic finite-graph redesign gate

Status: FROZEN_BY_USER_OBJECTIVE (new user-authorized change, 2026-08-20).
The explicit V31 goal text authorizes implementation and one pre-registered execution; no qualification/promotion is authorized.

## Stable planning IDs

### P001 — predecessor and input binding
- [ ] Bind V25 inventory/split/channel-count paths exactly as in proposal.
- [ ] Bind V26 canonical run_02 (RUN_MANIFEST/m0_report/readonly_verify).
- [ ] Bind V28R canonical run_02_v28r (v28_config/v28_evidence/RUN_MANIFEST/readonly_verify).
- [ ] Bind V30R canonical run_01 read-only.
- [ ] Bind `GF2mField.create(32)`, poly `0b100101`, field_id
  `c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`,
  zero-based `ratio_index`.
- [ ] Freeze H float64 values from V26 A02 adapter_H for all three sources.
- [ ] Freeze allocation table for n=1024 and n=2048 (m1=16, m_total, m2,
  leak_total, f_total<1.3).

### P002 — architecture and candidate freeze
- [ ] Freeze `m1=16` only; no screen, no other m1 candidates.
- [ ] Freeze families `PEG-capacity-aware` and `QC-cyclic-projective`.
- [ ] Freeze coefficient-label rule = V30R bounded rule (projective duplicate
  rejection, newly-closed Tanner-6 `(degenerate_6_new, ratio_index)` min, first
  coefficient 1, Tanner-8 topology-only).
- [ ] Freeze hard support occupancy <=31 for every support pair.
- [ ] Freeze M1: per-n 30-call confirmation (5 seeds × 3 sources × 2 layers),
  seeds 30101..30105, n_samples=2000, max_iter=200, tol=0.01, streak=20;
  both n must pass.
- [ ] Freeze M3: full validation windows (100 blocks/source at n=1024, 50
  blocks/source at n=2048), max_iter=200; per-source thresholds
  exact>=95% and tag>=95% and false_accept==0; V31 pass requires each n to have
  at least one passing family.

## Milestones

- [ ] M0/I01–I04: M0 read-only predecessor audit implemented and verified.
- [ ] M1/I05–I09: M1 pre-registered 60-call DE confirmation (30 per n)
  implemented, tested with fake runner, and executed in production.
- [ ] M2/I10–I17: deterministic family construction (PEG-capacity-aware,
  QC-cyclic-projective) implemented, occupancy<=31, projective-hard-gate,
  full rank, label-replay, tests.
- [ ] M3/I18–I25: Bob-only full-window validation at both n; per-block
  syndrome/exact/tag records; per-source FER/waterfall/failure-position
  summaries; pass/fail terminal.
- [ ] M4/I26–I29: read-only verifier, terminal classification, report,
  docs/memory/decision-log closeout, local commit (no push).

## Acceptance IDs

- **A01** M0 reproduces V30R baseline counts without writing predecessor dirs.
- **A02** Allocation table exact for both n with all f_total < 1.3.
- **A03** M1 registry has exactly 30 registered calls per n in the frozen order;
  production run persists all calls; per-n 30/30 pass required.
- **A04** Both families deterministic, no RNG/seed library/random search.
- **A05** Every matrix has occupancy<=31, no duplicate projective keys, no
  proportional pairs, no zero row/column, full rank.
- **A06** PEG-capacity-aware support score is exactly
  `(occupancy_after, component_flag, distance_cost, max_degree_after,
  sumsq_after, a, b)` and capacity-exhausted candidates are skipped.
- **A07** QC-cyclic-projective support order is exactly cyclic-shift enumeration
  by increasing s then increasing a, with `s % m == 0` candidates skipped, and
  occupancy<=31 asserted.
- **A08** Label replay uses frozen `nonzero_cycle` order and
  `(degenerate_6_new, ratio_index)`; Tanner-8 is topology-only.
- **A09** Validation block identity exact: n=1024 100 blocks/source, n=2048 50
  blocks/source; frames 1M 1200..1599 / 1p5M 1660..2059 / 2M 2187..2586.
- **A10** Bob-only sequential decoding; L2 not run when L1 fails; no Alice
  truth passed to adapter/decoder.
- **A11** Per-block records complete: syndrome convergence, exact, tag, false
  accept, symbol-error counts, iterations, runtime, failure positions.
- **A12** Per-source FER/waterfall/failure-position summaries recomputed by the
  read-only verifier from persisted block records.
- **A13** Terminal recomputed equals persisted; pass requires each n to have at
  least one passing family; fail otherwise.
- **A14** Read-only verifier returns ok=true with problems=[] and
  no_de_rerun/no_decoder_rerun true.
- **A15** No V30R packet rerun, no V29 holdout, no raw .ttbin, no
  qualification/promotion, no push.

## Execution plan (post-freeze ACCEPT)

1. Implement `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v31.py`,
   CLI `comparison_bench/src/comparison_bench/cli/run_nonbinary_v31_gate.py`,
   and tests `comparison_bench/tests/test_nonbinary_v31.py`.
2. Run T0/T1 tests (`pytest -q tests/test_nonbinary_v31.py -p no:cacheprovider`).
3. Run canonical production gate:
   `python -m comparison_bench.src.comparison_bench.cli.run_nonbinary_v31_gate \
   comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01`
4. Run/verify read-only verifier; persist `readonly_verify.json`.
5. Close with `finite_graph_pass` or `finite_graph_fail`; write report
   `docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md`;
   update CURRENT_TASK.md, HANDOFF.md, AGENT_HANDOFF.md, AGENT_PROJECT_MEMORY.md,
   docs/decision-log.md; commit locally (no push).
