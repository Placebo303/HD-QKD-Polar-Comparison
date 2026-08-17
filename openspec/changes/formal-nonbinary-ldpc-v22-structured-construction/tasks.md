# Tasks: formal-nonbinary-ldpc-v22-structured-construction

Status: DE_NOT_READY — structured target-rate DE does not converge with current SC/plain tools; frozen as scientific_not_ready pending MET/protograph

## T0 Planning
- [x] P0: freeze V22 task packet (approach: additive V22b structured MC-DE with configurable DEGREE_MAX, then SC-LDPC structured adaptation)
- [x] P1: select ensemble and DE budget/seeds/stop rules (V10 S1/S3 + V11 G1/G2/G3; q1024; n_samples=100; max_iter=50; p scan 0.05-0.20; stop on any pass at target f)

## T1 Engineering
- [x] I01: implement V22 DE gate harness (structured MC-DE wrapper)
- [x] I02: DE gate CLI + tests
- [x] I02b: implement SC-LDPC DE gate via V11 (`nonbinary_v22_sc_de_gate.py` + CLI + test)
- [ ] I03: finite construction if DE passes (blocked: DE not ready)
- [x] I04: implement additive V22b structured MC-DE with configurable DEGREE_MAX (>=128) to unblock high-rate DE

## T2 Execute
- [x] E01: DE gate on V17 structured channel (q16+q1024 irregular smoke; q1024 SC-LDPC p=0.05 pass; q1024 structured r0.70 non-converged; q1024 r0.9375 runs via V22b degree_max=512, non-converged at iter10 and iter30/n200)
- [ ] E02: finite Bob-only FER / f_total

## T3 Verify/Closeout
- [ ] V01: Bob-only semantic verifier
- [ ] C01: docs/memory update
