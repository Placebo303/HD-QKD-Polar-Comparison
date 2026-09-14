# Tasks — D14N Calibrated L1/L2 Discriminator (readiness N201–N210)

Packet: `.workbuddy/tasks/D14N_CALIBRATED_DISCRIMINATOR_IMPLEMENTATION_R1_TASK_PACKET.md`
Prereg: `docs/research_cycles/D14_VALIDITY_RESET/N_DISCRIMINATOR_PREREG_R1.md`
(accepted — transcribed exactly, not reinterpreted).
Track: `EXPLORE` (implementation/readiness now; future batch `EXPLORE`).
Scope: `openspec/changes/v72p2d14n-calibrated-l1-l2-discriminator/**` for N201;
code/scripts/tests/cycle-docs per packet §§3–6 for N202–N210 (later calls).

- [x] **N201 OpenSpec first**: proposal, design, tasks, and delta spec
  (this change dir). Explicitly list reused D11/D12/D14 helpers (design §4)
  and rejected duplication (design §4, duplication-rejection statement).
- [x] **N202 plan and identities**: deterministic 288-record plan built before
  any decoder binding or Model-F load; exact seed/profile/arm equality checks.
- [x] **N203 construction reuse**: import the accepted connectivity-first graph,
  admission, coefficient, sampling, and prior helpers. One construction path per
  frozen arm family; do not copy decoder or GF32 kernels.
- [x] **N204 dispatch**: share each paired block and graph identity across four
  arms; L2 APP consumes only CHECK_UPDATED L1 beliefs; L2 ORACLE uses true-L1
  conditioning and is marked `ORACLE`/ungraded.
- [x] **N205 gates**: implement the six terminals and exact priority from prereg
  §7. L045 discordances are descriptive only. Unit-test every boundary and
  priority collision.
- [x] **N206 CLI**: add `scripts/v72p2d14_discriminator_development.py` with
  `--profile-only`, `--n14-batch`, `--execution-authorized`, and `--verify`.
  Default-false batch refusal must occur before output creation, decoder
  binding, or Model-F load.
- [x] **N207 evidence**: fresh never-overwrite six-file root matching the prereg;
  minimal manifest, graph records, decoder records, arm summary, summary, and
  command log. Do not add hashes, transactional writes, retry frameworks, or
  production-style infrastructure.
- [x] **N208 verifier**: read-only fail-closed recomputation of identity set,
  admissions, calls, metric isolation, provenance, gates, terminal, and budgets.
  Missing/partial/mismatched roots fail nonzero.
- [x] **N209 focused tests/profile**: fake-runner tests for plan, sharing,
  provenance refusal, oracle exclusion, all gates, no-write authorization,
  writer and verifier. PROFILE_ONLY constructs all 12 graphs, proves A1–A6,
  emits exact mixed-degree counts and the 288 plan, with zero decoder calls and
  no future-root write.
- [x] **N210 independent readiness review**: actual artifact access; independently
  recompute graph counts/admission, plan identities, gate boundaries, reuse,
  refusal ordering, root absence, budgets, and zero production calls.

Verification proportionality (packet §4): T0 `py_compile` new module, runner
and tests; T1 new focused suite plus only directly reused D11/D12 focused
suites on a fresh `workspace/` basetemp with `-p no:cacheprovider`; no broad
reruns without a concrete focused conflict; PROFILE_ONLY + live unauthorized
refusal; no production batch. Reviewer-go evidence accepted when
`EVIDENCE_ACCESS: VERIFIED`, tests named, no blocking inconsistency; main thread
does not duplicate it.

## Freeze Amendment A1 note (2026-09-14, main-thread adjudicated)

- N201 stays [x] (this amendment extends the N201 OpenSpec artifacts; it does
  not re-open N201).
- N202–N209 remain [ ] and SHALL retry on the amended freeze: L045
  71/57/E313 `2^17+3^93`, L055 83/45/E301 `2^29+3^81` at m_L1=110; setup ≤32;
  PROFILE scope 18 graphs / 12 seeds (details: `design.md` §8).
- N210 SHALL verify the amended cells, setup-32 accounting, and 18-object
  PROFILE scope in addition to the packet-exact items above.
- Prereg file untouched (retain + supersede corrigendum pattern).
