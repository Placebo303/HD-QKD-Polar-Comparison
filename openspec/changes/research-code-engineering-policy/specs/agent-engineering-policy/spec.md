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

### Requirement: High-performance correction algorithms are the strict first principle

The project SHALL prioritize discovering, implementing, and experimentally
validating scientifically reasonable high-performance information-
reconciliation algorithms for actual HD-QKD data above package maturity,
generality, defensive hardening, exhaustive audit machinery, and verifier
sophistication.

Algorithm performance SHALL be evaluated using the applicable combination of
correction success/FER, leakage and reconciliation efficiency, throughput and
runtime, memory/resource cost, and accepted-frame net secret-key yield.

Engineering, audit, or verifier work SHALL block algorithm work only when the
unresolved issue can concretely cause a wrong numerical/scientific conclusion,
an irreproducible result, unauthorized expensive execution, or destructive
overwrite of existing data. Other engineering improvements SHALL be recorded
as non-blocking or deferred.

#### Scenario: Review finds a defensive or verifier improvement

- **WHEN** the finding cannot change the algorithm's numerical result,
  scientific attribution, authorization boundary, or existing data
- **THEN** it SHALL NOT block algorithm implementation or measurement
- **AND** the project SHALL continue with the highest-information algorithmic
  task.

#### Scenario: Algorithm and package work compete for effort

- **WHEN** both are available and package work is not required for a concrete
  scientific or data-safety failure mode
- **THEN** the algorithm hypothesis, implementation, or performance experiment
  SHALL be performed first.
