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

## A2 — RSS telemetry rework (complete; telemetry-only, no execution)

> Authority: `.workbuddy/tasks/D7_E_RSS_TELEMETRY_REWORK_VENV_A2_TASK_PACKET.md`
> §§5–7. Telemetry/environment compatibility correction only: `.venv/bin/python`,
> the exact frozen command, all scientific constants, and the strict `<2GiB`
> threshold are preserved. The renewed Pre-EXECUTE review becomes stale until
> A2 implementation review + fresh E09 pass.

- [x] A2-01 — **VmHWM parser (complete).** Pure parser over `/proc/self/status`-equivalent
  text: exactly one ASCII `VmHWM: <positive integer> kB` line yields bytes
  (`value * 1024`); all other cases yield `None`. Evidence: `parse_vmhwm_rss_bytes`
  in implementation `9e09538` (frozen delta `becf60f`); T5 review §1 PASS.
- [x] A2-02 — **File-read wrapper (complete).** Production Linux/WSL read opens
  `/proc/self/status` once per probe call; no subprocess/shell/psutil/
  caching/retries/averaging/polling/env-switch/provider abstraction; legacy
  `_read_ru_maxrss` deleted (zero `ru_maxrss` references in module and runner).
  Evidence: implementation `9e09538`; T5 review §2 PASS.
- [x] A2-03 — **Deterministic tests (complete).** Injected-text fixtures covering valid
  conversion, missing/duplicate/malformed/decimal/signed/zero/negative/
  wrong-unit/non-ASCII/overflow (>18-digit) rejection, read failure, and
  bogus-`ru_maxrss` independence (`_read_ru_maxrss` not called on the WSL path).
  Evidence: 15 `test_a2_*` tests in `9e09538` (focused 15 passed; full D7-E file
  40 passed); T5 review §6 PASS.
- [x] A2-04 — **Threshold boundaries (complete).** Below-limit permits the existing path;
  equal-to and above 2 GiB block; `None` blocks before the first scientific
  decoder attempt and preserves existing resource-terminal behavior mid-run.
  Evidence: `RSS_LIMIT_BYTES == 2147483648`, strict `<2GiB`, `bytes=value*1024`
  exact in `9e09538`; T5 review §§3–4 PASS.
- [x] A2-05 — **Schema invariance (complete).** Writers/verifier retain the same
  `rss_bytes` schema; no new output field or schema revision. Evidence:
  `RECORD_FIELDS` byte-identical to `becf60f` baseline; T5 review §4 PASS.
- [x] A2-06 — **Implementation review (complete).** Independent read-only review with the
  unique verdict `D7_E_RSS_TELEMETRY_REWORK_REVIEW_PASS_A2` (no `..._FAIL_A2`;
  FAIL would have meant STOP). Evidence:
  `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/D7_E_RSS_TELEMETRY_REWORK_REVIEW_A2.md`.
- [x] A2-07 — **Renewed Pre-EXECUTE with single live E09 (complete).** Only after A2-06
  PASS: ordinary D7-E Pre-EXECUTE checklist plus exactly one fresh live E09
  (`.venv/bin/python`; positive finite `<2GiB`; raw `VmHWM` line captured);
  no repeat-until-pass. Evidence: verdict
  `D7_E_PRE_EXECUTE_REVIEW_PASS_VENV_RSS_A2_AWAITING_FRESH_EXPLICIT_AUTHORIZATION`
  in `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/D7_E_PRE_EXECUTE_REVIEW_VENV_RSS_A2.md`;
  single live E09 `VmHWM 96484 kB → 98803712 B` (`96484*1024` exact).
- [x] A2-08 — **Closeout (complete).** For dual PASS only: mark A2 tasks complete with
  evidence, update state to
  `D7_E_WSL_RSS_READY_AWAITING_FRESH_EXPLICIT_AUTHORIZATION`, leave every
  authorization false and attempts/completed zero, scoped local commit, no push.
  Evidence: this T7 closeout commit `docs(d7-e): record RSS A2 reviews and readiness closeout`;
  no execution consumed; prior authorization not reusable.
