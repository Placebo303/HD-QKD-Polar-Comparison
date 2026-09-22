# Occam failure ablation

Status: offline descriptive analysis authorized by the user request; new decoder execution NOT authorized. Snapshot: `ff88696f3c242cfb441dc9c82720e4fa6a371968`, branch `formal-ir-v72p1-addendum-clean`.

Question: which extra computation/disclosure actually rescues failed blocks? Start with existing V64 records rather than a new sweep. Reconstruct the same-block policy truncations base / delta8 / delta16, then characterize the remaining failures by source and L1/L2 error counts. This is retrospective analysis, not fresh validation or algorithm promotion.

Allowed additions: this OpenSpec change and `scripts/analyze_v64_stage_ablation.py`. Read only the existing V64 records, summary and execution source. No decoder imports/calls, raw-data reads, baseline changes, output overwrites, Git mutations, or new dependencies. The analysis prints JSON to stdout. A focused self-check and independent luna review precede delivery.

Follow-up algorithm experiments remain proposals; reuse the existing V70R1 and V72 contracts instead of creating a parallel research framework.
