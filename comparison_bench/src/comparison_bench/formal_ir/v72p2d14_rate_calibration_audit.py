"""D14 Phase R — no-decoder rate-calibration audit (EXPLORE, synthetic only).

One small additive module. It reads ONLY the accepted CAL-only Model-F
artifact plus the frozen D11/D12 synthetic decoder records, recomputes
generator entropy / CE row arithmetic / per-block self-information with the
accepted helpers, and persists CSV/JSON + report.md to a fresh additive root.
Zero decoder calls, zero new random blocks, zero seed search, no VAL/real/raw
reads, no overwrite (fresh-root refusal).

Import map (reuse — never copy — of accepted D8–D12 input/sampling helpers):

- ``comparison_bench.formal_ir.v72p2d5_model_f_input.load_model_f_input``
  (CAL-only counts/P(B) loader, read-only);
- ``comparison_bench.formal_ir.v72p2d5_gf32_rate_mother``: accepted estimator
  ``prepare_model_f_prior_candidate`` (+ ``build_f_model_concentration`` via
  that chain), layer maps ``marginalize_f_to_p1`` / ``conditionalize_f_to_p2``,
  matched sampler ``sample_matched_block``, symbol split ``symbols_to_layers``,
  entropy math ``_ce_stats``, row math ``_rows_required``, and the frozen
  constants ``LAMBDA_STAR/Q/AUDIT_FLOOR`` + ``CE_L1_MEAN/CE_L2_ORACLE_MEAN/
  CE_JOINT_MEAN`` + ``P0_WIDTH/G1_WIDTH/G2_WIDTH/P0_F/G1_F/G2_F`` +
  ``MODEL_F_INPUT_FORMAL_ROOT``. Rejected ``build_f_model`` is imported ONLY
  for the (f) legacy-CE diagnostic column (labeled, never the generator);
- ``comparison_bench.formal_ir.v72p2d12_finite_l1_degree``: frozen D12
  ``BLOCK_SEEDS/D12_WIDTHS/D12_BATCH_ID`` (block identities only);
- ``comparison_bench.formal_ir.v72p2d11_forward_app``: frozen D11
  ``L1_BLOCK_SEEDS/D11_WIDTHS/D11_BATCH_ID`` (block identities only).

Claimed numbers under test (L1/L2 entropy, effective factors) are NOT
constants here: they enter ``run_audit`` via the ``hypotheses`` argument
(runner CLI flags) and are recorded as hypotheses under test.
"""

from __future__ import annotations

import csv
import json
import math
import time
from pathlib import Path

from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5
from comparison_bench.formal_ir import v72p2d5_model_f_input as model_f_in
from comparison_bench.formal_ir import v72p2d11_forward_app as d11
from comparison_bench.formal_ir import v72p2d12_finite_l1_degree as d12

__all__ = [
    "ACCEPTED_MODEL_F_ROOT", "ALLOWED_RECORD_ROOTS", "FROZEN_AUDIT_ROOT",
    "BITS_PER_SYMBOL", "ESTIMATOR_IDENTITY", "DECODER_CALLS",
    "refuse_unless_accepted_input", "refuse_fresh_out_root",
    "generator_entropy", "legacy_ce_diagnostic", "rate_row_record",
    "block_self_info", "read_decoder_records", "expand_cell_pairs",
    "quantile_summary", "run_audit",
]

#: The single accepted CAL-only input root (relative to the repo root).
ACCEPTED_MODEL_F_ROOT = d5.MODEL_F_INPUT_FORMAL_ROOT
#: Frozen audit output root (relative to the repo root; created once, never
#: overwritten).
FROZEN_AUDIT_ROOT = "workspace/v72p2d14_rate_audit/20260914_r1"
#: Immutable synthetic record roots this audit may read (D11 + D12 only).
ALLOWED_RECORD_ROOTS = {
    "d12": "workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450",
    "d11": "workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64",
}
#: Roots that must never be created, overwritten, or read as input here.
PROTECTED_PREFIXES = (
    "results/",
    "comparison_bench/outputs_comparison/",
    "workspace/v72p2d5_g2/",
    "workspace/v72p2d5_model_f_input/",
)
#: Bits per GF(32) syndrome symbol on the wire.
BITS_PER_SYMBOL = int(math.log2(d5.Q))
#: Identity of the generator estimator under audit.
ESTIMATOR_IDENTITY = (
    "prepare_model_f_prior_candidate/build_f_model_concentration "
    "(total per-Bob-column concentration LAMBDA_STAR=%.16f)" % d5.LAMBDA_STAR
)
#: This audit binds no decoder; the counter stays zero by construction.
DECODER_CALLS = 0


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _resolve(repo: Path, rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else repo / rel


def refuse_unless_accepted_input(model_f_root: str) -> Path:
    """Return the resolved input dir, refusing anything but the accepted root."""
    repo = _repo_root()
    got = _resolve(repo, model_f_root).resolve()
    want = _resolve(repo, ACCEPTED_MODEL_F_ROOT).resolve()
    if got != want:
        raise ValueError(
            "refusing non-accepted Model-F input root: %r (accepted: %r)"
            % (model_f_root, ACCEPTED_MODEL_F_ROOT)
        )
    return got


def refuse_unless_allowed_records(root: str, which: str) -> Path:
    """Return the resolved record dir, refusing anything but the frozen root."""
    repo = _repo_root()
    got = _resolve(repo, root).resolve()
    want = _resolve(repo, ALLOWED_RECORD_ROOTS[which]).resolve()
    if got != want:
        raise ValueError(
            "refusing non-allowlisted %s record root: %r" % (which, root)
        )
    return got


def refuse_fresh_out_root(out_root: str) -> Path:
    """Return the resolved output dir, refusing overwrite/protected roots."""
    repo = _repo_root()
    rel = str(out_root)
    for prefix in PROTECTED_PREFIXES:
        if rel == prefix.rstrip("/") or rel.startswith(prefix):
            raise ValueError("refusing protected output root: %r" % rel)
    for key, allowed in ALLOWED_RECORD_ROOTS.items():
        if rel == allowed or rel.startswith(allowed + "/"):
            raise ValueError(
                "refusing output inside frozen %s record root: %r" % (key, rel)
            )
    if rel == ACCEPTED_MODEL_F_ROOT or rel.startswith(ACCEPTED_MODEL_F_ROOT + "/"):
        raise ValueError("refusing output inside accepted input root: %r" % rel)
    resolved = _resolve(repo, rel)
    if resolved.exists():
        raise FileExistsError("refusing to overwrite existing root: %s" % resolved)
    return resolved


def generator_entropy(counts_ab, p_b) -> dict:
    """Expected generator entropies (bits/symbol) under the accepted chain.

    Equation (floor-then-log, NO renormalization — same convention as the
    accepted ``_ce_stats`` helper): with ``pf`` the candidate ``P_F(A|B)``
    table on axes ``(Alice=1024, Bob=1024)`` and ``pb = P(B)``,

    - ``H_joint = H(A|B) = -sum_b pb[b] sum_a pf*log2(pf)``,
    - ``H_L1 = H(U1|B)`` on ``p1 = marginalize_f_to_p1(pf)`` with
      ``A = 32*U1 + U2``,
    - ``H_L2 = H(U2|U1,B)`` on ``p2 = conditionalize_f_to_p2(pf)``
      weighted by ``pb[b]*p1[u1|b]``,

    where ``pf* = max(pf, AUDIT_FLOOR=1e-300)`` elementwise before ``log2``.
    Units: bits. Returns ``{joint, l1, l2}`` plus the estimator identity.
    """
    import numpy as np

    counts = np.asarray(counts_ab, dtype=np.float64)
    pb = np.asarray(p_b, dtype=np.float64).ravel()
    pb, pf = d5.prepare_model_f_prior_candidate(counts, pb / pb.sum())
    joint, l1, l2, _, _ = d5._ce_stats(pf, pb)
    return {
        "joint": float(joint), "l1": float(l1), "l2": float(l2),
        "units": "bits_per_symbol",
        "floor": "max(p, %.0e) elementwise before log2, no renormalization"
        % d5.AUDIT_FLOOR,
        "axes": "p_f(Alice=1024, Bob=1024); p_b(Bob=1024); A=32*U1+U2",
        "estimator": ESTIMATOR_IDENTITY,
    }


def legacy_ce_diagnostic(counts_ab, p_b) -> dict:
    """Same ``_ce_stats`` math on the REJECTED per-cell chain (diagnostic).

    Labeled diagnostic for the (f) mismatch-cause analysis only: this is NOT
    the generator (D10/D11/D12 blocks were drawn from the candidate chain).
    """
    import numpy as np

    counts = np.asarray(counts_ab, dtype=np.float64)
    pb = np.asarray(p_b, dtype=np.float64).ravel()
    pb = pb / pb.sum()
    pf = d5.build_f_model(counts, d5.LAMBDA_STAR)
    joint, l1, l2, _, _ = d5._ce_stats(pf, pb)
    return {"joint": float(joint), "l1": float(l1), "l2": float(l2),
            "units": "bits_per_symbol",
            "estimator": "REJECTED build_f_model (per-cell lam) — diagnostic only"}


def rate_row_record(stage: str, layer: str, ce_const: float,
                    ce_provenance: str, h_actual: float, n: int,
                    f: float) -> dict:
    """One frozen (layer, n, f) row: rows/disclosed/load/factors.

    ``rows = ceil(n*CE*f/5)`` (accepted ``_rows_required``); disclosed bits
    ``= rows*5``; generator entropy load ``= n*H_actual``; nominal factor
    ``= disclosed/(n*CE)``; effective factor ``= disclosed/(n*H_actual)``.
    Neither factor is labeled sufficient for decoding (see report §e).
    """
    rows = d5._rows_required(ce_const, n, f)
    disclosed = rows * BITS_PER_SYMBOL
    return {
        "stage": stage, "layer": layer, "n": int(n), "f": float(f),
        "ce_const": float(ce_const), "ce_provenance": ce_provenance,
        "h_actual": float(h_actual),
        "rows": int(rows), "disclosed_bits": int(disclosed),
        "entropy_load_bits": float(n * h_actual),
        "nominal_factor": float(disclosed / (n * ce_const)),
        "effective_factor": float(disclosed / (n * h_actual)),
    }


def block_self_info(p_b, p_f, width: int, block_seed: int) -> dict:
    """Self-information (bits) of one frozen block identity.

    The block is deterministically reconstructed with the accepted
    ``sample_matched_block`` from its FROZEN seed — the identical block the
    D11/D12 batches used, never a new random block. With ``(b, a, u1, u2)``
    per position and ``pf* = max(p, AUDIT_FLOOR)`` (no renormalization):

    - ``I_full = sum -log2(pb[b]) - log2(pf[a|b])``,
    - ``I_L1 = sum -log2(pb[b]) - log2(p1[u1|b])``,
    - ``I_L2_cond = sum -log2(p2[u2|u1,b])``.
    """
    import numpy as np

    pb = np.asarray(p_b, dtype=np.float64).ravel()
    pf = np.asarray(p_f, dtype=np.float64)
    p1 = d5.marginalize_f_to_p1(pf)
    p2 = d5.conditionalize_f_to_p2(pf)
    blk = d5.sample_matched_block(pb, pf, int(width), int(block_seed))
    bob = np.asarray(blk["bob"], dtype=np.int64)
    alice = np.asarray(blk["alice"], dtype=np.int64)
    u1, u2 = d5.symbols_to_layers(alice)
    fl = float(d5.AUDIT_FLOOR)

    def _nlog2(x):
        return -float(np.log2(max(float(x), fl)))

    i_full = sum(_nlog2(pb[int(b)]) + _nlog2(pf[int(a), int(b)])
                 for b, a in zip(bob, alice))
    i_l1 = sum(_nlog2(pb[int(b)]) + _nlog2(p1[int(v), int(b)])
               for b, v in zip(bob, u1))
    i_l2 = sum(_nlog2(p2[int(v), int(b), int(w)])
               for b, v, w in zip(bob, u1, u2))
    return {"width": int(width), "block_seed": int(block_seed),
            "n": int(width), "i_full_bits": float(i_full),
            "i_l1_bits": float(i_l1), "i_l2_cond_bits": float(i_l2)}


def read_decoder_records(root: Path) -> list:
    """Read-only load of a frozen ``decoder_records.csv``."""
    with open(str(Path(root) / "decoder_records.csv"), newline="",
              encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _is_true(value) -> bool:
    return str(value) == "True"


def expand_cell_pairs(x: float, n_calls: int, n_exact: int) -> list:
    """One (x, y01) pair per actual call in a joined outcome cell.

    Multiplicity is the stored call count — never the block length.
    """
    n_calls, n_exact = int(n_calls), int(n_exact)
    if not 0 <= n_exact <= n_calls:
        raise ValueError("exact count outside [0, n_calls]")
    return [(float(x), 0)] * (n_calls - n_exact) + [(float(x), 1)] * n_exact


def quantile_summary(pairs: list, n_bins: int = 3) -> dict:
    """Tercile-binned success counts + Pearson r (descriptive diagnostics).

    ``pairs`` is ``[(x_float, y_01_int)]``. Bins split the x-sorted order
    into ``n_bins`` contiguous chunks (no threshold tuning). Correlation is
    descriptive only — never a sufficiency claim.
    """
    import numpy as np

    xs = np.asarray([float(x) for x, _ in pairs], dtype=np.float64)
    ys = np.asarray([int(y) for _, y in pairs], dtype=np.float64)
    order = np.argsort(xs, kind="stable")
    chunks = np.array_split(order, n_bins)
    bins = []
    for chunk in chunks:
        sel_y = ys[np.asarray(chunk)]
        bins.append({
            "n": int(sel_y.size),
            "success": int(sel_y.sum()),
            "rate": float(sel_y.mean()) if sel_y.size else 0.0,
            "x_min": float(xs[np.asarray(chunk)].min()),
            "x_max": float(xs[np.asarray(chunk)].max()),
        })
    if xs.size > 2 and float(xs.std()) > 0 and float(ys.std()) > 0:
        r = float(np.corrcoef(xs, ys)[0, 1])
    else:
        r = 0.0
    return {"bins": bins, "pearson_r": r, "n": int(xs.size)}


def _snapshot(root: Path) -> list:
    return sorted(
        ({"name": p.name, "bytes": p.stat().st_size,
          "mtime_ns": p.stat().st_mtime_ns}
         for p in Path(root).iterdir()),
        key=lambda d: d["name"],
    )


def _write_csv(path: Path, rows: list, columns: list) -> None:
    with open(str(path), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns)
        w.writeheader()
        for row in rows:
            w.writerow({c: row.get(c, "") for c in columns})


def run_audit(model_f_root: str, d12_root: str, d11_root: str, out_root: str,
              hypotheses: dict, command: str = "") -> dict:
    """Run the full no-decoder audit once into a fresh root. Returns manifest."""
    import numpy as np

    t0 = time.perf_counter()
    in_dir = refuse_unless_accepted_input(model_f_root)
    r12 = refuse_unless_allowed_records(d12_root, "d12")
    r11 = refuse_unless_allowed_records(d11_root, "d11")
    out = refuse_fresh_out_root(out_root)
    snap_in = _snapshot(in_dir)
    snap12 = _snapshot(r12)
    snap11 = _snapshot(r11)

    loaded = model_f_in.load_model_f_input(str(in_dir))
    counts, pb0 = loaded["counts_ab"], loaded["p_b"]
    ent = generator_entropy(counts, pb0)
    legacy = legacy_ce_diagnostic(counts, pb0)
    pb, pf = d5.prepare_model_f_prior_candidate(
        np.asarray(counts, dtype=np.float64),
        np.asarray(pb0, dtype=np.float64).ravel())
    pb = pb / pb.sum()

    # (b) frozen CE row tables: P0/G1 n=64, G2 n=256.
    ce_l1, ce_l2 = d5.CE_L1_MEAN, d5.CE_L2_ORACLE_MEAN
    prov = ("D4 frozen CE (D4R2 audit outer-F TEST means; "
            "G1_WIDE_ATTRIBUTION_R2.md provenance table)")
    row_recs = []
    for stage, n, fs in (("P0", d5.P0_WIDTH, d5.P0_F),
                         ("G1", d5.G1_WIDTH, d5.G1_F)):
        for f in fs:
            row_recs.append(rate_row_record(stage, "L1", ce_l1, prov,
                                            ent["l1"], n, f))
            row_recs.append(rate_row_record(stage, "L2", ce_l2, prov,
                                            ent["l2"], n, f))
    for f in d5.G2_F:
        row_recs.append(rate_row_record("G2", "L1", ce_l1, prov, ent["l1"],
                                        d5.G2_WIDTH, f))
        row_recs.append(rate_row_record("G2", "L2", ce_l2, prov, ent["l2"],
                                        d5.G2_WIDTH, f))

    # (c) per-block self-information joined to stored outcomes.
    rec12 = read_decoder_records(r12)
    rec11 = read_decoder_records(r11)
    info_cache: dict = {}

    def _info(width, seed):
        key = (int(width), int(seed))
        if key not in info_cache:
            info_cache[key] = block_self_info(pb, pf, *key)
        return info_cache[key]

    by12: dict = {}
    for r in rec12:
        key = (int(r["width"]), int(r["block_seed"]))
        cell = by12.setdefault(key, {"records": []})
        cell["records"].append(r)
    blk12_rows = []
    for (width, seed), cell in sorted(by12.items()):
        info = _info(width, seed)
        recs = cell["records"]
        exact = sum(1 for r in recs if _is_true(r["exact"]))
        syn = sum(1 for r in recs if _is_true(r["syndrome_ok"]))
        und = sum(1 for r in recs
                  if _is_true(r["syndrome_ok"]) and not _is_true(r["exact"]))
        arms = sorted(set(r["arm"] for r in recs))
        blk12_rows.append({
            "width": width, "block_seed": seed, "arms": "+".join(arms),
            "n_calls": len(recs), "exact": exact, "syndrome_ok": syn,
            "undetected": und, **{k: info[k] for k in
                                  ("n", "i_full_bits", "i_l1_bits",
                                   "i_l2_cond_bits")},
        })

    by11: dict = {}
    for r in rec11:
        key = (int(r["width"]), int(r["block_seed"]))
        cell = by11.setdefault(key, {"records": []})
        cell["records"].append(r)
    blk11_rows = []
    for (width, seed), cell in sorted(by11.items()):
        info = _info(width, seed)
        recs = cell["records"]
        per_bl: dict = {}
        for r in recs:
            k = (r["branch"], r["layer"])
            c = per_bl.setdefault(k, {"n": 0, "exact": 0, "syndrome_ok": 0,
                                      "undetected": 0})
            c["n"] += 1
            c["exact"] += _is_true(r["exact"])
            c["syndrome_ok"] += _is_true(r["syndrome_ok"])
            c["undetected"] += (_is_true(r["syndrome_ok"])
                                and not _is_true(r["exact"]))
        for (branch, layer), c in sorted(per_bl.items()):
            blk11_rows.append({
                "width": width, "block_seed": seed, "branch": branch,
                "layer": layer, "n_symbols": info["n"],
                "n_calls": c["n"], "exact": c["exact"],
                "syndrome_ok": c["syndrome_ok"],
                "undetected": c["undetected"],
                **{k: info[k] for k in ("i_full_bits", "i_l1_bits",
                                        "i_l2_cond_bits")},
            })

    # (d) quantile diagnostics (descriptive only; D12 binned per width so
    # block length never confounds load bins).
    q12 = {}
    for width in sorted(set(row["width"] for row in blk12_rows)):
        pairs = []
        for row in blk12_rows:
            if row["width"] == width:
                key = (row["width"], row["block_seed"])
                pairs.extend([(row["i_l1_bits"], int(_is_true(r["exact"])))
                              for r in by12[key]["records"]])
        q12["n%d" % width] = quantile_summary(pairs)
    q11 = {}
    for (branch, layer) in sorted(set((r["branch"], r["layer"]) for r in rec11)):
        pairs = []
        for row in blk11_rows:
            if row["branch"] == branch and row["layer"] == layer:
                x = row["i_l2_cond_bits"] if layer == "L2" else row["i_l1_bits"]
                pairs.extend(expand_cell_pairs(x, row["n_calls"],
                                               row["exact"]))
        q11["%s/%s" % (branch, layer)] = quantile_summary(pairs)

    # (f) hypothesis cross-check (hypotheses are inputs, never constants).
    hyp_l1 = float(hypotheses["h_l1"])
    hyp_l2 = float(hypotheses["h_l2"])
    hyp_factors = [float(v) for v in hypotheses["factors"]]
    eff_l1_f = {(r["n"], r["f"]): r["effective_factor"] for r in row_recs
                if r["layer"] == "L1"}
    cross = {
        "hypotheses_as_tested": {"h_l1": hyp_l1, "h_l2": hyp_l2,
                                 "factors": hyp_factors},
        "reproduced": {"h_l1": ent["l1"], "h_l2": ent["l2"],
                       "joint": ent["joint"]},
        "legacy_diagnostic": legacy,
        "delta_l1": ent["l1"] - hyp_l1,
        "delta_l2": ent["l2"] - hyp_l2,
        "effective_factors_l1": {"n%d_f%s" % k: v for k, v in eff_l1_f.items()},
    }

    wall_s = time.perf_counter() - t0
    try:
        import resource

        peak_rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
    except Exception:
        peak_rss = None

    out.mkdir(parents=True, exist_ok=False)
    with open(str(out / "entropy.json"), "w", encoding="utf-8") as fh:
        json.dump({"generator": ent, "legacy_diagnostic": legacy,
                   "ce_frozen": {"ce_l1": ce_l1, "ce_l2_oracle": ce_l2,
                                 "ce_joint": d5.CE_JOINT_MEAN,
                                 "provenance": prov}}, fh, indent=2,
                  sort_keys=True)
        fh.write("\n")
    _write_csv(out / "rate_rows.csv", row_recs,
               ["stage", "layer", "n", "f", "ce_const", "ce_provenance",
                "h_actual", "rows", "disclosed_bits", "entropy_load_bits",
                "nominal_factor", "effective_factor"])
    _write_csv(out / "per_block_d12.csv", blk12_rows,
               ["width", "block_seed", "arms", "n_calls", "exact",
                "syndrome_ok", "undetected", "n", "i_full_bits",
                "i_l1_bits", "i_l2_cond_bits"])
    _write_csv(out / "per_block_d11.csv", blk11_rows,
               ["width", "block_seed", "branch", "layer", "n_symbols",
                "n_calls", "exact", "syndrome_ok", "undetected",
                "i_full_bits", "i_l1_bits", "i_l2_cond_bits"])
    q12_rows = []
    for key, q in q12.items():
        for i, b in enumerate(q["bins"]):
            q12_rows.append({"group": key, "bin": i, **b,
                             "pearson_r": q["pearson_r"]})
    _write_csv(out / "quantile_d12.csv", q12_rows,
               ["group", "bin", "n", "success", "rate", "x_min", "x_max",
                "pearson_r"])
    q11_rows = []
    for key, q in q11.items():
        for i, b in enumerate(q["bins"]):
            q11_rows.append({"group": key, "bin": i, **b,
                             "pearson_r": q["pearson_r"]})
    _write_csv(out / "quantile_d11.csv", q11_rows,
               ["group", "bin", "n", "success", "rate", "x_min", "x_max",
                "pearson_r"])
    with open(str(out / "crosscheck.json"), "w", encoding="utf-8") as fh:
        json.dump(cross, fh, indent=2, sort_keys=True)
        fh.write("\n")

    und12 = sum(r["undetected"] for r in blk12_rows)
    und11 = sum(r["undetected"] for r in (b for b in blk11_rows))
    lines = [
        "# D14 Phase R — rate-calibration audit (no-decoder, synthetic)",
        "",
        "Estimator: %s" % ESTIMATOR_IDENTITY,
        ("Entropy (bits/symbol, floor-then-log max(p,1e-300) no renorm; "
         "axes p_f(Alice=1024,Bob=1024), A=32*U1+U2):"),
        ("- H_joint=%.6f H_L1=%.6f H_L2=%.6f" % (
            ent["joint"], ent["l1"], ent["l2"])),
        ("- legacy per-cell diagnostic: joint=%.6f L1=%.6f L2=%.6f "
         "(rejected chain; cause-analysis only)" % (
             legacy["joint"], legacy["l1"], legacy["l2"])),
        ("- frozen CE constants: L1=%.6f L2=%.6f joint=%.6f (%s)" % (
            ce_l1, ce_l2, d5.CE_JOINT_MEAN, prov)),
        ("- hypotheses as tested: H_L1=%r H_L2=%r factors=%r" % (
            hyp_l1, hyp_l2, hyp_factors)),
        ("- reproduced deltas: dL1=%+.6f dL2=%+.6f; effective L1 factors "
         "(n,f): %s" % (cross["delta_l1"], cross["delta_l2"],
                        ", ".join("%.4f" % v for v in eff_l1_f.values()))),
        "",
        ("Per-block: %d D12 identities (%d calls, %d exact, %d undetected kept "
         "isolated), %d D11 rows (%d calls, %d undetected kept isolated)."
         % (len(blk12_rows), len(rec12),
            sum(r["exact"] for r in blk12_rows), und12, len(blk11_rows),
            len(rec11), und11)),
        ("Quantiles (descriptive only): D12 I_L1 per-width terciles %s; D11 "
         "per-branch/layer terciles in quantile_d11.csv."
         % "; ".join("%s r=%.3f" % (k, q["pearson_r"])
                     for k, q in sorted(q12.items()))),
        "",
        ("(e) Load-vs-success separation: expected information load "
         "(n*H, per-block I) describes the generator, not the finite code. "
         "`I <= disclosed bits` is NECESSARY-SHAPED but NEVER sufficient for "
         "decoding: finite-length structure, degree profile, and decoder "
         "dynamics decide success. No success is claimed from load alone."),
        "",
        ("Run: wall=%.1fs peak_rss=%s decoder_calls=0 new_blocks=0 "
         "seed_search=0; inputs %s + D11/D12 roots read-only; ceiling "
         "3600s/2GiB respected." % (
             wall_s, peak_rss,
             ACCEPTED_MODEL_F_ROOT)),
        "Claim ceiling: synthetic diagnostic only; no FER/SKR/qualification.",
    ]
    with open(str(out / "report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    manifest = {
        "change": "v72p2d14-scientific-validity-reset", "phase": "R",
        "track": "EXPLORE", "command": command,
        "inputs": {"model_f_root": ACCEPTED_MODEL_F_ROOT,
                   "snapshot": snap_in,
                   "d12_root": ALLOWED_RECORD_ROOTS["d12"],
                   "d12_snapshot": snap12, "d12_records": len(rec12),
                   "d11_root": ALLOWED_RECORD_ROOTS["d11"],
                   "d11_snapshot": snap11, "d11_records": len(rec11)},
        "hypotheses_as_tested": {"h_l1": hyp_l1, "h_l2": hyp_l2,
                                 "factors": hyp_factors},
        "outputs": sorted(p.name for p in out.iterdir()),
        "decoder_calls": DECODER_CALLS, "new_blocks": 0, "seed_search": 0,
        "val_real_raw_reads": 0,
        "wall_s": wall_s, "peak_rss_bytes": peak_rss,
        "ceilings": {"wall_s": 3600, "rss_bytes": 2 * 1024 ** 3},
    }
    with open(str(out / "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    manifest["outputs"] = sorted(p.name for p in out.iterdir())
    return manifest
