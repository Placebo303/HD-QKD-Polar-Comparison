# OpenSpec Tasks: formal-ir-v38r1-posterior-binding-correction

**Lifecycle**: `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Execution**: no real decoder, DE, run_02, tuning, or seed search

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
