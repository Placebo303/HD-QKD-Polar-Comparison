# OpenSpec Tasks: formal-ir-v42-conditional-realism-diagnostic

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Execution status**: nothing below is started or authorized. No task may
start before independent plan ACCEPT (design D13/O1 is RESOLVED — Candidate A
frozen as `cond_estimated_l1` by user adjudication 2026-08-26); no task in
this change may run a production decoder until a new explicit user
`EXECUTE_AUTH` bound to the accepted implementation SHA exists. (V41P0 run_01
evidence stands as recorded - terminal `V41_C_ONLY_RETAINED`; that terminal
authorizes nothing by itself.)

## Phase A — implementation candidate (after plan acceptance; O1 adjudicated 2026-08-26)

- [ ] **A1** Create module
      `comparison_bench/src/comparison_bench/formal_ir/v42_conditional_realism_diagnostic.py`
      with the composed dual-condition path per design Section 6/D15 (accepted
      v35 primitives + v38 reconstruction helpers only); NO import of the
      v39/v40/v41 modules (pattern copy only); no modification to any existing
      module; injectable `decode_fn` defaulting to the accepted decoder.
- [ ] **A2** Freeze constants: the 9 new block seeds (390110-390112 /
      390210-390212 / 390310-390312); FORBIDDEN seed union as copied data
      (V36_A3 ∪ V39 ∪ V40-probe ∪ V41-confirm, 42 seeds); the three lane_c
      ordinal-2 representative matrix ids (design Section 5); frozen workload
      C01-C18 in exact order with condition labels (Section 4); condition
      names (`cond_oracle`, `cond_estimated_l1`) and the frozen mechanism id
      (Candidate A, adjudicated 2026-08-26); decoder contract 90/1.0 poly 37
      (Section 6); budget hard cap 18 shared across arms; output root and
      minimal file set (Section 14); terminal names/reasons incl. the ACCEPTED
      fifth terminal `V42_ANOMALOUS_INVERSION` (Section 9); master stop rule
      verbatim; claim boundary; statistics note.
- [ ] **A3** Implement the frozen `cond_estimated_l1` MAP-L1 estimator
      (Candidate A, verbatim definition of design Section 7) as a pure
      function with public-inputs-only signature plus the Layer-1 accuracy
      diagnostic computation; mechanism identity asserted against the frozen
      constant.
- [ ] **A4** Seed-registry validator: no duplicates among the nine;
      mechanical disjointness vs the FOUR-family forbidden union (incl. V41);
      exactly three per source (J2).
- [ ] **A5** Deterministic reconstruction of the 3 unique matrices with strict
      comparison against the committed structural authority incl. Lane C
      `position_permutations`; representative identities equal to frozen
      constants; decoder-free, write-free (J3); counts shape/loading via the
      accepted loader for all three sources (J4).
- [ ] **A6** Dual posterior-binding preflight on 390110/390210/390310: six
      oracle sentinels + four estimated-L1-arm sentinels of design Section 11,
      including spy-captured carrier identity and arms-differ (J5);
      decoder-free, write-free.
- [ ] **A7** Guarded runner ordering (tiers per design Section 11): Tier 0
      refusal-class guards FIRST with NOTHING created on failure — default
      deny, mandatory `--execution-authorized`, exact-equality SHA preflight
      of HEAD AND `origin/formal-ir-mainline`, scoped tracked-dirty over (v42
      module, v42 CLI, v38 module, v35 module) (J1), output-root-already-
      exists refusal (J7) — non-zero exit, ZERO calls; THEN Tier 1 scientific
      preflights A4-A6; preflight failure -> create root + invalid notice +
      empty records + summary (terminal EVIDENCE_INVALID, planned 18, started
      0, completed 0, no aggregation), ZERO real calls, stop, no rerun (D9);
      success -> create root after all guards/preflights pass, before the
      first decoder call.
- [ ] **A8** Dual-condition decode loop in frozen order C01-C18: one shared
      deterministic sample per block passed to both arms; per-call record
      emission (schema design Section 12); pairing completeness — each block
      exactly once per condition — plus the STRICT per-pair cross-arm
      `errors_initial` equality gate (revised D14/J6): both arms'
      `errors_initial` must be strictly equal, checked BEFORE the pair's
      decode calls; inequality -> `V42_EVIDENCE_INVALID` with zero decoder
      calls when present at the first pair; the per-pair
      `pairing_errors_initial_equal` field still recorded as informational
      redundancy; cross-condition outcome differences never treated as
      failures; decoder-parameter assertions (J9); hard cap 18 SHARED across arms
      with structural refusal of call 19 (J10); workload/order assertion
      (J12); Tier 2 mid-run `BaseException`: retain raw partial records
      byte-for-byte + notice + summary with started/completed actuals +
      failure marker only, then re-raise.
- [ ] **A9** Aggregates and terminal machine: per-condition aggregates
      (`exact_total`, per-source counts, wrong counts); per-source aggregates;
      per-block paired outcomes + errors_final deltas;
      `l1_map_accuracy_by_source`; BOTH arms' gate evaluations (G1' >= 7/9,
      G2' >= 2/3 per source, G3' arm wrong = 0); total/disjoint terminal
      machine rules 0-4 over (pass_oracle, pass_estimated_l1) with arm-local
      wrong semantics only — `stopped_for_analysis` markers,
      `oracle_arm_wrong_codeword_anomaly` flag, no global wrong rule, no
      cross-arm veto — plus `terminal_reason` and routing trace.
- [ ] **A10** Additive writer: exact file set of design Section 14, CSV/JSON
      parity, no-NPZ-output enforcement, summary contents per design Section
      12 with gate details ordered AFTER terminal determination, verbatim stop
      rule, claim boundary, statistics note, provenance incl. O1 mechanism id;
      invalid-notice path.
- [ ] **A11** Add `scripts/execute_v42_conditional_realism_diagnostic.py`:
      default deny, mandatory flags, binding `fake_runner=False`, no
      fake-runner CLI option, non-zero exit with zero calls and NOTHING created
      on any guard failure.
- [ ] **A12** Bind predecessor constants from committed evidence at
      implementation freeze: V41 accepted plan SHA, V41 execution SHA
      (`6d75e754899e8470445c2bf58f2f4ff84130fc33`), structural authority
      identity, V25 counts provenance.

## Phase B — focused tests (fake runners/decode_fn only; zero production decode)

- [ ] **T1** Seed-registry validator rejects duplicates, wrong shape, and each
      overlapping family separately (V36_A3 range, V39 range, V40 probe seeds
      390106/390206/390306, V41 seeds 390107-109/390207-209/390307-309);
      accepts the frozen nine.
- [ ] **T2** Reconstruction match logic detects injected metric drift (incl.
      `position_permutations`) -> J-path; two reconstructions identical;
      representative identity mismatch -> J-path.
- [ ] **T3** Sentinel tests: all six oracle conditions incl. 1e-6 max-abs and
      argmax divergence; tampered `u2_bob` substitution detected by
      captured_equals_bob; non-oracle estimator rejects an injected
      alice-dependent variant (public-inputs contract); carrier_identity spy
      detects a substituted estimated-l1 prior; arms_differ fails -> J5 when
      priors are identical; l1 accuracy bounds enforced.
- [ ] **T4** Pairing consistency: same-seed resample identity (idx/alice/bob
      identical when re-derived; sample computed once and shared); missing or
      duplicated block-condition combination -> J6/J12; J6 strict-gate
      injection: tampering ONE arm's `errors_initial` -> J6 ->
      `V42_EVIDENCE_INVALID` with ZERO decoder calls (the strict pair-equality
      gate fires before the pair's decode calls); the per-pair
      `pairing_errors_initial_equal` field still reported; a cross-condition
      outcome difference is NOT flagged as integrity failure.
- [ ] **T5** Truth-table test: enumerate integrity ok/failed x
      (oracle_pass, estimated_l1_pass) over {TT both_pass, TF oracle_only,
      FT estimated_only(ANOMALOUS), FF both_fail}; each lands in EXACTLY ONE
      terminal per design Section 9 rules 0-4; EVIDENCE_INVALID has first
      precedence; FT lands in the ACCEPTED `V42_ANOMALOUS_INVERSION`.
      Exhaustive and mutually exclusive.
- [ ] **T6** Wrong-codeword three cases (never counted as exact anywhere):
      (i) oracle-arm injection -> oracle arm fails own G3',
      `oracle_arm_wrong_codeword_anomaly = true` prominent,
      `stopped_for_analysis[cond_oracle] = true`, other arm unaffected,
      terminal follows remaining combination; (ii) estimated-l1-arm injection ->
      symmetric without anomaly flag; (iii) both arms injected -> both G3'
      fail -> GO_STRUCTURE with both stopped_for_analysis markers. No
      cross-arm veto in any direction.
- [ ] **T7** Budget cap: structural refusal of the 19th call (J10) in fake
      mode; accounting planned/started/completed actuals consistent.
- [ ] **T8** Scientific-preflight failure path: each of J2/J3/J4/J5 injected
      -> additive root created with the three-piece evidence set (invalid
      notice, empty records, summary with planned 18 / started 0 / completed
      0, no aggregation, terminal EVIDENCE_INVALID) and ZERO decoder calls.
- [ ] **T9** Partial retention: injected mid-run `BaseException` -> raw
      partial records retained byte-for-byte inside the pre-created root,
      started/completed actuals recorded, failure marker present, no
      performance aggregate/gate evaluation/terminal beyond the marker, then
      re-raise observed.
- [ ] **T10** CLI guards: missing flag(s) -> non-zero exit, zero calls,
      nothing created; target SHA differing from HEAD OR from origin branch
      -> refuse; scoped tracked-dirty injection over any of the four files
      -> refuse (J1); pre-existing output root -> refuse with nothing created
      (J7, Tier 0).
- [ ] **T11** Record schema completeness incl. derived `wrong_codeword` and
      `condition`; decoder-parameter assertions: poly 37, setting 90/1.0 on
      every record, no warm-start parameter in the call path (J9 injection);
      oracle selector equals true u1_alice and estimated-l1 selector equals
      the frozen `cond_estimated_l1` MAP-L1 output (`u1_hat`) on fixture
      inputs.
- [ ] **T12** Writer contract: file-set exactness, CSV/JSON row parity,
      overwrite fail-closed (existing root refused, J7), no NPZ written,
      summary contains planned/completed/started actuals, l1_map diagnostics,
      per-arm and per-source aggregates, paired outcomes, both gate details
      ordered after terminal, stopped_for_analysis/anomaly fields, verbatim
      stop rule, claim boundary.

## Phase C — preflight (decoder-free, before any authorization request)

- [ ] **P1** Reconstruct the three matrices; strict metric match vs committed
      structural authority incl. permutations; verify zero evaluator calls and
      zero writes.
- [ ] **P2** Run dual posterior-binding preflight on 390110/390210/390310;
      report PASS/BLOCKED only.
- [ ] **P3** Mechanically verify J2 against copied four-family registries
      (zero overlap, no duplicates, 3-per-source shape) and confirm output
      root absent; report PASS/BLOCKED only.

## Phase D — authorized diagnostic execution (requires EXECUTE_AUTH)

- [ ] **D1** Main thread obtains an independent plan review verdict, explicit
      user D13 adjudication, and an explicit user `EXECUTE_AUTH` bound to
      repository, branch, full implementation SHA, cycle V42P0, scope
      `v42_diagnostic_18_calls_exactly_once`.
- [ ] **D2** Run exactly once:
      `python scripts/execute_v42_conditional_realism_diagnostic.py --execution-authorized --authorized-target-sha <sha>`;
      retain additive run_01 files; on error/partial state stop, retain raw
      partial records byte-for-byte without performance aggregates, return
      blocker; no rerun, resume, repair, tuning, block addition, or seed/
      mechanism change; NO second diagnostic round under any outcome.
- [ ] **D3** Read-only postcheck: accounting (18 planned / 18 completed /
      18 started unless integrity-stopped), record count and order C01-C18
      with correct pairing, no NPZ written, V38-V41 outputs byte-identical,
      summary completeness, independent recomputation of gates and terminal.

## Phase E — result review

- [ ] **E1** Write OPERATOR_RETURN.md and DEVELOPMENT_RESULT.md candidate;
      lifecycle stays result-candidate; include terminal state, routing trace,
      per-condition/per-source aggregates, paired outcomes, gate details, L1
      MAP accuracy context, and the bounded directional attribution (dual pass
      / upstream bottleneck / GO structure / anomalous inversion) strictly
      within the claim boundary.
- [ ] **E2** Independent recomputation of signals/machine/terminal by the main
      thread or reviewer; verdict copied into REVIEW_VERDICT.md.
- [ ] **E3** Memory triage as a separate milestone (this planning round is
      forbidden from editing AGENT_PROJECT_MEMORY.md).

## Explicitly forbidden during this change

Implementing before plan acceptance AND before D13 (O1) user adjudication;
choosing or altering the non-oracle mechanism at implementation time; running
any production decoder outside authorized Phase D or any
longrun/minrerun/routeA script; touching V35/V38/V39/V40/V41 code/tests/docs/
outputs, AGENT_PROJECT_MEMORY.md, existing OpenSpec changes, constructors,
loaders, evaluators, decoders, results/, or any official output root;
importing the v39/v40/v41 modules; reading any NPZ except read-only V25
`channel_counts.npz` via the accepted loader; writing ANY NPZ; reusing
prior-cycle blocks (360101-360105 family, 390101-390309) as diagnostic
samples; counting wrong codewords as exact recoveries; framing results as
condition/lanes superiority or any comparative ranking; FER/threshold/SKR/
security/qualification/promotion/real-frame claims; adding blocks or seeds
after results; revising thresholds or the mechanism after results; rerunning,
resuming, or compensating a partial run; starting a second diagnostic round
under any outcome; tuning decoder parameters under any outcome; treating
cross-condition outcome differences as integrity failures; self-acceptance;
automatic successor start.
