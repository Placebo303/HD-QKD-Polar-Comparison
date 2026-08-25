# OpenSpec Tasks: formal-ir-v38r1-posterior-binding-correction

**Lifecycle**: `IMPLEMENTATION_ACCEPTED / EXECUTE_AUTHORIZED`
**Execution**: one decoder-only `run_02` is explicitly authorized; no DE,
tuning, seed search, structural reselection, overwrite, or rerun

## Frozen implementation matrix

- [x] **R1-01** Record root cause, plan SHA `1b3fb4b8...`, accepted
  implementation `41cad74c...`, and invalid result `6a36914e...`.
- [x] **R1-02** Invalidate V38-P0 decoder evidence and
  `V38_NO_ROUTE_SIGNAL`; retain bounded 27/27 structural evidence only.
- [x] **R1-03** Set V38-P0 state to explicit invalid-result status while
  retaining historical `development_execution_authorized: true` and keeping
  formal execution and promotion false.
- [x] **R1-04** Apply the one-line complete-`bob` posterior binding correction.
- [x] **R1-05** Add the complete-Bob capture test with values greater than 31.
- [x] **R1-06** Add the fixed numerical wrong/correct posterior sentinel and
  V36 equality check.
- [x] **R1-07** Freeze decoder-only successor parameters, winner seeds, 45-call
  cap, additive run_02, and immutable invalid run_01.
- [x] **R1-08** Record that ignored local `v38_winning_matrices.npz` is not an
  authoritative input; future matrices must be reconstructed deterministically.
- [x] **R1-09** Keep lifecycle at implementation candidate and execution not
  authorized; independent ACCEPT and new user EXECUTE_AUTH remain required.
- [x] **R1-10** Run compile checks and targeted fake-runner tests; do not block
  on the complete Lane-A suite.
- [x] **R1-11** Final scoped diff/output checks completed; OpenSpec validation
  was attempted and is unavailable because the command is not installed.
- [x] **R1-12** Local coherent candidate commit is created; no push.
- [x] **R1-13** Freeze and implement the nine winner seed mapping.
- [x] **R1-14** Reconstruct exactly nine matrices from the committed run_01
  metrics JSON and strictly compare winner metrics, including Lane C
  permutations; do not use NPZ or 27-candidate search.
- [x] **R1-15** Implement default-deny `run_v38r1_development()` with exactly
  45 calls, frozen blocks/parameters, fake-runner support, and existing gates.
- [x] **R1-16** Add `scripts/execute_v38r1_development.py` with mandatory
  authorization flag, fixed additive run_02 writer, no-overwrite guard, and no
  NPZ output.
- [x] **R1-17** Add fake/monkeypatch tests for guard, nine reconstruction,
  fixed seeds, metric mismatch, NPZ independence, 45 calls, and writer guard.
- [x] **R1-18** Document the runner command, output files, and unchanged
  `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED` lifecycle.
- [x] **R1-19** Final targeted checks, diff/output audit, and successor
  candidate commit completed; no push and no production output.
- [x] **R1-20** Remove `--fake-runner` from the formal CLI, bind
  `fake_runner=False`, and test that the CLI cannot select the fake evaluator.
- [x] **R1-21** Set both run_02 summary lifecycle and execution status to
  `DEVELOPMENT_RESULT_CANDIDATE`, with a focused assertion.
- [x] **R1-22** Run one real decoder-free nine-winner reconstruction preflight
  against immutable run_01 metrics; record timing/result and verify no
  evaluator call, output write, run_01 diff, or run_02 creation.
- [x] **R1-23** Execute the separately authorized decoder-only development run
  exactly once, retain the five additive run_02 files, and complete the
  read-only 9/45/lane/seed/block/run_01 postcheck. Keep the result at
  `DEVELOPMENT_RESULT_CANDIDATE` pending independent result acceptance.
