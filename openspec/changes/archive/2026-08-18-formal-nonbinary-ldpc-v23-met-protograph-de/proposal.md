# Proposal: formal-nonbinary-ldpc-v23-met-protograph-de

> Historical directory name retained. Status:
> CONCLUDED_SINGLE_EDGE_DIAGNOSTIC_PENDING_ARCHIVE.

## What was actually implemented

V23 accepted a base matrix, derived aggregate edge-perspective `lambda/rho`
from its variable/check degree counts, and called the V22b single-edge DE
kernel. This erased base-matrix position/topology and maintained no edge-type
state.

Accordingly, V23 did **not** implement topology-preserving protograph DE and
did **not** implement MET/multi-edge DE, despite the historical change name.

## Observed diagnostic

The evaluated aggregate single-edge profiles did not converge on the q=1024
V17 structured channel near rate 0.9375. The raw `scan.json` package contains
three matrices. A consolidated summary later lists additional regular and
simple irregular points, but those additional points lack matching independent
raw and verifier packages. They are summary-only diagnostics and must not be
presented as independently verified scan coverage.

## Claim and archive boundary

V23 supports only `CONCLUDED_SINGLE_EDGE_DIAGNOSTIC_PENDING_ARCHIVE` for the
recorded candidates/current V22b kernel. True MET remains untested. Actual
archive movement requires independent read-only review and explicit user
authorization.
