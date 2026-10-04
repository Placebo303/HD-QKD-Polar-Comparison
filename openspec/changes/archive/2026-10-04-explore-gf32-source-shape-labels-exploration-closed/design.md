# Design

Use D10 generic degree-sequence PEG with frozen n128/m52 profile (128 degree2
variables, 4 degree4 and 48 degree5 checks) and six fixed seeds. This is a
new synthetic profile, not an accepted L055 support or cross-batch baseline.
All preflight checks precede decodes; no replacement on failure.

Hard-code the already accepted 2M nonzero marginal counts2295/1126/557/304/146
at E1=1/3/7/15/31. Normalize by4428 and stress only zero mass across a four
point frozen grid. iid/Bob-zero model omits conditional/temporal source
structure. Exact sparse prior remains fixed between arms, with only the
unchanged decoder's numerical behavior permitted.

CONTROL-only pilot chooses first eligible point; holdout seeds are disjoint.
H0D uses the existing one-pass check-entropy proxy and preserves rank/support/
cycle class. Lower redundancy and source shape are fixed batch conditions,
not claimed causes of an observed effect. Observe paired/per-graph truth-based
exact success; 260 syndrome bits per call and no physical verifier/tag.

Two additive files, existing helpers where practical, no generalized harness.
One four-file root, one log, no repair/retry. Independent review plus main
acceptance; do not merge delta spec until a separately requested archive.
