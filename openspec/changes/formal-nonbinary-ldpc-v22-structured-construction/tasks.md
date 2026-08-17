# Tasks: formal-nonbinary-ldpc-v22-structured-construction

Status: IN_PROGRESS — DE gate harness implemented; q16 smoke run completed; q1024 gate pending

## T0 Planning
- [ ] P0: freeze V22 task packet
- [ ] P1: select ensemble and DE budget/seeds/stop rules

## T1 Engineering
- [x] I01: implement V22 DE gate harness (structured MC-DE wrapper; full MET/SC still pending)
- [x] I02: DE gate CLI + tests
- [ ] I03: finite construction if DE passes

## T2 Execute
- [ ] E01: DE gate on V17 structured channel (q16 smoke done; q1024 pending)
- [ ] E02: finite Bob-only FER / f_total

## T3 Verify/Closeout
- [ ] V01: Bob-only semantic verifier
- [ ] C01: docs/memory update
