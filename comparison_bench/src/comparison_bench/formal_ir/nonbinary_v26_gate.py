"""V26 channel-informed multilevel DE gate (A01 F01 GF512+GF2 / A02 F03 GF32+GF32).

M0  layer-channel adapter semantic gate
M1  mechanism reference tests (posterior MC-DE kernel)
M2  fixed-ensemble screen (lambda={2:1}, harmonic-exact concentrated checks,
    f in {1.3,1.6,2.0})
M3  five-seed confirmation on each architecture's lowest passing f
M4  terminal state (pass_target_f13 / target_fail_slack_pass /
    fixed_ensemble_no_convergence / implementation_blocked_layer_channel_semantics /
    resource_blocked)

Forbidden by V26: degree random search, finite codes, FER, MET, fresh
qualification, raw .ttbin, public residual, Alice-oracle, holdout tuning, push.
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
from . import nonbinary_v26_verify as vfy
from .nonbinary_v25_gate import FACTORIZATIONS, F_LAYER_ORDER, join_label, split_label

__all__ = [
    "ARCH_LAYERS", "ARCH_Q", "ARCH_WIDTH", "SOURCES", "WORST_H",
    "SCREEN_F", "SCREEN_SEEDS", "SCREEN_N", "SCREEN_MAX_ITER",
    "CONFIRM_SEEDS", "CONFIRM_N", "CONFIRM_MAX_ITER",
    "ENTROPY_TOL_BITS", "STREAK", "LAMBDA", "RESOURCE_LIMIT_SECONDS",
    "build_screen_plan", "target_rate_for", "run_m0_gate", "run_m1_gate",
    "run_screen", "run_confirmation", "decide_terminal", "run_v26_gate",
    "verify_run", "write_run_manifest",
]

# Frozen V26 layout
ARCH_LAYERS = {"A01": ["L1", "L2"], "A02": ["L1", "L2"]}
ARCH_Q = {"A01": {"L1": 512, "L2": 2}, "A02": {"L1": 32, "L2": 32}}
ARCH_WIDTH = {"A01": {"L1": 9, "L2": 1}, "A02": {"L1": 5, "L2": 5}}
SOURCES = list(chn.SOURCES_ORDER)
LAMBDA = {2: 1.0}

# worst-source layer entropy (bits/symbol), from V25 layer_conditional_entropy
WORST_H = {
    "A01": {"L1": 0.41624778, "L2": 0.41631494},
    "A02": {"L1": 0.02566205, "L2": 0.80690067},
}

SCREEN_F = [1.3, 1.6, 2.0]
SCREEN_SEEDS = [26001, 26002]
SCREEN_N = 400
SCREEN_MAX_ITER = 100
CONFIRM_SEEDS = [26101, 26102, 26103, 26104, 26105]
CONFIRM_N = 2000
CONFIRM_MAX_ITER = 200
ENTROPY_TOL_BITS = 0.01
STREAK = 20

#: Completed-call accumulated wall-clock resource ceiling (design section 4):
#: once the running total of completed DE-call wall time reaches this and calls
#: still remain, all finished calls are saved and no new call is started, and
#: the terminal state becomes ``resource_blocked``.  24 h in seconds.
RESOURCE_LIMIT_SECONDS = 24 * 3600

#: V25 layer entropy reference (per arch/source) for the 1e-3 adapter gate.
V25_H = {
    "A01": {
        "type2_1M_20260121_184040": (0.40015934, 0.40087848),
        "type2_1p5M_20260121_183806": (0.41358107, 0.41198498),
        "type2_2M_20260121_183657": (0.41624778, 0.41631494),
    },
    "A02": {
        "type2_1M_20260121_184040": (0.02428055, 0.77675728),
        "type2_1p5M_20260121_183806": (0.02519950, 0.80036655),
        "type2_2M_20260121_183657": (0.02566205, 0.80690067),
    },
}
ADAPTER_TOL = 1e-3


def target_rate_for(arch: str, lid: str, f: float) -> float:
    return de.target_rate_layer(f, WORST_H[arch][lid], ARCH_WIDTH[arch][lid])


def build_screen_plan() -> list[dict[str, Any]]:
    plan = []
    for arch in ARCH_LAYERS:
        for lid in ARCH_LAYERS[arch]:
            for f in SCREEN_F:
                rate = target_rate_for(arch, lid, f)
                rho = de.make_rho(rate, LAMBDA)
                for src in SOURCES:
                    for seed in SCREEN_SEEDS:
                        plan.append({
                            "arch": arch, "layer": lid, "f": float(f),
                            "rate": float(rate), "rho": {int(k): float(v) for k, v in rho.items()},
                            "source": src, "seed": int(seed),
                            "q": ARCH_Q[arch][lid],
                        })
    return plan


# --------------------------------------------------------------------------- #
# M0 layer-channel adapter semantic gate
# --------------------------------------------------------------------------- #

def run_m0_gate(adapters: Mapping[str, Mapping[str, "chn.ChannelAdapter"]],
                counts: Mapping[str, np.ndarray]) -> dict[str, Any]:
    """Validate the per-layer posterior adapter semantics.

    ``adapters[arch][source]`` is a ChannelAdapter.  Checks per (arch,source):
    posterior non-negative + normalized; correct GF domain; adapter entropy vs
    V25 layer entropy within ``ADAPTER_TOL``; factorization invertible; layer-2
    genuinely conditioned on layer-1; +-1 direction preserved; three sources
    kept independent (not merged).
    """
    problems: list[str] = []
    detail: dict[str, Any] = {}
    rng = np.random.default_rng(2026)
    for arch in ARCH_LAYERS:
        for src in SOURCES:
            ad = adapters[arch][src]
            keys = ARCH_LAYERS[arch]
            # domain
            for lid in keys:
                if ARCH_Q[arch][lid] != (chn.Q[arch][lid] if arch in chn.Q else 0):
                    problems.append(f"{arch}/{src}/{lid} domain mismatch")
            # posterior nonneg + normalized via sampler
            for lid in keys:
                sampler = ad.make_channel_sampler(lid)
                rows = np.asarray(sampler(200, rng), dtype=np.float64)
                if np.any(rows < 0.0) or not np.all(np.isfinite(rows)):
                    problems.append(f"{arch}/{src}/{lid} non-finite/non-neg posterior")
                sums = rows.sum(axis=1)
                if not np.all(np.abs(sums - 1.0) < 1e-6):
                    problems.append(f"{arch}/{src}/{lid} posterior not normalized")
            # entropy vs V25
            hgot = ad.H_bits
            hv25 = dict(zip(keys, V25_H[arch][src]))
            errs = {lid: abs(hgot[lid] - hv25[lid]) for lid in keys}
            if any(e > ADAPTER_TOL for e in errs.values()):
                problems.append(f"{arch}/{src} adapter entropy outside 1e-3: {errs}")
            # factorization invertible (natural labeling)
            if not _factorization_invertible(arch):
                problems.append(f"{arch} factorization not invertible")
            # layer-2 conditioned on layer-1
            if not _l2_depends_on_l1(ad):
                problems.append(f"{arch}/{src} L2 posterior independent of known L1")
            # +-1 direction preserved: posterior differs between B and B+1
            if not _direction_preserved(ad):
                problems.append(f"{arch}/{src} +-1 direction not preserved")
            detail[f"{arch}:{src}"] = {
                "adapter_H": {k: float(v) for k, v in hgot.items()},
                "v25_H": {k: float(v) for k, v in hv25.items()},
                "abs_err": {k: float(v) for k, v in errs.items()},
                "source_label": ad.source_label,
                "delay_used_ps": ad.delay_used_ps,
                "n_pairs": ad.n_pairs,
            }
    # source separation: each source has a distinct, non-merged adapter
    merged = []
    for arch in ARCH_LAYERS:
        hs = [tuple(round(adapters[arch][s].H_bits[l], 8) for l in ARCH_LAYERS[arch]) for s in SOURCES]
        if len(set(hs)) < len(hs):
            merged.append(arch)
    if merged:
        problems.append(f"sources merged: {merged}")
    ok = not problems
    return {"schema": "nbldpc_v26_m0_v1", "ok": bool(ok), "problems": problems,
            "detail": detail, "adapter_tol": ADAPTER_TOL}


def _factorization_invertible(arch: str) -> bool:
    fact = "F01" if arch == "A01" else "F03"
    vals = np.array([0, 1, 255, 511, 555, 1023, 700, 42, 987, 5, 333, 1010], dtype=np.int64)
    for a in vals:
        layers = split_label(np.array([a]), fact, "L01_natural")
        back = join_label(layers, fact, "L01_natural")
        if int(back[0]) != int(a):
            return False
    return True


def _l2_depends_on_l1(ad: "chn.ChannelAdapter") -> bool:
    lids = ad.lids
    if len(lids) < 2:
        return True  # no L2
    # find a B where two distinct L1 values both have support and give
    # measurably different L2 posteriors
    b = np.arange(chn.V25_Q, dtype=np.int64)
    pb = ad.p_b
    for bb in range(chn.V25_Q):
        if pb[bb] <= 0:
            continue
        supp_u1 = np.nonzero(ad.p_u1_gb[:, bb] > 1e-9)[0]
        if supp_u1.size < 2:
            continue
        u1a, u1b = int(supp_u1[0]), int(supp_u1[1])
        row_a = ad.posterior_rows("L2", np.array([bb]), np.array([u1a]))[0]
        row_b = ad.posterior_rows("L2", np.array([bb]), np.array([u1b]))[0]
        if np.max(np.abs(row_a - row_b)) > 1e-9:
            return True
    return False


def _direction_preserved(ad: "chn.ChannelAdapter") -> bool:
    """+-1 direction: shifting the observed B by +1 must change the full-symbol
    posterior ``P(A|B)`` measurably (direction is a modeled channel feature).
    Uses the source-of-truth conditional ``ad.P_a_gb`` directly."""
    for b0 in (500, 700, 900, 100, 512):
        p0 = ad.P_a_gb[:, b0]
        p1 = ad.P_a_gb[:, (b0 + 1) % chn.V25_Q]
        if np.max(np.abs(p0 - p1)) > 1e-9:
            return True
    return False


# --------------------------------------------------------------------------- #
# M1 mechanism gate (wraps the independent reference suite)
# --------------------------------------------------------------------------- #

def run_m1_gate(adapter) -> dict[str, Any]:
    rep = vfy.run_m1_mechanism_tests(adapter)
    ok = bool(rep["all_ok"])
    return {"schema": "nbldpc_v26_m1_v1", "ok": ok, "tests": rep["tests"]}


# --------------------------------------------------------------------------- #
# M2 screen / M3 confirmation runners
# --------------------------------------------------------------------------- #

def _run_call(adapter, plan_item: dict, n: int, max_iter: int) -> dict[str, Any]:
    arch, lid, f, src, seed, q = (plan_item["arch"], plan_item["layer"],
                                  plan_item["f"], plan_item["source"],
                                  plan_item["seed"], plan_item["q"])
    rate = plan_item["rate"]
    rho = {int(k): float(v) for k, v in plan_item["rho"].items()}
    sampler = adapter.make_channel_sampler(lid)
    res = de.run_mcde_posterior(q, LAMBDA, rho, channel_sampler=sampler,
                                n_samples=n, max_iter=max_iter, seed=seed,
                                entropy_tol_bits=ENTROPY_TOL_BITS, streak=STREAK)
    return {
        "arch": arch, "layer": lid, "f": float(f), "rate": float(rate),
        "rho": rho, "source": src, "seed": int(seed), "q": int(q),
        "converged": bool(res["converged"]), "iterations": int(res["iterations"]),
        "final_entropy_bits": res["final_entropy_bits"],
        "entropy_trace_bits": res["entropy_trace_bits"],
    }


def _run_gated_stage(adapters, plan: list[dict[str, Any]], *, out_dir: Path,
                       checkpoint_path: Path | None, n_samples: int,
                       max_iter: int, stage: str,
                       resource_limit_seconds: float) -> dict[str, Any]:
    """Shared runner for M2 screen / M3 confirmation.

    Resource discipline (design section 4): each completed DE call is timed and
    added to a running ``accumulated_seconds`` total; when that total reaches
    ``resource_limit_seconds`` *while calls still remain*, all finished calls
    are saved (checkpoint) and no new call is started (``resource_blocked``).
    Calls already present in ``checkpoint_path`` are treated as previously
    completed and are reused without being re-timed in this invocation.
    """
    done: dict[str, dict[str, Any]] = {}
    if checkpoint_path is not None and Path(checkpoint_path).exists():
        done = json.loads(Path(checkpoint_path).read_text(encoding="utf-8"))
    started = time.time()
    accumulated = 0.0
    total_plan = len(plan)
    processed = 0
    for item in plan:
        key = (f"{item['arch']}|{item['layer']}|{item['f']}|{item['source']}|{item['seed']}")
        if key in done:
            processed += 1
            continue
        adapter = adapters[item["arch"]][item["source"]]
        t0 = time.time()
        call = _run_call(adapter, item, n_samples, max_iter)
        elapsed_call = time.time() - t0
        done[key] = call
        accumulated += elapsed_call
        processed += 1
        if checkpoint_path is not None:
            Path(checkpoint_path).write_text(json.dumps(done, indent=2), encoding="utf-8")
        # stop once the ceiling is reached and required calls still remain
        remaining = total_plan - processed
        if remaining > 0 and accumulated >= resource_limit_seconds:
            return {
                "schema": f"nbldpc_v26_{stage}_v1", "n_calls": len(done), "calls": done,
                "elapsed_s": time.time() - started,
                "resource_blocked": True,
                "resource_limit_seconds": resource_limit_seconds,
                "accumulated_seconds": accumulated,
                "completed_calls": len(done),
            }
    return {
        "schema": f"nbldpc_v26_{stage}_v1", "n_calls": len(done), "calls": done,
        "elapsed_s": time.time() - started,
        "resource_blocked": False,
        "resource_limit_seconds": resource_limit_seconds,
        "accumulated_seconds": accumulated,
        "completed_calls": len(done),
    }


def run_screen(adapters: Mapping[str, Mapping[str, "chn.ChannelAdapter"]],
               plan: list[dict[str, Any]], *, out_dir: Path,
               checkpoint_path: Path | None = None,
               resource_limit_seconds: float = RESOURCE_LIMIT_SECONDS) -> dict[str, Any]:
    """Run all 72 screen calls, checkpointing after each.  Reuses any finished
    calls already recorded in ``checkpoint_path`` (dict of (key)->call)."""
    return _run_gated_stage(adapters, plan, out_dir=out_dir,
                            checkpoint_path=checkpoint_path,
                            n_samples=SCREEN_N, max_iter=SCREEN_MAX_ITER,
                            stage="screen",
                            resource_limit_seconds=resource_limit_seconds)


def run_confirmation(adapters, plan: list[dict[str, Any]], *, out_dir: Path,
                     checkpoint_path: Path | None = None,
                     resource_limit_seconds: float = RESOURCE_LIMIT_SECONDS) -> dict[str, Any]:
    """Run confirmation on the lowest passing ``f`` per architecture."""
    return _run_gated_stage(adapters, plan, out_dir=out_dir,
                            checkpoint_path=checkpoint_path,
                            n_samples=CONFIRM_N, max_iter=CONFIRM_MAX_ITER,
                            stage="confirmation",
                            resource_limit_seconds=resource_limit_seconds)


def _arch_passes_at(calls: Mapping[str, dict[str, Any]], arch: str, f: float,
                    seeds: list[int]) -> bool:
    """All layers x all sources x the given seeds converged at this f."""
    for lid in ARCH_LAYERS[arch]:
        for src in SOURCES:
            for seed in seeds:
                key = f"{arch}|{lid}|{f}|{src}|{seed}"
                if key not in calls or not calls[key]["converged"]:
                    return False
    return True


# --------------------------------------------------------------------------- #
# M4 terminal state
# --------------------------------------------------------------------------- #

def decide_terminal(screen: dict[str, Any], confirm: dict[str, Any] | None,
                    m0: dict[str, Any], m1: dict[str, Any]) -> dict[str, Any]:
    if not m0["ok"] or not m1["ok"]:
        return {"status": "implementation_blocked_layer_channel_semantics",
                "reason": "M0/M1 semantic gate failed"}
    if screen.get("resource_blocked") or (confirm or {}).get("resource_blocked"):
        return {"status": "resource_blocked",
                "reason": "24h completed-call resource ceiling reached before all "
                          "required calls completed"}
    s = screen.get("calls", {})
    c = (confirm or {}).get("calls", {})
    passed = {}
    for arch in ARCH_LAYERS:
        for f in SCREEN_F:
            full = _arch_passes_at(c, arch, f, CONFIRM_SEEDS) if confirm else _arch_passes_at(s, arch, f, SCREEN_SEEDS)
            if full:
                passed.setdefault(arch, []).append(f)
    best_f = {}
    for arch in ARCH_LAYERS:
        if arch in passed and passed[arch]:
            best_f[arch] = min(passed[arch])
    if any(best_f.get(a) == 1.3 for a in ARCH_LAYERS):
        status = "pass_target_f13"
    elif any(best_f.get(a) in (1.6, 2.0) for a in ARCH_LAYERS):
        status = "target_fail_slack_pass"
    else:
        status = "fixed_ensemble_no_convergence"
    return {"status": status, "best_passing_f": best_f, "passed": passed}


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def _write_json(path: Path, data: Any) -> None:
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_v26_gate(*, out_dir: str | Path, counts_path: str | Path | None = None) -> dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    counts = chn.load_channel_counts(counts_path)
    adapters = {}
    for arch, fact in {"A01": "F01", "A02": "F03"}.items():
        adapters[arch] = {src: chn.build_adapter(counts, fact_id=fact, source=src)
                          for src in SOURCES}

    # M0 adapter gate
    m0 = run_m0_gate(adapters, counts)
    _write_json(out / "m0_report.json", m0)
    # M1 mechanism gate (representative adapter; A01 L2 GF2)
    m1 = run_m1_gate(adapters["A01"][SOURCES[-1]])
    _write_json(out / "m1_report.json", m1)

    if not m0["ok"] or not m1["ok"]:
        gate = decide_terminal({}, None, m0, m1)
        _write_json(out / "gate.json", gate)
        write_run_manifest(out, run_id=out.name, role="unclassified",
                           screen=None, confirm=None, gate=gate)
        return {"status": gate["status"], "evidence_root": str(out)}

    # M2 screen
    plan = build_screen_plan()
    screen = run_screen(adapters, plan, out_dir=out, checkpoint_path=out / "screen_checkpoint.json")
    _write_json(out / "screen_results.json", screen)

    # M3 confirmation on lowest passing f per arch
    confirm_plan = []
    for arch in ARCH_LAYERS:
        lows = [f for f in SCREEN_F if _arch_passes_at(screen["calls"], arch, f, SCREEN_SEEDS)]
        if not lows:
            continue
        f = min(lows)
        for lid in ARCH_LAYERS[arch]:
            rate = target_rate_for(arch, lid, f)
            rho = de.make_rho(rate, LAMBDA)
            for src in SOURCES:
                for seed in CONFIRM_SEEDS:
                    confirm_plan.append({
                        "arch": arch, "layer": lid, "f": float(f), "rate": float(rate),
                        "rho": {int(k): float(v) for k, v in rho.items()},
                        "source": src, "seed": int(seed), "q": ARCH_Q[arch][lid]})
    confirm = None
    if confirm_plan:
        confirm = run_confirmation(adapters, confirm_plan, out_dir=out,
                                   checkpoint_path=out / "confirm_checkpoint.json")
        _write_json(out / "confirmation_results.json", confirm)

    gate = decide_terminal(screen, confirm, m0, m1)
    _write_json(out / "gate.json", gate)
    # persist a compact per-call summary table (entropy trace, rate, f, status)
    _write_summary(out, screen, confirm, gate)
    write_run_manifest(out, run_id=out.name, role="unclassified",
                       screen=screen, confirm=confirm, gate=gate)
    return {"status": gate["status"], "evidence_root": str(out),
            "best_passing_f": gate["best_passing_f"]}


def _write_summary(out: Path, screen: dict[str, Any], confirm: dict[str, Any] | None,
                   gate: dict[str, Any]) -> None:
    rows = []
    for kind, data in (("screen", screen), ("confirm", confirm)):
        if not data:
            continue
        for key, call in data["calls"].items():
            rows.append({
                "stage": kind, "arch": call["arch"], "layer": call["layer"],
                "f": call["f"], "rate": call["rate"], "source": call["source"],
                "seed": call["seed"], "converged": call["converged"],
                "final_entropy_bits": call["final_entropy_bits"],
                "iterations": call["iterations"],
            })
    _write_json(out / "calls_summary.json",
                {"schema": "nbldpc_v26_calls_summary_v1", "terminal_state": gate["status"],
                 "rows": rows})


def write_run_manifest(root: str | Path, *, run_id: str, role: str,
                         screen: dict[str, Any] | None,
                         confirm: dict[str, Any] | None,
                         gate: dict[str, Any],
                         counts_basename: str = "channel_counts.npz") -> None:
    """Persist a run manifest marking the run identity and role.

    ``role`` is one of the frozen V26 roles: ``canonical`` (authoritative
    evidence root), ``deterministic_repeat`` (independent re-run that must be
    byte-identical to canonical on every deterministic field), or
    ``unclassified``.  Also records the explicit source <-> delay mapping
    (``SOURCE_METADATA``) that otherwise only lives inside the source id string,
    plus the 24h resource-gate verdict for the completed runs.
    """
    root = Path(root)
    manifest = {
        "schema": "nbldpc_v26_run_manifest_v1",
        "run_id": run_id,
        "role": role,
        "terminal_state": gate.get("status"),
        "best_passing_f": gate.get("best_passing_f"),
        "source_metadata": {
            src: dict(meta) for src, meta in chn.SOURCE_METADATA.items()
        },
        "resource": {
            "limit_seconds": RESOURCE_LIMIT_SECONDS,
            "screen_resource_blocked": bool((screen or {}).get("resource_blocked")),
            "confirm_resource_blocked": bool((confirm or {}).get("resource_blocked")),
            "screen_accumulated_seconds": (screen or {}).get("accumulated_seconds"),
            "confirm_accumulated_seconds": (confirm or {}).get("accumulated_seconds"),
            "screen_completed_calls": (screen or {}).get("completed_calls"),
            "confirm_completed_calls": (confirm or {}).get("completed_calls"),
        },
        "counts_basename": counts_basename,
        "design_constants": {
            "screen_n_samples": SCREEN_N, "screen_max_iter": SCREEN_MAX_ITER,
            "screen_seeds": list(SCREEN_SEEDS),
            "confirm_n_samples": CONFIRM_N, "confirm_max_iter": CONFIRM_MAX_ITER,
            "confirm_seeds": list(CONFIRM_SEEDS),
            "entropy_tol_bits": ENTROPY_TOL_BITS, "streak": STREAK,
            "lambda": {int(k): float(v) for k, v in LAMBDA.items()},
        },
    }
    _write_json(root / "RUN_MANIFEST.json", manifest)


def verify_run(root: str | Path) -> dict[str, Any]:
    """Independent read-only verification of a V26 gate run.

    Recomputes from channel_counts.npz: builds adapters, re-runs M0/M1 semantic
    gates, rebuilds screen plan (72 calls), recomputes all screen calls, builds
    confirmation plan from screen, recomputes all 60 confirmation calls, and
    checks that all results match the persisted artifacts bit-for-bit (within
    float determinism).  Also verifies A02@f=1.3 30/30 convergence.
    """
    import numpy as np
    root = Path(root)
    problems: list[str] = []
    details: dict[str, Any] = {}

    # 1) Load channel counts (must exist at run_04 or fallback)
    try:
        counts = chn.load_channel_counts(None)
    except Exception as exc:
        return {"schema": "nbldpc_v26_readonly_verify_v1", "ok": False,
                "problems": [f"cannot load channel_counts: {exc}"],
                "checked_root": str(root)}

    # 2) Build adapters
    adapters = {}
    for arch, fact in {"A01": "F01", "A02": "F03"}.items():
        adapters[arch] = {src: chn.build_adapter(counts, fact_id=fact, source=src)
                          for src in SOURCES}

    # 3) Re-run M0 gate
    m0 = run_m0_gate(adapters, counts)
    details["m0_ok"] = bool(m0["ok"])
    if not m0["ok"]:
        problems.append(f"M0 gate FAILED: {m0.get('problems', [])}")

    # 4) Re-run M1 gate (using A01 L2 GF2 representative adapter)
    m1 = run_m1_gate(adapters["A01"][SOURCES[-1]])
    details["m1_ok"] = bool(m1["ok"])
    if not m1["ok"]:
        problems.append(f"M1 gate FAILED: {[k for k,v in m1['tests'].items() if not v['ok']]}")

    # 5) Rebuild screen plan and recompute all 72 calls
    plan = build_screen_plan()
    if len(plan) != 72:
        problems.append(f"screen plan has {len(plan)} calls, expected 72")
    screen_recomp = run_screen(adapters, plan, out_dir=root, checkpoint_path=None)
    details["screen_n_calls"] = screen_recomp["n_calls"]

    # Load persisted screen results for comparison
    try:
        screen_persisted = json.loads((root / "screen_results.json").read_text(encoding="utf-8"))
    except Exception as exc:
        problems.append(f"cannot read screen_results.json: {exc}")
        screen_persisted = {"calls": {}}

    # Compare screen calls
    screen_mismatch = 0
    for key, call in screen_recomp["calls"].items():
        if key not in screen_persisted.get("calls", {}):
            problems.append(f"screen call {key} missing in persisted results")
            screen_mismatch += 1
            continue
        p = screen_persisted["calls"][key]
        # Check key deterministic fields
        for field in ("converged", "iterations", "final_entropy_bits"):
            if call[field] != p[field]:
                problems.append(f"screen {key} {field} mismatch: got {call[field]} persisted {p[field]}")
                screen_mismatch += 1
                break
        # Check rate/rho/seed/f/q match plan
        for field in ("arch", "layer", "f", "rate", "source", "seed", "q"):
            if call[field] != p[field]:
                problems.append(f"screen {key} {field} mismatch: got {call[field]} persisted {p[field]}")
                screen_mismatch += 1
                break
    details["screen_mismatches"] = screen_mismatch

    # 6) Build confirmation plan from recomputed screen results
    confirm_plan = []
    for arch in ARCH_LAYERS:
        lows = [f for f in SCREEN_F if _arch_passes_at(screen_recomp["calls"], arch, f, SCREEN_SEEDS)]
        if not lows:
            continue
        f = min(lows)
        for lid in ARCH_LAYERS[arch]:
            rate = target_rate_for(arch, lid, f)
            rho = de.make_rho(rate, LAMBDA)
            for src in SOURCES:
                for seed in CONFIRM_SEEDS:
                    confirm_plan.append({
                        "arch": arch, "layer": lid, "f": float(f), "rate": float(rate),
                        "rho": {int(k): float(v) for k, v in rho.items()},
                        "source": src, "seed": int(seed), "q": ARCH_Q[arch][lid]})

    # 7) Recompute confirmation calls
    confirm_recomp = None
    if confirm_plan:
        confirm_recomp = run_confirmation(adapters, confirm_plan, out_dir=root, checkpoint_path=None)
        details["confirm_n_calls"] = confirm_recomp["n_calls"]
        # Load persisted confirmation
        try:
            confirm_persisted = json.loads((root / "confirmation_results.json").read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"cannot read confirmation_results.json: {exc}")
            confirm_persisted = {"calls": {}}
        # Compare confirmation calls
        confirm_mismatch = 0
        for key, call in confirm_recomp["calls"].items():
            if key not in confirm_persisted.get("calls", {}):
                problems.append(f"confirm call {key} missing in persisted results")
                confirm_mismatch += 1
                continue
            p = confirm_persisted["calls"][key]
            for field in ("converged", "iterations", "final_entropy_bits"):
                if call[field] != p[field]:
                    problems.append(f"confirm {key} {field} mismatch: got {call[field]} persisted {p[field]}")
                    confirm_mismatch += 1
                    break
            for field in ("arch", "layer", "f", "rate", "source", "seed", "q"):
                if call[field] != p[field]:
                    problems.append(f"confirm {key} {field} mismatch: got {call[field]} persisted {p[field]}")
                    confirm_mismatch += 1
                    break
        details["confirm_mismatches"] = confirm_mismatch

        # 8) Verify A02@f=1.3 30/30 convergence
        a02_f13_confirmed = 0
        a02_f13_total = 0
        for key, call in confirm_recomp["calls"].items():
            if call["arch"] == "A02" and abs(call["f"] - 1.3) < 1e-9:
                a02_f13_total += 1
                if call["converged"]:
                    a02_f13_confirmed += 1
        details["a02_f13_confirmed"] = a02_f13_confirmed
        details["a02_f13_total"] = a02_f13_total
        if a02_f13_total != 30:
            problems.append(f"A02@f=1.3 confirmation has {a02_f13_total} calls, expected 30")
        if a02_f13_confirmed != 30:
            problems.append(f"A02@f=1.3 confirmed {a02_f13_confirmed}/30, expected 30/30")

    # 9) Recompute terminal state and verify gate.json
    gate_recomp = decide_terminal(screen_recomp, confirm_recomp, m0, m1)
    try:
        gate_persisted = json.loads((root / "gate.json").read_text(encoding="utf-8"))
    except Exception as exc:
        problems.append(f"cannot read gate.json: {exc}")
        gate_persisted = {}
    if gate_recomp != gate_persisted:
        problems.append(f"gate.json mismatch: recomputed {gate_recomp} persisted {gate_persisted}")
    details["gate_recomputed"] = gate_recomp
    details["gate_persisted"] = gate_persisted

    # 10) Verify calls_summary.json
    try:
        summary_persisted = json.loads((root / "calls_summary.json").read_text(encoding="utf-8"))
        # Recompute summary from recomputed calls
        rows = []
        for kind, data in (("screen", screen_recomp), ("confirm", confirm_recomp)):
            if not data:
                continue
            for key, call in data["calls"].items():
                rows.append({
                    "stage": kind, "arch": call["arch"], "layer": call["layer"],
                    "f": call["f"], "rate": call["rate"], "source": call["source"],
                    "seed": call["seed"], "converged": call["converged"],
                    "final_entropy_bits": call["final_entropy_bits"],
                    "iterations": call["iterations"],
                })
        summary_recomp = {"schema": "nbldpc_v26_calls_summary_v1",
                          "terminal_state": gate_recomp["status"], "rows": rows}
        # Compare row-by-row (order-independent) to give better diagnostics
        rp = { (r["stage"], r["arch"], r["layer"], r["f"], r["source"], r["seed"]): r for r in summary_recomp["rows"] }
        rs = { (r["stage"], r["arch"], r["layer"], r["f"], r["source"], r["seed"]): r for r in summary_persisted["rows"] }
        summary_ok = (rp == rs)
        if not summary_ok:
            problems.append("calls_summary.json mismatch vs recomputed")
        details["calls_summary_ok"] = summary_ok
    except Exception as exc:
        problems.append(f"cannot read/verify calls_summary.json: {exc}")

    # 11) Check all required artifact files exist
    for rel in ["m0_report.json", "m1_report.json", "screen_results.json",
                "gate.json", "calls_summary.json", "confirmation_results.json"]:
        if not (root / rel).exists():
            problems.append(f"missing artifact {rel}")

    ok = not problems
    return {"schema": "nbldpc_v26_readonly_verify_v1", "ok": ok,
            "problems": problems, "details": details, "checked_root": str(root)}


def _write_readonly_verify(root: str | Path, verify_result: dict[str, Any]) -> None:
    """Persist the read-only verification result to readonly_verify.json."""
    _write_json(Path(root) / "readonly_verify.json", verify_result)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--counts", default=None)
    a = ap.parse_args()
    res = run_v26_gate(out_dir=a.out, counts_path=a.counts)
    print(json.dumps(res, indent=2))
