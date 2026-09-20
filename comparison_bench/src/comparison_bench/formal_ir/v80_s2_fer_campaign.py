"""V80 S2b FER campaign executor (EXPLORE campaign code — NOT execution).

Frozen contract: ``docs/research_cycles/V80-NBLDPC-JAN21/
S2B_EXPERIMENT_PACKET_20260920.md`` (G-S2B, frozen, NOT granted).
Execution needs a fresh explicit grant + Pre-EXECUTE; this module only
provides the executor + fake-testable mechanics. No real/Jan-21 frames;
synthetic QSC hook only; no writes outside the run root; never writes
``results/`` or ``outputs_comparison/``.

Single arm S2b (packet §1): ``construct_l2(seed=2026092001)`` on FIXED
v10_peg (unreachable-first + correct girth + trials semantics);
λ={2:1} UNCHANGED. Pre-run assert ``four_cycles==0`` else STOP-BLOCKED.
No V2/fallback arm; any other variant refuses rc=2 (fail closed).

Seed policy (LITERAL, S2b packet §4 — no derivation): S2b frames
``2026097001+idx`` (idx=0..239, group g frame f → idx=4g+f).
rg check 2026-09-20: ``20260970xx`` absent from src/tests/configs/
docs-rest/openspec/tools/.codebuddy (only the frozen S2b packet+prompt
docs carry these seeds; no .workbuddy dir exists), so the
hundred-block is fresh. Recorded here + in the manifest.

Channel/prior (S2b packet §2, Option B ONLY): entropy-matched QSC
p*=0.081 BOTH in the sampler hook AND the decode prior
(``decode_error_domain`` qber=0.081); max_iter=300 unchanged.
H_qsc(p)=h2(p)+p·log2(31): p=0.081 → 0.40569+0.081×4.954196=0.80698
(Δ+7.5e-5 vs H_L2 anchor 0.80690067). The shared ``v80_s2_peg``
QBER_SYNTH default (0.05 proxy) is intentionally NOT changed here —
S2b pins p* at the campaign level (sampler + prior together).

Continuation (S2b packet §5): checkpoint-per-group + at most ONE
explicit wall-partial ``--resume-from`` in a fresh window (WALL-PARTIAL
only; terminal FAIL/early-stop states never resume); no auto-relaunch;
per-decode cap 300 s; wall cap 3600 s/window; RSS < 4 GiB.

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
    "S2B_CONSTRUCT_SEED", "S2B_MAX_TRIALS", "S2B_FOUR_CYCLES",
    "S2B_FRAME_BASE",
    "N_GROUPS", "GROUP_FRAMES", "N_DECODERS",
    "MAX_ITER", "QSTAR", "H_CHANNEL_S2B", "D_BLIND",
    "PASS_MAX_FAILS", "F_SUPER_MAX",
    "WALL_CAP_S", "PER_DECODE_CAP_S", "RSS_CAP_GIB",
    "ROOT_PREFIX", "FORBIDDEN_ROOT_PARTS",
    "Refusal", "refuse", "frame_seed", "leak_basis",
    "execute", "main",
]

#: Frozen S2b construction (S2b packet §1): fixed v10_peg,
#: construct_l2(seed=2026092001), λ={2:1} unchanged.
S2B_CONSTRUCT_SEED = 2026092001
S2B_MAX_TRIALS = 20
#: S2b 4-cycle gate: four_cycles==0 asserted pre-run (fixed PEG yields 0
#: for construct_l2(2026092001)); any mismatch halts STOP-BLOCKED.
S2B_FOUR_CYCLES = 0
#: Frozen literal frame-seed base (S2b packet §4; LITERAL, not derived).
S2B_FRAME_BASE = 2026097001
#: Frozen campaign shape (S2b packet §4): 60 groups x 4 frames = 240 decodes.
N_GROUPS = 60
GROUP_FRAMES = s2.GROUP_FRAMES
N_DECODERS = N_GROUPS * GROUP_FRAMES
#: Frozen decoder/channel point (S2b packet §2, Option B): entropy-matched
#: QSC p*=0.081 BOTH as sampler hook AND decode prior; max_iter=300.
MAX_ITER = s2.MAX_ITER
QSTAR = 0.081
#: Frozen S2b channel entropy: H=0.40569+0.081×4.954196=0.80698
#: (Δ+7.5e-5 vs H_L2 anchor 0.80690067).
H_CHANNEL_S2B = 0.80698
#: D_blind = 0 MEASURED (no blind/puncturing rounds in campaign path;
#: NEVER-ASSUME-ZERO label carried on every group record).
D_BLIND = 0.0
#: Frozen pass bars (S2b packet §3): <=3 fails/60 AND f_super <= 1.3.
PASS_MAX_FAILS = 3
F_SUPER_MAX = 1.3
#: Frozen caps (S2b packet §5): single window 3600 s.
WALL_CAP_S = 3600
PER_DECODE_CAP_S = 300
RSS_CAP_GIB = 4
#: Fresh additive run-root prefix (S2b packet §5).
ROOT_PREFIX = "workspace/s2b_"
#: Roots the executor never writes under (task D1).
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")

#: Group rule (a) arithmetic pin (S2b packet §3): superframe FER<=5% needs
#: per-frame FER <= 1-(1-0.05)^(1/4) = 1.274%.
PER_FRAME_FER_FOR_SUPERFRAME_5PCT = s2.PER_FRAME_FER_FOR_SUPERFRAME_5PCT


class Refusal(SystemExit):
    """rc=2 pre-write refusal (unauthorized / invalid / gate-blocked)."""


def refuse(reason: str) -> "Any":
    print(f"S2FER-REFUSAL rc=2: {reason}", file=sys.stderr)
    raise Refusal(2)


def frame_seed(variant: str, group: int, frame: int) -> int:
    """Frozen literal frame seed: 2026097001+idx, idx=4g+f (S2b packet §4).

    Single arm S2b only — any other variant refuses (fail closed, rc=2).
    """
    if variant != "S2b":
        refuse(f"unknown variant {variant} (frozen: single arm S2b only)")
    return S2B_FRAME_BASE + 4 * int(group) + int(frame)


def leak_basis() -> dict[str, Any]:
    """Frozen S2b f accounting (S2b packet §3).

    (i) Layer-local reported efficiency: f_L2=(m2·5)/(256·H_channel)
    =235/(256×0.80698)=235/206.586≈1.1376 (repro band 1.1373–1.1379).
    INFORMATIONAL ONLY — never gated.
    (ii) System budget mapping: f_super=(4·(m_total·5)+64)/(1024·H_full)
    =1044/852.544≈1.2246 (H_full=0.83256272). BUDGET MAPPING, not
    measured efficiency; L1 (m1≈2) unconstructed.
    """
    leak = s2.superframe_leakage(D_BLIND)
    content = GROUP_FRAMES * s2.N_FRAME * s2.H_FULL_ANCHOR
    f_l2 = (5 * s2.M2) / (s2.N_FRAME * H_CHANNEL_S2B)  # 235/206.586
    return {
        "leak_bits": leak,
        "content_bits": content,
        "f_super_basis": leak / content,  # 1.2246 at D_blind=0
        "f_super_label": ("System budget mapping: "
                          "f_super=(4·(m_total·5)+64)/(1024·H_full)"
                          "=1044/852.544≈1.2246 (H_full=0.83256272). "
                          "BUDGET MAPPING, not measured efficiency; "
                          "L1 (m1≈2) unconstructed (S2b packet §3)"),
        "f_L2_basis": f_l2,  # ≈1.1376 informational
        "f_L2_label": ("Layer-local reported efficiency: "
                       "f_L2=(m2·5)/(256·H_channel)=235/(256×0.80698)"
                       "=235/206.586≈1.1376 (repro band 1.1373–1.1379). "
                       "INFORMATIONAL ONLY — never gated (S2b packet §3)"),
        "h_channel": H_CHANNEL_S2B,
        "d_blind": D_BLIND,
        "d_blind_label": ("MEASURED zero: no blind/puncturing rounds exist "
                          "in the campaign path — NEVER assume zero "
                          "in a claim (S2b packet §3)"),
        "sensitivity": ("Δf_super = D_blind/852.544, i.e. each 16 bits "
                        "≈ +0.019; headroom to 1.3 is 64.31 bits"),
    }


def _s2b_sampler(rng, n):
    """S2b channel hook: QSC sampler at frozen p*=0.081 (S2b packet §2)."""
    return s2.qsc_pair_sampler(rng, n, p=QSTAR)


def _default_decode(construction: dict, seed: int) -> dict:
    return s2.smoke_decode_frame(construction, seed, sampler=_s2b_sampler,
                                 max_iter=MAX_ITER, qber=QSTAR)


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
        refuse("root required (fresh additive workspace/s2b_<uuid>)")
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
            "rank": construction.get("rank"),
            "family": construction.get("family"),
            "four_cycle_gate": ("==0 asserted pre-run (S2b; fixed "
                                "constructor seed 2026092001; mismatch "
                                "halts STOP-BLOCKED)"),
        },
        "seeds": {
            "policy": "literal-frozen (S2b packet §4; NOT derived)",
            "frame_base": S2B_FRAME_BASE,
            "frame_rule": "base+idx, idx=0..239 (group g frame f → idx=4g+f)",
            "absence": ("rg 2026-09-20: 20260970xx absent from src/tests/"
                        "configs/docs-rest/openspec/tools/.codebuddy; "
                        "only the frozen S2b packet+prompt docs carry "
                        "these seeds (no .workbuddy dir exists)"),
        },
        "budgets": {"wall_cap_s": WALL_CAP_S,
                    "per_decode_cap_s": PER_DECODE_CAP_S,
                    "rss_gib": RSS_CAP_GIB,
                    "max_groups": N_GROUPS, "max_decodes": N_DECODERS},
        "decoder": {"kernel": "log-FFT-SPA via smoke_decode_frame",
                    "max_iter": MAX_ITER, "qber": QSTAR,
                    "channel": ("qsc_pair_sampler QSC p*=0.081 AND decode "
                                "prior qber=0.081 (entropy-matched: "
                                "0.40569+0.081×4.954196=0.80698, Δ+7.5e-5 "
                                "vs H_L2 anchor 0.80690067); max_iter=300 "
                                "unchanged")},
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
        "f_super_label": basis["f_super_label"],
        "f_L2": basis["f_L2_basis"],
        "f_L2_label": basis["f_L2_label"],
        "h_channel": basis["h_channel"],
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
        "resume_policy_note": ("S2b packet §5: checkpoint-per-group + at "
                               "most ONE explicit wall-partial "
                               "--resume-from in a fresh window; terminal "
                               "FAIL/early-stop states never resume; no "
                               "auto-relaunch. A second resume refuses."),
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
    if (not isinstance(seeds, dict)
            or seeds.get("policy") != "literal-frozen (S2b packet §4; NOT derived)"
            or seeds.get("frame_base") != S2B_FRAME_BASE):
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
            variant: str = "S2b",
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
    if variant != "S2b":
        refuse(f"unknown variant {variant} (frozen: single arm S2b only)")
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
    """Pre-run construction gate (S2b packet §1): single arm S2b asserts
    four_cycles==0 (fixed constructor seed 2026092001) else STOP-BLOCKED;
    any other variant refuses (fail closed, rc=2)."""
    if variant != "S2b":
        refuse(f"unknown variant {variant} (frozen: single arm S2b only)")
    seed = S2B_CONSTRUCT_SEED
    trials = S2B_MAX_TRIALS
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
    if fc != S2B_FOUR_CYCLES:
        refuse(f"S2b four_cycles {fc} != {S2B_FOUR_CYCLES} (STOP-BLOCKED; "
               f"S2b packet §1)")
    code["construct_seed"] = seed
    code["construct_trials"] = trials
    return code


def run_execution(root: str, variant: str = "S2b",
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
    ap.add_argument("--variant", default="S2b")
    args = ap.parse_args(argv)
    # Dual-flag gate: refuse EVERYTHING else rc=2 BEFORE any root/contact.
    # There is no profile-only mode and no silent path.
    if not args.execute_real:
        refuse("refusing: --execute-real missing (rc2 pre-anything)")
    if not args.execution_authorized:
        refuse("refusing: --execution-authorized missing (rc2 pre-anything)")
    if args.variant != "S2b":
        refuse(f"unknown variant {args.variant} (frozen: single arm S2b only)")
    if args.resume_from and args.root and args.root != args.resume_from:
        refuse("root/resume-from mismatch (fail closed)")
    root = args.resume_from or args.root
    if not root:
        refuse("root required (fresh additive workspace/s2b_<uuid>)")
    if not root.startswith(ROOT_PREFIX):
        refuse(f"root must be fresh additive {ROOT_PREFIX}<uuid> "
               f"(got {root})")
    return run_execution(root=root, variant=args.variant,
                         resume_from=args.resume_from or None)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
