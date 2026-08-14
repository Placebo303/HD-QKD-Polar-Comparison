import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import codebook_v4
from comparison_bench.src.comparison_bench.formal_ir import codebook_v5_h2 as h2
from comparison_bench.src.comparison_bench.formal_ir.ldpc_v5 import build_v5_policy_manifest, verify_v5_policy_manifest


def test_h2_v2_reconstructs_all_selected_planes_at_maximal_rank():
    selected = [0, 0, 0, 0, 0, 0, 2, 0, 2, 2]
    for plane, candidate in enumerate(selected):
        h1 = codebook_v4.matrix_for(plane, candidate)
        h, trial = h2.generate_h2(plane, h1)
        assert trial == 0
        assert codebook_v4.gf2_rank(h) == h.shape[0]
        assert codebook_v4.gf2_rank(np.vstack((h1, h))) == h1.shape[0] + h.shape[0] - 1
        assert np.array_equal(h2.parse_h2_bytes(h2.canonical_h2_bytes(h, plane_id=plane, h1=h1), plane_id=plane, h1=h1), h)


def test_h2_rejects_header_and_payload_tampering():
    h1 = codebook_v4.matrix_for(0, 0)
    matrix, _ = h2.generate_h2(0, h1)
    raw = h2.canonical_h2_bytes(matrix, plane_id=0, h1=h1)
    with pytest.raises(ValueError):
        h2.parse_h2_bytes(b"bad" + raw[3:], plane_id=0, h1=h1)
    altered = bytearray(raw)
    altered[-1] ^= 1
    with pytest.raises(ValueError):
        h2.parse_h2_bytes(bytes(altered), plane_id=0, h1=h1)


def test_h2_manifest_self_hash_and_tamper_rejection():
    selected = [0, 0, 0, 0, 0, 0, 2, 0, 2, 2]
    manifest = h2.h2_manifest(selected, h1_codebook_manifest_sha256="a" * 64, h1_selection_sha256="b" * 64)
    h2.verify_h2_manifest(manifest, selected)
    manifest["candidates"][0]["accepted_trial"] += 1
    with pytest.raises(ValueError):
        h2.verify_h2_manifest(manifest, selected)


def test_h2_all_frozen_trials_and_canonical_hashes():
    selected=[0,0,0,0,0,0,2,0,2,2]
    manifest=h2.h2_manifest(selected,h1_codebook_manifest_sha256="a"*64,h1_selection_sha256="b"*64)
    assert manifest["manifest_sha256"] == "2b56c77056823780af4f535a978fd7ab6ef4b538e3d1c2623ca623e4ca51ded5"
    assert [x["accepted_trial"] for x in manifest["candidates"]] == [0]*10
    assert [x["canonical_bytes_sha256"] for x in manifest["candidates"]] == [
        "fa16f4c2dcd4096622719ca0f5a37a5e6da42bc9b3cf42616fe1f41ff0353b52","c756d83571af5593024f8f58652585cf5d131e8e12fd1700f1ba78adc9535198","26c704bbd80e8b3c9ec2c3823329d8946b4da682778744a3d07fb4a0584e6846","a82d8a8a1262e7a16e17490fd02af99fff0791abb7369d69b1389a48a49fab66","0950115c75415549f84332e7850682bb1561cb3b7d0ae7f9fd18f33c51c3ab00","468047bb9e5f177d393b59b74dec8784d52c8993e1f27a8dc39bfcc53b0a504b","ebd475804ab3b34fbde8e0fa305325ed0da5dbfeac4a67239e1e4444988390c2","510a95d23b5b7ef9031dd760f4152bcf1fcdafd5ef8c93bddf096a707f45d8a6","1ddb1a71a2a11f9cc2c1c49bdb2eb57ebdab4806d151a6285a8674caf4b2799b","83a63ff0bba1acd5b42f23177fa6e67846ba46da9c74c0f090130b51c30de4b3"]
    for plane,entry in enumerate(manifest["candidates"]):
        h1=codebook_v4.matrix_for(plane,selected[plane]); matrix,_=h2.generate_h2(plane,h1)
        assert entry["h2_shape"] == [h2.H2_ROW_COUNTS[plane],256]
        assert entry["h2_column_weight_min"] == entry["h2_column_weight_max"] == 3
        assert entry["h2_zero_rows"] == 0
        assert entry["h2_rank"] == h2.H2_ROW_COUNTS[plane]
        assert entry["stacked_rank"] == codebook_v4.row_count(plane)+h2.H2_ROW_COUNTS[plane]-1
        # Accessors are detached and mutation cannot poison their cache.
        matrix[0,0] ^= 1
        fresh,_=h2.generate_h2(plane,h1)
        assert fresh[0,0] != matrix[0,0]


def test_policy_manifest_self_hash_and_tamper_rejection():
    selected = [0, 0, 0, 0, 0, 0, 2, 0, 2, 2]
    h2m = h2.h2_manifest(selected, h1_codebook_manifest_sha256="a" * 64, h1_selection_sha256="b" * 64)
    kwargs = dict(selected_candidates=selected, selection_sha256="b" * 64, codebook_manifest_sha256="a" * 64,
                  channel_model_sha256="c" * 64, h2_manifest=h2m)
    manifest = build_v5_policy_manifest(**kwargs)
    verify_v5_policy_manifest(manifest, **kwargs)
    manifest["candidates"][0]["caps"]["events"] = 31
    with pytest.raises(ValueError):
        verify_v5_policy_manifest(manifest, **kwargs)
