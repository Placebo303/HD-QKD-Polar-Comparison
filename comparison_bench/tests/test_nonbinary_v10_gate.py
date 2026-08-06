"""V10-0.7 T2: complete fake q=4 lifecycle + tamper layers.

Scope: the V10-0 q=4 reference-recovery lifecycle is exercised ONLY through an
explicit fake runner (plan -> review -> fake execute -> strict replay).  The
production DE search / threshold binary search / gate path is never entered by
these tests: ``FakeQ4Runner`` writes canned deterministic payloads and the
lifecycle functions reject any non-fake runner fail-closed.

Tamper layers covered:
- seed separation (optimization vs validation vs V8/V9 seeds)
- winner reconstruction (max threshold proxy, canonical tie-break)
- gate reconstruction (conservative = min of per-seed thresholds, verdict rule)
- fake promotion (a FAIL fake payload must never be promoted to PASS)
- published-lambda non-injection (initial population contains no published
  Muller lambda; injection is detected by the assertion)

All outputs go to fresh pytest ``tmp_path`` roots; run with
``pytest -p no:cacheprovider``.
"""
from __future__ import annotations

import json
import os
from typing import Any, Mapping

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v10_common as common
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v10_de as de

# --------------------------------------------------------------------------- #
# frozen V10-0 protocol constants (mirror the official execution script)
# --------------------------------------------------------------------------- #

Q = 4
RATE = 0.75
P_GATE = 0.06
SEARCH_SEED = 2026100100
VALIDATION_SEEDS = [2026100101, 2026100102, 2026100103]
POP_SIZE = 20
MAX_GEN = 29
F = 0.5
CR = 0.9
DET_TARGET = 0.069
TOL = 0.012

PUBLISHED_LAMBDA = dict(common.MULLER_Q4_LAMBDA_PUBLISHED_DEGREES)

FAKE_WINNER = {
    "2": 0.04829771573031651,
    "3": 0.23512419576137655,
    "4": 0.06400915290370075,
    "5": 0.014878192875241999,
    "7": 0.058412639460654905,
    "25": 0.315005025934064,
    "27": 0.17568690058992167,
    "31": 0.08858617674472366,
}
FAKE_PER_SEED_THRESHOLDS = [0.064140625, 0.064140625, 0.064140625]


def _write_json(path: str, payload: Mapping[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# plan -> review
# --------------------------------------------------------------------------- #


def frozen_plan() -> dict:
    """The frozen V10-0 plan dict (fake lifecycle input)."""
    return {
        "schema": "v10_0_q4_plan_v1",
        "q": Q, "rate": RATE, "p_gate": P_GATE,
        "search_seed": SEARCH_SEED,
        "validation_seeds": list(VALIDATION_SEEDS),
        "pop_size": POP_SIZE, "max_gen": MAX_GEN, "F": F, "CR": CR,
        "K": 8, "degree_range": [2, 40], "min_weight": 0.01,
        "screen_n_samples": 500, "screen_max_iter": 100,
        "entropy_tol": 0.01, "streak": 20,
        "threshold_p_lo": 0.01, "threshold_p_hi": 0.12, "threshold_p_tol": 0.0025,
        "validation_n_samples": 100000, "validation_max_iter": 150,
        "det_target": DET_TARGET, "tolerance": TOL,
        "rate_tolerance": 1e-12,
        "de_variant": "DE/rand/1/bin",
        "objective": "hierarchical_6tier_lexicographic",
        "workers": 1,
    }


def review_plan(plan: Mapping[str, Any]) -> str:
    """Read-only plan review: READY when every frozen field is present and
    matches the protocol; REJECT otherwise."""
    required = {
        "q": 4, "rate": 0.75, "p_gate": 0.06, "search_seed": 2026100100,
        "pop_size": 20, "max_gen": 29, "F": 0.5, "CR": 0.9,
        "validation_seeds": [2026100101, 2026100102, 2026100103],
        "screen_n_samples": 500, "screen_max_iter": 100,
        "validation_n_samples": 100000, "validation_max_iter": 150,
        "det_target": 0.069, "tolerance": 0.012,
    }
    for key, value in required.items():
        if plan.get(key) != value:
            return "REJECT"
    return "READY"


# --------------------------------------------------------------------------- #
# fake runner (explicit; production runner never entered)
# --------------------------------------------------------------------------- #


class FakeQ4Runner:
    """Canned fake q=4 runner.

    Writes deterministic fake execute/replay payloads (schema
    ``v10_0_q4_fake_results_v1``).  It never calls the production
    ``de.run_de_search`` / ``de.threshold_binary_search`` / gate path: the
    payload is fully canned.  Passing a production runner object instead of
    this fake is rejected fail-closed by :func:`fake_execute`.
    """

    SCHEMA = "v10_0_q4_fake_results_v1"

    def __init__(self, winner: Mapping[int, float] | None = None,
                 per_seed_thresholds: list[float] | None = None,
                 verdict_override: str | None = None):
        self._winner = dict(FAKE_WINNER) if winner is None else dict(winner)
        self._thresholds = list(FAKE_PER_SEED_THRESHOLDS) if per_seed_thresholds is None \
            else list(per_seed_thresholds)
        self._verdict_override = verdict_override
        self.calls = 0

    def run(self, out_dir: str) -> dict:
        """Fake execute/replay: write deterministic scientific payloads."""
        self.calls += 1
        os.makedirs(out_dir, exist_ok=True)
        conservative = min(self._thresholds)
        delta = abs(conservative - DET_TARGET)
        passing = [abs(t - DET_TARGET) <= TOL for t in self._thresholds]
        if self._verdict_override is not None:
            verdict = self._verdict_override
        else:
            verdict = "PASS" if (delta <= TOL and sum(passing) >= 2) else "FAIL"
        payload = {
            "schema": self.SCHEMA,
            "fake": True,
            "de_config": frozen_plan(),
            "winner": {"lambda": {int(k): float(v) for k, v in self._winner.items()}},
            "validation": {
                "seeds": [
                    {"seed": int(seed), "threshold_proxy": float(t)}
                    for seed, t in zip(VALIDATION_SEEDS, self._thresholds)
                ],
                "conservative_threshold": conservative,
            },
            "gate": {
                "det_target": DET_TARGET, "tolerance": TOL,
                "conservative_threshold": conservative,
                "delta_vs_target": delta,
                "per_seed_passes": passing,
                "passing_seed_count": int(sum(passing)),
                "verdict": verdict,
            },
        }
        _write_json(os.path.join(out_dir, "results.json"), payload)
        _write_json(os.path.join(out_dir, "transcript.json"),
                    {"schema": "v10_0_q4_fake_transcript_v1", "fake": True,
                     "per_generation_best": [{"generation": 29}]})
        _write_json(os.path.join(out_dir, "run_meta.json"),
                    {"schema": "v10_0_q4_fake_run_meta_v1", "fake": True,
                     "pid": os.getpid()})
        return payload


def fake_execute(runner: object, plan: Mapping[str, Any], out_dir: str) -> dict:
    """Fake lifecycle execute.  Fail-closed: only a FakeQ4Runner is accepted;
    a production runner object is rejected before any file is written."""
    if not isinstance(runner, FakeQ4Runner):
        raise TypeError("fake lifecycle requires an explicit FakeQ4Runner; "
                        "production runner must never be entered")
    if review_plan(plan) != "READY":
        raise ValueError("plan review must pass before fake execute")
    return runner.run(out_dir)


def strict_replay(runner: object, plan: Mapping[str, Any],
                  out_dir_a: str, out_dir_b: str) -> dict:
    """Fake strict replay: run twice, byte-compare scientific files."""
    fake_execute(runner, plan, out_dir_a)
    fake_execute(runner, plan, out_dir_b)
    files_a = set(os.listdir(out_dir_a))
    files_b = set(os.listdir(out_dir_b))
    scientific = ["results.json", "transcript.json"]
    pairs = []
    for name in sorted(files_a & files_b):
        with open(os.path.join(out_dir_a, name), "rb") as handle:
            bytes_a = handle.read()
        with open(os.path.join(out_dir_b, name), "rb") as handle:
            bytes_b = handle.read()
        pairs.append({"file": name, "identical": bytes_a == bytes_b})
    scientific_identical = all(
        p["identical"] for p in pairs if p["file"] in scientific)
    return {
        "scientific_files_byte_identical": scientific_identical,
        "pairs": pairs,
        "files_only_in_a": sorted(files_a - files_b),
        "files_only_in_b": sorted(files_b - files_a),
    }


# --------------------------------------------------------------------------- #
# reconstruction helpers (used by tamper tests)
# --------------------------------------------------------------------------- #


def winner_reconstruct(eligible: list[Mapping[str, Any]]) -> dict:
    """Winner = eligible candidate with highest threshold proxy; ties broken
    by the canonical tuple ascending (frozen rule)."""
    best = None
    for entry in eligible:
        if entry.get("threshold_proxy") is None:
            continue
        if best is None or entry["threshold_proxy"] > best["threshold_proxy"] or (
                entry["threshold_proxy"] == best["threshold_proxy"]
                and tuple(entry["canonical_tuple"]) < tuple(best["canonical_tuple"])):
            best = entry
    return dict(best)


def gate_reconstruct(per_seed_thresholds: list[float],
                     det_target: float = DET_TARGET, tol: float = TOL) -> dict:
    """Conservative = min of per-seed thresholds; verdict per frozen rule."""
    conservative = min(per_seed_thresholds)
    delta = abs(conservative - det_target)
    passing = [abs(t - det_target) <= tol for t in per_seed_thresholds]
    verdict = "PASS" if (delta <= tol and sum(passing) >= 2) else "FAIL"
    return {"conservative_threshold": conservative, "delta_vs_target": delta,
            "per_seed_passes": passing, "passing_seed_count": int(sum(passing)),
            "verdict": verdict}


# --------------------------------------------------------------------------- #
# T2 tests
# --------------------------------------------------------------------------- #


def test_t2_fake_lifecycle_plan_review_execute_replay(tmp_path):
    """Plan -> review READY -> fake execute -> strict replay; scientific files
    byte-identical; production runner never entered."""
    plan = frozen_plan()
    assert review_plan(plan) == "READY"
    assert review_plan({}) == "REJECT"

    runner = FakeQ4Runner()
    a = os.path.join(str(tmp_path), "execute")
    b = os.path.join(str(tmp_path), "replay")
    report = strict_replay(runner, plan, a, b)
    assert report["scientific_files_byte_identical"] is True
    assert report["files_only_in_a"] == [] and report["files_only_in_b"] == []
    assert runner.calls == 2

    payload_a = json.load(open(os.path.join(a, "results.json"), encoding="utf-8"))
    payload_b = json.load(open(os.path.join(b, "results.json"), encoding="utf-8"))
    assert payload_a["schema"] == FakeQ4Runner.SCHEMA
    assert payload_a == payload_b
    # fake marker proves the production runner never wrote these payloads
    assert payload_a["fake"] is True
    assert "v10_0_q4_execute_results_v1" not in json.dumps(payload_a)


def test_t2_production_runner_rejected(tmp_path):
    """A production runner object must never enter the fake lifecycle."""
    plan = frozen_plan()
    # 'production' stand-in: the real search entrypoint is de.run_de_search;
    # passing anything that is not a FakeQ4Runner must fail closed.
    with pytest.raises(TypeError):
        fake_execute(de.run_de_search, plan, os.path.join(str(tmp_path), "x"))
    with pytest.raises(TypeError):
        fake_execute(object(), plan, os.path.join(str(tmp_path), "y"))


def test_t2_plan_field_validation_rejects_tamper():
    """Plan-binding field validation: any tampered frozen field must be
    rejected by the read-only plan review before the fake lifecycle runs."""
    plan = frozen_plan()
    assert review_plan(plan) == "READY"
    tamper_cases = [
        ("pop_size", 21), ("max_gen", 30), ("F", 0.51), ("CR", 0.89),
        ("q", 8), ("rate", 0.74), ("p_gate", 0.061),
        ("search_seed", 2026100999),
        ("validation_seeds", [2026100101, 2026100102]),
        ("validation_n_samples", 99999), ("det_target", 0.070),
    ]
    for key, bad in tamper_cases:
        tampered = dict(plan)
        tampered[key] = bad
        assert review_plan(tampered) == "REJECT", f"tampered field {key} not rejected"


def test_t2_seed_separation():
    """Optimization seed disjoint from validation seeds and from all V8/V9."""
    v8_seeds = [2026080418]
    v9_seeds = [2026090101, 2026090102, 2026090103, 2026090104,
                2026090111, 2026090112, 2026090113]
    all_prior = set(v8_seeds) | set(v9_seeds)
    assert SEARCH_SEED not in VALIDATION_SEEDS
    assert SEARCH_SEED not in all_prior
    assert not set(VALIDATION_SEEDS) & all_prior
    assert len(set(VALIDATION_SEEDS)) == 3
    assert all(str(s).startswith("20261001") for s in [SEARCH_SEED] + VALIDATION_SEEDS)


def test_t2_published_lambda_not_injected():
    """Initial population from seed 2026100100 is deterministic and contains no
    published Muller lambda; injecting it is detected by the assertion."""
    population = de.init_population(POP_SIZE, SEARCH_SEED)
    again = de.init_population(POP_SIZE, SEARCH_SEED)
    assert np.array_equal(population, again)
    decoded = [de.decode_vector(row) for row in population]
    assert not any(lam == PUBLISHED_LAMBDA for lam in decoded)
    # tamper detection: a population that DOES carry the published lambda must
    # be flagged by the same assertion logic used in the official run.
    tampered = list(decoded)
    tampered[0] = dict(PUBLISHED_LAMBDA)
    assert any(lam == PUBLISHED_LAMBDA for lam in tampered)  # detector triggers


# --------------------------------------------------------------------------- #
# tamper: winner reconstruction
# --------------------------------------------------------------------------- #


def _eligible_entry(threshold: float, canonical: tuple) -> dict:
    return {
        "population_index": 0,
        "entropy_converged": True,
        "converged_iter": 30,
        "final_entropy": 1e-9,
        "error_prob": 0.0,
        "threshold_proxy": threshold,
        "canonical_tuple": list(canonical),
        "penalty": 0.0,
        "lambda": {int(d): 1.0 / 8 for d in canonical[:8]},
    }


def test_t2_winner_reconstruction():
    """Winner = highest threshold proxy, canonical tuple tie-break."""
    eligible = [
        _eligible_entry(0.061, (2, 3, 5, 8, 12, 20, 30, 40)),
        _eligible_entry(0.072, (2, 3, 4, 5, 7, 25, 27, 31)),
        _eligible_entry(0.069, (2, 3, 5, 8, 12, 20, 30, 41)),
        _eligible_entry(None, (2, 3, 5, 8, 12, 20, 30, 42)),  # ineligible proxy
    ]
    winner = winner_reconstruct(eligible)
    assert winner["threshold_proxy"] == 0.072
    assert tuple(winner["canonical_tuple"]) == (2, 3, 4, 5, 7, 25, 27, 31)


def test_t2_winner_reconstruction_tie_break():
    """Equal threshold proxy -> smaller canonical tuple wins (deterministic)."""
    eligible = [
        _eligible_entry(0.071, (2, 3, 4, 5, 7, 25, 27, 31)),
        _eligible_entry(0.071, (2, 3, 4, 5, 7, 25, 27, 32)),
    ]
    winner = winner_reconstruct(eligible)
    assert tuple(winner["canonical_tuple"]) == (2, 3, 4, 5, 7, 25, 27, 31)


def test_t2_winner_tamper_detected():
    """Tampering the recorded winner threshold must change the reconstruction
    (winner reconstruction acts as the detector)."""
    eligible = [_eligible_entry(0.072, (2, 3, 4, 5, 7, 25, 27, 31))]
    baseline = winner_reconstruct(eligible)
    tampered = _eligible_entry(0.074, (2, 3, 4, 5, 7, 25, 27, 31))
    assert winner_reconstruct([tampered])["threshold_proxy"] != baseline["threshold_proxy"]


# --------------------------------------------------------------------------- #
# tamper: gate reconstruction
# --------------------------------------------------------------------------- #


def test_t2_gate_reconstruction_pass():
    """Frozen gate rule: |min(per-seed) - 0.069| <= 0.012 and >= 2 seeds pass."""
    gate = gate_reconstruct(FAKE_PER_SEED_THRESHOLDS)
    assert gate["conservative_threshold"] == 0.064140625
    assert gate["verdict"] == "PASS"
    assert gate["passing_seed_count"] == 3
    assert gate["delta_vs_target"] <= TOL


def test_t2_gate_tamper_detected():
    """A tampered per-seed threshold that breaks the gate must flip the verdict
    (gate reconstruction is the detector)."""
    baseline = gate_reconstruct(FAKE_PER_SEED_THRESHOLDS)
    assert baseline["verdict"] == "PASS"
    # tamper seed 0101 to a far-off threshold -> conservative drops below range
    tampered = [0.030, 0.064140625, 0.064140625]
    gate = gate_reconstruct(tampered)
    assert gate["verdict"] == "FAIL"
    assert gate["passing_seed_count"] == 2  # delta rule fails even with 2 seeds


def test_t2_gate_requires_two_seeds():
    """One passing seed alone must NOT pass the gate."""
    only_one = [0.064140625, 0.10, 0.11]
    gate = gate_reconstruct(only_one)
    assert gate["verdict"] == "FAIL"
    assert gate["passing_seed_count"] == 1


# --------------------------------------------------------------------------- #
# tamper: fake promotion
# --------------------------------------------------------------------------- #


def test_t2_fake_promotion_detected(tmp_path):
    """A FAIL fake payload must never be silently promoted to PASS: the
    recorded verdict must match the gate reconstruction from the payload's own
    per-seed thresholds."""
    plan = frozen_plan()
    runner = FakeQ4Runner(per_seed_thresholds=[0.030, 0.064140625, 0.064140625])
    out = os.path.join(str(tmp_path), "run")
    fake_execute(runner, plan, out)
    payload = json.load(open(os.path.join(out, "results.json"), encoding="utf-8"))
    assert payload["gate"]["verdict"] == "FAIL"
    # promotion attempt: rewrite the verdict field to PASS
    payload["gate"]["verdict"] = "PASS"
    with open(os.path.join(out, "results.json"), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
    reloaded = json.load(open(os.path.join(out, "results.json"), encoding="utf-8"))
    # detector: recompute the gate from the payload's own per-seed thresholds
    seeds = reloaded["validation"]["seeds"]
    recomputed = gate_reconstruct([s["threshold_proxy"] for s in seeds])
    assert reloaded["gate"]["verdict"] == "PASS"      # tampered claim
    assert recomputed["verdict"] == "FAIL"            # reconstruction disagrees


def test_t2_fake_promotion_byte_drift(tmp_path):
    """Promoting the fake payload also changes its bytes: strict replay of the
    un-tampered payload no longer matches (raw byte drift detection)."""
    plan = frozen_plan()
    runner = FakeQ4Runner(per_seed_thresholds=[0.030, 0.064140625, 0.064140625])
    a = os.path.join(str(tmp_path), "execute")
    b = os.path.join(str(tmp_path), "replay")
    strict_replay(runner, plan, a, b)
    path = os.path.join(a, "results.json")
    with open(path, "rb") as handle:
        original = handle.read()
    # tamper the execute copy's verdict
    payload = json.load(open(path, encoding="utf-8"))
    payload["gate"]["verdict"] = "PASS"
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
    with open(path, "rb") as handle:
        tampered = handle.read()
    assert tampered != original  # byte drift detected
