# OpenSpec Tasks: formal-ir-v41-fresh-block-confirm

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Execution status**: nothing below is started or authorized. No task in this
change may run a production decoder until an independent plan ACCEPT and a new
explicit user `EXECUTE_AUTH` bound to the accepted implementation SHA exist.
(V40P0 run_01 evidence stands ACCEPTED - terminal
`V40_PROBE_CONFIRM_ALLOWED`, result SHA
`a546d43c74be5f11e87426ff7ce837b31dd20142`, execution SHA
`80d605489f1f65eefd091625134514e8a09902de`; that terminal authorizes nothing
by itself.)

## Phase A — implementation candidate (after plan acceptance)

- [ ] **A1** Create module
      `comparison_bench/src/comparison_bench/formal_ir/v41_fresh_block_confirm.py`
      reusing accepted v38 constructors/evaluator and v35 loaders per design
      Section 14; NO import of the v39 or v40 modules (pattern copy only);
      no modification to any existing module.
- [ ] **A2** Freeze constants: the 9 new block seeds
      (390107-390109 / 390207-390209 / 390307-390309); FORBIDDEN seed union
      as copied data (V36_A3 360101-360105/360201-360205/360301-360305 ∪ V39
      390101-390105/390201-390205/390301-390305 ∪ V40 probe
      390106/390206/390306); the six ordinal-2 representative matrix ids
      (design Section 5); the frozen workload C01-C18 in exact order (Section
      4); decoder contract 90/1.0, poly 37 (Section 6); budget hard cap 18;
      output root and minimal file set (Section 13); terminal names/reasons
      (Section 8).
- [ ] **A3** Implement the seed-registry validator: no duplicates among the
      nine; mechanical disjointness vs the FORBIDDEN union; exactly three per
      source (J2).
- [ ] **A4** Implement deterministic reconstruction of the 6 unique matrices
      with strict comparison against the committed structural authority incl.
      Lane C `position_permutations`; representative identities must equal the
      frozen constants; decoder-free, write-free (J3); counts shape/loading
      check via the accepted loader for all three sources (J4).
- [ ] **A5** Implement posterior-binding preflight on 390107/390207/390307
      with the six sentinels of design Section 10 (decoder-free,
      write-free) (J5).
- [ ] **A6** Implement the guarded runner ordering (tiers per design Section
      10): Tier 0 refusal-class guards FIRST with NOTHING created on failure
      — default deny, mandatory `--execution-authorized`, exact-equality SHA
      preflight of HEAD AND `origin/formal-ir-mainline`, scoped tracked-dirty
      over (v41 module, v41 CLI, v38 module, v35 module) (J1), and
      output-root-already-exists refusal (J7) — non-zero exit, ZERO calls;
      THEN Tier 1 scientific preflights A3-A5; preflight failure -> create
      root + invalid notice + empty records + summary (terminal
      EVIDENCE_INVALID, planned 18, started 0, completed 0, no aggregation),
      ZERO real calls, stop, no rerun (D9); success -> create root after all
      guards/preflights pass, before the first decoder call.
- [ ] **A7** Implement the decode loop in frozen order C01-C18 with per-call
      record emission (schema Section 11), cross-lane `errors_initial`
      equality per block (J6), decoder-parameter assertions (J9), hard cap 18
      with structural refusal of call 19 (J10), workload/order assertion
      (J12), and Tier 2 mid-run `BaseException` handling: retain raw partial
      records byte-for-byte + notice + summary with started/completed actuals
      and failure marker only, then re-raise.
- [ ] **A8** Implement aggregates (per-lane `exact_total` / per-source counts
      / wrong counts), BOTH lanes' gate evaluations (G1 >= 7/9, G2 >= 2/3 per
      source, G3 that lane's wrong = 0), routing trace, and the total/disjoint
      terminal machine of design Section 8 rules 0-4 over
      (lane_c_pass, lane_b_pass) with lane-local wrong semantics only - no
      global wrong rule, no cross-lane veto - and `terminal_reason`.
- [ ] **A9** Implement additive writer: exact file set of Section 13,
      CSV/JSON parity, no-NPZ-output enforcement, summary contents per
      Section 11 (accounting actuals, per-lane/per-source aggregates, gate
      details AFTER terminal determination, routing trace, terminal state +
      reason, verbatim master stop rule, claim boundary, statistics note,
      provenance SHAs); invalid-notice path.
- [ ] **A10** Add `scripts/execute_v41_fresh_block_confirm.py`: default deny,
      mandatory flags, binding `fake_runner=False`, no fake-runner CLI option,
      non-zero exit with zero calls and NOTHING created on any guard failure.

## Phase B — focused tests (fake runners only; zero production decode)

- [ ] **T1** Seed-registry validator rejects duplicates, wrong shape, and each
      overlapping family separately (V36_A3 range, V39 range, V40 probe seeds
      390106/390206/390306); accepts the frozen nine.
- [ ] **T2** Reconstruction match logic detects injected metric drift (incl.
      `position_permutations`) -> J-path; two reconstructions identical;
      representative identity mismatch -> J-path.
- [ ] **T3** Posterior sentinel tests: all six fixed conditions incl. 1e-6
      max-abs and argmax divergence; tampered `u2_bob` substitution detected
      by captured_equals_bob.
- [ ] **T4** Gate boundaries on synthetic aggregates: overall 6/9 fails G1,
      7/9 passes; any source at 1/3 fails G2 while 2/3 passes; a lane with
      one wrong codeword fails its own G3 even at 9/9 exact.
- [ ] **T5** Truth-table test: enumerate integrity ok/failed x
      (lane_c_pass, lane_b_pass) over {TT, TF, FT, FF}; each lands in EXACTLY
      ONE terminal per design Section 8 rules 0-4; EVIDENCE_INVALID has first
      precedence. Exhaustive and mutually exclusive.
- [ ] **T6** Wrong-codeword lane-locality: inject a single wrong codeword on
      Lane C while Lane B fully passes its gates -> V41_B_ONLY_RETAINED
      reachable and lane_c judged FAIL via its own G3; symmetric injection on
      Lane B -> V41_C_ONLY_RETAINED and lane_b judged FAIL. No cross-lane
      veto in either direction.
- [ ] **T7** Budget cap: structural refusal of the 19th call (J10) in fake
      mode.
- [ ] **T8** Scientific-preflight failure path: each of J2/J3/J4/J5 injected ->
      additive root created with the three-piece evidence set (invalid notice,
      empty records, summary with planned 18 / started 0 / completed 0, no
      aggregation, terminal EVIDENCE_INVALID) and ZERO decoder calls.
- [ ] **T9** Partial retention: injected mid-run `BaseException` -> raw
      partial records retained byte-for-byte inside the pre-created root,
      started/completed actuals recorded, failure marker present, no
      performance aggregate/gate evaluation/terminal beyond the marker, then
      re-raise observed.
- [ ] **T10** CLI three guards: missing flag(s) -> non-zero exit, zero calls,
      nothing created; target SHA differing from HEAD OR from origin branch
      -> refuse; scoped tracked-dirty injection over any of the four files
      -> refuse (J1); pre-existing output root -> refuse with nothing created
      (J7, Tier 0).
- [ ] **T11** Record schema completeness incl. derived `wrong_codeword`;
      decoder-parameter assertions: poly 37, setting 90/1.0 on every record,
      no warm-start parameter in the call path (J9 injection); cross-lane
      `errors_initial` equality per block (J6 injection).
- [ ] **T12** Writer contract: file-set exactness, CSV/JSON row parity,
      overwrite fail-closed (existing root refused, J7), no NPZ written,
      summary contains planned/completed/started actuals, per-lane and
      per-source aggregates, both gate details ordered after terminal,
      verbatim stop rule, claim boundary.

## Phase C — preflight (decoder-free, before any authorization request)

- [ ] **P1** Reconstruct the six matrices; strict metric match vs committed
      structural authority; verify zero evaluator calls and zero writes.
- [ ] **P2** Run posterior-binding preflight on 390107/390207/390307; report
      PASS/BLOCKED only.
- [ ] **P3** Mechanically verify J2 against copied registries (zero overlap,
      no duplicates, 3-per-source shape) and confirm output root absent;
      report PASS/BLOCKED only.

## Phase D — authorized confirmation execution (requires EXECUTE_AUTH)

- [ ] **D1** Main thread obtains an independent plan review verdict and an
      explicit user `EXECUTE_AUTH` bound to repository, branch, full
      implementation SHA, cycle V41P0, scope
      `v41_confirmation_18_calls_exactly_once`.
- [ ] **D2** Run exactly once:
      `python scripts/execute_v41_fresh_block_confirm.py --execution-authorized --authorized-target-sha <sha>`;
      retain additive run_01 files; on error/partial state stop, retain raw
      partial records byte-for-byte without performance aggregates, return
      blocker; no rerun, resume, repair, tuning, block addition, or seed
      change; NO second confirmation round under any outcome.
- [ ] **D3** Read-only postcheck: accounting (18 planned / 18 completed /
      18 started unless integrity-stopped), record count and order C01-C18,
      no NPZ written, V38/V39/V40 outputs byte-identical, summary
      completeness, independent recomputation of gates and terminal.

## Phase E — result review

- [ ] **E1** Write OPERATOR_RETURN.md and DEVELOPMENT_RESULT.md candidate;
      lifecycle stays result-candidate; include terminal state, routing
      trace, per-lane/per-source aggregates and gate details, and the explicit
      decision (both lanes retained / single lane retained / STOP B/C
      parameter optimization with directional successor note).
- [ ] **E2** Independent recomputation of signals/machine/terminal by the main
      thread or reviewer; verdict copied into REVIEW_VERDICT.md.
- [ ] **E3** Memory triage as a separate milestone (this planning round is
      forbidden from editing AGENT_PROJECT_MEMORY.md).

## Explicitly forbidden during this change

Implementing before plan acceptance; running any production decoder or any
longrun/minrerun/routeA script; touching V38/V39/V40 code/tests/docs/outputs,
AGENT_PROJECT_MEMORY.md, existing OpenSpec changes, decoder, constructors,
loaders, evaluators, results/, or any official output root; importing the
v39 or v40 modules; reading any NPZ except read-only V25
`channel_counts.npz` via the accepted loader; writing ANY NPZ; reusing the
V40 probe blocks (390106/390206/390306) as confirmation samples; counting
wrong codewords as exact recoveries; framing results as Lane C or Lane B
superiority or any B-vs-C ranking; FER/threshold/SKR/security/qualification/
promotion/real-frame claims; adding blocks or seeds after results; revising
thresholds after results; rerunning, resuming, or compensating a partial run;
starting a second confirmation round under any outcome; tuning decoder
parameters under any outcome; self-acceptance; automatic successor start.
