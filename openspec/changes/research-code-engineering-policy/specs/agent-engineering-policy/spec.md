# Agent Engineering Policy

*Affected spec*: `AGENTS.md` — Repository-Level Agent Rules (currently no
corresponding spec in `openspec/specs/`; this is a new addition to the agent
rules domain).

## ADDED Requirements

### Requirement: Research Code Engineering Policy in AGENTS.md

`AGENTS.md` SHALL contain a "Research Code Engineering Policy" subsection
under §5 (Project-Specific Rules) that establishes the following constraints
for all agents operating in this repository:

- The repository is local research and data-analysis code, not a production
  service.
- Agents SHALL use the simplest implementation that is scientifically
  correct, readable, and reproducible.
- Agents SHALL NOT add integrity hashes, transactional writes, backup
  systems, file locking, elaborate validation, retry frameworks, security
  hardening, compatibility layers, custom caching, or excessive exception
  handling unless a task explicitly requires them.
- Agents SHALL assume trusted inputs, user-controlled execution, manual
  single-machine runs, rerunnable computations, and Git version control.
- Agents SHALL prioritize scientific correctness, explicit units and
  assumptions, readable calculations, reproducible seeds, validation against
  limits, clear errors, and minimal dependencies.
- Before adding any defensive mechanism, agents SHALL identify the concrete
  failure mode it prevents and SHALL omit it if no realistic failure mode
  exists.
- Agents SHALL NOT generalize one-off research scripts into production
  frameworks unless explicitly requested.
