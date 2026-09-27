# M3-b paired synthetic test of nested 200+8 graphs

## Why

`G-M3A-CONSTRUCT` established structural feasibility for two independently built degree-2 200-row bases plus eight appended rows. It measured no decoder performance. The accepted P1 Stage-1 batch used the same two construction seed labels and 240 synthetic frame seeds but truncated a separately constructed A208 graph, leaving degree-0/1 variables in its leading 200 rows. A matched-frame diagnostic can test whether the new base changes Stage-1 failures and final cold-rescue outcomes.

## Scope

Add a small M3-b adapter that reads the two accepted M3-a JSON graph artifacts and wires them to the existing P1 Stage-1 decode core. Run two frozen synthetic arms only after a new Pre-EXECUTE. Preserve P1's old roots, runner defaults, decoder, channel bundles, and original results. Persist truthful M3-b graph provenance in every new result. The successor counts rescue disclosure on **attempted** rescues: P1's `expected_leak_for(rescued)` undercounts when a rescue is attempted but fails (historical R1: attempted 84, rescued 83). Preserve the old P1 numbers as historical records; any corrected comparison must be separately reviewed. This is EXPLORE_HEAVY and diagnostic only; it neither evaluates the suspended M2 D2 branch nor makes a real-data or publication claim.

## Affected behavior

New `comparison_bench` CLI/test and, only if essential for truthful graph provenance and fresh-root routing, optional parameters in `p1_stage1_runner.py` whose defaults reproduce the old P1 path exactly. No changes to `src/`, `experiments/`, `tools/`, original P1 outputs or data bundles.
