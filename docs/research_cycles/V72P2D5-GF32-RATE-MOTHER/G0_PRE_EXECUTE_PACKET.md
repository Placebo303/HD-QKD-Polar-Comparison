# V72P2D5-GF32-RATE-MOTHER — G0 Pre-Execute Packet (frozen)

Status: `G0_IMPLEMENTATION_ACCEPTED_R1 / EXECUTE_NOT_AUTHORIZED`

This packet freezes the single authorized G0 invocation contract. It grants
no execution by itself; execution additionally requires an independent
pre-execute review PASS on the exact accepted implementation SHA.

## 1. Frozen command

```text
python scripts/v72p2d5_gf32_rate_mother.py --phase g0
```

No other command, phase, flag, or override is authorized for G0.

## 2. Frozen seeds (exactly once each, no retry, no substitution)

```text
2026090510, 2026090511, 2026090512, 2026090513,
2026090514, 2026090515, 2026090516, 2026090517
```

## 3. Attempt semantics

- Maximum ONE G0 invocation, eight tiny synthetic blocks (one per frozen seed).
- Invocation count increments immediately before the first authorized
  historical decoder call; preflight/test-only fake calls do not count.
- No rerun, reseeding, seed search, tuning, or partial-subset claim.

## 4. Budget

- Outer-process 120-second watchdog is required (a single hanging historical
  call must not escape the budget).
- Per-seed before/after checks: elapsed `<=120s` and RSS `<2GiB`; on exceed,
  remaining seeds stop as `G0_BLOCKED_RESOURCE` with obtained scalars
  preserved (never zeroed, never relabeled).
- Timeout/over-memory is `G0_BLOCKED_RESOURCE` with evidence retained.

## 5. Output root (must-not-exist-before)

```text
workspace/v72p2d5_g0/20260905_r2/
```

The directory must be absent before the authorized run. After the run it
holds exactly these four files, scalars/seeds/status/counts/error-bounds
only:

```text
results.json
table.csv
report.md
execution_summary.json
```

No matrices, support/coefficient arrays, prior tables, syndromes, raw
symbols, decoder messages, absolute paths, hashes, checksums, or tags.

## 6. Pre-execution gates

- `HEAD == origin/formal-ir-v72p1-addendum-clean == 98624e59` (accepted
  implementation; re-derive from `git log` / `cycle_state.yaml`).
- `py_compile` clean plus the complete existing D5 suite (104 tests) PASS.
- Formal output root absent; CAL reads `0`, VAL reads `0`.
- `g0_implementation_accepted=true`; `g0_execution_authorized` becomes true
  only via the separate independent pre-execute review, while structure /
  P0 / G1 / G2 / real / formal authorizations stay false.

## 7. Unauthorized scope

P0, G1, G2, real-data, formal, second G0 invocation, graph change, and any
data read (CAL/VAL/parquet/registry/raw pairs) stay unauthorized.

## 8. Honest outcomes

Only these G0 decisions are legal:

- `G0_PASS`
- `G0_BLOCKED_MATH`
- `G0_BLOCKED_DECODER`
- `G0_BLOCKED_RESOURCE`

Execution completion is not conditioned on algorithm success; a blocked
outcome with retained evidence is a complete run.
