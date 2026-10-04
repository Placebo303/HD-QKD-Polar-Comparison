# Tasks — G6 Minimum DECIDE Design

Legend: `[x]` done this call (coder-doc, docs-only, zero execution/data/commit);
`[ ]` future work (each needs its own authorization; future execution
additionally needs one explicit user grant with Pre-EXECUTE + Pre-RESULT).

## Design freeze (this call)

- [x] **G6 OpenSpec freeze** — this change (`proposal.md`, `design.md`,
  `tasks.md`) transcribing planner G6 return: G6-1 operating-point skeleton,
  G6-2 population split, G6-3 accounting, G6-4 schemas, G6-5 go/no-go, G6-6
  NON-authorizations, G6-7 unknowns, single STOP, future tasks 1–5. No
  `specs/` subdir (no behavior change). Zero execution/data/commit; forbidden
  paths untouched.

## Future tasks 1–5 (packet-frozen; [ ], each needs authorization)

- [ ] **Task 1** — Freeze confirmation population identity (resolves the single STOP below).
- [ ] **Task 2** — Freeze H denominator (`H_frozen`) for `beta_eff_empirical`.
- [ ] **Task 3** — Freeze disclosure constants (tag/control/interaction bits).
- [ ] **Task 4** — Freeze decoder-cap transfer statement and graph set + time basis.
- [ ] **Task 5** — Freeze numeric go/no-go cutoffs; then issue the future run packet with its own grant + Pre-EXECUTE + Pre-RESULT.

## STOP (single freeze-blocking user decision)

- [UNKNOWN] Confirmation population identity is the one freeze-blocking user
  decision: no confirmation execution may proceed until the user freezes which
  population serves as confirmation (key-disjoint from CAL 702..1725 and
  excluding VAL 1726..1729).

## G6-6 NON-authorizations (restatement)

- This change authorizes nothing: no run, no decoder call, no data access, no
  tuning/selection, no FER/SKR/qualification/promotion/publication claim.
- Any future run needs its own packet + explicit user grant + Pre-EXECUTE +
  independent Pre-RESULT + main-thread acceptance.

## G6-7 Unknowns carried

- [UNKNOWN] Confirmation population; H denominator; disclosure constants;
  decoder cap transfer; graph set; time basis; numeric cutoffs.
