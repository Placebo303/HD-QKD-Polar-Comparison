# M2 real accounting correction — Delta spec

## MAC-1 Tag-unit definitions

The corrected record SHALL define both tag totals from design §1 — the
recorded 64-bits-per-64-symbol-block total (`lambda_parts.tag`, 1,024
bits per superframe) and the nominal one-64-bit-tag-per-superframe
form — SHALL show both where f is discussed, and SHALL NOT let either
total silently stand in for the other. The protocol-under-test
selection between them is undetermined here.

## MAC-2 Actual disclosure as primary

The corrected record SHALL compute `f_ec_actual = leak_EC /
(superframes_done·1024·H_corr)` and `f_with_recorded_tags =
(leak_EC + tag) / (superframes_done·1024·H_corr)` per source/family/m
arm from the persisted summaries as the primary disclosure ratios, and
SHALL retain `f_notag` / `f_super` beside them labelled
`historical-nominal` (closed-form in `(m, H)`, identical across methods
at the same m). It SHALL reproduce the adjudication's discrepancy
mechanism (1M/m197: nominal 1.20048829 both arms vs actual 10.15137
HDC / 3.84156 LB, diagnostic). Primacy of `f_ec_actual` is an
accounting-ordering rule only: for the HDC arm it is the disclosure cost of an exhausted assumed-v1 schedule on blocks that were never corrected (`exact_match = 0` over all 28,000 real HDC blocks, design §11; status `void-no-correction`), hence void as a method quantity,
and for the LB arm it is measured under an UNKNOWN backend (design
§5). Neither is a validated method efficiency, and primacy SHALL NOT
read as endorsing cross-method comparison on those columns.

## MAC-3 Counterfactual labelling

Every occurrence of the one-tag-per-superframe column SHALL carry the
label COUNTERFACTUAL_ONLY (table, caption, and machine-readable field).
It SHALL NOT appear unlabeled where it could be quoted as an executed
protocol.

## MAC-4 FER units and f_eff

Block-level columns (blocks_done, fails, undetected, FER(block)) and
superframe-level columns (sf_success/sf_total, superframes_done) SHALL
be separate and SHALL NOT be merged; no superframe column SHALL serve
as an FER denominator. HDC and LB artifacts SHALL NOT carry an `f_eff` column in the corrected accounting (decided D-2, DROP, user, 2026-09-27; status `not-defined`; original values retained only as `historical-nominal` beside the original labels). Any reintroduction of an `f_eff` for these methods is explicitly gated behind a new preregistration carrying a method-specific, unit-consistent definition, and the frozen NB slope SHALL NOT be silently reused. Zero
recorded superframe successes (0/205, 0/287, 0/383) SHALL be stated.

## MAC-5 Backend provenance

The real LB backend SHALL be recorded as UNKNOWN (not recorded at
execution; not inferable from the current environment or the synthetic
batch) and SHALL NOT be inferred. The record SHALL specify the exact
future persistence set from design §5 (per-block `backend_used`,
per-root sidecar, stdout END/exit transcript, resource record) required
of any separately frozen DECIDE rerun.

## MAC-6 Method identity and HDC verification-path void

Every HDC number SHALL carry `assumed-v1` scope (provisional
Gray/block/pass pins, not source-verified Müller). No HDC figure SHALL
be presented as a method-family ranking. Additionally, the record
SHALL state as a standing two-part limit, attached to every HDC
number wherever it appears: (i) the parameters are assumed-v1, not
source-verified Müller; (ii) the implemented production verification
path cannot return success (`hd_cascade.py:224–229` unconditionally
returns `accepted=True, toeplitz_verified=False`, so the `:280–281`
gate forces `success=False, undetected=True` for every block), hence
every HDC success / FER / undetected value in any artifact is a stub
artifact with status `void-stub-artifact` and is void as a
measurement. The HDC `leak_EC`-derived ratios additionally carry
`void-no-correction` (design §11): they are the disclosure cost of an
exhausted assumed schedule on blocks that were never corrected
(`exact_match = 0` over all 28,000 real HDC blocks) — an upper bound
on a non-working configuration — void as a method quantity and barred
from cross-method ranking.

## MAC-7 D2 retirement (M2 scope)

D2 branch evaluation is RETIRED for M2 (D-3, decided by the user
2026-09-27). The record SHALL evaluate no D2 branch, report no D2
branch outcome, and set no revised D2 rule; the retired options
(i)/(ii) are recorded as considered-and-rejected (no valid input:
displayed f was not actual disclosure, tag unit undecided, HDC
unevaluable, LB backend UNKNOWN). Routing proceeds via the M0/P1
measured gap instead. Any future comparison metric SHALL require a
new preregistration before claim-bearing evaluation.

## MAC-8 Status discipline and claim ceiling

Every recomputed column SHALL carry an explicit status from the design
§8 vocabulary. Statuses `reference` / `stub` / `unavailable` /
`decode_failed` / `no_verified_success` SHALL never be converted to
`ok`; `undetected` (`accepted_wrong`) SHALL never merge into success
or FER numerators. The record SHALL carry the M2 claim ceiling (no
SKR/secure-key/qualification/composable-security/publication claim;
F9(i) u2-only annotation on every M0-number reference) and the
measured/assumed/projected/qualified column attribution.

## MAC-9 HDC exclusion from D2 and the comparison table

D2 SHALL NOT be evaluated with the HDC arm at all in its current
state, and the HDC column of the same-data comparison table CANNOT be
filled from existing artifacts. The appearance of HDC disclosure
being several times NB's nominal f is a property of an assumed
schedule on a non-functional verification path (design §6, §10), not
evidence about the method family. Wiring a real verifier alone does not change `exact_match`, `leak_EC` or FER (design §11) — it relabels the undetected column only. Any future HDC evaluation aiming at a citable number additionally needs a cascade that actually converges on this channel (a research sub-project, not designed here); either path requires a separately frozen DECIDE packet and a fresh-root rerun, and is not covered by this change.

## MAC-10 Layered-Binary disclosure void (no-correction)

The Layered-Binary `leak_EC` and all columns derived from it
(`f_ec_actual`, `f_with_recorded_tags`, `f_one_tag_CF`,
`lambda_total`, message counts as efficiency signals) SHALL carry
`void-no-correction` (design §14: 36 of 28,000 blocks exact, 0.13%,
block FER 0.9963-0.9995) and SHALL NOT appear in any cross-method
ranking. MAC-2's computation stands as stored arithmetic; this item
governs its status for LB. The existing LB SHALL NOTs are unchanged:
no backend inference (MAC-5), no `f_eff` (MAC-4), and no headline
tag ratio while D-1 stays deferred. LB's `success` / FER /
`undetected` columns are explicitly NOT void as measurements — they
are real, and they record a genuine failure — so the record SHALL
NOT over-void them. `void-stub-artifact` does NOT apply to LB.
