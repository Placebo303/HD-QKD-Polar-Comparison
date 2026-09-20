"""V80 O1 superframe-as-code campaign executor tests (EXPLORE, FAKE-ONLY).

Frozen spec: O1_EXPERIMENT_PACKET_20260920.md (G-O1, two arms A188|A208,
single n=1024 code, 60 blocks = 60 decodes). Every test injects fake
construct/decode/de_fn/clock/rss/writer or synthetic dict bundles — zero
production ``construct_arm`` / ``decode_block_empirical`` / gamma-file
loads, zero campaign disk writes (the writer is an in-memory capture;
resume/de-precheck shims use tmp_path and are removed by pytest).
Wall: milliseconds, except one dry gate-binding test (T15, ~seconds).
"""
import inspect
import json
import os

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import (
    v80_o1_campaign as c,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v10_common as common,
)


def _fake_bundle(seed=7):
    rng = np.random.default_rng(seed)
    g1 = rng.random((32, 1024)) + 0.01
    g1 = g1 / g1.sum(axis=0, keepdims=True)
    g2 = rng.random((32, 32, 1024)) + 0.01
    g2 = g2 / g2.sum(axis=1, keepdims=True)
    return {"g1": g1, "g2": g2,
            "p_b": np.full(1024, 1.0 / 1024), "source": "2M"}


def _fake_construct(arm):
    # Mirrors the frozen pin table (packet §2): fc=0/girth=8/rank-full
    # both arms; stable triples exercise construct-twice-identical.
    # Signature mirrors production construct_arm(arm, seed, max_trials) and
    # asserts the gate forwards the arm first (fake-mask regression guard).
    table = {"A188": 188, "A208": 208}
    m = table[arm]

    def _build(arm_in, seed, max_trials):
        assert (arm_in, seed, max_trials) == (arm, 2026092001, 20)
        return {"four_cycles": 0, "min_girth": 8, "rank": m,
                "family": "peg-irregular", "n": 1024, "m": m,
                "triples": [(0, 0, 1), (1, 1, 2)],
                "total_sockets": 2048, "parallel_edges": 0}

    return _build


def _decode_ok(construction, seed):
    return {"status": "success", "iterations": 10,
            "reconstruction_ok": True, "exact_match": True}


def _decode_fail(construction, seed):
    return {"status": "max_iter_reached", "iterations": 300,
            "reconstruction_ok": False, "exact_match": False}


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class MemWriter:
    """In-memory capture: path -> blob. Never touches disk."""

    def __init__(self):
        self.store = {}
        self.calls = 0

    def __call__(self, root, files):
        self.calls += 1
        for name, blob in files.items():
            self.store[f"{root}/{name}"] = blob


def _run(root, writer, clock, decode_fn, arm="A188", **kw):
    return c.execute(root=root, arm=arm,
                     construct_fn=_fake_construct(arm),
                     decode_fn=decode_fn, clock=clock,
                     rss_fn=lambda: 0, writer=writer, **kw)


# T1: dual-flag gate + arm/root/de-label refusal matrix (rc2 pre-anything).
def test_t1_dual_flag_refusal():
    with pytest.raises(c.Refusal):
        c.main([])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--arm", "A188",
                "--root", "workspace/o1_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execution-authorized", "--arm", "A188",
                "--root", "workspace/o1_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "A188", "--root", "workspace/wrong_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "A188", "--root", "workspace/s2c_deadbeef"])
    for bad_arm in ("L-A", "A189", "a188", ""):
        with pytest.raises(c.Refusal):
            c.main(["--execute-real", "--execution-authorized",
                    "--arm", bad_arm,
                    "--root", "workspace/o1_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "A188", "--root", "workspace/o1_aaaaaaaa",
                "--resume-from", "workspace/o1_bbbbbbbb"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "A188", "--root", "workspace/o1_deadbeef",
                "--de-label", "maybe"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "A188", "--root", "workspace/o1_deadbeef",
                "--de-precheck", "--resume-from",
                "workspace/o1_deadbeef"])


# T2: root absent/present matrix. ----------------------------------------
def test_t2_root_absent_present_matrix(tmp_path):
    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/o1_fake_absent_01", w, clk, _decode_ok,
              max_blocks=1)
    assert mf["verdict"] == "PROBE-truncated"
    with pytest.raises(c.Refusal):
        _run(str(tmp_path), MemWriter(), FakeClock(), _decode_ok,
             max_blocks=1)
    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/o1_fake_absent_02",
                  arm="A188",
                  resume_from="/tmp/opencode/o1_fake_absent_02",
                  construct_fn=_fake_construct("A188"),
                  decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0, writer=MemWriter())
    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/o1_fake_a",
                  arm="A188",
                  resume_from="/tmp/opencode/o1_fake_b",
                  construct_fn=_fake_construct("A188"),
                  decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0, writer=MemWriter())


# T3: per-arm pin gates (fc=0/girth=8/rank-full both arms). ---------------
@pytest.mark.parametrize("arm,m", [("A188", 188), ("A208", 208)])
def test_t3_per_arm_pins_pass(arm, m):
    assert c.ARMS[arm]["four_cycles"] == 0
    assert c.ARMS[arm]["min_girth"] == 8
    assert c.ARMS[arm]["rank"] == m
    w, clk = MemWriter(), FakeClock()
    mf = _run(f"/tmp/opencode/o1_fake_pins_{arm.lower()}", w, clk,
              _decode_ok, arm=arm, max_blocks=1)
    assert mf["verdict"] == "PROBE-truncated"
    assert mf["arm"] == arm


@pytest.mark.parametrize("arm,m", [("A188", 188), ("A208", 208)])
@pytest.mark.parametrize("pin", ["fc", "girth", "rank", "status"])
def test_t3_pin_mismatch_stop_blocked(arm, m, pin, capsys):
    vals = {"four_cycles": 0, "min_girth": 8, "rank": m}
    if pin == "fc":
        vals["four_cycles"] = 1
    elif pin == "girth":
        vals["min_girth"] = 6
    elif pin == "rank":
        vals["rank"] = m - 1

    def _bad(arm_in, seed, max_trials):
        rec = {"four_cycles": vals["four_cycles"],
               "min_girth": vals["min_girth"], "rank": vals["rank"],
               "family": "peg-irregular"}
        if pin == "status":
            rec["status"] = "frozen_failure"
        return rec

    calls = []

    def _counting(construction, seed):
        calls.append(seed)
        return _decode_ok(construction, seed)

    with pytest.raises(c.Refusal) as exc:
        c.execute(root=f"/tmp/opencode/o1_fake_pins_{arm.lower()}",
                  arm=arm, construct_fn=_bad, decode_fn=_counting,
                  clock=FakeClock(), rss_fn=lambda: 0,
                  writer=MemWriter(), max_blocks=1)
    assert exc.value.code == 2
    assert "STOP-BLOCKED" in capsys.readouterr().err
    assert calls == []  # fail closed pre-decode


# T4: construct-twice-identity. -------------------------------------------
def test_t4_construct_twice_identity():
    def _drifting(arm_in, seed, max_trials):
        _drifting.n += 1
        return {"four_cycles": 0, "min_girth": 8, "rank": 188,
                "family": "peg-irregular",
                "triples": [(0, _drifting.n, 1)]}
    _drifting.n = 0
    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/o1_fake_twice", arm="A188",
                  construct_fn=_drifting, decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0,
                  writer=MemWriter(), max_blocks=1)


# T5: bundle binding gates + zero-mass fallback (helpers reused from s2c).
def test_t5_bundle_binding_gates():
    good = _fake_bundle()
    bound = c.s2c.bind_empirical_bundle(dict(good))
    assert bound["g1"].shape == (32, 1024)
    assert bound["g2"].shape == (32, 32, 1024)
    assert bound["p_b"].shape == (1024,)
    bad_pb = dict(good, p_b=good["p_b"] * 2.0)
    with pytest.raises(c.s2c.Refusal):
        c.s2c.bind_empirical_bundle(bad_pb)
    missing = {"g1": good["g1"], "g2": good["g2"]}
    with pytest.raises(c.s2c.Refusal):
        c.s2c.bind_empirical_bundle(missing)


def test_t5_zero_mass_fallback_delta_at_0():
    g1 = np.full((32, 1024), 1.0 / 32)
    g1[:, 7] = 0.0
    g2 = np.full((32, 32, 1024), 1.0 / 32)
    g2[5, :, 9] = 0.0
    bundle = {"g1": g1, "g2": g2,
              "p_b": np.full(1024, 1.0 / 1024)}
    rows = c.s2c.posterior_rows_l2(bundle, np.array([7, 9]),
                                   np.array([5, 5]))
    assert rows[0, 0] == pytest.approx(1.0) and rows[0, 1:].sum() == 0.0
    assert rows[1, 0] == pytest.approx(1.0) and rows[1, 1:].sum() == 0.0
    delta_pb = {"g1": g1, "g2": g2,
                "p_b": np.array([1.0 if i == 7 else 0.0
                                 for i in range(1024)])}
    b, u1, u2 = c.s2c.empirical_triple_sampler(
        delta_pb, 16, np.random.default_rng(1))
    assert set(b.tolist()) == {7}
    assert set(u1.tolist()) == {0}


# T6: sampler determinism + frozen stream/seed pins. -----------------------
def test_t6_sampler_stream_pins():
    bundle = _fake_bundle()
    r1 = np.random.default_rng(42)
    r2 = np.random.default_rng(42)
    t1 = c.s2c.empirical_triple_sampler(bundle, 64, r1)
    t2 = c.s2c.empirical_triple_sampler(bundle, 64, r2)
    for a, b_ in zip(t1, t2):
        assert np.array_equal(a, b_)
    assert c.stream_seed(2026095501) == common.v10_seed("o1_blk:2026095501")
    # Distinct domain from the S2c s2c_emp: stream.
    assert (common.v10_seed("o1_blk:2026095501")
            != common.v10_seed("s2c_emp:2026095501"))
    # Frozen literal seeds (packet §5): 2026095501+idx, idx=0..59.
    assert c.block_seed("A188", 0) == 2026095501
    assert c.block_seed("A208", 59) == 2026095501 + 59
    assert c.O1_BLOCK_BASE == 2026095501
    assert c.O1_CONSTRUCT_SEED == 2026092001
    assert c.N_BLOCKS == 60
    for bad in ("L-A", "A189", "A209"):
        with pytest.raises(c.Refusal) as exc:
            c.block_seed(bad, 0)
        assert exc.value.code == 2


# T7: posterior/center normalization + XOR-centering identity (n=1024). ----
def test_t7_posterior_center_math():
    bundle = _fake_bundle()
    rng = np.random.default_rng(3)
    b = rng.choice(1024, size=1024, p=bundle["p_b"])
    u1 = rng.integers(0, 32, size=1024)
    rows = c.s2c.posterior_rows_l2(bundle, b, u1)
    assert rows.shape == (1024, 32)
    assert np.allclose(rows.sum(axis=1), 1.0, atol=1e-9)
    y = (b & 31).astype(np.int64)
    prior = c.s2c.center_rows_prior(rows, y)
    assert prior.shape == (1024, 32)
    assert np.allclose(prior.sum(axis=1), 1.0, atol=1e-9)
    ee = np.arange(32, dtype=np.int64)
    for i in (0, 511, 1023):
        assert np.allclose(prior[i], rows[i, y[i] ^ ee])


# T8: block decode wiring — posterior entrypoint, (1024,m) prior, 300. ----
@pytest.mark.parametrize("arm,m", [("A188", 188), ("A208", 208)])
def test_t8_block_decode_wiring_posterior_entrypoint(monkeypatch, arm, m):
    bundle = _fake_bundle()
    seen = {}

    def _fake_dense(triples, n, mm, field):
        assert (n, mm) == (1024, m)
        return np.zeros((mm, n), dtype=np.int64)

    def _fake_syn(field, dense, vec):
        assert len(vec) == 1024
        return [0] * m

    def _fake_posterior(field, y, matrix, s_x, prior, max_iter,
                        **kw):
        seen.setdefault("calls", []).append(
            {"y": list(y), "s_x": list(s_x),
             "prior_shape": tuple(np.asarray(prior).shape),
             "prior_rowsums": np.asarray(prior).sum(axis=1),
             "max_iter": max_iter})
        assert tuple(np.asarray(prior).shape) == (1024, 32)
        return {"status": "success", "iterations": 7,
                "reconstruction_ok": True, "x_hat": list(y)}

    monkeypatch.setattr(c.peg, "sparse_to_dense", _fake_dense)
    monkeypatch.setattr(c.fftqspa, "syndrome_of", _fake_syn)
    monkeypatch.setattr(c.v28, "decode_error_domain_posterior",
                        _fake_posterior)
    construction = {"triples": [(0, 0, 1)], "n": 1024, "m": m}
    out = c.decode_block_empirical(construction, 2026095501, bundle,
                                   1024, m)
    assert len(seen["calls"]) == 1
    call = seen["calls"][0]
    assert call["max_iter"] == 300
    assert all(0 <= v < 32 for v in call["y"])
    assert np.allclose(call["prior_rowsums"], 1.0, atol=1e-9)
    assert out["max_iter"] == 300
    assert out["l1_conditioning"].startswith("GENIE")
    # The scalar-p decode_error_domain path is never called here: the
    # module source references decode_error_domain only with the
    # _posterior suffix (plus NEVER-used-here comments).
    src = inspect.getsource(c)
    bare = [ln for ln in src.splitlines()
            if "decode_error_domain(" in ln
            and "decode_error_domain_posterior" not in ln
            and "NEVER" not in ln and "scalar" not in ln]
    assert bare == []


def test_t8_construction_nm_wiring_guard():
    bundle = _fake_bundle()
    with pytest.raises(c.Refusal):
        c.decode_block_empirical({"triples": [], "n": 1024, "m": 188},
                                 2026095501, bundle, 1024, 208)
    with pytest.raises(c.Refusal):
        c.decode_block_empirical({"triples": [], "n": 256, "m": 47},
                                 2026095501, bundle, 1024, 188)


# T9: all-ok per arm → PASS; paired block seeds across arms. ---------------
def test_t9_all_ok_pass_and_paired_seeds():
    seqs = {}
    for arm in ("A188", "A208"):
        w, clk = MemWriter(), FakeClock()
        seen = []

        def _rec(construction, seed, _s=seen):
            _s.append(seed)
            return _decode_ok(construction, seed)

        mf = c.execute(root=f"/tmp/opencode/o1_fake_allok_{arm}",
                       arm=arm, construct_fn=_fake_construct(arm),
                       decode_fn=_rec, clock=clk,
                       rss_fn=lambda: 0, writer=w)
        assert mf["verdict"] == "PASS"
        assert mf["failures"] == 0
        assert mf["blocks_completed"] == 60
        assert mf["ledger"] == {"decodes": 60, "blocks_completed": 60}
        assert mf["fer_blocks"] == pytest.approx(0.0)
        rows = json.loads(
            w.store[f"/tmp/opencode/o1_fake_allok_{arm}/rows.json"])
        assert len(rows) == 60
        assert [r["block"] for r in rows] == list(range(60))
        assert all(r["block_accept"] for r in rows)
        assert w.calls == 61  # 60 block checkpoints + 1 final
        assert mf["verify"] == {"pins_ok": True, "ledger_ok": True,
                                "rows_ok": True}
        assert len(mf["wall_windows"]) == 1
        assert mf["resume"] == {"continuations_used": 0,
                                "max_continuations": 1}
        seqs[arm] = seen
    assert seqs["A188"] == seqs["A208"]
    assert seqs["A188"][0] == 2026095501
    assert seqs["A188"][-1] == 2026095501 + 59
    assert len(seqs["A188"]) == 60


# T10: early-stop at the 4th block failure (single-code semantics). --------
def test_t10_early_stop_fourth_failure():
    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/o1_fake_early", w, clk, _decode_fail)
    assert mf["verdict"] == "FAIL-early-stop"
    assert mf["blocks_completed"] == 4
    assert mf["failures"] == 4
    assert mf["ledger"]["decodes"] == 4  # one decode per block, no grouping
    assert mf["next_block"] == 4
    assert mf["partial"] is True


# T11: checkpoint/resume — one wall-partial continuation; 2nd refuses. ----
def test_t11_resume_continuation_single_wall_window(tmp_path):
    root = str(tmp_path / "o1_fake_resume")
    w1, clk1 = MemWriter(), FakeClock()

    def _advancing(construction, seed):
        clk1.t += 100.0
        return _decode_ok(construction, seed)

    part = c.execute(root=root, arm="A188",
                     construct_fn=_fake_construct("A188"),
                     decode_fn=_advancing, clock=clk1,
                     rss_fn=lambda: 0, writer=w1)
    assert part["verdict"] == "INCOMPLETE-wall"
    assert part["blocks_completed"] == 37
    assert part["next_block"] == 37
    assert part["ledger"]["decodes"] == 37
    rows_p = json.loads(w1.store[f"{root}/rows.json"])
    w2, clk2 = MemWriter(), FakeClock()

    def _fast(construction, seed):
        clk2.t += 1.0
        return _decode_ok(construction, seed)

    import os as _os
    _os.makedirs(root, exist_ok=True)
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w1.store[f"{root}/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w1.store[f"{root}/rows.json"])
    done = c.execute(root=root, arm="A188",
                     resume_from=root,
                     construct_fn=_fake_construct("A188"),
                     decode_fn=_fast, clock=clk2,
                     rss_fn=lambda: 0, writer=w2)
    assert done["verdict"] == "PASS"
    assert done["ledger"]["decodes"] == 60
    assert done["blocks_completed"] == 60
    assert len(done["wall_windows"]) == 2
    assert done["resume"] == {"continuations_used": 1,
                              "max_continuations": 1}
    rows_d = json.loads(w2.store[f"{root}/rows.json"])
    assert (json.dumps(rows_d[:37], sort_keys=True)
            == json.dumps(rows_p, sort_keys=True))
    # A resumed-twice partial (2 windows) refuses with zero decodes.
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w2.store[f"{root}/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w2.store[f"{root}/rows.json"])
    calls = []

    def _counting(construction, seed):
        calls.append(seed)
        return _decode_ok(construction, seed)

    with pytest.raises(c.Refusal) as exc:
        c.execute(root=root, arm="A188", resume_from=root,
                  construct_fn=_fake_construct("A188"),
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter())
    assert exc.value.code == 2
    assert calls == []


# T12: no writes outside root; forbidden trees refuse; csv present. --------
def test_t12_no_writes_outside_root():
    w, clk = MemWriter(), FakeClock()
    root = "/tmp/opencode/o1_fake_nowrite"
    _run(root, w, clk, _decode_ok, max_blocks=1)
    assert set(w.store) == {f"{root}/manifest.json", f"{root}/rows.json",
                            f"{root}/block_accounting.csv"}
    assert w.store[f"{root}/block_accounting.csv"].splitlines()[0] == (
        "block,seed,exact_match,status,iterations,wall_s,d_blind,"
        "leak_bits,f_super")
    for bad in ("/tmp/opencode/results/o1_fake_x",
                "/tmp/opencode/comparison_bench/outputs_comparison/"
                "o1_fake_x"):
        with pytest.raises(c.Refusal):
            c.execute(root=bad, arm="A188",
                      construct_fn=_fake_construct("A188"),
                      decode_fn=_decode_ok, clock=FakeClock(),
                      rss_fn=lambda: 0, writer=MemWriter(), max_blocks=1)


# T13: accounting + manifest labels (gates, genie, D_blind, DE). -----------
@pytest.mark.parametrize("arm,m,leak,f_super", [
    ("A188", 188, 1004.0, 1.177652),
    ("A208", 208, 1104.0, 1.294947),
])
def test_t13_accounting_and_manifest_labels(arm, m, leak, f_super):
    basis = c.leak_basis(arm)
    assert basis["leak_bits"] == leak
    assert basis["f_super_basis"] == pytest.approx(f_super, abs=1e-6)
    assert "BUDGET MAPPING" in basis["f_super_label"]
    assert "not measured efficiency" in basis["f_super_label"]
    assert "INFORMATIONAL ONLY" in basis["f_L2_label"]
    assert basis["d_blind"] == 0.0
    assert "NEVER" in basis["d_blind_label"]
    assert "+0.019" in basis["sensitivity"]
    assert c.MAX_ITER == 300
    w, clk = MemWriter(), FakeClock()
    root = f"/tmp/opencode/o1_fake_manifest_{arm.lower()}"
    mf = _run(root, w, clk, _decode_ok, arm=arm, max_blocks=1)
    mani = json.loads(w.store[f"{root}/manifest.json"])
    con = mani["construct"]
    assert con["seed"] == 2026092001
    assert con["max_trials"] == 20
    assert con["n"] == 1024 and con["m"] == m
    assert con["four_cycles"] == 0
    assert con["min_girth"] == 8
    assert con["rank"] == m
    assert con["lambda"] == {"2": 1.0}
    assert "STOP-BLOCKED" in con["pins"]
    assert mani["seeds"]["block_base"] == 2026095501
    dec = mani["decoder"]
    assert dec["max_iter"] == 300
    assert "decode_error_domain_posterior" in dec["entrypoint"]
    assert "GENIE" in dec["l1_conditioning"]
    assert "D1 ceiling" in dec["l1_conditioning"]
    assert "INFORMATIONAL ONLY" in mani["f_L2_label"]
    assert "BUDGET MAPPING" in mani["f_super_label"]
    assert "ONE BLOCK" in mani["single_code"]
    assert mf["f_super"] == pytest.approx(f_super, abs=1e-6)
    rows = json.loads(w.store[f"{root}/rows.json"])
    assert rows[0]["seed"] == 2026095501
    # DE-cover label defaults to exploratory; campaign needs no precheck.
    assert mani["de_cover"]["label"] == "exploratory"
    assert "no precheck" in mani["de_cover"]["label_source"]
    if arm == "A208":
        assert "any blind disclosure fails" in mani["blind_risk"]
    else:
        assert "104.3" in mani["blind_risk"]


def test_t13_de_label_threading():
    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/o1_fake_delabel", w, clk, _decode_ok,
              arm="A208", max_blocks=1, de_label="covered")
    assert mf["de_cover"]["label"] == "covered"
    assert "explicit --de-label" in mf["de_cover"]["label_source"]
    with pytest.raises(c.Refusal):
        _run("/tmp/opencode/o1_fake_delabel_bad", MemWriter(),
             FakeClock(), _decode_ok, arm="A208", max_blocks=1,
             de_label="maybe")


# T14: unknown arm refuses with zero decodes; budget-fail nonresumable. ---
def test_t14_unknown_arm_and_budget_terminal(tmp_path):
    calls = []

    def _counting(construction, seed):
        calls.append(seed)
        return _decode_ok(construction, seed)

    with pytest.raises(c.Refusal) as exc:
        c.execute(root="/tmp/opencode/o1_fake_badarm", arm="A209",
                  construct_fn=_fake_construct("A188"),
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter(), max_blocks=1)
    assert exc.value.code == 2
    assert calls == []
    # Per-decode overrun (>300 s) halts FAIL(budget); that partial never
    # resumes (refuses rc=2, zero decodes).
    w, clk = MemWriter(), FakeClock()

    def _overrun(construction, seed):
        clk.t += 301.0
        return _decode_ok(construction, seed)

    mf = _run("/tmp/opencode/o1_fake_overrun", w, clk, _overrun)
    assert mf["verdict"] == "FAIL(budget)"
    assert mf["partial"] is True
    rows = json.loads(w.store["/tmp/opencode/o1_fake_overrun/rows.json"])
    assert len(rows) == 1 and rows[0]["status"] == "overrun"
    root = str(tmp_path / "o1_fake_budget_noresume")
    import os as _os
    _os.makedirs(root, exist_ok=True)
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w.store["/tmp/opencode/o1_fake_overrun/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w.store["/tmp/opencode/o1_fake_overrun/rows.json"])
    calls2 = []

    def _counting2(construction, seed):
        calls2.append(seed)
        return _decode_ok(construction, seed)

    with pytest.raises(c.Refusal) as exc:
        c.execute(root=root, arm="A188", resume_from=root,
                  construct_fn=_fake_construct("A188"),
                  decode_fn=_counting2, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter())
    assert exc.value.code == 2
    assert calls2 == []


# T15: gate binds the REAL construct_arm (dry construction, allowed). -----
def test_t15_gate_binds_real_construct_arm():
    # Production binding via the same gate path execute() uses: a spy
    # delegating to the real constructor asserts the arm arrives first.
    seen = []

    def _spy(arm_in, seed, max_trials):
        seen.append((arm_in, seed, max_trials))
        return c.construct_arm(arm_in, seed, max_trials)

    code = c._construct_gate("A188", _spy)
    assert seen[0] == ("A188", 2026092001, 20)
    assert code["four_cycles"] == 0  # real A188 pins, seed 2026092001
    assert code["min_girth"] == 8
    assert code["rank"] == 188
    assert code["construct_seed"] == 2026092001
    assert code["construct_trials"] == 20
    assert code["family"] == "peg-irregular"


# T16: A208-DE precheck mode (fake DE only) + campaign independence. ------
def _fake_de_ok(sampler):
    assert callable(sampler)
    probe = sampler(8, np.random.default_rng(0))
    assert np.asarray(probe).shape == (8, 32)
    return {"converged": True, "iterations": 6,
            "final_entropy_bits": 0.0005,
            "entropy_trace_bits": [0.5, 0.01, 0.0005]}


def test_t16_de_precheck_record_and_labels():
    bundle = _fake_bundle()
    captured = {}

    def _writer(path, blob):
        captured[path] = blob

    rec = c.run_de_precheck(root="workspace/o1_deadbeef", arm="A208",
                            bundle=bundle, de_fn=_fake_de_ok,
                            file_writer=_writer)
    assert rec["arm"] == "A208"
    assert rec["q"] == 32
    assert rec["lambda"] == {"2": 1.0}
    assert set(rec["rho"]) == {"9", "10"}
    assert rec["rate"] == pytest.approx(0.796875)
    assert rec["n_samples"] == 16000
    assert rec["max_iter"] == 100
    assert rec["seed"] == 2026094951
    assert rec["converged"] is True
    assert rec["cover_hint"] == "DE-covered secondary"
    assert captured == {
        "workspace/o1_deadbeef/de_precheck.json":
        json.dumps(rec, indent=1, sort_keys=True, default=str)}


def test_t16_de_precheck_fail_hint_and_a188_refusal():
    bundle = _fake_bundle()

    def _fake_de_marginal(sampler):
        return {"converged": False, "iterations": 100,
                "final_entropy_bits": 0.5, "entropy_trace_bits": [0.5]}

    rec = c.run_de_precheck(root="workspace/o1_deadbeef", arm="A208",
                            bundle=bundle, de_fn=_fake_de_marginal,
                            file_writer=lambda p, b: None)
    assert rec["cover_hint"].startswith("exploratory WITHOUT DE")
    with pytest.raises(c.Refusal):
        c.run_de_precheck(root="workspace/o1_deadbeef", arm="A188",
                          bundle=bundle, de_fn=_fake_de_ok,
                          file_writer=lambda p, b: None)
    with pytest.raises(c.Refusal):
        c.run_de_precheck(root="workspace/o1_deadbeef", arm="A208",
                          bundle=None, de_fn=_fake_de_ok,
                          file_writer=lambda p, b: None)


def test_t16_de_precheck_existing_record_refuses(monkeypatch):
    # No disk writes: the pre-write exists check is fail-closed even on
    # the injected-writer (test-seam) path.
    real_exists = os.path.exists
    monkeypatch.setattr(os.path, "exists",
                        lambda p: True if str(p).endswith("de_precheck.json")
                        else real_exists(p))
    with pytest.raises(c.Refusal):
        c.run_de_precheck(root="workspace/o1_deadbeef", arm="A208",
                          bundle=_fake_bundle(), de_fn=_fake_de_ok,
                          file_writer=lambda p, b: None)
    # Prefix/root policy still applies on the precheck path.
    with pytest.raises(c.Refusal):
        c.run_de_precheck(root="workspace/s2c_deadbeef", arm="A208",
                          bundle=_fake_bundle(), de_fn=_fake_de_ok,
                          file_writer=lambda p, b: None)


# T17: O1R back-compat — defaults behave exactly as before. ---------------
def test_t17_o1r_defaults_back_compat():
    assert c.O1_BLOCK_BASE == 2026095501
    assert c.O1_CONSTRUCT_SEED == 2026092001
    assert c.O1_MAX_TRIALS == 20
    assert c.N_BLOCKS == 60
    assert c.O1R_BLOCK_BASE == 2026095601
    assert c.O1R_N_BLOCKS == 240
    assert c.O1R_R1_SEED == 2026092001
    assert c.O1R_R2_SEED == 2026092011
    assert c.fail_bar(60) == c.PASS_MAX_FAILS == 3
    w, clk = MemWriter(), FakeClock()
    root = "/tmp/opencode/o1r_fake_backcompat"
    mf = _run(root, w, clk, _decode_ok, arm="A208")
    assert mf["campaign"] == "O1"
    assert mf["n_blocks"] == 60
    assert mf["fail_bar"] == 3
    assert mf["pass_bar"] == "block FER<=5% (fails/60<=3)"
    assert mf["replication"]["label"] == "R1"  # seed-derived (O1R §5)
    assert mf["quarter_tally"]["quarters_complete"] == 1
    assert mf["quarter_tally"]["quarters_le3"] == 1
    mani = json.loads(w.store[f"{root}/manifest.json"])
    assert mani["seeds"]["block_base"] == 2026095501
    assert mani["construct"]["seed"] == 2026092001


# T18: bar derivation + n=240 early-stop at the 13th fail. ---------------
def test_t18_fail_bar_derivation():
    assert c.fail_bar(60) == 3
    assert c.fail_bar(240) == 12
    assert c.fail_bar(59) == 2  # floor(n x 0.05)


def test_t18_n240_early_stop_thirteenth_fail():
    w, clk = MemWriter(), FakeClock()
    mf = c.execute(root="/tmp/opencode/o1r_fake_early240", arm="A208",
                   construct_fn=_fake_construct("A208"),
                   decode_fn=_decode_fail, clock=clk,
                   rss_fn=lambda: 0, writer=w, n_blocks=240)
    assert mf["verdict"] == "FAIL-early-stop"
    assert mf["blocks_completed"] == 13
    assert mf["failures"] == 13
    assert mf["n_blocks"] == 240
    assert mf["fail_bar"] == 12
    assert mf["campaign"] == "O1R-replication"
    assert mf["next_block"] == 13
    assert mf["partial"] is True


def test_t18_n240_all_ok_pass_four_quarters():
    w, clk = MemWriter(), FakeClock()
    mf = c.execute(root="/tmp/opencode/o1r_fake_allok240", arm="A208",
                   construct_fn=_fake_construct("A208"),
                   decode_fn=_decode_ok, clock=clk,
                   rss_fn=lambda: 0, writer=w, n_blocks=240)
    assert mf["verdict"] == "PASS"
    assert mf["blocks_completed"] == 240
    assert mf["failures"] == 0
    assert mf["fer_blocks"] == pytest.approx(0.0)
    assert mf["quarter_tally"]["quarters_complete"] == 4
    assert mf["quarter_tally"]["quarters_le3"] == 4


# T19: block-base / construct-seed overrides recorded in manifest. --------
def _fake_construct_param(arm, m):
    def _build(arm_in, seed, max_trials):
        assert arm_in == arm
        assert isinstance(seed, int) and isinstance(max_trials, int)
        return {"four_cycles": 0, "min_girth": 8, "rank": m,
                "family": "peg-irregular", "n": 1024, "m": m,
                "triples": [(0, 0, 1), (1, 1, 2), (seed % 7, 3, 4)],
                "total_sockets": 2048, "parallel_edges": 0}

    return _build


def test_t19_block_seed_base_override():
    assert c.block_seed("A208", 0, c.O1R_BLOCK_BASE) == 2026095601
    assert c.block_seed("A208", 239, c.O1R_BLOCK_BASE) == 2026095840
    assert c.block_seed("A188", 0) == 2026095501  # default unchanged
    with pytest.raises(c.Refusal):
        c.block_seed("A208", 0, True)


def test_t19_overrides_recorded_in_manifest():
    w, clk = MemWriter(), FakeClock()
    root = "/tmp/opencode/o1r_fake_override"
    seen = []

    def _rec(construction, seed):
        seen.append(seed)
        return _decode_ok(construction, seed)

    mf = c.execute(root=root, arm="A208",
                   construct_fn=_fake_construct_param("A208", 208),
                   decode_fn=_rec, clock=clk,
                   rss_fn=lambda: 0, writer=w,
                   block_base=2026095601, n_blocks=240,
                   construct_seed=2026092011, construct_trials=20,
                   max_blocks=2, de_label="covered")
    assert mf["campaign"] == "O1R-replication"
    assert mf["replication"]["label"] == "R2"
    assert mf["n_blocks"] == 240
    assert mf["fail_bar"] == 12
    assert mf["de_cover"]["label"] == "covered"
    assert seen == [2026095601, 2026095602]
    mani = json.loads(w.store[f"{root}/manifest.json"])
    assert mani["construct"]["seed"] == 2026092011
    assert mani["construct"]["max_trials"] == 20
    assert mani["seeds"]["block_base"] == 2026095601
    assert mani["seeds"]["n_blocks"] == 240
    rows = json.loads(w.store[f"{root}/rows.json"])
    assert rows[0]["seed"] == 2026095601


# T20: R2 dry-construct via the REAL constructor (allowed, fast).
# O1R Amendment 2026-09-21: R2 (seed 2026092011) pins are
# fc=0/rank-full/twice-identical ONLY; min_girth RECORDED as-measured (6),
# reported, never gated. R1 (seed 2026092001) keeps fc=0/girth=8/rank-full.
# No alternate seeds; no tuning.
def test_t20_r2_amended_pins_accept_girth_recorded():
    code = c.construct_arm("A208", 2026092011, 20)
    assert code["four_cycles"] == 0
    assert code["rank"] == 208
    assert code["min_girth"] == 6  # measured, recorded not gated
    again = c.construct_arm("A208", 2026092011, 20)
    sa = sorted(tuple(map(int, t)) for t in code["triples"])
    sb = sorted(tuple(map(int, t)) for t in again["triples"])
    assert sa == sb  # construct-twice-identical holds
    # Gate path accepts R2 girth 6 (real construction, allowed).
    gated = c._construct_gate("A208", c.construct_arm, 2026092011, 20)
    assert gated["four_cycles"] == 0
    assert gated["rank"] == 208
    assert gated["min_girth"] == 6
    assert gated["construct_seed"] == 2026092011
    assert gated["construct_trials"] == 20
    # Manifest pin table records the measured girth (fast fake R2-mimic).
    def _r2_mimic(arm_in, seed, max_trials):
        assert (arm_in, seed, max_trials) == ("A208", 2026092011, 20)
        return {"four_cycles": 0, "min_girth": 6, "rank": 208,
                "family": "peg-irregular", "n": 1024, "m": 208,
                "triples": [(0, 0, 1), (1, 1, 2)],
                "total_sockets": 2048, "parallel_edges": 0}

    w, clk = MemWriter(), FakeClock()
    root = "/tmp/opencode/o1r_fake_r2accept"
    mf = c.execute(root=root, arm="A208",
                   construct_fn=_r2_mimic,
                   decode_fn=_decode_ok, clock=clk,
                   rss_fn=lambda: 0, writer=w,
                   block_base=2026095601, n_blocks=240,
                   construct_seed=2026092011, construct_trials=20,
                   max_blocks=1)
    assert mf["replication"]["label"] == "R2"
    mani = json.loads(w.store[f"{root}/manifest.json"])
    assert mani["construct"]["min_girth"] == 6
    assert mani["construct"]["four_cycles"] == 0
    assert mani["construct"]["rank"] == 208
    assert "recorded-not-gated" in mani["construct"]["pins"]
    assert "STOP-BLOCKED" in mani["construct"]["pins"]


def test_t20_r2_rejects_fc_rank_mismatch(capsys):
    # R2 still STOP-BLOCKED on gated fields (fc≠0 or rank≠full), with the
    # measured girth carried in the raise-path evidence.
    for pin, rec in (("fc", {"four_cycles": 1, "min_girth": 6,
                             "rank": 208}),
                     ("rank", {"four_cycles": 0, "min_girth": 6,
                               "rank": 207})):
        def _bad(arm_in, seed, max_trials, _rec=dict(rec)):
            assert (arm_in, seed, max_trials) == ("A208", 2026092011, 20)
            return {"four_cycles": _rec["four_cycles"],
                    "min_girth": _rec["min_girth"], "rank": _rec["rank"],
                    "family": "peg-irregular"}

        with pytest.raises(c.Refusal) as exc:
            c._construct_gate("A208", _bad, 2026092011, 20)
        assert exc.value.code == 2
        err = capsys.readouterr().err
        assert "STOP-BLOCKED" in err
        assert "measured girth 6" in err
    # Full execute path with R2 fc-mismatch refuses pre-decode (zero).
    def _bad_fc(arm_in, seed, max_trials):
        assert (arm_in, seed, max_trials) == ("A208", 2026092011, 20)
        return {"four_cycles": 1, "min_girth": 6, "rank": 208,
                "family": "peg-irregular"}

    calls = []

    def _counting(construction, seed):
        calls.append(seed)
        return _decode_ok(construction, seed)

    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/o1r_fake_r2badfc", arm="A208",
                  construct_fn=_bad_fc,
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter(),
                  block_base=2026095601, n_blocks=240,
                  construct_seed=2026092011, construct_trials=20)
    assert calls == []


def test_t20_r1_girth8_gate_still_rejects(capsys):
    # R1 keeps the girth==8 gate: measured girth 6 refuses STOP-BLOCKED.
    def _r1_girth6(arm_in, seed, max_trials):
        assert (arm_in, seed, max_trials) == ("A208", 2026092001, 20)
        return {"four_cycles": 0, "min_girth": 6, "rank": 208,
                "family": "peg-irregular"}

    with pytest.raises(c.Refusal) as exc:
        c._construct_gate("A208", _r1_girth6, 2026092001, 20)
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "STOP-BLOCKED" in err and "min_girth" in err
    # Full execute path with R1 girth-6 refuses pre-decode (zero decodes).
    calls = []

    def _counting(construction, seed):
        calls.append(seed)
        return _decode_ok(construction, seed)

    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/o1r_fake_r1girth6", arm="A208",
                  construct_fn=_r1_girth6,
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter(),
                  block_base=2026095601, n_blocks=240,
                  construct_seed=2026092001, construct_trials=20)
    assert calls == []


# T21: R1/R2 labels derive from the construct seed. -----------------------
def test_t21_replication_label_derivation():
    assert c.replication_label(2026092001) == "R1"
    assert c.replication_label(2026092011) == "R2"
    assert c.replication_label(1) == "custom"


# T22: per-60 quarter tally is report-only and derived from rows. ---------
def test_t22_quarter_tally_report_only():
    rows = [{"block": i,
             "block_fail": 1 if i in (0, 61, 120, 200) else 0}
            for i in range(240)]
    t = c.quarter_tally(rows)
    assert t["idx_0_59"] == {"blocks": 60, "fails": 1}
    assert t["idx_60_119"] == {"blocks": 60, "fails": 1}
    assert t["idx_120_179"] == {"blocks": 60, "fails": 1}
    assert t["idx_180_239"] == {"blocks": 60, "fails": 1}
    assert t["quarters_complete"] == 4
    assert t["quarters_le3"] == 4  # O1-bar reference, never gated
    partial = c.quarter_tally([{"block": 0, "block_fail": 0}])
    assert partial["quarters_complete"] == 0
    assert partial["quarters_le3"] == 0


# T23: CLI O1R flags + o1r root prefix. -----------------------------------
def test_t23_cli_o1r_flags_and_root_prefix():
    assert c._allows_root("workspace/o1_deadbeef")
    assert c._allows_root("workspace/o1r_deadbeef")
    assert not c._allows_root("workspace/s2c_deadbeef")
    base = ["--execute-real", "--execution-authorized", "--arm", "A208",
            "--root", "workspace/o1r_deadbeef"]
    with pytest.raises(c.Refusal):
        c.main(base + ["--n-blocks", "0"])
    with pytest.raises(c.Refusal):
        c.main(base + ["--construct-trials", "0"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized", "--arm",
                "A208", "--root", "workspace/s2c_deadbeef"])
