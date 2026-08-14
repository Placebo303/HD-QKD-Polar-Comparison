# Spec Delta: formal-nonbinary-ldpc-v13-r3-fresh-acquisition

> 本 delta 仅在 change 完成（fresh-confirmed）且用户选择归档后才可合并
> 进 `openspec/specs/`；frozen failure 时**不合并**（V9/V10 先例）。

## 1. Purpose

Establish the fresh-acquisition confirmation lane for the frozen V13 R3
candidate `nbldpc_v13_r3_code_v1`, answering whether it still exact-corrects
on fresh frame/payload identities disjoint from all historical locks.

## 2. Requirements

- FRESH-1: The change must use fresh data whose frame/payload identities
  are disjoint from V4/V5/V12/V13 historical locks, verified via the
  reusable partition identity machinery.
- FRESH-2: The candidate codebook, QSC p=.20 prior, flooding FFT-QSPA
  interface, and max_iter=100 must remain byte-unchanged.
- FRESH-3: Roles (characterization / canary / confirmation) must be
  mutually exclusive and pre-registered in a frozen plan.
- FRESH-4: Stop rules must freeze: no-eligible-frames, distribution drift,
  and retain-all-failures (no frame replacement, no tuning, no rerun).
- FRESH-5: The route executes the frozen lifecycle exactly once:
  freeze → prepare → main-thread review → single fresh execute → one
  read-only verify → `fresh-confirmed` or `frozen failure`.
- FRESH-6: `fresh-confirmed` is the maximum state; it confers no
  promotion, qualification, efficiency, or comparison claim.

## 3. Out of scope

Efficiency (f≤1.3) belongs to the separate V17 gate; SC-LDPC / bit-plane /
multi-edge construction; V15/V16 relaunch; any official qualification root
write.
