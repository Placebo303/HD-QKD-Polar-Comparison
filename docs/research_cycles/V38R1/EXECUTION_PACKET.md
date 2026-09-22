# V38R1 Authorized Development Execution Packet

**Cycle**: `V38R1`
**Accepted implementation SHA**: `8f7bc7d8d7366772ff425528cd1080fa67ef7509`
**Implementation acceptance commit**: `65301365517af5718fce382cc8c9e40dd371ad65`
**Authorization**: `EXECUTE_AUTH`
**Execution count**: exactly once
**Formal execution**: not authorized
**Scientific promotion**: not granted

## Authorized command

```powershell
python scripts/execute_v38r1_development.py --development-execution-authorized
```

## Frozen scope

- Reconstruct exactly the nine accepted V38-P0 winner matrices from their
  frozen constructors and seeds, with strict comparison against committed
  `run_01` structural metrics.
- Use the same 15 frozen V36 A3 development blocks.
- Run exactly 45 real decoder calls with `max_iter=30`,
  `damping_alpha=1.0`, and GF(32) polynomial 37.
- Write only the additive `run_02` evidence defined by the accepted runner.
- Do not tune parameters, change seeds, repeat structural selection, depend on
  the ignored local NPZ, overwrite `run_01`, or rerun after any scientific
  outcome.

## Preflight and stop rules

Before starting, verify HEAD contains accepted implementation
`8f7bc7d8d7366772ff425528cd1080fa67ef7509`, `run_01` has no diff, and
`run_02` does not exist. Stop without execution if any check fails.

If execution raises an error or writes a partial `run_02`, retain it unchanged
and return a blocker. Do not delete, repair, resume, or rerun without a new
main-thread decision. Do not mark the result accepted or draw scientific
conclusions.
