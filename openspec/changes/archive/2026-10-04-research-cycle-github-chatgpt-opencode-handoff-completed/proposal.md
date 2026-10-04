# Proposal: GitHub-centered research-cycle handoff

## Why

ChatGPT is used for scientific planning and read-only review while OpenCode is
used as an implementation operator. Their chat histories are not a durable or
shared source of truth. Every research cycle therefore needs copy-pasteable
inputs and outputs that are bound to Git commits and carry enough result data,
or a reproducible data summary, for independent review.

## Scope

- Define one repository-native SOP for ChatGPT planning/review and OpenCode
  execution handoffs.
- Define lifecycle states, copy-paste prompt/return contracts, Git commit/PR
  rules, and the minimum data-summary contract.
- Add project entry points and a PR checklist.
- Record the current V35/V36 development state without promoting it.

## Non-goals

- No MCP server, workflow bot, release framework, or production packaging.
- No automatic scientific acceptance or formal-execution authorization.
- No requirement to commit raw, large, sensitive, or binary experiment data.

