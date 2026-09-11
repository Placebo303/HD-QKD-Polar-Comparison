# D6 R1d execution-packet addendum A1 — BP provenance compatibility (NOT authorized)

Status: `R1D_PRE_EXECUTE_STALE_SUPERSEDED_AFTER_REPAIR_NOT_AUTHORIZED`.
This addendum authorizes nothing: no R1d execution, rerun, resume,
`--phase`, G1/G2, VAL, or real/raw data. No R1d root was created (and none
may be created under this addendum). All authorization keys remain false.

## 1. Prior Pre-EXECUTE is stale

`D6_GRAPH_MOTHER_PRE_EXECUTE_REVIEW_R1D.md`
(`D6_R1D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`) reviewed
code that:

- unpacks five values from `_decode_block` while the accepted BP interface
  returns six including provenance
  (`scripts/v72p2d6_graph_mother_development.py:126`), so every decoder
  cell under the accepted interface raises `ValueError` into the broad
  worker `except` (L132–135) as a crash row (reproduced R01, fake only);
- forwards L1 beliefs via `softmax(bel)` → `d5.app_fed_l2_prior` with no
  provenance check (`run_cell`, L778–793), so a `PRIOR_ONLY` return would
  silently feed L2 as APP evidence.

That verdict therefore no longer describes the code and is superseded. It
is retained as history; no claim, selection, or terminal may cite it as a
live readiness verdict.

## 2. Repair freeze (Track A R02)

`openspec/changes/v72p2d6-r1d-bp-provenance-compat/` freezes exactly:
six-value unpacking + provenance IPC transport; `CHECK_UPDATED` required
before APP mixing (accepted `require_check_updated_provenance` helper);
prior-only/missing/unknown/warm → named fail-closed cell, never crash,
never L2 APP decode; warmup ready=false on incompatible shape; no
scientific arm/seed/rows/mother/schedule/estimator/threshold/budget/
terminal change; `DECODER_FIELDNAMES` unchanged; A2 roots immutable.

## 3. Renewed readiness gate

R1d readiness requires, in order: repaired implementation + focused fake
tests (R03–R04), independent implementation review R05
(`D6_R1D_BP_COMPAT_IMPLEMENTATION_REVIEW_PASS/FAIL`), renewed Pre-EXECUTE
R06 (`D6_R1D_PRE_EXECUTE_REVIEW_PASS_BP_COMPAT_A1_AWAITING_EXPLICIT_AUTHORIZATION`),
then a separate explicit main-thread execution authorization (NOT granted
here or anywhere in Track A R01–R04). R1d remains
`PAUSED_OPTIONAL_LOCAL_CONFIRMATION_NOT_MAINLINE_GATE` throughout.
