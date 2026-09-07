# G1 readiness rework (implementation candidate only)

- Change: `v72p2d5-g1-readiness-rework`
- Predecessor: `v72p2d5-p0-g1-g2-production-path` (production path, candidate)
- Cycle: `V72P2D5-GF32-RATE-MOTHER`
- Lifecycle: `IMPLEMENTATION_CANDIDATE_ONLY` (no execution, no authorization)
- Branch: `formal-ir-v72p1-addendum-clean`
- Prerequisite: P0 accepted `COST_MEASUREMENT_ONLY`; `next_gate: G1_PACKET_REVIEW`; `G1_PACKET_REVIEW_R1.md` = `G1_PACKET_REVIEW_PASS`
- Authority: `G1_EXECUTION_PACKET_R1.md` (frozen contract) + `G1_PACKET_REVIEW_R1.md` D1–D6 and A01–A13 (decided, not reopened here)

## Goal

Implement the reviewed G1 readiness deltas D1–D6 exactly as decided, as an
implementation candidate only: fresh G1 root, Windows RSS sampling, aggregate
observability, fail-loud writers, no-subdirectory test invariant, reviewed
signal rule with seven terminal labels, and a deferred real-launch sentinel
contract.

## Why

The packet review found the frozen G1 contract correct on all 16 audited
parameters with zero scientific disagreement, but G1 is
`IMPLEMENTATION_REWORK_REQUIRED_BEFORE_PRE_EXECUTE`: the production constant
still points at the retained VOID root, Windows RSS is unmeasured, per-`f`
schema lacks syndrome/iteration/RSS observability, both writers carry a
duplicated `app_failure_fraction` fallback, test snapshot helpers miss nested
writes, and the current `passed = monotonic and nonfinite == 0` admits an
all-zero exact sequence.

## Decided deltas (transcribed, not decided here)

- Fresh root `workspace/v72p2d5_g1/20260907_r2/` (D1, OQ-G1-ROOT).
- Windows current-process working-set RSS via stdlib `ctypes`; sample after
  every completed block result; persist per-`f` and run maxima; 2 GiB remains
  a hard gate; `None` is resource failure (D2, OQ-G1-RSS).
- Aggregate exact/syndrome/iteration observability, scalar only (D3).
- Direct fail-loud access to `app_failure_fraction` in G1/G2 writers (D4).
- No-subdirectory invariant in both test helpers (D5).
- Real-launch sentinel remains a Pre-EXECUTE check, not run here (D6).
- Reviewed signal rule and seven terminal labels with frozen precedence
  (OQ-G1-SIGNAL, OQ-G1-WATCHDOG, OQ-G1-OUTCOME).

## Scope

- Modify only `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
  and the two D5 test files; land the read-only `G1_PACKET_REVIEW_R1.md`.
- Tests use explicit fake decoder, injected fake Model-F arrays, and tmp
  output roots only.

## Non-Goals

- No G1 execution or authorization; no formal G1/G2 output creation; no
  decoder run; no CLI `--phase` invocation of any kind.
- No prepare/verify replay; no CAL/VAL/parquet/raw-row read (the D6 probe's
  accepted-Model-F consumer load is the sole named exception, deferred to
  Pre-EXECUTE and not run here).
- No change to seeds, row tables, width, `f` values, block counts, oracle
  subset, decoder parameters, budgets, G2 grading, Model-F input, or P0/G0
  behavior.
- No new dependency, monitor, retry/resume, hash/manifest, compat layer, or
  generic abstraction.

## Acceptance Criteria

- [ ] A01–A13 from `G1_PACKET_REVIEW_R1.md` §5 all checked with fake/injected/tmp evidence.
- [ ] Full three-file D5 suite green; pre/post formal-root snapshots identical;
  proposed G1 `20260907_r2` and G2 roots absent before/after tests.
- [ ] All authorizations still false, promotion false, `next_gate` unchanged.
