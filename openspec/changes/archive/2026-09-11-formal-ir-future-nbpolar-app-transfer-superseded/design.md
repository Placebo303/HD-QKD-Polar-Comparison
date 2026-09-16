# Design: NB-Polar APP Transfer and Conditional Rescue

**Lifecycle**: `BACKLOG_PLAN / IMPLEMENTATION_NOT_AUTHORIZED / EXECUTE_NOT_AUTHORIZED`

## 1. Transferable science

The future NB-Polar path SHALL reuse only these accepted semantics:

- `p_i(U1)=P(U1|B_i)` from the frozen empirical channel;
- upper-layer posterior `q_i(U1)` derived from disclosed constraints and Bob;
- lower-layer mixture
  `P_i(U2)=sum_u1 q_i(u1) P(U2|B_i,u1)`;
- exact/full recovery and verification separated;
- extra disclosure triggered only by public verification failure.

It SHALL NOT reuse LDPC `H1/H2/H_inc`, BP messages, graph labels, or claims.

## 2. Phase ordering

### Phase 0 — backend feasibility (decoder-free/synthetic)

Audit whether an existing comparison-layer implementation supports a q-ary
Polar transform over `GF(32)` or an equivalent 5-bit multilevel Polar code,
frozen-set construction, syndrome/frozen-symbol disclosure, and posterior or
list-derived symbol beliefs.  The sibling Polar Release remains read-only.

### Phase 1 — hybrid single-factor experiment

- Arm A: accepted NB-LDPC upper layer + NB-LDPC lower layer (reference).
- Arm B: NB-Polar upper layer producing `q(U1)` + the same frozen NB-LDPC lower
  layer and the same mixture.
- Optional diagnostic only: NB-Polar hard `U1_hat` transfer, preregistered and
  excluded from promotion gates.

Only the upper-layer code family changes.  Same frames, channel prior, lower
layer, verification, and total-disclosure accounting are mandatory.

### Phase 2 — Polar conditional disclosure

If Phase 1 retains a signal, freeze one rate-compatible Polar mechanism such as
additional frozen-symbol disclosure, incremental parity/CRC-compatible constraint,
or list-resolution information.  Compare fixed disclosure with verification-only
incremental disclosure.  No grid search.

### Phase 3 — full NB-Polar

Only after Phases 1/2: replace the lower layer with NB-Polar while preserving
the empirical conditional mixture and paired baseline.  This is a new change and
new authorization, not an automatic continuation.

## 3. Posterior contract

NB-Polar output SHALL be a normalized 32-state posterior or a reproducible
list-to-posterior approximation with declared temperature/normalization fixed
before outcomes.  Delta/hard one-hot output is not accepted as APP evidence.
No Alice truth may enter decoding priors; exactness remains an oracle metric only.

## 4. Metrics and gates

Report upper-layer exact, lower-layer exact, exact-full, detected/undetected
verification, disclosure per block/final exact, calls, list operations, runtime,
throughput, and memory.  Phase-1 terminal states:

- `NBPOLAR_APP_TRANSFER_SIGNAL`;
- `NBPOLAR_UPPER_WORKS_NO_NET_VALUE`;
- `NBPOLAR_NO_RETAINED_SIGNAL`;
- `NBPOLAR_BACKEND_NOT_READY`;
- `EVIDENCE_INVALID`.

A signal requires source-balanced full-exact performance within the frozen
baseline tolerance, zero undetected acceptance, complete disclosure accounting,
and no hard-decision substitution.  It is development evidence, not qualification.

