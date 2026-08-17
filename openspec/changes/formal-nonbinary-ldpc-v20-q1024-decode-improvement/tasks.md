# Tasks: formal-nonbinary-ldpc-v20-q1024-decode-improvement

Status: DRAFT — V19 OSD/MRB-OSD prototype implemented; V20 freeze still pending. Round 83-84 evidence shows V19 OSD family exhausted; ready for freeze review.

## Current blocker
V19 showed all current PEG/FFT-QSPA + bounded OSD attempts at q=1024 f≤1.3
result in `exact_mismatch` (or high FER at best point n=64 f=1.136: 28/64 exact).
Round 83-84 added MRB-OSD, rho variants, and fixed-frame code-seed sweeps; none
recovered the hard frame seed 2055. V20 must start from this blocker and select a
strictly stronger decoder/construction before execute.

## T0 Planning
- [ ] P0: freeze proposal/design/tasks and get main-thread/acceptance review
- [ ] P1: select M1/M2/M3/M4 subset and pre-register budgets/seeds/stop rules

## T1 Engineering
- [x] I01 (V19 prototype): implement bounded q-ary OSD order-0/1 using GF(q) field tables (`nonbinary_v19_osd.py`)
- [x] I02 (V19 prototype): add OSD integration to `nonbinary_v19_finite`
- [ ] I03: add improved construction/QC-PEG helper if M2 selected
- [ ] I04: add retry/blind-reconciliation helper if M3 selected
- [ ] I05: add channel-aware DE gate CLI if M4 selected
- [x] I06 (V19 prototype): tests for OSD helpers in `test_nonbinary_v19_osd.py`
- [x] I07 (V19 prototype): implement reliability-sorted MRB-OSD `osd_decode_candidates_mrb` and integrate MRB OSD-1/2

## T2 Execute
- [ ] E01: execute once on deterministic q=1024 synthetic frames
- [ ] E02: record exact_correct / decode_failed / FER / f / runtime / status

## T3 Verify/Closeout
- [ ] V01: read-only strict replay
- [ ] C01: update CURRENT_TASK.md, AGENT_HANDOFF.md, AGENT_PROJECT_MEMORY.md
- [ ] C02: local git commit only; no push
