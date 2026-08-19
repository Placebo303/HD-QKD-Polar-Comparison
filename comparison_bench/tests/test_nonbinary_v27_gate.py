"""V27 finite-leakage-margin gate — T0/T1 focused tests.

Covers: frozen config completeness; exact source-adaptive budget table; candidate
enumeration / dedup / legality; m1_ep rounding rule; rate/rho reconstruction;
source metadata (delay_used_ps, n_pairs); ordering keys determinism; terminal
precedence; 24h completed-call resource gate + checkpoint binding.  No production
DE / no V26 rerun / no fresh .ttbin.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v26_channel as chn
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v27_gate as v27

FROZEN_M_TOTAL = {"1M": [200, 413, 840, 1693],
                  "1p5M": [206, 426, 866, 1745],
                  "2M": [208, 430, 873, 1760]}
BLOCK_LENS = [1024, 2048, 4096, 8192]


# --------------------------------------------------------------------------- #
# T0 — compile / import / structural
# --------------------------------------------------------------------------- #
def test_import_and_frozen_config_keys():
    cfg = v27.frozen_config()
    for k in ("q", "lambda", "lids", "block_lens", "offsets", "tag_bits", "f_max",
              "m_total", "screen", "confirm", "order_keys", "terminal_states",
              "resource_limit_seconds", "m1_ep_rule", "rate_rule"):
        assert k in cfg, f"missing frozen-config key {k}"
    assert cfg["q"] == 32
    assert cfg["terminal_states"] == [
        "pass_finite_budget_ready", "de_pass_no_finite_headroom",
        "implementation_blocked", "resource_blocked"]
    # explicit ruling present
    assert "round(m_total * H1 / H_total)" in cfg["m1_ep_rule"]
    assert cfg["rate_rule"] == "R_i = 1 - m_i / block_len"
    # block_len vs mc_samples are distinct fields in screen/confirm
    assert "mc_samples" in cfg["screen"] and "mc_samples" in cfg["confirm"]
    assert "block_lens" in cfg and "mc_samples" not in cfg  # block_len != mc_samples


def test_candidate_enumeration_dedup_legality():
    cands = {}
    for src in v27.SOURCE_LABELS:
        for bl in BLOCK_LENS:
            lst = v27.candidates_for(src, bl)
            assert len(lst) == 5, (src, bl, len(lst))
            for c in lst:
                assert c["offset"] in v27.OFFSETS
                assert (c["m1"] + c["m2"]) == c["m_total"]
                # candidate_id unique: (block_len, source, m1)
                assert c["candidate_id"] not in cands
                cands[c["candidate_id"]] = c
                # all legal in frozen table
                assert c["legal"]
                assert 0 <= c["m1"] <= c["m_total"]
                assert 0 <= c["m2"] <= c["m_total"]
                assert c["m1"] < bl and c["m2"] < bl


# --------------------------------------------------------------------------- #
# T1 — exact budget, m1_ep, rate/rho, source metadata, terminal, resource
# --------------------------------------------------------------------------- #
def test_m_total_frozen_table():
    for src in v27.SOURCE_LABELS:
        for i, bl in enumerate(BLOCK_LENS):
            got = v27.m_total_for(src, bl)
            assert got == FROZEN_M_TOTAL[src][i], (src, bl, got, FROZEN_M_TOTAL[src][i])


def test_m1_ep_rounding_rule_and_f_margin():
    adapters = v27.build_adapters()
    for src in v27.SOURCE_LABELS:
        h = v27.source_h(adapters[src])
        for i, bl in enumerate(BLOCK_LENS):
            mt = FROZEN_M_TOTAL[src][i]
            m1ep = v27.m1_ep_for(src, bl, mt)
            # explicit rule: round(m_total * H1 / H_total)
            assert m1ep == int(round(mt * h["H1"] / h["H_total"])), (src, bl)
            # realized total f < 1.3 (positive but small finite headroom)
            f = (5 * mt + 64) / bl / h["H_total"]
            assert 0.0 < f < 1.3, (src, bl, f)


def test_rate_rho_reconstruction():
    rate, rho = v27.layer_rate_rho(m_i=6, block_len=1024)
    assert abs(rate - (1 - 6 / 1024)) < 1e-12
    assert abs(sum(rho.values()) - 1.0) < 1e-9
    # concentrated around 1/(1-rate) ~ 171
    assert all(d >= 100 for d in rho)


def test_source_metadata():
    for lab in v27.SOURCE_LABELS:
        sid = v27.LABEL_TO_SOURCE[lab]
        md = chn.SOURCE_METADATA[sid]
        assert md["delay_used_ps"] in (-50, 50)
        assert md["n_pairs"] > 0


def test_ordering_keys_deterministic():
    # two candidates for the SAME (block_len, source): lower worst entropy ranks first
    ca = {"candidate_id": "1024|1M|6", "block_len": 1024, "source": "1M",
          "m_total": 200, "m1_ep": 6, "offset": 0, "m1": 6, "m2": 194, "legal": True}
    cb = {"candidate_id": "1024|1M|8", "block_len": 1024, "source": "1M",
          "m_total": 200, "m1_ep": 6, "offset": 2, "m1": 8, "m2": 192, "legal": True}
    calls = {
        "1024|1M|6|L1|27001": {"final_entropy_bits": 0.05},
        "1024|1M|6|L2|27001": {"final_entropy_bits": 0.04},
        "1024|1M|8|L1|27001": {"final_entropy_bits": 0.10},
        "1024|1M|8|L2|27001": {"final_entropy_bits": 0.09},
    }
    # candidates keyed by (block_len, source, m1)
    ranked = v27.rank_candidates(
        calls, {(1024, "1M", 6): ca, (1024, "1M", 8): cb})
    # ca has lower worst entropy (0.05) -> ranks first
    assert ranked["1024|1M"][0] == "1024|1M|6"
    assert ranked["1024|1M"][1] == "1024|1M|8"


def test_terminal_pass_detection():
    confirmed = {"1024|1M": "1024|1M|6", "1024|1p5M": "1024|1p5M|6",
                 "1024|2M": "1024|2M|6", "2048|1M": None, "2048|1p5M": None,
                 "2048|2M": None}
    g = v27.decide_terminal(confirmed)
    assert g["status"] == "pass_finite_budget_ready"
    assert g["passing_block_len"] == 1024


def test_terminal_no_headroom():
    confirmed = {"1024|1M": "1024|1M|6", "1024|1p5M": None, "1024|2M": None}
    g = v27.decide_terminal(confirmed)
    assert g["status"] == "de_pass_no_finite_headroom"


def _fake_runner(adapter, cand, lid, *, n_samples, max_iter, seed):
    return {"candidate_id": cand["candidate_id"], "block_len": cand["block_len"],
            "source": cand["source"], "lid": lid, "m1": cand["m1"], "m2": cand["m2"],
            "rate": 0.0, "rho": {}, "seed": int(seed), "mc_samples": n_samples,
            "converged": True, "iterations": 1, "final_entropy_bits": 0.0,
            "entropy_trace_bits": [0.0]}


def test_readonly_verify_reconstructs_run():
    # read-only verifier over the persisted additive run root (no DE execution)
    from pathlib import Path
    root = Path("comparison_bench/outputs_comparison/nonbinary_diagnostics/"
                "nbldpc_v27r_finite_leakage_margin/run_01")
    if not (root / "gate.json").exists():
        pytest.skip("V27 run_01 evidence not present")
    vr = v27.verify_run(root)
    assert vr["ok"] is True
    assert vr["problems"] == []
    assert vr["recomputed_terminal"]["status"] == "pass_finite_budget_ready"
    assert vr["recomputed_terminal"]["passing_block_len"] == 1024
    assert vr["persisted_terminal"]["status"] == "pass_finite_budget_ready"
    assert vr["screen_n_calls"] == 240
    assert vr["confirm_n_calls"] == 120
    assert vr["ranked_groups"] == 12


def test_resource_gate_completed_call_ceiling(tmp_path):
    # inject a fake runner so T1 exercises the gated-runner path without the
    # real MCDE kernel; resource_limit=0.0 is deterministic (block after 1st call)
    adapters = v27.build_adapters()
    cand = v27.candidates_for("1M", 1024)[2]  # m1_ep, legal
    screen = v27._run_screen_stage(
        {(1024, "1M", cand["m1"]): cand}, adapters, tmp_path, None,
        resource_limit_seconds=0.0, runner=_fake_runner)
    assert screen["resource_blocked"] is True
    # at least one completed call is preserved when the ceiling trips
    assert screen["completed_calls"] >= 1
    # the stage never writes the orchestrator's frozen_config
    assert (tmp_path / "frozen_config.json").exists() is False
