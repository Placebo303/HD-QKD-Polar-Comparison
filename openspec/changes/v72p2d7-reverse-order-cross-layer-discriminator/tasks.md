# D7-F reverse-order cross-layer discriminator — tasks

> Operator authority: Phase B (freeze) only, per
> `.workbuddy/tasks/D7_E_ACCEPT_D7_F_REVERSE_ORDER_READINESS_R1_TASK_PACKET.md`
> §5. Docs only, zero decoder calls, zero Model-F content reads, zero
> roots, zero identifiers, zero push, zero commits beyond the scoped docs
> commit.

- [x] B-freeze — **Freeze before code (docs only, this change).** This
  change folder (`proposal.md`, `design.md`, `specs/`, `tasks.md`)
  freezing §5 in substance (B01–B07) plus the cycle directory
  `docs/research_cycles/V72P2D7-GF32-REVERSE-ORDER-DISCRIMINATOR/` with
  `D7_F_PREREG_R1.md` and `D7_F_EXECUTION_PACKET_R1.md` (frozen command
  NOT run, seven-file schema, test plan, review tokens, authorization
  lifecycle, nonclaims; status `NOT_AUTHORIZED_NOT_EXECUTED`; no
  identifier) and `cycle_state.yaml` (D7-E keys adapted to D7-F; all
  authorization/promotion/decoder/result false; no identifier/root;
  predecessor D7-E acceptance). Single scoped commit `docs(d7-f): freeze
  reverse-order cross-layer discriminator`.
- [ ] C-impl — **Minimal implementation (later gate).** New files only at
  the frozen paths (module, one test file, one thin script); reuse D7-E
  loaders/estimator/transfer/provenance/RSS/scalar/verifier conventions
  via narrow imports, no predecessor-module copies; lazy binding, DI,
  dry-run, unauthorized refusal, exact arm order, transient q, fail-closed
  provenance, budgets, no-overwrite, read-only verify; seven scalar text
  files only.
- [ ] D-tests — **Tests (later gate).** At minimum cover the packet §7
  list: exact 128-call matrix/order and cap; arm transitions and blocked
  non-calls; source exact not an eligibility gate; only exact
  `CHECK_UPDATED` transfers; each syndrome consumed once, no target
  feedback; both-layer exact truth table and syndrome isolation;
  paired-label boundaries and terminal priority; RSS boundaries/fail-closed
  behavior; scalar-only schema/forbidden payloads; writer/verifier tamper
  cases; protected-root/no-overwrite refusal; external-cwd
  decoder/loader sentinel; dry-run and unauthorized refusal; D7-E/BP
  provenance regression. Focused tests plus one milestone regression; no
  perf-v38 or scientific decoder.
- [ ] E-reviews — **Independent reviews (later gate).** Implementation
  verdict `D7_F_IMPLEMENTATION_REVIEW_PASS` or `...FAIL`, then fresh
  Pre-EXECUTE verdict
  `D7_F_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` or
  `...FAIL`. Neither grants authorization.

## Non-goals

- No execution authorization, no D7-F run, no result acceptance in this
  change.
- No scientific/budget/terminal/schema change beyond frozen B01–B07; no
  V35/D5/D6/D7-A/B/C/D/E edits; no R1d/G1/G2 work.
