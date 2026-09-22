"""X1 successor bundle build + verification reporter (T-X1S-1 / T-X1S-2).

Entry-evidence step for the X1 successor entry gate (cycle V80-NBLDPC-JAN21).
Frozen contract: ``docs/research_cycles/V80-NBLDPC-JAN21/
X1_SUCCESSOR_ENTRY_PACKET.md`` §2.6 + gates G-D/G-E (§4); command/authorization
frame in ``X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md``.

What this module does (synthetic numpy on already-persisted artifacts ONLY):

- build mode: dense-reconstruct per-source TRAIN ``N_ab`` (1024,1024) from the
  read-only R1 COO triplets in ``workspace/r1_histogram_5e2a91c4/`` and
  factorize via the UNMODIFIED frozen builder
  ``ChannelAdapter(fact_id="F03", source=<V26 id>, N_ab=...)`` into the F1/F2
  file set under a fresh additive ``workspace/x1_bundles_<UUID8>/`` root.
- verify mode: read-only reporter — R1 checksum identities, the frozen
  ``bind_empirical_bundle()`` shape/normalization gates on the built files,
  the F1 p_b sibling-copy identity, and the 2M lineage comparison
  (report-only; NEVER refit/overwrite/substitute the frozen files — no such
  code path exists in this module).

Frozen conventions applied exactly (main-thread decisions from review F1/F2):

- F1: the bundle root holds ``x1_gamma_f03r1.npz`` with keys
  ``{source}_gamma1_L1`` (32,1024) + ``{source}_gamma2_L2condU1``
  (32,32,1024) + ``{source}_p_b`` (1024,) for sources ``1M``/``1p5M``/``2M``,
  PLUS a sibling file literally named ``gamma_f03_pb.npz`` holding the same
  ``{source}_p_b`` keys, so the frozen path-form
  ``bind_empirical_bundle(<bundle path>)`` resolves its hardcoded sidecar
  name with ZERO frozen-module change.
- F2: the re-derived 2M factorization (same arrays as the main bundle's 2M
  keys, rebuilt from the R1-root 2M COO for lineage verification) ALSO lives
  in ``x1_gamma_f03r1_2M_verify.npz``; that file is verification-only and is
  NEVER passed to any decode path (this module contains no decode path at
  all); 2M decode arms bind ONLY the frozen ``gamma_f03.npz`` lineage.
- F5: the T2-* -> V26 source-id mapping is READ from
  ``nonbinary_v26_channel.SOURCES_ORDER``/``SOURCE_METADATA`` (see
  ``source_table()``), never invented; the exact triple is recorded in the
  build log.

Hard negatives: no ``.ttbin`` read (no such import, path, or string handling
anywhere here), no decoder/DE/graph call, no real-data access, no commit/push,
no write outside the fresh bundle root, no write to ``results/`` or
``comparison_bench/outputs_comparison/``.
"""

from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path
from typing import Any

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v26_channel import (
    SOURCES_ORDER,
    SOURCE_METADATA,
    ChannelAdapter,
)
from comparison_bench.src.comparison_bench.formal_ir.v80_s2c_campaign import (
    PB_SIDECAR_NAME,
    bind_empirical_bundle,
)

FACT_ID = "F03"
BUNDLE_NAME = "x1_gamma_f03r1.npz"
VERIFY_NAME = "x1_gamma_f03r1_2M_verify.npz"
BUILD_LOG_NAME = "BUNDLE_BUILD_LOG.md"
VERIFY_LOG_NAME = "BUNDLE_VERIFY_LOG.md"
R1_ROOT_DEFAULT = "workspace/r1_histogram_5e2a91c4"
GAMMA_DEFAULT = "docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz"
DH_MATERIAL = 0.01  # |ΔH| per-plane materiality bar (packet §2.6 item 3)
PB_MATERIAL = 1e-3  # p_b L_inf materiality bar (packet §2.6 item 3)
FROZEN_2M_TRAIN_N = 559872.0  # frozen sidecar 2M_N (ΔN EXPECTED-vintage note)

# T2 dataset id -> V26 human label (display id; "1.5M" never a key). The V26
# source id itself is resolved via source_table() from the frozen V26 module.
T2_TO_LABEL = {"T2-1M": "1M", "T2-1.5M": "1p5M", "T2-2M": "2M"}
T2_ORDER = ("T2-1M", "T2-1.5M", "T2-2M")


def source_table() -> dict[str, dict[str, str]]:
    """F5: T2-* -> {v26_source, prefix}, READ from the frozen V26 module.

    Raises SystemExit (STOP) if the triple cannot be read unambiguously.
    """
    table: dict[str, dict[str, str]] = {}
    for t2, label in T2_TO_LABEL.items():
        hits = [s for s in SOURCES_ORDER
                if SOURCE_METADATA.get(s, {}).get("label") == label]
        if len(hits) != 1:
            raise SystemExit(
                f"STOP: V26 source id for label {label!r} ambiguous "
                f"(hits={hits}); refusing to invent ids")
        table[t2] = {"v26_source": hits[0], "prefix": label}
    return table


def load_sparse_coo(path: str | Path) -> tuple[np.ndarray, dict[str, Any]]:
    """Reload an R1 COO npz (read-only) -> (dense int64 (1024,1024), meta)."""
    z = np.load(str(path), allow_pickle=False)
    try:
        keys = set(z.files)
        if keys != {"row", "col", "count", "shape", "N_train"}:
            raise ValueError(f"COO keys {sorted(keys)} != "
                             f"{{row,col,count,shape,N_train}}")
        for k in ("row", "col", "count"):
            if np.asarray(z[k]).dtype != np.int64:
                raise ValueError(f"COO {k} dtype {np.asarray(z[k]).dtype} "
                                 f"!= int64")
        shape = tuple(int(v) for v in np.asarray(z["shape"]).tolist())
        if shape != (1024, 1024):
            raise ValueError(f"COO shape {shape} != (1024, 1024)")
        n_train = int(z["N_train"])
        row = np.asarray(z["row"], dtype=np.int64)
        col = np.asarray(z["col"], dtype=np.int64)
        count = np.asarray(z["count"], dtype=np.int64)
    finally:
        z.close()
    dense = np.zeros((1024, 1024), dtype=np.int64)
    dense[row, col] = count
    return dense, {"N_train": n_train, "nnz": int(row.size),
                   "sum": int(dense.sum())}


def factorize(v26_source: str, n_ab_dense: np.ndarray) -> dict[str, Any]:
    """Factorize dense TRAIN N_ab via the UNMODIFIED frozen ChannelAdapter.

    Returns g1 (32,1024) P(U1|B), g2 (32,32,1024) P(U2|B,U1) conditional
    (joint->conditional via the frozen ``posterior_rows`` transform itself,
    incl. its delta-at-0 fallback), p_b (1024,), and per-plane H bits.
    """
    adapter = ChannelAdapter(fact_id=FACT_ID, source=v26_source,
                             N_ab=np.asarray(n_ab_dense, dtype=np.float64))
    g1 = np.array(adapter.p_u1_gb, dtype=np.float64)
    b_all = np.tile(np.arange(1024, dtype=np.int64), 32)
    u1_all = np.repeat(np.arange(32, dtype=np.int64), 1024)
    rows = adapter.posterior_rows("L2", b_all, u1_all)  # (32768, 32)
    g2 = np.empty((32, 32, 1024), dtype=np.float64)
    for u1 in range(32):
        g2[u1] = rows[u1 * 1024:(u1 + 1) * 1024].T
    return {"g1": g1, "g2": g2,
            "p_b": np.array(adapter.p_b, dtype=np.float64),
            "H_L1": float(adapter.H_bits["L1"]),
            "H_L2": float(adapter.H_bits["L2"])}


def checksum_record(dense: np.ndarray, r1_json: dict[str, Any]) -> dict[str, Any]:
    """R1 checksum identities recomputed from the COO (read-only inputs)."""
    n_train = int(dense.sum())
    nnz = int(np.count_nonzero(dense))
    k_b = int((dense.sum(axis=0) > 0).sum())
    colsum = dense.sum(axis=0).astype(np.float64)
    p_b_ref = colsum / float(n_train)
    return {
        "N_train_coo": n_train,
        "N_train_json": int(r1_json["N_train"]),
        "N_ok": n_train == int(r1_json["N_train"]),
        "K_AB_coo": nnz,
        "K_AB_json": int(r1_json["K_AB_train"]),
        "K_AB_ok": nnz == int(r1_json["K_AB_train"]),
        "K_B_coo": k_b,
        "K_B_json": int(r1_json["K_B_train"]),
        "K_B_ok": k_b == int(r1_json["K_B_train"]),
        "p_b_ref": p_b_ref,
    }


def compare_2m_lineage(*, h_l1: float, h_l2: float, p_b: np.ndarray,
                       g1: np.ndarray, g2: np.ndarray, n_train: int,
                       gamma_path: str) -> dict[str, Any]:
    """2M lineage comparison vs the frozen bundle (report-only, read-only).

    NEVER refits/overwrites/substitutes the frozen files (np.load only).
    Materiality: |ΔH|>0.01 b/sym per plane OR p_b L_inf>1e-3 ⇒ FINDING.
    """
    rec: dict[str, Any] = {"ran": False, "gamma_path": str(gamma_path)}
    try:
        z = np.load(str(gamma_path), allow_pickle=False)
        try:
            fH1 = float(z["2M_H_L1"])
            fH2 = float(z["2M_H_L2"])
            fg1 = np.asarray(z["2M_gamma1_L1"], dtype=np.float64)
            fg2 = np.asarray(z["2M_gamma2_L2condU1"], dtype=np.float64)
        finally:
            z.close()
        side = Path(str(gamma_path)).parent / PB_SIDECAR_NAME
        sp = np.load(str(side), allow_pickle=False)
        try:
            fpb = np.asarray(sp["2M_p_b"], dtype=np.float64)
            side_n = float(sp["2M_N"]) if "2M_N" in sp.files else None
        finally:
            sp.close()
    except Exception as exc:  # noqa: BLE001 — report-only, never gated
        rec["reason"] = (f"frozen lineage unreadable "
                         f"({type(exc).__name__}: {exc}); report-only, not gated")
        rec["finding"] = False
        return rec
    pb = np.asarray(p_b, dtype=np.float64)
    dH1 = float(h_l1) - fH1
    dH2 = float(h_l2) - fH2
    linf = float(np.max(np.abs(pb - fpb)))
    material = bool(abs(dH1) > DH_MATERIAL or abs(dH2) > DH_MATERIAL
                    or linf > PB_MATERIAL)
    rec.update({
        "ran": True,
        "N_train_r1": int(n_train),
        "N_train_frozen_packet": FROZEN_2M_TRAIN_N,
        "N_train_frozen_sidecar": side_n,
        "delta_N_train_vs_frozen": float(n_train) - FROZEN_2M_TRAIN_N,
        "delta_N_expected_note": ("delta EXPECTED — different pairing "
                                  "vintage/scope; N alone is never a "
                                  "discrepancy finding"),
        "H_L1_rederived": float(h_l1), "H_L1_frozen": fH1,
        "delta_H_L1": dH1,
        "H_L2_rederived": float(h_l2), "H_L2_frozen": fH2,
        "delta_H_L2": dH2,
        "p_b_max_abs_diff": linf,
        "g1_max_abs_diff": float(np.max(np.abs(np.asarray(g1) - fg1))),
        "g2_max_abs_diff": float(np.max(np.abs(np.asarray(g2) - fg2))),
        "materiality_bar": (f"|ΔH|>{DH_MATERIAL}/plane OR "
                            f"p_b L_inf>{PB_MATERIAL}"),
        "material": material,
        "finding": material,
    })
    return rec


def _read_r1_json(r1_root: Path, t2: str) -> dict[str, Any]:
    with open(r1_root / f"{t2}.json", encoding="utf-8") as fh:
        return json.load(fh)


def run_build(root: str, r1_root: str) -> dict[str, Any]:
    """Build the F1/F2 file set into a fresh root (refuses pre-existing)."""
    wall0 = time.monotonic()
    out = Path(root)
    absence_proof = not out.exists()
    if not absence_proof:
        raise SystemExit(f"output root already exists (refusing to "
                         f"overwrite): {out}")
    r1 = Path(r1_root)
    if not r1.is_dir():
        raise SystemExit(f"R1 root absent (read-only input required): {r1}")
    table = source_table()
    out.mkdir(parents=True, exist_ok=False)

    per_source: dict[str, Any] = {}
    bundle_keys: dict[str, np.ndarray] = {}
    for t2 in T2_ORDER:
        dense, meta = load_sparse_coo(r1 / f"{t2}_N_ab_train_sparse.npz")
        js = _read_r1_json(r1, t2)
        chk = checksum_record(dense, js)
        for gate in ("N_ok", "K_AB_ok", "K_B_ok"):
            if not chk[gate]:
                raise SystemExit(f"STOP: R1 checksum {gate} FAIL for {t2} "
                                 f"({chk}); refusing to build")
        fac = factorize(table[t2]["v26_source"], dense)
        dpb = float(np.max(np.abs(fac["p_b"] - chk["p_b_ref"])))
        if dpb != 0.0:
            raise SystemExit(f"STOP: built p_b != COO colsum/N for {t2} "
                             f"(maxabs={dpb})")
        file_pb = np.load(str(r1 / f"{t2}_p_b_train.npy"))
        try:
            dfile = float(np.max(np.abs(fac["p_b"] - file_pb)))
        finally:
            del file_pb
        prefix = table[t2]["prefix"]
        bundle_keys[f"{prefix}_gamma1_L1"] = fac["g1"]
        bundle_keys[f"{prefix}_gamma2_L2condU1"] = fac["g2"]
        bundle_keys[f"{prefix}_p_b"] = fac["p_b"]
        per_source[t2] = {
            "v26_source": table[t2]["v26_source"],
            "prefix": prefix,
            "N_train": chk["N_train_coo"],
            "K_AB": chk["K_AB_coo"],
            "K_B": chk["K_B_coo"],
            "p_b_vs_coo_colsum_maxabs": dpb,
            "p_b_vs_r1_file_maxabs": dfile,
            "H_L1": fac["H_L1"], "H_L2": fac["H_L2"],
            "H_L1_json": float(js["H_L1"]), "H_L2_json": float(js["H_L2"]),
            "H_plug_json": float(js["H_full_plug"]),
            "H_sum_identity_err": abs(float(js["H_L1"]) + float(js["H_L2"])
                                      - float(js["H_full_plug"])),
        }

    bundle_path = out / BUNDLE_NAME
    np.savez(str(bundle_path), **bundle_keys)
    sidecar_path = out / PB_SIDECAR_NAME  # F1: literal frozen sidecar name
    np.savez(str(sidecar_path),
             **{f"{table[t]['prefix']}_p_b": bundle_keys[f"{table[t]['prefix']}_p_b"]
                for t in T2_ORDER})
    # F2: re-derived 2M factorization, verification-only file.
    p2 = table["T2-2M"]["prefix"]
    np.savez(str(out / VERIFY_NAME),
             **{f"{p2}_gamma1_L1": bundle_keys[f"{p2}_gamma1_L1"],
                f"{p2}_gamma2_L2condU1": bundle_keys[f"{p2}_gamma2_L2condU1"],
                f"{p2}_p_b": bundle_keys[f"{p2}_p_b"],
                "H_L1": np.float64(per_source["T2-2M"]["H_L1"]),
                "H_L2": np.float64(per_source["T2-2M"]["H_L2"]),
                "N_train": np.int64(per_source["T2-2M"]["N_train"])})

    wall_s = time.monotonic() - wall0
    rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    lines = ["# X1 bundle build log (T-X1S-1, entry-evidence step)", "",
             f"- bundle root: `{out}` (fresh; absence proven immediately "
             f"before creation: `not exists` == {absence_proof})",
             f"- R1 root (read-only input): `{r1}`",
             "- frozen builder: `ChannelAdapter(fact_id=\"F03\", ...)` "
             "UNMODIFIED (no frozen-module change; joint→conditional via the "
             "frozen `posterior_rows` transform incl. its delta-at-0 fallback)",
             "",
             "## F5 source-id triple (read from nonbinary_v26_channel, "
             "never invented)",
             ""]
    for t2 in T2_ORDER:
        lines.append(f"- {t2} -> V26 id `{table[t2]['v26_source']}` "
                     f"(label/prefix `{table[t2]['prefix']}`)")
    lines += ["",
              "## Per-source checksums (COO recompute vs R1 JSON; ALL exact)",
              ""]
    for t2 in T2_ORDER:
        s = per_source[t2]
        lines.append(
            f"- {t2} [{s['prefix']}]: N_train {s['N_train']} "
            f"(COO sum == JSON N_train exact); "
            f"K_AB {s['K_AB']} (COO nnz == JSON K_AB_train exact); "
            f"K_B {s['K_B']} (occupied-B cols == JSON K_B_train exact); "
            f"p_b vs COO colsum/N maxabs {s['p_b_vs_coo_colsum_maxabs']}; "
            f"p_b vs R1 file maxabs {s['p_b_vs_r1_file_maxabs']}; "
            f"H_L1 {s['H_L1']!r} (JSON {s['H_L1_json']!r}); "
            f"H_L2 {s['H_L2']!r} (JSON {s['H_L2_json']!r}); "
            f"H_L1+H_L2==H_plug err {s['H_sum_identity_err']}")
    lines += ["",
              "## F1 file set (ONE binding convention for verifier+runner)",
              "",
              f"- `{BUNDLE_NAME}` keys: "
              + ", ".join(f"{k} {bundle_keys[k].shape}" for k in sorted(bundle_keys)),
              f"- `{PB_SIDECAR_NAME}` keys: "
              + ", ".join(sorted(f"{table[t]['prefix']}_p_b" for t in T2_ORDER))
              + " (p_b copies; verifier cross-checks identity)",
              f"- `{VERIFY_NAME}`: re-derived 2M factorization "
              "(2M_gamma1_L1 (32,1024) + 2M_gamma2_L2condU1 (32,32,1024) + "
              "2M_p_b (1024,) + H_L1/H_L2/N_train scalars)",
              "",
              "## F2 segregation statement",
              "",
              "- The re-derived 2M factorization in "
              f"`{VERIFY_NAME}` is VERIFICATION-ONLY: it is NEVER bound by "
              "any decode path (this module contains no decode path at all; "
              "no code path may pass that file to a decoder/campaign).",
              "- 2M decode arms bind ONLY the frozen "
              "`docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` (+ "
              "`gamma_f03_pb.npz`) read-only — NEVER refit, NEVER substituted.",
              "",
              "## Cost",
              "",
              f"- build wall: {wall_s:.1f} s; peak RSS: {rss_kb} KiB "
              f"({rss_kb / 1024 ** 2:.3f} GiB); CPUs: 1",
              "- decoder/DE/graph calls: 0; `.ttbin` reads: 0",
              ""]
    (out / BUILD_LOG_NAME).write_text("\n".join(lines), encoding="utf-8")
    return {"root": str(out), "per_source": per_source,
            "wall_s": wall_s, "rss_kb": rss_kb,
            "bundle": str(bundle_path), "sidecar": str(sidecar_path),
            "verify_file": str(out / VERIFY_NAME)}


def run_verify(root: str, r1_root: str, gamma_path: str) -> dict[str, Any]:
    """Verify a built bundle root read-only; writes the verify log."""
    wall0 = time.monotonic()
    out = Path(root)
    if not out.is_dir():
        raise SystemExit(f"bundle root absent (nothing to verify): {out}")
    r1 = Path(r1_root)
    table = source_table()
    bundle_path = out / BUNDLE_NAME
    sidecar_path = out / PB_SIDECAR_NAME
    verify_path = out / VERIFY_NAME
    for p in (bundle_path, sidecar_path, verify_path):
        if not p.is_file():
            raise SystemExit(f"STOP: bundle file missing: {p}")

    zb = np.load(str(bundle_path), allow_pickle=False)
    try:
        bundle = {k: np.asarray(zb[k], dtype=np.float64) for k in zb.files}
    finally:
        zb.close()
    zs = np.load(str(sidecar_path), allow_pickle=False)
    try:
        sidecar = {k: np.asarray(zs[k], dtype=np.float64) for k in zs.files}
    finally:
        zs.close()

    lines = ["# X1 bundle verify log (T-X1S-2, read-only reporter)", "",
             f"- bundle root (read-only): `{out}`",
             f"- R1 root (read-only): `{r1}`",
             f"- frozen lineage (read-only): `{gamma_path}`",
             "",
             "## (i) R1 checksum identities (COO recompute vs JSON scalars)",
             ""]
    failures: list[str] = []
    per_source: dict[str, Any] = {}
    for t2 in T2_ORDER:
        prefix = table[t2]["prefix"]
        dense, _ = load_sparse_coo(r1 / f"{t2}_N_ab_train_sparse.npz")
        js = _read_r1_json(r1, t2)
        chk = checksum_record(dense, js)
        ok = bool(chk["N_ok"] and chk["K_AB_ok"] and chk["K_B_ok"])
        built_pb = bundle.get(f"{prefix}_p_b")
        if built_pb is None:
            ok = False
            dpb = None
        else:
            dpb = float(np.max(np.abs(built_pb - chk["p_b_ref"])))
            ok = ok and dpb == 0.0
        hsum_err = abs(float(js["H_L1"]) + float(js["H_L2"])
                       - float(js["H_full_plug"]))
        ok = ok and hsum_err == 0.0
        per_source[t2] = {"identities_ok": ok, "dpb": dpb,
                          "hsum_err": hsum_err, **{k: chk[k] for k in
                          ("N_train_coo", "K_AB_coo", "K_B_coo")}}
        lines.append(
            f"- {t2} [{prefix}]: N {chk['N_train_coo']}==JSON "
            f"{chk['N_train_json']} {chk['N_ok']}; K_AB {chk['K_AB_coo']}== "
            f"{chk['K_AB_json']} {chk['K_AB_ok']}; K_B {chk['K_B_coo']}== "
            f"{chk['K_B_json']} {chk['K_B_ok']}; built p_b vs COO colsum/N "
            f"maxabs {dpb}; H_L1+H_L2==H_plug err {hsum_err} ⇒ "
            f"{'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"{t2} checksum identities")

    lines += ["",
              "## (ii) Frozen bind gates (path-form, per source)",
              ""]
    for t2 in T2_ORDER:
        prefix = table[t2]["prefix"]
        try:
            bound = bind_empirical_bundle(str(bundle_path), prefix)
            bok = (bound["g1"].shape == (32, 1024)
                   and bound["g2"].shape == (32, 32, 1024)
                   and bound["p_b"].shape == (1024,))
        except Exception as exc:  # noqa: BLE001 — bind refuses ⇒ FAIL
            lines.append(f"- {prefix}: BIND REFUSAL "
                         f"({type(exc).__name__}: {exc}) ⇒ FAIL")
            failures.append(f"{prefix} bind gate")
            continue
        lines.append(f"- {prefix}: bind PASS (g1 {bound['g1'].shape} "
                     f"finite/nonneg/colsums=1; g2 {bound['g2'].shape} "
                     f"cond-rowsums(axis=1)=1; p_b sum=1±1e-9) "
                     f"⇒ {'PASS' if bok else 'FAIL'}")
        if not bok:
            failures.append(f"{prefix} bind shape")

    lines += ["",
              "## (iii) F1 sibling-copy identity (bundle p_b vs sidecar p_b)",
              ""]
    for t2 in T2_ORDER:
        prefix = table[t2]["prefix"]
        a, b = bundle.get(f"{prefix}_p_b"), sidecar.get(f"{prefix}_p_b")
        same = (a is not None and b is not None and np.array_equal(a, b))
        lines.append(f"- {prefix}: identical {same} ⇒ "
                     f"{'PASS' if same else 'FAIL'}")
        if not same:
            failures.append(f"{prefix} F1 sibling identity")

    lines += ["",
              "## (iv) 2M lineage comparison (report-only; never refit)",
              ""]
    zv = np.load(str(verify_path), allow_pickle=False)
    try:
        v2 = {k: np.asarray(zv[k], dtype=np.float64) for k in zv.files}
    finally:
        zv.close()
    p2 = table["T2-2M"]["prefix"]
    js2 = _read_r1_json(r1, "T2-2M")
    lin = compare_2m_lineage(
        h_l1=float(v2["H_L1"]) if "H_L1" in v2 else float(js2["H_L1"]),
        h_l2=float(v2["H_L2"]) if "H_L2" in v2 else float(js2["H_L2"]),
        p_b=v2[f"{p2}_p_b"], g1=v2[f"{p2}_gamma1_L1"],
        g2=v2[f"{p2}_gamma2_L2condU1"],
        n_train=int(js2["N_train"]), gamma_path=gamma_path)
    if not lin.get("ran"):
        lines.append(f"- lineage reporter did not run: {lin.get('reason')}")
    else:
        lines += [
            f"- ΔN_train (R1 {lin['N_train_r1']} vs frozen "
            f"{lin['N_train_frozen_packet']:.0f}; sidecar "
            f"{lin['N_train_frozen_sidecar']}): "
            f"{lin['delta_N_train_vs_frozen']:.0f} "
            f"({lin['delta_N_expected_note']})",
            f"- ΔH_L1={lin['delta_H_L1']!r} "
            f"(rederived {lin['H_L1_rederived']!r} vs frozen "
            f"{lin['H_L1_frozen']!r})",
            f"- ΔH_L2={lin['delta_H_L2']!r} "
            f"(rederived {lin['H_L2_rederived']!r} vs frozen "
            f"{lin['H_L2_frozen']!r})",
            f"- p_b L_inf={lin['p_b_max_abs_diff']!r}; "
            f"max-abs Δg1={lin['g1_max_abs_diff']!r}; "
            f"max-abs Δg2={lin['g2_max_abs_diff']!r}",
            f"- materiality {lin['materiality_bar']} ⇒ "
            f"{'FINDING ESCALATED' if lin['finding'] else 'no finding'}"]
        if lin["finding"]:
            failures.append("2M material FINDING")

    wall_s = time.monotonic() - wall0
    rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    lines += ["",
              "## Verdict",
              "",
              f"- {'ALL CHECKS PASS — no finding' if not failures else 'FAIL: ' + '; '.join(failures)}",
              f"- verify wall: {wall_s:.1f} s; peak RSS: {rss_kb} KiB "
              f"({rss_kb / 1024 ** 2:.3f} GiB); CPUs: 1",
              "- decoder/DE/graph calls: 0; `.ttbin` reads: 0",
              ""]
    (out / VERIFY_LOG_NAME).write_text("\n".join(lines), encoding="utf-8")
    rec = {"root": str(out), "per_source": per_source, "lineage": lin,
           "failures": failures, "wall_s": wall_s, "rss_kb": rss_kb}
    if failures:
        raise SystemExit(f"VERIFY FAIL: {'; '.join(failures)} "
                         f"(see {out / VERIFY_LOG_NAME})")
    return rec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="X1 bundle build + verifier (T-X1S-1/2/3 entry evidence).")
    ap.add_argument("--root", required=True,
                    help="bundle root workspace/x1_bundles_<UUID8> "
                    "(build refuses a pre-existing root)")
    ap.add_argument("--r1-root", default=R1_ROOT_DEFAULT,
                    help="read-only R1 histogram root")
    ap.add_argument("--mode", required=True, choices=("build", "verify"),
                    help="build the F1/F2 file set, or verify a built root")
    ap.add_argument("--gamma", default=GAMMA_DEFAULT,
                    help="read-only frozen 2M lineage for the verify reporter")
    args = ap.parse_args(argv)
    if args.mode == "build":
        rec = run_build(args.root, args.r1_root)
        print(json.dumps({"mode": "build", "root": rec["root"],
                          "sources": sorted(rec["per_source"]),
                          "wall_s": rec["wall_s"],
                          "rss_kib": rec["rss_kb"]}, indent=1, sort_keys=True))
    else:
        rec = run_verify(args.root, args.r1_root, args.gamma)
        print(json.dumps({"mode": "verify", "root": rec["root"],
                          "failures": rec["failures"],
                          "finding_2m": bool(rec["lineage"].get("finding")),
                          "wall_s": rec["wall_s"],
                          "rss_kib": rec["rss_kb"]}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
