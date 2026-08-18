# Proposal: formal-nonbinary-ldpc-v22-structured-construction

> Status: CONCLUDED_CURRENT_KERNEL_NEGATIVE_PENDING_ARCHIVE.

## What was evaluated

V22 added structured DE harnesses and V22b, which raised the executable check
degree cap to 512. It evaluated selected plain/irregular and inherited SC-LDPC
profiles, including q=1024 on the V17 structured channel near rate 0.9375.

## Conclusion

The tested target-rate candidates did not converge under the current V22b
kernel and recorded budgets. This is a negative result for those candidates,
not a proof that all single-edge profiles, protographs, MET ensembles, or
q=1024 codes are impossible.

## Cancelled finite branch

The proposal originally allowed finite construction only after DE PASS. No
target DE candidate passed, so finite I03/E02 and the Bob-only semantic
verifier were not run. They are `CANCELLED_BY_DE_GATE`/`NOT_RUN`, not
completed.

## Claim and archive boundary

Highest claim: `diagnostic_only` and
`CONCLUDED_CURRENT_KERNEL_NEGATIVE_PENDING_ARCHIVE`. Actual archive movement
requires independent read-only review and explicit user authorization.
