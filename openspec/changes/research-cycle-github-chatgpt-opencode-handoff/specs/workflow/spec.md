# Research-cycle handoff specification

## Requirements

### RC-01: Durable review target

Every ChatGPT or OpenCode handoff SHALL name the repository, branch, cycle ID,
target commit SHA, required entrypoint document, and allowed lifecycle action.

### RC-02: Copy-paste contracts

The repository SHALL provide directly reusable prompts for ChatGPT review and
OpenCode execution, plus fixed return schemas for review and operator results.

### RC-03: Role separation

ChatGPT review SHALL be advisory until committed. OpenCode SHALL NOT redefine
requirements, grant acceptance, authorize formal execution, or claim
scientific promotion. The user/main reviewer owns those decisions.

### RC-04: Git evidence contract

Each research milestone commit or PR SHALL include the applicable code,
OpenSpec delta, tests, and either compact machine-readable result data or a
result-summary document. Omitted data SHALL be identified with the reason,
provenance, and reproduction or retrieval instructions.

### RC-05: Scientific priority

The workflow SHALL remain subordinate to high-performance error-correction
research. It SHALL NOT require checksums, adversarial evidence frameworks, or
package-grade infrastructure unless a concrete scientific or data-loss risk
requires them.

### RC-06: GitHub safety

Publishing SHALL use a normal non-force push. If the configured remote branch
contains an incompatible line, the research state SHALL be pushed to a new,
clearly named branch rather than merged across repository boundaries or
force-pushed.

