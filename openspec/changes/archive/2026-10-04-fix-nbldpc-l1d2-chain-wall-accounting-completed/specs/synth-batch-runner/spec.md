# Delta: single-chain timing for future L1D2 batches

Track: DECIDE. This delta changes future runner measurement only and grants no
execution. The completed n128 machine root remains immutable.

## MODIFIED requirements

- The existing 24-column frame schema SHALL retain its order. `wall_s` SHALL
  contain the elapsed time of that **attempted complete layered chain** (L1,
  any invoked L2, transfer and verification), measured around that arm of the
  pair. A pair elapsed time SHALL NOT be copied into both chains'
  `wall_s` fields.
- A new manifest `pair_timings` diagnostic MAY record the total elapsed time
  and actually attempted arms for each started pair. It SHALL NOT replace the
  per-chain frame `wall_s` or decide the single-chain cap; the old n128
  manifest SHALL remain untouched.
- The frozen `single-chain≤120s` cap SHALL apply to each attempted chain,
  while the `wall≤7200s` cap SHALL retain its existing `execute_pairs` batch
  timing boundary from the current `t_batch` start through the decode loop;
  model/prior/graph setup and STOP-result persistence are outside this clock.
  Once batch elapsed time reaches the 7200 s cap, the runner SHALL STOP before
  starting another chain; an unattempted chain SHALL have no frame row.
  A synchronous layered chain SHALL be classified after return;
  an over-cap chain SHALL
  produce `resource_abort` and a STOP with its attempted disclosure retained.
- If the first chain breaches its cap, the paired second chain and later pairs
  SHALL NOT start. An unattempted chain SHALL have no frame row and SHALL NOT
  contribute a success, failure or disclosure count. The stopped batch SHALL
  remain incomplete and SHALL NOT enable conditional n256 entry.
- Non-resource pair/exact, syndrome, accepted-wrong, blocked-transfer,
  disclosure, seed, prior, graph, decoder, output-root and authorization rules
  SHALL remain as frozen in the completed Stage-2 contract.
