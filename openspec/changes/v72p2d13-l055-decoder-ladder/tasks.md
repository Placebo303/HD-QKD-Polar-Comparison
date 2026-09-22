# Tasks — D13 L055 failure decoder ladder (readiness D1301–D1310)

Packet: `.workbuddy/tasks/D13_L055_FAILURE_DECODER_LADDER_READINESS_TASK_PACKET.md`
(sole authority; §1–§4 frozen). Track: implementation/readiness (zero
scientific calls; no D13 execution, no decoder calls, no root creation, no
L2/D7-H, no real data, no commit/push). Branch
`formal-ir-v72p1-addendum-clean` (do not switch; no commit, no push).
Predecessor immutable: `D12_L055_ACCEPTED_ROUTE_TO_D13_DECODER_LADDER`
(root `workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`,
terminal `D12_SELECT_L055`, VERIFIED PASS_WITH_FINDINGS; read-only context,
successes never enter the ladder).

- [x] D1301: create D13 OpenSpec proposal/design/tasks/spec before behavior edits.
- [x] D1302: read-only audit D12 root and freeze the exact 56 identities plus stored
  baseline fields; independently confirm 30/26 and iteration=90.
- [x] D1303: audit/import D12 reconstruction and existing accepted RL/flooding
  binders; record semantic map and reject decoder duplication.
- [x] D1304: implement thin additive selector/replay/ladder/gate/verifier with plan
  built before any binding; first replay mismatch stops later calls.
- [x] D1305: require explicit default-false CLI execution flag and refuse before
  root creation, decoder binding or Model-F load.
- [x] D1306: write a fresh never-overwrite minimal root; verifier independently
  checks selection, replay, calls, rescues, ranking, terminal and budgets.
- [x] D1307: focused fake tests for exact selection, exclusion of successes,
  56+168 accounting, first-mismatch stop, provenance, all rescue boundaries,
  ranking, exact/syndrome/undetected isolation and unauthorized refusal.
- [x] D1308: `py_compile` and focused D13 plus directly affected D12/X3 tests in a
  fresh workspace basetemp; no broad suite absent focused external failure.
- [x] D1309: PLAN_ONLY reconstruction metadata for all 56 with zero decoder calls,
  deterministic identities, input root unchanged and future root absent.
- [x] D1310: independent reviewer-go readiness review with
  `EVIDENCE_ACCESS: VERIFIED`, recomputing selection, frozen replay contract,
  decoder bindings, gates/rank, budgets and no-production boundary; append one
  log/readiness record and perform memory triage.

D1301 evidence (this task): new additive change
`openspec/changes/v72p2d13-l055-decoder-ladder/` (`proposal.md`, `design.md`,
`tasks.md`, `specs/l055-decoder-ladder/spec.md`); packet §2 frozen verbatim
(input root read-only, 56 identities, preserved fields, no-success rule,
strict RL90 replay with first-mismatch block, exactly three ladder arms,
224 ceiling, rescue counting per arm by width+total, MATERIAL/MODEST/NO/
AMBIGUOUS gates, ranking, seven terminals + eng-blocked with MATERIAL-required
selection, future root
`workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e`
(absent verified), budgets ≤224/≤8/1800 s/120 s/RSS<2 GiB/1-proc/
no-retry-resume-repair-search-tune, claim ceiling frozen synthetic L1 decoder
diagnostic only). Allowed files:
`openspec/changes/v72p2d13-l055-decoder-ladder/**` only. Zero decoder calls;
no commit/push.

D1302 evidence (this task): selector predicate `arm == L055 AND exact == false`
over D12 `decoder_records.csv`; three-source count corroboration
(`arm_summary.csv` pooled 42/72 n128 + 46/72 n256, `summary.json` pools,
direct row audit) → 30 at n128 + 26 at n256 = 56 total; every selected record
`iterations=90`, `syndrome_ok=False`, `converged_no_syndrome`, `CHECK_UPDATED`;
undetected grep (`L055.*False,True`) empty; full 56-identity list frozen in
`design.md` §3; stored baseline fields + preserved fields recorded in
`design.md` §2. No mismatch → no BLOCKED condition met.

D1303 evidence (this task): semantic map (`path:line`) + duplication rejection
in `design.md` §4: D12 `build_graph` + R2 construction/admission/coeff/prior/
dispatch-cold path, R2-runner prior/block loaders, D12 production decoder bind,
accepted D7-E RL90 binder + D7-D schedule RL90/flooding-90 binder, RL360 via
parametrizable `max_iter`, damping-0.7 as existing tunable parameter only (NOT
tuned), flooding-360 via accepted target, CHECK_UPDATED provenance. All
required binders accepted → no BLOCKED condition met.

Gate: return `D13_L055_DECODER_LADDER_READY_AWAITING_EXPLICIT_AUTHORIZATION`
only when D1301–D1310 pass with zero scientific calls and no blocker
(packet §4). STOP on identity/count mismatch, reconstruction ambiguity,
missing accepted decoder binder, predecessor modification, decoder/scientific
entry, root creation, failed review or dirty-file conflict. Do not execute
D13, tune damping, add arms, alter D12, run L2/D7-H, commit or push.
