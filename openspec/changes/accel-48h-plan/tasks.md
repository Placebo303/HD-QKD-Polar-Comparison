# Tasks: 48h Acceleration Plan (ordered P-1…P-6)

Convention: implement exactly these tasks in order; on requirement ambiguity STOP and return to planner/main instead of guessing. This increment itself performs no execution, writes no workspace root, and commits nothing. P-1 and P-4 execute only under their frozen packets' Pre-EXECUTE + new explicit verbatim grants. Small-enough note: P-2/P-5/P-6 are doc-only and small enough to implement directly (no pipeline); P-1/P-3/P-4 follow their packets' frozen T-lists and need no `/opsx-explore` (every primitive frozen).

Allowed paths for this increment: `openspec/changes/accel-48h-plan/` (this directory only). Forbidden: any `.py` edit, any `workspace/` read/write/list as evidence, any `results/`/`comparison_bench/outputs_comparison/` write, any commit/push.

---

- [ ] **P-1 — JOINT-PRICING-R2 re-evaluation execution (FIRST, seconds-scale unblock)**
  - Owner: **planner** (gate + terminal-word recording; delegates the frozen T-JR04 command to **coder-fast** as operator; D-4 by **reviewer-go**).
  - Packet vs doc-only: **packet** — frozen `docs/research_cycles/JOINT-PRICING-R2/PREREG_AND_AUTH.md` (§§1–17, §14 grant EMPTY → needs new verbatim grant).
  - Track: **EXPLORE** (analytic; zero data contact; design §2 row P-1).
  - Cost ceiling: 1 proc, 1 CPU, threads pinned, sequential; wall **≤300 s**, RSS **≤1 GiB**; fresh `workspace/jp_<uuid8>` only (uuid8 fixed at Pre-EXECUTE, distinct from executed root); no retry/resume except the §8 single infra repair.
  - Steps (frozen T-JR01…T-JR05): T-JR01 freeze-verify P-2 manifest (4 files: corrected `joint_pricing.py` + corrected fake test + `accounting_identities.py` + its fake test; hashes recorded; frozen packets/`perplane_stage0.py`/roots byte-untouched) → T-JR02 T0 `pytest test_joint_pricing_fake + test_accounting_identities_fake -p no:cacheprovider` all-pass + `py_compile` → T-JR03 Pre-EXECUTE P-1…P-9 (incl. F-1…F-4 greps with per-hit shape dispositions) → T-JR04 single frozen P-6 command → operator writes D-1…D-3 → T-JR05 batch-end review D-4 vs JR-01…JR-08.
  - 通过 (pass): JR-01…JR-08 PASS (or PASS_WITH_FINDINGS zero blocking) with anticipated **MARGINAL §5.3(a)** (CQ-J21c Scope A nominal M=1100 fits by 4; +20% backoff M=1319 excess 215; THIN-MARGIN acute) → terminal, **no joint-design work licensed**; any continuation needs new proposal + packet + grant. (If PASS-shaped, THIN-MARGIN flag still blocks downstream design until the user addresses the margin on record.)
  - 杀死/停止 (kill/stop): any §9 stop (input drift, fidelity violation, formula ambiguity, raw-data attempt, invented H, total-form regression `M+64`/`M+1024`/`M−1040`/bare-ceil-labelled-leak, budget breach, collision, label error) ⇒ retain + return, no input-fitting, no rerun except §8 infra repair; review FAIL ⇒ every number unpromotable, rework + re-review.
  - Acceptance: D-1…D-4 in the fresh root; both excess columns identically `M−1104`; no `M+64` vs 1104 outside the quoted withdrawal note; §11 ceiling verbatim; THIN-MARGIN state recorded.

- [ ] **P-2 — Stage-0 batch-end review closure (SECOND, zero-compute formalization)**
  - Owner: **reviewer-go** (independent; planner records the accepted KILL).
  - Packet vs doc-only: **doc-only** — review document into the existing Stage-0 root; no command runs.
  - Track: **— (doc-only, no gate)**; batch-end review of the executed EXPLORE batch per AGENTS.md §10.3.
  - Cost ceiling: **zero execution**; doc edits only in the Stage-0 root + decision-log/NOW maintenance path (separate from P-6).
  - 通过: S0-01…S0-08 PASS (or PASS_WITH_FINDINGS zero blocking) → provisional KILL becomes **accepted KILL**: ten independent per-plane allocations infeasible at the frozen `f` grid (CQ-J21c nominal total 1875 vs 1104 excess 771; backoff 2233 excess 1129); joint/structured-layered designs explicitly not excluded; no Stage-1 work licensed by anything short of a new proposal + packet + grant.
  - 杀死/停止: review FAIL (any blocking S0 finding) ⇒ KILL stays provisional, Stage-0 numbers uncitable as execution basis, no Stage-1 drafting, rework + re-review; never publish-then-patch.
  - Acceptance: `BATCH_END_REVIEW.md` filed; S0-02 hand-recompute ≥1 plane; S0-08 `0.098260`/`f_eff` zero-hits outside the quoted §11 ceiling; 771-bit D-1-robustness note carried (consistent 16-tag accounting still exceeds by 771).

- [ ] **P-3 — PROXY-RECAL-R2 segmented driver + fake test (THIRD, code-only unblock)**
  - Owner: **coder-fast** (implements; **reviewer-go** verifies T-R2-01/02 before any Pre-EXECUTE).
  - Packet vs doc-only: **implementation-only (packet-prep)** — exactly two new files: `comparison_bench/src/comparison_bench/cli/proxy_recal_sampler_seg.py` (T-R2-01: partition 6×40 ascending, per-block SEG rewrite, manifest, assemble gate; imports — never copies — frozen Packet-A helpers; dual-flag + `--num-segments 6` refusal; path-gate; I-5-vs-I-6 bitwise check; per-segment §3.5 validation gate; Stage-1 m=200 cold pins; per AGENTS.md §5.7 simplest-correct, no checksums/atomic/locking/retry/caching) + `comparison_bench/tests/test_proxy_recal_seg_fake.py` (T-R2-02: hand constants only, zero file reads; partition-once / checkpoint-survives-kill / refuse-short / refuse-overlap / word-helper-equality / path-gate).
  - Track: **— (implementation-only, no gate)**.
  - Cost ceiling: T0 `pytest test_proxy_recal_seg_fake -p no:cacheprovider` all-pass on fresh `workspace/proxy_recal_r2__pytest_<uuid8>` roots + `py_compile`; Packet-A files unmodified; no science execution.
  - 通过: fake test all-pass + reviewer-go implementation review PASS (no blocking) → eligible for P-4 Pre-EXECUTE (still BLOCKED until the §14 execution grant lands).
  - 杀死/停止: test failure or blocking review finding ⇒ no Pre-EXECUTE, scoped rework; any science-input/seed/graph/setting/partition/rule change ⇒ new packet, never a repair.
  - Acceptance: scoped manifest = exactly the two new files; Packet-A module reused by import; no `src/` touch.

- [ ] **P-4 — PROXY-RECAL-R2 segmented execution (FOURTH, the single heavy spend, alone)**
  - Owner: **coder-fast** (operator for six frozen segment commands + assemble; D-4 by **reviewer-go**; planner owns Pre-EXECUTE T-R2-03).
  - Packet vs doc-only: **packet** — frozen `docs/research_cycles/PROXY-RECAL-R2/PREREG_AND_AUTH.md` (DRAFT-FROZEN; §14 execution grant PENDING → needs new verbatim grant naming PROXY-RECAL-R2 with §8 ceilings).
  - Track: **EXPLORE (EXPLORE_HEAVY cost annotation)** — synthetic route-gate diagnostic arms; design §2 row P-4.
  - Cost ceiling: sequential segments, 1 proc at a time, 1 CPU, threads pinned (incl. NUMBA); per-segment wall **≤1800 s**, total **≤10800 s**, RSS **≤2 GiB**, per-block 300 s overrun ⇒ block failed + segment INCOMPLETE; fresh `workspace/proxy_recal_r2_<uuid8>` only; attempt-2 root read-only provenance.
  - Steps: T-R2-03 Pre-EXECUTE PR2 P-1…P-8 (nine input size/mtime + I-5-vs-I-6 bitwise; output absence; frozen commands; budgets/stops read-back) → T-R2-04 six ascending segment commands + frozen assemble → SEG/Manifest/D-1…D-3 → T-R2-05 review D-4 vs PR2-01…PR2-08.
  - 通过: full 240/240 ⇒ mechanical word: **PASS** (k′>10= k0 and W′ overlaps M0-2M R=[0.025875,0.066776]) licenses **only rescreen-packet drafting**; **MARGINAL** (k′>10 above R) / **KILL** (k′≤10) terminal with paired table as evidence; partial <240 ⇒ **INCOMPLETE** with retained segments, no word, no extrapolation, no trend sentence.
  - 杀死/停止: §3.5 validation REFUSE in segment g ⇒ zero decodes in g, no later segment; any §9 stop (input drift, invented rate, Bernoulli-plane draw, graph/seed/setting/partition drift, Stage-2 attempt, budget breach, collision, label error incl. quoting the shortfall factor as a number, checkpoint mismatch) ⇒ retain flushed SEG blocks + return; only §8 infra repair permitted.
  - Acceptance: on full completion D-1…D-4 + 6 SEG + manifest; on INCOMPLETE retained SEG + manifest + log with no D-1/D-2 assembly; §11 ceiling + §2.4 fences verbatim; `0.098260`/`f_eff` zero-hits outside ceiling.

- [ ] **P-5 — U1 review closure + dead-route fence consolidation (FIFTH, parallelizable with P-4 waits)**
  - Owner: **coder-doc** (writes; **reviewer-go** closes U1 PU-01…PU-06 review).
  - Packet vs doc-only: **doc-only** — no command runs.
  - Track: **— (doc-only, no gate)**.
  - Cost ceiling: **zero execution**; edits only under `docs/research_cycles/` + decision-log/NOW maintenance path.
  - 通过: U1 D-4 PASS (zero blocking) + fence doc records: option F closed under every U1 outcome (header ceiling ≈24.6 bit/≈0.03 f); M3C STOP restated (no two-graph/FER/leakage/f/SKR conclusion); M3D narrow mechanical sentence only (no "cap useless / M3C wall solved" reading); M2 WITHHELD with five blocks; HDC 0/28,000 + LB 36/28,000 `void-no-correction` never ranked (LB `void-stub-artifact` explicitly inapplicable); D-1 DEFERRED with both tag totals distinct; `0.098260`/`2–4x`/entropy-subset/throughput derivations only with their required annotations.
  - 杀死/停止: any attempt to reopen a dead route, pool M3B instances, cite a void number as method data, or designate a headline tag without a new packet + grant ⇒ STOP; review FAIL ⇒ rework + re-review.
  - Acceptance: fence sweep (no bare "plane independence / no easier point / unused groups do not help / is an artifact of" forms outside meta-quotations); U1 §5 clause + header bound restated verbatim.

- [ ] **P-6 — 48h decision record + scoped manifest + memory triage (LAST, auditability)**
  - Owner: **memory** (triage; **planner** signs the record; **coder-doc** stages the manifest).
  - Packet vs doc-only: **doc-only** — decision-log entry + NOW maintenance + triage note; manifest listed, not committed.
  - Track: **— (doc-only, no gate)**.
  - Cost ceiling: **zero execution, zero workspace write, zero commit/push**; dirty-tree check re-measured (`git branch --show-current`, `git rev-parse HEAD`, `git status --porcelain`).
  - 通过: 48h record states per-P terminal words (P-1 word + THIN-MARGIN state; P-2 KILL accepted/provisional; P-3 eligible/blocked; P-4 word or INCOMPLETE with retained counts; P-5 fences closed), next-grant requirements (P-1 grant text if still pending; P-4 grant naming PROXY-RECAL-R2 with §8 ceilings), and the scoped manifest (this directory's three files + pending review docs only; `git add -A` forbidden; no Polar/sibling-line merge; ordinary non-force pushes only on a named formal-IR branch + PR).
  - 杀死/停止: dirty-tree expansion beyond the scoped manifest, any workspace write, or any commit/push attempted under this change ⇒ STOP and return to planner.
  - Acceptance: memory triage complete (endpoint §4 per mandatory processes); no number citable beyond its packet's review; next session resumes from this record + NOW + EXECUTION_PLAN without reading chat history.

---

## Execution order and 48h budget rollup

P-1 (≤300 s) → P-2 (0 s) → P-3 (pytest minutes) → P-4 (≤10800 s ≈ 3 h, the only heavy item) with P-5 doc work overlapping P-4 waits → P-6 (0 s). Total machine budget ≈ 3.1 h wall + reviews; fits 48h with margin for one preregistered infra repair per executed packet and one re-review per FAIL. No two heavy executions overlap. P-4 does not start until P-1/P-2 terminals are recorded and its grant + Pre-EXECUTE pass.
