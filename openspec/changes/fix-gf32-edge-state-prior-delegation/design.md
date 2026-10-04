# Minimal correction

Delegate the original prior to v35; keep a cleaned copy solely as state.log_prior. Reuse the existing helper and paired runner, replacing only this delegation and the successor's frozen UUID/root/seed/exclusion/contract constants. Tests retain existing numerical/lifecycle coverage and add raw-delegation and explicit saved synthetic first-frame numerical regression. No new loop, tolerance, algorithm, graph, scoring, verification or framework.
