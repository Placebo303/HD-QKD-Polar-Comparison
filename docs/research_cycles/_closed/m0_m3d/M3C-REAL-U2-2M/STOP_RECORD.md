# M3C terminal record — 2026-09-27

**Disposition: STOP; two-arm diagnostic not accepted.** R1 completed, but R2 reached the frozen internal wall limit during Stage 2. The one-shot `DECIDE` packet prohibits retry/resume or tuning. Both arm roots and the append-only family `execution.jsonl` are retained. No two-graph performance decision, full-protocol claim, leakage/f, SKR, P3/G0B verdict or publication number follows from this packet.

## Execution and machine evidence

| arm | process exit | terminal | final dispositions | Stage-1 nonexact | Stage-2 attempted / rescued | wall / peak RSS |
|---|---:|---|---:|---:|---:|---|
| M3C-R1 | 0 | `COMPLETE` | 383/383 | 39 | 39 / 28 | 4813.20 s / 0.7281 GiB |
| M3C-R2 | 1 | `INCOMPLETE-wall` | 359/383 | 41 | 18 / 10 | 5280.0024 s / 0.7286 GiB |

The R1 rows have 344 Stage-1 exact frames; Stage-2 attempted exactly the 39 Stage-1 nonexact indices, leaving 372 final u2 successes and 11 failures. Its full10 field is report-only: 168 mismatches among 372 final-u2-success frames. R1's 383-frame FER/Wilson fields are present in its machine artifact, but this stopped two-arm packet does not promote them to a cross-arm conclusion.

R2 completed Stage 1 on all 383 frames: 342 exact, 41 nonexact. Of 18 Stage-2 attempts, 17 returned (10 rescued, 7 remained nonexact); Stage-2 frame 160 was interrupted after 3.792049 s by the remaining-wall alarm. The other 23 Stage-1 nonexact frames were never attempted. Final outcomes are therefore 352 success, 7 failure and **24 unknown**; `processed_n=359`. R2 reports **no** 383-frame FER, Wilson interval, or complete Stage-2-set equality. Its full10 field is separate: 150 mismatches among 352 known final-u2-success frames. Stage-1 and Stage-2 undetected counts are zero in both arms.

R2 `execution.jsonl` has 401 `DECODE_START` events, 400 `DECODE_RESULT` events, one `DECODE_TIMEOUT` on Stage-2 frame 160, then a `TERMINAL` event; no retry or next frame follows. The recorded 5280.002407 s includes a 2.4 ms stop/flush tail beyond the nominal 5280 s internal timer, while the external 5400 s cap was met and terminal artifacts were retained. The source/prior/graph metadata remained pinned; protected output trees were not written.

## Independent read-only terminal audit and claim gate

An independent `luna_worker` recomputed both arms from `rows.json`, CSV, Markdown, resource summaries and the event log and returned **PASS for truthful STOP retention**. It confirmed the R1 Stage-2 set equality, R2 partial-set/unknown accounting, full10 isolation, zero undetected counts, retained timeout row, absence of R2 FER/Wilson, and no claim promotion in the scoped artifacts. This was a terminal-evidence audit, **not** a Pre-RESULT acceptance review. Because R2 is incomplete, M3C-05 cannot proceed under the frozen packet.

The active follow-up automation `m3c-real-u2-run-follow-up` was deleted after terminal status. No arm was rerun, no graph was rebuilt, and no further real decoder execution is authorized by this packet. Any successor needs a new frozen question, cost budget and authorization gate; the observed partial R2 rows must not be used as an accepted FER denominator.
