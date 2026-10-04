# V28 — Independent Freeze Review (in-conversation, main thread)

**Reviewer**: main thread (subagent infrastructure unavailable; user authorized in-conversation
review, not gated on subagent — goal revision 4).
**Date**: 2026-08-20
**Subject**: `openspec/changes/formal-nonbinary-ldpc-v28-gf32-finite-code-engineering/`
(proposal / design / tasks / specs/.../spec.md).
**Scope**: freeze the V28 OpenSpec before implementation. Verify parameter transcription from
the V27 gate result, reuse-claim accuracy against existing code, and leakage math.

## Reuse-claim verification (against real code)
- `GF2mField.create(32)` → q=32, m=5, primitive polynomial `0b100101`, pinned `field_id`
  present. ✅ No new field math.
- `nonbinary_codebook.gf_rank` present; `_TOPOLOGY` ==
  `three_shift_cyclic_information_half_plus_identity_parity_half` (matches design §3). ✅
- `nonbinary_qspa.decode_nonbinary_fft_qspa(bob_symbols, syndrome, manifest, matrices, *,
  check_count, p, max_iter=20)` exists → GF(32) FFT-QSPA decoder available for reuse. ✅
  (design §4 binding is correct; per-layer call uses `matrices={m_i: H_i}`, `check_count=m_i`.)

## Parameter transcription from V27 (`pass_finite_budget_ready`, block_len=1024)
Confirmed candidates (m1_ep offset-0) per source:
- 1M: m_total=200, m1=6, m2=194, R1=1−6/1024, R2=1−194/1024. ✅
- 1p5M: m_total=206, m1=6, m2=200, R1=1−6/1024, R2=1−200/1024. ✅
- 2M: m_total=208, m1=6, m2=202, R1=1−6/1024, R2=1−202/1024. ✅
design §1 table matches exactly. m1=6 shared → H_mother_L1 shared; m2 differs → H_mother_L2
prefix per source. ✅

## Leakage math (design §5)
Total leakage = m_total·5 + 64 bits; f = leak / (n·H_source), n=1024.
- 1M: 1064 / 820.263 = 1.29715 < 1.3 ✅
- 1p5M: 1094 / 845.380 = 1.29409 < 1.3 ✅
- 2M: 1104 / 852.544 = 1.29495 < 1.3 ✅
Consistent with V27 realized f (≈1.294). 64-bit tag counted only in total block leakage. ✅

## Terminal state
Only `engineering_ready_for_retrospective_gate` defined; no FER/qual/promotion. ✅ Matches
Phase C item 7. Forbidden set (DE/MC-DE rerun, fresh .ttbin, degree/MET search, push) explicit. ✅

## Verdict
**ACCEPT** — V28 OpenSpec is frozen and correctly grounded in V27 results + existing GF(32)
field/matrix/decoder infrastructure. Implementation may proceed (Phase C item 1 satisfied).

## Residual (non-blocking)
- Exact `decode_nonbinary_fft_qspa` call wiring (posterior conditioning for L2) is an
  implementation detail to validate during T4; the reuse target is confirmed present.
