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
  writer and verifier. PROFILE_ONLY constructs all 12 graphs (pre-A1 wording —
  SUPERSEDED by Amendment A1: 18 graphs / 12 seeds, design §8.4), proves A1–A6,
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
- Status note (R201, 2026-09-14): the "remain [ ]" lines above are pre-retry
  wording — the retry completed and N202–N210 are [x] per the N210 VERIFIED
  PASS. R2 work proceeds as R202–R207 below; N-series boxes are history.

## R2 authorized-path completion (R201–R207; R2 packet, 2026-09-14)

Authority: `.workbuddy/tasks/D14N_AUTHORIZED_PATH_COMPLETION_R2_TASK_PACKET.md`.
Track: `EXPLORE` readiness planning for R201 (docs only; no code, no execution,
decoder calls 0, no commit/push); future batch remains `EXPLORE`. Scope:
`openspec/changes/v72p2d14n-calibrated-l1-l2-discriminator/**` for R201;
code/scripts/tests/cycle-docs per R2 packet §§3–4 for R202–R207 (later calls).
Design §9 + spec R2 deltas are normative for R202+; prereg file stays untouched.

- [x] **R201 OpenSpec amendment**: record the blocking fall-through (authorized
  `--n14-batch` → unconditional `SystemExit`, design §9.1) and the R2
  authorized-path completion scope; correct stale pre-A1 ≤26 / m=118 statements
  (design §9.3); FREEZE the APP transfer-source profile (L055 challenger L1
  `CHECK_UPDATED` beliefs, design §9.2) and re-affirm `L1-ADEQUATE(L055)` with
  L045 descriptive-only; freeze R202–R207 contracts packet-exact (design §9.4).
- [x] **R202 production adapters**: one narrow binder returning the accepted
  Model-F loader/prior, L1 decoder, `CHECK_UPDATED` transfer, L2 APP, and
  true-L1 oracle callables. Reuse D11/D12/D14 helpers (design §4); no kernel
  copies, no alternate algorithms. Validate callable signatures before root
  creation or decoder calls.
- [x] **R203 batch orchestrator**: build/validate the complete 288 plan before
  binding; construct the frozen 18 graphs + 12 blocks once per setup-32
  accounting; dispatch in frozen order; collect distinct exact, syndrome,
  source, target, joint, and `undetected` fields; STOP on provenance,
  nonfinite, admission, resource, or contract violation.
- [x] **R204 CLI true branch**: replace the unconditional authorized-path
  `SystemExit` with exactly one orchestrator call + one never-overwrite writer.
  Unauthorized refusal stays before root, binding, and Model-F load. Authorized
  launch form: frozen command plus `--execution-authorized`; manifest may retain
  the flag-free scientific command identity iff that precedent is explicit.
- [x] **R205 fake authorized-path test**: injected fake adapters, true
  authorized branch, fresh scratch root. Acceptance: exactly 288 fake calls
  (72×4), 32 setup units, six files, deterministic identities, expected fake
  gate/terminal, read-only verifier PASS, proof of zero production-binder /
  Model-F entry. Failure tests: first contract error, existing root, partial
  root, invalid APP provenance.
- [x] **R206 production-boundary probe**: without decoding or creating the
  future root, resolve + inspect the real adapter identities/signatures —
  including the explicit L055 APP transfer-source profile; callable +
  accepted-helper check only, no scientific invocation.
- [x] **R207 independent re-review**: reviewer with actual files reruns focused
  tests in its own basetemp and independently traces both CLI branches; SHALL
  prove the authorized branch no longer reaches the old `SystemExit`, fake
  dispatch 288/288, verifier PASS, future root
  `workspace/v72p2d14_discriminator/20260914_r1` absent, production decoder
  calls zero.

R2 verification proportionality (R2 packet §4): T0 `py_compile` amended module,
CLI, and focused tests; T1 D14N focused suite + directly-affected D11/D12
suites only when imports changed, on a fresh `workspace/` basetemp with
`-p no:cacheprovider`; PROFILE_ONLY + live unauthorized refusal; authorized
true branch only with injected fakes + fresh scratch root (test machinery, not
scientific execution); future root absent; zero production decoder calls. Return
only at `D14N_R2_EXECUTION_PATH_READY_AWAITING_EXPLICIT_AUTHORIZATION` with the
R2 packet §6 bundle; any mismatch → STOP, no real batch, no root, no
authorization.
