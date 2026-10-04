# Proposal: Standardize Agent Delivery Workflow v1

## Why

Recent qualification work lost time and tokens through underspecified test
matrices, repeated partial subagent returns, incremental acceptance review,
and repeated test invocations.

## What Changes

- Make one complete frozen task packet the default unit of delegated work.
- Restrict operator returns to complete delivery or a concrete blocker.
- Limit main-thread reviews to specification freeze, candidate review, and
  independent acceptance.
- Require layered evidence and tamper matrices to be frozen before coding.
- Reuse accepted predecessor machinery through an explicit delta list.
- Standardize T0--T3 test stages, explicit fake runners, Windows test roots,
  process ownership, scoped dirty-worktree review, and compact handoffs.

## Scope

This is a project-wide coordination rule. It does not change scientific
thresholds, source locks, production evidence, or method implementations.
