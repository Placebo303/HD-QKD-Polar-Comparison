# Proposal: NB-Polar APP Transfer and Conditional Rescue

**Lifecycle**: `BACKLOG_PLAN / IMPLEMENTATION_NOT_AUTHORIZED / EXECUTE_NOT_AUTHORIZED`

## Why

The NB-LDPC line established three reusable mechanisms: empirical full-Bob
multilevel posteriors, syndrome-derived soft APP transfer, and verification-only
conditional disclosure.  These are decoder-family-independent and may improve a
future non-binary Polar route.  The LDPC graph/matrices and their evidence do not
transfer.

After the NB-LDPC comparison closes, evaluate the lowest-risk hybrid first:
NB-Polar reconciles the upper layer and supplies `q_i(U1)`; the accepted NB-LDPC
reconciles the lower layer using the same APP mixture.  A full NB-Polar stack is
conditional on the hybrid producing a valid signal.

## Scope

- Freeze `d=1024`, `N=1024`, `[5,5]`, empirical channel, samples, disclosure
  semantics, verification, and current NB-LDPC lower-layer baseline.
- Add one NB-Polar upper-layer encoder/decoder capable of returning normalized
  posterior/path beliefs, not only a hard estimate.
- Compare APP transfer with a hard-decision control on identical blocks.
- Add rate-compatible/incremental Polar disclosure only after the fixed-rate
  APP-transfer experiment passes.
- Consider full NB-Polar `U1+U2` only as a later conditional phase.

## Non-goals

- Do not modify the frozen Polar Release checkout or claim its binary Polar
  results implement NB-Polar.
- Do not port LDPC parity matrices or call an LDPC result Polar evidence.
- Do not jointly tune kernel, list size, frozen set, rate, mapping, and rescue.
- No implementation or decoder run in this backlog turn.

## Entry gate

Implementation requires an accepted NB-LDPC/V62 result, an explicit user go,
and a decoder-free feasibility review of the available q-ary Polar backend.

