# Tasks: formal-nonbinary-ldpc-v21-bob-only-selector-validation

Status: **CONCLUDED_STOP_GATE_TRIGGERED_PENDING_ARCHIVE**

## T0 Planning

- [ ] P0: CANCELLED_NOT_PRE_FROZEN — acceptance IDs were not frozen before
  execution; closeout cannot retroactively satisfy this task.
- [ ] P1: CANCELLED_NOT_PRE_FROZEN — seeds/frame count/stop rule were recorded
  in planning material but not accepted as a complete pre-execution freeze.

## T1 Engineering

- [x] I01: implemented S0/S1/S2 in `nonbinary_v21_bob_only.py`.
- [x] I02: implemented CLI `run_v21_bob_only.py`.
- [ ] I03: PARTIAL_UNVERIFIED — static AST Alice-reference test exists;
  planned runtime Alice-injection semantic verifier was NOT_RUN.
- [x] I04: focused S0/S1/S2 tests ran; this does not close I03 or V01.

## T2 Execute

- [x] E01: executed 64 frames and retained S0/S1/S2 results.
- [x] E02: retained summary metrics: S0 24/64, S1 28/64, S2 28/64;
  FER 0.625/0.5625/0.5625.

## T3 Verify/Closeout

- [ ] V01: NOT_RUN_UNVERIFIED — no runtime Alice-injection independent
  semantic verification. AST coverage is not a substitute.
- [x] C01: CLOSEOUT_ACCEPTED — corrected docs/memory synchronized; independent
  read-only closeout review and memory triage ACCEPT.
- [ ] C02: PENDING_USER_AUTHORIZED_ARCHIVE — no archive action in this round.

Terminal rule: the observed stop gate remains concluded; missing verification
is preserved as a limitation and does not authorize rerun or promotion.
