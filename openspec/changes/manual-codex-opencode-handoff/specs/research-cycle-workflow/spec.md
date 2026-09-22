# Research-cycle workflow delta

## Requirement: Cross-agent handoff SHALL be manual

Project-level Codex/ChatGPT and OpenCode prompts and returns SHALL be
transferred manually by the user through the repository-native packet and
return documents.

### Scenario: An agent wants to continue the other agent

- **WHEN** Codex/ChatGPT or OpenCode finishes a bounded turn
- **THEN** it SHALL produce the appropriate prompt or receipt for manual
  transfer
- **AND** it SHALL NOT invoke an automatic cross-agent bridge or callback loop.

## Requirement: Global bridge components SHALL remain untouched

Disabling bridge use for this project SHALL NOT uninstall, rewrite, restart,
or close the global bridge, skills, server, or existing sessions.
