# V28R archive note

Archived 2026-08-20 after main-thread independent acceptance.

- The historical V28 `run_01` and its original `ACCEPT` are retained as
  superseded evidence and are `superseded_invalid_for_v29`. They must not be
  used as the V29 predecessor: the old row-prefix/identity construction did
  not satisfy the repaired degree-two contract.
- V28R `run_02_v28r` is the canonical engineering evidence. Its read-only
  verifier is `ok=true` and its terminal is
  `engineering_ready_for_retrospective_gate`.
- V28R is an engineering smoke gate only. It is not a finite FER result,
  qualification, promotion, or production claim. V29 is the separate frozen
  retrospective finite-code gate.

No code, tests, or comparison output was changed by this closeout.
