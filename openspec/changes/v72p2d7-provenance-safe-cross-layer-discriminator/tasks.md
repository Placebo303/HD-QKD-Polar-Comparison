# D7-E provenance-safe cross-layer discriminator — tasks

> Operator authority: Track B R14 (freeze) through R19 (reviews) is
> complete per the evidence below; A1 command closeout is complete per the
> A04 PASS token below. Zero decoder calls, zero Model-F content reads, zero roots, zero
> identifiers, zero push, zero commits beyond the scoped docs commits.

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
- [x] R15 — **Minimal implementation (complete).** Preferred new files only; reuse accepted D7-C identity/model helpers and
  D5 BP-provenance/mixing helpers; lazy binding, DI, dry-run, unauthorized
  refusal, exact matrix order, transient q, fail-closed provenance,
  budgets, no-overwrite, read-only verify; seven scalar text files only.
  Evidence: commit `08590fba` (`feat(d7-e): implement
  provenance-safe cross-layer discriminator`, 3 files, +3356).
- [x] R16 — **Verifier (complete).** Recompute from record scalars only;
  never loads Model-F or binds/calls decoder. Evidence: `verify_root` in
  the R15 commit (`08590fba`).
- [x] R17 — **Tests (complete).** Exact 192-slot dry-run order; both
  transfer formulas; corrected estimator identity + legacy-builder
  negative fixture; `CHECK_UPDATED` gate; refused provenance classes;
  source-exact-false eligibility; <12 coverage block; thresholds/terminal
  truth table; crash/nonfinite/resource/watchdog priority; scalar-only
  writer/no-overwrite/tamper; external-cwd import and decoder/loader
  sentinels; D7-C/D7-D independence; no production root read. Evidence:
  25 tests in the R15 commit (`08590fba`).
- [x] R18 — **Implementation review (complete).** Independent reviewer
  created `D7_E_IMPLEMENTATION_REVIEW_R1.md`; verdict
  `D7_E_IMPLEMENTATION_REVIEW_PASS` (exact token, line 17 of that doc;
  recorded in commit `031deee7`).
- [x] R19 — **Independent WSL Pre-EXECUTE (complete).** Separate reviewer
  created `D7_E_PRE_EXECUTE_REVIEW_R1.md`; PASS token
  `D7_E_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` (line 13
  of that doc; recorded in commit `031deee7`); grants nothing.
- [x] A1 — **Venv command closeout (complete).** Superseded only
  the frozen-command interpreter spelling to `.venv/bin/python` (prereg
  §4, execution packet, addendum
  `D7_E_EXECUTION_PACKET_ADDENDUM_VENV_A1.md`) and passed the independent
  A1 review (A04): `D7_E_PRE_EXECUTE_REVIEW_PASS_VENV_A1_AWAITING_EXPLICIT_AUTHORIZATION`.

## Non-goals

- R15–R19 are complete with the evidence above. No execution
  authorization, no D7-E run, no result acceptance in this change.
- No scientific/budget/terminal/schema change beyond the frozen R08–R13;
  no V35/D5/D6/D7-C edits; no R1d/G1/G2 work.
