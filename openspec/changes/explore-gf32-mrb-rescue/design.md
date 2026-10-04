# Minimal design

Reuse accepted deep graph/BP and existing generic GF(q) MRB candidate helper.
Thin adapter checks raw syndrome, enumerates at most256 original-coordinate
candidates, scores all with the actual effective matched input prior, and
independently rechecks selected syndrome. Preserve BP result/provenance and
separate BP versus total rescue costs. GF32-specific tiny tests are required;
historical GF4 and q1024 diagnostic use is not acceptance for this batch.
