# Frozen Phase 2 Performance Correction

## Problem

Production prepare cannot complete within 30 minutes because strict public
payload replay calls deterministic `matrix_for()` once per frame and plane,
reconstructing the same selected matrices thousands of times. No production
plan or output directory was created by the terminated attempts.

## Allowed Change

- Do not modify `formal_ir/codebook_v4.py`: its source hash is part of the
  frozen development prerequisite.
- In the new 16 dB runner, add a temporary replay-cache context that wraps the
  exact `matrix_for()` reference used by the synthetic public-payload
  verifier. Cache at most the 40 deterministic `(plane_id, candidate_id)`
  matrices, return a detached writable copy, and restore the original
  reference in `finally`.
- In the same context, wrap the exact `candidate_entry()` reference imported
  by the frozen development verifier with a 40-entry deep-copy cache.
- Replace the frozen development verifier's imported `_rows()` only within the
  context with a semantically identical linear parser that splits canonical
  CSV bytes once, rather than once per row. It must preserve all schema, bool,
  numeric, finite-runtime, and byte-for-byte row canonicality checks.
- Use the same temporary context around 16 dB public-payload reconstruction.
- Do not change seeds, matrices, canonical bytes, manifests, diagnostics,
  selection, decoder behavior, or evidence.
- Include `codebook_v4.py` and `ldpc_v4_channel.py` in the 16 dB scoped source
  hash map and exact plan validation.

## Acceptance IDs

- **P2P-01**: All 40 cached matrices are byte-identical to uncached
  `generate_candidate(...)[0]`.
- **P2P-02**: Mutating one `matrix_for()` result cannot affect a later call.
- **P2P-03**: Repeated calls for one identity invoke the original deterministic
  reconstruction once per replay context; cache is bounded to 40 identities
  and the original verifier reference is restored after normal or exceptional
  exit.
- **P2P-03A**: The linear development CSV parser returns exactly the same
  typed rows as the frozen parser on canonical fixtures and rejects each
  malformed/noncanonical fixture accepted by neither implementation.
- **P2P-04**: Candidate manifest and all historical artifact hashes remain
  unchanged.
- **P2P-05**: 16 dB focused T0-T2 and v4 codebook/formal regression pass.
- **P2P-06**: A strict read-only replay of the promoted synthetic prerequisite
  completes without decoder reexecution and reports promoted.

No production prepare/execute is permitted during this correction.
