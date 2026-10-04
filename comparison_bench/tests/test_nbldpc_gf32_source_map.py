from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
import zipfile
import numpy as np
import pytest

from comparison_bench.cli import nbldpc_gf32_source_map as source_map


def _source_records():
    return [
        {
            "source_id": spec["source_id"],
            "pairs_parquet": source_map._expected_pairs_path(spec["source_id"]),
            **source_map.EXPECTED_ROLES,
        }
        for spec in source_map.SOURCE_SPECS
    ]


def _fake_provenance(tmp_path: Path, *, bad_role: bool = False):
    records = _source_records()
    if bad_role:
        records[0]["data_role"] = "qualification"
    inventory = {"primary_joint_data_sources": records}
    evidence_inventory = json.loads(json.dumps(inventory))
    split = {
        "split_ratios": [0.60, 0.20, 0.20],
        "per_source": {
            spec["source_id"]: {"pairs": {"train": spec["train_pairs"]}}
            for spec in source_map.SOURCE_SPECS
        },
    }
    upstream = {
        "sources": [
            {
                "source_tag": spec["source_id"],
                "pairs_parquet": {
                    "path": "D:\\Code\\HD-QKD_Polar_Comparison\\"
                    + source_map._expected_pairs_path(spec["source_id"])
                },
            }
            for spec in source_map.SOURCE_SPECS
        ]
    }
    documents = {
        "run_inventory": inventory,
        "split_manifest": split,
        "evidence_inventory": evidence_inventory,
        "build_manifest": upstream,
    }
    paths = {}
    for name, document in documents.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        paths[name] = path
    return paths, documents


def _fake_npz(path: Path, arrays=None):
    if arrays is None:
        arrays = {
            source_map.expected_npz_key(spec["source_id"]): np.zeros(
                source_map.ARRAY_SHAPE, dtype=np.float64
            )
            for spec in source_map.SOURCE_SPECS
        }
    np.savez_compressed(path, **arrays)
    return path


def test_validate_exact_documented_provenance_and_double_suffix_keys(tmp_path):
    _, documents = _fake_provenance(tmp_path)
    result = source_map.validate_provenance(documents)
    assert result["status"] == "PASS"
    assert result["provenance_level"] == "DOCUMENTED_TRAIN_ROLE_CONSISTENT"
    assert result["total_train_pairs"] == 1_292_032
    assert [source_map.expected_npz_key(s["source_id"]) for s in source_map.SOURCE_SPECS] == [
        "type2_1M_20260121_184040_N_ab_train_N_ab_train",
        "type2_1p5M_20260121_183806_N_ab_train_N_ab_train",
        "type2_2M_20260121_183657_N_ab_train_N_ab_train",
    ]


@pytest.mark.parametrize(
    "mutate",
    ["bad_role", "bad_split", "bad_train", "bad_path", "bad_source_tag", "bad_upstream_path"],
)
def test_provenance_gate_rejects_role_split_and_path_drift(tmp_path, mutate):
    _, docs = _fake_provenance(tmp_path)
    docs = json.loads(json.dumps(docs))
    if mutate == "bad_role":
        docs["run_inventory"]["primary_joint_data_sources"][0]["forbidden_uses"] = "none"
    elif mutate == "bad_split":
        docs["split_manifest"]["split_ratios"] = [0.5, 0.25, 0.25]
    elif mutate == "bad_train":
        docs["split_manifest"]["per_source"][source_map.SOURCE_SPECS[0]["source_id"]]["pairs"]["train"] += 1
    elif mutate == "bad_path":
        docs["evidence_inventory"]["primary_joint_data_sources"][0]["pairs_parquet"] = "other/pairs.parquet"
    elif mutate == "bad_source_tag":
        docs["build_manifest"]["sources"][0]["source_tag"] = "wrong-source"
    elif mutate == "bad_upstream_path":
        docs["build_manifest"]["sources"][0]["pairs_parquet"]["path"] = "D:\\other\\pairs.parquet"
    with pytest.raises(source_map.SourceGateError):
        source_map.validate_provenance(docs)


def test_header_inspection_accepts_only_exact_logical_keys_and_float64_c_order(tmp_path):
    path = _fake_npz(tmp_path / "counts.npz")
    headers = source_map.inspect_npz_headers(path)
    assert list(headers) == [source_map.expected_npz_key(s["source_id"]) for s in source_map.SOURCE_SPECS]
    assert all(header["shape"] == [1024, 1024] for header in headers.values())
    assert all(header["dtype"] in ("<f8", "=f8") for header in headers.values())
    assert all(header["fortran_order"] is False for header in headers.values())


def test_header_inspection_does_not_need_array_payload(tmp_path):
    path = tmp_path / "header_only.npz"
    with zipfile.ZipFile(path, "w") as archive:
        for spec in source_map.SOURCE_SPECS:
            header = BytesIO()
            np.lib.format.write_array_header_1_0(
                header,
                {
                    "descr": np.lib.format.dtype_to_descr(np.dtype(np.float64)),
                    "fortran_order": False,
                    "shape": source_map.ARRAY_SHAPE,
                },
            )
            archive.writestr(
                source_map.expected_npz_key(spec["source_id"]) + ".npy",
                header.getvalue() + b"truncated-payload-is-not-read",
            )
    headers = source_map.inspect_npz_headers(path)
    assert len(headers) == 3
    assert all(header["shape"] == [1024, 1024] for header in headers.values())


def test_header_gate_rejects_missing_extra_and_wrong_profile(tmp_path):
    keys = [source_map.expected_npz_key(s["source_id"]) for s in source_map.SOURCE_SPECS]
    missing = tmp_path / "missing.npz"
    np.savez(missing, **{keys[0]: np.zeros((1024, 1024)), keys[1]: np.zeros((1024, 1024))})
    with pytest.raises(source_map.SourceGateError):
        source_map.inspect_npz_headers(missing)

    extra = tmp_path / "extra.npz"
    np.savez(extra, **{**{k: np.zeros((1024, 1024)) for k in keys}, "extra": np.zeros(1)})
    with pytest.raises(source_map.SourceGateError):
        source_map.inspect_npz_headers(extra)

    wrong_shape = tmp_path / "wrong_shape.npz"
    np.savez(wrong_shape, **{**{k: np.zeros((1024, 1024)) for k in keys}, keys[2]: np.zeros((10, 10))})
    with pytest.raises(source_map.SourceGateError):
        source_map.inspect_npz_headers(wrong_shape)

    wrong_dtype = tmp_path / "wrong_dtype.npz"
    np.savez(wrong_dtype, **{k: np.zeros((1024, 1024), dtype=np.int64) for k in keys})
    with pytest.raises(source_map.SourceGateError, match="dtype"):
        source_map.inspect_npz_headers(wrong_dtype)

    fortran = tmp_path / "fortran.npz"
    np.savez(fortran, **{
        k: np.asfortranarray(np.zeros((1024, 1024), dtype=np.float64)) for k in keys
    })
    with pytest.raises(source_map.SourceGateError, match="C-order"):
        source_map.inspect_npz_headers(fortran)


@pytest.mark.parametrize(
    "values, message",
    [
        (np.zeros((3, 3), dtype=np.float64), "shape"),
        (np.zeros((1024, 1024), dtype=np.int64), "float64"),
        (np.full((1024, 1024), np.nan, dtype=np.float64), "non-finite"),
        (np.full((1024, 1024), -1.0, dtype=np.float64), "negative"),
        (np.full((1024, 1024), 0.5, dtype=np.float64), "fractional"),
    ],
)
def test_value_gate_rejects_invalid_fake_count_arrays(values, message):
    with pytest.raises(source_map.CountValueError, match=message):
        source_map.validate_count_values(values, 1)


def test_value_gate_rejects_wrong_total():
    values = np.zeros((1024, 1024), dtype=np.float64)
    values[0, 0] = 6
    with pytest.raises(source_map.CountValueError, match="differs from frozen train total"):
        source_map.validate_count_values(values, 7)


def test_high_five_bit_xor_mapping_conserves_counts_and_ignores_low_bits():
    values = np.zeros((1024, 1024), dtype=np.float64)
    values[0, 0] = 7
    values[1, 30] = 3  # same U1 on both sides: low bits do not affect E1
    values[32, 0] = 5
    values[0, 32 * 7 + 31] = 11
    values[32 * 17 + 5, 32 * 9 + 2] = 13
    result = source_map.summarize_source_counts(values, "fake", "fake", 39)
    # 17 XOR 9 = 24; totals: 0->10, 1->5, 7->11, 24->13.
    expected = [0] * 32
    expected[0], expected[1], expected[7], expected[24] = 10, 5, 11, 13
    assert result["E1_counts"] == expected
    assert result["N"] == sum(expected) == 39
    assert sum(result["E1_pmf"]) == pytest.approx(1.0)
    assert result["n_zero"] == 10
    assert result["n_nonzero"] == 29
    assert result["observed_B_columns"] == 4
    assert result["error_bearing_B_columns"] == 3
    assert "conditional_counts" not in result


def test_bob_conditional_entropy_and_mutual_information():
    values = np.zeros((1024, 1024), dtype=np.float64)
    values[0, 0] = 3
    values[32, 0] = 1
    values[32, 32] = 4
    result = source_map.summarize_source_counts(values, "fake", "fake", 8)
    expected_h = -(7 / 8) * np.log2(7 / 8) - (1 / 8) * np.log2(1 / 8)
    expected_cond = 0.5 * (-(3 / 4) * np.log2(3 / 4) - (1 / 4) * np.log2(1 / 4))
    assert result["H_E1_bits"] == pytest.approx(expected_h)
    assert result["H_E1_given_B_bits"] == pytest.approx(expected_cond)
    assert result["I_E1_B_bits"] == pytest.approx(expected_h - expected_cond)


def test_zero_nonzero_error_tv_is_null_but_zero_error_mass_is_reported():
    values = np.zeros((1024, 1024), dtype=np.float64)
    values[1, 30] = 6  # both U1 symbols are zero
    result = source_map.summarize_source_counts(values, "fake", "fake", 6)
    assert result["n_zero"] == 6
    assert result["n_nonzero"] == 0
    assert result["nonzero_tv"] is None
    assert result["conditional_nonzero_tv_weighted"] is None
    assert result["error_bearing_B_columns"] == 0
    assert result["error_bearing_B_columns_lt5"] == 0
    assert result["error_bearing_B_columns_lt20"] == 0


def test_nonzero_tv_and_bob_weighted_tv_for_single_error_symbol():
    values = np.zeros((1024, 1024), dtype=np.float64)
    values[32, 0] = 4
    result = source_map.summarize_source_counts(values, "fake", "fake", 4)
    expected_tv = 30 / 31
    assert result["nonzero_tv"] == pytest.approx(expected_tv)
    assert result["conditional_nonzero_tv_weighted"] == pytest.approx(expected_tv)
    assert result["error_bearing_B_columns_lt5"] == 1
    assert result["error_bearing_B_columns_lt20"] == 1


def test_invalid_provenance_stops_before_npz_value_loader(tmp_path):
    provenance_paths, documents = _fake_provenance(tmp_path, bad_role=True)
    npz = _fake_npz(tmp_path / "counts.npz")
    del documents  # run_batch reads only the fake provenance files above
    result = source_map.run_batch(
        counts_path=npz,
        provenance_paths=provenance_paths,
        out_root=tmp_path / "result",
        source_specs=source_map.SOURCE_SPECS,
        load_member=lambda path, key: (_ for _ in ()).throw(
            AssertionError("value read")
        ),
    )
    assert result["status"] == "SOURCE_OR_SPLIT_UNRESOLVED"
    assert result["attempted_sources"] == []
    assert sorted(p.name for p in (tmp_path / "result").iterdir()) == [
        "RESULT_LOG.md", "manifest.json", "source_summary.json"
    ]


def test_value_mismatch_retains_incomplete_root_and_stops_before_next_source(tmp_path):
    provenance_paths, _ = _fake_provenance(tmp_path)
    npz = _fake_npz(tmp_path / "counts.npz")
    calls = []

    def loader(path, key):
        calls.append(key)
        return source_map._load_one_npz_member(path, key)

    out_root = tmp_path / "count_mismatch"
    result = source_map.run_batch(
        counts_path=npz,
        provenance_paths=provenance_paths,
        out_root=out_root,
        load_member=loader,
    )
    first = source_map.SOURCE_SPECS[0]
    assert result["status"] == "INCOMPLETE_COUNT_VALUE_MISMATCH"
    assert result["attempted_sources"] == [first["source_id"]]
    assert result["stop_code"] == "COUNT_VALUE_MISMATCH"
    assert calls == [source_map.expected_npz_key(first["source_id"])]
    assert result["resource_checks"][-1]["phase"] == "after_failed"
    summary = json.loads((out_root / "source_summary.json").read_text(encoding="utf-8"))
    assert summary["per_source"] == []


def test_resource_stop_happens_before_first_count_value(tmp_path):
    provenance_paths, _ = _fake_provenance(tmp_path)
    npz = _fake_npz(tmp_path / "counts.npz")
    ticks = iter((0.0, 61.0, 61.1))
    result = source_map.run_batch(
        counts_path=npz,
        provenance_paths=provenance_paths,
        out_root=tmp_path / "resource_stop",
        clock=lambda: next(ticks),
        rss_bytes=lambda: 1024,
        load_member=lambda path, key: (_ for _ in ()).throw(
            AssertionError("value read after wall cap")
        ),
    )
    assert result["status"] == "INCOMPLETE_RESOURCE_STOP"
    assert result["stop_code"] == "WALL_BUDGET_EXCEEDED"
    assert result["attempted_sources"] == []


def test_dry_run_reads_and_writes_nothing(tmp_path, capsys):
    out_root = tmp_path / "must_not_exist"
    with patch.object(source_map.np, "load", side_effect=AssertionError("NPZ read")):
        assert source_map.main(["--out-root", str(out_root)]) == 0
    assert not out_root.exists()
    assert "no provenance or NPZ reads" in capsys.readouterr().out


def test_fake_batch_writes_only_three_root_files_and_per_source_summaries(tmp_path):
    provenance_paths, _ = _fake_provenance(tmp_path)
    arrays = {}
    for spec in source_map.SOURCE_SPECS:
        arr = np.zeros((1024, 1024), dtype=np.float64)
        arr[0, 0] = float(spec["train_pairs"])
        arrays[source_map.expected_npz_key(spec["source_id"])] = arr
    npz = _fake_npz(tmp_path / "fake_counts.npz", arrays)
    out_root = tmp_path / "fake_result"
    result = source_map.run_batch(
        counts_path=npz,
        provenance_paths=provenance_paths,
        out_root=out_root,
    )
    assert result["status"] == "DESCRIPTIVE_MAPPING_COMPLETE"
    assert result["admitted_sources"] == [s["source_id"] for s in source_map.SOURCE_SPECS]
    assert result["attempted_sources"] == result["admitted_sources"]
    assert sorted(p.name for p in out_root.iterdir()) == [
        "RESULT_LOG.md", "manifest.json", "source_summary.json"
    ]
    summary = json.loads((out_root / "source_summary.json").read_text(encoding="utf-8"))
    assert len(summary["per_source"]) == 3
    assert all(item["n_nonzero"] == 0 for item in summary["per_source"])
    assert all(item["nonzero_tv"] is None for item in summary["per_source"])
    serialized = json.dumps(summary)
    assert "conditional_counts" not in serialized


def test_existing_output_root_is_refused(tmp_path):
    out_root = tmp_path / "existing"
    out_root.mkdir()
    with pytest.raises(FileExistsError):
        source_map.run_batch(
            counts_path=tmp_path / "unused.npz",
            provenance_paths={},
            out_root=out_root,
        )
