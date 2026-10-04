# M3-a nested 200+8 construction probe

Track: implementation-only for this change; first synthetic construction is a separate EXPLORE batch. This route is motivated by M0's real-frame gap and P1's measured prefix defect, independently of the suspended M2 D2 result.

Build a 200-row GF(32) PEG base first, then append eight ten-edge parity rows without changing any base triple or label. Test two frozen seed pairs. Record structural pins only; zero decoding, no FER/efficiency/route claim. The smallest implementation belongs in a new `comparison_bench` CLI module and fake-only test, leaving the frozen PEG constructor and existing result roots unchanged.

Affected spec: `specs/m3a-nested-construction/spec.md`.
