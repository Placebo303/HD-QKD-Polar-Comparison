# V72P2D5 G0 implementation candidate

```yaml
review_status: PENDING_INDEPENDENT_REVIEW
implementation_review: NOT_SELF_GRANTED
g0_execution_authorized: false
decoder_executed: false
cal_rows_read: 0
val_rows_read: 0
formal_output_created: false
```

This file records only the implementation handoff. The G0 packet remains the
source of truth for the tiny synthetic contract, the eight frozen seeds, the
historical decoder call parameters, the output schema, and the separate
execution gates. An independent reviewer must inspect the code and tests
before any G0 authorization record is created.

Implementation notes for review (not acceptance): the tiny fixture uses an
eight-cycle with check and variable degree two; one coefficient is 2 so the
all-ones cycle is not singular, and no degree-one check is passed to the
historical kernel. The exhaustive check explicitly enumerates the
``(U1, B, U2)`` states and compares the recovered ``P_F`` with
``P1(U1|B) * P2(U2|U1,B)``. The fake authorized test supplies its generated
fixture truth only to exercise the adapter; the adapter independently
recomputes the candidate syndrome. No claim is made that the historical
decoder will pass all eight seeds until a separately authorized G0 run.
