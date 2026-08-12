# Proposal: Formal Nonbinary LDPC v4 Incremental Redundancy

## Why

The immutable v3 covered-layered package passed development readiness and
strict replay but missed synthetic promotion by one p=.30 confirmation frame:
32/32 at p=.20 and 30/32 at p=.30 against 31/32 gates.  Both misses were
`decode_failed` after the fixed 40-check, 12-iteration decoder; there were no
prohibited failures.  This does not authorize tuning or rerunning v3.

The smallest attributable successor is a new method that keeps the verified
v3 GF(1024) codebook and layered FFT-QSPA, then discloses exactly one further
eight-row syndrome prefix after a bounded first-stage failure.  Warm-state and
restart recovery are compared only on wholly fresh development data.

## Scope

- Add independent method `nbldpc_formal_v4_ir` without modifying v1-v3.
- Reuse and reconstruct the exact v3 24/32/40/48 codebook identity.
- Compare exact-v3 control, one warm incremental-redundancy policy, and one
  restart incremental-redundancy policy.
- Add exact two-stage transcript and disclosure accounting, fresh isolated
  development/confirmation data, and strict read-only replay.
- Target observed 128/128 confirmation success independently at p=.20 and
  p=.30; do not describe this finite observation as FER=0.

## Out of Scope

- New base-graph or edge-label search, EMS/list/neural/ADMM decoding, external
  decoder dependencies, v3 reruns, existing confirmation analysis, real
  sidecars/raw `.ttbin`, N4, or a method-comparison claim.

## Affected Specs

- Add `formal-nonbinary-ldpc-v4-ir`.
