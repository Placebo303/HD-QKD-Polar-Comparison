# Design

## Default loop

The main thread treats an operator return as an input to review, not as an
accepted terminal report. It checks the frozen acceptance items and evidence
in proportion to risk, records an acceptance/rework/blocking decision, and
then emits the next bounded handoff.

The next handoff is always a pair:

1. a complete task packet containing the contract;
2. a short prompt pointing to that packet and defining operator autonomy and
   return conditions.

The loop pauses when new user authority or a route-changing scientific choice
is required. A prompt must never manufacture that authority.

## Naming

New files use one shared stem:

`<CYCLE>_<STAGE>_<ACTION>_<REV>`

and the suffixes `_TASK_PACKET.md` and `_PROMPT.md`. Components use uppercase
ASCII letters, digits, and underscores. Existing historical names remain
valid and need not be renamed.

## Storage

Operational handoff pairs live in `.workbuddy/tasks/`. Durable scientific
contracts, reviews, returns, and results remain in OpenSpec and
`docs/research_cycles/`; the workbuddy packet is not a substitute for either.

## Review proportionality

The main-thread review is always performed. A separate independent reviewer is
used at frozen-plan acceptance, risky implementation acceptance, Pre-EXECUTE,
and Pre-RESULT gates, or when the packet explicitly requires it. Low-risk
documentation and mechanical closeout may use the main-thread review alone and
be batched into the next milestone review.
