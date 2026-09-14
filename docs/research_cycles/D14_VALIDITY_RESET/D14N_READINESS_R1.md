# D14N Calibrated L1/L2 Discriminator — Implementation Readiness R1

- Authority: `.workbuddy/tasks/D14N_CALIBRATED_DISCRIMINATOR_IMPLEMENTATION_R1_TASK_PACKET.md`
  (§6 readiness record + D14 log append); D14N-R210 review result
  (EVIDENCE_ACCESS VERIFIED, VERDICT PASS, BLOCKING none — trusted, not rerun).
- Track: `EXPLORE` (implementation/readiness now; future 288-call batch `EXPLORE`).
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch
  `formal-ir-v72p1-addendum-clean` (no switch; no commit/push in this call).
- Predecessor: accepted D14-FINAL (`D14_VALIDITY_RESET_COMPLETE_CALIBRATED_BATCH_READY_AWAITING_EXPLICIT_AUTHORIZATION`)
  + frozen prereg `N_DISCRIMINATOR_PREREG_R1.md` (203 lines, unedited — retain + supersede corrigendum pattern).
- This call: documentation-only close (this record + one D14 log append +
  D14N OpenSpec `tasks.md` N202–N210 checkbox update). No code, no execution,
  no decoder/scientific calls, no staging/commits, no push.

## 1. Amendment A1 summary (STOP-then-amend, main-thread adjudicated)

- Trigger: operator pre-code STOP with zero writes — frozen L1 check-allocation
  strings transcribed from D12 (`2^41+3^77`, `2^53+3^65`) sum to m=118
  (41+77=118; 53+65=118), not frozen m_L1=110; constructor probe confirmed
  (m=110 refuses, m=118 accepts).
- Adjudication A (ADOPTED): variable side is m-independent and STANDS —
  L045 n2=71/n3=57/E313 (70.53/57.47 largest-remainder), L055 n2=83/n3=45/E301
  (82.82/45.18 largest-remainder); check side re-derived from (E, m=110) D9
  floor/ceil rule: L045 `2^17+3^93` (b=313−220=93), L055 `2^29+3^81`
  (b=301−220=81); socket checks at m=110 close exactly
  (17·2+93·3=313; 29·2+81·3=301); old strings diagnose m=118
  (b=313−236=77; b=301−236=65).
- Adjudication B (REJECTED with rationale): m=118 would disclose 590 bits,
  effective 590/548.700215065776=1.07527≈1.0753, destroying Choice A
  (550/548.700215065776=1.00237, effective≈1.0) — the discriminator's point.
- Setup-32 ruling (supersedes ≤26): **32 = 18 built objects** (6 L045 + 6 L055
  at the 6 shared L1 seeds + 6 L2 DV3) **+ 12 block samples + 2 fixed
  (plan/manifest)**; PROFILE scope 18 graphs over 12 seeds. Prereg file
  untouched (0 check-alloc strings edited, ≤26-line budget line intact via
  supersede, not edit). Normative deltas live in `design.md` §8 / delta spec;
  `proposal.md` retains pre-amendment strings (non-blocking, recorded).

## 2. Frozen contract (as amended)

- n=128 only; L1 m=110 — L045 control (71/57/E313, `2^17+3^93`), L055
  challenger (83/45/E301, `2^29+3^81`); L2 DV3 m=104, E=384, `3^32+4^72`.
- Six paired L1/L2 graph seeds `2026093401..06` / `2026093501..06`; twelve
  block seeds `2026093601..12`; shared identities per cell.
- 288 = 72×4 deterministic plan (L045→L055→L2_APP→L2_ORACLE, pairs/blocks
  asc, idx 0..287); L2 APP consumes only CHECK_UPDATED L1 beliefs; L2 ORACLE
  true-L1 conditioned, marked `ORACLE`/ungraded, never gates.
- Six frozen routing terminals + exact priority verbatim (incl. exhaustive
  8-combo priority, engineering-first); L045 discordances descriptive-only
  (structurally non-gating); AMBIGUOUS retained-frozen-unreachable documented.
- Candidate concentration-backoff prior only; GF32/poly37; row-layered cold
  decoder max_iter=90, damping=1.0; exact/syndrome/source/target/joint/
  undetected separate (`undetected` never merged into success/FER).
- Budgets: ≤288 decoder calls, ≤32 setup, ≤1800 s wall, ≤120 s/call,
  RSS <2 GiB, one process, CPU-only, no retry/resume/repair/seed search/tuning.
- Future root `workspace/v72p2d14_discriminator/20260914_r1` absent; exact
  future command frozen; no D7-H; n=128 only.

## 3. N201–N210 evidence table (trusted VERIFIED, not rerun)

| Task | Evidence |
|---|---|
| N201 OpenSpec first | 4 files: proposal/design/tasks/delta spec; reuse map + duplication-rejection statement (design §4) |
| N202 plan and identities | 288-record deterministic plan pre-decoder-binding; seed/profile/arm equality checks |
| N203 construction reuse | Accepted connectivity-first graph/admission/coefficient/sampling/prior helpers imported; one `_compose_graph` per family; no copied GF32/decoder kernels; donors unmodified |
| N204 dispatch | Paired block+graph identity shared across four arms; APP CHECK_UPDATED-only; ORACLE marked/ungraded |
| N205 gates | Six terminals verbatim; every boundary + priority collision unit-tested |
| N206 CLI | `scripts/v72p2d14_discriminator_development.py` (`--profile-only`, `--n14-batch`, `--execution-authorized`, `--verify`); default-false refusal pre-write/bind/load |
| N207 evidence | Fresh never-overwrite six-file root (manifest, graph/decoder records, arm summary, summary, command log); no hashes/txn/retry infra |
| N208 verifier | Read-only fail-closed recompute (identities, admissions, calls, metric isolation, provenance, gates, terminal, budgets); missing/partial/mismatch → nonzero |
| N209 tests/profile | 22/22 focused tests on reviewer-own basetemp (fake runner; plan/sharing/refusal/oracle/gates/no-write/writer/verifier); PROFILE_ONLY 18 graphs, A1–A6 proven, amended counts + 288 plan, zero decoder calls, no future-root write |
| N210 independent review | **PASS, BLOCKING none**: amended cells recomputed exact-rational; 18/18 admitted (reviewer's own numbers: L045 E313 vh{2:71,3:57} ch{2:17,3:93}; L055 E301 vh{2:83,3:45} ch{2:29,3:81}; L2 E384 vh{3:128} ch{3:32,4:72}; all A=1×6 by independent double-build, 0 replacements); refusal live-run RC=2 pre-write/bind/load (v35/decoder/Model-F absent, root absent; even `--execution-authorized --n14-batch` raises pre-adapters); budgets in code+spec+manifest+verifier; zero production calls; no D7-H; D11/D12 trusted per trust rule |

New code files (3, additive untracked):
`comparison_bench/src/comparison_bench/formal_ir/v72p2d14n_calibrated_discriminator.py`,
`comparison_bench/tests/test_v72p2d14n_calibrated_discriminator.py`,
`scripts/v72p2d14_discriminator_development.py` —
plus reuse (`dispatch_l1`/`coefficient_seed`/`refuse_out_root` + Q/POLY/90/1.0/ROOT/RSS is-identical).
Reviewer-go evidence accepted per packet §4 (EVIDENCE_ACCESS VERIFIED, tests
named, no blocking inconsistency); main thread does not duplicate it.

## 4. Authorization state (all false)

- Batch authorized: **false**. Execution authorized: **false**. Result root
  exists: **false** (`workspace/v72p2d14_discriminator/20260914_r1` absent).
  Decoder calls: **0**. Scientific/production calls: **0**. Commit: **none**.
  Push: **none**. Branch switch: **none**.
- FLAG adjudication (carried, not blocking): APP transfer-source profile is
  correctly carried to the batch-runner freeze (fail-closed injection, no
  default) — becomes execution-gating at Pre-EXECUTE, NOT readiness-blocking.

## 5. Terminal + Pre-EXECUTE notes

- Terminal: `D14N_CALIBRATED_DISCRIMINATOR_READY_AWAITING_EXPLICIT_AUTHORIZATION`.
- Pre-EXECUTE (future paired A1 execution packet) must reconfirm: APP-source
  freeze injection (fail-closed, no default) resolves to an explicit source
  before any run; d5-tree reconfirm carried; target-output absence re-verified;
  exact frozen command + budgets + explicit user authorization recorded.
- Non-blocking findings carried: `proposal.md` pre-amendment strings (design
  §8/spec normative); dirty worktree additive-untracked (combined-process
  pollution unverified-but-contracted).

## 6. Next gate + claim boundary

- Next gate: paired A1 execution packet after main-thread readiness acceptance
  of this record. No execution prompt is created here; the batch is not
  self-authorized.
- Claim boundary: synthetic diagnostic only. No FER/leakage/SKR/real-data/
  qualification/promotion/optimality/route-closure/publication claim. Real
  data, formal qualification, route-closing decisions and publication claims
  remain DECIDE-gated. D7-H NOT revived.
