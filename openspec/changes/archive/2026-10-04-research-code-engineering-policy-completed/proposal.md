# Proposal: Research Code Engineering Policy

## Why

The user requires an explicit "Research Code Engineering Policy" be added to
the repository's agent rules. AGENTS.md §3 mandates that any change modifying
prompt rules must go through an OpenSpec change first. This proposal satisfies
that requirement and documents the policy for all agents operating in this
repository.

The user further requires **high-performance error-correction algorithm
research to be the project's strict first principle**. The existing policy
limits production-style engineering, but does not yet define what wins when
algorithm work competes with packaging, audit, verifier, or framework work.

## What Changes

Add a binding priority rule: discover, implement, and experimentally validate
scientifically reasonable high-performance IR algorithms for the actual
HD-QKD data first. Correction success, leakage efficiency, throughput,
resource cost, and net secret-key yield take priority over package maturity,
generality, defensive hardening, exhaustive audit machinery, and verifier
sophistication. Engineering may block algorithm work only for a concrete risk
of wrong science, irreproducible numerics, unauthorized expensive execution,
or destructive overwrite.

Add a new subsection `### 5.7 Research Code Engineering Policy` to
`AGENTS.md` §5 (Project-Specific Rules), containing the following policy
text:

> ### 5.7 Research Code Engineering Policy
>
> This repository contains local research and data-analysis code, not a
> production service.
>
> Use the simplest implementation that is scientifically correct, readable,
> and reproducible.
>
> Do not add the following unless the task explicitly requires them:
>
> * SHA-256, MD5, checksums, signatures, or integrity manifests
> * atomic file replacement or transactional writes
> * backup and rollback systems
> * file locking or concurrency protection
> * elaborate schema validation
> * retry frameworks
> * security hardening for untrusted input
> * compatibility layers for hypothetical environments
> * custom caching or artifact versioning
> * excessive exception handling that hides errors
>
> Assume:
>
> * inputs are trusted local research files;
> * the user controls the execution environment;
> * scripts are run manually on a single machine;
> * failed computations can normally be rerun;
> * Git is used for source-code version control.
>
> Prioritize:
>
> 1. scientific and numerical correctness;
> 2. explicit units, assumptions, and parameter definitions;
> 3. readable calculations;
> 4. reproducible random seeds where relevant;
> 5. validation against known limits or small test cases;
> 6. clear error messages for realistic input mistakes;
> 7. minimal dependencies and minimal abstraction.
>
> Before adding any defensive mechanism, identify the concrete failure mode
> it prevents. If no realistic failure mode exists in this repository, omit
> it.
>
> Do not generalize a one-off research script into a production framework
> unless explicitly requested.

## Scope

- **Files modified**: `AGENTS.md`, `openspec/project.md`, `README.md`, project
  decision/memory/roadmap documents, and this OpenSpec packet
- **Files NOT touched**: algorithm source code or scientific outputs
- **No new files** outside this change directory
- **No test requirements** (pure policy/documentation change)
