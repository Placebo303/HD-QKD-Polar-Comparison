"""Print a diagnostic replay of explicitly selected M2 accounting summaries.

This module reads only the named ``rows.json`` files and writes only stdout.
Its output is diagnostic and unreviewed; it does not evaluate D2 or infer a
method-family ranking.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Sequence


SOURCE_ORDER = ("1M", "1p5M", "2M")
SUPERFRAME_SYMBOLS = 1024
SYMBOLS_PER_BLOCK = 64
BLOCKS_PER_SUPERFRAME = 16
TAG_BITS_PER_BLOCK = 64
F_LABELS = ("f_super", "f_notag", "f_eff")
CLAIM_CEILING = (
    "DIAGNOSTIC_UNREVIEWED: no D2 evaluation, backend inference, method-family "
    "ranking, SKR, qualification, or publication claim; cite only after the "
    "separate DECIDE replay and independent Pre-RESULT review."
)


def _count(value: Any, name: str, *, positive: bool = False) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer count")
    try:
        count = int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be an integer count") from exc
    try:
        if count != value:
            raise ValueError(f"{name} must be an integer count")
    except TypeError as exc:
        raise ValueError(f"{name} must be an integer count") from exc
    if count < (1 if positive else 0):
        qualifier = "positive " if positive else "nonnegative "
        raise ValueError(f"{name} must be a {qualifier}integer count")
    return count


def _finite_number(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(number) or (positive and number <= 0.0):
        qualifier = "positive finite" if positive else "finite"
        raise ValueError(f"{name} must be {qualifier}")
    return number


def _arm_replay(source: str, h_corr: float, arm: dict[str, Any]) -> dict[str, Any]:
    family = arm.get("family")
    if family not in ("hdc", "lb"):
        raise ValueError(f"{source}: unexpected arm family {family!r}")

    m = _count(arm.get("m"), f"{source}/{family}.m", positive=True)
    blocks = _count(arm.get("blocks_done"), f"{source}/{family}/m{m}.blocks_done",
                    positive=True)
    superframes = _count(
        arm.get("superframes_done"),
        f"{source}/{family}/m{m}.superframes_done", positive=True)
    sf_total = _count(arm.get("sf_total"), f"{source}/{family}/m{m}.sf_total",
                      positive=True)
    sf_success = _count(arm.get("sf_success"),
                        f"{source}/{family}/m{m}.sf_success")
    fer = _finite_number(arm.get("fer_blocks"),
                         f"{source}/{family}/m{m}.fer_blocks")
    if not 0.0 <= fer <= 1.0:
        raise ValueError(f"{source}/{family}/m{m}.fer_blocks must be in [0, 1]")

    if arm.get("verdict") != "COMPLETE":
        raise ValueError(f"{source}/{family}/m{m} is not a COMPLETE arm")
    if blocks != BLOCKS_PER_SUPERFRAME * superframes:
        raise ValueError(
            f"{source}/{family}/m{m}: blocks_done must equal "
            f"16*superframes_done ({blocks} != {BLOCKS_PER_SUPERFRAME}*{superframes})")
    if sf_total != superframes:
        raise ValueError(
            f"{source}/{family}/m{m}: sf_total must equal superframes_done")
    if sf_success > sf_total:
        raise ValueError(f"{source}/{family}/m{m}: sf_success exceeds sf_total")

    lambda_parts = arm.get("lambda_parts")
    if not isinstance(lambda_parts, dict):
        raise ValueError(f"{source}/{family}/m{m}.lambda_parts must be an object")
    ec_bits = _finite_number(lambda_parts.get("leak_EC"),
                             f"{source}/{family}/m{m}.lambda_parts.leak_EC")
    tag_bits = _finite_number(lambda_parts.get("tag"),
                              f"{source}/{family}/m{m}.lambda_parts.tag")
    if ec_bits < 0.0 or tag_bits < 0.0:
        raise ValueError(f"{source}/{family}/m{m}: disclosure bits cannot be negative")
    expected_tags = TAG_BITS_PER_BLOCK * blocks
    if tag_bits != expected_tags:
        raise ValueError(
            f"{source}/{family}/m{m}: recorded tag bits must equal "
            f"64*blocks_done ({tag_bits} != {TAG_BITS_PER_BLOCK}*{blocks})")

    denominator = superframes * SUPERFRAME_SYMBOLS * h_corr
    if not math.isfinite(denominator) or denominator <= 0.0:
        raise ValueError(f"{source}/{family}/m{m}: efficiency denominator is not positive")

    return {
        "source": source,
        "family": family,
        "m": m,
        "blocks_done": blocks,
        "superframes_done": superframes,
        "fer_blocks": fer,
        "sf_success": sf_success,
        "sf_total": sf_total,
        "original_f_labels": {label: arm.get(label) for label in F_LABELS},
        "leak_EC_bits_recorded": ec_bits,
        "tag_bits_recorded": tag_bits,
        "tags_per_superframe": tag_bits / (TAG_BITS_PER_BLOCK * superframes),
        "f_ec_actual": ec_bits / denominator,
        "f_with_recorded_tags": (ec_bits + tag_bits) / denominator,
        "f_if_one_tag_per_superframe": (
            ec_bits + TAG_BITS_PER_BLOCK * superframes) / denominator,
        "one_tag_per_superframe_value_is": "COUNTERFACTUAL_ONLY",
    }


def build_replay(paths: Sequence[str | Path]) -> dict[str, Any]:
    """Read exactly three explicit M2 summary paths and return diagnostic JSON data."""
    if len(paths) != len(SOURCE_ORDER):
        raise ValueError(f"exactly {len(SOURCE_ORDER)} rows.json paths are required")

    by_source: dict[str, dict[str, Any]] = {}
    roots: dict[str, str] = {}
    for path_value in paths:
        path = Path(path_value)
        with path.open("r", encoding="utf-8") as stream:
            payload = json.load(stream)
        summary = payload.get("summary") if isinstance(payload, dict) else None
        if not isinstance(summary, dict):
            raise ValueError(f"{path}: expected an object named 'summary'")
        source = summary.get("source")
        if source not in SOURCE_ORDER:
            raise ValueError(f"{path}: unexpected source {source!r}")
        if source in by_source:
            raise ValueError(f"duplicate source {source!r}")
        if summary.get("verdict") != "COMPLETE":
            raise ValueError(f"{path}: source {source} is not COMPLETE")

        h_corr = _finite_number(summary.get("H_corr"),
                                f"{source}.H_corr", positive=True)
        arms = summary.get("arms")
        if not isinstance(arms, list) or len(arms) != 4:
            raise ValueError(f"{source}: expected four HDC/LB arms")
        arm_rows = [_arm_replay(source, h_corr, arm) for arm in arms
                    if isinstance(arm, dict)]
        if len(arm_rows) != 4:
            raise ValueError(f"{source}: every arm must be an object")

        identities = [(row["family"], row["m"]) for row in arm_rows]
        if len(set(identities)) != 4:
            raise ValueError(f"{source}: duplicate family/m arm identity")
        families = {family for family, _ in identities}
        m_values = {m for _, m in identities}
        if families != {"hdc", "lb"} or len(m_values) != 2:
            raise ValueError(f"{source}: expected HDC and LB at the same two m values")
        if any((family, m) not in identities
               for family in families for m in m_values):
            raise ValueError(f"{source}: missing family/m arm identity")

        by_source[source] = {
            "source": source,
            "H_corr_bits_per_symbol": h_corr,
            "rows_json_path": str(path),
            "original_root_path": str(path.parent),
            "arms": sorted(arm_rows, key=lambda row: (row["m"], row["family"])),
        }

    if set(by_source) != set(SOURCE_ORDER):
        missing = sorted(set(SOURCE_ORDER) - set(by_source))
        raise ValueError(f"missing required source(s): {', '.join(missing)}")

    return {
        "status": "DIAGNOSTIC_UNREVIEWED",
        "formulas_and_units": {
            "D": "superframes_done * 1024 symbols/superframe * H_corr bits/symbol",
            "f_ec_actual": "recorded leak_EC bits / D",
            "f_with_recorded_tags": "(recorded leak_EC bits + recorded tag bits) / D",
            "tags_per_superframe": "recorded tag bits / (64 bits/tag * superframes_done)",
            "f_if_one_tag_per_superframe": (
                "(recorded leak_EC bits + 64 bits * superframes_done) / D; "
                "counterfactual only"),
        },
        "claim_ceiling": CLAIM_CEILING,
        "sources": [by_source[source] for source in SOURCE_ORDER],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print an unreviewed diagnostic replay from three explicit M2 rows.json paths.")
    parser.add_argument("rows_json", nargs=3, metavar="ROWS_JSON",
                        help="one explicit rows.json path for each M2 source")
    args = parser.parse_args(argv)
    print(json.dumps(build_replay(args.rows_json), indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
