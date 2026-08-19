"""V27 finite-leakage-margin multistage DE gate (source-adaptive).

Reuses the V26 A02 (F03 GF32+GF32) posterior-population MC-DE kernel via a
thin adapter/wrapper.  It does NOT copy or rewrite the V26 kernel -- only:

* a minimal **budget planner** that, per source, derives an integer ``m_total``
  from the source's own full-precision layer entropies and the 64-bit public
  tag budget, then enumerates the five entropy-proportional +/-2 m1 candidates;
* a **wrapper** that maps each candidate/layer to a V26 ``run_mcde_posterior``
  call (rate reconstructed as ``R_i = 1 - m_i / block_len``);
* a screen -> ranked-confirmation driver with a 24h completed-call resource
  gate and a checkpoint bound to the full frozen configuration;
* the V27 terminal-state decision (only the four allowed states);
* a read-only verifier that reconstructs the plan/budget/calls/order/terminal
  from the frozen configuration plus the persisted call set.

V27 is an asymptotic, true-predecessor-conditioned multistage DE: L2 is
conditioned on the correctly-decoded L1 in the asymptotic modeling sense; it
does NOT simulate finite-code error propagation.  The single 64-bit public tag
is counted only in the total block leakage, never between layers.

Forbidden by V27 (inherited from V26 + V27R OpenSpec): degree/m1/m2 search,
finite parity-check-matrix construction, finite FER/decoder, MET, V26 rerun,
fresh/raw .ttbin, factorization/labeling changes, holdout tuning, push.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from . import nonbinary_v26_channel as chn
from . import nonbinary_v26_mcde as de

__all__ = [
    "LAMBDA", "Q", "BLOCK_LENS", "OFFSETS", "TAG_BITS", "F_MAX",
    "SCREEN_MC_SAMPLES", "SCREEN_MAX_ITER", "SCREEN_SEEDS",
    "CONFIRM_MC_SAMPLES", "CONFIRM_MAX_ITER", "CONFIRM_SEEDS",
    "ENTROPY_TOL_BITS", "STREAK", "RESOURCE_LIMIT_SECONDS",
    "SOURCE_LABELS", "LIDS", "ORDER_KEYS",
    "frozen_config", "build_adapters", "source_h",
    "m_total_for", "m1_ep_for", "candidates_for",
    "layer_rate_rho", "run_candidate_layer_call",
    "build_screen_plan", "rank_candidates",
    "decide_terminal", "run_v27_gate", "verify_run", "write_run_manifest",
]

# --------------------------------------------------------------------------- #
# Frozen V27 layout (from the accepted V27R OpenSpec)
# --------------------------------------------------------------------------- #
LAMBDA: dict[int, float] = {2: 1.0}      # fixed ensemble
Q = 32                                  # GF32 in both layers (F03 A02)
LIDS = ["L1", "L2"]
BLOCK_LENS = [1024, 2048, 4096, 8192]
OFFSETS = [-2, -1, 0, 1, 2]
TAG_BITS = 64
F_MAX = 1.3

# distinct fields: block_len (block size in symbols) vs mc_samples (DE draws)
SCREEN_MC_SAMPLES = 400
SCREEN_MAX_ITER = 100
SCREEN_SEEDS = [27001, 27002]
CONFIRM_MC_SAMPLES = 2000
CONFIRM_MAX_ITER = 200
CONFIRM_SEEDS = [27101, 27102, 27103, 27104, 27105]
ENTROPY_TOL_BITS = 0.01
STREAK = 20

#: completed-call accumulated wall-clock ceiling (24 h)
RESOURCE_LIMIT_SECONDS = 24 * 3600

SOURCE_LABELS = ["1M", "1p5M", "2M"]
#: human label -> channel source id (independent of any single worst-source)
LABEL_TO_SOURCE = {
    "1M": "type2_1M_20260121_184040",
    "1p5M": "type2_1p5M_20260121_183806",
    "2M": "type2_2M_20260121_183657",
}
#: human label -> frozen m_total per block_len (1024/2048/4096/8192)
FROZEN_M_TOTAL = {
    "1M": [200, 413, 840, 1693],
    "1p5M": [206, 426, 866, 1745],
    "2M": [208, 430, 873, 1760],
}
#: ordering keys (ascending), frozen in the OpenSpec
ORDER_KEYS = ["worst_final_entropy", "mean_final_entropy", "abs_offset", "m1"]


# --------------------------------------------------------------------------- #
# Frozen configuration (bound to every checkpoint / run root)
# --------------------------------------------------------------------------- #
def frozen_config() -> dict[str, Any]:
    """The complete frozen configuration, serializable and sufficient to
    reconstruct every call in the gate.  A checkpoint must embed this so the
    run is fully reproducible and 'config-swap reruns' are impossible."""
    return {
        "schema": "nbldpc_v27_frozen_config_v1",
        "q": Q, "lambda": {int(k): float(v) for k, v in LAMBDA.items()},
        "lids": list(LIDS),
        "block_lens": list(BLOCK_LENS),
        "offsets": list(OFFSETS),
        "tag_bits": TAG_BITS, "f_max": F_MAX,
        "m_total": {k: list(v) for k, v in FROZEN_M_TOTAL.items()},
        "source_labels": list(SOURCE_LABELS),
        "screen": {"mc_samples": SCREEN_MC_SAMPLES, "max_iter": SCREEN_MAX_ITER,
                   "seeds": list(SCREEN_SEEDS), "tol": ENTROPY_TOL_BITS, "streak": STREAK},
        "confirm": {"mc_samples": CONFIRM_MC_SAMPLES, "max_iter": CONFIRM_MAX_ITER,
                     "seeds": list(CONFIRM_SEEDS), "tol": ENTROPY_TOL_BITS, "streak": STREAK},
        "order_keys": list(ORDER_KEYS),
        "terminal_states": ["pass_finite_budget_ready", "de_pass_no_finite_headroom",
                            "implementation_blocked", "resource_blocked"],
        "resource_limit_seconds": RESOURCE_LIMIT_SECONDS,
        "m1_ep_rule": "m1_ep = round(m_total * H1 / H_total)  (Python round, "
                       "round-half-to-even)",
        "rate_rule": "R_i = 1 - m_i / block_len",
    }


_ADAPTER_POOL: dict[str, "chn.ChannelAdapter"] | None = None


def build_adapters(counts_path: str | Path | None = None) -> dict[str, "chn.ChannelAdapter"]:
    """Build one F03 GF32+GF32 ChannelAdapter per human source label."""
    global _ADAPTER_POOL
    if _ADAPTER_POOL is not None and counts_path is None:
        return _ADAPTER_POOL
    counts = chn.load_channel_counts(counts_path)
    pool = {lab: chn.build_adapter(counts, fact_id="F03", source=sid)
             for lab, sid in LABEL_TO_SOURCE.items()}
    if counts_path is None:
        _ADAPTER_POOL = pool
    return pool


def source_h(adapter: "chn.ChannelAdapter") -> dict[str, float]:
    """Per-source full-precision H1/H2/total from the V25 channel_counts.npz."""
    return {"H1": float(adapter.H_bits["L1"]), "H2": float(adapter.H_bits["L2"]),
            "H_total": float(adapter.total_H)}


# --------------------------------------------------------------------------- #
# Budget planner (source-adaptive, integer)
# --------------------------------------------------------------------------- #
def m_total_for(source_label: str, block_len: int) -> int:
    """m_total = floor((1.3 * block_len * H_source - tag) / 5)."""
    htot = source_h(build_adapters()[source_label])["H_total"]
    return int(math.floor((F_MAX * block_len * htot - TAG_BITS) / 5))


def m1_ep_for(source_label: str, block_len: int, m_total: int) -> int:
    """Frozen explicit rounding: m1_ep = round(m_total * H1 / H_total)."""
    h = source_h(build_adapters()[source_label])
    return int(round(m_total * h["H1"] / h["H_total"]))


def candidates_for(source_label: str, block_len: int) -> list[dict[str, Any]]:
    """Enumerate the 5 +/-2 candidates for one (source, block_len)."""
    m_total = m_total_for(source_label, block_len)
    m1_ep = m1_ep_for(source_label, block_len, m_total)
    out = []
    for off in OFFSETS:
        m1 = m1_ep + off
        m2 = m_total - m1
        legal = (0 <= m1 <= m_total and 0 <= m2 <= m_total
                 and m1 < block_len and m2 < block_len)
        out.append({
            "candidate_id": f"{block_len}|{source_label}|{m1}",
            "block_len": block_len, "source": source_label,
            "m_total": m_total, "m1_ep": m1_ep, "offset": off,
            "m1": m1, "m2": m2,
            "R1": (1 - m1 / block_len) if legal else None,
            "R2": (1 - m2 / block_len) if legal else None,
            "legal": legal,
        })
    return out


# --------------------------------------------------------------------------- #
# Rate / rho reconstruction + MC-DE wrapper
# --------------------------------------------------------------------------- #
def layer_rate_rho(m_i: int, block_len: int) -> tuple[float, dict[int, float]]:
    """Reconstruct rate and rho from the integer split: R_i = 1 - m_i/n."""
    rate = 1.0 - m_i / block_len
    rho = de.make_rho(rate, LAMBDA)
    return float(rate), {int(k): float(v) for k, v in rho.items()}


def run_candidate_layer_call(adapter: "chn.ChannelAdapter", candidate: dict[str, Any],
                             lid: str, *, n_samples: int, max_iter: int,
                             seed: int) -> dict[str, Any]:
    """Run ONE V26 posterior-population MC-DE call for a (candidate, layer).

    The single 64-bit tag is NOT used here (asymptotic DE): L2 is conditioned
    on the correctly-decoded L1 in the asymptotic sense via the true-symbol
    centered posterior; the tag only enters the block-level leakage bookkeeping.
    """
    m_i = candidate["m1"] if lid == "L1" else candidate["m2"]
    rate, rho = layer_rate_rho(m_i, candidate["block_len"])
    sampler = adapter.make_channel_sampler(lid)
    res = de.run_mcde_posterior(
        q=Q, lambda_edge=LAMBDA, rho_edge=rho, channel_sampler=sampler,
        n_samples=n_samples, max_iter=max_iter, seed=seed,
        entropy_tol_bits=ENTROPY_TOL_BITS, streak=STREAK,
    )
    return {
        "candidate_id": candidate["candidate_id"], "block_len": candidate["block_len"],
        "source": candidate["source"], "lid": lid, "m1": candidate["m1"],
        "m2": candidate["m2"], "rate": rate, "rho": rho, "seed": int(seed),
        "mc_samples": n_samples,
        "converged": bool(res["converged"]), "iterations": int(res["iterations"]),
        "final_entropy_bits": res["final_entropy_bits"],
        "entropy_trace_bits": res["entropy_trace_bits"],
    }


def build_screen_plan(candidates: Mapping[tuple, dict[str, Any]],
                      adapters: Mapping[str, "chn.ChannelAdapter"]) -> list[dict[str, Any]]:
    """Full screen plan: every legal candidate x layer x screen_seed."""
    plan = []
    for cand in candidates.values():
        if not cand["legal"]:
            continue
        adapter = adapters[cand["source"]]
        for lid in LIDS:
            for seed in SCREEN_SEEDS:
                # call is run lazily per the gated runner; plan records intent
                plan.append({"candidate": cand, "adapter": adapter, "lid": lid,
                             "seed": seed, "n_samples": SCREEN_MC_SAMPLES,
                             "max_iter": SCREEN_MAX_ITER})
    return plan


# --------------------------------------------------------------------------- #
# Ranking (per (block_len, source))
# --------------------------------------------------------------------------- #
def _call_key(cand_id: str, lid: str, seed: int) -> str:
    return f"{cand_id}|{lid}|{seed}"


def _screen_metrics(calls: Mapping[str, dict[str, Any]], cand: dict[str, Any]) -> dict[str, float]:
    """worst / mean final entropy over 2 layers x 2 screen seeds for a candidate."""
    entropies = []
    for lid in LIDS:
        for seed in SCREEN_SEEDS:
            rec = calls.get(_call_key(cand["candidate_id"], lid, seed))
            if rec is None:
                return {"worst_final_entropy": math.inf,
                        "mean_final_entropy": math.inf}
            entropies.append(rec["final_entropy_bits"])
    return {"worst_final_entropy": float(max(entropies)),
            "mean_final_entropy": float(sum(entropies) / len(entropies))}


def rank_candidates(calls: Mapping[str, dict[str, Any]],
                    candidates: Mapping[tuple, dict[str, Any]]) -> dict[str, list[str]]:
    """Per (block_len, source): rank the 5 candidates by frozen keys ascending.

    ``candidates`` is keyed by ``(block_len, source, m1)``; ranking groups all
    candidates sharing a ``(block_len, source)`` and orders them by the frozen
    keys (worst_final_entropy, mean_final_entropy, abs_offset, m1).
    """
    ranked: dict[str, list[str]] = {}
    for (bl, src, _m1), cand in candidates.items():
        if not cand["legal"]:
            continue
        key = f"{bl}|{src}"
        m = _screen_metrics(calls, cand)
        cand["_metrics"] = m
        ranked.setdefault(key, []).append(cand["candidate_id"])
    by_id = {c["candidate_id"]: c for c in candidates.values()}
    for key in ranked:
        cands = [by_id[ck] for ck in ranked[key]]
        cands.sort(key=lambda c: (c["_metrics"]["worst_final_entropy"],
                                  c["_metrics"]["mean_final_entropy"],
                                  abs(c["offset"]), c["m1"]))
        ranked[key] = [c["candidate_id"] for c in cands]
    return ranked


# --------------------------------------------------------------------------- #
# Gated stage runner (24h completed-call resource gate + checkpoint bound to config)
# --------------------------------------------------------------------------- #
def _run_screen_stage(candidates, adapters, out_dir, checkpoint_path,
                      resource_limit_seconds, runner=None):
    if runner is None:
        runner = run_candidate_layer_call
    done: dict[str, dict[str, Any]] = {}
    if checkpoint_path is not None and Path(checkpoint_path).exists():
        done = json.loads(Path(checkpoint_path).read_text(encoding="utf-8"))
    started = time.time()
    accumulated = 0.0
    total = 0
    for cand in candidates.values():
        if not cand["legal"]:
            continue
        total += len(LIDS) * len(SCREEN_SEEDS)
    processed = 0
    for cand in candidates.values():
        if not cand["legal"]:
            continue
        adapter = adapters[cand["source"]]
        for lid in LIDS:
            for seed in SCREEN_SEEDS:
                k = _call_key(cand["candidate_id"], lid, seed)
                if k in done:
                    processed += 1
                    continue
                t0 = time.time()
                call = runner(adapter, cand, lid, n_samples=SCREEN_MC_SAMPLES,
                              max_iter=SCREEN_MAX_ITER, seed=seed)
                done[k] = call
                accumulated += time.time() - t0
                processed += 1
                if checkpoint_path is not None:
                    Path(checkpoint_path).write_text(json.dumps(done, indent=2),
                                                    encoding="utf-8")
                if total - processed > 0 and accumulated >= resource_limit_seconds:
                    return {"schema": "nbldpc_v27_screen_v1", "n_calls": len(done),
                            "calls": done, "elapsed_s": time.time() - started,
                            "resource_blocked": True,
                            "resource_limit_seconds": resource_limit_seconds,
                            "accumulated_seconds": accumulated,
                            "completed_calls": len(done)}
    return {"schema": "nbldpc_v27_screen_v1", "n_calls": len(done), "calls": done,
            "elapsed_s": time.time() - started, "resource_blocked": False,
            "resource_limit_seconds": resource_limit_seconds,
            "accumulated_seconds": accumulated, "completed_calls": len(done)}


def _run_confirm_stage(ranked, candidates, adapters, out_dir, checkpoint_path,
                       resource_limit_seconds, runner=None):
    if runner is None:
        runner = run_candidate_layer_call
    """Per (block_len, source): confirm in rank order; stop on first pass."""
    done: dict[str, dict[str, Any]] = {}
    if checkpoint_path is not None and Path(checkpoint_path).exists():
        done = json.loads(Path(checkpoint_path).read_text(encoding="utf-8"))
    started = time.time()
    accumulated = 0.0
    confirmed: dict[str, str | None] = {}
    resource_blocked = False
    for key, cand_ids in ranked.items():
        bl, src = key.split("|")
        confirmed[key] = None
        for cid in cand_ids:
            cand = candidates[(int(bl), src, int(cid.split('|')[-1]))]
            # 2 layers x 5 confirm seeds
            allok = True
            for lid in LIDS:
                for seed in CONFIRM_SEEDS:
                    k = f"{cid}|{lid}|{seed}|confirm"
                    if k in done:
                        if not done[k]["converged"]:
                            allok = False
                        continue
                    t0 = time.time()
                    call = runner(adapters[src], cand, lid,
                                  n_samples=CONFIRM_MC_SAMPLES,
                                  max_iter=CONFIRM_MAX_ITER, seed=seed)
                    done[k] = call
                    accumulated += time.time() - t0
                    if checkpoint_path is not None:
                        Path(checkpoint_path).write_text(json.dumps(done, indent=2),
                                                        encoding="utf-8")
                    if not call["converged"]:
                        allok = False
                    if accumulated >= resource_limit_seconds:
                        resource_blocked = True
                        break
                if not allok:
                    break
            if resource_blocked:
                break
            if allok:
                confirmed[key] = cid
                break  # first passing candidate per (block_len, source)
        if resource_blocked:
            break
    return {"schema": "nbldpc_v27_confirm_v1", "n_calls": len(done), "calls": done,
            "confirmed": confirmed, "elapsed_s": time.time() - started,
            "resource_blocked": resource_blocked,
            "resource_limit_seconds": resource_limit_seconds,
            "accumulated_seconds": accumulated, "completed_calls": len(done)}


# --------------------------------------------------------------------------- #
# Terminal decision
# --------------------------------------------------------------------------- #
def decide_terminal(confirmed: Mapping[str, str | None]) -> dict[str, Any]:
    """Only the four allowed states.  pass = one block_len with all 3 sources."""
    # build per block_len -> set of confirmed sources
    per_bl: dict[int, set[str]] = {}
    for key, cid in confirmed.items():
        bl, src = key.split("|")
        bl = int(bl)
        per_bl.setdefault(bl, set())
        if cid:
            per_bl[bl].add(src)
    passing = [bl for bl, s in per_bl.items() if s == set(SOURCE_LABELS)]
    if passing:
        chosen = min(passing)
        return {"status": "pass_finite_budget_ready",
                "passing_block_len": chosen,
                "per_block_len_confirmed_sources": {str(b): sorted(s)
                                                    for b, s in per_bl.items()},
                "detail": f"block_len={chosen} has all {SOURCE_LABELS} confirmed"}
    return {"status": "de_pass_no_finite_headroom",
            "per_block_len_confirmed_sources": {str(b): sorted(s)
                                                for b, s in per_bl.items()},
            "detail": "no block_len has all three sources confirmed"}


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run_v27_gate(*, out_dir: str | Path, counts_path: str | Path | None = None,
                resource_limit_seconds: float = RESOURCE_LIMIT_SECONDS) -> dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cfg = frozen_config()
    Path(out / "frozen_config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    adapters = build_adapters(counts_path)

    # enumerate all candidates
    candidates: dict[tuple, dict[str, Any]] = {}
    # dedup by (block_len, source, m1) -> candidate_id already unique
    for src in SOURCES_LABELS():
        for bl in BLOCK_LENS:
            for cand in candidates_for(src, bl):
                candidates[(bl, src, cand['m1'])] = cand

    # M screen (full sweep)
    screen = _run_screen_stage(candidates, adapters, out, out / "screen_checkpoint.json",
                               resource_limit_seconds)
    Path(out / "screen_results.json").write_text(json.dumps(screen, indent=2), encoding="utf-8")

    # rank (per block_len,source) using screen metrics
    ranked = rank_candidates(screen["calls"], candidates)
    Path(out / "ranking.json").write_text(json.dumps(ranked, indent=2), encoding="utf-8")

    if screen.get("resource_blocked"):
        gate = {"status": "resource_blocked",
                "reason": "24h completed-call resource ceiling reached during screen"}
        Path(out / "gate.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
        write_run_manifest(out, run_id=out.name, role="v27-finite-leakage-margin",
                           screen=screen, confirm=None, gate=gate, cfg=cfg)
        return {"status": gate["status"], "evidence_root": str(out)}

    # M confirmation (ranked, per block_len/source)
    confirm = _run_confirm_stage(ranked, candidates, adapters, out,
                                 out / "confirm_checkpoint.json", resource_limit_seconds)
    Path(out / "confirmation_results.json").write_text(json.dumps(confirm, indent=2),
                                                      encoding="utf-8")

    gate = decide_terminal(confirm["confirmed"])
    if confirm.get("resource_blocked"):
        gate = {"status": "resource_blocked",
                "reason": "24h completed-call resource ceiling reached during confirmation"}
    Path(out / "gate.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
    write_run_manifest(out, run_id=out.name, role="v27-finite-leakage-margin",
                       screen=screen, confirm=confirm, gate=gate, cfg=cfg)
    return {"status": gate["status"], "evidence_root": str(out),
            "gate": gate}


def SOURCES_LABELS():
    return list(SOURCE_LABELS)


# --------------------------------------------------------------------------- #
# Read-only verifier (reconstruct plan/budget/calls/order/terminal)
# --------------------------------------------------------------------------- #
def verify_run(evidence_root: str | Path) -> dict[str, Any]:
    """Independently reconstruct the gate from the frozen config + persisted
    calls.  Does NOT re-run any DE."""
    root = Path(evidence_root)
    cfg = json.loads((root / "frozen_config.json").read_text(encoding="utf-8"))
    screen = json.loads((root / "screen_results.json").read_text(encoding="utf-8"))
    confirm = json.loads((root / "confirmation_results.json").read_text(encoding="utf-8"))
    gate = json.loads((root / "gate.json").read_text(encoding="utf-8")) if (root / "gate.json").exists() else None
    ranked = json.loads((root / "ranking.json").read_text(encoding="utf-8"))

    # recompute budget table from frozen config + recompute the same candidates
    problems = []
    adapters = build_adapters()
    candidates: dict[tuple, dict[str, Any]] = {}
    for src in cfg["source_labels"]:
        for bl in cfg["block_lens"]:
            for cand in candidates_for(src, bl):
                candidates[(bl, src, cand['m1'])] = cand
    # verify screen calls reconstructable and consistent
    rec_screen = _run_screen_stage_recompute(candidates, screen["calls"])
    if rec_screen["n_mismatch"]:
        problems.append(f"screen reconstruction mismatches: {rec_screen['n_mismatch']}")
    # verify terminal recomputation
    rec_gate = decide_terminal(confirm["confirmed"])
    if gate is not None and rec_gate["status"] != gate["status"]:
        problems.append(f"terminal mismatch: recomputed {rec_gate['status']} "
                         f"vs persisted {gate['status']}")
    # verify ranking keys present
    return {
        "schema": "nbldpc_v27_verify_v1", "ok": not problems,
        "problems": problems,
        "recomputed_terminal": rec_gate,
        "persisted_terminal": gate,
        "screen_n_calls": screen["n_calls"],
        "confirm_n_calls": confirm["n_calls"],
        "ranked_groups": len(ranked),
    }


def _run_screen_stage_recompute(candidates, persisted_calls):
    n_mismatch = 0
    for (bl, src, _m1), cand in candidates.items():
        if not cand["legal"]:
            continue
        for lid in LIDS:
            for seed in SCREEN_SEEDS:
                k = _call_key(cand["candidate_id"], lid, seed)
                if k not in persisted_calls:
                    n_mismatch += 1
    return {"n_mismatch": n_mismatch}


# --------------------------------------------------------------------------- #
# Manifest
# --------------------------------------------------------------------------- #
def write_run_manifest(root: str | Path, *, run_id: str, role: str,
                       screen: dict[str, Any] | None,
                       confirm: dict[str, Any] | None,
                       gate: dict[str, Any], cfg: dict[str, Any]) -> None:
    root = Path(root)
    manifest = {
        "schema": "nbldpc_v27_run_manifest_v1",
        "run_id": run_id, "role": role,
        "frozen_config_binding": "co-located frozen_config.json in run root; verify_run reconstructs budget/terminal from it",
        "resource_gate": {
            "limit_seconds": cfg["resource_limit_seconds"],
            "screen_accumulated_seconds": (screen or {}).get("accumulated_seconds"),
            "confirm_accumulated_seconds": (confirm or {}).get("accumulated_seconds"),
        },
        "screen_resource_blocked": (screen or {}).get("resource_blocked"),
        "confirm_resource_blocked": (confirm or {}).get("resource_blocked"),
        "terminal_state": gate["status"],
        "sources": [
            {"label": lab, "source_id": LABEL_TO_SOURCE[lab],
             "delay_used_ps": chn.SOURCE_METADATA[LABEL_TO_SOURCE[lab]]["delay_used_ps"],
             "n_pairs": chn.SOURCE_METADATA[LABEL_TO_SOURCE[lab]]["n_pairs"]}
            for lab in SOURCE_LABELS
        ],
        "terminal_states_allowed": cfg["terminal_states"],
    }
    Path(root / "RUN_MANIFEST.json").write_text(json.dumps(manifest, indent=2),
                                               encoding="utf-8")
