# V35R1 corrected nonbinary algorithm-development report

**Date**: 2026-08-24  
**Implementation**: `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`  
**Runner**: `comparison_bench/src/comparison_bench/cli/run_v35_algorithm_development.py`  
**Authoritative development data**: `comparison_bench/outputs_comparison/nonbinary_diagnostics/v35_algorithm_development/run_02/`

Corrected bounded status:

- **`V35R1_A1_A3_RUN_COMPLETE`**
- **`PROTOCOL_PARTIAL_A4_NOT_EXECUTED`**
- **`NO_NB_CANDIDATE_FOR_TESTED_HAND_DESIGNED_CONFIGURATION`**
- **`SCIENTIFIC_PROMOTION_NOT_GRANTED`**

`run_01` is invalid and explicitly withdrawn by its
`RUN_STATUS_INVALID.md`. All numbers below are recomputed from `run_02`.

## Scope

V35R1 used 15 development blocks: 1M seeds `350101..350105`, 1p5M
`350201..350205`, and 2M `350301..350305`. It compared three schedules on the
true V31 baseline, one hand-designed mixed-degree graph, and cold-start nested
syndrome stages through +160 bits.

The original V35 OpenSpec required A4 binary MLC when A3 failed. A4 was not
executed in corrected `run_02`. Therefore V35R1 is not a completed four-route
`NO_CANDIDATE_SUCCESS` result and contains no binary-MLC evidence.

## Directly recomputed results

`v35_algorithm_development_blocks.csv` contains 120 records, zero exact L2
recoveries and zero recorded false accepts.

| Stage/method | Records | Final errors mean | Median | Exact |
|---|---:|---:|---:|---:|
| V31 flooding | 15 | 175.93 | 179 | 0/15 |
| V31 layered | 15 | 175.93 | 179 | 0/15 |
| V31 damped layered $\alpha=0.5$ | 15 | 175.93 | 179 | 0/15 |
| Hand-designed graph S0 (A2 records) | 15 | 245.87 | 247 | 0/15 |
| Hand-designed graph S0 (A3 records) | 15 | 245.87 | 247 | 0/15 |
| Hand-designed graph S1 (+40 bits) | 15 | 245.40 | 247 | 0/15 |
| Hand-designed graph S2 (+80 bits) | 15 | 245.40 | 247 | 0/15 |
| Hand-designed graph S3 (+160 bits) | 15 | 245.40 | 247 | 0/15 |

The three V31 schedules produced the same final residual on every development
block. That is bounded evidence of no observed schedule advantage here, not a
general proof of schedule equivalence.

The hand-designed graph worsened mean residual by about 69.93 errors relative
to V31. Incremental cold-start checks changed the mean by less than one symbol
and produced no exact recovery. These results close only this hand-designed
configuration.

## Graph and protocol limitations

- The lifted 192-row graph passed its recorded construction checks, but the 1M
  path used a row prefix with different realized finite structure. V35 did not
  test a source-native empirical-P-optimized irregular graph or a true MET
  ensemble.
- A4 was skipped despite the original conditional-A4 requirement. The original
  all-route terminal cannot be claimed.
- The finite screen is an oracle-L1 L2 diagnostic because the posterior is
  conditioned on true Alice `x1`; it is not Bob-only end-to-end reconciliation.
- Zero recorded false accepts is useful bookkeeping, but it does not convert a
  0/15 exact development result into a security or qualification result.

## Claim ledger

### Supported

- On these 15 development blocks, flooding/layered/damped V31 schedules ended
  with identical residuals.
- The tested hand-designed graph was substantially worse than the V31
  baseline, and +160 bits of its tested cold-start incremental checks did not
  produce exact recovery.
- V35R1 found no NB candidate for this hand-designed configuration.

### Unsupported

- General failure of NB-LDPC, empirical-P irregular graphs, MET, or rate
  adaptation.
- Any binary-MLC result.
- Bob-only FER, qualification, promotion, or net-key performance.
- Causal claims that one graph property alone explains all failures.

## Next decision

V36 subsequently tested one empirical-P-selected low-average-degree graph and
is documented separately. Its corrected status must be read from
`docs/nbldpc-v36-empirical-graph-development.md`; it does not retroactively
promote V35R1.

