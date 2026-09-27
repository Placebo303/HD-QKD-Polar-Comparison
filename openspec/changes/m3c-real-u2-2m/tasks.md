# Tasks

- [x] M3C-01: implement a new thin real u2 diagnostic runner exactly as frozen in the packet, preserving M0 and M3-b defaults/artifacts.
- [x] M3C-02: fake-only focused tests for gates, roots, data/frame identity, graph prefix, oracle-triggered rescue, undetected/full10 isolation, budget and no production calls.
- [x] M3C-03: independent implementation review and main-thread Pre-EXECUTE with exact command, fresh roots, source presence/identity, budget, focused tests and explicit grant.
- [x] M3C-04: run R1 then R2 only if R1 machine gate passes; retain an execution record and all failures, no retry/resume. R2 stopped `INCOMPLETE-wall`; see `STOP_RECORD.md`.
- [ ] M3C-05: independent Pre-RESULT from actual per-frame artifacts, then main acceptance limited to two real 2M u2 graph-instance diagnostics. Not reached because R2 is incomplete; no result promotion under this packet.
