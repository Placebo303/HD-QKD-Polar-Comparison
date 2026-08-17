# Tasks: formal-nonbinary-ldpc-v22-structured-construction

Status: IN_PROGRESS — SC-LDPC DE gate passes at q1024 p=0.05 max_iter=50; higher p/non-structured still pending

## T0 Planning
- [ ] P0: freeze V22 task packet
- [ ] P1: select ensemble and DE budget/seeds/stop rules

## T1 Engineering
- [x] I01: implement V22 DE gate harness (structured MC-DE wrapper)
- [x] I02: DE gate CLI + tests
- [x] I02b: implement SC-LDPC DE gate via V11 (`nonbinary_v22_sc_de_gate.py` + CLI + test)
- [ ] I03: finite construction if DE passes

## T2 Execute
- [x] E01: DE gate on V17 structured channel (q16+q1024 irregular smoke; q1024 SC-LDPC p=0.20/0.10/0.05 smoke; p=0.05 iter50 passes all 6 rows)
- [ ] E02: finite Bob-only FER / f_total

## T3 Verify/Closeout
- [ ] V01: Bob-only semantic verifier
- [ ] C01: docs/memory update
