# V15 Aborted Draft Notice (2026-08-15)

Change: `formal-nonbinary-ldpc-v15-high-rate-candidate`

**Status**: **ABORTED DRAFT — NOT LAUNCHED** (2026-08-15).

## Why aborted

- This change was drafted (proposal.md + design.md only) while the V14
  efficiency gate was still pending.
- V14 `gate_state=fail` (2026-08-15, evidence commit `1cdc63b6`, E02
  independent review ACCEPT): no frozen point converged on the structured
  channel at rate 0.93–0.94, f≤1.3.
- Per V14's frozen discipline, FAIL ⇒ route frozen; V15 is **not
  launched** (`未立项/前置门失败`).

## Frozen semantics retained

- **No finite code** `nbldpc_v15_hr_v1` was constructed; no code, decoder,
  canary, development, qualification, real-data, or promotion output exists
  under V15.
- **Delta spec**: none exists (proposal/design drafts only) and none is
  merged into `openspec/specs/`.
- The drafts are retained immutably as the planning record of the gated
  route; their proposal.md precondition statements (`V14 gate_state = pass`
  required) remain correct.

## Future boundary

V15 may be reopened only via a NEW OpenSpec change after a new DE gate
PASS on a different ensemble family (e.g. V17 multibit/bit-plane gate
PASS). Do not relaunch V15 from these drafts without that gate.
