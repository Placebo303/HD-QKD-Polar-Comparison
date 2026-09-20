# Proposal — G6 Minimum DECIDE Design (First-DECIDE Readiness)

- Role: coder-doc, docs-only. No code, no execution, no data access, no commit/push/branch move.
- Branch: `formal-ir-v72p1-addendum-clean` (do not switch; no commit/push in this call).
- Track: no track gate (documentation-only change, per AGENTS.md §1.2 applicability matrix).
- Frozen source: planner G6 return in this session (transcribed faithfully; no added science).
- This call: create this change (`proposal.md`, `design.md`, `tasks.md`) only. No `specs/` subdir (no behavior change).

## Why this is the first DECIDE

- [OBSERVED] Prior cycles through D19 established synthetic diagnostic coverage only; no first-DECIDE design freeze exists yet for a real-data confirmation.
- [PROPOSED] G6 freezes the minimum DECIDE design (operating point, population split, accounting, schemas, go/no-go) before any real-data execution, so a future run needs only its own packet + grant + Pre-EXECUTE + Pre-RESULT.
- [PROPOSED] This change authorizes nothing executable (see G6-6 NON-authorizations in `tasks.md`).

## Scope

- G6-1 operating-point skeleton (n128/m94/L020 `lam_d2_0.20_d3_0.80` representative; n256 excluded; realizable decoder cold row-layered 90/1.0 with Model-F marginal prior; disclosure form syndrome470+tag+control+interaction; no SKR).
- G6-2 CAL/selection/confirmation split (CAL 702..1725 consumed; selection ideally empty; VAL 1726..1729 ineligible; key-disjointness rule).
- G6-3 accounting equations + denominators, G6-4 schemas, G6-5 go/no-go (in `design.md`).
- G6-6 NON-authorizations, G6-7 unknowns, single STOP, future tasks 1–5 (in `tasks.md`).

## Non-goals

- No production code, no decoder/config changes, no execution, no data access.
- No `specs/` delta (no behavior change).
- No v72p2d19 change, no astra prep change, no cycle logs, no `AGENT_PROJECT_MEMORY.md` / `decision-log.md` / `troubleshooting.md` edits.
- No authorization of any future run (G6-6).

## G6-1 Operating-point skeleton

- [PROPOSED] Operating point: n128 / m94 / L020 `lam_d2_0.20_d3_0.80` as representative (not an optimality claim).
- [PROPOSED] n256 excluded from this DECIDE.
- [PROPOSED] Realizable decoder: cold row-layered 90/1.0 with Model-F marginal prior.
- [PROPOSED] Disclosure accounting form: syndrome470 + tag + control + interaction.
- [PROPOSED] No SKR claim in this DECIDE (secure-key output BLOCKED; see `design.md` §3/§5).

## G6-2 CAL / selection / confirmation split

- [OBSERVED] CAL 702..1725 consumed (prior development population).
- [PROPOSED] Selection stage ideally empty (no tuning/selection on confirmation).
- [OBSERVED] VAL 1726..1729 (4 frames) ineligible as confirmation (too small; descriptive-smoke role only).
- [PROPOSED] Key-disjointness rule: confirmation population must be key-disjoint from CAL/selection material.
- [UNKNOWN] Confirmation population identity (see G6-7; the single freeze-blocking STOP in `tasks.md`).
