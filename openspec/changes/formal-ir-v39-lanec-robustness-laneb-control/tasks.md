# OpenSpec Tasks: formal-ir-v39-lanec-robustness-laneb-control

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Execution status**: nothing below is started or authorized. No task in this
change may run a production decoder until an independent plan ACCEPT and a new
explicit user `EXECUTE_AUTH` bound to the accepted implementation SHA exist.

## Phase A — implementation candidate (after plan acceptance)

- [ ] **A1** Create module
      `comparison_bench/src/comparison_bench/formal_ir/v39_lanec_robustness_laneb_control.py`
      reusing accepted constructors/evaluator/loaders per design Section 16;
      no modification to any existing module.
- [ ] **A2** Freeze constants: seed registries (Section 2), new block seeds
      (Section 4), decoder contract (Section 6), output root and file set
      (design Section 15).
- [ ] **A3** Implement 18-matrix deterministic reconstruction with strict
      comparison against the committed 27-record run_01 structural JSON
      (lanes b/c subset), including Lane C `position_permutations`; NPZ must
      not be read.
- [ ] **A4** Implement block registry validator (exact seeds, no duplicates,
      no overlap with V36 seeds) and record-schema validator.
- [ ] **A5** Implement posterior-binding preflight checks P-BIND-1/2/3
      (decoder-free, write-free).
- [ ] **A6** Implement the guarded runner: default-deny authorization,
      exactly 45 + 45 + 15 = 105 real calls, one baseline call per block,
      join-based comparisons, no warm start, fail-closed behavior on any
      integrity failure with `v39_invalid_notice.json`.
- [ ] **A7** Implement aggregation levels 1-7, gates C1/B1/CB/BASE, terminal
      machine with integrity-first precedence, Wilson/McNemar descriptive
      helpers.
- [ ] **A8** Implement additive writer: exact file set of design Section 15,
      CSV/JSON parity, no NPZ output, fail-closed overwrite guard.
- [ ] **A9** Add `scripts/execute_v39_development.py` with mandatory
      `--development-execution-authorized`, no fake-runner option, binding
      `fake_runner=False`.

## Phase B — focused tests (fake runners only; zero production decode)

- [ ] **T1** Constructor determinism: two reconstructions of all 18 matrices
      are identical; shapes/ranks match registry.
- [ ] **T2** Reconstruction match logic detects an injected one-digit metric
      drift (I1 path).
- [ ] **T3** Block registry rejects duplicate/missing/V36-overlapping seeds
      (I3 path).
- [ ] **T4** Posterior capture test: forwarded second argument equals complete
      `bob`; probe blocks include Bob values > 31.
- [ ] **T5** Posterior sentinel: complete-bob prior differs from `u2_bob`
      prior; corrected path equals V36-style call element-for-element.
- [ ] **T6** Baseline dedup: exactly 15 baseline calls in fake mode; joins map
      every lane record to the unique same-block baseline record; tripling
      baseline observations fails.
- [ ] **T7** Call accounting: exactly 105 evaluator invocations in fake mode;
      cell counts 45/45/15.
- [ ] **T8** Record schema completeness incl. derived `wrong_codeword`.
- [ ] **T9-T11** Gate unit tests C1/B1/CB/BASE on synthetic aggregates,
      including boundary values (36/45, 12/15, +5, discordance, medians) and
      failure branches.
- [ ] **T12** Terminal-machine table-driven tests for all six states plus the
      BASE-C-fail edge case and EVIDENCE_INVALID precedence.
- [ ] **T13** Wilson interval and McNemar exact helpers against hand-computed
      fixtures.
- [ ] **T14** Writer contract: file-set exactness, CSV/JSON row parity,
      overwrite guard, absence of NPZ.
- [ ] **T15** CLI guards: missing flag -> non-zero exit and zero calls; CLI
      exposes no fake-runner option.
- [ ] **T16** Integrity injection: each of I1-I11 triggers
      `V39_EVIDENCE_INVALID` + invalid notice without performance output.
- [ ] **T17** Pairing completeness: exactly 45 C/B pairs and full baseline
      joins at both ordinal and source level.
- [ ] **T18** Frozen-parameter assertions: max_iter=30, damping_alpha=1.0,
      polynomial 37; no warm-start parameter exists in the call path.

## Phase C — preflight (decoder-free, before any authorization request)

- [ ] **P1** Reconstruct 18/18 matrices; strict metric match vs run_01 JSON;
      record timing; verify zero evaluator calls and zero writes.
- [ ] **P2** Run posterior-binding preflight P-BIND-1/2/3 on probe blocks
      390101 / 390201 / 390301.
- [ ] **P3** Verify V31 loader returns three expected-shape matrices; verify
      output root absent; report PASS/BLOCKED only.

## Phase D — authorized development execution (requires EXECUTE_AUTH)

- [ ] **D1** Main thread obtains independent plan review verdict and explicit
      user `EXECUTE_AUTH` bound to repo, branch, full target SHA, cycle
      V39P0, scope `v39_decoder_only_105_calls_exactly_once`.
- [ ] **D2** Run exactly once:
      `python scripts/execute_v39_development.py --development-execution-authorized`;
      retain additive run_01 files; on error/partial state stop, retain
      unchanged, return blocker; no rerun, repair, tuning, or seed change.
- [ ] **D3** Read-only postcheck: 105-call accounting, 90 lane records, 15
      baseline records, pairing completeness, run-root immutability of V38
      outputs, absence of NPZ.

## Phase E — result review

- [ ] **E1** Write OPERATOR_RETURN.md and DEVELOPMENT_RESULT.md candidate;
      lifecycle stays `DEVELOPMENT_RESULT_CANDIDATE`.
- [ ] **E2** Independent recomputation of aggregates/gates/terminal by the
      main thread or reviewer; copy verdict into REVIEW_VERDICT.md.
- [ ] **E3** Memory triage as a separate milestone (this planning round is
      forbidden from editing AGENT_PROJECT_MEMORY.md).

## Explicitly forbidden during this change

Implementing before plan acceptance; running any production decoder; touching
V38/V38R1 code/tests/docs/outputs, AGENT_PROJECT_MEMORY.md, existing OpenSpec
changes, decoder, constructors, results/run_01/run_02; writing any NPZ; adding
seeds after results; revising thresholds after results; self-acceptance;
automatic successor start.
