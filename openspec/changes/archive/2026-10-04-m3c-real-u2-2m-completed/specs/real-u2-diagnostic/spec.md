# Real u2 diagnostic delta

## Requirement: bounded real transfer canary

The M3-c command SHALL use the M0 2M VAL+HOLD real-frame loader and same-source TRAIN prior, exactly 383 n=1024 frames, and one selected accepted M3-a graph per arm. It SHALL decode the 200-row prefix cold and the 208-row full graph cold only for Stage-1 u2 mismatches. It SHALL record that the rescue trigger uses posthoc Alice truth and SHALL never present that result as a deployable verification protocol.

## Requirement: report semantics

Each COMPLETE arm SHALL separately report all 383 frames' Stage-1 and final u2 exact outcome, Stage-2 attempt/rescue, per-stage undetected and full10 argmax observation, denominator, Wilson interval, wall/RSS, graph/source/prior identity, and failures; its Stage-2 set SHALL equal its complete Stage-1 non-exact set. An incomplete arm SHALL retain stage rows, the number of frames with final disposition, and stop reason without an accepted 383-frame FER/Wilson point or complete-set equality claim; an interrupted Stage-2 frame has no final disposition. It SHALL NOT derive actual leakage, f, SKR, qualification, method-family ranking, or full-symbol success from these oracle-assisted outputs.

## Requirement: safety gates

The command SHALL require two execution flags, a fresh direct-child workspace root, the frozen graph/data/bundle checks, focused fake tests and DECIDE Pre-EXECUTE. It SHALL retain an incomplete run and stop on frozen input, structural, output collision, or resource gate failure; it SHALL NOT retry/resume or overwrite historical roots.
