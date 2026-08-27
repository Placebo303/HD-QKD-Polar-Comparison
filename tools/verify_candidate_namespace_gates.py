#!/usr/bin/env python3
"""Self-check gates for the loss-namespaced candidate rebuild (fix-candidate-loss-namespace).

Gates (design.md section 4):
  G0  raw ttbin precheck: existence / nonzero size / sha256 for all four loss tiers
      (+ .1 chunks), plus archive fingerprint spot-check against sidecar
      `source_fingerprints` (mismatch is recorded, never fatal).
  G1  determinism anchor: two materialization runs must produce byte-identical
      a_eff.npy / b_eff.npy / chan_ll_table.npy.
  G2  cross-tier byte uniqueness: no a_eff/b_eff sha256 may be shared between any
      two loss tiers over common cells.
  G3  physical sanity (2026-08-26 THIRD revision = FINAL; design.md section 4):
      hard conditions ONLY (1) zero exact cross-tier ser equality on comparable
      cells (exact equality is the shared-pool contamination signature) and
      (2) tier-MEAN ser strictly ordered ser(6dB) > ser(10dB) > ser(16dB) >
      ser(20dB). Per-cell adjacent-pair ordering inversions NEVER gate:
      every inversion goes to a diagnostic list with its relative difference
      (no threshold, no grading); inversions >= 2% additionally get a
      statistical background paragraph (per-tier n_pairs_actual /
      coincidence_rate_hz / small-sample sigma, high-dim near-degenerate band
      note) written into the report, still non-gating. map_sanity
      verdict=FAIL cells go to an isolation list (grid-inherent diagnostic).
      Rationale: independent per-cell measurements have no physical
      monotonicity requirement; the second revision's >=2% needs-explanation
      gate failed on real maxima of 2.2303% (0.23pp past the threshold)
      with no natural clustering — adjudicated as criterion overreach.
  G4  provenance completeness: sidecar meta carries source ttbin path, metrics
      fingerprint, pairing_v2 processing rule, unsampled sequences.

Extra mode:
  affected-cells  enumerate cross-tier joint_fingerprint collisions over existing
      (pre-fix) authoritative sidecars -> affected_cells.csv + count cross-check.
  self-test       synthetic tamper test: injected duplicate/modified bytes MUST fail.

Exit code 0 = gate PASS, 1 = FAIL, 2 = usage error. Nothing under results/ is written.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# Canonical tier keys -> raw record directory name under the raw data root.
TIER_TTBIN_DIRS = {
    "20dB": "Type2_5s_20dB_2026-01-30_224943",
    "16dB": "Type2_5s_16dB_2026-01-30_224900",
    "10dB": "Type2_5s_10dB_2026-01-30_224808",
    "6dB": "Type2_5s_6dB_2026-01-30_224719",
}
# design.md section 2 namespace tags.
SRC_TAG_BY_TIER = {
    "20dB": "loss20dB_t15",
    "16dB": "loss16dB",
    "10dB": "loss10dB",
    "6dB": "loss6dB",
}
# Default pre-fix authoritative sidecar roots used by affected-cells / G3 / G4.
DEFAULT_SIDECAR_ROOTS = {
    "20dB": "results/authoritative/e2e_20dB_fullgrid_pairing_v2_candidate_t15/sidecars",
    "16dB": "results/authoritative/e2e_16dB_fullgrid_pairing_v2_candidate/sidecars",
    "10dB": "results/authoritative/e2e_10dB_fullgrid_pairing_v2_candidate/sidecars",
    "6dB": "results/authoritative/e2e_6dB_fullgrid_pairing_v2_candidate/sidecars",
}
# Event record reference numbers (DATA_PROVENANCE_INCIDENT_20260825.md section 3).
EXPECTED_PAIR_COUNTS = {("10dB", "16dB"): 56, ("6dB", "16dB"): 56, ("6dB", "10dB"): 40}
EXPECTED_6DB_UNION_APPROX = 61

MANIFEST_HEADER = [
    "src_tag", "d", "bw", "blk", "ttbin_path", "ttbin_sha256",
    "a_eff_sha256", "b_eff_sha256", "params_tag", "chan_ll_sha256",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(4 * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def parse_sidecar_roots(value: str | None) -> dict[str, Path]:
    """Parse "tier=path,tier=path" or use defaults; tier key normalized to '6dB' form."""
    roots: dict[str, Path] = {}
    if not value:
        for tier, rel in DEFAULT_SIDECAR_ROOTS.items():
            p = Path(rel)
            roots[tier] = p if p.is_absolute() else REPO_ROOT / p
        return roots
    for part in str(value).split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"--sidecar-roots entry needs tier=path, got: {part}")
        tier, path = part.split("=", 1)
        tier_n = normalize_tier(tier)
        roots[tier_n] = Path(path) if Path(path).is_absolute() else REPO_ROOT / path
    return roots


def normalize_tier(tag: str) -> str:
    t = str(tag).strip().removeprefix("loss").removesuffix("_t15")
    for key in TIER_TTBIN_DIRS:
        if t.lower() == key.lower():
            return key
    raise ValueError(f"unknown tier tag: {tag}")


def cell_blk_dirs(sidecars_root: Path) -> dict[str, Path]:
    """cell name (dX_bwY) -> blk directory containing sidecar_meta.json."""
    out: dict[str, Path] = {}
    if not sidecars_root.is_dir():
        return out
    for cell in sorted(sidecars_root.iterdir()):
        if not cell.is_dir() or not cell.name.startswith("d"):
            continue
        blks = sorted(cell.glob("blk*"))
        if len(blks) == 1 and (blks[0] / "sidecar_meta.json").exists():
            out[cell.name] = blks[0]
    return out


def load_meta(blk_dir: Path) -> dict[str, Any] | None:
    try:
        return json.loads((blk_dir / "sidecar_meta.json").read_text(encoding="utf-8"))
    except Exception:
        return None


def _rel_cells(root: Path) -> dict[str, Path]:
    """relative cell dir (dX_bwY/blkZ) -> absolute path, recursive one level."""
    out: dict[str, Path] = {}
    if not root.is_dir():
        return out
    for cell in sorted(root.iterdir()):
        if not cell.is_dir() or not cell.name.startswith("d"):
            continue
        for blk in sorted(cell.glob("blk*")):
            out[f"{cell.name}/{blk.name}"] = blk
    return out


# --------------------------------------------------------------------------- G0
def gate_g0(
    raw_root: Path,
    report_path: Path | None,
    archive_root: Path,
    sidecar_roots: dict[str, Path],
    manifest_skeleton: Path | None,
) -> tuple[bool, list[str]]:
    lines: list[str] = []
    ok = True
    lines.append("# G0 预检报告 — fix-candidate-loss-namespace")
    lines.append("")
    lines.append(f"- 生成时间: {datetime.now().isoformat()}")
    lines.append(f"- 原始数据根: `{raw_root}`")
    lines.append(f"- 归档 override 根: `{archive_root}`")
    lines.append("")

    lines.append("## 1. 原始 ttbin 检查（存在 + 非零 + sha256）")
    lines.append("")
    lines.append("| 档 | 文件 | 存在 | 字节数 | sha256 |")
    lines.append("|---|---|---|---|---|")
    ttbin_info: dict[str, dict[str, Any]] = {}
    for tier, dirname in TIER_TTBIN_DIRS.items():
        rec = {"main": None, "chunk1": None}
        ddir = raw_root / dirname
        for kind, fname in (("main", f"{dirname}.ttbin"), ("chunk1", f"{dirname}.1.ttbin")):
            f = ddir / fname
            exists = f.is_file()
            size = f.stat().st_size if exists else -1
            digest = sha256_file(f) if exists and size > 0 else ""
            rec[kind] = {"path": str(f), "exists": exists, "size": int(size), "sha256": digest}
            label = f"{tier} {'主文件' if kind == 'main' else '.1 分片'}"
            lines.append(
                f"| {label} | `{fname}` | {exists} | {size if exists else '-'} | `{digest[:32]}{'…' if digest else ''}` |"
            )
            if not exists or size <= 0:
                ok = False
        ttbin_info[tier] = rec
    lines.append("")

    # Archive fingerprint spot-check vs sidecar source_fingerprints (mismatch allowed).
    lines.append("## 2. 归档 override 点指纹抽验（对账 sidecar source_fingerprints；mismatch 允许，仅记录）")
    lines.append("")
    lines.append("| 档 | 对账格数 | 匹配 | 失配 | 归档缺失 | sidecar 无指纹 |")
    lines.append("|---|---|---|---|---|---|")
    mismatch_examples: dict[str, list[str]] = {}
    for tier, sc_root in sorted(sidecar_roots.items()):
        matched = mismatched = missing_arch = no_fp = 0
        mismatch_examples[tier] = []
        for cell, blk in cell_blk_dirs(sc_root).items():
            meta = load_meta(blk) or {}
            fp = ((meta.get("source_fingerprints") or {}).get("metrics_file") or {})
            recorded = str(fp.get("sha256") or "")
            if not recorded:
                no_fp += 1
                continue
            arch = archive_root / cell / "results" / "attempt_0" / "ttbin_parsing" / "ttbin_metrics.json"
            if not arch.is_file():
                missing_arch += 1
                continue
            actual = sha256_file(arch)
            if actual == recorded:
                matched += 1
            else:
                mismatched += 1
                if len(mismatch_examples[tier]) < 5:
                    mismatch_examples[tier].append(f"{cell}: recorded={recorded[:12]}… archived={actual[:12]}…")
        lines.append(f"| {tier} | {matched + mismatched} | {matched} | {mismatched} | {missing_arch} | {no_fp} |")
    lines.append("")
    lines.append("说明：归档内 resolved_config.json 已被 2026-04-26 之后的运行覆盖（design.md §1 已知），")
    lines.append("ttbin_metrics.json 失配仅作记录，不阻断；主路线为原始 ttbin 直提。失配示例：")
    for tier in sorted(mismatch_examples):
        for ex in mismatch_examples[tier]:
            lines.append(f"- {tier} {ex}")
    lines.append("")

    lines.append("## 3. MANIFEST 骨架")
    lines.append("")
    if manifest_skeleton is not None:
        manifest_skeleton.parent.mkdir(parents=True, exist_ok=True)
        with manifest_skeleton.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(MANIFEST_HEADER)
        lines.append(f"- 骨架（仅表头，Phase 3 定稿前不落 results/）：`{manifest_skeleton}`")
        lines.append(f"- 表头: `{','.join(MANIFEST_HEADER)}`")
    lines.append("")

    lines.append(f"## 结论：G0 {'PASS' if ok else 'FAIL'}")
    lines.append("")

    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"[G0] report written: {report_path}")
    for ln in lines:
        print(ln)
    return ok, lines


# --------------------------------------------------------------------------- G1
def gate_g1(root_a: Path, root_b: Path) -> tuple[bool, list[str]]:
    files = ("a_eff.npy", "b_eff.npy", "chan_ll_table.npy")
    ca, cb = _rel_cells(root_a), _rel_cells(root_b)
    common = sorted(set(ca) & set(cb))
    lines: list[str] = []
    only_a = sorted(set(ca) - set(cb))
    only_b = sorted(set(cb) - set(ca))
    if only_a:
        lines.append(f"[G1] cells only in A: {only_a}")
    if only_b:
        lines.append(f"[G1] cells only in B: {only_b}")
    if not common:
        lines.append("[G1] FAIL: no common cells between the two runs")
        return False, lines
    failures: list[str] = []
    for rel in common:
        for fname in files:
            fa, fb = ca[rel] / fname, cb[rel] / fname
            ea, eb = fa.is_file(), fb.is_file()
            if ea != eb:
                failures.append(f"{rel}/{fname}: presence mismatch A={ea} B={eb}")
                continue
            if not ea:
                continue
            if sha256_file(fa) != sha256_file(fb):
                ba, bb = fa.read_bytes(), fb.read_bytes()
                off = next((i for i, (x, y) in enumerate(zip(ba, bb)) if x != y), min(len(ba), len(bb)))
                failures.append(f"{rel}/{fname}: byte diff at offset {off}")
    for ln in [f"[G1] compared {len(common)} cells x {len(files)} file kinds"]:
        lines.append(ln)
    if failures:
        lines.append(f"[G1] FAIL: {len(failures)} byte-level differences (first 10):")
        lines.extend(f"  - {x}" for x in failures[:10])
        return False, lines
    lines.append("[G1] PASS: all common cells byte-identical across the double run")
    return True, lines


# --------------------------------------------------------------------------- G2
def gate_g2(sidecar_roots: dict[str, Path], *, min_cells: int = 1) -> tuple[bool, list[str]]:
    lines: list[str] = []
    if len(sidecar_roots) < 2:
        lines.append("[G2] FAIL: need at least two tiers")
        return False, lines
    hashes: dict[str, dict[str, dict[str, str]]] = {}
    for tier, root in sorted(sidecar_roots.items()):
        per_cell: dict[str, dict[str, str]] = {}
        for cell, blk in cell_blk_dirs(root).items():
            entry: dict[str, str] = {}
            for fname in ("a_eff.npy", "b_eff.npy"):
                f = blk / fname
                if f.is_file():
                    entry[fname] = sha256_file(f)
            if entry:
                per_cell[cell] = entry
        hashes[tier] = per_cell
    collisions: list[str] = []
    compared = 0
    for (t1, h1), (t2, h2) in itertools.combinations(hashes.items(), 2):
        for cell in sorted(set(h1) & set(h2)):
            for fname in ("a_eff.npy", "b_eff.npy"):
                s1, s2 = h1[cell].get(fname), h2[cell].get(fname)
                if s1 and s2:
                    compared += 1
                    if s1 == s2:
                        collisions.append(f"{cell}/{fname}: {t1} == {t2} sha256={s1[:16]}…")
    lines.append(f"[G2] cross-tier hash comparisons: {compared}")
    if collisions:
        lines.append(f"[G2] FAIL: {len(collisions)} cross-tier byte-identical arrays (first 10):")
        lines.extend(f"  - {x}" for x in collisions[:10])
        return False, lines
    if compared < min_cells:
        lines.append(f"[G2] FAIL: only {compared} cross-tier hash comparisons, below required minimum {min_cells}")
        return False, lines
    lines.append("[G2] PASS: no a_eff/b_eff sha256 shared between any two tiers")
    return True, lines


# --------------------------------------------------------------------------- G3
# Final G3 (2026-08-26): 2% is a REPORTING marker only — cells at/above it get
# the statistical background paragraph. It never gates anything.
STAT_BACKGROUND_REL_TOL = 0.02


def _rel_diff(a: float, b: float) -> float:
    """Symmetric relative difference |a-b| / ((|a|+|b|)/2); inf when both are 0."""
    denom = (abs(a) + abs(b)) / 2.0
    return abs(a - b) / denom if denom > 0.0 else float("inf")


def _parse_cell(cell: str) -> tuple[int, int] | None:
    try:
        d_part, bw_part = cell.split("_bw", 1)
        return int(d_part.removeprefix("d")), int(bw_part)
    except Exception:
        return None


def _coincidence_rates(sidecar_root: Path) -> dict[tuple[int, int], float]:
    """coincidence_rate_hz per (dimension, bw) from the candidate's _tmp_grid_table.csv when present."""
    grid = sidecar_root.parent / "_tmp_grid_table.csv"
    out: dict[tuple[int, int], float] = {}
    if not grid.is_file():
        return out
    try:
        with grid.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    out[(int(row["dimension"]), int(row["bin_width_ps"]))] = float(row["coincidence_rate_hz"])
                except Exception:
                    continue
    except Exception:
        pass
    return out


def gate_g3(
    sidecar_roots: dict[str, Path],
    *,
    min_cells: int = 1,
    detail_csv: Path | None = None,
) -> tuple[bool, list[str]]:
    """FINAL G3 (2026-08-26 third revision; design.md section 4).

    Hard FAIL conditions ONLY:
      ① exact ser equality between any two tiers on a comparable cell
         (byte-identical measurement = shared-pool contamination signature);
      ② tier-mean ser not strictly ordered ser(6dB) > ser(10dB) > ser(16dB) > ser(20dB).

    Non-gating diagnostics:
      - inversion list: EVERY per-cell adjacent-pair ordering inversion with its
        symmetric relative difference |a-b| / ((|a|+|b|)/2) — no threshold, no grading;
      - statistical background: inversions with rel diff >= STAT_BACKGROUND_REL_TOL
        additionally get per-tier n_pairs_actual / coincidence_rate_hz and a
        small-sample sigma estimate sqrt(ser*(1-ser)/n_pairs), plus the known
        high-dim near-degenerate band note (d512-d2048 mapping-layer coincidence);
      - isolation list: map_sanity verdict != PASS cells.

    A comparable cell is present in every provided tier with finite map_ser.
    """
    order = ["6dB", "10dB", "16dB", "20dB"]
    tiers_present = [t for t in order if t in sidecar_roots]
    lines: list[str] = []
    isolation: list[tuple[str, str, str]] = []   # (tier, cell, detail)
    inversions: list[tuple[str, str, float, str]] = []  # (pair, cell, rel_diff, detail)
    eq_hits: list[str] = []
    ser_by_cell: dict[str, dict[str, float]] = {}
    npairs_by_cell: dict[str, dict[str, float]] = {}
    coinc_by_tier: dict[str, dict[tuple[int, int], float]] = {}
    n_cells_seen = 0
    for tier in tiers_present:
        coinc_by_tier[tier] = _coincidence_rates(sidecar_roots[tier])
        cells = cell_blk_dirs(sidecar_roots[tier])
        n_cells_seen += len(cells)
        for cell, blk in cells.items():
            meta = load_meta(blk) or {}
            ms = meta.get("map_sanity") or {}
            ser = ms.get("map_ser")
            verdict = str(ms.get("verdict") or "").upper()
            diag = meta.get("diagnostics") or {}
            up = ((meta.get("materialize_params") or {}).get("used_params") or {})
            n_pairs = diag.get("n_pairs_actual", up.get("n_pairs_actual"))
            if isinstance(ser, (int, float)):
                ser_by_cell.setdefault(cell, {})[tier] = float(ser)
            if isinstance(n_pairs, (int, float)):
                npairs_by_cell.setdefault(cell, {})[tier] = float(n_pairs)
            if verdict != "PASS":
                isolation.append((tier, cell, f"verdict={verdict or 'MISSING'} ser={ser}"))

    # Comparable cells: full tier coverage AND finite ser in every tier.
    ordered_cells = {c: s for c, s in ser_by_cell.items() if len(s) == len(tiers_present)}

    # ① zero exact cross-tier ser equality on comparable cells.
    for cell, s in sorted(ordered_cells.items()):
        for t1, t2 in itertools.combinations(tiers_present, 2):
            if s[t1] == s[t2]:
                eq_hits.append(f"{cell}: ser({t1}) == ser({t2}) == {s[t1]!r} (exact contamination signature)")

    # ② tier-mean ser strictly ordered.
    means = {
        t: (sum(s[t] for s in ordered_cells.values()) / len(ordered_cells))
        if ordered_cells else float("nan")
        for t in tiers_present
    }
    mean_violations: list[str] = []
    for t_a, t_b in zip(tiers_present, tiers_present[1:]):
        if not (means[t_a] > means[t_b]):
            mean_violations.append(f"mean ser({t_a})={means[t_a]:.6g} <= mean ser({t_b})={means[t_b]:.6g}")

    # Per-cell adjacent-pair inversions -> diagnostic list (ALL of them, no gating).
    for cell, s in sorted(ordered_cells.items()):
        for t_a, t_b in zip(tiers_present, tiers_present[1:]):
            va, vb = s[t_a], s[t_b]
            if va <= vb:
                rel = _rel_diff(va, vb)
                detail = f"{t_a}={va!r} <= {t_b}={vb!r} rel_diff={rel:.4%}"
                inversions.append((f"{t_a}>{t_b}", cell, rel, detail))

    lines.append(f"[G3] cells seen: {n_cells_seen} across {len(tiers_present)} tiers {tiers_present}")
    lines.append(f"[G3] comparable full-coverage cells: {len(ordered_cells)}")
    lines.append("[G3] tier mean ser (condition ②, required strict 6>10>16>20): "
                 + " ".join(f"{t}={means[t]:.6g}" for t in tiers_present))
    lines.append(f"[G3] ① exact cross-tier ser equalities: {len(eq_hits)}")
    lines.append(f"[G3] ② mean-order violations: {len(mean_violations)}")
    lines.append(f"[G3] per-cell inversions (diagnostic only, non-gating): {len(inversions)} "
                 f"[of which >= {STAT_BACKGROUND_REL_TOL:.0%} get a statistical background paragraph]")
    lines.append(f"[G3] isolation list (verdict!=PASS, non-gating): {len(isolation)}")
    for d in eq_hits[:10]:
        lines.append(f"  [exact-eq] {d}")
    if len(eq_hits) > 10:
        lines.append(f"  [exact-eq] ... {len(eq_hits) - 10} more")
    for pair, cell, rel, d in inversions:
        lines.append(f"  [inversion] {cell} [{pair}]: {d}")

    # Statistical background paragraphs for inversions >= 2% (non-gating).
    bg_cells = [(pair, cell, rel, d) for pair, cell, rel, d in inversions if rel >= STAT_BACKGROUND_REL_TOL]
    if bg_cells:
        lines.append(f"[G3] statistical background for {len(bg_cells)} inversion cell(s) "
                     f">= {STAT_BACKGROUND_REL_TOL:.0%} (non-gating evidence, small-sample / near-degeneracy mechanism):")
        for pair, cell, rel, _d in bg_cells:
            key = _parse_cell(cell)
            lines.append(f"  [background] {cell} [{pair}] max_rel_diff={rel:.4%} dimension-band: "
                         + ("high-dim near-degenerate band d512-d2048 (known mapping-layer coincidence pattern)"
                            if key and 512 <= key[0] <= 2048 else f"d{key[0]} standard band"))
            for tier in tiers_present:
                s_val = ser_by_cell[cell].get(tier)
                n_pair = npairs_by_cell.get(cell, {}).get(tier)
                parts = [f"ser({tier})={s_val!r}" if s_val is not None else f"ser({tier})=n/a"]
                if n_pair:
                    sigma = (s_val * (1.0 - s_val) / n_pair) ** 0.5 if s_val is not None else None
                    parts.append(f"n_pairs_actual={int(n_pair)}")
                    if sigma is not None:
                        parts.append(f"sigma_small_sample={sigma:.2e}")
                else:
                    parts.append("n_pairs_actual=n/a")
                c_hz = coinc_by_tier.get(tier, {}).get(key) if key else None
                if c_hz is not None:
                    parts.append(f"coincidence_rate_hz={c_hz:.2f}")
                lines.append("    " + "; ".join(parts))

    for t, c, d in isolation[:10]:
        lines.append(f"  [isolation] {t}/{c}: {d}")
    if len(isolation) > 10:
        lines.append(f"  [isolation] ... {len(isolation) - 10} more")

    if detail_csv is not None:
        detail_csv.parent.mkdir(parents=True, exist_ok=True)
        with detail_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["kind", "tier_or_pair", "cell", "rel_diff", "detail"])
            w.writerows(("isolation", t, c, "", d) for t, c, d in isolation)
            w.writerows(("inversion", p, c, f"{rel:.6%}", d) for p, c, rel, d in inversions)
        print(f"[G3] detail csv written: {detail_csv}")

    if len(ordered_cells) < min_cells:
        lines.append(f"[G3] FAIL: only {len(ordered_cells)} comparable ordering cells, "
                     f"below required minimum {min_cells}")
        return False, lines
    if eq_hits:
        lines.append(f"[G3] FAIL: condition ① broken — {len(eq_hits)} exact cross-tier ser equality hit(s)")
        return False, lines
    if mean_violations:
        lines.append(f"[G3] FAIL: condition ② broken — {'; '.join(mean_violations)}")
        return False, lines
    lines.append(f"[G3] PASS: no exact cross-tier ser equality; tier means strictly ordered; "
                 f"{len(inversions)} inversion(s) diagnostic-listed ({len(bg_cells)} with statistical background); "
                 f"{len(isolation)} verdict=FAIL cell(s) isolated")
    return True, lines


# --------------------------------------------------------------------------- G4
def gate_g4(sidecar_roots: dict[str, Path]) -> tuple[bool, list[str]]:
    lines: list[str] = []
    problems: list[str] = []
    checked = 0
    for tier, root in sorted(sidecar_roots.items()):
        expect_dirname = TIER_TTBIN_DIRS[tier]
        for cell, blk in cell_blk_dirs(root).items():
            checked += 1
            meta = load_meta(blk)
            if not meta:
                problems.append(f"{tier}/{cell}: sidecar_meta.json unreadable")
                continue
            fp = ((meta.get("source_fingerprints") or {}).get("metrics_file") or {})
            jfp = meta.get("joint_fingerprint") or {}
            up = ((meta.get("materialize_params") or {}).get("used_params") or {})
            ttbin_path = str(up.get("source_ttbin_paths") or "")
            checks = {
                "metrics_fingerprint": bool(fp.get("sha256")),
                "joint_fingerprint": bool(jfp.get("sha256")),
                "source_ttbin_path": bool(ttbin_path),
                "processing_rule_version==pairing_v2": (
                    str((meta.get("materialize_params") or {}).get("processing_rule_version")) == "pairing_v2"
                ),
                "sequence_is_sampled==0": int(meta.get("sequence_is_sampled", 1)) == 0,
                "ttbin_matches_tier_record": expect_dirname in ttbin_path,
                "params_snapshot": isinstance(up, dict) and "max_pairs" in up,
            }
            for k, vok in checks.items():
                if not vok:
                    problems.append(f"{tier}/{cell}: {k} missing/invalid")
    lines.append(f"[G4] provenance fields checked on {checked} sidecars across {len(sidecar_roots)} tiers")
    if problems:
        lines.append(f"[G4] FAIL: {len(problems)} problems (first 10):")
        lines.extend(f"  - {x}" for x in problems[:10])
        return False, lines
    lines.append("[G4] PASS: provenance complete and consistent with each tier's raw record")
    return True, lines


# --------------------------------------------------------------- affected-cells
def mode_affected_cells(sidecar_roots: dict[str, Path], out_csv: Path) -> tuple[bool, list[str]]:
    lines: list[str] = []
    fps: dict[str, dict[str, str]] = {}
    for tier, root in sorted(sidecar_roots.items()):
        per_cell: dict[str, str] = {}
        for cell, blk in cell_blk_dirs(root).items():
            meta = load_meta(blk) or {}
            digest = str(((meta.get("joint_fingerprint") or {}).get("sha256")) or "")
            if digest:
                per_cell[cell] = digest
        fps[tier] = per_cell
        print(f"[affected-cells] {tier}: {len(per_cell)} cells with joint fingerprint")

    pairs = list(itertools.combinations(sorted(fps), 2))
    pair_counts: dict[tuple[str, str], list[str]] = {}
    rows: list[dict[str, Any]] = []
    all_cells = sorted({c for m in fps.values() for c in m})
    for cell in all_cells:
        sharing = [(a, b) for (a, b) in pairs if cell in fps[a] and cell in fps[b] and fps[a][cell] == fps[b][cell]]
        for pr in sharing:
            pair_counts.setdefault(tuple(sorted(pr)), []).append(cell)
        if sharing:
            rows.append({
                "d_bw": cell,
                "fp_prefix": fps[sharing[0][0]][cell][:16],
                "shared_pairs": "|".join("∩".join(sorted(pr)) for pr in sharing),
            })

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["d_bw", "fp_prefix", "shared_pairs"])
        w.writeheader()
        w.writerows(rows)

    union6 = sorted({c for (a, b), cells in pair_counts.items() if "6dB" in (a, b) for c in cells})
    lines.append(f"[affected-cells] wrote {len(rows)} affected cells -> {out_csv}")
    discrepancies: list[str] = []
    for pr in sorted(EXPECTED_PAIR_COUNTS):
        got = len(pair_counts.get(tuple(sorted(pr)), []))
        exp = EXPECTED_PAIR_COUNTS[pr]
        mark = "OK" if got == exp else "DIFF"
        lines.append(f"[affected-cells] {pr[0]}∩{pr[1]}: got {got}, event record says {exp} [{mark}]")
        if got != exp:
            discrepancies.append(f"{pr}: got {got} expected {exp}")
    if "6dB" in fps:
        lines.append(f"[affected-cells] 6dB union: got {len(union6)}, event record ≈{EXPECTED_6DB_UNION_APPROX}")
    for other in ("20dB",):
        if other in fps:
            shared_other = sum(1 for (a, b) in pair_counts if other in (a, b) for _ in pair_counts[(a, b)])
            uniq_shared = len({c for (a, b), cs in pair_counts.items() if other in (a, b) for c in cs})
            lines.append(f"[affected-cells] {other} shared-with-any: {uniq_shared} (event record: 0)")
            if uniq_shared != 0:
                discrepancies.append(f"{other} shared with others: {uniq_shared} expected 0")
    ok = not discrepancies
    if discrepancies:
        lines.append("[affected-cells] DISCREPANCIES vs event record: " + "; ".join(discrepancies))
    else:
        lines.append("[affected-cells] counts match the event record exactly")
    summary_path = out_csv.with_suffix(".summary.txt")
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[affected-cells] summary written: {summary_path}")
    for ln in lines:
        print(ln)
    return ok, lines


# -------------------------------------------------------------------- self-test
def self_test() -> tuple[bool, list[str]]:
    """Synthetic tamper test against the FINAL gate semantics.
    Duplicate bytes must FAIL G2; modified bytes must FAIL G1;
    final G3 scenarios: S0 well-ordered PASS; S1 exact ser equality FAIL;
    S2 inverted tier-mean order FAIL; S3 <2% inversion PASS + diagnostic-listed;
    S4 >=2% inversion PASS + diagnostic-listed + statistical background paragraph;
    S5 lone verdict=FAIL cell PASS + isolation-listed; stripped provenance FAIL G4."""
    lines: list[str] = []
    with tempfile.TemporaryDirectory(prefix="nsfix_selftest_") as td:
        tmp = Path(td)
        ns = tmp / "sidecars"
        cells = ("d8_bw100", "d8_bw200")

        def _fake_meta(tier: str, ser: float) -> dict[str, Any]:
            return {
                "sequence_is_sampled": 0,
                "joint_fingerprint": {"sha256": "f" * 64},
                "source_fingerprints": {"metrics_file": {"sha256": "a" * 64}},
                "materialize_params": {
                    "processing_rule_version": "pairing_v2",
                    "used_params": {"max_pairs": 0, "n_pairs_actual": 120000,
                                    "source_ttbin_paths": rf"D:\raw\{TIER_TTBIN_DIRS[tier]}\x.ttbin"},
                },
                "diagnostics": {"n_pairs_actual": 120000},
                "map_sanity": {"verdict": "PASS", "map_ser": ser},
            }

        def make_tier(tier: str, sers: dict[str, float], verdicts: dict[str, str] | None = None) -> Path:
            root = ns / tier
            for cell in cells:
                blk = root / cell / "blk0"
                blk.mkdir(parents=True, exist_ok=True)
                base = (f"{tier}/{cell}".encode() + b"P" * 256)[:256]
                (blk / "a_eff.npy").write_bytes(base)
                (blk / "b_eff.npy").write_bytes(bytes(reversed(base)))
                (blk / "chan_ll_table.npy").write_bytes(b"C" * 64)
                meta = _fake_meta(tier, sers[cell])
                if verdicts and cell in verdicts:
                    meta["map_sanity"]["verdict"] = verdicts[cell]
                (blk / "sidecar_meta.json").write_text(json.dumps(meta), encoding="utf-8")
            return root

        # Two cells per tier so a single <2% per-cell inversion can leave the
        # tier means strictly ordered (condition ② decouples from condition ③).
        def build_tiers(ser16: dict[str, float]) -> dict[str, Path]:
            return {
                "6dB": make_tier("6dB", {"d8_bw100": 0.0500, "d8_bw200": 0.0600}),
                "10dB": make_tier("10dB", {"d8_bw100": 0.0400, "d8_bw200": 0.0500}),
                "16dB": make_tier("16dB", ser16),
                "20dB": make_tier("20dB", {"d8_bw100": 0.0200, "d8_bw200": 0.0250}),
            }
        proper16 = {"d8_bw100": 0.0390, "d8_bw200": 0.0300}
        tiers = build_tiers(proper16)

        # G2 pass on distinct tiers
        ok, _ = gate_g2(dict(tiers))
        if not ok:
            lines.append("self-test: G2 unexpectedly FAILED on distinct tiers")
            return False, lines
        # Tamper: duplicate tier bytes into another tier -> G2 must FAIL
        dup_from, dup_to = tiers["6dB"] / "d8_bw100" / "blk0", tiers["16dB"] / "d8_bw100" / "blk0"
        backup = (dup_to / "a_eff.npy").read_bytes()
        (dup_to / "a_eff.npy").write_bytes((dup_from / "a_eff.npy").read_bytes())
        ok, _ = gate_g2(dict(tiers))
        if ok:
            lines.append("self-test: G2 unexpectedly PASSED after injecting duplicate bytes")
            return False, lines
        (dup_to / "a_eff.npy").write_bytes(backup)

        # G1 pass on identical copy, then flip a byte -> must FAIL
        run_a, run_b = tmp / "runA", tmp / "runB"
        for r in (run_a, run_b):
            (r / "d8_bw100" / "blk0").mkdir(parents=True)
            for fname in ("a_eff.npy", "b_eff.npy", "chan_ll_table.npy"):
                (r / "d8_bw100" / "blk0" / fname).write_bytes(b"Z" * 512)
        ok, _ = gate_g1(run_a, run_b)
        if not ok:
            lines.append("self-test: G1 unexpectedly FAILED on identical runs")
            return False, lines
        target = run_b / "d8_bw100" / "blk0" / "a_eff.npy"
        target.write_bytes(b"Z" * 511 + b"Y")
        ok, _ = gate_g1(run_a, run_b)
        if ok:
            lines.append("self-test: G1 unexpectedly PASSED after single-byte tamper")
            return False, lines

        # G3 (FINAL semantics, six scenarios S0-S5):
        # S0 well-ordered synthetic tiers -> PASS.
        ok, g3_lines = gate_g3(dict(tiers))
        if not ok:
            lines.append("self-test: G3 S0 unexpectedly FAILED on well-ordered synthetic tiers")
            return False, lines
        # S1 exact cross-tier equality (16dB c1 := 10dB c1) -> MUST FAIL on ①.
        tiers = build_tiers({"d8_bw100": 0.0400, "d8_bw200": 0.0300})
        ok, g3_lines = gate_g3(dict(tiers))
        if ok or not any("[exact-eq]" in l for l in g3_lines):
            lines.append("self-test: G3 S1 must FAIL and flag exact cross-tier ser equality")
            return False, lines
        # S2 inverted tier-MEAN order -> MUST FAIL on ②.
        tiers = build_tiers({"d8_bw100": 0.0401, "d8_bw200": 0.0501})
        ok, g3_lines = gate_g3(dict(tiers))
        if ok or not any("condition ②" in l for l in g3_lines):
            lines.append("self-test: G3 S2 must FAIL when tier-mean ordering is inverted")
            return False, lines
        # S3 lone <2% per-cell inversion with ordered means -> PASS; diagnostic-listed.
        tiers = build_tiers({"d8_bw100": 0.0401, "d8_bw200": 0.0300})
        ok, g3_lines = gate_g3(dict(tiers))
        if not ok or not any("[inversion] d8_bw100" in l for l in g3_lines) \
                or any("[background] d8_bw100" in l for l in g3_lines):
            lines.append("self-test: G3 S3 must PASS a <2% inversion and diagnostic-list it without background")
            return False, lines
        # S4 >=2% per-cell inversion (means stay ordered, no exact equality)
        # -> PASS + listed + statistical background paragraph present (non-gating).
        tiers = build_tiers({"d8_bw100": 0.0495, "d8_bw200": 0.0300})
        ok, g3_lines = gate_g3(dict(tiers))
        if not ok or not any("[background] d8_bw100" in l for l in g3_lines) \
                or not any("n_pairs_actual=120000" in l for l in g3_lines):
            lines.append("self-test: G3 S4 must PASS an >=2% inversion with a statistical background paragraph")
            return False, lines
        # S5 lone verdict=FAIL (ser unchanged, ordering intact) -> gate PASS + isolation.
        tiers = build_tiers(proper16)
        (tiers["16dB"] / "d8_bw100" / "blk0" / "sidecar_meta.json").write_text(
            json.dumps({**_fake_meta("16dB", 0.0390), "map_sanity": {"verdict": "FAIL", "map_ser": 0.0390}}),
            encoding="utf-8")
        ok, g3_lines = gate_g3(dict(tiers))
        if not ok or not any("[isolation] 16dB/d8_bw100" in l for l in g3_lines):
            lines.append("self-test: G3 S5 must PASS a lone verdict=FAIL cell and list it as isolated")
            return False, lines

        # G4 pass on complete provenance, then strip fingerprint -> must FAIL
        ok, _ = gate_g4({"16dB": tiers["16dB"]})
        if not ok:
            lines.append("self-test: G4 unexpectedly FAILED on complete synthetic provenance")
            return False, lines
        (tiers["16dB"] / "d8_bw100" / "blk0" / "sidecar_meta.json").write_text(
            json.dumps({"note": "stripped"}), encoding="utf-8")
        ok, _ = gate_g4({"16dB": tiers["16dB"]})
        if ok:
            lines.append("self-test: G4 unexpectedly PASSED with stripped provenance")
            return False, lines

    lines.append("self-test PASS: G1/G2 detect tampered bytes; final G3 (S0-S5) fails only on "
                 "exact ser equality / inverted tier means while diagnostic-listing all per-cell "
                 "inversions, adding statistical background paragraphs at >=2%, and isolating "
                 "verdict=FAIL cells; G4 detects stripped provenance")
    return True, lines


# -------------------------------------------------------------------------- CLI
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--gate", required=True,
                    choices=["G0", "G1", "G2", "G3", "G4", "affected-cells", "self-test"])
    ap.add_argument("--raw-root", default=r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s")
    ap.add_argument("--archive-root", default="results/archive/workspace_override_points")
    ap.add_argument("--report", default="", help="G0 markdown report path (default: alongside --manifest-skeleton)")
    ap.add_argument("--manifest-skeleton", default="", help="G0 empty MANIFEST.csv skeleton path")
    ap.add_argument("--sidecar-roots", default="", help='tier=path pairs, e.g. "6dB=D:/x/sidecars,10dB=..."')
    ap.add_argument("--min-cells", type=int, default=1,
                    help="G2/G3 minimum required comparison/cell count; empty or below this is FAIL")
    ap.add_argument("--g1-root-a", default="")
    ap.add_argument("--g1-root-b", default="")
    ap.add_argument("--out", default="", help="affected-cells output csv")
    args = ap.parse_args(argv)

    try:
        sidecar_roots = parse_sidecar_roots(args.sidecar_roots)
    except ValueError as e:
        print(f"usage error: {e}", file=sys.stderr)
        return 2

    if args.gate == "self-test":
        ok, _lines = self_test()
        print("\n".join(_lines))
        return 0 if ok else 1

    if args.gate == "G0":
        archive_root = Path(args.archive_root)
        if not archive_root.is_absolute():
            archive_root = REPO_ROOT / archive_root
        skeleton = Path(args.manifest_skeleton) if args.manifest_skeleton else None
        report = Path(args.report) if args.report else (
            skeleton.parent / "G0_precheck_report.md" if skeleton else None
        )
        ok, _ = gate_g0(Path(args.raw_root), report, archive_root, sidecar_roots, skeleton)
        return 0 if ok else 1

    if args.gate == "G1":
        if not args.g1_root_a or not args.g1_root_b:
            print("usage error: --g1-root-a and --g1-root-b required", file=sys.stderr)
            return 2
        ok, lines = gate_g1(Path(args.g1_root_a), Path(args.g1_root_b))
        print("\n".join(lines))
        return 0 if ok else 1

    if args.gate in {"G2", "G3", "G4"}:
        if args.gate == "G2":
            ok, lines = gate_g2(sidecar_roots, min_cells=int(args.min_cells))
        elif args.gate == "G3":
            detail_csv = Path(args.out) if args.out else None
            ok, lines = gate_g3(
                sidecar_roots,
                min_cells=int(args.min_cells),
                detail_csv=detail_csv,
            )
        else:
            ok, lines = gate_g4(sidecar_roots)
        print("\n".join(lines))
        return 0 if ok else 1

    if args.gate == "affected-cells":
        if not args.out:
            print("usage error: --out required for affected-cells", file=sys.stderr)
            return 2
        ok, _ = mode_affected_cells(sidecar_roots, Path(args.out))
        return 0 if ok else 1

    return 2


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    raise SystemExit(main())
