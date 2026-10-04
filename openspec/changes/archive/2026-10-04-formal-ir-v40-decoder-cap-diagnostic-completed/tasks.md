# OpenSpec Tasks: formal-ir-v40-decoder-cap-diagnostic

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Execution status**: nothing below is started or authorized. No task in
this change may run a production decoder until an independent plan ACCEPT
and a new explicit user `EXECUTE_AUTH` bound to the accepted
implementation SHA exist. (V39P0 run_01 evidence is already accepted —
lifecycle `DEVELOPMENT_RESULT_ACCEPTED`, result SHA
`940bfc996a0bd87d60e958150c4f770ee35f16b8` — so no V39 review
precondition remains.)

## Phase A — implementation candidate (after plan acceptance)

- [ ] **A1** Create module
      `comparison_bench/src/comparison_bench/formal_ir/v40_decoder_cap_diagnostic.py`
      reusing accepted v38 constructors/evaluator and v35 loaders per
      design Section 16; no import of the v39 module; no modification to
      any existing module.
- [ ] **A2** Freeze constants: the 12-instance table with V39 reference
      residuals (design Section 3, order A01–A12); representative
      ordinals C=2 / B=2 with their six matrix ids (Section 4); probe
      block seeds 390106/390206/390306; FORBIDDEN seed union
      (V36_A3 ∪ V39 registries); decoder contract per phase (Section 10);
      budget caps 12/12/6 hard 30; output root and file set (Section 15).
- [ ] **A3** Implement instance extraction + validator: parse the committed
      `v39_paired_comparison.json`, filter `discordance_label ==
      "NEITHER_EXACT"`, assert exactly 6 pairs / 12 instances in frozen
      order matching the embedded table (J1), all V39 references
      `exact_l2 == false`, min residual > 0 (J2).
- [ ] **A4** Implement deterministic reconstruction of the 12 matrix
      usage rows (10 unique matrix ids; Phases A/B and the probe share
      `lane_c_1M_s383102` and `lane_b_1M_s382102`) with strict comparison
      against the committed 27-record
      V38P0 structural JSON incl. Lane C `position_permutations`;
      representative-ordinal recomputation from `v39_summary.json` must
      equal frozen constants (J3); NPZ must not be read.
- [ ] **A5** Implement block registry validator for probe seeds: exact one-
      per-source shape, no duplicates, mechanical disjointness vs
      V36_A3 ∪ V39 seeds (J4).
- [ ] **A6** Implement posterior-binding preflight P-BIND-1/2/3 on probe
      blocks 390106/390206/390306 per design Section 16 sentinels
      (decoder-free, write-free).
- [ ] **A7** Implement IMP_A/IMP_B exactly per design Section 6
      (matched-subset denominators, empty-set -> 1.0, zero-denominator ->
      J2) plus descriptive pooled-median reporting.
- [ ] **A8** Implement the guarded phased runner: default-deny authorization
      (`--execution-authorized` + exact-equality SHA preflight of HEAD AND
      `origin/formal-ir-mainline`, J11), scoped tracked-dirty check over
      (v40 module, v40 CLI, v38 module, v35 module), output root created
      before the decoder stage with fail-closed existence guard (J8),
      Phase A always / Phase B gated by R10 trigger / probe gated by R11
      triggers with unique-setting assertion (J12), frozen call order,
      per-call record emission, hard budget enforcement (J5),
      `BaseException` partial-record retention with started/completed
      actuals and no performance aggregation on partial sets.
- [ ] **A9** Implement signals, routing trace, and the total/disjoint
      terminal machine of design Section 13 rules 0–6 including wrong-
      codeword propagation and `terminal_reason`.
- [ ] **A10** Implement additive writer: exact file set of design Section 15,
      CSV/JSON parity, no-NPZ-output enforcement, winner-NPZ read
      rejection, summary contents per design Section 12 incl. frozen
      probe aggregates (`exact_total`, `exact_lane_c`, `exact_lane_b`,
      `wrong_lane_c`, `wrong_lane_b`), verbatim master stop rule, claim
      boundary, statistics note, provenance SHAs; invalid-notice path.
- [ ] **A11** Add `scripts/execute_v40_decoder_cap_diagnostic.py`: default
      deny, mandatory flags, binding `fake_runner=False`, no fake-runner
      CLI option, non-zero exit with zero calls on any guard failure.

## Phase B — focused tests (fake runners only; zero production decode)

- [ ] **T1** Instance extraction: synthetic paired JSON with 6 NEITHER +
      decoy labels yields exactly A01–A12 in order; any membership/order/
      residual drift raises J1.
- [ ] **T2** Reconstruction match logic detects injected metric drift (incl.
      `position_permutations`) → J-path; two reconstructions identical.
- [ ] **T3** Representative-rule unit test: synthetic ordinal aggregates
      (unique max, tied max) resolve correctly; constants C=2/B=2 asserted
      against the committed summary values 11/12/10 and 10/11/10.
- [ ] **T4** Probe-seed validator rejects duplicates, wrong shape, and each
      overlapping family (V36_A3 range, V39 range); accepts the frozen
      trio.
- [ ] **T5** Posterior capture/sentinel tests per design Section 16
      (complete-bob forwarding; all six fixed conditions incl. 1e-6 and
      argmax divergence).
- [ ] **T6** IMP math on hand-computed fixtures: boundary IMP_A == 0.25
      exactly; empty S_P -> 1.0; zero-denominator -> J2; matched-subset vs
      pooled medians both reported.
- [ ] **T7** Call accounting in fake mode: Phase A = 12; B runs only when
      the R10 trigger holds (`W_A == 0 and R_A <= 1 (out of 12) and
      IMP_A >= 0.25`,
      12 calls) else skipped; probe only per R11 triggers (6);
      total <= 30; any over-count raises J5; skipped stages consume
      nothing.
- [ ] **T8** Record schema completeness incl. derived `wrong_codeword`,
      `rescued_vs_v39` correctness (null on probe rows), per-phase
      max_iter/damping_alpha recorded; decoder-parameter assertions:
      poly 37, phase settings table honored, no warm-start parameter in
      the call path (J10 injection).
- [ ] **T9** Truth-table test: enumerate all reachable (W_A?, R_A class,
      IMP_A class, R_B_new class, W_B?, probe aggregate fields
      exact_total/exact_lane_c/exact_lane_b/wrong_lane_c/wrong_lane_b)
      combinations; each lands in exactly one terminal per design
      Section 13 rules 0–6; EVIDENCE_INVALID precedence; impossible
      combinations (probe while `W_A > 0`; Phase B while `W_A > 0` or
      `R_A >= 2 (out of 12)`; two probe settings) asserted unreachable; probe truth
      table exhaustive and mutually exclusive incl. per-lane thresholds.
- [ ] **T10** Boundary cases: R_A = 4 (out of 12) with W_A > 0 → STOP_BC
      (reason WRONG_CODEWORD_PHASE_A, probe unreachable); R_A = 4 (out of
       12) with W_A = 0 → probe (90/1.0); R_A = 2–3 (out of 12) with
      W_A = 0 → GO_STRUCTURE (WEAK_EXACT_RESCUE) even when IMP_A >= 0.25;
      R_A = 1 (out of 12) with IMP_A = 0.25 exactly → Phase B;
      R_B_new = 3 (out of 12) boundary → DAMPING_VALUE only when W_B = 0,
      else GO_STRUCTURE (reason DAMPING_NO_VALUE); probe boundaries
      exact_total = 2/3/4, either lane exact = 1/2, and any
      wrong_lane_* > 0.
- [ ] **T11** errors_initial equality: cross-lane same-block equality in all
      phases; Phase A/B equality vs V39 references (J7 injections).
- [ ] **T12** Writer contract: file-set exactness, CSV/JSON row parity,
      overwrite fail-closed (J8), no NPZ output, winner-NPZ read rejected,
      summary contains planned/completed/started actuals, master stop
      rule verbatim, claim boundary.
- [ ] **T13** CLI guards: missing either flag → non-zero exit and zero
      calls; SHA differing from HEAD or origin branch → refuse; scoped
      tracked-dirty injection → refuse (J11).
- [ ] **T14** Partial retention: injected mid-phase `BaseException` → raw
      partial records retained byte-for-byte inside the pre-created root,
      actuals recorded, no performance aggregate or terminal beyond the
      failure marker.
- [ ] **T15** Budget cap: structural refusal of a 31st call (J5).
- [ ] **T16** Phase gating: B run without trigger or probe without trigger
      or ambiguous setting → J12.

## Phase C — preflight (decoder-free, before any authorization request)

- [ ] **P1** Reconstruct all matrices (12 usage rows / 10 unique ids);
      strict metric match vs committed
      structural JSON; verify zero evaluator calls and zero writes.
- [ ] **P2** Run posterior-binding preflight on 390106/390206/390306;
      report PASS/BLOCKED only.
- [ ] **P3** Verify J1/J3/J4 mechanically against the committed V39 files
      (instance set, representative ordinals, seed disjointness); verify
      output root absent; report PASS/BLOCKED only.

## Phase D — authorized diagnostic execution (requires EXECUTE_AUTH)

- [ ] **D1** Main thread obtains an independent plan review verdict and an
      explicit user `EXECUTE_AUTH` bound to repository, branch, full
      implementation SHA, cycle V40P0, scope
      `v40_decoder_only_max30_calls_exactly_once`.
- [ ] **D2** Run exactly once:
      `python scripts/execute_v40_decoder_cap_diagnostic.py --execution-authorized --authorized-target-sha <sha>`;
      retain additive run_01 files; on error/partial state stop, retain
      raw partial records byte-for-byte without performance aggregates,
      return blocker; no rerun, resume, repair, tuning, or seed change.
- [ ] **D3** Read-only postcheck: accounting vs budget (12 / 0-or-12 /
      0-or-6; <= 30), record counts per executed phase, errors_initial
      equalities, no NPZ written, winner-NPZ unread, V38/V39 outputs
      byte-identical, summary completeness.

## Phase E — result review

- [ ] **E1** Write OPERATOR_RETURN.md and DEVELOPMENT_RESULT.md candidate;
      lifecycle stays result-candidate; include terminal state, routing
      trace, IMP/rescue/wrong numbers, and the explicit decision (retain
      Lane B/C at the fixed setting pending a NEW confirmation change vs
      stop decoder direction and move budget to protograph/MET).
- [ ] **E2** Independent recomputation of signals/machine/terminal by the
      main thread or reviewer; verdict copied into REVIEW_VERDICT.md.
- [ ] **E3** Memory triage as a separate milestone (this planning round is
      forbidden from editing AGENT_PROJECT_MEMORY.md).

## Explicitly forbidden during this change

Implementing before plan acceptance; running any production decoder or any
longrun/minrerun/routeA script; touching V38/V39 code/tests/docs/outputs,
AGENT_PROJECT_MEMORY.md, existing OpenSpec changes, decoder, constructors,
loaders, evaluators, results/, or any official output root; reading
`v38_winning_matrices.npz` or writing any NPZ (read-only V25
`channel_counts.npz` via the accepted loader stays allowed); counting
diagnostic rescues as Lane B/C route successes; retroactively editing V39
terminal state or conclusions; adding a third decoder setting, damping
grid, iteration grid, warm start, or retry under any outcome; adding
seeds after results; revising thresholds after results; rerunning or
resuming a partial run; self-acceptance; automatic successor start.
