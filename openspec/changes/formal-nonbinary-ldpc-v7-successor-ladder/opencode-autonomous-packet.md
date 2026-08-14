# OpenCode Autonomous Packet: V7 Successor Ladder

## Authority

Implement and run V7-00 through V7-42 in the frozen route order. Development
execution is authorized only under the plan/review/execute/replay state machine
defined here. Confirmation, real data, official outputs, reruns, and scientific
promotion are not authorized.

## Required Reading

Read `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`, the complete V6 change, and every
file in this V7 change before acting. Read every reused source file before
editing or importing it.

## Route Control

- Work on only one subroute at a time.
- Before an actual canary/development execute, create the complete plan and a
  read-only review JSON from a distinct reviewer context.
- Execute once, replay once, then make only the frozen gate transition.
- Preserve a failed route. Never adjust it or reuse its data.
- Stop immediately at the first development-ready result.
- If all routes fail/block, return `ladder_exhausted`; do not improvise R4.

## Tests

Use fresh `workspace/nbldpc_v7_<route>_<uuid>` roots and
`pytest -p no:cacheprovider`. T0 is compile/import/structure/tiny oracle; T1 is
focused unit/boundary/tamper; T2 is complete fake lifecycle and strict replay;
T3 is v5/v6 regression plus frozen-directory and source-hash audit. Test-only
execution must always pass an explicit fake runner.

## Forbidden Actions

- No changes to `src/`, `experiments/`, `tools/`, `results/`, v1-v6 source or
  evidence, existing outputs, or unrelated dirty-worktree files.
- No Git clean/reset/checkout, staging, commit, push, dependency installation,
  repository clone, or external source copying.
- No official `formal_ir_methods` v7 directory, confirmation, real data, N4,
  sidecars, `.ttbin`, or post-hoc gate changes.
- No parallel execution of two scientific routes.

## Return Conditions

Return only with either:

1. the first development-ready route, its immutable 16+16 package, strict
   replay, acceptance evidence, commands/results/hashes, and a statement that
   qualification remains unexecuted;
2. `ladder_exhausted`, with immutable evidence for every route; or
3. a concrete blocker including command, traceback, attempted remedies, and
   the single decision required.

## Suggested Prompt

```text
Read AGENTS.md and
openspec/changes/formal-nonbinary-ldpc-v7-successor-ladder/opencode-autonomous-packet.md
completely. Execute the V7 development ladder exactly as frozen, one route at
a time. Implement, test, independently review each plan, execute each eligible
canary/development exactly once, strict-replay exactly once, preserve failures,
and stop at the first development-ready route. Never run confirmation or real
data, create official outputs, rerun/tune sacrificed data, install dependencies,
clone repositories, stage, or commit. Return only under the packet conditions.
```

OpenCode provider policies may retain submitted content. Do not expose private
lab data, credentials, secrets, or confidential source to an unsuitable
provider. This packet requires synthetic data only.

