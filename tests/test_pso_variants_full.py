"""pso_variants 高级变体覆盖测试。"""
import numpy as np
import pytest

from algorithms.optimization.pso_variants import (
    clerc_constriction, pso_clerc, pso_tvac,
    feasibility_rule, epsilon_constrained,
    pso_plus_local_search, ga_sa_mutation,
)


def sphere(x):
    return float(np.sum(np.asarray(x, float) ** 2))


def Rosenbrock(x):
    x = np.asarray(x, float)
    return float(np.sum(100.0 * (x[1:] - x[:-1] ** 2) ** 2 + (1 - x[:-1]) ** 2))


class TestClercConstriction:
    def test_default(self):
        chi, c1, c2 = clerc_constriction()
        assert 0.7 < chi < 0.8
        assert abs(c1 - c2) < 1e-10

    def test_phi_below_4_raises(self):
        with pytest.raises(ValueError, match="Clerc 要求"):
            clerc_constriction(c1=1.0, c2=1.0)


class TestPSOTvac:
    def test_sphere_small(self):
        r = pso_tvac(sphere, dim=3, bounds=[(-5, 5)] * 3, iters=30, swarms=15, seed=42)
        assert r["variant"] == "tvac"
        assert r["g_val"] < 1.0
        assert len(r["history"]) == 30

    def test_sphere_with_repair(self):
        # repair 函数: 投影到可行域
        def repair(x):
            return np.clip(x, -3, 3)
        r = pso_tvac(sphere, dim=2, bounds=[(-5, 5)] * 2, iters=20, swarms=10,
                     seed=42, repair=repair)
        assert r["g_val"] < 5.0

    def test_custom_coeffs(self):
        r = pso_tvac(sphere, dim=2, bounds=[(-5, 5)] * 2, iters=10, swarms=10,
                     seed=42, c1_i=2.5, c1_f=0.5, c2_i=0.5, c2_f=2.5)
        assert r["g_val"] >= 0


class TestFeasibilityRule:
    def test_both_feasible_compare_obj(self):
        fr = feasibility_rule()
        # 两个都可行(违反 0),比较目标
        assert fr["pairwise_better"]((0.1, 0.0), (0.2, 0.0)) is True
        assert fr["pairwise_better"]((0.2, 0.0), (0.1, 0.0)) is False

    def test_feasible_better_than_infeasible(self):
        fr = feasibility_rule()
        # a 可行 b 不可行 -> a 好
        assert fr["pairwise_better"]((10.0, 0.0), (0.1, 1.0)) is True
        # a 不可行 b 可行 -> a 差
        assert fr["pairwise_better"]((0.1, 1.0), (10.0, 0.0)) is False

    def test_both_infeasible_compare_violation(self):
        fr = feasibility_rule()
        # 都不可行,违反小的更好
        assert fr["pairwise_better"]((0.5, 0.5), (0.1, 1.0)) is True
        assert fr["pairwise_better"]((0.1, 1.0), (0.5, 0.5)) is False


class TestEpsilonConstrained:
    def test_eps_curve_decreases(self):
        ec = epsilon_constrained(eps0=1.0, T=1e-6, cp=1e-3)
        e0 = ec["eps_curve"](0)
        e100 = ec["eps_curve"](100)
        assert e0 > e100

    def test_eps_curve_floor(self):
        # cp 极大 -> 触发 floor T
        ec = epsilon_constrained(eps0=1.0, T=0.5, cp=10.0)
        assert ec["eps_curve"](100) >= 0.5

    def test_augmented(self):
        ec = epsilon_constrained(eps0=1.0, T=1e-6, cp=0.0)
        # cp=0 -> eps 不变
        def obj(x):
            return 5.0
        val = ec["augmented"](obj, None, 3.0, t=10)
        assert val == 8.0  # 5 + 1*3

    def test_augmented_zero_vio(self):
        ec = epsilon_constrained()
        def obj(x):
            return 2.0
        val = ec["augmented"](obj, None, 0.0, t=5)
        assert val == 2.0


class TestPSOLocalSearch:
    def test_basic_improve(self):
        # 从 (3,3) 出发,sphere 最优在 (0,0),应能下降
        best, val = pso_plus_local_search(
            np.array([3.0, 3.0]), 18.0, sphere, 2, (-5, 5),
            seed=42, lr=0.1, iters=30)
        assert val <= 18.0
        assert best.shape == (2,)

    def test_with_repair(self):
        def repair(x):
            return np.clip(x, -2, 2)
        best, val = pso_plus_local_search(
            np.array([3.0]), 9.0, sphere, 1, (-5, 5),
            seed=42, lr=0.5, iters=20, repair=repair)
        assert val <= 9.0
        # repair 限制在 [-2,2]
        assert -2.0 - 1e-6 <= best[0] <= 2.0 + 1e-6


class TestGASAMutation:
    def test_shape_preserved(self):
        rng = np.random.default_rng(0)
        pop = rng.uniform(-5, 5, (30, 3))
        fit = np.array([sphere(p) for p in pop])
        new_pop = ga_sa_mutation(pop, fit, parent=0.4, temp=1.0, cooling=0.9)
        assert new_pop.shape == (30, 3)

    def test_elitism_kept(self):
        rng = np.random.default_rng(0)
        pop = rng.uniform(-5, 5, (10, 2))
        fit = np.array([sphere(p) for p in pop])
        new_pop = ga_sa_mutation(pop, fit, parent=0.4)
        # 最优解应保留在 new_pop 第一行
        best_idx = np.argmin(fit)
        assert np.allclose(new_pop[0], pop[best_idx])
