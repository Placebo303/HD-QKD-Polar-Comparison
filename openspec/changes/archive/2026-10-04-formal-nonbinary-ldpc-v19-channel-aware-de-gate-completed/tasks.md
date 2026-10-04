# Tasks: formal-nonbinary-ldpc-v19-channel-aware-de-gate

Status: DRAFT — scoping + binary-MLC prototype implemented; DE gate still pending

## T0 Planning
- [ ] P0: freeze proposal/design/tasks and get user gate approval
- [ ] P1: define effective channel models and honest leakage formula

## T1 Engineering
- [x] I00: channel scoping CLI (per-plane h2, ideal f, existing v4/v5 f)
- [x] I01: binary-MLC prototype using v4 H1 + v5 H2 fallback
- [ ] I02: implement v19 channel-aware DE gate CLI
- [ ] I03: tests for effective channels and DE gate plumbing

## T2 Execute
- [ ] E01: execute rate ladder on selected mechanism(s) once
- [ ] V01: read-only verify + strict replay

## T3 Closeout
- [ ] C01: decision log, memory triage, CURRENT_TASK/AGENT_HANDOFF update
