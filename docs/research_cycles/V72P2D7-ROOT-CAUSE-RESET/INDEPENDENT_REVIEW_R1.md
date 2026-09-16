# D7 R1 independent review and authorized correction record

- Authority: `.workbuddy/tasks/D7_ROOT_CAUSE_AND_ROUTE_RESET_R1_TASK_PACKET.md` Phase F (F05) plus main-thread authorization 2026-09-13 (D7-F count-direction correction).
- Branch: `formal-ir-v72p1-addendum-clean`; HEAD `278fdf07` (no commit created by this cycle; nothing pushed).
- Operator return: `OPERATOR_RETURN_R1.md`, terminal `IMPLEMENTATION_CANDIDATE_AWAITING_INDEPENDENT_REVIEW`.
- Reviewers: independent sessions, separate context from the implementation operator.

## 1. Implementation review verdict: PASS-WITH-FINDINGS

Scope: A01–F05 acceptance IDs, scoped changed-file manifest, tests, claim ceiling, zero-production-execution boundary.

Confirmed:
- changed-file set matches the manifest exactly (D5 module +278/−33; new module/CLI/test; OpenSpec change; cycle docs; one decision-log entry; one memory entry);
- tests replayed with `.venv/bin/python -m pytest -p no:cacheprovider -q --basetemp=<fresh workspace root>`: new suite 36 passed; bp-provenance + decoder-certification + new 73 passed; `test_v72p2d5_gf32_rate_mother.py` 165 passed; `test_v72p2d5_model_f_input.py` 32 passed; `test_v72p2d6_gf32_graph_mother.py` 62 passed; `test_v72p2d7_gf32_alternating_discriminator.py` 32 passed; `py_compile` exit 0;
- zero production decoder/CAL/VAL calls; all executed test paths fake-injected; fresh `workspace/v72p2d7_r1_*` roots only; no formal or comparison output root written;
- historical evidence content-identical; no frozen-directory edit; no branch switch, commit, or push;
- same-input equivalence: `q` bitwise equal, syndromes/decoded targets/per-layer counters equal, L1/L2 priors within 6.9e-18..2.1e-17 versus frozen `atol=1e-12`, conditional on identical input priors (estimator difference outside scope).

Non-blocking findings (recorded for acceptance):
- A03 nit: cycle-state initial terminal present only as a YAML comment/doc header, not a machine field.
- B minor: `_load_v35_provenance_module` `.src.`-first import preference in the accepted D5 module is a behavior change not described in design; traced safe in the tested layouts.
- D minor: production reference-ladder bind (`bind_reference_ladder_decoders`) unexercised until X3.
- E minor: G2 evidence serialization lacks APP iteration totals; the None-RSS→BLOCKED rule is not stated in design §7.
- nits: unused `PER_CALL_WATCHDOG_S`; unreachable `SOURCE_CRASH` target branch; `*_decoded_target` aliases the counters.
- Pre-existing unrelated stale-world-state failures in D7-C/D/E/F/B/H suites reproduced; those files are unmodified by this change.
- Worktree not quiescent during review (concurrent external activity in `docs/v35-algorithm-development-report.md`); the scoped manifest remained reviewable.

## 2. Authorized correction (D7-F f=1.2 count direction)

- Finding: packet §4 stated "candidate-only 2, reference-only 0"; the immutable `workspace/d7_f_reverse_order_discriminator_b6d62184-fd15-483d-947e-01ea66ddc13c/stratum_summary.csv` stores `candidate_only=0, reference_only=2, both=0, neither=14`, consistent with `D7_F_PREREG_R1.md` §B05 and `D7_F_RESULT_ACCEPTANCE_R1.md`.
- Main thread authorized a scoped text-only correction on 2026-09-13; applied to six locations: `D7_F_CORRIGENDUM_R1.md`, `proposal.md`, `spec.md`, the decision-log R1 entry, the operator-return A04 line plus delta note, and packet §4 (original line preserved with a dated correction note).
- Focused independent re-verification verdict: PASS. Ground truth re-read; residual inverted-phrasing scan clean except the packet's intentionally preserved original line; historical artifacts, code, and tests untouched; no commit, no push.

## 3. Lifecycle

- `IMPLEMENTATION_REVIEWED_AND_CORRECTED_AWAITING_MAIN_THREAD_ACCEPTANCE`.
- Not accepted; no scientific promotion; X1–X4 and D7-H remain unauthorized; nothing pushed.
