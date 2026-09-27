# M3-c: bounded real 2M u2 transfer diagnostic

## Why

M3-b's two accepted nested graphs had low Stage-1 non-exact counts on frozen synthetic frames, while M0 showed a real/synthetic proxy mismatch. A one-source real canary measures how these two graph instances decode the existing 2M eval frames before any broader route decision. Historical M0 m=204/208 results are not a matched-rate graph comparator for the new m=200 Stage-1.

## Scope

Add a fresh, fail-closed CLI and fake tests that reuse M0's exact read/alignment/split and source-keyed prior path, M3-a's saved graphs, and the frozen b2f decoder. Execute two graph instances sequentially only under `G-M3C-REAL-U2-2M` DECIDE gates. Stage-2 is triggered by posthoc Alice `u2` exact mismatch, so the output is explicitly an oracle-assisted development diagnostic. It provides no deployable verification or actual leakage claim. Preserve all old outputs and baselines.

## Affected behavior

New CLI, fake tests, compact cycle documents, and additive workspace roots only. No mutation of M0/M3-a/M3-b artifacts, `src/`, `experiments/`, `tools/`, `results/`, or `outputs_comparison/`.
