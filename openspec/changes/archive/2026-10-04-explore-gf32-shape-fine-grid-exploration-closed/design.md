# Design

Reuse accepted graph/preflight, one-pass label alignment, T0/field, sampling,
pairing and decoder helpers unchanged. Prior runner orchestration is tied to
its old grid/root/UUID; do not parameterize it by mutating module globals.
Write explicit batch-only orchestration in a new CLI, preserving schemas and
the full retained-clause index in the packet. No generalized scan framework.

Grid `[.625,.600,.575,.550,.525,.500,.475]`, CONTROL24 calls each until first
5..19; new prefix gf32-shape-fine-v1, same six seeds3801–3806 and n128/m52
profile, same2M marginal shape and unchanged decoder/prior floor. Candidate
never chooses point. Holdout192 paired frames only after admission; each
attempted call260-bit syndrome, no implemented physical verifier/tag.

Max168+384=552 calls,1800s/120s/4GiB, one fresh four-file root/log. No repair,
rerun or tuning. Preserve incomplete unknowns and no denominator for unstarted
arms. Independent reviews and main acceptance; original EXPLORE science
ceiling remains binding. New user grant resolves prior NOT GRANTED draft.
