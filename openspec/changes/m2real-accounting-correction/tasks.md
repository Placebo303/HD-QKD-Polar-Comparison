# Tasks: M2 real accounting correction (DECIDE-gated; no redecoding)

Convention: implement exactly these tasks; on requirement ambiguity
STOP and return to planner/main instead of guessing. No task below is
small enough to skip the pipeline: T1–T2 are claim-bearing
recalculations from real-data artifacts and SHALL NOT execute before
the T0 DECIDE gate (preregistration + Pre-EXECUTE + explicit user
grant) passes. Orchestrator SHALL NOT route around the gate.

Allowed paths (read-only inputs): the three T3 `rows.json` summaries,
`workspace/m2_accounting_replay_20260926/diagnostic.json` +
`resource.txt`, and the cycle documents cited in the proposal.
Forbidden for all tasks: any decoder/construction call, any `.ttbin`
or bundle read, any write to existing roots/records/reviews, any edit
to `m2real_runner.py` / `m2_accounting_replay.py` / `src/` /
`experiments/` / `tools/`, any write under `results/` or
`comparison_bench/outputs_comparison/`, any commit/push (ordinary
non-force named-branch pushes are main's separate decision).

- [ ] T0 — DECIDE preregistration + Pre-EXECUTE + grant (main thread
  owns; coder waits). Write `docs/research_cycles/M2-REALCOMP/CORRECTION_PREREG_AND_AUTH.md`
  (new analysis, not an amendment of T3): frozen read-only input list,
  exact recomputation formulas (design §§1–4), output document name and
  location (decided here: additive doc under
  `docs/research_cycles/M2-REALCOMP/`, never inside an existing root),
  budget (one process, wall ≤300 s, RSS <2 GiB, no retry), stop rules,
  and the verbatim user grant. Record the Pre-EXECUTE checklist
  (branch `formal-ir-v72p1-addendum-clean`; scoped cleanliness;
  `git diff -- src/ experiments/ tools/` empty for this task; output
  absence; focused-test N/A with reason — no code is added by this
  change — or the exact test command if a helper is preregistered).
  Evidence: grant verbatim on file; all checks PASS or STOP. No
  fallback to raw data or redecoding. (Acceptance: main-thread sign-off
  on the packet before T1.)
- [ ] T1 — Corrected-accounting record (coder-doc, after T0 grant).
  Write the preregistered record document: per source/family/m arm (12
  arms, kept separate, never pooled) carry original nominal columns
  (`historical-nominal`) beside `f_ec_actual` and
  `f_with_recorded_tags` (`measured-corrected`), the one-tag column
  (`counterfactual`, COUNTERFACTUAL_ONLY everywhere), separate
  block-level and superframe-level denominators, `f_eff` as
  `not-defined` (originals retained as history) per decided D-2
  (DROP, user, 2026-09-27; reintroduction gated behind a new
  preregistration),
  per-column status from the design §8 vocabulary, `backend_used =
  UNKNOWN`, HDC `assumed-v1` scope plus both void limits
  (MAC-6/MAC-9; `void-stub-artifact` and `void-no-correction`) on every HDC number, LB
  `leak_EC` and every derived column carrying `void-no-correction`
  (MAC-10, decided D-5) with LB `success`/FER/`undetected` standing
  as real measurements of genuine failure (explicitly not voided), D2
  `retired-m2` (no rule, no branch evaluation, no branch reporting;
  rejected options recorded per decided D-3), `undetected`
  isolated, F9(i) annotation on every M0-number reference, and the
  claim ceiling verbatim. No task SHALL evaluate or report a D2
  branch, fill an HDC comparison column, fill any LB comparison
  column, or infer the LB backend.
  Source values: reviewed `diagnostic.json`
  arm rows; original labels from its `original_f_labels`. (Acceptance:
  AC-1/AC-2/AC-5 check against design §§1–15 and spec MAC-1..10 by a
  reader who did not write the file; any mismatch → rework, no
  publish-then-patch.)
- [ ] T2 — Independent recomputation check (read-only; after T0 grant;
  a thread that did not write T1). Recompute at least one arm per
  source directly from the persisted `rows.json` `summary` values
  (`D = superframes_done·1024·H_corr`, `E`, `T`, both tag ratios, the
  nominal closed-forms) using only a calculator or a throwaway
  read-only script that imports no decoder/construction module and
  writes no file outside a fresh additive `workspace/` scratch root
  (or no file at all); verify all 12 (source, family, m) identities,
  `blocks_done = 16·superframes_done`, `tag = 64·blocks_done`,
  denominator positivity, source/arm separation, and the 1M/m197
  discrepancy reproduction (nominal 1.20048829 both arms vs actual
  10.15137 / 3.84156 and inclusive 11.39939 / 5.08958, diagnostic).
  Confirm the three input roots unmodified (sizes/mtimes against the
  replay Pre-EXECUTE record). (Acceptance: AC-3; any mismatch → STOP,
  retain evidence, return to main — never adjust inputs to fit.)
- [ ] T3 — Independent Pre-RESULT review (separate review thread; after
  T1+T2). Re-check the frozen packet thresholds, leakage-formula
  decomposition, `undetected` isolation, per-source breakdown,
  disclosure accounting, tag-unit labelling, counterfactual labelling,
  FER-unit separation, backend-UNKNOWN stance, HDC scope including the
  verification-path void, the zero-correction void, the LB
  `void-no-correction` (MAC-10, decided D-5) and MAC-9 HDC exclusion, D2
  retirement (M2 scope), status discipline, A-CMPE consistency scoping (§9
  choices), and claim ceiling against the actual record artifacts.
  Record PASS or FAIL with findings in
  `docs/research_cycles/M2-REALCOMP/CORRECTION_INDEPENDENT_ACCEPTANCE.md`.
  FAIL blocks solidification (revise-required; scoped root cause,
  re-review). (Acceptance: AC-4 first half.)
- [ ] T4 — Main-thread acceptance (main + user; coder does not sign).
  Record the acceptance decision (BLANK until signed) in the
  decision-log: accept the corrected record as stored disclosure
  arithmetic for the recorded implementations, keep original M2
  scientific acceptance WITHHELD, and record D-1 as DEFERRED-open
  with D-2/D-3/D-4/D-5 as decided 2026-09-27 (see decided-status block
  below). Until signed, no corrected
  number is citable beyond the record itself. (Acceptance: AC-4 second
  half + AC-5.)

- Parallel bounded item P-BE — read-only backend trace (authorised by
  decided D-5(iii); separate from T1–T4; not scheduled beyond this
  scope). Search the three M2 T3 roots and adjacent cycle records for
  any surviving contemporaneous backend trace (sidecar, stdout
  transcript, resource record). No decoder or construction call, no
  `.ttbin` read, no new execution, no write to any existing root.
  Outcome refines the LB negative finding but never withdraws it
  (D-5(i) stands either way).

Decided status (decided by the user, 2026-09-27, relayed by the main thread; implementers SHALL treat decided items as frozen, T4 records them):

- D-1 (tag verification unit): DEFERRED — the single open item. The user will not pick a unit by inference from code. Scope of deferral: it does NOT block the T0 read-only recompute, because all tag totals are already carried distinctly (recorded 16x64-bit-per-block, one-tag-per-superframe nominal, one-tag column COUNTERFACTUAL); D-1 decides only which column is the headline. Resolving it later changes the headline f column, not any already-published column; the settling evidence is a frozen protocol specification, not a code reading.
- D-2 (`f_eff` for HDC/LB): DROP — decided 2026-09-27 (user). Rationale: the NB 1024-symbol superframe slope is unit-incompatible with 64-block arms and all recorded superframe successes are zero. Standing condition: any reintroduction needs a NEW preregistered method-specific, unit-consistent definition; the NB slope may never be silently reused.
- D-3 (D2 rule): RETIRE D2 FOR M2 (option iii) — decided 2026-09-27 (user). Rationale: after the HDC void findings D2 has no valid input in M2 (displayed f was not actual disclosure, tag unit undecided, HDC unevaluable, LB backend UNKNOWN); options (i)/(ii) considered-and-rejected on those grounds. Routing proceeds via the M0/P1 measured gap. Scoped to M2 only — not a statement that the comparison question is unanswerable forever.
- D-4 (HD-Cascade column): option (iii) — decided 2026-09-27 (user). HDC is a documented negative implementation result, not a comparison column; both void labels attach to every HDC number wherever it appears; disclosure labelled `exhausted assumed schedule on uncorrected blocks — not a method property`. Option (ii) was considered: a fresh-root real-data DECIDE execution relabelling `undetected` while changing no value of `exact_match`, `leak_EC` or FER — recorded here so it is never later adopted as a repair. A citable HD-Cascade number needs a converging cascade (real verifier AND correcting parameters), a research sub-project outside this change.
- D-5 (Layered-Binary disclosure): decided 2026-09-27 (user, relayed by main; verbatim acceptance: 「可以接受这些」) as option **(i) plus (iii) in parallel**. (i) LB is a documented negative implementation result with `void-no-correction` on its disclosure and every derived column (MAC-10, design §10.2/§14), exactly parallel to D-4(iii) for HD-Cascade. (iii) A read-only trace for contemporaneous backend provenance is authorised in parallel — no redecoding, no new execution, only a search of the three M2 roots and adjacent records for any surviving backend trace. Option (ii) — retaining the disclosure as a bare diagnostic without the void label — was considered and rejected: it is the reading that invites the ranking this change exists to prevent. (i)+(iii) is operative and (iii) does not change (i) either way: if a backend trace is found, the finding is refined, not withdrawn.
