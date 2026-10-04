# POSTHOC replay delta

## ADDED Requirements

### Requirement: truthblind counterfactual profile
The replay SHALL rank the six guesses from stored all32-softmax beliefs at the accepted selected variable, then choose within fixed top1/2/3/6 subsets by original-prior score without truth. k6 SHALL reproduce each parent's accepted candidate. It SHALL count shared baselines plus every retained attempt in logical costs, use zero decoder/sampler calls, reference actual vectors, preserve two parents separately and label output posthoc counterfactual rather than fresh performance/throughput/promotion.

#### Scenario: empty restricted valid set
WHEN no topk branch is syndrome-valid THEN retain that pair's baseline failure vector.

#### Scenario: accepted-output inconsistency
WHEN parent identity/maps or k6 replay mismatch THEN STOP with retained evidence and no repair/rerun.
