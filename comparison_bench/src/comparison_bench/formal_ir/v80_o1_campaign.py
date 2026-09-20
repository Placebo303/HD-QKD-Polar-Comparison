"""V80 O1 superframe-as-code FER campaign executor (EXPLORE code — NOT execution).

Frozen contract: ``docs/research_cycles/V80-NBLDPC-JAN21/
O1_EXPERIMENT_PACKET_20260920.md`` (G-O1, frozen, NOT granted).
Execution needs a fresh explicit grant + Pre-EXECUTE; this module only
provides the executor + fake-testable mechanics. Synthetic draws from the
read-only 2M derived bundle only; no real/Jan-21 frames; no writes outside
the run root; never writes ``results/`` or ``outputs_comparison/``.

Single-code semantics (packet §1, REPLACES the S2c 4x256 grouping): ONE
code n=1024, GF(32), lambda={2:1}; acceptance unit = ONE BLOCK = one
n=1024 decode with ``exact_match is True``. No frames, no group-of-4 rule,
no any-frame-fail grouping. Per arm: 60 blocks = 60 decodes; block FER =
fails/60; gate <=3/60 (<=5%). Early-stop at 4th block failure -> FAIL,
retain partials. Block outcomes are NOT directly comparable to S2c group
FER (packet §9).

Two arms, one construction each (packet §2): FIXED ``peg_construct`` +
``make_rho`` + ``_reconcile_check_counts`` (frozen v10_peg path, GF(32)
labels), seed 2026092001, trials 20, construct-twice-identical required.
A188 PRIMARY (m=188, rate 0.81640625, S1 rate-identical -> NO new DE arm);
A208 SECONDARY (m=208, rate 0.796875 -> A208-DE pre-check, packet §3).
Per-arm pins: four_cycles=0, min_girth=8, rank=m (scoping dry trial-1);
mismatch halts STOP-BLOCKED. Banned-family refusal unchanged
(family="peg-irregular" stamped; three-shift-cyclic never emitted).

Channel/decoder (packet §4, frozen S2c semantics at n=1024 symbols/block):
same 2M bundle binding, per-symbol triple (L2 order, i.i.d. x1024),
y_i=b_i&31, rows=gamma_2(.|b_i,u1_i), XOR-centered prior, entrypoint
``decode_error_domain_posterior`` (NEVER the scalar-p
``decode_error_domain``). max_iter=300, streak default; per-decode cap
300 s. GENIE true-u1 = D1 ceiling label carried (upper bound only).

Channel helpers (``bind_empirical_bundle``, ``empirical_triple_sampler``,
``posterior_rows_l2``, ``center_rows_prior``) are reused READ-ONLY from
``v80_s2c_campaign`` — never re-implemented here. Only the block decode
is local: S2c ``decode_frame_empirical`` hardcodes n=256/m=47, so this
module implements its own (n,m)-parameterized block decode following the
SAME frozen semantics.

Reuse from ``v80_s2c_campaign``/``v80_s2_peg`` (patterns only, never S2c
science): dual-flag gate, checkpoint manifest+rows overwrite-in-place
single writer, append-only ``wall_windows``, explicit ``--resume-from``
with strict pre-decode validation, early-stop at the 4th block fail.
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
from . import v80_s2c_campaign as s2c
from .nonbinary_field import GF2mField

__all__ = [
    "O1_CONSTRUCT_SEED", "O1_MAX_TRIALS", "O1_BLOCK_BASE",
    "ARMS", "O1_N", "N_BLOCKS",
    "MAX_ITER", "H_L2_O1", "H_FULL_O1", "CONTENT_BITS", "D_BLIND",
    "PASS_MAX_FAILS", "F_SUPER_MAX",
    "WALL_CAP_S", "PER_DECODE_CAP_S", "RSS_CAP_GIB",
    "ROOT_PREFIX", "FORBIDDEN_ROOT_PARTS",
    "GAMMA_DEFAULT", "SOURCE_DEFAULT",
    "DE_PRECHECK", "DE_PRECHECK_RATE", "DE_LABELS",
    "Refusal", "refuse", "block_seed", "stream_seed",
    "construct_arm", "decode_block_empirical",
    "de_centered_sampler", "leak_basis", "block_accounting_csv",
    "run_de_precheck", "execute", "main",
]

#: Frozen O1 construction seed (packet §2; both arms; n=1024 here, so
#: disjoint from prior n=256 uses of the same seed).
O1_CONSTRUCT_SEED = 2026092001
O1_MAX_TRIALS = 20
#: Frozen literal block-seed base (packet §5; LITERAL, not derived).
O1_BLOCK_BASE = 2026095501
#: Frozen per-arm constructor/accounting table (packet §2/§6). Pins are
#: the hard gate (STOP-BLOCKED); sockets/parity are recorded pins from
#: the scoping dry run (sockets 2048, parity 0 both arms).
ARMS: dict[str, dict[str, Any]] = {
    "A188": {"m": 188, "four_cycles": 0, "min_girth": 8, "rank": 188,
             "lambda": {2: 1.0}, "rate": 1.0 - 188 / 1024,
             "leak_bits": 188 * 5 + 64, "role": "PRIMARY (DE-covered)"},
    "A208": {"m": 208, "four_cycles": 0, "min_girth": 8, "rank": 208,
             "lambda": {2: 1.0}, "rate": 1.0 - 208 / 1024,
             "leak_bits": 208 * 5 + 64, "role": "SECONDARY (budget-max)"},
}
#: Frozen single-code length (packet §1): n=1024 symbols/block.
O1_N = 1024
#: Frozen campaign shape (packet §1): 60 blocks = 60 decodes/arm.
N_BLOCKS = 60
#: Frozen decoder cap (packet §4): max_iter=300, streak default.
MAX_ITER = s2.MAX_ITER
#: Frozen entropy anchors (packet §6): H_L2 (2M) + H_full content basis.
H_L2_O1 = s2.H_L2_ANCHOR
H_FULL_O1 = s2.H_FULL_ANCHOR
#: Content basis: 1024 * H_full = 852.544 bits (packet §6).
CONTENT_BITS = O1_N * H_FULL_O1
#: D_blind = 0 MEASURED placeholder (NEVER-ASSUME-ZERO label on records).
D_BLIND = 0.0
#: Frozen pass bars (packet §6, AND): <=3 fails/60 AND f_super <= 1.3.
PASS_MAX_FAILS = 3
F_SUPER_MAX = 1.3
#: Frozen caps (packet §7): single window 3600 s; per-decode 300 s; 4 GiB.
WALL_CAP_S = 3600
PER_DECODE_CAP_S = 300
RSS_CAP_GIB = 4
#: Fresh additive run-root prefix (packet §7).
ROOT_PREFIX = "workspace/o1_"
#: Roots the executor never writes under.
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")
#: Read-only derived bundle (packet §4): gamma file + p_b sidecar sibling
#: (same files as S2c; binding helper reused read-only from s2c).
GAMMA_DEFAULT = s2c.GAMMA_DEFAULT
#: Worst-source anchor (packet §4); never auto-merge sources.
SOURCE_DEFAULT = s2c.SOURCE_DEFAULT
#: A208-DE pre-check rate (packet §3): m=208 -> 1-208/1024 = 0.796875.
DE_PRECHECK_RATE = 1.0 - 208 / 1024
#: A208-DE pre-check sampling convention: S1 CONFIRM (n_samples=16000,
#: max_iter=100, tol=1e-4, streak=20) + first CONFIRM seed 2026094951
#: (v80_s1_mcde_runner CONFIRM/CONFIRM_SEEDS). A confirmatory-grade single
#: point (not SCREEN): the pre-check decides a DE-cover label.
DE_PRECHECK: dict[str, Any] = {
    "n_samples": 16000, "max_iter": 100, "tol": 1e-4, "streak": 20,
    "seed": 2026094951,
}
#: Allowed DE-cover labels threading into the campaign manifest.
DE_LABELS = ("covered", "exploratory")


class Refusal(SystemExit):
    """rc=2 pre-write refusal (unauthorized / invalid / gate-blocked)."""


def refuse(reason: str) -> "Any":
    print(f"O1-REFUSAL rc=2: {reason}", file=sys.stderr)
    raise Refusal(2)


def block_seed(arm: str, idx: int) -> int:
    """Frozen literal block seed: 2026095501+idx, idx=0..59 (packet §5).

    Shared/paired across arms (same seed ⇒ same channel triple ⇒ same
    (x, b)). Unknown arm refuses (fail closed, rc=2).
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: A188|A208 only)")
    return O1_BLOCK_BASE + int(idx)


def stream_seed(seed: int) -> int:
    """Frozen stream derivation: ``common.v10_seed(f"o1_blk:{seed}")``."""
    return common.v10_seed(f"o1_blk:{int(seed)}")


def construct_arm(arm: str, seed: int = O1_CONSTRUCT_SEED,
                  max_trials: int = O1_MAX_TRIALS) -> dict[str, Any]:
    """FIXED per-arm constructor (packet §2): ``peg_construct`` + ``make_rho``
    + ``_reconcile_check_counts`` (inside ``peg_construct``), GF(32) labels,
    n=1024/m per arm. No re-seed; no tuning. Pure in-memory; no disk writes.
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: A188|A208 only)")
    m = int(ARMS[arm]["m"])
    field = GF2mField.create(s2.Q)
    lam = {int(k): float(v) for k, v in ARMS[arm]["lambda"].items()}
    rho = _mcde.make_rho(1.0 - m / O1_N, lam)
    result = peg.peg_construct(O1_N, m, lam, rho, int(seed),
                               max_trials=int(max_trials), field=field)
    result["family"] = "peg-irregular"
    s2.refuse_three_shift_cyclic({"family": result["family"]})
    result["lambda_edge"] = lam
    result["rho_edge"] = {int(k): float(v) for k, v in rho.items()}
    return result


def decode_block_empirical(construction: dict[str, Any], seed: int,
                           bundle: dict[str, Any], n: int,
                           m: int) -> dict[str, Any]:
    """One empirical-channel block (packet §4): triple draw on the
    ``o1_blk:{seed}`` stream; Alice x=u2; Bob y=b&31; GENIE true-u1 rows;
    centered (n,32) prior into ``decode_error_domain_posterior``
    (NEVER the scalar-p ``decode_error_domain``); max_iter=300, streak
    default. Returns the raw kernel verdict + exact-match flag
    (``exact_match is True`` gates block acceptance). Fail-closed wiring
    guard: (n, m) must match the construction under test.
    """
    if isinstance(seed, bool) or not isinstance(seed, int):
        refuse("block seed must be an integer")
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        refuse("block n must be a positive int")
    if isinstance(m, bool) or not isinstance(m, int) or m < 1:
        refuse("block m must be a positive int")
    if construction.get("n") != int(n) or construction.get("m") != int(m):
        refuse(f"construction (n, m) mismatch: got "
               f"({construction.get('n')}, {construction.get('m')}) "
               f"for block ({int(n)}, {int(m)})")
    field = GF2mField.create(s2.Q)
    dense = peg.sparse_to_dense(construction["triples"], int(n), int(m),
                                field)
    rng = np.random.default_rng(stream_seed(int(seed)))
    b, u1, u2 = s2c.empirical_triple_sampler(bundle, int(n), rng)
    x = np.asarray(u2, dtype=np.int64)  # Alice vector (syndrome source)
    y = np.asarray(b & 31, dtype=np.int64)  # Bob L2 half (F03 bits 4..0)
    s_x = fftqspa.syndrome_of(field, dense, x.tolist())
    rows = s2c.posterior_rows_l2(bundle, b, u1)  # GENIE true-u1 (D1 ceiling)
    prior = s2c.center_rows_prior(rows, y)
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


def de_centered_sampler(bundle: dict[str, Any]) -> Callable:
    """Empirical L2 centered sampler for the A208-DE pre-check (packet §3).

    SAME frozen draw order as the S1 ``make_centered_sampler`` L2 branch
    (b~p_b; u1~g1[:,b]; u2~g2[u1,:,b]; zero-mass→delta-at-0) with the
    kernel's centered contract (true symbol to index 0 via XOR). Returns
    ``sampler(n, rng) -> (n, 32)`` row-normalized posteriors. RNG-only.
    """
    g1, g2, p_b = bundle["g1"], bundle["g2"], bundle["p_b"]
    _idx32 = np.arange(32, dtype=np.int64)

    def sampler(n: int, rng: np.random.Generator) -> np.ndarray:
        b = rng.choice(1024, size=int(n), p=p_b)
        out = np.empty((int(n), 32), dtype=np.float64)
        for i in range(int(n)):
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
            out[i] = row[_idx32 ^ u2t]
        return out

    return sampler


def leak_basis(arm: str) -> dict[str, Any]:
    """Frozen O1 f accounting (packet §6; per-arm m, single n=1024 code).

    (i) Layer-local reported efficiency: f_L2=(m·5)/(1024·H_L2)
    INFORMATIONAL ONLY — never gated.
    (ii) System budget mapping: f_super=(m·5+64)/(1024·H_full) BUDGET
    MAPPING, not measured efficiency; L1 unconstructed, GENIE-conditioned.
    A188: 1004/852.544≈1.177652 (headroom ~104.3 b). A208:
    1104/852.544≈1.294947 (headroom ~4.3 b — TIGHT).
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: A188|A208 only)")
    m = int(ARMS[arm]["m"])
    leak = float(m * 5 + 64)
    f_super = leak / CONTENT_BITS
    f_l2 = (5 * m) / (O1_N * H_L2_O1)
    blind_line = ("A208 blind risk: headroom ~4.3 b ⇒ any blind disclosure "
                  "fails gate (b) (O1 packet §6).") if arm == "A208" else (
        "A188 headroom ~104.3 b to the 1.3 bar (O1 packet §6).")
    return {
        "arm": arm,
        "m": m,
        "leak_bits": leak,
        "content_bits": CONTENT_BITS,
        "f_super_basis": f_super,
        "f_super_label": ("System budget mapping: "
                          "f_super=(m·5+64)/(1024·H_full) "
                          f"=({m}·5+64)/852.544≈{f_super:.6f} "
                          "(H_full=0.83256272). "
                          "BUDGET MAPPING, not measured efficiency; "
                          "L1 unconstructed, GENIE true-u1 "
                          "conditioning (O1 packet §6)"),
        "f_L2_basis": f_l2,
        "f_L2_label": ("Layer-local reported efficiency: "
                       f"f_L2=(m·5)/(1024·H_L2)=({m}·5)/(1024×0.80690067)"
                       f"≈{f_l2:.6f}. INFORMATIONAL ONLY — never gated "
                       "(O1 packet §6)"),
        "h_l2": H_L2_O1,
        "h_full": H_FULL_O1,
        "d_blind": D_BLIND,
        "d_blind_label": ("MEASURED zero: no blind/puncturing rounds exist "
                          "in the campaign path — NEVER assume zero "
                          "in a claim (O1 packet §6)"),
        "sensitivity": ("Δf = D_blind/852.544, i.e. each 16 bits "
                        "≈ +0.019"),
        "blind_risk": blind_line,
    }


def block_accounting_csv(rows: list[dict]) -> str:
    """Per-block accounting table (packet §9 deliverable)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["block", "seed", "exact_match", "status", "iterations",
                "wall_s", "d_blind", "leak_bits", "f_super"])
    for r in rows:
        if r.get("status") in ("error", "overrun"):
            w.writerow([r.get("block"), "", "", r.get("status"), "",
                        "", "", "", ""])
            continue
        w.writerow([r.get("block"), r.get("seed"), r.get("exact_match"),
                    r.get("status"), r.get("iterations"), r.get("wall_s"),
                    r.get("d_blind"), r.get("leak_bits"),
                    r.get("f_super")])
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
        refuse("root required (fresh additive workspace/o1_<uuid>)")
    parts = Path(root).parts
    if any(p in FORBIDDEN_ROOT_PARTS for p in parts):
        refuse(f"root under forbidden tree (results/outputs_comparison): {root}")


def _de_cover_record(arm: str, de_label: str | None) -> dict[str, Any]:
    label = de_label or "exploratory"
    if label not in DE_LABELS:
        refuse(f"unknown de-label {label} (frozen: covered|exploratory only)")
    note = ("A188 rate 0.81640625 is S1-identical "
            "(rho byte-identical {10:0.098,11:0.902}); NO new DE arm needed "
            "(O1 packet §2/scoping §3).") if arm == "A188" else (
        "A208 rho differs ({9:0.141,10:0.859}); A208-DE pre-check decides "
        "the cover label (O1 packet §3). Campaign proceeds regardless: "
        "pass → DE-covered secondary; fail/marginal → exploratory WITHOUT "
        "DE (gates unchanged).")
    return {"label": label,
            "label_source": ("explicit --de-label" if de_label
                             else "default 'exploratory' (no precheck "
                                   "required for the campaign run)"),
            "arm_note": note}


def _build_manifest(*, arm: str, construction: dict, rows: list[dict],
                    failures: int, blocks_completed: int, verdict: str,
                    partial: bool, next_block: int,
                    wall_windows: list[dict], ledger_decodes: int,
                    elapsed_s: float,
                    de_label: str | None) -> dict:
    basis = leak_basis(arm)
    spec = ARMS[arm]
    n = len(rows)
    fer = (failures / n) if n else None
    return {
        "arm": arm,
        "single_code": ("acceptance unit = ONE BLOCK = one n=1024 decode "
                        "with exact_match is True. No frames, no "
                        "group-of-4 rule (O1 packet §1; block≠S2c-group, "
                        "not directly comparable to S2c group FER)"),
        "construct": {
            "seed": construction.get("construct_seed"),
            "max_trials": construction.get("construct_trials"),
            "n": construction.get("n"),
            "m": construction.get("m"),
            "lambda": {str(k): float(v)
                       for k, v in spec["lambda"].items()},
            "four_cycles": construction.get("four_cycles"),
            "min_girth": construction.get("min_girth"),
            "rank": construction.get("rank"),
            "family": construction.get("family"),
            "pins": (f"fc=0/girth=8/rank-full asserted pre-run ({arm}; "
                     f"fixed constructor seed {O1_CONSTRUCT_SEED}; "
                     f"construct-twice-identical required; mismatch halts "
                     f"STOP-BLOCKED)"),
            "sockets_parity": {"sockets": construction.get("total_sockets"),
                               "parity": construction.get("parallel_edges")},
        },
        "seeds": {
            "policy": "literal-frozen (O1 packet §5; NOT derived)",
            "block_base": O1_BLOCK_BASE,
            "block_rule": "base+idx, idx=0..59 (block k → idx=k)",
            "stream": "common.v10_seed(f\"o1_blk:{seed}\") (paired across "
                      "arms; distinct domain from S2c s2c_emp:)",
            "absence": ("rg 2026-09-20: 20260955xx absent repo-wide "
                        "(outside consumed 2026096–98xx blocks and "
                        "20260920xx/70xx/72xx/75xx spots; Pre-EXECUTE "
                        "rg-absence re-check required)"),
        },
        "channel": {
            "source": SOURCE_DEFAULT,
            "bundle": "gamma_f03.npz keys 2M_gamma1_L1 (32,1024) + "
                      "2M_gamma2_L2condU1 (32,32,1024) + sidecar "
                      "gamma_f03_pb.npz key 2M_p_b (1024,) normalized "
                      "sum=1±1e-9 else refuse (read-only, never refit)",
            "sampler": ("per-symbol triple b~p_b; u1~g1[:,b]; u2~g2[u1,:,b]; "
                        "zero-mass→delta-at-0; frozen make_centered_sampler "
                        "L2 order; i.i.d. ×1024/block; Alice x=u2, "
                        "Bob 10-bit b"),
        },
        "budgets": {"wall_cap_s": WALL_CAP_S,
                    "per_decode_cap_s": PER_DECODE_CAP_S,
                    "rss_gib": RSS_CAP_GIB,
                    "max_blocks": N_BLOCKS, "max_decodes": N_BLOCKS},
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
            "l1_conditioning": ("GENIE true-u1 (D1 ceiling): O1 is a "
                                "genie-aided single-code upper bound, "
                                "never an L1/two-layer claim (O1 packet "
                                "§4/§9)"),
            "channel": "empirical 2M triple sampler at n=1024 (packet §4)",
        },
        "de_cover": _de_cover_record(arm, de_label),
        "ledger": {"decodes": ledger_decodes,
                   "blocks_completed": blocks_completed},
        "blocks_completed": blocks_completed,
        "failures": failures,
        "fer_blocks": fer,
        "pass_bar": f"block FER<=5% (fails/60<={PASS_MAX_FAILS})",
        "d_blind": basis["d_blind"],
        "d_blind_label": basis["d_blind_label"],
        "sensitivity": basis["sensitivity"],
        "blind_risk": basis["blind_risk"],
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
        "next_block": int(next_block),
        "resume": {"continuations_used": len(wall_windows) - 1,
                   "max_continuations": 1},
        "wall_windows": list(wall_windows),
        "elapsed_s": float(elapsed_s),
        "n_rows": n,
        "resume_policy_note": ("O1 packet §7: checkpoint-per-block + at "
                               "most ONE explicit wall-partial "
                               "--resume-from in a fresh window; terminal "
                               "FAIL/early-stop states never resume; no "
                               "auto-relaunch. A second resume refuses."),
        "verify": {
            "pins_ok": True,  # construct gate passed pre-run
            "ledger_ok": ledger_decodes == blocks_completed,
            "rows_ok": n == blocks_completed,
        },
    }


def _validate_partial(manifest: dict, rows: list, arm: str) -> dict:
    """Fail-closed partial validation BEFORE any decode (zero decodes on
    refuse). Checks: arm match, frozen seeds/budgets, ledger internal
    consistency (decodes == blocks, rows contiguous 0..k-1), no final
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
            or seeds.get("policy") != "literal-frozen (O1 packet §5; NOT derived)"
            or seeds.get("block_base") != O1_BLOCK_BASE):
        refuse("partial seeds mismatch frozen literal")
    if manifest.get("budgets", None) != {"wall_cap_s": WALL_CAP_S,
                                         "per_decode_cap_s": PER_DECODE_CAP_S,
                                         "rss_gib": RSS_CAP_GIB,
                                         "max_blocks": N_BLOCKS,
                                         "max_decodes": N_BLOCKS}:
        refuse("partial budgets mismatch frozen")
    if manifest.get("verdict") not in ("INCOMPLETE-wall",):
        refuse("partial carries a final/verdict state (nothing resumable; "
               "completion and FAIL states never resume)")
    blocks_completed = manifest.get("blocks_completed")
    failures = manifest.get("failures")
    ledger = manifest.get("ledger", {})
    try:
        k, f = int(blocks_completed), int(failures)
        ld = int(ledger.get("decodes"))
    except Exception:  # noqa: BLE001
        refuse("partial counts corrupt")
    if not 0 <= k < N_BLOCKS or not 0 <= f <= k or ld != k:
        refuse("partial ledger/blocks counts corrupt")
    if len(rows) != k:
        refuse(f"partial rows {len(rows)} != blocks_completed {k}")
    for i, r in enumerate(rows):
        if not isinstance(r, dict) or r.get("block") != i:
            refuse("partial blocks not contiguous 0..k-1")
    windows = manifest.get("wall_windows", None)
    if not isinstance(windows, list) or len(windows) != 1:
        refuse("partial wall_windows != exactly one window "
               "(continuation already used or corrupt)")
    try:
        float(windows[0].get("turn_start"))
        assert windows[0].get("cap") == WALL_CAP_S
    except Exception:  # noqa: BLE001
        refuse("partial wall window corrupt")
    return {"blocks_completed": k, "failures": f, "decodes": ld,
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
    """Pre-run construction gate (packet §2/E1): per-arm pin asserts
    (four_cycles=0, min_girth=8, rank=m) on the FIXED constructor (seed
    2026092001, trials 20), construct-twice-identical required; mismatch
    halts STOP-BLOCKED; unknown arm refuses (rc=2). ``construct_fn``
    convention is ``(arm, seed, max_trials)``, mirroring ``construct_arm``.
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: A188|A208 only)")
    seed = O1_CONSTRUCT_SEED
    trials = O1_MAX_TRIALS
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
    spec = ARMS[arm]
    try:
        fc = int(code_a.get("four_cycles"))
        girth = int(code_a.get("min_girth"))
        rank = int(code_a.get("rank"))
    except Exception:  # noqa: BLE001
        refuse(f"construction missing fc/girth/rank pins ({arm}; STOP-BLOCKED)")
    if fc != int(spec["four_cycles"]):
        refuse(f"{arm} four_cycles {fc} != {spec['four_cycles']} "
               f"(STOP-BLOCKED; O1 packet §2)")
    if girth != int(spec["min_girth"]):
        refuse(f"{arm} min_girth {girth} != {spec['min_girth']} "
               f"(STOP-BLOCKED; O1 packet §2)")
    if rank != int(spec["rank"]):
        refuse(f"{arm} rank {rank} != {spec['rank']} "
               f"(STOP-BLOCKED; O1 packet §2)")
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
            max_blocks: int | None = None,
            de_label: str | None = None) -> dict:
    """Run (or once-continue) the frozen 60-block campaign under ``root``.

    One arm per invocation; paired block seeds shared across arms.
    ``max_blocks`` is a PROBE-ONLY cap (timing integration; never a CLI
    flag, never part of any verdict). All writes stay under ``root``.
    Without an injected ``decode_fn``, ``bundle`` is required (no silent
    production bind — the CLI binds ``--gamma`` explicitly). The campaign
    run never requires the A208-DE precheck (``de_label`` defaults
    'exploratory' if absent).
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: A188|A208 only)")
    if de_label is not None and de_label not in DE_LABELS:
        refuse(f"unknown de-label {de_label} (frozen: covered|exploratory)")
    _check_root(root)
    m = int(ARMS[arm]["m"])
    construct_fn = construct_fn or construct_arm
    if decode_fn is None:
        if bundle is None:
            refuse("empirical bundle required (no silent production bind; "
                   "pass bundle or bind --gamma at the CLI)")
        _bundle = bundle

        def decode_fn(construction, seed, _b=_bundle):  # noqa: B023
            return decode_block_empirical(construction, seed, _b, O1_N, m)
    clock = clock or time.monotonic
    rss_fn = rss_fn or _default_rss
    writer = writer or default_writer
    if max_blocks is not None and (
            not isinstance(max_blocks, int) or max_blocks < 1):
        refuse("max_blocks (probe-only) must be a positive int")

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
        start_block = int(st["blocks_completed"])
    else:
        if os.path.exists(root):
            refuse(f"root not fresh: {root}")
        construction = _construct_gate(arm, construct_fn)
        rows = []
        failures = 0
        ledger_decodes = 0
        t_start = clock()
        wall_windows = [{"turn_start": float(t_start), "cap": WALL_CAP_S}]
        start_block = 0

    target = N_BLOCKS if max_blocks is None else min(max_blocks, N_BLOCKS)

    def _flush(verdict: str, partial: bool, next_block: int):
        mf = _build_manifest(
            arm=arm, construction=construction, rows=rows,
            failures=failures, blocks_completed=len(rows), verdict=verdict,
            partial=partial, next_block=next_block,
            wall_windows=wall_windows, ledger_decodes=ledger_decodes,
            elapsed_s=clock() - t_start, de_label=de_label)
        writer(root, {"manifest.json": json.dumps(mf, indent=1,
                                                  sort_keys=True, default=str),
                      "rows.json": json.dumps(rows, indent=1,
                                              sort_keys=True, default=str),
                      "block_accounting.csv": block_accounting_csv(rows)})
        return mf

    for k in range(start_block, target):
        # Wall check per block (fresh window per invocation).
        if clock() - t_start > WALL_CAP_S:
            return _flush("INCOMPLETE-wall", True, k)
        try:
            rss_gib = float(rss_fn()) / (1024 ** 3)
        except Exception:  # noqa: BLE001 — probe failure never halts
            rss_gib = 0.0
        if rss_gib >= RSS_CAP_GIB:
            return _flush("FAIL(budget)", True, k)
        seed = block_seed(arm, k)
        t0 = clock()
        try:
            out = decode_fn(construction, seed)
        except Exception as exc:  # noqa: BLE001 — no-retry: retain + halt
            rows.append({"block": k, "status": "error",
                         "error": f"{type(exc).__name__}: {exc}"})
            return _flush("FAIL(budget)", True, k)
        dt = clock() - t0
        if dt > PER_DECODE_CAP_S:
            rows.append({"block": k, "status": "overrun",
                         "decode_s": dt})
            return _flush("FAIL(budget)", True, k)
        ok = bool(out.get("exact_match") is True)
        if not ok:
            failures += 1
        ledger_decodes += 1
        basis = leak_basis(arm)
        rows.append({
            "block": k,
            "seed": seed,
            "exact_match": bool(out.get("exact_match", False)),
            "block_accept": ok,
            "block_fail": 0 if ok else 1,
            "status": out.get("status"),
            "converged": bool(out.get("reconstruction_ok", False)),
            "iterations": out.get("iterations"),
            "wall_s": dt,
            "d_blind": basis["d_blind"],
            "d_blind_label": basis["d_blind_label"],
            "leak_bits": basis["leak_bits"],
            "f_super": basis["f_super_basis"],
        })
        # Checkpoint per COMPLETED block (overwrite-in-place, single writer).
        _flush("INCOMPLETE-wall", True, k + 1)
        if failures > PASS_MAX_FAILS:
            # Early-stop: 4th block failure makes the bar unpassable.
            return _flush("FAIL-early-stop", True, k + 1)

    if max_blocks is not None:
        # Probe-only truncation: no verdict, no claim.
        return _flush("PROBE-truncated", True, target)
    basis = leak_basis(arm)
    passed = (failures <= PASS_MAX_FAILS
              and basis["f_super_basis"] <= F_SUPER_MAX)
    return _flush("PASS" if passed else "FAIL", False, N_BLOCKS)


def run_de_precheck(*, root: str, arm: str,
                    bundle: dict[str, Any] | None = None,
                    de_fn: Callable | None = None,
                    file_writer: Callable | None = None) -> dict:
    """Run the ONE single-point A208-DE pre-check (packet §3) and write the
    small ``de_precheck.json`` record into the arm root.

    Frozen call: ``run_mcde_posterior(q=32, λ={2:1},
    ρ=make_rho(0.796875))`` on the same empirical L2 bundle/sampler with
    the S1 CONFIRM n_samples/seed convention (``DE_PRECHECK``). A188
    refuses (no new DE arm needed there — rate-identical to S1). Refuses
    if ``de_precheck.json`` already exists (no silent overwrite). The
    campaign run never requires this record (label defaults
    'exploratory').
    """
    if arm != "A208":
        refuse(f"de-precheck is A208-only (frozen ρ=make_rho(0.796875)); "
               f"got arm {arm}")
    _check_root(root)
    if not root.startswith(ROOT_PREFIX):
        refuse(f"root must be fresh additive {ROOT_PREFIX}<uuid> "
               f"(got {root})")
    if bundle is None:
        refuse("empirical bundle required (no silent production bind; "
               "bind --gamma at the CLI)")
    lam = {2: 1.0}
    rho = _mcde.make_rho(DE_PRECHECK_RATE, lam)
    sampler = de_centered_sampler(bundle)
    cfg = dict(DE_PRECHECK)
    if de_fn is None:
        def de_fn(_sampler=sampler, _rho=dict(rho)):  # noqa: B023
            return _mcde.run_mcde_posterior(
                32, {2: 1.0}, _rho, channel_sampler=_sampler,
                n_samples=int(cfg["n_samples"]),
                max_iter=int(cfg["max_iter"]),
                seed=int(cfg["seed"]),
                entropy_tol_bits=float(cfg["tol"]),
                streak=int(cfg["streak"]))
    try:
        res = de_fn(sampler)
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed, no partial write
        refuse(f"de-precheck failed: {type(exc).__name__}: {exc}")
    record = {
        "mode": "o1-a208-de-precheck",
        "arm": arm,
        "q": 32,
        "lambda": {"2": 1.0},
        "rho": {str(k): float(v) for k, v in rho.items()},
        "rate": DE_PRECHECK_RATE,
        "n_samples": int(cfg["n_samples"]),
        "max_iter": int(cfg["max_iter"]),
        "entropy_tol_bits": float(cfg["tol"]),
        "streak": int(cfg["streak"]),
        "seed": int(cfg["seed"]),
        "seed_convention": ("S1 CONFIRM (n_samples=16000/max_iter=100/"
                            "tol=1e-4/streak=20) + first CONFIRM seed "
                            "2026094951 (v80_s1_mcde_runner)"),
        "source": bundle.get("source", SOURCE_DEFAULT),
        "channel": ("same empirical L2 bundle/sampler as S1 "
                    "(gamma_f03.npz + p_b sidecar; L2 draw order)"),
        "converged": bool(res.get("converged", False)),
        "iterations": res.get("iterations"),
        "final_entropy_bits": res.get("final_entropy_bits"),
        "entropy_trace_len": (len(res["entropy_trace_bits"])
                              if isinstance(res.get("entropy_trace_bits"),
                                            list) else None),
        "cover_hint": ("DE-covered secondary" if res.get("converged")
                       else "exploratory WITHOUT DE (gates unchanged)"),
    }
    blob = json.dumps(record, indent=1, sort_keys=True, default=str)
    target = os.path.join(root, "de_precheck.json")
    if os.path.exists(target):
        refuse(f"de-precheck record already exists: {target}")
    if file_writer is None:
        os.makedirs(root, exist_ok=True)
        with open(target, "w") as fh:
            fh.write(blob)
    else:
        file_writer(target, blob)
    return record


def run_execution(root: str, arm: str,
                  resume_from: str | None = None,
                  gamma: str = GAMMA_DEFAULT,
                  source: str = SOURCE_DEFAULT,
                  bundle: dict[str, Any] | None = None,
                  de_label: str | None = None) -> int:
    bound = bundle if bundle is not None else s2c.bind_empirical_bundle(
        gamma, source)
    manifest = execute(root=root, arm=arm, bundle=bound,
                       resume_from=resume_from, de_label=de_label)
    print(json.dumps({"arm": manifest["arm"],
                      "verdict": manifest["verdict"],
                      "failures": manifest["failures"],
                      "fer_blocks": manifest["fer_blocks"],
                      "f_super": manifest["f_super"],
                      "de_cover": manifest["de_cover"],
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
    ap.add_argument("--de-precheck", action="store_true", default=False)
    ap.add_argument("--de-label", default="")
    args = ap.parse_args(argv)
    # Dual-flag gate: refuse EVERYTHING else rc=2 BEFORE any root/contact.
    # There is no profile-only mode and no silent path.
    if not args.execute_real:
        refuse("refusing: --execute-real missing (rc2 pre-anything)")
    if not args.execution_authorized:
        refuse("refusing: --execution-authorized missing (rc2 pre-anything)")
    if args.arm not in ARMS:
        refuse(f"unknown arm {args.arm} (frozen: A188|A208 only)")
    if args.de_label and args.de_label not in DE_LABELS:
        refuse(f"unknown de-label {args.de_label} (frozen: covered|exploratory)")
    if args.resume_from and args.root and args.root != args.resume_from:
        refuse("root/resume-from mismatch (fail closed)")
    root = args.resume_from or args.root
    if not root:
        refuse("root required (fresh additive workspace/o1_<uuid>)")
    if not root.startswith(ROOT_PREFIX):
        refuse(f"root must be fresh additive {ROOT_PREFIX}<uuid> "
               f"(got {root})")
    if args.de_precheck:
        if args.resume_from:
            refuse("de-precheck takes no --resume-from (fail closed)")
        bound = s2c.bind_empirical_bundle(args.gamma, args.source)
        rec = run_de_precheck(root=root, arm=args.arm, bundle=bound)
        print(json.dumps({"arm": rec["arm"], "mode": rec["mode"],
                          "converged": rec["converged"],
                          "iterations": rec["iterations"],
                          "cover_hint": rec["cover_hint"],
                          "root": root}, indent=1, sort_keys=True,
                         default=str))
        return 0
    return run_execution(root=root, arm=args.arm,
                         resume_from=args.resume_from or None,
                         gamma=args.gamma, source=args.source,
                         bundle=None,
                         de_label=args.de_label or None)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
