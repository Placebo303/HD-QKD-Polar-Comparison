# Tasks — D18 Current-Channel L2 Ensemble DE

Legend: `[x]` done this call (E01, planner, no production code, zero
scientific calls); `[ ]` packet-exact future work (each needs its own
authorization; the future DE batch additionally needs one explicit user
grant with Pre-EXECUTE).

## Readiness spec (this call)

- [x] **E01 OpenSpec freeze** — this change (`proposal.md`, `design.md`,
  `tasks.md`, `specs/l2-ensemble-de/spec.md`) with packet §§1–6, 8–9 verbatim
  in scientific effect: §2 adjudication FIRST (FALSIFIED preserved, ceiling,
  forward-only latent-vs-predictive amendment with both formulas, descriptive
  tail formula + inputs with numeric evaluation deferred to E02/E06,
  secondary-signal status, main-thread route); §3 reuse map + rejected
  duplication; §4 21-family/IDs/DV3-control/D9-rho/grid/baseline/socket gate;
  §5 Stage-S (≤168, rank, top-3+DV3, blocked edge) + Stage-C (selected-4,
  32-reuse, ≤288 new, ≤456 total, rank-only) + decision (D17 bracket
  recompute, eligibility `delta_DE <= 0.5077488653656221`, winner rank,
  candidate-only effect); §6 four terminals; §8 boundary (root pattern, ≤456
  DE + ≤16 setup, 1800s/300s/2GiB/1-proc, no retry/resume/search/adaptive,
  later-grant scope, zero granted now). Zero DE/decoder calls; no
  code/scripts/tests/roots edits; no commit/push; branch unchanged.

## Future implementation/readiness (packet §7 — [ ], each needs authorization)

- [x] **E02 D18 module** — add a thin D18 module importing the corrected
  D17/D9/V26 helpers; document reuse and rejected duplication. Evidence:
  `design.md` §3 + delta-spec reuse requirements.
- [x] **E03 Plans + feasibility** — build the deterministic 21-candidate
  feasibility table, Stage-S plan, selection rule, conditional Stage-C plan,
  de-duplication (32-identity reuse, never rerun), and terminals. Evidence:
  `design.md` §§4–6 + delta-spec family/stage/terminal requirements.
- [x] **E04 Runner** — add a runner with `--profile-only`, `--de-sweep`,
  default-false `--execution-authorized`, fresh-root refusal, and read-only
  `--verify`. Evidence: delta-spec boundary/runner requirements.
- [x] **E05 Freeze** — freeze fresh DE seeds (`2026094301..4308` per §5),
  fresh root (`workspace/d18_l2_ensemble_de_<uuid>`, UUID picked here),
  exact repo-venv command, and budgets; prove all D16/D17 and predecessor
  seeds disjoint; prove future root absent. Evidence: `design.md` §8.
- [x] **E06 Focused tests** — exact candidate grid/IDs; rho/socket
  feasibility; stage counts/order; selection ties; overlap de-duplication;
  all terminal edges; corrected L2 sampler dispatch; APP/L1 exclusion; fake
  complete run; refusal/no-overwrite/tamper checks proportionate to
  scientific risk. Includes descriptive evaluation of the §2.4 tail
  `T(p_lo)`, `T(p_hi)` as a test value (description only, never a verdict
  revision). Evidence: delta-spec test requirements.
- [x] **E07 PROFILE_ONLY** — plan/candidate arithmetic only, zero DE/decoder
  calls, future root absent. Evidence: profile log + root-absence proof.
- [x] **E08 Independent review** — with actual artifact access: channel
  identity, reuse, feasibility, frozen plans, rank/eligibility, budgets,
  no-production, D16 interpretation ceiling, and tests. Any blocker → STOP.
  Evidence: review record with `EVIDENCE_ACCESS`.
- [x] **E09 Memory + decision log** — memory triage and one decision-log
  entry. No commit/push unless the task session's explicit scope safely
  permits a D18-only local commit.

(End of file)
