"""V80 S1 readiness tests — FAKE only, zero scientific DE calls.

T0: kernel import/compile + lambda_validate + make_rho shape +
    target_rate_layer recompute (pure helpers, never run_mcde_posterior).
T1: fixed-seed replay identical + config-hash + fake-runner complete path.
Plus: S1 construction ban assert + refusal (rc2) + no-overwrite checks.
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v26_mcde as K,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    v80_s1_mcde_runner as R,
)
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v9_mcde import (
    parse_degree_hist,
)

RECORDED_CONFIG_HASH = "60ab1e44dc179e6d783d1792dae59fd691c5657e386056498140d37fe04fb0da"
# F1 rotation: old 57e5da44…684 → new 60ab1e44…0da ("primary_m2_grid" entered
# frozen_config(); "m_grid" stays SECONDARY-only).


def fake_channel_sampler(n, rng):
    """Frozen fake gamma interface: peaked-at-0 (n,32) population, deterministic."""
    q = 32
    pop = np.full((n, q), 0.001, dtype=np.float64)
    pop[:, 0] = 1.0
    return pop / pop.sum(axis=1, keepdims=True)


class S1ReadinessTest(unittest.TestCase):
    def test_t0_kernel_pure_helpers(self):
        self.assertAlmostEqual(K.target_rate_layer(1.3, 0.80, 5), 0.792)
        self.assertAlmostEqual(K.target_rate_layer(1.3, 0.025, 5), 0.9935)
        rho = K.make_rho(1 - 27 / 256, {2: 1.0})
        self.assertEqual(set(rho), {18, 19})
        self.assertAlmostEqual(sum(rho.values()), 1.0, places=12)
        d, p = parse_degree_hist({2: 1.0}, "lambda_edge", 32)
        self.assertEqual(d.tolist(), [2])
        self.assertEqual(p.tolist(), [1.0])
        perm, nz = K.build_gf_perm_table(32)
        self.assertEqual(perm.shape, (32, 32))
        self.assertEqual(len(nz), 31)

    def test_t0_validate_ok(self):
        R.validate_lambda({2: 1.0})
        R.validate_rho(K.make_rho(1 - 24 / 256, {2: 1.0}))

    def test_t1_config_hash_recorded(self):
        self.assertEqual(R.config_hash(), RECORDED_CONFIG_HASH)
        self.assertEqual(R.config_hash(), R.config_hash(R.frozen_config()))

    def test_t1_fixed_seed_replay_identical(self):
        import json
        self.assertEqual(json.dumps(R.build_plan(), sort_keys=True),
                         json.dumps(R.build_plan(), sort_keys=True))
        a = fake_channel_sampler(64, np.random.default_rng(2026094951))
        b = fake_channel_sampler(64, np.random.default_rng(2026094951))
        np.testing.assert_array_equal(a, b)

    def test_t1_fake_runner_profile_complete_zero_de(self):
        calls = {"mcde": 0, "sampler": 0}
        real = K.run_mcde_posterior
        K.run_mcde_posterior = lambda *a, **k: (calls.__setitem__("mcde", 1),
                                                (_ for _ in ()).throw(
                                                    AssertionError("DE called")))

        def counting_sampler(n, rng):
            calls["sampler"] += 1
            return fake_channel_sampler(n, rng)

        try:
            with tempfile.TemporaryDirectory() as td:
                root = os.path.join(td, "s1_mcde_fresh")
                rc = R.main(["--profile-only", "--root", root],
                            channel_sampler=counting_sampler)
        finally:
            K.run_mcde_posterior = real
        self.assertEqual(rc, 0)
        self.assertEqual(calls, {"mcde": 0, "sampler": 0})
        plan = R.build_plan()
        self.assertEqual((plan["totals"]["PRIMARY"], plan["totals"]["SECONDARY"],
                          plan["totals"]["de"], plan["totals"]["setup"]),
                         (420, 180, 600, 12))
        self.assertEqual(plan["totals"]["node_updates"], 108800000)
        self.assertLessEqual(plan["totals"]["wall_s"], 3600)

    def test_ban_assert_pass_and_fail_closed(self):
        R.assert_no_construction(R.build_plan())
        with self.assertRaises(R.Refusal) as cm:
            R.assert_no_construction({"outputs": ["parity_matrix"]})
        self.assertEqual(cm.exception.code, 2)

    def test_refusal_default_no_auth(self):
        with self.assertRaises(R.Refusal) as cm:
            R.main([])
        self.assertEqual(cm.exception.code, 2)

    def test_refusal_existing_root_no_write(self):
        with tempfile.TemporaryDirectory() as td:
            before = set(os.listdir(td))
            with self.assertRaises(R.Refusal) as cm:
                R.main(["--profile-only", "--root", td])
            self.assertEqual(cm.exception.code, 2)
            self.assertEqual(set(os.listdir(td)), before)

    def test_refusal_invalid_rho(self):
        with self.assertRaises(R.Refusal) as cm:
            R.validate_rho({18: 0.5, 19: 0.4})
        self.assertEqual(cm.exception.code, 2)

    def test_refusal_unnormalized_lambda(self):
        with self.assertRaises(R.Refusal) as cm:
            R.validate_lambda({2: 0.9, 3: 0.2})
        self.assertEqual(cm.exception.code, 2)

    def test_refusal_bound_violation(self):
        with self.assertRaises(R.Refusal) as cm:
            R.validate_lambda({41: 1.0})
        self.assertEqual(cm.exception.code, 2)

    def test_no_overwrite_profile_creates_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            root = os.path.join(td, "s1_mcde_fresh")
            self.assertEqual(R.main(["--profile-only", "--root", root]), 0)
            self.assertFalse(os.path.exists(root))


def _fake_bundle():
    rng = np.random.default_rng(7)
    g1 = rng.random((32, 1024)) + 0.1
    g1 /= g1.sum(axis=0, keepdims=True)
    g2 = rng.random((32, 32, 1024)) + 0.1
    # Q5 branch-a: fake follows [u1,u2,b] = V26 pjoint convention
    # (cond-rowsum over axis=1), matching the real artifact.
    g2 /= g2.sum(axis=1, keepdims=True)
    # F3: explicitly-flagged fake (uniform-p_b fallback is fake-only).
    return {"gamma1": g1, "gamma2": g2, "H_L1": 0.025, "H_L2": 0.80,
            R.FAKE_BUNDLE_FLAG: True}


def _make_fake_de(calls, trace=(0.70, 0.69, 0.68)):
    def fake(q, lambda_edge, rho_edge, *, channel_sampler, n_samples,
             max_iter, seed, entropy_tol_bits=0.01, streak=20,
             record_entropy=True, record_channel_entropy=False):
        calls.append((q, dict(lambda_edge), n_samples, seed))
        try:
            channel_sampler(4, np.random.default_rng(seed))
        except Exception:
            pass
        return {"schema": "fake", "converged": True, "iterations": 2,
                "entropy_trace_bits": [0.01, 0.001],
                "final_entropy_bits": 0.001, "q": q,
                "n_samples": n_samples, "max_iter": max_iter, "seed": seed,
                "entropy_tol_bits": entropy_tol_bits, "streak": streak,
                "lambda": dict(lambda_edge), "rho": dict(rho_edge),
                "channel_entropy_trace_bits": list(trace)}
    return fake


def _shim_production_raises(testcase, calls):
    real = K.run_mcde_posterior

    def raiser(*a, **k):
        calls.append(1)
        raise AssertionError("production DE called")
    K.run_mcde_posterior = raiser
    testcase.addCleanup(setattr, K, "run_mcde_posterior", real)


class S1ExecutePathTest(unittest.TestCase):
    """D2 execution-path tests — FAKE kernel only, zero production calls."""

    def test_exec_refusal_missing_either_flag(self):
        for argv in ([], ["--execute-real"], ["--execution-authorized"]):
            prod = []
            _shim_production_raises(self, prod)
            with tempfile.TemporaryDirectory() as td:
                root = os.path.join(td, "s1_mcde_fresh")
                with self.assertRaises(R.Refusal) as cm:
                    R.main(argv + (["--root", root] if argv else []))
                self.assertEqual(cm.exception.code, 2)
                self.assertEqual(prod, [])
                self.assertFalse(os.path.exists(root))

    def test_exec_ledger_caps_refuse_before_exceed(self):
        led = R.Ledger()
        for _ in range(420):
            led.charge("PRIMARY")
        with self.assertRaises(R.Refusal):
            led.charge("PRIMARY")
        led2 = R.Ledger()
        for _ in range(180):
            led2.charge("SECONDARY")
        with self.assertRaises(R.Refusal):
            led2.charge("SECONDARY")
        led3 = R.Ledger()
        for _ in range(420):
            led3.charge("PRIMARY")
        for _ in range(180):
            led3.charge("SECONDARY")
        self.assertEqual(led3.counts["TOTAL"], 600)
        with self.assertRaises(R.Refusal):
            led3.charge("PRIMARY")
        led4 = R.Ledger()
        for _ in range(12):
            led4.charge("SETUP", "setup")
        with self.assertRaises(R.Refusal):
            led4.charge("SETUP", "setup")

    def test_exec_overlap_reuse_skips_rerun(self):
        calls = []
        led, seen = R.Ledger(), set()
        ident = ("PRIMARY", "screen", 27, 2026094951, 0, ((2, 1.0),),
                 ((18, 0.5), (19, 0.5)))
        kw = {"q": 32, "lambda_edge": {2: 1.0}, "rho_edge": {18: 0.5},
              "channel_sampler": fake_channel_sampler, "n_samples": 4000,
              "max_iter": 60, "seed": 2026094951}
        st1, _ = R.run_once(led, seen, ident, _make_fake_de(calls),
                            lambda: 0.0, "PRIMARY", "de", kw)
        st2, out2 = R.run_once(led, seen, ident, _make_fake_de(calls),
                               lambda: 0.0, "PRIMARY", "de", kw)
        self.assertEqual((st1, st2, out2), ("ok", "skipped", None))
        self.assertEqual(len(calls), 1)

    def test_exec_resource_gate_halts_retains_partial(self):
        prod = []
        _shim_production_raises(self, prod)
        calls = []
        tick = {"n": 0}

        def clock():
            tick["n"] += 1
            return 0.0 if tick["n"] < 8 else 99999.0

        captured = {}
        R.execute(root=os.path.join("no-such-dir", "s1_mcde_never"),
                  gamma_source=_fake_bundle(),
                  de_fn=_make_fake_de(calls), clock=clock,
                  rss_fn=lambda: 0,
                  writer=lambda root, files: captured.update(files))
        manifest = __import__("json").loads(captured["manifest.json"])
        self.assertIn("resource_blocked", manifest["terminals"].values())
        self.assertEqual(prod, [])
        self.assertGreater(len(calls), 0)
        rows = __import__("json").loads(captured["rows.json"])
        self.assertEqual(len(rows), len(calls))  # partial retained, no retry

    def test_exec_overrun_row_status_honest_fake(self):
        # P1 pin (FAKE only, zero production calls): per-call overrun persists
        # status "overrun" (never "ok") with elapsed_s > per_call_s, halts the
        # turn as resource_blocked, is excluded from ok counts/gate; a normal
        # row stays "ok".
        prod = []
        _shim_production_raises(self, prod)
        bundle = _fake_bundle()
        samplers = {"L2": R.make_centered_sampler(bundle, "L2"),
                    "JOINT": R.make_joint_sampler(bundle)}
        calls = []
        ticks = iter([0.0, 0.0,
                      R.BUDGETS["per_call_s"] + 1.0])

        def clock():
            try:
                return next(ticks)
            except StopIteration:
                return R.BUDGETS["per_call_s"] + 1.0

        rows = []
        term = R.execute_arm(
            "PRIMARY", bundle, samplers, R.Ledger(), set(),
            _make_fake_de(calls), clock, lambda: 0, 0.0, rows, {2: 1.0})
        self.assertEqual(term, "resource_blocked")  # terminal unchanged
        self.assertEqual(len(calls), 1)  # halted: no second attempt
        self.assertEqual(len(rows), 1)
        self.assertGreater(rows[0]["elapsed_s"], R.BUDGETS["per_call_s"])
        self.assertEqual(rows[0]["status"], "overrun")  # honest label
        self.assertEqual(sum(1 for r in rows
                             if r.get("status") == "ok"), 0)
        # Gate exclusion: overrun twin of a passing confirm row never counts.
        ok_row = {"arm": "PRIMARY", "phase": "confirm", "m": 44,
                  "status": "ok", "converged": True, "width": 5,
                  "f_row": 1.05}
        ov_row = dict(ok_row, status="overrun")
        gate = R.evaluate_gate([ok_row, ov_row])
        self.assertEqual(gate["PRIMARY"]["n"], 1)  # no double-count
        self.assertTrue(gate["PRIMARY"]["pass"])
        gate_ov = R.evaluate_gate([ov_row])
        self.assertEqual(gate_ov["PRIMARY"]["n"], 0)
        self.assertFalse(gate_ov["PRIMARY"]["pass"])
        self.assertIsNone(gate_ov["PRIMARY"]["f_ens"])
        # Normal path stays "ok": benign clock -> run_once ok -> _row passthru.
        led2, seen2 = R.Ledger(), set()
        kw = {"q": 32, "lambda_edge": {2: 1.0}, "rho_edge": {18: 0.5},
              "channel_sampler": fake_channel_sampler, "n_samples": 4000,
              "max_iter": 60, "seed": 2026094951}
        st, out = R.run_once(
            led2, seen2,
            ("PRIMARY", "screen", 44, 2026094951, 0,
             ((2, 1.0),), ((18, 0.5), (19, 0.5))),
            _make_fake_de([]), lambda: 0.0, "PRIMARY", "de", kw)
        self.assertEqual(st, "ok")
        row_ok = R._row("PRIMARY", "screen", 44, 1 - 44 / R.N_FRAME,
                        2026094951, 0, {2: 1.0}, {18: 0.5},
                        out["result"], 5, bundle, out["elapsed_s"],
                        status=st)
        self.assertEqual(row_ok["status"], "ok")
        self.assertEqual(prod, [])

    def test_exec_gamma_shape_mismatch_fail_closed(self):
        prod = []
        _shim_production_raises(self, prod)
        bad = dict(_fake_bundle())
        bad["gamma1"] = bad["gamma1"][:16, :]
        with self.assertRaises(R.Refusal):
            R.bind_gamma(bad)
        calls = []
        with self.assertRaises(R.Refusal):
            R.execute(root=os.path.join("no-such-dir", "s1_mcde_never"),
                      gamma_source=bad, de_fn=_make_fake_de(calls),
                      writer=lambda root, files: None)
        self.assertEqual(calls, [])
        self.assertEqual(prod, [])

    def test_exec_ban_construction_shaped_result(self):
        with self.assertRaises(R.Refusal) as cm:
            R.validate_result_row({"lambda": {2: 1.0},
                                   "parity_matrix": [[1, 0]]})
        self.assertEqual(cm.exception.code, 2)
        R.validate_result_row({"arm": "PRIMARY", "lambda": {"2": 1.0},
                               "rho": {"18": 0.5}})

    def test_exec_l1_search_attempt_refused(self):
        prod = []
        _shim_production_raises(self, prod)
        calls = []
        with self.assertRaises(R.Refusal):
            R.execute(root=os.path.join("no-such-dir", "s1_mcde_never"),
                      gamma_source=_fake_bundle(), l1_lambda={3: 1.0},
                      de_fn=_make_fake_de(calls),
                      writer=lambda root, files: None)
        self.assertEqual(calls, [])
        self.assertEqual(prod, [])

    def test_grant_gate_profile_free_execute_gated(self):
        prod = []
        _shim_production_raises(self, prod)
        with tempfile.TemporaryDirectory() as td:
            root = os.path.join(td, "s1_mcde_fresh")
            self.assertEqual(R.main(["--profile-only", "--root", root]), 0)
            self.assertFalse(os.path.exists(root))
        self.assertEqual(prod, [])


class S1SamplerBindingTest(unittest.TestCase):
    """D5 rework pins — FAKE only, zero production calls, zero disk writes."""

    def test_joint_sampler_shape_1024_vs_layer_32(self):
        prod = []
        _shim_production_raises(self, prod)
        bundle = _fake_bundle()
        l2 = R.make_centered_sampler(bundle, "L2")
        joint = R.make_joint_sampler(bundle)
        rng = np.random.default_rng(2026094951)
        for n in (1, 4, 16):
            self.assertEqual(l2(n, rng).shape, (n, 32))  # PRIMARY pairing
            self.assertEqual(joint(n, rng).shape, (n, 1024))  # SECONDARY
        rows = joint(16, np.random.default_rng(7))
        np.testing.assert_allclose(rows.sum(axis=1), 1.0, atol=1e-12)
        # R2: binding lives outside frozen_config — hash untouched by sampler keys
        cfg = R.frozen_config()
        self.assertNotIn("samplers", cfg)
        self.assertNotIn("JOINT", __import__("json").dumps(cfg))
        self.assertEqual(R.config_hash(), RECORDED_CONFIG_HASH)
        self.assertEqual(prod, [])

    def test_q_sampler_pairing_refuses_mismatch_pre_de(self):
        prod = []
        _shim_production_raises(self, prod)
        bundle = _fake_bundle()
        l1 = R.make_centered_sampler(bundle, "L1")  # (n,32): wrong for q=1024
        calls = []
        kw = {"q": 1024, "lambda_edge": {2: 1.0}, "rho_edge": {18: 0.5},
              "channel_sampler": l1, "n_samples": 4000,
              "max_iter": 60, "seed": 2026094951}
        led, seen = R.Ledger(), set()
        ident = ("SECONDARY", "screen", 27, 2026094951, 0,
                 ((2, 1.0),), ((18, 0.5), (19, 0.5)))
        with self.assertRaises(R.Refusal):
            R.run_once(led, seen, ident, _make_fake_de(calls),
                       lambda: 0.0, "SECONDARY", "de", kw)
        self.assertEqual(calls, [])  # refused BEFORE any DE call
        self.assertEqual(led.counts["TOTAL"], 0)  # ... and before charging
        calls2 = []
        good_l2 = R.make_centered_sampler(bundle, "L2")
        with self.assertRaises(R.Refusal):  # (n,32) in JOINT slot: pre-loop
            R.execute_arm("SECONDARY", bundle,
                          {"L2": good_l2, "JOINT": l1},
                          R.Ledger(), set(), _make_fake_de(calls2),
                          lambda: 0.0, lambda: 0, 0.0, [], {2: 1.0})
        self.assertEqual(calls2, [])
        with self.assertRaises(R.Refusal):  # unknown sampler key fails closed
            R.execute_arm("SECONDARY", bundle, {"L2": good_l2},
                          R.Ledger(), set(), _make_fake_de(calls2),
                          lambda: 0.0, lambda: 0, 0.0, [], {2: 1.0})
        with self.assertRaises(R.Refusal):  # unknown arm fails closed
            R.Ledger().charge("TERTIARY")
        self.assertEqual(prod, [])

    def test_execute_binds_secondary_joint_shape(self):
        prod = []
        _shim_production_raises(self, prod)
        shapes = {}

        def probing_de(q, lambda_edge, rho_edge, *, channel_sampler,
                       n_samples, max_iter, seed, entropy_tol_bits=0.01,
                       streak=20, record_entropy=True,
                       record_channel_entropy=False):
            probe = np.asarray(channel_sampler(4, np.random.default_rng(seed)))
            shapes.setdefault(q, set()).add(tuple(probe.shape))
            return {"schema": "fake", "converged": True, "iterations": 2,
                    "entropy_trace_bits": [0.01], "final_entropy_bits": 0.001,
                    "q": q, "channel_entropy_trace_bits": [0.95, 0.95]}

        captured = {}
        manifest = R.execute(
            root=os.path.join("no-such-dir", "s1_mcde_never"),
            gamma_source=_fake_bundle(), de_fn=probing_de,
            clock=lambda: 0.0, rss_fn=lambda: 0,
            writer=lambda root, files: captured.update(files))
        self.assertEqual(shapes.get(32), {(4, 32)})  # PRIMARY on L2
        self.assertEqual(shapes.get(1024), {(4, 1024)})  # SECONDARY on JOINT
        self.assertEqual(manifest["scientific_de_calls"], 600)
        self.assertEqual(manifest["ledger"],
                         {"PRIMARY": 420, "SECONDARY": 180,
                          "TOTAL": 600, "SETUP": 12})
        # h=0.95 fake, F2 ∃-converged gate on the F1 grids: PRIMARY (m2 44–60)
        # f_ens~1.01 SELECT (min valid ≤1.15); SECONDARY (m 24–31) f_ens~1.03
        # SELECT (m25 valid ≤1.15; old max-gate gave NO-IMPROVING via m31 max
        # 1.27 — gate-change update, not a weakening).
        self.assertEqual(manifest["terminals"],
                         {"PRIMARY": "SELECT", "SECONDARY": "SELECT"})
        self.assertTrue(manifest["verify"]["ok"])
        self.assertEqual(prod, [])

    def test_terminal_secondary_select_reachable_fake(self):
        prod = []
        _shim_production_raises(self, prod)
        calls = []
        captured = {}
        manifest = R.execute(
            root=os.path.join("no-such-dir", "s1_mcde_never"),
            gamma_source=_fake_bundle(),
            de_fn=_make_fake_de(calls, trace=(0.83, 0.83)),
            clock=lambda: 0.0, rss_fn=lambda: 0,
            writer=lambda root, files: captured.update(files))
        # h=0.83 physical fake: SECONDARY m24 f≈1.13 SELECT + PRIMARY m44
        # f≈1.04 SELECT (gate not rigged to fail). Old h=3.0 trace gave f<1
        # SW violations → non-pass under the fixed F2 gate, so the trace (not
        # the SELECT expectation) is updated to keep the reachability proof.
        self.assertEqual(manifest["terminals"]["SECONDARY"], "SELECT")
        self.assertEqual(manifest["terminals"]["PRIMARY"], "SELECT")
        self.assertEqual(len(calls), 600)
        self.assertEqual(prod, [])

    def test_terminal_bound_hit_fake_driven(self):
        prod = []
        _shim_production_raises(self, prod)
        calls = []
        real_propose = R.propose_trial
        R.propose_trial = lambda rng, pop, cur: {"terminal": "BOUND_HIT",
                                                 "lambda": {2: 1.0}}
        try:
            captured = {}
            manifest = R.execute(
                root=os.path.join("no-such-dir", "s1_mcde_never"),
                gamma_source=_fake_bundle(), de_fn=_make_fake_de(calls),
                clock=lambda: 0.0, rss_fn=lambda: 0,
                writer=lambda root, files: captured.update(files))
        finally:
            R.propose_trial = real_propose
        self.assertEqual(manifest["terminals"], {"PRIMARY": "BOUND_HIT"})
        self.assertEqual(calls, [])
        rows = __import__("json").loads(captured["rows.json"])
        self.assertEqual(rows, [])
        self.assertEqual(prod, [])

    def test_flip_margins_compute_only_no_promotion(self):
        import json
        rows = []
        for m in R.M_GRID:
            rows.append({"arm": "PRIMARY", "phase": "confirm", "m": m,
                         "status": "ok", "f_row": 1.0})
            rows.append({"arm": "SECONDARY", "phase": "confirm", "m": m,
                         "status": "ok",
                         "f_row": 0.85 if m in (27, 29, 30) else 1.05})
        before = json.dumps(rows, sort_keys=True)
        res = R.evaluate_flip_rule(rows)
        self.assertEqual(set(res), {"margins", "wins", "flip", "note"})
        for m in (27, 29, 30):
            self.assertAlmostEqual(res["margins"][m], 0.15)
        self.assertEqual(set(res["wins"]), {27, 29, 30})
        self.assertTrue(res["flip"])  # wins incl m27/m29, >=2 pts
        self.assertEqual(res["note"], "computed only; no auto-promotion")
        self.assertEqual(json.dumps(rows, sort_keys=True), before)
        near = [dict(r, f_row=0.98)
                if (r["arm"] == "SECONDARY" and r["m"] == 29) else r
                for r in rows]
        res2 = R.evaluate_flip_rule(near)
        self.assertAlmostEqual(res2["margins"][29], 0.02)
        self.assertNotIn(29, res2["wins"])
        self.assertFalse(res2["flip"])  # required-m rule kills the flip

    def test_verify_manifest_hash_fens_anchors(self):
        prod = []
        _shim_production_raises(self, prod)
        # F2 ∃-converged gate update (not a weakening): rows carry converged +
        # width on the F1 grids; f values in the physical ≥1 range (old 0.5 /
        # 0.8 / 0.9 were SW-violating <1, now excluded from every pass).
        rows = [
            {"arm": "PRIMARY", "phase": "confirm", "m": 44,
             "status": "ok", "converged": True, "width": 5, "f_row": 1.05},
            {"arm": "PRIMARY", "phase": "confirm", "m": 45,
             "status": "ok", "converged": True, "width": 5, "f_row": 1.10},
            {"arm": "PRIMARY", "phase": "screen", "m": 44,
             "status": "ok", "converged": True, "width": 5,
             "f_row": 1.01},  # ignored: screen phase
            {"arm": "SECONDARY", "phase": "confirm", "m": 24,
             "status": "ok", "converged": True, "width": 10, "f_row": 1.20},
            {"arm": "SECONDARY", "phase": "confirm", "m": 25,
             "status": "ok", "converged": True, "width": 10, "f_row": 1.25},
            {"arm": "SECONDARY", "phase": "confirm", "m": 25,
             "status": "error"},  # ignored: non-ok
        ]
        gate = R.evaluate_gate(rows)
        self.assertEqual(gate["PRIMARY"],
                         {"f_ens": 1.05, "n": 2, "pass": True,
                          "sw_violations": 0})
        self.assertEqual(gate["SECONDARY"],
                         {"f_ens": 1.20, "n": 2, "pass": False,
                          "sw_violations": 0})
        manifest = {"config_hash": R.config_hash(), "gate": gate}
        v = R.verify_manifest(manifest, rows)
        self.assertTrue(v["hash_ok"] and v["gate_match"] and v["ok"])
        self.assertEqual(v["gate_recomputed"], gate)
        # F2: verify.ok is non-adjudicating (hash + gate-recompute only).
        self.assertIn("non-adjudicating", v["note"])
        self.assertAlmostEqual(v["anchors"]["L1"], 0.02566, places=5)
        self.assertAlmostEqual(v["anchors"]["L2"], 0.80690, places=5)
        exp = v["recompute_expected"]
        self.assertAlmostEqual(exp["27"]["f_implied"],
                               10 * 27 / (256 * (R.H_ANCHORS["L1"]
                                                 + R.H_ANCHORS["L2"])))
        bad = dict(manifest, config_hash="0" * 64)
        vb = R.verify_manifest(bad, rows)
        self.assertFalse(vb["hash_ok"] or vb["ok"])
        self.assertEqual(prod, [])


def _fake_concentrated_bundle():
    """FAKE [u1,u2,b] bundle where XOR vs cyclic-shift are distinguishable.

    U1 delta at 5; P(U2|B,U1=5) bimodal 7(0.6)/8(0.4); other-U1 rows
    fallback delta-at-0. XOR secondary mass lands at 8^7=15; a
    cyclic-shift would land it at 1. Uniform-U1 would rarely hit U1=5
    (unimodal delta-at-0, no mass at 15)."""
    g1 = np.zeros((32, 1024))
    g1[5, :] = 1.0
    g2 = np.zeros((32, 32, 1024))
    for b in range(1024):
        g2[5, 7, b] = 0.6
        g2[5, 8, b] = 0.4
        for u1 in range(32):
            if u1 != 5:
                g2[u1, 0, b] = 1.0
    # F3: explicitly-flagged fake (uniform-p_b fallback is fake-only).
    return {"gamma1": g1, "gamma2": g2, "H_L1": 0.025, "H_L2": 0.80,
            R.FAKE_BUNDLE_FLAG: True}


class S1Q0SamplerSemanticsTest(unittest.TestCase):
    """Q0 fix pins — FAKE only, zero production calls, zero disk writes."""

    def test_q0_xor_centering_distinguishable_fake(self):
        prod = []
        _shim_production_raises(self, prod)
        bundle = _fake_concentrated_bundle()
        R.bind_gamma(bundle)  # axis=1 normalized; must not refuse
        l2 = R.make_centered_sampler(bundle, "L2")
        rows = l2(4000, np.random.default_rng(2026094951))
        self.assertEqual(rows.shape, (4000, 32))
        np.testing.assert_allclose(rows.sum(axis=1), 1.0, atol=1e-12)
        mean = rows.mean(axis=0)
        self.assertGreater(mean[15], 0.30)  # XOR secondary 8^7=15
        self.assertLess(mean[1], 0.01)  # cyclic-shift secondary would be 1
        self.assertGreater(mean[0], 0.40)  # truth mass at 0
        joint = R.make_joint_sampler(bundle)
        jrows = joint(4000, np.random.default_rng(2026094951))
        self.assertEqual(jrows.shape, (4000, 1024))
        np.testing.assert_allclose(jrows.sum(axis=1), 1.0, atol=1e-12)
        jmean = jrows.mean(axis=0)
        # joint U=U1<<5|U2: true 167/168, XOR secondary 168^167=15
        self.assertGreater(jmean[15], 0.30)
        self.assertLess(jmean[1], 0.01)
        self.assertGreater(jmean[0], 0.40)
        self.assertEqual(prod, [])

    def test_q0_empirical_b_sampling_distinguishable_fake(self):
        prod = []
        _shim_production_raises(self, prod)
        g1 = np.zeros((32, 1024))
        g1[5, 0] = 1.0  # B=0: concentrated
        g1[:, 1] = 1.0 / 32  # B=1: uniform
        g1[0, 2:] = 1.0
        g2 = np.zeros((32, 32, 1024))
        for b in range(1024):
            for u1 in range(32):
                g2[u1, 0, b] = 1.0
        bundle0 = {"gamma1": g1, "gamma2": g2, "H_L1": 0.5,
                   "H_L2": 0.80, "p_b": np.eye(1024)[0]}
        bundle1 = {"gamma1": g1, "gamma2": g2, "H_L1": 0.5,
                   "H_L2": 0.80, "p_b": np.eye(1024)[1]}
        l1a = R.make_centered_sampler(bundle0, "L1")
        l1b = R.make_centered_sampler(bundle1, "L1")
        ra = l1a(512, np.random.default_rng(11)).mean(axis=0)
        rb = l1b(512, np.random.default_rng(11)).mean(axis=0)
        # p_b=B0 -> delta-at-0 rows (mean[0]=1); p_b=B1 -> uniform (1/32)
        self.assertAlmostEqual(ra[0], 1.0, places=12)
        self.assertAlmostEqual(rb[0], 1.0 / 32, places=12)
        self.assertGreater(abs(ra[0] - rb[0]), 0.5)  # B matters: empirical
        self.assertEqual(prod, [])

    def test_q0_no_uniform_int_or_cyclic_shift_in_samplers(self):
        import ast
        import inspect
        prod = []
        _shim_production_raises(self, prod)
        for fn in (R.make_centered_sampler, R.make_joint_sampler):
            tree = ast.parse(inspect.getsource(fn))
            attrs = [n.attr for n in ast.walk(tree)
                     if isinstance(n, ast.Attribute)]
            self.assertNotIn("integers", attrs)  # uniform-int path gone
            self.assertNotIn("roll", attrs)  # cyclic-shift path gone
            self.assertIn("choice", attrs)  # empirical pick with p
            ops = [type(n.op).__name__ for n in ast.walk(tree)
                   if isinstance(n, ast.BinOp)]
            self.assertIn("BitXor", ops)  # XOR/GF-add centering
        self.assertFalse(hasattr(R, "_uniform_b"))
        self.assertFalse(hasattr(R, "make_uniform_b_sampler"))
        self.assertEqual(prod, [])


class S1Q5AxisRegressionTest(unittest.TestCase):
    """Q5 branch-a pins — gamma npz read-only, FAKE DE (zero prod calls)."""

    GAMMA_PATH = "docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz"

    def test_q5_axis_entropy_signature_pins_u1_u2(self):
        prod = []
        _shim_production_raises(self, prod)
        npz = np.load(self.GAMMA_PATH)  # read-only; never refit
        try:
            g1 = np.asarray(npz["2M_gamma1_L1"], dtype=np.float64)
            g2 = np.asarray(npz["2M_gamma2_L2condU1"], dtype=np.float64)
            h1 = float(npz["2M_H_L1"])
            h2 = float(npz["2M_H_L2"])
        finally:
            npz.close()
        # axis labels pinned: axis=1 normalized (U2), axis=0 not (U1 cond)
        self.assertTrue(np.allclose(g2.sum(axis=1), 1.0, atol=1e-9))
        self.assertFalse(np.allclose(g2.sum(axis=0), 1.0, atol=1e-9))
        pb = np.full(1024, 1.0 / 1024)  # read-only neutral (no p_b in file)

        def _ent(p):
            p = p[p > 0]
            return float(-np.sum(p * np.log2(p)))

        h0 = sum(pb[b] * _ent(g1[:, b]) for b in range(1024))
        h1 = 0.0
        for b in range(1024):
            for u1 in range(32):
                w = g1[u1, b] * pb[b]
                row = g2[u1, :, b]
                row = row[row > 0]
                if w > 0 and row.size:
                    h1 += w * float(-np.sum(row * np.log2(row)))
        self.assertAlmostEqual(h0, 0.02566205, delta=0.002)  # axis0 IS U1
        self.assertAlmostEqual(h1, 0.80690067, delta=0.002)  # axis1 IS U2
        self.assertAlmostEqual(h1, h2, delta=0.002)
        self.assertGreater(h1 / h0, 20)  # ~30x separation, unmistakable
        self.assertEqual(prod, [])

    def test_q5_runner_indexing_consistent_with_pinned_labels(self):
        prod = []
        _shim_production_raises(self, prod)
        bundle = R.bind_gamma(self.GAMMA_PATH, "2M")  # file branch
        self.assertEqual(bundle["gamma1"].shape, (32, 1024))
        bad = dict(bundle)
        bad["gamma2"] = bundle["gamma2"].transpose(1, 0, 2)
        with self.assertRaises(R.Refusal):  # transposed axes fail closed
            R.bind_gamma(bad)
        fake = _fake_concentrated_bundle()
        l2 = R.make_centered_sampler(fake, "L2")
        mean = l2(4000, np.random.default_rng(7)).mean(axis=0)
        # [u1,u2,b] indexing: rows g2[5,:,b] bimodal -> XOR mass at 15
        self.assertGreater(mean[15], 0.30)
        self.assertLess(mean[1], 0.01)
        self.assertEqual(prod, [])


class S1PbBindingTest(unittest.TestCase):
    """F3 p_b-binding pins — FAKE DE only, zero production calls.

    Production path binds empirical train P(B) from the sibling sidecar;
    uniform fallback exists ONLY for bundles carrying the frozen fake flag.
    """

    GAMMA_PATH = "docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz"
    SIDECAR_PATH = "docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03_pb.npz"

    def test_pb_file_bound_bundle_carries_normalized_pb(self):
        prod = []
        _shim_production_raises(self, prod)
        side = np.load(self.SIDECAR_PATH)  # read-only; never refit
        try:
            for src in ("1M", "1p5M", "2M"):
                bundle = R.bind_gamma(self.GAMMA_PATH, src)
                pb = bundle["p_b"]
                self.assertEqual(tuple(np.shape(pb)), (1024,))
                self.assertTrue(np.all(np.asarray(pb) >= 0.0))
                self.assertAlmostEqual(float(np.sum(pb)), 1.0, delta=1e-9)
                np.testing.assert_array_equal(
                    np.asarray(pb), np.asarray(side[f"{src}_p_b"]))
        finally:
            side.close()
        self.assertEqual(prod, [])

    def test_pb_sampler_honors_bound_pb(self):
        prod = []
        _shim_production_raises(self, prod)
        # distinct fake p_b vectors -> distinct sampler behavior (same seed).
        g1 = np.zeros((32, 1024))
        g1[5, 0] = 1.0
        g1[:, 1] = 1.0 / 32
        g1[0, 2:] = 1.0
        g2 = np.zeros((32, 32, 1024))
        for b in range(1024):
            for u1 in range(32):
                g2[u1, 0, b] = 1.0
        mk = lambda b: {"gamma1": g1, "gamma2": g2, "H_L1": 0.5,
                        "H_L2": 0.80, "p_b": np.eye(1024)[b],
                        R.FAKE_BUNDLE_FLAG: True}
        ra = R.make_centered_sampler(mk(0), "L1")(
            256, np.random.default_rng(11)).mean(axis=0)
        rb = R.make_centered_sampler(mk(1), "L1")(
            256, np.random.default_rng(11)).mean(axis=0)
        self.assertGreater(abs(ra[0] - rb[0]), 0.5)
        # file-bound bundle drives real samplers (shape + rowsums).
        bundle = R.bind_gamma(self.GAMMA_PATH, "2M")
        rng = np.random.default_rng(2026094951)
        for samp, q in ((R.make_centered_sampler(bundle, "L2"), 32),
                        (R.make_joint_sampler(bundle), 1024)):
            rows = samp(8, rng)
            self.assertEqual(rows.shape, (8, q))
            np.testing.assert_allclose(rows.sum(axis=1), 1.0, atol=1e-12)
        # production-shaped bundle without p_b and without the fake flag:
        # sampler construction itself refuses (both makers).
        unbound = {k: v for k, v in _fake_bundle().items()
                   if k not in ("p_b", R.FAKE_BUNDLE_FLAG)}
        for fn, layer in ((R.make_centered_sampler, "L1"),
                          (R.make_centered_sampler, "L2"),
                          (R.make_joint_sampler, None)):
            with self.assertRaises(R.Refusal):
                fn(unbound) if layer is None else fn(unbound, layer)
        self.assertEqual(prod, [])

    def test_pb_absent_pb_production_bind_refuses(self):
        prod = []
        _shim_production_raises(self, prod)
        calls = []
        # gamma-only file with NO sibling sidecar -> file bind refuses.
        with tempfile.TemporaryDirectory() as td:
            only = os.path.join(td, "gamma_only.npz")
            src = np.load(self.GAMMA_PATH)
            try:
                np.savez_compressed(
                    only, **{k: np.asarray(src[k]) for k in src.files})
            finally:
                src.close()
            with self.assertRaises(R.Refusal):
                R.bind_gamma(only, "2M")
            with self.assertRaises(R.Refusal):
                R.execute(root=os.path.join(td, "s1_mcde_never"),
                          gamma_source=only, source="2M",
                          de_fn=_make_fake_de(calls),
                          writer=lambda root, files: None)
        # production-shaped dict without p_b and without the fake flag refuses.
        unflagged = {k: v for k, v in _fake_bundle().items()
                     if k != R.FAKE_BUNDLE_FLAG}
        with self.assertRaises(R.Refusal):
            R.bind_gamma(unflagged)
        with self.assertRaises(R.Refusal):
            R.execute(root=os.path.join("no-such-dir", "s1_mcde_never"),
                      gamma_source=unflagged, de_fn=_make_fake_de(calls),
                      writer=lambda root, files: None)
        self.assertEqual(calls, [])
        self.assertEqual(prod, [])

    def test_pb_reverify_anchors_empirical_pb(self):
        prod = []
        _shim_production_raises(self, prod)

        def _ent(p):
            p = p[p > 0]
            return float(-np.sum(p * np.log2(p)))

        g = np.load(self.GAMMA_PATH)  # read-only; never refit
        s = np.load(self.SIDECAR_PATH)  # read-only; never refit
        try:
            for src in ("1M", "1p5M", "2M"):
                g1 = np.asarray(g[f"{src}_gamma1_L1"], dtype=np.float64)
                g2 = np.asarray(g[f"{src}_gamma2_L2condU1"], dtype=np.float64)
                h1s, h2s = float(g[f"{src}_H_L1"]), float(g[f"{src}_H_L2"])
                pb = np.asarray(s[f"{src}_p_b"], dtype=np.float64)
                h1 = sum(pb[b] * _ent(g1[:, b]) for b in range(1024)
                         if pb[b] > 0)
                h2 = 0.0
                for b in range(1024):
                    if pb[b] <= 0:
                        continue
                    for u1 in range(32):
                        w = g1[u1, b] * pb[b]
                        if w > 0:
                            h2 += w * _ent(g2[u1, :, b])
                # empirical-p_b recompute reproduces the stored anchors.
                self.assertAlmostEqual(h1, h1s, delta=1e-9)
                self.assertAlmostEqual(h2, h2s, delta=1e-9)
                # STOP gate mirrored in code: shift vs uniform must stay <0.01.
                pu = np.full(1024, 1.0 / 1024)
                u1 = sum(pu[b] * _ent(g1[:, b]) for b in range(1024))
                u2 = sum(pu[b] * g1[u1x, b] * _ent(g2[u1x, :, b])
                         for b in range(1024) for u1x in range(32)
                         if pu[b] * g1[u1x, b] > 0)
                self.assertLess(abs(h1 - u1), 0.01)
                self.assertLess(abs(h2 - u2), 0.01)
        finally:
            g.close()
            s.close()
        # 2M uniform recompute vs reviewer values (kept outside the npz
        # context since g/s are closed above; recomputed read-only again).
        g2r = np.load(self.GAMMA_PATH)
        try:
            g1 = np.asarray(g2r["2M_gamma1_L1"], dtype=np.float64)
            g2 = np.asarray(g2r["2M_gamma2_L2condU1"], dtype=np.float64)
        finally:
            g2r.close()
        pu = np.full(1024, 1.0 / 1024)
        ru1 = sum(pu[b] * _ent(g1[:, b]) for b in range(1024))
        ru2 = sum(pu[b] * g1[u1x, b] * _ent(g2[u1x, :, b])
                  for b in range(1024) for u1x in range(32)
                  if pu[b] * g1[u1x, b] > 0)
        self.assertAlmostEqual(ru1, 0.02537264, delta=1e-7)
        self.assertAlmostEqual(ru2, 0.80696232, delta=1e-7)
        self.assertEqual(prod, [])


class S1CheckpointResumeTest(unittest.TestCase):
    """K1-K4 checkpoint/resume pins — FAKE only, zero production calls.

    Wall-clock fields excluded from byte-identity (enumerated): per-row
    ``elapsed_s`` + ``provenance.root`` (temp paths differ) — everything else
    (identities/seeds/config/gates/budgets/ledger/rows) must be identical.
    ``resume.wall_start`` is 0.0 under the fake clock so it matches exactly.
    """

    def _run_single_shot_history(self, prod, trace=(0.70, 0.69, 0.68)):
        _shim_production_raises(self, prod)
        hist = []

        def _w(root, files):
            hist.append(dict(files))

        calls = []
        R.execute(root=os.path.join("no-such-dir", "s1_mcde_never_hist"),
                  gamma_source=_fake_bundle(),
                  de_fn=_make_fake_de(calls, trace=trace),
                  clock=lambda: 0.0, rss_fn=lambda: 0, writer=_w)
        return hist, calls

    @staticmethod
    def _strip_manifest(m):
        m = dict(m)
        m.pop("verify", None)
        # wall_windows is operational wall-clock (1 entry single-shot vs 2
        # resumed by design): excluded, enumerated (like elapsed_s/root) —
        # both the top-level manifest copy and the nested resume-state copy.
        # resume.wall_start stays asserted (matches exactly under fake clock).
        m.pop("wall_windows", None)
        res = dict(m.get("resume", {}))
        res.pop("wall_windows", None)
        m["resume"] = res
        prov = dict(m.get("provenance", {}))
        prov["root"] = "X"  # temp paths differ: excluded, enumerated
        m["provenance"] = prov
        return m

    @staticmethod
    def _strip_rows(rows):
        return [{k: v for k, v in r.items() if k != "elapsed_s"}
                for r in rows]  # wall-clock: excluded, enumerated

    def test_k1_checkpoint_per_eval_presence(self):
        prod = []
        hist, calls = self._run_single_shot_history(prod)
        self.assertEqual(len(calls), 600)
        self.assertGreater(len(hist), 600)  # per-eval flush + done + final
        first = json.loads(hist[0]["manifest.json"])
        first_rows = json.loads(hist[0]["rows.json"])
        self.assertIn("manifest.json", hist[0])
        self.assertGreater(len(first_rows), 0)  # exists after N>0 evals
        self.assertEqual(first["ledger"]["TOTAL"], len(first_rows))
        self.assertEqual(len(first["completed_identities"]), len(first_rows))
        # verbatim seen-set: decode round-trips without duplication
        seen = {tuple(R._decode_identity(e)) for e in
                first["completed_identities"]}
        self.assertEqual(len(seen), len(first_rows))
        self.assertEqual(prod, [])

    def test_k2_two_phase_equivalence_half(self):
        prod = []
        hist, calls1 = self._run_single_shot_history(prod)
        m1 = json.loads(hist[-1]["manifest.json"])
        r1 = json.loads(hist[-1]["rows.json"])
        self.assertEqual(m1["ledger"],
                         {"PRIMARY": 420, "SECONDARY": 180,
                          "TOTAL": 600, "SETUP": 12})
        # Half prefix N=300 (PRIMARY screen 280 + 20 confirm).
        pref = next(f for f in hist
                    if len(json.loads(f["rows.json"])) == 300)
        mm, rr = (json.loads(pref["manifest.json"]),
                  json.loads(pref["rows.json"]))
        self.assertEqual(mm["ledger"]["TOTAL"], 300)
        self.assertEqual(len(mm["completed_identities"]), 300)
        with tempfile.TemporaryDirectory() as td:
            proot = os.path.join(td, "partial")
            os.makedirs(proot)
            with open(os.path.join(proot, "manifest.json"), "w") as fh:
                fh.write(json.dumps(mm, sort_keys=True, indent=1,
                                    default=str))
            with open(os.path.join(proot, "rows.json"), "w") as fh:
                fh.write(json.dumps(rr, sort_keys=True, indent=1,
                                    default=str))
            prod2 = []
            _shim_production_raises(self, prod2)
            calls2 = []
            m2 = R.execute(
                root=proot, gamma_source=_fake_bundle(),
                de_fn=_make_fake_de(calls2), clock=lambda: 0.0,
                rss_fn=lambda: 0, resume_from=proot)
            # Ledger continuity: resumed charges ONLY missing; totals==caps.
            self.assertEqual(len(calls2), 600 - 300)
            self.assertEqual(m2["ledger"],
                             {"PRIMARY": 420, "SECONDARY": 180,
                              "TOTAL": 600, "SETUP": 12})
            self.assertEqual(m2["scientific_de_calls"], 600)
            self.assertTrue(m1["verify"]["ok"])
            self.assertTrue(m2["verify"]["ok"])
            m2f = json.load(open(os.path.join(proot, "manifest.json")))
            r2 = json.load(open(os.path.join(proot, "rows.json")))
            self.assertEqual(
                json.dumps(self._strip_manifest(m1), sort_keys=True,
                           default=str),
                json.dumps(self._strip_manifest(m2f), sort_keys=True,
                           default=str))  # BYTE-IDENTICAL mod wall-clock
            self.assertEqual(
                json.dumps(self._strip_rows(r1), sort_keys=True,
                           default=str),
                json.dumps(self._strip_rows(r2), sort_keys=True,
                           default=str))
            self.assertEqual(prod2, [])
        self.assertEqual(prod, [])

    def test_k2_odd_n_resume_equivalence(self):
        # Odd-N resume pins — FAKE only, zero production calls.
        # Mid-trial snapshots (odd screen-N) persist lam + [fit0] + si=1;
        # resume SKIPS propose_trial, reuses lam (rho via make_rho, fit0 via
        # cached row) and runs ONLY missing si=1. Operator-picked extras:
        # N=451 (odd SECONDARY-screen mid-trial: 420 PRIMARY + 31) +
        # N=350 (PRIMARY confirm boundary: 280 screen + 70 confirm).
        prod = []
        hist, calls1 = self._run_single_shot_history(prod)
        m1 = json.loads(hist[-1]["manifest.json"])
        r1 = json.loads(hist[-1]["rows.json"])
        self.assertEqual(len(calls1), 600)
        self.assertTrue(m1["verify"]["ok"])
        for n in (1, 3, 51, 421, 451, 350):
            with self.subTest(n=n):
                pref = next(f for f in hist
                            if len(json.loads(f["rows.json"])) == n)
                mm, rr = (json.loads(pref["manifest.json"]),
                          json.loads(pref["rows.json"]))
                with tempfile.TemporaryDirectory() as td:
                    proot = os.path.join(td, "partial")
                    os.makedirs(proot)
                    with open(os.path.join(proot, "manifest.json"),
                              "w") as fh:
                        fh.write(json.dumps(mm, sort_keys=True, indent=1,
                                            default=str))
                    with open(os.path.join(proot, "rows.json"), "w") as fh:
                        fh.write(json.dumps(rr, sort_keys=True, indent=1,
                                            default=str))
                    prod2 = []
                    _shim_production_raises(self, prod2)
                    calls2 = []
                    m2 = R.execute(
                        root=proot, gamma_source=_fake_bundle(),
                        de_fn=_make_fake_de(calls2), clock=lambda: 0.0,
                        rss_fn=lambda: 0, resume_from=proot)
                    self.assertEqual(len(calls2), 600 - n)
                    self.assertEqual(m2["ledger"],
                                     {"PRIMARY": 420, "SECONDARY": 180,
                                      "TOTAL": 600, "SETUP": 12})
                    self.assertEqual(m2["scientific_de_calls"], 600)
                    self.assertTrue(m2["verify"]["ok"])
                    m2f = json.load(
                        open(os.path.join(proot, "manifest.json")))
                    r2 = json.load(open(os.path.join(proot, "rows.json")))
                    self.assertEqual(
                        json.dumps(self._strip_manifest(m1), sort_keys=True,
                                   default=str),
                        json.dumps(self._strip_manifest(m2f), sort_keys=True,
                                   default=str))
                    self.assertEqual(
                        json.dumps(self._strip_rows(r1), sort_keys=True,
                                   default=str),
                        json.dumps(self._strip_rows(r2), sort_keys=True,
                                   default=str))
                    self.assertEqual(prod2, [])
        self.assertEqual(prod, [])

    def test_k3_root_exists_matrix(self):
        # absent+no-flag -> fresh run (fake root cleaned, real fs temp dir).
        prod = []
        _shim_production_raises(self, prod)
        with tempfile.TemporaryDirectory() as td:
            fresh = os.path.join(td, "fresh")
            calls = []
            m = R.execute(root=fresh, gamma_source=_fake_bundle(),
                          de_fn=_make_fake_de(calls), clock=lambda: 0.0,
                          rss_fn=lambda: 0)
            self.assertEqual(m["ledger"]["TOTAL"], 600)
            self.assertTrue(os.path.exists(
                os.path.join(fresh, "manifest.json")))
            # present+no-flag -> refuse (existing behavior, no overwrite).
            prod_r = []
            _shim_production_raises(self, prod_r)
            with self.assertRaises(R.Refusal) as cm:
                R.execute(root=fresh, gamma_source=_fake_bundle(),
                          de_fn=_make_fake_de([]), clock=lambda: 0.0,
                          rss_fn=lambda: 0)
            self.assertEqual(cm.exception.code, 2)
            self.assertEqual(prod_r, [])
            # present-valid-partial+flag -> resume (uses equivalence prefix).
            hist, _ = self._run_single_shot_history([])
            pref = next(f for f in hist
                        if len(json.loads(f["rows.json"])) == 50)
            pdir = os.path.join(td, "partial")
            os.makedirs(pdir)
            open(os.path.join(pdir, "manifest.json"), "w").write(
                pref["manifest.json"])
            open(os.path.join(pdir, "rows.json"), "w").write(
                pref["rows.json"])
            calls3 = []
            m3 = R.execute(root=pdir, gamma_source=_fake_bundle(),
                           de_fn=_make_fake_de(calls3), clock=lambda: 0.0,
                           rss_fn=lambda: 0, resume_from=pdir)
            self.assertEqual(m3["ledger"]["TOTAL"], 600)
            self.assertEqual(len(calls3), 550)
        # absent+flag -> refuse (nothing to resume, zero calls).
        with tempfile.TemporaryDirectory() as td:
            missing = os.path.join(td, "absent_partial")
            prod_m = []
            _shim_production_raises(self, prod_m)
            with self.assertRaises(R.Refusal) as cm:
                R.execute(root=missing, gamma_source=_fake_bundle(),
                          de_fn=_make_fake_de([]), clock=lambda: 0.0,
                          rss_fn=lambda: 0, resume_from=missing)
            self.assertEqual(cm.exception.code, 2)
            self.assertEqual(prod_m, [])
        # present-invalid -> refuse always (both with and without flag).
        with tempfile.TemporaryDirectory() as td:
            bad = os.path.join(td, "bad")
            os.makedirs(bad)
            open(os.path.join(bad, "manifest.json"), "w").write("{corrupt")
            open(os.path.join(bad, "rows.json"), "w").write("[]")
            for kw in ({}, {"resume_from": bad}):
                prod_b = []
                _shim_production_raises(self, prod_b)
                root = bad if not kw else kw["resume_from"]
                with self.assertRaises(R.Refusal):
                    R.execute(root=root, gamma_source=_fake_bundle(),
                              de_fn=_make_fake_de([]), clock=lambda: 0.0,
                              rss_fn=lambda: 0, **kw)
                self.assertEqual(prod_b, [])
        # NEVER silent auto-resume: present partial + no flag refuses.
        with tempfile.TemporaryDirectory() as td:
            hist, _ = self._run_single_shot_history([])
            pref = next(f for f in hist
                        if len(json.loads(f["rows.json"])) == 10)
            pdir = os.path.join(td, "partial_nosilent")
            os.makedirs(pdir)
            open(os.path.join(pdir, "manifest.json"), "w").write(
                pref["manifest.json"])
            open(os.path.join(pdir, "rows.json"), "w").write(
                pref["rows.json"])
            prod_n = []
            _shim_production_raises(self, prod_n)
            with self.assertRaises(R.Refusal) as cm:
                R.execute(root=pdir, gamma_source=_fake_bundle(),
                          de_fn=_make_fake_de([]), clock=lambda: 0.0,
                          rss_fn=lambda: 0)
            self.assertEqual(cm.exception.code, 2)
            self.assertEqual(prod_n, [])
        self.assertEqual(prod, [])

    def test_k2_invalid_partial_refusals_zero_calls(self):
        prod = []
        hist, _ = self._run_single_shot_history(prod)
        pref = next(f for f in hist
                    if len(json.loads(f["rows.json"])) == 50)
        base_m = json.loads(pref["manifest.json"])
        base_r = json.loads(pref["rows.json"])

        def _try_bad(mut, rows=None, source="2M"):
            with tempfile.TemporaryDirectory() as td:
                pdir = os.path.join(td, "p")
                os.makedirs(pdir)
                open(os.path.join(pdir, "manifest.json"), "w").write(
                    json.dumps(mut, sort_keys=True, default=str))
                open(os.path.join(pdir, "rows.json"), "w").write(
                    json.dumps(base_r if rows is None else rows,
                               sort_keys=True, default=str))
                calls = []
                with self.assertRaises(R.Refusal) as cm:
                    R.execute(root=pdir, gamma_source=_fake_bundle(),
                              de_fn=_make_fake_de(calls), clock=lambda: 0.0,
                              rss_fn=lambda: 0, resume_from=pdir,
                              source=source)
                self.assertEqual(cm.exception.code, 2)
                self.assertEqual(calls, [])

        bad_hash = dict(base_m, config_hash="0" * 64)
        _try_bad(bad_hash)
        bad_seeds = dict(base_m, seeds={"screen": [1, 2], "confirm": [1, 2]})
        _try_bad(bad_seeds)
        bad_bud = dict(base_m, budgets={"wall_total_s": 1})
        _try_bad(bad_bud)
        dup = dict(base_m, completed_identities=(
            base_m["completed_identities"] +
            base_m["completed_identities"][:1]))
        _try_bad(dup)
        missing = dict(base_m, completed_identities=[])
        _try_bad(missing)
        _try_bad(base_m, source="1M")  # foreign source
        # CLI: resume-from without --execute-real refuses pre-anything.
        with self.assertRaises(R.Refusal):
            R.main(["--resume-from", "x"])
        self.assertEqual(prod, [])


class S1WallRestartTest(unittest.TestCase):
    """W1-W3 wall-restart pins — FAKE only, zero production calls.

    Wall = per-turn operational safety (fresh window at resume time, SAME
    3600s cap); ledger = frozen scientific budget (continues verbatim).
    """

    def _hist(self, prod):
        _shim_production_raises(self, prod)
        hist = []
        calls = []
        R.execute(root=os.path.join("no-such-dir", "s1_mcde_never_hist"),
                  gamma_source=_fake_bundle(),
                  de_fn=_make_fake_de(calls),
                  clock=lambda: 0.0, rss_fn=lambda: 0,
                  writer=lambda root, files: hist.append(dict(files)))
        return hist, calls

    @staticmethod
    def _write_partial(td, manifest, rows):
        proot = os.path.join(td, "partial")
        os.makedirs(proot)
        with open(os.path.join(proot, "manifest.json"), "w") as fh:
            fh.write(json.dumps(manifest, sort_keys=True, indent=1,
                                default=str))
        with open(os.path.join(proot, "rows.json"), "w") as fh:
            fh.write(json.dumps(rows, sort_keys=True, indent=1,
                                default=str))
        return proot

    def test_w1_resume_restarts_exhausted_wall(self):
        prod = []
        hist, _ = self._hist(prod)
        pref = next(f for f in hist
                    if len(json.loads(f["rows.json"])) == 50)
        mm = json.loads(pref["manifest.json"])
        rr = json.loads(pref["rows.json"])
        # Mimic the on-disk S1 389-call turn: pre-wall-windows shape (no
        # wall_windows key; resume synthesizes one window from wall_start).
        mm.pop("wall_windows", None)
        mm["resume"].pop("wall_windows", None)
        with tempfile.TemporaryDirectory() as td:
            proot = self._write_partial(td, mm, rr)
            prod2 = []
            _shim_production_raises(self, prod2)
            calls2 = []
            now = {"t": 5000.0}  # old window (turn_start=0) long exhausted

            def clock():
                t = now["t"]
                now["t"] += 1.0
                return t

            m2 = R.execute(
                root=proot, gamma_source=_fake_bundle(),
                de_fn=_make_fake_de(calls2), clock=clock,
                rss_fn=lambda: 0, resume_from=proot)
            # Fresh window: proceeds to completion (old window would block
            # instantly with 0 calls).
            self.assertEqual(len(calls2), 600 - 50)
            # Exact ledger continuity: no reset, no double-charge.
            self.assertEqual(m2["ledger"],
                             {"PRIMARY": 420, "SECONDARY": 180,
                              "TOTAL": 600, "SETUP": 12})
            self.assertEqual(m2["scientific_de_calls"], 600)
            # Windows appended (synthesized first + fresh second, SAME cap).
            self.assertEqual(m2["wall_windows"],
                             [{"turn_start": 0.0, "cap": 3600},
                              {"turn_start": 5000.0, "cap": 3600}])
            self.assertEqual(m2["wall_windows"][1]["cap"],
                             R.BUDGETS["wall_total_s"])
            self.assertTrue(m2["verify"]["ok"])
            self.assertEqual(prod2, [])
        self.assertEqual(prod, [])

    def test_w2_fresh_run_single_window_unchanged(self):
        prod = []
        _shim_production_raises(self, prod)
        calls = []
        captured = {}
        m = R.execute(
            root=os.path.join("no-such-dir", "s1_mcde_never"),
            gamma_source=_fake_bundle(), de_fn=_make_fake_de(calls),
            clock=lambda: 0.0, rss_fn=lambda: 0,
            writer=lambda root, files: captured.update(files))
        self.assertEqual(m["wall_windows"],
                         [{"turn_start": 0.0, "cap": 3600}])
        self.assertEqual(m["ledger"],
                         {"PRIMARY": 420, "SECONDARY": 180,
                          "TOTAL": 600, "SETUP": 12})
        self.assertEqual(len(calls), 600)
        self.assertEqual(prod, [])

    def test_w3_mid_resume_exhaustion_blocked_retained(self):
        prod = []
        hist, _ = self._hist(prod)
        pref = next(f for f in hist
                    if len(json.loads(f["rows.json"])) == 50)
        mm = json.loads(pref["manifest.json"])
        rr = json.loads(pref["rows.json"])
        with tempfile.TemporaryDirectory() as td:
            proot = self._write_partial(td, mm, rr)
            prod2 = []
            _shim_production_raises(self, prod2)
            calls2 = []
            tick = {"n": 0}

            def clock():
                tick["n"] += 1
                # Fresh window opens at 5000, then exhausts mid-resume.
                return 5000.0 if tick["n"] <= 12 else 5000.0 + 3601.0

            m2 = R.execute(
                root=proot, gamma_source=_fake_bundle(),
                de_fn=_make_fake_de(calls2), clock=clock,
                rss_fn=lambda: 0, resume_from=proot)
            self.assertIn("resource_blocked", m2["terminals"].values())
            self.assertTrue(m2["partial"])  # retained partial, halt
            self.assertGreater(len(calls2), 0)  # fresh window made progress
            m2f = json.load(open(os.path.join(proot, "manifest.json")))
            r2 = json.load(open(os.path.join(proot, "rows.json")))
            self.assertEqual(m2f["ledger"]["TOTAL"], len(r2))
            self.assertEqual(len(r2), 50 + len(calls2))  # no retry, no loss
            self.assertEqual(len(m2f["completed_identities"]), len(r2))
            self.assertEqual(m2f["wall_windows"],
                             [{"turn_start": 0.0, "cap": 3600},
                              {"turn_start": 5000.0, "cap": 3600}])
            self.assertEqual(prod2, [])
        self.assertEqual(prod, [])

    def test_w3_invalid_wall_windows_refuses_zero_calls(self):
        prod = []
        hist, _ = self._hist(prod)
        pref = next(f for f in hist
                    if len(json.loads(f["rows.json"])) == 50)
        base_m = json.loads(pref["manifest.json"])
        base_r = json.loads(pref["rows.json"])

        def _try_bad(windows):
            with tempfile.TemporaryDirectory() as td:
                mut = dict(base_m, wall_windows=windows)
                proot = self._write_partial(td, mut, base_r)
                calls = []
                with self.assertRaises(R.Refusal) as cm:
                    R.execute(root=proot, gamma_source=_fake_bundle(),
                              de_fn=_make_fake_de(calls),
                              clock=lambda: 5000.0, rss_fn=lambda: 0,
                              resume_from=proot)
                self.assertEqual(cm.exception.code, 2)
                self.assertEqual(calls, [])

        _try_bad([{"turn_start": 0.0, "cap": 1}])  # cap must stay 3600
        _try_bad([])  # non-empty list required
        _try_bad([{"turn_start": 999.0, "cap": 3600}])  # != wall_start
        _try_bad(["not-a-dict"])
        self.assertEqual(prod, [])


class S1F3RedGreenTest(unittest.TestCase):
    """F3 non-trivial fake pins (a)/(b)/(c) — FAKE only, zero prod calls.

    Each pin FAILS on the pre-fix (buggy) logic and PASSES after the fix
    (red-green; re-review executes the red confirmation — coder states the
    red construction per pin in the packet return).
    """

    def test_f3a_layer_rate_feasibility_bound_pinned(self):
        prod = []
        _shim_production_raises(self, prod)
        # Bound pinned at the grid definition (packet §2).
        self.assertAlmostEqual(R.L2_FEASIBILITY_BOUND, 0.83862, places=5)
        self.assertAlmostEqual(
            R.L2_FEASIBILITY_BOUND,
            1.0 - R.H_ANCHORS["L2"] / 5, places=12)
        # Layer-local derivation: m2=ceil(41.31f); f=1.3→54; sweep 44–60.
        self.assertEqual(R.primary_m2_for_f(1.3), 54)
        self.assertEqual(R.primary_m2_for_f(1.05), 44)
        self.assertEqual(R.primary_m2_for_f(1.45), 60)
        self.assertEqual(R.PRIMARY_M2_GRID, tuple(range(44, 61)))
        # No full-symbol m 24–31 reuse for L2 (branch separation).
        self.assertTrue(
            set(R.PRIMARY_M2_GRID).isdisjoint(set(R.M_GRID)))
        self.assertEqual(R.frozen_config()["primary_m2_grid"],
                         list(range(44, 61)))
        self.assertEqual(R.frozen_config()["m_grid"], list(R.M_GRID))
        # Full-symbol grid sits ABOVE the L2 bound (infeasible for L2) …
        for m in R.M_GRID:
            self.assertGreater(1 - m / R.N_FRAME, R.L2_FEASIBILITY_BOUND)
        # … yet the layer grid sits AT/BELOW it (feasible) …
        for m2 in R.PRIMARY_M2_GRID:
            self.assertLessEqual(1 - m2 / R.N_FRAME,
                                 R.L2_FEASIBILITY_BOUND)
        # … and vice versa at full-symbol width (SECONDARY disposition:
        # M_GRID 24–31 feasible as a width-10 budget).
        h_tot = R.H_ANCHORS["L1"] + R.H_ANCHORS["L2"]
        full_bound = 1.0 - h_tot / 10
        for m in R.M_GRID:
            self.assertLessEqual(1 - m / R.N_FRAME, full_bound)
        # Wrong-grid binding (full-symbol m27 on the L2 layer) is infeasible
        # + SW-violating; layer m2=44 is feasible with 1.0≤f≤1.15.
        h_l2 = R.H_ANCHORS["L2"]
        self.assertLess(
            R.layer_efficiency(1 - 27 / R.N_FRAME, h_l2, 5), 1.0)
        f44 = R.layer_efficiency(1 - 44 / R.N_FRAME, h_l2, 5)
        self.assertGreaterEqual(f44, 1.0)
        self.assertLessEqual(f44, 1.15)
        self.assertEqual(prod, [])

    def test_f3b_gate_convergence_screens_unconverged(self):
        prod = []
        _shim_production_raises(self, prod)
        # Attractive f_row (≤1.15, incl. <1) but converged=false ⇒ non-pass
        # on BOTH arms' widths (5 layer / 10 full-symbol).
        rows = [
            {"arm": "PRIMARY", "phase": "confirm", "m": 44,
             "status": "ok", "converged": False, "width": 5, "f_row": 1.05},
            {"arm": "PRIMARY", "phase": "confirm", "m": 45,
             "status": "ok", "converged": False, "width": 5, "f_row": 0.75},
            {"arm": "SECONDARY", "phase": "confirm", "m": 24,
             "status": "ok", "converged": False, "width": 10,
             "f_row": 1.10},
            {"arm": "SECONDARY", "phase": "confirm", "m": 25,
             "status": "ok", "converged": False, "width": 10,
             "f_row": 0.90},
        ]
        gate = R.evaluate_gate(rows)
        for arm in ("PRIMARY", "SECONDARY"):
            self.assertIsNone(gate[arm]["f_ens"])
            self.assertEqual(gate[arm]["n"], 0)  # converged rows only
            self.assertFalse(gate[arm]["pass"])  # empty ⇒ non-pass
        # Only ∃-converged ≤1.15 passes (PRIMARY m44 1.05 passes;
        # SECONDARY m24 1.20 above bar fails).
        rows2 = [
            {"arm": "PRIMARY", "phase": "confirm", "m": 44,
             "status": "ok", "converged": True, "width": 5, "f_row": 1.05},
            {"arm": "PRIMARY", "phase": "confirm", "m": 45,
             "status": "ok", "converged": False, "width": 5, "f_row": 1.01},
            {"arm": "SECONDARY", "phase": "confirm", "m": 24,
             "status": "ok", "converged": True, "width": 10,
             "f_row": 1.20},
        ]
        gate2 = R.evaluate_gate(rows2)
        self.assertTrue(gate2["PRIMARY"]["pass"])
        self.assertEqual(gate2["PRIMARY"]["f_ens"], 1.05)
        self.assertEqual(gate2["PRIMARY"]["n"], 1)
        self.assertFalse(gate2["SECONDARY"]["pass"])
        self.assertEqual(prod, [])

    def test_f3c_sw_orientation_violation_never_passes(self):
        prod = []
        _shim_production_raises(self, prod)
        # PRIMARY 0.7506-class fingerprint (live non-converged max): converged
        # f<1 trips the SW pin, never contributes to a pass.
        rows = [
            {"arm": "PRIMARY", "phase": "confirm", "m": 54,
             "status": "ok", "converged": True, "width": 5,
             "f_row": 0.7506},
        ]
        gate = R.evaluate_gate(rows)
        self.assertFalse(gate["PRIMARY"]["pass"])
        self.assertIsNone(gate["PRIMARY"]["f_ens"])  # decoupled: no valid
        self.assertEqual(gate["PRIMARY"]["n"], 1)
        self.assertGreaterEqual(gate["PRIMARY"]["sw_violations"], 1)
        # Violation + above-bar converged ⇒ still non-pass (violations
        # excluded, 1.50 above 1.15).
        rows2 = [
            {"arm": "PRIMARY", "phase": "confirm", "m": 54,
             "status": "ok", "converged": True, "width": 5,
             "f_row": 0.7506},
            {"arm": "PRIMARY", "phase": "confirm", "m": 60,
             "status": "ok", "converged": True, "width": 5, "f_row": 1.50},
            {"arm": "SECONDARY", "phase": "confirm", "m": 24,
             "status": "ok", "converged": True, "width": 10,
             "f_row": 0.98},
        ]
        gate2 = R.evaluate_gate(rows2)
        self.assertFalse(gate2["PRIMARY"]["pass"])
        self.assertFalse(gate2["SECONDARY"]["pass"])
        self.assertGreaterEqual(gate2["SECONDARY"]["sw_violations"], 1)
        # Max-of-unconverged decoy: unconverged 0.75 alone would look like a
        # "pass" under the old max logic ⇒ fixed gate stays non-pass.
        rows3 = [
            {"arm": "PRIMARY", "phase": "confirm", "m": 44,
             "status": "ok", "converged": False, "width": 5,
             "f_row": 0.75},
        ]
        gate3 = R.evaluate_gate(rows3)
        self.assertFalse(gate3["PRIMARY"]["pass"])
        self.assertIsNone(gate3["PRIMARY"]["f_ens"])
        self.assertEqual(prod, [])


class S1ReproGateTest(unittest.TestCase):
    """G-REPRO pins — FAKE only, zero production calls, zero disk writes."""

    def test_repro_enumeration_30_distinct(self):
        prod = []
        _shim_production_raises(self, prod)
        cells = R.build_repro_plan()
        self.assertEqual(len(cells), 30)
        self.assertEqual(len(R.REPRO_M2) * len(R.CONFIRM_SEEDS)
                         * R.REPRO_N_RESTARTS, 30)
        self.assertEqual(
            len({(c["m"], c["seed_eff"]) for c in cells}), 30)
        for m in R.REPRO_M2:
            self.assertEqual(sum(1 for c in cells if c["m"] == m), 10)
            for s in R.CONFIRM_SEEDS:
                sub = [c for c in cells
                       if c["m"] == m and c["base_seed"] == s]
                self.assertEqual(len(sub), 5)
                self.assertEqual(sorted(c["restart"] for c in sub),
                                 [0, 1, 2, 3, 4])
                for c in sub:
                    self.assertEqual(c["seed_eff"],
                                     s + c["restart"] * 7919)
                r0 = [c for c in sub if c["restart"] == 0][0]
                self.assertEqual(r0["seed_eff"], s)  # r=0 exact seeds
        self.assertEqual(prod, [])

    def test_repro_hash_neutral(self):
        prod = []
        _shim_production_raises(self, prod)
        self.assertEqual(R.config_hash(), RECORDED_CONFIG_HASH)
        cfg = R.frozen_config()
        self.assertEqual(
            set(cfg.keys()),
            {"kernel", "n_frame", "m_grid", "primary_m2_grid", "screen",
             "confirm", "dv_support", "dv_ceiling", "L1_fixed", "outer_de",
             "pop_gen", "caps", "screen_seeds", "confirm_seeds", "budgets",
             "no_retry"})
        blob = json.dumps(cfg).lower()
        for token in ("repro", "7919", "superframe", "restart", "h_full"):
            self.assertNotIn(token, blob)
        self.assertEqual(R.REPRO_LAMBDA, {2: 1.0})
        self.assertEqual(prod, [])

    def test_repro_root_and_auth_refusals(self):
        prod = []
        _shim_production_raises(self, prod)
        absent = os.path.join("workspace", "s1_repro_never_absent")
        # Every non-authorized shape refuses rc=2 pre-anything.
        for argv in (["--repro-gate"],
                     ["--repro-gate", "--execute-real",
                      "--root", absent],
                     ["--repro-gate", "--execution-authorized",
                      "--root", absent],
                     ["--repro-gate", "--execute-real",
                      "--execution-authorized", "--profile-only",
                      "--root", absent],
                     ["--repro-gate", "--execute-real",
                      "--execution-authorized",
                      "--resume-from", absent],
                     ["--repro-gate", "--execute-real",
                      "--execution-authorized",
                      "--root", os.path.join("workspace",
                                             "s1_mcde_other")]):
            with self.assertRaises(R.Refusal) as cm:
                R.main(argv)
            self.assertEqual(cm.exception.code, 2)
        self.assertFalse(os.path.exists(absent))
        # Present root refuses with zero DE calls.
        with tempfile.TemporaryDirectory() as td:
            calls = []
            with self.assertRaises(R.Refusal) as cm:
                R.execute_repro(
                    root=td, gamma_source=_fake_bundle(),
                    de_fn=_make_fake_de(calls), clock=lambda: 0.0,
                    rss_fn=lambda: 0,
                    writer=lambda root, files: None)
            self.assertEqual(cm.exception.code, 2)
            self.assertEqual(calls, [])
        self.assertEqual(prod, [])

    def test_repro_dual_reporting_fake(self):
        prod = []
        _shim_production_raises(self, prod)
        calls = []
        captured = {}
        manifest = R.execute_repro(
            root=os.path.join("no-such-dir", "s1_repro_never"),
            gamma_source=_fake_bundle(),
            de_fn=_make_fake_de(calls, trace=(0.83, 0.83)),
            clock=lambda: 0.0, rss_fn=lambda: 0,
            writer=lambda root, files: captured.update(files))
        self.assertEqual(len(calls), 30)
        self.assertEqual(manifest["ledger"],
                         {"PRIMARY": 30, "SECONDARY": 0,
                          "TOTAL": 30, "SETUP": 0})
        self.assertEqual(manifest["scientific_de_calls"], 30)
        rows = json.loads(captured["rows.json"])
        self.assertEqual(len(rows), 30)
        for r in rows:
            # BOTH units carried per row (packet §5).
            self.assertIn("f_row", r)
            self.assertIn("f_superframe", r)
            self.assertAlmostEqual(
                r["f_superframe"],
                (4 * 5 * (r["m"] + 2) + 64) / (1024 * R.H_FULL_ANCHOR))
            self.assertIn("base_seed", r)
            self.assertIn("restart", r)
            self.assertEqual(r["seed"],
                             r["base_seed"] + r["restart"] * 7919)
        # h=0.83 fake: all m46-48 in 1.0..1.15, all converged -> PASS.
        self.assertAlmostEqual(
            next(r for r in rows
                 if r["m"] == 47)["f_superframe"], 1.2246, places=3)
        self.assertEqual(manifest["config_hash"], RECORDED_CONFIG_HASH)
        self.assertTrue(manifest["verify"]["ok"])
        self.assertEqual(manifest["terminals"], {"REPRO": "COMPLETE"})
        self.assertTrue(manifest["repro_gate"]["pass"])
        self.assertEqual(manifest["repro_gate"]["m47_per_seed_pass"],
                         {str(s): 5 for s in R.CONFIRM_SEEDS})
        self.assertEqual(prod, [])

    def test_repro_gate_bar_arithmetic(self):
        prod = []
        _shim_production_raises(self, prod)
        s0, s1 = R.CONFIRM_SEEDS

        def _mk(m, s, f, conv=True, r=0):
            return {"arm": "PRIMARY", "phase": "confirm", "m": m,
                    "status": "ok", "converged": conv, "width": 5,
                    "f_row": f, "base_seed": s, "restart": r}

        # PASS shape: 3/5 each seed, pooled converged range 0.02 <= 0.04.
        ok_rows = [_mk(47, s0, 1.13, r=0), _mk(47, s0, 1.12, r=1),
                   _mk(47, s0, 1.14, r=2),
                   _mk(47, s0, 1.50, conv=False, r=3),
                   _mk(47, s0, 0.90, conv=False, r=4),
                   _mk(47, s1, 1.13, r=0), _mk(47, s1, 1.135, r=1),
                   _mk(47, s1, 1.125, r=2),
                   _mk(47, s1, 1.60, conv=False, r=3),
                   _mk(47, s1, 0.80, conv=False, r=4)]
        g = R.evaluate_repro_gate(ok_rows)
        self.assertTrue(g["pass"])
        self.assertEqual(g["m47_per_seed_pass"],
                         {str(s0): 3, str(s1): 3})
        self.assertAlmostEqual(g["m47_f_range"], 0.02)
        # FAIL-count: seed1 only 2/5.
        short = [r for r in ok_rows
                 if not (r["base_seed"] == s1 and r["restart"] == 2)]
        g2 = R.evaluate_repro_gate(short)
        self.assertFalse(g2["pass"])
        self.assertEqual(g2["m47_per_seed_pass"][str(s1)], 2)
        # FAIL-range: counts met but pooled spread 0.09 > 0.04.
        wide = ([_mk(47, s0, 1.05, r=0), _mk(47, s0, 1.13, r=1),
                 _mk(47, s0, 1.14, r=2)]
                + [_mk(47, s1, 1.13, r=0), _mk(47, s1, 1.13, r=1),
                   _mk(47, s1, 1.13, r=2)])
        g3 = R.evaluate_repro_gate(wide)
        self.assertFalse(g3["pass"])
        self.assertAlmostEqual(g3["m47_f_range"], 0.09)
        # Empty converged set: explicit non-pass, range None.
        g4 = R.evaluate_repro_gate([])
        self.assertFalse(g4["pass"])
        self.assertIsNone(g4["m47_f_range"])
        self.assertEqual(prod, [])


if __name__ == "__main__":
    unittest.main()
