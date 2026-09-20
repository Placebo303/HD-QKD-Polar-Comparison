"""V80 S2c empirical-channel campaign executor tests (EXPLORE, FAKE-ONLY).

Frozen spec: S2C_EXPERIMENT_PACKET_20260920.md (G-S2C, three arms
L-A|L-B|L-C). Every test injects fake construct/decode/clock/rss/writer
or synthetic dict bundles — zero production ``construct_arm`` /
``decode_frame_empirical`` / gamma-file loads, zero disk writes (the
writer is an in-memory capture; resume shims under /tmp/opencode are
created and removed inside the test). Wall: milliseconds.
"""
import inspect
import json

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import (
    v80_s2c_campaign as c,
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
    # Mirrors the frozen pinned table (packet §1): per-arm four_cycles
    # L-A 0 / L-B 0 / L-C 2 (PINNED), min_girth, rank, family.
    # Signature mirrors production construct_arm(arm, seed, max_trials) and
    # asserts the gate forwards the arm (fake-mask regression guard: the
    # gate once called construct_fn(seed, trials), which fakes accepted
    # while production refused as unknown arm 2026092001).
    table = {"L-A": (0, 6), "L-B": (0, 6), "L-C": (2, 4)}
    fc, girth = table[arm]

    def _build(arm_in, seed, max_trials):
        assert (arm_in, seed, max_trials) == (arm, 2026092001, 20)
        return {"four_cycles": fc, "min_girth": girth, "rank": 47,
                "family": "peg-irregular"}

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


def _run(root, writer, clock, decode_fn, arm="L-A", **kw):
    return c.execute(root=root, arm=arm,
                     construct_fn=_fake_construct(arm),
                     decode_fn=decode_fn, clock=clock,
                     rss_fn=lambda: 0, writer=writer, **kw)


# T1: dual-flag gate + arm/root refusal matrix (rc2 pre-anything). ------
def test_t1_dual_flag_refusal():
    with pytest.raises(c.Refusal):
        c.main([])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--arm", "L-A",
                "--root", "workspace/s2c_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execution-authorized", "--arm", "L-A",
                "--root", "workspace/s2c_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "L-A", "--root", "workspace/wrong_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "L-A", "--root", "workspace/s2b_deadbeef"])
    for bad_arm in ("V2", "S2b", "l-a", ""):
        with pytest.raises(c.Refusal):
            c.main(["--execute-real", "--execution-authorized",
                    "--arm", bad_arm,
                    "--root", "workspace/s2c_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "L-A", "--root", "workspace/s2c_aaaaaaaa",
                "--resume-from", "workspace/s2c_bbbbbbbb"])


# T2: root absent/present matrix. ----------------------------------------
def test_t2_root_absent_present_matrix(tmp_path):
    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/s2c_fake_absent_01", w, clk, _decode_ok,
              max_groups=1)
    assert mf["verdict"] == "PROBE-truncated"
    with pytest.raises(c.Refusal):
        _run(str(tmp_path), MemWriter(), FakeClock(), _decode_ok,
             max_groups=1)
    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/s2c_fake_absent_02",
                  arm="L-A",
                  resume_from="/tmp/opencode/s2c_fake_absent_02",
                  construct_fn=_fake_construct("L-A"),
                  decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0, writer=MemWriter())
    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/s2c_fake_a",
                  arm="L-A",
                  resume_from="/tmp/opencode/s2c_fake_b",
                  construct_fn=_fake_construct("L-A"),
                  decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0, writer=MemWriter())


# T3: per-arm four-cycle gates (L-C pinned 2). ----------------------------
@pytest.mark.parametrize("arm,fc", [("L-A", 0), ("L-B", 0), ("L-C", 2)])
def test_t3_per_arm_gate_pass(arm, fc):
    assert c.ARMS[arm]["four_cycles"] == fc
    w, clk = MemWriter(), FakeClock()
    mf = _run(f"/tmp/opencode/s2c_fake_gate_{arm.lower()}", w, clk,
              _decode_ok, arm=arm, max_groups=1)
    assert mf["verdict"] == "PROBE-truncated"
    assert mf["arm"] == arm


@pytest.mark.parametrize("arm,bad_fc", [("L-A", 1), ("L-A", 2),
                                        ("L-B", 1), ("L-B", 1158),
                                        ("L-C", 0), ("L-C", 1),
                                        ("L-C", 3)])
def test_t3_per_arm_gate_mismatch_stop_blocked(arm, bad_fc, capsys):
    def _bad(arm_in, seed, max_trials):
        return {"four_cycles": bad_fc, "min_girth": 6, "rank": 47,
                "family": "peg-irregular"}

    calls = []

    def _counting(construction, seed):
        calls.append(seed)
        return _decode_ok(construction, seed)

    with pytest.raises(c.Refusal) as exc:
        c.execute(root=f"/tmp/opencode/s2c_fake_gate_{arm.lower()}",
                  arm=arm, construct_fn=_bad, decode_fn=_counting,
                  clock=FakeClock(), rss_fn=lambda: 0,
                  writer=MemWriter(), max_groups=1)
    assert exc.value.code == 2
    assert "STOP-BLOCKED" in capsys.readouterr().err
    assert calls == []  # fail closed pre-decode


# T4: construct-twice-identity + frozen_failure refuse. -------------------
def test_t4_construct_twice_identity_and_status():
    def _drifting(arm_in, seed, max_trials):
        _drifting.n += 1
        return {"four_cycles": 0, "min_girth": 6, "rank": 47,
                "family": "peg-irregular",
                "triples": [(0, _drifting.n, 1)]}
    _drifting.n = 0
    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/s2c_fake_twice", arm="L-A",
                  construct_fn=_drifting, decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0,
                  writer=MemWriter(), max_groups=1)

    def _frozen_fail(arm_in, seed, max_trials):
        return {"status": "frozen_failure", "four_cycles": 0,
                "triples": []}
    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/s2c_fake_frozenfail", arm="L-A",
                  construct_fn=_frozen_fail, decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0,
                  writer=MemWriter(), max_groups=1)


# T5: bundle binding gates (normalization fail-closed). -------------------
def test_t5_bundle_binding_gates():
    good = _fake_bundle()
    bound = c.bind_empirical_bundle(dict(good))
    assert bound["g1"].shape == (32, 1024)
    assert bound["g2"].shape == (32, 32, 1024)
    assert bound["p_b"].shape == (1024,)
    bad_pb = dict(good, p_b=good["p_b"] * 2.0)
    with pytest.raises(c.Refusal):
        c.bind_empirical_bundle(bad_pb)
    bad_shape = {"g1": np.ones((32, 1000)), "g2": good["g2"],
                 "p_b": good["p_b"]}
    with pytest.raises(c.Refusal):
        c.bind_empirical_bundle(bad_shape)
    missing = {"g1": good["g1"], "g2": good["g2"]}
    with pytest.raises(c.Refusal):
        c.bind_empirical_bundle(missing)
    zero_col = {"g1": good["g1"].copy(), "g2": good["g2"],
                "p_b": good["p_b"]}
    zero_col["g1"][:, 3] = 0.0  # colsum 0 != 1 -> bind refuses
    with pytest.raises(c.Refusal):
        c.bind_empirical_bundle(zero_col)


def test_t5_zero_mass_fallback_delta_at_0():
    # Bypass bind (zero cells are unbindable by design); exercise the
    # frozen posterior_rows delta-at-0 fallback directly.
    g1 = np.full((32, 1024), 1.0 / 32)
    g1[:, 7] = 0.0
    g2 = np.full((32, 32, 1024), 1.0 / 32)
    g2[5, :, 9] = 0.0
    bundle = {"g1": g1, "g2": g2,
              "p_b": np.full(1024, 1.0 / 1024)}
    rows = c.posterior_rows_l2(bundle, np.array([7, 9]), np.array([5, 5]))
    assert rows[0, 0] == pytest.approx(1.0) and rows[0, 1:].sum() == 0.0
    assert rows[1, 0] == pytest.approx(1.0) and rows[1, 1:].sum() == 0.0
    # Sampler zero-mass path: all mass on b=7 forces u1t=0 every draw.
    delta_pb = {"g1": g1, "g2": g2,
                "p_b": np.array([1.0 if i == 7 else 0.0
                                 for i in range(1024)])}
    b, u1, u2 = c.empirical_triple_sampler(
        delta_pb, 16, np.random.default_rng(1))
    assert set(b.tolist()) == {7}
    assert set(u1.tolist()) == {0}


# T6: sampler determinism + frozen stream tag. -----------------------------
def test_t6_sampler_stream_pins():
    bundle = _fake_bundle()
    r1 = np.random.default_rng(42)
    r2 = np.random.default_rng(42)
    t1 = c.empirical_triple_sampler(bundle, 64, r1)
    t2 = c.empirical_triple_sampler(bundle, 64, r2)
    for a, b_ in zip(t1, t2):
        assert np.array_equal(a, b_)
    assert c.stream_seed(2026097201) == common.v10_seed("s2c_emp:2026097201")
    # Distinct domain from the S2b s2_smoke: stream.
    assert (common.v10_seed("s2c_emp:2026097201")
            != common.v10_seed("s2_smoke:2026097201"))
    # Frozen literal seeds (packet §4): 2026097201+idx, idx=0..239.
    assert c.frame_seed("L-A", 0, 0) == 2026097201
    assert c.frame_seed("L-C", 59, 3) == 2026097201 + 239
    assert c.S2C_FRAME_BASE == 2026097201
    assert c.S2C_CONSTRUCT_SEED == 2026092001
    for bad in ("S2b", "V1", "L-D"):
        with pytest.raises(c.Refusal) as exc:
            c.frame_seed(bad, 0, 0)
        assert exc.value.code == 2


# T7: posterior/center normalization + XOR-centering identity. -------------
def test_t7_posterior_center_math():
    bundle = _fake_bundle()
    rng = np.random.default_rng(3)
    b = rng.choice(1024, size=32, p=bundle["p_b"])
    u1 = rng.integers(0, 32, size=32)
    rows = c.posterior_rows_l2(bundle, b, u1)
    assert rows.shape == (32, 32)
    assert np.allclose(rows.sum(axis=1), 1.0, atol=1e-9)
    y = (b & 31).astype(np.int64)
    prior = c.center_rows_prior(rows, y)
    assert prior.shape == (32, 32)
    assert np.allclose(prior.sum(axis=1), 1.0, atol=1e-9)
    ee = np.arange(32, dtype=np.int64)
    for i in range(32):
        assert np.allclose(prior[i], rows[i, y[i] ^ ee])


# T8: decoder wiring — posterior entrypoint, (n,32) prior, max_iter=300. ---
def test_t8_decoder_wiring_posterior_entrypoint(monkeypatch):
    bundle = _fake_bundle()
    seen = {}

    def _fake_dense(triples, n, m, field):
        assert (n, m) == (256, 47)
        return np.zeros((47, 256), dtype=np.int64)

    def _fake_syn(field, dense, vec):
        assert len(vec) == 256
        return [0] * 47

    def _fake_posterior(field, y, matrix, s_x, prior, max_iter,
                        **kw):
        seen.setdefault("calls", []).append(
            {"y": list(y), "s_x": list(s_x),
             "prior_shape": tuple(np.asarray(prior).shape),
             "prior_rowsums": np.asarray(prior).sum(axis=1),
             "max_iter": max_iter})
        assert tuple(np.asarray(prior).shape) == (256, 32)
        return {"status": "success", "iterations": 7,
                "reconstruction_ok": True, "x_hat": list(y)}

    monkeypatch.setattr(c.peg, "sparse_to_dense", _fake_dense)
    monkeypatch.setattr(c.fftqspa, "syndrome_of", _fake_syn)
    monkeypatch.setattr(c.v28, "decode_error_domain_posterior",
                        _fake_posterior)
    out = c.decode_frame_empirical({"triples": [(0, 0, 1)]},
                                   2026097201, bundle)
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


# T9: all-ok per arm → PASS; paired seeds across arms. ---------------------
def test_t9_all_ok_pass_and_paired_seeds():
    seqs = {}
    for arm in ("L-A", "L-B", "L-C"):
        w, clk = MemWriter(), FakeClock()
        seen = []

        def _rec(construction, seed, _s=seen):
            _s.append(seed)
            return _decode_ok(construction, seed)

        mf = c.execute(root=f"/tmp/opencode/s2c_fake_allok_{arm}",
                       arm=arm, construct_fn=_fake_construct(arm),
                       decode_fn=_rec, clock=clk,
                       rss_fn=lambda: 0, writer=w)
        assert mf["verdict"] == "PASS"
        assert mf["failures"] == 0
        assert mf["groups_completed"] == 60
        assert mf["ledger"] == {"decodes": 240, "groups_completed": 60}
        assert mf["fer_groups"] == pytest.approx(0.0)
        rows = json.loads(
            w.store[f"/tmp/opencode/s2c_fake_allok_{arm}/rows.json"])
        assert len(rows) == 60
        assert [r["group"] for r in rows] == list(range(60))
        assert all(r["group_accept"] for r in rows)
        assert w.calls == 61  # 60 group checkpoints + 1 final
        assert mf["verify"] == {"four_cycles_ok": True, "ledger_ok": True,
                                "rows_ok": True}
        assert len(mf["wall_windows"]) == 1
        assert mf["resume"] == {"continuations_used": 0,
                                "max_continuations": 1}
        seqs[arm] = seen
    assert seqs["L-A"] == seqs["L-B"] == seqs["L-C"]
    assert seqs["L-A"][0] == 2026097201
    assert seqs["L-A"][-1] == 2026097201 + 239
    assert len(seqs["L-A"]) == 240


# T10: early-stop at the 4th group failure. ---------------------------------
def test_t10_early_stop_fourth_failure():
    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/s2c_fake_early", w, clk, _decode_fail)
    assert mf["verdict"] == "FAIL-early-stop"
    assert mf["groups_completed"] == 4
    assert mf["failures"] == 4
    assert mf["ledger"]["decodes"] == 16
    assert mf["next_group"] == 4
    assert mf["partial"] is True


# T11: checkpoint/resume — one wall-partial continuation; 2nd refuses. ------
def test_t11_resume_continuation_single_wall_window():
    import os as _os
    root = "/tmp/opencode/s2c_fake_resume"
    w1, clk1 = MemWriter(), FakeClock()

    def _advancing(construction, seed):
        clk1.t += 300.0
        return _decode_ok(construction, seed)

    part = c.execute(root=root, arm="L-A",
                     construct_fn=_fake_construct("L-A"),
                     decode_fn=_advancing, clock=clk1,
                     rss_fn=lambda: 0, writer=w1)
    assert part["verdict"] == "INCOMPLETE-wall"
    assert part["groups_completed"] == 4
    assert part["next_group"] == 4
    assert part["ledger"]["decodes"] == 16
    rows_p = json.loads(w1.store[f"{root}/rows.json"])
    w2, clk2 = MemWriter(), FakeClock()

    def _fast(construction, seed):
        clk2.t += 1.0
        return _decode_ok(construction, seed)

    _os.makedirs(root, exist_ok=True)
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w1.store[f"{root}/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w1.store[f"{root}/rows.json"])
    try:
        done = c.execute(root=root, arm="L-A",
                         resume_from=root,
                         construct_fn=_fake_construct("L-A"),
                         decode_fn=_fast, clock=clk2,
                         rss_fn=lambda: 0, writer=w2)
    finally:
        _os.remove(f"{root}/manifest.json")
        _os.remove(f"{root}/rows.json")
        _os.rmdir(root)
    assert done["verdict"] == "PASS"
    assert done["ledger"]["decodes"] == 240
    assert done["groups_completed"] == 60
    assert len(done["wall_windows"]) == 2
    assert done["resume"] == {"continuations_used": 1,
                              "max_continuations": 1}
    rows_d = json.loads(w2.store[f"{root}/rows.json"])
    assert (json.dumps(rows_d[:4], sort_keys=True)
            == json.dumps(rows_p, sort_keys=True))
    # A resumed-twice partial (2 windows) refuses with zero decodes.
    import os as _os2
    _os2.makedirs(root, exist_ok=True)
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w2.store[f"{root}/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w2.store[f"{root}/rows.json"])
    try:
        calls = []

        def _counting(construction, seed):
            calls.append(seed)
            return _decode_ok(construction, seed)

        with pytest.raises(c.Refusal) as exc:
            c.execute(root=root, arm="L-A", resume_from=root,
                      construct_fn=_fake_construct("L-A"),
                      decode_fn=_counting, clock=FakeClock(),
                      rss_fn=lambda: 0, writer=MemWriter())
        assert exc.value.code == 2
        assert calls == []
    finally:
        _os2.remove(f"{root}/manifest.json")
        _os2.remove(f"{root}/rows.json")
        _os2.rmdir(root)


# T12: no writes outside root; forbidden trees refuse; csv present. ---------
def test_t12_no_writes_outside_root():
    w, clk = MemWriter(), FakeClock()
    root = "/tmp/opencode/s2c_fake_nowrite"
    _run(root, w, clk, _decode_ok, max_groups=1)
    assert set(w.store) == {f"{root}/manifest.json", f"{root}/rows.json",
                            f"{root}/group_accounting.csv"}
    assert w.store[f"{root}/group_accounting.csv"].splitlines()[0] == (
        "group,n_frames,n_ok,group_accept,superframe_fail,per_frame_fer,"
        "d_blind,leak_bits,f_super,seeds,iterations")
    for bad in ("/tmp/opencode/results/s2c_fake_x",
                "/tmp/opencode/comparison_bench/outputs_comparison/"
                "s2c_fake_x"):
        with pytest.raises(c.Refusal):
            c.execute(root=bad, arm="L-A",
                      construct_fn=_fake_construct("L-A"),
                      decode_fn=_decode_ok, clock=FakeClock(),
                      rss_fn=lambda: 0, writer=MemWriter(), max_groups=1)


# T13: accounting + manifest labels (gates, genie, D_blind). -----------------
def test_t13_accounting_and_manifest_labels():
    assert c.PER_FRAME_FER_FOR_SUPERFRAME_5PCT == pytest.approx(0.01274,
                                                               abs=1e-5)
    basis = c.leak_basis()
    assert basis["leak_bits"] == 1044.0
    assert basis["f_super_basis"] == pytest.approx(1.2246, abs=1e-4)
    assert "BUDGET MAPPING" in basis["f_super_label"]
    assert "not measured efficiency" in basis["f_super_label"]
    assert basis["f_L2_basis"] == pytest.approx(1.1376, abs=5e-4)
    assert "INFORMATIONAL ONLY" in basis["f_L2_label"]
    assert basis["d_blind"] == 0.0
    assert "NEVER" in basis["d_blind_label"]
    assert "+0.019" in basis["sensitivity"]
    assert c.MAX_ITER == 300
    w, clk = MemWriter(), FakeClock()
    root = "/tmp/opencode/s2c_fake_manifest"
    mf = _run(root, w, clk, _decode_ok, arm="L-C", max_groups=1)
    assert mf["arm"] == "L-C"
    mani = json.loads(w.store[f"{root}/manifest.json"])
    con = mani["construct"]
    assert con["seed"] == 2026092001
    assert con["max_trials"] == 20
    assert con["four_cycles"] == 2  # L-C pinned, not zero
    assert con["lambda"] == {"3": 1.0}
    assert "==2" in con["four_cycle_gate"]
    assert "STOP-BLOCKED" in con["four_cycle_gate"]
    assert mani["seeds"]["frame_base"] == 2026097201
    dec = mani["decoder"]
    assert dec["max_iter"] == 300
    assert "decode_error_domain_posterior" in dec["entrypoint"]
    assert "GENIE" in dec["l1_conditioning"]
    assert "upper bound" in dec["l1_conditioning"]
    assert mani["f_L2"] == pytest.approx(1.1376, abs=5e-4)
    assert "INFORMATIONAL ONLY" in mani["f_L2_label"]
    assert mani["f_super"] == pytest.approx(1.2246, abs=1e-4)
    assert "BUDGET MAPPING" in mani["f_super_label"]
    rows = json.loads(w.store[f"{root}/rows.json"])
    assert rows[0]["frames"][0]["seed"] == 2026097201


# T14: unknown arm refuses with zero decodes; budget-fail nonresumable. -----
def test_t14_unknown_arm_and_budget_terminal():
    import os as _os
    calls = []

    def _counting(construction, seed):
        calls.append(seed)
        return _decode_ok(construction, seed)

    with pytest.raises(c.Refusal) as exc:
        c.execute(root="/tmp/opencode/s2c_fake_badarm", arm="L-D",
                  construct_fn=_fake_construct("L-A"),
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter(), max_groups=1)
    assert exc.value.code == 2
    assert calls == []
    # Per-decode overrun (>300 s) halts FAIL(budget); that partial never
    # resumes (refuses rc=2, zero decodes).
    w, clk = MemWriter(), FakeClock()

    def _overrun(construction, seed):
        clk.t += 301.0
        return _decode_ok(construction, seed)

    mf = _run("/tmp/opencode/s2c_fake_overrun", w, clk, _overrun)
    assert mf["verdict"] == "FAIL(budget)"
    assert mf["partial"] is True
    rows = json.loads(w.store["/tmp/opencode/s2c_fake_overrun/rows.json"])
    assert len(rows) == 1 and rows[0]["status"] == "overrun"
    root = "/tmp/opencode/s2c_fake_budget_noresume"
    _os.makedirs(root, exist_ok=True)
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w.store["/tmp/opencode/s2c_fake_overrun/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w.store["/tmp/opencode/s2c_fake_overrun/rows.json"])
    try:
        calls2 = []

        def _counting2(construction, seed):
            calls2.append(seed)
            return _decode_ok(construction, seed)

        with pytest.raises(c.Refusal) as exc:
            c.execute(root=root, arm="L-A", resume_from=root,
                      construct_fn=_fake_construct("L-A"),
                      decode_fn=_counting2, clock=FakeClock(),
                      rss_fn=lambda: 0, writer=MemWriter())
        assert exc.value.code == 2
        assert calls2 == []
    finally:
        _os.remove(f"{root}/manifest.json")
        _os.remove(f"{root}/rows.json")
        _os.rmdir(root)


# T15: gate binds the REAL construct_arm (fake-mask regression guard). ------
def test_t15_gate_binds_real_construct_arm():
    # Production binding via the same gate path execute() uses: the gate
    # once called construct_fn(seed, trials), which fakes accepted while
    # production refused as unknown arm 2026092001. A spy delegating to
    # the real constructor asserts the arm arrives as the first arg.
    seen = []

    def _spy(arm_in, seed, max_trials):
        seen.append((arm_in, seed, max_trials))
        return c.construct_arm(arm_in, seed, max_trials)

    code = c._construct_gate("L-A", _spy)
    assert seen[0] == ("L-A", 2026092001, 20)
    assert code["four_cycles"] == 0  # real L-A construction, seed 2026092001
    assert code["construct_seed"] == 2026092001
    assert code["construct_trials"] == 20
    assert code["family"] == "peg-irregular"
