# A2 — X2–X4 remediation authorization record R1

- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- Change: `formal-ir-d7-root-cause-and-route-reset`
- Authority: user authorization received in the main thread on 2026-09-13,
  supplementing `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md`
  and Addendum A1. This record does not replace either; every frozen command,
  input, root, ceiling, budget, provenance rule, terminal vocabulary, and STOP
  condition remains binding.

## 1. Verbatim user authorization

> 后续的X2-X4的实际运行如果首次失败，我给一次机会你修改，然后允许你运行第二次，和之前X1一样，但是最后要讲清楚你改了哪些，是否会对本次实际探索的目标造成一定影响

## 2. Scope

- Applies only to the real X2 / X3 / X4 attempts under the master packet.
- If a first attempt fails, the grant permits: one scoped
  implementation-level remediation, an independent review of that
  remediation, and then exactly one second attempt of the same phase.
- The second attempt runs with the unchanged frozen command, roots, budgets,
  selector/plan, and success/failure contract. No parameter is retuned.
- One remediation + one second attempt per phase, mirroring the X1 precedent
  (fixture root-cause fix, independent implementation review, one rerun).
- If the second attempt fails, if its remediation review fails, or if no safe
  implementation-level fix exists, the chain stops `BLOCKED`; no third
  attempt, no cleanup, no root replacement.
- Each attempt consumes its own grant: the phase flag is set true only
  immediately before the process start and restored false immediately after
  the attempt, regardless of outcome.
- The final return must state exactly what was changed and whether the change
  can affect the exploration goals: X2 graph sensitivity, X3 strong-reference
  diagnosis of X2 f=1.2 failures, X4 G2 length discrimination.

## 3. Hard limits on any remediation

A remediation must not change, replace, or reinterpret:

- matrices (graphs, graph seeds, block seeds, f values, rows, arms, blocks),
- the frozen selector and call plan, thresholds, or decoder budgets,
- the exact command literals, input roots, or output roots,
- provenance semantics, terminal vocabulary, or claim ceiling,
- historical evidence, Model-F input, or the frozen baseline.

A change that would alter any of the above is not an implementation-level
remediation; it is a scientific-contract change and is outside this grant
(chain stops `BLOCKED`, main-thread decision).

## 4. Current usage state

- X1: first attempt failed (unsatisfiable fixture); the user separately
  authorized a fixture-only fix, an independent implementation review
  (`X1_FIX_IMPLEMENTATION_REVIEW_R1.md`), and exactly one rerun
  (`X1_FIX_AND_RERUN_NOTE_R1.md` §3), and approved automatic continuation
  X2 -> X3 -> X4 after X1 verification, each phase gated by its own
  independent review. The X1 rerun succeeded and was independently verified
  (`X1_RERUN_VERIFICATION_REVIEW_R1.md`, `X1_RERUN_VERIFIED`).
- X2: completed on its first attempt, so this A2 remediation grant was not
  used for X2 (`GRAPH_SENSITIVITY_OBSERVED`, X2 Pre-RESULT review PASS).
- X3: not yet attempted at record creation; `x3_reference_ladder_authorized`
  false; this A2 grant is available for a first-attempt failure.
- X4: not yet attempted; `x4_g2_execution_authorized` false; this A2 grant is
  available for a first-attempt failure.

## 5. Recording

- The authorization trail above (X1 fix + rerun, auto-continuation X2–X4) is
  recorded here and referenced by `cycle_state.yaml`
  (`x1_rerun_authorization`, `x1_x4_authorization_granted`).
- Any X3/X4 remediation under this grant must be recorded as its own
  artifact, independently reviewed, and summarized in the corresponding
  operator return with an explicit statement of changed files and of any
  possible effect on the exploration goals.
