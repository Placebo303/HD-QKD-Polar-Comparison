# P0 operator return R1 — 2026-09-07 (record only, NOT_INTERPRETED)

## Command (verbatim intent from the frozen packet)

Frozen guarded command:
`time timeout -k 30 1500 python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost`

Executed on this machine (Windows; `time` unavailable and bare `timeout`
resolves to Windows timeout.exe, which lacks `-k`/124 semantics; GNU timeout
from Git for Windows used so the OQ-P0-2 guard is real; wall time measured
around the guarded process):
`& "C:\Program Files\Git\usr\bin\timeout.exe" -k 30 1500 python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost`
Guarded argv after `timeout -k 30 1500` is exactly the frozen command.
Watchdog rehearsal this session: exit 124.

## Exit code and wall time

```
exit=3
wall_s=0.3759348
```

## Literal stdout

```
phase 'p0-cost' refused: MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS: D4R2 F-model CAL-TRAIN canonical counts (1024,1024) + P(B) marginal on CAL702..1725 TRAIN
```

## Literal stderr

(no separate stderr lines captured beyond the line above; the refusal line is
the complete process output.)

## Output root listing

```
exists False
---LIST---
ABSENT
```

Statement: `workspace/v72p2d5_p0_cost/20260906_r1/` is absent. The refused
phase created no output root and no files.

## Literal cost scalars

No `results.json` exists (`NO-RESULTS-JSON`). Therefore there are no scalars
to quote:

- `decoder_calls`: (absent — no results.json)
- per-record `f` / `kind` / `wall_s` / `iterations` / `rss_bytes`: (absent)
- `projected_g1_s`: (absent)
- `projected_g2_s`: (absent)
- `projection_blocked`: (absent)
- `passed`: (absent)

## Decode-attributed total vs the 1440 s cap (OQ-P0-1)

No decoder ran (refusal before any work; wall 0.3759348 s of process time,
zero decode-attributed seconds). 0 s against the 1440 s cap: no breach.

`RESOURCE_OVERRUN`: no.

## Peak RSS vs the 2 GiB reference

No decoder ran; no `rss_bytes` recorded. Nothing to compare against the 2 GiB
reference. Stated only: no peak RSS exists for this attempt.

## Post-run authorization state

`p0_cost_execution_authorized` returned to `false` immediately after the
single attempt, before this document was written. Nine
`*_execution_authorized` keys `false`; `next_gate: P0_PACKET_REVIEW`
unchanged. The single-attempt authorization is consumed.

## NOT_INTERPRETED

This document draws no conclusion about correctness, rate points, FER,
leakage, key rate, the method, or G1/G2 readiness. The refusal string is
quoted literally and is not analyzed, diagnosed, or dispositioned here. No
acceptance is granted. Acceptance requires an independent Pre-RESULT review.
G1 remains unauthorized.
