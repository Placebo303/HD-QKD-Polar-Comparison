"""Fake-only checks for the stdout-only M2 accounting replay."""

import json

import pytest

from comparison_bench.src.comparison_bench.cli.m2_accounting_replay import (
    build_replay,
    main,
)


SOURCES = ("1M", "1p5M", "2M")


def _summary(source, *, blocks=32, superframes=2, tag_bits=None,
             h_corr=0.8, verdict="COMPLETE"):
    if tag_bits is None:
        tag_bits = 64 * blocks
    arms = []
    for family in ("hdc", "lb"):
        for m in (197, 201):
            arms.append({
                "family": family,
                "m": m,
                "blocks_done": blocks,
                "superframes_done": superframes,
                "fer_blocks": 0.25,
                "sf_success": 1,
                "sf_total": superframes,
                "verdict": "COMPLETE",
                "f_super": 1.25,
                "f_notag": 1.17,
                "f_eff": 2.44,
                "lambda_parts": {
                    "leak_EC": 100 + m,
                    "tag": tag_bits,
                    "rescue": 0,
                    "control": 0,
                },
            })
    return {"summary": {
        "source": source,
        "verdict": verdict,
        "H_corr": h_corr,
        "arms": arms,
    }}


def _write_inputs(tmp_path, summaries):
    paths = []
    for source, summary in summaries.items():
        path = tmp_path / source / "rows.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(summary), encoding="utf-8")
        paths.append(path)
    return paths


def test_replay_reports_measured_and_counterfactual_tag_formulas_by_source(tmp_path):
    summaries = {source: _summary(source) for source in SOURCES}
    paths = _write_inputs(tmp_path, summaries)

    report = build_replay([paths[2], paths[0], paths[1]])

    assert report["status"] == "DIAGNOSTIC_UNREVIEWED"
    assert [row["source"] for row in report["sources"]] == list(SOURCES)
    first_source = report["sources"][0]
    assert first_source["rows_json_path"] == str(paths[0])
    assert len(first_source["arms"]) == 4
    assert [(arm["family"], arm["m"]) for arm in first_source["arms"]] == [
        ("hdc", 197), ("lb", 197), ("hdc", 201), ("lb", 201),
    ]

    arm = first_source["arms"][0]
    denominator = 2 * 1024 * 0.8
    ec_bits = 100 + 197
    tag_bits = 64 * 32
    assert arm["f_ec_actual"] == pytest.approx(ec_bits / denominator)
    assert arm["f_with_recorded_tags"] == pytest.approx(
        (ec_bits + tag_bits) / denominator)
    assert arm["tag_bits_recorded"] == tag_bits
    assert arm["tags_per_superframe"] == pytest.approx(16.0)
    assert arm["f_if_one_tag_per_superframe"] == pytest.approx(
        (ec_bits + 64 * 2) / denominator)
    assert arm["one_tag_per_superframe_value_is"] == "COUNTERFACTUAL_ONLY"
    assert arm["original_f_labels"] == {
        "f_super": 1.25,
        "f_notag": 1.17,
        "f_eff": 2.44,
    }
    assert "f_eff_actual" not in arm


def test_cli_writes_json_to_stdout_without_creating_output_files(tmp_path, capsys):
    paths = _write_inputs(
        tmp_path, {source: _summary(source) for source in SOURCES})
    before = {path for path in tmp_path.rglob("*") if path.is_file()}

    assert main([str(path) for path in paths]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out)["status"] == "DIAGNOSTIC_UNREVIEWED"
    assert {path for path in tmp_path.rglob("*") if path.is_file()} == before


@pytest.mark.parametrize(
    ("summary_kwargs", "message"),
    [
        ({"blocks": 31}, "blocks_done must equal"),
        ({"tag_bits": 64 * 32 - 64}, "recorded tag bits must equal"),
        ({"superframes": 0}, "superframes_done must be a positive"),
        ({"h_corr": 0}, "H_corr must be positive finite"),
        ({"verdict": "INCOMPLETE-wall"}, "source 1M is not COMPLETE"),
    ],
)
def test_replay_rejects_incomplete_or_inconsistent_units(
        tmp_path, summary_kwargs, message):
    summaries = {source: _summary(source) for source in SOURCES}
    summaries["1M"] = _summary("1M", **summary_kwargs)
    paths = _write_inputs(tmp_path, summaries)

    with pytest.raises(ValueError, match=message):
        build_replay(paths)


def test_replay_rejects_duplicate_source_and_duplicate_arm(tmp_path):
    one = tmp_path / "one.json"
    two = tmp_path / "two.json"
    three = tmp_path / "three.json"
    one.write_text(json.dumps(_summary("1M")), encoding="utf-8")
    two.write_text(json.dumps(_summary("1M")), encoding="utf-8")
    three.write_text(json.dumps(_summary("2M")), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate source '1M'"):
        build_replay([one, two, three])

    duplicate_arm = _summary("1M")
    duplicate_arm["summary"]["arms"][3]["m"] = 197
    one.write_text(json.dumps(duplicate_arm), encoding="utf-8")
    middle = tmp_path / "middle.json"
    middle.write_text(json.dumps(_summary("1p5M")), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate family/m arm identity"):
        build_replay([one, middle, three])
