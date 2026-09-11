# D7-E provenance-safe cross-layer discriminator — tasks

> Operator authority: Track B R14 only (freeze before code). R15–R19
> (implementation, verifier, tests, reviews) are later gates, other owners.
> Zero decoder calls, zero Model-F content reads, zero roots, zero
> identifiers, zero push, zero commits beyond the single scoped R14 commit.

- [x] R14 — **Freeze before code (docs only, this change).** This change
  folder (`proposal.md`, `design.md`, `specs/`, `tasks.md`) freezing §§3–5
  in substance (R08–R13) plus the cycle directory
  `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/` with
  `D7_E_PREREG_R1.md` and `D7_E_EXECUTION_PACKET_R1.md` (frozen command
  NOT run, seven-file schema, test plan R17, review tokens R18/R19,
  authorization lifecycle, nonclaims; status
  `NOT_AUTHORIZED_NOT_EXECUTED`; no identifier) and `cycle_state.yaml`
  (D7-D keys adapted to D7-E; all authorization/promotion/decoder/result
  false; no identifier/root; predecessor D7-D acceptance). Single scoped
  commit `docs(d7-e): freeze provenance-safe cross-layer discriminator`.
- [ ] R15 — **Minimal implementation (later gate, not this change).**
  Preferred new files only; reuse accepted D7-C identity/model helpers and
  D5 BP-provenance/mixing helpers; lazy binding, DI, dry-run, unauthorized
  refusal, exact matrix order, transient q, fail-closed provenance,
  budgets, no-overwrite, read-only verify; seven scalar text files only.
- [ ] R16 — **Verifier (later gate).** Recompute from record scalars only;
  never loads Model-F or binds/calls decoder.
- [ ] R17 — **Tests (later gate).** Exact 192-slot dry-run order; both
  transfer formulas; corrected estimator identity + legacy-builder
  negative fixture; `CHECK_UPDATED` gate; refused provenance classes;
  source-exact-false eligibility; <12 coverage block; thresholds/terminal
  truth table; crash/nonfinite/resource/watchdog priority; scalar-only
  writer/no-overwrite/tamper; external-cwd import and decoder/loader
  sentinels; D7-C/D7-D independence; no production root read.
- [ ] R18 — **Implementation review (later gate).** Independent reviewer
  creates `D7_E_IMPLEMENTATION_REVIEW_R1.md`; verdict only
  `D7_E_IMPLEMENTATION_REVIEW_PASS` / `D7_E_IMPLEMENTATION_REVIEW_FAIL`.
- [ ] R19 — **Independent WSL Pre-EXECUTE (later gate).** Separate reviewer
  creates `D7_E_PRE_EXECUTE_REVIEW_R1.md`; required PASS token
  `D7_E_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`; grants
  nothing.

## Non-goals

- No R15 implementation, no R16 verifier, no R17 test run, no R18/R19
  reviews, no execution authorization, no D7-E run, no result acceptance
  in this change.
- No scientific/budget/terminal/schema change beyond the frozen R08–R13;
  no V35/D5/D6/D7-C edits; no R1d/G1/G2 work.
