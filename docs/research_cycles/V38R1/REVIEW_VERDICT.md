# V38R1 Independent Implementation Review

**Cycle**: `V38R1`
**Review kind**: `PLAN_AND_IMPLEMENTATION_DELTA`
**Target SHA**: `8f7bc7d8d7366772ff425528cd1080fa67ef7509`
**SHA verification**: `VERIFIED_LOCAL`
**Verdict**: `ACCEPT`
**Lifecycle**: `IMPLEMENTATION_ACCEPTED / EXECUTE_NOT_AUTHORIZED`

## Accepted delta

- V38 now supplies complete Bob symbols to the empirical L2 posterior, matching
  the V36 contract.
- V38-P0 `run_01` remains immutable and is classified as
  `V38_DIRECTION_EVIDENCE_INVALID`; its structural records remain bounded
  structural evidence, while its 45 decoder records support no lane result.
- V38R1 reconstructs only the nine frozen winner matrices from accepted
  constructors and seeds, strictly compares their metrics with committed
  `run_01`, and does not depend on the ignored local NPZ.
- The guarded successor fixes the original 15 blocks, decoder settings,
  thresholds, and exactly 45 future decoder calls. The production CLI has no
  fake-runner option and writes only additive `run_02`, refusing overwrite.

## Independent evidence

- Focused posterior, reconstruction, runner, writer, and CLI tests:
  `6 passed` (`32 deselected`).
- Python compile checks: pass.
- Independent real decoder-free reconstruction: `9 / 9` winners matched the
  committed structural metrics in `212.055172 s`.
- `run_01` diff: none. `run_02`: absent. Production decoder calls: zero.
- `openspec validate` was unavailable because the command is not installed;
  the OpenSpec files were reviewed directly.

## Authorization boundary

This verdict accepts the correction and guarded execution implementation only.
It does not authorize `run_02`, formal execution, qualification, promotion,
parameter tuning, seed changes, or any scientific conclusion about Lane A/B/C.
A new explicit user `EXECUTE_AUTH` bound to the accepted implementation SHA is
required before the single decoder-only development run.

---

## Development Result Review

**Target result SHA**: `2416486f724f4fb7cbf1058d9dc1bb1fc5ded5ed`
**SHA verification**: `VERIFIED_LOCAL`
**Review kind**: `DEVELOPMENT_RESULT`
**Verdict**: `ACCEPT`
**Accepted terminal**: `V38_MULTIPLE_ROUTE_SIGNALS`
**Lifecycle**: `DEVELOPMENT_RESULT_ACCEPTED`

The single authorized V38R1 decoder-only run exited successfully and produced
exactly nine winner records and 45 decoder records. Independent recomputation
confirmed the frozen lane/source/block/seed matrix, all lane aggregates,
paired baseline counts, triage criteria, and terminal-state calculation.
`run_01` is unchanged and remains invalid evidence; `fake_runner` and the
ignored NPZ were not used.

Accepted bounded development results:

- Lane A: `0 / 15` exact recovery, median residual `115`, with all `15 / 15`
  blocks improved relative to the frozen baseline. It passes the direction
  gate through criteria B and C, but does not demonstrate correction success.
- Lane B: `9 / 15` exact recovery, median residual `0`, with `15 / 15` blocks
  improved. One additional block was syndrome-valid but not exact and is not
  counted as recovery.
- Lane C: `14 / 15` exact recovery, median residual `0`, with `15 / 15` blocks
  improved. Its only non-exact block was source `1p5M`, seed `360202`, with 63
  residual symbol errors.

These results support all three lanes as positive directions under the frozen
V38 triage gate. Lane C is the strongest observed development candidate, Lane
B is second, and Lane A supports residual reduction only. This ranking is an
inference from the bounded development records, not a formal qualification.

The blocks are deterministic samples from source-specific V25 TRAIN empirical
counts with oracle-L1 conditioning. The result is not a real-frame FER,
threshold, SKR, formal-execution, qualification, security, or promotion claim.
No rerun, tuning, seed change, or automatic V39 execution is authorized.
