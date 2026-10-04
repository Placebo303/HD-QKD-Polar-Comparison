# Proposal: standardize the review-to-next-packet loop

## Why

Research operator returns currently rely on conversation context to decide
whether the main thread should review the result and what handoff comes next.
Task packets and their companion prompts are used consistently in practice,
but their types, location, names, and default continuation rule are not stated
in the repository SOP.

## What changes

- Make proportional main-thread review the default response to every completed
  or blocked operator return.
- After that review, create the next appropriate task packet and a paired,
  directly usable prompt unless the route is terminal, blocked on a user
  scientific decision, or awaiting explicit execution authorization.
- Standardize packet types, storage location, paired naming, revision and
  supersession rules.
- Keep independent review gates proportional to scientific risk; this change
  does not require duplicate independent review of every small task.

## Scope

- `docs/research-cycle-sop.md`
- this OpenSpec change

No production code, scientific threshold, execution authority, or existing
packet is changed.
