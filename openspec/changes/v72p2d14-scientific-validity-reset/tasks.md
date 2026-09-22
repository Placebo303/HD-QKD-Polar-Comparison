# Tasks: D14 Scientific Validity Reset R1 (successor implementation)

Frozen packet: `.workbuddy/tasks/D14_SCIENTIFIC_VALIDITY_RESET_R1_TASK_PACKET.md`
(sole authority; §1–§8 frozen). Track: `EXPLORE` (packet §1; P/C
implementation and the no-decoder R run require no execution gate). Branch
`formal-ir-v72p1-addendum-clean` (do not switch; no commit/push by any task
except the explicitly scoped local non-pushed commits a later instruction may
authorize — this task list authorizes none). Implement exactly what
`specs/validity-reset/spec.md` specifies; on any ambiguity STOP and return to
the planner (do not guess). Predecessor context trusted, not re-audited:
S1/S2 markers PRESENT; S3 groups 2/3/4 + manifest committed locally
(`55ab6de`/`5f4b121`/`43308b8`/`ccc33eb` on `278fdf07`); group 1 deferred;
group 5 STOPPED (carried; blocks nothing below).

- [x] T0 — P-spec (this call, planning only)
  - Wrote `openspec/changes/v72p2d14-scientific-validity-reset/` (`proposal.md`,
    `design.md`, `tasks.md`, `specs/validity-reset/spec.md`) covering Phases
    P+C+R+N with claim ceiling, budgets, and STOP rules per packet §1/§8–§9.
  - Allowed files (this task only): the four listed OpenSpec paths. Touched no
    code/scripts/tests/roots, `AGENTS.md`, or decision-log. Zero execution,
    zero decoder calls, no commit, no push.

- [x] P1 — P-impl: prior-selection correction (code + focused tests, NO execution)
  - Allowlist: `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
    (exactly three call sites + two docstrings, §VR-P-01–VR-P-03) and
    `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py` (additive cases
    only, §VR-P-04). Verify the `scripts/` shim carries no estimator symbol
    (read-only grep); touch nothing else.
  - Contract: candidate exactly once per entrypoint, legacy never (poisoned);
    fake decoder + fresh scratch `out_dir`; finite/normalized/non-uniform/
    bitwise-equal asserts; static anti-return assert (legacy stem + `(`);
    legacy functions behavior-identical.
  - Verify: `py_compile` on the touched module; focused test file only
    (`pytest -p no:cacheprovider`, fresh additive `workspace/<task>/<uuid>`
    basetemp where needed); decoder calls 0; no formal-root creation or
    modification (snapshot proof); `*_execution_authorized` unchanged.
  - STOP: any ambiguity; any legacy reachability; any formal-root write;
    any decoder import on fake paths.

- [x] P2 — P-impl independent review
  - Independent thread with artifact access verifies the three-site diff,
    both docstrings, legacy identity, the full VR-P-04 evidence matrix, zero
    executions, and scoped-tree cleanliness. Verdict + exact corrections;
    FAIL blocks C/R/N.

- [x] C1 — C-impl: additive G2/X4 corrigendum (docs only, NO execution)
  - Allowlist: new
    `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/G2_PRIOR_CONFIG_CORRIGENDUM_R1.md`
    plus append-only pointer blocks in
    `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_WIDE_ATTRIBUTION_R2.md`
    and `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/OPERATOR_RETURN_R1.md`,
    plus append-only status/pointer lines in the D5/D7 `cycle_state.yaml`
    files, `docs/decision-log.md`, and `AGENT_PROJECT_MEMORY.md`. No
    historical body line rewritten (§VR-C-01–VR-C-05).
  - Verify: root `workspace/v72p2d5_g2/20260906_r1` byte-identical (file list +
    grade grep); scoped `git status` shows root and record bodies untouched;
    required wording present verbatim in scope (literal grade, rejected-config
    statement, inference-only supersession, no unique-cause claim).

- [x] C2 — C-impl independent review
  - Independent thread verifies corrigendum wording against §VR-C-03,
  unchanged-root proof, additive-only diffs, and pointer linkage. FAIL blocks
  R/N.

- [x] R1 — R-impl: audit module + focused math tests (NO run beyond tests)
  - Allowlist: new
    `comparison_bench/src/comparison_bench/formal_ir/v72p2d14_rate_calibration_audit.py`,
    new `scripts/v72p2d14_rate_calibration_audit.py` (thin runner), new
    `comparison_bench/tests/test_v72p2d14_rate_calibration_audit.py`.
    Reuse (never copy) accepted D8–D12 input/sampling helpers; record the
    exact import map in the module docstring (§VR-R-01–VR-R-02).
  - Verify: `py_compile`; focused tests only (tiny entropy/CE/self-information
    fixtures + no-write/refusal checks in fresh basetemps); frozen audit root
    `workspace/v72p2d14_rate_audit/20260914_r1/` proven absent afterwards.

- [x] R2 — R-run: no-decoder calibration audit (EXPLORE synthetic-diagnostic run)
  - Single run of the frozen command into the frozen fresh root (absent-proof
    immediately before write); persists the full §VR-R-03 surface (CSV/JSON +
    one concise `report.md`); records wall/RSS; decoder calls 0; no new
    blocks, no seed search, no VAL/real/raw reads (§VR-R-04–VR-R-05).
  - STOP: root pre-exists; any decoder/real-data reach; ceiling breach
    (3600 s / 2 GiB) → re-scope, never tune.

- [x] R3 — R-impl+run independent review
  - Independent thread recomputes both-layer entropy/rate arithmetic and a
    sample of per-block joins from the frozen root, checks equations/axes/
    units/floor-order/estimator records, the load-vs-success separation (no
    sufficiency label), `undetected` isolation, hypothesis cross-check
    (reproduced or mismatch-with-cause), and zero decoder/real-data calls.
    FAIL blocks N.

- [x] N1 — N-freeze: paired L1/L2 discriminator packet (docs only, NO code, NO run)
  - Wrote new `docs/research_cycles/D14_VALIDITY_RESET/N_DISCRIMINATOR_PREREG_R1.md`
    only (this call, planning only). Built solely from R evidence
    (`workspace/v72p2d14_rate_audit/20260914_r1/`): Choice A (entropy-derived
    rows on the actual generator, m_L1=110/effective 1.00237 at n128, no
    generator change + why; triple mismatch retained as open note, never copied);
    L045-control + L055 on L1, frozen D11-DV3 L2 APP + true-L1-prior oracle
    diagnostic (never gating); paired blocks + 6+6 fresh graph seeds
    (2026093401..06/2026093501..06/2026093601..12, absence-proven); 288-call
    routing-only batch; preregistered thresholds (§7 priority rule), exact call
    list, fresh root/command/budgets within frozen ceilings, claim ceiling;
    terminal `READY_AWAITING_EXPLICIT_AUTHORIZATION` with root-absent proof
    (read `File not found` + content search no-hits); no D7-H revival
    (§VR-N-01–VR-N-03).
  - Freeze contingent on pending R3/N2/final independent reviews. Zero execution,
    zero decoder calls, no commit, no push.
  - Allowlist: new `docs/research_cycles/D14_VALIDITY_RESET/N_DISCRIMINATOR_PREREG_R1.md`
    only. Built solely from reviewed R evidence: stated rate/row-vs-generator
    choice + why; L055 + frozen control (L1) + L2 DV3/oracle diagnostic;
    paired blocks + multi-seed; investment-routing batch size; preregistered
    thresholds/calls/fresh root/command/budgets/ceiling; terminal
    `READY_AWAITING_EXPLICIT_AUTHORIZATION` with root-absent proof; no D7-H
    revival (§VR-N-01–VR-N-03).

- [x] N2 — N-freeze independent review
  - Independent thread verifies every frozen value traces to reviewed R
  evidence, thresholds/calls/root/command/budgets/ceiling are complete and
  within frozen ceilings, the root is absent, and no authorization is granted.
  FAIL blocks the final review.

- [x] F — Final independent review + return
  - Full packet §8 checklist (manifests/scope, estimator selection, unchanged
    roots, corrigendum wording, both-layer arithmetic, per-block joins,
    next-batch thresholds/budgets, zero decoder/real-data calls) returning
    `EVIDENCE_ACCESS: VERIFIED`, verdict, blocking findings, exact
    corrections. On pass, return
    `D14_VALIDITY_RESET_COMPLETE_CALIBRATED_BATCH_READY_AWAITING_EXPLICIT_AUTHORIZATION`
    with the packet §9 report (scoped commits, wiring delta + tests,
    corrigendum locations + unchanged-root proof, reproduced entropy/factors +
    per-block findings, frozen next-batch packet/root/command/budgets still
    unauthorized, findings + claim boundaries). On any blocker, return the raw
    command/output, attempted safe checks, and the single decision needed. Do
    not self-authorize scientific execution.
