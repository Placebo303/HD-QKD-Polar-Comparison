# Proposal: Improve Formal Nonbinary LDPC v2

## Why

The immutable `nbldpc_formal_v1` N3 package is non-promoted: its selected policy achieved 18/32 verified successes at QSC p=.20 and 5/32 at p=.30, below the 31/32 gate. Its strict verifier was rendered unverifiable by post-run whole-worktree-status drift. The package and its confirmation data remain frozen: neither may be tuned, rerun, replaced, nor used as a selection oracle.

The smallest defensible successor is a new, independent synthetic development lane that first tests a bounded set of codebook/decoder candidates, then locks one candidate and a wholly fresh confirmation package. Real `.ttbin` work is deferred until that confirmation package is promoted.

## Scope

- Add `nbldpc_formal_v2` under the additive formal-IR layer; retain v1, `qldpc_reference`, Polar, and outputs.
- Compare only fresh sacrificed synthetic development data using a small, pre-registered codebook/decoder candidate set.
- Freeze fresh development and confirmation generation, selection, artifacts, scoped provenance, verifier, gates, and stop rules before creating a plan.
- Permit an N4 sidecar adapter design only after v2 synthetic promotion; a locked real-data run needs separate N4 review and authorization.

## Out of Scope

- Tuning, rerunning, repairing, or reclassifying v1 confirmation; changing its artifacts; or using `_test_only` replay as an official verifier pass.
- Real `.ttbin` processing, real-data claims, fair comparison, dependency installation, EMS/list-decoding, or production-performance claims.

## Affected Specs

- Add `formal-nonbinary-ldpc-v2`.

