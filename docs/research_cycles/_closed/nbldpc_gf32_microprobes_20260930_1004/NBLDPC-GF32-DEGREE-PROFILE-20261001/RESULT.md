# RESULT — NB-LDPC GF32 degree-profile construction attempt

**Track:** EXPLORE  
**Batch UUID:** `8c881d42-8d11-4867-8175-bc6f5c97f1f3`  
**Status:** `INCOMPLETE` (`STOP` during graph construction)  
**Machine root:** `workspace/gf32_degree_8c881d42/`

## Attempt and stopping point

The single authorized command was run once after confirming the output root was absent. It exited 0 and produced the five frozen artifacts. Construction stopped at candidate graph seed `2026093905`: `no eligible check placement at variable 127 socket 2`. No replacement seed, fallback profile, resume, or rerun was used.

The manifest retains ten graph-attempt diagnostics: control seeds `2026093901`–`2026093905` and candidate seeds `2026093901`–`2026093905`. Nine actual constructor matrices were admitted with rank 52 and the requested degree profiles: all five control graphs and candidate seeds `2026093901`–`2026093904`. Candidate seed `2026093905` failed construction; seed `2026093906` was not attempted. No deep-label matrix, pair, truth, syndrome, or decoder vector was produced. Label searches, BP, OSD, decoder calls, pairs, frame rows, and disclosed syndrome bits were all zero.

The terminal state is `STOP` / `INCOMPLETE`; all complete performance totals are null. The frozen performance screen was not reached and has no positive or negative result.

## Artifacts and resource record

The five retained artifacts are `manifest.json`, `frame_records.csv`, `summary.json`, `diagnostics.npz`, and `EXPLORATION_LOG.md`. The CSV contains its header only. The NPZ contains the nine available constructor matrices and their maps; it contains no deep-H, pair, or vector data.

Recorded wall time was `0.191249693 s`. Sampled RSS peaked at `102936576` bytes across 22 samples. `diagnostics.npz` is 15,899 bytes with 480,024 bytes of array payload. Resource violations were 0 and authorization violations were 0. The summary records `integrity_violations=1`; that counter comes solely from the construction/admission STOP. It does not indicate data corruption, tampering, or a decoder error.

## Interpretation boundary

This is an incomplete construction attempt, not a degree-profile performance result, `NO_SUFFICIENT_SIGNAL` result, or route rejection. No decoder or paired outcome was observed. Verification remains `NOT_IMPLEMENTED`; undetected errors remain `NOT_MEASURED`. The one-shot grant is consumed; no rerun, resume, seed replacement, or extra graph attempt is authorized.

Independent D6 review and main acceptance are recorded in [INDEPENDENT_ACCEPTANCE.md](INDEPENDENT_ACCEPTANCE.md).
