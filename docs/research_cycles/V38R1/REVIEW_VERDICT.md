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
