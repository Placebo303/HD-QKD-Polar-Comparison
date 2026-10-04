# Research-cycle handoff delta

## ADDED requirements

### Requirement: completed returns enter review before continuation

For every operator `COMPLETE` or `BLOCKED` return, the main thread SHALL review
the scoped evidence against the active packet before accepting the result,
changing the route, or delegating more work.

### Requirement: next handoffs are paired

After review, the main thread SHALL normally create both a complete task packet
and its directly usable companion prompt. It SHALL omit or pause the next pair
only when the route is terminal, a concrete blocker remains, an explicit user
scientific decision is required, or execution requires fresh user authority.

### Requirement: standard location and naming

New operational handoff pairs SHALL live under `.workbuddy/tasks/` and SHALL
share a stem of the form `<CYCLE>_<STAGE>_<ACTION>_<REV>`, followed by
`_TASK_PACKET.md` and `_PROMPT.md` respectively. Existing historical packets
MAY retain their names.

### Requirement: authority remains external to prompts

A packet or prompt SHALL NOT grant claim-bearing/formal execution authority.
When explicit user authorization is required, the pair may prepare or review
the execution but must stop before invocation.
