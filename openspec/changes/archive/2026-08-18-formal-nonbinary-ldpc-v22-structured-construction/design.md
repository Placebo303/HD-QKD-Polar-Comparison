# Design: formal-nonbinary-ldpc-v22-structured-construction

## Status

CONCLUDED_CURRENT_KERNEL_NEGATIVE_PENDING_ARCHIVE.

## Implemented gate-first path

1. Reused plain/structured and inherited SC-LDPC DE paths.
2. Added V22b with configurable degree cap, exercised up to 512.
3. Evaluated selected q=1024 candidates, including V17 structured channel at
   target rate approximately 0.9375.
4. Stopped before finite construction because no tested target candidate
   passed the DE convergence gate.

Low-QSC p=0.05 SC convergence is retained only as a mechanism/control result;
it is not convergence on the target V17 channel/rate.

## Scientific boundary

V22 establishes only that the **tested candidates under the current kernel and
budgets** were negative. It did not perform bounded full `lambda/rho`
optimization and did not test true MET. It cannot support a global route
impossibility claim.

## Cancelled work

- finite construction: CANCELLED_BY_DE_GATE;
- finite Bob-only FER and `f_total`: NOT_RUN;
- Bob-only runtime semantic verifier: NOT_RUN.

The cancelled tasks cannot be relabelled completed during archive closeout.
