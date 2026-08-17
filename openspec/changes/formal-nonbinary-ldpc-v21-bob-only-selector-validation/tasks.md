# Tasks: formal-nonbinary-ldpc-v21-bob-only-selector-validation

Status: STOP_GATE_TRIGGERED — Bob-only S0/S1/S2 FER all >=0.45 on 64 fresh frames; short-block branch frozen, V22 drafted.

## T0 Planning
- [ ] P0: freeze task packet (acceptance IDs)
- [ ] P1: pre-register seeds, frame counts, stop rules

## T1 Engineering
- [x] I01: implement `nonbinary_v21_bob_only.py` with S0/S1/S2
- [x] I02: implement CLI `run_v21_bob_only.py`
- [ ] I03: implement semantic verifier (Bob-only static + runtime injection) [static AST check added in tests]
- [x] I04: tests for S0/S1/S2 and verifier

## T2 Execute
- [x] E01: run fresh seeds n=64, 8 seeds x 8 frames
- [x] E02: record exact_correct / mismatch / coverage / rank / f_total (summary JSON)

## T3 Verify/Closeout
- [ ] V01: semantic verifier pass
- [ ] C01: update docs/memory
- [ ] C02: local commit only
