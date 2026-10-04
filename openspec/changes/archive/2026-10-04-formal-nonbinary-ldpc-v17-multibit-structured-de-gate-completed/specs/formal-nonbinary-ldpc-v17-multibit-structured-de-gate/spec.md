# Spec Delta: formal-nonbinary-ldpc-v17-multibit-structured-de-gate

> 本 delta 仅在 change 完成且用户选择归档后才可合并；gate_state=fail
> 时**不合并**（V9/V10/V14 先例）。

## 1. Purpose

Establish a gate-only feasibility lane: decide, via density evolution,
whether edge-label / bit-plane structured nonbinary LDPC ensembles can
reach rate ≥ 0.90 at f ≤ 1.3 on the frozen multibit channel model derived
from the V13 MSB→LSB monotone mismatch observation.

## 2. Requirements

- V17-1: No finite code, codebook, decoder, canary, development, or
  qualification output may be produced by this change.
- V17-2: Stage 0 must reproduce/validate the multibit (bit-plane
  decomposition) DE mechanism against frozen anchors before any model or
  point evaluation.
- V17-3: The channel model must be rebuilt read-only from characterization
  frames and persisted as schema `nbldpc_v17_multibit_channel_model_v1`.
- V17-4: A small candidate set (3–5) is pre-registered before execution
  with the FULL evaluation point set m∈{15,16,17,18} (rate 0.9297–0.9414,
  same protocol as V14); no subsetting, no search, no tuning, no rerun.
- V17-5: Convergence, efficiency (f≤1.3), budget (3 GiB / 24 h), and
  execute-once + strict replay standards are frozen before execution.
- V17-6: PASS ⇒ a separate finite-code candidate change; FAIL ⇒ route
  frozen, V15/V16 not launched, search not expanded.

## 3. Out of scope

Finite-code construction; SC-LDPC gate (second candidate); multi-edge /
high-dimensional lambda search; V15/V16 relaunch; fresh acquisition (P1
separate change).
