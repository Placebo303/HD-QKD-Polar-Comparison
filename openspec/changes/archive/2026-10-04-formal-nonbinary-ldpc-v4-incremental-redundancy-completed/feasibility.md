# Feasibility: Nonbinary LDPC v4 Incremental Redundancy

## Repository evidence

- The v3 mother matrix already exposes exact nested prefixes
  `mother[:24]`, `mother[:32]`, `mother[:40]`, and `mother[:48]`.
- Every prefix is reconstruction-bound, full GF(1024) row rank, has zero
  4-cycles, covers all 64 columns, and passes the frozen no-weight-1/2 proxy.
- Dense decoder storage is 4,456,448 bytes at 40 rows and 5,505,024 bytes at
  48 rows, below the existing 24 MiB cap.
- The current v3 function keeps beliefs and check messages in local variables
  and returns no resumable state.  Warm continuation therefore requires a new
  v4 state machine; it cannot be emulated by calling v3 twice.
- The 48-row support graph contains many 6/8-cycles.  Zero 4-cycles is not a
  trapping-set guarantee, so codebook optimization remains a conditional
  successor rather than a claim about this route.

## Feasibility decision

**GO** for a separate v4 lane that reuses the v3 codebook.  This isolates the
effect of eight additional syndrome symbols and warm versus restart recovery.
Do not simultaneously change the codebook, prior, GF representation, damping,
or check update.

The fixed implementation shall keep at most one 48-row state in memory.
Stage 1 processes the initial prefix.  Warm recovery retains its old messages,
initializes only new-row messages uniformly, recomputes beliefs consistently,
and then scans every active row in ascending order.  Restart recovery discards
the old state and initializes the complete final prefix from the same Bob
prior.  State is never serialized into evidence.

## Runtime feasibility

A prior non-qualification 40-row/12-iteration probe took about 3.9 seconds,
while immutable v3 failure rows recorded roughly 16-18 seconds under the
formal execution environment.  Before any official plan, main-thread
acceptance must run the fixed-seed non-qualification cost probe to decide
whether execution is operationally practical.  Wall time cannot change a
formal status because it cannot be reproduced under strict replay; deterministic
iterations, calls, rows, events and memory are the resource gates.

## Conditional second route

Start a separate optimized-codebook change only if both IR policies miss the
new development readiness gate through ordinary `decode_failed` or
`verify_failed` outcomes after completing the 48-row stage.  That future
route must jointly optimize every prefix using at least exact 6/8-cycle
counts, ACE/EMD or generalized girth, an active-subgraph trapping proxy, and a
bounded low-weight search.  It must use new data again.

## Audit note

One read-only planning agent inadvertently opened an existing policy manifest
whose payload included confirmation material.  No material values were
returned to the main thread or used in any policy, root, gate, or parameter
decision.  The agent's confirmation-related observations are excluded.  The
structural facts above are independently reconstructible from source and the
canonical codebook contract.
