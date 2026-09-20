"""V80 S2 FER campaign executor (EXPLORE campaign code — NOT execution).

Frozen contract: ``docs/research_cycles/V80-NBLDPC-JAN21/
S2_FER_CAMPAIGN_PACKET_20260920.md`` (G-S2FER, frozen, NOT granted).
Execution needs a fresh explicit grant + Pre-EXECUTE; this module only
provides the executor + fake-testable mechanics. No real/Jan-21 frames;
synthetic QSC hook only; no writes outside the run root; never writes
``results/`` or ``outputs_comparison/``.

Seed policy (LITERAL, packet §2 — no derivation): V1 frames
``2026096001+idx`` (idx=0..239, group g frame f → idx=4g+f); V2 frames
``2026096301+idx``. rg check 2026-09-20: ``2026096[01]`` absent from
src/tests (only the two frozen packet docs carry these seeds), so the
hundred-block is fresh. Recorded here + in the manifest.

Resume-policy deviation (flagged for Pre-EXECUTE adjudication): packet §4
says "one shot per arm ... never resumed" and §3 says budget halt →
FAIL(budget) with no resume. This executor implements the delegated task
spec instead: exactly ONE explicit wall-continuation via ``--resume-from``
(fresh 3600 s window appended to ``wall_windows``; scientific ledger
continues verbatim, completed groups never recomputed). A second resume
refuses rc=2. Per-decode-overrun / RSS halts stay terminal FAIL(budget)
(no resume). Pre-EXECUTE adjudicates which rule governs the real run.

Reuse from ``v80_s1_mcde_runner`` (patterns only, never its science):
dual-flag gate, checkpoint manifest+rows overwrite-in-place single writer,
append-only ``wall_windows``, explicit ``--resume-from`` with strict
pre-decode validation. No import of the S1 module.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

from . import v80_s2_peg as s2

__all__ = [
    "V1_CONSTRUCT_SEED", "V1_MAX_TRIALS", "V1_FOUR_CYCLES",
    "V2_CONSTRUCT_SEED", "V2_MAX_TRIALS",
    "V1_FRAME_BASE", "V2_FRAME_BASE",
    "N_GROUPS", "GROUP_FRAMES", "N_DECODERS",
    "MAX_ITER", "QBER_SYNTH", "D_BLIND",
    "PASS_MAX_FAILS", "F_SUPER_MAX",
    "WALL_CAP_S", "PER_DECODE_CAP_S", "RSS_CAP_GIB",
    "ROOT_PREFIX", "FORBIDDEN_ROOT_PARTS",
    "Refusal", "refuse", "frame_seed", "leak_basis",
    "execute", "main",
]

#: Frozen V1 construction (packet §1).
V1_CONSTRUCT_SEED = 2026092001
V1_MAX_TRIALS = 20
#: V1 4-cycle count REPORT-ONLY anchor (sponsor-reported; Pre-run assert).
V1_FOUR_CYCLES = 1158
#: Frozen V2 construction (packet §1; runs IFF V1 verdict=FAIL).
V2_CONSTRUCT_SEED = 2026096101
V2_MAX_TRIALS = 100
#: Frozen literal frame-seed bases (packet §2; LITERAL, not derived).
V1_FRAME_BASE = 2026096001
V2_FRAME_BASE = 2026096301
#: Frozen campaign shape (packet §2): 60 groups x 4 frames = 240 decodes.
N_GROUPS = 60
GROUP_FRAMES = s2.GROUP_FRAMES
N_DECODERS = N_GROUPS * GROUP_FRAMES
#: Frozen decoder/channel point (packet §2).
MAX_ITER = s2.MAX_ITER
QBER_SYNTH = s2.QBER_SYNTH
#: D_blind = 0 MEASURED (no blind/puncturing rounds in campaign path;
#: NEVER-ASSUME-ZERO label carried on every group record).
D_BLIND = 0.0
#: Frozen pass bars (packet §3): <=3 fails/60 AND f_super <= 1.3.
PASS_MAX_FAILS = 3
F_SUPER_MAX = 1.3
#: Frozen caps (packet §4 + task wall spec): single window 3600 s.
WALL_CAP_S = 3600
PER_DECODE_CAP_S = 300
RSS_CAP_GIB = 4
#: Fresh additive run-root prefix (packet §4).
ROOT_PREFIX = "workspace/s2_fer_"
#: Roots the executor never writes under (task D1).
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")

#: Group rule (a) arithmetic pin (packet §2): superframe FER<=5% needs
#: per-frame FER <= 1-(1-0.05)^(1/4) = 1.274%.
PER_FRAME_FER_FOR_SUPERFRAME_5PCT = s2.PER_FRAME_FER_FOR_SUPERFRAME_5PCT


class Refusal(SystemExit):
    """rc=2 pre-write refusal (unauthorized / invalid / gate-blocked)."""


def refuse(reason: str) -> "Any":
    print(f"S2FER-REFUSAL rc=2: {reason}", file=sys.stderr)
    raise Refusal(2)


def frame_seed(variant: str, group: int, frame: int) -> int:
    """Frozen literal frame seed: base + 4g+f (packet §2)."""
    base = V1_FRAME_BASE if variant == "V1" else V2_FRAME_BASE
    return base + 4 * int(group) + int(frame)


def leak_basis() -> dict[str, Any]:
    """Frozen f accounting (packet §2/§3): 1044 bits over 852.544 content."""
    leak = s2.superframe_leakage(D_BLIND)
    content = GROUP_FRAMES * s2.N_FRAME * s2.H_FULL_ANCHOR
    return {
        "leak_bits": leak,
        "content_bits": content,
        "f_super_basis": leak / content,  # 1.2246 at D_blind=0
        "d_blind": D_BLIND,
        "d_blind_label": ("MEASURED zero: no blind/puncturing rounds exist "
                          "in the campaign path — NEVER assume zero "
                          "in a claim (packet §2)"),
        "sensitivity": ("Δf_super = D_blind/852.544, i.e. each 16 bits "
                        "≈ +0.019; headroom to 1.3 is 64.31 bits"),
    }


def _default_decode(construction: dict, seed: int) -> dict:
    return s2.smoke_decode_frame(construction, seed,
                                 max_iter=MAX_ITER, qber=QBER_SYNTH)


def default_writer(root: str, files: dict[str, str]) -> None:
    """Single-writer overwrite-in-place (research code; root policy is
    enforced in ``execute`` — fail closed before the first write)."""
    os.makedirs(root, exist_ok=True)
    for name, blob in files.items():
        with open(os.path.join(root, name), "w") as fh:
            fh.write(blob)


def _default_rss() -> int:
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except Exception:  # noqa: BLE001 — RSS probe is best-effort only
        return 0


def _check_root(root: str) -> None:
    if not root:
        refuse("root required (fresh additive workspace/s2_fer_<uuid>)")
    parts = Path(root).parts
    if any(p in FORBIDDEN_ROOT_PARTS for p in parts):
        refuse(f"root under forbidden tree (results/outputs_comparison): {root}")


def _build_manifest(*, variant: str, construction: dict, rows: list[dict],
                    failures: int, groups_completed: int, verdict: str,
                    partial: bool, next_group: int,
                    wall_windows: list[dict], ledger_decodes: int,
                    elapsed_s: float) -> dict:
    basis = leak_basis()
    n = len(rows)
    fer = (failures / n) if n else None
    return {
        "variant": variant,
        "construct": {
            "seed": construction.get("construct_seed"),
            "max_trials": construction.get("construct_trials"),
            "four_cycles": construction.get("four_cycles"),
            "min_girth": construction.get("min_girth"),
            "family": construction.get("family"),
            "four_cycle_gate": ("==1158 asserted pre-run (V1)"
                                if variant == "V1"
                                else "<1158 asserted pre-run (V2)"),
        },
        "seeds": {
            "policy": "literal-frozen (packet §2; NOT derived)",
            "frame_base": V1_FRAME_BASE if variant == "V1" else V2_FRAME_BASE,
            "frame_rule": "base+idx, idx=0..239 (group g frame f → idx=4g+f)",
            "absence": ("rg 2026-09-20: 2026096[01] absent from src/tests; "
                        "only the frozen packet docs carry these seeds"),
        },
        "budgets": {"wall_cap_s": WALL_CAP_S,
                    "per_decode_cap_s": PER_DECODE_CAP_S,
                    "rss_gib": RSS_CAP_GIB,
                    "max_groups": N_GROUPS, "max_decodes": N_DECODERS},
        "decoder": {"kernel": "log-FFT-SPA via smoke_decode_frame",
                    "max_iter": MAX_ITER, "qber": QBER_SYNTH,
                    "channel": ("qsc_pair_sampler QSC p=0.05 — V17/V25-class "
                                "QBER≈5% PROXY, not the V17/V25 kernel")},
        "ledger": {"decodes": ledger_decodes,
                   "groups_completed": groups_completed},
        "groups_completed": groups_completed,
        "failures": failures,
        "fer_groups": fer,
        "pass_bar": f"superframe FER<=5% (fails/60<={PASS_MAX_FAILS})",
        "d_blind": basis["d_blind"],
        "d_blind_label": basis["d_blind_label"],
        "sensitivity": basis["sensitivity"],
        "leak_bits": basis["leak_bits"],
        "f_super": basis["f_super_basis"],
        "f_bar": f"f_super<={F_SUPER_MAX}",
        "verdict": verdict,
        "partial": bool(partial),
        "next_group": int(next_group),
        "resume": {"continuations_used": len(wall_windows) - 1,
                   "max_continuations": 1},
        "wall_windows": list(wall_windows),
        "elapsed_s": float(elapsed_s),
        "n_rows": n,
        "per_frame_target": PER_FRAME_FER_FOR_SUPERFRAME_5PCT,
        "resume_policy_note": ("packet §4/§3: one shot per arm, never "
                               "resumed; budget halt → FAIL(budget). "
                               "Executor (task spec) permits exactly ONE "
                               "explicit wall-continuation; second resume "
                               "refuses. Pre-EXECUTE adjudicates."),
        "verify": {
            "four_cycles_ok": True,  # construct gate passed pre-run
            "ledger_ok": ledger_decodes == 4 * groups_completed,
            "rows_ok": n == groups_completed,
        },
    }


def _validate_partial(manifest: dict, rows: list, variant: str) -> dict:
    """Fail-closed partial validation BEFORE any decode (zero decodes on
    refuse). Checks: variant match, frozen seeds/budgets, ledger internal
    consistency (decodes == 4*groups, rows contiguous 0..k-1), no final
    verdict (completion is not resumable), at most-one continuation unused
    (exactly one wall window so far)."""
    if not isinstance(manifest, dict):
        refuse("partial manifest not a dict")
    if not isinstance(rows, list):
        refuse("partial rows not a list")
    if manifest.get("variant") != variant:
        refuse("partial variant mismatch (fail closed)")
    seeds = manifest.get("seeds", {})
    want_base = V1_FRAME_BASE if variant == "V1" else V2_FRAME_BASE
    if (not isinstance(seeds, dict)
            or seeds.get("policy") != "literal-frozen (packet §2; NOT derived)"
            or seeds.get("frame_base") != want_base):
        refuse("partial seeds mismatch frozen literal")
    if manifest.get("budgets", None) != {"wall_cap_s": WALL_CAP_S,
                                         "per_decode_cap_s": PER_DECODE_CAP_S,
                                         "rss_gib": RSS_CAP_GIB,
                                         "max_groups": N_GROUPS,
                                         "max_decodes": N_DECODERS}:
        refuse("partial budgets mismatch frozen")
    if manifest.get("verdict") not in ("INCOMPLETE-wall",):
        refuse("partial carries a final/verdict state (nothing resumable; "
               "completion and FAIL states never resume)")
    groups_completed = manifest.get("groups_completed")
    failures = manifest.get("failures")
    ledger = manifest.get("ledger", {})
    try:
        k, f = int(groups_completed), int(failures)
        ld = int(ledger.get("decodes"))
    except Exception:  # noqa: BLE001
        refuse("partial counts corrupt")
    if not 0 <= k < N_GROUPS or not 0 <= f <= k or ld != 4 * k:
        refuse("partial ledger/groups counts corrupt")
    if len(rows) != k:
        refuse(f"partial rows {len(rows)} != groups_completed {k}")
    for i, r in enumerate(rows):
        if not isinstance(r, dict) or r.get("group") != i:
            refuse("partial groups not contiguous 0..k-1")
    windows = manifest.get("wall_windows", None)
    if not isinstance(windows, list) or len(windows) != 1:
        refuse("partial wall_windows != exactly one window "
               "(continuation already used or corrupt)")
    try:
        float(windows[0].get("turn_start"))
        assert windows[0].get("cap") == WALL_CAP_S
    except Exception:  # noqa: BLE001
        refuse("partial wall window corrupt")
    return {"groups_completed": k, "failures": f, "decodes": ld,
            "windows": windows}


def _load_partial_fs(partial_root: str):
    try:
        with open(os.path.join(partial_root, "manifest.json")) as fh:
            manifest = json.load(fh)
        with open(os.path.join(partial_root, "rows.json")) as fh:
            rows = json.load(fh)
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed, zero decodes
        refuse(f"partial load failed ({partial_root}): "
               f"{type(exc).__name__}: {exc}")
    return manifest, rows


def execute(*, root: str,
            variant: str = "V1",
            construct_fn: Callable | None = None,
            decode_fn: Callable | None = None,
            clock: Callable | None = None,
            rss_fn: Callable | None = None,
            writer: Callable | None = None,
            resume_from: str | None = None,
            max_groups: int | None = None) -> dict:
    """Run (or once-continue) the frozen 60x4 campaign under ``root``.

    ``max_groups`` is a PROBE-ONLY cap (D3 timing integration; never a CLI
    flag, never part of any verdict). All writes stay under ``root``.
    """
    if variant not in ("V1", "V2"):
        refuse(f"unknown variant {variant} (frozen: V1/V2 only)")
    _check_root(root)
    construct_fn = construct_fn or (lambda seed, trials: s2.construct_l2(
        seed, max_trials=trials))
    decode_fn = decode_fn or _default_decode
    clock = clock or time.monotonic
    rss_fn = rss_fn or _default_rss
    writer = writer or default_writer
    if max_groups is not None and (
            not isinstance(max_groups, int) or max_groups < 1):
        refuse("max_groups (probe-only) must be a positive int")

    if resume_from is not None:
        # Explicit continuation: root must equal the partial root.
        if root != resume_from:
            refuse("root/resume-from mismatch (fail closed: pass same path)")
        if not os.path.exists(resume_from):
            refuse(f"nothing to resume (absent): {resume_from}")
        manifest_p, rows_p = _load_partial_fs(resume_from)
        st = _validate_partial(manifest_p, rows_p, variant)
        construction = _construct_gate(variant, construct_fn)
        rows = list(rows_p)
        failures = int(st["failures"])
        ledger_decodes = int(st["decodes"])
        t_start = clock()
        wall_windows = list(st["windows"]) + [
            {"turn_start": float(t_start), "cap": WALL_CAP_S}]
        start_group = int(st["groups_completed"])
    else:
        if os.path.exists(root):
            refuse(f"root not fresh: {root}")
        construction = _construct_gate(variant, construct_fn)
        rows = []
        failures = 0
        ledger_decodes = 0
        t_start = clock()
        wall_windows = [{"turn_start": float(t_start), "cap": WALL_CAP_S}]
        start_group = 0

    target = N_GROUPS if max_groups is None else min(max_groups, N_GROUPS)

    def _flush(verdict: str, partial: bool, next_group: int):
        mf = _build_manifest(
            variant=variant, construction=construction, rows=rows,
            failures=failures, groups_completed=len(rows), verdict=verdict,
            partial=partial, next_group=next_group,
            wall_windows=wall_windows, ledger_decodes=ledger_decodes,
            elapsed_s=clock() - t_start)
        writer(root, {"manifest.json": json.dumps(mf, indent=1,
                                                  sort_keys=True, default=str),
                      "rows.json": json.dumps(rows, indent=1,
                                              sort_keys=True, default=str)})
        return mf

    for g in range(start_group, target):
        # Wall check per group (fresh window per invocation).
        if clock() - t_start > WALL_CAP_S:
            return _flush("INCOMPLETE-wall", True, g)
        try:
            rss_gib = float(rss_fn()) / (1024 ** 3)
        except Exception:  # noqa: BLE001 — probe failure never halts
            rss_gib = 0.0
        if rss_gib >= RSS_CAP_GIB:
            return _flush("FAIL(budget)", True, g)
        frame_recs: list[dict] = []
        frame_ok: list[bool] = []
        for f in range(GROUP_FRAMES):
            seed = frame_seed(variant, g, f)
            t0 = clock()
            try:
                out = decode_fn(construction, seed)
            except Exception as exc:  # noqa: BLE001 — no-retry: retain + halt
                rows.append({"group": g, "status": "error",
                             "error": f"{type(exc).__name__}: {exc}"})
                return _flush("FAIL(budget)", True, g)
            dt = clock() - t0
            if dt > PER_DECODE_CAP_S:
                rows.append({"group": g, "status": "overrun",
                             "decode_s": dt})
                return _flush("FAIL(budget)", True, g)
            ok = bool(out.get("exact_match") is True)
            frame_ok.append(ok)
            ledger_decodes += 1
            frame_recs.append({
                "seed": seed,
                "status": out.get("status"),
                "converged": bool(out.get("reconstruction_ok", False)),
                "iterations": out.get("iterations"),
                "wall_s": dt,
                "exact_match": bool(out.get("exact_match", False)),
                "frame_ok": ok,
            })
        grp = s2.evaluate_superframe(frame_ok, d_blind=D_BLIND)
        if not grp["group_accept"]:
            failures += 1
        rows.append({
            "group": g,
            "frames": frame_recs,
            "group_accept": grp["group_accept"],
            "superframe_fail": grp["superframe_fail"],
            "per_frame_fer": grp["per_frame_fer"],
            "d_blind": grp["d_blind"],
            "d_blind_label": grp["d_blind_label"],
            "leak_bits": grp["leak_bits"],
            "f_super": grp["f_super"],
        })
        # Checkpoint per COMPLETED group (overwrite-in-place, single writer).
        _flush("INCOMPLETE-wall", True, g + 1)
        if failures > PASS_MAX_FAILS:
            # Early-stop: 4th group failure makes the bar unpassable.
            return _flush("FAIL-early-stop", True, g + 1)

    if max_groups is not None:
        # Probe-only truncation: no verdict, no claim.
        return _flush("PROBE-truncated", True, target)
    basis = leak_basis()
    passed = failures <= PASS_MAX_FAILS and basis["f_super_basis"] <= F_SUPER_MAX
    return _flush("PASS" if passed else "FAIL", False, N_GROUPS)


def _construct_gate(variant: str, construct_fn: Callable) -> dict:
    """Pre-run construction gate (packet §1): V1 asserts four_cycles==1158
    else STOP-BLOCKED; V2 asserts four_cycles<1158 else FAILs closed."""
    seed = V1_CONSTRUCT_SEED if variant == "V1" else V2_CONSTRUCT_SEED
    trials = V1_MAX_TRIALS if variant == "V1" else V2_MAX_TRIALS
    try:
        code = construct_fn(seed, trials)
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed pre-decode
        refuse(f"construction failed ({variant}): "
               f"{type(exc).__name__}: {exc}")
    try:
        fc = int(code.get("four_cycles"))
    except Exception:  # noqa: BLE001
        refuse(f"construction missing four_cycles ({variant}; STOP-BLOCKED)")
    if variant == "V1":
        if fc != V1_FOUR_CYCLES:
            refuse(f"V1 four_cycles {fc} != {V1_FOUR_CYCLES} (STOP-BLOCKED; "
                   f"packet §1)")
    elif fc >= V1_FOUR_CYCLES:
        refuse(f"V2 four_cycles {fc} not < {V1_FOUR_CYCLES} "
               f"(V2 arm FAILs closed; packet §1)")
    code["construct_seed"] = seed
    code["construct_trials"] = trials
    return code


def run_execution(root: str, variant: str = "V1",
                  resume_from: str | None = None) -> int:
    manifest = execute(root=root, variant=variant, resume_from=resume_from)
    print(json.dumps({"variant": manifest["variant"],
                      "verdict": manifest["verdict"],
                      "failures": manifest["failures"],
                      "fer_groups": manifest["fer_groups"],
                      "f_super": manifest["f_super"],
                      "ledger": manifest["ledger"],
                      "wall_windows": manifest["wall_windows"],
                      "root": root}, indent=1, sort_keys=True, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute-real", action="store_true", default=False)
    ap.add_argument("--execution-authorized", action="store_true",
                    default=False)
    ap.add_argument("--root", default="")
    ap.add_argument("--resume-from", default="")
    ap.add_argument("--variant", default="V1")
    args = ap.parse_args(argv)
    # Dual-flag gate: refuse EVERYTHING else rc=2 BEFORE any root/contact.
    # There is no profile-only mode and no silent path.
    if not args.execute_real:
        refuse("refusing: --execute-real missing (rc2 pre-anything)")
    if not args.execution_authorized:
        refuse("refusing: --execution-authorized missing (rc2 pre-anything)")
    if args.variant not in ("V1", "V2"):
        refuse(f"unknown variant {args.variant} (frozen: V1/V2 only)")
    if args.resume_from and args.root and args.root != args.resume_from:
        refuse("root/resume-from mismatch (fail closed)")
    root = args.resume_from or args.root
    if not root:
        refuse("root required (fresh additive workspace/s2_fer_<uuid>)")
    if not root.startswith(ROOT_PREFIX):
        refuse(f"root must be fresh additive {ROOT_PREFIX}<uuid> "
               f"(got {root})")
    return run_execution(root=root, variant=args.variant,
                         resume_from=args.resume_from or None)
