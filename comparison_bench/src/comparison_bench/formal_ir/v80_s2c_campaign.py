"""V80 S2c empirical-channel FER campaign executor (EXPLORE code — NOT execution).

Frozen contract: ``docs/research_cycles/V80-NBLDPC-JAN21/
S2C_EXPERIMENT_PACKET_20260920.md`` (G-S2C, frozen, NOT granted).
Execution needs a fresh explicit grant + Pre-EXECUTE; this module only
provides the executor + fake-testable mechanics. Synthetic draws from the
read-only 2M derived bundle only; no real/Jan-21 frames; no writes outside
the run root; never writes ``results/`` or ``outputs_comparison/``.

Three arms, one construction each (packet §1): FIXED ``peg_construct`` +
``make_rho`` + ``_reconcile_check_counts`` (frozen v10_peg path, GF(32)
labels), seed 2026092001, n=256/m2=47, construct-twice-identical required.
No ``construct_l2`` (lambda-locked {2:1}); no re-seed; no tuning.
Per-arm four-cycle gate: L-A == 0, L-B == 0, L-C == 2 (PINNED, not zero);
mismatch halts STOP-BLOCKED. Banned-family refusal unchanged
(family="peg-irregular" stamped; three-shift-cyclic never emitted).

Channel (packet §2): read-only ``gamma_f03.npz`` keys ``2M_gamma1_L1``
(32,1024) g1[u1,b], ``2M_gamma2_L2condU1`` (32,32,1024) g2[u1,u2,b]
(Q5 branch-a axes) + sibling ``gamma_f03_pb.npz`` key ``2M_p_b`` (1024,)
normalized sum=1±1e-9 (else refuse BEFORE any decode). Per-symbol triple
draw in the frozen ``make_centered_sampler`` L2 order (S1 runner L507-526):
b~p_b; u1~g1[:,b]; u2~g2[u1,:,b]; zero-mass→delta-at-0. Alice x=u2,
Bob 10-bit b. L1 conditioning is GENIE true-u1 (D1) — a genie-aided L2
upper bound, never a two-layer claim.

Decoder (packet §3, exact quoted semantics): y_i=b_i&31 (``factor_layers``
v29 L269-273); rows_i = gamma_2(.|b_i,u1_i) (``posterior_rows`` v26
L239-244 semantics); prior_error pi_i(e)=rows_i[y_i XOR e]
(``_center_rows`` v28 L189-197; GF32 char-2 add = XOR); entrypoint
``decode_error_domain_posterior`` v28 L155-186 (takes (n,q) prior;
s_e=s_x+H*y; x_hat=y+e_hat). Frozen ``decode_error_domain`` v10
L491-518 takes scalar p ONLY — NEVER used here. max_iter=300, streak
default; per-decode cap 300 s.

Seeds (packet §4, LITERAL): constructor 2026092001 all arms; frames
2026097201+idx, idx=0..239 (group g frame f → idx=4g+f, paired across
arms); stream ``common.v10_seed(f"s2c_emp:{seed}")`` (distinct domain
from S2b ``s2_smoke:``). rg 2026-09-20: 20260972/73/74xx absent
repo-wide (only the frozen S2c packet+prompt carry these seeds);
2026098xxx REJECTED (2026098001 collides R23/v22b).

Reuse from ``v80_s2_fer_campaign`` (patterns only, never its science):
dual-flag gate, checkpoint manifest+rows overwrite-in-place single writer,
append-only ``wall_windows``, explicit ``--resume-from`` with strict
pre-decode validation, early-stop at 4th group fail. No import of the S2b
campaign module's science (QSC p* path deleted here); accounting helpers
(``evaluate_superframe``, ``superframe_leakage``) are reused read-only
from ``v80_s2_peg``.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

from . import nonbinary_v10_common as common
from . import nonbinary_v10_fftqspa as fftqspa
from . import nonbinary_v10_peg as peg
from . import nonbinary_v26_mcde as _mcde  # noqa: F401 (read-only rho reuse; never edited)
from . import nonbinary_v28 as v28
from . import v80_s2_peg as s2
from .nonbinary_field import GF2mField

__all__ = [
    "S2C_CONSTRUCT_SEED", "S2C_MAX_TRIALS", "S2C_FRAME_BASE",
    "ARMS", "N_GROUPS", "GROUP_FRAMES", "N_DECODERS",
    "MAX_ITER", "H_L2_S2C", "H_FULL_S2C", "D_BLIND",
    "PASS_MAX_FAILS", "F_SUPER_MAX",
    "WALL_CAP_S", "PER_DECODE_CAP_S", "RSS_CAP_GIB",
    "ROOT_PREFIX", "FORBIDDEN_ROOT_PARTS",
    "GAMMA_DEFAULT", "PB_SIDECAR_NAME", "SOURCE_DEFAULT",
    "Refusal", "refuse", "frame_seed", "stream_seed",
    "construct_arm", "bind_empirical_bundle",
    "empirical_triple_sampler", "posterior_rows_l2",
    "center_rows_prior", "decode_frame_empirical",
    "leak_basis", "group_accounting_csv",
    "execute", "main",
]

#: Frozen S2c construction seed (packet §1; all arms).
S2C_CONSTRUCT_SEED = 2026092001
S2C_MAX_TRIALS = 20
#: Frozen literal frame-seed base (packet §4; LITERAL, not derived).
S2C_FRAME_BASE = 2026097201
#: Frozen per-arm constructor table (packet §1). four_cycles is the hard
#: gate (STOP-BLOCKED); the var/chk/socket/girth/rank pins are recorded
#: in the manifest for the Pre-EXECUTE assert table.
ARMS: dict[str, dict[str, Any]] = {
    "L-A": {"lambda": {2: 1.0}, "four_cycles": 0,
            "var_counts": {2: 256}, "chk_counts": {10: 5, 11: 42},
            "sockets": 512, "min_girth": 6, "rank": 47},
    "L-B": {"lambda": {2: 0.5, 3: 0.5}, "four_cycles": 0,
            "var_counts": {2: 154, 3: 102}, "chk_counts": {13: 44, 14: 3},
            "sockets": 614, "min_girth": 6, "rank": 47},
    "L-C": {"lambda": {3: 1.0}, "four_cycles": 2,
            "var_counts": {3: 256}, "chk_counts": {16: 31, 17: 16},
            "sockets": 768, "min_girth": 4, "rank": 47},
}
#: Frozen campaign shape (packet §1/§4): 60 groups x 4 frames = 240 decodes.
N_GROUPS = 60
GROUP_FRAMES = s2.GROUP_FRAMES
N_DECODERS = N_GROUPS * GROUP_FRAMES
#: Frozen decoder cap (packet §3): max_iter=300, streak default.
MAX_ITER = s2.MAX_ITER
#: Frozen entropy anchors (packet §5): H_L2 (2M) + H_full content basis.
H_L2_S2C = s2.H_L2_ANCHOR
H_FULL_S2C = s2.H_FULL_ANCHOR
#: D_blind = 0 MEASURED placeholder (NEVER-ASSUME-ZERO label on records).
D_BLIND = 0.0
#: Frozen pass bars (packet §5, AND): <=3 fails/60 AND f_super <= 1.3.
PASS_MAX_FAILS = 3
F_SUPER_MAX = 1.3
#: Frozen caps (packet §6): single window 3600 s; per-decode 300 s; 4 GiB.
WALL_CAP_S = 3600
PER_DECODE_CAP_S = 300
RSS_CAP_GIB = 4
#: Fresh additive run-root prefix (packet §6).
ROOT_PREFIX = "workspace/s2c_"
#: Roots the executor never writes under.
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")
#: Read-only derived bundle (packet §2): gamma file + p_b sidecar sibling.
GAMMA_DEFAULT = "docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz"
PB_SIDECAR_NAME = "gamma_f03_pb.npz"
#: Worst-source anchor (packet §2); never auto-merge sources.
SOURCE_DEFAULT = "2M"

#: Group rule (a) arithmetic pin (packet §1/§5): superframe FER<=5% needs
#: per-frame FER <= 1-(1-0.05)^(1/4) = 1.274%.
PER_FRAME_FER_FOR_SUPERFRAME_5PCT = s2.PER_FRAME_FER_FOR_SUPERFRAME_5PCT


class Refusal(SystemExit):
    """rc=2 pre-write refusal (unauthorized / invalid / gate-blocked)."""


def refuse(reason: str) -> "Any":
    print(f"S2C-REFUSAL rc=2: {reason}", file=sys.stderr)
    raise Refusal(2)


def frame_seed(arm: str, group: int, frame: int) -> int:
    """Frozen literal frame seed: 2026097201+idx, idx=4g+f (packet §4).

    Paired across arms (same seed ⇒ same channel triple ⇒ same (x, b)).
    Unknown arm refuses (fail closed, rc=2).
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: L-A|L-B|L-C only)")
    return S2C_FRAME_BASE + 4 * int(group) + int(frame)


def stream_seed(seed: int) -> int:
    """Frozen stream derivation: ``common.v10_seed(f"s2c_emp:{seed}")``."""
    return common.v10_seed(f"s2c_emp:{int(seed)}")


def construct_arm(arm: str, seed: int = S2C_CONSTRUCT_SEED,
                  max_trials: int = S2C_MAX_TRIALS) -> dict[str, Any]:
    """FIXED per-arm constructor (packet §1): ``peg_construct`` + ``make_rho``
    + ``_reconcile_check_counts`` (inside ``peg_construct``), GF(32) labels,
    n=256/m2=47. No ``construct_l2`` (lambda-locked); no re-seed; no tuning.
    Pure in-memory; no disk writes.
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: L-A|L-B|L-C only)")
    field = GF2mField.create(s2.Q)
    lam = {int(k): float(v) for k, v in ARMS[arm]["lambda"].items()}
    rho = _mcde.make_rho(1.0 - s2.M2 / s2.N_FRAME, lam)
    result = peg.peg_construct(s2.N_FRAME, s2.M2, lam, rho, int(seed),
                               max_trials=int(max_trials), field=field)
    result["family"] = "peg-irregular"
    s2.refuse_three_shift_cyclic({"family": result["family"]})
    result["lambda_edge"] = lam
    result["rho_edge"] = {int(k): float(v) for k, v in rho.items()}
    return result


def bind_empirical_bundle(gamma_source: Any,
                          source: str = SOURCE_DEFAULT) -> dict[str, Any]:
    """Bind the read-only 2M derived bundle (packet §2). Fail closed BEFORE
    any decode. Accepts a file path (loads ``{source}_gamma1_L1`` /
    ``{source}_gamma2_L2condU1`` + the sibling-sidecar ``{source}_p_b``)
    or an already-loaded mapping (tests) with keys g1/g2/p_b.

    Axes (Q5 branch-a, frozen): g1[u1,b] (32,1024), g2[u1,u2,b]
    (32,32,1024) = V26 pjoint convention (cond-rowsum over axis=1).
    Artifact untouched. p_b MUST be normalized sum=1±1e-9 (else refuse);
    there is no uniform fallback here. Bundle read-only; never refit.
    """
    if isinstance(gamma_source, str):
        try:
            npz = np.load(gamma_source)  # read-only load; never refit
            try:
                g1 = np.asarray(npz[f"{source}_gamma1_L1"], dtype=np.float64)
                g2 = np.asarray(npz[f"{source}_gamma2_L2condU1"],
                                dtype=np.float64)
            finally:
                npz.close()
        except Refusal:
            raise
        except Exception as exc:  # noqa: BLE001 — fail closed on load failure
            refuse(f"gamma load failed for {gamma_source}[{source}]: "
                   f"{type(exc).__name__}: {exc}")
        side = Path(gamma_source).parent / PB_SIDECAR_NAME
        try:
            sp = np.load(side)  # read-only sidecar; never refit
            try:
                _pb = np.asarray(sp[f"{source}_p_b"], dtype=np.float64)
            finally:
                sp.close()
        except Refusal:
            raise
        except Exception as exc:  # noqa: BLE001 — fail closed, no fallback
            refuse(f"p_b sidecar missing/unreadable ({side}[{source}_p_b]): "
                   f"{type(exc).__name__}: {exc}")
        p_b = _pb
    else:
        try:
            g1 = np.asarray(gamma_source["g1"], dtype=np.float64)
            g2 = np.asarray(gamma_source["g2"], dtype=np.float64)
            p_b = np.asarray(gamma_source["p_b"], dtype=np.float64)
        except Exception as exc:  # noqa: BLE001 — fail closed (absent keys)
            refuse(f"bundle missing g1/g2/p_b keys: "
                   f"{type(exc).__name__}: {exc}")
    if g1.shape != (32, 1024):
        refuse(f"g1 shape {g1.shape} != (32, 1024)")
    if g2.shape != (32, 32, 1024):
        refuse(f"g2 shape {g2.shape} != (32, 32, 1024)")
    if (not np.all(np.isfinite(g1)) or np.any(g1 < 0.0)
            or not np.allclose(g1.sum(axis=0), 1.0, atol=1e-9)):
        refuse("g1 colsums != 1 (finite/nonneg/colsums)")
    if (not np.all(np.isfinite(g2)) or np.any(g2 < 0.0)
            or not np.allclose(g2.sum(axis=1), 1.0, atol=1e-9)):
        refuse("g2 cond-rowsums (axis=1) != 1 (finite/nonneg/rowsums)")
    p_b = np.asarray(p_b, dtype=np.float64)
    if (p_b.shape != (1024,) or not np.all(np.isfinite(p_b))
            or np.any(p_b < 0.0) or abs(float(p_b.sum()) - 1.0) > 1e-9):
        refuse("p_b not normalized (shape/finite/nonneg/sum=1±1e-9)")
    return {"g1": g1, "g2": g2, "p_b": p_b, "source": source}


def empirical_triple_sampler(bundle: dict[str, Any], n: int,
                             rng: np.random.Generator) -> tuple:
    """Per-symbol triple draw (packet §2) in the frozen
    ``make_centered_sampler`` L2 order (S1 runner L507-526): b~p_b via
    ``rng.choice(1024, p=p_b)``; u1~g1[:,b]/sum (zero-mass→delta-at-0);
    u2~g2[u1,:,b]/sum (zero-mass→delta-at-0). I.i.d. per symbol.
    Returns (b, u1, u2) int64 vectors; the triple is retained (Alice
    x=u2, Bob b, GENIE u1). RNG-only randomness.
    """
    g1, g2, p_b = bundle["g1"], bundle["g2"], bundle["p_b"]
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        refuse("triple sampler n must be a positive int")
    if not isinstance(rng, np.random.Generator):
        refuse("triple sampler rng must be a numpy Generator")
    b = rng.choice(1024, size=n, p=p_b)
    u1 = np.empty(n, dtype=np.int64)
    u2 = np.empty(n, dtype=np.int64)
    for i in range(n):
        bb = int(b[i])
        g1col = g1[:, bb]
        s1 = g1col.sum()
        if not np.isfinite(s1) or s1 <= 0.0:
            u1t = 0
        else:
            u1t = int(rng.choice(32, p=g1col / s1))
        row = np.asarray(g2[u1t, :, bb], dtype=np.float64)
        tot = row.sum()
        if not np.isfinite(tot) or tot <= 0.0:
            row = np.zeros(32)
            row[0] = 1.0
        else:
            row = row / tot
        u2t = int(rng.choice(32, p=row))
        u1[i], u2[i] = u1t, u2t
    return (np.asarray(b, dtype=np.int64), u1, u2)


def posterior_rows_l2(bundle: dict[str, Any], b_vec: Any,
                      u1_vec: Any) -> np.ndarray:
    """rows_i = gamma_2(.|b_i,u1_i) (``posterior_rows`` v26 L239-244
    semantics): ``pjoint[u1,:,b]/norm``, ``norm<=0 → delta-at-0``.
    Here g2 IS the conditional (cond-rowsum over axis=1 == 1, bound at
    bind); norm = g1[u1,b] = P(U1|B) carries the frozen zero-mass gate.
    """
    g1, g2 = bundle["g1"], bundle["g2"]
    b = np.asarray(b_vec, dtype=np.int64)
    u1 = np.asarray(u1_vec, dtype=np.int64)
    if b.shape != u1.shape or b.ndim != 1:
        refuse("posterior rows need same-shape 1-D (b, u1)")
    n = int(b.shape[0])
    rows = np.empty((n, 32), dtype=np.float64)
    for i in range(n):
        bb, uu = int(b[i]), int(u1[i])
        if not 0 <= bb < 1024 or not 0 <= uu < 32:
            refuse("posterior rows symbol out of domain")
        norm = float(g1[uu, bb])
        row = np.asarray(g2[uu, :, bb], dtype=np.float64)
        tot = float(row.sum())
        if (not np.isfinite(norm) or norm <= 0.0
                or not np.isfinite(tot) or tot <= 0.0):
            row = np.zeros(32)
            row[0] = 1.0
        else:
            row = row / tot
        rows[i] = row
    return rows


def center_rows_prior(rows: Any, y_vec: Any) -> np.ndarray:
    """prior_error pi_i(e) = rows_i[y_i XOR e] (``_center_rows`` v28
    L189-197 ``out[i]=arr[i,add[y,arange]]``; GF32 char-2 add = XOR).
    """
    arr = np.asarray(rows, dtype=np.float64)
    yv = np.asarray(y_vec, dtype=np.int64)
    if arr.ndim != 2 or arr.shape[1] != 32 or arr.shape[0] != yv.shape[0]:
        refuse("center rows need (n,32) rows + length-n y")
    idx = np.bitwise_xor(yv[:, None], np.arange(32, dtype=np.int64)[None, :])
    out = np.empty_like(arr)
    for i in range(arr.shape[0]):
        out[i] = arr[i, idx[i]]
    return out


def decode_frame_empirical(construction: dict[str, Any], seed: int,
                           bundle: dict[str, Any]) -> dict[str, Any]:
    """One empirical-channel frame (packet §3): triple draw on the
    ``s2c_emp:{seed}`` stream; Alice x=u2; Bob y=b&31; GENIE true-u1 rows;
    centered (n,32) prior into ``decode_error_domain_posterior``
    (NEVER the scalar-p ``decode_error_domain``); max_iter=300, streak
    default. Returns the raw kernel verdict + exact-match flag
    (``exact_match is True`` per frame gates the group).
    """
    if isinstance(seed, bool) or not isinstance(seed, int):
        refuse("frame seed must be an integer")
    field = GF2mField.create(s2.Q)
    dense = peg.sparse_to_dense(construction["triples"], s2.N_FRAME, s2.M2,
                                field)
    rng = np.random.default_rng(stream_seed(int(seed)))
    b, u1, u2 = empirical_triple_sampler(bundle, s2.N_FRAME, rng)
    x = np.asarray(u2, dtype=np.int64)  # Alice vector (syndrome source)
    y = np.asarray(b & 31, dtype=np.int64)  # Bob L2 half (F03 bits 4..0)
    s_x = fftqspa.syndrome_of(field, dense, x.tolist())
    rows = posterior_rows_l2(bundle, b, u1)  # GENIE true-u1 (D1 ceiling)
    prior = center_rows_prior(rows, y)
    result = v28.decode_error_domain_posterior(field, y.tolist(), dense,
                                               s_x, prior, MAX_ITER)
    x_hat = result.get("x_hat")
    return {
        "status": result.get("status"),
        "iterations": result.get("iterations"),
        "reconstruction_ok": bool(result.get("reconstruction_ok", False)),
        "exact_match": (bool(np.array_equal(np.asarray(x_hat), x))
                        if x_hat is not None else False),
        "seed": int(seed),
        "max_iter": int(MAX_ITER),
        "l1_conditioning": "GENIE true-u1 (D1 ceiling)",
    }


def leak_basis() -> dict[str, Any]:
    """Frozen S2c f accounting (packet §5; same m2/anchors as S2b).

    (i) Layer-local reported efficiency: f_L2=(m2·5)/(256·H_L2)
    =235/(256×0.80690067)≈1.1376. INFORMATIONAL ONLY — never gated.
    (ii) System budget mapping: f_super=(4·(m_total·5)+64)/(1024·H_full)
    =1044/852.544≈1.2246 (H_full=0.83256272). BUDGET MAPPING, not
    measured efficiency; L1 (m1≈2) unconstructed, GENIE-conditioned.
    """
    leak = s2.superframe_leakage(D_BLIND)
    content = GROUP_FRAMES * s2.N_FRAME * H_FULL_S2C
    f_l2 = (5 * s2.M2) / (s2.N_FRAME * H_L2_S2C)  # ≈1.1376 informational
    return {
        "leak_bits": leak,
        "content_bits": content,
        "f_super_basis": leak / content,  # 1.2246 at D_blind=0
        "f_super_label": ("System budget mapping: "
                          "f_super=(4·(m_total·5)+64)/(1024·H_full)"
                          "=1044/852.544≈1.2246 (H_full=0.83256272). "
                          "BUDGET MAPPING, not measured efficiency; "
                          "L1 (m1≈2) unconstructed, GENIE true-u1 "
                          "conditioning (S2c packet §5)"),
        "f_L2_basis": f_l2,  # ≈1.1376 informational
        "f_L2_label": ("Layer-local reported efficiency: "
                       "f_L2=(m2·5)/(256·H_L2)=235/(256×0.80690067)"
                       "≈1.1376. INFORMATIONAL ONLY — never gated "
                       "(S2c packet §5)"),
        "h_l2": H_L2_S2C,
        "h_full": H_FULL_S2C,
        "d_blind": D_BLIND,
        "d_blind_label": ("MEASURED zero: no blind/puncturing rounds exist "
                          "in the campaign path — NEVER assume zero "
                          "in a claim (S2c packet §5)"),
        "sensitivity": ("Δf_super = D_blind/852.544, i.e. each 16 bits "
                        "≈ +0.019; headroom to 1.3 is 64.31 bits"),
    }


def group_accounting_csv(rows: list[dict]) -> str:
    """Per-group accounting table (packet §8 deliverable)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["group", "n_frames", "n_ok", "group_accept",
                "superframe_fail", "per_frame_fer", "d_blind",
                "leak_bits", "f_super", "seeds", "iterations"])
    for r in rows:
        if r.get("status") in ("error", "overrun"):
            w.writerow([r.get("group"), "", "", "", "", "",
                        "", "", "", "", r.get("status")])
            continue
        frames = r.get("frames", [])
        w.writerow([r.get("group"), len(frames),
                    sum(1 for f in frames if f.get("frame_ok")),
                    r.get("group_accept"), r.get("superframe_fail"),
                    r.get("per_frame_fer"), r.get("d_blind"),
                    r.get("leak_bits"), r.get("f_super"),
                    ";".join(str(f.get("seed")) for f in frames),
                    ";".join(str(f.get("iterations")) for f in frames)])
    return buf.getvalue()


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
        refuse("root required (fresh additive workspace/s2c_<uuid>)")
    parts = Path(root).parts
    if any(p in FORBIDDEN_ROOT_PARTS for p in parts):
        refuse(f"root under forbidden tree (results/outputs_comparison): {root}")


def _build_manifest(*, arm: str, construction: dict, rows: list[dict],
                    failures: int, groups_completed: int, verdict: str,
                    partial: bool, next_group: int,
                    wall_windows: list[dict], ledger_decodes: int,
                    elapsed_s: float) -> dict:
    basis = leak_basis()
    spec = ARMS[arm]
    n = len(rows)
    fer = (failures / n) if n else None
    return {
        "arm": arm,
        "construct": {
            "seed": construction.get("construct_seed"),
            "max_trials": construction.get("construct_trials"),
            "lambda": {str(k): float(v)
                       for k, v in spec["lambda"].items()},
            "four_cycles": construction.get("four_cycles"),
            "min_girth": construction.get("min_girth"),
            "rank": construction.get("rank"),
            "family": construction.get("family"),
            "four_cycle_gate": (f"=={spec['four_cycles']} asserted pre-run "
                                f"({arm}; fixed constructor seed "
                                f"{S2C_CONSTRUCT_SEED}; construct-twice-"
                                f"identical required; mismatch halts "
                                f"STOP-BLOCKED)"),
            "pinned_table": {k: spec[k] for k in
                             ("var_counts", "chk_counts", "sockets",
                              "min_girth", "rank")},
        },
        "seeds": {
            "policy": "literal-frozen (S2c packet §4; NOT derived)",
            "frame_base": S2C_FRAME_BASE,
            "frame_rule": "base+idx, idx=0..239 (group g frame f → idx=4g+f)",
            "stream": "common.v10_seed(f\"s2c_emp:{seed}\") (paired across "
                      "arms; distinct domain from S2b s2_smoke:)",
            "absence": ("rg 2026-09-20: 20260972/73/74xx absent repo-wide "
                        "(only the frozen S2c packet+prompt docs carry "
                        "these seeds); 2026098xxx REJECTED (2026098001 "
                        "collides R23/v22b)"),
        },
        "channel": {
            "source": SOURCE_DEFAULT,
            "bundle": "gamma_f03.npz keys 2M_gamma1_L1 (32,1024) + "
                      "2M_gamma2_L2condU1 (32,32,1024) + sidecar "
                      "gamma_f03_pb.npz key 2M_p_b (1024,) normalized "
                      "sum=1±1e-9 else refuse (read-only, never refit)",
            "sampler": ("per-symbol triple b~p_b; u1~g1[:,b]; u2~g2[u1,:,b]; "
                        "zero-mass→delta-at-0; frozen make_centered_sampler "
                        "L2 order; Alice x=u2, Bob 10-bit b"),
        },
        "budgets": {"wall_cap_s": WALL_CAP_S,
                    "per_decode_cap_s": PER_DECODE_CAP_S,
                    "rss_gib": RSS_CAP_GIB,
                    "max_groups": N_GROUPS, "max_decodes": N_DECODERS},
        "decoder": {
            "entrypoint": ("decode_error_domain_posterior (nonbinary_v28 "
                           "L155-186; takes (n,q) prior; s_e=s_x+H*y; "
                           "x_hat=y+e_hat). Frozen decode_error_domain "
                           "(v10 L491-518, scalar p ONLY) NEVER used here."),
            "kernel": "log-FFT-SPA with per-variable P(E_i) prior",
            "max_iter": MAX_ITER, "streak": "default (3)",
            "wiring": ("y_i=b_i&31 (factor_layers v29 L269-273); "
                       "rows_i=gamma_2(.|b_i,u1_i) (posterior_rows v26 "
                       "L239-244); pi_i(e)=rows_i[y_i XOR e] (_center_rows "
                       "v28 L189-197; GF32 char-2 add=XOR)"),
            "l1_conditioning": ("GENIE true-u1 (D1): S2c is a genie-aided L2 "
                                "upper bound (ceiling), never a two-layer "
                                "claim (S2c packet §2/§8)"),
            "channel": "empirical 2M triple sampler (packet §2)",
        },
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
        "h_l2": basis["h_l2"],
        "h_full": basis["h_full"],
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
        "resume_policy_note": ("S2c packet §6: checkpoint-per-group + at "
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


def _validate_partial(manifest: dict, rows: list, arm: str) -> dict:
    """Fail-closed partial validation BEFORE any decode (zero decodes on
    refuse). Checks: arm match, frozen seeds/budgets, ledger internal
    consistency (decodes == 4*groups, rows contiguous 0..k-1), no final
    verdict (completion is not resumable), at most-one continuation unused
    (exactly one wall window so far)."""
    if not isinstance(manifest, dict):
        refuse("partial manifest not a dict")
    if not isinstance(rows, list):
        refuse("partial rows not a list")
    if manifest.get("arm") != arm:
        refuse("partial arm mismatch (fail closed)")
    seeds = manifest.get("seeds", {})
    if (not isinstance(seeds, dict)
            or seeds.get("policy") != "literal-frozen (S2c packet §4; NOT derived)"
            or seeds.get("frame_base") != S2C_FRAME_BASE):
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


def _construct_gate(arm: str, construct_fn: Callable) -> dict:
    """Pre-run construction gate (packet §1/E1): per-arm four-cycle assert
    on the FIXED constructor (seed 2026092001), construct-twice-identical
    required; mismatch halts STOP-BLOCKED; unknown arm refuses (rc=2).
    ``construct_fn`` convention is ``(arm, seed, max_trials)``, mirroring
    ``construct_arm`` (NOT the single-arm S2b ``(seed, trials)``)."""
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: L-A|L-B|L-C only)")
    seed = S2C_CONSTRUCT_SEED
    trials = S2C_MAX_TRIALS
    try:
        code_a = construct_fn(arm, seed, trials)
        code_b = construct_fn(arm, seed, trials)
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed pre-decode
        refuse(f"construction failed ({arm}): "
               f"{type(exc).__name__}: {exc}")
    ta, tb = code_a.get("triples"), code_b.get("triples")
    if ta is not None or tb is not None:
        try:
            sa = sorted(tuple(map(int, t)) for t in ta)
            sb = sorted(tuple(map(int, t)) for t in tb)
        except Exception:  # noqa: BLE001
            refuse(f"construction triples corrupt ({arm}; STOP-BLOCKED)")
        if sa != sb:
            refuse(f"construct-twice mismatch ({arm}; not identical; "
                   f"STOP-BLOCKED)")
    if code_a.get("status", "ok") != "ok":
        refuse(f"construction {code_a.get('status')} ({arm}; STOP-BLOCKED)")
    try:
        fc = int(code_a.get("four_cycles"))
    except Exception:  # noqa: BLE001
        refuse(f"construction missing four_cycles ({arm}; STOP-BLOCKED)")
    want = int(ARMS[arm]["four_cycles"])
    if fc != want:
        refuse(f"{arm} four_cycles {fc} != {want} (STOP-BLOCKED; "
               f"S2c packet §1)")
    code_a["construct_seed"] = seed
    code_a["construct_trials"] = trials
    return code_a


def execute(*, root: str, arm: str,
            bundle: dict[str, Any] | None = None,
            construct_fn: Callable | None = None,
            decode_fn: Callable | None = None,
            clock: Callable | None = None,
            rss_fn: Callable | None = None,
            writer: Callable | None = None,
            resume_from: str | None = None,
            max_groups: int | None = None) -> dict:
    """Run (or once-continue) the frozen 60x4 campaign under ``root``.

    One arm per invocation; paired frame seeds shared across arms.
    ``max_groups`` is a PROBE-ONLY cap (timing integration; never a CLI
    flag, never part of any verdict). All writes stay under ``root``.
    Without an injected ``decode_fn``, ``bundle`` is required (no silent
    production bind — the CLI binds ``--gamma`` explicitly).
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: L-A|L-B|L-C only)")
    _check_root(root)
    construct_fn = construct_fn or construct_arm
    if decode_fn is None:
        if bundle is None:
            refuse("empirical bundle required (no silent production bind; "
                   "pass bundle or bind --gamma at the CLI)")
        _bundle = bundle

        def decode_fn(construction, seed, _b=_bundle):  # noqa: B023
            return decode_frame_empirical(construction, seed, _b)
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
        st = _validate_partial(manifest_p, rows_p, arm)
        construction = _construct_gate(arm, construct_fn)
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
        construction = _construct_gate(arm, construct_fn)
        rows = []
        failures = 0
        ledger_decodes = 0
        t_start = clock()
        wall_windows = [{"turn_start": float(t_start), "cap": WALL_CAP_S}]
        start_group = 0

    target = N_GROUPS if max_groups is None else min(max_groups, N_GROUPS)

    def _flush(verdict: str, partial: bool, next_group: int):
        mf = _build_manifest(
            arm=arm, construction=construction, rows=rows,
            failures=failures, groups_completed=len(rows), verdict=verdict,
            partial=partial, next_group=next_group,
            wall_windows=wall_windows, ledger_decodes=ledger_decodes,
            elapsed_s=clock() - t_start)
        writer(root, {"manifest.json": json.dumps(mf, indent=1,
                                                  sort_keys=True, default=str),
                      "rows.json": json.dumps(rows, indent=1,
                                              sort_keys=True, default=str),
                      "group_accounting.csv": group_accounting_csv(rows)})
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
            seed = frame_seed(arm, g, f)
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


def run_execution(root: str, arm: str,
                  resume_from: str | None = None,
                  gamma: str = GAMMA_DEFAULT,
                  source: str = SOURCE_DEFAULT,
                  bundle: dict[str, Any] | None = None) -> int:
    bound = bundle if bundle is not None else bind_empirical_bundle(
        gamma, source)
    manifest = execute(root=root, arm=arm, bundle=bound,
                       resume_from=resume_from)
    print(json.dumps({"arm": manifest["arm"],
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
    ap.add_argument("--arm", default="")
    ap.add_argument("--root", default="")
    ap.add_argument("--resume-from", default="")
    ap.add_argument("--gamma", default=GAMMA_DEFAULT)
    ap.add_argument("--source", default=SOURCE_DEFAULT)
    args = ap.parse_args(argv)
    # Dual-flag gate: refuse EVERYTHING else rc=2 BEFORE any root/contact.
    # There is no profile-only mode and no silent path.
    if not args.execute_real:
        refuse("refusing: --execute-real missing (rc2 pre-anything)")
    if not args.execution_authorized:
        refuse("refusing: --execution-authorized missing (rc2 pre-anything)")
    if args.arm not in ARMS:
        refuse(f"unknown arm {args.arm} (frozen: L-A|L-B|L-C only)")
    if args.resume_from and args.root and args.root != args.resume_from:
        refuse("root/resume-from mismatch (fail closed)")
    root = args.resume_from or args.root
    if not root:
        refuse("root required (fresh additive workspace/s2c_<uuid>)")
    if not root.startswith(ROOT_PREFIX):
        refuse(f"root must be fresh additive {ROOT_PREFIX}<uuid> "
               f"(got {root})")
    return run_execution(root=root, arm=args.arm,
                         resume_from=args.resume_from or None,
                         gamma=args.gamma, source=args.source)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
