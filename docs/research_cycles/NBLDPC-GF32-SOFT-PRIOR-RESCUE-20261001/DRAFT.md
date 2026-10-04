# Single-symbol soft-prior restart — EXPLORE candidate

DRAFT ONLY: not frozen, not implemented, not executed. This document is not
an execution authorization. A complete packet/seed plan/OpenSpec and independent
review must precede a fresh one-shot batch under the ongoing user grant.

## Mechanism and nearest evidence

Retain the accepted six DV2 deep matrices from source batch UUID
a9352bc1-ae56-443b-ae93-9dcfa85d4229; retain matched synthetic PMF and cold
v35 row-layered BP90/alpha1. Use a new, frozen and disjoint holdout seed plan.
Control is baseline BP; candidate reuses that same baseline call and attempts
bounded rescue only when the actual returned vector fails its own syndrome.
Truth must never affect whether to rescue, variable selection or output choice.

Failed v35 calls return final_beliefs (CHECK_UPDATED approximate log-beliefs),
so a new call can support uncertainty-guided selection without another
baseline run. Old artifacts do not persist beliefs: never recover them by
rerunning consumed batches. Entropy of these beliefs is a heuristic, not a
calibrated posterior. Candidate variable rule to freeze: maximum entropy
among variables adjacent to violated checks, deterministic lowest-column tie.

Try six original PMF-support values {0,1,3,7,15,31} in ascending order.
For each copy the original prior and replace only the selected variable row
by one-hot; call cold BP90 with the same H and same public syndrome. v35 floors
zeros to1e-15 and continues message updates, hence this is a strong SOFT-prior
restart, not hard clamping or an oracle. Record guessed value and final value.
Choose a syndrome-valid branch by highest whole-vector ORIGINAL prior score,
with deterministic tie rule; if none is valid retain the baseline failure.
Selection must not inspect truth. Baseline-valid output passes through.

## Costs and evaluation to freeze

Six graphs x32 new frames =192. Physical calls192+6F (F baseline syndrome
failures), worst1344; using the historical F48 only as planning estimate would
give480, not a promise or a fresh measurement. Budget proposal1800s/4GiB,
per-call90 iterations; no graph/label/OSD work. Capture baseline beliefs, all
actual branch vectors, selected-variable rule, likelihoods and selection maps.
Separate physical executed cost from standalone control/candidate pipeline
cost: shared baseline time is not two physical calls.
Logical control calls=192; standalone candidate calls=192+6F. With shared
baseline the physical calls=192+6F; independently running both pipelines
would cost384+6F (672 if F48). Choose and freeze one execution design.

Reuse the same syndrome within each candidate pipeline; internal restarts
produce no additional syndrome disclosure. Explicitly freeze method-level
260 bits/frame PER METHOD PIPELINE (paired benchmark arms520 bits/frame),
tag0/verification NOT_IMPLEMENTED/undetected NOT_MEASURED;
do not count each internal BP call as fresh public disclosure. No security
or f_eff claim follows from that accounting.

Report baseline/candidate exact, syndrome-valid-wrong and syndrome failures
separately, paired and per-graph gains, actual wall/iterations and rescue costs.
A predeclared outcome must distinguish exact recovery gain from extra wrong
valid candidates; no "syndrome satisfied => success" shortcut. Thresholds,
selection ties, partial-state retention and full fake matrix remain to freeze.

## Why this is a testable hypothesis, not an established gain

MRB-TOP6 enumerated symbols without rerunning BP and gained no exact recovery;
each arm had41 valid-wrong outputs (1 passthrough+40 wrong rescues). A separate
MRB rescue had candidate43 wrong rescues against control0. This new treatment
changes the BP trajectory through one altered soft prior, but those findings
make valid-wrong selection a central risk. Current evidence supports testing
the difference, not asserting improvement. No route closure, real data,
n256, qualification or publication; no old root overwrite or scientific rerun.
