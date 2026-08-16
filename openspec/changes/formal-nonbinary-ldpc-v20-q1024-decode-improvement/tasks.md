# Tasks: formal-nonbinary-ldpc-v20-q1024-decode-improvement

Status: DRAFT

## T0 Planning
- [ ] P0: freeze proposal/design/tasks and get main-thread/acceptance review
- [ ] P1: select M1/M2/M3/M4 subset and pre-register budgets/seeds/stop rules

## T1 Engineering
- [ ] I01: implement bounded q-ary OSD order-0/1 using GF(q) field tables
- [ ] I02: add OSD integration to `nonbinary_v19_finite` or new `nonbinary_v20_finite`
- [ ] I03: add improved construction/QC-PEG helper if M2 selected
- [ ] I04: add retry/blind-reconciliation helper if M3 selected
- [ ] I05: add channel-aware DE gate CLI if M4 selected
- [ ] I06: tests for all new V20 modules

## T2 Execute
- [ ] E01: execute once on deterministic q=1024 synthetic frames
- [ ] E02: record exact_correct / decode_failed / FER / f / runtime / status

## T3 Verify/Closeout
- [ ] V01: read-only strict replay
- [ ] C01: update CURRENT_TASK.md, AGENT_HANDOFF.md, AGENT_PROJECT_MEMORY.md
- [ ] C02: local git commit only; no push
